output "backend_s3_bucket_name" {
  value = aws_s3_bucket.terraform_state_bucket.id
}

output "backend_s3_bucket_arn" {
  value = aws_s3_bucket.terraform_state_bucket.arn
}