"""A restaurant standing over the water on timber piles, from Christina's
photograph of a classic Californian harbour restaurant (2026-10-02: "a
restaurant on the water"; "it can be for anything"; "we can always build
another pier in town"). A general, reusable building, not one of the beach
town's planned seafood restaurants; where it stands is decided later. First
model pass.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/waterfront_restaurant.blend \
        --python tools/blender/waterfront_restaurant.py -- [--replace] [--save] [--render <folder>]

Builds the building into `export`, one object a part, and a `ground_line`
marker, a 1.7 m figure and the footprint outlines into the locked `reference`.
Rerunning rebuilds both from scratch (`--replace` while `export` holds
anything, which may be hers). `--render <folder>` shoots Eevee frames from
temporary cameras that are never saved; `--save` saves the file before any
render.

**Frame.** Real metres, Z up. z = 0 is the water's surface and the origin is
the middle of the 26 x 14 m deck; the piles go 2.5 m below the water, so
`ground_line` at the origin tells Check the building stands in the water on
purpose (as the hardscape kit's walls stand in the ground). The long glazed
dining front faces -Y here (+Z in Godot, as every prop); the entrance doors
and the gangway stub are on +X, where the photograph's seawall promenade runs
past the building's right end. The deck is 2 m above the water.

**What the photograph shows, and what is built.** A two-storey block of dark
timber under a steep shingled gable running along its length, with a big
cross-gable on the front, rows of small warm-lit windows upstairs and an
arched window in the cross-gable; on the ridge a small square lantern with a
pyramid roof and a weathervane mast; at the right end a square tower with a
pyramid roof rising above the roof line; a narrow stair climbing the roof's
front slope diagonally toward the lantern; and round the ground floor, on the
front and both ends, a glazed dining room, a long glass band on a low solid
wall under a low-pitched roof just above the glass, wrapping the dark block.
A gangway joins the promenade at the right end and a blank cream banner stands
by the entrance (no text: the park is unbranded). Sizes are the lead's reading
of the photo: about 26 m long and 14 m deep with the glass room, the ridge
about 11 m above the deck, the lantern's top about 14 m.

**House style** (`prop-pipeline.md`, Standards applied): chunky and few, the
silhouette faithful; shingles, boards, the window panes beyond their frames
and the lantern's louvres are painting, not geometry. The glass room's frames
are chunky mullions only where they read; every pane is one glass stand-in.
Stand-in materials by surface (`waterfront_<surface>`): timber, shingle,
trim, glass, piles, deck, metal, fabric. No interior beyond what the glass
shows: the deck is the dining room's floor and the block's wall its back wall.

**Shapes overlap, never share a plane** (`AGENTS.md`, Geometry): walls start
10 cm inside the deck and run 10 cm up into their roof slabs; the piles end
inside the cap beams and the cap beams inside the deck; posts stop inside
rails and sills inside walls; the gangway's top rises 1.2 cm over its metre so
it is not the deck's plane while it meets the deck's edge with no lip (the
player has no step-up). The stair is a catwalk on legs: level treads on two
stringers, each leg as long as the roof under it needs.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

TAG = "kyt_waterfront"  # on everything this tool makes, so a rerun removes only its own
NAME = "waterfront_restaurant"

# --- the plan ---------------------------------------------------------------------

DECK_Z = 2.0                     # the deck's top above the water (z = 0)
DECK_T = 0.40
DECK_X, DECK_Y = 13.0, 7.0       # half the 26 x 14 m deck
EDGE = 0.18                      # the deck's edge beam, square
EDGE_PROUD = 0.03                # proud of the deck's face, so it is not the deck's plane
EDGE_Z1 = DECK_Z + 0.14
GANGWAY_W, GANGWAY_LEN, GANGWAY_IN = 2.4, 1.0, 0.3   # a stub: where the real gangway starts
GANGWAY_RISE, GANGWAY_T = 0.012, 0.30
RAIL_TOP, POST = 1.05, 0.10

PILE_R, PILE_SIDES, PILE_BOTTOM = 0.20, 12, -2.5
PILES_X = (-12.0, -8.0, -4.0, 0.0, 4.0, 8.0, 12.0)
PILES_Y = (-6.0, -2.0, 2.0, 6.0)
CAP = 0.32                       # the cap beams on each pile row, square
CAP_Z1 = DECK_Z - DECK_T + 0.05  # lapped 5 cm into the deck
CAP_Z0 = CAP_Z1 - CAP
PILE_TOP = CAP_Z0 + 0.20         # inside the cap beam
BRACE_W, BRACE_T = 0.14, 0.26    # the cross bracing: across the row, in its plane
BRACE_Z0, BRACE_Z1 = 0.30, CAP_Z0 - 0.05
BRACE_OFF = PILE_R + BRACE_W / 2 - 0.02   # on the piles' outer faces, lapping 2 cm in

# Everything that stands on the deck starts inside it, each kind at its own
# depth, so no two buried bottoms lie in one plane (the block, the bay, the
# tower and the glass room's stubs all ended at one plane on 2026-10-02).
SINK = {"walls": 0.10, "bay": 0.08, "tower": 0.12, "glass_wall": 0.06, "edge": 0.14,
        "posts": 0.05, "door": 0.04, "banner": 0.07}

# the main block: two storeys of dark timber under the gable
BLOCK_X0, BLOCK_X1 = -9.5, 8.5
BLOCK_Y0, BLOCK_Y1 = -2.5, 6.0
EAVE_Z = DECK_Z + 6.4
PITCH = math.radians(48)
TANP, SINP, COSP = math.tan(PITCH), math.sin(PITCH), math.cos(PITCH)
RIDGE_Y = (BLOCK_Y0 + BLOCK_Y1) / 2
HALF_SPAN = (BLOCK_Y1 - BLOCK_Y0) / 2
RIDGE_Z = EAVE_Z + HALF_SPAN * TANP
ROOF_T = 0.30                    # roof slabs are measured vertically
EAVE_OUT, GABLE_OUT = 0.6, 0.5
WALL_INTO_ROOF = 0.10            # walls run this far up into their roof slab

# the cross gable on the front: a shallow bay rising through the glass roof
CG_X0, CG_X1 = -3.6, 2.4
CG_PROUD = 0.25
CG_Y_FACE, CG_Y_BACK = BLOCK_Y0 - CG_PROUD, 0.0   # its back is buried in the block
CG_XC, CG_HALF = (CG_X0 + CG_X1) / 2, (CG_X1 - CG_X0) / 2
CG_TAN = math.tan(math.radians(45))
CG_EAVE_Z = EAVE_Z
CG_APEX_Z = CG_EAVE_Z + CG_HALF * CG_TAN
CG_ROOF_OUT, CG_ROOF_Y_BACK = 0.5, 0.9            # past Y = 0.5 its ridge is under the main roof

# the end tower, at the front-right corner, proud of both walls
TW_X0, TW_X1 = 5.0, 8.8
TW_Y0, TW_Y1 = BLOCK_Y0 - 0.3, 1.0
TW_EAVE_Z = 13.0                 # its roof's underside at the wall line: above the main roof there
TW_HALF = (TW_X1 - TW_X0) / 2
TW_ROOF_OUT, TW_ROOF_T = 0.45, 0.25
TW_TAN = math.tan(math.radians(45))

# the lantern on the ridge, over the cross gable
CUP_XC, CUP_YC, CUP_HALF = CG_XC, RIDGE_Y, 1.0
CUP_BASE_Z0 = RIDGE_Z + ROOF_T - CUP_HALF * TANP - 0.3   # under the roof's surface at its sides
CUP_BASE_Z1 = RIDGE_Z + ROOF_T + 0.3
CUP_GLASS_Z1 = CUP_BASE_Z1 + 0.85
CUP_POST = 0.22
CUP_ROOF_OUT, CUP_ROOF_T = 0.35, 0.20
CUP_TAN = math.tan(math.radians(45))

# the glazed dining room: a low wall, a glass band, a head beam, a low roof
GR_X0, GR_X1, GR_Y0, GR_YB = -12.3, 11.3, -6.3, 5.0   # outer faces; the end wings return to the block at GR_YB
GR_T = 0.30
GR_C = GR_T / 2
GR_WALL_TOP = DECK_Z + 0.9
SILL_Z0, SILL_Z1, SILL_W = GR_WALL_TOP - 0.02, GR_WALL_TOP + 0.10, GR_T + 0.08
HEAD_Z0, HEAD_Z1, HEAD_W = DECK_Z + 2.6, DECK_Z + 2.9, GR_T + 0.04
GLASS_Z0, GLASS_Z1, GLASS_T = SILL_Z1 - 0.05, HEAD_Z0 + 0.05, 0.04
MULLION, MULLION_PITCH, CORNER_POST = 0.16, 2.4, GR_T + 0.06
GR_TAN = math.tan(math.radians(12))
GR_ROOF_UNDER = HEAD_Z1 - 0.05   # the roof's underside at the outer wall faces, lapping the head beam
GR_ROOF_OUT, GR_ROOF_T, GR_ROOF_IN = 0.5, 0.25, 0.2

# the entrance, in the +X glass wall, and the service door on the back
DOOR_Y = (GR_Y0 + GR_YB) / 2
DOOR_CLEAR, DOOR_H = 2.0, 2.3
FRAME, FRAME_PROUD, FRAME_LAP = 0.15, 0.03, 0.02
DOOR_GAP = DOOR_CLEAR + 2 * FRAME - 2 * FRAME_LAP   # the opening in the wall: the jambs lap 2 cm in
DOOR_HEAD_TOP = HEAD_Z0 + 0.08                      # inside the head beam, above the glass's top
# The glass room's layers end at their own depth inside the block and their
# own distance short of the entrance jambs, so no two end faces share a plane.
LAYER_ENDS = {"wall": (0.10, 0.0), "sill": (0.12, 0.01), "glass": (0.14, -0.01), "head": (0.16, 0.0)}
LEAF_T, LEAF_LIFT = 0.05, 0.02
SERVICE_X, SERVICE_W, SERVICE_H = 6.0, 1.0, 2.2

# windows: proud frames and a pane just off the wall; the panes' bars are painting
W_F, W_PROUD, W_IN = 0.12, 0.05, 0.02
UPPER = (DECK_Z + 4.4, DECK_Z + 5.9)
LOWER = (DECK_Z + 1.0, DECK_Z + 2.4)
TOWER_UPPER = (DECK_Z + 8.2, DECK_Z + 9.7)
ARCH = (CG_XC, 1.8, DECK_Z + 6.9, DECK_Z + 7.9)   # centre, width, sill, springline; apex a half width higher

# the roof stair: from near the front eave, right of the cross gable, up to the lantern
STAIR_FOOT, STAIR_HEAD = (4.5, -2.6), (0.8, 1.4)
STAIR_W, STAIR_LIFT, TREADS = 0.80, 0.60, 20    # the tread line is LIFT above the roof's surface

# the banner by the entrance, facing arrivals from the gangway
BANNER_X, BANNER_Y = 12.25, (-2.55, -4.45)
BANNER_Z = (DECK_Z + 1.25, DECK_Z + 2.25)
BANNER_POST_H = 2.5

BEVEL = 0.03

# colours are stand-ins for the painting: dark stained timber, dark shingle,
# cream trim, warm glass, near-black piles, weathered deck, dark metal, cream cloth
COLOURS = {
    "timber": (0.17, 0.10, 0.06, 1.0),
    "shingle": (0.12, 0.105, 0.095, 1.0),
    "trim": (0.90, 0.86, 0.76, 1.0),
    "glass": (0.72, 0.80, 0.84, 0.45),
    "piles": (0.09, 0.07, 0.05, 1.0),
    "deck": (0.44, 0.37, 0.28, 1.0),
    "metal": (0.24, 0.25, 0.27, 1.0),
    "fabric": (0.93, 0.89, 0.78, 1.0),
}

# The faces windows and doors sit on: the axis across the face, its position,
# and the sign of outward. An opening on a 'y' face is given in (x, z), on an
# 'x' face in (y, z).
FACES = {
    "front": ("y", BLOCK_Y0, -1), "back": ("y", BLOCK_Y1, 1),
    "left": ("x", BLOCK_X0, -1), "right": ("x", BLOCK_X1, 1),
    "bay": ("y", CG_Y_FACE, -1),
    "tower_front": ("y", TW_Y0, -1), "tower_right": ("x", TW_X1, 1),
}
# (face, centre, width, (z0, z1))
WINDOWS = [
    ("front", -8.2, 1.4, UPPER), ("front", -5.9, 1.4, UPPER), ("front", 3.7, 1.4, UPPER),
    ("bay", -2.6, 1.4, UPPER), ("bay", -0.6, 1.4, UPPER), ("bay", 1.4, 1.4, UPPER),
    ("tower_front", 6.15, 1.1, UPPER), ("tower_front", 7.65, 1.1, UPPER),
    ("tower_front", 6.15, 1.1, TOWER_UPPER), ("tower_front", 7.65, 1.1, TOWER_UPPER),
    ("tower_right", -1.85, 1.1, UPPER), ("tower_right", -0.1, 1.1, UPPER),
    ("tower_right", -1.85, 1.1, TOWER_UPPER), ("tower_right", -0.1, 1.1, TOWER_UPPER),
    ("left", 0.0, 1.4, UPPER), ("left", 3.5, 1.4, UPPER), ("left", RIDGE_Y, 1.0, (DECK_Z + 7.6, DECK_Z + 8.8)),
    ("right", 3.2, 1.4, UPPER), ("right", 3.2, 1.0, (DECK_Z + 7.6, DECK_Z + 8.8)),
] + [("back", x, 1.4, UPPER) for x in (-8.2, -6.0, -3.8, -1.6, 0.6, 2.8, 5.0, 7.2)] \
  + [("back", x, 1.4, LOWER) for x in (-7.1, -3.8, -0.5, 2.8)]


# --- building blocks ----------------------------------------------------------------

def material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        if mat.node_tree is None:
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
    (x, z), 'z' gives (x, y)). `axis` may instead be a function (a, b, t) -> xyz,
    for a prism in a tilted frame. Several prisms may share one bmesh."""
    bm = bm or bmesh.new()

    def at(a, b, t):
        if callable(axis):
            return axis(a, b, t)
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


