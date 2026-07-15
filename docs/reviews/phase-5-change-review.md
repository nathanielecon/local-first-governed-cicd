# Phase 5 Change Review

Date: 2026-07-13  
Reviewer lane: P5-T05 independent change review (fresh context after PC-014 trusted-input remediation)  
Branch: `phase-5-remediation`

## Verdict: clear

P5-T01 through P5-T04 are review-clear for the bounded local Phase 5 authorization remediation. The prior High trusted-input gap (PC-014) is closed: release input is now bound to an immutable 40-character commit SHA, arbitrary branch/tag refs are rejected before `git fetch`, and static regression coverage plus refreshed local evidence demonstrate the contract. The governing P5-T04 unauthorized-denial proof remains valid under the accepted 400-or-403 contract. No material correctness, security, or claim-boundary findings remain that should block progression to Phase 5 QA.

This verdict is local-only. It does not approve live production, cloud activity, organizational Jenkins administration, digest promotion, durable release evidence (PC-002), or verified rollback recovery (PC-003).

## Reviewed scope

- Current working-tree Phase 5 diff for `Jenkinsfile`, `compose.yaml`, `infra/jenkins/`, `scripts/validate_jenkinsfile.py`, `tests/test_jenkinsfile_contract.py`, related static tests, README/runbook credential boundary text, and retained Phase 5 evidence.
- Governing design: `docs/reviews/phase-5-eng-review.md`.
- PLAN acceptance for P5-T01 (external credentials + least-privilege JCasC), P5-T02 (no Compose/doc credential fallbacks), P5-T03 (named approvers + trusted commit/controlled reference), P5-T04 (local unauthorized denial without production continuation), and P5-T05 (cite diff/AC/evidence; no unsupported claims; actionable file/line findings).
- Open issue PC-014 and resolved PC-010 through PC-013 context.

## Diff and acceptance mapping

| Task | Acceptance focus | Review disposition |
|---|---|---|
| P5-T01 | No usable default admin password; role-based authz; externally supplied pinned config | Met: `compose.yaml:38-43` requires env injection; `infra/jenkins/casc.yaml:15-45` uses named roles, not `loggedInUsersCanDoAnything`. |
| P5-T02 | Compose/docs require external local-only placeholders without fallbacks | Met: required `${VAR:?...}` injection; docs state local-only fake-credential boundary. |
| P5-T03 | Named submitter restriction + trusted commit/controlled reference with failing static checks when missing | Met after remediation: `TRUSTED_GIT_SHA` + pre-fetch rejection of `refs/` and non-SHA input; validator/tests reject the old loose-ref gate. |
| P5-T04 | Isolated local fake-identity fixture denies unauthorized approval; no production continuation | Met: governing proof shows `unauthorized_status=400`, explicit local-approver denial, pause at approval, final `ABORTED`. |

## Evidence and checks

- `evidence/phase-5/p5-t01-pytest.txt`: 9 passed.
- `evidence/phase-5/p5-t02-pytest.txt`: 6 passed.
- `evidence/phase-5/p5-t03-pytest.txt`: 9 passed (refreshed after trusted-input remediation).
- `evidence/phase-5/p5-t03-validate-jenkinsfile.txt`: `valid: true`, `errors: []`.
- Governing P5-T04 proof: `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt` records placeholder identities, `unauthorized_status=400`, `X-Error=You need to be local-approver to submit this.`, console pause at `FIXTURE_AWAITING_APPROVAL`, no production continuation marker, and final result `ABORTED`.
- Independent review re-checks: `.venv\Scripts\python.exe -m pytest tests/test_jenkinsfile_contract.py -q -o addopts=` → 9 passed; `.venv\Scripts\python.exe scripts/validate_jenkinsfile.py --json` → `valid: true`; `.venv\Scripts\python.exe -m pytest -q` → 75 passed, 96.59% coverage; `git diff --check` clean for the reviewed implementation paths.

