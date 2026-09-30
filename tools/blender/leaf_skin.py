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
  paints one azalea or hibiscus flower, each colourway side by side
  along the canvas (`kyt_slots`), which a placement's Godot script picks,
  and inside each colourway's slot the flower again in each of `shades`
  (`kyt_shades`), lightest first; each flower's `kyt_shade` picks one.
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
- For a tree of clumps (`crown`, the coast live oak): `export/crown`, its
  core, wearing the hats on `authored/domes/clumps` (`kyt_clump_skin`), and
  `export/trunk/trunk`, the trunk and a branch up into every hat, which collides.

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
# sphere instead of a egg, and smaller"). The egg's outline is her ideal's,
# measured (her "the egg shapes just arent eggy enough, they still read as
# vertically stretched spheres. refer to this as more of an ideal base
# shape", `documentation/reference/azalea_bush/egg_topiary_ideal_shape.png`):
# `profile`, (depth, radius) as shares of its height and widest, 0.75 of its
# height across, widest two thirds of the way down, a long taper to a round
# top and a blunt base; its rings at its own `turns`, the third at its
# widest, the last on the soil before the base tucks under, so it stands on a
# broad base (her "the egg shape should be wider at the base").
EGG_IDEAL = [(0.0, 0.0), (0.01, 0.17), (0.04, 0.3), (0.083, 0.43), (0.125, 0.535), (0.167, 0.62), (0.208, 0.685),
             (0.25, 0.745), (0.333, 0.843), (0.417, 0.915), (0.5, 0.965), (0.583, 0.993), (0.646, 1.0), (0.708, 0.99),
             (0.792, 0.965), (0.833, 0.93), (0.875, 0.875), (0.917, 0.79), (0.948, 0.71), (0.969, 0.62), (0.99, 0.5),
             (1.0, 0.0)]
BODIES = {"egg": dict(width=0.753, profile=EGG_IDEAL, turns=(35.0, 70.0, 107.0, 140.0)),
          "sphere": dict(width=1.0, broad=0.0)}
BODY_TURNS = (35.0, 70.0, 105.0, 140.0)


def egg_outline(width, broad, turns):
    """(radius, depth below the top) at the top and at each of `turns`
    degrees round a body's outline, for a body one unit high."""
    def at(t):
        z = (1.0 - math.cos(t)) / 2.0  # 0 at the top, 1 at the bottom
        return width / 2.0 * math.sin(t) * (1.0 + broad * (z - 0.5)), z
    return [(0.0, 0.0)] + [at(math.radians(t)) for t in turns]


def body_outline(egg, turns):
    """`egg_outline` for a body in `BODIES`: from its measured `profile` if it
    has one (depth as the formula's, radius read off the profile), else the
    formula."""
    if "profile" not in egg:
        return egg_outline(egg["width"], egg["broad"], turns)

    def at(t):
        z = (1.0 - math.cos(math.radians(t))) / 2.0
        for (z0, r0), (z1, r1) in zip(egg["profile"], egg["profile"][1:]):
            if z0 <= z <= z1:
                return egg["width"] / 2.0 * (r0 + (r1 - r0) * (z - z0) / max(z1 - z0, 1e-9)), z
        return 0.0, z
    return [(0.0, 0.0)] + [at(t) for t in turns]


def body_turns(egg):
    """The degrees round a body's outline its rings lie at."""
    return egg.get("turns", BODY_TURNS)


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


for _name, _body in BODIES.items():
    DOME_SHAPES[_name] = outline_shape(body_outline(_body, body_turns(_body)))


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
    metres = body["reach"] / sum(s for s, _ in outline_steps(body_outline(egg, body_turns(egg))))
    cap = body_outline(egg, (down / 2.0, down))
    if flare is not None:
        widest = max(r for r, _ in body_outline(egg, range(5, 180, 5)))
        cap[-1] = ((1.0 + flare) * widest / grow, cap[-1][1])  # the whole cap is grown by `grow` after
    DOME_SHAPES["crown_cap"] = outline_shape(cap)
    reach = sum(s for s, _ in outline_steps(cap)) * metres * grow
    return reach, cap[-1][1] * metres * grow - clear


def sphere_reach(radius):
    """The `reach` (apex to rim along its outline) of a sphere body `radius`
    in metres."""
    unit = body_outline(BODIES["sphere"], body_turns(BODIES["sphere"]))
    return sum(s for s, _ in outline_steps(unit)) * 2.0 * radius


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
    unit = body_outline(egg, body_turns(egg))
    metres = body["reach"] / sum(s for s, _ in outline_steps(unit))
    rim = unit[-1][1] * metres  # the body's rim, at its pivot, lies this far below its top
    widest = max(r for r, _ in body_outline(egg, range(5, 180, 5))) * metres
    fine = body_outline(egg, [t / 2 for t in range(1, 2 * int(tier["down"]) + 1)])

    def along(t):
        """Distance along the outline from the top to `t` degrees, metres."""
        return sum(s for s, _ in outline_steps(fine[:int(round(t * 2)) + 1])) * metres

    rings = []
    for t in (tier["top"], tier["down"]):
        (r0, d0), (r1, d1) = body_outline(egg, (t - 1.0, t + 1.0))[1:]
        size = math.hypot(d1 - d0, r1 - r0)
        out_r, out_z = (d1 - d0) / size, (r1 - r0) / size  # outward, in (radius, height)
        r, d = body_outline(egg, (t,))[1]
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
    unit = body_outline(egg, body_turns(egg))
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


def sprig_card(name, strays, material):
    """A stray leaf grouping (her "stray leaf groupings need to be added
    also"): `leaves` leaf cards `length` long and `width` of that across, fanned
    `spread` degrees apart side to side (along x) from a foot at the origin,
    up +z, flat; placed with +z down the bush and +y out of it, so the fan
    lies on the shingles. The
    topper's one painted leaf on them all (`paint_canvas.py`, `cut_topper`).
    2 triangles a leaf."""
    length, half = strays["length"], strays["length"] * strays["width"] / 2.0
    verts, faces, flat = [], [], []
    for i in range(strays["leaves"]):
        a = math.radians((i - (strays["leaves"] - 1) / 2) * strays["spread"])
        along = Vector((math.sin(a), 0.0, math.cos(a)))
        side = Vector((math.cos(a), 0.0, -math.sin(a)))
        k = len(verts)
        verts += [-side * half, side * half, along * length + side * half, along * length - side * half]
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
        body=dict(shape="egg", reach=1.356,  # 0.98 m across, 0.85 m at its base, 1.15 m high
                  tier=dict(top=56.0, down=100.0, gap=0.05, flare=0.2, turn=36.8),
                  topper=dict(leaves=3, length=0.28, width=0.7, tilt=100.0, sink=0.0, turn=71.4)),
        sizes={"small": 0.75, "medium": 1.0, "large": 1.3},
        leaf=dict(colour=(0.40, 0.68, 0.26), rough=0.7),
        core=((0.16, 0.36, 0.13), 0.9),  # the carrier's; not shown
        dome=dict(courses=0, cap_down=64.0, cap_flare=0.15, crown_turn=22.5, roundness=0.3, core=False, seed=3),
        # One flower per card, a six-sided trumpet, 0.21 m across (her "make
        # the flowers on the azaleas all bigger proportionally", from 0.15; "each individual
        # azalea flower needs to be given a cone/trumpet shape to match their
        # real life counterparts"), in trusses of seven to eleven round a main
        # one ("their clusters need the same treatment as the hibiscus", "at
        # least twice the amount of blooms, small blooms, and buds"),
        # `count` trusses; three colourways painted side by side (`slots`:
        # pink, magenta, white), each in `shades` from light to dark (her
        # "the lightest will be a light pink almost white, the dark will be
        # almost fushia, and every shade in between"; `paint_canvas.py`).
        bloom=dict(radius=0.105, dome=-0.063, sides=6, count=10, group=(6, 10), small=(0.5, 0.65), sizes=(0.85, 1.15),
                   keep=0.6, clump=(3, 5), super_gap=2.8,
                   band=(15, 115), lie=0.0,
                   nestle=0.5, hug=None, behind=0.15, sink=0.006, seed=5, slots=3, shades=5,
                   colour=((0.97, 0.52, 0.76), 0.6),
                   bud=dict(length=0.171, width=0.117, count=(0, 1), cluster=(2, 3), green=0.5, near=(0.8, 1.0))),
        strays=dict(count=5, leaves=3, length=0.2, width=0.7, spread=30.0, lift=-3.0, band=(55, 125), hug=0.08, seed=12),
    ),
    "azalea_tree": dict(
        godot="res://scenes/world/landscape_kit/azalea_tree.tscn",
        base=dict(square=2.0, lift=0.85),  # the body's (`body_base`), on the trunk
        body=dict(shape="egg", reach=2.196,  # 1.59 m across, 1.37 m at its base, 1.87 m high
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
        bloom=dict(radius=0.105, dome=-0.063, sides=6, count=24, group=(6, 10), small=(0.5, 0.65), sizes=(0.85, 1.15),
                   keep=0.6, clump=(3, 5), super_gap=2.8,
                   band=(15, 150), lie=0.0,
                   nestle=0.5, hug=None, behind=0.3, sink=0.006, seed=11, slots=3, shades=5,
                   colour=((0.97, 0.52, 0.76), 0.6),
                   bud=dict(length=0.171, width=0.117, count=(0, 1), cluster=(2, 3), green=0.5, near=(0.8, 1.0))),
        strays=dict(count=8, leaves=3, length=0.26, width=0.7, spread=30.0, lift=-3.0, band=(55, 125), hug=0.08, seed=13),
    ),
    "hibiscus_shrub": dict(
        godot="res://scenes/world/landscape_kit/hibiscus_shrub.tscn",
        base=dict(square=2.0),  # the body's (`body_base`)
        body=dict(shape="egg", reach=1.622,  # 1.18 m across, 1.01 m at its base, 1.38 m high
                  tier=dict(top=56.0, down=100.0, gap=0.05, flare=0.25, turn=36.8),
                  # Her "expand the cluster crowning the hibiscus": 0.42 (was 0.3).
                  topper=dict(leaves=3, length=0.42, width=1.4, tilt=110.0, sink=-0.01, turn=71.4)),
        sizes={"small": 0.75, "medium": 1.0, "large": 1.3},
        leaf=dict(colour=(0.20, 0.44, 0.36), rough=0.55),
        core=((0.10, 0.26, 0.21), 0.9),  # the carrier's; not shown
        dome=dict(courses=0, cap_down=64.0, cap_flare=0.2, crown_turn=22.5, roundness=0.3, core=False, seed=6),
        # One flower per card, in loose twos and threes (her "hibiscus could
        # also benefit from some clustering"); four colourways (`slots`: red,
        # pink, yellow-red, pink-white), each in `shades` a little darker (her
        # "some blooms just being a slightly darker shade of red, by maybe 2%").
        bloom=dict(radius=0.16, dome=-0.07, sides=6, count=8, group=(0, 2), sizes=(0.85, 1.15), band=(15, 115), lie=0.0,
                   nestle=0.5, hug=None, behind=0.15, sink=0.006, seed=8, slots=4, shades=3, spread_seasons=True, spread_round=0.35, clear_leaves=True,
                   colour=((0.93, 0.20, 0.15), 0.55),
                   bud=dict(length=0.257, width=0.171, count=(0, 1), cluster=(2, 3), stand=0.5, uphill=True)),
        strays=dict(count=5, leaves=3, length=0.22, width=1.2, spread=35.0, lift=-3.0, band=(55, 125), hug=0.08, seed=14,
                    spread_out=True),
    ),
}
# The second version of each (her "dont forget our second version that is a
# sphere instead of a egg, and smaller", "yes they can be their own files"): a
# ball, its hat down 72 degrees so its hem lies round the ball's top third (her
# "it looks good because it hits around the top third of the sphere"), the
# brim flared wider than the ball ("have the hat flare out be larger than the
# base sphere", "it oculd be a bit more pronounced", then "flair the sphere
# tiers even more": 15%), and the egg's leaf topper ("put their approved
# sprout back").
for _shrub, _reach in (("azalea_bush", 1.2), ("hibiscus_shrub", 1.35), ("azalea_tree", 1.9)):
    SPECIES[f"{_shrub}_sphere"] = dict(
        SPECIES[_shrub], godot=f"res://scenes/world/landscape_kit/{_shrub}_sphere.tscn",
        body=dict(shape="sphere", reach=_reach, topper=SPECIES[_shrub]["body"]["topper"]),
        dome=dict(SPECIES[_shrub]["dome"], cap_down=72.0, cap_flare=0.15))
# The sphere tree's and sphere bush's clumps placed where their season's
# flowers are furthest off (`spread_seasons`), seated out from the body's
# middle (`envelope`).
SPECIES["azalea_tree_sphere"]["bloom"] = dict(SPECIES["azalea_tree"]["bloom"], spread_seasons=True, envelope=True)
# Clumps of two to four on the sphere bush: its baseline is ten trusses, and
# at three to five a clump, three clumps left a side of the small ball bare.
SPECIES["azalea_bush_sphere"]["bloom"] = dict(SPECIES["azalea_bush"]["bloom"], spread_seasons=True, envelope=True,
                                              clump=(2, 4))  # her "do the same for the azalea sphere bush"
