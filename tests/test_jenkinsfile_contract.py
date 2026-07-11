from __future__ import annotations

from pathlib import Path

from scripts.validate_jenkinsfile import validate_text


ROOT = Path(__file__).resolve().parents[1]


def test_repository_jenkinsfile_satisfies_contract() -> None:
    text = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")
    assert validate_text(text) == []


def test_missing_submitter_parameter_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace("submitterParameter: 'APPROVED_BY'", "submitterParameter: ''")
    )
    assert "Production Approval stage must record APPROVED_BY" in validate_text(text)


def test_unbalanced_braces_are_rejected() -> None:
    text = (ROOT / "Jenkinsfile").read_text(encoding="utf-8").replace("\n  }\n}\n", "\n  }\n", 1)
    assert "unbalanced braces in Jenkinsfile" in validate_text(text)
