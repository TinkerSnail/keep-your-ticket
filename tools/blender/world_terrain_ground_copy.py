"""Copy the generator's ground into the world terrain master, exactly
(2026-10-05, Stage 0 of `documentation/terrain-master-into-game-plan-2026-10-05.md`;
Christina chose "Exact copy": the master's base is the ground the game stands
on today, vertex for vertex, so mounting it changes nothing).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/world_terrain_master.blend \
        --python tools/blender/world_terrain_ground_copy.py -- --dump <folder> [--dry]

`<folder>` is what `tools/ground_copy_dump.gd` wrote: one `<body>.json` and
`<body>.bin` per generator ground body (the mainland reserve, both coasts, T2,
T3, T6 and both east shoulders). For each body this builds one mesh object of
the same name in a `Ground` collection:
- positions are the dump's float32 world positions, axes mapped
  blender = (x, -z, y)_godot, so the generator's sub-millimetre seam
  displacement is kept;
- the dump is a triangle soup; corners at exactly the same position are
  welded into one vertex, so the surface is one connected sheet she can
  sculpt; nothing is moved or rounded;
- normals, colours and UVs stay per corner, exactly: custom split normals,
  a corner colour attribute `Col` and a UV map `UVMap` (v flipped to
  Blender's convention, so the glTF export writes the game's v back);
- each triangle is written (a, c, b): Godot's front faces wind clockwise and
  Blender's anticlockwise, and the axis map is a rotation, not a mirror;
- a material per body, `<body>_ground`, carrying the colour attribute where
  the body has one, so the export writes it; the game's look comes from the
  mounted wrapper's materials, not from these.
The existing grid mesh `terrain_world` and its `Terrain` collection are kept
as the design reference for edits 1-7 (redone on this base in Stage 3): the
collection is hidden and the scene's `kyt_export_collections` is set to
`["Ground"]`, which `tools/export_world_source.py` honours, so only the copy
ever reaches the game.

Verified before saving: every corner's position equals the dump's bit for bit,
colours and UVs exactly, and normals to 5e-3: Blender stores custom split
normals in a compressed form, so about 1e-3 is as close as it can hold them,
far under anything visible. No degenerate triangle after welding. Triangles
that share all three vertices with another are kept, because the game has
them today (two on 2026-10-05: one in the reserve, one in the north coast);
they are reported with their positions. `--dry` builds and verifies without saving. Saved with
save_version 0, so no `.blend1`. The run is logged in the README text and in
the scene's `kyt_ground_copy`.
"""
import json
import os
import sys

import bpy
import numpy as np

BODIES = [
    "terrain_world_mainland_reserve",
    "terrain_world_coast_north",
    "terrain_world_coast_south",
    "terrain_T2_lowland",
    "terrain_T3_headland",
    "terrain_T6_outer_highland",
    "east_shoulder_n",
    "east_shoulder_s",
]
COLLECTION = "Ground"


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    dump = a[a.index("--dump") + 1] if "--dump" in a else None
    if not dump:
        raise SystemExit("world_terrain_ground_copy: --dump <folder> is required")
    return os.path.abspath(dump), "--dry" in a


def read_body(folder, body):
    meta = json.load(open(os.path.join(folder, body + ".json")))
    raw = open(os.path.join(folder, body + ".bin"), "rb").read()
    out = []
    for s in meta["surfaces"]:
        o = s["byte_offset"]
        n, ni = s["vertices"], s["indices"]
        v = np.frombuffer(raw, np.float32, n * 3, o).reshape(-1, 3)
        o += n * 12
        nr = None
        if s["has_normals"]:
            nr = np.frombuffer(raw, np.float32, n * 3, o).reshape(-1, 3)
            o += n * 12
        c = None
        if s["has_colors"]:
            c = np.frombuffer(raw, np.float32, n * 4, o).reshape(-1, 4)
            o += n * 16
        uv = None
        if s["has_uv"]:
            uv = np.frombuffer(raw, np.float32, n * 2, o).reshape(-1, 2)
            o += n * 8
        idx = np.frombuffer(raw, np.int32, ni, o)
        out.append({"v": v, "n": nr, "c": c, "uv": uv, "idx": idx, "material": s["material"]})
    return meta, out


