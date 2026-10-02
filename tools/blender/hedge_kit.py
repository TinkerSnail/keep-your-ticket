"""The boxwood hedge kit: clipped hedges in three heights, in pieces that snap
together on a one-metre grid (2026-09-29).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/boxwood_hedge.blend --python tools/blender/hedge_kit.py -- [--replace] [--save]
    ... --python tools/blender/hedge_kit.py -- --render <folder>

After her photograph of a boxwood knot garden
(`documentation/reference/boxwood_hedge/knot_garden_parterre.webp`): "lets
make some boxy hedges so we can make shapes like this", then "this will be the
standard height but lets also have waist height and a taller than people
version one for privacy".

A hedge is the shrubs' greenery on a long base (`prop-pipeline.md`, "Bushes and
hedges share one greenery"): a body of dense leaves in shade and, over it, a
lid of the box shrub's leaves, almost flat: a flat top that only rolls over its
edge, its hem the leaves' own tips just below the top and 20 mm past the
body's side (her "the top tier is still to long, it needs to be almost flat on
top"; it had hung a skirt a third of the way down the knee-high side). Tiers of
leaves down the taller two's sides were tried and taken off (her "the tiers are
good for visual interest but also bad because they are so linear they create
their own horizontal line. can we put it only on the very top of the hedges
like a lid?"); loose clusters of leaves over the sides break them up instead
(her "then add random clusters of leaves"), small fans of three leaves lying
almost flat on the sides and a few on the lid, in darker shades of the hedge's
green (`CLUSTER_*`, `CLUMP_*`); and the sides end at the soil in a hem of leaf
tips like the lid's (her "can the bottom edges be shaped like the edge of the
lid instead of flat").

The kit, in each of `HEIGHTS` (each piece a `kyt_variant`, `<height>_<piece>`).
Every piece is one grid cell or a few, its origin in the middle of its first
cell, the hedge running along the cells' middles, so Godot's one-metre snap
lays pieces together and a quarter turn fits them any way round. Where a piece
meets the next, both are open and share one cross-section.

- `straight`, `straight_2`, `straight_4`: one, two or four metres, west to east.
- `corner`: west to north, a square corner. `tee`: west to east with a branch
  north. `cross`: all four ways.
- `end`: from the west, closed a half-width past the middle. `post`: a square
  block on its own.
- `bend`: west to north round a half-metre radius, in one cell, a rounded
  corner. `curve`: a quarter circle of 1.5 m radius over two cells by two;
  four make a ring 3 m across. `curve_large`: 2.5 m over three by three; four
  make a ring 5 m across.

Each piece is five objects in `export/<height>`: `<height>_<piece>`, the
body, which collides; `<height>_<piece>_hat`, the lid (merge group `hat`); and
`<height>_<piece>_clusters_a`, `_b`, `_c`, three scatterings of leaf clusters
(merge groups `clusters_a` to `_c`), none of which collide. Send gives
`boxwood_hedge_<height>_<piece>-col`, `..._hat` and `..._clusters_<set>`; the
wrapper `scenes/world/landscape_kit/boxwood_hedge.tscn` shows the piece its
inspector names with one scattering, chosen by the grid square it stands on,
so a run of pieces doesn't repeat its clusters every metre. They all stand at
the origin, so the `export` collection is hidden in the viewport;
`authored/sample_parterre` lays them out as a garden from linked duplicates,
so a piece reshaped in `export` is reshaped there too.

The canvas (`assets/source/textures/boxwood_hedge/`) is one metre wide and
repeats along every hedge: a piece's texture runs along it by the grid (on a
straight the metre it stands in, on a curve a whole number of metres), so the
leaves meet the next piece's. Down it are three bands: the lids', read from
the ridge out and down to the hem, the hem at the band's foot for every height;
a row of three painted leaf clusters, one to a card; the bodies', from the
ground up, their foot a hem of leaf tips on the soil as the lid's is (her "can
the bottom edges be shaped like the edge of the lid instead of flat"). Leaves
point away from the ridge and down, each row laid over the
one below like shingles.

A piece reshaped by hand is kept: a run refuses while any piece differs from
what this tool last built, and names it. `--replace` builds over it anyway.
Saves with `--save`. `--render <folder>` renders the sample garden, the
heights beside a person and a sheet of the pieces, without saving.
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paint_canvas import box_blur2, grow, one_material, ovate_leaf_profile, srgb, stroke  # noqa: E402

NAME = "boxwood_hedge"
E = 0.5  # half a grid cell

# Each height's cross-section, metres. `width` across the shoulders and
# `height` to the flat top; `shoulder` how far in from the edge the lid's top
# starts to roll over it; `drop` how far below the top the lid's hem hangs
# (half as far again since her "restore the last lid shape but lower it
# down", and a touch more for "lower it like a mm"); `lift` the body's side in from the shoulders under the lid;
# `batter` how much wider the body is at the soil than under the lid; `sprig`
# the leaf clusters' size (the knee-high side is too short for a full one).
# Standard is the parterre's knee-high box of her photo (the shrubs' 1.3 times
# a real boxwood's 0.3 to 0.4 m); waist; privacy, taller than a person. Each a
# step under its round height since the whole lid was lowered (her "now lower
# the lid another mm", "like the whole thing", "not jus the hem right?").
HEIGHTS = {
    "standard": dict(width=0.45, height=0.495, shoulder=0.09, drop=0.095, lift=0.025, batter=0.02,
                     sprig=0.75),
    "waist": dict(width=0.6, height=0.993, shoulder=0.12, drop=0.126, lift=0.03, batter=0.03, sprig=1.0),
    "privacy": dict(width=0.8, height=2.192, shoulder=0.16, drop=0.158, lift=0.035, batter=0.05,
                    sprig=1.0),
}
# How far the lid's hem stands out past the body's side: 20 mm (her "pull those
# edges in a little bit", then "bring it in even more", past 5 mm, to 3 mm, then
# "make it a few mm larger", 1 cm, "make the lid like another mm wide", 15 mm,
# and "make it another mm wider"; it had overhung 46 mm on the knee-high hedge). A lid 1 cm inside the side, the
# side rounding in under it, was tried and taken back (her "restore the last lid
# shape but lower it down").
OVERHANG = 0.02
WALL_UP = 0.5  # the body's wall reaches this share of the way from the lid's hem up to the lid over it
SHOULDER_STEPS = 2
ROOF_V = 0.1  # canvas metres the body's hidden roof takes

PIECES = ("straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "post", "bend", "curve",
          "curve_large")
ARCS = {"bend": 0.5, "curve": 1.5, "curve_large": 2.5}  # radius along the middle

# The canvas: `PX_M` pixels a metre, one metre wide, four tall.
PX_M = 512
CANVAS_W = PX_M
CANVAS_H = 4 * PX_M
CANVAS_H_M = CANVAS_H / PX_M
MARGIN_M = 0.04
# The box shrub's leaf (`paint_canvas.py`, `PROP_LEAFLETS["box_shrub"]`): small
# pointed ovals, stalk dark to tip light, each throwing a thin shadow on the
# leaves under it; a faint midrib. Between them, the leaves' shade (`GAP`).
LEAF_M = 0.13
LEAF_WIDTH = 0.32
SHADE = (0.62, 1.18)
SHADOW, SHADOW_M = 0.4, 0.008
GAP = 0.45
GAP_SHORT = 0.6  # the fill stops this many leaf lengths above a hem, so the tips stand free
ROW_STEP = 0.5  # leaf lengths between rows
COL_STEP = 0.52  # leaf lengths between leaves along a row
TILT = 15.0  # each leaf turned up to this far either way; a herringbone read as knitting
VARY_DARK = 0.03
TIP_INSET_PX = 2
LEAF_COLOUR = (0.24, 0.50, 0.17)  # linear, the box shrub's
RIB_COLOUR, RIB_TINT, RIB_PX = (0.40, 0.62, 0.18), 0.25, 1.5
ROUGH = 0.7
# Band shading, on the painted leaves: the lid's last `HEM_REACH` darker,
# `HEM_DARK` at its hem, its whole roll over the edge (her "the edge of the lid
# is a little too light"; it was 0.2 over 6 cm); the bodies darker all over
# (in the lid's shade) and more so at the soil.
HEM_DARK, HEM_REACH, BODY_DARK, GROUND_DARK = 0.32, 0.1, 0.72, 0.25

# The leaf clusters: small fans of three leaves, one or two together
# (`CLUMP_SPRIGS`), lying almost flat on the leaves in nearly the hedge's own
# green, as the shrubs' stray leaf clusters do (her choice, "B", of three
# tried after "the clusters are kind of weird": long pale sprigs in clumps of
# two to four, their tops cut off straight where they met the side, read as
# stiff bunches; round tufts were the third; `cluster_trials.png`). Each fan
# is a card `CLUSTER_M` square, bent once across its middle, its foot
# `CLUSTER_SINK` into the leaves and its middle and tip lifted out of them
# (the tip by `CLUSTER_TIP`, give or take `TIP_JITTER`, so no two cards of a
# clump share a plane); a clump's fans within `CLUMP_REACH` of its middle,
# fanned `CLUMP_FAN` degrees apart round its own turn. On the sides they hang
# turned up to `CLUSTER_TURN` either way from straight down, from the top of
# the body's wall (just behind the lid's hem) down to `CLUSTER_CLEAR` over the
# soil, clear of the gaps in its hem, never past a corner; on the lid's flat top (her "lets put a few random
# clusters on the top of the lid") they lie turned any way, reaching no more
# than `TOP_ROOM` onto its roll. About `CLUMP_DENSITY` clumps a square metre,
# dropped at random with none nearer another than `CLUMP_APART`. A height's
# `sprig` scales its cards. Three scatterings a piece. The canvas paints
# `CLUSTER_KINDS` fans of the box leaf side by side, a touch lighter than the
# hedge (`CLUSTER_LIGHT`); each card wears one, mirrored at random. None on
# the inside of a `bend`, too tight for a card.
CLUSTER_M = 0.22
CLUSTER_SINK, CLUSTER_MID, CLUSTER_TIP, TIP_JITTER = 0.003, 0.01, 0.025, 0.008
CLUSTER_TURN = 45.0
CLUSTER_CLEAR = GAP_SHORT * LEAF_M  # above the gaps between the body's hem of leaf tips
CLUMP_DENSITY = 2.6
CLUMP_APART = 0.3
CLUMP_SPRIGS = (1, 2)
CLUMP_REACH = (0.06, 0.04)  # along the side, up and down
CLUMP_FAN = 40.0
TOP_ROOM = 0.02
CLUSTER_SETS = ("a", "b", "c")
CLUSTER_KINDS = 3
# Each fan is painted in each of these shades, a row of the canvas apiece, and
# every card wears one at random (her "vary the lightness and darkness of hte
# leaf clusters a bit too", then "no lighter shades", "theyre already almost
# too light", "still a little too light in some places": the lightest a touch
# under `CLUSTER_LIGHT`).
CLUSTER_SHADES = (0.76, 0.85, 0.94)
CLUSTER_ROW = CLUSTER_M + 2 * MARGIN_M  # the canvas one shade's fans take
CLUSTER_LIGHT = 1.03
CLUSTER_TIGHTEST = 0.6  # no clusters on a wall curving in tighter than this radius
# A fan, from its foot: (how far along it, turn from its middle in degrees,
# length) of each pair of leaves, and last the one down its middle.
SPRIG = [(0.0, 26.0, 0.13), (0.0, 0.0, 0.16)]
STEM_COLOUR = (0.22, 0.30, 0.09)  # linear

SEED = 29


# --- cross-sections -------------------------------------------------------

def sections(spec):
    """(hat, body, wall_top, hem) for one height: the lid and the body each a
    list of (inset, z), inset in metres in from the shoulders' outline (out
    past it when negative), from the ridge out and down; the body's wall top;
    the lid's hem."""
    w, top, r, drop, lift = spec["width"], spec["height"], spec["shoulder"], spec["drop"], spec["lift"]
    flare = OVERHANG - lift  # the hem's reach past the shoulders' outline
    hem = top - drop
    # Flat to `shoulder` from the edge, then a quarter ellipse out and down to
    # the hem: the lid rolls over the edge and no further.
    reach = r + flare
    hat = [(w / 2, top)]
    for k in range(SHOULDER_STEPS + 1):
        phi = math.pi / 2 * k / SHOULDER_STEPS
        hat.append((r - reach * math.sin(phi), hem + drop * math.cos(phi)))
    # The body's wall rises behind the hem, part way up to the lid over the
    # body's side, so it meets the lid's underside without touching it.
    over = hem + drop * math.cos(math.asin((r - lift) / reach))
    wall_top = hem + (over - hem) * WALL_UP
    body = [(w / 2, top - lift - 0.01), (lift, wall_top), (lift - spec["batter"], 0.0)]
    return hat, body, wall_top, hem


