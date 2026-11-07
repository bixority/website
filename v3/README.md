# bixority.com

The company website of SIA "Bixority". It is a static site: plain HTML, one CSS
file and a little JavaScript, built by a dependency-free Python script.

The content brief and the decisions behind the site are in
[docs/content-brief.md](docs/content-brief.md). This is version 3, "Keynote":
its principles, tokens and components are in [docs/v3-design.md](docs/v3-design.md).
Versions 1 and 2 are kept as the git tags `v1` and `v2`; the research behind
version 2 is in [docs/v2-research.md](docs/v2-research.md).

## Build and preview

```bash
python3 build.py                 # writes dist/
python3 build.py --strict        # also fails on broken internal links
python3 build.py --out /tmp/site # write somewhere other than dist/ (for parallel builds)
python3 -m http.server 8765 --directory dist   # preview at http://127.0.0.1:8765/
```

Python 3.10 or newer; no packages to install. `dist/` is generated output and
is not committed.

You can also open `dist/index.html` straight from disk. Internal URLs are
written relative to each page, and when a page is opened from disk `site.js`
points directory links (`services/`) at their `index.html`. The 404 page is the
exception: it keeps root-relative URLs because the server shows it at whatever
address was missing, so view it through the local server.

## Layout

| Path                         | What it holds |
|------------------------------|---------------|
| `src/site.json`              | Site address, company details, languages, page addresses, navigation |
| `src/i18n/{en,lv}.json`      | Text of the shared header and footer, per language |
| `src/layout.html`            | The page shell every page is rendered into |
| `src/pages/{en,lv}/*.html`   | One file per page and language: front matter (`title`, `description`, optional `robots: noindex`) then the page body |
| `src/partials/*.html`        | Sections shared by several pages, included as `{{ partial_<name> }}`; today only `mark.html`, the 3D mark |
| `tools/gen_mark.py`          | Generates `src/partials/mark.html` (the lit, extruded mark as inline SVG) from the logo's geometry; run `python3 tools/gen_mark.py` after changing the mark |
| `src/assets/css/*.css`       | `site.css` is the design system (tokens, header, footer, home, inner-page components, print; its top comment documents the components). Add `page-<name>.css` for page-specific rules |
| `src/assets/js/site.js`      | Progressive enhancement only: on `file://` it points directory links (`services/`) at their `index.html`. Nothing else |
| `src/assets/fonts/`          | Self-hosted Geist (Latin and Latin Extended) and Geist Mono (Latin) (SIL OFL 1.1) |
| `src/assets/img/`            | Logos (`logo.svg` for dark grounds, `logo-ink.svg` for light grounds and print), favicons and the share image, generated from `brand/` |
| `brand/`                     | Logo SVGs and the script that generates them (`brand/source/`) |
| `../infra/`                  | Terraform for hosting, at the top of the repository: S3, CloudFront, the certificate and the domainname.shop DNS records; see [../infra/README.md](../infra/README.md) |

Pages and layout use `{{ name }}` placeholders. The build stops on a
placeholder it does not know, so typos cannot reach the output.

### What the build does

- Bundles `fonts.css`, `site.css` and every other `src/assets/css/*.css` (in
  sorted name order) into one stylesheet, and fingerprints the CSS and JS
  filenames, so they can be cached for a long time.
- Renders each page into the layout with its canonical URL, `hreflang` links,
  Open Graph tags, navigation state and a one-word link to the other language
  ("Latviski" or "English", with `lang` and `hreflang`).
- Adds Organization structured data to the home pages.
- Writes `sitemap.xml` with language alternates, and `robots.txt`.
- Checks every internal link in the output.

### Adding a page

1. Add the page's address to `pages` in `src/site.json`, and add it to `nav`
   if it belongs in the header.
2. Create `src/pages/en/<key>.html` and `src/pages/lv/<key>.html`.

`src/pages/en/404.html` is a single bilingual page. CloudFront serves it for
missing addresses (custom error responses for 403 and 404 in `../infra/cdn.tf`).
It is left out of the sitemap and marked `noindex`.

## Regenerating brand-derived images

The files in `src/assets/img/` are made from the logo SVGs in `brand/`. Run
these from the `v3/` folder; they need `rsvg-convert` and ImageMagick.

```bash
cp brand/bixority-logo-dark-tight.svg src/assets/img/logo.svg
cp brand/bixority-logo-ink-tight.svg src/assets/img/logo-ink.svg
cp brand/bixority-mark.svg src/assets/img/favicon.svg
for s in 16 32 48; do rsvg-convert -w $s -h $s brand/bixority-mark.svg -o /tmp/m$s.png; done
magick /tmp/m16.png /tmp/m32.png /tmp/m48.png src/assets/img/favicon.ico
rsvg-convert -w 132 -h 132 brand/bixority-mark.svg | magick -size 180x180 xc:'#001b35' png:- -gravity center -composite -depth 8 -strip src/assets/img/apple-touch-icon.png
rsvg-convert -w 512 -h 512 brand/bixority-mark.svg -o src/assets/img/mark-512.png
rsvg-convert -w 1000 brand/bixority-logo-dark.svg | magick -size 1200x630 xc:'#001b35' png:- -gravity center -composite -depth 8 -strip src/assets/img/og-image.png
```
