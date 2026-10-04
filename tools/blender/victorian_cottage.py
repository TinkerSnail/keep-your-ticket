"""The beach town's Victorian worker's cottage, blocked out (2026-10-02):
two storeys, gable to the street, on a 9 m lot with a side driveway, in two
variants from Christina's photographs (`documentation/reference/houses/`).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/victorian_cottage.blend --python tools/blender/victorian_cottage.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, one shell in four `kyt_variant`s that stand
at the origin together, as the park lamp's three do (`plaza_street.py`):
`blue` in `export` itself and `purple`, `blue_b` and `purple_b` each in
`export/variant_<name>` with its eye shut (Send writes one prop per variant;
Check and the handback render show the first). The `_b` pair (2026-10-03)
are Christina's "this AND that": the alternatives the first pass asked about,
built as variants with `blue` and `purple` left exactly as they were.
`blue_b` is the blue with the glazed porch wrapping the corner under an
L-shaped lean-to tucked under the main eave, a side door and landing on the
driveway side instead of the back stoop, and a brick chimney. `purple_b` is
the purple at a lower pitch over a knee wall, so the upstairs windows straddle
the eave as its photo's do and the peak ornament has room, its porch railed,
and a brick chimney. Into the locked `reference` go the lot and footprint outlines, a
1.7 m figure and the `ground_line` marker Check reads (the walls reach below
z = 0 on purpose). Everything the tool makes carries `kyt_victorian_cottage`,
so a rerun removes and rebuilds its own work and keeps anything of hers;
`export` holding anything untagged refuses without `--replace`.

**Frame.** Real metres, Z up, the street-side ground at z = 0, the origin at
the body's footprint centre. The front (gable, porch, door) faces -Y here,
which the glTF export (`send.py`, `export_yup=True`) turns into Godot's +Z.
+X is the viewer's right from the street: the driveway side.

**Contract** (enclosing, as the beach cottage): public faces, porches and
windows, no interior. Every opening is a real hole through a wall of real
thickness; the door and the panes are solid slabs set in the holes. Every
door's sill stands THRESHOLD over the deck it opens onto, flush for the
player. The decks are walkable from their steps, and the steps follow the
park's stair rule: a narrow ramp is the floor, the treads are scenery showing
past it and do not collide (`kyt_collision = none`). No two shapes share a
plane: a part that meets another laps into it or stands proud of it, and the
tool's own scan (`coplanar_pairs`) reports any pair that does.

**What the photographs say.** `victorian_blue_cottage.webp`: a tall narrow
gable, steeper than 45 degrees, the balcony's floor on the eave line (so the
upstairs floor is the eave and the upstairs is in the gable), a triple
window over the balcony, a sunburst at the peak between bargeboards with a
red inner band, the main floor about ten risers over the driveway, the stair
straight down from the door, the glazed porch at the right-front corner with
its own small gable tucked under the main eave, the entry landing open under
the balcony. `purple_painted_lady.png`: the same bones three risers up, the
porch the house's width on turned posts with a shed roof under the eave,
paired upstairs windows with pointed hoods tight under the rakes, a
spindle-work fan in the peak, a door at the left and a window at the right.
Both read in silhouette and chunky trim, so that is what is built:
bargeboards, the fan, brackets, posts, railings, hoods. Board-and-batten,
lap siding, divided lights and the sawn ornament are left to painting.

**Choices to state.** The body is W = 6.0 m across by D = 10.5 m deep: the
blue photo's front is about seven doors wide and the lot leaves 2.4 m for
the driveway beside a 6.0 m body plus eaves. One pitch serves both, 48
degrees; the blue reads a little steeper, the purple a little flatter.
Floor to eave is 3.0 m, the upstairs floor is the eave. The blue's main
floor is 1.55 m up (ten risers), the purple's 0.60 m (four). Colours are
flat stand-ins named `victorian_cottage_<variant>_<surface>` for the
painting to replace.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_victorian_cottage"
NAME = "victorian_cottage"

# --- the shell, both variants ----------------------------------------------
W, D = 6.0, 10.5           # the body: across the front, and deep
T = 0.20                   # wall thickness
STOREY = 3.0               # the floor to the eave; the upstairs floor is the eave
PITCH_DEG = 48.0           # the gable, between the two photographs
PITCH = math.radians(PITCH_DEG)
TAN = math.tan(PITCH)
RISE = (W / 2) * TAN       # the ridge over the eave
ROOF_T = 0.20              # the roof slab, perpendicular to its slope
ROOF_VT = ROOF_T / math.cos(PITCH)
EAVE_OVER, RAKE_OVER = 0.40, 0.50
WALL_TOP_IN = 0.28         # the side walls end this far over the eave, inside the slab
LIFT = 0.03                # a gable wall's top, this far inside the slab
CORNER, PROUD = 0.26, 0.04  # the corner boards, 4 cm proud of the walls
E_IN = CORNER / 2 - PROUD  # the walls stop this short of the corners, under the boards
BELOW = 0.05               # the end walls' feet under the ground (sides 1 cm lower, boards 3)
DOOR_H = 2.30
SILL, HEAD = 0.80, 2.30    # the main storey's windows over the floor
UP_SILL, UP_HEAD = 0.70, 2.00   # the gable windows over the upstairs floor
THRESHOLD = 0.01           # a door's sill over the deck outside it (the door is shut)
RISER_ABOUT, GOING = 0.155, 0.28
RAIL_H = 0.90
POST = 0.14                # newels
BARGE_H, BARGE_T, BARGE_BAND = 0.28, 0.06, 0.10
BAND_H = 0.15              # the water-table band at the floor line
SIDE_WINDOWS = (-3.5, 0.0, 3.5)   # centres along each side, SIDE_WIN_W wide
SIDE_WIN_W = 1.0
BACK_WINDOW_X = (-2.2, -1.0)
BACK_DOOR_X = (0.45, 1.40)
BACK_UP_WINDOW_X = (-0.5, 0.5)
STOOP_D, STOOP_X = 1.20, (0.15, 1.70)   # the back landing: deep, and its x range
STAIR_W = 1.10

# --- blue --------------------------------------------------------------------
B_FLOOR = 1.55             # ten risers over the driveway
B_DOOR_X = (-0.60, 0.35)
B_WINDOW_X = (-2.40, -1.00)
B_UP_WINDOW_X = (-0.80, 0.80)   # the triple window over the balcony
B_LANDING_D = 1.30         # the entry landing, open under the balcony
B_BALCONY_HW, B_BALCONY_D = 1.9, 0.75
B_BRACKETS_X = (-1.6, 0.0, 1.6)
B_PORCH_X0 = 0.90          # the glazed corner porch's left face
B_PORCH_PROUD = 0.07       # its right face past the body's corner board
B_PORCH_D = 1.25           # how far it stands in front of the body
B_PORCH_T = 0.15
B_PORCH_EAVE = 2.35        # over the floor
B_PORCH_PITCH = math.radians(38)
B_PORCH_ROOF_T = 0.15
B_PORCH_POST = 0.20
B_PORCH_GLASS = (0.85, 2.15)    # the glass band over the floor
B_FAN_R = 0.42             # the sunburst at the peak
B_FAN_Z = 2.30             # its centre over the eave
B_HOOD_H = 0.10            # the red hoods over the main-floor openings

# --- purple ------------------------------------------------------------------
P_FLOOR = 0.60             # four risers
P_DOOR_X = (-2.35, -1.40)
P_WINDOW_X = (0.30, 1.80)
P_UP_WINDOWS_X = ((-0.90, -0.25), (0.25, 0.90))
P_UP_HEAD = 1.95           # a little under UP_HEAD, for the hoods under the rakes
P_PORCH_D = 2.30           # the full-width porch
P_DECK_OVER = 0.15         # the deck past the body each side
P_ROOF_OVER = 0.02         # the porch roof past the body each side, under the eave
P_POSTS_X = (-2.85, -0.95, 0.95, 2.85)
P_POST_R = 0.08            # the turned shaft
P_POST_BLOCK = 0.22        # its base and capital
P_BEAM_Z = (2.22, 2.40)    # the porch beam over the floor
P_ROOF_UNDER = (2.75, 2.40)    # the shed roof's underside over the floor: at the wall, at the front
P_ROOF_T = 0.16
P_STEP_X = (-2.50, -1.25)
P_BAR_Z = (2.47, 2.55)     # the spindle bar over the eave
P_FAN_R = 0.28
P_SPINDLES_X = (-0.40, -0.20, 0.0, 0.20, 0.40)
P_SPINDLE_L = 0.20
P_HOOD_H = 0.30            # the pointed hoods over the upstairs windows

# --- blue_b: the blue with the porch round the corner, a side door, a chimney --
BB_WRAP = 1.0              # the porch past the body's right wall
BB_SIDE_D = 2.6            # how far it runs back along the side from the front wall
BB_PORCH_EAVE = 2.20       # over the floor: the lean-to's eave, under the main eave
BB_PORCH_SLOPE = 0.15      # the lean-to's rise per metre toward the body
BB_PORCH_ROOF_T = 0.16     # vertical
BB_PORCH_ROOF_OVER = 0.25
BB_ROOF_LAP = 0.05         # the lean-to's inner edges this far inside the body's walls
BB_PORCH_GLASS = (0.85, 2.00)
BB_SIDE_DOOR_Y = (1.00, 1.95)   # on the driveway side, between the side windows
BB_SIDE_DECK_Y = (0.60, 2.30)   # the side landing's y range
BB_SIDE_DECK_W = 1.35      # how far it stands out from the wall

# --- purple_b: the purple at a lower pitch over a knee wall, railed, a chimney --
PB_PITCH_DEG = 38.0
PB_KNEE = 1.20             # the side walls rise this far over the upstairs floor
PB_WALL_TOP_IN = 0.20      # the side walls end this far over the eave, inside the flatter slab
PB_BAR_Z = (1.45, 1.53)    # the spindle bar over the eave
PB_FAN_R = 0.50
PB_SPINDLES_X = (-0.60, -0.40, -0.20, 0.0, 0.20, 0.40, 0.60)
PB_SPINDLE_L = 0.25

# --- the chimney (blue_b, purple_b) ------------------------------------------------
CHIMNEY = (0.60, 1.20, 0.60, 0.90)   # x0, y0, across, deep: through the east slope near the ridge
CHIMNEY_OVER = 0.70        # its top over the ridge cap

LOT_W, LOT_X0, LOT_Y = 9.0, -3.6, (-16.0, 14.0)   # the lot: 9 m wide, the kerb to the back fence

PALETTES = {
    "blue": dict(walls="a9c4d3", base="8aa7ba", trim="f6f3ec", accent="b5202c", frames="f6f3ec",
                 door="b5202c", deck="7d8a94", roof="6b6f66", glass="3e5566"),
    "purple": dict(walls="5b2e9e", base="4a2480", trim="1e8a7c", accent="c2298e", frames="d8a62a",
                   door="6a1a3a", deck="8a7a6a", roof="4a4a4c", glass="3e5566"),
}
# the b pair in their own colours (Christina, 3 Oct 2026: "on the variations
# lets change the colors", "can the doors be different colors too"): sage,
# cream and deep red with a navy door; pink, teal and gold with a sunflower door
PALETTES["blue_b"] = dict(walls="a3b899", base="86997f", trim="f3ead6", accent="8e1f24", frames="f3ead6",
                          door="1f2f5a", deck="7d8a94", roof="6b6f66", glass="3e5566", brick="8a4a3a")
PALETTES["purple_b"] = dict(walls="e8559a", base="c43f80", trim="1e8a7c", accent="d8a62a", frames="d8a62a",
                            door="f2b705", deck="8a7a6a", roof="4a4a4c", glass="3e5566", brick="7a3f36")
VARIANTS = ("blue", "purple", "blue_b", "purple_b")


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


def octagon(cx, cy, r):
    return [(cx + r * math.cos(math.tau * (k + 0.5) / 8), cy + r * math.sin(math.tau * (k + 0.5) / 8)) for k in range(8)]


class Top:
    """A wall's top edge: flat, or a gable following the roof's underside
    LIFT higher (inside the slab, so the two never share a plane)."""

    def __init__(self, flat=None, gable=None):
        self.flat = flat
        self.gable = gable      # (u of the ridge, half span, eave z, tan of the pitch)

    def z(self, u):
        if self.gable is None:
            return self.flat
        ridge_u, half, eave, tan = self.gable
        return eave + (half - abs(u - ridge_u)) * tan + LIFT

    def apex(self):
        ridge_u, half, eave, tan = self.gable
        return eave + half * tan + LIFT


class Kit:
    """One variant's parts: every maker here names, tags and colours for it."""

    def __init__(self, variant, coll, pitch_deg=PITCH_DEG, knee=0.0, wall_top_in=WALL_TOP_IN):
        self.v = variant
        self.coll = coll
        self.m = {k: material(f"{NAME}_{variant}_{k}", srgb(hex6)) for k, hex6 in PALETTES[variant].items()}
        self.pitch = math.radians(pitch_deg)
        self.tan = math.tan(self.pitch)
        self.rise = (W / 2) * self.tan
        self.roof_vt = ROOF_T / math.cos(self.pitch)
        self.knee = knee                  # the side walls over the upstairs floor
        self.wall_top_in = wall_top_in

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

    # -- walls --

    def wall(self, part, origin, u_dir, v_dir, length, thick, z0, top, openings, base_below, mats):
        """One wall as a closed shell: two skins, ends, bottom, top, and a real
        reveal round every opening. `origin` is the outer face's start,
        `u_dir` runs along it, `v_dir` into the wall. An opening is
        (u0, u1, z0, z1), anywhere under the top, the gable included: the
        wall is a grid of cells between the opening lines, each cell clipped
        by the roof line, and a cell's edge gets a side face wherever its
        neighbour is an opening, the outside or the sky. Faces below
        `base_below` take the second material (the base)."""
        O, U, V = Vector(origin), Vector(u_dir), Vector(v_dir)
        us, zs = {0.0, length}, {z0}
        for u0, u1, oz0, oz1 in openings:
            assert 0.0 < u0 < u1 < length and z0 < oz0 < oz1, (part, u0, u1, oz0, oz1)
            if top.gable is None:
                assert oz1 <= top.flat - 0.05, (part, "an opening through the top", oz1, top.flat)
            else:
                assert oz1 + 0.03 <= min(top.z(u0), top.z(u1)), (part, "an opening through the gable", u0, u1, oz1)
            us.update((u0, u1))
            zs.update((oz0, oz1))
        if top.gable is None:
            zs.add(top.flat)
        else:
            if 0.0 < top.gable[0] < length:
                us.add(top.gable[0])
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
            return 1 if zm < base_below else 0

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

    def shell(self, prefix, x0, x1, y0, y1, thick, e, feet, tops, openings, mats, base_below, which=("front", "back", "west", "east")):
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
        for key in which:
            origin, u_dir, v_dir, length, to_u = spec[key]
            ops = []
            for a0, a1, z0, z1 in openings.get(key, ()):
                ua, ub = sorted((to_u(a0), to_u(a1)))
                ops.append((ua, ub, z0, z1))
            self.wall(f"{prefix}wall_{key}", origin, u_dir, v_dir, length, thick, feet[key], tops[key], ops,
                      base_below, mats)

    def corner_boards(self, prefix, mat, x0, x1, y0, y1, size, proud, z0, z1, which=("sw", "se", "nw", "ne")):
        """Corner boards `proud` of both faces, their feet and tops past the walls'."""
        for sx, sy, tag in ((-1, -1, "sw"), (1, -1, "se"), (-1, 1, "nw"), (1, 1, "ne")):
            if tag not in which:
                continue
            cx = (x0 - proud + size / 2) if sx < 0 else (x1 + proud - size / 2)
            cy = (y0 - proud + size / 2) if sy < 0 else (y1 + proud - size / 2)
            self.box(f"{prefix}corner_{tag}", mat, cx - size / 2, cx + size / 2, cy - size / 2, cy + size / 2, z0, z1)

    def gable_roof(self, part, mat, xc, half, eave, tan, over, thick, y0, y1):
        """A gable roof as one piece: an inverted V of `thick` perpendicular
        thickness whose underside passes through z = eave at x = xc +- half
        and peaks over xc, extruded from rake to rake."""
        vt = thick / math.cos(math.atan(tan))

        def under(x):
            return eave + (half - abs(x - xc)) * tan
        xe = half + over
        section = [(xc - xe, under(xc - xe)), (xc, under(xc)), (xc + xe, under(xc + xe)),
                   (xc + xe, under(xc + xe) + vt), (xc, under(xc) + vt), (xc - xe, under(xc - xe) + vt)]
        return self.prism(part, mat, section, "y", y0, y1)

    def l_roof(self, part, mat, x_in, x_out, y_in, y_out, y_back, z_e, slope, thick):
        """A lean-to round a corner as one mesh: a front slope rising from the
        eave at `y_out` toward the body and a side slope rising from `x_out`
        toward the body's side, meeting on a 45-degree hip that is a crease
        of the mesh; the inner edges at `x_in` and `y_in` are inside the
        body's walls. `thick` is vertical."""
        def z_front(y):
            return z_e + (y - y_out) * slope

        def z_side(x):
            return z_e + (x_out - x) * slope
        # the hip from the outer corner reaches the body's front wall plane here
        x_c = x_out - (y_in - y_out)
        A, B, C, D = (x_in - 0.0, y_out), (x_out, y_out), (x_c, y_in), (x_in, y_in)
        E, F, G = (x_out, y_back), (x_in, y_back), (x_in, y_in)
        bm = bmesh.new()

        def pair(x, y, z):
            return bm.verts.new((x, y, z)), bm.verts.new((x, y, z - thick))
        a, b, c, d = pair(*A, z_front(A[1])), pair(*B, z_e), pair(*C, z_front(C[1])), pair(*D, z_front(D[1]))
        e, f, g = pair(*E, z_e), pair(*F, z_side(F[0])), pair(*G, z_side(G[0]))
        bm.faces.new((a[0], b[0], c[0], d[0]))
        bm.faces.new((b[0], e[0], f[0], g[0], c[0]))
        bm.faces.new((d[1], c[1], b[1], a[1]))
        bm.faces.new((c[1], g[1], f[1], e[1], b[1]))
        for p, q in ((a, b), (b, e), (e, f), (f, g), (g, c), (c, d), (d, a)):
            bm.faces.new((p[0], q[0], q[1], p[1]))
        return self.finish(part, bm, [mat])

    def bargeboard(self, part, mat, xc, half, eave, tan, over, thick_vt, y_rake, out, height, proud, lap, under_off=0.0, end_in=0.0):
        """A chevron board on a gable's rake face: its back `lap` inside the
        roof slab's end, its top 2 cm under the slab's top, `height` tall
        under that. `out` is -1 at the front, +1 at the back. `under_off`
        drops it (the inner band hangs under the main board)."""
        def under(x):
            return eave + (half - abs(x - xc)) * tan
        xe = half + over + 0.05 - end_in
        zt = thick_vt - 0.02 - under_off
        section = [(xc - xe, under(xc - xe) + zt - height), (xc, under(xc) + zt - height), (xc + xe, under(xc + xe) + zt - height),
                   (xc + xe, under(xc + xe) + zt), (xc, under(xc) + zt), (xc - xe, under(xc - xe) + zt)]
        lo, hi = sorted((y_rake - out * lap, y_rake + out * proud))
        return self.prism(part, mat, section, "y", lo, hi, collide=False)

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

    def mullions(self, prefix, mat, axis, face_at, outward, a0, a1, z0, z1, lights):
        """Chunky mullions dividing an opening into `lights`, 3.5 cm proud
        and lapped 2 cm into the pane behind."""
        lo, hi = sorted((face_at - 0.10 * outward, face_at + 0.035 * outward))
        for m in range(1, lights):
            a = a0 + (a1 - a0) * m / lights
            if axis == "x":
                self.box(f"{prefix}_mullion{m}", mat, a - 0.05, a + 0.05, lo, hi, z0 - 0.01, z1 + 0.01, collide=False)
            else:
                self.box(f"{prefix}_mullion{m}", mat, lo, hi, a - 0.05, a + 0.05, z0 - 0.01, z1 + 0.01, collide=False)

    def hood(self, prefix, mat, axis, face_at, outward, a0, a1, z_head, tall, proud=0.06):
        """A flat hood board over a head casing, lapped 2 cm into its top."""
        lo, hi = sorted((face_at + 0.02 * outward, face_at - proud * outward))
        z0, z1 = z_head + 0.12 - 0.02, z_head + 0.12 - 0.02 + tall
        if axis == "x":
            self.box(f"{prefix}_hood", mat, a0 - 0.15, a1 + 0.15, lo, hi, z0, z1, collide=False)
        else:
            self.box(f"{prefix}_hood", mat, lo, hi, a0 - 0.15, a1 + 0.15, z0, z1, collide=False)

    def pointed_hood(self, prefix, mat, face_y, a0, a1, z_head, tall):
        """A pointed pediment over a front-wall window: a triangle on the
        head casing's width, lapped 2 cm into the casing's top, 5 cm proud."""
        base = z_head + 0.12 - 0.02
        poly = [(a0 - 0.12, base), (a1 + 0.12, base), ((a0 + a1) / 2, base + tall)]
        self.prism(f"{prefix}_pediment", mat, poly, "y", face_y - 0.05, face_y + 0.02, collide=False)

    # -- decks, rails, stairs --

    def newel(self, part, mat, x0, y0, z_floor):
        """A newel: the post 2 cm into the deck, a square cap and a turned ball."""
        z1 = z_floor + RAIL_H + 0.12
        self.box(f"{part}_post", mat, x0, x0 + POST, y0, y0 + POST, z_floor - 0.02, z1)
        self.box(f"{part}_cap", mat, x0 - 0.02, x0 + POST + 0.02, y0 - 0.02, y0 + POST + 0.02, z1 - 0.02, z1 + 0.04, collide=False)
        self.prism(f"{part}_ball", mat, octagon(x0 + POST / 2, y0 + POST / 2, 0.065), "z", z1 + 0.03, z1 + 0.16, collide=False)

    def lattice_rail(self, prefix, mat, axis, at, a0, a1, z_floor):
        """The photo's geometric railing: top and bottom rails between the
        newels (a0..a1 already lap 2 cm into them), a mid bar, a full
        upright at each panel division and two short ones over the mid bar
        in each panel. Thicknesses all differ, so the crossing bars share no
        plane."""
        def b(name, p0, p1, q0, q1, z0, z1, collide=True):
            if axis == "x":
                self.box(name, mat, p0, p1, q0, q1, z0, z1, collide=collide)
            else:
                self.box(name, mat, q0, q1, p0, p1, z0, z1, collide=collide)
        top0, top1 = z_floor + RAIL_H - 0.08, z_floor + RAIL_H
        bot0, bot1 = z_floor + 0.08, z_floor + 0.14
        b(f"{prefix}_top", a0, a1, at - 0.04, at + 0.04, top0, top1)
        b(f"{prefix}_bottom", a0, a1, at - 0.035, at + 0.035, bot0, bot1)
        mid = z_floor + 0.50
        b(f"{prefix}_mid", a0 + 0.01, a1 - 0.01, at - 0.02, at + 0.02, mid - 0.025, mid + 0.025, collide=False)
        panels = max(1, round((a1 - a0) / 0.9))
        pitch = (a1 - a0) / panels
        for k in range(1, panels):
            a = a0 + k * pitch
            b(f"{prefix}_up{k}", a - 0.03, a + 0.03, at - 0.03, at + 0.03, bot1 - 0.02, top0 + 0.02)
        for k in range(panels):
            for m, frac in enumerate((1 / 3, 2 / 3)):
                a = a0 + (k + frac) * pitch
                b(f"{prefix}_bar{k}{m}", a - 0.025, a + 0.025, at - 0.015, at + 0.015, mid + 0.005, top0 + 0.02, collide=False)

    def panel_rail(self, prefix, mat, axis, at, a0, a1, z_floor, panel=0.06, cap=0.12):
        """A plain deck rail as a solid panel with a cap (the back stoop's):
        the panel's foot 1.5 cm into the deck, its ends lapping the posts."""
        z0, z1 = z_floor - 0.015, z_floor + RAIL_H
        if axis == "x":
            self.box(f"{prefix}_panel", mat, a0, a1, at - panel / 2, at + panel / 2, z0, z1)
            self.box(f"{prefix}_cap", mat, a0 + 0.015, a1 - 0.015, at - cap / 2, at + cap / 2, z1 - 0.03, z1 + 0.05, collide=False)
        else:
            self.box(f"{prefix}_panel", mat, at - panel / 2, at + panel / 2, a0, a1, z0, z1)
            self.box(f"{prefix}_cap", mat, at - cap / 2, at + cap / 2, a0 + 0.015, a1 - 0.015, z1 - 0.03, z1 + 0.05, collide=False)

    def stair(self, prefix, mat, x0, x1, y_edge, out, z_top):
        """A straight flight down from a deck's edge at `y_edge`, outward in
        `out` (-1 toward the street): the treads one stepped block, scenery
        (no collision), lapping 2 cm into the deck; the narrow ramp on the
        nosing line is the floor, flush with the deck's edge and ending
        inside the deck, its foot 2 cm below the treads' so the two share no
        plane; nosing strips 3 cm proud of the ramp. Returns (n, riser)."""
        n = max(1, round(z_top / RISER_ABOUT))
        riser = z_top / n

        def y(s):
            return y_edge + out * s
        profile = [(y(n * GOING), -BELOW)]
        for k in range(1, n):
            profile += [(y(n * GOING - (k - 1) * GOING), k * riser), (y(n * GOING - k * GOING), k * riser)]
        profile += [(y(-0.02), (n - 1) * riser), (y(-0.02), -BELOW)]
        self.prism(f"{prefix}_treads", mat, profile, "x", x0, x1, collide=False)
        ramp = [(y(n * GOING + 0.05), -BELOW - 0.02), (y(n * GOING), 0.0), (y(0.0), z_top), (y(-0.06), -BELOW - 0.02)]
        self.prism(f"{prefix}_ramp", mat, ramp, "x", x0 + 0.10, x1 - 0.10)
        for k in range(1, n):
            nose = n * GOING - (k - 1) * GOING
            ya, yb = sorted((y(nose + 0.01), y(nose - 0.05)))
            self.box(f"{prefix}_nosing_{k}", mat, x0 + 0.005, x1 - 0.005, ya, yb, k * riser - 0.01, k * riser + 0.03, collide=False)
        return n, riser

    def stair_rail(self, prefix, mat, x_at, y_edge, out, z_top, n, riser, newels=True):
        """A sloped rail beside a flight: a top newel on the deck, a bottom
        newel on the ground, a top rail and a bottom rail as parallelograms
        on the nosing line's slope, uprights on alternate treads."""
        slope = riser / GOING

        def y(s):
            return y_edge + out * s

        def zline(s):
            return z_top - s * slope
        if newels:
            ya, yb = sorted((y(-0.03), y(-0.03 - POST)))
            self.newel(f"{prefix}_newel_top", mat, x_at - POST / 2, ya, z_top)
            ya, yb = sorted((y(n * GOING + 0.03), y(n * GOING + 0.03 + POST)))
            self.newel(f"{prefix}_newel_foot", mat, x_at - POST / 2, ya, 0.02)
        sa, sb = -POST - 0.01, n * GOING + 0.05
        for name, lo, hi, half in (("top", RAIL_H - 0.08, RAIL_H, 0.04), ("bottom", 0.12, 0.18, 0.035)):
            poly = [(y(sa), zline(sa) + lo), (y(sb), zline(sb) + lo), (y(sb), zline(sb) + hi), (y(sa), zline(sa) + hi)]
            self.prism(f"{prefix}_{name}", mat, poly, "x", x_at - half, x_at + half)
        for m in range(1, n + 1, 2 if n > 4 else 1):
            s = (m - 0.5) * GOING
            tread_z = (n - m) * riser
            ya, yb = sorted((y(s - 0.03), y(s + 0.03)))
            self.box(f"{prefix}_up{m}", mat, x_at - 0.03, x_at + 0.03, ya, yb, tread_z - 0.02, zline(s) + RAIL_H - 0.06)

    def skirt(self, part, mat, x0, x1, y0, y1, z_deck):
        """The solid base under a deck, 10 cm under the ground, its top inside the deck."""
        self.box(part, mat, x0, x1, y0, y1, -0.10, z_deck - 0.18)

    # -- ornament --

    def half_disc(self, part, mat, xc, zc, r, y_lo, y_hi, segments=12, collide=False):
        pts = [(xc + r * math.cos(math.pi * k / segments), zc + r * math.sin(math.pi * k / segments)) for k in range(segments + 1)]
        return self.prism(part, mat, pts, "y", y_lo, y_hi, collide=collide)

    def rays(self, prefix, mat, xc, zc, r0, r1, width, angles, y_lo, y_hi, stagger=0.004):
        """Radiating boards from (xc, zc) between radii r0 and r1, as prisms
        in the gable's plane, so nothing is rotated."""
        for k, deg in enumerate(angles):
            a = math.radians(deg)
            dx, dz = math.cos(a), math.sin(a)
            px, pz = -dz * width / 2, dx * width / 2
            poly = [(xc + dx * r0 + px, zc + dz * r0 + pz), (xc + dx * r0 - px, zc + dz * r0 - pz),
                    (xc + dx * r1 - px, zc + dz * r1 - pz), (xc + dx * r1 + px, zc + dz * r1 + pz)]
            dy = -stagger if k % 2 else 0.0
            self.prism(f"{prefix}_ray{k}", mat, poly, "y", y_lo + dy, y_hi + dy, collide=False)

    def bracket(self, part, mat, x0, x1, y_wall, out, z_top, depth, drop, lap=0.03):
        """A knee bracket under something that projects from a wall: a right
        triangle, its back `lap` into the wall, its top lapped 2 cm into the
        thing it carries."""
        yb = y_wall - out * lap          # inside the wall
        yf = y_wall + out * depth
        poly = [(yb, z_top), (yf, z_top), (yb, z_top - drop)]
        self.prism(part, mat, poly, "x", x0, x1, collide=False)


