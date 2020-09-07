#-----------------------------------
# Common variables
#-----------------------------------
variable "tags" {
  type        = map(string)
  default     = {}
  description = "Terraform resource tags -- useful for metadata and cost tracking"
}

variable "environment" {
  type        = string
  default     = "sharedsvcs"
  description = "AWS sharedsvcs account environment name"
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

#-----------------------------------
# ecs tasks
#-----------------------------------

variable "ecs_cluster_id" {
  type        = string
  default     = ""
  description = "ECS Cluster Id use to setup the tasks and services"
}