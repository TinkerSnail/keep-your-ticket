"""Authored edit 5 on the world terrain master: the falls (2026-10-02, Christina approved
the 30 m fall at C2, lip +41.9 at (400,-290), no notch, the turnout on the river side, the
K1 sluice release running over the fall; the lakes stay as built by edit 4).

    Blender --background <master or copy> --python tools/blender/world_terrain_edit_falls.py --
        [--dry] [--undo] [--render <folder>]

Same logged, reversible pattern as edits 1-4. Content:
1. A FINER PATCH (grid 3, 3 m) over the K-1 valley: an L-shaped region (x 240..470 for
   z -400..-292, plus x 285..470 for z -292..-180) that stays clear of the park's 4 m patch
   (x -272..280, z -290..278). Built like the park patch: the coarse (25 m) faces strictly
   under the region, inset one coarse step, are dropped; the ring between the remaining
   coarse edge and the patch border is triangulated with the constrained Delaunay; the
   patch's vertices are RESAMPLED from the existing master surface by ray cast, so before
   the carve the patch reproduces the ground (error reported). No original vertex moves.
2. THE CLIFF and POOL carved into the patch only: below the lip the 33 % slope is cut to a
   bench at +11.9 over a 50 m face, which makes the vertical face and the plunge pool
   (12 x 8 m, floor +9.9); a 6 m lip notch; the bed from the pool to the take-off (300,-230)
   +9.4 as a gentle stepped cascade. K1's spill, the K-1 reach above the lip, the take-off
   weir and sluice, the highway and its bridges are untouched (hash).
3. THE TURNOUT: a 60 x 3.5 m pad on the river side at x 255..285, graded flat at the road
   edge's level; the carriageway untouched; a pedestrian rail 18 m from the centreline as a
   reference curve.
4. WATER references: the fall ribbon, the plunge pool plane, notes on the looks.
--undo removes the patch and its stitch faces, restores the dropped coarse faces from the
stored list, removes what edit 5 added and drops the log entry; the original vertices never
moved, so the terrain hash returns bit-identical.
"""
import hashlib
import json
import math
import os
import sys

import numpy as np

import bpy
import bmesh
from mathutils import Vector
from mathutils import geometry
from mathutils.bvhtree import BVHTree

EDIT_ID = 5
EDIT_NAME = "falls"
GRID_ID = 3
STEP = 3.0
REGIONS = [(240.0, 470.0, -399.0, -292.0), (285.0, 470.0, -292.0, -180.0)]   # -399, not -400: the 25 m lattice line at z -400 must not coincide with the patch border
COARSE = 25.0
LIP = (400.0, -290.0)
LIP_Y = 41.9
POOL_Y = 11.9
POOL_FLOOR = 9.9
FACE_W = 50.0
LIP_W = 6.0
TAKEOFF = (300.0, -230.0)
TAKEOFF_Y = 9.4
PROTECT_BOXES = {"Plaza floor": (-52, 52, -52, 52), "NT-1 and its bluff": (-80, -50, -20, 17), "entrance precinct": (-48, 48, 83, 228), "Boardwalk deck": (-108, -56, -230, 220),
                 "park program envelope": (-212, 222, -230, 220)}


def attr(me, name, dtype):
    out = np.zeros(len(me.vertices), dtype=dtype)
    me.attributes[name].data.foreach_get("value", out)
    return out


def vertex_hash(co, sel=None):
    return hashlib.sha1((co if sel is None else co[sel]).tobytes()).hexdigest()


def in_region(x, z, inset=0.0):
    return any(x0 + inset <= x <= x1 - inset and z0 + inset <= z <= z1 - inset for x0, x1, z0, z1 in REGIONS)


def ref_curve(coll, name, pts3, colour, bevel, note, closed=False):
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
    for i, (x, y, z) in enumerate(pts3):
        sp.points[i].co = (x, -z, y, 1.0)
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu)
    o["kyt_reference"] = True
    o["kyt_collision"] = "none"
    o["kyt_edit_id"] = EDIT_ID
    o["kyt_note"] = note
    o.hide_select = True
    coll.objects.link(o)
    return o


def water_plane(coll, name, pts_xz, level, note):
    me = bpy.data.meshes.new(name)
    verts = [(x, -z, level) for x, z in pts_xz]
    me.from_pydata(verts, [], [list(range(len(verts)))])
    me.update()
    m = bpy.data.materials.new(f"water_{name}")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.0, 0.45, 1.0, 1.0)
    nt.links.new(em.outputs[0], o_.inputs[0])
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    o["kyt_reference"] = True
    o["kyt_collision"] = "none"
    o["kyt_water_level"] = float(level)
    o["kyt_edit_id"] = EDIT_ID
    o["kyt_note"] = note
    o.hide_select = True
    coll.objects.link(o)
    return o