# The coast live oak (PRP-PLANT-049; her "using the spherical shrubs we made,
# create a simplified version of a mature oak", 2026-09-29, after her photo in
# `documentation/reference/coastal_live_oak/`, a live oak sketched, and Mario
# Kart trees, "constructed somewhat similarly"): the sphere shrub's hat as it
# is, 72 degrees down with its brim flared 15% and turned 22.5, with its
# three-leaf topper (the brim flared further, below), without the ball (her
# "they skip the main 'ball' base of the sphere and just keep the 'stack of
# hats' that our shrubs are made of"),
# stacked in tiers as a broad crown (`crown`, `build_crown`) over a short,
# massive trunk forking into thick limbs that spread low and wide (`limbs`).
# Each hat's open underside is the dark band under the tier above. No flowers,
# evergreen, one size. `ball`: the sphere the hat is cut from, its radius;
# `tiers`: rings of hats, (how many, how far out, the height of their tops,
# their balls' radius, the first one's bearing), each hat put off true by
# `jitter` (out, up, degrees round, radius); `droop`: the lower two tiers
# further out and lower toward bearing 180 (-x, the photo's left) by up to
# (out, down); `flare`: a tier's brims spread that share of their ball
# further (the top hat, her "flare the top most tier"); `tilt`: each hat
# turned that share of the way from upright to facing out from `centre`. `core`: the crown's shaded middle, (radius,
# height) from the bottom up, closed, inside the tiers (not shown: the
# branches show instead). The topper keeps the shrubs' leaf to topper proportion (their 0.22 m
# leaves, 0.28 m topper), so its leaves read as the crown's.
SPECIES["coastal_live_oak"] = dict(
    godot="res://scenes/world/coastal_live_oak.tscn",
    stem="oak",
    base=dict(square=2.0),
    # The sprouts flared up (her "flare the top most tier and sprouts too",
    # "now flare jus the sprout", "flare means up", "right now they lay down
    # too much", then "they can tilt up a little bit"): 65 degrees from upright,
    # rising out of the hat, where the shrubs' lie over theirs at 100 (trials at
    # 100, 85, 72 and 60:
    # `documentation/screenshots/coastal-live-oak-2026-09-29/oak_sprout_up_trials.png`).
    body=dict(shape="sphere", reach=sphere_reach(2.2),
              topper=dict(leaves=3, length=0.8, width=0.7, tilt=65.0, sink=0.0, turn=71.4)),
    leaf=dict(colour=(0.34, 0.50, 0.18), rough=0.75),
    core=((0.13, 0.24, 0.09), 0.95),
    # The hat's brim flared 30% past its ball (the shrubs' 15%; her "the top
    # tier but not the sprout on the top of each dome needs to be flared more").
    dome=dict(courses=0, cap_down=72.0, cap_flare=0.3, crown_turn=22.5, roundness=0.25, core=False, seed=21),
    crown=dict(hats_only=True, ball=2.2, centre=(0.0, 0.0, 5.0), tilt=0.45, seed=21,
               tiers=[(1, 0.0, 9.6, 2.3, 0.0), (4, 2.4, 8.5, 2.1, 30.0), (6, 4.3, 7.2, 2.1, 15.0),
                      (8, 5.3, 5.8, 1.95, 22.5)],
               jitter=(0.3, 0.25, 8.0, 0.1), droop=(0.5, 0.6), flare={0: 0.15},
               # A second tier on each segment, under its sprout (her "can we
               # add another tier to each segment?", "under the sprout", after
               # "the top tier can also be a bit more proud from the tier
               # beneath it"): the hat's shape `scale` the size, turned `turn`
               # degrees from the one under it, its brim `proud` metres over
               # that hat's leaves; the sprout on it. Its own card and island
               # (`blade_upper`), so its painted leaves are the full size (her
               # "yeah make that fix", when sharing the hat's made them 0.6).
               # Brought down 0.15 m (her "lets move the new tier down a little
               # on each segment").
               upper=dict(scale=0.6, proud=0.15, turn=36.9),
               core=[(0.0, 4.4), (2.8, 4.6), (4.3, 5.3), (4.4, 6.0), (3.6, 7.2), (2.2, 8.3), (0.0, 8.8)]),
    # Stray leaf clusters (her "can we add the random leaf clusters like how we
    # added to the shrubs"): the shrubs' three-leaf fans (`sprig_card`,
    # `place_sprigs`), their leaves the oak's size, `count` spread evenly over
    # the crown (`spread_out`), only where a hat slopes at least `steep`
    # degrees, so they lie on it and never stand out like wings (the shrubs'
    # band did that for a body), and off each hat's sprouts.
    strays=dict(count=24, leaves=3, length=0.7, width=0.7, spread=30.0, lift=-3.0, band=(0, 150), steep=35.0,
                seed=22, spread_out=True),
    # Acorns (her "lets use the same base we used for the flower buds and make
    # acorns", "some green some brown"): the buds' spindle (`bud_card`),
    # `length` by `width`, oversized as the buds are, its cap painted at its fat
    # end (`paint_canvas.py`, `cut_acorn`), in `count` clusters of `cluster`
    # spread evenly, hanging point down (leaning `lean` out) from the hats'
    # brims where a brim is on the outside of the crown, none into a hat below
    # nor lower than `low`. By season (her "green in summer and brown in
    # fall"): the same acorns twice, green (`blade_acorn_green`) in merge group
    # `summer_acorns` and brown (`blade_acorn`) in `fall_acorns`, the wrapper
    # showing one. Fall also has a few on the ground under the tree, and
    # leaves (her "fall can have a few acorns and leaves on the ground under the
    # tree"): `ground`, `acorns` lying on their sides and `leaves` flat, on
    # three single-leaf cards (`blade_fallen_a` to `_c`), scattered between
    # `from_trunk` metres off the trunk and `reach` of the crown's radius, in
    # merge group `fall_ground`. The foliage's fall colours are a second
    # canvas (`paint_canvas.py`, `fall`), not geometry.
    # Winter and spring keep the leafy tree, each on a canvas of its own (her
    # "its kind of unsettling... maybe we go back to the fall tree as a
    # baseline, in winter it just gets more sparse ... just more see through
    # parts in the leaves and the leaves maybe turn red-brown", "spring uses
    # the same setup but makes the foliage bright green and the acorns become
    # buds and there are more buds"; `paint_canvas.py`, `seasons`; a bare tree
    # of twigs and branchlets was tried for both and dropped): `winter` of
    # the brown acorns stay on in merge group `winter_acorns`; in spring
    # `buds` leaf buds (`blade_leaf_bud`, `bud` long and across) stand round
    # the acorns' brim places and more, farthest first, in clusters of
    # `cluster` scattered `scatter` metres over the leaves, pointing up and
    # out, in `spring_buds`.
    acorns=dict(length=0.36, width=0.2, count=22, cluster=(1, 3), lean=0.35, low=2.2, seed=23,
                ground=dict(acorns=10, leaves=30, leaf_length=0.65, from_trunk=1.8, reach=0.85, seed=24),
                winter=3, buds=dict(count=60, cluster=(1, 3), bud=(0.2, 0.11), scatter=0.5, seed=26)),
    # No hat floats (her "there are some bad errors in the last example,
    # where the tree greenery just floats with no branches ... we however can
    # do better", "like a series of umbrellas on a shishkabob"): each hat is
    # held by its own branch (`hat_branches`), turning up into its middle
    # along its axis as an umbrella's shaft does. `trunk`, (point, radius)
    # from the foot, metres: short and massive, flaring to the ground (her
    # photo and sketch), forking at its top into the leader, which carries the
    # top hat and the tier under it, and `majors` major limbs spreading low
    # and wide, each forking `split` of the way out into a scaffold limb to
    # each of its hats of the lowest tier; each hat of the tier above that
    # branches off the scaffold limb nearest it round the tree. Radii (start,
    # end) per kind of branch; `bend`, how far a branch's knee drops below the
    # straight line (a share of its length), so a limb spreads out and then
    # turns up into its hat.
    limbs=dict(colour=((0.34, 0.28, 0.22), 0.95), sides=8, twig_sides=6, bend=0.12,
               trunk=[((0.0, 0.0, 0.0), 1.15), ((0.0, 0.0, 0.4), 0.8), ((0.05, 0.0, 1.2), 0.68),
                      ((0.1, 0.0, 2.0), 0.6)],
               leader=(0.45, 0.2), majors=4, split=0.4, major=(0.52, 0.38), scaffold=(0.34, 0.15),
               branch=(0.22, 0.11),
               # The bark's grain (`paint_canvas.py --bark`): its texture `tile`
               # metres round and along, wrapped up every limb; and `knots` where
               # branches broke away long ago (her "add a few large knots where a
               # branch might have detached a long time ago"), on the trunk,
               # leader and major limbs (the first `on` paths), their stubs'
               # material `knot_colour` under the end grain `--bark` paints.
               # Grown on thick limbs (her "lets enlarge the pattern on the
               # larger branches and even more on the central trunk"): `tile_grow`.
               tile=(1.0, 2.0), tile_grow=(0.2, 0.7), knot_colour=((0.62, 0.46, 0.28), 1.0),
               knots=dict(count=5, radius=(0.28, 0.4), on=6, along=(0.3, 0.7), seed=29)),
)
BLOOM_CLEAR = 0.01  # a bloom rests this far off the leaves it touches
BLOOM_FLOAT = 0.03  # a bloom whose middle ends further than this off the leaves is left out (her "i see some floating flowers")
LEAF_TIP = 0.08  # how far in from a dome's rim its leaves are whole, not cut between their tips
LEAF_CLEAR = 0.02  # with `clear_leaves`, a flower's or bud's rim this far off a leaf cluster's leaves


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


def bloom_card(name, radius, dome, material, sides=4):
    """The flowers' card (her "needs to be optimized for using textures"): a
    square, or `sides` round, `radius` from its middle to each side, its
    middle `dome` proud; the texture paints the flowers on it. A hibiscus's
    is a cone, its middle sunk (her "the individual flowers can be little
    more conical"), six round so it reads as a funnel, not a folded square.
    A triangle a side."""
    corner = radius / math.cos(math.pi / sides)
    verts = [(0.0, 0.0, dome)] + [(corner * math.cos((k + 0.5) / sides * math.tau),
                                   corner * math.sin((k + 0.5) / sides * math.tau), 0.0) for k in range(sides)]
    faces = [(0, 1 + k, 1 + (k + 1) % sides) for k in range(sides)]
    return card_mesh(name, verts, faces, material)


def bud_card(name, length, width, material):
    """A flower bud (her "flower buds need to be added"): a closed spindle
    `length` long from its foot to its point and `width` across a third of the
    way up, four round, oversized (her "all buds should be larger and
    oversized"); painted green at its foot, the sepals, and the
    flower's colour up to its point (`paint_canvas.py`, `cut_bud`), so it
    takes the colourway with the flowers. Laid out flat as seen from the side.
    Eight triangles."""
    verts = [(0.0, 0.0, 0.0)] + [(width / 2 * math.cos(k / 4 * math.tau), width / 2 * math.sin(k / 4 * math.tau),
                                  length * 0.35) for k in range(4)] + [(0.0, 0.0, length)]
    faces = [(0, 1 + (k + 1) % 4, 1 + k) for k in range(4)] + [(5, 1 + k, 1 + (k + 1) % 4) for k in range(4)]
    flat = [(v[0], v[2]) for v in verts]
    return card_mesh(name, verts, faces, material, flat)


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


def body_distance(base):
    """How far a point stands off a body (the egg or ball under the hat and
    tier), from its outline turned round (`base`'s profile, from the ground
    up): a function of the point, metres."""
    outline = [(r * base["width"] / 2.0, base.get("lift", 0.0) + h * base["height"]) for r, h in base["profile"]]

    def off(p):
        q = Vector((p.xy.length, p.z))
        best = float("inf")
        for (r0, z0), (r1, z1) in zip(outline, outline[1:]):
            a, b = Vector((r0, z0)), Vector((r1, z1))
            t = max(0.0, min(1.0, (q - a).dot(b - a) / max((b - a).length_squared, 1e-12)))
            best = min(best, (a + (b - a) * t - q).length)
        return best
    return off


