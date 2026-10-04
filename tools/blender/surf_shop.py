"""The beach town's surf shop, D2 of the row on Beach Road (the beach town
plan, zone D), as a Blender source. Pass 2 (2026-10-02): built from her
photograph, `documentation/reference/surf_shop/good_surf_shop.webp`, after
pass 1's block-out of the generator's one-storey lot.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/surf_shop.blend --python tools/blender/surf_shop.py -- \
        [--replace] [--save] [--render <folder>] [--render-wing <folder>] \
        [--render-block <folder>] [--form photo|parapet|gable]

Builds into `export`, one object a part, the floor (the threshold) on z = 0,
the origin at the footprint's centre, the storefront facing -Y here (+Z in
Godot: the panel exports with `export_yup`, which turns Blender -Y into glTF
+Z). Into the locked `reference` collection go the standing lot's box, the
generator's floor level, the plan's rectangle, Beach Road's kerbs,
centreline and parking bay, and two 1.7 m figures. Rerunning rebuilds both
collections from scratch (`--replace` when `export` holds anything, in case
it is hers). `--render` writes Eevee frames from temporary cameras, lights
and stage pieces that are never saved: render after `--save`.

**What binds (Christina, 2 October: "why do we care if the current grey box
is one story").** The generator's greybox is a maquette; it binds neither
height, roof form nor floor level. What binds is D2's place in the row (its
frontage between D1 and D3, inside the plan's 12 x 11 m rectangle), the 6.9 m
between the wall and Beach Road's kerb (sidewalk and parking must still fit),
and the ground. The lot's footprint, 8.95 along the street by 8.10 deep, is
kept as the frontage; the threshold is level with the sidewalk (z = 0 is
world y -0.383, the flat apron the probe found from the wall to the road);
the ground at the back corners is 1.11 and 1.27 m above that, rising about
16% inland, so the service yard behind is dug down 1.1 to 1.3 m at the wall
and about 2.1 m six metres back, which is not modelled here.

**The photo form (`--form photo`, the default, saved as `export`).** Two full
storeys, 3.3 m and 2.7 m to the walls' top at 6.0, and above the upstairs
windows the street face as the photo reads up it. Pass 3 (3 October,
Christina, the photo beside the model: "see the roof") replaced pass 2's front
gable: the photo is taken along the building's long side, so the face to the
road is the eave side. Reading up it: a pent roof of tin 1.0 m out over the
upstairs windows (its edge at their heads, its top 6.0 on the wall); a tall
plain vent band, 6.0 to 7.38, holding three round louvred vents 0.8 m across;
a bracketed cornice (frieze board, twelve modillions, fascia) to the tin's top
at 7.90; and from it the main roof falls back at one pitch (0.21, 11.8 deg) to
the back wall's top, 0.30 out at the front, 0.40 at the back, 0.55 past each
end wall. The end walls above the walls' top are shingled right triangles in
dark brown under that deep rake, 1.66 m tall at the street and running out at
the back wall; the one toward the wing (+X) carries a poster, as in the
photo. Heights are read off the photo at the block's near corner with the
wing's 3.66 m fascia as scale and laid above this model's own window heads
(the photo's stand about 0.6 m lower); the constants beside `PENT_OUT` say
which is which. The building's register nomination (Surf-n-Sea Building,
Haleiwa, 2021) agrees: a corrugated metal pent roof, side walls of cut
shingles, a shed-roofed hood above the second-storey windows, three circular
slat ventilators and a bracketed eave. Four small sash windows upstairs on the
front, two on each flank and two at the back; dark brown-maroon board siding
with every corner, edge and opening trimmed in bright yellow (corner boards,
the street face's up its full height, a storey band, the pent's fascia, end
boards and head board, the cornice, the rakes' fascias and friezes, the back
fascia, proud window and door frames); a low rust-red tin porch roof on five thin posts across the
whole front, 2.5 m out over the sidewalk, leaving a 2.0 m clear walk and a
2.4 m parallel-parking bay before the kerb; under it the customer door
(right of centre), a display window with boards, a stand of boards and a
clothes rack; a few boards leaning on posts and wall and a sandwich board as
non-colliding dressing. No name, sign, brand or the photographer's watermark
is copied. Inside, only what the door and the window show: the floor, the
upper floor's underside, a counter, the wax-and-leash rack on the back wall.

**The first two variants (3 October, Christina: "looks like its missing its single
story part").** The photo form above is `kyt_variant = "photo"`, in `export`
itself. `export/variant_photo_wing` (eye shut) holds `photo_wing`: the same
block, every part rebuilt under a `pw_` prefix, plus the photo's one-storey
wing on its right (+X). Read off the photo with the block as scale, about
70 px/m along its wall: 8.2 m wide (the right end is out of frame; at least
7.5 m), as deep as the block, bright yellow siding with a dark band at the
eave (3.26 to 3.49 m), a yellow fascia over it and a corrugated edge showing
above that, a dark skirting board, two big dark-framed display windows (2.0
and 2.55 m wide, 1.33 m tall at sill 0.58) with posters behind the glass, a
small poster box up high between them (1.05 x 0.85 at sill 2.2), a heavy
bench out front as non-colliding dressing. The front is flush with the
block's wall (2 cm back, so no face is shared); the porch's end overhangs the
wing's left 0.3 m as it does in the photo. The roof surface cannot be seen
from the sidewalk, so it is a 1:12 shed falling to the back, 3.70 m at the
front edge; there is no parapet. The photo shows no door on the wing, so its
one door is a service door at the back. `photo_wing` needs 17.15 m of
frontage, D2's 8.95 and 8.2 more; where that goes is a placement matter.
`--render-wing <folder>` shoots it at the photo's standpoint, three-quarter,
front and plan.

**The third variant, `block` (3 October, Christina: "for the surf shop, save a
varient without the second wing and recolor it, it can become a different
thing somewhere else maybe").** `export/variant_block` (eye shut) holds the
two-storey block exactly as `photo` builds it, every part rebuilt under a
`bk_` prefix, with no wing, on materials of its own (`surf_block_*`,
`BLOCK_COLOURS`) in colours neither sibling uses: deep sea-green siding, cream
trim wherever `photo` has yellow, faded red tin on the porch, the pent and the
main roof, slate-grey shingles on the end walls, a dark green door, and dark
green posts, porch fascia and vent slats.
Since it is meant to become some other shop, it leaves out what makes it a
surf shop: every board (the two in the window, the six on the stand, the four
leaning on posts and wall), the board stand, the clothes rack, the
sandwich board and the poster on the end wall. The building, its porch, the display window with its empty
plinth, the door, the counter and the back-wall shelves stay. Dressing is
added back per use, for whatever it becomes (`build_photo(surf=True)` puts the
surf shop's own back). `--render-block <folder>` shoots it three-quarter and
front, and beside `photo` on the next lot along Beach Road.

**Pass 1's forms** stay behind the flag for comparison: `parapet` (the
generator's one-storey shell with its parapet and roof sign) and `gable`
(the same shell under a street-facing gable). Their lot numbers, read off
the 30 September probe (`user://beach_town_plan/`): centre (-55.454,
423.460) world x,z; yaw -74.93 deg (front west, to the road); w 8.95, d 8.10,
walls 4.02, floor y 1.02.

Shapes overlap, they never share a plane: every part laps into its neighbour
or stands off it. Collision is derived from the visible object at export;
dressing (boards, racks, the sandwich board, the banner) is
`kyt_collision = none`.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

# --- the lot, in world terms (see the docstring) ------------------------------
LOT_CENTRE = (-55.454, 423.460)      # world x, z
LOT_YAW_DEG = -74.93                 # Godot yaw; Basis(UP, yaw) turns +z onto the front
W, D = 8.95, 8.10                    # along the street, deep
H1 = 4.02                            # the generator's one-storey wall height (pass 1 forms)
LOT_FLOOR_Y = 1.02                   # the generator's floor
SIDEWALK_Y = -0.383                  # the ground at the front, flat to the road
GROUND_BACK = (0.726, 0.889)         # the ground at the two back corners
ROAD_CENTRE = 9.91                   # Beach Road's centreline from the front wall
ROAD_HALF = 3.0                      # its width is 6 m
PARKING = 2.4                        # a parallel-parking bay along the kerb
PLAN_RECT = (-62.0, 418.0, 12.0, 11.0)   # the plan's D2 rectangle: x, z, w, h in world

# --- shared block-out numbers ------------------------------------------------------
T = 0.30                             # wall thickness
SKIRT = 1.6                          # the foundation's reach below the floor
SKIRT_IN = 0.03                      # and its inset from the wall faces
LID = 0.30                           # the walls' own lid (roof deck, or the attic floor)
FRAME = 0.10                         # frame bar width
SERVICE_X, SERVICE_W, SERVICE_H = -1.8, 1.0, 2.1

# --- the photo form ---------------------------------------------------------------
GF = 3.3                             # ground floor, floor to floor
EAVE = 6.0                           # the walls' top (the attic floor's top), the back eave's wall plate
DOOR_X, DOOR_W, DOOR_H = 2.5, 1.0, 2.2
WIN_X, WIN_W, WIN_SILL, WIN_H = -0.75, 3.3, 0.75, 1.7          # the display window
SASH_W, SASH_SILL, SASH_H = 0.75, 4.2, 1.2                     # the small sash windows
SASH_FRONT_X = (-3.0, -1.0, 1.0, 3.0)
SASH_FLANK_Y = (-1.8, 1.8)
SASH_BACK_X = (-2.2, 2.2)
# The street face above the upstairs windows and the roof (pass 3, 3 October,
# Christina: "see the roof"). Heights read off the photo at the block's near
# corner, where the wing's 3.66 m fascia sets the scale (about 57 px/m), and
# laid above this model's own window heads (5.42 with frames; the photo's
# stand about 0.6 m lower): the pent roof's lower edge at the window heads,
# the vent band about 1.4 m, the cornice about 0.5 m from the frieze's
# foot to the tin's top. The building's register nomination (Surf-n-Sea,
# Haleiwa) calls the main roof a corrugated metal pent roof: one pitch,
# high at the street, falling to the back; both end walls are shingled.
PENT_OUT, PENT_PITCH, PENT_T = 1.00, 0.40, 0.10   # the pent roof over the upstairs windows: out from the wall, fall, thickness
PENT_TOP = 6.00                      # its top where it meets the wall, so the vent wall's foot hides under it
HEAD_Z = (5.41, 5.55)                # the yellow head board under the pent, sat on the window frames' tops
VENT_WALL_Z0 = 5.97                  # the vent wall's foot, 3 cm into the walls' top, 1 cm proud of their face
FRIEZE_Z = (7.38, 7.68)              # the cornice's frieze board, its top lapped into the roof
BRACKET_N, BRACKET_W, BRACKET_OUT, BRACKET_FOOT = 12, 0.10, 0.25, 7.32   # the modillions under the front eave
ROOF_TOP = 7.90                      # the tin's top at the front eave, the highest point
ROOF_T = 0.18                        # the roof's thickness, measured plumb
EAVE_FRONT_OUT, EAVE_BACK_OUT, RAKE_OUT = 0.30, 0.40, 0.55   # past the front and back walls, past the end walls
ROOF_BACK_UNDER = 5.96               # the roof's underside at the back wall's face, 4 cm into the walls' top
CORNER_FRONT_TOP = 7.70              # the street face's corner boards, up into the roof
VENTS = ((-2.0, 6.69, 0.32), (0.0, 6.69, 0.32), (2.0, 6.69, 0.32))   # x, z, radius: centred in the vent band
POSTER = (0.32, 1.32, 6.04, 7.12)    # on the +X end wall's shingles: y from the front wall, then z (photo and photo_wing only)
PORCH_OUT, PORCH_TOP, PORCH_DROP, PORCH_T = 2.5, 3.15, 0.40, 0.10
POST = 0.12
POST_X = (-4.4, -2.2, 0.0, 2.2, 4.4)
BAND_Z = (3.3, 3.55)                 # the yellow storey band
CORNER, PROUD, LAPIN = 0.14, 0.04, 0.03   # corner boards: leg, proud, lapped into the wall

# --- the one-storey wing (the photo_wing variant) ----------------------------------
WING_W = 8.2                         # along the street, from the block's right wall
WING_LAP = 0.05                      # its left wall sunk into the block's right wall
WING_SET = 0.02                      # its front behind the block's front, its back past the block's
WING_BACK_OVER = 0.05
WING_TOP = 3.50                      # the walls' top at the front, under the band and fascia
WING_PITCH = 1.0 / 12.0              # the shed roof, falling to the back
WING_ROOF_T = 0.22
WING_LID = 0.30
WING_BAND_Z = (3.26, 3.49)           # the dark band, 1 cm under the walls' top
WING_FASCIA_Z = (3.47, 3.66)         # the yellow fascia, lapped into the roof's edge, 1 cm under its underside
WING_SKIRT_Z = (-0.02, 0.18)         # the dark skirting board
WING_WIN = ((1.35, 2.00, 0.58, 1.33), (4.90, 2.55, 0.58, 1.33))   # x from the block's wall, width, sill, height
WING_POSTER_BOX = (3.53, 1.05, 2.20, 0.85)
WING_DOOR_X, WING_DOOR_W, WING_DOOR_H = 2.0, 1.0, 2.1          # the service door at the back, x from the block's wall
WING_BENCH = (4.25, 1.40, 0.45)      # centre x from the block's wall, length, seat height

# --- pass 1's forms --------------------------------------------------------------
PARAPET, PARAPET_OUT = 0.55, 0.06
P1_DOOR_X, P1_DOOR_W, P1_DOOR_H, P1_TRANSOM = W / 2 - 1.25, 1.0, 2.1, 2.65
P1_WIN = (-W / 2 + 0.75, W / 2 - 1.25 - 0.5 - 0.35, 0.55, 2.65)      # x0, x1, sill, head
P1_FRAME = 0.08
AWN_TOP, AWN_OUT, AWN_DROP, AWN_T, VALANCE = 3.05, 1.35, 0.30, 0.12, 0.25
BACK_WIN = (1.3, 2.3, 1.9, 2.7)
GABLE1_PITCH = 0.5

COLOURS = {   # preview colours by part; the photo's palette for the photo form
    "siding": (0.30, 0.13, 0.11),
    "shingle": (0.12, 0.065, 0.05),    # the end walls' cut shingles, darker than the boards
    "trim": (0.95, 0.78, 0.10),
    "tin": (0.62, 0.25, 0.12),
    "post": (0.25, 0.16, 0.10),
    "louvre": (0.15, 0.12, 0.10),
    "glass": (0.62, 0.78, 0.86),
    "door": (0.22, 0.10, 0.09),
    "foundation": (0.44, 0.43, 0.41),
    "floor": (0.58, 0.56, 0.52),
    "timber": (0.55, 0.40, 0.25),
    "garments": (0.35, 0.50, 0.65),
    "sandwich": (0.95, 0.78, 0.10),
    "counter": (0.85, 0.82, 0.75),
    "rack": (0.45, 0.34, 0.24),
    "board_a": (0.96, 0.62, 0.30),
    "board_b": (0.45, 0.72, 0.82),
    "board_c": (0.95, 0.92, 0.55),
    "board_d": (0.90, 0.35, 0.40),
    # the wing
    "wing_siding": (0.97, 0.76, 0.08),
    "wing_trim": (0.17, 0.13, 0.12),
    "poster_a": (0.35, 0.55, 0.62),
    "poster_b": (0.78, 0.64, 0.46),
    # pass 1's forms
    "walls": (0.93, 0.91, 0.85),
    "trim1": (0.20, 0.42, 0.62),
    "parapet": (0.18, 0.38, 0.58),
    "sign": (0.97, 0.95, 0.90),
    "awning": (0.24, 0.47, 0.72),
    "door1": (0.20, 0.42, 0.62),
    "roof_unit": (0.62, 0.62, 0.64),
    "banner": (0.92, 0.36, 0.30),
    "gable_roof": (0.36, 0.38, 0.40),
}
# the `block` variant's own palette (materials `surf_block_*`): every role the
# block uses, each a colour neither `photo` nor `photo_wing` wears
BLOCK_COLOURS = {
    "siding": (0.025, 0.14, 0.105),    # deep sea-green
    "shingle": (0.08, 0.10, 0.10),     # slate-grey shingles on the end walls
    "trim": (0.90, 0.82, 0.60),        # cream, where photo has yellow
    "tin": (0.50, 0.14, 0.11),         # faded red tin, porch and main roof
    "post": (0.025, 0.085, 0.06),      # dark green posts and porch fascia
    "louvre": (0.03, 0.06, 0.05),
    "glass": (0.60, 0.78, 0.80),
    "door": (0.02, 0.07, 0.035),       # dark green
    "foundation": (0.42, 0.42, 0.40),
    "floor": (0.56, 0.55, 0.51),
    "counter": (0.80, 0.78, 0.70),
    "rack": (0.40, 0.31, 0.22),
}
REF_COLOURS = {"lot": (0.9, 0.2, 0.2), "plan": (0.2, 0.25, 0.85), "road": (0.25, 0.25, 0.27),
               "parking": (0.42, 0.42, 0.44), "paint": (0.92, 0.92, 0.90),
               "figure": (0.55, 0.42, 0.60), "ink": (0.02, 0.02, 0.02)}

HW, HD = W / 2, D / 2
FRONT, BACK = -HD, HD
# the four wall faces: which axis the face is on, its sign, and the yaw that
# turns a part built flat in the XZ plane (outward -Y) to face out of it
FACES = {"front": ("y", -1.0, 0.0), "back": ("y", 1.0, math.pi),
         "right": ("x", 1.0, math.pi / 2), "left": ("x", -1.0, -math.pi / 2)}


# --- building blocks ---------------------------------------------------------

def material(name, rgb, alpha=1.0):
    """A flat preview material by name; an existing one is reset to the
    colour asked for, so a rerun never keeps an earlier pass's colour."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.15 if alpha < 1.0 else 0.85
    bsdf.inputs["Alpha"].default_value = alpha
    if alpha < 1.0:
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        else:
            mat.blend_method = "BLEND"
    return mat


