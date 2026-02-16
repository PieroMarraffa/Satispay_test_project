output "website_endpoint" {
  value = aws_s3_bucket_website_configuration.site.website_endpoint
}

output "website_url" {
  value = "http://${aws_s3_bucket_website_configuration.site.website_endpoint}"
}

output "website_bucket_name" {
  value = aws_s3_bucket.site.id
}

resource "local_file" "frontend_ui_website_url" {
  filename = "${path.root}/ui_website_url.txt"
  content  = <<EOF
UI_WEBSITE_URL=http://${aws_s3_bucket_website_configuration.site.website_endpoint}
EOF
}