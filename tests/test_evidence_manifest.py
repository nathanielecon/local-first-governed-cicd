"""Tests for append-only release evidence and derived summary validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts import evidence, project_cli

DIGEST = "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
OTHER_DIGEST = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
COMMIT = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _base_event(
    event_type: str,
    *,
    event_id: str,
    release_id: str = "rel-1",
    digest: str = DIGEST,
    commit_sha: str = COMMIT,
    environment: str = "local",
    result: str = "pass",
    details: dict | None = None,
    recorded_at: str = "2026-07-13T12:00:00Z",
    actor: str = "tester",
) -> dict:
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "release_id": release_id,
        "commit_sha": commit_sha,
        "environment": environment,
        "recorded_at": recorded_at,
        "actor": actor,
        "result": result,
        "details": details or {},
    }
    if digest:
        event["image_digest"] = digest
    return event


def _happy_path_events(release_id: str = "rel-1") -> list[dict]:
    return [
        _base_event(
            "build_published",
            event_id="e1",
            release_id=release_id,
            details={"image_reference": "local/app:rel-1"},
            recorded_at="2026-07-13T12:00:00Z",
        ),
        _base_event(
            "staging_deployed",
            event_id="e2",
            release_id=release_id,
            environment="staging",
            recorded_at="2026-07-13T12:01:00Z",
        ),
        _base_event(
            "staging_verified",
            event_id="e3",
            release_id=release_id,
            environment="staging",
            recorded_at="2026-07-13T12:02:00Z",
            details={"checks": {"deployed_digest": "pass", "health": "pass"}},
        ),
        _base_event(
            "production_approval",
            event_id="e4",
            release_id=release_id,
            environment="production",
            recorded_at="2026-07-13T12:03:00Z",
            actor="approver.jane",
            details={"approver_id": "approver.jane", "approved_at": "2026-07-13T12:03:00Z"},
        ),
        _base_event(
            "first_release_decision",
            event_id="e5",
            release_id=release_id,
            environment="production",
            result="recorded",
            digest="",
            recorded_at="2026-07-13T12:04:00Z",
            details={
                "decision": "first_release_no_rollback_target",
                "decided_by": "approver.jane",
                "decided_at": "2026-07-13T12:04:00Z",
                "rationale": "No verified prior production digest.",
                "accepted_risk": "No prior verified digest available for rollback.",
            },
        ),
        _base_event(
            "production_deployed",
            event_id="e6",
            release_id=release_id,
            environment="production",
            recorded_at="2026-07-13T12:05:00Z",
        ),
        _base_event(
            "production_verified",
            event_id="e7",
            release_id=release_id,
            environment="production",
            recorded_at="2026-07-13T12:06:00Z",
        ),
    ]


def _write_release(tmp_path: Path, release_id: str, events: list[dict]) -> Path:
    for event in events:
        evidence.append_event(tmp_path, release_id, event, regenerate_manifest=False)
    evidence.write_derived_manifest(
        evidence.release_dir(tmp_path, release_id), release_id=release_id
    )
    return evidence.release_dir(tmp_path, release_id)


def test_append_is_append_only_and_derives_summary(tmp_path: Path) -> None:
    events = _happy_path_events()
    directory = _write_release(tmp_path, "rel-1", events[:3])
    first = (directory / "events.jsonl").read_text(encoding="utf-8")

    evidence.append_event(tmp_path, "rel-1", events[3])
    second = (directory / "events.jsonl").read_text(encoding="utf-8")
    assert second.startswith(first)
    assert first.count("\n") == 3
    assert second.count("\n") == 4

    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == evidence.SCHEMA_VERSION
    assert manifest["image"]["digest"] == DIGEST
    assert manifest["approvals"][0]["approver_id"] == "approver.jane"
    assert manifest["approvals"][0]["approved_at"] == "2026-07-13T12:03:00Z"
    assert manifest["staging"]["status"] == "verified"
    assert manifest["claim_boundary"].startswith("local-only")


def test_duplicate_event_id_rejected(tmp_path: Path) -> None:
    event = _base_event("build_published", event_id="same")
    evidence.append_event(tmp_path, "rel-1", event)
    with pytest.raises(evidence.EvidenceError, match="duplicate event_id"):
        evidence.append_event(tmp_path, "rel-1", event)


def test_validate_passes_for_complete_production_claim(tmp_path: Path) -> None:
    _write_release(tmp_path, "rel-1", _happy_path_events())
    assert evidence.validate_release_evidence(tmp_path, "rel-1") == []


def test_validate_fails_when_events_missing_for_production_claim(tmp_path: Path) -> None:
    events = [
        event
        for event in _happy_path_events("rel-bad")
        if event["event_type"] not in {"staging_verified", "production_approval"}
    ]
    directory = evidence.release_dir(tmp_path, "rel-bad")
    directory.mkdir(parents=True)
    for event in events:
        evidence.append_event(tmp_path, "rel-bad", event, regenerate_manifest=False)
    evidence.write_derived_manifest(directory, release_id="rel-bad")
    errors = evidence.validate_release_evidence(tmp_path, "rel-bad")
    assert any("staging_verified" in error for error in errors)
    assert any("production_approval" in error or "approver" in error for error in errors)


def test_validate_fails_on_digest_mismatch(tmp_path: Path) -> None:
    events = _happy_path_events()
    events[2]["image_digest"] = OTHER_DIGEST
    _write_release(tmp_path, "rel-1", events)
    errors = evidence.validate_release_evidence(tmp_path, "rel-1")
    assert any("inconsistent image_digest" in error for error in errors)


def test_validate_fails_on_missing_approval_identity(tmp_path: Path) -> None:
    events = _happy_path_events()
    events[3]["details"] = {"approver_id": "", "approved_at": "2026-07-13T12:03:00Z"}
    with pytest.raises(evidence.EvidenceError, match="approver_id"):
        _write_release(tmp_path, "rel-1", events)


def test_validate_fails_when_summary_not_derived_from_events(tmp_path: Path) -> None:
    directory = _write_release(tmp_path, "rel-1", _happy_path_events())
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["approvals"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    errors = evidence.validate_release_evidence(tmp_path, "rel-1")
    assert any("not derived from the event log" in error for error in errors)


def test_validate_fails_without_rollback_target_or_first_release(tmp_path: Path) -> None:
    events = [
        event for event in _happy_path_events() if event["event_type"] != "first_release_decision"
    ]
    _write_release(tmp_path, "rel-1", events)
    errors = evidence.validate_release_evidence(tmp_path, "rel-1")
    assert any("rollback_target_bound or first_release_decision" in error for error in errors)


def test_rollback_target_fields_are_derived(tmp_path: Path) -> None:
    events = [
        event for event in _happy_path_events() if event["event_type"] != "first_release_decision"
    ]
    events.insert(
        4,
        _base_event(
            "rollback_target_bound",
            event_id="e5b",
            environment="production",
            digest="",
            recorded_at="2026-07-13T12:04:00Z",
            details={
                "digest": OTHER_DIGEST,
                "commit_sha": "cccccccccccccccccccccccccccccccccccccccc",
                "verified_at": "2026-07-12T18:00:00Z",
                "source_release_id": "prior-rel",
                "environment": "production",
            },
        ),
    )
    directory = _write_release(tmp_path, "rel-1", events)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["rollback_target"]["digest"] == OTHER_DIGEST
    assert manifest["rollback_target"]["source_release_id"] == "prior-rel"
    assert manifest["first_release_decision"] is None
    assert evidence.validate_release_evidence(tmp_path, "rel-1") == []


def test_self_referential_rollback_target_rejected(tmp_path: Path) -> None:
    event = _base_event(
        "rollback_target_bound",
        event_id="bad-target",
        environment="production",
        digest=DIGEST,
        details={
            "digest": DIGEST,
            "commit_sha": COMMIT,
            "verified_at": "2026-07-12T18:00:00Z",
            "source_release_id": "prior-rel",
            "environment": "production",
        },
    )
    with pytest.raises(evidence.EvidenceError, match="self-referential"):
        evidence.append_event(tmp_path, "rel-1", event)


def test_secrets_in_events_rejected(tmp_path: Path) -> None:
    event = _base_event(
        "build_published",
        event_id="secret-event",
        details={"password": "super-secret-value"},
    )
    with pytest.raises(evidence.EvidenceError, match="secrets"):
        evidence.append_event(tmp_path, "rel-1", event)


def test_example_release_validates_via_cli(capsys: pytest.CaptureFixture[str]) -> None:
    result = project_cli.main(["evidence", "example", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == project_cli.EXIT_OK
    assert output["valid"] is True
    assert output["errors"] == []
    assert output["path"] == "evidence/example/manifest.json"
    assert output["events_path"] == "evidence/example/events.jsonl"


def test_cli_evidence_fails_on_digest_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    events = _happy_path_events("cli-bad")
    events[1]["image_digest"] = OTHER_DIGEST
    _write_release(tmp_path, "cli-bad", events)
    monkeypatch.setattr(project_cli, "ROOT", tmp_path)
    result = project_cli.main(["evidence", "cli-bad", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == project_cli.EXIT_VALIDATION
    assert output["valid"] is False
    assert any("inconsistent image_digest" in error for error in output["errors"])


def test_cli_evidence_fails_when_events_log_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory = tmp_path / "evidence" / "orphan"
    directory.mkdir(parents=True)
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "6.0",
                "release_id": "orphan",
                "commit_sha": COMMIT,
                "status": "production_verified",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(project_cli, "ROOT", tmp_path)
    result = project_cli.main(["evidence", "orphan", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == project_cli.EXIT_VALIDATION
    assert output["valid"] is False
    assert any("missing append-only event log" in error for error in output["errors"])
