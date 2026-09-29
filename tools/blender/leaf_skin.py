"""The bushes' greenery: semi-domes of painted leaves over any base (2026-09-28).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<bush>.blend --python tools/blender/leaf_skin.py -- <bush> [--replace]

After the Animal Crossing bushes Christina pointed to: every bush and hedge
wears the same greenery on a different base; a species differs by its leaf
(the hibiscus "a darker leaf with a different shape", the holly the same) and
its flowers. Ours are "slightly taller and more conical" than AC's scoop: a
gumdrop. Then her Mario Kart tree ("our shrubs will be assembled from a series
of these types of shapes and texture approaches", "optimize these for the
fewest amount of triangles"): the greenery is a few big semi-domes, each a
shallow cap of many painted leaves, overlapping like courses of shingles.

What it makes, for a bush in `SPECIES`:

- `authored/blades/blade_leaf`: the semi-dome (`dome_card`): its apex on top,
  its rim drooping, its leaves painted on it radiating from the apex, their
  tips its rim (`paint_canvas.py --leaflets`, `PROP_LEAFLETS`, style `dome`);
  its underside is the leaves' shaded side. Reshape it and every dome follows.
- `authored/blades/blade_bloom`: the flowers' card, a square; its texture
  paints an azalea truss or a hibiscus flower, each colourway side by side
  along the canvas (`kyt_slots`), which a placement's Godot script picks.
- `authored/domes/domes` (and `_small`, `_large`): where the domes go, one
  point each (`dome_spots`), turned (`kyt_turn`) and sized (`kyt_size`) on
  it. Move a point in edit mode to move its dome.
- `export/bush`: the base she can reshape in edit mode, in the shaded leaf
  colour that shows between domes. Its `kyt_dome_skin` modifier puts the dome
  on every point, rests any rim that would pass under the soil on it, and
  shades each dome Roundness of the way round the base.
- `export/blooms` (a collection): the flowers, points each wearing the bloom
  card, set just above the leaves under them. Being in a child collection,
  they are merged on Send but are not laid out as islands of their own.
- `export/trunk` for the tree form.

Then `unwrap_blades.py --size 1024 --save` (the bloom card's slots across the
top) and `paint_canvas.py --leaflets --size 1024 --orm-size 256 --save`.
`--replace` clears what `export`, `authored/blades` and `authored/domes` held
first (an agent's own earlier shape, never her work). Saves.
"""

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_courses  # noqa: E402
import plant_blades  # noqa: E402
from add_courses import link  # noqa: E402

# The gumdrop: (radius, height) as shares of the base's half-width and height,
# from the ground up. Fuller low down, narrowing steadily to a rounded tip.
GUMDROP = [(0.86, 0.0), (0.97, 0.06), (1.0, 0.18), (0.98, 0.33), (0.93, 0.48), (0.84, 0.62),
           (0.71, 0.75), (0.53, 0.86), (0.30, 0.95), (0.15, 0.988), (0.0, 1.0)]
# Her hibiscus (2026-09-28, her photo in `documentation/reference/hibiscus_shrub/`:
# "a bit more boxy and round, but just as tall"): full to the shoulders, near
# upright sides, a broad rounded top.
BOXY = [(0.86, 0.0), (0.97, 0.05), (1.0, 0.15), (1.0, 0.32), (0.99, 0.48), (0.96, 0.62), (0.9, 0.74),
        (0.79, 0.845), (0.62, 0.925), (0.38, 0.975), (0.0, 1.0)]
# The giant tree form (her "giant tree type variation", 2026-09-28: a tall
# egg of leaves and blooms on a bare trunk, a standard): the crown's profile,
# closed underneath, from its bottom pole to its top.
EGG = [(0.0, 0.0), (0.42, 0.03), (0.7, 0.09), (0.88, 0.18), (0.98, 0.31), (1.0, 0.45), (0.97, 0.59),
       (0.88, 0.72), (0.72, 0.84), (0.48, 0.93), (0.24, 0.98), (0.0, 1.0)]
AROUND = 6  # the core is mostly hidden under the domes
CORE_EVERY = 3  # and takes every third ring of its profile

# The semi-dome's shape (`dome_card`), out from its apex: each ring (share of
# the reach along the surface, slope below level over the stretch in to it,
# in degrees, vertices round); eight and eight is 24 triangles.
DOME_SHAPES = {
    # A shallow cap, level round its apex and drooping to its rim, the shrubs'
    # first domes: her "perfect little individual unit of greenery we can use
    # as a box shrub etc", kept when the shrubs went to half spheres
    # (`assets/source/archive/landscape_kit_checkpoints/icecap_domes_2026-09-28`).
    "ice_cap": ((0.45, 12.0, 8), (1.0, 62.0, 8)),
    # Her "think of the shape of an ice cap vs a half sphere": a half ball,
    # its rim straight down; its reach is a quarter round, radius x pi / 2.
    "half_sphere": ((0.5, 22.5, 8), (1.0, 67.5, 8)),
    # The same, rounder over its top: three rings, 36 triangles.
    "half_sphere_round": ((1 / 3, 15.0, 6), (2 / 3, 45.0, 8), (1.0, 75.0, 8)),
}


# A shrub's body, one piece standing on the ground under its crown (her "the
# base of each shrub can be one singular sphere or egg shape ... then the
# semi-domes create visual interest on top", "the goal is to simplify", "its
# like an unshelled boiled egg shape that were looking for"): a peeled egg
# standing on its broad end, `width` of its height across, `broad` wider below
# the middle, rounded over the top and rounding under to its rim on the soil;
# the leaves hang from its top and their tips are that rim. Rings at
# `BODY_TURNS` degrees round its outline from the top, 56 triangles. The
# second version is a ball (her "dont forget our second version that is a
# sphere instead of a egg, and smaller").
BODIES = {"egg": dict(width=0.78, broad=0.2), "sphere": dict(width=1.0, broad=0.0)}
BODY_TURNS = (35.0, 70.0, 105.0, 140.0)


def egg_outline(width, broad, turns):
    """(radius, depth below the top) at the top and at each of `turns`
    degrees round a body's outline, for a body one unit high."""
    def at(t):
        z = (1.0 - math.cos(t)) / 2.0  # 0 at the top, 1 at the bottom
        return width / 2.0 * math.sin(t) * (1.0 + broad * (z - 0.5)), z
    return [(0.0, 0.0)] + [at(math.radians(t)) for t in turns]


def outline_steps(points):
    """(length, slope below level in degrees) of each stretch of an outline."""
    return [(math.hypot(r1 - r0, z1 - z0), math.degrees(math.atan2(z1 - z0, r1 - r0)))
            for (r0, z0), (r1, z1) in zip(points, points[1:])]


def outline_shape(points, count=8):
    """An outline from the apex as `DOME_SHAPES` rings."""
    steps = outline_steps(points)
    total, done, rings = sum(s for s, _ in steps), 0.0, []
    for s, slope in steps:
        done += s
        rings.append((done / total, slope, count))
    return tuple(rings)


