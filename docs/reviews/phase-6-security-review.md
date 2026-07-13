# Phase 6 Security Review

Date: 2026-07-13  
Reviewer lane: P6-T07 independent security review  
Gate: `phase-6-security-review`  
Branch / tree: working tree Phase 6 evidence and recovery implementation (P6-T02 / P6-T03 / P6-T04)

**Verdict: CLEAR for the local Phase 6 security-review gate.**

No new critical or high security finding was identified beyond the still-open ledger issues `PC-002` and `PC-003`. Local source, fixtures, validators, and tests support append-only release evidence with approver persistence, identity-bound digest promotion, rollback-target or first-release fail-closed gating, and recovery verification against a verified prior digest. This verdict does **not** resolve or close `PC-002` or `PC-003`; integrated closure belongs to P6-T08.

This review is local-only / production-like / non-E2E. It does not approve live Jenkins runtime promotion, live cloud, AWS, organizational Jenkins administration, sustained production operation, or digest promotion as a completed organizational outcome.

## Reviewed baseline

- Authority: `PLAN.md` (P6-T07), `STATUS.md`, `ISSUES.md` (`PC-002` open; `PC-003` open), `AGENTS.md`
- Design / prior gates: `docs/phase-6-spec.md`, `docs/reviews/phase-6-eng-review.md`, `docs/reviews/phase-6-change-review.md`, `docs/change-records/phase-6-local.md`, `evidence/phase-6/qa.txt` (P6-T06 PASS)
- Implementation: `scripts/evidence.py`, `scripts/project_cli.py`, `scripts/verify_deployment.py`, `scripts/deploy.sh`, `scripts/deploy.ps1`, `scripts/rollback.sh`, `scripts/rollback.ps1`, `Jenkinsfile`, related static tests
- Evidence: `evidence/example/` (first-release fixture), `evidence/phase-6/` (recovery-demo fixture + task evidence)
- Independent checks this review:
  - `git diff HEAD -- scripts/evidence.py scripts/verify_deployment.py Jenkinsfile scripts/project_cli.py` → material Phase 6 security-boundary changes present
  - `.venv\Scripts\python.exe -m pytest -q` → **111 passed**, coverage **96.59%**, exit 0
  - `scripts/evidence.py validate --release-id phase-6` → `valid: true`
  - `scripts/evidence.py validate --release-id example` → `valid: true`
  - `scripts/project_cli.py evidence phase-6` → `valid: true`
  - `scripts/validate_jenkinsfile.py --json` → `valid: true`, `errors: []`

## Trust-boundary map

| Identity / surface | Trust role | Privileged operations | Phase 6 control |
|---|---|---|---|
| `TRUSTED_GIT_SHA` | Immutable release commit input | Selects commit fetched before Validate/Build | 40-char lowercase hex only; `refs/` and non-SHA rejected before `git fetch`; FETCH_HEAD must equal trusted SHA |
| Build-once `IMAGE_DIGEST` / `IMAGE_DIGEST_REF` | Canonical promotion identity | Staging and production deploy the same digest | RepoDigest selected via `select_matching_repo_digest` with registry/repository binding; arbitrary first RepoDigest rejected |
| Named approver (`PROJECT_C_ALLOWED_APPROVERS` / `APPROVED_BY`) | Human production-like approval | Advances promotion past `input` gate; identity persisted into evidence | Fail-closed without allow-list; `submitter:` restriction; `production_approval` requires `approver_id` + `approved_at` |
| Append-only `events.jsonl` | Event source of truth | Records build, staging, approval, rollback bind / first-release, production, failure, rollback, recovery | Append-only write path; duplicate `event_id` rejected; secrets patterns rejected; derived `manifest.json` must match gate fields |
| Derived `manifest.json` | Operator/gate summary | Must not silently discard history | Regenerated from events; validation fails if gate fields disagree with derivation |
| Verified rollback target (`VERIFIED_ROLLBACK_*`) **or** first-release decision | Production readiness gate | Required before production deploy | XOR enforced; self-referential and staging-as-prior rejected; deploy scripts call `promotion-gate` fail-closed |
| Rollback / recovery path | Restore prior verified digest | Digest-targeted rollback + full recovery suite | `rollback.sh` / `rollback.ps1` require explicit verified digest; `previous.env` is non-authoritative cache only; `--mode recovery` re-runs digest/health/version/business checks |
| PR / GitHub Actions | Untrusted contribution path | Read-only repository validation | `permissions: {}` default; jobs use `contents: read` only; pinned actions; “Build without credentials”; no deployment secrets |
| Host Docker socket + local Jenkins root (Phase 5 residual) | Local control-plane privilege | Container can drive host Docker | Out of Phase 6 evidence/recovery claim scope; retained accepted residual |

