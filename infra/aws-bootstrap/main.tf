terraform {
  required_version = ">= 1.13.3, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.13.0" }
  }
  # Bootstrap first uses protected local state; migrate to its own S3 key after
  # creation. It is NEVER in the demo state or demo destroy.
}

provider "aws" {
  region              = "eu-west-3"
  allowed_account_ids = [var.account_id]
  default_tags {
    tags = { Project = "economicon", Environment = "bootstrap", Task = "JUP-131", ManagedBy = "Terraform" }
  }
}

variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Provide the actual project account ID."
  }
}
variable "connection_arn" {
  description = "Existing AVAILABLE GitHub CodeConnections connection in Paris. Complete installation separately."
  type        = string
  validation {
    condition     = can(regex("^arn:aws:(codeconnections|codestar-connections):eu-west-3:[0-9]{12}:connection/", var.connection_arn))
    error_message = "Use an existing GitHub connection in eu-west-3."
  }
}
variable "permissions_boundary_arn" {
  description = "Existing reviewed boundary used on ALL demo IAM roles. Prevents Terraform privilege escalation."
  type        = string
  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:policy/", var.permissions_boundary_arn))
    error_message = "Supply an existing, reviewed permissions boundary ARN."
  }
}
variable "github_token_secret_arn" {
  description = "Existing Paris secret containing JSON token: read-only GitHub checks access. Never a Terraform secret value."
  type        = string
}
variable "mq_password_secret_arn" {
  description = "Existing Paris secret containing JSON password. Value is read only at runtime."
  type        = string
}
variable "route53_zone_id" {
  description = "Existing approved public zone only; never a wildcard DNS permission."
  type        = string
  validation {
    condition     = can(regex("^Z[A-Z0-9]+$", var.route53_zone_id))
    error_message = "Supply an existing public zone ID."
  }
}
variable "bootstrap_name" {
  type    = string
  default = "economicon-defensa"
}

locals {
  name = var.bootstrap_name
  phases = {
    up   = ["validate", "build", "plan", "APPROVAL", "apply", "release"]
    down = ["plan-down", "APPROVAL", "destroy"]
  }
}

resource "aws_s3_bucket" "control" {
  bucket_prefix = "${local.name}-control-"
  force_destroy = false
  lifecycle { prevent_destroy = true }
}
resource "aws_s3_bucket" "artifacts" {
  bucket_prefix = "${local.name}-artifacts-"
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_policy" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect    = "Deny", Principal = "*", Action = "s3:*",
    Resource  = [aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*"],
    Condition = { Bool = { "aws:SecureTransport" = "false" } }
  }] })
}
resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    id = "short-lived-pipeline-artifacts"
    filter { prefix = "" }
    status = "Enabled"
    expiration { days = 7 }
    noncurrent_version_expiration { noncurrent_days = 7 }
  }
}
resource "aws_s3_bucket_public_access_block" "control" {
  bucket                  = aws_s3_bucket.control.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "control" {
  bucket = aws_s3_bucket.control.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "control" {
  bucket = aws_s3_bucket.control.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_policy" "control" {
  bucket = aws_s3_bucket.control.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect    = "Deny", Principal = "*", Action = "s3:*",
    Resource  = [aws_s3_bucket.control.arn, "${aws_s3_bucket.control.arn}/*"],
    Condition = { Bool = { "aws:SecureTransport" = "false" } }
  }] })
}
resource "aws_s3_bucket_lifecycle_configuration" "control" {
  bucket = aws_s3_bucket.control.id
  rule {
    id = "short-lived-artifacts"
    filter { prefix = "cycles/" }
    status = "Enabled"
    expiration { days = 7 }
    noncurrent_version_expiration { noncurrent_days = 7 }
    abort_incomplete_multipart_upload { days_after_initiation = 1 }
  }
  # No expiration of Terraform state or the cycle registry.
}
resource "aws_dynamodb_table" "lease" {
  name         = "${local.name}-lease"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "domain"
  attribute {
    name = "domain"
    type = "S"
  }
  point_in_time_recovery { enabled = true }
  # No automatic TTL: an expired lock must never silently permit another stack
  # with the same public domain while AWS resources still exist.
}
resource "aws_cloudwatch_log_group" "build" {
  name              = "/codebuild/${local.name}"
  retention_in_days = 7
}
resource "aws_sqs_queue" "expiry_dlq" {
  name                      = "${local.name}-expiry-failures"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}
