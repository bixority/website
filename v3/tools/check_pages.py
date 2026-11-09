#!/usr/bin/env python3
"""Browser checks for a built dist/ folder (Playwright, Firefox and Chromium).

    uvx --with playwright python tools/check_pages.py --dist dist
    uvx --with playwright python tools/check_pages.py --dist dist --engine firefox --only sections

dist/ is served on a free local port. A check is a function `check_<name>(page, base) -> list[str]` that returns
its failure messages (none: it passed). Register it with @check(name, *sizes); it then runs in every selected engine
and in each viewport size it declares. Exit status 1 if any check fails.
"""
import argparse
import functools
import http.server
import struct
import sys
import threading
import zlib
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

DESKTOP = (1440, 900)
PHONE = (390, 844)
CheckFn = Callable[[Page, str], list[str]]
CHECKS: list[tuple[str, tuple[tuple[int, int], ...], bool, CheckFn]] = []


def check(name: str, *sizes: tuple[int, int], reduced_motion: bool = False) -> Callable[[CheckFn], CheckFn]:
    """Register a check under `name`, to run at each of `sizes` (default: desktop and phone), with
    prefers-reduced-motion: reduce if asked."""
    def register(fn: CheckFn) -> CheckFn:
        CHECKS.append((name, sizes or (DESKTOP, PHONE), reduced_motion, fn))
        return fn
    return register


# ---- helpers ----

def open_at(page: Page, url: str) -> None:
    """A fresh load of url (a hash change alone would not reload the document)."""
    page.goto("about:blank")
    page.goto(url)
    page.wait_for_load_state("load")


def shown_pages(page: Page) -> list[str]:
    """The modifier of every displayed .pg ('pg--services')."""
    return page.evaluate("""() => [...document.querySelectorAll('.pg')]
        .filter(e => getComputedStyle(e).display !== 'none')
        .map(e => [...e.classList].find(c => c.startsWith('pg--')))""")


def scroll_y(page: Page) -> float:
    return page.evaluate("window.scrollY")


def underlined(page: Page) -> list[str]:
    return page.evaluate("""() => [...document.querySelectorAll('.hd__link')]
        .filter(a => getComputedStyle(a).textDecorationLine.includes('underline'))
        .map(a => [...a.classList].find(c => c.startsWith('hd__link--')).slice(10))""")


def shown_lang_links(page: Page) -> list[str]:
    return page.evaluate("""() => [...document.querySelectorAll('.hd__lang')]
        .filter(a => getComputedStyle(a).display !== 'none').map(a => a.getAttribute('href'))""")


def png_pixels(data: bytes) -> tuple[int, int, int, bytes]:
    """Decode an 8-bit, non-interlaced RGB or RGBA PNG: (width, height, bytes per pixel, raw rows)."""
    pos, idat, width = 8, b"", 0
    height = depth = ctype = 0
    while pos < len(data):
        (size,) = struct.unpack(">I", data[pos:pos + 4])
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + size]
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and ctype in (2, 6) and interlace == 0, "unsupported PNG"
        elif kind == b"IDAT":
            idat += body
        pos += 12 + size
    bpp = 3 if ctype == 2 else 4
    raw, stride, rows, prev = zlib.decompress(idat), width * bpp, [], bytearray(width * bpp)
    for y in range(height):
        ft, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                line[i] = (line[i] + a) & 255
            elif ft == 2:
                line[i] = (line[i] + b) & 255
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    return width, height, bpp, b"".join(rows)


def pixel(data: bytes, x: int, y: int) -> tuple[int, int, int]:
    width, _, bpp, raw = png_pixels(data)
    i = (y * width + x) * bpp
    return raw[i], raw[i + 1], raw[i + 2]


# ---- checks ----

PAGE_TARGETS = [("", "index"), ("#services", "services"), ("#open-source", "open-source"),
                ("#company", "company"), ("#privacy", "privacy"), ("#development", "services")]


@check("sections")
def check_sections(page: Page, base: str) -> list[str]:
    bad = []
    for hash_, key in PAGE_TARGETS:
        open_at(page, f"{base}/{hash_}")
        shown = shown_pages(page)
        if shown != [f"pg--{key}"]:
            bad.append(f"{hash_ or 'Home'}: displayed {shown}, expected pg--{key}")
        y = scroll_y(page)
        if hash_ == "#development" and y <= 0:
            bad.append("#development: did not scroll to the sub-section")
        if hash_ != "#development" and y != 0:
            bad.append(f"{hash_ or 'Home'}: scrollY is {y}, expected 0")
    open_at(page, f"{base}/")
    page.click(".hd__link--services")
    if shown_pages(page) != ["pg--services"] or scroll_y(page) != 0:
        bad.append(f"click Services from Home: displayed {shown_pages(page)}, scrollY {scroll_y(page)}")
    open_at(page, f"{base}/#company")
    page.evaluate("window.scrollTo(0, 1500)")
    page.click(".hd__link--open-source")
    if shown_pages(page) != ["pg--open-source"] or scroll_y(page) != 0:
        bad.append(f"click Open source from a scrolled Company: displayed {shown_pages(page)}, scrollY {scroll_y(page)}")
    return bad


@check("header")
def check_header(page: Page, base: str) -> list[str]:
    bad = []
    for prefix, home_end in (("", "lv/"), ("lv/", "../")):
        for hash_, key in PAGE_TARGETS:
            where = f"/{prefix}{hash_}"
            open_at(page, f"{base}/{prefix}{hash_}")
            expect = [key] if key in ("services", "open-source", "company") else []
            if underlined(page) != expect:
                bad.append(f"{where}: underlined {underlined(page)}, expected {expect}")
            links = shown_lang_links(page)
            end = home_end if key == "index" else f"{home_end}#{key}" if home_end == "../" else f"lv/#{key}"
            if len(links) != 1 or not links[0].endswith(end):
                bad.append(f"{where}: language links shown {links}, expected one ending with {end}")
    return bad


