resource "aws_lb_target_group" "jira80" {
  name                 = "${var.lb_name}-jira-port80"
  port                 = 80
  protocol             = "HTTP"
  vpc_id               = local.lookups.vpc_id
  target_type          = var.jira_instance.target_type
  deregistration_delay = 15

  health_check {
    path                = "/"
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    matcher             = "200-399"
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(
    var.lb_tags,
    {Name : "${var.lb_name}-jira-port80"}
  )
}


resource "aws_lb_listener_rule" "jira443" {
  listener_arn = aws_lb_listener.default443.arn
  priority     = 11

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.jira80.arn
  }

  condition {
    field  = "host-header"
    values = var.jira_instance.match_hosts
  }

//   condition {
//     field  = "path-pattern"
//     values = var.jenkins_paths
//   }
}

resource "aws_lb_listener_rule" "jira80" {
  listener_arn = aws_lb_listener.default80.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.jira80.arn
  }

  condition {
    field  = "host-header"
    values = var.jira_instance.match_hosts
  }

//   condition {
//     field  = "path-pattern"
//     values = var.jenkins_paths
//   }
}

// Associate targe-group with the instance(s)

resource "aws_lb_target_group_attachment" "jira80" {
  target_group_arn = aws_lb_target_group.jira80.arn
  target_id        = var.jira_instance.target_id
  port             = var.jira_instance.port
}