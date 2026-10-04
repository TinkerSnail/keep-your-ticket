"""The flared tower cottage, blocked out (2026-10-03): Christina's photographs
`documentation/reference/houses/flared_tower_cottage.webp` (front three-quarter)
and `flared_tower_cottage_side.png` (from the front-left, small), a tiny
two-storey house whose walls lean inward going up, wider at the ground than
at the eave, "its supposed to resemble a wind mill" (Christina), with the
deep cornice and pediment as the mill's cap. The first pass had the taper
upside down, wider at the eave, from a brief that misread the photo; it was
inverted the same day and nothing else about the three variants changed.
Later the same day, from Christina: a round window upstairs on the tower's
front on all three ("lets put a window, circular, on the front of the
tower"); `gentle`'s windows fixed ("yellow needs its windows fixed": its
three-light window showed wall, because the 3-degree tower wall stood in
front of the glass); and the side windows' hoods given clear air ("window
awning things are colliding", "upper hood runs into roof": the lower hood
met the upper sill and the upper hood ran 14 cm into the bed board, and on
`bell` into its back corner board).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/flared_tower.blend --python tools/blender/flared_tower.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, three variants of one house, all standing at
the origin, each marked `kyt_variant` so Send writes each as a prop of its
own (`send.py`): **photo**, the house as the photographs show it, in
`export`; **bell**, in `export/variant_bell`, the same house with a stronger
flare, the wing on the other side, a plain boxed cornice under a low hip
instead of the pediment, and the balcony on the open side; and **gentle**,
in `export/variant_gentle`, a gentler flare, a two-storey wing under the
cornice, the pediment front as the photo's. Each extra variant wears its own
colours on its own materials (Christina's rule for houses: either/or choices
are variations, "we want this AND that"). Into the locked `reference`
collection go the base and eave footprints, a 1.7 m figure and the
`ground_line` marker Check reads (the walls reach 5 cm below z = 0 on
purpose, like the hardscape kit's). Everything the tool makes carries
`kyt_flared_tower`, so a rerun removes and rebuilds its own work and keeps
anything of hers; `export` holding anything untagged refuses without
`--replace`.

**Frame.** Real metres, Z up, the ground at z = 0, the origin at the tower's
footprint centre. The front (the pediment, the wing's door) faces -Y here,
which the glTF export (`send.py`, `export_yup=True`) turns into Godot's +Z.
The photographed window side is +X (the house's right as you face it); the
wing stands on -X.

**Read off the photographs** (the side windows' casing as the scale, about
1.55 m tall and 140 px/m in the big photo; the wing's door, 2 m, in the
small one): the tower's eave (the cornice's underside) 4.8 m up; the cornice
a full metre deep, a bed board, a plain frieze, a soffit and a fascia, with a
low shingled pediment over it to the front at 20 degrees; the side windows
one over the other at seven tenths of the depth from the front, 0.72 x 1.4 m
glass with a chunky casing and a little gable hood each, the upper hood's
peak touching the cornice (drawn otherwise, below); the ground floor's front under the pediment a
board-and-batten bay with a three-light shuttered window under a flat roof
with a white fascia at 2.5 m, which runs on as the wing's roof; the wing
one storey, the door at its far end; the balcony upstairs on the back wall,
at the window side, past the corner from the front-left, with a white rail.
The lean reads as 4-6 degrees once the big photo's perspective is taken off,
the walls closing toward the cap; the tower is drawn at 5 (`photo`), 8
(`bell`) and 3 (`gentle`). The small photo puts the front about 2.8 m wide
at the bay's roof, which at 5 degrees is 3.2 m at the ground and 2.4 m at
the eave.

**Chosen, not read:** the tower 3.2 x 4.0 m at the ground and 2.36 x 3.16 m
at the eave (`photo`), the wing 2.4 m wide and 3.3 m deep. The lower storey
2.65 m, the upper 2.15 m under the cornice. The back and the wing side carry
plain windows.

**The hooded side windows** are stacked down from the bed board so every
hood has bare wall over it: 18 cm (`HOOD_AIR`) from the upper hood to the
bed board and from the lower hood to the upper sill, more than a gap needs
because from standing height a hood's front edge rises in front of what is
over it. To fit, their glass is 0.72 x 1.2 m (the photo's 1.4 m left no
room), sills at 0.92 and 2.82 m, and the hoods are 1.0 m wide, 0.26 m of
rise and 0.22 m deep. Under `bell`'s 8-degree lean the back corner comes in
on the upper hood, so its windows stand forward of seven tenths until the
eave clears that corner's board by 10 cm. The report prints each hood's
clear air straight up and its nearest part.

**The round window** is upstairs on the front, centred on the face halfway
between the bay roof's fascia and the bed board (3.64 m): its glass 0.31 of
the face's width there (0.80 m `photo`, 0.74 `bell`, 0.82 `gentle`) in a
12 cm white ring.

**Contract** (enclosing): public faces, doors, windows, balcony, no interior.
Every opening is a real hole through a wall of real thickness; in the
leaning walls the hole's reveals are square to the wall, so its head and
sill lean with it, and the casing, hood and pane are set in the wall's own
tilted frame. The round window is a circle drawn in the leaning wall's own
plane, so it is round on the face, cut square to it with a reveal of 24
facets. The bay's three-light window is cut on through the tower's leaning
front wall behind it, 4 cm larger all round: that wall stands inside the
bay's reveal, and at `gentle`'s 3 degrees in front of the glass. The report
casts rays square-on at every pane from outside and names whatever they
reach first if it is not glass or a mullion. The doors are at flush thresholds (a centimetre over the
ground, the leaf shut in the hole). There are no steps: the wing's floor is
the ground. No two shapes share a plane: a part that meets another laps
2 cm into it or stands proud of it; a lean makes every tower face its own
plane, so the wing's vertical walls meet it without a share.

**A tall box may not be tilted** (AGENTS.md): the tower is not four rotated
boxes but one tapered shell (`tapered_shell`), a closed solid along the base
footprint whose outer skin at height z is the footprint drawn in by
z * tan(lean), mitred at the corners, with the inner skin a wall's thickness
inside it and every opening cut through square to the skin. The corner
boards are L-shaped prisms sheared along the leaning corner. The wing and
the bay are the same shell with no lean; because the tower leans away from
them, every end that meets it is carried to where the tower's face stands at
the wing's top, and the roof slab is notched where it would otherwise run
on beside the tower's corner (`build_wing`, `flat_roof`).

**Collision.** The leaning walls stand back from their own foot: the
capsule meets the wall's foot first, a plinth line the player can stand
against, and the wall leans away above it by 13 cm at the shoulder
(`photo`; 21 cm in `bell`, 8 cm in `gentle`); the cornice overhangs a metre
past the wall at 4.64 m, above head height. Trim, hoods, rails, fascias and
the round window's frame do not collide (`kyt_collision = none`); walls,
roofs, panes and the balcony do.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TAG = "kyt_flared_tower"
PROP = "flared_tower"
VARIANTS = ("photo", "bell", "gentle")

# --- the photograph's numbers -------------------------------------------------
T = 0.20                   # wall thickness
BELOW = 0.05               # how far the walls reach below the ground
THRESHOLD = 0.01           # a door's sill over the ground outside it (the door is shut)
EAVE = 4.80                # the cornice's underside (the bed board's top line)
WALL_TOP = EAVE + 0.03     # the tower's walls end inside the frieze ring
UPPER_SILL, UPPER_HEAD = 2.95, 4.35   # the plain upstairs window; the balcony door's head
UPPER_FLOOR = 2.65         # the balcony's deck
WIN_W = 0.72               # the side windows' glass width
SIDE_GLASS = 1.20          # the hooded side windows' glass height
JAMB, HEAD_T, SILL_T = 0.09, 0.10, 0.08
PROUD, SUNK = 0.035, 0.015
HOOD_RISE, HOOD_OUT, HOOD_WING = 0.26, 0.22, 0.05
HOOD_AIR, HOOD_AIR_SIDE = 0.18, 0.10   # bare wall over each hood (to the upper sill, to the bed board), and beside the upper one
SIDE_WINDOW_AT = 0.70      # along the side from the front corner
BAY_EAVE = 2.50            # the flat roof's underside over the ground floor's front bay (the wing's too)
FLAT_T = 0.12              # the flat roof slab
FLAT_OVER = 0.30           # its fascia past the walls
FASCIA_T, FASCIA_H = 0.05, 0.24
WING_W, WING_BACK = 2.40, 1.30   # the wing's width, and its back wall's y (less under a strong lean, `wing_back_y`)
DOOR_W, DOOR_H = 0.90, 2.05
BAY_WIN = (-0.45, 1.00)    # the three-light window's glass, x (mirrored for a right wing)
BAY_SILL, BAY_HEAD = 1.10, 2.05
# the cornice, from the bottom: bed board, frieze, soffit, fascia
BED_Z0, BED_Z1, BED_OUT, BED_IN = EAVE - 0.16, EAVE + 0.02, 0.18, 0.04
FRIEZE_Z1, FRIEZE_OUT, FRIEZE_IN = EAVE + 0.52, 0.06, 0.03
SOFFIT_Z0, SOFFIT_T, OVER = EAVE + 0.50, 0.06, 0.45
CFASCIA_Z0, CFASCIA_Z1, CFASCIA_T = EAVE + 0.48, EAVE + 0.84, 0.06
ROOF_Z0 = CFASCIA_Z1 - 0.02       # the roof solid's underside, inside the fascia
# the hooded side windows, stacked down from the cornice's underside (the
# bed board's): a hood's top stands HOOD_PEAK over its window's head (the
# head board, a centimetre, the rise, the roofing, and up to 4 cm more where
# the lean tips its front edge up), with HOOD_AIR of bare wall over the
# upper hood and between the lower hood and the upper sill. From standing
# height a hood's front edge rises in front of what is over it, so the air
# is more than a gap needs (Christina, 2026-10-03: "upper hood runs into
# roof", which the first 10 cm still looked to from the ground)
HOOD_PEAK = HEAD_T + 0.01 + HOOD_RISE + 0.03 + 0.04
SIDE_UPPER = (BED_Z0 - HOOD_AIR - HOOD_PEAK - SIDE_GLASS, BED_Z0 - HOOD_AIR - HOOD_PEAK)
SIDE_LOWER = (SIDE_UPPER[0] - SILL_T - HOOD_AIR - HOOD_PEAK - SIDE_GLASS, SIDE_UPPER[0] - SILL_T - HOOD_AIR - HOOD_PEAK)
# the bay's three-light window is cut on through the tower's front wall
# behind it, this much larger all round, so the tower's reveals stay hidden
# in the bay's wall
BAY_CUT = 0.04
# the round window on the tower's front, upstairs: centred on the face,
# halfway between the bay roof's fascia and the bed board, its glass
# ROUND_OF_FACE of the face's width there, a chunky ring of frame from 2 cm
# inside the hole to ROUND_FRAME outside it; the wall round it is patched
# back out to ROUND_MARGIN past the hole
ROUND_Z = (BAY_EAVE + FLAT_T + 0.02 + BED_Z0) / 2
ROUND_OF_FACE, ROUND_FRAME, ROUND_MARGIN, ROUND_SEG = 0.312, 0.10, 0.14, 24
PITCH = math.radians(20.0)
RAKE_H = 0.12
CORNER, CORNER_PROUD, CORNER_SUNK = 0.12, 0.03, 0.01
BALCONY_W, BALCONY_D, DECK_T = 1.30, 0.90, 0.10
POST, RAIL_H, MID_RAIL = 0.09, 1.00, 0.50
FIGURE_AT = (3.6, -4.6)

# each variant: the base footprint, the lean, which side the wing is on,
# how many storeys it has, the cap over the cornice, and the balcony's wall
SPEC = {
    "photo": dict(base=(3.2, 4.0), lean=5.0, wing_side=-1, wing_eave=BAY_EAVE, cap="pediment"),
    "bell": dict(base=(3.4, 4.2), lean=8.0, wing_side=1, wing_eave=BAY_EAVE, cap="hip"),
    "gentle": dict(base=(3.0, 3.8), lean=3.0, wing_side=-1, wing_eave=4.30, cap="pediment"),
}


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


SURFACES = ("walls", "wing", "trim", "glass", "door", "roof", "pediment")
COLOURS = {
    # the photograph: grey-blue lap siding, the same on the battened wing,
    # white trim, pale shutters behind the glass, a pale blue-grey door, a
    # dark grey roof, white-painted shingles in the pediment
    f"{PROP}_walls": srgb("8ea3b0"),
    f"{PROP}_wing": srgb("889eab"),
    f"{PROP}_trim": srgb("f4f4f0"),
    f"{PROP}_glass": srgb("c7d2d9"),
    f"{PROP}_door": srgb("a9bfcc"),
    f"{PROP}_roof": srgb("474a4f"),
    f"{PROP}_pediment": srgb("e8e8e2"),
    # bell: sage siding, cream trim, a brick-red door, a dark brown roof
    f"{PROP}_bell_walls": srgb("9fb08a"),
    f"{PROP}_bell_wing": srgb("93a47f"),
    f"{PROP}_bell_trim": srgb("f3ecd9"),
    f"{PROP}_bell_glass": srgb("8a9ba1"),
    f"{PROP}_bell_door": srgb("a6412f"),
    f"{PROP}_bell_roof": srgb("4e3f36"),
    f"{PROP}_bell_pediment": srgb("e6dcc4"),
    # gentle: butter-yellow siding, white trim, a teal door, a slate roof
    f"{PROP}_gentle_walls": srgb("e9cf74"),
    f"{PROP}_gentle_wing": srgb("e2c468"),
    f"{PROP}_gentle_trim": srgb("f7f6f0"),
    f"{PROP}_gentle_glass": srgb("6f8a99"),
    f"{PROP}_gentle_door": srgb("1f8a84"),
    f"{PROP}_gentle_roof": srgb("5c5f66"),
    f"{PROP}_gentle_pediment": srgb("efe9d8"),
}


def material(name, colour=None):
    """A stand-in material by name. The colours in COLOURS are the
    builder's: a rerun resets them, because a material survives
    `--replace` (the streetcar's big door stayed red, 2026-10-03)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour or COLOURS[name]
        bsdf.inputs["Roughness"].default_value = 0.85
    elif name in COLOURS and mat.node_tree is not None:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = COLOURS[name]
    return mat


def mats(variant):
    """The stand-in materials by surface, `flared_tower_<variant>_<surface>`
    (the photo variant's without the variant)."""
    tag = "" if variant == "photo" else f"{variant}_"
    return {k: material(f"{PROP}_{tag}{k}") for k in SURFACES}


# --- building blocks -----------------------------------------------------------

def finish(name, bm, coll, mats, variant=None, collide=True, flat=True):
    """A bmesh into an object in `coll`, tagged, with its material slots."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # recalc guesses which side is out from the faces furthest out, and the
    # round window's fan of small faces fooled it on `bell`'s walls, which
    # came out inside-out (2026-10-03): a closed part's volume is positive
    if not any(e.is_boundary for e in bm.edges) and bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    if flat:
        for f in bm.faces:
            f.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    for m in mats:
        mesh.materials.append(m)
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    if variant:
        obj["kyt_variant"] = variant
    if not collide:
        obj["kyt_collision"] = "none"
    coll.objects.link(obj)
    return obj


def prism_bm(poly, axis, lo, hi):
    """A 2D polygon extruded along `axis` ('x' gives (y, z) pairs, 'y' gives
    (x, z), 'z' gives (x, y))."""
    bm = bmesh.new()

    def at(a, b, t):
        return {"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis]

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return bm


def box(name, coll, mat, x0, x1, y0, y1, z0, z1, variant=None, collide=True):
    """An axis-aligned box, 12 triangles."""
    assert x1 > x0 and y1 > y0 and z1 > z0, (name, x0, x1, y0, y1, z0, z1)
    bm = prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)
    return finish(name, bm, coll, [mat], variant=variant, collide=collide)


# --- a leaning wall's frame -------------------------------------------------------

class Ring:
    """A footprint at the ground, anticlockwise (the inside on the left of
    each wall), whose walls all lean outward by the same angle: wall i runs
    from pts[i] to pts[i + 1] along U[i]; OUT[i] is its outward normal in
    plan; at height z the outer face is pushed out by z * k."""

    def __init__(self, pts, lean_deg, closed=True):
        self.P = [Vector(p) for p in pts]
        self.closed = closed
        n = len(self.P)
        self.nseg = n if closed else n - 1
        self.U, self.L, self.OUT = [], [], []
        for i in range(self.nseg):
            d = self.P[(i + 1) % n] - self.P[i]
            self.L.append(d.length)
            u = d / d.length
            self.U.append(u)
            self.OUT.append(Vector((u.y, -u.x)))
        # the lean is inward going up (the windmill's), so the push is negative
        self.k = -math.tan(math.radians(lean_deg))
        self.cos = 1.0 / math.sqrt(1.0 + self.k * self.k)
        self.sin = self.k * self.cos

    def inset(self, z):
        """How far every face has leaned in from its base line at height z."""
        return -self.k * z

    def mitre(self, i):
        """The outward direction at the corner where wall i begins (not a
        unit vector: it moves both walls' faces out by one unit)."""
        if not self.closed and i == 0:
            return self.OUT[0]
        o_prev, o = self.OUT[i - 1 if i > 0 else self.nseg - 1], self.OUT[i]
        return (o_prev + o) / (1.0 + o_prev.dot(o))

    def w(self, z):
        """The wall-plane coordinate (along the lean) of outer-face height z."""
        return z / self.cos

    def frame(self, i):
        """The wall's own axes: U along it, W up its leaning face, N out of
        it, from the wall's base start."""
        out = self.OUT[i]
        W = Vector((out.x * self.sin, out.y * self.sin, self.cos))
        N = Vector((out.x * self.cos, out.y * self.cos, -self.sin))
        return Frame(Vector((self.P[i].x, self.P[i].y, 0.0)), Vector((self.U[i].x, self.U[i].y, 0.0)), W, N, self)

    def u_at(self, i, xy):
        return (Vector(xy) - self.P[i]).dot(self.U[i])

    def out_at(self, i, z):
        """How far wall i's outer face stands past its base line at height z."""
        return z * self.k


class Frame:
    def __init__(self, origin, U, W, N, ring):
        self.o, self.U, self.W, self.N, self.ring = origin, U, W, N, ring

    def at(self, u, w, n):
        return self.o + self.U * u + self.W * w + self.N * n

    def w(self, z):
        return self.ring.w(z)


def frame_prism(name, coll, mats, frame, poly_uw, n0, n1, variant=None, collide=True):
    """A polygon in a wall's (u, w) plane extruded along its normal from n0
    (into the wall when negative) to n1 (proud)."""
    bm = bmesh.new()
    near = [bm.verts.new(frame.at(u, w, n0)) for u, w in poly_uw]
    far = [bm.verts.new(frame.at(u, w, n1)) for u, w in poly_uw]
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    n = len(poly_uw)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return finish(name, bm, coll, mats, variant=variant, collide=collide)


def frame_box(name, coll, mat, frame, u0, u1, w0, w1, n0, n1, variant=None, collide=True):
    """A box square to a leaning wall, 12 triangles."""
    assert u1 > u0 and w1 > w0 and n1 > n0, (name, u0, u1, w0, w1, n0, n1)
    return frame_prism(name, coll, [mat], frame, [(u0, w0), (u1, w0), (u1, w1), (u0, w1)], n0, n1,
                       variant=variant, collide=collide)


def tapered_shell(name, coll, ring, z0, z1, openings, mats, thick=T, variant=None, collide=True, rounds=()):
    """A closed solid of thickness `thick` along `ring`, its walls leaning
    out by the ring's lean: two skins, a top and a bottom square to the
    walls, ends if the ring is open, and a real reveal round every opening,
    square to the wall. An opening is (wall, u0, u1, z0, z1): u along the
    wall from its base start, z on the outer face. Corners are mitred, so a
    closed ring has no end faces at all. A round opening is (wall, uc, zc,
    r): a circle of radius r drawn in the wall's own leaning plane, so it is
    round on the face, centred uc along the wall and zc up its outer face;
    the shell leaves out the square ROUND_MARGIN round it and fills that
    back with a patch on each skin, fanned from the square's edge to the
    circle, and a reveal of ROUND_SEG facets square to the wall."""
    R = ring
    nseg = R.nseg
    squares = []             # each round opening's square, as an opening with no reveal of its own
    for wall, uc, zc, r in rounds:
        e = r + ROUND_MARGIN
        wc = R.w(zc)
        squares.append((wall, uc - e, uc + e, (wc - e) * R.cos, (wc + e) * R.cos))
    cut = list(openings) + squares
    stations = []            # per wall: sorted u's from 0 to the wall's length
    for i in range(nseg):
        us = {0.0, R.L[i]}
        for wall, u0, u1, oz0, oz1 in cut:
            if wall == i:
                assert 0.0 < u0 < u1 < R.L[i] and z0 < oz0 < oz1 < z1, (name, wall, u0, u1, oz0, oz1)
                us.update((u0, u1))
        stations.append(sorted(us))
    zs = {z0, z1}
    for _, _, _, oz0, oz1 in cut:
        zs.update((oz0, oz1))
    zs = sorted(zs)
    nz = len(zs) - 1

    def key(i, u):
        """A corner belongs to the wall that begins there."""
        if abs(u - R.L[i]) < 1e-9 and (R.closed or i < nseg - 1):
            return ((i + 1) % nseg, 0.0)
        return (i, u)

    bm = bmesh.new()
    verts = {}

    def vert(i, u, j, side):
        k = key(i, u)
        kk = (k, j, side)
        if kk not in verts:
            wi, wu = k
            if abs(wu) < 1e-9:
                m = R.mitre(wi)
            elif not R.closed and wi == nseg - 1 and abs(wu - R.L[wi]) < 1e-9:
                m = R.OUT[wi]
            else:
                m = R.OUT[wi]
            base = R.P[wi] + R.U[wi] * wu
            z = zs[j]
            p = base + m * (z * R.k)
            if side == 0:
                verts[kk] = bm.verts.new((p.x, p.y, z))
            else:
                q = p - m * (thick * R.cos)
                verts[kk] = bm.verts.new((q.x, q.y, z + thick * R.sin))
        return verts[kk]

    def in_opening(i, ua, ub, j):
        um, zm = (ua + ub) / 2, (zs[j] + zs[j + 1]) / 2
        return any(wall == i and u0 < um < u1 and oz0 < zm < oz1 for wall, u0, u1, oz0, oz1 in cut)

    for i in range(nseg):
        us = stations[i]
        for a, b in zip(us, us[1:]):
            for j in range(nz):
                if in_opening(i, a, b, j):
                    continue
                bm.faces.new((vert(i, a, j, 0), vert(i, b, j, 0), vert(i, b, j + 1, 0), vert(i, a, j + 1, 0)))
                bm.faces.new((vert(i, a, j, 1), vert(i, a, j + 1, 1), vert(i, b, j + 1, 1), vert(i, b, j, 1)))
            bm.faces.new((vert(i, a, 0, 0), vert(i, a, 0, 1), vert(i, b, 0, 1), vert(i, b, 0, 0)))
            bm.faces.new((vert(i, a, nz, 0), vert(i, b, nz, 0), vert(i, b, nz, 1), vert(i, a, nz, 1)))
    if not R.closed:
        for i, u in ((0, 0.0), (nseg - 1, R.L[nseg - 1])):
            for j in range(nz):
                bm.faces.new((vert(i, u, j, 0), vert(i, u, j + 1, 0), vert(i, u, j + 1, 1), vert(i, u, j, 1)))
    for wall, u0, u1, oz0, oz1 in openings:
        j0, j1 = zs.index(oz0), zs.index(oz1)
        us = stations[wall]
        for j in range(j0, j1):
            bm.faces.new((vert(wall, u0, j, 0), vert(wall, u0, j, 1), vert(wall, u0, j + 1, 1), vert(wall, u0, j + 1, 0)))
            bm.faces.new((vert(wall, u1, j, 0), vert(wall, u1, j + 1, 0), vert(wall, u1, j + 1, 1), vert(wall, u1, j, 1)))
        for a, b in zip(us, us[1:]):
            if a < u0 - 1e-9 or b > u1 + 1e-9:
                continue
            bm.faces.new((vert(wall, a, j0, 0), vert(wall, b, j0, 0), vert(wall, b, j0, 1), vert(wall, a, j0, 1)))
            bm.faces.new((vert(wall, a, j1, 0), vert(wall, a, j1, 1), vert(wall, b, j1, 1), vert(wall, b, j1, 0)))
    for (wall, uc, zc, r), (_, u0, u1, oz0, oz1) in zip(rounds, squares):
        round_patch(bm, R, vert, stations[wall], zs, wall, uc, zc, r, u0, u1, oz0, oz1, thick)
    return finish(name, bm, coll, mats, variant=variant, collide=collide)


def round_patch(bm, R, vert, us, zs, wall, uc, zc, r, u0, u1, z0, z1, thick):
    """Fill a round opening's square in a shell: on each skin, triangles
    fanned between the square's edge (every vertex the cells round it put
    there, so the skin stays closed) and the circle, by angle round the
    centre; then the round reveal between the two skins' circles."""
    fr = R.frame(wall)
    wc = R.w(zc)
    j0, j1 = zs.index(z0), zs.index(z1)
    inside = [u for u in us if u0 - 1e-9 <= u <= u1 + 1e-9]
    # the square's edge anticlockwise in the wall's (u, w) plane (outward on the outer skin)
    edge = [(u, j0) for u in inside] + [(u1, j) for j in range(j0 + 1, j1 + 1)] + \
           [(u, j1) for u in reversed(inside[:-1])] + [(u0, j) for j in range(j1 - 1, j0, -1)]
    angles = [math.tau * k / ROUND_SEG for k in range(ROUND_SEG)]

    def ang(u, w):
        return math.atan2(w - wc, u - uc)

    edge_a = [ang(u, R.w(zs[j])) for u, j in edge]
    # both loops unwrapped to rising angles, the circle starting at its
    # vertex nearest the square's first
    start = min(range(ROUND_SEG), key=lambda k: abs(math.remainder(angles[k] - edge_a[0], math.tau)))
    a0 = edge_a[0] + math.remainder(angles[start] - edge_a[0], math.tau)
    circ_a = [a0 + math.tau * k / ROUND_SEG for k in range(ROUND_SEG)]
    unwrapped = [edge_a[0]]
    for a in edge_a[1:]:
        while a <= unwrapped[-1]:
            a += math.tau
        unwrapped.append(a)
    rings = []
    for side, n in ((0, 0.0), (1, -thick)):
        sq = [vert(wall, u, j, side) for u, j in edge]
        circle = [bm.verts.new(fr.at(uc + r * math.cos(angles[(start + k) % ROUND_SEG]),
                                     wc + r * math.sin(angles[(start + k) % ROUND_SEG]), n)) for k in range(ROUND_SEG)]
        rings.append(circle)
        B, Ba = sq + [sq[0]], unwrapped + [unwrapped[0] + math.tau]
        C, Ca = circle + [circle[0]], circ_a + [circ_a[0] + math.tau]
        i = j = 0
        while i < len(sq) or j < ROUND_SEG:
            if j >= ROUND_SEG or (i < len(sq) and Ba[i + 1] <= Ca[j + 1]):
                tri = (B[i], B[i + 1], C[j])
                i += 1
            else:
                tri = (B[i], C[j + 1], C[j])
                j += 1
            bm.faces.new(tri if side == 0 else tuple(reversed(tri)))
    out, inn = rings
    for k in range(ROUND_SEG):
        l = (k + 1) % ROUND_SEG
        bm.faces.new((out[k], out[l], inn[l], inn[k]))


def corner_board(name, coll, mat, ring, i, z_lo, z_hi, variant):
    """The L-shaped corner board where wall i begins, an L in plan sheared
    up the leaning corner so each of its faces lies parallel to the wall it
    dresses; it stands CORNER_PROUD of both faces and CORNER_SUNK into
    them, so neither shares a plane with the wall or the other board."""
    o_prev, o = ring.OUT[i - 1 if i > 0 else ring.nseg - 1], ring.OUT[i]
    m = ring.mitre(i)
    c = ring.P[i]
    s, p, z = CORNER, CORNER_PROUD, CORNER_SUNK
    # (a, b) along the previous wall's outward and this wall's outward
    L = [(-z, -s), (p, -s), (p, p), (-s, p), (-s, -z), (-z, -z)]
    bm = bmesh.new()

    def at(a, b, h):
        q = c + o_prev * a + o * b + m * (h * ring.k)
        return bm.verts.new((q.x, q.y, h))

    lo = [at(a, b, z_lo) for a, b in L]
    hi = [at(a, b, z_hi) for a, b in L]
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    for a in range(6):
        b = (a + 1) % 6
        bm.faces.new((lo[a], lo[b], hi[b], hi[a]))
    return finish(name, bm, coll, [mat], variant=variant, collide=False)


# --- openings ------------------------------------------------------------------------

def casing(prefix, coll, mat, frame, u0, u1, z0, z1, variant, head=True, sill=True):
    """Chunky casing round an opening, square to its wall: jambs PROUD of
    the wall, the head and sill boards a centimetre prouder and a touch
    shallower, every board lapping 2 cm over the opening's edge."""
    w0, w1 = frame.w(z0), frame.w(z1)
    frame_box(f"{prefix}_jamb_a", coll, mat, frame, u0 - JAMB, u0 + 0.02, w0 - 0.02, w1 + 0.02, -SUNK, PROUD,
              variant=variant, collide=False)
    frame_box(f"{prefix}_jamb_b", coll, mat, frame, u1 - 0.02, u1 + JAMB, w0 - 0.02, w1 + 0.02, -SUNK, PROUD,
              variant=variant, collide=False)
    if head:
        frame_box(f"{prefix}_head", coll, mat, frame, u0 - JAMB - 0.03, u1 + JAMB + 0.03, w1 - 0.02, w1 + HEAD_T,
                  -SUNK + 0.005, PROUD + 0.01, variant=variant, collide=False)
    if sill:
        frame_box(f"{prefix}_sill", coll, mat, frame, u0 - JAMB - 0.03, u1 + JAMB + 0.03, w0 - SILL_T, w0 + 0.02,
                  -SUNK + 0.005, PROUD + 0.01, variant=variant, collide=False)


def pane(name, coll, mat, frame, u0, u1, z0, z1, variant, recess=0.08, thick=0.05):
    """A slab set in an opening, recessed into the wall, 2 cm into the
    reveals all round."""
    w0, w1 = frame.w(z0), frame.w(z1)
    return frame_box(name, coll, mat, frame, u0 - 0.02, u1 + 0.02, w0 - 0.02, w1 + 0.02, -(recess + thick), -recess,
                     variant=variant)


def hood(prefix, coll, m, frame, u0, u1, z1, variant):
    """The little gable hood over a side window: a solid gable in the wall's
    frame, its base over the head board, projecting HOOD_OUT, and a chevron
    of roofing on its two slopes sunk a centimetre into it."""
    wb = frame.w(z1) + HEAD_T + 0.01
    ua, ub = u0 - JAMB - HOOD_WING, u1 + JAMB + HOOD_WING
    um, wt = (u0 + u1) / 2, wb + HOOD_RISE
    frame_prism(f"{prefix}_hood", coll, [m["trim"]], frame, [(ua, wb), (ub, wb), (um, wt)], -0.02, HOOD_OUT,
                variant=variant, collide=False)
    # the roofing: a chevron of white boards 3 cm thick over the two slopes,
    # its underside 1 cm below them, its eaves 3 cm past the hood's base
    # corners; only its two top faces wear the roof (the photo's hood is
    # white from below, grey shingle on top)
    half, rise = (ub - ua) / 2, HOOD_RISE
    slope = math.hypot(half, rise)
    t = (half / slope, rise / slope)             # up the left slope
    n = (-rise / slope, half / slope)            # its outward normal
    ext, up, down = 0.03, 0.02, 0.01
    el = (ua - t[0] * ext, wb - t[1] * ext)      # the left eave, extended
    er = (ub + t[0] * ext, wb - t[1] * ext)
    outer = [(el[0] + n[0] * up, el[1] + n[1] * up), (um, wt + up * slope / half), (er[0] - n[0] * up, er[1] + n[1] * up)]
    inner = [(er[0] + n[0] * down, er[1] - n[1] * down), (um, wt - down * slope / half), (el[0] - n[0] * down, el[1] - n[1] * down)]
    roof = frame_prism(f"{prefix}_hood_roof", coll, [m["trim"], m["roof"]], frame, outer + inner, -0.015, HOOD_OUT + 0.03,
                       variant=variant, collide=False)
    for p in roof.data.polygons:
        if p.normal.z > 0.3:
            p.material_index = 1


def dress(prefix, coll, m, frame, u0, u1, z0, z1, variant, kind="window", hooded=False):
    """Casing and slab for one opening; a door takes no sill and its leaf
    sits nearer the face."""
    if kind == "door":
        casing(prefix, coll, m["trim"], frame, u0, u1, z0, z1, variant, sill=False)
        pane(f"{prefix}_leaf", coll, m["door"], frame, u0, u1, z0, z1, variant, recess=0.02)
    else:
        casing(prefix, coll, m["trim"], frame, u0, u1, z0, z1, variant)
        pane(f"{prefix}_pane", coll, m["glass"], frame, u0, u1, z0, z1, variant)
        if hooded:
            hood(prefix, coll, m, frame, u0, u1, z1, variant)


def round_window(prefix, coll, m, frame, uc, zc, r, variant):
    """The round window's chunky frame and pane, square to the leaning wall
    like the casings: the frame a ring from 2 cm inside the hole's edge to
    ROUND_FRAME outside it, SUNK into the wall and as proud as a head board;
    the pane a disc 2 cm into the round reveal, recessed as the others are.
    Their facets line up with the reveal's, 2 cm off it, so none shares its
    plane."""
    wc = frame.w(zc)
    angles = [math.tau * k / ROUND_SEG for k in range(ROUND_SEG)]

    def circle(bm, rad, n):
        return [bm.verts.new(frame.at(uc + rad * math.cos(a), wc + rad * math.sin(a), n)) for a in angles]

    bm = bmesh.new()
    ri, ro, n0, n1 = r - 0.02, r + ROUND_FRAME, -SUNK, PROUD + 0.01
    fo, fi, bi, bo = circle(bm, ro, n1), circle(bm, ri, n1), circle(bm, ri, n0), circle(bm, ro, n0)
    for k in range(ROUND_SEG):
        l = (k + 1) % ROUND_SEG
        for a, b in ((fo, fi), (fi, bi), (bi, bo), (bo, fo)):
            bm.faces.new((a[k], a[l], b[l], b[k]))
    finish(f"{prefix}_frame", bm, coll, [m["trim"]], variant=variant, collide=False)
    bm = bmesh.new()
    front, back = circle(bm, r + 0.02, -0.08), circle(bm, r + 0.02, -0.13)
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    for k in range(ROUND_SEG):
        l = (k + 1) % ROUND_SEG
        bm.faces.new((front[k], back[k], back[l], front[l]))
    finish(f"{prefix}_pane", bm, coll, [m["glass"]], variant=variant)


# --- the tower ---------------------------------------------------------------------------

def tower_ring(spec):
    hx, hy = spec["base"][0] / 2, spec["base"][1] / 2
    # front (U = +x), right (+y), back (-x), left (-y): anticlockwise from the front-left corner
    return Ring([(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)], spec["lean"])


FRONT, RIGHT, BACK, LEFT = 0, 1, 2, 3


def round_radius(spec):
    """The round window's glass radius: ROUND_OF_FACE of the front face's
    width at ROUND_Z, to the centimetre across."""
    return round(ROUND_OF_FACE * (spec["base"][0] - 2 * tower_ring(spec).inset(ROUND_Z)), 2) / 2


def build_tower(coll, m, variant, prefix, spec):
    """The flared block: the tapered shell with every opening cut, its
    corner boards, casings, hoods, panes, the balcony and its door."""
    R = tower_ring(spec)
    wing = spec["wing_side"]
    # the photographed side: two hooded windows one over the other, at
    # SIDE_WINDOW_AT of the depth from the front, or further forward where
    # the back corner, leaning in, would come within HOOD_AIR_SIDE of the upper
    # hood's eave (its corner board by then CORNER past the corner; `bell`);
    # the opposite side takes one plain upstairs window unless the wing
    # rises past its sill; the back carries the balcony door at the window
    # side's end and nothing below (a window there would sit under the
    # deck's beams)
    side = RIGHT if wing < 0 else LEFT
    hood_half = WIN_W / 2 + JAMB + HOOD_WING + 0.04       # the roofing's eaves run 3 cm past the hood
    from_back = max((1.0 - SIDE_WINDOW_AT) * R.L[side],
                    R.inset(SIDE_UPPER[1] + HOOD_PEAK) + CORNER + HOOD_AIR_SIDE + hood_half)
    u_c = R.L[side] - from_back if side == RIGHT else from_back
    side_windows = [(side, u_c - WIN_W / 2, u_c + WIN_W / 2, *SIDE_LOWER),
                    (side, u_c - WIN_W / 2, u_c + WIN_W / 2, *SIDE_UPPER)]
    other = LEFT if side == RIGHT else RIGHT
    uo = R.L[other] / 2
    plain = [] if spec["wing_eave"] > UPPER_SILL else [(other, uo - WIN_W / 2, uo + WIN_W / 2, UPPER_SILL, UPPER_HEAD)]
    # the back wall runs -x, so the window side (+x) is near u = 0 when the
    # wing is on -x; the deck's centre is 0.9 m in from that corner where
    # the corner stands at the deck's height, u measured along the base
    in_at_deck = 0.25 + BALCONY_W / 2 + R.inset(UPPER_FLOOR)
    ud = in_at_deck if wing < 0 else R.L[BACK] - in_at_deck
    door = (BACK, ud - 0.40, ud + 0.40, UPPER_FLOOR + THRESHOLD, UPPER_HEAD)
    # the leaning front wall stands inside the bay's three-light window, by
    # the glass at 3 degrees in front of it (`gentle`): cut the window on
    # through it, so it is a hole into the room on every variant
    hx = spec["base"][0] / 2
    ba, bb = bay_window(wing)
    bay_cut = (FRONT, ba + hx - BAY_CUT, bb + hx + BAY_CUT, BAY_SILL - BAY_CUT, BAY_HEAD + BAY_CUT)
    # the round window upstairs on the front, its glass sized to the face
    r = round_radius(spec)
    rnd = (FRONT, R.L[FRONT] / 2, ROUND_Z, r)
    openings = side_windows + plain + [door, bay_cut]
    tapered_shell(f"{prefix}walls", coll, R, -BELOW, WALL_TOP, openings, [m["walls"]], variant=variant, rounds=[rnd])
    round_window(f"{prefix}round_window", coll, m, R.frame(FRONT), rnd[1], ROUND_Z, r, variant)
    # the front corners' boards start inside the bay's roof slab: below it
    # the bay's and the wing's vertical walls stand in front of the leaning
    # corner and wear their own boards; the back corners' run to the ground
    for i in range(4):
        z_lo = BAY_EAVE + 0.05 if i in (FRONT, RIGHT) else -BELOW + 0.01
        corner_board(f"{prefix}corner_{i}", coll, m["trim"], R, i, z_lo, BED_Z0 + 0.06, variant)
    for k, (wall, u0, u1, z0, z1) in enumerate(side_windows):
        dress(f"{prefix}side{k}", coll, m, R.frame(wall), u0, u1, z0, z1, variant, hooded=True)
    for k, (wall, u0, u1, z0, z1) in enumerate(plain):
        dress(f"{prefix}plain{k}", coll, m, R.frame(wall), u0, u1, z0, z1, variant)
    dress(f"{prefix}balcony_door", coll, m, R.frame(door[0]), door[1], door[2], door[3], door[4], variant, kind="door")
    build_balcony(coll, m, variant, prefix, R, BACK, ud)
    build_cornice(coll, m, variant, prefix, R, spec)


def build_balcony(coll, m, variant, prefix, R, wall, ud):
    """A small deck square off the wall at the upper floor, on two beams
    buried in the wall, a post at each outer corner and a top and mid rail
    round three sides, the side rails run 2 cm into the leaning wall."""
    out = R.OUT[wall]
    U = R.U[wall]
    base = R.P[wall] + U * ud

    def face_y(z):
        """The wall's outer face at height z, along `out` from `base`."""
        return R.out_at(wall, z)

    def pt(a, b, z):
        """Along the wall (a, from ud) and out from the base line (b)."""
        q = base + U * a + out * b
        return (q.x, q.y, z)

    def slab(name, mat, a0, a1, b0, b1, z0, z1, collide=True):
        bm = bmesh.new()
        lo = [bm.verts.new(pt(a, b, z0)) for a, b in ((a0, b0), (a1, b0), (a1, b1), (a0, b1))]
        hi = [bm.verts.new(pt(a, b, z1)) for a, b in ((a0, b0), (a1, b0), (a1, b1), (a0, b1))]
        bm.faces.new(lo)
        bm.faces.new(list(reversed(hi)))
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        return finish(name, bm, coll, [mat], variant=variant, collide=collide)

    hw = BALCONY_W / 2
    z_deck = UPPER_FLOOR
    b_wall = face_y(z_deck) - 0.04                       # 4 cm into the wall at the deck's level
    b_edge = face_y(z_deck) + BALCONY_D
    slab(f"{prefix}balcony_deck", m["trim"], -hw, hw, b_wall, b_edge, z_deck - DECK_T, z_deck)
    for tag, a in (("a", -hw + 0.12), ("b", hw - 0.12 - 0.10)):
        slab(f"{prefix}balcony_beam_{tag}", m["trim"], a, a + 0.10, face_y(z_deck - DECK_T) - 0.06, b_edge - 0.03,
             z_deck - DECK_T - 0.12, z_deck - DECK_T + 0.02, collide=False)
    # the posts stand 2 cm over the top rail, which is a centimetre deeper
    # than they are, so no two of the three share a face
    for tag, a in (("a", -hw + 0.01), ("b", hw - 0.01 - POST)):
        slab(f"{prefix}balcony_post_{tag}", m["trim"], a, a + POST, b_edge - 0.01 - POST, b_edge - 0.01,
             z_deck - 0.02, z_deck + RAIL_H + 0.02)
    for tag, z1, depth in (("top", z_deck + RAIL_H, POST + 0.01), ("mid", z_deck + MID_RAIL, 0.05)):
        bc = b_edge - 0.01 - POST / 2
        slab(f"{prefix}balcony_rail_{tag}_f", m["trim"], -hw + 0.015, hw - 0.015, bc - depth / 2, bc + depth / 2,
             z1 - 0.05, z1, collide=False)
        # the side rails end at the posts' centres, inside both the post
        # and the front rail, and ride 5 mm higher than the front rail
        for stag, a in (("a", -hw + 0.01 + POST / 2), ("b", hw - 0.01 - POST / 2)):
            slab(f"{prefix}balcony_rail_{tag}_{stag}", m["trim"], a - depth / 2, a + depth / 2, face_y(z1) - 0.02,
                 bc, z1 - 0.05 + 0.005, z1 + 0.005, collide=False)


def build_cornice(coll, m, variant, prefix, R, spec):
    """The entablature round the tower's top: a bed board ring, the plain
    frieze ring (the walls end inside it), a soffit slab over the whole
    tower, the fascia ring round it, and over that the cap: a low gable
    whose end triangles are the shingled pediments under raking boards, or a
    hip."""
    hx, hy = spec["base"][0] / 2, spec["base"][1] / 2
    hxe, hye = hx + R.k * EAVE, hy + R.k * EAVE            # the walls' outer faces at the eave
    rect_ring = lambda ox, oy: Ring([(-ox, -oy), (ox, -oy), (ox, oy), (-ox, oy)], 0.0)
    tapered_shell(f"{prefix}bed_board", coll, rect_ring(hxe + BED_OUT, hye + BED_OUT), BED_Z0, BED_Z1, (), [m["trim"]],
                  thick=BED_OUT + BED_IN, variant=variant, collide=False)
    tapered_shell(f"{prefix}frieze", coll, rect_ring(hxe + FRIEZE_OUT, hye + FRIEZE_OUT), EAVE, FRIEZE_Z1, (), [m["trim"]],
                  thick=FRIEZE_OUT + FRIEZE_IN, variant=variant, collide=False)
    xe, ye = hxe + FRIEZE_OUT + OVER, hye + FRIEZE_OUT + OVER   # the fascia's outer faces
    box(f"{prefix}soffit", coll, m["trim"], -(xe - 0.02), xe - 0.02, -(ye - 0.02), ye - 0.02, SOFFIT_Z0, SOFFIT_Z0 + SOFFIT_T,
        variant=variant, collide=False)
    tapered_shell(f"{prefix}fascia", coll, rect_ring(xe, ye), CFASCIA_Z0, CFASCIA_Z1, (), [m["trim"]],
                  thick=CFASCIA_T, variant=variant, collide=False)
    if spec["cap"] == "pediment":
        gable_cap(coll, m, variant, prefix, xe, ye)
    else:
        hip_cap(coll, m, variant, prefix, xe, ye)


def gable_cap(coll, m, variant, prefix, xe, ye):
    """A low gable along Y over the fascia box, a centimetre inside its
    faces and 2 cm into its top; the end triangles wear the pediment's
    shingles, and a raking board runs up each slope at each end, sunk a
    centimetre into the roof so the two share no plane."""
    x, y = xe - 0.01, ye - 0.01
    zb = ROOF_Z0
    zr = zb + x * math.tan(PITCH)
    bm = bmesh.new()
    v = {}
    for name, co in (("fl", (-x, -y, zb)), ("fr", (x, -y, zb)), ("br", (x, y, zb)), ("bl", (-x, y, zb)),
                     ("rf", (0.0, -y, zr)), ("rb", (0.0, y, zr))):
        v[name] = bm.verts.new(co)
    bm.faces.new((v["fl"], v["bl"], v["br"], v["fr"]))             # underside
    bm.faces.new((v["fl"], v["fr"], v["rf"])).material_index = 1    # the front pediment
    bm.faces.new((v["br"], v["bl"], v["rb"])).material_index = 1    # the back one
    bm.faces.new((v["fr"], v["br"], v["rb"], v["rf"]))              # the right slope
    bm.faces.new((v["bl"], v["fl"], v["rf"], v["rb"]))              # the left slope
    finish(f"{prefix}roof", bm, coll, [m["roof"], m["pediment"]], variant=variant)
    # the raking boards: a parallelogram up each slope in the (x, z) plane,
    # RAKE_H tall, 1 cm below the slope, extruded through the end wall from
    # 3 cm inside the fascia to 4 cm proud of it; the pair overlap 3 cm at the peak
    rise = math.tan(PITCH)
    for end, (y0, y1) in (("f", (-ye - 0.04, -ye + 0.03)), ("b", (ye - 0.03, ye + 0.04))):
        for side, sx in (("l", -1), ("r", 1)):
            x_eave, x_peak = sx * (xe + 0.02), -sx * 0.03
            if sx > 0:      # the right board is 5 mm thinner each side, so the pair's faces never share
                y0, y1 = y0 + 0.005, y1 - 0.005
            z_at = lambda px: zb + (x - abs(px)) * rise      # the slope's surface, continued past the eave
            prof = [(x_eave, z_at(x_eave) - 0.01), (x_peak, z_at(x_peak) - 0.01),
                    (x_peak, z_at(x_peak) - 0.01 + RAKE_H), (x_eave, z_at(x_eave) - 0.01 + RAKE_H)]
            if sx > 0:
                prof.reverse()
            finish(f"{prefix}rake_{end}{side}", prism_bm(prof, "y", y0, y1), coll, [m["trim"]], variant=variant, collide=False)


def hip_cap(coll, m, variant, prefix, xe, ye):
    """A low hip over the fascia box, the ridge along the longer axis."""
    x, y = xe - 0.01, ye - 0.01
    zb = ROOF_Z0
    bm = bmesh.new()
    c = [bm.verts.new(p) for p in ((-x, -y, zb), (x, -y, zb), (x, y, zb), (-x, y, zb))]
    bm.faces.new(list(reversed(c)))
    if y >= x:
        zr = zb + x * math.tan(PITCH)
        r = [bm.verts.new(p) for p in ((0.0, -(y - x), zr), (0.0, y - x, zr))]
        bm.faces.new((c[0], c[1], r[0]))
        bm.faces.new((c[1], c[2], r[1], r[0]))
        bm.faces.new((c[2], c[3], r[1]))
        bm.faces.new((c[3], c[0], r[0], r[1]))
    else:
        zr = zb + y * math.tan(PITCH)
        r = [bm.verts.new(p) for p in ((-(x - y), 0.0, zr), (x - y, 0.0, zr))]
        bm.faces.new((c[0], c[1], r[1], r[0]))
        bm.faces.new((c[1], c[2], r[1]))
        bm.faces.new((c[2], c[3], r[0], r[1]))
        bm.faces.new((c[3], c[0], r[0]))
    finish(f"{prefix}roof", bm, coll, [m["roof"]], variant=variant)


# --- the bay and the wing -----------------------------------------------------------------

def wing_back_y(spec, R):
    """The wing's back wall's y: WING_BACK, or less when the tower's back
    face has leaned in past it by the wing's top (the strong lean), so the
    wing's end stays inside the tower the whole way up."""
    hy = spec["base"][1] / 2
    return min(WING_BACK, hy - R.inset(spec["wing_eave"] + 0.03) - 0.10)


def build_wing(coll, m, variant, prefix, spec):
    """The ground floor's front bay and the wing beside the tower, vertical
    walls on the same shell as the tower (no lean). The tower leans away
    from them going up, so every end that meets it is carried to where the
    tower's face stands at the wing's top, plus 2 cm: at the ground that end
    is deep in the tower's wall or just inside its hollow, never outside.
    The bay's front is flush with the tower's base line, so the bay is the
    ground floor's front under a ledge: its far end is a fin the tower's
    leaning corner reveals as a wedge, the photo's dark strip beside the
    corner board. With the wing one storey the bay's front and the wing's
    are one wall under one roof slab; a two-storey wing gets its own roof
    and the bay's front stands 2 cm back from the wing's, its near end
    buried in the wing's wall. The three-light window on the bay, the door
    at the wing's far end, a window on the wing's outer side and on its
    back; vertical corner boards on the wing's and the bay's own corners."""
    s = spec["wing_side"]
    hx, hy = spec["base"][0] / 2, spec["base"][1] / 2
    R = tower_ring(spec)
    one_storey = abs(spec["wing_eave"] - BAY_EAVE) < 1e-6
    wing_top = spec["wing_eave"] + 0.03
    bay_top = BAY_EAVE + 0.03
    back = wing_back_y(spec, R)
    wx_in = s * (hx - R.inset(wing_top) - 0.02)          # the wing's end, inside the tower's side up to the wing's top
    wx_out = s * (hx + WING_W)                           # the wing's outer face
    bx = -s * hx                                         # the bay's far end: the fin, flush with the tower's base corner
    y_fin = -hy + R.inset(BAY_EAVE + FLAT_T) - 0.01      # the fin's end, a centimetre short of the slab's notch
    if one_storey:
        # one shell: the wing's back and outer side, the front across both
        # (flush with the tower's base line), and the fin back into the tower
        if s < 0:
            pts = [(wx_in, back), (wx_out, back), (wx_out, -hy), (bx, -hy), (bx, y_fin)]
            front_wall, back_wall, side_wall = 2, 0, 1
        else:
            pts = [(bx, y_fin), (bx, -hy), (wx_out, -hy), (wx_out, back), (wx_in, back)]
            front_wall, back_wall, side_wall = 1, 3, 2
        ring = Ring(pts, 0.0, closed=False)
        openings = wing_openings(ring, s, hx, hy, wx_out, back, front_wall, back_wall, side_wall, one_storey=True)
        tapered_shell(f"{prefix}wing_walls", coll, ring, -BELOW, wing_top, openings, [m["wing"]], variant=variant)
        dress_wing(coll, m, variant, prefix, ring, openings, front_wall)
        for i in (1, 2, 3):
            corner_board(f"{prefix}wing_corner_{i}", coll, m["trim"], ring, i, -BELOW + 0.01, BAY_EAVE + 0.02, variant)
        flat_roof(coll, m, variant, prefix, R, spec, s, hx, hy, back, BAY_EAVE, with_bay=True)
    else:
        # the wing alone: back, outer side, front, ending in the tower's wall
        if s < 0:
            pts = [(wx_in, back), (wx_out, back), (wx_out, -hy), (wx_in, -hy)]
            front_wall, back_wall, side_wall = 2, 0, 1
        else:
            pts = [(wx_in, -hy), (wx_out, -hy), (wx_out, back), (wx_in, back)]
            front_wall, back_wall, side_wall = 0, 2, 1
        ring = Ring(pts, 0.0, closed=False)
        openings = wing_openings(ring, s, hx, hy, wx_out, back, front_wall, back_wall, side_wall, one_storey=False)
        tapered_shell(f"{prefix}wing_walls", coll, ring, -BELOW, wing_top, openings, [m["wing"]], variant=variant)
        dress_wing(coll, m, variant, prefix, ring, openings, front_wall)
        for i in (1, 2):
            corner_board(f"{prefix}wing_corner_{i}", coll, m["trim"], ring, i, -BELOW + 0.01, spec["wing_eave"] + 0.02, variant)
        flat_roof(coll, m, variant, prefix, R, spec, s, hx, hy, back, spec["wing_eave"], with_bay=False)
        # the bay: its front 2 cm behind the wing's, its near end buried in
        # the wing's front wall, its far end the fin
        near = s * (hx + 0.02)
        bf = -hy + 0.02
        if s < 0:
            bring = Ring([(near, bf), (bx, bf), (bx, y_fin)], 0.0, closed=False)
            bay_wall, fin_corner = 0, 1
        else:
            bring = Ring([(bx, y_fin), (bx, bf), (near, bf)], 0.0, closed=False)
            bay_wall, fin_corner = 1, 1
        bw = bay_window(s)
        bopen = [(bay_wall, *sorted((bring.u_at(bay_wall, (bw[0], bf)), bring.u_at(bay_wall, (bw[1], bf)))), BAY_SILL, BAY_HEAD)]
        # its foot a centimetre above the wing's and the corner boards', so no bottom is shared
        tapered_shell(f"{prefix}bay_walls", coll, bring, -BELOW + 0.02, bay_top, bopen, [m["wing"]], variant=variant)
        fr = bring.frame(bay_wall)
        dress(f"{prefix}bay_window", coll, m, fr, bopen[0][1], bopen[0][2], BAY_SILL, BAY_HEAD, variant)
        mullions(coll, m, variant, prefix, fr, bopen[0][1], bopen[0][2], BAY_SILL, BAY_HEAD)
        corner_board(f"{prefix}bay_corner", coll, m["trim"], bring, fin_corner, -BELOW + 0.025, BAY_EAVE + 0.02, variant)
        flat_roof(coll, m, variant, prefix, R, spec, s, hx, hy, back, BAY_EAVE, with_bay=True, bay_only=True)


def bay_window(s):
    """The three-light window's glass, x, on whichever side the wing is."""
    a, b = BAY_WIN
    return (a, b) if s < 0 else (-b, -a)


def wing_openings(ring, s, hx, hy, wx_out, back, front_wall, back_wall, side_wall, one_storey):
    """The wing's openings in the open shell's walls: the door near the
    wing's far end, the bay's three-light window (on the one-storey shell),
    a window on the outer side and one on the back; a second storey gets a
    window over the door and over the side window."""
    def span(wall, p, q):
        """An opening between two plan points on a wall, as sorted u's."""
        return tuple(sorted((ring.u_at(wall, p), ring.u_at(wall, q))))

    front_y = -hy
    dx = s * (hx + WING_W - 0.70)                 # the door's centre, 0.7 m in from the wing's outer face
    door = span(front_wall, (dx - DOOR_W / 2, front_y), (dx + DOOR_W / 2, front_y))
    yc = (back + front_y) / 2
    side = span(side_wall, (wx_out, yc - 0.45), (wx_out, yc + 0.45))
    xc = s * (hx + WING_W / 2)
    back_win = span(back_wall, (xc - 0.45, back), (xc + 0.45, back))
    ops = [(front_wall, *door, THRESHOLD, DOOR_H), (side_wall, *side, BAY_SILL, BAY_HEAD), (back_wall, *back_win, BAY_SILL, BAY_HEAD)]
    if one_storey:
        a, b = bay_window(s)
        ops.append((front_wall, *span(front_wall, (a, front_y), (b, front_y)), BAY_SILL, BAY_HEAD))
    else:
        up0, up1 = BAY_EAVE + 0.55, BAY_EAVE + 0.55 + 1.2
        ops.append((front_wall, *door, up0, up1))
        ops.append((side_wall, *side, up0, up1))
    return ops


def dress_wing(coll, m, variant, prefix, ring, openings, front_wall):
    """Casings and slabs for every wing opening; the door's leaf, the
    three-light window's two mullions."""
    for k, (wall, u0, u1, z0, z1) in enumerate(openings):
        fr = ring.frame(wall)
        if abs(z0 - THRESHOLD) < 1e-9:
            dress(f"{prefix}door", coll, m, fr, u0, u1, z0, z1, variant, kind="door")
        elif wall == front_wall and abs(z0 - BAY_SILL) < 1e-9 and (u1 - u0) > 1.2:
            # the three-light window
            dress(f"{prefix}bay_window", coll, m, fr, u0, u1, z0, z1, variant)
            mullions(coll, m, variant, prefix, fr, u0, u1, z0, z1)
        else:
            dress(f"{prefix}wing_win{k}", coll, m, fr, u0, u1, z0, z1, variant)


def mullions(coll, m, variant, prefix, frame, u0, u1, z0, z1):
    """Two chunky mullions dividing the bay window into three lights, set
    just proud of the pane."""
    w0, w1 = frame.w(z0), frame.w(z1)
    for k in (1, 2):
        uc = u0 + (u1 - u0) * k / 3
        frame_box(f"{prefix}mullion_{k}", coll, m["trim"], frame, uc - 0.035, uc + 0.035, w0 - 0.01, w1 + 0.01, -0.075, -0.03,
                  variant=variant, collide=False)


def flat_roof(coll, m, variant, prefix, R, spec, s, hx, hy, back, eave, with_bay, bay_only=False):
    """The flat roof: a slab from FLAT_OVER past the walls back to 4 cm
    inside the tower's leaning wall at the slab's top, an L over the wing
    and the bay when they share an eave. The tower's faces have leaned in by
    the slab's top, so where the slab runs past the tower's corner it is
    notched back to the face's line there, and its lap into the tower is
    only as long as the tower's face at that height; a fascia round its
    open sides, its ends short of the tower's face at their own foot."""
    z0, z1 = eave, eave + FLAT_T
    kz = R.inset(z1)                              # the tower's faces at the slab's top, in from the base line
    y_front = -hy - FLAT_OVER
    y_notch = -hy + kz                            # the slab's back edge beside the tower's leaning front corner
    into_front = y_notch + 0.04
    xc = -s * (hx - kz - 0.02)                    # the lap into the front wall ends inside the leaning corner
    bay_far = -s * (hx + 0.04)                    # 4 cm past the bay's end fin, 1 cm past its corner board's face
    if bay_only:
        near = s * (hx + 0.04)                    # 4 cm into the wing's front wall
        poly = [(near, y_front), (bay_far, y_front), (bay_far, y_notch), (xc, y_notch), (xc, into_front), (near, into_front)]
        name, runs = "bay_roof", [(bay_far, y_front), (near, y_front)]
    else:
        x_out = s * (hx + WING_W + FLAT_OVER)
        x_face = s * (hx - kz + 0.01)             # a centimetre outside the tower's side face at the slab's top
        into_side = s * (hx - kz - 0.04)
        y_back = back + FLAT_OVER
        y_lap_back = min(y_back, hy - kz - 0.02)  # the lap stops inside the tower's back face
        y_lap_front = -hy + kz + 0.02
        if with_bay:
            poly = [(x_out, y_front), (bay_far, y_front), (bay_far, y_notch), (xc, y_notch), (xc, into_front), (into_side, into_front),
                    (into_side, y_lap_back), (x_face, y_lap_back), (x_face, y_back), (x_out, y_back)]
        else:
            poly = [(x_out, y_front), (x_face, y_front), (x_face, y_lap_front), (into_side, y_lap_front), (into_side, y_lap_back),
                    (x_face, y_lap_back), (x_face, y_back), (x_out, y_back)]
        x_fas = s * (hx - R.inset(z1 - FASCIA_H) + 0.01)   # the back fascia's end clears the face at the fascia's foot
        name, runs = "wing_roof", [(bay_far if with_bay else x_fas, y_front), (x_out, y_front), (x_out, y_back), (x_fas, y_back)]
    # a notch that closes up (the lap already inside the face) leaves
    # repeated corners; drop them
    clean = [poly[0]]
    for p in poly[1:]:
        if abs(p[0] - clean[-1][0]) > 1e-6 or abs(p[1] - clean[-1][1]) > 1e-6:
            clean.append(p)
    if abs(clean[0][0] - clean[-1][0]) < 1e-6 and abs(clean[0][1] - clean[-1][1]) < 1e-6:
        clean.pop()
    finish(f"{prefix}{name}", prism_bm(clean, "z", z0, z1), coll, [m["roof"]], variant=variant)
    fascia_run(coll, m, variant, f"{prefix}{name.replace('roof', 'fascia')}", runs, z1, s)


def fascia_run(coll, m, variant, name, pts, z_top, s):
    """A fascia board along a run of roof edges: an open shell FASCIA_T
    thick standing just outside the slab's edge, FASCIA_H tall, hanging a
    little below the slab and 2 cm above its top. Its ends are cut where the
    run ends, 2 cm short of a leaning wall."""
    # the board's outer face stands 0.005 past the slab's edge: push the
    # run outward (its inside is on the left, so outward is to the right)
    pts = [Vector(p) for p in pts]
    if s < 0:
        pts.reverse()
    ring = Ring(pts, 0.0, closed=False)
    shifted = []
    for i, p in enumerate(pts):
        if i == 0:
            o = ring.OUT[0]
        elif i == len(pts) - 1:
            o = ring.OUT[ring.nseg - 1]
        else:
            o = ring.mitre(i)
        shifted.append(p + o * 0.005)
    # trim the ends 2 cm along the run so they stop short of a wall
    shifted[0] = shifted[0] + ring.U[0] * 0.02
    shifted[-1] = shifted[-1] - ring.U[ring.nseg - 1] * 0.02
    ring2 = Ring([(p.x, p.y) for p in shifted], 0.0, closed=False)
    tapered_shell(name, coll, ring2, z_top - FASCIA_H + 0.02, z_top + 0.02, (), [m["trim"]], thick=FASCIA_T,
                  variant=variant, collide=False)


# --- reference ----------------------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm = prism_bm(ring, "z", 0.0, height - 0.40)
    body_verts = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:
        if v not in body_verts:
            v.co.z += height - 0.17
    obj = finish(name, bm, coll, [mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0))], collide=False, flat=False)
    obj.location = (x, y, z)
    return obj


