"""Canal proposals D, E and D+E, PROPOSAL only (2026-10-01, Christina: C "seems kind of
weird and not integrated into the park very well"; "arrival by water sounds awesome too").

D, the cascade-fed canal: the park's water story continued. NT-1's niche fountain at the
foot of the Cascading Staircases (the trough, surface -5.17 m Godot, blind: no outflow is
modelled today) overflows over a weir into a head basin in the shore band south of the
monument's band, and a canal runs south along the shore band's landward strip, through
the waterfront lawn, to the tidal lagoon. Coastal Creek (05A) crosses the head basin's
site and would discharge into it.
E, arrival by water: a landing basin in the lagoon's north-west corner at the foot of the
bank below the belvedere's west garden path, beside the arrival axis, with a step-free
ramp to the bluff-top walk and the gate.
D+E: D's canal ends in E's basin; one gate at the basin's mouth.

Everything here is a proposal: master, ParkPlan, generator, game and maps unchanged.
NT-1 is a protected anchor: nothing in it moves; the one thing D asks of it (an outflow
from the trough) is flagged for Christina's approval and has a no-touch alternative.

    python3 tools/blender/world_terrain_proposals_canals_DE.py --analyse <folder>
        (system Python; needs <folder>/park_raster10.npz from the earlier canal study)
    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_proposals_canals_DE.py -- --render <folder>
        (saves a scratch copy PROPOSAL_canals_DE.blend beside the raster, never the master)
"""
import json
import math
import os
import shutil
import sys

import numpy as np

SEA = -7.5
LAGOON = -7.5
TIDE = 0.5                 # m, assumed muted range inside the Beach Road gates (ocean +-0.6)
SHORE_TOP = -6.0
TROUGH_TOP = -5.17         # NT-1's niche trough: node trough_water at y -5.26, 0.18 thick (west_stair.tscn)
BOWL_TOP = -3.88           # the bowl above it (bowl_water)
STAIR_FOOT = (-69.5, -2.0)
NT1_BAND_Z = (-34.0, 16.0)  # BLUFF_TOP_FROM_Z .. BLUFF_TOP_TO_Z, the monument's walkable band
NT1_CLEAR = 25.0           # m kept between the band and any new water (the earlier study's rule)
WALL_X = -63.0             # CASCADE_WALL_X, the niche face
DEPTH = {"canal": 1.5, "basin": 2.0}
WIDTH_D = 8.0              # two paddle boats (2.5 m) abreast, or the 4 m glass-bottom boat one way with passing at the basins
CANAL_X = -70.0            # centreline: between the back lane (x -74, service) and the frontage backs (x -64)
HEAD_BASIN = {"x": (-78.0, -62.0), "z": (41.0, 63.0)}       # D's head basin, 16 x 22 m, north wall at NT1_BAND_Z[1] + NT1_CLEAR
E_BASIN = {"x": (-77.0, -61.0), "z": (300.0, 323.0)}        # E's landing basin, 16 x 23 m, mouth on the lagoon's north shore at z 323
LAWN_Z = (220.0, 300.0)    # the waterfront lawn / front-road corner, ground about 0: walls, 9 m deep
PIER_HEAD = (-152.0, 6.0)
PIER_ROOT = (-108.0, 6.0)
WHEEL = (-111.6, -16.0, 13.2)
CREEK = [(-48.0, 22.0), (-54.0, 29.0), (-59.0, 37.0), (-62.0, 44.0), (-70.0, 50.0), (-79.0, 54.0), (-88.0, 55.0), (-96.0, 55.0), (-104.0, 55.0)]
CROWN_CORNER = (-58.0, 261.0, 25.0)   # the front road's west corner arc, centre and radius (entrance plan)
BEACH_ROAD_X = -83.0
FOOTBRIDGE = (-76.8, 321.6)
BATHHOUSE_X = -60.0
GATE = (0.0, 150.0)
Q0_BAND = {"x": (-20.0, 20.0), "z": (140.0, 304.0)}