def mats(colours=None, prefix="surf_"):
    """The parts' materials by role: the photo's palette as `surf_*`, or
    another palette under its own prefix (the block's `surf_block_*`)."""
    colours = colours or COLOURS
    out = {k: material(f"{prefix}{k}", v) for k, v in colours.items() if k != "glass"}
    out["glass"] = material(f"{prefix}glass", colours["glass"], alpha=0.45)
    return out


def prism(poly, axis, lo, hi):
    """A 2D polygon extruded along an axis: `poly` is (a, b) pairs, the plane's
    two axes in X, Y, Z order with `axis` left out ('x' gives (y, z), 'y' gives
    (x, z), 'z' gives (x, y))."""
    bm = bmesh.new()

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


def box_bm(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def frame_bm(x0, x1, z0, z1, b, y0, y1):
    """A rectangular frame in the XZ plane, bars `b` wide, from y0 to y1:
    four mitred bars, one closed mesh with no overlapping faces."""
    bm = bmesh.new()

    def ring(y):
        o = [bm.verts.new((x0, y, z0)), bm.verts.new((x1, y, z0)),
             bm.verts.new((x1, y, z1)), bm.verts.new((x0, y, z1))]
        i = [bm.verts.new((x0 + b, y, z0 + b)), bm.verts.new((x1 - b, y, z0 + b)),
             bm.verts.new((x1 - b, y, z1 - b)), bm.verts.new((x0 + b, y, z1 - b))]
        return o, i

    o0, i0 = ring(y0)
    o1, i1 = ring(y1)
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((o0[k], o0[j], i0[j], i0[k]))
        bm.faces.new((o1[k], o1[j], i1[j], i1[k]))
        bm.faces.new((o0[k], o0[j], o1[j], o1[k]))
        bm.faces.new((i0[k], i0[j], i1[j], i1[k]))
    return bm


def ring_poly_bm(r_in, r_out, y0, y1, n=16):
    """A round ring in the XZ plane about the origin, from y0 to y1."""
    bm = bmesh.new()

    def loop(r, y):
        return [bm.verts.new((r * math.cos(math.tau * i / n), y, r * math.sin(math.tau * i / n))) for i in range(n)]

    o0, i0, o1, i1 = loop(r_out, y0), loop(r_in, y0), loop(r_out, y1), loop(r_in, y1)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((o0[k], o0[j], i0[j], i0[k]))
        bm.faces.new((o1[k], o1[j], i1[j], i1[k]))
        bm.faces.new((o0[k], o0[j], o1[j], o1[k]))
        bm.faces.new((i0[k], i0[j], i1[j], i1[k]))
    return bm


def cylinder_bm(axis, centre, radius, lo, hi, sides=16):
    poly = [(centre[0] + radius * math.cos(math.tau * i / sides),
             centre[1] + radius * math.sin(math.tau * i / sides)) for i in range(sides)]
    return prism(poly, axis, lo, hi)


# Where parts go while a variant builds: its collection, its `kyt_variant` tag
# and the prefix on every part's name (`pw_` for photo_wing, so the two
# variants' parts never collide on a name and the photo form keeps its own).
_ctx = {"coll": "export", "variant": None, "prefix": ""}
PREFIXES = {"photo": "", "photo_wing": "pw_", "block": "bk_"}


def building(coll="export", variant=None, prefix=""):
    _ctx.update(coll=coll, variant=variant, prefix=prefix)


def _mesh_object(name, bm, coll, smooth=False):
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections[coll].objects.link(obj)
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    return obj


def new_object(name, bm, mat, coll=None, smooth=False):
    """A part: named with the variant's prefix, in its collection, marked
    with its `kyt_variant` (an explicit `coll` is for the reference and the
    render stage, which carry no variant)."""
    obj = _mesh_object(_ctx["prefix"] + name, bm, coll or _ctx["coll"], smooth)
    if mat is not None:
        obj.data.materials.append(mat)
    if coll is None and _ctx["variant"]:
        obj["kyt_variant"] = _ctx["variant"]
    return obj


def apply_modifiers(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    # Slot by slot, never `materials.clear()`: in Blender 5 clearing resets
    # every face's material index to 0, so a two-material part comes out all
    # one (the sky ride gondola's tub, 2026-10-02). The evaluated mesh keeps
    # the object's slots; only fill them if it came back without any.
    if len(new.materials) == 0:
        for m in old.materials:
            new.materials.append(m)
    bpy.data.meshes.remove(old)


def cut(base, cutters):
    """Take each cutter (a bmesh) out of `base` with an exact boolean."""
    coll = base.users_collection[0].name
    for i, cb in enumerate(cutters):
        tool = _mesh_object(f"_cut_{base.name}_{i}", cb, coll)
        # the cutter wears the base's material, so the boolean adds no empty
        # slot of its own (Check refuses a slot with no material)
        for mat in base.data.materials:
            tool.data.materials.append(mat)
        mod = base.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = tool
        mod.solver = "EXACT"
        apply_modifiers(base)
        bpy.data.objects.remove(tool)
    return base


def ring(name, x0, x1, y0, y1, z0, z1, b, mat, coll=None):
    """A rectangular ring in plan: a box with its middle taken out."""
    obj = new_object(name, box_bm(x0, x1, y0, y1, z0, z1), mat, coll)
    return cut(obj, [box_bm(x0 + b, x1 - b, y0 + b, y1 - b, z0 - 0.1, z1 + 0.1)])


def dressing(obj):
    obj["kyt_collision"] = "none"
    return obj


def face_depth(face, d=None):
    """How far out from the origin a wall face's plane lies: the block's by
    default, or `d` for the wing's faces."""
    axis, sign, yaw = FACES[face]
    if d is None:
        d = HD if axis == "y" else HW
    return axis, sign, yaw, d


def face_cut(face, u0, u1, z0, z1, d=None):
    """A box through the wall on that face, between u0 and u1 along it."""
    axis, sign, _, d = face_depth(face, d)
    t0, t1 = sorted((sign * (d + 0.1), sign * (d - T - 0.1)))
    if axis == "y":
        return box_bm(u0, u1, t0, t1, z0, z1)
    return box_bm(t0, t1, u0, u1, z0, z1)


def place(obj, face, u, z, d=None):
    """Put a part built flat in the XZ plane (its face plane at local y = 0,
    outward -Y) on that wall face at `u` along it and height z."""
    axis, sign, yaw, d = face_depth(face, d)
    obj.location = (u, sign * d, z) if axis == "y" else (sign * d, u, z)
    obj.rotation_euler = (0.0, 0.0, yaw)
    return obj


def window(m, name, face, u, sill, w, h, cutters, sash=True, proud=0.04, lap_in=0.10, d=None, trim="trim"):
    """A window on a wall face: its opening (added to `cutters`), a frame
    proud of the siding and lapped into the wall, a pane, and a sash rail."""
    cutters.append(face_cut(face, u - w / 2, u + w / 2, sill, sill + h, d))
    e = 0.02
    place(new_object(f"{name}_frame", frame_bm(-w / 2 - e, w / 2 + e, -e, h + e, FRAME + e, -proud, lap_in), m[trim]), face, u, sill, d)
    lap = FRAME - 0.01
    place(new_object(f"{name}_glass", box_bm(-w / 2 + lap, w / 2 - lap, lap_in + 0.02, lap_in + 0.04, lap, h - lap), m["glass"]), face, u, sill, d)
    if sash:
        place(new_object(f"{name}_rail", box_bm(-w / 2 + lap, w / 2 - lap, -proud + 0.02, lap_in - 0.02, h / 2 - 0.03, h / 2 + 0.03), m[trim]), face, u, sill, d)


def door(m, name, face, u, w, h, cutters, hinge=1.0, proud=0.04, lap_in=0.10, mat="door", d=None, trim="trim"):
    """A door on a wall face: the opening down through the floor (so no wall
    stands under the threshold), a frame whose bottom bar is sunk below the
    floor tab, and a leaf hinged at one jamb, 5 mm clear all round."""
    cutters.append(face_cut(face, u - w / 2, u + w / 2, -0.5, h, d))
    e = 0.02
    place(new_object(f"{name}_frame", frame_bm(-w / 2 - e, w / 2 + e, -0.40, h + e, FRAME + e, -proud, lap_in), m[trim]), face, u, 0.0, d)
    lw = w - 2 * FRAME - 0.01
    hx = -hinge * (w / 2 - FRAME - 0.005)
    # the leaf's origin is its hinge jamb on the face's plane, so it can swing
    leaf = new_object(f"{name}_leaf", box_bm(0.0, hinge * lw, lap_in - 0.055, lap_in - 0.005, 0.012, h - 0.015), m[mat])
    axis, sign, yaw, d = face_depth(face, d)
    base = Vector((u, sign * d, 0.0)) if axis == "y" else Vector((sign * d, u, 0.0))
    c, s = math.cos(yaw), math.sin(yaw)
    leaf.location = base + Vector((c * hx, s * hx, 0.0))
    leaf.rotation_euler = (0.0, 0.0, yaw)
    return leaf


def floor_slab(m, doors, name="floor", x0=-HW, x1=HW, y0=FRONT, y1=BACK):
    """The floor: the inner slab with a tab out through each door, flush with
    the outer face, one mesh so the threshold has no seam. Its top is z = 0.
    `doors` are (face, u, w) for the front and back doors; the walls' outer
    faces are the block's unless given."""
    fx0, fx1, fy0, fy1 = x0 + T - 0.05, x1 - T - 0.05, y0 + T - 0.05, y1 - T + 0.05
    g = 0.01
    front_doors = sorted((u, w) for f, u, w in doors if f == "front")
    back_doors = sorted(((u, w) for f, u, w in doors if f == "back"), reverse=True)
    poly = [(fx0, fy0)]
    for u, w in front_doors:
        poly += [(u - w / 2 + g, fy0), (u - w / 2 + g, y0), (u + w / 2 - g, y0), (u + w / 2 - g, fy0)]
    poly += [(fx1, fy0), (fx1, fy1)]
    for u, w in back_doors:
        poly += [(u + w / 2 - g, fy1), (u + w / 2 - g, y1), (u - w / 2 + g, y1), (u - w / 2 + g, fy1)]
    poly += [(fx0, fy1)]
    return new_object(name, prism(poly, "z", -0.3, 0.0), m["floor"])


def capsule_figure(name, x, y, height, mat, coll):
    """A standing figure, a capsule: a cylinder with a sphere for a head."""
    r = 0.20
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=r, depth=height - 2 * r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, (height - 2 * r) / 2 + r))
    body = new_object(name, bm, mat, coll, smooth=True)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, height - r))
    head = new_object(name + "_head", bm, mat, coll, smooth=True)
    for o in (body, head):
        o.location = (x, y, 0.0)
        o["kyt_surf_shop_reference"] = True
    return body


