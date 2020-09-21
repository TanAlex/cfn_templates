terragrunt = {
  terraform {
    source = "git::git@github.com:terraform-aws-modules/terraform-aws-ec2-instance.git"
  }

  include = {
    path = "${find_in_parent_folders()}"
  }

  
}

# ID of AMI to use for the instance
# type: string
ami = ""

# The type of instance to start
# type: string
instance_type = "m4.large"

# Name to be used on all resources as prefix
# type: string
name = "actual-gannet"

# The VPC Subnet ID to launch in
# type: string
subnet_id = ""

# A list of security group IDs to associate with
# type: list
vpc_security_group_ids = []