# --- the house -----------------------------------------------------------------

def body_openings(kit, floor, front, side_door=None, back_door=True):
    """The shared side and back openings plus the variant's front ones; a
    side door on the driveway side (its y range) in place of the back one."""
    sill, head = floor + SILL, floor + HEAD
    up = floor + STOREY                   # the upstairs floor
    sides = [(c - SIDE_WIN_W / 2, c + SIDE_WIN_W / 2, sill, head) for c in SIDE_WINDOWS]
    back = [(*BACK_WINDOW_X, sill, head)]
    if back_door:
        back.append((*BACK_DOOR_X, floor + THRESHOLD, floor + DOOR_H))
    back.append((*BACK_UP_WINDOW_X, up + UP_SILL, up + UP_HEAD - 0.2))
    east = list(sides)
    if side_door:
        east.append((*side_door, floor + THRESHOLD, floor + DOOR_H))
    return {"front": front, "back": back, "west": sides, "east": east}


def build_body(kit, floor, openings, kinds):
    """The body: four walls with gables front and back, corner boards, the
    gable roof and its ridge cap, casings and panes. `kinds` names the
    openings that are doors, as (face, index)."""
    hw, hd, e = W / 2, D / 2, E_IN
    eave = floor + STOREY + kit.knee
    wall_top = eave + kit.wall_top_in
    gable = Top(gable=(hw - e, hw, eave, kit.tan))
    flat = Top(flat=wall_top)
    feet = {"front": -BELOW, "back": -BELOW, "west": -BELOW - 0.01, "east": -BELOW - 0.01}
    kit.shell("", -hw, hw, -hd, hd, T, e, feet, {"front": gable, "back": gable, "west": flat, "east": flat},
              openings, [kit.m["walls"], kit.m["base"]], floor)
    kit.corner_boards("", kit.m["trim"], -hw, hw, -hd, hd, CORNER, PROUD, -BELOW - 0.03, wall_top + 0.02)
    y0, y1 = -hd - RAKE_OVER, hd + RAKE_OVER
    kit.gable_roof("roof", kit.m["roof"], 0.0, hw, eave, kit.tan, EAVE_OVER, ROOF_T, y0, y1)
    rt = eave + kit.rise + kit.roof_vt
    kit.box("ridge_cap", kit.m["roof"], -0.20, 0.20, y0 - 0.02, y1 + 0.02, rt - 0.10, rt + 0.05, collide=False)
    # bargeboards on both rakes, a main board and an accent band under it
    for face, y_rake, out in (("front", y0, -1), ("back", y1, 1)):
        kit.bargeboard(f"barge_{face}", kit.m["trim"], 0.0, hw, eave, kit.tan, EAVE_OVER, kit.roof_vt, y_rake, out, BARGE_H, 0.06, 0.02)
        kit.bargeboard(f"barge_{face}_band", kit.m["accent"], 0.0, hw, eave, kit.tan, EAVE_OVER, kit.roof_vt, y_rake, out,
                       BARGE_BAND, 0.07, 0.01, under_off=BARGE_H - 0.02, end_in=0.03)
    # casings, panes, doors
    for face, axis, at, out in (("front", "x", -hd, -1), ("back", "x", hd, 1), ("west", "y", -hw, -1), ("east", "y", hw, 1)):
        for k, (a0, a1, z0, z1) in enumerate(openings[face]):
            is_door = (face, k) in kinds
            kit.opening_trim(f"{face}{k}_trim", kit.m["frames"], axis, at, out, a0, a1, z0, z1, sill=not is_door)
            kit.pane(f"{face}{k}_{'door' if is_door else 'pane'}", kit.m["door"] if is_door else kit.m["glass"],
                     axis, at, out, a0, a1, z0, z1)


