"""Authored edit 2 on the world terrain master: the south beach front, option
A of the coast extension (2026-10-01, Christina: option A, 100 m, the 3.5 m
bench, the rail on the new shore edge; recorded in park-rebuild-masterplan.md,
"The south beach front").

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/world_terrain_master.blend \
        --python tools/blender/world_terrain_edit_coast_extension.py -- --work <folder> [--render <folder>] [--undo] [--dry]

The ground is exactly the proposal's (`world_terrain_coast_extension.py`,
whose sampling, shoreline and surface this script imports and re-runs on
the master): the bench at -4.0 m Godot (3.5 m over the -7.5 m sea) falling
1 % seaward to a crest 3 m over the sea, a 45 m beach at 1:15, a 1:15 shelf
to the placeholder seabed; the shoreline of option A (100 m of land between
the highway's seaward edge and the water) from z 504 to z 2336; the highway's
ground and the bluff untouched.

Reversible and logged, as edit 1 (`blend_south_range`):
- `authored_edit = 2` on every vertex it moves. `height_pre_edit` stays one
  float: edit 1's polygon is z >= 5250 and this edit is z <= 2600, so the two
  sets are disjoint (asserted), and for these vertices the stored pre-edit
  height equals the height before this edit (asserted).
- A moved vertex that ends above sea level is AUTHORED land, not sampled:
  `placeholder_bathymetry` is cleared on it, `sampled` stays false,
  `authored_land` (new, bool) is set; `ground_y_sampled` is untouched.
- The log is appended to `terrain_world["kyt_edits"]` and the in-file README;
  the option A shoreline goes into the locked Reference collection as
  `coast_extension_A_shoreline`, the three water candidates into
  `Reference_proposals` as PROPOSAL markers.
- `--undo` restores exactly these vertices (height, flags, colours), removes
  the curves and the log entry. The builder's guard names both edits.
"""

import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world_terrain_coast_extension as CE  # noqa: E402

try:
    import bpy
    from mathutils import Vector
except ImportError:
    bpy = None

EDIT_ID = 2
EDIT_NAME = "coast_extension_B"   # replaces coast_extension_A (Christina 2026-10-01: "go with B, narrower beach, rail climbs the bluff")
OPTION = "B"
SEA_LEVEL = CE.SEA_LEVEL
STATION = CE.STATION


def attr(me, name, dtype):
    out = np.zeros(len(me.vertices), dtype=dtype)
    me.attributes[name].data.foreach_get("value", out)
    return out


def vertex_hash(co, sel=None):
    return hashlib.sha1((co if sel is None else co[sel]).tobytes()).hexdigest()


def design_heights(me, co0, out):
    """Option A's surface for every vertex it raises: (heights, changed)."""
    n = len(me.vertices)
    offs = np.array(out["offsets"])
    stations = out["stations"]
    sx_ = np.array([q["x"] for q in stations])
    sz_ = np.array([q["z"] for q in stations])
    snx = np.array([q["nx"] for q in stations])
    snz = np.array([q["nz"] for q in stations])
    tx, tz = -snz, snx
    opt = out["options"][OPTION]
    new_off = np.array(opt["new_offset_per_station"])
    heights = co0.copy()
    changed = np.zeros(n, dtype=bool)
    X, Z = co0[:, 0], -co0[:, 1]
    box = (Z >= out["start_z"] - 300) & (Z <= out["end_z"] + 300) & (X <= 1000.0)
    rows = [np.array([np.nan if r is None else r for r in row]) for row in out["ground_rows"]]
    for v in np.nonzero(box)[0]:
        dx, dz = X[v] - sx_, Z[v] - sz_
        k = int(np.argmin(np.hypot(dx, dz)))
        along = dx[k] * tx[k] + dz[k] * tz[k]
        off = dx[k] * snx[k] + dz[k] * snz[k]
        if abs(along) > STATION * 0.75 or off < 0:
            continue
        q = stations[k]
        if q["existing_shore_off"] is None:
            continue
        sh0 = q["existing_shore_off"]
        if new_off[k] - sh0 < 0.5:
            continue
        h = CE.design_height(off, sh0, new_off[k], CE.BENCH_H, rows[k], offs, g=float(co0[v, 2]))
        if h > co0[v, 2] + 1e-3:
            heights[v, 2] = h
            changed[v] = True
    return heights, changed


