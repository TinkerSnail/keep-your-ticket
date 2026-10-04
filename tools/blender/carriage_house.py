"""The beach town's carriage house, blocked out (2026-10-03): two storeys, a
carriage house with rooms over it, gable to the street on a 9 m lot, from
Christina's photograph `documentation/reference/houses/carriage_house_cottage.png`.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/carriage_house.blend --python tools/blender/carriage_house.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, one shell in four `kyt_variant`s that stand
at the origin together, as the Victorian cottage's do: `photo` in `export`
itself and `plain`, `hillside` and `stilts` each in `export/variant_<name>`
with its eye shut (Send writes one prop per variant; Check and the handback
render show the first). `plain` and `hillside` are Christina's "this AND that" (3 Oct 2026):
alternatives built as variants rather than asked as questions, each on its
own materials in colours its siblings do not use. `plain` is the photo's
house with a sectional garage door in place of the carriage doors, a short
balcony over it instead of the full-width one, no cross-gable (a knee-wall
window and a second skylight instead) and round vents in the peaks in place
of the stick-work. `hillside` is the photo's house set into a 35 % slope
rising behind it: the garage storey at the street, the entry door beside
the carriage doors on the street face under the balcony, the ground
reaching the upstairs floor at the back wall, where a back door opens onto
a deck on a flat pad cut into the hill, one step down. It is the reference
the hillside cottages lacked, a garage under and living above. `stilts`
(her "a good base for creating an elevated beach house on stilts", 3 Oct
2026) is the upper body alone, lifted on eight-sided timber piles so the
floor stands 2.9 m up and the ground under it is open for a car, the
outer pile rows X-braced; the storey is built full height (2.45 m walls),
because the carriage house's 1.35 m knee wall over a 2.6 m void read as a
hat on legs and the side door needs a full wall; the stick-work peak and
the balcony idea stay, the balcony grown into a deck 2.4 m deep across the
gable end (the sea side) and 1.5 m along the east side, railed in white,
reached by an outside stair of two flights with a middle landing by the
park's stair rule, open underneath (Christina, 3 Oct 2026: "that staircase
doesnt need that grey mass under it"): tread boards on two cut stringers,
the walking ramp a thin board hidden between them, air down to the ground;
French doors open onto the front deck and the entry door onto the side
deck by the stair's top, both at flush thresholds.

Into the locked `reference` go the lot, footprint and driveway outlines, a
1.7 m figure, the hillside's ground profile and the `ground_line` marker
Check reads (the walls reach below z = 0 on purpose). Everything the tool
makes carries `kyt_carriage_house`, so a rerun removes and rebuilds its own
work and keeps anything of hers; `export` holding anything untagged refuses
without `--replace`.

**Frame.** Real metres, Z up, the street-side ground at z = 0, the origin at
the body's footprint centre. The front (the gable, carriage doors and
balcony) faces -Y here, which the glTF export (`send.py`, `export_yup=True`)
turns into Godot's +Z. +X is the viewer's right from the street: the
driveway side, where the photo's front door is.

**Contract** (enclosing, as the cottages): public faces, doors, windows and
the balcony, no interior. Every opening is a real hole through a wall of
real thickness; the doors and the panes are solid slabs set in the holes.
Every door's sill stands THRESHOLD over the ground or deck it opens onto,
flush for the player. The hillside's step follows the park's stair rule: a
narrow ramp is the floor, the tread is scenery showing past it and does not
collide (`kyt_collision = none`); the stilts' flights follow it open
(`Kit.open_stair`), the same ramp as a board, the treads and the stringers
scenery. No two shapes share a plane: a part that meets another laps into
it or stands proud of it, and the tool's own scan (`coplanar_pairs`)
reports any pair that does.

**What the photograph says** (measured on a gridded enlargement, the
front door as scale, the vanishing points for the depths). A narrow gable
to the street on a long body, dark shingles. The lower storey in pale blue
lap siding, the upper in grey-blue board-and-batten, a white belt course
between at the balcony's floor. Double carriage doors centred in the gable
end between two pilasters that carry the balcony's diagonal struts; the
balcony nearly the gable's full width and a metre deep, solid pierced
panels and ball-capped newels, a turned pendant under each strut's arm;
over it a glazed door with a little pointed cap; in the peak a collar tie,
a king post and a V of braces between the bargeboards. On the driveway
side the glazed front door about two metres back from the corner under a
shed hood on two braces; a skylight on the slope beyond it; then, about six
metres back, a cross-gable nearly the body's width rising flush from the
wall with a tall sash window and the same stick-work in its peak, its apex
a little under the main ridge, the eave fascia stopping at its rakes and
running on behind it to the back corner; a round metal flue by the ridge
and a weathervane over the cross-gable. White corner boards and casings.
It reads in silhouette and chunky trim, so that is what is built; lap
siding, battens, divided lights and the panels' cut-outs are left to
painting.

**Choices to state.** The front door at 2.1 m gives the lower storey 3.25 m
to the belt and 1.35 m of knee wall to the eave; the carriage doors come
out 2.4 by 2.5 m and the gable about 5.2 m wide; the pitch 45 degrees (the
rise reads 2.2 to 2.6 m, the "steep" look is the gable's narrowness); the
body W = 5.2 m across by D = 10.0 m deep, the cross-gable 4.6 m wide
centred 6 m back. The photo does not show the back or the west: the main
ridge is run through to a back gable and the west gets windows. On the
9 m lot that leaves a 2.4 m driveway beside the east wall for the front
door, with the carriage doors served straight off the street. Colours are
flat stand-ins named `carriage_house_<variant>_<surface>` for the painting
to replace.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_carriage_house"
NAME = "carriage_house"

# --- the shell, every variant ----------------------------------------------
W, D = 5.2, 10.0           # the body: across the front, and deep
T = 0.20                   # wall thickness
LOWER = 3.25               # the ground to the belt course: the upstairs floor
KNEE = 1.35                # the upper wall over the belt, to the eave
EAVE = LOWER + KNEE        # the roof's underside at the side walls' outer face
PITCH_DEG = 45.0
PITCH = math.radians(PITCH_DEG)
TAN = math.tan(PITCH)
RISE = (W / 2) * TAN       # the ridge over the eave
ROOF_T = 0.20              # the roof slab, perpendicular to its slope
ROOF_VT = ROOF_T / math.cos(PITCH)
RIDGE_TOP = EAVE + RISE + ROOF_VT
EAVE_OVER, RAKE_OVER = 0.40, 0.50
# the side walls end this far over the eave: inside the slab at both skins
# (over T * TAN = 0.20 at the inner skin, under ROOF_VT = 0.28 at the outer)
WALL_TOP_IN = 0.24
LIFT = 0.03                # a gable wall's top, this far inside the slab
CORNER, PROUD = 0.26, 0.04  # the corner boards, 4 cm proud of the walls
E_IN = CORNER / 2 - PROUD  # the walls stop this short of the corners, under the boards
BELOW = 0.05               # the end walls' feet under the ground (sides 1 cm lower, boards 3)
THRESHOLD = 0.01           # a door's sill over the ground or deck outside it (the door is shut)
DOOR_H = 2.10
CARRIAGE_H = 2.50          # the carriage doors' opening
BELT_H = 0.22              # the belt course, centred on LOWER
SILL, HEAD = 0.90, 2.10    # the lower storey's windows
KNEE_WIN = (3.55, 4.35)    # a knee-wall window upstairs
UP_WIN = (3.75, 5.00)      # a gable window upstairs
BARGE_H = 0.26
FASCIA_H = 0.30
PIL_W, PIL_PROUD, PIL_GAP = 0.16, 0.14, 0.17   # the pilasters flanking the carriage doors
BEAM_Z = (2.66, 2.94)      # the header between them, under the balcony
BAL_D = 1.00               # the photo's balcony, out from the wall
BAL_HALF = W / 2 - 0.17    # and half its width: nearly the gable's (its side rails 2 cm clear of the corner boards)
STRUT_FOOT_Z = 2.15        # where a strut lands on its pilaster
PLATE_T = 0.15             # the balcony's floor plate
RAIL_H = 0.90
POST = 0.14                # newels
RISER_ABOUT, GOING = 0.155, 0.28
STAIR_W = 1.10
HOOD = dict(out=0.90, rise=2.80, drop=0.52, thick=0.12, half=1.00, brace=0.76)   # the shed hood over the front door
DORMER_YC, DORMER_HALF = 1.00, 2.30    # the cross-gable on the east wall: centre and half span
DORMER_WIN = (0.45, 3.60, 5.40)        # half width, sill, head
COLLAR_Z = 6.30            # the main gable's collar tie
DORMER_COLLAR_Z = 6.00
SKYLIGHT = (-2.20, -1.30, W / 2 - 2.30, W / 2 - 1.50)   # y0, y1, x0, x1 on the east slope
FLUE = (0.45, -2.60, 0.11, 8.20)       # x, y, radius, top
VANE_Y = 0.80              # the weathervane on the ridge, over the cross-gable
CARRIAGE_X = (-1.20, 1.20)
BAL_DOOR_X = (-0.45, 0.45)
FRONT_DOOR_Y = (-D / 2 + 1.85, -D / 2 + 2.75)   # the photo's door, on the east wall
BACK_WIN_X = (-1.90, -0.80)
BACK_UP_WIN_X = (-0.50, 0.50)
WEST_WINS_Y = ((-3.20, -2.20), (1.00, 2.00))
WEST_KNEE_Y = (-0.50, 0.50)
EAST_KNEE_Y = (0.80, 1.80)

# --- plain: a sectional garage door, a short balcony, no cross-gable ----------
PLAIN_BAL_HALF, PLAIN_BAL_D = 1.50, 1.00
PLAIN_DOORS_X = (-0.65, 0.65)          # French doors onto the balcony
PLAIN_SKYLIGHT_2 = (1.30, 2.20, W / 2 - 2.30, W / 2 - 1.50)
PLAIN_VENT_R = 0.40        # the round vent in each peak
PLAIN_VENT_Z = 6.35        # its centre
PLAIN_GARAGE_RAILS = (0.85, 1.70)      # the sectional door's panel lines

# --- hillside: the photo's house into a 35 % slope rising behind it -----------
HILL_CARRIAGE_X = (-0.55, 1.85)        # the carriage doors, shifted for the entry beside them
HILL_DOOR_X = (-2.15, -1.35)           # the entry door on the street face, under the balcony
HILL_BAL_DOOR_X = (0.20, 1.10)         # over the carriage doors
HILL_STRUT_W_X = -2.28                 # the third strut, on the wall beside the west corner board
HILL_BACK_DOOR_X = (0.60, 1.50)        # the back door, upstairs, onto the deck
HILL_BACK_UP_WIN_X = (-1.80, -0.80)
PAD_Z = LOWER - 0.15       # the flat pad behind the house, a step under the deck
HILL_SLOPE = 0.35          # the ground reaches the pad 1.1 m before the back wall
PAD_END = D / 2 + 2.60     # where the ground rises again
DECK_X, DECK_D = (-0.20, 2.30), 2.00   # the deck off the back door

# --- stilts: the upper body lifted on timber piles, a beach house ------------
ST_FLOOR = 2.90            # the floor and decks over the ground
ST_PLATE_T = 0.30          # the floor platform, its rim the deck's edge
ST_STOREY = 2.45           # a full-height storey (the knee wall read as a hat on legs)
ST_EAVE = ST_FLOOR + ST_STOREY
ST_RIDGE_TOP = ST_EAVE + RISE + ROOF_VT
ST_FRONT_DECK = 2.40       # the deck past the gable end, toward the sea
ST_SIDE_DECK = 1.50        # and along the east side
ST_LIP = 0.10              # the platform past the west and back walls
ST_STAIR_X = (W / 2 + ST_SIDE_DECK + 0.13, W / 2 + ST_SIDE_DECK + 1.08)   # the flights, beside the side deck
ST_LANDING_D = 1.20        # the top landing (part of the platform) and the middle one
ST_MID_Z = 1.45            # the middle landing's floor: nine risers up, nine more to the deck
OPEN_TREAD_T = 0.06        # an open flight's tread boards
OPEN_RAMP_T = 0.10         # its ramp board, square to its slope
STRINGER_W, STRINGER_OUT = 0.06, 0.0125   # its stringers: thick, and out past the tread ends
ST_PILE_R = 0.17           # the piles, eight-sided
ST_PILE_X = (-2.30, 0.00, 2.30, 3.80)    # the columns: under the body and the side deck's edge
ST_PILE_Y = (-7.15, -4.70, -2.30, 0.10, 2.50, 4.70)   # the rows: the front deck's edge to the back
ST_PILES_EXTRA = ((4.95, -7.15), (4.95, -6.45))      # under the top landing
ST_PILE_FOOT, ST_PILE_TOP = -0.30, ST_FLOOR - ST_PLATE_T + 0.02
ST_BRACE_Z = (0.40, 2.20)  # where a brace leaves one pile and enters the next
ST_DOORS_X = (-0.70, 0.70)             # French doors onto the front deck
ST_DOOR_Y = (-D / 2 + 0.40, -D / 2 + 1.30)   # the entry door onto the side deck, by the stair's top
ST_GABLE_WIN_X = (-0.45, 0.45)
ST_WIN = (0.90, 2.10)                  # sill and head over the floor
ST_GABLE_WIN = (2.85, 3.85)            # the gable windows over the floor
ST_EAST_WINS_Y = ((0.30, 1.30), (2.70, 3.70))
ST_WEST_WINS_Y = ((-3.20, -2.20), (1.00, 2.00))
ST_BACK_WIN_X = (-1.90, -0.80)
ST_COLLAR_Z = ST_EAVE + 1.75           # the collar tie
ST_VANE_Y = D / 2 - 1.00

LOT_W, LOT_X0, LOT_Y = 9.0, -3.6, (-16.0, 14.0)   # the lot: 9 m wide, the kerb to the back fence

PALETTES = {
    # the photo: pale blue lap siding, grey-blue board-and-batten, white
    "photo": dict(walls_lower="b9d0dd", walls_upper="8f9ca5", trim="f6f3ec", door="f1efe8",
                  deck="8a8f93", roof="4a4c4a", glass="3e5566", metal="9a9d9f"),
    # plain: butter yellow under sage, slate trim, teal doors
    "plain": dict(walls_lower="f0d27a", walls_upper="9db08c", trim="3d4a5c", door="2d7e86",
                 deck="7d8a94", roof="4b4845", glass="3e5566", metal="9a9d9f"),
    # hillside: sand under olive, parchment trim, barn-red doors
    "hillside": dict(walls_lower="e9c6a3", walls_upper="7d8b5c", trim="f1e6c8", door="9b2d2a",
                     deck="8a7a6a", roof="5e5a55", glass="3e5566", metal="9a9d9f"),
    # stilts, sea-washed: weathered grey shingle, cool white trim, a sky-blue
    # door, driftwood decks, sun-bleached roof, dark timber piles
    "stilts": dict(walls="9a9a92", trim="e9eef0", door="6fb3e0", deck="a39a8a", roof="6e6a63",
                   glass="46606f", metal="9a9d9f", pile="6b5a48"),
}
VARIANTS = ("photo", "plain", "hillside", "stilts")


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def material(name, colour):
    """A flat stand-in by name; its colour is set every run, so a palette
    change reaches a material the file already holds."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = colour
    mat.diffuse_color = colour
    return mat


