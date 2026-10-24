locals {
  applications = {
    backend = {
      port        = 8000
      secret_keys = ["DATABASE_URL", "VECTOR_DATABASE_URL", "RABBITMQ_URL", "AUTH_SECRET_KEY", "CHAT_HMAC_KEY"]
    }
    processor = {
      port        = 8001
      secret_keys = ["DATABASE_URL", "VECTOR_DATABASE_URL", "RABBITMQ_URL", "AZURE_COST_API_TOKEN", "CHAT_HMAC_KEY"]
    }
    azure-cost-api = {
      port        = 8002
      secret_keys = ["AZURE_COST_VALID_TOKENS", "AZURE_COST_SKIPTOKEN_SECRET"]
    }
  }
  workloads                   = merge(local.applications, { grafana = { port = 3000, secret_keys = ["GF_DATABASE_PASSWORD", "GF_SECURITY_ADMIN_PASSWORD", "GF_SECURITY_SECRET_KEY", "GRAFANA_EVALUATION_DB_PASSWORD"] } })
  application_rolling_percent = 150
  rolling_vcpu                = length(local.applications) * floor(var.desired_count * local.application_rolling_percent / 100) * 0.5 + 1
  active_applications         = var.deploy_applications ? local.applications : {}
  task_trust = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "ecs-tasks.amazonaws.com" } }]
  })
}
resource "aws_ecs_cluster" "main" {
  name = local.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
resource "aws_ecr_repository" "application" {
  for_each             = local.workloads
  name                 = "${local.name}/${each.key}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  image_scanning_configuration {
    scan_on_push = true
  }
  encryption_configuration {
    encryption_type = "AES256"
  }
}
resource "aws_cloudwatch_log_group" "application" {
  for_each          = local.workloads
  name              = "/ecs/${local.name}/${each.key}"
  retention_in_days = 30
}
resource "aws_iam_role" "execution" {
  for_each             = local.workloads
  name                 = "${local.name}-${each.key}-exec"
  permissions_boundary = var.permissions_boundary_arn
  assume_role_policy   = local.task_trust
}
resource "aws_iam_role_policy" "execution" {
  for_each = local.workloads
  role     = aws_iam_role.execution[each.key].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = "ecr:GetAuthorizationToken", Resource = "*" },
      {
        Effect   = "Allow", Action = ["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"]
        Resource = aws_ecr_repository.application[each.key].arn
      },
      {
        Effect   = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.application[each.key].arn}:*"
      },
      { Effect = "Allow", Action = "secretsmanager:GetSecretValue", Resource = aws_secretsmanager_secret.application[each.key].arn },
      {
        Effect    = "Allow", Action = "kms:Decrypt", Resource = aws_kms_key.data.arn
        Condition = { StringEquals = { "kms:ViaService" = "secretsmanager.${var.region}.amazonaws.com" } }
      }
    ]
  })
}
resource "aws_iam_role" "task" {
  for_each             = local.workloads
  name                 = "${local.name}-${each.key}-task"
  permissions_boundary = var.permissions_boundary_arn
  assume_role_policy   = local.task_trust
}
resource "aws_iam_role_policy" "bedrock" {
  for_each = length(var.bedrock_model_arns) > 0 ? toset(["backend", "processor"]) : toset([])
  role     = aws_iam_role.task[each.key].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow", Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
      Resource = var.bedrock_model_arns
    }]
  })
}
resource "aws_iam_role_policy" "documents" {
  for_each = toset(["backend", "processor"])
  role     = aws_iam_role.task[each.key].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      { Effect = "Allow", Action = "s3:ListBucket", Resource = aws_s3_bucket.main["documents"].arn },
      { Effect = "Allow", Action = "s3:GetObject", Resource = each.key == "backend" ? ["${aws_s3_bucket.main["documents"].arn}/staging/*", "${aws_s3_bucket.main["documents"].arn}/confirmed/*"] : ["${aws_s3_bucket.main["documents"].arn}/confirmed/*"] },
      { Effect = "Allow", Action = "s3:DeleteObject", Resource = ["${aws_s3_bucket.main["documents"].arn}/staging/*", "${aws_s3_bucket.main["documents"].arn}/confirmed/*"] },
      {
        Effect    = "Allow", Action = each.key == "backend" ? ["kms:Decrypt", "kms:GenerateDataKey"] : ["kms:Decrypt"], Resource = aws_kms_key.data.arn
        Condition = { StringEquals = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" } }
      }
    ], each.key == "backend" ? [{ Effect = "Allow", Action = "s3:PutObject", Resource = ["${aws_s3_bucket.main["documents"].arn}/staging/*", "${aws_s3_bucket.main["documents"].arn}/confirmed/*"] }] : [])
  })
}
resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "${local.name}.internal"
  vpc  = aws_vpc.main.id
}
resource "aws_service_discovery_service" "fixture" {
  name = "azure-cost-api"
  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.main.id
    routing_policy = "MULTIVALUE"
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}
resource "aws_service_discovery_service" "processor" {
  name = "processor"
  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.main.id
    routing_policy = "MULTIVALUE"
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}
resource "aws_ecs_task_definition" "application" {
  for_each                 = local.active_applications
  family                   = "${local.name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution[each.key].arn
  task_role_arn            = aws_iam_role.task[each.key].arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  volume {
    name = "tmp"
  }
  container_definitions = jsonencode([{
    name                   = each.key
    image                  = lookup(var.container_images, each.key, "MISSING_IMAGE")
    essential              = true
    readonlyRootFilesystem = true
    linuxParameters        = { initProcessEnabled = true }
    mountPoints            = [{ sourceVolume = "tmp", containerPath = "/tmp", readOnly = false }]
    portMappings           = concat([{ containerPort = each.value.port, hostPort = each.value.port, protocol = "tcp" }], each.key == "processor" ? [{ containerPort = 8003, hostPort = 8003, protocol = "tcp" }] : [])
    environment = [for key, value in merge(
      lookup(var.application_environment, each.key, {}),
      {
        AWS_REGION                    = var.region
        RUNTIME_ENVIRONMENT           = "production"
        ALLOW_INSECURE_LOCAL_DATABASE = "false"
        DEMO_SEED_ENABLED             = "false"
      },
      contains(["backend", "processor"], each.key) ? {
        ECONOMICON_AWS_RUNTIME      = "ecs"
        DOCUMENT_S3_AUTH_MODE       = "iam"
        DOCUMENT_S3_REGION          = var.region
        DOCUMENT_S3_BUCKET          = aws_s3_bucket.main["documents"].id
        DOCUMENT_S3_ENDPOINT        = "https://s3.${var.region}.amazonaws.com"
        DOCUMENT_S3_PUBLIC_ENDPOINT = "https://s3.${var.region}.amazonaws.com"
      } : {},
      each.key == "backend" ? {
        AUTH_PROVIDER           = "cognito"
        COGNITO_ISSUER          = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
        COGNITO_CLIENT_ID       = aws_cognito_user_pool_client.frontend.id
        CORS_ALLOWED_ORIGINS    = jsonencode(["https://${var.frontend_domain}"])
        BACKEND_SCHEMA_MODE     = "verify"
        PROCESSOR_CHAT_BASE_URL = "http://processor.${aws_service_discovery_private_dns_namespace.main.name}:8003"
      } : {},
      each.key == "processor" ? {
        AZURE_COST_API_BASE_URL = "http://azure-cost-api.${aws_service_discovery_private_dns_namespace.main.name}:8002"
        PROCESSOR_SCHEMA_MODE   = "verify"
      } : {},
      each.key == "azure-cost-api" ? { AZURE_COST_AUTH_ENABLED = "true" } : {}
    ) : { name = key, value = value }]
    secrets = [for key in each.value.secret_keys : {
      name = key, valueFrom = "${aws_secretsmanager_secret.application[each.key].arn}:${key}::"
    }]
    healthCheck = {
      command  = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:${each.value.port}/health', timeout=5).read()"]
      interval = 30, timeout = 10, retries = 3, startPeriod = 60
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.application[each.key].name
        awslogs-region        = var.region
        awslogs-stream-prefix = each.key
      }
    }
    stopTimeout = 60
  }])
  lifecycle {
    precondition {
      condition     = var.application_adaptations_verified && alltrue([for key in keys(local.applications) : contains(keys(var.container_images), key)])
      error_message = "Adapted applications, populated runtime secrets, completed migrations and three immutable images are prerequisites."
    }
    precondition {
      condition     = startswith(lookup(var.container_images, each.key, ""), "${aws_ecr_repository.application[each.key].repository_url}@sha256:")
      error_message = "Image must belong to the ECR repository for this application; IAM is scoped to that repository."
    }
  }
}
resource "aws_ecs_service" "application" {
  for_each                           = local.active_applications
  name                               = each.key
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.application[each.key].arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = var.desired_count
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = local.application_rolling_percent
  health_check_grace_period_seconds  = each.key == "backend" ? 90 : null
  enable_execute_command             = false
  wait_for_steady_state              = true
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = [for subnet in aws_subnet.app : subnet.id]
    security_groups  = [aws_security_group.component[each.key].id]
    assign_public_ip = false
  }
  dynamic "load_balancer" {
    for_each = each.key == "backend" ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.api.arn
      container_name   = each.key
      container_port   = each.value.port
    }
  }
  dynamic "service_registries" {
    for_each = [1]
    content {
      registry_arn = each.key == "backend" ? aws_service_discovery_service.backend.arn : (each.key == "processor" ? aws_service_discovery_service.processor.arn : aws_service_discovery_service.fixture.arn)
    }
  }
  depends_on = [
    aws_lb_listener.https, aws_route.app_egress, aws_iam_role_policy.execution,
    aws_db_instance.main, aws_mq_broker.main, aws_iam_role_policy.bedrock,
    aws_iam_role_policy.documents, aws_iam_role_policy.bedrock_chat
  ]
}
