variable "tags" {
  type        = map(string)
  default     = {}
  description = "Terraform resource tags -- useful for metadata and cost tracking"
}

variable "environment" {
  type        = string
  default     = "shared"
  description = "AWS environment name"
}

variable "region" {
  type        = string
  default     = "ca-central-1"
  description = "AWS region"
}

variable "assume_role_arn" {
  type        = string
  default     = "arn:aws:iam::123456784589:role/AWSControlTowerExecution"
  description = "arn of the assume role to execute the terrafom"
}

variable "dynamodb_table" {
  type        = string
  default     = "lab-dev-tf-state-lock"
  description = "Terraform lock table dynamodb name"
}

variable "bucket" {
  type        = string
  default     = "lab-dev-tf-remote"
  description = "Terraform state bucket name"
}

variable "key" {
  type        = string
  default     = "default/terraform.tfstate"
  description = "Terraform state bucket key name"
}

variable "workspace" {
  type        = string
  default     = "default"
  description = "Terraform workspace"
}

#--------------------------------------------
#  VPC
#--------------------------------------------
variable "vpc_name" {
  type        = string
  default     = "Main-VPC"
  description = "VPC Name"
}

variable "owner" {
  type        = string
  default     = ""
  description = "Owner name"
}

variable "private_subnets" {
  type        = list
  default     = []
  description = "private subnets list"
}

variable "public_subnets" {
  type        = list
  default     = []
  description = "public subnets list"
}

variable "database_subnets" {
  type        = list
  default     = []
  description = "database_subnets subnets list"
}

variable "elasticache_subnets" {
  type        = list
  default     = []
  description = "elasticache_subnets subnets list"
}

variable "create_database_subnet_group" {
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  type        = bool
  default     = true
}

variable "enable_classiclink" {
  type        = bool
  default     = true
}
variable "enable_classiclink_dns_support" {
  type        = bool
  default     = true
}
variable "enable_nat_gateway" {
  type        = bool
  default     = true
}
variable "single_nat_gateway" {
  type        = bool
  default     = true
}