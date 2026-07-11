# Phase 2 Retrospective: Local Application Evidence Cycle

Date: 2026-07-11  
Scope: Phase 2 local application, CLI-harness, and evidence-readiness work only.  
Baseline: `9ddc1f978dc5f8307867d74218f775bb6ad0dabb`

## Expected Versus Actual

| Area | Expected | Actual | Evidence |
| --- | --- | --- | --- |
| Integrated application gate | The newly authorized Phase 2 local application contract and CLI harness pass the full suite and application validation. | The first full run failed because the CLI test still expected authorized Phase 2 to be rejected (PC-006). After the targeted harness correction, the current full suite passed: 14 tests and 96.59% coverage. | `ISSUES.md` PC-006; `evidence/phase-2/pytest.txt`; `evidence/phase-2/cli-harness.txt` |
| Evidence currency | Retained pytest and coverage artifacts support the repaired gate. | The first retained full-suite report predated the PC-006 repair and still recorded failure; it could not support a passing claim (PC-007). Fresh full-suite and coverage artifacts were then retained and independently reviewed. | `ISSUES.md` PC-007; `docs/reviews/change-review.md`; `evidence/phase-2/pytest.txt`; `evidence/phase-2/coverage.xml` |
| Independent validation | Local quality checks, negative-path behavior, and application validation are independently inspectable. | QA recorded successful local Ruff, mypy, pytest, and application validation; it also inspected readiness and invalid-request assertions. The pytest run reported 32 FastAPI deprecation warnings but no failures. | `evidence/phase-2/qa.txt` |
| Delivery outcome | A local evidence-readiness verdict is available without extending delivery authority. | The change record is clear for local Phase 2 evidence readiness only. No image, hosted CI, Jenkins, registry, deployment, production, rollback, or cloud action was performed or verified. | `docs/change-records/phase-2-local.md` |

No release, deployment, promotion, or recovery occurred in this cycle. Consequently, lead time, deployment result, and recovery-time metrics are not available and are not inferred.

## Rework and Failure Analysis

### PC-006 — stale authorization-boundary expectation

- **Symptom:** the full pytest suite and `project validate app` failed because `tests/test_project_cli.py` asserted that Phase 2 was unauthorized after authorization had been recorded through Phase 2.
- **Root cause:** the authorization change and its CLI regression test were not kept as one consistency contract; the test encoded the prior plan state.
- **Why this caused rework:** the application gate could not be trusted until the harness tested the current boundary. The repair changed the narrow expectation to accept Phase 2 while preserving rejection of Phase 3 with the human-gate exit code.
- **Earlier gate that should have caught it:** before the first integrated gate, a plan-state-to-CLI-boundary check should have been required whenever `authorized_through_phase` changes. The narrow CLI test should precede and be recorded alongside the full suite.
- **Retained failure evidence:** PC-006 remains recorded in `ISSUES.md`; the issue points to the affected test, plan, and retained pytest evidence. It was resolved on 2026-07-11 after the corrected narrow and integrated checks.

### PC-007 — stale full-suite and coverage evidence after repair

- **Symptom:** the retained Phase 2 pytest report was from before the PC-006 repair and recorded a failing full suite, despite the repaired working tree later passing.
- **Root cause:** evidence freshness was not explicitly bound to the code and harness state validated after remediation. A passing-gate claim was considered before the raw full-suite and coverage artifacts had been regenerated.
- **Why this caused rework:** the previously retained report could not establish the repaired gate outcome, so fresh pytest and coverage artifacts and a repeated independent change review were necessary.
- **Earlier gate that should have caught it:** the evidence-capture gate should require a post-remediation full-suite run, coverage artifact, timestamp/command record, and reviewer confirmation that those artifacts supersede any earlier failed report before a passing claim is made.
- **Retained failure evidence:** PC-007 remains recorded in `ISSUES.md`, including the original evidence locations and prescribed remediation. The refreshed reports show 14 passed and 96.59% coverage; the independent review explicitly identifies them as superseding the previous failing report.

## Observed Guardrails

- The corrected CLI test now verifies both sides of the authorization boundary: Phase 2 succeeds and Phase 3 remains rejected. This limits the repair to recorded authority.
- Raw Ruff, mypy, CLI-harness, pytest, coverage, and QA outputs are retained under `evidence/phase-2/`; the review found no request payloads or apparent sensitive values in those reports.
- Local evidence readiness is not release approval. The change record explicitly preserves all external delivery boundaries as unverified.

## Follow-up Actions

| Action | Owner | Acceptance criterion | Target phase |
| --- | --- | --- | --- |
| Define an authorization-state regression contract for every plan authorization transition. | Future CLI-harness worker | A test derives or explicitly asserts the current authorized phase and the immediately next rejected phase, including the documented human-gate exit code; the narrow test is retained before the integrated suite. | Phase 3 planning / next authorization change |
| Add an evidence-freshness checklist to the gate workflow. | Future evidence-process owner | For any remediation, raw full-suite output and coverage are regenerated after the fix; the record identifies the command, result, and artifact paths, and review explicitly confirms that they postdate and supersede failed evidence. | Phase 6 evidence work |
| Track and resolve the FastAPI deprecation warnings without weakening coverage or behavior assertions. | Future application-maintenance worker | The Phase 2-equivalent local suite reports no FastAPI coroutine deprecation warnings, or a documented upstream compatibility constraint and approved follow-up issue is retained; readiness, validation, lifecycle, and logging tests continue to pass at at least 90% coverage. | Phase 3 planning |
| Carry the local-versus-external claim boundary into later delivery records. | Future change-record owner | Each later-phase change record lists executed checks and explicitly separates unexecuted container, hosted CI, registry, deployment, approval, production, rollback, and cloud boundaries until evidence exists. | Phases 3–8 |

## Evidence Index

- `ISSUES.md` — resolved PC-006 and PC-007 entries, including original summaries, evidence paths, attempts, and remediation.
- `docs/reviews/change-review.md` — independent confirmation of the repaired authorization test and refreshed reports.
- `evidence/phase-2/cli-harness.txt` — narrow CLI regression result: 7 passed.
- `evidence/phase-2/pytest.txt` and `evidence/phase-2/coverage.xml` — refreshed full-suite result: 14 passed, 96.59% coverage.
- `evidence/phase-2/qa.txt` — independent local QA commands, results, warnings, and negative-path inspection.
- `docs/change-records/phase-2-local.md` — local-only readiness verdict and explicit unverified boundaries.
