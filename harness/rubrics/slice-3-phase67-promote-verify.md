# Frozen Rubric — Slice 3: Phase 6–7 promote / verify / rollback / failure-injection

**Status:** FROZEN  
**Frozen at:** 2026-07-13T21:35:00Z  
**Branch:** `phase-5-remediation`  
**Sources:** setter A (`7b979054`) + setter B (`c36bb66e`); orchestrator condensation  
**Scope:** deploy/rollback/verify scripts, `scripts/phase7_run_lanes.py`, related tests, `evidence/phase-6/**`, `evidence/phase-7/**`, phase-6/7 reviews  
**Claim boundary:** local-only / production-like / non-E2E / non-AWS

**Scoring rule:** All must-haves must PASS. Judges score /10 against this frozen rubric only. Advance is orchestrator-only.

## Must-have

| ID | Check | Pass |
|---|---|---|
| S3-M01 | `python -m ruff check scripts/verify_deployment.py scripts/phase7_run_lanes.py tests/test_verify_deployment.py tests/test_phase7_failure_injection.py` | 0 errors |
| S3-M02 | `python -m pytest -q -o addopts= tests/test_verify_deployment.py tests/test_phase7_failure_injection.py` | all pass |
| S3-M03 | `python scripts/evidence.py validate --release-id example` and `--release-id phase-6` | both valid |
| S3-M04 | Deploy/rollback invoke verify; fail-closed on verify failure | script review + tests |
| S3-M05 | Rollback requires verified target XOR explicit first-release decision | evidence + script gates |
| S3-M06 | Recovery verify checks digest/health/version/business behavior | verify_deployment recovery mode |
| S3-M07 | Phase 7 lanes fake-credential only; no live cloud mutate | phase7_run_lanes + tests |
| S3-M08 | Residuals (operator-attested VERIFIED_ROLLBACK_*, hardcoded verify maps, Docker-socket/root) disclosed not cleared | security reviews |
| S3-M09 | Phase-6/7 integrated-gate evidence exists and matches claim boundary | evidence files |
| S3-M10 | No secret leakage in phase-6/7 evidence artifacts | validate / scan |

## Needed for 9/10+

| ID | Check | Pass |
|---|---|---|
| S3-9-01 | Eng/change/security review docs CLEAR under stated residuals | docs/reviews |
| S3-9-02 | PC-002/PC-003 resolution honesty matches STATUS | ISSUES/STATUS |
| S3-9-03 | Five Phase 7 lanes indexed with retained scene evidence | evidence/phase-7 |
| S3-9-04 | Deploy.ps1/sh and rollback.ps1/sh parity on verify hooks | script diff review |

## Needed for 10/10

| ID | Check | Pass |
|---|---|---|
| S3-10-01 | Manifest/events field-level zero contradiction vs change-record | spot check |
| S3-10-02 | Hardcoded verify-map advisory explicitly owned for future hardening | review text |

## Nice-to-have

| ID | Check | Pass |
|---|---|---|
| S3-N01 | Replace hardcoded Jenkins verify maps with piped JSON | deferred |
| S3-N02 | Live Jenkins E2E | out of claim |

Do not edit unless security/integrity/acceptance credibility requires it.
