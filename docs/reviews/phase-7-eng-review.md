# Phase 7 Engineering Review

Date: 2026-07-13

Reviewer role: independent Phase 7 engineering gate (`P7-T00`), fresh context.

**Verdict: CLEAR for bounded Phase 7 execution of the five isolated security / failure-injection lanes under the approved baseline below.** This review approves the local-only failure-injection design, fixture isolation rules, and fake-credential boundaries before any `P7-T01` execution. It does **not** authorize live cloud, AWS, organizational Jenkins administration, sustained production operation, Phase 9, or any claim that Phase 5 Docker-socket/root residual or Phase 6 operator-attested rollback / hardcoded verify-map residuals have been cleared. It does **not** upgrade Phase 6 local fixtures into live Jenkins E2E or live-cloud proof.

Reviewed baseline: `PROJECT.md`, `PLAN.md`, `STATUS.md`, `ISSUES.md`, `DECISIONS.md`, `AGENTS.md`, `docs/TERRA_ORCHESTRATOR_PROMPT.md` (Phase 7), `docs/failure-injection.md`, `docs/retrospectives/phase-6.md`, `docs/reviews/phase-6-eng-review.md`, `docs/reviews/phase-6-security-review.md`, `docs/reviews/phase-5-security-review.md`, `docs/runbook.md`, `Jenkinsfile`, `compose.yaml`, `.github/workflows/pr-validation.yml`, existing Phase 5 unauthorized-approval fixture scripts/tests, and Phase 6 evidence/recovery control plane (read-only).

---

## Scope

Phase 7 proves that local security and failure-injection controls reject, fail closed, or recover as designed across five parallel-isolated lanes. It is an evidence-producing pressure test against the already-closed Phase 5/6 local contracts, not a redesign of digest promotion, append-only evidence, or authorization.

| Obligation | Approved here |
| --- | --- |
| Supply-chain / secrets | Local scanners and quality gates reject documented fake-secret and vulnerable fixtures without real credentials. |
| Credential / authorization | Unauthorized promotion remains denied; only placeholder local identities and fake credentials are used. |
| Runtime / connectivity | Not-ready and dependency-unreachable conditions fail readiness/smoke before production continuation. |
| Provenance / tag drift | Missing SHA / version mismatch and mutable-tag drift do not defeat digest-targeted selection. |
| Jenkins / Docker permissions | Disposable local controller/agent permission failures are isolated via runbook; residual Docker-socket/root risk stays explicit. |
| Consolidation gate | Independent security review (`P7-T02`) then integrated evidence (`P7-T03`) require per-scenario evidence, zero unaccepted critical/high, and a pressure-usable runbook. |

`P7-T01` may proceed only against this approved baseline. Do not start Phase 7 by reopening resolved `PC-001` / `PC-002` / `PC-003` boundaries, inventing live-cloud probes, or treating Phase 6 fixture agreement as runtime E2E proof.

---

## Approved baseline (must not be reinterpreted by implementers)

### Claim boundary (local-only / non-cloud)

- Phase 7 claims are **local-only / production-like / non-cloud**.
- Forbidden without separate authorization and evidence: live AWS, live organizational Jenkins administration, sustained production operation, Phase 9 Terraform/ECR/ECS/OIDC work, and any statement that Phase 6 synthetic fixtures (`pipeline.run_id: manual`) equal live Jenkins E2E promotion/recovery.
- GitHub Actions scanner invocations, if used, may support a **locally reproduced scanner-block** claim or cite prior GitHub-verified Phase 4 evidence. They must not invent a new “GitHub blocked merge on this throwaway branch” claim without retained GitHub check evidence. Prefer local `gitleaks` / `trivy` / pytest reproductions under `evidence/phase-7/` for Phase 7 lane proofs.
- Portfolio claim labels (implemented / locally verified / GitHub-verified / externally approved / deferred) remain a Phase 8 concern; Phase 7 must not blur them.

### Fake-credential and secret boundaries

