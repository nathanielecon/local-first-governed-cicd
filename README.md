# Project C: Governed CI/CD Delivery

A local-first, production-like delivery platform that separates fast GitHub pull-request validation from controlled Jenkins deployment. It builds a FastAPI image once, promotes the immutable digest, verifies each environment, records evidence, and restores the previous image when verification fails.

## Quick start on Windows

Prerequisites: Docker Desktop with Linux containers, PowerShell 7, Git, and Python 3.12+.

```powershell
./scripts/project.ps1 bootstrap --skip-docker
./scripts/project.ps1 status
./scripts/project.ps1 issues
./scripts/project.ps1 validate phase-1
```

Open the service at `http://localhost:8081`, production at `http://localhost:8082`, and Jenkins at `http://localhost:8080`. The local Jenkins default is `admin` / `change-me-locally`; override both values before any shared use.

## Commands

```text
project bootstrap [--skip-docker]
project status [--phase N] [--task ID]
project issues [--status STATE] [--severity LEVEL]
project phase N [--task ID] [--dry-run]
project validate <scope>
project resume <task-id>
project evidence <release-id>
```

On Windows use `./scripts/project.ps1`; Linux/WSL may use `./project`. Phase 1 is the only currently authorized implementation phase. Later-phase files are audited candidates, not verified capabilities.

See [the orchestration contract](docs/orchestration.md), [running issues](ISSUES.md), and [the runbook](docs/runbook.md). Runtime and demo commands remain unavailable until their phases are authorized and gated.

## Delivery contract

- PR workflows receive no registry or deployment credentials.
- Jenkins builds once and promotes a digest, never a rebuilt tag.
- Staging must pass before production approval is available.
- Production requires a human decision.
- Failed deployment verification restores the previous recorded image.
- Local validation is never described as live-cloud production.
