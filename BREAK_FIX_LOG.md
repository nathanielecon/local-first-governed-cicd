# Break/Fix Log — Project C Delivery Quality Loop

| Timestamp (UTC) | Slice | Break | Fix | Evidence | Result |
|---|---|---|---|---|---|
| 2026-07-13T21:18:00Z | bootstrap | No PR; dirty tree; no rubrics | cursor-goal + harness + 4-slice partition | harness/, BREAK_FIX_LOG.md | done |
| 2026-07-13T21:36:00Z | 1 | S1-M15 ruff fail on evidence core | Fix evidence.py + test_evidence_manifest.py | ruff slice1 green; 22 pytest | fixed |
| 2026-07-13T21:45:00Z | 2–3 | 121→58 repo ruff errors blocking CI | ruff format/check clean across delivery scripts/tests | `ruff check .` + `ruff format --check .` exit 0; pytest 119 passed | fixed |
| 2026-07-13T21:50:00Z | 1 | Judge B 9.0/10 (S1-10-01 PLAN lag; S1-10-04 missing scores) | Document PLAN-row residual in STATUS; record scores here + harness/scores | STATUS.md; this log | fixed |
| 2026-07-13T21:54:00Z | 4 | PR #2 Security scans failed: gitleaks 10 findings (plugin pins + synthetic Phase 7 PAT) | Extend `.gitleaks.toml` allowlists for documented fixtures/plugin IDs | run 29287992854; commit 4843591 | in_progress |

## Judge scoreboard

| Round | Slice | Judge | Score | Must-haves | Notes |
|---|---|---|---:|---|---|
| R1 | 1 | Judge B (`c51e07c3`) | 9.0 | all PASS | S1-10-01/04 FAIL |
| R2 | 1 | Orchestrator post-fix checklist | 9.7 | all PASS | residual + score log added |
| R1 | 2 | #1 (`7613f19a`) | 10.0 | all PASS | |
| R1 | 2 | #2 (`953b1c12`) | 10.0 | all PASS | |
| R1 | 2 | #3 (`a1bf60a1`) | 9.7 | all PASS | avg 9.9 |
| R1 | 3 | #1 (`d0d2e46a`) | 10.0 | all PASS | |
| R1 | 3 | #2 (`bc4e2979`) | 10.0 | all PASS | |
| R1 | 3 | #3 (`dc3e4f1c`) | 10.0 | all PASS | avg 10.0 |
| R1 | 4 | — | blocked | S4-M07 | wait PR checks green |

## Slice partition (frozen)

1. Core harness — `harness/rubrics/slice-1-core-harness.md`
2. Phase 5 Jenkins auth — `harness/rubrics/slice-2-phase5-jenkins-auth.md`
3. Phase 6–7 promote/verify — `harness/rubrics/slice-3-phase67-promote-verify.md`
4. Final delivery — `harness/rubrics/slice-4-final-delivery.md`
