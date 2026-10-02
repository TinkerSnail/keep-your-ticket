"""The beach-front coast extension, PROPOSAL only (2026-10-01, Christina:
"draw the coast extension next": the shore between the coast highway and the
water moves west into the ocean from south of the lagoon's inlet to the end of
the strip, for cottage grids and shops, kicked back and forth before any
building).

Three phases; the master, ParkPlan, the generator, the game and the maps stay
unchanged, the land is built on a scratch copy:

    # 1. cross-sections of the master seaward of the highway, and its reference curves (Blender)
    Blender --background assets/source/world_terrain_master.blend \
        --python tools/blender/world_terrain_coast_extension.py -- --sample <folder>
    # 2. the two shorelines, areas, sunset rays, conflicts, cross-section plots, JSON (system Python)
    python3 tools/blender/world_terrain_coast_extension.py --design <folder>
    # 3. the land on a scratch copy, reference-style curves, renders (Blender)
    Blender --background --factory-startup \
        --python tools/blender/world_terrain_coast_extension.py -- --build <folder>

Stations run along `highway_path()` (the master's `coast_highway_centreline`)
every STATION m; each cross-section samples the ground along the seaward
normal from LAND_BACK m behind the centreline to SEA_OUT m out. The new
waterline is the highway's seaward edge (HIGHWAY_W / 2) plus the option's
depth plus a smooth sinuous variation, tapered to the existing shore over
TAPER m at both ends. The reclaimed ground is a bench at the existing coast
bench's height falling BENCH_FALL seaward to a beach crest, then a beach at
BEACH_SLOPE through sea level into a shelf at SHELF_SLOPE until it meets the
existing (placeholder) seabed; existing ground is never lowered and the
highway's own ground is never touched.
"""

import json
import math
import os
import shutil
import sys

import numpy as np

try:
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
except ImportError:
    bpy = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DEFAULT_MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
SEA_LEVEL = -7.5
HIGHWAY_W = 31.2
STATION = 20.0
LAND_BACK = 60.0
SEA_OUT = 420.0
XS_STEP = 5.0
Z_FROM, Z_TO = 300.0, 2600.0   # the stretch of highway sampled (Godot z)
OPTIONS = {"A": 100.0, "B": 140.0}   # m of land between the highway's seaward edge and the new waterline
SINUOUS = [(430.0, 12.0, 0.0), (1150.0, 8.0, 1.3)]  # (wavelength m, amplitude m, phase) of the shoreline's variation
TAPER = 200.0
BENCH_FALL = 0.01       # the bench falls 1 % seaward (streets want <= 2-3 %)
BENCH_H = -4.0          # Godot m, 3.5 m above the sea: the reclaimed bench (the existing bench behind it is a bluff at about +6 m Godot, 13.7 m above the sea)
BEACH_W = 30.0          # m of beach between the bench's crest and the waterline (Christina 2026-10-01, "narrower beach"): about 3.3 m of fall, 1:9
                        # alternative recorded, not applied: a 2 m crest at 1:15 over 30 m
BEACH_SLOPE = 1.0 / 10.0   # the beach's nominal gradient (the crest-to-waterline fall over BEACH_W sets the actual one)
SHELF_SLOPE = 1.0 / 15.0
# the strip: from south of the lagoon mouth and the ferry landing to short of the bridge approach
START_Z = 480.0          # first station of new land (the ferry landing ends at z 446, the lagoon mouth at z 345)
END_Z = 2260.0           # last station of new land: before the highway's bend round the spur at (750, 2300), where the station normals fold (the bridge approach hull starts at z 2428)
PIER_HEAD = (-152.0, 6.0)
SUNSET = (280.0, 310.0)


def to_blender(x, y, z):
    return (x, -z, y)


# --- phase 1 ----------------------------------------------------------------

def curve_points(name):
    o = bpy.data.objects.get(name)
    if o is None or o.type != "CURVE":
        return None
    return [(float(p.co[0]), float(p.co[2]), float(-p.co[1])) for sp in o.data.splines for p in sp.points]