- **Fake credentials only.** Documented Gitleaks test signatures, local Compose placeholder identities (`local-*-password` / externally supplied Phase 5 placeholders), and synthetic approver IDs are allowed.
- **Real secrets are forbidden** in fixtures, throwaway branches, repository history, evidence logs, manifests, change records, Docker build contexts, and retained screenshots.
- Evidence dumps that necessarily show Compose-resolved local placeholders must label them as local-fake only; do not present them as hygiene exemplars (Phase 6 advisory retained).
- Scanners must run with redaction where available (`gitleaks --redact`). Failed evidence is preserved; do not delete failing secret-scan logs to manufacture a pass.
- No Phase 7 scenario may request, load, or probe live cloud tokens, AWS keys, production passwords, or organizational credential stores.

### Isolated test fixtures

- Each lane owns an exclusive evidence subtree: `evidence/phase-7/<lane-id>/`.
- Shared mutable runtime state (Compose deploy profile, local registry tags used by a lane, Jenkins job parameters for a disposable fixture) must be attempt-scoped and cleaned up so lanes cannot cross-contaminate proofs.
- Throwaway branches, temporary failing tests, vulnerable fixture trees, and fake-secret files must live only in disposable paths or disposable branches and must be removed or reverted before the lane closes, while **retaining** the redacted rejection evidence under `evidence/phase-7/<lane-id>/`.
- Do not mutate protected main as the injection vehicle. Do not permanently weaken CI thresholds, digest identity checks, or authorization gates to make a scenario pass.
- Phase 5 unauthorized-approval fixture and Phase 6 promotion/recovery fixtures may be **reused as read-only baselines** or re-run under Phase 7 evidence prefixes; they must not be rewritten into live-cloud claims.

### Digest, recovery, and Phase 6 residuals (advisory — not cleared)

- Digest promotion SoT remains: **one build, immutable digest** (`DECISIONS.md`). Tags are aliases only.
- Mutable-tag drift scenarios must prove digest deployment continues to select the recorded digest; they must not introduce tag-as-identity.
- Any recovery claim (including `DEMONSTRATE_RECOVERY` / failure-injection demos) still requires `rollback_executed` + `recovery_verified` with digest, health, version, and business checks against an event-backed verified prior (or must not claim recovery).
- **Operator-attested `VERIFIED_ROLLBACK_*` parameters** remain an accepted Phase 6 honesty residual. Phase 7 may document the residual under pressure; it must **not** claim automated prior-evidence binding is implemented unless a separately approved hardening slice lands with tests.
- **Hardcoded Jenkinsfile verified/recovery check maps** remain an accepted fidelity residual. Phase 7 must not treat literal pass maps as independent probe proof that residual is gone.
- **Host Docker socket + Compose `user: root`** remain an accepted Phase 5 controller-isolation residual. The Jenkins/Docker permission lane proves runbook isolation of a permission/socket failure mode; it does **not** clear or rebrand that residual as hardened multi-tenant isolation.
- `cpsScm` tip load and `cleanWs` archive-loss residuals remain accepted; preserve/fail closed on missing required evidence.

### Control-plane baseline (read-only for design; inject via fixtures/params)

Approved injectable surfaces for `P7-T01` without redesign:

| Surface | Allowed injection | Forbidden reinterpretation |
| --- | --- | --- |
| `Jenkinsfile` | Existing params (`TRUSTED_GIT_SHA`, `FIRST_RELEASE`, `DEMONSTRATE_RECOVERY`, `VERIFIED_ROLLBACK_*`); disposable fixture pipelines under test fixtures | Permanent removal of Failure Injection / recovery gates; weakening named approvers |
| `compose.yaml` / deploy profile | Env toggles `STAGING_READY` / `PRODUCTION_READY`; disposable permission/socket fixtures | Claiming root+socket residual cleared |
| `.github/workflows/pr-validation.yml` | Local reproduction of gitleaks/trivy/quality commands against fixtures | Lowering CRITICAL/HIGH exit thresholds permanently |
| `scripts/verify_deployment.py` / deploy/rollback | Negative host / digest / readiness fixtures | Treating `previous.env` as verified rollback SoT |
| Phase 5 unauthorized fixture | Re-run or cite under Phase 7 evidence prefix | Expanding to live org Jenkins |

