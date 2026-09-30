"""The hardscape kit: little brick retaining walls with piers, iron railings
and fences, and concrete curbs, in pieces that snap together on the hedge
kit's one-metre grid (2026-09-30).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/hardscape_kit.blend --python tools/blender/hardscape_kit.py -- [--replace] [--save]
    ... --python tools/blender/hardscape_kit.py -- --render <folder>

After her photograph of a front-garden wall on a city sidewalk
(`documentation/reference/hardscape_kit/brick_wall_iron_railing.webp`), "time
for fences and little retaining walls and curbs": red brick in running bond
with light mortar, a thick coping, brick piers under thick flat caps (the
coping and caps one solid light colour, her "the ledge parts should be a
solid lighter color" and "make the brick coping and caps match"; her
photograph's rock-faced cast stone was built and taken out), and between the
piers a black railing standing on the coping, square pickets between a flat
top rail and a flat bottom rail (all square: her photograph's twisted ones
were built and taken out, her "no twisted bars"), a heavier post against each pier face (her photograph's
double scroll either side of a picket was built and taken out too, her "no
need for the ornamentation"). The street's curb is the Southern
California curb and gutter, the everyday one (`design.md`, "The everyday").
Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
bricks a touch large, bars a touch thick, every edge rounded over.

The kit is one prop, one canvas and one material, in kinds (each piece a
`kyt_variant`, `<kind>_<size>_<piece>`), every piece on the hedge kit's grid:
its origin the middle of its first cell, the run along the cells' middles, open
ends meeting open ends, so Godot's one-metre snap and quarter turns lay pieces
together and a wall, its railing and a hedge beside it share one plan.

- `wall_seat`, `wall_garden`: the wall with its coping on top, `seat` at
  sitting height (coping 0.475 m), `garden` her photograph's (0.70 m). Pieces
  `straight`, `straight_2`, `straight_4`, `corner` (west to north), `tee`,
  `cross`, `end` (from the west, closed a half-width past the middle), `bend`,
  `curve`, `curve_large` (radii 0.5, 1.5, 2.5 m, as the hedges'), and `pier`,
  a brick pier under its cap, which stands over whichever wall piece is in its
  cell (they overlap; the pier hides the wall and railing inside it). A wall
  goes `FOOT` below the ground, so uneven ground never shows under it; which
  side is the higher ground is the terrain's business, not the piece's.
- `town_wall_seat`, `town_wall_garden`: the same brick walls weathered for
  the beach town outside the park (her "remember this is a beach town", "lots
  of sun and history", "lets keep this, though in the park itself it will be
  a different kind of weathering"): sun-bleached, salt at the foot, patched
  and chipped. The park's own, `wall_*`, are only a little darker toward the
  bottom (her "mostly just a little darker towards the bottom"). Every wall
  has rain streaks under its coping and caps (her "maybe all of them can have
  some rain streaks under the ledge at the top").
- `concrete_wall_seat`, `concrete_wall_garden`: the same walls and piers in
  poured concrete instead of brick (her "lets make a version of the wall thats
  concrete", "instead of brick"): every shape, height, coping and cap as the
  brick's, so railings and piers fit both; only the body is poured concrete.
- `railing_wall`: the railing that stands on a wall's coping (placed at the
  coping's height). `railing_fence`: the same railing standing on the ground
  as a fence, taller, with posts with ball finials. Both have a little section
  across the top, a second rail just under the top one. Pieces
  as the wall's, less `pier`, plus, for the wall railing, `pier` (a metre whose
  two posts stand just off a pier's faces), for the fence `post`. An `end`
  stops at a post: the wall railing's just off the face of a pier on its end
  cell, the fence's on the middle. Rails and posts collide; pickets don't.
  (The wall railing was tried in segments, the fence's posts and balls at
  four fifths every two metres, and taken out: her "the non free standing
  iron segments are weird so lets revert those".)
- `curb_road`, `curb_road_red`: curb and gutter, the road to the south of a
  west-to-east run, its back at the sidewalk to the north. `red` is the same
  piece painted for no parking, the fire lane. Pieces `straight`, `straight_2`,
  `straight_4`, `bend`, `curve`, `curve_large` (turning north: the road
  outside, a street corner's curb return), `bend_in`, `curve_in`,
  `curve_large_in` (turning south: the road inside, a turning circle's),
  `end` (tapering down into the gutter), `cut` (two cells, the curb dropped
  for a driveway or a ramp). `curb_edging`: a small bullnosed curb round a
  bed, the same both sides, pieces as the wall's less `pier`. Curbs don't
  collide: the player has no step-up, and a centimetre of lip is a wall
  (`AGENTS.md`, Geometry), as the approach road's visual curb.

Bird droppings (her "bird poop on the ledges", "and iron railings"): small
cut-out cards lying on the copings, caps and top rails, three scatterings a
piece (merge groups `droppings_a` to `_c`), the wrapper choosing one by the
grid square a placement stands on, as the hedges choose their leaf clusters.

The canvas (`assets/source/textures/hardscape_kit/`) is one metre wide and
repeats along every run, `PX_M` pixels a metre: a wall's bricks sit by their
height (a course is `COURSE`, the ground a bed joint, the coping's underside
and the piers' tops on joints too) and along the grid, so pieces and piers
line up course for course. A wall's body is mapped in two parts (`STREAK_M`). Down the canvas are bands for the bricks, the
concrete, the coping and caps (one solid colour, the coping's seams a metre
apart), the iron and the three
curbs (the red curb's band holds only its painted top and face; the rest of
it wears the plain curb's); a bump (`<prop>_bump.png`, white raised: mortar
sunk, bricks rounded at their arrises, bug holes in the concrete) and the
normal map made from it. Nothing is cut out, so the material is opaque. `tools/bump_to_normal.py` knows this prop's depth
and that its canvas wraps round.

A piece reshaped by hand is kept: a run refuses while any piece differs from
what this tool last built, and names it. `--replace` builds over it anyway.
Saves with `--save`. `--render <folder>` renders the sample street (her
photograph's view, from above, the railing and a pier close, the curb), the
kinds beside a person and a sheet of each kind's pieces, without saving.
"""

import hashlib
import math
import os
import sys
import zlib

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bump_to_normal import DEPTH_PX, WRAP_U, normal_from_height  # noqa: E402
from paint_canvas import grow, one_material, srgb  # noqa: E402

NAME = "hardscape_kit"
E = 0.5  # half a grid cell
FOOT = 0.2  # walls and curbs reach this far below the ground
SEED = 30

# --- walls ------------------------------------------------------------------

# Her photograph's wall: coping about 0.7 m over the sidewalk, eight courses
# under it; the pier seven more courses over the coping, then its cap; the
# railing's top rail just under the pier's top. `seat` is a sitting wall
# round a bed, the bench's seat height. Heights sit on brick courses.
COURSE = 0.075  # 1.1 real courses: chunky, and 0.6 m is eight of them
BRICK = 0.25  # four to the metre, so the running bond repeats every metre
JOINT = 0.011
WALLS = {
    "seat": dict(top=0.475, pier_top=1.05),
    "garden": dict(top=0.70, pier_top=1.275),
}
WALL_W = 0.30
COPING_W = 0.42  # 6 cm over each face
COPING_T = 0.10
COPING_NOSE = 0.022  # the top edge's round
COPING_HEEL = 0.008  # the bottom edge's
COPING_WASH = 0.012  # the top rises this much to its middle, to shed rain
PIER_W = 0.45
CAP_W = 0.57
CAP_T = 0.10
CAP_WASH = 0.012
NOSE_STEPS = 3
WALL_PIECES = ("straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "bend", "curve",
               "curve_large", "pier")
ARCS = {"bend": 0.5, "curve": 1.5, "curve_large": 2.5}  # radius along the middle
# A wall's body is mapped in two parts. Its top `STREAK_M` under the coping
# or cap goes by distance down from that ledge onto a streak band, which
# carries the rain streaks, the same under every ledge whatever its height;
# the rest goes by height above the ground onto the body band, whose foot is
# the ground (the darkening, the salt, the sand). Every ledge's underside and
# so every split is on a course joint, so the bricks line up across it; a
# running bond's stagger depends on whether the course under the ledge is odd
# or even, so each body has two streak bands, painted as the garden wall's
# (`even`, eight courses) and the sitting wall's (`odd`, five) are, and the
# foot's weathering stays below the lowest split, the sitting wall's.
STREAK_M = 2 * COURSE
UNDERSIDES = {"even": WALLS["garden"]["top"] - COPING_T, "odd": WALLS["seat"]["top"] - COPING_T}
Z_BODY_TOP = max(w["pier_top"] for w in WALLS.values()) - STREAK_M  # the highest split
LEDGE_IN = 0.02  # a body reaches this far up inside its ledge
# The rain streaks: running down from under a ledge from `RAIN_DRIPS` of its
# columns, each up to `STREAK_M` long, darkening by up to `RAIN_DARK`; a
# faint wet line right under the ledge.
RAIN_DRIPS, RAIN_DARK = 0.025, 0.45
# The park's bricks: only a little darker toward the ground.
FOOT_DARK, FOOT_UP = 0.16, 0.2
BODIES = {"wall": "brick", "town_wall": "town_brick", "concrete_wall": "concrete"}
# Bird droppings: cards of `DROP_SIZE` (the top rail's narrower, `DROP_RAIL_W`
# across it), `DROP_LIFT` over what they lie on, at least `DROP_APART`
# apart, about `DROP_RATE` a metre of wall or top rail and `DROP_PIER` a cap;
# painted `DROP_CELLS` ways in a row of the canvas.
DROP_SIZE, DROP_RAIL_W, DROP_LIFT, DROP_APART = (0.06, 0.12), 0.036, 0.0015, 0.15
DROP_RATE = {"wall": 0.7, "railing": 0.35}
DROP_PIER = 0.5
DROP_CELLS, DROP_CELL = 8, 0.1
DROP_SETS = ("a", "b", "c")

# --- railings ----------------------------------------------------------------

# Rails: (height of the middle, width, depth), the top rail last. The wall
# railing stands on the coping (its 0 the coping's top at the face, the
# middle `COPING_WASH` higher), its bottom rail clear of it as in her
# photograph; the fence stands on the ground. Pickets run from the bottom
# rail into the top one. Under the top rail a second rail closes a little
# section across the top, the pickets running through it (her "instead give
# the iron parts a little section at the top", with a photograph of a black
# fence on a curved stone wall, in place of the double scroll): its clear
# height `TOP_SECTION`. The fence's middle rail, which framed the scroll, is
# that second rail now.
TOP_SECTION = {"wall": 0.08, "fence": 0.10}
RAILINGS = {
    "wall": dict(rails=((0.045, 0.045, 0.02), (0.52 - TOP_SECTION["wall"] - 0.01, 0.045, 0.02),
                        (0.535, 0.05, 0.03)), post_top=0.56),
    "fence": dict(rails=((0.12, 0.045, 0.02), (1.07 - TOP_SECTION["fence"] - 0.01, 0.045, 0.02),
                         (1.085, 0.05, 0.03)), post_top=1.13),
}
PICKET = 0.022  # square
PICKET_STEP = 0.125  # eight to the metre, so the pattern repeats every metre
END_POST = 0.056  # the posts against a pier and at an end, heavier than a picket
PIER_POST_AT = PIER_W / 2 + 0.008 + END_POST / 2  # a pier's posts just off its faces
FENCE_POST = 0.07
FENCE_POST_SINK = 0.3
FINIAL_R = 0.045
RAILING_PIECES = ("straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "bend",
                  "curve", "curve_large")

