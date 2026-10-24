# One private task; metadata on existing RDS, metrics bounded to this rehearsal.
resource "aws_service_discovery_service" "backend" {
  name = "backend"
  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.main.id
    routing_policy = "MULTIVALUE"
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}
resource "aws_lb_target_group" "grafana" {
  name        = "${local.name}-grafana"
  target_type = "ip"
  protocol    = "HTTP"
  port        = 3000
  vpc_id      = aws_vpc.main.id
  health_check {
    path                = "/grafana/api/health"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}
resource "aws_lb_listener_rule" "grafana" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana.arn
  }
  condition {
    path_pattern { values = ["/grafana", "/grafana/*"] }
  }
}
resource "aws_ecs_task_definition" "monitoring" {
  count                    = var.deploy_applications ? 1 : 0
  family                   = "${local.name}-grafana"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution["grafana"].arn
  task_role_arn            = aws_iam_role.task["grafana"].arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  volume { name = "grafana-tmp" }
  volume { name = "prometheus-data" }
  container_definitions = jsonencode([
    {
      name                   = "grafana"
      image                  = lookup(var.container_images, "grafana", "MISSING_IMAGE")
      essential              = true
      cpu                    = 256
      memoryReservation      = 512
      readonlyRootFilesystem = true
      linuxParameters        = { initProcessEnabled = true }
      mountPoints            = [{ sourceVolume = "grafana-tmp", containerPath = "/tmp", readOnly = false }]
      portMappings           = [{ containerPort = 3000, hostPort = 3000, protocol = "tcp" }]
      environment = [for name, value in {
        GF_SERVER_ROOT_URL            = "https://${var.frontend_domain}/grafana/"
        GF_SERVER_SERVE_FROM_SUB_PATH = "true"
        GF_AUTH_ANONYMOUS_ENABLED     = "false"
        GF_AUTH_BASIC_ENABLED         = "true"
        GF_USERS_ALLOW_SIGN_UP        = "false"
        GF_SECURITY_ADMIN_USER        = "admin"
        GF_SECURITY_COOKIE_SECURE     = "true"
        GF_SECURITY_COOKIE_SAMESITE   = "lax"
        GF_SECURITY_ALLOW_EMBEDDING   = "false"
        # Grafana 11.3 compares Origin.Hostname(), not the complete URL.
        GF_SECURITY_CSRF_TRUSTED_ORIGINS = var.frontend_domain
        GF_ANALYTICS_REPORTING_ENABLED   = "false"
        GF_ANALYTICS_CHECK_FOR_UPDATES   = "false"
        GF_DATABASE_TYPE                 = "postgres"
        GF_DATABASE_HOST                 = "${aws_db_instance.main["vectors"].address}:5432"
        GF_DATABASE_NAME                 = "grafana"
        GF_DATABASE_USER                 = "economicon_grafana"
        GF_DATABASE_SSL_MODE             = "verify-full"
        GF_DATABASE_CA_CERT_PATH         = "/etc/grafana/rds-ca.pem"
        GF_DATABASE_MAX_OPEN_CONN        = "5"
        GRAFANA_EVALUATION_DB_HOST       = "${aws_db_instance.main["vectors"].address}:5432"
      } : { name = name, value = value }]
      secrets = [for key in local.workloads.grafana.secret_keys : {
        name = key, valueFrom = "${aws_secretsmanager_secret.application["grafana"].arn}:${key}::"
      }]
      healthCheck      = { command = ["CMD-SHELL", "wget -q -O /dev/null http://127.0.0.1:3000/grafana/api/health"], interval = 30, timeout = 10, retries = 3, startPeriod = 90 }
      logConfiguration = { logDriver = "awslogs", options = { awslogs-group = aws_cloudwatch_log_group.application["grafana"].name, awslogs-region = var.region, awslogs-stream-prefix = "grafana" } }
      stopTimeout      = 60
    },
    {
      name                   = "prometheus"
      image                  = lookup(var.container_images, "prometheus", "MISSING_IMAGE")
      essential              = true
      cpu                    = 256
      memoryReservation      = 256
      readonlyRootFilesystem = true
      linuxParameters        = { initProcessEnabled = true }
      mountPoints            = [{ sourceVolume = "prometheus-data", containerPath = "/prometheus", readOnly = false }]
      environment            = [{ name = "MONITORING_NAMESPACE", value = aws_service_discovery_private_dns_namespace.main.name }]
      healthCheck            = { command = ["CMD-SHELL", "wget -q -O /dev/null http://127.0.0.1:9090/-/healthy"], interval = 30, timeout = 5, retries = 3, startPeriod = 30 }
      logConfiguration       = { logDriver = "awslogs", options = { awslogs-group = aws_cloudwatch_log_group.application["grafana"].name, awslogs-region = var.region, awslogs-stream-prefix = "prometheus" } }
      stopTimeout            = 60
    }
  ])
  lifecycle {
    precondition {
      condition     = var.application_adaptations_verified && alltrue([for name in ["grafana", "prometheus"] : startswith(lookup(var.container_images, name, ""), "${aws_ecr_repository.application["grafana"].repository_url}@sha256:")])
      error_message = "Monitoring requires verified private bootstrap and both immutable images in its own ECR repository."
    }
    precondition {
      condition     = local.rolling_vcpu <= 6 && var.desired_count >= 2
      error_message = "Keep two application replicas with total rolling capacity within the requested six vCPU."
    }
  }
}
resource "aws_ecs_service" "monitoring" {
  count                              = var.deploy_applications ? 1 : 0
  name                               = "grafana"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.monitoring[0].arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = 1
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 120
  enable_execute_command             = false
  wait_for_steady_state              = true
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = [for subnet in aws_subnet.app : subnet.id]
    security_groups  = [aws_security_group.component["grafana"].id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.grafana.arn
    container_name   = "grafana"
    container_port   = 3000
  }
  depends_on = [aws_lb_listener_rule.grafana, aws_route.app_egress, aws_iam_role_policy.execution, aws_db_instance.main]
}
