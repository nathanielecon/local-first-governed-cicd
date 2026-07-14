# Optional AWS Validation

Status: **authorized and in progress** (owner explicit authorization 2026-07-14).

## Scope

Minimal Terraform in `infra/terraform/` for:

- Amazon ECR repository (immutable tags, scan on push)
- ECS/Fargate staging service behind an ALB
- Default VPC public subnets with `assign_public_ip=true` (no NAT gateway)
- Region: **us-east-1** (lowest-cost default for this account)

## Auth modes

- **This validation run:** operator AWS CLI session (account credentials present on the workstation).
- **Follow-on:** optional GitHub Actions OIDC role via `enable_github_oidc=true` (not required for first efficacy proof).

## Procedure

```powershell
python scripts/phase9_aws_validate.py
```

That script:

1. `terraform apply` bootstrap (ECR + cluster + IAM + log group)
2. Builds the repo Dockerfile and pushes an immutable tag
3. Records the ECR image digest
4. `terraform apply` with `create_service=true` and `container_image=<repo>@sha256:...`
5. Runs `scripts/smoke_test.py` against the ALB with `--expected-sha` and `--expected-environment staging`
6. Writes evidence under `evidence/phase-9/`

## Teardown

```powershell
cd infra/terraform
terraform destroy -auto-approve `
  -var "git_sha=<full-sha>" `
  -var "create_service=true" `
  -var "container_image=<ecr-url>@sha256:..."
```

## Claims

Live AWS success claims require retained `evidence/phase-9/` artifacts (digest, smoke PASS, manifest). Until those exist, AWS remains unverified in `STATUS.md`.