# --- curbs --------------------------------------------------------------------

# Profiles (across, z, part), across positive to the north of a west-to-east
# run, listed from the back's foot over the top to the front's: the order
# that faces them outward. `part` names the stretch that starts at the point.
# The road curb: 6 inches of reveal with a batter on its face and a round on
# both top edges, then a gutter pan sloping up from the flow line to its lip,
# flush with the road; its back meets the sidewalk.


def _round(cy, cz, r, a0, a1, steps, part):
    return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / steps)), part) for k in range(steps + 1)]


ROAD_CURB = ([(0.09, -FOOT, "back")] + _round(0.07, 0.13, 0.02, 0, 90, 2, "top")
             + _round(-0.06, 0.12, 0.03, 90, 180, 3, "face")
             + [(-0.10, 0.012, "gutter"), (-0.50, 0.024, "lip"), (-0.50, -0.10, "lip")])
EDGING = ([(0.075, -0.15, "back")] + _round(0.035, 0.05, 0.04, 0, 90, 3, "top")
          + _round(-0.035, 0.05, 0.04, 90, 180, 3, "top")[:-1] + [(-0.075, 0.05, "front"), (-0.075, -0.15, "front")])
RED_PARTS = ("top", "face")  # what the red curb's paint covers
CURB_FLOW = 0.012  # the gutter's flow line: `cut` and `end` bring the curb down to it
CURB_LOW = 0.1  # the share of the curb left over the flow line where it is cut
CURB_PIECES = {
    "road": ("straight", "straight_2", "straight_4", "bend", "curve", "curve_large", "bend_in", "curve_in",
             "curve_large_in", "end", "cut"),
    "edging": ("straight", "straight_2", "straight_4", "corner", "tee", "end", "bend", "curve", "curve_large"),
}

# --- the canvas ---------------------------------------------------------------

PX_M = 512
CANVAS_W = PX_M
CANVAS_H = 16 * PX_M  # 512 by 8192: two brick looks and the concrete, each with its streak bands
CANVAS_H_M = CANVAS_H / PX_M
MARGIN_M = 0.04


def srgb_bytes(r, g, b):
    c = np.array((r, g, b), dtype=np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


# Colours from her photograph, as the sRGB a colour picker shows.
# The bricks softened and weathered for a beach town (her "lets soften the
# bricks colors a bit too and weather", "remember this is a beach town", "lots
# of sun and history"): sun-faded terracotta, the odd redder replacement brick
# (`BRICK_PATCH`, `PATCHES` of them), bleached in soft patches toward
# `SUN_BLEACH` (`BLEACH` and up to twice it), corners chipped to the paler
# clay inside (`CLAY`), mortar worn back here and fresh-pointed there, salt
# bloom rising from the foot (`SALT`, up to `SALT_UP` high), sand at the foot
# (`SAND`), and wind-worn pits. It was 172, 76, 58 with a dark city grime.
BRICK_COLOUR = srgb_bytes(182, 104, 84)
BRICK_PATCH = srgb_bytes(168, 80, 62)
SUN_BLEACH = srgb_bytes(224, 198, 178)
CLAY = srgb_bytes(222, 170, 140)
SALT = srgb_bytes(238, 234, 224)
SAND = srgb_bytes(208, 188, 154)
FRESH_MORTAR = srgb_bytes(226, 221, 208)
PATCHES, BLEACH, SALT_UP = 0.04, 0.14, 0.22  # salt below the sitting wall's streak band (0.225 m)
# Poured, darker and warmer than the curbs (her "make the body of the wall a
# little darker and warmer"; it was 192, 188, 178).
WALL_CONCRETE = srgb_bytes(180, 172, 157)
# Every wall's coping and caps, one solid colour (her "just a touch greyer",
# then "still a bit too white"; it was 224, 221, 213, then 211, 209, 203).
LEDGE_CONCRETE = srgb_bytes(197, 195, 189)
# The coping's seams (her "lets use the texture to add some seams here and
# there"): one where each metre's section meets the next, in the middle of a
# cell, so a pier standing there hides it; `SEAM_M` wide, `SEAM_DARK` darker
# and sunk in the bump. The caps are one piece each.
SEAM_M, SEAM_DARK = 0.006, 0.8
# Their edges roughed up (her "can we kind of rough up the edges a bit?"):
# chips and nicks along the nose and the heel, `CHIP_REACH` either side of the
# middle of each, `CHIP_DARK` darker and sunk in the bump. Weathered a tad
# (her "weather them a tad"): blotches `WEATHER` either way, streaks down the
# edge face darkening toward its foot by up to `STREAK`, the underside
# `UNDER_DARK` darker.
CHIP_REACH, CHIP_DARK = (0.016, 0.01), 0.84
WEATHER, STREAK, UNDER_DARK = 0.035, 0.07, 0.9
BRICK_DARK = srgb_bytes(152, 88, 74)  # the odd darker, browner brick
BRICK_LIGHT = srgb_bytes(202, 132, 106)
MORTAR_COLOUR = srgb_bytes(214, 205, 186)
IRON_COLOUR = srgb_bytes(30, 30, 33)
# The iron weathered a little (her "is there a way to weather the iron too a
# little"): the paint faded toward `IRON_FADED` in soft patches (up to
# `FADE`), a few rust spots (`RUST_SPOTS` a pixel, each with a faint brown
# halo) and the odd chip to grey primer (`CHIPS` a pixel). The iron's canvas
# is one strip every bar and rail wears, so the weathering falls anywhere.
IRON_FADED = srgb_bytes(64, 63, 64)
RUST = srgb_bytes(116, 60, 36)
PRIMER = srgb_bytes(104, 101, 96)
FADE, RUST_SPOTS, CHIPS = 0.3, 3e-4, 1.5e-4
CONCRETE = srgb_bytes(196, 192, 183)
GUTTER = srgb_bytes(152, 147, 139)
RED_PAINT = srgb_bytes(184, 42, 38)
DROP_WHITE = srgb_bytes(238, 236, 226)
DROP_CORE = srgb_bytes(118, 116, 98)
SOIL = srgb_bytes(84, 68, 52)


def length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def coping_profile(width, top, t, wash, into):
    """A coping or cap in section, (inset from its outline, z, part), from its
    middle out over the nose, down its edge and in under it to
    `into`, inside the wall or pier it sits on."""
    h, r, heel = width / 2, COPING_NOSE, COPING_HEEL
    pts = [(h, top + wash, "top")]
    pts += [(r - r * math.sin(math.pi / 2 * k / NOSE_STEPS), top - r + r * math.cos(math.pi / 2 * k / NOSE_STEPS),
             "top" if k == 0 else "face") for k in range(NOSE_STEPS + 1)]
    pts += [(0.0, top - t + heel, "face"), (heel, top - t, "under"), (into + 0.01, top - t, "under")]
    return pts


def layout():
    """The canvas's bands, (top, bottom) in metres down from its top."""
    wall = WALLS["garden"]
    sizes = []
    for body in BODIES.values():
        sizes += [(body, Z_BODY_TOP + FOOT)] + [(f"{body}_streak_{p}", STREAK_M + LEDGE_IN) for p in UNDERSIDES]
    sizes += [
        ("coping", length([(d, z) for d, z, _ in coping_profile(COPING_W, wall["top"], COPING_T, COPING_WASH,
                                                                (COPING_W - WALL_W) / 2)])),
        ("cap", length([(d, z) for d, z, _ in coping_profile(CAP_W, wall["pier_top"] + CAP_T, CAP_T, CAP_WASH,
                                                             (CAP_W - PIER_W) / 2)])),
        ("iron", 0.25),
        ("curb_road", length(ROAD_CURB)),
        ("curb_road_red", sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(ROAD_CURB, ROAD_CURB[1:])
                              if a[2] in RED_PARTS)),
        ("curb_edging", length(EDGING)),
        ("droppings", DROP_CELL + 0.02),
    ]
    y, bands = MARGIN_M, {}
    for name, size in sizes:
        bands[name] = (y, y + size)
        y += size + MARGIN_M
    if y > CANVAS_H_M:
        raise SystemExit(f"hardscape_kit: the bands need {y:.2f} m of canvas; it is {CANVAS_H_M:.2f} m tall")
    return bands


def v_of(m):
    """A canvas position in metres down from its top, as a UV's v."""
    return 1.0 - m / CANVAS_H_M


def brick_v(bands, z, band="brick"):
    """Where height `z` of a wall's body lies down its body band."""
    return bands[band][0] + (Z_BODY_TOP - z)


def profile_v(profile, band_top):
    """Each profile point's canvas row: the band's top plus how far along the
    profile it lies."""
    out, s = [], 0.0
    for k, p in enumerate(profile):
        if k:
            s += math.hypot(p[0] - profile[k - 1][0], p[1] - profile[k - 1][1])
        out.append(band_top + s)
    return out


# --- footprints (the hedge kit's, `hedge_kit.py`, copied: that file is in use) --


def footprint(piece, w):
    """(points, closed, u, ring): the piece's outline in plan, anticlockwise;
    `closed[i]` whether the side from point i to the next is built (it isn't
    where the piece meets the next); `u(i, k, p)` the canvas's run along side
    i at point k, placed at p; `ring(d)` the outline with its built sides `d`
    in (out when negative)."""
    h = w / 2
    if piece in ARCS:
        radius = ARCS[piece]
        n = max(6, round(6 * radius))
        centre = Vector((-E, radius))
        turns = np.linspace(-math.pi / 2, 0.0, n + 1)

        def ring(d):
            return ([centre + (radius + h - d) * Vector((math.cos(t), math.sin(t))) for t in turns]
                    + [centre + (radius - h + d) * Vector((math.cos(t), math.sin(t))) for t in turns[::-1]])

        runs = (max(1, round((radius + h) * math.pi / 2)), max(1, round((radius - h) * math.pi / 2)))

        def u(i, k, p):
            return -E + (k / n * runs[0] if k <= n else (2 * n + 1 - k) / n * runs[1])

        return ring(0.0), [True] * n + [False] + [True] * n + [False], u, ring
    if piece.startswith("straight"):
        x1 = E + {"straight": 0, "straight_2": 1, "straight_4": 3}[piece]
        pts, closed = [(-E, -h), (x1, -h), (x1, h), (-E, h)], [True, False, True, False]
    elif piece == "corner":
        pts = [(-E, -h), (h, -h), (h, E), (-h, E), (-h, h), (-E, h)]
        closed = [True, True, False, True, True, False]
    elif piece == "tee":
        pts = [(-E, -h), (E, -h), (E, h), (h, h), (h, E), (-h, E), (-h, h), (-E, h)]
        closed = [True, False, True, True, False, True, True, False]
    elif piece == "cross":
        pts = [(-E, -h), (-h, -h), (-h, -E), (h, -E), (h, -h), (E, -h), (E, h), (h, h), (h, E), (-h, E), (-h, h),
               (-E, h)]
        closed = [True, True, False, True, True, False] * 2
    elif piece == "end":
        pts, closed = [(-E, -h), (h, -h), (h, h), (-E, h)], [True, True, True, False]
    elif piece in ("post", "pier"):
        pts, closed = [(-h, -h), (h, -h), (h, h), (-h, h)], [True] * 4
    else:
        raise KeyError(piece)
    pts = [Vector(p) for p in pts]

    def u(i, k, p):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        return p.x if abs(b.x - a.x) > abs(b.y - a.y) else p.y

    return pts, closed, u, lambda d: inset_ring(pts, closed, d)


