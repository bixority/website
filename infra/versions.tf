terraform {
  required_version = "~> 1.17"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.72"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.3"
    }
    # Generic REST client for the domainname.shop (Domeneshop) API. The only
    # dedicated provider stopped at 0.1.0 in 2021.
    restapi = {
      source  = "Mastercard/restapi"
      version = "~> 3.0"
    }
  }

  # The bucket is created once by bootstrap/. A backend block cannot use
  # variables, so the account ID is written out here.
  backend "s3" {
    bucket       = "bixority-tfstate-<account ID>"
    key          = "website/terraform.tfstate"
    region       = "eu-north-1"
    profile      = "bx"
    use_lockfile = true
    encrypt      = true
  }
}