def egg_shape(width, broad, turns=BODY_TURNS, count=8):
    """A body's outline down to `turns` as `DOME_SHAPES` rings."""
    return outline_shape(egg_outline(width, broad, turns), count)


for _name, _body in BODIES.items():
    DOME_SHAPES[_name] = egg_shape(**_body)


def crown_cap(body, down, clear=0.02, grow=1.04, flare=None):
    """The crown dome of a body (her "the bowl of the upside down dome
    segment on top of the egg is too deep, again think polar ice cap, or
    saucer"): the body's own outline from its top `down` degrees round,
    `grow` times the body's size, so it lies over the body like a polar cap,
    its middle `clear` above the body's top. With `flare`, its rim flares out
    to that share wider than the body at its widest, a brim (her "have the hat
    flare out be larger than the base sphere by like 2%"). Registers its shape
    as `DOME_SHAPES["crown_cap"]`; (reach, sink) for the dome."""
    egg = BODIES[body["shape"]]
    metres = body["reach"] / sum(s for s, _ in outline_steps(egg_outline(egg["width"], egg["broad"], BODY_TURNS)))
    cap = egg_outline(egg["width"], egg["broad"], (down / 2.0, down))
    if flare is not None:
        widest = max(r for r, _ in egg_outline(egg["width"], egg["broad"], range(5, 180, 5)))
        cap[-1] = ((1.0 + flare) * widest / grow, cap[-1][1])  # the whole cap is grown by `grow` after
    DOME_SHAPES["crown_cap"] = outline_shape(cap)
    reach = sum(s for s, _ in outline_steps(cap)) * metres * grow
    return reach, cap[-1][1] * metres * grow - clear


def body_tier(name, body, material, count=8):
    """A second tier round a body (her "should hte egg shaped ones hae an
    additional tier", "try it on the eggs"): a band of leaves from `top` to
    `down` degrees round the body's outline, `gap` off it, its hem flared
    `flare` wider than the body at its widest, their tips that hem; its top
    tucks under the crown's hat. In the body's own frame (placed with it, at
    every size), 16 triangles, unwrapped by distance along the body from its
    top as the body is (`kyt_flat_xy`, `kyt_rings`)."""
    tier = body["tier"]
    egg = BODIES[body["shape"]]
    unit = egg_outline(egg["width"], egg["broad"], BODY_TURNS)
    metres = body["reach"] / sum(s for s, _ in outline_steps(unit))
    rim = unit[-1][1] * metres  # the body's rim, at its pivot, lies this far below its top
    widest = max(r for r, _ in egg_outline(egg["width"], egg["broad"], range(5, 180, 5))) * metres
    fine = egg_outline(egg["width"], egg["broad"], [t / 2 for t in range(1, 2 * int(tier["down"]) + 1)])

    def along(t):
        """Distance along the outline from the top to `t` degrees, metres."""
        return sum(s for s, _ in outline_steps(fine[:int(round(t * 2)) + 1])) * metres

    rings = []
    for t in (tier["top"], tier["down"]):
        (r0, d0), (r1, d1) = egg_outline(egg["width"], egg["broad"], (t - 1.0, t + 1.0))[1:]
        size = math.hypot(d1 - d0, r1 - r0)
        out_r, out_z = (d1 - d0) / size, (r1 - r0) / size  # outward, in (radius, height)
        r, d = egg_outline(egg["width"], egg["broad"], (t,))[1]
        r, z = r * metres + tier["gap"] * out_r, rim - d * metres + tier["gap"] * out_z
        if t == tier["down"]:
            r = (1.0 + tier.get("flare", 0.0)) * widest
        rings.append((r, z, along(t)))
    verts, flat = [], []
    for r, z, s in rings:
        for j in range(count):
            # Turned `turn` degrees from the body's facets, so its corners and
            # leaf tips fall between those of the hat above and the body (her
            # "our tiers need to be offset on their horizontal rotation").
            a = (j / count + tier.get("turn", 0.0) / 360.0) * math.tau
            verts.append((r * math.cos(a), r * math.sin(a), z))
            flat.append((s * math.cos(a), s * math.sin(a)))
    faces = zip_band(0, count, count, count)
    me = card_mesh(name, verts, faces, material, flat)
    me["kyt_rings"] = [c for r, _, s in rings for c in (s, r)]
    return me


def body_topper(name, body, material):
    """A sprout of `leaves` leaves standing up out of a body's very top (her
    "lets give them a little like two or three leaf topper"): each a card
    `length` long and `width` of that across, fanned round the top and leaning
    `tilt` degrees out, their feet `sink` into the hat; one leaf painted on
    them all (`paint_canvas.py`, `cut_topper`). In the body's own frame, 2
    triangles a leaf."""
    top = body["topper"]
    egg = BODIES[body["shape"]]
    unit = egg_outline(egg["width"], egg["broad"], BODY_TURNS)
    foot = Vector((0.0, 0.0, unit[-1][1] * body["reach"] / sum(s for s, _ in outline_steps(unit))
                   + 0.02 - top["sink"]))  # the body's top, where the hat lies 2 cm over it
    length, half = top["length"], top["length"] * top["width"] / 2.0
    verts, faces, flat = [], [], []
    for i in range(top["leaves"]):
        a = (i / top["leaves"] + top.get("turn", 0.0) / 360.0) * math.tau
        tilt = math.radians(top["tilt"])
        up = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
        side = Vector((-math.sin(a), math.cos(a), 0.0))
        k = len(verts)
        verts += [foot - side * half, foot + side * half, foot + up * length + side * half, foot + up * length - side * half]
        flat += [(-half, 0.0), (half, 0.0), (half, length), (-half, length)]
        faces += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
    return card_mesh(name, [tuple(v) for v in verts], faces, material, flat)

