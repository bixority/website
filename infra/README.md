# Hosting: S3, CloudFront and domainname.shop

Terraform builds one version of the site (`v4` by default), uploads it to a private S3 bucket and serves it
through CloudFront at `https://www.bixority.com`. DNS stays at domainname.shop
(Domeneshop), and Terraform manages its records through the Domeneshop API.

## What it creates

| File            | Resources |
|-----------------|-----------|
| `site.tf`       | Runs `<version>/build.py --strict` on every plan; one S3 object per file in `<version>/dist/`, with its content type and cache rule; clears the CloudFront cache after any change |
| `storage.tf`    | The bucket `bixority-website-<account>` in eu-north-1: private, readable only by this distribution, TLS only |
| `cdn.tf`        | The certificate for www (ACM, us-east-1, ECDSA P-256); the distribution; the viewer-request function; the security headers |
| `dns.tf`        | At domainname.shop: `www` CNAME to CloudFront, the certificate's validation CNAME, and a forward of the bare domain to `https://www.bixority.com/` |
| `bootstrap/`    | Created once: the state bucket `bixority-tfstate-<account>`, the GitHub OIDC provider and the CI role `bixority-website-ci` (`github.tf`) |

Which version is deployed is set by the variable `site_version`: the name of its folder at the top
of the repository (only `v4` is left; it is the default), for example
`terraform -chdir=infra apply -var site_version=v4`. The host name comes from `base_url` in that
version's `src/site.json`.

**Caching.** `site.<hash>.css` is kept for a year, because
a new version gets a new name. Fonts and images are kept for a week. Pages,
the sitemap and robots.txt are checked by browsers on every visit, and
CloudFront keeps them for a day. Every apply that changes a file clears
CloudFront's copies (an `aws_cloudfront_create_invalidation` action), so the
new version is live as soon as the apply finishes.

**Addresses.** The function in `functions/viewer-request.js` serves
a folder address such as `/lv/` from its `index.html`, redirects `/lv` to `/lv/`,
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
- The AWS profile `bx`, with the permissions in `deployer-policy.json.tftpl`
  (S3 on the two buckets, CloudFront, and ACM in us-east-1). The template takes
  the account ID; after the bootstrap apply,
  `terraform -chdir=infra/bootstrap output -raw deployer_policy` prints it filled in. Creating the CI
  role in `bootstrap/` needs more: IAM roles and OIDC providers. Set
  `aws_profile = null` to use the standard AWS environment variables instead.
- A domainname.shop API token and secret, created at
  <https://www.domeneshop.no/admin?view=api>, in the environment:

  ```bash
  export TF_VAR_domeneshop_token=...   # fish: set -gx TF_VAR_domeneshop_token ...
  export TF_VAR_domeneshop_secret=...
  ```

  These variables are ephemeral: Terraform does not write them to the state or
  to a saved plan. In CI they come from GitHub secrets (see below).

## Continuous integration

The workflow `.github/workflows/ci.yaml` has three jobs.

- **check** runs on pull requests, pushes to `main` and manual runs. It builds `v4`
  with `--strict`, runs its unit tests, runs `node --test 'infra/functions/*.test.mjs'`, checks
  `terraform fmt`, and runs `terraform init -backend=false -lockfile=readonly`
  and `terraform validate` in `infra/` and `infra/bootstrap/`. It needs no secrets.
- **plan** runs after `check` on pull requests from this repository, on
  pushes to `main` and on manual runs on `main`. It runs `terraform plan` against the real state and writes
  the plan to the job summary, so it can be read before anything is approved.
  Pull requests from forks are skipped (no secrets, no OIDC token). Dependabot
  pull requests are skipped by an explicit actor check, which must stay: Dependabot
  runs may raise the token's permissions, so without it a Dependabot pull request could get an
  OIDC token for the deploy role. A manual run on another branch is skipped too: the
  AWS role does not trust that branch. A Dependabot change is planned on `main` after it is
  merged, before the apply is approved. The plan file is not uploaded anywhere.
- **apply** runs only on `main` (a push, or a manual run of the workflow on
  `main`), after `plan`, and only once the owner approves it in the GitHub
  environment `production`. It plans again, shows the plan, and applies that
  saved plan.

A newer push to a pull request cancels that pull request's older plan. A plan
on `main` or an apply that has started is never cancelled; one that is still
waiting is replaced by the newer run. Pull request plans run with `-lock=false`
(a plan never writes state, and a cancelled step would leave the lock behind).
Plans on `main` wait up to 30 minutes for the state lock, the apply up to 10:
its AWS credentials last an hour and are not refreshed, so the apply job is
limited to 55 minutes. If a plan
still fails with "Error acquiring the state lock" while an apply runs, re-run it.

**Secrets.** Add these as repository secrets (Settings, Secrets and variables,
Actions):

| Secret              | Value |
|---------------------|-------|
| `AWS_ACCOUNT_ID`    | The 12-digit AWS account ID |
| `DOMENESHOP_TOKEN`  | domainname.shop API token |
| `DOMENESHOP_SECRET` | domainname.shop API secret |

The workflow passes them as `TF_VAR_domeneshop_token` and
`TF_VAR_domeneshop_secret`. The Domeneshop token cannot be scoped down.
There are no AWS keys in GitHub. The account ID is not a credential, but it is
kept out of the public repository: the workflow builds the role ARN and the
state bucket's name from the secret, and GitHub masks it in logs and job
summaries.

