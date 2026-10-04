"""The beach town's second seafood restaurant, on the ferry plaza's south side
(beach-town-plan.html, zone C, "Seafood restaurant 2"): block-out and massing,
2026-10-02.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/pier_seafood_restaurant.blend \
        --python tools/blender/pier_seafood_restaurant.py -- [--replace] [--save] [--render <folder>]

Builds the building into `export`, one object a part, and the plan's footprint,
the site round it and a 1.7 m figure into the locked `reference`. Rerunning
rebuilds both from scratch (`--replace` while `export` holds anything, which may
be hers). `--render <folder>` shoots Eevee frames from temporary cameras that
are never saved; `--save` saves the file before any render.

**Frame.** Real metres, Z up, the origin at the middle of the plan's 18 x 10 m
rectangle, z = 0 the plaza paving, which is the restaurant's floor level. The
front, the plaza face with the customer door, faces -Y here (+Z in Godot, as
every prop: `picnic_tables.py`, and the bench greybox's `_front` parts lie on
-Y). In the world the front faces north, so the prop is placed turned half
round, which puts +X here at world west: the sunset deck is on +X, the kitchen
on -X toward the sitting steps and the ice-cream kiosk, the service door on +Y
toward the 2 m strip at the plaza's south edge and the beach ramp.

**The rectangle is building plus deck.** The plaza's sea face, a low wall at
the strand's edge, is 2 m beyond the rectangle's west side, and that 2 m strip
is the walk from the pier gate to the beach ramp and steps; a deck outside the
rectangle would block it. So the enclosed building is 12.5 x 10 m (a 4 m
kitchen at the east end, an 8.5 m dining room) and the deck the last 5.5 m,
full width, at floor level with its railing open to the plaza beside the
building.

**The look** is the building at the pier's root in Christina's Avila Beach
photographs (`documentation/reference/beach_town/`, 2026-10-02: "pretty darn
close right"): pale blue walls, white trim (corner boards, window and door
frames, fascia and soffit), a low grey shingle gable along the long axis with
a round porthole window in each gable end and a flue at the kitchen end, pairs
of tall white-framed windows, and a railed deck, white rails on blue posts.
Not taken: its piles over the sand and its stair up from the beach (ours stands
on the plaza at the landing's level, the plan's siting), its flagpole, sign
and name. Chunky and plain, as the park's props (`prop-pipeline.md`, Standards
applied): walls 0.3 m thick, the roof slab 0.22 m with its white edge for the
fascia, few big pieces.

**Thresholds.** The player has no step-up (`AGENTS.md`, Geometry), so every
door is flush: the floor and the deck are 12 mm proud of the paving with
`kyt_collision = none`, as the park's paving, and the walls' openings are cut
below the floor so the floor runs through them. Each door is a true opening in
the wall closed by its own leaf, the leaf's origin on its hinge edge at the
floor so the game can swing it later (Send's `kyt_hinge` knows only `top`, the
bin flaps' hinge; a side hinge is for the next pass). Walls, the bin screen and
the deck go 0.2 m below the paving so uneven ground never shows a gap
(`ground_line` at the origin, as the hardscape kit). Shapes overlap, never
share a plane: frames penetrate their walls and stand 3 cm proud, mullions sit
1 cm behind the frame's face, the deck runs under the west wall 2 mm lower
than the floor, posts stop inside the cap rail.

Preview colours only, one material slot a part (`seafood_<part>`); the one
material per prop comes at the texture stage.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

TAG = "kyt_restaurant"  # on everything this tool makes, so a rerun removes only its own

# --- the plan ---------------------------------------------------------------------

FOOT_X, FOOT_Y = 9.0, 5.0        # half the 18 x 10 m rectangle
BUILDING_E = -FOOT_X             # the building's east end (-X here is world east)
BUILDING_W = 3.5                 # its west end; the deck runs from here to +FOOT_X
KITCHEN_W = -5.0                 # the kitchen partition's middle
WALL_T = 0.30
WALL_TOP = 3.1                   # the eave line: the roof's underside at the outer wall face
WALL_Z0 = -0.2                   # walls reach this far below the paving
WALL_Z1 = 3.3                    # and this far up into the roof slab
PITCH = 1.0 / 3.0                # 4 in 12
ROOF_T = 0.22
EAVE_OUT, GABLE_OUT = 0.6, 0.5   # the roof past the walls, sides and ends
RIDGE_UNDER = WALL_TOP + FOOT_Y * PITCH
CEILING_Z = 2.85
FLOOR_TOP = 0.012                # proud of the paving, no collision (AGENTS.md: paving)
DECK_TOP = 0.010
DECK_IN = 0.2                    # the deck runs this far under the west wall
DECK_OVER = 0.3                  # and this far past the building's sides
PORTHOLE_R, PORTHOLE_Z = 0.35, 3.95
FRAME = 0.08                     # a frame's visible leg, and its buried half
FRAME_PROUD = 0.03
MULLION = 0.10
GLASS_T = 0.02
LEAF_T = 0.05
LEAF_LIFT = 0.02                 # a door leaf's bottom over the floor
POST = 0.12
RAIL_TOP = 1.10
RAILS = ((RAIL_TOP - 0.06, RAIL_TOP, 0.14), (0.70, 0.75, 0.08), (0.35, 0.40, 0.08))  # (z0, z1, width)
POST_PITCH = 1.85
GATE = 1.8                       # the railing's opening onto the plaza, from the building's corner
RAIL_IN = 0.05                   # the south run ends this far inside the west wall; its post 1 cm less
FLUE = (-7.0, 0.6, 0.5, 5.65)    # x, y, side, top
BIN_SCREEN_H, BIN_SCREEN_T = 1.3, 0.12
BEVEL = 0.03

# colours are stand-ins for the painting (her Avila photograph's building)
WALLS = (0.42, 0.66, 0.86, 1.0)
TRIM = (0.92, 0.92, 0.90, 1.0)
ROOF = (0.33, 0.34, 0.35, 1.0)
GLASS = (0.65, 0.82, 0.90, 0.35)
DOOR = (0.10, 0.30, 0.48, 1.0)
DECK = (0.55, 0.47, 0.36, 1.0)
RAILING = (0.93, 0.93, 0.92, 1.0)
FLOOR = (0.60, 0.45, 0.30, 1.0)
METAL = (0.22, 0.22, 0.24, 1.0)
BINS = (0.20, 0.32, 0.26, 1.0)

# The walls, each with its normal axis, its two faces, and the sign of outward.
# An opening on a 'y' wall is given in (x, z); on an 'x' wall in (y, z).
WALL_IN = {
    "front": ("y", -FOOT_Y, -FOOT_Y + WALL_T, -1),
    "back": ("y", FOOT_Y - WALL_T, FOOT_Y, 1),
    "west": ("x", BUILDING_W - WALL_T, BUILDING_W, 1),
    "east": ("x", BUILDING_E, BUILDING_E + WALL_T, -1),
    "partition": ("x", KITCHEN_W - 0.1, KITCHEN_W + 0.1, 1),
}
# (wall, a0, a1, z0, z1, kind): kind 'pair' is a window with a mullion,
# 'window' a single pane, 'door' a leaf hinged at a0, 'double' two leaves.
OPENINGS = {
    "win_kitchen_front": ("front", -7.6, -6.4, 1.5, 2.4, "window"),
    "win_front_l": ("front", -4.3, -2.4, 0.9, 2.3, "pair"),
    "door_front": ("front", -1.65, 0.15, -0.1, 2.3, "double"),
    "win_front_r": ("front", 0.9, 2.8, 0.9, 2.3, "pair"),
    "win_kitchen_back": ("back", -8.6, -7.4, 1.6, 2.4, "window"),
    "door_service": ("back", -6.5, -5.5, -0.1, 2.2, "door"),
    "win_back_l": ("back", -4.3, -2.4, 0.9, 2.3, "pair"),
    "win_back_r": ("back", 0.9, 2.8, 0.9, 2.3, "pair"),
    "win_west_n": ("west", -4.2, -2.3, 0.9, 2.3, "pair"),
    "door_west": ("west", -0.9, 0.9, -0.1, 2.3, "double"),
    "win_west_s": ("west", 2.3, 4.2, 0.9, 2.3, "pair"),
    "win_east": ("east", -0.95, 0.95, 0.9, 2.3, "pair"),
    "door_kitchen": ("partition", 2.4, 3.3, -0.1, 2.1, "door"),
}

# The site round the building, in this frame (x = -116 - world x, y = world z - 457),
# from the plan's polygons, for the reference collection.
SITE = {
    "site_plaza": [(-11.05, -41), (-23.96, 7), (11, 7), (11, -41)],
    "site_pier": [(11, -23), (74, -23), (74, -11), (11, -11)],
    "site_waiting_room": [(-9, -22), (11, -22), (11, -12), (-9, -12)],
    "site_shacks": [(-6.5, -39), (11, -39), (11, -32), (-6.5, -32)],
    "site_kiosk_ice_cream": [(-17, -8), (-12, -8), (-12, -4), (-17, -4)],
    "site_beach_ramp": [(-4, 7), (9, 7), (9, 10), (-4, 10)],
    "site_lower_steps": [(-17.26, -41), (-30.18, 7), (-23.96, 7), (-11.05, -41)],
    "site_middle_terrace": [(-23.48, -41), (-36.4, 7), (-30.18, 7), (-17.26, -41)],
}


# --- building blocks ----------------------------------------------------------------

def material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = 0.8
        if colour[3] < 1.0:
            bsdf.inputs["Alpha"].default_value = colour[3]
            bsdf.inputs["Roughness"].default_value = 0.1
            for attr, value in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
                try:
                    setattr(mat, attr, value)
                except (AttributeError, TypeError):
                    pass
    return mat


def box_bm(x0, x1, y0, y1, z0, z1, bm=None):
    bm = bm or bmesh.new()
    v = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (1, 5, 7, 3), (3, 7, 6, 2), (2, 6, 4, 0)):
        bm.faces.new([v[i] for i in f])
    return bm


def prism(poly, axis, lo, hi, bm=None):
    """A 2D polygon extruded along an axis: `poly` is (a, b) pairs, the plane's
    two axes in X, Y, Z order with `axis` left out ('x' gives (y, z), 'y' gives
    (x, z), 'z' gives (x, y)). Several prisms may share one bmesh."""
    bm = bm or bmesh.new()

    def at(a, b, t):
        if axis == "x":
            return (t, a, b)
        if axis == "y":
            return (a, t, b)
        return (a, b, t)

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    n = len(poly)
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return bm


def ring_prism(outer, inner, axis, lo, hi, bm=None):
    """A rectangular frame: `outer` and `inner` are (a0, a1, b0, b1) in the
    plane across `axis`, extruded from lo to hi. No hole-filling needed: the
    end faces are four trapezoids."""
    bm = bm or bmesh.new()

    def at(a, b, t):
        if axis == "x":
            return (t, a, b)
        if axis == "y":
            return (a, t, b)
        return (a, b, t)

    def corners(r):
        a0, a1, b0, b1 = r
        return [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]

    o, i = corners(outer), corners(inner)
    on = [bm.verts.new(at(a, b, lo)) for a, b in o]
    of = [bm.verts.new(at(a, b, hi)) for a, b in o]
    inn = [bm.verts.new(at(a, b, lo)) for a, b in i]
    inf = [bm.verts.new(at(a, b, hi)) for a, b in i]
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((on[k], on[j], inn[j], inn[k]))
        bm.faces.new((of[k], inf[k], inf[j], of[j]))
        bm.faces.new((on[k], of[k], of[j], on[j]))
        bm.faces.new((inn[k], inn[j], inf[j], inf[k]))
    return bm


def cylinder_bm(axis, centre, radius, lo, hi, sides=16, bm=None):
    poly = [(centre[0] + radius * math.cos(math.tau * i / sides),
             centre[1] + radius * math.sin(math.tau * i / sides)) for i in range(sides)]
    return prism(poly, axis, lo, hi, bm)


def mitred_path(points, width):
    """A polyline's outline `width` wide with mitred corners, as a polygon."""
    pts = [Vector(p) for p in points]
    h = width / 2
    left, right = [], []
    for k, p in enumerate(pts):
        if k == 0:
            t = (pts[1] - p).normalized()
            n = Vector((-t.y, t.x))
            off = n * h
        elif k == len(pts) - 1:
            t = (p - pts[k - 1]).normalized()
            n = Vector((-t.y, t.x))
            off = n * h
        else:
            a, b = (p - pts[k - 1]).normalized(), (pts[k + 1] - p).normalized()
            na, nb = Vector((-a.y, a.x)), Vector((-b.y, b.x))
            off = (na + nb) * (h / (1.0 + na.dot(nb)))
        left.append(p + off)
        right.append(p - off)
    return [(v.x, v.y) for v in left + right[::-1]]


