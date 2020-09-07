
data "aws_security_group" "default" {
  name   = "default"
  vpc_id = module.vpc.vpc_id
}

module "vpc" {
  source = "../../../modules/terraform-aws-vpc"

  name = var.vpc_name

  cidr = "10.1.0.0/16"  # 10.0.0.0/8 is reserved for EC2-Classic

  azs                 = ["${var.region}a", "${var.region}b"]
  private_subnets     = var.private_subnets
  public_subnets      = var.public_subnets
  database_subnets    = var.database_subnets
  elasticache_subnets = var.elasticache_subnets


  create_database_subnet_group = var.create_database_subnet_group

  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  enable_classiclink             = var.enable_classiclink
  enable_classiclink_dns_support = var.enable_classiclink_dns_support

  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway

  

  tags = {
    Owner       = var.owner
    Environment = var.environment
  }

  vpc_endpoint_tags = {
    Environment  = var.environment
    Endpoint = "true"
  }
}

