# Phase 6 Retrospective: Promotion Evidence and Recovery Cycle

Date: 2026-07-13  
Scope: Phase 6 shared evidence and recovery contract for `PC-002` and `PC-003`, including design freeze (`P6-T00`), engineering review (`P6-T01`), append-only evidence (`P6-T02`), rollback-target gating and recovery verification (`P6-T03`), Jenkins integration and local fixtures (`P6-T04`), change review, QA, security review, and integrated evidence (`P6-T05`–`P6-T08`).  
Phase outcome: local remediation of `PC-002` and `PC-003` verified under an explicit non-E2E claim; retrospective gate active.  
Claim boundary: local-only / production-like / non-E2E. This retrospective does not claim live Jenkins runtime promotion, live cloud, AWS, organizational Jenkins administration, sustained production operation, organizational digest promotion, or Phase 9 live-cloud authorization. Phase 7 planning may continue under existing authorization; residual advisories must not be rebranded as cleared organizational readiness.

## Expected Versus Actual

| Area | Expected | Actual | Evidence |
| --- | --- | --- | --- |
| Lead time | Spec → eng-review → parallel evidence/recovery slices → Jenkins integration → independent gates → local resolve of `PC-002` / `PC-003` | Calendar span was same-day (2026-07-13). Gate rhythm held: freeze → CLEAR eng-review → P6-T02/P6-T03 → P6-T04 → clear change/QA/security → PASS integrated gate → orchestrator resolved both issues | `docs/phase-6-spec.md`; `docs/reviews/phase-6-*.md`; `evidence/phase-6/integrated-gate.txt`; `ISSUES.md` |
| Failed-change detection | Shared design freeze plus eng-review catch identity/SoT defects before implementation; change review catch claim/identity escapes | Eng-review closed staging-as-prior ambiguity before code. Change/security/QA found no High blockers. Residual fidelity/honesty gaps were recorded as advisories, not silent passes | `docs/reviews/phase-6-eng-review.md`; `docs/reviews/phase-6-change-review.md`; `docs/reviews/phase-6-security-review.md` |
| Manual / fixture steps | Local fixtures prove first-release and recovery paths without requiring live Jenkins E2E for this claim | Two agreeing fixtures retained: `evidence/example/` (first-release happy path) and `evidence/phase-6/` (rollback_target_bound + recovery). Validation is pytest / validators / static Jenkinsfile contracts; `pipeline.run_id: manual` | `evidence/example/`; `evidence/phase-6/`; `evidence/phase-6/qa.txt` |
| Deployment / promotion result | Production-like promotion blocked without verified rollback target or first-release; recovery proves digest/health/version/business | Promotion-gate negatives retained (`blocked`, `first-release`, `staging-rejected`). Recovery fixture restores prior digest `sha256:aaa…` and records all four recovery checks pass | `evidence/phase-6/p6-t03-promotion-gate-*.txt`; `evidence/phase-6/events.jsonl`; `docs/change-records/phase-6-local.md` |
| Recovery time | Known scaffold defects remediated once against an approved shared contract; avoid Phase 5-style multi-class opaque fixture loops | No new mid-cycle blocking issue IDs (`PC-010`-style) were opened. Pre-existing `PC-002` / `PC-003` defects were remade into append-only events + event-backed rollback/recovery in one design cycle | `ISSUES.md`; `evidence/phase-6/integrated-gate.txt` |

## What Went Well

- Treating `PC-002` and `PC-003` as **one shared design problem** before implementation prevented conflicting SoTs (digest identity, event model, rollback readiness).
- Engineering review earned its keep by rejecting freeze ambiguity: staging-as-prior is **not** approved for production rollback claims in Phase 6.
- Parallel write-scope split (`P6-T02` evidence vs `P6-T03` recovery) then sequential Jenkins wiring (`P6-T04`) matched the eng-review dispatch recommendation and avoided overlapping schema ownership fights.
- Gate rhythm stayed clean: change review clear → QA PASS (111 tests; both fixtures validate) → security CLEAR → integrated PASS → orchestrator resolved `PC-002` / `PC-003` without inventing live-cloud claims.
- Negative promotion-gate proofs were retained as first-class evidence (`blocked`, `first-release`, `staging-rejected`), not collapsed into a single happy-path fixture.
- Claim-boundary discipline held across reviews, QA, change record, and integrated gate: local-only / production-like / non-E2E remained explicit through ledger closure.

