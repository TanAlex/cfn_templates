region = "us-east-1"
#assume_role_arn = "arn:aws:iam::152876274589:role/AWSControlTowerExecution"
assume_role_arn = "arn:aws:iam::788562962147:role/onica-sso-OnicaSsoRole-1L47XZZPIVQJ7"
environment = "shared"


# VPC Variables

owner = "ttan"
vpc_name = "Main-VPC"
private_subnets     = ["10.1.0.0/21", "10.1.8.0/21"]
public_subnets      = ["10.1.32.0/21", "10.1.40.0/21"]
database_subnets    = ["10.1.96.0/21", "10.1.104.0/21"]
elasticache_subnets = ["10.1.128.0/21", "10.1.136.0/21"]


create_database_subnet_group = true

enable_dns_hostnames = true
enable_dns_support   = true

enable_classiclink             = false
enable_classiclink_dns_support = false

enable_nat_gateway = true
single_nat_gateway = true