def finish(name, bm, mats, *, bevel=BEVEL, segments=2, smooth=True, collide=True, unwrap="facets"):
    """A bmesh into an object in `export`, bevelled and tagged."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections["export"].objects.link(obj)
    for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
        mesh.materials.append(m)
    obj[TAG] = True
    obj["kyt_unwrap"] = unwrap
    if not collide:
        obj["kyt_collision"] = "none"
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35)
        mod.harden_normals = False
        apply_modifiers(obj)
    if smooth:
        smooth_by_angle(obj)
    return obj


def apply_modifiers(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    new.materials.clear()
    for m in old.materials:
        new.materials.append(m)
    bpy.data.meshes.remove(old)


def booleans(name, base_bm, ops, mats, **kw):
    """`ops` is [(operation, bmesh)] applied in order with the exact solver,
    then the bevel on the result."""
    base = finish(name, base_bm, mats, bevel=0, smooth=False)
    for i, (op, cb) in enumerate(ops):
        cut = finish(f"{name}_op{i}", cb, mats, bevel=0, smooth=False)
        mod = base.modifiers.new(f"op{i}", "BOOLEAN")
        mod.operation = op
        mod.object = cut
        mod.solver = "EXACT"
        apply_modifiers(base)
        me = cut.data
        bpy.data.objects.remove(cut)
        bpy.data.meshes.remove(me)
    if kw.get("bevel", BEVEL):
        mod = base.modifiers.new("bevel", "BEVEL")
        mod.width = kw.get("bevel", BEVEL)
        mod.segments = kw.get("segments", 2)
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35)
        apply_modifiers(base)
    smooth_by_angle(base)
    return base


def smooth_by_angle(obj, deg=40.0):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(deg))
    bm.to_mesh(mesh)
    bm.free()


def roof_under(y):
    return WALL_TOP + (FOOT_Y - abs(y)) * PITCH


def wall_box(wall, a0, a1, z0, z1, grow=0.0, depth=None):
    """A box through `wall` over the opening (a0..a1, z0..z1): across the
    wall's full depth plus `grow` each side, or `depth` (lo, hi) instead."""
    axis, lo, hi, _ = WALL_IN[wall]
    lo, hi = depth if depth else (lo - grow, hi + grow)
    if axis == "y":
        return box_bm(a0, a1, lo, hi, z0, z1)
    return box_bm(lo, hi, a0, a1, z0, z1)


