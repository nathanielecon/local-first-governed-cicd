# Phase 5 Retrospective: Jenkins Authorization Remediation Cycle

Date: 2026-07-13  
Scope: Phase 5 local Jenkins authorization remediation for `PC-001`, including implementation slices, diagnostic blocked-loop tasks (`P5-T11`–`P5-T14`), trusted-input rework (`PC-014`), change review, QA, security review, and integrated evidence.  
Phase outcome: local remediation verified; retrospective gate active.  
Claim boundary: local-only. This retrospective does not claim live production, cloud activity, digest promotion, durable multi-environment evidence (`PC-002`), or verified rollback recovery (`PC-003`).

## Expected Versus Actual

| Area | Expected | Actual | Evidence |
| --- | --- | --- | --- |
| Lead time | Bounded local remediation of credentials, least-privilege roles, named approvers, trusted input, and unauthorized denial after eng-review approval | Eng review cleared design on 2026-07-12; integrated evidence cleared on 2026-07-13. Calendar span was short, but wall-clock rework was dominated by a multi-issue `P5-T04` blocked loop and one post-implementation trusted-input repair | `docs/reviews/phase-5-eng-review.md`; `evidence/phase-5/integrated-gate.txt`; `ISSUES.md` (`PC-010`–`PC-014`) |
| Failed-change detection | Static contracts and independent change review catch authz defects before QA/security/integrated gates | Credential externalization, role strategy, and named-approver contracts largely held. The decisive security escape was `TRUSTED_GIT_REF` accepting arbitrary refs (`PC-014`), caught at change review after first implementation, not at eng-review or static acceptance wording alone | `docs/reviews/phase-5-change-review.md`; `evidence/phase-5/p5-t03-pytest.txt`; `evidence/phase-5/p5-t03-validate-jenkinsfile.txt` |
| Manual / fixture steps | One isolated unauthorized-denial fixture run after `P5-T01`–`P5-T03` | Fixture path required four extra remediation/diagnostic tasks before a governing proof existed: JCasC shape (`P5-T11`/`PC-010`), evidence disambiguation (`P5-T12`/`PC-011`), image rebuild (`P5-T13`/`PC-012`), crumb/session path (`P5-T14`/`PC-013`) | `ISSUES.md`; `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt` |
| Deployment / promotion result | No production continuation after unauthorized approval | Governing proof shows `unauthorized_status=400`, explicit `X-Error=You need to be local-approver to submit this.`, pause at `FIXTURE_AWAITING_APPROVAL`, final `ABORTED`, no production-continuation marker | `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt`; `evidence/phase-5/qa.txt` |
| Recovery time | Failures should be diagnosable within one repair attempt per class | Same-class ambiguity was reduced once attempt-scoped evidence existed. Image drift and crumb/session defects were then isolated and closed in single-owner slices rather than repeated opaque retries | `PC-011`→`PC-013` resolutions in `ISSUES.md` |

## What Went Well

- Scope control held. Reviews and gates consistently preserved the local-only claim and left `PC-002` / `PC-003` open as Phase 6 hard blockers.
- Diagnostic tasking after the first opaque `P5-T04` failures was high value. `P5-T12` separated mixed logs from real load-path failure; `P5-T13` proved stale image content; `P5-T14` moved the fixture past CSRF/session noise into the decisive authorization check.
- Independent change review earned its keep by rejecting a syntactically “controlled reference” trusted-input design that still allowed arbitrary branch/tag fetch (`PC-014`), forcing immutable `TRUSTED_GIT_SHA` binding with pre-fetch rejection.
- Gate rhythm after the trusted-input repair was clean: change review clear → QA pass (75 tests, fail-closed bare Compose) → security clear → integrated evidence agreement → orchestrator resolved `PC-001` without weakening Phase 6 blockers.
- Failed evidence was retained rather than overwritten into a false pass. Attempt-scoped `p5-t04-*-*.txt` artifacts and the governing unauthorized proof remain inspectable.

## Root Causes Versus Symptoms

