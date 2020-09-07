resource "aws_wafregional_geo_match_set" "geo_match_set" {
  name = "geo_match_set"

  geo_match_constraint {
    type  = "Country"
    value = "US"
  }

//   geo_match_constraint {
//     type  = "Country"
//     value = "CA"
//   }
}

resource "aws_wafregional_rule" "geo_match_rule" {
  name        = "GeoMatchBlockNonUS"
  metric_name = "GeoMatchBlockNonUS"

  predicate {
    type    = "GeoMatch"
    data_id = aws_wafregional_geo_match_set.geo_match_set.id
    negated = false
  }
}


resource "aws_wafregional_web_acl" "wafacl" {
  name        = "ALBWafacl"
  metric_name = "ALBWafacl"

  default_action {
    type = "BLOCK"
  }


  rule {
    type     = "REGULAR"
    rule_id  = aws_wafregional_rule.geo_match_rule.id
    priority = 1 

    action {
      type = "ALLOW"
    }
  }


  lifecycle {
    create_before_destroy = true
  }

}

resource "aws_wafregional_web_acl_association" "main" {
  resource_arn = aws_lb.default.arn
  web_acl_id   = aws_wafregional_web_acl.wafacl.id
}