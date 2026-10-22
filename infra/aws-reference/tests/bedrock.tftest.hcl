# All providers and account metadata are mocked: no AWS calls or credentials.
mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012" }
  }
}
mock_provider "aws" {
  alias = "edge"
}

variables {
  region                    = "eu-south-2"
  availability_zones        = ["eu-south-2a", "eu-south-2b", "eu-south-2c"]
  route53_zone_id           = "Z0000000000000TEST"
  frontend_domain           = "app.example.com"
  origin_domain             = "origin.example.com"
  postgres_version          = "16.9"
  postgres_parameter_family = "postgres16"
  rabbitmq_version          = "3.13"
  mq_admin_password         = "FictionalTestOnly-123!"
}

run "eu_chat_profile_is_explicit_and_scoped" {
  command = plan
  variables {
    bedrock_chat_profile_id = "eu.amazon.nova-micro-v1:0"
  }
  assert {
    condition     = length(aws_iam_role_policy.bedrock_chat) == 1 && length(aws_iam_role_policy.bedrock) == 0
    error_message = "Only the processor chat profile policy may be added when embeddings are not enabled."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.bedrock_chat[0].policy).Statement[0].Resource == ["arn:aws:bedrock:eu-south-2:123456789012:inference-profile/eu.amazon.nova-micro-v1:0"]
    error_message = "The profile must be pinned to the deployment account and source region."
  }
  assert {
    condition = toset(jsondecode(aws_iam_role_policy.bedrock_chat[0].policy).Statement[1].Resource) == toset([
      for region in ["eu-central-1", "eu-north-1", "eu-south-2", "eu-west-1", "eu-west-3"] :
      "arn:aws:bedrock:${region}::foundation-model/amazon.nova-micro-v1:0"
    ])
    error_message = "Only the documented EU destinations of the exact foundation model may be allowed."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.bedrock_chat[0].policy).Statement[1].Condition.StringEquals["bedrock:InferenceProfileArn"] == "arn:aws:bedrock:eu-south-2:123456789012:inference-profile/eu.amazon.nova-micro-v1:0"
    error_message = "Destination foundation models must be callable only through the reviewed profile."
  }
}

run "no_chat_inference_by_default" {
  command = plan
  assert {
    condition     = length(aws_iam_role_policy.bedrock_chat) == 0
    error_message = "The reference must not grant chat inference by default."
  }
}

run "reject_global_or_unreviewed_profile" {
  command = plan
  variables {
    bedrock_chat_profile_id = "global.amazon.nova-micro-v1:0"
  }
  expect_failures = [var.bedrock_chat_profile_id]
}