def outline(name, coll, pts, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in pts]
    for i in range(len(vs)):
        bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def build_reference(reference):
    spec = SPEC["photo"]
    hx, hy = spec["base"][0] / 2, spec["base"][1] / 2
    R = tower_ring(spec)
    ex, ey = hx - R.inset(EAVE), hy - R.inset(EAVE)
    outline(f"tower_base_{spec['base'][0]:.1f}x{spec['base'][1]:.1f}".replace(".", "p"), reference,
            [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)])
    outline(f"tower_eave_{2 * ex:.2f}x{2 * ey:.2f}".replace(".", "p"), reference,
            [(-ex, -ey), (ex, -ey), (ex, ey), (-ex, ey)], z=EAVE)
    back = wing_back_y(spec, R)
    outline(f"wing_{WING_W:.1f}x{back + hy:.1f}".replace(".", "p"), reference,
            [(-hx, -hy), (-hx - WING_W, -hy), (-hx - WING_W, back), (-hx, back)])
    figure("figure_1p7m", reference, *FIGURE_AT)
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        reference.objects.link(marker)


# --- checks ------------------------------------------------------------------------------

def triangles(objs):
    total = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            total += len(o.data.loop_triangles)
    return total


def coplanar_pairs(objs, tol=1e-4):
    """Pairs of faces from different objects lying in one plane and
    overlapping in area (by their bounds in the plane): the z-fights."""
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


