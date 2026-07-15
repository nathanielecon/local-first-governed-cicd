# Frozen Rubric — Slice 6: Smoke tooling + harness PowerShell accuracy

**Status:** FROZEN  
**Frozen at:** 2026-07-13T23:45:00Z  
**Branch:** `phase-5-remediation`  
**Scope:** `scripts/smoke_test.py`, `tests/test_smoke_tool.py`, `scripts/Harness.Common.psm1`, `scripts/Start-Harness.ps1`, `scripts/Invoke-CodexAdapter.ps1`, `scripts/bootstrap.ps1`, `scripts/project.ps1`, `tests/Run-ContractTests.ps1`  
**Out of scope:** `src/delivery_api` deep review (Slice 5), Jenkins/compose (Slice 2), skills content (Slice 7)

**Scoring rule:** All must-haves must PASS. Judges score /10 against this frozen rubric only. Advance is orchestrator-only.

---

## Must-have

| ID | Check | Pass criteria |
|---|---|---|
| S6-M01 | `python -m ruff check scripts/smoke_test.py tests/test_smoke_tool.py` | 0 errors |
| S6-M02 | `python -m pytest -q -o addopts= tests/test_smoke_tool.py` | all pass |
| S6-M03 | Smoke validates live + ready + version + quotes contracts | code + tests |
| S6-M04 | Smoke fails closed on version/sha/environment mismatch | `test_main_reports_release_identity_and_expected_sha_failures` + env mismatch test |
| S6-M05 | Smoke reports HTTP/connection/disconnect failures without traceback spam | dedicated tests pass |
| S6-M06 | PowerShell files parse: Start-Harness, Invoke-CodexAdapter, Harness.Common, bootstrap, project, Run-ContractTests | `[Parser]::ParseFile` zero errors |
| S6-M07 | `project.ps1` / harness entrypoints do not embed live cloud credentials | static review |
| S6-M08 | Adapter/harness scripts respect stop/sentinel or non-interactive safety conventions where present | review against AGENTS thin-orchestrator intent |

## Needed for 9/10+

| ID | Check | Pass criteria |
|---|---|---|
| S6-9-01 | `smoke_test.validate_version_contract` requires non-empty version/git_sha/environment | unit path |
| S6-9-02 | `--base-url` required; timeout bounded (≤5s per request in get_json) | argparse + get_json |
| S6-9-03 | Harness.Common exports reusable helpers used by Start-Harness / adapter | import/dot-source review |
| S6-9-04 | bootstrap.ps1 does not mutate git config or force-push | static review |
| S6-9-05 | Run-ContractTests.ps1 invokes pytest/ruff (or documented contract suite) without skipping failures | review |

## Needed for 10/10

| ID | Check | Pass criteria |
|---|---|---|
| S6-10-01 | Smoke exit codes distinguish pass vs contract fail clearly (non-zero on failure) | tests + main |
| S6-10-02 | No secret-like string literals in Slice 6 scope | grep |
| S6-10-03 | Scripts stay within local/GitHub claim boundary (no silent AWS mutate) | review |

## Nice-to-have

| ID | Check | Pass criteria |
|---|---|---|
| S6-N01 | Documented one-liner to run smoke against local compose API | docs cross-link optional |
