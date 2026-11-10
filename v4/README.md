# bixority.com

The company website of SIA "Bixority". It is a static site: plain HTML, one CSS
file and no JavaScript, built by a dependency-free Python script.

The content brief and the decisions behind the site are in
[docs/content-brief.md](docs/content-brief.md). This is version 4: version 3, "Keynote",
as one document per language, with the page-change animation of the mark. Its principles, tokens and components are in [docs/v4-design.md](docs/v4-design.md).
Versions 1, 2 and 3 are kept as the git tags `v1`, `v2` and `v3`; the research behind
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

The output is two documents, `dist/index.html` (English) and `dist/lv/index.html`
(Latvian), plus `404.html`, `sitemap.xml`, `robots.txt`, `assets/` and `favicon.ico`.
Each document holds every page of its language as a section: Home, then
`#services`, `#open-source`, `#company` and `#privacy`. A page address is a
fragment (`/#services`, `/lv/#company`); there are no per-page files.

You can also open `dist/index.html` straight from disk. Internal URLs are
written relative to each document. The language link points at a folder
(`lv/#services`), and from `file://` a browser shows a folder listing instead of
`lv/index.html`; on the web server it works. The 404 page keeps root-relative URLs
because the server shows it at whatever address was missing, so view it through
the local server.

## Layout

| Path                         | What it holds |
|------------------------------|---------------|
| `src/site.json`              | Site address, company details, languages, page addresses, navigation |
| `src/i18n/{en,lv}.json`      | Text of the shared header and footer, per language |
| `src/layout.html`            | The shell each document is rendered into: head, header, `<main>`, footer, and the shared mark defs at the top of `<body>` |
| `src/pages/{en,lv}/*.html`   | One file per page and language: front matter (`title`, `description`, optional `robots: noindex`) then the page body. In a document the body becomes a section; only the home page's `title` and `description` are used |
| `src/partials/*.html`        | Pieces shared by several pages, included as `{{ partial_<name> }}`: `mark.html` (the 3D mark) and `mark-defs.html` (its gradients, filter and outlines, once per document) |
| `tools/gen_mark.py`          | Generates `src/partials/mark.html` (the lit, extruded mark as inline SVG, plus the hidden solids and shadows the page change uses) and `src/partials/mark-defs.html` from the logo's geometry; run `python3 tools/gen_mark.py` after changing the mark, and put the output of `python3 tools/gen_mark.py --css` in place of the rules marked "generated" in `site.css` |
| `tools/check_pages.py`       | Browser checks of a built `dist/` in Firefox and Chromium (see [Checks](#checks)) |
| `tests/`                     | Unit tests of the build (`unittest`) |
| `src/assets/css/*.css`       | `site.css` is the design system (tokens, header, footer, home, inner-page components, print; its top comment documents the components). Add `page-<name>.css` for page-specific rules |
| `src/assets/fonts/`          | Self-hosted Geist (Latin and Latin Extended) and Geist Mono (Latin) (SIL OFL 1.1) |
| `src/assets/img/`            | Logos (`logo.svg` for dark grounds, `logo-ink.svg` for light grounds and print), favicons and the share image, generated from `brand/` |
| `brand/`                     | Logo SVGs and the script that generates them (`brand/source/`) |
| `../infra/`                  | Terraform for hosting, at the top of the repository: S3, CloudFront, the certificate and the domainname.shop DNS records; see [../infra/README.md](../infra/README.md) |

Pages and layout use `{{ name }}` placeholders. The build stops on a
placeholder it does not know, so typos cannot reach the output.

### What the build does

- Bundles `fonts.css`, `site.css` and every other `src/assets/css/*.css` (in
  sorted name order) into one stylesheet, and fingerprints the CSS
  filename, so it can be cached for a long time. There is no JavaScript.
- Renders every page body, then assembles one document per language: each page is a
  `<section class="pg pg--<key>">` (Home has no `id`; the others have `id="<key>"`), in the
  order of `pages` in `site.json`. Page links become fragments (`#services`; a link to a
  sub-section such as `#development` is the fragment alone).
- An id that occurs on more than one page of a language (`page-title`, `principle`) is
  prefixed with the page key (`services-page-title`) on the pages other than Home, with the
  `aria-labelledby` and `href="#…"` references that point at it. The build fails if any id
  is still repeated in a document.
- Renders the layout once per language with the home page's title, description, canonical URL,
  `hreflang` links and Open Graph tags; the header has one language link per page, each to
  the same page in the other language, and `.mk`, the travelling mark, is the first child of
  `<main>`.
- Adds Organization structured data to the documents.
- Writes `sitemap.xml` with the two documents and their language alternates, and `robots.txt`.
- Checks every internal file link, and that every `href="#id"` has its `id` in the same
  document (`href="#"` is the top).

### Adding a page

1. Add the page's address to `pages` in `src/site.json`, and add it to `nav`
   if it belongs in the header.
2. Create `src/pages/en/<key>.html` and `src/pages/lv/<key>.html`.
3. In `site.css`, add the page to THE DOCUMENT and THE PAGE CHANGE: the keys are written out
   in the `:target` selectors (which section shows, the header underline, the language
   link) and `--n` is the page's number (Home 0, Services 1, Open source 2, Company 3,
   Privacy 4). A page with a mark also needs its place in the `.mk` formulas.

`src/pages/en/404.html` is a single bilingual page. CloudFront serves it for
missing addresses (custom error responses for 403 and 404 in `../infra/cdn.tf`).
It is left out of the sitemap and marked `noindex`.

## Checks

```bash
python3 -m unittest discover -s tests          # build tests; CI runs them
uvx --with playwright python tools/check_pages.py --dist dist
```

`check_pages.py` serves `dist/` locally and checks it in Firefox and Chromium (Playwright's
own browsers must be installed): which section shows for each address, the header underline
and language link, print, that the mark's gradients paint, and the page change (no motion on
load, a change that runs once and ends at rest, the travelling mark handing over to the
resting mark within 1 px, the Privacy fade, reduced motion, a double click, a sub-section
link from another page, a resize between changes). `--engine firefox|chromium|both` and
`--only NAME` narrow a run. The browser checks are not run in CI.

## Regenerating brand-derived images

The files in `src/assets/img/` are made from the logo SVGs in `brand/`. Run
these from the `v4/` folder; they need `rsvg-convert` and ImageMagick.

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
