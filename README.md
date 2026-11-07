# bixority.com

The company website of SIA "Bixority", in three versions side by side. Each
version folder is a complete static site with its own build script, sources,
brand files and notes; nothing is shared between them.

| Folder   | What it holds |
|----------|---------------|
| `v1/`    | Version 1: navy brand bands, chamfered lime buttons, IBM Plex |
| `v2/`    | Version 2, "the drawing set": the mark's construction drawing as the hero, Geist and Geist Mono |
| `v3/`    | Version 3, "Keynote", the current design: one idea per screen, the lit 3D mark |
| `infra/` | Terraform that builds one version (`v3` by default) and serves it from S3 and CloudFront at `https://www.bixority.com`; see [infra/README.md](infra/README.md) |

## Build and preview a version

```bash
python3 v3/build.py --strict                    # writes v3/dist/
python3 -m http.server 8765 --directory v3/dist # preview at http://127.0.0.1:8765/
```

The same works for `v1` and `v2`. Python 3.10 or newer; no packages to
install. Each version's `README.md` explains its layout, and its `docs/` holds
the content brief and the design notes.

The commits each version was first made in are kept as the tags `v1`, `v2` and
`v3`, and the first hosting commit as `infra`.
