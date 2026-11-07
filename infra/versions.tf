terraform {
  required_version = "~> 1.17"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.72"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.4"
    }
    # Generic REST client for the domainname.shop (Domeneshop) API. The only
    # dedicated provider stopped at 0.1.0 in 2021.
    restapi = {
      source  = "Mastercard/restapi"
      version = "~> 3.0"
    }
  }

  # The bucket, bixority-tfstate-<account ID>, is created once by bootstrap/.
  # Its name carries the account ID, which is kept out of the repository, and a
  # backend block cannot use variables, so it is given at init:
  #   terraform -chdir=infra init -backend-config=bucket=bixority-tfstate-<account ID>
  backend "s3" {
    key          = "website/terraform.tfstate"
    region       = "eu-north-1"
    profile      = "bx"
    use_lockfile = true
    encrypt      = true
  }
}
