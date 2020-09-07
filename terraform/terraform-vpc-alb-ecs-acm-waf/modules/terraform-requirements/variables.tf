variable "tags" {
  type        = map
  default     = {}
  description = "Terraform resource tags -- useful for metadata and cost tracking"
}

variable "environment" {
  type        = string
  default     = "shared"
  description = "ccount environment name"
}

variable "region" {
  type        = string
  default     = "us-west-1"
  description = "AWS region"
}

variable "lock_table_read_capacity" {
  type        = string
  default     = "1"
  description = "DynamoDB read capacity for the lock table"
}

variable "lock_table_write_capacity" {
  type        = string
  default     = "1"
  description = "DynamoDB write capacity for the lock table"
}

variable "tf_dynamodb_lock_table_name" {
  type        = string
  default     = "lab-dev-tf-state-lock"
  description = "Terraform lock table dynamodb name"
}

variable "tf_state_bucket_name" {
  type        = string
  default     = "lab-dev-tf-remote"
  description = "Terraform state bucket name"
}

variable "assume_role_arn" {
  type        = string
  default     = "arn:aws:iam::123456784589:role/AWSControlTowerExecution"
  description = "arn of the assume role to execute the terrafom"
}