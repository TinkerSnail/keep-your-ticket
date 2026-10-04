"""The top view: today's hill with her lines, then D1, D2, A, B and C, each
shaded, tinted by cut depth, with 5 m contours of the designed ground, the
streets, steps and lanes, the lots, the walls and the highway's band; on the
regrades, ground left steeper than 1:3 is marked."""

import json
import os

import numpy as np

import ht_pil as G
from ht_geom import offset, resample
from ht_site import DOWN, HW_HALF, HW_VERGE, J3, LINE1, LINE2, LOT_RISE, MEET, NEAR, PREFIX, RENDERS

HW_LINE = None

BOX = (-10.0, 370.0, 385.0, 760.0)    # x0, x1, z0, z1 of the drawing (D's regrade reaches x 360)
PPM = 1.6
RED = (220, 30, 30)
LOT_COL = {"cut_pad": (235, 140, 40), "natural_uphill": (60, 150, 60), "natural_downhill": (60, 150, 60), "lane": (225, 190, 30),
           "terrace": (40, 120, 200)}


def crop(A):
    i0, i1 = int(BOX[0] - NEAR["x0"]), int(BOX[1] - NEAR["x0"]) + 1
    j0, j1 = int(BOX[2] - NEAR["z0"]), int(BOX[3] - NEAR["z0"]) + 1
    return A[j0:j1, i0:i1]


def dashed(dr, pts, colour, width=2, on=6, off=5):
    acc, draw = 0.0, True
    for a, b in zip(pts, pts[1:]):
        L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
        if draw:
            dr.line([a, b], fill=colour, width=width)
        acc += L
        if acc > (on if draw else off):
            acc, draw = 0.0, not draw


