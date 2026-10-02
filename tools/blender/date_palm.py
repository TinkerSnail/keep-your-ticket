"""Build the giant date palm, Phoenix canariensis, in its Blender file.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/date_palm.blend --python tools/blender/date_palm.py -- [--replace] [--save]

After Christina's photo (2026-09-29, "lets make a giant centerpiece date palm",
`documentation/reference/date_palm/canary_date_palm_front_yard.webp`): a thick
pineapple trunk of diamond leaf scars, swelling a little into the nut under
the crown, and a great dense dome of feather fronds, the young ones rising,
the mature ones arching out, the old ones hanging, a few snapped down. Drawn
the park's cartoony way (`prop-pipeline.md`, Standards applied): big chunky
pieces, the leaflets cut in the texture, not the geometry.

What it makes, the palm crown's editable pieces (`add_courses.py`):
- `authored/courses`: a Bezier curve per frond, `course_<kind>_<i>`. Move its
  points to bend that frond.
- `authored/blades`: one blade per kind (spear, young, mature, old, stub),
  lying along +Y from its base at y = 0, width along X, the two halves folded
  up into a V from the midrib at x = 0. Every frond of a kind is its blade bent
  along its course (`kyt_course_blade`), so reshaping `blade_mature` reshapes
  all the mature fronds.
- `export`: the fronds; `trunk`, the diamond scars as low pyramids, each its
  own facet group so the grooves stay crisp; `heart`, the crown's core the
  fronds leave from. `plant_base` in `reference` is the soil line.

`--replace` removes everything this script made (courses, blades, fronds,
trunk, heart) and builds them again; it refuses once a canvas PSD exists,
which would be her painting. Without `--save` the file is not written.

    ... -- --paint [--save]

after `unwrap_blades.py` and `paint_canvas.py --leaflets`: paints the trunk's
diamond tiles into its island of `<prop>_colour.png` and shades each feather
blade dark at the rachis to light at the leaflet tips. For an unpainted
canvas only (run `paint_canvas.py --leaflets --overwrite` first to repeat it).
"""

import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_courses  # noqa: E402  (the course and blade helpers)

NAME = "date_palm"
SEED = 1847

# The trunk. Its top, where the crown sits, is SEAT above the soil. The photo's
# palm has a crown as tall as its bare trunk and wider than the house's gable;
# "giant" takes it to about 12.5 m tall and 14 m across, a crown seat of 6.5 m.
SEAT = 6.5
TRUNK_R = 0.66  # the shaft's radius between the flare and the nut
FLARE = (0.36, 0.5)  # the root flare: how much wider at the soil, and how fast it goes (m)
NUT = (0.16, SEAT - 0.55, 0.6)  # the swelling under the crown: how much, where, how long
TOP_CLOSE = 0.16  # the trunk narrows this much into the heart
# The pineapple (her "it needs this bulge thing", 2026-09-29, with a photo,
# `documentation/reference/date_palm/pineapple_bulge.webp`): the trimmed frond
# bases make a knob under the crown about 1.7 times the neck below it, tucked
# in sharply at its foot and rounding up into the fronds, its scars big cut
# boots standing well proud. How much wider, where its widest is, how far it
# reaches below that and above; the lowest fronds leave its upper shoulder.
BULGE = (0.45, SEAT - 2.1, 0.8, 1.1)
# The bulge's boots, as the photo's: more round than the shaft's scars, a
# little shorter, standing well proud and hanging lower in the middle.
BULGE_AROUND, BULGE_PITCH = 16, 0.13
BULGE_RELIEF, BULGE_SAG = 0.16, 0.35
BULGE_TUCK = 0.05  # at its foot and top the bulge dives this far inside the shaft
# The shadow under the bulge (her "shadow under the bulge ledge", 2026-09-29),
# painted, so it shows whatever the sun does: the neck darkest right under the
# ledge, times SHADOW's colour there, lifting over its metres down; the bulge's
# own boots darker the more they face down, times BOOT_SHADE at straight down.
# Warm, so the sky's sheen doesn't turn the shade blue (a first, grey 0.42 was
# too faint and read cold). Each shadowed row wears a tile of its own, laid
# out TILE_COLS to a row of the trunk's island.
SHADOW = ((0.34, 0.27, 0.22), 0.75)
BOOT_SHADE = (0.46, 0.38, 0.32)
TILE_COLS = 4
AROUND = 10  # diamond scars round the trunk
PITCH = 0.14  # rows of the diamond lattice; a scar is two rows tall
BURIED = 0.3  # the lattice starts this far under the soil
RELIEF = (0.035, 0.1)  # how proud a scar's middle stands: low on the trunk, and in the nut
SAG = 0.22  # a scar's middle sits this share of a row low, so its lower face is the steeper
# Below the first height every scar is weathered, above the second fresh: the
# bulge's boots are all fresh cuts, the trunk under it weathered.
FRESH = (BULGE[1] - BULGE[2] - 0.2, BULGE[1] - BULGE[2] + 0.4)