def bury_curve(terrain, name, out):
    from mathutils.bvhtree import BVHTree
    o = bpy.data.objects.get(name)
    if o is None or o.type != "CURVE" or o.get("kyt_edit2_restore"):
        return
    bvh = BVHTree.FromObject(terrain, bpy.context.evaluated_depsgraph_get())
    down = Vector((0.0, 0.0, -1.0))
    orig = {}
    z0, z1 = out["start_z"] - 30.0, out["end_z"] + 60.0
    for si, sp in enumerate(o.data.splines):
        for pi, p in enumerate(sp.points):
            gz = -p.co[1]
            if z0 <= gz <= z1:
                hit = bvh.ray_cast(Vector((p.co[0], p.co[1], 1000.0)), down, 5000.0)
                if hit[0] is not None:
                    # 8 m under the ground: the tube's 6 m bevel then stays 2 m below the surface
                    orig[f"{si}:{pi}"] = float(p.co[2])
                    p.co[2] = min(p.co[2], hit[0].z - 8.0)
    if orig:
        o["kyt_edit2_restore"] = json.dumps(orig)
        o["kyt_note_edit2"] = ("sunk under the south beach front between z %d and %d by authored edit 2; the extension supersedes this "
                               "stretch of the generator's shoreline; --undo lifts it back" % (z0, z1))
        print(f"{EDIT_NAME}: {name}: {len(orig)} points sunk under the new land")


def ref_curve(coll, name, pts, colour, bevel, note=""):
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
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*CE.to_blender(*p), 1.0)
    o = bpy.data.objects.new(name, cu)
    o["kyt_reference"] = True
    o["kyt_collision"] = "none"
    o["kyt_edit_id"] = EDIT_ID
    if note:
        o["kyt_note"] = note
    o.hide_select = True
    coll.objects.link(o)
    return o


