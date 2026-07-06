variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "subnet_id_b" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}