def bloom_spots(skin, surface, base, spec, keep_off=0.0, span=0.0, avoid=()):
    """`count` places on the leaves as built, spread evenly, each (place,
    outward normal): many candidates over the skin by area, kept `band`
    degrees round the body from its top (the hat, the tier), only where the
    leaves face out with nothing standing over them (not under a brim, where
    a flower would be pushed out past it into the air) and leaves under it
    `span` all round (not on a brim's edge, where half of it would hang in
    the air), and clear of the topper, `keep_off` from the middle; with
    `hug`, only where the leaves lie no more than that off the body itself,
    not out on a hat's or tier's flare (her "some are floating on the tops of
    the flairs"); none within reach of a point of `avoid` ((place, reach),
    the leaf clusters); then the highest, and each next the farthest from
    those taken."""
    rng = random.Random(spec["seed"])
    top = base.get("lift", 0.0) + base["height"]
    middle = Vector((0.0, 0.0, top - base["height"] / 2))
    tris = []
    for p in skin.polygons:
        vs = [skin.vertices[i].co.copy() for i in p.vertices]
        for k in range(1, len(vs) - 1):
            area = (vs[k] - vs[0]).cross(vs[k + 1] - vs[0]).length / 2
            if area > 1e-8:
                tris.append((vs[0], vs[k], vs[k + 1], area))
    lo, hi = spec["band"]
    off_body = body_distance(base) if spec.get("hug") is not None and "profile" in base else None
    cands = []
    for a, b, c, _ in rng.choices(tris, weights=[t[3] for t in tris], k=6000):
        u, v = rng.random(), rng.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        pos = a + (b - a) * u + (c - a) * v
        down = math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * max(0.0, top - pos.z) / base["height"]))))
        if not lo <= down <= hi or (pos.xy.length < keep_off and down < 45.0):
            continue
        if off_body is not None and off_body(pos) > spec["hug"]:
            continue
        if any((pos - at).length < reach for at, reach in avoid):
            continue
        n = (b - a).cross(c - a).normalized()
        n = n if n.dot(pos - middle) > 0 else -n
        if spec.get("steep") is not None and n.z > math.cos(math.radians(spec["steep"])):
            continue  # with `steep`, only where the leaves slope at least that many degrees
        hit = surface.ray_cast(pos + n * 1.5, -n, 3.0)[0]
        if hit is None or (hit - pos).length > 0.01:
            continue
        side = n.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        ups = side.cross(n)
        if any((h := surface.ray_cast(pos + d * span + n * 0.3, -n, 0.6)[0]) is None or abs((h - pos).dot(n)) > 0.1
               for d in (side, -side, ups, -ups)):
            continue
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
    by `kyt_size`, realized so Send merges it with its UVs and material; its
    UVs slid `kyt_shade` Shade steps along the canvas, onto the copy of the
    flower painted in that shade (her "vary the lightness and darkness of
    the flower blooms")."""
    ng, io = plant_blades._node_group("kyt_blooms_on_points", (("Bloom", "NodeSocketObject", None),
                                                              ("Shade step", "NodeSocketFloat", 0.0)))
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
    shade = N("GeometryNodeInputNamedAttribute")
    shade.data_type = "FLOAT"
    shade.inputs["Name"].default_value = "kyt_shade"
    uv = N("GeometryNodeInputNamedAttribute")
    uv.data_type = "FLOAT_VECTOR"
    uv.inputs["Name"].default_value = "UVMap"
    along = N("ShaderNodeMath")
    along.operation = "MULTIPLY"
    ng.links.new(shade.outputs["Attribute"], along.inputs[0])
    ng.links.new(gin.outputs["Shade step"], along.inputs[1])
    slide = N("ShaderNodeCombineXYZ")
    ng.links.new(along.outputs[0], slide.inputs["X"])
    moved = N("ShaderNodeVectorMath")
    moved.operation = "ADD"
    ng.links.new(uv.outputs["Attribute"], moved.inputs[0])
    ng.links.new(slide.outputs[0], moved.inputs[1])
    store = N("GeometryNodeStoreNamedAttribute")
    store.data_type = "FLOAT2"
    store.domain = "CORNER"
    store.inputs["Name"].default_value = "UVMap"
    link(ng, real, "Geometry", store, "Geometry")
    ng.links.new(moved.outputs[0], store.inputs["Value"])
    link(ng, store, "Geometry", gout, "Geometry")
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


def place_blooms(bush, blooms, base_spec, bloom_spec, flower, bloom_mat, tag, suffix, keep_off=0.0, bud=None, avoid=(),
                 bud_green=None, leaves=()):
    """The flowers for one size of bush: points in `blooms`, the baseline and
    the peak's, each set just above the leaves under it, none within
    `keep_off` of the middle of the top (the topper), and their `bud`s;
    their counts."""
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

    def resting(foot, n, radius, dome, reach):
        """How far out along n a flower's card sits resting on the leaves
        (her "all flowers need to be touching the greenery"): rays cast in
        along -n at its middle and six points round it `reach` out, and the
        card as low as its own shape lets it go over each, its middle `dome`
        proud of its rim (`radius`). So a mound comes down onto the leaves at
        its rim and a cone (a hibiscus, an azalea) rests on its middle with its
        petals flaring out; past `reach`, out to its rim, it
        may tuck in among them. Domes are big, so their faces, not only their
        rims, can pass over a flower."""
        side = n.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(n).normalized()
        low = -1.0
        for k in range(7):
            a = k / 6 * math.tau
            r = reach if k < 6 else 0.0
            at = foot + (side * math.cos(a) + up * math.sin(a)) * r
            hit = surface.ray_cast(at + n * 1.5, -n, 3.0)[0]
            if hit is not None:
                low = max(low, (hit - foot).dot(n) - dome * max(0.0, 1.0 - r / radius))
        return low

    # Through the year (her "during the peak season for that flower the
    # clusters should be increased three fold, and during winter we will
    # treat these as evergreen shrubs"): `blooms`, the baseline, and
    # `blooms_peak`, twice as many again, each its own merge group so the
    # Godot wrapper shows the baseline outside winter and both in the
    # species' peak chapter. The spots are one farthest-first run of three
    # times `count`: the first `count` are the baseline's, spread evenly on
    # their own, and the peak's fill between them.
    off_body = body_distance(base_spec) if bloom_spec.get("hug") is not None and "profile" in base_spec else None
    top = base_spec.get("lift", 0.0) + base_spec["height"]

    def on_topper(p):
        """On the topper's leaves: near the middle, within 45 degrees of the
        top, as the flowers' spots are kept off it (`bloom_spots`)."""
        return keep_off > 0.0 and p.xy.length < keep_off and top - p.z < (1.0 - math.cos(math.radians(45.0))) / 2.0 * base_spec["height"]

    behind = bloom_spec.get("behind", 0.1)

    def supported(p, n, reach, depth=None, over_ok=False):
        """Leaves under `reach` all round `p` on the face out along `n`, no
        further behind it than `behind` (the tree's may cross a brim's edge
        onto the leaves below it: her "why does it need to fit in that
        space", of clumps held to one strip between the hat and the tier)."""
        side = n.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        ups = side.cross(n)
        deep = behind if depth is None else depth
        for d in (side, -side, ups, -ups):
            h = surface.ray_cast(p + d * reach + n * 0.3, -n, 0.3 + deep + 0.1)[0]
            # With `over_ok`, leaves standing over it (a brim above a flower
            # under it) count, only nothing close behind it does not.
            if h is None or (-(h - p).dot(n) if over_ok else abs((h - p).dot(n))) > deep:
                return False
        return True

    rng = random.Random(bloom_spec["seed"])
    bud_rng = random.Random(bloom_spec["seed"] + 101)  # its own, so buds leave the flowers where they were
    # Each flower's shade, 0 (lightest) to `shades` - 1 (darkest), on the
    # canvas beside its colourway (her "vary the lightness and darkness of
    # the flower blooms ... to create some visual variety"): a group's own
    # shade, each of its flowers that or the next either way, so a truss
    # reads lighter or darker and still varies inside. Its own random, so the
    # flowers stay where they were.
    shade_rng = random.Random(bloom_spec["seed"] + 202)
    shades = bloom_spec.get("shades", 1)
    shade_sets = {"blooms": [], "blooms_peak": []}
    bud_spec = bloom_spec.get("bud") if bud else None
    sets = {"blooms": ([], [], []), "blooms_peak": ([], [], [])}
    bud_sets = {"blooms": ([], [], []), "blooms_peak": ([], [], [])}
    green_sets = {"blooms": ([], [], []), "blooms_peak": ([], [], [])}  # buds not showing their colour yet
    discs, bud_jobs = [], []  # every flower's middle and radius; the groups' buds to place
    span = bloom_spec["radius"] * sum(bloom_spec["sizes"]) / 2 * 0.7 + LEAF_TIP
    core = Vector((0.0, 0.0, base_spec.get("lift", 0.0) + base_spec["height"] * 0.55))

    def envelope_seat(d):
        """The leaves out along `d` from the body's middle, whichever lie
        outermost there (hat, brim, tier or body): (place, face out), or
        None."""
        hit, face, _, _ = surface.ray_cast(core + d * 3.0, -d, 3.0)
        if hit is None:
            return None
        return hit, (face if face.dot(d) > 0 else -face)

    def group_at(pos, n, season):
        """One group round `pos` (an azalea's truss, a hibiscus's twos and
        threes): its flowers into `season`'s set, its buds queued; whether any
        of its flowers was placed."""
        points, turns, sizes = sets[season]
        # A group: one card here and `group` more close by, overlapping a
        # little, tipped out and smaller (the hibiscus's twos and threes, the
        # azalea's trusses).
        side = n.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(n).normalized()
        ring = rng.randint(*bloom_spec["group"])
        spin = rng.uniform(0, math.tau)
        big = rng.uniform(*bloom_spec["sizes"])
        # Round the main flower evenly, a third of a turn apart or closer,
        # not swept along an arc (her "the clustering of the hibiscus is kind
        # of odd": a chain of flowers), close in, each tucked just under it.
        # With `small`, every other one round it a small bloom, a little
        # further out (her azalea "clusters to have at least twice the amount
        # of blooms, small blooms, and buds").
        members = [(Vector((0, 0, 0)), 0.0, big)]
        small = bloom_spec.get("small")
        for j in range(ring):
            a = spin + j / max(ring, 3) * math.tau + rng.uniform(-0.3, 0.3)
            d = side * math.cos(a) + up * math.sin(a)
            tiny = small is not None and j % 2 == 1
            members.append((d * bloom_spec["radius"] * big * rng.uniform(0.75, 0.9) * (1.2 if tiny else 1.0), 0.45,
                            big * (rng.uniform(*small) if tiny else rng.uniform(0.7, 0.9))))
        placed, made = [], []  # the group's flowers that were placed: (offset, size); (place, turn, size, disc)
        for offset, tip, size in members:
            # Seated on the leaves as built (the egg or its saucer, not the
            # base's ideal outline, which stands off the egg's flat faces):
            # carried in along n to the first leaf it meets, facing out as
            # that face does, tipped `lie` of the way to facing straight up
            # (seen from above, as a standing eye sees a bush, and never
            # edge-on sticking out of its side), then lifted only as far as
            # its own card needs to clear the leaves under it.
            # A partner off the bush's edge, or that would drop in under a
            # brim, is left out.
            foot = pos + offset
            if bloom_spec.get("envelope"):
                # Out from the body's middle, onto whichever leaves lie
                # outermost there, so a group runs over a brim's edge onto the
                # body below it (her "fix the clusters under the hat on the
                # sphere tree"): dropped along its middle's normal instead, a
                # flower past the brim fell a long way and was left out.
                seat = envelope_seat((foot - core).normalized())
                if seat is None:
                    continue
                foot, out = seat
            else:
                hit, face, _, _ = surface.ray_cast(foot + n * 1.5, -n, 3.0)
                if hit is None or (hit - foot).dot(n) < -0.1:
                    continue
                foot, out = hit, (face if face.dot(n) > 0 else -face)
            radius = bloom_spec["radius"] * size
            facing = out.lerp(Vector((0, 0, 1)), bloom_spec["lie"]).normalized()
            facing = (facing + (offset.normalized() * tip if offset.length else Vector())).normalized()
            # Sunk `sink` in among the leaves, so its petals lie close over them
            # (her "make sure the flowers attach closer to the base of the bush",
            # "sit closer to the leaves", "a few more mm closer to the core").
            lift = (resting(foot, facing, radius, bloom_spec["dome"] * size, radius * bloom_spec["nestle"]) + BLOOM_CLEAR
                    - bloom_spec.get("sink", 0.0) * size)
            if ring and not offset.length:
                lift += 0.02  # a group's main flower over its partners
            rot = facing.to_track_quat("Z", "Y") @ Matrix.Rotation(rng.uniform(0, math.tau), 3, "Z").to_quaternion()
            at = foot + facing * lift
            # Its middle down onto the leaves under it where the card was held
            # up by a leaf beside it (a brim or tier over its edge, which then
            # tucks over it), so none stands off the leaves; one with nothing
            # under its middle is left out.
            middle = at + facing * bloom_spec["dome"] * size
            under = surface.ray_cast(middle + facing * 0.05, -facing, 1.0)[0]
            if under is None:
                continue
            want = BLOOM_CLEAR - bloom_spec.get("sink", 0.0) * size
            gap = (middle - under).dot(facing)
            if gap > want:
                at -= facing * (gap - want)
            if surface.find_nearest(at + facing * bloom_spec["dome"] * size)[3] > BLOOM_FLOAT:
                continue
            # Every flower of a group as its first is, where it ends: not out
            # on a flare, not on the topper, whole leaves under the whole of it
            # (not over a dome's rim, where the sky shows between the leaves'
            # tips, nor past a hat's edge). Its seat can be the egg under a
            # brim, and the flower then lifted onto the brim's rim.
            if (off_body is not None and off_body(under) > bloom_spec["hug"]) or on_topper(under):
                continue
            if not supported(under, facing, bloom_spec["radius"] * size * 0.9 + LEAF_TIP):
                continue
            # Seated from the body's middle, one could sit on a brim's very rim,
            # the sky showing between the leaves' tips round it: whole leaves a
            # leaf tip all round it, close under it.
            if bloom_spec.get("envelope") and not supported(under, facing, LEAF_TIP, 0.05, over_ok=True):
                continue
            # A low card tipped out may dip a corner under the soil: raise it
            # just clear (Check places a prop by z = 0).
            r = bloom_spec["radius"] * size
            low = min((rot @ Vector((x * r, y * r, 0.0))).z for x in (-1, 1) for y in (-1, 1))
            at.z = max(at.z, 0.01 - low)
            # Off the leaf clusters' own leaves (`leaves`, with `clear_leaves`).
            if any((at - q).length < r * 1.1 + LEAF_CLEAR for q in leaves):
                continue
            made.append((at, rot.to_euler(), size, (at + facing * bloom_spec["dome"] * size, bloom_spec["radius"] * size)))
            placed.append((offset, size))
        # A group left with too few of its flowers is left out whole, not
        # left as one or two strays (her "there are still scattered flowers on
        # the tree version of the azalea"); another place makes it up.
        if len(placed) < max(1, math.ceil(bloom_spec.get("keep", 0.0) * len(members))):
            return False
        own = shade_rng.randrange(shades)
        for at, turn, size, disc in made:
            points.append(at)
            turns.append(turn)
            sizes.append(size)
            discs.append(disc)
            shade_sets[season].append(min(shades - 1, max(0, own + shade_rng.randint(-1, 1))))
        # Buds (her "flower buds need to be added"): `count` closed buds just
        # past this group's rim, each standing out of the leaves as built,
        # leaning away from the flowers, its foot tucked in among them; the
        # baseline's flowers' buds show with them, the peak's with the peak.
        # Only by flowers that were placed, just past how far they reach
        # (her "i still see some stray green buds on the azalea").
        if bud_spec and placed:
            bud_jobs.append((season, pos, n, side, up, placed))
        return bool(placed)

    # Groups gathered into super clusters of `super` side by side, their
    # middles `super_gap` flower radii apart (her "on azaleas, we can cluster
    # the clusters to make super clusters"): as many flowers as before, fewer
    # and fuller places.
    per = bloom_spec.get("super", (1, 1))
    # Twice the places it needs, in turn: a place none of whose flowers could
    # be placed (all out on a flare, off an edge or on the topper) is made up
    # by the next, so each season keeps its number of groups.
    clumps = []  # the clumps' middles, none placed over another
    def around(pos, n, each, spread, gap, season):
        """`each` at `pos`, then `spread` more of them round it `gap` flower
        radii off (up to four tries apiece round it): how many groups they
        placed."""
        made = each(pos, n, season)
        if spread[1] > 1:
            side = n.cross(Vector((0, 0, 1)))
            side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
            up = side.cross(n).normalized()
            many, spin = rng.randint(*spread), rng.uniform(0, math.tau)
            for k in range(1, many):
                for _try in range(4):  # round the first until one takes
                    a = spin + k / many * math.tau + rng.uniform(-0.6, 0.6)
                    q = pos + (side * math.cos(a) + up * math.sin(a)) * bloom_spec["radius"] * gap
                    hit, face, _, _ = surface.ray_cast(q + n * 1.5, -n, 3.0)
                    if hit is None or (hit - q).dot(n) < -0.1:
                        continue
                    got = each(hit, face if face.dot(n) > 0 else -face, season)
                    if got:
                        made += got
                        break
        return made

    def one(pos, n, season):
        return 1 if group_at(pos, n, season) else 0

    lo, hi = bloom_spec["band"]

    def fits(q, n):
        """Where a group round `q` would sit, if it could: (place, face) on
        the leaves, within the band, close over the body, off the topper, with
        leaves under it all round; else None."""
        hit, face, _, _ = surface.ray_cast(q + n * 1.5, -n, 3.0)
        if hit is None or (hit - q).dot(n) < -0.1:
            return None
        face = face if face.dot(n) > 0 else -face
        down = math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * max(0.0, top - hit.z) / base_spec["height"]))))
        if not lo <= down <= hi or on_topper(hit) or (off_body is not None and off_body(hit) > bloom_spec["hug"]):
            return None
        return (hit, face) if supported(hit, face, bloom_spec["radius"] * 0.9) else None

    def envelope_spots(count, farthest=True):
        """`count` places spread evenly over the body's smooth outline turned
        round, as if the hat and tier were not there, each dropped onto the
        leaves it looks down on (hat, brim, tier or body): (place, face),
        farthest first. So clumps are spread over the whole crown, not held
        in the strips the brims leave between them (her "the tree still just
        has three clumps in a row", "the flowers dont need a tier system")."""
        prof = base_spec["profile"]
        middle_z = base_spec.get("lift", 0.0) + base_spec["height"] * 0.55
        cands = []
        for _ in range(8000):
            h = rng.uniform(0.0, 1.0)
            for (r0, h0), (r1, h1) in zip(prof, prof[1:]):
                if h0 <= h <= h1:
                    r = r0 + (r1 - r0) * (h - h0) / max(h1 - h0, 1e-9)
                    break
            else:
                continue
            if rng.random() > r:  # by area: fewer where it is narrow
                continue
            a = rng.uniform(0, math.tau)
            p = Vector((r * base_spec["width"] / 2 * math.cos(a), r * base_spec["width"] / 2 * math.sin(a),
                        base_spec.get("lift", 0.0) + h * base_spec["height"]))
            d = (p - Vector((0.0, 0.0, middle_z))).normalized()
            hit, face, _, _ = surface.ray_cast(p + d * 1.0, -d, 2.0)
            if hit is None:
                continue
            face = face if face.dot(d) > 0 else -face
            down = math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * max(0.0, top - hit.z) / base_spec["height"]))))
            if not lo <= down <= hi or on_topper(hit):
                continue
            cands.append((hit, face))
            if len(cands) >= 2500:
                break
        if not cands or not farthest:
            return cands
        taken = [max(cands, key=lambda c: c[0].z)]
        near = [min((c[0] - taken[0][0]).length, 1e9) for c in cands]
        while len(taken) < min(count, len(cands)):
            k = max(range(len(cands)), key=lambda i: near[i])
            taken.append(cands[k])
            near = [min(near[i], (cands[i][0] - cands[k][0]).length) for i in range(len(cands))]
        return taken

    def fits_seat(seat):
        """`fits` for a place already on the leaves."""
        if seat is None:
            return None
        hit, face = seat
        down = math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * max(0.0, top - hit.z) / base_spec["height"]))))
        if not lo <= down <= hi or on_topper(hit) or (off_body is not None and off_body(hit) > bloom_spec["hug"]):
            return None
        return (hit, face) if supported(hit, face, bloom_spec["radius"] * 0.9) else None

    def clump_at(pos, n, season):
        """A compact clump (her "you made the super cluster a fanned out
        line"): a group here and the rest of `clump` evenly round it
        `super_gap` flower radii off, only where three fifths of them fit,
        so none is left lopsided or strung out along the bush: how many
        groups it placed."""
        many = rng.randint(*bloom_spec["clump"])
        side = n.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(n).normalized()
        spin = rng.uniform(0, math.tau)
        gap = bloom_spec["radius"] * bloom_spec.get("super_gap", 3.2)
        rings = [pos + (side * math.cos(a) + up * math.sin(a)) * gap for a in (spin + k / (many - 1) * math.tau for k in range(many - 1))]
        if bloom_spec.get("envelope"):
            spots_here = [(pos, n)] + [fits_seat(envelope_seat((q - core).normalized())) for q in rings]
        else:
            spots_here = [(pos, n)] + [fits(q, n) for q in rings]
        spots_here = [sp for sp in spots_here if sp is not None]
        if len(spots_here) < math.ceil(0.6 * many):
            return 0
        return sum(1 for q, m in spots_here if group_at(q, m, season))

    def super_at(pos, n, season):
        return around(pos, n, one, per, bloom_spec.get("super_gap", 3.2), season)

    # Super clusters gathered again, `mega` of them `mega_gap` flower radii
    # apart; or, with `clump`, groups in compact clumps (`clump_at`, the
    # tree's: her "on the tree version of the azaleas, cluster the existing
    # clusters again", then "you made the super cluster a fanned out line").
    mega = bloom_spec.get("mega", (1, 1))
    if bloom_spec.get("clump"):
        spots = envelope_spots(bloom_spec["count"] * 30)
    else:
        spots = bloom_spots(skin, surface, base_spec, dict(bloom_spec, count=bloom_spec["count"] * 6), keep_off, span, avoid)
    done = 0  # groups placed
    made_by = {"blooms": 0, "blooms_peak": 0}  # groups placed in each season
    if bloom_spec.get("spread_seasons"):
        # Each next clump where the season's flowers are furthest off, the
        # baseline's first, then the peak's among all of them, so no side is
        # left bare (her "looks good but theres a bald patch on the back"):
        # handed out in turn, a whole side could miss the baseline. Without
        # `clump`, each next group of twos and threes the same way, from the
        # places `bloom_spots` finds (the hibiscus, her "theres a patch on the
        # hibiscus thats missing flowers": the first groups that took left a
        # quarter of it bare outside its peak).
        import numpy as np
        if bloom_spec.get("clump"):
            cands, place = envelope_spots(10 ** 9, farthest=False), clump_at
        else:
            cands = bloom_spots(skin, surface, base_spec, dict(bloom_spec, count=bloom_spec["count"] * 30), keep_off, span,
                                avoid)

            def place(pos, n, season):
                return around(pos, n, super_at, mega, bloom_spec.get("mega_gap", 6.5), season)
        # Far off mostly round the bush, less up and down (`spread_round`,
        # the hibiscus's): measured on the body, a group low on a side that
        # already had flowers counted as filling a gap, and the side opposite
        # went bare instead.
        squash = bloom_spec.get("spread_round")

        def key(p_):
            if not squash:
                return tuple(p_)
            a_ = math.atan2(p_.y, p_.x)
            return (math.cos(a_) * base_spec["width"] / 2, math.sin(a_) * base_spec["width"] / 2, p_.z * squash)
        where = np.array([key(c[0]) for c in cands]) if cands else np.zeros((0, 3))
        for season, want in (("blooms", bloom_spec["count"]), ("blooms_peak", bloom_spec["count"] * 2)):
            open_ = np.ones(len(cands), dtype=bool)
            pts = sets["blooms"][0] + (sets["blooms_peak"][0] if season == "blooms_peak" else [])
            near = np.full(len(cands), np.inf)
            for p_ in pts:
                near = np.minimum(near, np.linalg.norm(where - np.array(key(p_)), axis=1))
            while made_by[season] < want and open_.any():
                i = int(np.argmax(np.where(open_, near, -1.0)))
                open_ &= np.linalg.norm(where - where[i], axis=1) > bloom_spec["radius"]  # not this place again
                before = len(sets[season][0])
                got = place(cands[i][0], cands[i][1], season)
                made_by[season] += got
                for p_ in sets[season][0][before:]:
                    near = np.minimum(near, np.linalg.norm(where - np.array(key(p_)), axis=1))
        spots = []
    for pos, n in spots:
        if done >= bloom_spec["count"] * 3:
            break
        season = "blooms" if done < bloom_spec["count"] else "blooms_peak"
        if bloom_spec.get("spread_seasons"):
            # Every third clump that takes to the baseline, the rest to the
            # peak, so the baseline is spread as the peak is, not the first
            # that took, most on the hat (her "the clusters on the spherical
            # tree are still bound by the tier and they shouldnt be").
            base_turn = len(clumps) % 3 == 0 or made_by["blooms_peak"] >= bloom_spec["count"] * 2
            season = "blooms" if made_by["blooms"] < bloom_spec["count"] and base_turn else "blooms_peak"
            if made_by["blooms"] >= bloom_spec["count"] and made_by["blooms_peak"] >= bloom_spec["count"] * 2:
                break
        if bloom_spec.get("clump"):
            # Apart from the season's other clumps; the peak's may fill in
            # over the baseline's, as a bush in full bloom does.
            if any((pos - c).length < bloom_spec["radius"] * bloom_spec.get("super_gap", 3.2) * 1.2
                   for c, when in clumps if when == season):
                continue
            made = clump_at(pos, n, season)
            done += made
            made_by[season] += made
            if made:
                clumps.append((pos, season))
        else:
            done += around(pos, n, super_at, mega, bloom_spec.get("mega_gap", 6.5), season)
    # The buds, once every flower is placed, so none is put through one (her
    # "buds shouldnt collide through the center of a hibiscus flower").
    centre = Vector((0.0, 0.0, base_spec.get("lift", 0.0) + base_spec["height"] / 2))  # the body's middle

    def bud_cluster(season, pos, n, side, up, placed):
        """One cluster of buds against one of a group's placed flowers, on
        its side away from the group's middle (her "i still see some stray
        green buds on the azalea": set round the group, one could land where
        no flower was): its buds (group, place, turn, size, green), or None
        where its first bud would miss the bush or pass through a flower."""
        offset, flower_size = bud_rng.choice(placed)
        if bud_spec.get("uphill"):
            # Up the bush from its flower, leaning up over the leaves: the
            # hibiscus's flowers ring its hat's edge, and a bud leaning away
            # from one there would stand out past it into the air.
            a = math.pi / 2 + bud_rng.uniform(-0.7, 0.7)
            d = side * math.cos(a) + up * math.sin(a)
        elif offset.length > 1e-6:
            d = offset.normalized()
        else:
            a = bud_rng.uniform(0, math.tau)
            d = side * math.cos(a) + up * math.sin(a)
        # `near` of the way out to that flower's rim (the azaleas' tucked in
        # at their trusses, her "buds on azaleas need to be closer to the
        # clusters").
        reach = offset.length + bloom_spec["radius"] * flower_size * bud_rng.uniform(*bud_spec.get("near", (1.0, 1.2)))
        foot = pos + d * (reach + bud_spec["width"] * 0.5)
        grow = bud_rng.uniform(0.85, 1.15)
        twist = bud_rng.uniform(0, math.tau)
        hit, face, _, _ = surface.ray_cast(foot + n * 1.5, -n, 3.0)
        if hit is None or (hit - foot).dot(n) < -0.1:
            return None
        out = face if face.dot(n) > 0 else -face
        # A cluster of `cluster` buds (her "buds should be clustered too"),
        # side by side, splayed a little apart; at most one of them still
        # green (her "no more than one green bud per group").
        many = bud_rng.randint(*bud_spec.get("cluster", (1, 1)))
        green_left = 1 if bud_green else 0
        got = []
        for m in range(many):
            b = twist + m / many * math.tau
            e = side * math.cos(b) + up * math.sin(b)
            near = hit + (e * bud_spec["width"] * 0.7 if many > 1 else Vector())
            seat = surface.ray_cast(near + n * 1.5, -n, 3.0)[0]
            ok = not (seat is None or (seat - near).dot(n) < -0.1 or on_topper(seat)
                      or (off_body is not None and off_body(seat) > bloom_spec["hug"]))
            ok = ok and supported(seat, out, LEAF_TIP)  # not over a dome's rim
            if ok:
                # Leaning away from its flower along the bush, so it sits
                # beside the flower, not across it, low over the leaves so its
                # tip does not stand off them past the bush's outline.
                axis = (out.lerp(Vector((0, 0, 1)), 0.3) * 0.35 + d * 0.9 + (e * 0.3 if many > 1 else Vector())).normalized()
                rot = axis.to_track_quat("Z", "Y") @ Matrix.Rotation(twist + m, 3, "Z").to_quaternion()
                size = grow * (1.0 if m == 0 else bud_rng.uniform(0.75, 0.95))
                at = seat - axis * bud_spec["length"] * size * 0.2
                at.z = max(at.z, 0.01 - min((rot @ v.co).z for v in bud.data.vertices) * size)  # above the soil
                along = [at + axis * bud_spec["length"] * size * k / 4 for k in range(5)]
                ok = not any((q - c).length < r * 0.6 for c, r in discs for q in along)  # not through a flower's middle
                ok = ok and not any((q - lf).length < bud_spec["width"] * size * 0.6 + LEAF_CLEAR
                                    for lf in leaves for q in along)  # nor on a leaf cluster
                # Its tip close over the leaves, not out in the air where the
                # bush curves away under it (her "now there are floating buds
                # on the hibiscus").
                tip = along[-1]
                stand = (tip - surface.find_nearest(tip)[0]).dot((tip - centre).normalized())
                ok = ok and stand < bud_spec.get("stand", 0.3) * bud_spec["length"] * size
            if not ok:
                if m == 0:
                    return None
                continue  # off the bush's edge, under a brim, on a flare or the topper, or through a flower
            # Some still light green, their colour not showing yet (her
            # "include some light green buds that dont show their color yet").
            green = m > 0 and green_left and bud_rng.random() < bud_spec.get("green", 0.0)  # never one alone
            green_left -= 1 if green else 0
            got.append((season, at, rot.to_euler(), size, green))
        return got

    for job in bud_jobs:
        for _ in range(bud_rng.randint(*bud_spec["count"])):
            for _try in range(8):  # round the group until a clear place is found
                got = bud_cluster(*job)
                if got:
                    break
            for group, at, turn, size, green in got or []:
                into = green_sets[group] if green else bud_sets[group]
                into[0].append(at)
                into[1].append(turn)
                into[2].append(size)
    bng = blooms_on_points_group()
    counts = {}
    placings = [(group, group, flower, got) for group, got in sets.items()]
    if bud_spec:
        placings += [(group.replace("blooms", "buds"), group, bud, got) for group, got in bud_sets.items()]
    if bud_spec and bud_green:
        placings += [(group.replace("blooms", "buds_green"), group, bud_green, got) for group, got in green_sets.items()]
    for name, group, card, (points, turns, sizes) in placings:
        pm = bpy.data.meshes.new(name + suffix)
        pm.from_pydata([tuple(p) for p in points], [], [])
        pm.attributes.new("kyt_turn", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for e in turns for c in e])
        pm.attributes.new("kyt_size", "FLOAT", "POINT").data.foreach_set("value", sizes)
        if card is flower:
            pm.attributes.new("kyt_shade", "FLOAT", "POINT").data.foreach_set("value", shade_sets[group])
        pm.materials.append(bloom_mat)  # a slot, as the Purple Heart's leaf points carry; the card's own material shows
        placed_obj = bpy.data.objects.new(name + suffix, pm)
        placed_obj["kyt_collision"] = "none"
        placed_obj["kyt_merge_group"] = f"{tag}_{group}"
        blooms.objects.link(placed_obj)
        bmod = placed_obj.modifiers.new(bng.name, "NODES")
        bmod.node_group = bng
        plant_blades._set(bmod, bng, {"Bloom": card})
        if card is flower:
            # A shade's copy is a `1 / (slots x shades)` of the canvas along
            # from the last (`unwrap_blades.py` keeps the card that narrow).
            plant_blades._set(bmod, bng, {"Shade step": 1.0 / (bloom_spec["slots"] * shades)})
        counts[name] = len(points)
    return counts