# The fronds, youngest first. `count` of each kind; `length` (m), `half` (the
# blade's half-width at its widest, m) and `fold` (degrees each half rises from
# the midrib, the V of a date palm's leaflets). Colours are sRGB, the canvas's
# starting fill. Her "lets do fewer fronds but larger" (2026-09-30): 40 fronds,
# a quarter longer and wider (it had 69: 3 spear, 10 young, 38 mature, 18 old;
# the mature 6.8 m long, 0.82 m half-width).
KINDS = {
    "spear": dict(count=2, length=4.25, half=0.25, fold=12, colour=(0.62, 0.72, 0.32)),
    "young": dict(count=6, length=6.75, half=0.78, fold=26, colour=(0.38, 0.6, 0.2)),
    "mature": dict(count=22, length=8.5, half=1.02, fold=28, colour=(0.2, 0.42, 0.15)),
    "old": dict(count=10, length=8.0, half=0.95, fold=30, colour=(0.4, 0.46, 0.16)),
    "stub": dict(count=12, length=0.75, half=0.17, fold=35, colour=(0.66, 0.5, 0.3)),
}
HEART_COLOUR = (0.56, 0.47, 0.27)
TRUNK_COLOUR = (0.6, 0.5, 0.38)
STATIONS = 16  # rows along a feather blade
GOLDEN = math.radians(137.508)
RISE = (72.0, -18.0)  # a frond's first heading above level: the youngest, the oldest (degrees)
BEND = (14.0, 48.0)  # how far it arches down along its length: the youngest, the oldest
LOWEST = -86.0  # no frond points further down than this
SNAPPED = 3  # the oldest fronds this many snapped and hanging (the photo's lower left)
# Where the fronds leave the trunk: the youngest's base, the oldest's. Her "let
# the crown start further down the trunk a little like the example so it makes
# more of a spray" (2026-09-29): the photo's fronds leave a tall head, not a
# knot at the top, so the old ones come off well down the nut (it was 0.7 m).
ATTACH = (SEAT + 0.35, SEAT - 1.3)
BURY = 0.18  # a frond's base sits this far inside the trunk's surface
HEART = (0.62, 0.85, 0.12)  # the heart's radius, its squash, and how far above the seat its middle is


