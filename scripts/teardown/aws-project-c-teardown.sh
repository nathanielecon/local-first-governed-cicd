#!/usr/bin/env bash
# Project C staging teardown. Dry-run by default; --apply performs deletion.
# Live identifiers are supplied only through a protected GitHub environment.
# Deliberately preserves ECR, CloudWatch logs, VPC/subnets, KMS, S3, and evidence.
set -euo pipefail

required=(
  AWS_REGION AWS_TEARDOWN_ROLE_ARN EXPECTED_AWS_ACCOUNT_ID
  ECS_CLUSTER_NAME ECS_SERVICE_NAME LOAD_BALANCER_NAME
  TARGET_GROUP_NAME ALB_SECURITY_GROUP_ID
)
for name in "${required[@]}"; do
  test -n "${!name:-}" || { echo "Missing required environment value: $name" >&2; exit 1; }
done

APPLY=0
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
fi

run() {
  if [[ "$APPLY" -eq 1 ]]; then
    "$@"
  else
    printf '[dry-run]'
    printf ' %q' "$@"
    printf '\n'
  fi
}

CALLER_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
CALLER_ARN="$(aws sts get-caller-identity --query Arn --output text)"
EXPECTED_ROLE_NAME="${AWS_TEARDOWN_ROLE_ARN##*/}"

if [[ "$CALLER_ACCOUNT" != "$EXPECTED_AWS_ACCOUNT_ID" ]]; then
  echo "Refusing to operate in an unexpected AWS account." >&2
  exit 1
fi

if [[ "$APPLY" -eq 1 && ! "$CALLER_ARN" =~ ^arn:aws:sts::[0-9]{12}:assumed-role/${EXPECTED_ROLE_NAME}/ ]]; then
  echo "Apply requires the configured non-root OIDC teardown role." >&2
  exit 1
fi

LB_ARN="$(aws elbv2 describe-load-balancers --names "$LOAD_BALANCER_NAME" --region "$AWS_REGION" --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || true)"
TARGET_GROUP_ARN="$(aws elbv2 describe-target-groups --names "$TARGET_GROUP_NAME" --region "$AWS_REGION" --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || true)"
SERVICE_STATUS="$(aws ecs describe-services --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" --region "$AWS_REGION" --query 'services[0].status' --output text 2>/dev/null || true)"
CLUSTER_STATUS="$(aws ecs describe-clusters --clusters "$ECS_CLUSTER_NAME" --region "$AWS_REGION" --query 'clusters[0].status' --output text 2>/dev/null || true)"

[[ -n "$SERVICE_STATUS" && "$SERVICE_STATUS" != "None" ]] && service_present=yes || service_present=no
[[ -n "$LB_ARN" && "$LB_ARN" != "None" ]] && lb_present=yes || lb_present=no
[[ -n "$TARGET_GROUP_ARN" && "$TARGET_GROUP_ARN" != "None" ]] && target_group_present=yes || target_group_present=no
printf 'Plan: service=%s load_balancer=%s target_group=%s\n' "$service_present" "$lb_present" "$target_group_present"

if [[ "$service_present" == yes ]]; then
  run aws ecs update-service --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" --desired-count 0 --region "$AWS_REGION"
  if [[ "$APPLY" -eq 1 ]]; then
    aws ecs wait services-stable --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" --region "$AWS_REGION"
  fi
  run aws ecs delete-service --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" --force --region "$AWS_REGION"
  if [[ "$APPLY" -eq 1 ]]; then
    aws ecs wait services-inactive --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" --region "$AWS_REGION"
  fi
fi

if [[ "$lb_present" == yes ]]; then
  run aws elbv2 delete-load-balancer --load-balancer-arn "$LB_ARN" --region "$AWS_REGION"
  if [[ "$APPLY" -eq 1 ]]; then
    aws elbv2 wait load-balancers-deleted --load-balancer-arns "$LB_ARN" --region "$AWS_REGION"
  fi
fi

if [[ "$target_group_present" == yes ]]; then
  run aws elbv2 delete-target-group --target-group-arn "$TARGET_GROUP_ARN" --region "$AWS_REGION"
fi

if [[ -n "$CLUSTER_STATUS" && "$CLUSTER_STATUS" != "None" && "$CLUSTER_STATUS" != "INACTIVE" ]]; then
  run aws ecs delete-cluster --cluster "$ECS_CLUSTER_NAME" --region "$AWS_REGION"
fi

if [[ "$APPLY" -eq 1 ]]; then
  if ! aws ec2 delete-security-group --group-id "$ALB_SECURITY_GROUP_ID" --region "$AWS_REGION"; then
    echo "The designated security group was absent or still in use; it is non-billable and requires verification." >&2
  fi
else
  run aws ec2 delete-security-group --group-id "$ALB_SECURITY_GROUP_ID" --region "$AWS_REGION"
fi

echo "Teardown commands completed; verify the named resources are absent."
