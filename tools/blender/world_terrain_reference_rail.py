"""The regional railway along the south beach front, as REFERENCE curves in
the world terrain master (2026-10-01, Christina: "go with B, narrower beach,
rail climbs the bluff"; park-rebuild-masterplan.md, "The south beach front";
coastal-world-expansion-plan-2026-09-06.md, "North-south railway").

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/world_terrain_master.blend \
        --python tools/blender/world_terrain_reference_rail.py -- --design <applied_coast_design.json> --out <folder>
    python3 tools/blender/world_terrain_reference_rail.py --plot <folder>      # the z 1400 and z 1900 cross-sections, with PIL

Not a terrain edit: no vertex moves (the terrain_world vertex hash is
asserted equal before and after; the shelf is future earthworks). The
locked `Reference_rail` collection is cleared and redrawn:

- `rail_beach_town_from_plan_*`: the chosen line through the beach town as
  the Beach Town Plan draws it (the lagoon trestle, Shore Street's median,
  the station at the pier's root), copied from documentation/maps/
  beach-town-plan.html, draped on the master's ground; the plan's old-shore
  line south of the town kept as superseded.
- `rail_south_beach_front_centreline`: the line on the new shore edge, on
  the bench, RAIL_MARGIN landward of the beach crest, flat, from the
  station's south end to the departure.
- `rail_bluff_shelf_centreline`: from the departure the line swings landward
  and climbs the bluff face at MAX_GRADE on its own shelf: at height h its
  plan position is where the 1:2 face stands at that height (the foot at the
  old shore, -4 m), never closer than HIGHWAY_CLEAR to the highway's edge.
- `PROPOSAL_rail_to_bridge_landing`, `PROPOSAL_rail_deck_stub`: round the
  spur to the landing and along the approach to the deck, APPROXIMATE (the
  spit becomes water, the inlet fill, the lengthened bridge and the viaduct
  are decided and not built).

Assumed (the plan gives the grade only): single track, standard gauge,
corridor CORRIDOR_W, minimum radius MIN_RADIUS, maximum grade MAX_GRADE,
1:2 side slopes for the shelf's cut and fill.
"""

import hashlib
import json
import math
import os
import sys

import numpy as np

try:
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
except ImportError:
    bpy = None

SEA_LEVEL = -7.5
BENCH_H = -4.0
BEACH_W = 30.0
RAIL_MARGIN = 10.0       # m from the beach crest to the rail centreline on the bench
CORRIDOR_W = 7.5         # m: single track, 4.5 m formation plus 1.5 m each side
MIN_RADIUS = 300.0       # m, assumed (the plan gives none)
MAX_GRADE = 0.02         # the plan's "about 2 %"
FACE_SLOPE = 2.0         # the bluff face, horizontal per vertical (1:2)
HIGHWAY_W = 31.2
HIGHWAY_CLEAR = 5.0      # m the rail keeps from the highway's seaward edge
DECK_Y = 29.0            # Godot m, the bridge deck (hull y 28..30)
DECK_EAST = (150.0, 2452.0)
LANDING = (585.0, 2560.0)
STRIP_END_Z = 2240.0
WALL_CUT, WALL_FILL, TUNNEL_CUT = 8.0, 8.0, 15.0
PLAN_TRESTLE = [(70.0, 290.0), (8.0, 376.0), (0.0, 388.0)]
PLAN_TOWN = [(0.0, 388.0), (-6.0, 396.0), (-14.0, 400.0), (-40.0, 400.0), (-58.0, 400.0), (-66.0, 401.5), (-74.0, 406.5),
             (-81.38, 413.25), (-80.3, 417.25), (-79.22, 421.25), (-78.15, 425.25), (-77.07, 429.25), (-75.99, 433.25),
             (-74.92, 437.25), (-73.84, 441.25), (-72.76, 445.25), (-71.69, 449.25), (-70.61, 453.25), (-70.0, 470.0),
             (-71.0, 482.0), (-68.0, 494.0)]
