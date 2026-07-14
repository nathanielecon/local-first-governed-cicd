# Optional AWS Validation

Status: **live staging validated** (owner-authorized 2026-07-14; evidence retained).

## Result

| Field | Value |
|---|---|
| Region | `us-east-1` |
| Image | `…/project-c-delivery-api@sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229` |
| Git SHA | `376b7e18c5cc94e67ff180ca2f42b8eb05535be3` |
| Service URL | `http://project-c-stg-117678206.us-east-1.elb.amazonaws.com` |
| Smoke | PASS (live/ready/version/quotes + expected SHA/env) |
| Governing evidence | `evidence/phase-9/governing-manifest.json` |

## Scope

Minimal Terraform in `infra/terraform/`:

- ECR (immutable tags, scan on push)
- ECS/Fargate 256 CPU / 512 MB behind ALB
- Default VPC public subnets with `assign_public_ip=true` (**no NAT gateway**)
- Region **us-east-1**

## Auth modes

- **This validation run:** operator `aws login` session exported for Terraform (`aws configure export-credentials`).
- **Follow-on:** `enable_github_oidc=true` creates a GitHub Actions OIDC role for short-lived ECR push.

## Procedure

```powershell
python scripts/phase9_aws_validate.py
```

## Cost posture

Ephemeral staging: Fargate task + ALB + ECR storage + 7-day logs. No NAT. Tear down when finished to stop ALB hourly charges.

## Teardown

```powershell
cd infra/terraform
terraform destroy -auto-approve `
  -var "git_sha=376b7e18c5cc94e67ff180ca2f42b8eb05535be3" `
  -var "create_service=true" `
  -var "container_image=000000000000.dkr.ecr.us-east-1.amazonaws.com/project-c-delivery-api@sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229"
```

## Residuals (disclosed)

- Root/login session credentials used for apply (not least-privilege IAM role)
- OIDC not used for this efficacy run
- HTTP-only ALB (no ACM/TLS) for short-lived proof
