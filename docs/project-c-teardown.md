# Protected Project C teardown

The retired manual-only workflow removed the cost-bearing staging service, load
balancer, target group, cluster, and project security groups. It deliberately
preserved the container registry, logs, network, encryption keys, object
storage, and repository evidence.

Live AWS identifiers were never committed. During execution, one protected
environment secret supplied these fields:

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

The environment required an authorized reviewer. The workflow used short-lived
GitHub OIDC credentials, masked each parsed value before AWS access, checked the
immutable repository ID and AWS account, verified a non-root role, required the
exact confirmation `DESTROY-PROJECT-C-STAGING`, and targeted only the protected
values.

The IAM template is parameterized for auditability and portability. Do not place live parameter values in the repository or workflow logs.

## Retirement result

The protected teardown completed on September 6, 2026. The service and load
balancer were already absent; the remaining target group and ECS cluster were
deleted. A second protected run revalidated the absent billable resources. A
non-root dependency check then identified an unused service security group as
the remaining reference to the designated load-balancer group; both unused
groups were deleted in dependency order and verified absent.

An inventory of all 17 enabled regions found no matching active ECS cluster or
service, load balancer, target group, or Project C security group. The retained
ECR repository, CloudWatch log group, default VPC/subnets, and account KMS/S3
inventories remained accessible. The read-only verifier lacked ECR image-list
permission, so the immutable digest's continued presence is bounded by the
earlier live evidence and the fact that no cleanup identity had ECR deletion
permission.

The dedicated teardown role, temporary user permissions, protected secret,
environment, and workflow were removed after verification. The hardened script,
parameterized IAM template, documentation, evidence, and historical Actions
runs remain for auditability. See
[`evidence/project-c-teardown/2026-09-06.md`](../evidence/project-c-teardown/2026-09-06.md)
for the redacted execution record and verification limits.