Credential values for local Jenkins identities remain external `${JENKINS_LOCAL_*}` injections from Phase 5. Phase 6 evidence paths do not introduce new deployment credential surfaces into the PR workflow.

## Findings

No new critical or high findings. No new issue ID is required from this review. Existing open criticals `PC-002` and `PC-003` remain the ledger blockers for integrated closure at P6-T08.

### Closed relative to PC-002 (local remediation supported; ledger close deferred to P6-T08)

| Original PC-002 defect | Current disposition | Evidence |
|---|---|---|
| Manifest overwrite without durable event history | Remediated in local contract | `scripts/evidence.py` `append_event` opens events JSONL in append mode and never rewrites prior lines; `validate_release_evidence` fails when summary gate fields are not derived from events |
| Approver identity not persisted into release evidence | Remediated in local contract | Jenkinsfile Production Approval appends `production_approval` with `--approver-id` / `--approved-at`; validator requires both fields for production claims; fixtures and change record cite `local-approver` |

### Closed relative to PC-003 (local remediation supported; ledger close deferred to P6-T08)

| Original PC-003 defect | Current disposition | Evidence |
|---|---|---|
| Production promotion without verified prior digest or explicit first-release decision | Remediated in local contract | `validate_production_promotion_gate` + `deploy.sh` / `deploy.ps1` fail closed; Jenkinsfile Rollback Readiness records exactly one of `rollback_target_bound` or `first_release_decision`; recovery demo forbidden on first release |
| Rollback restores env file without proving restored digest/health/version/business | Remediated in local contract | Rollback scripts require explicit verified digest argument; `previous.env` labeled non-authoritative; recovery verification runs `--mode recovery` with identity-bound digest checks |

### Advisory — accepted residual risks (non-blocking for Phase 6 local security gate)

| Severity | Finding | Disposition |
|---|---|---|
| Advisory | `VERIFIED_ROLLBACK_*` Jenkins parameters are operator-attested. The pipeline records and syntactically validates them but does not automatically load or prove those fields from a prior `evidence/<release>/` `production_verified` history. | Acceptable under local-only / production-like claim. Residual honesty assumption already recorded in change review. Stronger prior-evidence binding remains out of authorized live-org scope; keep visible until P6-T08 decides integrated closure sufficiency for `PC-003`. Owner: phase-6 orchestrator / future hardening. Expiry: before any organizational production claim (unauthorized today). |
| Advisory | Jenkinsfile Staging / Production / Recovery stages append verified/recovery check maps as literal JSON rather than piping `verify_deployment.py` JSON output. | Not fail-open today: deploy/rollback scripts already exit non-zero on verify failure before appends can succeed on the happy path. Residual evidence-fidelity risk if a future stage appends without calling verify. Owner: future Jenkins integration hardening. Expiry: next evidence-fidelity improvement slice. |
| Advisory | Recovery stage appends `recovery_verified` after `rollback.sh` already ran recovery verify; the append itself does not re-invoke verify. | Current path still fail-closed at rollback. Do not treat hardcoded recovery maps as independent probe evidence. Owner: future Jenkins integration hardening. Expiry: next evidence-fidelity improvement slice. |
| Advisory | `evidence/phase-6/p6-t03-compose-config.txt` contains Compose-resolved local placeholder password env values (`local-*-password`). | Local Phase 5 fake-credential pattern leakage into retained config dump. Not production secrets. Do not reuse as shared defaults or promote as sensitive-evidence hygiene exemplar. Owner: local evidence hygiene. Expiry: optional cleanup before portfolio packaging. |
| Advisory | Phase 5 residual: Jenkins Compose root + Docker socket; `cpsScm` tip load; `cleanWs` after archive. | Outside Phase 6 evidence/recovery contract. Keep local-only claims honest; do not rebrand as hardened multi-tenant isolation. Owner: controller isolation backlog. Expiry: before multi-tenant / shared controller claims. |
| Advisory | Retained `evidence/phase-6/` is a synthetic local fixture (`pipeline.run_id: manual`, synthetic digests/commits), not live Jenkins E2E runtime proof. | Explicit non-E2E boundary. QA and this security review must not upgrade the fixture into a live promotion claim. Owner: P6-T08 claim boundary. Expiry: n/a while claim remains local-only. |

