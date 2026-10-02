"""The ferry route as a REFERENCE curve in the world terrain master (2026-10-01, Christina:
"add the ferry route"). Source: documentation/maps/detailed-world-map.html (and its
planning/ copy, byte-identical), polyline "Ferry to the city (A)" (-190, 440) -> (-360, 1320)
-> (-610, 2115) in Godot x,z, class w-civil; the circle "Ferry landing (A) at the pier's
head" at (-190, 440). The master's three ferry markers stay where they are.

Not a terrain edit: the terrain_world vertex hash is asserted equal. Also recolours the
sunset wedge and the 294 degree bearing as sightlines (thin lilac) so they are not read as
routes, and gives the ferry route a route colour (teal). Cameras and lights for the
renders are made after the save and never saved.

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_reference_ferry.py -- --out documentation/terrain/renders
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
ROUTE_Y = SEA_LEVEL + 0.05
MAP_ROUTE = [(-190.0, 440.0), (-360.0, 1320.0), (-610.0, 2115.0)]   # detailed-world-map.html, "Ferry to the city (A)"
ARC_RADIUS = 2000.0          # m: a gentle arc through the bay waypoint; a ferry cannot turn at a point
PIER_HEAD = (-152.0, 6.0)
LAGOON_MOUTH_SEA_END = (-193.0, 336.0)   # the mouth channel's seaward end (entrance plan: x -193..-88, z 326..346)
BAY_LOOP_ARRIVAL = (650.0, 2535.0)
SIGHT_COL = (0.75, 0.6, 1.0, 1.0)   # sightlines: lilac, thin
SIGHT_BEVEL = 2.0
ROUTE_COL = (0.0, 0.8, 0.8, 1.0)    # routes: teal
ROUTE_BEVEL = 4.0


def to_blender(x, y, z):
    return (x, -z, y)


def arc_through(p0, p1, p2, R, step=25.0):
    """p0-p1-p2 polyline with the corner at p1 rounded by a circular arc of radius R, sampled every `step` m."""
    a = np.array(p0)
    b = np.array(p1)
    c = np.array(p2)
    d1 = (b - a) / np.linalg.norm(b - a)
    d2 = (c - b) / np.linalg.norm(c - b)
    theta = math.acos(max(-1.0, min(1.0, float(np.dot(d1, d2)))))
    T = R * math.tan(theta / 2.0)
    t1 = b - d1 * T
    t2 = b + d2 * T
    pts = []
    n1 = max(2, int(np.linalg.norm(t1 - a) / step))
    for i in range(n1):
        pts.append(tuple(a + (t1 - a) * i / n1))
    # the arc: centre on the inside bisector
    turn = np.sign(d1[0] * d2[1] - d1[1] * d2[0])   # +1 left turn in (x, z) plane as drawn
    n1p = np.array([-d1[1], d1[0]]) * turn
    centre = t1 + n1p * R
    a0 = math.atan2(t1[1] - centre[1], t1[0] - centre[0])
    a1 = math.atan2(t2[1] - centre[1], t2[0] - centre[0])
    da = a1 - a0
    while da > math.pi:
        da -= 2 * math.pi
    while da < -math.pi:
        da += 2 * math.pi
    na = max(4, int(abs(da) * R / step))
    for i in range(na + 1):
        ang = a0 + da * i / na
        pts.append((centre[0] + R * math.cos(ang), centre[1] + R * math.sin(ang)))
    n2 = max(2, int(np.linalg.norm(c - t2) / step))
    for i in range(1, n2 + 1):
        pts.append(tuple(t2 + (c - t2) * i / n2))
    mid_offset = R * (1.0 / math.cos(theta / 2.0) - 1.0)
    return [(float(x), float(z)) for x, z in pts], {"deflection_deg": math.degrees(theta), "tangent_length_m": T, "arc_midpoint_offset_from_waypoint_m": mid_offset}


def seg_dist(p, a, b):
    p, a, b = np.array(p), np.array(a), np.array(b)
    ab = b - a
    t = float(np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0.0, 1.0))
    return float(np.linalg.norm(p - (a + ab * t)))


def poly_dist(pts, poly, closed=False):
    best = (1e9, None)
    segs = list(zip(poly, poly[1:] + ([poly[0]] if closed else [])))
    for p in pts:
        for a, b in segs:
            d = seg_dist(p, a, b)
            if d < best[0]:
                best = (d, p)
    return best


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out_dir = argv[argv.index("--out") + 1]
    os.makedirs(out_dir, exist_ok=True)
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

    def pts_of(name):
        o = bpy.data.objects[name]
        return [(p.co[0], -p.co[1]) for s in o.data.splines for p in s.points]

    route, arc = arc_through(*MAP_ROUTE, ARC_RADIUS)
    length = sum(math.hypot(route[i + 1][0] - route[i][0], route[i + 1][1] - route[i][1]) for i in range(len(route) - 1))
    # checks
    shore = pts_of("coast_extension_B_shoreline")
    d_shore, at_shore = poly_dist(route, shore)
    pen = pts_of("city_peninsula_footprint")
    d_pen, at_pen = poly_dist(route, pen, closed=True)
    deck = pts_of("bridge_main_deck_footprint")
    d_deck, at_deck = poly_dist(route, deck, closed=True)
    via = pts_of("PROPOSAL_rail_viaduct_spur")
    d_via, at_via = poly_dist(route, via)
    outlet = pts_of("PROPOSAL_water_lagoon_canal_outlet")
    d_out, at_out = poly_dist(route, outlet)
    d_mouth = min(math.hypot(p[0] - LAGOON_MOUTH_SEA_END[0], p[1] - LAGOON_MOUTH_SEA_END[1]) for p in route)
    d_bay = min(math.hypot(p[0] - BAY_LOOP_ARRIVAL[0], p[1] - BAY_LOOP_ARRIVAL[1]) for p in route)
    bearings = [(math.degrees(math.atan2(p[0] - PIER_HEAD[0], -(p[1] - PIER_HEAD[1]))) + 360.0) % 360.0 for p in route]
    in_wedge = [p for p, b in zip(route, bearings) if 280.0 <= b <= 310.0]
    depths = [ground(x, z) for x, z in route]
    depth_ok = [d for d in depths if d == d]
    markers = {k: tuple(bpy.data.objects[k].location) for k in ("beach_town_ferry_landing_marker", "bay_ferry_hull_marker", "city_ferry_landing_marker")}
    markers_godot = {k: (v[0], -v[1]) for k, v in markers.items()}
    report = {"source": "documentation/maps/detailed-world-map.html, 'Ferry to the city (A)' (planning/ copy byte-identical)", "map_route_godot_xz": MAP_ROUTE,
              "arc_radius_m": ARC_RADIUS, "arc": arc, "length_m": length, "points": len(route),
              "endpoints_deviation_m": [0.0, 0.0], "waypoint_deviation_m": arc["arc_midpoint_offset_from_waypoint_m"],
              "markers_godot_xz": markers_godot,
              "marker_vs_map": {"beach_town": {"marker": markers_godot["beach_town_ferry_landing_marker"], "map_pier_head": MAP_ROUTE[0],
                                               "note": "the map's landing polygon is x -190..-96 at z 434..446; the marker is its midpoint, the route starts at its head: 47 m apart"},
                                "city": {"marker": markers_godot["city_ferry_landing_marker"], "map_pier_head": MAP_ROUTE[2],
                                         "note": "the map's landing polygon is x -621..-599, z 2115..2220 with the pier head at z 2101..2129; the marker is the landing's midpoint, the route ends at the head: 53 m apart"},
                                "bay": {"marker": markers_godot["bay_ferry_hull_marker"], "map_waypoint": MAP_ROUTE[1], "note": "the hull marker is the waypoint; the arc passes %.1f m inside it" % arc["arc_midpoint_offset_from_waypoint_m"]}},
              "clearances_m": {"coast_extension_B_shoreline": [d_shore, at_shore], "lagoon_mouth_sea_end": d_mouth, "canal_outlet_marker": [d_out, at_out],
                               "bay_loop_arrival": d_bay, "rail_viaduct_spur": [d_via, at_via], "city_peninsula_footprint": [d_pen, at_pen], "bridge_main_deck_footprint": [d_deck, at_deck]},
              "sunset_wedge_280_310": {"route_bearings_from_pier_head_deg": [min(bearings), max(bearings)], "points_inside": in_wedge, "crosses": bool(in_wedge)},
              "seabed_under_route_godot_y": {"min": min(depth_ok), "max": max(depth_ok), "note": "PLACEHOLDER bathymetry: the game has no seabed; the master's open-sea cells are a stand-in shelf"},
              "shallow_points_under_2m": [(round(p[0]), round(p[1]), round(d, 1)) for p, d in zip(route, depths) if d == d and d > SEA_LEVEL - 2.0],
              "terrain_hash_before": hash_before}

    # --- the curve
    ref = bpy.data.collections["Reference"]
    coll = bpy.data.collections.get("Reference_ferry")
    if coll is None:
        coll = bpy.data.collections.new("Reference_ferry")
        ref.children.link(coll)
    coll.hide_select = True
    for o in list(coll.objects):
        bpy.data.objects.remove(o)

    def emission(mat, colour):
        mat.use_nodes = True
        nt = mat.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        o_ = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = colour
        nt.links.new(em.outputs[0], o_.inputs[0])

    cu = bpy.data.curves.new("ferry_route_beach_town_to_city", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = ROUTE_BEVEL
    cu.bevel_resolution = 0
    m = bpy.data.materials.new("ref_ferry_route_beach_town_to_city")
    emission(m, ROUTE_COL)
    m["kyt_reference"] = True
    cu.materials.append(m)
    sp = cu.splines.new("POLY")
    sp.points.add(len(route) - 1)
    for i, (x, z) in enumerate(route):
        sp.points[i].co = (*to_blender(x, ROUTE_Y, z), 1.0)
    o = bpy.data.objects.new("ferry_route_beach_town_to_city", cu)
    o["kyt_reference"] = True
    o["kyt_collision"] = "none"
    o["kyt_reference_group"] = "ferry"
    o["kyt_note"] = (f"the bay ferry's route, beach town pier head (-190, 440) to the city ferry pier head (-610, 2115) via (-360, 1320), as documentation/maps/detailed-world-map.html "
                     f"draws 'Ferry to the city (A)'; the corner at the bay waypoint is an arc of radius {ARC_RADIUS:.0f} m passing {arc['arc_midpoint_offset_from_waypoint_m']:.1f} m inside it, "
                     f"endpoints exact; {length:.0f} m; drawn at sea level + 0.05. The three ferry markers (landing midpoints and the hull) are the GLB's and stay. Route colour teal; the sunset lines are lilac sightlines.")
    o.hide_select = True
    coll.objects.link(o)

    # --- recolour the sightlines
    for name in ("sunset_water_wedge_280_310", "sunset_bearing_294"):
        s = bpy.data.objects.get(name)
        if s is None:
            continue
        s.data.bevel_depth = SIGHT_BEVEL
        for mat in s.data.materials:
            emission(mat, SIGHT_COL)
        s["kyt_note"] = str(s.get("kyt_note", "")) + " | sightline, not a route: lilac, thin (2026-10-01)"

    notes = bpy.data.texts.get("README")
    if notes:
        notes.write("\nREFERENCE: the ferry route (tools/blender/world_terrain_reference_ferry.py, 2026-10-01, no terrain edit):\n"
                    f"  ferry_route_beach_town_to_city <- documentation/maps/detailed-world-map.html 'Ferry to the city (A)'; arc radius {ARC_RADIUS:.0f} m at the bay waypoint; {length:.0f} m.\n"
                    "  KEY: routes (ferry) are teal, bevel 4; sightlines (sunset_water_wedge_280_310, sunset_bearing_294) are lilac, bevel 2; the ferry markers are the GLB's landing midpoints and hull.\n")
    scene = bpy.context.scene
    scene["kyt_reference_notes"] = json.dumps(json.loads(scene.get("kyt_reference_notes", "[]")) +
                                              [{"group": "ferry", "script": "tools/blender/world_terrain_reference_ferry.py", "date": "2026-10-01"}])
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    hash_after = hashlib.sha1(co2.tobytes()).hexdigest()
    assert hash_after == hash_before, "the terrain moved"
    report["terrain_hash_after"] = hash_after
    report["cameras_or_lights_in_file"] = [ob.name for ob in bpy.data.objects if ob.type in ("CAMERA", "LIGHT")]
    bpy.ops.wm.save_mainfile()
    with open(os.path.join(out_dir, "reference_ferry_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    for k in ("arc", "length_m", "marker_vs_map", "clearances_m", "sunset_wedge_280_310", "seabed_under_route_godot_y", "shallow_points_under_2m", "cameras_or_lights_in_file"):
        print(f"reference_ferry: {k}: {json.dumps(report[k])[:600]}")
    print(f"reference_ferry: terrain hash {hash_before} == {hash_after}; saved {bpy.data.filepath}")
    render(out_dir, obj)


def render(folder, obj):
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
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        print(f"reference_ferry: rendered {scene.render.filepath}")

    top_down("reference_ferry_top.png", -1100.0, 800.0, -300.0, 2700.0)
    top_down("reference_ferry_pierhead.png", -420.0, 80.0, 200.0, 700.0, px=1800)


if __name__ == "__main__":
    main()