# --- building blocks ---------------------------------------------------------

def prism_bm(poly, axis, lo, hi, bm=None):
    """A 2D polygon extruded along `axis` ('x' gives (y, z) pairs, 'y' gives
    (x, z), 'z' gives (x, y)), into `bm` when given (several pieces, one part)."""
    bm = bm or bmesh.new()

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


def octagon(cx, cy, r):
    return [(cx + r * math.cos(math.tau * (k + 0.5) / 8), cy + r * math.sin(math.tau * (k + 0.5) / 8)) for k in range(8)]


def member(a, b, width):
    """A straight member of `width` from point a to point b, in a plane, as
    a four-point polygon (its ends square to its run)."""
    (ax, az), (bx, bz) = a, b
    dx, dz = bx - ax, bz - az
    length = math.hypot(dx, dz)
    px, pz = -dz / length * width / 2, dx / length * width / 2
    return [(ax + px, az + pz), (ax - px, az - pz), (bx - px, bz - pz), (bx + px, bz + pz)]


class Top:
    """A wall's top edge: flat, a gable following a roof's underside LIFT
    higher (inside the slab, so the two never share a plane), or both: flat
    where the gable line is lower, the gable where it rises above (the east
    wall under the cross-gable)."""

    def __init__(self, flat=None, gable=None):
        self.flat = flat
        self.gable = gable      # (u of the ridge, half span, eave z, tan of the pitch)

    def gable_z(self, u):
        ridge_u, half, eave, tan = self.gable
        return eave + (half - abs(u - ridge_u)) * tan + LIFT

    def z(self, u):
        if self.gable is None:
            return self.flat
        if self.flat is None:
            return self.gable_z(u)
        return max(self.flat, self.gable_z(u))

    def apex(self):
        ridge_u, half, eave, tan = self.gable
        return eave + half * tan + LIFT

    def breaks(self):
        """Where the top's slope changes: the ridge, and the flat's crossings."""
        if self.gable is None:
            return []
        ridge_u, half, eave, tan = self.gable
        out = [ridge_u]
        if self.flat is not None:
            du = half - (self.flat - eave - LIFT) / tan
            if du > 0:
                out += [ridge_u - du, ridge_u + du]
        return out