`P7-T01` write scope remains `tests/`, `scripts/`, `evidence/phase-7/` only. Changes to `Jenkinsfile`, `compose.yaml`, workflows, or `ISSUES.md` are out of implementation write scope unless a later authorized task expands it.

---

## Lane catalog

Five lanes. Evidence root: `evidence/phase-7/`. Naming: `evidence/phase-7/<lane-id>/<scenario-id>-<artifact>.txt` (plus any structured JSON/JSONL the scenario needs). Failed and passing outputs are both retained.

### Lane A — `supply-chain` (supply-chain / secrets)

| Scenario ID | Injection | Expected reject / fail / recover | Evidence path convention |
| --- | --- | --- | --- |
| `A-lint-test` | Temporary failing test or lint defect in a disposable fixture/branch | Local quality gate (pytest/ruff or equivalent contract) rejects; no merge/promotion continuation claimed | `evidence/phase-7/supply-chain/A-lint-test-*.txt` |
| `A-fake-secret` | Documented Gitleaks test signature only (never a real secret) | Gitleaks detect fails closed with redaction; fixture removed/reverted after evidence capture | `evidence/phase-7/supply-chain/A-fake-secret-*.txt` |
| `A-vuln-component` | Known-vulnerable fixture tree/branch for Trivy fs scan | Trivy exits non-zero at CRITICAL/HIGH threshold; fixture disposed | `evidence/phase-7/supply-chain/A-vuln-component-*.txt` |

### Lane B — `credential` (credential / authorization)

| Scenario ID | Injection | Expected reject / fail / recover | Evidence path convention |
| --- | --- | --- | --- |
| `B-unauthorized-promotion` | Attempt production approval / promotion as non-approver using local placeholder identities only | Denial or pause without production continuation (Phase 5 fixture contract or equivalent local proof) | `evidence/phase-7/credential/B-unauthorized-promotion-*.txt` |
| `B-fake-cred-boundary` | Prove scenario materials contain only documented local-fake / test-signature credentials | No real secret patterns in retained evidence; scanners/redaction notes recorded | `evidence/phase-7/credential/B-fake-cred-boundary-*.txt` |

### Lane C — `runtime` (runtime / connectivity)

| Scenario ID | Injection | Expected reject / fail / recover | Evidence path convention |
| --- | --- | --- | --- |
| `C-not-ready` | `STAGING_READY=false` (or equivalent readiness false) | Staging smoke/readiness fails; production gate unreachable | `evidence/phase-7/runtime/C-not-ready-*.txt` |
| `C-dependency-unreachable` | Fixture service / dependency pointed at invalid host | Readiness or contract verification identifies connectivity failure | `evidence/phase-7/runtime/C-dependency-unreachable-*.txt` |

### Lane D — `provenance` (provenance / tag drift)

| Scenario ID | Injection | Expected reject / fail / recover | Evidence path convention |
| --- | --- | --- | --- |
| `D-missing-provenance` | Build/deploy fixture without expected SHA / version binding | `/version` or smoke rejects mismatch; promotion does not claim success | `evidence/phase-7/provenance/D-missing-provenance-*.txt` |
| `D-mutable-tag-drift` | Move/retarget a test tag after recording digest | Digest-targeted deploy/verify continues to select recorded digest; tag alias drift does not change identity | `evidence/phase-7/provenance/D-mutable-tag-drift-*.txt` |
| `D-production-regression` | Production-like fixture with `APP_READY=false` / verification failure after bind | Failure recorded; digest-targeted rollback + recovery verification when recovery is claimed | `evidence/phase-7/provenance/D-production-regression-*.txt` |

### Lane E — `jenkins-docker` (Jenkins / Docker permissions)

| Scenario ID | Injection | Expected reject / fail / recover | Evidence path convention |
| --- | --- | --- | --- |
| `E-docker-permission` | Disposable local controller/agent without usable Docker access (or equivalent permission fault) | Failure mode identified; `docs/runbook.md` Jenkins/Docker isolation steps usable under pressure; **no** claim that host socket/root residual is remediated | `evidence/phase-7/jenkins-docker/E-docker-permission-*.txt` |
| `E-runbook-pressure` | Operator follows runbook against the captured failure | Runbook steps are executable and cite local-only boundary; evidence notes residual Docker-socket/root advisory remains | `evidence/phase-7/jenkins-docker/E-runbook-pressure-*.txt` |

