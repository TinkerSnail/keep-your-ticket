"""The park's connected water network, designed with numbers, PROPOSAL only (2026-10-01,
Christina approved the connected network: two real creeks K and L with their hill lakes, L
forked into Kiddieland's pond chain, K's take-off feeding the north shelf pond then, under
the Grove mound, the Grove pond and the bluff-notch weir, the pond chain ducking under the
entrance to a Fairground duct and Coastal Creek; E's landing basin kept; creeks may duck
under the ground; no canal parallel to the coast).

Uses the hydrology sampling of world_terrain_hydrology.py (hydro_grid10 / hydro_grid4 /
hydro_analysis10 in the same folder). Nothing touches the master; the Blender step writes a
scratch copy with azure PROPOSAL_network_* curves.

    python3 tools/blender/world_terrain_water_network.py --analyse <hydro folder> --out <renders>
    python3 tools/blender/world_terrain_water_network.py --draw <hydro folder> --out <renders>
    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_water_network.py -- --curves <hydro folder> --out <renders>
"""
import json
import math
import os
import shutil
import sys

import numpy as np

SEA = -7.5
AZURE = (0, 115, 255)
# ----------------------------------------------------------------------------- the design
# Each reach: points (Godot x, z), water level at the first and last point (interpolated
# linearly along the reach), kind: creek (natural/open), channel (designed open), cascade,
# duct (underground: size, invert = water level - 0.6 for a flowing duct, pressure in a siphon),
# lake/pond (polygon with level and bed).
REACHES = [
    # --- K, the north creek
    {"id": "K-L2", "name": "tarn K2 (762,-697): closed basin, spills at (830,-640) +119.9 into the north creek's head", "kind": "lake", "centre": (762, -697), "level": 119.9, "area_ha": 1.17, "vol_m3": 52000, "spill": (830, -640)},
    {"id": "K-L1", "name": "lake K1 (600,-471): the north creek's lake, level +79.7 at the brim (recommended +70: 1.5 ha, see balance), spills W at (520,-410) +79.7 straight into the north creek", "kind": "lake", "centre": (600, -471), "level": 79.7, "area_ha": 3.49, "vol_m3": 345000, "spill": (520, -410)},
    {"id": "K-1", "name": "north creek, lake outlet to the take-off", "kind": "creek", "pts": [(520, -410), (480, -370), (440, -330), (400, -290), (360, -250), (330, -225), (300, -230)], "wl": (79.7, 9.4)},
    {"id": "K-2", "name": "north creek, main stem to the north cove (natural, 70 ha)", "kind": "creek", "pts": [(300, -230), (280, -250), (240, -290), (200, -330), (140, -350), (80, -360), (0, -370), (-80, -380), (-120, -400), (-140, -400)], "wl": (9.4, -6.0)},
    {"id": "K-3", "name": "take-off: side weir crest +8.9 at (300,-230), 1.5 m box culvert through the +20 spur (cover to 11 m); open-cut alternative costed", "kind": "duct", "pts": [(290, -230), (250, -230), (220, -230), (195, -230)], "wl": (8.4, 7.2), "size": "1.5 x 1.5 m box", "invert": (7.9, 6.9)},
    {"id": "K-4", "name": "the corner cascade: pop-out at (195,-230) +7.2 down the corner's own slope to the shelf, 7 m over 40 m (17 %), rock steps", "kind": "cascade", "pts": [(195, -230), (175, -230), (155, -229)], "wl": (7.2, 0.3)},
    {"id": "K-5", "name": "north-shelf channel across the shelf (ground -0.2) to pond P3; cut 1 m into the shelf, 4 m wide", "kind": "channel", "pts": [(152, -229), (130, -222), (110, -215), (90, -208), (70, -203), (58, -200)], "wl": (0.3, -0.2)},
    {"id": "P3", "name": "P3 north-shelf pond at D6 (54,-200): 50 x 35 m, 0.17 ha, level -0.2 (the saucer's rim 0), bed -1.7, about 2,000 m3 dug; outlets: the Grove duct and an overflow weir at -0.1 west along the shelf", "kind": "pond", "poly": [(30, -215), (80, -215), (80, -182), (30, -182)], "level": -0.2, "bed": -1.7},
    {"id": "K-6", "name": "Grove duct: P3 to P2 under the Grove mound (+4), 1.2 m pipe, 104 m, invert -1.4 to -1.8 (0.4 %), cover 1.2 to 5.8 m; under route F's arc and route A's north leg", "kind": "duct", "pts": [(50, -190), (33, -182), (12, -164), (-9, -146), (-20, -137), (-34, -130)], "wl": (-0.2, -0.6), "size": "1.2 m pipe", "invert": (-1.6, -2.0)},
    {"id": "P2", "name": "P2 Grove pond: the existing pond (-19.5,-118) r 5.4 grown to 24 x 50 m, 0.12 ha, between route A (x -10) and route B (x -44), level -0.6, bed -2.1; takes the park's 9 ha runoff; outlet weir -0.6 at (-38,-138)", "kind": "pond", "poly": [(-38, -150), (-14, -150), (-14, -100), (-38, -100)], "level": -0.6, "bed": -2.1},
    {"id": "K-7", "name": "notch cascade: weir -0.6, culvert under route B's north return at (-44,-134), the bluff notch (-48,-148), 7 m of falls to the shore band (-6), culvert under the Grand Circuit at (-84,-150), to the sea; north of the coaster's footprint (z -142) by 8 m", "kind": "cascade", "pts": [(-38, -138), (-44, -142), (-48, -148), (-56, -150), (-70, -150), (-84, -150), (-96, -150), (-108, -150)], "wl": (-0.6, -7.5)},
    # --- L, the south creek
    {"id": "L-L0", "name": "lake L0 (730,206): the south creek's lake, 4.3 ha and 31 m deep at the brim +92 (recommended +72: 1.0 ha), spills W at (660,110) +91.9", "kind": "lake", "centre": (730, 206), "level": 92.0, "area_ha": 4.32, "vol_m3": 583000, "spill": (660, 110)},
    {"id": "L-L1", "name": "lake L1 (292,706): 2.0 ha, +65.9, 14 m: NOT in L's catchment; it spills at (260,640) to the beach front (exit (-10,850)); a separate small watershed", "kind": "lake", "centre": (292, 706), "level": 65.9, "area_ha": 2.03, "vol_m3": 134000, "spill": (260, 640)},
    {"id": "L-1", "name": "south creek, lake outlet down the valley to the fork", "kind": "creek", "pts": [(660, 110), (610, 200), (560, 200), (500, 200), (440, 200), (380, 200), (320, 200), (290, 220), (265, 228)], "wl": (91.9, 9.6)},
    {"id": "L-2", "name": "south creek, fork to the lagoon's east body under the arrival bridge: the creek's mouth is a 14 m cascade into the dug lagoon", "kind": "creek", "pts": [(265, 228), (240, 285), (215, 305), (195, 318)], "wl": (9.6, 6.4)},
    {"id": "L-2b", "name": "the creek's mouth: a 14 m cascade from the valley floor (+6.4) into the dug east body (-7.5) under the arrival bridge; the road fill there is removed by the lagoon dig", "kind": "cascade", "pts": [(195, 318), (180, 312), (165, 305)], "wl": (6.4, -7.5)},
    {"id": "L-3", "name": "fork culvert: side weir +9.3 at (265,228), 1.2 m box, 100 m under the +20 spur (cover to 10 m), invert 9.0 to 7.0 (2 %), pop-out at (192,158) ground 7.1", "kind": "duct", "pts": [(265, 228), (240, 205), (215, 180), (192, 158)], "wl": (9.3, 6.8), "size": "1.2 x 1.2 m box", "invert": (9.0, 6.5)},
    {"id": "L-4", "name": "fork cascade: (192,158) +7.2 to P1a's inlet (182,150) +3.9, 2.6 m of steps", "kind": "cascade", "pts": [(192, 158), (182, 150)], "wl": (6.8, 3.9)},
    {"id": "P1a", "name": "P1a Kiddieland pond at D5 (171,145): 36 x 30 m, 0.1 ha, level +3.9 (rim 4.13), bed +2.4; outlet weir +3.9 at (152,152)", "kind": "pond", "poly": [(152, 160), (189, 160), (189, 128), (152, 128)], "level": 3.9, "bed": 2.4},
    {"id": "L-5", "name": "P1a to P1b: open channel 4 m, 45 m, +3.9 to +2.9 (2 %); crosses the S3 service lane and the Grand Circuit lane (culverts) and the +0.5 trench at x 140 (a flume or fill, see risks)", "kind": "channel", "pts": [(152, 152), (140, 155), (128, 158)], "wl": (3.9, 2.9)},
    {"id": "P1b", "name": "P1b Kiddieland pond at D4 (106,162): 45 x 34 m, 0.15 ha, level +2.9 (rim 3.43), bed +1.4; outlets: the slough spillway and the entrance siphon", "kind": "pond", "poly": [(84, 178), (128, 178), (128, 146), (84, 146)], "level": 2.9, "bed": 1.4},
    {"id": "L-6", "name": "slough spillway: weir +2.9 at (112,176), cascade down the slough to the lagoon's NE lobe, 10 m over 45 m; beside the rail halt's east edge (x 110)", "kind": "cascade", "pts": [(112, 176), (116, 190), (120, 205), (122, 215)], "wl": (2.9, -7.5)},
    {"id": "L-7", "name": "entrance siphon: P1b (+2.9) to D3 (-0.3), 118 m inverted siphon, 1.0 m pipe, drop shaft at (96,165), invert -2.6 under the berm, apron and the arrival walk at (0,170) (crown -1.6, 1.6 m cover), rising to D3; drive head 3.2 m; no surface change, feeds nothing on the way", "kind": "duct", "pts": [(96, 165), (60, 167), (28, 170), (0, 171), (-18, 173)], "wl": (2.9, -0.3), "size": "1.0 m pipe", "invert": (-2.6, -2.6)},
    {"id": "D3", "name": "D3 pond (-18,174): the entrance saucer as a pop-up pond, 28 x 27 m rim, 0.07 ha, level -0.3, bed -1.5; inside the Q0 cone at ground level (water, nothing above 0)", "kind": "pond", "poly": [(-32, 187), (-4, 187), (-4, 160), (-32, 160)], "level": -0.3, "bed": -1.5},
    {"id": "L-8", "name": "Fairground duct: D3 (-0.3) to Coastal Creek beside CX1 (-60,40) (creek water about -1.5), 1.0 m pipe, 190 m, invert -1.6 to -2.6 (0.5 %), cover 1.3 m under the Fairground's paths; under route C twice; east of the Big Top and I1, west of the booths; never under the Plaza square (x,z within +-52) nor NT-1", "kind": "duct", "pts": [(-22, 165), (-26, 140), (-21, 120), (-20, 70), (-45, 62), (-56, 48), (-60, 40)], "wl": (-0.3, -1.5), "size": "1.0 m pipe", "invert": (-2.2, -2.9)},
    {"id": "CC", "name": "Coastal Creek 05A as built: head (-48,22) -0.13, CX1 (-62,44), rain pond (-88,57) -4.3, CB1, CB2, outfall (-104,57) -5.9 to the shore band: unchanged", "kind": "creek", "pts": [(-48, 22), (-54, 29), (-59, 37), (-62, 44), (-70, 50), (-79, 55), (-88, 57), (-96, 57), (-104, 57), (-108, 57)], "wl": (-0.13, -5.9)},
    {"id": "E", "name": "E landing basin, lagoon NW corner (candidate component, unchanged)", "kind": "pond", "poly": [(-77, 300), (-61, 300), (-61, 323), (-77, 323)], "level": -7.5, "bed": -9.5},
]
CROSSINGS = [  # surface crossings: (x, z, what, how)
    (80, -205, "Grand Circuit lane (K-5)", "lane bridges the shelf channel"),
    (50, -189, "S3 service lane end (P3)", "S3's last leg ends at the pond's north bank (moves 10 m north)"),
    (-44, -134, "route B north return (K-7)", "creek in a culvert under the path"),
    (-84, -150, "Grand Circuit lane (K-7)", "culvert under the lane"),
    (165, 300, "arrival arm (L-2)", "the plan's arrival bridge"),
    (141, 155, "S3 service lane (L-5)", "culvert under the lane"),
    (135, 157, "Grand Circuit lane (L-5)", "culvert under the lane"),
]
UNDER = [  # underground passages beneath routes (no surface change)
    (28, -150, "route F outer arc (K-6)"), (-14, -142, "route A north leg (K-6)"), (0, 171, "arrival walk / axis (L-7), crown -1.6"), (60, 167, "east berm (L-7)"),
    (-24, 147, "route C loop (L-8)"), (-34, 92, "route C loop (L-8)"), (-21, 100, "route C plaza link (L-8)"),
]
ASSUME = {"rain_mm": 300, "runoff_hills": 0.3, "runoff_park": 0.5, "evap_mm": 1400, "note": "latitude 32.75 Mediterranean assumptions; creeks are winter-seasonal; summer flow near zero"}


