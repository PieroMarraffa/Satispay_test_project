variable "role_name"   { 
    type = string 
}

variable "policy_name" { 
    type = string 
}

variable "tags"        { 
    type = map(string)
}

variable "statements" {
  type = list(object({
    sid       = optional(string)
    effect    = string
    actions   = list(string)
    resources = list(string)
    conditions = optional(list(object({
      test     = string
      variable = string
      values   = list(string)
    })), [])
  }))
}