variable "site_version" {
  description = "The version of the site to build and deploy: its folder at the top of the repository (v4)."
  type        = string
  default     = "v4"

  validation {
    condition     = can(regex("^v[0-9]+$", var.site_version)) && fileexists("${path.module}/../${var.site_version}/build.py")
    error_message = "site_version must name a version folder with a build.py, such as \"v4\"."
  }
}

variable "aws_profile" {
  description = "AWS CLI profile to deploy with. Set it to null to use the standard AWS environment variables instead."
  type        = string
  default     = "bx"
}

variable "region" {
  description = "Region of the website bucket. CloudFront serves it worldwide, so this only decides where the files are stored."
  type        = string
  default     = "eu-north-1"
}

# API credentials from https://www.domeneshop.no/admin?view=api, passed as
# TF_VAR_domeneshop_token and TF_VAR_domeneshop_secret. They are ephemeral:
# Terraform never writes them to the state or to a saved plan.
variable "domeneshop_token" {
  description = "domainname.shop API token (the HTTP Basic user name)."
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "domeneshop_secret" {
  description = "domainname.shop API secret (the HTTP Basic password)."
  type        = string
  sensitive   = true
  ephemeral   = true
}
