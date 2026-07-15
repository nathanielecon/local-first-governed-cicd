# Phase 9 AWS staging architecture (SRE / GitOps)

**Claim boundary:** ephemeral owner-authorized staging validation in `us-east-1` only. This document does **not** claim sustained production SRE, organizational multi-account GitOps, TLS-terminated public hostname, GitHub OIDC already live, or a least-privilege operator principal already in use.

**Governing evidence:** `evidence/phase-9/governing-manifest.json`  
**Diagram source:** `docs/project-c-phase9-staging-architecture.drawio`  
**PNG export (README):** `docs/screenshots/phase9-architecture.png`  
**Terraform root:** `infra/terraform/`

---

## Evidenced staging path

| Fact | Value (from governing manifest) |
|---|---|
| Region | `us-east-1` |
| Immutable image | `…/project-c-delivery-api@sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229` |
| Git SHA | `376b7e18c5cc94e67ff180ca2f42b8eb05535be3` |
| Runtime | ECS cluster `project-c-staging`, service `project-c-delivery-api` on Fargate behind ALB |
| Smoke | `PASS` (retained under `evidence/phase-9/`) |
| Auth mode used | `operator-aws-session` (not GitHub OIDC for this run) |

Supporting artifacts include digest capture (`20260714T010224Z-image-digest.txt`), smoke PASS / re-verify texts, and authorization notes under `evidence/phase-9/`.

The diagram matches those evidenced services and region: GitHub → ECR (immutable digest) → ALB (HTTP :80) → ECS/Fargate in the default VPC public subnets, plus CloudWatch logs and IAM task roles. Optional PNG export may be added later; the draw.io file is the canonical architecture asset.

---

## Digest / promotion orientation (no rebuild between environments)

Terraform is **digest-oriented**:

- `container_image` is expected as an immutable reference (`repo@sha256:…`); variable description prefers digest form.
- ECR repository uses `image_tag_mutability = "IMMUTABLE"` and scan-on-push.
- `create_service` defaults to `false` so ALB/ECS service resources are created only after a digest exists.
- Task definition receives `var.container_image` and binds `APP_GIT_SHA` / `APP_VERSION` from trusted inputs — it does **not** rebuild the image inside Terraform.

Promotion contract for Project C remains: **build once, promote the same digest**. Staging and any later environment must consume the identical digest identity. Rebuilding between environments is forbidden.

---

## Apply control plane (Cloud Agents ≠ apply)

| Actor | Allowed | Forbidden |
|---|---|---|
| Cursor Cloud Agents | Edit repo, docs, Terraform *source*, evidence pointers | Live `terraform apply` / destroy, AWS console mutation as the control plane |
| GitOps / CI (human-gated) | Apply after review + explicit authorization | Unattended production promotion |
| Human operator | Authorize cost, credentials, apply, tear-down | Treating agent chat as apply authority |

Cloud Agents and local coding agents **edit the repository only**. Live AWS apply stays on CI or a human-gated workflow with retained authorization evidence. See `harness/ORCH-CLOUD-ENV.md` and `docs/runbook.md` (GitOps / tear-down sections).

This Project C path does **not** import Project A harness sequential-approval widening into the AWS apply story. Apply remains human-gated; approval semantics for production stay with Project C’s Phase 6 event/digest contract, not an external harness widen.

---

## Secrets posture

- `.cursor/environment.json` install script runs **version checks only** (Python/git/gh + optional terraform/aws/docker). No AWS keys, GitHub tokens, or passwords are baked into the Cloud Agent image definition.
- Application `Dockerfile` and `infra/jenkins/Dockerfile` do not embed secrets; runtime uses non-root UID `10001` for the delivery API image.
- Operator credentials for the Phase 9 efficacy run were session-exported outside the repo (`auth_mode: operator-aws-session`). Do not commit `*.auto.tfvars`, credential files, or exported session material.

---

## Documented GitHub OIDC path (not enabled for the efficacy run)

Terraform already encodes an optional path (`enable_github_oidc`, default `false`):

1. Confirm no conflicting GitHub OIDC provider already exists in the account.
2. Apply with `-var enable_github_oidc=true` (human-gated).
3. Role `project-c-github-actions-ecr` trusts `token.actions.githubusercontent.com` for `repo:nathanielecon/project-c-cloud:*` and grants short-lived ECR push/describe permissions only.
4. Wire GitHub Actions to `sts:AssumeRoleWithWebIdentity` using that role ARN (output `github_actions_role_arn`).

**Honesty:** OIDC was **not** used for the retained Phase 9 smoke. Enabling it is a follow-on hardening step, not a present claim.

---

## Least-privilege operator principal (path only — not live)

**Documented target (not claimed live):**

1. Create an IAM role or IAM user dedicated to staging Terraform (e.g. `project-c-staging-operator`) with scoped permissions for ECR, ECS, ELB, IAM role pass for task/execution roles, CloudWatch Logs, and VPC read on the default VPC — no account-wide `AdministratorAccess`.
2. Prefer SSO / assumed-role sessions over long-lived access keys; never store keys in the repo or Cloud Agent image.
3. Re-run staging apply/destroy only under that principal; retire root/login session use for routine applies.

**Honesty residual:** the evidenced Phase 9 apply used an **account root / login session**. Replacement with the least-privilege principal above is unverified / not yet live (`STATUS.md` `unverified`).

---

## Tear-down / cost-stop (ALB / Fargate)

Ephemeral staging incurs ALB hourly charges plus Fargate task and ECR storage. When validation is finished:

```powershell
cd infra/terraform
terraform destroy -auto-approve `
  -var "git_sha=376b7e18c5cc94e67ff180ca2f42b8eb05535be3" `
  -var "create_service=true" `
  -var "container_image=000000000000.dkr.ecr.us-east-1.amazonaws.com/project-c-delivery-api@sha256:bffa93adcbe247be118de0726842f673e14310052b3fdcd6ddaa853fbc05c229"
```

Exact destroy vars are also recorded in `evidence/phase-9/governing-manifest.json` (`teardown` field). Do not leave ALB/Fargate running after the proof window without an explicit cost decision.

---

## Residuals (disclosed — not cleared by this doc)

| Residual | Status |
|---|---|
| Operator AWS root/login session used for apply | Disclosed; replace with least-privilege role (path above) |
| GitHub OIDC short-lived creds not used for this run | Disclosed; Terraform path exists, default off |
| HTTP ALB only (no ACM/TLS hostname) | Disclosed; TLS hostname remains unverified |
| Non-root AWS operator principal for Terraform | Path documented; not claimed live |
| Phases 5–8 local residuals (Docker socket/root, etc.) | Remain disclosed elsewhere; not cleared by Phase 9 |

---

## Related docs

- Procedure / cost notes: `docs/aws-validation.md`
- Operator runbook GitOps / OIDC / tear-down: `docs/runbook.md`
- Cloud Agent apply boundary: `harness/ORCH-CLOUD-ENV.md`
- Screenshot / diagram index: `docs/screenshots/README.md`
