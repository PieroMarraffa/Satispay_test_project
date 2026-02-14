resource "aws_apigatewayv2_integration" "integration" {
  api_id                = var.api_gateway_id
  integration_type      = "AWS_PROXY"
  integration_uri       = var.lambda_integration.lambda_arn

  integration_method    = var.lambda_integration.method

  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

resource "aws_apigatewayv2_route" "route" {
  for_each = { for idx, r in var.lambda_integration.route : idx => r }

  api_id    = var.api_gateway_id
  route_key = "${upper(var.lambda_integration.method)} /${each.value.path}${each.value.by_id ? "/{id}" : ""}"

  target = "integrations/${aws_apigatewayv2_integration.integration.id}"
  authorization_type = "NONE"
}

resource "aws_lambda_permission" "lambda_permission" {
  for_each = { for idx, r in var.lambda_integration.route : idx => r }
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_integration.lambda_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${var.api_gateway_execution_arn}/${upper(var.lambda_integration.method)}/${each.value.path}${each.value.by_id ? "/*" : ""}"
}