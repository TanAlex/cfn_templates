resource "aws_eip" "service-eip" {
  instance    = "${aws_instance.aws-instance-01.id}"
}
