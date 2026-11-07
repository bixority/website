# bixority.com

The company website of SIA "Bixority". It is a static site: plain HTML, one CSS
file and a little JavaScript, built by a dependency-free Python script.

The content brief and the decisions behind the site are in
[docs/content-brief.md](docs/content-brief.md). Version 2 ("the drawing set")
follows [docs/v2-research.md](docs/v2-research.md); version 1 is kept as the
git tag `v1`.

## Build and preview

```bash
python3 build.py                 # writes dist/
python3 build.py --strict        # also fails on broken internal links
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
| `src/partials/*.html`        | Sections shared by several pages, included as `{{ partial_<name> }}`: the contact block and `fig-mark.html`, the hero's construction drawing |
| `tools/fig_mark.py`          | Generates `src/partials/fig-mark.html` from the mark's geometry; run it after changing the mark |
| `src/assets/css/site.css`    | All styles; the light and dark themes are colour tokens at the top |
| `src/assets/js/site.js`      | Progressive enhancement only (the copy-email button) |
| `src/assets/fonts/`          | Self-hosted Geist and Geist Mono, Latin and Latin Extended (SIL OFL 1.1) |
| `src/assets/img/`            | Logo, favicons and the share image, generated from `brand/` |
| `brand/`                     | Logo SVGs and the script that generates them (`brand/source/`) |

Pages and layout use `{{ name }}` placeholders. The build stops on a
placeholder it does not know, so typos cannot reach the output.

### What the build does

- Bundles the font and site CSS into one file and fingerprints the CSS and JS
  filenames, so they can be cached for a long time.
- Renders each page into the layout with its canonical URL, `hreflang` links,
  Open Graph tags, navigation state and the link to the other language.
- Adds Organization structured data to the home pages.
- Writes `sitemap.xml` with language alternates, and `robots.txt`.
- Checks every internal link in the output.

### Adding a page

1. Add the page's address to `pages` in `src/site.json`, and add it to `nav`
   if it belongs in the header.
2. Create `src/pages/en/<key>.html` and `src/pages/lv/<key>.html`.

`src/pages/en/404.html` is a single bilingual page. CloudFront should serve
it for missing addresses (custom error response for 403 and 404 → `/404.html`).
It is left out of the sitemap and marked `noindex`.

## Regenerating brand-derived images

The files in `src/assets/img/` are made from the logo SVGs in `brand/`. Run
these from the `v2/` folder; they need `rsvg-convert` and ImageMagick.

```bash
cp brand/bixority-logo-dark-tight.svg src/assets/img/logo.svg
cp brand/bixority-mark.svg src/assets/img/favicon.svg
for s in 16 32 48; do rsvg-convert -w $s -h $s brand/bixority-mark.svg -o /tmp/m$s.png; done
magick /tmp/m16.png /tmp/m32.png /tmp/m48.png src/assets/img/favicon.ico
rsvg-convert -w 132 -h 132 brand/bixority-mark.svg | magick -size 180x180 xc:'#001b35' png:- -gravity center -composite -depth 8 -strip src/assets/img/apple-touch-icon.png
rsvg-convert -w 512 -h 512 brand/bixority-mark.svg -o src/assets/img/mark-512.png
rsvg-convert -w 1000 brand/bixority-logo-dark.svg | magick -size 1200x630 xc:'#001b35' png:- -gravity center -composite -depth 8 -strip src/assets/img/og-image.png
```
