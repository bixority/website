# GitHub Actions access to AWS through OpenID Connect (OIDC). The workflow
# .github/workflows/ci.yaml gets short-lived credentials for one role, so no
# AWS access keys are stored in GitHub.

variable "github_repository" {
  description = "GitHub repository whose workflows may assume the CI role, as owner/name."
  type        = string
  default     = "bixority/website"

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must look like owner/name."
  }
}

variable "github_owner_id" {
  description = "Numeric ID of the GitHub owner (user or organization). The bixority organization is 333506."
  type        = number
  default     = 333506
}

variable "github_repository_id" {
  description = "Numeric ID of the GitHub repository. Read it after creating the repository: gh api repos/bixority/website --jq .id"
  type        = number
}

locals {
  # Repositories created after 2026-07-15 get immutable subjects that carry the owner and
  # repository IDs: repo:OWNER@OWNER-ID/NAME@REPO-ID:... Name-only subjects never match
  # them, and they would also trust a renamed or recreated repository of the same name.
  # Check the prefix before applying:
  #   gh api repos/bixority/website/actions/oidc/customization/sub --jq .sub_claim_prefix
  github_owner = split("/", var.github_repository)[0]
  github_name  = split("/", var.github_repository)[1]
  sub_prefix   = "repo:${local.github_owner}@${var.github_owner_id}/${local.github_name}@${var.github_repository_id}"
}

# An account can hold only one OIDC provider per URL. If this account already has
# one for GitHub, import it instead of creating it:
#   terraform -chdir=infra/bootstrap import aws_iam_openid_connect_provider.github \
#     arn:aws:iam::<account ID>:oidc-provider/token.actions.githubusercontent.com
# The thumbprint list is optional: AWS verifies GitHub's certificate chain itself.
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# Only tokens issued for this repository and one of three subjects can assume the role:
#   pull_request:           plan jobs of pull requests from this repository
#   ref:refs/heads/main:    plan jobs on pushes to main and manual runs on main
#   environment:production: the apply job, after the owner approves it
# No wildcards. Pull requests from forks get no OIDC token.
data "aws_iam_policy_document" "ci_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "${local.sub_prefix}:pull_request",
        "${local.sub_prefix}:ref:refs/heads/main",
        "${local.sub_prefix}:environment:production",
      ]
    }
  }
}

resource "aws_iam_role" "ci" {
  name                 = "bixority-website-ci"
  description          = "Assumed by the GitHub Actions workflow of ${var.github_repository} to plan and apply infra/."
  assume_role_policy   = data.aws_iam_policy_document.ci_trust.json
  max_session_duration = 3600
}

# The permissions live in one file, shared with the manual deployer setup.
resource "aws_iam_role_policy" "ci" {
  name   = "deployer"
  role   = aws_iam_role.ci.id
  policy = file("${path.module}/../deployer-policy.json")
}

output "ci_role_arn" {
  description = "Role ARN for role-to-assume in .github/workflows/ci.yaml."
  value       = aws_iam_role.ci.arn
}
