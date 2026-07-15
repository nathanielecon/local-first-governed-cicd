# Project C — Governed CI/CD Delivery

Ship a change the boring, safe way: check it without deploy keys, build one sealed image, prove it in staging, get a named human yes, keep the receipts, and undo if it breaks.

![How a change gets safely shipped](docs/screenshots/project-c-delivery-infographic.png)

<p align="center"><em>Read top row left to right. Cloud strip is optional demo only.</em></p>

## What the picture means

1. **Open a PR** — Your change shows up for review.
2. **Robots check it** — Tests and scans run. Those jobs do not get registry or deploy keys.
3. **Build one sealed image** — Jenkins builds once. That image keeps the same fingerprint (digest) everywhere. No rebuild between environments.
4. **Try it in staging** — Prove it works before anyone can promote further.
5. **A person approves** — A named human says yes. Not a silent auto-promote.
6. **Keep receipts or undo** — Save evidence of what shipped. If verify fails, go back to the last good image.

The thin cloud strip (ECR → ECS/Fargate → ALB) is an optional, time-boxed AWS staging smoke with retained evidence. It is not “we run production in AWS.” Details: [`docs/aws-validation.md`](docs/aws-validation.md), [`evidence/phase-9/governing-manifest.json`](evidence/phase-9/governing-manifest.json).

## Quick start

Needs Docker Desktop (Linux containers), PowerShell 7 on Windows, Git, and Python 3.12+.

```powershell
./scripts/project.ps1 bootstrap --skip-docker
./scripts/project.ps1 status
./scripts/project.ps1 issues
./scripts/project.ps1 validate phase-1
```

On Linux/WSL use `./project` with the same subcommands. After bootstrap: app `http://localhost:8081`, production-like lane `http://localhost:8082`, Jenkins `http://localhost:8080`.

Set local-only Jenkins placeholder identities before starting Jenkins (`JENKINS_LOCAL_ADMIN_ID`, `JENKINS_LOCAL_ADMIN_PASSWORD`, `JENKINS_LOCAL_APPROVER_ID`, `JENKINS_LOCAL_APPROVER_PASSWORD`, `JENKINS_LOCAL_VIEWER_ID`, `JENKINS_LOCAL_VIEWER_PASSWORD`) from your shell or an untracked env file. This repo does not ship shared default Jenkins passwords.

```text
project bootstrap [--skip-docker]
project status [--phase N] [--task ID]
project issues [--status STATE] [--severity LEVEL]
project phase N [--task ID] [--dry-run]
project validate <scope>
project resume <task-id>
project evidence <release-id>
```

## Delivery contract

- PR workflows get no registry or deployment credentials.
- Build once; promote by immutable digest. Do not rebuild between environments.
- Staging must pass before production approval is available.
- Production promotion needs a human decision.
- Failed verify restores the previous recorded image.
- Local proof is not the same thing as live cloud production.

## Read next

| Path | Why |
| --- | --- |
| [Portfolio walkthrough](docs/portfolio-walkthrough.md) | Recruiter story with evidence-bound claims |
| [Runbook](docs/runbook.md) | Operate and recover locally |
| [Evidence index](evidence/README.md) | Where release evidence lives |
| [Phase 8 portfolio index](docs/change-records/phase-8-portfolio-index.md) | Portfolio trio and change-record map |
| [Orchestration contract](docs/orchestration.md) | How gated work is authorized |
| [Optional AWS staging](docs/aws-validation.md) | Phase 9 facts and leftovers |
| [Public naming](docs/public-naming.md) | Display title vs `project-c-cloud` slug |

## Honest scope

Primary proof is local / production-like delivery (phases 2–8) plus GitHub-hosted PR checks. Optional AWS staging in `us-east-1` is evidence-scoped smoke, not sustained production ops.

Still disclosed (not papered over): local Jenkins Docker-socket / root controller privilege; operator-attested rollback parameters; Phase 9 used a login session (not least-privilege OIDC); ALB was HTTP-only for that short proof. See the AWS note and phase security reviews.
