"""Per variant: the street profiles (heights every 10 m over the ground along
the centreline) and cross-sections every 35 m, drawn at true scale."""

import json
import os

import numpy as np

import ht_pil as G
from ht_site import PREFIX, RENDERS

COLS = 4
SW, SH = 440, 300           # one section cell, px
PPM = 3.4                   # px per metre, both ways (no exaggeration)
CUT_FILL = (246, 196, 180)
FILL_FILL = (190, 210, 240)


def section_cell(dr, ox, oy, sec, f, fb):
    u = np.array(sec["u"]) * sec["east"]          # west on the left
    o = np.argsort(u)
    u, E, D = u[o], np.array(sec["E"])[o], np.array(sec["D"])[o]
    prot = np.array(sec["prot"])[o]
    mid = 0.5 * (min(E.min(), D.min()) + max(E.max(), D.max()))
    X = lambda v: ox + SW / 2 + v * PPM
    Y = lambda h: oy + SH / 2 + 18 - (h - mid) * PPM
    dr.rectangle([ox, oy, ox + SW - 6, oy + SH - 6], outline=(200, 200, 200))
    for k in range(len(u) - 1):
        top, bot = max(E[k], D[k]), min(E[k], D[k])
        if top - bot > 0.05:
            col = CUT_FILL if E[k] > D[k] else FILL_FILL
            dr.rectangle([X(u[k]), Y(top), X(u[k + 1]), Y(bot)], fill=col)
    for hv in range(int(mid - 40) // 10 * 10, int(mid + 40), 10):
        if oy + 4 < Y(hv) < oy + SH - 10:
            dr.line([ox + 2, Y(hv), ox + 14, Y(hv)], fill=(150, 150, 150))
            dr.text((ox + 16, Y(hv) - 7), f"{hv}", fill=(130, 130, 130), font=f)
    dr.line([(X(a), Y(b)) for a, b in zip(u, E)], fill=(130, 130, 130), width=1)
    pts = [(X(a), Y(b)) for a, b in zip(u, D)]
    dr.line(pts, fill=(20, 20, 20), width=2)
    for k in np.nonzero(prot)[0][::3]:
        dr.line([X(u[k]), Y(E[k]), X(u[k]) - 3, Y(E[k]) + 5], fill=(90, 100, 160))
    dr.line([X(0), Y(sec["h"]) - 6, X(0), Y(sec["h"]) + 6], fill=(200, 30, 30), width=2)
    cut = float(np.max(E - D))
    if prot[len(prot) // 2]:
        dr.text((ox + SW / 2 - 70, oy + SH / 2 + 40), "under the highway: not cut here", fill=(90, 100, 160), font=fb)
    dr.text((ox + 6, oy + 4), f"{sec['element']}, s {sec['s']:.0f} m  ({sec['x']:.0f}, {sec['z']:.0f})", fill=(10, 10, 10), font=fb)
    dr.text((ox + 6, oy + 22), f"street {sec['h']:.1f} m · deepest cut here {cut:.1f} m", fill=(70, 70, 70), font=f)
    dr.text((ox + 6, oy + SH - 24), "west", fill=(120, 120, 120), font=f)
    dr.text((ox + SW - 44, oy + SH - 24), "east", fill=(120, 120, 120), font=f)


def profile_strip(dr, ox, oy, w, h, r, f, fb):
    names = list(r["profiles"])
    cw = (w - 20 * (len(names) - 1)) / max(len(names), 1)
    for k, nm in enumerate(names):
        rows = r["profiles"][nm]
        el = next((e for e in r["elements"] if e["name"] == nm), None)
        x0 = ox + k * (cw + 20)
        L = rows[-1]["s"]
        hs = [p["h"] for p in rows]
        gr = []
        if el is not None:
            gr = el.get("ground", [])
        lo, hi = min(hs + gr) - 3, max(hs + gr) + 3
        X = lambda s: x0 + 40 + s / max(L, 1) * (cw - 50)
        Y = lambda v: oy + h - 24 - (v - lo) / max(hi - lo, 1) * (h - 54)
        dr.rectangle([x0, oy, x0 + cw, oy + h], outline=(200, 200, 200))
        if gr:
            ss = np.linspace(0, L, len(gr))
            dr.line([(X(a), Y(b)) for a, b in zip(ss, gr)], fill=(150, 150, 150), width=2)
        dr.line([(X(p["s"]), Y(p["h"])) for p in rows], fill=(20, 20, 20), width=3)
        for p in rows[::2]:
            dr.text((X(p["s"]) - 8, Y(p["h"]) - 18), f"{p['h']:.0f}", fill=(20, 20, 20), font=f)
        mg = r["max_grades"].get(nm, {})
        dr.text((x0 + 6, oy + 4), f"{nm}: {L:.0f} m, max grade {mg.get('pct', 0):.1f} %", fill=(10, 10, 10), font=fb)
        for v in range(int(lo) // 10 * 10 + 10, int(hi), 10):
            dr.text((x0 + 4, Y(v) - 7), f"{v}", fill=(140, 140, 140), font=f)


def run(folder):
    R = json.load(open(os.path.join(folder, "ht_report.json")))
    f, fb = G.font(12), G.font(14)
    for v, r in R["variants"].items():
        secs = r["sections"]
        rows = (len(secs) + COLS - 1) // COLS
        W = COLS * SW + 40
        PH = 230
        img, dr = G.new(W, 70 + PH + 30 + rows * SH + 40)
        title = {"A": "A, her lines exactly, all three legs streets", "B": "B, her two lines streets, the leg down public steps",
                 "C": "C, her lines in plan: streets to turning heads, stepped lanes beyond",
                 "D1": "D1, the hill regraded: all three legs streets on it", "D2": "D2, the hill regraded: two streets, steps down"}[v]
        dr.text((20, 14), f"{title}: profiles (heights over the sea; grey the ground along the centreline)", fill=(10, 10, 10), font=G.font(18))
        profile_strip(dr, 20, 50, W - 40, PH, r, f, fb)
        dr.text((20, 50 + PH + 8), "Cross-sections at true scale, every 35 m: grey today's ground, black the design, pink cut, blue fill, "
                "red tick the street's centreline, slate hatching the highway's protected ground", fill=(60, 60, 60), font=fb)
        for k, sec in enumerate(secs):
            section_cell(dr, 20 + (k % COLS) * SW, 50 + PH + 34 + (k // COLS) * SH, sec, f, fb)
        out = os.path.join(RENDERS, f"{PREFIX}sections_{v}.png")
        img.save(out)
        print(f"hillside_terraces: wrote {out}")
