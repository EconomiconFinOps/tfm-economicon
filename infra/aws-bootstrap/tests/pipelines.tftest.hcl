mock_provider "aws" {}

# Make only generated identity attributes known while evaluating the real policy.
override_resource {
  target          = aws_s3_bucket.control
  override_during = plan
  values          = { arn = "arn:aws:s3:::synthetic-control" }
}
override_resource {
  target          = aws_s3_bucket.artifacts
  override_during = plan
  values          = { arn = "arn:aws:s3:::synthetic-artifacts" }
}
override_resource {
  target          = aws_iam_role.build
  override_during = plan
  values          = { arn = "arn:aws:iam::123456789012:role/synthetic-build" }
}

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
    condition = alltrue([for p in aws_codepipeline.demo : alltrue([
      for stage in p.stage : alltrue([for action in stage.action :
        action.category != "Approval" || strcontains(lookup(action.configuration, "CustomData", ""), "#{PlanVariables.PLAN_SHA256}")
      ])
    ])])
    error_message = "Manual approvals must display the hash exported by the corresponding plan action."
  }
  assert {
    condition     = toset(jsondecode(aws_iam_role_policy.deploy.policy).Statement[0].Condition.StringEquals["aws:RequestedRegion"]) == toset(["eu-west-1", "us-east-1"])
    error_message = "Application creation stays in Ireland with Virginia edge; Spain is not allowed."
  }
  assert {
    condition = toset(one([for statement in jsondecode(aws_iam_role_policy.deploy.policy).Statement : statement if statement.Action == "servicequotas:GetServiceQuota"]).Resource) == toset([
      "arn:aws:servicequotas:eu-west-1:123456789012:fargate/L-3032A538",
      "arn:aws:servicequotas:eu-west-3:123456789012:codebuild/L-2DC20C30"
    ])
    error_message = "Quota preflight may read only the two approved quotas; it cannot request increases."
  }
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
  assert {
    condition = jsondecode(aws_iam_role_policy.bedrock_metadata.policy).Statement[0].Action == ["bedrock:GetInferenceProfile"] && toset(jsondecode(aws_iam_role_policy.bedrock_metadata.policy).Statement[0].Resource) == toset([
      "arn:aws:bedrock:eu-west-1:123456789012:inference-profile/eu.amazon.nova-micro-v1:0",
      "arn:aws:bedrock:eu-west-1:123456789012:inference-profile/eu.amazon.nova-lite-v1:0"
    ])
    error_message = "Deploy may read only the reviewed profile metadata; model invocation belongs to ECS."
  }
}
