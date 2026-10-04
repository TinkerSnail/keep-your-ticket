"""The streetcar beach house, blocked out (2026-10-02): Christina's photograph
`documentation/reference/houses/streetcar_beach_house.webp`, "this was a
streetcar turned into a beach house".

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/streetcar_house.blend --python tools/blender/streetcar_house.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, two variants of one house, both standing at
the origin, each marked `kyt_variant` so Send writes each as a prop of its
own (`send.py`): **photo**, the house as the photograph shows it, in
`export`; and **tell**, the same house with one clue for a curious player,
in `export/variant_tell` with its eye shut. The clue is the car's rounded
end: the east end (+X, the photograph's right, where its purple fence hides
the corner) is the streetcar's D-shaped end in plan, its band of three
windows following the curve under the same teal head band, and the room the
owners added behind the car stops 0.6 m short of it, so from the side or the
back the house reads as a car with a box built on; the street face is the
photo variant's, part for part. Into the locked `reference` collection go
the footprint and lot outlines, a 1.7 m figure and the `ground_line` marker
Check reads (the walls reach 5 cm below z = 0 on purpose, like the hardscape
kit's). A third variant, **big** (2026-10-03, Christina's rule that the
alternatives become variants), stands in `export/variant_big`: a 14 m
double-truck car body, its row of windows and door on the long side under
the same broad low roof, over the car alone; a lean-to room behind it with
its own tin roof tucked under the car's eave, set 0.3 m in from the car's
square west end and stopping 0.6 m short of its rounded east end, so the
D-end shows past it with no post; the back and end windows on the car's
1.2 m bay rhythm. It needs the long end of the plan's 15-20 m frontage. Everything the tool makes carries `kyt_streetcar_house`, so a rerun
removes and rebuilds its own work and keeps anything of hers; `export`
holding anything untagged refuses without `--replace`.

**Frame.** Real metres, Z up, the ground at z = 0, the origin at the
footprint's centre. The front (porch, door, the car's window row) faces -Y
here, which the glTF export (`send.py`, `export_yup=True`) turns into
Godot's +Z. The car runs along X.

**Read off the photograph** (the door as the scale, about 96 px/m): the car
body 9.6 m long, a single-truck car's length, not the 12-15 m of a big one;
window sills 1.08 m over the floor and heads 2.05 m, the door's head on the
same line; the eave 2.4 m over the floor; the deck three risers up; a very
low roof whose slope never shows, so it is a 5 degree hip under a flat soffit
with a 0.65 m overhang all round, corrugated tin (paint) with a 0.22 m blue
fascia; a knee brace under each end of the overhang; the porch roof a
separate tin lean-to that steps forward and 7 cm lower than the main fascia,
two posts, a wide top rail and a mid rail each side, steps the deck's full
width with teal nosings; no corner boards, the siding turns the corner.

**Chosen, not read** (the photo shows the long side only): the car 2.7 m wide
(real ones 2.6-2.9), with a 2.9 m room added behind it under the one roof, so
the house is 5.6 m deep; the back and ends carry plain windows. The house is
9.6 x 5.6 m plus a 1.5 m porch and 0.6 m of steps: it suits the plan's 9 x
15-20 m lot turned lengthwise along the street (1.5-4 m clear at each end,
the back wall 1 m off the rear line), not a lot it runs down.

**Contract** (enclosing): public faces, porch, windows, no interior. Every
opening is a real hole through a wall of real thickness; the door and the
panes are slabs set in the holes, so nothing behind them needs to exist. The
deck is walkable from its steps, and the steps follow the park's stair rule
(`tools/gen_props.gd`, `_flight_ramp`): a narrow ramp through the nosings is
the floor, the treads are scenery showing past it on both sides and do not
collide (`kyt_collision = none`). No two shapes share a plane: a part that
meets another laps 2 cm into it or stands proud of it.

**How it is built.** The walls of each variant are one closed shell along a
path of straight runs and arcs (`shell`), mitred at the corners, with the
openings cut through it and a reveal round each, the skirt below the floor
line as the second material slot; the tell's rounded end is an arc in that
path, faceted at the same fixed 15 degree stations as every curved trim and
pane on it, so the curved pieces lie parallel and never share a plane. The
roof is a flat soffit slab, a hip solid on it and a mitred fascia loop round
both. Parts both variants share (porch, roof, the street windows and door,
the west end) are built once and the tell gets linked copies (one mesh each,
so reshaping one reshapes both), the way the park lamp's three share a plate.
Stand-in materials by surface, `streetcar_house_<surface>`; the lap siding,
the corrugations, the door's panes and the curtains are painting.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_streetcar_house"
PROP = "streetcar_house"

# --- the photograph's numbers ----------------------------------------------
L = 9.6                    # the car body, along X
HL = L / 2
CAR_W = 2.7                # the car body, across (the street rooms)
ADD_D = 2.9                # the room added behind it
D = CAR_W + ADD_D
HD = D / 2
FRONT_Y = -HD              # the street face's outer plane
CAR_BACK_Y = FRONT_Y + CAR_W
T = 0.20                   # wall thickness
BELOW = 0.05               # how far the walls reach below the ground
FLOOR = 0.45               # the deck, the floor, the door's sill line
THRESHOLD = 0.01           # a door's sill over the floor outside it (the door is shut)
SKIRT_TOP = FLOOR + THRESHOLD   # the plum skirt ends on the door's sill line
SILL = FLOOR + 1.08
HEAD = FLOOR + 2.05        # one head line for the windows and the door
EAVE = FLOOR + 2.42        # the soffit's underside
WALL_TOP = EAVE + 0.03     # the walls end inside the soffit slab
BAND_Z0, BAND_T = HEAD - 0.02, 0.17   # the teal head band the openings hang from
JAMB, SILL_T = 0.10, 0.10
PITCH = math.radians(5.0)  # the hip, unseen from the street
OVER = 0.65                # the eave overhang all round
SOFFIT_T = 0.06
ROOF_LIFT = 0.04           # the roof solid's flat underside, inside the soffit
ROOF_EDGE = 0.12           # the roof's top at the eave edge, over EAVE
FASCIA_Z0, FASCIA_Z1, FASCIA_T = EAVE - 0.06, EAVE + 0.16, 0.08
XE, YE = HL + OVER, HD + OVER
RIDGE_TOP = EAVE + ROOF_EDGE + (YE - 0.01) * math.tan(PITCH)   # the hip solid is inset 1 cm
WIN_W, WIN_H = 0.90, HEAD - SILL
DOOR_X = (0.27, 1.17)
DOOR_C = (DOOR_X[0] + DOOR_X[1]) / 2
# the car's windows along the street, world x: three west of the porch, one east
FRONT_WINDOWS = ((-3.84, -2.94), (-2.60, -1.70), (-1.37, -0.47), (2.37, 3.27))
BACK_WINDOWS = ((-3.4, -2.2), (0.6, 1.8))          # world x on the back wall
END_WINDOWS = ((-1.9, -1.0), (0.9, 1.8))           # world y on an end wall
PORCH_W, PORCH_D = 2.9, 1.5
PORCH_X0, PORCH_X1 = DOOR_C - PORCH_W / 2, DOOR_C + PORCH_W / 2
DECK_Y0 = FRONT_Y - PORCH_D                        # the deck's front edge
POST = 0.14
RAIL_H, MID_RAIL = 0.90, 0.45
RISER, GOING = 0.15, 0.30
PR_X0, PR_X1 = DOOR_C - 2.15, DOOR_C + 2.15        # the porch roof, 0.75 m past each post
PR_Y1 = DECK_Y0 - 0.40                             # its front edge
PR_PITCH = math.radians(3.0)
PR_T = 0.06
PR_Z_BACK = EAVE + 0.01                            # its top where it tucks under the main fascia
PR_FASCIA = 0.22
PIPE_AT = (0.60, -2.30)                            # the stovepipe, on the front slope
# the tell: the car's rounded east end, a D in plan, and the addition short of it
ROUND_R = CAR_W / 2
ROUND_C = (HL - ROUND_R, FRONT_Y + ROUND_R)
ADD_END_X = ROUND_C[0] - 0.6
FACET = math.radians(15.0)                         # every curved piece breaks at k * FACET
ARC_WINDOWS = tuple((math.radians(a), math.radians(b)) for a, b in ((-70, -32), (-19, 19), (32, 70)))
LOT_W, LOT_D = 16.0, 9.0
LOT_Y0 = -5.5                                      # the street line
ROOF = (-XE, XE, -YE, YE)                          # the roof's plan, overhang included
VARIANTS = ("photo", "tell", "big")
# the big variant: a 14 m double-truck car, a lean-to behind, the car's
# rhythm of 0.9 m windows at a 1.2 m pitch on every face
B_L = 14.0
B_HL = B_L / 2
B_LEAN_D = 2.4
B_D = CAR_W + B_LEAN_D
B_HD = B_D / 2
B_FRONT_Y = -B_HD
B_CAR_BACK_Y = B_FRONT_Y + CAR_W
B_ROUND_C = (B_HL - ROUND_R, B_FRONT_Y + ROUND_R)
B_LEAN_X0, B_LEAN_X1 = -B_HL + 0.3, B_ROUND_C[0] - 0.6
B_DOOR_X = (0.15, 1.05)
B_DOOR_C = (B_DOOR_X[0] + B_DOOR_X[1]) / 2
# five bays west of the porch (the last one's jamb under the post, as the
# photo's), the door's wide bay, a blank bay under the east post, three
# bays to the rounded end, and the end's three on the arc
B_FRONT_WINDOWS = ((-6.50, -5.60), (-5.30, -4.40), (-4.10, -3.20), (-2.90, -2.00), (-1.70, -0.80),
                   (2.25, 3.15), (3.45, 4.35), (4.65, 5.55))
B_BACK_WINDOWS = ((-5.30, -4.40), (-2.90, -2.00), (-0.50, 0.40), (1.90, 2.80))   # every second bay
B_CAR_END_WINDOWS = ((-2.25, -1.35), (-1.05, -0.15))   # two bays centred on the car's axis
B_LEAN_END_WINDOW = (0.90, 1.80)                       # one, centred on the lean-to's end
B_LEAN_HEAD = 2.30                                     # under the lean-to's lower eave
B_LEAN_PITCH = math.radians(5.3)
B_LEAN_TOP0 = EAVE - 0.03          # the lean-to roof's top where it laps into the car's back wall
B_LEAN_OVER, B_LEAN_END_OVER = 0.50, 0.25
B_LEAN_T = 0.08                    # the lean-to roof at its eave; it thickens toward the car
B_PORCH_X0, B_PORCH_X1 = B_DOOR_C - PORCH_W / 2, B_DOOR_C + PORCH_W / 2
B_DECK_Y0 = B_FRONT_Y - PORCH_D
B_PR_X0, B_PR_X1 = B_DOOR_C - 2.15, B_DOOR_C + 2.15
B_PR_Y1 = B_DECK_Y0 - 0.40
B_PIPE_AT = (-2.0, -2.0)
B_ROOF = (-B_HL - OVER, B_HL + OVER, B_FRONT_Y - OVER, B_CAR_BACK_Y + OVER)   # over the car alone


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {
    f"{PROP}_walls": srgb("f3c531"),     # yellow lap siding
    f"{PROP}_skirt": srgb("4a2240"),     # the dark plum skirt
    f"{PROP}_trim": srgb("1f8c8a"),      # teal: band, jambs, sills, nosings
    f"{PROP}_glass": srgb("c9d3d8"),     # the panes (white curtains behind)
    f"{PROP}_door": srgb("a8203c"),      # the red many-paned door
    f"{PROP}_fascia": srgb("2a56a8"),    # blue fascia, both roofs
    f"{PROP}_tin": srgb("aeb4b8"),       # corrugated tin, both roofs and the soffit
    f"{PROP}_rails": srgb("c22a8e"),     # magenta posts, rails, braces
    f"{PROP}_deck": srgb("5a2c6e"),      # the purple deck
    # the big car's own set (2026-10-03, "on the variations lets change the
    # colors"), so it is not the photo house's twin: turquoise body, cream
    # trim, coral posts and rails, white fascia, navy skirt, a bright yellow
    # door ("can the doors be different colors too"); the rest as the photo's
    f"{PROP}_big_walls": srgb("35b7b0"),
    f"{PROP}_big_skirt": srgb("1d2a55"),
    f"{PROP}_big_trim": srgb("f3ead2"),
    f"{PROP}_big_glass": srgb("c9d3d8"),
    f"{PROP}_big_door": srgb("f7d117"),
    f"{PROP}_big_fascia": srgb("f4f4f0"),
    f"{PROP}_big_tin": srgb("aeb4b8"),
    f"{PROP}_big_rails": srgb("ee6f55"),
    f"{PROP}_big_deck": srgb("5a2c6e"),
}
SURFACES = ("walls", "skirt", "trim", "glass", "door", "fascia", "tin", "rails", "deck")


def material(name, colour=None):
    """A stand-in material by name. The colours in COLOURS are the
    builder's: a rerun resets them, because a material survives
    `--replace` and the big car's door stayed red after its colour changed
    (2026-10-03)."""
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


def mats(tag=""):
    """The stand-in materials by surface, `streetcar_house_<tag><surface>`."""
    return {k: material(f"{PROP}_{tag}{k}") for k in SURFACES}


# --- building blocks -------------------------------------------------------

def finish(name, bm, coll, mats, variant=None, collide=True, flat=True):
    """A bmesh into an object in `coll`, tagged, with its material slots."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
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


