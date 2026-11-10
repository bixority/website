#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10,<3.15"
# dependencies = ["minify-html==0.18.1"]
# ///
"""Build the static site from src/ into dist/. One dependency: minify-html (uv installs it).

    uv run build.py                    # build, minify HTML and CSS, warn about links to pages that don't exist yet
    uv run build.py --strict           # build, fail on any broken internal link
    uv run build.py --no-minify        # readable HTML and CSS, for debugging
    uv run build.py --out /tmp/site    # write somewhere else than dist/ (parallel builds)
"""
import argparse
import hashlib
import html
import json
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent
BUILD_MARKER = ".bixority-build"
SRC = ROOT / "src"
PLACEHOLDER = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")
# Context values that are HTML already and must not be escaped.
RAW = {"alternates", "nav", "lang_switch", "content", "jsonld", "robots", "canonical_link"}
RAW_PREFIXES = ("partial_",)


def fail(msg) -> NoReturn:
    sys.exit(f"build: {msg}")


def render(text, ctx, where):
    def sub(m):
        key = m.group(1)
        if key not in ctx:
            fail(f"{where}: unknown placeholder {{{{ {key} }}}}")
        value = str(ctx[key])
        return value if key in RAW or key.startswith(RAW_PREFIXES) else html.escape(value, quote=True)
    return PLACEHOLDER.sub(sub, text)


def read_page(path):
    """A page is optional front matter between '---' lines, then an HTML body."""
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---\n"):
        head, sep, body = text[4:].partition("\n---\n")
        if not sep:
            fail(f"{path}: front matter is not closed with '---'")
        for line in head.splitlines():
            if line.strip():
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
    for key in ("title", "description"):
        if not meta.get(key):
            fail(f"{path}: front matter needs '{key}'")
    return meta, body


ROOT_RELATIVE = re.compile(r'(href|src)="/(?!/)([^"]*)"')


def relativize(page_html, page_path):
    """Rewrite root-relative URLs to be relative to the page, so dist/ also
    works when opened straight from disk (file://). page_path is the output
    file relative to dist/, such as 'lv/index.html'."""
    base = posixpath.dirname(page_path) or "."

    def sub(m):
        attr, target = m.group(1), m.group(2)
        path, sep, frag = target.partition("#")
        rel = posixpath.relpath(path.rstrip("/") or ".", base)
        if path == "" or path.endswith("/"):
            rel = "./" if rel == "." else rel + "/"
        return f'{attr}="{rel}{sep}{frag}"'
    return ROOT_RELATIVE.sub(sub, page_html)


def fingerprinted(data, stem, suffix):
    digest = hashlib.sha256(data).hexdigest()[:10]
    return f"{stem}.{digest}{suffix}"


def load_minifier():
    try:
        import minify_html
    except ImportError:
        fail("minify-html is not installed; run `uv run build.py` (or pass --no-minify)")
    return minify_html


def minify_css(css, minify_html):
    wrapped = minify_html.minify(f"<style>{css}</style>", minify_css=True)
    if not (wrapped.startswith("<style>") and wrapped.endswith("</style>")):
        fail("minify-html changed the shape of the CSS wrapper")
    return wrapped[len("<style>"):-len("</style>")]


def minify_page(page_html, minify_html):
    # The doctype, closing tags and <html>/<head> stay; JS is left alone (JSON-LD is JSON).
    return minify_html.minify(page_html, minify_css=True, minify_js=False,
                              keep_closing_tags=True, keep_html_and_head_opening_tags=True)


def build_assets(dist, minifier=None):
    """Copy static assets; bundle and fingerprint the CSS. Returns its URL."""
    assets = dist / "assets"
    shutil.copytree(SRC / "assets" / "img", assets / "img")
    fonts = assets / "fonts"
    fonts.mkdir(parents=True)
    for f in (SRC / "assets" / "fonts").iterdir():
        if f.suffix in (".woff2", ".txt"):
            shutil.copy2(f, fonts / f.name)
    shutil.copy2(SRC / "assets" / "img" / "favicon.ico", dist / "favicon.ico")

    font_css = (SRC / "assets" / "fonts" / "fonts.css").read_text(encoding="utf-8")
    font_css = re.sub(r"url\('([^'/]+\.woff2)'\)", r"url('fonts/\1')", font_css)
    # fonts, then site.css, then every other stylesheet in sorted name order (page-<name>.css)
    sheets = [SRC / "assets" / "css" / "site.css"]
    sheets += sorted(p for p in (SRC / "assets" / "css").glob("*.css") if p.name != "site.css")
    css = "\n".join([font_css, *(p.read_text(encoding="utf-8") for p in sheets)])
    if minifier:
        css = minify_css(css, minifier)  # before the hash: the name is of the bytes served
    css = css.encode()
    css_name = fingerprinted(css, "site", ".css")
    (assets / css_name).write_bytes(css)

    return f"/assets/{css_name}"


