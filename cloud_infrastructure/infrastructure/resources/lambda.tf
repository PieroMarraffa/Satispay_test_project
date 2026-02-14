locals {
  lambdas = {
    API_writer = {
      source_dir         = "${path.module}/lambda_codes/writer"
      output_path         = "${path.module}/lambda_codes/writer/function.zip"
      function_name       = "API_writer"
      role_arn           = module.lambda_writer_iam.role_arn
      environment_variables = {
          DDB_TABLE_NAME = aws_dynamodb_table.messages_table.name
      }
    }
    API_reader = {
      source_dir         = "${path.module}/lambda_codes/reader"
      output_path         = "${path.module}/lambda_codes/reader/function.zip"
      function_name       = "API_reader"
      role_arn           = module.lambda_reader_iam.role_arn
      environment_variables = {
          DDB_TABLE_NAME = aws_dynamodb_table.messages_table.name
      }
    }
  }
}

module "lambda" {
  source = "../../modules/lambda"
  for_each = local.lambdas
  source_dir = each.value.source_dir
  output_path = each.value.output_path
  function_name = each.value.function_name
  role_arn = each.value.role_arn
  environment_variables = each.value.environment_variables
  tags = var.tags
}