"""Two small reference changes in the world terrain master, decided 2026-10-01.

1. The last stretch of the regional rail, from about z 2140 round the spur to the
   bridge deck, is a VIADUCT (Christina, 2026-10-01), not an embankment. The
   bluff-shelf centreline is cut at z 2140 and the rest of it, together with the
   former `PROPOSAL_rail_to_bridge_landing`, becomes one curve
   `PROPOSAL_rail_viaduct_spur`; its deck height follows the 2 % profile as
   already drawn, so no point moves. The report gives the length, start and end
   heights and the height above the mounted ground along it. The plan gives no
   pier spacing, so none is assumed.
2. The canal outlet marker `PROPOSAL_water_lagoon_canal_outlet` moves from z 560
   (in the north taper, where the bench is 11 m wide) to the first station where
   the bench reaches its full width and the rail is straight (z 668 by default);
   it is redrawn as a bar across the new land from the old shore to the
   waterline, so it also shows the canal's course. A marker only.

Not a terrain edit: no vertex moves, the terrain_world vertex hash is asserted
equal before and after (9b68aacf... after edit 2 B). Cameras and lights for the
renders are made after the save and never saved.

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_reference_rail_viaduct.py --
        --design documentation/terrain/renders/applied_coast_design.json
        --out documentation/terrain/renders [--outlet-z 668] [--split-z 2140]
"""
import hashlib
import json
import math
import os
import sys

import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SEA_LEVEL = -7.5
BEACH_W = 30.0
RAIL_MARGIN = 10.0
CORRIDOR_W = 7.5


def to_blender(x, y, z):
    return (x, -z, y)


def to_godot(bx, by, bz):
    return (bx, bz, -by)


