#!/usr/bin/env python3
"""Write src/partials/mark.html: the lit, extruded 3D mark as inline SVG.

The geometry is the logo's own (brand/bixority-mark.svg, 468.48 units square).
The two chevrons are separate parts (class part--l and part--c) so the page's
CSS can move and dim them; the partial has no animation of its own.

The mark is <div class="mark"> holding one wrapper per chevron (div.mark__chev), stacked in one grid cell, so that
a page change can turn each chevron in 3D on its own (only an element with a CSS box can, not a <g> in an SVG):
- div.mark__chev--c holds svg.mark__c, the whole mark as one SVG with the defs; the page's CSS hides its lime part,
  so it paints the cyan chevron.
- div.mark__chev--l holds svg.mark__l, the lime chevron on top, using the defs of the first. Its display="none"
  attribute gives way to the page's CSS: without the stylesheet the first SVG alone shows the whole mark, as before.
- After each face come six empty i.mark__side, one per edge of the outline, and svg.mark__slab, the outline alone.
  They are hidden at rest; during a page change the CSS stands each side on its edge and puts the outline behind
  the face as its back, so the chevron turns as a closed solid. The sides' places are fixed by the drawing:
  `python3 tools/gen_mark.py --css` prints their rules for site.css.
- Before each chevron comes div.mark__shadow: the chevron's outline again, which the page's CSS turns into the
  shadow it casts on the background while it spins (at rest each face draws its own soft shadow, .shade).
At rest the mark paints exactly like one SVG with two groups.

Run from the repository root after changing the mark:

    python3 tools/gen_mark.py
"""
import math
import sys
from pathlib import Path

LIME = [(385.89, 82.59), (282.49, 468.48), (234.81, 420.79), (303.30, 165.18), (47.68, 233.67), (0.0, 185.99)]
CYAN = [(468.48, 0.0), (365.08, 385.89), (316.58, 337.39), (384.47, 84.0), (131.09, 151.90), (82.59, 103.40)]
DEPTH = 12.0  # extrusion, straight down: the light comes from above
OUT = Path(__file__).resolve().parent.parent / "src" / "partials" / "mark.html"

Point = tuple[float, float]


def path_d(poly: list[Point]) -> str:
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in poly) + "Z"


def area(poly: list[Point]) -> float:
    n = len(poly)
    return sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n)) / 2


def normal(a: Point, b: Point, ccw: bool) -> tuple[float, float]:
    ex, ey = b[0] - a[0], b[1] - a[1]
    nx, ny = (ey, -ex) if ccw else (-ey, ex)
    length = math.hypot(nx, ny)
    return nx / length, ny / length


def sides(poly: list[Point]) -> list[str]:
    """Quads for the edges whose outward normal faces down (visible under a top light)."""
    ccw = area(poly) > 0  # in SVG's y-down coordinates
    out = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        nx, ny = normal(a, b, ccw)
        if ny <= 0.02:
            continue
        quad = [a, b, (b[0], b[1] + DEPTH), (a[0], a[1] + DEPTH)]
        tone = "a" if nx > 0 else "b"  # right-facing faces catch a little more light
        out.append(f'<path class="side side-{tone}" d="{path_d(quad)}"/>')
    return out


def rims(poly: list[Point]) -> str:
    """Edges whose outward normal faces up: they catch the light."""
    ccw = area(poly) > 0
    segs = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        if normal(a, b, ccw)[1] < -0.2:
            segs.append(f"M{a[0]:.2f} {a[1]:.2f}L{b[0]:.2f} {b[1]:.2f}")
    return "".join(segs)


def part(key: str, poly: list[Point], indent: str) -> str:
    lines = [
        f'<g class="part part--{key}">',
        f'  <use class="shade" href="#p-{key}" transform="translate(8 36)" filter="url(#f-soft)"/>',
        '  <g class="body">',
        *(f"    {s}" for s in sides(poly)),
        f'    <use href="#p-{key}" fill="url(#g-{key})"/>',
        f'    <path class="rim" d="{rims(poly)}"/>',
        "  </g>",
        "</g>",
    ]
    return "\n".join(indent + ln for ln in lines)


def solid(key: str) -> str:
    sides = "".join('<i class="mark__side"></i>' for _ in range(6))
    return (f"    {sides}\n"
            f'    <svg class="mark__slab" viewBox="-24 -24 520 548" aria-hidden="true" focusable="false" display="none">'
            f'<use href="#p-{key}"/></svg>')


def side_css() -> str:
    """The rules that stand each i.mark__side on its edge: from the edge's start (--x, --y), its length and angle."""
    lines = []
    for key, poly in (("c", CYAN), ("l", LIME)):
        ccw = area(poly) > 0
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            nx, ny = normal(a, b, ccw)
            tone = "a" if nx > 0 else "b"
            # rotate(angle) rotateX(90deg) turns the side's front to (sin, -cos) of the angle; use -90deg where that
            # points into the chevron, so every side faces out and hides when turned away
            rad = math.radians(angle)
            flip = 90 if nx * math.sin(rad) - ny * math.cos(rad) > 0 else -90
            lines.append(f".mark__chev--{key} > .mark__side:nth-of-type({i + 1}) {{ --x: {a[0]:.2f}; --y: {a[1]:.2f}; "
                         f"--l: {math.dist(a, b):.2f}; --a: {angle:.2f}deg; --f: {flip}deg; "
                         f"background: var(--side-{tone}); }}")
    return "\n".join(lines)


def shadow(key: str) -> str:
    return (f'  <div class="mark__shadow mark__shadow--{key}"><svg viewBox="-24 -24 520 548" aria-hidden="true" '
            f'focusable="false" display="none"><use class="shade" href="#p-{key}"/></svg></div>')


def build() -> str:
    return f"""<!-- Generated by tools/gen_mark.py; do not edit by hand. Regenerate: python3 tools/gen_mark.py -->
<div class="mark">
{shadow("c")}
  <div class="mark__chev mark__chev--c">
    <svg class="mark__c" viewBox="-24 -24 520 548" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="g-l" gradientUnits="userSpaceOnUse" x1="385.89" y1="82.59" x2="141.24" y2="327.23"><stop offset=".054" stop-color="#ccff00"/><stop offset="1" stop-color="#9ec600"/></linearGradient>
        <linearGradient id="g-c" gradientUnits="userSpaceOnUse" x1="468.48" y1="0" x2="223.83" y2="244.64"><stop offset="0" stop-color="#00ccff"/><stop offset="1" stop-color="#00a9cf"/></linearGradient>
        <filter id="f-soft" x="-25%" y="-25%" width="150%" height="150%"><feGaussianBlur stdDeviation="13"/></filter>
        <path id="p-l" d="{path_d(LIME)}"/>
        <path id="p-c" d="{path_d(CYAN)}"/>
      </defs>
{part("c", CYAN, "      ")}
{part("l", LIME, "      ")}
    </svg>
{solid("c")}
  </div>
{shadow("l")}
  <div class="mark__chev mark__chev--l">
    <svg class="mark__l" viewBox="-24 -24 520 548" aria-hidden="true" focusable="false" display="none">
{part("l", LIME, "      ")}
    </svg>
{solid("l")}
  </div>
</div>
"""


if __name__ == "__main__":
    if "--css" in sys.argv:
        print(side_css())
        raise SystemExit
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
