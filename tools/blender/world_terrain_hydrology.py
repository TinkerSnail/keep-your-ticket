"""Hydrology of the park and its hills, from the world terrain master (2026-10-01, Christina:
"a creek from the mountains running through the park to the sea ... the park needs at least
one pond ... try the creek/canals first, then explore the hollows").

Diagram-level analysis, no change to the master. Two steps:

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_hydrology.py -- --sample <folder>
      ray-samples the mounted surface (decks and buildings count as ground) on a 10 m grid over
      x -400..1000, z -1000..1000 (the park and the crescent range to its crest) and a 4 m grid
      over the park x -260..260, z -360..360; writes hydro_grid10.npz / hydro_grid4.npz.

    python3 tools/blender/world_terrain_hydrology.py --analyse <folder> --out <renders>
      priority-flood sink filling (Barnes 2014), D8 flow direction and accumulation, catchments
      by sea exit, hollows (depressions the raw surface holds, depth and volume), the plan's own
      water drawn over it; writes hydro_report.json and the hydro_* PNG diagrams.

Everything in Godot world coordinates (x east, z south, heights y; sea -7.5, plaza 0).
"""
import heapq
import json
import math
import os
import sys

import numpy as np

SEA = -7.5
GRIDS = {"hydro_grid10": (-400.0, 1000.0, -1000.0, 1000.0, 10.0), "hydro_grid4": (-260.0, 260.0, -360.0, 360.0, 4.0)}
# the plan's own water (world coordinates; from the digest of park-sections.html, park_plan.gd, gen_props.gd, the entrance plan)
PLAN_WATER = {
    "Coastal Creek 05A": [(-48, 22), (-54, 29), (-59, 37), (-62, 44), (-70, 50), (-79, 55.1), (-88, 56.6), (-96, 56.6), (-104, 56.6)],
    "rain pond (r 7, y -4.3)": (-88, 56.6),
    "Grove pond (r 5.4)": (-19.5, -118),
    "D3 drainage low (-0.3)": (-18, 174.45), "D4 (+2.93)": (105.55, 162.05), "D5 (+3.63)": (170.8, 145), "D6 (-0.5)": (53.75, -200.33),
    "Squirt Garden KG1": (31, 117.1), "plaza fountain": (0, 0), "NT-1 trough (-5.17)": (-63, -2), "NT-2 (protected)": (86, 0),
    "lagoon (plan, -7.5)": [(-110, 327), (-86, 326), (-77, 324.5), (-66, 323.5), (-57, 314), (-39, 315.3), (-17, 322), (17, 322), (33, 311), (42, 308), (60, 302.6), (69, 300.8),
                            (73, 286), (78.5, 262), (88, 256), (100, 262), (112, 256), (114, 238), (113, 222), (114, 200), (122, 184), (137, 178), (151, 175), (163, 176), (170, 184), (172, 205), (170, 232), (166, 262), (166, 283), (150, 297)],
    "E landing basin (candidate)": [(-77, 300), (-61, 300), (-61, 323), (-77, 323)],
}
LANDS = {  # world frames from the digest (park-sections.html through rebuild_expand_point)
    "Entrance": (-48, 48, 83, 196), "Plaza": (-82, 175, -78, 57), "Boardwalk": (-200, -44, -215, 88), "Fairground": (-88, 8, 18, 185),
    "Kiddieland": (-5, 181, 42, 185), "High Terrace": (35, 217, -123, 64), "Frontier": (48, 196, -194, -45), "Grove": (-55, 81, -214, -45), "Headland": (-229, 18, -337, -148),
}
PROTECT = {"NT-1": (-74, -55, -15, 12), "NT-2 ellipse (86,0) 42x36": None, "Plaza 104 m": (-52, 52, -52, 52), "entrance axis |x|<13, z 50..228": (-13, 13, 50, 228)}


