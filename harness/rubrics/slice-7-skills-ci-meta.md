# Frozen Rubric — Slice 7: Skills + CI static contracts + meta accuracy

**Status:** FROZEN  
**Frozen at:** 2026-07-13T23:45:00Z  
**Branch:** `phase-5-remediation`  
**Scope:** `.codex/skills/**`, `tests/test_dockerfile_static.py`, `tests/test_github_workflow_static.py`, `.github/workflows/pr-validation.yml`, `Dockerfile`, `Makefile`, `pyproject.toml`, `AGENTS.md`, `PROJECT.md`, `DECISIONS.md`  
**Out of scope:** App API (Slice 5), smoke/harness PS (Slice 6), Phase 5–7 delivery already judged (Slices 1–4)

**Scoring rule:** All must-haves must PASS. Judges score /10 against this frozen rubric only. Advance is orchestrator-only.

---

## Must-have

| ID | Check | Pass criteria |
|---|---|---|
| S7-M01 | `python scripts/project_cli.py validate skills --json` | exit 0; skills checks empty/pass |
| S7-M02 | Nine skill folders present with `SKILL.md` frontmatter `name` + `description` | implement-slice, plan-eng-review, project-discovery, qa, retro, review, security-review, ship, spec |
| S7-M03 | `python -m pytest -q -o addopts= tests/test_dockerfile_static.py tests/test_github_workflow_static.py` | all pass |
| S7-M04 | `python -m ruff check tests/test_dockerfile_static.py tests/test_github_workflow_static.py` | 0 errors |
| S7-M05 | Dockerfile: pinned multi-stage images, non-root runtime, readiness healthcheck, OCI/release labels | static tests |
| S7-M06 | GitHub workflow: actions pinned to full SHAs; jobs declare read-only permissions; no deploy credentials | static tests |
| S7-M07 | Workflow Jenkinsfile job uses `scripts/validate_jenkinsfile.py` | static test |
| S7-M08 | `PROJECT.md` claim boundary: no sustained prod / live AWS proven without optional phase | text present |
| S7-M09 | `AGENTS.md` phase-auth + thin-orchestrator prohibitions still consistent with `PROJECT.md` | review |

## Needed for 9/10+

| ID | Check | Pass criteria |
|---|---|---|
| S7-9-01 | Each skill description states when to use (gate ordering / trigger) | frontmatter review |
| S7-9-02 | `pyproject.toml` defines package/src layout compatible with `mypy src` + pytest | file review |
| S7-9-03 | Makefile targets (if any) do not claim live cloud deploy | review |
| S7-9-04 | `DECISIONS.md` indexes decisions without contradicting claim boundary | spot check |
| S7-9-05 | `.github/pull_request_template.md` / issue template exist and do not request secrets in plaintext | presence + skim |

## Needed for 10/10

| ID | Check | Pass criteria |
|---|---|---|
| S7-10-01 | Skill names match CLI `validate skills` expected set exactly | CLI + folder parity |
| S7-10-02 | No skills instruct bypassing security/ship gates or deleting failing tests | content skim |
| S7-10-03 | Dockerfile + workflow contracts remain credential-free for PR jobs | tests + skim |

## Nice-to-have

| ID | Check | Pass criteria |
|---|---|---|
| S7-N01 | openai.yaml agent stubs present beside each skill | optional |
