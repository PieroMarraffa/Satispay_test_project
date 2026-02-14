variable "tags" {
  description = "A map of tags to assign to all resources"
  type        = map(string)
}

variable "s3_website_uri" {
  description = "The URI of the S3 website"
  type        = string
  default     = null
}

variable "test_via_ui" {
  description = "Whether to deploy the S3 website for testing via UI"
  type        = bool
  default     = false
}