def to_blender(a):
    """Godot (x, y, z) rows to Blender (x, -z, y), float32 kept."""
    b = np.empty_like(a)
    b[:, 0] = a[:, 0]
    b[:, 1] = -a[:, 2]
    b[:, 2] = a[:, 1]
    return b


def build(body, meta, surfaces, coll):
    if len(surfaces) != 1:
        raise SystemExit(f"{body}: {len(surfaces)} surfaces; this copy expects one")
    s = surfaces[0]
    tri = s["idx"].reshape(-1, 3)[:, [0, 2, 1]]          # (a, c, b): clockwise to anticlockwise
    corners = tri.reshape(-1)
    pos = to_blender(s["v"][corners])                     # per corner, Blender axes
    uniq, inverse = np.unique(pos, axis=0, return_inverse=True)
    inverse = inverse.reshape(-1)
    faces = inverse.reshape(-1, 3)
    degenerate = int(np.sum((faces[:, 0] == faces[:, 1]) | (faces[:, 1] == faces[:, 2]) | (faces[:, 0] == faces[:, 2])))
    key = np.sort(faces, axis=1)
    _, first, counts = np.unique(key, axis=0, return_index=True, return_counts=True)
    dup = int(np.sum(counts > 1))
    dup_at = [[round(float(c), 2) for c in (uniq[faces[i]].mean(axis=0) * np.array([1, -1, 1]))[[0, 2, 1]]]
              for i in first[counts > 1]]
    me = bpy.data.meshes.new(body)
    me.vertices.add(len(uniq))
    me.vertices.foreach_set("co", uniq.astype(np.float32).ravel())
    me.loops.add(len(corners))
    me.loops.foreach_set("vertex_index", inverse.astype(np.int32))
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", (np.arange(len(faces), dtype=np.int32) * 3))
    me.polygons.foreach_set("loop_total", np.full(len(faces), 3, dtype=np.int32))
    me.update(calc_edges=True)
    if s["n"] is not None:
        nrm = to_blender(s["n"][corners])
        me.normals_split_custom_set([tuple(r) for r in nrm.tolist()])
    if s["c"] is not None:
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        ca.data.foreach_set("color", s["c"][corners].astype(np.float32).ravel())
        me.color_attributes.active_color = ca
        me.color_attributes.render_color_index = me.color_attributes.active_color_index
    if s["uv"] is not None:
        uvl = me.uv_layers.new(name="UVMap")
        uv = s["uv"][corners].copy()
        uv[:, 1] = 1.0 - uv[:, 1]
        uvl.data.foreach_set("uv", uv.astype(np.float32).ravel())
    me.update()
    obj = bpy.data.objects.new(body, me)
    coll.objects.link(obj)
    mat = bpy.data.materials.new(f"{body}_ground")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    rec = meta.get("material_override") or {}
    alb = rec.get("albedo") or [0.4, 0.45, 0.32, 1.0]
    bsdf.inputs["Base Color"].default_value = tuple(alb)
    if s["c"] is not None:
        node = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        node.layer_name = "Col"
        mat.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    me.materials.append(mat)
    obj["kyt_ground_copy"] = json.dumps({"from": meta["source"], "body": body, "mesh_node": meta["mesh_node"],
                                         "date": "2026-10-05", "transform_godot": meta["transform"]})
    return obj, {"corners": int(len(corners)), "vertices": int(len(uniq)), "triangles": int(len(faces)),
                 "degenerate": degenerate, "duplicate": int(dup), "duplicate_at_godot": dup_at}, (s, tri)