def inset_ring(pts, closed, d):
    n = len(pts)
    out = []
    for i in range(n):
        p = pts[i]
        e_in = (p - pts[i - 1]).normalized()
        e_out = (pts[(i + 1) % n] - p).normalized()
        n_in, n_out = Vector((-e_in.y, e_in.x)), Vector((-e_out.y, e_out.x))
        d_in, d_out = (d if closed[i - 1] else 0.0), (d if closed[i] else 0.0)
        det = n_in.x * n_out.y - n_in.y * n_out.x
        if abs(det) < 1e-9:
            out.append(p + n_in * d_in)
            continue
        b1, b2 = p.dot(n_in) + d_in, p.dot(n_out) + d_out
        out.append(Vector(((b1 * n_out.y - b2 * n_in.y) / det, (n_in.x * b2 - n_out.x * b1) / det)))
    return out


class Builder:
    """A bmesh with one UV layer, welding vertices by position within a sheet."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.verts = {}

    def vert(self, co, weld=True):
        if not weld:
            return self.bm.verts.new(co)
        key = (round(co[0], 5), round(co[1], 5), round(co[2], 5))
        if key not in self.verts:
            self.verts[key] = self.bm.verts.new(co)
        return self.verts[key]

    def face(self, loop):
        """`loop`: (vertex, (u, v)) round the face, outward anticlockwise."""
        out = []
        for v, t in loop:
            if out and out[-1][0] is v:
                continue
            out.append((v, t))
        if len(out) > 1 and out[0][0] is out[-1][0]:
            out.pop()
        if len(out) < 3:
            return None
        try:
            f = self.bm.faces.new([v for v, _ in out])
        except ValueError:
            return None
        if f.calc_area() < 1e-9:
            self.bm.faces.remove(f)
            return None
        for corner, (_, t) in zip(f.loops, out):
            corner[self.uv].uv = t
        return f

    def sheet(self, outline, sheet):
        """A section, [(inset, z, canvas row in metres)], from its top or middle
        outward and down, round the outline's built sides."""
        pts, closed, u, ring = outline
        rings = [ring(d) for d, z, m in sheet]
        n = len(pts)
        for k in range(len(sheet) - 1):
            for i in range(n):
                if not closed[i]:
                    continue
                j = (i + 1) % n
                loop = []
                for kk, ii in ((k, i), (k + 1, i), (k + 1, j), (k, j)):
                    p = rings[kk][ii]
                    loop.append((self.vert((p.x, p.y, sheet[kk][1])), (u(i, ii, p), v_of(sheet[kk][2]))))
                self.face(loop)

    def sweep(self, path, profile, rows, u_scale=1.0, closed=False, zmap=None):
        """`profile` [(across, z, _)] swept along the polyline `path`, mitred at
        its corners, `rows` each point's canvas row (a closed profile's last
        side runs on past its last row); u runs with the distance along, from
        -E. Returns each profile ring's vertices."""
        frames = path_frames(path)
        k = len(profile)
        rings = []
        for p, m, s in frames:
            ring = []
            for y, z, _ in profile:
                q = p + m * y
                ring.append(self.bm.verts.new((q.x, q.y, zmap(p, s, y, z) if zmap else z)))
            rings.append(ring)
        for i in range(len(frames) - 1):
            u0, u1 = -E + frames[i][2] * u_scale, -E + frames[i + 1][2] * u_scale
            for j in range(k if closed else k - 1):
                jj = (j + 1) % k
                va = rows[j]
                vb = va + math.hypot(profile[jj][0] - profile[j][0], profile[jj][1] - profile[j][1])
                self.face([(rings[i][j], (u0, v_of(va))), (rings[i][jj], (u0, v_of(vb))),
                           (rings[i + 1][jj], (u1, v_of(vb))), (rings[i + 1][j], (u1, v_of(va)))])
        return rings

    def cap(self, ring, profile, band_row, forward):
        """Close a swept profile's end, facing along the path when `forward`,
        its canvas a patch of the band at `band_row`."""
        loop = [(v, (0.5 + y, v_of(band_row + 0.2 - z))) for v, (y, z, _) in zip(ring, profile)]
        self.face(loop if forward else loop[::-1])

    def bar(self, x, y, z0, z1, size, band_row, top=False, turn=0.0):
        """An upright square bar from z0 to z1, turned `turn` round its
        middle, its faces round `band_row`; `top` closes its top."""
        zs = [z0, z1]
        h = size / 2

        def corners(z):
            return [(x + h * math.sqrt(2) * math.cos(turn + math.pi / 4 + q * math.pi / 2),
                     y + h * math.sqrt(2) * math.sin(turn + math.pi / 4 + q * math.pi / 2), z) for q in range(4)]

        rings = [[self.bm.verts.new(c) for c in corners(z)] for z in zs]
        for i in range(len(zs) - 1):
            for q in range(4):
                qq = (q + 1) % 4
                v0, v1 = band_row + q * size, band_row + (q + 1) * size
                self.face([(rings[i][q], (zs[i], v_of(v0))), (rings[i][qq], (zs[i], v_of(v1))),
                           (rings[i + 1][qq], (zs[i + 1], v_of(v1))), (rings[i + 1][q], (zs[i + 1], v_of(v0)))])
        if top:
            self.face([(v, (0.2 + (v.co.x - x), v_of(band_row + 0.15 + (v.co.y - y)))) for v in rings[-1]])

    def box(self, centre, size, band_row, bottom=False):
        """A box, every face but its bottom unless asked."""
        cx, cy, cz = centre
        sx, sy, sz = (s / 2 for s in size)
        c = [self.bm.verts.new((cx + a * sx, cy + b * sy, cz + d * sz))
             for d in (-1, 1) for b in (-1, 1) for a in (-1, 1)]
        faces = [(4, 5, 7, 6), (0, 1, 5, 4), (1, 3, 7, 5), (3, 2, 6, 7), (2, 0, 4, 6)]
        if bottom:
            faces.append((0, 2, 3, 1))
        for f in faces:
            self.face([(c[i], (0.3 + 0.05 * k, v_of(band_row + 0.02 + 0.03 * (k % 2)))) for k, i in enumerate(f)])

    def ball(self, centre, r, band_row, segments=8, rings=4):
        cx, cy, cz = centre
        top = self.bm.verts.new((cx, cy, cz + r))
        bottom = self.bm.verts.new((cx, cy, cz - r))
        grid = []
        for i in range(1, rings):
            phi = math.pi * i / rings
            grid.append([self.bm.verts.new((cx + r * math.sin(phi) * math.cos(2 * math.pi * j / segments),
                                            cy + r * math.sin(phi) * math.sin(2 * math.pi * j / segments),
                                            cz + r * math.cos(phi))) for j in range(segments)])

        def t(j, i):
            return (0.6 + 0.3 * j / segments, v_of(band_row + 0.02 + 0.15 * i / rings))

        for j in range(segments):
            jj = (j + 1) % segments
            self.face([(top, t(j, 0)), (grid[0][j], t(j, 1)), (grid[0][jj], t(j + 1, 1))])
            for i in range(len(grid) - 1):
                self.face([(grid[i][j], t(j, i + 1)), (grid[i + 1][j], t(j, i + 2)),
                           (grid[i + 1][jj], t(j + 1, i + 2)), (grid[i][jj], t(j + 1, i + 1))])
            self.face([(grid[-1][j], t(j, rings - 1)), (bottom, t(j, rings)), (grid[-1][jj], t(j + 1, rings - 1))])

    def mesh(self, name, material):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        me.materials.append(material)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(50))
        return me


def path_frames(points):
    """Each point of a polyline with its left normal, mitred at corners, and
    its distance along."""
    out, s, n = [], 0.0, len(points)
    for i, p in enumerate(points):
        if i:
            s += (p - points[i - 1]).length
        if i == 0 or i == n - 1:
            t = (points[1] - points[0]) if i == 0 else (p - points[i - 1])
            t = t.normalized()
            if n > 3:
                # A curve in chords: its ends turn half a chord's angle past
                # the end chords, so they are square to the curve and meet
                # the next piece's.
                a = (points[1] - points[0]) if i == 0 else (points[-2] - points[-3])
                b = (points[2] - points[1]) if i == 0 else (points[-1] - points[-2])
                half = math.atan2(a.x * b.y - a.y * b.x, a.dot(b)) / 2 * (-1 if i == 0 else 1)
                t = Vector((t.x * math.cos(half) - t.y * math.sin(half), t.x * math.sin(half) + t.y * math.cos(half)))
            m = Vector((-t.y, t.x))
        else:
            a, b = (p - points[i - 1]).normalized(), (points[i + 1] - p).normalized()
            na, nb = Vector((-a.y, a.x)), Vector((-b.y, b.x))
            m = (na + nb).normalized()
            if n <= 3:
                # A sharp corner is mitred; a curve's points keep their
                # offsets on the radius, so its sides are true concentric arcs
                # (a gutter reaching a tight bend's centre stops there).
                m = m / max(m.dot(na), 0.2)
        out.append((p, m, s))
    return out


def arc(radius, inward=False, per_m=4):
    """A quarter circle from the west edge of the first cell, heading east,
    turning north (south when `inward`), as the hedges' curves."""
    n = max(8, round(per_m * radius * math.pi / 2))
    if inward:
        centre = Vector((-E, -radius))
        turns = np.linspace(math.pi / 2, 0.0, n + 1)
    else:
        centre = Vector((-E, radius))
        turns = np.linspace(-math.pi / 2, 0.0, n + 1)
    return [centre + radius * Vector((math.cos(t), math.sin(t))) for t in turns]


def paths(piece):
    """The piece's run along the cells' middles as polylines."""
    if piece in ARCS:
        return [arc(ARCS[piece])]
    if piece.endswith("_in"):
        return [arc(ARCS[piece.removesuffix("_in")], inward=True)]
    x1 = E + {"straight_2": 1, "straight_4": 3, "cut": 1}.get(piece, 0)
    if piece in ("straight", "straight_2", "straight_4", "pier", "post", "cut"):
        return [[Vector((-E, 0.0)), Vector((x1, 0.0))]]
    if piece == "corner":
        return [[Vector((-E, 0.0)), Vector((0.0, 0.0)), Vector((0.0, E))]]
    if piece == "tee":
        return [[Vector((-E, 0.0)), Vector((E, 0.0))], [Vector((0.0, 0.0)), Vector((0.0, E))]]
    if piece == "cross":
        return [[Vector((-E, 0.0)), Vector((E, 0.0))], [Vector((0.0, -E)), Vector((0.0, E))]]
    if piece == "end":
        return [[Vector((-E, 0.0)), Vector((0.0, 0.0))]]
    raise KeyError(piece)