def wall_inset(spec, z):
    """Where the body's side is at height `z`, in from the shoulders."""
    wall_top = sections(spec)[2]
    return spec["lift"] - spec["batter"] * (1.0 - z / wall_top)


def length(sheet):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(sheet, sheet[1:]))


def layout():
    """The canvas's three bands: (top, bottom) in metres down from its top."""
    hat_max = max(length(sections(s)[0]) for s in HEIGHTS.values())
    body_max = max(length(sections(s)[1][1:]) + ROOF_V for s in HEIGHTS.values())
    y = MARGIN_M
    bands = {}
    for name, size in (("hat", hat_max), ("clusters", CLUSTER_ROW * len(CLUSTER_SHADES)), ("body", body_max)):
        bands[name] = (y, y + size)
        y += size + MARGIN_M
    if y > CANVAS_H_M:
        raise SystemExit(f"hedge_kit: the bands need {y:.2f} m of canvas; it is {CANVAS_H_M:.2f} m tall")
    return bands


def rings(spec, bands):
    """The lid and body of one height as rings (inset, z, y): y its canvas row
    in metres down from the top."""
    hat, body, wall_top, hem = sections(spec)

    def mapped(sheet, band):
        total, s, out = length(sheet), 0.0, []
        for k, (d, z) in enumerate(sheet):
            if k:
                s += math.hypot(d - sheet[k - 1][0], z - sheet[k - 1][1])
            out.append((d, z, band[1] - (total - s)))  # the hem at the band's foot
        return out

    # The body read up from the ground by its length, its hidden roof squeezed
    # into `ROOF_V` of canvas above its wall.
    seen = mapped(body[1:], bands["body"])
    return mapped(hat, bands["hat"]), [(body[0][0], body[0][1], seen[0][2] - ROOF_V)] + seen


