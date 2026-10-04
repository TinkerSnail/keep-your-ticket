"""The skylines from the town and the summary table."""

import json
import os

import numpy as np

import ht_pil as G
from ht_site import PREFIX, RENDERS, VIEWS

VCOL = {"D1": (40, 90, 200), "D2": (130, 70, 200), "A": (200, 40, 60), "B": (230, 140, 30), "C": (40, 130, 70)}
KEYS = ("D1", "D2", "A", "B", "C")


def skylines(R):
    W, PH = 1500, 260
    img, dr = G.new(W, 60 + len(VIEWS) * (PH + 30) + 40)
    f, fb = G.font(13), G.font(15)
    dr.text((20, 14), "The hill's skyline from the town: elevation angle of the highest ground on each bearing, today (grey) "
            "and after D1, D2, A, B, C (terrain only)", fill=(10, 10, 10), font=G.font(17))
    for k, key in enumerate(VIEWS):
        oy = 50 + k * (PH + 30)
        views = {v: R["variants"][v]["views"][key] for v in KEYS}
        az = np.array(views["A"]["az"])
        lo_az, hi_az = min(np.min(views[v]["az"]) for v in KEYS), max(np.max(views[v]["az"]) for v in KEYS)
        vals = np.concatenate([np.array(views[v]["sky0"]) for v in KEYS] + [np.array(views[v]["sky1"]) for v in KEYS])
        lo, hi = float(vals.min()) - 1, float(vals.max()) + 1
        X = lambda a: 80 + (a - lo_az) / (hi_az - lo_az) * (W - 120)
        Y = lambda e: oy + PH - 20 - (e - lo) / (hi - lo) * (PH - 40)
        dr.rectangle([80, oy, W - 40, oy + PH], outline=(200, 200, 200))
        for e in range(int(lo) + 1, int(hi) + 1, 2 if hi - lo < 25 else 5):
            dr.line([80, Y(e), W - 40, Y(e)], fill=(235, 235, 235))
            dr.text((48, Y(e) - 8), f"{e}°", fill=(120, 120, 120), font=f)
        for a in range(int(lo_az) // 10 * 10 + 10, int(hi_az), 10):
            dr.text((X(a) - 12, oy + PH + 4), f"{a}°", fill=(120, 120, 120), font=f)
        v0 = max(views.values(), key=lambda vw: len(vw["az"]))     # today's skyline over the widest bearings
        dr.line([(X(a), Y(e)) for a, e in zip(v0["az"], v0["sky0"])], fill=(150, 150, 150), width=4)
        for v in KEYS:
            vw = views[v]
            dr.line([(X(a), Y(e)) for a, e in zip(vw["az"], vw["sky1"])], fill=VCOL[v], width=2)
        eye = v0["eye"]
        dr.text((90, oy + 6), f"{VIEWS[key]['label']}, eye {eye[1]:.1f} m over the sea at ({eye[0]:.0f}, {eye[2]:.0f})", fill=(10, 10, 10), font=fb)
        txt = "   ".join(f"{v}: down {views[v]['skyline_max_drop_deg']:.1f}°, {views[v]['visible_disturbed_m2'] / 1000:.1f}k m² new in view"
                         for v in KEYS)
        dr.text((90, oy + 26), txt, fill=(60, 60, 60), font=f)
    y = 50 + len(VIEWS) * (PH + 30)
    for i, (lab, col) in enumerate([("today", (150, 150, 150))] + [(v, VCOL[v]) for v in KEYS]):
        dr.rectangle([80 + i * 120, y, 100 + i * 120, y + 12], fill=col)
        dr.text((106 + i * 120, y - 2), lab, fill=(30, 30, 30), font=f)
    img.save(os.path.join(RENDERS, PREFIX + "skylines.png"))
    print("hillside_terraces: wrote skylines")


def run(folder):
    R = json.load(open(os.path.join(folder, "ht_report.json")))
    skylines(R)
    import ht_draw_table
    ht_draw_table.table(R)
    import ht_draw_sections
    ht_draw_sections.run(folder)
