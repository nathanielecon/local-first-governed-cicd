# Phase 5 Security Review

Date: 2026-07-13  
Reviewer lane: P5-T07 independent security review  
Gate: `phase-5-security-review`  
Branch / tree: working tree on `phase-5-remediation` (current Phase 5 Jenkins remediation diff)

**Verdict: clear for the local Phase 5 security-review gate.**

No new critical or high security finding was identified in the approved Phase 5 local Jenkins authorization scope. Local evidence supports the PC-001 remediation claims (external credentials, least-privilege roles, named approvers, trusted immutable SHA input, unauthorized-promotion denial). This verdict does **not** close PC-001 in the issue ledger; integrated closure belongs to P5-T08. PC-002 and PC-003 remain out of scope. Docker-socket/root residual risk remains accepted and unresolved as controller isolation.

This review is local-only. It does not approve live production, real cloud, organizational Jenkins administration, digest promotion, durable multi-environment evidence, or verified rollback recovery.

## Reviewed baseline

- Authority: `PLAN.md` (P5-T07), `STATUS.md`, `ISSUES.md` (PC-001 open; PC-014 resolved; PC-002/PC-003 Phase 6)
- Design / prior gates: `docs/reviews/phase-5-eng-review.md`, `docs/reviews/phase-5-change-review.md`, `evidence/phase-5/qa.txt`
- Implementation: `Jenkinsfile`, `compose.yaml`, `infra/jenkins/casc.yaml`, `infra/jenkins/Dockerfile`, `infra/jenkins/plugins.txt`, `scripts/validate_jenkinsfile.py`, related static tests, `README.md`, `docs/runbook.md`
- Evidence: `evidence/phase-5/p5-t01-pytest.txt`, `p5-t02-pytest.txt`, `p5-t03-pytest.txt`, `p5-t03-validate-jenkinsfile.txt`, `p5-t04-manual-verify2-unauthorized-proof.txt`
- Independent checks this review: `git diff HEAD` (Phase 5 implementation paths), `.venv\Scripts\python.exe -m pytest -q` → **75 passed**, coverage **96.59%**, exit 0

## Trust-boundary map

| Identity / surface | Trust role | Privileged operations | Phase 5 control |
|---|---|---|---|
| `JENKINS_LOCAL_ADMIN_ID` | Local controller admin | `Overall/Administer`; delivery-job Build/Cancel/Read/Workspace | Externally injected; distinct from approver/viewer; no repo password fallback |
| `JENKINS_LOCAL_APPROVER_ID` | Named production-like approver | Global read; delivery-job Build/Cancel/Read/Workspace; sole value of `PROJECT_C_ALLOWED_APPROVERS` | Named `input` submitter restriction in `Jenkinsfile` |
| `JENKINS_LOCAL_VIEWER_ID` | Read-only observer | `Overall/Read`, `Job/Read`, `View/Read` only | Unauthorized fixture subject; cannot satisfy submitter gate |
| `TRUSTED_GIT_SHA` | Release input | Selects commit fetched before Validate/Build | Required 40-char lowercase hex; `refs/` and non-SHA rejected before `git fetch`; FETCH_HEAD must equal trusted SHA |
| Host Docker socket + `user: root` | Local control-plane privilege | Container can drive host Docker | Retained local residual; **not** claimed as hardened isolation |
| `./:/workspace:ro` + `file:///workspace` SCM | Operator workspace bind | Job DSL loads `Jenkinsfile` from workspace tip (`branch('*/master')`) | Local single-operator fixture; script-load tip is residual, not Phase 5 trusted-release-input defect |

Credential values exist only as external `${JENKINS_LOCAL_*}` injections. Repository source defines variable names and `${VAR:?...}` fail-closed Compose interpolation; it does not ship usable default passwords.

## Findings

No new critical or high findings. No new issue ID is required from this review.

### Closed relative to PC-001 (local remediation supported; ledger close deferred to P5-T08)

| Original PC-001 defect | Current disposition | Evidence |
|---|---|---|
| Default administrator password in Compose/docs | Remediated | `compose.yaml:38-43` requires all six identity vars; README/runbook require external local-only placeholders; static tests reject `change-me-locally` / legacy `JENKINS_ADMIN_*` |
| Every authenticated user has administrative authority | Remediated | `infra/jenkins/casc.yaml:15-45` uses `roleBased` (`role-strategy` plugin); `loggedInUsersCanDoAnything` absent; viewer lacks Job/Build |
| Production approval not restricted to named submitters | Remediated | `Jenkinsfile:82-86` fails closed without `PROJECT_C_ALLOWED_APPROVERS` and passes `submitter:`; governing proof `unauthorized_status=400` with `X-Error=You need to be local-approver to submit this.`, pause at `FIXTURE_AWAITING_APPROVAL`, final `ABORTED`, no production continuation |

