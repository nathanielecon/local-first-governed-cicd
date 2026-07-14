# Delivery Slice Registry

| Slice | Name | Rubric path | Status |
|---|---|---|---|
| 1 | core-harness | harness/rubrics/slice-1-core-harness.md | blind advance (avg 10.00 R2) |
| 2 | phase5-jenkins-auth | harness/rubrics/slice-2-phase5-jenkins-auth.md | blind advance (avg 10.00 R2) |
| 3 | phase67-promote-verify | harness/rubrics/slice-3-phase67-promote-verify.md | blind advance (avg 10.00) |
| 4 | final-delivery | harness/rubrics/slice-4-final-delivery.md | reloop pending (blind; unstick) |
| 5 | app-api | harness/rubrics/slice-5-app-api.md | blind advance (avg 10.00) |
| 6 | smoke-harness | harness/rubrics/slice-6-smoke-harness.md | blind advance (avg 10.00) |
| 7 | skills-ci-meta | harness/rubrics/slice-7-skills-ci-meta.md | blind advance (avg 10.00) |
| 9a | sre-gitops | harness/rubrics/slice-9a-sre-gitops.md | frozen (pending implement+judge) |
| 9b | recruiter-readme | harness/rubrics/slice-9b-recruiter-readme.md | frozen (pending implement+judge) |
| 9c | infographic | harness/rubrics/slice-9c-infographic.md | frozen (pending implement+judge) |
| 9d | portfolio-resume | harness/rubrics/slice-9d-portfolio-resume.md | frozen (pending implement+judge) |

## Accuracy partition (2026-07-13)

Previously unjudged remainder, now primary-scored under blind reloop:
- Slice 5: `src/delivery_api/**`, `tests/test_api.py`
- Slice 6: `scripts/smoke_test.py`, harness PowerShell entrypoints, `tests/Run-ContractTests.ps1`
- Slice 7: `.codex/skills/**`, Dockerfile/workflow static contracts, `Makefile`/`pyproject.toml`/`AGENTS.md`/`PROJECT.md`/`DECISIONS.md`

Still excluded (noise / non-delivery): `.playwright-mcp/`, HVAC docs, root tooling PNGs, attempt-scoped evidence dumps.

## Contamination note

Prior “passed (avg …)” rows are archived in `harness/scores/CONTAMINATED-ARCHIVE.md` and are not pass claims until blind reloops clear the orchestrator gate.