**AWS access.** The plan and apply jobs get AWS credentials through GitHub OIDC.
`aws-actions/configure-aws-credentials` exchanges the job's OIDC token for the
role `bixority-website-ci` and writes the credentials to the profile `bx` on the
runner, which is what the backend and the providers read. The credentials last
at most an hour, and nothing is stored in GitHub.

- The role trusts only tokens from `bixority/website` with one of three
  subjects, and no others. New repositories use immutable subjects that carry the
  owner and repository IDs (`<prefix>` below is
  `repo:bixority@333506/website@<repository ID>`): `<prefix>:pull_request`
  (plans of pull requests from this repository), `<prefix>:ref:refs/heads/main`
  (plans on `main`) and `<prefix>:environment:production` (the apply job, after
  approval). Name-only subjects are not trusted. Check the prefix with
  `gh api repos/bixority/website/actions/oidc/customization/sub --jq .sub_claim_prefix`.
- The role has the permissions in `deployer-policy.json.tftpl`, filled in with
  the account ID by the bootstrap, as an inline policy.
- `infra/bootstrap` creates the OIDC provider and the role (`github.tf`). Apply
  bootstrap again, once, with credentials that may create IAM roles and OIDC
  providers; the deployer policy cannot:

  ```bash
  id=$(gh api repos/bixority/website --jq .id)   # or "id" from https://api.github.com/repos/bixority/website
  terraform -chdir=infra/bootstrap apply -var aws_profile=<admin profile> -var github_repository_id=$id
  ```

  An account can hold only one OIDC provider per URL. If it already has one for
  GitHub, import it before the apply:

  ```bash
  terraform -chdir=infra/bootstrap import -var aws_profile=<admin profile> -var github_repository_id=$id \
    aws_iam_openid_connect_provider.github arn:aws:iam::<account ID>:oidc-provider/token.actions.githubusercontent.com
  ```

- `ci.yaml` builds the role ARN from the secret `AWS_ACCOUNT_ID` and the role
  name, set once as `AWS_ROLE_NAME`.

**One role, one trust boundary.** There is a single role, so pull request plans
get the same deploy-capable credentials as the apply job. The approval gates
only this workflow's apply job. Anyone with write access to the repository can
run code with these credentials before any approval, from a pull request plan
(which runs `infra/build_site.py` and the `vN/build.py` scripts) or from a
workflow on `main`. Keep write access to the owner only.

The repository is public. Pull requests from forks get no secrets and no OIDC
token, so their plan is skipped. GitHub asks for approval before it runs
workflows from first-time outside contributors (the default setting; keep it).

A possible later step: two roles. A read-only plan role (read access, plus write
access to the state lockfile) trusted for `pull_request` and `main`, and the
deploy role trusted only for `environment:production`. Pull request code would
then never hold deploy permissions.

**The `production` environment.** Create it under Settings, Environments, and
add the owner as a required reviewer. The apply job names this environment and
waits for the approval; without protection rules it runs without waiting.
Required reviewers are available on every GitHub plan, including Free, because
the repository is public. Under Deployment branches and tags, allow only `main`.

**Setup order.** GitHub creates a missing environment without protection rules
when a workflow first names it, so configure it before anything can reach apply:
1. Create the repository `bixority/website`, and the `production`
   environment with the required reviewer and `main` as the only branch.
2. Add the secrets `AWS_ACCOUNT_ID`, `DOMENESHOP_TOKEN` and `DOMENESHOP_SECRET`.
3. Apply bootstrap (the role), with the repository ID as above.
4. Push the workflow to `main`.

**Versions.** The Terraform version used by CI is set once, in `ci.yaml`
(`TERRAFORM_VERSION`). Raise it by hand; Dependabot does not. Dependabot
updates the providers (and their lock files) in `infra/` and `infra/bootstrap/`
and the pinned actions, weekly.

## First deployment

1. **Create the state bucket, the GitHub OIDC provider and the CI role.**
   Create the GitHub repository first (see "Setup order"); its ID goes into the
   subjects the role trusts.

   ```bash
   terraform -chdir=infra/bootstrap init
   terraform -chdir=infra/bootstrap apply -var aws_profile=<admin profile> \
     -var github_repository_id=$(gh api repos/bixority/website --jq .id)
   ```

   Its state stays in `infra/bootstrap/terraform.tfstate`, which is not
   committed. The bucket is protected from `terraform destroy`. The apply needs
   a profile that may create IAM roles and OIDC providers (see "AWS access"
   above for the import of an existing provider).

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

3. **Deploy.** The state bucket's name carries the account ID, which is not
   in the repository, so `init` is given it once (Terraform keeps it in
   `infra/.terraform/`):

   ```bash
   account=$(aws sts get-caller-identity --profile bx --query Account --output text)
   terraform -chdir=infra init -backend-config="bucket=bixority-tfstate-$account"
   terraform -chdir=infra apply
   ```

   The first apply waits for the certificate (a few minutes) and for the
   distribution to deploy (up to about 15 minutes).

## Deploying a change

```bash
terraform -chdir=infra apply
```

The plan rebuilds the site and lists exactly which files will be uploaded,
changed or deleted. Run `python3 v4/build.py --strict` first if you only want to
check the build.

## Tests

```bash
node --test 'infra/functions/*.test.mjs'  # the viewer-request function
```