| Observed symptom | Root cause | Earlier gate that should have caught it | Escape / detection point |
| --- | --- | --- | --- |
| Jenkins CasC crash on `globalNodeProperties` (`PC-010`) | Static casc assertions encoded a text-valid but runtime-invalid node-property shape | Phase 5 eng-review / `P5-T01` static tests should require a runtime-proven JCasC shape, not a stale snapshot | Escaped into `P5-T04` startup; closed by `P5-T11` |
| Mixed Jenkins boot logs and unclear “stale config” narrative (`PC-011`) | Fixture evidence appended across attempts and did not bind image identity + embedded/runtime casc contents to one attempt | Fixture design / eng-review acceptance for `P5-T04` should require single-attempt, non-appended evidence with runtime identity capture before denial claims | Escaped into opaque retries; closed by `P5-T12` |
| Fixture still booted old map-shaped casc after workspace fix (`PC-012`) | Docker image/load chain reused a stale Jenkins image whose embedded casc lagged the accepted baseline | Runtime verification should force rebuild/no-cache or digest-bound image identity whenever casc content is a gate dependency | Diagnosed only after `P5-T12`; closed by `P5-T13` |
| `config.xml` update failed with crumb/session 403 (`PC-013`) | Fixture HTTP client session/CSRF handling was incomplete for job upsert | Fixture harness review should treat authenticated mutating Jenkins API paths as first-class acceptance, not incidental plumbing | Surfaced only after image drift cleared; closed by `P5-T14` |
| Trusted input still allowed arbitrary refs (`PC-014`) | Eng-review allowed “trusted commit SHA **or** controlled reference”; implementation chose a loose ref gate that still fetched operator-chosen branches/tags before approval | Eng-review contract and `P5-T03` acceptance should have required immutable 40-char SHA only (or an equally strict pre-approved registry), with static tests rejecting any `refs/` acceptance path | Escaped initial implementation; caught at independent change review; repaired before QA |
| Unauthorized denial “not yet proven” despite many fixture runs | Teams conflated startup failures, evidence ambiguity, and authz outcomes as one defect class | Orchestrator/harness should open separate issues per diagnosable class after first failure, matching the eventual `PC-010`–`PC-013` split | Process improved mid-cycle; became the successful pattern |

Important distinction retained: the governing unauthorized proof uses a stub approval pipeline and therefore does **not** re-exercise `TRUSTED_GIT_SHA` at runtime. Trusted-input assurance for Phase 5 rests on Jenkinsfile + validator + contract tests + refreshed `P5-T03` evidence. That split is acceptable for the unauthorized-approval claim, but it is a coverage gap if a later phase claims end-to-end trusted-input enforcement from the same fixture.

## Harness, Evidence, and Scope Lessons

### Harness improvements

1. **Runtime-proven config contracts:** static Jenkins/Compose fixtures must assert shapes that have been boot-proven at least once, or they become false confidence.
2. **Attempt-scoped evidence by default:** any Dockerized gate that can retry must emit unique non-appended artifacts and bind container/image identity on both success and failure paths.
3. **Separate diagnosable failure classes early:** `P5-T12`/`P5-T13`/`P5-T14` demonstrate that splitting ambiguity, drift, and CSRF into discrete owners shortens recovery versus repeating the same end-to-end fixture hope.
4. **Security-worded acceptance must be adversarial:** “controlled reference” was too weak. Prefer fail-closed immutable identifiers in the eng-review contract when the risk is untrusted code execution before approval.

### Evidence discipline

- Preserve failing attempt evidence; do not collapse retries into one file.
- Prefer governing proofs that record status, explicit denial reason, non-continuation, and terminal build result together (as in `p5-t04-manual-verify2-unauthorized-proof.txt`).
- QA correctly treated bare `docker compose config` exit 1 as positive fail-closed evidence for credential externalization.
- Integrated evidence correctly deferred ledger closure of `PC-001` to the orchestrator and refused to touch `PC-002` / `PC-003`.

### Scope control

- Residual Docker-socket + `user: root` risk remained advisory and was never rebranded as isolation.
- `cpsScm` `branch('*/master')` script-load tip remains a local operator-workspace residual, not a Phase 5 trusted-release-input defect, because runtime release trust is enforced after load by `TRUSTED_GIT_SHA`.
- Stale README “Phase 1 only authorized” text remains documentation drift, not a capability claim.

## Defect Escape Map (Gate Timing)

| Gate | Caught well | Missed or under-specified |
| --- | --- | --- |
| `phase-5-engineering-review` | Local-only boundary; `PC-002`/`PC-003` out of scope; named approvers; credential externalization; residual Docker-socket risk | Trusted-input wording allowed loose “controlled reference”; fixture evidence/identity requirements under-specified |
| Implementation static tests | Credential fallbacks, role strategy presence, later SHA validator regressions | Initially accepted invalid JCasC node-property shape; initially accepted arbitrary-ref trusted input |
| `P5-T04` fixture (pre-diagnostics) | Eventually produced decisive denial proof | First loops mixed symptoms; needed dedicated diagnostic tasks |
| `phase-5-change-review` | Caught and forced closure of `PC-014`; preserved claim boundary | N/A for earlier fixture runtime defects (those were already remediated) |
| `phase-5-qa` / `phase-5-security-review` / integrated | Confirmed agreement without expanding claims; supported `PC-001` local closure | Did not need to rediscover prior defects; residual risks correctly left advisory |