# sRGB colours; metres. `dome`, the semi-domes (her Mario Kart tree): `shape`
# in `DOME_SHAPES`, `reach` from apex to rim along the surface. Laid out
# (`dome_spots`) in courses `spacing` apart round the base and `rows` of that
# down it, the first a single dome on the crown and the last `low` above the
# base's foot; each turned `tilt` of the way from the base's face to straight
# up, its middle `sink` under the base's surface (the crown's `crown_sink`),
# sized 1 +- `size_jitter`, shaded `roundness` of the way round the base.
# `core`: the base shows, in the shaded leaf colour, between domes.
# `single`: the whole plant is one dome standing on the ground, its rim on the
# soil. A species without `bloom` has no flowers and is evergreen. `body`: the
# plant's one peeled egg (`BODIES`), its own island on the canvas, the base
# its domes and flowers are laid out over. The flowering shrubs are that egg
# and one dome on its crown (her "start with just one on the crown"), a
# saucer cut from the egg's own outline `cap_down` degrees round (`crown_cap`;
# her "the bowl ... is too deep, again think polar ice cap, or saucer"),
# turned `crown_turn` degrees from the egg's facets, sized with the egg across
# the sizes; `courses` 0 is that one dome alone. 80 triangles. The canvas is
# 2048 for the egg's island.
SPECIES = {
    # The box shrub (her "these are perfect little individual unit of greenery
    # we can use as a box shrub etc - lets create a small box shrub that is
    # just a singular one of these domes", 2026-09-28): one ice cap, 0.75 m
    # across and 0.32 m high, 24 triangles, in a boxwood's small leaves
    # (`paint_canvas.py`, `PROP_LEAFLETS`).
    "box_shrub": dict(
        godot="res://scenes/world/landscape_kit/box_shrub.tscn",
        base=dict(width=0.6, height=0.25, profile=GUMDROP, square=2.0),  # holds the dome; not shown
        leaf=dict(colour=(0.24, 0.50, 0.17), rough=0.7),
        core=((0.12, 0.28, 0.10), 0.9),
        dome=dict(shape="ice_cap", reach=0.56, single=True, roundness=0.0, core=False, seed=2),
    ),
    "azalea_bush": dict(
        godot="res://scenes/world/landscape_kit/azalea_bush.tscn",
        base=dict(square=2.0),  # the body's (`body_base`)
        body=dict(shape="egg", reach=1.42,  # 1.0 m across, 1.15 m high
                  tier=dict(top=56.0, down=100.0, gap=0.05, flare=0.2, turn=36.8),
                  topper=dict(leaves=3, length=0.28, width=0.7, tilt=100.0, sink=0.0, turn=71.4)),
        sizes={"small": 0.75, "medium": 1.0, "large": 1.3},
        leaf=dict(colour=(0.40, 0.68, 0.26), rough=0.7),
        core=((0.16, 0.36, 0.13), 0.9),  # the carrier's; not shown
        dome=dict(courses=0, cap_down=64.0, cap_flare=0.15, crown_turn=22.5, roundness=0.3, core=False, seed=3),
        # A truss per card (seven blooms painted on it), `count` of them; three
        # colourways painted side by side (`slots`: pink, magenta, white).
        bloom=dict(radius=0.19, dome=0.07, count=10, group=(0, 0), sizes=(0.6, 1.3), from_height=0.3, seed=5, slots=3,
                   colour=((0.97, 0.52, 0.76), 0.6)),
    ),
    "azalea_tree": dict(
        godot="res://scenes/world/landscape_kit/azalea_tree.tscn",
        base=dict(square=2.0, lift=0.85),  # the body's (`body_base`), on the trunk
        body=dict(shape="egg", reach=2.3,  # 1.64 m across, 1.87 m high
                  tier=dict(top=56.0, down=100.0, gap=0.05, flare=0.2, turn=36.8),
                  topper=dict(leaves=3, length=0.38, width=0.7, tilt=100.0, sink=0.0, turn=71.4)),
        # A bigger tree of this kind shows more bare trunk and grows broader,
        # not just taller: per size, `scale` across, `tall` the crown's
        # height, `lift` the trunk (her "the largest one looks weird", when the
        # large was the medium blown up 1.3 times, a tall egg on a stub).
        sizes={"small": dict(scale=0.75, tall=0.75, lift=0.85), "medium": 1.0,
               "large": dict(scale=1.3, tall=1.12, lift=1.6)},
        trunk=dict(height=1.2, radius=(0.075, 0.05), colour=((0.36, 0.26, 0.18), 0.9)),
        leaf=dict(colour=(0.40, 0.68, 0.26), rough=0.7),
        core=((0.16, 0.36, 0.13), 0.9),
        dome=dict(courses=0, cap_down=64.0, cap_flare=0.15, crown_turn=22.5, roundness=0.3, core=False, seed=4),
        bloom=dict(radius=0.19, dome=0.07, count=24, group=(0, 0), sizes=(0.6, 1.35), from_height=0.08, seed=11, slots=3,
                   colour=((0.97, 0.52, 0.76), 0.6)),
    ),
    "hibiscus_shrub": dict(
        godot="res://scenes/world/landscape_kit/hibiscus_shrub.tscn",
        base=dict(square=2.0),  # the body's (`body_base`)
        body=dict(shape="egg", reach=1.7,  # 1.21 m across, 1.38 m high
                  tier=dict(top=56.0, down=100.0, gap=0.05, flare=0.25, turn=36.8),
                  topper=dict(leaves=3, length=0.3, width=1.4, tilt=110.0, sink=-0.01, turn=71.4)),
        sizes={"small": 0.75, "medium": 1.0, "large": 1.3},
        leaf=dict(colour=(0.20, 0.44, 0.36), rough=0.55),
        core=((0.10, 0.26, 0.21), 0.9),  # the carrier's; not shown
        dome=dict(courses=0, cap_down=64.0, cap_flare=0.2, crown_turn=22.5, roundness=0.3, core=False, seed=6),
        # One flower per card, in loose twos and threes (her "hibiscus could
        # also benefit from some clustering"); four colourways (`slots`: red,
        # pink, yellow-red, pink-white).
        bloom=dict(radius=0.16, dome=-0.03, count=8, group=(0, 2), sizes=(0.85, 1.15), from_height=0.3, seed=8, slots=4,
                   colour=((0.93, 0.20, 0.15), 0.55)),
    ),
}
# The second version of each (her "dont forget our second version that is a
# sphere instead of a egg, and smaller", "yes they can be their own files"): a
# ball, its hat down 72 degrees so its hem lies round the ball's top third (her
# "it looks good because it hits around the top third of the sphere"), the
# brim flared wider than the ball ("have the hat flare out be larger than the
# base sphere", "it oculd be a bit more pronounced").
for _shrub, _reach in (("azalea_bush", 1.2), ("hibiscus_shrub", 1.35), ("azalea_tree", 1.9)):
    SPECIES[f"{_shrub}_sphere"] = dict(
        SPECIES[_shrub], godot=f"res://scenes/world/landscape_kit/{_shrub}_sphere.tscn",
        body=dict(shape="sphere", reach=_reach),
        dome=dict(SPECIES[_shrub]["dome"], cap_down=72.0, cap_flare=0.05))
BLOOM_CLEAR = 0.025  # a bloom sits this far above the highest leaf under it


# --- Shapes ------------------------------------------------------------------

def profile_at(profile, h):
    """(radius share, d radius / d height) of a base's profile at height share h."""
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        if z0 <= h <= z1:
            f = (h - z0) / (z1 - z0)
            return r0 + (r1 - r0) * f, (r1 - r0) / (z1 - z0)
    return 0.0, 0.0


def plan(a, square):
    """The base's plan at bearing a: (reach, outward direction). A circle at
    `square` 2; above it a superellipse, squarer the higher (2.6: corners 8%
    further out than the sides)."""
    c, s = math.cos(a), math.sin(a)
    reach = (abs(c) ** square + abs(s) ** square) ** (-1.0 / square)
    x, y = reach * c, reach * s
    out = Vector((math.copysign(abs(x) ** (square - 1), x), math.copysign(abs(y) ** (square - 1), y), 0.0))
    return reach, out.normalized()