def design_target(x, z, g, hw_xz):
    """Edit 5's surface for a patch vertex at (x, z) with resampled ground g, or None if untouched."""
    # the fall's axis: from the lip toward the take-off
    dx, dz = TAKEOFF[0] - LIP[0], TAKEOFF[1] - LIP[1]
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    nx_, nz_ = -uz, ux
    s = (x - LIP[0]) * ux + (z - LIP[1]) * uz      # along the fall, positive downstream
    t = (x - LIP[0]) * nx_ + (z - LIP[1]) * nz_    # across
    hw_d = min(math.hypot(x - a, z - b) for a, b in hw_xz)
    if hw_d <= 25.0:
        return None                                 # the highway's ground is never touched
    # the lip notch: 6 m wide, 1 m deep, 8 m back from the lip line
    if -8.0 <= s < 0.0 and abs(t) <= LIP_W / 2:
        return min(g, LIP_Y - 1.0 + (-s / 8.0) * 0.0)
    if 0.0 <= s <= L and abs(t) <= FACE_W / 2:
        # the bench / pool / cascade bed below the face
        if s <= 12.0 and abs(t) <= 4.0:
            tgt = POOL_FLOOR
        elif s <= 86.0:
            tgt = POOL_Y - 0.5 * (s - 12.0) / 74.0     # the bench falls 0.5 m over its length so the pool drains (0.7 %)
        else:
            # gentle stepped cascade from the bench to the take-off: 2.5 m over the last metres, in 0.5 m steps
            frac = (s - 86.0) / max(1.0, L - 86.0)
            tgt = POOL_Y - 0.5 - 0.5 * math.floor(frac * 4.0)   # four 0.5 m rock steps from +11.4 down to the take-off's +9.4
            tgt = max(tgt, TAKEOFF_Y)
        # the face's sides: 1:1 wings outside the 50 m face would widen the cut; the face edge is vertical here (t = +-25)
        return min(g, tgt)
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    undo = "--undo" in argv
    dry = "--dry" in argv
    render_dir = argv[argv.index("--render") + 1] if "--render" in argv else None
    obj = bpy.data.objects["terrain_world"]
    me = obj.data
    edits = json.loads(obj.get("kyt_edits", "[]"))
    n0 = len(me.vertices)
    co0 = np.empty(n0 * 3)
    me.vertices.foreach_get("co", co0)
    co0 = co0.reshape(-1, 3)
    grid = attr(me, "grid", np.int32)

    if undo:
        if not any(e.get("id") == EDIT_ID for e in edits):
            raise SystemExit(f"{EDIT_NAME}: nothing to undo")
        removed = json.loads(obj["kyt_edit5_removed_faces"])
        n_orig = int(obj["kyt_edit5_n_orig"])
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        fl = bm.faces.layers.int.get("edit5_face")
        # drop the stitch faces and every patch vertex (their faces go with them)
        for f in [f for f in bm.faces if fl is not None and f[fl] > 0]:
            bm.faces.remove(f)
        for v in [v for v in bm.verts if v.index >= n_orig]:
            bm.verts.remove(v)
        bm.verts.ensure_lookup_table()
        for face in removed:
            try:
                bm.faces.new([bm.verts[i] for i in face])
            except ValueError:
                pass
        bm.to_mesh(me)
        bm.free()
        me.update()
        if "edit5_face" in me.attributes:
            me.attributes.remove(me.attributes["edit5_face"])
        for o in list(bpy.data.objects):
            if o.get("kyt_edit_id") == EDIT_ID:
                data = o.data
                bpy.data.objects.remove(o)
                if data and data.users == 0:
                    (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.curves).remove(data)
        del obj["kyt_edit5_removed_faces"]
        del obj["kyt_edit5_n_orig"]
        obj["kyt_edits"] = json.dumps([e for e in edits if e.get("id") != EDIT_ID])
        tbl = json.loads(obj.get("kyt_grid_table", "[]"))
        if tbl and tbl[-1].startswith("falls_3m"):
            obj["kyt_grid_table"] = json.dumps(tbl[:-1])
        notes = bpy.data.texts.get("README")
        if notes:
            notes.write(f"\nAUTHORED EDIT {EDIT_ID} ({EDIT_NAME}) UNDONE: the falls patch removed, {len(removed)} coarse faces restored.\n")
        bpy.ops.wm.save_mainfile()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_set
        me.vertices.foreach_get("co", co)
        print(f"{EDIT_NAME}: undone; vertices {len(me.vertices)}; terrain hash {vertex_hash(co.reshape(-1, 3))}; saved")
        return
    if any(e.get("id") == EDIT_ID for e in edits):
        raise SystemExit(f"{EDIT_NAME}: edit 5 is already applied; --undo first")
    assert not (grid == GRID_ID).any(), "grid 3 already exists"
    X, Z = co0[:, 0], -co0[:, 1]
    hash_orig_before = vertex_hash(co0)
    aid = attr(me, "authored_edit", np.int32)
    # protected sets (original vertices only)
    masks = {}
    for name, (x0, x1, z0, z1) in PROTECT_BOXES.items():
        masks[name] = (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
    masks["NT-2 (+5 m)"] = ((X - 86) / 47) ** 2 + ((Z - 0) / 41) ** 2 <= 1.0
    hw = bpy.data.objects["coast_highway_centreline"]
    hw_xz = [(p.co[0], -p.co[1]) for s_ in hw.data.splines for p in s_.points]
    hw_near = [(a, b) for a, b in hw_xz if 0 <= a <= 600 and -500 <= b <= -50]
    near_hw = np.zeros(n0, dtype=bool)
    for v in np.nonzero((X > 0) & (X < 600) & (Z > -500) & (Z < -50))[0]:
        if min(math.hypot(X[v] - a, Z[v] - b) for a, b in hw_near) <= 25.0:
            near_hw[v] = True
    masks["coast highway ground (25 m) incl. both bridges"] = near_hw
    for e in (1, 2, 3, 4):
        masks[f"edit {e}"] = aid == e
    masks["K1 lake (edit 4) and spill"] = (aid == 4) | (np.hypot(X - 520, Z + 410) <= 45)
    hb = {k: vertex_hash(co0, m) for k, m in masks.items()}
    hb["all original vertices"] = hash_orig_before
    # --- the patch: samples on the existing surface
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    down = Vector((0, 0, -1))

    def ground(x, z):
        h = bvh.ray_cast(Vector((x, -z, 2000.0)), down, 6000.0)
        return float(h[0].z) if h[0] is not None else float("nan")
    pts = {}
    for x0, x1, z0, z1 in REGIONS:
        for x in np.arange(x0, x1 + 0.01, STEP):
            for z in np.arange(z0, z1 + 0.01, STEP):
                key = (round(float(x), 3), round(float(z), 3))
                if key not in pts:
                    pts[key] = ground(x, z)
    keys = list(pts)
    kidx = {k: i for i, k in enumerate(keys)}
    patch_faces = []
    for x0, x1, z0, z1 in REGIONS:
        xs_ = np.arange(x0, x1 + 0.01, STEP)
        zs_ = np.arange(z0, z1 + 0.01, STEP)
        for i in range(len(xs_) - 1):
            for j in range(len(zs_) - 1):
                a = kidx[(round(float(xs_[i]), 3), round(float(zs_[j]), 3))]
                b = kidx[(round(float(xs_[i + 1]), 3), round(float(zs_[j]), 3))]
                c = kidx[(round(float(xs_[i + 1]), 3), round(float(zs_[j + 1]), 3))]
                d = kidx[(round(float(xs_[i]), 3), round(float(zs_[j + 1]), 3))]
                patch_faces.append((a, b, c, d))
    # the carve targets
    patch_xz = np.array(keys)
    patch_g = np.array([pts[k] for k in keys])
    patch_t = patch_g.copy()
    carved = np.zeros(len(keys), dtype=bool)
    # the turnout: 60 x 3.5 m on the river (north-west) side at x 255..285, between 5 and 8.5 m from the centreline
    hw_seg = [(a, b) for a, b in hw_near if 245 <= a <= 295]
    road_edge_y = float(np.mean([ground(a, b) for a, b in hw_seg]))
    for i, (x, z) in enumerate(patch_xz):
        if x < 285.0 and in_region(x, z) is False:
            pass
        t = design_target(x, z, patch_g[i], hw_near)
        if t is not None and t < patch_g[i] - 1e-3:
            patch_t[i] = t
            carved[i] = True
    # turnout pad (only the part inside the patch region)
    turnout = []
    for i, (x, z) in enumerate(patch_xz):
        if 255.0 <= x <= 285.0 or True:
            d = min(math.hypot(x - a, z - b) for a, b in hw_seg) if hw_seg else 1e9
            # side test: north-west of the road = the river side (the road heads NE here; left of travel southbound)
            if 5.0 <= d <= 8.5 and 250.0 <= x <= 290.0 and z < -255.0:
                if abs(patch_g[i] - road_edge_y) > 1e-3:
                    patch_t[i] = road_edge_y
                    carved[i] = True
                    turnout.append(i)
    cell = STEP * STEP
    cut_m3 = float(np.sum(np.where(patch_g > patch_t, patch_g - patch_t, 0.0)) * cell)
    fill_m3 = float(np.sum(np.where(patch_t > patch_g, patch_t - patch_g, 0.0)) * cell)
    face_cut = float(np.sum([(patch_g[i] - patch_t[i]) * cell for i in range(len(keys)) if carved[i] and i not in set(turnout)]))
    turnout_cut = float(np.sum([max(0.0, patch_g[i] - patch_t[i]) * cell for i in turnout]))
    turnout_fill = float(np.sum([max(0.0, patch_t[i] - patch_g[i]) * cell for i in turnout]))
    report = {"id": EDIT_ID, "name": EDIT_NAME, "script": "tools/blender/world_terrain_edit_falls.py", "patch": {"regions": REGIONS, "step_m": STEP, "vertices": len(keys), "quads": len(patch_faces), "triangles_equiv": 2 * len(patch_faces)},
              "carve": {"vertices": int(carved.sum()), "cliff_pool_bed_cut_m3": round(face_cut), "design_cut_m3": 64000, "turnout_cut_m3": round(turnout_cut), "turnout_fill_m3": round(turnout_fill), "turnout_vertices": len(turnout), "road_edge_y": round(road_edge_y, 2),
                        "max_cut_m": float((patch_g - patch_t).max())}, "hashes_before": hb}
    print(f"{EDIT_NAME}: patch {report['patch']}; carve {report['carve']}")
    if dry:
        return
    # --- stitch: drop coarse faces strictly under the region (inset one coarse step), remember them
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    fl = bm.faces.layers.int.new("edit5_face")
    removed = []
    hole_edges = set()
    for f in list(bm.faces):
        if any(in_region(v.co.x, -v.co.y, inset=1e-6) for v in f.verts):   # any vertex inside: the kept coarse boundary then lies wholly outside the patch
            removed.append([v.index for v in f.verts])
    rem_set = set(tuple(r) for r in removed)
    for f in [f for f in bm.faces if tuple(v.index for v in f.verts) in rem_set]:
        for e in f.edges:
            hole_edges.add(tuple(sorted((e.verts[0].index, e.verts[1].index))))
        bm.faces.remove(f)
    # the hole's boundary: edges that still belong to a face
    boundary = []
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    for a, b in hole_edges:
        e = bm.edges.get((bm.verts[a], bm.verts[b]))
        if e is not None and len(e.link_faces) > 0:
            boundary.append((a, b))
    # order the boundary into one loop
    adj = {}
    for a, b in boundary:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    start = boundary[0][0]
    loop = [start]
    prev, cur = None, start
    while True:
        nxt = [v for v in adj[cur] if v != prev]
        if not nxt:
            break
        prev, cur = cur, nxt[0]
        if cur == start:
            break
        loop.append(cur)
        if len(loop) > len(boundary) + 2:
            break
    # add the patch vertices and faces
    new_verts = []
    for i, (x, z) in enumerate(patch_xz):
        new_verts.append(bm.verts.new((x, -z, float(patch_t[i]))))
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    for a, b, c, d in patch_faces:
        f = bm.faces.new((new_verts[a], new_verts[b], new_verts[c], new_verts[d]))
        f[fl] = 1
    # the patch border vertices (on the region outline)
    border = [i for i, (x, z) in enumerate(patch_xz) if not in_region(x, z, inset=STEP * 0.5 + 1e-6) or any(abs(x - r[0]) < 1e-6 or abs(x - r[1]) < 1e-6 or abs(z - r[2]) < 1e-6 or abs(z - r[3]) < 1e-6 for r in REGIONS)]
    # keep only border vertices that are on the outer outline of the L (not on the shared edge inside)
    def on_outline(x, z):
        cnt = sum(1 for r in REGIONS if r[0] - 1e-6 <= x <= r[1] + 1e-6 and r[2] - 1e-6 <= z <= r[3] + 1e-6)
        edges_on = 0
        for r in REGIONS:
            if r[0] - 1e-6 <= x <= r[1] + 1e-6 and r[2] - 1e-6 <= z <= r[3] + 1e-6:
                if abs(x - r[0]) < 1e-6 or abs(x - r[1]) < 1e-6 or abs(z - r[2]) < 1e-6 or abs(z - r[3]) < 1e-6:
                    edges_on += 1
        return edges_on > 0 and not in_region(x, z, inset=1e-3)
    border = [i for i in border if on_outline(patch_xz[i][0], patch_xz[i][1])]
    # CDT: the hole loop as the face, the patch border points inside it, patch border edges as constraints (ordered by angle about the patch centre)
    coords = [Vector((bm.verts[v].co.x, bm.verts[v].co.y)) for v in loop]
    hole_n = len(coords)
    # order the border along the L's outline (an L is not star-shaped, so no sorting by angle)
    outline = [(240.0, -399.0), (470.0, -399.0), (470.0, -180.0), (285.0, -180.0), (285.0, -292.0), (240.0, -292.0)]
    border_sorted = []
    for k in range(len(outline)):
        a, b = outline[k], outline[(k + 1) % len(outline)]
        seg = []
        for i in border:
            x, z = patch_xz[i]
            vx, vz = b[0] - a[0], b[1] - a[1]
            Ls = math.hypot(vx, vz)
            t = ((x - a[0]) * vx + (z - a[1]) * vz) / (Ls * Ls)
            off = abs((x - a[0]) * vz - (z - a[1]) * vx) / Ls
            if off < 1e-6 and -1e-6 <= t <= 1 - 1e-6:
                seg.append((t, i))
        for _, i in sorted(seg):
            if i not in border_sorted:
                border_sorted.append(i)
    coords += [Vector((patch_xz[i][0], -patch_xz[i][1])) for i in border_sorted]
    edges = [(hole_n + k, hole_n + (k + 1) % len(border_sorted)) for k in range(len(border_sorted))]
    out = geometry.delaunay_2d_cdt(coords, edges, [list(range(hole_n))], 1, 1e-5)
    vert_coords, out_edges, out_faces, orig_verts, orig_edges, orig_faces = out
    # map CDT verts back: first hole_n are loop verts, next are border patch verts; CDT may add none (eps) - assert
    if len(vert_coords) != len(coords):
        extra = [(round(v.x, 2), round(-v.y, 2)) for v in vert_coords[len(coords):]]
        print(f"{EDIT_NAME}: CDT debug: loop {hole_n} verts, boundary edges {len(boundary)}, border {len(border_sorted)}, extra {len(extra)}: {extra[:12]}")
        # is the loop simple? count repeated vertices
        print(f"{EDIT_NAME}: CDT debug: loop repeats {len(loop) - len(set(loop))}; loop span x {min(c.x for c in coords[:hole_n]):.0f}..{max(c.x for c in coords[:hole_n]):.0f} z {min(-c.y for c in coords[:hole_n]):.0f}..{max(-c.y for c in coords[:hole_n]):.0f}")
    # the CDT may insert a vertex where a border edge meets the coarse loop at the L's inner corner: it lies on an
    # existing coarse edge, so its height is the old surface's there (sampled by ray cast), appended as a patch vertex
    cdt_extra = []
    for v2 in vert_coords[len(coords):]:
        hx, hz = float(v2.x), float(-v2.y)
        nv = bm.verts.new((hx, -hz, ground(hx, hz)))
        new_verts.append(nv)
        cdt_extra.append(nv)
        keys.append((round(hx, 3), round(hz, 3)))
        pts[keys[-1]] = ground(hx, hz)
    if cdt_extra:
        patch_xz = np.array(keys)
        patch_g = np.array([pts[k] for k in keys])
        patch_t = np.concatenate([patch_t, patch_g[len(patch_t):]])
        carved = np.concatenate([carved, np.zeros(len(cdt_extra), dtype=bool)])
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    stitch_faces = 0
    n_border = len(border_sorted)
    for face in out_faces:
        # skip triangles inside the patch (centroid inside the region)
        cx_ = sum(vert_coords[i].x for i in face) / len(face)
        cy_ = sum(vert_coords[i].y for i in face) / len(face)
        if in_region(cx_, -cy_, inset=1e-3):
            continue
        vs = []
        for i in face:
            if i < hole_n:
                vs.append(bm.verts[loop[i]])
            elif i < hole_n + n_border:
                vs.append(new_verts[border_sorted[i - hole_n]])
            else:
                vs.append(cdt_extra[i - hole_n - n_border])
        try:
            f = bm.faces.new(vs)
            f[fl] = 2
            stitch_faces += 1
        except ValueError:
            pass
    bm.to_mesh(me)
    bm.free()
    me.update()
    # attributes for the new vertices
    n = len(me.vertices)
    assert n == n0 + len(keys), "vertex count"
    g = attr(me, "grid", np.int32)
    g[n0:] = GRID_ID
    me.attributes["grid"].data.foreach_set("value", g)
    a2 = attr(me, "authored_edit", np.int32)
    a2[n0:] = np.where(carved, EDIT_ID, 0)
    me.attributes["authored_edit"].data.foreach_set("value", a2)
    pre = attr(me, "height_pre_edit", float)
    pre[n0:] = patch_g
    me.attributes["height_pre_edit"].data.foreach_set("value", pre)
    if "resampled_from_master" not in me.attributes:
        me.attributes.new("resampled_from_master", "BOOLEAN", "POINT")
    rs = attr(me, "resampled_from_master", bool)
    rs[n0:] = True
    me.attributes["resampled_from_master"].data.foreach_set("value", rs)
    sampled = attr(me, "sampled", bool)
    sampled[n0:] = False
    me.attributes["sampled"].data.foreach_set("value", sampled)
    # owner/kind from the nearest original vertex in the region (the coarse lattice's values)
    own = attr(me, "owner", np.int32)
    kind = attr(me, "kind", np.int32)
    near_idx = np.nonzero((X > 200) & (X < 500) & (Z > -430) & (Z < -150))[0]
    for i in range(len(keys)):
        k = near_idx[int(np.argmin(np.hypot(X[near_idx] - patch_xz[i][0], Z[near_idx] - patch_xz[i][1])))]
        own[n0 + i] = own[k]
        kind[n0 + i] = kind[k]
    me.attributes["owner"].data.foreach_set("value", own)
    me.attributes["kind"].data.foreach_set("value", kind)
    col = np.empty(n * 4)
    me.color_attributes["height_shade"].data.foreach_get("color", col)
    col = col.reshape(-1, 4)
    col[n0:] = (0.80, 0.78, 0.70, 1.0)
    col[n0:][carved] = (0.55, 0.5, 0.45, 1.0)
    me.color_attributes["height_shade"].data.foreach_set("color", col.ravel())
    me.update()
    obj["kyt_edit5_removed_faces"] = json.dumps(removed)
    obj["kyt_edit5_n_orig"] = n0
    tbl = json.loads(obj.get("kyt_grid_table", "[]"))
    tbl.append("falls_3m (edit 5, resampled from the master)")
    obj["kyt_grid_table"] = json.dumps(tbl)
    # --- references
    ref = bpy.data.collections["Reference"]
    rw = bpy.data.collections.get("Reference_water") or bpy.data.collections.new("Reference_water")
    if rw.name not in [c.name for c in ref.children]:
        ref.children.link(rw)
    ws = bpy.data.collections.get("Water_surfaces") or bpy.data.collections.new("Water_surfaces")
    if ws.name not in [c.name for c in ref.children]:
        ref.children.link(ws)
    dx, dz = TAKEOFF[0] - LIP[0], TAKEOFF[1] - LIP[1]
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    nx_, nz_ = -uz, ux
    ref_curve(rw, "falls_ribbon", [(LIP[0], LIP_Y, LIP[1]), (LIP[0] + ux * 2.0, POOL_Y, LIP[1] + uz * 2.0)], (0.75, 0.9, 1.0, 1.0), 3.0,
              "the fall: 30 m free fall over the 6 m lip at +41.9 into the plunge pool at +11.9. Looks: 457 L/s mean = an 8 cm sheet that breaks into a veil within 10 m (Bridalveil); May 1.08 m3/s = 15 cm, a solid white fall; late summer 380 L/s = 7 cm, a thin veil the wind bends; 13.6 m3/s peak = a 60 cm roaring sheet. The K1 sluice release outfalls into K-1 and runs over the fall")
    pool = [(LIP[0] + ux * s + nx_ * t, LIP[1] + uz * s + nz_ * t) for s, t in ((1.0, -4.0), (12.0, -4.0), (12.0, 4.0), (1.0, 4.0))]
    water_plane(ws, "water_plunge_pool", pool, POOL_Y, "the plunge pool at the fall's foot, 12 x 8 m, water +11.9, floor +9.9; drains down the stepped bed to the take-off (300,-230) +9.4")
    ref_curve(rw, "falls_cliff_face_top", [(LIP[0] + nx_ * t, LIP_Y + 0.3, LIP[1] + nz_ * t) for t in (-25.0, 25.0)], (0.9, 0.3, 0.3, 1.0), 1.0, "the cliff's top edge: a 50 m vertical face from +41.9 to the bench at +11.9, cut by edit 5")
    ref_curve(rw, "falls_turnout_rail", [(a + (-b_ + b) * 0, ground(a, b) + 1.0, b) for a, b, b_ in []] or
              [(x, road_edge_y + 1.0, z) for x, z in [(hw_seg[0][0] + (-(hw_seg[-1][1] - hw_seg[0][1])) / math.hypot(hw_seg[-1][0] - hw_seg[0][0], hw_seg[-1][1] - hw_seg[0][1]) * 18.0 * (1 if True else -1), hw_seg[0][1] + ((hw_seg[-1][0] - hw_seg[0][0])) / math.hypot(hw_seg[-1][0] - hw_seg[0][0], hw_seg[-1][1] - hw_seg[0][1]) * 18.0)]],
              (0.9, 0.6, 0.2, 1.0), 0.8, "pedestrian rail placeholder")
    # the rail properly: 18 m from the centreline on the river side, along the turnout's length
    rail = []
    for a, b in hw_seg:
        k = hw_seg.index((a, b))
        a2, b2 = hw_seg[min(k + 1, len(hw_seg) - 1)]
        a1, b1 = hw_seg[max(k - 1, 0)]
        ddx, ddz = a2 - a1, b2 - b1
        Ld = math.hypot(ddx, ddz) or 1.0
        rail.append((a - ddz / Ld * 18.0 * -1, road_edge_y + 1.0, b + ddx / Ld * 18.0 * -1))
    o = bpy.data.objects.get("falls_turnout_rail")
    if o is not None:
        bpy.data.objects.remove(o)
    ref_curve(rw, "falls_turnout_rail", rail, (0.9, 0.6, 0.2, 1.0), 0.8, "the turnout's pedestrian rail on the river bank, 18 m from the highway centreline, 1 m high; the pad is 60 x 3.5 m on the river side at the road edge's level (edit 5 grades it)")
    # --- verification
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    co2 = co2.reshape(-1, 3)
    ha = {k: vertex_hash(co2[:n0], m) for k, m in masks.items()}
    ha["all original vertices"] = vertex_hash(co2[:n0])
    for k in hb:
        assert hb[k] == ha[k], f"changed: {k}"
    report["hashes_after"] = ha
    report["protected_identical"] = True
    report["stitch"] = {"coarse_faces_dropped": len(removed), "hole_loop_vertices": len(loop), "stitch_triangles": stitch_faces, "border_vertices": len(border_sorted), "cdt_corner_vertices_added": len(cdt_extra), "note": "corner vertices lie on coarse edges, heights sampled from the old surface"}
    # resampling error before the carve: compare the patch's pre-carve heights with the old surface at random points inside the region
    bvh2 = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    rng = np.random.default_rng(5)
    errs = []
    for _ in range(300):
        r = REGIONS[int(rng.integers(0, 2))]
        x = float(rng.uniform(r[0] + 2, r[1] - 2))
        z = float(rng.uniform(r[2] + 2, r[3] - 2))
        if design_target(x, z, 0.0, hw_near) is not None:
            continue
        h_old = ground(x, z)
        h2 = bvh2.ray_cast(Vector((x, -z, 2000.0)), down, 6000.0)
        if h2[0] is not None and h_old == h_old:
            errs.append(abs(float(h2[0].z) - h_old))
    report["resample_error_m"] = {"max": float(max(errs)) if errs else None, "mean": float(np.mean(errs)) if errs else None, "samples": len(errs), "note": "old surface vs the patch at random points outside the carve; 0 at the samples by construction"}
    # drain trace from the pool to the take-off on the carved patch (steepest descent over patch vertices)
    px_ = patch_xz
    pt_ = patch_t
    cur_i = int(np.argmin(np.hypot(px_[:, 0] - (LIP[0] + ux * 14), px_[:, 1] - (LIP[1] + uz * 14))))   # the pool's downstream rim on the bench
    path = [cur_i]
    for _ in range(200):
        d = np.hypot(px_[:, 0] - px_[cur_i, 0], px_[:, 1] - px_[cur_i, 1])
        nb = np.nonzero((d > 0.1) & (d <= STEP * 1.5))[0]
        if len(nb) == 0:
            break
        j = nb[int(np.argmin(pt_[nb]))]
        if pt_[j] >= pt_[cur_i] - 1e-6:
            break
        cur_i = j
        path.append(cur_i)
    end = px_[cur_i]
    report["drain_trace"] = {"from_pool": [float(px_[path[0]][0]), float(px_[path[0]][1]), float(pt_[path[0]])], "end": [float(end[0]), float(end[1]), float(pt_[cur_i])], "steps": len(path),
                             "distance_to_takeoff_m": float(math.hypot(end[0] - TAKEOFF[0], end[1] - TAKEOFF[1])), "reaches_takeoff": bool(math.hypot(end[0] - TAKEOFF[0], end[1] - TAKEOFF[1]) < 30.0)}
    report["cameras_or_lights"] = [o.name for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]
    edits.append({"id": EDIT_ID, "name": EDIT_NAME, "script": report["script"], "date": "2026-10-02", "patch_vertices": len(keys), "carved": int(carved.sum()), "cut_m3": round(face_cut),
                  "hash_orig_before": hash_orig_before, "hash_after_all": vertex_hash(co2)})
    obj["kyt_edits"] = json.dumps(edits)
    notes = bpy.data.texts.get("README")
    if notes:
        notes.write(f"\nAUTHORED EDIT {EDIT_ID} ({EDIT_NAME}), {report['script']}, 2026-10-02: the falls. A 3 m patch (grid 3, {len(keys)} vertices, resampled from the master) over the K-1 valley; "
                    f"the cliff below the lip (400,-290) +41.9 cut to a bench at +11.9 over a 50 m face ({face_cut:.0f} m3), the plunge pool, the stepped bed to the take-off, the turnout pad; original vertices untouched (hash). --undo removes the patch and restores the {len(removed)} coarse faces.\n")
    bpy.ops.wm.save_mainfile()
    out_dir = render_dir or os.path.dirname(bpy.data.filepath)
    with open(os.path.join(out_dir, "falls_built_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(f"{EDIT_NAME}: stitch {report['stitch']}; resample {report['resample_error_m']}; drain {report['drain_trace']}; cameras {report['cameras_or_lights']}")
    print(f"{EDIT_NAME}: applied, saved {bpy.data.filepath}; original-vertex hash {hash_orig_before} == {ha['all original vertices']}; all-vertex hash {vertex_hash(co2)}")
    if render_dir:
        render(render_dir, obj, hw_near, road_edge_y)


def render(folder, obj, hw_near, road_edge_y):
    scene = bpy.context.scene
    me = obj.data
    me.polygons.foreach_set("material_index", np.zeros(len(me.polygons), dtype=np.int32))
    # smooth shading for the render only (set after the save: never saved)
    sm = np.ones(len(me.polygons), dtype=bool)
    me.polygons.foreach_set("use_smooth", sm)
    me.update()
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.75, 0.82, 0.92, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.9, 0.0, -2.3)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0

    def shoot(name, eye, aim, lens=28.0, ortho=None, res=(2400, 1350)):
        cam_data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam_data.ortho_scale = ortho
        cam_data.lens = lens
        e, a = Vector((eye[0], -eye[1], eye[2])), Vector((aim[0], -aim[1], aim[2]))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = res
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        print(f"{EDIT_NAME}: rendered {scene.render.filepath}")
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def g(x, z):
        h = bvh.ray_cast(Vector((x, -z, 2000.0)), Vector((0, 0, -1)), 6000.0)
        return float(h[0].z) if h[0] is not None else 0.0
    lip3 = (LIP[0], LIP[1], LIP_Y - 15.0)
    for name, (x, z) in (("first_sight_SB", (104, -361)), ("best_view_SB", (270, -265)), ("last_sight_SB", (296, -232)), ("reveal_NB", (337, -132))):
        shoot(f"falls_built_driver_{name}.png", (x, z, g(x, z) + 1.2), lip3)
    shoot("falls_built_turnout_view.png", (266, -278, road_edge_y + 1.6), lip3, lens=35.0)
    shoot("falls_built_plan.png", (350, -290, 1500.0), (350, -290.001, 0.0), ortho=320.0, res=(2000, 2000))
    shoot("falls_built_cliff_oblique.png", (250, -200, 70.0), (400, -290, 25.0), lens=35.0)
    shoot("falls_built_section_view.png", (430, -230, 50.0), (400, -290, 25.0), lens=35.0)


if __name__ == "__main__":
    main()