def board(mat, name, x, y, z, length, lean_deg=10.0, yaw_deg=0.0, width=0.55):
    """A surfboard: a chunky eight-point outline, 6 cm thick, standing on
    its tail and leaning back (positive lean tips the top toward +Y before
    the yaw)."""
    hw, hl = width / 2, length / 2
    pts = [(0.0, 0.0), (hw * 0.75, hl * 0.25), (hw, hl * 0.9), (hw * 0.55, hl * 1.7), (0.0, 2 * hl),
           (-hw * 0.55, hl * 1.7), (-hw, hl * 0.9), (-hw * 0.75, hl * 0.25)]
    obj = new_object(name, prism(pts, "y", -0.03, 0.03), mat, smooth=False)
    obj.location = (x, y, z)
    obj.rotation_euler = (math.radians(-lean_deg), 0.0, math.radians(yaw_deg))
    return obj


def world_to_prop(wx, wz):
    """A world (x, z) point in this file's frame: Godot's local x is Blender X,
    Godot's local +z (the front) is Blender -Y."""
    yaw = math.radians(LOT_YAW_DEG)
    ex = (math.cos(yaw), -math.sin(yaw))
    ez = (math.sin(yaw), math.cos(yaw))
    px, pz = wx - LOT_CENTRE[0], wz - LOT_CENTRE[1]
    return (px * ex[0] + pz * ex[1], -(px * ez[0] + pz * ez[1]))


# --- the photo form ----------------------------------------------------------

ROOF_FRONT_Y, ROOF_BACK_Y = FRONT - EAVE_FRONT_OUT, BACK + EAVE_BACK_OUT
# one pitch, from the front eave's underside down to the back wall's
ROOF_PITCH = (ROOF_TOP - ROOF_T - ROOF_BACK_UNDER) / (BACK - ROOF_FRONT_Y)


def roof_under(y):
    """The main roof's underside at depth y: highest at the front eave,
    falling at one pitch to the back."""
    return ROOF_TOP - ROOF_T - (y - ROOF_FRONT_Y) * ROOF_PITCH


def roof_depth_at(z):
    """Where the roof's underside comes down to height z."""
    return ROOF_FRONT_Y + (ROOF_TOP - ROOF_T - z) / ROOF_PITCH


def pent_top(y):
    """The pent roof's top at depth y (y < FRONT is out over the windows)."""
    return PENT_TOP - (FRONT - y) * PENT_PITCH