def gumdrop(name, spec, material):
    """The base: its profile turned round the upright axis over its plan, open
    underneath, shaded smooth."""
    width, height, lift = spec["width"], spec["height"], spec.get("lift", 0.0)
    profile = spec["profile"][:-1:CORE_EVERY] + [spec["profile"][-1]]
    closed = profile[0][0] == 0.0  # a crown held up on a trunk is closed underneath
    bm = bmesh.new()
    rings = []
    for r, z in profile[1:-1] if closed else profile[:-1]:
        rings.append([bm.verts.new((r * width / 2 * plan(a, spec["square"])[0] * math.cos(a),
                                    r * width / 2 * plan(a, spec["square"])[0] * math.sin(a), lift + z * height))
                      for a in (k / AROUND * math.tau for k in range(AROUND))])
    if closed:
        bottom = bm.verts.new((0.0, 0.0, lift))
        for k in range(AROUND):
            bm.faces.new((rings[0][(k + 1) % AROUND], rings[0][k], bottom))
    top = bm.verts.new((0.0, 0.0, lift + height))
    for lo, hi in zip(rings, rings[1:]):
        for k in range(AROUND):
            bm.faces.new((lo[k], lo[(k + 1) % AROUND], hi[(k + 1) % AROUND], hi[k]))
    for k in range(AROUND):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % AROUND], top))
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    return me


def dome_rings(dome):
    """A dome's rings out from its apex: (radius, depth below the apex,
    distance along the surface, vertices round) each."""
    out = down = done = 0.0
    rings = []
    for share, slope, count in DOME_SHAPES[dome["shape"]]:
        step = (share - done) * dome["reach"]
        out += step * math.cos(math.radians(slope))
        down += step * math.sin(math.radians(slope))
        done = share
        rings.append((out, down, share * dome["reach"], count))
    return rings


def body_base(body, base_spec):
    """The base a body stands for (its profile as `gumdrop` takes one, from
    the ground up), so the domes and flowers are laid out over it."""
    rings = dome_rings(body)
    wide, deep = max(r for r, _, _, _ in rings), rings[-1][1]
    profile = [(r / wide, 1.0 - d / deep) for r, d, _, _ in reversed(rings)] + [(0.0, 1.0)]
    return dict(base_spec, width=2 * wide, height=deep, profile=profile, square=2.0)


def dome_card(name, dome, material):
    """One semi-dome of leaves (her Mario Kart tree): a shallow cap, level
    round its apex and drooping to its rim, its many leaves painted on it
    (`paint_canvas.py`, style `dome`), their tips its rim; from under it, the
    leaves' shaded side. Its rings are `DOME_SHAPES[dome["shape"]]` out from
    the apex; the pivot is the middle of the rim's plane, so a dome stands its
    own height off where it is placed. Unwrapped by distance along the surface
    from the apex (`kyt_flat_xy`, which `unwrap_blades.py` lays out), so a
    leaf is painted its true length; round the dome it is narrower than
    painted by the ring's girth against its flat one, which each ring keeps
    (`kyt_rings` on the mesh: distance along, radius, in metres) for the
    painting to widen its leaves by."""
    rings = dome_rings(dome)
    rim = rings[-1][1]
    verts, flat, starts = [(0.0, 0.0, rim)], [(0.0, 0.0)], []
    for r, d, s, count in rings:
        starts.append(len(verts))
        for j in range(count):
            a = j / count * math.tau
            verts.append((r * math.cos(a), r * math.sin(a), rim - d))
            flat.append((s * math.cos(a), s * math.sin(a)))
    first = rings[0][3]
    faces = [(0, starts[0] + j, starts[0] + (j + 1) % first) for j in range(first)]
    for k in range(len(rings) - 1):
        faces += zip_band(starts[k], rings[k][3], starts[k + 1], rings[k + 1][3])
    me = card_mesh(name, verts, faces, material, flat)
    me["kyt_rings"] = [c for r, _, s, _ in rings for c in (s, r)]
    return me


def zip_band(a0, na, b0, nb):
    """Triangles joining a ring of `na` vertices from index a0 to an outer
    ring of `nb` from b0, both evenly round from bearing 0: one per vertex of
    each, stepping round by whichever ring's next vertex comes first."""
    faces, i, j = [], 0, 0
    while i < na or j < nb:
        if i < na and (j >= nb or (i + 1) / na <= (j + 1) / nb):
            faces.append((a0 + i, b0 + j % nb, a0 + (i + 1) % na))
            i += 1
        else:
            faces.append((a0 + i % na, b0 + j, b0 + (j + 1) % nb))
            j += 1
    return faces