# --- the building ----------------------------------------------------------------------

def build_walls(mats):
    """One object: the ring of outer walls with the two gables, every door and
    window a true hole, the portholes through the gables."""
    outer = box_bm(BUILDING_E, BUILDING_W, -FOOT_Y, FOOT_Y, WALL_Z0, WALL_Z1)
    inner = box_bm(BUILDING_E + WALL_T, BUILDING_W - WALL_T, -FOOT_Y + WALL_T, FOOT_Y - WALL_T,
                   WALL_Z0 - 0.1, WALL_Z1 + 0.1)
    # The gables: their base inside the ring's top band, their slopes 2 cm up
    # inside the roof slab at the ridge and 10 cm at the eaves (so never in the
    # slab's underside plane).
    apex = RIDGE_UNDER + 0.02
    base = WALL_Z1 - 0.1
    gable = [(-FOOT_Y, base), (FOOT_Y, base), (0.0, apex)]
    ops = [("DIFFERENCE", inner),
           ("UNION", prism(gable, "x", BUILDING_E, BUILDING_E + WALL_T)),
           ("UNION", prism(gable, "x", BUILDING_W - WALL_T, BUILDING_W))]
    for name, (wall, a0, a1, z0, z1, kind) in OPENINGS.items():
        if wall != "partition":
            ops.append(("DIFFERENCE", wall_box(wall, a0, a1, z0, z1, grow=0.1)))
    for x0, x1 in ((BUILDING_E - 0.1, BUILDING_E + WALL_T + 0.1), (BUILDING_W - WALL_T - 0.1, BUILDING_W + 0.1)):
        ops.append(("DIFFERENCE", cylinder_bm("x", (0.0, PORTHOLE_Z), PORTHOLE_R, x0, x1, 16)))
    return booleans("walls", outer, ops, mats["walls"], segments=1)


