resource "local_file" "frontend_env" {
  filename = "${path.root}/s3_website/code/.env.local"
  content  = <<EOF
VITE_API_BASE_URL=${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.stage.name}
EOF
}

output "api_base_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.stage.name}"
}