variable "lambda_integration"{
  type = object({
    lambda_arn = string
    lambda_name = string
    method = string
    route = list(object({
      path = string
      by_id = bool
    }))
  })
}

variable "tags" {
  type = map(string)
}

variable "api_gateway_id" {
  type = string
}

variable "api_gateway_execution_arn" {
  type = string
}