Lane-level passes never substitute for `P7-T02` / `P7-T03` integration.

---

## Failure modes (design challenges)

| Class | Challenge | Required response |
| --- | --- | --- |
| Secret exposure | Real credential enters fixture or history | Immediate fail; preserve evidence; escalate — do not continue lane as pass |
| Claim inflation | Phase 6 fixture or Phase 7 local scan rebranded as live E2E / AWS | Reject claim; keep local-only wording in evidence headers |
| Residual laundering | Docker permission demo claimed as isolation fix; operator-attested rollback claimed as auto prior-binding; literal verify maps claimed as probe fidelity | Forbidden; residual advisories stay explicit |
| Cross-lane contamination | Shared deploy state or shared evidence files mixed across attempts | Attempt-scoped dirs; cleanup; one conclusion per lane subtree |
| Threshold weakening | Lower Trivy/gitleaks/pytest gates to pass a fixture | Forbidden; dispose fixture instead |
| Tag-as-identity | Mutable tag used as promotion/rollback identity | Forbidden; digest remains SoT |
| Partial recovery | Rollback restores env/container without four recovery checks | Must not claim `recovery_verified` |
| Evidence loss | `cleanWs` / missing archive deletes required proofs | Fail closed; retain raw outputs under `evidence/phase-7/` |
| Parallel write overlap | Concurrent workers mutate same `scripts/` helpers | See dispatch rules below |

---

## Challenges and findings

| Severity | Finding | Affected artifact | Disposition |
| --- | --- | --- | --- |
| Advisory (known residual) | Host Docker socket + Compose root controller retain host control-plane privilege. | `compose.yaml`, Phase 5/6 security reviews | **Not cleared by Phase 7.** Lane E proves failure isolation / runbook usability only. No new issue required for design approval. |
| Advisory (known residual) | `VERIFIED_ROLLBACK_*` remain operator-attested; not auto-loaded from prior `production_verified` evidence. | `Jenkinsfile`, Phase 6 security/change reviews | **Not cleared by Phase 7.** Keep honesty residual visible. Optional future issue if a hardening slice is authorized; suggested ID for orchestrator if opened later: `PC-015` (prior-evidence rollback bind). |
| Advisory (known residual) | Hardcoded verified/recovery check maps in Jenkinsfile are fidelity risk, not today’s fail-open path. | `Jenkinsfile` | **Not cleared by Phase 7.** Suggested future issue ID if hardening authorized: `PC-016` (probe-derived verify maps). |
| Advisory | Draft `docs/failure-injection.md` lacks lane IDs, evidence subtree rules, and residual-claim guards. | `docs/failure-injection.md` | Closed for execution by **this review’s approved baseline**; implementers follow this document. Optional later docs sync is non-blocking. |
| Major (dispatch constraint, in-scope) | Five “parallel” lanes share `P7-T01` write scope (`tests/`, `scripts/`, `evidence/phase-7/`), so naive parallel workers can collide on shared helpers. | `PLAN.md` `P7-T01`, `AGENTS.md` | **Approved mitigation:** partition evidence by lane; parallelize only non-overlapping test/fixture trees; serialize any shared `scripts/` harness edits. Sequential single-worker execution of all lanes is also approved. |
| Major (claim constraint, in-scope) | Supply-chain draft text implies GitHub merge blocks; Phase 7 may lack live PR evidence. | `docs/failure-injection.md`, `.github/workflows/pr-validation.yml` | **Approved mitigation:** local scanner/quality reproductions are sufficient for Phase 7 local claims; do not invent GitHub-merge-block claims without GitHub check evidence. |

No **new critical** design finding and no undecided architecture path that blocks `P7-T01` after the fixture, credential, claim-boundary, and dispatch constraints above.

**Critical design risks before execution:** none requiring a new open issue. Suggested future IDs `PC-015` / `PC-016` are optional hardening trackers only — **do not open them as Phase 7 execution blockers** unless the orchestrator expands scope to remediate those residuals inside Phase 7. `ISSUES.md` was not modified by this review.