# --- footprints ---------------------------------------------------------------

def footprint(piece, w):
    """(points, closed, u, ring): the piece's outline in plan, anticlockwise,
    at the shoulders; `closed[i]` whether the side from point i to the next
    is hedge (it isn't where the piece meets the next); `u(i, k, p)` the
    texture's run along side i at point k, placed at p; `ring(d)` the
    outline with its hedge sides `d` in (out when negative)."""
    h = w / 2
    if piece in ARCS:
        radius = ARCS[piece]
        n = max(6, round(6 * radius))
        centre = Vector((-E, radius))
        turns = np.linspace(-math.pi / 2, 0.0, n + 1)

        def ring(d):
            # True arcs, not the chords' offsets: at both ends the section is
            # exactly a straight's, so the next piece meets it without a step.
            return ([centre + (radius + h - d) * Vector((math.cos(t), math.sin(t))) for t in turns]
                    + [centre + (radius - h + d) * Vector((math.cos(t), math.sin(t))) for t in turns[::-1]])

        # A whole number of metres along each face, so it meets the next
        # piece's leaves at both ends.
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
    elif piece == "post":
        pts, closed = [(-h, -h), (h, -h), (h, h), (-h, h)], [True] * 4
    else:
        raise KeyError(piece)
    pts = [Vector(p) for p in pts]

    def u(i, k, p):
        # Along a side by the grid: x along an east-west side, y along a
        # north-south one.
        a, b = pts[i], pts[(i + 1) % len(pts)]
        return p.x if abs(b.x - a.x) > abs(b.y - a.y) else p.y

    return pts, closed, u, lambda d: inset_ring(pts, closed, d)


def inset_ring(pts, closed, d):
    """`pts` with every hedge side moved `d` in (out when negative) and the
    open sides left where they are, each corner where its two sides meet."""
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


def add_sheet(bm, uv, verts, outline, sheet):
    """The sheet's bands round the outline's hedge sides into `bm`."""
    pts, closed, u, ring = outline
    ring_pts = [ring(d) for d, z, y in sheet]
    n = len(pts)

    def vert(p, z):
        key = (round(p.x, 5), round(p.y, 5), round(z, 5))
        if key not in verts:
            verts[key] = bm.verts.new((p.x, p.y, z))
        return verts[key]

    for k in range(len(sheet) - 1):
        for i in range(n):
            if not closed[i]:
                continue
            j = (i + 1) % n
            loop = []
            for kk, ii in ((k, i), (k + 1, i), (k + 1, j), (k, j)):
                p = ring_pts[kk][ii]
                v = vert(p, sheet[kk][1])
                if loop and loop[-1][0] is v:
                    continue
                loop.append((v, (u(i, ii, p), 1.0 - sheet[kk][2] / CANVAS_H_M)))
            if len(loop) > 1 and loop[0][0] is loop[-1][0]:
                loop.pop()
            if len(loop) < 3:
                continue
            try:
                face = bm.faces.new([v for v, _ in loop])
            except ValueError:
                continue
            if face.calc_area() < 1e-8:
                bm.faces.remove(face)
                continue
            for corner, (_, t) in zip(face.loops, loop):
                corner[uv].uv = t


def mesh_of(name, outline, sheets, material):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    verts = {}
    for sheet in sheets:
        add_sheet(bm, uv, verts, outline, sheet)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(50))
    return me


def runs(pts, closed):
    """The outline's hedge sides as runs that turn less than 30 degrees where
    they meet (a curve's many sides are one run): (sides, starts at an open
    side, ends at one, the radius it curves in by, or infinity)."""
    n = len(pts)

    def turn(i):
        """Degrees the outline turns at point i, anticlockwise positive."""
        a = (pts[i] - pts[i - 1]).normalized()
        b = (pts[(i + 1) % n] - pts[i]).normalized()
        return math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))

    out = []
    for i in range(n):
        if not closed[i] or (closed[i - 1] and abs(turn(i)) < 30.0):
            continue
        sides, j = [i], (i + 1) % n
        while closed[j] and abs(turn(j)) < 30.0 and j != i:
            sides.append(j)
            j = (j + 1) % n
        inward = [-turn(k) for k in sides[1:] if turn(k) < 0.0]
        radius = math.inf
        if inward:
            radius = (pts[(sides[0] + 1) % n] - pts[sides[0]]).length / math.radians(sum(inward) / len(inward))
        out.append((sides, not closed[i - 1], not closed[j], radius))
    return out