# --- paths: straight runs and arcs for the wall shells ------------------------

class Straight:
    """A straight run of a path, `p0` to `p1` in plan. The path's inside is on
    its left, so a closed path runs anticlockwise."""

    def __init__(self, p0, p1):
        self.p0, self.p1 = Vector(p0), Vector(p1)
        d = self.p1 - self.p0
        self.length = d.length
        self.dir = d / self.length
        self.n = Vector((-self.dir.y, self.dir.x))
        self.breaks = ()

    def point(self, u):
        return self.p0 + self.dir * u

    def normal(self, u):
        return self.n

    def u_at(self, xy):
        """The path coordinate of a point on (or beside) this run."""
        return (Vector(xy) - self.p0).dot(self.dir)


class Arc:
    """An anticlockwise arc about `c`, radius `r`, from `th0` to `th1`,
    faceted at the fixed stations k * FACET so arcs of different radii run
    parallel facet by facet."""

    def __init__(self, c, r, th0, th1):
        assert th1 > th0, (th0, th1)
        self.c, self.r, self.th0, self.th1 = Vector(c), r, th0, th1
        self.length = r * (th1 - th0)
        self.breaks = []
        k = math.floor(th0 / FACET) + 1
        while k * FACET < th1 - 1e-9:
            if k * FACET > th0 + 1e-9:
                self.breaks.append((k * FACET - th0) * r)
            k += 1
        self.breaks = tuple(self.breaks)

    def theta(self, u):
        return self.th0 + u / self.r

    def point(self, u):
        t = self.theta(u)
        return self.c + Vector((math.cos(t), math.sin(t))) * self.r

    def normal(self, u):
        t = self.theta(u)
        return -Vector((math.cos(t), math.sin(t)))

    def u_of(self, theta):
        return (theta - self.th0) * self.r