LEGS = {
    "D": [
        {"name": "NT-1 weir and runnel: trough (-5.17) to the head basin's north wall, 43 m along the bluff foot (needs approval: NT-1 water)", "pts": [(-61.0, -1.0), (-61.0, 41.0)], "level": TROUGH_TOP, "pipe": True},
        {"name": "head basin in the shore band, 16 x 22 m, walls; Coastal Creek enters from the east; dock on the west quay", "basin": HEAD_BASIN, "level": LAGOON},
        {"name": "shore band canal south, walls, 8 m, bed -9 in the -6 floor; swings west at z 170 to pass the west parking field 4 m clear", "pts": [(CANAL_X, 63.0), (CANAL_X, 170.0), (-76.0, 185.0), (-76.0, 220.0)], "level": LAGOON, "walls": True},
        {"name": "under the front road's west end (z 236) and through the lawn to the basin: D1 open with walls 9 m high and a road bridge, D2 an 80 m culvert, the road untouched", "pts": [(-76.0, 220.0), (-76.0, 236.0), (-73.0, 300.0)], "level": LAGOON, "walls": True, "d2_culvert": True},
        {"name": "lagoon basin (E's basin) to the lagoon's north shore", "basin": E_BASIN, "level": LAGOON},
    ],
    "E": [
        {"name": "landing basin at the lagoon's north-west corner, 14 x 23 m, walls, bed -9.5, mouth 14 m on the lagoon at z 323", "basin": E_BASIN, "level": LAGOON},
    ],
}


def bilinear(H, xs, zs, x, z):
    fx = (x - xs[0]) / (xs[1] - xs[0])
    fz = (z - zs[0]) / (zs[1] - zs[0])
    i0 = int(np.clip(math.floor(fx), 0, len(xs) - 2))
    j0 = int(np.clip(math.floor(fz), 0, len(zs) - 2))
    tx, tz = fx - i0, fz - j0
    q = H[j0:j0 + 2, i0:i0 + 2]
    if np.isnan(q).any():
        return float(np.nanmean(q)) if not np.isnan(q).all() else math.nan
    return float((q[0, 0] * (1 - tx) + q[0, 1] * tx) * (1 - tz) + (q[1, 0] * (1 - tx) + q[1, 1] * tx) * tz)


def basin_volume(H, xs, zs, b, bed):
    (x0, x1), (z0, z1) = b["x"], b["z"]
    vol = 0.0
    gmax = -1e9
    for x in np.arange(x0 + 1.0, x1, 2.0):
        for z in np.arange(z0 + 1.0, z1, 2.0):
            g = bilinear(H, xs, zs, x, z)
            gmax = max(gmax, g)
            vol += max(0.0, g - bed) * 4.0
    return vol, gmax