def build_partition(mats):
    axis, lo, hi, _ = WALL_IN["partition"]
    wall, a0, a1, z0, z1, _ = OPENINGS["door_kitchen"]
    base = box_bm(lo, hi, -FOOT_Y + WALL_T / 2 + 0.02, FOOT_Y - WALL_T / 2 - 0.02, -0.03, CEILING_Z + 0.1)
    return booleans("kitchen_partition", base, [("DIFFERENCE", wall_box("partition", a0, a1, z0, z1, grow=0.1))],
                    mats["walls"], segments=1)


def build_roof(mats):
    """The gable roof as one thick chevron slab, shingles on top and white on
    its edges and underside: the fascia and soffit without a second piece."""
    ys = (-FOOT_Y - EAVE_OUT, 0.0, FOOT_Y + EAVE_OUT)
    top = [(y, roof_under(y) + ROOF_T) for y in ys]
    under = [(y, roof_under(y)) for y in reversed(ys)]
    bm = prism(top + under, "x", BUILDING_E - GABLE_OUT, BUILDING_W + GABLE_OUT)
    obj = finish("roof", bm, [mats["roof"], mats["trim"]])
    for p in obj.data.polygons:
        p.material_index = 0 if p.normal.z > 0.5 else 1
    return obj


def build_floors(mats):
    floor = box_bm(BUILDING_E + 0.03, BUILDING_W - 0.03, -FOOT_Y + 0.03, FOOT_Y - 0.03, -0.04, FLOOR_TOP)
    finish("floor", floor, mats["floor"], bevel=0, collide=False, unwrap="planar")
    ceiling = box_bm(BUILDING_E + WALL_T / 2, BUILDING_W - WALL_T / 2, -FOOT_Y + WALL_T / 2, FOOT_Y - WALL_T / 2,
                     CEILING_Z, CEILING_Z + 0.2)
    finish("ceiling", ceiling, mats["trim"], bevel=0, unwrap="planar")
    deck = box_bm(BUILDING_W - DECK_IN, FOOT_X, -FOOT_Y - DECK_OVER, FOOT_Y + DECK_OVER, WALL_Z0 + 0.02, DECK_TOP)
    finish("deck", deck, mats["deck"], bevel=0.01, segments=1, collide=False, unwrap="planar")


