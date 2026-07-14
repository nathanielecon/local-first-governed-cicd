# Optional AWS Validation

Status: **evidenced optional strip — live staging smoke validated** (owner-authorized 2026-07-14; evidence retained).

Claim boundary: ephemeral `us-east-1` staging proof only. Aligns with `evidence/phase-9/governing-manifest.json` and `STATUS.md` Phase 9 verified baseline. This is **not** completed production cloud and **not** “AWS deferred / never done.” Portfolio Phase 8 packages remain local-first; cite this strip only with the governing manifest.

## Result

| Field | Value |
|---|---|
| Region | `us-east-1` |
| Image | `…/project-c-delivery-api@sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229` |
| Git SHA | `376b7e18c5cc94e67ff180ca2f42b8eb05535be3` |
| Service URL | `http://project-c-stg-117678206.us-east-1.elb.amazonaws.com` |
| Smoke | PASS (live/ready/version/quotes + expected SHA/env) |
| Auth mode | `operator-aws-session` (OIDC not used for this run) |
| Governing evidence | `evidence/phase-9/governing-manifest.json` |
| Architecture / residuals | `docs/architecture/phase-9-aws.md` |
| Architecture diagram | `docs/project-c-phase9-staging-architecture.drawio` |

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
  -var "container_image=283077380808.dkr.ecr.us-east-1.amazonaws.com/project-c-delivery-api@sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229"
```

## Residuals (disclosed — not cleared)

Point to `STATUS.md` `unverified` and `docs/architecture/phase-9-aws.md` for follow-on honesty:

- GitHub OIDC short-lived credential path not enabled for the retained smoke (`STATUS.md` unverified)
- TLS-terminated public staging hostname not claimed (`STATUS.md` unverified; HTTP ALB only)
- Least-privilege non-root AWS operator principal not live (`STATUS.md` unverified; root/login session used for apply)
- Cost tear-down after the proof window — procedure in Teardown above and `docs/architecture/phase-9-aws.md`; manifest `teardown` field — not a cleared production gate
