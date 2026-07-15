"""Verify deployed digest identity and recovery suite for Project C.

Promotion and recovery gates bind the immutable image digest to an expected
registry/repository identity. Selecting an arbitrary first RepoDigest is not a
verified claim. Staging digests are never accepted as production rollback targets.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import smoke_test  # noqa: E402

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
CHECK_NAMES = ("deployed_digest", "health", "version", "business_behavior")


class VerificationError(ValueError):
    """Raised for invalid verification inputs."""


def normalize_digest(value: str) -> str:
    digest = (value or "").strip()
    if digest.startswith("sha256:") and DIGEST_RE.fullmatch(digest):
        return digest
    if re.fullmatch(r"[0-9a-f]{64}", digest):
        return f"sha256:{digest}"
    raise VerificationError(f"invalid digest identity: {value!r}")


def parse_image_ref(image_ref: str) -> dict[str, str]:
    """Parse registry/repository[@digest|:tag] style references."""
    ref = (image_ref or "").strip()
    if not ref:
        raise VerificationError("image reference is empty")

    digest = ""
    tag = ""
    name = ref
    if "@" in ref:
        name, digest = ref.rsplit("@", 1)
        digest = normalize_digest(digest)
    elif ":" in ref.split("/")[-1]:
        name, tag = ref.rsplit(":", 1)

    if "/" in name:
        registry, repository = name.split("/", 1)
    else:
        registry, repository = "", name

    if not repository:
        raise VerificationError(f"image reference missing repository: {image_ref!r}")

    return {
        "registry": registry,
        "repository": repository,
        "digest": digest,
        "tag": tag,
        "name": name,
    }


def canonical_repo_digest(registry: str, repository: str, digest: str) -> str:
    digest = normalize_digest(digest)
    repository = repository.strip().strip("/")
    registry = registry.strip().strip("/")
    if not repository:
        raise VerificationError("expected repository is required for digest identity binding")
    if registry:
        return f"{registry}/{repository}@{digest}"
    return f"{repository}@{digest}"


def select_matching_repo_digest(
    repo_digests: list[str],
    *,
    expected_registry: str,
    expected_repository: str,
    expected_digest: str,
) -> str:
    """Return the RepoDigest that matches expected registry/repository/digest.

    Fails closed when no identity-bound match exists. Never returns an arbitrary
    first RepoDigest.
    """
    expected = canonical_repo_digest(expected_registry, expected_repository, expected_digest)
    expected_digest = normalize_digest(expected_digest)
    matches = [item.strip() for item in repo_digests if item and item.strip() == expected]
    if len(matches) == 1:
        return matches[0]

    # Allow digest-only equality only when the matched entry also shares name identity.
    name_matches = []
    for item in repo_digests:
        raw = (item or "").strip()
        if not raw or "@" not in raw:
            continue
        try:
            parsed = parse_image_ref(raw)
        except VerificationError:
            continue
        if parsed["digest"] != expected_digest:
            continue
        if parsed["repository"] != expected_repository.strip().strip("/"):
            continue
        if (parsed["registry"] or "") != (expected_registry or "").strip().strip("/"):
            continue
        name_matches.append(raw)

    if len(name_matches) == 1:
        return name_matches[0]
    if not repo_digests:
        raise VerificationError(
            "no RepoDigests observed; cannot bind deployed digest to registry/repository identity"
        )
    raise VerificationError(
        "deployed digest does not match expected registry/repository identity "
        f"(expected {expected}; observed {repo_digests!r})"
    )


def validate_production_promotion_gate(
    *,
    candidate_digest: str,
    verified_rollback_digest: str = "",
    verified_rollback_commit: str = "",
    verified_rollback_verified_at: str = "",
    verified_rollback_source_release: str = "",
    verified_rollback_environment: str = "",
    first_release_decision: str = "",
    first_release_decided_by: str = "",
    first_release_decided_at: str = "",
    first_release_rationale: str = "",
    first_release_accepted_risk: str = "",
) -> list[str]:
    """Fail closed unless a verified production rollback target or first-release decision exists."""
    failures: list[str] = []
    candidate = ""
    try:
        candidate = normalize_digest(candidate_digest)
    except VerificationError as error:
        failures.append(str(error))
        return failures

    has_target = bool((verified_rollback_digest or "").strip())
    has_decision = bool((first_release_decision or "").strip())

    if has_target and has_decision:
        failures.append(
            "production promotion must supply exactly one of verified rollback target "
            "or first-release decision"
        )
        return failures

    if not has_target and not has_decision:
        failures.append(
            "production promotion blocked: no verified rollback target and "
            "no first-release decision"
        )
        return failures

    if has_target:
        try:
            target = normalize_digest(verified_rollback_digest)
        except VerificationError as error:
            failures.append(f"verified rollback target invalid: {error}")
            return failures
        if target == candidate:
            failures.append("verified rollback target must not be self-referential")
        environment = (verified_rollback_environment or "").strip().lower()
        if environment != "production":
            failures.append(
                "verified rollback target environment must be production "
                f"(got {verified_rollback_environment!r}; staging-as-prior is forbidden)"
            )
        if not (verified_rollback_commit or "").strip():
            failures.append("verified rollback target missing commit_sha")
        if not (verified_rollback_verified_at or "").strip():
            failures.append("verified rollback target missing verified_at")
        if not (verified_rollback_source_release or "").strip():
            failures.append("verified rollback target missing source_release_id")
        return failures

    decision = (first_release_decision or "").strip()
    if decision != "first_release_no_rollback_target":
        failures.append(
            f"first-release decision must be 'first_release_no_rollback_target' (got {decision!r})"
        )
    if not (first_release_decided_by or "").strip():
        failures.append("first-release decision missing decided_by")
    if not (first_release_decided_at or "").strip():
        failures.append("first-release decision missing decided_at")
    if not (first_release_rationale or "").strip():
        failures.append("first-release decision missing rationale")
    if not (first_release_accepted_risk or "").strip():
        failures.append("first-release decision missing accepted_risk")
    return failures


def classify_smoke_checks(smoke_payload: dict[str, Any]) -> dict[str, str]:
    failures = [str(item) for item in smoke_payload.get("failures", [])]
    health_fail = any(
        item.startswith("readiness ") or item.startswith("liveness ") for item in failures
    )
    version_fail = any(
        item.startswith("version ")
        or item.startswith("expected SHA ")
        or item.startswith("expected environment ")
        for item in failures
    )
    business_fail = any(item.startswith("quote ") for item in failures)
    return {
        "health": "fail" if health_fail else "pass",
        "version": "fail" if version_fail else "pass",
        "business_behavior": "fail" if business_fail else "pass",
    }


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True)


def compose_container_id(service: str) -> str:
    completed = run_command(["docker", "compose", "--profile", "deploy", "ps", "-q", service])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise VerificationError(f"docker compose ps failed for {service}: {detail}")
    container_id = completed.stdout.strip().splitlines()
    if not container_id or not container_id[0].strip():
        raise VerificationError(f"no running container for compose service {service}")
    return container_id[0].strip()


def image_repo_digests(image_id_or_ref: str) -> list[str]:
    completed = run_command(
        ["docker", "image", "inspect", "--format", "{{json .RepoDigests}}", image_id_or_ref]
    )
    if completed.returncode != 0:
        raise VerificationError(
            f"docker image inspect failed: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    try:
        payload = json.loads(completed.stdout.strip() or "[]")
    except json.JSONDecodeError as error:
        raise VerificationError(f"invalid RepoDigests JSON: {error}") from error
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise VerificationError("RepoDigests payload must be a list")
    return [str(item) for item in payload]


def container_image_id(container_id: str) -> str:
    completed = run_command(["docker", "inspect", "--format", "{{.Image}}", container_id])
    if completed.returncode != 0:
        raise VerificationError(
            f"docker inspect failed: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    image_id = completed.stdout.strip()
    if not image_id:
        raise VerificationError("container image id is empty")
    return image_id


def verify_deployed_digest(
    *,
    compose_service: str,
    expected_digest: str,
    expected_registry: str,
    expected_repository: str,
) -> dict[str, Any]:
    container_id = compose_container_id(compose_service)
    image_id = container_image_id(container_id)
    repo_digests = image_repo_digests(image_id)
    matched = select_matching_repo_digest(
        repo_digests,
        expected_registry=expected_registry,
        expected_repository=expected_repository,
        expected_digest=expected_digest,
    )
    return {
        "container_id": container_id,
        "image_id": image_id,
        "repo_digests": repo_digests,
        "matched_repo_digest": matched,
        "expected": canonical_repo_digest(expected_registry, expected_repository, expected_digest),
    }


def run_verification(
    *,
    base_url: str,
    compose_service: str,
    expected_digest: str,
    expected_registry: str,
    expected_repository: str,
    expected_sha: str = "",
    expected_environment: str = "",
    mode: str = "verify",
) -> dict[str, Any]:
    checks = {name: "fail" for name in CHECK_NAMES}
    failures: list[str] = []
    digest_proof: dict[str, Any] | None = None

    try:
        digest_proof = verify_deployed_digest(
            compose_service=compose_service,
            expected_digest=expected_digest,
            expected_registry=expected_registry,
            expected_repository=expected_repository,
        )
        checks["deployed_digest"] = "pass"
    except VerificationError as error:
        failures.append(f"deployed digest failed: {error}")
        checks["deployed_digest"] = "fail"

    smoke_argv = ["--base-url", base_url]
    if expected_sha:
        smoke_argv.extend(["--expected-sha", expected_sha])
    if expected_environment:
        smoke_argv.extend(["--expected-environment", expected_environment])

    # Capture smoke JSON without exiting the process.
    from contextlib import redirect_stdout
    from io import StringIO

    buffer = StringIO()
    with redirect_stdout(buffer):
        smoke_rc = smoke_test.main(smoke_argv)
    smoke_raw = buffer.getvalue().strip()
    try:
        smoke_payload = (
            json.loads(smoke_raw) if smoke_raw else {"failures": ["smoke produced no JSON"]}
        )
    except json.JSONDecodeError:
        smoke_payload = {"failures": [f"smoke produced invalid JSON: {smoke_raw!r}"]}
        smoke_rc = 1

    smoke_checks = classify_smoke_checks(smoke_payload if isinstance(smoke_payload, dict) else {})
    checks.update(smoke_checks)
    for item in smoke_payload.get("failures", []) if isinstance(smoke_payload, dict) else []:
        failures.append(str(item))
    if smoke_rc != 0 and not smoke_payload.get("failures"):
        failures.append("smoke verification failed without structured failures")

    # Skipped checks are failures for recovery/verify claims.
    for name in CHECK_NAMES:
        if checks.get(name) not in {"pass", "fail"}:
            checks[name] = "fail"
            failures.append(f"check {name} was skipped")

    ok = all(checks[name] == "pass" for name in CHECK_NAMES) and not failures
    return {
        "mode": mode,
        "ok": ok,
        "checks": checks,
        "failures": failures,
        "digest_proof": digest_proof,
        "smoke": smoke_payload,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Project C deployment verification and production promotion gate"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gate = subparsers.add_parser(
        "promotion-gate",
        help="Fail closed unless verified rollback target or first-release decision is present",
    )
    gate.add_argument("--candidate-digest", required=True)
    gate.add_argument("--verified-rollback-digest", default="")
    gate.add_argument("--verified-rollback-commit", default="")
    gate.add_argument("--verified-rollback-verified-at", default="")
    gate.add_argument("--verified-rollback-source-release", default="")
    gate.add_argument("--verified-rollback-environment", default="")
    gate.add_argument("--first-release-decision", default="")
    gate.add_argument("--first-release-decided-by", default="")
    gate.add_argument("--first-release-decided-at", default="")
    gate.add_argument("--first-release-rationale", default="")
    gate.add_argument("--first-release-accepted-risk", default="")

    verify = subparsers.add_parser(
        "verify",
        help="Verify deployed digest identity plus health/version/business behavior",
    )
    verify.add_argument("--base-url", required=True)
    verify.add_argument("--compose-service", required=True, choices=("staging", "production"))
    verify.add_argument("--expected-digest", required=True)
    verify.add_argument("--expected-registry", required=True)
    verify.add_argument("--expected-repository", required=True)
    verify.add_argument("--expected-sha", default="")
    verify.add_argument("--expected-environment", default="")
    verify.add_argument(
        "--mode",
        default="verify",
        choices=("verify", "recovery"),
        help="recovery mode reuses the full suite; any failed/skipped check fails the claim",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "promotion-gate":
        failures = validate_production_promotion_gate(
            candidate_digest=args.candidate_digest,
            verified_rollback_digest=args.verified_rollback_digest,
            verified_rollback_commit=args.verified_rollback_commit,
            verified_rollback_verified_at=args.verified_rollback_verified_at,
            verified_rollback_source_release=args.verified_rollback_source_release,
            verified_rollback_environment=args.verified_rollback_environment,
            first_release_decision=args.first_release_decision,
            first_release_decided_by=args.first_release_decided_by,
            first_release_decided_at=args.first_release_decided_at,
            first_release_rationale=args.first_release_rationale,
            first_release_accepted_risk=args.first_release_accepted_risk,
        )
        payload = {"ok": not failures, "failures": failures}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if not failures else 1

    if args.command == "verify":
        try:
            expected_digest = normalize_digest(args.expected_digest)
        except VerificationError as error:
            print(json.dumps({"ok": False, "failures": [str(error)]}, indent=2, ensure_ascii=False))
            return 1
        payload = run_verification(
            base_url=args.base_url,
            compose_service=args.compose_service,
            expected_digest=expected_digest,
            expected_registry=args.expected_registry,
            expected_repository=args.expected_repository,
            expected_sha=args.expected_sha,
            expected_environment=args.expected_environment or args.compose_service,
            mode=args.mode,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if payload["ok"] else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
