# Mock-only private networking, IAM, CORS and container startup contracts.
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
  permissions_boundary_arn  = "arn:aws:iam::123456789012:policy/synthetic-boundary"
}

run "private_chat_and_document_permissions" {
  command = plan
  assert {
    condition     = local.connections.backend_chat == { source = "backend", target = "processor", port = 8003 }
    error_message = "Only backend may reach the private processor chat port."
  }
  assert {
    condition     = toset(keys(aws_iam_role_policy.documents)) == toset(["backend", "processor"])
    error_message = "Both document services need scoped task role permissions."
  }
  assert {
    condition     = toset(one(aws_s3_bucket_cors_configuration.documents.cors_rule).allowed_origins) == toset(["https://app.example.com"])
    error_message = "Document upload CORS must allow only the frontend origin."
  }
  assert {
    condition     = aws_iam_role.bootstrap.permissions_boundary == var.permissions_boundary_arn && jsondecode(aws_iam_role.bootstrap.assume_role_policy).Statement[0].Principal.Service == "ecs-tasks.amazonaws.com"
    error_message = "Bootstrap must use a distinct ECS role constrained by the reviewed boundary."
  }
  assert {
    condition     = local.connections.bootstrap_db == { source = "bootstrap", target = "db", port = 5432 } && local.connections.bootstrap_mq == { source = "bootstrap", target = "mq", port = 443 }
    error_message = "Database and RabbitMQ management bootstrap must stay on private security group paths."
  }
  assert {
    condition     = contains(aws_cognito_user_pool_client.frontend.explicit_auth_flows, "ALLOW_ADMIN_USER_PASSWORD_AUTH") && !contains(aws_cognito_user_pool_client.frontend.explicit_auth_flows, "ALLOW_USER_PASSWORD_AUTH") && !contains(aws_cognito_user_pool_client.frontend.write_attributes, "custom:rehearsal") && one([for attr in aws_cognito_user_pool.main.schema : attr if attr.name == "rehearsal"]).mutable == false
    error_message = "Rehearsal login must be admin-only and its ownership marker immutable."
  }
}

