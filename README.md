# Project C — Governed CI/CD Delivery

A local-first delivery platform that separates credential-free GitHub pull-request validation from controlled Jenkins promotion of one immutable image digest—with staging verification, named human approval, append-only evidence, and rollback that restores the previous verified image.

**Claim boundary:** production-like local delivery is the primary proof. Optional AWS staging in `us-east-1` is evidenced and scoped; this repository does not claim sustained production cloud operation. Naming: public title vs slug `project-c-cloud` is recorded in [`docs/public-naming.md`](docs/public-naming.md).

## Quick start

Prerequisites: Docker Desktop with Linux containers, PowerShell 7 (Windows), Git, and Python 3.12+.

```powershell
./scripts/project.ps1 bootstrap --skip-docker
./scripts/project.ps1 status
./scripts/project.ps1 issues
./scripts/project.ps1 validate phase-1
```

On Linux/WSL use `./project` with the same subcommands. After bootstrap, open the local service at `http://localhost:8081`, production-like lane at `http://localhost:8082`, and Jenkins at `http://localhost:8080`. Before starting Jenkins, inject local-only placeholder administrator, approver, and read-only observer identities through `JENKINS_LOCAL_ADMIN_ID`, `JENKINS_LOCAL_ADMIN_PASSWORD`, `JENKINS_LOCAL_APPROVER_ID`, `JENKINS_LOCAL_APPROVER_PASSWORD`, `JENKINS_LOCAL_VIEWER_ID`, and `JENKINS_LOCAL_VIEWER_PASSWORD` from your shell or an untracked env file—the repository does not ship shared default Jenkins credentials.

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

- Pull-request workflows receive no registry or deployment credentials.
- Jenkins builds once and promotes an immutable digest—never a rebuilt tag between environments.
- Staging must pass before production approval is available.
- Production promotion requires a human decision.
- Failed deployment verification restores the previous recorded image.
- Local validation is never described as live-cloud production.

## Read next

| Path | Why |
| --- | --- |
| [Portfolio walkthrough](docs/portfolio-walkthrough.md) | Recruiter-facing story with evidence-bound claims |
| [Runbook](docs/runbook.md) | Local operate / recover steps |
| [Evidence index](evidence/README.md) | Where release evidence lives |
| [Phase 8 portfolio index](docs/change-records/phase-8-portfolio-index.md) | Mandatory trio and change-record map |
| [Orchestration contract](docs/orchestration.md) | How gated work is authorized |
| [Optional AWS staging](docs/aws-validation.md) | Phase 9 staging facts + residuals |

## Scope notes

- **Local platform:** Phases 2–8 retain production-like CI/CD, approval, evidence, and failure-injection proof under local / GitHub-hosted claim boundaries. Start with the portfolio walkthrough.
- **AWS staging (optional):** Owner-authorized ephemeral staging smoke in `us-east-1` (ECR digest on ECS/Fargate behind ALB) is retained under [`evidence/phase-9/governing-manifest.json`](evidence/phase-9/governing-manifest.json) and summarized in [`docs/aws-validation.md`](docs/aws-validation.md). That is staging validation evidence—not sustained production SRE.
- **Disclosed residuals (not cleared by the portfolio story):** local Jenkins Docker-socket / root controller privilege; operator-attested rollback parameters and hardcoded verify maps; Phase 9 apply used a login session (not least-privilege OIDC), and the ALB was HTTP-only for the short-lived proof. Details stay in the linked AWS note and phase security reviews.
