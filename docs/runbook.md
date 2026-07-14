# Delivery Runbook

Authority: promotion, evidence, rollback, and recovery steps in this runbook obey `docs/phase-6-spec.md`. Tags and Compose references are aliases only; the immutable image digest is the promotion and rollback source of truth. Claim boundary remains local-only / production-like unless separately authorized evidence exists.

## First five minutes

1. Record time, release ID, commit, environment, reported symptom, and last known-good **digest** (not tag alone).
2. Do not rebuild, retag, delete containers, rotate credentials, or prune Docker yet.
3. Check `docker compose ps`, `docker ps --format '{{.Names}} {{.Image}} {{.Status}}'`, and `docker compose logs --tail 100 <service>`.
4. Probe `/health/live`, `/health/ready`, and `/version`; compare the returned identity and the actual deployed digest to the release event log / derived summary manifest.
5. Inspect append-only release events and the derived summary. If user impact persists and a **verified** previous digest exists, roll back to that digest and complete recovery verification.

## Jenkins failure

- Before starting or retrying Jenkins, confirm that `JENKINS_LOCAL_ADMIN_ID`, `JENKINS_LOCAL_ADMIN_PASSWORD`, `JENKINS_LOCAL_APPROVER_ID`, `JENKINS_LOCAL_APPROVER_PASSWORD`, `JENKINS_LOCAL_VIEWER_ID`, and `JENKINS_LOCAL_VIEWER_PASSWORD` are injected from the local shell or an untracked environment file. These are local-only placeholder identities; never commit or share their values.
- Check controller health and logs: `docker compose ps jenkins` and `docker compose logs --tail 200 jenkins`.
- Confirm checkout commit and archived reports before retrying.
- For Docker failures, inspect `/var/run/docker.sock`, controller user/group access, host Docker health, and disk space.
- For credential failures, verify the credential ID and scope; never print its value.
- Resume from a clean Jenkins run. Do not manually skip failed stages.
- Do not treat a green stage as sufficient proof: require event-backed digest identity, persisted approver identity/timestamp, and recovery verification when those claims are made.

## Application or connectivity failure

- `docker inspect <container>` confirms image digest, user, health, environment, and network.
- `docker exec <container> getent hosts <dependency>` distinguishes DNS from application failure when the image provides the command.
- Compare listening ports, Compose networks, and service names before changing security boundaries.
- Liveness success plus readiness failure indicates the process runs but cannot safely receive traffic.

## Promotion gates (before production deploy)

1. Confirm staging verification events exist for the **same** digest to be promoted.
2. Confirm a named production approval event will persist approver identity and timestamp into append-only evidence.
3. Confirm exactly one of:
   - a verified rollback target is bound, or
   - an explicit first-release decision is recorded.
4. If neither target nor first-release decision exists, **stop**. Do not promote.
5. Deploy scripts fail closed on that gate. Production examples:

```powershell
# First production-like release (no prior verified digest)
./scripts/deploy.ps1 -Environment production `
  -Image 'localhost:5000/delivery-api@sha256:<candidate>' `
  -ExpectedSha '<commit>' `
  -FirstReleaseDecision 'first_release_no_rollback_target' `
  -FirstReleaseDecidedBy 'local-approver' `
  -FirstReleaseDecidedAt '2026-07-13T18:00:00Z' `
  -FirstReleaseRationale 'No verified prior production digest exists.' `
  -FirstReleaseAcceptedRisk 'Rollback to a prior verified digest is unavailable.'

# Later release with event-backed prior production digest
./scripts/deploy.ps1 -Environment production `
  -Image 'localhost:5000/delivery-api@sha256:<candidate>' `
  -ExpectedSha '<commit>' `
  -VerifiedRollbackDigest 'sha256:<prior>' `
  -VerifiedRollbackCommit '<prior-commit>' `
  -VerifiedRollbackVerifiedAt '2026-07-12T18:00:00Z' `
  -VerifiedRollbackSourceRelease '<prior-release-id>' `
  -VerifiedRollbackEnvironment production
```

```bash
FIRST_RELEASE_DECISION=first_release_no_rollback_target \
FIRST_RELEASE_DECIDED_BY=local-approver \
FIRST_RELEASE_DECIDED_AT=2026-07-13T18:00:00Z \
FIRST_RELEASE_RATIONALE='No verified prior production digest exists.' \
FIRST_RELEASE_ACCEPTED_RISK='Rollback to a prior verified digest is unavailable.' \
./scripts/deploy.sh production 'localhost:5000/delivery-api@sha256:<candidate>' '<commit>'
```

Hard refusals:

- Empty, unknown, self-referential, or staging-only digests as production rollback targets.
- Using `deploy/state/production.previous.env` as proof of a verified target.
- Selecting an arbitrary first `RepoDigest` without matching expected registry/repository identity.

## Rollback

Rollback must restore an **event-backed verified digest** and then re-run the full verification suite. Restoring an env file alone is not recovery.

```powershell
./scripts/rollback.ps1 -Environment production `
  -VerifiedRollbackDigest 'sha256:<verified-prior>' `
  -ExpectedRegistry 'localhost:5000' `
  -ExpectedRepository 'delivery-api' `
  -ExpectedSha '<prior-commit>'
```

```bash
./scripts/rollback.sh production 'sha256:<verified-prior>' 'localhost:5000' 'delivery-api' '<prior-commit>'
```

### Mandatory recovery verification

`scripts/verify_deployment.py verify --mode recovery` (invoked by the rollback scripts) must pass all of:

1. Actual deployed digest matches the verified rollback target **and** the expected registry/repository identity.
2. Health probes succeed (`/health/live`, `/health/ready`).
3. Version identity agrees with the restored release expectations.
4. Business endpoint / smoke contract succeeds.
5. Append recovery results to the release event log; regenerate or refresh the derived summary from events (evidence append path is owned by Phase 6 evidence/Jenkins slices).
6. Record start/end times in the change record and preserve failed-release evidence.

If any recovery check fails or is skipped, treat it as a critical incident: keep evidence, do not rebuild to manufacture a match, and escalate. Rollback scripts return a failing status in that case.

## Evidence discipline

- Release events are append-only; do not overwrite history to manufacture a pass.
- The summary manifest is derived from events; it is not an independent place to silently drop staging, approval, or production facts.
- Change records must cite the same commit, digest, approver/time, and rollback target or first-release decision as the evidence artifacts.
- Never place secrets in events, manifests, change records, or retained logs.

## Phase 9 AWS / GitOps (staging)

Authority for the staging path: `docs/architecture/phase-9-aws.md`, `docs/aws-validation.md`, and `evidence/phase-9/governing-manifest.json`. Local Phase 6 digest promotion rules above still apply; AWS staging consumes the **same** immutable digest — no rebuild between environments.

### Control plane

- Cursor Cloud Agents and coding agents **edit the repo only**. They are not the AWS apply plane.
- Live `terraform apply` / `destroy`, ECR push with live creds, and ECS/ALB mutation require human authorization (and preferably CI / GitOps with short-lived credentials).
- Do not bake secrets into `.cursor/environment.json`, Dockerfiles, or committed tfvars.

### Digest on ECS/Fargate

Governing staging claim (ephemeral proof, not sustained production): ECR digest `sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229` served on ECS/Fargate behind ALB in `us-east-1` with smoke PASS — see `evidence/phase-9/`.

Terraform under `infra/terraform/` takes `container_image` as a digest-preferring reference, keeps ECR tags immutable, and gates ALB/service creation behind `create_service` after a digest exists.

### GitHub OIDC (documented path; not claimed live for the efficacy run)

1. Confirm no conflicting account OIDC provider for GitHub Actions.
2. Human-gated apply with `-var enable_github_oidc=true`.
3. Use output role ARN `github_actions_role_arn` from Actions via `AssumeRoleWithWebIdentity` for short-lived ECR push.
4. Keep `enable_github_oidc=false` until that follow-on is intentionally authorized.

Phase 9 evidence used `auth_mode: operator-aws-session`, not OIDC.

### Least-privilege operator (path only)

Replace root/login session applies with a dedicated staging operator role (scoped ECR/ECS/ELB/Logs/IAM-pass). Do **not** claim this principal is already live; it remains an honesty residual until evidenced.

### Tear-down / cost-stop

Stop ALB hourly and Fargate charges when the proof window ends:

```powershell
cd infra/terraform
terraform destroy -auto-approve `
  -var "git_sha=376b7e18c5cc94e67ff180ca2f42b8eb05535be3" `
  -var "create_service=true" `
  -var "container_image=000000000000.dkr.ecr.us-east-1.amazonaws.com/project-c-delivery-api@sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229"
```

Commands match `evidence/phase-9/governing-manifest.json` → `teardown`. Architecture diagram: `docs/project-c-phase9-staging-architecture.drawio`.

### Phase 9 residuals (disclosed)

- Root/login AWS session used for apply (not least-privilege operator).
- GitHub OIDC not enabled for the retained smoke.
- HTTP-only ALB (no TLS hostname).
- Do not clear these residuals in narrative without new evidence.
