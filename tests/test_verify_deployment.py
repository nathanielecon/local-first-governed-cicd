import json
from typing import Any

import pytest
from scripts import verify_deployment as vd

DIGEST_A = "sha256:" + ("a" * 64)
DIGEST_B = "sha256:" + ("b" * 64)
DIGEST_C = "sha256:" + ("c" * 64)


def test_parse_image_ref_with_registry_and_digest() -> None:
    parsed = vd.parse_image_ref(f"localhost:5000/delivery-api@{DIGEST_A}")
    assert parsed["registry"] == "localhost:5000"
    assert parsed["repository"] == "delivery-api"
    assert parsed["digest"] == DIGEST_A


def test_select_matching_repo_digest_binds_registry_and_repository() -> None:
    matched = vd.select_matching_repo_digest(
        [
            f"example.invalid/other@{DIGEST_A}",
            f"localhost:5000/delivery-api@{DIGEST_A}",
        ],
        expected_registry="localhost:5000",
        expected_repository="delivery-api",
        expected_digest=DIGEST_A,
    )
    assert matched == f"localhost:5000/delivery-api@{DIGEST_A}"


def test_select_matching_repo_digest_rejects_arbitrary_first_entry() -> None:
    with pytest.raises(vd.VerificationError, match="does not match expected registry/repository"):
        vd.select_matching_repo_digest(
            [f"evil.example/other@{DIGEST_A}", f"localhost:5000/delivery-api@{DIGEST_B}"],
            expected_registry="localhost:5000",
            expected_repository="delivery-api",
            expected_digest=DIGEST_A,
        )


def test_select_matching_repo_digest_rejects_empty_repo_digests() -> None:
    with pytest.raises(vd.VerificationError, match="no RepoDigests observed"):
        vd.select_matching_repo_digest(
            [],
            expected_registry="localhost:5000",
            expected_repository="delivery-api",
            expected_digest=DIGEST_A,
        )


def test_promotion_gate_fails_without_target_or_decision() -> None:
    failures = vd.validate_production_promotion_gate(candidate_digest=DIGEST_A)
    assert failures == [
        "production promotion blocked: no verified rollback target and no first-release decision"
    ]


def test_promotion_gate_rejects_staging_as_prior() -> None:
    failures = vd.validate_production_promotion_gate(
        candidate_digest=DIGEST_A,
        verified_rollback_digest=DIGEST_B,
        verified_rollback_commit="c" * 40,
        verified_rollback_verified_at="2026-07-12T00:00:00Z",
        verified_rollback_source_release="prior-rel",
        verified_rollback_environment="staging",
    )
    assert any("staging-as-prior is forbidden" in item for item in failures)


def test_promotion_gate_rejects_self_referential_target() -> None:
    failures = vd.validate_production_promotion_gate(
        candidate_digest=DIGEST_A,
        verified_rollback_digest=DIGEST_A,
        verified_rollback_commit="c" * 40,
        verified_rollback_verified_at="2026-07-12T00:00:00Z",
        verified_rollback_source_release="prior-rel",
        verified_rollback_environment="production",
    )
    assert "verified rollback target must not be self-referential" in failures


def test_promotion_gate_accepts_verified_production_target() -> None:
    failures = vd.validate_production_promotion_gate(
        candidate_digest=DIGEST_A,
        verified_rollback_digest=DIGEST_B,
        verified_rollback_commit="c" * 40,
        verified_rollback_verified_at="2026-07-12T00:00:00Z",
        verified_rollback_source_release="prior-rel",
        verified_rollback_environment="production",
    )
    assert failures == []


def test_promotion_gate_accepts_first_release_decision() -> None:
    failures = vd.validate_production_promotion_gate(
        candidate_digest=DIGEST_A,
        first_release_decision="first_release_no_rollback_target",
        first_release_decided_by="local-approver",
        first_release_decided_at="2026-07-13T00:00:00Z",
        first_release_rationale="No verified prior production digest exists.",
        first_release_accepted_risk="Rollback unavailable for this first release.",
    )
    assert failures == []


def test_promotion_gate_rejects_both_target_and_decision() -> None:
    failures = vd.validate_production_promotion_gate(
        candidate_digest=DIGEST_A,
        verified_rollback_digest=DIGEST_B,
        verified_rollback_commit="c" * 40,
        verified_rollback_verified_at="2026-07-12T00:00:00Z",
        verified_rollback_source_release="prior-rel",
        verified_rollback_environment="production",
        first_release_decision="first_release_no_rollback_target",
        first_release_decided_by="local-approver",
        first_release_decided_at="2026-07-13T00:00:00Z",
        first_release_rationale="n/a",
        first_release_accepted_risk="n/a",
    )
    assert any("exactly one" in item for item in failures)