def sample(folder):
    os.makedirs(folder, exist_ok=True)
    obj = bpy.data.objects["terrain_world"]
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    down = Vector((0.0, 0.0, -1.0))

    def ground(x, z):
        hit = bvh.ray_cast(Vector((x, -z, 1000.0)), down, 5000.0)
        if hit[0] is None:
            hit = bvh.ray_cast(Vector((x + 2e-3, -z + 2e-3, 1000.0)), down, 5000.0)
        return math.nan if hit[0] is None else float(hit[0].z)

    hw = curve_points("coast_highway_centreline")
    hw = [(p[0], p[2]) for p in hw if Z_FROM <= p[2] <= Z_TO]
    # resample the centreline at STATION
    seg = [math.hypot(hw[k + 1][0] - hw[k][0], hw[k + 1][1] - hw[k][1]) for k in range(len(hw) - 1)]
    s = np.concatenate([[0.0], np.cumsum(seg)])
    st = np.arange(0.0, s[-1], STATION)
    cx = np.interp(st, s, [p[0] for p in hw])
    cz = np.interp(st, s, [p[1] for p in hw])
    tx, tz = np.gradient(cx), np.gradient(cz)
    nrm = np.maximum(np.hypot(tx, tz), 1e-9)
    tx, tz = tx / nrm, tz / nrm
    # the seaward normal: the sea is west of this highway, so the normal points to the side with lower ground
    offs = np.arange(-LAND_BACK, SEA_OUT + XS_STEP / 2, XS_STEP)
    G = np.full((len(st), len(offs)), np.nan)
    nx_, nz_ = np.zeros(len(st)), np.zeros(len(st))
    for k in range(len(st)):
        # left normal (-tz, tx) in Godot x,z; pick whichever side reaches the sea first
        cand = [(-tz[k], tx[k]), (tz[k], -tx[k])]
        best = None
        for n in cand:
            gl = [ground(cx[k] + n[0] * o, cz[k] + n[1] * o) for o in (60.0, 120.0, 200.0)]
            score = sum(1 for g in gl if not np.isnan(g) and g <= SEA_LEVEL + 3.0)
            if best is None or score > best[0]:
                best = (score, n)
        n = best[1]
        nx_[k], nz_[k] = n
        for m, o in enumerate(offs):
            G[k, m] = ground(cx[k] + n[0] * o, cz[k] + n[1] * o)
    refs = {}
    for name in ("coast_highway_centreline", "coast_south_outline", "PROPOSAL_tidal_lagoon", "PROPOSAL_lagoon_bluff_walk",
                 "beach_town_outline", "bridge_approach_footprint", "bridge_main_deck_footprint", "coastal_creek",
                 "street_beach_second_street", "pier", "sunset_water_wedge_280_310", "sunset_bearing_294", "land_reserve"):
        pts = curve_points(name)
        if pts:
            refs[name] = pts
    np.savez(os.path.join(folder, "coast_sections.npz"), st=st, cx=cx, cz=cz, tx=tx, tz=tz, nx=nx_, nz=nz_, offs=offs, G=G)
    with open(os.path.join(folder, "coast_refs.json"), "w") as f:
        json.dump(refs, f)
    print(f"coast_extension: {len(st)} stations x {len(offs)} offsets sampled; refs {sorted(refs)}")


# --- phase 2 ----------------------------------------------------------------

def existing_shore(G, offs):
    """Per station: the offset where the ground first drops under sea level
    seaward of the highway edge, and the bench height between the edge and it."""
    edge = HIGHWAY_W / 2
    shore = np.full(len(G), np.nan)
    bench = np.full(len(G), np.nan)
    for k in range(len(G)):
        row = G[k]
        m0 = int(np.argmin(np.abs(offs - edge)))
        for m in range(m0, len(offs)):
            if not np.isnan(row[m]) and row[m] <= SEA_LEVEL:
                shore[k] = offs[m - 1] + (row[m - 1] - SEA_LEVEL) / (row[m - 1] - row[m]) * XS_STEP if m > m0 and row[m - 1] > SEA_LEVEL else offs[m]
                vals = row[m0:m]
                vals = vals[~np.isnan(vals)]
                bench[k] = float(np.median(vals)) if len(vals) else np.nan
                break
    return shore, bench


