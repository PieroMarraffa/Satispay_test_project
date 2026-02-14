# Package the Lambda function code
data "archive_file" "this" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = var.output_path
}

# Lambda function
resource "aws_lambda_function" "this" {
  filename      = data.archive_file.this.output_path
  function_name = var.function_name
  role          = var.role_arn
  handler       = "lambda_function.lambda_handler"
  source_code_hash   = data.archive_file.this.output_base64sha256

  runtime = "python3.13"

  environment {
    variables = var.environment_variables
  }

  tags = var.tags
}

# Lambda function cloudwatch group
resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.function_name}"
  tags              = var.tags

  retention_in_days = 14
}