---

## Required tests and evidence

`P7-T01` and later QA / security consolidation must fail closed on at least:

1. **Fake-credential only** — real-secret patterns in fixtures or retained evidence fail the lane.
2. **Per-scenario evidence** — each catalog scenario above has retained raw output under its lane subtree proving expected rejection, failure, or recovery.
3. **No production continuation on authz deny** — unauthorized promotion does not deploy production.
4. **Readiness/connectivity fail closed** — not-ready / unreachable dependency blocks promotion path.
5. **Provenance / digest identity** — SHA/version mismatch rejected; tag drift does not change selected digest.
6. **Recovery completeness when claimed** — recovery claims include digest + health + version + business checks against bound verified prior.
7. **Residual honesty** — evidence/runbook text must not claim Docker-socket/root, operator-attested rollback bind, or hardcoded verify-map residuals are cleared.
8. **Claim boundary** — artifacts must not assert live cloud / AWS / org-production / Phase 9 authority.
9. **Pressure-usable runbook** — Jenkins/Docker failure path cites actionable `docs/runbook.md` steps with local-only boundary preserved.
10. **Negative proofs retained** — do not delete failing scanner/permission/readiness outputs to manufacture a clean package.

Minimum automation expected:

- Pytest (or equivalent) contracts for fixture helpers and any new scripts under `tests/`.
- Full suite still green: `.venv\Scripts\python.exe -m pytest -q`.
- Lane evidence index files sufficient for `P7-T02` to cite every scenario.

Gate after lanes: `P7-T02` consolidates with zero unaccepted critical/high; `P7-T03` requires agreeing evidence and preserved non-cloud boundary.

---

## Dispatch recommendation

1. Orchestrator records this gate **CLEAR** and may dispatch `P7-T01`.
2. Approved baseline for `P7-T01`: this document’s fixture/fake-credential rules, five-lane catalog, evidence path convention, residual-advisory posture, and local-only claim boundary.
3. Preferred execution: one implementation worker runs lanes A→E sequentially **or** parallelizes only when write trees do not overlap (exclusive `evidence/phase-7/<lane-id>/` and non-overlapping test fixture paths; shared `scripts/` edits serialized).
4. Continue lanes after successful `P7-T01`: `P7-T02` (security consolidation), then `P7-T03` (integrated evidence).
5. Blocked / unauthorized lanes: live cloud, AWS, Phase 9, organizational Jenkins hardening claims, and any work that reopens resolved Phase 5/6 issue boundaries as if uncleared without new evidence of regression.
6. Do not open `PC-015` / `PC-016` unless intentionally authorizing residual-hardening scope beyond failure-injection evidence.

---

## Validation executed by this review

| Command | Result |
| --- | --- |
| `.venv\Scripts\python.exe scripts\project_cli.py validate state` | Passed |
| `.venv\Scripts\python.exe -m pytest -q` | Passed — 111 tests |

These checks confirm harness/state health for the review lane. They do **not** prove Phase 7 failure-injection execution.

---

## Final gate statement

**CLEAR** for Phase 7 security and failure-injection design under the approved baseline above.

- Approved baseline: five isolated lanes (`supply-chain`, `credential`, `runtime`, `provenance`, `jenkins-docker`); fake credentials only; `evidence/phase-7/<lane-id>/` evidence convention; local-only / non-cloud claim boundary; Phase 5/6 residuals remain advisory and uncleared.
- Required tests: per-scenario rejection/failure/recovery evidence; fake-secret and claim-boundary fail-closed checks; runbook pressure path for Docker/Jenkins permission failure; full pytest green.
- Critical design risks requiring issue IDs before execution: **none**. Optional future hardening IDs only: `PC-015` (auto prior-evidence rollback bind), `PC-016` (probe-derived verify maps) — not blockers.
- Continue lanes after orchestrator records this gate: `P7-T01`.
- Blocked lanes: live-cloud / AWS / Phase 9; residual-laundering claims; overlapping parallel writes to shared scripts without serialization.
