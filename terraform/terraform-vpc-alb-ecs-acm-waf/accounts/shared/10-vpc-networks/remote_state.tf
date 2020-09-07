locals{
  remote_key_name = (var.workspace == "default")? var.key : "env:/${var.workspace}/${var.key}"
}

data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket = var.bucket
    key = local.remote_key_name
    region = var.region
  }
}