def bilinear(H, xs, zs, x, z):
    fx = (x - xs[0]) / (xs[1] - xs[0])
    fz = (z - zs[0]) / (zs[1] - zs[0])
    i0 = int(np.clip(math.floor(fx), 0, len(xs) - 2))
    j0 = int(np.clip(math.floor(fz), 0, len(zs) - 2))
    tx, tz = fx - i0, fz - j0
    q = H[j0:j0 + 2, i0:i0 + 2]
    return float((q[0, 0] * (1 - tx) + q[0, 1] * tx) * (1 - tz) + (q[1, 0] * (1 - tx) + q[1, 1] * tx) * tz)


def profile(H, xs, zs, pts, wl, invert=None, step=5.0, natural=False):
    out = []
    s = 0.0
    total = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for k in range(n + (1 if i == len(pts) - 2 else 0)):
            t = k / n
            x, z = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
            ss = s + t * L
            w = wl[0] + (wl[1] - wl[0]) * (ss / total if total else 0)
            g = bilinear(H, xs, zs, x, z)
            row = {"s": ss, "x": x, "z": z, "ground": g, "water": (g - 0.3) if natural else w}
            if invert:
                row["invert"] = invert[0] + (invert[1] - invert[0]) * (ss / total if total else 0)
            out.append(row)
        s += L
    return out, total


