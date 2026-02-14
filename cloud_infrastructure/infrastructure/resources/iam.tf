module "lambda_reader_iam" {
  source      = "../../modules/iam"
  role_name   = "lambda-reader-role"
  policy_name = "lambda-reader-policy"

  statements = [
    {
      sid     = "DynamoDBRead"
      effect  = "Allow"
      actions = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"]
      resources = [
        aws_dynamodb_table.messages_table.arn,
        "${aws_dynamodb_table.messages_table.arn}/index/*"
      ]
    },
    {
      sid     = "WriteOwnLogs"
      effect  = "Allow"
      actions = ["logs:CreateLogStream", "logs:PutLogEvents"]
      resources = ["${module.lambda["API_reader"].cloudwatch_log_group_arn}:*"]
    }
  ]

  tags = var.tags
}

module "lambda_writer_iam" {
  source      = "../../modules/iam"
  role_name   = "lambda-writer-role"
  policy_name = "lambda-writer-policy"

  statements = [
    {
      sid      = "DynamoDBWrite"
      effect   = "Allow"
      actions  = ["dynamodb:PutItem"]
      resources = [aws_dynamodb_table.messages_table.arn]
    },
    {
      sid     = "WriteOwnLogs"
      effect  = "Allow"
      actions = ["logs:CreateLogStream", "logs:PutLogEvents"]
      resources = ["${module.lambda["API_writer"].cloudwatch_log_group_arn}:*"]
    }
  ]

  tags = var.tags
}