def bloom_card(name, radius, dome, material):
    """The flowers' card (her "needs to be optimized for using textures"): a
    square `radius` from its middle to each side, its middle `dome` proud (a
    hibiscus's cup is a negative dome); the texture paints the flowers on it.
    Four triangles."""
    verts = [(0.0, 0.0, dome)] + [(radius * x, radius * y, 0.0) for x, y in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    faces = [(0, 1 + k, 1 + (k + 1) % 4) for k in range(4)]
    return card_mesh(name, verts, faces, material)


def card_mesh(name, verts, faces, material, flat=None):
    """A card with a top-view unwrap, or one by `flat` (x, y per vertex, in
    metres) kept on it as `kyt_flat_xy`; `unwrap_blades.py` lays it out again."""
    flat = flat or [v[:2] for v in verts]
    x0, y0 = min(f[0] for f in flat), min(f[1] for f in flat)
    w, h = max(f[0] for f in flat) - x0, max(f[1] for f in flat) - y0

    def uv(i):
        return ((flat[i][0] - x0) / w, (flat[i][1] - y0) / h)
    me = plant_blades.mesh_from(name, verts, faces, [0] * len(faces), [tuple(uv(i) for i in f) for f in faces], [material])
    me.attributes.new("kyt_flat_xy", "FLOAT2", "POINT").data.foreach_set("vector", [c for f in flat for c in f])
    for p in me.polygons:
        p.use_smooth = True
    return me


def bloom_spots(base, spec):
    """`count` places spread evenly over the base above `from_height`: many
    candidates by area, then each next the farthest from those taken."""
    width, height = base["width"], base["height"]
    rng = random.Random(spec["seed"])
    cands = []
    while len(cands) < 600:
        h = rng.uniform(spec["from_height"], 0.9)
        r, slope = profile_at(base["profile"], h)
        if rng.random() > r:  # by area: fewer where the base is narrow
            continue
        a = rng.uniform(0, math.tau)
        reach, out = plan(a, base["square"])
        pos = Vector((r * reach * width / 2 * math.cos(a), r * reach * width / 2 * math.sin(a),
                      base.get("lift", 0.0) + h * height))
        # Outward normal from the plan and the profile's slope (radius against height, in metres).
        dr = slope * reach * (width / 2) / height
        n = Vector((out.x, out.y, -dr)).normalized()
        cands.append((pos, n))
    taken = [max(cands, key=lambda c: c[0].z)]
    while len(taken) < spec["count"]:
        taken.append(max(cands, key=lambda c: min((c[0] - t[0]).length for t in taken)))
    return taken


def dome_spots(base, dome):
    """Where the semi-domes go on a base, like courses of shingles: a single
    dome on the crown, then courses `rows` x `spacing` apart down the
    surface to `low` above the base's foot, each course's domes `spacing`
    apart round it (by its plan's girth there) and turned half a step from the
    course above, a little off true. (position, base normal) each."""
    width, height, lift, square = base["width"], base["height"], base.get("lift", 0.0), base["square"]
    if dome.get("single"):
        return [(Vector((0.0, 0.0, lift)), Vector((0.0, 0.0, 1.0)))]
    rng = random.Random(dome["seed"])
    # The profile from the top down, in metres, and distance down it.
    prof = [(r * width / 2, lift + z * height) for r, z in reversed(base["profile"])]
    arc = [0.0]
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        arc.append(arc[-1] + math.hypot(r1 - r0, z1 - z0))

    def at(s):
        s = min(max(s, 0.0), arc[-1])
        k = next(k for k in range(len(prof) - 1) if arc[k + 1] >= s)
        f = (s - arc[k]) / max(arc[k + 1] - arc[k], 1e-9)
        return (prof[k][0] + (prof[k + 1][0] - prof[k][0]) * f, prof[k][1] + (prof[k + 1][1] - prof[k][1]) * f)

    def normal(s):
        (r0, z0), (r1, z1) = at(s - 0.06), at(s + 0.06)
        across, up = -(z1 - z0), r1 - r0  # the profile's direction turned outward
        size = math.hypot(across, up)
        return across / size, up / size

    spots = [(Vector((0.0, 0.0, prof[0][1])), Vector((0.0, 0.0, 1.0)))]
    # `courses` 0 is the crown's one dome alone (her "start with just one on
    # the crown" of the egg).
    if dome.get("courses") == 0:
        return spots
    end = next((s / 100 * arc[-1] for s in range(100, -1, -1) if at(s / 100 * arc[-1])[1] >= lift + dome["low"]), 0.0)
    courses = max(1, round(end / (dome["spacing"] * dome["rows"])))
    for c in range(1, courses + 1):
        s = end * c / courses
        r, z = at(s)
        across, up = normal(s)
        ring = [plan(k / 64 * math.tau, square)[0] * r for k in range(64)]
        girth = sum(math.hypot(ring[k] * math.cos(k / 64 * math.tau) - ring[k - 1] * math.cos((k - 1) / 64 * math.tau),
                               ring[k] * math.sin(k / 64 * math.tau) - ring[k - 1] * math.sin((k - 1) / 64 * math.tau))
                    for k in range(64))
        count = max(3, round(girth / dome["spacing"]))
        for j in range(count):
            a = (j + 0.5 * (c % 2) + rng.uniform(-0.12, 0.12)) / count * math.tau
            # Every other dome a little up or down the surface, so the courses
            # interlock into one mound instead of standing in tiers.
            here = s + (0.5 - j % 2) * dome.get("stagger", 0.0) * dome["spacing"] * dome["rows"] * (c < courses)
            r, z = at(here)
            across, up = normal(here)
            reach, out = plan(a, square)
            pos = Vector((r * reach * math.cos(a), r * reach * math.sin(a), z))
            spots.append((pos, Vector((out.x * across, out.y * across, up)).normalized()))
    return spots


# --- The skin ------------------------------------------------------------------

def dome_skin_group():
    """The Leaf (the semi-dome) on every point of Domes, turned by `kyt_turn`
    (Euler) and sized by `kyt_size`; no rim through the ground; each dome's
    normals leaning Roundness of the way to the base's there
    (`kyt_skin_normal`), so the bush shades as one mound of domes; the base
    kept under them as the core when Show core."""
    ng, io = plant_blades._node_group("kyt_dome_skin", (
        ("Leaf", "NodeSocketObject", None), ("Domes", "NodeSocketObject", None),
        ("Roundness", "NodeSocketFloat", 0.3), ("Ground", "NodeSocketFloat", 0.004),
        ("Show core", "NodeSocketBool", True),
        ("Body", "NodeSocketObject", None), ("Body scale", "NodeSocketVector", (1.0, 1.0, 1.0)),
        ("Body lift", "NodeSocketFloat", 0.0), ("Tier", "NodeSocketObject", None),
        ("Topper", "NodeSocketObject", None)))
    if io is None:
        return ng
    gin, gout = io
    N = ng.nodes.new

    def vec(op, a, b=None, scale=None):
        v = N("ShaderNodeVectorMath")
        v.operation = op
        ng.links.new(a, v.inputs[0])
        if b is not None:
            ng.links.new(b, v.inputs[1])
        if scale is not None:
            ng.links.new(scale, v.inputs["Scale"])
        return v.outputs["Vector"]

    def named(name, kind):
        n = N("GeometryNodeInputNamedAttribute")
        n.data_type = kind
        n.inputs["Name"].default_value = name
        return n.outputs["Attribute"]

    spots = N("GeometryNodeObjectInfo")
    spots.transform_space = "ORIGINAL"  # the points as laid out round the base, so the domes go where the bush goes
    link(ng, gin, "Domes", spots, "Object")
    leaf = N("GeometryNodeObjectInfo")
    leaf.transform_space = "ORIGINAL"
    leaf.inputs["As Instance"].default_value = True
    link(ng, gin, "Leaf", leaf, "Object")
    turn = N("FunctionNodeEulerToRotation")
    ng.links.new(named("kyt_turn", "FLOAT_VECTOR"), turn.inputs["Euler"])
    inst = N("GeometryNodeInstanceOnPoints")
    link(ng, spots, "Geometry", inst, "Points")
    link(ng, leaf, "Geometry", inst, "Instance")
    ng.links.new(turn.outputs["Rotation"], inst.inputs["Rotation"])
    ng.links.new(named("kyt_size", "FLOAT_VECTOR"), inst.inputs["Scale"])  # a crown fitted to its body is sized as the body
    # The Body (a shrub's one sphere or egg under its domes), once, Body lift
    # off the ground and sized Body scale; none without one.
    body = N("GeometryNodeObjectInfo")
    body.transform_space = "ORIGINAL"
    body.inputs["As Instance"].default_value = True
    link(ng, gin, "Body", body, "Object")
    one = N("GeometryNodePoints")
    one.inputs["Count"].default_value = 1
    lift = N("ShaderNodeCombineXYZ")
    link(ng, gin, "Body lift", lift, "Z")
    link(ng, lift, "Vector", one, "Position")
    # The body's Tier (a band of leaves round it), in the body's own frame.
    tier = N("GeometryNodeObjectInfo")
    tier.transform_space = "ORIGINAL"
    tier.inputs["As Instance"].default_value = True
    link(ng, gin, "Tier", tier, "Object")
    # And its Topper (a sprout of leaves on its very top), in the same frame.
    topper = N("GeometryNodeObjectInfo")
    topper.transform_space = "ORIGINAL"
    topper.inputs["As Instance"].default_value = True
    link(ng, gin, "Topper", topper, "Object")
    body_and_tier = N("GeometryNodeJoinGeometry")
    link(ng, body, "Geometry", body_and_tier, "Geometry")
    link(ng, tier, "Geometry", body_and_tier, "Geometry")
    link(ng, topper, "Geometry", body_and_tier, "Geometry")
    whole = N("GeometryNodeInstanceOnPoints")
    link(ng, one, "Points", whole, "Points")
    link(ng, body_and_tier, "Geometry", whole, "Instance")
    link(ng, gin, "Body scale", whole, "Scale")
    both = N("GeometryNodeJoinGeometry")
    link(ng, whole, "Instances", both, "Geometry")
    link(ng, inst, "Instances", both, "Geometry")
    real = N("GeometryNodeRealizeInstances")
    link(ng, both, "Geometry", real, "Geometry")

    # No rim through the ground: it rests on it.
    ground = N("GeometryNodeSetPosition")
    link(ng, real, "Geometry", ground, "Geometry")
    sep = N("ShaderNodeSeparateXYZ")
    ng.links.new(N("GeometryNodeInputPosition").outputs["Position"], sep.inputs["Vector"])
    kept = N("ShaderNodeCombineXYZ")
    link(ng, sep, "X", kept, "X")
    link(ng, sep, "Y", kept, "Y")
    top = N("ShaderNodeMath")
    top.operation = "MAXIMUM"
    link(ng, sep, "Z", top, 0)
    link(ng, gin, "Ground", top, 1)
    link(ng, top, "Value", kept, "Z")
    link(ng, kept, "Vector", ground, "Position")

    # Shaded round the base: each dome's own normal leaning Roundness of the
    # way to the base's where it stands.
    keep = N("ShaderNodeMath")
    keep.operation = "SUBTRACT"
    keep.inputs[0].default_value = 1.0
    link(ng, gin, "Roundness", keep, 1)
    mixed = vec("NORMALIZE", vec("ADD", vec("SCALE", N("GeometryNodeInputNormal").outputs["Normal"], scale=keep.outputs[0]),
                                 vec("SCALE", named("kyt_skin_normal", "FLOAT_VECTOR"), scale=gin.outputs["Roundness"])))
    setn = N("GeometryNodeSetMeshNormal")
    setn.mode, setn.domain = "FREE", "POINT"
    link(ng, ground, "Geometry", setn, "Mesh")
    ng.links.new(mixed, next(s for s in setn.inputs if s.type == "VECTOR"))

    core = N("GeometryNodeSwitch")
    core.input_type = "GEOMETRY"
    link(ng, gin, "Show core", core, "Switch")
    ng.links.new(gin.outputs["Geometry"], core.inputs["True"])
    join = N("GeometryNodeJoinGeometry")
    link(ng, core, "Output", join, "Geometry")
    link(ng, setn, "Mesh", join, "Geometry")
    link(ng, join, "Geometry", gout, "Geometry")
    plant_blades._tidy(ng)
    return ng


def dome_points(name, base, dome, seed):
    """The domes' places for one size (`dome_spots`), as a points object:
    each turned `tilt` of the way up from the base's face and spun at random
    (`kyt_turn`), sized (`kyt_size`), its base normal kept (`kyt_skin_normal`)."""
    rng = random.Random(seed)
    points, turns, sizes, normals = [], [], [], []
    for pos, n in dome_spots(base, dome):
        axis = n.lerp(Vector((0.0, 0.0, 1.0)), dome.get("tilt", 1.0)).normalized()
        spin = rng.uniform(0, math.tau)
        if not points and "crown_turn" in dome:
            # The crown's dome turned `crown_turn` degrees counterclockwise
            # from above, from lying corner over corner with a body's facets
            # (her "maybe rotated counterclockwise a bit", "needs to be
            # rotated a litte").
            spin = math.radians(dome["crown_turn"])
        rot = axis.to_track_quat("Z", "Y") @ Matrix.Rotation(spin, 3, "Z").to_quaternion()
        # The crown's dome sits deeper, down among the course below it.
        sink = dome.get("sink", 0.0)
        points.append(pos - n * (dome.get("crown_sink", sink) if not points else sink))
        turns.append(rot.to_euler())
        # Across and up: a crown fitted to a body is sized as the body is.
        size = 1.0 + rng.uniform(-1.0, 1.0) * dome.get("size_jitter", 0.0)
        fit = dome.get("crown_size", (1.0, 1.0, 1.0)) if len(turns) == 1 else (1.0, 1.0, 1.0)
        sizes.append(tuple(size * f for f in fit))
        normals.append(n)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in points], [], [])
    me.attributes.new("kyt_turn", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for e in turns for c in e])
    me.attributes.new("kyt_size", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for s in sizes for c in s])
    me.attributes.new("kyt_skin_normal", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for v in normals for c in v])
    return bpy.data.objects.new(name, me)