# ----------------------------------------------------------------------------- sampling (Blender)
def sample(folder):
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    obj = bpy.data.objects["terrain_world"]
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    down = Vector((0.0, 0.0, -1.0))
    os.makedirs(folder, exist_ok=True)
    for name, (x0, x1, z0, z1, step) in GRIDS.items():
        xs = np.arange(x0, x1 + 0.01, step)
        zs = np.arange(z0, z1 + 0.01, step)
        H = np.full((len(zs), len(xs)), np.nan)
        for j, z in enumerate(zs):
            for i, x in enumerate(xs):
                hit = bvh.ray_cast(Vector((x, -z, 2000.0)), down, 6000.0)
                if hit[0] is None:
                    hit = bvh.ray_cast(Vector((x + 1e-2, -z + 1e-2, 2000.0)), down, 6000.0)
                if hit[0] is not None:
                    H[j, i] = hit[0].z
        np.savez(os.path.join(folder, name + ".npz"), H=H, xs=xs, zs=zs)
        print(f"hydrology: {name}: {H.shape}, {np.isnan(H).sum()} misses, y {np.nanmin(H):.1f}..{np.nanmax(H):.1f}")


# ----------------------------------------------------------------------------- analysis (system Python)
def priority_flood(H, sea_mask):
    """Barnes et al. 2014: fill every depression to its spill level; cells draining to the sea stay as they are."""
    nz, nx = H.shape
    F = H.copy()
    filled = np.zeros_like(H, dtype=bool)
    heap = []
    for j in range(nz):
        for i in range(nx):
            if sea_mask[j, i] or j in (0, nz - 1) or i in (0, nx - 1):
                heapq.heappush(heap, (H[j, i], j, i))
                filled[j, i] = True
    while heap:
        h, j, i = heapq.heappop(heap)
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                jj, ii = j + dj, i + di
                if 0 <= jj < nz and 0 <= ii < nx and not filled[jj, ii]:
                    filled[jj, ii] = True
                    if F[jj, ii] < h:
                        F[jj, ii] = h + 1e-4
                    heapq.heappush(heap, (F[jj, ii], jj, ii))
    return F


def flow_d8(F, step):
    nz, nx = F.shape
    dj_, di_ = [], []
    best = np.full(F.shape, -1, dtype=np.int32)
    slope = np.zeros(F.shape)
    neigh = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    dist = [math.sqrt(2) * step if a and b else step for a, b in neigh]
    for k, (dj, di) in enumerate(neigh):
        shifted = np.full(F.shape, np.inf)
        js = slice(max(0, -dj), nz - max(0, dj))
        is_ = slice(max(0, -di), nx - max(0, di))
        shifted[js, is_] = F[js.start + dj: js.stop + dj, is_.start + di: is_.stop + di]
        s = (F - shifted) / dist[k]
        better = s > slope
        slope[better] = s[better]
        best[better] = k
    return best, neigh


def accumulate(F, best, neigh):
    nz, nx = F.shape
    order = np.argsort(F.ravel())[::-1]
    acc = np.ones(F.shape)
    exit_id = -np.ones(F.shape, dtype=np.int64)
    for flat in order:
        j, i = divmod(int(flat), nx)
        k = best[j, i]
        if k < 0:
            exit_id[j, i] = flat
            continue
        jj, ii = j + neigh[k][0], i + neigh[k][1]
        acc[jj, ii] += acc[j, i]
    # exits propagate downstream: resolve by following pointers (memoised)
    exit_id = -np.ones(nz * nx, dtype=np.int64)

    def find_exit(flat):
        path = []
        cur = flat
        while exit_id[cur] < 0:
            j, i = divmod(cur, nx)
            k = best[j, i]
            if k < 0:
                exit_id[cur] = cur
                break
            path.append(cur)
            cur = (j + neigh[k][0]) * nx + (i + neigh[k][1])
        e = exit_id[cur]
        for p in path:
            exit_id[p] = e
        return e
    for flat in range(nz * nx):
        if exit_id[flat] < 0:
            find_exit(flat)
    return acc, exit_id.reshape(F.shape)