def build_back_stoop(kit, floor):
    """The back door's landing and straight flight, with plain panel rails."""
    hd = D / 2
    deck, trim = kit.m["deck"], kit.m["trim"]
    x0, x1 = STOOP_X
    y_edge = hd + STOOP_D
    kit.box("stoop_deck", deck, x0, x1, hd - 0.03, y_edge, floor - 0.20, floor)
    kit.skirt("stoop_skirt", kit.m["base"], x0 + 0.08, x1 - 0.08, hd - 0.04, y_edge - 0.08, floor)
    sx0, sx1 = (x0 + x1) / 2 - STAIR_W / 2, (x0 + x1) / 2 + STAIR_W / 2
    n, riser = kit.stair("stoop_stair", deck, sx0, sx1, y_edge, 1, floor)
    for tag, x_at in (("w", sx0 - 0.05), ("e", sx1 + 0.05)):
        kit.stair_rail(f"stoop_rail_{tag}", trim, x_at, y_edge, 1, floor, n, riser)
        kit.panel_rail(f"stoop_side_{tag}", trim, "y", x_at, hd + 0.05, y_edge - 0.03 - POST + 0.03, floor)


def band(kit, mat, z, segments):
    """The water-table band at the floor line, 3 cm proud, 1 cm into the
    wall, its ends inside the corner boards. `segments`: (face, a0, a1)."""
    hw, hd = W / 2, D / 2
    for k, (face, a0, a1) in enumerate(segments):
        if face in ("front", "back"):
            y = -hd if face == "front" else hd
            lo, hi = (y - 0.03, y + 0.01) if face == "front" else (y - 0.01, y + 0.03)
            kit.box(f"band_{face}{k}", mat, a0, a1, lo, hi, z - BAND_H / 2, z + BAND_H / 2, collide=False)
        else:
            x = -hw if face == "west" else hw
            lo, hi = (x - 0.03, x + 0.01) if face == "west" else (x - 0.01, x + 0.03)
            kit.box(f"band_{face}{k}", mat, lo, hi, a0, a1, z - BAND_H / 2, z + BAND_H / 2, collide=False)


