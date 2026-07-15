from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from scripts.p5_t04_unauthorized_fixture import (
    AWAITING_APPROVAL_MARKER,
    INPUT_ID,
    PRODUCTION_MARKER,
    JenkinsSession,
    _post_input_action,
    _trigger_build,
    _wait_for_build_number,
    _wait_for_build_result,
    _wait_for_input_gate,
    build_job_config_xml,
    evaluate_fixture_outcome,
)

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_FIXTURE = (
    ROOT / "infra" / "jenkins" / "test-fixtures" / "p5-t04-unauthorized-approval.groovy"
)
WRAPPER_SCRIPT = ROOT / "scripts" / "Invoke-P5UnauthorizedApprovalFixture.ps1"


@contextmanager
def run_session_fixture_server() -> Iterator[type[BaseHTTPRequestHandler]]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"
        crumb_fetches = 0
        login_gets = 0
        login_posts = 0
        received_post_cookies: list[str | None] = []
        received_post_crumbs: list[str | None] = []
        received_post_auth_headers: list[str | None] = []

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                body = b"ok"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path == "/login":
                type(self).login_gets += 1
                body = (
                    b"<html><body>"
                    b'<form method="post" action="/j_spring_security_check">'
                    b'<input type="hidden" name="from" value="/" />'
                    b'<input type="text" name="j_username" value="" />'
                    b'<input type="password" name="j_password" value="" />'
                    b"</form>"
                    b"</body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Set-Cookie", "session=preauth; Path=/")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path == "/whoAmI/api/json":
                if self.headers.get("Cookie") != "session=fixture-session":
                    self.send_response(403)
                    self.end_headers()
                    return

                body = json.dumps({"authenticated": True, "name": "viewer"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path != "/crumbIssuer/api/json":
                self.send_response(404)
                self.end_headers()
                return

            type(self).crumb_fetches += 1
            session_cookie = self.headers.get("Cookie")
            body = json.dumps(
                {
                    "crumbRequestField": "Jenkins-Crumb",
                    "crumb": f"crumb-{type(self).crumb_fetches}",
                }
            ).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            if session_cookie != "session=fixture-session":
                self.send_header("Set-Cookie", "session=fixture-session; Path=/")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/j_spring_security_check":
                type(self).login_posts += 1
                body = b""
                self.send_response(302)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", "session=fixture-session; Path=/")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            type(self).received_post_cookies.append(self.headers.get("Cookie"))
            type(self).received_post_crumbs.append(self.headers.get("Jenkins-Crumb"))
            type(self).received_post_auth_headers.append(self.headers.get("Authorization"))
            expected_crumb = f"crumb-{type(self).crumb_fetches}"
            status = (
                200
                if self.headers.get("Cookie") == "session=fixture-session"
                and self.headers.get("Jenkins-Crumb") == expected_crumb
                else 403
            )
            body = b"ok" if status == 200 else b"forbidden"
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        Handler.base_url = f"http://127.0.0.1:{server.server_port}"  # type: ignore[attr-defined]
        yield Handler
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@contextmanager
def run_login_403_fixture_server() -> Iterator[type[BaseHTTPRequestHandler]]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/login":
                body = (
                    b"<html><body>"
                    b'<form method="post" action="/j_spring_security_check">'
                    b'<input type="hidden" name="from" value="/" />'
                    b'<input type="text" name="j_username" value="" />'
                    b'<input type="password" name="j_password" value="" />'
                    b"</form>"
                    b"</body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path == "/whoAmI/api/json":
                body = json.dumps({"authenticated": False, "name": "anonymous"}).encode("utf-8")
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_response(404)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/j_spring_security_check":
                body = b"missing-overall-read"
                self.send_response(403)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("X-Jenkins", "2.452.3")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        Handler.base_url = f"http://127.0.0.1:{server.server_port}"  # type: ignore[attr-defined]
        yield Handler
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@contextmanager
def run_login_403_authenticated_fixture_server() -> Iterator[type[BaseHTTPRequestHandler]]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"
        crumb_fetches = 0
        received_post_cookies: list[str | None] = []
        received_post_crumbs: list[str | None] = []

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/login":
                body = (
                    b"<html><body>"
                    b'<form method="post" action="/j_spring_security_check">'
                    b'<input type="hidden" name="from" value="/" />'
                    b'<input type="text" name="j_username" value="" />'
                    b'<input type="password" name="j_password" value="" />'
                    b"</form>"
                    b"</body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Set-Cookie", "session=preauth; Path=/")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path == "/whoAmI/api/json":
                if self.headers.get("Cookie") != "session=fixture-session":
                    self.send_response(403)
                    self.end_headers()
                    return
                body = json.dumps({"authenticated": True, "name": "viewer"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path == "/crumbIssuer/api/json":
                if self.headers.get("Cookie") != "session=fixture-session":
                    self.send_response(403)
                    self.end_headers()
                    return
                type(self).crumb_fetches += 1
                body = json.dumps(
                    {
                        "crumbRequestField": "Jenkins-Crumb",
                        "crumb": f"crumb-{type(self).crumb_fetches}",
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_response(404)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/j_spring_security_check":
                body = b"access-denied-after-login"
                self.send_response(403)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Set-Cookie", "session=fixture-session; Path=/")
                self.send_header("X-Required-Permission", "hudson.model.Hudson.Administer")
                self.send_header("X-You-Are-Authenticated-As", "viewer")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            type(self).received_post_cookies.append(self.headers.get("Cookie"))
            type(self).received_post_crumbs.append(self.headers.get("Jenkins-Crumb"))
            body = b"forbidden"
            self.send_response(403)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        Handler.base_url = f"http://127.0.0.1:{server.server_port}"  # type: ignore[attr-defined]
        yield Handler
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_pipeline_fixture_keeps_named_approver_gate_and_production_marker() -> None:
    text = PIPELINE_FIXTURE.read_text(encoding="utf-8")

    assert "PROJECT_C_ALLOWED_APPROVERS" in text
    assert "submitter: env.PROJECT_C_ALLOWED_APPROVERS" in text
    assert "submitterParameter: 'APPROVED_BY'" in text
    assert f"id: '{INPUT_ID}'" in text
    assert AWAITING_APPROVAL_MARKER in text
    assert PRODUCTION_MARKER in text


def test_wrapper_script_uses_placeholder_local_identities_only() -> None:
    text = WRAPPER_SCRIPT.read_text(encoding="utf-8")

    for expected in (
        '$env:JENKINS_LOCAL_ADMIN_ID = "local-admin"',
        '$env:JENKINS_LOCAL_ADMIN_PASSWORD = "placeholder-admin-password"',
        '$env:JENKINS_LOCAL_APPROVER_ID = "local-approver"',
        '$env:JENKINS_LOCAL_APPROVER_PASSWORD = "placeholder-approver-password"',
        '$env:JENKINS_LOCAL_VIEWER_ID = "local-viewer"',
        '$env:JENKINS_LOCAL_VIEWER_PASSWORD = "placeholder-viewer-password"',
    ):
        assert expected in text

    assert "prod-" not in text.lower()
    assert "aws_" not in text.lower()


def test_wrapper_script_overwrites_compose_evidence_files_in_single_pass() -> None:
    text = WRAPPER_SCRIPT.read_text(encoding="utf-8")

    assert "Tee-Object -FilePath $composeUpEvidence -Append" not in text
    assert "Tee-Object -FilePath $composeLogsEvidence -Append" not in text
    assert '$AttemptId = [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")' in text
    assert '$EvidencePrefix = "p5-t04-$AttemptId"' in text
    assert 'Join-Path $EvidenceDir "$EvidencePrefix-compose-build.txt"' in text
    assert 'Join-Path $EvidenceDir "$EvidencePrefix-compose-up.txt"' in text
    assert 'Join-Path $EvidenceDir "$EvidencePrefix-compose-logs.txt"' in text
    assert 'Join-Path $EvidenceDir "$EvidencePrefix-compose-down-before.txt"' in text
    assert 'Join-Path $EvidenceDir "$EvidencePrefix-compose-down-after.txt"' in text
    assert (
        "Write-CommandEvidence -Path $composeBuildEvidence "
        '-Title "docker compose build --pull --no-cache jenkins"' in text
    )
    assert (
        "Write-CommandEvidence -Path $composeUpEvidence "
        '-Title "docker compose up -d --force-recreate jenkins"' in text
    )
    assert (
        "Write-CommandEvidence -Path $composeLogsEvidence "
        '-Title "docker compose logs --tail 200 jenkins"' in text
    )


def test_wrapper_script_captures_runtime_identity_for_single_attempt_diagnosis() -> None:
    text = WRAPPER_SCRIPT.read_text(encoding="utf-8")

    assert 'Join-Path $EvidenceDir "$EvidencePrefix-runtime-identity.txt"' in text
    assert "Write-RuntimeIdentityEvidence -Path $runtimeIdentityEvidence" in text
    assert "docker compose ps -a -q jenkins" in text
    assert "docker compose ps -a jenkins" in text
    assert "docker compose images jenkins" in text
    assert 'New-EvidenceSection -Title "jenkins container id"' in text
    assert 'New-EvidenceSection -Title "jenkins image reference"' in text
    assert 'New-EvidenceSection -Title "jenkins image id"' in text
    assert 'New-EvidenceSection -Title "workspace infra/jenkins/casc.yaml"' in text
    assert 'New-EvidenceSection -Title "workspace infra/jenkins/casc.yaml sha256"' in text
    assert 'New-EvidenceSection -Title "/usr/share/jenkins/ref/casc.yaml"' in text
    assert 'New-EvidenceSection -Title "/usr/share/jenkins/ref/casc.yaml sha256"' in text
    assert 'New-EvidenceSection -Title "/var/jenkins_home/casc.yaml"' in text
    assert 'New-EvidenceSection -Title "/var/jenkins_home/casc.yaml sha256"' in text
    assert "& docker cp $copySource $tempPath *>&1" in text
    assert "--evidence-prefix $EvidencePrefix" in text
    assert "& docker inspect --format '{{.Image}}' $containerId *>&1" in text
    assert "& docker inspect --format '{{.Config.Image}}' $containerId *>&1" in text
    assert "Get-ContentSha256" in text


def test_python_fixture_supports_attempt_scoped_evidence_prefix() -> None:
    text = (ROOT / "scripts" / "p5_t04_unauthorized_fixture.py").read_text(encoding="utf-8")

    assert 'parser.add_argument("--evidence-prefix", default="p5-t04")' in text
    assert 'proof_path = evidence_dir / f"{args.evidence_prefix}-unauthorized-proof.txt"' in text


def test_jenkins_session_posts_crumb_with_same_cookie_session() -> None:
    with run_session_fixture_server() as handler:
        session = JenkinsSession(
            handler.base_url,  # type: ignore[attr-defined]
            username="viewer",
            password="viewer-password",
        )

        status, _, body = session.post_with_crumb("/submit")

    assert status == 200
    assert body == b"ok"
    assert handler.login_gets == 1
    assert handler.login_posts == 1
    assert handler.crumb_fetches == 1
    assert handler.received_post_cookies == ["session=fixture-session"]
    assert handler.received_post_crumbs == ["crumb-1"]
    assert handler.received_post_auth_headers == [None]


def test_jenkins_session_refreshes_crumb_for_each_post() -> None:
    with run_session_fixture_server() as handler:
        session = JenkinsSession(
            handler.base_url,  # type: ignore[attr-defined]
            username="viewer",
            password="viewer-password",
        )

        first_status, _, _ = session.post_with_crumb("/submit")
        second_status, _, _ = session.post_with_crumb("/submit")

    assert first_status == 200
    assert second_status == 200
    assert handler.login_gets == 1
    assert handler.login_posts == 1
    assert handler.crumb_fetches == 2
    assert handler.received_post_cookies == [
        "session=fixture-session",
        "session=fixture-session",
    ]
    assert handler.received_post_crumbs == ["crumb-1", "crumb-2"]
    assert handler.received_post_auth_headers == [None, None]


def test_jenkins_session_rejects_crumb_replayed_from_different_session() -> None:
    with run_session_fixture_server() as handler:
        crumb_session = JenkinsSession(
            handler.base_url,  # type: ignore[attr-defined]
            username="viewer",
            password="viewer-password",
        )
        replay_session = JenkinsSession(
            handler.base_url,  # type: ignore[attr-defined]
            username="viewer",
            password="viewer-password",
        )

        crumb_headers = crumb_session._crumb_headers()
        status, _, body = replay_session.request(
            "/submit",
            method="POST",
            headers=crumb_headers,
            use_auth=False,
        )

    assert status == 403
    assert body == b"forbidden"
    assert handler.crumb_fetches == 1
    assert handler.received_post_cookies == [None]
    assert handler.received_post_crumbs == ["crumb-1"]


def test_jenkins_session_surfaces_login_403_diagnostics() -> None:
    with run_login_403_fixture_server() as handler:
        session = JenkinsSession(
            handler.base_url,  # type: ignore[attr-defined]
            username="viewer",
            password="viewer-password",
        )

        with pytest.raises(RuntimeError) as exc_info:
            session.post_with_crumb("/submit")

    message = str(exc_info.value)
    diagnostics = session.last_auth_diagnostics

    assert "login_status=403" in message
    assert '"Content-Type": "text/plain; charset=utf-8"' in message
    assert '"X-Jenkins": "2.452.3"' in message
    assert 'login_body_summary="missing-overall-read"' in message
    assert diagnostics["login_status"] == 403
    assert diagnostics["login_headers"]["X-Jenkins"] == "2.452.3"
    assert diagnostics["login_body_summary"] == "missing-overall-read"
    assert diagnostics["whoami_status"] == 403


def test_jenkins_session_accepts_authenticated_session_after_login_403() -> None:
    with run_login_403_authenticated_fixture_server() as handler:
        session = JenkinsSession(
            handler.base_url,  # type: ignore[attr-defined]
            username="viewer",
            password="viewer-password",
        )

        status, _, body = session.post_with_crumb("/submit")

    diagnostics = session.last_auth_diagnostics

    assert status == 403
    assert body == b"forbidden"
    assert diagnostics["login_status"] == 403
    assert diagnostics["whoami_status"] == 200
    assert diagnostics["whoami_payload"]["name"] == "viewer"
    assert handler.crumb_fetches == 1
    assert handler.received_post_cookies == ["session=fixture-session"]
    assert handler.received_post_crumbs == ["crumb-1"]


def test_jenkins_session_surfaces_transient_api_parse_failures() -> None:
    class FakeSession(JenkinsSession):
        def __init__(self) -> None:
            super().__init__("http://127.0.0.1:8080", username="viewer", password="viewer-password")

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
            return 503, {"Content-Type": "text/html; charset=utf-8"}, b"<html>starting up</html>"

    session = FakeSession()

    with pytest.raises(RuntimeError) as exc_info:
        session.request_json("/job/project-c-delivery/7/api/json", timeout_seconds=10)

    message = str(exc_info.value)
    assert "Transient Jenkins API parse failure" in message
    assert "status=503" in message
    assert "text/html; charset=utf-8" in message
    assert "starting up" in message


def test_wait_for_build_number_retries_transient_connection_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.calls = 0

        def request_json(
            self, url: str, *, timeout_seconds: int
        ) -> tuple[int, dict[str, str], object]:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError(
                    "Failed to reach Jenkins at http://127.0.0.1:8080/queue/item/1/api/json"
                )
            return 200, {}, {"executable": {"number": 7}}

    monkeypatch.setattr("scripts.p5_t04_unauthorized_fixture.time.sleep", lambda _: None)

    session = FakeSession()

    assert (
        _wait_for_build_number(session, "http://127.0.0.1:8080/queue/item/1", timeout_seconds=5)
        == 7
    )
    assert session.calls == 2


def test_post_input_action_uses_proceed_empty_endpoint_for_approval() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []
            self.base_url = "http://127.0.0.1:8080"

        def _authenticate(self) -> None:
            self.calls.append({"method": "authenticate"})

        def _crumb_headers(self) -> dict[str, str]:
            self.calls.append({"method": "crumb_headers"})
            return {"Jenkins-Crumb": "crumb-123"}

        def _resolve_url(self, url: str) -> str:
            return f"{self.base_url}{url}"

        def request(
            self,
            url: str,
            *,
            method: str = "GET",
            headers: dict[str, str] | None = None,
            data: bytes | None = None,
            timeout_seconds: int,
            use_auth: bool,
        ) -> tuple[int, dict[str, str], bytes]:
            self.calls.append(
                {
                    "method": "request",
                    "url": url,
                    "http_method": method,
                    "headers": headers,
                    "data": data,
                    "timeout_seconds": timeout_seconds,
                    "use_auth": use_auth,
                }
            )
            if method == "POST":
                return 403, {}, b"forbidden"
            body = (
                b'<html><body><form method="post" action="Production-approval/submit">'
                b'<button name="proceed" value="Promote">Promote</button>'
                b'<button name="abort" value="Abort">Abort</button>'
                b"</form></body></html>"
            )
            return 200, {"Content-Type": "text/html; charset=utf-8"}, body

    session = FakeSession()

    status, headers, body = _post_input_action(
        job_name="project-c-delivery",
        build_number=7,
        action="proceedEmpty",
        session=session,  # type: ignore[arg-type]
    )

    assert (status, headers, body) == (403, {}, b"forbidden")
    assert session.calls == [
        {
            "method": "authenticate",
        },
        {
            "method": "request",
            "url": "/job/project-c-delivery/7/input/",
            "http_method": "GET",
            "headers": None,
            "data": None,
            "timeout_seconds": 10,
            "use_auth": False,
        },
        {
            "method": "crumb_headers",
        },
        {
            "method": "request",
            "url": "/job/project-c-delivery/7/input/Production-approval/submit",
            "http_method": "POST",
            "headers": {
                "Jenkins-Crumb": "crumb-123",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://127.0.0.1:8080",
                "Referer": "http://127.0.0.1:8080/job/project-c-delivery/7/input/",
            },
            "data": (
                b"proceed=Promote&Jenkins-Crumb=crumb-123&"
                b"json=%7B%22proceed%22%3A%22Promote%22%2C%22abort%22%3A%22Abort%22%2C%22Jenkins-Crumb%22%3A%22crumb-123%22%7D"
            ),
            "timeout_seconds": 10,
            "use_auth": False,
        },
    ]


def test_post_input_action_rejects_missing_runtime_submit_form() -> None:
    class FakeSession:
        def _authenticate(self) -> None:
            return

        def _crumb_headers(self) -> dict[str, str]:
            raise AssertionError(
                "_crumb_headers should not be called when no approval form is present"
            )

        def request(
            self,
            url: str,
            *,
            method: str = "GET",
            headers: dict[str, str] | None = None,
            data: bytes | None = None,
            timeout_seconds: int,
            use_auth: bool,
        ) -> tuple[int, dict[str, str], bytes]:
            return (
                200,
                {"Content-Type": "text/html; charset=utf-8"},
                b"<html><body><form action='noop'></form></body></html>",
            )

    with pytest.raises(RuntimeError, match="approval submit form"):
        _post_input_action(
            job_name="project-c-delivery",
            build_number=7,
            action="proceedEmpty",
            session=FakeSession(),  # type: ignore[arg-type]
        )


def test_post_input_action_uses_build_stop_for_abort() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def post_with_crumb(
            self, url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None
        ) -> tuple[int, dict[str, str], bytes]:
            self.calls.append({"url": url, "data": data, "headers": headers})
            return 302, {"Location": "/job/project-c-delivery/7/"}, b""

    session = FakeSession()

    status, headers, body = _post_input_action(
        job_name="project-c-delivery",
        build_number=7,
        action="abort",
        session=session,  # type: ignore[arg-type]
    )

    assert status == 302
    assert headers["Location"] == "/job/project-c-delivery/7/"
    assert body == b""
    assert session.calls == [
        {
            "url": "/job/project-c-delivery/7/stop",
            "data": None,
            "headers": None,
        }
    ]


def test_trigger_build_falls_back_to_next_build_number_when_location_missing() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def request_json(
            self, url: str, *, timeout_seconds: int
        ) -> tuple[int, dict[str, str], object]:
            self.calls.append(("request_json", url))
            return 200, {}, {"nextBuildNumber": 11}

        def post_with_crumb(
            self, url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None
        ) -> tuple[int, dict[str, str], bytes]:
            self.calls.append(("post_with_crumb", url))
            return 201, {}, b""

    session = FakeSession()

    queue_url, build_number_hint = _trigger_build(
        job_name="project-c-delivery",
        session=session,  # type: ignore[arg-type]
    )

    assert queue_url is None
    assert build_number_hint == 11
    assert session.calls == [
        ("request_json", "/job/project-c-delivery/api/json"),
        ("post_with_crumb", "/job/project-c-delivery/buildWithParameters?PROMOTE_PRODUCTION=true"),
    ]


def test_wait_for_input_gate_retries_transient_connection_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.console_calls = 0
            self.json_calls = 0
            self.base_url = "http://127.0.0.1:8080"

        def request(self, url: str, *, timeout_seconds: int) -> tuple[int, dict[str, str], bytes]:
            self.console_calls += 1
            if self.console_calls == 1:
                raise RuntimeError(
                    "Transient Jenkins connection failure at http://127.0.0.1:8080/job/project-c-delivery/7/consoleText"
                )
            return 200, {}, AWAITING_APPROVAL_MARKER.encode("utf-8")

        def request_json(
            self, url: str, *, timeout_seconds: int
        ) -> tuple[int, dict[str, str], object]:
            self.json_calls += 1
            return 200, {}, {"building": True}

    monkeypatch.setattr("scripts.p5_t04_unauthorized_fixture.time.sleep", lambda _: None)

    session = FakeSession()

    payload = _wait_for_input_gate(
        job_name="project-c-delivery",
        build_number=7,
        session=session,  # type: ignore[arg-type]
        timeout_seconds=5,
    )

    assert payload == {"building": True}
    assert session.console_calls == 2
    assert session.json_calls == 1


def test_wait_for_build_result_retries_transient_api_parse_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.calls = 0
            self.base_url = "http://127.0.0.1:8080"

        def request_json(
            self, url: str, *, timeout_seconds: int
        ) -> tuple[int, dict[str, str], object]:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError(
                    "Transient Jenkins API parse failure at "
                    "http://127.0.0.1:8080/job/project-c-delivery/7/api/json"
                )
            return 200, {}, {"building": False, "result": "ABORTED"}

    monkeypatch.setattr("scripts.p5_t04_unauthorized_fixture.time.sleep", lambda _: None)

    session = FakeSession()

    payload = _wait_for_build_result(
        job_name="project-c-delivery",
        build_number=7,
        session=session,  # type: ignore[arg-type]
        timeout_seconds=5,
    )

    assert payload == {"building": False, "result": "ABORTED"}
    assert session.calls == 2


def test_job_config_xml_embeds_local_only_description() -> None:
    xml = build_job_config_xml("echo 'hello'")

    assert "<description>P5-T04 local-only unauthorized approval fixture.</description>" in xml
    assert "<name>PROMOTE_PRODUCTION</name>" in xml
    assert "<hudson.model.BooleanParameterDefinition>" in xml
    assert "<defaultValue>false</defaultValue>" in xml
    assert "&quot;" not in xml
    assert "<script>echo &#x27;hello&#x27;</script>" in xml


def test_evaluate_fixture_outcome_accepts_expected_rejection() -> None:
    errors = evaluate_fixture_outcome(
        unauthorized_status=403,
        pre_abort_build={"building": True},
        final_build={"result": "ABORTED"},
        console_text="some log\n" + AWAITING_APPROVAL_MARKER,
    )

    assert errors == []


def test_evaluate_fixture_outcome_accepts_runtime_400_rejection() -> None:
    errors = evaluate_fixture_outcome(
        unauthorized_status=400,
        pre_abort_build={"building": True},
        final_build={"result": "ABORTED"},
        console_text="some log\n" + AWAITING_APPROVAL_MARKER,
    )

    assert errors == []


def test_evaluate_fixture_outcome_rejects_production_continuation() -> None:
    errors = evaluate_fixture_outcome(
        unauthorized_status=200,
        pre_abort_build={"building": False},
        final_build={"result": "SUCCESS"},
        console_text=f"{AWAITING_APPROVAL_MARKER}\n{PRODUCTION_MARKER}",
    )

    assert any("400 or 403" in error for error in errors)
    assert any("Production marker" in error for error in errors)
    assert any("paused at the approval gate" in error for error in errors)
    assert any("fixture cleanup" in error for error in errors)