def srgb(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(name, colour, rough=0.9):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        lin = srgb(colour)
        mat.diffuse_color = (*lin, 1.0)
        mat.use_backface_culling = False
        bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
            bsdf.inputs["Roughness"].default_value = rough
    return mat


def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def shaft_radius(z):
    r = TRUNK_R + FLARE[0] * math.exp(-max(z, -0.4) / FLARE[1])
    r += NUT[0] * math.exp(-((z - NUT[1]) / NUT[2]) ** 2)
    return r - TOP_CLOSE * smoothstep(SEAT - 0.3, SEAT + 0.1, z)


def trunk_radius(z):
    """The trunk's outside, the bulge included: where fronds and stubs start."""
    return shaft_radius(z) + BULGE[0] * bulge(z)


def bulge(z):
    """0 off the bulge, 1 at its widest: full and tucking in sharply below,
    rounding off more slowly above."""
    if z < BULGE[1]:
        s = (BULGE[1] - z) / BULGE[2]
        return max(0.0, 1.0 - s ** 3) ** 0.5 if s < 1.0 else 0.0
    s = (z - BULGE[1]) / BULGE[3]
    return max(0.0, 1.0 - s * s) ** 0.7 if s < 1.0 else 0.0


def relief(z):
    return RELIEF[0] + (RELIEF[1] - RELIEF[0]) * smoothstep(1.0, NUT[1], z)


# ---------------------------------------------------------------- blades

def blade_width(kind, t):
    """The blade's half-width at share t of the way along. A feather frond is
    narrow where its spines are, widest a little before halfway, and tapers
    to a narrow tip; the spear is a closed frond, a slim point."""
    half = KINDS[kind]["half"]
    if kind == "spear":
        return half * max(0.08, math.sin(math.pi * min(t, 0.999)) ** 0.6)
    if kind == "stub":
        return half * (1.0 - 0.35 * t)
    if t < 0.45:
        return half * (0.22 + 0.78 * smoothstep(0.02, 0.45, t))
    return half * max(0.05, math.cos((t - 0.45) / 0.55 * math.pi / 2) ** 0.75)


def make_blade(kind):
    k = KINDS[kind]
    stations = 4 if kind == "stub" else STATIONS
    rise = math.tan(math.radians(k["fold"]))
    verts, faces = [], []
    for i in range(stations):
        t = i / (stations - 1)
        w = blade_width(kind, t)
        y = k["length"] * t
        verts += [(-w, y, w * rise), (0.0, y, 0.0), (w, y, w * rise)]
        if i:
            a = 3 * (i - 1)
            faces += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
    me = bpy.data.meshes.new(f"blade_{kind}")
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = verts[me.loops[li].vertex_index]
            uv.data[li].uv = (0.5 + co[0] / k["length"], co[1] / k["length"])
    me.materials.append(material(f"date_{kind}", k["colour"]))
    obj = bpy.data.objects.new(f"blade_{kind}", me)
    return obj


# ---------------------------------------------------------------- courses

def heading(elevation, azimuth):
    e, a = math.radians(elevation), azimuth
    return Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))


def course_points(start, azimuth, rise, bend, length, snap=None, count=7):
    """Points along a frond from `start`: it leaves at `rise` degrees above
    level and arches down by `bend` degrees over its length, more toward the
    tip. A snapped frond (`snap`, (share along, degrees)) folds down there."""
    pts = [Vector(start)]
    step = length / (count - 1)
    for i in range(count - 1):
        s = (i + 0.5) / (count - 1)
        e = rise - bend * s ** 1.6
        if snap is not None:
            e -= snap[1] * smoothstep(snap[0] - 0.06, snap[0] + 0.06, s)
        e = max(e, LOWEST)
        pts.append(pts[-1] + heading(e, azimuth) * step)
    return pts


def add_course(name, pts, coll):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 12
    spline = cu.splines.new("BEZIER")
    spline.bezier_points.add(len(pts) - 1)
    for bp, p in zip(spline.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, cu)
    coll.objects.link(obj)
    return obj


def frond_plan(rng):
    """(name, kind, points) for every frond: the live ones in a golden-angle
    spiral, youngest at the top and rising, oldest low on the nut and hanging;
    then the ring of stubs below them, old frond bases cut back."""
    order = [kind for kind in ("spear", "young", "mature", "old") for _ in range(KINDS[kind]["count"])]
    n = len(order)
    counts, plan = {}, []
    for k, kind in enumerate(order):
        u = k / (n - 1)
        azimuth = k * GOLDEN + math.radians(rng.uniform(-8, 8))
        rise = RISE[0] + (RISE[1] - RISE[0]) * u ** 0.95 + rng.uniform(-5, 5)
        bend = BEND[0] + (BEND[1] - BEND[0]) * u ** 1.3 + rng.uniform(-6, 6)
        length = KINDS[kind]["length"] * rng.uniform(0.93, 1.06)
        z = ATTACH[0] + (ATTACH[1] - ATTACH[0]) * u
        r = max(0.36, trunk_radius(min(z, SEAT)) - BURY)
        start = (r * math.cos(azimuth), r * math.sin(azimuth), z)
        snap = None
        if k >= n - SNAPPED * 2 and (n - k) % 2 == 0:  # every other of the oldest
            snap = (rng.uniform(0.45, 0.6), rng.uniform(30, 45))
        i = counts[kind] = counts.get(kind, -1) + 1
        plan.append((f"{kind}_{i}", kind, course_points(start, azimuth, rise, bend, length, snap)))
    for i in range(KINDS["stub"]["count"]):
        azimuth = 2 * math.pi * (i + 0.5 * (i % 2)) / KINDS["stub"]["count"] + math.radians(rng.uniform(-6, 6))
        z = ATTACH[1] - 0.15 - 0.28 * (i % 2)  # the cut-back bases, under the live fronds
        r = trunk_radius(z) - 0.12
        start = (r * math.cos(azimuth), r * math.sin(azimuth), z)
        plan.append((f"stub_{i}", "stub", course_points(start, azimuth, rng.uniform(18, 32), 6,
                                                       KINDS["stub"]["length"], count=3)))
    return plan