def design(folder):
    d = np.load(os.path.join(folder, "coast_sections.npz"))
    st, cx, cz, nx_, nz_, offs, G = d["st"], d["cx"], d["cz"], d["nx"], d["nz"], d["offs"], d["G"]
    with open(os.path.join(folder, "coast_refs.json")) as f:
        refs = json.load(f)
    shore0, bench0 = existing_shore(G, offs)
    edge = HIGHWAY_W / 2
    active = (cz >= START_Z) & (cz <= END_Z)
    # taper weight: 0 outside, 1 inside, smooth over TAPER at both ends (by station distance)
    s_start = float(st[np.argmax(active)])
    s_end = float(st[len(st) - 1 - np.argmax(active[::-1])])

    def weight(s_):
        if s_ < s_start or s_ > s_end:
            return 0.0
        a = min(1.0, (s_ - s_start) / TAPER)
        b = min(1.0, (s_end - s_) / TAPER)
        w = min(a, b)
        return 0.5 * (1 - math.cos(math.pi * w))

    out = {"stations": [], "options": {}, "existing": {}, "start_z": START_Z, "end_z": END_Z, "highway_w": HIGHWAY_W, "bench_h_godot": BENCH_H,
           "bench_above_sea_m": BENCH_H - SEA_LEVEL,
           "bench_fall": BENCH_FALL, "beach_w": BEACH_W, "beach_slope": BEACH_SLOPE, "shelf_slope": SHELF_SLOPE, "taper_m": TAPER,
           "sinuous": SINUOUS}
    ok = ~np.isnan(shore0)
    hw_ground = G[:, int(np.argmin(np.abs(offs - 0.0)))]
    drop = hw_ground - BENCH_H
    out["existing"] = {"highway_ground_godot_m": {"min": float(np.nanmin(hw_ground[active])), "median": float(np.nanmedian(hw_ground[active])),
                                                   "max": float(np.nanmax(hw_ground[active]))},
                       "bluff_from_highway_to_bench_m": {"min": float(np.nanmin(drop[active])), "median": float(np.nanmedian(drop[active])),
                                                         "max": float(np.nanmax(drop[active]))},"land_between_edge_and_water_m": {"min": float(np.nanmin(shore0[ok & active] - edge)),
                                                        "median": float(np.nanmedian(shore0[ok & active] - edge)),
                                                        "max": float(np.nanmax(shore0[ok & active] - edge))},
                       "bench_height_godot_m": {"min": float(np.nanmin(bench0[ok & active])), "median": float(np.nanmedian(bench0[ok & active])),
                                                "max": float(np.nanmax(bench0[ok & active]))},
                       "bench_above_sea_m": float(np.nanmedian(bench0[ok & active]) - SEA_LEVEL),
                       "shore_length_m": float(st[active][-1] - st[active][0])}
    print(f"coast_extension: highway ground {out['existing']['highway_ground_godot_m']}; bluff from the highway down to the new bench {out['existing']['bluff_from_highway_to_bench_m']}")
    print(f"coast_extension: existing land between highway edge and water: {out['existing']['land_between_edge_and_water_m']}; "
          f"bench {out['existing']['bench_height_godot_m']} (median {out['existing']['bench_above_sea_m']:.1f} m above the sea)")
    polys = {}
    for key, depth in OPTIONS.items():
        new_off = np.full(len(st), np.nan)
        for k in range(len(st)):
            w = weight(float(st[k]))
            sin = sum(a * math.sin(2 * math.pi * st[k] / L + ph) for L, a, ph in SINUOUS)
            target = edge + depth + sin
            base = shore0[k] if not np.isnan(shore0[k]) else edge + 35.0
            new_off[k] = base + w * max(0.0, target - base)
        shift = new_off - np.where(np.isnan(shore0), edge + 35.0, shore0)
        # polygon of new land: existing shore line out to the new one, between the first and last changed station
        ch = shift > 0.5
        idx = np.nonzero(ch)[0]
        poly = []
        for k in idx:
            poly.append((float(cx[k] + nx_[k] * shore0[k]), float(cz[k] + nz_[k] * shore0[k])))
        for k in idx[::-1]:
            poly.append((float(cx[k] + nx_[k] * new_off[k]), float(cz[k] + nz_[k] * new_off[k])))
        area = 0.5 * abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))))
        line = [(float(cx[k] + nx_[k] * new_off[k]), float(cz[k] + nz_[k] * new_off[k])) for k in idx]
        length = sum(math.hypot(line[i + 1][0] - line[i][0], line[i + 1][1] - line[i][1]) for i in range(len(line) - 1))
        polys[key] = poly
        # fill volume: the design surface over the existing ground on the station x offset grid
        fill_land = fill_sea = 0.0
        max_fill = 0.0
        for k in idx:
            row = G[k]
            for o in offs:
                if o <= shore0[k]:
                    continue
                h = design_height(o, shore0[k], new_off[k], BENCH_H, row, offs)
                g = np.interp(o, offs, np.where(np.isnan(row), SEA_LEVEL - 40.0, row))
                dh = max(0.0, h - g)
                max_fill = max(max_fill, dh)
                if h > SEA_LEVEL:
                    fill_land += dh * XS_STEP * STATION
                else:
                    fill_sea += dh * XS_STEP * STATION
        out["options"][key] = {"depth_m": depth, "area_ha": area / 1e4, "max_shift_m": float(np.nanmax(shift)),
                               "fill_volume_above_sea_m3": fill_land, "fill_volume_below_sea_m3": fill_sea, "max_fill_m": max_fill,
                               "mean_shift_m": float(np.nanmean(shift[ch])), "new_shore_length_m": length,
                               "from_z": float(cz[idx[0]]), "to_z": float(cz[idx[-1]]), "new_shoreline_godot_xz": line, "polygon_godot_xz": poly,
                               "new_offset_per_station": [float(v) for v in new_off]}
        print(f"coast_extension: option {key}: depth {depth:g} m, area {area / 1e4:.1f} ha, max shift {np.nanmax(shift):.0f} m, "
              f"new shore {length:.0f} m from z {cz[idx[0]]:.0f} to {cz[idx[-1]]:.0f}; fill {fill_land / 1e6:.2f} Mm3 above and "
              f"{fill_sea / 1e6:.2f} Mm3 below sea level, deepest fill {max_fill:.1f} m")
    # sunset: from the pier head and promenade points, the bearing span of the new land
    views = [("pier_head", PIER_HEAD)] + [(f"promenade_z{int(z)}", (-105.0, z)) for z in (60.0, 200.0, 354.0, 430.0)]
    sun = {}
    for key, poly in polys.items():
        sun[key] = {}
        for name, (vx, vz) in views:
            bearings = [(math.degrees(math.atan2(px - vx, -(pz - vz))) + 360.0) % 360.0 for px, pz in poly]
            inside = [b for b in bearings if SUNSET[0] <= b <= SUNSET[1]]
            # the land lies to the south; the bearing nearest the wedge's 280 edge, from below, sets the margin
            below = [b for b in bearings if 90.0 <= b < SUNSET[0]]
            closest = max(below) if below else None
            sun[key][name] = {"blocked": bool(inside), "closest_bearing_deg": closest,
                              "margin_to_280_deg": (None if closest is None else SUNSET[0] - closest),
                              "bearing_span_deg": [min(bearings), max(bearings)]}
        print(f"coast_extension: sunset {key}: " + "; ".join((f"{n}: closest {v['closest_bearing_deg']:.1f} deg, margin {v['margin_to_280_deg']:.1f}" if v["closest_bearing_deg"] is not None else f"{n}: no land west of south") + (" BLOCKED" if v["blocked"] else "") for n, v in sun[key].items()))
    out["sunset"] = sun
    # conflicts: distances from the new shorelines to the references
    def dpoly(x, z, pts, closed):
        best = math.inf
        n = len(pts)
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            ax, az = pts[i][0], pts[i][2]
            bx, bz = pts[(i + 1) % n][0], pts[(i + 1) % n][2]
            vx, vz = bx - ax, bz - az
            L2 = vx * vx + vz * vz
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * vx + (z - az) * vz) / L2))
            best = min(best, math.hypot(x - (ax + t * vx), z - (az + t * vz)))
        return best
    conf = {}
    for key in polys:
        line = out["options"][key]["new_shoreline_godot_xz"]
        c = {}
        for nm, closed in (("bridge_approach_footprint", True), ("bridge_main_deck_footprint", True), ("PROPOSAL_tidal_lagoon", True),
                           ("pier", True), ("coastal_creek", False), ("beach_town_outline", True)):
            if nm in refs:
                c[nm + "_min_m"] = float(min(dpoly(x, z, refs[nm], closed) for x, z in line[::2]))
        c["ferry_landing_note"] = "the ferry landing z 434-446 reaches x -190; the new land starts at z 480 and its taper keeps the berth open"
        c["lagoon_mouth_note"] = "the lagoon mouth and jetties (x -118..-103, z 330-345) lie 135 m north of the first new land"
        c["bay_loop_note"] = "the bay loop arrives at (650, 2535) on the highway's landward side; the new land ends at z 2360 on the seaward side"
        c["railway_note"] = ("the coastal expansion plan puts the railway on the shelf between the highway's southbound lanes and the shore: "
                             "the new land widens that shelf and the rail keeps its line against the highway; the beach town's rail crossing stays")
        conf[key] = c
    out["conflicts"] = conf
    # candidate water outlets (markers, not designs)
    out["water_markers"] = [{"name": "lagoon_canal_outlet", "at_godot_xz": [float(cx[np.argmin(np.abs(cz - 560.0))]), 560.0],
                             "note": "a canal from the lagoon could leave through the new land here, south of the ferry landing"},
                            {"name": "creek_outlet_mid", "at_godot_xz": [float(cx[np.argmin(np.abs(cz - 1300.0))]), 1300.0],
                             "note": "a creek from the hills under the highway (culvert) to the beach"},
                            {"name": "south_green_inlet", "at_godot_xz": [float(cx[np.argmin(np.abs(cz - 2000.0))]), 2000.0],
                             "note": "an inlet by the south green / lookout, where the bluff is lowest"}]
    # cross-section plots at three stations
    out["sections_at_z"] = [700.0, 1400.0, 2100.0]
    for k in range(len(st)):
        out["stations"].append({"s": float(st[k]), "x": float(cx[k]), "z": float(cz[k]), "nx": float(nx_[k]), "nz": float(nz_[k]),
                                "existing_shore_off": None if np.isnan(shore0[k]) else float(shore0[k]),
                                "highway_ground": None if np.isnan(hw_ground[k]) else float(hw_ground[k]),
                                "bench_h": None if np.isnan(bench0[k]) else float(bench0[k])})
    out["offsets"] = [float(o) for o in offs]
    out["ground_rows"] = [[None if np.isnan(v) else float(v) for v in row] for row in G]
    with open(os.path.join(folder, "proposal_coast_extension.json"), "w") as f:
        json.dump(out, f)
    try:
        section_plots(folder, out)
    except ImportError:
        print("coast_extension: PIL missing (Blender's Python); run --design under the system Python for the section plot")