def build_photo(wing=False, surf=True, palette=None):
    """The photo form into the current collection; with `wing`, the
    one-storey wing on its right as well (the photo_wing variant). Without
    `surf`, none of the surf shop's own things: no boards anywhere, no board
    stand, clothes rack or sandwich board (the block variant). `palette` is
    (colours, material prefix) for a variant on materials of its own."""
    m = mats(*palette) if palette else mats()
    cutters = [box_bm(-HW + T, HW - T, FRONT + T, BACK - T, -0.6, EAVE - LID)]   # the cavity

    # the openings and their kit: the display window and the customer door
    # under the porch, the sash windows upstairs, the service door and a
    # small window at the back
    window(m, "display", "front", WIN_X, WIN_SILL, WIN_W, WIN_H, cutters, sash=False)
    door(m, "door", "front", DOOR_X, DOOR_W, DOOR_H, cutters, hinge=1.0)
    for k, x in enumerate(SASH_FRONT_X):
        window(m, f"sash_front_{k}", "front", x, SASH_SILL, SASH_W, SASH_H, cutters)
    for face in ("left", "right"):
        for k, y in enumerate(SASH_FLANK_Y):
            window(m, f"sash_{face}_{k}", face, y, SASH_SILL, SASH_W, SASH_H, cutters)
    for k, x in enumerate(SASH_BACK_X):
        window(m, f"sash_back_{k}", "back", x, SASH_SILL, SASH_W, SASH_H, cutters)
    door(m, "service", "back", SERVICE_X, SERVICE_W, SERVICE_H, cutters, hinge=-1.0)
    bx0, bx1, bz0, bz1 = BACK_WIN
    window(m, "back_window", "back", (bx0 + bx1) / 2, bz0, bx1 - bx0, bz1 - bz0, cutters, sash=False)

    # the walls: one hollow box up to the eaves, its lid the attic floor
    walls = new_object("walls", box_bm(-HW, HW, FRONT, BACK, -0.4, EAVE), m["siding"])
    cut(walls, cutters)
    new_object("foundation", box_bm(-HW + SKIRT_IN, HW - SKIRT_IN, FRONT + SKIRT_IN, BACK - SKIRT_IN, -SKIRT, -0.2), m["foundation"])
    floor_slab(m, [("front", DOOR_X, DOOR_W), ("back", SERVICE_X, SERVICE_W)])
    # the upper floor, lapped into the walls: the shop's ceiling
    new_object("upper_floor", box_bm(-HW + T - 0.1, HW - T + 0.1, FRONT + T - 0.1, BACK - T + 0.1, GF - 0.3, GF), m["floor"])

    # The street face above the upstairs windows, as the photo reads up it
    # (pass 3): a pent roof of tin over the windows, a tall plain vent band
    # with three round louvred vents, a bracketed cornice, and the main roof
    # sloping back from it at one pitch to the back wall. The end walls above
    # the walls' top are shingled triangles under a deep rake.
    #
    # The pent roof: lapped 5 cm into the wall, its top meeting the wall at
    # PENT_TOP (over the vent wall's foot, so that joint never shows), its
    # outer edge level with the window heads; a yellow fascia on that edge
    # with 2 cm of tin above it, a yellow end board at each end lapped into
    # the corner board, and the yellow head board on the wall under it.
    py_in, py_out = FRONT + 0.05, FRONT - PENT_OUT
    psect = [(py_in, pent_top(py_in)), (py_out, pent_top(py_out)),
             (py_out, pent_top(py_out) - PENT_T), (py_in, pent_top(py_in) - PENT_T)]
    new_object("pent_roof", prism(psect, "x", -HW - 0.06, HW + 0.06), m["tin"])
    new_object("pent_fascia", box_bm(-HW - 0.07, HW + 0.07, py_out - 0.03, py_out + 0.03,
                                     pent_top(py_out) - PENT_T - 0.10, pent_top(py_out) - 0.02), m["trim"])
    ya, yb = FRONT + 0.03, py_out - 0.01
    esect = [(ya, pent_top(ya) + 0.015), (yb, pent_top(yb) + 0.015),
             (yb, pent_top(yb) - PENT_T - 0.015), (ya, pent_top(ya) - PENT_T - 0.015)]
    for tag, x0, x1 in (("l", -HW - 0.08, -HW - 0.03), ("r", HW + 0.03, HW + 0.08)):
        new_object(f"pent_end_{tag}", prism(esect, "x", x0, x1), m["trim"])
    new_object("pent_head", box_bm(-HW + 0.05, HW - 0.05, FRONT - 0.03, FRONT + 0.02, *HEAD_Z), m["trim"])

    # The vent wall: the street face carried up from under the pent to the
    # roof, 1 cm proud of the walls below (so no face is shared) and its top
    # sloped 3 cm up into the roof; the three vents cut through it, each with
    # a yellow ring proud of the siding and three slats in the hole.
    vy0, vy1 = FRONT - 0.01, FRONT + T - 0.02
    vsect = [(vy0, VENT_WALL_Z0), (vy1, VENT_WALL_Z0), (vy1, roof_under(vy1) + 0.03), (vy0, roof_under(vy0) + 0.03)]
    vent_wall = new_object("vent_wall", prism(vsect, "x", -HW - 0.01, HW + 0.01), m["siding"])
    cut(vent_wall, [cylinder_bm("y", (x, z), r, FRONT - 0.1, FRONT + T + 0.1) for x, z, r in VENTS])
    for k, (x, z, r) in enumerate(VENTS):
        place(new_object(f"vent_ring_{k}", ring_poly_bm(r - 0.01, r + 0.08, -0.04, 0.08), m["trim"]), "front", x, z)
        for i, dz in enumerate((-r * 0.5, 0.0, r * 0.5)):
            half = math.sqrt(max(r * r - dz * dz, 0.01)) - 0.01
            place(new_object(f"vent_slat_{k}_{i}", box_bm(-half, half, 0.10, 0.16, dz - 0.02, dz + 0.02), m["louvre"]), "front", x, z)

    # The end walls above the walls' top: shingled right triangles, tall at
    # the street and running out to nothing at the back wall, where the roof
    # comes down to the walls' top; 2 cm proud of the boards below, their
    # sloped tops 4.5 cm up into the roof (the vent wall's are 3 cm, so the
    # two never share that plane), their fronts behind the corner boards and
    # 1 cm behind the pent roof's buried back face.
    gy0, gz0, glap = FRONT + 0.06, EAVE - 0.01, 0.045
    tri = [(gy0, gz0), (roof_depth_at(gz0 - glap), gz0), (gy0, roof_under(gy0) + glap)]
    for tag, x0, x1 in (("l", -HW - 0.02, -HW + T - 0.04), ("r", HW - T + 0.04, HW + 0.02)):
        new_object(f"gable_{tag}", prism(tri, "x", x0, x1), m["shingle"])

    # The main roof, tin, one pitch from the front eave to the back eave,
    # past the end walls by the rake's deep overhang.
    rsect = [(ROOF_FRONT_Y, roof_under(ROOF_FRONT_Y)), (ROOF_BACK_Y, roof_under(ROOF_BACK_Y)),
             (ROOF_BACK_Y, roof_under(ROOF_BACK_Y) + ROOF_T), (ROOF_FRONT_Y, roof_under(ROOF_FRONT_Y) + ROOF_T)]
    new_object("roof", prism(rsect, "x", -HW - RAKE_OUT, HW + RAKE_OUT), m["tin"])

    # Yellow on every edge of it. The front eave: a fascia with 2 cm of tin
    # above it, a frieze board on the wall under the soffit, and the
    # modillions between, from the frieze out under the eave. The back eave:
    # a fascia. The rakes: a fascia on the roof's end, lapped into both eave
    # fascias, and a frieze board on the end wall under the soffit, lapped
    # into the corner boards at both ends.
    xf = HW + RAKE_OUT + 0.04
    zf = roof_under(ROOF_FRONT_Y)
    new_object("eave_fascia_front", box_bm(-xf, xf, ROOF_FRONT_Y - 0.03, ROOF_FRONT_Y + 0.03, zf - 0.06, zf + ROOF_T - 0.02), m["trim"])
    zb = roof_under(ROOF_BACK_Y)
    new_object("eave_fascia_back", box_bm(-xf, xf, ROOF_BACK_Y - 0.03, ROOF_BACK_Y + 0.03, zb - 0.10, zb + ROOF_T - 0.03), m["trim"])
    ra, rb = ROOF_FRONT_Y - 0.02, ROOF_BACK_Y + 0.02
    rake = [(ra, roof_under(ra) - 0.04), (rb, roof_under(rb) - 0.04),
            (rb, roof_under(rb) + ROOF_T - 0.03), (ra, roof_under(ra) + ROOF_T - 0.03)]
    fa, fb = FRONT + 0.10, BACK + 0.02
    rfrieze = [(fa, roof_under(fa) - 0.20), (fb, roof_under(fb) - 0.20), (fb, roof_under(fb) + 0.02), (fa, roof_under(fa) + 0.02)]
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        x0, x1 = sorted((sx * (HW + RAKE_OUT - 0.03), sx * (HW + RAKE_OUT + 0.03)))
        new_object(f"rake_fascia_{tag}", prism(rake, "x", x0, x1), m["trim"])
        x0, x1 = sorted((sx * (HW - 0.02), sx * (HW + 0.05)))
        new_object(f"rake_frieze_{tag}", prism(rfrieze, "x", x0, x1), m["trim"])
    new_object("frieze_front", box_bm(-HW - 0.02, HW + 0.02, FRONT - 0.05, FRONT + 0.02, *FRIEZE_Z), m["trim"])
    # each modillion deep under the soffit and tapering to a foot below the
    # frieze, lapped into the vent wall behind and the roof above
    b0, b1 = FRONT + 0.01, FRONT - BRACKET_OUT
    bsect = [(b0, BRACKET_FOOT), (b0, roof_under(b0) + 0.02), (b1, roof_under(b1) + 0.02),
             (b1, roof_under(b1) - 0.09), (FRONT - 0.11, FRIEZE_Z[0] + 0.03), (FRONT - 0.07, BRACKET_FOOT)]
    span = HW - 0.24
    for k in range(BRACKET_N):
        cx = -span + k * 2 * span / (BRACKET_N - 1)
        new_object(f"bracket_{k}", prism(bsect, "x", cx - BRACKET_W / 2, cx + BRACKET_W / 2), m["trim"])
    # the poster on the end wall toward the wing, as in the photo (the surf
    # shop's own: the block variant has none), clear of the flank window
    if surf:
        p0, p1, pz0, pz1 = POSTER
        dressing(new_object("gable_poster", box_bm(HW - 0.01, HW + 0.035, FRONT + p0, FRONT + p1, pz0, pz1), m["poster_a"]))

    # the corner boards: the street face's two up its full height into the
    # roof, the back two to the walls' top under the back eave
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            L = [(sx * (HW + PROUD), sy * (HD + PROUD)), (sx * (HW + PROUD), sy * (HD - CORNER)),
                 (sx * (HW - LAPIN), sy * (HD - CORNER)), (sx * (HW - LAPIN), sy * (HD - LAPIN)),
                 (sx * (HW - CORNER), sy * (HD - LAPIN)), (sx * (HW - CORNER), sy * (HD + PROUD))]
            top = CORNER_FRONT_TOP if sy < 0 else EAVE - 0.02
            new_object(f"corner_{'l' if sx < 0 else 'r'}{'f' if sy < 0 else 'b'}", prism(L, "z", -0.2, top), m["trim"])
    # and the storey band
    new_object("band_front", box_bm(-HW, HW, FRONT - 0.03, FRONT + 0.06, *BAND_Z), m["trim"])
    new_object("band_back", box_bm(-HW, HW, BACK - 0.06, BACK + 0.03, *BAND_Z), m["trim"])
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        x0, x1 = sorted((sx * (HW - 0.06), sx * (HW + 0.03)))
        new_object(f"band_{tag}", box_bm(x0, x1, FRONT, BACK, *BAND_Z), m["trim"])

    # the porch: a low tin shed roof across the whole front, out over the
    # sidewalk, a fascia on its outer edge, five thin posts
    po = FRONT - PORCH_OUT
    psect = [(FRONT + 0.05, PORCH_TOP), (po, PORCH_TOP - PORCH_DROP), (po, PORCH_TOP - PORCH_DROP - PORCH_T), (FRONT + 0.05, PORCH_TOP - PORCH_T)]
    new_object("porch_roof", prism(psect, "x", -HW - 0.3, HW + 0.3), m["tin"])
    new_object("porch_fascia", box_bm(-HW - 0.28, HW + 0.28, po - 0.06, po + 0.04, PORCH_TOP - PORCH_DROP - 0.25, PORCH_TOP - PORCH_DROP - 0.01), m["post"])
    slope = PORCH_DROP / (PORCH_OUT + 0.05)
    py = po + 0.25
    under_at_post = PORCH_TOP - PORCH_T - (FRONT + 0.05 - py) * slope
    for k, x in enumerate(POST_X):
        new_object(f"post_{k}", box_bm(x - POST / 2, x + POST / 2, py - POST / 2, py + POST / 2, -0.2, under_at_post + 0.05), m["post"])

    # inside: what the door and the window show
    new_object("window_plinth", box_bm(WIN_X - WIN_W / 2 + 0.1, WIN_X + WIN_W / 2 - 0.1, FRONT + T + 0.02, FRONT + T + 0.72, -0.02, 0.30), m["counter"])
    if surf:
        board(m["board_a"], "board_window_a", WIN_X - 0.7, FRONT + T + 0.40, 0.29, 2.2)
        board(m["board_b"], "board_window_b", WIN_X + 0.6, FRONT + T + 0.40, 0.29, 2.0)
    new_object("counter", box_bm(0.6, 2.4, -1.6, -1.0, -0.02, 1.0), m["counter"])
    rx0, rx1 = DOOR_X - 1.0, DOOR_X + 1.0
    new_object("rack_panel", box_bm(rx0, rx1, BACK - T - 0.12, BACK - T + 0.02, 0.9, 2.4), m["rack"])
    for i, z in enumerate((1.30, 1.90)):
        new_object(f"rack_shelf_{i}", box_bm(rx0 + 0.1, rx1 - 0.1, BACK - T - 0.30, BACK - T - 0.10, z, z + 0.05), m["rack"])

    # dressing under the porch and on the sidewalk, none of it colliding: a
    # stand of boards against the wall left of the window, a clothes rack
    # right of the door, boards leaning on posts and wall, a sandwich board
    # (the surf shop's own, so the block variant has none of it)
    if surf:
        sx0 = -HW + 0.25
        dressing(new_object("board_stand", box_bm(sx0, sx0 + 1.7, FRONT - 0.62, FRONT - 0.12, -0.02, 0.12), m["timber"]))
        for i in range(6):
            col = ("board_a", "board_b", "board_c", "board_d")[i % 4]
            dressing(board(m[col], f"stand_board_{i}", sx0 + 0.2 + i * 0.26, FRONT - 0.42, 0.10, 2.1 + 0.08 * (i % 3), lean_deg=9.0, width=0.5))
        cx = DOOR_X + 1.15
        for i, x in enumerate((cx - 0.55, cx + 0.55)):
            dressing(new_object(f"clothes_post_{i}", box_bm(x - 0.03, x + 0.03, FRONT - 0.50, FRONT - 0.44, -0.02, 1.55), m["post"]))
        dressing(new_object("clothes_rail", box_bm(cx - 0.60, cx + 0.60, FRONT - 0.49, FRONT - 0.45, 1.50, 1.54), m["post"]))
        dressing(new_object("garments", box_bm(cx - 0.50, cx + 0.50, FRONT - 0.66, FRONT - 0.28, 0.55, 1.49), m["garments"]))
        tail = py - 0.55
        for i, (x, col) in enumerate(((POST_X[0] + 0.10, "board_c"), (POST_X[4] - 0.35, "board_a"))):
            dressing(board(m[col], f"lean_post_{i}", x, tail, 0.0, 2.3 + 0.1 * i, lean_deg=14.0))
        for i, (x, col) in enumerate(((HW - 1.0, "board_d"), (HW - 0.45, "board_b"))):
            dressing(board(m[col], f"lean_wall_{i}", x, FRONT - 0.52, 0.0, 2.2 - 0.1 * i, lean_deg=14.0))
        for i, s in enumerate((-1.0, 1.0)):
            panel = new_object(f"sandwich_{i}", box_bm(-0.30, 0.30, -0.015, 0.015, -0.90, 0.0), m["sandwich"])
            panel.location = (0.9, FRONT - PORCH_OUT - 0.8, 0.88)
            panel.rotation_euler = (math.radians(s * 15.0), 0.0, 0.0)
            dressing(panel)

    if wing:
        build_wing(m)
    for o in bpy.data.collections[_ctx["coll"]].objects:
        if "kyt_unwrap" not in o:
            o["kyt_unwrap"] = "planar" if o.name.endswith("glass") else "facets"