BAND_END_X = W / 2 - CORNER + PROUD + 0.02   # a band's end, 2 cm inside the corner board
BAND_END_Y = D / 2 - CORNER + PROUD + 0.02


def gable_brackets(kit, mat, eave, y_face):
    """Knee brackets at the front gable's lower corners, under the rakes."""
    hw = W / 2
    for tag, sx in (("w", -1), ("e", 1)):
        xi, xo = sx * (hw - 0.45), sx * (hw - 0.07)
        poly = [(xi, eave + 0.05), (xo, eave + 0.05), (xi, eave + 0.05 + 0.38 * kit.tan)]
        kit.prism(f"gable_bracket_{tag}", mat, poly, "y", y_face - 0.05, y_face + 0.02, collide=False)


def chimney(kit, eave):
    """A brick chimney through the east slope near the ridge: the stack
    starts inside the attic and rises CHIMNEY_OVER past the ridge cap, with a
    cap a hand wider on top."""
    x0, y0, across, deep = CHIMNEY
    top = eave + kit.rise + kit.roof_vt + CHIMNEY_OVER
    kit.box("chimney", kit.m["brick"], x0, x0 + across, y0, y0 + deep, eave + 0.5, top)
    kit.box("chimney_cap", kit.m["brick"], x0 - 0.05, x0 + across + 0.05, y0 - 0.05, y0 + deep + 0.05,
            top - 0.02, top + 0.12, collide=False)