def design_height(off, shore_off0, new_off, bench_h, row, offs, g=None):
    """The reclaimed surface at one offset of one station: existing ground
    kept where it is higher (so the bluff stays and the bench meets it on
    its BENCH_H contour); the bench from the old shore to the beach crest,
    the beach to the new waterline, the shelf beyond. `g` is the existing
    height at the point (a vertex's own, when applying to a mesh); without
    it the station row is read. Beyond the sampled SEA_OUT nothing changes."""
    if off > SEA_OUT:
        return g if g is not None else SEA_LEVEL - 40.0
    if g is None:
        g = np.interp(off, offs, np.where(np.isnan(row), SEA_LEVEL - 40.0, row))
    # the beach narrows with the land in the tapers (at most 60 % of the land's width), so a
    # bench always exists and the beach never spans the whole width at sea level
    beach_w = min(BEACH_W, max(0.0, 0.6 * (new_off - shore_off0)))
    crest_off = new_off - beach_w
    if off <= shore_off0:
        # landward of the old shore the bench runs level into the bluff and meets it on its
        # BENCH_H contour; the old shoreline cells, which sat at the seabed, come up with it
        # (Christina, 2026-10-01, "fill it"); anything already higher, the bluff, the highway, stays
        return max(g, bench_h)
    if off <= crest_off:
        h = bench_h - BENCH_FALL * (off - shore_off0)
    elif off <= new_off:
        h_crest = bench_h - BENCH_FALL * (crest_off - shore_off0)
        h = h_crest - (off - crest_off) / max(beach_w, 1e-6) * (h_crest - SEA_LEVEL)
    else:
        h = SEA_LEVEL - SHELF_SLOPE * (off - new_off)
    return max(g, h) if off <= new_off else max(g, h)