def rail_path():
    """The railing's run round the deck: from the gate post on the plaza side,
    round the sea corner and back to the building on the south side."""
    c = POST / 2 + 0.02
    x_out, y_out = FOOT_X - c, FOOT_Y - c
    return [(BUILDING_W + GATE, -y_out), (x_out, -y_out), (x_out, y_out), (BUILDING_W - RAIL_IN, y_out)]


def build_railing(mats):
    path = rail_path()
    bm = None
    for z0, z1, w in RAILS:
        bm = prism(mitred_path(path, w), "z", z0, z1, bm)
    finish("deck_rails", bm, mats["railing"], bevel=0)
    # posts at the path's corners and ends, and evenly along each run
    spots = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        run = math.hypot(x1 - x0, y1 - y0)
        n = max(1, math.ceil(run / POST_PITCH))
        for k in range(n + 1):
            p = (x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)
            if not spots or math.hypot(p[0] - spots[-1][0], p[1] - spots[-1][1]) > 0.01:
                spots.append(p)
    bm = None
    h = POST / 2
    for x, y in spots:
        x0, x1 = x - h, x + h
        if abs(x - (BUILDING_W - RAIL_IN)) < 1e-6:  # the post against the west wall goes 4 cm into it
            x0, x1 = BUILDING_W - RAIL_IN + 0.01, BUILDING_W - RAIL_IN + 0.01 + POST
        bm = box_bm(x0, x1, y - h, y + h, DECK_TOP - 0.04, RAIL_TOP - 0.03, bm)
    finish("deck_posts", bm, mats["walls"], bevel=0)
    return spots


def build_openings(mats):
    """A frame round every opening, glass in the windows, a leaf in every door."""
    for name, (wall, a0, a1, z0, z1, kind) in OPENINGS.items():
        axis, lo, hi, out = WALL_IN[wall]
        depth = (lo - FRAME_PROUD, hi + FRAME_PROUD)
        mid = (lo + hi) / 2
        inner = (a0 + FRAME, a1 - FRAME, z0 + FRAME if kind.startswith(("window", "pair")) else z0, z1 - FRAME)
        if kind in ("window", "pair"):
            bm = ring_prism((a0 - FRAME, a1 + FRAME, z0 - FRAME, z1 + FRAME), inner, axis, *depth)
            if kind == "pair":  # a mullion down the middle, 1 cm behind the frame's faces
                c = (a0 + a1) / 2
                bm = _join(bm, wall_box(wall, c - MULLION / 2, c + MULLION / 2, inner[2] - 0.03, inner[3] + 0.03,
                                        depth=(lo - FRAME_PROUD + 0.01, hi + FRAME_PROUD - 0.01)))
            finish(f"frame_{name}", bm, mats["trim"], bevel=0)
            g = 0.04
            glass = wall_box(wall, inner[0] - g, inner[1] + g, inner[2] - g, inner[3] + g,
                             depth=(mid - GLASS_T / 2, mid + GLASS_T / 2))
            finish(f"glass_{name}", glass, mats["glass"], bevel=0, unwrap="planar")
        else:
            # a U: the frame's two jambs and head, the floor running through
            o0, o1, oz = a0 - FRAME, a1 + FRAME, z1 + FRAME
            i0, i1, iz = inner[0], inner[1], inner[3]
            zb = -0.02
            u = [(o0, zb), (o0, oz), (o1, oz), (o1, zb), (i1, zb), (i1, iz), (i0, iz), (i0, zb)]
            finish(f"frame_{name}", prism(u, axis, *depth), mats["trim"], bevel=0)
            clear = i1 - i0
            leaves = [(i0 + 0.01, (clear - 0.04) / 2, 1, "_l"), (i1 - 0.01, (clear - 0.04) / 2, -1, "_r")] \
                if kind == "double" else [(i0 + 0.01, clear - 0.02, 1, "")]
            for hinge, width, direction, suffix in leaves:
                _leaf(f"{name}{suffix}", axis, hinge, width, direction, mid, iz - LEAF_LIFT - 0.02, mats["door"])


def _join(bm, other):
    mesh = bpy.data.meshes.new("_join")
    other.to_mesh(mesh)
    other.free()
    bm.from_mesh(mesh)
    bpy.data.meshes.remove(mesh)
    return bm


def _leaf(name, axis, hinge, width, direction, mid, height, mat):
    """A door leaf built with its hinge edge on its origin, at the floor, so a
    turn about its local Z swings it."""
    t = LEAF_T / 2
    if axis == "y":
        bm = box_bm(min(0.0, direction * width), max(0.0, direction * width), -t, t, 0.0, height)
        loc = (hinge, mid, LEAF_LIFT)
    else:
        bm = box_bm(-t, t, min(0.0, direction * width), max(0.0, direction * width), 0.0, height)
        loc = (mid, hinge, LEAF_LIFT)
    obj = finish(name, bm, mat, bevel=0)
    obj.location = loc
    obj["kyt_hinge_edge"] = "side"  # a side hinge: Send's `kyt_hinge` knows only `top` so far
    return obj


