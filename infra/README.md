# Hosting: S3, CloudFront and domainname.shop

Terraform builds one version of the site (`v3` by default), uploads it to a private S3 bucket and serves it
through CloudFront at `https://www.bixority.com`. DNS stays at domainname.shop
(Domeneshop), and Terraform manages its records through the Domeneshop API.

## What it creates

| File            | Resources |
|-----------------|-----------|
| `site.tf`       | Runs `<version>/build.py --strict` on every plan; one S3 object per file in `<version>/dist/`, with its content type and cache rule; clears the CloudFront cache after any change |
| `storage.tf`    | The bucket `bixority-website-<account>` in eu-north-1: private, readable only by this distribution, TLS only |
| `cdn.tf`        | The certificate for www (ACM, us-east-1, ECDSA P-256); the distribution; the viewer-request function; the security headers |
| `dns.tf`        | At domainname.shop: `www` CNAME to CloudFront, the certificate's validation CNAME, and a forward of the bare domain to `https://www.bixority.com/` |
| `bootstrap/`    | The state bucket `bixority-tfstate-<account>`, created once |

Which version is deployed is set by the variable `site_version`: the name of its folder at the top
of the repository (`v1`, `v2` or `v3`; the default is `v3`), for example
`terraform -chdir=infra apply -var site_version=v3`. The host name comes from `base_url` in that
version's `src/site.json`.

**Caching.** `site.<hash>.css` and `site.<hash>.js` are kept for a year, because
a new version gets a new name. Fonts and images are kept for a week. Pages,
the sitemap and robots.txt are checked by browsers on every visit, and
CloudFront keeps them for a day. Every apply that changes a file clears
CloudFront's copies (an `aws_cloudfront_create_invalidation` action), so the
new version is live as soon as the apply finishes.

**Addresses.** The function in `functions/viewer-request.js` serves
`/services/` from `services/index.html`, redirects `/services` to `/services/`,
and redirects any other host name (such as the distribution's own
`*.cloudfront.net` name) to www. A missing page gets `404.html` with status 404.

**Headers.** A strict Content Security Policy (only same-origin scripts,
styles, images and fonts; no forms; no framing), HSTS for two years without
preload, `nosniff`, `X-Frame-Options: DENY`, a strict referrer policy and a
Permissions-Policy. No access logs are written.

**Limits.**

- `https://bixority.com` does not connect. The Domeneshop API has no alias
  record for the bare domain, and its forwards answer only plain HTTP unless the
  domain has Domeneshop web hosting. `http://bixority.com` redirects to
  `https://www.bixority.com/`, and browsers fall back to HTTP when a typed
  address has no HTTPS.
- For the same reason the domain cannot join the HSTS preload list.
- Requests to `http://bixority.com` reach Domeneshop's redirect server, not AWS.

## Requirements

- Terraform 1.17 or newer, and Python 3.10 or newer for the build.
- The AWS profile `bx`, with the permissions in `deployer-policy.json`
  (S3 on the two buckets, CloudFront, and ACM in us-east-1). Set
  `aws_profile = null` to use the standard AWS environment variables instead.
- A domainname.shop API token and secret, created at
  <https://www.domeneshop.no/admin?view=api>, in the environment:

  ```bash
  export TF_VAR_domeneshop_token=...   # fish: set -gx TF_VAR_domeneshop_token ...
  export TF_VAR_domeneshop_secret=...
  ```

  These variables are ephemeral: Terraform does not write them to the state or
  to a saved plan.

## First deployment

1. **Create the state bucket.**

   ```bash
   terraform -chdir=infra/bootstrap init
   terraform -chdir=infra/bootstrap apply
   ```

   Its state stays in `infra/bootstrap/terraform.tfstate`, which is not
   committed. The bucket is protected from `terraform destroy`.

2. **Remove the parking records.** Before the first deployment, `@` and `www`
   answered with domainname.shop's parking server (185.134.245.113 and
   2a01:5b40:0:bc03::1). A or AAAA records for those hosts block the `www` CNAME
   and the forward of the bare domain, so list the records and delete those,
   after checking the IDs:

   ```bash
   auth=(--variable %TF_VAR_domeneshop_token --variable %TF_VAR_domeneshop_secret
         --expand-user '{{TF_VAR_domeneshop_token}}:{{TF_VAR_domeneshop_secret}}')
   api=https://api.domeneshop.no/v0
   curl -s "${auth[@]}" "$api/domains?domain=bixority.com"         # note the "id"
   curl -s "${auth[@]}" "$api/domains/<domain id>/dns"             # find the parking A and AAAA records
   curl -s "${auth[@]}" "$api/domains/<domain id>/forwards/"       # should be empty
   curl -s "${auth[@]}" -X DELETE "$api/domains/<domain id>/dns/<record id>"
   ```

   Leave every other record alone: MX, TXT (SPF, Proton verification,
   DMARC) and the `_domainkey` CNAMEs are the mail setup.

3. **Deploy.**

   ```bash
   terraform -chdir=infra init
   terraform -chdir=infra apply
   ```

   The first apply waits for the certificate (a few minutes) and for the
   distribution to deploy (up to about 15 minutes).

## Deploying a change

```bash
terraform -chdir=infra apply
```

The plan rebuilds the site and lists exactly which files will be uploaded,
changed or deleted. Run `python3 v3/build.py --strict` first if you only want to
check the build.

## Tests

```bash
node --test infra/functions/        # the viewer-request function
```