# --- the one-storey wing -----------------------------------------------------

WX0, WX1 = HW - WING_LAP, HW + WING_W            # its walls' outer faces in x
WY0, WY1 = FRONT + WING_SET, BACK + WING_BACK_OVER   # and in y


def wing_top(y):
    """The wing's wall top at depth y: level with the band at the front,
    falling to the back under the shed roof."""
    return WING_TOP - (y - WY0) * WING_PITCH


def sloped_box(x0, x1, y0, y1, dz0, dz1):
    """A box along the wing's flank whose top and bottom follow the roof:
    from wing_top + dz0 to wing_top + dz1 at every depth."""
    sect = [(y0, wing_top(y0) + dz0), (y1, wing_top(y1) + dz0), (y1, wing_top(y1) + dz1), (y0, wing_top(y0) + dz1)]
    return prism(sect, "x", x0, x1)


def build_wing(m):
    """The photo's one-storey wing, lapped 5 cm into the block's right wall
    and 2 cm behind its front face so no face is shared with the block; its
    trims end at their own depths inside the block's wall (1, 2, 4.5 and 8 cm
    in) for the same reason, and each trim's corner laps into the next."""
    d_front, d_back = HD - WING_SET, HD + WING_BACK_OVER
    cutters = []
    # the walls: a box whose top slopes with the roof, the cavity cut out
    # under a 30 cm lid, then the openings
    # the walls stand 2 cm lower than the block's so the two bottoms do not
    # share a plane over the lap, and the door frame's sunk bar stays inside
    shell = [(WY0, -0.42), (WY1, -0.42), (WY1, wing_top(WY1)), (WY0, wing_top(WY0))]
    walls = new_object("wing_walls", prism(shell, "x", WX0, WX1), m["wing_siding"])
    cavity = [(WY0 + T, -0.6), (WY1 - T, -0.6), (WY1 - T, wing_top(WY1 - T) - WING_LID), (WY0 + T, wing_top(WY0 + T) - WING_LID)]
    cutters.append(prism(cavity, "x", WX0 + T, WX1 - T))
    posters = []
    for k, (x, w, sill, h) in enumerate(WING_WIN):
        u = HW + x + w / 2
        window(m, f"wing_display_{k}", "front", u, sill, w, h, cutters, sash=False, d=d_front, trim="wing_trim")
        posters.append((u, w, sill, h, ("poster_a", "poster_b")[k]))
    x, w, sill, h = WING_POSTER_BOX
    u = HW + x + w / 2
    window(m, "wing_poster_box", "front", u, sill, w, h, cutters, sash=False, d=d_front, trim="wing_trim")
    posters.append((u, w, sill, h, "poster_b"))
    door_u = HW + WING_DOOR_X
    door(m, "wing_service", "back", door_u, WING_DOOR_W, WING_DOOR_H, cutters, hinge=-1.0, d=d_back, trim="wing_trim")
    cut(walls, cutters)
    new_object("wing_foundation", box_bm(WX0 + SKIRT_IN, WX1 - SKIRT_IN, WY0 + SKIRT_IN, WY1 - SKIRT_IN, -SKIRT, -0.22), m["foundation"])
    floor_slab(m, [("back", door_u, WING_DOOR_W)], "wing_floor", WX0, WX1 + 0.1, WY0, WY1)
    # what the windows show: a poster filling each, 2 cm behind the pane,
    # as the photo's are taped to the glass
    for k, (u, w, sill, h, col) in enumerate(posters):
        new_object(f"wing_poster_{k}", box_bm(u - w / 2 + 0.05, u + w / 2 - 0.05, WY0 + 0.16, WY0 + 0.20, sill + 0.05, sill + h - 0.05), m[col])

    # the shed roof, lapped 2 cm into the walls' top, 1 cm past the front and
    # back faces and the right flank, 8 cm into the block's wall
    ya, yb = WY0 - 0.01, WY1 + 0.01
    sect = [(ya, wing_top(ya) - 0.02), (yb, wing_top(yb) - 0.02), (yb, wing_top(yb) - 0.02 + WING_ROOF_T), (ya, wing_top(ya) - 0.02 + WING_ROOF_T)]
    new_object("wing_roof", prism(sect, "x", HW - 0.08, WX1 + 0.01), m["tin"])
    # the trims: the dark band under the walls' top, the yellow fascia on the
    # roof's edge with 4 cm of tin showing above it, the dark skirting; each
    # on the front, the right flank (following the roof) and the back
    b0, b1 = WING_BAND_Z
    new_object("wing_band_front", box_bm(HW - 0.01, WX1 - 0.02, WY0 - 0.03, WY0 + 0.06, b0, b1), m["wing_trim"])
    new_object("wing_band_right", sloped_box(WX1 - 0.06, WX1 + 0.03, WY0 - 0.02, WY1 + 0.02, b0 - WING_TOP, b1 - WING_TOP), m["wing_trim"])
    zb = wing_top(WY1)
    new_object("wing_band_back", box_bm(HW - 0.01, WX1 - 0.02, WY1 - 0.06, WY1 + 0.03, zb + b0 - WING_TOP, zb + b1 - WING_TOP), m["wing_trim"])
    f0, f1 = WING_FASCIA_Z
    new_object("wing_fascia_front", box_bm(HW - 0.02, WX1 + 0.02, WY0 - 0.055, WY0 + 0.015, f0, f1), m["trim"])
    new_object("wing_fascia_right", sloped_box(WX1 - 0.01, WX1 + 0.05, WY0 - 0.04, WY1 + 0.04, f0 - WING_TOP, f1 - WING_TOP), m["trim"])
    new_object("wing_fascia_back", box_bm(HW - 0.02, WX1 + 0.02, WY1 - 0.015, WY1 + 0.055, zb + f0 - WING_TOP, zb + f1 - WING_TOP), m["trim"])
    s0, s1 = WING_SKIRT_Z
    new_object("wing_skirt_front", box_bm(HW - 0.045, WX1 - 0.02, WY0 - 0.03, WY0 + 0.06, s0, s1), m["wing_trim"])
    # the flank's skirt is a centimetre taller top and bottom, so the corners
    # it laps do not share its faces; the back's stops inside the door's jambs
    new_object("wing_skirt_right", box_bm(WX1 - 0.06, WX1 + 0.03, WY0 - 0.02, WY1 + 0.02, s0 - 0.01, s1 + 0.01), m["wing_trim"])
    for tag, x0, x1 in (("l", HW - 0.045, door_u - WING_DOOR_W / 2 + 0.04), ("r", door_u + WING_DOOR_W / 2 - 0.04, WX1 - 0.02)):
        new_object(f"wing_skirt_back_{tag}", box_bm(x0, x1, WY1 - 0.06, WY1 + 0.03, s0, s1), m["wing_trim"])

    # the bench out front, between the windows: a seat on two end frames
    # with a solid back, dark wood, none of it colliding
    bx, bl, bz = WING_BENCH
    cx = HW + bx
    dressing(new_object("wing_bench_seat", box_bm(cx - bl / 2, cx + bl / 2, WY0 - 0.57, WY0 - 0.12, bz - 0.05, bz + 0.01), m["post"]))
    dressing(new_object("wing_bench_back", box_bm(cx - bl / 2 + 0.02, cx + bl / 2 - 0.02, WY0 - 0.19, WY0 - 0.13, bz - 0.01, bz + 0.50), m["post"]))
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        x0, x1 = sorted((cx + sx * (bl / 2 - 0.03), cx + sx * (bl / 2 - 0.09)))
        dressing(new_object(f"wing_bench_end_{tag}", box_bm(x0, x1, WY0 - 0.55, WY0 - 0.14, -0.02, bz - 0.03), m["post"]))


