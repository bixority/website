# bixority.com

The company website of SIA "Bixority". The `v4` folder is a complete static
site with its own build script, sources, brand files and notes.

| Folder   | What it holds |
|----------|---------------|
| `v4/`    | Version 4, the current design: one idea per screen, the lit 3D mark spinning as solids on page changes, in CSS only |
| `infra/` | Terraform that builds the site and serves it from S3 and CloudFront at `https://www.bixority.com`; see [infra/README.md](infra/README.md) |

## Build and preview

```bash
python3 v4/build.py --strict                    # writes v4/dist/
python3 -m http.server 8765 --directory v4/dist # preview at http://127.0.0.1:8765/
```

The site is one document per language (`/` and `/lv/`); its pages are `#` sections of it. Python 3.10 or newer; no
packages to install. `v4/README.md` explains its layout, and `v4/docs/` holds the content brief and the design notes.

GitHub Actions (`.github/workflows/ci.yaml`) builds the site, runs its unit tests, tests the CloudFront function and
plans the Terraform changes. Applying them needs the
owner's approval; see [infra/README.md](infra/README.md#continuous-integration).

Versions 1, 2 and 3 were removed from the tree; the commits they were first made in are kept as the tags `v1`, `v2`
and `v3`, and the first hosting commit as `infra`.