def offset(segs, d):
    """The same path moved outward by `d` (a trim's face proud of a wall);
    only tangent junctions survive this, which is all the house has."""
    out = []
    for s in segs:
        if isinstance(s, Straight):
            out.append(Straight(s.p0 - s.n * d, s.p1 - s.n * d))
        else:
            out.append(Arc(s.c, s.r + d, s.th0, s.th1))
    return out


def shell(name, coll, segs, z0, z1, openings, mats, base_below=None, closed=False,
          thick=T, variant=None, collide=True):
    """A closed solid of thickness `thick` along a path, inside on the path's
    left: two skins, top, bottom, ends if the path is open, and a real reveal
    round every opening. An opening is (u0, u1, z0, z1) in path length.
    Faces whose middle lies below `base_below` take the second material (the
    skirt). Corners are mitred, so a loop has no end faces at all."""
    offs, total = [], 0.0
    for s in segs:
        offs.append(total)
        total += s.length
    us = {0.0} if closed else {0.0, total}
    for s, o in zip(segs, offs):
        us.add(o)
        us.update(o + b for b in s.breaks)
    for u0, u1, oz0, oz1 in openings:
        assert 0.0 < u0 < u1 < total and z0 < oz0 < oz1 <= z1, (name, u0, u1, oz0, oz1)
        us.update((u0, u1))
    us = sorted(us)
    merged = [us[0]]
    for u in us[1:]:
        if u - merged[-1] > 1e-6:
            merged.append(u)
    us = merged
    zs = {z0, z1}
    if base_below is not None and z0 < base_below < z1:
        zs.add(base_below)
    for u0, u1, oz0, oz1 in openings:
        zs.update((oz0, oz1))
    zs = sorted(zs)
    nz = len(zs) - 1

    def seg_index(u):
        for i in range(len(segs) - 1, -1, -1):
            if u >= offs[i] - 1e-9:
                return i
        return 0

    plan = []        # (outer point, inner point) per path vertex
    for u in us:
        i = seg_index(u)
        local = u - offs[i]
        p, n = segs[i].point(local), segs[i].normal(local)
        if abs(local) < 1e-9 and (closed or i > 0):
            prev = segs[i - 1] if i > 0 else segs[-1]
            n_prev = prev.normal(prev.length)
            if (n_prev - n).length > 1e-6:
                n = (n_prev + n) / (1.0 + n_prev.dot(n))
        plan.append((p, p + n * thick))
    N = len(plan)
    nseg = N if closed else N - 1
    bm = bmesh.new()
    verts = {}

    def vert(k, j, side):
        key = (k % N, j, side)
        if key not in verts:
            p = plan[k % N][side]
            verts[key] = bm.verts.new((p.x, p.y, zs[j]))
        return verts[key]

    def u_mid(k):
        u_a = us[k]
        u_b = us[k + 1] if k + 1 < N else total
        return (u_a + u_b) / 2

    def in_opening(k, j):
        um, zm = u_mid(k), (zs[j] + zs[j + 1]) / 2
        return any(u0 < um < u1 and oz0 < zm < oz1 for u0, u1, oz0, oz1 in openings)

    def face(vs, zmid):
        f = bm.faces.new(vs)
        f.material_index = 1 if (base_below is not None and len(mats) > 1 and zmid < base_below) else 0

    for k in range(nseg):
        for j in range(nz):
            if in_opening(k, j):
                continue
            zm = (zs[j] + zs[j + 1]) / 2
            face((vert(k, j, 0), vert(k + 1, j, 0), vert(k + 1, j + 1, 0), vert(k, j + 1, 0)), zm)
            face((vert(k, j, 1), vert(k + 1, j, 1), vert(k + 1, j + 1, 1), vert(k, j + 1, 1)), zm)
        face((vert(k, 0, 0), vert(k + 1, 0, 0), vert(k + 1, 0, 1), vert(k, 0, 1)), zs[0])
        face((vert(k, nz, 0), vert(k + 1, nz, 0), vert(k + 1, nz, 1), vert(k, nz, 1)), zs[nz])
    if not closed:
        for k in (0, N - 1):
            for j in range(nz):
                face((vert(k, j, 0), vert(k, j + 1, 0), vert(k, j + 1, 1), vert(k, j, 1)), (zs[j] + zs[j + 1]) / 2)
    for u0, u1, oz0, oz1 in openings:
        k0 = min(range(N), key=lambda k: abs(us[k] - u0))
        k1 = min(range(N), key=lambda k: abs(us[k] - u1))
        j0, j1 = zs.index(oz0), zs.index(oz1)
        zm = (oz0 + oz1) / 2
        for j in range(j0, j1):
            face((vert(k0, j, 0), vert(k0, j, 1), vert(k0, j + 1, 1), vert(k0, j + 1, 0)), zm)
            face((vert(k1, j, 0), vert(k1, j + 1, 0), vert(k1, j + 1, 1), vert(k1, j, 1)), zm)
        for k in range(k0, k1):
            face((vert(k, j0, 0), vert(k + 1, j0, 0), vert(k + 1, j0, 1), vert(k, j0, 1)), zm)
            face((vert(k, j1, 0), vert(k, j1, 1), vert(k + 1, j1, 1), vert(k + 1, j1, 0)), zm)
    return finish(name, bm, coll, mats, variant=variant, collide=collide)


# --- openings on straight walls ------------------------------------------------

