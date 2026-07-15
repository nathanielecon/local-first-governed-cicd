# Frozen Rubric — Slice 9a: SRE harden via GitOps

**Status:** FROZEN  
**Frozen at:** 2026-07-14T22:05:00Z  
**Scope:** AWS/GitOps hardening for Project C staging path — Terraform under `infra/terraform/**`, evidence under `evidence/phase-9/**`, OIDC/least-privilege docs, draw.io architecture if present  
**Out of scope:** Live apply without human gate; Cloud Agent as apply plane; inventing account IDs from other projects

**Scoring rule:** All must-haves must PASS. Judges score /10 against this frozen rubric only. Advance is orchestrator-only.

## Must-have

| ID | Check | Pass |
|---|---|---|
| S9a-M01 | Phase 9 staging evidence retained with digest + smoke PASS + claim boundary | `evidence/phase-9/` |
| S9a-M02 | Terraform path is digest/promotion oriented; no rebuild-between-env pattern | `infra/terraform/**` review |
| S9a-M03 | Docs state Cloud Agents edit repo only; apply is GitOps/CI/human-gated | AGENTS / orch notes / runbook |
| S9a-M04 | Secrets not baked into `.cursor/environment.json` or Dockerfiles | static review |
| S9a-M05 | Residuals (root/login, missing OIDC, TLS hostname, non-root operator) disclosed in STATUS/unverified or docs | honesty |
| S9a-M06 | Architecture diagram (draw.io or equivalent) matches evidenced services/region | docs/screenshots or infra docs |
| S9a-M07 | `python scripts/project_cli.py validate state` passes | CLI |

## Needed for 9/10+

| ID | Check | Pass |
|---|---|---|
| S9a-9-01 | Documented path to GitHub OIDC short-lived AWS creds (even if not enabled) | docs |
| S9a-9-02 | Tear-down / cost-stop guidance present for ALB/Fargate | docs/STATUS |
| S9a-9-03 | Governing manifest cites immutable digest served on ECS/Fargate behind ALB | evidence |

## Needed for 10/10

| ID | Check | Pass |
|---|---|---|
| S9a-10-01 | Least-privilege operator principal path written without claiming it is already live | docs |
| S9a-10-02 | No Project A harness sequential/approval widen sneaks into Project C apply story | review |

Do not edit unless security/integrity/acceptance credibility requires it.