## Remaining Jenkins-Risk Boundaries (Do Not Weaken)

| Risk | Impact | Status |
| --- | --- | --- |
| `PC-002` append-only release evidence + approver persistence | Staging/approval/production cannot be durably proven together | Open — Phase 6 hard blocker |
| `PC-003` verified rollback target and recovery | First promotion/recovery may lack verified restored digest/health/business checks | Open — Phase 6 hard blocker |
| Docker socket + root Compose override | Local controller retains host Docker control-plane privilege | Accepted Phase 5 residual; not isolation |
| `cpsScm` script load from workspace tip | Operator-owned workspace can load Jenkinsfile tip independently of release SHA gate | Accepted local residual; future shared SCM needs binding |
| Operator-chosen `TRUSTED_GIT_SHA` without separate registry | Builder can select any reachable commit; named approval still gates promotion | Matches Phase 5 contract; not a Phase 5 defect |
| Fixture stub vs full Jenkinsfile SHA path | Unauthorized-denial proof does not runtime-exercise trusted-input fetch | Accepted coverage split for current claim |

## Follow-up Actions

| Action | Owner | Acceptance criterion | Target phase |
| --- | --- | --- | --- |
| Require attempt-scoped Docker fixture evidence with bound image identity and captured runtime config on failure paths for any new Jenkins/Compose gate | `phase-6-spec-worker` / future fixture owners | Spec or fixture contract forbids appended multi-attempt logs as sole evidence and requires image ID + relevant casc/config capture before retry claims | Phase 6 (and later runtime fixtures) |
| Keep JCasC/Compose static tests coupled to a boot-proven shape, not text snapshots alone | future Jenkins harness / authz workers | Static test fails if node-property or credential shape diverges from the last retained successful startup/export evidence | Next Jenkins config change |
| Treat immutable commit SHA (or stricter pre-approved digest registry) as the default trusted-input eng-review requirement; reject “any valid ref” designs | future eng-review / approval workers | Eng-review and validators fail closed on `refs/` acceptance or non-immutable release selectors before fetch/execute | Phase 6 evidence binding; any future Jenkinsfile trust change |
| Carry `PC-002` into an append-only event + summary manifest contract that persists approver identity and timestamps | `phase-6-spec-worker` / evidence worker | Staging, approval, and production events can be reconstructed without overwrite; approver identity is inspectable | Phase 6 (`PC-002`) |
| Carry `PC-003` into a verified rollback-target and recovery-verification contract | `phase-6-spec-worker` / recovery worker | Promotion without verified rollback target is blocked unless an explicit first-release decision is recorded; recovery proves digest, health, version, and business behavior | Phase 6 (`PC-003`) |
| If a later claim asserts end-to-end trusted-input enforcement from the unauthorized fixture, extend the fixture beyond the stub approval pipeline | future Phase 5/6 fixture owner | Fixture evidence shows SHA pre-fetch rejection or FETCH_HEAD mismatch fail-closed behavior in the same attempt as approval gating | Only if claim scope expands |
| Revisit Docker-socket/root controller isolation only under a dedicated security design review | future security reviewer | Any isolation claim cites a reviewed design that removes or bounds host Docker control-plane exposure; until then residual risk stays explicit | Post–Phase 6 security design (not Phase 5 closure) |
| Align stale authorization wording in operator-facing docs with `PLAN.md` / `STATUS.md` without inventing new capability claims | docs / orchestrator follow-up | README/runbook authorization statements match the currently authorized phase ceiling and preserve unverified boundaries | Docs hygiene / next planning pass |

## Evidence Index

- `docs/reviews/phase-5-eng-review.md` — approved local `PC-001` remediation design; preserved `PC-002`/`PC-003`.
- `docs/reviews/phase-5-change-review.md` — clear after `PC-014` trusted-input remediation.
- `docs/reviews/phase-5-security-review.md` — clear local security gate; residual Docker-socket/root retained.
- `evidence/phase-5/qa.txt` — independent QA pass; fail-closed bare Compose; unauthorized denial supported.
- `evidence/phase-5/integrated-gate.txt` — agreeing local evidence set; recommend resolve `PC-001`; preserve Phase 6 blockers.
- `evidence/phase-5/p5-t03-pytest.txt` — trusted-input contract tests: 9 passed.
- `evidence/phase-5/p5-t03-validate-jenkinsfile.txt` — `valid: true`, `errors: []`.
- `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt` — governing local unauthorized-denial proof.
- `ISSUES.md` — `PC-001` resolved locally; `PC-010`–`PC-014` resolved; `PC-002`/`PC-003` remain open.
