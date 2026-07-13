# Frozen Rubric — Slice 2: Phase 5 Jenkins auth / compose / fixture

**Status:** FROZEN  
**Frozen at:** 2026-07-13T21:35:00Z  
**Branch:** `phase-5-remediation`  
**Sources:** setter A (`d13944a6`) + setter B (`09761206`); orchestrator condensation  
**Scope:** `Jenkinsfile`, `scripts/validate_jenkinsfile.py`, `infra/jenkins/**`, `compose.yaml`, P5 unauthorized fixture scripts/tests, governing proof `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt`  
**Out of scope:** portfolio, Phase 6/7 promote/verify (except cross-ref markers), PR open

**Scoring rule:** All must-haves PASS; average judge ≥ 9.5/10 to advance.

## Must-have

| ID | Check | Pass |
|---|---|---|
| S2-M01 | `python -m ruff check tests/test_jenkinsfile_contract.py tests/test_jenkins_casc_static.py tests/test_compose_static.py tests/test_p5_t04_unauthorized_fixture.py scripts/p5_t04_unauthorized_fixture.py scripts/validate_jenkinsfile.py` | 0 errors |
| S2-M02 | `python -m pytest -q -o addopts= tests/test_jenkinsfile_contract.py tests/test_jenkins_casc_static.py tests/test_compose_static.py tests/test_p5_t04_unauthorized_fixture.py` | all pass |
| S2-M03 | `python scripts/validate_jenkinsfile.py Jenkinsfile` | valid |
| S2-M04 | Compose requires external `JENKINS_LOCAL_*` identities (no hardcoded admin) | static tests + compose config behavior |
| S2-M05 | JCasC named roles, least privilege, sequence-shaped globalNodeProperties | casc static tests pass |
| S2-M06 | Dockerfile/plugins pinned; role-strategy present | tests pass |
| S2-M07 | Jenkinsfile: named submitter + immutable `TRUSTED_GIT_SHA` + digest-bound RepoDigest selection + evidence.py append path | contract tests pass |
| S2-M08 | Unauthorized fixture evaluates 400/403 denial, pause at approval, ABORTED, no production continuation | unit tests pass |
| S2-M09 | Governing proof file exists with unauthorized_status=400, X-Error local-approver denial, FIXTURE_AWAITING_APPROVAL, no FIXTURE_PRODUCTION_CONTINUED, final ABORTED | text markers present |
| S2-M10 | Residuals Docker-socket/root remain disclosed, not claimed cleared | docs/reviews honesty |

## Needed for 9/10+

| ID | Check | Pass |
|---|---|---|
| S2-9-01 | Full-repo `ruff check .` and `ruff format --check .` clean (CI parity) | exit 0 |
| S2-9-02 | PC-010..PC-014 remain resolved | ISSUES.md |
| S2-9-03 | Attempt-scoped evidence prefix + runtime identity capture | tests |
| S2-9-04 | Approver role scoped to delivery job only | casc test |
| S2-9-05 | Integrated-gate / qa pointers match governing proof | evidence/phase-5 |

## Needed for 10/10

| ID | Check | Pass |
|---|---|---|
| S2-10-01 | Governing proof X-Jenkins matches Dockerfile base | version match |
| S2-10-02 | Header+body dual denial evidence | both present |
| S2-10-03 | No parameter-probe / legacy admin leftovers | greps clean |

## Nice-to-have

| ID | Check | Pass |
|---|---|---|
| S2-N01 | Deduplicate historical attempt-scoped evidence noise | optional |
| S2-N02 | Mechanical marker checker script | optional |

Do not edit unless security/integrity/acceptance credibility requires it.
