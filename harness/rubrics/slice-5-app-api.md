# Frozen Rubric — Slice 5: Application API accuracy

**Status:** FROZEN  
**Frozen at:** 2026-07-13T23:45:00Z  
**Branch:** `phase-5-remediation`  
**Scope:** `src/delivery_api/**`, `tests/test_api.py`  
**Out of scope:** Jenkins/compose, deploy/rollback, portfolio docs, harness PowerShell, `.codex/skills`

**Scoring rule:** All must-haves PASS. Average judge score ≥ 9.5/10 to advance. Judges score only against this frozen artifact and must run the listed commands.

---

## Must-have (any fail = slice fail)

| ID | Check | Pass criteria |
|---|---|---|
| S5-M01 | `python -m ruff check src/delivery_api tests/test_api.py` | 0 errors |
| S5-M02 | `python -m ruff format --check src/delivery_api tests/test_api.py` | exit 0 |
| S5-M03 | `python -m mypy src` | exit 0 |
| S5-M04 | `python -m pytest -q -o addopts= tests/test_api.py` | all pass |
| S5-M05 | Health: `/health/live` 200 + echoes `x-request-id` | covered by `test_liveness_and_request_id` |
| S5-M06 | Readiness fail-closed: `ready=False` → 503 JSON | covered by `test_readiness_success_and_failure` |
| S5-M07 | `/version` exposes name/version/git_sha/environment | covered by `test_version_is_release_traceable` |
| S5-M08 | `/quotes` correct math + validation 422 on bad units | covered by `test_quote_calculation_and_validation` |
| S5-M09 | Structured request logs include request_id/method/path/status | covered by `test_request_completed_log_contains_structured_context` |
| S5-M10 | Settings use `APP_` env prefix; no secrets in defaults | `config.py` review + no credential fields |

## Needed for 9/10+

| ID | Check | Pass criteria |
|---|---|---|
| S5-9-01 | Lifecycle start/stop logs present | `test_lifecycle_logs_service_start_and_stop` |
| S5-9-02 | JsonFormatter includes context fields | `test_json_formatter_includes_context` |
| S5-9-03 | Quote bounds enforce Field constraints (units/price/discount) | model + 422 path |
| S5-9-04 | App does not claim live AWS / production identity by default | defaults are local/development |
| S5-9-05 | No hardcoded credentials, tokens, or private keys in `src/delivery_api` | grep review |

## Needed for 10/10

| ID | Check | Pass criteria |
|---|---|---|
| S5-10-01 | Endpoint set matches portfolio/demo smoke expectations (live/ready/version/quotes) | cross-check smoke_test contract |
| S5-10-02 | Exception path logs `request_failed` without leaking secrets | middleware review |
| S5-10-03 | Tests use TestClient factory with Settings overrides only | no global mutation |

## Nice-to-have

| ID | Check | Pass criteria |
|---|---|---|
| S5-N01 | OpenAPI schema generated without error | optional `/openapi.json` smoke |
