output "server-ip" {
  value = "${aws_eip.service-eip.public_ip}"
}
