# Frozen Rubric — Slice 4: Final delivery (docs / evidence / CI-PR / hygiene)

**Status:** FROZEN  
**Frozen at:** 2026-07-13T21:35:00Z  
**Branch:** `phase-5-remediation`  
**Sources:** setter A (`d69c8632`) + setter B (`25870a75`); orchestrator condensation  
**Micropartitions:** 4a docs · 4b phase-8 evidence · 4c CI/PR · 4d tree hygiene

**Scoring rule:** All must-haves PASS; average judge ≥ 9.5/10 to advance.

## Must-have

| ID | Check | Pass |
|---|---|---|
| S4-M01 | Claim boundary honest (no live AWS/cloud completion claims) | portfolio trio + runbook |
| S4-M02 | Mandatory trio present: blocked-change demo, named approval, recovery | walkthrough + evidence |
| S4-M03 | Portfolio plan/walkthrough/demo-script/metrics/runbook/phase-8 index exist and consistent | file checks |
| S4-M04 | `evidence/phase-8/integrated-gate.txt` PASS + metrics-trace overall PASS | evidence |
| S4-M05 | `python scripts/project_cli.py validate state` passes | CLI |
| S4-M06 | Full local CI-parity suite green: `ruff format --check .` · `ruff check .` · `mypy src` · `pytest` · `validate_jenkinsfile.py` | all exit 0 |
| S4-M07 | Open PR on current head; `gh pr checks <N>` all green | remote |
| S4-M08 | Architecture trust-boundary docs accurate and linked (`PROJECT.md`, runbook, portfolio) | review |
| S4-M09 | `BREAK_FIX_LOG.md` + all four frozen rubrics + `harness/SLICES.md` | present |
| S4-M10 | Delivery tree clean of unrelated noise in commit set (exclude `.playwright-mcp/`, HVAC docs, root tooling PNGs unless justified) | git status of staged/committed set |
| S4-M11 | No leftover `.harness/runtime/stop.flag` / stale smoke locks / orphan worker approvals | filesystem |
| S4-M12 | cursor-goal verify command configured to remote check and passes | `cursor-goal --json` |

## Needed for 9/10+

| ID | Check | Pass |
|---|---|---|
| S4-9-01 | Screenshots README policy compliant | docs/screenshots |
| S4-9-02 | Residuals disclosed in portfolio/demo closing | docs |
| S4-9-03 | Phase change-records inventory linked | docs/change-records |
| S4-9-04 | PR description cites claim boundary + test plan | gh pr view |

## Needed for 10/10

| ID | Check | Pass |
|---|---|---|
| S4-10-01 | Working tree fully clean after delivery commit | `git status -sb` |
| S4-10-02 | All slice judge averages ≥ 9.5 recorded in BREAK_FIX_LOG | log |
| S4-10-03 | No open blocking ISSUES for phases 2–8 | ISSUES.md |

## Nice-to-have

| ID | Check | Pass |
|---|---|---|
| S4-N01 | Delete or quarantine HVAC / playwright noise from workspace | optional |
| S4-N02 | Automate micropartition scoreboard | optional |

Do not edit unless security/integrity/acceptance credibility requires it.