# ---------------------------------------------------------------- trunk

def scars(verts, faces, uvs, z0, rows, pitch, around, radius, proud, sag, tile_of, skip=None, along_normal=False):
    """One lattice of diamond scars into `verts`, `faces` and `uvs`. The rows
    alternate half a scar round, so each scar's left and right corners are on
    one row and its top and bottom on the rows either side; its middle stands
    `proud(z)` out and `sag` of a row low, so its lower face is the steeper.
    Out is straight from the axis, or with `along_normal` square to the
    profile, so on the bulge's underside the boots point down. Every scar has
    its own corners (the grooves stay sharp) and wears the tile `tile_of(z)`
    gives; the middle's place on the tile is the trunk's, so the painted lip
    lies on the crease. Rows `skip(z)` covers are left out."""
    step = 2 * math.pi / around
    z_of = [z0 + j * pitch for j in range(rows + 1)]

    def lattice(j, i):
        a = (i + 0.5 * (j % 2)) * step
        r = radius(z_of[j])
        return Vector((r * math.cos(a), r * math.sin(a), z_of[j]))

    for j in range(rows + 1):
        z = z_of[j]
        if skip is not None and skip(z):
            continue
        slope = (radius(z + 0.01) - radius(z - 0.01)) / 0.02
        for i in range(around):
            a = (i + 0.5 + 0.5 * (j % 2)) * step
            tile = tile_of(j, z)
            radial = Vector((math.cos(a), math.sin(a), 0.0))
            out = (radial - Vector((0, 0, slope))).normalized() if along_normal else radial
            mid = radial * radius(z) + Vector((0, 0, z - sag * pitch)) + out * proud(z)
            corners = {"left": lattice(j, i), "right": lattice(j, i + 1), "mid": mid}
            if j + 1 <= rows:
                corners["top"] = lattice(j + 1, i + j % 2)
            if j >= 1:
                corners["bottom"] = lattice(j - 1, i + j % 2)
            base = len(verts)
            keys = list(corners)
            verts += [corners[key] for key in keys]
            at = {key: base + n for n, key in enumerate(keys)}
            ring = [key for key in ("top", "left", "bottom", "right") if key in corners]
            pairs = list(zip(ring, ring[1:] + ring[:1]))
            if len(ring) < 4:  # a half scar at either end: no face across its open side
                pairs = [p for p in pairs if set(p) != {"left", "right"}]
            for p, q in pairs:
                tri = (at["mid"], at[p], at[q])
                n = (verts[tri[1]] - verts[tri[0]]).cross(verts[tri[2]] - verts[tri[0]])
                if n.dot(out) < 0:
                    tri = (tri[0], tri[2], tri[1])
                faces.append(tri)
                uvs.append([tile_uv(tile, keys[v - base]) for v in tri])
    return z_of, lattice


TILE_INSET = 0.03
CORNER_UV = {"left": (0.0, 0.5), "right": (1.0, 0.5), "top": (0.5, 1.0), "bottom": (0.5, 0.0),
             "mid": (0.5, 0.5 - SAG * 0.5)}


# The trunk island's grid of tiles, set by `build_trunk`: columns, rows, and
# each tile's cell.
GRID = {"cols": 2, "rows": 2, "cell": {0: 0, 1: 1, 2: 2, 3: 3}}


