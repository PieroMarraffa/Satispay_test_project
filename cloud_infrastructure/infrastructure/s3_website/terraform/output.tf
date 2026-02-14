output "website_endpoint" {
  value = aws_s3_bucket_website_configuration.site.website_endpoint
}

output "website_url" {
  value = "http://${aws_s3_bucket_website_configuration.site.website_endpoint}"
}

output "website_bucket_name" {
  value = aws_s3_bucket.site.bucket_name
}