# --- pass 1's one-storey forms ------------------------------------------------

def build_one_storey(roof):
    m = mats()
    hw, hd, front, back = HW, HD, FRONT, BACK
    walls = new_object("walls", box_bm(-hw, hw, front, back, -0.4, H1), m["walls"])
    wx0, wx1, sill, head = P1_WIN
    cut(walls, [
        box_bm(-hw + T, hw - T, front + T, back - T, -0.6, H1 - 0.2),
        box_bm(wx0, wx1, front - 0.1, front + T + 0.1, sill, head),
        box_bm(P1_DOOR_X - P1_DOOR_W / 2, P1_DOOR_X + P1_DOOR_W / 2, front - 0.1, front + T + 0.1, -0.5, P1_TRANSOM),
        box_bm(SERVICE_X - SERVICE_W / 2, SERVICE_X + SERVICE_W / 2, back - T - 0.1, back + 0.1, -0.5, SERVICE_H),
        box_bm(BACK_WIN[0], BACK_WIN[1], back - T - 0.1, back + 0.1, BACK_WIN[2], BACK_WIN[3]),
    ])
    new_object("foundation", box_bm(-hw + SKIRT_IN, hw - SKIRT_IN, front + SKIRT_IN, back - SKIRT_IN, -SKIRT, -0.2), m["foundation"])
    floor_slab(m, [("front", P1_DOOR_X, P1_DOOR_W), ("back", SERVICE_X, SERVICE_W)])
    y0, y1, e, fr = front + 0.08, front + 0.18, 0.02, P1_FRAME
    lap = fr - 0.01
    new_object("window_frame", frame_bm(wx0 - e, wx1 + e, sill - e, head + e, fr + e, y0, y1), m["trim1"])
    new_object("window_glass", box_bm(wx0 + lap, wx1 - lap, front + 0.12, front + 0.14, sill + lap, head - lap), m["glass"])
    new_object("door_frame", frame_bm(P1_DOOR_X - P1_DOOR_W / 2 - e, P1_DOOR_X + P1_DOOR_W / 2 + e, -0.40, P1_TRANSOM + e, fr + e, y0, y1), m["trim1"])
    tz = P1_DOOR_H + 0.06
    new_object("transom_bar", box_bm(P1_DOOR_X - P1_DOOR_W / 2 + fr - 0.01, P1_DOOR_X + P1_DOOR_W / 2 - fr + 0.01, y0 + 0.01, y1 - 0.01, P1_DOOR_H, tz), m["trim1"])
    new_object("transom_glass", box_bm(P1_DOOR_X - P1_DOOR_W / 2 + lap, P1_DOOR_X + P1_DOOR_W / 2 - lap, front + 0.12, front + 0.14, tz - 0.01, P1_TRANSOM - lap), m["glass"])
    lw = P1_DOOR_W - 2 * fr - 0.01
    leaf = new_object("door_leaf", box_bm(0.0, lw, -0.025, 0.025, 0.012, P1_DOOR_H - 0.015), m["door1"])
    leaf.location = (P1_DOOR_X - P1_DOOR_W / 2 + fr + 0.005, front + 0.135, 0.0)
    yb0, yb1 = back - 0.18, back - 0.08
    new_object("service_frame", frame_bm(SERVICE_X - SERVICE_W / 2 - e, SERVICE_X + SERVICE_W / 2 + e, -0.40, SERVICE_H + e, fr + e, yb0, yb1), m["trim1"])
    sleaf = new_object("service_leaf", box_bm(0.0, -(SERVICE_W - 2 * fr - 0.01), -0.025, 0.025, 0.012, SERVICE_H - 0.015), m["door1"])
    sleaf.location = (SERVICE_X + SERVICE_W / 2 - fr - 0.005, back - 0.135, 0.0)
    bx0, bx1, bz0, bz1 = BACK_WIN
    new_object("back_window_frame", frame_bm(bx0 - e, bx1 + e, bz0 - e, bz1 + e, fr + e, yb0, yb1), m["trim1"])
    new_object("back_window_glass", box_bm(bx0 + lap, bx1 - lap, back - 0.14, back - 0.12, bz0 + lap, bz1 - lap), m["glass"])
    sect = [(front + 0.05, AWN_TOP), (front - AWN_OUT, AWN_TOP - AWN_DROP), (front - AWN_OUT, AWN_TOP - AWN_DROP - VALANCE),
            (front - AWN_OUT + AWN_T, AWN_TOP - AWN_DROP - VALANCE), (front - AWN_OUT + AWN_T, AWN_TOP - AWN_DROP - AWN_T), (front + 0.05, AWN_TOP - AWN_T)]
    new_object("awning", prism(sect, "x", -hw + 0.35, hw - 0.35), m["awning"])
    dressing(new_object("banner", box_bm(-3.3, 1.3, front - 0.16, front - 0.12, 3.15, 3.75), m["banner"]))
    if roof == "gable":
        over, rise, rt = 0.3, (hw + 0.3) * GABLE1_PITCH, 0.18
        rs = [(-hw - over, H1), (0.0, H1 + rise), (hw + over, H1), (hw + over, H1 + rt), (0.0, H1 + rise + rt), (-hw - over, H1 + rt)]
        new_object("gable_roof", prism(rs, "y", -hd - over, hd + over), m["gable_roof"])
        lift = over * GABLE1_PITCH
        end = [(-hw, H1), (hw, H1), (hw, H1 + lift + 0.02), (0.0, H1 + rise + 0.02), (-hw, H1 + lift + 0.02)]
        new_object("gable_front", prism(end, "y", -hd, -hd + T), m["walls"])
        new_object("gable_back", prism(end, "y", hd - T, hd), m["walls"])
        for tag, x0, x1 in (("l", -hw, -hw + T), ("r", hw - T, hw)):
            new_object(f"eave_block_{tag}", box_bm(x0, x1, -hd + T - 0.02, hd - T + 0.02, H1, H1 + lift + 0.02), m["walls"])
        new_object("sign_board", box_bm(-2.8, 2.8, -hd - 0.06, -hd + 0.04, H1 + 0.35, H1 + 1.10), m["sign"])
    else:
        ring("parapet", -hw - PARAPET_OUT, hw + PARAPET_OUT, front - PARAPET_OUT, back + PARAPET_OUT,
             H1 - 0.15, H1 + PARAPET, T + PARAPET_OUT + 0.02, m["parapet"])
        new_object("sign_board", box_bm(-hw + 0.4, hw - 0.4, front - 0.02, front + 0.10, H1 + 0.50, H1 + 1.30), m["sign"])
        new_object("roof_unit", box_bm(-1.0, 0.6, 0.62, 2.02, H1 - 0.02, H1 + 1.05), m["roof_unit"])
    px0, px1 = wx0 + 0.10, wx1 - 0.10
    new_object("window_plinth", box_bm(px0, px1, front + T + 0.02, front + T + 0.72, -0.02, 0.30), m["counter"])
    for k, col in enumerate(("board_a", "board_b", "board_c")):
        board(m[col], f"board_{col[-1]}", px0 + 0.55 + k * 1.2, front + T + 0.40, 0.29, 2.2 - 0.15 * k)
    new_object("counter", box_bm(0.4, 2.2, -1.4, -0.8, -0.02, 1.0), m["counter"])
    new_object("rack_panel", box_bm(2.0, 4.0, back - T - 0.12, back - T + 0.02, 0.9, 2.4), m["rack"])
    for i, z in enumerate((1.30, 1.90)):
        new_object(f"rack_shelf_{i}", box_bm(2.1, 3.9, back - T - 0.30, back - T - 0.10, z, z + 0.05), m["rack"])
    for o in bpy.data.collections["export"].objects:
        if "kyt_unwrap" not in o:
            o["kyt_unwrap"] = "planar" if o.name.endswith(("glass", "banner")) else "facets"


# --- the reference ------------------------------------------------------------

