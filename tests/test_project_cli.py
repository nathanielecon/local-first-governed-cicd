import json
from pathlib import Path

import pytest
from scripts import project_cli


def test_authoritative_state_and_skills_validate() -> None:
    assert project_cli.validate_state() == []
    assert project_cli.validate_skills() == []


def test_status_can_filter_phase(capsys: pytest.CaptureFixture[str]) -> None:
    result = project_cli.main(["status", "--phase", "1", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == project_cli.EXIT_OK
    assert output["tasks"]
    assert {task["phase"] for task in output["tasks"]} == {1}


def test_phase_authorization_boundary(capsys: pytest.CaptureFixture[str]) -> None:
    result = project_cli.main(["phase", "8", "--dry-run", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == project_cli.EXIT_OK
    assert output["phase"] == 8

    result = project_cli.main(["phase", "9", "--dry-run", "--json"])
    error = json.loads(capsys.readouterr().err)
    assert result == project_cli.EXIT_HUMAN
    assert "not authorized" in error["error"]


def test_verified_task_cannot_resume(capsys: pytest.CaptureFixture[str]) -> None:
    result = project_cli.main(["resume", "P1-T04", "--json"])
    error = json.loads(capsys.readouterr().err)
    assert result == project_cli.EXIT_CONFLICT
    assert "not resumable from verified" in error["error"]


def test_issue_filters(capsys: pytest.CaptureFixture[str]) -> None:
    result = project_cli.main(["issues", "--severity", "critical", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == project_cli.EXIT_OK
    assert output["count"] == 3


def test_evidence_reports_missing_release(capsys: pytest.CaptureFixture[str]) -> None:
    result = project_cli.main(["evidence", "does-not-exist", "--json"])
    assert result == project_cli.EXIT_VALIDATION
    assert "not found" in capsys.readouterr().err


def test_evidence_example_passes_phase6_validation(capsys: pytest.CaptureFixture[str]) -> None:
    result = project_cli.main(["evidence", "example", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == project_cli.EXIT_OK
    assert output["valid"] is True
    assert output["errors"] == []
    assert "events_path" in output


def test_read_json_block_rejects_missing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "ROOT", tmp_path)
    with pytest.raises(project_cli.ProjectError) as error:
        project_cli.read_json_block("PLAN.md")
    assert error.value.exit_code == project_cli.EXIT_SCHEMA
