resource "aws_acm_certificate" "default" {
  domain_name               = "*.aws.ttan.site"
  validation_method         = "DNS"
  subject_alternative_names = []
  tags                      = {
      "Name": "Cert for aws.ttan.site"
  }

  lifecycle {
    create_before_destroy = true
  }
}

locals {
  zone_name                         = aws_route53_zone.default.name
  domain_validation_options_list    = aws_acm_certificate.default.domain_validation_options
}


resource "aws_route53_record" "default" {
  zone_id         = aws_route53_zone.default.zone_id
  ttl             = 60
  allow_overwrite = true
  name            = lookup(local.domain_validation_options_list[0], "resource_record_name")
  type            = lookup(local.domain_validation_options_list[0], "resource_record_type")
  records         = [lookup(local.domain_validation_options_list[0], "resource_record_value")]
}



// resource "aws_acm_certificate_validation" "default" {
//   certificate_arn         = aws_acm_certificate.default.arn
//   validation_record_fqdns = ["*.aws.ttan.site"]
// }