def blooms_on_points_group():
    """The Bloom card on every point, turned by `kyt_turn` (Euler) and sized
    by `kyt_size`, realized so Send merges it with its UVs and material."""
    ng, io = plant_blades._node_group("kyt_blooms_on_points", (("Bloom", "NodeSocketObject", None),))
    if io is None:
        return ng
    gin, gout = io
    N = ng.nodes.new
    info = N("GeometryNodeObjectInfo")
    info.transform_space = "ORIGINAL"
    info.inputs["As Instance"].default_value = True
    link(ng, gin, "Bloom", info, "Object")
    turn = N("GeometryNodeInputNamedAttribute")
    turn.data_type = "FLOAT_VECTOR"
    turn.inputs["Name"].default_value = "kyt_turn"
    euler = N("FunctionNodeEulerToRotation")
    ng.links.new(turn.outputs["Attribute"], euler.inputs["Euler"])
    size = N("GeometryNodeInputNamedAttribute")
    size.data_type = "FLOAT"
    size.inputs["Name"].default_value = "kyt_size"
    inst = N("GeometryNodeInstanceOnPoints")
    link(ng, gin, "Geometry", inst, "Points")
    link(ng, info, "Geometry", inst, "Instance")
    ng.links.new(euler.outputs["Rotation"], inst.inputs["Rotation"])
    ng.links.new(size.outputs["Attribute"], inst.inputs["Scale"])
    real = N("GeometryNodeRealizeInstances")
    link(ng, inst, "Instances", real, "Geometry")
    link(ng, real, "Geometry", gout, "Geometry")
    plant_blades._tidy(ng)
    return ng


def add_trunk(t, scale, lift, stem, home, suffix, tag):
    """The tree form's bare trunk, six-sided and tapering from its foot, its height and girth scaled with the crown. In a collection of its
    own, as the blooms are: merged on Send (with its size's body), plain bark,
    not a leaf-canvas island."""
    bark = plant_blades.material(f"{stem}_trunk", *t["colour"], double_sided=False)
    tm = bpy.data.meshes.new(f"trunk{suffix}")
    bm = bmesh.new()
    rings = [[bm.verts.new((r * scale * math.cos(k / 6 * math.tau), r * scale * math.sin(k / 6 * math.tau), z * lift))
              for k in range(6)]
             for r, z in ((t["radius"][0] * 1.3, 0.0), (t["radius"][1], t["height"]))]
    for lo, hi in zip(rings, rings[1:]):
        for k in range(6):
            bm.faces.new((lo[k], lo[(k + 1) % 6], hi[(k + 1) % 6], hi[k]))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(tm)
    bm.free()
    tm.materials.append(bark)
    trunk = bpy.data.objects.new(f"trunk{suffix}", tm)
    trunk["kyt_collision"] = "none"
    trunk["kyt_merge_group"] = tag
    coll = bpy.data.collections.new(f"trunk{suffix}")
    home.children.link(coll)
    coll.objects.link(trunk)


