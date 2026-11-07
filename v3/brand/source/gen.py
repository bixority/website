"""Build the Bixority logo as clean SVG geometry.

Everything is measured in the pixel space of the supplied raster (dark variant):
the wordmark is a monoline geometric face drawn as stroked centre lines
(straight segments and circular arcs), the mark is two 60-degree chevrons.
"""
import json
import math
import sys

# ---------------------------------------------------------------- metrics
W_STROKE = 27.3            # wordmark stroke width
H = 138.0                  # x-height (outer)
ASC = 193.0                # ascender top above baseline (outer)
S = W_STROKE / 2
R = (H - W_STROKE) / 2     # centre-line radius of every bowl
YT, YB, CY = -H + S, -S, -H / 2
EXT = S                    # horizontal terminals run half a stroke past the curve
DESC = YB + R + S          # descender bottom edge

WORD_BASE = 602.5
TAG_BASE = 679.0
TAG_K = 39.0 / 138.0
TAG_STROKE = 7.6

# glyph left edges in raster px (refined by fit)
WORD_POS = {"b": 608, "i": 755, "x": 791, "o": 938, "r": 1086, "i2": 1177, "t": 1212, "y": 1305}
TAG_POS = [("b", 461), ("e", 502), ("c", 540), ("a", 578), ("u", 618), ("s", 659), ("e", 700),
           ("q", 781), ("u", 822), ("a", 862), ("l", 903), ("i", 913), ("t", 923), ("y", 949),
           ("m", 1032), ("a", 1104), ("t", 1144), ("t", 1170), ("e", 1196), ("r", 1234), ("s", 1259)]
TAG_WORDS = [(0, 7), (7, 14), (14, 21)]   # because / quality / matters

C_TERM = 30.0   # c terminals, degrees from horizontal
E_TERM = 28.0   # e lower terminal
E_BAR = 36.0    # e crossbar angle (through the centre)
S_RC = R / 2     # s bowls are two semicircles

# mark
APEX = (519.75, 290.87)    # lime apex
ARM = 399.5                # outer edge length
THICK = 57.8               # band thickness
OFFSET = 2 * THICK         # cyan sits flush outside lime, along the 45deg axis


SHIFT: tuple[float, float] = (0.0, 0.0)          # subtracted from every emitted coordinate (final viewBox origin)


class Pen:
    def __init__(self, ox=0.0, oy=0.0, k=1.0):
        self.ox, self.oy, self.k, self.d = ox, oy, k, []

    def p(self, x, y):
        return f"{self.ox + self.k * x - SHIFT[0]:.2f} {self.oy + self.k * y - SHIFT[1]:.2f}"

    def M(self, x, y):
        self.cur = self.p(x, y); self.d.append("M" + self.cur)

    def L(self, x, y):
        q = self.p(x, y)
        if q != self.cur:                       # skip zero-length segments
            self.cur = q; self.d.append("L" + q)

    def A(self, cx, cy, r, a0, a1):
        x = cx + r * math.cos(math.radians(a1)); y = cy + r * math.sin(math.radians(a1))
        large = 1 if abs(a1 - a0) > 180 else 0
        sweep = 1 if a1 > a0 else 0
        self.cur = self.p(x, y)
        self.d.append(f"A{self.k * r:.2f} {self.k * r:.2f} 0 {large} {sweep} " + self.cur)

    def circle(self, cx, cy, r):
        self.M(cx + r, cy); self.A(cx, cy, r, 0, 180); self.A(cx, cy, r, 180, 360)

    def path(self): return "".join(self.d)


def pt(cx, cy, r, a):
    return cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))


# ---------------------------------------------------------------- glyphs (x=0 left edge, y=0 baseline)
def g_b(p):
    p.M(S, -ASC); p.L(S, CY); p.A(S + R, CY, R, 180, -90); p.L(S, YT)
def g_i(p):
    p.M(S, -H); p.L(S, 0)
def g_l(p):
    p.M(S, -ASC); p.L(S, 0)
def g_x(p):
    xl = EXT; xr = xl + 2 * R; w = xr + EXT
    p.M(0, YT); p.L(xl, YT); p.A(xl, CY, R, -90, 90); p.L(0, YB)
    p.M(w, YT); p.L(xr, YT); p.A(xr, CY, R, -90, -270); p.L(w, YB)
def g_o(p):
    p.circle(S + R, CY, R)
def g_r(p):
    p.M(S, 0); p.L(S, CY); p.A(S + R, CY, R, 180, 270); p.L(S + R + EXT, YT)
def g_t(p):
    # crossbar on the x-height (the supplied raster had it one stroke lower;
    # moved up by request)
    p.M(S, -ASC); p.L(S, CY); p.A(S + R, CY, R, 180, 90); p.L(S + R + EXT, YB)
    p.M(S, YT); p.L(S + R + EXT, YT)