def u_scale(path):
    """Stretch a curve's canvas to a whole number of metres, so it meets the
    next piece's."""
    total = length([(p.x, p.y) for p in path])
    return max(1, round(total)) / total if total > 0 else 1.0


# --- building the pieces ---------------------------------------------------------


def wall_piece(size, piece, bands, body):
    """A wall piece or pier, its body on `body`'s bands: the top under the
    ledge on a streak band, the rest by height (`STREAK_M`)."""
    spec = WALLS[size]
    b = Builder()
    if piece == "pier":
        outline = footprint("pier", CAP_W)
        into = (CAP_W - PIER_W) / 2
        prof = coping_profile(CAP_W, spec["pier_top"] + CAP_T, CAP_T, CAP_WASH, into)
        underside = spec["pier_top"]
    else:
        outline = footprint(piece, COPING_W)
        into = (COPING_W - WALL_W) / 2
        prof = coping_profile(COPING_W, spec["top"], COPING_T, COPING_WASH, into)
        underside = spec["top"] - COPING_T
    rows = profile_v(prof, bands["cap" if piece == "pier" else "coping"][0])
    b.sheet(outline, [(d, z, m) for (d, z, _), m in zip(prof, rows)])
    body_top, split = underside + LEDGE_IN, underside - STREAK_M
    parity = "even" if round(underside / COURSE) % 2 == 0 else "odd"
    streak = bands[f"{body}_streak_{parity}"][0]
    b.sheet(outline, [(into, body_top, streak), (into, split, streak + body_top - split)])
    b.sheet(outline, [(into, split, brick_v(bands, split, body)), (into, -FOOT, brick_v(bands, -FOOT, body))])
    return b


def fence_post(b, x, y, bottom, top, size, iron):
    """A fence post `size` square from `bottom` to `top`, under a cap plate, a
    neck and a ball finial, all in proportion to it (the fence's own is
    `FENCE_POST`)."""
    k = size / FENCE_POST
    b.bar(x, y, bottom, top, size, iron + 0.02)
    b.box((x, y, top + 0.012 * k), (size + 0.025 * k, size + 0.025 * k, 0.024 * k), iron)
    b.bar(x, y, top + 0.02 * k, top + 0.045 * k, 0.03 * k, iron + 0.02)
    b.ball((x, y, top + 0.045 * k + FINIAL_R * k * 0.85), FINIAL_R * k, iron)


def picket_spots(path, skip=()):
    """Where the pickets stand along a polyline: every `PICKET_STEP` from half
    a step in, so a metre holds eight and the pattern runs on from piece to
    piece; on a curve as many as fit, evenly. Those within a `skip` (point,
    radius) are left out. (point, direction, index)."""
    frames = path_frames(path)
    total = frames[-1][2]
    if len(path) > 3:
        count = max(1, round(total / PICKET_STEP))
        step = total / count
    else:
        step = PICKET_STEP
        count = math.ceil(total / step - 0.5 - 1e-9)
    out = []
    for k in range(count):
        s = (k + 0.5) * step
        for (p0, _, s0), (p1, _, s1) in zip(frames, frames[1:]):
            if s0 <= s <= s1:
                p = p0 + (p1 - p0) * ((s - s0) / (s1 - s0))
                if not any((p - Vector(q)).length < r for q, r in skip):
                    out.append((p, (p1 - p0).normalized(), k))
                break
    return out


def railing_piece(size, piece, bands):
    """(rails and posts, pickets): the first collides."""
    spec = RAILINGS[size]
    iron = bands["iron"][0]
    solid, light = Builder(), Builder()
    rails = spec["rails"]
    picket_from, picket_to = rails[0][0], rails[-1][0]
    skip = []
    posts = []  # (x, y, size, kind)
    if piece == "end":
        at = -PIER_POST_AT if size == "wall" else 0.0
        posts.append((at, 0.0, END_POST if size == "wall" else FENCE_POST, "end" if size == "wall" else "fence"))
        skip.append(((at, 0.0), (END_POST if size == "wall" else FENCE_POST) / 2 + PICKET / 2 + 0.005))
    if piece == "pier":
        for at in (-PIER_POST_AT, PIER_POST_AT):
            posts.append((at, 0.0, END_POST, "end"))
        skip.append(((0.0, 0.0), PIER_POST_AT + END_POST / 2 + 0.01))
    if piece == "post":
        posts.append((0.0, 0.0, FENCE_POST, "fence"))
        skip.append(((0.0, 0.0), FENCE_POST / 2 + PICKET + 0.01))
    lines = paths(piece)
    if piece == "end":
        stop = posts[0][0]
        lines = [[Vector((-E, 0.0)), Vector((stop, 0.0))]]
    for line in lines:
        scale = u_scale(line) if piece in ARCS else 1.0
        for z, w, dep in rails:
            prof = [(w / 2, z + dep / 2, "r"), (-w / 2, z + dep / 2, "r"), (-w / 2, z - dep / 2, "r"),
                    (w / 2, z - dep / 2, "r")]
            solid.sweep(line, prof, profile_v(prof, iron + 0.02), scale, closed=True)
    for line in (paths(piece) if piece != "end" else lines):
        for p, t, _ in picket_spots(line, skip):
            light.bar(p.x, p.y, picket_from, picket_to, PICKET, iron + 0.12, turn=math.atan2(t.y, t.x))
    for x, y, s, kind in posts:
        if kind == "end":
            solid.bar(x, y, -0.02, spec["post_top"], s, iron + 0.02, top=True)
        else:
            fence_post(solid, x, y, -FENCE_POST_SINK, spec["post_top"], s, iron)
    return solid, light


def curb_piece(kind, piece, bands):
    prof = ROAD_CURB if kind.startswith("road") else EDGING
    band = bands["curb_road" if kind.startswith("road") else "curb_" + kind]
    rows = profile_v(prof, band[0])
    if kind == "road_red":
        # A row is where its stretch of the profile starts (`Builder.sweep`).
        v = bands["curb_road_red"][0]
        for j, (y, z, part) in enumerate(prof[:-1]):
            if part in RED_PARTS:
                rows[j] = v
                v += math.hypot(prof[j + 1][0] - y, prof[j + 1][1] - z)
    b = Builder()
    lines = paths(piece)
    zmap = None
    if piece == "cut":
        def zmap(p, s, y, z):  # noqa: F811 (a closure per piece)
            f = 1.0 - (1.0 - CURB_LOW) * min(max(min(s - 0.0, 2.0 - s) / 0.5, 0.0), 1.0)
            return z if z <= CURB_FLOW or y < -0.101 else CURB_FLOW + (z - CURB_FLOW) * f
        lines = [[Vector((-E + 0.25 * k, 0.0)) for k in range(9)]]
    if piece == "end" and kind.startswith("road"):
        def zmap(p, s, y, z):  # noqa: F811
            f = 1.0 - (1.0 - CURB_LOW) * min(max(s / 0.8, 0.0), 1.0)
            return z if z <= CURB_FLOW or y < -0.101 else CURB_FLOW + (z - CURB_FLOW) * f
        lines = [[Vector((-E + 0.1 * k, 0.0)) for k in range(9)]]
    elif piece == "end":
        lines = [[Vector((-E, 0.0)), Vector((0.0, 0.0))]]
    for line in lines:
        rings = b.sweep(line, prof, rows, u_scale(line) if piece in ARCS or piece.endswith("_in") else 1.0,
                        zmap=zmap)
        if piece == "end":
            b.cap(rings[-1], prof, band[0], True)
    return b


# --- the canvas's painting ------------------------------------------------------------


def blur(a, r, axis_wrap=1):
    """Box blur, radius r, twice: wrapping round the canvas's width, clamped
    down it."""
    for _ in range(2):
        for axis in (0, 1):
            m = np.moveaxis(a, axis, 0)
            pad = [(r + 1, r)] + [(0, 0)] * (m.ndim - 1)
            m = np.pad(m, pad, mode="wrap" if axis == axis_wrap else "edge")
            c = np.cumsum(m, axis=0)
            n = a.shape[axis]
            a = np.moveaxis((c[2 * r + 1:2 * r + 1 + n] - c[:n]) / (2 * r + 1), 0, axis)
    return a


def mottle(rng, h, w, r):
    a = blur(rng.standard_normal((h, w)).astype(np.float32), r)
    return a / max(float(a.std()), 1e-6)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def paint_concrete(rows, rng, z_top):
    """Poured concrete by height, as the bricks: mottled, a few bug holes, a
    tooled joint where pieces meet (u 0.5, the cells' edges, so none crosses a
    pier), grime up from the ground and soil under it."""
    z = z_top - (np.arange(rows, dtype=np.float32) + 0.5) / PX_M
    u = (np.arange(CANVAS_W, dtype=np.float32) + 0.5) / PX_M
    Z, U = np.meshgrid(z, u, indexing="ij")
    rgb = WALL_CONCRETE * (1.0 + 0.05 * mottle(rng, rows, CANVAS_W, 24) + 0.03 * mottle(rng, rows, CANVAS_W, 6)
                           + 0.02 * mottle(rng, rows, CANVAS_W, 1))[..., None]
    seeds = (rng.random((rows, CANVAS_W)) < 1.5e-4).astype(np.float32)  # about 40 a square metre
    holes = blur(seeds, 1) > 0.05
    joint = np.abs(U - 0.5) < 0.004
    rgb[holes] *= 0.72
    rgb[joint] *= 0.78
    grime = 1.0 - 0.2 * (1.0 - smooth(0.0, 0.2, Z)) * (0.8 + 0.2 * mottle(rng, rows, CANVAS_W, 6))
    rgb *= grime[..., None]
    below = smooth(0.0, -0.04, Z)[..., None]
    rgb = rgb * (1.0 - below) + SOIL * below
    bump = 0.55 + 0.02 * mottle(rng, rows, CANVAS_W, 1)
    bump[holes] -= 0.25
    bump[joint] = 0.25
    return rgb, bump, np.full((rows, CANVAS_W), 0.88, np.float32)


