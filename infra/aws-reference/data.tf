resource "aws_kms_key" "data" {
  description             = "${local.name} data and application secrets"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}
resource "aws_kms_alias" "data" {
  name          = "alias/${local.name}-data"
  target_key_id = aws_kms_key.data.key_id
}
resource "aws_db_subnet_group" "main" {
  name       = local.name
  subnet_ids = [for subnet in aws_subnet.data : subnet.id]
}
resource "aws_db_parameter_group" "main" {
  name_prefix = "${local.name}-"
  family      = var.postgres_parameter_family
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}
resource "aws_db_instance" "main" {
  for_each                        = { operational = "economicon", vectors = "embeddings" }
  identifier                      = "${local.name}-${each.key}"
  engine                          = "postgres"
  engine_version                  = var.postgres_version
  instance_class                  = var.db_instance_class
  db_name                         = each.value
  username                        = "economicon_admin"
  manage_master_user_password     = true
  master_user_secret_kms_key_id   = aws_kms_key.data.arn
  allocated_storage               = 20
  max_allocated_storage           = 100
  storage_type                    = "gp3"
  storage_encrypted               = true
  kms_key_id                      = aws_kms_key.data.arn
  multi_az                        = true
  publicly_accessible             = false
  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.component["db"].id]
  parameter_group_name            = aws_db_parameter_group.main.name
  backup_retention_period         = 7
  backup_window                   = "02:00-03:00"
  maintenance_window              = "sun:04:00-sun:05:00"
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  deletion_protection             = true
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${local.name}-${each.key}-${var.final_snapshot_suffix}"
  copy_tags_to_snapshot           = true
  auto_minor_version_upgrade      = true
  apply_immediately               = false
}
resource "aws_mq_broker" "main" {
  broker_name                = local.name
  engine_type                = "RabbitMQ"
  engine_version             = var.rabbitmq_version
  host_instance_type         = var.mq_instance_type
  deployment_mode            = "CLUSTER_MULTI_AZ"
  subnet_ids                 = [for subnet in aws_subnet.data : subnet.id]
  security_groups            = [aws_security_group.component["mq"].id]
  publicly_accessible        = false
  auto_minor_version_upgrade = true
  apply_immediately          = false
  encryption_options {
    use_aws_owned_key = false
    kms_key_id        = aws_kms_key.data.arn
  }
  user {
    username = "economicon_admin"
    password = var.mq_admin_password
  }
  logs {
    general = true
  }
}
resource "aws_secretsmanager_secret" "application" {
  for_each                = toset(["backend", "processor", "azure-cost-api"])
  name                    = "${local.name}/${each.key}/runtime"
  description             = "JSON secret container only: values are provisioned outside Terraform, see README"
  kms_key_id              = aws_kms_key.data.arn
  recovery_window_in_days = 30
}
resource "aws_s3_bucket" "main" {
  for_each      = toset(["frontend", "documents"])
  bucket_prefix = "${local.name}-${each.key}-"
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "main" {
  for_each                = aws_s3_bucket.main
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "main" {
  for_each = aws_s3_bucket.main
  bucket   = each.value.id
  versioning_configuration {
    status = "Enabled"
  }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  for_each = aws_s3_bucket.main
  bucket   = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = each.key == "documents" ? "aws:kms" : "AES256"
      kms_master_key_id = each.key == "documents" ? aws_kms_key.data.arn : null
    }
    bucket_key_enabled = each.key == "documents"
  }
}
resource "aws_s3_bucket_policy" "main" {
  for_each = aws_s3_bucket.main
  bucket   = each.value.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Sid       = "DenyInsecureTransport", Effect = "Deny", Principal = "*", Action = "s3:*"
        Resource  = [each.value.arn, "${each.value.arn}/*"]
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      }
      ], each.key == "frontend" ? [{
        Sid       = "CloudFrontRead", Effect = "Allow", Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject", Resource = "${each.value.arn}/*"
        Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.main.arn } }
    }] : [])
  })
}
