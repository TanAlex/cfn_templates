locals{
  #------------ Remote State ------------
  vpc_state_key = "vpc/terraform.tfstate"
  vpc_remote_key_name = (var.workspace == "default")? local.vpc_state_key : "env:/${var.workspace}/${local.vpc_state_key}"
  ecs_state_key = "ecs/terraform.tfstate"
  ecs_remote_key_name = (var.workspace == "default")? local.ecs_state_key : "env:/${var.workspace}/${local.ecs_state_key}"
  #------------ Lookup  Vars ------------
  lookups = {
    ecs_cluster_id = (var.ecs_cluster_id == "")? data.terraform_remote_state.ecs.outputs.ecs_cluster_id : var.ecs_cluster_id
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


data "terraform_remote_state" "ecs" {
  backend = "s3"
  config = {
    bucket = var.bucket
    key = local.ecs_remote_key_name
    region = var.region
  }
}