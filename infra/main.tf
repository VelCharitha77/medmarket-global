terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "networking" {
  source      = "./modules/networking"
  aws_region  = var.aws_region
  environment = var.environment
}

module "storage" {
  source         = "./modules/storage"
  environment    = var.environment
  account_suffix = "373700524836"
}



variable "db_password" {
  type      = string
  sensitive = true
}

module "warehouse" {
  source      = "./modules/warehouse"
  environment = var.environment
  vpc_id      = module.networking.vpc_id
  subnet_id   = module.networking.subnet_id
  subnet_id_b = module.networking.subnet_id_b
  db_password = var.db_password
}

module "iam" {
  source      = "./modules/iam"
  environment = var.environment
  account_id  = "373700524836"
}

module "secrets" {
  source      = "./modules/secrets"
  environment = var.environment
}