def g_y(p):
    # a full u bowl; the right stem carries on into a quarter-circle descender
    xr = S + 2 * R
    p.M(S, -H); p.L(S, CY); p.A(S + R, CY, R, 180, 0)
    p.M(xr, -H); p.L(xr, YB); p.A(xr - R, YB, R, 0, 90); p.L(xr - R - EXT, YB + R)
def g_u(p):
    p.M(S, -H); p.L(S, CY); p.A(S + R, CY, R, 180, 0); p.L(S + 2 * R, -H)
def g_a(p, stem_end=0.0):
    xs = S + 2 * R
    p.M(xs, stem_end); p.L(xs, CY); p.A(S + R, CY, R, 0, -270); p.L(xs, YB)
def g_q(p):
    g_a(p, DESC)
def g_c(p):
    cx = S + R
    p.M(*pt(cx, CY, R, C_TERM)); p.A(cx, CY, R, C_TERM, 360 - C_TERM)
def g_e(p):
    cx = S + R; top = 360 - E_BAR
    p.M(*pt(cx, CY, R, E_TERM)); p.A(cx, CY, R, E_TERM, top); p.L(*pt(cx, CY, R, top - 180))
def g_s(p):
    # strokes on the o's sides; each bar stops at the far stroke's centre line
    xl = S; xr = S + 2 * R; rc = S_RC
    p.M(xr, YT); p.L(xl + rc, YT); p.A(xl + rc, YT + rc, rc, -90, -180)
    p.L(xl, CY - rc); p.A(xl + rc, CY - rc, rc, 180, 90)
    p.L(xr - rc, CY); p.A(xr - rc, CY + rc, rc, -90, 0)
    p.L(xr, YB - rc); p.A(xr - rc, YB - rc, rc, 0, 90); p.L(xl, YB)
def g_m(p):
    p.M(S, 0); p.L(S, CY); p.A(S + R, CY, R, 180, 360); p.L(S + 2 * R, 0)
    p.M(S + 2 * R, CY); p.A(S + 3 * R, CY, R, 180, 360); p.L(S + 4 * R, 0)

GLYPHS = {"b": g_b, "i": g_i, "i2": g_i, "l": g_l, "x": g_x, "o": g_o, "r": g_r, "t": g_t, "y": g_y,
          "u": g_u, "a": g_a, "q": g_q, "c": g_c, "e": g_e, "s": g_s, "m": g_m}


def wordmark_path(shift=None):
    p = Pen(0, WORD_BASE, 1.0)
    for name, x in WORD_POS.items():
        p.ox = x + (shift or {}).get(name, 0.0)
        GLYPHS[name](p)
    return p.path()


def tag_paths(shift=None):
    out = []
    for a, b in TAG_WORDS:
        p = Pen(0, TAG_BASE, TAG_K)
        for idx in range(a, b):
            name, x = TAG_POS[idx]
            p.ox = x + (shift or {}).get(idx, 0.0)
            GLYPHS[name](p)
        out.append(p.path())
    return out


# ---------------------------------------------------------------- mark
AX = (-math.sqrt(0.5), math.sqrt(0.5))          # axis from apex towards the cut
U1 = (-math.cos(math.radians(15)), math.sin(math.radians(15)))   # apex -> left tip
U2 = (-math.sin(math.radians(15)), math.cos(math.radians(15)))   # apex -> bottom tip


def chevron(apex, arm, thick):
    ax, ay = apex
    c = thick / math.cos(math.radians(30))      # length of the 45deg end cut
    t1 = (ax + arm * U1[0], ay + arm * U1[1])
    t2 = (ax + arm * U2[0], ay + arm * U2[1])
    t1i = (t1[0] + c * math.sqrt(.5), t1[1] + c * math.sqrt(.5))
    t2i = (t2[0] - c * math.sqrt(.5), t2[1] - c * math.sqrt(.5))
    el = (ax + 2 * thick * AX[0], ay + 2 * thick * AX[1])
    pts = [apex, t2, t2i, el, t1i, t1]
    return "M" + "L".join(f"{x - SHIFT[0]:.2f} {y - SHIFT[1]:.2f}" for x, y in pts) + "Z"


def mark_geometry():
    lime = chevron(APEX, ARM, THICK)
    capex = (APEX[0] - OFFSET * AX[0], APEX[1] - OFFSET * AX[1])
    # cyan is 1px thicker on its inner side; the extra hides under the lime and
    # stops a hairline seam where the two bands meet
    cyan = chevron(capex, ARM, THICK + 1.0)
    return lime, cyan, capex


def axis_grad(gid, apex, stops):
    d = ARM * math.cos(math.radians(30))
    x2, y2 = apex[0] + d * AX[0], apex[1] + d * AX[1]
    st = "".join(f'<stop offset="{o:.3f}" stop-color="{c}"/>' for o, c in stops)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{apex[0] - SHIFT[0]:.2f}" '
            f'y1="{apex[1] - SHIFT[1]:.2f}" x2="{x2 - SHIFT[0]:.2f}" y2="{y2 - SHIFT[1]:.2f}">{st}</linearGradient>')


