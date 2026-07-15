# Delivery Metrics

**Preamble:** local-only / production-like / non-AWS. Values below are phase-local extracts from retained evidence. Schema is ready for cross-release trends; these rows are **not** multi-release operational history and must not be read as production traffic or live-cloud SLOs.

Do not fabricate durations, users, or baselines beyond the cited sources.

---

## Metric extracts

| Metric | Value (evidence-backed) | Source | Disallowed upgrade |
| --- | --- | --- | --- |
| PR validation — hosted pass | Run `29166389732` passed all four jobs on `main` @ `e82f4a2` | `evidence/phase-4/integrated-gate.txt`; `docs/change-records/phase-4-github-validation.md` | Invented wall-clock duration |
| PR validation — intentional fail | Run `29166442925` failed Python quality only (Ruff F401); PR `#1` | Same as above | Claiming production incident detection |
| Local pytest / coverage (Phase 2 gate) | 14 passed; 96.59% total coverage | `evidence/phase-2/integrated-gate.txt`; `docs/change-records/phase-2-local.md` | Rounding up coverage |
| Local pytest (Phase 4 QA) | 38 passed; 96.59% total coverage | `evidence/phase-4/integrated-gate.txt` | Treating as hosted runtime |
| Failed-change detection — PR lane | Blocked at Python quality (Phase 4 demo) | Run `29166442925` | Claiming org branch-protection enforcement beyond retained runs |
| Failed-change detection — approval | Unauthorized submit → HTTP 400 / ABORTED; no production continuation | `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt` | Claiming live org production denial |
| Failed-change detection — promotion gates | Rollback-target / first-release fail-closed; staging-as-prior rejected | `evidence/phase-6/` promotion-gate proofs; phase-6 retrospective | Claiming live E2E promotion failure times |
| High/critical findings opened → resolved | `PC-001`–`PC-014` resolved in `ISSUES.md` (as applicable); residuals remain advisory | `ISSUES.md`; phase integrated gates | Claiming zero residual risk |
| Evidence completeness | Integrated-gate present for phases 2–7; Phase 8 assembly indexed pending `P8-T03` | `evidence/phase-*/integrated-gate.txt`; `docs/change-records/phase-8-portfolio-index.md` | Marking Phase 8 complete before gate |
| Manual / fixture steps | Phase 5 P5-T04 diagnostic loop; Phase 6 `pipeline.run_id: manual` | `docs/retrospectives/phase-5.md`; `evidence/phase-6/manifest.json` | Hiding fixture nature |
| Named human approval (fixture) | `local-approver` @ `2026-07-13T17:15:00Z` | `evidence/phase-6/events.jsonl`; `manifest.json`; `docs/change-records/phase-6-local.md` | Organizational production approval |
| Recovery verification | All four checks pass (`deployed_digest`, `health`, `version`, `business_behavior`); status `recovery_verified` | `evidence/phase-6/manifest.json` recovery block; event `p6-local-recovery` | Live E2E recovery time without timed runtime evidence |
| Failure-injection lanes | 12/12 scenarios ok | `evidence/phase-7/P7-T01-lane-index.txt`; `evidence/phase-7/integrated-gate.txt` | Clearing residual advisories |
| Lead time (phase-local only) | Phase 5 eng-review (2026-07-12) → integrated (2026-07-13); Phase 6 same-day calendar span on 2026-07-13 | Phase 5/6 retrospectives; integrated-gate timestamps | Fabricated baseline trends across releases |

---

## Per-release recording checklist (schema)

For future releases, record when evidence exists:

1. PR validation outcome and run IDs (pass / intentional fail)
2. Merge-to-staging / merge-to-production lead time (only with dated retained timestamps)
3. Deployment result and digest identity
4. Failed-change detection stage
5. High/critical findings opened and resolved
6. Flaky tests (if observed in retained reports)
7. Evidence completeness vs declared set
8. Manual / fixture steps disclosed
9. Recovery verification result and evidence path

Trend language allowed only as: *schema ready; initial points are phase-local evidence extracts.*