def section_plots(folder, out):
    from PIL import Image, ImageDraw
    offs = np.array(out["offsets"])
    W, Hh, pad = 1800, 360, 50
    zs = out["sections_at_z"]
    img = Image.new("RGB", (W, Hh * len(zs) + pad), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for i, zq in enumerate(zs):
        k = int(np.argmin([abs(q["z"] - zq) for q in out["stations"]]))
        q = out["stations"][k]
        row = np.array([math.nan if v is None else v for v in out["ground_rows"][k]])
        top = i * Hh + pad // 2
        hmin, hmax = -25.0, 25.0
        sx = lambda o: pad + (o - offs[0]) / (offs[-1] - offs[0]) * (W - 2 * pad)
        sy = lambda h: top + Hh - 40 - (min(max(h, hmin), hmax) - hmin) / (hmax - hmin) * (Hh - 50)
        dr.rectangle([pad, top, W - pad, top + Hh - 40], outline=(120, 120, 120))
        for hv in range(-20, 30, 10):
            dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
            dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
        dr.line([pad, sy(SEA_LEVEL), W - pad, sy(SEA_LEVEL)], fill=(120, 170, 230), width=2)
        dr.rectangle([sx(-HIGHWAY_W / 2), sy(hmax), sx(HIGHWAY_W / 2), sy(hmin)], fill=(235, 235, 225))
        dr.text((sx(0) - 25, top + 6), "highway", fill=(90, 90, 90))
        for key, col in (("A", (220, 120, 40)), ("B", (160, 60, 200))):
            opt = out["options"][key]
            new_off = opt["new_offset_per_station"][k]
            sh0 = q["existing_shore_off"] or HIGHWAY_W / 2 + 35.0
            bh = BENCH_H
            pts = [(sx(o), sy(design_height(o, sh0, new_off, bh, row, offs))) for o in offs if o >= 0]
            dr.line(pts, fill=col, width=3)
            dr.line([sx(new_off), sy(hmin), sx(new_off), sy(hmax)], fill=col)
        gpts = [(sx(o), sy(v)) for o, v in zip(offs, row) if not np.isnan(v)]
        dr.line(gpts, fill=(60, 60, 60), width=2)
        dr.text((pad + 6, top + 4), f"station z {q['z']:.0f}: existing ground (grey), sea -7.5 (blue), option A (orange) and B (purple); "
                f"offset from the highway centreline in m, heights in Godot m", fill=(20, 20, 20))
        for o in range(0, int(offs[-1]) + 1, 50):
            dr.text((sx(o) - 8, top + Hh - 36), f"{o}", fill=(60, 60, 60))
    img.save(os.path.join(folder, "proposal_coast_sections.png"))
    print(f"coast_extension: wrote {os.path.join(folder, 'proposal_coast_sections.png')}")


# --- phase 3 ----------------------------------------------------------------

def build(folder, master=DEFAULT_MASTER):
    with open(os.path.join(folder, "proposal_coast_extension.json")) as f:
        out = json.load(f)
    assets = os.path.join(ROOT, "assets")
    if os.path.commonpath([os.path.abspath(folder), assets]) == assets:
        raise SystemExit("coast_extension: the folder may not be under assets/")
    scratch = os.path.join(folder, "PROPOSAL_coast_extension.blend")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    scene = bpy.context.scene
    obj = bpy.data.objects["terrain_world"]
    me = obj.data
    me.polygons.foreach_set("material_index", np.zeros(len(me.polygons), dtype=np.int32))
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co0 = co.copy()
    coll = bpy.data.collections.get("Reference_proposals")
    if coll is None:
        coll = bpy.data.collections.new("Reference_proposals")
        bpy.data.collections["Reference"].children.link(coll)
    offs = np.array(out["offsets"])
    stations = out["stations"]
    sx_ = np.array([q["x"] for q in stations])
    sz_ = np.array([q["z"] for q in stations])
    snx = np.array([q["nx"] for q in stations])
    snz = np.array([q["nz"] for q in stations])
    tx, tz = -snz, snx  # the tangent
    ss = np.array([q["s"] for q in stations])

    def apply(option):
        opt = out["options"][option]
        new_off = np.array(opt["new_offset_per_station"])
        heights = co0.copy()
        changed = np.zeros(n, dtype=bool)
        X, Z = co0[:, 0], -co0[:, 1]
        # vertices within the strip's box
        box = (Z >= out["start_z"] - 300) & (Z <= out["end_z"] + 300) & (X <= 1000.0)
        for v in np.nonzero(box)[0]:
            # station: nearest by projection on the tangent
            dx, dz = X[v] - sx_, Z[v] - sz_
            k = int(np.argmin(np.hypot(dx, dz)))  # the nearest station; the strip is a gentle curve
            along = dx[k] * tx[k] + dz[k] * tz[k]
            off = dx[k] * snx[k] + dz[k] * snz[k]
            if abs(along) > STATION * 0.75 or off < 0:
                continue
            q = stations[k]
            if q["existing_shore_off"] is None:
                continue
            sh0, bh = q["existing_shore_off"], BENCH_H
            if new_off[k] - sh0 < 0.5 or off <= sh0:
                continue
            row = np.array([math.nan if r is None else r for r in out["ground_rows"][k]])
            h = design_height(off, sh0, new_off[k], bh, row, offs, g=float(co0[v, 2]))
            if h > co0[v, 2] + 1e-3:
                heights[v, 2] = h
                changed[v] = True
        return heights, changed

    results = {}
    for key in ("A", "B"):
        heights, changed = apply(key)
        results[key] = {"vertices_raised": int(changed.sum()), "max_raise_m": float((heights[:, 2] - co0[:, 2])[changed].max()) if changed.any() else 0.0,
                        "volume_m3": float(np.sum((heights[:, 2] - co0[:, 2])[changed]) * 25.0 * 25.0 * 0.4)}
        print(f"coast_extension: option {key}: {results[key]}")
    with open(os.path.join(folder, "proposal_coast_build.json"), "w") as f:
        json.dump(results, f)

    def curve(name, pts, colour, bevel, note=""):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = bevel
        cu.bevel_resolution = 0
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        o_ = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = colour
        nt.links.new(em.outputs[0], o_.inputs[0])
        cu.materials.append(m)
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*to_blender(*p), 1.0)
        o = bpy.data.objects.new(name, cu)
        o["kyt_proposal"] = True
        o["kyt_reference"] = True
        o["kyt_collision"] = "none"
        if note:
            o["kyt_note"] = note
        coll.objects.link(o)
        return o

    curves = {}
    for key, col in (("A", (1.0, 0.55, 0.1, 1.0)), ("B", (0.65, 0.2, 0.9, 1.0))):
        line = out["options"][key]["new_shoreline_godot_xz"]
        curves[key] = curve(f"PROPOSAL_coast_extension_{key}_shoreline", [(x, SEA_LEVEL + 1.5, z) for x, z in line], col, 5.0,
                            f"option {key}: {out['options'][key]['depth_m']:g} m of land between the highway's seaward edge and the water")
    for mk in out["water_markers"]:
        x, z = mk["at_godot_xz"]
        curve(f"PROPOSAL_coast_extension_marker_{mk['name']}", [(x - 25, SEA_LEVEL + 4.0, z), (x + 25, SEA_LEVEL + 4.0, z)], (0.3, 0.5, 1.0, 1.0), 4.0, mk["note"])

    # renders
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.7854, 0.0, -2.0944)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0
    outputs = []

    def shoot(name):
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        outputs.append(scene.render.filepath)
        print(f"coast_extension: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2400):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = to_blender(cx, 5000.0, cz)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            scene.render.resolution_x, scene.render.resolution_y = px, int(px * ez / ex)
        else:
            scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
        shoot(name)

    def oblique(name, eye, aim, lens=35.0):
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector(to_blender(*eye)), Vector(to_blender(*aim))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
        shoot(name)

    ca = me.color_attributes["height_shade"]
    col0 = np.empty(n * 4)
    ca.data.foreach_get("color", col0)
    col0 = col0.reshape(-1, 4)

    def set_heights(h):
        me.vertices.foreach_set("co", h.ravel())
        # raised vertices keep the seabed's review colour otherwise: sand below -3 m Godot, grass above
        col = col0.copy()
        raised = h[:, 2] > co0[:, 2] + 1e-3
        land = raised & (h[:, 2] > SEA_LEVEL)
        col[land & (h[:, 2] <= -3.0)] = (0.88, 0.82, 0.62, 1.0)
        col[land & (h[:, 2] > -3.0)] = (0.70, 0.80, 0.52, 1.0)
        ca.data.foreach_set("color", col.ravel())
        me.update()

    # existing shore first (both lines drawn, ground untouched)
    top_down("proposal_coast_top_existing.png", -450.0, 950.0, 250.0, 2650.0)
    for key in ("A", "B"):
        heights, _ = apply(key)
        set_heights(heights)
        for k2, c in curves.items():
            c.hide_render = k2 != key
        top_down(f"proposal_coast_top_{key}.png", -450.0, 950.0, 250.0, 2650.0)
        top_down(f"proposal_coast_inlet_end_{key}.png", -400.0, 200.0, 250.0, 850.0, px=1800)
        top_down(f"proposal_coast_south_end_{key}.png", 200.0, 900.0, 1950.0, 2650.0, px=1800)
    heights, _ = apply("A")
    set_heights(heights)
    for k2, c in curves.items():
        c.hide_render = k2 != "A"
    oblique("proposal_coast_oblique_A_from_sea.png", (-700.0, 160.0, 1500.0), (250.0, 0.0, 1350.0), lens=35.0)
    bpy.ops.wm.save_mainfile()  # the scratch copy holds option A's land
    with open(os.path.join(folder, "proposal_coast_renders.json"), "w") as f:
        json.dump({"renders": outputs, "scratch": scratch, "scratch_holds": "option A"}, f)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--sample" in argv:
        sample(argv[argv.index("--sample") + 1])
    elif "--design" in argv:
        design(argv[argv.index("--design") + 1])
    elif "--build" in argv:
        folder = argv[argv.index("--build") + 1]
        master = argv[argv.index("--master") + 1] if "--master" in argv else DEFAULT_MASTER
        build(folder, master)
    else:
        raise SystemExit("coast_extension: --sample <folder> | --design <folder> | --build <folder>")


if __name__ == "__main__":
    main()
