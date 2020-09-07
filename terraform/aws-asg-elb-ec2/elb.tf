### Creating ELB


resource "aws_elb" "example" {
  name            = "terraform-asg-example"
  security_groups = ["${aws_security_group.elb.id}"]
  //availability_zones = ["${data.aws_availability_zones.all.names}"]
  //has to write like below for Terraform 0.12
  //availability_zones = data.aws_availability_zones.all.names.*

  //Add subnet here to use our VPC
  subnets = ["${aws_subnet.public-subnet.id}"]
  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
    target              = "HTTP:80/"
  }
  listener {
    lb_port           = 80
    lb_protocol       = "http"
    instance_port     = "80"
    instance_protocol = "http"
  }
}