def card_uv(bands, kind, shade, x, a, mirror):
    """Where a cluster card's point `x` across and `a` down from its foot lies
    on the canvas: its kind's square in its shade's row of the clusters."""
    u0 = kind / CLUSTER_KINDS + (1.0 / CLUSTER_KINDS - CLUSTER_M) / 2
    u = u0 + (CLUSTER_M / 2 - x if mirror else x + CLUSTER_M / 2)
    return u, 1.0 - (bands["clusters"][0] + shade * CLUSTER_ROW + MARGIN_M + a) / CANVAS_H_M


def card(tip):
    """A cluster card's corners (across, down from its foot, out of the leaves)
    and its two faces, bent once across its middle."""
    return ([(-CLUSTER_M / 2, 0.0, -CLUSTER_SINK), (CLUSTER_M / 2, 0.0, -CLUSTER_SINK),
             (-CLUSTER_M / 2, CLUSTER_M / 2, CLUSTER_MID), (CLUSTER_M / 2, CLUSTER_M / 2, CLUSTER_MID),
             (-CLUSTER_M / 2, CLUSTER_M, tip), (CLUSTER_M / 2, CLUSTER_M, tip)], [(0, 1, 3, 2), (2, 3, 5, 4)])


def scatter(spec, outline, seed):
    """One scattering of leaf clusters over a piece's sides and lid: each card
    as ([(point, (x, a))], its kind, whether it is mirrored, the way out)."""
    pts, closed, u, ring = outline
    wall_top, hem = sections(spec)[2:]
    top = wall_top
    slope = spec["batter"] / wall_top  # the side leans out this much a metre down
    rng = np.random.default_rng(seed)
    shades = np.random.default_rng(seed ^ 0x5EED)  # its own random: the cards lie where they did
    n = len(pts)
    cards, roots = [], []
    for sides, open_a, open_b, radius in runs(pts, closed):
        if radius < CLUSTER_TIGHTEST:
            continue
        base = ring(wall_inset(spec, 0.0))
        run_m = sum((base[(k + 1) % n] - base[k]).length for k in sides)
        want = CLUMP_DENSITY * run_m * hem
        count = int(want) + (1 if rng.random() < want - int(want) else 0)
        clumps, tries = 0, 0
        while clumps < count and tries < 80 * count:
            tries += 1
            middle_s = rng.uniform(0.0, run_m)
            middle_z = rng.uniform(CLUSTER_CLEAR, top)
            middle_turn = rng.uniform(-CLUSTER_TURN, CLUSTER_TURN)
            sprigs = int(rng.integers(CLUMP_SPRIGS[0], CLUMP_SPRIGS[1] + 1))
            fan = [middle_turn + (i - (sprigs - 1) / 2) * CLUMP_FAN + rng.uniform(-6.0, 6.0) for i in range(sprigs)]
            clump = []
            for turn in fan:
                placed = place_sprig(spec, ring, sides, open_a, open_b, slope, wall_top, top,
                                     middle_s + rng.uniform(-1.0, 1.0) * CLUMP_REACH[0],
                                     middle_z + rng.uniform(-1.0, 1.0) * CLUMP_REACH[1], math.radians(turn),
                                     CLUSTER_TIP + rng.uniform(-TIP_JITTER, TIP_JITTER))
                if placed is not None:
                    clump.append(placed)
            if not clump:
                continue
            centre = sum((placed[0] for placed in clump), Vector()) / len(clump)
            if any((centre - q).length < CLUMP_APART for q in roots):
                continue
            roots.append(centre)
            for root, corners, face, faces in clump:
                cards.append((corners, int(rng.integers(CLUSTER_KINDS)), int(shades.integers(len(CLUSTER_SHADES))),
                          bool(rng.random() < 0.5), face, faces))
            clumps += 1
    # A few on the lid's flat top, lying on it, turned any way.
    flat = ring(spec["shoulder"])
    room = ring(spec["shoulder"] - TOP_ROOM)
    want = CLUMP_DENSITY * abs(sum(a.x * b.y - b.x * a.y for a, b in zip(flat, flat[1:] + flat[:1]))) / 2
    count = int(want) + (1 if rng.random() < want - int(want) else 0)
    low = Vector((min(p.x for p in flat), min(p.y for p in flat)))
    high = Vector((max(p.x for p in flat), max(p.y for p in flat)))
    clumps, tries = 0, 0
    while clumps < count and tries < 80 * count:
        tries += 1
        middle = Vector((rng.uniform(low.x, high.x), rng.uniform(low.y, high.y)))
        if not inside(flat, middle):
            continue
        middle_turn = rng.uniform(0.0, 360.0)
        sprigs = int(rng.integers(CLUMP_SPRIGS[0], CLUMP_SPRIGS[1] + 1))
        clump = []
        for i in range(sprigs):
            turn = math.radians(middle_turn + (i - (sprigs - 1) / 2) * CLUMP_FAN + rng.uniform(-6.0, 6.0))
            foot = middle + Vector((rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0))) * CLUMP_REACH[0]
            placed = place_top(spec, room, foot, turn, CLUSTER_TIP + rng.uniform(-TIP_JITTER, TIP_JITTER))
            if placed is not None:
                clump.append(placed)
        if not clump:
            continue
        centre = sum((placed[0] for placed in clump), Vector()) / len(clump)
        if any((centre - q).length < CLUMP_APART for q in roots):
            continue
        roots.append(centre)
        for root, corners, face, faces in clump:
            cards.append((corners, int(rng.integers(CLUSTER_KINDS)), int(shades.integers(len(CLUSTER_SHADES))),
                          bool(rng.random() < 0.5), face, faces))
        clumps += 1
    return cards


def inside(poly, p):
    """Whether plan point `p` lies inside the outline `poly`."""
    hit = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a.y > p.y) != (b.y > p.y) and p.x < a.x + (p.y - a.y) / (b.y - a.y) * (b.x - a.x):
            hit = not hit
    return hit


