"""Write src/partials/fig-mark.html: the mark's construction drawing (hero figure).

Coordinates are the mark's own (brand/bixority-mark.svg, 468.48 units square).
Every annotation is a true property of the logo: 45° axis, 60° apex, outer edges
at 15°/75°, band thickness t, cyan copy offset 2t along the axis, cut ⟂ axis.
"""
import math
from pathlib import Path

A = (385.89, 82.59)      # lime apex
T1 = (0.00, 185.99)      # lime left tip
T2 = (282.49, 468.48)    # lime bottom tip
E = (303.30, 165.18)     # lime inner elbow
AC = (468.48, 0.00)      # cyan apex
CT1 = (82.59, 103.40)    # cyan left tip
CT2 = (365.08, 385.89)   # cyan bottom tip
T = 58.4
R2 = math.sqrt(0.5)
AX = (-R2, R2)                                           # axis, apex -> cut
U = (math.cos(math.radians(-15)), math.sin(math.radians(-15)))   # along top edge, to apex
V = (-math.sin(math.radians(15)), math.cos(math.radians(15)))    # along right edge, away from apex
W = (R2, R2)                                             # along the cut


def add(p, d, s=1.0):
    return (p[0] + d[0] * s, p[1] + d[1] * s)


def f(p):
    return f"{p[0]:.2f} {p[1]:.2f}"


def line(p, q, i, cls="c-line"):
    return f'<path class="{cls}" style="--i:{i}" pathLength="1" d="M{f(p)}L{f(q)}"/>'


def label(c, text, i, w=44):
    x, y = c
    return (f'<g class="c-label" style="--i:{i}"><rect x="{x - w / 2:.2f}" y="{y - 12:.2f}" width="{w}" height="24" rx="2"/>'
            f'<text x="{x:.2f}" y="{y + 4.5:.2f}">{text}</text></g>')


def arc(c, r, a0, a1, i):
    p = add(c, (math.cos(math.radians(a0)), math.sin(math.radians(a0))), r)
    q = add(c, (math.cos(math.radians(a1)), math.sin(math.radians(a1))), r)
    return f'<path class="c-line" style="--i:{i}" pathLength="1" d="M{f(p)}A{r} {r} 0 0 1 {f(q)}"/>'


els = []
# 1. the 45° axis, through both apexes, the elbow and the cut
els.append(line(add(AC, AX, -90), add(AC, AX, 560), 0, "c-line c-axis"))
# 2. outer edges extended past the apex
els.append(line(add(T1, U, -45), add(A, U, 110), 1))
els.append(line(add(A, V, -110), add(T2, V, 45), 1))
# 3. the cut lines, perpendicular to the axis
els.append(line(add(T1, W, -45), add(T2, W, 45), 2))
els.append(line(add(CT1, W, -30), add(CT2, W, 30), 2, "c-line c-dash"))
# right-angle marker where the lime cut meets the axis
P = (141.23, 327.25)
m1, m3 = add(P, (R2, -R2), 14), add(P, W, 14)
m2 = add(m1, W, 14)
els.append(f'<path class="c-line" style="--i:3" pathLength="1" d="M{f(m1)}L{f(m2)}L{f(m3)}"/>')
# 4. 60° apex angle (vertical angle beyond the apex) and 45° axis angle
els.append(arc(A, 44, -75, -15, 3))
axis_ref = add(AC, AX, -40)
els.append(line(axis_ref, add(axis_ref, (1, 0), 52), 3))
els.append(arc(axis_ref, 30, -45, 0, 3))
# 5. thickness t across the top arm, offset 2t between the apexes
po = add(A, (-U[0], -U[1]), 250)
pi = add(po, (math.sin(math.radians(15)), math.cos(math.radians(15))), T)
els.append(line(po, pi, 4, "c-line c-dim"))
n = (R2, R2)
els.append(line(add(A, n, 12), add(A, n, 84), 4, "c-line c-ext"))
els.append(line(add(AC, n, 12), add(AC, n, 84), 4, "c-line c-ext"))
els.append(line(add(A, n, 72), add(AC, n, 72), 4, "c-line c-dim"))
nodes = "".join(f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="3.2"/>' for p in (A, AC, E, T1, T2, CT1, CT2, po, pi))
labels = [
    label(add(A, (math.cos(math.radians(-22)), math.sin(math.radians(-22))), 66), "60°", 5),
    label(add(axis_ref, (1, 0), 82), "45°", 5),
    label(add(pi, (math.sin(math.radians(15)), math.cos(math.radians(15))), 26), "t", 5, 28),
    label(add(add(A, n, 72), (AC[0] - A[0], AC[1] - A[1]), 0.5), "2t", 5, 34),
]
labels[3] = label(add(add(add(A, n, 72), ((AC[0] - A[0]) / 2, (AC[1] - A[1]) / 2)), n, 24), "2t", 5, 34)

svg = f'''<svg class="fig-mark" viewBox="-70 -80 660 640" role="img" aria-labelledby="fig-mark-title">
  <title id="fig-mark-title">{{{{ fig_title }}}}</title>
  <defs>
    <linearGradient id="fig-lime" gradientUnits="userSpaceOnUse" x1="385.89" y1="82.59" x2="141.24" y2="327.23"><stop offset="0.054" stop-color="#ccff00"/><stop offset="1" stop-color="#9ec600"/></linearGradient>
    <linearGradient id="fig-cyan" gradientUnits="userSpaceOnUse" x1="468.48" y1="0" x2="223.83" y2="244.64"><stop offset="0" stop-color="#00ccff"/><stop offset="1" stop-color="#00a9cf"/></linearGradient>
  </defs>
  <g class="c-shapes">
    <path class="c-shape c-shape--cyan" pathLength="1" fill="url(#fig-cyan)" d="M468.48 0L365.08 385.89L316.58 337.39L384.47 84L131.09 151.9L82.59 103.4Z"/>
    <path class="c-shape c-shape--lime" pathLength="1" fill="url(#fig-lime)" d="M385.89 82.59L282.49 468.48L234.81 420.79L303.3 165.18L47.68 233.67L0 185.99Z"/>
  </g>
  <g class="c-lines">
    {"".join(els)}
  </g>
  <g class="c-nodes">{nodes}</g>
  <g class="c-labels">{"".join(labels)}</g>
</svg>
'''
Path(__file__).resolve().parent.parent.joinpath("src/partials/fig-mark.html").write_text(svg, encoding="utf-8")
print("wrote src/partials/fig-mark.html")
