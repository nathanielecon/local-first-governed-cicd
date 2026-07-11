# Phase 3 Threat Review

**Verdict: acceptable for engine-independent Phase 3 work only.** This review is
limited to static source and configuration inspection of `Dockerfile`,
`compose.yaml`, `scripts/smoke_test.py`, `Jenkinsfile`, `infra/jenkins/`, and the
approved Phase 3 engineering review. It does not approve Docker runtime,
Compose execution, registry publication, Jenkins startup, deployment,
production, rollback verification, GitHub-hosted validation, or cloud activity.

## Scope and boundaries

- `Dockerfile` keeps the application runtime in a separate stage, exposes version
  and Git SHA through OCI labels and environment variables, and selects UID/GID
  `10001`. Static tests are appropriate to preserve that source-level contract,
  but they do not prove the built image or the running process identity.
- `compose.yaml` clearly separates `registry`, `staging`, `production`, and
  `jenkins` services, with `staging` and `production` limited to the `deploy`
  profile. Promotion identity still comes from an image reference passed through
  environment substitution; no source-only result may be described as a verified
  digest deployment.
- `scripts/smoke_test.py` is a source-level client that can validate response
  contracts and failure reporting, but until `PC-004` is cleared it cannot prove
  container reachability, readiness behavior, or deployed image identity.

## Findings

| Severity | Finding | Required disposition |
|---|---|---|
| Major | `compose.yaml` still defines a Jenkins service that runs as `root`, mounts `/var/run/docker.sock`, and accepts a default fallback administrator password through `${JENKINS_ADMIN_PASSWORD:-change-me-locally}`. | Keep `PC-001` open and do not treat any Phase 3 static work as Jenkins hardening or authorization evidence. |
| Major | `scripts/deploy.ps1` and `scripts/deploy.sh` restore only the previous configured image reference after a smoke failure; they do not verify restored health, version, business behavior, or actual deployed digest. | Keep `PC-003` open and do not claim verified rollback or recovery from any Phase 3 artifact. |
| Major | Runtime-dependent controls remain unproven because no Docker Linux engine evidence exists in the current window. Source inspection alone cannot prove image user, health-check execution, resolved digests, service logs, or network behavior. | Keep `PC-004` open and block all Docker/Compose execution until the user provides real Docker Linux engine availability evidence. |

## Review notes

- No new secret material was introduced in the reviewed static assets. The only
  credential-like value in scope is the intentionally insecure local Jenkins
  fallback, which remains an acknowledged future-phase risk rather than an
  accepted control.
- The Phase 3 worker scopes are correctly split for non-overlapping
  engine-independent work: image definition, Compose topology, smoke helper, and
  this review artifact.
- The approved path after these slices is an independent change review, static
  QA, security review, and an integrated evidence gate that preserves the
  unverified runtime boundary.

No additional issue ID is required from this review because the material risks
are already tracked as `PC-001`, `PC-003`, and `PC-004`.
