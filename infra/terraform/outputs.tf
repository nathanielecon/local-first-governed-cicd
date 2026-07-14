output "aws_region" {
  value = var.aws_region
}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "ecr_repository_url" {
  value = aws_ecr_repository.delivery_api.repository_url
}

output "ecr_repository_arn" {
  value = aws_ecr_repository.delivery_api.arn
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.staging.name
}

output "service_base_url" {
  value = var.create_service ? "http://${aws_lb.staging[0].dns_name}" : null
}

output "container_image" {
  value = var.create_service ? var.container_image : null
}

output "git_sha" {
  value = var.git_sha
}

output "github_actions_role_arn" {
  value = try(aws_iam_role.github_actions_ecr_push[0].arn, null)
}