## Secret exposure and unsupported-claim checks

- **Source / config:** No hardcoded deployment passwords, cloud tokens, or AWS keys observed in `Jenkinsfile`, `scripts/evidence.py`, `scripts/verify_deployment.py`, `scripts/project_cli.py`, or deploy/rollback scripts. Approver and actor fields are identities, not secrets. Evidence append rejects secret-like patterns.
- **Evidence:** `evidence/example/` and `evidence/phase-6/events.jsonl` + `manifest.json` contain synthetic digests, local actor names, and local-only claim strings. No live cloud credentials or production secrets observed. Compose-config evidence retains local placeholder password strings only (advisory above).
- **PR path:** `.github/workflows/pr-validation.yml` uses default `permissions: {}`, per-job `contents: read`, pinned third-party actions by full SHA, gitleaks + trivy, and container build without credentials. No deployment credential injection on untrusted PR jobs.
- **Claims:** Change record, QA, eng review, change review, and this security review preserve local-only / production-like / non-E2E boundaries. No reviewed artifact asserts live cloud, AWS, organizational Jenkins administration, or sustained production operation.
- **Untrusted execution:** PR validation cannot promote. Local Jenkins production-like path still requires named approver allow-list and fails closed without it.

## Independent validation

| Check | Result |
|---|---|
| `git diff HEAD` (evidence / verify / Jenkinsfile / CLI) | Phase 6 append-only evidence, identity-bound digest, approval persistence, rollback readiness, recovery stages present |
| `.venv\Scripts\python.exe -m pytest -q` | Pass — 111 passed, 96.59% coverage, exit 0 |
| Evidence validate `phase-6` / `example` | `valid: true`, `errors: []` |
| Jenkinsfile validator | `valid: true`, `errors: []` |
| Claim-boundary strings in QA / change record / fixture manifest | local-only / production-like; non-E2E explicitly stated |

## PC-002 / PC-003 and follow-on gates

- Local security evidence **supports** resolving `PC-002` and `PC-003` at the integrated evidence gate once P6-T08 confirms all declared Phase 6 artifacts agree.
- This task does **not** mark verified/done and does **not** close `PC-002` or `PC-003`. Orchestrator must keep both open until P6-T08.
- No critical/high finding requires a new issue ID; existing `PC-002` / `PC-003` cover the residual ledger blockers. `ISSUES.md` was not modified.

## Verdict

**CLEAR.** Proceed to P6-T08 integrated evidence. Phase 6 local evidence and recovery security boundaries are acceptable under the local-only / non-E2E claim: append-only events with secret rejection and derived-summary consistency, named approval persistence, identity-bound digest promotion, fail-closed rollback-target or first-release gating, and digest-targeted recovery verification. `PC-002` and `PC-003` remain open. Residual operator-attested rollback parameters, hardcoded verify maps, Docker-socket/root controller risk, and non-E2E fixture limits remain explicitly accepted and must not be rebranded as live or organizational production readiness.
