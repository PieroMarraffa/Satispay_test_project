variable "source_dir" {
    type = string
    description = "The source file for the Lambda function"
}

variable "output_path" {
    type = string
    description = "The output path for the Lambda function"
}

variable "function_name" {
    type = string
    description = "The name of the Lambda function"
}

variable "role_arn" {
    type = string
    description = "The ARN of the IAM role for the Lambda function"
}

variable "environment_variables" {
    type = map(string)
    description = "The environment variables for the Lambda function"
}

variable "tags" {
    type = map(string)
    description = "The tags for the Lambda function"
}