def place_blooms(bush, blooms, base_spec, bloom_spec, flower, bloom_mat, tag, suffix):
    """The flowers for one size of bush: points in `blooms`, the baseline and
    the peak's, each set just above the leaves under it; their counts."""
    # Every bloom is the card, placed by `kyt_blooms_on_points` on a point of
    # the `blooms` object at its own turn (`kyt_turn`) and size (`kyt_size`,
    # her "the clusters should have varying sizes"): same UVs, same painting.
    # Move a point in edit mode to move its bloom. Each sits just above the
    # leaves under it, measured from the skin as built (her "the blooms on the
    # hibiscus are being occluded by leaves"), so none is under a dome and
    # none floats higher than it needs to.
    bpy.context.view_layer.update()
    skin = bush.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    surface = BVHTree.FromPolygons([v.co.copy() for v in skin.vertices], [tuple(p.vertices) for p in skin.polygons])

    def above_leaves(foot, n, reach):
        """How far out the leaves stand over a flower's footprint: rays cast
        in along -n at its middle and six points round it; the outermost hit.
        Domes are big, so their faces, not only their rims, can pass over a
        flower."""
        side = n.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(n).normalized()
        top = 0.0
        for k in range(7):
            a = k / 6 * math.tau
            at = foot + (side * math.cos(a) + up * math.sin(a)) * (reach if k < 6 else 0.0)
            hit = surface.ray_cast(at + n * 1.5, -n, 3.0)[0]
            if hit is not None:
                top = max(top, (hit - foot).dot(n))
        return top

    # Through the year (her "during the peak season for that flower the
    # clusters should be increased three fold, and during winter we will
    # treat these as evergreen shrubs"): `blooms`, the baseline, and
    # `blooms_peak`, twice as many again, each its own merge group so the
    # Godot wrapper shows the baseline outside winter and both in the
    # species' peak chapter. The spots are one farthest-first run of three
    # times `count`: the first `count` are the baseline's, spread evenly on
    # their own, and the peak's fill between them.
    rng = random.Random(bloom_spec["seed"])
    sets = {"blooms": ([], [], []), "blooms_peak": ([], [], [])}
    for spot, (pos, n) in enumerate(bloom_spots(base_spec, dict(bloom_spec, count=bloom_spec["count"] * 3))):
        points, turns, sizes = sets["blooms" if spot < bloom_spec["count"] else "blooms_peak"]
        # A group: one card here and `group` more close by, overlapping a
        # little, tipped out and smaller (the hibiscus's twos and threes; the
        # azalea's truss is already a bunch on one card).
        side = n.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(n).normalized()
        ring = rng.randint(*bloom_spec["group"])
        spin = rng.uniform(0, math.tau)
        big = rng.uniform(*bloom_spec["sizes"])
        members = [(Vector((0, 0, 0)), 0.0, big)]
        for j in range(ring):
            a = spin + j / max(ring, 1) * math.pi * 0.9 + rng.uniform(-0.3, 0.3)
            d = side * math.cos(a) + up * math.sin(a)
            members.append((d * bloom_spec["radius"] * big * rng.uniform(1.05, 1.25), 0.45,
                            big * rng.uniform(0.7, 0.9)))
        for offset, tip, size in members:
            # Seated on the leaves as built (the egg or its saucer, not the
            # base's ideal outline, which stands off the egg's flat faces):
            # carried in along n to the first leaf it meets, facing out as
            # that face does, tipped up a little, then lifted only as far as
            # its own card needs to clear the leaves under it.
            foot = pos + offset
            out = n
            hit, face, _, _ = surface.ray_cast(foot + n * 1.5, -n, 3.0)
            if hit is not None:
                foot, out = hit, (face if face.dot(n) > 0 else -face)
            reach = bloom_spec["radius"] * size * 0.9
            facing = (out + (offset.normalized() * tip if offset.length else Vector()) + Vector((0, 0, 0.3))).normalized()
            lift = above_leaves(foot, facing, reach) + BLOOM_CLEAR + max(0.0, -bloom_spec["dome"]) * size
            rot = facing.to_track_quat("Z", "Y") @ Matrix.Rotation(rng.uniform(0, math.tau), 3, "Z").to_quaternion()
            at = foot + facing * lift
            # A low card tipped out may dip a corner under the soil: raise it
            # just clear (Check places a prop by z = 0).
            r = bloom_spec["radius"] * size
            low = min((rot @ Vector((x * r, y * r, 0.0))).z for x in (-1, 1) for y in (-1, 1))
            at.z = max(at.z, 0.01 - low)
            points.append(at)
            turns.append(rot.to_euler())
            sizes.append(size)
    bng = blooms_on_points_group()
    counts = {}
    for group, (points, turns, sizes) in sets.items():
        pm = bpy.data.meshes.new(group + suffix)
        pm.from_pydata([tuple(p) for p in points], [], [])
        pm.attributes.new("kyt_turn", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for e in turns for c in e])
        pm.attributes.new("kyt_size", "FLOAT", "POINT").data.foreach_set("value", sizes)
        pm.materials.append(bloom_mat)  # a slot, as the Purple Heart's leaf points carry; the card's own material shows
        placed_obj = bpy.data.objects.new(group + suffix, pm)
        placed_obj["kyt_collision"] = "none"
        placed_obj["kyt_merge_group"] = f"{tag}_{group}"
        blooms.objects.link(placed_obj)
        bmod = placed_obj.modifiers.new(bng.name, "NODES")
        bmod.node_group = bng
        plant_blades._set(bmod, bng, {"Bloom": flower})
        counts[group] = len(points)
    return counts