def analyse(folder, out):
    os.makedirs(out, exist_ok=True)
    d10 = np.load(os.path.join(folder, "hydro_grid10.npz"))
    d4 = np.load(os.path.join(folder, "hydro_grid4.npz"))
    H10, xs10, zs10 = d10["H"], d10["xs"], d10["zs"]
    H4, xs4, zs4 = d4["H"], d4["xs"], d4["zs"]

    def grid_for(pts):
        inside = all(xs4[0] <= x <= xs4[-1] and zs4[0] <= z <= zs4[-1] for x, z in pts)
        return (H4, xs4, zs4) if inside else (H10, xs10, zs10)
    rows = []
    for r in REACHES:
        if r["kind"] in ("lake",):
            rows.append({"id": r["id"], "kind": "lake", "name": r["name"], "level": r["level"], "area_ha": r["area_ha"], "vol_m3": r["vol_m3"], "spill": r["spill"]})
            continue
        if r["kind"] == "pond":
            H, xs, zs = grid_for(r["poly"])
            xs_ = [p[0] for p in r["poly"]]
            zs_ = [p[1] for p in r["poly"]]
            area = (max(xs_) - min(xs_)) * (max(zs_) - min(zs_))
            gs = [bilinear(H, xs, zs, x, z) for x in np.arange(min(xs_) + 2, max(xs_), 4) for z in np.arange(min(zs_) + 2, max(zs_), 4)]
            dig = sum(max(0.0, g - r["bed"]) for g in gs) * 16
            rows.append({"id": r["id"], "kind": "pond", "name": r["name"], "level": r["level"], "bed": r["bed"], "area_ha": round(area / 1e4, 3), "depth_m": round(r["level"] - r["bed"], 1),
                         "ground_mean": round(float(np.mean(gs)), 2), "dig_m3": round(dig), "water_m3": round(area * (r["level"] - r["bed"]) * 0.8)})
            continue
        H, xs, zs = grid_for(r["pts"])
        prof, L = profile(H, xs, zs, r["pts"], r["wl"], r.get("invert"), natural=(r["kind"] == "creek"))
        fall = r["wl"][0] - r["wl"][1]
        row = {"id": r["id"], "kind": r["kind"], "name": r["name"], "length_m": round(L), "fall_m": round(fall, 2), "gradient_pct": round(100 * fall / L, 2) if L else None,
               "wl": r["wl"], "profile": prof}
        if r["kind"] == "duct":
            body = [p for p in prof if 10.0 <= p["s"] <= L - 10.0] or prof
            cover = [p["ground"] - (p["invert"] + (1.5 if "box" in r["size"] else 1.0)) for p in body]
            kmin = int(np.argmin(cover))
            row.update({"size": r["size"], "invert": r["invert"], "cover_min_m": round(min(cover), 1), "cover_max_m": round(max(cover), 1), "cover_min_at": [round(body[kmin]["x"]), round(body[kmin]["z"])], "note_cover": "portals (first/last 10 m) excluded: headwalls"})
        if r["kind"] in ("channel", "cascade"):
            cut = [max(0.0, p["ground"] - (p["water"] - 1.0)) for p in prof]
            row.update({"max_cut_to_bed_m": round(max(cut), 1)})
        if r["kind"] == "creek":
            row.update({"fall_m": round(prof[0]["ground"] - prof[-1]["ground"], 1), "gradient_pct": round(100 * (prof[0]["ground"] - prof[-1]["ground"]) / L, 2), "note": "natural creek: water follows the ground"})
        rows.append(row)
    # K open-cut alternative along z -230 from x 296 to 162: bed 8.6 -> 7.5, 4 m base, 1:2 slopes
    vol = 0.0
    for x in np.arange(162, 297, 2.0):
        g = bilinear(H10, xs10, zs10, x, -230)
        bed = 7.5 + (8.6 - 7.5) * (x - 162) / (296 - 162)
        dcut = max(0.0, g - bed)
        vol += (4 * dcut + 2 * dcut * dcut) * 2.0
    # balance
    A = ASSUME
    k_in = 70e4 * A["rain_mm"] / 1000 * A["runoff_hills"]
    l_in = 47e4 * A["rain_mm"] / 1000 * A["runoff_hills"]
    lakes = {"K1 at +80": 3.49e4 * A["evap_mm"] / 1000, "K1 at +70 (1.5 ha)": 1.5e4 * A["evap_mm"] / 1000, "L0 at +92": 4.32e4 * A["evap_mm"] / 1000, "L0 at +72 (1.0 ha)": 1.0e4 * A["evap_mm"] / 1000}
    lake_in = {"K1 catchment about 25 ha": 25e4 * A["rain_mm"] / 1000 * A["runoff_hills"], "L0 catchment about 21 ha": 21e4 * A["rain_mm"] / 1000 * A["runoff_hills"]}
    ponds_ha = sum(rw["area_ha"] for rw in rows if rw["kind"] == "pond" and rw["id"] != "E")
    balance = {"assumptions": A, "K_runoff_m3_per_yr": round(k_in), "L_runoff_m3_per_yr": round(l_in), "mean_flow_K_L_per_s": round(k_in / 31.5e6 * 1000, 1), "mean_flow_L_L_per_s": round(l_in / 31.5e6 * 1000, 1),
               "lake_evaporation_m3_per_yr": {k: round(v) for k, v in lakes.items()}, "lake_inflow_m3_per_yr": {k: round(v) for k, v in lake_in.items()},
               "park_ponds_ha": round(ponds_ha, 2), "park_ponds_evaporation_m3_per_yr": round(ponds_ha * 1e4 * A["evap_mm"] / 1000),
               "park_runoff_to_P2_m3_per_yr": round(9e4 * A["rain_mm"] / 1000 * A["runoff_park"]),
               "verdict": "on rain alone the hill lakes cannot stay at their brims (evaporation 49-60 k m3/yr against 19-22 k of inflow): they are credible as lakes about 10 m below their spill levels, overflowing only in wet winters; "
                          "the creeks run on their own lower catchments (K 45 ha, L 26 ha below the lakes) in winter and dry in summer; the park ponds (0.5 ha, 7 k m3/yr evaporation) need a dry-season recirculation of 2-5 L/s "
                          "(a small pump at the Coastal Creek outfall lifting 10 m to P1a, and one at the notch cascade's foot lifting 7 m to P3), the same role 05A's rain pond already implies; every pond has a gravity outlet"}
    report = {"reaches": rows, "crossings": CROSSINGS, "underground_passages": UNDER, "K_takeoff_open_cut_alternative_m3": round(vol), "balance": balance,
              "gravity_links": {
                  "P3 -> P2 (Grove duct)": "minimum fall available 0.4 m over 104 m (0.4 %) with P3 at -0.2 and P2 at -0.6, both inside the existing saucer rims; a 1.2 m pipe passes about 2 m3/s at that slope: no re-grade, no pump",
                  "P1b -> D3 -> Coastal Creek": "P1b at +2.9 stands 3.2 m above D3 (-0.3): the inverted siphon under the entrance runs on that head; D3 to the creek at CX1 (-1.5) has 1.2 m of head over 190 m: gravity, no pump; the creek's head (-0.13) is NOT touched because the duct joins the creek 25 m downstream beside CX1",
                  "K take-off": "the +20 spur between (300,-230) +9.4 and the shelf (0) is passed by a culvert (cover up to 11 m) rather than a cutting of about %d m3; the 7 m drop onto the shelf is the corner falls" % round(vol),
                  "L fork": "the +20 spur between the valley (+9.6) and D5 (+3.9) is passed by a 100 m culvert at 2 %; a surface channel would need a 10 m cut; the lobe (0) lies between the valley and D5 so no surface line can reach D5 by gravity",
              },
              "protected": {"Plaza": "no element inside x,z +-52: the Fairground duct's nearest point is (-56,48); nothing under the Plaza floor",
                            "NT-1": "the duct outfall at (-60,40) is 28 m south of NT-1's box z -15..12 and joins the existing creek; NT-1's bluff z -15..12 is not undercut; no water to or from NT-1",
                            "NT-2": "nothing east of x 44 between z -52 and 52 except the valley creeks 200 m away",
                            "entrance": "surface untouched: the siphon passes beneath the berm, apron and walk with 1.6 m cover; D3 is the approved saucer, now holding water at -0.3",
                            "views": "Q0: D3's water lies in the cone at ground level, nothing above 0; Q1-Q6: no element in any view; P1 ponds are south of J7's line to NT-2"},
              "changes_to_approved_plan": ["D4 and D5 drainage saucers become ponds P1b/P1a with spillways (02A/05)", "D3 saucer becomes a pop-up pond (02A)", "D6 saucer becomes pond P3 (05)",
                                           "Coastal Creek 05A gains an inflow beside CX1 (its head, rain pond, bridges and outfall unchanged)", "the coastal plan's 'extend Coastal Creek upstream into the foothills' is replaced by this network",
                                           "S3's last leg ends at P3's north bank", "the Grand Circuit lane gets three culverts/bridges, route B one culvert", "the lagoon's east body receives creek L under the arrival bridge; the NE lobe receives the Kiddieland spillway"],
              "approvals": ["the ponds P1a/P1b/P3/D3 at the approved saucers", "the entrance siphon beneath the apron and arrival walk (underground only)", "the duct into Coastal Creek beside CX1 (05A)",
                            "the culverts under the Grand Circuit, S3 and route B", "the hill lakes' recommended levels (+70 / +72) and the seasonal-creek assumption", "the x 140 trench crossing in Kiddieland"]}
    with open(os.path.join(out, "network_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    for rw in rows:
        if rw["kind"] in ("pond", "lake"):
            print(f"network: {rw['id']}: {rw['kind']} level {rw['level']} area {rw['area_ha']} ha" + (f" dig {rw['dig_m3']} m3" if "dig_m3" in rw else ""))
        else:
            print(f"network: {rw['id']}: {rw['kind']} {rw['length_m']} m, fall {rw['fall_m']} m ({rw['gradient_pct']} %)" + (f", cover {rw['cover_min_m']}..{rw['cover_max_m']} m" if "cover_min_m" in rw else "") + (f", max cut {rw['max_cut_to_bed_m']} m" if "max_cut_to_bed_m" in rw else ""))
    print(f"network: K take-off open-cut alternative {vol:.0f} m3; balance {balance['verdict'][:120]}...")
    return report


# ----------------------------------------------------------------------------- drawings
def draw(folder, out):
    from PIL import Image, ImageDraw
    rep = json.load(open(os.path.join(out, "network_report.json")))
    d = np.load(os.path.join(folder, "hydro_grid10.npz"))
    H, xs, zs = d["H"], d["xs"], d["zs"]

    def base(x0, x1, z0, z1, sc, title, foot=120):
        W, Hh = int((x1 - x0) * sc), int((z1 - z0) * sc)
        img = Image.new("RGB", (W, Hh + foot), (250, 250, 248))
        arr = np.zeros((Hh, W, 3), dtype=np.uint8)
        jj = np.clip(((np.arange(Hh) / sc + z0 - zs[0]) / 10).astype(int), 0, len(zs) - 1)
        ii = np.clip(((np.arange(W) / sc + x0 - xs[0]) / 10).astype(int), 0, len(xs) - 1)
        Hs = H[jj][:, ii]
        sea = Hs <= SEA + 0.05
        t = np.clip((Hs + 8) / 300.0, 0, 1)
        arr[..., 0] = (235 - 90 * t).astype(np.uint8)
        arr[..., 1] = (232 - 110 * t).astype(np.uint8)
        arr[..., 2] = (215 - 130 * t).astype(np.uint8)
        band = (np.floor(Hs / 5) != np.floor(np.roll(Hs, 1, axis=0) / 5)) | (np.floor(Hs / 5) != np.floor(np.roll(Hs, 1, axis=1) / 5))
        arr[band & ~sea] = (190, 180, 160)
        arr[sea] = (150, 185, 215)
        img.paste(Image.fromarray(arr), (0, 0))
        dr = ImageDraw.Draw(img)
        px = lambda x: (x - x0) * sc
        pz = lambda z: (z - z0) * sc
        dr.text((10, Hh + 8), title, fill=(10, 10, 10))
        return img, dr, px, pz, Hh

    def dashed(dr, pts, fill, width, dash):
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            L = math.hypot(bx - ax, by - ay)
            n = max(1, int(L / dash))
            for k in range(0, n, 2):
                t0, t1 = k / n, min(1.0, (k + 1) / n)
                dr.line([(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)], fill=fill, width=width)

    def draw_network(dr, px, pz, sc, labels=True):
        for r in REACHES:
            if r["kind"] == "lake":
                x, z = r["centre"]
                rr = math.sqrt(r["area_ha"] * 1e4 / math.pi) * sc
                dr.ellipse([px(x) - rr, pz(z) - rr, px(x) + rr, pz(z) + rr], fill=(120, 170, 255), outline=AZURE, width=2)
                sx, sz = r["spill"]
                dr.ellipse([px(sx) - 3, pz(sz) - 3, px(sx) + 3, pz(sz) + 3], fill=(220, 40, 40))
                if labels:
                    dr.text((px(x) - 20, pz(z) - 6), f"{r['id']} +{r['level']:.0f}", fill=(0, 40, 120))
            elif r["kind"] == "pond":
                pts = [(px(x), pz(z)) for x, z in r["poly"]]
                dr.polygon(pts, fill=(120, 170, 255), outline=AZURE)
                if labels:
                    dr.text((pts[0][0], pts[0][1] - 12), f"{r['id']} {r['level']:+.1f}", fill=(0, 40, 120))
            else:
                pts = [(px(x), pz(z)) for x, z in r["pts"]]
                if r["kind"] == "duct":
                    dashed(dr, pts, AZURE, 4, 8)
                elif r["kind"] == "cascade":
                    dr.line(pts, fill=(0, 60, 200), width=5)
                elif r["kind"] == "creek":
                    dr.line(pts, fill=AZURE, width=3)
                else:
                    dr.line(pts, fill=AZURE, width=4)
                if labels:
                    x, z = r["pts"][len(r["pts"]) // 2]
                    dr.text((px(x) + 4, pz(z) - 12), r["id"], fill=(0, 40, 120))
        for x, z, what, how in CROSSINGS:
            dr.line([px(x) - 5, pz(z) - 5, px(x) + 5, pz(z) + 5], fill=(220, 30, 30), width=3)
            dr.line([px(x) - 5, pz(z) + 5, px(x) + 5, pz(z) - 5], fill=(220, 30, 30), width=3)
        for x, z, what in UNDER:
            dr.ellipse([px(x) - 4, pz(z) - 4, px(x) + 4, pz(z) + 4], outline=(120, 60, 200), width=2)
        for (x0, x1, z0, z1), lab in [((-74, -55, -15, 12), "NT-1"), ((-52, 52, -52, 52), "Plaza"), ((-13, 13, 50, 228), "arrival axis")]:
            dr.rectangle([px(x0), pz(z0), px(x1), pz(z1)], outline=(230, 60, 60), width=2)
            dr.text((px(x0) + 2, pz(z0) + 2), lab, fill=(200, 40, 40))
        dr.ellipse([px(44), pz(-36), px(128), pz(36)], outline=(230, 60, 60), width=2)
        dr.text((px(86) - 10, pz(0) - 6), "NT-2", fill=(200, 40, 40))

    # 1. overview
    img, dr, px, pz, Hh = base(-250, 900, -800, 800, 0.8, "network_overview: the connected water network. Azure: creeks and channels; dashed azure: underground ducts/siphons; dark blue: cascades; light fill: lakes and ponds; red x: surface crossing (bridge/culvert); purple o: passes beneath a route; red dot: lake spill; red boxes: protected (untouched)", 150)
    draw_network(dr, px, pz, 0.8)
    for name, (x0, x1, z0, z1) in {"Boardwalk": (-200, -44, -215, 88), "Fairground": (-88, 8, 18, 185), "Kiddieland": (-5, 181, 42, 185), "High Terrace": (35, 217, -123, 64), "Frontier": (48, 196, -194, -45), "Grove": (-55, 81, -214, -45), "Headland": (-229, 18, -337, -148), "Entrance": (-48, 48, 83, 196)}.items():
        dr.rectangle([px(x0), pz(z0), px(x1), pz(z1)], outline=(130, 130, 130))
        dr.text((px(x0) + 3, pz(z1) - 14), name, fill=(90, 90, 90))
    lag = [(-110, 327), (-86, 326), (-77, 324.5), (-66, 323.5), (-57, 314), (-39, 315.3), (-17, 322), (17, 322), (33, 311), (42, 308), (60, 302.6), (69, 300.8), (73, 286), (78.5, 262), (88, 256), (100, 262), (112, 256), (114, 238), (113, 222), (114, 200), (122, 184), (137, 178), (151, 175), (163, 176), (170, 184), (172, 205), (170, 232), (166, 262), (166, 283), (150, 297)]
    dr.line([(px(x), pz(z)) for x, z in lag], fill=(150, 60, 200), width=2)
    dr.text((px(-100), pz(340)), "tidal lagoon (plan)", fill=(120, 40, 170))
    y = Hh + 26
    dr.text((10, y), "K: tarn K2 -> lake K1 (+80 brim, +70 recommended) -> north creek -> take-off (300,-230) +8.9 -> culvert through the spur -> corner falls -> shelf channel -> P3 (-0.2) -> Grove duct -> P2 (-0.6) -> notch cascade -> sea; main stem on to the north cove.", fill=(20, 20, 20))
    dr.text((10, y + 18), "L: lake L0 (+92 brim, +72 recommended) -> south creek -> fork (265,228) +9.3 -> culvert -> fork cascade -> P1a (+3.9) -> P1b (+2.9) -> slough spillway to the NE lobe; main stem -> cascade into the east body under the arrival bridge.", fill=(20, 20, 20))
    dr.text((10, y + 36), "P1b -> inverted siphon under the entrance (invert -2.6, crown -1.6) -> D3 pond (-0.3) -> Fairground duct -> Coastal Creek beside CX1 (-1.5) -> rain pond -> outfall -> shore band -> sea. E basin: candidate landing on the lagoon.", fill=(20, 20, 20))
    dr.text((10, y + 54), "Surface crossings: 7 (listed in network_reaches_table.png); underground passages beneath routes: 7; Plaza, NT-1, NT-2 and the entrance surface untouched.", fill=(20, 20, 20))
    img.save(os.path.join(out, "network_overview.png"))

    # 2. profiles per creek system and per underground link
    def plot_profile(ids, name, title):
        rows = [r for r in rep["reaches"] if r["id"] in ids and "profile" in r]
        s0 = 0.0
        segs = []
        for r in rows:
            segs.append((r, s0))
            s0 += r["length_m"]
        W, Hh, pad = 1800, 520, 60
        img = Image.new("RGB", (W, Hh + pad), (250, 250, 248))
        dr = ImageDraw.Draw(img)
        allg = [p["ground"] for r, _ in segs for p in r["profile"]] + [p["water"] for r, _ in segs for p in r["profile"]]
        hmin, hmax = min(allg) - 2, max(allg) + 2
        sx = lambda s: pad + s / max(s0, 1) * (W - 2 * pad)
        sy = lambda h: pad // 2 + Hh - 40 - (min(max(h, hmin), hmax) - hmin) / (hmax - hmin) * (Hh - 50)
        dr.rectangle([pad, pad // 2, W - pad, pad // 2 + Hh - 40], outline=(120, 120, 120))
        stepv = 10 if hmax - hmin > 40 else (2 if hmax - hmin > 8 else 1)
        for hv in range(int(hmin), int(hmax) + 1, stepv):
            dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
            dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
        dr.line([pad, sy(SEA), W - pad, sy(SEA)], fill=(120, 170, 230), width=1)
        for r, off in segs:
            pr = r["profile"]
            dr.line([(sx(off + p["s"]), sy(p["ground"])) for p in pr], fill=(60, 60, 60), width=3)
            if r["kind"] == "duct":
                dr.line([(sx(off + p["s"]), sy(p["invert"])) for p in pr], fill=(0, 115, 255), width=3)
                dr.line([(sx(off + p["s"]), sy(p["invert"] + (1.5 if "box" in r["size"] else 1.0))) for p in pr], fill=(0, 115, 255), width=1)
                dr.text((sx(off) + 3, sy(pr[0]["invert"]) + 8), f"{r['id']} duct {r['size']}, cover {r['cover_min_m']}..{r['cover_max_m']} m", fill=(0, 70, 170))
            else:
                dr.line([(sx(off + p["s"]), sy(p["water"])) for p in pr], fill=(30, 90, 200), width=3)
            dr.line([sx(off), sy(hmax), sx(off), sy(hmin)], fill=(200, 200, 200))
            dr.text((sx(off) + 3, pad // 2 + 4), f"{r['id']} {r['kind']} {r['length_m']} m, {r['gradient_pct']} %", fill=(0, 40, 120))
        for r in rep["reaches"]:
            if r["kind"] == "pond" and r["id"] in ids:
                pass
        dr.text((pad + 6, pad // 2 + Hh - 34), title + "  (ground grey, water blue, duct invert azure; s in m; Godot heights; sea -7.5)", fill=(20, 20, 20))
        for s in range(0, int(s0) + 1, 100):
            dr.text((sx(s) - 8, pad // 2 + Hh - 20), f"{s}", fill=(60, 60, 60))
        img.save(os.path.join(out, name))
        print(f"network: wrote {name}")
    plot_profile(["K-1", "K-3", "K-4", "K-5", "K-6", "K-7"], "network_profile_K.png", "creek K: lake K1 outlet to the sea through the take-off, corner falls, shelf channel, P3, Grove duct, P2 and the notch cascade")
    plot_profile(["K-2"], "network_profile_K_main_stem.png", "creek K main stem: take-off to the north cove")
    plot_profile(["L-1", "L-3", "L-4", "L-5", "L-6"], "network_profile_L.png", "creek L: lake L0 outlet down the valley, the fork culvert, P1a, P1b and the slough spillway")
    plot_profile(["L-2", "L-2b"], "network_profile_L_main_stem.png", "creek L main stem: fork to the lagoon's east body")
    plot_profile(["L-7", "L-8", "CC"], "network_profile_entrance_siphon_fairground_duct.png", "P1b to the sea: the entrance siphon, D3, the Fairground duct, Coastal Creek")
    plot_profile(["K-3"], "network_profile_K_takeoff_culvert.png", "K take-off culvert through the spur")
    plot_profile(["K-6"], "network_profile_grove_duct.png", "Grove duct P3 to P2")
    plot_profile(["L-3"], "network_profile_L_fork_culvert.png", "L fork culvert through the spur to Kiddieland")

    # 3. pond close-ups
    d4 = np.load(os.path.join(folder, "hydro_grid4.npz"))
    H4, xs4, zs4 = d4["H"], d4["xs"], d4["zs"]
    for pid, (cx, cz) in {"P1": (140, 160), "P2": (-28, -125), "P3": (54, -200), "D3": (-18, 174)}.items():
        half = 70
        sc = 6.0
        W = int(2 * half * sc)
        img = Image.new("RGB", (W, W + 90), (250, 250, 248))
        arr = np.zeros((W, W, 3), dtype=np.uint8)
        jj = np.clip(((np.arange(W) / sc + cz - half - zs4[0]) / 4).astype(int), 0, len(zs4) - 1)
        ii = np.clip(((np.arange(W) / sc + cx - half - xs4[0]) / 4).astype(int), 0, len(xs4) - 1)
        Hs = H4[jj][:, ii]
        t = np.clip((Hs + 8) / 30.0, 0, 1)
        arr[..., 0] = (235 - 90 * t).astype(np.uint8)
        arr[..., 1] = (232 - 110 * t).astype(np.uint8)
        arr[..., 2] = (215 - 130 * t).astype(np.uint8)
        band = (np.floor(Hs) != np.floor(np.roll(Hs, 1, axis=0))) | (np.floor(Hs) != np.floor(np.roll(Hs, 1, axis=1)))
        arr[band] = (190, 180, 160)
        img.paste(Image.fromarray(arr), (0, 0))
        dr = ImageDraw.Draw(img)
        px = lambda x: (x - (cx - half)) * sc
        pz = lambda z: (z - (cz - half)) * sc
        draw_network(dr, px, pz, sc, labels=True)
        info = [r for r in rep["reaches"] if r["kind"] == "pond" and r["id"].startswith(pid)]
        y = W + 6
        for r in info:
            dr.text((8, y), f"{r['id']}: level {r['level']:+.1f}, bed {r['bed']:+.1f}, {r['area_ha']} ha, dig {r['dig_m3']} m3, water {r['water_m3']} m3, ground mean {r['ground_mean']:+.1f}", fill=(20, 20, 20))
            y += 16
        dr.text((8, y), "1 m contours of the master's 4 m surface; azure = water, dashed = duct, red x = crossing", fill=(90, 90, 90))
        img.save(os.path.join(out, f"network_pond_{pid}.png"))
    print("network: wrote pond close-ups")

    # 4. hill-lake sheet
    img, dr, px, pz, Hh = base(150, 1000, -800, 800, 0.7, "network_hill_lakes: the range's closed basins as lakes: brim levels (data), recommended levels (balance), spill points (red) and where each drains", 150)
    draw_network(dr, px, pz, 0.7, labels=True)
    y = Hh + 26
    for r in REACHES:
        if r["kind"] == "lake":
            dr.text((10, y), f"{r['id']}: {r['name']}; brim volume {r['vol_m3'] / 1e3:.0f} k m3", fill=(20, 20, 20))
            y += 18
    b = rep["balance"]
    dr.text((10, y + 4), f"balance: K {b['K_runoff_m3_per_yr'] / 1e3:.0f} k m3/yr ({b['mean_flow_K_L_per_s']} L/s mean), L {b['L_runoff_m3_per_yr'] / 1e3:.0f} k; lake evaporation {b['lake_evaporation_m3_per_yr']}; lake inflow {b['lake_inflow_m3_per_yr']} (rain 300 mm, runoff 0.3, evaporation 1,400 mm: assumptions)", fill=(20, 20, 20))
    img.save(os.path.join(out, "network_hill_lakes.png"))

    # 5. schematic
    W, Hh = 1500, 700
    img = Image.new("RGB", (W, Hh), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for yb, lab in [(90, "HILLS"), (330, "PARK (shelf at 0)"), (600, "SEA / LAGOON (-7.5)")]:
        dr.line([20, yb, W - 20, yb], fill=(200, 200, 200))
        dr.text((24, yb - 14), lab, fill=(120, 120, 120))
    nodes = {"K2": (260, 40), "K1": (300, 110), "takeoff": (380, 180), "cove": (120, 620), "falls": (420, 260), "P3": (440, 330), "P2": (330, 400), "notch": (250, 500), "sea1": (250, 620),
             "L0": (1100, 60), "fork": (1000, 190), "P1a": (960, 300), "P1b": (860, 330), "lobe": (960, 560), "eastbody": (1150, 600), "D3": (720, 360), "CC": (560, 400), "rainpond": (480, 470), "sea2": (480, 620), "E": (1050, 640)}
    edges = [("K2", "K1", "creek"), ("K1", "takeoff", "creek"), ("takeoff", "cove", "creek"), ("takeoff", "falls", "duct"), ("falls", "P3", "channel"), ("P3", "P2", "duct"), ("P2", "notch", "cascade"), ("notch", "sea1", "cascade"),
             ("L0", "fork", "creek"), ("fork", "eastbody", "creek"), ("fork", "P1a", "duct"), ("P1a", "P1b", "channel"), ("P1b", "lobe", "cascade"), ("P1b", "D3", "duct"), ("D3", "CC", "duct"), ("CC", "rainpond", "creek"), ("rainpond", "sea2", "creek"), ("eastbody", "E", "boat")]
    for a, b_, k in edges:
        pa, pb = nodes[a], nodes[b_]
        if k == "duct":
            dashed(dr, [pa, pb], AZURE, 4, 10)
        elif k == "boat":
            dashed(dr, [pa, pb], (150, 60, 200), 2, 6)
        else:
            dr.line([pa, pb], fill=AZURE if k != "cascade" else (0, 60, 200), width=4 if k != "creek" else 3)
    labels = {"K2": "tarn K2 +120", "K1": "lake K1 +70..80", "takeoff": "take-off +8.9", "cove": "north cove", "falls": "corner falls 7 m", "P3": "P3 -0.2", "P2": "P2 -0.6 (+9 ha runoff)", "notch": "notch weir, 7 m falls", "sea1": "sea",
              "L0": "lake L0 +72..92", "fork": "fork +9.3", "P1a": "P1a +3.9", "P1b": "P1b +2.9", "lobe": "NE lobe (slough)", "eastbody": "east body, under the arrival bridge", "D3": "D3 -0.3 (pop-up)", "CC": "Coastal Creek at CX1 -1.5", "rainpond": "rain pond -4.3, outfall -5.9", "sea2": "shore band / sea", "E": "E landing"}
    for k, (x, y) in nodes.items():
        dr.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(120, 170, 255), outline=AZURE, width=2)
        dr.text((x + 10, y - 6), labels[k], fill=(0, 40, 120))
    dr.text((20, Hh - 40), "network_schematic: solid = open creek/channel, dashed = underground (culvert, duct, siphon), dark = cascade/falls; entrance, Plaza, NT-1, NT-2 untouched (the siphon passes beneath the entrance)", fill=(20, 20, 20))
    img.save(os.path.join(out, "network_schematic.png"))

    # 6. reaches table
    rows = [["id", "kind", "length m", "fall m", "grade %", "levels / size", "note"]]
    for r in rep["reaches"]:
        if r["kind"] == "lake":
            rows.append([r["id"], "lake", "", "", "", f"level {r['level']}, {r['area_ha']} ha, {r['vol_m3'] / 1e3:.0f} k m3", r["name"][:150]])
        elif r["kind"] == "pond":
            rows.append([r["id"], "pond", "", "", "", f"level {r['level']:+.1f}, bed {r['bed']:+.1f}, {r['area_ha']} ha, dig {r['dig_m3']} m3", r["name"][:150]])
        else:
            extra = f"{r['size']}, invert {r['invert'][0]}..{r['invert'][1]}, cover {r['cover_min_m']}..{r['cover_max_m']} m" if r["kind"] == "duct" else f"water {r['wl'][0]}..{r['wl'][1]}"
            rows.append([r["id"], r["kind"], str(r["length_m"]), str(r["fall_m"]), str(r["gradient_pct"]), extra, r["name"][:150]])
    rows.append(["", "", "", "", "", "", ""])
    rows.append(["crossings", "", "", "", "", "", "; ".join(f"({x},{z}) {w}: {h}" for x, z, w, h in rep["crossings"])[:400]])
    widths = [70, 70, 80, 70, 70, 420, 980]
    img = Image.new("RGB", (sum(widths) + 40, 24 * len(rows) + 60), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for r_, row in enumerate(rows):
        x = 20
        y = 20 + r_ * 24
        dr.line([20, y - 5, sum(widths) + 20, y - 5], fill=(225, 225, 225))
        for v, w in zip(row, widths):
            dr.text((x, y), str(v)[:int(w / 5.6)], fill=(20, 20, 20))
            x += w
    dr.text((20, 24 * len(rows) + 30), f"network_reaches_table; K take-off open-cut alternative {rep['K_takeoff_open_cut_alternative_m3']} m3 (culvert chosen); balance: {rep['balance']['verdict'][:230]}", fill=(90, 90, 90))
    img.save(os.path.join(out, "network_reaches_table.png"))
    print("network: wrote overview, profiles, ponds, hill lakes, schematic, table")


# ----------------------------------------------------------------------------- Blender scratch copy
def curves(folder, out, master):
    import bpy
    scratch = os.path.join(folder, "PROPOSAL_water_network.blend")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    props = bpy.data.collections.get("Reference_proposals") or bpy.data.collections.new("Reference_proposals")
    if props.name not in [c.name for c in bpy.data.collections["Reference"].children]:
        bpy.data.collections["Reference"].children.link(props)

    def to_blender(x, y, z):
        return (x, -z, y)

    def curve(name, pts3, colour, bevel, note, closed=False):
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
    AZ = (0.0, 0.45, 1.0, 1.0)
    AZD = (0.0, 0.3, 0.7, 1.0)
    for r in REACHES:
        nm = f"PROPOSAL_network_{r['id']}"
        if r["kind"] == "lake":
            x, z = r["centre"]
            rr = math.sqrt(r["area_ha"] * 1e4 / math.pi)
            pts = [(x + rr * math.cos(a), r["level"], z + rr * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 33)[:-1]]
            curve(nm, pts, AZ, 2.0, r["name"], closed=True)
        elif r["kind"] == "pond":
            curve(nm, [(x, r["level"] + 0.2, z) for x, z in r["poly"]], AZ, 1.2, r["name"], closed=True)
        else:
            n = len(r["pts"])
            pts = [(x, (r["invert"][0] + (r["invert"][1] - r["invert"][0]) * i / max(1, n - 1)) if r["kind"] == "duct" else (r["wl"][0] + (r["wl"][1] - r["wl"][0]) * i / max(1, n - 1)) + 0.3, z) for i, (x, z) in enumerate(r["pts"])]
            curve(nm, pts, AZD if r["kind"] == "duct" else AZ, 1.0 if r["kind"] == "duct" else 2.0, r["name"] + (" [UNDERGROUND: drawn at the invert]" if r["kind"] == "duct" else ""))
    bpy.ops.wm.save_mainfile()
    print(f"network: scratch copy with PROPOSAL_network_* curves saved {scratch}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = argv[argv.index("--out") + 1]
    if "--analyse" in argv:
        analyse(argv[argv.index("--analyse") + 1], out)
    if "--draw" in argv:
        draw(argv[argv.index("--draw") + 1], out)
    if "--curves" in argv:
        master = argv[argv.index("--master") + 1] if "--master" in argv else os.path.join(os.getcwd(), "assets/source/world_terrain_master.blend")
        curves(argv[argv.index("--curves") + 1], out, master)


if __name__ == "__main__":
    main()
