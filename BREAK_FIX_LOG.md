# Break/Fix Log — Project C Delivery Quality Loop

| Timestamp (UTC) | Slice | Break | Fix | Evidence | Result |
|---|---|---|---|---|---|
| 2026-07-13T21:18:00Z | bootstrap | No PR; dirty tree; no rubrics | cursor-goal + harness + 4-slice partition | harness/, BREAK_FIX_LOG.md | done |
| 2026-07-13T21:36:00Z | 1 | S1-M15 ruff fail on evidence core | Fix evidence.py + test_evidence_manifest.py | ruff slice1 green; 22 pytest | fixed |
| 2026-07-13T21:45:00Z | 2–3 | 121→58 repo ruff errors blocking CI | ruff format/check clean across delivery scripts/tests | `ruff check .` + `ruff format --check .` exit 0; pytest 119 passed | fixed |
| 2026-07-13T21:50:00Z | 1 | Judge B 9.0/10 (S1-10-01 PLAN lag; S1-10-04 missing scores) | Document PLAN-row residual in STATUS; record scores here + harness/scores | STATUS.md; this log | fixed |

## Judge scoreboard

| Round | Slice | Judge | Score | Must-haves | Notes |
|---|---|---|---:|---|---|
| R1 | 1 | Judge B (`c51e07c3`) | 9.0 | all PASS | S1-10-01/04 FAIL |
| R2 | 1 | (pending re-score after 10/10 fixes) | — | — | — |

## Slice partition (frozen)

1. Core harness — `harness/rubrics/slice-1-core-harness.md`
2. Phase 5 Jenkins auth — `harness/rubrics/slice-2-phase5-jenkins-auth.md`
3. Phase 6–7 promote/verify — `harness/rubrics/slice-3-phase67-promote-verify.md`
4. Final delivery — `harness/rubrics/slice-4-final-delivery.md`