def verify(obj, s, tri):
    me = obj.data
    nl = len(me.loops)
    vi = np.zeros(nl, dtype=np.int32)
    me.loops.foreach_get("vertex_index", vi)
    co = np.zeros(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    corners = tri.reshape(-1)
    want = to_blender(s["v"][corners])
    pos_ok = bool(np.array_equal(co[vi], want))
    res = {"positions_bit_equal": pos_ok}
    if s["n"] is not None:
        got = np.array([tuple(l.normal) for l in me.loops], dtype=np.float64) if bpy.app.version < (4, 1, 0) else \
            np.array([tuple(cn.vector) for cn in me.corner_normals], dtype=np.float64)
        wantn = to_blender(s["n"][corners]).astype(np.float64)
        wantn /= np.linalg.norm(wantn, axis=1, keepdims=True) + 1e-30
        res["normal_max_err"] = float(np.abs(got - wantn).max())
    if s["c"] is not None:
        ca = me.color_attributes["Col"]
        c = np.zeros(nl * 4, dtype=np.float32)
        ca.data.foreach_get("color", c)
        res["colours_equal"] = bool(np.array_equal(c.reshape(-1, 4), s["c"][corners]))
    if s["uv"] is not None:
        u = np.zeros(nl * 2, dtype=np.float32)
        me.uv_layers["UVMap"].data.foreach_get("uv", u)
        u = u.reshape(-1, 2)
        wu = s["uv"][corners].copy()
        wu[:, 1] = 1.0 - wu[:, 1]
        res["uv_max_err"] = float(np.abs(u - wu).max())
    return res


def main():
    folder, dry = args()
    scene = bpy.context.scene
    if COLLECTION in bpy.data.collections:
        raise SystemExit(f"world_terrain_ground_copy: a `{COLLECTION}` collection already exists; remove it to copy again")
    coll = bpy.data.collections.new(COLLECTION)
    scene.collection.children.link(coll)
    report = {"dump": folder, "bodies": {}}
    for body in BODIES:
        meta, surfaces = read_body(folder, body)
        obj, stats, (s, tri) = build(body, meta, surfaces, coll)
        stats.update(verify(obj, s, tri))
        report["bodies"][body] = stats
        print(f"world_terrain_ground_copy: {body} {stats}")
    bad = [b for b, st in report["bodies"].items()
           if not st["positions_bit_equal"] or st["degenerate"]
           or st.get("normal_max_err", 0.0) > 5e-3 or st.get("colours_equal") is False or st.get("uv_max_err", 0.0) > 1e-6]
    report["ok"] = not bad
    # The grid master stays as the design reference for edits 1-7, hidden and never exported.
    terrain = bpy.data.collections.get("Terrain")
    if terrain is not None:
        terrain.hide_viewport = True
        terrain.hide_render = True
    scene["kyt_export_collections"] = [COLLECTION]
    scene["kyt_ground_copy"] = json.dumps({"date": "2026-10-05", "tool": "tools/blender/world_terrain_ground_copy.py",
                                           "dump_tool": "tools/ground_copy_dump.gd",
                                           "bodies": {b: {k: v for k, v in st.items()} for b, st in report["bodies"].items()}})
    txt = bpy.data.texts.get("README")
    if txt is not None:
        txt.write("\n\nGROUND (2026-10-05, Stage 0 of documentation/terrain-master-into-game-plan-2026-10-05.md; "
                  "Christina: \"Exact copy\"): the `Ground` collection is the game's ground today, copied vertex for vertex "
                  "from the generator's eight ground bodies by tools/ground_copy_dump.gd and "
                  "tools/blender/world_terrain_ground_copy.py; corners welded where they share a position, normals, "
                  "colours and UVs kept per corner. It is what tools/export_world_source.py exports "
                  "(scene property kyt_export_collections). The grid mesh `terrain_world` in the hidden `Terrain` "
                  "collection is now the design reference for edits 1-7, which are redone on the Ground in Stage 3; "
                  "it is never exported.\n")
    print("world_terrain_ground_copy: REPORT " + json.dumps(report))
    if bad:
        raise SystemExit(f"world_terrain_ground_copy: verification failed for {bad}; nothing saved")
    if dry:
        print("world_terrain_ground_copy: dry run, nothing saved")
        return
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    print("world_terrain_ground_copy: saved")


main()
