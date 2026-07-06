variable "environment" {
  type = string
}

variable "account_suffix" {
  type        = string
  description = "Unique suffix for bucket names, e.g. AWS account ID"
}
