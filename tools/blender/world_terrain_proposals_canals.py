"""Canals from the tidal lagoon into the park, PROPOSAL only (2026-10-01,
Christina: "yes connect the canal to the park's canals"; no in-park canals
exist in any plan, so three topologies are proposed for her to choose from).

    python3 tools/blender/world_terrain_proposals_canals.py --analyse <folder>     # needs <folder>/park_raster10.npz
    Blender --background --factory-startup \
        --python tools/blender/world_terrain_proposals_canals.py -- --render <folder>   # scratch copy, curves, renders

Nothing touches the master, ParkPlan, the generator, the game or the maps.
The raster is the master's ground sampled every 10 m over x -300..500,
z -300..800 (ray casts; made beside this tool). Levels are Godot metres:
the plaza datum is 0, the sea and the lagoon -7.5 (ParkPlan.WATER_TOP; the
entrance plan says "sea level, -7.5 m"), the shore band -6 (SHORE_TOP).

Options (Godot x, z; water at the lagoon's level unless a lock lifts it):
- A, the shore loop: lagoon -> a cut through the arrival court's west edge ->
  the shore band's landward edge north along the Boardwalk, past NT-1 (kept
  clear by 25 m), to the band's north end; and lagoon -> the beach-front
  outlet. Tidal, gated at the lagoon.
- B, the creek corridor with locks: lagoon north-east lobe -> up the
  approach valley -> the entrance -> Coastal Creek's corridor to the shore
  band. Non-tidal above the first lock (fed by the creek / rain pond).
- C, the Boardwalk pair: two short canals in the shore band either side of
  NT-1, fed from the lagoon by a culvert under the arrival court. Tidal.
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
except ImportError:
    bpy = None

SEA = -7.5
LAGOON = -7.5          # the lagoon's level, held near sea level by the tide gates
TIDE = 0.5             # m, assumed muted range inside the gates (ocean +-0.6 assumed)
DEPTH = 1.5            # m of water for paddle boats and the glass-bottom boat
WIDTH = {"A": 12.0, "B": 8.0, "C": 8.0}   # m: two-way with a 4 m glass-bottom boat (A), paddle boats only (B, C)
SIDE = 1.0             # side slopes 1:1 in the cut (area = w*d + d*d)
NT1 = (-69.5, -2.0)    # NT-1's foot (STAIR_FOOT); its band z -34..16 (BLUFF_TOP_FROM/TO_Z) is kept clear by 25 m
NT1_CLEAR_Z = (-34.0 - 25.0, 16.0 + 25.0)
SHORE_X = (-108.0, -56.0)   # SHORE_EDGE .. SHORE_FROM_X, the shore band
OUTLET_Z = 560.0

ROUTES = {
    "A": {"colour": (0.0, 0.45, 1.0, 1.0), "legs": [
        {"name": "lagoon to the shore band (cut through the arrival court's west edge)", "pts": [(-70.0, 318.0), (-70.0, 290.0), (-68.0, 250.0), (-66.0, 225.0)], "level": LAGOON},
        {"name": "shore band north, landward edge, to the band's north end", "pts": [(-66.0, 225.0), (-64.0, 60.0), (-64.0, 41.0)], "level": LAGOON},
        {"name": "shore band north of NT-1 to the north end", "pts": [(-64.0, -59.0), (-64.0, -150.0), (-64.0, -230.0)], "level": LAGOON},
        {"name": "lagoon to the beach-front outlet", "pts": [(-40.0, 384.0), (-30.0, 430.0), (-10.0, 500.0), (0.0, 540.0), (20.0, 560.0)], "level": LAGOON},
    ]},
    "B": {"colour": (0.0, 0.45, 1.0, 1.0), "legs": [
        {"name": "north-east lobe up the approach valley to the entrance (tidal, as the slough)", "pts": [(150.0, 200.0), (140.0, 180.0), (120.0, 160.0), (90.0, 150.0)], "level": LAGOON},
        {"name": "lock flight at the entrance (two locks, +3.75 m each)", "pts": [(90.0, 150.0), (60.0, 140.0)], "level": LAGOON + 3.75},
        {"name": "across the entrance precinct to Coastal Creek's head (non-tidal, creek-fed)", "pts": [(60.0, 140.0), (0.0, 110.0), (-48.0, 60.0), (-48.0, 22.0)], "level": 0.0 - DEPTH - 0.5},
        {"name": "Coastal Creek's corridor to the shore band, lock down (-2 m)", "pts": [(-48.0, 22.0), (-62.0, 44.0), (-79.0, 54.0), (-104.0, 55.0)], "level": LAGOON},
    ]},
    "C": {"colour": (0.0, 0.45, 1.0, 1.0), "legs": [
        {"name": "culvert from the lagoon under the arrival court (buried pipe, no open cut)", "pts": [(-70.0, 318.0), (-70.0, 225.0)], "level": LAGOON, "culvert": True},
        {"name": "south canal in the shore band, z 200..60", "pts": [(-70.0, 225.0), (-72.0, 200.0), (-72.0, 60.0), (-72.0, 41.0)], "level": LAGOON},
        {"name": "north canal in the shore band, z -59..-200", "pts": [(-72.0, -59.0), (-72.0, -200.0)], "level": LAGOON},
    ]},
}
CROSSINGS = {  # z or (x, z) lines the canals pass, from the plans and the master's references
    "A": ["Beach Road / the bluff-top walk at the lagoon's north bank (bridge)", "the arrival court's west garden path (bridge)",
          "route B north return / the Boardwalk's landward walk, bridged at each deck access (3-4)", "the pier root and wheel deck (kept 25 m clear)",
          "the regional rail on the new shore edge at z 560 (rail bridge)", "the beach-front lane (bridge)", "the beach (groyne pair)"],
    "B": ["the arrival bridge over the lobe (exists in the plan)", "the front road z 236 (bridge)", "the arrival allee / entrance street (bridge or the canal in its median)",
          "the arcade and turnstiles precinct (conflict: the arrival axis)", "Coastal Creek's guest bridges (exist in 05A)", "route B north return (bridge)"],
    "C": ["none open at the arrival court (culvert)", "route B north return / Boardwalk accesses (2 per canal)", "the pier root (kept 25 m clear)"],
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


def analyse(folder):
    d = np.load(os.path.join(folder, "park_raster10.npz"))
    H, xs, zs = d["H"], d["xs"], d["zs"]
    X, Z = np.meshgrid(xs, zs)
    low = (H <= SEA + 3.0) & (H > SEA - 3.0)
    out = {"datum": {"plaza": 0.0, "sea": SEA, "lagoon": LAGOON, "tide_assumed_m": TIDE, "shore_top": -6.0, "beach_front_bench": -4.0},
           "low_ground": {"cells_10m_within_3m_of_sea": int(low.sum()), "area_ha": float(low.sum() * 100 / 1e4),
                          "where": "the shore band x -108..-56 at -6 m (z -230..220, the Boardwalk deck and NT-1's foot), the lagoon basin, the beach-front bench at -4 m, the new beach; "
                                   "the entrance fields are 0..+1, the plaza 0, the belvedere +5.5, the hill behind to +20"},
           "options": {}}
    for key, r in ROUTES.items():
        w = WIDTH[key]
        legs = []
        total_len = total_vol = 0.0
        max_cut = 0.0
        profile = []
        s_acc = 0.0
        for leg in r["legs"]:
            pts = leg["pts"]
            level = leg["level"]
            bed = level - DEPTH
            seg_len = vol = 0.0
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                n = max(2, int(L / 5))
                for k in range(n):
                    t = k / n
                    x, z = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
                    g = bilinear(H, xs, zs, x, z)
                    cut = max(0.0, g - bed)
                    max_cut = max(max_cut, cut if not leg.get("culvert") else 0.0)
                    area = 0.0 if leg.get("culvert") else (w * cut + SIDE * cut * cut)
                    vol += area * (L / n)
                    profile.append({"s": s_acc + seg_len + t * L, "x": x, "z": z, "ground": g, "water": level, "bed": bed, "cut": cut, "culvert": bool(leg.get("culvert"))})
                seg_len += L
            legs.append({"name": leg["name"], "length_m": seg_len, "water_level": level, "cut_volume_m3": vol, "culvert": bool(leg.get("culvert"))})
            total_len += seg_len
            total_vol += vol
            s_acc += seg_len
        out["options"][key] = {"width_m": w, "depth_m": DEPTH, "side_slopes": "1:1", "legs": legs, "length_m": total_len, "cut_volume_m3": total_vol,
                               "max_cut_depth_m": max_cut, "crossings": CROSSINGS[key], "profile": profile, "colour": r["colour"]}
        print(f"canals: option {key}: {total_len:.0f} m, cut {total_vol / 1e3:.0f} k m3, deepest cut {max_cut:.1f} m, {len(CROSSINGS[key])} crossing items")
    # the waterfall feasibility at the lagoon's north-east corner
    cx, cz = 172.0, 205.0
    dd = np.hypot(X - cx, Z - cz)
    wf = {"corner_ground": bilinear(H, xs, zs, cx, cz), "lagoon_level": LAGOON}
    for rad in (100, 200, 300, 400):
        m = (dd < rad) & (X > cx - 20)
        k = int(np.nanargmax(np.where(m, H, -1e9)))
        wf[f"max_ground_within_{rad}m"] = {"height": float(H.flat[k]), "at": [float(X.flat[k]), float(Z.flat[k])]}
    # the high ground east: ridge line sample along x from the corner
    ridge = [(float(x), bilinear(H, xs, zs, x, cz)) for x in range(int(cx), 500, 25)]
    wf["ground_east_along_z205"] = ridge
    wf["note"] = ("a creek from the east hill could reach the corner: the ground rises east of the lagoon; the drop from the nearest 20 m contour to the "
                  "lagoon (-7.5) is the fall available; a catchment of the hill's west face (order 20-40 ha) feeds a seasonal creek, not a river")
    out["waterfall"] = wf
    print(f"canals: waterfall: corner ground {wf['corner_ground']:.1f} m; max within 100/200/300 m: "
          + ", ".join(f"{wf[f'max_ground_within_{r}m']['height']:.0f} m at {wf[f'max_ground_within_{r}m']['at']}" for r in (100, 200, 300)))
    out["outlet"] = {"marker_z": OUTLET_Z,
                     "recommendation": "move the outlet to about z 640-700 where the bench is full width and the rail is straight; cross the rail on one short bridge; "
                                       "pass the beach between a groyne pair like the lagoon mouth (8 m rock mounds, shorter, 40-60 m); its own tide gate at the bench "
                                       "so the canal can be held still while the lagoon's gates run; flow: open at the lagoon end on the ebb and the sea end on the flood so the "
                                       "canal flushes once a tide"}
    with open(os.path.join(folder, "proposal_canals.json"), "w") as f:
        json.dump(out, f)
    plots(folder, out)


def plots(folder, out):
    from PIL import Image, ImageDraw
    keys = list(out["options"])
    W, Hh, pad = 2000, 380, 60
    img = Image.new("RGB", (W, Hh * len(keys) + pad), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for k, key in enumerate(keys):
        o = out["options"][key]
        top = k * Hh + pad // 2
        pr = o["profile"]
        s = np.array([p["s"] for p in pr])
        g = np.array([p["ground"] for p in pr])
        wl = np.array([p["water"] for p in pr])
        bed = np.array([p["bed"] for p in pr])
        hmin, hmax = -12.0, max(12.0, float(np.nanmax(g)) + 2)
        sx = lambda v: pad + v / s[-1] * (W - 2 * pad)
        sy = lambda h: top + Hh - 40 - (min(max(h, hmin), hmax) - hmin) / (hmax - hmin) * (Hh - 50)
        dr.rectangle([pad, top, W - pad, top + Hh - 40], outline=(120, 120, 120))
        for hv in range(-10, int(hmax) + 1, 5):
            dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
            dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
        for m in range(len(s) - 1):
            if g[m] > bed[m] and not pr[m]["culvert"]:
                dr.rectangle([sx(s[m]), sy(g[m]), sx(s[m + 1]) + 1, sy(bed[m])], fill=(235, 190, 150))
        dr.line([(sx(a), sy(b)) for a, b in zip(s, g)], fill=(60, 60, 60), width=2)
        col = tuple(int(c * 255) for c in o["colour"][:3])
        dr.line([(sx(a), sy(b)) for a, b in zip(s, wl)], fill=col, width=3)
        dr.line([(sx(a), sy(b)) for a, b in zip(s, bed)], fill=(120, 90, 60), width=1)
        dr.text((pad + 6, top + 4), f"option {key}: ground (grey), water level (colour), bed (brown), cut shaded; {o['length_m']:.0f} m, "
                f"cut {o['cut_volume_m3'] / 1e3:.0f} k m3, deepest {o['max_cut_depth_m']:.1f} m, width {o['width_m']:g} m, depth {o['depth_m']:g} m; Godot heights, plaza 0, sea -7.5", fill=(20, 20, 20))
        acc = 0.0
        for leg in o["legs"]:
            dr.line([sx(acc), sy(hmin), sx(acc), sy(hmax)], fill=(200, 200, 200))
            dr.text((sx(acc) + 3, top + Hh - 36), leg["name"][:60], fill=(80, 80, 80))
            acc += leg["length_m"]
    img.save(os.path.join(folder, "proposal_canals_profiles.png"))
    rows = [("option", "length m", "cut k m3", "deepest cut m", "width m", "water", "crossings / structures")]
    for key in keys:
        o = out["options"][key]
        rows.append((key, f"{o['length_m']:.0f}", f"{o['cut_volume_m3'] / 1e3:.0f}", f"{o['max_cut_depth_m']:.1f}", f"{o['width_m']:g}",
                     "tidal" if all(l["water_level"] == LAGOON for l in o["legs"]) else "tidal + locked/creek-fed", str(len(o["crossings"]))))
    cw = [90, 110, 110, 130, 90, 190, 180]
    timg = Image.new("RGB", (sum(cw) + 20, 30 * len(rows) + 20), (250, 250, 248))
    td = ImageDraw.Draw(timg)
    for rI, row in enumerate(rows):
        x = 10
        for cI, cell in enumerate(row):
            td.text((x, 10 + rI * 30), str(cell), fill=(20, 20, 20) if rI else (90, 40, 40))
            x += cw[cI]
    timg.save(os.path.join(folder, "proposal_canals_table.png"))
    print(f"canals: wrote profiles and table in {folder}")


def render(folder, master):
    with open(os.path.join(folder, "proposal_canals.json")) as f:
        out = json.load(f)
    scratch = os.path.join(folder, "PROPOSAL_canals.blend")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    scene = bpy.context.scene
    obj = bpy.data.objects["terrain_world"]
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()
    coll = bpy.data.collections.get("Reference_proposals")
    if coll is None:
        coll = bpy.data.collections.new("Reference_proposals")
        bpy.data.collections["Reference"].children.link(coll)

    def curve(name, pts3, colour, bevel, note=""):
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
        sp.points.add(len(pts3) - 1)
        for i, p in enumerate(pts3):
            sp.points[i].co = (p[0], -p[2], p[1], 1.0)
        o = bpy.data.objects.new(name, cu)
        o["kyt_proposal"] = True
        o["kyt_reference"] = True
        o["kyt_collision"] = "none"
        if note:
            o["kyt_note"] = note
        coll.objects.link(o)
        return o

    objs = {}
    for key, o in out["options"].items():
        col = tuple(o["colour"])
        for li, leg in enumerate(o["legs"]):
            pts = [p for p in o["profile"] if True]
        # draw each leg from the ROUTES points at the water level + 1 m (visible), culverts thinner
        for li, leg in enumerate(ROUTES[key]["legs"]):
            pts3 = [(x, leg["level"] + 1.0 + (8.0 if leg.get("culvert") else 0.0), z) for x, z in leg["pts"]]
            objs.setdefault(key, []).append(curve(f"PROPOSAL_canal_{key}_{li}_{leg['name'][:30].replace(' ', '_')}", pts3, col, 2.0 if leg.get("culvert") else 4.0, leg["name"]))
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
        print(f"canals: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2400):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = (cx, -cz, 5000.0)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            scene.render.resolution_x, scene.render.resolution_y = px, int(px * ez / ex)
        else:
            scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
        shoot(name)

    def oblique(name, eye, aim, lens=35.0):
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector((eye[0], -eye[2], eye[1])), Vector((aim[0], -aim[2], aim[1]))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
        shoot(name)

    top_down("proposal_canals_top.png", -320.0, 420.0, -300.0, 700.0)
    for key in objs:
        for k2, lst in objs.items():
            for o in lst:
                o.hide_render = k2 != key
        top_down(f"proposal_canals_top_{key}.png", -320.0, 420.0, -300.0, 700.0)
    for k2, lst in objs.items():
        for o in lst:
            o.hide_render = k2 != "C"
    oblique("proposal_canals_oblique_C.png", (-450.0, 120.0, 420.0), (-70.0, -6.0, 60.0), lens=35.0)
    for k2, lst in objs.items():
        for o in lst:
            o.hide_render = k2 != "A"
    oblique("proposal_canals_oblique_A.png", (-450.0, 140.0, 520.0), (-60.0, -6.0, 120.0), lens=35.0)
    bpy.ops.wm.save_mainfile()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--analyse" in argv:
        analyse(argv[argv.index("--analyse") + 1])
    elif "--render" in argv:
        folder = argv[argv.index("--render") + 1]
        master = argv[argv.index("--master") + 1] if "--master" in argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "assets", "source", "world_terrain_master.blend")
        render(folder, os.path.abspath(master))
    else:
        raise SystemExit("canals: --analyse <folder> | --render <folder>")


if __name__ == "__main__":
    main()
