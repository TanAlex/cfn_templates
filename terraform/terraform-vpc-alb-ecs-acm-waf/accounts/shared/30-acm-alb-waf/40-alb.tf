
resource "aws_lb" "default" {
  name               = var.lb_name
  tags               = var.lb_tags
  internal           = false
  load_balancer_type = "application"

  security_groups = compact(
    concat(var.additional_instance_sg, [aws_security_group.lb_security_group.id]),
  )

  subnets                          = local.lookups.public_subnets
  enable_cross_zone_load_balancing = true
  enable_http2                     = true
  idle_timeout                     = 60
  ip_address_type                  = "ipv4"
  enable_deletion_protection       = false

//   access_logs {
//     bucket  = module.access_logs.bucket_id
//     prefix  = var.access_logs_prefix
//     enabled = var.access_logs_enabled
//   }
}

resource "aws_route53_record" "star" {
  zone_id = aws_route53_zone.default.zone_id
  name    = "*"
  type    = "A"

  alias {
    name                   = aws_lb.default.dns_name
    zone_id                = aws_lb.default.zone_id
    evaluate_target_health = false
  }
}

// resource "aws_lb_target_group" "default" {
//   name                 = "${var.lb_name}-tg4inst-1-port80"
//   port                 = 80
//   protocol             = "HTTP"
//   vpc_id               = local.lookups.vpc_id
//   target_type          = "ip"
//   deregistration_delay = 15

//   health_check {
//     path                = "/"
//     timeout             = 10
//     healthy_threshold   = 2
//     unhealthy_threshold = 2
//     interval            = 15
//     matcher             = "200-399"
//   }

//   lifecycle {
//     create_before_destroy = true
//   }

//   tags = merge(
//     var.lb_tags,
//     [{Name : "${var.lb_name}-tg4inst-1-port80"}]
//   )
// }

// resource "aws_lb_listener" "http" {
//   load_balancer_arn = aws_lb.default.arn
//   port              = 80
//   protocol          = "HTTP"

//   default_action {
//     target_group_arn = aws_lb_target_group.default.arn
//     type             = "forward"
//   }
// }

// resource "aws_lb_listener" "https" {
//   load_balancer_arn = aws_lb.default.arn

//   port            = 443
//   protocol        = "HTTPS"
//   ssl_policy      = var.https_ssl_policy
//   certificate_arn = var.certificate_arn

//   default_action {
//     target_group_arn = aws_lb_target_group.default.arn
//     type             = "forward"
//   }
// }
