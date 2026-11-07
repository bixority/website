"""Write the final logo SVGs (dark, light, ink, greyscale, mark-only) from gen.py + fit.json."""
import json
import os
import sys

import gen

OUT = sys.argv[1]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fit.json")) as fh:
    fit = json.load(fh)
for k, v in fit.get("params", {}).items():
    setattr(gen, k, v)
gen.OFFSET = 2 * gen.THICK
wshift = fit["wshift"]
tshift = {int(k): v for k, v in fit["tshift"].items()}
shadow = {k: [round(x, 2) for x in v] for k, v in fit["shadow"].items()}
PAD = 24.0
TITLE = "Bixority — because quality matters"


def bbox_logo():
    lime_tip_x = gen.APEX[0] + gen.ARM * gen.U1[0]
    cyan_apex_y = gen.APEX[1] - gen.OFFSET * gen.AX[1]
    lime_bottom = gen.APEX[1] + gen.ARM * gen.U2[1]
    word_right = gen.WORD_POS["y"] + wshift["y"] + 2 * gen.S + 2 * gen.R
    tag_bottom = gen.TAG_BASE + gen.TAG_K * gen.DESC   # descender bottom edge of q and y
    return lime_tip_x, cyan_apex_y, word_right, max(lime_bottom, tag_bottom)


def pretty(svg):
    from xml.dom import minidom
    root = minidom.parseString(svg).documentElement
    assert root is not None
    text = root.toprettyxml(indent="  ")
    return "\n".join(line for line in text.splitlines() if line.strip()) + "\n"


def logo_svg(variant, prefix, pad=PAD):
    x0, y0, x1, y1 = bbox_logo()
    gen.SHIFT = (x0 - pad, y0 - pad)
    w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    defs, body = gen.logo_group(variant, shadow, wshift, tshift, prefix)
    return pretty(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
                  f'viewBox="0 0 {w:.2f} {h:.2f}" role="img" aria-labelledby="{prefix}title">'
                  f'<title id="{prefix}title">{TITLE}</title><defs>{defs}</defs>{body}</svg>')


def mark_svg(prefix):
    x0 = gen.APEX[0] + gen.ARM * gen.U1[0]
    capex = (gen.APEX[0] - gen.OFFSET * gen.AX[0], gen.APEX[1] - gen.OFFSET * gen.AX[1])
    y0, x1, y1 = capex[1], capex[0], gen.APEX[1] + gen.ARM * gen.U2[1]
    gen.SHIFT = (x0, y0)
    w, h = x1 - x0, y1 - y0
    lime, cyan, capex = gen.mark_geometry()
    defs = gen.axis_grad(prefix + "lime", gen.APEX, gen.LIME_STOPS) + gen.axis_grad(prefix + "cyan", capex, gen.CYAN_STOPS)
    body = f'<path fill="url(#{prefix}cyan)" d="{cyan}"/><path fill="url(#{prefix}lime)" d="{lime}"/>'
    return pretty(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
                  f'viewBox="0 0 {w:.2f} {h:.2f}" role="img" aria-labelledby="{prefix}title">'
                  f'<title id="{prefix}title">Bixority</title><defs>{defs}</defs>{body}</svg>')


def grey(hex_colour):
    """The grey with the same relative luminance as an sRGB colour."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    y = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    v = y * 12.92 if y <= 0.0031308 else 1.055 * y ** (1 / 2.4) - 0.055
    return "#{0:02x}{0:02x}{0:02x}".format(round(v * 255))


def greyscale(fn, *args):
    """Run fn with every brand colour swapped for its greyscale equivalent."""
    saved = {k: getattr(gen, k) for k in ("LIME_STOPS", "CYAN_STOPS", "TAG_DARK", "TAG_LIGHT")}
    gen.LIME_STOPS = [(o, grey(c)) for o, c in saved["LIME_STOPS"]]
    gen.CYAN_STOPS = [(o, grey(c)) for o, c in saved["CYAN_STOPS"]]
    gen.TAG_DARK = [grey(c) for c in saved["TAG_DARK"]]
    gen.TAG_LIGHT = [grey(c) for c in saved["TAG_LIGHT"]]
    try:
        return fn(*args)
    finally:
        for k, v in saved.items():
            setattr(gen, k, v)


os.makedirs(OUT, exist_ok=True)
for name, text in (("bixority-logo-dark.svg", logo_svg("dark", "bxd-")),
                   ("bixority-logo-light.svg", logo_svg("light", "bxl-")),
                   # navy lettering for light grounds (aluminium, paper), where "light" is too pale
                   ("bixority-logo-ink.svg", logo_svg("ink", "bxi-")),
                   ("bixority-logo-ink-tight.svg", logo_svg("ink", "bxit-", pad=0)),
                   ("bixority-logo-greyscale-dark.svg", greyscale(logo_svg, "dark", "bxgd-")),
                   ("bixority-logo-greyscale-light.svg", greyscale(logo_svg, "light", "bxgl-")),
                   # the full logo without padding, for web layouts on dark backgrounds
                   ("bixority-logo-dark-tight.svg", logo_svg("dark", "bxt-", pad=0)),
                   ("bixority-mark.svg", mark_svg("bxm-"))):
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(text)
    print(name, len(text), "bytes")