def analyse(folder):
    d = np.load(os.path.join(folder, "park_raster10.npz"))
    H, xs, zs = d["H"], d["xs"], d["zs"]
    out = {"datum": {"plaza": 0.0, "sea": SEA, "lagoon": LAGOON, "tide_assumed_m": TIDE, "shore_band": SHORE_TOP, "nt1_trough_surface": TROUGH_TOP,
                     "nt1_bowl_surface": BOWL_TOP, "nt1_foot_court": SHORE_TOP, "weir_fall_m": TROUGH_TOP - LAGOON,
                     "weir_fall_range_with_tide_m": [TROUGH_TOP - LAGOON - TIDE, TROUGH_TOP - LAGOON + TIDE]},
           "nt1": {"stair_foot": STAIR_FOOT, "band_z": NT1_BAND_Z, "clearance_rule_m": NT1_CLEAR,
                   "water_today": "the niche fountain: a spout into a bowl (-3.88) and a trough (-5.17) on the niche floor; blind, no outflow or drain is modelled; "
                                  "the court in front is the shore band at -6",
                   "head_basin_north_wall_z": HEAD_BASIN["z"][0], "clearance_band_to_basin_m": HEAD_BASIN["z"][0] - NT1_BAND_Z[1],
                   "clearance_stair_foot_to_basin_m": math.hypot(0.0, HEAD_BASIN["z"][0] - STAIR_FOOT[1]),
                   "clearance_trough_to_basin_m": HEAD_BASIN["z"][0] - (-2.0),
                   "runnel": "a buried 43 m runnel from the trough's south end along the bluff foot (x -61) to the basin's north wall, under the frontage's south strip; "
                             "it lies inside the band z -2..16 on the bluff foot: a change to NT-1's water that needs approval",
                   "no_touch_alternative": "the weir at the basin's north wall is fed by Coastal Creek's outfall and the lagoon's own water; the cascade's trough stays a closed "
                                           "recirculating fountain; the story reads the same from the dock (the weir is on the cascade's axis side) without a pipe into NT-1"},
           "options": {}}
    for key, legs in LEGS.items():
        total_len = total_vol = vol_walls = vol_d2 = 0.0
        max_cut = 0.0
        prof = []
        s_acc = 0.0
        rows = []
        for leg in legs:
            level = leg["level"]
            if "basin" in leg:
                b = leg["basin"]
                bed = level - DEPTH["basin"]
                vol, gmax = basin_volume(H, xs, zs, b, bed)
                L = b["z"][1] - b["z"][0]
                # the profile crosses the basin along its length at the canal's x
                for z in np.arange(b["z"][0], b["z"][1] + 0.01, 2.0):
                    x = min(max(CANAL_X, b["x"][0] + 1), b["x"][1] - 1)
                    g = bilinear(H, xs, zs, x, z)
                    prof.append({"s": s_acc + (z - b["z"][0]), "x": x, "z": float(z), "ground": g, "water": level, "bed": bed, "kind": "basin"})
                rows.append({"name": leg["name"], "length_m": L, "area_m2": (b["x"][1] - b["x"][0]) * L, "water_level": level, "bed": bed, "cut_volume_m3": vol, "max_cut_m": gmax - bed})
                total_len += L
                total_vol += vol
                vol_walls += vol
                vol_d2 += vol
                max_cut = max(max_cut, gmax - bed)
                s_acc += L
                continue
            pts = leg["pts"]
            bed = level - DEPTH["canal"]
            seg_len = vol = vol_w = 0.0
            leg_max = 0.0
            for i in range(len(pts) - 1):
                a, b_ = pts[i], pts[i + 1]
                L = math.hypot(b_[0] - a[0], b_[1] - a[1])
                n = max(2, int(L / 4))
                for k in range(n):
                    t = k / n
                    x, z = a[0] + t * (b_[0] - a[0]), a[1] + t * (b_[1] - a[1])
                    g = bilinear(H, xs, zs, x, z)
                    cut = max(0.0, g - bed)
                    if not leg.get("pipe"):
                        leg_max = max(leg_max, cut)
                        vol += (WIDTH_D * cut + cut * cut) * (L / n)   # 1:1 side slopes
                        vol_w += (WIDTH_D * cut) * (L / n)             # vertical walls
                    prof.append({"s": s_acc + seg_len + t * L, "x": x, "z": z, "ground": g, "water": level, "bed": bed if not leg.get("pipe") else level - 0.6,
                                 "kind": "pipe" if leg.get("pipe") else "canal", "cut": cut})
                seg_len += L
            rows.append({"name": leg["name"], "length_m": seg_len, "water_level": level, "bed": bed, "cut_volume_m3_1to1": vol, "cut_volume_m3_walls": vol_w, "max_cut_m": leg_max,
                         "pipe": bool(leg.get("pipe")), "walls": bool(leg.get("walls"))})
            total_len += seg_len if not leg.get("pipe") else 0.0
            total_vol += vol
            vol_walls += vol_w
            vol_d2 += 0.0 if leg.get("d2_culvert") else vol_w
            max_cut = max(max_cut, leg_max)
            s_acc += seg_len
        out["options"][key] = {"legs": rows, "length_m": total_len, "cut_volume_m3_1to1": total_vol, "cut_volume_m3_walls": vol_walls, "max_cut_depth_m": max_cut, "profile": prof}
        if key == "D":
            out["options"][key]["cut_volume_m3_D2_culvert_lawn"] = vol_d2
            out["options"][key]["d2_culvert_length_m"] = LAWN_Z[1] - LAWN_Z[0]
        print(f"canals_DE: {key}: {total_len:.0f} m, cut {total_vol / 1e3:.1f} k m3 at 1:1 / {vol_walls / 1e3:.1f} k m3 with walls, deepest {max_cut:.1f} m")
    D, E = out["options"]["D"], out["options"]["E"]
    out["options"]["DE"] = {"length_m": D["length_m"], "cut_volume_m3_walls": D["cut_volume_m3_walls"], "cut_volume_m3_1to1": D["cut_volume_m3_1to1"],
                            "max_cut_depth_m": D["max_cut_depth_m"],
                            "note": "D already ends in E's basin, so D+E is D with E's landing, ramp and gate: one network, one gate at the basin's mouth"}
    # geometry checks
    creek_hit = [p for p in CREEK if HEAD_BASIN["x"][0] <= p[0] <= HEAD_BASIN["x"][1] and HEAD_BASIN["z"][0] <= p[1] <= HEAD_BASIN["z"][1]]
    cz = CROWN_CORNER[1] - math.sqrt(CROWN_CORNER[2] ** 2 - (CANAL_X - CROWN_CORNER[0]) ** 2)
    bearings = []
    for z in np.arange(41.0, 323.0, 10.0):
        b = (math.degrees(math.atan2(CANAL_X - PIER_HEAD[0], -(z - PIER_HEAD[1]))) + 360.0) % 360.0  # bearing from north, x east, -z north
        bearings.append(b)
    out["checks"] = {
        "sunset_wedge_280_310_from_pier_head": {"canal_bearings_from_pier_head_deg": [round(min(bearings)), round(max(bearings))], "crosses": any(280 <= b <= 310 for b in bearings),
                                                "note": "the whole canal lies east-south-east of the pier head, 90 to 170 degrees; the wedge is open water to the west"},
        "pier_root_to_head_basin_m": math.hypot(PIER_ROOT[0] - HEAD_BASIN["x"][0], PIER_ROOT[1] - HEAD_BASIN["z"][0]),
        "wheel_rim_to_head_basin_m": math.hypot(WHEEL[0] - HEAD_BASIN["x"][0], WHEEL[1] - HEAD_BASIN["z"][0]) - WHEEL[2],
        "west_arch_rim_view": "the arch at (-39, -2) looks west down the axis z -2 to the wheel; the head basin's north wall is 43 m south of the axis and 3 m below the court, outside the 6 m arch's frame",
        "coastal_creek_points_inside_head_basin": creek_hit, "coastal_creek_note": "05A's creek corridor (-48,22)->(-104,55) crosses the basin's site: its controlled waterfront outfall becomes an outfall into the basin (a second small fall, east side)",
        "crown_corner_crossing_z": cz, "crown_corner_note": "the front road's west corner arc crosses the canal at about z %.0f: a road bridge, 8 m span" % cz,
        "bluff_top_walk_crossing": "the bluff-top walk leaves the garden-path turn at (-64.4, 297.8) for (-75, 313.5): it crosses the basin's north end: a footbridge over the canal's mouth into the basin, or the walk goes round the basin's quay",
        "beach_road_clearance_m": E_BASIN["x"][0] - (BEACH_ROAD_X + 3.5), "footbridge_clearance_m": E_BASIN["x"][0] - FOOTBRIDGE[0],
        "bathhouse_clearance_m": BATHHOUSE_X - E_BASIN["x"][1],
        "q0_band": "the basin at x -75..-61, z 300..323 is 41 m west of the Q0 band |x| < 20; the canal at x -70 is 50 m west of it: outside; from the crown's west corner the water appears beside the departure arm",
        "belvedere": "the belvedere (+5.5, x -16..16, z 304..317) is 45 m east of the basin; its view back over the lagoon gains a quay and boats in the north-west corner",
        "shore_band_section": "the canal takes the 8 m strip between the back lane (x -74, the service side) and the frontage backs (x -64): the back lane keeps its line on the canal's west quay, "
                              "every Boardwalk access from the frontage to the bluff foot and route B's north return cross it on footbridges (two in z 63..220 per the earlier study, the count is the atlas's)",
        "rail_trestle": "the trestle (70,290)->(0,388) is 70 m east of the basin: no crossing; the beach-town line on Shore Street's median is 70 m south",
        "nt2_plaza": "NT-2 and the plaza datum are untouched: nothing here is east of the bluff foot or above -5.17",
        "entrance_untouched": {
            "rule": "the car entrance stays exactly as it is (Christina, 2026-10-01); the water arrival is a second way in beside it",
            "existing_within_40m": [
                {"element": "west parking field x -68..-13, z 179.5..222", "nearest_m": -68.0 - (-76.0 + WIDTH_D / 2), "note": "the canal swings to x -76 at z 170 to pass it; not touched"},
                {"element": "the front road z 236, x -80..80 (its west end)", "nearest_m": 0.0, "note": "D1 crosses it on an 8 m road bridge in its last 10 m (a change to the road); D2 passes in a culvert beneath it: the road surface untouched. D2 is the entrance-untouched form"},
                {"element": "the arrival palms x +-11.5, z 140..224", "nearest_m": 11.5 - 0 + 56.0, "note": "about 60 m east of the canal; the walk passes the west field's north edge, no palm foot touched"},
                {"element": "lamp banners x -44, z 265/283 (moved with the field in the plan; existing at the field)", "nearest_m": 24.0, "note": "clear"},
                {"element": "the existing drop-off bay x 4..24, z 228..232", "nearest_m": 76.0, "note": "clear"},
                {"element": "Beach Road (departure arm) x about -83, z 261..320", "nearest_m": -77.0 - (BEACH_ROAD_X + 3.5), "note": "the basin's west wall is 2.5 m from the road's east edge: a quay wall, the road untouched"},
                {"element": "the arcade / turnstile axis x +-13, the apron and entrance street z about 140..175", "nearest_m": 55.0, "note": "never crossed; the walk joins the precinct at the west field's north-west corner (-68, 180) and reaches the allee opening at (-13, 170)"},
                {"element": "the approach road and turning circle (east, x > 90)", "nearest_m": 160.0, "note": "clear"},
            ],
            "join_point": "the walk from the landing joins the existing entrance precinct at the west field's north-west corner (-68, 180), then the field's north edge to the allee opening at (-13, 170)",
            "sightlines": "Q0 (arrival from the car, the band |x| < 20 from z 304 to the gate) is 50 m east of the canal and 41 m east of the basin: unchanged. The package 06 views Q1..Q6 are in the park; nothing here is in them. "
                          "The departure view along Beach Road gains the basin and boats on its left; nothing is harmed",
        },
    }
    # E's walking connection
    ramp_len = (0.0 - SHORE_TOP) * 12.0
    wpts = [(-61.0, 310.0), (-70.0, 300.0), (-70.0, 236.0), (-68.0, 180.0), (-13.0, 170.0), (0.0, 150.0)]
    walk_field = ramp_len + sum(math.hypot(wpts[i + 1][0] - wpts[i][0], wpts[i + 1][1] - wpts[i][1]) for i in range(len(wpts) - 1))
    walk_belv = ramp_len + math.hypot(-64.4 - (-61.0), 297.8 - 310.0) + math.hypot(-16 - (-64.4), 310 - 297.8) + 12.0 + (293 - GATE[1])
    out["E_landing"] = {"quay_level": SHORE_TOP, "quay_height_over_water_m": SHORE_TOP - LAGOON, "landing": "a floating pontoon on gangways in the basin's east side (as the boating centre's)",
                        "ramp": f"1:12 from the quay at -6 to the bluff-top walk at 0: {ramp_len:.0f} m in two switchbacks on the basin's east bank, plus a stair",
                        "walk_to_gate_step_free_m": walk_field, "walk_to_gate_via_belvedere_m": walk_belv,
                        "boats": "paddle boats (2.5 m) and a water taxi (4 m) fit the 14 m basin; the 10 m glass-bottom boat berths bow-in and backs out, it cannot turn inside",
                        "gate": "none needed for level (the basin is inside the Beach Road gates); a 14 m stop-log or sector gate at the mouth to isolate the canal for cleaning"}
    out["levels"] = {"canal_and_basins": LAGOON, "tide_range_assumed": TIDE, "weir": f"a fixed weir at the head basin's north wall: {TROUGH_TOP - LAGOON:.2f} m fall from the trough's surface, {TROUGH_TOP - LAGOON - TIDE:.1f} to {TROUGH_TOP - LAGOON + TIDE:.1f} m with the tide",
                     "flow_assumption": "the niche fountain recirculates; its make-up is assumed 20 L/s (a garden cascade), which turns D's 4,600 m3 over in 2.7 days; the lagoon's gate cycle (open on the ebb at the mouth) flushes it once a tide: an assumption, not a measurement",
                     "lock": "none: canal, basins and lagoon share one level"}
    out["comparison"] = {
        "A": {"length_m": 638, "cut_k_m3": 122, "bridges": 7, "gates_locks": "2 gates", "nt1_clearance_m": 25, "integration": "shore loop + outlet; the outlet leg is a culvert under the town bluff"},
        "C": {"length_m": 418, "cut_k_m3": 13, "bridges": 3, "gates_locks": "1 gate + culvert", "nt1_clearance_m": 25, "integration": "a Boardwalk pair fed by a culvert; no park water story"},
        "D": {"length_m": round(D["length_m"]), "cut_k_m3": round(D["cut_volume_m3_walls"] / 1e3, 1), "bridges": 4, "gates_locks": "1 gate (basin mouth), weir", "nt1_clearance_m": NT1_CLEAR,
              "integration": "fountain -> cascade -> weir -> canal -> lagoon; dock at the cascade; creek joins"},
        "E": {"length_m": round(E["length_m"]), "cut_k_m3": round(E["cut_volume_m3_walls"] / 1e3, 1), "bridges": 0, "gates_locks": "optional stop-log", "nt1_clearance_m": "n/a",
              "integration": "arrival landing below the belvedere; 260 m step-free to the gate"},
        "D+E": {"length_m": round(D["length_m"]), "cut_k_m3": round(D["cut_volume_m3_walls"] / 1e3, 1), "bridges": 4, "gates_locks": "1 gate (basin mouth), weir", "nt1_clearance_m": NT1_CLEAR,
                "integration": "one network: boating centre <-> arrival basin <-> park shore; out-and-back, not a loop"},
    }
    with open(os.path.join(folder, "proposal_canals_DE.json"), "w") as f:
        json.dump(out, f)
    plots(folder, out)
    return out