def panel(main, mdr, ox, oy, E, D, prot, res, title, sub):
    """Draw one panel on its own tile (so nothing spills into the next), then paste it."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (int((BOX[1] - BOX[0]) * PPM), int((BOX[3] - BOX[2]) * PPM)), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    _panel(img, dr, E, D, prot, res)
    main.paste(img, (int(ox), int(oy)))
    mdr.text((ox, oy - 48), title, fill=(10, 10, 10), font=G.font(20))
    mdr.text((ox, oy - 24), sub, fill=(60, 60, 60), font=G.font(13))


def _panel(img, dr, E, D, prot, res):
    ox = oy = 0
    fr = G.Frame(BOX[0], BOX[2], PPM, ox, oy)
    rgb = G.terrain_rgb(crop(E), crop(D))
    pr = crop(prot)
    rgb[pr] = (rgb[pr] * 0.5 + np.array([140, 150, 175]) * 0.5).astype(np.uint8)
    from PIL import Image
    tile = Image.fromarray(rgb).resize((int(rgb.shape[1] * PPM), int(rgb.shape[0] * PPM)), Image.BILINEAR)
    img.paste(tile, (int(ox), int(oy)))
    if res and res["variant"].startswith("D"):
        gz, gx = np.gradient(crop(D))
        bad = (np.hypot(gx, gz) > 0.36) & (np.abs(crop(D) - crop(E)) > 1.0) & ~pr
        rgb[bad] = (rgb[bad] * 0.3 + np.array([210, 40, 190]) * 0.7).astype(np.uint8)
        tile = Image.fromarray(rgb).resize((int(rgb.shape[1] * PPM), int(rgb.shape[0] * PPM)), Image.BILINEAR)
        img.paste(tile, (int(ox), int(oy)))
    G.contours(dr, crop(D), fr, (BOX[0], BOX[2]), 1.0, range(10, 140, 5), (120, 110, 90), 1, 25, (60, 50, 40))
    for side in (1, -1):
        hw = resample(HW_LINE, 2.0)[0]
        dr.line(fr.pts(offset(hw, side * (HW_HALF + HW_VERGE))), fill=(90, 100, 140), width=1)
    for pl in (LINE1 + [MEET], LINE2 + [MEET], DOWN):
        dr.line(fr.pts(pl), fill=RED, width=2)
    if res:
        for lot in res["lots"]["rects"]:
            from ht_geom import rect
            dr.polygon(fr.pts(rect(lot["c"], lot["t"], 8.0, 7.0)), outline=LOT_COL[lot["kind"]], width=2)
        for e in res["elements"]:
            pts = np.array(e["pts"])
            if e["kind"] == "head":
                cx, cz = fr(*pts[0])
                r = e["half"] * PPM
                dr.ellipse([cx - r, cz - r, cx + r, cz + r], outline=(30, 30, 30), width=2)
                continue
            if e["kind"] == "lane":
                continue                      # drawn below, dashed, from the lane records
            if e["kind"] == "context":
                dr.line(fr.pts(pts), fill=(110, 110, 110), width=2)
                continue
            col = (110, 70, 30) if e["kind"] == "steps" else (30, 30, 30)
            for side in (1, -1):
                dr.line(fr.pts(offset(pts, side * e["half"])), fill=col, width=2)
            dashed(dr, fr.pts(pts), (255, 255, 255), 1, 4, 4)
        for u in res["underpass"]:
            dashed(dr, fr.pts(u["pts"]), (20, 20, 120), 3, 8, 5)
        for ln in res["lanes"]:
            dashed(dr, fr.pts(ln["pts"]), (110, 70, 30), 4, 5, 4)
        for w in res.get("wall_list", []):
            if not w["verge"] and abs(w["h_m"] - LOT_RISE) < 0.4:
                continue                      # garage fronts are the houses' own base, not drawn as walls
            c = (0, 170, 200) if w["verge"] else (255, 110, 0) if w.get("portal") else ((200, 0, 160) if w["h_m"] > 4.3 else (20, 20, 20))
            x, y = fr(w["x"], w["z"])
            dr.ellipse([x - 1.2, y - 1.2, x + 1.2, y + 1.2], fill=c)
        x, y = fr(*MEET)
        dr.text((x + 8, y - 22), f"{res['meet_h']:.1f}", fill=(0, 0, 0), font=G.font(15))
    if res is None:                                   # today: the ground under her lines' ends
        for px, pz in (LINE1[0], LINE1[-1], LINE2[0], LINE2[-1], MEET, DOWN[-1], (52, 530), (89, 545)):
            hh = float(E[int(pz - NEAR["z0"]), int(px - NEAR["x0"])])
            x, y = fr(px, pz)
            dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=RED)
            dr.text((x + 6, y - 8), f"{hh:.0f}", fill=(120, 0, 0), font=G.font(14))
    x, y = fr(*J3)
    dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(20, 20, 120))
    dr.text((x + 6, y - 6), "J3 18.2", fill=(20, 20, 120), font=G.font(13))
    dr.rectangle([0, 0, img.width - 1, img.height - 1], outline=(150, 150, 150))


def run(folder):
    global HW_LINE
    R = json.load(open(os.path.join(folder, "ht_report.json")))
    HW_LINE = R["hw_line"]
    Z = np.load(os.path.join(folder, "ht_design.npz"))
    E = Z["E"]
    w = int((BOX[1] - BOX[0]) * PPM)
    h = int((BOX[3] - BOX[2]) * PPM)
    gap, top = 26, 66
    img, dr = G.new(3 * w + 4 * gap, 2 * (h + top) + 150)
    names = {"D1": "D1  regrade, all three legs streets", "D2": "D2  regrade, two streets, steps down",
             "A": "A  her lines, all streets (cut)", "B": "B  two streets, steps down (cut)", "C": "C  streets, then stepped lanes"}
    slots = [("today", None)] + [(v, R["variants"][v]) for v in ("D1", "D2", "A", "B", "C")]
    for k, (v, r) in enumerate(slots):
        ox, oy = gap + (k % 3) * (w + gap), top + (k // 3) * (h + top)
        if r is None:
            panel(img, dr, ox, oy, E, E, Z["prot_A"], None, "Today", "her lines in red; heights over the sea; 5 m contours")
            continue
        if v.startswith("D"):
            vol, sm = r["volumes"], r["summit"]
            sub = (f"meet {r['meet_h']:.1f} m · cut {vol['cut_m3'] / 1000:.0f}k m³ · summit {sm['before_m']:.0f} → {sm['there_after_m']:.0f} m · "
                   f"lots {r['lots']['total']}")
        else:
            vol = r["volumes_1:1"]
            sub = (f"meet {r['meet_h']:.1f} m · cut {vol['cut_m3'] / 1000:.0f}k m³ · deepest {vol['deepest_cut_m']:.0f} m · "
                   f"lots {r['lots']['total']}")
        panel(img, dr, ox, oy, E, Z[f"D_{v}"], Z[f"prot_{v}"], r, names[v], sub)
    oy = 2 * (h + top) + 4                 # below the second row of panels
    f = G.font(14)
    y = oy + 14
    items = [((220, 30, 30), "her lines"), ((30, 30, 30), "street, 9 m"), ((110, 70, 30), "steps / stepped lane"),
             ((20, 20, 120), "under the highway (not cut here)"), ((235, 140, 40), "lot cut as a pad, garage under"),
             ((60, 150, 60), "lot on natural ground"), ((225, 190, 30), "lane lot (no car)"), ((20, 20, 20), "wall ≤ 4 m"),
             ((200, 0, 160), "wall over 4 m"), ((255, 110, 0), "walled cutting to the underpass"),
             ((0, 170, 200), "wall holding the highway's verge"), ((140, 150, 175), "highway band, protected"),
             ((40, 120, 200), "lot on a low terrace (walls ≤ 2 m)"), ((210, 40, 190), "regrade left steeper than 1:3"),
             ((110, 110, 110), "pass 10's terrace streets, held on grade")]
    x = gap
    for col, label in items:
        need = 34 + int(dr.textlength(label, font=f))
        if x + need > img.width - gap:
            x, y = gap, y + 24
        dr.rectangle([x, y + 3, x + 16, y + 15], fill=col)
        dr.text((x + 22, y), label, fill=(30, 30, 30), font=f)
        x += need
    dr.text((gap, y + 30), "Tint: cut depth (white 0, orange 15 m, red 30 m, plum 50 m); blue: fill. North up, x east, z south; "
            "grid 1 m sampled from a scratch copy of the world terrain master.", fill=(70, 70, 70), font=f)
    out = os.path.join(RENDERS, PREFIX + "top.png")
    img.save(out)
    print(f"hillside_terraces: wrote {out}")
