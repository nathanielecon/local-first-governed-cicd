# Delivery Slice Registry

| Slice | Name | Rubric path | Status |
|---|---|---|---|
| 1 | core-harness | harness/rubrics/slice-1-core-harness.md | passed (avg 9.57) |
| 2 | phase5-jenkins-auth | harness/rubrics/slice-2-phase5-jenkins-auth.md | passed (avg 9.90) |
| 3 | phase67-promote-verify | harness/rubrics/slice-3-phase67-promote-verify.md | passed (avg 10.00) |
| 4 | final-delivery | harness/rubrics/slice-4-final-delivery.md | passed (avg 9.50) |
| 5 | app-api | harness/rubrics/slice-5-app-api.md | passed (avg 10.00) |
| 6 | smoke-harness | harness/rubrics/slice-6-smoke-harness.md | passed (avg 10.00) |
| 7 | skills-ci-meta | harness/rubrics/slice-7-skills-ci-meta.md | passed (avg 10.00) |

## Accuracy partition (2026-07-13)

Previously unjudged remainder, now primary-scored:
- Slice 5: `src/delivery_api/**`, `tests/test_api.py`
- Slice 6: `scripts/smoke_test.py`, harness PowerShell entrypoints, `tests/Run-ContractTests.ps1`
- Slice 7: `.codex/skills/**`, Dockerfile/workflow static contracts, `Makefile`/`pyproject.toml`/`AGENTS.md`/`PROJECT.md`/`DECISIONS.md`

Still excluded (noise / non-delivery): `.playwright-mcp/`, HVAC docs, root tooling PNGs, attempt-scoped evidence dumps.
