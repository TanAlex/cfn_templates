resource "aws_route53_zone" "default" {
  name  = "aws.ttan.site"
  tags  = {
      "Name": "zone for aws.ttan.site"
  }
}