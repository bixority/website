# bixority.com

The company website of SIA "Bixority", in four versions side by side. Each
version folder is a complete static site with its own build script, sources,
brand files and notes; nothing is shared between them.

| Folder   | What it holds |
|----------|---------------|
| `v1/`    | Version 1: navy brand bands, chamfered lime buttons, IBM Plex |
| `v2/`    | Version 2, "the drawing set": the mark's construction drawing as the hero, Geist and Geist Mono |
| `v3/`    | Version 3, "Keynote": one idea per screen, the lit 3D mark |
| `v4/`    | Version 4, the current design: version 3 with the mark spinning as solids on page changes |
| `infra/` | Terraform that builds one version (`v4` by default) and serves it from S3 and CloudFront at `https://www.bixority.com`; see [infra/README.md](infra/README.md) |

## Build and preview a version

```bash
python3 v4/build.py --strict                    # writes v4/dist/
python3 -m http.server 8765 --directory v4/dist # preview at http://127.0.0.1:8765/
```

The same works for `v1`, `v2` and `v3`. Python 3.10 or newer; no packages to
install. Each version's `README.md` explains its layout, and its `docs/` holds
the content brief and the design notes.

GitHub Actions (`.github/workflows/ci.yaml`) builds all four versions, tests
the CloudFront function and plans the Terraform changes. Applying them needs the
owner's approval; see [infra/README.md](infra/README.md#continuous-integration).

The commits each version was first made in are kept as the tags `v1`, `v2` and
`v3`, and the first hosting commit as `infra`.