## Findings

No High, Medium, or Low blocking findings.

### Closed — prior High (PC-014) trusted-input arbitrary-ref acceptance

Previously, `TRUSTED_GIT_REF` accepted any syntactically valid `refs/heads/*` or `refs/tags/*` before fetch. The remediated contract replaces that path:

- `Jenkinsfile:11,21-28` requires `TRUSTED_GIT_SHA`, rejects empty input, rejects `refs/` prefixes, and requires `/^[0-9a-f]{40}$/` before any fetch.
- `Jenkinsfile:30-38` fetches only the SHA, detaches to `FETCH_HEAD`, and fails closed if the resolved commit does not equal `TRUSTED_GIT_SHA`.
- `scripts/validate_jenkinsfile.py:12-27,109-181` encodes the SHA helper, requires the SHA parameter and pre-fetch `refs/` rejection, and fails the contract if `TRUSTED_GIT_REF` or the old refs/(heads|tags) syntax gate reappears.
- `tests/test_jenkinsfile_contract.py:57-97` adds behavioral rejection of arbitrary branch/tag refs and a regression that the loose-ref Jenkinsfile shape fails the validator.

This satisfies P5-T03 and the PC-014 remediation requirement for immutable commit binding with arbitrary-ref rejection before fetch.

### Advisory — residual local-fixture risks (non-blocking)

- `compose.yaml:35,47` still runs Jenkins as `root` with `/var/run/docker.sock` mounted. This remains the documented Phase 5 local-control-plane residual risk from the engineering review; it is not cleared as controller isolation.
- `README.md:30-32` still states that only Phase 1 is authorized, which conflicts with `PLAN.md` / `STATUS.md` authorizing through Phase 8. Treat as stale documentation outside the substantive credential/authorization change; do not use it as a Phase 5 capability claim.
- `infra/jenkins/casc.yaml:71-72` still loads the pipeline script via `branch('*/master')` for `cpsScm`. Release execution trust is enforced by the Jenkinsfile SHA gate after load; this SCM script-load branch is not treated as a remaining trusted-release-input defect for Phase 5.

## Confirmed controls and claim boundaries

- Named approval: `Jenkinsfile:82-86` fails closed without `PROJECT_C_ALLOWED_APPROVERS` and passes that list to `input` as `submitter`.
- Least privilege: viewer is not granted delivery-job build permissions in `infra/jenkins/casc.yaml:25-45`.
- Credential externalization: no repository-supplied usable Jenkins administrator password fallback in Compose.
- P5-T04 remains a local fake-identity denial proof only; 400 is accepted as unauthorized denial because the retained proof also includes the explicit denial header, non-continuation, and `ABORTED` cleanup.
- PC-002 and PC-003 remain hard out-of-scope blockers for durable multi-environment evidence and verified rollback claims.

## Assumptions and open questions

- This review treats operator-supplied immutable SHA binding plus named production approval as the Phase 5 trusted-input contract. A separate pre-approved SHA registry is not required by the current eng-review or PC-014 remediation text.
- The P5-T04 fixture uses a stub approval pipeline and therefore does not re-exercise `TRUSTED_GIT_SHA` at runtime; trusted-input assurance for this gate rests on the Jenkinsfile + validator + contract tests and refreshed P5-T03 evidence. That split is acceptable for the unauthorized-approval proof scope.
- No re-run of the Dockerized unauthorized fixture was required for this review because the governing proof is unchanged and the trusted-input remediation did not alter the approval denial contract.

## Concise change summary

Phase 5 removes repository Jenkins administrator defaults, injects distinct local placeholder identities with role-based authorization, restricts production approval to named submitters, binds release input to an immutable commit SHA with pre-fetch arbitrary-ref rejection, and retains local unauthorized-denial evidence under the 400-or-403 acceptance contract. Independent change review clears P5-T01 through P5-T04 and supports resolving PC-014 so QA (`P5-T06`) may proceed.