## Root Causes Versus Symptoms

| Observed symptom | Root cause | Earlier gate that should have caught it | Escape / detection point |
| --- | --- | --- | --- |
| Staging, approval, and production could not be proven together (`PC-002`) | `scripts/evidence.py` overwrote `manifest.json` environment/status fields and did not append durable event history; Jenkins `APPROVED_BY` stayed in transient UI state | Earlier scaffold / Phase 4–5 evidence design should have required append-only events + derived summary before any production-like claim | Known critical entering Phase 6; remade by `P6-T02`/`P6-T04`; closed at integrated evidence |
| Approver identity missing from release evidence (`PC-002` symptom) | Approval persistence was never a required evidence event / summary field | Spec freeze §6 and eng-review made this mandatory before implementation | Caught by design freeze; implemented and validated in fixtures |
| First promotion could proceed with empty prior digest (`PC-003`) | Production stage derived rollback identity from env-file / empty prior without XOR first-release decision | Scaffold promotion gate lacked verified-target-or-decision fail-closed rule | Known critical; remade by `P6-T03`/`P6-T04`; promotion-gate proofs retained |
| “Rollback” restored env file without proving restored digest/health/version/business (`PC-003`) | Recovery was operational restart/env restore, not verification against a bound verified digest | Scaffold rollback scripts treated `previous.env` as authoritative | Known critical; remade so `previous.env` is non-authoritative cache; recovery `--mode recovery` required |
| Freeze text allowed “staging-as-prior when contractually allowed” without rules | Spec under-specified an alternate SoT that would undermine production rollback identity | `P6-T00` freeze should have closed it; eng-review correctly rejected it for Phase 6 production claims | Caught at `P6-T01` before implementation; no new issue required |
| Verified event payloads can disagree with probe JSON in a future regression | Jenkinsfile appends literal pass maps for verified/recovery checks instead of piping `verify_deployment.py` output | Change-review / Jenkins integration acceptance could require captured verify JSON in event `details` | Advisory at change + security review; not fail-open today because deploy/rollback exit non-zero before happy-path appends |
| Wrong but syntactically complete `VERIFIED_ROLLBACK_*` parameters could bind an unverified digest | Rollback-target fields are operator-attested parameters, not auto-loaded from prior `production_verified` evidence | Acceptable under local honesty claim; stronger prior-evidence binding needed before org-production claims | Advisory retained through integrated gate; must not be weakened by calling `PC-003` “fully automated” |
| Compose-config evidence retains local placeholder password env values | Local Phase 5 fake-credential pattern leaked into retained `p6-t03-compose-config.txt` | Evidence hygiene / redaction guidance for config dumps | Advisory; not production secret exposure; do not promote as hygiene exemplar |

Important distinction retained: Phase 6 local closure of `PC-002` / `PC-003` rests on **validators + deploy/rollback/verify scripts + static Jenkinsfile contracts + agreeing local fixtures**, not on a live Jenkins end-to-end promotion/recovery run. That split is acceptable for the local-only / non-E2E claim and must not be upgraded into a runtime E2E or live-cloud claim without new authorized evidence.

## Harness, Evidence, and Scope Lessons

### Harness improvements

1. **Shared design freeze before dual-issue implementation:** freezing append-only events, digest identity, rollback SoT, and recovery checks as one contract prevented evidence-only or recovery-only half-fixes.
2. **Eng-review must close SoT ambiguities:** “staging-as-prior when contractually allowed” would have been an implementation landmine; rejecting it early was cheaper than post-implementation rework.
3. **Retain negative gate proofs:** blocked / first-release / staging-rejected artifacts make the fail-closed story inspectable without re-running every gate.
4. **Separate evidence fidelity from fail-closed control:** hardcoded verify maps are not today’s fail-open path, but they are a future regression surface; treat fidelity follow-ups as harness work, not as weakening current gates.
5. **Do not conflate local fixture validation with Jenkins E2E:** QA and integrated correctly refused to upgrade `pipeline.run_id: manual` into a live promotion claim.

### Evidence discipline