PLAN_PLATFORM = [(-80.02, 427.9), (-82.92, 428.68), (-75.38, 456.68), (-72.48, 455.9)]
PLAN_TOWN_SOUTH = [(-68.0, 494.0), (-58.0, 515.0), (-46.0, 540.0), (-38.0, 560.0), (-22.0, 600.0), (12.0, 660.0), (40.0, 720.0), (92.0, 800.0)]
CONTINUATION = [(712.0, 2290.0), (728.0, 2340.0), (700.0, 2400.0), (650.0, 2470.0), (605.0, 2530.0), (585.0, 2560.0),
                (520.0, 2545.0), (420.0, 2500.0), (300.0, 2470.0), (150.0, 2452.0)]
BAY_LOOP_ARRIVAL = (650.0, 2535.0)


def to_blender(x, y, z):
    return (x, -z, y)


def circumradius(a, b, c):
    ab = math.hypot(b[0] - a[0], b[1] - a[1])
    bc = math.hypot(c[0] - b[0], c[1] - b[1])
    ca = math.hypot(a[0] - c[0], a[1] - c[1])
    s = (ab + bc + ca) / 2
    area = math.sqrt(max(s * (s - ab) * (s - bc) * (s - ca), 0.0))
    return math.inf if area < 1e-9 else ab * bc * ca / (4 * area)


def smooth_xy(pts, passes=2):
    p = np.array(pts, dtype=float)
    for _ in range(passes):
        q = p.copy()
        q[1:-1] = (p[:-2] + p[1:-1] + p[2:]) / 3.0
        p = q
    return [tuple(map(float, r)) for r in p]