def build_reference():
    coll = bpy.data.collections["reference"]
    for o in list(coll.objects):
        if o.get("kyt_surf_shop_reference"):
            bpy.data.objects.remove(o)
    lot = material("_ref_lot", REF_COLOURS["lot"])
    plan = material("_ref_plan", REF_COLOURS["plan"])
    road = material("_ref_road", REF_COLOURS["road"])
    parking = material("_ref_parking", REF_COLOURS["parking"])
    paint = material("_ref_paint", REF_COLOURS["paint"])
    fig = material("_ref_figure", REF_COLOURS["figure"])
    made = []
    # the standing generator lot: its footprint and one-storey wall height, as
    # a wire cage, and its floor 1.4 m over the sidewalk as a thin frame
    o = new_object("lot_box", box_bm(-HW, HW, FRONT, BACK, 0.0, H1), lot, "reference")
    mod = o.modifiers.new("wire", "WIREFRAME")
    mod.thickness = 0.05
    apply_modifiers(o)
    made.append(o)
    gen_floor = LOT_FLOOR_Y - SIDEWALK_Y
    made.append(ring("lot_generator_floor", -HW, HW, FRONT, BACK, gen_floor - 0.015, gen_floor + 0.015, 0.05, lot, "reference"))
    # the plan's rectangle, axis-aligned in the world, here turned by the lot's
    # yaw: a flat band 6 cm wide lying on the ground
    x, z, w, h = PLAN_RECT
    corners = [Vector(world_to_prop(x, z)), Vector(world_to_prop(x + w, z)),
               Vector(world_to_prop(x + w, z + h)), Vector(world_to_prop(x, z + h))]
    inner = []
    for i in range(4):
        a, b, c = corners[i - 1], corners[(i + 1) % 4], corners[i]
        u = (a - c).normalized() + (b - c).normalized()
        inner.append(c + u.normalized() * (0.06 * math.sqrt(2)))
    bm = bmesh.new()
    lo_o = [bm.verts.new((p.x, p.y, 0.02)) for p in corners]
    lo_i = [bm.verts.new((p.x, p.y, 0.02)) for p in inner]
    hi_o = [bm.verts.new((p.x, p.y, 0.045)) for p in corners]
    hi_i = [bm.verts.new((p.x, p.y, 0.045)) for p in inner]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo_o[i], lo_o[j], lo_i[j], lo_i[i]))
        bm.faces.new((hi_o[i], hi_o[j], hi_i[j], hi_i[i]))
        bm.faces.new((lo_o[i], lo_o[j], hi_o[j], hi_o[i]))
        bm.faces.new((lo_i[i], lo_i[j], hi_i[j], hi_i[i]))
    made.append(new_object("plan_rect", bm, plan, "reference"))
    # Beach Road: its centreline and both kerbs; the parking bay along the
    # near kerb with two stall lines; the clear walk is what is left between
    # the bay and the porch
    kerb = -(HD + ROAD_CENTRE - ROAD_HALF)
    for name, yy in (("road_centreline", -(HD + ROAD_CENTRE)), ("road_kerb_near", kerb), ("road_kerb_far", -(HD + ROAD_CENTRE + ROAD_HALF))):
        made.append(new_object(name, box_bm(-14.0, 14.0, yy - 0.08, yy + 0.08, -0.03, 0.0), road, "reference"))
    made.append(new_object("parking_bay", box_bm(-14.0, 14.0, kerb + 0.08, kerb + PARKING, -0.03, -0.005), parking, "reference"))
    for k, x in enumerate((-6.0, 0.0, 6.0)):
        made.append(new_object(f"stall_line_{k}", box_bm(x - 0.05, x + 0.05, kerb + 0.1, kerb + PARKING - 0.02, -0.02, 0.002), paint, "reference"))
    # two 1.7 m figures: one under the porch by the window, one at the service face
    made.append(capsule_figure("figure_front", -3.8, FRONT - 3.6, 1.7, fig, "reference"))
    made.append(capsule_figure("figure_back", SERVICE_X + 1.0, BACK + 1.5, 1.7, fig, "reference"))
    gl = bpy.data.objects.new("ground_line", None)
    gl.empty_display_type = "PLAIN_AXES"
    gl.empty_display_size = 1.0
    coll.objects.link(gl)
    made.append(gl)
    for o in made:
        o["kyt_surf_shop_reference"] = True
    for o in coll.objects:
        if o.name.startswith("figure_") and o.name.endswith("_head"):
            o["kyt_surf_shop_reference"] = True


# --- checks and counts ----------------------------------------------------------