def build_portholes(mats):
    for x0, x1 in ((BUILDING_E, BUILDING_E + WALL_T), (BUILDING_W - WALL_T, BUILDING_W)):
        tag = "e" if x0 < 0 else "w"
        bm = bmesh.new()
        n = 16
        ro, ri = PORTHOLE_R + FRAME, PORTHOLE_R - FRAME
        lo, hi = x0 - FRAME_PROUD, x1 + FRAME_PROUD
        ring = [[bm.verts.new((x, r * math.cos(math.tau * i / n), PORTHOLE_Z + r * math.sin(math.tau * i / n)))
                 for i in range(n)] for x, r in ((lo, ro), (lo, ri), (hi, ro), (hi, ri))]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((ring[0][i], ring[0][j], ring[1][j], ring[1][i]))
            bm.faces.new((ring[2][i], ring[3][i], ring[3][j], ring[2][j]))
            bm.faces.new((ring[0][i], ring[2][i], ring[2][j], ring[0][j]))
            bm.faces.new((ring[1][i], ring[1][j], ring[3][j], ring[3][i]))
        finish(f"frame_porthole_{tag}", bm, mats["trim"], bevel=0)
        mid = (x0 + x1) / 2
        finish(f"glass_porthole_{tag}", cylinder_bm("x", (0.0, PORTHOLE_Z), ri + 0.03, mid - GLASS_T / 2, mid + GLASS_T / 2, n),
               mats["glass"], bevel=0, unwrap="planar")


def build_corner_boards(mats):
    """White boards wrapping each corner, 3 cm proud, 2 cm into the wall so no
    face lies in the wall's own planes, up into the roof slab."""
    p, leg, into = 0.03, 0.16, 0.035  # 3.5 cm in: off the floor's, the posts' and the rails' planes
    bm = None
    for cx, sx in ((BUILDING_E, 1), (BUILDING_W, -1)):
        for cy, sy in ((-FOOT_Y, 1), (FOOT_Y, -1)):
            # sx, sy point from the corner into the building
            pts = [(cx - sx * p, cy - sy * p), (cx + sx * leg, cy - sy * p), (cx + sx * leg, cy + sy * into),
                   (cx + sx * into, cy + sy * into), (cx + sx * into, cy + sy * leg), (cx - sx * p, cy + sy * leg)]
            bm = prism(pts, "z", -0.05, WALL_TOP + 0.08, bm)
    finish("corner_boards", bm, mats["trim"], bevel=0)


def build_flue(mats):
    x, y, s, top = FLUE
    h = s / 2
    bm = box_bm(x - h, x + h, y - h, y + h, roof_under(y + h) - 0.1, top)
    lid = s / 2 + 0.05
    bm = box_bm(x - lid, x + lid, y - lid, y + lid, top - 0.03, top + 0.07, bm)
    finish("kitchen_flue", bm, mats["metal"], bevel=0.02, segments=1)


def build_bin_store(mats):
    """An L of screen wall on the back wall at the kitchen's corner, open
    toward the service door, with two bins in it."""
    x0, x1 = BUILDING_E + 0.05, BUILDING_E + 2.0
    y0, y1 = FOOT_Y - 0.05, FOOT_Y + 1.1
    t = BIN_SCREEN_T
    l_shape = [(x0, y0), (x0 + t, y0), (x0 + t, y1 - t), (x1, y1 - t), (x1, y1), (x0, y1)]
    finish("bin_screen", prism(l_shape, "z", WALL_Z0, BIN_SCREEN_H), mats["walls"], bevel=0.02, segments=1)
    for k, bx in enumerate((x0 + 0.25, x0 + 1.0)):
        finish(f"bin_{'ab'[k]}", box_bm(bx, bx + 0.6, y0 + 0.28, y1 - t - 0.05, -0.02, 1.05), mats["bins"], bevel=0.025, segments=1)


def build():
    mats = {k: material(f"seafood_{k}", c) for k, c in
            (("walls", WALLS), ("trim", TRIM), ("roof", ROOF), ("glass", GLASS), ("door", DOOR), ("deck", DECK),
             ("railing", RAILING), ("floor", FLOOR), ("metal", METAL), ("bins", BINS))}
    build_walls(mats)
    build_partition(mats)
    build_roof(mats)
    build_floors(mats)
    build_openings(mats)
    build_portholes(mats)
    build_corner_boards(mats)
    build_flue(mats)
    build_bin_store(mats)
    spots = build_railing(mats)
    return spots


# --- the reference ------------------------------------------------------------------------

