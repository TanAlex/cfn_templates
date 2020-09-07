provider "aws" {
  region = var.region
  assume_role {
    role_arn     = var.assume_role_arn
    session_name = "main_tf_session"
  }
}

data "aws_caller_identity" "current" {}
data "aws_availability_zones" "all" {}