# What the company works with, for search engines (schema.org knowsAbout): the Services page's own terms.
KNOWS_ABOUT = ["DevOps", "Site reliability engineering", "Kubernetes", "Infrastructure as code", "CI/CD",
               "Observability", "PostgreSQL", "Rust", "Python", "TypeScript", "Software development"]


def org_jsonld(site, lang, description, here):
    """The company (an Organization that is also a ProfessionalService) and this language's website."""
    c, base = site["company"], site["base_url"]
    org_id = base + "/#organization"
    logo = base + "/assets/img/mark-512.png"
    org = {
        "@type": ["Organization", "ProfessionalService"],
        "@id": org_id,
        "name": site["brand"],
        "legalName": c["legal_name"],
        "description": description,
        "url": base + "/",
        "logo": logo,
        "image": logo,
        "email": site["email"],
        "foundingDate": site["founded"],
        "vatID": c["vat"],
        "identifier": c["reg_no"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": c["street"],
            "addressLocality": c["city"],
            "postalCode": c["postal"],
            "addressCountry": c["country_code"],
        },
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "email": site["email"],
            "availableLanguage": ["English", "Latvian"],
        },
        "knowsAbout": KNOWS_ABOUT,
        "sameAs": site["profiles"],
    }
    website = {
        "@type": "WebSite",
        "@id": base + here + "#website",
        "url": base + here,
        "name": site["brand"],
        "inLanguage": lang["code"],
        "publisher": {"@id": org_id},
    }
    data = {"@context": "https://schema.org", "@graph": [org, website]}
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'  <script type="application/ld+json">\n{body}\n  </script>'