def outline(name, pts, z=0.0, closed=True):
    """An edge-only outline in `reference`: shows in the viewport, never renders."""
    mesh = bpy.data.meshes.new(name)
    verts = [(x, y, z) for x, y in pts]
    edges = [(i, (i + 1) % len(pts)) for i in range(len(pts) if closed else len(pts) - 1)]
    mesh.from_pydata(verts, edges, [])
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    bpy.data.collections["reference"].objects.link(obj)
    return obj


def figure_bm():
    """A 1.7 m standing figure: a body and a head."""
    bm = cylinder_bm("z", (0.0, 0.0), 0.18, 0.0, 1.45, 12)
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.125, matrix=Matrix.Translation((0, 0, 1.575)))
    return bm


def build_reference():
    ref = bpy.data.collections["reference"]
    outline("footprint_18x10", [(-FOOT_X, -FOOT_Y), (FOOT_X, -FOOT_Y), (FOOT_X, FOOT_Y), (-FOOT_X, FOOT_Y)])
    outline("building_12p5x10", [(BUILDING_E, -FOOT_Y), (BUILDING_W, -FOOT_Y), (BUILDING_W, FOOT_Y), (BUILDING_E, FOOT_Y)])
    for name, pts in SITE.items():
        outline(name, pts)
    outline("sunset_arrow_plus_x", [(12.0, 0.0), (16.0, 0.0), (15.0, 0.6), (16.0, 0.0), (15.0, -0.6)], closed=False)
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        ref.objects.link(marker)
    mesh = bpy.data.meshes.new("figure_1p7m")
    bm = figure_bm()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    fig = bpy.data.objects.new("figure_1p7m", mesh)
    fig.location = (-0.75, -8.0, 0.0)
    fig[TAG] = True
    ref.objects.link(fig)
    return fig


# --- checks ------------------------------------------------------------------------------

def checks():
    export = bpy.data.collections["export"]
    total, lines = 0, []
    for o in sorted(export.objects, key=lambda o: o.name):
        o.data.calc_loop_triangles()
        n = len(o.data.loop_triangles)
        total += n
        lines.append(f"    {o.name}: {n}")
    eave_under, eave_top = roof_under(FOOT_Y + EAVE_OUT), roof_under(FOOT_Y + EAVE_OUT) + ROOF_T
    out = [
        f"footprint {2 * FOOT_X:.1f} x {2 * FOOT_Y:.1f} m: building {BUILDING_W - BUILDING_E:.1f} x {2 * FOOT_Y:.1f} m "
        f"(kitchen {KITCHEN_W - BUILDING_E:.1f} m, dining {BUILDING_W - KITCHEN_W:.1f} m), deck {FOOT_X - BUILDING_W:.1f} m deep "
        f"x {2 * (FOOT_Y + DECK_OVER):.1f} m wide at the sunset end (+X)",
        f"walls {WALL_T:.2f} m thick, eave line {WALL_TOP:.2f} m at the wall, the eave's edge {eave_under:.2f} under / "
        f"{eave_top:.2f} top at {EAVE_OUT:.1f} m out; ridge {RIDGE_UNDER + ROOF_T:.2f} m; ceiling {CEILING_Z:.2f} m; "
        f"railing {RAIL_TOP:.2f} m",
        f"thresholds: floor {FLOOR_TOP * 1000:.0f} mm and deck {DECK_TOP * 1000:.0f} mm proud, no collision; "
        f"door leaves {LEAF_LIFT * 1000:.0f} mm over the floor",
        f"doors: " + ", ".join(f"{n} {a1 - a0:.2f} x {z1:.2f}" for n, (w, a0, a1, z0, z1, k) in OPENINGS.items() if k in ("door", "double")),
        f"{len(export.objects)} parts, {total} triangles, materials "
        + ", ".join(sorted({m.name for o in export.objects for m in o.data.materials})),
    ]
    return out, lines


# --- renders ------------------------------------------------------------------------------

