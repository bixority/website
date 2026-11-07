#!/usr/bin/env python3
"""Build the static site from src/ into dist/. Standard library only.

    python3 build.py                   # build, warn about links to pages that don't exist yet
    python3 build.py --strict          # build, fail on any broken internal link
    python3 build.py --out /tmp/site   # write somewhere else than dist/ (parallel builds)
"""
import argparse
import hashlib
import html
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_MARKER = ".bixority-build"
SRC = ROOT / "src"
PLACEHOLDER = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")
# Context values that are HTML already and must not be escaped.
RAW = {"alternates", "nav", "lang_switch", "content", "jsonld", "robots", "canonical_link"}
RAW_PREFIXES = ("partial_",)


def fail(msg):
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


def build_assets(dist):
    """Copy static assets; bundle and fingerprint CSS and JS. Returns their URLs."""
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
    css = "\n".join([font_css, *(p.read_text(encoding="utf-8") for p in sheets)]).encode()
    css_name = fingerprinted(css, "site", ".css")
    (assets / css_name).write_bytes(css)

    js = (SRC / "assets" / "js" / "site.js").read_bytes()
    js_name = fingerprinted(js, "site", ".js")
    (assets / js_name).write_bytes(js)
    return f"/assets/{css_name}", f"/assets/{js_name}"


def org_jsonld(site):
    c, base = site["company"], site["base_url"]
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site["brand"],
        "legalName": c["legal_name"],
        "url": base + "/",
        "logo": base + "/assets/img/mark-512.png",
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
        "sameAs": site["profiles"],
    }
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'  <script type="application/ld+json">\n{body}\n  </script>'


def parse_args(argv):
    ap = argparse.ArgumentParser(description="Build the static site from src/.")
    ap.add_argument("--strict", action="store_true", help="fail on any broken internal link")
    ap.add_argument("--out", type=Path, default=ROOT / "dist", metavar="DIR", help="output directory (default: dist/)")
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
    if dist != ROOT / "dist":
        # dist/ is always ours to replace; other outputs carry a marker, and dist/ is
        # what gets deployed, so the marker never ships with the site
        (dist / BUILD_MARKER).write_text("Output of build.py; it may be deleted and rebuilt.\n", encoding="utf-8")
    css_url, js_url = build_assets(dist)

    def url_of(lang, key):
        if key == "404":
            return f"{lang['prefix']}/404.html"
        return lang["prefix"] + site["pages"][key]

    # Which pages exist in which language.
    pages = {}
    for lang in langs:
        for path in sorted((SRC / "pages" / lang["code"]).glob("*.html")):
            key = path.stem
            if key != "404" and key not in site["pages"]:
                fail(f"{path}: page '{key}' is not listed in site.json")
            pages.setdefault(key, {})[lang["code"]] = path

    sitemap = []
    for key, by_lang in pages.items():
        for lang in langs:
            if lang["code"] not in by_lang:
                continue
            t = strings[lang["code"]]
            meta, body = read_page(by_lang[lang["code"]])
            here = url_of(lang, key)
            others = [lg for lg in langs if lg is not lang]
            siblings = [lg for lg in langs if lg["code"] in by_lang]

            alternates = []
            if key != "404":
                alternates = [f'  <link rel="alternate" hreflang="{lg["code"]}" href="{base}{url_of(lg, key)}">' for lg in siblings]
                default = langs[0]
                if default["code"] in by_lang:
                    alternates.append(f'  <link rel="alternate" hreflang="x-default" href="{base}{url_of(default, key)}">')

            nav = []
            for item in site["nav"]:
                href = url_of(lang, item)
                current = ' aria-current="page"' if item == key else ""
                nav.append(f'      <li><a href="{href}"{current}>{html.escape(t["nav"][item])}</a></li>')

            # One word, in the other language: the only language control.
            switch = []
            for other in others:
                target = url_of(other, key) if other["code"] in by_lang else url_of(other, "index")
                switch.append(f'<a class="hd__lang" href="{target}" hreflang="{other["code"]}" lang="{other["code"]}">{html.escape(other["name"])}</a>')

            c = site["company"]
            ctx = {
                "lang": lang["code"],
                "title": meta["title"],
                "description": meta["description"],
                "robots": '  <meta name="robots" content="noindex">' if meta.get("robots") == "noindex" else "",
                "canonical": base + here,
                "canonical_link": "" if key == "404" else f'  <link rel="canonical" href="{base}{here}">',
                "alternates": "\n".join(alternates),
                "og_locale": lang["locale"],
                "og_locale_alt": ", ".join(lg["locale"] for lg in others),
                "base_url": base,
                "css": css_url,
                "js": js_url,
                "jsonld": org_jsonld(site) if key == "index" else "",
                "skip": t["skip"],
                "home_url": url_of(lang, "index"),
                "home_link": t["home_link"],
                "nav_label": t["nav_label"],
                "nav": "\n".join(nav),
                "lang_switch": " ".join(switch),
                "privacy_url": url_of(lang, "privacy"),
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
                ctx["url_" + k.replace("-", "_")] = url_of(lang, k)

            for name, text in partials.items():
                ctx["partial_" + name] = render(text, ctx, f"partials/{name}.html")
            ctx["content"] = render(body, ctx, str(by_lang[lang["code"]]))
            out = render(layout, ctx, "layout.html")
            out_path = here.lstrip("/") + ("index.html" if here.endswith("/") else "")
            # The 404 page is served at whatever address was missing, so its
            # links must stay root-relative; every other page gets relative ones.
            if key != "404":
                out = relativize(out, out_path)
            target = dist / out_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(out, encoding="utf-8")
            if key != "404":
                sitemap.append((here, [(lg["code"], url_of(lg, key)) for lg in siblings]))

    write_sitemap(dist, base, sitemap)
    (dist / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    broken = check_links(dist)
    for page, link in broken:
        print(f"{'error' if strict else 'warning'}: {page} links to missing {link}", file=sys.stderr)
    if strict and broken:
        sys.exit(1)
    count = sum(len(v) for v in pages.values())
    shown = dist.relative_to(ROOT) if dist.is_relative_to(ROOT) else dist
    print(f"build: {count} pages written to {shown}/")


def write_sitemap(dist, base, entries):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for here, alts in entries:
        lines.append(f"  <url>\n    <loc>{base}{here}</loc>")
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


if __name__ == "__main__":
    main()
