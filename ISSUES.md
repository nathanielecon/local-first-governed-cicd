# Running Issue Ledger

The active Codex task is the immediate notification channel. This ledger is the durable record. Critical issues freeze the affected and dependent lanes, not unrelated work.

```json
{
  "schema_version": "1.0",
  "revision": 3,
  "issues": [
    {
      "id": "PC-001",
      "opened_at": "2026-07-11T15:00:00Z",
      "phase": 5,
      "task": "Jenkins production authorization",
      "severity": "critical",
      "category": "security",
      "summary": "Production approval is not restricted to named submitters, Jenkins grants every authenticated user administrative authority, and the local stack defines a default administrator password.",
      "evidence": ["Jenkinsfile", "infra/jenkins/casc.yaml", "compose.yaml"],
      "owner": "future-phase-5-security-worker",
      "attempts": 0,
      "status": "open",
      "human_question": "",
      "resolution": "Phase 5 must introduce externally supplied credentials, least-privilege authorization, named approvers, and an unauthorized-promotion test.",
      "resolved_at": "",
      "continue_lanes": ["Phase 1 harness", "Phase 2 planning", "daemon-independent validation"]
    },
    {
      "id": "PC-002",
      "opened_at": "2026-07-11T15:00:00Z",
      "phase": 6,
      "task": "Append-only release evidence",
      "severity": "critical",
      "category": "defect",
      "summary": "The evidence manifest overwrites environment state and does not record the Jenkins approver, so staging, approval, and production cannot be proven together.",
      "evidence": ["Jenkinsfile", "scripts/evidence.py"],
      "owner": "future-phase-6-evidence-worker",
      "attempts": 0,
      "status": "open",
      "human_question": "",
      "resolution": "Phase 6 must use append-only events plus a summary manifest and persist approver identity and timestamps.",
      "resolved_at": "",
      "continue_lanes": ["Phase 1 harness", "Phase 2 planning", "Phase 3 test design"]
    },
    {
      "id": "PC-003",
      "opened_at": "2026-07-11T15:00:00Z",
      "phase": 6,
      "task": "Verified rollback target and recovery",
      "severity": "critical",
      "category": "defect",
      "summary": "First production promotion may have no rollback digest, and recovery does not verify health, version, business behavior, or deployed digest.",
      "evidence": ["Jenkinsfile", "scripts/deploy.ps1", "scripts/deploy.sh", "scripts/rollback.ps1", "scripts/rollback.sh"],
      "owner": "future-phase-6-recovery-worker",
      "attempts": 0,
      "status": "open",
      "human_question": "",
      "resolution": "Phase 6 must prohibit promotion without a verified target or an explicit first-release decision and must fully verify restored state.",
      "resolved_at": "",
      "continue_lanes": ["Phase 1 harness", "Phase 2 planning", "Phase 3 test design"]
    },
    {
      "id": "PC-004",
      "opened_at": "2026-07-11T15:00:00Z",
      "phase": 3,
      "task": "Container runtime verification",
      "severity": "blocking",
      "category": "environment",
      "summary": "Docker Desktop is installed but its Linux engine did not become available during the earlier verification window.",
      "evidence": ["STATUS.md"],
      "owner": "future-phase-3-runtime-worker",
      "attempts": 2,
      "status": "open",
      "human_question": "Start or repair Docker Desktop Linux-container support before Phase 3 runtime validation.",
      "resolution": "",
      "resolved_at": "",
      "continue_lanes": ["Phase 1", "Phase 2", "GitHub workflow drafting"]
    },
    {
      "id": "PC-005",
      "opened_at": "2026-07-11T15:20:00Z",
      "phase": 1,
      "task": "Phase 1 engineering gate closure",
      "severity": "blocking",
      "category": "approval",
      "summary": "The Phase 1 harness passes, but its gate prohibits unresolved critical findings while PC-001 through PC-003 belong to currently unauthorized Phase 5-6 implementation.",
      "evidence": ["docs/reviews/eng-review.md", "ISSUES.md", "PLAN.md"],
      "owner": "human-project-owner",
      "attempts": 0,
      "status": "resolved",
      "human_question": "May Phase 1 close conditionally while PC-001 through PC-003 remain hard blockers on Phases 5 and 6?",
      "resolution": "Project owner removed the Phase 1 administrative human gate. Phase 1 closed conditionally; PC-001 through PC-003 remain hard blockers on their affected future phases.",
      "resolved_at": "2026-07-11T15:30:00Z",
      "continue_lanes": ["No additional implementation; read-only inspection and planning only"]
    }
  ]
}
```