def place_sprigs(bush, home, base_spec, strays, sprig, leaf_mat, tag, suffix, keep_off=0.0, avoid=()):
    """The stray leaf groupings for one size of bush: `count` sprigs spread
    over the leaves as built, `band` degrees round from the top, each
    standing out of the greenery as it faces, tipped a little up, its foot
    tucked in among the leaves, turned any way round and sized 1 +- 0.15. In
    the bush's own merge group: they are leaves, there all year. Move a point
    in edit mode to move a sprig. None within reach of a point of `avoid`
    ((place, reach) each). Their count."""
    bpy.context.view_layer.update()
    skin = bush.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    surface = BVHTree.FromPolygons([v.co.copy() for v in skin.vertices], [tuple(p.vertices) for p in skin.polygons])
    rng = random.Random(strays["seed"] + 7)
    points, turns, sizes, leaves = [], [], [], []

    def sprig_at(pos, n):
        """The sprig at `pos`, facing `n`: (place, turn, size), or None if a
        leaf would hang off into the air."""
        # Down the bush as its leaves hang, lifted `lift` degrees out of it,
        # swung a little either way; only where the bush is steep (`band`
        # from 55 degrees), for lifted out of a gentler slope a sprig stands
        # level, sticking out like a wing (her "like plane wings").
        side = Vector((0, 0, 1)).cross(n)
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        down = side.cross(n).normalized()  # down the surface
        down = Matrix.Rotation(rng.uniform(-0.5, 0.5), 3, n) @ down
        lift = math.radians(strays["lift"])
        along = (down * math.cos(lift) + n * math.sin(lift)).normalized()
        face = along.cross(n.cross(along)).normalized()  # the fan's face, out of the bush
        rot = Matrix((face.cross(along), face, along)).transposed().to_quaternion()  # x, y, z of the card
        grow = rng.uniform(0.85, 1.15)
        # Laid down flat on the leaves, pressed a little into them, tipped a
        # little into the bush so they follow its curve (her "just ...lay down
        # the small, brand new leaf clusters that stick out", "still too
        # proud"), not so far they sink under its leaves (her "the smaller leaf
        # clusters are missing"); `lift` -3 degrees (her "flare them by like 2
        # degrees more", from -5).
        at = pos - along * strays["length"] * 0.2 - n * 0.005
        # Low on a ball, a sprig hanging down may reach the soil: raise it
        # just clear (Check places a prop by z = 0).
        at.z = max(at.z, 0.01 - min((rot @ v.co).z for v in sprig.data.vertices) * grow)
        # On the leaves, not under them (her "the smaller leaf clusters are
        # missing", when tipped into the bush they sank under its outer
        # leaves): raised just so far that each leaf's middle clears the
        # leaves under it.
        middle = Vector((0.0, 0.0, base_spec.get("lift", 0.0) + base_spec["height"] / 2))

        def stand(q):
            """How far `q` stands out of (+) or under (-) the leaves, along
            the line out from the body's middle."""
            d = (q - middle).normalized()
            hit = surface.ray_cast(q + d * 0.5, -d, 1.0)[0]
            return (q - hit).dot(d) if hit is not None else 1.0

        verts = [(rot @ v.co) * grow for v in sprig.data.vertices]
        halves = [(verts[k] + (verts[k + 2] + verts[k + 3]) / 2) / 2 for k in range(0, len(verts), 4)]
        at += n * max(0.0, 0.006 - min(stand(at + h) for h in halves))
        # None hanging off an edge into the air (her "i see floating leaves
        # on the hibiscus"): every leaf's tip ends on the leaves.
        if any(stand(at + (verts[k + 2] + verts[k + 3]) / 2) > 0.05 for k in range(0, len(verts), 4)):
            return None
        # Points along each leaf, foot to tip and its tip's corners, for
        # flowers to keep off (`clear_leaves`).
        along = [at + verts[k].lerp((verts[k + 2] + verts[k + 3]) / 2, t / 5) for k in range(0, len(verts), 4)
                 for t in range(6)]
        along += [at + verts[k + c] for k in range(0, len(verts), 4) for c in (2, 3)]
        return at, rot.to_euler("XYZ"), grow, along

    if strays.get("spread_out"):
        # Each next where the sprigs are furthest off (the hibiscus's: taken
        # in turn, those left out let three bunch on one side, and the
        # flowers, kept clear of them, left that side bare: her "theres a
        # patch on the hibiscus thats missing flowers").
        cands = bloom_spots(skin, surface, base_spec, dict(strays, count=strays["count"] * 15), keep_off, avoid=avoid)
        open_ = [True] * len(cands)
        while len(points) < strays["count"] and any(open_):
            i = max((k for k in range(len(cands)) if open_[k]),
                    key=lambda k: min(((cands[k][0] - q).length for q in points), default=-k))
            open_[i] = False
            got = sprig_at(*cands[i])
            if got:
                for into, value in zip((points, turns, sizes, leaves), got):
                    into.append(value)
    else:
        # Three times as many places as it needs, in turn, so one left out
        # is made up by the next.
        for pos, n in bloom_spots(skin, surface, base_spec, dict(strays, count=strays["count"] * 3), keep_off, avoid=avoid):
            if len(points) == strays["count"]:
                break
            got = sprig_at(pos, n)
            if got:
                for into, value in zip((points, turns, sizes, leaves), got):
                    into.append(value)
    pm = bpy.data.meshes.new(f"sprigs{suffix}")
    pm.from_pydata([tuple(p) for p in points], [], [])
    pm.attributes.new("kyt_turn", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for e in turns for c in e])
    pm.attributes.new("kyt_size", "FLOAT", "POINT").data.foreach_set("value", sizes)
    pm.materials.append(leaf_mat)
    obj = bpy.data.objects.new(f"sprigs{suffix}", pm)
    obj["kyt_collision"] = "none"
    obj["kyt_merge_group"] = tag
    coll = bpy.data.collections.new(f"sprigs{suffix}")
    home.children.link(coll)
    coll.objects.link(obj)
    ng = blooms_on_points_group()
    mod = obj.modifiers.new(ng.name, "NODES")
    mod.node_group = ng
    plant_blades._set(mod, ng, {"Bloom": sprig})
    return [(p, strays["length"], along) for p, along in zip(points, leaves)]


