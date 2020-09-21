terragrunt = {
  terraform {
    source = "git::git@github.com:terraform-aws-modules/terraform-aws-elb.git"
  }

  include = {
    path = "${find_in_parent_folders()}"
  }

  
}

# A health check block
# type: list
health_check = []

# If true, ELB will be an internal ELB
# type: string
internal = ""

# A list of listener blocks
# type: list
listener = []

# The name of the ELB
# type: string
name = "wise-turkey"

# A list of security group IDs to assign to the ELB
# type: list
security_groups = []

# A list of subnet IDs to attach to the ELB
# type: list
subnets = []


