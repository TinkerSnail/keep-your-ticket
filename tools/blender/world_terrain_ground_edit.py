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

Edit 2, the south beach front (2026-10-06), designed land where the game has open sea, beyond
Ground's edge, so it is built rather than cut: a new Ground object, `NEW_LAND`, the edited grid
from the coasts' shore wall out to the grid's seabed, running on below the waterline. See
`new_land`.

The coast shelf (2026-10-06, `-- --edit shelf`, id `SHELF_ID`) is no grid edit: every coast's
shore wall is cut just under the waterline and a shelf runs out from it under the water, so the
coast goes on below the sea instead of ending in a wall. See `coast_shelf`.

Logged and reversible: the faces each edit replaced are kept, hidden and unexported, as
`<object>__before_edit<N>` in the `Ground_history` collection; the new faces carry the
face attribute `authored_edit`; `--undo` puts the old faces back exactly, removes what the
edit added and unhides what it hid. The log is the scene's `kyt_ground_edits` and the
README text. Prints the proof: every vertex outside the edit's faces unchanged, the cut's
depth, each lake's area against the grid design. `--dry` reports without saving.
"""
import ast
import datetime
import hashlib
import json
import math
import os
import re
import sys

import numpy as np

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()
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
VIEWS = {100: {"shelf_north": ((-300.0, -1300.0), 1400.0, -8.0), "shelf_east": ((3300.0, 600.0), 1400.0, -8.0),
              "shelf_spur": ((500.0, 2450.0), 900.0, -8.0)},
         2: {"beach_north": ((130.0, 900.0), 900.0, -4.0), "beach_south": ((500.0, 1850.0), 900.0, -4.0)},
         5: {"falls": ((355.0, -290.0), 320.0, 41.9)}}
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
# Over the first this-many metres of an edit's change, Ground fades from its own surface to
# the edit's, so the edge of a cut meets the untouched ground without a step.
BLEND = 2.0
# How far an edit may move Ground against its own direction to meet the design.
AGAINST = 1.0
# Edits that build land where the game has open sea, beyond Ground's own edge: {edit: the new
# Ground object}. Edit 2, the south beach front (option B), lies wholly beyond the shore.
NEW_LAND = {2: "terrain_south_beach_front"}
# The generator's coasts end at the shore in a vertical wall down to this depth, its skirt.
SKIRT_Z = -13.5
# The sea and the beach front's bench are the edit's own (`world_terrain_coast_extension.py`'s
# `SEA_LEVEL` and `BENCH_H`), read where they are used.
# The bench meets the shore's top edge over a bank this wide (a smoothstep, so it leaves the
# shore level and lands on the bench without a crease).
RAMP = 10.0
# New land's colours: the shore's own planting on the bench and its bank, the generator's beach
# sand (`gen_props.gd`, the 02B beaches) from the bench's crest down past the waterline, and its
# sea-cliff colour (`REBUILD_SEA_CLIFF_COLOUR`) once the shelf is well under water.
SAND = (0.78, 0.72, 0.58)
SEABED = (0.47, 0.44, 0.39)
# The beach's crest: the bench is -4 at the bluff falling 1 % seaward, up to 86 m, to a crest
# 3 m over the sea; this takes the lowest. Sand begins here, and wherever the design stands
# above it against the shore wall, the bank climbs to the wall's top.
CREST = -4.6
SAND_FROM = (CREST + 0.4, CREST)
# An edge this close under the wall's top is the top: no sliver of wall is left above it.
SNAP = 0.05
SEABED_FROM = (-8.5, -10.5)
# A face flatter than this is a wall, not ground one could stand on (`world_terrain_source.gd`'s
# `MIN_UP`).
MIN_UP_FACE = 0.05
# Each end of new land meets the shore wall at least this far under the sea.
END_UNDER = 0.5
JOIN = 0.01
# The coast shelf (2026-10-06), a ground job that is no grid edit, so it takes an id clear of
# them: `--edit shelf`.
SHELF_ID = 100
SHELF = "terrain_coast_shelf"
# The wall keeps this much below the waterline, so the water meets the wall and not the crease
# where the shelf begins.
SHELF_UNDER = 0.5
# How far out the shelf runs, and its depth there (Godot y): 8.5 m of water, the generator's
# skirt going down to -13.5 and edit 2's shelf to about -14.
SHELF_W = 60.0
SHELF_DEPTH = -16.0
# Rows out from the wall, metres; a row point nearer than min(CROWD + SHELF_SPREAD * distance,
# 0.45 * the gap from the row before) to one already placed is dropped.
SHELF_ROWS = (3.0, 8.0, 15.0, 25.0, 40.0, 60.0)
SHELF_SPREAD = 0.3
SHELF_LONGEST = 60.0
# The park's own west shore is left alone: its rebuild footprint grown by this, the margin
# `footprint_test` gives it.
SHELF_CLEAR = 45.0
# A shore whose top colour is within this of the generator's beach sand has a sandy shelf.
SANDY = 0.15
# The edits this script knows how to carry, each in its own Stage 3 batch.
CARRIED = (2, 4, 5, SHELF_ID)


def argv():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"edit": None, "dry": "--dry" in a, "undo": "--undo" in a, "render": None}
    if "--edit" in a:
        v = a[a.index("--edit") + 1]
        out["edit"] = SHELF_ID if v == "shelf" else int(v)
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
    # Height too: a shore wall's top and foot share their plan position, and without it their
    # normals were swapped between them (fixed 2026-10-06; edits 4 and 5 had done it).
    return (round(co.x, 3), round(co.y, 3), round(co.z, 3), round(centre.x, 3), round(centre.y, 3), round(centre.z, 3))


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


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def region_faces(edit):
    """The grid's faces edit `edit` moved any corner of, flattened to a plan BVH, and their
    corners' plan positions."""
    ob = bpy.data.objects[GRID]
    me = ob.data
    M = ob.matrix_world
    ed = np.zeros(len(me.vertices), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", ed)
    world = [M @ Vector(v) for v in coords(ob)]
    polys = [tuple(p.vertices) for p in me.polygons if any(ed[i] == edit for i in p.vertices)]
    corners = sorted({i for p in polys for i in p})
    flat = BVHTree.FromPolygons([Vector((v.x, v.y, 0.0)) for v in world], polys)
    return flat, [Vector((world[i].x, world[i].y)) for i in corners]


def column_top(b):
    """The vertex straight above `b` on its wall: the generator's skirt drops each shore vertex
    to `SKIRT_Z` in one vertical edge."""
    for e in b.link_edges:
        o = e.other_vert(b)
        if (o.co.xy - b.co.xy).length < 1e-3 and o.co.z > b.co.z + 0.01:
            return o
    return None


def plan_constant(name):
    """A number written in `scripts/park_plan.gd`, read without Godot."""
    text = open(os.path.join(HERE, os.pardir, os.pardir, "scripts", "park_plan.gd")).read()
    m = re.search(r"^const %s\s*:?=\s*(-?[0-9.]+)\s*$" % name, text, re.M)
    if m is None:
        raise SystemExit("scripts/park_plan.gd has no number %s" % name)
    return float(m.group(1))


def ground_from_above(box=None, margin=100.0):
    """Whether Ground stands at (x, y): every upward face of Ground, within `box` grown by
    `margin` when one is given."""
    up_v = []
    up_f = []
    for ob in ground_objects():
        me = ob.data
        for poly in me.polygons:
            if poly.normal.z < MIN_UP_FACE:
                continue
            c = poly.center
            if box is not None and not (box[0] - margin <= c.x <= box[1] + margin and box[2] - margin <= c.y <= box[3] + margin):
                continue
            base = len(up_v)
            up_v.extend(Vector(me.vertices[i].co) for i in poly.vertices)
            up_f.append(tuple(range(base, base + len(poly.vertices))))
    land = BVHTree.FromPolygons(up_v, up_f)

    def over_ground(x, y):
        return land.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    return over_ground


def uv_projection(box=None):
    """The reserve's texture coordinates as a plan projection, (u, v) = [x, y, 1] @ coef, and
    how far its own corners stray from it."""
    reserve = bpy.data.objects["terrain_world_mainland_reserve"].data
    ruv = reserve.uv_layers["UVMap"]
    fit = []
    for poly in reserve.polygons:
        if poly.normal.z < 0.3:
            continue
        c = poly.center
        if box is not None and not (box[0] <= c.x <= box[1] and box[2] <= c.y <= box[3]):
            continue
        for li in poly.loop_indices:
            co = reserve.vertices[reserve.loops[li].vertex_index].co
            fit.append((co.x, co.y, ruv.data[li].uv.x, ruv.data[li].uv.y))
        if len(fit) >= 20000:
            break
    F = np.array(fit)
    coef, *_ = np.linalg.lstsq(np.c_[F[:, 0], F[:, 1], np.ones(len(F))], F[:, 2:], rcond=None)
    err = float(np.abs(np.c_[F[:, 0], F[:, 1], np.ones(len(F))] @ coef - F[:, 2:]).max())
    if err > 1e-3:
        raise SystemExit("the reserve's texture coordinates are not a plan projection (off by %.4f)" % err)
    return coef, err


class Shore:
    """The coasts' vertical shore walls in Ground, the generator's skirt: each panel a sea edge
    at `SKIRT_Z`, the two vertices straight above it, and the panel's faces between them.

    `box` limits the panels to a plan box. Holds a bmesh of every Ground object until `cut`."""

    def __init__(self, over_ground, box=None):
        self.over_ground = over_ground
        self.bms = {}
        self.panels = []
        # A shore vertex by its plan position. The two coasts' walls meet a few millimetres
        # apart (each body carries its seam displacement), so a vertex within `JOIN` of one
        # already seen is the same shore vertex.
        self.canon = {}
        for ob in ground_objects():
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            # The edit's face mark goes on before any face is held: adding a layer later leaves
            # every face reference stale.
            bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            self.bms[ob.name] = bm
            for e in bm.edges:
                if not e.is_boundary:
                    continue
                b0, b1 = e.verts
                if b0.co.z > SKIRT_Z + 0.01 or b1.co.z > SKIRT_Z + 0.01:
                    continue
                mid = (b0.co + b1.co) * 0.5
                if box is not None and not (box[0] <= mid.x <= box[1] and box[2] <= mid.y <= box[3]):
                    continue
                t0, t1 = column_top(b0), column_top(b1)
                if t0 is None or t1 is None:
                    continue
                quad = {b0, b1, t0, t1}
                fs = sorted({f for v in (b0, b1) for f in v.link_faces if set(f.verts) <= quad}, key=lambda f: f.index)
                if not fs or len(fs) > 2:
                    raise SystemExit("%s: the shore wall at (%.1f, %.1f) is not one panel" % (ob.name, mid.x, mid.y))
                self.panels.append({"ob": ob.name, "b": (b0, b1), "t": (t0, t1), "faces": fs})
        self.at_key = {}
        for n, p in enumerate(self.panels):
            for b in p["b"]:
                self.at_key.setdefault(self.key(b), []).append(n)
        self.top_z = {}
        self.top_xy = {}
        for p in self.panels:
            for b, t in zip(p["b"], p["t"]):
                self.top_z.setdefault(self.key(b), t.co.z)
                self.top_xy.setdefault(self.key(b), Vector((t.co.x, t.co.y)))
        # Which side of the shore is the sea: each panel's outward normal, away from the
        # coast's own ground. The land side may also be ground the generator still builds (the
        # road corridor's hole at the spur), which Ground does not hold, so sea is told by the
        # wall, not by the absence of Ground.
        self.outward = []
        for p in self.panels:
            a, b = (Vector(v.co.xy) for v in p["b"])
            d = (b - a).normalized()
            out = Vector((d.y, -d.x))
            if over_ground(*((a + b) * 0.5 + out * 1.5)):
                out = -out
            self.outward.append(out)
        self.SA = np.array([tuple(p["b"][0].co.xy) for p in self.panels])
        self.SAB = np.array([tuple(p["b"][1].co.xy) for p in self.panels]) - self.SA
        self.SO = np.array([tuple(o) for o in self.outward])
        self.SL2 = np.maximum((self.SAB ** 2).sum(axis=1), 1e-9)

    def find(self, x, y):
        cx, cy = int(math.floor(x / 0.05)), int(math.floor(y / 0.05))
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for k in self.canon.get((cx + i, cy + j), ()):
                    if abs(k[0] - x) < JOIN and abs(k[1] - y) < JOIN:
                        return k
        return None

    def key(self, v):
        k = self.find(v.co.x, v.co.y)
        if k is None:
            k = (round(v.co.x, 3), round(v.co.y, 3))
            self.canon.setdefault((int(math.floor(v.co.x / 0.05)), int(math.floor(v.co.y / 0.05))), []).append(k)
        return k

    def nearest(self, x, y):
        """The nearest panel to (x, y), the distance to it, and how far along it."""
        P = np.array((x, y))
        u = np.clip(((P - self.SA) * self.SAB).sum(axis=1) / self.SL2, 0.0, 1.0)
        Q = self.SA + self.SAB * u[:, None]
        d2 = ((Q - P) ** 2).sum(axis=1)
        i = int(np.argmin(d2))
        return i, math.sqrt(float(d2[i])), float(u[i])

    def seaward(self, x, y):
        i, _, u = self.nearest(x, y)
        Q = self.SA[i] + self.SAB[i] * u
        return float(((np.array((x, y)) - Q) * self.SO[i]).sum()) > 0.0

    def normals(self, run, keys):
        """Each run vertex's seaward direction: the mean of its panels' outward normals."""
        normal = {k: Vector((0.0, 0.0)) for k in keys}
        for n in run:
            for k in map(self.key, self.panels[n]["b"]):
                normal[k] += self.outward[n]
        return {k: v.normalized() for k, v in normal.items()}

    def cut(self, edit, run, edge_z, dry, what):
        """Cut each run panel at `edge_z` and drop the part below; keep the panels' old faces in
        `Ground_history` for the undo. Frees every bmesh. Returns a report per object cut."""
        cut = {}
        for n in sorted(run):
            cut.setdefault(self.panels[n]["ob"], []).append(self.panels[n])
        for name, bm in self.bms.items():
            if name not in cut or dry:
                bm.free()
        report = {}
        for name, ps in sorted(cut.items()):
            report[name] = {"wall_panels": len(ps), "wall_faces_before": sum(len(p["faces"]) for p in ps)}
        if dry:
            return report
        for name, ps in sorted(cut.items()):
            ob = bpy.data.objects[name]
            me = ob.data
            bm = self.bms[name]
            col = bm.loops.layers.float_color.get("Col")
            uv = bm.loops.layers.uv.get("UVMap")
            fa = bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
            gone = {f for p in ps for f in p["faces"]}
            corner_normals = me.corner_normals
            # Every other face's corner normals, to set again; and the panels' own, for the undo.
            kept_normals = {}
            old_normals = {}
            gone_index = {f.index for f in gone}
            for poly in me.polygons:
                if poly.index in gone_index:
                    old_normals[poly.index] = [Vector(corner_normals[li].vector) for li in poly.loop_indices]
                    continue
                c = poly.center
                for li in poly.loop_indices:
                    kept_normals[corner_key(me.vertices[me.loops[li].vertex_index].co, c)] = Vector(corner_normals[li].vector)
            hist = bmesh.new()
            hcol = hist.loops.layers.float_color.new("Col")
            huv = hist.loops.layers.uv.new("UVMap")
            hmap = {}
            hnormals = []
            for f in sorted(gone, key=lambda f: f.index):
                vs = []
                for v in f.verts:
                    if v not in hmap:
                        hmap[v] = hist.verts.new(v.co)
                    vs.append(hmap[v])
                nf = hist.faces.new(vs)
                nf.material_index = f.material_index
                nf.smooth = f.smooth
                for la, lb, n in zip(f.loops, nf.loops, old_normals[f.index]):
                    lb[hcol] = la[col]
                    lb[huv].uv = la[uv].uv
                    hnormals.append(n)
            hme = bpy.data.meshes.new("%s__before_edit%d" % (name, edit))
            hist.to_mesh(hme)
            hist.free()
            hme.attributes.new("kyt_normal", 'FLOAT_VECTOR', 'CORNER').data.foreach_set(
                "vector", [x for n in hnormals for x in n])
            for m in me.materials:
                hme.materials.append(m)
            hob = bpy.data.objects.new(hme.name, hme)
            hob["kyt_note"] = "the shore wall panels of %s that %s cut, for its --undo; never exported" % (name, what)
            history_collection().objects.link(hob)

            made = {}
            new_faces = []
            for p in ps:
                # The panel's corners as they were, colour and texture at its top and foot: a
                # column shared by two panels carries each its own texture coordinate.
                data = {}
                for f in p["faces"]:
                    for lp in f.loops:
                        data[lp.vert] = (Vector(lp[col][:]), lp[uv].uv.copy())
                outward = p["faces"][0].normal.copy()
                mids = []
                for b, t in zip(p["b"], p["t"]):
                    k = self.key(b)
                    if edge_z[k] >= t.co.z - SNAP:
                        mids.append(t)
                        continue
                    if k not in made:
                        made[k] = bm.verts.new((t.co.x, t.co.y, edge_z[k]))
                    w = (edge_z[k] - b.co.z) / (t.co.z - b.co.z)
                    data[made[k]] = (data[b][0].lerp(data[t][0], w), data[b][1].lerp(data[t][1], w))
                    mids.append(made[k])
                t0, t1 = p["t"]
                m0, m1 = mids
                tris = []
                if m0 is not t0 and m1 is not t1:
                    tris = [(t0, t1, m1), (t0, m1, m0)]
                elif m0 is not t0:
                    tris = [(t0, t1, m0)]
                elif m1 is not t1:
                    tris = [(t0, t1, m1)]
                for tri in tris:
                    n = (tri[1].co - tri[0].co).cross(tri[2].co - tri[0].co)
                    if n.dot(outward) < 0.0:
                        tri = (tri[0], tri[2], tri[1])
                    nf = bm.faces.new(tri)
                    nf.material_index = p["faces"][0].material_index
                    nf.smooth = p["faces"][0].smooth
                    nf[fa] = edit
                    for lp in nf.loops:
                        lp[col], lp[uv].uv = data[lp.vert][0], data[lp.vert][1]
                    new_faces.append(nf)
            bmesh.ops.delete(bm, geom=list(gone), context='FACES')
            bm.to_mesh(me)
            bm.free()
            me.update()
            normals = []
            for poly in me.polygons:
                c = poly.center
                for li in poly.loop_indices:
                    vi = me.loops[li].vertex_index
                    normals.append(kept_normals.get(corner_key(me.vertices[vi].co, c), Vector(poly.normal)))
            me.normals_split_custom_set(normals)
            report[name]["wall_faces_after"] = len(new_faces)
        return report


def build_ground(name, out_v, zmap, faces, colour, coef, edit, note):
    """A new Ground object from a triangulation's points, heights and kept faces, smooth, with
    corner colours from `colour(x, y, z)` and the reserve's plan projection for its texture."""
    me = bpy.data.meshes.new(name)
    verts = [(p.x, p.y, zmap[k]) for k, p in enumerate(out_v)]
    used = sorted({i for f in faces for i in f})
    remap = {i: n for n, i in enumerate(used)}
    me.from_pydata([verts[i] for i in used], [], [tuple(remap[i] for i in f) for f in faces])
    me.validate()
    for poly in me.polygons:
        if poly.normal.z < 0.0:
            poly.flip()
        poly.use_smooth = True
    ccol = me.color_attributes.new("Col", 'FLOAT_COLOR', 'CORNER')
    cuv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            ccol.data[li].color = colour(co.x, co.y, co.z)
            u, v = np.array([co.x, co.y, 1.0]) @ coef
            cuv.data[li].uv = (float(u), float(v))
    fa = me.attributes.new("authored_edit", 'INT', 'FACE')
    fa.data.foreach_set("value", [edit] * len(me.polygons))
    me.materials.append(bpy.data.objects["terrain_world_mainland_reserve"].data.materials[0])
    ob = bpy.data.objects.new(name, me)
    ob["kyt_note"] = note
    bpy.data.collections[GROUND].objects.link(ob)
    return me


def triangulate(pts, segs, zs):
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, segs, [], 0, 1e-4, True)
    zmap = []
    for k, p in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(pts)]
        if not src:
            raise SystemExit("the triangulator added a point at (%.1f, %.1f)" % (p.x, p.y))
        zmap.append(zs[src[0]])
    return out_v, out_f, zmap