def glazed_porch(kit, floor, wrap=False):
    """The blue's glazed corner porch: walls on their own corner posts, a
    glass band in each over a solid wainscot. Plain, it stands in front of
    the body's right-front corner under a small gable to the street. With
    `wrap` (blue_b) it runs BB_WRAP past the body's right wall and BB_SIDE_D
    back along the side, under an L-shaped lean-to (`l_roof`) low enough to
    pass under the main eave at the corner, with a fourth post at its back
    corner and a back wall segment into the body's side wall."""
    hw, hd = W / 2, D / 2
    trim, glass, base = kit.m["trim"], kit.m["glass"], kit.m["base"]
    if not wrap:
        # the glazed corner porch: three walls on their own corner posts, a glass
        # band in each over a solid wainscot, a small gable to the street
        px0, px1 = B_PORCH_X0, hw + B_PORCH_PROUD
        py0 = -hd - B_PORCH_D
        pe = B_PORCH_POST / 2 - PROUD
        p_eave = floor + B_PORCH_EAVE
        p_tan = math.tan(B_PORCH_PITCH)
        p_half = (px1 - px0) / 2
        p_xc = (px0 + px1) / 2
        p_top = Top(flat=p_eave + 0.14)
        p_gable = Top(gable=(p_half - pe, p_half, p_eave, p_tan))
        g0, g1 = floor + B_PORCH_GLASS[0], floor + B_PORCH_GLASS[1]
        p_open = {
            "front": [(px0 + 0.30, px1 - 0.30, g0, g1)],
            "east": [(py0 + 0.30, -hd - 0.30, g0, g1)],
            "west": [(py0 + 0.30, py0 + 0.95, g0, g1)],
        }
        # the side walls run on 2 cm into the body's front wall; their feet differ from the body's
        kit.shell("porch_", px0, px1, py0, -hd + 0.02 + pe, B_PORCH_T, pe,
                  {"front": -BELOW + 0.005, "west": -BELOW - 0.015, "east": -BELOW - 0.015},
                  {"front": p_gable, "west": p_top, "east": p_top}, p_open,
                  [kit.m["walls"], base], floor, which=("front", "west", "east"))
        kit.corner_boards("porch_", trim, px0, px1, py0, -hd, B_PORCH_POST, PROUD, -BELOW - 0.035, p_eave + 0.16, which=("sw", "se"))
        kit.gable_roof("porch_roof", kit.m["roof"], p_xc, p_half, p_eave, p_tan, 0.25, B_PORCH_ROOF_T, py0 - 0.25, -hd + 0.045)
        p_vt = B_PORCH_ROOF_T / math.cos(B_PORCH_PITCH)
        prt = p_eave + p_half * p_tan + p_vt
        kit.box("porch_ridge_cap", kit.m["roof"], p_xc - 0.15, p_xc + 0.15, py0 - 0.27, -hd + 0.04, prt - 0.08, prt + 0.04, collide=False)
        kit.bargeboard("porch_barge", trim, p_xc, p_half, p_eave, p_tan, 0.25, p_vt, py0 - 0.25, -1, 0.20, 0.06, 0.02)
        for face, axis, at, out in (("front", "x", py0, -1), ("west", "y", px0, -1), ("east", "y", px1, 1)):
            for k, (a0, a1, z0, z1) in enumerate(p_open[face]):
                kit.opening_trim(f"porch_{face}{k}_trim", kit.m["frames"], axis, at, out, a0, a1, z0, z1)
                kit.pane(f"porch_{face}{k}_pane", glass, axis, at, out, a0, a1, z0, z1)
                kit.mullions(f"porch_{face}{k}", kit.m["frames"], axis, at, out, a0, a1, z0, z1,
                             3 if face == "front" else (2 if face == "east" else 1))
        return
    px0, px1 = B_PORCH_X0, hw + BB_WRAP
    py0, py1 = -hd - B_PORCH_D, -hd + BB_SIDE_D
    pe = B_PORCH_POST / 2 - PROUD
    z_e = floor + BB_PORCH_EAVE
    s = BB_PORCH_SLOPE
    over = BB_PORCH_ROOF_OVER
    g0, g1 = floor + BB_PORCH_GLASS[0], floor + BB_PORCH_GLASS[1]
    low = Top(flat=z_e + 0.12)                      # inside the slab near its eaves
    low_e = Top(flat=z_e + 0.11)                    # the east wall's, a centimetre off the front's
    # the west wall's top follows the front slope up to the body (u runs
    # from the body toward the front); the back segment's follows the side
    # slope up to the body's side wall
    west_top = Top(gable=(0.0, (-hd + 0.02) - (py0 - over), z_e, s))
    p_open = {
        "front": [(px0 + 0.30, px1 - 0.30, g0, g1)],
        "west": [(py0 + 0.30, py0 + 0.95, g0, g1)],
        "east": [(py0 + 0.30, py1 - 0.30, g0, g1)],
    }
    kit.shell("porch_", px0, px1, py0, -hd + 0.02 + pe, B_PORCH_T, pe,
              {"front": -BELOW + 0.005, "west": -BELOW - 0.015}, {"front": low, "west": west_top},
              p_open, [kit.m["walls"], base], floor, which=("front", "west"))
    kit.shell("porch_", px0, px1, py0, py1, B_PORCH_T, pe,
              {"east": -BELOW - 0.015}, {"east": low_e}, p_open, [kit.m["walls"], base], floor, which=("east",))
    x_start = px1 - pe
    back_len = x_start - (hw - 0.02)
    back_top = Top(gable=(back_len, back_len + (px1 + over) - x_start, z_e, s))
    back_open = [(0.15, 0.55, g0, g1)]
    kit.wall("porch_wall_back", (x_start, py1, 0.0), (-1, 0, 0), (0, -1, 0), back_len, B_PORCH_T, -BELOW - 0.005,
             back_top, back_open, floor, [kit.m["walls"], base])
    kit.corner_boards("porch_", trim, px0, px1, py0, py1, B_PORCH_POST, PROUD, -BELOW - 0.035, z_e + 0.10,
                      which=("sw", "se", "ne"))
    kit.l_roof("porch_roof", kit.m["roof"], hw - BB_ROOF_LAP, px1 + over, -hd + BB_ROOF_LAP, py0 - over, py1 + over,
               z_e, s, BB_PORCH_ROOF_T)
    faces = (("front", "x", py0, -1, p_open["front"], 4), ("west", "y", px0, -1, p_open["west"], 1),
             ("east", "y", px1, 1, p_open["east"], 4), ("back", "x", py1, 1, [(x_start - 0.55, x_start - 0.15, g0, g1)], 1))
    for face, axis, at, out, opens, lights in faces:
        for k, (a0, a1, z0, z1) in enumerate(opens):
            kit.opening_trim(f"porch_{face}{k}_trim", kit.m["frames"], axis, at, out, a0, a1, z0, z1)
            kit.pane(f"porch_{face}{k}_pane", glass, axis, at, out, a0, a1, z0, z1)
            kit.mullions(f"porch_{face}{k}", kit.m["frames"], axis, at, out, a0, a1, z0, z1, lights)