def ring_bm(outer, inner, axis, lo, hi, bm=None):
    """A frame: two loops of (a, b) points with the same count, matched point for
    point, extruded from lo to hi across `axis`. Its faces are quads between the
    loops, so no hole-filling is needed and any outline works, an arch included."""
    bm = bm or bmesh.new()

    def at(a, b, t):
        if axis == "x":
            return (t, a, b)
        if axis == "y":
            return (a, t, b)
        return (a, b, t)

    n = len(outer)
    on = [bm.verts.new(at(a, b, lo)) for a, b in outer]
    of = [bm.verts.new(at(a, b, hi)) for a, b in outer]
    inn = [bm.verts.new(at(a, b, lo)) for a, b in inner]
    inf = [bm.verts.new(at(a, b, hi)) for a, b in inner]
    for k in range(n):
        j = (k + 1) % n
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


def bar(p0, p1, w, h, bm=None):
    """A box along the segment p0-p1: `w` wide across it (level), `h` thick in
    the vertical plane through it, its ends square to it."""
    bm = bm or bmesh.new()
    p0, p1 = Vector(p0), Vector(p1)
    t = (p1 - p0).normalized()
    side = t.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((0, -1, 0))
    side.normalize()
    up = side.cross(t).normalized()
    v = [bm.verts.new(p + side * (sw * w / 2) + up * (su * h / 2))
         for p in (p0, p1) for su in (-1, 1) for sw in (-1, 1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (1, 5, 7, 3), (3, 7, 6, 2), (2, 6, 4, 0)):
        bm.faces.new([v[i] for i in f])
    return bm


def obox(centre, direction, length, width, z0, z1, bm=None):
    """A level box turned about Z: `length` along `direction` (a unit xy vector)."""
    bm = bm or bmesh.new()
    cx, cy = centre
    dx, dy = direction
    sx, sy = -dy, dx
    corners = [(cx + dx * a + sx * b, cy + dy * a + sy * b)
               for a, b in ((-length / 2, -width / 2), (length / 2, -width / 2),
                            (length / 2, width / 2), (-length / 2, width / 2))]
    return prism(corners, "z", z0, z1, bm)


def heightfield_slab(polys, ztop, thickness, bm=None):
    """A slab under a piecewise-planar surface: `polys` are plan polygons
    (convex, sharing vertices exactly where they meet), `ztop(x, y)` the top
    surface, the underside `thickness` lower. Edges used by one polygon only
    get a vertical side face: the fascia. One closed solid, so a roof's hips
    and ridges are its own edges and no two slabs meet in a plane."""
    bm = bm or bmesh.new()
    top, bot, used = {}, {}, {}

    def key(p):
        return (round(p[0], 5), round(p[1], 5))

    for poly in polys:
        for p in poly:
            k = key(p)
            if k not in top:
                z = ztop(p[0], p[1])
                top[k] = bm.verts.new((p[0], p[1], z))
                bot[k] = bm.verts.new((p[0], p[1], z - thickness))
    for poly in polys:
        ks = [key(p) for p in poly]
        bm.faces.new([top[k] for k in ks])
        bm.faces.new([bot[k] for k in reversed(ks)])
        for i in range(len(ks)):
            e = (ks[i], ks[(i + 1) % len(ks)])
            used[frozenset(e)] = used.get(frozenset(e), []) + [e]
    for e, uses in used.items():
        if len(uses) == 1:
            a, b = uses[0]
            bm.faces.new((top[a], top[b], bot[b], bot[a]))
    return bm


def pyramid(xc, yc, half, eave_z, tan_p, thickness):
    """A square pyramid roof slab: `eave_z` is the underside at its eave edge,
    `half` from the centre, rising at `tan_p`; four hips meet at the apex."""
    c = [(xc - half, yc - half), (xc + half, yc - half), (xc + half, yc + half), (xc - half, yc + half)]
    polys = [[c[i], c[(i + 1) % 4], (xc, yc)] for i in range(4)]
    return heightfield_slab(polys, lambda x, y: eave_z + (half - max(abs(x - xc), abs(y - yc))) * tan_p + thickness,
                            thickness)


def arch_pts(half_w, sill, spring, n=12):
    """An arched opening's outline, (a, z): up the left side, over the half
    circle, down the right side; the closing edge is the sill."""
    pts = [(-half_w, sill)]
    for i in range(n + 1):
        a = math.pi - math.pi * i / n
        pts.append((half_w * math.cos(a), spring + half_w * math.sin(a)))
    pts.append((half_w, sill))
    return pts


def finish(name, bm, mats, *, bevel=BEVEL, segments=2, smooth=True, smooth_deg=40.0, unwrap="facets"):
    """A bmesh into an object in `export`: n-gons triangulated, the bevel
    applied, cleaned for unwrap_parts.py, smoothed by angle, and tagged."""
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="EAR_CLIP")
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections["export"].objects.link(obj)
    for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
        mesh.materials.append(m)
    obj[TAG] = True
    if unwrap:
        obj["kyt_unwrap"] = unwrap
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35)
        mod.harden_normals = False
        apply_modifiers(obj)
    clean(obj)
    if smooth:
        smooth_by_angle(obj, smooth_deg)
    return obj