def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def world_bvh(o):
    mw = o.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])


def glass_seen(objs):
    """Every pane looked at square-on from 2 m outside, through its opening:
    a grid of rays over the glass 6 cm in from its edges (the casing laps
    over them), and what each ray reaches first. A window is right when
    every ray reaches its pane or a mullion; a wall there is the fault
    `gentle`'s bay window had."""
    trees = {o.name: world_bvh(o) for o in objs}
    seen = []
    for o in objs:
        if not o.name.endswith("_pane"):
            continue
        mw, me = o.matrix_world, o.data
        casing = bpy.data.objects.get(o.name[:-5] + "_jamb_a") or bpy.data.objects.get(o.name[:-5] + "_frame")
        toward = sum((mw @ Vector(c) for c in casing.bound_box), Vector()) / 8 - \
            sum((mw @ v.co for v in me.vertices), Vector()) / len(me.vertices)
        front = max(sorted(me.polygons, key=lambda p: -p.area)[:2], key=lambda p: (mw.to_3x3() @ p.normal).dot(toward))
        n = (mw.to_3x3() @ front.normal).normalized()
        pts = [mw @ me.vertices[i].co for i in front.vertices]
        c = sum(pts, Vector()) / len(pts)
        a = (pts[1] - pts[0]).normalized()
        b = n.cross(a)
        poly = [((q - c).dot(a), (q - c).dot(b)) for q in pts]
        lo_u, hi_u = min(p[0] for p in poly), max(p[0] for p in poly)
        lo_v, hi_v = min(p[1] for p in poly), max(p[1] for p in poly)
        sgn = 1.0 if sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1])) > 0 else -1.0

        def inside(u, v):
            for (pu, pv), (qu, qv) in zip(poly, poly[1:] + poly[:1]):
                eu, ev = qu - pu, qv - pv
                if sgn * (eu * (v - pv) - ev * (u - pu)) / math.hypot(eu, ev) < 0.06:
                    return False
            return True

        hits = {}
        for i in range(1, 24):
            for j in range(1, 24):
                u, v = lo_u + (hi_u - lo_u) * i / 24, lo_v + (hi_v - lo_v) * j / 24
                if not inside(u, v):
                    continue
                p = c + a * u + b * v
                best = None
                for name, t in trees.items():
                    hit = t.ray_cast(p + n * 2.0, -n, 2.5)
                    if hit[0] is not None and (best is None or hit[3] < best[1]):
                        best = (name, hit[3])
                k = "nothing" if not best else "glass" if best[0] == o.name else "mullions" if "mullion" in best[0] else best[0]
                hits[k] = hits.get(k, 0) + 1
        total = sum(hits.values())
        seen.append((o.name, hits.get("glass", 0) / total, {k: x / total for k, x in hits.items() if k != "glass"}))
    return seen


