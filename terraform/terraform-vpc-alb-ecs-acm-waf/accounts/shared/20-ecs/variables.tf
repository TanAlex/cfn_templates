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

#---------------------------------
# keypair SSM
#---------------------------------

variable "keyname" {
  type        = string
  default     = "default_shared_key"
  description = "ssh key name"
}

variable "ssm_parameter_publickey" {
  default = "/secrets/ssh_keys/shared_service.pub"
}

variable "ssm_parameter_privatekey" {
  default = "/secrets/ssh_keys/shared_service.pem"
}

variable "ssm_parameter_type" {
  default = "SecureString"
}

#----------------------------------
# ECS
#----------------------------------

variable "ecs_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "ecs_tags" {
  description = "A map of tags to add to ECS Cluster"
  type        = map(string)
  default     = {}
}

variable "additional_instance_sg" {
  description = "Some additional Security Group Ids you want to attach to the instance"
  type        = list
  default     = []
}

#----------------------------------
# ELB Ingress Rules
#----------------------------------
variable "ingress_rules" {
  description = "A map of tags to add to ECS Cluster"
  type        = list
  default     = []
}

#----------------------------------
# EFS 
#----------------------------------
variable "use_efs" {
  description = "Whether use EFS or not"
  type        = bool
  default     = true
}