def place_top(spec, room, foot2, turn, tip):
    """One cluster card lying on the lid's flat top, its foot at plan point
    `foot2`, pointing `turn` radians round: as `place_sprig`, or None where a
    corner would reach past `room` (onto the lid's roll, or past an open end)."""
    down = Vector((math.cos(turn), math.sin(turn), 0.0))
    face = Vector((0.0, 0.0, 1.0))
    across = face.cross(down)
    root = Vector((foot2.x, foot2.y, spec["height"]))
    shape, faces = card(tip)
    corners = [root + (across * x + down * a + face * o) * spec["sprig"] for x, a, o in shape]
    if not all(inside(room, c) for c in corners):
        return None
    return root, [(c, (x, a)) for c, (x, a, o) in zip(corners, shape)], face, faces


def place_sprig(spec, ring, sides, open_a, open_b, slope, wall_top, top, s_want, z, theta, tip):
    """One sprig card on a run of the body's side, its foot `s_want` along
    the run at height `z`, turned `theta` from hanging straight down: (foot,
    [(point, (x, a))], the way out), or None where it would reach past a
    corner, under the soil or over the lid's hem allowance."""
    n = len(ring(0.0))
    poly = ring(wall_inset(spec, min(max(z, 0.0), wall_top)))
    chain = [poly[sides[0]]] + [poly[(k + 1) % n] for k in sides]
    lengths = [(b - a).length for a, b in zip(chain, chain[1:])]
    s_at = s_want
    if not 0.0 <= s_at <= sum(lengths):
        return None
    k, gone = 0, 0.0
    while k < len(lengths) - 1 and gone + lengths[k] < s_at:
        gone += lengths[k]
        k += 1
    along2 = (chain[k + 1] - chain[k]).normalized()
    at2 = chain[k].lerp(chain[k + 1], (s_at - gone) / lengths[k])
    tangent = Vector((along2.x, along2.y, 0.0))
    out = Vector((along2.y, -along2.x, 0.0))
    down_side = (Vector((0.0, 0.0, -1.0)) + out * slope).normalized()
    face = down_side.cross(tangent)
    face = face if face.dot(out) > 0 else -face
    down = down_side * math.cos(theta) + tangent * math.sin(theta)
    across = face.cross(down).normalized()
    root = Vector((at2.x, at2.y, z))
    shape, faces = card(tip)
    corners = [root + (across * x + down * a + face * o) * spec["sprig"] for x, a, o in shape]
    if min(c.z for c in corners) < CLUSTER_CLEAR or max(c.z for c in corners) > top:
        return None
    # Along the run, the card's reach either way: never past a corner,
    # though it may hang over an open end onto the next piece's side.
    reach = [(c - root).dot(tangent) for c in corners]
    if (not open_a and s_at + min(reach) < 0.02) or (not open_b and s_at + max(reach) > sum(lengths) - 0.02):
        return None
    return root, [(c, (x, a)) for c, (x, a, o) in zip(corners, shape)], face, faces


def clusters_mesh(name, cards, bands, material):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for corners, kind, shade, mirror, face, faces in cards:
        vs = [bm.verts.new(c) for c, _ in corners]
        for quad in faces:
            f = bm.faces.new([vs[q] for q in quad])
            f.normal_update()
            if f.normal.dot(face) < 0:
                f.normal_flip()
            for loop in f.loops:
                x, a = corners[vs.index(loop.vert)][1]
                loop[uv].uv = card_uv(bands, kind, shade, x, a, mirror)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    me.shade_smooth()
    return me


def cluster_set(x, y):
    """The scattering a piece at grid point (x, y) shows: the game's rule
    (`boxwood_hedge.gd`, by Godot's (x, z), and Godot's z is Blender's -y)."""
    return CLUSTER_SETS[(round(x) * 7 - round(y) * 13) % len(CLUSTER_SETS)]


def shape_hash(me):
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    return hashlib.sha1(np.round(co, 5).tobytes()).hexdigest()[:16]


# --- the canvas -----------------------------------------------------------------

def lay_leaf(state, start, direction, here, own, vary):
    """One leaf into `state` (leaves, midribs, tone), within its own window."""
    leaves, ribs, tone = state
    h, w = leaves.shape
    tip = start + direction * here
    half = here * LEAF_WIDTH
    pad = int(SHADOW_M * PX_M) + 4
    x0 = max(int(math.floor(min(start[0], tip[0]) - half - pad)), 0)
    x1 = min(int(math.ceil(max(start[0], tip[0]) + half + pad)), w)
    y0 = max(int(math.floor(min(start[1], tip[1]) - half - pad)), 0)
    y1 = min(int(math.ceil(max(start[1], tip[1]) + half + pad)), h)
    if x1 <= x0 or y1 <= y0:
        return
    o = np.array([x0, y0], dtype=np.float64)
    leaf = np.zeros((y1 - y0, x1 - x0), dtype=np.float32)
    rib = np.zeros_like(leaf)
    stroke(leaf, start - o, tip - o, half, ovate_leaf_profile)
    stroke(rib, start + direction * here * 0.08 - o, start + direction * here * 0.8 - o, RIB_PX,
           lambda t: 1.0 - 0.8 * t)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    along = np.clip(((xx - start[0]) * direction[0] + (yy - start[1]) * direction[1]) / here, 0.0, 1.0)
    shade = (SHADE[0] + (SHADE[1] - SHADE[0]) * along ** 0.8) * own * vary
    solid = (leaf > 0.5).astype(np.float32)
    near = box_blur2(solid, max(2, int(SHADOW_M * PX_M)))
    lv, rb, tn = leaves[y0:y1, x0:x1], ribs[y0:y1, x0:x1], tone[y0:y1, x0:x1]
    tn = tn * (1.0 - SHADOW * np.clip(near * 2.0, 0.0, 1.0) * (1.0 - leaf) * lv)
    tone[y0:y1, x0:x1] = tn * (1.0 - leaf) + shade * leaf
    ribs[y0:y1, x0:x1] = rb * (1.0 - leaf) + rib * leaf
    leaves[y0:y1, x0:x1] = np.maximum(lv, leaf)