def chain_of(pts):
    return np.concatenate([[0.0], np.cumsum([math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)])])


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--plot" in argv:
        plot(argv[argv.index("--plot") + 1])
        return
    design_path = argv[argv.index("--design") + 1]
    out_dir = argv[argv.index("--out") + 1]
    os.makedirs(out_dir, exist_ok=True)
    with open(design_path) as f:
        out = json.load(f)
    option = "B" if "B" in out["options"] else "A"
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

    # station geometry on the bench
    st = out["stations"]
    new_off = np.array(out["options"][option]["new_offset_per_station"])
    rows = []  # per usable station: (z, x, z, nx, nz, sh0, crest, rail_off_bench)
    for k, q in enumerate(st):
        if q["existing_shore_off"] is None or not (out["start_z"] <= q["z"] <= STRIP_END_Z):
            continue
        sh0 = q["existing_shore_off"]
        land = new_off[k] - sh0
        if land < 0.5:
            continue
        beach_w = min(BEACH_W, max(0.0, 0.6 * land))
        crest = new_off[k] - beach_w
        rail = crest - RAIL_MARGIN
        if rail < sh0 + 4.0:
            continue
        rows.append({"q": q, "sh0": sh0, "crest": crest, "rail_bench": rail, "hw_ground": q.get("highway_ground")})
    # the plan line on the bench, joined to the plan's station end; the chain to the deck sets the departure
    bench_pts = [(r["q"]["x"] + r["q"]["nx"] * r["rail_bench"], r["q"]["z"] + r["q"]["nz"] * r["rail_bench"]) for r in rows]
    head = [PLAN_TOWN[-3], PLAN_TOWN[-2], PLAN_TOWN[-1]]
    full_plan = smooth_xy(head + bench_pts + CONTINUATION, 3)
    ch = chain_of(full_plan)
    s_total = ch[-1]
    need = (DECK_Y - BENCH_H) / MAX_GRADE
    s_dep = s_total - need
    # heights along the full line: flat on the bench until s_dep, then +MAX_GRADE
    # plan offsets: on the bench until s_dep; beyond, where the 1:2 face stands at the rail's height, clear of the highway
    final = []
    per_station = []
    dep_xz = None
    n_head = len(head)
    for i, (x, z) in enumerate(full_plan):
        s_ = ch[i]
        h = BENCH_H + max(0.0, s_ - s_dep) * MAX_GRADE
        px, pz = x, z
        on_face = False
        if s_ > s_dep and n_head <= i < n_head + len(rows):
            r = rows[i - n_head]
            q = r["q"]
            face_off = r["sh0"] - FACE_SLOPE * (h - BENCH_H)
            face_off = max(face_off, HIGHWAY_W / 2 + HIGHWAY_CLEAR)
            # swing from the bench line to the face over the first 150 m of climb
            t = min(1.0, (s_ - s_dep) / 150.0)
            off = r["rail_bench"] * (1 - t) + face_off * t
            px, pz = q["x"] + q["nx"] * off, q["z"] + q["nz"] * off
            on_face = True
            if dep_xz is None:
                dep_xz = (px, pz)
        final.append((px, h, pz, on_face))
    final_xy = smooth_xy([(p[0], p[2]) for p in final], 6)  # the station-normal offsets and the swing leave 20 m wiggles; six passes keep the line, drop the wiggle
    final = [(xy[0], p[1], xy[1], p[3]) for xy, p in zip(final_xy, final)]
    # per 20 m station: ground, cut/fill with 1:2 side slopes
    stations = []
    chf = chain_of([(p[0], p[2]) for p in final])
    for i, (x, h, z, on_face) in enumerate(final):
        g = ground(x, z)
        cut = max(0.0, g - h)
        fill = max(0.0, h - g)
        stations.append({"s": float(chf[i]), "x": x, "z": z, "rail_y": h, "ground_y": g, "cut": cut, "fill": fill, "on_face": on_face,
                         "cut_area": CORRIDOR_W * cut + 2.0 * cut * cut, "fill_area": CORRIDOR_W * fill + 2.0 * fill * fill})
    ds = np.gradient(chf)
    cut_vol = float(sum(s_["cut_area"] * d for s_, d in zip(stations, ds)))
    fill_vol = float(sum(s_["fill_area"] * d for s_, d in zip(stations, ds)))
    walls = [s_ for s_ in stations if s_["cut"] > WALL_CUT or s_["fill"] > WALL_FILL]
    tunnels = [s_ for s_ in stations if s_["cut"] > TUNNEL_CUT]
    radii = [circumradius((final[i - 1][0], final[i - 1][2]), (final[i][0], final[i][2]), (final[i + 1][0], final[i + 1][2])) for i in range(1, len(final) - 1)]
    tight = [(final[i + 1][0], final[i + 1][2], radii[i]) for i in range(len(radii)) if radii[i] < MIN_RADIUS]
    # the highway: distance and relative level at each station (highway centreline from the design's stations)
    hw = [(q["x"], q["z"], q.get("highway_ground")) for q in st]
    hw_rel = []
    for s_ in stations:
        k = int(np.argmin([math.hypot(a - s_["x"], b - s_["z"]) for a, b, _ in hw]))
        d = math.hypot(hw[k][0] - s_["x"], hw[k][1] - s_["z"])
        hg = hw[k][2]
        hw_rel.append({"s": s_["s"], "dist_to_highway_centreline_m": d, "highway_ground_y": hg, "rail_y": s_["rail_y"],
                       "rail_minus_highway_m": None if hg is None else s_["rail_y"] - hg})
    min_hw = min(hw_rel, key=lambda r: r["dist_to_highway_centreline_m"])
    inside_envelope = [r for r in hw_rel if r["dist_to_highway_centreline_m"] < HIGHWAY_W / 2]
    bay_d = min(math.hypot(s_["x"] - BAY_LOOP_ARRIVAL[0], s_["z"] - BAY_LOOP_ARRIVAL[1]) for s_ in stations)
    climb = DECK_Y - BENCH_H
    report = {"option": option, "terrain_hash_before": hash_before, "rail_margin_m": RAIL_MARGIN, "corridor_w_m": CORRIDOR_W, "min_radius_assumed_m": MIN_RADIUS,
              "max_grade_assumed": MAX_GRADE, "face_slope": "1:2", "side_slopes": "1:2", "deck_y": DECK_Y,
              "length_m": float(chf[-1]), "shore_edge_length_m": float(s_dep), "climb_length_m": float(need), "climb_m": climb,
              "departure_godot_xz": dep_xz, "departure_z": dep_xz[1] if dep_xz else None, "strip_end_rail_y": float([s_["rail_y"] for s_ in stations if s_["z"] <= STRIP_END_Z][-1]),
              "min_radius_m": float(min(radii)), "radii_under_min": [(round(x), round(z), round(r)) for x, z, r in tight],
              "cut_volume_m3": cut_vol, "fill_volume_m3": fill_vol, "max_cut_m": float(max(s_["cut"] for s_ in stations)), "max_fill_m": float(max(s_["fill"] for s_ in stations)),
              "wall_candidate_stations": [(round(w["x"]), round(w["z"]), round(w["cut"], 1), round(w["fill"], 1)) for w in walls],
              "tunnel_candidate_stations": [(round(w["x"]), round(w["z"]), round(w["cut"], 1)) for w in tunnels],
              "highway": {"closest_m": min_hw, "stations_inside_highway_envelope": len(inside_envelope),
                          "note": "the rail stays seaward of the highway's edge by at least HIGHWAY_CLEAR; where the highway dives to the landing the rail is above it on its viaduct, seaward, no crossing"},
              "bay_loop_arrival_distance_m": bay_d, "stations": stations, "highway_relation": hw_rel[::5]}
    # cross-sections at z 1400 and z 1900 across the bench and the face
    sections = {}
    for zq in (1400.0, 1900.0):
        kq = int(np.argmin([abs(q["z"] - zq) for q in st]))
        q = st[kq]
        prof = [(float(o), ground(q["x"] + q["nx"] * o, q["z"] + q["nz"] * o)) for o in np.arange(-20.0, 200.0, 2.0)]
        r = min(rows, key=lambda r_: abs(r_["q"]["z"] - zq))
        sr = min(stations, key=lambda s_: abs(s_["z"] - zq))
        dx, dz = sr["x"] - q["x"], sr["z"] - q["z"]
        sections[str(int(zq))] = {"offsets_ground": prof, "old_shore_off": r["sh0"], "crest_off": r["crest"], "water_off": float(new_off[kq]),
                                  "rail_off": dx * q["nx"] + dz * q["nz"], "rail_y": sr["rail_y"], "on_face": sr["on_face"], "station": [q["x"], q["z"]]}
    report["sections"] = sections

    # --- the curves
    ref = bpy.data.collections["Reference"]
    coll = bpy.data.collections.get("Reference_rail")
    if coll is None:
        coll = bpy.data.collections.new("Reference_rail")
        ref.children.link(coll)
    coll.hide_select = True
    for o in list(coll.objects):
        bpy.data.objects.remove(o)

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
        m["kyt_reference"] = True
        cu.materials.append(m)
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts3) - 1)
        for i, p in enumerate(pts3):
            sp.points[i].co = (*to_blender(*p), 1.0)
        sp.use_cyclic_u = closed
        o = bpy.data.objects.new(name, cu)
        o["kyt_reference"] = True
        o["kyt_collision"] = "none"
        o["kyt_reference_group"] = "rail"
        o["kyt_note"] = note
        o.hide_select = True
        coll.objects.link(o)
        return o

    RAIL = (0.45, 0.2, 0.6, 1.0)
    PROP = (0.9, 0.3, 0.9, 1.0)
    curve("rail_beach_town_from_plan_trestle", [(x, ground(x, z) + 1.0, z) for x, z in PLAN_TRESTLE], RAIL, 2.5,
          "the lagoon trestle, about 100 m, as beach-town-plan.html draws it (chosen 2026-09-30); heights draped, the trestle deck is not modelled")
    curve("rail_beach_town_from_plan_town", [(x, ground(x, z) + 1.0, z) for x, z in PLAN_TOWN], RAIL, 2.5,
          "the line through the beach town, Shore Street's median to the station at the pier's root, as beach-town-plan.html draws it; heights draped")
    curve("rail_beach_town_from_plan_platform", [(x, ground(x, z) + 1.2, z) for x, z in PLAN_PLATFORM], RAIL, 1.5,
          "Beach Town station platform at the pier's root, as beach-town-plan.html draws it", closed=True)
    curve("rail_beach_town_plan_old_shore_line_superseded", [(x, ground(x, z) + 1.0, z) for x, z in PLAN_TOWN_SOUTH], (0.5, 0.5, 0.5, 1.0), 1.2,
          "the plan's line south of the town on the old shore, drawn before the extension; superseded")
    bench_part = [(p[0], p[1] + 0.3, p[2]) for p in final if not p[3] and p[2] <= (dep_xz[1] if dep_xz else STRIP_END_Z)]
    face_part = [(p[0], p[1] + 0.3, p[2]) for p in final if p[3] or (dep_xz and p[2] >= dep_xz[1] and p[2] <= STRIP_END_Z + 1)]
    cont_part = [(p[0], p[1] + 0.3, p[2]) for p in final if p[2] > STRIP_END_Z]
    curve("rail_south_beach_front_centreline", bench_part, RAIL, 3.0,
          f"the regional rail on the new shore edge: {RAIL_MARGIN:g} m landward of the beach crest, flat on the bench at about {BENCH_H:g} m, corridor {CORRIDOR_W:g} m, "
          f"from the station's south end to the departure at z {dep_xz[1]:.0f}")
    curve("rail_bluff_shelf_centreline", face_part, (0.6, 0.15, 0.3, 1.0), 3.0,
          f"from the departure the line swings landward and climbs the bluff face on its own shelf at {MAX_GRADE * 100:g} %: at height h it sits where the 1:2 face "
          f"stands at that height, never nearer than {HIGHWAY_CLEAR:g} m to the highway's edge; cut and fill with 1:2 side slopes are future earthworks (not terrain)")
    curve("PROPOSAL_rail_to_bridge_landing", cont_part, PROP, 3.0,
          "APPROXIMATE: still climbing at 2 %, round the spur seaward of the highway on an embankment/viaduct, to the landing and along the bridge approach to the deck's east end; "
          "the spit becomes water, the inlet fill, the lengthened bridge and the viaduct are decided and not built")
    curve("PROPOSAL_rail_deck_stub", [(x, DECK_Y + 0.5, z) for x, z in (DECK_EAST, (0.0, 2450.0), (-150.0, 2447.0))], PROP, 3.0,
          "APPROXIMATE: onto the bridge deck at about 29 m Godot toward the raised terminal")

    notes = bpy.data.texts.get("README")
    if notes:
        notes.write("\nREFERENCE: the regional rail redrawn for option B (tools/blender/world_terrain_reference_rail.py, 2026-10-01, no terrain edit):\n"
                    f"  on the shore edge to the departure at z {dep_xz[1]:.0f}, then up the bluff face on its own shelf at {MAX_GRADE * 100:g} % to the deck; "
                    f"cut {cut_vol / 1e3:.0f} k m3, fill {fill_vol / 1e3:.0f} k m3 with 1:2 side slopes; min radius {min(radii):.0f} m.\n")
    scene = bpy.context.scene
    scene["kyt_reference_notes"] = json.dumps(json.loads(scene.get("kyt_reference_notes", "[]")) +
                                              [{"group": "rail", "script": "tools/blender/world_terrain_reference_rail.py", "date": "2026-10-01", "option": option}])
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    hash_after = hashlib.sha1(co2.tobytes()).hexdigest()
    assert hash_after == hash_before, "the terrain moved"
    report["terrain_hash_after"] = hash_after
    bpy.ops.wm.save_mainfile()
    with open(os.path.join(out_dir, "reference_rail_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    for k in ("length_m", "shore_edge_length_m", "departure_godot_xz", "strip_end_rail_y", "min_radius_m", "radii_under_min", "cut_volume_m3", "fill_volume_m3",
              "max_cut_m", "max_fill_m", "wall_candidate_stations", "tunnel_candidate_stations", "highway", "bay_loop_arrival_distance_m"):
        print(f"reference_rail: {k}: {json.dumps(report[k])[:500]}")
    print(f"reference_rail: terrain hash {hash_before} == {hash_after}; saved {bpy.data.filepath}")
    render(out_dir, obj, dep_xz)


def render(folder, obj, dep_xz):
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
        print(f"reference_rail: rendered {scene.render.filepath}")

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

    top_down("reference_rail_top.png", -450.0, 950.0, 250.0, 2650.0)
    dx, dz = dep_xz if dep_xz else (400.0, 1470.0)
    top_down("reference_rail_departure_closeup.png", dx - 250.0, dx + 250.0, dz - 250.0, dz + 250.0, px=1800)
    top_down("reference_rail_south_end_closeup.png", 100.0, 900.0, 2100.0, 2700.0, px=1800)
    oblique("reference_rail_oblique_from_sea.png", (-600.0, 120.0, 1600.0), (300.0, -2.0, 1300.0), lens=35.0)
    oblique("reference_rail_oblique_bluff_shelf.png", (250.0, 60.0, 2450.0), (520.0, 15.0, 1900.0), lens=40.0)


def plot(folder):
    from PIL import Image, ImageDraw
    with open(os.path.join(folder, "reference_rail_report.json")) as f:
        r = json.load(f)
    for zq, s in r["sections"].items():
        offs = [o for o, _ in s["offsets_ground"]]
        g = [h for _, h in s["offsets_ground"]]
        W, H, pad = 1800, 520, 60
        img = Image.new("RGB", (W, H + pad), (250, 250, 248))
        dr = ImageDraw.Draw(img)
        hmin, hmax = -12.0, 36.0
        sx = lambda o: pad + (o - offs[0]) / (offs[-1] - offs[0]) * (W - 2 * pad)
        sy = lambda h: pad // 2 + H - 40 - (min(max(h, hmin), hmax) - hmin) / (hmax - hmin) * (H - 50)
        dr.rectangle([pad, pad // 2, W - pad, pad // 2 + H - 40], outline=(120, 120, 120))
        for hv in range(-10, 40, 5):
            dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
            dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
        dr.line([pad, sy(SEA_LEVEL), W - pad, sy(SEA_LEVEL)], fill=(120, 170, 230), width=2)
        hw = HIGHWAY_W / 2
        dr.rectangle([sx(-hw), sy(hmax), sx(hw), sy(hmin)], fill=(235, 235, 225))
        dr.line([(sx(o), sy(h)) for o, h in zip(offs, g) if h == h], fill=(60, 60, 60), width=3)
        marks = [(s["old_shore_off"], "bluff foot / old shore", (150, 90, 40)), (s["crest_off"], "beach crest", (200, 140, 40)), (s["water_off"], "waterline", (60, 120, 220))]
        for i, (o, label, col) in enumerate(marks):
            dr.line([sx(o), sy(hmin), sx(o), sy(hmax)], fill=col, width=2)
            dr.text((sx(o) + 3, pad // 2 + 8 + 14 * i), label, fill=col)
        ro, ry = s["rail_off"], s["rail_y"]
        dr.rectangle([sx(ro - r["corridor_w_m"] / 2), sy(ry + 1.2), sx(ro + r["corridor_w_m"] / 2), sy(ry)], fill=(170, 130, 200))
        dr.text((sx(ro) + 3, sy(ry) - 16), "rail" + (" (shelf)" if s["on_face"] else " (bench)"), fill=(110, 50, 150))
        dr.text((pad + 6, pad // 2 + H - 34), f"cross-section at z {zq}: ground (grey), sea -7.5 (blue), highway, bluff foot, bench, rail corridor {r['corridor_w_m']:g} m, "
                f"beach crest, waterline; offsets from the highway centreline in m, Godot heights", fill=(20, 20, 20))
        for o in range(0, int(offs[-1]) + 1, 20):
            dr.text((sx(o) - 8, pad // 2 + H - 20), f"{o}", fill=(60, 60, 60))
        img.save(os.path.join(folder, f"reference_rail_section_z{zq}.png"))
        print(f"reference_rail: wrote {os.path.join(folder, f'reference_rail_section_z{zq}.png')}")


if __name__ == "__main__":
    main()