def paint_brick(rows, rng, z_top, town):
    """Bricks by height from `z_top` down: the park's (softened, a little
    darker toward the ground) or, `town`, the beach town's (sun, salt, sand
    and history)."""
    z = z_top - (np.arange(rows, dtype=np.float32) + 0.5) / PX_M
    u = (np.arange(CANVAS_W, dtype=np.float32) + 0.5) / PX_M
    Z, U = np.meshgrid(z, u, indexing="ij")
    course = np.floor(Z / COURSE + 1e-6).astype(int)
    zc = Z - course * COURSE
    uu = (U + np.where(course % 2 == 0, 0.0, BRICK / 2)) % 1.0
    idx = np.floor(uu / BRICK).astype(int)
    uc = uu - idx * BRICK
    d = np.minimum.reduce([zc, COURSE - JOINT - zc, uc - JOINT, BRICK - uc])  # the bed joint on top
    brick = d > 0
    table = rng.random((64, 4, 3)).astype(np.float32)
    pick = table[(course + 16) % 64, idx]
    tone = 0.95 + 0.1 * pick[..., 0]
    colour = BRICK_COLOUR * tone[..., None]
    dark = pick[..., 1] < 0.1
    light = pick[..., 1] > 0.88
    colour[dark] = BRICK_DARK * (0.95 + 0.1 * pick[dark][:, 2:3])
    colour[light] = BRICK_LIGHT * (0.96 + 0.08 * pick[light][:, 2:3])
    colour *= (1.0 + 0.04 * mottle(rng, rows, CANVAS_W, 10) + 0.03 * mottle(rng, rows, CANVAS_W, 1))[..., None]
    if not town:
        mortar = MORTAR_COLOUR * (1.0 + 0.05 * mottle(rng, rows, CANVAS_W, 2))[..., None]
        rgb = np.where(brick[..., None], colour, mortar)
        foot = FOOT_DARK * (1.0 - smooth(0.0, FOOT_UP, Z)) * (0.8 + 0.2 * mottle(rng, rows, CANVAS_W, 6))
        rgb *= (1.0 - foot)[..., None]
        below = smooth(0.0, -0.04, Z)[..., None]
        rgb = rgb * (1.0 - below) + SOIL * below
        bump = np.where(brick, 0.72 + 0.28 * smooth(0.0, 0.007, d), 0.18) + 0.03 * mottle(rng, rows, CANVAS_W, 1)
        return rgb, bump, np.where(brick, 0.86, 0.95)
    patch = (pick[..., 1] > 0.5) & (pick[..., 1] < 0.5 + PATCHES)
    colour[patch] = BRICK_PATCH * (0.96 + 0.08 * pick[patch][:, 2:3])
    # Sun: bleached in broad soft patches; a replacement brick has had less of it.
    bleach = (BLEACH * (1.0 + np.clip(mottle(rng, rows, CANVAS_W, 30), -1.0, 1.0)))[..., None]
    bleach = np.where(patch[..., None], bleach * 0.3, bleach)
    colour = colour * (1.0 - bleach) + SUN_BLEACH * bleach
    # History: corners chipped to the paler clay inside.
    chipped = brick & (d < 0.007) & (mottle(rng, rows, CANVAS_W, 1) > 1.5)
    colour[chipped] = CLAY * (0.95 + 0.1 * rng.random((int(chipped.sum()), 1)))
    pits = brick & (blur((rng.random((rows, CANVAS_W)) < 0.003).astype(np.float32), 1) > 0.04)
    colour[pits] *= 0.9
    # Mortar worn back and darker here, fresh-pointed and lighter there.
    wear = mottle(rng, rows, CANVAS_W, 8)
    fresh = mottle(rng, rows, CANVAS_W, 24) > 1.2
    mortar = MORTAR_COLOUR * (1.0 + 0.05 * mottle(rng, rows, CANVAS_W, 2))[..., None]
    mortar = np.where((wear > 0.9)[..., None], mortar * 0.86, mortar)
    mortar = np.where(fresh[..., None], FRESH_MORTAR, mortar)
    rgb = np.where(brick[..., None], colour, mortar)
    # The foot: salt bloom rising from it, sand on it, a little shade of dirt.
    salt = (0.4 * (1.0 - smooth(0.05, SALT_UP, Z)) * np.clip(mottle(rng, rows, CANVAS_W, 6) + 0.3, 0.0, 1.0))[..., None]
    rgb = rgb * (1.0 - salt) + SALT * salt
    sand = (0.4 * (1.0 - smooth(0.0, 0.1, Z)) * np.clip(0.7 + 0.3 * mottle(rng, rows, CANVAS_W, 4), 0.0, 1.0))[..., None]
    rgb = rgb * (1.0 - sand) + SAND * sand
    rgb *= (1.0 - 0.06 * (1.0 - smooth(0.0, 0.2, Z)))[..., None]
    below = smooth(0.0, -0.04, Z)[..., None]
    rgb = rgb * (1.0 - below) + SOIL * below
    bump = np.where(brick, 0.72 + 0.28 * smooth(0.0, 0.007, d), np.where(wear > 0.9, 0.08, 0.18))
    bump = bump + 0.03 * mottle(rng, rows, CANVAS_W, 1)
    bump[chipped] -= 0.12
    bump[pits] -= 0.12
    rough = np.where(brick, 0.88, 0.95)
    return rgb, bump, rough