def paint_band(size_m, rng):
    """(leaves, midribs, tone) for one band `size_m` tall and the canvas wide,
    repeating across: painted three canvases wide, each leaf in all three, and
    the middle one kept. The lowest row's tips are its foot, a hem, and the
    fill stops short of them so the tips stand free."""
    rows_px = int(round(size_m * PX_M))
    wide = 3 * CANVAS_W
    length_px = LEAF_M * PX_M
    leaves = np.zeros((rows_px, wide), dtype=np.float32)
    tone = np.ones((rows_px, wide), dtype=np.float32)
    ribs = np.zeros((rows_px, wide), dtype=np.float32)
    fill_to = int(rows_px - length_px * GAP_SHORT)
    leaves[:fill_to] = 1.0
    tone[:fill_to] = GAP
    state = [leaves, ribs, tone]
    step = length_px * ROW_STEP
    count = max(1, round(CANVAS_W / (length_px * COL_STEP)))
    first = rows_px - TIP_INSET_PX - length_px
    rows = []
    y = first
    while y > -length_px * 0.6:
        rows.append(y)
        y -= step
    vary_rng = np.random.default_rng(zlib.crc32(f"dark {size_m:.3f}".encode()))
    for r, y in enumerate(rows):  # the lowest first: each row up lies over the one below
        turn = rng.uniform(0.0, 1.0)
        for j in range(count):
            x = (j + turn + rng.uniform(-0.15, 0.15)) / count * CANVAS_W
            jitter = rng.uniform(-0.35, 0.35) * step
            yj = y - abs(jitter) if r == 0 else y + jitter
            a = math.radians(rng.uniform(-TILT, TILT))
            direction = np.array([math.sin(a), math.cos(a)])
            here = min(length_px * rng.uniform(0.9, 1.05), (rows_px - TIP_INSET_PX - yj) / max(direction[1], 0.3))
            own = 1.0 + rng.uniform(-0.06, 0.06)
            vary = (1.0 - vary_rng.uniform(0.0, VARY_DARK)) ** 2.2
            for copy in range(3):
                lay_leaf(state, np.array([x + copy * CANVAS_W, yj]), direction, here, own, vary)
    leaves, ribs, tone = (a[:, CANVAS_W:2 * CANVAS_W] for a in state)
    return leaves, ribs, tone


