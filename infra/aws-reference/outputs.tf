output "frontend_url" {
  value       = "https://${var.frontend_domain}"
  description = "Planned URL; an output is not evidence of a working or deployed application."
}
output "bootstrap_network" {
  description = "Private network for controlled one-off bootstrap tasks."
  value = {
    subnets            = [for subnet in aws_subnet.app : subnet.id]
    security_groups    = { for name in ["backend", "processor", "azure-cost-api"] : name => aws_security_group.component[name].id }
    execution_roles    = { for name, role in aws_iam_role.execution : name => role.arn }
    task_roles         = { for name, role in aws_iam_role.task : name => role.arn }
    bootstrap_role_arn = aws_iam_role.bootstrap.arn
    security_group_id  = aws_security_group.component["bootstrap"].id
    log_groups         = { for name, group in aws_cloudwatch_log_group.application : name => group.name }
  }
}
output "api_base_url" {
  value = "https://${var.frontend_domain}/api"
}
output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}
output "readiness" {
  description = "Public resource references used by the live acceptance checker."
  value = {
    api_target_group_arn = aws_lb_target_group.api.arn
  }
}
output "ecr_repositories" {
  value = { for key, repo in aws_ecr_repository.application : key => repo.repository_url }
}
output "buckets" {
  value = { for key, bucket in aws_s3_bucket.main : key => bucket.id }
}
output "database_endpoints" {
  value = { for key, db in aws_db_instance.main : key => { host = db.address, port = db.port, database = db.db_name } }
}
output "database_admin_secret_arns" {
  value = { for key, db in aws_db_instance.main : key => db.master_user_secret[0].secret_arn }
}
output "runtime_secret_arns" {
  value = { for key, secret in aws_secretsmanager_secret.application : key => secret.arn }
}
output "rehearsal_secret_arn" {
  value = aws_secretsmanager_secret.rehearsal.arn
}
output "rabbitmq_endpoints" {
  value = flatten([for instance in aws_mq_broker.main.instances : instance.endpoints])
}
output "rabbitmq_console_url" {
  value = aws_mq_broker.main.instances[0].console_url
}
output "mq_admin_secret_arn" {
  value = var.mq_admin_secret_arn
}
output "cognito" {
  value = {
    user_pool_id = aws_cognito_user_pool.main.id
    client_id    = aws_cognito_user_pool_client.frontend.id
    issuer       = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
    login_domain = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.region}.amazoncognito.com"
    callback_url = "https://${var.frontend_domain}/auth/callback"
  }
}
output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.main.id
}
output "alarm_topic_arn" {
  value       = aws_sns_topic.alarms.arn
  description = "No subscription is configured."
}
output "bedrock_chat" {
  description = "Reviewed routing contract; output alone does not prove model access or inference acceptance."
  value = {
    profile_id          = var.bedrock_chat_profile_id
    profile_arn         = local.bedrock_chat_profile_arn
    destination_regions = var.bedrock_chat_profile_id == null ? [] : local.bedrock_chat_regions
  }
}