def build_side_stoop(kit, floor):
    """The side door's landing on the driveway side and its flight down
    along the wall toward the back, railed on the open sides."""
    hw = W / 2
    deck, trim, base = kit.m["deck"], kit.m["trim"], kit.m["base"]
    y0, y1 = BB_SIDE_DECK_Y
    x_out = hw + BB_SIDE_DECK_W
    kit.box("side_deck", deck, hw - 0.03, x_out, y0, y1, floor - 0.20, floor)
    kit.skirt("side_skirt", base, hw - 0.04, x_out - 0.08, y0 + 0.08, y1 - 0.08, floor)
    sx0, sx1 = hw + 0.10, x_out - 0.15
    n, riser = kit.stair("side_stair", deck, sx0, sx1, y1, 1, floor)
    x_at = sx1 + 0.05
    kit.stair_rail("side_rail", trim, x_at, y1, 1, floor, n, riser)
    kit.newel("side_newel_f", trim, x_at - POST / 2, y0 + 0.03, floor)
    kit.panel_rail("side_rail_out", trim, "y", x_at, y0 + 0.03 + POST - 0.02, y1 - 0.03 - POST + 0.03, floor)
    kit.panel_rail("side_rail_front", trim, "x", y0 + 0.03 + POST / 2, hw - 0.06, x_at - POST / 2 + 0.02, floor)


def build_blue(kit, wrap=False, side_door=False, with_chimney=False):
    floor = B_FLOOR
    hw, hd = W / 2, D / 2
    eave = floor + STOREY
    trim, accent, glass, deck, base = (kit.m[k] for k in ("trim", "accent", "glass", "deck", "base"))
    front = [(*B_DOOR_X, floor + THRESHOLD, floor + DOOR_H), (*B_WINDOW_X, floor + SILL, floor + HEAD),
             (*B_UP_WINDOW_X, eave + UP_SILL, eave + UP_HEAD)]
    openings = body_openings(kit, floor, front, side_door=BB_SIDE_DOOR_Y if side_door else None, back_door=not side_door)
    kinds = {("front", 0)} | ({("east", len(openings["east"]) - 1)} if side_door else {("back", 1)})
    build_body(kit, floor, openings, kinds=kinds)
    if side_door:
        build_side_stoop(kit, floor)
        a0, a1, z0, z1 = openings["east"][-1]
        kit.hood("side_door", accent, "y", hw, 1, a0, a1, z1, B_HOOD_H)
    else:
        build_back_stoop(kit, floor)
    if with_chimney:
        chimney(kit, eave)
    # the triple window over the balcony and the paired one by the door
    kit.mullions("front2", kit.m["frames"], "x", -hd, -1, *front[2], 3)
    kit.mullions("front1", kit.m["frames"], "x", -hd, -1, *front[1], 2)
    # red hoods over the door and the main-floor window
    for k in (0, 1):
        a0, a1, z0, z1 = front[k]
        kit.hood(f"front{k}", accent, "x", -hd, -1, a0, a1, z1, B_HOOD_H)
    # the water table, clear of the landing, the porch and the stoop
    if side_door:
        sy0, sy1 = BB_SIDE_DECK_Y
        band(kit, trim, floor, [("back", -BAND_END_X, BAND_END_X), ("west", -BAND_END_Y, BAND_END_Y),
                                ("east", -hd + BB_SIDE_D + 0.06, sy0 - 0.06), ("east", sy1 + 0.06, BAND_END_Y)])
    else:
        band(kit, trim, floor, [("back", -BAND_END_X, STOOP_X[0] - 0.06), ("back", STOOP_X[1] + 0.06, BAND_END_X),
                                ("west", -BAND_END_Y, BAND_END_Y), ("east", -BAND_END_Y, BAND_END_Y)])
    # the sunburst at the peak: a white ring, a red disc, white rays
    zc = eave + B_FAN_Z
    ring_out = kit.half_disc("fan_ring", trim, 0.0, zc, B_FAN_R, -hd - 0.06, -hd + 0.02, segments=12)
    kit.half_disc("fan_disc", accent, 0.0, zc + 0.01, B_FAN_R - 0.10, -hd - 0.04, -hd + 0.03, segments=12)
    kit.rays("fan", trim, 0.0, zc, 0.12, B_FAN_R - 0.04, 0.05, (12, 38, 64, 90, 116, 142, 168), -hd - 0.075, -hd - 0.03)
    kit.box("fan_base", trim, -B_FAN_R - 0.02, B_FAN_R + 0.02, -hd - 0.065, -hd + 0.025, zc - 0.07, zc + 0.02, collide=False)
    gable_brackets(kit, accent, eave, -hd)
    # the balcony on the eave line: a plate 3 cm into the wall, three knee
    # brackets under it, lattice rails on newels
    bx0, bx1 = -B_BALCONY_HW, B_BALCONY_HW
    by0 = -hd - B_BALCONY_D
    kit.box("balcony", deck, bx0, bx1, by0, -hd + 0.03, eave - 0.15, eave)
    for k, x in enumerate(B_BRACKETS_X):
        kit.bracket(f"balcony_bracket_{k}", trim, x - 0.06, x + 0.06, -hd, -1, eave - 0.13, B_BALCONY_D - 0.12, 0.62, lap=0.04)
    # the newels 4.5 cm in from the plate's edge: their posts and caps then
    # miss the bargeboards' planes half a metre in front of the wall
    for tag, x0 in (("w", bx0 + 0.03), ("e", bx1 - 0.03 - POST)):
        kit.newel(f"balcony_newel_{tag}", trim, x0, by0 + 0.045, eave)
    post_y = by0 + 0.045 + POST / 2
    kit.lattice_rail("balcony_rail_front", trim, "x", post_y, bx0 + 0.03 + POST - 0.02, bx1 - 0.03 - POST + 0.02, eave)
    kit.lattice_rail("balcony_rail_w", trim, "y", bx0 + 0.03 + POST / 2, post_y + POST / 2 - 0.02, -hd + 0.05, eave)
    kit.lattice_rail("balcony_rail_e", trim, "y", bx1 - 0.03 - POST / 2, post_y + POST / 2 - 0.02, -hd + 0.05, eave)
    glazed_porch(kit, floor, wrap=wrap)
    px0 = B_PORCH_X0
    # the entry landing from the left corner to the porch, its skirt, lattice
    # rails on newels, the straight flight down from the door
    lx0, lx1 = -hw - 0.06, px0 + 0.02
    ly0 = -hd - B_LANDING_D
    kit.box("landing", deck, lx0, lx1, ly0, -hd + 0.03, floor - 0.20, floor)
    kit.skirt("landing_skirt", base, -hw + 0.04, px0 - 0.08, ly0 + 0.10, -hd + 0.04, floor)
    sx0, sx1 = (B_DOOR_X[0] + B_DOOR_X[1]) / 2 - STAIR_W / 2, (B_DOOR_X[0] + B_DOOR_X[1]) / 2 + STAIR_W / 2
    n, riser = kit.stair("stair", deck, sx0, sx1, ly0, -1, floor)
    rail_w, rail_e = sx0 - 0.05, sx1 + 0.05
    for tag, x_at in (("w", rail_w), ("e", rail_e)):
        kit.stair_rail(f"stair_rail_{tag}", trim, x_at, ly0, -1, floor, n, riser)
    kit.newel("landing_newel_w", trim, lx0 + 0.03, ly0 + 0.03, floor)
    post_y = ly0 + 0.03 + POST / 2
    kit.lattice_rail("landing_rail_w", trim, "y", lx0 + 0.03 + POST / 2, post_y + POST / 2 - 0.02, -hd + 0.05, floor)
    kit.lattice_rail("landing_rail_fw", trim, "x", post_y, lx0 + 0.03 + POST - 0.02, rail_w - POST / 2 + 0.02, floor)
    kit.lattice_rail("landing_rail_fe", trim, "x", post_y, rail_e + POST / 2 - 0.02, px0 + 0.02, floor)
    # the door's fan light: a half-disc of glass on the leaf
    dx = (B_DOOR_X[0] + B_DOOR_X[1]) / 2
    kit.half_disc("door_fanlight", glass, dx, floor + DOOR_H - 0.45, 0.30, -hd + 0.07, -hd + 0.10, segments=8)