- Preserve both happy-path fixtures (`example` first-release; `phase-6` recovery) and negative promotion-gate proofs.
- Derived `manifest.json` must remain regenerable from `events.jsonl`; overwrite-without-event stays forbidden.
- Change records must cite event-backed commit, digest, approver, timestamps, and rollback target / first-release decision — never invent them.
- Failed or advisory evidence (including compose placeholder leakage) stays inspectable; do not delete it to manufacture a cleaner package.
- Integrated gate correctly deferred ledger closure to the orchestrator and preserved the non-E2E claim while recommending resolve of `PC-002` / `PC-003`.

### Scope control

- `PC-002` / `PC-003` resolutions remain local-only / non-E2E; they do not authorize Phase 9 live-cloud work.
- Phase 5 residuals (Docker socket + root Compose controller, `cpsScm` tip, `cleanWs` archive risk) stay outside the Phase 6 evidence/recovery claim.
- Operator-attested rollback parameters and hardcoded verify maps remain accepted residuals under the local claim; they are not silent defects and must not be rebranded as fully automated prior-evidence binding.
- Phase 7 security and failure-injection lanes may continue; they must not treat Phase 6 fixture agreement as live runtime proof.

## Defect Escape Map (Gate Timing)

| Gate | Caught well | Missed or under-specified |
| --- | --- | --- |
| `phase-6-spec` (`P6-T00`) | Append-only model; recovery checks; first-release fields; local claim boundary | Staging-as-prior phrase left ambiguous until eng-review |
| `phase-6-engineering-review` | Digest SoT; rejected staging-as-prior; env-file non-authoritative; required negatives; parallel dispatch | Did not yet require captured verify JSON or auto prior-evidence lookup (acceptable for local claim) |
| `P6-T02` / `P6-T03` / `P6-T04` | Append-only + derived summary; promotion XOR; identity-bound RepoDigest; recovery suite; agreeing fixtures | Jenkins verified-event fidelity still literal maps; rollback params still operator-attested |
| `phase-6-change-review` | Cleared implementation under non-E2E boundary; recorded advisories without inventing High blockers | N/A for pre-existing scaffold defects (already remade) |
| `phase-6-qa` / `phase-6-security-review` / integrated | Independent agreement; negative proofs; recommend resolve without claim overreach | Did not execute live Jenkins E2E (correct for claim); residuals left explicit |

## Remaining Risk Boundaries (Do Not Weaken)

| Risk | Impact | Status |
| --- | --- | --- |
| Non-E2E synthetic fixtures (`pipeline.run_id: manual`) | Local validators can pass without proving a live Jenkins promotion/recovery runtime | Accepted Phase 6 claim boundary; do not upgrade without new evidence |
| Operator-attested `VERIFIED_ROLLBACK_*` parameters | Syntactic gate can bind an unverified prior digest if the operator is wrong | Accepted local honesty residual; stronger binding before org-production claims |
| Hardcoded Jenkinsfile verified/recovery check maps | Evidence `details` may not equal probe JSON if a future stage appends without verify | Accepted fidelity residual; deploy/rollback still fail closed today |
| Docker socket + root Compose controller | Local controller retains host Docker control-plane privilege | Accepted Phase 5 residual; out of Phase 6 evidence claim |
| `cpsScm` tip / `cleanWs` archive loss | Script-load tip and unarchived evidence loss remain local residuals | Accepted; keep claims honest |
| Compose-config evidence placeholder passwords | Local fake credentials appear in retained config dump | Advisory hygiene; not production secret exposure |
| Live cloud / AWS / Phase 9 digest promotion | Unauthorized and unverified | Explicitly out of scope; Phase 6 resolution must not be read as authorization |

## Follow-up Actions