class Kit:
    """One variant's parts: every maker here names, tags and colours for it."""

    def __init__(self, variant, coll):
        self.v = variant
        self.coll = coll
        self.m = {k: material(f"{NAME}_{variant}_{k}", srgb(hex6)) for k, hex6 in PALETTES[variant].items()}

    def finish(self, part, bm, mats, collide=True):
        name = f"{self.v}_{part}"
        mesh = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            f.smooth = False
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        for m in mats:
            mesh.materials.append(m)
        obj[TAG] = True
        obj["kyt_unwrap"] = "facets"
        obj["kyt_variant"] = self.v
        if not collide:
            obj["kyt_collision"] = "none"
        self.coll.objects.link(obj)
        return obj

    def box(self, part, mat, x0, x1, y0, y1, z0, z1, collide=True):
        """An axis-aligned box, 12 triangles."""
        assert x1 > x0 and y1 > y0 and z1 > z0, (part, x0, x1, y0, y1, z0, z1)
        bm = prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)
        return self.finish(part, bm, [mat], collide=collide)

    def prism(self, part, mat, poly, axis, lo, hi, collide=True):
        return self.finish(part, prism_bm(poly, axis, lo, hi), [mat], collide=collide)

    def slab(self, part, mat, axis, poly, face_at, outward, proud, lap, collide=False):
        """A polygon in a wall's plane, `proud` of the wall's face and
        `lap` into it (every slab on one face gets its own proud and lap, so
        no two share a plane)."""
        lo, hi = sorted((face_at - lap * outward, face_at + proud * outward))
        return self.prism(part, mat, poly, axis, lo, hi, collide=collide)

    def octo(self, part, mat, cx, cy, r, z0, z1, collide=False):
        return self.prism(part, mat, octagon(cx, cy, r), "z", z0, z1, collide=collide)

    # -- walls --

    def wall(self, part, origin, u_dir, v_dir, length, thick, z0, top, openings, split_z, mats):
        """One wall as a closed shell: two skins, ends, bottom, top, and a real
        reveal round every opening. `origin` is the outer face's start,
        `u_dir` runs along it, `v_dir` into the wall. An opening is
        (u0, u1, z0, z1), anywhere under the top, the gable included: the
        wall is a grid of cells between the opening lines, each cell clipped
        by the roof line, and a cell's edge gets a side face wherever its
        neighbour is an opening, the outside or the sky. Faces below
        `split_z` take the first material (the lower storey's siding), the
        rest the second (the upper's)."""
        O, U, V = Vector(origin), Vector(u_dir), Vector(v_dir)
        us, zs = {0.0, length}, {z0}
        if split_z > z0:
            zs.add(split_z)
        for u0, u1, oz0, oz1 in openings:
            assert 0.0 < u0 < u1 < length and z0 < oz0 < oz1, (part, u0, u1, oz0, oz1)
            assert oz1 + 0.03 <= min(top.z(u0), top.z(u1)), (part, "an opening through the top", u0, u1, oz1)
            us.update((u0, u1))
            zs.update((oz0, oz1))
        for u in top.breaks():
            if 0.0 < u < length:
                us.add(u)
        if top.gable is None:
            zs.add(top.flat)
        else:
            zs.add(top.apex() + 1.0)       # a nominal top, clipped away
        us, zs = sorted(us), sorted(zs)
        nu, nz = len(us) - 1, len(zs) - 1
        bm = bmesh.new()
        verts = {}

        def vert(u, z, side):
            key = (round(u, 5), round(z, 5), side)
            if key not in verts:
                verts[key] = bm.verts.new(O + U * u + V * (thick if side else 0.0) + Vector((0.0, 0.0, z)))
            return verts[key]

        def is_open(i, j):
            um, zm = (us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            return any(u0 < um < u1 and oz0 < zm < oz1 for u0, u1, oz0, oz1 in openings)

        def clip(i, j):
            ua, ub, za, zb = us[i], us[i + 1], zs[j], zs[j + 1]
            poly = [(ua, za), (ub, za), (ub, zb), (ua, zb)]
            if top.gable is None:
                return poly
            out = []
            for k in range(4):
                p, q = poly[k], poly[(k + 1) % 4]
                fp, fq = top.z(p[0]) - p[1], top.z(q[0]) - q[1]
                if fp >= 0:
                    out.append(p)
                if (fp >= 0) != (fq >= 0):
                    t = fp / (fp - fq)
                    out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
            clean = []
            for p in out:
                if not clean or (abs(p[0] - clean[-1][0]) > 1e-6 or abs(p[1] - clean[-1][1]) > 1e-6):
                    clean.append(p)
            if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-6 and abs(clean[0][1] - clean[-1][1]) < 1e-6:
                clean.pop()
            return clean if len(clean) >= 3 else None

        solid = {(i, j): (None if is_open(i, j) else clip(i, j)) for i in range(nu) for j in range(nz)}

        def index(zm):
            return 0 if zm < split_z else 1

        for (i, j), poly in solid.items():
            if poly is None:
                continue
            zm = sum(p[1] for p in poly) / len(poly)
            f = bm.faces.new([vert(u, z, 0) for u, z in poly])
            f.material_index = index(zm)
            f = bm.faces.new([vert(u, z, 1) for u, z in reversed(poly)])
            f.material_index = index(zm)
            n = len(poly)
            for k in range(n):
                p, q = poly[k], poly[(k + 1) % n]
                eps = 1e-6
                if abs(p[0] - q[0]) < eps and abs(p[0] - us[i]) < eps:
                    nb = (i - 1, j)
                elif abs(p[0] - q[0]) < eps and abs(p[0] - us[i + 1]) < eps:
                    nb = (i + 1, j)
                elif abs(p[1] - q[1]) < eps and abs(p[1] - zs[j]) < eps:
                    nb = (i, j - 1)
                elif abs(p[1] - q[1]) < eps and abs(p[1] - zs[j + 1]) < eps:
                    nb = (i, j + 1)
                else:
                    nb = None
                if nb is not None and solid.get(nb) is not None:
                    continue        # shared with a solid neighbour
                f = bm.faces.new((vert(*p, 0), vert(*q, 0), vert(*q, 1), vert(*p, 1)))
                f.material_index = index((p[1] + q[1]) / 2)
        return self.finish(part, bm, mats)

    def shell(self, prefix, x0, x1, y0, y1, thick, e, feet, tops, openings, mats, split_z):
        """Walls as closed shells round the rectangle (x0..x1, y0..y1), their
        ends lost inside the corner boards (`e` short of each corner). `feet`
        gives each wall's foot z; `tops` a Top per wall; `openings` per wall a
        list of (a0, a1, z0, z1) in world x (front, back) or world y (west,
        east) and absolute z."""
        spec = {
            "front": ((x0 + e, y0, 0.0), (1, 0, 0), (0, 1, 0), x1 - x0 - 2 * e, lambda a: a - x0 - e),
            "back": ((x1 - e, y1, 0.0), (-1, 0, 0), (0, -1, 0), x1 - x0 - 2 * e, lambda a: x1 - e - a),
            "west": ((x0, y1 - e, 0.0), (0, -1, 0), (1, 0, 0), y1 - y0 - 2 * e, lambda a: y1 - e - a),
            "east": ((x1, y0 + e, 0.0), (0, 1, 0), (-1, 0, 0), y1 - y0 - 2 * e, lambda a: a - y0 - e),
        }
        for key in ("front", "back", "west", "east"):
            origin, u_dir, v_dir, length, to_u = spec[key]
            ops = []
            for a0, a1, z0, z1 in openings.get(key, ()):
                ua, ub = sorted((to_u(a0), to_u(a1)))
                ops.append((ua, ub, z0, z1))
            self.wall(f"{prefix}wall_{key}", origin, u_dir, v_dir, length, thick, feet[key], tops[key], ops,
                      split_z, mats)

    def corner_boards(self, prefix, mat, x0, x1, y0, y1, size, proud, z0, eave=None):
        """Corner boards `proud` of both faces, their feet below the walls',
        their tops cut to the roof's slope inside the slab (a flat top
        under a 50-degree roof cannot be hidden)."""
        for sx, sy, tag in ((-1, -1, "sw"), (1, -1, "se"), (-1, 1, "nw"), (1, 1, "ne")):
            cx = (x0 - proud + size / 2) if sx < 0 else (x1 + proud - size / 2)
            cy = (y0 - proud + size / 2) if sy < 0 else (y1 + proud - size / 2)
            xa, xb = cx - size / 2, cx + size / 2
            # 2 cm over the gable walls' tops, which follow the same slope
            if eave is None:
                poly = [(xa, z0), (xb, z0), (xb, roof_under(xb) + LIFT + 0.02), (xa, roof_under(xa) + LIFT + 0.02)]
            else:
                def under(x):
                    return eave + (W / 2 - abs(x)) * TAN + LIFT + 0.02
                poly = [(xa, z0), (xb, z0), (xb, under(xb)), (xa, under(xa))]
            self.prism(f"{prefix}corner_{tag}", mat, poly, "y", cy - size / 2, cy + size / 2)

    def gable_roof(self, part, mat, axis, c, half, eave, tan, over, thick, lo, hi):
        """A gable roof as one piece: an inverted V of `thick` perpendicular
        thickness whose underside passes through z = eave at c +- half and
        peaks over c, extruded from `lo` to `hi` along `axis` (the ridge
        runs along it; 'y' for the main roof, 'x' for the cross-gable)."""
        vt = thick / math.cos(math.atan(tan))

        def under(a):
            return eave + (half - abs(a - c)) * tan
        ae = half + over
        section = [(c - ae, under(c - ae)), (c, under(c)), (c + ae, under(c + ae)),
                   (c + ae, under(c + ae) + vt), (c, under(c) + vt), (c - ae, under(c - ae) + vt)]
        return self.prism(part, mat, section, axis, lo, hi)

    def bargeboard(self, part, mat, axis, c, half, eave, tan, over, thick_vt, face_at, out, height, proud, lap):
        """A chevron board on a gable's rake face: its back `lap` inside the
        roof slab's end, its top 2 cm under the slab's top, `height` tall
        under that. `out` is the rake face's outward sign along `axis`."""
        def under(a):
            return eave + (half - abs(a - c)) * tan
        ae = half + over + 0.05
        zt = thick_vt - 0.02
        section = [(c - ae, under(c - ae) + zt - height), (c, under(c) + zt - height), (c + ae, under(c + ae) + zt - height),
                   (c + ae, under(c + ae) + zt), (c, under(c) + zt), (c - ae, under(c - ae) + zt)]
        lo, hi = sorted((face_at - out * lap, face_at + out * proud))
        return self.prism(part, mat, section, axis, lo, hi, collide=False)

    # -- openings --

    def opening_trim(self, prefix, mat, axis, face_at, outward, a0, a1, z0, z1, sill=True):
        """Chunky casing round an opening: a head board over two jambs (and a
        sill board), 3.5 cm proud, the back sunk 1 cm into the wall, the
        jambs lapping 2 cm over the opening's edge and 2 cm into the head and
        sill. `axis` is 'x' when the opening's width runs along X."""
        w = 0.12

        def part(name, a_lo, a_hi, b_lo, b_hi, sunk, proud):
            lo, hi = sorted((face_at - sunk * outward, face_at + proud * outward))
            if axis == "x":
                return self.box(name, mat, a_lo, a_hi, lo, hi, b_lo, b_hi, collide=False)
            return self.box(name, mat, lo, hi, a_lo, a_hi, b_lo, b_hi, collide=False)

        part(f"{prefix}_head", a0 - w - 0.04, a1 + w + 0.04, z1 - 0.02, z1 + w, 0.010, 0.045)
        part(f"{prefix}_jamb_a", a0 - w, a0 + 0.02, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
        part(f"{prefix}_jamb_b", a1 - 0.02, a1 + w, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
        if sill:
            part(f"{prefix}_sill", a0 - w - 0.04, a1 + w + 0.04, z0 - w, z0 + 0.02, 0.010, 0.045)

    def pane(self, part, mat, axis, face_at, outward, a0, a1, z0, z1, recess=0.08, thick=0.05, collide=True):
        """A slab set in an opening, recessed into the wall, 2 cm into the reveals all round."""
        lo, hi = sorted((face_at - recess * outward, face_at - (recess + thick) * outward))
        if axis == "x":
            return self.box(part, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, collide=collide)
        return self.box(part, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, collide=collide)

    def bar(self, part, mat, axis, face_at, outward, a0, a1, z0, z1, sunk, proud, collide=False):
        """A bar on a face: a box over (a0..a1, z0..z1), `proud` of the face
        and `sunk` into it."""
        lo, hi = sorted((face_at - sunk * outward, face_at + proud * outward))
        if axis == "x":
            return self.box(part, mat, a0, a1, lo, hi, z0, z1, collide=collide)
        return self.box(part, mat, lo, hi, a0, a1, z0, z1, collide=collide)

    def mullions(self, prefix, mat, axis, face_at, outward, a0, a1, z0, z1, lights):
        """Chunky mullions dividing an opening into `lights`, 3.5 cm proud
        and lapped 2 cm into the pane behind, their ends a centimetre inside
        the head and sill casings (so a door's never meets the deck)."""
        for m in range(1, lights):
            a = a0 + (a1 - a0) * m / lights
            self.bar(f"{prefix}_mullion{m}", mat, axis, face_at, outward, a - 0.05, a + 0.05, z0 + 0.01, z1 - 0.01, 0.10, 0.035)

    def window(self, prefix, kit_mat, axis, face_at, outward, a0, a1, z0, z1, rail=False):
        """A window: casing with a sill, a glass pane, and a meeting rail
        across the middle for a sash."""
        self.opening_trim(f"{prefix}_trim", kit_mat["trim"], axis, face_at, outward, a0, a1, z0, z1)
        self.pane(f"{prefix}_pane", kit_mat["glass"], axis, face_at, outward, a0, a1, z0, z1)
        if rail:
            zm = (z0 + z1) / 2
            self.bar(f"{prefix}_rail", kit_mat["trim"], axis, face_at, outward, a0 - 0.01, a1 + 0.01, zm - 0.03, zm + 0.03, 0.10, 0.03)

    def glazed_door(self, prefix, kit_mat, axis, face_at, outward, a0, a1, z0, z1, light=(0.25, 0.95, 1.95)):
        """A door with a big light: casing without a sill, the leaf, and a
        glass slab on the leaf 1 cm proud of it. `light` is the glass's
        half width and its z range."""
        self.opening_trim(f"{prefix}_trim", kit_mat["trim"], axis, face_at, outward, a0, a1, z0, z1, sill=False)
        self.pane(f"{prefix}_leaf", kit_mat["door"], axis, face_at, outward, a0, a1, z0, z1)
        hw, g0, g1 = light
        c = (a0 + a1) / 2
        self.bar(f"{prefix}_light", kit_mat["glass"], axis, face_at, outward, c - hw, c + hw, g0, g1, 0.095, -0.070)

    # -- decks, rails, stairs --

    def newel(self, part, mat, x0, y0, z_floor):
        """A newel: the post 2 cm into the deck, a square cap and a turned ball."""
        z1 = z_floor + RAIL_H + 0.12
        self.box(f"{part}_post", mat, x0, x0 + POST, y0, y0 + POST, z_floor - 0.02, z1)
        self.box(f"{part}_cap", mat, x0 - 0.02, x0 + POST + 0.02, y0 - 0.02, y0 + POST + 0.02, z1 - 0.02, z1 + 0.04, collide=False)
        self.octo(f"{part}_ball", mat, x0 + POST / 2, y0 + POST / 2, 0.065, z1 + 0.03, z1 + 0.16)

    def panel_rail(self, prefix, mat, axis, at, a0, a1, z_floor, panel=0.06, cap=0.12):
        """A deck rail as a solid panel with a cap (the photo's pierced
        panels: the painting cuts the slots): the panel's foot 1.5 cm into
        the deck, its ends lapping the posts."""
        z0, z1 = z_floor - 0.015, z_floor + RAIL_H
        if axis == "x":
            self.box(f"{prefix}_panel", mat, a0, a1, at - panel / 2, at + panel / 2, z0, z1)
            self.box(f"{prefix}_cap", mat, a0 + 0.015, a1 - 0.015, at - cap / 2, at + cap / 2, z1 - 0.03, z1 + 0.05, collide=False)
        else:
            self.box(f"{prefix}_panel", mat, at - panel / 2, at + panel / 2, a0, a1, z0, z1)
            self.box(f"{prefix}_cap", mat, at - cap / 2, at + cap / 2, a0 + 0.015, a1 - 0.015, z1 - 0.03, z1 + 0.05, collide=False)

    def stair(self, prefix, mat, x0, x1, y_edge, out, z_top, z_ground):
        """A straight flight down from a deck's edge at `y_edge`, outward in
        `out`, to the ground at `z_ground`: the treads one stepped block,
        scenery (no collision), lapping 2 cm into the deck; the narrow ramp
        on the nosing line is the floor, flush with the deck's edge and
        ending inside the deck, its foot 2 cm below the treads' so the two
        share no plane; nosing strips 3 cm proud of the ramp."""
        n = max(1, round((z_top - z_ground) / RISER_ABOUT))
        riser = (z_top - z_ground) / n

        def y(s):
            return y_edge + out * s
        g = z_ground
        profile = [(y(n * GOING), g - BELOW)]
        for k in range(1, n):
            profile += [(y(n * GOING - (k - 1) * GOING), g + k * riser), (y(n * GOING - k * GOING), g + k * riser)]
        profile += [(y(-0.02), g + (n - 1) * riser), (y(-0.02), g - BELOW)]
        self.prism(f"{prefix}_treads", mat, profile, "x", x0, x1, collide=False)
        ramp = [(y(n * GOING + 0.05), g - BELOW - 0.02), (y(n * GOING), g), (y(0.0), z_top), (y(-0.06), g - BELOW - 0.02)]
        self.prism(f"{prefix}_ramp", mat, ramp, "x", x0 + 0.10, x1 - 0.10)
        for k in range(1, n):
            nose = n * GOING - (k - 1) * GOING
            ya, yb = sorted((y(nose + 0.01), y(nose - 0.05)))
            self.box(f"{prefix}_nosing_{k}", mat, x0 + 0.005, x1 - 0.005, ya, yb, g + k * riser - 0.01, g + k * riser + 0.03, collide=False)
        return n, riser

    def open_stair(self, prefix, mat, x0, x1, y_edge, out, z_top, z_ground, foot="ground"):
        """`stair` for a flight seen from beside and below, with air under it
        (the stilts', 3 Oct 2026: "that staircase doesnt need that grey mass
        under it"; `stair` fills its treads and its ramp down to the ground).
        The floor is `stair`'s ramp exactly: the same top plane through the
        treads' inner corners from the foot to the deck's edge, the same toe,
        width and grade, still the only part that collides; but a board
        OPEN_RAMP_T thick under that plane instead of a wedge, its top end
        sitting 2 cm into the top tread (whose back half it rises over, as
        `stair`'s does) and running 6 cm into the deck. The treads, the
        nosing strips and the top tread 2 cm under the deck's edge are
        `stair`'s too, but each tread a board OPEN_TREAD_T thick, open
        between, and scenery. Two cut stringers carry them, STRINGER_OUT
        past the tread ends: each tooth 2 cm into its tread, each riser cut
        5 mm in from a tread's back edge (under the next nosing strip, so no
        face meets a tread's or a nosing's), the bottom edge 5 cm under the
        ramp's, so from beside the ramp is hidden between the stringers and
        the tread ends; the top end rises 5 mm under the ramp's line to the
        deck's edge (the ramp's top edge shows those 5 mm over the top
        tread's back half, in its own colour) and runs 2 cm into the deck,
        sloping away from its top face. The stringers do not collide. `foot`
        is "ground" (the stringers' feet cut level 3 cm into it) or "rim" (a
        landing's back edge, which the stringers' bottoms run into)."""
        n = max(1, round((z_top - z_ground) / RISER_ABOUT))
        assert n >= 3, (prefix, n)
        riser = (z_top - z_ground) / n
        slope = riser / GOING
        g = z_ground
        tv = OPEN_RAMP_T / math.cos(math.atan(slope))     # the board's depth, plumb

        def y(s):
            return y_edge + out * s

        def line(s):
            """The ramp's top: through the treads' inner corners."""
            return g + (n * GOING - s) * slope

        def z(k):
            return g + k * riser

        def section(points):
            return [(y(s), zz) for s, zz in points]
        # the treads, one board each, the top one 2 cm under the deck's edge
        bm = bmesh.new()
        for k in range(1, n):
            ya, yb = sorted((y((n - k + 1) * GOING), y((n - k) * GOING if k < n - 1 else -0.02)))
            prism_bm([(x0, ya), (x1, ya), (x1, yb), (x0, yb)], "z", z(k) - OPEN_TREAD_T, z(k), bm=bm)
        self.finish(f"{prefix}_treads", bm, [mat], collide=False)
        # the ramp: `stair`'s toe, foot and top edge, then into the deck and
        # back down its underside (level where it sits into the top tread)
        toe = g - BELOW - 0.02
        zc = z(n - 1) - 0.02
        s_seat = n * GOING - (zc + tv - g) / slope
        s_toe = n * GOING - (toe + tv - g) / slope
        assert -0.06 < s_seat < s_toe < n * GOING, (prefix, s_seat, s_toe)
        ramp = [(n * GOING + 0.05, toe), (n * GOING, g), (0.0, z_top), (-0.06, zc), (s_seat, zc), (s_toe, toe)]
        self.prism(f"{prefix}_ramp", mat, section(ramp), "x", x0 + 0.10, x1 - 0.10)
        for k in range(1, n):
            nose = n * GOING - (k - 1) * GOING
            ya, yb = sorted((y(nose + 0.01), y(nose - 0.05)))
            self.box(f"{prefix}_nosing_{k}", mat, x0 + 0.005, x1 - 0.005, ya, yb, g + k * riser - 0.01, g + k * riser + 0.03, collide=False)
        # the stringers: the teeth from the foot up, the cheek over the top
        # tread to the deck's edge, then the bottom edge back down to the foot
        s_foot = n * GOING + 0.005
        top = [(s_foot, z(1) - 0.04)]
        for k in range(1, n - 1):
            cut = (n - k) * GOING + 0.005
            top += [(cut, z(k) - 0.04), (cut, z(k + 1) - 0.04)]
        s_cheek = n * GOING - (z(n - 1) - 0.035 - g) / slope
        top += [(s_cheek, z(n - 1) - 0.04), (0.0, z_top - 0.005), (-0.02, z_top - 0.03)]
        under = 0.05 + tv
        bottom = [(-0.02, line(-0.02) - under)]
        if foot == "ground":
            s_cut = n * GOING - (under - 0.03) / slope
            bottom += [(s_cut, g - 0.03), (s_foot, g - 0.03)]
        else:
            bottom += [(s_foot, line(s_foot) - under)]
        stringer = section(top + bottom)
        for tag, a, b in (("w", x0 - STRINGER_OUT, x0 - STRINGER_OUT + STRINGER_W),
                          ("e", x1 + STRINGER_OUT - STRINGER_W, x1 + STRINGER_OUT)):
            self.prism(f"{prefix}_stringer_{tag}", mat, stringer, "x", a, b, collide=False)
        return n, riser

    def skirt(self, part, mat, x0, x1, y0, y1, z_deck, z_ground):
        """The solid base under a deck, 10 cm under the ground, its top inside the deck."""
        self.box(part, mat, x0, x1, y0, y1, z_ground - 0.10, z_deck - PLATE_T + 0.02)

    def stair_rail(self, prefix, mat, x_at, y_edge, out, z_top, n, riser, z_ground=0.0):
        """A sloped rail beside a flight: a top newel on the deck, a foot
        newel on the ground or the landing below (its post 2 cm into
        either), a top rail and a bottom rail as parallelograms on the
        nosing line's slope, uprights on alternate treads."""
        slope = riser / GOING

        def y(s):
            return y_edge + out * s

        def zline(s):
            return z_top - s * slope
        ya, yb = sorted((y(-0.03), y(-0.03 - POST)))
        self.newel(f"{prefix}_newel_top", mat, x_at - POST / 2, ya, z_top)
        ya, yb = sorted((y(n * GOING + 0.03), y(n * GOING + 0.03 + POST)))
        self.newel(f"{prefix}_newel_foot", mat, x_at - POST / 2, ya, z_ground)
        sa, sb = -POST - 0.01, n * GOING + 0.05
        for name, lo, hi, half in (("top", RAIL_H - 0.08, RAIL_H, 0.04), ("bottom", 0.12, 0.18, 0.035)):
            poly = [(y(sa), zline(sa) + lo), (y(sb), zline(sb) + lo), (y(sb), zline(sb) + hi), (y(sa), zline(sa) + hi)]
            self.prism(f"{prefix}_{name}", mat, poly, "x", x_at - half, x_at + half)
        for m in range(1, n + 1, 2 if n > 4 else 1):
            s = (m - 0.5) * GOING
            tread_z = z_ground + (n - m) * riser
            ya, yb = sorted((y(s - 0.03), y(s + 0.03)))
            self.box(f"{prefix}_up{m}", mat, x_at - 0.03, x_at + 0.03, ya, yb, tread_z - 0.02, zline(s) + RAIL_H - 0.06)


def roof_under(x):
    """The main roof's underside over x, at any y under it."""
    return EAVE + (W / 2 - abs(x)) * TAN


# --- the house -----------------------------------------------------------------

def stickwork(kit, prefix, axis, face_at, outward, c, half, eave, tan, collar_z, width):
    """The peak's stick-work on a gable wall's face: a collar tie whose ends
    run into the roof slab, a king post from it up into the ridge, and a V
    of braces from the collar's middle up into the rakes at 50 degrees.
    Each member has its own proud and lap, so no two share a plane."""
    trim = kit.m["trim"]
    apex = eave + half * tan
    h = width / 2
    reach = half - (collar_z - eave) / tan + 0.10
    collar = [(c - reach, collar_z - h), (c + reach, collar_z - h), (c + reach, collar_z + h), (c - reach, collar_z + h)]
    kit.slab(f"{prefix}_collar", trim, axis, collar, face_at, outward, 0.080, 0.020)
    pw = h * 0.9
    post = [(c - pw, collar_z - h + 0.02), (c + pw, collar_z - h + 0.02), (c + pw, apex + 0.06), (c - pw, apex + 0.06)]
    kit.slab(f"{prefix}_post", trim, axis, post, face_at, outward, 0.090, 0.015)
    a = math.radians(50.0)
    s = (apex - collar_z - 0.02) / (math.sin(a) + math.cos(a) * tan) + 0.08
    for tag, sx, proud, lap in (("a", -1, 0.085, 0.018), ("b", 1, 0.082, 0.016)):
        end = (c + sx * s * math.cos(a), collar_z + 0.02 + s * math.sin(a))
        kit.slab(f"{prefix}_brace_{tag}", trim, axis, member((c, collar_z + 0.02), end, width), face_at, outward, proud, lap)


def pediment(kit, prefix, mat, face_y, a0, a1, z_head, tall):
    """A pointed cap over a front-wall door: a triangle on the head casing's
    width, lapped 2 cm into the casing's top, 5 cm proud."""
    base = z_head + 0.12 - 0.02
    poly = [(a0 - 0.12, base), (a1 + 0.12, base), ((a0 + a1) / 2, base + tall)]
    kit.prism(f"{prefix}_pediment", mat, poly, "y", face_y - 0.05, face_y + 0.02, collide=False)


def belt(kit, segments):
    """The belt course at the upstairs floor, 3 cm proud (a centimetre
    less than the corner boards, whose faces its ends lap behind), 1 cm into
    the wall. `segments`: (face, a0, a1)."""
    hw, hd = W / 2, D / 2
    z0, z1 = LOWER - BELT_H / 2, LOWER + BELT_H / 2
    trim = kit.m["trim"]
    for k, (face, a0, a1) in enumerate(segments):
        if face in ("front", "back"):
            y = -hd if face == "front" else hd
            lo, hi = (y - 0.03, y + 0.01) if face == "front" else (y - 0.01, y + 0.03)
            kit.box(f"belt_{face}{k}", trim, a0, a1, lo, hi, z0, z1, collide=False)
        else:
            x = -hw if face == "west" else hw
            lo, hi = (x - 0.03, x + 0.01) if face == "west" else (x - 0.01, x + 0.03)
            kit.box(f"belt_{face}{k}", trim, lo, hi, a0, a1, z0, z1, collide=False)


BAND_END_X = W / 2 - CORNER + PROUD + 0.02   # a band's end, 2 cm inside the corner board
BAND_END_Y = D / 2 - CORNER + PROUD + 0.02


def build_body(kit, openings, kinds, dormer=True):
    """The body: four walls with gables front and back (and the cross-gable
    rising from the east wall), corner boards cut to the slope, the gable
    roof, ridge cap, eave fascias and bargeboards, casings and panes.
    `kinds` names the openings that are doors, as (face, index) -> kind."""
    hw, hd, e = W / 2, D / 2, E_IN
    wall_top = EAVE + WALL_TOP_IN
    gable = Top(gable=(hw - e, hw, EAVE, TAN))
    flat = Top(flat=wall_top)
    east = Top(flat=wall_top, gable=(DORMER_YC + hd - e, DORMER_HALF, EAVE, TAN)) if dormer else flat
    feet = {"front": -BELOW, "back": -BELOW, "west": -BELOW - 0.01, "east": -BELOW - 0.01}
    kit.shell("", -hw, hw, -hd, hd, T, e, feet, {"front": gable, "back": gable, "west": flat, "east": east},
              openings, [kit.m["walls_lower"], kit.m["walls_upper"]], LOWER)
    kit.corner_boards("", kit.m["trim"], -hw, hw, -hd, hd, CORNER, PROUD, -BELOW - 0.03)
    y0, y1 = -hd - RAKE_OVER, hd + RAKE_OVER
    # the east overhang is cut away over the cross-gable's eaves, 2 cm wider
    # than them, so the eave and its fascia stop at its rakes
    notch = (DORMER_YC - DORMER_HALF - EAVE_OVER - 0.02, DORMER_YC + DORMER_HALF + EAVE_OVER + 0.02) if dormer else None
    main_roof(kit, notch)
    kit.box("ridge_cap", kit.m["roof"], -0.20, 0.20, y0 - 0.02, y1 + 0.02, RIDGE_TOP - 0.10, RIDGE_TOP + 0.05, collide=False)
    for face, y_rake, out in (("front", y0, -1), ("back", y1, 1)):
        kit.bargeboard(f"barge_{face}", kit.m["trim"], "y", 0.0, hw, EAVE, TAN, EAVE_OVER, ROOF_VT, y_rake, out, BARGE_H, 0.06, 0.02)
    # fascia boards along both eaves, 2 cm into the slab's edge, their ends
    # a centimetre past the bargeboards' faces; on the east they run on
    # under the cross-gable's rakes, as the photo's does, to where their
    # top meets its bargeboard's underside, a centimetre short of it
    xe = hw + EAVE_OVER
    ze = roof_under(xe)
    runs = {"w": [(y0 - 0.07, y1 + 0.07)], "e": [(y0 - 0.07, y1 + 0.07)]}
    if notch:
        into = DORMER_HALF + (ROOF_VT - 0.02 - BARGE_H - (ze - 0.03 + FASCIA_H - EAVE)) / TAN - 0.01
        runs["e"] = [(y0 - 0.07, DORMER_YC - into), (DORMER_YC + into, y1 + 0.07)]
    for tag, sx in (("w", -1), ("e", 1)):
        lo, hi = sorted((sx * (xe - 0.02), sx * (xe + 0.04)))
        for k, (ya, yb) in enumerate(runs[tag]):
            kit.box(f"fascia_{tag}{k}", kit.m["trim"], lo, hi, ya, yb, ze - 0.03, ze - 0.03 + FASCIA_H, collide=False)
    if dormer:
        build_dormer(kit)
    # casings, panes, doors
    for face, axis, at, out in (("front", "x", -hd, -1), ("back", "x", hd, 1), ("west", "y", -hw, -1), ("east", "y", hw, 1)):
        for k, (a0, a1, z0, z1) in enumerate(openings[face]):
            kind = kinds.get((face, k), "window")
            if kind == "window":
                kit.window(f"{face}{k}", kit.m, axis, at, out, a0, a1, z0, z1, rail=z1 - z0 > 1.5)
            elif kind == "door":
                kit.glazed_door(f"{face}{k}", kit.m, axis, at, out, a0, a1, z0, z1)
            elif kind == "balcony_door":
                kit.glazed_door(f"{face}{k}", kit.m, axis, at, out, a0, a1, z0, z1, light=(0.30, z0 + 0.35, z1 - 0.25))
            elif kind == "french_doors":
                kit.glazed_door(f"{face}{k}", kit.m, axis, at, out, a0, a1, z0, z1, light=(0.55, z0 + 0.35, z1 - 0.25))
                kit.mullions(f"{face}{k}", kit.m["trim"], axis, at, out, a0, a1, z0, z1, 2)
            elif kind == "carriage":
                carriage_doors(kit, a0, a1, z0, z1)
            elif kind == "garage":
                garage_door(kit, a0, a1, z0, z1)


def main_roof(kit, notch=None):
    """The main gable roof as one closed mesh: the chevron section swept
    from rake to rake, with the east overhang cut away over `notch` (a y
    range) down to a centimetre inside the wall's face, so the eave stops
    at the cross-gable as the photo's does. Every face is planar: the
    slopes, the rake ends, the eave edges and the notch's two sides."""
    hw, hd = W / 2, D / 2
    y0, y1 = -hd - RAKE_OVER, hd + RAKE_OVER
    xe = hw + EAVE_OVER
    bm = bmesh.new()
    verts = {}

    def v(x, y, z):
        key = (round(x, 5), round(y, 5), round(z, 5))
        if key not in verts:
            verts[key] = bm.verts.new((x, y, z))
        return verts[key]

    def under(x):
        return roof_under(x)

    def top(x):
        return roof_under(x) + ROOF_VT
    east = [(xe, y0), (xe, y1)]
    if notch:
        ya, yb = notch
        east = [(xe, y0), (xe, ya), (hw - 0.01, ya), (hw - 0.01, yb), (xe, yb), (xe, y1)]
    for z in (under, top):
        bm.faces.new([v(-xe, y0, z(-xe)), v(0.0, y0, z(0.0)), v(0.0, y1, z(0.0)), v(-xe, y1, z(-xe))])
        bm.faces.new([v(0.0, y0, z(0.0))] + [v(x, y, z(x)) for x, y in east] + [v(0.0, y1, z(0.0))])
    for y in (y0, y1):
        bm.faces.new([v(-xe, y, under(-xe)), v(0.0, y, under(0.0)), v(xe, y, under(xe)),
                      v(xe, y, top(xe)), v(0.0, y, top(0.0)), v(-xe, y, top(-xe))])
    bm.faces.new([v(-xe, y0, under(-xe)), v(-xe, y1, under(-xe)), v(-xe, y1, top(-xe)), v(-xe, y0, top(-xe))])
    for (xa, ya), (xb, yb) in zip(east, east[1:]):
        bm.faces.new([v(xa, ya, under(xa)), v(xb, yb, under(xb)), v(xb, yb, top(xb)), v(xa, ya, top(xa))])
    return kit.finish("roof", bm, [kit.m["roof"]])


def build_dormer(kit):
    """The cross-gable on the east wall, flush with it: its roof an inverted
    V along X whose eaves sit at the main eave's outer edge height, so it
    emerges from the main slope along two valleys and is buried inside the
    slab elsewhere (nothing is cut); a bargeboard on its rake, 10 cm past
    the main fascia; the stick-work in its peak."""
    hw = W / 2
    yc, half = DORMER_YC, DORMER_HALF
    # its underside passes through EAVE at the wall line (y = yc +- half)
    # and, EAVE_OVER further out, through the main eave edge's height: the
    # same pitch, so the valleys run at 45 degrees in plan
    kit.gable_roof("dormer_roof", kit.m["roof"], "x", yc, half, EAVE, TAN, EAVE_OVER, ROOF_T,
                   hw - half - 0.05, hw + RAKE_OVER)
    apex = EAVE + half * TAN + ROOF_VT
    kit.box("dormer_ridge_cap", kit.m["roof"], hw - half - 0.02, hw + RAKE_OVER + 0.02, yc - 0.18, yc + 0.18,
            apex - 0.10, apex + 0.05, collide=False)
    kit.bargeboard("dormer_barge", kit.m["trim"], "x", yc, half, EAVE, TAN, EAVE_OVER, ROOF_VT,
                   hw + RAKE_OVER, 1, BARGE_H, 0.06, 0.02)
    stickwork(kit, "dormer_stick", "x", hw, 1, yc, half, EAVE, TAN, DORMER_COLLAR_Z, 0.08)


def carriage_doors(kit, a0, a1, z0, z1):
    """The double carriage doors: one slab recessed 10 cm in the opening, a
    meeting stile up the middle and a rail across each leaf; the casing;
    the pilasters either side carrying the balcony, and the header between
    them under its plate."""
    hd = D / 2
    trim, door = kit.m["trim"], kit.m["door"]
    kit.opening_trim("carriage_trim", trim, "x", -hd, -1, a0, a1, z0, z1, sill=False)
    kit.pane("carriage_leaves", door, "x", -hd, -1, a0, a1, z0, z1, recess=0.10)
    c = (a0 + a1) / 2
    kit.bar("carriage_stile", trim, "x", -hd, -1, c - 0.05, c + 0.05, z0 + 0.01, z1 - 0.01, 0.115, -0.060)
    for tag, r0, r1 in (("a", a0 + 0.02, c - 0.07), ("b", c + 0.07, a1 - 0.02)):
        kit.bar(f"carriage_rail_{tag}", trim, "x", -hd, -1, r0, r1, 0.85, 0.95, 0.115, -0.070)
    pilasters(kit, a0, a1)


def garage_door(kit, a0, a1, z0, z1):
    """The plain variant's sectional door: one slab with two panel lines."""
    hd = D / 2
    kit.opening_trim("garage_trim", kit.m["trim"], "x", -hd, -1, a0, a1, z0, z1, sill=False)
    kit.pane("garage_leaf", kit.m["door"], "x", -hd, -1, a0, a1, z0, z1, recess=0.10)
    for k, z in enumerate(PLAIN_GARAGE_RAILS):
        kit.bar(f"garage_line{k}", kit.m["door"], "x", -hd, -1, a0 + 0.03, a1 - 0.03, z - 0.03, z + 0.03, 0.115, -0.085)
    pilasters(kit, a0, a1)


def pilasters(kit, a0, a1):
    """The posts flanking the carriage doors, from the ground into the
    balcony's plate, and the header beam between them."""
    hd = D / 2
    trim = kit.m["trim"]
    for tag, x0 in (("w", a0 - PIL_GAP - PIL_W), ("e", a1 + PIL_GAP)):
        kit.box(f"pilaster_{tag}", trim, x0, x0 + PIL_W, -hd - PIL_PROUD, -hd + 0.02, -0.03, LOWER - PLATE_T + 0.02)
    # 3 cm into the pilasters: the balcony's arms end 2 cm inside them
    kit.box("header", trim, a0 - PIL_GAP - 0.03, a1 + PIL_GAP + 0.03, -hd - 0.12, -hd + 0.015, BEAM_Z[0], BEAM_Z[1], collide=False)


def balcony(kit, c, half, depth, strut_xs):
    """The balcony over the carriage doors: a floor plate lapped 3 cm into
    the wall at the belt, an arm under it at each strut with a diagonal
    strut down to the pilaster or corner board it lands on and a turned
    pendant at its tip; newels at the outer corners, solid panel rails
    between them and back to the wall. `strut_xs` are (x centre, y of the
    strut's foot) pairs; a foot at -hd + 0.08 is inside the wall."""
    hd = D / 2
    trim, deck = kit.m["trim"], kit.m["deck"]
    z_floor = LOWER
    x0, x1 = c - half, c + half
    y_out = -hd - depth
    kit.box("balcony", deck, x0, x1, y_out, -hd + 0.03, z_floor - PLATE_T, z_floor)
    for k, (x, y_foot) in enumerate(strut_xs):
        arm_back = -hd - 0.10 if y_foot < -hd else -hd + 0.01
        kit.box(f"balcony_arm{k}", trim, x - 0.06, x + 0.06, y_out + 0.04, arm_back, z_floor - PLATE_T - 0.14, z_floor - PLATE_T + 0.01)
        a = (y_out + 0.16, z_floor - PLATE_T - 0.07)
        b = (y_foot, STRUT_FOOT_Z)
        kit.prism(f"balcony_strut{k}", trim, member(a, b, 0.10), "x", x - 0.045, x + 0.045, collide=False)
        kit.octo(f"balcony_pendant{k}", trim, x, y_out + 0.10, 0.055, z_floor - PLATE_T - 0.29, z_floor - PLATE_T - 0.12)
    # the newels 4.5 cm in from the plate's edge, panel rails between
    for tag, nx in (("w", x0 + 0.03), ("e", x1 - 0.03 - POST)):
        kit.newel(f"balcony_newel_{tag}", trim, nx, y_out + 0.045, z_floor)
    post_y = y_out + 0.045 + POST / 2
    kit.panel_rail("balcony_rail_front", trim, "x", post_y, x0 + 0.03 + POST - 0.02, x1 - 0.03 - POST + 0.02, z_floor)
    kit.panel_rail("balcony_rail_w", trim, "y", x0 + 0.03 + POST / 2, post_y + POST / 2 - 0.02, -hd + 0.05, z_floor)
    kit.panel_rail("balcony_rail_e", trim, "y", x1 - 0.03 - POST / 2, post_y + POST / 2 - 0.02, -hd + 0.05, z_floor)


def shed_hood(kit, prefix, axis, face_at, outward, c, half=None, brace=None):
    """The shed hood over a door: a slab sloping down away from the wall,
    lapped 3 cm into it, a fascia along its outer edge, and under it two
    braces from the hood down to cleats on the wall."""
    roof, trim = kit.m["roof"], kit.m["trim"]
    out, rise, drop, thick = (HOOD[k] for k in ("out", "rise", "drop", "thick"))
    half = HOOD["half"] if half is None else half
    brace = HOOD["brace"] if brace is None else brace
    f_in, f_out = face_at - 0.03 * outward, face_at + out * outward
    section = [(f_in, rise), (f_out, rise - drop), (f_out, rise - drop + thick), (f_in, rise + thick)]
    # the section lies in the plane across the wall and is extruded along
    # the wall's run, which is the opening axis
    run = axis
    kit.prism(f"{prefix}_hood", roof, section, run, c - half, c + half)
    kit.bar(f"{prefix}_hood_fascia", trim, axis, face_at, outward, c - half - 0.02, c + half + 0.02,
            rise - drop - 0.02, rise - drop + thick + 0.02, -(abs(f_out - face_at) - 0.02), abs(f_out - face_at) + 0.04)
    for tag, s in (("a", -1), ("b", 1)):
        a = (face_at + 0.70 * outward, rise - 0.70 * drop / out + 0.06)
        b = (face_at + 0.02 * outward, 1.70)
        kit.prism(f"{prefix}_hood_brace_{tag}", trim, member(a, b, 0.08), run, c + s * brace - 0.04, c + s * brace + 0.04, collide=False)
        kit.bar(f"{prefix}_hood_cleat_{tag}", trim, axis, face_at, outward, c + s * brace - 0.05, c + s * brace + 0.05,
                1.55, rise - 0.02, 0.02, 0.06)


def skylight(kit, prefix, y0, y1, x0, x1):
    """A skylight on the east slope: a frame lapped into the slab and a
    glass slab on it, both as prisms along the slope so nothing is tilted."""
    def top(x):
        return roof_under(x) + ROOF_VT
    frame = [(x0 - 0.08, top(x0 - 0.08) - 0.02), (x1 + 0.08, top(x1 + 0.08) - 0.02),
             (x1 + 0.08, top(x1 + 0.08) + 0.05), (x0 - 0.08, top(x0 - 0.08) + 0.05)]
    kit.prism(f"{prefix}_frame", kit.m["trim"], frame, "y", y0 - 0.08, y1 + 0.08, collide=False)
    glass = [(x0, top(x0) + 0.03), (x1, top(x1) + 0.03), (x1, top(x1) + 0.08), (x0, top(x0) + 0.08)]
    kit.prism(f"{prefix}_glass", kit.m["glass"], glass, "y", y0, y1, collide=False)


def flue_and_vane(kit):
    """The round metal flue by the ridge with its cap, and the weathervane
    on the ridge's back end: a rod, cross-arms and an arrow."""
    metal = kit.m["metal"]
    x, y, r, top = FLUE
    kit.octo("flue", metal, x, y, r, roof_under(x) + ROOF_VT - 0.25, top)
    kit.octo("flue_cap", metal, x, y, r + 0.07, top - 0.02, top + 0.06)
    vy = VANE_Y
    kit.octo("vane_rod", metal, 0.0, vy, 0.02, RIDGE_TOP - 0.06, RIDGE_TOP + 1.20)
    kit.box("vane_arm_x", metal, -0.26, 0.26, vy - 0.015, vy + 0.015, RIDGE_TOP + 0.735, RIDGE_TOP + 0.765, collide=False)
    kit.box("vane_arm_y", metal, -0.014, 0.014, vy - 0.26, vy + 0.26, RIDGE_TOP + 0.736, RIDGE_TOP + 0.764, collide=False)
    za = RIDGE_TOP + 1.10
    kit.box("vane_shaft", metal, -0.012, 0.012, vy - 0.30, vy + 0.22, za - 0.012, za + 0.012, collide=False)
    kit.prism("vane_head", metal, [(vy - 0.42, za), (vy - 0.28, za + 0.06), (vy - 0.28, za - 0.06)], "x", -0.005, 0.005, collide=False)
    kit.prism("vane_tail", metal, [(vy + 0.20, za - 0.07), (vy + 0.34, za), (vy + 0.20, za + 0.07)], "x", -0.004, 0.004, collide=False)


def round_vent(kit, prefix, face_y, out):
    """The plain variant's peak: a round louvred vent as a ring and a disc."""
    kit.slab(f"{prefix}_ring", kit.m["trim"], "y", octagon(0.0, PLAIN_VENT_Z, PLAIN_VENT_R), face_y, out, 0.05, 0.02)
    kit.slab(f"{prefix}_disc", kit.m["door"], "y", octagon(0.0, PLAIN_VENT_Z, PLAIN_VENT_R - 0.10), face_y, out, 0.07, 0.01)


def build_photo(kit):
    hw, hd = W / 2, D / 2
    openings = {
        "front": [(*CARRIAGE_X, THRESHOLD, CARRIAGE_H), (*BAL_DOOR_X, LOWER + THRESHOLD, LOWER + 2.05)],
        "back": [(*BACK_WIN_X, SILL, HEAD), (*BACK_UP_WIN_X, *UP_WIN)],
        "west": [(*w, SILL, HEAD) for w in WEST_WINS_Y] + [(*WEST_KNEE_Y, *KNEE_WIN)],
        "east": [(*FRONT_DOOR_Y, THRESHOLD, DOOR_H),
                 (DORMER_YC - DORMER_WIN[0], DORMER_YC + DORMER_WIN[0], DORMER_WIN[1], DORMER_WIN[2])],
    }
    kinds = {("front", 0): "carriage", ("front", 1): "balcony_door", ("east", 0): "door"}
    build_body(kit, openings, kinds, dormer=True)
    belt(kit, [("front", -BAND_END_X, BAND_END_X), ("back", -BAND_END_X, BAND_END_X),
               ("west", -BAND_END_Y, BAND_END_Y), ("east", -BAND_END_Y, BAND_END_Y)])
    pediment(kit, "balcony_door", kit.m["trim"], -hd, *BAL_DOOR_X, LOWER + 2.05, 0.30)
    stickwork(kit, "stick", "y", -hd, -1, 0.0, hw, EAVE, TAN, COLLAR_Z, 0.10)
    a0, a1 = CARRIAGE_X
    balcony(kit, 0.0, BAL_HALF, BAL_D, [(a0 - PIL_GAP - PIL_W / 2, -hd - 0.07), (a1 + PIL_GAP + PIL_W / 2, -hd - 0.07)])
    shed_hood(kit, "front_door", "y", hw, 1, (FRONT_DOOR_Y[0] + FRONT_DOOR_Y[1]) / 2)
    skylight(kit, "skylight", *SKYLIGHT)
    flue_and_vane(kit)


def build_plain(kit):
    hw, hd = W / 2, D / 2
    openings = {
        "front": [(*CARRIAGE_X, THRESHOLD, CARRIAGE_H), (*PLAIN_DOORS_X, LOWER + THRESHOLD, LOWER + 2.05)],
        "back": [(*BACK_WIN_X, SILL, HEAD), (*BACK_UP_WIN_X, *UP_WIN)],
        "west": [(*w, SILL, HEAD) for w in WEST_WINS_Y] + [(*WEST_KNEE_Y, *KNEE_WIN)],
        "east": [(*FRONT_DOOR_Y, THRESHOLD, DOOR_H), (*EAST_KNEE_Y, *KNEE_WIN)],
    }
    kinds = {("front", 0): "garage", ("front", 1): "french_doors", ("east", 0): "door"}
    build_body(kit, openings, kinds, dormer=False)
    belt(kit, [("front", -BAND_END_X, BAND_END_X), ("back", -BAND_END_X, BAND_END_X),
               ("west", -BAND_END_Y, BAND_END_Y), ("east", -BAND_END_Y, BAND_END_Y)])
    pediment(kit, "balcony_door", kit.m["trim"], -hd, *PLAIN_DOORS_X, LOWER + 2.05, 0.34)
    round_vent(kit, "vent_front", -hd, -1)
    round_vent(kit, "vent_back", hd, 1)
    a0, a1 = CARRIAGE_X
    balcony(kit, 0.0, PLAIN_BAL_HALF, PLAIN_BAL_D, [(a0 - PIL_GAP - PIL_W / 2, -hd - 0.07), (a1 + PIL_GAP + PIL_W / 2, -hd - 0.07)])
    shed_hood(kit, "front_door", "y", hw, 1, (FRONT_DOOR_Y[0] + FRONT_DOOR_Y[1]) / 2)
    skylight(kit, "skylight", *SKYLIGHT)
    skylight(kit, "skylight2", *PLAIN_SKYLIGHT_2)
    flue_and_vane(kit)


def build_hillside(kit):
    hw, hd = W / 2, D / 2
    openings = {
        "front": [(*HILL_CARRIAGE_X, THRESHOLD, CARRIAGE_H), (*HILL_DOOR_X, THRESHOLD, DOOR_H),
                  (*HILL_BAL_DOOR_X, LOWER + THRESHOLD, LOWER + 2.05)],
        "back": [(*HILL_BACK_DOOR_X, LOWER + THRESHOLD, LOWER + DOOR_H), (*HILL_BACK_UP_WIN_X, *UP_WIN)],
        "west": [(*WEST_KNEE_Y, *KNEE_WIN)],
        "east": [(DORMER_YC - DORMER_WIN[0], DORMER_YC + DORMER_WIN[0], DORMER_WIN[1], DORMER_WIN[2])],
    }
    kinds = {("front", 0): "carriage", ("front", 1): "door", ("front", 2): "balcony_door", ("back", 0): "door"}
    build_body(kit, openings, kinds, dormer=True)
    belt(kit, [("front", -BAND_END_X, BAND_END_X), ("back", -BAND_END_X, BAND_END_X),
               ("west", -BAND_END_Y, BAND_END_Y), ("east", -BAND_END_Y, BAND_END_Y)])
    pediment(kit, "balcony_door", kit.m["trim"], -hd, *HILL_BAL_DOOR_X, LOWER + 2.05, 0.30)
    stickwork(kit, "stick", "y", -hd, -1, 0.0, hw, EAVE, TAN, COLLAR_Z, 0.10)
    # the full-width balcony on the two pilasters and, with the doors
    # shifted east, a third strut lapped into the wall beside the west corner board
    a0, a1 = HILL_CARRIAGE_X
    balcony(kit, 0.0, BAL_HALF, BAL_D, [(HILL_STRUT_W_X, -hd + 0.08), (a0 - PIL_GAP - PIL_W / 2, -hd - 0.07),
                                       (a1 + PIL_GAP + PIL_W / 2, -hd - 0.07)])
    skylight(kit, "skylight", *SKYLIGHT)
    flue_and_vane(kit)
    # the deck off the back door on the pad behind, one step down to it,
    # rails on its two sides, the back edge open to the step
    trim, deck = kit.m["trim"], kit.m["deck"]
    x0, x1 = DECK_X
    y_edge = hd + DECK_D
    kit.box("deck", deck, x0, x1, hd - 0.03, y_edge, LOWER - PLATE_T, LOWER)
    kit.skirt("deck_skirt", kit.m["walls_lower"], x0 + 0.08, x1 - 0.08, hd - 0.04, y_edge - 0.08, LOWER, PAD_Z)
    c = (HILL_BACK_DOOR_X[0] + HILL_BACK_DOOR_X[1]) / 2
    kit.stair("deck_step", deck, c - STAIR_W / 2, c + STAIR_W / 2, y_edge, 1, LOWER, PAD_Z)
    for tag, nx in (("w", x0 + 0.03), ("e", x1 - 0.03 - POST)):
        kit.newel(f"deck_newel_{tag}", trim, nx, y_edge - 0.045 - POST, LOWER)
    post_y = y_edge - 0.045 - POST / 2
    kit.panel_rail("deck_rail_w", trim, "y", x0 + 0.03 + POST / 2, hd + 0.05, post_y - POST / 2 + 0.02, LOWER)
    kit.panel_rail("deck_rail_e", trim, "y", x1 - 0.03 - POST / 2, hd + 0.05, post_y - POST / 2 + 0.02, LOWER)


def x_brace(kit, prefix, axis, a, b, face_at, outward):
    """An X of two timber braces between two piles of one row, in the row's
    plane on its outer face, each from one pile's foot to the other's head,
    lapped into both piles. The two have their own proud and lap, so they
    share no plane where they cross; `axis` is the row's run."""
    za, zb = ST_BRACE_Z
    for tag, z0, z1, proud, lap in (("a", za, zb, 0.08, 0.02), ("b", zb, za, 0.07, 0.01)):
        kit.slab(f"{prefix}_{tag}", kit.m["pile"], axis, member((a, z0), (b, z1), 0.12), face_at, outward, proud, lap)


def weathervane(kit, vy, ridge_top):
    """A weathervane on the ridge: a rod, cross-arms and an arrow."""
    metal = kit.m["metal"]
    kit.octo("vane_rod", metal, 0.0, vy, 0.02, ridge_top - 0.06, ridge_top + 1.20)
    kit.box("vane_arm_x", metal, -0.26, 0.26, vy - 0.015, vy + 0.015, ridge_top + 0.735, ridge_top + 0.765, collide=False)
    kit.box("vane_arm_y", metal, -0.014, 0.014, vy - 0.26, vy + 0.26, ridge_top + 0.736, ridge_top + 0.764, collide=False)
    za = ridge_top + 1.10
    kit.box("vane_shaft", metal, -0.012, 0.012, vy - 0.30, vy + 0.22, za - 0.012, za + 0.012, collide=False)
    kit.prism("vane_head", metal, [(vy - 0.42, za), (vy - 0.28, za + 0.06), (vy - 0.28, za - 0.06)], "x", -0.005, 0.005, collide=False)
    kit.prism("vane_tail", metal, [(vy + 0.20, za - 0.07), (vy + 0.34, za), (vy + 0.20, za + 0.07)], "x", -0.004, 0.004, collide=False)


def build_stilts(kit):
    """The beach house: the upper body on piles. The platform is one plate
    (the body's floor, the front and side decks and the stair's top
    landing, as one L-shaped prism so nothing on it shares a plane); the
    piles stand 2 cm into it; the walls' feet, the newels and the rails
    stand in it. The stair is two flights of nine risers beside the side
    deck, from the ground at the back to a middle landing on posts and on
    up to the platform's landing at the front corner, each flight by the
    stair rule and open beneath (`Kit.open_stair`): the walking ramp a
    board between two cut stringers, the treads boards, and under them air
    down to the ground; the middle landing a 0.20 m plate on its four posts."""
    hw, hd = W / 2, D / 2
    walls, trim, deck, roof, pile = (kit.m[k] for k in ("walls", "trim", "deck", "roof", "pile"))
    floor, eave = ST_FLOOR, ST_EAVE
    wall_top = eave + WALL_TOP_IN
    px0, px1 = -hw - ST_LIP, hw + ST_SIDE_DECK
    py0, py1 = -hd - ST_FRONT_DECK, hd + ST_LIP
    sx0, sx1 = ST_STAIR_X
    lx1 = sx1 + 0.05 + POST     # the top landing runs under the stair's outer newels
    ly1 = py0 + ST_LANDING_D
    # the platform
    kit.prism("platform", deck, [(px0, py0), (lx1, py0), (lx1, ly1), (px1, ly1), (px1, py1), (px0, py1)], "z",
              floor - ST_PLATE_T, floor)
    # the body on it
    sill, head = floor + ST_WIN[0], floor + ST_WIN[1]
    g0, g1 = floor + ST_GABLE_WIN[0], floor + ST_GABLE_WIN[1]
    openings = {
        "front": [(*ST_DOORS_X, floor + THRESHOLD, floor + DOOR_H), (*ST_GABLE_WIN_X, g0, g1)],
        "back": [(*ST_BACK_WIN_X, sill, head), (*ST_GABLE_WIN_X, g0, g1)],
        "west": [(*w, sill, head) for w in ST_WEST_WINS_Y],
        "east": [(*ST_DOOR_Y, floor + THRESHOLD, floor + DOOR_H)] + [(*w, sill, head) for w in ST_EAST_WINS_Y],
    }
    e = E_IN
    gable = Top(gable=(hw - e, hw, eave, TAN))
    flat = Top(flat=wall_top)
    feet = {"front": floor - 0.03, "back": floor - 0.03, "west": floor - 0.04, "east": floor - 0.04}
    kit.shell("", -hw, hw, -hd, hd, T, e, feet, {"front": gable, "back": gable, "west": flat, "east": flat},
              openings, [walls, walls], floor - 1.0)
    kit.corner_boards("", trim, -hw, hw, -hd, hd, CORNER, PROUD, floor - 0.05, eave=eave)
    y0, y1 = -hd - RAKE_OVER, hd + RAKE_OVER
    kit.gable_roof("roof", roof, "y", 0.0, hw, eave, TAN, EAVE_OVER, ROOF_T, y0, y1)
    kit.box("ridge_cap", roof, -0.20, 0.20, y0 - 0.02, y1 + 0.02, ST_RIDGE_TOP - 0.10, ST_RIDGE_TOP + 0.05, collide=False)
    for face, y_rake, out in (("front", y0, -1), ("back", y1, 1)):
        kit.bargeboard(f"barge_{face}", trim, "y", 0.0, hw, eave, TAN, EAVE_OVER, ROOF_VT, y_rake, out, BARGE_H, 0.06, 0.02)
    xe = hw + EAVE_OVER
    ze = eave - EAVE_OVER * TAN
    for tag, sx in (("w", -1), ("e", 1)):
        lo, hi = sorted((sx * (xe - 0.02), sx * (xe + 0.04)))
        kit.box(f"fascia_{tag}", trim, lo, hi, y0 - 0.07, y1 + 0.07, ze - 0.03, ze - 0.03 + FASCIA_H, collide=False)
    for face, axis, at, out in (("front", "x", -hd, -1), ("back", "x", hd, 1), ("west", "y", -hw, -1), ("east", "y", hw, 1)):
        for k, (a0, a1, z0, z1) in enumerate(openings[face]):
            if face == "front" and k == 0:
                kit.glazed_door(f"{face}{k}", kit.m, axis, at, out, a0, a1, z0, z1, light=(0.55, z0 + 0.35, z1 - 0.25))
                kit.mullions(f"{face}{k}", trim, axis, at, out, a0, a1, z0, z1, 2)
            elif face == "east" and k == 0:
                kit.glazed_door(f"{face}{k}", kit.m, axis, at, out, a0, a1, z0, z1, light=(0.25, z0 + 0.94, z0 + 1.94))
            else:
                kit.window(f"{face}{k}", kit.m, axis, at, out, a0, a1, z0, z1)
    pediment(kit, "doors", trim, -hd, *ST_DOORS_X, floor + DOOR_H, 0.34)
    stickwork(kit, "stick", "y", -hd, -1, 0.0, hw, eave, TAN, ST_COLLAR_Z, 0.10)
    weathervane(kit, ST_VANE_Y, ST_RIDGE_TOP)
    # the piles, and the X-bracing on the four outer rows
    piles = [(x, y) for x in ST_PILE_X for y in ST_PILE_Y] + list(ST_PILES_EXTRA)
    for k, (x, y) in enumerate(piles):
        kit.octo(f"pile{k}", pile, x, y, ST_PILE_R, ST_PILE_FOOT, ST_PILE_TOP, collide=True)
    flat_r = ST_PILE_R * math.cos(math.pi / 8)      # an eight-sided pile's flat face
    front = sorted(x for x, y in piles if y == ST_PILE_Y[0])
    back = sorted(x for x, y in piles if y == ST_PILE_Y[-1])
    for k, (a, b) in enumerate(zip(front, front[1:])):
        x_brace(kit, f"brace_front{k}", "y", a, b, ST_PILE_Y[0] - flat_r, -1)
    for k, (a, b) in enumerate(zip(back, back[1:])):
        x_brace(kit, f"brace_back{k}", "y", a, b, ST_PILE_Y[-1] + flat_r, 1)
    for k, (a, b) in enumerate(zip(ST_PILE_Y, ST_PILE_Y[1:])):
        x_brace(kit, f"brace_east{k}", "x", a, b, ST_PILE_X[-1] + flat_r, 1)
        x_brace(kit, f"brace_west{k}", "x", a, b, ST_PILE_X[0] - flat_r, -1)
    # the deck rails: newels at the corners and every few metres, solid
    # panels between, their ends into the newels or the corner boards
    def newel_at(tag, x0, y0):
        kit.newel(f"deck_newel_{tag}", trim, x0, y0, floor)
    newel_at("sw", px0 + 0.03, py0 + 0.045)
    newel_at("se", lx1 - 0.03 - POST, py0 + 0.045)
    for k, x in enumerate((0.0, 2.5)):
        newel_at(f"f{k}", x - POST / 2, py0 + 0.045)
    newel_at("ef", px1 - 0.03 - POST, ly1 + 0.03)
    newel_at("ne", px1 - 0.03 - POST, py1 - 0.03 - POST)
    for k, y in enumerate((-2.3, 1.3)):
        newel_at(f"e{k}", px1 - 0.03 - POST, y - POST / 2)
    front_y = py0 + 0.045 + POST / 2
    kit.panel_rail("deck_rail_front", trim, "x", front_y, px0 + 0.03 + POST - 0.02, lx1 - 0.03 - POST + 0.02, floor)
    kit.panel_rail("deck_rail_west", trim, "y", px0 + 0.03 + POST / 2, front_y + POST / 2 - 0.02, -hd + 0.05, floor)
    # the top landing's outer rail runs to the stair's outer top newel
    kit.panel_rail("deck_rail_landing", trim, "y", lx1 - 0.03 - POST / 2 - 0.02, front_y + POST / 2 - 0.02, ly1 - 0.03 - POST + 0.03, floor)
    east_x = px1 - 0.03 - POST / 2
    kit.panel_rail("deck_rail_east", trim, "y", east_x, ly1 + 0.03 + POST - 0.02, py1 - 0.03 - POST + 0.02, floor)
    kit.panel_rail("deck_rail_back", trim, "x", py1 - 0.03 - POST / 2, hw - 0.02, px1 - 0.03 - POST + 0.02, floor)
    # the stair: the upper flight down from the landing's back edge, the
    # middle landing on four posts, the lower flight down to the ground
    n_up, r_up = kit.open_stair("stair_upper", deck, sx0, sx1, ly1, 1, floor, ST_MID_Z, foot="rim")
    my0 = ly1 + n_up * GOING + 0.02
    my1 = ly1 + n_up * GOING + ST_LANDING_D
    # the landing 2 cm past the newels either side and under the upper
    # flight's foot; its posts a centimetre off every face that meets them
    kit.box("stair_landing", deck, sx0 - 0.14, sx1 + 0.14, my0 - 0.04, my1, ST_MID_Z - 0.20, ST_MID_Z)
    for tag, x in (("w", sx0 - 0.11), ("e", sx1 + 0.11 - POST)):
        for tag2, y in (("f", my0 - 0.01), ("b", my1 - 0.03 - POST)):
            kit.box(f"landing_post_{tag}{tag2}", pile, x, x + POST, y, y + POST, ST_PILE_FOOT, ST_MID_Z - 0.20 + 0.02)
    n_lo, r_lo = kit.open_stair("stair_lower", deck, sx0, sx1, my1, 1, ST_MID_Z, 0.0)
    for tag, x_at in (("w", sx0 - 0.05), ("e", sx1 + 0.05)):
        kit.stair_rail(f"stair_upper_rail_{tag}", trim, x_at, ly1, 1, floor, n_up, r_up, z_ground=ST_MID_Z)
        kit.stair_rail(f"stair_lower_rail_{tag}", trim, x_at, my1, 1, ST_MID_Z, n_lo, r_lo)
        kit.panel_rail(f"landing_rail_{tag}", trim, "y", x_at, ly1 + n_up * GOING + 0.03 + POST - 0.02, my1 - 0.03 - POST + 0.03, ST_MID_Z)


def build_variant(v, coll):
    kit = Kit(v, coll)
    {"photo": build_photo, "plain": build_plain, "hillside": build_hillside, "stilts": build_stilts}[v](kit)


# --- reference -----------------------------------------------------------------

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
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    mesh.materials.append(mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0)))
    obj[TAG] = True
    obj["kyt_collision"] = "none"
    obj.location = (x, y, z)
    coll.objects.link(obj)
    return obj


def outline(name, coll, x0, x1, y0, y1, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    for i in range(4):
        bm.edges.new((vs[i], vs[(i + 1) % 4]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def hill_ground_z(y):
    """The hillside's ground: the street level to the front wall, a 35 %
    rise to the pad just before the back wall, the pad past the deck, then
    the hill again."""
    hd = D / 2
    if y <= -hd:
        return 0.0
    if y <= -hd + PAD_Z / HILL_SLOPE:
        return HILL_SLOPE * (y + hd)
    if y <= PAD_END:
        return PAD_Z
    return PAD_Z + HILL_SLOPE * (y - PAD_END)


def hill_mesh(name, coll, mat, x0, x1, y0, y1, ox=0.0, thick=None):
    """The hillside's ground as a strip, a thin solid when `thick` is given."""
    hd = D / 2
    ys = sorted({y0, -hd, -hd + PAD_Z / HILL_SLOPE, PAD_END, y1})
    ys = [y for y in ys if y0 <= y <= y1]
    bm = bmesh.new()
    rows = [[bm.verts.new((ox + x, y, hill_ground_z(y))) for x in (x0, x1)] for y in ys]
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    if thick:
        under = [[bm.verts.new((ox + x, y, hill_ground_z(y) - thick)) for x in (x0, x1)] for y in ys]
        for a, b in zip(under, under[1:]):
            bm.faces.new((b[0], b[1], a[1], a[0]))
        for k in range(len(ys) - 1):
            bm.faces.new((rows[k][0], under[k][0], under[k + 1][0], rows[k + 1][0]))
            bm.faces.new((rows[k][1], rows[k + 1][1], under[k + 1][1], under[k][1]))
        bm.faces.new((rows[0][0], rows[0][1], under[0][1], under[0][0]))
        bm.faces.new((rows[-1][0], under[-1][0], under[-1][1], rows[-1][1]))
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    mesh.materials.append(mat)
    obj[TAG] = True
    obj["kyt_collision"] = "none"
    coll.objects.link(obj)
    return obj


def build_reference(reference):
    hw, hd = W / 2, D / 2
    outline("footprint_body", reference, -hw, hw, -hd, hd)
    outline("lot_9m", reference, LOT_X0, LOT_X0 + LOT_W, LOT_Y[0], LOT_Y[1])
    outline("driveway", reference, hw + 0.1, LOT_X0 + LOT_W, LOT_Y[0], hd + 2.0)
    figure("figure_1p7m", reference, 4.0, -6.0)
    hill_mesh("hillside_ground_reference", reference, material("reference_ground", (0.35, 0.45, 0.25, 1.0)),
              LOT_X0, LOT_X0 + LOT_W, -12.0, 14.0)
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        reference.objects.link(marker)


# --- checks --------------------------------------------------------------------

def triangles(objs):
    total = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            total += len(o.data.loop_triangles)
    return total


def coplanar_pairs(objs, tol=1e-4):
    """Pairs of faces from different objects lying in one plane and
    overlapping in area (by their bounds in the plane): the z-fights. Each
    face's plane is written the same way up, so a pair facing opposite
    ways is found too."""
    faces = []
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        rot = mw.to_3x3()
        for p in o.data.polygons:
            n = (rot @ p.normal).normalized()
            for c in n:
                if abs(c) > 1e-6:
                    if c < 0:
                        n = -n
                    break
            pts = [mw @ o.data.vertices[i].co for i in p.vertices]
            d = n.dot(pts[0])
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            flat = [(q.dot(e1), q.dot(e2)) for q in pts]
            us, vs = [a for a, _ in flat], [b for _, b in flat]
            faces.append((d, o.name, n, min(us), max(us), min(vs), max(vs), flat))
    faces.sort(key=lambda f: f[0])

    def overlap(P, Q):
        """Two polygons in the plane overlap unless an edge of either
        separates them (exact for convex faces, conservative otherwise)."""
        for poly in (P, Q):
            n = len(poly)
            for k in range(n):
                ax, ay = poly[(k + 1) % n][0] - poly[k][0], poly[(k + 1) % n][1] - poly[k][1]
                length = math.hypot(ax, ay)
                if length < 1e-9:
                    continue
                nx, ny = -ay / length, ax / length
                p = [x * nx + y * ny for x, y in P]
                q = [x * nx + y * ny for x, y in Q]
                if min(max(p), max(q)) - max(min(p), min(q)) <= 1e-3:
                    return False
        return True

    found = []
    for i in range(len(faces)):
        di, oi, ni, u0, u1, v0, v1, pi = faces[i]
        j = i + 1
        while j < len(faces) and faces[j][0] - di < tol:
            dj, oj, nj, w0, w1, x0, x1, pj = faces[j]
            j += 1
            if oi == oj or (ni - nj).length > 1e-3:
                continue
            ou = min(u1, w1) - max(u0, w0)
            ov = min(v1, x1) - max(v0, x0)
            if ou > 1e-3 and ov > 1e-3 and overlap(pi, pj):
                found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def report(objs, label):
    bpy.context.view_layer.update()
    objs = [o for o in objs if o.type == "MESH"]
    tris = triangles(objs)
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    print(f"{NAME}: {label}: {len(objs)} parts, {tris} triangles, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, z {min(zs):.2f}..{max(zs):.2f}")
    return tris


# --- renders -------------------------------------------------------------------

def variant_parts(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and o.get("kyt_variant") == variant]


def render(folder):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True
    kit = Kit("photo", stage)       # a maker for the stage's own pieces
    kit.v = "_stage"

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    ground = mat("_ground", (0.36, 0.44, 0.26))
    walk = mat("_walk", (0.62, 0.60, 0.56))
    street = mat("_street", (0.28, 0.28, 0.30))
    kit.box("ground", ground, -60, 60, -60, 60, -0.30, -0.01, collide=False)
    kit.box("walk", walk, -60, 60, LOT_Y[0] - 1.6, LOT_Y[0], -0.30, 0.0, collide=False)
    kit.box("street", street, -60, 60, -60, LOT_Y[0] - 1.6, -0.30, -0.005, collide=False)
    hd = D / 2
    drives = [kit.box("drive", walk, W / 2 + 0.2, LOT_X0 + LOT_W - 0.2, LOT_Y[0] - 1.6, hd + 2.0, -0.30, 0.004, collide=False),
              kit.box("apron", walk, -2.2, 2.2, LOT_Y[0] - 1.6, -hd - 0.3, -0.30, 0.003, collide=False)]
    hills = {}
    for ox in (0.0, 2 * LOT_W):
        hills[ox] = hill_mesh(f"_hill_{int(ox)}", stage, ground, LOT_X0 + 0.05, LOT_X0 + LOT_W - 0.05, -hd - 0.3, 40.0, ox=ox, thick=6.0)
        hills[ox].hide_render = True
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    fig_obj = figure("_figure", stage, 3.9, -6.2, mat=fig)
    fig_obj.hide_render = True

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.45, -0.70, 0.55)).to_track_quat("Z", "Y").to_euler()
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

    def show(variant):
        for v in VARIANTS:
            for o in variant_parts(v):
                o.hide_render = v != variant
        hills[0.0].hide_render = variant != "hillside"

    def shoot(name, eye, target, lens=32, size=(1600, 1000), ortho=None):
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
        print(f"{NAME}: rendered {scene.render.filepath}")

    # the photo from the driveway side of the street, where its camera stood:
    # the gable end foreshortened on the left, the door side on the right
    show("photo")
    shoot("photo_three_quarter", (11.5, -11.0, 2.0), (0.6, -0.8, 4.0), lens=28)
    shoot("photo_front_elevation", (0.0, -40.0, 4.2), (0.0, 0.0, 4.2), ortho=12.0)
    shoot("photo_side_elevation", (40.0, 0.0, 4.2), (0.0, 0.0, 4.2), ortho=18.0)
    shoot("photo_rear_three_quarter", (-10.0, 15.0, 1.7), (-0.5, 2.5, 4.0), lens=30)
    fig_obj.hide_render = False
    shoot("photo_with_figure", (11.0, -12.0, 1.7), (1.0, -3.0, 3.2), lens=30)
    fig_obj.hide_render = True
    show("plain")
    shoot("plain_three_quarter", (11.5, -11.0, 2.0), (0.6, -0.8, 4.0), lens=28)
    shoot("plain_front_elevation", (0.0, -40.0, 4.2), (0.0, 0.0, 4.2), ortho=12.0)
    show("hillside")
    shoot("hillside_three_quarter", (11.5, -11.0, 2.0), (0.6, -0.8, 4.0), lens=28)
    shoot("hillside_rear_three_quarter", (-10.0, 16.0, 6.0), (0.3, 3.5, 4.5), lens=30)
    shoot("hillside_side_elevation", (40.0, 1.0, 4.2), (0.0, 1.0, 4.2), ortho=20.0)
    # the stilts from the street corner, from the beach below its front deck,
    # the stair side-on from the ground beside it (air under the flights),
    # and with the figure under the deck's edge for the clearance
    show("stilts")
    shoot("stilts_three_quarter", (13.0, -13.0, 2.2), (0.8, -1.5, 4.6), lens=28)
    shoot("stilts_from_beach", (-7.5, -18.0, 0.9), (0.5, -2.5, 4.6), lens=26)
    shoot("stilts_stair_side", (15.0, -3.1, 1.0), (4.7, -3.1, 1.5), lens=30)
    fig_obj.location = (3.6, -8.6, 0.0)
    fig_obj.hide_render = False
    shoot("stilts_with_figure", (12.0, -14.0, 1.7), (1.0, -4.0, 3.8), lens=30)
    fig_obj.hide_render = True
    fig_obj.location = (3.9, -6.2, 0.0)
    # all four on neighbouring lots: the others moved over for the shot only
    lots = ("photo", "plain", "hillside", "stilts")
    for k, v in enumerate(lots):
        for o in variant_parts(v):
            o.location.x += k * LOT_W
            o.hide_render = False
    hills[0.0].hide_render = True
    hills[2 * LOT_W].hide_render = False
    for d in drives:
        d.hide_render = True
    shoot("four_up_lots", (13.5, -42.0, 2.0), (13.5, -1.0, 4.6), lens=26, size=(2400, 900))
    for k, v in enumerate(lots):
        for o in variant_parts(v):
            o.location.x -= k * LOT_W


# --- main ------------------------------------------------------------------------

def layer_collection(name, root=None):
    """The view layer's entry for a collection, whose `hide_viewport` is its eye."""
    root = root or bpy.context.view_layer.layer_collection
    if root.name == name:
        return root
    for child in root.children:
        found = layer_collection(name, child)
        if found:
            return found
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != NAME:
        raise SystemExit(f"{NAME}: open {NAME}.blend, not {name}")
    export, reference = (bpy.data.collections[n] for n in ("export", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"{NAME}: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    build_variant(VARIANTS[0], export)
    for v in VARIANTS[1:]:
        sub = bpy.data.collections.new(f"variant_{v}")
        export.children.link(sub)
        build_variant(v, sub)
    bpy.context.view_layer.update()
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True
    build_reference(reference)

    for v in VARIANTS:
        report(variant_parts(v), f"{v} ({'export' if v == VARIANTS[0] else 'export/variant_' + v})")
    print(f"{NAME}: body {W:.1f} x {D:.1f} m, walls {T:.2f} m, pitch {PITCH_DEG:.0f} deg; lower storey {LOWER:.2f} to the belt, "
          f"knee {KNEE:.2f}, eave {EAVE:.2f}, ridge top {RIDGE_TOP:.2f}; carriage doors {CARRIAGE_X[1] - CARRIAGE_X[0]:.2f} x {CARRIAGE_H:.2f}; "
          f"balcony {2 * BAL_HALF:.1f} x {BAL_D:.2f} m at {LOWER:.2f}; cross-gable {2 * DORMER_HALF:.1f} m at y {DORMER_YC:.2f}; "
          f"plain balcony {2 * PLAIN_BAL_HALF:.1f} x {PLAIN_BAL_D:.2f}; hillside slope {HILL_SLOPE * 100:.1f} %, pad {PAD_Z:.2f}, "
          f"deck {DECK_X[1] - DECK_X[0]:.1f} x {DECK_D:.1f}; stilts floor {ST_FLOOR:.2f}, storey {ST_STOREY:.2f}, eave {ST_EAVE:.2f}, "
          f"ridge top {ST_RIDGE_TOP:.2f}, front deck {ST_FRONT_DECK:.1f} m, side deck {ST_SIDE_DECK:.1f} m, "
          f"middle landing {ST_MID_Z:.2f}")
    for v in VARIANTS:
        pairs = coplanar_pairs(variant_parts(v))
        print(f"{NAME}: {v}: {len(pairs)} coplanar overlapping face pairs" +
              ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{NAME}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1])


main()
