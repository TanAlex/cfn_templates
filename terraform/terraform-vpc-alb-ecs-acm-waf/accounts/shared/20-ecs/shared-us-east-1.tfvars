region = "us-east-1"
#assume_role_arn = "arn:aws:iam::152876274589:role/AWSControlTowerExecution"
assume_role_arn = "arn:aws:iam::788562962147:role/onica-sso-OnicaSsoRole-1L47XZZPIVQJ7"
environment = "shared"

#---------------------------------
# keypair SSM
#---------------------------------
keyname = "shared_service_key"
ssm_parameter_publickey = "/secrets/ssh_keys/lab_shared_ssh_pub_key.pub"
ssm_parameter_privatekey = "/secrets/ssh_keys/lab_shared_ssh_pri_key.pem"


#---------------------------------
# ECS
#---------------------------------
ecs_name = "lab-ecs"

# additional security group ids you can attach to the ECS instances
# something like the Bastion VPN security group to allow bastion to access
# Or SG to allow ECS instances to talk to each other
# Or RDS Client Security Group that allows instance to connect to DB
additional_instance_sg = ["sg-071e25085ea35aa13"]

#---------------------------------
# ELB Ingress
#---------------------------------
ingress_rules = [
    [443, 443, "tcp", "Allow HTTPS" ],
    [80, 80, "tcp", "Allow HTTP"]
]