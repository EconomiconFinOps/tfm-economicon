# System-defined inference profiles already exist in Bedrock. This creates only
# the processor's scoped role policy, never a model, profile or throughput.
data "aws_caller_identity" "bedrock" {
  count = var.bedrock_chat_profile_id == null ? 0 : 1
}

locals {
  # Destination changes must be reviewed and matched in the live preflight.
  # https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-micro.html
  bedrock_chat_regions = ["eu-central-1", "eu-north-1", "eu-south-2", "eu-west-1", "eu-west-3"]
  bedrock_chat_profile_arn = var.bedrock_chat_profile_id == null ? null : (
    "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.bedrock[0].account_id}:inference-profile/${var.bedrock_chat_profile_id}"
  )
}

resource "aws_iam_role_policy" "bedrock_chat" {
  count = var.bedrock_chat_profile_id == null ? 0 : 1
  role  = aws_iam_role.task["processor"].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = [local.bedrock_chat_profile_arn]
      },
      {
        Effect = "Allow"
        Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = [for region in local.bedrock_chat_regions :
          "arn:aws:bedrock:${region}::foundation-model/${trimprefix(var.bedrock_chat_profile_id, "eu.")}"
        ]
        Condition = { StringEquals = { "bedrock:InferenceProfileArn" = local.bedrock_chat_profile_arn } }
      }
    ]
  })
}
