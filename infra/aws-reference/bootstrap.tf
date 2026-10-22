# Privileged one-off tasks only; services keep their separate runtime roles.
resource "aws_iam_role" "bootstrap" {
  name                 = "${local.name}-bootstrap"
  permissions_boundary = var.permissions_boundary_arn
  assume_role_policy   = local.task_trust
}
resource "aws_iam_role_policy" "bootstrap" {
  role = aws_iam_role.bootstrap.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Effect = "Allow", Action = "secretsmanager:GetSecretValue"
        Resource = concat([for db in aws_db_instance.main : db.master_user_secret[0].secret_arn],
        [for secret in aws_secretsmanager_secret.application : secret.arn], [aws_secretsmanager_secret.rehearsal.arn])
      },
      {
        Effect    = "Allow", Action = "kms:Decrypt", Resource = aws_kms_key.data.arn
        Condition = { StringEquals = { "kms:ViaService" = "secretsmanager.${var.region}.amazonaws.com" } }
      },
      {
        Effect   = "Allow"
        Action   = ["cognito-idp:AdminCreateUser", "cognito-idp:AdminGetUser", "cognito-idp:AdminSetUserPassword"]
        Resource = aws_cognito_user_pool.main.arn
      }
      ], var.mq_admin_secret_arn == null ? [] : [{
        Effect = "Allow", Action = "secretsmanager:GetSecretValue", Resource = var.mq_admin_secret_arn
        }], length(var.bedrock_model_arns) == 0 ? [] : [{
        Effect = "Allow", Action = "bedrock:InvokeModel", Resource = var.bedrock_model_arns
    }])
  })
}
