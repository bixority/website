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
import re
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
LANDSCAPE = [(1440, 900), (1920, 1080), (1280, 720), (1024, 768)]  # wide landscape: the mark travels
TABLET = (820, 1180)  # upright: the arriving page's own mark turns in place
EVERY_SIZE = [*LANDSCAPE, TABLET, PHONE]
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
    box = page.locator(".pg--services .mark__c").bounding_box()
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


# ---- the page change (motion) ----

REST = [1, 0, 0, 0, 0, 1, 0, 0, 0, -0.4, 1, 0, 0, 0, 0, 1]  # matrix3d of a chevron at rest
CLICK_HOME = ".hd .logo"
SAMPLES = [0, 120, 360, 760]

# One snapshot of everything the checks look at: the state on :root, the pages shown, and every visible mark
# (the travelling .mk or a page's own): its box, its opacity with its ancestors', the lime chevron's transform and
# the opacity of its first side.
SAMPLE_JS = """() => {
  const eff = e => { let o = 1; for (let n = e; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity); return o; };
  const box = e => { const b = e.getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; };
  const root = getComputedStyle(document.documentElement);
  const marks = [...document.querySelectorAll('.mark')].filter(m => m.checkVisibility()).map(m => {
    const mk = m.closest('.mk');
    return { kind: mk ? 'mk' : 'own', rect: box(mk || m), op: eff(mk || m), own_op: parseFloat(getComputedStyle(m).opacity),
             transform: getComputedStyle(m.querySelector('.mark__chev--l')).transform,
             side: getComputedStyle(m.querySelector('.mark__side')).display === 'none' ? 0 : eff(m.querySelector('.mark__side')) };
  });
  const own = [...document.querySelectorAll('.pg .mark')].filter(m => m.checkVisibility()).map(box)[0] || null;
  return { cur: parseFloat(root.getPropertyValue('--cur')), old: parseFloat(root.getPropertyValue('--old')),
           n: parseFloat(root.getPropertyValue('--n')), ready: parseFloat(root.getPropertyValue('--ready')),
           pgs: [...document.querySelectorAll('.pg')].filter(e => getComputedStyle(e).display !== 'none')
                  .map(e => [...e.classList].find(c => c.startsWith('pg--'))),
           own_rect: own, scroll: window.scrollY, marks };
}"""


def progress(s: dict) -> float:
    """--t as the stylesheet computes it."""
    return min(max(s["ready"] * (s["cur"] - s["old"]) / (s["n"] - s["old"] + 0.0001), 0), 1)

# Do an action in the page, then take a snapshot at each of the given times (ms after the action), timed in the page.
RUN_JS = """async ([action, times, sample]) => {
  const snap = eval(sample);
  const go = () => {
    if (action === 'back') history.back();
    else if (action.startsWith('click:')) document.querySelector(action.slice(6)).click();
  };
  const t0 = performance.now();
  go();
  const out = [];
  for (const t of times) {
    const wait = t - (performance.now() - t0);
    if (wait > 0) await new Promise(r => setTimeout(r, wait));
    const s = snap(); s.at = Math.round(performance.now() - t0); out.push(s);
  }
  // the end state: not before .75 s (the change may not have started yet), then until it is over (1.5 s at most)
  let rest = snap();
  while ((rest.cur !== rest.old || performance.now() - t0 < 750) && performance.now() - t0 < 1500) {
    await new Promise(r => setTimeout(r, 50));
    rest = snap();
  }
  rest.at = Math.round(performance.now() - t0);
  return { samples: out, rest };
}"""


def snapshot(page: Page) -> dict:
    return page.evaluate(SAMPLE_JS)


def act_full(page: Page, action: str, times: list[int] | None = None) -> tuple[list[dict], dict]:
    """Do `action` ('click:<selector>' or 'back'), snapshot at each time, then poll until the change is over
    (not before .75 s; --cur equals --old, 1.5 s at most) and snapshot that too: the end state does not depend on a fixed time."""
    out = page.evaluate(RUN_JS, [action, times or SAMPLES, SAMPLE_JS])
    return out["samples"], out["rest"]


def act(page: Page, action: str, times: list[int] | None = None) -> list[dict]:
    """Like act_full, without the end state."""
    return act_full(page, action, times)[0]


def is_landscape(page: Page) -> bool:
    size = page.viewport_size
    assert size
    return size["width"] >= 768 and size["width"] > size["height"]


