# Builds the chosen version (<version>/build.py --strict) whenever Terraform plans,
# so the objects below always match the sources. A broken internal link stops the plan.
data "external" "build" {
  program = ["python3", "${path.module}/build_site.py"]
  query   = { site = var.site_version }
}

locals {
  dist  = data.external.build.result.dist
  files = fileset(local.dist, "**")

  # The text after the last dot, or the whole name when there is none.
  extension = { for f in local.files : f => lower(regex("[^.]*$", f)) }

  content_types = {
    css   = "text/css; charset=utf-8"
    html  = "text/html; charset=utf-8"
    ico   = "image/x-icon"
    js    = "text/javascript; charset=utf-8"
    png   = "image/png"
    svg   = "image/svg+xml"
    txt   = "text/plain; charset=utf-8"
    woff2 = "font/woff2"
    xml   = "application/xml"
  }

  # The bundle's names carry a content hash (site.5145083d23.css), so a new
  # version is a new file and the old one can be kept for a year. Fonts and
  # images keep their names, so they are kept for a week. Pages are checked by
  # browsers on every visit; CloudFront keeps them for a day, and each deploy
  # clears its copies (terraform_data.deploy below).
  cache_control = {
    for f in local.files : f => (
      can(regex("^assets/site\\.[0-9a-f]+\\.(css|js)$", f)) ? "public, max-age=31536000, immutable" :
      startswith(f, "assets/") ? "public, max-age=604800" :
      "public, max-age=0, s-maxage=86400"
    )
  }
}

resource "aws_s3_object" "site" {
  for_each = local.files

  bucket        = aws_s3_bucket.site.id
  key           = each.key
  source        = "${local.dist}/${each.key}"
  source_hash   = filemd5("${local.dist}/${each.key}")
  content_type  = lookup(local.content_types, local.extension[each.key], "application/octet-stream")
  cache_control = local.cache_control[each.key]

  lifecycle {
    precondition {
      condition     = contains(keys(local.content_types), local.extension[each.key])
      error_message = "No content type is set for ${each.key}. Add its extension to local.content_types in site.tf."
    }
  }
}

action "aws_cloudfront_create_invalidation" "site" {
  config {
    distribution_id = aws_cloudfront_distribution.site.id
    paths           = ["/*"]
  }
}

# Changes whenever a file is added, removed or changed, and then clears
# CloudFront's copies so the new version is served at once.
resource "terraform_data" "deploy" {
  input = sha256(jsonencode({
    for key, object in aws_s3_object.site : key => [object.source_hash, object.content_type, object.cache_control]
  }))

  lifecycle {
    action_trigger {
      events  = [after_create, after_update]
      actions = [action.aws_cloudfront_create_invalidation.site]
    }
  }
}