| Action | Owner | Acceptance criterion | Target phase |
| --- | --- | --- | --- |
| Capture `verify_deployment.py` JSON output into Jenkinsfile verified/recovery event `details` instead of literal pass maps | future Jenkins integration / evidence-fidelity worker | Staging, production, and recovery append events include probe-derived check maps; contract test fails if verified events are appended without a preceding successful verify artifact binding | Phase 7 hardening slice (or next Jenkins evidence-fidelity change) |
| Auto-load and prove `VERIFIED_ROLLBACK_*` from prior release `production_verified` / `recovery_verified` evidence when available | future recovery / evidence worker | Production rollback-target bind fails closed unless fields match a retained prior evidence record (or an explicit first-release decision remains); operator free-text alone is insufficient for any claim beyond local honesty demos | Before any organizational production claim (still unauthorized); design review in Phase 7+ if scope expands |
| Keep negative promotion-gate and recovery fixtures as mandatory retained evidence for any future evidence/recovery change | Phase 7 QA / integrated owners | Diffs that touch promotion gate or recovery must refresh or re-validate blocked / first-release / staging-rejected (or equivalent) proofs plus at least one recovery path | Phase 7 and later evidence/recovery changes |
| Redact or quarantine local placeholder credential values from retained Compose-config evidence dumps | local evidence hygiene / Phase 8 portfolio packager | Portfolio or shared evidence packages do not present `local-*-password` dumps as hygiene exemplars; placeholders either redacted or clearly labeled local-fake only | Phase 8 portfolio packaging (optional cleanup earlier) |
| Preserve append-only events + derived-summary contract; reject overwrite-without-event regressions | future evidence workers / eng-review | Validators fail closed on rewritten/truncated events or summary gate fields that cannot be derived from the event log | Any future evidence schema change |
| Preserve digest-targeted recovery (health, version, business, deployed digest); never treat env-file restore alone as recovery | future recovery workers / security review | Recovery claim without all four checks + matching restored digest fails validation; `previous.env` remains non-authoritative | Any future rollback/recovery change |
| Revisit Docker-socket/root controller isolation only under a dedicated security design review | future security reviewer | Any isolation claim cites a reviewed design that removes or bounds host Docker control-plane exposure; until then residual risk stays explicit | Post–Phase 6 security design (not Phase 6 closure) |
| If a later claim asserts live Jenkins E2E promotion/recovery, require runtime evidence beyond synthetic fixtures | future Phase 7+ runtime / ship owners | Retained evidence shows a real controller run with bound digests, approval persistence, and recovery verification in one attempt-scoped artifact set; fixtures alone are insufficient | Only if claim scope expands (not authorized by Phase 6) |
| Continue Phase 7 security and failure-injection lanes without importing Phase 6 fixture agreement as live-cloud readiness | Phase 7 eng-review / orchestrator | Phase 7 plans cite Phase 6 local-only / non-E2E boundary and do not authorize Phase 9 live-cloud activity | Phase 7 |

## Evidence Index

- `docs/phase-6-spec.md` — frozen shared `PC-002` / `PC-003` contract.
- `docs/reviews/phase-6-eng-review.md` — CLEAR shared design; rejected staging-as-prior; kept issues open until evidenced.
- `docs/reviews/phase-6-change-review.md` — clear after P6-T02–P6-T04; advisories on fidelity and operator-attested rollback params.
- `docs/reviews/phase-6-security-review.md` — CLEAR local security gate; ledger close deferred to integrated evidence.
- `docs/change-records/phase-6-local.md` — event-backed local recovery-demo change record.
- `evidence/phase-6/qa.txt` — independent QA PASS; non-E2E boundary; issues left open at QA time.
- `evidence/phase-6/integrated-gate.txt` — agreeing local evidence set; recommend resolve `PC-002` / `PC-003`.
- `evidence/example/events.jsonl` + `manifest.json` — first-release happy-path fixture.
- `evidence/example/p6-t02-pytest.txt` / `p6-t02-cli-evidence.txt` — append-only evidence slice proofs.
- `evidence/phase-6/events.jsonl` + `manifest.json` — recovery-demo fixture with bound prior digest.
- `evidence/phase-6/p6-t03-promotion-gate-blocked.txt` — promotion blocked without target+decision.
- `evidence/phase-6/p6-t03-promotion-gate-first-release.txt` — first-release path allowed.
- `evidence/phase-6/p6-t03-promotion-gate-staging-rejected.txt` — staging-as-prior forbidden.
- `evidence/phase-6/p6-t03-pytest.txt` / `p6-t03-compose-config.txt` — recovery slice proofs (compose dump retains local placeholders; advisory).
- `evidence/phase-6/p6-t04-*.txt` — Jenkins integration static/fixture validation set.
- `ISSUES.md` — `PC-002` and `PC-003` resolved under local-only / non-E2E claim; continue lanes include Phase 6 retrospective and Phase 7 planning.
