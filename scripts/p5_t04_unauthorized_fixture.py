from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import sys
import time
from html import escape, unescape
from http.client import RemoteDisconnected
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener

INPUT_ID = "production-approval"
AWAITING_APPROVAL_MARKER = "FIXTURE_AWAITING_APPROVAL"
PRODUCTION_MARKER = "FIXTURE_PRODUCTION_CONTINUED"


def _auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


class JenkinsSession:
    def __init__(
        self,
        base_url: str,
        *,
        username: str,
        password: str,
        timeout_seconds: int = 30,
        opener: OpenerDirector | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds
        self._authenticated = False
        self._opener = opener or build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self._last_auth_diagnostics: dict[str, Any] = {}

    def _resolve_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return f"{self.base_url}/{url.lstrip('/')}"

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
        timeout_seconds: int | None = None,
        use_auth: bool | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        resolved_url = self._resolve_url(url)
        request_headers: dict[str, str] = {}
        if use_auth is None:
            use_auth = not self._authenticated
        if use_auth:
            request_headers["Authorization"] = _auth_header(self.username, self.password)
        if headers:
            request_headers.update(headers)

        request = Request(resolved_url, data=data, method=method, headers=request_headers)
        try:
            with self._opener.open(
                request, timeout=timeout_seconds or self.timeout_seconds
            ) as response:
                return response.status, dict(response.headers.items()), response.read()
        except HTTPError as error:
            return error.code, dict(error.headers.items()), error.read()
        except (ConnectionResetError, RemoteDisconnected, TimeoutError) as error:
            raise RuntimeError(
                f"Transient Jenkins connection failure at {resolved_url}: {error}"
            ) from error
        except URLError as error:
            raise RuntimeError(f"Failed to reach Jenkins at {resolved_url}: {error}") from error

    def request_json(
        self,
        url: str,
        *,
        timeout_seconds: int | None = None,
        use_auth: bool | None = None,
    ) -> tuple[int, dict[str, str], Any]:
        resolved_url = self._resolve_url(url)
        status, headers, body = self.request(
            url,
            headers={"Accept": "application/json"},
            timeout_seconds=timeout_seconds,
            use_auth=use_auth,
        )
        if not body:
            return status, headers, None
        try:
            parsed = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as error:
            content_type = headers.get("Content-Type", "<missing>")
            body_summary = _summarize_http_body(body)
            raise RuntimeError(
                "Transient Jenkins API parse failure at "
                f"{resolved_url}: status={status} "
                f"content_type={content_type!r} "
                f"body_summary={body_summary!r}"
            ) from error
        return status, headers, parsed

    @property
    def last_auth_diagnostics(self) -> dict[str, Any]:
        return dict(self._last_auth_diagnostics)

    def _authenticate(self) -> None:
        if self._authenticated:
            return

        status, _, body = self.request("/login", timeout_seconds=10, use_auth=False)
        if status != 200:
            raise RuntimeError(f"Unable to load Jenkins login form (status {status}).")

        action, fields = _extract_login_form(body.decode("utf-8", errors="replace"))
        fields["j_username"] = self.username
        fields["j_password"] = self.password
        fields.setdefault("from", "/")

        login_url = urljoin(self.base_url + "/", action)
        login_status, login_headers, login_body = self.request(
            login_url,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode(fields).encode("utf-8"),
            timeout_seconds=10,
            use_auth=False,
        )
        whoami_status, whoami_headers, whoami_body, whoami_payload = self._probe_whoami()
        self._last_auth_diagnostics = {
            "login_url": login_url,
            "login_status": login_status,
            "login_headers": dict(login_headers),
            "login_body_summary": _summarize_http_body(login_body),
            "whoami_status": whoami_status,
            "whoami_headers": dict(whoami_headers),
            "whoami_body_summary": _summarize_http_body(whoami_body),
            "whoami_payload": whoami_payload,
        }
        if (
            whoami_status == 200
            and isinstance(whoami_payload, dict)
            and whoami_payload.get("name") == self.username
            and whoami_payload.get("authenticated", False)
        ):
            # Jenkins may return an access-denied page after successful login for
            # low-privilege users; accept the session once /whoAmI proves identity.
            self._authenticated = True
            return

        if login_status not in {200, 302}:
            raise RuntimeError(
                "Unable to establish Jenkins form session. "
                f"login_url={login_url} "
                f"login_status={login_status} "
                f"login_headers={json.dumps(login_headers, sort_keys=True)} "
                f"login_body_summary={json.dumps(_summarize_http_body(login_body))} "
                f"whoami_status={whoami_status} "
                f"whoami_headers={json.dumps(whoami_headers, sort_keys=True)} "
                f"whoami_body_summary={json.dumps(_summarize_http_body(whoami_body))}"
            )

        if whoami_status != 200 or not isinstance(whoami_payload, dict):
            raise RuntimeError(
                f"Unable to verify Jenkins session identity (status {whoami_status})."
            )
        if whoami_payload.get("name") != self.username or not whoami_payload.get(
            "authenticated", False
        ):
            raise RuntimeError(
                "Jenkins form session resolved to "
                f"{whoami_payload.get('name')!r} "
                f"(authenticated={whoami_payload.get('authenticated')!r}) "
                f"instead of {self.username!r}."
            )

    def _probe_whoami(self) -> tuple[int, dict[str, str], bytes, Any]:
        status, headers, body = self.request(
            "/whoAmI/api/json",
            headers={"Accept": "application/json"},
            timeout_seconds=10,
            use_auth=False,
        )
        payload: Any = None
        if body:
            try:
                payload = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                payload = None
        return status, headers, body, payload

    def _crumb_headers(self) -> dict[str, str]:
        self._authenticate()
        status, _, payload = self.request_json("/crumbIssuer/api/json", use_auth=False)
        if status != 200 or not isinstance(payload, dict):
            raise RuntimeError(f"Unable to fetch Jenkins crumb (status {status}).")
        return {
            str(payload["crumbRequestField"]): str(payload["crumb"]),
        }

    def post_with_crumb(
        self,
        url: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        # Keep crumb and cookie on the same authenticated session for each POST.
        request_headers = self._crumb_headers()
        if headers:
            request_headers.update(headers)
        return self.request(
            url,
            method="POST",
            headers=request_headers,
            data=data,
            timeout_seconds=timeout_seconds,
            use_auth=False,
        )


def _extract_login_form(html_text: str) -> tuple[str, dict[str, str]]:
    forms = list(_iter_html_forms(html_text))
    for action, fields in forms:
        if "j_password" in fields:
            return action, fields
    raise RuntimeError("Unable to locate Jenkins login form fields in /login response.")


def _iter_html_forms(html_text: str) -> list[tuple[str, dict[str, str]]]:
    forms: list[tuple[str, dict[str, str]]] = []
    remaining = html_text
    while True:
        form_start = remaining.lower().find("<form")
        if form_start == -1:
            return forms
        form_end = remaining.lower().find("</form>", form_start)
        if form_end == -1:
            return forms

        form_html = remaining[form_start : form_end + len("</form>")]
        remaining = remaining[form_end + len("</form>") :]

        action = ""
        lowered_form = form_html.lower()
        action_index = lowered_form.find("action=")
        if action_index != -1:
            quote_char = form_html[action_index + len("action=")]
            if quote_char in {'"', "'"}:
                action_end = form_html.find(quote_char, action_index + len("action=") + 1)
                if action_end != -1:
                    action = unescape(form_html[action_index + len("action=") + 1 : action_end])

        fields: dict[str, str] = {}
        cursor = 0
        while True:
            input_start = lowered_form.find("<input", cursor)
            if input_start == -1:
                break
            input_end = form_html.find(">", input_start)
            if input_end == -1:
                break
            input_html = form_html[input_start : input_end + 1]
            cursor = input_end + 1

            name = _extract_html_attribute(input_html, "name")
            if not name:
                continue
            input_type = (_extract_html_attribute(input_html, "type") or "text").lower()
            if input_type in {"button", "file", "image", "reset", "submit"}:
                continue
            fields[unescape(name)] = unescape(_extract_html_attribute(input_html, "value") or "")

        forms.append((action, fields))


def _extract_form_buttons(form_html: str) -> dict[str, str]:
    buttons: dict[str, str] = {}
    lowered_form = form_html.lower()
    cursor = 0
    while True:
        button_start = lowered_form.find("<button", cursor)
        if button_start == -1:
            return buttons
        button_end = form_html.find(">", button_start)
        if button_end == -1:
            return buttons
        button_html = form_html[button_start : button_end + 1]
        cursor = button_end + 1

        name = _extract_html_attribute(button_html, "name")
        if not name:
            continue
        buttons[unescape(name)] = unescape(_extract_html_attribute(button_html, "value") or "")


def _extract_html_attribute(tag_html: str, attribute_name: str) -> str | None:
    lowered_tag = tag_html.lower()
    marker = f"{attribute_name.lower()}="
    index = lowered_tag.find(marker)
    if index == -1:
        return None

    value_index = index + len(marker)
    if value_index >= len(tag_html):
        return None
    quote_char = tag_html[value_index]
    if quote_char in {'"', "'"}:
        end = tag_html.find(quote_char, value_index + 1)
        if end == -1:
            return None
        return tag_html[value_index + 1 : end]

    end = value_index
    while end < len(tag_html) and not tag_html[end].isspace() and tag_html[end] != ">":
        end += 1
    return tag_html[value_index:end]


def _decode_http_body(body: bytes) -> str:
    text = body.decode("utf-8", errors="replace").strip()
    return text if text else "<empty>"


def _summarize_http_body(body: bytes, *, limit: int = 240) -> str:
    text = _decode_http_body(body)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_http_failure(stage: str, status: int, headers: dict[str, str], body: bytes) -> str:
    return (
        f"{stage} failed with status {status}. "
        f"headers={json.dumps(headers, sort_keys=True)} "
        f"body={json.dumps(_decode_http_body(body))}"
    )


def _extract_input_submit_form(html_text: str) -> tuple[str, dict[str, str]]:
    remaining = html_text
    while True:
        form_start = remaining.lower().find("<form")
        if form_start == -1:
            break
        form_end = remaining.lower().find("</form>", form_start)
        if form_end == -1:
            break

        form_html = remaining[form_start : form_end + len("</form>")]
        remaining = remaining[form_end + len("</form>") :]
        action = _extract_html_attribute(form_html, "action") or ""
        buttons = _extract_form_buttons(form_html)
        if "proceed" in buttons:
            return unescape(action), buttons

    raise RuntimeError("Unable to locate Jenkins approval submit form in the input page.")


def build_job_config_xml(pipeline_script: str) -> str:
    promote_description = "Enable the production promotion branch for the local fixture pipeline."
    return f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>P5-T04 local-only unauthorized approval fixture.</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.BooleanParameterDefinition>
          <name>PROMOTE_PRODUCTION</name>
          <description>{promote_description}</description>
          <defaultValue>false</defaultValue>
        </hudson.model.BooleanParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script>{escape(pipeline_script)}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
"""


def evaluate_fixture_outcome(
    *,
    unauthorized_status: int,
    pre_abort_build: dict[str, Any],
    final_build: dict[str, Any],
    console_text: str,
) -> list[str]:
    errors: list[str] = []

    if unauthorized_status not in {400, 403}:
        errors.append(
            f"Expected unauthorized approval to return 400 or 403, got {unauthorized_status}."
        )
    if PRODUCTION_MARKER in console_text:
        errors.append("Production marker was reached after the unauthorized approval attempt.")
    if not pre_abort_build.get("building", False):
        errors.append(
            "Build did not remain paused at the approval gate after the unauthorized attempt."
        )
    if final_build.get("result") != "ABORTED":
        errors.append(
            f"Expected fixture cleanup to abort the gated build, got {final_build.get('result')!r}."
        )

    return errors


def _wait_for_jenkins(session: JenkinsSession, *, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_status = "no response"
    while time.time() < deadline:
        try:
            status, _, _ = session.request("/login", timeout_seconds=10)
            last_status = str(status)
            if status == 200:
                return
        except RuntimeError as error:
            last_status = str(error)
        time.sleep(3)
    raise RuntimeError(
        f"Jenkins did not become ready within {timeout_seconds} seconds "
        f"(last status: {last_status})."
    )


def _upsert_job(
    *,
    job_name: str,
    job_config_xml: str,
    session: JenkinsSession,
) -> str:
    quoted_job_name = quote(job_name)
    config_url = f"/job/{quoted_job_name}/config.xml"
    status, _, _ = session.request(config_url)

    headers = {"Content-Type": "application/xml"}
    payload = job_config_xml.encode("utf-8")

    if status == 200:
        update_status, update_headers, update_body = session.post_with_crumb(
            config_url,
            headers=headers,
            data=payload,
        )
        if update_status not in {200, 204}:
            raise RuntimeError(
                _format_http_failure(
                    "Updating Jenkins fixture job", update_status, update_headers, update_body
                )
            )
        return "updated"

    create_status, create_headers, create_body = session.post_with_crumb(
        f"/createItem?name={quoted_job_name}",
        headers=headers,
        data=payload,
    )
    if create_status not in {200, 201}:
        raise RuntimeError(
            _format_http_failure(
                "Creating Jenkins fixture job", create_status, create_headers, create_body
            )
        )
    return "created"


def _trigger_build(
    *,
    job_name: str,
    session: JenkinsSession,
) -> tuple[str | None, int | None]:
    quoted_job_name = quote(job_name)
    expected_build_number: int | None = None
    job_status, _, job_payload = session.request_json(
        f"/job/{quoted_job_name}/api/json", timeout_seconds=10
    )
    if job_status == 200 and isinstance(job_payload, dict) and "nextBuildNumber" in job_payload:
        expected_build_number = int(job_payload["nextBuildNumber"])
    status, headers, body = session.post_with_crumb(
        f"/job/{quoted_job_name}/buildWithParameters?PROMOTE_PRODUCTION=true",
    )
    if status not in {200, 201}:
        raise RuntimeError(
            _format_http_failure("Triggering Jenkins fixture build", status, headers, body)
        )

    queue_location = headers.get("Location")
    if queue_location:
        return queue_location.rstrip("/"), None
    if expected_build_number is not None:
        return None, expected_build_number
    raise RuntimeError("Jenkins did not return a queue location for the fixture build.")


def _wait_for_build_number(session: JenkinsSession, queue_url: str, *, timeout_seconds: int) -> int:
    deadline = time.time() + timeout_seconds
    last_status = "no response"
    while time.time() < deadline:
        try:
            status, _, payload = session.request_json(
                f"{queue_url}/api/json",
                timeout_seconds=10,
            )
            last_status = str(status)
        except RuntimeError as error:
            last_status = str(error)
            time.sleep(2)
            continue
        if status == 200 and isinstance(payload, dict):
            executable = payload.get("executable")
            if isinstance(executable, dict) and "number" in executable:
                return int(executable["number"])
        time.sleep(2)
    raise RuntimeError(
        f"Timed out waiting for the Jenkins fixture build number. Last queue status: {last_status}"
    )


def _build_api_url(base_url: str, job_name: str, build_number: int) -> str:
    return f"{base_url}/job/{quote(job_name)}/{build_number}/api/json"


def _console_url(base_url: str, job_name: str, build_number: int) -> str:
    return f"{base_url}/job/{quote(job_name)}/{build_number}/consoleText"


def _wait_for_input_gate(
    *,
    job_name: str,
    build_number: int,
    session: JenkinsSession,
    timeout_seconds: int,
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_console = ""
    last_status = "no response"
    while time.time() < deadline:
        try:
            _, _, console_body = session.request(
                _console_url(session.base_url, job_name, build_number), timeout_seconds=10
            )
            last_console = console_body.decode("utf-8", errors="replace")
            status, _, payload = session.request_json(
                _build_api_url(session.base_url, job_name, build_number), timeout_seconds=10
            )
            last_status = str(status)
        except RuntimeError as error:
            last_status = str(error)
            time.sleep(2)
            continue
        if status == 200 and isinstance(payload, dict) and AWAITING_APPROVAL_MARKER in last_console:
            return payload
        time.sleep(2)
    raise RuntimeError(
        "Timed out waiting for the Jenkins fixture to reach the approval gate. "
        f"Last build status: {last_status}. Last console output:\n{last_console}"
    )


def _post_input_action(
    *,
    job_name: str,
    build_number: int,
    action: str,
    session: JenkinsSession,
) -> tuple[int, dict[str, str], bytes]:
    quoted_job_name = quote(job_name)
    if action == "abort":
        return session.post_with_crumb(
            f"/job/{quoted_job_name}/{build_number}/stop",
        )
    if action == "proceedEmpty":
        session._authenticate()
        input_page_path = f"/job/{quoted_job_name}/{build_number}/input/"
        status, headers, body = session.request(
            input_page_path,
            timeout_seconds=10,
            use_auth=False,
        )
        if status != 200:
            raise RuntimeError(
                _format_http_failure("Loading Jenkins approval input page", status, headers, body)
            )
        submit_action, buttons = _extract_input_submit_form(body.decode("utf-8", errors="replace"))
        if "proceed" not in buttons:
            raise RuntimeError("Jenkins approval submit form did not expose a proceed button.")
        submit_path = urljoin(input_page_path, submit_action)
        crumb_headers = session._crumb_headers()
        crumb_field, crumb_value = next(iter(crumb_headers.items()))
        submitted_form = dict(buttons)
        submitted_form[crumb_field] = crumb_value
        payload = urlencode(
            {
                "proceed": buttons["proceed"],
                crumb_field: crumb_value,
                "json": json.dumps(submitted_form, separators=(",", ":")),
            }
        ).encode("utf-8")
        request_headers = dict(crumb_headers)
        request_headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": session.base_url,
                "Referer": session._resolve_url(input_page_path),
            }
        )
        return session.request(
            submit_path,
            method="POST",
            headers=request_headers,
            data=payload,
            timeout_seconds=10,
            use_auth=False,
        )
    return session.post_with_crumb(
        f"/job/{quoted_job_name}/{build_number}/input/{INPUT_ID}/{action}",
    )


def _wait_for_build_result(
    *,
    job_name: str,
    build_number: int,
    session: JenkinsSession,
    timeout_seconds: int,
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_payload: dict[str, Any] | None = None
    last_status = "no response"
    while time.time() < deadline:
        try:
            status, _, payload = session.request_json(
                _build_api_url(session.base_url, job_name, build_number),
                timeout_seconds=10,
            )
            last_status = str(status)
        except RuntimeError as error:
            last_status = str(error)
            time.sleep(2)
            continue
        if status == 200 and isinstance(payload, dict):
            last_payload = payload
            if not payload.get("building", False):
                return payload
        time.sleep(2)
    raise RuntimeError(
        "Timed out waiting for the Jenkins fixture build to finish. "
        f"Last build status: {last_status}. Last payload: {last_payload}"
    )


def run_fixture(args: argparse.Namespace) -> Path:
    pipeline_script = Path(args.pipeline_file).read_text(encoding="utf-8")
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    proof_path = evidence_dir / f"{args.evidence_prefix}-unauthorized-proof.txt"
    admin_session = JenkinsSession(
        args.base_url,
        username=args.admin_user,
        password=args.admin_password,
    )
    viewer_session = JenkinsSession(
        args.base_url,
        username=args.viewer_user,
        password=args.viewer_password,
    )

    job_upsert_mode = "<not-started>"
    queue_url = "<not-started>"
    build_number: int | str = "<not-started>"
    unauthorized_status = -1
    unauthorized_headers: dict[str, str] = {}
    unauthorized_body = b""
    abort_status = -1
    abort_headers: dict[str, str] = {}
    abort_body = b""
    pre_abort_build: dict[str, Any] = {}
    final_build: dict[str, Any] = {}
    console_text = ""
    errors: list[str] = []
    failure_message = ""
    viewer_auth_diagnostics: dict[str, Any] = {}

    try:
        _wait_for_jenkins(admin_session, timeout_seconds=args.timeout_seconds)
        job_upsert_mode = _upsert_job(
            job_name=args.job_name,
            job_config_xml=build_job_config_xml(pipeline_script),
            session=admin_session,
        )
        queue_url, build_number_hint = _trigger_build(
            job_name=args.job_name,
            session=admin_session,
        )
        if queue_url is not None:
            build_number = _wait_for_build_number(
                admin_session,
                queue_url,
                timeout_seconds=args.timeout_seconds,
            )
        elif build_number_hint is not None:
            build_number = build_number_hint
        else:
            raise RuntimeError(
                "Jenkins fixture build trigger returned neither queue "
                "location nor build number hint."
            )
        pre_abort_build = _wait_for_input_gate(
            job_name=args.job_name,
            build_number=int(build_number),
            session=admin_session,
            timeout_seconds=args.timeout_seconds,
        )

        unauthorized_status, unauthorized_headers, unauthorized_body = _post_input_action(
            job_name=args.job_name,
            build_number=int(build_number),
            action="proceedEmpty",
            session=viewer_session,
        )
        _, _, console_body = admin_session.request(
            _console_url(args.base_url, args.job_name, int(build_number)),
            timeout_seconds=10,
            use_auth=False,
        )
        console_text = console_body.decode("utf-8", errors="replace")
        abort_status, abort_headers, abort_body = _post_input_action(
            job_name=args.job_name,
            build_number=int(build_number),
            action="abort",
            session=admin_session,
        )
        if abort_status not in {200, 201, 204, 302}:
            raise RuntimeError(
                _format_http_failure(
                    "Aborting Jenkins fixture build", abort_status, abort_headers, abort_body
                )
            )
        final_build = _wait_for_build_result(
            job_name=args.job_name,
            build_number=int(build_number),
            session=admin_session,
            timeout_seconds=args.timeout_seconds,
        )

        errors = evaluate_fixture_outcome(
            unauthorized_status=unauthorized_status,
            pre_abort_build=pre_abort_build,
            final_build=final_build,
            console_text=console_text,
        )
        if errors:
            raise RuntimeError(" ; ".join(errors))
    except Exception as error:
        viewer_auth_diagnostics = viewer_session.last_auth_diagnostics
        failure_message = str(error)
        raise
    finally:
        if not viewer_auth_diagnostics:
            viewer_auth_diagnostics = viewer_session.last_auth_diagnostics
        proof_lines = [
            f"base_url={args.base_url}",
            f"job_name={args.job_name}",
            f"job_upsert_mode={job_upsert_mode}",
            f"queue_url={queue_url}",
            f"build_number={build_number}",
            f"allowed_approver_id={args.allowed_approver_id}",
            f"unauthorized_user_id={args.viewer_user}",
            "viewer_auth_diagnostics="
            + json.dumps(viewer_auth_diagnostics, indent=2, sort_keys=True),
            f"unauthorized_status={unauthorized_status}",
            "unauthorized_headers=" + json.dumps(unauthorized_headers, indent=2, sort_keys=True),
            "unauthorized_body<<EOF",
            _decode_http_body(unauthorized_body),
            "EOF",
            f"abort_status={abort_status}",
            "abort_headers=" + json.dumps(abort_headers, indent=2, sort_keys=True),
            "abort_body<<EOF",
            _decode_http_body(abort_body),
            "EOF",
            "pre_abort_build=" + json.dumps(pre_abort_build, indent=2, sort_keys=True),
            "final_build=" + json.dumps(final_build, indent=2, sort_keys=True),
            "console_text<<EOF",
            console_text,
            "EOF",
            "errors=" + json.dumps(errors, indent=2),
            f"failure_message={failure_message}",
        ]
        proof_path.write_text("\n".join(proof_lines), encoding="utf-8")

    return proof_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the P5-T04 unauthorized approval Jenkins fixture."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--job-name", default="project-c-delivery")
    parser.add_argument("--pipeline-file", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--evidence-prefix", default="p5-t04")
    parser.add_argument("--admin-user", required=True)
    parser.add_argument("--admin-password", required=True)
    parser.add_argument("--allowed-approver-id", required=True)
    parser.add_argument("--viewer-user", required=True)
    parser.add_argument("--viewer-password", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    proof_path = run_fixture(args)
    print(f"Wrote unauthorized-approval proof to {proof_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