def label_regions(mask):
    nz, nx = mask.shape
    lab = np.zeros(mask.shape, dtype=np.int32)
    n = 0
    for j in range(nz):
        for i in range(nx):
            if mask[j, i] and lab[j, i] == 0:
                n += 1
                stack = [(j, i)]
                lab[j, i] = n
                while stack:
                    a, b = stack.pop()
                    for dj in (-1, 0, 1):
                        for di in (-1, 0, 1):
                            aa, bb = a + dj, b + di
                            if 0 <= aa < nz and 0 <= bb < nx and mask[aa, bb] and lab[aa, bb] == 0:
                                lab[aa, bb] = n
                                stack.append((aa, bb))
    return lab, n


def land_of(x, z):
    for name, (x0, x1, z0, z1) in LANDS.items():
        if x0 <= x <= x1 and z0 <= z <= z1:
            return name
    return "outside the park" if not (-212 <= x <= 222 and -230 <= z <= 220) else "park (between frames)"


def analyse(folder, out):
    os.makedirs(out, exist_ok=True)
    report = {}
    grids = {}
    for name in GRIDS:
        d = np.load(os.path.join(folder, name + ".npz"))
        H, xs, zs = d["H"], d["xs"], d["zs"]
        step = float(xs[1] - xs[0])
        H = np.where(np.isnan(H), SEA - 20.0, H)
        sea = H <= SEA + 0.05
        F = priority_flood(H, sea)
        best, neigh = flow_d8(F, step)
        best[sea] = -1   # the sea is the terminal exit: flow stops at the first sea cell
        acc, exit_id = accumulate(F, best, neigh)
        cell = step * step
        depth = F - H
        hollow_mask = (depth > 0.3) & ~sea
        lab, n = label_regions(hollow_mask)
        hollows = []
        for k in range(1, n + 1):
            m = lab == k
            area = m.sum() * cell
            if area < (0.05e4 if step < 5 else 0.2e4):
                continue
            jj, ii = np.where(m)
            cx, cz = float(xs[ii].mean()), float(zs[jj].mean())
            dmax = float(depth[m].max())
            vol = float(depth[m].sum() * cell)
            kmin = np.argmin(H[m])
            hollows.append({"centre": [round(cx), round(cz)], "area_ha": round(area / 1e4, 2), "max_depth_m": round(dmax, 2), "volume_m3": round(vol),
                            "spill_level": round(float(F[m].max()), 2), "floor": round(float(H[m].min()), 2), "floor_at": [float(xs[ii[kmin]]), float(zs[jj[kmin]])],
                            "land": land_of(cx, cz), "cells": int(m.sum())})
        hollows.sort(key=lambda h: -h["volume_m3"])
        grids[name] = {"H": H, "F": F, "xs": xs, "zs": zs, "acc": acc, "exit": exit_id, "sea": sea, "depth": depth, "step": step, "best": best, "neigh": neigh}
        report[name] = {"hollows": hollows[:40], "step_m": step}
        print(f"hydrology: {name}: {n} depressions, {len(hollows)} reported; largest {hollows[0] if hollows else None}")
    # catchments on the 10 m grid, by shore exit
    g = grids["hydro_grid10"]
    H, F, xs, zs, acc, exit_id, sea = g["H"], g["F"], g["xs"], g["zs"], g["acc"], g["exit"], g["sea"]
    nz, nx = H.shape
    cell = g["step"] ** 2
    exits = {}
    for flat, cnt in zip(*np.unique(exit_id[~sea], return_counts=True)):
        j, i = divmod(int(flat), nx)
        exits[int(flat)] = {"x": float(xs[i]), "z": float(zs[j]), "area_ha": cnt * cell / 1e4, "edge": bool(j in (0, nz - 1) or i in (0, nx - 1))}
    # name the exits that matter
    named = {"north cove / headland (z < -230, x < -100)": lambda e: e["z"] < -230 and e["x"] < -100 and not e["edge"],
             "Boardwalk shore z -230..220 (Coastal Creek outfall at z 57)": lambda e: -230 <= e["z"] <= 220 and e["x"] < -50 and not e["edge"],
             "south of the park to the lagoon site z 220..420": lambda e: 220 < e["z"] <= 420 and e["x"] < -50 and not e["edge"],
             "beach front z 420..1000": lambda e: 420 < e["z"] and e["x"] < 100 and not e["edge"],
             "north edge of the sample (z -1000)": lambda e: e["edge"] and e["z"] <= -990,
             "east/south edge of the sample": lambda e: e["edge"] and e["z"] > -990}
    catch = {}
    for key, fn in named.items():
        sel = [f for f, e in exits.items() if fn(e)]
        catch[key] = {"area_ha": round(sum(exits[f]["area_ha"] for f in sel), 1), "exits": len(sel),
                      "largest_exits": sorted([(round(exits[f]["x"]), round(exits[f]["z"]), round(exits[f]["area_ha"], 1)) for f in sel], key=lambda t: -t[2])[:6]}
    report["catchments_by_exit"] = catch
    # specific points: area draining through (or nearest to) the plan's water
    def area_at(x, z, r=15.0):
        i0, i1 = int((x - r - xs[0]) / g["step"]), int((x + r - xs[0]) / g["step"]) + 1
        j0, j1 = int((z - r - zs[0]) / g["step"]), int((z + r - zs[0]) / g["step"]) + 1
        sub = acc[max(0, j0):j1, max(0, i0):i1]
        k = np.unravel_index(np.argmax(sub), sub.shape)
        return float(sub.max() * cell / 1e4), [float(xs[max(0, i0) + k[1]]), float(zs[max(0, j0) + k[0]])]
    pts = {"Coastal Creek head (-48, 22)": (-48, 22), "Coastal Creek outfall (-104, 57)": (-104, 57), "rain pond (-88, 57)": (-88, 57),
           "Grove pond (-19.5, -118)": (-19.5, -118), "lagoon NE lobe / approach valley (140, 200)": (140, 200), "lagoon west body (-70, 350)": (-70, 350),
           "D3 (-18, 174)": (-18, 174), "D4 (106, 162)": (106, 162), "D5 (171, 145)": (171, 145), "D6 (54, -200)": (54, -200),
           "north cove (-150, -300)": (-150, -300), "east hills col (420, 370)": (420, 370)}
    report["accumulation_at_plan_water_ha"] = {k: {"area_ha": round(a, 1), "at": at} for k, (a, at) in ((k, area_at(*v)) for k, v in pts.items())}
    # the main channels: cells with accumulation over 20 ha, as polylines downstream from their heads
    channels = []
    thr = 20e4 / cell
    big = acc > thr
    heads = []
    for j in range(1, nz - 1):
        for i in range(1, nx - 1):
            if big[j, i] and not any(big[j + dj, i + di] and g["best"][j + dj, i + di] >= 0 and (j + dj + g["neigh"][g["best"][j + dj, i + di]][0], i + di + g["neigh"][g["best"][j + dj, i + di]][1]) == (j, i)
                                      for dj in (-1, 0, 1) for di in (-1, 0, 1) if (dj or di)):
                heads.append((j, i))
    for j, i in heads:
        path = []
        seen = set()
        while 0 <= j < nz and 0 <= i < nx and not sea[j, i] and (j, i) not in seen:
            seen.add((j, i))
            path.append((float(xs[i]), float(zs[j]), round(float(H[j, i]), 1), round(float(acc[j, i] * cell / 1e4), 1)))
            k = g["best"][j, i]
            if k < 0:
                break
            j, i = j + g["neigh"][k][0], i + g["neigh"][k][1]
        if len(path) > 3:
            channels.append(path)
    channels.sort(key=lambda p: -p[-1][3])
    report["channels_over_20ha"] = [{"head": c[0][:3], "mouth": c[-1][:3], "mouth_area_ha": c[-1][3], "length_m": round(len(c) * g["step"]), "points": c[::max(1, len(c) // 40)]} for c in channels[:12]]
    with open(os.path.join(out, "hydro_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    np.savez(os.path.join(folder, "hydro_analysis10.npz"), F=F, acc=acc, exit=exit_id, depth=g["depth"])
    np.savez(os.path.join(folder, "hydro_analysis4.npz"), F=grids["hydro_grid4"]["F"], acc=grids["hydro_grid4"]["acc"], depth=grids["hydro_grid4"]["depth"])
    for k, v in report["catchments_by_exit"].items():
        print(f"hydrology: catchment {k}: {v['area_ha']} ha, exits {v['largest_exits'][:3]}")
    for k, v in report["accumulation_at_plan_water_ha"].items():
        print(f"hydrology: at {k}: {v['area_ha']} ha")
    return report, grids


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--sample" in argv:
        sample(argv[argv.index("--sample") + 1])
    if "--analyse" in argv:
        analyse(argv[argv.index("--analyse") + 1], argv[argv.index("--out") + 1])


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------------- diagrams (system Python, PIL)
AZURE = (0, 115, 255)
SPINES = {  # creek spine candidates, world x,z; style: dash length (0 = solid)
    "K  north-valley branch along the park's north shelf": {"pts": [(300, -230), (200, -228), (150, -230), (100, -222), (54, -200), (0, -222), (-40, -215), (-62, -204), (-88, -190), (-108, -200)],
                                                             "dash": 0, "width": 5, "fork": [(54, -200), (20, -205)]},
    "L  south-valley creek to the lagoon, Kiddieland fork": {"pts": [(610, 200), (400, 200), (320, 200), (260, 250), (230, 300), (200, 320), (160, 330), (140, 350), (110, 360), (60, 370), (0, 370), (-70, 365), (-110, 360)],
                                                              "dash": 18, "width": 5, "fork": [(230, 300), (205, 240), (190, 170), (171, 145), (140, 150), (106, 162), (115, 185), (120, 200)]},
    "M  Coastal Creek, extended into the Fairground only": {"pts": [(-18, 174), (-40, 160), (-42, 110), (-44, 60), (-48, 22), (-62, 44), (-79, 55), (-96, 57), (-104, 57), (-108, 57)],
                                                             "dash": 6, "width": 3, "fork": []},
}
PONDS = [  # rank, name, centre, radius (m, drawn), note
    (1, "P1 Kiddieland pond chain: D5 (+3.6) and D4 (+2.9) saucers, 0.3 + 0.2 ha, fed by L's fork", (140, 152), 28),
    (2, "P2 Grove low at (-40,-130): 0.3-0.5 ha at 0..-1 behind the bluff notch, the park's own 9 ha runoff", (-30, -128), 24),
    (3, "P3 north-shelf pond at D6 (54,-200) -0.5, 0.3 ha, fed by K", (54, -200), 20),
    (4, "P4 valley pond (275,-252) +9.4, 0.6 ha, 1.5 m, beside the north channel (outside the park)", (275, -252), 22),
    (5, "P5 upper lake (292,706) +51..66, 2.0 ha, 14 m deep: L's source lake (outside)", (292, 706), 40),
    (0, "X  Grove bluff notch (-48,-148): 4 m 'hollow' = the bluff cut, data/structure, not a pond", (-48, -148), 10),
]


def draw(folder, out):
    from PIL import Image, ImageDraw
    d = np.load(os.path.join(folder, "hydro_grid10.npz"))
    H, xs, zs = d["H"], d["xs"], d["zs"]
    a = np.load(os.path.join(folder, "hydro_analysis10.npz"))
    acc, exit_id, depth = a["acc"], a["exit"], a["depth"]
    rep = json.load(open(os.path.join(out, "hydro_report.json")))
    X0, X1, Z0, Z1 = -400.0, 1000.0, -1000.0, 1000.0
    sc = 0.9  # px per m
    W, Hh = int((X1 - X0) * sc), int((Z1 - Z0) * sc)
    px = lambda x: (x - X0) * sc
    pz = lambda z: (z - Z0) * sc

    def base(title):
        # height shading: sea blue, land from pale to brown, 10 m contours
        img = Image.new("RGB", (W, Hh + 140), (250, 250, 248))
        arr = np.zeros((Hh, W, 3), dtype=np.uint8)
        jj = np.clip(((np.arange(Hh) / sc + Z0 - zs[0]) / 10).astype(int), 0, len(zs) - 1)
        ii = np.clip(((np.arange(W) / sc + X0 - xs[0]) / 10).astype(int), 0, len(xs) - 1)
        Hs = H[jj][:, ii]
        sea = Hs <= SEA + 0.05
        t = np.clip((Hs + 8) / 300.0, 0, 1)
        arr[..., 0] = (235 - 90 * t).astype(np.uint8)
        arr[..., 1] = (232 - 110 * t).astype(np.uint8)
        arr[..., 2] = (215 - 130 * t).astype(np.uint8)
        band = (np.floor(Hs / 10) != np.floor(np.roll(Hs, 1, axis=0) / 10)) | (np.floor(Hs / 10) != np.floor(np.roll(Hs, 1, axis=1) / 10))
        arr[band & ~sea] = (180, 170, 150)
        arr[sea] = (150, 185, 215)
        img.paste(Image.fromarray(arr), (0, 0))
        dr = ImageDraw.Draw(img)
        for name, (x0, x1, z0, z1) in LANDS.items():
            dr.rectangle([px(x0), pz(z0), px(x1), pz(z1)], outline=(120, 120, 120))
            dr.text((px(x0) + 3, pz(z0) + 2), name, fill=(80, 80, 80))
        dr.rectangle([px(-212), pz(-230), px(222), pz(220)], outline=(60, 60, 60), width=2)
        dr.text((px(-212) + 4, pz(220) + 4), "park program envelope x -212..222, z -230..220", fill=(60, 60, 60))
        # the plan's water
        for key, v in PLAN_WATER.items():
            if isinstance(v, list):
                dr.line([(px(x), pz(z)) for x, z in v] + ([(px(v[0][0]), pz(v[0][1]))] if "lagoon" in key or "basin" in key else []), fill=(150, 60, 200), width=2)
                dr.text((px(v[0][0]) + 4, pz(v[0][1]) - 12), key, fill=(120, 40, 170))
            else:
                x, z = v
                dr.ellipse([px(x) - 4, pz(z) - 4, px(x) + 4, pz(z) + 4], outline=(150, 60, 200), width=2)
                dr.text((px(x) + 6, pz(z) - 6), key, fill=(120, 40, 170))
        dr.text((10, Hh + 8), title, fill=(10, 10, 10))
        return img, dr

    # 1. flow and catchments
    img, dr = base("hydro_flow_catchments: priority-flood filled surface of the master (10 m), D8 flow accumulation (blue, > 2 ha thin, > 20 ha thick), catchments by sea exit, hollows, the plan's water (purple)")
    nz, nx = H.shape
    groups = {"north cove": ((230, 120, 60), lambda x, z: z < -230 and x < -100), "Boardwalk shore": ((60, 160, 90), lambda x, z: -230 <= z <= 220 and x < -50),
              "lagoon site": ((220, 170, 40), lambda x, z: 220 < z <= 420 and x < -50), "beach front": ((160, 100, 200), lambda x, z: z > 420 and x < 100)}
    ex = exit_id
    for name, (col, fn) in groups.items():
        sel = np.zeros(H.shape, dtype=bool)
        for flat in np.unique(ex):
            j, i = divmod(int(flat), nx)
            if fn(float(xs[i]), float(zs[j])) and not (j in (0, nz - 1) or i in (0, nx - 1)):
                sel |= ex == flat
        jj, ii = np.where(sel & (H > SEA))
        for j, i in zip(jj[::1], ii[::1]):
            dr.rectangle([px(xs[i]) - 4, pz(zs[j]) - 4, px(xs[i]) + 4, pz(zs[j]) + 4], outline=col)
    for j in range(nz):
        for i in range(nx):
            A = acc[j, i] * 100 / 1e4
            if A > 2 and H[j, i] > SEA:
                r = 2 if A < 20 else 4
                dr.ellipse([px(xs[i]) - r, pz(zs[j]) - r, px(xs[i]) + r, pz(zs[j]) + r], fill=(0, 90, 220))
    for h in rep["hydro_grid10"]["hollows"]:
        x, z = h["centre"]
        r = math.sqrt(h["area_ha"] * 1e4 / math.pi) * sc
        dr.ellipse([px(x) - r, pz(z) - r, px(x) + r, pz(z) + r], outline=(200, 40, 40), width=2)
        dr.text((px(x) + r + 2, pz(z) - 6), f"hollow {h['area_ha']} ha, {h['max_depth_m']:.0f} m deep, floor {h['floor']:.0f}", fill=(170, 30, 30))
    c = rep["catchments_by_exit"]
    y = Hh + 28
    for key, (col, _) in groups.items():
        k = [kk for kk in c if key.split()[0].lower() in kk.lower()][0]
        dr.rectangle([10, y, 30, y + 12], outline=col, width=2)
        dr.text((36, y), f"{k}: {c[k]['area_ha']} ha; main exits {c[k]['largest_exits'][:3]}", fill=(20, 20, 20))
        y += 18
    dr.text((10, y), "The park (shelf at 0) lies between two valleys: the north valley (70 ha) to the north cove and the south valley (47 ha) to the lagoon site; the east hills' water bypasses the park. Range bowls east are closed basins of the mesh.", fill=(20, 20, 20))
    img.save(os.path.join(out, "hydro_flow_catchments.png"))

    # 2. creek spines
    img, dr = base("hydro_creek_spines: candidate creek spines K (solid), L (long dash) and M (short dash), all azure per the colour key; forks thinner; the plan's water purple; crossings = bridges (red ticks)")
    for name, s in SPINES.items():
        pts = [(px(x), pz(z)) for x, z in s["pts"]]
        if s["dash"] == 0:
            dr.line(pts, fill=AZURE, width=s["width"])
        else:
            for i in range(len(pts) - 1):
                (x0, y0), (x1, y1) = pts[i], pts[i + 1]
                L = math.hypot(x1 - x0, y1 - y0)
                n = max(1, int(L / s["dash"]))
                for k in range(0, n, 2):
                    t0, t1 = k / n, min(1.0, (k + 1) / n)
                    dr.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=AZURE, width=s["width"])
        if s["fork"]:
            dr.line([(px(x), pz(z)) for x, z in s["fork"]], fill=AZURE, width=max(2, s["width"] - 2))
        x, z = s["pts"][0]
        dr.text((px(x) + 6, pz(z) - 14), name, fill=(0, 70, 170))
    for (x, z), lab in [((120, -185), "Grand Circuit"), ((-42, -181), "route B"), ((-52, -171), "S1"), ((107, 137), "route D"), ((139, 151), "S3 / Grand Circuit"), ((150, 280), "arrival arm (bridge in plan)"), ((-18, 128), "route C"), ((-96, 57), "CB2"), ((-76, 53), "CB1")]:
        dr.line([px(x) - 6, pz(z) - 6, px(x) + 6, pz(z) + 6], fill=(220, 30, 30), width=3)
        dr.text((px(x) + 8, pz(z) + 2), lab, fill=(180, 20, 20))
    for (x0, x1, z0, z1), lab in [((-74, -55, -15, 12), "NT-1"), ((-52, 52, -52, 52), "Plaza datum"), ((-13, 13, 50, 228), "arrival axis, never crossed")]:
        dr.rectangle([px(x0), pz(z0), px(x1), pz(z1)], outline=(230, 60, 60), width=2)
        dr.text((px(x0) + 2, pz(z1) + 2), lab, fill=(200, 40, 40))
    dr.ellipse([px(86 - 42), pz(0 - 36), px(86 + 42), pz(0 + 36)], outline=(230, 60, 60), width=2)
    dr.text((px(86) - 10, pz(0) - 6), "NT-2", fill=(200, 40, 40))
    dr.text((10, Hh + 28), "K: take-off from the north channel at (300,-230) +9.4, west along the shelf at 0 to the Boardwalk's north end, 420 m, fall 15 m (3.6 %); 3 bridges. Cannot climb into the Grove mound (+4).", fill=(20, 20, 20))
    dr.text((10, Hh + 46), "L: the real south-valley creek, 47 ha, +10.6 at (320,200) to the lagoon site; fork at (230,300) +7 into Kiddieland's saucers D5 (+3.6) and D4 (+2.9) and back down the slough to the NE lobe (0): 2 bridges + the plan's arrival bridge.", fill=(20, 20, 20))
    dr.text((10, Hh + 64), "M: Coastal Creek has no natural catchment (0 ha); extending it upstream reaches only D3 in the Fairground; further east it would cross the arrival axis or the Plaza: not possible.", fill=(20, 20, 20))
    img.save(os.path.join(out, "hydro_creek_spines.png"))

    # 3. ponds
    img, dr = base("hydro_pond_candidates: real hollows and designed lows as pond sites, ranked (azure fill = candidate, red = data/structure); figures in the summary table")
    for rank, name, (x, z), r in PONDS:
        rr = r * sc
        col = AZURE if rank else (220, 40, 40)
        dr.ellipse([px(x) - rr, pz(z) - rr, px(x) + rr, pz(z) + rr], outline=col, width=3)
        dr.text((px(x) + rr + 3, pz(z) - 6), name, fill=(0, 70, 170) if rank else (180, 20, 20))
    img.save(os.path.join(out, "hydro_pond_candidates.png"))

    # 4. summary table
    rows = [
        ["catchment / feature", "area or size", "level(s)", "finding", "confidence"],
        ["north valley -> north cove", "70 ha", "+93 head, valley floor +10, cove -6", "the hills' main drainage; passes the park's NE corner at (300,-230) +9.4; a +17 ridge keeps it off the park", "high"],
        ["south valley -> lagoon site", "47 ha", "+91 head, +10.6 at (320,200), +6 at (200,320), -7.5 lagoon", "the lagoon's natural feeder (the plan's slough / NE lobe); the arrival arm bridges it", "high"],
        ["Boardwalk shore (park shelf)", "19 ha", "0 shelf, -6 band", "the park's own runoff: 9 ha out of the Grove notch at z -140, 6 ha at z 150 (Fairground)", "medium (flat shelf, D8 paths indicative)"],
        ["Coastal Creek 05A", "0 ha natural", "-0.13 head to -5.9 outfall", "a designed drain of the plateau; no hill water reaches it", "high"],
        ["Grove pond / low", "9 ha runoff", "0 at the pond, spill -0.06", "a real low behind the bluff notch; the 4 m 'hollow' at (-48,-148) is the bluff cut", "medium"],
        ["north shelf beyond Grove/Frontier", "about 4 ha at -0.2", "0; ridge +17 north; D6 -0.5", "real flat shelf, open to the west; it does NOT collect the hills' water", "high"],
        ["Kiddieland saucers D4, D5", "0.2 / 0.4 ha rims", "+2.9 / +3.6", "designed lows 3 m above the entrance; reachable by a fork from the south valley at +7", "high"],
        ["range bowls (730,206), (600,-471), (292,706)", "4.3 / 3.5 / 2.0 ha", "62-92, 57-80, 51-66", "closed basins of the range mesh; (292,706) sits in L's catchment as a possible source lake", "low-medium (mesh artefacts possible)"],
        ["ponds in the park (picks)", "P1 Kiddieland 0.5 ha; P2 Grove 0.3-0.5 ha; P3 shelf 0.3 ha", "+3; 0..-1; -0.5", "P1 fed by L's fork, P2 by park runoff + a K lift, P3 by K", "proposal"],
    ]
    widths = [260, 330, 380, 760, 260]
    img = Image.new("RGB", (sum(widths) + 40, 30 * len(rows) + 60), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for r_, row in enumerate(rows):
        x = 20
        y = 20 + r_ * 30
        dr.line([20, y - 6, sum(widths) + 20, y - 6], fill=(220, 220, 220))
        for v, w in zip(row, widths):
            dr.text((x, y), v[:int(w / 5.6)], fill=(20, 20, 20) if r_ else (0, 0, 0))
            x += w
    dr.text((20, 30 * len(rows) + 30), "hydro_summary: master terrain sampled 10 m (park and range) and 4 m (park); priority-flood; sea -7.5; plaza 0; areas from the filled surface", fill=(90, 90, 90))
    img.save(os.path.join(out, "hydro_summary_table.png"))
    print("hydrology: wrote hydro_flow_catchments.png, hydro_creek_spines.png, hydro_pond_candidates.png, hydro_summary_table.png")


if __name__ == "__main__" and "--draw" in sys.argv:
    argv = sys.argv
    draw(argv[argv.index("--draw") + 1], argv[argv.index("--out") + 1])