def apply_modifiers(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    # Slot by slot, never `materials.clear()`: in Blender 5 clearing resets every
    # face's material index to 0, so a two-material part comes out all one
    # (the sky ride gondola's tub, 2026-10-02). The evaluated mesh keeps the
    # object's slots; only fill them if it came back without any.
    if len(new.materials) == 0:
        for m in old.materials:
            new.materials.append(m)
    bpy.data.meshes.remove(old)


def clean(obj):
    """Merge coincident vertices and drop faces with no area. unwrap_parts.py
    works on a merged copy and needs the same faces in the same order, so a
    part must already be clean (the picnic tables' trestles, 2026-10-02)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bad = [f for f in bm.faces if f.calc_area() < 1e-9]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


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


def roof(name, bm, mats, **kw):
    """A roof slab: shingle on its top, trim on its fascia and soffit, one
    piece. Hips and ridges stay crisp (smooth only below 8 degrees)."""
    obj = finish(name, bm, [mats["shingle"], mats["trim"]], smooth_deg=8.0, **kw)
    for p in obj.data.polygons:
        p.material_index = 0 if p.normal.z > 0.5 else 1
    return obj


def roof_top_front(y):
    """The main roof's top surface on its front slope."""
    return EAVE_Z + ROOF_T + (y - BLOCK_Y0) * TANP


# --- the building ----------------------------------------------------------------------

def build_piles(mats):
    """The pile grid, each pile its own cylinder (unwrap_parts.py classifies
    them itself); cap beams along each row into the deck; cross bracing on
    the four outer rows, lying on the piles' outer faces."""
    for i, x in enumerate(PILES_X):
        for j, y in enumerate(PILES_Y):
            finish(f"pile_{i}{j}", cylinder_bm("z", (x, y), PILE_R, PILE_BOTTOM, PILE_TOP, PILE_SIDES),
                   mats["piles"], bevel=0, unwrap=None)
    bm = None
    h = CAP / 2
    for y in PILES_Y:
        bm = box_bm(PILES_X[0] - 0.5, PILES_X[-1] + 0.5, y - h, y + h, CAP_Z0, CAP_Z1, bm)
    finish("pile_caps", bm, mats["piles"], bevel=0.02, segments=1)
    bm = None

    def brace(a, b):
        nonlocal bm
        a, b = Vector(a), Vector(b)
        t = (b - a).normalized() * 0.2   # run on through the pile, so the bays' braces meet
        bm = bar(a - t, b + t, BRACE_W, BRACE_T, bm)

    for y, s in ((PILES_Y[0], -1), (PILES_Y[-1], 1)):
        yo = y + s * BRACE_OFF
        for xa, xb in zip(PILES_X, PILES_X[1:]):
            brace((xa, yo, BRACE_Z0), (xb, yo, BRACE_Z1))
            brace((xa, yo, BRACE_Z1), (xb, yo, BRACE_Z0))
    for x, s in ((PILES_X[0], -1), (PILES_X[-1], 1)):
        xo = x + s * BRACE_OFF
        for ya, yb in zip(PILES_Y, PILES_Y[1:]):
            brace((xo, ya, BRACE_Z0), (xo, yb, BRACE_Z1))
            brace((xo, ya, BRACE_Z1), (xo, yb, BRACE_Z0))
    finish("pile_bracing", bm, mats["piles"], bevel=0)


def gangway_top(x):
    return DECK_Z + (x - DECK_X) * GANGWAY_RISE / GANGWAY_LEN


def build_deck(mats):
    finish("deck", box_bm(-DECK_X, DECK_X, -DECK_Y, DECK_Y, DECK_Z - DECK_T, DECK_Z), mats["deck"], bevel=0.04)
    # the edge beam round the deck, open at the gangway
    cx, cy = DECK_X + EDGE_PROUD - EDGE / 2, DECK_Y + EDGE_PROUD - EDGE / 2
    g = GANGWAY_W / 2 + 0.05
    path = [(cx, DOOR_Y + g), (cx, cy), (-cx, cy), (-cx, -cy), (cx, -cy), (cx, DOOR_Y - g)]
    finish("deck_edge", prism(mitred_path(path, EDGE), "z", DECK_Z - SINK["edge"], EDGE_Z1), mats["deck"], bevel=0.02, segments=1)
    # the gangway stub: lapped into the deck, its top a hair off level so it
    # meets the deck's top at the edge without a lip and without sharing its plane
    x0, x1 = DECK_X - GANGWAY_IN, DECK_X + GANGWAY_LEN
    poly = [(x0, DECK_Z - GANGWAY_T), (x1, DECK_Z - GANGWAY_T), (x1, gangway_top(x1)), (x0, gangway_top(x0))]
    finish("gangway", prism(poly, "y", DOOR_Y - GANGWAY_W / 2, DOOR_Y + GANGWAY_W / 2), mats["deck"], bevel=0.03, segments=1)
    bm = None
    for sy in (-1, 1):
        yc = DOOR_Y + sy * (GANGWAY_W / 2 - POST / 2 - 0.02)
        for x in (DECK_X + 0.12, x1 - 0.10):
            bm = box_bm(x - POST / 2, x + POST / 2, yc - POST / 2, yc + POST / 2,
                        gangway_top(x) - 0.06, gangway_top(x) + RAIL_TOP - 0.04, bm)
        bm = bar((DECK_X + 0.04, yc, gangway_top(DECK_X) + RAIL_TOP), (x1 - 0.02, yc, gangway_top(x1) + RAIL_TOP),
                 0.12, 0.08, bm)
    finish("gangway_rails", bm, mats["trim"], bevel=0)


def build_block(mats):
    """The block is one pentagon prism, walls and gables together, its slopes
    parallel to the roof's underside and 10 cm up inside the slab; the cross
    gable's bay the same along Y, 25 cm proud of the front wall so its face is
    not the wall's plane; the tower a box up into its own roof."""
    z0, top, apex = DECK_Z - SINK["walls"], EAVE_Z + WALL_INTO_ROOF, RIDGE_Z + WALL_INTO_ROOF
    pent = [(BLOCK_Y0, z0), (BLOCK_Y1, z0), (BLOCK_Y1, top), (RIDGE_Y, apex), (BLOCK_Y0, top)]
    finish("walls", prism(pent, "x", BLOCK_X0, BLOCK_X1), mats["timber"])
    z0, top, apex = DECK_Z - SINK["bay"], CG_EAVE_Z + WALL_INTO_ROOF, CG_APEX_Z + WALL_INTO_ROOF
    pent = [(CG_X0, z0), (CG_X1, z0), (CG_X1, top), (CG_XC, apex), (CG_X0, top)]
    finish("walls_bay", prism(pent, "y", CG_Y_FACE, CG_Y_BACK), mats["timber"])
    finish("tower", box_bm(TW_X0, TW_X1, TW_Y0, TW_Y1, DECK_Z - SINK["tower"], TW_EAVE_Z + WALL_INTO_ROOF), mats["timber"])


def build_roofs(mats):
    # the main gable: two slopes sharing the ridge
    x0, x1 = BLOCK_X0 - GABLE_OUT, BLOCK_X1 + GABLE_OUT
    y0, y1 = BLOCK_Y0 - EAVE_OUT, BLOCK_Y1 + EAVE_OUT
    polys = [[(x0, y0), (x1, y0), (x1, RIDGE_Y), (x0, RIDGE_Y)], [(x0, RIDGE_Y), (x1, RIDGE_Y), (x1, y1), (x0, y1)]]
    roof("roof_main", heightfield_slab(polys, lambda x, y: EAVE_Z + (HALF_SPAN - abs(y - RIDGE_Y)) * TANP + ROOF_T,
                                       ROOF_T), mats)
    # the cross gable's roof, run back until it is under the main roof
    bx0, bx1 = CG_X0 - CG_ROOF_OUT, CG_X1 + CG_ROOF_OUT
    by0, by1 = CG_Y_FACE - CG_ROOF_OUT, CG_ROOF_Y_BACK
    polys = [[(bx0, by0), (CG_XC, by0), (CG_XC, by1), (bx0, by1)], [(CG_XC, by0), (bx1, by0), (bx1, by1), (CG_XC, by1)]]
    roof("roof_bay", heightfield_slab(polys, lambda x, y: CG_EAVE_Z + (CG_HALF - abs(x - CG_XC)) * CG_TAN + ROOF_T,
                                      ROOF_T), mats)
    # the tower's pyramid: its underside TW_EAVE_Z at the wall line
    roof("roof_tower", pyramid((TW_X0 + TW_X1) / 2, (TW_Y0 + TW_Y1) / 2, TW_HALF + TW_ROOF_OUT,
                               TW_EAVE_Z - TW_ROOF_OUT * TW_TAN, TW_TAN, TW_ROOF_T), mats)
    # the glass room's roof: a shed round three sides, hipped at the two
    # front corners, 0.5 m past the glass walls, cut 0.2 m inside the block's
    # walls. Its height is the distance to the nearest outer wall face, so
    # the hips are the 45-degree lines from the eave corners.
    xl, xr, yo = GR_X0 - GR_ROOF_OUT, GR_X1 + GR_ROOF_OUT, GR_Y0 - GR_ROOF_OUT
    yi, yb = BLOCK_Y0 + GR_ROOF_IN, GR_YB + GR_ROOF_OUT
    xli, xri = BLOCK_X0 + GR_ROOF_IN, BLOCK_X1 - GR_ROOF_IN
    t = yi - yo
    A, A2 = (xl, yo), (xr, yo)
    B, B2 = (xl + t, yi), (xr - t, yi)
    C, C2 = (xli, yi), (xri, yi)
    D, D2 = (xli, yb), (xri, yb)
    E, E2 = (xl, yb), (xr, yb)
    polys = [[A, B, C], [A, C, D, E], [A, A2, B2, B], [A2, E2, D2, C2], [A2, C2, B2]]

    def ztop(x, y):
        return GR_ROOF_UNDER + min(y - GR_Y0, x - GR_X0, GR_X1 - x) * GR_TAN + GR_ROOF_T

    roof("roof_glass_room", heightfield_slab(polys, ztop, GR_ROOF_T), mats)


def mast(name, x, y, z0, z1, mats, arrow=False):
    """A slim mast with a ball at its top; the lantern's carries a weathervane
    arrow pointing out to the water (-Y)."""
    bm = cylinder_bm("z", (x, y), 0.045, z0, z1 - 0.1, 10)
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.11, matrix=Matrix.Translation((x, y, z1 - 0.1)))
    if arrow:
        za = z1 - 0.5
        pts = [(y - 0.55, za), (y - 0.25, za + 0.12), (y - 0.25, za + 0.04), (y + 0.30, za + 0.04),
               (y + 0.30, za + 0.11), (y + 0.42, za + 0.11), (y + 0.42, za - 0.11), (y + 0.30, za - 0.11),
               (y + 0.30, za - 0.04), (y - 0.25, za - 0.04), (y - 0.25, za - 0.12)]
        bm = prism(pts, "x", x - 0.012, x + 0.012, bm)
    finish(name, bm, mats["metal"], bevel=0)


