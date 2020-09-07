#-----------------------------------------
# Load Balancer Security Group
#-----------------------------------------
resource "aws_security_group" "lb_security_group" {
  name_prefix = "${var.lb_name}-lb-sg"
  description = "Security Group for Load Balancer"
  vpc_id      = local.lookups.vpc_id

  tags = merge(
    var.tags,
    {
      "Name" = "${var.lb_name}-lb-security-group"
    },
  )

  lifecycle {
    create_before_destroy = true
  }
}


resource "aws_security_group_rule" "lb_ingress_rules" {
  count = length(var.ingress_rules)
  security_group_id = aws_security_group.lb_security_group.id
  type              = "ingress"

  cidr_blocks      = ["0.0.0.0/0"]
  #ipv6_cidr_blocks = var.ingress_ipv6_cidr_blocks
  #prefix_list_ids  = var.ingress_prefix_list_ids
  description      = var.ingress_rules[count.index][3]

  from_port = var.ingress_rules[count.index][0]
  to_port   = var.ingress_rules[count.index][1]
  protocol  = var.ingress_rules[count.index][2]
}

resource "aws_security_group_rule" "lb_egress_rules" {
  security_group_id = aws_security_group.lb_security_group.id
  type              = "egress"

  cidr_blocks      = ["0.0.0.0/0"]
  #ipv6_cidr_blocks = var.ingress_ipv6_cidr_blocks
  #prefix_list_ids  = var.ingress_prefix_list_ids
  description      = "All Traffic"

  from_port = -1
  to_port   = -1
  protocol  = -1
}

#-----------------------------------------
# Instance Security Group
#-----------------------------------------
resource "aws_security_group" "instance_security_group" {
  name_prefix = "${var.lb_name}-instant-sg"
  description = "Security Group for instances behind ELB"
  vpc_id      = local.lookups.vpc_id

  tags = merge(
    var.tags,
    {
      "Name" = "${var.lb_name}-instance-security-group"
    },
  )

  lifecycle {
    create_before_destroy = true
  }
}


resource "aws_security_group_rule" "instance_ingress_rules" {
  count = length(var.ingress_rules)
  security_group_id = aws_security_group.instance_security_group.id
  type              = "ingress"
  source_security_group_id = aws_security_group.lb_security_group.id
  #cidr_blocks      = "0.0.0.0/0"
  #ipv6_cidr_blocks = var.ingress_ipv6_cidr_blocks
  #prefix_list_ids  = var.ingress_prefix_list_ids
  description      = var.ingress_rules[count.index][3]

  from_port = var.ingress_rules[count.index][0]
  to_port   = var.ingress_rules[count.index][1]
  protocol  = var.ingress_rules[count.index][2]
}

resource "aws_security_group_rule" "allow_all_among_us" {
  security_group_id = aws_security_group.instance_security_group.id
  type              = "ingress"
  source_security_group_id = aws_security_group.instance_security_group.id
  #cidr_blocks      = "0.0.0.0/0"
  #ipv6_cidr_blocks = var.ingress_ipv6_cidr_blocks
  #prefix_list_ids  = var.ingress_prefix_list_ids
  description      = "Allow All among our intances"

  from_port = -1
  to_port   = -1
  protocol  = -1
}

resource "aws_security_group_rule" "instance_egress_rules" {
  security_group_id = aws_security_group.instance_security_group.id
  type              = "egress"

  cidr_blocks      = ["0.0.0.0/0"]
  #ipv6_cidr_blocks = var.ingress_ipv6_cidr_blocks
  #prefix_list_ids  = var.ingress_prefix_list_ids
  description      = "All Traffic"

  from_port = -1
  to_port   = -1
  protocol  = -1
}