# --- A tree of clumps (the coast live oak) ----------------------------------------

def lathe(name, profile, material, around=8):
    """A closed body of revolution, `profile` (radius, height) from its bottom
    pole to its top, `around` round, shaded smooth."""
    bm = bmesh.new()
    bottom = bm.verts.new((0.0, 0.0, profile[0][1]))
    top = bm.verts.new((0.0, 0.0, profile[-1][1]))
    rings = [[bm.verts.new((r * math.cos(k / around * math.tau), r * math.sin(k / around * math.tau), z))
              for k in range(around)] for r, z in profile[1:-1]]
    for k in range(around):
        bm.faces.new((rings[0][(k + 1) % around], rings[0][k], bottom))
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % around], top))
    for lo, hi in zip(rings, rings[1:]):
        for k in range(around):
            bm.faces.new((lo[k], lo[(k + 1) % around], hi[(k + 1) % around], hi[k]))
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    return me


def clump_skin_group():
    """A sphere shrub's unit, its Body (the ball), its Hat (lifted Hat lift up
    the ball's axis and turned Hat turn round it), an Upper hat over it
    (Upper lift, Upper scale, Upper turn) and its Topper (lifted Topper lift
    onto the top hat), on every
    point of Clumps, turned by `kyt_turn` (Euler) and sized by `kyt_size`,
    its brim spread by `kyt_flare` (`clump_points`); each clump's normals
    leaning Roundness of the way out from Centre, so the
    crown shades as one mound of clumps; the crown's own mesh (its core) kept
    under them when Show core."""
    ng, io = plant_blades._node_group("kyt_clump_skin", (
        ("Body", "NodeSocketObject", None), ("Hat", "NodeSocketObject", None), ("Topper", "NodeSocketObject", None),
        ("Clumps", "NodeSocketObject", None), ("Hat lift", "NodeSocketFloat", 0.0), ("Hat turn", "NodeSocketFloat", 0.0),
        ("Roundness", "NodeSocketFloat", 0.25), ("Centre", "NodeSocketVector", (0.0, 0.0, 0.0)),
        ("Show core", "NodeSocketBool", True), ("Upper hat", "NodeSocketObject", None),
        ("Upper lift", "NodeSocketFloat", 0.0), ("Upper scale", "NodeSocketFloat", 1.0),
        ("Upper turn", "NodeSocketFloat", 0.0), ("Topper lift", "NodeSocketFloat", 0.0)))
    if io is None:
        return ng
    gin, gout = io
    N = ng.nodes.new

    def instance(socket):
        info = N("GeometryNodeObjectInfo")
        info.transform_space = "ORIGINAL"
        info.inputs["As Instance"].default_value = True
        link(ng, gin, socket, info, "Object")
        return info

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

    body, hat, topper, upper = instance("Body"), instance("Hat"), instance("Topper"), instance("Upper hat")

    def up_axis_at(geometry, lift, turn=None, scale=None):
        """`geometry` on one point `lift` up the ball's axis, turned `turn`
        round it and sized `scale` (input names)."""
        one = N("GeometryNodePoints")
        one.inputs["Count"].default_value = 1
        up = N("ShaderNodeCombineXYZ")
        link(ng, gin, lift, up, "Z")
        link(ng, up, "Vector", one, "Position")
        on = N("GeometryNodeInstanceOnPoints")
        link(ng, one, "Points", on, "Points")
        link(ng, geometry, "Geometry", on, "Instance")
        if turn:
            spin = N("ShaderNodeCombineXYZ")
            link(ng, gin, turn, spin, "Z")
            spun = N("FunctionNodeEulerToRotation")
            link(ng, spin, "Vector", spun, "Euler")
            ng.links.new(spun.outputs["Rotation"], on.inputs["Rotation"])
        if scale:
            ng.links.new(gin.outputs[scale], on.inputs["Scale"])
        return on

    # The hat up the ball's axis, turned round it; an upper hat, if any,
    # smaller, over it (her "can we add another tier to each segment?",
    # "under the sprout"); the sprout lifted onto the top one.
    unit = N("GeometryNodeJoinGeometry")
    link(ng, body, "Geometry", unit, "Geometry")
    link(ng, up_axis_at(hat, "Hat lift", "Hat turn"), "Instances", unit, "Geometry")
    link(ng, up_axis_at(upper, "Upper lift", "Upper turn", "Upper scale"), "Instances", unit, "Geometry")
    link(ng, up_axis_at(topper, "Topper lift"), "Instances", unit, "Geometry")
    # The unit on every clump.
    spots = N("GeometryNodeObjectInfo")
    spots.transform_space = "ORIGINAL"
    link(ng, gin, "Clumps", spots, "Object")
    turn = N("FunctionNodeEulerToRotation")
    ng.links.new(named("kyt_turn", "FLOAT_VECTOR"), turn.inputs["Euler"])
    on = N("GeometryNodeInstanceOnPoints")
    link(ng, spots, "Geometry", on, "Points")
    link(ng, unit, "Geometry", on, "Instance")
    ng.links.new(turn.outputs["Rotation"], on.inputs["Rotation"])
    ng.links.new(named("kyt_size", "FLOAT_VECTOR"), on.inputs["Scale"])
    real = N("GeometryNodeRealizeInstances")
    link(ng, on, "Instances", real, "Geometry")
    # A hat with a `kyt_flare` spread wider toward its brim (the top hat, her
    # "flare the top most tier"): each point pushed out from the hat's axis by
    # that share of its distance from it, times the square of how far down
    # from the top to the brim it is, so the top keeps its shape and the brim
    # opens (the sprouts, lying at the top, all but unmoved).
    def op2(op, a, b, clamp=False):
        m = N("ShaderNodeMath")
        m.operation = op
        m.use_clamp = clamp
        ng.links.new(a, m.inputs[0])
        ng.links.new(b, m.inputs[1])
        return m.outputs["Value"]

    d = vec("SUBTRACT", N("GeometryNodeInputPosition").outputs["Position"], named("kyt_pivot", "FLOAT_VECTOR"))
    axis = named("kyt_axis", "FLOAT_VECTOR")
    dot = N("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    ng.links.new(d, dot.inputs[0])
    ng.links.new(axis, dot.inputs[1])
    up_axis = dot.outputs["Value"]
    radial = vec("SUBTRACT", d, vec("SCALE", axis, scale=up_axis))
    top_h, rim_h = named("kyt_top_h", "FLOAT"), named("kyt_rim_h", "FLOAT")
    down = op2("DIVIDE", op2("SUBTRACT", top_h, up_axis), op2("SUBTRACT", top_h, rim_h), clamp=True)
    push = op2("MULTIPLY", op2("MULTIPLY", down, down), named("kyt_flare", "FLOAT"))
    spread = N("GeometryNodeSetPosition")
    link(ng, real, "Geometry", spread, "Geometry")
    ng.links.new(vec("SCALE", radial, scale=push), spread.inputs["Offset"])
    # Shaded round the crown: each clump's own normal leaning Roundness of the
    # way out from the crown's middle.
    keep = N("ShaderNodeMath")
    keep.operation = "SUBTRACT"
    keep.inputs[0].default_value = 1.0
    link(ng, gin, "Roundness", keep, 1)
    out = vec("NORMALIZE", vec("SUBTRACT", N("GeometryNodeInputPosition").outputs["Position"], gin.outputs["Centre"]))
    mixed = vec("NORMALIZE", vec("ADD", vec("SCALE", N("GeometryNodeInputNormal").outputs["Normal"], scale=keep.outputs[0]),
                                 vec("SCALE", out, scale=gin.outputs["Roundness"])))
    setn = N("GeometryNodeSetMeshNormal")
    setn.mode, setn.domain = "FREE", "POINT"
    link(ng, spread, "Geometry", setn, "Mesh")
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


def clump_points(name, crown, apex_up, rim_up):
    """The clumps' places as a points object: `crown["tiers"]`, rings of
    hats, each by its top and its ball's radius, put off true by `jitter` and
    toward the photo's left by `droop` (`SPECIES["coastal_live_oak"]`). Each
    point is the unit's pivot, `apex_up` under its hat's top as the unit
    stands: turned `tilt` of the way from upright to facing out from the
    crown's `centre` and spun at random (`kyt_turn`), sized its radius over the
    unit's (`kyt_size`), with its tier's `flare` (`kyt_flare`) and what
    `kyt_clump_skin` flares it by: its place, its axis, and how far up that
    axis its brim (`rim_up`) and its top stand (`kyt_pivot`, `kyt_axis`,
    `kyt_rim_h`, `kyt_top_h`). Move a point in edit mode to move its hat
    (its `kyt_pivot` then comes from the next build). Also each hat: its top,
    axis, size and tier."""
    rng = random.Random(crown["seed"])
    centre = Vector(crown["centre"])
    jo, ju, ja, jr = crown["jitter"]
    tops = []
    for k, (count, out, up, radius, first) in enumerate(crown["tiers"]):
        for j in range(count):
            a = math.radians(first + j * 360.0 / count + rng.uniform(-ja, ja))
            far, z = out + rng.uniform(-jo, jo), up + rng.uniform(-ju, ju)
            if k >= len(crown["tiers"]) - 2 and count > 1:
                toward = max(0.0, -math.cos(a))  # the photo's left
                far, z = far + crown["droop"][0] * toward, z - crown["droop"][1] * toward
            tops.append((Vector((far * math.cos(a), far * math.sin(a), z)), radius + rng.uniform(-jr, jr) * (count > 1), k))
    points, turns, sizes, hats = [], [], [], []
    for top, r, tier in tops:
        out = (top - centre).normalized() if (top - centre).length > 1e-6 else Vector((0.0, 0.0, 1.0))
        axis = Vector((0.0, 0.0, 1.0)).lerp(out, crown["tilt"]).normalized()
        rot = axis.to_track_quat("Z", "Y") @ Matrix.Rotation(rng.uniform(0, math.tau), 3, "Z").to_quaternion()
        s = r / crown["ball"]
        points.append(top - rot @ Vector((0.0, 0.0, apex_up * s)))
        turns.append(rot.to_euler())
        sizes.append((s, s, s))
        hats.append(dict(top=top, axis=rot @ Vector((0.0, 0.0, 1.0)), size=s, tier=tier))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in points], [], [])
    me.attributes.new("kyt_turn", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for e in turns for c in e])
    me.attributes.new("kyt_size", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for s in sizes for c in s])
    me.attributes.new("kyt_pivot", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for p in points for c in p])
    me.attributes.new("kyt_axis", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for h in hats for c in h["axis"]])
    me.attributes.new("kyt_flare", "FLOAT", "POINT").data.foreach_set(
        "value", [crown.get("flare", {}).get(h["tier"], 0.0) for h in hats])
    me.attributes.new("kyt_rim_h", "FLOAT", "POINT").data.foreach_set("value", [rim_up * h["size"] for h in hats])
    me.attributes.new("kyt_top_h", "FLOAT", "POINT").data.foreach_set("value", [apex_up * h["size"] for h in hats])
    return bpy.data.objects.new(name, me), hats