def paint_clusters(size_m, rng):
    """(leaves, midribs, tone, stems) for the clusters: `CLUSTER_KINDS` fans
    side by side, each in its card's square: from the card's foot, pairs of
    leaves turned out from its middle (`SPRIG`; a stem where a pair starts down
    it) and a leaf down the middle laid over them; now and then a leaf of a
    pair left out. The row again for each of `CLUSTER_SHADES`."""
    rows_px = int(round(CLUSTER_ROW * PX_M))
    leaves = np.zeros((rows_px, CANVAS_W), dtype=np.float32)
    ribs = np.zeros_like(leaves)
    tone = np.ones_like(leaves)
    stems = np.zeros_like(leaves)
    state = [leaves, ribs, tone]
    for kind in range(CLUSTER_KINDS):
        u0 = kind / CLUSTER_KINDS + (1.0 / CLUSTER_KINDS - CLUSTER_M) / 2
        foot = np.array([(u0 + CLUSTER_M / 2) * PX_M, (MARGIN_M + 0.006) * PX_M])
        stroke(stems, foot, foot + np.array([0.0, SPRIG[-1][0] * PX_M]), 1.8, lambda t: 1.0 - 0.4 * t)
        for down_m, turn, leaf_m in SPRIG:
            for side in ((-1, 1) if turn else (0,)):
                if turn and rng.random() < 0.15:
                    continue
                a = math.radians(side * turn + rng.uniform(-8.0, 8.0))
                lay_leaf(state, foot + np.array([0.0, down_m * PX_M]), np.array([math.sin(a), math.cos(a)]),
                         leaf_m * rng.uniform(0.92, 1.0) * PX_M, CLUSTER_LIGHT * (1.0 + rng.uniform(-0.06, 0.06)),
                         1.0)
    full = [np.zeros((int(round(size_m * PX_M)), CANVAS_W), dtype=np.float32) for _ in range(4)]
    full[2][:] = 1.0
    for k, shade in enumerate(CLUSTER_SHADES):
        y0 = int(round(k * CLUSTER_ROW * PX_M))
        for whole, row in zip(full, (leaves, ribs, tone * shade, stems)):
            whole[y0:y0 + rows_px] = row
    return tuple(full)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def paint(bands, folder):
    """The canvas, its ORM, cut-out and guide; returns (colour, orm) images."""
    rng = np.random.default_rng(SEED)
    rgb = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.float32)
    alpha = np.zeros((CANVAS_H, CANVAS_W), dtype=np.float32)
    known = np.zeros((CANVAS_H, CANVAS_W), dtype=bool)
    for name, (top, bottom) in bands.items():
        stems = None
        if name == "clusters":
            leaves, ribs, tone, stems = paint_clusters(bottom - top, rng)
        else:
            leaves, ribs, tone = paint_band(bottom - top, rng)
        rows = leaves.shape[0]
        f = (np.arange(rows, dtype=np.float32) / max(rows - 1, 1))[:, None]  # 0 at the band's top, 1 at its foot
        from_foot = (1.0 - f) * (bottom - top)  # metres up from the foot
        if name == "body":
            tone = tone * BODY_DARK * (1.0 - GROUND_DARK * (1.0 - smooth(0.0, 0.18, from_foot)))
        elif name == "hat":
            tone = tone * (1.0 - HEM_DARK * (1.0 - smooth(0.0, HEM_REACH, from_foot)))
        colour = np.array(LEAF_COLOUR, dtype=np.float32) * tone[..., None]
        tint = (ribs * RIB_TINT)[..., None]
        colour = colour * (1.0 - tint) + np.array(RIB_COLOUR, dtype=np.float32) * tint
        if stems is not None:
            bare = (stems * (1.0 - leaves))[..., None]  # the stem shows only where no leaf lies over it
            colour = colour * (1.0 - bare) + np.array(STEM_COLOUR, dtype=np.float32) * bare
            leaves = np.maximum(leaves, stems)
        y0 = int(round(top * PX_M))
        rgb[y0:y0 + rows] = colour
        alpha[y0:y0 + rows] = leaves
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
    orm = np.zeros((CANVAS_H // 16, CANVAS_W // 16, 3), dtype=np.float32)
    orm[..., 0], orm[..., 1] = 1.0, ROUGH
    orm_img = write(os.path.join(folder, f"{NAME}_orm.png"), orm, None, "Non-Color")
    bpy.data.images.remove(write(os.path.join(folder, f"{NAME}_cutout.png"),
                                 np.repeat(alpha[..., None], 3, axis=2), None, "Non-Color"))
    # The guide: each band's edges, and where each height's ridge, hem and
    # wall top fall on it.
    guide = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.float32)
    for top, bottom in bands.values():
        for y in (top, bottom):
            guide[int(round(y * PX_M)):int(round(y * PX_M)) + 2] = (1, 1, 1, 1)
    for spec in HEIGHTS.values():
        for sheet in rings(spec, bands):
            for _, _, y in (sheet[0], sheet[-1]):
                guide[int(round(y * PX_M)), ::4] = (1, 1, 1, 1)
    bpy.data.images.remove(write(os.path.join(folder, f"{NAME}_uv_guide.png"), guide[..., :3], guide[..., 3]))
    return colour, orm_img


# --- the file -------------------------------------------------------------------

def child(parent, name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if coll.name not in parent.children:
        parent.children.link(coll)
    return coll


# The sample garden (`authored/sample_parterre`): (height, piece, x, y, turn in
# quarter turns anticlockwise), after her photograph: a bed quartered by tees,
# a ring, a bed with rounded corners and an opening between two ends, a bed
# crossed four ways, two rings one inside the other; behind, a waist-high row
# and a privacy hedge wrapping the back corners.
def sample_garden():
    out = []

    def rect(x0, y0, x1, y1, corner="corner", height="standard"):
        out.extend([(height, corner, x0, y0, 3), (height, corner, x1, y0, 0),
                    (height, corner, x1, y1, 1), (height, corner, x0, y1, 2)])

    def run_x(y, xs, height="standard"):
        out.extend((height, "straight", x, y, 0) for x in xs)

    def run_y(x, ys, height="standard"):
        out.extend((height, "straight", x, y, 1) for y in ys)

    def ring(cx, cy, piece, height="standard"):
        r = ARCS[piece]
        for q, (ox, oy) in enumerate(((0.5, -r), (r, 0.5), (-0.5, r), (-r, -0.5))):
            out.append((height, piece, cx + ox, cy + oy, q))

    # A bed divided down the middle by tees.
    rect(0, 0, 4, 3)
    run_x(0, (1, 3))
    run_x(3, (1, 3))
    out += [("standard", "tee", 2, 0, 0), ("standard", "tee", 2, 3, 2)]
    run_y(0, (1, 2))
    run_y(4, (1, 2))
    run_y(2, (1, 2))
    ring(7.5, 1.5, "curve")
    # Rounded corners and an opening between two ends.
    rect(11, 0, 14, 3, corner="bend")
    out += [("standard", "end", 12, 0, 0), ("standard", "end", 13, 0, 2)]
    run_x(3, (12, 13))
    run_y(11, (1, 2))
    run_y(14, (1, 2))
    # Crossed four ways.
    rect(0, -6, 4, -2)
    run_x(-6, (1, 3))
    run_x(-2, (1, 3))
    run_x(-4, (1, 3))
    run_y(0, (-5, -3))
    run_y(4, (-5, -3))
    run_y(2, (-5, -3))
    out += [("standard", "tee", 2, -6, 0), ("standard", "tee", 2, -2, 2), ("standard", "tee", 0, -4, 3),
            ("standard", "tee", 4, -4, 1), ("standard", "cross", 2, -4, 0)]
    ring(8.5, -3.5, "curve_large")
    ring(8.5, -3.5, "curve")
    out += [("standard", "post", 12, -4, 0), ("standard", "post", 14, -4, 0),
            ("standard", "post", 12, -2, 0), ("standard", "post", 14, -2, 0)]
    # Behind: a waist-high row, and the privacy hedge round the back.
    out += [("waist", "end", -1, 5, 2), ("waist", "straight_4", 0, 5, 0), ("waist", "straight_4", 4, 5, 0),
            ("waist", "straight_4", 8, 5, 0), ("waist", "straight_2", 12, 5, 0), ("waist", "straight", 14, 5, 0),
            ("waist", "end", 15, 5, 0)]
    out += [("privacy", "corner", -2, 7, 2), ("privacy", "straight_4", -1, 7, 0),
            ("privacy", "straight_4", 3, 7, 0), ("privacy", "straight_4", 7, 7, 0),
            ("privacy", "straight_4", 11, 7, 0), ("privacy", "straight", 15, 7, 0),
            ("privacy", "corner", 16, 7, 1), ("privacy", "straight", -2, 6, 1), ("privacy", "straight", -2, 5, 1),
            ("privacy", "straight", 16, 6, 1), ("privacy", "straight", 16, 5, 1), ("privacy", "end", -2, 4, 3),
            ("privacy", "end", 16, 4, 3)]
    return out


def place_copies(coll, placements, parts, offset=(0.0, 0.0)):
    """Linked duplicates of each placement's body, lid and the scattering of
    clusters the game would show there into `coll`."""
    made = []
    for height, piece, x, y, turn in placements:
        part = parts[f"{height}_{piece}"]
        for src in (part["body"], part["hat"], part["clusters"][cluster_set(x, y)]):
            dup = src.copy()  # shares its mesh: reshape the piece and every copy follows
            dup.location = (x + offset[0], y + offset[1], 0.0)
            dup.rotation_euler = (0.0, 0.0, turn * math.pi / 2)
            for key in ("kyt_variant", "kyt_merge_group", "kyt_collision", "kyt_hedge_hash"):
                if key in dup:
                    del dup[key]
            coll.objects.link(dup)
            made.append(dup)
    return made


def build(replace):
    scene = bpy.context.scene
    root = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), os.pardir, os.pardir, os.pardir))
    export = bpy.data.collections["export"]
    authored = bpy.data.collections["authored"]
    edited = [o.name for o in export.all_objects
              if o.type == "MESH" and o.data.get("kyt_hedge_hash") not in (None, shape_hash(o.data))]
    if edited and not replace:
        raise SystemExit("hedge_kit: these pieces were reshaped since the last build and would be lost: "
                         + ", ".join(sorted(edited)) + ". Move them out of 'export' or run with --replace.")
    old = [o for o in list(export.all_objects) + list(authored.all_objects)
           if o.get("kyt_hedge") or (o.type == "MESH" and o.data.get("kyt_hedge_hash"))]
    for o in old:
        bpy.data.objects.remove(o, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    bands = layout()
    colour, orm = paint(bands, os.path.join(root, "assets", "source", "textures", NAME))
    material = one_material(NAME, colour, orm, "UVMap", clip=True, double_sided=True)

    parts = {}
    triangles = {}

    def add(coll, key, name, me, group=None):
        me["kyt_hedge_hash"] = shape_hash(me)
        obj = bpy.data.objects.new(name, me)
        obj["kyt_variant"] = key
        obj["kyt_hedge"] = True
        if group:
            obj["kyt_merge_group"] = group
            obj["kyt_collision"] = "none"
        coll.objects.link(obj)
        me.calc_loop_triangles()
        return obj, len(me.loop_triangles)

    for height, spec in HEIGHTS.items():
        coll = child(export, height)
        hat, body = rings(spec, bands)
        for piece in PIECES:
            outline = footprint(piece, spec["width"])
            key = f"{height}_{piece}"
            body_obj, body_tris = add(coll, key, key, mesh_of(key, outline, [body], material))
            hat_obj, hat_tris = add(coll, key, f"{key}_hat", mesh_of(f"{key}_hat", outline, [hat], material), "hat")
            sets, counts = {}, []
            for tag in CLUSTER_SETS:
                name = f"{key}_clusters_{tag}"
                cards = scatter(spec, outline, zlib.crc32(name.encode()))
                sets[tag], tris = add(coll, key, name, clusters_mesh(name, cards, bands, material), f"clusters_{tag}")
                counts.append(len(cards))
            parts[key] = dict(body=body_obj, hat=hat_obj, clusters=sets)
            triangles[key] = (body_tris + hat_tris, counts)

    garden = child(authored, "sample_parterre")
    garden["kyt_hedge"] = True
    for o in place_copies(garden, sample_garden(), parts):
        o["kyt_hedge"] = True
    layer = bpy.context.view_layer.layer_collection.children.get("export")
    if layer is not None:
        layer.hide_viewport = True  # every piece stands at the origin; the sample shows them laid out
    scene["kyt_hedge_bands"] = {k: list(v) for k, v in bands.items()}

    for height in HEIGHTS:
        row = ", ".join(f"{p} {triangles[f'{height}_{p}'][0]} + {'/'.join(map(str, triangles[f'{height}_{p}'][1]))}"
                        for p in PIECES)
        print(f"hedge_kit: {height} (triangles + clusters in each scattering, 4 triangles each): {row}")
    print(f"hedge_kit: canvas {CANVAS_W}x{CANVAS_H} ({PX_M} px/m, repeating every metre); bands "
          + ", ".join(f"{k} {b - t:.2f} m" for k, (t, b) in bands.items()))
    return parts


# --- review renders -----------------------------------------------------------

def render(folder):
    """The sample garden from above and at eye level, the three heights beside
    a person, and each height's pieces, labelled, into `folder`."""
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    parts = {}
    for o in bpy.data.collections["export"].all_objects:
        if not o.get("kyt_variant"):
            continue
        part = parts.setdefault(o["kyt_variant"], dict(clusters={}))
        group = str(o.get("kyt_merge_group", ""))
        if group.startswith("clusters_"):
            part["clusters"][group.removeprefix("clusters_")] = o
        else:
            part["hat" if group == "hat" else "body"] = o
    authored = bpy.data.collections["authored"]
    authored.hide_render = False
    bpy.data.collections["export"].hide_render = True
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)

    def colour_material(name, rgb, emit=False):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
        if emit:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 1.0
        return mat

    bpy.ops.mesh.primitive_plane_add(size=1000, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.data.materials.append(colour_material("_gravel", (0.30, 0.25, 0.19)))
    for coll in ground.users_collection:
        coll.objects.unlink(ground)
    stage.objects.link(ground)
    person_mat = colour_material("_person", (0.55, 0.42, 0.6))
    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 2.4
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(48), 0.0, math.radians(-35))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False

    def label(text, x, y, size=0.4):
        curve = bpy.data.curves.new(f"_label_{text}", "FONT")
        curve.body = text
        curve.size = size
        curve.align_x = "CENTER"
        obj = bpy.data.objects.new(f"_label_{text}", curve)
        obj.location = (x, y, 0.01)
        curve.materials.append(colour_material("_ink", (0.02, 0.02, 0.02)))
        stage.objects.link(obj)

    def person(x, y):
        """A person 1.75 m tall, for scale: a capsule."""
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.31, location=(x, y, 0.22 + 1.31 / 2))
        body = bpy.context.active_object
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(x, y, 1.53))
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
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"hedge_kit: rendered {scene.render.filepath}")

    shoot("garden_overview", (-4.0, -13.0, 8.5), (7.0, -0.5, 0.0), lens=26)
    shoot("garden_corner_close", (-2.3, -8.2, 1.7), (1.5, -4.0, 0.3), lens=30)
    shoot("garden_eye_level", (5.0, -9.5, 1.6), (6.5, 2.0, 0.6), lens=30)

    # The heights side by side: a person in front, and one behind the privacy
    # hedge, hidden from eye height.
    ox = 200.0
    for i, height in enumerate(HEIGHTS):
        y = i * 3.0
        place_copies(stage, [(height, "end", -1, y, 2), (height, "straight_2", 0, y, 0), (height, "corner", 2, y, 0),
                             (height, "end", 2, y + 1, 1)], parts, (ox, 0.0))
        label(height, ox - 2.6, y, 0.45)
    for i in range(3):
        person(ox - 1.9, i * 3.0 - 0.9)
    person(ox + 0.6, 7.3)
    shoot("heights", (ox - 6.5, -7.5, 1.6), (ox + 0.2, 3.0, 1.0), lens=32)

    # Each height's pieces, labelled.
    oy = -200.0
    rows = (("straight", "straight_2", "straight_4", "end", "post", "corner"),
            ("tee", "cross", "bend", "curve", "curve_large"))
    span = {"straight_2": 2, "straight_4": 4, "curve": 2, "curve_large": 3}
    for i, height in enumerate(HEIGHTS):
        base_x = i * 40.0
        for r, row in enumerate(rows):
            x = base_x
            for piece in row:
                wide = span.get(piece, 1)
                y = oy - r * 6.0
                place_copies(stage, [(height, piece, x + 0.5, y, 0)], parts)
                label(piece, x + wide / 2, y - 1.4, 0.4)
                x += wide + 1.6
        label(height, base_x - 3.0, oy - 2.5, 0.7)
        shoot(f"pieces_{height}", (base_x + 9.0, oy - 19.0, 14.0), (base_x + 9.0, oy - 3.2, 0.0), lens=30,
              size=(1800, 1100))


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
