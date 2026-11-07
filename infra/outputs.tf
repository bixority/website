output "url" {
  description = "The website."
  value       = "https://${local.www}/"
}

output "bucket" {
  description = "Bucket that holds the built site."
  value       = aws_s3_bucket.site.bucket
}

output "distribution_id" {
  description = "CloudFront distribution ID."
  value       = aws_cloudfront_distribution.site.id
}

output "distribution_domain" {
  description = "CloudFront host name that www points to."
  value       = aws_cloudfront_distribution.site.domain_name
}