def build_cupola(mats):
    h = CUP_HALF
    finish("cupola_base", box_bm(CUP_XC - h, CUP_XC + h, CUP_YC - h, CUP_YC + h, CUP_BASE_Z0, CUP_BASE_Z1), mats["timber"])
    g = h - 0.08
    finish("cupola_glass", box_bm(CUP_XC - g, CUP_XC + g, CUP_YC - g, CUP_YC + g, CUP_BASE_Z1 - 0.03, CUP_GLASS_Z1 + 0.03),
           mats["glass"], bevel=0)
    bm = None
    p = CUP_POST / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = CUP_XC + sx * (h - p + 0.01), CUP_YC + sy * (h - p + 0.01)   # 1 cm proud of the base
            bm = box_bm(cx - p, cx + p, cy - p, cy + p, CUP_BASE_Z1 - 0.05, CUP_GLASS_Z1 + 0.06, bm)
    finish("cupola_posts", bm, mats["trim"], bevel=0)
    eave = CUP_GLASS_Z1 - CUP_ROOF_OUT * CUP_TAN   # the underside meets the glass top at the wall line
    roof("cupola_roof", pyramid(CUP_XC, CUP_YC, h + CUP_ROOF_OUT, eave, CUP_TAN, CUP_ROOF_T), mats)
    apex = eave + (h + CUP_ROOF_OUT) * CUP_TAN + CUP_ROOF_T
    mast("cupola_mast", CUP_XC, CUP_YC, apex - 0.35, apex + 0.85, mats, arrow=True)
    t_apex = TW_EAVE_Z - TW_ROOF_OUT * TW_TAN + (TW_HALF + TW_ROOF_OUT) * TW_TAN + TW_ROOF_T
    mast("tower_mast", (TW_X0 + TW_X1) / 2, (TW_Y0 + TW_Y1) / 2, t_apex - 0.3, t_apex + 0.65, mats)
    return apex + 0.85, t_apex + 0.65