def plots(folder, out):
    from PIL import Image, ImageDraw
    for key in ("D", "E"):
        prof = out["options"][key]["profile"]
        if not prof:
            continue
        W, H, pad = 1800, 420, 60
        img = Image.new("RGB", (W, H + pad), (250, 250, 248))
        dr = ImageDraw.Draw(img)
        s_max = max(p["s"] for p in prof)
        hmin, hmax = -11.0, 3.0
        sx = lambda s: pad + s / max(s_max, 1) * (W - 2 * pad)
        sy = lambda h: pad // 2 + H - 40 - (min(max(h, hmin), hmax) - hmin) / (hmax - hmin) * (H - 50)
        dr.rectangle([pad, pad // 2, W - pad, pad // 2 + H - 40], outline=(120, 120, 120))
        for hv in range(-10, 4, 2):
            dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
            dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
        dr.line([(sx(p["s"]), sy(p["ground"])) for p in prof if p["ground"] == p["ground"]], fill=(60, 60, 60), width=3)
        dr.line([(sx(p["s"]), sy(p["bed"])) for p in prof], fill=(120, 90, 50), width=2)
        for p in prof:
            col = (60, 120, 220) if p["kind"] != "pipe" else (120, 160, 220)
            dr.line([sx(p["s"]), sy(p["water"]), sx(p["s"]), sy(p["bed"])], fill=col if p["kind"] != "pipe" else (200, 215, 235))
        dr.line([(sx(p["s"]), sy(p["water"])) for p in prof], fill=(30, 90, 200), width=3)
        if key == "D":
            s_w = [p["s"] for p in prof if p["kind"] == "basin"][0]
            dr.line([sx(s_w), sy(hmax), sx(s_w), sy(hmin)], fill=(200, 60, 60), width=2)
            dr.text((sx(s_w) + 4, pad // 2 + 6), f"weir: {TROUGH_TOP - LAGOON:.2f} m fall (NT-1 trough -5.17 to canal -7.5)", fill=(200, 60, 60))
            s_c = [p["s"] for p in prof if p["kind"] == "basin"][-1] - 23.0
            dr.line([sx(s_c), sy(hmax), sx(s_c), sy(hmin)], fill=(60, 160, 60), width=2)
            dr.text((sx(s_c) + 4, pad // 2 + 6), "basin and gate on the lagoon", fill=(60, 160, 60))
            dr.text((sx(0) + 4, pad // 2 + 20), "runnel from the trough (pipe)", fill=(120, 160, 220))
        dr.text((pad + 6, pad // 2 + H - 34), f"option {key}: ground (grey), water level (blue, -7.5 +-{TIDE} tide), bed (brown); s along the route in m, heights Godot m",
                fill=(20, 20, 20))
        for s in range(0, int(s_max) + 1, 50):
            dr.text((sx(s) - 8, pad // 2 + H - 20), f"{s}", fill=(60, 60, 60))
        name = f"proposal_canal{key}_profile.png"
        img.save(os.path.join(folder, name))
        print(f"canals_DE: wrote {name}")
    # the table
    cmp_ = out["comparison"]
    cols = ["option", "length m", "cut k m3", "bridges", "gates / locks", "NT-1 clear m", "integration"]
    rows = [[k, c["length_m"], c["cut_k_m3"], c["bridges"], c["gates_locks"], c["nt1_clearance_m"], c["integration"]] for k, c in cmp_.items()]
    widths = [70, 90, 90, 80, 170, 110, 640]
    W = sum(widths) + 40
    Hh = 30 * (len(rows) + 1) + 50
    img = Image.new("RGB", (W, Hh), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    x = 20
    for c, w in zip(cols, widths):
        dr.text((x, 16), c, fill=(20, 20, 20))
        x += w
    for i, r in enumerate(rows):
        x = 20
        y = 46 + i * 30
        dr.line([20, y - 6, W - 20, y - 6], fill=(220, 220, 220))
        for v, w in zip(r, widths):
            dr.text((x, y), str(v), fill=(40, 40, 40))
            x += w
    dr.text((20, Hh - 22), "canal options compared: cut volumes against the master's ground (walls for D/E, 1:1 for A/C); NT-1 clearance from its band z -34..16", fill=(90, 90, 90))
    img.save(os.path.join(folder, "proposal_canalDE_table.png"))
    print("canals_DE: wrote proposal_canalDE_table.png")


# ----------------------------------------------------------------------------- Blender
def render(folder, master):
    import bpy
    from mathutils import Vector
    scratch = os.path.join(folder, "PROPOSAL_canals_DE.blend")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    obj = bpy.data.objects["terrain_world"]
    props = bpy.data.collections.get("Reference_proposals")
    if props is None:
        props = bpy.data.collections.new("Reference_proposals")
        bpy.data.collections["Reference"].children.link(props)

    def to_blender(x, y, z):
        return (x, -z, y)

    def curve(name, pts3, colour, bevel, note="", closed=False):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = bevel
        cu.bevel_resolution = 0
        m = bpy.data.materials.new(f"ref_{name}")
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
        sp.points.add(len(pts3) - 1)
        for i, p in enumerate(pts3):
            sp.points[i].co = (*to_blender(*p), 1.0)
        sp.use_cyclic_u = closed
        o = bpy.data.objects.new(name, cu)
        o["kyt_reference"] = True
        o["kyt_collision"] = "none"
        o["kyt_note"] = note
        o.hide_select = True
        props.objects.link(o)
        return o

    def basin_outline(b, y):
        (x0, x1), (z0, z1) = b["x"], b["z"]
        return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]

    CANAL = (0.0, 0.45, 1.0, 1.0)      # azure: every canal proposal and water marker (colour key, world_terrain_reference_palette.py)
    WATER = (0.9, 0.3, 0.9, 1.0)       # the lagoon as the entrance plan proposes it: magenta like the other lagoon proposals
    D_COL = CANAL
    E_COL = CANAL
    y = LAGOON + 0.3
    objs = {}
    objs["D_runnel"] = curve("PROPOSAL_canalD_runnel_from_NT1_trough", [(-61.0, TROUGH_TOP, -1.0), (-61.0, TROUGH_TOP, 41.0)], (0.6, 0.8, 1.0, 1.0), 0.6,
                             "D: buried runnel from the trough's south end to the head basin's weir; inside NT-1's band on the bluff foot: needs approval")
    objs["D_head"] = curve("PROPOSAL_canalD_head_basin", basin_outline(HEAD_BASIN, y), D_COL, 1.5, "D: head basin 16 x 22 m at -7.5, walls, weir on the north wall, dock on the west quay, Coastal Creek enters east", closed=True)
    objs["D_canal"] = curve("PROPOSAL_canalD_centreline", [(CANAL_X, y, 63.0), (CANAL_X, y, 170.0), (-76.0, y, 185.0), (-76.0, y, 236.0), (-73.0, y, 300.0)], D_COL, WIDTH_D / 2,
                            "D: 8 m canal at -7.5, bed -9, walls; shore band z 63..220 then the lawn z 220..300 (D2: culvert there)")
    objs["E_basin"] = curve("PROPOSAL_canalE_landing_basin", basin_outline(E_BASIN, y), E_COL, 1.5, "E: landing basin 14 x 23 m at -7.5, bed -9.5, walls, mouth on the lagoon at z 323, pontoon on the east quay, 1:12 ramp to the bluff-top walk", closed=True)
    objs["E_ramp"] = curve("PROPOSAL_canalE_ramp_to_bluff_top_walk", [(-61.0, -6.0, 310.0), (-56.0, -3.0, 322.0), (-56.0, -3.0, 300.0), (-61.0, 0.0, 298.0)], (1.0, 0.85, 0.3, 1.0), 0.8,
                           "E: 72 m of 1:12 ramp in two switchbacks from the pontoon quay (-6) to the bluff-top walk (0)")
    objs["E_walk"] = curve("PROPOSAL_canalE_walk_to_gate", [(-61.0, 0.3, 298.0), (-70.0, 0.3, 300.0), (-70.0, 0.3, 236.0), (-68.0, 0.3, 180.0), (-13.0, 0.3, 170.0), (0.0, 0.3, 150.0)], (1.0, 0.9, 0.5, 1.0), 0.8,
                           "E: the step-free walk from the landing to the gate, about 285 m: the canal's east quay north, the front road's west end, the west field's north edge to the allee opening")
    lag = [(-110, 327), (-86, 326), (-77, 324.5), (-66, 323.5), (-57, 314), (-39, 315.3), (-17, 322), (17, 322), (33, 311), (42, 308), (60, 302.6), (69, 300.8)]
    objs["lagoon"] = curve("PROPOSAL_canalDE_lagoon_north_shore_from_plan", [(x, y, z) for x, z in lag], WATER, 0.8, "the lagoon's north shore as entrance-landscaping.html draws it (proposal)")
    bpy.ops.wm.save_mainfile()
    print(f"canals_DE: scratch copy saved {scratch}")

    scene = bpy.context.scene
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

    def shoot(name):
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        print(f"canals_DE: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2400):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = to_blender(cx, 3000.0, cz)
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

    def show(keys):
        for k, o in objs.items():
            o.hide_render = k not in keys
    allD = ["D_runnel", "D_head", "D_canal", "E_basin", "lagoon"]
    allE = ["E_basin", "E_ramp", "E_walk", "lagoon"]
    show(allD)
    top_down("proposal_canalD_top.png", -200.0, 100.0, -60.0, 400.0)
    oblique("proposal_canalD_oblique_from_lagoon.png", (-60.0, 40.0, 420.0), (-70.0, -6.0, 60.0), lens=40.0)
    top_down("proposal_canalD_junction_closeup.png", -130.0, -20.0, -40.0, 110.0, px=1800)
    oblique("proposal_canalD_junction_oblique.png", (-120.0, 25.0, 110.0), (-66.0, -6.0, 30.0), lens=40.0)
    show(allE)
    top_down("proposal_canalE_top.png", -140.0, 100.0, 130.0, 400.0)
    oblique("proposal_canalE_oblique_from_water.png", (-75.0, 14.0, 372.0), (-45.0, 0.0, 250.0), lens=30.0)
    show(allD + allE)
    top_down("proposal_canalDE_top.png", -200.0, 120.0, -60.0, 420.0)
    oblique("proposal_canalDE_oblique_network.png", (-260.0, 150.0, 480.0), (-60.0, -6.0, 150.0), lens=35.0)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--analyse" in argv:
        analyse(argv[argv.index("--analyse") + 1])
    if "--render" in argv:
        folder = argv[argv.index("--render") + 1]
        master = argv[argv.index("--master") + 1] if "--master" in argv else os.path.join(os.getcwd(), "assets/source/world_terrain_master.blend")
        render(folder, master)


if __name__ == "__main__":
    main()