LIME_STOPS = [(0.054, "#ccff00"), (1.0, "#9ec600")]
CYAN_STOPS = [(0.0, "#00ccff"), (1.0, "#00a9cf")]
WORD_STOPS = [(417, "#ffffff"), (537, "#bababa"), (602, "#bababa"), (658, "#e8e8e8")]
TAG_DARK = ["#ccff00", "#00ccff", "#ccff00"]
TAG_LIGHT = ["#b8bfc9", "#939dac", "#b8bfc9"]
# "ink": the logo for light grounds where the pale "light" lettering does not read
# (aluminium, paper). Navy wordmark; the tagline keeps the dark logo's rhythm with
# "quality" in a deep cyan (4.8:1 on #e3e6e9, 6.0:1 on white).
WORD_INK = "#001b35"
TAG_INK = ["#001b35", "#006c8a", "#001b35"]


def word_grad(gid):
    y0, y1 = WORD_STOPS[0][0], WORD_STOPS[-1][0]
    st = "".join(f'<stop offset="{(y - y0) / (y1 - y0):.3f}" stop-color="{c}"/>' for y, c in WORD_STOPS)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{y0 - SHIFT[1]:.2f}" '
            f'x2="0" y2="{y1 - SHIFT[1]:.2f}">{st}</linearGradient>')


def logo_group(variant, shadow, wshift=None, tshift=None, prefix=""):
    lime, cyan, capex = mark_geometry()
    defs = [axis_grad(prefix + "lime", APEX, LIME_STOPS), axis_grad(prefix + "cyan", capex, CYAN_STOPS)]
    if variant != "ink":
        defs.append(word_grad(prefix + "word"))
    body = []
    if variant in ("light", "ink"):
        sx, sy, sd, so = shadow["mark"]
        defs.append(f'<filter id="{prefix}ms" x="-30%" y="-30%" width="160%" height="160%" color-interpolation-filters="sRGB">'
                    f'<feGaussianBlur in="SourceAlpha" stdDeviation="{sd}"/><feOffset dx="{sx}" dy="{sy}"/>'
                    f'<feComponentTransfer><feFuncA type="linear" slope="{so}"/></feComponentTransfer>'
                    f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    if variant == "light":
        wx, wy, wd, wo = shadow["word"]
        defs.append(f'<filter id="{prefix}ws" x="-5%" y="-10%" width="110%" height="125%" color-interpolation-filters="sRGB">'
                    f'<feGaussianBlur in="SourceAlpha" stdDeviation="{wd}"/><feOffset dx="{wx}" dy="{wy}"/>'
                    f'<feComponentTransfer><feFuncA type="linear" slope="{wo}"/></feComponentTransfer>'
                    f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    mf = f' filter="url(#{prefix}ms)"' if variant in ("light", "ink") else ""
    wf = f' filter="url(#{prefix}ws)"' if variant == "light" else ""
    body.append(f'<g{mf}><path fill="url(#{prefix}cyan)" d="{cyan}"/><path fill="url(#{prefix}lime)" d="{lime}"/></g>')
    stroke = WORD_INK if variant == "ink" else f"url(#{prefix}word)"
    body.append(f'<path{wf} fill="none" stroke="{stroke}" stroke-width="{W_STROKE}" d="{wordmark_path(wshift)}"/>')
    cols = {"dark": TAG_DARK, "ink": TAG_INK}.get(variant, TAG_LIGHT)
    tw = TAG_STROKE
    for col, d in zip(cols, tag_paths(tshift)):
        body.append(f'<path fill="none" stroke="{col}" stroke-width="{tw:.3f}" d="{d}"/>')
    return "".join(defs), "".join(body)


if __name__ == "__main__":
    cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    for _k, _v in cfg.get("params", {}).items():
        globals()[_k] = tuple(_v) if isinstance(_v, list) else _v
    if "THICK" in cfg.get("params", {}) and "OFFSET" not in cfg.get("params", {}):
        OFFSET = 2 * THICK
    shadow =cfg.get("shadow", {"mark": [0, 0, 20, 0.25], "word": [-1.5, 1.5, 1.2, 0.6]})
    wshift = cfg.get("wshift"); tshift = {int(k): v for k, v in cfg.get("tshift", {}).items()}
    LO = cfg.get("light_offset", [123.5, 889.5])
    d1, b1 = logo_group("dark", shadow, wshift, tshift, "d")
    d2, b2 = logo_group("light", shadow, wshift, tshift, "l")
    print(f'<svg xmlns="http://www.w3.org/2000/svg" width="1746" height="1754" viewBox="0 0 1746 1754">'
          f'<defs>{d1}{d2}</defs><rect width="1746" height="1754" fill="#ffffff"/>'
          f'<rect x="0" y="0" width="1746" height="885" fill="#001b35"/>{b1}'
          f'<g transform="translate({LO[0]} {LO[1]})">{b2}</g></svg>')