def tile_uv(tile, key):
    u, v = CORNER_UV[key]
    u = TILE_INSET + (1 - 2 * TILE_INSET) * u
    v = TILE_INSET + (1 - 2 * TILE_INSET) * v
    cell, cols = GRID["cell"][tile], GRID["cols"]
    return ((cell % cols + u) / cols, (cell // cols + v) / GRID["rows"])


def ledge_height():
    """Where the bulge's underside comes out past the shaft's scars."""
    z = BULGE[1] - BULGE[2]
    while z < BULGE[1] and BULGE[0] * bulge(z) - BULGE_TUCK <= relief(z):
        z += 0.005
    return z


def build_trunk(rng):
    """The diamond scars of the shaft, and over them the bulge's own ring of
    boots: more of them round than the shaft's, standing further out, the
    bulge's surface diving `BULGE_TUCK` inside the shaft at its foot and top so
    the two never share a face. Shaft rows the bulge covers are left out. One
    object; its tiles on the canvas are fresh A and B, weathered A and B, and
    one per row in the bulge's shadow (`SHADOW`, `BOOT_SHADE`), recorded on the
    object for `--paint` (`kyt_trunk_tiles`). Weathered B takes the grid's last
    cell, so the island's box is always the whole grid."""
    verts, faces, uvs = [], [], []

    def covered(z):
        return all(BULGE[0] * bulge(zz) - BULGE_TUCK > relief(zz) + 0.02 for zz in (z - PITCH, z + PITCH))

    rows = int(math.floor((SEAT + BURIED) / PITCH))
    low, high = BULGE[1] - BULGE[2], BULGE[1] + BULGE[3]
    bulge_rows = max(2, round((high - low) / BULGE_PITCH))
    bulge_pitch = (high - low) / bulge_rows

    def bulge_radius(z):
        return shaft_radius(z) + BULGE[0] * bulge(z) - BULGE_TUCK

    specs = [dict(kind="fresh", variant=0), dict(kind="fresh", variant=1),
             dict(kind="weathered", variant=0), dict(kind="weathered", variant=1)]
    ledge = ledge_height()
    neck, boots = {}, {}
    for j in range(rows + 1):
        z = -BURIED + j * PITCH
        # Up a scar (v 0 to 1) the shadow's share of the way lifted is a - b v.
        a, b = (ledge - z + PITCH) / SHADOW[1], 2 * PITCH / SHADOW[1]  # t: 0 dark, 1 lifted
        if z < BULGE[1] and a - b < 1.0 and not covered(z):
            neck[j] = len(specs)
            specs.append(dict(kind="weathered", variant=0, grad=[round(a, 4), round(b, 4)]))
    for k in range(bulge_rows + 1):
        z = low + k * bulge_pitch
        slope = (bulge_radius(z + 0.01) - bulge_radius(z - 0.01)) / 0.02
        down = slope / math.hypot(1.0, slope)  # 0 facing level, 1 straight down
        if down > 0.2:
            boots[k] = len(specs)
            specs.append(dict(kind="fresh", variant=0, shade=round(min(1.0, (down - 0.2) / 0.6), 4)))
    grid_rows = -(-len(specs) // TILE_COLS)
    last = TILE_COLS * grid_rows - 1
    cell = {0: 0, 1: 1, 2: 2, 3: last}
    cell.update({t: c for t, c in zip(range(4, len(specs)), range(3, last))})
    GRID.update(cols=TILE_COLS, rows=grid_rows, cell=cell)

    def shaft_tile(j, z):
        fresh = rng.random() < smoothstep(FRESH[0], FRESH[1], z)
        variant = rng.randrange(2)  # drawn on every row, so the unshadowed keep their tiles
        return neck.get(j, (0 if fresh else 2) + variant)

    def bulge_tile(k, z):
        variant = rng.randrange(2)
        return boots.get(k, variant)

    z_of, lattice = scars(verts, faces, uvs, -BURIED, rows, PITCH, AROUND, shaft_radius, relief, SAG,
                          shaft_tile, skip=covered)
    # Close the top under the heart: a fan from the last row to the axis.
    centre = len(verts)
    verts.append(Vector((0.0, 0.0, z_of[rows] + 0.05)))
    for i in range(AROUND):
        a, b = len(verts), len(verts) + 1
        verts += [lattice(rows, i), lattice(rows, i + 1)]
        faces.append((centre, b, a))
        uvs.append([tile_uv(0, "mid"), tile_uv(0, "right"), tile_uv(0, "left")])

    scars(verts, faces, uvs, low, bulge_rows, bulge_pitch, BULGE_AROUND, bulge_radius,
          lambda z: BULGE_RELIEF * bulge(z) ** 0.5, BULGE_SAG, bulge_tile, along_normal=True)

    me = bpy.data.meshes.new("trunk")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for poly, face_uv in zip(me.polygons, uvs):
        for li, co in zip(poly.loop_indices, face_uv):
            uv.data[li].uv = co
    me.shade_smooth()
    me.materials.append(material("date_trunk", TRUNK_COLOUR))
    obj = bpy.data.objects.new("trunk", me)
    obj["kyt_trunk_tiles"] = json.dumps(dict(cols=GRID["cols"], rows=GRID["rows"],
                                             tiles=[dict(spec, cell=cell[t]) for t, spec in enumerate(specs)]))
    print(f"date_palm: trunk tiles {GRID['cols']} by {GRID['rows']}: 4 plain, {len(neck)} neck rows and "
          f"{len(boots)} bulge rows in shadow; the ledge at {ledge:.2f} m")
    return obj


def build_heart():
    """The crown's core the fronds leave from: a squashed ball, its own
    unwrap round and up."""
    radius, squash, lift = HEART
    seg, rings = 12, 6
    verts, faces, uvs = [], [], []
    for r in range(rings + 1):
        polar = math.pi * r / rings
        for s in range(seg + 1):
            a = 2 * math.pi * s / seg
            verts.append((radius * math.sin(polar) * math.cos(a), radius * math.sin(polar) * math.sin(a),
                          SEAT + lift + radius * squash * math.cos(polar)))
    for r in range(rings):
        for s in range(seg):
            a = r * (seg + 1) + s
            faces.append((a, a + seg + 1, a + seg + 2, a + 1))
    me = bpy.data.meshes.new("heart")
    me.from_pydata(verts, [], faces)
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = ((vi % (seg + 1)) / seg, 1.0 - (vi // (seg + 1)) / rings)
    me.shade_smooth()
    me.materials.append(material("date_heart", HEART_COLOUR))
    return bpy.data.objects.new("heart", me)


# ---------------------------------------------------------------- build

def owned():
    names = {"trunk", "heart"} | {f"blade_{k}" for k in KINDS}
    objs = [o for o in bpy.data.objects if o.name in names]
    for coll in ("courses",):
        if coll in bpy.data.collections:
            objs += list(bpy.data.collections[coll].objects)
    objs += [o for o in bpy.data.collections["export"].objects if o.get("kyt_course_blade")]
    return objs


def build(replace):
    folder = os.path.join(root(), "assets", "source", "textures", NAME)
    if replace:
        if os.path.exists(os.path.join(folder, f"{NAME}_colour.psd")):
            raise SystemExit("date_palm: a canvas PSD exists (her painting); not replacing the palm")
        for obj in owned():
            data = obj.data
            bpy.data.objects.remove(obj)
            if data is not None and data.users == 0:
                (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.curves).remove(data)
    elif owned():
        raise SystemExit("date_palm: the palm is already built; --replace builds it again")
    rng = random.Random(SEED)
    courses = add_courses.child_collection("authored", "courses")
    blades_coll = add_courses.child_collection("authored", "blades")
    export = bpy.data.collections["export"]

    blades, x = {}, 9.0
    for kind in KINDS:
        obj = make_blade(kind)
        obj.location = (x + KINDS[kind]["half"], 0.0, 0.0)
        x += 2 * KINDS[kind]["half"] + 1.0
        blades_coll.objects.link(obj)
        blades[kind] = obj

    plan = frond_plan(rng)
    for name, kind, pts in plan:
        course = add_course(f"course_{name}", pts, courses)
        course["kyt_course"] = name
        course["kyt_kind"] = kind
        add_courses.add_frond(name, course, blades[kind], kind)

    trunk = build_trunk(random.Random(SEED + 1))
    heart = build_heart()
    export.objects.link(trunk)
    export.objects.link(heart)
    for obj in export.objects:
        if obj.type == "MESH" and obj is not trunk:
            obj["kyt_collision"] = "none"
    if bpy.data.objects.get("plant_base") is None:
        base = bpy.data.objects.new("plant_base", None)
        base.empty_display_type = "ARROWS"
        bpy.data.collections["reference"].objects.link(base)
    bpy.context.scene["kyt_godot_scene"] = f"res://scenes/world/{NAME}.tscn"

    depsgraph = bpy.context.evaluated_depsgraph_get()
    tris, lo, hi = 0, Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for obj in export.objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        for v in me.vertices:
            co = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, co))
            hi = Vector(map(max, hi, co))
        ev.to_mesh_clear()
    fronds = sum(1 for _, kind, _ in plan if kind != "stub")
    print(f"date_palm: {fronds} fronds and {KINDS['stub']['count']} stubs, trunk to {SEAT} m; "
          f"{tris} triangles; {hi.z:.2f} m tall, {hi.x - lo.x:.1f} by {hi.y - lo.y:.1f} m across, "
          f"lowest frond tip {min(p[-1].z for _, k, p in plan if k != 'stub'):.2f} m")


# ---------------------------------------------------------------- paint

def island_box(obj, size):
    uv = obj.data.uv_layers.active.data
    us = np.array([d.uv[0] for d in uv]) * size
    vs = np.array([d.uv[1] for d in uv]) * size
    return us.min(), us.max(), vs.min(), vs.max()


def paint(size_hint=None):
    folder = os.path.join(root(), "assets", "source", "textures", NAME)
    path = os.path.join(folder, f"{NAME}_colour.png")
    if os.path.exists(os.path.join(folder, f"{NAME}_colour.psd")):
        raise SystemExit("date_palm: a canvas PSD exists (her painting); --paint is for the unpainted canvas")
    img = bpy.data.images.load(path, check_existing=False)
    size = img.size[0]
    px = np.empty(size * size * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(size, size, 4)
    rng = np.random.default_rng(SEED)

    # The trunk's tiles: a diamond each, its face lit from above and darker
    # below its middle ridge, fibres across it, a dark groove round it; the
    # shadowed rows' tiles darkened as `build_trunk` recorded.
    trunk = bpy.data.objects["trunk"]
    grid = json.loads(trunk["kyt_trunk_tiles"])
    cols, rows = grid["cols"], grid["rows"]
    u0, u1, v0, v1 = island_box(trunk, size)
    margin = 6
    x0, x1 = int(math.floor(u0)) - margin, int(math.ceil(u1)) + margin
    y0, y1 = int(math.floor(v0)) - margin, int(math.ceil(v1)) + margin
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    # The island's box runs from the first cell's inset corner to the last's
    # (`tile_uv`), so it maps onto the grid less an inset at each end.
    inset = TILE_INSET
    tu = inset + (xx - u0) / max(u1 - u0, 1) * (cols - 2 * inset)
    tv = inset + (yy - v0) / max(v1 - v0, 1) * (rows - 2 * inset)
    cu, cv = np.clip(np.floor(tu), 0, cols - 1), np.clip(np.floor(tv), 0, rows - 1)
    tile = (cu + cols * cv).astype(int)
    fu, fv = tu - cu, tv - cv
    du = (fu - inset) / (1 - 2 * inset) - 0.5
    dv = (fv - inset) / (1 - 2 * inset) - 0.5
    edge = np.abs(du) * 2 + np.abs(dv) * 2  # 1 on the diamond's outline
    # sRGB, as painted (the PNG's own values, not linear).
    faces = {
        ("fresh", 0): ((0.82, 0.65, 0.46), (0.62, 0.47, 0.32), (0.38, 0.27, 0.18)),  # light, shade, groove
        ("fresh", 1): ((0.79, 0.62, 0.43), (0.6, 0.45, 0.3), (0.36, 0.26, 0.17)),
        ("weathered", 0): ((0.72, 0.6, 0.46), (0.55, 0.44, 0.33), (0.35, 0.27, 0.2)),  # warm grey-brown
        ("weathered", 1): ((0.69, 0.58, 0.45), (0.52, 0.42, 0.32), (0.33, 0.26, 0.19)),
    }
    lc, sc, gc = faces[("weathered", 0)]  # an unused cell
    light = np.broadcast_to(np.array(lc, dtype=np.float32), yy.shape + (3,)).copy()
    shade = np.broadcast_to(np.array(sc, dtype=np.float32), yy.shape + (3,)).copy()
    groove = np.broadcast_to(np.array(gc, dtype=np.float32), yy.shape + (3,)).copy()
    dark = np.ones(yy.shape + (3,), dtype=np.float32)
    shadow, boot = np.array(SHADOW[0], dtype=np.float32), np.array(BOOT_SHADE, dtype=np.float32)
    for spec in grid["tiles"]:
        mine = tile == spec["cell"]
        lc, sc, gc = faces[(spec["kind"], spec["variant"])]
        light[mine], shade[mine], groove[mine] = lc, sc, gc
        if "grad" in spec:
            a, b = spec["grad"]
            lifted = smoothstep_np(0.0, 1.0, a - b * (dv + 0.5))[..., None]
            dark = np.where(mine[..., None], shadow + (1.0 - shadow) * lifted, dark)
        elif "shade" in spec:
            dark = np.where(mine[..., None], 1.0 - spec["shade"] * (1.0 - boot), dark)
    mid = -SAG * 0.5  # the middle sits low, as the mesh's does
    upper = np.clip((dv - mid) / (0.5 - mid), 0, 1)
    face = shade + (light - shade) * (0.35 + 0.65 * upper[..., None] ** 0.7)
    ridge = np.exp(-((dv - mid) / 0.04) ** 2) * (np.abs(du) < 0.42)  # the scar's lip, catching light
    face = face + (np.array((0.9, 0.8, 0.64)) - face) * (0.3 * ridge)[..., None]
    fibres = np.sin((dv * 60.0 + np.sin(du * 9.0 + tile) * 1.5) * 1.0) * 0.5 + 0.5
    face = face * (0.965 + 0.035 * fibres)[..., None]
    noise = rng.standard_normal((yy.shape[0] // 4 + 2, yy.shape[1] // 4 + 2)).astype(np.float32)
    noise = np.kron(noise, np.ones((4, 4), dtype=np.float32))[:yy.shape[0], :yy.shape[1]]
    face = face * (1.0 + 0.04 * noise)[..., None]
    g = smoothstep_np(0.84, 0.94, edge)[..., None]
    rgb = (face + (groove - face) * g) * dark
    region = px[y0:y1, x0:x1]
    region[..., :3] = np.clip(rgb, 0, 1)
    region[..., 3] = 1.0

    # Each feather blade dark at the rachis to light at its leaflets' tips,
    # and darker at its base: the Mario Kart palms' painted leaves.
    shaded = []
    for kind in ("spear", "young", "mature", "old"):
        obj = bpy.data.objects[f"blade_{kind}"]
        me = obj.data
        uv = me.uv_layers.active.data
        mids = [uv[li].uv for p in me.polygons for li in p.loop_indices
                if abs(me.vertices[me.loops[li].vertex_index].co.x) < 1e-6]
        mid_u = float(np.median([m[0] for m in mids])) * size
        u0, u1, v0, v1 = island_box(obj, size)
        x0, x1 = int(u0) - 2, int(math.ceil(u1)) + 2
        y0, y1 = int(v0) - 2, int(math.ceil(v1)) + 2
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        half = max(mid_u - u0, u1 - mid_u, 1.0)
        out = np.clip(np.abs(xx - mid_u) / half, 0, 1)
        along = np.clip((yy - v0) / max(v1 - v0, 1), 0, 1)
        rachis = np.abs(xx - mid_u) < 0.03 * half + 2
        tone = (0.7 + 0.55 * out ** 0.8) * (0.8 + 0.2 * np.clip(along / 0.35, 0, 1))
        tone = np.where(rachis, 1.0, tone)
        region = px[y0:y1, x0:x1]
        region[..., :3] = np.clip(region[..., :3] * tone[..., None], 0, 1)
        shaded.append(kind)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print(f"date_palm: trunk tiles painted; {', '.join(shaded)} shaded rachis to tip, in {os.path.relpath(path, root())}")


def smoothstep_np(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def root():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "authored" not in bpy.data.collections:
        raise SystemExit("date_palm: this file has no 'authored' collection; start it with new_prop.py")
    if "--paint" in argv:
        paint()
    else:
        build("--replace" in argv)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("date_palm: saved")


if __name__ == "__main__":
    main()
