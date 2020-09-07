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

#----------------------------------
# ALB
#----------------------------------

variable "vpc_id" {
  description = "VPC id, if omit, it will look it up using remote_state"
  type        = string
  default     = ""
}

variable "lb_name" {
  description = "Name of the Load Balancer"
  type        = string
}

variable "lb_tags" {
  description = "A map of tags to add to LoadBalancer"
  type        = map(string)
  default     = {}
}

variable "additional_instance_sg" {
  description = "Some additional Security Group Ids you want to attach to the instance"
  type        = list
  default     = []
}

# optional private_subnets for ALB, 
# if not given, it will look it up in VPC remotestate
variable "private_subnets" {
  description = "Private Subnets for ALB"
  type        = list
  default     = []
}
# optional public_subnets for ALB, 
# if not given, it will look it up in VPC remotestate
variable "public_subnets" {
  description = "Public Subnets for ALB"
  type        = list
  default     = []
}
# optional security_groups for ALB, 
# if not given, it will look it up in VPC remotestate
variable "security_groups" {
  description = "ALB Security Groups"
  type        = list
  default     = []
}

variable "ingress_rules" {
  description = "ALB ingress rules"
  type        = list
  default     = []
}

#-------- Liseners --------------------------
# target_type is either "ip" or "instance"
# target_id is either IP addr or instance_id based on the type above
variable "jenkins_instance" {
  description = "instance object like: { ip: 'x.x.x.x', port: 80 }"
  type        = object({
    match_hosts = list(string),
    port: number,
    target_type: string
    target_id: string
  })
}

variable "jira_instance" {
  description = "instance object like: { ip: 'x.x.x.x', port: 80 }"
  type        = object({
    match_hosts = list(string),
    port: number,
    target_type: string
    target_id: string
  })
}