def coplanar_pairs(objs, tol=1e-4):
    """Pairs of faces from different objects lying in one plane and
    overlapping in area (by their bounds in the plane): the z-fights. The
    scan `tools/blender/cottage_kit.py` runs; a face with an opening cut out
    of it is scanned by its bounds, so a floor tab flush in a door's opening
    is reported and is not a fight."""
    faces = []
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        for p in o.data.polygons:
            n = (mw.to_3x3() @ p.normal).normalized()
            pts = [mw @ o.data.vertices[i].co for i in p.vertices]
            d = n.dot(pts[0])
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            us = [q.dot(e1) for q in pts]
            vs = [q.dot(e2) for q in pts]
            faces.append((o.name, n, d, min(us), max(us), min(vs), max(vs)))
    buckets = {}
    for f in faces:
        n = f[1]
        key = tuple(round(c, 2) for c in n)
        buckets.setdefault(key, []).append(f)
        anti = tuple(round(-c, 2) for c in n)
        if anti != key:
            buckets.setdefault(anti, []).append(f)
    found, seen = [], set()
    for group in buckets.values():
        for i in range(len(group)):
            oi, ni, di, u0, u1, v0, v1 = group[i]
            for j in range(i + 1, len(group)):
                oj, nj, dj, w0, w1, x0, x1 = group[j]
                if oi == oj:
                    continue
                same = (ni - nj).length < 1e-3 and abs(di - dj) < tol
                flipped = (ni + nj).length < 1e-3 and abs(di + dj) < tol
                if not (same or flipped):
                    continue
                if flipped:
                    x0, x1 = -x1, -x0
                ou = min(u1, w1) - max(u0, w0)
                ov = min(v1, x1) - max(v0, x0)
                if ou > 1e-3 and ov > 1e-3:
                    key = (oi, oj, round(di, 4), round(u0, 3), round(w0, 3))
                    if key not in seen:
                        seen.add(key)
                        found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def threshold_rays(objs, x_at, y_at, skip):
    """Where rays dropped through a door first land: 15 rays, three across
    the door at five depths into the wall, past the leaf, frame and anything
    overhead (`skip`, name endings)."""
    tops = []
    for k in range(5):
        y = y_at(k)
        for x in x_at:
            top = None
            for o in objs:
                if o.name.endswith(skip):
                    continue
                inv = o.matrix_world.inverted()
                ok, loc, _n, _i = o.ray_cast(inv @ Vector((x, y, 2.0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
                if ok:
                    z = (o.matrix_world @ loc).z
                    top = z if top is None else max(top, z)
            tops.append(top if top is not None else -9.0)
    return f"{len(tops)} rays through the door first meet z {min(tops):+.3f} to {max(tops):+.3f}; flush is 0"


def checks(form, objs, variant=None):
    """The numbers for one variant's parts (`objs`)."""
    tris = 0
    pts = []
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
        pts += [o.matrix_world @ Vector(b) for b in o.bound_box]
    dressing_n = sum(1 for o in objs if o.get("kyt_collision") == "none")
    lines = [f"{len(objs)} parts ({dressing_n} non-colliding dressing), {tris} triangles",
             f"extents x {min(p.x for p in pts):+.2f}..{max(p.x for p in pts):+.2f}, y {min(p.y for p in pts):+.2f}..{max(p.y for p in pts):+.2f}, "
             f"z {min(p.z for p in pts):+.2f}..{max(p.z for p in pts):+.2f}; footprint {W:.2f} x {D:.2f} m, walls {T:.2f} thick"]
    door_x, door_w = (DOOR_X, DOOR_W) if form == "photo" else (P1_DOOR_X, P1_DOOR_W)
    if form == "photo":
        walk = (ROAD_CENTRE - ROAD_HALF) - PORCH_OUT - PARKING
        lines += [f"storeys {GF:.1f} + {EAVE - GF:.1f} m to the walls' top at {EAVE:.2f}; sash windows {SASH_W:.2f} x {SASH_H:.2f} "
                  f"at sill {SASH_SILL:.2f}, heads {SASH_SILL + SASH_H + 0.02:.2f} with frames",
                  f"pent roof {PENT_OUT:.2f} m out, top {PENT_TOP:.2f} at the wall to {pent_top(FRONT - PENT_OUT):.2f} at its edge "
                  f"(pitch {PENT_PITCH:.2f}); vent band {PENT_TOP:.2f}..{FRIEZE_Z[0]:.2f}, vents r {VENTS[0][2]:.2f} "
                  f"(rings {2 * (VENTS[0][2] + 0.08):.2f} across) at z {VENTS[0][1]:.2f}; cornice {FRIEZE_Z[0]:.2f}..{ROOF_TOP:.2f} "
                  f"({BRACKET_N} brackets, foot {BRACKET_FOOT:.2f}); front eave {EAVE_FRONT_OUT:.2f} out",
                  f"roof one pitch {ROOF_PITCH:.3f} ({math.degrees(math.atan(ROOF_PITCH)):.1f} deg): tin top {ROOF_TOP:.2f} at the front eave, "
                  f"underside {roof_under(FRONT):.2f} at the street wall to {roof_under(BACK):.2f} at the back wall, back eave "
                  f"{EAVE_BACK_OUT:.2f} out, rake {RAKE_OUT:.2f} out; end-wall triangles {roof_under(FRONT) - EAVE:.2f} m tall under the soffit at the front",
                  f"porch {PORCH_OUT:.2f} m out, {PORCH_TOP:.2f} m at the wall, fascia bottom {PORCH_TOP - PORCH_DROP - 0.25:.2f} m, "
                  f"{len(POST_X)} posts {POST:.2f} square; kerb {ROAD_CENTRE - ROAD_HALF:.1f} m from the wall: "
                  f"porch {PORCH_OUT:.1f} + clear walk {walk:.1f} + parking {PARKING:.1f}",
                  f"door {DOOR_W:.2f} x {DOOR_H:.2f}; display window {WIN_W:.2f} x {WIN_H:.2f} at sill {WIN_SILL:.2f}; "
                  f"yard behind dug down {GROUND_BACK[0] - SIDEWALK_Y:.2f}..{GROUND_BACK[1] - SIDEWALK_Y:.2f} m at the back wall"]
    overhead = ("door_leaf", "door_frame", "transom_bar", "transom_glass", "awning", "banner", "porch_roof", "porch_fascia")
    lines.append("threshold: " + threshold_rays(objs, (door_x - 0.3, door_x, door_x + 0.3), lambda k: FRONT + 0.1 * k, overhead))
    if variant == "photo_wing":
        wu = HW + WING_DOOR_X
        lines.append(f"wing {WING_W:.2f} x {WY1 - WY0:.2f} m, walls {WING_TOP:.2f} at the front to {wing_top(WY1):.2f} at the back, "
                     f"roof edge {wing_top(WY0 - 0.01) - 0.02 + WING_ROOF_T:.2f} m at the front, pitch 1:{1 / WING_PITCH:.0f}; "
                     f"frontage in all {W + WING_W:.2f} m; windows " +
                     ", ".join(f"{w:.2f} x {h:.2f} at sill {s:.2f}" for _x, w, s, h in WING_WIN) +
                     f"; poster box {WING_POSTER_BOX[1]:.2f} x {WING_POSTER_BOX[3]:.2f} at sill {WING_POSTER_BOX[2]:.2f}")
        lines.append("wing threshold: " + threshold_rays(objs, (wu - 0.3, wu, wu + 0.3), lambda k: WY1 - 0.02 - 0.1 * k, ("wing_service_leaf", "wing_service_frame")))
    pairs = coplanar_pairs(objs)
    lines.append(f"{len(pairs)} coplanar overlapping face pairs" + ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    return lines


def layer_collection(name, root=None):
    root = root or bpy.context.view_layer.layer_collection
    if root.name == name:
        return root
    for child in root.children:
        hit = layer_collection(name, child)
        if hit is not None:
            return hit
    return None


# --- renders -------------------------------------------------------------------

# Where the photo was taken from, solved from the photo (3 October): the
# block's near corner (the wing's side) lands 46% across the frame and its far
# end about 10%, the cornice and the ground where the photo has them, the
# horizon 1.15 m up and 78% down the frame, verticals upright (a shifted lens,
# as the photo's are). The real facade is longer than D2's 8.95 m, so the far
# end recedes less than the photo's. The photo and photo_wing variants both
# render it.
PHOTO_VIEW = dict(loc=(HW + 4.94, FRONT - 12.11, 1.15), target=(HW + 1.68, FRONT - 2.65, 1.15), lens=24,
                  shift_y=0.184, res=(1400, 934))

def render(folder, form, variant=None):
    """Frames of one variant (the other's parts are kept out of them)."""
    os.makedirs(folder, exist_ok=True)
    building()
    scene = bpy.context.scene
    export = bpy.data.collections["export"]
    others = [o for o in export.all_objects if variant and o.get("kyt_variant") != variant]
    for o in others:
        o.hide_render = True
    prefix = PREFIXES.get(variant, "")
    # the block's `beside` view: photo shown on D2 and the block moved onto
    # the next lot along Beach Road, the plan rectangle's 11 m along the
    # street (moved for the frame only: rendering comes after any save)
    neighbour = [o for o in others if o.get("kyt_variant") == "photo"] if variant == "block" else []
    mine = [o for o in export.all_objects if variant == "block" and o.get("kyt_variant") == "block"]
    home_x = {o.name: o.location.x for o in mine}
    next_lot = PLAN_RECT[3]
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False
    stage = bpy.data.collections.new("_stage")
    scene.collection.children.link(stage)
    ref = bpy.data.collections["reference"]
    ref.hide_render = False
    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.70, 0.88, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.world = world
    new_object("_ground", box_bm(-60, 60, -60, 60, -3.0, -0.01), material("_ref_ground", (0.60, 0.58, 0.52)), "_stage")
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(-30))
    stage.objects.link(sun)
    grid = material("_ref_grid", (0.15, 0.15, 0.15))
    grid_bars = []
    gx1 = 16 if variant == "photo_wing" else 10
    for i in range(-10, gx1 + 1):
        grid_bars.append(new_object(f"_gx{i}", box_bm(i - 0.015, i + 0.015, -20, 12, -0.012, -0.003), grid, "_stage"))
    for j in range(-20, 13):
        grid_bars.append(new_object(f"_gy{j}", box_bm(-10, gx1, j - 0.015, j + 0.015, -0.012, -0.003), grid, "_stage"))
    ink = material("_ref_ink", REF_COLOURS["ink"])

    def label(text, x, y, size=0.6):
        curve = bpy.data.curves.new(f"_label_{text}", "FONT")
        curve.body = text
        curve.size = size
        curve.align_x = "CENTER"
        obj = bpy.data.objects.new(f"_label_{text}", curve)
        obj.location = (x, y, 0.01)
        curve.materials.append(ink)
        stage.objects.link(obj)
        return obj

    kerb = -(HD + ROAD_CENTRE - ROAD_HALF)
    lx = -9.0 if variant == "photo_wing" else 7.5    # the street section's labels, clear of the wing
    labels = [label("Beach Road", 0, -(HD + ROAD_CENTRE) - 0.4, 0.8),
              label("parking 2.4 m", lx, kerb + 0.9, 0.45),
              label("clear walk 2.0 m", lx, kerb + PARKING + 0.8, 0.45),
              label("porch 2.5 m", lx, FRONT - 1.4, 0.45),
              label("1 m grid", -5.5, -18.2, 0.6),
              label("service yard, dug down 1.1 to 1.3 m", 0, HD + 2.6, 0.5)]
    if variant == "photo_wing":
        labels += [label(f"wing {WING_W:.1f} m, frontage {W + WING_W:.2f} m in all", HW + WING_W / 2, 5.9, 0.45),
                   label("D2 is 8.95 m: the wing's lot is a placement matter", HW + WING_W / 2, 5.0, 0.4)]
    else:
        labels += [label("D1 surf school, Shore St (north)", -6.0, 7.6, 0.45),
                   label("D3 skate shop, Second St (south)", 6.0, 7.6, 0.45)]
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    leaf = bpy.data.objects.get(prefix + "door_leaf")
    lot_refs = [o for o in ref.objects if o.name.startswith("lot_")]
    top = 8.5 if form == "photo" else 5.5
    if variant == "photo_wing":
        # the photo's standpoint (PHOTO_VIEW); the rest as for the block
        cxm = (-HW + WX1) / 2
        views = {
            "photo_standpoint": PHOTO_VIEW,
            "three_quarter": dict(loc=(WX1 + 6.0, FRONT - 14.0, 2.2), target=(cxm, -1.5, 3.0), lens=30),
            "front": dict(loc=(cxm, -70, top * 0.45), target=(cxm, 0, top * 0.45), ortho=24.0),
            "plan": dict(loc=(cxm, -4.0, 40), target=(cxm, -4.0, 0), ortho=30.0, up="Y", res=(1300, 1000), grid=True),
        }
    elif variant == "block":
        views = {
            "three_quarter": dict(loc=(-10.5, -19.5, 1.6), target=(0.5, -3.0, top * 0.42), lens=30),
            "front": dict(loc=(0, -70, top * 0.45), target=(0, 0, top * 0.45), ortho=max(13.0, top * 1.9)),
            "beside": dict(loc=(-9.0, -24.0, 1.6), target=(next_lot / 2, -2.5, top * 0.40), lens=26, pair=True),
        }
    else:
        views = {
            "three_quarter": dict(loc=(-10.5, -19.5, 1.6), target=(0.5, -3.0, top * 0.42), lens=30),
            "three_quarter_right": dict(loc=(13.0, -16.5, 1.6), target=(0.3, -3.0, top * 0.42), lens=30),
            "photo_standpoint": PHOTO_VIEW,
            "through_door": dict(loc=(door_x_of(form) + 0.4, -9.0, 1.6), target=(door_x_of(form) + 0.5, 3.7, 1.3), lens=30, close=True, open_door=True),
            "window": dict(loc=(-2.5, -9.5, 1.6), target=(-0.9, 0.0, 1.5), lens=35, close=True),
            "front": dict(loc=(0, -70, top * 0.45), target=(0, 0, top * 0.45), ortho=max(13.0, top * 1.9)),
            "back": dict(loc=(0, 70, top * 0.45), target=(0, 0, top * 0.45), ortho=max(13.0, top * 1.9)),
            "plan": dict(loc=(0, -5.5, 40), target=(0, -5.5, 0), ortho=27.0, up="Y", res=(1000, 1400), grid=True),
        }
    stem = variant or form
    for tag, v in views.items():
        cam.location = v["loc"]
        d = Vector(v["target"]) - Vector(v["loc"])
        cam.rotation_euler = d.to_track_quat("-Z", v.get("up", "Y")).to_euler()
        if "ortho" in v:
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = v["ortho"]
        else:
            cam.data.type = "PERSP"
            cam.data.lens = v["lens"]
        cam.data.shift_y = v.get("shift_y", 0.0)
        scene.render.resolution_x, scene.render.resolution_y = v.get("res", (1400, 900))
        for o in labels + grid_bars:
            o.hide_render = not v.get("grid", False)
        # the standing lot's cage and floor line are pass 1's reference; they
        # stay in the file but out of the frames (the greybox binds nothing)
        for o in lot_refs:
            o.hide_render = True
        if leaf is not None:
            leaf.rotation_euler = (0.0, 0.0, math.radians(100) if v.get("open_door") else 0.0)
        for o in neighbour:
            o.hide_render = not v.get("pair", False)
        for o in mine:
            o.location.x = home_x[o.name] + (next_lot if v.get("pair") else 0.0)
        scene.render.filepath = os.path.join(folder, f"surf_shop_{stem}_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)
    if leaf is not None:
        leaf.rotation_euler = (0.0, 0.0, 0.0)
    for o in mine:
        o.location.x = home_x[o.name]
    for o in lot_refs + others:
        o.hide_render = False
    ref.hide_render = True
    # take the stage down, so a second render flag in the same run does not
    # shoot through this one's ground, sun, grid and labels (the plan view
    # leaves them showing)
    for o in list(stage.objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(stage)


def door_x_of(form):
    return DOOR_X if form == "photo" else P1_DOOR_X


# --- the file -------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != "surf_shop":
        raise SystemExit(f"surf_shop: open surf_shop.blend, not {name}")
    form = argv[argv.index("--form") + 1] if "--form" in argv else "photo"
    if form not in ("photo", "parapet", "gable"):
        raise SystemExit("surf_shop: --form photo, parapet or gable")
    export = bpy.data.collections["export"]
    if export.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"surf_shop: export already holds {[o.name for o in export.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(export.all_objects):
            bpy.data.objects.remove(o)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for sub in list(export.children):
        bpy.data.collections.remove(sub)
    if form == "photo":
        building("export", "photo", "")
        build_photo()
        sub = bpy.data.collections.new("variant_photo_wing")
        export.children.link(sub)
        building(sub.name, "photo_wing", PREFIXES["photo_wing"])
        build_photo(wing=True)
        blk = bpy.data.collections.new("variant_block")
        export.children.link(blk)
        building(blk.name, "block", PREFIXES["block"])
        build_photo(surf=False, palette=(BLOCK_COLOURS, "surf_block_"))
        building()
        bpy.context.view_layer.update()
        for name in (sub.name, blk.name):
            eye = layer_collection(name)
            if eye is not None:
                eye.hide_viewport = True
    else:
        building()
        build_one_storey(form)
    build_reference()
    by_variant = {}
    for o in export.all_objects:
        by_variant.setdefault(o.get("kyt_variant"), []).append(o)
    for variant, objs in by_variant.items():
        print(f"surf_shop ({form} form{', variant ' + variant if variant else ''}):")
        for line in checks(form, objs, variant):
            print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], form, "photo" if form == "photo" else None)
    if "--render-wing" in argv:
        render(argv[argv.index("--render-wing") + 1], form, "photo_wing")
    if "--render-block" in argv:
        render(argv[argv.index("--render-block") + 1], form, "block")


main()
