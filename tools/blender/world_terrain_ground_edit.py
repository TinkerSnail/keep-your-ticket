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

Edit 1, the south range blend (2026-10-06), lands on the range's and city's closed landform
shells, which overlap: in the zone it changed they are cut along its edge, emptied and capped,
and one sheet, `RANGE_BLEND`, takes the designed surface there. See `range_blend`.

Edit 6, the hillside regrade (2026-10-08), goes in with edit 7, its refinement of the band
beside the coast highway (`WITH`), measured from the grid before either. It reshapes ground the
highway's corridor covers, so Ground's edge along the corridor moves with it and the edit's
designed natural ground under the corridor is handed to the generator, which cuts the road's
sides down to it (`ROAD_NATURAL`, `road_natural`).

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
# And an edit's own grid points and the lattice keep this far from every edge of the region's
# faces, which stay as constraints: a point a hair beside one makes a sliver that shades as a
# notch (2026-10-08: edits 6 and 7's 10 m and 3 m grids left 889 along the reserve's 24 m edges).
# Edits 4 and 5, carried before, had sparse grids and were not refined with it.
SEP = 1.0
# The bay's water (tools/gen_props.gd, mats["water"]), so lake and sea read as one water.
LAKE_COLOUR = (0.34, 0.44, 0.52, 1.0)
DESIGN_PLANES = {"K1": "water_K1_enlarged", "L0": "water_L0_enlarged"}
# Small still water an edit designed as a plane on the grid, built on Ground inside that
# plane's outline grown by `POOL_GROW`: {edit: {game name: design plane}}.
POOLS = {5: {"plunge_pool": "water_plunge_pool"}}
POOL_GROW = 2.0
# Render views per edit beyond the lakes: {name: ((x, z) centre, width across, eye level)}.
VIEWS = {6: {"hillside": ((160.0, 570.0), 520.0, 30.0), "hillside_band": ((120.0, 600.0), 280.0, 25.0)},
         101: {"landform_bay": ((200.0, 3500.0), 1800.0, -8.0), "landform_plug": ((-730.0, -2220.0), 900.0, -8.0),
              "landform_south": ((-600.0, 6600.0), 1500.0, -8.0)},
         1: {"range_west": ((-1150.0, 5550.0), 1100.0, 40.0), "range_east": ((-150.0, 5800.0), 1500.0, 60.0)},
         100: {"shelf_north": ((-300.0, -1300.0), 1400.0, -8.0), "shelf_east": ((3300.0, 600.0), 1400.0, -8.0),
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
# Edit 1, the south range blend (2026-10-06), lands on the range's and city's landforms, which
# joined Ground that day as their sources drew them: closed shells (a top, sides straight down,
# a floor at -11) lying over one another. Carried shell by shell, a cut would bare the shell
# under it and a raise would leave a slot against the next one's side. So in the zone the edit
# changed, Ground becomes one sheet, this object: every shell is cut along the zone's edge,
# emptied inside it and capped where it was cut, so each is still closed, and the sheet takes the
# designed surface inside and meets the topmost shell's cut edge, edge for edge. See `range_blend`.
RANGE_BLEND = {1: "terrain_south_range_blend"}
# The sheet's lattice inside the zone: the grid's own 25 m, halved.
RANGE_LATTICE = 12.5
# Where the zone's edge crosses a shell's straight side, the ground steps down it; the sheet, a
# surface over the plan, takes the step over twice this of its edge.
JUMP = 0.01
OFF_LINE = 0.05
# The sheet's lattice by the coastal branch's road box (see `range_blend`).
HELD_LATTICE = 4.0
# Over this far in from the zone's edge the edit fades in, and the sheet has rows along it,
# points this far apart.
EDGE_FADE = 12.5
EDGE_ROW = 6.0
# The range's level bands (background_distant_range_south's `toe_rock_bands`): a sheet face that
# was in one takes its band again from its height after the edit.
TOE_BANDS = ((16.0, "distant_massif_toe_dark"), (32.0, "distant_massif_toe_rock"),
             (43.0, "distant_massif_toe_rock_forest_1"), (54.0, "distant_massif_toe_rock_forest_2"),
             (65.0, "distant_massif_toe_rock_forest_3"), (math.inf, "distant_massif_forest"))
# Land the edit made out of the sea is the range's cove sand below this, its bands above.
SAND_BELOW = -4.0
# The landforms' coasts (2026-10-08), the coast shelf's sibling: `-- --edit landform_shelf`, one
# more object, the landform shells themselves untouched. See `landform_shelf`.
LANDFORM_SHELF_ID = 101
LANDFORM_SHELF = "terrain_landform_shelf"
# Shore points along a landform's side, at most this far apart, as the generator's wall panels are.
LANDFORM_SHORE_STEP = 8.0
# The edits this script knows how to carry, each in its own Stage 3 batch.
# Edit 7 (2026-10-03) refined edit 6, the hillside regrade: the band beside the coast highway
# that edit 6 had to hold, re-cut at 3 m on faces of its own. It is the rest of edit 6's design,
# not a design of its own, so the two go onto Ground together as edit 6, measured from the grid
# as it stood before either. Edit 7's own heights before it are edit 6's surface, and its band's
# old faces are kept on the grid as `kyt_<tag>_removed_faces`: {edit: (its refinement, face tag)}.
WITH = {6: (7, "edit7_face")}
# Edit 6 reshapes ground the coast highway's corridor covers: the hill's old surface runs down into
# the cutting's batter, which the generator builds, 15 to 20 m wider than the strip edit 7 kept.
# Christina, 2026-10-08, "let the slope follow": Ground's edge along the corridor moves with the
# edit instead of being held (by `design_at`'s weight, uncapped, as the corridor's side will), and
# the edit's designed natural ground under the corridor goes to the game beside Ground, so the
# generator cuts the road's sides down to it; the road's own level never reads it. The object
# stands on the designed ground and carries, as its u texture coordinate, how far the design
# governs at each point, 1 inside the edit fading to 0 where it leaves the ground as it was; it is
# no ground one stands on (`kyt_collision=none`, hidden in the game). {edit: that object}.
ROAD_NATURAL = {6: "corridor_natural_edit6"}
EARTHWORKS = "Earthworks"
ROAD_NATURAL_STEP = 3.0
# A lattice point this close to Ground's edge is dropped, so the triangulation makes no slivers.
ROAD_NATURAL_CLEAR = 1.0
# What the grid may name under a corridor point the design governs: the corridor, and the ground
# its edge faces straddle. Anything else there (a tunnel lid, an anchor) is refused.
ROAD_NATURAL_OWNERS = ("terrain_road_corridor", "terrain_world_mainland_reserve")
CARRIED = (1, 2, 4, 5, 6, SHELF_ID, LANDFORM_SHELF_ID)


def argv():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"edit": None, "dry": "--dry" in a, "undo": "--undo" in a, "render": None}
    if "--edit" in a:
        v = a[a.index("--edit") + 1]
        out["edit"] = SHELF_ID if v == "shelf" else LANDFORM_SHELF_ID if v == "landform_shelf" else int(v)
        for edit, (also, _tag) in WITH.items():
            if out["edit"] == also:
                raise SystemExit("edit %d refines edit %d and is carried with it: --edit %d" % (also, edit, edit))
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
    box the edit's vertices cover, and those vertices' plan positions. An edit carried `WITH`
    its refinement is measured as both left the grid against the grid before either."""
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
    before_polys = polys
    moved = sel
    if edit in WITH:
        also, tag = WITH[edit]
        if not (ed == also).any():
            raise SystemExit("the grid has no vertex of edit %d, which edit %d is carried with" % (also, edit))
        refined = np.zeros(len(me.polygons), dtype=np.int32)
        me.attributes[tag].data.foreach_get("value", refined)
        # The refinement's faces are none of the grid before it; the faces it dropped are.
        before_polys = [tuple(p.vertices) for p in me.polygons if not refined[p.index]] + [
            tuple(s["v"]) for s in json.loads(ob["kyt_%s_removed_faces" % tag])]
        moved = sel | (ed == also)
    idx = np.nonzero(moved)[0]
    xs = np.array([now[i].x for i in idx])
    ys = np.array([now[i].y for i in idx])
    box = (xs.min() - 60.0, xs.max() + 60.0, ys.min() - 60.0, ys.max() + 60.0)
    points = [Vector((now[i].x, now[i].y)) for i in idx]
    return BVHTree.FromPolygons(now, polys), BVHTree.FromPolygons(before, before_polys), box, points


def height(tree, x, y):
    hit = tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
    return None if hit[0] is None else hit[0].z


def design_at(now_t, pre_t, x, y):
    """The edited grid surface at (x, y), how far it governs there (1 where the edit moved the
    grid by `BLEND` or more, fading to 0 where it did not move it) and the grid's move; None
    where the edit left the grid alone."""
    t = height(now_t, x, y)
    p = height(pre_t, x, y)
    if t is None or p is None:
        return None
    d = t - p
    if abs(d) <= MIN_CHANGE:
        return None
    return t, min(1.0, abs(d) / BLEND), d


def designed(now_t, pre_t, x, y, z):
    """Where edit N puts ground that stands at z at (x, y): unchanged where the edit left
    the grid alone, and the edited grid surface where it moved the grid by `BLEND` or more,
    faded between. The design wins outright inside the edit even where Ground stood a few
    tenths below it: taking the lower of the two at every point (the first try) flipped
    between them along every bank, by the grid's own 0.3 m, and serrated it."""
    tw = design_at(now_t, pre_t, x, y)
    if tw is None:
        return z
    t, w, d = tw
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
    # Unless the corridor follows the edit (`ROAD_NATURAL`): then its edge moves with it.
    follow = edit in ROAD_NATURAL
    pinned = set() if follow else {bm.verts[vi] for vi in seam}
    report = {"faces_before": len(faces), "region_vertices": len(rverts), "seam_held": 0 if follow else len(held),
              "seam_held_most": 0.0 if follow else max((abs(h) for h in held), default=0.0)}
    if follow:
        report.update({"seam_followed": len(held), "seam_followed_most": max((abs(h) for h in held), default=0.0)})
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
    extra = []
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

    def take(q):
        taken.setdefault((int(q.x // CROWD), int(q.y // CROWD)), []).append(q)

    for q in pts2 + extra:
        take(q)

    def crowded(q, r=CROWD):
        cx, cy = int(q.x // CROWD), int(q.y // CROWD)
        return any((q - o).length < r for i in (-1, 0, 1) for j in (-1, 0, 1) for o in taken.get((cx + i, cy + j), ()))

    edges_at = {}
    for f in faces:
        for e in f.edges:
            a, b = e.verts[0].co.xy.copy(), e.verts[1].co.xy.copy()
            for cx in range(int((min(a.x, b.x) - SEP) // LATTICE), int((max(a.x, b.x) + SEP) // LATTICE) + 1):
                for cy in range(int((min(a.y, b.y) - SEP) // LATTICE), int((max(a.y, b.y) + SEP) // LATTICE) + 1):
                    edges_at.setdefault((cx, cy), []).append((a, b))

    def beside_edge(q):
        for a, b in edges_at.get((int(q.x // LATTICE), int(q.y // LATTICE)), ()):
            d = b - a
            l2 = d.length_squared
            s = 0.0 if l2 < 1e-12 else min(1.0, max(0.0, (q - a).dot(d) / l2))
            if (q - (a + d * s)).length < SEP:
                return True
        return False

    for p in grid_points:
        if inside(p) and not beside_edge(p) and not crowded(p, SEP):
            extra.append(p)
            take(p)

    x = math.floor(min(xs) / LATTICE) * LATTICE
    while x <= max(xs):
        y = math.floor(min(ys) / LATTICE) * LATTICE
        while y <= max(ys):
            q = Vector((x, y))
            if inside(q) and not crowded(q) and not beside_edge(q):
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
            # A point on the region's open edge (an edit's grid vertex on Ground's edge at the
            # road corridor, edit 6) can graze past it; it is on the surface a hair inward.
            for dx, dy in ((1e-3, 0.0), (-1e-3, 0.0), (0.0, 1e-3), (0.0, -1e-3)):
                z = height(surf, p.x + dx, p.y + dy)
                if z is not None:
                    break
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
        if v in pinned:
            continue
        if any(e.is_boundary for e in v.link_edges):
            if not follow:
                continue
            # On the road corridor's edge: moved as the corridor's side will be, by the design's
            # weight and uncapped, so the two meet.
            tw = design_at(now_t, pre_t, v.co.x, v.co.y)
            z = v.co.z if tw is None else v.co.z + tw[1] * (tw[0] - v.co.z)
        else:
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


def landform_shelf(edit, dry):
    """Run the landforms' coasts on below the waterline (Christina, 2026-10-06: "in general the
    coast should have enough mesh extending into the water and below the water line"), as the
    coast shelf does the generator's.

    The range's and city's landforms, which joined Ground on 2026-10-06, are closed shells, and
    where one meets the open sea its side runs straight down to its floor at about -11 with nothing
    beyond; since the sea cleared (2026-10-07) that side shows under the water. The shells are kept
    whole. The shelf starts on each sea-facing side `SHELF_UNDER` below the waterline, or at the
    side's top where that is lower, and slopes out `SHELF_W` to `SHELF_DEPTH`; the side below its
    start stands behind it. It meets no other ground: where ground already lies under the water
    (the coast shelf, edit 1's sheet, another shell), it stops short of it. Sandy where the shore is:
    the landform's own sand or beach colour at the top of its side, or a beach sheet on it."""
    if LANDFORM_SHELF in bpy.data.objects:
        raise SystemExit("%s already exists" % LANDFORM_SHELF)
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    cut_z = sea - SHELF_UNDER
    over_ground = ground_from_above()
    beach_bm = bmesh.new()
    for ob in ground_objects():
        if ob.get("kyt_collision") == "none":
            beach_bm.from_mesh(ob.data)
    beach_tree = BVHTree.FromBMesh(beach_bm)
    beach_bm.free()

    def on_beach(x, y):
        return beach_tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    keys = []
    index = {}
    xy = []
    edge_z = []
    normal = []
    sandy = set()
    segs = []
    seg_out = []
    shells = []

    def key(co):
        k = (round(co.x, 2), round(co.y, 2))
        if k not in index:
            index[k] = len(keys)
            keys.append(k)
            xy.append(Vector((co.x, co.y)))
            edge_z.append(None)
            normal.append(Vector((0.0, 0.0)))
        return index[k]

    for ob in ground_objects():
        if ob.get("kyt_collision") == "none":
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.normal_update()
        if any(e.is_boundary for e in bm.edges) or not any(f.normal.z < -0.5 for f in bm.faces):
            bm.free()
            continue
        if ob.matrix_world != ob.matrix_world.Identity(4):
            raise SystemExit("%s is not at the origin; Ground objects hold world positions" % ob.name)
        bm.faces.ensure_lookup_table()
        own = BVHTree.FromBMesh(bm)
        mats = [m.name if m else "" for m in ob.data.materials]

        def own_top(p):
            hit = own.ray_cast(Vector((p.x, p.y, 5000.0)), Vector((0.0, 0.0, -1.0)))
            return None if hit[0] is None else (hit[0].z, hit[2])

        found = 0
        for e in bm.edges:
            # The floor's rim: where a face looking down meets one that does not.
            fs = e.link_faces
            if len(fs) != 2 or (fs[0].normal.z < -0.5) == (fs[1].normal.z < -0.5):
                continue
            a, b = e.verts
            # A floor standing above the cut is buried in other ground, not at the sea.
            if max(a.co.z, b.co.z) > cut_z:
                continue
            d = b.co.xy - a.co.xy
            if d.length < 0.05:
                continue
            m = (a.co.xy + b.co.xy) * 0.5
            n = Vector((d.y, -d.x)).normalized()
            if own_top(m + n * 0.5) is not None:
                n = -n
            if own_top(m - n * 0.5) is None or own_top(m + n * 0.5) is not None:
                continue
            if over_ground(*(m + n * 2.0)):
                continue
            # The side in pieces of at most `LANDFORM_SHORE_STEP` (the shells' sides run up to a
            # hundred metres), each point's height its top just inside, under the cut; a side
            # with a point that has no top (a sliver at a corner of edit 1's caps) is left.
            pieces = max(1, int(math.ceil(d.length / LANDFORM_SHORE_STEP)))
            along = [a.co.xy.lerp(b.co.xy, k / pieces) for k in range(pieces + 1)]
            tops = [own_top(q - n * 0.05) for q in along]
            if None in tops:
                continue
            ids = []
            for q, top in zip(along, tops):
                i = key(q)
                normal[i] += n
                if edge_z[i] is None:
                    edge_z[i] = min(cut_z, top[0])
                    name = mats[bm.faces[top[1]].material_index]
                    if "sand" in name or "beach" in name or on_beach(*(q - n * 0.05)):
                        sandy.add(i)
                ids.append(i)
            for ia, ib in zip(ids, ids[1:]):
                segs.append((ia, ib))
                seg_out.append(n)
            found += 1
        if found:
            shells.append("%s %d" % (ob.name, found))
        bm.free()
    if not segs:
        raise SystemExit("no landform meets the open sea")
    normal = [v.normalized() for v in normal]

    A = np.array([xy[i].to_tuple() for i, _ in segs])
    AB = np.array([xy[j].to_tuple() for _, j in segs]) - A
    EA = np.array([edge_z[i] for i, _ in segs])
    EB = np.array([edge_z[j] for _, j in segs])
    SO = np.array([n.to_tuple() for n in seg_out])
    L2 = np.maximum((AB ** 2).sum(axis=1), 1e-9)

    def to_run(x, y):
        """The nearest sea-facing side: the distance to it, its height there, and whether (x, y) is
        in front of it."""
        P = np.array((x, y))
        u = np.clip(((P - A) * AB).sum(axis=1) / L2, 0.0, 1.0)
        Q = A + AB * u[:, None]
        d2 = ((Q - P) ** 2).sum(axis=1)
        i = int(np.argmin(d2))
        return math.sqrt(float(d2[i])), float(EA[i] + (EB[i] - EA[i]) * u[i]), float(((P - Q[i]) * SO[i]).sum()) > 0.0

    def depth(d, e):
        t = min(1.0, d / SHELF_W)
        return min(e, e + (SHELF_DEPTH - e) * (1.0 - (1.0 - t) ** 2))

    def wanted(x, y):
        if over_ground(x, y):
            return False
        d, _, front = to_run(x, y)
        return front and d <= SHELF_W + 1.0

    pts = list(xy)
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
        for i in range(len(keys)):
            q = xy[i] + normal[i] * s
            if not wanted(q.x, q.y) or crowded(q, r):
                continue
            pts.append(q)
            taken.setdefault((int(q.x // 8.0), int(q.y // 8.0)), []).append(q)
            rows += 1
    zs = list(edge_z) + [depth(*to_run(p.x, p.y)[:2]) for p in pts[len(keys):]]

    # Where two landforms touch, their sea-facing sides can cross; the triangulator puts a point
    # there, and it takes the shelf's height at it like any other.
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, segs, [], 0, 1e-4, True)
    zmap = []
    for k, p in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(pts)]
        zmap.append(zs[src[0]] if src else depth(*to_run(p.x, p.y)[:2]))
    faces = []
    for tri in out_f:
        c = Vector((sum(out_v[i].x for i in tri) / 3.0, sum(out_v[i].y for i in tri) / 3.0))
        longest = max((out_v[tri[k]] - out_v[tri[(k + 1) % 3]]).length for k in range(3))
        if longest > SHELF_LONGEST or not wanted(c.x, c.y):
            continue
        # Off other ground over the whole face, not only at its centre: each edge's middle, drawn
        # a quarter of the way in, so a side's own rim, which the face shares, is not asked.
        if any(over_ground(*(((out_v[tri[k]] + out_v[tri[(k + 1) % 3]]) * 0.5).lerp(c, 0.25))) for k in range(3)):
            continue
        faces.append(tuple(tri))
    shelf_report = {"faces": len(faces), "shore_m": round(sum((xy[i] - xy[j]).length for i, j in segs), 1),
                    "sides": len(segs), "row_points": rows, "sandy_shore_points": len(sandy),
                    "starting_under_the_cut": sum(1 for z in edge_z if z < cut_z - SNAP), "deepest": round(min(zmap), 2),
                    "shells": "; ".join(shells)}
    if dry or not faces:
        return {}, shelf_report, None

    coef, uv_err = uv_projection()
    tree = KDTree(len(keys))
    for i, k in enumerate(keys):
        tree.insert((k[0], k[1], 0.0), i)
    tree.balance()

    def colour(x, y, z):
        grain = 1.0 + math.sin(x * 0.37) * math.sin(-y * 0.41) * 0.05
        bed = Vector((SEABED[0] * grain, SEABED[1] * grain, SEABED[2] * grain, 1.0))
        if tree.find((x, y, 0.0))[1] not in sandy:
            return bed
        sand = Vector((SAND[0] * grain, SAND[1] * grain, SAND[2] * grain, 1.0))
        return sand.lerp(bed, 1.0 - smoothstep(SEABED_FROM[1], SEABED_FROM[0], z))

    me = build_ground(LANDFORM_SHELF, out_v, zmap, faces, colour, coef, edit,
                      "The landforms' shelf (Ground edit %d): the range's and city's landforms run on below the "
                      "waterline from each sea-facing side, %.1f m under the sea; the shells untouched; built by "
                      "tools/blender/world_terrain_ground_edit.py -- --edit landform_shelf, undone by its --undo" % (
                          edit, SHELF_UNDER))
    area = sum(p.area for p in me.polygons)
    shelf_report.update({"faces": len(me.polygons), "vertices": len(me.vertices), "area_ha": round(area / 10000.0, 1)})
    return {}, shelf_report, LANDFORM_SHELF


def zone_cells(edit, step):
    """The grid cells edit `edit` changed a corner of (by more than `MIN_CHANGE`), as (i, j) for
    the cell [i, i + 1] x [j, j + 1] in `step`s, with every hole filled and every place two cells
    meet only at a corner filled out, so the zone's edge is one simple loop."""
    ob = bpy.data.objects[GRID]
    me = ob.data
    M = ob.matrix_world
    co = coords(ob)
    ed = np.zeros(len(me.vertices), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", ed)
    pre = np.zeros(len(me.vertices))
    me.attributes["height_pre_edit"].data.foreach_get("value", pre)
    cells = set()
    for i in np.nonzero(ed == edit)[0]:
        w = M @ Vector(co[i])
        if abs(w.z - pre[i]) <= MIN_CHANGE:
            continue
        fx, fy = w.x / step, w.y / step
        if abs(fx - round(fx)) > 1e-6 or abs(fy - round(fy)) > 1e-6:
            raise SystemExit("the grid vertex at (%.3f, %.3f) is off its %.0f m lattice" % (w.x, w.y, step))
        for a in (0, -1):
            for b in (0, -1):
                cells.add((round(fx) + a, round(fy) + b))
    while True:
        grew = False
        for (i, j) in list(cells):
            for di, dj in ((1, 1), (1, -1)):
                if (i + di, j + dj) in cells and (i + di, j) not in cells and (i, j + dj) not in cells:
                    cells.add((i + di, j))
                    grew = True
        i0 = min(c[0] for c in cells) - 1
        i1 = max(c[0] for c in cells) + 1
        j0 = min(c[1] for c in cells) - 1
        j1 = max(c[1] for c in cells) + 1
        outside = set()
        todo = [(i0, j0)]
        while todo:
            c = todo.pop()
            if c in outside or c in cells or not (i0 <= c[0] <= i1 and j0 <= c[1] <= j1):
                continue
            outside.add(c)
            todo.extend(((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)))
        holes = {(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)} - cells - outside
        if holes:
            cells |= holes
            grew = True
        if not grew:
            return cells


def zone_loops(cells, step):
    """The zone's edge as loops of corner points, counter-clockwise, the zone on the left."""
    edges = {}
    for (i, j) in cells:
        for a, b in (((i, j), (i + 1, j)), ((i + 1, j), (i + 1, j + 1)), ((i + 1, j + 1), (i, j + 1)), ((i, j + 1), (i, j))):
            if (b, a) in edges:
                del edges[(b, a)]
            else:
                edges[(a, b)] = True
    nxt = {}
    for a, b in edges:
        if a in nxt:
            raise SystemExit("the zone's edge touches itself at (%d, %d)" % a)
        nxt[a] = b
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop = [start]
        p = nxt.pop(start)
        while p != start:
            loop.append(p)
            p = nxt.pop(p)
        n = len(loop)

        def turn(k):
            d0 = (loop[k][0] - loop[k - 1][0], loop[k][1] - loop[k - 1][1])
            d1 = (loop[(k + 1) % n][0] - loop[k][0], loop[(k + 1) % n][1] - loop[k][1])
            return d0 != d1

        loops.append([Vector((c[0] * step, c[1] * step)) for k, c in enumerate(loop) if turn(k)])
    return loops


class Zone:
    """Edit 1's zone: its cells, its edge as straight runs, and where a point lies against them."""

    def __init__(self, cells, step):
        self.cells = cells
        self.step = step
        # One loop per separate piece of the zone; the holes are filled.
        self.loops = zone_loops(cells, step)
        self.runs = []
        self.by_line = {}
        self.perimeters = []
        self.first_run = []
        for li, corners in enumerate(self.loops):
            s = 0.0
            self.first_run.append(len(self.runs))
            for k in range(len(corners)):
                # In Python's doubles, not mathutils' single floats: along a run, distance is
                # exact, so a corner is the same point seen from either side.
                a, b = corners[k], corners[(k + 1) % len(corners)]
                ax, ay, bx, by = float(a.x), float(a.y), float(b.x), float(b.y)
                dx, dy = (bx > ax) - (bx < ax), (by > ay) - (by < ay)
                length = abs(bx - ax) + abs(by - ay)
                run = {"loop": li, "a": a, "b": b, "ax": ax, "ay": ay, "dx": dx, "dy": dy, "len": length, "s0": s,
                       "horizontal": dy == 0, "inside": Vector((-dy, dx))}
                self.runs.append(run)
                key = ("y", round(ay / step)) if run["horizontal"] else ("x", round(ax / step))
                self.by_line.setdefault(key, []).append(len(self.runs) - 1)
                s += length
            self.perimeters.append(s)
        xs = [c.x for loop in self.loops for c in loop]
        ys = [c.y for loop in self.loops for c in loop]
        self.box = (min(xs), max(xs), min(ys), max(ys))

    def next_run(self, ri):
        """The run after `ri` round its loop."""
        li = self.runs[ri]["loop"]
        nxt = ri + 1
        if nxt == len(self.runs) or self.runs[nxt]["loop"] != li:
            nxt = self.first_run[li]
        return nxt

    def inside(self, x, y):
        return (math.floor(x / self.step), math.floor(y / self.step)) in self.cells

    def on_edge(self, x, y, tol=1e-4):
        """The runs (index, distance along) that (x, y) lies on."""
        out = []
        for axis, c, along in (("y", y, x), ("x", x, y)):
            k = round(c / self.step)
            if abs(c - k * self.step) > tol:
                continue
            for ri in self.by_line.get((axis, k), ()):
                r = self.runs[ri]
                u = (x - r["ax"]) * r["dx"] + (y - r["ay"]) * r["dy"]
                if -tol <= u <= r["len"] + tol:
                    out.append((ri, min(max(u, 0.0), r["len"])))
        return out

    def edge_distance(self, x, y, within=math.inf):
        """The distance from (x, y) to the zone's edge, looked for only `within` that of it."""
        best = math.inf
        span = self.step if within == math.inf else within
        for axis, c in (("y", y), ("x", x)):
            k0 = math.floor((c - span) / self.step)
            k1 = math.ceil((c + span) / self.step)
            rng = range(k0, k1 + 1) if within != math.inf else None
            keys = [(axis, k) for k in rng] if rng is not None else [key for key in self.by_line if key[0] == axis]
            for key in keys:
                for ri in self.by_line.get(key, ()):
                    best = min(best, self.run_distance(ri, x, y))
        return best

    def run_distance(self, ri, x, y):
        r = self.runs[ri]
        px, py = x - r["ax"], y - r["ay"]
        u = min(max(px * r["dx"] + py * r["dy"], 0.0), r["len"])
        return math.hypot(px - r["dx"] * u, py - r["dy"] * u)

    def nearest_run(self, x, y):
        return min(range(len(self.runs)), key=lambda ri: self.run_distance(ri, x, y))

    def face_inside(self, f):
        """Whether a face cut along the zone's edge lies in the zone: tested at its centre, or
        halfway from it to a corner when the centre sits on the edge."""
        c = f.calc_center_median()
        for q in [c] + [c.lerp(v.co, 0.5) for v in f.verts]:
            if not self.on_edge(q.x, q.y, 1e-5):
                return self.inside(q.x, q.y)
        raise SystemExit("a face at (%.2f, %.2f) lies along the zone's edge: %s, area %.6f" % (
            c.x, c.y, [tuple(round(x, 4) for x in v.co) for v in f.verts], f.calc_area()))


def as_exported(bm, me, indices):
    """Rebuild the faces `indices` as the triangles the exporter draws (Blender's own loop
    triangles), so a non-planar face can be cut without its surface moving."""
    me.calc_loop_triangles()
    tris = {}
    for lt in me.loop_triangles:
        if lt.polygon_index in indices:
            tris.setdefault(lt.polygon_index, []).append(tuple(lt.vertices))
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    held = [(bm.faces[pi], [[bm.verts[i] for i in t] for t in ts]) for pi, ts in tris.items()]
    gone = []
    for f, ts in held:
        if len(f.verts) == 3:
            continue
        for t in ts:
            nf = bm.faces.new(t)
            nf.material_index = f.material_index
            nf.smooth = f.smooth
        gone.append(f)
    bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')


def all_hits(tree, x, y):
    out = []
    z = 5000.0
    while True:
        hit = tree.ray_cast(Vector((x, y, z)), Vector((0.0, 0.0, -1.0)))
        if hit[0] is None:
            return out
        out.append(hit[0].z)
        z = hit[0].z - 1e-4


def range_band(z):
    for top, name in TOE_BANDS:
        if z < top:
            return name
    return TOE_BANDS[-1][1]


def range_blend(edit, now_t, pre_t, dry):
    """Edit 1 on the landforms it lands on: one sheet in the zone it changed, the shells cut along
    that zone's edge, emptied inside it and capped (see `RANGE_BLEND`)."""
    name = RANGE_BLEND[edit]
    if name in bpy.data.objects:
        raise SystemExit("%s already exists" % name)
    script = "world_terrain_edit_blend_south_range.py"
    step = float(edit_constant(script, "STEP"))
    sea = float(edit_constant(script, "SEA_LEVEL"))
    zone = Zone(zone_cells(edit, step), step)
    zb = zone.box
    print("  zone: %d cells, %.1f ha, %d runs, x %.0f..%.0f, y %.0f..%.0f" % (
        len(zone.cells), len(zone.cells) * step * step / 10000.0, len(zone.runs), *zb))

    def near(ob, margin):
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        return not (max(b.x for b in bb) < zb[0] - margin or min(b.x for b in bb) > zb[1] + margin or
                    max(b.y for b in bb) < zb[2] - margin or min(b.y for b in bb) > zb[3] + margin)

    shells = []
    decor = []
    for ob in ground_objects():
        if not near(ob, 1.0):
            continue
        if ob.matrix_world != ob.matrix_world.Identity(4):
            raise SystemExit("%s is not at the origin; Ground objects hold world positions" % ob.name)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        closed = not any(e.is_boundary for e in bm.edges)
        bm.free()
        if ob.get("kyt_collision") == "none":
            decor.append(ob)
        elif closed:
            shells.append(ob)
        else:
            raise SystemExit("%s is open and collides; edit 1 knows only closed shells" % ob.name)
    print("  shells: %s; decoration: %s" % (", ".join(o.name for o in shells), ", ".join(o.name for o in decor) or "none"))

    # The ground as it stands, before anything is cut: its top, and whose face that is.
    before = {}
    for ob in shells:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mats = [ob.data.materials[f.material_index].name for f in bm.faces]
        before[ob.name] = (BVHTree.FromBMesh(bm), mats)
        bm.free()

    def top_before(x, y):
        best = None
        for oname, (tree, mats) in before.items():
            hit = tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
            if hit[0] is not None and (best is None or hit[0].z > best[0]):
                best = (hit[0].z, mats[hit[2]])
        return best

    # How far the edit cut the grid and how far it raised it, each a surface of its own. The fade
    # reads their sum, not the change itself, which where a cut row meets a raised row (the wall
    # at z 5500, cut 80 m above and raised 75 m below) passes through nothing halfway and would
    # fade the edit out along that line, wall and all. And the ground is cut only where the edit
    # cut, raised only where it raised, beyond `AGAINST`: by the coastal branch's end the grid
    # sampled the hill either side of the road's cutting, 35 m over its floor, and the design,
    # 2 m under the grid there, would otherwise fill the cutting.
    gob = bpy.data.objects[GRID]
    gco = [gob.matrix_world @ Vector(v) for v in coords(gob)]
    ged = np.zeros(len(gco), dtype=np.int32)
    gob.data.attributes["authored_edit"].data.foreach_get("value", ged)
    gpre = np.zeros(len(gco))
    gob.data.attributes["height_pre_edit"].data.foreach_get("value", gpre)
    gpolys = [tuple(p.vertices) for p in gob.data.polygons]
    gcut = [max(0.0, gpre[i] - v.z) if ged[i] == edit else 0.0 for i, v in enumerate(gco)]
    graised = [max(0.0, v.z - gpre[i]) if ged[i] == edit else 0.0 for i, v in enumerate(gco)]

    def field(values):
        return BVHTree.FromPolygons([Vector((v.x, v.y, values[i])) for i, v in enumerate(gco)], gpolys)

    cut_t, raised_t = field(gcut), field(graised)

    def moved(x, y):
        return height(cut_t, x, y), height(raised_t, x, y)

    # Edit 1 held the coastal branch's road box fixed (its `NO_RAISE`, Godot x0, x1, z0, z1) so
    # the blend worked round the road. A cell beyond it the grid still moved a little, over ground
    # the grid never saw (the road's cutting and the hill beside it, up to 35 m under the grid),
    # so there the ground comes down with the design and does not rise at all.
    nr = edit_constant(script, "NO_RAISE")
    held = (nr[0] - step, nr[1] + step, -nr[3] - step, -nr[2] + step)

    def target(x, y):
        """Where edit 1 puts the ground at (x, y): the ground as it stands where the edit left the
        grid alone, its designed surface where it moved the grid by `BLEND` or more, faded
        between. The design wins outright, as in `designed`, except against the edit's own
        direction, where `AGAINST` holds (see `cut_t`). Where the game had open sea, the ground
        as it stands is the grid's sea floor, kept a metre under the water: in a cell between
        sea and a cliff the grid rises straight across it, and that is no land anyone designed."""
        t = height(now_t, x, y)
        p = height(pre_t, x, y)
        top = top_before(x, y)
        base = top[0] if top is not None else min(p, sea - 1.0)
        cut, raised = moved(x, y)
        if cut + raised <= MIN_CHANGE:
            return base
        change = t - base
        if change < 0.0 and cut <= MIN_CHANGE:
            change = max(change, -AGAINST)
        elif change > 0.0 and held[0] <= x <= held[1] and held[2] <= y <= held[3]:
            change = 0.0
        elif change > 0.0 and raised <= MIN_CHANGE:
            change = min(change, AGAINST)
        # Faded by distance from the zone's edge as well: there the grid, a straight line between
        # two of its samples, stands off the shells' own surface, and faded over `BLEND` alone the
        # sheet stepped from the one to the other within a metre, a saw along the edge's stair.
        edge = smoothstep(0.0, EDGE_FADE, zone.edge_distance(x, y, EDGE_FADE))
        return base + min(1.0, (cut + raised) / BLEND) * edge * change

    # Each shell cut along the zone's edge: the faces near the zone first rebuilt as the
    # triangles the game draws, then split along every run.
    work = {}
    for ob in shells + decor:
        me = ob.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        fa = bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
        bm.faces.ensure_lookup_table()

        def overlaps(f, margin=1.0):
            xs = [v.co.x for v in f.verts]
            ys = [v.co.y for v in f.verts]
            return not (max(xs) < zb[0] - margin or min(xs) > zb[1] + margin or max(ys) < zb[2] - margin or min(ys) > zb[3] + margin)

        near_faces = {f.index for f in bm.faces if overlaps(f)}
        ring = {g.index for i in near_faces for v in bm.faces[i].verts for g in v.link_faces}
        as_exported(bm, me, near_faces | ring)
        kept_ngons = {f: len(f.verts) for f in bm.faces if len(f.verts) > 3}
        for r in zone.runs:
            if r["horizontal"]:
                c, lo, hi = r["a"].y, min(r["a"].x, r["b"].x), max(r["a"].x, r["b"].x)
            else:
                c, lo, hi = r["a"].x, min(r["a"].y, r["b"].y), max(r["a"].y, r["b"].y)
            cand = []
            for f in bm.faces:
                if r["horizontal"]:
                    across = [v.co.y for v in f.verts]
                    along = [v.co.x for v in f.verts]
                else:
                    across = [v.co.x for v in f.verts]
                    along = [v.co.y for v in f.verts]
                if min(across) < c - 1e-6 and max(across) > c + 1e-6 and max(along) > lo - 1e-6 and min(along) < hi + 1e-6:
                    cand.append(f)
            if not cand:
                continue
            geom = set(cand)
            for f in cand:
                geom.update(f.edges)
                geom.update(f.verts)
            no = Vector((0.0, 1.0, 0.0)) if r["horizontal"] else Vector((1.0, 0.0, 0.0))
            co = Vector((0.0, c, 0.0)) if r["horizontal"] else Vector((c, 0.0, 0.0))
            # A vertex within 0.1 mm of the line counts as on it; each cut's vertices go onto the
            # line exactly (the cut leaves them up to 3e-5 off; the lines are whole metres), so the
            # next cut finds them there and both rims of a corner agree to the bit.
            cut = bmesh.ops.bisect_plane(bm, geom=list(geom), dist=1e-4, plane_co=co, plane_no=no)
            for v in cut["geom_cut"]:
                if isinstance(v, bmesh.types.BMVert):
                    if r["horizontal"]:
                        v.co.y = c
                    else:
                        v.co.x = c
        degenerate = [f for f in bm.faces if f.calc_area() < 1e-8]
        if degenerate:
            c = degenerate[0].calc_center_median()
            raise SystemExit("%s: the cut left %d faces of no area, the first at (%.3f, %.3f)" % (ob.name, len(degenerate), c.x, c.y))
        for f, n in kept_ngons.items():
            if not f.is_valid or len(f.verts) != n:
                raise SystemExit("%s: a face away from the zone was cut; widen the ring rebuilt first" % ob.name)
        pieces = [f for f in bm.faces if len(f.verts) > 3 and f not in kept_ngons]
        if pieces:
            bmesh.ops.triangulate(bm, faces=pieces)
        gone = [f for f in bm.faces if overlaps(f, 0.0) and zone.face_inside(f)]
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        work[ob.name] = {"bm": bm, "fa": fa, "deleted": len(gone), "faces_before": len(me.polygons)}

    # The rim each shell is left with lies on the zone's edge; along each run, the topmost rim
    # is the ground the sheet meets.
    rims = {}
    for ob in shells:
        bm = work[ob.name]["bm"]
        rim = []
        for e in bm.edges:
            if not e.is_boundary:
                continue
            a, b = e.verts
            ra = {ri for ri, _ in zone.on_edge(a.co.x, a.co.y)}
            rb = {ri for ri, _ in zone.on_edge(b.co.x, b.co.y)}
            if not (ra & rb):
                raise SystemExit("%s: an open edge at (%.2f, %.2f) is off the zone's edge" % (ob.name, a.co.x, a.co.y))
            rim.append(e)
        rims[ob.name] = rim
    splits = {ob.name: {} for ob in shells}
    boundary = {}
    corner_ends = []
    jumps = 0
    for ri, r in enumerate(zone.runs):
        segs = []
        for ob in shells:
            for e in rims[ob.name]:
                a, b = e.verts
                on_a = {k: u for k, u in zone.on_edge(a.co.x, a.co.y)}
                on_b = {k: u for k, u in zone.on_edge(b.co.x, b.co.y)}
                if ri in on_a and ri in on_b:
                    segs.append((on_a[ri], a.co.z, on_b[ri], b.co.z, ob.name, e, a, b))
        flat = [s for s in segs if abs(s[2] - s[0]) > 1e-6]

        def z_on(s, u):
            return s[1] + (u - s[0]) / (s[2] - s[0]) * (s[3] - s[1])

        def point(u):
            return r["ax"] + r["dx"] * u, r["ay"] + r["dy"] * u

        cuts = {0.0, r["len"]}
        for s in segs:
            cuts.update((min(max(s[0], 0.0), r["len"]), min(max(s[2], 0.0), r["len"])))
        for i in range(len(flat)):
            for j in range(i + 1, len(flat)):
                s, t = flat[i], flat[j]
                lo = max(min(s[0], s[2]), min(t[0], t[2]))
                hi = min(max(s[0], s[2]), max(t[0], t[2]))
                if hi - lo <= 1e-6:
                    continue
                f0 = z_on(s, lo) - z_on(t, lo)
                f1 = z_on(s, hi) - z_on(t, hi)
                if f0 * f1 < 0.0:
                    cuts.add(lo + (hi - lo) * f0 / (f0 - f1))
        cuts = sorted(cuts)
        pieces = []
        for u0, u1 in zip(cuts, cuts[1:]):
            if u1 - u0 <= 1e-6:
                continue
            mid = 0.5 * (u0 + u1)
            cover = [s for s in flat if min(s[0], s[2]) < mid < max(s[0], s[2])]
            owner = max(cover, key=lambda s: z_on(s, mid)) if cover else None
            if pieces and pieces[-1][2] is owner:
                pieces[-1][1] = u1
            else:
                pieces.append([u0, u1, owner])

        def piece_z(p, u):
            if p[2] is None:
                # Open sea along the edge: the edit left the grid alone here, so `target` there.
                return target(*point(u))
            return z_on(p[2], u)

        def vertex_at(p, u):
            s = p[2] if p is not None else None
            if s is None:
                return None
            if abs(u - s[0]) <= 1e-6:
                return s[6]
            if abs(u - s[2]) <= 1e-6:
                return s[7]
            return None

        def edge_point(p, q, u, z):
            """The sheet's edge point at u, where piece p ends and piece q begins (either may be
            None): an owner's own vertex there, or a new point split into the owners' edges. Its
            position is the shell's own, to the last bit, so the two rims are one edge."""
            own = next((v for v in (vertex_at(p, u), vertex_at(q, u)) if v is not None), None)
            if own is not None:
                at = own.co.copy()
            else:
                x, y = point(u)
                at = Vector((x, y, z))
            for piece in (p, q):
                if piece is not None and piece[2] is not None and vertex_at(piece, u) is None:
                    splits[piece[2][4]].setdefault(piece[2][5], []).append(at)
            return at

        # A piece of the edge shorter than this is bridged, not followed: the sheet's edge spans
        # it, and what it leaves is a hairline, narrower than anything to see through.
        pieces = [p for k, p in enumerate(pieces) if p[1] - p[0] >= 4.0 * JUMP or k in (0, len(pieces) - 1)]
        run_pts = []
        for k, p in enumerate(pieces):
            u0, u1 = p[0], p[1]
            if k == 0:
                run_pts.append(edge_point(None, p, u0, piece_z(p, u0)))
            if p[2] is None:
                n = int(math.ceil((u1 - u0) / RANGE_LATTICE))
                for m in range(1, n):
                    u = u0 + (u1 - u0) * m / n
                    run_pts.append(Vector((*point(u), piece_z(p, u))))
            if k + 1 < len(pieces):
                q = pieces[k + 1]
                v0 = q[0]
                zl, zr = piece_z(p, u1), piece_z(q, v0)
                if v0 - u1 <= 1e-6 and abs(zl - zr) <= 1e-4:
                    run_pts.append(edge_point(p, q, u1, zl))
                else:
                    # A step: the ground drops down a shell's side here. The sheet cannot stand
                    # straight, so it takes the step over a hair of its edge, `JUMP` either side.
                    dl = min(JUMP, 0.25 * (u1 - u0))
                    dr = min(JUMP, 0.25 * (q[1] - v0))
                    run_pts.append(edge_point(p, None, u1 - dl, piece_z(p, u1 - dl)))
                    run_pts.append(edge_point(None, q, v0 + dr, piece_z(q, v0 + dr)))
                    jumps += 1
            else:
                run_pts.append(edge_point(p, None, u1, piece_z(p, u1)))
        # Each run ends at the corner the next begins at.
        corner_ends.append((run_pts[0], run_pts[-1], pieces[0][2][4] if pieces[0][2] else None,
                            pieces[-1][2][4] if pieces[-1][2] else None,
                            [(round(s[0], 4), round(s[1], 4), round(s[2], 4), round(s[3], 4), s[4]) for s in segs
                             if min(s[0], s[2]) < 0.05 or max(s[0], s[2]) > r["len"] - 0.05]))
        boundary.setdefault(r["loop"], []).extend(run_pts[:-1])
    for k in range(len(corner_ends)):
        end = corner_ends[k][1]
        start = corner_ends[zone.next_run(k)][0]
        if (end - start).length > 1e-3:
            raise SystemExit("the ground at the zone's corner (%.2f, %.2f) is %.3f m apart along its two sides: %s %s / %s %s\n%s\n%s" % (
                end.x, end.y, (end - start).length, tuple(end), corner_ends[k][3], tuple(start), corner_ends[zone.next_run(k)][2],
                corner_ends[k][4], corner_ends[zone.next_run(k)][4]))

    # Split the topmost rims where the sheet's edge turns, so every edge of the sheet's rim is an
    # edge of a shell.
    split_count = 0
    for oname, by_edge in splits.items():
        for e, ps in by_edge.items():
            v_from, v_to = e.verts
            ps = sorted(ps, key=lambda p: (p - v_from.co).length)
            ps = [p for k, p in enumerate(ps) if k == 0 or (p - ps[k - 1]).length > 1e-6]
            cur = e
            for p in ps:
                span = (v_to.co - v_from.co).length
                t = (p - v_from.co).length / span
                _, nv = bmesh.utils.edge_split(cur, v_from, t)
                nv.co = p
                cur = next(g for g in nv.link_edges if v_to in g.verts)
                v_from = nv
                split_count += 1
    for oname in splits:
        bm = work[oname]["bm"]
        quads = [f for f in bm.faces if len(f.verts) > 3 and any(zone.on_edge(v.co.x, v.co.y) for v in f.verts)]
        if quads:
            bmesh.ops.triangulate(bm, faces=quads)

    # Caps: each shell closed again along its cut, flat on the zone's edge, facing into the zone.
    caps = {}
    for ob in shells:
        bm = work[ob.name]["bm"]
        fa = work[ob.name]["fa"]
        me = ob.data
        walls = [p.material_index for p in me.polygons if abs(p.normal.z) <= 0.05]
        wall_mat = max(set(walls), key=walls.count) if walls else 0
        rim = [e for e in bm.edges if e.is_boundary]
        link = {}
        for e in rim:
            for v in e.verts:
                link.setdefault(v, []).append(e)
        if any(len(es) != 2 for es in link.values()):
            raise SystemExit("%s: its cut rim branches" % ob.name)
        seen = set()
        made = 0
        for e0 in rim:
            if e0 in seen:
                continue
            loop = [e0.verts[0]]
            e = e0
            v = e0.verts[1]
            seen.add(e0)
            while v is not loop[0]:
                loop.append(v)
                e = next(g for g in link[v] if g is not e)
                seen.add(e)
                v = e.other_vert(v)

            def s_of(v):
                ri, u = zone.on_edge(v.co.x, v.co.y)[0]
                return zone.runs[ri]["loop"], zone.runs[ri]["s0"] + u

            li = s_of(loop[0])[0]
            if any(s_of(v)[0] != li for v in loop):
                raise SystemExit("%s: one rim of its cut lies on two pieces of the zone" % ob.name)
            per = zone.perimeters[li]
            s = [s_of(loop[0])[1]]
            for v in loop[1:] + loop[:1]:
                d = s_of(v)[1] - s[-1] % per
                d = (d + 0.5 * per) % per - 0.5 * per
                s.append(s[-1] + d)
            if abs(s.pop() - s[0]) > 1e-3:
                raise SystemExit("%s: its cut runs right round a piece of the zone" % ob.name)
            pts = [Vector((s[k], loop[k].co.z)) for k in range(len(loop))]
            area = sum(pts[k].x * pts[(k + 1) % len(pts)].y - pts[(k + 1) % len(pts)].x * pts[k].y for k in range(len(pts)))
            order = list(range(len(loop))) if area > 0.0 else list(reversed(range(len(loop))))
            # Across a corner of the zone the cap must fold, not cut the corner: a constraint up
            # each corner the rim passes.
            cons = []
            lo, hi = min(s), max(s)
            for r in zone.runs:
                if r["loop"] != li:
                    continue
                for k in range(int(math.floor((lo - r["s0"]) / per)), int(math.ceil((hi - r["s0"]) / per)) + 1):
                    sc = r["s0"] + k * per
                    at = sorted((i for i in range(len(loop)) if abs(s[i] - sc) < 1e-4), key=lambda i: pts[i].y)
                    for i, j in zip(at, at[1:]):
                        m = Vector((sc, 0.5 * (pts[i].y + pts[j].y)))
                        inside = False
                        for k2 in range(len(pts)):
                            p0, p1 = pts[k2], pts[(k2 + 1) % len(pts)]
                            if (p0.y > m.y) != (p1.y > m.y) and m.x < p0.x + (m.y - p0.y) * (p1.x - p0.x) / (p1.y - p0.y):
                                inside = not inside
                        if inside:
                            cons.append((i, j))
            out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, cons, [order], 1, 1e-6, True)
            idx = []
            for k, ov in enumerate(orig_v):
                src = [i for i in ov if i < len(loop)]
                if not src:
                    raise SystemExit("%s: its cap needed a point the rim does not have, at s %.2f z %.2f" % (ob.name, out_v[k].x, out_v[k].y))
                idx.append(src[0])
            for tri in out_f:
                vs = [loop[idx[i]] for i in tri]
                if len(set(vs)) < 3:
                    continue
                nf = bm.faces.new(vs)
                nf.material_index = wall_mat
                nf.smooth = False
                nf[fa] = edit
                nf.normal_update()
                c = nf.calc_center_median()
                inward = zone.runs[zone.nearest_run(c.x, c.y)]["inside"]
                if nf.normal.x * inward.x + nf.normal.y * inward.y < 0.0:
                    nf.normal_flip()
                made += 1
        caps[ob.name] = made
        if any(e.is_boundary for e in bm.edges):
            raise SystemExit("%s is still open after its caps" % ob.name)
        if any(len(e.link_faces) > 2 for e in bm.edges):
            raise SystemExit("%s: an edge with more than two faces after its caps" % ob.name)

    # The sheet: its edge as found, the grid's own vertices and a lattice inside, and where the
    # edit faded in or left the ground alone, the shells' own top vertices. By the road box the
    # ground keeps the shape the grid never saw (the road's cutting), so there the sheet takes
    # every top vertex of the shells and a `HELD_LATTICE` lattice, and its triangles do not
    # bridge the cutting.
    pts = []
    zs = []
    rings = []
    for li in sorted(boundary):
        rings.append(list(range(len(pts), len(pts) + len(boundary[li]))))
        pts.extend(Vector((p.x, p.y)) for p in boundary[li])
        zs.extend(p.z for p in boundary[li])
    nb = len(pts)
    crowd = 0.35 * RANGE_LATTICE
    taken = {}

    def in_held(q):
        return held[0] <= q.x <= held[1] and held[2] <= q.y <= held[3]

    def crowded(q):
        near = 0.35 * HELD_LATTICE if in_held(q) else crowd
        cx, cy = int(q.x // crowd), int(q.y // crowd)
        return any((q - o).length < near for i in (-1, 0, 1) for j in (-1, 0, 1) for o in taken.get((cx + i, cy + j), ()))

    def take(q):
        taken.setdefault((int(q.x // crowd), int(q.y // crowd)), []).append(q)

    for q in pts:
        take(q)
    # The grid's vertices and the lattice stand `OFF_LINE` off the grid's lines: the foothills
    # were drawn on the same 25 m lattice, so their old wall stands on a grid row, and on it the
    # ground as it stands is the plateau's edge and the base at once.
    cand = []
    for oname, (tree, mats) in before.items():
        for v in bpy.data.objects[oname].data.vertices:
            q = Vector((v.co.x, v.co.y))
            top = top_before(q.x, q.y)
            if top is not None and abs(top[0] - v.co.z) < 1e-3 and (in_held(q) or sum(moved(q.x, q.y)) < BLEND):
                cand.append(q)
    # Rows a little inside the edge, so the fade there is drawn, not spanned by long fans.
    for r in zone.runs:
        n = int(math.ceil(r["len"] / EDGE_ROW))
        for inset in (EDGE_FADE / 3.0, 2.0 * EDGE_FADE / 3.0):
            for k in range(n):
                u = (k + 0.5) * r["len"] / n
                cand.append(Vector((r["ax"] + r["dx"] * u - r["dy"] * inset, r["ay"] + r["dy"] * u + r["dx"] * inset)))
    x = math.floor(held[0] / HELD_LATTICE) * HELD_LATTICE
    while x <= held[1]:
        y = math.floor(held[2] / HELD_LATTICE) * HELD_LATTICE
        while y <= held[3]:
            cand.append(Vector((x + OFF_LINE, y + OFF_LINE)))
            y += HELD_LATTICE
        x += HELD_LATTICE
    cand.extend(Vector((v.x + OFF_LINE, v.y + OFF_LINE)) for v in gco)
    x = math.floor(zb[0] / RANGE_LATTICE) * RANGE_LATTICE
    while x <= zb[1]:
        y = math.floor(zb[2] / RANGE_LATTICE) * RANGE_LATTICE
        while y <= zb[3]:
            cand.append(Vector((x + OFF_LINE, y + OFF_LINE)))
            y += RANGE_LATTICE
        x += RANGE_LATTICE
    for q in cand:
        if not (zb[0] < q.x < zb[1] and zb[2] < q.y < zb[3]) or not zone.inside(q.x, q.y):
            continue
        clear = 0.3 * (HELD_LATTICE if in_held(q) else RANGE_LATTICE)
        if zone.edge_distance(q.x, q.y, clear) < clear or crowded(q):
            continue
        take(q)
        pts.append(q)
        zs.append(target(q.x, q.y))
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, [], rings, 1, 1e-5, True)
    zmap = []
    for k, ov in enumerate(orig_v):
        src = [i for i in ov if i < len(pts)]
        if not src:
            raise SystemExit("the sheet's triangulation added a point at (%.2f, %.2f)" % (out_v[k].x, out_v[k].y))
        zmap.append(zs[src[0]])
    merged = sum(1 for ov in orig_v if len([i for i in ov if i < len(pts)]) > 1)
    if merged:
        raise SystemExit("the sheet's triangulation merged %d of its points" % merged)

    report = {}
    for oname, w in work.items():
        report[oname] = {"faces_before": w["faces_before"], "faces_in_zone_removed": w["deleted"],
                         "cap_faces": caps.get(oname, 0)}
    sheet = {"zone_ha": round(len(zone.cells) * step * step / 10000.0, 1), "edge_points": nb, "rim_splits": split_count,
             "steps_along_edge": jumps, "faces": len(out_f)}
    if dry:
        for w in work.values():
            w["bm"].free()
        return report, sheet, None

    # The shells as they were, whole, for the undo.
    hist = history_collection()
    for ob in shells + decor:
        hme = ob.data.copy()
        hme.name = "%s__before_edit%d" % (ob.name, edit)
        hob = bpy.data.objects.new(hme.name, hme)
        hob["kyt_whole"] = 1
        hob["kyt_note"] = "%s whole as it stood before Ground edit %d, for its --undo; never exported" % (ob.name, edit)
        hist.objects.link(hob)
    old_tris = {}
    for ob in shells + decor:
        me = ob.data
        me.calc_loop_triangles()
        old_tris[ob.name] = [tuple(tuple(me.vertices[i].co) for i in lt.vertices) for lt in me.loop_triangles]
        bm = work[ob.name]["bm"]
        bm.to_mesh(me)
        bm.free()
        me.update()

    # The sheet's faces take the colour of the ground the edit found under them: the range's
    # level bands again at their new height; where the edit made land out of the sea, the
    # range's cove sand under `SAND_BELOW`, its bands above.
    mats = []
    faces = []
    findex = []
    verts = [(p.x, p.y, zmap[k]) for k, p in enumerate(out_v)]
    for tri in out_f:
        a, b, c = (Vector(verts[i]) for i in tri)
        if (b - a).cross(c - a).z < 0.0:
            tri = [tri[0], tri[2], tri[1]]
        m = (a + b + c) / 3.0
        top = top_before(m.x, m.y)
        if top is None:
            mat = "distant_range_cove_sand" if m.z < SAND_BELOW else range_band(m.z)
        elif top[1] in (band for _, band in TOE_BANDS):
            mat = range_band(m.z)
        else:
            mat = top[1]
        if mat not in mats:
            mats.append(mat)
        faces.append(tuple(tri))
        findex.append(mats.index(mat))
    sheet_me = bpy.data.meshes.new(name)
    sheet_me.from_pydata(verts, [], faces)
    sheet_me.validate()
    for mat in mats:
        sheet_me.materials.append(bpy.data.materials[mat])
    sheet_me.polygons.foreach_set("material_index", findex)
    sheet_me.polygons.foreach_set("use_smooth", [True] * len(sheet_me.polygons))
    fa = sheet_me.attributes.new("authored_edit", 'INT', 'FACE')
    fa.data.foreach_set("value", [edit] * len(sheet_me.polygons))
    sob = bpy.data.objects.new(name, sheet_me)
    sob["kyt_note"] = ("Ground edit %d, the south range blend: one sheet where the grid edit changed the range's and "
                       "city's landforms, which are cut along its edge and capped; built by "
                       "tools/blender/world_terrain_ground_edit.py -- --edit %d, undone by its --undo" % (edit, edit))
    bpy.data.collections[GROUND].objects.link(sob)
    sheet_me.update()

    # Proof. Outside the zone every shell's surface is where it was: each triangle the cut did
    # not touch is still there exactly, and on every one it touched (rebuilt or split), points
    # sampled off the zone's edge lie on the other surface, the old on the new and the new on
    # the old.
    worst_outside = 0.0
    worst_at = None
    kept_exactly = 0
    for ob in shells + decor:
        me = ob.data
        me.calc_loop_triangles()
        new = [tuple(tuple(me.vertices[i].co) for i in lt.vertices) for lt in me.loop_triangles]
        bm = bmesh.new()
        bm.from_mesh(me)
        new_tree = BVHTree.FromBMesh(bm)
        bm.free()
        old = old_tris[ob.name]
        old_tree = BVHTree.FromPolygons([Vector(c) for t in old for c in t], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(old))])
        old_keys = {tuple(sorted(t)) for t in old}
        new_keys = {tuple(sorted(t)) for t in new}
        kept_exactly += len(old_keys & new_keys)
        for side, tris, other, theirs in (("old", old, new_tree, new_keys), ("new", new, old_tree, old_keys)):
            for t in tris:
                if tuple(sorted(t)) in theirs:
                    continue
                A, B, C = (Vector(c) for c in t)
                if (B - A).cross(C - A).length < 1e-6:
                    continue
                for bary in ((1 / 3, 1 / 3, 1 / 3), (0.8, 0.1, 0.1), (0.1, 0.8, 0.1), (0.1, 0.1, 0.8), (0.45, 0.45, 0.1), (0.1, 0.45, 0.45), (0.45, 0.1, 0.45)):
                    q = A * bary[0] + B * bary[1] + C * bary[2]
                    if zone.inside(q.x, q.y) or zone.edge_distance(q.x, q.y, 0.01) < 0.01:
                        continue
                    # How far the point is from the other surface: straight down, or in 3D for a
                    # shell's straight sides, which a ray from above never meets. Either near
                    # enough will do: the nearest-point search is a few centimetres out on the
                    # range's long sliver faces, and the ray slips through the crease of a side.
                    down = min((abs(h - q.z) for h in all_hits(other, q.x, q.y)), default=math.inf)
                    off = min(down, (other.find_nearest(q)[0] - q).length)
                    if off > worst_outside:
                        worst_outside = off
                        worst_at = (ob.name, side, tuple(round(c, 3) for c in q), [tuple(round(x, 3) for x in c) for c in t])
    if worst_outside > 0.01:
        raise SystemExit("a shell's surface outside the zone moved by %.4f m: %s" % (worst_outside, worst_at))

    # The sheet's rim is the shells' cut, edge for edge, wherever it stands clear of the water.
    keys = set()
    for ob in shells:
        for e in ob.data.edges:
            a, b = (tuple(round(c, 4) for c in ob.data.vertices[i].co) for i in e.vertices)
            keys.add((min(a, b), max(a, b)))
    bm = bmesh.new()
    bm.from_mesh(sheet_me)
    open_above = 0
    open_at = []
    vkeys = {k for pair in keys for k in pair}
    for e in bm.edges:
        if not e.is_boundary:
            continue
        a, b = e.verts
        if max(a.co.z, b.co.z) < sea + 1.0 or (a.co.xy - b.co.xy).length < 0.3:
            continue
        ka, kb = tuple(round(c, 4) for c in a.co), tuple(round(c, 4) for c in b.co)
        if (min(ka, kb), max(ka, kb)) not in keys:
            open_above += 1
            if len(open_at) < 6:
                open_at.append((ka, ka in vkeys, kb, kb in vkeys))
    sheet_tree = BVHTree.FromBMesh(bm)
    bm.free()
    if open_above:
        raise SystemExit("%s: %d edges of its rim above the water meet no shell: %s" % (name, open_above, open_at))

    # Inside the zone the sheet is the ground, at the edit's surface.
    after = []
    for ob in shells:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        after.append(BVHTree.FromBMesh(bm))
        bm.free()
    errs = []
    poke = 0
    dry_new = 0.0
    sample = 5.0
    x = math.floor(zb[0] / sample) * sample + 0.5 * sample
    while x < zb[1]:
        y = math.floor(zb[2] / sample) * sample + 0.5 * sample
        while y < zb[3]:
            if zone.inside(x, y) and zone.edge_distance(x, y, 1.0) > 1.0:
                h = height(sheet_tree, x, y)
                if h is None:
                    raise SystemExit("the sheet has a hole at (%.1f, %.1f)" % (x, y))
                errs.append(abs(h - target(x, y)))
                for tree in after:
                    g = height(tree, x, y)
                    if g is not None and g > h + 0.01:
                        poke += 1
                top = top_before(x, y)
                if h > sea and (top is None or top[0] <= sea):
                    dry_new += sample * sample
            y += sample
        x += sample
    if poke:
        raise SystemExit("a shell stands above the sheet at %d points in the zone" % poke)
    errs.sort()
    sheet.update({"faces": len(sheet_me.polygons), "vertices": len(sheet_me.vertices), "materials": len(mats),
                  "off_design_p99": round(errs[int(0.99 * len(errs))], 2), "off_design_most": round(errs[-1], 2),
                  "new_dry_land_ha": round(dry_new / 10000.0, 1), "shell_surface_outside_moved": round(worst_outside, 6),
                  "shell_triangles_kept_exactly": kept_exactly})
    return report, sheet, name


def road_natural(edit, now_t, pre_t, box, dry):
    """The designed natural ground under the road corridor where edit `edit` reshapes what the
    corridor covers (`ROAD_NATURAL`): every point of the edit's box with no Ground over it, on a
    `ROAD_NATURAL_STEP` lattice, and Ground's open edges there as they now stand, triangulated
    with those edges as constraints, the faces over Ground or wholly ungoverned dropped. Returns
    the object (None when `dry`) and its report."""
    over = ground_from_above(box)
    grid = bpy.data.objects[GRID]
    gme = grid.data
    owner_names = json.loads(grid["kyt_owner_table"])
    owner = np.zeros(len(gme.vertices), dtype=np.int32)
    gme.attributes["owner"].data.foreach_get("value", owner)
    gtree = BVHTree.FromPolygons([grid.matrix_world @ v.co for v in gme.vertices], [tuple(q.vertices) for q in gme.polygons])
    # Ground's open edges in the box that bound ground one stands on: where Ground meets the
    # corridor. (A shore wall's skirt is open too, under its top; its faces are walls.)
    pts = []
    zs = []
    ws = []
    index = {}
    segs = []

    def point(x, y, z, w):
        key = (round(x, 4), round(y, 4))
        if key not in index:
            index[key] = len(pts)
            pts.append(Vector((x, y)))
            zs.append(z)
            ws.append(w)
        return index[key]

    for ob in ground_objects():
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        for e in bm.edges:
            if not e.is_boundary or e.link_faces[0].normal.z < MIN_UP_FACE:
                continue
            a, b = e.verts
            if not all(box[0] <= v.co.x <= box[1] and box[2] <= v.co.y <= box[3] for v in (a, b)):
                continue
            ends = []
            for v in (a, b):
                tw = design_at(now_t, pre_t, v.co.x, v.co.y)
                ends.append(point(v.co.x, v.co.y, v.co.z if tw is None else tw[0], 0.0 if tw is None else tw[1]))
            segs.append(tuple(ends))
        bm.free()
    edge_pts = list(pts)
    near = KDTree(len(edge_pts))
    for k, q in enumerate(edge_pts):
        near.insert((q.x, q.y, 0.0), k)
    near.balance()
    refused = {}
    x = math.floor(box[0] / ROAD_NATURAL_STEP) * ROAD_NATURAL_STEP
    while x <= box[1]:
        y = math.floor(box[2] / ROAD_NATURAL_STEP) * ROAD_NATURAL_STEP
        while y <= box[3]:
            if not over(x, y) and (not edge_pts or near.find((x, y, 0.0))[2] >= ROAD_NATURAL_CLEAR):
                tw = design_at(now_t, pre_t, x, y)
                if tw is not None:
                    hit = gtree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
                    names = {owner_names[owner[i]] for i in gme.polygons[hit[2]].vertices} if hit[0] is not None else set()
                    if not any(n.endswith(ROAD_NATURAL_OWNERS) for n in names):
                        refused[(x, y)] = sorted(names)
                    point(x, y, tw[0], tw[1])
                else:
                    z = height(now_t, x, y)
                    if z is not None:
                        point(x, y, z, 0.0)
            y += ROAD_NATURAL_STEP
        x += ROAD_NATURAL_STEP
    if refused:
        where, names = next(iter(refused.items()))
        raise SystemExit("edit %d reshapes %d points under no road corridor (e.g. (%.0f, %.0f), under %s); refusing" % (
            edit, len(refused), where[0], -where[1], names))
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, segs, [], 0, 1e-4, True)
    vz = []
    vw = []
    for k, q in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(pts)]
        if src:
            vz.append(zs[src[0]])
            vw.append(ws[src[0]])
        else:
            tw = design_at(now_t, pre_t, q.x, q.y)
            vz.append(height(now_t, q.x, q.y) if tw is None else tw[0])
            vw.append(0.0 if tw is None else tw[1])
    faces = []
    for f in out_f:
        if max(vw[i] for i in f) <= 0.0:
            continue
        cx = sum(out_v[i].x for i in f) / 3.0
        cy = sum(out_v[i].y for i in f) / 3.0
        if over(cx, cy):
            continue
        faces.append(tuple(f))
    used = sorted({i for f in faces for i in f})
    area = 0.0
    for f in faces:
        a, b, c = (out_v[i] for i in f)
        area += abs((b - a).cross(c - a)) * 0.5
    report = {"faces": len(faces), "points": len(used), "edge_points": len(edge_pts), "ha": round(area / 10000.0, 2),
              "governed": sum(1 for i in used if vw[i] >= 1.0)}
    if dry or not faces:
        return None, report
    remap = {i: n for n, i in enumerate(used)}
    name = ROAD_NATURAL[edit]
    me = bpy.data.meshes.new(name)
    me.from_pydata([(out_v[i].x, out_v[i].y, vz[i]) for i in used], [], [tuple(remap[i] for i in f) for f in faces])
    me.validate()
    for poly in me.polygons:
        if poly.normal.z < 0.0:
            poly.flip()
    weight = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            weight.data[li].uv = (vw[used[me.loops[li].vertex_index]], 0.0)
    ob = bpy.data.objects.new(name, me)
    ob["kyt_collision"] = "none"
    ob["kyt_note"] = ("not ground: the natural ground the road corridor's sides are cut to where Ground edit %d "
                      "reshapes what the corridor covers, on the edit's design, its u texture coordinate how far "
                      "the design governs (1 inside the edit, 0 where it leaves the ground as it was); "
                      "tools/blender/world_terrain_ground_edit.py, ROAD_NATURAL" % edit)
    c = bpy.data.collections.get(EARTHWORKS)
    if c is None:
        c = bpy.data.collections.new(EARTHWORKS)
        bpy.context.scene.collection.children.link(c)
    c.objects.link(ob)
    # Drawn as wire, so it never reads as ground in the master; hidden, it would not export.
    ob.display_type = 'WIRE'
    return ob, report


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
        if hob.get("kyt_whole"):
            # Kept whole (edit 1): the object takes its old mesh back.
            old = ob.data
            keep = old.name
            ob.data = hob.data
            bpy.data.objects.remove(hob)
            bpy.data.meshes.remove(old)
            ob.data.name = keep
            continue
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
    for cname in (LAKES_COLLECTION, HISTORY, EARTHWORKS):
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
    if edit not in (SHELF_ID, LANDFORM_SHELF_ID):
        now_t, pre_t, box, grid_points = grid_surfaces(edit)
    before = {ob.name: coords(ob).copy() for ob in ground_objects()}
    reports = {}
    land = None
    land_report = {}
    if edit == SHELF_ID:
        reports, land_report, land = coast_shelf(edit, a["dry"])
        print("  %-34s %s" % (SHELF, ", ".join("%s %s" % kv for kv in land_report.items())))
    elif edit == LANDFORM_SHELF_ID:
        reports, land_report, land = landform_shelf(edit, a["dry"])
        print("  %-34s %s" % (LANDFORM_SHELF, ", ".join("%s %s" % kv for kv in land_report.items())))
        if not a["dry"] and land is None:
            raise SystemExit("no shelf face to build")
    elif edit in RANGE_BLEND:
        reports, land_report, land = range_blend(edit, now_t, pre_t, a["dry"])
        print("  %-34s %s" % (RANGE_BLEND[edit], ", ".join("%s %s" % kv for kv in land_report.items())))
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
    road = None
    road_report = {}
    if edit in ROAD_NATURAL:
        road, road_report = road_natural(edit, now_t, pre_t, box, a["dry"])
        print("  %-34s %s" % (ROAD_NATURAL[edit], ", ".join("%s %s" % kv for kv in road_report.items())))
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
        if edit in RANGE_BLEND:
            # Cut, emptied and capped whole; `range_blend` proved its surface outside the zone.
            continue
        now = coords(ob)
        used = edit_face_vertices(ob, edit)
        old = {tuple(v) for v in before[ob.name]}
        strays = sum(1 for i in range(len(now)) if i not in used and tuple(now[i]) not in old)
        if strays:
            raise SystemExit("%s: %d vertices outside the edit's faces moved" % (ob.name, strays))
    if edit == SHELF_ID:
        design = {"name": "coast_shelf"}
    elif edit == LANDFORM_SHELF_ID:
        design = {"name": "landform_shelf"}
    else:
        design = next(e for e in json.loads(bpy.data.objects[GRID].get("kyt_edits", "[]")) if e.get("id") == edit)
        if edit in WITH:
            refine = next(e for e in json.loads(bpy.data.objects[GRID].get("kyt_edits", "[]")) if e.get("id") == WITH[edit][0])
            design = dict(design, name="%s with %s" % (design["name"], refine["name"]))
    tris = ground_triangles()
    coll = lakes_collection()
    added = [land] if land else []
    if road is not None:
        added.append(road.name)
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
    earthworks = bpy.data.collections.get(EARTHWORKS)
    scene["kyt_export_collections"] = [GROUND, LAKES_COLLECTION] + ([EARTHWORKS] if earthworks and earthworks.all_objects else [])
    entry = {"id": edit, "name": design["name"], "script": "tools/blender/world_terrain_ground_edit.py",
             "date": TODAY, "objects": sorted(reports), "report": reports, "lakes_ha": areas,
             "added": added, "hid": hid, "export_before": export_before}
    if land:
        entry["new_land"] = land_report
    if road is not None:
        entry["road_natural"] = road_report
    log(entry)
    held = sum(r.get("seam_held", 0) for r in reports.values())
    if edit == SHELF_ID:
        readme("Ground edit %d (%s), %s: every coast's shore wall cut %.1f m under the sea and the part below "
               "dropped, in %s; from that line %s slopes %.0f m out to %.1f (%s); the wall panels' old faces "
               "kept in %s. Undo: tools/blender/world_terrain_ground_edit.py -- --edit shelf --undo." % (
                   edit, design["name"], TODAY, SHELF_UNDER, ", ".join(reports), land, SHELF_W, SHELF_DEPTH,
                   ", ".join("%s %s" % kv for kv in land_report.items()), HISTORY))
    elif edit == LANDFORM_SHELF_ID:
        readme("Ground edit %d (%s), %s: %s runs the landforms' coasts on below the waterline from each side "
               "facing the open sea, %.1f m under it, %.0f m out to %.1f (%s); the shells untouched. Undo: "
               "tools/blender/world_terrain_ground_edit.py -- --edit landform_shelf --undo." % (
                   edit, design["name"], TODAY, land, SHELF_UNDER, SHELF_W, SHELF_DEPTH,
                   ", ".join("%s %s" % kv for kv in land_report.items())))
    elif edit in RANGE_BLEND:
        readme("Ground edit %d (%s), Stage 3, %s: in the zone grid edit %d changed, the landforms %s were cut along "
               "its edge, emptied inside it and capped, and %s built there as one sheet on the edit's surface (%s); "
               "the landforms kept whole in %s. Undo: tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
                   edit, design["name"], TODAY, edit, ", ".join(reports), land,
                   ", ".join("%s %s" % kv for kv in land_report.items()), HISTORY, edit))
    elif land:
        readme("Ground edit %d (%s), Stage 3, %s: the land grid edit %d designed beyond the shore built as %s in "
               "Ground (%s); the shore wall panels it meets cut at its edge in %s, their old faces kept in %s. Undo: "
               "tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
                   edit, design["name"], TODAY, edit, land, ", ".join("%s %s" % kv for kv in land_report.items()),
                   ", ".join(reports), HISTORY, edit))
    else:
        readme("Ground edit %d (%s), Stage 3, %s: grid edit %s carried onto Ground (%s): its region refined to "
           "a %.0f m lattice and given the grid's designed surface; %d vertices on the seams with the generator's "
           "ground held where they were; water %s built on Ground in the Lakes collection, exported with Ground; "
           "design planes %s hidden; the replaced faces kept in %s. Undo: "
           "tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
               edit, design["name"], TODAY, ("%d with %d, its refinement," % (edit, WITH[edit][0])) if edit in WITH else edit,
               ", ".join(reports), LATTICE, held,
               ", ".join("%s %s" % (k, ("%.2f ha" % v) if k in lakes else ("%.0f m2" % v)) for k, v in areas.items()) or "none",
               ", ".join(hid) or "none", HISTORY, edit))
        if road is not None:
            readme("Ground edit %d: Ground's edge along the road corridor moved with it (%d vertices, up to %.1f m), "
                   "and %s, in the %s collection, hands the generator the edit's natural ground under the "
                   "corridor (%s); the road's own level does not read it." % (
                       edit, sum(r.get("seam_followed", 0) for r in reports.values()),
                       max((r.get("seam_followed_most", 0.0) for r in reports.values()), default=0.0),
                       road.name, EARTHWORKS, ", ".join("%s %s" % kv for kv in road_report.items())))
    if edit in RANGE_BLEND:
        print("world_terrain_ground_edit: edit %d carried; every shell's surface outside its zone unchanged" % edit)
    else:
        print("world_terrain_ground_edit: edit %d carried; every vertex outside its faces unchanged" % edit)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    # After the save, so the render's hidden layers and cameras never reach the master.
    if a["render"]:
        views = {key: (lk["centre"], 2.0 * float(lk["R"]) + 300.0, float(lk["brim"])) for key, lk in lakes.items()}
        views.update(VIEWS.get(edit, {}))
        render(a["render"], edit, views)


main()