def rain_streaks(rng, rows):
    """0 to 1 down a streak band, whose top is `LEDGE_IN` above a ledge's
    underside: streaks from a few columns, each its own length up to
    `STREAK_M`, fading to nothing by the band's foot; a faint wet line right
    under the ledge."""
    y = (np.arange(rows, dtype=np.float32) + 0.5) / PX_M - LEDGE_IN  # metres under the ledge
    # Each drip a streak about 4 cm wide at full strength, whatever its neighbours.
    impulse = np.zeros((1, CANVAS_W), np.float32)
    impulse[0, CANVAS_W // 2] = 1.0
    drips = blur((rng.random((1, CANVAS_W)) < RAIN_DRIPS).astype(np.float32), 5) / float(blur(impulse, 5).max())
    strength = np.clip(1.4 * drips, 0.0, 1.0) * (0.75 + 0.25 * blur(rng.random((1, CANVAS_W)).astype(np.float32), 4))
    reach = blur(rng.random((1, CANVAS_W)).astype(np.float32), 8)
    reach = (reach - reach.min()) / max(float(reach.max() - reach.min()), 1e-6)
    long = STREAK_M * (0.6 + 0.4 * reach)
    fall = np.clip(1.0 - np.maximum(y[:, None], 0.0) / long, 0.0, 1.0)
    wet = 0.35 * np.clip(1.0 - np.maximum(y, 0.0) / 0.025, 0.0, 1.0)[:, None]
    streaks = np.maximum(strength * fall, wet) * (0.85 + 0.15 * mottle(rng, rows, CANVAS_W, 1))
    return np.clip(streaks, 0.0, 1.0)


def drop_u(k):
    return 0.015 + k * 0.12


def paint_droppings(rows, rng):
    """`DROP_CELLS` splats side by side: a chalky white blob with a ragged
    edge, a grey-green core off its middle and a few spattered drops; nothing
    round them."""
    rgb = np.broadcast_to(DROP_WHITE, (rows, CANVAS_W, 3)).copy()
    alpha = np.zeros((rows, CANVAS_W), np.float32)
    bump = np.full((rows, CANVAS_W), 0.5, np.float32)
    ys = (np.arange(rows, dtype=np.float32) + 0.5) / PX_M
    xs = (np.arange(CANVAS_W, dtype=np.float32) + 0.5) / PX_M
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    for k in range(DROP_CELLS):
        cx, cy = drop_u(k) + DROP_CELL / 2, 0.01 + DROP_CELL / 2
        dx, dy = X - cx, Y - cy
        a = np.arctan2(dy, dx)
        r = np.hypot(dx, dy)
        wobble = sum(rng.uniform(0.0, 0.25) * np.cos(n * a + rng.uniform(0, 2 * np.pi)) for n in (2, 3, 5, 7))
        radius = rng.uniform(0.028, 0.034) * (1.0 + 0.6 * wobble)
        blob = np.clip((radius - r) * PX_M + 0.5, 0.0, 1.0)
        for _ in range(rng.integers(2, 6)):
            ang, dist = rng.uniform(0, 2 * np.pi), rng.uniform(0.04, 0.046)
            rr = rng.uniform(0.002, 0.005)
            blob = np.maximum(blob, np.clip((rr - np.hypot(dx - dist * np.cos(ang), dy - dist * np.sin(ang))) * PX_M
                                            + 0.5, 0.0, 1.0))
        ox, oy = rng.uniform(-0.006, 0.006, 2)
        core = np.clip(1.0 - np.hypot(dx - ox, dy - oy) / (radius * rng.uniform(0.35, 0.5)), 0.0, 1.0)[..., None]
        cell = (np.abs(dx) < DROP_CELL / 2) & (np.abs(dy) < DROP_CELL / 2)
        shade = (DROP_WHITE * (1.0 - 0.8 * core) + DROP_CORE * 0.8 * core)
        rgb = np.where(cell[..., None], shade, rgb)
        alpha = np.where(cell, blob, alpha)
        bump = np.where(cell, 0.5 + 0.2 * blob + 0.1 * core[..., 0], bump)
    return rgb, bump, np.full((rows, CANVAS_W), 0.6, np.float32), alpha


def paint_iron(rows, rng):
    rgb = np.broadcast_to(IRON_COLOUR, (rows, CANVAS_W, 3)).copy()
    rgb *= (1.0 + 0.08 * mottle(rng, rows, CANVAS_W, 3))[..., None]
    fade = FADE * np.clip(mottle(rng, rows, CANVAS_W, 12), 0.0, 1.5)[..., None] / 1.5
    rgb = rgb * (1.0 - fade) + IRON_FADED * fade
    rough = 0.45 + 0.5 * fade[..., 0]
    bump = np.full((rows, CANVAS_W), 0.5, np.float32)
    rust = blur((rng.random((rows, CANVAS_W)) < RUST_SPOTS).astype(np.float32), 1)
    halo = np.clip(blur(rust, 3) * 12.0, 0.0, 0.35)[..., None]
    rgb = rgb * (1.0 - halo) + RUST * halo
    spot = rust > 0.04
    rgb[spot] = RUST * (0.85 + 0.3 * rng.random((int(spot.sum()), 1)))
    rough[spot] = 0.9
    bump[spot] = 0.6
    chips = blur((rng.random((rows, CANVAS_W)) < CHIPS).astype(np.float32), 1) > 0.05
    rgb[chips] = PRIMER
    rough[chips] = 0.7
    bump[chips] = 0.38
    return rgb, bump, rough.astype(np.float32)


def paint_ledge(rows, rng, profile, seam):
    """Every wall's coping and caps down `profile`: one solid colour,
    weathered a tad, chipped along the nose and heel; the coping's `seam`s."""
    v = profile_v(profile, 0.0)
    y = (np.arange(rows, dtype=np.float32) + 0.5) / PX_M
    part = np.full(rows, "top", dtype=object)
    for (_, _, name), at in zip(profile, v):
        part[y >= at] = name
    face = (part == "face")[:, None]
    under = (part == "under")[:, None]
    nose = (v[1] + v[1 + NOSE_STEPS]) / 2  # the middle of the top edge's round
    heel = (v[-3] + v[-2]) / 2  # of the bottom edge's
    edge = np.maximum(np.exp(-((y - nose) / CHIP_REACH[0]) ** 2), np.exp(-((y - heel) / CHIP_REACH[1]) ** 2))[:, None]
    rgb = np.broadcast_to(LEDGE_CONCRETE, (rows, CANVAS_W, 3)).copy()
    rgb *= (1.0 + WEATHER * mottle(rng, rows, CANVAS_W, 20) + 0.4 * WEATHER * mottle(rng, rows, CANVAS_W, 4))[..., None]
    # Streaks down the face: a darkening that varies along the run and grows
    # toward the face's foot.
    runs = blur(rng.standard_normal((1, CANVAS_W)).astype(np.float32), 6)
    runs = np.clip(runs / max(float(runs.std()), 1e-6), 0.0, 2.0)
    down = np.clip((y - nose) / max(heel - nose, 1e-6), 0.0, 1.0)[:, None]
    rgb *= np.where(face, 1.0 - STREAK * 0.5 * runs * down, 1.0)[..., None]
    rgb *= np.where(under, UNDER_DARK, 1.0)[..., None]
    chips = (mottle(rng, rows, CANVAS_W, 2) + 0.6 * mottle(rng, rows, CANVAS_W, 6)) * edge > 1.35
    rgb[chips] *= CHIP_DARK
    bump = 0.5 + 0.06 * mottle(rng, rows, CANVAS_W, 1) * edge + 0.015 * mottle(rng, rows, CANVAS_W, 3)
    bump[chips] = 0.22
    if seam:
        u = (np.arange(CANVAS_W, dtype=np.float32) + 0.5) / PX_M
        at = np.broadcast_to((np.minimum(u, 1.0 - u) < SEAM_M / 2)[None, :], (rows, CANVAS_W))
        rgb[at] *= SEAM_DARK
        bump[at] = 0.2
    return rgb, bump, np.full((rows, CANVAS_W), 0.8, np.float32)


def paint_red_curb(rows, rng):
    """The red curb's top and face: the paint, chipped here and there to the
    concrete."""
    concrete = CONCRETE * (1.0 + 0.045 * mottle(rng, rows, CANVAS_W, 12)
                           + 0.03 * mottle(rng, rows, CANVAS_W, 2))[..., None]
    worn = mottle(rng, rows, CANVAS_W, 1) > 2.6  # a few small chips
    paint = RED_PAINT * (1.0 + 0.05 * mottle(rng, rows, CANVAS_W, 8))[..., None]
    rgb = np.where(worn[..., None], concrete, paint)
    rough = np.where(worn, 0.86, 0.6).astype(np.float32)
    bump = 0.5 + 0.035 * mottle(rng, rows, CANVAS_W, 1)
    return rgb, bump, rough


def paint_curb(rows, rng, profile):
    v = profile_v(profile, 0.0)
    y = (np.arange(rows, dtype=np.float32) + 0.5) / PX_M
    part = np.full(rows, profile[0][2], dtype=object)
    z_at = np.interp(y, v, [p[1] for p in profile])
    for (_, _, p), s in zip(profile, v):
        part[y >= s] = p
    rgb = np.broadcast_to(CONCRETE, (rows, CANVAS_W, 3)).copy()
    rgb *= (1.0 + 0.045 * mottle(rng, rows, CANVAS_W, 12) + 0.03 * mottle(rng, rows, CANVAS_W, 2))[..., None]
    gutter = np.isin(part, ("gutter",))[:, None]
    rgb = np.where(gutter[..., None], rgb * (GUTTER / CONCRETE), rgb)
    top = (part == "top")[:, None]
    rgb *= np.where(top, 1.04, 1.0)[..., None]
    # Dirt: along the gutter's flow line and up the curb's foot.
    if "gutter" in part:
        g0 = v[[p[2] for p in profile].index("gutter")]
        flow = np.exp(-((y - g0) / 0.05) ** 2)[:, None] * (0.8 + 0.4 * np.clip(mottle(rng, rows, CANVAS_W, 8), -1, 1))
        rgb *= (1.0 - 0.25 * np.clip(flow, 0.0, 1.0))[..., None]
    rough = np.full((rows, CANVAS_W), 0.86, np.float32)
    below = smooth(0.0, -0.03, z_at)[:, None, None]
    rgb = rgb * (1.0 - below) + SOIL * below
    bump = 0.5 + 0.035 * mottle(rng, rows, CANVAS_W, 1)
    pores = rng.random((rows, CANVAS_W)) < 0.01
    bump[pores] -= 0.15
    return rgb, bump, rough


def paint(bands, folder):
    """The canvas, its ORM, bump and normal, and guide; returns (colour, orm,
    normal) images."""
    rng = np.random.default_rng(SEED)
    rgb = np.zeros((CANVAS_H, CANVAS_W, 3), np.float32)
    bump = np.full((CANVAS_H, CANVAS_W), 0.5, np.float32)
    rough = np.full((CANVAS_H, CANVAS_W), 0.85, np.float32)
    known = np.zeros((CANVAS_H, CANVAS_W), bool)
    alpha = np.ones((CANVAS_H, CANVAS_W), np.float32)
    painted = {}
    for name, (top, bottom) in bands.items():
        y0 = int(round(top * PX_M))
        rows = int(round(bottom * PX_M)) - y0
        if name in ("brick", "town_brick"):
            c, h, r = paint_brick(rows, rng, Z_BODY_TOP, town=name == "town_brick")
            painted[name] = (c, h, r)
        elif name == "concrete":
            c, h, r = paint_concrete(rows, rng, Z_BODY_TOP)
            painted[name] = (c, h, r)
        elif "_streak_" in name:
            # The body band's own pixels at the height of a ledge of this
            # parity, so the streak band meets the body band there without a
            # seam; then the streaks.
            body, parity = name.split("_streak_")
            i0 = int(round((Z_BODY_TOP - (UNDERSIDES[parity] + LEDGE_IN)) * PX_M))
            c, h, r = (a[i0:i0 + rows].copy() for a in painted[body])
            wet = rain_streaks(rng, rows)[..., None]
            grey = c.mean(axis=2, keepdims=True)
            c = (c * (1.0 - 0.3 * wet) + grey * 0.3 * wet) * (1.0 - RAIN_DARK * wet)
        elif name == "droppings":
            c, h, r, a = paint_droppings(rows, rng)
            alpha[y0:y0 + rows] = a
        elif name in ("coping", "cap"):
            wall = WALLS["garden"]
            profile = (coping_profile(COPING_W, wall["top"], COPING_T, COPING_WASH, (COPING_W - WALL_W) / 2)
                       if name == "coping" else
                       coping_profile(CAP_W, wall["pier_top"] + CAP_T, CAP_T, CAP_WASH, (CAP_W - PIER_W) / 2))
            c, h, r = paint_ledge(rows, rng, profile, seam=name == "coping")
        elif name == "iron":
            c, h, r = paint_iron(rows, rng)
        elif name == "curb_road_red":
            c, h, r = paint_red_curb(rows, rng)
        else:
            c, h, r = paint_curb(rows, rng, ROAD_CURB if name == "curb_road" else EDGING)
        rgb[y0:y0 + rows] = c
        bump[y0:y0 + rows] = h
        rough[y0:y0 + rows] = r
        known[y0:y0 + rows] = True
    rgb = grow(rgb, known, 8)

    def write(path, pixels, channels_alpha=None, colour_space="sRGB"):
        h, w = pixels.shape[:2]
        name = os.path.splitext(os.path.basename(path))[0]
        old = bpy.data.images.get(name)
        if old is not None:
            bpy.data.images.remove(old)
        img = bpy.data.images.new(name, w, h, alpha=channels_alpha is not None)
        img.colorspace_settings.name = colour_space
        px = np.ones((h, w, 4), dtype=np.float32)
        px[..., :3] = pixels
        if channels_alpha is not None:
            px[..., 3] = channels_alpha
        img.pixels.foreach_set(px[::-1].ravel())  # Blender's rows run from the bottom
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        img.filepath = bpy.path.relpath(path)
        img.source = "FILE"
        img.reload()
        return img

    os.makedirs(folder, exist_ok=True)
    colour = write(os.path.join(folder, f"{NAME}_colour.png"), srgb(rgb), alpha)
    orm = np.zeros((CANVAS_H // 4, CANVAS_W // 4, 3), np.float32)
    orm[..., 0] = 1.0
    orm[..., 1] = rough.reshape(CANVAS_H // 4, 4, CANVAS_W // 4, 4).mean(axis=(1, 3))
    orm_img = write(os.path.join(folder, f"{NAME}_orm.png"), orm, None, "Non-Color")
    bump = np.clip(bump, 0.0, 1.0)
    bpy.data.images.remove(write(os.path.join(folder, f"{NAME}_bump.png"), np.repeat(bump[..., None], 3, 2), None,
                                 "Non-Color"))
    normal = normal_from_height(bump, DEPTH_PX.get(NAME, 3.0), NAME in WRAP_U)
    normal_img = write(os.path.join(folder, f"{NAME}_normal.png"), normal, None, "Non-Color")
    bpy.data.images.remove(write(os.path.join(folder, f"{NAME}_cutout.png"), np.repeat(alpha[..., None], 3, 2), None,
                                 "Non-Color"))
    guide = np.zeros((CANVAS_H, CANVAS_W, 4), np.float32)
    for top, bottom in bands.values():
        for y in (top, bottom):
            guide[int(round(y * PX_M)):int(round(y * PX_M)) + 2] = (1, 1, 1, 1)
    z = 0.0  # the ground on the brick band
    guide[int(round(brick_v(bands, z) * PX_M)), ::3] = (1, 1, 0, 1)
    bpy.data.images.remove(write(os.path.join(folder, f"{NAME}_uv_guide.png"), guide[..., :3], guide[..., 3]))
    return colour, orm_img, normal_img


def scatter_droppings(bvh, lines, top, rate, seed, band_top, across=0.0, square=None, rail=False, clear=0.0):
    """A scattering of bird droppings lying on `bvh` where it is within 5 mm
    of `top` or higher: along `lines` (`across` either side of them), or in
    `square` (half a cap's top), about `rate` a metre (or a cap); each a card
    of 3 by 3 points, every point dropped onto the surface and lifted
    `DROP_LIFT`, so it follows the coping's wash; none within `clear` of x = 0
    (inside a pier). A Builder, or None when none fell."""
    rng = np.random.default_rng(seed)
    b = Builder()
    frames = [path_frames(line) for line in lines]
    total = sum(f[-1][2] for f in frames)
    count = rng.poisson(rate * (total if lines else 1.0))
    placed = []
    for _ in range(60):
        if len(placed) >= count:
            break
        if square is not None:
            p = Vector((rng.uniform(-square, square), rng.uniform(-square, square)))
            turn = rng.uniform(0, 2 * math.pi)
        else:
            pick = rng.uniform(0, total)
            for f in frames:
                if pick <= f[-1][2]:
                    break
                pick -= f[-1][2]
            for (p0, _, s0), (p1, _, s1) in zip(f, f[1:]):
                if s0 <= pick <= s1:
                    t = (p1 - p0).normalized()
                    p = p0 + (p1 - p0) * ((pick - s0) / max(s1 - s0, 1e-9)) + Vector((-t.y, t.x)) * rng.uniform(-across, across)
                    turn = math.atan2(t.y, t.x) + (rng.uniform(-0.3, 0.3) if rail else rng.uniform(0, 2 * math.pi))
                    break
        if abs(p.x) < clear or any((p - q).length < DROP_APART for q in placed):
            continue
        size = rng.uniform(*DROP_SIZE)
        long, wide = (size, min(size, DROP_RAIL_W)) if rail else (size, size)
        e1, e2 = Vector((math.cos(turn), math.sin(turn))), Vector((-math.sin(turn), math.cos(turn)))
        grid = {}
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                q = p + e1 * (i * long / 2) + e2 * (j * wide / 2)
                hit = bvh.ray_cast(Vector((q.x, q.y, top + 1.0)), Vector((0.0, 0.0, -1.0)), 2.0)
                if hit[0] is None or hit[0].z < top - 0.005:
                    grid = None
                    break
                grid[i, j] = Vector((q.x, q.y, hit[0].z + DROP_LIFT))
            if grid is None:
                break
        if grid is None:
            continue
        k = int(rng.integers(DROP_CELLS))
        flip = bool(rng.integers(2))
        verts = {ij: b.bm.verts.new(co) for ij, co in grid.items()}

        def uv(i, j):
            fu = (i + 1) / 2
            return (drop_u(k) + DROP_CELL * ((1 - fu) if flip else fu), v_of(band_top + 0.01 + DROP_CELL * (1 - (j + 1) / 2)))

        for i in (-1, 0):
            for j in (-1, 0):
                corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                b.face([(verts[c], uv(*c)) for c in corners])
        placed.append(p)
    return b if placed else None


def drop_set(x, y):
    """Which scattering of droppings a placement at grid square (x, y) shows:
    the wrapper's rule, on Godot's (x, z), z = -y."""
    return DROP_SETS[(round(x) * 7 - round(y) * 13) % len(DROP_SETS)]


# --- the file -----------------------------------------------------------------


def child(parent, name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if coll.name not in parent.children:
        parent.children.link(coll)
    return coll


def shape_hash(me):
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    return hashlib.sha1(np.round(co, 5).tobytes()).hexdigest()[:16]


def kinds():
    """(kind, size, pieces): every kind the kit builds."""
    out = [(kind, size, WALL_PIECES) for kind in BODIES for size in WALLS]
    after = RAILING_PIECES.index("end") + 1
    out += [("railing", size, RAILING_PIECES[:after] + (("pier",) if size == "wall" else ("post",))
             + RAILING_PIECES[after:]) for size in RAILINGS]
    out += [("curb", k, CURB_PIECES["road" if k.startswith("road") else k]) for k in ("road", "road_red", "edging")]
    return out


# The sample street (`authored/sample_street`), a street in the beach town
# after her photograph: a garden wall (the town's brick) along the back of a sidewalk with piers every four metres, the railing
# on it, a corner turning in beside a front walk; past the walk to the west,
# the same wall in concrete; the parkway and the curb and gutter at the street,
# a driveway cut, and a red stretch. (kind, piece, x, y, turn in quarter turns
# anticlockwise, z).
def sample_street():
    wall, top = "town_wall_garden", WALLS["garden"]["top"]
    out = [(wall, "end", -6, 0, 2, 0.0), (wall, "straight_4", -5, 0, 0, 0.0), (wall, "straight_4", -1, 0, 0, 0.0),
           (wall, "straight_4", 3, 0, 0, 0.0), (wall, "straight_2", 7, 0, 0, 0.0), (wall, "straight", 9, 0, 0, 0.0),
           (wall, "corner", 10, 0, 0, 0.0), (wall, "straight_2", 10, 1, 1, 0.0), (wall, "end", 10, 3, 1, 0.0)]
    out += [(wall, "pier", x, y, 0, 0.0) for x, y in ((-6, 0), (-2, 0), (2, 0), (6, 0), (10, 0), (10, 3))]
    rail = "railing_wall"
    out += [(rail, "end", -6, 0, 2, top), (rail, "corner", 10, 0, 0, top), (rail, "straight_2", 10, 1, 1, top),
            (rail, "end", 10, 3, 1, top)]
    for x in range(-5, 10):
        piece = "pier" if x in (-2, 2, 6) else "straight"
        out.append((rail, piece, x, 0, 0, top))
    concrete = "concrete_wall_garden"
    out += [(concrete, "end", -17, 0, 2, 0.0), (concrete, "straight_4", -16, 0, 0, 0.0),
            (concrete, "straight_2", -12, 0, 0, 0.0), (concrete, "straight", -10, 0, 0, 0.0),
            (concrete, "end", -9, 0, 0, 0.0)]
    out += [(concrete, "pier", x, 0, 0, 0.0) for x in (-17, -13, -9)]
    out += [(rail, "end", -17, 0, 2, top), (rail, "end", -9, 0, 0, top)]
    out += [(rail, "pier" if x == -13 else "straight", x, 0, 0, top) for x in range(-16, -9)]
    curb = "curb_road"
    y = -4
    xs = list(range(-14, 15))
    for x in xs:
        if x == 3:
            out.append((curb, "cut", x, y, 0, 0.0))
        elif x == 4:
            continue
        else:
            out.append(("curb_road_red" if 8 <= x <= 11 else curb, "straight", x, y, 0, 0.0))
    # A bed in the parkway, edged, round a tree to come.
    out += [("curb_edging", "corner", -9, -3, 3, 0.0), ("curb_edging", "straight", -8, -3, 0, 0.0),
            ("curb_edging", "corner", -7, -3, 0, 0.0)]
    return out


def place_copies(coll, placements, parts, offset=(0.0, 0.0, 0.0)):
    """Linked duplicates of each placement's parts into `coll`."""
    made = []
    for kind, piece, x, y, turn, z in placements:
        for src in parts[f"{kind}_{piece}"]:
            group = str(src.get("kyt_merge_group", ""))
            if group.startswith("droppings_") and group != f"droppings_{drop_set(x, y)}":
                continue
            dup = src.copy()  # shares its mesh: reshape the piece and every copy follows
            dup.location = (x + offset[0], y + offset[1], z + offset[2])
            dup.rotation_euler = (0.0, 0.0, turn * math.pi / 2)
            for key in ("kyt_variant", "kyt_merge_group", "kyt_collision", "kyt_hardscape"):
                if key in dup:
                    del dup[key]
            dup["kyt_hardscape"] = True
            coll.objects.link(dup)
            made.append(dup)
    return made


def build(replace):
    root = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), os.pardir, os.pardir, os.pardir))
    export = bpy.data.collections["export"]
    authored = bpy.data.collections["authored"]
    edited = [o.name for o in export.all_objects
              if o.type == "MESH" and o.data.get("kyt_hardscape_hash") not in (None, shape_hash(o.data))]
    if edited and not replace:
        raise SystemExit("hardscape_kit: these pieces were reshaped since the last build and would be lost: "
                         + ", ".join(sorted(edited)) + ". Move them out of 'export' or run with --replace.")
    for o in [o for o in list(export.all_objects) + list(authored.all_objects) if o.get("kyt_hardscape")]:
        bpy.data.objects.remove(o, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    # The ground the kit stands in (Check's `ground_line`): walls, curbs and
    # fence posts go below it on purpose.
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        bpy.data.collections["reference"].objects.link(marker)

    bands = layout()
    colour, orm, normal = paint(bands, os.path.join(root, "assets", "source", "textures", NAME))
    material = one_material(NAME, colour, orm, "UVMap", clip=True, normal=normal)

    parts, triangles = {}, {}

    def add(coll, key, name, builder, collide, group=None):
        me = builder.mesh(name, material)
        if not len(me.polygons):
            bpy.data.meshes.remove(me)
            return None, 0
        me["kyt_hardscape_hash"] = shape_hash(me)
        obj = bpy.data.objects.new(name, me)
        obj["kyt_variant"] = key
        obj["kyt_hardscape"] = True
        if group:
            obj["kyt_merge_group"] = group
        if not collide:
            obj["kyt_collision"] = "none"
        coll.objects.link(obj)
        me.calc_loop_triangles()
        return obj, len(me.loop_triangles)

    for kind, size, pieces in kinds():
        group = f"{kind}_{size}"
        coll = child(export, group)
        for piece in pieces:
            key = f"{group}_{piece}"
            objs, tris = [], 0
            drops = []
            band_top = bands["droppings"][0]
            if kind in BODIES:
                wall = wall_piece(size, piece, bands, BODIES[kind])
                bvh = BVHTree.FromBMesh(wall.bm)
                spec = WALLS[size]
                for tag in DROP_SETS:
                    seed = zlib.crc32(f"{size}_{piece}_{tag}".encode())  # the same on brick and concrete
                    if piece == "pier":
                        drops.append((tag, scatter_droppings(bvh, [], spec["pier_top"] + CAP_T, DROP_PIER, seed,
                                                             band_top, square=CAP_W / 2 - 0.05)))
                    else:
                        drops.append((tag, scatter_droppings(bvh, paths(piece), spec["top"], DROP_RATE["wall"], seed,
                                                             band_top, across=COPING_W / 2 - 0.05)))
                built = [(key, wall, True)]
            elif kind == "railing":
                solid, light = railing_piece(size, piece, bands)
                bvh = BVHTree.FromBMesh(solid.bm)
                z, _, depth = RAILINGS[size]["rails"][-1]
                lines = paths(piece)
                if piece == "end":
                    lines = [[Vector((-E, 0.0)), Vector((-PIER_POST_AT if size == "wall" else 0.0, 0.0))]]
                for tag in DROP_SETS:
                    seed = zlib.crc32(f"railing_{size}_{piece}_{tag}".encode())
                    drops.append((tag, scatter_droppings(bvh, lines, z + depth / 2, DROP_RATE["railing"], seed,
                                                         band_top, rail=True,
                                                         clear=PIER_W / 2 + 0.05 if piece == "pier" else 0.0)))
                built = [(key, solid, True), (f"{key}_pickets", light, False)]
            else:
                built = [(key, curb_piece(size, piece, bands), False)]
            for name, builder, collide in built:
                obj, n = add(coll, key, name, builder, collide)
                if obj is not None:
                    objs.append(obj)
                    tris += n
            for tag, builder in drops:
                if builder is not None:
                    obj, _ = add(coll, key, f"{key}_droppings_{tag}", builder, False, f"droppings_{tag}")
                    if obj is not None:
                        objs.append(obj)
            parts[key] = objs
            triangles[key] = tris

    street = child(authored, "sample_street")
    for o in place_copies(street, sample_street(), parts):
        o["kyt_hardscape"] = True
    layer = bpy.context.view_layer.layer_collection.children.get("export")
    if layer is not None:
        layer.hide_viewport = True  # every piece stands at the origin; the sample shows them laid out
    bpy.context.scene["kyt_hardscape_bands"] = {k: list(v) for k, v in bands.items()}

    for kind, size, pieces in kinds():
        group = f"{kind}_{size}"
        print(f"hardscape_kit: {group} triangles: " + ", ".join(f"{p} {triangles[f'{group}_{p}']}" for p in pieces))
    print(f"hardscape_kit: canvas {CANVAS_W}x{CANVAS_H} ({PX_M} px/m, repeating every metre); bands "
          + ", ".join(f"{k} {b - t:.2f} m" for k, (t, b) in bands.items()))
    return parts


# --- review renders -------------------------------------------------------------


def render(folder):
    """The sample street from her photograph's standpoint, from above, the
    railing and a pier close and the curb; the kinds beside a person; a sheet
    of each kind's pieces, labelled; into `folder`."""
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    parts = {}
    for o in bpy.data.collections["export"].all_objects:
        if o.get("kyt_variant"):
            parts.setdefault(o["kyt_variant"], []).append(o)
    bpy.data.collections["authored"].hide_render = False
    bpy.data.collections["export"].hide_render = True
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)

    def colour_material(name, rgb, rough=0.9):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        return mat

    def slab(name, x0, x1, y0, y1, z0, z1, rgb):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        o = bpy.context.active_object
        o.name = name
        o.scale = (x1 - x0, y1 - y0, z1 - z0)
        o.data.materials.append(colour_material(f"_{name}", rgb))
        for coll in o.users_collection:
            coll.objects.unlink(o)
        stage.objects.link(o)
        return o

    # The street: road, parkway, sidewalk (her photograph's, wide), and the
    # garden raised behind the wall, its soil a little under the coping.
    top = WALLS["garden"]["top"]
    slab("road", -40, 40, -40, -4.48, -0.2, 0.0, tuple(srgb_bytes(62, 62, 66)))
    slab("parkway", -40, 40, -3.93, -2.6, -0.2, 0.004, tuple(srgb_bytes(96, 120, 60)))
    slab("sidewalk", -40, 40, -2.6, -0.12, -0.2, 0.006, tuple(srgb_bytes(184, 180, 172)))
    slab("garden", -6.1, 9.9, 0.1, 3.1, -0.2, top - 0.15, tuple(srgb_bytes(66, 96, 44)))
    slab("garden_west", -17.1, -8.9, 0.1, 3.1, -0.2, top - 0.15, tuple(srgb_bytes(66, 96, 44)))
    slab("parkway_bed", -9.1, -6.9, -3.9, -2.9, -0.2, 0.03, tuple(srgb_bytes(88, 70, 52)))
    slab("ground", -300, 300, -300, 300, -0.25, -0.01, tuple(srgb_bytes(96, 120, 60)))
    try:
        path = os.path.join(os.path.dirname(bpy.data.filepath), "box_shrub.blend")
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.collections = ["export"]
        shrubs = [o for o in dst.collections[0].all_objects if o.type == "MESH"]
        for k, (x, y) in enumerate(((-4.5, 1.4), (-3.2, 2.4), (0.6, 1.2), (3.8, 2.2), (7.5, 1.5), (-1.0, 2.0))):
            for s in shrubs:
                inst = bpy.data.objects.new(f"_shrub_{k}_{s.name}", s.data)
                inst.location = (x, y, top - 0.15)
                inst.rotation_euler = (0, 0, k * 1.3)
                inst.scale = (1.3, 1.3, 1.3)
                stage.objects.link(inst)
    except (OSError, RuntimeError, IndexError) as err:
        print(f"hardscape_kit: no box shrubs in the garden ({err})")
    person_mat = colour_material("_person", (0.55, 0.42, 0.6))
    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.62, -0.55, 0.56)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False

    def label(text, x, y, size=0.35, z=-0.009):
        curve = bpy.data.curves.new(f"_label_{text}", "FONT")
        curve.body = text
        curve.size = size
        curve.align_x = "CENTER"
        obj = bpy.data.objects.new(f"_label_{text}", curve)
        obj.location = (x, y, z)
        curve.materials.append(colour_material("_ink", (0.02, 0.02, 0.02)))
        stage.objects.link(obj)

    def person(x, y, z=0.0):
        """A person 1.75 m tall, for scale: a capsule."""
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.31, location=(x, y, z + 0.22 + 1.31 / 2))
        body = bpy.context.active_object
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(x, y, z + 1.53))
        head = bpy.context.active_object
        for o in (body, head):
            o.data.materials.append(person_mat)
            for coll in o.users_collection:
                coll.objects.unlink(o)
            stage.objects.link(o)

    def shoot(name, eye, target, lens=35, size=(1600, 1000)):
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"hardscape_kit: rendered {scene.render.filepath}")

    person(-3.0, -1.9)
    shoot("street_photo_view", (-8.8, -1.3, 1.55), (3.0, 0.1, 0.55), lens=24)
    shoot("street_overview", (-15.0, -17.0, 9.5), (-3.0, -1.2, 0.3), lens=26)
    shoot("railing_close", (-3.6, -1.35, 1.35), (-3.9, 0.3, 0.85), lens=38)
    shoot("pier_close", (-0.4, -1.8, 1.45), (-2.0, 0.0, 0.95), lens=34)
    shoot("curb_close", (1.6, -2.6, 1.0), (3.6, -4.2, 0.02), lens=32)
    shoot("concrete_view", (-5.8, -1.5, 1.55), (-15.0, 0.1, 0.55), lens=26)
    shoot("concrete_pier_close", (-11.4, -1.8, 1.45), (-13.0, 0.0, 0.95), lens=34)

    # The kinds side by side with a person between, off to the side of the
    # street: the walls and fence, then the curbs.
    ox = 200.0
    beside = [("wall_seat", "end", 0, 0, 2, 0.0), ("wall_seat", "straight_2", 1, 0, 0, 0.0),
              ("wall_seat", "end", 3, 0, 0, 0.0), ("wall_seat", "pier", 3, 0, 0, 0.0),
              ("wall_garden", "end", 6, 0, 2, 0.0), ("wall_garden", "straight_2", 7, 0, 0, 0.0),
              ("wall_garden", "end", 9, 0, 0, 0.0), ("wall_garden", "pier", 6, 0, 0, 0.0),
              ("wall_garden", "pier", 9, 0, 0, 0.0),
              ("railing_wall", "end", 6, 0, 2, top), ("railing_wall", "straight", 7, 0, 0, top),
              ("railing_wall", "straight", 8, 0, 0, top), ("railing_wall", "end", 9, 0, 0, top),
              ("railing_fence", "end", 12, 0, 2, 0.0), ("railing_fence", "straight", 13, 0, 0, 0.0),
              ("railing_fence", "straight", 14, 0, 0, 0.0), ("railing_fence", "post", 15, 0, 0, 0.0),
              ("railing_fence", "straight", 16, 0, 0, 0.0), ("railing_fence", "end", 17, 0, 0, 0.0),
              ("curb_road", "straight_4", 50, 20, 0, 0.0), ("curb_road", "cut", 54, 20, 0, 0.0),
              ("curb_road_red", "straight_2", 56, 20, 0, 0.0), ("curb_road", "end", 58, 20, 0, 0.0),
              ("curb_edging", "end", 51, 22, 2, 0.0), ("curb_edging", "straight_4", 52, 22, 0, 0.0),
              ("curb_edging", "straight", 56, 22, 0, 0.0), ("curb_edging", "end", 57, 22, 0, 0.0)]
    place_copies(stage, beside, parts, (ox, 0.0, 0.0))
    for x, text in ((1.5, "wall_seat (park)"), (7.5, "wall_garden (park) + railing_wall"), (14.5, "railing_fence")):
        label(text, ox + x, -1.6, 0.34)
    for x, y, text in ((53.5, 18.7, "curb_road, cut, red, end"), (54.5, 23.2, "curb_edging")):
        label(text, ox + x, y, 0.3)
    for x in (4.5, 10.5):
        person(ox + x, -0.3)
    person(ox + 60.0, 21.0)
    shoot("kinds_walls", (ox + 8.5, -12.5, 2.2), (ox + 8.5, 0.0, 0.6), lens=24)
    shoot("park_pier_close", (ox + 10.6, -1.8, 1.45), (ox + 9.0, 0.0, 0.95), lens=34)
    shoot("kinds_curbs", (ox + 54.5, 14.2, 2.4), (ox + 54.5, 21.0, 0.0), lens=26)
    concrete = [("concrete_wall_seat", "end", -30, 0, 2, 0.0), ("concrete_wall_seat", "straight_2", -29, 0, 0, 0.0),
                ("concrete_wall_seat", "end", -27, 0, 0, 0.0), ("concrete_wall_seat", "pier", -27, 0, 0, 0.0),
                ("concrete_wall_garden", "end", -24, 0, 2, 0.0), ("concrete_wall_garden", "straight_2", -23, 0, 0, 0.0),
                ("concrete_wall_garden", "end", -21, 0, 0, 0.0), ("concrete_wall_garden", "pier", -24, 0, 0, 0.0),
                ("concrete_wall_garden", "pier", -21, 0, 0, 0.0),
                ("railing_wall", "end", -24, 0, 2, top), ("railing_wall", "straight", -23, 0, 0, top),
                ("railing_wall", "straight", -22, 0, 0, top), ("railing_wall", "end", -21, 0, 0, top)]
    place_copies(stage, concrete, parts, (ox, 0.0, 0.0))
    for x, text in ((-28.5, "concrete_wall_seat"), (-22.5, "concrete_wall_garden + railing_wall")):
        label(text, ox + x, -1.6, 0.34)
    person(ox - 25.5, -0.3)
    shoot("kinds_concrete", (ox - 25.5, -9.0, 2.0), (ox - 25.5, 0.0, 0.6), lens=24)

    # Each kind's pieces, labelled, four to a row.
    span = {"straight_2": 2, "straight_4": 4, "curve": 2, "curve_large": 3, "curve_in": 2, "curve_large_in": 3,
            "cut": 2}
    for i, (kind, size, pieces) in enumerate(kinds()):
        group = f"{kind}_{size}"
        base_x, oy = i * 60.0, -200.0
        rows = [pieces[k:k + 4] for k in range(0, len(pieces), 4)]
        z = top if group == "railing_wall" else 0.0
        for r, row in enumerate(rows):
            x = base_x
            for piece in row:
                wide = span.get(piece, 1)
                y = oy - r * 6.5
                place_copies(stage, [(group, piece, x + 0.5, y, 0, z)], parts)
                if group == "railing_wall":
                    under = "straight" if piece == "pier" else piece
                    place_copies(stage, [("wall_garden", under, x + 0.5, y, 0, 0.0)]
                                 + ([("wall_garden", "pier", x + 0.5, y, 0, 0.0)] if piece == "pier" else []), parts)
                label(piece, x + wide / 2, y - 1.0, 0.34)
                x += wide + 1.8
        label(group, base_x + 6.5, oy + 3.6, 0.6)
        shoot(f"pieces_{group}", (base_x + 6.8, oy - 19.0, 10.0), (base_x + 6.8, oy - 6.3, 0.0), lens=30,
              size=(1800, 1300))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--render" in argv:
        render(os.path.abspath(argv[argv.index("--render") + 1]))
        return
    build("--replace" in argv)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


if __name__ == "__main__":
    main()