def glass_room_paths(layer):
    """The dining room's wall as a path along its centre line: from inside the
    block's right end, round the three glass sides, into the block's left end;
    and the same split at the entrance. Each layer ends at its own depth."""
    into, short = LAYER_ENDS[layer]
    cx0, cx1 = GR_X0 + GR_C, GR_X1 - GR_C
    cy0, cyb = GR_Y0 + GR_C, GR_YB - GR_C
    g = DOOR_GAP / 2 + short
    full = [(BLOCK_X1 - into, cyb), (cx1, cyb), (cx1, cy0), (cx0, cy0), (cx0, cyb), (BLOCK_X0 + into, cyb)]
    gapped = [[(BLOCK_X1 - into, cyb), (cx1, cyb), (cx1, DOOR_Y + g)],
              [(cx1, DOOR_Y - g), (cx1, cy0), (cx0, cy0), (cx0, cyb), (BLOCK_X0 + into, cyb)]]
    return full, gapped


def build_glass_room(mats):
    def along(layer, width, z0, z1, whole=False):
        full, gapped = glass_room_paths(layer)
        bm = None
        for p in ([full] if whole else gapped):
            bm = prism(mitred_path(p, width), "z", z0, z1, bm)
        return bm

    finish("glass_room_wall", along("wall", GR_T, DECK_Z - SINK["glass_wall"], GR_WALL_TOP), mats["timber"])
    finish("glass_room_sill", along("sill", SILL_W, SILL_Z0, SILL_Z1), mats["trim"], bevel=0.02, segments=1)
    finish("glass_room_glass", along("glass", GLASS_T, GLASS_Z0, GLASS_Z1), mats["glass"], bevel=0)
    finish("glass_room_head", along("head", HEAD_W, HEAD_Z0, HEAD_Z1, whole=True), mats["trim"])
    full, _ = glass_room_paths("wall")
    # chunky mullions along each run, none in the entrance bay; a post at each corner
    bm = None
    m = MULLION / 2
    cx1 = full[1][0]
    for (xa, ya), (xb, yb) in zip(full, full[1:]):
        run = math.hypot(xb - xa, yb - ya)
        n = max(1, math.ceil(run / MULLION_PITCH))
        for k in range(1, n):
            x, y = xa + (xb - xa) * k / n, ya + (yb - ya) * k / n
            if abs(x - cx1) < 1e-6 and abs(y - DOOR_Y) < DOOR_GAP / 2 + 0.5:
                continue
            bm = box_bm(x - m, x + m, y - m, y + m, GLASS_Z0 - 0.02, GLASS_Z1 + 0.02, bm)
    finish("glass_room_mullions", bm, mats["trim"], bevel=0)
    bm = None
    p = CORNER_POST / 2
    for x, y in full[1:5]:
        bm = box_bm(x - p, x + p, y - p, y + p, DECK_Z - SINK["posts"], GLASS_Z1 + 0.02, bm)
    finish("glass_room_posts", bm, mats["trim"], bevel=0.02, segments=1)


