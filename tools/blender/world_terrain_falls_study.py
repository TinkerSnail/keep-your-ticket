"""A Bridalveil moment: a tall slender waterfall on creek K seen as a reveal from the coast
highway, with the river K beside the road (2026-10-02, Christina: "let's have a Bridalveil
Falls moment with the river visible from the highway"). PROPOSAL only: nothing touches the
master; the Blender step renders from scratch cameras it never saves.

    Blender --background assets/source/world_terrain_master.blend --python <this> -- --sample <folder>
        (5 m ray grid of the valley x 100..700, z -600..-120 and the highway centreline -> grid5.npz, highway.json)
    python3 <this> --analyse <folder> --out <renders>     (viewshed, ranking, design, falls_plan.png, falls_profile.png, falls_table.png)
    Blender --background assets/source/world_terrain_master.blend --python <this> -- --render <folder> --out <renders>
        (driver's-eye renders at first sight / best / last sight and the turnout; cameras not saved)

Highway drive order: highway_path() runs from the far north down the coast, turns east up the
north valley at the cove and south past the park's north-east corner (index increasing =
SOUTHBOUND; decreasing = NORTHBOUND).
"""
import json
import math
import os
import sys

import numpy as np

EYE = 1.2
SPEEDS = {"60 km/h": 60 / 3.6, "90 km/h": 90 / 3.6}
WINDSCREEN = 70.0   # degrees either side of the travel direction a driver can see
K1 = [(520, -410), (480, -370), (440, -330), (400, -290), (360, -250), (330, -225), (300, -230)]   # the K-1 creek line (lake spill to the take-off)
SUN = {"morning 09:00": (115.0, 35.0), "noon": (180.0, 70.0), "afternoon 15:30": (245.0, 40.0), "sunset (azimuth 294)": (294.0, 4.0)}   # lat 32.75, early summer; the project's sunset azimuth
MEAN_Q, MAY_Q, LATE_Q, PEAK_Q = 0.457, 1.08, 0.38, 13.6


def load(folder):
    d = np.load(os.path.join(folder, "grid5.npz"))
    hw = json.load(open(os.path.join(folder, "highway.json")))
    return d["H"], d["xs"], d["zs"], hw


def g_at(H, xs, zs, x, z):
    fx = (x - xs[0]) / 5.0
    fz = (z - zs[0]) / 5.0
    i0 = int(np.clip(math.floor(fx), 0, len(xs) - 2))
    j0 = int(np.clip(math.floor(fz), 0, len(zs) - 2))
    tx, tz = fx - i0, fz - j0
    q = H[j0:j0 + 2, i0:i0 + 2]
    return float((q[0, 0] * (1 - tx) + q[0, 1] * tx) * (1 - tz) + (q[1, 0] * (1 - tx) + q[1, 1] * tx) * tz)


