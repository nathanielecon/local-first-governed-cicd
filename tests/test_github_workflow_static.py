from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pr-validation.yml"


def read_workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_all_actions_are_pinned_to_full_commit_shas() -> None:
    workflow = read_workflow()
    uses_refs = re.findall(r"uses:\s+([^\s#]+)", workflow)
    assert uses_refs
    assert all(re.search(r"@[0-9a-f]{40}$", ref) for ref in uses_refs)


def test_each_job_declares_read_only_permissions() -> None:
    workflow = read_workflow()
    for job in ("python", "security", "container", "jenkinsfile"):
        pattern = rf"{job}:\n(?:[^\n]*\n)+?\s{{4}}permissions:\n\s{{6}}contents:\sread"
        assert re.search(pattern, workflow)


def test_jenkinsfile_job_uses_validator_script() -> None:
    workflow = read_workflow()
    assert "python scripts/validate_jenkinsfile.py Jenkinsfile" in workflow


def test_workflow_remains_credential_free_for_deployment() -> None:
    workflow = read_workflow()
    forbidden = ("AWS_", "AZURE_", "KUBE", "PRODUCTION_", "STAGING_")
    assert all(token not in workflow for token in forbidden)
