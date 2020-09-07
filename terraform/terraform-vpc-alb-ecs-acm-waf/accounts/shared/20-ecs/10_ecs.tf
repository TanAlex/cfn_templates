
locals {
    efs_security_groups = (var.use_efs)? [aws_security_group.elk-efs-securitygroup.id] : []
    user_data = (var.use_efs)? data.template_file.user-data-with-efs.rendered : data.template_file.user_data.rendered
}
resource "aws_ecs_cluster" "this" {
  name = var.ecs_name
  tags = var.ecs_tags
}

# For now we only use the AWS ECS optimized ami 
# <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html>
data "aws_ami" "amazon_linux_ecs" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn-ami-*-amazon-ecs-optimized"]
  }

  filter {
    name   = "owner-alias"
    values = ["amazon"]
  }
}

module "asg" {
  source  = "../../../modules/terraform-aws-autoscaling"
//   version = "~> 3.0"

  name = "${var.ecs_name}-asg-lc"

  # Launch configuration
  lc_name = "${var.ecs_name}-launchconfig"

  image_id             = data.aws_ami.amazon_linux_ecs.id
  instance_type        = "t2.micro"
  security_groups      = concat(
    [aws_security_group.instance_security_group.id],
    local.efs_security_groups,
    var.additional_instance_sg
    )
  iam_instance_profile = aws_iam_instance_profile.this.id
  user_data            = local.user_data
  key_name             = var.keyname

  
  # Auto scaling group
  asg_name                  = "${var.ecs_name}-asg"
  vpc_zone_identifier       = local.lookups.private_subnets
  health_check_type         = "EC2"
  min_size                  = 2
  max_size                  = 2
  desired_capacity          = 2
  wait_for_capacity_timeout = 0

  load_balancers  = [module.elb.this_elb_id]

  tags = [
    {
      key                 = "Environment"
      value               = var.environment
      propagate_at_launch = true
    },
    {
      key                 = "Cluster"
      value               = var.ecs_name
      propagate_at_launch = true
    },
  ]
}

data "template_file" "user_data" {
  template = file("${path.module}/templates/user-data.sh")

  vars = {
    cluster_name = var.ecs_name
  }
}


#--------------------------------
# ELB
#--------------------------------
module "elb" {
  source = "../../../modules/terraform-aws-elb"

  name = "${var.ecs_name}-elb"

  subnets         = local.lookups.public_subnets
  security_groups = [aws_security_group.lb_security_group.id]
  internal        = false

  listener = [
    {
      instance_port     = "80"
      instance_protocol = "HTTP"
      lb_port           = "80"
      lb_protocol       = "HTTP"
    },
  ]

  health_check = {
    target              = "HTTP:80/"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
  }

  tags = {
    Environment = var.environment
  }
}
