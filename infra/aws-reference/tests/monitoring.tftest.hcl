mock_provider "aws" {}
mock_provider "aws" { alias = "edge" }
variables {
  route53_zone_id           = "Z0000000000000TEST"
  frontend_domain           = "app.example.com"
  origin_domain             = "origin.example.com"
  postgres_version          = "16.9"
  postgres_parameter_family = "postgres16"
  rabbitmq_version          = "3.13"
  mq_admin_password         = "FictionalTestOnly-123!"
}
run "monitoring_private_routing_and_capacity" {
  command = plan
  assert {
    condition     = local.connections.alb_grafana == { source = "alb", target = "grafana", port = 3000 } && local.connections.grafana_db == { source = "grafana", target = "db", port = 5432 }
    error_message = "Grafana must use the private ALB and existing RDS."
  }
  assert {
    condition     = local.connections.metrics_backend == { source = "grafana", target = "backend", port = 8000 } && local.connections.metrics_processor == { source = "grafana", target = "processor", port = 8001 }
    error_message = "Prometheus must discover and scrape private tasks."
  }
  assert {
    condition     = local.rolling_vcpu <= 6 && local.rolling_vcpu == 5.5
    error_message = "The aggregate rolling capacity must fit the requested six vCPU."
  }
  assert {
    condition     = alltrue([for route in aws_cloudfront_distribution.main.ordered_cache_behavior : length(route.function_association) == 0 if startswith(route.path_pattern, "/grafana")]) && length([for route in aws_cloudfront_distribution.main.ordered_cache_behavior : route if startswith(route.path_pattern, "/grafana")]) == 2
    error_message = "Grafana routes must preserve the prefix instead of using the API rewrite."
  }
  assert {
    condition     = aws_lb_target_group.grafana.health_check[0].path == "/grafana/api/health" && aws_secretsmanager_secret.application["grafana"].recovery_window_in_days == 30 && length(aws_ecs_service.monitoring) == 0
    error_message = "Preparation must not enable services; credentials remain outside Terraform."
  }
}