def build_purple(kit, bar_z, fan_r, spindles_x, spindle_l, railed=False, with_chimney=False):
    floor = P_FLOOR
    hw, hd = W / 2, D / 2
    up = floor + STOREY                   # the upstairs floor
    eave = up + kit.knee                  # the roof's eave
    trim, accent, frames, deck, base = (kit.m[k] for k in ("trim", "accent", "frames", "deck", "base"))
    front = [(*P_DOOR_X, floor + THRESHOLD, floor + DOOR_H), (*P_WINDOW_X, floor + SILL, floor + HEAD)]
    front += [(a0, a1, up + UP_SILL, up + P_UP_HEAD) for a0, a1 in P_UP_WINDOWS_X]
    openings = body_openings(kit, floor, front)
    build_body(kit, floor, openings, kinds={("front", 0), ("back", 1)})
    build_back_stoop(kit, floor)
    if with_chimney:
        chimney(kit, eave)
    for k in (2, 3):
        a0, a1, z0, z1 = front[k]
        kit.pointed_hood(f"front{k}", frames, -hd, a0, a1, z1, P_HOOD_H)
    band(kit, trim, floor, [("back", -BAND_END_X, STOOP_X[0] - 0.06), ("back", STOOP_X[1] + 0.06, BAND_END_X),
                            ("west", -BAND_END_Y, BAND_END_Y), ("east", -BAND_END_Y, BAND_END_Y)])
    # the spindle-work fan: a bar across the gable, a gold sunburst on it,
    # spindles hanging under it, a magenta panel filling the peak behind
    zb0, zb1 = eave + bar_z[0], eave + bar_z[1]
    half_at_bar = (kit.rise + LIFT - (zb1 - eave)) / kit.tan - 0.05
    kit.box("fan_bar", trim, -half_at_bar, half_at_bar, -hd - 0.06, -hd + 0.02, zb0, zb1, collide=False)
    apex = eave + kit.rise + LIFT
    panel = [(-half_at_bar + 0.02, zb1 - 0.02), (half_at_bar - 0.02, zb1 - 0.02), (0.0, apex - 0.40)]
    kit.prism("fan_panel", accent, panel, "y", -hd - 0.015, -hd + 0.03, collide=False)
    kit.half_disc("fan_disc", frames, 0.0, zb1 - 0.01, fan_r, -hd - 0.05, -hd - 0.005, segments=10)
    kit.rays("fan", trim, 0.0, zb1 - 0.01, 0.08, fan_r - 0.03, 0.04, (20, 50, 90, 130, 160), -hd - 0.07, -hd - 0.04)
    for k, x in enumerate(spindles_x):
        kit.prism(f"fan_spindle{k}", frames, octagon(x, -hd - 0.025, 0.025), "z", zb0 - spindle_l, zb0 + 0.02, collide=False)
    gable_brackets(kit, accent, eave, -hd)
    # the full-width porch: deck and skirt, four turned posts with blocks and
    # brackets, the beam, the shed roof under the eave, the steps at the door
    dx0, dx1 = -hw - P_DECK_OVER, hw + P_DECK_OVER
    dy0 = -hd - P_PORCH_D
    kit.box("porch_deck", deck, dx0, dx1, dy0, -hd + 0.03, floor - 0.20, floor)
    kit.skirt("porch_skirt", base, dx0 + 0.10, dx1 - 0.10, dy0 + 0.10, -hd + 0.04, floor)
    post_y = dy0 + 0.15 + P_POST_BLOCK / 2
    beam0, beam1 = floor + P_BEAM_Z[0], floor + P_BEAM_Z[1]
    for k, x in enumerate(P_POSTS_X):
        b = P_POST_BLOCK / 2
        kit.box(f"post{k}_base", trim, x - b, x + b, post_y - b, post_y + b, floor - 0.02, floor + 0.50)
        kit.prism(f"post{k}_shaft", trim, octagon(x, post_y, P_POST_R), "z", floor + 0.48, beam0 + 0.04)
        kit.box(f"post{k}_capital", frames, x - b, x + b, post_y - b, post_y + b, beam0 - 0.14, beam0 + 0.01, collide=False)
        for tag, sx in (("w", -1), ("e", 1)):
            if (k == 0 and sx < 0) or (k == len(P_POSTS_X) - 1 and sx > 0):
                continue
            xi, xo = x + sx * (b - 0.02), x + sx * (b + 0.30)
            poly = [(xi, beam0 + 0.05), (xo, beam0 + 0.05), (xi, beam0 - 0.30)]
            kit.prism(f"post{k}_bracket_{tag}", accent, poly, "y", post_y - 0.04, post_y + 0.04, collide=False)
    kit.box("porch_beam", trim, dx0 + 0.05, dx1 - 0.05, post_y - 0.10, post_y + 0.10, beam0, beam1, collide=False)
    kit.box("porch_frieze", frames, dx0 + 0.09, dx1 - 0.09, post_y - 0.06, post_y + 0.06, beam0 - 0.10, beam0 + 0.02, collide=False)
    r_wall, r_front = floor + P_ROOF_UNDER[0], floor + P_ROOF_UNDER[1]
    ry0, ry1 = dy0 - 0.30, -hd + 0.02
    poly = [(ry0, r_front), (ry1, r_wall), (ry1, r_wall + P_ROOF_T), (ry0, r_front + P_ROOF_T)]
    kit.prism("porch_roof", kit.m["roof"], poly, "x", -hw - P_ROOF_OVER, hw + P_ROOF_OVER)
    kit.box("porch_fascia", trim, -hw - P_ROOF_OVER - 0.02, hw + P_ROOF_OVER + 0.02, ry0 - 0.05, ry0 + 0.02,
            r_front - 0.10, r_front + P_ROOF_T - 0.03, collide=False)
    sx0, sx1 = P_STEP_X
    kit.stair("stair", deck, sx0, sx1, dy0, -1, floor)   # no rails, as the photograph
    if railed:
        # panel rails between the posts (the painting cuts the balusters),
        # their ends 2 cm inside the shafts' flat faces, the steps' bay open
        inset = P_POST_R * math.cos(math.pi / 8) - 0.02
        for k in range(1, len(P_POSTS_X) - 1):
            kit.panel_rail(f"porch_rail_{k}", trim, "x", post_y, P_POSTS_X[k] + inset, P_POSTS_X[k + 1] - inset, floor)
        # the side rails 1.5 cm inside the posts' centres: their caps then
        # miss the body's wall ends and corner boards where they enter
        for tag, x in (("w", P_POSTS_X[0] + 0.015), ("e", P_POSTS_X[-1] - 0.015)):
            kit.panel_rail(f"porch_rail_{tag}", trim, "y", x, post_y + inset, -hd + 0.05, floor)