### Closed relative to PC-014 (trusted-input)

Release input is immutable SHA-only. `Jenkinsfile:11,21-38` and `scripts/validate_jenkinsfile.py` reject `TRUSTED_GIT_REF`, `refs/` prefixes, and non-40-hex inputs before fetch; contract tests cover arbitrary branch/tag rejection. Retained P5-T03 evidence shows `valid: true`.

### Advisory — accepted residual risks (non-blocking for Phase 5)

| Severity | Finding | Disposition |
|---|---|---|
| Advisory | `compose.yaml:35,47` runs Jenkins as `root` and mounts `/var/run/docker.sock`. Dockerfile builds as root then switches to `USER jenkins`, but Compose overrides to root for the local demo. | Documented Phase 5 residual from eng review. Authorization fix does **not** eliminate host Docker control-plane risk. Do not claim multi-tenant or production-ready host isolation. |
| Advisory | `infra/jenkins/casc.yaml:71-72` loads the pipeline script via `cpsScm` `branch('*/master')` from `file:///workspace`. Runtime release trust is enforced inside the loaded Jenkinsfile by `TRUSTED_GIT_SHA`. | Acceptable for local operator-owned workspace. Future shared/remote SCM would need script-load binding to the same trusted commit; out of Phase 5 claim scope. |
| Advisory | `TRUSTED_GIT_SHA` is operator-supplied at job start; there is no separate pre-approved SHA registry. | Matches eng-review / change-review Phase 5 contract. Operator with Job/Build can choose any reachable commit SHA; named approval still gates production-like promotion. |
| Advisory | Local admin retains `Overall/Administer` and delivery-job build rights. Jenkins administrators may retain broader controller power than the submitter list alone. | Expected for a local admin identity. Unauthorized-denial proof correctly targets the read-only viewer, not admin bypass. |
| Advisory | `evidence/phase-5/qa.txt` records local placeholder password strings (`placeholder-*-password`) used for Compose config rendering. | Labeled local-only fake credentials, not production secrets. Acceptable for local evidence; do not reuse as shared defaults. |

## Secret exposure and unsupported-claim checks

- **Source / config:** No hardcoded Jenkins passwords, tokens, or cloud credentials in `compose.yaml`, `casc.yaml`, `Jenkinsfile`, or Dockerfile. Passwords are `${ENV}` placeholders only.
- **Evidence:** Phase 5 evidence contains placeholder identity names, Jenkins public instance-identity material, and ephemeral local crumb/session headers from the fixture. No live cloud credentials or production secrets observed in the governing proof or QA record.
- **Claims:** Change review, QA, and this security review preserve the local-only boundary. No artifact reviewed here asserts live production approval, cloud validation, digest promotion as a completed Phase 5 outcome, PC-002 durable evidence, or PC-003 rollback recovery.
- **Untrusted execution:** PR/GitHub path is outside this gate. Local Jenkins delivery job is a production-like local fixture with named roles; unauthorized viewer cannot advance approval.

## Independent validation

| Check | Result |
|---|---|
| `git diff HEAD` | Phase 5 remediation present: external identities, role-based JCasC, named submitter, `TRUSTED_GIT_SHA` gate, validator/tests, docs credential boundary |
| `.venv\Scripts\python.exe -m pytest -q` | Pass — 75 passed, 96.59% coverage, exit 0 |
| Governing unauthorized proof | Supports named-approver denial without production continuation |
| P5-T03 validator evidence | `valid: true`, `errors: []` |

## PC-001 and follow-on gates

- Local security evidence **supports** resolving PC-001 at the integrated evidence gate once P5-T08 confirms all declared Phase 5 artifacts agree.
- This task does **not** modify `ISSUES.md` / authoritative state. Orchestrator should keep PC-001 open until P5-T08.
- PC-002 (append-only evidence + approver persistence) and PC-003 (verified rollback) remain hard Phase 6 blockers and are untouched.
- No critical/high finding requires a new issue from P5-T07.

## Verdict

**Clear.** Proceed to P5-T08 integrated evidence. Phase 5 local Jenkins security boundary remediation is acceptable under the local-only claim: credentials are externally supplied, authorization is role-based with named approvers, trusted input is immutable SHA with pre-fetch ref rejection, and unauthorized promotion is denied in the retained local fixture. Residual Docker-socket/root and SCM script-load tip risks remain explicitly accepted and must not be rebranded as isolation or production readiness.