def chain_len(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][2] - pts[i][2]) for i in range(len(pts) - 1))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    design_path = argv[argv.index("--design") + 1]
    out_dir = argv[argv.index("--out") + 1]
    outlet_z = float(argv[argv.index("--outlet-z") + 1]) if "--outlet-z" in argv else 668.0
    split_z = float(argv[argv.index("--split-z") + 1]) if "--split-z" in argv else 2140.0
    os.makedirs(out_dir, exist_ok=True)
    with open(design_path) as f:
        design = json.load(f)

    obj = bpy.data.objects["terrain_world"]
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    hash_before = hashlib.sha1(co.tobytes()).hexdigest()
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    down = Vector((0.0, 0.0, -1.0))

    def ground(x, z):
        hit = bvh.ray_cast(Vector((x, -z, 1000.0)), down, 5000.0)
        if hit[0] is None:
            hit = bvh.ray_cast(Vector((x + 2e-3, -z + 2e-3, 1000.0)), down, 5000.0)
        return math.nan if hit[0] is None else float(hit[0].z)

    coll = bpy.data.collections["Reference_rail"]
    shelf = coll.objects["rail_bluff_shelf_centreline"]
    landing = coll.objects["PROPOSAL_rail_to_bridge_landing"]

    def points_of(o):
        return [to_godot(*p.co[:3]) for p in o.data.splines[0].points]

    shelf_pts = points_of(shelf)
    landing_pts = points_of(landing)
    # the shelf curve is drawn north to south (z rising); split at the first point at or past split_z
    k = next(i for i, p in enumerate(shelf_pts) if p[2] >= split_z)
    shelf_keep = shelf_pts[:k + 1]
    viaduct_pts = shelf_pts[k:] + landing_pts
    assert abs(shelf_keep[-1][2] - split_z) < 25.0, f"split point z {shelf_keep[-1][2]:.0f} is not near {split_z:.0f}"

    def set_points(o, pts3):
        cu = o.data
        sp = cu.splines[0]
        cu.splines.remove(sp)
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts3) - 1)
        for i, p in enumerate(pts3):
            sp.points[i].co = (*to_blender(*p), 1.0)

    def curve(collection, name, pts3, colour, bevel, note):
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
        m["kyt_reference"] = True
        cu.materials.append(m)
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts3) - 1)
        for i, p in enumerate(pts3):
            sp.points[i].co = (*to_blender(*p), 1.0)
        o = bpy.data.objects.new(name, cu)
        o["kyt_reference"] = True
        o["kyt_collision"] = "none"
        o["kyt_reference_group"] = "rail"
        o["kyt_note"] = note
        o.hide_select = True
        collection.objects.link(o)
        return o

    # --- 1. the viaduct
    gs = [ground(p[0], p[2]) for p in viaduct_pts]
    above = [p[1] - 0.3 - g for p, g in zip(viaduct_pts, gs) if g == g]  # the curves sit 0.3 m over the rail level
    length = chain_len(viaduct_pts)
    h0, h1 = viaduct_pts[0][1] - 0.3, viaduct_pts[-1][1] - 0.3
    report = {"split_godot_xz": [viaduct_pts[0][0], viaduct_pts[0][2]], "end_godot_xz": [viaduct_pts[-1][0], viaduct_pts[-1][2]],
              "viaduct_length_m": length, "rail_y_start": h0, "rail_y_end": h1, "grade": (h1 - h0) / length,
              "height_above_ground_m": {"min": float(min(above)), "median": float(np.median(above)), "max": float(max(above))},
              "points_over_sea_level_ground": int(sum(1 for g in gs if g == g and g <= SEA_LEVEL + 0.5)),
              "points": [{"x": p[0], "z": p[2], "rail_y": p[1] - 0.3, "ground_y": g, "above_m": (p[1] - 0.3 - g) if g == g else None} for p, g in zip(viaduct_pts, gs)],
              "pier_spacing": "none assumed: the plan gives none", "terrain_hash_before": hash_before}
    set_points(shelf, shelf_keep)
    shelf["kyt_note"] = (str(shelf.get("kyt_note", "")) +
                         f" | ends at z {shelf_keep[-1][2]:.0f}, where the viaduct begins (decided 2026-10-01)")
    bpy.data.objects.remove(landing)
    note = (f"viaduct, decided 2026-10-01; deck height follows the 2 % profile: {length:.0f} m from ({viaduct_pts[0][0]:.0f}, {viaduct_pts[0][2]:.0f}) at "
            f"{h0:.1f} m round the spur, seaward of the highway, to the bridge deck's east end at {h1:.1f} m; "
            f"{np.median(above):.0f} m above the mounted ground at the median (max {max(above):.0f} m); the spur's ground, the beach and the inlet stay open "
            f"beneath it, and a canal, a lane or a path can pass under; pier spacing not assumed (the plan gives none). "
            "The spit becomes water, the inlet fill and the lengthened bridge are decided and not built.")
    curve(coll, "PROPOSAL_rail_viaduct_spur", viaduct_pts, (1.0, 0.55, 0.95, 1.0), 3.0, note)

    # --- 2. the canal outlet marker
    props = bpy.data.collections["Reference_proposals"]
    mk = props.objects["PROPOSAL_water_lagoon_canal_outlet"]
    old_pts = points_of(mk)
    old_z = old_pts[0][2]
    st = design["stations"]
    new_off = design["options"]["B"]["new_offset_per_station"]
    k = int(np.argmin([abs(q["z"] - outlet_z) for q in st]))
    q = st[k]
    sh0 = q["existing_shore_off"]
    land = new_off[k] - sh0
    beach = min(BEACH_W, max(0.0, 0.6 * land))
    bench = land - beach
    rail_off = new_off[k] - beach - RAIL_MARGIN
    # the bar: along the station's normal from 10 m inside the old shore (the bluff foot) to 10 m past the waterline
    bar = [(q["x"] + q["nx"] * o, q["z"] + q["nz"] * o, SEA_LEVEL + 4.0) for o in (sh0 - 10.0, new_off[k] + 10.0)]
    set_points(mk, [(x, y, z) for x, z, y in bar])
    mk["kyt_previous_at_godot_xz"] = json.dumps([old_pts[0][0] + 25.0, old_z])
    mk["kyt_note"] = (f"a canal from the lagoon could leave through the new land here, south of the ferry landing; moved from z {old_z:.0f} to z {q['z']:.0f} on 2026-10-01: "
                      f"at z {old_z:.0f} the bench was 11 m wide (the north taper), here the land is {land:.0f} m from the old shore (bench {bench:.0f} m, beach {beach:.0f} m), "
                      f"the first station at full width, and the rail on the bench is straight (radius over 900 m) from z 610 to z 670, so it crosses on one short square bridge. "
                      f"The bar runs from the bluff foot to the waterline along the canal's course; the rail centreline crosses it {rail_off:.0f} m from the highway centreline. "
                      "A marker only: the canal is a proposal (world_terrain_proposals_canals.py); the lagoon-to-outlet link crosses the beach town's bluff and would be a culvert.")
    report["outlet_marker"] = {"from_z": old_z, "to_z": q["z"], "station_godot_xz": [q["x"], q["z"]], "normal_xz": [q["nx"], q["nz"]],
                               "old_shore_off": sh0, "waterline_off": new_off[k], "land_m": land, "bench_m": bench, "beach_m": beach, "rail_off": rail_off,
                               "bar_godot_xz": [[b[0], b[1]] for b in bar]}

    notes = bpy.data.texts.get("README")
    if notes:
        notes.write("\nREFERENCE: the rail's last stretch is a viaduct (tools/blender/world_terrain_reference_rail_viaduct.py, 2026-10-01, no terrain edit):\n"
                    f"  rail_bluff_shelf_centreline ends at z {shelf_keep[-1][2]:.0f}; PROPOSAL_rail_viaduct_spur, {length:.0f} m, {h0:.1f} -> {h1:.1f} m, "
                    f"{np.median(above):.0f} m over the ground at the median, replaces PROPOSAL_rail_to_bridge_landing.\n"
                    f"  PROPOSAL_water_lagoon_canal_outlet moved from z {old_z:.0f} to z {q['z']:.0f} (full-width bench, straight rail) and drawn bluff foot to waterline.\n")
    scene = bpy.context.scene
    scene["kyt_reference_notes"] = json.dumps(json.loads(scene.get("kyt_reference_notes", "[]")) +
                                              [{"group": "rail", "script": "tools/blender/world_terrain_reference_rail_viaduct.py", "date": "2026-10-01",
                                                "viaduct_from_z": shelf_keep[-1][2], "outlet_marker_z": q["z"]}])
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    hash_after = hashlib.sha1(co2.tobytes()).hexdigest()
    assert hash_after == hash_before, "the terrain moved"
    report["terrain_hash_after"] = hash_after
    report["cameras_or_lights_in_file"] = [o.name for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]
    bpy.ops.wm.save_mainfile()
    with open(os.path.join(out_dir, "reference_rail_viaduct_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    for key in ("split_godot_xz", "end_godot_xz", "viaduct_length_m", "rail_y_start", "rail_y_end", "grade", "height_above_ground_m",
                "points_over_sea_level_ground", "outlet_marker", "cameras_or_lights_in_file"):
        print(f"reference_rail_viaduct: {key}: {json.dumps(report[key])[:400]}")
    print(f"reference_rail_viaduct: terrain hash {hash_before} == {hash_after}; saved {bpy.data.filepath}")
    render(out_dir, obj, viaduct_pts, bar)


def render(folder, obj, viaduct_pts, bar):
    scene = bpy.context.scene
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()
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
        print(f"reference_rail_viaduct: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2000):
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

    xs = [p[0] for p in viaduct_pts]
    zs = [p[2] for p in viaduct_pts]
    top_down("reference_rail_viaduct_spur_top.png", min(xs) - 80.0, max(xs) + 80.0, min(zs) - 80.0, max(zs) + 80.0)
    oblique("reference_rail_viaduct_spur_oblique.png", (950.0, 120.0, 2050.0), (520.0, 15.0, 2420.0), lens=35.0)
    mx, mz = (bar[0][0] + bar[1][0]) / 2, (bar[0][1] + bar[1][1]) / 2
    top_down("reference_rail_viaduct_outlet_marker_top.png", mx - 220.0, mx + 220.0, mz - 220.0, mz + 220.0)
    oblique("reference_rail_viaduct_outlet_marker_oblique.png", (mx - 420.0, 110.0, mz + 160.0), (mx + 40.0, -4.0, mz), lens=40.0)


if __name__ == "__main__":
    main()
