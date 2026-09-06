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

aws_error_code() {
  local error_file="$1"
  local code
  code="$(sed -n 's/.*An error occurred (\([^)]*\)).*/\1/p' "$error_file" | head -n 1)"
  printf '%s' "${code:-AwsCliError}"
}

AWS_ERROR_CODE=""
invoke_aws() {
  local error_file
  error_file="$(mktemp)"
  if "$@" >/dev/null 2>"$error_file"; then
    rm -f "$error_file"
    AWS_ERROR_CODE=""
    return 0
  else
    local status=$?
    AWS_ERROR_CODE="$(aws_error_code "$error_file")"
    rm -f "$error_file"
    return "$status"
  fi
}

run_step() {
  local operation="$1"
  shift
  if [[ "$APPLY" -eq 0 ]]; then
    printf '[dry-run] %s\n' "$operation"
    return 0
  fi

  if invoke_aws "$@"; then
    printf '%s: complete\n' "$operation"
    return 0
  fi

  printf '%s: failed (%s)\n' "$operation" "$AWS_ERROR_CODE" >&2
  return 1
}

query_aws() {
  local operation="$1"
  shift
  local error_file output
  error_file="$(mktemp)"
  if output="$("$@" 2>"$error_file")"; then
    rm -f "$error_file"
    printf '%s' "$output"
    return 0
  else
    local status=$?
    local code
    code="$(aws_error_code "$error_file")"
    rm -f "$error_file"
    printf '%s: failed (%s)\n' "$operation" "$code" >&2
    return "$status"
  fi
}

query_optional_aws() {
  local operation="$1"
  shift
  local error_file output code
  error_file="$(mktemp)"
  if output="$("$@" 2>"$error_file")"; then
    rm -f "$error_file"
    printf '%s' "$output"
    return 0
  else
    local status=$?
    code="$(aws_error_code "$error_file")"
    rm -f "$error_file"
    case "$code" in
      ClusterNotFoundException|LoadBalancerNotFound|ServiceNotFoundException|TargetGroupNotFound)
        return 0
        ;;
      *)
        printf '%s: failed (%s)\n' "$operation" "$code" >&2
        return "$status"
        ;;
    esac
  fi
}

CALLER_ACCOUNT="$(query_aws 'Verify caller account' aws sts get-caller-identity --query Account --output text)"
CALLER_ARN="$(query_aws 'Verify caller role' aws sts get-caller-identity --query Arn --output text)"
EXPECTED_ROLE_NAME="${AWS_TEARDOWN_ROLE_ARN##*/}"

if [[ "$CALLER_ACCOUNT" != "$EXPECTED_AWS_ACCOUNT_ID" ]]; then
  echo "Refusing to operate in an unexpected AWS account." >&2
  exit 1
fi

if [[ "$APPLY" -eq 1 && ! "$CALLER_ARN" =~ ^arn:aws:sts::[0-9]{12}:assumed-role/${EXPECTED_ROLE_NAME}/ ]]; then
  echo "Apply requires the configured non-root OIDC teardown role." >&2
  exit 1
fi

LB_ARN="$(query_optional_aws 'Discover load balancer' aws elbv2 describe-load-balancers --names "$LOAD_BALANCER_NAME" --region "$AWS_REGION" --query 'LoadBalancers[0].LoadBalancerArn' --output text)"
TARGET_GROUP_ARN="$(query_optional_aws 'Discover target group' aws elbv2 describe-target-groups --names "$TARGET_GROUP_NAME" --region "$AWS_REGION" --query 'TargetGroups[0].TargetGroupArn' --output text)"
SERVICE_STATUS="$(query_optional_aws 'Discover ECS service' aws ecs describe-services --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" --region "$AWS_REGION" --query 'services[0].status' --output text)"
CLUSTER_STATUS="$(query_optional_aws 'Discover ECS cluster' aws ecs describe-clusters --clusters "$ECS_CLUSTER_NAME" --region "$AWS_REGION" --query 'clusters[0].status' --output text)"

case "$SERVICE_STATUS" in
  ACTIVE|DRAINING) service_present=yes ;;
  INACTIVE|None|"") service_present=no ;;
  *)
    echo "Refusing to operate on an ECS service with an unexpected status." >&2
    exit 1
    ;;
esac
[[ -n "$LB_ARN" && "$LB_ARN" != "None" ]] && lb_present=yes || lb_present=no
[[ -n "$TARGET_GROUP_ARN" && "$TARGET_GROUP_ARN" != "None" ]] && target_group_present=yes || target_group_present=no
printf 'Plan: service=%s load_balancer=%s target_group=%s\n' "$service_present" "$lb_present" "$target_group_present"

case "$SERVICE_STATUS" in
  ACTIVE)
    run_step 'Drain ECS service' aws ecs update-service --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" --desired-count 0 --region "$AWS_REGION"
    run_step 'Wait for ECS service to drain' aws ecs wait services-stable --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" --region "$AWS_REGION"
    run_step 'Delete ECS service' aws ecs delete-service --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" --force --region "$AWS_REGION"
    run_step 'Wait for ECS service deletion' aws ecs wait services-inactive --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" --region "$AWS_REGION"
    ;;
  DRAINING)
    run_step 'Wait for ECS service deletion' aws ecs wait services-inactive --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" --region "$AWS_REGION"
    ;;
esac

if [[ "$lb_present" == yes ]]; then
  run_step 'Delete load balancer' aws elbv2 delete-load-balancer --load-balancer-arn "$LB_ARN" --region "$AWS_REGION"
  run_step 'Wait for load balancer deletion' aws elbv2 wait load-balancers-deleted --load-balancer-arns "$LB_ARN" --region "$AWS_REGION"
fi

if [[ "$target_group_present" == yes ]]; then
  if [[ "$APPLY" -eq 0 ]]; then
    run_step 'Delete target group with bounded retry' aws elbv2 delete-target-group --target-group-arn "$TARGET_GROUP_ARN" --region "$AWS_REGION"
  else
    target_group_deleted=no
    for attempt in $(seq 1 12); do
      if invoke_aws aws elbv2 delete-target-group --target-group-arn "$TARGET_GROUP_ARN" --region "$AWS_REGION"; then
        echo 'Delete target group: complete'
        target_group_deleted=yes
        break
      fi
      if [[ "$AWS_ERROR_CODE" != "ResourceInUse" ]]; then
        printf 'Delete target group: failed (%s)\n' "$AWS_ERROR_CODE" >&2
        exit 1
      fi
      if [[ "$attempt" -lt 12 ]]; then
        printf 'Delete target group: retrying after dependency release (%d/12)\n' "$attempt"
        sleep 10
      fi
    done
    if [[ "$target_group_deleted" != yes ]]; then
      echo 'Delete target group: failed (ResourceInUse after 12 attempts)' >&2
      exit 1
    fi
  fi
fi

if [[ -n "$CLUSTER_STATUS" && "$CLUSTER_STATUS" != "None" && "$CLUSTER_STATUS" != "INACTIVE" ]]; then
  run_step 'Delete ECS cluster' aws ecs delete-cluster --cluster "$ECS_CLUSTER_NAME" --region "$AWS_REGION"
fi

if ! run_step 'Delete designated security group' aws ec2 delete-security-group --group-id "$ALB_SECURITY_GROUP_ID" --region "$AWS_REGION"; then
  echo 'The designated security group was absent or still in use; it is non-billable and requires verification.' >&2
fi

echo "Teardown commands completed; verify the named resources are absent."
