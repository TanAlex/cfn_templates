region = "us-east-1"
#assume_role_arn = "arn:aws:iam::152876274589:role/AWSControlTowerExecution"
assume_role_arn = "arn:aws:iam::788562962147:role/onica-sso-OnicaSsoRole-1L47XZZPIVQJ7"
environment = "shared"

#---------------------------------
# ALB
#---------------------------------
lb_name = "lab-alb"
lb_tags = {
    "Environment" : "shared"
}
# additional security group ids you can attach to the ECS instances
# something like the Bastion VPN security group to allow bastion to access
# Or SG to allow ECS instances to talk to each other
# Or RDS Client Security Group that allows instance to connect to DB
additional_instance_sg = ["sg-071e25085ea35aa13"]

#---------------------------------
# LB Ingress
#---------------------------------
ingress_rules = [
    [443, 443, "tcp", "Allow HTTPS" ],
    [80, 80, "tcp", "Allow HTTP"]
]

jenkins_instance = {
    match_hosts: ["jenkins.aws.ttan.site"]
    port: 80,
    target_type: "instance",
    target_id: "i-0ae872412dbc272a4"
}


jira_instance = {
    match_hosts: ["jira.aws.ttan.site"]
    port: 80,
    target_type: "instance",
    target_id: "i-0f88e5e593c889e57"
}