def hood_clearance(objs, prefix):
    """Each window hood's clear air, with the tower's wall it is sunk into
    and its own window's parts left out: straight up from every point of
    its top surfaces to the first part over it, and the nearest any other
    part comes to it at all; and whether it touches anything."""
    trees = {o.name: world_bvh(o) for o in objs}
    wall = f"{prefix}walls"
    found = []
    for h in [o for o in objs if o.name.endswith("_hood")]:
        win = h.name[:-len("hood")]
        own = [o for o in objs if o.name.startswith(win)]
        others = [o for o in objs if o not in own and o.name != wall]
        pts = []
        for o in own:
            if "hood" not in o.name:
                continue
            mw = o.matrix_world
            o.data.calc_loop_triangles()
            for t in o.data.loop_triangles:
                if (mw.to_3x3() @ t.normal).normalized().z < 0.3:
                    continue
                a, b, c = (mw @ o.data.vertices[i].co for i in t.vertices)
                for i in range(24):
                    for j in range(24 - i):
                        p = a + (b - a) * (i + 0.5) / 24.5 + (c - a) * (j + 0.5) / 24.5
                        loc, nrm, _, d = trees[wall].find_nearest(p)
                        if loc is not None and (d < 0.003 or (p - loc).dot(nrm) < 0):
                            continue        # in or on the wall the hood is sunk into
                        pts.append(p)
        up, over = 99.0, "nothing"
        for p in pts:
            for o in others:
                hit = trees[o.name].ray_cast(p + Vector((0, 0, 1e-4)), Vector((0, 0, 1)), 5.0)
                if hit[0] is not None and hit[3] < up:
                    up, over = hit[3], o.name
        # the nearest approach, from points along every edge both ways
        def edge_points(o, step=0.02):
            mw = o.matrix_world
            out = []
            for e in o.data.edges:
                p, q = (mw @ o.data.vertices[i].co for i in e.vertices)
                k = max(1, int((q - p).length / step))
                out += [p + (q - p) * (t / k) for t in range(k + 1)]
            return out

        hood_pts = [p for o in own if "hood" in o.name for p in edge_points(o)]
        lo = Vector((min(p.x for p in hood_pts), min(p.y for p in hood_pts), min(p.z for p in hood_pts))) - Vector((0.6,) * 3)
        hi = Vector((max(p.x for p in hood_pts), max(p.y for p in hood_pts), max(p.z for p in hood_pts))) + Vector((0.6,) * 3)
        near, nearest, touch = 99.0, "nothing", []
        for o in others:
            box = [o.matrix_world @ Vector(c) for c in o.bound_box]
            if any(min(q[k] for q in box) > hi[k] or max(q[k] for q in box) < lo[k] for k in range(3)):
                continue
            for p in hood_pts:
                d = trees[o.name].find_nearest(p)[3]
                if d is not None and d < near:
                    near, nearest = d, o.name
            for p in edge_points(o):
                for hp in own:
                    if "hood" in hp.name:
                        d = trees[hp.name].find_nearest(p)[3]
                        if d is not None and d < near:
                            near, nearest = d, o.name
            if any(trees[hp.name].overlap(trees[o.name]) for hp in own if "hood" in hp.name):
                touch.append(o.name)
        found.append((h.name, up, over, near, nearest, touch))
    return found


