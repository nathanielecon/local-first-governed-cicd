# Protected Project C teardown

This manual-only workflow removes the cost-bearing staging service, load balancer, target group, cluster, and designated load-balancer security group. It deliberately preserves the container registry, logs, network, encryption keys, object storage, and repository evidence.

Live AWS identifiers are not committed. Configure one secret named `PROJECT_C_TEARDOWN_CONFIG` on the protected GitHub environment named `teardown`. Its value must be a compact JSON object with these keys:

```json
{
  "role_arn": "<dedicated-non-root-role-arn>",
  "account_id": "<expected-account-id>",
  "repository_id": "<immutable-github-repository-id>",
  "cluster_name": "<ecs-cluster-name>",
  "service_name": "<ecs-service-name>",
  "load_balancer_name": "<application-load-balancer-name>",
  "target_group_name": "<target-group-name>",
  "security_group_id": "<load-balancer-security-group-id>"
}
```

The environment must require an authorized reviewer. The workflow uses short-lived GitHub OIDC credentials, masks each parsed value before AWS access, checks the immutable repository ID and AWS account, verifies that the session is using the configured non-root role, requires the exact confirmation `DESTROY-PROJECT-C-STAGING`, and targets only the protected values.

The IAM template is parameterized for auditability and portability. Do not place live parameter values in the repository or workflow logs.

## Retirement result

The protected teardown completed on September 6, 2026. The service and load balancer were already absent; the remaining target group and ECS cluster were deleted. The designated security group could not be deleted because an AWS dependency still references it. Security groups do not incur standalone charges, so this does not leave Project C compute or load-balancer spend running.

The workflow intentionally has no delete permissions for ECR, CloudWatch Logs, VPCs/subnets, KMS, or S3. Their preservation is enforced by the narrow role and script boundary. See [`evidence/project-c-teardown/2026-09-06.md`](../evidence/project-c-teardown/2026-09-06.md) for the redacted execution record and verification limits.
