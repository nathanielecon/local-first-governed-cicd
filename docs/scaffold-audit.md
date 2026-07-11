# Phase 1 Scaffold Audit

Audit date: 2026-07-11. All project assets were untracked at audit time. `retain` means suitable as a candidate, not verified. Phase 2 must be re-gated; Phases 3–6 are definitions only.

## Retain candidates

| Assets | Reason |
|---|---|
| `.codex/skills/*/agents/openai.yaml` | Valid skill interface metadata. |
| `.dockerignore`, `.gitignore`, `deploy/state/.gitkeep` | Appropriate repository hygiene. |
| `PROJECT.md`, `pyproject.toml` | Clear scope and viable Phase 2 candidate configuration. |
| `.github/pull_request_template.md` | Useful outcome, risk, validation, and rollback fields. |
| `Dockerfile`, `infra/jenkins/plugins.txt` | Viable candidates; build/runtime compatibility remains unverified. |
| `src/delivery_api/__init__.py`, `config.py`, `logging.py`, `main.py` | Phase 2 implementation candidates requiring re-verification. |
| `tests/test_api.py`, `scripts/smoke_test.py` | Test candidates requiring the new evidence gate. |
| `docs/aws-validation.md`, `docs/change-records/TEMPLATE.md`, `docs/failure-injection.md`, `docs/metrics.md`, `docs/retrospectives/TEMPLATE.md` | Appropriate planned/deferred evidence documents. |
| `docs/decisions/0001-delivery-boundaries.md`, `0002-promote-digests.md` | Sound delivery invariants. |
| `docs/reviews/change-review.md`, `docs/reviews/security-review.md` | Correctly remain pending. |
| `evidence/README.md` | Appropriate evidence and sensitive-data boundary. |

## Revise before affected phase

| Assets | Required revision |
|---|---|
| `.codex/skills/*/SKILL.md` | Align state authority, model tiers, Mandarin handoff, write scopes, and escalation. |
| `AGENTS.md`, `PLAN.md`, `STATUS.md`, `README.md`, `Makefile` | Replace premature state and fragmented command behavior with the Phase 1 contract and unified CLI. |
| `.github/ISSUE_TEMPLATE/implementation.yml`, `.github/workflows/pr-validation.yml` | Add orchestration fields; pin actions and replace grep-only Jenkins validation. |
| `compose.yaml`, `infra/jenkins/Dockerfile`, `infra/jenkins/casc.yaml`, `Jenkinsfile` | Resolve authorization, default credential, Docker privilege, trusted commit, digest, and evidence findings. |
| `scripts/bootstrap.ps1`, `scripts/project.ps1`, `scripts/deploy.*`, `scripts/rollback.*`, `scripts/evidence.py` | Unify CLI; add atomic state, append-only evidence, verified target, and recovery verification. |
| `docs/decisions/0003-codex-gstack-adaptation.md`, `docs/portfolio-walkthrough.md`, `docs/runbook.md` | Add the Terra Medium orchestrator, Mandarin protocol, issue alerts, and CLI-first proof boundaries. |
| `docs/reviews/eng-review.md` | Replace placeholder with the independent Phase 1 review. |
| `evidence/example/manifest.json` | Represent environment events, approval, checks, issues, and recovery without overwriting history. |

## Remove generated artifacts

| Assets | Reason |
|---|---|
| `.coverage`, `coverage.xml` | Generated test output; ignored and not authoritative evidence. |

## Verification boundary

- Phase 2: source and tests exist and historically passed local checks, but are candidates until re-run through the new gate with recorded evidence.
- Phase 3: Docker/Compose/smoke definitions exist; no accepted image or runtime evidence exists.
- Phase 4: workflow definition exists; no GitHub run, required-check, or blocked-change evidence exists.
- Phase 5: Jenkins/JCasC definitions exist; controller, plugins, checkout, permissions, and pipeline are unverified.
- Phase 6: deployment/evidence/rollback scripts exist; registry push, approval, promotion, and recovery are unverified.

