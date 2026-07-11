# Phase 4 Engineering Review

Date: 2026-07-11

Status: clear to begin bounded local Phase 4 implementation; real GitHub-hosted evidence still required before Phase 4 can be marked complete

Reviewed baseline: current repository state after verified Phase 3 runtime evidence, the existing `.github/workflows/pr-validation.yml`, `Jenkinsfile`, current authoritative project state, and the retained future-phase issues `PC-001`, `PC-002`, and `PC-003`.

Scope reviewed: GitHub PR-validation workflow structure, action pinning, job permissions, local credential boundary, container-contract validation intent, Jenkinsfile validation credibility, and the evidence boundary between local workflow hardening and real GitHub-hosted validation.

## Findings

No Phase 4 design blocker prevents local implementation work from starting. One expected external-evidence gap remains: real GitHub-hosted validation and a safe blocked-change demonstration will still need authenticated repository execution before the phase can close.

## Approved implementation boundary

- The current workflow is a valid starting point but not an acceptable final Phase 4 artifact. It still uses floating or tag-only third-party actions, global permissions are minimal but job-level least-privilege is not explicit, and the Jenkinsfile lane is only a grep-based text check.
- Phase 4 implementation may proceed only within engine-independent and repository-local workflow-hardening scope first:
  - align the phase-authorization harness to accept Phase 4 and reject Phase 5;
  - pin third-party actions to full commit SHAs;
  - keep PR jobs read-only and free of deployment credentials;
  - retain Python quality, secret scanning, Dockerfile scanning, and container contract coverage;
  - replace grep-only Jenkinsfile validation with a syntax-aware or parser-backed local contract check;
  - document the exact boundary between local workflow preparation and real GitHub-hosted evidence.
- Phase 4 must not claim GitHub-hosted success, required-check enforcement, branch protection changes, Jenkins runtime startup, release approval, rollback recovery, or cloud activity from local-only evidence.

## Required checks and risks

| Area | Current risk | Required Phase 4 response |
| --- | --- | --- |
| Third-party action sources | Tag-only references can drift or be retargeted. | Pin every third-party action in `.github/workflows/pr-validation.yml` to a full commit SHA and retain the human-readable version in a comment when helpful. |
| Untrusted PR permissions | Job permissions are not yet declared narrowly per lane. | Set explicit least-privilege permissions by job and keep the workflow credential-free. |
| Jenkinsfile verification | `grep` proves text presence, not a credible declarative structure. | Replace the text-only check with a validation path that parses or meaningfully inspects the Jenkinsfile structure and required controls. |
| Hosted evidence gap | Local edits alone cannot prove GitHub-hosted execution or required-check enforcement. | Capture local static evidence first, then obtain real hosted evidence or open an explicit blocker issue with the exact missing authority. |
| Future-phase security boundaries | `PC-001`, `PC-002`, and `PC-003` remain unresolved. | Preserve those issues as blockers for Jenkins authorization, append-only evidence, and rollback verification; do not widen Phase 4 scope into their remediation. |

## Dispatch recommendation

The next deterministic Phase 4 slices can run in parallel with non-overlapping scopes:

1. `P4-T01` phase-boundary harness alignment.
2. `P4-T02` workflow hardening for pinned actions, permissions, and scan lanes.
3. `P4-T03` credible Jenkinsfile declarative validation path.
4. `P4-T04` required-check and blocked-change boundary documentation.

After those local slices finish, run independent change review, QA, security review, and an integrated evidence gate that either includes real GitHub-hosted proof or explicitly records the missing external authority as a blocker.