def build_variant(v, coll):
    if v == "blue":
        build_blue(Kit("blue", coll))
    elif v == "purple":
        build_purple(Kit("purple", coll), P_BAR_Z, P_FAN_R, P_SPINDLES_X, P_SPINDLE_L)
    elif v == "blue_b":
        build_blue(Kit("blue_b", coll), wrap=True, side_door=True, with_chimney=True)
    elif v == "purple_b":
        build_purple(Kit("purple_b", coll, pitch_deg=PB_PITCH_DEG, knee=PB_KNEE, wall_top_in=PB_WALL_TOP_IN),
                     PB_BAR_Z, PB_FAN_R, PB_SPINDLES_X, PB_SPINDLE_L, railed=True, with_chimney=True)


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


def build_reference(reference):
    hw, hd = W / 2, D / 2
    outline("footprint_body", reference, -hw, hw, -hd, hd)
    outline("lot_9m", reference, LOT_X0, LOT_X0 + LOT_W, LOT_Y[0], LOT_Y[1])
    outline("driveway", reference, hw + B_PORCH_PROUD + 0.1, LOT_X0 + LOT_W, LOT_Y[0], hd + 2.0)
    figure("figure_1p7m", reference, -4.4, -9.0)
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
    kit = Kit("blue", stage)       # a maker for the stage's own pieces
    kit.v = "_stage"

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    ground = mat("_ground", (0.36, 0.44, 0.26))
    walk = mat("_walk", (0.62, 0.60, 0.56))
    street = mat("_street", (0.28, 0.28, 0.30))
    kit.box("ground", ground, -60, 60, -60, 60, -0.30, -0.01, collide=False)
    kit.box("walk", walk, -60, 60, LOT_Y[0] - 1.6, LOT_Y[0], -0.30, 0.0, collide=False)
    kit.box("street", street, -60, 60, -60, LOT_Y[0] - 1.6, -0.30, -0.005, collide=False)
    kit.box("drive", walk, W / 2 + B_PORCH_PROUD + 0.2, LOT_X0 + LOT_W - 0.2, LOT_Y[0] - 1.6, D / 2 + 2.0, -0.30, 0.004, collide=False)
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    fig_obj = figure("_figure", stage, -1.7, -10.0, mat=fig)
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

    # the blue from the street at the photo's angle (right of centre, eye height)
    show("blue")
    shoot("blue_three_quarter", (4.8, -15.5, 1.6), (0.2, -1.5, 3.8), lens=30)
    shoot("blue_front_elevation", (0.0, -40.0, 4.1), (0.0, 0.0, 4.1), ortho=14.0)
    shoot("blue_side_elevation", (40.0, -1.0, 4.1), (0.0, -1.0, 4.1), ortho=20.0)
    shoot("blue_rear_three_quarter", (7.0, 17.0, 1.7), (0.5, 3.0, 3.6), lens=30)
    fig_obj.hide_render = False
    shoot("blue_with_figure", (5.5, -16.5, 1.6), (-0.6, -4.5, 2.9), lens=30)
    fig_obj.hide_render = True
    # the purple from the left front, closer, as its photo
    show("purple")
    shoot("purple_three_quarter", (-8.5, -12.5, 1.5), (-0.5, -1.5, 3.0), lens=26)
    shoot("purple_front_elevation", (0.0, -40.0, 3.6), (0.0, 0.0, 3.6), ortho=14.0)
    shoot("purple_side_elevation", (40.0, -1.0, 3.6), (0.0, -1.0, 3.6), ortho=20.0)
    # the b pair: the blue_b from the driveway side, where its porch wraps
    # and its side door is; the purple_b as the purple
    show("blue_b")
    shoot("blue_b_three_quarter", (10.5, -14.0, 1.6), (0.8, -1.0, 3.6), lens=28)
    show("purple_b")
    shoot("purple_b_three_quarter", (-8.5, -12.5, 1.5), (-0.5, -1.5, 3.6), lens=26)
    # both originals on neighbouring lots, then all four: the others moved
    # over for the shot only
    for o in variant_parts("purple"):
        o.location.x += LOT_W
    for v in ("blue", "purple"):
        for o in variant_parts(v):
            o.hide_render = False
    shoot("both_side_by_side", (1.0, -26.0, 1.7), (4.6, -1.0, 3.8), lens=30)
    for o in variant_parts("purple"):
        o.location.x -= LOT_W
    lots = ("blue", "blue_b", "purple", "purple_b")
    for k, v in enumerate(lots):
        for o in variant_parts(v):
            o.location.x += k * LOT_W
            o.hide_render = False
    shoot("four_up_lots", (13.5, -37.0, 1.8), (13.5, -1.0, 4.4), lens=26, size=(2000, 900))
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

    build_variant("blue", export)
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

    tris = {}
    for v in VARIANTS:
        tris[v] = report(variant_parts(v), f"{v} ({'export' if v == 'blue' else 'export/variant_' + v})")
    eave_b, eave_p = B_FLOOR + STOREY, P_FLOOR + STOREY
    print(f"{NAME}: body {W:.1f} x {D:.1f} m, walls {T:.2f} m, pitch {PITCH_DEG:.0f} deg, storey {STOREY:.1f} m; "
          f"blue floor {B_FLOOR:.2f}, eave {eave_b:.2f}, ridge top {eave_b + RISE + ROOF_VT:.2f}, "
          f"landing {B_LANDING_D:.2f} m deep, balcony {2 * B_BALCONY_HW:.1f} x {B_BALCONY_D:.2f} m at {eave_b:.2f}, "
          f"corner porch {W / 2 + B_PORCH_PROUD - B_PORCH_X0:.2f} x {B_PORCH_D:.2f} m; "
          f"purple floor {P_FLOOR:.2f}, eave {eave_p:.2f}, ridge top {eave_p + RISE + ROOF_VT:.2f}, "
          f"porch {W + 2 * P_DECK_OVER:.1f} x {P_PORCH_D:.2f} m; blue_b porch {BB_WRAP:.1f} m past the wall, "
          f"{BB_SIDE_D:.1f} m back, lean-to eave {B_FLOOR + BB_PORCH_EAVE:.2f}, side door at y {BB_SIDE_DOOR_Y[0]:.2f}..{BB_SIDE_DOOR_Y[1]:.2f}; "
          f"purple_b pitch {PB_PITCH_DEG:.0f} deg, knee {PB_KNEE:.2f}, eave {P_FLOOR + STOREY + PB_KNEE:.2f}, "
          f"ridge top {P_FLOOR + STOREY + PB_KNEE + (W / 2) * math.tan(math.radians(PB_PITCH_DEG)) + ROOF_T / math.cos(math.radians(PB_PITCH_DEG)):.2f}")
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
