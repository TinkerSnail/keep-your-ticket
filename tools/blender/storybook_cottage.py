"""The beach town's storybook cottage, blocked out (2026-10-03): the wide,
low, dark-stained cottage in Christina's photograph
`documentation/reference/houses/black_pearl_cottage.webp` (the rental's own
name stays off the asset), in three `kyt_variant`s.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/storybook_cottage.blend --python tools/blender/storybook_cottage.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, `photo` in `export` itself and `narrow` and
`bungalow` each in `export/variant_<name>` with its eye shut (Send writes one
prop per variant; Check and the handback render show the first). Into the
locked `reference` go the footprint and lot outlines, a 1.7 m figure and the
`ground_line` marker Check reads (the walls reach below z = 0 on purpose).
Everything the tool makes carries `kyt_storybook_cottage`, so a rerun removes
and rebuilds its own work and keeps anything of hers; `export` holding
anything untagged refuses without `--replace`.

**Frame.** Real metres, Z up, the ground at z = 0, the origin at the
footprint's centre. The front (bonnet, door, bays) faces -Y here, which the
glTF export (`send.py`, `export_yup=True`) turns into Godot's +Z. +X is the
viewer's right from the street.

**Contract** (enclosing, as the other houses): public faces, doors and
windows, no interior. Every opening is a real hole through a wall of real
thickness; the door and the panes are solid slabs set in the holes. The
front door's leaf stands on a flush threshold a centimetre over the ground,
so there are no steps at all. No two shapes share a plane: a part that meets
another laps 2 cm into it or stands 2 cm proud of it, and the tool's own scan
(`coplanar_pairs`) reports any pair that does.

**What the photograph says**, read with the door as scale (about 43 px/m at
the front wall): a hipped main roof whose ridge runs about 6.7 m and whose
eave is barely 0.3 m over the door's arch; a 3.1 m wide bonnet arching 1.6 m
out of that eave over a round-topped cream door with a small arched window,
narrow sidelights and lanterns; a small sash window left of the entry; to
the right a deep square bay of three tall windows under a 0.6 m fascia and
frieze, then a lower bay wrapping the corner with glass on both faces, the
main roof's slope running straight down onto both bay roofs (no eave
between); at the left a gabled wing coming 2.5 m forward with a big
small-paned window in its gable and a glazed side toward the entry (the
porch); behind the ridge a green front gable with a truss in its peak, a
brick chimney at its left and a taller stone one at its right, both standing
on the front slope; two skylights under the ridge. The eaves are thick and
rounded (a roll, not a thatch). Board-and-batten, shingles, the stone and
the divided lights are left to painting.

**Choices to state.** The main body is 13.0 m across by 7.5 m deep, the
wing 5.5 m by 10 m: 20.5 m eave to eave, 11.6 m deep, so `photo` and
`bungalow` want a 24 by 20 m lot (two and a half of the town's 9 m lots);
`narrow` drops the wing and shortens the body to 10.3 m (12.3 m eave to
eave) for a 13 m lot. Eave underside 2.60 m at the wall, pitch 30 degrees,
overhang 0.6 m, roll radius 0.20 m, ridge top 5.05 m; the bonnet 3.3 m wide
with its crown 4.05 m up; the big bay 1.5 m deep under a fascia 2.15 to
2.80 m; the corner bay 1.2 m deep and 0.9 m past the east wall under a
2.10 to 2.46 m fascia; the upper storey's eave 4.70 m and gable peak 6.5 m.
`narrow` is the body, bays, entry and upper storey without the wing;
`bungalow` keeps the wing, drops the upper storey and the stone chimney,
and puts a square bay on each side of the entry instead of the corner bay.
Each variant wears its own colours on its own materials, flat stand-ins
named `storybook_cottage_<variant>_<surface>` for the painting to replace.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_storybook_cottage"
NAME = "storybook_cottage"

# --- the shell -----------------------------------------------------------------
T = 0.20                   # wall thickness
BELOW = 0.05               # the walls' feet under the ground
PROUD = 0.02               # a side wall stands this proud of the end walls it laps
EAVE_U = 2.60              # the main roof's underside at the wall face
PITCH_DEG = 30.0
TAN = math.tan(math.radians(PITCH_DEG))
ROOF_T = 0.25              # the roof slab, perpendicular
ROOF_VT = ROOF_T / math.cos(math.radians(PITCH_DEG))
OVER = 0.60                # eaves and rakes
ROLL_R = 0.20              # the rolled eave: a round bar on the slab's square edge
WALL_TOP = 2.80            # flat wall tops, inside the slab (2.715 under, 2.889 over)
LIFT = 0.03                # a gable wall's top, this far inside its slab
EDGE_TOP = EAVE_U - OVER * TAN + ROOF_VT     # the main slab's top at its eave edge
ROLL_Z = EAVE_U - OVER * TAN + ROOF_VT / 2   # the roll's centre: the edge face's middle

WING_PITCH_DEG = 32.0
WING_TAN = math.tan(math.radians(WING_PITCH_DEG))
WING_VT = ROOF_T / math.cos(math.radians(WING_PITCH_DEG))

THRESHOLD = 0.01
DOOR_W, DOOR_H = 1.00, 2.20       # the round-topped door: a rectangle to DOOR_H - DOOR_W/2 and a half-disc
SIDELIGHT = (0.95, 0.30, 0.35, 2.00)   # centre offset from the door, width, sill, head
SMALL_WIN = (-2.80, 0.75, 1.00, 2.00)  # the sash window left of the entry: offset, width, sill, head
SILL, HEAD = 1.00, 2.00           # ordinary windows
BAY_SILL, BAY_HEAD = 0.55, 2.05   # the big bay's windows
BAY_T = 0.15                      # the bays' walls

# the bonnet: a thick arch band lofted from the front section to a flatter
# one inside the attic, so it dies into the slope as an eyebrow does
BONNET_A_IN, BONNET_BAND = 1.30, 0.35
BONNET_H_FRONT, BONNET_H_BACK = 1.45, 0.75
BONNET_LEG = 0.15                 # the band's feet hang this far under the eave line
BONNET_FRONT = 0.45               # its face past the eave edge
BONNET_BACK_OFF = 1.80            # its back section this far behind the front wall, inside the attic

# the big bay: 1.5 m deep, a deep fascia, a 6 degree roof hipped at the ends
BAY_D, BAY_EAVE, BAY_SOFFIT, BAY_TAN, BAY_WALL_TOP = 1.50, 2.80, 2.15, math.tan(math.radians(6)), 2.40
BAY_OVER = 0.30
# the corner bay: lower, 1.2 m deep in front, 0.9 m past the body's east wall,
# a 15 degree roof wrapping the corner on a hip
CB_D, CB_OUT, CB_BACK = 1.20, 0.90, 1.40     # deep, past the east wall, back along it
CB_EAVE, CB_SOFFIT, CB_TAN, CB_WALL_TOP = 2.46, 2.10, math.tan(math.radians(15)), 2.25
CB_SILL, CB_HEAD = 0.55, 2.00

# the upper storey: a gable to the street behind the ridge; its front wall
# 0.45 m behind the ridge and its back wall 2 cm inside the body's, both
# measured from the front wall
UP_Y_OFF = (4.20, 7.28)
UP_FOOT = 2.00                    # its walls start inside the attic
UP_EAVE = 4.70                    # its roof's underside at its wall face
UP_PITCH_DEG = 36.0
UP_TAN = math.tan(math.radians(UP_PITCH_DEG))
UP_OVER = 0.40
UP_ROOF_T = 0.20
UP_VT = UP_ROOF_T / math.cos(math.radians(UP_PITCH_DEG))

SKYLIGHT_OFF = (2.50, 3.30)       # the skylights, behind the front wall
CHIMNEY_FOOT = 3.00               # the stacks start inside the attic

# --- the variants ----------------------------------------------------------------
# body: the main body's x range; door: the door's centre x; wing: the wing's x
# range or None; bays: (x0, x1) of the big bay or None; corner: the corner
# bay (True wraps the body's east end); left_bay: a second square bay west
# of the entry (x0, x1) or None; upper: the upper storey's x range or None;
# brick, stone: chimney (x0, x1, dy0, dy1, top), its depth behind the front
# wall, or None; lot: (half width, y0, y1). Every variant's whole extent,
# eaves and all, is centred on the origin
SPECS = {
    "photo": dict(body=(-4.0, 9.0), depth=(-2.55, 4.95), door=0.0, wing=(-9.5, -4.0), small=True,
                  bay=(2.6, 6.6), corner=True, left_bay=None, upper=(3.0, 8.0),
                  brick=(3.3, 4.0, 2.9, 3.7, 6.6), stone=(6.9, 8.2, 2.5, 3.5, 7.4),
                  skylights=(-0.3, 1.9), lot=(12.0, -10.0, 10.0)),
    "narrow": dict(body=(-5.2, 5.1), depth=(-3.25, 4.25), door=-1.7, wing=None, small=True,
                   bay=(0.8, 4.1), corner=True, left_bay=None, upper=(0.3, 4.8),
                   brick=(0.8, 1.5, 2.9, 3.7, 6.6), stone=(3.9, 5.0, 2.5, 3.5, 7.4),
                   skylights=(-1.8, -0.2), lot=(6.5, -10.0, 10.0)),
    "bungalow": dict(body=(-4.0, 9.0), depth=(-2.55, 4.95), door=1.5, wing=(-9.5, -4.0), small=False,
                     bay=(3.5, 7.5), corner=False, left_bay=(-3.6, -0.6), upper=None,
                     brick=(4.6, 5.3, 3.35, 4.15, 6.0), stone=None,
                     skylights=(-0.5, 1.3), lot=(12.0, -10.0, 10.0)),
}
VARIANTS = ("photo", "narrow", "bungalow")

PALETTES = {
    # the photograph: weathered dark stain, dark green trim, a cream door, brown shingle
    "photo": dict(walls="4f453b", trim="3b4f3f", frames="3b4f3f", door="e9dfc0", roof="5e554a",
                  glass="3e5566", brick="8a4a3a", stone="8a8275", upper="5f7a5a", fascia="4a4038"),
    # silvered cedar, cream trim, a barn-red door, a darker roof
    "narrow": dict(walls="8d8577", trim="f0e8d2", frames="f0e8d2", door="8f2f2a", roof="4d4a46",
                   glass="3e5566", brick="7a3f36", stone="9a9388", upper="b9ae96", fascia="7d7668"),
    # honey stain, navy trim, a sunflower door, cedar shakes
    "bungalow": dict(walls="8a6a3c", trim="2f3e52", frames="2f3e52", door="d8a62a", roof="6b5a4a",
                     glass="3e5566", brick="9c5a48", stone="9a8f80", upper="8a6a3c", fascia="6e5430"),
}


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


def arch_poly(xc, z0, half, z_top, segs=10):
    """A rectangle from z0 up with a half-disc of radius `half` whose crown
    is at z_top (the round-topped door, its little window, the panes)."""
    zs = z_top - half
    pts = [(xc - half, z0), (xc + half, z0)]
    pts += [(xc + half * math.cos(math.pi * k / segs), zs + half * math.sin(math.pi * k / segs)) for k in range(segs + 1)]
    return pts


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

    def __init__(self, variant, coll):
        self.v = variant
        self.coll = coll
        self.m = {k: material(f"{NAME}_{variant}_{k}", srgb(hex6)) for k, hex6 in PALETTES[variant].items()}

    def finish(self, part, bm, mats, collide=True):
        name = f"{self.v}_{part}"
        mesh = bpy.data.meshes.new(name)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
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

    def wall(self, part, origin, u_dir, v_dir, length, thick, z0, top, openings, mat):
        """One wall as a closed shell: two skins, ends, bottom, top, and a real
        reveal round every opening. `origin` is the outer face's start,
        `u_dir` runs along it, `v_dir` into the wall. An opening is
        (u0, u1, z0, z1), anywhere under the top, the gable included: the
        wall is a grid of cells between the opening lines, each cell clipped
        by the roof line, and a cell's edge gets a side face wherever its
        neighbour is an opening, the outside or the sky."""
        O, U, V = Vector(origin), Vector(u_dir), Vector(v_dir)
        us, zs = {0.0, length}, {z0}
        for u0, u1, oz0, oz1 in openings:
            assert 0.0 < u0 < u1 < length and z0 < oz0 < oz1, (part, u0, u1, oz0, oz1, length)
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
        for (i, j), poly in solid.items():
            if poly is None:
                continue
            bm.faces.new([vert(u, z, 0) for u, z in poly])
            bm.faces.new([vert(u, z, 1) for u, z in reversed(poly)])
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
                bm.faces.new((vert(*p, 0), vert(*q, 0), vert(*q, 1), vert(*p, 1)))
        return self.finish(part, bm, [mat])

    def rect_walls(self, prefix, mat, x0, x1, y0, y1, thick, z_top, openings, which=("front", "back", "west", "east"),
                   tops=None, feet=None, front_x0=None, back_x0=None):
        """Walls round the rectangle (x0..x1, y0..y1): the front and back run
        the full length with their outer faces on y0 and y1; the side walls
        stand PROUD of the ends and stop 2 cm inside the end walls, so no
        two faces share a plane and the corners read as a board's edge. The
        side walls' feet and tops sit a centimetre off the end walls' so
        their laps share no plane either. `openings` per wall are
        (a0, a1, z0, z1) in world x (front, back) or world y (west, east).
        `tops` gives a Top per wall; `front_x0` starts the front wall
        elsewhere (lapping into a wing)."""
        tops = tops or {}
        feet = feet or {}
        fx0 = x0 if front_x0 is None else front_x0
        bx0 = x0 if back_x0 is None else back_x0
        spec = {
            "front": ((fx0, y0, 0.0), (1, 0, 0), (0, 1, 0), x1 - fx0, lambda a: a - fx0, 0.0, 0.0),
            "back": ((x1, y1, 0.0), (-1, 0, 0), (0, -1, 0), x1 - bx0, lambda a: x1 - a, 0.0, 0.0),
            "west": ((x0 - PROUD, y1 - 0.02, 0.0), (0, -1, 0), (1, 0, 0), y1 - y0 - 0.04, lambda a: y1 - 0.02 - a, -0.01, -0.01),
            "east": ((x1 + PROUD, y0 + 0.02, 0.0), (0, 1, 0), (-1, 0, 0), y1 - y0 - 0.04, lambda a: a - y0 - 0.02, -0.01, -0.01),
        }
        for key in which:
            origin, u_dir, v_dir, length, to_u, dz_foot, dz_top = spec[key]
            ops = []
            for a0, a1, oz0, oz1 in openings.get(key, ()):
                ua, ub = sorted((to_u(a0), to_u(a1)))
                ops.append((ua, ub, oz0, oz1))
            top = tops.get(key) or Top(flat=z_top + dz_top)
            foot = feet.get(key, -BELOW + dz_foot)
            self.wall(f"{prefix}wall_{key}", origin, u_dir, v_dir, length, thick, foot, top, ops, mat)

    # -- roofs --

    def hip_roof(self, part, mat, x0, x1, y0, y1, z_edge_top, tan, thick_vt):
        """A hipped roof as one closed solid over the eave rectangle
        (x0..x1, y0..y1): the top rises from `z_edge_top` at the edge at
        `tan` to a ridge along the longer axis, the underside `thick_vt`
        under it, the eave edges square (a roll bar covers them)."""
        half = min((x1 - x0) / 2, (y1 - y0) / 2)
        profile = [(half, z_edge_top + half * tan), (0.0, z_edge_top),
                   (0.0, z_edge_top - thick_vt), (half, z_edge_top + half * tan - thick_vt)]
        bm = bmesh.new()
        rings = []
        for d, z in profile:
            xa, xb, ya, yb = x0 + d, x1 - d, y0 + d, y1 - d
            if xa > xb - 1e-6:
                xa = xb = (x0 + x1) / 2
            if ya > yb - 1e-6:
                ya = yb = (y0 + y1) / 2
            rings.append([bm.verts.new((x, y, z)) for x, y in ((xa, ya), (xb, ya), (xb, yb), (xa, yb))])
        for k in range(len(profile) - 1):
            A, B = rings[k], rings[k + 1]
            for s in range(4):
                quad = [A[s], A[(s + 1) % 4], B[(s + 1) % 4], B[s]]
                uniq = []
                for v in quad:
                    if not uniq or (v.co - uniq[-1].co).length > 1e-6:
                        uniq.append(v)
                if len(uniq) > 1 and (uniq[0].co - uniq[-1].co).length < 1e-6:
                    uniq.pop()
                if len(uniq) >= 3:
                    bm.faces.new(uniq)
        return self.finish(part, bm, [mat])

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

    def bay_roof(self, part, mat, fascia, x_a, x_b, y_f, y_b, z_f, tan, soffit):
        """A lean-to over a bay as one solid: the top rising from `z_f` at
        the front edge `y_f` at `tan` to the back edge `y_b` (lapped into
        the body), hipped at both ends (the end slopes rise inward from
        the end edges at the same pitch), a flat soffit at `soffit`. The
        slopes wear the roof material, the deep fascias and the soffit the
        second."""
        D = y_b - y_f
        z_b = z_f + D * tan
        # a narrow bay's hips would cross at 45 degrees: they reach no
        # further than 0.2 m short of its middle, and so stand steeper
        D = min(D, (x_b - x_a) / 2 - 0.2)
        bm = bmesh.new()
        v = {}

        def P(x, y, z):
            key = (round(x, 5), round(y, 5), round(z, 5))
            if key not in v:
                v[key] = bm.verts.new((x, y, z))
            return v[key]

        def face(index, *pts):
            f = bm.faces.new(pts)
            f.material_index = index
        face(0, P(x_a, y_f, z_f), P(x_b, y_f, z_f), P(x_b - D, y_b, z_b), P(x_a + D, y_b, z_b))
        face(0, P(x_b, y_f, z_f), P(x_b, y_b, z_f), P(x_b - D, y_b, z_b))
        face(0, P(x_a, y_f, z_f), P(x_a + D, y_b, z_b), P(x_a, y_b, z_f))
        face(1, P(x_a, y_f, soffit), P(x_a, y_b, soffit), P(x_b, y_b, soffit), P(x_b, y_f, soffit))
        face(1, P(x_a, y_f, soffit), P(x_b, y_f, soffit), P(x_b, y_f, z_f), P(x_a, y_f, z_f))
        face(1, P(x_a, y_f, soffit), P(x_a, y_f, z_f), P(x_a, y_b, z_f), P(x_a, y_b, soffit))
        face(1, P(x_b, y_f, soffit), P(x_b, y_b, soffit), P(x_b, y_b, z_f), P(x_b, y_f, z_f))
        face(1, P(x_a, y_b, soffit), P(x_a, y_b, z_f), P(x_a + D, y_b, z_b), P(x_b - D, y_b, z_b),
             P(x_b, y_b, z_f), P(x_b, y_b, soffit))
        return self.finish(part, bm, [mat, fascia])

    def corner_roof(self, part, mat, fascia, x_in_f, x_in_s, x_out, y_in, y_out, y_back, z_e, slope, thick):
        """A lean-to round the body's corner as one mesh: a front slope
        rising from the eave at `y_out` toward the body and a side slope
        rising from `x_out` toward the body's side, meeting on a 45-degree
        hip that is a crease of the mesh. The front slope's west end is cut
        square at `x_in_f` (inside the big bay) and the side slope stops at
        `x_in_s` (inside the body's east wall), so neither climbs through
        the main roof. `thick` is vertical."""
        def z_front(y):
            return z_e + (y - y_out) * slope

        def z_side(x):
            return z_e + (x_out - x) * slope
        x_c = x_out - (y_in - y_out)
        assert x_in_f < x_c < x_in_s, (part, x_in_f, x_c, x_in_s)
        A, B, C, D = (x_in_f, y_out), (x_out, y_out), (x_c, y_in), (x_in_f, y_in)
        E, F, G = (x_out, y_back), (x_in_s, y_back), (x_in_s, y_in)
        bm = bmesh.new()

        def pair(x, y, z):
            return bm.verts.new((x, y, z)), bm.verts.new((x, y, z - thick))
        a, b, c, d = pair(*A, z_front(A[1])), pair(*B, z_e), pair(*C, z_front(C[1])), pair(*D, z_front(D[1]))
        e, f, g = pair(*E, z_e), pair(*F, z_side(F[0])), pair(*G, z_side(G[0]))
        bm.faces.new((a[0], b[0], c[0], d[0]))
        bm.faces.new((b[0], e[0], f[0], g[0], c[0]))
        bm.faces.new((d[1], c[1], b[1], a[1])).material_index = 1
        bm.faces.new((c[1], g[1], f[1], e[1], b[1])).material_index = 1
        for p, q, index in ((a, b, 1), (b, e, 1), (e, f, 1), (f, g, 0), (g, c, 0), (c, d, 0), (d, a, 1)):
            bm.faces.new((p[0], q[0], q[1], p[1])).material_index = index
        return self.finish(part, bm, [mat, fascia])

    def roll(self, part, mat, pts, r=ROLL_R, sides=12):
        """The rolled eave: a round bar of radius `r` along a polyline, laid
        on a roof's square edge with its centre on the edge face's middle;
        mitred at every inner vertex (one ring in the bisecting plane,
        shared by both runs), flat caps at the ends, which are buried in
        whatever the roll runs into."""
        pts = [Vector(p) for p in pts]
        n = len(pts)
        dirs = [(pts[i + 1] - pts[i]).normalized() for i in range(n - 1)]
        up = Vector((0.0, 0.0, 1.0))
        bm = bmesh.new()
        rings = []
        for i in range(n):
            u = dirs[min(i, n - 2)]
            e1 = (up - u * u.dot(up)).normalized()
            e2 = u.cross(e1)
            circle = [pts[i] + (e1 * math.cos(a) + e2 * math.sin(a)) * r
                      for a in (math.tau * k / sides for k in range(sides))]
            if 0 < i < n - 1:
                nrm = (dirs[i - 1] + dirs[i]).normalized()
                circle = [q + u * ((pts[i] - q).dot(nrm) / u.dot(nrm)) for q in circle]
            rings.append([bm.verts.new(q) for q in circle])
        for i in range(n - 1):
            for k in range(sides):
                bm.faces.new((rings[i][k], rings[i][(k + 1) % sides], rings[i + 1][(k + 1) % sides], rings[i + 1][k]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        return self.finish(part, bm, [mat], collide=False)

    def bonnet(self, part, mat, xc, y_front, y_back, z_spring, a_in, band, h_front, h_back, leg, segs=14):
        """The arched bonnet over the door: a thick arch band (inner
        half-width `a_in`, `band` thick) whose feet hang `leg` under the
        eave line, lofted from its face at `y_front` (rise `h_front`) to a
        flatter section at `y_back` inside the attic (rise `h_back`), so
        its top dies into the main slope as an eyebrow does."""
        angles = [math.pi * k / segs for k in range(segs + 1)]

        def section(h):
            inner = [(xc + a_in * math.cos(t), z_spring + h * math.sin(t)) for t in angles]
            outer = [(xc + (a_in + band) * math.cos(t), z_spring + (h + band) * math.sin(t)) for t in angles]
            return ([(xc + a_in, z_spring - leg)] + inner + [(xc - a_in, z_spring - leg), (xc - a_in - band, z_spring - leg)]
                    + list(reversed(outer)) + [(xc + a_in + band, z_spring - leg)])
        front, back = section(h_front), section(h_back)
        n = len(front)
        bm = bmesh.new()
        F = [bm.verts.new((x, y_front, z)) for x, z in front]
        B = [bm.verts.new((x, y_back, z)) for x, z in back]
        for ring in (F, B):
            o = lambda k: 2 * segs + 4 - k   # the outer arc's index for angle k
            for k in range(segs):
                bm.faces.new((ring[1 + k], ring[2 + k], ring[o(k + 1)], ring[o(k)]))
            bm.faces.new((ring[0], ring[1], ring[o(0)], ring[2 * segs + 5]))
            bm.faces.new((ring[segs + 1], ring[segs + 2], ring[segs + 3], ring[segs + 4]))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((F[i], F[j], B[j], B[i]))
        return self.finish(part, bm, [mat], collide=False)

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

    def mullions(self, prefix, mat, axis, face_at, outward, a0, a1, z0, z1, across, down=1):
        """Chunky bars dividing an opening into `across` by `down` lights,
        3.5 cm proud and lapped 2 cm into the pane behind; the horizontal
        bars a hair thinner than the uprights, so where they cross no two
        faces share a plane."""
        lo, hi = sorted((face_at - 0.10 * outward, face_at + 0.035 * outward))
        for m in range(1, across):
            a = a0 + (a1 - a0) * m / across
            if axis == "x":
                self.box(f"{prefix}_bar{m}", mat, a - 0.05, a + 0.05, lo, hi, z0 - 0.01, z1 + 0.01, collide=False)
            else:
                self.box(f"{prefix}_bar{m}", mat, lo, hi, a - 0.05, a + 0.05, z0 - 0.01, z1 + 0.01, collide=False)
        lo2, hi2 = sorted((face_at - 0.09 * outward, face_at + 0.03 * outward))
        for m in range(1, down):
            z = z0 + (z1 - z0) * m / down
            if axis == "x":
                self.box(f"{prefix}_rail{m}", mat, a0 - 0.01, a1 + 0.01, lo2, hi2, z - 0.04, z + 0.04, collide=False)
            else:
                self.box(f"{prefix}_rail{m}", mat, lo2, hi2, a0 - 0.01, a1 + 0.01, z - 0.04, z + 0.04, collide=False)

    def window(self, prefix, axis, face_at, outward, a0, a1, z0, z1, across=1, down=1):
        self.opening_trim(f"{prefix}_trim", self.m["frames"], axis, face_at, outward, a0, a1, z0, z1)
        self.pane(f"{prefix}_pane", self.m["glass"], axis, face_at, outward, a0, a1, z0, z1)
        if across > 1 or down > 1:
            self.mullions(prefix, self.m["frames"], axis, face_at, outward, a0, a1, z0, z1, across, down)

    def arch_ring(self, part, mat, xc, zc, r_in, r_out, y_lo, y_hi, segs=10):
        """A half-ring in the front wall's plane (the door casing's head)."""
        bm = bmesh.new()
        inner = [bm.verts.new((xc + r_in * math.cos(math.pi * k / segs), y, zc + r_in * math.sin(math.pi * k / segs)))
                 for y in (y_lo, y_hi) for k in range(segs + 1)]
        outer = [bm.verts.new((xc + r_out * math.cos(math.pi * k / segs), y, zc + r_out * math.sin(math.pi * k / segs)))
                 for y in (y_lo, y_hi) for k in range(segs + 1)]
        n = segs + 1
        for k in range(segs):
            bm.faces.new((inner[k], inner[k + 1], outer[k + 1], outer[k]))
            bm.faces.new((inner[n + k], outer[n + k], outer[n + k + 1], inner[n + k + 1]))
            bm.faces.new((outer[k], outer[k + 1], outer[n + k + 1], outer[n + k]))
            bm.faces.new((inner[k], inner[n + k], inner[n + k + 1], inner[k + 1]))
        bm.faces.new((inner[0], outer[0], outer[n], inner[n]))
        bm.faces.new((inner[segs], inner[n + segs], outer[n + segs], outer[segs]))
        return self.finish(part, bm, [mat], collide=False)


# --- the house -----------------------------------------------------------------

def build_house(kit, spec):
    x0, x1 = spec["body"]
    y0, y1 = spec["depth"]
    dx = spec["door"]
    walls, trim, frames, glass, roof, fascia = (kit.m[k] for k in ("walls", "trim", "frames", "glass", "roof", "fascia"))
    wing = spec["wing"]
    bay = spec["bay"]
    corner = spec["corner"]
    left_bay = spec["left_bay"]
    ex = x1 + PROUD                      # the body's east outer face

    # -- the main body's walls: no west wall where the wing covers it --
    door = (dx - DOOR_W / 2, dx + DOOR_W / 2, THRESHOLD, DOOR_H)
    front = [door]
    for s in (-1, 1):
        c, w, z0, z1 = SIDELIGHT
        front.append((dx + s * c - w / 2, dx + s * c + w / 2, z0, z1))
    if spec["small"]:
        off, w, z0, z1 = SMALL_WIN
        front.append((dx + off - w / 2, dx + off + w / 2, z0, z1))
    if not corner:
        front.append((bay[1] + 0.3, bay[1] + 1.2, SILL, HEAD))   # a window where the corner bay would be
    back = [(x0 + 1.5, x0 + 2.7, SILL, HEAD), (x0 + 5.0, x0 + 6.2, SILL, HEAD),
            (x1 - 3.0, x1 - 2.0, THRESHOLD, 2.10), (x1 - 1.6, x1 - 0.6, SILL, HEAD)]
    east = [(y0 + 4.0, y0 + 5.2, SILL, HEAD), (y1 - 1.5, y1 - 0.5, SILL, HEAD)]
    if not corner:
        east.insert(0, (y0 + 0.5, y0 + 2.0, SILL, HEAD))
    which = ("front", "back", "east") if wing else ("front", "back", "west", "east")
    west = [(y0 + 1.0, y0 + 2.2, SILL, HEAD), (y1 - 2.2, y1 - 1.0, SILL, HEAD)]
    # the wing's east wall is the body's west wall; the body's end walls lap
    # 2 cm into it, and the wing's back wall stands 2 cm inside the body's
    lap = (x0 - 0.02) if wing else None
    kit.rect_walls("", walls, x0, x1, y0, y1, T, WALL_TOP, {"front": front, "back": back, "east": east, "west": west},
                   which=which, front_x0=lap, back_x0=lap)
    for k, (a0, a1, z0, z1) in enumerate(front[1:], 1):
        kit.window(f"front{k}", "x", y0, -1, a0, a1, z0, z1, across=1 if k <= 2 else 2, down=1 if k <= 2 else 2)
    for k, (a0, a1, z0, z1) in enumerate(back):
        if k == 2:
            kit.opening_trim(f"back{k}_trim", frames, "x", y1, 1, a0, a1, z0, z1, sill=False)
            kit.pane(f"back{k}_door", kit.m["door"], "x", y1, 1, a0, a1, z0, z1)
        else:
            kit.window(f"back{k}", "x", y1, 1, a0, a1, z0, z1, across=2)
    for k, (a0, a1, z0, z1) in enumerate(east):
        kit.window(f"east{k}", "y", ex, 1, a0, a1, z0, z1, across=2)
    if not wing:
        for k, (a0, a1, z0, z1) in enumerate(west):
            kit.window(f"west{k}", "y", x0 - PROUD, -1, a0, a1, z0, z1, across=2)

    # -- the door: a chunky casing with an arched head, the cream leaf set
    # in the hole with its own little arched window, the wall's corners
    # over the arch filled behind it --
    r = DOOR_W / 2
    zc = DOOR_H - r
    kit.arch_ring("door_casing_head", trim, dx, zc, r - 0.02, r + 0.12, y0 - 0.035, y0 + 0.01)
    for tag, s in (("w", -1), ("e", 1)):
        xa, xb = sorted((dx + s * (r - 0.02), dx + s * (r + 0.12)))
        # half a centimetre off the head's faces, so the lap shares no plane
        kit.box(f"door_jamb_{tag}", trim, xa, xb, y0 - 0.040, y0 + 0.012, -0.02, zc + 0.02, collide=False)
    kit.prism("door_leaf", kit.m["door"], arch_poly(dx, -0.01, r + 0.02, DOOR_H + 0.02), "y", y0 + 0.06, y0 + 0.11)
    kit.box("door_spandrel", walls, dx - r - 0.015, dx + r + 0.015, y0 + 0.10, y0 + 0.14, zc - 0.02, DOOR_H + 0.02, collide=False)
    kit.prism("door_window", glass, arch_poly(dx, 1.50, 0.16, 1.82), "y", y0 + 0.04, y0 + 0.07, collide=False)
    for tag, s in (("w", -1), ("e", 1)):
        xa, xb = sorted((dx + s * 1.12, dx + s * 1.27))
        kit.box(f"lantern_{tag}", trim, xa, xb, y0 - 0.14, y0 + 0.005, 1.85, 2.14, collide=False)

    # -- the main roof: a hipped slab with square edges, the bonnet, the
    # rolled eave as a bar on the edges, broken only where the bonnet's
    # feet and the bay roofs swallow it --
    ex0, ex1, ey0, ey1 = x0 - OVER, x1 + OVER, y0 - OVER, y1 + OVER
    kit.hip_roof("roof", roof, ex0, ex1, ey0, ey1, EDGE_TOP, TAN, ROOF_VT)
    z_spring = EAVE_U - OVER * TAN
    kit.bonnet("bonnet", roof, dx, ey0 - BONNET_FRONT, y0 + BONNET_BACK_OFF, z_spring, BONNET_A_IN, BONNET_BAND,
               BONNET_H_FRONT, BONNET_H_BACK, BONNET_LEG)
    foot = BONNET_A_IN + BONNET_BAND / 2           # the roll's ends, buried in the bonnet's feet
    z_r = ROLL_Z
    # east of the bonnet the roll runs into the big bay's roof (a bay's roof
    # swallows it 0.3 m inside its edge); the long run goes west from the
    # bonnet, round the wing (or the body's west corner), along the back and
    # down the east side into the corner bay's roof, or round the corner
    # and back west into the big bay's
    kit.roll("roll_front_e", roof, [(dx + foot, ey0, z_r), (bay[0], ey0, z_r)])
    if wing:
        wx0, wx1 = wing
        wex0, wex1, wey0 = wx0 - OVER, wx1 + OVER, y0 - 2.5 - OVER
        apex = (wx0 + wx1) / 2
        z_eave_w = EAVE_U - OVER * WING_TAN + WING_VT / 2
        z_apex_w = EAVE_U + ((wx1 - wx0) / 2) * WING_TAN + WING_VT / 2
        path = [(dx - foot, ey0, z_r), (wex1, ey0, z_r), (wex1, wey0, z_eave_w), (apex, wey0, z_apex_w),
                (wex0, wey0, z_eave_w), (wex0, ey1 + 0.02, z_eave_w), (apex, ey1 + 0.02, z_apex_w), (wex1, ey1 + 0.02, z_eave_w)]
    else:
        path = [(dx - foot, ey0, z_r), (ex0, ey0, z_r), (ex0, ey1, z_r)]
    if left_bay:
        # the west run stops in the left bay's roof; the long run starts past it
        lb0, lb1 = left_bay
        kit.roll("roll_front_w", roof, [(dx - foot, ey0, z_r), (lb1, ey0, z_r)])
        path = [(lb0, ey0, z_r)] + path[1:]
    path.append((ex1, ey1, z_r))
    if corner:
        path.append((ex1, y0 + CB_BACK + 0.05, z_r))   # 5 cm past the corner bay's back wall face
    else:
        path += [(ex1, ey0, z_r), (bay[1], ey0, z_r)]
    kit.roll("roll_main", roof, path)
    for k, sx in enumerate(spec["skylights"]):
        ya, yb = y0 + SKYLIGHT_OFF[0], y0 + SKYLIGHT_OFF[1]
        def top(y):
            return EDGE_TOP + (y - ey0) * TAN
        kit.prism(f"skylight{k}", glass, [(ya, top(ya) - 0.05), (yb, top(yb) - 0.05), (yb, top(yb) + 0.08), (ya, top(ya) + 0.08)],
                  "x", sx, sx + 0.70, collide=False)
        kit.prism(f"skylight{k}_curb", trim, [(ya - 0.06, top(ya - 0.06) - 0.04), (yb + 0.06, top(yb + 0.06) - 0.04),
                                              (yb + 0.06, top(yb + 0.06) + 0.05), (ya - 0.06, top(ya - 0.06) + 0.05)],
                  "x", sx - 0.06, sx + 0.76, collide=False)

    # -- the wing: a gable to the street, 2.5 m forward, its big window in
    # the gable and its glazed side (the porch) toward the entry --
    if wing:
        wy0 = y0 - 2.5
        half = (wx1 - wx0) / 2
        gable = Top(gable=(half, half, EAVE_U, WING_TAN))
        big = (wx0 + 0.4, wx0 + 2.2, 0.45, 2.35)
        w_open = {"front": [big], "back": [(apex - 0.75, apex + 0.75, SILL, HEAD)],
                  "west": [(wy0 + 1.0, wy0 + 2.2, SILL, HEAD), (wy0 + 4.5, wy0 + 5.7, SILL, HEAD), (y1 - 2.5, y1 - 1.3, SILL, HEAD)]}
        kit.rect_walls("wing_", walls, wx0, wx1, wy0, y1 - 0.02, T, WALL_TOP, w_open, which=("front", "back", "west"),
                       tops={"front": gable, "back": gable}, feet={"back": -BELOW - 0.005})
        # the east wall only in front of the body, lapping 2 cm into its front wall
        porch = (wy0 + 0.30, y0 - 0.30, 0.50, 2.30)
        kit.wall("wing_wall_east", (wx1 + PROUD, wy0 + 0.02, 0.0), (0, 1, 0), (-1, 0, 0), y0 + 0.02 - (wy0 + 0.02), T,
                 -BELOW - 0.01, Top(flat=WALL_TOP - 0.01), [(porch[0] - wy0 - 0.02, porch[1] - wy0 - 0.02, porch[2], porch[3])], walls)
        kit.window("wing_big", "x", wy0, -1, *big, across=3, down=4)
        kit.window("wing_porch", "y", wx1 + PROUD, 1, *porch, across=3, down=2)
        kit.window("wing_back0", "x", y1 - 0.02, 1, *w_open["back"][0], across=2)
        for k, (a0, a1, z0, z1) in enumerate(w_open["west"]):
            kit.window(f"wing_west{k}", "y", wx0 - PROUD, -1, a0, a1, z0, z1, across=2)
        kit.gable_roof("wing_roof", roof, apex, half, EAVE_U, WING_TAN, OVER, ROOF_T, wey0, ey1 + 0.02)

    # -- the bays --
    def square_bay(prefix, bx0, bx1, lights):
        by0 = y0 - BAY_D
        b_open = {"front": [], "west": [], "east": []}
        n = len(lights)
        gap = 0.34                  # casings reach 0.16 past an opening: neighbours miss by 2 cm
        total = bx1 - bx0 - gap * (n + 1)
        a = bx0 + gap
        for w_rel, across, down in lights:
            w = total * w_rel
            b_open["front"].append((a, a + w, BAY_SILL, BAY_HEAD, across, down))
            a += w + gap
        ops = {"front": [o[:4] for o in b_open["front"]]}
        # the side walls end 2 cm inside the body's front wall
        kit.rect_walls(prefix, walls, bx0, bx1, by0, y0 + 0.04, BAY_T, BAY_WALL_TOP, ops, which=("front", "west", "east"),
                       feet={"front": -BELOW - 0.02, "west": -BELOW - 0.03, "east": -BELOW - 0.03},
                       tops={"front": Top(flat=BAY_WALL_TOP - 0.02), "west": Top(flat=BAY_WALL_TOP - 0.03), "east": Top(flat=BAY_WALL_TOP - 0.03)})
        for k, (a0, a1, z0, z1, across, down) in enumerate(b_open["front"]):
            kit.window(f"{prefix}front{k}", "x", by0, -1, a0, a1, z0, z1, across=across, down=down)
        kit.bay_roof(f"{prefix}roof", roof, fascia, bx0 - BAY_OVER, bx1 + BAY_OVER, by0 - BAY_OVER, y0 + 0.30, BAY_EAVE, BAY_TAN, BAY_SOFFIT)

    if bay:
        square_bay("bay_", bay[0], bay[1], ((0.3, 1, 1), (0.4, 4, 6), (0.3, 1, 1)))
    if left_bay:
        square_bay("lbay_", left_bay[0], left_bay[1], ((0.33, 2, 3), (0.34, 2, 3), (0.33, 2, 3)))
    if corner:
        cx0, cx1 = (bay[1] if bay else x1 - 3.3), ex + CB_OUT
        cy0, cy1 = y0 - CB_D, y0 + CB_BACK
        if cx1 - cx0 > 2.6:
            c_front = [(cx0 + 0.30, cx0 + 1.42, CB_SILL, CB_HEAD), (cx0 + 1.78, cx1 - 0.30, CB_SILL, CB_HEAD)]
        else:
            c_front = [(cx0 + 0.30, cx1 - 0.30, CB_SILL, CB_HEAD)]
        c_east = [(cy0 + 0.25, cy1 - 0.30, CB_SILL, CB_HEAD)]
        c_feet = {"front": -BELOW - 0.02, "east": -BELOW - 0.03, "back": -BELOW - 0.025}
        c_tops = {"front": Top(flat=CB_WALL_TOP - 0.02), "east": Top(flat=CB_WALL_TOP - 0.03), "back": Top(flat=CB_WALL_TOP - 0.025)}
        kit.rect_walls("cbay_", walls, cx0, cx1, cy0, cy1, BAY_T, CB_WALL_TOP, {"front": c_front, "east": c_east},
                       which=("front", "east"), feet=c_feet, tops=c_tops)
        # the back wall from inside the body's east wall to the bay's east wall
        kit.wall("cbay_wall_back", (cx1 - 0.0, cy1, 0.0), (-1, 0, 0), (0, -1, 0), cx1 - (x1 - 0.02), BAY_T, c_feet["back"],
                 c_tops["back"], [], walls)
        for k, (a0, a1, z0, z1) in enumerate(c_front):
            kit.window(f"cbay_front{k}", "x", cy0, -1, a0, a1, z0, z1, across=2, down=2)
        kit.window("cbay_east0", "y", cx1 + PROUD, 1, *c_east[0], across=3, down=2)
        # a centimetre past the big bay's wall ends and 2 cm short of its roof's back, so no lap shares a plane
        kit.corner_roof("cbay_roof", roof, fascia, cx0 + 0.01, x1 - 0.15, cx1 + PROUD + BAY_OVER, y0 + 0.28, cy0 - BAY_OVER, cy1 + BAY_OVER,
                        CB_EAVE, CB_TAN, CB_EAVE - CB_SOFFIT)

    # -- the upper storey: a gable to the street behind the ridge, a truss
    # in its peak, the chimneys standing on the front slope --
    up = spec["upper"]
    if up:
        ux0, ux1 = up
        uy0, uy1 = y0 + UP_Y_OFF[0], y0 + UP_Y_OFF[1]
        uhalf = (ux1 - ux0) / 2
        u_gable = Top(gable=(uhalf, uhalf, UP_EAVE, UP_TAN))
        # the side walls' lower halves are inside the main roof, so only the
        # back wall, which rises clear of its slope, has windows
        xc_u = (ux0 + ux1) / 2
        u_open = {"back": [(xc_u - 1.35, xc_u - 0.35, UP_FOOT + 1.4, UP_FOOT + 2.3), (xc_u + 0.35, xc_u + 1.35, UP_FOOT + 1.4, UP_FOOT + 2.3)]}
        kit.rect_walls("up_", kit.m["upper"], ux0, ux1, uy0, uy1, T, UP_EAVE + 0.18, u_open,
                       feet={"front": UP_FOOT, "back": UP_FOOT, "west": UP_FOOT - 0.01, "east": UP_FOOT - 0.01},
                       tops={"front": u_gable, "back": u_gable})
        for k, (a0, a1, z0, z1) in enumerate(u_open["back"]):
            kit.window(f"up_back{k}", "x", uy1, 1, a0, a1, z0, z1, across=2)
        kit.gable_roof("up_roof", roof, (ux0 + ux1) / 2, uhalf, UP_EAVE, UP_TAN, UP_OVER, UP_ROOF_T, uy0 - UP_OVER, uy1 + UP_OVER)
        # one chevron bargeboard on the front rake, the truss under the peak:
        # a collar, a king post and two struts, each a hair different in
        # depth so their laps share no plane
        apex_u = UP_EAVE + uhalf * UP_TAN + LIFT
        xe = uhalf + UP_OVER + 0.05
        top_a, top_b = apex_u + UP_VT - LIFT - 0.02, UP_EAVE - UP_OVER * UP_TAN + UP_VT - 0.02
        poly = [(xc_u - xe, top_b), (xc_u, top_a), (xc_u + xe, top_b), (xc_u + xe, top_b - 0.28), (xc_u, top_a - 0.28), (xc_u - xe, top_b - 0.28)]
        kit.prism("up_barge", trim, poly, "y", uy0 - UP_OVER - 0.06, uy0 - UP_OVER + 0.02, collide=False)
        collar = UP_EAVE + 0.70
        reach = (apex_u - LIFT - collar) / UP_TAN - 0.10
        kit.box("up_collar", trim, xc_u - reach, xc_u + reach, uy0 - 0.08, uy0 + 0.01, collar, collar + 0.16, collide=False)
        kit.box("up_king", trim, xc_u - 0.08, xc_u + 0.08, uy0 - 0.07, uy0 + 0.005, collar + 0.14, apex_u - 0.05, collide=False)
        for sx in (-1, 1):
            poly = [(xc_u + sx * (reach - 0.35), collar + 0.14), (xc_u + sx * (reach - 0.75), collar + 0.14), (xc_u + sx * 0.06, apex_u - 0.55)]
            kit.prism(f"up_strut_{'w' if sx < 0 else 'e'}", trim, poly, "y", uy0 - 0.06, uy0 + 0.015, collide=False)
    for key, mat_key in (("brick", "brick"), ("stone", "stone")):
        c = spec[key]
        if not c:
            continue
        cx0, cx1, dy0, dy1, top = c
        cy0, cy1 = y0 + dy0, y0 + dy1
        kit.box(key, kit.m[mat_key], cx0, cx1, cy0, cy1, CHIMNEY_FOOT, top)
        kit.box(f"{key}_cap", kit.m[mat_key], cx0 - 0.06, cx1 + 0.06, cy0 - 0.06, cy1 + 0.06, top - 0.02, top + 0.14, collide=False)


def build_variant(v, coll):
    build_house(Kit(v, coll), SPECS[v])


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
    for v in VARIANTS:
        s = SPECS[v]
        outline(f"footprint_{v}", reference, s["body"][0], s["body"][1], s["depth"][0], s["depth"][1])
        if s["wing"]:
            outline(f"footprint_{v}_wing", reference, s["wing"][0], s["wing"][1], s["depth"][0] - 2.5, s["depth"][1])
    hw, ly0, ly1 = SPECS["photo"]["lot"]
    outline("lot_24m", reference, -hw, hw, ly0, ly1)
    hw, ly0, ly1 = SPECS["narrow"]["lot"]
    outline("lot_13m", reference, -hw, hw, ly0, ly1)
    figure("figure_1p7m", reference, -5.5, -9.0)
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
    overlapping in area: the z-fights. Each face's plane is written the
    same way up, so a pair facing opposite ways is found too."""
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
    ly0 = SPECS["photo"]["lot"][1]
    kit.box("ground", ground, -80, 80, -80, 80, -0.30, -0.01, collide=False)
    kit.box("walk", walk, -80, 80, ly0 - 1.8, ly0, -0.30, 0.0, collide=False)
    kit.box("street", street, -80, 80, -80, ly0 - 1.8, -0.30, -0.005, collide=False)
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    fig_obj = figure("_figure", stage, -5.5, -7.0, mat=fig)
    fig_obj.hide_render = True

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.35, -0.75, 0.60)).to_track_quat("Z", "Y").to_euler()
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

    # the photo's view: straight on from the sidewalk across the street, a
    # little above eye height, wide enough for the whole front
    show("photo")
    shoot("photo_front", (0.4, -19.5, 1.9), (0.4, -0.5, 2.6), lens=26, size=(1800, 1200))
    shoot("photo_three_quarter", (-15.0, -15.5, 2.0), (0.0, -0.5, 2.8), lens=30)
    shoot("photo_three_quarter_right", (17.0, -14.5, 2.0), (1.0, -0.5, 2.8), lens=30)
    shoot("photo_rear_three_quarter", (14.0, 16.5, 2.2), (1.0, 2.5, 3.2), lens=30)
    shoot("photo_front_elevation", (0.0, -60.0, 3.5), (0.0, 0.0, 3.5), ortho=24.0, size=(2000, 1000))
    fig_obj.hide_render = False
    shoot("photo_with_figure", (-9.0, -13.5, 1.7), (-1.5, -2.5, 2.4), lens=30)
    fig_obj.hide_render = True
    show("narrow")
    shoot("narrow_three_quarter", (-11.0, -13.0, 1.9), (0.0, -1.0, 2.8), lens=30)
    show("bungalow")
    shoot("bungalow_three_quarter", (-15.0, -15.5, 2.0), (0.0, -0.5, 2.8), lens=30)
    # all three side by side, moved over for the shot only, each 4 m clear of the
    # last by its own extent (fixed steps let the bungalow's wing run into the narrow)
    steps, left, edge = {}, None, None
    for v in ("photo", "narrow", "bungalow"):
        xs = [(o.matrix_world @ Vector(c)).x
              for o in variant_parts(v) if o.type == "MESH" for c in o.bound_box]
        steps[v] = 0.0 if edge is None else edge + 4.0 - min(xs)
        left = min(xs) if left is None else left
        edge = max(xs) + steps[v]
    for v, step in steps.items():
        for o in variant_parts(v):
            o.location.x += step
            o.hide_render = False
    mid, span = (left + edge) / 2, edge - left
    shoot("all_variants", (mid, -(0.8 * span + 4.0), 2.6), (mid, 0.5, 3.6), lens=28, size=(2400, 900))
    for v, step in steps.items():
        for o in variant_parts(v):
            o.location.x -= step


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
    print(f"{NAME}: walls {T:.2f} m, eave underside {EAVE_U:.2f} at the wall, pitch {PITCH_DEG:.0f} deg, "
          f"overhang {OVER:.2f}, roll radius {ROLL_R:.2f}, ridge top {EDGE_TOP + 4.35 * TAN:.2f}; "
          f"bonnet {2 * (BONNET_A_IN + BONNET_BAND):.2f} m wide, crown {EAVE_U - OVER * TAN + BONNET_H_FRONT + BONNET_BAND:.2f}; "
          f"big bay {BAY_D:.2f} m deep, fascia top {BAY_EAVE:.2f}; corner bay {CB_D:.2f} m deep, fascia top {CB_EAVE:.2f}; "
          f"upper eave {UP_EAVE:.2f}, pitch {UP_PITCH_DEG:.0f} deg")
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