resource "aws_iam_role" "build" {
  name = "${local.name}-build"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "codebuild.amazonaws.com" }
  }] })
}
resource "aws_iam_role_policy" "build_control" {
  role = aws_iam_role.build.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["s3:ListBucket", "s3:GetBucketVersioning", "s3:GetBucketLocation", "s3:GetBucketAcl"], Resource = aws_s3_bucket.control.arn },
    { Effect = "Allow", Action = ["s3:GetBucketLocation", "s3:GetBucketVersioning", "s3:GetBucketAcl"], Resource = aws_s3_bucket.artifacts.arn },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject"], Resource = "${aws_s3_bucket.artifacts.arn}/*" },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject", "s3:DeleteObject"], Resource = ["${aws_s3_bucket.control.arn}/economicon/*", "${aws_s3_bucket.control.arn}/cycles/*", "${aws_s3_bucket.control.arn}/configs/*"] },
    { Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem"], Resource = aws_dynamodb_table.lease.arn },
    { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.build.arn}:*" },
    { Effect = "Allow", Action = "secretsmanager:GetSecretValue", Resource = [var.github_token_secret_arn, var.mq_password_secret_arn] },
    { Effect = "Allow", Action = "sts:AssumeRole", Resource = aws_iam_role.deploy.arn },
    { Effect = "Allow", Action = ["scheduler:CreateSchedule", "scheduler:GetSchedule", "scheduler:DeleteSchedule"], Resource = "arn:aws:scheduler:eu-west-3:${var.account_id}:schedule/default/economicon-*" },
    { Effect = "Allow", Action = "iam:PassRole", Resource = aws_iam_role.expiry.arn, Condition = { StringEquals = { "iam:PassedToService" = "scheduler.amazonaws.com" } } }
  ] })
}
resource "aws_iam_role" "deploy" {
  name = "${local.name}-deploy"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Action = "sts:AssumeRole", Principal = { AWS = aws_iam_role.build.arn }
  }] })
}
resource "aws_iam_role_policy" "deploy" {
  role = aws_iam_role.deploy.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    # Resource creation APIs often lack resource-level scoping. Restrict regional
    # APIs and IAM privilege separately. Dedicated project account only.
    { Effect = "Allow", Action = ["ec2:*", "elasticloadbalancing:*", "rds:*", "mq:*", "ecs:*", "ecr:*", "servicediscovery:*", "cognito-idp:*", "secretsmanager:*", "kms:*", "logs:*", "cloudwatch:*", "sns:*", "acm:*", "cloudfront:*", "wafv2:*", "tag:GetResources"], Resource = "*", Condition = { StringEquals = { "aws:RequestedRegion" = ["eu-south-2", "us-east-1"] } } },
    { Effect = "Allow", Action = ["route53:GetHostedZone", "route53:ListResourceRecordSets", "route53:ChangeResourceRecordSets"], Resource = "arn:aws:route53:::hostedzone/${var.route53_zone_id}" },
    { Effect = "Allow", Action = "route53:GetChange", Resource = "arn:aws:route53:::change/*" },
    { Effect = "Allow", Action = ["s3:CreateBucket", "s3:DeleteBucket", "s3:ListBucket", "s3:GetBucket*", "s3:PutBucket*", "s3:DeleteBucketPolicy", "s3:GetObject*", "s3:PutObject", "s3:DeleteObject*", "s3:ListBucketVersions"], Resource = ["arn:aws:s3:::economicon-ensayo*", "arn:aws:s3:::economicon-defensa*"] },
    { Effect = "Allow", Action = ["iam:CreateRole", "iam:PutRolePermissionsBoundary"], Resource = "arn:aws:iam::${var.account_id}:role/economicon-*", Condition = { StringEquals = { "iam:PermissionsBoundary" = var.permissions_boundary_arn } } },
    { Effect = "Allow", Action = ["iam:GetRole", "iam:DeleteRole", "iam:TagRole", "iam:UntagRole", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies", "iam:GetRolePolicy", "iam:PutRolePolicy", "iam:DeleteRolePolicy"], Resource = "arn:aws:iam::${var.account_id}:role/economicon-*" },
    { Effect = "Allow", Action = "iam:PassRole", Resource = "arn:aws:iam::${var.account_id}:role/economicon-*", Condition = { StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } } },
    { Effect = "Allow", Action = "iam:CreateServiceLinkedRole", Resource = "*", Condition = { StringLike = { "iam:AWSServiceName" = ["ecs.amazonaws.com", "rds.amazonaws.com", "elasticloadbalancing.amazonaws.com", "mq.amazonaws.com", "cloudfront.amazonaws.com", "vpcorigin.cloudfront.amazonaws.com"] } } },
    { Effect = "Deny", Action = ["iam:DeleteRolePermissionsBoundary", "iam:CreatePolicy", "iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion"], Resource = "*" },
    { Effect = "Deny", Action = "s3:*", Resource = [aws_s3_bucket.control.arn, "${aws_s3_bucket.control.arn}/*", aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*"] },
    { Effect = "Deny", Action = ["iam:DeleteRole", "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:PutRolePermissionsBoundary"], Resource = [aws_iam_role.build.arn, "arn:aws:iam::${var.account_id}:role/${local.name}-deploy", "arn:aws:iam::${var.account_id}:role/${local.name}-pipeline", "arn:aws:iam::${var.account_id}:role/${local.name}-expiry"] }
  ] })
}
resource "aws_iam_role" "pipeline" {
  name               = "${local.name}-pipeline"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "codepipeline.amazonaws.com" } }] })
}
resource "aws_iam_role_policy" "pipeline" {
  role = aws_iam_role.pipeline.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["codestar-connections:UseConnection", "codeconnections:UseConnection"], Resource = var.connection_arn },
    { Effect = "Allow", Action = ["s3:GetBucketVersioning", "s3:GetBucketLocation", "s3:GetBucketAcl"], Resource = aws_s3_bucket.artifacts.arn },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject"], Resource = "${aws_s3_bucket.artifacts.arn}/*" },
    { Effect = "Allow", Action = ["codebuild:StartBuild", "codebuild:BatchGetBuilds"], Resource = aws_codebuild_project.runner.arn }
  ] })
}
resource "aws_codebuild_project" "runner" {
  name                   = local.name
  service_role           = aws_iam_role.build.arn
  build_timeout          = 180
  queued_timeout         = 60
  concurrent_build_limit = 1
  artifacts { type = "CODEPIPELINE" }
  source {
    type      = "CODEPIPELINE"
    buildspec = "infra/aws-cicd/buildspec.yml"
  }
  environment {
    compute_type    = "BUILD_GENERAL1_MEDIUM"
    image           = "aws/codebuild/standard:7.0"
    type            = "LINUX_CONTAINER"
    privileged_mode = true
    dynamic "environment_variable" {
      for_each = {
        CONTROL_BUCKET   = aws_s3_bucket.control.id, LEASE_TABLE = aws_dynamodb_table.lease.name,
        EXPECTED_ACCOUNT = var.account_id, DEPLOY_ROLE_ARN = aws_iam_role.deploy.arn,
        BOUNDARY_ARN     = var.permissions_boundary_arn, EXPIRY_ROLE_ARN = aws_iam_role.expiry.arn,
        RUNNER_NAME      = local.name, CONTROL_REGION = "eu-west-3"
        EXPIRY_DLQ_ARN   = aws_sqs_queue.expiry_dlq.arn
      }
      content {
        name  = environment_variable.key
        value = environment_variable.value
      }
    }
    environment_variable {
      name  = "GITHUB_TOKEN"
      value = "${var.github_token_secret_arn}:token"
      type  = "SECRETS_MANAGER"
    }
    environment_variable {
      name  = "MQ_ADMIN_PASSWORD"
      value = "${var.mq_password_secret_arn}:password"
      type  = "SECRETS_MANAGER"
    }
  }
  logs_config {
    cloudwatch_logs { group_name = aws_cloudwatch_log_group.build.name }
  }
}
resource "aws_iam_role" "expiry" {
  name               = "${local.name}-expiry"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "scheduler.amazonaws.com" } }] })
}
resource "aws_iam_role_policy" "expiry" {
  role = aws_iam_role.expiry.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Action = "codebuild:StartBuild", Resource = aws_codebuild_project.runner.arn
  }, { Effect = "Allow", Action = "sqs:SendMessage", Resource = aws_sqs_queue.expiry_dlq.arn }] })
}
resource "aws_codepipeline" "demo" {
  depends_on     = [aws_iam_role_policy.pipeline]
  for_each       = local.phases
  name           = "${local.name}-${each.key}"
  role_arn       = aws_iam_role.pipeline.arn
  pipeline_type  = "V2"
  execution_mode = "QUEUED"
  variable {
    name          = "ConfigKey"
    default_value = "configs/NOT_READY.json"
    description   = "Immutable cycle configuration uploaded outside Git; not secrets."
  }
  artifact_store {
    location = aws_s3_bucket.artifacts.id
    type     = "S3"
  }
  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      namespace        = "SourceVariables"
      output_artifacts = ["Source"]
      configuration    = { ConnectionArn = var.connection_arn, FullRepositoryId = "EconomiconFinOps/tfm-economicon", BranchName = "develop", DetectChanges = "false", OutputArtifactFormat = "CODE_ZIP" }
    }
  }
  dynamic "stage" {
    for_each = each.value
    content {
      name = replace(stage.value, "-", "_")
      action {
        name            = replace(stage.value, "-", "_")
        category        = stage.value == "APPROVAL" ? "Approval" : "Build"
        owner           = "AWS"
        provider        = stage.value == "APPROVAL" ? "Manual" : "CodeBuild"
        version         = "1"
        input_artifacts = stage.value == "APPROVAL" ? null : ["Source"]
        configuration = stage.value == "APPROVAL" ? {
          CustomData = "Review saved plan/binding in control S3 for #{variables.ConfigKey}, SHA #{SourceVariables.CommitId}. No pipeline success attests runtime."
          } : {
          ProjectName = aws_codebuild_project.runner.name
          EnvironmentVariables = jsonencode([
            { name = "PHASE", value = stage.value, type = "PLAINTEXT" },
            { name = "CONFIG_KEY", value = "#{variables.ConfigKey}", type = "PLAINTEXT" },
            { name = "SOURCE_SHA", value = "#{SourceVariables.CommitId}", type = "PLAINTEXT" },
            { name = "EXECUTION_ID", value = "#{codepipeline.PipelineExecutionId}", type = "PLAINTEXT" }
          ])
        }
      }
    }
  }
}
output "control_bucket" { value = aws_s3_bucket.control.id }
output "expiry_dlq_url" { value = aws_sqs_queue.expiry_dlq.url }
output "lease_table" { value = aws_dynamodb_table.lease.name }
output "pipelines" { value = { for action, pipeline in aws_codepipeline.demo : action => pipeline.name } }
