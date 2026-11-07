locals {
  # The deployed version's own configuration is the single source of the host name:
  # base_url "https://www.bixority.com" gives www.bixority.com and bixority.com.
  site   = jsondecode(file("${path.module}/../${var.site_version}/src/site.json"))
  www    = trimprefix(local.site.base_url, "https://")
  domain = trimprefix(local.www, "www.")

  tags = {
    Project   = "bixority-website"
    ManagedBy = "terraform"
  }
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = local.tags
  }
}

# CloudFront only accepts certificates issued in us-east-1.
provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = var.aws_profile

  default_tags {
    tags = local.tags
  }
}

# domainname.shop API, https://api.domeneshop.no/docs/. A new DNS record is
# answered with {"id": N}, which becomes the Terraform ID.
provider "restapi" {
  uri                   = "https://api.domeneshop.no/v0"
  username              = var.domeneshop_token
  password              = var.domeneshop_secret
  id_attribute          = "id"
  create_returns_object = true
  timeout               = 30

  headers = {
    "Content-Type" = "application/json"
  }

  retries {
    max_retries = 3
  }
}

# Forwards have no numeric ID: the API addresses them by host ("@" for the bare
# domain) and answers a create with an empty body.
provider "restapi" {
  alias        = "forwards"
  uri          = "https://api.domeneshop.no/v0"
  username     = var.domeneshop_token
  password     = var.domeneshop_secret
  id_attribute = "host"
  timeout      = 30

  headers = {
    "Content-Type" = "application/json"
  }

  retries {
    max_retries = 3
  }
}
