output "frontend_url" {
  value       = "https://${var.frontend_domain}"
  description = "Planned URL; an output is not evidence of a working or deployed application."
}
output "api_base_url" {
  value = "https://${var.frontend_domain}/api"
}
output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
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
output "rabbitmq_endpoints" {
  value = flatten([for instance in aws_mq_broker.main.instances : instance.endpoints])
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
