# Mocked providers: these tests do not contact AWS, request credentials or apply.
mock_provider "aws" {}
mock_provider "aws" {
  alias = "edge"
}

variables {
  route53_zone_id           = "Z0000000000000TEST"
  frontend_domain           = "app.example.com"
  origin_domain             = "origin.example.com"
  postgres_version          = "16.9"
  postgres_parameter_family = "postgres16"
  rabbitmq_version          = "3.13"
  mq_admin_password         = "FictionalTestOnly-123!"
}

run "private_data_and_documentary_defaults" {
  command = plan

  assert {
    condition     = length(aws_ecs_service.application) == 0 && length(aws_ecs_task_definition.application) == 0
    error_message = "Applications must not be enabled by default."
  }
  assert {
    condition     = aws_lb.api.internal && alltrue([for db in aws_db_instance.main : !db.publicly_accessible && db.storage_encrypted && db.multi_az && db.deletion_protection])
    error_message = "The ALB and databases must remain private and databases protected."
  }
  assert {
    condition     = !aws_mq_broker.main.publicly_accessible && aws_mq_broker.main.deployment_mode == "CLUSTER_MULTI_AZ" && length(aws_subnet.data) == 3
    error_message = "MQ must be private across three AZs."
  }
  assert {
    condition     = aws_cloudfront_cache_policy.api.min_ttl == 0 && aws_cloudfront_cache_policy.api.max_ttl == 0 && alltrue([for error in aws_cloudfront_distribution.main.custom_error_response : error.error_caching_min_ttl == 0])
    error_message = "API responses and errors must not be cached across tenants."
  }
  assert {
    condition     = length(aws_nat_gateway.main) == 3 && length(aws_iam_role_policy.bedrock) == 0
    error_message = "Default uses one NAT per AZ and grants no Bedrock inference permissions."
  }
  assert {
    condition     = alltrue([for block in aws_s3_bucket_public_access_block.main : block.block_public_acls && block.block_public_policy && block.ignore_public_acls && block.restrict_public_buckets])
    error_message = "S3 public access must remain fully blocked."
  }
}

run "application_activation_requires_adaptation" {
  command = plan
  variables {
    deploy_applications              = true
    application_adaptations_verified = false
  }
  expect_failures = [
    aws_ecs_task_definition.application["backend"],
    aws_ecs_task_definition.application["processor"],
    aws_ecs_task_definition.application["azure-cost-api"]
  ]
}

run "single_nat_is_explicit" {
  command = plan
  variables {
    single_nat_gateway = true
  }
  assert {
    condition     = length(aws_nat_gateway.main) == 1 && length(aws_route_table.app) == 3
    error_message = "Single-NAT option must retain all three private application subnets."
  }
}

run "reject_wrong_region_zones" {
  command = plan
  variables {
    availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  }
  expect_failures = [var.availability_zones]
}

run "adapted_workload_shape" {
  command = plan
  override_resource {
    target = aws_ecr_repository.application["backend"]
    values = { repository_url = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/backend" }
  }
  override_resource {
    target = aws_ecr_repository.application["processor"]
    values = { repository_url = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/processor" }
  }
  override_resource {
    target = aws_ecr_repository.application["azure-cost-api"]
    values = { repository_url = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/azure-cost-api" }
  }
  variables {
    deploy_applications              = true
    application_adaptations_verified = true
    container_images = {
      backend        = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/backend@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      processor      = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/processor@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
      azure-cost-api = "123456789012.dkr.ecr.eu-west-1.amazonaws.com/economicon-reference/azure-cost-api@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    }
  }
  assert {
    condition     = length(aws_ecs_service.application) == 3 && alltrue([for service in aws_ecs_service.application : !service.network_configuration[0].assign_public_ip && service.deployment_circuit_breaker[0].rollback])
    error_message = "Adapted workloads must use private interfaces and deployment rollback."
  }
  assert {
    condition     = alltrue([for task in aws_ecs_task_definition.application : task.network_mode == "awsvpc" && task.cpu == "512" && task.memory == "1024"])
    error_message = "Fargate sizing and network mode must remain internally consistent."
  }
}

run "reject_database_family_mismatch" {
  command = plan
  variables {
    postgres_parameter_family = "postgres15"
  }
  expect_failures = [var.postgres_parameter_family]
}