def los(H, xs, zs, a, b, step=4.0):
    """line of sight from a (x,z,y) to b (x,z,y): True if the terrain stays 0.5 m under the ray."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(L / step))
    for k in range(1, n):
        t = k / n
        x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        y = a[2] + (b[2] - a[2]) * t
        if not (xs[0] <= x <= xs[-1] and zs[0] <= z <= zs[-1]):
            return False
        if g_at(H, xs, zs, x, z) + 0.5 > y:
            return False
    return True


def bearing(dx, dz):
    return (math.degrees(math.atan2(dx, -dz)) + 360.0) % 360.0   # from north, x east, -z north


def analyse(folder, out):
    os.makedirs(out, exist_ok=True)
    H, xs, zs, hw = load(folder)
    # stations every 10 m along the highway between the cove and the park's east side
    seg = [p for p in hw if -600 <= p[1] <= -100 and -150 <= p[0] <= 700]
    st = []
    s = 0.0
    for i in range(len(seg) - 1):
        a, b = seg[i], seg[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / 10))
        for k in range(n):
            t = k / n
            x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            heading_sb = bearing(b[0] - a[0], b[1] - a[1])
            st.append({"s": s + t * L, "x": x, "z": z, "y": g_at(H, xs, zs, x, z) + EYE, "heading_sb": heading_sb})
        s += L
    # the K-1 profile and candidate lips: the steepest 40 m windows along the creek line
    prof = []
    for i in range(len(K1) - 1):
        a, b = K1[i], K1[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(int(L / 5)):
            t = k / (L / 5)
            x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            prof.append((x, z, g_at(H, xs, zs, x, z)))
    prof.append((K1[-1][0], K1[-1][1], g_at(H, xs, zs, *K1[-1])))
    sp = [0.0]
    for i in range(1, len(prof)):
        sp.append(sp[-1] + math.hypot(prof[i][0] - prof[i - 1][0], prof[i][1] - prof[i - 1][1]))
    cands = {
        "C1 upper leap (440,-330)": {"lip": (440, -330), "pool": (405, -295)},
        "C2 lower leap (400,-290)": {"lip": (400, -290), "pool": (365, -255)},
        "C3 lake lip (500,-390)": {"lip": (500, -390), "pool": (470, -360)},
    }
    report = {"stations": len(st), "candidates": {}}
    for name, c in cands.items():
        lx, lz = c["lip"]
        ly = g_at(H, xs, zs, lx, lz)
        px_, pz_ = c["pool"]
        py = g_at(H, xs, zs, px_, pz_)
        drop = ly - py
        run = math.hypot(px_ - lx, pz_ - lz)
        slope = drop / run
        # the face aspect: downhill direction at the lip
        gx = (g_at(H, xs, zs, lx + 5, lz) - g_at(H, xs, zs, lx - 5, lz)) / 10
        gz = (g_at(H, xs, zs, lx, lz + 5) - g_at(H, xs, zs, lx, lz - 5)) / 10
        aspect = bearing(-gx, -gz)
        mid = (lx, lz, ly + 1.0)   # the lip, 1 m up: the fall's head; the slope below is an open 33 % hillside that today hides nothing
        vis = []
        for i, q in enumerate(st):
            d = math.hypot(mid[0] - q["x"], mid[1] - q["z"])
            if d > 900:
                vis.append(None)
                continue
            b = bearing(mid[0] - q["x"], mid[1] - q["z"])
            el = math.degrees(math.atan2(mid[2] - q["y"], d))
            see = los(H, xs, zs, (q["x"], q["z"], q["y"]), mid)
            rel_sb = (b - q["heading_sb"] + 540) % 360 - 180
            rel_nb = (b - (q["heading_sb"] + 180) + 540) % 360 - 180
            vis.append({"i": i, "s": q["s"], "d": d, "bearing": b, "el": el, "los": see, "sb": see and abs(rel_sb) <= WINDSCREEN, "nb": see and abs(rel_nb) <= WINDSCREEN})
        def runs(key):
            idx = [v["i"] for v in vis if v and v[key]]
            if not idx:
                return []
            groups, cur = [], [idx[0]]
            for i in idx[1:]:
                if i == cur[-1] + 1:
                    cur.append(i)
                else:
                    groups.append(cur)
                    cur = [i]
            groups.append(cur)
            return groups
        info = {}
        for key, label in (("sb", "southbound (east up the valley, then south)"), ("nb", "northbound (north past the corner, then west down the valley)")):
            gr = runs(key)
            n_st = sum(len(g) for g in gr)
            best = None
            for v in vis:
                if v and v[key] and (best is None or v["d"] < best["d"]):
                    best = v
            first = min((v for v in vis if v and v[key]), key=lambda v: v["i"] if key == "sb" else -v["i"], default=None)
            last = max((v for v in vis if v and v[key]), key=lambda v: v["i"] if key == "sb" else -v["i"], default=None)
            info[key] = {"direction": label, "stations_seeing": n_st, "length_m": n_st * 10, "runs": [[g[0], g[-1]] for g in gr],
                         "seconds": {k: round(n_st * 10 / v_, 1) for k, v_ in SPEEDS.items()},
                         "first": None if first is None else {"i": first["i"], "at": [round(st[first["i"]]["x"]), round(st[first["i"]]["z"])], "d": round(first["d"]), "el": round(first["el"], 1), "bearing": round(first["bearing"])},
                         "best": None if best is None else {"i": best["i"], "at": [round(st[best["i"]]["x"]), round(st[best["i"]]["z"])], "d": round(best["d"]), "el": round(best["el"], 1), "bearing": round(best["bearing"])},
                         "last": None if last is None else {"i": last["i"], "at": [round(st[last["i"]]["x"]), round(st[last["i"]]["z"])], "d": round(last["d"]), "el": round(last["el"], 1)},
                         "reveal": "a reveal: hidden then seen" if (first is not None and first["d"] < 300) else "seen from afar: the hillside is open to the road"}
        lit = {}
        for when, (az, el) in SUN.items():
            diff = abs((az - aspect + 540) % 360 - 180)
            lit[when] = "lit (face toward the sun)" if diff < 80 and el > 8 else ("grazing / rim-lit" if diff < 110 or el <= 8 else "in shadow, backlit mist")
        report["candidates"][name] = {"lip": c["lip"], "lip_y": round(ly, 1), "pool": c["pool"], "pool_y": round(py, 1), "natural_drop_m": round(drop, 1), "run_m": round(run), "slope": round(slope, 2),
                                      "face_aspect_deg": round(aspect), "lit": lit, "views": info, "vis_stations": [v["i"] for v in vis if v and (v["sb"] or v["nb"])]}
    # choose: most reveal-like with a real drop: score = stations seeing (both) * drop, penalise distance
    def score(c):
        v = c["views"]
        n_ = v["sb"]["stations_seeing"] + v["nb"]["stations_seeing"]
        return n_ * c["natural_drop_m"]
    ranked = sorted(report["candidates"].items(), key=lambda kv: -score(kv[1]))
    report["ranking"] = [k for k, _ in ranked]
    chosen = ranked[0][0]
    report["chosen"] = chosen
    c = report["candidates"][chosen]
    # the fall's design at the chosen site: a 30 m free fall needs a vertical face where the slope is c["slope"]
    H_free = 30.0
    width_face = 50.0
    wedge_area = 0.5 * H_free * (H_free / max(c["slope"], 0.1))
    cut = wedge_area * width_face
    lip_w = 6.0
    def nappe(q):
        qq = q / lip_w
        return (qq * qq / 9.81) ** (1 / 3)
    report["design"] = {"free_fall_m": H_free, "lip_width_m": lip_w, "lip_y": c["lip_y"], "pool_y": round(c["lip_y"] - H_free, 1), "cascade_below_m": round(c["lip_y"] - H_free - c["pool_y"], 1),
                        "cliff_cut_m3": round(cut), "cliff_face_width_m": width_face, "cut_where": f"the slope below the lip at {c['lip']} over {round(H_free / max(c['slope'], 0.1))} m of run, cut vertical",
                        "alternatives": {"45 m free fall": round(0.5 * 45 * (45 / max(c["slope"], 0.1)) * width_face), "70 m all-in-one": round(0.5 * 70 * (70 / max(c["slope"], 0.1)) * width_face), "20 m free fall": round(0.5 * 20 * (20 / max(c["slope"], 0.1)) * width_face)},
                        "plunge_pool": "12 x 8 m, 2 m deep at the foot of the face; outlet down the existing K-1 bed to the take-off (300,-230) +9.4; the take-off sluice still caps the park at 0.3 m3/s; the K1 spill lies upstream, unaffected",
                        "nappe_thickness_m": {"mean 457 L/s": round(nappe(MEAN_Q), 3), "May 1.08 m3/s": round(nappe(MAY_Q), 3), "late summer 380 L/s": round(nappe(LATE_Q), 3), "design peak 13.6": round(nappe(PEAK_Q), 2)},
                        "look": "457 L/s over a 6 m lip is an 8 cm sheet that breaks into a veil within 10 m of fall and arrives at the pool as spray: a Bridalveil veil; in May (15 cm) a solid white fall; in late summer (7 cm) a thin veil the wind bends; at the 13.6 m3/s peak a roaring 60 cm sheet",
                        "highway_flood": "the pool and the K-1 bed stay east of the highway bridge at (330,-230); the design peak passes under the 12 m bridge as before",
                        "reveal_by_notch": "the K-1 hillside is an open 33 % slope facing the road, so no site on it is naturally hidden; a reveal is made by cutting the fall into a notch: an amphitheatre 60 m wide and 40 m deep into the slope whose side walls hide the veil until a driver is within about 250 m (southbound, from the valley) or until the corner at (300,-226) (northbound); the notch adds about 80,000 m3 to the cliff cut: roughly 150,000 m3 in all for a 30 m fall"}
    with open(os.path.join(out, "falls_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    json.dump({"stations": st, "prof": prof, "sp": sp}, open(os.path.join(folder, "falls_work.json"), "w"))
    for name, c in report["candidates"].items():
        v = c["views"]
        print(f"falls: {name}: lip {c['lip_y']} pool {c['pool_y']} drop {c['natural_drop_m']} slope {c['slope']} aspect {c['face_aspect_deg']}; SB {v['sb']['stations_seeing']} st, NB {v['nb']['stations_seeing']} st; lit {c['lit']}")
    print(f"falls: chosen {chosen}; design {json.dumps(report['design'])[:400]}")
    draw(folder, out, report)
    return report


def draw(folder, out, rep):
    from PIL import Image, ImageDraw
    H, xs, zs, hw = load(folder)
    work = json.load(open(os.path.join(folder, "falls_work.json")))
    st = work["stations"]
    X0, X1, Z0, Z1, sc = 100, 700, -600, -120, 2.0
    W, Hh = int((X1 - X0) * sc), int((Z1 - Z0) * sc)
    img = Image.new("RGB", (W, Hh + 200), (250, 250, 248))
    arr = np.zeros((Hh, W, 3), dtype=np.uint8)
    jj = np.clip(((np.arange(Hh) / sc + Z0 - zs[0]) / 5).astype(int), 0, len(zs) - 1)
    ii = np.clip(((np.arange(W) / sc + X0 - xs[0]) / 5).astype(int), 0, len(xs) - 1)
    Hs = H[jj][:, ii]
    t = np.clip((Hs + 8) / 100, 0, 1)
    arr[..., 0] = (235 - 90 * t).astype(np.uint8)
    arr[..., 1] = (232 - 110 * t).astype(np.uint8)
    arr[..., 2] = (215 - 130 * t).astype(np.uint8)
    band = (np.floor(Hs / 5) != np.floor(np.roll(Hs, 1, axis=0) / 5)) | (np.floor(Hs / 5) != np.floor(np.roll(Hs, 1, axis=1) / 5))
    arr[band] = (190, 180, 160)
    img.paste(Image.fromarray(arr), (0, 0))
    dr = ImageDraw.Draw(img)
    px = lambda x: (x - X0) * sc
    pz = lambda z: (z - Z0) * sc
    dr.line([(px(q["x"]), pz(q["z"])) for q in st], fill=(40, 40, 40), width=5)
    dr.line([(px(x), pz(z)) for x, z in K1], fill=(0, 115, 255), width=4)
    dr.text((px(K1[0][0]) + 6, pz(K1[0][1])), "K-1 creek from lake K1 (+79.7)", fill=(0, 60, 170))
    cols = {"C1": (220, 40, 40), "C2": (230, 140, 20), "C3": (120, 60, 200)}
    for name, c in rep["candidates"].items():
        key = name[:2]
        for i in c["vis_stations"]:
            q = st[i]
            off = {"C1": -8, "C2": 0, "C3": 8}[key]
            dr.rectangle([px(q["x"]) - 3, pz(q["z"]) + off - 3, px(q["x"]) + 3, pz(q["z"]) + off + 3], fill=cols[key])
        lx, lz = c["lip"]
        dr.ellipse([px(lx) - 9, pz(lz) - 9, px(lx) + 9, pz(lz) + 9], outline=cols[key], width=4)
        dr.text((px(lx) + 12, pz(lz) - 8), f"{name}: lip {c['lip_y']}, drop {c['natural_drop_m']} m", fill=cols[key])
    dr.rectangle([px(212) if 212 > X0 else 0, pz(-230), px(222), pz(-120)], outline=(120, 120, 120))
    dr.text((px(110), pz(-225)), "park (north edge z -230; NE corner (222,-230))", fill=(90, 90, 90))
    y = Hh + 10
    dr.text((10, y), "falls_plan: the coast highway (black, stations every 10 m), creek K-1 (azure), three candidate lips and the stations that see each (coloured ticks beside the road: red C1, orange C2, purple C3)", fill=(10, 10, 10))
    for k, (name, c) in enumerate(rep["candidates"].items()):
        v = c["views"]
        dr.text((10, y + 20 + k * 18), f"{name}: SB sees it from {v['sb']['stations_seeing']} stations ({v['sb']['length_m']} m, {v['sb']['seconds']}), NB {v['nb']['stations_seeing']} ({v['nb']['length_m']} m); best SB {v['sb']['best']}; lit: {c['lit']['afternoon 15:30']} afternoon, {c['lit']['morning 09:00']} morning", fill=(20, 20, 20))
    dr.text((10, y + 80), f"chosen: {rep['chosen']}; ranking {rep['ranking']}", fill=(0, 60, 170))
    img.save(os.path.join(out, "falls_plan.png"))
    # profile of K-1 with the chosen fall
    prof, sp = work["prof"], work["sp"]
    W2, H2, pad = 1600, 500, 60
    img = Image.new("RGB", (W2, H2 + pad), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    hmin, hmax = 0, 90
    sx = lambda s: pad + s / sp[-1] * (W2 - 2 * pad)
    sy = lambda h: pad // 2 + H2 - 40 - (h - hmin) / (hmax - hmin) * (H2 - 50)
    for hv in range(0, 91, 10):
        dr.line([pad, sy(hv), W2 - pad, sy(hv)], fill=(225, 225, 225))
        dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
    dr.line([(sx(s), sy(p[2])) for s, p in zip(sp, prof)], fill=(60, 60, 60), width=3)
    c = rep["candidates"][rep["chosen"]]
    d = rep["design"]
    # locate the lip on the profile
    k_lip = int(np.argmin([math.hypot(p[0] - c["lip"][0], p[1] - c["lip"][1]) for p in prof]))
    s_lip = sp[k_lip]
    run = d["free_fall_m"] / max(c["slope"], 0.1)
    dr.polygon([(sx(s_lip), sy(c["lip_y"])), (sx(s_lip), sy(c["lip_y"] - d["free_fall_m"])), (sx(s_lip + run), sy(c["lip_y"] - d["free_fall_m"]))], outline=(220, 40, 40), fill=(250, 200, 200))
    dr.line([(sx(s_lip), sy(c["lip_y"])), (sx(s_lip), sy(c["lip_y"] - d["free_fall_m"]))], fill=(0, 115, 255), width=5)
    dr.text((sx(s_lip) + 6, sy(c["lip_y"]) - 16), f"lip +{c['lip_y']}: {d['free_fall_m']:.0f} m free fall, 6 m wide; the pink wedge is the cliff cut ({d['cliff_cut_m3'] / 1e3:.0f} k m3 over a {d['cliff_face_width_m']:.0f} m face)", fill=(0, 60, 170))
    dr.text((sx(s_lip) + 6, sy(c["lip_y"] - d["free_fall_m"]) + 4), f"plunge pool +{d['pool_y']}, then {d['cascade_below_m']} m of cascades to the natural bed", fill=(0, 60, 170))
    dr.text((pad + 6, pad // 2 + H2 - 34), "falls_profile: creek K-1 from lake K1's spill (left, +79.7) to the take-off (right, +9.4); ground grey; s in m along the creek; the chosen fall in azure", fill=(20, 20, 20))
    for s_ in range(0, int(sp[-1]) + 1, 50):
        dr.text((sx(s_) - 8, pad // 2 + H2 - 20), f"{s_}", fill=(60, 60, 60))
    img.save(os.path.join(out, "falls_profile.png"))
    # table
    rows = [["candidate", "lip y", "natural drop / slope", "aspect", "SB stations / s at 60", "NB stations / s at 60", "best view SB (d, el)", "lit afternoon / morning / sunset", "verdict"]]
    for name, c in rep["candidates"].items():
        v = c["views"]
        rows.append([name, c["lip_y"], f"{c['natural_drop_m']} m / {c['slope']}", c["face_aspect_deg"], f"{v['sb']['stations_seeing']} / {v['sb']['seconds']['60 km/h']}", f"{v['nb']['stations_seeing']} / {v['nb']['seconds']['60 km/h']}",
                     str(v["sb"]["best"]), f"{c['lit']['afternoon 15:30']} / {c['lit']['morning 09:00']} / {c['lit']['sunset (azimuth 294)']}", "CHOSEN" if name == rep["chosen"] else ""])
    widths = [190, 60, 150, 60, 170, 170, 330, 330, 80]
    img = Image.new("RGB", (sum(widths) + 40, 28 * len(rows) + 60), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for r_, row in enumerate(rows):
        x = 20
        yy = 20 + r_ * 28
        dr.line([20, yy - 6, sum(widths) + 20, yy - 6], fill=(225, 225, 225))
        for v, w in zip(row, widths):
            dr.text((x, yy), str(v)[:int(w / 5.6)], fill=(20, 20, 20))
            x += w
    dr.text((20, 28 * len(rows) + 30), "falls_table: viewshed from the highway at 1.2 m eye height, windscreen +-70 deg of the travel direction; SB = southbound (east up the valley), NB = northbound", fill=(90, 90, 90))
    img.save(os.path.join(out, "falls_table.png"))
    print("falls: wrote falls_plan.png, falls_profile.png, falls_table.png")


# ----------------------------------------------------------------------------- Blender: sample and render
def sample(folder):
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    obj = bpy.data.objects["terrain_world"]
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    down = Vector((0, 0, -1))
    xs = np.arange(100.0, 700.1, 5.0)
    zs = np.arange(-600.0, -120.1, 5.0)
    H = np.full((len(zs), len(xs)), np.nan)
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            h = bvh.ray_cast(Vector((x, -z, 2000.0)), down, 6000.0)
            if h[0] is not None:
                H[j, i] = h[0].z
    os.makedirs(folder, exist_ok=True)
    np.savez(os.path.join(folder, "grid5.npz"), H=H, xs=xs, zs=zs)
    o = bpy.data.objects["coast_highway_centreline"]
    pts = [(float(p.co[0]), float(-p.co[1]), float(p.co[2])) for s in o.data.splines for p in s.points]
    json.dump(pts, open(os.path.join(folder, "highway.json"), "w"))
    print(f"falls: sampled {H.shape}; highway {len(pts)} points")


def render(folder, out):
    import bpy
    from mathutils import Vector
    rep = json.load(open(os.path.join(out, "falls_report.json")))
    work = json.load(open(os.path.join(folder, "falls_work.json")))
    st = work["stations"]
    c = rep["candidates"][rep["chosen"]]
    d = rep["design"]
    scene = bpy.context.scene
    obj = bpy.data.objects["terrain_world"]
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()
    # the fall as a temporary azure ribbon (never saved): lip to pool
    cu = bpy.data.curves.new("scratch_fall", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 3.0
    m = bpy.data.materials.new("scratch_fall_mat")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.7, 0.9, 1.0, 1.0)
    nt.links.new(em.outputs[0], o_.inputs[0])
    cu.materials.append(m)
    sp = cu.splines.new("POLY")
    sp.points.add(1)
    lx, lz = c["lip"]
    sp.points[0].co = (lx, -lz, c["lip_y"] + 1.0, 1.0)
    sp.points[1].co = (lx, -lz, c["lip_y"] - d["free_fall_m"], 1.0)
    fo = bpy.data.objects.new("scratch_fall", cu)
    scene.collection.objects.link(fo)
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.75, 0.8, 0.9, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.9, 0.0, -2.3)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0
    cam_data.lens = 28.0
    scene.render.resolution_x, scene.render.resolution_y = 2400, 1350

    def shoot(name, eye, aim):
        e, a = Vector((eye[0], -eye[1], eye[2])), Vector((aim[0], -aim[1], aim[2]))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(out, name)
        bpy.ops.render.render(write_still=True)
        print(f"falls: rendered {scene.render.filepath}")
    mid = (lx, lz, c["lip_y"] - d["free_fall_m"] * 0.5)
    v = c["views"]["sb"]
    for tag, key in (("first_sight", "first"), ("best_view", "best"), ("last_sight", "last")):
        q = st[v[key]["i"]]
        # look along the drive, biased toward the fall
        nxt = st[min(len(st) - 1, v[key]["i"] + 3)]
        aim = ((nxt["x"] + mid[0]) / 2, (nxt["z"] + mid[1]) / 2, (q["y"] + mid[2]) / 2)
        shoot(f"falls_driver_{tag}.png", (q["x"], q["z"], q["y"]), aim)
    b = st[v["best"]["i"]]
    shoot("falls_turnout_view.png", (b["x"] + 6, b["z"] - 12, b["y"] + 0.5), mid)
    print("falls: cameras and the scratch fall were not saved")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--sample" in argv:
        sample(argv[argv.index("--sample") + 1])
    if "--analyse" in argv:
        analyse(argv[argv.index("--analyse") + 1], argv[argv.index("--out") + 1])
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], argv[argv.index("--out") + 1])


if __name__ == "__main__":
    main()