def opening_trim(prefix, coll, mat, axis, face_at, outward, a0, a1, z0, z1, variant, head=True, sill=True):
    """Chunky casing round an opening: jambs 3.5 cm proud, head and sill
    boards a centimetre prouder and a half-centimetre shallower, every board
    lapping 2 cm over the opening's edge, so no two share a face. `axis` is
    'x' when the opening's width runs along X (a wall facing +-Y). The
    street openings hang from the house's band and take no head."""
    def part(name, a_lo, a_hi, b_lo, b_hi, sunk, proud):
        lo, hi = sorted((face_at - sunk * outward, face_at + proud * outward))
        if axis == "x":
            return box(name, coll, mat, a_lo, a_hi, lo, hi, b_lo, b_hi, variant=variant, collide=False)
        return box(name, coll, mat, lo, hi, a_lo, a_hi, b_lo, b_hi, variant=variant, collide=False)

    part(f"{prefix}_jamb_a", a0 - JAMB, a0 + 0.02, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
    part(f"{prefix}_jamb_b", a1 - 0.02, a1 + JAMB, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
    if head:
        part(f"{prefix}_head", a0 - JAMB - 0.04, a1 + JAMB + 0.04, z1 - 0.02, z1 + JAMB, 0.010, 0.045)
    if sill:
        part(f"{prefix}_sill", a0 - JAMB - 0.04, a1 + JAMB + 0.04, z0 - SILL_T, z0 + 0.02, 0.010, 0.045)


def pane(name, coll, mat, axis, face_at, outward, a0, a1, z0, z1, variant, recess=0.08, thick=0.05):
    """A slab set in an opening, recessed into the wall, 2 cm into the
    reveals all round."""
    lo, hi = sorted((face_at - recess * outward, face_at - (recess + thick) * outward))
    if axis == "x":
        return box(name, coll, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, variant=variant)
    return box(name, coll, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, variant=variant)


def dress_opening(prefix, coll, m, axis, face_at, outward, a0, a1, z0, z1, variant, kind="window", head=True):
    """Casing and slab for one opening on a straight wall."""
    is_door = kind == "door"
    opening_trim(prefix, coll, m["trim"], axis, face_at, outward, a0, a1, z0, z1, variant,
                 head=head and not is_door, sill=not is_door)
    pane(f"{prefix}_{'door' if is_door else 'pane'}", coll, m["door" if is_door else "glass"],
         axis, face_at, outward, a0, a1, z0, z1, variant)


# --- openings on the rounded end ---------------------------------------------------

def arc_piece(name, coll, mat, arc, d_out, thick, th_a, th_b, z0, z1, variant, collide=False):
    """A curved board or slab following `arc` between two angles: its outer
    face `d_out` proud of the wall (negative: recessed into it), `thick`
    deep, faceted at the same stations as the wall."""
    return shell(name, coll, [Arc(arc.c, arc.r + d_out, th_a, th_b)], z0, z1, (), [mat],
                 thick=thick, variant=variant, collide=collide)


def dress_arc_opening(prefix, coll, m, arc, th_a, th_b, z0, z1, variant):
    """Jambs, sill and pane for a window on the rounded end; the band is its
    head. Widths along the wall's own radius, as angles."""
    j, lap, ext = JAMB / arc.r, 0.02 / arc.r, 0.04 / arc.r
    arc_piece(f"{prefix}_jamb_a", coll, m["trim"], arc, 0.035, 0.050, th_a - j, th_a + lap, z0 - 0.02, z1 + 0.02, variant)
    arc_piece(f"{prefix}_jamb_b", coll, m["trim"], arc, 0.035, 0.050, th_b - lap, th_b + j, z0 - 0.02, z1 + 0.02, variant)
    arc_piece(f"{prefix}_sill", coll, m["trim"], arc, 0.045, 0.055, th_a - j - ext, th_b + j + ext, z0 - SILL_T, z0 + 0.02, variant)
    arc_piece(f"{prefix}_pane", coll, m["glass"], arc, -0.08, 0.05, th_a - lap, th_b + lap, z0 - 0.02, z1 + 0.02, variant, collide=True)


# --- the house ----------------------------------------------------------------------

def perimeter(rounded):
    """The walls' path, anticlockwise from the south-west corner, and the
    index of each named run."""
    if not rounded:
        segs = [Straight((-HL, FRONT_Y), (HL, FRONT_Y)), Straight((HL, FRONT_Y), (HL, HD)),
                Straight((HL, HD), (-HL, HD)), Straight((-HL, HD), (-HL, FRONT_Y))]
        names = {"front": 0, "east": 1, "back": 2, "west": 3}
    else:
        segs = [Straight((-HL, FRONT_Y), (ROUND_C[0], FRONT_Y)),
                Arc(ROUND_C, ROUND_R, -math.pi / 2, math.pi / 2),
                Straight((ROUND_C[0], CAR_BACK_Y), (ADD_END_X, CAR_BACK_Y)),
                Straight((ADD_END_X, CAR_BACK_Y), (ADD_END_X, HD)),
                Straight((ADD_END_X, HD), (-HL, HD)), Straight((-HL, HD), (-HL, FRONT_Y))]
        names = {"front": 0, "arc": 1, "car_back": 2, "east": 3, "back": 4, "west": 5}
    return segs, names


def build_walls(coll, m, variant, prefix):
    """The variant's wall shell with every opening cut, and the casings and
    panes of the openings this variant does not share with the other (the
    east end). Returns the shared openings' descriptions for `build_shared`."""
    rounded = variant == "tell"
    segs, names = perimeter(rounded)
    offs, total = [], 0.0
    for s in segs:
        offs.append(total)
        total += s.length

    def u(run, xy):
        i = names[run]
        return offs[i] + segs[i].u_at(xy)

    openings = []
    # the street: the car's windows and the door, all hung from the band
    for a0, a1 in FRONT_WINDOWS:
        openings.append((u("front", (a0, FRONT_Y)), u("front", (a1, FRONT_Y)), SILL, HEAD))
    openings.append((u("front", (DOOR_X[0], FRONT_Y)), u("front", (DOOR_X[1], FRONT_Y)), FLOOR + THRESHOLD, HEAD))
    for a0, a1 in BACK_WINDOWS:
        openings.append((u("back", (a1, HD)), u("back", (a0, HD)), SILL, HEAD))
    for a0, a1 in END_WINDOWS:
        openings.append((u("west", (-HL, a1)), u("west", (-HL, a0)), SILL, HEAD))
    east = []
    if rounded:
        arc = segs[names["arc"]]
        for th_a, th_b in ARC_WINDOWS:
            openings.append((offs[names["arc"]] + arc.u_of(th_a), offs[names["arc"]] + arc.u_of(th_b), SILL, HEAD))
        east.append((u("east", (ADD_END_X, END_WINDOWS[1][0])), u("east", (ADD_END_X, END_WINDOWS[1][1])), SILL, HEAD))
    else:
        for a0, a1 in END_WINDOWS:
            east.append((u("east", (HL, a0)), u("east", (HL, a1)), SILL, HEAD))
    openings.extend(east)
    shell(f"{prefix}walls", coll, segs, -BELOW, WALL_TOP, openings, [m["walls"], m["skirt"]],
          base_below=SKIRT_TOP, closed=True, variant=variant)

    # this variant's own east-end dressings
    if rounded:
        arc = segs[names["arc"]]
        for k, (th_a, th_b) in enumerate(ARC_WINDOWS):
            dress_arc_opening(f"{prefix}arc{k}", coll, m, arc, th_a, th_b, SILL, HEAD, variant)
        a0, a1 = END_WINDOWS[1]
        dress_opening(f"{prefix}east0", coll, m, "y", ADD_END_X, 1, a0, a1, SILL, HEAD, variant)
        # the band runs on round the car's end and along its exposed back
        band = offset([Straight((-HL + 0.02, FRONT_Y), (ROUND_C[0], FRONT_Y)), arc,
                       Straight((ROUND_C[0], CAR_BACK_Y), (ADD_END_X + 0.02, CAR_BACK_Y))], 0.045)
        shell(f"{prefix}band", coll, band, BAND_Z0, BAND_Z0 + BAND_T, (), [m["trim"]], thick=0.055,
              variant=variant, collide=False)
        # the car's end gets no knee brace (a bar off the curved band read as
        # a flagpole in render); a post holds the roof's far corner over the
        # nook the short addition leaves
        box(f"{prefix}nook_post", coll, m["rails"], XE - 0.30 - POST, XE - 0.30, YE - 0.30 - POST, YE - 0.30,
            -BELOW - 0.01, EAVE + 0.02, variant=variant)
    else:
        for k, (a0, a1) in enumerate(END_WINDOWS):
            dress_opening(f"{prefix}east{k}", coll, m, "y", HL, 1, a0, a1, SILL, HEAD, variant)
        box(f"{prefix}band", coll, m["trim"], -HL + 0.02, HL - 0.02, FRONT_Y - 0.045, FRONT_Y + 0.01,
            BAND_Z0, BAND_Z0 + BAND_T, variant=variant, collide=False)
        for y in (FRONT_Y + 0.10, HD - 0.10):
            brace(f"{prefix}brace_e{'f' if y < 0 else 'b'}", coll, m, 1, y, variant)


def brace(name, coll, m, sx, y, variant, hl=HL, xe=XE):
    """A knee brace under the end overhang: a flat bar 8 cm thick, 10 cm
    deep, from 2 cm inside the wall up to 1 cm inside the soffit, its ends
    cut vertical so both stay buried."""
    x_wall, x_eave = sx * (hl - 0.02), sx * (xe - 0.10)
    z_wall, z_eave = HEAD - 0.30, EAVE + 0.01     # the foot clears the band on the tell's arc
    poly = [(x_wall, z_wall), (x_wall, z_wall + 0.10), (x_eave, z_eave + 0.10), (x_eave, z_eave)]
    if sx < 0:
        poly.reverse()
    return finish(name, prism_bm(poly, "y", y - 0.04, y + 0.04), coll, [m["rails"]], variant=variant, collide=False)


def hip_roof(name, coll, mat, variant, rect=ROOF):
    """The roof as one solid over the plan rectangle `rect`: a flat
    underside inside the soffit slab, the hip on top, vertical edges inside
    the fascia."""
    bm = bmesh.new()
    zb, ze = EAVE + ROOF_LIFT, EAVE + ROOF_EDGE
    x0, x1, y0, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # a centimetre inside the soffit's edges, so the two solids' vertical
    # edge faces share no plane (both edges stand inside the fascia)
    xe, ye = (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01
    c = [bm.verts.new(v) for v in ((cx - xe, cy - ye, zb), (cx + xe, cy - ye, zb), (cx + xe, cy + ye, zb), (cx - xe, cy + ye, zb))]
    e = [bm.verts.new(v) for v in ((cx - xe, cy - ye, ze), (cx + xe, cy - ye, ze), (cx + xe, cy + ye, ze), (cx - xe, cy + ye, ze))]
    rx = xe - ye
    rt = EAVE + ROOF_EDGE + ye * math.tan(PITCH)
    r = [bm.verts.new(v) for v in ((cx - rx, cy, rt), (cx + rx, cy, rt))]
    bm.faces.new(list(reversed(c)))
    for i in range(4):
        bm.faces.new((c[i], c[(i + 1) % 4], e[(i + 1) % 4], e[i]))
    bm.faces.new((e[0], e[1], r[1], r[0]))
    bm.faces.new((e[2], e[3], r[0], r[1]))
    bm.faces.new((e[1], e[2], r[1]))
    bm.faces.new((e[3], e[0], r[0]))
    return finish(name, bm, coll, [mat], variant=variant)


def build_shared(coll, m, variant, prefix):
    """Everything the photo and tell variants show alike: the roof, the
    west end's braces, the stovepipe, the street openings and the porch."""
    build_roof(coll, m, variant, prefix, ROOF, HL, FRONT_Y, HD, PIPE_AT)
    build_street(coll, m, variant, prefix, FRONT_Y, DOOR_X, FRONT_WINDOWS, HD, BACK_WINDOWS, END_WINDOWS, HL)
    build_porch(coll, m, variant, prefix, PORCH_X0, PORCH_X1, DECK_Y0, FRONT_Y, PR_X0, PR_X1, PR_Y1, ROOF[2])


def build_roof(coll, m, variant, prefix, rect, hl, front_y, back_y, pipe_at):
    """The broad low roof over the plan rectangle `rect`: soffit slab, hip
    solid, mitred fascia loop, the west end's two knee braces (the east
    end's are each variant's own) and the stovepipe through the front slope.
    `hl` is the walls' half length, `front_y`/`back_y` the walls the braces
    stand beside."""
    x0, x1, y0, y1 = rect
    box(f"{prefix}soffit", coll, m["tin"], x0, x1, y0, y1, EAVE, EAVE + SOFFIT_T, variant=variant)
    hip_roof(f"{prefix}roof", coll, m["tin"], variant, rect)
    xa, xb, ya, yb = x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04
    shell(f"{prefix}fascia", coll, [Straight((xa, ya), (xb, ya)), Straight((xb, ya), (xb, yb)),
                                    Straight((xb, yb), (xa, yb)), Straight((xa, yb), (xa, ya))],
          FASCIA_Z0, FASCIA_Z1, (), [m["fascia"]], closed=True, thick=FASCIA_T, variant=variant, collide=False)
    for y in (front_y + 0.10, back_y - 0.10):
        brace(f"{prefix}brace_w{'f' if y < 0 else 'b'}", coll, m, -1, y, variant, hl=hl, xe=x1)
    # the stovepipe through the front slope, with a cap
    px, py = pipe_at
    cy = (y0 + y1) / 2
    roof_z = EAVE + ROOF_EDGE + ((y1 - y0) / 2 - abs(py - cy)) * math.tan(PITCH)
    ring = [(px + 0.075 * math.cos(math.tau * i / 12), py + 0.075 * math.sin(math.tau * i / 12)) for i in range(12)]
    finish(f"{prefix}stovepipe", prism_bm(ring, "z", roof_z - 0.10, roof_z + 0.85), coll, [m["tin"]],
           variant=variant, collide=False)
    cap = [(px + 0.14 * math.cos(math.tau * i / 12), py + 0.14 * math.sin(math.tau * i / 12)) for i in range(12)]
    finish(f"{prefix}stovepipe_cap", prism_bm(cap, "z", roof_z + 0.83, roof_z + 0.89), coll, [m["tin"]],
           variant=variant, collide=False)


def build_street(coll, m, variant, prefix, front_y, door_x, front_windows, back_y, back_windows, end_windows, hl):
    """The street openings (hung from the band, no heads), the door, the
    back's windows and the west end's."""
    for k, (a0, a1) in enumerate(front_windows):
        dress_opening(f"{prefix}front{k}", coll, m, "x", front_y, -1, a0, a1, SILL, HEAD, variant, head=False)
    dress_opening(f"{prefix}door", coll, m, "x", front_y, -1, door_x[0], door_x[1], FLOOR + THRESHOLD, HEAD, variant, kind="door")
    for k, (a0, a1) in enumerate(back_windows):
        dress_opening(f"{prefix}back{k}", coll, m, "x", back_y, 1, a0, a1, SILL, HEAD, variant)
    for k, (a0, a1) in enumerate(end_windows):
        dress_opening(f"{prefix}west{k}", coll, m, "y", -hl, -1, a0, a1, SILL, HEAD, variant)


def build_porch(coll, m, variant, prefix, porch_x0, porch_x1, deck_y0, front_y, pr_x0, pr_x1, pr_y1, roof_y0):
    """The porch: deck, posts, rails, the tin lean-to roof with its fascia,
    and the steps. `roof_y0` is the main roof's front edge the porch roof
    tucks under."""
    # a yellow base 2 cm into the wall under a purple deck slab that
    # overhangs it a centimetre, a teal nosing hiding their joint
    base_top = FLOOR - 0.03
    box(f"{prefix}deck_base", coll, m["walls"], porch_x0, porch_x1, deck_y0, front_y + 0.02, -BELOW + 0.01, base_top, variant=variant)
    box(f"{prefix}deck", coll, m["deck"], porch_x0 - 0.01, porch_x1 + 0.01, deck_y0 - 0.01, front_y + 0.03,
        base_top - 0.01, FLOOR, variant=variant)
    box(f"{prefix}deck_nosing", coll, m["trim"], porch_x0 - 0.015, porch_x1 + 0.015, deck_y0 - 0.02, deck_y0 + 0.04,
        FLOOR - 0.05, FLOOR + 0.01, variant=variant, collide=False)
    # posts at the deck's front corners, 5 cm in from its edges, up into the porch roof
    post_y0 = deck_y0 + 0.05
    for tag, x0 in (("w", porch_x0 + 0.05), ("e", porch_x1 - 0.05 - POST)):
        top = porch_roof_z(post_y0 + POST / 2, roof_y0) - PR_T + 0.02
        box(f"{prefix}post_{tag}", coll, m["rails"], x0, x0 + POST, post_y0, post_y0 + POST, FLOOR - 0.02, top, variant=variant)
        # rails from 2 cm inside the post to 2 cm into the wall: a wide top
        # board and a mid rail, both a touch wider than the post
        xc = x0 + POST / 2
        y0, y1 = post_y0 + POST - 0.02, front_y + 0.02
        box(f"{prefix}rail_top_{tag}", coll, m["rails"], xc - 0.075, xc + 0.075, y0, y1,
            FLOOR + RAIL_H - 0.05, FLOOR + RAIL_H, variant=variant)
        box(f"{prefix}rail_mid_{tag}", coll, m["rails"], xc - 0.045, xc + 0.045, y0 + 0.01, y1 - 0.01,
            FLOOR + MID_RAIL - 0.04, FLOOR + MID_RAIL, variant=variant, collide=False)
    # the porch roof: a tin slab tucked 2 cm under the main fascia, falling
    # 3 degrees to the front, its own fascia on three sides
    y_back = roof_y0 + 0.02
    prof = [(y_back, PR_Z_BACK - PR_T), (y_back, PR_Z_BACK), (pr_y1, porch_roof_z(pr_y1, roof_y0)), (pr_y1, porch_roof_z(pr_y1, roof_y0) - PR_T)]
    finish(f"{prefix}porch_roof", prism_bm(prof, "x", pr_x0 + 0.02, pr_x1 - 0.02), coll, [m["tin"]], variant=variant)
    zf = porch_roof_z(pr_y1, roof_y0) + 0.02
    box(f"{prefix}porch_fascia_f", coll, m["fascia"], pr_x0, pr_x1, pr_y1 - 0.02, pr_y1 + PR_FASCIA / 4,
        zf - PR_FASCIA, zf, variant=variant, collide=False)
    # the side boards' front ends are buried in the front board and their
    # outer faces stand 5 mm inside its ends; their back ends go 2 cm into
    # the main fascia, where the part below it shows as a butt joint
    y_end = roof_y0 - 0.02
    for tag, x0 in (("w", pr_x0 + 0.005), ("e", pr_x1 - 0.005 - FASCIA_T)):
        side = [(pr_y1 + PR_FASCIA / 4 - 0.02, zf - PR_FASCIA), (pr_y1 + PR_FASCIA / 4 - 0.02, zf),
                (y_end, porch_roof_z(y_end, roof_y0) + 0.02), (y_end, porch_roof_z(y_end, roof_y0) + 0.02 - PR_FASCIA)]
        finish(f"{prefix}porch_fascia_{tag}", prism_bm(side, "x", x0, x0 + FASCIA_T), coll, [m["fascia"]],
               variant=variant, collide=False)
    # the steps: risers at y_k = front - (n - k) * GOING, the treads one
    # yellow block that laps 2 cm into the deck base (scenery), the narrow
    # ramp through the nosings the floor, teal nosing strips on each riser
    n = round(FLOOR / RISER)
    front = deck_y0
    ys = [front - (n - k) * GOING for k in range(1, n + 1)]
    prof = [(ys[0], -BELOW - 0.01)]
    for k in range(1, n):
        prof += [(ys[k - 1], k * RISER), (ys[k] if k < n - 1 else front + 0.02, k * RISER)]
    prof.append((front + 0.02, -BELOW - 0.01))
    finish(f"{prefix}steps", prism_bm(prof, "x", porch_x0 - 0.01, porch_x1 + 0.01), coll, [m["walls"]], variant=variant, collide=False)
    foot = front - n * GOING
    ramp = [(foot - 0.05, -BELOW - 0.02), (foot, 0.0), (front, FLOOR), (front + 0.06, -BELOW - 0.02)]
    finish(f"{prefix}step_ramp", prism_bm(ramp, "x", porch_x0 + 0.10, porch_x1 - 0.10), coll, [m["walls"]], variant=variant)
    for k in range(1, n):
        box(f"{prefix}step_nosing_{k}", coll, m["trim"], porch_x0 - 0.015, porch_x1 + 0.015, ys[k - 1] - 0.015, ys[k - 1] + 0.04,
            k * RISER - 0.05, k * RISER + 0.01, variant=variant, collide=False)


def porch_roof_z(y, roof_y0=-YE):
    """The porch roof's top surface at `y` (it falls to the front from
    where it tucks under the main roof's front edge, `roof_y0`)."""
    return PR_Z_BACK - (roof_y0 + 0.02 - y) * math.tan(PR_PITCH)


# --- the big car ------------------------------------------------------------------

def build_big(coll, m, variant="big", prefix="big_"):
    """The 14 m car with its lean-to: the car's walls as one closed shell
    (street, D-end, its exposed back, square west end), the band round the
    end to the lean-to, the broad roof over the car alone, the porch, and
    the lean-to as an open U of walls lapped into the car's back wall under
    its own tin roof."""
    segs = [Straight((-B_HL, B_FRONT_Y), (B_ROUND_C[0], B_FRONT_Y)),
            Arc(B_ROUND_C, ROUND_R, -math.pi / 2, math.pi / 2),
            Straight((B_ROUND_C[0], B_CAR_BACK_Y), (-B_HL, B_CAR_BACK_Y)),
            Straight((-B_HL, B_CAR_BACK_Y), (-B_HL, B_FRONT_Y))]
    offs, total = [], 0.0
    for s in segs:
        offs.append(total)
        total += s.length

    def u(i, xy):
        return offs[i] + segs[i].u_at(xy)

    arc = segs[1]
    openings = []
    for a0, a1 in B_FRONT_WINDOWS:
        openings.append((u(0, (a0, B_FRONT_Y)), u(0, (a1, B_FRONT_Y)), SILL, HEAD))
    openings.append((u(0, (B_DOOR_X[0], B_FRONT_Y)), u(0, (B_DOOR_X[1], B_FRONT_Y)), FLOOR + THRESHOLD, HEAD))
    for th_a, th_b in ARC_WINDOWS:
        openings.append((offs[1] + arc.u_of(th_a), offs[1] + arc.u_of(th_b), SILL, HEAD))
    for a0, a1 in B_CAR_END_WINDOWS:
        openings.append((u(3, (-B_HL, a1)), u(3, (-B_HL, a0)), SILL, HEAD))
    shell(f"{prefix}walls", coll, segs, -BELOW, WALL_TOP, openings, [m["walls"], m["skirt"]],
          base_below=SKIRT_TOP, closed=True, variant=variant)
    for k, (th_a, th_b) in enumerate(ARC_WINDOWS):
        dress_arc_opening(f"{prefix}arc{k}", coll, m, arc, th_a, th_b, SILL, HEAD, variant)
    band = offset([Straight((-B_HL + 0.02, B_FRONT_Y), (B_ROUND_C[0], B_FRONT_Y)), arc,
                   Straight((B_ROUND_C[0], B_CAR_BACK_Y), (B_LEAN_X1 + 0.02, B_CAR_BACK_Y))], 0.045)
    shell(f"{prefix}band", coll, band, BAND_Z0, BAND_Z0 + BAND_T, (), [m["trim"]], thick=0.055,
          variant=variant, collide=False)
    build_roof(coll, m, variant, prefix, B_ROOF, B_HL, B_FRONT_Y, B_CAR_BACK_Y, B_PIPE_AT)
    build_street(coll, m, variant, prefix, B_FRONT_Y, B_DOOR_X, B_FRONT_WINDOWS, None, (), B_CAR_END_WINDOWS, B_HL)
    build_porch(coll, m, variant, prefix, B_PORCH_X0, B_PORCH_X1, B_DECK_Y0, B_FRONT_Y, B_PR_X0, B_PR_X1, B_PR_Y1, B_ROOF[2])
    build_lean_to(coll, m, variant, prefix)


def lean_top_z(y):
    """The lean-to roof's top at `y`: it falls from the car's back wall."""
    return B_LEAN_TOP0 - (y - (B_CAR_BACK_Y - 0.02)) * math.tan(B_LEAN_PITCH)


def build_lean_to(coll, m, variant, prefix):
    """The room behind the big car: a U of walls (east end, back, west
    end) whose two ends lap 2 cm into the car's back wall, a foot a
    centimetre shallower than the car's; a tin roof with a flat soffit that
    thickens toward the car so its top falls 5.3 degrees from 3 cm under
    the car's soffit and passes under the car's fascia; a level back fascia
    and sloped side boards. The lean-to's eave is lower than the car's, so
    its windows take a lower head."""
    x0, x1, y1 = B_LEAN_X0, B_LEAN_X1, B_HD
    y_join = B_CAR_BACK_Y - 0.02
    y_eave = y1 + B_LEAN_OVER
    z_under = lean_top_z(y_eave) - B_LEAN_T
    segs = [Straight((x1, y_join), (x1, y1)), Straight((x1, y1), (x0, y1)), Straight((x0, y1), (x0, y_join))]
    offs, total = [], 0.0
    for s in segs:
        offs.append(total)
        total += s.length

    def u(i, xy):
        return offs[i] + segs[i].u_at(xy)

    a0, a1 = B_LEAN_END_WINDOW
    openings = [(u(0, (x1, a0)), u(0, (x1, a1)), SILL, B_LEAN_HEAD), (u(2, (x0, a1)), u(2, (x0, a0)), SILL, B_LEAN_HEAD)]
    for b0, b1 in B_BACK_WINDOWS:
        openings.append((u(1, (b1, y1)), u(1, (b0, y1)), SILL, B_LEAN_HEAD))
    shell(f"{prefix}lean_walls", coll, segs, -BELOW + 0.01, z_under + 0.03, openings, [m["walls"], m["skirt"]],
          base_below=SKIRT_TOP, closed=False, variant=variant)
    dress_opening(f"{prefix}lean_east", coll, m, "y", x1, 1, a0, a1, SILL, B_LEAN_HEAD, variant)
    dress_opening(f"{prefix}lean_west", coll, m, "y", x0, -1, a0, a1, SILL, B_LEAN_HEAD, variant)
    for k, (b0, b1) in enumerate(B_BACK_WINDOWS):
        dress_opening(f"{prefix}back{k}", coll, m, "x", y1, 1, b0, b1, SILL, B_LEAN_HEAD, variant)
    # the roof: its upper edge a centimetre short of the walls' ends inside
    # the car's wall, so the two share no plane there
    rx0, rx1 = x0 - B_LEAN_END_OVER, x1 + B_LEAN_END_OVER
    y_top = y_join - 0.01
    prof = [(y_top, z_under), (y_top, lean_top_z(y_top)), (y_eave, lean_top_z(y_eave)), (y_eave, z_under)]
    finish(f"{prefix}roof_lean", prism_bm(prof, "x", rx0, rx1), coll, [m["tin"]], variant=variant)
    box(f"{prefix}fascia_lean_b", coll, m["fascia"], rx0 - 0.04, rx1 + 0.04, y_eave - 0.04, y_eave + 0.04,
        z_under - 0.06, z_under + B_LEAN_T + 0.02, variant=variant, collide=False)
    for tag, bx in (("w", rx0 - 0.04 + 0.005), ("e", rx1 + 0.04 - 0.005 - FASCIA_T)):
        side = [(y_eave - 0.02, z_under - 0.06), (y_eave - 0.02, z_under + B_LEAN_T + 0.02),
                (y_join, lean_top_z(y_join) + 0.02), (y_join, lean_top_z(y_join) + 0.02 - (B_LEAN_T + 0.08))]
        finish(f"{prefix}fascia_lean_{tag}", prism_bm(side, "x", bx, bx + FASCIA_T), coll, [m["fascia"]],
               variant=variant, collide=False)


# --- reference ---------------------------------------------------------------

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
    outline("footprint_9p6x5p6", reference, -HL, HL, -HD, HD)
    outline("car_body_9p6x2p7", reference, -HL, HL, FRONT_Y, CAR_BACK_Y)
    outline("lot_16x9_along_street", reference, -LOT_W / 2, LOT_W / 2, LOT_Y0, LOT_Y0 + LOT_D)
    outline("car_body_14x2p7_big", reference, -B_HL, B_HL, B_FRONT_Y, B_CAR_BACK_Y)
    outline("lot_20x9_along_street_big", reference, -10.0, 10.0, LOT_Y0, LOT_Y0 + LOT_D)
    figure("figure_1p7m", reference, 3.6, -5.0)
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        reference.objects.link(marker)


# --- checks ------------------------------------------------------------------

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
    found = []
    for i in range(len(faces)):
        oi, ni, di, u0, u1, v0, v1 = faces[i]
        for j in range(i + 1, len(faces)):
            oj, nj, dj, w0, w1, x0, x1 = faces[j]
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
                found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def report(variant):
    bpy.context.view_layer.update()
    objs = variant_objects(variant)
    tris = triangles(objs)
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    print(f"{PROP}: {variant}: {len(objs)} parts, {tris} triangles, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, z {min(zs):.2f}..{max(zs):.2f}")
    pairs = coplanar_pairs(objs)
    print(f"{PROP}: {variant}: {len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    return tris


# --- renders -----------------------------------------------------------------

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

    ground = mat("_ground", (0.42, 0.33, 0.22))       # the photo's bark mulch
    walk = mat("_walk", (0.62, 0.58, 0.55))           # the flagstone walk
    lane = mat("_lane", (0.30, 0.30, 0.32))
    ink = mat("_ink", (0.02, 0.02, 0.02))
    box("_ground", stage, ground, -60, 60, -60, 60, -0.30, -0.01, collide=False)
    box("_walk", stage, walk, -8.0, 8.0, LOT_Y0 - 0.6, LOT_Y0 + 1.6, -0.30, -0.005, collide=False)
    box("_lane", stage, lane, -60, 60, LOT_Y0 - 8.0, LOT_Y0 - 1.0, -0.30, 0.0, collide=False)
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    figures = [figure("_figure_0", stage, 3.6, -5.0, mat=fig)]

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
        print(f"{PROP}: rendered {scene.render.filepath}")

    # the photograph's view: straight on from across the street at eye
    # height, then a three-quarter, then close beside the figure
    show_variant("photo")
    shoot("photo_street", (DOOR_C, -17.0, 1.55), (DOOR_C, 0.0, 1.7), lens=30)
    shoot("photo_three_quarter", (13.0, -14.0, 1.7), (0.0, -1.0, 1.9), lens=32)
    shoot("photo_with_figure", (6.5, -9.5, 1.6), (1.2, -2.6, 1.6), lens=35)
    shoot("photo_east_elevation", (40.0, 0.0, 1.6), (0.0, 0.0, 1.6), ortho=9.0)
    # the tell: the same street view, then its clue from the back and the
    # side, and its end elevation
    show_variant("tell")
    shoot("tell_street", (DOOR_C, -17.0, 1.55), (DOOR_C, 0.0, 1.7), lens=30)
    shoot("tell_clue_back", (13.5, 9.5, 1.7), (3.0, -0.5, 1.9), lens=32)
    shoot("tell_clue_side", (15.0, -6.5, 1.6), (3.5, -1.2, 1.9), lens=35)
    shoot("tell_east_elevation", (40.0, 0.0, 1.6), (0.0, 0.0, 1.6), ortho=9.0)
    shoot("tell_plan_roof_on", (0.0, -1.0, 60.0), (0.0, -1.0, 0.0), size=(1200, 1000), ortho=17.0)
    # the big car from the street, a three-quarter, and its lean-to and
    # rounded end from behind
    show_variant("big")
    shoot("big_street", (B_DOOR_C, -21.0, 1.55), (B_DOOR_C, 0.0, 1.7), lens=30)
    shoot("big_three_quarter", (16.0, -17.0, 1.7), (0.0, -1.0, 1.9), lens=32)
    shoot("big_back_three_quarter", (16.0, 11.0, 1.7), (2.0, 0.0, 1.8), lens=32)
    # plans with a metre grid and a 5 m bar, the roof off so the walls,
    # the porch and the tell's D-end and nook show
    for o in figures:
        bpy.data.objects.remove(o, do_unlink=True)
    def base_name(o):
        for pre in ("tell_", "big_"):
            if o.name.startswith(pre):
                return o.name[len(pre):]
        return o.name

    roof_parts = [o for o in bpy.data.collections["export"].all_objects
                  if base_name(o).startswith(("soffit", "roof", "fascia", "stovepipe", "porch_roof", "porch_fascia"))]
    for gx in range(-8, 9):
        box(f"_grid_x{gx}", stage, ink, gx - 0.015, gx + 0.015, -7.0, 5.0, -0.012, -0.003, collide=False)
    for gy in range(-7, 6):
        box(f"_grid_y{gy}", stage, ink, -8.0, 8.0, gy - 0.015, gy + 0.015, -0.012, -0.003, collide=False)
    box("_bar", stage, ink, -7.5, -2.5, -6.4, -6.2, -0.012, 0.03, collide=False)
    for k in range(6):
        box(f"_bar_tick{k}", stage, ink, -7.5 + k - 0.03, -7.5 + k + 0.03, -6.7, -5.9, -0.012, 0.03, collide=False)
    curve = bpy.data.curves.new("_label", "FONT")
    curve.body = "5 m bar, 1 m grid"
    curve.size = 0.5
    curve.align_x = "LEFT"
    label = bpy.data.objects.new("_label", curve)
    label.location = (-2.0, -6.5, 0.02)
    curve.materials.append(ink)
    stage.objects.link(label)
    for v in VARIANTS:
        show_variant(v)
        for o in roof_parts:
            o.hide_render = True
        shoot(f"{v}_plan_roof_off", (0.0, -1.0, 60.0), (0.0, -1.0, 0.0), size=(1200, 1000),
              ortho=19.0 if v == "big" else 17.0)
    show_variant("photo")


# --- main ----------------------------------------------------------------------

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

    m = mats()
    tell = bpy.data.collections.new("variant_tell")
    export.children.link(tell)
    build_walls(export, m, "photo", "")
    build_shared(export, m, "photo", "")
    build_walls(tell, m, "tell", "tell_")
    # the tell's linked copies of what the two share
    shared = [o for o in export.objects if o.get("kyt_variant") == "photo"
              and not o.name in ("walls", "band") and not o.name.startswith(("east", "brace_e"))]
    for src in shared:
        dup = src.copy()
        dup.name = f"tell_{src.name}"
        dup["kyt_variant"] = "tell"
        tell.objects.link(dup)
    big = bpy.data.collections.new("variant_big")
    export.children.link(big)
    build_big(big, mats("big_"))
    build_reference(reference)
    bpy.context.view_layer.update()
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    print(f"{PROP}: car {L:.1f} x {CAR_W:.1f} m, house {L:.1f} x {D:.1f} m, walls {T:.2f} thick, floor {FLOOR:.2f}, "
          f"sill {SILL:.2f}, head {HEAD:.2f}, eave {EAVE:.2f}, ridge top {RIDGE_TOP:.2f} "
          f"(pitch {math.degrees(PITCH):.0f} deg, overhang {OVER:.2f}), porch {PORCH_W:.1f} x {PORCH_D:.1f} m, "
          f"rounded end R {ROUND_R:.2f} at x {ROUND_C[0]:.2f}, addition to x {ADD_END_X:.2f}; "
          f"big: car {B_L:.1f} x {CAR_W:.1f} m, lean-to {B_LEAN_X1 - B_LEAN_X0:.2f} x {B_LEAN_D:.1f} m behind, "
          f"house {B_L:.1f} x {B_D:.1f} m, lean-to eave {lean_top_z(B_HD + B_LEAN_OVER) - B_LEAN_T:.2f}")
    for v in VARIANTS:
        report(v)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1])


main()
