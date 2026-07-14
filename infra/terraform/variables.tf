variable "aws_region" {
  type        = string
  description = "Lowest-cost default region for this validation."
  default     = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "project-c"
}

variable "container_image" {
  type        = string
  description = "Immutable image reference including digest (@sha256:...) preferred."
  default     = ""
}

variable "git_sha" {
  type        = string
  description = "Trusted git SHA bound into the running task environment."
}

variable "app_version" {
  type    = string
  default = "0.1.0"
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "task_cpu" {
  type    = string
  default = "256"
}

variable "task_memory" {
  type    = string
  default = "512"
}

variable "create_service" {
  type        = bool
  description = "Create ALB+ECS service only after an image digest exists."
  default     = false
}

variable "enable_github_oidc" {
  type        = bool
  description = "Create GitHub Actions OIDC provider/role for short-lived ECR push."
  default     = false
}