def edge_stats(me, co, mask_a, mask_b=None):
    """Largest |dh|/length and |dh| over mesh edges with one end in mask_a
    (and the other in mask_b, or any)."""
    ev = np.empty(len(me.edges) * 2, dtype=np.int32)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)
    a, b = ev[:, 0], ev[:, 1]
    sel = mask_a[a] | mask_a[b] if mask_b is None else (mask_a[a] & mask_b[b]) | (mask_a[b] & mask_b[a])
    if mask_b is not None and mask_b is mask_a:
        sel = mask_a[a] & mask_a[b]
    if not sel.any():
        return 0.0, 0.0, 0
    d = np.abs(co[a[sel], 2] - co[b[sel], 2])
    L = np.hypot(co[a[sel], 0] - co[b[sel], 0], co[a[sel], 1] - co[b[sel], 1])
    return float((d / np.maximum(L, 1e-6)).max()), float(d.max()), int(sel.sum())


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    work = argv[argv.index("--work") + 1] if "--work" in argv else os.path.join(os.path.dirname(bpy.data.filepath), "_coast_work")
    render_dir = argv[argv.index("--render") + 1] if "--render" in argv else None
    undo = "--undo" in argv
    dry = "--dry" in argv
    obj = bpy.data.objects.get("terrain_world")
    if obj is None:
        raise SystemExit(f"{EDIT_NAME}: no terrain_world in this file")
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    aid = attr(me, "authored_edit", np.int32) if "authored_edit" in me.attributes else np.zeros(n, dtype=np.int32)
    pre = attr(me, "height_pre_edit", float) if "height_pre_edit" in me.attributes else co[:, 2].copy()
    sampled = attr(me, "sampled", bool)
    edits = json.loads(obj.get("kyt_edits", "[]"))

    if undo:
        sel = aid == EDIT_ID
        if not sel.any():
            raise SystemExit(f"{EDIT_NAME}: nothing to undo")
        co[sel, 2] = pre[sel]
        me.vertices.foreach_set("co", co.ravel())
        aid[sel] = 0
        me.attributes["authored_edit"].data.foreach_set("value", aid)
        pb = attr(me, "placeholder_bathymetry", bool)
        pb[sel] = ~sampled[sel]
        me.attributes["placeholder_bathymetry"].data.foreach_set("value", pb)
        if "authored_land" in me.attributes:
            al = attr(me, "authored_land", bool)
            al[sel] = False
            me.attributes["authored_land"].data.foreach_set("value", al)
        if "height_shade_pre_edit2" in me.color_attributes:
            c = np.empty(n * 4)
            me.color_attributes["height_shade_pre_edit2"].data.foreach_get("color", c)
            cur = np.empty(n * 4)
            me.color_attributes["height_shade"].data.foreach_get("color", cur)
            c, cur = c.reshape(-1, 4), cur.reshape(-1, 4)
            cur[sel] = c[sel]
            me.color_attributes["height_shade"].data.foreach_set("color", cur.ravel())
            me.color_attributes.remove(me.color_attributes["height_shade_pre_edit2"])
        for o in list(bpy.data.objects):
            if o.get("kyt_edit_id") == EDIT_ID:
                bpy.data.objects.remove(o)
        for o in bpy.data.objects:
            if o.type == "CURVE" and o.get("kyt_edit2_restore"):
                orig = json.loads(o["kyt_edit2_restore"])
                for key, z in orig.items():
                    si, pi = (int(t) for t in key.split(":"))
                    o.data.splines[si].points[pi].co[2] = z
                del o["kyt_edit2_restore"]
                if "kyt_note_edit2" in o:
                    del o["kyt_note_edit2"]
        obj["kyt_edits"] = json.dumps([e for e in edits if e.get("id") != EDIT_ID])
        notes = bpy.data.texts.get("README")
        if notes:
            notes.write(f"\nAUTHORED EDIT {EDIT_ID} ({EDIT_NAME}) UNDONE on {int(sel.sum())} vertices.\n")
        me.update()
        bpy.ops.wm.save_mainfile()
        print(f"{EDIT_NAME}: undone on {int(sel.sum())} vertices and saved")
        return

    if any(e.get("id") == EDIT_ID for e in edits):
        raise SystemExit(f"{EDIT_NAME}: edit 2 is already applied (kyt_edits); run with --undo first")

    # the proposal's sampling and design, re-run on this very file
    os.makedirs(work, exist_ok=True)
    CE.sample(work)
    CE.design(work)
    with open(os.path.join(work, "proposal_coast_extension.json")) as f:
        out = json.load(f)
    heights, changed = design_heights(me, co, out)
    sel = changed
    # the two edits are disjoint, and the single height_pre_edit is valid for this edit
    assert not (sel & (aid == 1)).any(), "edit 2 would touch an edit 1 vertex"
    assert np.array_equal(pre[sel], co[sel, 2]), "height_pre_edit differs from the current height on an edit 2 vertex"
    hash_all_before = vertex_hash(co)
    hash_outside_before = vertex_hash(co, ~sel)
    hash_edit1_before = vertex_hash(co, aid == 1)
    report = {"id": EDIT_ID, "name": EDIT_NAME, "script": "tools/blender/world_terrain_edit_coast_extension.py", "option": OPTION,
              "depth_m": out["options"][OPTION]["depth_m"], "bench_h_godot": CE.BENCH_H, "bench_fall": CE.BENCH_FALL, "beach_w_m": CE.BEACH_W,
              "beach_slope": CE.BEACH_SLOPE, "shelf_slope": CE.SHELF_SLOPE, "z_from": out["options"][OPTION]["from_z"], "z_to": out["options"][OPTION]["to_z"],
              "polygon_godot_xz": out["options"][OPTION]["polygon_godot_xz"], "vertices_moved": int(sel.sum()),
              "max_raise_m": float((heights[:, 2] - co[:, 2])[sel].max()) if sel.any() else 0.0,
              "proposal_area_ha": out["options"][OPTION]["area_ha"], "sunset": out["sunset"][OPTION],
              "mesh_hash_before": hash_all_before, "outside_hash_before": hash_outside_before, "edit1_hash_before": hash_edit1_before}
    for k, v in report.items():
        if k not in ("polygon_godot_xz", "sunset"):
            print(f"{EDIT_NAME}: {k}: {v}")
    if dry:
        return

    # colours before, for the undo
    cur = np.empty(n * 4)
    me.color_attributes["height_shade"].data.foreach_get("color", cur)
    cur = cur.reshape(-1, 4)
    keep = me.color_attributes.new("height_shade_pre_edit2", "FLOAT_COLOR", "POINT")
    keep.data.foreach_set("color", cur.ravel())
    # apply
    co[sel, 2] = heights[sel, 2]
    me.vertices.foreach_set("co", co.ravel())
    aid[sel] = EDIT_ID
    if "authored_edit" not in me.attributes:
        me.attributes.new("authored_edit", "INT", "POINT")
    me.attributes["authored_edit"].data.foreach_set("value", aid)
    if "height_pre_edit" not in me.attributes:
        me.attributes.new("height_pre_edit", "FLOAT", "POINT")
        me.attributes["height_pre_edit"].data.foreach_set("value", pre)
    land = sel & (co[:, 2] > SEA_LEVEL)
    pb = attr(me, "placeholder_bathymetry", bool)
    pb[land] = False
    me.attributes["placeholder_bathymetry"].data.foreach_set("value", pb)
    if "authored_land" not in me.attributes:
        me.attributes.new("authored_land", "BOOLEAN", "POINT")
    al = attr(me, "authored_land", bool)
    al[land] = True
    me.attributes["authored_land"].data.foreach_set("value", al)
    col = cur.copy()
    col[land & (co[:, 2] <= -3.0)] = (0.88, 0.82, 0.62, 1.0)
    col[land & (co[:, 2] > -3.0)] = (0.70, 0.80, 0.52, 1.0)
    me.color_attributes["height_shade"].data.foreach_set("color", col.ravel())
    me.update()

    # the generator's coast outline (ParkPlan.COAST_SOUTH_OUTLINE, a 6 m reference tube at sea level + 0.3)
    # now runs through the new land; its tube's top (-1.2 m) poked up through the -4 m bench as a broken
    # blue line (her "random line of water"). Under the new land it is sunk 8 m below the new ground;
    # the original point heights are kept on the object for --undo.
    bury_curve(obj, "coast_south_outline", out)
    # reference curves
    ref_coast = bpy.data.collections.get("Reference_coast") or bpy.data.collections["Reference"]
    line = out["options"][OPTION]["new_shoreline_godot_xz"]
    ref_curve(ref_coast, f"coast_extension_{OPTION}_shoreline", [(x, SEA_LEVEL + 1.0, z) for x, z in line], (1.0, 0.55, 0.1, 1.0), 4.0,
              f"the south beach front's waterline, option {OPTION}: {out['options'][OPTION]['depth_m']:g} m of land between the highway's seaward edge and the water, "
              "the bench at -4 m Godot, a 30 m beach; the rail runs on this edge then climbs the bluff (park-rebuild-masterplan.md, The south beach front)")
    props = bpy.data.collections.get("Reference_proposals")
    if props is None:
        props = bpy.data.collections.new("Reference_proposals")
        bpy.data.collections["Reference"].children.link(props)
    props.hide_select = True
    for mk in out["water_markers"]:
        x, z = mk["at_godot_xz"]
        ref_curve(props, f"PROPOSAL_water_{mk['name']}", [(x - 25, SEA_LEVEL + 4.0, z), (x + 25, SEA_LEVEL + 4.0, z)], (0.3, 0.5, 1.0, 1.0), 4.0, mk["note"])

    # verification on the mesh itself
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    co2 = co2.reshape(-1, 3)
    report["outside_hash_after"] = vertex_hash(co2, ~sel)
    report["edit1_hash_after"] = vertex_hash(co2, aid == 1)
    assert report["outside_hash_after"] == hash_outside_before and report["edit1_hash_after"] == hash_edit1_before
    gs = attr(me, "ground_y_sampled", float)
    up = attr(me, "top_from_upray", bool)
    chk = (aid == 0) & sampled & ~up
    report["unedited_sampled_vs_ground_y_sampled_max_m"] = float(np.abs(co2[chk, 2] - gs[chk]).max())
    report["unedited_equal_height_pre_edit"] = bool(np.array_equal(co2[aid == 0, 2], pre[aid == 0]))
    grid = attr(me, "grid", np.int32)
    cell = np.where(grid == 0, 625.0, 100.0)  # the 25 m lattice and the 10 m patches
    report["area_new_land_ha_master"] = float(cell[land].sum() / 1e4)
    bench = land & (co2[:, 2] > -4.6)
    beach = land & (co2[:, 2] <= -4.6)
    report["bench_vertices"], report["beach_vertices"] = int(bench.sum()), int(beach.sum())
    report["bench_max_slope"] = edge_stats(me, co2, bench, bench)[0]
    report["beach_max_slope"] = edge_stats(me, co2, beach, beach)[0]
    report["edit_edges_max_slope"], report["edit_edges_max_jump_m"], _ = edge_stats(me, co2, sel, sel)
    outside = ~sel
    report["seam_max_slope"], report["seam_max_jump_m"], report["seam_edges"] = edge_stats(me, co2, sel, outside)
    # the highway's ground: vertices within HIGHWAY_W/2 of the centreline, untouched
    hw = out["stations"]
    hx = np.array([q["x"] for q in hw])
    hz = np.array([q["z"] for q in hw])
    X, Z = co2[:, 0], -co2[:, 1]
    near_hw = np.zeros(n, dtype=bool)
    for v in np.nonzero((Z >= 300) & (Z <= 2600) & (X < 1000))[0]:
        if np.min(np.hypot(hx - X[v], hz - Z[v])) <= CE.HIGHWAY_W / 2:
            near_hw[v] = True
    report["highway_vertices_moved"] = int((near_hw & sel).sum())
    # shoreline smoothness: the largest turn between successive 20 m chords
    turns = []
    for i in range(1, len(line) - 1):
        a = np.array(line[i]) - np.array(line[i - 1])
        b = np.array(line[i + 1]) - np.array(line[i])
        turns.append(abs(np.degrees(np.arctan2(a[0] * b[1] - a[1] * b[0], np.dot(a, b)))))
    report["shoreline_max_turn_deg_per_20m"] = float(max(turns)) if turns else 0.0
    report["cameras_or_lights"] = [o.name for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]
    report["placeholder_cleared"] = int(land.sum())
    # the bench width, every 100 m: the -4 m level between the bluff foot (old shore) and the beach crest
    bench_rows = []
    for q, no in zip(out["stations"], out["options"][OPTION]["new_offset_per_station"]):
        if q["existing_shore_off"] is None or not (out["start_z"] <= q["z"] <= out["end_z"]):
            continue
        land_w = no - q["existing_shore_off"]
        if land_w < 0.5:
            continue
        bw = min(CE.BEACH_W, max(0.0, 0.6 * land_w))
        width = land_w - bw
        bench_rows.append({"z": round(q["z"]), "land_from_old_shore_m": round(land_w, 1), "beach_m": round(bw, 1), "bench_width_m": round(width, 1),
                           "left_after_rail_m": round(width - 10.0 - 7.5 / 2 - 7.5 / 2, 1)})
    report["bench_width_every_100m"] = bench_rows[::5]
    widths = [r["bench_width_m"] for r in bench_rows]
    lefts = [r["left_after_rail_m"] for r in bench_rows]
    report["bench_width_m"] = {"min": min(widths), "median": float(np.median(widths)), "max": max(widths)}
    report["left_after_rail_m"] = {"min": min(lefts), "median": float(np.median(lefts)), "max": max(lefts)}
    # pockets: any vertex on the new land's bench zone (between the highway edge and the beach crest) still at sea level
    # pockets: any vertex inside the new land's polygon, more than 10 m landward of the waterline,
    # within 0.3 m of sea level or under it (the water plane would show through)
    pockets = []
    Xp, Zp = co2[:, 0], -co2[:, 1]
    opt = out["options"][OPTION]
    poly = opt["polygon_godot_xz"]
    new_off = np.array(opt["new_offset_per_station"])
    hw = out["stations"]
    hx = np.array([q["x"] for q in hw]); hz = np.array([q["z"] for q in hw])
    hnx = np.array([q["nx"] for q in hw]); hnz = np.array([q["nz"] for q in hw])

    def pip(x, z):
        inside = False
        m = len(poly)
        for i in range(m):
            x0, z0 = poly[i]
            x1, z1 = poly[(i + 1) % m]
            if (z0 > z) != (z1 > z) and x0 + (z - z0) * (x1 - x0) / (z1 - z0) > x:
                inside = not inside
        return inside

    for v in np.nonzero((Zp >= out["start_z"] - 50) & (Zp <= out["end_z"] + 50) & (Xp < 1000) & (co2[:, 2] <= SEA_LEVEL + 0.3))[0]:
        if not pip(Xp[v], Zp[v]):
            continue
        dx, dz = Xp[v] - hx, Zp[v] - hz
        k = int(np.argmin(np.hypot(dx, dz)))
        off = dx[k] * hnx[k] + dz[k] * hnz[k]
        if off <= new_off[k] - 10.0:
            pockets.append({"at_godot_xz": [float(Xp[v]), float(Zp[v])], "station_z": float(hz[k]), "height": float(co2[v, 2]), "offset": float(off)})
    report["sea_level_cells_on_bench"] = len(pockets)
    report["sea_level_cells_on_bench_list"] = pockets[:40]
    report["swale_filled"] = True
    report["mesh_hash_after"] = vertex_hash(co2)
    for k in ("outside_hash_after", "edit1_hash_after", "unedited_sampled_vs_ground_y_sampled_max_m", "unedited_equal_height_pre_edit",
              "area_new_land_ha_master", "bench_vertices", "beach_vertices", "bench_max_slope", "beach_max_slope", "edit_edges_max_slope",
              "edit_edges_max_jump_m", "seam_max_slope", "seam_max_jump_m", "seam_edges", "highway_vertices_moved",
              "shoreline_max_turn_deg_per_20m", "cameras_or_lights", "placeholder_cleared", "sea_level_cells_on_bench", "bench_width_m",
              "left_after_rail_m", "mesh_hash_after"):
        print(f"{EDIT_NAME}: {k}: {report[k]}")

    edits.append({k: v for k, v in report.items() if k not in ("sunset", "sea_level_cells_on_bench_list", "bench_width_every_100m")}
                 | {"sunset_margin_deg_min": min(v["margin_to_280_deg"] for v in report["sunset"].values()),
                    "replaces": "coast_extension_A (100 m, 45 m beach), undone 2026-10-01 on her 'go with B, narrower beach'",
                    "beach_alternative_not_applied": "a 2 m crest at 1:15 over 30 m",
                    "note": "swale filled: landward of the old shore the bench runs level into the bluff; the beach narrows with the land in the tapers; "
                            "the coast_south_outline reference tube, which poked through the bench as the 'random line of water', is sunk 8 m under "
                            "the new ground between z 474 and 2300 (Christina, 2026-10-01, 'fill it')"})
    obj["kyt_edits"] = json.dumps(edits)
    notes = bpy.data.texts.get("README")
    if notes:
        notes.write(f"\nAUTHORED EDIT {EDIT_ID}, {EDIT_NAME} (tools/blender/world_terrain_edit_coast_extension.py; replaces coast_extension_A):\n"
                    f"  the south beach front, option A: {out['options'][OPTION]['depth_m']:g} m of land between the highway's seaward edge and the water, "
                    f"z {out['options'][OPTION]['from_z']:.0f}..{out['options'][OPTION]['to_z']:.0f}; bench {CE.BENCH_H:g} m Godot ({CE.BENCH_H - SEA_LEVEL:g} m over the sea) "
                    f"falling {CE.BENCH_FALL * 100:g} % to a crest 3 m over the sea, {CE.BEACH_W:g} m beach at 1:{1 / CE.BEACH_SLOPE:g}, shelf 1:{1 / CE.SHELF_SLOPE:g};\n"
                    f"  {int(sel.sum())} vertices moved (authored_edit = 2), {int(land.sum())} of them now AUTHORED land (authored_land, placeholder_bathymetry cleared, "
                    "sampled stays false, ground_y_sampled untouched); height_pre_edit keeps the heights before; --undo restores.\n"
                    "  The rail runs on the new shore edge (Christina, 2026-10-01). Edit 1 (blend_south_range) is untouched and undoable on its own.\n"
                    "  Swale filled (her 'fill it'): landward of the old shore the bench runs level into the bluff, no cell between them under the bench;\n"
                    "  the beach narrows with the land in the tapers; the coast_south_outline reference tube is sunk 8 m under the new ground here.\n")
    bpy.ops.wm.save_mainfile()
    print(f"{EDIT_NAME}: saved {bpy.data.filepath}")
    with open(os.path.join(work, "applied_coast_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    if render_dir:
        render(render_dir, obj, out)


def render(folder, obj, out):
    os.makedirs(folder, exist_ok=True)
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
        print(f"{EDIT_NAME}: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2400):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = CE.to_blender(cx, 5000.0, cz)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            scene.render.resolution_x, scene.render.resolution_y = px, int(px * ez / ex)
        else:
            scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
        shoot(name)

    def oblique(name, eye, aim, lens=35.0):
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector(CE.to_blender(*eye)), Vector(CE.to_blender(*aim))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
        shoot(name)

    top_down("applied_coast_top.png", -450.0, 950.0, 250.0, 2650.0)
    top_down("applied_coast_inlet_end.png", -400.0, 200.0, 250.0, 850.0, px=1800)
    top_down("applied_coast_south_end.png", 200.0, 900.0, 1950.0, 2650.0, px=1800)
    oblique("applied_coast_oblique_from_sea.png", (-700.0, 160.0, 1500.0), (250.0, 0.0, 1350.0), lens=35.0)
    # the bluff-foot contact, close: a low oblique along the bench looking north
    oblique("applied_coast_bluff_foot_closeup.png", (120.0, 40.0, 1250.0), (200.0, -2.0, 1050.0), lens=40.0)


if __name__ == "__main__":
    main()
