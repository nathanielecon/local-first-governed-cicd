# Protected Project C teardown

This manual-only workflow removes the cost-bearing staging service, load balancer, target group, cluster, and designated load-balancer security group. It deliberately preserves the container registry, logs, network, encryption keys, object storage, and repository evidence.

Live AWS identifiers are not committed. Configure these as secrets on the protected GitHub environment named `teardown`:

- `AWS_TEARDOWN_ROLE_ARN`
- `EXPECTED_AWS_ACCOUNT_ID`
- `EXPECTED_REPOSITORY_ID`
- `ECS_CLUSTER_NAME`
- `ECS_SERVICE_NAME`
- `LOAD_BALANCER_NAME`
- `TARGET_GROUP_NAME`
- `ALB_SECURITY_GROUP_ID`

The environment must require an authorized reviewer. The workflow uses short-lived GitHub OIDC credentials, checks the immutable repository ID and AWS account, verifies that the session is using the configured non-root role, requires the exact confirmation `DESTROY-PROJECT-C-STAGING`, and targets only the protected values.

The IAM template is parameterized for auditability and portability. Do not place live parameter values in the repository or workflow logs.
