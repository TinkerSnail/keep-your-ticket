"""Stage 3 of documentation/terrain-master-into-game-plan-2026-10-05.md: an authored edit
made on the grid master `terrain_world` carried onto the world terrain master's `Ground`,
the ground the game stands on (2026-10-05, Christina: "start stage 3").

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_ground_edit.py -- --edit 4 [--dry] [--undo] [--render <folder>]

Edits 1-7 were made on the 25 m grid, which matches the game only at its sample points
(a median 0.35 m off around the park, up to 20 m at cliffs), so an edit is not copied as
a height change. It is carried as the surface it designed: wherever edit N moved the grid,
Ground takes the edited grid surface, faded in over the first `BLEND` of the change so the
edit's edge meets untouched ground smoothly. Nothing the edit did not reach moves.

Ground's lattice does not line up with the grid's (the reserve is 24 m out where the hill
lakes are), and its long triangles would climb back out of a cut up to a cell early: on
the first try K1 lost a 19 m band of shore, 3.8 ha. So the faces the edit reaches, and two
rings round them, are first refined: every original vertex and edge is kept, and points are
added on a `LATTICE` lattice and at the edit's own grid vertices, triangulated inside the
original faces (constrained Delaunay), each new corner taking its colour and UV from the
face it lies in. Only then is the surface cut or raised. Every vertex outside the region
keeps its position exactly, and the region's edge does not move.

Edit 4, the hill lakes: cut only. Each lake's water is then built on Ground itself, not
taken from the grid's plane: every Ground triangle connected to the lake's floor that lies
below the brim, clipped at the brim, walled off where the lake spills (the spill and the
creek below it, from edit 4's own `LAKES`) and where another source's ground stands over
Ground. The planes go in the `Lakes` collection, which the export now carries with
`Ground`; edit 4's design planes are hidden, since the game planes stand in their place.

Logged and reversible: the faces each edit replaced are kept, hidden and unexported, as
`<object>__before_edit<N>` in the `Ground_history` collection; the new faces carry the
face attribute `authored_edit`; `--undo` puts the old faces back exactly, removes what the
edit added and unhides what it hid. The log is the scene's `kyt_ground_edits` and the
README text. Prints the proof: every vertex outside the edit's faces unchanged, the cut's
depth, each lake's area against the grid design. `--dry` reports without saving.
"""
import ast
import hashlib
import json
import math
import os
import sys

import numpy as np

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

HERE = os.path.dirname(os.path.abspath(__file__))
GRID = "terrain_world"
GROUND = "Ground"
HISTORY = "Ground_history"
LAKES_COLLECTION = "Lakes"
# The refined lattice inside an edit's region.
LATTICE = 8.0
# A lattice point nearer than this to a kept vertex, an edge point or a grid vertex is
# dropped, so the triangulation makes no slivers (they shade as spikes).
CROWD = 0.35 * LATTICE
# The bay's water (tools/gen_props.gd, mats["water"]), so lake and sea read as one water.
LAKE_COLOUR = (0.34, 0.44, 0.52, 1.0)
DESIGN_PLANES = {"K1": "water_K1_enlarged", "L0": "water_L0_enlarged"}
# Small still water an edit designed as a plane on the grid, built on Ground inside that
# plane's outline grown by `POOL_GROW`: {edit: {game name: design plane}}.
POOLS = {5: {"plunge_pool": "water_plunge_pool"}}
POOL_GROW = 2.0
# Render views per edit beyond the lakes: {name: ((x, z) centre, width across, eye level)}.
VIEWS = {5: {"falls": ((355.0, -290.0), 320.0, 41.9)}}
# Where a lake runs out over its spill: triangles past the spill (further from the lake's
# centre than the spill, within this of it) and within this of the creek below are dry.
SPILL_WALL = 60.0
CREEK_WALL = 35.0
# Where another source's ground stands over Ground (the range's hills east of L0 stand up
# to 130 m over the copied reserve), the grid, sampled from the game's top ground, is the
# rim: water stands only where the edited grid is within this of the brim or below it, which
# runs the water a little under that ground rather than leaving a dry strip below the brim
# where the 25 m grid is unsure of its edge. Water still crosses only Ground below the brim.
TOP_RIM = 5.0
MIN_CHANGE = 0.01
# The edits this script knows how to carry, each in its own Stage 3 batch.
CARRIED = (4, 5)
# Over the first this-many metres of an edit's change, Ground fades from its own surface to
# the edit's, so the edge of a cut meets the untouched ground without a step.
BLEND = 2.0
# How far an edit may move Ground against its own direction to meet the design.
AGAINST = 1.0