def matrix_values(transform: str) -> list[float] | None:
    if transform in ("none", ""):
        return None
    return [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", transform.partition("(")[2])]


def at_rest(transform: str) -> bool:
    """The rest matrix, or no transform at all."""
    values = matrix_values(transform)
    return values is None or (len(values) == 16 and all(abs(a - b) < 1e-3 for a, b in zip(values, REST)))


def close(a: list[float] | None, b: list[float] | None, tol: float = 1.0) -> bool:
    return a is not None and b is not None and all(abs(x - y) <= tol for x, y in zip(a, b))


def settled(page: Page, ms: int = 1100) -> None:
    page.wait_for_timeout(ms)


def open_settled(page: Page, url: str) -> None:
    open_at(page, url)
    settled(page)


def movers(snap: dict) -> list[dict]:
    """The marks that are drawn at all."""
    return [m for m in snap["marks"] if m["op"] > 0.01]


@check("no_motion_on_load", *EVERY_SIZE)
def check_no_motion_on_load(page: Page, base: str) -> list[str]:
    bad = []

    def watch(label: str) -> None:
        for _ in range(11):
            snap = snapshot(page)
            for m in snap["marks"]:
                if m["side"] > 0 or not at_rest(m["transform"]):
                    bad.append(f"{label}: a mark moves ({m['kind']}, side {m['side']:.2f}, {m['transform']})")
                    return
            page.wait_for_timeout(100)

    open_at(page, f"{base}/")
    watch("load /")
    open_at(page, f"{base}/#company")
    page.reload()
    watch("reload at #company")
    open_at(page, f"{base}/#services")
    watch("new page at #services")
    open_at(page, f"{base}/#development")
    watch("load at #development")
    return bad


@check("change_runs_once", *EVERY_SIZE)
def check_change_runs_once(page: Page, base: str) -> list[str]:
    bad = []
    landscape = is_landscape(page)
    open_settled(page, f"{base}/")
    steps = [("Home to Services", "click:.hd__link--services", "pg--services"),
             ("Services to Company", "click:.hd__link--company", "pg--company"),
             ("Company to Privacy", "click:.ft__links a[href='#privacy']", "pg--privacy"),
             ("Back", "back", "pg--company"),
             ("the logo", f"click:{CLICK_HOME}", "pg--index")]
    for label, action, expect in steps:
        snaps, rest = act_full(page, action)
        at360 = snaps[2]
        # who should turn: the travelling mark, or the arriving page's own mark where it is shown
        if landscape:
            movers_expected = [m for m in at360["marks"] if m["kind"] == "mk"]
        else:
            movers_expected = [m for m in at360["marks"] if m["kind"] == "own"]
        arriving_has_mark = expect != "pg--privacy" or landscape
        if movers_expected and arriving_has_mark:
            m = movers_expected[0]
            if m["side"] <= 0.05 or at_rest(m["transform"]):
                bad.append(f"{label}: at 360 ms the mark is not turning (side {m['side']:.2f}, {m['transform']})")
        if at360["pgs"] != [expect]:
            bad.append(f"{label}: shows {at360['pgs']}, expected {expect}")
        if rest["cur"] != rest["old"] or rest["cur"] != rest["n"]:
            bad.append(f"{label}: the change did not end: --cur {rest['cur']} --old {rest['old']} --n {rest['n']} after {rest['at']} ms")
        for m in rest["marks"]:
            if not at_rest(m["transform"]) or m["side"] > 0.01:
                bad.append(f"{label}: at the end a {m['kind']} mark is not at rest ({m['transform']}, side {m['side']:.2f})")
        page.wait_for_timeout(400)
    return bad


@check("travel_or_in_place", *EVERY_SIZE)
def check_travel_or_in_place(page: Page, base: str) -> list[str]:
    bad = []
    open_settled(page, f"{base}/")
    s = act(page, "click:.hd__link--services", [360])[0]
    mk = [m for m in s["marks"] if m["kind"] == "mk"]
    own = [m for m in s["marks"] if m["kind"] == "own"]
    if is_landscape(page):
        if len(mk) != 1 or mk[0]["op"] < 0.99:
            bad.append(f"landscape: the travelling mark is not fully shown at 360 ms: {mk}")
        if any(m["own_op"] > 0.01 for m in own):
            bad.append("landscape: the page's own mark is still shown while .mk travels")
    else:
        if mk:
            bad.append("upright or phone: .mk is displayed")
        # Home has its mark on phones; on tablets the inner page's mark is displayed from 48rem
        phone = (page.viewport_size or {"width": 0})["width"] < 768
        if not phone and not own:
            bad.append("tablet: the arriving page's own mark is not displayed")
    return bad


def hand_over(page: Page, base: str, url: str | None, action: str, label: str) -> list[str]:
    """.mk equals the old page's resting mark at the start of the change, and the new page's at its end (1 px).
    url is the page to open first (None: the page as it is)."""
    if url is not None:
        open_settled(page, url)
    before = snapshot(page)["own_rect"]
    snaps, rest = act_full(page, action, [0])
    mk0 = [m["rect"] for m in snaps[0]["marks"] if m["kind"] == "mk"]
    mk1 = [m["rect"] for m in rest["marks"] if m["kind"] == "mk"]
    after = rest["own_rect"]
    bad = []
    if not mk0 or not mk1:
        return [f"{label}: no .mk"]
    if before is not None and not close(mk0[0], before):
        bad.append(f"{label}: at the start .mk is {fmt(mk0[0])}, the old mark {fmt(before)}")
    if after is not None and not close(mk1[0], after):
        bad.append(f"{label}: at the end .mk is {fmt(mk1[0])}, the new mark {fmt(after)}")
    return bad


def fmt(rect: list[float]) -> str:
    return "[" + ", ".join(f"{v:.1f}" for v in rect) + "]"


@check("handover", *LANDSCAPE)
def check_handover(page: Page, base: str) -> list[str]:
    bad = []
    langs = ["", "lv/"] if (page.viewport_size or {}).get("width") == 1440 else [""]
    for lang in langs:
        tag = f"/{lang}"
        bad += hand_over(page, base, f"{base}/{lang}", "click:.hd__link--services", f"{tag} Home to Services")
        bad += hand_over(page, base, f"{base}/{lang}#services", "click:.hd__link--company", f"{tag} Services to Company")
        bad += hand_over(page, base, f"{base}/{lang}#company", f"click:{CLICK_HOME}", f"{tag} Company to Home")
    return bad


@check("privacy_fade", DESKTOP)
def check_privacy_fade(page: Page, base: str) -> list[str]:
    bad = []
    open_settled(page, f"{base}/#services")
    services = snapshot(page)["own_rect"]
    snaps = act(page, "click:.ft__links a[href='#privacy']", [0, 120, 360, 600])
    for s in snaps:
        mk = [m for m in s["marks"] if m["kind"] == "mk"]
        if not mk or not close(mk[0]["rect"], services):
            bad.append(f"to Privacy at {s['at']} ms: .mk is not at the Services mark {fmt(services)}: {mk and fmt(mk[0]['rect'])}")
    last = [m for m in snaps[3]["marks"] if m["kind"] == "mk"]
    if last and last[0]["op"] >= 0.5:
        bad.append(f"to Privacy: .mk opacity {last[0]['op']:.2f} at 600 ms, expected below .5")
    open_settled(page, f"{base}/#privacy")
    snaps = act(page, "click:.hd__link--company", [0, 120, 360, 600])
    company = snaps[3]["own_rect"]
    for s in snaps:
        if s["pgs"] != ["pg--company"]:
            continue  # the hash has not been applied yet
        mk = [m for m in s["marks"] if m["kind"] == "mk"]
        if mk and company and not close(mk[0]["rect"], company):
            bad.append(f"from Privacy at {s['at']} ms: .mk is {fmt(mk[0]['rect'])}, the Company mark {fmt(company)}")
    ops = [next((m["op"] for m in s["marks"] if m["kind"] == "mk"), 0) for s in snaps]
    if not (ops[1] < ops[2] and ops[2] > 0.3):
        bad.append(f"from Privacy: .mk opacity should rise, got {[round(o, 2) for o in ops]}")
    return bad


@check("reduced_motion", DESKTOP, PHONE, reduced_motion=True)
def check_reduced_motion(page: Page, base: str) -> list[str]:
    bad = []
    open_settled(page, f"{base}/")
    s = act(page, "click:.hd__link--services", [100])[0]
    if s["cur"] != s["n"] or s["cur"] != 1:
        bad.append(f"--cur is {s['cur']} 100 ms after the click, expected 1")
    if any(m["side"] > 0 for m in s["marks"]):
        bad.append("a side is visible with reduced motion")
    return bad


@check("double_click", DESKTOP)
def check_double_click(page: Page, base: str) -> list[str]:
    bad = []
    open_settled(page, f"{base}/")
    page.evaluate("""() => new Promise(r => {
        document.querySelector('.hd__link--services').click();
        setTimeout(() => { document.querySelector('.hd__link--company').click(); r(); }, 150); })""")
    page.wait_for_timeout(1100)
    s = snapshot(page)
    if s["cur"] != s["old"] or abs(progress(s)) > 1e-6:
        bad.append(f"after 1100 ms --cur {s['cur']} --old {s['old']}, expected equal")
    if s["pgs"] != ["pg--company"]:
        bad.append(f"shows {s['pgs']}, expected pg--company")
    mk = [m for m in s["marks"] if m["kind"] == "mk"]
    if mk and s["own_rect"] and not close(mk[0]["rect"], s["own_rect"]):
        bad.append(f".mk is {fmt(mk[0]['rect'])}, the Company mark {fmt(s['own_rect'])}")
    page_mk = page.evaluate("(() => { const b = document.querySelector('.mk').getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; })()")
    if s["own_rect"] and not close(page_mk, s["own_rect"]):
        bad.append(f".mk box {fmt(page_mk)} is not at the Company mark {fmt(s['own_rect'])}")
    return bad


# A second change while one runs (a click, or Back): no mark spins out of control. The sampler reads the lime chevron
# of every visible mark each frame and counts the frames in which a matrix value moves by more than .9 per 16.7 ms (a
# frame at 60 Hz, timed by the frame's own timestamp, so a late frame does not count); a turn over --spin moves none
# by more than about .4. CSS cannot carry the angle of a turn that is cut short over to the next
# change, so each interrupting change may snap once; an unbounded progress jumps in nearly every frame.
STEADY_JS = """async ([steps, ms]) => {
  const t0 = performance.now(); let i = 0, prev = null, last = null, frame = t0, worst = 0, at = 0, jumps = 0;
  // each visible mark by name (the travelling one, or the page it belongs to): a page that gives way to another is
  // a different mark, not a jump
  const vals = () => Object.fromEntries([...document.querySelectorAll('.mark')].filter(m => m.checkVisibility()).map(m => {
    const t = getComputedStyle(m.querySelector('.mark__chev--l')).transform;
    const name = m.closest('.mk') ? 'mk' : [...m.closest('.pg').classList].find(c => c.startsWith('pg--'));
    return [name, t === 'none' ? null : t.slice(t.indexOf('(') + 1, -1).split(',').map(Number)]; }));
  while (performance.now() - t0 < ms) {
    const now = performance.now() - t0;
    while (i < steps.length && now >= steps[i][0]) {
      const a = steps[i++][1];
      if (a === 'back') history.back(); else document.querySelector(a).click();
    }
    const cur = vals();
    let step = 0;
    if (prev) for (const [k, v] of Object.entries(cur)) if (v && prev[k]) v.forEach((x, j) => {
      step = Math.max(step, Math.abs(x - prev[k][j])); });
    if (last !== null) step *= 16.7 / Math.max(frame - last, 16.7);
    last = frame;
    if (step > .9) jumps++;
    if (step > worst) { worst = step; at = Math.round(now); }
    prev = cur;
    frame = await new Promise(r => requestAnimationFrame(r));
  }
  return [worst, at, jumps];
}"""


@check("second_change_mid_turn", DESKTOP, TABLET, PHONE)
def check_second_change_mid_turn(page: Page, base: str) -> list[str]:
    bad = []
    cases = {
        "Company, then Home at 500 ms": [[0, ".hd__link--company"], [500, CLICK_HOME]],
        "Services, then Back at 300 ms": [[0, ".hd__link--services"], [300, "back"]],
        "Services and Home in turn every 150 ms": [[0, ".hd__link--services"], [150, CLICK_HOME],
                                                   [300, ".hd__link--services"], [450, CLICK_HOME]],
        "Services, then Company at 200 ms": [[0, ".hd__link--services"], [200, ".hd__link--company"]],
    }
    for label, steps in cases.items():
        open_settled(page, f"{base}/")
        worst, at, jumps = page.evaluate(STEADY_JS, [steps, 1600])
        if jumps > len(steps) - 1:
            bad.append(f"{label}: {jumps} frames with a jump over .9, at most {len(steps) - 1} allowed "
                       f"(largest {worst:.2f} at {at} ms)")
        s = snapshot(page)
        if s["cur"] != s["old"]:
            bad.append(f"{label}: after 1.6 s --cur {s['cur']} --old {s['old']}, expected equal")
    return bad


@check("subsection_from_other_page", DESKTOP, PHONE)
def check_subsection_from_other_page(page: Page, base: str) -> list[str]:
    bad = []
    open_settled(page, f"{base}/#company")
    page.evaluate("""() => { const a = document.createElement('a'); a.id = 'to-dev'; a.href = '#development'; a.textContent = 'x';
        document.querySelector('.pg--company').append(a); }""")
    page.evaluate("document.getElementById('to-dev').click()")
    page.wait_for_timeout(400)
    if shown_pages(page) != ["pg--services"]:
        bad.append(f"displayed {shown_pages(page)}, expected pg--services")
    if underlined(page) != ["services"]:
        bad.append(f"underlined {underlined(page)}, expected services")
    if scroll_y(page) <= 0:
        bad.append("did not scroll to the sub-section")
    return bad


@check("resize_then_change", DESKTOP)
def check_resize_then_change(page: Page, base: str) -> list[str]:
    open_settled(page, f"{base}/")
    page.set_viewport_size({"width": 1280, "height": 720})
    settled(page)
    return hand_over(page, base, None, "click:.hd__link--services", "after resize, Home to Services")


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
