resource "aws_lb_target_group" "jenkins80" {
  name                 = "${var.lb_name}-jenkins-port80"
  port                 = 80
  protocol             = "HTTP"
  vpc_id               = local.lookups.vpc_id
  target_type          = var.jenkins_instance.target_type
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
    {Name : "${var.lb_name}-jenkins-port80"}
  )
}

resource "aws_lb_listener" "default80" {
  load_balancer_arn = aws_lb.default.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    target_group_arn = aws_lb_target_group.jenkins80.arn
    type             = "forward"
  }
}

resource "aws_lb_listener" "default443" {
  load_balancer_arn = aws_lb.default.arn

  port            = 443
  protocol        = "HTTPS"
  ssl_policy      = "ELBSecurityPolicy-2016-08"
  certificate_arn = aws_acm_certificate.default.arn

  default_action {
    target_group_arn = aws_lb_target_group.jenkins80.arn
    type             = "forward"
  }
}

resource "aws_lb_listener_rule" "jenkins443" {
  listener_arn = aws_lb_listener.default443.arn
  priority     = 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.jenkins80.arn
  }

  condition {
    field  = "host-header"
    values = var.jenkins_instance.match_hosts
  }

//   condition {
//     field  = "path-pattern"
//     values = var.jenkins_paths
//   }
}

resource "aws_lb_listener_rule" "jenkins80" {
  listener_arn = aws_lb_listener.default80.arn
  priority     = 2

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.jenkins80.arn
  }

  condition {
    field  = "host-header"
    values = var.jenkins_instance.match_hosts
  }

//   condition {
//     field  = "path-pattern"
//     values = var.jenkins_paths
//   }
}

// Associate targe-group with the instance(s)

resource "aws_lb_target_group_attachment" "jenkins80" {
  target_group_arn = aws_lb_target_group.jenkins80.arn
  target_id        = var.jenkins_instance.target_id
  port             = var.jenkins_instance.port
}

