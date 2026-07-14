data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

resource "aws_ecr_repository" "delivery_api" {
  name                 = "${var.project_name}-delivery-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "delivery_api" {
  repository = aws_ecr_repository.delivery_api.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_cloudwatch_log_group" "delivery_api" {
  name              = "/ecs/${var.project_name}-delivery-api"
  retention_in_days = 7
}

resource "aws_ecs_cluster" "staging" {
  name = "${var.project_name}-staging"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_security_group" "alb" {
  count       = var.create_service ? 1 : 0
  name        = "${var.project_name}-alb"
  description = "Phase 9 staging ALB"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "service" {
  count       = var.create_service ? 1 : 0
  name        = "${var.project_name}-service"
  description = "Phase 9 Fargate tasks"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "App from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "staging" {
  count              = var.create_service ? 1 : 0
  name               = "${var.project_name}-stg"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "delivery_api" {
  count       = var.create_service ? 1 : 0
  name        = "${var.project_name}-api"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health/ready"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 15
    matcher             = "200"
  }
}

resource "aws_lb_listener" "http" {
  count             = var.create_service ? 1 : 0
  load_balancer_arn = aws_lb.staging[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.delivery_api[0].arn
  }
}

resource "aws_ecs_task_definition" "delivery_api" {
  count                    = var.create_service ? 1 : 0
  family                   = "${var.project_name}-delivery-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "delivery-api"
      image     = var.container_image
      essential = true
      portMappings = [{
        containerPort = 8080
        hostPort      = 8080
        protocol      = "tcp"
      }]
      environment = [
        { name = "APP_ENVIRONMENT", value = "staging" },
        { name = "APP_VERSION", value = var.app_version },
        { name = "APP_GIT_SHA", value = var.git_sha },
        { name = "APP_READY", value = "true" },
        { name = "APP_LOG_LEVEL", value = "INFO" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.delivery_api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "delivery-api"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "delivery_api" {
  count           = var.create_service ? 1 : 0
  name            = "${var.project_name}-delivery-api"
  cluster         = aws_ecs_cluster.staging.id
  task_definition = aws_ecs_task_definition.delivery_api[0].arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.service[0].id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.delivery_api[0].arn
    container_name   = "delivery-api"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.http]

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# GitHub OIDC is optional: enable after confirming no conflicting account provider.
# This validation apply uses the operator AWS session; wire CI to the role when enabled.
variable "enable_github_oidc" {
  type    = bool
  default = false
}

data "tls_certificate" "github" {
  count = var.enable_github_oidc ? 1 : 0
  url   = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github" {
  count           = var.enable_github_oidc ? 1 : 0
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github[0].certificates[0].sha1_fingerprint]
}

resource "aws_iam_role" "github_actions_ecr_push" {
  count = var.enable_github_oidc ? 1 : 0
  name  = "${var.project_name}-github-actions-ecr"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github[0].arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:nathanielecon/project-c-cloud:*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_actions_ecr_push" {
  count = var.enable_github_oidc ? 1 : 0
  name  = "${var.project_name}-github-actions-ecr"
  role  = aws_iam_role.github_actions_ecr_push[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:DescribeRepositories",
          "ecr:DescribeImages"
        ]
        Resource = aws_ecr_repository.delivery_api.arn
      }
    ]
  })
}
