## Creating Launch Configuration
resource "aws_launch_configuration" "example" {
  image_id      = "${data.aws_ami.ubuntu.id}"
  instance_type = "t2.micro"
  key_name      = "${aws_key_pair.my-ssh-key.key_name}"

  security_groups = ["${aws_security_group.ec2.id}"]
  user_data       = <<-EOF
              #!/bin/bash
              HOSTNAME=$(hostname)
              echo "Hello, World<br>Hostname: $HOSTNAME" > index.html
              #echo "Hello, World" > index.html
              nohup busybox httpd -f -p 80 &
              EOF
  lifecycle {
    create_before_destroy = true
  }
}
## Creating AutoScaling Group
resource "aws_autoscaling_group" "example" {
  launch_configuration = "${aws_launch_configuration.example.id}"
  //availability_zones = data.aws_availability_zones.all.names.*
  //availability_zones = ["us-west-2a"]
  vpc_zone_identifier = ["${aws_subnet.public-subnet.id}"]
  min_size = 2
  max_size = 10
  desired_capacity = 3
  force_delete = false
  load_balancers = ["${aws_elb.example.name}"]
  health_check_type = "ELB"
  tag {
    key = "Name"
    value = "terraform-asg-example"
    propagate_at_launch = true
  }
}