def door_frame(name, axis, lo, hi, a0, a1, z_top, mats):
    """A U of two jambs and a head across the opening a0..a1, from inside the
    deck up to z_top, between lo and hi across the wall."""
    o0, o1 = a0 - FRAME, a1 + FRAME
    zb = DECK_Z - SINK["door"]
    u = [(o0, zb), (o0, z_top), (o1, z_top), (o1, zb), (a1, zb), (a1, z_top - FRAME - 0.2), (a0, z_top - FRAME - 0.2), (a0, zb)]
    finish(name, prism(u, axis, lo, hi), mats["trim"], segments=1)


def leaf(name, axis, hinge_a, width, direction, mid, height, mats):
    """A door leaf built with its hinge edge on its origin, at the floor, so a
    turn about its local Z swings it (Send's `kyt_hinge` knows only `top`)."""
    t = LEAF_T / 2
    if axis == "y":
        bm = box_bm(min(0.0, direction * width), max(0.0, direction * width), -t, t, 0.0, height)
        loc = (hinge_a, mid, DECK_Z + LEAF_LIFT)
    else:
        bm = box_bm(-t, t, min(0.0, direction * width), max(0.0, direction * width), 0.0, height)
        loc = (mid, hinge_a, DECK_Z + LEAF_LIFT)
    obj = finish(name, bm, mats["timber"], bevel=0.015, segments=1)
    obj.location = loc
    obj["kyt_hinge_edge"] = "side"
    return obj


def build_doors(mats):
    # the entrance: double doors in the +X glass wall, on the gangway's axis
    cx1 = GR_X1 - GR_C
    a0, a1 = DOOR_Y - DOOR_CLEAR / 2, DOOR_Y + DOOR_CLEAR / 2
    door_frame("door_frame", "x", cx1 - GR_C - FRAME_PROUD, cx1 + GR_C + FRAME_PROUD, a0, a1, DOOR_HEAD_TOP, mats)
    clear_h = DOOR_HEAD_TOP - FRAME - 0.2 - DECK_Z
    w = DOOR_CLEAR / 2 - 0.02
    leaf("door_l", "x", a0 + 0.01, w, 1, cx1, clear_h - LEAF_LIFT - 0.02, mats)
    leaf("door_r", "x", a1 - 0.01, w, -1, cx1, clear_h - LEAF_LIFT - 0.02, mats)
    # the service door on the back: a frame on the wall and a leaf set back
    # 1.5 cm in it, off the wall's face and the frame's
    a0, a1 = SERVICE_X - SERVICE_W / 2, SERVICE_X + SERVICE_W / 2
    door_frame("service_door_frame", "y", BLOCK_Y1 - W_IN, BLOCK_Y1 + W_PROUD + 0.01, a0, a1,
               DECK_Z + SERVICE_H + FRAME + 0.2, mats)
    leaf("service_door", "y", a0 + 0.01, SERVICE_W - 0.02, 1, BLOCK_Y1 + 0.02, SERVICE_H - LEAF_LIFT - 0.02, mats)


def build_windows(mats):
    """Every window as a proud frame and a pane just off the wall, two objects
    in all; the arched window in the cross gable among them."""
    frames = panes = None
    for face, c, w, (z0, z1) in WINDOWS:
        axis, pos, out = FACES[face]
        a0, a1 = c - w / 2, c + w / 2
        lo, hi = sorted((pos - out * W_IN, pos + out * W_PROUD))
        outer = [(a0 - W_F, z0 - W_F), (a1 + W_F, z0 - W_F), (a1 + W_F, z1 + W_F), (a0 - W_F, z1 + W_F)]
        inner = [(a0, z0), (a1, z0), (a1, z1), (a0, z1)]
        frames = ring_bm(outer, inner, axis, lo, hi, frames)
        lo, hi = sorted((pos + out * 0.01, pos + out * 0.03))
        panes = prism([(a0 - 0.02, z0 - 0.02), (a1 + 0.02, z0 - 0.02), (a1 + 0.02, z1 + 0.02), (a0 - 0.02, z1 + 0.02)],
                      axis, lo, hi, panes)
    xc, w, sill, spring = ARCH
    axis, pos, out = FACES["bay"]
    lo, hi = sorted((pos - out * W_IN, pos + out * W_PROUD))
    outer = [(xc + a, z) for a, z in arch_pts(w / 2 + W_F, sill - W_F, spring)]
    inner = [(xc + a, z) for a, z in arch_pts(w / 2, sill, spring)]
    frames = ring_bm(outer, inner, axis, lo, hi, frames)
    lo, hi = sorted((pos + out * 0.01, pos + out * 0.03))
    panes = prism([(xc + a, z) for a, z in arch_pts(w / 2 + 0.02, sill - 0.02, spring)], axis, lo, hi, panes)
    finish("window_frames", frames, mats["trim"], bevel=0)
    finish("window_glass", panes, mats["glass"], bevel=0)


