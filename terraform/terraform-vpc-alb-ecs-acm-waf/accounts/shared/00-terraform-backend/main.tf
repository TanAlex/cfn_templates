module "terraform_requirements" {
  source        = "../../../modules/terraform-requirements"
  region = var.region
  #assume_role_arn = "arn:aws:iam::152876274589:role/AWSControlTowerExecution"
  assume_role_arn = var.assume_role_arn
  environment = var.environment
  tf_dynamodb_lock_table_name = var.tf_dynamodb_lock_table_name
  tf_state_bucket_name = var.tf_state_bucket_name
}