def argv():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"edit": None, "dry": "--dry" in a, "undo": "--undo" in a, "render": None}
    if "--edit" in a:
        out["edit"] = int(a[a.index("--edit") + 1])
    if "--render" in a:
        out["render"] = a[a.index("--render") + 1]
    return out


def edit_constant(script, name):
    """A literal assigned at the top of a grid edit script, read without running it."""
    tree = ast.parse(open(os.path.join(HERE, script)).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit("%s has no %s" % (script, name))


def ground_objects():
    return [o for o in bpy.data.collections[GROUND].all_objects if o.type == 'MESH']


def coords(ob):
    co = np.zeros(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def grid_surfaces(edit):
    """BVH trees of the grid as edit `edit` left it and as it stood before it, the plan
    box the edit's vertices cover, and those vertices' plan positions."""
    ob = bpy.data.objects[GRID]
    me = ob.data
    M = ob.matrix_world
    co = coords(ob)
    ed = np.zeros(len(me.vertices), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", ed)
    pre = np.zeros(len(me.vertices))
    me.attributes["height_pre_edit"].data.foreach_get("value", pre)
    sel = ed == edit
    if not sel.any():
        raise SystemExit("the grid has no vertex of edit %d" % edit)
    now = [M @ Vector(v) for v in co]
    before = [Vector((v.x, v.y, pre[i] if sel[i] else v.z)) for i, v in enumerate(now)]
    polys = [tuple(p.vertices) for p in me.polygons]
    idx = np.nonzero(sel)[0]
    xs = np.array([now[i].x for i in idx])
    ys = np.array([now[i].y for i in idx])
    box = (xs.min() - 60.0, xs.max() + 60.0, ys.min() - 60.0, ys.max() + 60.0)
    points = [Vector((now[i].x, now[i].y)) for i in idx]
    return BVHTree.FromPolygons(now, polys), BVHTree.FromPolygons(before, polys), box, points


def height(tree, x, y):
    hit = tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
    return None if hit[0] is None else hit[0].z


def designed(now_t, pre_t, x, y, z):
    """Where edit N puts ground that stands at z at (x, y): unchanged where the edit left
    the grid alone, and the edited grid surface where it moved the grid by `BLEND` or more,
    faded between. The design wins outright inside the edit even where Ground stood a few
    tenths below it: taking the lower of the two at every point (the first try) flipped
    between them along every bank, by the grid's own 0.3 m, and serrated it."""
    t = height(now_t, x, y)
    p = height(pre_t, x, y)
    if t is None or p is None:
        return z
    d = t - p
    if abs(d) <= MIN_CHANGE:
        return z
    w = min(1.0, abs(d) / BLEND)
    # A cut never lifts Ground by more than the grid's own error, nor a raise lowers it:
    # where another source's ground was the grid's top (the range's hills over the reserve),
    # Ground lies far below the design and stays there.
    change = t - z
    if d < 0.0:
        change = min(change, AGAINST)
    else:
        change = max(change, -AGAINST)
    return z + w * change


def corner_key(co, centre):
    return (round(co.x, 3), round(co.y, 3), round(centre.x, 3), round(centre.y, 3))


def history_collection():
    c = bpy.data.collections.get(HISTORY)
    if c is None:
        c = bpy.data.collections.new(HISTORY)
        bpy.context.scene.collection.children.link(c)
        c.hide_viewport = True
        c.hide_render = True
    return c


def carry(ob, edit, now_t, pre_t, box, grid_points, dry):
    """Refine and cut one Ground object. Returns its report, or None if untouched."""
    me = ob.data
    if ob.matrix_world != ob.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin; Ground objects hold world positions" % ob.name)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    def in_box(co):
        return box[0] <= co.x <= box[1] and box[2] <= co.y <= box[3]

    def reached(co):
        return in_box(co) and abs(designed(now_t, pre_t, co.x, co.y, co.z) - co.z) > MIN_CHANGE

    touched = set()
    for f in bm.faces:
        c = f.calc_center_median()
        if not in_box(c):
            continue
        # A face is reached if the edit moves any of its corners, its centre, or the middle of
        # any edge, so a cut that falls between Ground's vertices is not missed.
        probes = [c] + [v.co for v in f.verts] + [(e.verts[0].co + e.verts[1].co) * 0.5 for e in f.edges]
        if any(reached(q) for q in probes):
            touched.add(f.index)
    if not touched:
        bm.free()
        return None
    region = set(touched)
    for _ in range(2):
        ring = set()
        for fi in region:
            for v in bm.faces[fi].verts:
                for f in v.link_faces:
                    ring.add(f.index)
        region |= ring
    faces = [bm.faces[i] for i in sorted(region)]
    if any(len(f.verts) != 3 for f in faces):
        raise SystemExit("%s: a face in the region is not a triangle" % ob.name)
    rverts = sorted({v.index for f in faces for v in f.verts})
    edge_verts = set()
    seam = set()
    for vi in rverts:
        v = bm.verts[vi]
        if any(e.is_boundary for e in v.link_edges):
            seam.add(vi)
        elif not all(f.index in region for f in v.link_faces):
            edge_verts.add(vi)
    moving_edge = [vi for vi in edge_verts if reached(bm.verts[vi].co)]
    if moving_edge:
        raise SystemExit("%s: the edit reaches %d vertices on the region's edge (e.g. %s); refusing" % (
            ob.name, len(moving_edge), tuple(round(c, 1) for c in bm.verts[moving_edge[0]].co)))
    # Ground's open edges are stitched to what the generator still builds (the road
    # corridor, the tunnel lids, the anchors): a vertex on one never moves, and what the
    # edit asked of it is reported.
    held = [designed(now_t, pre_t, bm.verts[vi].co.x, bm.verts[vi].co.y, bm.verts[vi].co.z) - bm.verts[vi].co.z
            for vi in seam if reached(bm.verts[vi].co)]
    pinned = {bm.verts[vi] for vi in seam}
    report = {"faces_before": len(faces), "region_vertices": len(rverts), "seam_held": len(held),
              "seam_held_most": max((abs(h) for h in held), default=0.0)}
    if dry:
        bm.free()
        return report
    col = bm.loops.layers.float_color.get("Col")
    uv = bm.loops.layers.uv.get("UVMap")

    # Keep the region's faces as they are, for the undo.
    hist = bmesh.new()
    vmap = {vi: hist.verts.new(bm.verts[vi].co) for vi in rverts}
    hcol = hist.loops.layers.float_color.new("Col")
    huv = hist.loops.layers.uv.new("UVMap")
    for f in faces:
        nf = hist.faces.new([vmap[v.index] for v in f.verts])
        nf.material_index = f.material_index
        nf.smooth = f.smooth
        for la, lb in zip(f.loops, nf.loops):
            lb[hcol] = la[col]
            lb[huv].uv = la[uv].uv
    hme = bpy.data.meshes.new("%s__before_edit%d" % (ob.name, edit))
    hist.to_mesh(hme)
    hist.free()
    for m in me.materials:
        hme.materials.append(m)
    hob = bpy.data.objects.new(hme.name, hme)
    hob["kyt_note"] = "the faces of %s that Ground edit %d replaced, for its --undo; never exported" % (ob.name, edit)
    history_collection().objects.link(hob)

    # The normal of every corner outside the region, to set again after the rebuild.
    kept_normals = {}
    corner_normals = me.corner_normals
    for poly in me.polygons:
        if poly.index in region:
            continue
        c = poly.center
        for li in poly.loop_indices:
            kept_normals[corner_key(me.vertices[me.loops[li].vertex_index].co, c)] = Vector(corner_normals[li].vector)

    # Refine: the region's own vertices and faces as constraints, plus lattice points and
    # the edit's grid vertices inside it.
    local = {vi: k for k, vi in enumerate(rverts)}
    tri_idx = [[local[v.index] for v in f.verts] for f in faces]
    pts2 = [Vector((bm.verts[vi].co.x, bm.verts[vi].co.y)) for vi in rverts]
    flat = BVHTree.FromPolygons([Vector((p.x, p.y, 0.0)) for p in pts2], tri_idx)

    def inside(p):
        return flat.ray_cast(Vector((p.x, p.y, 1.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    xs = [p.x for p in pts2]
    ys = [p.y for p in pts2]
    extra = [p for p in grid_points if inside(p)]
    # Points along every original edge inside the region too: an edge kept whole would span
    # the cut as a straight bridge between its ends. The region's outer edges stay whole,
    # since the faces outside still use them.
    for f in faces:
        for e in f.edges:
            if e.is_boundary or not all(lf.index in region for lf in e.link_faces):
                continue
            a, b = e.verts[0].co, e.verts[1].co
            n = int(math.floor((a - b).xy.length / LATTICE))
            for k in range(1, n + 1):
                t = k / (n + 1)
                extra.append(Vector((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)))
    taken = {}
    for q in pts2 + extra:
        taken.setdefault((int(q.x // CROWD), int(q.y // CROWD)), []).append(q)

    def crowded(q):
        cx, cy = int(q.x // CROWD), int(q.y // CROWD)
        return any((q - o).length < CROWD for i in (-1, 0, 1) for j in (-1, 0, 1) for o in taken.get((cx + i, cy + j), ()))

    x = math.floor(min(xs) / LATTICE) * LATTICE
    while x <= max(xs):
        y = math.floor(min(ys) / LATTICE) * LATTICE
        while y <= max(ys):
            q = Vector((x, y))
            if inside(q) and not crowded(q):
                extra.append(q)
            y += LATTICE
        x += LATTICE
    out_v, _, out_f, orig_v, _, orig_f = delaunay_2d_cdt(pts2 + extra, [], tri_idx, 1, 1e-4, True)
    surf = BVHTree.FromPolygons([bm.verts[vi].co.copy() for vi in rverts], tri_idx)
    loops = [[(lp[col][:], lp[uv].uv.copy()) for lp in f.loops] for f in faces]
    corners = [[lp.vert.co.copy() for lp in f.loops] for f in faces]
    materials = [(f.material_index, f.smooth) for f in faces]

    def parent_sample(fi, p):
        a, b, c = corners[fi]
        v0 = Vector((b.x - a.x, b.y - a.y))
        v1 = Vector((c.x - a.x, c.y - a.y))
        v2 = Vector((p.x - a.x, p.y - a.y))
        den = v0.x * v1.y - v1.x * v0.y
        u = (v2.x * v1.y - v1.x * v2.y) / den
        w = (v0.x * v2.y - v2.x * v0.y) / den
        bary = (1.0 - u - w, u, w)
        colour = [sum(bary[k] * loops[fi][k][0][j] for k in range(3)) for j in range(4)]
        tex = loops[fi][0][1] * bary[0] + loops[fi][1][1] * bary[1] + loops[fi][2][1] * bary[2]
        return colour, tex

    # Rebuild: the region's faces go, its vertices stay (inner ones may move), new vertices
    # and faces come in.
    bmesh.ops.delete(bm, geom=faces, context='FACES_ONLY')
    bm.verts.ensure_lookup_table()
    made = []
    for k, p in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(rverts)]
        if src:
            made.append(bm.verts[rverts[src[0]]])
            continue
        z = height(surf, p.x, p.y)
        if z is None:
            raise SystemExit("%s: a refined point at (%.1f, %.1f) lies off the original surface" % (ob.name, p.x, p.y))
        made.append(bm.verts.new((p.x, p.y, z)))
    fa = bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
    new_faces = []
    for k, tri in enumerate(out_f):
        vs = [made[i] for i in tri]
        if len(set(vs)) < 3:
            continue
        fi = orig_f[k][0] if orig_f[k] else None
        if fi is None:
            # The triangulator names no parent for some faces along split constraint edges;
            # the original face under the centre is the parent.
            cx = sum(out_v[i].x for i in tri) / 3.0
            cy = sum(out_v[i].y for i in tri) / 3.0
            hit = flat.ray_cast(Vector((cx, cy, 1.0)), Vector((0.0, 0.0, -1.0)))
            if hit[0] is None:
                raise SystemExit("%s: a refined face at (%.1f, %.1f) lies outside the region" % (ob.name, cx, cy))
            fi = hit[2]
        nf = bm.faces.new(vs)
        for lp in nf.loops:
            colour, tex = parent_sample(fi, lp.vert.co)
            lp[col] = colour
            lp[uv].uv = tex
        nf.material_index, nf.smooth = materials[fi]
        nf[fa] = edit
        new_faces.append(nf)
    # Cut (or raise) every vertex of the new faces to the edit's surface, except on the seams.
    depth = [0.0, 0.0]
    moved = 0
    for v in {v for f in new_faces for v in f.verts}:
        if v in pinned or any(e.is_boundary for e in v.link_edges):
            continue
        z = designed(now_t, pre_t, v.co.x, v.co.y, v.co.z)
        if abs(z - v.co.z) > MIN_CHANGE:
            depth[0] = min(depth[0], z - v.co.z)
            depth[1] = max(depth[1], z - v.co.z)
            v.co.z = z
            moved += 1
    bm.to_mesh(me)
    bm.free()
    me.update()

    # Normals: every corner outside the region as it was, the new ones smooth.
    vn = [Vector(v.vector) for v in me.vertex_normals]
    normals = []
    for poly in me.polygons:
        c = poly.center
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            normals.append(kept_normals.get(corner_key(me.vertices[vi].co, c), vn[vi]))
    me.normals_split_custom_set(normals)
    report.update({"faces_after": len(new_faces), "moved": moved, "deepest": depth[0], "highest": depth[1]})
    return report


def ground_triangles():
    tris = []
    for ob in ground_objects():
        M = ob.matrix_world
        me = ob.data
        me.calc_loop_triangles()
        co = [M @ v.co for v in me.vertices]
        for lt in me.loop_triangles:
            a, b, c = (co[k] for k in lt.vertices)
            tris.append((a, b, c))
    return tris


def clip_below(tri, level):
    """The part of a triangle at or below `level`, as a polygon on that level."""
    out = []
    pts = list(tri)
    for k in range(3):
        p, q = pts[k], pts[(k + 1) % 3]
        if p.z <= level:
            out.append(Vector((p.x, p.y, level)))
        if (p.z - level) * (q.z - level) < 0.0:
            s = (level - p.z) / (q.z - p.z)
            out.append(Vector((p.x + (q.x - p.x) * s, p.y + (q.y - p.y) * s, level)))
    return out


def lake_water(key, lk, tris, top):
    """Ground triangles of one lake below its brim, flooded from its floor, and only
    where the game's top ground (the edited grid, `top`) is low enough for water too."""
    brim = float(lk["brim"])
    cx, cz = lk["centre"]
    sx, sz = lk["spill"]
    reach = float(lk["R"]) + 120.0
    centre = Vector((cx, -cz))
    spill = Vector((sx, -sz))
    creek = [Vector((x, -z)) for x, z in lk["creek"]]
    spill_r = (spill - centre).length

    def dry(c2):
        if (c2 - spill).length < SPILL_WALL and (c2 - centre).length > spill_r - 5.0:
            return True
        if any((c2 - q).length < CREEK_WALL for q in creek):
            return True
        t = height(top, c2.x, c2.y)
        return t is None or t > brim + TOP_RIM

    near = []
    for t in tris:
        c2 = Vector(((t[0].x + t[1].x + t[2].x) / 3.0, (t[0].y + t[1].y + t[2].y) / 3.0))
        if (c2 - centre).length < reach and min(v.z for v in t) < brim and not dry(c2):
            near.append(t)
    key_of = lambda v: (round(v.x, 2), round(v.y, 2))
    edges = {}
    for n, t in enumerate(near):
        for k in range(3):
            e = tuple(sorted((key_of(t[k]), key_of(t[(k + 1) % 3]))))
            edges.setdefault(e, []).append(n)
    # Start in the triangle nearest the lake's centre: anything else below the brim within
    # reach (the lowland west of K1) lies beyond the rim and is never reached.
    start = min(range(len(near)), key=lambda n: (Vector(((near[n][0].x + near[n][1].x + near[n][2].x) / 3.0,
                                                          (near[n][0].y + near[n][1].y + near[n][2].y) / 3.0)) - centre).length)
    wet = {start}
    todo = [start]
    while todo:
        n = todo.pop()
        t = near[n]
        for k in range(3):
            e = tuple(sorted((key_of(t[k]), key_of(t[(k + 1) % 3]))))
            # Water crosses an edge only where some of the edge is below the brim.
            if min(t[k].z, t[(k + 1) % 3].z) >= brim:
                continue
            for m in edges[e]:
                if m not in wet:
                    wet.add(m)
                    todo.append(m)
    polys = [clip_below(near[n], brim) for n in sorted(wet)]
    polys = [p for p in polys if len(p) >= 3]
    area = sum(0.5 * abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[(i + 1) % len(p)].x * p[i].y for i in range(len(p)))) for p in polys)
    xs = [v.x for p in polys for v in p]
    zs = [-v.y for p in polys for v in p]
    return polys, area, (min(xs), max(xs), min(zs), max(zs))


def pool_water(design, tris):
    """Ground triangles below a design plane's level, inside its outline grown by
    `POOL_GROW`, clipped at the level."""
    me = design.data
    M = design.matrix_world
    verts = [M @ v.co for v in me.vertices]
    level = sum(v.z for v in verts) / len(verts)
    flat = BVHTree.FromPolygons([Vector((v.x, v.y, 0.0)) for v in verts], [tuple(p.vertices) for p in me.polygons])
    polys = []
    for t in tris:
        if min(v.z for v in t) >= level:
            continue
        c = Vector(((t[0].x + t[1].x + t[2].x) / 3.0, (t[0].y + t[1].y + t[2].y) / 3.0, 0.0))
        hit = flat.find_nearest(c, POOL_GROW)
        if hit[0] is None:
            continue
        p = clip_below(t, level)
        if len(p) >= 3:
            polys.append(p)
    area = sum(0.5 * abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[(i + 1) % len(p)].x * p[i].y for i in range(len(p)))) for p in polys)
    return polys, area, level


def build_plane(name, polys, note):
    verts = []
    faces = []
    index = {}
    for p in polys:
        f = []
        for v in p:
            k = (round(v.x, 4), round(v.y, 4))
            if k not in index:
                index[k] = len(verts)
                verts.append((v.x, v.y, v.z))
            f.append(index[k])
        if len(set(f)) >= 3:
            faces.append(f)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    for poly in me.polygons:
        if poly.normal.z < 0:
            poly.flip()
    # The water is flat, so only its outline needs vertices: the clipped triangles of the
    # refined ground (tens of thousands) are merged into a few faces.
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.001, verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    mat = bpy.data.materials.get("lake_water") or bpy.data.materials.new("lake_water")
    mat.diffuse_color = LAKE_COLOUR
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob["kyt_collision"] = "none"
    ob["kyt_note"] = note
    return ob


def lakes_collection():
    c = bpy.data.collections.get(LAKES_COLLECTION)
    if c is None:
        c = bpy.data.collections.new(LAKES_COLLECTION)
        bpy.context.scene.collection.children.link(c)
    return c


def edit_face_vertices(ob, edit):
    me = ob.data
    if "authored_edit" not in me.attributes:
        return set()
    fa = np.zeros(len(me.polygons), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", fa)
    used = set()
    for p in me.polygons:
        if fa[p.index] == edit:
            used.update(p.vertices)
    return used


def log(entry=None, remove=None):
    scene = bpy.context.scene
    edits = json.loads(scene.get("kyt_ground_edits", "[]"))
    if remove is not None:
        edits = [e for e in edits if e.get("id") != remove]
    if entry is not None:
        edits = [e for e in edits if e.get("id") != entry["id"]] + [entry]
    scene["kyt_ground_edits"] = json.dumps(edits)
    return edits


def readme(line):
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n" + line + "\n")


def undo(edit):
    edits = json.loads(bpy.context.scene.get("kyt_ground_edits", "[]"))
    entry = next((e for e in edits if e.get("id") == edit), None)
    if entry is None:
        raise SystemExit("Ground carries no edit %d" % edit)
    if edits[-1].get("id") != edit:
        raise SystemExit("edit %d was carried after edit %d; undo it first" % (edits[-1]["id"], edit))
    for name in entry["objects"]:
        ob = bpy.data.objects[name]
        hob = bpy.data.objects["%s__before_edit%d" % (name, edit)]
        me = ob.data
        fa = np.zeros(len(me.polygons), dtype=np.int32)
        me.attributes["authored_edit"].data.foreach_get("value", fa)
        kept_normals = {}
        corner_normals = me.corner_normals
        for poly in me.polygons:
            if fa[poly.index] == edit:
                continue
            for li in poly.loop_indices:
                kept_normals[corner_key(me.vertices[me.loops[li].vertex_index].co, poly.center)] = Vector(corner_normals[li].vector)
        bm = bmesh.new()
        bm.from_mesh(me)
        fl = bm.faces.layers.int["authored_edit"]
        gone = [f for f in bm.faces if f[fl] == edit]
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        bm.verts.ensure_lookup_table()
        at = {(round(v.co.x, 4), round(v.co.y, 4)): v for v in bm.verts}
        col = bm.loops.layers.float_color["Col"]
        uv = bm.loops.layers.uv["UVMap"]
        hme = hob.data
        hcol = hme.color_attributes["Col"]
        huv = hme.uv_layers["UVMap"]
        made = []
        for v in hme.vertices:
            k = (round(v.co.x, 4), round(v.co.y, 4))
            if k in at:
                at[k].co = v.co
                made.append(at[k])
            else:
                nv = bm.verts.new(v.co)
                at[k] = nv
                made.append(nv)
        for poly in hme.polygons:
            nf = bm.faces.new([made[i] for i in poly.vertices])
            nf.material_index = poly.material_index
            nf.smooth = poly.use_smooth
            for lp, li in zip(nf.loops, poly.loop_indices):
                lp[col] = hcol.data[li].color
                lp[uv].uv = huv.data[li].uv
        bm.to_mesh(me)
        bm.free()
        me.update()
        if "authored_edit" in me.attributes and not any(
                v for v in (lambda a: (me.attributes["authored_edit"].data.foreach_get("value", a), a)[1])(np.zeros(len(me.polygons), dtype=np.int32))):
            me.attributes.remove(me.attributes["authored_edit"])
        vn = [Vector(v.vector) for v in me.vertex_normals]
        normals = []
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                normals.append(kept_normals.get(corner_key(me.vertices[vi].co, poly.center), vn[vi]))
        me.normals_split_custom_set(normals)
        bpy.data.objects.remove(hob)
        bpy.data.meshes.remove(hme)
    for name in entry.get("added", []):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            me = ob.data
            bpy.data.objects.remove(ob)
            if me.users == 0:
                bpy.data.meshes.remove(me)
    for name in entry.get("hid", []):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            ob.hide_set(False)
            ob.hide_render = False
    for cname in (LAKES_COLLECTION, HISTORY):
        c = bpy.data.collections.get(cname)
        if c is not None and not c.all_objects:
            bpy.data.collections.remove(c)
    if entry.get("export_before") is not None:
        bpy.context.scene["kyt_export_collections"] = entry["export_before"]
    log(remove=edit)
    readme("Ground edit %d undone (%s): the replaced faces restored; %s removed." % (edit, entry["name"], ", ".join(entry.get("added", [])) or "nothing"))
    print("world_terrain_ground_edit: edit %d undone" % edit)


def render(folder, edit, views):
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'OBJECT'
    for ob in ground_objects():
        ob.color = (0.62, 0.66, 0.55, 1.0)
    for ob in bpy.data.collections[LAKES_COLLECTION].objects:
        ob.color = LAKE_COLOUR
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    for c in bpy.data.collections:
        if c.name not in (GROUND, LAKES_COLLECTION):
            for ob in c.objects:
                ob.hide_render = True
    for key, (centre, across, level) in views.items():
        cx, cz = centre
        half = 0.5 * (across - 300.0) if across > 600.0 else 0.5 * across
        cam = bpy.data.cameras.new("tmp_cam")
        cam.type = 'ORTHO'
        cam.ortho_scale = across
        cam.clip_start = 1.0
        cam.clip_end = 20000.0
        ob = bpy.data.objects.new("tmp_cam", cam)
        scene.collection.objects.link(ob)
        ob.location = (cx, -cz, 3000.0)
        scene.camera = ob
        scene.render.filepath = os.path.join(folder, "ground_edit%d_%s_top.png" % (edit, key))
        bpy.ops.render.render(write_still=True)
        ob.location = (cx - 0.9 * half, -cz - 0.9 * half, level + 260.0 * half / 300.0)
        cam.type = 'PERSP'
        cam.lens = 30.0
        ob.rotation_euler = (math.radians(62.0), 0.0, math.radians(-45.0))
        scene.render.filepath = os.path.join(folder, "ground_edit%d_%s_oblique.png" % (edit, key))
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(ob)
        bpy.data.cameras.remove(cam)


def main():
    a = argv()
    if a["edit"] not in CARRIED:
        raise SystemExit("edits %s are carried so far; the rest come in their own batches" % sorted(CARRIED))
    edit = a["edit"]
    if a["undo"]:
        undo(edit)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_mainfile()
        return
    if any(e.get("id") == edit for e in json.loads(bpy.context.scene.get("kyt_ground_edits", "[]"))):
        raise SystemExit("Ground already carries edit %d; --undo first" % edit)
    now_t, pre_t, box, grid_points = grid_surfaces(edit)
    before = {ob.name: coords(ob).copy() for ob in ground_objects()}
    reports = {}
    for ob in ground_objects():
        r = carry(ob, edit, now_t, pre_t, box, grid_points, a["dry"])
        if r is not None:
            reports[ob.name] = r
    for name, r in reports.items():
        print("  %-34s %s" % (name, ", ".join("%s %s" % (k, ("%.2f" % v) if isinstance(v, float) else v) for k, v in r.items())))
    if a["dry"]:
        print("world_terrain_ground_edit: --dry; nothing saved")
        return
    # Every vertex outside the edit's faces exactly where it was.
    for ob in ground_objects():
        if ob.name not in reports:
            if not np.array_equal(before[ob.name], coords(ob)):
                raise SystemExit("%s moved, and the edit never reached it" % ob.name)
            continue
        now = coords(ob)
        used = edit_face_vertices(ob, edit)
        old = {tuple(v) for v in before[ob.name]}
        strays = sum(1 for i in range(len(now)) if i not in used and tuple(now[i]) not in old)
        if strays:
            raise SystemExit("%s: %d vertices outside the edit's faces moved" % (ob.name, strays))
    design = next(e for e in json.loads(bpy.data.objects[GRID].get("kyt_edits", "[]")) if e.get("id") == edit)
    tris = ground_triangles()
    coll = lakes_collection()
    added = []
    hid = []
    areas = {}
    lakes = edit_constant("world_terrain_edit_hill_lakes.py", "LAKES") if edit == 4 else {}
    for key, lk in lakes.items():
        polys, area, lbox = lake_water(key, lk, tris, now_t)
        areas[key] = round(area / 10000.0, 2)
        name = "lake_%s" % key
        note = ("%s at +%.1f, built on Ground's own triangles below the brim (Stage 3, edit 4 carried; "
                "%.1f ha against %.1f ha on the grid design); spill and creek walled off" % (key, lk["brim"], area / 10000.0, design["lakes"][key]["area_ha"]))
        ob = build_plane(name, polys, note)
        coll.objects.link(ob)
        added.append(name)
        print("  %s: %.2f ha of water at +%.1f, x %.0f..%.0f z %.0f..%.0f (grid design %.1f ha)" % (
            name, area / 10000.0, lk["brim"], lbox[0], lbox[1], lbox[2], lbox[3], design["lakes"][key]["area_ha"]))
        plane = bpy.data.objects.get(DESIGN_PLANES[key])
        if plane is not None and not plane.hide_get():
            plane.hide_set(True)
            plane.hide_render = True
            hid.append(plane.name)
    for name, plane_name in POOLS.get(edit, {}).items():
        plane = bpy.data.objects[plane_name]
        polys, area, level = pool_water(plane, tris)
        if not polys:
            raise SystemExit("%s: no Ground below +%.2f inside %s" % (name, level, plane_name))
        areas[name] = round(area, 1)
        ob = build_plane(name, polys, "%s at +%.1f, built on Ground's own triangles below that level inside %s's outline "
                                     "grown by %.0f m (Stage 3, edit %d carried)" % (name, level, plane_name, POOL_GROW, edit))
        coll.objects.link(ob)
        added.append(name)
        print("  %s: %.0f m2 of water at +%.2f (design plane %s)" % (name, area, level, plane_name))
        if not plane.hide_get():
            plane.hide_set(True)
            plane.hide_render = True
            hid.append(plane.name)
    scene = bpy.context.scene
    export_before = list(scene.get("kyt_export_collections", []))
    scene["kyt_export_collections"] = [GROUND, LAKES_COLLECTION]
    entry = {"id": edit, "name": design["name"], "script": "tools/blender/world_terrain_ground_edit.py",
             "date": "2026-10-05", "objects": sorted(reports), "report": reports, "lakes_ha": areas,
             "added": added, "hid": hid, "export_before": export_before}
    log(entry)
    held = sum(r.get("seam_held", 0) for r in reports.values())
    readme("Ground edit %d (%s), Stage 3, 2026-10-05: grid edit %d carried onto Ground (%s): its region refined to "
           "a %.0f m lattice and given the grid's designed surface; %d vertices on the seams with the generator's "
           "ground held where they were; water %s built on Ground in the Lakes collection, exported with Ground; "
           "design planes %s hidden; the replaced faces kept in %s. Undo: "
           "tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
               edit, design["name"], edit, ", ".join(reports), LATTICE, held,
               ", ".join("%s %s" % (k, ("%.2f ha" % v) if k in lakes else ("%.0f m2" % v)) for k, v in areas.items()) or "none",
               ", ".join(hid) or "none", HISTORY, edit))
    print("world_terrain_ground_edit: edit %d carried; every vertex outside its faces unchanged" % edit)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    # After the save, so the render's hidden layers and cameras never reach the master.
    if a["render"]:
        views = {key: (lk["centre"], 2.0 * float(lk["R"]) + 300.0, float(lk["brim"])) for key, lk in lakes.items()}
        views.update(VIEWS.get(edit, {}))
        render(a["render"], edit, views)


main()
