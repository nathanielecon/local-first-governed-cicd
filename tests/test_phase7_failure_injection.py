"""Phase 7 failure-injection negative contracts (local-only / fake credentials)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts import phase7_run_lanes as p7
from scripts import smoke_test
from scripts import verify_deployment as vd

ROOT = Path(__file__).resolve().parents[1]
DIGEST_A = "sha256:" + ("a" * 64)
DIGEST_B = "sha256:" + ("b" * 64)


def test_fake_secret_fixture_is_documented_example_only() -> None:
    assert "ghp_012345678901234567890123456789012345" in p7.FAKE_SECRET_BODY
    assert (
        "NOT a real credential" in p7.FAKE_SECRET_BODY
        or "test signature" in p7.FAKE_SECRET_BODY.lower()
    )
    # Single synthetic PAT shape only — no additional live-looking tokens.
    assert p7.FAKE_SECRET_BODY.count("ghp_") == 1


def test_mutable_tag_drift_keeps_recorded_digest() -> None:
    matched = vd.select_matching_repo_digest(
        [
            f"localhost:5000/delivery-api@{DIGEST_B}",
            f"localhost:5000/delivery-api@{DIGEST_A}",
        ],
        expected_registry="localhost:5000",
        expected_repository="delivery-api",
        expected_digest=DIGEST_A,
    )
    assert matched == f"localhost:5000/delivery-api@{DIGEST_A}"


def test_mutable_tag_drift_rejects_unrelated_repo() -> None:
    with pytest.raises(vd.VerificationError):
        vd.select_matching_repo_digest(
            [f"evil.example/other@{DIGEST_B}"],
            expected_registry="localhost:5000",
            expected_repository="delivery-api",
            expected_digest=DIGEST_A,
        )


def test_not_ready_blocks_smoke_and_promotion_gate(capsys: pytest.CaptureFixture[str]) -> None:
    server, base = p7._serve("not-ready")
    try:
        rc = smoke_test.main(
            [
                "--base-url",
                base,
                "--expected-sha",
                "abc123deadbeef",
                "--expected-environment",
                "staging",
            ]
        )
        payload = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert any("readiness" in item for item in payload["failures"])
        promo = vd.validate_production_promotion_gate(candidate_digest=DIGEST_A)
        assert promo
        assert any("no verified rollback target" in item for item in promo)
    finally:
        server.shutdown()
        server.server_close()


def test_missing_provenance_rejects_sha_mismatch(capsys: pytest.CaptureFixture[str]) -> None:
    server, base = p7._serve("ready", git_sha="actual-sha-111")
    try:
        rc = smoke_test.main(["--base-url", base, "--expected-sha", "expected-sha-999"])
        payload = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert any("expected SHA" in item for item in payload["failures"])
    finally:
        server.shutdown()
        server.server_close()


def test_phase5_unauthorized_proof_markers_present() -> None:
    proof = ROOT / "evidence" / "phase-5" / "p5-t04-manual-verify2-unauthorized-proof.txt"
    assert proof.is_file()
    text = proof.read_text(encoding="utf-8", errors="replace")
    assert "unauthorized_status=400" in text
    assert "You need to be local-approver to submit this." in text
    assert "FIXTURE_AWAITING_APPROVAL" in text
    assert "ABORTED" in text
    assert "local-viewer" in text


def test_runbook_documents_docker_isolation_cues() -> None:
    runbook = (ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
    assert "docker compose ps jenkins" in runbook
    assert "/var/run/docker.sock" in runbook
    assert "local-only" in runbook


def test_production_regression_records_failure_and_recovers_by_digest(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    prior = DIGEST_B
    candidate = "sha256:" + ("c" * 64)
    fail_server, fail_base = p7._serve("not-ready", git_sha="regress-sha", environment="production")
    try:
        fail_rc = smoke_test.main(
            [
                "--base-url",
                fail_base,
                "--expected-sha",
                "regress-sha",
                "--expected-environment",
                "production",
            ]
        )
        fail_payload = json.loads(capsys.readouterr().out)
        assert fail_rc == 1
        assert any("readiness" in item for item in fail_payload["failures"])
    finally:
        fail_server.shutdown()
        fail_server.server_close()

    matched = vd.select_matching_repo_digest(
        [
            f"localhost:5000/delivery-api@{candidate}",
            f"localhost:5000/delivery-api@{prior}",
        ],
        expected_registry="localhost:5000",
        expected_repository="delivery-api",
        expected_digest=prior,
    )
    assert matched == f"localhost:5000/delivery-api@{prior}"

    recover_server, recover_base = p7._serve("ready", git_sha="prior-sha", environment="production")
    try:

        def fake_verify_deployed_digest(**kwargs: object) -> dict[str, object]:
            return {
                "container_id": "fixture",
                "image_id": "sha256:img",
                "repo_digests": [f"localhost:5000/delivery-api@{prior}"],
                "matched_repo_digest": f"localhost:5000/delivery-api@{prior}",
                "expected": f"localhost:5000/delivery-api@{prior}",
            }

        monkeypatch.setattr(vd, "verify_deployed_digest", fake_verify_deployed_digest)
        recovery = vd.run_verification(
            base_url=recover_base,
            compose_service="production",
            expected_digest=prior,
            expected_registry="localhost:5000",
            expected_repository="delivery-api",
            expected_sha="prior-sha",
            expected_environment="production",
            mode="recovery",
        )
        assert recovery["ok"] is True
        assert recovery["checks"] == {
            "deployed_digest": "pass",
            "health": "pass",
            "version": "pass",
            "business_behavior": "pass",
        }
    finally:
        recover_server.shutdown()
        recover_server.server_close()