run "ecs_runtime_configuration" {
  command = plan
  override_resource {
    target          = aws_cognito_user_pool.main
    override_during = plan
    values          = { id = "eu-west-1_Synthetic" }
  }
  override_resource {
    target          = aws_cognito_user_pool_client.frontend
    override_during = plan
    values          = { id = "syntheticclientid" }
  }
  override_resource {
    target          = aws_kms_key.data
    override_during = plan
    values          = { arn = "arn:aws:kms:eu-west-1:123456789012:key/00000000-0000-0000-0000-000000000000" }
  }
  override_resource {
    target          = aws_s3_bucket.main["documents"]
    override_during = plan
    values          = { id = "economicon-synthetic-documents", arn = "arn:aws:s3:::economicon-synthetic-documents" }
  }
  override_resource {
    target          = aws_secretsmanager_secret.application["backend"]
    override_during = plan
    values          = { arn = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-backend-000000" }
  }
  override_resource {
    target          = aws_secretsmanager_secret.application["processor"]
    override_during = plan
    values          = { arn = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-processor-000000" }
  }
  override_resource {
    target          = aws_secretsmanager_secret.application["azure-cost-api"]
    override_during = plan
    values          = { arn = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-fixture-000000" }
  }
  override_resource {
    target          = aws_ecr_repository.application["backend"]
    override_during = plan
    values          = { repository_url = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/backend" }
  }
  override_resource {
    target          = aws_ecr_repository.application["processor"]
    override_during = plan
    values          = { repository_url = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/processor" }
  }
  override_resource {
    target          = aws_ecr_repository.application["azure-cost-api"]
    override_during = plan
    values          = { repository_url = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/azure-cost-api" }
  }
  override_resource {
    target          = aws_ecr_repository.application["grafana"]
    override_during = plan
    values          = { repository_url = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/grafana" }
  }
  override_resource {
    target          = aws_secretsmanager_secret.application["grafana"]
    override_during = plan
    values          = { arn = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-grafana-000000" }
  }
  override_resource {
    target          = aws_db_instance.main["vectors"]
    override_during = plan
    values          = { address = "synthetic.eu-west-1.rds.amazonaws.com", master_user_secret = [{ secret_arn = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:rds!db-synthetic-vectors", kms_key_id = "synthetic", secret_status = "active" }] }
  }
  variables {
    deploy_applications              = true
    application_adaptations_verified = true
    container_images = {
      grafana        = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/grafana@sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
      prometheus     = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/grafana@sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
      backend        = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/backend@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      processor      = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/processor@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
      azure-cost-api = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/azure-cost-api@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    }
  }
  assert {
    condition     = contains([for port in jsondecode(aws_ecs_task_definition.application["processor"].container_definitions)[0].portMappings : port.containerPort], 8003)
    error_message = "Processor must publish its private chat listener in awsvpc mode."
  }
  assert {
    condition     = contains([for env in jsondecode(aws_ecs_task_definition.application["backend"].container_definitions)[0].environment : "${env.name}=${env.value}"], "AUTH_PROVIDER=cognito") && contains([for env in jsondecode(aws_ecs_task_definition.application["processor"].container_definitions)[0].environment : "${env.name}=${env.value}"], "PROCESSOR_SCHEMA_MODE=verify")
    error_message = "AWS services must use Cognito and verify pre-migrated schemas."
  }
  assert {
    condition = alltrue([for name in ["backend", "processor"] :
      contains([for secret in jsondecode(aws_ecs_task_definition.application[name].container_definitions)[0].secrets : secret.name], "CHAT_HMAC_KEY") &&
      contains([for env in jsondecode(aws_ecs_task_definition.application[name].container_definitions)[0].environment : "${env.name}=${env.value}"], "ECONOMICON_AWS_RUNTIME=ecs")
    ])
    error_message = "Both images must prepare the injected HMAC before starting the application."
  }
  assert {
    condition     = contains([for statement in jsondecode(aws_iam_role_policy.documents["backend"].policy).Statement : jsonencode(statement.Action)], jsonencode("s3:PutObject")) && !contains([for statement in jsondecode(aws_iam_role_policy.documents["processor"].policy).Statement : jsonencode(statement.Action)], jsonencode("s3:PutObject"))
    error_message = "Only backend may grant upload URLs or finalize objects; processor reads and cleans up."
  }
  assert {
    condition     = aws_ecs_service.monitoring[0].desired_count == 1 && !aws_ecs_service.monitoring[0].network_configuration[0].assign_public_ip && aws_ecs_task_definition.monitoring[0].cpu == "512" && aws_ecs_task_definition.monitoring[0].memory == "1024"
    error_message = "Monitoring stays one private 0.5vCPU/1GiB task."
  }
  assert {
    condition     = length(jsondecode(aws_ecs_task_definition.monitoring[0].container_definitions)) == 2 && alltrue([for container in jsondecode(aws_ecs_task_definition.monitoring[0].container_definitions) : container.readonlyRootFilesystem]) && length(jsondecode(aws_ecs_task_definition.monitoring[0].container_definitions)[0].secrets) == 4
    error_message = "Both containers must use read-only roots; credentials are secret references."
  }
  assert {
    condition     = contains([for env in jsondecode(aws_ecs_task_definition.monitoring[0].container_definitions)[0].environment : "${env.name}=${env.value}"], "GF_DATABASE_SSL_MODE=verify-full") && contains([for env in jsondecode(aws_ecs_task_definition.monitoring[0].container_definitions)[0].environment : "${env.name}=${env.value}"], "GF_AUTH_ANONYMOUS_ENABLED=false") && alltrue([for service in aws_ecs_service.application : service.deployment_maximum_percent == 150])
    error_message = "RDS TLS, authenticated Grafana and constrained rolling capacity are required."
  }
  assert {
    condition     = contains([for env in jsondecode(aws_ecs_task_definition.monitoring[0].container_definitions)[0].environment : "${env.name}=${env.value}"], "GF_SECURITY_CSRF_TRUSTED_ORIGINS=${var.frontend_domain}")
    error_message = "Browser session queries must trust only the frontend Origin when CloudFront strips Host."
  }

}