def report(variant):
    bpy.context.view_layer.update()
    objs = variant_objects(variant)
    tris = triangles(objs)
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    pairs = coplanar_pairs(objs)
    used = sorted({s.material.name for o in objs for s in o.material_slots if s.material})
    print(f"{PROP}: {variant}: {len(objs)} parts, {tris} triangles, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, z {min(zs):.2f}..{max(zs):.2f}; "
          f"{len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    print(f"{PROP}: {variant}: materials {', '.join(n.replace(PROP + '_', '') for n in used)}")
    prefix = "" if variant == "photo" else f"{variant}_"
    r = round_radius(SPEC[variant])
    print(f"{PROP}: {variant}: round window {2 * r:.2f} m glass, {2 * (r + ROUND_FRAME):.2f} m over its frame, "
          f"centred on the front face {ROUND_Z:.2f} m up")
    print(f"{PROP}: {variant}: hooded side windows {WIN_W:.2f} x {SIDE_GLASS:.2f} m glass, sills {SIDE_LOWER[0]:.2f} and "
          f"{SIDE_UPPER[0]:.2f} m, heads {SIDE_LOWER[1]:.2f} and {SIDE_UPPER[1]:.2f} m")
    faults = []
    for name, share, rest in glass_seen(objs):
        line = f"{name.replace(prefix, '', 1)} {share:.0%}" + "".join(
            f", {x:.0%} {k.replace(prefix, '', 1)}" for k, x in sorted(rest.items()))
        if any(k != "mullions" for k in rest) or share < 0.75:
            faults.append(line)
        print(f"{PROP}: {variant}: glass seen square-on: {line}")
    for name, up, over, near, nearest, touch in hood_clearance(objs, prefix):
        line = (f"hood {name.replace(prefix, '', 1)}: {up:.3f} m clear straight up to {over.replace(prefix, '', 1)}, "
                f"nearest part {nearest.replace(prefix, '', 1)} {near:.3f} m, touching {', '.join(touch) or 'nothing'}")
        if up < 0.05 or near < 0.03 or touch:
            faults.append(line)
        print(f"{PROP}: {variant}: {line}")
    if faults:
        print(f"{PROP}: {variant}: WINDOW FAULTS: " + "; ".join(faults))
    return tris, pairs


# --- renders --------------------------------------------------------------------------------

def show_variant(variant):
    for v in VARIANTS:
        for o in variant_objects(v):
            o.hide_render = v != variant


def render(folder):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    ground = mat("_ground", (0.40, 0.32, 0.22))
    walk = mat("_walk", (0.64, 0.61, 0.58))
    box("_ground", stage, ground, -80, 80, -80, 80, -0.30, -0.01, collide=False)
    box("_walk", stage, walk, -30, 30, -7.5, -5.0, -0.30, -0.005, collide=False)
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    # the figure stands by the wing's door for its one frame and is hidden
    # for the rest, where it got between the camera and the corner
    figures = [figure("_figure_0", stage, -2.4, -3.6, mat=fig)]
    for o in figures:
        o.hide_render = True
    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((0.45, -0.70, 0.60)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 48
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False

    def shoot(name, eye, target, lens=32, size=(1600, 1100), ortho=None):
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 500
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{PROP}: rendered {scene.render.filepath}")

    # the big photograph's view: close, from the front-right, looking up;
    # the small one's: from the front-left across the yard, level
    show_variant("photo")
    shoot("photo_front_three_quarter", (6.2, -7.8, 1.6), (0.3, -0.6, 3.2), lens=24, size=(1400, 1400))
    shoot("photo_side", (-8.0, -11.0, 1.5), (-1.0, -0.8, 2.6), lens=30, size=(1600, 1060))
    shoot("photo_front_elevation", (0.0, -40.0, 3.3), (0.0, 0.0, 3.3), ortho=9.5)
    shoot("photo_back_three_quarter", (6.5, 8.5, 2.2), (0.3, 0.8, 3.0), lens=30)
    # the other variants from their hooded side, the wing showing past the tower
    for v in VARIANTS[1:]:
        show_variant(v)
        sx = -SPEC[v]["wing_side"]
        shoot(f"{v}_three_quarter", (sx * 6.0, -7.8, 1.7), (-sx * 0.3, -0.6, 3.2), lens=26, size=(1400, 1400))
    # every variant side by side, from the front and as elevations
    shifts = {v: dx for v, dx in zip(VARIANTS, (-8.5, 0.0, 8.5))}
    for v, dx in shifts.items():
        for o in variant_objects(v):
            o.location.x += dx
            o.hide_render = False
    shoot("all_variants", (6.0, -24.0, 5.0), (0.0, 0.0, 3.0), lens=30, size=(2200, 1000))
    shoot("all_front_elevations", (0.0, -60.0, 3.3), (0.0, 0.0, 3.3), ortho=27.0, size=(2400, 900))
    for v, dx in shifts.items():
        for o in variant_objects(v):
            o.location.x -= dx
    # the photo house beside the figure at the gate
    show_variant("photo")
    for o in figures:
        o.hide_render = False
    shoot("photo_with_figure", (-5.5, -10.0, 1.6), (-1.4, -2.2, 2.4), lens=35)


# --- main -------------------------------------------------------------------------------------

def layer_collection(name, root=None):
    root = root or bpy.context.view_layer.layer_collection
    if root.name == name:
        return root
    for child in root.children:
        found = layer_collection(name, child)
        if found is not None:
            return found
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != PROP:
        raise SystemExit(f"{PROP}: open {PROP}.blend, not {name}")
    export, authored, reference = (bpy.data.collections[n] for n in ("export", "authored", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"{PROP}: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    for v in VARIANTS:
        if v == "photo":
            coll, prefix = export, ""
        else:
            coll = bpy.data.collections.new(f"variant_{v}")
            export.children.link(coll)
            prefix = f"{v}_"
        m = mats(v)
        build_tower(coll, m, v, prefix, SPEC[v])
        build_wing(coll, m, v, prefix, SPEC[v])
    build_reference(reference)
    bpy.context.view_layer.update()
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    for v in VARIANTS:
        s = SPEC[v]
        k = math.tan(math.radians(s["lean"]))
        print(f"{PROP}: {v}: base {s['base'][0]:.2f} x {s['base'][1]:.2f} m, lean {s['lean']:.0f} deg inward, "
              f"eave {s['base'][0] - 2 * k * EAVE:.2f} x {s['base'][1] - 2 * k * EAVE:.2f} m at {EAVE:.2f}, "
              f"cornice {BED_Z0:.2f}..{CFASCIA_Z1:.2f}, wing {WING_W:.1f} m wide on {'-x' if s['wing_side'] < 0 else '+x'} "
              f"to eave {s['wing_eave']:.2f}, cap {s['cap']}")
    total = 0
    for v in VARIANTS:
        tris, pairs = report(v)
        total += tris
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1])


main()