def test_promotion_gate_cli_fail_closed(capsys: pytest.CaptureFixture[str]) -> None:
    rc = vd.main(["promotion-gate", "--candidate-digest", DIGEST_A])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert any("no verified rollback target" in item for item in payload["failures"])


def test_run_verification_fails_when_any_recovery_check_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_deployed_digest(**kwargs: Any) -> dict[str, Any]:
        return {
            "container_id": "abc",
            "image_id": "sha256:img",
            "repo_digests": [f"localhost:5000/delivery-api@{DIGEST_B}"],
            "matched_repo_digest": f"localhost:5000/delivery-api@{DIGEST_B}",
            "expected": f"localhost:5000/delivery-api@{DIGEST_B}",
        }

    def fake_smoke_main(argv: list[str] | None = None) -> int:
        print(
            json.dumps(
                {
                    "failures": ["readiness failed: 503 {'status': 'not-ready'}"],
                    "checks": {
                        "health": "fail",
                        "version": "pass",
                        "business_behavior": "pass",
                    },
                }
            )
        )
        return 1

    monkeypatch.setattr(vd, "verify_deployed_digest", fake_verify_deployed_digest)
    monkeypatch.setattr(vd.smoke_test, "main", fake_smoke_main)

    payload = vd.run_verification(
        base_url="http://example.test",
        compose_service="production",
        expected_digest=DIGEST_B,
        expected_registry="localhost:5000",
        expected_repository="delivery-api",
        expected_sha="abc123",
        mode="recovery",
    )
    assert payload["ok"] is False
    assert payload["checks"]["deployed_digest"] == "pass"
    assert payload["checks"]["health"] == "fail"
    assert any("readiness failed" in item for item in payload["failures"])


def test_run_verification_fails_on_digest_identity_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_deployed_digest(**kwargs: Any) -> dict[str, Any]:
        raise vd.VerificationError(
            "deployed digest does not match expected registry/repository identity"
        )

    def fake_smoke_main(argv: list[str] | None = None) -> int:
        print(
            json.dumps(
                {
                    "failures": [],
                    "checks": {
                        "health": "pass",
                        "version": "pass",
                        "business_behavior": "pass",
                    },
                }
            )
        )
        return 0

    monkeypatch.setattr(vd, "verify_deployed_digest", fake_verify_deployed_digest)
    monkeypatch.setattr(vd.smoke_test, "main", fake_smoke_main)

    payload = vd.run_verification(
        base_url="http://example.test",
        compose_service="production",
        expected_digest=DIGEST_C,
        expected_registry="localhost:5000",
        expected_repository="delivery-api",
        mode="recovery",
    )
    assert payload["ok"] is False
    assert payload["checks"]["deployed_digest"] == "fail"
    assert payload["checks"]["health"] == "pass"


def test_run_verification_passes_full_suite(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_verify_deployed_digest(**kwargs: Any) -> dict[str, Any]:
        return {
            "container_id": "abc",
            "image_id": "sha256:img",
            "repo_digests": [f"localhost:5000/delivery-api@{DIGEST_B}"],
            "matched_repo_digest": f"localhost:5000/delivery-api@{DIGEST_B}",
            "expected": f"localhost:5000/delivery-api@{DIGEST_B}",
        }

    def fake_smoke_main(argv: list[str] | None = None) -> int:
        print(
            json.dumps(
                {
                    "failures": [],
                    "checks": {
                        "health": "pass",
                        "version": "pass",
                        "business_behavior": "pass",
                    },
                }
            )
        )
        return 0

    monkeypatch.setattr(vd, "verify_deployed_digest", fake_verify_deployed_digest)
    monkeypatch.setattr(vd.smoke_test, "main", fake_smoke_main)

    payload = vd.run_verification(
        base_url="http://example.test",
        compose_service="production",
        expected_digest=DIGEST_B,
        expected_registry="localhost:5000",
        expected_repository="delivery-api",
        expected_sha="abc123",
        mode="recovery",
    )
    assert payload["ok"] is True
    assert payload["checks"] == {
        "deployed_digest": "pass",
        "health": "pass",
        "version": "pass",
        "business_behavior": "pass",
    }