def limb_mesh(name, paths, material, tile=None, knots=(), knot_material=None, grow=None):
    """Tapering tubes along `paths` (each (sides round, a list of (point,
    radius))), each ring square to the path and carried along it without
    twisting, each path ending in a point past its last ring. With `tile`
    ((width, height) metres of the bark's texture), unwrapped round and along
    each tube: a whole number of tiles round it (by its mean girth), metres
    along it; with `grow` ((radius, power)), a tube thicker than `radius`
    wears the tile larger by its mean radius over that to the `power`, so the
    grain is bigger on the big limbs and biggest on the trunk. `knots`
    (`knot_faces`) are added, their stubs in `knot_material`."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap") if tile else None

    def face(verts, uvs, index=0):
        f = bm.faces.new(verts)
        f.material_index = index
        if uv:
            for loop, co in zip(f.loops, uvs):
                loop[uv].uv = co
        return f

    for sides, path in paths:
        pts = [Vector(p) for p, _ in path]
        tangents = []
        for k in range(len(pts)):
            a, b = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]
            tangents.append((b - a).normalized())
        side = tangents[0].cross(Vector((0.0, 0.0, 1.0)))
        if side.length < 1e-3:
            side = tangents[0].cross(Vector((1.0, 0.0, 0.0)))
        side.normalize()
        rings = []
        for k, ((_, radius), t) in enumerate(zip(path, tangents)):
            if k:
                side = (tangents[k - 1].rotation_difference(t) @ side).normalized()
            other = t.cross(side).normalized()
            rings.append([bm.verts.new(pts[k] + (side * math.cos(j / sides * math.tau)
                                                 + other * math.sin(j / sides * math.tau)) * radius)
                          for j in range(sides)])
        # Round: a whole number of tiles by the tube's mean girth; along: metres;
        # the tile grown on a thick tube.
        mean_r = sum(r for _, r in path) / len(path)
        big = max(1.0, (mean_r / grow[0]) ** grow[1]) if grow else 1.0
        tw, th = (tile[0] * big, tile[1] * big) if tile else (1.0, 1.0)
        around = max(1, round(math.tau * mean_r / tw)) if tile else 1
        vs = [0.0]
        for a, b in zip(pts, pts[1:]):
            vs.append(vs[-1] + (b - a).length / th)
        us = [j / sides * around for j in range(sides + 1)]
        for k, (lo, hi) in enumerate(zip(rings, rings[1:])):
            for j in range(sides):
                face((lo[j], lo[(j + 1) % sides], hi[(j + 1) % sides], hi[j]),
                     [(us[j], vs[k]), (us[j + 1], vs[k]), (us[j + 1], vs[k + 1]), (us[j], vs[k + 1])])
        tip_at = pts[-1] + tangents[-1] * path[-1][1] * 1.5
        tip = bm.verts.new(tip_at)
        v_tip = vs[-1] + path[-1][1] * 1.5 / th
        for j in range(sides):
            face((rings[-1][j], rings[-1][(j + 1) % sides], tip),
                 [(us[j], vs[-1]), (us[j + 1], vs[-1]), ((us[j] + us[j + 1]) / 2, v_tip)])
    for knot in knots:
        knot_faces(bm, face, knot, tile)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    if knot_material is not None:
        me.materials.append(knot_material)
    return me


def knot_spots(paths, knots):
    """Where the knots go (`knots`: `count` of them, `radius` range, `on`
    the paths they may sit on, `along` the share of the way up, `seed`): each
    on one of those limbs, its own, facing out at a bearing chosen at random
    but never down; (point on the surface, facing, the limb's way, the knot's
    radius, how far the limb's curve falls from its middle to its rim)."""
    rng = random.Random(knots["seed"])
    chosen = rng.sample(range(min(knots["on"], len(paths))), min(knots["count"], knots["on"], len(paths)))
    out = []
    for i in chosen:
        path = paths[i][1]
        pts, radii = [Vector(p) for p, _ in path], [r for _, r in path]
        lengths = [(b - a).length for a, b in zip(pts, pts[1:])]
        want = rng.uniform(*knots["along"]) * sum(lengths)
        for a, b, ra, rb, l in zip(pts, pts[1:], radii, radii[1:], lengths):
            if want <= l:
                f = want / max(l, 1e-9)
                at, way, r = a.lerp(b, f), (b - a).normalized(), ra + (rb - ra) * f
                break
            want -= l
        across = way.cross(Vector((0.0, 0.0, 1.0)))
        across = across.normalized() if across.length > 1e-3 else Vector((1.0, 0.0, 0.0))
        face = Matrix.Rotation(rng.uniform(0, math.tau), 3, way) @ across
        if face.z < -0.2:
            face = -face
        size = min(rng.uniform(*knots["radius"]), 0.55 * r)
        sag = r - math.sqrt(max(r * r - size * size, 0.0))
        out.append((at + face * r, face, way, size, sag))
    return out


def knot_faces(bm, face, knot, tile):
    """A knot where a branch broke away long ago (her "add a few large knots
    where a branch might have detached a long time ago"): an oval of bark 1.25
    times as long as wide along the limb, its rim down on the limb's curve, a
    raised lip `radius` 0.72 out standing 0.3 of the radius proud, rolling in
    to the stub of the old branch (her "the holes should have a knot inside
    kind of like this", four photographs of knots and cut branches): its end
    grain (material 1, `paint_canvas.py --bark`'s knot disc, a dark crack at
    its rim) a little domed, just proud of the bark (the limb runs on under
    it). Eight round, 56 triangles; the bark's faces take the grain across
    them."""
    at, n, way, size, sag = knot
    e1 = (way - n * way.dot(n)).normalized()
    e2 = n.cross(e1).normalized()
    rings = [(1.0, -sag), (0.72, 0.3 * size), (0.52, 0.2 * size), (0.4, 0.1 * size)]
    around = 8
    made = []
    for share, up in rings:
        ring = []
        for j in range(around):
            a = j / around * math.tau
            x, y = math.cos(a) * share * size, math.sin(a) * share * size * 1.25
            ring.append((bm.verts.new(at + e2 * x + e1 * y + n * up), (x, y)))
        made.append(ring)
    # The stub's face stands just proud of the bark (the limb's own surface
    # runs on unbroken under the knot, and hides anything sunk into it), a
    # little domed.
    centre = bm.verts.new(at + n * 0.14 * size)

    def uv(xy):
        return (xy[0] / (tile[0] if tile else 1.0), xy[1] / (tile[1] if tile else 1.0))

    def disc(xy):
        """The end grain's texture: its disc's rim at the lip's inner edge."""
        return (0.5 + 0.5 * xy[0] / (0.52 * size), 0.5 + 0.5 * xy[1] / (0.52 * size * 1.25))
    # The rings run clockwise seen from outside, so each face is wound from
    # the inner ring to face out (the bark is one-sided). The band inside the
    # lip and the face are the stub (material 1), on the end grain's disc.
    for k, (lo, hi) in enumerate(zip(made, made[1:])):
        stub = k == 2
        m = disc if stub else uv
        for j in range(around):
            j1 = (j + 1) % around
            face((hi[j][0], hi[j1][0], lo[j1][0], lo[j][0]),
                 [m(hi[j][1]), m(hi[j1][1]), m(lo[j1][1]), m(lo[j][1])], 1 if stub else 0)
    for j in range(around):
        j1 = (j + 1) % around
        face((centre, made[-1][j1][0], made[-1][j][0]), [(0.5, 0.5), disc(made[-1][j1][1]), disc(made[-1][j][1])], 1)


def hat_branches(hats, limbs, hold):
    """The branches holding the hats (her "the tree greenery just floats with
    no branches ... we however can do better"): each ends `hold` metres (at
    the unit's size) in under its hat's top, having turned up into it along
    the hat's axis, an umbrella's shaft. The leader rises from the fork to the
    top hat, and each hat of the tiers between branches off it; a few major
    limbs spread from the fork and fork again into a scaffold limb to each hat
    of the lowest tier; each hat of the tier above that branches off the
    scaffold limb nearest it round the tree.
    Each (sides, path of (point, radius))."""
    fork, _ = limbs["trunk"][-1]
    fork = Vector(fork)
    last = max(h["tier"] for h in hats)

    def end_of(h):
        return h["top"] - h["axis"] * hold * h["size"]

    def path(start, h, radii, sides):
        """From `start` out to hat `h`: a knee `bend` below the straight line
        a little past halfway, then up its axis into it."""
        end = end_of(h)
        shaft = end - h["axis"] * min(1.0, 0.25 * (end - start).length)
        knee = start.lerp(shaft, 0.55) - Vector((0.0, 0.0, limbs["bend"] * (shaft - start).length))
        r0, r1 = radii
        pts = [start, knee, shaft, end]
        return sides, [(p, r0 + (r1 - r0) * k / 3) for k, p in enumerate(pts)]

    def bearing(v):
        return math.atan2(v.y, v.x)

    def along(p, t):
        """The point `t` of the way along a branch's path."""
        pts = [q for q, _ in p[1]]
        lengths = [(b - a).length for a, b in zip(pts, pts[1:])]
        want = t * sum(lengths)
        for a, b, l in zip(pts, pts[1:], lengths):
            if want <= l:
                return a.lerp(b, want / max(l, 1e-9))
            want -= l
        return pts[-1]

    paths = []
    top = next(h for h in hats if h["tier"] == 0)
    leader = path(fork, top, limbs["leader"], limbs["sides"])
    paths.append(leader)
    # The lowest tier's hats, round the tree, shared out among `majors` major
    # limbs (an oak's few big limbs, not one each from the fork), each forking
    # `split` of the way out into a scaffold limb to each of its hats.
    lowest = sorted((h for h in hats if h["tier"] == last), key=lambda h: bearing(h["top"]))
    per = len(lowest) / limbs["majors"]
    scaffolds = []
    for g in range(limbs["majors"]):
        group = lowest[round(g * per):round((g + 1) * per)]
        mean = sum((end_of(h) for h in group), Vector()) / len(group)
        out = Vector((mean.x, mean.y, 0.0)).normalized()
        start = fork + out * 0.25 - Vector((0.0, 0.0, 0.25))
        split = start.lerp(mean, limbs["split"])
        knee = start.lerp(split, 0.5) - Vector((0.0, 0.0, limbs["bend"] * (split - start).length))
        r0, r1 = limbs["major"]
        paths.append((limbs["sides"], [(start, r0), (knee, (r0 + r1) / 2), (split, r1)]))
        for h in group:
            scaffolds.append((bearing(h["top"]), path(split, h, limbs["scaffold"], limbs["sides"])))
    paths += [p for _, p in scaffolds]
    for h in hats:
        if h["tier"] in (0, last):
            continue
        if h["tier"] == last - 1:
            b = bearing(h["top"])
            _, near = min(scaffolds, key=lambda c: abs(math.remainder(c[0] - b, math.tau)))
            start = along(near, 0.35)
        else:
            start = along(leader, 0.45)
        paths.append(path(start, h, limbs["branch"], limbs["twig_sides"]))
    return paths


def place_acorns(crown_obj, home, acorns, brown, green, sprouts, bud=None):
    """The acorns (`acorns`): hanging from the hats' brims as built, the open
    edges of the crown's cards, each brim point kept where nothing of the
    crown lies outside it and not by a sprout (`sprouts`, (place, reach));
    `count` clusters spread farthest first, each of `cluster` acorns side by
    side along the brim, point down leaning `lean` out, foot tucked just under
    the leaves' tips, none into a hat below nor its point under `low`. The
    same places twice in `export/acorns`: `acorns_summer` wearing `green`
    (merge group `summer_acorns`) and `acorns_fall` wearing `brown`
    (`fall_acorns`), each point its card by `kyt_blooms_on_points` (move a
    point to move an acorn); `winter` of them brown in `winter_acorns`; with
    `bud`, spring's `buds` at those places and more, up and out
    (`spring_buds`). Their counts."""
    bpy.context.view_layer.update()
    ev = crown_obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    surface = BVHTree.FromPolygons([v.co.copy() for v in ev.vertices], [tuple(p.vertices) for p in ev.polygons])
    bm = bmesh.new()
    bm.from_mesh(ev)
    rng = random.Random(acorns["seed"])
    length = acorns["length"]
    cands = []
    for e in bm.edges:
        if not e.is_boundary:
            continue
        a, b = e.verts[0].co.copy(), e.verts[1].co.copy()
        m = (a + b) / 2
        out = Vector((m.x, m.y, 0.0))
        if out.length < 0.5 or any((m - q).length < reach for q, reach in sprouts):
            continue
        out.normalize()
        if surface.ray_cast(m + out * 0.3, (out - Vector((0.0, 0.0, 0.2))).normalized(), 30.0)[0] is not None:
            continue  # something of the crown outside it: not on the outside
        down = (Vector((0.0, 0.0, -1.0)) + out * acorns["lean"]).normalized()
        foot = m - Vector((0.0, 0.0, 0.06))
        if foot.z + down.z * length < acorns["low"]:
            continue
        if surface.ray_cast(foot + down * 0.02, down, length * 1.1)[0] is not None:
            continue  # it would hang into a hat below
        cands.append((foot, down, (b - a).normalized()))
    bm.free()
    if not cands:
        return 0
    # Farthest first: the acorns' clusters are the first `count`, spring's
    # buds' the first `buds` `count`, the same places and more.
    buds = acorns.get("buds") if bud is not None else None
    want = max(acorns["count"], buds["count"] if buds else 0)
    taken = [max(cands, key=lambda c: c[0].z)]
    while len(taken) < min(want, len(cands)):
        taken.append(max(cands, key=lambda c: min((c[0] - t[0]).length for t in taken)))
    points, turns, sizes = [], [], []
    for foot, down, along in taken[:acorns["count"]]:
        many = rng.randint(*acorns["cluster"])
        for k in range(many):
            points.append(foot + along * (k - (many - 1) / 2) * acorns["width"] * 1.1)
            axis = (down + along * rng.uniform(-0.15, 0.15)).normalized()
            rot = axis.to_track_quat("Z", "Y") @ Matrix.Rotation(rng.uniform(0, math.tau), 3, "Z").to_quaternion()
            turns.append(rot.to_euler())
            sizes.append(rng.uniform(0.9, 1.1))
    coll = bpy.data.collections.new("acorns")
    home.children.link(coll)
    for name, card, group in (("acorns_summer", green, "summer_acorns"), ("acorns_fall", brown, "fall_acorns")):
        on_points(name, card, group, coll, points, turns, sizes)
    counts = dict(hanging=len(points))
    if acorns.get("winter"):
        # Winter's few: brown, where some of the acorns hang, their own random.
        keep = random.Random(acorns["seed"] + 1).sample(range(len(points)), min(acorns["winter"], len(points)))
        on_points("acorns_winter", brown, "winter_acorns", coll, [points[i] for i in keep], [turns[i] for i in keep],
                  [sizes[i] for i in keep])
        counts["winter"] = len(keep)
    if buds:
        # Spring's buds, their own random, so the acorns are as they were:
        # round each brim place, each bud dropped onto the leaves at its own
        # spot, up to `scatter` metres along the brim and up onto the hat, and
        # standing out of the leaves there, up and out (her "the buds on spring
        # are kind of in a line": side by side on the rim's very edge, a
        # cluster was a row and the clusters a ring).
        brng = random.Random(buds["seed"])
        pts, trs, szs = [], [], []
        reach = buds.get("scatter", 0.5)
        for foot, down, along in taken[:buds["count"]]:
            out = Vector((down.x, down.y, 0.0))
            out = out.normalized() if out.length > 1e-6 else Vector((1.0, 0.0, 0.0))
            edge = foot + Vector((0.0, 0.0, 0.06))
            for k in range(brng.randint(*buds["cluster"])):
                spot = edge + along * brng.uniform(-reach, reach) * 0.7 - out * brng.uniform(0.05, reach)
                hit, face, _, _ = surface.ray_cast(spot + Vector((0.0, 0.0, 1.5)), Vector((0.0, 0.0, -1.0)), 3.0)
                if hit is None or abs(hit.z - edge.z) > 1.0:
                    continue  # off the hat, or onto one far below
                face = face if face.z > 0 else -face
                axis = (face + Vector((0.0, 0.0, 0.8)) + out * 0.4
                        + Vector((brng.uniform(-0.2, 0.2), brng.uniform(-0.2, 0.2), 0.0))).normalized()
                rot = axis.to_track_quat("Z", "Y") @ Matrix.Rotation(brng.uniform(0, math.tau), 3, "Z").to_quaternion()
                pts.append(hit - axis * buds["bud"][0] * 0.15)
                trs.append(rot.to_euler())
                szs.append(brng.uniform(0.9, 1.1))
        on_points("buds_spring", bud, "spring_buds", coll, pts, trs, szs)
        counts["buds"] = len(pts)
    return counts


def on_points(name, card, group, coll, points, turns, sizes):
    """A points object `name` in `coll`, each point wearing `card` turned by
    `kyt_turn` and sized by `kyt_size` (`kyt_blooms_on_points`), in merge
    group `group`, not colliding. Move a point to move its card."""
    ng = blooms_on_points_group()
    pm = bpy.data.meshes.new(name)
    pm.from_pydata([tuple(p) for p in points], [], [])
    pm.attributes.new("kyt_turn", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", [c for e in turns for c in e])
    pm.attributes.new("kyt_size", "FLOAT", "POINT").data.foreach_set("value", sizes)
    pm.materials.append(card.data.materials[0])
    obj = bpy.data.objects.new(name, pm)
    obj["kyt_collision"] = "none"
    obj["kyt_merge_group"] = group
    coll.objects.link(obj)
    mod = obj.modifiers.new(ng.name, "NODES")
    mod.node_group = ng
    plant_blades._set(mod, ng, {"Bloom": card})
    return obj


def fallen_leaf_card(name, length, material):
    """A single leaf lying flat (fall's leaves on the ground): a card
    `length` long and 0.7 of that across, its middle at the origin, its foot
    toward -y; the leaf painted up it (`paint_canvas.py`, `cut_topper`). Two
    triangles."""
    half = length * 0.35
    verts = [(-half, -length / 2, 0.0), (half, -length / 2, 0.0), (half, length / 2, 0.0), (-half, length / 2, 0.0)]
    return card_mesh(name, verts, [(0, 1, 2), (0, 2, 3)], material, [(x, y + length / 2) for x, y, _ in verts])


def place_ground(home, ground, radius, acorn, leaves, acorn_spec):
    """Fall's litter under the tree (`ground`): `acorns` acorns lying on their
    sides and `leaves` leaves flat on the soil, each on one of the `leaves`
    cards, scattered evenly by area between `from_trunk` metres off the trunk
    and `reach` of the crown's `radius`, turned any way. In merge group
    `fall_ground`. Their counts."""
    rng = random.Random(ground["seed"])
    inner, outer = ground["from_trunk"], ground["reach"] * radius

    def spot():
        r = math.sqrt(rng.uniform(inner ** 2, outer ** 2))
        a = rng.uniform(0, math.tau)
        return Vector((r * math.cos(a), r * math.sin(a), 0.0))

    coll = bpy.data.collections.new("fall_ground")
    home.children.link(coll)
    # Acorns on their sides: the spindle's axis level, its middle just above
    # the soil (sunk a little into it).
    pts, turns, sizes = [], [], []
    for _ in range(ground["acorns"]):
        at = spot()
        size = rng.uniform(0.9, 1.1)
        rot = (Matrix.Rotation(rng.uniform(0, math.tau), 3, "Z") @ Matrix.Rotation(math.radians(90 + rng.uniform(-8, 8)), 3, "X"))
        pts.append(at + Vector((0.0, 0.0, acorn_spec["width"] * 0.4 * size)))
        turns.append(rot.to_euler())
        sizes.append(size)
    on_points("fallen_acorns", acorn, "fall_ground", coll, pts, turns, sizes)
    # Leaves flat, a centimetre up, tipped a few degrees.
    for k, card in enumerate(leaves):
        pts, turns, sizes = [], [], []
        for _ in range(ground["leaves"] // len(leaves) + (k < ground["leaves"] % len(leaves))):
            pts.append(spot() + Vector((0.0, 0.0, 0.01)))
            turns.append((math.radians(rng.uniform(-4, 4)), math.radians(rng.uniform(-4, 4)), rng.uniform(0, math.tau)))
            sizes.append(rng.uniform(0.85, 1.1))
        on_points(f"fallen_leaves_{'abc'[k]}", card, "fall_ground", coll, pts, turns, sizes)
    return ground["acorns"], ground["leaves"]


def build_crown(name, spec, export, layout, card, body, topper, dome, core_mat, stem, sprig=None, leaf_mat=None):
    """A tree whose crown is clumps of a sphere shrub's unit (`crown`), its hat
    and topper and, unless `hats_only`, its ball, over a trunk and limbs
    (`limbs`): `export/crown`, the core, wearing the clumps through its
    `kyt_clump_skin` modifier; `authored/domes/clumps`, their places;
    `export/trunk/trunk`, the bark, which collides; with `strays`,
    `export/sprigs/sprigs`, the stray leaf clusters over the hats as built;
    with `acorns`, the season's acorns and fall's litter (`place_acorns`,
    `place_ground`), each season's its own merge group: spring's buds,
    summer's and fall's acorns, fall's ground, winter's acorns; the foliage
    the same all year, each season's colours its canvas. One size."""
    crown = spec["crown"]
    obj = bpy.data.objects.new("crown", lathe("crown", crown["core"], core_mat))
    export.objects.link(obj)
    obj["kyt_collision"] = "none"
    obj["kyt_leaf_blades"] = True  # unwrap_blades.py lays out the unit it places
    hat_lift = dome_rings(spec["body"])[-1][1] - dome["crown_sink"]  # up the unit's axis from its pivot
    hat_depth = dome_rings(dome)[-1][1]
    spots, hats = clump_points("clumps", crown, hat_lift + hat_depth, hat_lift)
    # The upper tier: its top `rise` over the hat's, so that its brim stands
    # `proud` over the hat's leaves at the brim's reach.
    rise, hold = 0.0, hat_depth * 0.5  # hold: how far under the top hat's top its branch ends
    upper = crown.get("upper")
    if upper:
        k = upper["scale"]
        rings = [(0.0, 0.0)] + [(r, d) for r, d, _, _ in dome_rings(dome)]
        brim_r, brim_d = rings[-1]
        under = next(d0 + (d1 - d0) * (k * brim_r - r0) / (r1 - r0)
                     for (r0, d0), (r1, d1) in zip(rings, rings[1:]) if r0 <= k * brim_r <= r1)
        rise = k * brim_d - under + upper["proud"]
        hold = k * hat_depth * 0.5 - rise
    layout.objects.link(spots)
    ng = clump_skin_group()
    mod = obj.modifiers.new(ng.name, "NODES")
    mod.node_group = ng
    plant_blades._set(mod, ng, {"Hat": card, "Topper": topper, "Clumps": spots, "Hat lift": hat_lift,
                                "Hat turn": math.radians(dome["crown_turn"]), "Roundness": dome["roundness"],
                                "Centre": crown["centre"], "Show core": dome["core"], "Topper lift": rise})
    upper_card = None
    if upper:
        upper_dome = dict(dome, reach=dome["reach"] * upper["scale"])
        upper_card = bpy.data.objects.new("blade_upper", dome_card("blade_upper", upper_dome, leaf_mat))
        upper_card["kyt_around"] = card["kyt_around"]
        card.users_collection[0].objects.link(upper_card)
        plant_blades._set(mod, ng, {"Upper hat": upper_card, "Upper scale": 1.0,
                                    "Upper lift": hat_lift + hat_depth + rise - dome_rings(upper_dome)[-1][1],
                                    "Upper turn": math.radians(dome["crown_turn"] + upper["turn"])})
    if body is not None:
        plant_blades._set(mod, ng, {"Body": body})
    limbs = spec["limbs"]
    bark = plant_blades.material(f"{stem}_trunk", *limbs["colour"], double_sided=False)
    # Each branch ends half the top hat's depth in under its top, inside it,
    # through the hat under it when there is an upper tier.
    paths = [(limbs["sides"], limbs["trunk"])] + hat_branches(hats, limbs, hold)
    knots = knot_spots(paths, limbs["knots"]) if limbs.get("knots") else ()
    hole = plant_blades.material(f"{stem}_knot", *limbs["knot_colour"], double_sided=False) if knots else None
    trunk = bpy.data.objects.new("trunk", limb_mesh("trunk", paths, bark, limbs.get("tile"), knots, hole,
                                                    limbs.get("tile_grow")))
    coll = bpy.data.collections.new("trunk")
    export.children.link(coll)
    coll.objects.link(trunk)
    sprig_tris = 0
    if sprig is not None:
        # The crown as the base the clusters are spread over: its bounds as
        # built, and each hat's top kept clear by its sprouts' reach.
        bpy.context.view_layer.update()
        ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
        lo, hi = min(v.co.z for v in ev.vertices), max(v.co.z for v in ev.vertices)
        wide = 2.0 * max(v.co.xy.length for v in ev.vertices)
        base = dict(width=wide, height=hi - lo, lift=lo, square=2.0)
        clear = [(h["top"] + h["axis"] * rise * h["size"], spec["body"]["topper"]["length"] * h["size"] * 1.2)
                 for h in hats]
        place_sprigs(obj, export, base, spec["strays"], sprig, leaf_mat, "", "", avoid=clear)
        sprigs = bpy.data.objects["sprigs"]
        del sprigs["kyt_merge_group"]  # one size: they go with the crown
        sprig_tris = sum(len(p.vertices) - 2 for p in sprigs.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
    acorn_cards, acorn_counts = (), {}
    if spec.get("acorns"):
        a = spec["acorns"]
        acorn_cards = tuple(bpy.data.objects.new(n, bud_card(n, a["length"], a["width"], leaf_mat))
                            for n in ("blade_acorn", "blade_acorn_green"))
        bud = bpy.data.objects.new("blade_leaf_bud", bud_card("blade_leaf_bud", *a["buds"]["bud"], leaf_mat)) \
            if a.get("buds") else None
        fallen = tuple(bpy.data.objects.new(f"blade_fallen_{c}", fallen_leaf_card(f"blade_fallen_{c}",
                                                                                 a["ground"]["leaf_length"], leaf_mat))
                       for c in "abc") if a.get("ground") else ()
        acorn_cards += fallen + ((bud,) if bud else ())
        for c in acorn_cards:
            card.users_collection[0].objects.link(c)
        sprouts = [(h["top"] + h["axis"] * rise * h["size"], spec["body"]["topper"]["length"] * h["size"] * 1.2)
                   for h in hats]
        acorn_counts = place_acorns(obj, export, a, acorn_cards[0], acorn_cards[1], sprouts, bud)
        if fallen:
            bpy.context.view_layer.update()
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
            radius = max(v.co.xy.length for v in ev.vertices)
            acorn_counts["ground"] = place_ground(export, a["ground"], radius, acorn_cards[0], fallen, a)
    # The blades beside the tree, not in it.
    for blade in (b for b in (card, upper_card, body, topper, sprig) + acorn_cards if b):
        blade.location.x += max(out + 3.0 * r for _, out, _, r, _ in crown["tiers"]) + 1.0
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg).data
    tris = sum(len(p.vertices) - 2 for p in ev.polygons)
    bark_tris = sum(len(p.vertices) - 2 for p in trunk.data.polygons)
    xs, ys, zs = ([v.co[i] for v in ev.vertices] for i in range(3))
    print(f"leaf_skin: {name}: {len(spots.data.vertices)} clumps, {tris} triangles in the crown (core and clumps), "
          f"{sprig_tris} in {len(bpy.data.objects['sprigs'].data.vertices) if sprig else 0} stray leaf clusters, "
          f"{acorn_counts.get('hanging', 0)} acorns ({8 * acorn_counts.get('hanging', 0)} triangles, green in summer, "
          f"brown in fall, {acorn_counts.get('winter', 0)} in winter), {acorn_counts.get('buds', 0)} buds in spring "
          f"({8 * acorn_counts.get('buds', 0)} triangles), on the ground in fall {acorn_counts.get('ground', (0, 0))[0]} "
          f"acorns and {acorn_counts.get('ground', (0, 0))[1]} leaves "
          f"({8 * acorn_counts.get('ground', (0, 0))[0] + 2 * acorn_counts.get('ground', (0, 0))[1]} triangles), "
          f"{bark_tris} in the trunk and limbs, {max(zs):.2f} m tall, {max(xs) - min(xs):.2f} x {max(ys) - min(ys):.2f} m "
          f"across, crown from {min(zs):.2f} m")


# --- The file ------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv or argv[0] not in SPECIES:
        raise SystemExit(f"leaf_skin: give one of {', '.join(SPECIES)} after --")
    name, spec = argv[0], SPECIES[argv[0]]
    stem = spec.get("stem", name.split("_")[0])  # the plant's materials are `<stem>_leaf` and so on
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
        for group in ("kyt_leaf_skin", "kyt_dome_skin", "kyt_blooms_on_points", "kyt_clump_skin"):
            if bpy.data.node_groups.get(group):
                bpy.data.node_groups.remove(bpy.data.node_groups[group])
        # The plant's own materials too, so they are made again from `SPECIES`:
        # the canvas keeps the leaf's (a fake user) as the colour it paints
        # from, and a rebuild would otherwise wear its first colour and gloss.
        for part in ("leaf", "core", "bloom_card", "trunk", "knot"):
            if bpy.data.materials.get(f"{stem}_{part}"):
                bpy.data.materials.remove(bpy.data.materials[f"{stem}_{part}"])
        for pool in (bpy.data.meshes, bpy.data.materials):
            for block in list(pool):
                if block.users == 0:
                    pool.remove(block)

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
    if spec.get("body") and not spec.get("crown", {}).get("hats_only"):
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
                                                                bloom_mat, bloom_spec.get("sides", 4)))
        flower["kyt_slots"] = bloom_spec["slots"]  # its colourways, painted side by side on the canvas
        flower["kyt_shades"] = bloom_spec.get("shades", 1)  # and each colourway's shades, side by side inside its slot
        blades.objects.link(flower)
    bud = None
    if bloom_spec and bloom_spec.get("bud"):
        bud = bpy.data.objects.new("blade_bud", bud_card("blade_bud", bloom_spec["bud"]["length"],
                                                         bloom_spec["bud"]["width"], bloom_mat))
        bud["kyt_slots"] = bloom_spec["slots"]  # the flowers' colourways, in their material
        blades.objects.link(bud)
    bud_green = None
    if bloom_spec and bloom_spec.get("bud", {}).get("green"):
        bud_green = bpy.data.objects.new("blade_bud_green", bud_card("blade_bud_green", bloom_spec["bud"]["length"],
                                                                     bloom_spec["bud"]["width"], bloom_mat))
        bud_green["kyt_slots"] = bloom_spec["slots"]  # green in every colourway, in the flowers' material
        blades.objects.link(bud_green)
    sprig = None
    if spec.get("strays"):
        sprig = bpy.data.objects.new("blade_sprig", sprig_card("blade_sprig", spec["strays"], leaf_mat))
        blades.objects.link(sprig)
    plant_blades.lay_out_blades([b for b in (card, body, tier, topper, flower, bud, bud_green, sprig) if b])
    if spec.get("crown"):
        build_crown(name, spec, export, layout, card, body, topper, dome, core_mat, stem, sprig, leaf_mat)
        bpy.context.scene["kyt_godot_scene"] = spec["godot"]
        bpy.ops.wm.save_mainfile()
        print("leaf_skin: saved")
        return

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
        # Off the topper: its leaves' reach.
        topper_reach = spec["body"].get("topper", {}).get("length", 0.0) * scale if body else 0.0
        sprigs = []
        if sprig:
            sprigs = place_sprigs(bush, home, base, dict(spec["strays"], count=round(spec["strays"]["count"] * scale * tall)),
                                  sprig, leaf_mat, tag, suffix, topper_reach)
        if flower:
            blooms = bpy.data.collections.new(f"blooms{suffix}")
            home.children.link(blooms)
            # Off the topper: its leaves' reach, and half a flower's.
            keep_off = topper_reach + bloom_spec["radius"] * 0.5 if topper_reach else 0.0
            # Off the leaf clusters: each group's middle a sprig's length and a
            # flower's radius from one's foot, or, with `clear_leaves` (the
            # hibiscus's: five clusters round its middle closed that whole band
            # to its flowers, her "theres a patch on the hibiscus thats missing
            # flowers"), each flower and bud off the clusters' own leaves.
            if bloom_spec.get("clear_leaves"):
                leaves = [q for _, _, along in sprigs for q in along]
                avoid = [(q, bloom_spec["radius"] * 0.8) for q in leaves]
            else:
                leaves, avoid = [], [(at, reach + bloom_spec["radius"]) for at, reach, _ in sprigs]
            counts[tag] = place_blooms(bush, blooms, base, dict(bloom_spec, count=round(bloom_spec["count"] * scale * tall)),
                                       flower, bloom_mat, tag, suffix, keep_off, bud, avoid, bud_green, leaves)
    for tag in counts:
        if tag != "medium":
            bpy.context.view_layer.layer_collection.children["export"].children[f"size_{tag}"].hide_viewport = True

    bpy.context.scene["kyt_godot_scene"] = spec["godot"]
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    card = sum(len(p.vertices) - 2 for p in flower.data.polygons) if flower else 0
    bud_card_tris = sum(len(p.vertices) - 2 for p in bud.data.polygons) if bud else 0
    for tag, got in counts.items():
        flowers = card * got["blooms"] + bud_card_tris * (got.get("buds", 0) + got.get("buds_green", 0))
        peak = flowers + card * got["blooms_peak"] + bud_card_tris * (got.get("buds_peak", 0) + got.get("buds_green_peak", 0))
        b = bpy.data.objects["bush" if tag == "medium" else f"bush_{tag}"]
        ev = b.evaluated_get(dg).data
        tris = sum(len(p.vertices) - 2 for p in ev.polygons)
        sprigs = bpy.data.objects.get("sprigs" if tag == "medium" else f"sprigs_{tag}")
        if sprigs:
            tris += sum(len(p.vertices) - 2 for p in sprigs.evaluated_get(dg).data.polygons)
        zs = [v.co.z for v in ev.vertices]
        domes = len(bpy.data.objects["domes" if tag == "medium" else f"domes_{tag}"].data.vertices)
        print(f"leaf_skin: {name} {tag}: {domes} domes, "
              f"{got['blooms']} blooms ({got['blooms'] + got['blooms_peak']} at peak), "
              f"{got.get('buds', 0) + got.get('buds_green', 0)} buds, {got.get('buds_green', 0)} green "
              f"({sum(got.get(k, 0) for k in ('buds', 'buds_peak', 'buds_green', 'buds_green_peak'))} at peak), "
              f"{tris + flowers} triangles ({tris + peak} at peak, "
              f"{tris} in winter), {max(zs):.2f} m tall, low {min(zs):.3f}")
    bpy.ops.wm.save_mainfile()
    print("leaf_skin: saved")


if __name__ == "__main__":
    main()