def build_stair(mats):
    """A catwalk stair up the front slope to the lantern: level treads on two
    stringers that stand on legs, each leg as long as the roof under it asks,
    a rail each side. The tread line runs STAIR_LIFT above the roof's surface
    on the stair's centre line; the roof is higher under the uphill stringer
    and lower under the downhill one, which is what the legs take up."""
    (xa, ya), (xb, yb) = STAIR_FOOT, STAIR_HEAD
    za, zb = roof_top_front(ya) + STAIR_LIFT, roof_top_front(yb) + STAIR_LIFT
    plan = math.hypot(xb - xa, yb - ya)
    d = ((xb - xa) / plan, (yb - ya) / plan)
    lat = (d[1], -d[0])

    def P(f, s=0.0, dz=0.0):
        """A point on the stair: fraction f of the way up, s to the side, dz above the tread line."""
        return Vector((xa + (xb - xa) * f + lat[0] * s, ya + (yb - ya) * f + lat[1] * s, za + (zb - za) * f + dz))

    rise, going = (zb - za) / TREADS, plan / TREADS
    sw = STAIR_W / 2 - 0.04
    bm = None
    for s in (-sw, sw):
        bm = bar(P(-0.01, s, -0.14), P(1.01, s, -0.14), 0.08, 0.22, bm)
        for j in range(5):
            p = P(0.08 + 0.84 * j / 4, s)
            bm = box_bm(p.x - 0.04, p.x + 0.04, p.y - 0.04, p.y + 0.04, roof_top_front(p.y) - 0.05, p.z - 0.14, bm)
    finish("roof_stair_frame", bm, mats["metal"], bevel=0)
    bm = None
    for k in range(TREADS):
        top = za + rise * (k + 1)
        c = P((k + 0.5) / TREADS)
        bm = obox((c.x, c.y), d, going + 0.02, STAIR_W + 0.04, top - rise - 0.08, top, bm)
    finish("roof_stair_treads", bm, mats["metal"], bevel=0)
    bm = None
    for s in (-sw, sw):
        for j in range(5):
            p = P(0.06 + 0.88 * j / 4, s)
            bm = box_bm(p.x - 0.03, p.x + 0.03, p.y - 0.03, p.y + 0.03, p.z - 0.25, p.z + 0.92, bm)
        bm = bar(P(0.02, s, 0.95), P(1.0, s, 0.95), 0.06, 0.09, bm)
    finish("roof_stair_rails", bm, mats["metal"], bevel=0)
    return math.degrees(math.atan2(zb - za, plan)), rise, going


def build_banner(mats):
    bm = None
    for y in BANNER_Y:
        bm = box_bm(BANNER_X - 0.04, BANNER_X + 0.04, y - 0.04, y + 0.04, DECK_Z - SINK["banner"], DECK_Z + BANNER_POST_H, bm)
    finish("banner_posts", bm, mats["metal"], bevel=0)
    ya, yb = BANNER_Y[0] + 0.02, BANNER_Y[1] - 0.02   # ends inside the posts
    n = 8
    line = [(BANNER_X + 0.09 * math.sin(math.pi * k / n), ya + (yb - ya) * k / n) for k in range(n + 1)]
    finish("banner_cloth", prism(mitred_path(line, 0.015), "z", *BANNER_Z), mats["fabric"], bevel=0)


def build():
    mats = {k: material(f"waterfront_{k}", c) for k, c in COLOURS.items()}
    build_piles(mats)
    build_deck(mats)
    build_block(mats)
    build_roofs(mats)
    tops = build_cupola(mats)
    build_glass_room(mats)
    build_doors(mats)
    build_windows(mats)
    stair = build_stair(mats)
    build_banner(mats)
    return tops, stair


# --- the reference ------------------------------------------------------------------------

