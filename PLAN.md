# Authoritative Implementation Plan

The JSON block is the machine-readable task authority. Workers may not edit it directly; state changes go through the project CLI and the orchestrator.

```json
{
  "schema_version": "1.0",
  "revision": 4,
  "authorized_through_phase": 2,
  "tasks": [
    {
      "id": "P1-T01",
      "phase": 1,
      "title": "Audit the existing scaffold",
      "outcome": "Every intentional asset has a retain, revise, quarantine, or remove disposition.",
      "state": "verified",
      "depends_on": [],
      "model_tier": "low",
      "owner": "scaffold-audit-worker",
      "write_scope": ["docs/scaffold-audit.md"],
      "acceptance_criteria": ["All project assets classified", "Generated artifacts separated", "Phase 2-6 verification boundary stated"],
      "validation_commands": ["project validate state"],
      "evidence_paths": ["docs/scaffold-audit.md"],
      "gate": "phase-1-engineering-review",
      "issue_ids": [],
      "attempts": 1,
      "last_error_class": ""
    },
    {
      "id": "P1-T02",
      "phase": 1,
      "title": "Establish orchestrator and worker contract",
      "outcome": "Model routing, Mandarin handoff, write scopes, retry limits, escalation, and human decisions are enforceable.",
      "state": "verified",
      "depends_on": ["P1-T01"],
      "model_tier": "medium",
      "owner": "orchestrator",
      "write_scope": ["AGENTS.md", "docs/orchestration.md", "DECISIONS.md"],
      "acceptance_criteria": ["Terra Medium ceiling recorded", "Mandarin handoff schema recorded", "Human notification contract recorded"],
      "validation_commands": ["project validate state"],
      "evidence_paths": ["docs/orchestration.md", "DECISIONS.md"],
      "gate": "phase-1-engineering-review",
      "issue_ids": [],
      "attempts": 1,
      "last_error_class": ""
    },
    {
      "id": "P1-T03",
      "phase": 1,
      "title": "Implement unified CLI harness",
      "outcome": "Bootstrap, status, issues, phase, validate, resume, and evidence share one cross-platform core.",
      "state": "verified",
      "depends_on": ["P1-T01"],
      "model_tier": "medium",
      "owner": "orchestrator",
      "write_scope": ["scripts/project_cli.py", "scripts/project.ps1", "project", "tests/test_project_cli.py"],
      "acceptance_criteria": ["All required commands parse", "State and skills validate", "Blocked later phases cannot start"],
      "validation_commands": ["project validate phase-1"],
      "evidence_paths": ["evidence/phase-1/cli-tests.txt"],
      "gate": "phase-1-engineering-review",
      "issue_ids": [],
      "attempts": 1,
      "last_error_class": ""
    },
    {
      "id": "P1-T04",
      "phase": 1,
      "title": "Run independent engineering review",
      "outcome": "Trust boundaries, promotion identity, evidence, rollback, and concurrency risks are explicitly gated.",
      "state": "verified",
      "depends_on": ["P1-T01", "P1-T02", "P1-T03"],
      "model_tier": "independent-gate",
      "owner": "terra-medium-independent-reviewer",
      "write_scope": ["docs/reviews/eng-review.md", "ISSUES.md"],
      "acceptance_criteria": ["No unresolved Phase 1 critical findings", "Future critical findings have assigned blocking phases and remediation requirements", "Later-phase scaffold is not treated as verified"],
      "validation_commands": ["project validate phase-1"],
      "evidence_paths": ["docs/reviews/eng-review.md", "ISSUES.md"],
      "gate": "phase-1-engineering-review",
      "issue_ids": ["PC-001", "PC-002", "PC-003"],
      "attempts": 1,
      "last_error_class": "critical-design-findings"
    },
    {
      "id": "P2-T01",
      "phase": 2,
      "title": "Re-verify application and test contract",
      "outcome": "The existing Phase 2 candidate passes the new evidence-producing gate.",
      "state": "ready",
      "depends_on": ["P1-T04"],
      "model_tier": "medium",
      "owner": "",
      "write_scope": ["src/", "tests/", "pyproject.toml"],
      "acceptance_criteria": ["Ruff and mypy pass", "Tests pass with at least 90 percent coverage", "Release identity contract verified"],
      "validation_commands": ["project validate app"],
      "evidence_paths": ["evidence/phase-2/"],
      "gate": "phase-2-application",
      "issue_ids": [],
      "attempts": 0,
      "last_error_class": ""
    }
  ]
}
```

No task may move directly to `done`. The legal path is `planned -> ready -> running -> blocked|review -> verified -> done`. Later phases remain unauthorized until a human decision changes `authorized_through_phase`.