@check("print", DESKTOP)
def check_print(page: Page, base: str) -> list[str]:
    bad = []
    open_at(page, f"{base}/#company")
    page.emulate_media(media="print")
    if shown_pages(page) != ["pg--company"]:
        bad.append(f"print: displayed {shown_pages(page)}")
    visible = page.evaluate("[...document.querySelectorAll('.mark')].filter(e => e.checkVisibility()).length")
    if visible:
        bad.append(f"print: {visible} .mark elements are visible")
    return bad


@check("defs_painted", DESKTOP)
def check_defs_painted(page: Page, base: str) -> list[str]:
    bad = []
    open_at(page, f"{base}/#services")
    box = page.locator(".pg--services .mark").bounding_box()
    if not box:
        return ["#services: no mark box"]
    # a point on the cyan arm: (300, 75) of the viewBox -24 -24 520 548
    x, y = round(box["x"] + box["width"] * (324 / 520)), round(box["y"] + box["height"] * (99 / 548))
    shot = page.screenshot()
    r, g, b = pixel(shot, x, y)
    if max(r, g, b) - min(r, g, b) <= 10:
        bad.append(f"#services: the face at ({x}, {y}) is grey: rgb({r}, {g}, {b}), the gradient is not painted")
    open_at(page, f"{base}/404.html")
    data = page.locator(".mark").first.screenshot()
    width, height, bpp, raw = png_pixels(data)
    colours = {raw[i:i + bpp] for i in range(0, width * height * bpp, bpp)}
    if len(colours) <= 1:
        bad.append("404.html: the mark is one flat colour (the shared defs are not painted)")
    return bad


# ---- nothing but the page moves ----

# Every running animation or transition on the document timeline, with its target. (The home mark's scroll-driven
# reveal runs on a scroll or view timeline and is not part of a page change.)
RUNNING_JS = """() => document.getAnimations()
    .filter(a => a.timeline === document.timeline && a.playState === 'running')
    .map(a => { const t = a.effect && a.effect.target;
                return { name: a.animationName || a.transitionProperty || '?',
                         target: t ? t.tagName.toLowerCase() + (t.className && t.className.baseVal === undefined ? '.' + t.className : '') : null,
                         pg: !!(t && t.classList && t.classList.contains('pg')) }; })"""

CHANGE_JS = """async ([action, times, running]) => {
  const snap = eval(running);
  document.querySelector(action).click();
  const t0 = performance.now();
  const out = [];
  for (const t of times) {
    const wait = t - (performance.now() - t0);
    if (wait > 0) await new Promise(r => setTimeout(r, wait));
    out.push({ at: Math.round(performance.now() - t0), running: snap(),
               pgs: [...document.querySelectorAll('.pg')].filter(e => getComputedStyle(e).display !== 'none').length });
  }
  return out;
}"""


@check("no_motion", DESKTOP, PHONE)
def check_no_motion(page: Page, base: str) -> list[str]:
    """During a page change nothing but the .pg sections has a running animation or transition."""
    bad = []
    for label, start, action in (("Home to Services", "/", ".hd__link--services"),
                                 ("Services to Home", "/#services", ".hd .logo")):
        open_at(page, f"{base}{start}")
        page.wait_for_timeout(600)
        for sample in page.evaluate(CHANGE_JS, [action, [0, 120, 360], RUNNING_JS]):
            if sample["pgs"] != 1:
                bad.append(f"{label} at {sample['at']} ms: {sample['pgs']} pages displayed")
            for a in sample["running"]:
                if not a["pg"]:
                    bad.append(f"{label} at {sample['at']} ms: {a['name']} runs on {a['target']}")
    return bad


# ---- runner ----

def serve(dist: Path) -> tuple[http.server.ThreadingHTTPServer, str]:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

    handler = functools.partial(Quiet, directory=str(dist))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dist", type=Path, required=True, help="the built site")
    ap.add_argument("--engine", choices=("firefox", "chromium", "both"), default="both")
    ap.add_argument("--only", metavar="NAME", help="run one check (e.g. sections)")
    args = ap.parse_args(argv)
    chosen = [c for c in CHECKS if args.only in (None, c[0])]
    if not chosen:
        print(f"no check named {args.only}; known: {', '.join(c[0] for c in CHECKS)}", file=sys.stderr)
        return 2
    engines = ["firefox", "chromium"] if args.engine == "both" else [args.engine]
    server, base = serve(args.dist.resolve())
    failed = 0
    with sync_playwright() as pw:
        for engine in engines:
            browser = getattr(pw, engine).launch()
            for name, sizes, reduced, fn in chosen:
                for width, height in sizes:
                    context = browser.new_context(viewport={"width": width, "height": height},
                                                  reduced_motion="reduce" if reduced else "no-preference")
                    try:
                        problems = fn(context.new_page(), base)
                    except (PlaywrightError, AssertionError) as exc:  # a check that cannot run is a failed check
                        problems = [f"error: {type(exc).__name__}: {exc}"]
                    context.close()
                    failed += bool(problems)
                    print(f"{'FAIL' if problems else 'PASS'} {name} {engine} {width}x{height}")
                    for p in problems:
                        print(f"     {p}")
            browser.close()
    server.shutdown()
    print("failed" if failed else "all checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