def outline(name, pts, z=0.0):
    """An edge-only outline in `reference`: shows in the viewport, never renders."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x, y, z) for x, y in pts], [(i, (i + 1) % len(pts)) for i in range(len(pts))], [])
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
    rect = [(-DECK_X, -DECK_Y), (DECK_X, -DECK_Y), (DECK_X, DECK_Y), (-DECK_X, DECK_Y)]
    outline("water_line_26x14", rect, 0.0)
    outline("deck_26x14", rect, DECK_Z)
    outline("block_18x8p5", [(BLOCK_X0, BLOCK_Y0), (BLOCK_X1, BLOCK_Y0), (BLOCK_X1, BLOCK_Y1), (BLOCK_X0, BLOCK_Y1)], DECK_Z)
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
    fig.location = (12.4, 1.5, DECK_Z)
    fig[TAG] = True
    ref.objects.link(fig)
    return fig


# --- checks ------------------------------------------------------------------------------

def checks(tops, stair):
    export = bpy.data.collections["export"]
    total, lines = 0, []
    for o in sorted(export.objects, key=lambda o: o.name):
        o.data.calc_loop_triangles()
        n = len(o.data.loop_triangles)
        total += n
        lines.append(f"    {o.name}: {n}")
    piles = sum(1 for o in export.objects if o.name.startswith("pile_") and o.name[5:].isdigit())
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in export.objects:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
    out = [
        f"deck {2 * DECK_X:.0f} x {2 * DECK_Y:.0f} m at {DECK_Z:.1f} m over the water, on {piles} piles to {PILE_BOTTOM:.1f} m; "
        f"gangway stub {GANGWAY_LEN:.1f} m toward +X at y = {DOOR_Y:.2f}",
        f"block {BLOCK_X1 - BLOCK_X0:.0f} x {BLOCK_Y1 - BLOCK_Y0:.1f} m, eave {EAVE_Z - DECK_Z:.1f} m and ridge "
        f"{RIDGE_Z + ROOF_T - DECK_Z:.1f} m above the deck ({math.degrees(PITCH):.0f} deg); cross gable {CG_X1 - CG_X0:.0f} m wide, "
        f"apex {CG_APEX_Z + ROOF_T - DECK_Z:.1f} m; tower {TW_X1 - TW_X0:.1f} m square, mast top {tops[1] - DECK_Z:.1f} m; "
        f"lantern {2 * CUP_HALF:.0f} m square, mast top {tops[0] - DECK_Z:.1f} m",
        f"glass room {GR_X1 - GR_X0:.1f} m long, {BLOCK_Y0 - GR_Y0:.1f} m deep in front and {BLOCK_X0 - GR_X0:.1f} m at the ends; "
        f"low wall {GR_WALL_TOP - DECK_Z:.1f} m, glass {GLASS_Z0 - DECK_Z:.2f} to {GLASS_Z1 - DECK_Z:.2f} m, "
        f"roof {GR_ROOF_UNDER - DECK_Z:.2f} m at the eave rising {math.degrees(math.atan(GR_TAN)):.0f} deg",
        f"entrance {DOOR_CLEAR:.1f} x {DOOR_H:.1f} m clear; roof stair {stair[0]:.0f} deg, {TREADS} treads of "
        f"{stair[1] * 100:.0f} cm rise and {stair[2] * 100:.0f} cm going",
        f"extent x {lo.x:.2f}..{hi.x:.2f}, y {lo.y:.2f}..{hi.y:.2f}, z {lo.z:.2f}..{hi.z:.2f} "
        f"(centre {(lo.x + hi.x) / 2:.2f}, {(lo.y + hi.y) / 2:.2f})",
        f"{len(export.objects)} parts, {total} triangles, materials "
        + ", ".join(sorted({m.name for o in export.objects for m in o.data.materials})),
    ]
    return out, lines


# --- renders ------------------------------------------------------------------------------

def render(folder, name, figure):
    """Eevee frames from temporary cameras, lights, water and figures, none of
    which are saved: everything made here is removed after. The dusk frame
    lends the glass a warm emission for its duration only."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    try:
        scene.eevee.taa_render_samples = 32
        scene.eevee.use_shadows = True
    except AttributeError:
        pass
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    world = bpy.data.worlds.new("_render_world")
    if world.node_tree is None:
        world.use_nodes = True
    background = world.node_tree.nodes["Background"]
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

    water = material("_render_water", (0.13, 0.24, 0.32, 1))
    water.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.28
    add("_water", box_bm(-200, 200, -200, 200, -0.3, -0.002), water)
    fig_mat = material("_render_figure", (0.85, 0.30, 0.25, 1))
    figures = [add(f"_figure{k}", figure.data.copy(), fig_mat, loc)
               for k, loc in enumerate(((12.4, 1.5, DECK_Z), (-11.0, -6.75, DECK_Z), (DECK_X + 0.6, DOOR_Y + 0.3, DECK_Z + 0.007),
                                        (-3.0, -4.5, DECK_Z)))]
    # the plan's grid: 1 m lines, 5 m heavy, shown in the plan only
    grid_mat = material("_render_grid", (0.25, 0.22, 0.20, 1))
    bm = None
    for x in range(-16, 17):
        w = 0.05 if x % 5 == 0 else 0.015
        bm = box_bm(x - w, x + w, -10, 10, 0.001, 0.003, bm)
    for y in range(-10, 11):
        w = 0.05 if y % 5 == 0 else 0.015
        bm = box_bm(-16, 16, y - w, y + w, 0.001, 0.003, bm)
    grid = add("_grid", bm, grid_mat)
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.angle = math.radians(2)
    tmp.objects.link(sun)
    lamps = []
    for k, loc in enumerate([(x, -4.4, DECK_Z + 2.0) for x in (-10, -6, -2, 2, 6, 10)]
                            + [(-11.0, 0.5, DECK_Z + 2.0), (10.0, 2.5, DECK_Z + 2.0), (CUP_XC, CUP_YC, CUP_BASE_Z1 + 0.4)]):
        light = bpy.data.lights.new(f"_lamp{k}", "POINT")
        light.energy = 600 if k < 8 else 250
        light.color = (1.0, 0.72, 0.45)
        light.shadow_soft_size = 0.5
        lamp = bpy.data.objects.new(f"_lamp{k}", light)
        lamp.location = loc
        tmp.objects.link(lamp)
        lamps.append(lamp)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    tmp.objects.link(cam)
    scene.camera = cam
    glass = bpy.data.materials["waterfront_glass"]
    bsdf = glass.node_tree.nodes["Principled BSDF"]

    def aim(obj, loc, target):
        obj.location = loc
        obj.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

    # every vertex above the water, to frame a view round
    from bpy_extras.object_utils import world_to_camera_view
    points = [o.matrix_world @ v.co for o in bpy.data.collections["export"].objects for v in o.data.vertices]
    points = [p for p in points if p.z > -0.05]

    def fit(loc, target):
        """Back the camera off along its line until the whole prop is in frame."""
        loc, target = Vector(loc), Vector(target)
        d = loc - target
        k = 1.0
        while k < 4.0:
            aim(cam, target + d * k, target)
            bpy.context.view_layer.update()
            if all(0.03 <= c.x <= 0.97 and 0.03 <= c.y <= 0.97 for c in (world_to_camera_view(scene, cam, p) for p in points)):
                break
            k *= 1.08

    def day(light_from):
        background.inputs[0].default_value = (0.60, 0.74, 0.90, 1)
        background.inputs[1].default_value = 0.9
        sun.data.energy = 3.0
        sun.data.color = (1.0, 0.97, 0.92)
        aim(sun, (0, 0, 40), (-light_from[0], -light_from[1], 40 - light_from[2]))
        for lamp in lamps:
            lamp.hide_render = True
        bsdf.inputs["Emission Strength"].default_value = 0.0

    def dusk():
        background.inputs[0].default_value = (0.05, 0.08, 0.16, 1)
        background.inputs[1].default_value = 0.55
        sun.data.energy = 1.4
        sun.data.color = (1.0, 0.60, 0.38)
        aim(sun, (0, 0, 40), (30, 22, 40 - 3.5))
        for lamp in lamps:
            lamp.hide_render = False
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.74, 0.45, 1)
        bsdf.inputs["Emission Strength"].default_value = 2.5

    # (camera, target, lens, light from, at dusk, back off to fit the whole prop)
    sea = (-0.9, -1.0, 1.3)
    views = {
        "three_quarter": ((-30.0, -32.0, 4.5), (0.5, 0.0, 6.0), 32, sea, False, True),
        "front": ((0.0, -48.0, 4.5), (0.0, 0.0, 6.5), 35, sea, False, True),
        "side_entrance": ((48.0, -2.0, 4.5), (0.0, 0.0, 6.5), 35, (1.0, -0.6, 1.2), False, True),
        "back_three_quarter": ((30.0, 34.0, 5.0), (0.0, 0.0, 6.0), 32, (0.8, 1.0, 1.3), False, True),
        "figure": ((19.5, -7.5, 3.0), (11.6, -0.8, 3.4), 35, (1.0, -0.8, 1.0), False, False),
        "dusk": ((-30.0, -32.0, 4.5), (0.5, 0.0, 6.0), 32, sea, True, True),
        "top": (None, None, 32.0, (0.3, -0.3, 1.0), False, False),
    }
    for tag, (loc, target, lens, light, at_dusk, whole) in views.items():
        plan = loc is None
        grid.hide_render = not plan
        for f in figures:
            f.hide_render = plan
        if at_dusk:
            dusk()
        else:
            day(light)
        if plan:
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = lens
            cam.location = (0.0, 0.0, 60.0)
            cam.rotation_euler = (0.0, 0.0, 0.0)   # north (+Y) up, the glazed front at the bottom
        else:
            cam.data.type = "PERSP"
            cam.data.lens = lens
            if whole:
                fit(loc, target)
            else:
                aim(cam, loc, target)
        scene.render.filepath = os.path.join(folder, f"{name}_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)

    bsdf.inputs["Emission Strength"].default_value = 0.0
    for o in list(tmp.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
        elif isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
    bpy.data.collections.remove(tmp)
    scene.world = old_world
    bpy.data.worlds.remove(world)


# --- the file ------------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name != NAME:
        raise SystemExit(f"{NAME}: open {NAME}.blend, not {name}")
    export, reference = bpy.data.collections["export"], bpy.data.collections["reference"]
    foreign = [o.name for o in export.objects if not o.get(TAG)]
    if export.objects and "--replace" not in argv:
        raise SystemExit(f"{NAME}: export already holds {[o.name for o in export.objects][:4]}...; "
                         "it may be hers. --replace builds over it")
    if foreign:
        print(f"{NAME}: replacing parts this tool did not make: {foreign}")
    for coll in (export, reference):
        for o in list(coll.objects):
            if o.get(TAG) or coll is export:
                bpy.data.objects.remove(o)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)
    figure = build_reference()
    tops, stair = build()
    out, lines = checks(tops, stair)
    print(f"{NAME}:")
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
