# output "server-ip" {
#   value = "${aws_eip.service-eip.public_ip}"
# }

output "aws-instance-01-ip" {
  value = "${aws_instance.aws-instance-01.0.public_ip}"
}

output "aws-instance-02-ip" {
  value = "${aws_instance.aws-instance-02.0.public_ip}"
}