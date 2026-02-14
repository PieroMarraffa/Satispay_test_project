output "api_base_url" {
  value = module.cloud_resources.api_base_url
}

output "website_endpoint" {
  value = try(module.s3_website[0].website_endpoint, null)
}

output "website_url" {
  value = try(module.s3_website[0].website_url, null)
}

output "website_bucket_name" {
  value = try(module.s3_website[0].website_bucket_name, null)
}