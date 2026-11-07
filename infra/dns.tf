# Records at domainname.shop (Domeneshop), managed through its API. Terraform
# only touches the objects below; mail records (MX, SPF, DKIM, DMARC), the
# Proton verification record and DNSSEC stay as they are.

data "restapi_object" "domain" {
  path         = "/domains"
  query_string = "domain=${local.domain}"
  search_key   = "domain"
  search_value = local.domain
}

locals {
  dns_path      = "/domains/${data.restapi_object.domain.id}/dns"
  forwards_path = "/domains/${data.restapi_object.domain.id}/forwards"
}

# The API stores names relative to the domain and without the final dot.
resource "restapi_object" "www" {
  path = local.dns_path
  data = jsonencode({
    host = trimsuffix(local.www, ".${local.domain}")
    type = "CNAME"
    data = aws_cloudfront_distribution.site.domain_name
    ttl  = 3600
  })
  force_new               = ["host", "type"]
  ignore_server_additions = true
}

resource "restapi_object" "acm_validation" {
  for_each = {
    for option in aws_acm_certificate.www.domain_validation_options : option.domain_name => option
  }

  path = local.dns_path
  data = jsonencode({
    host = trimsuffix(each.value.resource_record_name, ".${local.domain}.")
    type = each.value.resource_record_type
    data = trimsuffix(each.value.resource_record_value, ".")
    ttl  = 3600
  })
  force_new               = ["host", "type"]
  ignore_server_additions = true
}

# The bare domain has no alias record type in this API, so domainname.shop's
# own web forward answers it with a 301 to www. It works over plain HTTP
# only: https://bixority.com does not connect.
resource "restapi_object" "apex_forward" {
  provider = restapi.forwards

  path        = local.forwards_path
  create_path = "${local.forwards_path}/"
  data = jsonencode({
    host  = "@"
    frame = false
    url   = "https://${local.www}/"
  })
  force_new               = ["host"]
  ignore_server_additions = true
}