def render(folder, name, figure):
    """Eevee frames from temporary cameras, lights, ground and figures, none of
    which are saved: everything made here is removed after."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    try:
        scene.eevee.taa_render_samples = 24
        scene.eevee.use_shadows = True
    except AttributeError:
        pass
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    world = bpy.data.worlds.new("_render_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.88, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    old_world, scene.world = scene.world, world
    tmp = bpy.data.collections.new("_render_tmp")
    scene.collection.children.link(tmp)

    def add(name, mesh_or_bm, mat=None, loc=(0, 0, 0)):
        if isinstance(mesh_or_bm, bmesh.types.BMesh):
            me = bpy.data.meshes.new(name)
            bmesh.ops.recalc_face_normals(mesh_or_bm, faces=mesh_or_bm.faces)
            mesh_or_bm.to_mesh(me)
            mesh_or_bm.free()
        else:
            me = mesh_or_bm
        o = bpy.data.objects.new(name, me)
        if mat and not me.materials:
            me.materials.append(mat)
        o.location = loc
        tmp.objects.link(o)
        return o

    ground = material("_render_ground", (0.72, 0.70, 0.64, 1))
    add("_ground", box_bm(-60, 60, -60, 60, -0.5, -0.001), ground)
    # the figure where each view can see one: on the plaza by the door, on the
    # deck, at the service door, in the dining room
    fig_mat = material("_render_figure", (0.85, 0.30, 0.25, 1))
    for k, loc in enumerate(((-0.75, -8.0, 0.0), (6.5, -1.0, DECK_TOP), (-5.0, 6.6, 0.0), (1.2, 2.6, FLOOR_TOP))):
        add(f"_figure{k}", figure.data.copy(), fig_mat, loc)
    # the plan's grid: 1 m lines, 5 m heavy, and a scale bar
    grid_mat = material("_render_grid", (0.25, 0.22, 0.20, 1))
    bm = None
    for x in range(-14, 15):
        w = 0.05 if x % 5 == 0 else 0.02
        bm = box_bm(x - w, x + w, -12, 12, 0.001, 0.003, bm)
    for y in range(-12, 13):
        w = 0.05 if y % 5 == 0 else 0.02
        bm = box_bm(-14, 14, y - w, y + w, 0.001, 0.003, bm)
    grid = add("_grid", bm, grid_mat)
    bar = add("_scale_bar", box_bm(11, 16, 8.6, 9.0, 0.002, 0.004), material("_render_bar", (0.05, 0.05, 0.05, 1)))
    curve = bpy.data.curves.new("_label", "FONT")
    curve.body = "5 m bar; 1 m grid, 5 m heavy. Top -Y: the plaza (north). Left +X: the deck (west, sunset)."
    curve.size = 0.55
    label = bpy.data.objects.new("_label", curve)
    label.location = (10.5, 9.75, 0.01)
    label.rotation_euler = (0, 0, math.pi)
    label.data.materials.append(bpy.data.materials["_render_bar"])
    tmp.objects.link(label)
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    tmp.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    tmp.objects.link(cam)
    scene.camera = cam

    def aim(obj, loc, target):
        obj.location = loc
        obj.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

    # (camera, target, lens, light from): light from the sea and the plaza unless said
    sea = (1.0, -0.8, 1.2)
    views = {
        "plaza_three_quarter": ((13.0, -17.0, 1.6), (-1.0, 0.0, 1.6), 28, sea),
        "steps_three_quarter": ((-17.0, -14.0, 1.6), (-1.0, 0.0, 1.6), 28, (-0.6, -1.0, 1.2)),
        "sunset_deck": ((24.0, 5.0, 1.6), (3.0, 0.0, 1.6), 32, sea),
        "back_service": ((-3.0, 17.0, 1.6), (-3.5, 2.0, 1.4), 28, (-0.7, 1.0, 1.1)),
        "interior_dining": ((-4.2, -3.4, 1.5), (6.0, 1.0, 1.0), 20, sea),
        "plan": (None, None, 34.0, (0.3, -0.3, 1.0)),
    }
    for tag, (loc, target, lens, light) in views.items():
        plan = loc is None
        grid.hide_render = not plan
        bar.hide_render = not plan
        label.hide_render = not plan
        aim(sun, (0, 0, 20), (-light[0], -light[1], 20 - light[2]))
        if plan:
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = lens
            cam.location = (0.0, -1.0, 40.0)
            cam.rotation_euler = (0.0, 0.0, math.pi)  # north (-Y) up, west (+X) left
        else:
            cam.data.type = "PERSP"
            cam.data.lens = lens
            aim(cam, loc, target)
        scene.render.filepath = os.path.join(folder, f"{name}_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)

    for o in list(tmp.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
    bpy.data.collections.remove(tmp)
    scene.world = old_world
    bpy.data.worlds.remove(world)


# --- the file ------------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != "pier_seafood_restaurant":
        raise SystemExit(f"pier_seafood_restaurant: open pier_seafood_restaurant.blend, not {name}")
    export, reference = bpy.data.collections["export"], bpy.data.collections["reference"]
    foreign = [o.name for o in export.objects if not o.get(TAG)]
    if export.objects and "--replace" not in argv:
        raise SystemExit(f"pier_seafood_restaurant: export already holds {[o.name for o in export.objects][:4]}...; "
                         "it may be hers. --replace builds over it")
    if foreign:
        print(f"pier_seafood_restaurant: replacing parts this tool did not make: {foreign}")
    for coll in (export, reference):
        for o in list(coll.objects):
            if o.get(TAG) or coll is export:
                bpy.data.objects.remove(o)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)
    figure = build_reference()
    build()
    out, lines = checks()
    print("pier_seafood_restaurant:")
    for line in out:
        print("  " + line)
    for line in lines:
        print(line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name, figure)


main()
