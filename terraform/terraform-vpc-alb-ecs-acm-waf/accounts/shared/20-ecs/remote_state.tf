locals{
  vpc_state_key = "vpc/terraform.tfstate"
  vpc_remote_key_name = (var.workspace == "default")? local.vpc_state_key : "env:/${var.workspace}/${local.vpc_state_key}"
  lookups = {
    private_subnets = data.terraform_remote_state.vpc.outputs.private_subnets
    public_subnets = data.terraform_remote_state.vpc.outputs.public_subnets
    security_groups = data.terraform_remote_state.vpc.outputs.default_security_group_id
    vpc_id = data.terraform_remote_state.vpc.outputs.vpc_id
  }
}

data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket = var.bucket
    key = local.vpc_remote_key_name
    region = var.region
  }
}