mock_provider "aws" {}

variables {
  route53_zone_id          = "Z0000000TEST"
  account_id               = "123456789012"
  connection_arn           = "arn:aws:codeconnections:eu-west-3:123456789012:connection/fake"
  permissions_boundary_arn = "arn:aws:iam::123456789012:policy/demo-boundary"
  github_token_secret_arn  = "arn:aws:secretsmanager:eu-west-3:123456789012:secret:fake-gh"
  mq_password_secret_arn   = "arn:aws:secretsmanager:eu-west-3:123456789012:secret:fake-mq"
}

run "manual_serialized_pipelines_and_private_state" {
  command = plan
  assert {
    condition     = length(aws_codepipeline.demo) == 2 && alltrue([for p in aws_codepipeline.demo : p.pipeline_type == "V2" && p.execution_mode == "QUEUED" && p.stage[0].action[0].configuration.DetectChanges == "false"])
    error_message = "Only manual queued up/down pipelines may be defined."
  }
  assert {
    condition     = aws_codebuild_project.runner.concurrent_build_limit == 1 && aws_codebuild_project.runner.source[0].type == "CODEPIPELINE"
    error_message = "Both pipelines must share a single serialized runner."
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.control.block_public_policy && aws_s3_bucket_public_access_block.control.restrict_public_buckets && !aws_s3_bucket.control.force_destroy && aws_s3_bucket_versioning.control.versioning_configuration[0].status == "Enabled"
    error_message = "State must be private/versioned and never emptied by demo teardown."
  }
  assert {
    condition     = length([for env in aws_codebuild_project.runner.environment[0].environment_variable : env if env.type == "SECRETS_MANAGER"]) == 2
    error_message = "Only secret ARNs may enter the runner definition, never secret values."
  }
}