# --- The file ------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv or argv[0] not in SPECIES:
        raise SystemExit(f"leaf_skin: give one of {', '.join(SPECIES)} after --")
    name, spec = argv[0], SPECIES[argv[0]]
    export = bpy.data.collections["export"]
    blades = add_courses.child_collection("authored", "blades")
    layout = add_courses.child_collection("authored", "domes")
    if list(export.all_objects) or list(blades.objects) or list(layout.objects):
        if "--replace" not in argv:
            raise SystemExit("leaf_skin: export or authored/blades already hold something; "
                             "--replace clears them (an agent's earlier shape only)")
        for o in list(export.all_objects) + list(blades.objects) + list(layout.objects):
            bpy.data.objects.remove(o)
        for c in list(export.children):
            bpy.data.collections.remove(c)
        for group in ("kyt_leaf_skin", "kyt_dome_skin", "kyt_blooms_on_points"):
            if bpy.data.node_groups.get(group):
                bpy.data.node_groups.remove(bpy.data.node_groups[group])
        # The plant's own materials too, so they are made again from `SPECIES`:
        # the canvas keeps the leaf's (a fake user) as the colour it paints
        # from, and a rebuild would otherwise wear its first colour and gloss.
        for part in ("leaf", "core", "bloom_card", "trunk"):
            if bpy.data.materials.get(f"{name.split('_')[0]}_{part}"):
                bpy.data.materials.remove(bpy.data.materials[f"{name.split('_')[0]}_{part}"])
        for pool in (bpy.data.meshes, bpy.data.materials):
            for block in list(pool):
                if block.users == 0:
                    pool.remove(block)

    stem = name.split("_")[0]
    leaf_spec, base_spec, dome, bloom_spec = spec["leaf"], spec["base"], spec["dome"], spec.get("bloom")
    leaf_mat = plant_blades.material(f"{stem}_leaf", leaf_spec["colour"], leaf_spec["rough"], double_sided=True)
    core_mat = plant_blades.material(f"{stem}_core", *spec["core"], double_sided=False)

    if dome.get("cap_down") and spec.get("body"):
        # The crown dome is a polar cap cut from the body's own outline.
        reach, sink = crown_cap(spec["body"], dome["cap_down"], flare=dome.get("cap_flare"))
        dome = dict(dome, shape="crown_cap", reach=reach, crown_sink=sink)
    card = bpy.data.objects.new("blade_leaf", dome_card("blade_leaf", dome, leaf_mat))
    card["kyt_around"] = DOME_SHAPES[dome["shape"]][-1][2]  # the rim's corners: its leaves' tips stay inside them
    blades.objects.link(card)
    # A shrub with a `body` is that one sphere or egg, its own island on the
    # canvas painted as a dome is, with the domes laid out over its top
    # instead of round a hidden base.
    body = None
    if spec.get("body"):
        body = bpy.data.objects.new("blade_body", dome_card("blade_body", spec["body"], leaf_mat))
        body["kyt_around"] = DOME_SHAPES[spec["body"]["shape"]][-1][2]
        blades.objects.link(body)
        base_spec = body_base(spec["body"], base_spec)
    tier = None
    if spec.get("body", {}).get("tier"):
        tier = bpy.data.objects.new("blade_tier", body_tier("blade_tier", spec["body"], leaf_mat))
        tier["kyt_around"] = 8
        blades.objects.link(tier)
    topper = None
    if spec.get("body", {}).get("topper"):
        topper = bpy.data.objects.new("blade_topper", body_topper("blade_topper", spec["body"], leaf_mat))
        blades.objects.link(topper)
    flower = None
    if bloom_spec:
        bloom_mat = plant_blades.material(f"{stem}_bloom_card", *bloom_spec["colour"], double_sided=True)
        flower = bpy.data.objects.new("blade_bloom", bloom_card("blade_bloom", bloom_spec["radius"], bloom_spec["dome"],
                                                                bloom_mat))
        flower["kyt_slots"] = bloom_spec["slots"]  # its colourways, painted side by side on the canvas
        blades.objects.link(flower)
    plant_blades.lay_out_blades([b for b in (card, body, tier, topper, flower) if b])

    # Sizes (her "can we also vary the size of the shrubs themselves, one
    # smaller and one larger (flowers stay the same size)"): the base scaled,
    # the domes and the flowers not, so a larger bush wears more of each
    # (flower clusters by its surface, the scale squared). Each size is
    # its own merge groups, `<size>`, `<size>_blooms`, `<size>_blooms_peak`,
    # on the one canvas; the Godot wrapper's `size` shows one. The small and
    # large sit at the origin with the medium, in `size_small` and
    # `size_large`, hidden in the viewport: click their eyes to see them.
    # The tree form's trunk scales with its crown.
    counts = {}
    for tag, size in spec.get("sizes", {"medium": 1.0}).items():
        size = size if isinstance(size, dict) else dict(scale=size)
        scale = size["scale"]
        tall, lift = size.get("tall", scale), size.get("lift", scale)
        suffix = "" if tag == "medium" else f"_{tag}"
        home = export
        if tag != "medium":
            home = bpy.data.collections.new(f"size_{tag}")
            export.children.link(home)
        base = dict(base_spec, width=base_spec["width"] * scale, height=base_spec["height"] * tall,
                    lift=base_spec.get("lift", 0.0) * lift)
        bush = bpy.data.objects.new(f"bush{suffix}", gumdrop(f"bush{suffix}", base, core_mat))
        home.objects.link(bush)
        bush["kyt_collision"] = "none"
        bush["kyt_leaf_blades"] = True  # unwrap_blades.py lays out the leaf it places
        bush["kyt_merge_group"] = tag
        # A body's crown dome is a cap fitted to it, so it grows and sinks with
        # the body across the sizes; other domes keep their size.
        fitted = dict(dome, crown_size=(scale, scale, tall), crown_sink=dome.get("crown_sink", 0.0) * tall) if body else dome
        spots = dome_points(f"domes{suffix}", base, fitted, dome["seed"])
        layout.objects.link(spots)
        ng = dome_skin_group()
        mod = bush.modifiers.new(ng.name, "NODES")
        mod.node_group = ng
        plant_blades._set(mod, ng, {"Leaf": card, "Domes": spots, "Roundness": dome["roundness"],
                                    "Show core": dome["core"]})
        if body:
            plant_blades._set(mod, ng, {"Body": body, "Body scale": (scale, scale, tall), "Body lift": base["lift"]})
            if tier:
                plant_blades._set(mod, ng, {"Tier": tier})
            if topper:
                plant_blades._set(mod, ng, {"Topper": topper})
        if "trunk" in spec:
            add_trunk(spec["trunk"], scale, lift, stem, export if tag == "medium" else home, suffix, tag)
        counts[tag] = dict(blooms=0, blooms_peak=0)
        if flower:
            blooms = bpy.data.collections.new(f"blooms{suffix}")
            home.children.link(blooms)
            counts[tag] = place_blooms(bush, blooms, base, dict(bloom_spec, count=round(bloom_spec["count"] * scale * tall)),
                                       flower, bloom_mat, tag, suffix)
    for tag in counts:
        if tag != "medium":
            bpy.context.view_layer.layer_collection.children["export"].children[f"size_{tag}"].hide_viewport = True

    bpy.context.scene["kyt_godot_scene"] = spec["godot"]
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    card = sum(len(p.vertices) - 2 for p in flower.data.polygons) if flower else 0
    for tag, got in counts.items():
        b = bpy.data.objects["bush" if tag == "medium" else f"bush_{tag}"]
        ev = b.evaluated_get(dg).data
        tris = sum(len(p.vertices) - 2 for p in ev.polygons)
        zs = [v.co.z for v in ev.vertices]
        domes = len(bpy.data.objects["domes" if tag == "medium" else f"domes_{tag}"].data.vertices)
        print(f"leaf_skin: {name} {tag}: {domes} domes, "
              f"{got['blooms']} blooms ({got['blooms'] + got['blooms_peak']} at peak), "
              f"{tris + card * got['blooms']} triangles ({tris + card * (got['blooms'] + got['blooms_peak'])} at peak, "
              f"{tris} in winter), {max(zs):.2f} m tall, low {min(zs):.3f}")
    bpy.ops.wm.save_mainfile()
    print("leaf_skin: saved")


if __name__ == "__main__":
    main()