def last_changed():
    """The date (YYYY-MM-DD) of the last commit that changed the site's sources, for the sitemap's lastmod.
    None outside a git checkout, or when git is missing; then the sitemap has no lastmod."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", "src", "build.py"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out if re.fullmatch(r"\d{4}-\d{2}-\d{2}", out) else None


def parse_args(argv):
    ap = argparse.ArgumentParser(description="Build the static site from src/.")
    ap.add_argument("--strict", action="store_true", help="fail on any broken internal link")
    ap.add_argument("--out", type=Path, default=ROOT / "dist", metavar="DIR", help="output directory (default: dist/)")
    ap.add_argument("--no-minify", action="store_true", help="keep the HTML and CSS readable")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    strict = args.strict
    dist = args.out.resolve()
    if dist == ROOT or dist in ROOT.parents:
        fail(f"refusing to use {dist} as the output directory")
    if ROOT in dist.parents and dist != ROOT / "dist":
        fail(f"refusing to use {dist}: inside the repository, only dist/ may be the output directory")
    site = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
    langs = site["languages"]
    strings = {lg["code"]: json.loads((SRC / "i18n" / f"{lg['code']}.json").read_text(encoding="utf-8")) for lg in langs}
    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    # Shared page sections, used in pages as {{ partial_<name> }}.
    partials = {p.stem: p.read_text(encoding="utf-8") for p in sorted((SRC / "partials").glob("*.html"))}
    base = site["base_url"]

    if dist.exists():
        # Only ever delete a previous build, never a directory that merely exists.
        if dist != ROOT / "dist" and not (dist / BUILD_MARKER).is_file() and any(dist.iterdir()):
            fail(f"refusing to overwrite {dist}: it is not empty and is not a previous build (no {BUILD_MARKER})")
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    minifier = None if args.no_minify else load_minifier()
    if dist != ROOT / "dist":
        # dist/ is always ours to replace; other outputs carry a marker, and dist/ is
        # what gets deployed, so the marker never ships with the site
        (dist / BUILD_MARKER).write_text("Output of build.py; it may be deleted and rebuilt.\n", encoding="utf-8")
    css_url = build_assets(dist, minifier)

    def url_of(lang, key):
        if key == "404":
            return f"{lang['prefix']}/404.html"
        return lang["prefix"] + site["pages"][key]

    def frag_of(lang, key):
        """Root-relative address of a page's section: '/#services', '/lv/#services'; Home is '/' or '/lv/'."""
        return lang["prefix"] + "/" + ("" if key == "index" else f"#{key}")

    # Which pages exist in which language.
    pages = {}
    for lang in langs:
        for path in sorted((SRC / "pages" / lang["code"]).glob("*.html")):
            key = path.stem
            if key != "404" and key not in site["pages"]:
                fail(f"{path}: page '{key}' is not listed in site.json")
            pages.setdefault(key, {})[lang["code"]] = path
    order = [k for k in site["pages"] if k in pages]  # the order of the sections in a document
    if "index" not in pages:
        fail("there is no index page")

    c = site["company"]

    def make_ctx(lang, meta, here, link):
        """The placeholders of one language; link(page_key) gives the address of a page."""
        t = strings[lang["code"]]
        others = [lg for lg in langs if lg is not lang]
        ctx = {
            "lang": lang["code"],
            "title": meta["title"],
            "description": meta["description"],
            "robots": '  <meta name="robots" content="noindex">' if meta.get("robots") == "noindex" else "",
            "canonical": base + here,
            "og_locale": lang["locale"],
            "og_locale_alt": ", ".join(lg["locale"] for lg in others),
            "base_url": base,
            "css": css_url,
            "skip": t["skip"],
            "home_url": link("index"),
            "home_link": t["home_link"],
            "nav_label": t["nav_label"],
            "privacy_url": link("privacy"),
            "email": site["email"],
            "legal_name": c["legal_name"],
            "legal_display": c["legal_display"],
            "reg_no": c["reg_no"],
            "vat": c["vat"],
            "street": c["street"],
            "street_nbsp": c["street"].replace(" - ", "\u00a0-\u00a0"),
            "city": c["city"],
            "postal": c["postal"],
        }
        for k, v in t["footer"].items():
            ctx["f_" + k] = v
        for k in site["pages"]:
            ctx["url_" + k.replace("-", "_")] = link(k)
        for name, text in partials.items():
            ctx["partial_" + name] = render(text, ctx, f"partials/{name}.html")
        return ctx

    def cls(item):
        return f' class="hd__link hd__link--{item}"'

    def nav_html(lang, link, doc):
        t = strings[lang["code"]]
        return "\n".join(
            f'      <li><a{cls(item) if doc else ""} href="{link(item)}">'
            f'{html.escape(t["nav"][item])}</a></li>' for item in site["nav"])

    def switch_html(lang, keys, doc):
        """One word, in the other language: the only language control. In a document there is one link
        per page (the page that is open shows its own), each to the same page in the other language."""
        out = []
        for other in langs:
            if other is lang:
                continue
            for key in keys:
                has = other["code"] in pages.get(key, {})
                target = frag_of(other, key) if has else frag_of(other, "index")
                cls = f"hd__lang hd__lang--{key}" if doc else "hd__lang"
                out.append(f'<a class="{cls}" href="{target}" hreflang="{other["code"]}" lang="{other["code"]}">'
                           f'{html.escape(other["name"])}</a>')
        return " ".join(out)

    written = []
    sitemap = []
    for lang in langs:
        code = lang["code"]
        siblings = [lg for lg in langs if lg["code"] in pages["index"]]
        # --- the document: every page of this language as a section, in one HTML file ---
        keys = [k for k in order if code in pages[k]]
        parsed = {k: read_page(pages[k][code]) for k in keys}
        home_meta, here = parsed["index"][0], url_of(lang, "index")

        def link(key, lang=lang):
            return "#" if key == "index" else f"#{key}"

        ctx = make_ctx(lang, home_meta, here, link)
        # a link to a sub-section of a page ("{{ url_services }}#development") is just the fragment
        bodies = {}
        for k in keys:
            text = render(parsed[k][1], ctx, str(pages[k][code]))
            bodies[k] = re.sub(r'href="#[\w-]+(#[^"]*)"', r'href="\1"', text)
        id_pages = {k: set(re.findall(r'(?<![\w-])id="([^"]*)"', b)) for k, b in bodies.items()}
        shared = {i for i in set().union(*id_pages.values()) if sum(i in ids for ids in id_pages.values()) > 1}
        sections = []
        for k in keys:
            text = bodies[k] if k == "index" else prefix_ids(k, bodies[k], shared)
            ident = "" if k == "index" else f' id="{k}"'
            sections.append(f'    <section class="pg pg--{k}"{ident}>\n{text.strip(chr(10))}\n    </section>')
        default = langs[0]
        alternates = [f'  <link rel="alternate" hreflang="{lg["code"]}" href="{base}{url_of(lg, "index")}">' for lg in siblings]
        if default["code"] in pages["index"]:
            alternates.append(f'  <link rel="alternate" hreflang="x-default" href="{base}{url_of(default, "index")}">')
        ctx.update({
            "canonical_link": f'  <link rel="canonical" href="{base}{here}">',
            "alternates": "\n".join(alternates),
            "jsonld": org_jsonld(site, lang, home_meta["description"], here),
            "nav": nav_html(lang, link, True),
            "lang_switch": switch_html(lang, keys, True),
            # the travelling mark of the page change: one more copy of the mark, first in <main>
            "content": f'    <div class="mk" aria-hidden="true">{ctx["partial_mark"]}</div>\n' + "\n".join(sections),
        })
        out_path = here.lstrip("/") + "index.html"
        doc = relativize(render(layout, ctx, "layout.html"), out_path)
        dups = duplicate_ids(doc)
        if dups:
            fail(f"{out_path}: ids that are not unique: {', '.join(dups)}")
        write(dist / out_path, doc)
        written.append(out_path)
        sitemap.append((here, [(lg["code"], url_of(lg, "index")) for lg in siblings]))

        # --- the error page: its own file, served at whatever address was missing, so its links stay root-relative ---
        if code in pages.get("404", {}):
            meta, body = read_page(pages["404"][code])
            here404 = url_of(lang, "404")

            def link404(key, lang=lang):
                return frag_of(lang, key)

            ctx = make_ctx(lang, meta, here404, link404)
            ctx.update({
                "canonical_link": "",
                "alternates": "",
                "jsonld": "",
                "nav": nav_html(lang, link404, False),
                "lang_switch": switch_html(lang, ["index"], False),
                "content": render(body, ctx, str(pages["404"][code])),
            })
            out = render(layout, ctx, "layout.html")
            dups = duplicate_ids(out)
            if dups:
                fail(f"{here404}: ids that are not unique: {', '.join(dups)}")
            write(dist / here404.lstrip("/"), out)
            written.append(here404.lstrip("/"))

    write_sitemap(dist, base, sitemap, last_changed())
    (dist / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    problems = check_links(dist) + check_fragments(dist)
    for page, link in problems:
        print(f"{'error' if strict else 'warning'}: {page} links to missing {link}", file=sys.stderr)
    if strict and problems:
        sys.exit(1)
    if minifier:
        # last, so the checks above ran on the readable HTML
        for page in dist.rglob("*.html"):
            write(page, minify_page(page.read_text(encoding="utf-8"), minifier))
    shown = dist.relative_to(ROOT) if dist.is_relative_to(ROOT) else dist
    docs = sum(1 for w in written if w.endswith("index.html"))
    print(f"build: {docs} documents and {len(written) - docs} error page written to {shown}/")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


ID_ATTR = re.compile(r'(?<![\w-])id="([^"]*)"')


def duplicate_ids(page_html):
    """The ids that occur more than once in a document, in order of first repeat."""
    seen, dups = set(), []
    for i in ID_ATTR.findall(page_html):
        if i in seen and i not in dups:
            dups.append(i)
        seen.add(i)
    return dups


def prefix_ids(key, page_html, shared):
    """Give every id in `shared` the prefix '<key>-', and so also the references to it in this page:
    aria-labelledby (a list of ids) and href="#id"."""
    def one(i):
        return f"{key}-{i}" if i in shared else i

    page_html = ID_ATTR.sub(lambda m: f'id="{one(m.group(1))}"', page_html)
    page_html = re.sub(r'aria-labelledby="([^"]*)"',
                       lambda m: 'aria-labelledby="' + " ".join(one(i) for i in m.group(1).split()) + '"', page_html)
    return re.sub(r'href="#([^"]+)"', lambda m: f'href="#{one(m.group(1))}"', page_html)


def write_sitemap(dist, base, entries, lastmod=None):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for here, alts in entries:
        lines.append(f"  <url>\n    <loc>{base}{here}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        for code, url in alts:
            lines.append(f'    <xhtml:link rel="alternate" hreflang="{code}" href="{base}{url}"/>')
        lines.append("  </url>")
    lines.append("</urlset>")
    (dist / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_links(dist):
    """Every internal href/src in the output must point at a file in dist/."""
    broken = []
    for page in dist.rglob("*.html"):
        page_path = page.relative_to(dist).as_posix()
        for link in re.findall(r'(?:href|src)="([^"#?]*)', page.read_text(encoding="utf-8")):
            if not link or link.startswith("//") or re.match(r"[a-z][a-z0-9+.-]*:", link):
                continue                      # external, mailto: or in-page
            if link.startswith("/"):
                path = link.lstrip("/")
            else:
                path = posixpath.normpath(posixpath.join(posixpath.dirname(page_path), link))
            target = dist / path
            if link.endswith("/") or path in ("", "."):
                target = target / "index.html"
            if not target.exists() and (page_path, link) not in broken:
                broken.append((page_path, link))
    return broken


def check_fragments(dist):
    """Every href="#id" in a document must match an id in that same document; href="#" alone is valid."""
    broken = []
    for page in sorted(dist.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        ids = set(ID_ATTR.findall(text))
        for frag in re.findall(r'href="#([^"]+)"', text):
            if frag not in ids and (page.relative_to(dist).as_posix(), "#" + frag) not in broken:
                broken.append((page.relative_to(dist).as_posix(), "#" + frag))
    return broken


if __name__ == "__main__":
    main()
