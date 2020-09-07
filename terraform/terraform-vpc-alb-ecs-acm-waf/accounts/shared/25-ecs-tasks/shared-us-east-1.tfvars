region = "us-east-1"
#assume_role_arn = "arn:aws:iam::152876274589:role/AWSControlTowerExecution"
assume_role_arn = "arn:aws:iam::788562962147:role/onica-sso-OnicaSsoRole-1L47XZZPIVQJ7"
environment = "shared"

#-----------------------------------
# ecs tasks
#-----------------------------------

# if don't provide, it will look it up using remote_state.tf
# ecs_cluster_id = xxx