def new_land(edit, now_t, pre_t, box, dry):
    """Build the land an edit designed beyond Ground's edge, where the game has open sea.

    The coasts end at the shore in a vertical wall, the generator's skirt, from the shore's top
    edge down to `SKIRT_Z`. The new land is one new Ground object, the grid's edited surface
    from that wall out to where the edit meets the grid's seabed again, so it runs on below the
    waterline the way a real shore does (Christina, 2026-10-06: "new land can go down into the
    ocean a little like in real life"). It meets the shore along the wall: on its top edge where
    the design stands out of the water, the bench rising to it over a `RAMP` bank, and lower
    down the wall towards the ends, where the edit's taper leaves only water against the wall.
    Each wall panel the new land reaches is cut at that line and the part below it, buried,
    goes, so the new land's edge is the wall's own edge and nothing is left inside the land.
    The bluff above the wall and everything else of Ground stays exactly where it was."""
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    bench = float(edit_constant("world_terrain_coast_extension.py", "BENCH_H"))
    if not sea < CREST < bench:
        raise SystemExit("CREST %.1f is not between the sea %.1f and the bench %.1f" % (CREST, sea, bench))
    region, corners = region_faces(edit)

    def in_region(x, y):
        return region.ray_cast(Vector((x, y, 1.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    over_ground = ground_from_above(box)
    shore = Shore(over_ground, (box[0] - 200.0, box[1] + 200.0, box[2] - 200.0, box[3] + 200.0))
    panels = shore.panels
    key = shore.key
    seaward = shore.seaward

    def edge_height(x, y, top_z):
        """Where the new land meets the wall at (x, y): the wall's top edge wherever the design
        stands on the bench, down the wall to the design itself where it is under water."""
        t = height(design_t, x, y)
        if t is None:
            return SKIRT_Z
        f = min(1.0, max(0.0, (t - sea) / (CREST - sea)))
        e = t + f * (top_z - t)
        return top_z if e > top_z - SNAP else max(SKIRT_Z, e)

    # The design: the edited grid, except that a grid vertex the edit did not move, standing
    # off Ground above the sea near the edit, lies under water. Off Ground the grid is either
    # its 10 m smear of the shore wall or ground the generator builds (the road corridor), and
    # neither is new land: at the spur the design rose round the bend against the wall on
    # them. This shapes only the new land; nothing else reads it.
    grid = bpy.data.objects[GRID]
    gme = grid.data
    ged = np.zeros(len(gme.vertices), dtype=np.int32)
    gme.attributes["authored_edit"].data.foreach_get("value", ged)
    gco = [grid.matrix_world @ Vector(v) for v in coords(grid)]
    smeared = 0
    for i, v in enumerate(gco):
        if ged[i] == edit or v.z <= sea - END_UNDER:
            continue
        if not (box[0] <= v.x <= box[1] and box[2] <= v.y <= box[3]) or over_ground(v.x, v.y):
            continue
        v.z = sea - END_UNDER
        smeared += 1
    design_t = BVHTree.FromPolygons(gco, [tuple(p.vertices) for p in gme.polygons])
    run = {n for n, p in enumerate(panels) if in_region(*((p["b"][0].co.xy + p["b"][1].co.xy) * 0.5))}
    if not run:
        raise SystemExit("edit %d reaches no shore wall" % edit)

    def e_at(k):
        return edge_height(k[0], k[1], shore.top_z[k])

    # Carry the run on along the wall until each end meets the wall under water, so no edge
    # of the new land is left standing open above the sea.
    for _ in range(2):
        for k in sorted({k for n in run for k in map(key, panels[n]["b"])}):
            steps = 0
            while sum(1 for n in shore.at_key[k] if n in run) == 1 and e_at(k) > sea - END_UNDER:
                nxt = [n for n in shore.at_key[k] if n not in run]
                if not nxt or steps > 60:
                    raise SystemExit("the new land's end at (%.1f, %.1f) stands %.1f m over the sea against the wall" % (
                        k[0], k[1], e_at(k) - sea))
                run.add(nxt[0])
                k = [kk for kk in map(key, panels[nxt[0]]["b"]) if kk != k][0]
                steps += 1
    keys = sorted({k for n in run for k in map(key, panels[n]["b"])})
    edge_z = {k: e_at(k) for k in keys}
    design_at = {k: (height(design_t, k[0], k[1]) if height(design_t, k[0], k[1]) is not None else edge_z[k]) for k in keys}
    ends = [k for k in keys if sum(1 for n in shore.at_key[k] if n in run) == 1]
    normal = shore.normals(run, keys)

    # Points: the shore line, rows across the bank, and the edit's grid corners off the land.
    # The shore points stand exactly on the wall's top vertices, so the new land's edge is the
    # wall's own edge, not one a rounding away.
    pts = [shore.top_xy[k].copy() for k in keys]
    index = {k: i for i, k in enumerate(keys)}
    segs = [(index[key(panels[n]["b"][0])], index[key(panels[n]["b"][1])]) for n in sorted(run)]
    taken = {}

    def take(q):
        taken.setdefault((int(q.x // CROWD), int(q.y // CROWD)), []).append(q)

    def crowded(q):
        cx, cy = int(q.x // CROWD), int(q.y // CROWD)
        return any((q - o).length < CROWD for i in (-1, 0, 1) for j in (-1, 0, 1) for o in taken.get((cx + i, cy + j), ()))

    for q in pts:
        take(q)
    for k in keys:
        if edge_z[k] - design_at[k] < 0.1:
            continue
        for s in (2.5, 5.0, 7.5, RAMP):
            q = shore.top_xy[k] + normal[k] * s
            if not over_ground(q.x, q.y) and seaward(q.x, q.y) and not crowded(q):
                pts.append(q)
                take(q)
    for q in corners:
        if not over_ground(q.x, q.y) and seaward(q.x, q.y) and not crowded(q):
            pts.append(q)
            take(q)

    # Heights: the edited grid, lifted near the shore by the bank.
    A = np.array([pts[i].to_tuple() for i, _ in segs])
    B = np.array([pts[j].to_tuple() for _, j in segs])
    lift_a = np.array([max(0.0, edge_z[keys[i]] - design_at[keys[i]]) for i, _ in segs])
    lift_b = np.array([max(0.0, edge_z[keys[j]] - design_at[keys[j]]) for _, j in segs])
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(axis=1), 1e-9)

    def to_shore(p):
        P = np.array(p.to_tuple())
        u = np.clip(((P - A) * AB).sum(axis=1) / L2, 0.0, 1.0)
        d = np.sqrt((((A + AB * u[:, None]) - P) ** 2).sum(axis=1))
        i = int(np.argmin(d))
        return float(d[i]), float(lift_a[i] + (lift_b[i] - lift_a[i]) * u[i])

    zs = []
    for i, p in enumerate(pts):
        if i < len(keys):
            zs.append(edge_z[keys[i]])
            continue
        t = height(design_t, p.x, p.y)
        if t is None:
            raise SystemExit("a new-land point at (%.1f, %.1f) lies off the grid" % (p.x, p.y))
        d, lift = to_shore(p)
        zs.append(t + lift * (1.0 - smoothstep(0.0, RAMP, d)))

    out_v, out_f, zmap = triangulate(pts, segs, zs)
    faces = []
    for tri in out_f:
        c = Vector((sum(out_v[i].x for i in tri) / 3.0, sum(out_v[i].y for i in tri) / 3.0))
        longest = max((out_v[tri[k]] - out_v[tri[(k + 1) % 3]]).length for k in range(3))
        if longest > 40.0 or over_ground(c.x, c.y) or not seaward(c.x, c.y):
            continue
        if not in_region(c.x, c.y) and to_shore(c)[0] > RAMP:
            continue
        faces.append(tuple(tri))

    land_report = {"faces": len(faces), "shore_m": round(sum((pts[i] - pts[j]).length for i, j in segs), 1),
                   "shore_vertices": len(keys), "top_of_wall": sum(1 for k in keys if edge_z[k] >= shore.top_z[k] - SNAP),
                   "highest": round(max(zmap), 2), "deepest": round(min(zmap), 2), "grid_held_under_sea": smeared,
                   "ends_under_sea": [round(edge_z[k] - sea, 2) for k in ends]}
    # The colours read the walls' top faces before the cut changes them.
    shore_col = {}
    for ob in ground_objects():
        if ob.name not in {panels[n]["ob"] for n in run}:
            continue
        ome = ob.data
        ocol = ome.color_attributes["Col"]
        for poly in ome.polygons:
            if poly.normal.z < 0.3:
                continue
            c = poly.center
            if ob.name == "terrain_world_mainland_reserve" and not (box[0] <= c.x <= box[1] and box[2] <= c.y <= box[3]):
                continue
            for li in poly.loop_indices:
                co = ome.vertices[ome.loops[li].vertex_index].co
                k = shore.find(co.x, co.y)
                if k in index:
                    shore_col.setdefault(k, []).append(Vector(ocol.data[li].color))
    report = shore.cut(edit, run, edge_z, dry, "Ground edit %d" % edit)
    if dry:
        return report, land_report, None

    # The new land's colours: the planting at the top of the wall it meets, sand from the
    # bench's crest down, the sea cliff's colour deep under water; its texture coordinates
    # continue the reserve's own.
    coef, uv_err = uv_projection(box)
    kk = sorted(shore_col)
    if not kk:
        raise SystemExit("no planting found at the top of the shore wall")
    tree = KDTree(len(kk))
    for i, k in enumerate(kk):
        tree.insert((k[0], k[1], 0.0), i)
    tree.balance()
    bench_col = {k: sum(shore_col[k], Vector((0.0, 0.0, 0.0, 0.0))) / len(shore_col[k]) for k in kk}

    def colour(x, y, z):
        c = bench_col[kk[tree.find((x, y, 0.0))[1]]]
        grain = 1.0 + math.sin(x * 0.37) * math.sin(-y * 0.41) * 0.05
        sand = Vector((SAND[0] * grain, SAND[1] * grain, SAND[2] * grain, 1.0))
        bed = Vector((SEABED[0] * grain, SEABED[1] * grain, SEABED[2] * grain, 1.0))
        c = c.lerp(sand, 1.0 - smoothstep(SAND_FROM[1], SAND_FROM[0], z))
        return c.lerp(bed, 1.0 - smoothstep(SEABED_FROM[1], SEABED_FROM[0], z))

    name = NEW_LAND[edit]
    me = build_ground(name, out_v, zmap, faces, colour, coef, edit,
                      "Ground edit %d: land the grid edit designed beyond the shore, where the game had open sea; "
                      "built by tools/blender/world_terrain_ground_edit.py, undone by its --undo" % edit)
    area = sum(p.area for p in me.polygons if min(me.vertices[i].co.z for i in p.vertices) >= sea)
    land_report.update({"faces": len(me.polygons), "vertices": len(me.vertices), "dry_ha": round(area / 10000.0, 2),
                        "uv_fit_error": round(uv_err, 6)})
    return report, land_report, name


def coast_shelf(edit, dry):
    """Run every coast in Ground on below the waterline (Christina, 2026-10-06: "in general the
    coast should have enough mesh extending into the water and below the water line").

    The coasts end at the shore in the generator's vertical wall, down to `SKIRT_Z` with nothing
    beyond it. Each wall is cut `SHELF_UNDER` below the waterline, so the water still meets the
    wall and the shore above it is exactly as it was, and the part below goes. From that line a
    shelf, one new Ground object, slopes out `SHELF_W` to `SHELF_DEPTH`, steepest at the wall and
    easing out flat, where a seabed can join it. Where two shores face each other across narrow
    water their shelves meet, each point taking the depth its nearest wall gives it. The park's
    own west shore is left alone: there the generator's shore strip, pier and protected NT-1 meet
    the sea, not Ground."""
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    cut_z = sea - SHELF_UNDER
    over_ground = ground_from_above()
    shore = Shore(over_ground)
    panels = shore.panels
    key = shore.key
    x0 = plan_constant("REBUILD_FOOTPRINT_MIN_X") - SHELF_CLEAR
    x1 = plan_constant("REBUILD_FOOTPRINT_MAX_X") + SHELF_CLEAR
    z0 = plan_constant("REBUILD_FOOTPRINT_MIN_Z") - SHELF_CLEAR
    z1 = plan_constant("REBUILD_FOOTPRINT_MAX_Z") + SHELF_CLEAR

    def in_park(x, y):
        return x0 <= x <= x1 and z0 <= -y <= z1

    run = {n for n, p in enumerate(panels) if not in_park(*((p["b"][0].co.xy + p["b"][1].co.xy) * 0.5))}
    if not run:
        raise SystemExit("Ground has no shore wall to run on below the water")
    keys = sorted({k for n in run for k in map(key, panels[n]["b"])})
    edge_z = {k: (shore.top_z[k] if shore.top_z[k] <= cut_z + SNAP else cut_z) for k in keys}
    normal = shore.normals(run, keys)
    pts = [shore.top_xy[k].copy() for k in keys]
    index = {k: i for i, k in enumerate(keys)}
    segs = [(index[key(panels[n]["b"][0])], index[key(panels[n]["b"][1])]) for n in sorted(run)]

    A = np.array([pts[i].to_tuple() for i, _ in segs])
    AB = np.array([pts[j].to_tuple() for _, j in segs]) - A
    EA = np.array([edge_z[keys[i]] for i, _ in segs])
    EB = np.array([edge_z[keys[j]] for _, j in segs])
    L2 = np.maximum((AB ** 2).sum(axis=1), 1e-9)

    def to_run(x, y):
        """The distance to the nearest wall the shelf runs from, and that wall's cut height."""
        P = np.array((x, y))
        u = np.clip(((P - A) * AB).sum(axis=1) / L2, 0.0, 1.0)
        d2 = (((A + AB * u[:, None]) - P) ** 2).sum(axis=1)
        i = int(np.argmin(d2))
        return math.sqrt(float(d2[i])), float(EA[i] + (EB[i] - EA[i]) * u[i])

    def depth(d, e):
        t = min(1.0, d / SHELF_W)
        return min(e, e + (SHELF_DEPTH - e) * (1.0 - (1.0 - t) ** 2))

    def wanted(x, y):
        """A point the shelf covers: on the sea side, off the land and the park, and in front of
        a wall it runs from rather than one it leaves alone."""
        if in_park(x, y) or over_ground(x, y) or not shore.seaward(x, y):
            return False
        return shore.nearest(x, y)[0] in run

    # Rows out from the wall, nearest first; a row's point too near one already placed goes, so
    # rows from the two walls of a cove do not pile up.
    taken = {}

    def crowded(q, r):
        cx, cy = int(q.x // 8.0), int(q.y // 8.0)
        reach = int(math.ceil(r / 8.0))
        return any((q - o).length < r for i in range(-reach, reach + 1) for j in range(-reach, reach + 1)
                   for o in taken.get((cx + i, cy + j), ()))

    rows = 0
    last = 0.0
    for s in SHELF_ROWS:
        r = min(CROWD + SHELF_SPREAD * s, 0.45 * (s - last))
        last = s
        for k in keys:
            q = shore.top_xy[k] + normal[k] * s
            if not wanted(q.x, q.y) or crowded(q, r):
                continue
            pts.append(q)
            taken.setdefault((int(q.x // 8.0), int(q.y // 8.0)), []).append(q)
            rows += 1
    zs = [edge_z[k] for k in keys] + [depth(*to_run(p.x, p.y)) for p in pts[len(keys):]]

    out_v, out_f, zmap = triangulate(pts, segs, zs)
    faces = []
    for tri in out_f:
        c = Vector((sum(out_v[i].x for i in tri) / 3.0, sum(out_v[i].y for i in tri) / 3.0))
        longest = max((out_v[tri[k]] - out_v[tri[(k + 1) % 3]]).length for k in range(3))
        if longest > SHELF_LONGEST or not wanted(c.x, c.y) or to_run(c.x, c.y)[0] > SHELF_W + 1.0:
            continue
        faces.append(tuple(tri))

    shelf_report = {"faces": len(faces), "shore_m": round(sum((pts[i] - pts[j]).length for i, j in segs), 1),
                    "wall_panels": len(run), "left_at_the_park": len(panels) - len(run),
                    "walls_kept_above": sum(1 for k in keys if edge_z[k] < shore.top_z[k] - SNAP),
                    "walls_wholly_under": sum(1 for k in keys if edge_z[k] >= shore.top_z[k] - SNAP),
                    "row_points": rows, "deepest": round(min(zmap), 2)}
    # Sand under a beach: the shore's own colour at the top of the wall, where it is the
    # generator's beach sand.
    sandy = set()
    run_objects = {panels[n]["ob"] for n in run}
    for ob in ground_objects():
        if ob.name not in run_objects:
            continue
        ome = ob.data
        ocol = ome.color_attributes["Col"]
        for poly in ome.polygons:
            if poly.normal.z < 0.3:
                continue
            for li in poly.loop_indices:
                co = ome.vertices[ome.loops[li].vertex_index].co
                k = shore.find(co.x, co.y)
                if k in index and (Vector(ocol.data[li].color[:3]) - Vector(SAND)).length < SANDY:
                    sandy.add(k)
    report = shore.cut(edit, run, edge_z, dry, "the coast shelf (Ground edit %d)" % edit)
    shelf_report["sandy_shore_vertices"] = len(sandy)
    if dry:
        return report, shelf_report, None

    coef, uv_err = uv_projection()
    tree = KDTree(len(keys))
    for i, k in enumerate(keys):
        tree.insert((k[0], k[1], 0.0), i)
    tree.balance()

    def colour(x, y, z):
        grain = 1.0 + math.sin(x * 0.37) * math.sin(-y * 0.41) * 0.05
        bed = Vector((SEABED[0] * grain, SEABED[1] * grain, SEABED[2] * grain, 1.0))
        if keys[tree.find((x, y, 0.0))[1]] not in sandy:
            return bed
        sand = Vector((SAND[0] * grain, SAND[1] * grain, SAND[2] * grain, 1.0))
        return sand.lerp(bed, 1.0 - smoothstep(SEABED_FROM[1], SEABED_FROM[0], z))

    me = build_ground(SHELF, out_v, zmap, faces, colour, coef, edit,
                      "The coast shelf (Ground edit %d): every coast run on below the waterline from its shore "
                      "wall, cut %.1f m under the sea; built by tools/blender/world_terrain_ground_edit.py "
                      "-- --edit shelf, undone by its --undo" % (edit, SHELF_UNDER))
    area = sum(p.area for p in me.polygons)
    shelf_report.update({"faces": len(me.polygons), "vertices": len(me.vertices), "area_ha": round(area / 10000.0, 1),
                         "uv_fit_error": round(uv_err, 6)})
    return report, shelf_report, SHELF


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
        # A kept vertex is found where it stands; one the edit moved, by its plan position,
        # unless another kept vertex stands in that column (a shore wall's top over its foot).
        exact = {tuple(round(c, 4) for c in v.co): v for v in bm.verts}
        column = {}
        for v in bm.verts:
            column.setdefault((round(v.co.x, 4), round(v.co.y, 4)), []).append(v)
        col = bm.loops.layers.float_color["Col"]
        uv = bm.loops.layers.uv["UVMap"]
        hme = hob.data
        hcol = hme.color_attributes["Col"]
        huv = hme.uv_layers["UVMap"]
        claimed = {exact[k] for k in (tuple(round(c, 4) for c in v.co) for v in hme.vertices) if k in exact}
        made = []
        for v in hme.vertices:
            k3 = tuple(round(c, 4) for c in v.co)
            k2 = k3[:2]
            spare = [o for o in column.get(k2, []) if o not in claimed]
            if k3 in exact:
                made.append(exact[k3])
            elif len(spare) == 1 and len(column[k2]) == 1:
                spare[0].co = v.co
                made.append(spare[0])
            else:
                nv = bm.verts.new(v.co)
                column.setdefault(k2, []).append(nv)
                claimed.add(nv)
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
        # The restored faces' corner normals, where the history kept them (edit 2 on); else smooth.
        if "kyt_normal" in hme.attributes:
            hn = np.zeros(len(hme.loops) * 3)
            hme.attributes["kyt_normal"].data.foreach_get("vector", hn)
            hn = hn.reshape(-1, 3)
            for poly in hme.polygons:
                c = poly.center
                for li in poly.loop_indices:
                    kept_normals[corner_key(hme.vertices[hme.loops[li].vertex_index].co, c)] = Vector(hn[li])
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
    if edit in NEW_LAND:
        # The sea, so the waterline reads; only in the render, which runs after the save.
        sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
        sme = bpy.data.meshes.new("tmp_sea")
        sme.from_pydata([(-3000.0, 3000.0, sea), (4000.0, 3000.0, sea), (4000.0, -4000.0, sea), (-3000.0, -4000.0, sea)], [], [(0, 1, 2, 3)])
        sob = bpy.data.objects.new("tmp_sea", sme)
        sob.color = LAKE_COLOUR
        scene.collection.objects.link(sob)
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
    if edit != SHELF_ID:
        now_t, pre_t, box, grid_points = grid_surfaces(edit)
    before = {ob.name: coords(ob).copy() for ob in ground_objects()}
    reports = {}
    land = None
    land_report = {}
    if edit == SHELF_ID:
        reports, land_report, land = coast_shelf(edit, a["dry"])
        print("  %-34s %s" % (SHELF, ", ".join("%s %s" % kv for kv in land_report.items())))
    elif edit in NEW_LAND:
        reports, land_report, land = new_land(edit, now_t, pre_t, box, a["dry"])
        print("  %-34s %s" % (NEW_LAND[edit], ", ".join("%s %s" % kv for kv in land_report.items())))
    else:
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
        if ob.name == land:
            continue
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
    if edit == SHELF_ID:
        design = {"name": "coast_shelf"}
    else:
        design = next(e for e in json.loads(bpy.data.objects[GRID].get("kyt_edits", "[]")) if e.get("id") == edit)
    tris = ground_triangles()
    coll = lakes_collection()
    added = [land] if land else []
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
             "date": TODAY, "objects": sorted(reports), "report": reports, "lakes_ha": areas,
             "added": added, "hid": hid, "export_before": export_before}
    if land:
        entry["new_land"] = land_report
    log(entry)
    held = sum(r.get("seam_held", 0) for r in reports.values())
    if edit == SHELF_ID:
        readme("Ground edit %d (%s), %s: every coast's shore wall cut %.1f m under the sea and the part below "
               "dropped, in %s; from that line %s slopes %.0f m out to %.1f (%s); the wall panels' old faces "
               "kept in %s. Undo: tools/blender/world_terrain_ground_edit.py -- --edit shelf --undo." % (
                   edit, design["name"], TODAY, SHELF_UNDER, ", ".join(reports), land, SHELF_W, SHELF_DEPTH,
                   ", ".join("%s %s" % kv for kv in land_report.items()), HISTORY))
    elif land:
        readme("Ground edit %d (%s), Stage 3, %s: the land grid edit %d designed beyond the shore built as %s in "
               "Ground (%s); the shore wall panels it meets cut at its edge in %s, their old faces kept in %s. Undo: "
               "tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
                   edit, design["name"], TODAY, edit, land, ", ".join("%s %s" % kv for kv in land_report.items()),
                   ", ".join(reports), HISTORY, edit))
    else:
        readme("Ground edit %d (%s), Stage 3, %s: grid edit %d carried onto Ground (%s): its region refined to "
           "a %.0f m lattice and given the grid's designed surface; %d vertices on the seams with the generator's "
           "ground held where they were; water %s built on Ground in the Lakes collection, exported with Ground; "
           "design planes %s hidden; the replaced faces kept in %s. Undo: "
           "tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
               edit, design["name"], TODAY, edit, ", ".join(reports), LATTICE, held,
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
