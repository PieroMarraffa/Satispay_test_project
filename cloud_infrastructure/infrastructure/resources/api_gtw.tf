locals {
  lambda_integration = {
    lambda_reader_integration = {
      lambda_arn = module.lambda["API_reader"].invoke_arn
      lambda_name = module.lambda["API_reader"].function_name
      method      = "GET"
      route       = [
        {
          path  = "messages"
          by_id = false
        },
        {
          path  = "messages" #/messages/{id}
          by_id = true
        }
      ]
    }
    lambda_writer_integration = {
      lambda_arn = module.lambda["API_writer"].invoke_arn
      lambda_name = module.lambda["API_writer"].function_name
      method      = "POST"
      route       = [
        {
          path  = "messages"
          by_id = false
        }
      ]
    }
  }
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "satispay_http_api"
  protocol_type = "HTTP"
  tags          = var.tags

  dynamic "cors_configuration" {
    for_each = var.test_via_ui ? [1] : []
    content {
      allow_origins = [var.s3_website_uri]

      allow_headers = [
        "content-type",
        "authorization",
        "x-amz-date",
        "x-amz-security-token",
        "x-amz-user-agent",
        "x-api-key"
      ]

      allow_methods = [
        "GET",
        "POST",
        "OPTIONS"
      ]
    }
  }
}

module "api_gateway_lambda_integration" {
  for_each = local.lambda_integration

  source = "../../modules/api_gtw_lambda_integration"

  api_gateway_id = aws_apigatewayv2_api.http_api.id
  api_gateway_execution_arn = aws_apigatewayv2_api.http_api.execution_arn
  lambda_integration = each.value
  tags = var.tags
}

resource "aws_apigatewayv2_stage" "stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "test"
  auto_deploy = true

  default_route_settings {
    detailed_metrics_enabled = false
    throttling_burst_limit   = 100
    throttling_rate_limit    = 50
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw_log_group.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      ip             = "$context.identity.sourceIp"
      protocol       = "$context.protocol"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gw_log_group" {
  name              = "/aws/apigateway/${aws_apigatewayv2_api.http_api.name}"
  retention_in_days = 14

  tags = var.tags
}