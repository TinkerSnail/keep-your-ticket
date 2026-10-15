"""Seabed C3 into the ground's height grid (2026-10-14).

Christina chose seabed C3 (`documentation/screenshots/seabed-canyon-bay-2026-10-12/`): the canyon
coast with its trunk taken into the bay and a south arm, over the sandy shelf, with a bed for the
park's west-shore box. Since 2026-10-13 the ground is one height grid
(`documentation/terrain-height-grid-plan-2026-10-12.md`), so the seabed goes into the grid rather
than becoming a mesh: this computes C3's bed at every node of both tiers that has no ground, and
records it, with the sandy shelf's reshape of the shelves it starts from and the harbour's cliff
foot, as one undoable grid edit, `seabed_c3`, through `ground_grid_edit.apply_arrays` (the array form
of `apply_values`, which a sea of tens of millions of nodes needs).

    Blender -b --factory-startup --python tools/blender/seabed_build.py -- [--root DIR] [--dry]
        [--report FILE] [--stride N] [--aerial PNG] [--carry-down | --as-drawn]
    python3 tools/blender/seabed_build.py --chart PNG --report FILE [--root DIR]     # needs Pillow

- `--root` works on another copy of `assets/source/world_ground/` (a proof's scratch copy).
- `--dry` computes and measures everything and writes nothing into the grid.
- `--report` writes the measurements, and what the chart needs, as JSON.
- `--stride N` evaluates every Nth node only, for a quick look; it is always `--dry`.
- `--aerial PNG` renders the aerial frame from the bed as built (written or `--dry`): the C3
  proposals' camera, water colouring and stand-ins. Cameras, lights and render materials exist only
  during the run; nothing is saved.
- `--chart PNG` (plain Python with Pillow) draws the bathymetric chart in the C3 style from the
  grid as it stands, with the ferry route, footings and park box from a build's `--report`.
- `--carry-down` (the default since 2026-10-14) and `--as-drawn` set `DEAN_CARRIES_DOWN` (below).
- Undo is the grid's own: `python3 tools/ground_grid_edit.py --undo` restores every file bit for bit.
- A run takes about seven minutes and 5.5 GB.

The bed is C3's, as the proposals drew it on 2026-10-12, with its rules reading the grid instead of
the master's open edges:
- **Where it starts.** The grid's own no-data boundary is the edge. A sea node beside ground lies
  `UNDER` (5 cm) under the lowest ground of its four neighbours (of its diagonal ones where those
  have none), never above `CAP` (-8.05). Every other node is the bed's function, never above `CAP`.
- **The sea** is every no-data node joined to the grid's outer edge, outside the held outlines in
  `holes.json` (the road corridor, the tunnel lids, NT-2's earth), and in the park's box only the
  water the game's collision shows (`PARK_CSV`, with the pier, its pavilion and the wheel's jetty);
  the bed runs `OVERLAP` on under the park's shore box at its foot, and near that shore starts from
  the foot (`PARK_HOLD`).
- **The sandy shelf.** Shores are sandy by height, slope and name. Names are gone from the grid, so
  sand is read from the colour images: the generator's beach sand, the city's beaches, and the
  range's cove sand under `SAND_BELOW`. The beach town and the lagoon side count as sand by name
  (a build note of the 2026-10-12 re-run: the rule had found 13 of their 123 shore cells sandy).
  Where a shore is sandy, the shelf's own nodes are raised to the equilibrium profile, as C3's
  reshape of the shelf copies did, and beyond the shelf the bed carries the profile on down
  (`DEAN_CARRIES_DOWN`: Christina's fix to C3 as drawn, 2026-10-14).
- **The harbour cove** keeps `FERRY_WATER` of water: coast north's cliff foot in the cove, left at
  -8 by the headland fork, is carried down to the harbour's floor, and the bed beside the cliff
  with it (a build note of the re-run).
- **The bridge's tower footings** (bottoms -15.5) stand on the bed: within `FOOTING_REACH` of each the
  bed is `FOOTING_CLEAR` under the footing's bottom, blending into the bed beyond over
  `FOOTING_BLEND` (a build note of the re-run; the bed was -16.2..-16.8 under them).
- **Colour.** New bed nodes take the shelves' scheme (`shelf_colour` in
  `tools/blender/world_terrain_ground_edit.py`): the generator's beach sand by a sandy shore down to
  -8.5, darkening to the seabed colour by -10.5, and the seabed colour elsewhere, with the shelves'
  grain. Raised shelf nodes take the same.
- **The outer tier** (8 m, beyond the inner tiles' domain) takes the same bed.
- **What the generator builds stays put.** It reads the grid's ground where it builds, so ground
  that had ground before is changed nowhere within `GEN_CLEAR` (60 m) of a held outline or inside
  the towns' or the park's footprints, tapering in over `GEN_TAPER` beyond (`generator_footprints`).
  New sea nodes have no baseline and read as no change.

The report re-measures C3's checks on the grid's bilinear surface: the ferry route, the landings,
the harbour cove, the pier's sides, the sunset bearing, the footings, the park box's bed, the bed's
highest point, the beach town's shore, where the bed meets the ground, and that no ground in the
generator's buffer changed. Nothing here touches `baseline/`, the master, the game's tiles or any
generated scene: the build, mount and regeneration are separate steps.
"""

import datetime
import hashlib
import json
import math
import os
import re
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import ground_bake as gb  # noqa: E402  (the EXR reader and writer)
import ground_colour_bake as gc  # noqa: E402  (the PNG reader and writer)
import ground_grid_edit as gge  # noqa: E402  (the grid, its log and its held outlines)

GROUND = os.path.join(ROOT, "assets", "source", "world_ground")
MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
CITY_SOURCE = os.path.join(ROOT, "assets", "source", "far_shore_city_relocation.blend")
PARK_CSV = os.path.join(ROOT, "documentation", "terrain", "heightfield_park_4m.csv")
EDIT_NAME = "seabed_c3"
EDIT_WHY = "lay seabed C3 (the bay canyon and the south arm) on the sea, with the sandy shelf, the park box's bed and solid footings"

# The sea (the generator's water top); the shelves start this far under it.
SEA = -7.5
START = SEA - 0.5
# The bed lies this far under the ground beside it, and never above `CAP`.
UNDER = 0.05
CAP = -8.05
# The sandy shelf: an equilibrium beach profile, depth ~ distance^(2/3), from the shelf's start to
# `SHELF_DEPTH` `DEAN_16` out.
DEAN_16 = 400.0
SHELF_DEPTH = -16.0
# Today's shelf is kept round the bridge's footings, the ferry's landing heads and its route (inner
# radius, outer radius).
HOLD_FOOTING = (200.0, 320.0)
HOLD_LANDING = (50.0, 90.0)
HOLD_ROUTE = (30.0, 60.0)
# A shore is sandy where the land within `SHORE_REACH` of the waterline stays under `SHORE_LOW` over
# the sea and flatter than `SHORE_SLOPE`, or where `SHORE_NAMED` of it is sand by name.
SHORE_REACH = 32.0
SHORE_LOW = 3.0
SHORE_SLOPE = 0.2
SHORE_NAMED = 0.3
# Shores sandy by name that the colours do not mark (planted to the water): the beach town and the
# lagoon side, from the park's box to the beach front (Godot x, z).
NAMED_SANDY = {"the beach town and the lagoon side": [(-300.0, 265.0), (80.0, 265.0), (80.0, 540.0), (-300.0, 540.0)]}
# Sand by colour (sRGB bytes): the generator's beach sand (`gen_props.gd`, the shelves' `SAND`, with
# its grain); the city's beaches; the range's cove sand and the plug's infill, only under `SAND_BELOW`
# (above it the same colour is a range band).
SAND = (0.78, 0.72, 0.58)
SEABED = (0.47, 0.44, 0.39)
BEACH_RGB = (200.0, 192.0, 160.0)
COVE_RGB = (200.0, 170.0, 130.0)
COLOUR_NEAR = 10.0
SAND_BELOW = -4.0
# The shelves' colour scheme (`world_terrain_ground_edit.py`'s `SEABED_FROM`): sand to -8.5,
# darkening to seabed by -10.5.
SEABED_FROM = (-8.5, -10.5)
# A ferry needs `FERRY_WATER` under its route, across `FERRY_HALF` either side.
FERRY_WATER = 4.0
FERRY_HALF = 30.0
# The bridge's footings: the bed under a tower footing is `FOOTING_CLEAR` under its bottom within
# `FOOTING_REACH` of it, blending into the bed beyond over `FOOTING_BLEND`.
FOOTING_CLEAR = 0.05
FOOTING_REACH = 25.0
FOOTING_BLEND = 25.0
# The harbour cove in the headland's lee and the pier's sides keep `FERRY_WATER` (Godot x, z).
HARBOUR = [(-70.0, -178.0), (-116.0, -168.0), (-178.0, -212.0), (-176.0, -258.0), (-104.0, -252.0), (-68.0, -224.0)]
HARBOUR_REACH = 10.0
PIER_SIDES = 30.0
# The park's west shore: its rebuild footprint grown by this (the park's box).
ZONE_CLEAR = 45.0
# The bed runs this far on under the park's shore box, at its foot; within the first distance of
# that shore the bed's edge height is held to the box's foot, blending out by the second.
OVERLAP = 8.0
PARK_HOLD = (100.0, 250.0)
# The generator reads the grid's ground where it builds (`delta_y`, `road_natural`), so ground the
# seabed changes there moves what it builds (G8, 2026-10-14: the shelf's reshape moved the road
# corridor, an embankment and the north town). No node that had ground is changed within
# `GEN_CLEAR` of a held outline in `holes.json`, or inside the generated towns' or the park's
# footprints (`generator_footprints`); the reshape tapers in over `GEN_TAPER` beyond those.
GEN_CLEAR = 60.0
GEN_TAPER = 40.0
TOWNS_SCENE = os.path.join(ROOT, "scenes", "world", "generated", "park_towns.tscn")
# The bed's own regional and canyon fields reach this far past the land's box.
MARGIN = 4500.0
# Only nodes moved more than this are written.
MIN_CHANGE = 0.001

# Godot plan (x, z) -> the bed's plan (X, Y) = (x, -z), as the C3 proposals worked.


def g2b(x, z):
    return (x, -z)


T_START = time.time()


def log(msg):
    print("[%6.1fs] %s" % (time.time() - T_START, msg), flush=True)


def plan_constant(name):
    """A number written in `scripts/park_plan.gd`."""
    text = open(os.path.join(ROOT, "scripts", "park_plan.gd")).read()
    m = re.search(r"^const %s\s*:?=\s*(-?[0-9.]+)\s*$" % name, text, re.M)
    if m is None:
        raise SystemExit("scripts/park_plan.gd has no number %s" % name)
    return float(m.group(1))


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smin(a, b, k):
    """Polynomial smooth minimum: the lower of a and b, rounded over k."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1.0 - h) + a * h - k * h * (1.0 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


# Beyond a sandy shelf's edge the profile carries on down until the regional depth is deeper
# (Christina, 2026-10-14: "fix the profile"). C3 as drawn on 2026-10-08 had the sign turned, so its
# bed rose from the edge (to about a metre, with the bars) until the regional depth took over;
# False (`--as-drawn`) gives that back. Off the park it moves the sunset bearing's least water from
# 3.9 to 8.4 m and the ferry route's from 5.1 to 7.9 m.
DEAN_CARRIES_DOWN = True


def dean(d):
    """Metres below the shelf's start, `d` metres out, on the sandy profile."""
    return (SHELF_DEPTH - START) * (np.maximum(d, 0.0) / DEAN_16) ** (2.0 / 3.0)


def grain(x, z):
    """The shelves' colour grain at Godot (x, z)."""
    return 1.0 + np.sin(np.asarray(x) * 0.37) * np.sin(np.asarray(z) * 0.41) * 0.05


def shelf_rgb(x, z, y, sandy):
    """The shelves' colour scheme as sRGB bytes: sand by a sandy shore down to -8.5, darkening to the
    seabed colour by -10.5; the seabed colour elsewhere; with the grain."""
    f = np.where(sandy, smoothstep(SEABED_FROM[1], SEABED_FROM[0], y), 0.0)
    c = np.array(SAND)[None, :] * f[:, None] + np.array(SEABED)[None, :] * (1.0 - f[:, None])
    c = c * grain(x, z)[:, None]
    return np.clip(np.floor(c * 255.0), 0, 255).astype(np.uint8)


def box_blur(A, r, axis):
    """A running mean of half-width r cells along one axis, edges clamped."""
    if r < 1:
        return A
    pad = [(0, 0)] * A.ndim
    pad[axis] = (r + 1, r)
    P = np.pad(A, pad, mode="edge")
    C = np.cumsum(P, axis=axis)
    n = A.shape[axis]
    hi = np.take(C, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(C, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * r + 1)


def gaussian(A, sigma_cells):
    """Three box blurs, close to a Gaussian of sigma_cells."""
    r = max(1, int(round(math.sqrt(sigma_cells * sigma_cells + 1.0) - 0.5)))
    for _ in range(3):
        A = box_blur(box_blur(A, r, 0), r, 1)
    return A


def value_noise(seed, cell, X, Y):
    """Smooth value noise in [-1, 1] on a lattice of `cell` metres."""
    rng = np.random.default_rng(seed)
    lat = rng.uniform(-1.0, 1.0, (64, 64))
    gx, gy = X / cell, Y / cell
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - ix, gy - iy
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = lat[iy % 64, ix % 64]
    b = lat[iy % 64, (ix + 1) % 64]
    c = lat[(iy + 1) % 64, ix % 64]
    d = lat[(iy + 1) % 64, (ix + 1) % 64]
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


def maxfilter(A, rad):
    """The largest value within `rad` cells (a square window)."""
    out = A.copy()
    for axis in (0, 1):
        B = out.copy()
        for k in range(1, rad + 1):
            B = np.maximum(B, np.roll(out, k, axis=axis))
            B = np.maximum(B, np.roll(out, -k, axis=axis))
        out = B
    return out


def dilate(M, k):
    """`M` grown by `k` cells, eight-connected."""
    out = M.copy()
    for _ in range(k):
        g = out.copy()
        g[1:, :] |= out[:-1, :]
        g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        g[1:, 1:] |= out[:-1, :-1]
        g[:-1, :-1] |= out[1:, 1:]
        g[1:, :-1] |= out[:-1, 1:]
        g[:-1, 1:] |= out[1:, :-1]
        out = g
    return out


def flood(passable, seeds):
    """Every passable cell joined to a seed, four-connected, by runs along rows and columns."""

    def rows(P, R):
        H, W = P.shape
        start = P & ~np.concatenate([np.zeros((H, 1), bool), P[:, :-1]], axis=1)
        run = np.cumsum(start.ravel()) * P.ravel()
        has = np.zeros(int(run.max()) + 1, bool)
        has[run[R.ravel() & P.ravel()]] = True
        has[0] = False
        return has[run].reshape(H, W)

    reached = seeds & passable
    count = -1
    while reached.sum() != count:
        count = reached.sum()
        reached = rows(passable, reached)
        reached = rows(passable.T.copy(), reached.T.copy()).T
    return reached


def spline(points, step=5.0):
    """A Catmull-Rom course through plan points, sampled every `step` metres, and its arc length."""
    P = np.asarray(points, dtype=float)
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    pts = [P[0]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n = max(2, int(np.linalg.norm(p2 - p1) / step))
        for t in np.arange(1, n + 1) / n:
            pts.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    pts = np.array(pts)
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    return pts, arc


def kdtree(X, Y):
    from mathutils.kdtree import KDTree
    kd = KDTree(len(X))
    for i, (x, y) in enumerate(zip(np.asarray(X).tolist(), np.asarray(Y).tolist())):
        kd.insert((x, y, 0.0), i)
    kd.balance()
    return kd


def nearest(kd, X, Y):
    """Distance to the nearest point of `kd` and its index, for each (X, Y)."""
    X = np.asarray(X, dtype=float).ravel()
    Y = np.asarray(Y, dtype=float).ravel()
    D = np.empty(len(X))
    I = np.empty(len(X), dtype=np.int64)
    find = kd.find
    for k, (x, y) in enumerate(zip(X.tolist(), Y.tolist())):
        _, i, d = find((x, y, 0.0))
        D[k] = d
        I[k] = i
    return D, I


class Course:
    """Distance to a sampled course and the arc length at its nearest point."""

    def __init__(self, points_godot, step=5.0):
        self.pts, self.arc = spline([g2b(x, z) for x, z in points_godot], step)
        self.kd = kdtree(self.pts[:, 0], self.pts[:, 1])
        self.box = (self.pts[:, 0].min(), self.pts[:, 0].max(), self.pts[:, 1].min(), self.pts[:, 1].max())
        self.length = float(self.arc[-1])

    def query(self, X, Y, reach):
        X = np.asarray(X, dtype=float)
        Y = np.asarray(Y, dtype=float)
        d = np.full(len(X), np.inf)
        s = np.zeros(len(X))
        b = self.box
        near = np.nonzero((X > b[0] - reach) & (X < b[1] + reach) & (Y > b[2] - reach) & (Y < b[3] + reach))[0]
        if len(near):
            dd, ii = nearest(self.kd, X[near], Y[near])
            d[near] = dd
            s[near] = self.arc[ii]
        return d, s


def polyline_distance(P, X, Y):
    """Distance from each (X, Y) to the plan polyline P (n, 2), and the arc length at the nearest point."""
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    A = P[:-1]
    AB = P[1:] - A
    L2 = np.maximum((AB ** 2).sum(axis=1), 1e-9)
    cum = np.concatenate([[0.0], np.cumsum(np.sqrt(L2))])
    best = np.full(X.shape, np.inf)
    s = np.zeros(X.shape)
    for i in range(len(A)):
        u = np.clip(((X - A[i, 0]) * AB[i, 0] + (Y - A[i, 1]) * AB[i, 1]) / L2[i], 0.0, 1.0)
        d = np.hypot(X - (A[i, 0] + u * AB[i, 0]), Y - (A[i, 1] + u * AB[i, 1]))
        m = d < best
        best[m] = d[m]
        s[m] = cum[i] + u[m] * math.sqrt(L2[i])
    return best, s


def polygon_signed_distance(poly, X, Y):
    """Positive inside the closed plan polygon, negative outside, in metres."""
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    P = np.asarray(list(poly) + [poly[0]])
    d, _ = polyline_distance(P, X, Y)
    inside = np.zeros(X.shape, bool)
    for i in range(len(P) - 1):
        (x0, y0), (x1, y1) = P[i], P[i + 1]
        c = ((y0 > Y) != (y1 > Y)) & (X < (x1 - x0) * (Y - y0) / np.where(y1 == y0, 1e-9, y1 - y0) + x0)
        inside ^= c
    return np.where(inside, d, -d)


def bilinear(A, x0, y0, h, X, Y):
    H, W = A.shape
    gx = np.clip((X - x0) / h, 0, W - 1.001)
    gy = np.clip((Y - y0) / h, 0, H - 1.001)
    i, j = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - i, gy - j
    return (A[j, i] * (1 - fx) + A[j, i + 1] * fx) * (1 - fy) + (A[j + 1, i] * (1 - fx) + A[j + 1, i + 1] * fx) * fy


# --- the grid ---------------------------------------------------------------------------------------

def file_sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


class Inner:
    """The grid's 2 m tier as one array: row r at z = z0 + step r, column c at x = x0 + step c. A tile
    with no file holds no ground. Each file's hash is kept, so a write can refuse if one changed."""

    def __init__(self, root):
        self.root = root
        self.g = gge.Grid(root)
        self.step, self.n, self.per = self.g.step, self.g.n, self.g.per
        self.x0 = self.g.tx[0] * self.g.tile_m
        self.z0 = self.g.tz[0] * self.g.tile_m
        nx = len(self.g.tx) * self.per + 1
        nz = len(self.g.tz) * self.per + 1
        self.H = np.full((nz, nx), np.nan, np.float32)
        self.C = np.zeros((nz, nx, 4), np.uint8)
        self.tiles = [(tx, tz) for tz in self.g.tz for tx in self.g.tx]
        self.hashes = {}
        for (tx, tz) in self.tiles:
            r, c = self.at_tile(tx, tz)
            hp = self.g.path("height", tx, tz, "exr")
            cp = self.g.path("colour", tx, tz, "png")
            self.hashes[hp] = file_sha(hp)
            self.hashes[cp] = file_sha(cp)
            if os.path.exists(hp):
                self.H[r, c] = gb.read_exr(hp)[0]
            if os.path.exists(cp):
                self.C[r, c] = gc.png_read(cp)
        self.xs = self.x0 + self.step * np.arange(nx)
        self.zs = self.z0 + self.step * np.arange(nz)
        self.box = (self.xs[0], self.xs[-1], self.zs[0], self.zs[-1])

    def at_tile(self, tx, tz):
        r0 = (tz - self.g.tz[0]) * self.per
        c0 = (tx - self.g.tx[0]) * self.per
        return slice(r0, r0 + self.n), slice(c0, c0 + self.n)

    def rc(self, x, z):
        return int(round((z - self.z0) / self.step)), int(round((x - self.x0) / self.step))


class Outer:
    """The grid's 8 m sea tier (`grid.json`'s `outer`, `outer/height/` and `outer/colour/`), as one
    array; only its nodes beyond the inner tier's domain are its own (`own`)."""

    def __init__(self, root, inner):
        spec = json.load(open(os.path.join(root, "grid.json")))["outer"]
        self.step = float(spec["spacing_m"])
        self.n = int(spec["tile_samples"])
        self.per = self.n - 1
        self.tile_m = float(spec["tile_m"])
        self.tx = range(spec["tiles_x"][0], spec["tiles_x"][1] + 1)
        self.tz = range(spec["tiles_z"][0], spec["tiles_z"][1] + 1)
        self.x0, self.z0 = self.tx[0] * self.tile_m, self.tz[0] * self.tile_m
        nx = len(self.tx) * self.per + 1
        nz = len(self.tz) * self.per + 1
        self.H = np.full((nz, nx), np.nan, np.float32)
        self.hashes = {}
        for tz in self.tz:
            for tx in self.tx:
                hp = os.path.join(root, "outer", "height", "x%d_z%d.exr" % (tx, tz))
                cp = os.path.join(root, "outer", "colour", "x%d_z%d.png" % (tx, tz))
                self.hashes[hp] = file_sha(hp)
                self.hashes[cp] = file_sha(cp)
                if os.path.exists(hp):
                    r0, c0 = (tz - self.tz[0]) * self.per, (tx - self.tx[0]) * self.per
                    self.H[r0:r0 + self.n, c0:c0 + self.n] = gb.read_exr(hp)[0]
        self.xs = self.x0 + self.step * np.arange(nx)
        self.zs = self.z0 + self.step * np.arange(nz)
        XS, ZS = np.meshgrid(self.xs, self.zs)
        b = inner.box
        self.own = ~((XS >= b[0]) & (XS <= b[1]) & (ZS >= b[2]) & (ZS <= b[3]))

    def with_inner(self, H, inner):
        """This tier's heights with the inner tier's (`H`) at its nodes inside the inner domain, so a
        cell across the seam has its four corners (for drawing only; those nodes are the inner's)."""
        out = self.H.copy()
        r, c = np.nonzero(~self.own)
        ir = np.rint((self.zs[r] - inner.z0) / inner.step).astype(int)
        ic = np.rint((self.xs[c] - inner.x0) / inner.step).astype(int)
        out[r, c] = H[ir, ic]
        return out


# --- the sea as the grid leaves it ------------------------------------------------------------------

def named_sand(C, H):
    """Sand by colour at each node (see `BEACH_RGB`): the generator's beach sand with its grain, the
    city's beaches, and the range's cove sand under `SAND_BELOW`."""
    rgb = C[..., :3].astype(np.float32)
    ground = C[..., 3] == 255
    ratio = rgb / (np.array(SAND, np.float32) * 255.0)
    sand = (ratio.max(-1) - ratio.min(-1) < 0.04) & (ratio.mean(-1) > 0.93) & (ratio.mean(-1) < 1.07)
    beach = np.abs(rgb - np.array(BEACH_RGB, np.float32)).max(-1) <= COLOUR_NEAR
    with np.errstate(invalid="ignore"):
        cove = (np.abs(rgb - np.array(COVE_RGB, np.float32)).max(-1) <= COLOUR_NEAR) & (H < SAND_BELOW)
    return ground & (sand | beach | cove)


class GridSea:
    """The sea the grid leaves, its edges, and the smooth fields the bed reads, as C3's `Sea` read
    the master: an edge is a node with ground beside a sea node. Plan positions are the bed's
    (X, Y) = (x, -z)."""

    second = True

    def __init__(self, inner, ctx):
        t0 = time.time()
        self.inner = inner
        self.ctx = ctx
        self.feet = generator_footprints(inner.root)
        H = inner.H
        self.report = {}
        nan = np.isnan(H)
        # the park's box, where only the water the park's collision shows is sea
        zx0 = plan_constant("REBUILD_FOOTPRINT_MIN_X") - ZONE_CLEAR
        zx1 = plan_constant("REBUILD_FOOTPRINT_MAX_X") + ZONE_CLEAR
        zz0 = plan_constant("REBUILD_FOOTPRINT_MIN_Z") - ZONE_CLEAR
        zz1 = plan_constant("REBUILD_FOOTPRINT_MAX_Z") + ZONE_CLEAR
        self.zone = (zx0, zx1, -zz1, -zz0)
        self.shore_edge_x = plan_constant("SHORE_EDGE")
        self.load_park()
        zone = np.zeros(H.shape, bool)
        r0, c0 = int(math.ceil((zz0 - inner.z0) / inner.step)), int(math.ceil((zx0 - inner.x0) / inner.step))
        r1, c1 = int(math.floor((zz1 - inner.z0) / inner.step)), int(math.floor((zx1 - inner.x0) / inner.step))
        zone[r0:r1 + 1, c0:c1 + 1] = True
        XS, ZS = np.meshgrid(inner.xs[c0:c1 + 1], inner.zs[r0:r1 + 1])
        water, inside = self.park_at(XS, -ZS, self.pk_water)
        not_water = zone.copy()
        not_water[r0:r1 + 1, c0:c1 + 1] = ~(inside & water)
        self.held = gge._held_mask(inner.g, H.shape, inner.x0, inner.z0)
        passable = nan & ~self.held & ~not_water
        seeds = np.zeros(H.shape, bool)
        seeds[0, :] = seeds[-1, :] = seeds[:, 0] = seeds[:, -1] = True
        self.sea = flood(passable, seeds)
        # the park's own shore (no ground of the grid's, not water): the bed runs on under it, at the
        # shore box's foot, `OVERLAP` in from the water
        park_land = zone & nan & ~self.held & ~self.sea
        zone_sea = self.sea & zone
        self.park_ring = park_land & dilate(zone_sea, 1)
        self.overlap = park_land & dilate(zone_sea, int(round(OVERLAP / inner.step)))
        self.bed = self.sea | self.overlap
        ground = ~nan
        self.edge = ground & dilate(self.bed, 1)
        self.report["sea"] = {"sea_nodes": int(self.sea.sum()), "overlap_nodes": int(self.overlap.sum()),
                              "edge_nodes": int(self.edge.sum()), "held_nodes_without_ground": int((self.held & nan).sum()),
                              "enclosed_no_data_nodes_left": int((nan & ~self.held & ~self.bed).sum())}
        # the edges: each edge node, its height, and the way out to the sea beside it
        er, ec = np.nonzero(self.edge)
        out = np.zeros((len(er), 2))
        nz, nx = H.shape
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if not (dr or dc):
                    continue
                rr, cc = er + dr, ec + dc
                ok = (rr >= 0) & (rr < nz) & (cc >= 0) & (cc < nx)
                hit = np.zeros(len(er), bool)
                hit[ok] = self.bed[rr[ok], cc[ok]]
                v = np.array([dc, -dr], float) / math.hypot(dc, dr)
                out[hit] += v
        out /= np.maximum(np.linalg.norm(out, axis=1), 1e-9)[:, None]
        self.edge_rc = (er, ec)
        self.es_x = inner.xs[ec].astype(float)
        self.es_y = -inner.zs[er].astype(float)
        self.es_z = H[er, ec].astype(float)
        self.es_out = out
        # the park's shore: at the shore box's foot, sand, on the gentle profile from where it has
        # fallen to the foot
        pr, pc = np.nonzero(self.park_ring)
        self.pk_rc = (pr, pc)
        self.b_x = np.concatenate([self.es_x, inner.xs[pc]])
        self.b_y = np.concatenate([self.es_y, -inner.zs[pr]])
        self.n_e = len(self.es_x)
        self.b_park = np.concatenate([np.zeros(self.n_e, bool), np.ones(len(pr), bool)])
        self.b_e = np.concatenate([self.es_z, np.full(len(pr), self.box_bottom)])
        self.b_d0 = np.concatenate([np.full(self.n_e, 60.0), np.full(len(pr), self.park_d0)])
        self.kd = kdtree(self.b_x, self.b_y)
        self.pk_kd = kdtree(inner.xs[pc], -inner.zs[pr]) if len(pr) else None
        lr, lc = np.nonzero(ground)
        self.land_box = (inner.xs[lc].min(), inner.xs[lc].max(), -inner.zs[lr].max(), -inner.zs[lr].min())
        self.raster()
        self.shore_raster()
        self.sandiness()
        self.edge_fields()
        self.report["analysis_s"] = round(time.time() - t0, 1)

    # -- the park, from the game's collision
    def load_park(self):
        """Which 4 m samples of the park's collision are water (no collision at all, or a deck the
        generator stands in the sea: the pier, its pavilion, the wheel's jetty), and the top there."""
        import csv
        xs, zs, top, water, struct = [], [], [], [], []
        edge_x = self.shore_edge_x
        for r in csv.DictReader(open(PARK_CSV)):
            x, z = float(r["x"]), float(r["z"])
            kind = r["kind"]
            owner = (r["top_owner"] + "|" + r["ground_owner"]).lower()
            on_piles = kind != "open" and "terrain" not in r["ground_owner"] and (
                "pier_deck" in owner or "wheel_deck" in owner or ("authored_additions" in owner and x < edge_x - 8.0))
            xs.append(x)
            zs.append(z)
            top.append(float(r["top_y"]) if r["top_y"] else np.nan)
            water.append(kind == "open" or on_piles)
            struct.append(on_piles)
        self.pk_x0, self.pk_z0 = min(xs), min(zs)
        nx = int(round((max(xs) - self.pk_x0) / 4.0)) + 1
        nz = int(round((max(zs) - self.pk_z0) / 4.0)) + 1
        self.pk_top = np.full((nz, nx), np.nan)
        self.pk_water = np.zeros((nz, nx), bool)
        self.pk_struct = np.zeros((nz, nx), bool)
        ix = np.rint((np.array(xs) - self.pk_x0) / 4.0).astype(int)
        iz = np.rint((np.array(zs) - self.pk_z0) / 4.0).astype(int)
        self.pk_top[iz, ix] = top
        self.pk_water[iz, ix] = water
        self.pk_struct[iz, ix] = struct
        self.box_bottom = plan_constant("SHORE_TOP") - 6.0
        # where the gentle profile has fallen to the shore box's foot, so it runs on from there
        self.park_d0 = DEAN_16 * ((START - self.box_bottom) / (START - SHELF_DEPTH)) ** 1.5

    def park_at(self, X, Y, grid):
        """A park sample's value at (X, Y), and whether it is inside the sampled box."""
        ix = np.rint((np.asarray(X) - self.pk_x0) / 4.0).astype(int)
        iz = np.rint((-np.asarray(Y) - self.pk_z0) / 4.0).astype(int)
        nz, nx = grid.shape
        inside = (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz)
        return grid[np.clip(iz, 0, nz - 1), np.clip(ix, 0, nx - 1)], inside

    def in_zone(self, X, Y):
        z = self.zone
        X = np.asarray(X)
        Y = np.asarray(Y)
        return (X >= z[0]) & (X <= z[1]) & (Y >= z[2]) & (Y <= z[3])

    # -- every other node, 4 m: the reefs' and the shore's raster, rows by Y = -z ascending
    def raster(self):
        inner = self.inner
        s = slice(None, None, 2)
        T = inner.H[s, s][::-1]
        self.F = ~np.isnan(T)
        self.Ftop = T
        self.seamask = self.sea[s, s][::-1]
        self.corridor = self.held[s, s][::-1]
        self.Fnamed = named_sand(inner.C[s, s][::-1], T)
        self.rxs = inner.xs[::2].astype(float)
        self.rys = -inner.zs[::2][::-1].astype(float)
        self.rx0, self.ry0 = self.rxs[0] - 2.0, self.rys[0] - 2.0

    def cell(self, X, Y):
        i = np.floor((np.asarray(X) - self.rx0) / 4.0).astype(int)
        j = np.floor((np.asarray(Y) - self.ry0) / 4.0).astype(int)
        inside = (i >= 0) & (i < self.F.shape[1]) & (j >= 0) & (j < self.F.shape[0])
        return np.clip(i, 0, self.F.shape[1] - 1), np.clip(j, 0, self.F.shape[0] - 1), inside

    def is_sea(self, X, Y):
        i, j, inside = self.cell(X, Y)
        return np.where(inside, self.seamask[j, i], True)

    def nearest(self, X, Y):
        """Distance to the nearest point that starts the seabed, and its index."""
        return nearest(self.kd, X, Y)

    def shore_raster(self):
        """Sandy or rocky, per 4 m cell, by the land within `SHORE_REACH` of it: low and gentle, or
        sand by name (its colour); and the named shores (`NAMED_SANDY`)."""
        r = int(round(SHORE_REACH / 4.0))
        T = np.where(self.F, self.Ftop, np.nan).astype(float)
        land = self.F & (np.nan_to_num(T, nan=-1e9) > SEA)
        X, Y = np.meshgrid(self.rxs, self.rys)
        ptop, inside = self.park_at(X, Y, self.pk_top)
        pw, _ = self.park_at(X, Y, self.pk_water)
        park_land = inside & ~self.F & ~pw & ~np.isnan(ptop) & (np.nan_to_num(ptop, nan=-1e9) > SEA)
        T = np.where(park_land, ptop, T)
        land = land | park_land
        top_land = np.where(land, T, -1e9)
        maxtop = maxfilter(top_land, r)
        has_land = maxfilter(land.astype(np.int8), r) > 0
        d = np.zeros(T.shape)
        Tz = np.nan_to_num(T, nan=0.0)
        for axis in (0, 1):
            for k in (1, -1):
                Tn = np.roll(Tz, k, axis=axis)
                Ln = np.roll(land, k, axis=axis)
                d = np.maximum(d, np.where(land & Ln, np.abs(Tz - Tn), 0.0))
        maxslope = maxfilter(d / 4.0, r)
        named = (self.Fnamed & land).astype(float)
        cnt = box_blur(box_blur(land.astype(float), r, 0), r, 1)
        frac = box_blur(box_blur(named, r, 0), r, 1) / np.maximum(cnt, 1e-9)
        geom = (maxtop <= SEA + SHORE_LOW) & (maxslope < SHORE_SLOPE)
        by_name = frac >= SHORE_NAMED
        listed = np.zeros(T.shape, bool)
        for poly in NAMED_SANDY.values():
            listed |= polygon_signed_distance([g2b(x, z) for x, z in poly], X, Y) > 0.0
        self.sandy_r = has_land & (geom | by_name | listed)
        self.sandy_why = np.where(geom, 1, 0) + np.where(by_name, 2, 0) + np.where(listed, 4, 0)
        self.land_r = land
        # the shore itself: land cells beside water or under-water ground that face the sea
        water = (~self.F | (self.F & (np.nan_to_num(T, nan=-1e9) <= SEA))) & ~land
        nb = np.zeros(T.shape, bool)
        for axis in (0, 1):
            for k in (1, -1):
                nb |= np.roll(water, k, axis=axis)
        near = maxfilter(self.seamask.astype(np.int8), 30) > 0
        self.shore_cells = land & nb & near & ~self.corridor
        js, is_ = np.nonzero(self.shore_cells)
        new = self.sandy_r[js, is_]
        why = self.sandy_why[js, is_]
        self.report["shore_km"] = {
            "cells_are_4m": True, "sandy": round(new.sum() * 4.0 / 1000, 2), "rocky": round((~new).sum() * 4.0 / 1000, 2),
            "sandy_by_height_and_slope": round(((why & 1) > 0).sum() * 4.0 / 1000, 2),
            "sandy_by_colour": round(((why & 2) > 0).sum() * 4.0 / 1000, 2),
            "sandy_by_the_named_list": round(((why & 4) > 0).sum() * 4.0 / 1000, 2)}
        town = polygon_signed_distance([g2b(x, z) for x, z in NAMED_SANDY["the beach town and the lagoon side"]],
                                       self.rxs[is_], self.rys[js]) > 0.0
        self.report["beach_town_shore_cells"] = {"cells": int(town.sum()), "sandy": int(new[town].sum()),
                                                 "sandy_without_the_named_list": int((((why & 3) > 0) & town).sum())}

    def classify(self, X, Y):
        """Sandy (True) or rocky at points on or near the shore."""
        i, j, inside = self.cell(np.asarray(X, float).ravel(), np.asarray(Y, float).ravel())
        return np.where(inside, self.sandy_r[j, i], False)

    def sandiness(self):
        """Each edge node's shore, sandy or rocky: looking back from the edge to the first land, then
        smoothed along the shore over 60 m. The park's shore is sand."""
        n_e = self.n_e
        out = np.concatenate([self.es_out, np.zeros((len(self.b_x) - n_e, 2))])
        sand = np.zeros(len(self.b_x))
        found = np.zeros(len(self.b_x), bool)
        for t in np.arange(0.0, 200.0, 4.0):
            i, j, inside = self.cell(self.b_x - out[:, 0] * t, self.b_y - out[:, 1] * t)
            hit = inside & ~found & self.land_r[j, i]
            sand = np.where(hit, self.sandy_r[j, i].astype(float), sand)
            found |= hit
        sand[n_e:] = 1.0
        kd = self.kd
        self.b_sand = np.array([np.mean([sand[i] for _, i, _ in kd.find_range((x, y, 0.0), 30.0)])
                                for x, y in zip(self.b_x.tolist(), self.b_y.tolist())])
        self.report["edge_nodes_sandy"] = round(float((self.b_sand > 0.5).mean()), 3)
        # the sand field, splatted and blurred on 10 m
        d0, d1, e0, e1 = self.land_box
        self.fx0, self.fy0, self.fh = d0 - 1500.0, e0 - 1500.0, 10.0
        W = int((d1 - d0 + 3000.0) / self.fh) + 1
        Hh = int((e1 - e0 + 3000.0) / self.fh) + 1
        self.fi = np.clip(((self.b_x - self.fx0) / self.fh).astype(int), 0, W - 1)
        self.fj = np.clip(((self.b_y - self.fy0) / self.fh).astype(int), 0, Hh - 1)
        w = np.zeros((Hh, W))
        ws = np.zeros((Hh, W))
        np.add.at(w, (self.fj, self.fi), 1.0)
        np.add.at(ws, (self.fj, self.fi), self.b_sand)
        gw = gaussian(w, 8.0)
        self.sand_field = np.where(gw > 1e-6, gaussian(ws, 8.0) / np.maximum(gw, 1e-9), 0.0)
        self.fshape = (Hh, W)

    def edge_fields(self):
        """The edge's height and its distance from its shelf's start, blurred on 10 m."""
        Hh, W = self.fshape
        w = np.zeros((Hh, W))
        we = np.zeros((Hh, W))
        wd = np.zeros((Hh, W))
        np.add.at(w, (self.fj, self.fi), 1.0)
        np.add.at(we, (self.fj, self.fi), self.b_e)
        np.add.at(wd, (self.fj, self.fi), self.b_d0)
        gw = gaussian(w, 4.0)
        self.e_field = np.where(gw > 1e-6, gaussian(we, 4.0) / np.maximum(gw, 1e-9), SHELF_DEPTH)
        self.d0_field = np.where(gw > 1e-6, gaussian(wd, 4.0) / np.maximum(gw, 1e-9), 60.0)

    def land_distance(self, domain):
        """The distance to land on 25 m over `domain` (X0, X1, Y0, Y1), blurred, for the regional
        depth. The park's own west shore counts as land, 60 m off its edge."""
        x0, x1, y0, y1 = domain
        self.dh = 25.0
        self.dx0, self.dy0 = x0, y0
        W = int((x1 - x0) / self.dh) + 1
        Hh = int((y1 - y0) / self.dh) + 1
        zs = np.arange(-70.0, 71.0, 10.0)
        px = np.concatenate([self.b_x, np.full(len(zs), self.shore_edge_x - 60.0)])
        py = np.concatenate([self.b_y, -zs])
        kd = kdtree(px, py)
        X, Y = np.meshgrid(x0 + np.arange(W) * self.dh, y0 + np.arange(Hh) * self.dh)
        Dl, _ = nearest(kd, X.ravel(), Y.ravel())
        Dl = Dl.reshape(X.shape)
        # on the grid's ground the distance is nought
        inner = self.inner
        c = np.rint((X - inner.x0) / inner.step).astype(int)
        r = np.rint((-Y - inner.z0) / inner.step).astype(int)
        ok = (c >= 0) & (c < inner.H.shape[1]) & (r >= 0) & (r < inner.H.shape[0])
        on = np.zeros(X.shape, bool)
        on[ok] = ~np.isnan(inner.H[r[ok], c[ok]])
        Dl = np.where(on, 0.0, Dl)
        self.Dl = gaussian(Dl, 8.0)

    def sample(self, X, Y):
        """What the bed reads at (X, Y): the distance to the edge, the edge's height and distance from
        its shelf's start, sandiness, and the smoothed distance to land."""
        X = np.asarray(X, dtype=float).ravel()
        Y = np.asarray(Y, dtype=float).ravel()
        D, I = self.nearest(X, Y)
        t = smoothstep(0.0, 12.0, D)
        e = self.b_e[I] * (1 - t) + bilinear(self.e_field, self.fx0, self.fy0, self.fh, X, Y) * t
        # the park box's own bed starts at the shore box's foot and only falls from it: near the
        # park's shore the edge's height is no higher than that foot (the field's blur of the coast's
        # shallower edges would otherwise raise it towards the pier)
        if self.pk_kd is not None:
            Dp, _ = nearest(self.pk_kd, X, Y)
            w = 1.0 - smoothstep(PARK_HOLD[0], PARK_HOLD[1], Dp)
            e = e * (1 - w) + np.minimum(e, self.box_bottom) * w
        d0 = self.b_d0[I] * (1 - t) + bilinear(self.d0_field, self.fx0, self.fy0, self.fh, X, Y) * t
        sand = bilinear(self.sand_field, self.fx0, self.fy0, self.fh, X, Y)
        Dl = bilinear(self.Dl, self.dx0, self.dy0, self.dh, X, Y)
        return {"D": D, "e": np.minimum(e, CAP + UNDER), "d0": d0, "sand": np.clip(sand, 0, 1), "Dl": Dl}


# --- the sandy shelf and the harbour: changes to ground the grid has --------------------------------

def hold_field(ctx, X, Y):
    """1 where today's shelf is kept (round the bridge's footings, the ferry's landing heads and its
    route), 0 where the sandy reshape applies, smooth between."""
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    h = np.zeros(X.shape)
    for (fx0, fx1, fy0, fy1, _) in ctx["footings"]:
        dx = np.maximum(np.maximum(fx0 - X, X - fx1), 0.0)
        dy = np.maximum(np.maximum(fy0 - Y, Y - fy1), 0.0)
        h = np.maximum(h, 1 - smoothstep(*HOLD_FOOTING, np.hypot(dx, dy)))
    for hx, hy in ctx["landing_heads"]:
        h = np.maximum(h, 1 - smoothstep(*HOLD_LANDING, np.hypot(X - hx, Y - hy)))
    d, _ = polyline_distance(ctx["ferry"], X, Y)
    return np.maximum(h, 1 - smoothstep(*HOLD_ROUTE, d))


def generator_footprints(root):
    """Where the generator builds on the grid's ground, as plan shapes (Godot x, z): the held
    outlines of `holes.json` sampled every metre (kept `GEN_CLEAR` clear); the park's rebuild
    footprint (`ParkPlan.REBUILD_FOOTPRINT_*`); the towns: `grid.json`'s north town, beach town and
    city outlines (`ParkPlan.north_town_outline()`, `BEACH_TOWN_OUTLINE`, the city blocks' hull) and
    the plan box of every street and lot mesh `park_towns.tscn` holds inline (its buildings are in
    those outlines)."""
    holes = json.load(open(os.path.join(root, "holes.json")))
    pts, owner = [], []
    for body in holes["holes"]:
        for ch in body["chains"]:
            P = np.array([(p[0], p[2]) for p in ch["points"]], float)
            n = len(P)
            for e in range(n if ch["closed"] else n - 1):
                a, b = P[e], P[(e + 1) % n]
                k = max(1, int(math.ceil(float(np.hypot(*(b - a))))))
                pts.append(a + (b - a) * (np.arange(k) / k)[:, None])
                owner += [body["name"].split("/")[-1]] * k
    outline = np.concatenate(pts)
    polys = {}
    for z in json.load(open(os.path.join(root, "grid.json")))["tolerance_zones"]["zones"]:
        for name, poly in z.get("polygons", {}).items():
            polys[name] = [tuple(p) for p in poly]
    boxes = {"park": (plan_constant("REBUILD_FOOTPRINT_MIN_X"), plan_constant("REBUILD_FOOTPRINT_MAX_X"),
                      plan_constant("REBUILD_FOOTPRINT_MIN_Z"), plan_constant("REBUILD_FOOTPRINT_MAX_Z"))}
    if os.path.exists(TOWNS_SCENE):
        for k, m in enumerate(re.finditer(r'"aabb": AABB\(([^)]*)\)', open(TOWNS_SCENE).read())):
            x, y, z, sx, sy, sz = (float(v) for v in m.group(1).split(","))
            if sx < 400.0 and sz < 400.0:  # a street or a lot; one mesh's box spans both towns
                boxes["town_mesh_%d" % k] = (x, x + sx, z, z + sz)
    return {"outline": outline, "owner": np.array(owner), "polygons": polys, "boxes": boxes}


def generator_weight(feet, sea, x, z):
    """Per node (Godot x, z): 0 within `GEN_CLEAR` of a held outline or inside a footprint, rising to
    1 over `GEN_TAPER` beyond; and which kept it lowest."""
    x = np.asarray(x, float)
    z = np.asarray(z, float)
    if not hasattr(sea, "outline_kd"):
        sea.outline_kd = kdtree(feet["outline"][:, 0], feet["outline"][:, 1])
    d, i = nearest(sea.outline_kd, x, z)
    w = smoothstep(GEN_CLEAR, GEN_CLEAR + GEN_TAPER, d)
    which = np.where(w < 1.0, feet["owner"][i], "")
    for name, poly in feet["polygons"].items():
        dist = np.maximum(-polygon_signed_distance(poly, x, z), 0.0)
        wp = smoothstep(0.0, GEN_TAPER, dist)
        which = np.where(wp < w, name, which)
        w = np.minimum(w, wp)
    for name, (x0, x1, z0, z1) in feet["boxes"].items():
        dist = np.hypot(np.maximum(np.maximum(x0 - x, x - x1), 0.0), np.maximum(np.maximum(z0 - z, z - z1), 0.0))
        wp = smoothstep(0.0, GEN_TAPER, dist)
        which = np.where(wp < w, "town streets" if name.startswith("town_mesh") else name, which)
        w = np.minimum(w, wp)
    return w, which


def harbour_region(X, Y):
    """The harbour cove and `HARBOUR_REACH` round it."""
    return polygon_signed_distance([g2b(x, z) for x, z in HARBOUR], X, Y) > -HARBOUR_REACH


def reshape_shelves(sea, ctx, H):
    """The sandy shelf on the grid: where the shore is sandy, the shelves' nodes under the water are
    raised to the equilibrium profile `dean` from the shelf's start, as C3's reshape of the shelf
    copies did; only ever raised, never above the start; held off round the footings, the landings
    and the ferry's route. The shelves are the ground under `START` outside the park's box and the
    harbour, gentler than 1:1; their start, the ground at the start beside them. Changes `H` in place;
    returns every reshaped node's (rows, cols, distance from the start), the raised nodes' new
    colours, and a report."""
    inner = sea.inner
    nan = np.isnan(H)
    with np.errstate(invalid="ignore"):
        under = ~nan & (H < START - 0.005)
    ur, uc = np.nonzero(under)
    x, y = inner.xs[uc].astype(float), -inner.zs[ur].astype(float)
    Hz = np.where(nan, 0.0, H)
    nz, nx = H.shape
    def at(r, c):
        return Hz[np.clip(r, 0, nz - 1), np.clip(c, 0, nx - 1)].astype(float)
    slope = np.hypot(at(ur, uc + 1) - at(ur, uc - 1), at(ur + 1, uc) - at(ur - 1, uc)) / (2 * inner.step)
    ok = (slope < 1.0) & ~sea.in_zone(x, y) & ~harbour_region(x, y)
    shelf = np.zeros(H.shape, bool)
    shelf[ur[ok], uc[ok]] = True
    with np.errstate(invalid="ignore"):
        start = ~nan & (H >= START - 0.02) & dilate(shelf, 1)
    sr, sc = np.nonzero(start)
    P = np.column_stack([inner.xs[sc], -inner.zs[sr]]).astype(float)
    Z = np.minimum(H[sr, sc].astype(float), START)
    Fl = sea.classify(P[:, 0], P[:, 1]).astype(float)
    kd = kdtree(P[:, 0], P[:, 1])
    W = np.array([np.mean([Fl[i] for _, i, _ in kd.find_range((px, py, 0.0), 80.0)]) for px, py in P.tolist()])
    rr, cc = ur[ok], uc[ok]
    x, y = x[ok], y[ok]
    d, idx = nearest(kd, x, y)
    z = H[rr, cc].astype(float)
    e = Z[idx]
    target = e - (e - SHELF_DEPTH) * np.clip(d / DEAN_16, 0, None) ** (2.0 / 3.0)
    free = smoothstep(0.3, 0.7, W[idx]) * (1 - hold_field(ctx, x, y))
    gen, which = generator_weight(sea.feet, sea, x, -y)
    weight = free * gen
    new = np.maximum(np.minimum(z + weight * np.maximum(target - z, 0.0), START), z)
    raised = new - z
    moved = raised > MIN_CHANGE
    # what the buffer spared: nodes the reshape would have raised that it now raises less or not at all
    would = np.maximum(np.minimum(z + free * np.maximum(target - z, 0.0), START), z) - z
    spared = (would > MIN_CHANGE) & (would - raised > MIN_CHANGE)
    whole = spared & ~moved
    by = {}
    for name in sorted(set(which[spared].tolist())):
        k = spared & (which == name)
        cells = {}
        for cx, cz in zip((np.floor(x[k] / 500.0) * 500).astype(int).tolist(), (np.floor(-y[k] / 500.0) * 500).astype(int).tolist()):
            cells[(cx, cz)] = cells.get((cx, cz), 0) + 1
        by[name] = {"nodes": int(k.sum()), "untouched": int((k & whole).sum()),
                    "would_have_risen_m": round(float(would[k].max()), 2),
                    "in_500m_cells_x_z": [[cx, cz, n] for (cx, cz), n in sorted(cells.items(), key=lambda kv: -kv[1])]}
    H[rr[moved], cc[moved]] = new[moved].astype(np.float32)
    keep = weight > 0.02
    d0 = (rr[keep], cc[keep], d[keep])
    paint = moved & (weight > 0.3)
    colours = (rr[paint], cc[paint], shelf_rgb(x[paint], -y[paint], new[paint], np.ones(int(paint.sum()), bool)))
    report = {"shelf_nodes": int(len(rr)), "start_nodes": int(len(sr)),
              "start_nodes_sandy": int((smoothstep(0.3, 0.7, W) > 0.5).sum()),
              "nodes_raised": int(moved.sum()), "raised_max_m": round(float(raised.max()) if len(raised) else 0.0, 2),
              "area_raised_ha": round(float(moved.sum()) * inner.step ** 2 / 1e4, 1), "nodes_recoloured": int(paint.sum()),
              "spared_by_the_generator_buffer": {"nodes": int(spared.sum()), "untouched": int(whole.sum()),
                                                 "tapered": int((spared & moved).sum()), "by": by}}
    return d0, colours, report


def lower_harbour(sea, H):
    """Coast north's cliff foot in the harbour cove, left at -8 by the headland fork, carried down to
    the harbour's floor: every node of ground under the water in the cove (and `HARBOUR_REACH` round
    it) shallower than `FERRY_WATER` (and `UNDER`) is lowered to it. Changes `H` in place."""
    inner = sea.inner
    floor = SEA - FERRY_WATER - UNDER
    xs = [p[0] for p in HARBOUR]
    zs = [p[1] for p in HARBOUR]
    r0, c0 = inner.rc(min(xs) - HARBOUR_REACH - 2, min(zs) - HARBOUR_REACH - 2)
    r1, c1 = inner.rc(max(xs) + HARBOUR_REACH + 2, max(zs) + HARBOUR_REACH + 2)
    sub = H[r0:r1 + 1, c0:c1 + 1]
    XS, ZS = np.meshgrid(inner.xs[c0:c1 + 1], inner.zs[r0:r1 + 1])
    with np.errstate(invalid="ignore"):
        foot = ~np.isnan(sub) & (sub < SEA) & (sub > floor) & harbour_region(XS, -ZS)
    rr, cc = np.nonzero(foot)
    rr, cc = rr + r0, cc + c0
    gen, _ = generator_weight(sea.feet, sea, inner.xs[cc], inner.zs[rr])
    clear = gen > 0.0
    held_back = int((~clear).sum())
    rr, cc = rr[clear], cc[clear]
    before = H[rr, cc].copy()
    H[rr, cc] = np.float32(floor)
    d, _ = nearest(sea.outline_kd, inner.xs[cc], inner.zs[rr]) if len(rr) else (np.zeros(0), None)
    return (rr, cc), {"nodes": int(len(rr)), "floor": floor, "held_back_by_the_generator_buffer": held_back,
                      "from_m": [round(float(before.min()), 2), round(float(before.max()), 2)] if len(rr) else None,
                      "nearest_held_outline_m": round(float(d.min()), 1) if len(rr) else None}


# --- the bed: C3, as proposed (seabed-proposals-2026-10-08, seabed-canyon-bay-2026-10-12) ------------
# B, a Pacific coast; C, a canyon coast (B with a winding canyon off the pier and two tributaries);
# C2, the canyon's trunk taken into the bay; C3, C2 with a south arm. Each adds to the one before.

class PacificCoast:
    """B: the sandy shelf carried on with long-shore bars; rocky shores dropping off steeply; reef
    clusters off headlands, points and cliffs; the bay and the inner bay a sandy basin; a dredged
    ferry channel with turning basins; outside, the shelf deepening to a break and the slope down to
    the floor. Then every option's holds: the ferry's water, the footings, the harbour, the pier."""
    seed = 1985
    ROCKY_SLOPE = 1.0 / 12.0
    # long-shore bars, by distance from the shelf's start: (at, width, height); cut by rip gaps
    BARS = ((150.0, 26.0, 1.0), (290.0, 34.0, 0.8))
    SHELF_BREAK = 3000.0
    BREAK_DEPTH = -100.0
    SLOPE = 1.0 / 4.0
    ABYSS = -480.0
    # the bay and the inner bay south of the bridge (Godot x, z), blended over 200 m
    BAY = [(-300.0, -330.0), (0.0, -330.0), (0.0, 300.0), (750.0, 2200.0), (650.0, 2700.0), (700.0, 3200.0),
           (500.0, 4300.0), (300.0, 5150.0), (-300.0, 5200.0), (-700.0, 4600.0), (-800.0, 3600.0),
           (-700.0, 2950.0), (-1000.0, 2400.0), (-1000.0, 2000.0), (-650.0, 900.0), (-450.0, 0.0)]
    BAY_DEEP = -30.0
    CHANNEL_CUT = 3.0
    BASIN_R = 90.0
    BASIN_CUT = 2.5
    REEFS = 24
    REEF_TOP = (-20.0, -10.5)

    def __init__(self, sea, context):
        self.sea = sea
        self.ctx = context
        self.notes = []
        self.use_bumps = True
        self.bay_poly = [g2b(x, z) for x, z in self.BAY]
        self.reefs = []
        self.make_reefs()

    def height(self, X, Y):
        X = np.asarray(X, dtype=float).ravel()
        Y = np.asarray(Y, dtype=float).ravel()
        s = self.sea.sample(X, Y)
        S = self.after(X, Y, self.base(X, Y, s), s)
        return self.common(X, Y, S)

    def after(self, X, Y, S, s):
        return S

    def common(self, X, Y, S):
        """Every option's holds: water for the ferry, the footings, the harbour cove and the pier's
        sides, never above `CAP`. The bridge's towers stand on the bed: within `FOOTING_REACH` of
        each tower footing the bed is `FOOTING_CLEAR` under its bottom, blending into the bed beyond
        over `FOOTING_BLEND`; by the approach piers, which stand on ground, it is no higher than that."""
        c = self.ctx
        d, _ = polyline_distance(c["ferry"], X, Y)
        S = np.where(d < FERRY_HALF + 5.0, np.minimum(S, SEA - FERRY_WATER), S)
        for (fx0, fx1, fy0, fy1, fbot), name in zip(c["footings"], c["footing_names"]):
            dx = np.maximum(np.maximum(fx0 - X, X - fx1), 0.0)
            dy = np.maximum(np.maximum(fy0 - Y, Y - fy1), 0.0)
            dist = np.hypot(dx, dy)
            if name.startswith("bridge_tower_"):
                w = 1.0 - smoothstep(FOOTING_REACH, FOOTING_REACH + FOOTING_BLEND, dist)
                S = S * (1.0 - w) + (fbot - FOOTING_CLEAR) * w
            else:
                S = np.where(dist < FOOTING_REACH, np.minimum(S, fbot - FOOTING_CLEAR), S)
        hp = polygon_signed_distance([g2b(x, z) for x, z in HARBOUR], X, Y)
        S = np.where(hp > -HARBOUR_REACH, np.minimum(S, SEA - FERRY_WATER), S)
        dp, _ = polyline_distance(c["pier"], X, Y)
        S = np.where(dp < PIER_SIDES, np.minimum(S, SEA - FERRY_WATER), S)
        return np.minimum(S, CAP)

    def make_reefs(self):
        """About two dozen reef clusters off the headlands, rocky points and cliffed shores: each a
        few merged, irregular mounds, tops -10.5..-20; none in the ferry's channel or basins, by the
        bridge, or in the park's box."""
        sea = self.sea
        rng = np.random.default_rng(self.seed + 7)
        c = self.ctx
        n_e = len(sea.es_x)
        share = box_blur(box_blur(sea.seamask.astype(float), 75, 0), 75, 1)
        land_top = np.where(sea.F & (np.nan_to_num(sea.Ftop, nan=-1e9) > SEA), sea.Ftop, -1e9)
        cliff = maxfilter(land_top, 20) > SEA + 12.0
        cand = []
        for k in range(0, n_e, 3):
            if sea.b_sand[k] >= 0.3:
                continue
            ox, oy = sea.es_out[k]
            sx, sy = sea.es_x[k] - ox * 60.0, sea.es_y[k] - oy * 60.0
            i, j, inside = sea.cell(np.array([sx]), np.array([sy]))
            if not inside[0]:
                continue
            score = share[j[0], i[0]] + 0.35 * float(cliff[j[0], i[0]]) + rng.uniform(0, 0.08)
            cand.append((score, k))
        cand.sort(reverse=True)
        z = sea.zone

        def ok(x, y, R):
            if z[0] - 60 - R <= x <= z[1] + 60 + R and z[2] - 60 - R <= y <= z[3] + 60 + R:
                return False
            if not sea.is_sea(np.array([x]), np.array([y]))[0]:
                return False
            if polyline_distance(c["ferry"], np.array([x]), np.array([y]))[0][0] < 300.0 + R:
                return False
            for hx, hy in c["landing_heads"]:
                if math.hypot(x - hx, y - hy) < 300.0 + R:
                    return False
            for (fx0, fx1, fy0, fy1, _) in c["footings"]:
                if math.hypot(max(fx0 - x, x - fx1, 0), max(fy0 - y, y - fy1, 0)) < 250.0 + R:
                    return False
            return True

        centres = []
        for score, k in cand:
            if len(centres) >= self.REEFS:
                break
            ox, oy = sea.es_out[k]
            dist = rng.uniform(90.0, 260.0)
            side = rng.uniform(-60, 60)
            cx = sea.es_x[k] + ox * dist - oy * side
            cy = sea.es_y[k] + oy * dist + ox * side
            if any(math.hypot(cx - a, cy - b) < 550.0 for a, b, _ in centres):
                continue
            if not ok(cx, cy, 140.0):
                continue
            if sea.nearest([cx], [cy])[0][0] < 60.0:
                continue
            centres.append((cx, cy, score))
        mounds = []
        for n, (cx, cy, _) in enumerate(centres):
            crest = rng.uniform(-18.0, -11.0)
            for m in range(int(rng.integers(4, 9))):
                off = np.clip(rng.normal(0.0, 45.0, 2), -110.0, 110.0)
                R = rng.uniform(28.0, 70.0)
                top = float(np.clip(crest - abs(rng.normal(0.0, 2.2)), *self.REEF_TOP))
                ang = rng.uniform(0, math.pi)
                aspect = rng.uniform(0.55, 1.0)
                mounds.append([cx + off[0], cy + off[1], R, top, ang, aspect, n])
        if not mounds:
            return
        M = np.array(mounds)
        s = sea.sample(M[:, 0], M[:, 1])
        base = self.profile(M[:, 0], M[:, 1], s, bars=False)
        keep = M[:, 3] > base + 1.0
        M = M[keep]
        base = base[keep]
        self.reef_mounds = np.column_stack([M, M[:, 3] - base + 3.0])
        self.reefs = []
        for n in range(len(centres)):
            sel = self.reef_mounds[self.reef_mounds[:, 6] == n]
            if len(sel):
                r = sel[:, 2].max()
                self.reefs.append((sel, sel[:, 0].min() - r, sel[:, 0].max() + r, sel[:, 1].min() - r, sel[:, 1].max() + r))
        self.notes.append("%d reef clusters of %d mounds in all (4-8 each, 28-70 m across); tops %.1f..%.1f" % (
            len(self.reefs), len(M), M[:, 3].min(), M[:, 3].max()))

    def apply_reefs(self, X, Y, S):
        if not self.reefs or not self.use_bumps:
            return S
        out = S.copy()
        for sel, x0, x1, y0, y1 in self.reefs:
            m = np.nonzero((X > x0) & (X < x1) & (Y > y0) & (Y < y1))[0]
            if not len(m):
                continue
            x, y = X[m], Y[m]
            M = np.full(len(m), -1e9)
            for bx, by, R, top, ang, aspect, n, Hh in sel:
                u = (x - bx) * math.cos(ang) + (y - by) * math.sin(ang)
                v = -(x - bx) * math.sin(ang) + (y - by) * math.cos(ang)
                r = np.hypot(u / R, v / (R * aspect)) * (1.0 + 0.22 * value_noise(int(n) * 31 + 5, 22.0, x, y))
                M = smax(M, top - Hh * np.clip(r, 0, 4) ** 1.7, 5.0)
            raised = smax(S[m], M, 3.0)
            out[m] = np.where(raised > S[m], np.minimum(raised, self.REEF_TOP[1]), S[m])
        return out

    def far(self, Dl):
        """The open coast's shelf by distance to land: shallow inshore, steepening to the break, then
        the continental slope down to the floor."""
        shelf = START + (self.BREAK_DEPTH - START) * (np.maximum(Dl, 0) / self.SHELF_BREAK) ** 1.6
        slope = self.BREAK_DEPTH - (Dl - self.SHELF_BREAK) * self.SLOPE
        return smax(smin(shelf, slope, 20.0), np.full(len(Dl), self.ABYSS), 30.0)

    def regional(self, X, Y, s):
        Dl = s["Dl"]
        bay = START + (self.BAY_DEEP - START) * smoothstep(0.0, 900.0, Dl) ** 1.2
        w = smoothstep(-200.0, 200.0, polygon_signed_distance(self.bay_poly, X, Y))
        return self.far(Dl) * (1 - w) + bay * w

    def profile(self, X, Y, s, bars=True):
        D, e, sand, d0, Dl = s["D"], s["e"], s["sand"], s["d0"], s["Dl"]
        T = self.regional(X, Y, s)
        # sandy: the profile on from the shelf's edge, until the regional depth is deeper; dean() is
        # negative, so going out adds dean(ds) - dean(d0) (`DEAN_CARRIES_DOWN`; as drawn, subtracted)
        ds = d0 + D
        carry = dean(ds) - dean(d0)
        sandy = smin(e - UNDER + (carry if DEAN_CARRIES_DOWN else -carry), T, 4.0)
        if bars:
            amp = np.clip(0.55 + 0.75 * value_noise(self.seed, 260.0, X, Y), 0.0, 1.0)
            # no bars off the promenade: the box's own bed runs plain
            z = self.sea.zone
            dz = np.maximum(np.maximum(z[0] - X, X - z[1]), np.maximum(z[2] - Y, Y - z[3]))
            amp = amp * smoothstep(0.0, 200.0, dz)
            sandy = sandy + amp * sum(h * np.exp(-((ds - at) / w) ** 2) for at, w, h in self.BARS)
        # rocky: steep off the shelf's edge to a floor 14 m under the regional depth inshore
        floor = T - 14.0 * (1 - smoothstep(600.0, 1800.0, Dl))
        rocky = smax(e - UNDER - D * self.ROCKY_SLOPE, floor, 8.0)
        k = smoothstep(0.2, 0.7, sand)
        return sandy * k + rocky * (1 - k)

    def base(self, X, Y, s):
        return self.harbour(X, Y, self.apply_reefs(X, Y, self.profile(X, Y, s)))

    def harbour(self, X, Y, S):
        """The ferry's dredged channel and the turning basins at its landing heads."""
        c = self.ctx
        d, sarc = polyline_distance(c["ferry"], X, Y)
        L = c["ferry_len"]
        ends = smoothstep(0.0, 120.0, sarc) * smoothstep(0.0, 120.0, L - sarc)
        S = S - self.CHANNEL_CUT * (1 - smoothstep(22.0, 48.0, d)) * np.maximum(ends, 0.35)
        for hx, hy in c["landing_heads"]:
            S = S - self.BASIN_CUT * (1 - smoothstep(0.6 * self.BASIN_R, self.BASIN_R, np.hypot(X - hx, Y - hy)))
        return S


class CanyonCoast(PacificCoast):
    """C: B with a winding canyon whose head plunges from -45 just outside the park's box off the
    pier, rounded in section, widening and deepening seaward, with two tributaries curving in."""
    COURSE = [(-330.0, -40.0), (-480.0, 30.0), (-640.0, 170.0), (-820.0, 300.0), (-1010.0, 280.0), (-1150.0, 150.0),
              (-1330.0, 40.0), (-1560.0, 70.0), (-1800.0, 210.0), (-2080.0, 380.0), (-2450.0, 450.0), (-2900.0, 520.0),
              (-3500.0, 700.0), (-4300.0, 900.0), (-5300.0, 1050.0), (-6900.0, 1250.0)]
    BRANCHES = [[(-560.0, -520.0), (-640.0, -400.0), (-740.0, -250.0), (-860.0, -100.0), (-990.0, 60.0), (-1120.0, 135.0)],
                [(-760.0, 760.0), (-900.0, 640.0), (-1080.0, 520.0), (-1300.0, 400.0), (-1520.0, 250.0), (-1690.0, 160.0)]]
    TRIB_FLOOR = -28.0
    # the head plunges, as La Jolla's and Monterey's do, so the darker water reaches in to the pier
    HEAD_FLOOR_2 = -45.0

    def __init__(self, sea, context):
        super().__init__(sea, context)
        self.course = Course(self.COURSE)
        self.branches = [Course(b) for b in self.BRANCHES]
        self.joins = []
        for br in self.branches:
            end = br.pts[-1]
            _, sj = self.course.query(np.array([end[0]]), np.array([end[1]]), 1e6)
            self.joins.append(float(sj[0]))

    def section(self, d, floor, w, m):
        """A rounded canyon: a parabolic floor `w` either side of the axis, then walls at slope `m`."""
        return floor + np.where(d < w, m * d * d / (2.0 * w), m * w / 2.0 + m * (d - w))

    def course_floor(self, sarc, Dl):
        f = self.HEAD_FLOOR_2 - 70.0 * smoothstep(0, 1500.0, sarc) - 0.03 * sarc
        under = 18.0 + 140.0 * smoothstep(800.0, 4800.0, sarc)
        return np.minimum(f, self.far(Dl) - under)

    def after(self, X, Y, S, s):
        d, sarc = self.course.query(X, Y, 2500.0)
        sarc = np.where(np.isfinite(d), sarc, 0.0)
        w = 40.0 + 0.05 * sarc
        m = 0.22 + 0.2 * smoothstep(0, 2500.0, sarc)
        H = self.section(np.where(np.isfinite(d), d, 1e5), self.course_floor(sarc, s["Dl"]), w, m)
        S = smin(S, H, 12.0)
        for br, sj in zip(self.branches, self.joins):
            dt, st = br.query(X, Y, 1500.0)
            st = np.where(np.isfinite(dt), st, 0.0)
            frac = st / br.length
            join = self.course_floor(np.full(len(X), sj), s["Dl"])
            f = self.TRIB_FLOOR + (join - self.TRIB_FLOOR) * frac ** 1.3
            Ht = self.section(np.where(np.isfinite(dt), dt, 1e5), f, 25.0 + 0.04 * st, 0.25 + 0.1 * frac)
            S = smin(S, Ht, 10.0)
        return S


class CanyonBay(CanyonCoast):
    """C2: the bay and the inner bay are a drowned river valley and the canyon its seaward
    continuation, so the bay's river is the trunk. It heads in the outer bay as near the bridge's
    narrows as a 200 m rim-to-footing margin allows, on the inner bay's line, runs up the bay along
    its axis, under the ferry route, out past the peninsula's tip, and on down C's course offshore;
    larger and deeper than C's. C's canyon off the pier is kept as a tributary, its floor falling over
    its last `PIER_BLEND` to the trunk's at the junction; the headland tributary joins it as in C;
    C's south branch is folded into the trunk."""
    JOIN = (-2080.0, 380.0)
    TRUNK = [(-55.0, 2033.0), (-70.0, 1870.0), (-215.0, 1720.0), (-340.0, 1560.0), (-460.0, 1440.0), (-610.0, 1350.0),
             (-700.0, 1200.0), (-770.0, 1035.0), (-930.0, 905.0), (-1150.0, 855.0), (-1330.0, 720.0), (-1510.0, 565.0),
             (-1750.0, 470.0), JOIN] + CanyonCoast.COURSE[10:]
    PIER = CanyonCoast.COURSE[:10]
    BRANCHES = CanyonCoast.BRANCHES[:1]
    TRUNK_HEAD = -50.0
    TRUNK_PLUNGE = 80.0
    TRUNK_GRADE = 0.035
    TRUNK_W = 60.0
    PIER_BLEND = 600.0

    def __init__(self, sea, context):
        PacificCoast.__init__(self, sea, context)
        self.trunk = Course(self.TRUNK)
        self.pier = Course(self.PIER)
        self.branches = [Course(b) for b in self.BRANCHES]
        self.joins = []
        for br in self.branches:
            end = br.pts[-1]
            _, sj = self.pier.query(np.array([end[0]]), np.array([end[1]]), 1e6)
            self.joins.append(float(sj[0]))
        j = g2b(*self.JOIN)
        _, sj = self.trunk.query(np.array([j[0]]), np.array([j[1]]), 1e6)
        self.join_trunk = float(sj[0])
        # below the junction the trunk is at least as deep as C's canyon was at the same place
        self.offset = self.join_trunk - self.pier.length

    def trunk_floor(self, s, Dl):
        own = self.TRUNK_HEAD - self.TRUNK_PLUNGE * smoothstep(0, 1500.0, s) - self.TRUNK_GRADE * s
        under = 18.0 + 140.0 * smoothstep(800.0, 4800.0, s)
        below = self.course_floor(np.maximum(s - self.offset, 0.0), Dl)
        return np.minimum(np.minimum(own, self.far(Dl) - under), below)

    def after(self, X, Y, S, s):
        d, st = self.trunk.query(X, Y, 2500.0)
        st = np.where(np.isfinite(d), st, 0.0)
        w = self.TRUNK_W + 0.05 * st
        m = 0.22 + 0.2 * smoothstep(0, 2500.0, st)
        S = smin(S, self.section(np.where(np.isfinite(d), d, 1e5), self.trunk_floor(st, s["Dl"]), w, m), 12.0)
        dp, sp = self.pier.query(X, Y, 2500.0)
        sp = np.where(np.isfinite(dp), sp, 0.0)
        fp = self.course_floor(sp, s["Dl"])
        join = self.trunk_floor(np.full(len(X), self.join_trunk), s["Dl"])
        fp = fp + (np.minimum(fp, join) - fp) * smoothstep(self.pier.length - self.PIER_BLEND, self.pier.length, sp)
        wp = 40.0 + 0.05 * sp
        mp = 0.22 + 0.2 * smoothstep(0, 2500.0, sp)
        S = smin(S, self.section(np.where(np.isfinite(dp), dp, 1e5), fp, wp, mp), 12.0)
        for br, sj in zip(self.branches, self.joins):
            dt, st = br.query(X, Y, 1500.0)
            st = np.where(np.isfinite(dt), st, 0.0)
            frac = st / br.length
            join = self.course_floor(np.full(len(X), sj), s["Dl"])
            f = self.TRIB_FLOOR + (join - self.TRIB_FLOOR) * frac ** 1.3
            Ht = self.section(np.where(np.isfinite(dt), dt, 1e5), f, 25.0 + 0.04 * st, 0.25 + 0.1 * frac)
            S = smin(S, Ht, 10.0)
        return S


class CanyonFork(CanyonBay):
    """C3, Christina's choice: C2 with a south arm, so the canyon forks north and south out past the
    city as seen from the land. The arm heads at the mouth of the cove where the valley between the
    southern foothills and the southern massif reaches the outer coast, plunging from -40; it winds
    north-west down the outer shelf and the slope and joins the main canyon at (-5300, 1050) at an
    acute angle pointing downstream. Smaller than the trunk: a narrower section, and its floor runs
    `ARM_UNDER` under the regional depth down the slope where the trunk's runs 140 m."""
    ARM_JOIN = (-5300.0, 1050.0)
    ARM = [(-1760.0, 5890.0), (-2020.0, 5860.0), (-2280.0, 5700.0), (-2460.0, 5420.0), (-2783.0, 4759.0),
           (-3330.0, 4245.0), (-3578.0, 3536.0), (-4125.0, 3022.0), (-4381.0, 2317.0), (-4700.0, 1750.0),
           (-5050.0, 1280.0), ARM_JOIN]
    ARM_HEAD = -40.0
    ARM_PLUNGE = 40.0
    ARM_GRADE = 0.025
    ARM_W = 30.0
    ARM_UNDER = 80.0

    def __init__(self, sea, context):
        super().__init__(sea, context)
        self.arm = Course(self.ARM)
        end = self.arm.pts[-1]
        _, sj = self.trunk.query(np.array([end[0]]), np.array([end[1]]), 1e6)
        self.join_arm = float(sj[0])

    def arm_floor(self, s, Dl):
        own = self.ARM_HEAD - self.ARM_PLUNGE * smoothstep(0, 1500.0, s) - self.ARM_GRADE * s
        under = 18.0 + self.ARM_UNDER * smoothstep(800.0, 4800.0, s)
        f = np.minimum(own, self.far(Dl) - under)
        join = self.trunk_floor(np.full(len(s), self.join_arm), Dl)
        L = self.arm.length
        return f + (np.minimum(f, join) - f) * smoothstep(L - self.PIER_BLEND, L, s)

    def after(self, X, Y, S, s):
        S = super().after(X, Y, S, s)
        d, st = self.arm.query(X, Y, 1500.0)
        st = np.where(np.isfinite(d), st, 0.0)
        w = self.ARM_W + 0.04 * st
        m = 0.24 + 0.16 * smoothstep(0, 2500.0, st)
        H = self.section(np.where(np.isfinite(d), d, 1e5), self.arm_floor(st, s["Dl"]), w, m)
        return smin(S, H, 10.0)


# --- context: the ferry, the landings, the bridge, the pier -------------------------------------------

def context():
    """The ferry's route and landing heads (the master's reference curve, read only), the bridge's
    footings (the city source, read only), the pier (`ParkPlan`), in the bed's plan."""
    import bpy
    tmp = bpy.data.collections.new("scratch_context")
    bpy.context.scene.collection.children.link(tmp)
    with bpy.data.libraries.load(MASTER, link=False) as (src, dst):
        dst.objects = ["ferry_route_beach_town_to_city", "coast_highway_centreline"]
    with bpy.data.libraries.load(CITY_SOURCE, link=False) as (src, dst2):
        dst2.objects = [n for n in src.objects if n.startswith(("bridge_tower_", "bridge_approach_pier_")) and "beam" not in n]
    loaded = [ob for ob in list(dst.objects) + list(dst2.objects) if ob is not None]
    extra = set()
    for ob in loaded:
        tmp.objects.link(ob)
        p = ob.parent
        while p is not None:
            if p.name not in tmp.objects:
                tmp.objects.link(p)
                extra.add(p)
            p = p.parent
    bpy.context.view_layer.update()
    route = bpy.data.objects["ferry_route_beach_town_to_city"]
    pts = []
    for sp in route.data.splines:
        if len(sp.points):
            pts += [route.matrix_world @ p.co.xyz for p in sp.points]
        else:
            pts += [route.matrix_world @ p.co for p in sp.bezier_points]
    ferry = np.array([(p.x, p.y) for p in pts])
    road = bpy.data.objects["coast_highway_centreline"]
    hpts = []
    for sp in road.data.splines:
        if len(sp.points):
            hpts += [road.matrix_world @ p.co.xyz for p in sp.points]
        else:
            hpts += [road.matrix_world @ p.co for p in sp.bezier_points]
    highway = np.array([(p.x, p.y, p.z) for p in hpts])
    footings, names = [], []
    for ob in loaded:
        if ob.type != "MESH":
            continue
        co = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
        footings.append((co[:, 0].min(), co[:, 0].max(), co[:, 1].min(), co[:, 1].max(), co[:, 2].min()))
        names.append(ob.name)
    for ob in loaded + list(extra):
        data = ob.data
        bpy.data.objects.remove(ob)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
    bpy.data.collections.remove(tmp)
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(ferry, axis=0).T))])
    edge = plan_constant("SHORE_EDGE")
    pz = plan_constant("PIER_Z")
    head = edge - plan_constant("PIER_LENGTH") - 6.0
    return {"ferry": ferry, "ferry_cum": cum, "ferry_len": float(cum[-1]),
            "landing_heads": [(ferry[0, 0], ferry[0, 1]), (ferry[-1, 0], ferry[-1, 1])],
            "footings": footings, "footing_names": names, "highway": highway,
            "pier": np.array([g2b(edge + 4.0, pz), g2b(head - 8.0, pz)]), "pier_head": g2b(head, pz)}


def context_godot(ctx, sea):
    """What the chart draws, in Godot (x, z)."""
    return {"ferry": [[round(float(x), 2), round(float(-y), 2)] for x, y in ctx["ferry"]],
            "footings": [{"name": n, "x": [round(float(f[0]), 2), round(float(f[1]), 2)], "z": [round(float(-f[3]), 2), round(float(-f[2]), 2)],
                          "bottom": round(float(f[4]), 3)} for f, n in zip(ctx["footings"], ctx["footing_names"])],
            "zone": [sea.zone[0], sea.zone[1], -sea.zone[3], -sea.zone[2]],
            "landing_heads": [[round(float(x), 2), round(float(-y), 2)] for x, y in ctx["landing_heads"]]}


# --- the bed on the grid --------------------------------------------------------------------------

def lowest_beside(H, br, bc):
    """For nodes (br, bc): the lowest ground of their four neighbours, or of their diagonal ones
    where none of the four has ground; inf where neither has."""
    G = np.where(np.isnan(H), np.inf, H).astype(np.float64)
    nz, nx = H.shape
    low4 = np.full(len(br), np.inf)
    lowd = np.full(len(br), np.inf)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if not (dr or dc):
                continue
            rr, cc = br + dr, bc + dc
            ok = (rr >= 0) & (rr < nz) & (cc >= 0) & (cc < nx)
            v = np.full(len(br), np.inf)
            v[ok] = G[rr[ok], cc[ok]]
            if dr and dc:
                lowd = np.minimum(lowd, v)
            else:
                low4 = np.minimum(low4, v)
    return np.where(np.isfinite(low4), low4, lowd)


class Bed:
    """C3's bed on the grid: the inner tier's new heights and colours (`H`, `C`; `changed` and
    `painted` say where), and the outer tier's (`outer`, `outer_y`) where `grid.json` has one."""

    def __init__(self, root, stride=1):
        self.root = root
        self.inner = Inner(root)
        inner = self.inner
        log("grid: %d inner tiles, %d nodes with ground" % (len(inner.tiles), int((~np.isnan(inner.H)).sum())))
        self.ctx = context()
        sea = GridSea(inner, self.ctx)
        self.sea = sea
        log("sea: %s" % json.dumps(sea.report["sea"]))
        H = inner.H.copy()
        C = inner.C.copy()
        d0, shelf_cols, shelf_rep = reshape_shelves(sea, self.ctx, H)
        log("sandy shelf: %s" % json.dumps(shelf_rep))
        (hr, hc), harb_rep = lower_harbour(sea, H)
        log("harbour: %s" % json.dumps(harb_rep))
        sr, sc, rgb = shelf_cols
        C[sr, sc, :3] = rgb
        # the edges read the reshaped shelf: its height, and how far out from its start it is
        er, ec = sea.edge_rc
        sea.b_e[:sea.n_e] = H[er, ec]
        D0 = np.full(H.shape, np.nan, np.float32)
        D0[d0[0], d0[1]] = d0[2]
        sea.b_d0[:sea.n_e] = np.where(np.isnan(D0[er, ec]), 60.0, D0[er, ec])
        del D0
        sea.edge_fields()
        self.outer = Outer(root, inner) if "outer" in json.load(open(os.path.join(root, "grid.json"))) else None
        x0, x1, y0, y1 = sea.land_box
        domain = [x0 - MARGIN, x1 + MARGIN, y0 - MARGIN, y1 + MARGIN]
        boxes = [(inner.box[0], inner.box[1], -inner.box[3], -inner.box[2])]
        if self.outer is not None:
            o = self.outer
            boxes.append((o.xs[0], o.xs[-1], -o.zs[-1], -o.zs[0]))
        for b in boxes:
            domain = [min(domain[0], b[0]), max(domain[1], b[1]), min(domain[2], b[2]), max(domain[3], b[3])]
        sea.land_distance(domain)
        self.opt = CanyonFork(sea, self.ctx)
        log("bed: %s" % "; ".join(self.opt.notes))
        # every bed node of the inner tier
        br, bc = np.nonzero(sea.bed)
        if stride > 1:
            keep = (br % stride == 0) & (bc % stride == 0)
            br, bc = br[keep], bc[keep]
        Z = self.evaluate(inner.xs[bc], inner.zs[br], "inner")
        # the edge rule: a node beside ground lies `UNDER` under the lowest ground beside it (its four
        # neighbours', or its diagonal ones' where those have none), never above `CAP`
        low = lowest_beside(H, br, bc)
        at_edge = np.isfinite(low)
        Z[at_edge] = np.minimum(low[at_edge] - UNDER, CAP)
        # the harbour cove keeps a ferry's water up to its cliffs: the bed beside the cliff is carried
        # down to the cove's floor with the cliff's foot
        k = np.flatnonzero(at_edge)
        k = k[harbour_region(inner.xs[bc[k]], -inner.zs[br[k]])]
        Z[k] = np.minimum(Z[k], SEA - FERRY_WATER - UNDER)
        # under the park's shore box, at its foot
        ov = sea.overlap[br, bc]
        Z[ov] = np.minimum(Z[ov], sea.box_bottom - UNDER)
        Z = np.minimum(Z, CAP)
        H[br, bc] = Z.astype(np.float32)
        x, z = inner.xs[bc].astype(float), inner.zs[br].astype(float)
        C[br, bc, :3] = self.colour(x, z, Z)
        C[br, bc, 3] = 255
        self.H, self.C = H, C
        with np.errstate(invalid="ignore"):
            self.changed = (np.isnan(inner.H) & ~np.isnan(H)) | (np.abs(H - inner.H) > MIN_CHANGE)
        self.painted = np.any(C != inner.C, axis=-1)
        self.bed_rc = (br, bc)
        self.edge_bed = at_edge
        self.report = {"sea": sea.report, "sandy_shelf": shelf_rep, "harbour_foot": harb_rep, "notes": self.opt.notes,
                       "inner": {"bed_nodes": int(len(br)), "bed_nodes_at_an_edge": int(at_edge.sum()),
                                 "bed_nodes_under_the_park_shore": int(ov.sum()),
                                 "changed_nodes": int(self.changed.sum()), "painted_nodes": int(self.painted.sum()),
                                 "bed_height": [round(float(Z.min()), 2), round(float(Z.max()), 3)]}}
        if self.outer is not None:
            o = self.outer
            orr, occ = np.nonzero(o.own & np.isnan(o.H))
            if stride > 1:
                keep = (orr % stride == 0) & (occ % stride == 0)
                orr, occ = orr[keep], occ[keep]
            oy = np.minimum(self.evaluate(o.xs[occ], o.zs[orr], "outer"), CAP)
            self.outer_rc = (orr, occ)
            self.outer_y = oy
            self.outer_rgb = self.colour(o.xs[occ].astype(float), o.zs[orr].astype(float), oy)
            self.report["outer"] = {"bed_nodes": int(len(orr)), "bed_height": [round(float(oy.min()), 2), round(float(oy.max()), 3)]}

    def evaluate(self, x, z, label):
        """The bed's function at nodes (Godot x, z), a chunk at a time."""
        Z = np.empty(len(x), np.float64)
        CH = 400000
        for k in range(0, len(x), CH):
            Z[k:k + CH] = self.opt.height(np.asarray(x[k:k + CH], float), -np.asarray(z[k:k + CH], float))
            if (k // CH) % 5 == 4 or k + CH >= len(x):
                log("  %s bed: %d of %d nodes" % (label, min(k + CH, len(x)), len(x)))
        return Z

    def colour(self, x, z, y):
        sea = self.sea
        sand = bilinear(sea.sand_field, sea.fx0, sea.fy0, sea.fh, x, -z) > 0.5
        return shelf_rgb(x, z, y, sand)


# --- measuring, on the grid's bilinear surface after the edit ----------------------------------------

class Surface:
    """The grid's bilinear surface (Godot x, z): NaN where a cell's corner has no ground."""

    def __init__(self, H, x0, z0, step):
        self.H, self.x0, self.z0, self.step = H, x0, z0, step

    def at(self, x, z):
        x = np.asarray(x, float)
        z = np.asarray(z, float)
        gx = (x - self.x0) / self.step
        gz = (z - self.z0) / self.step
        nz, nx = self.H.shape
        i = np.clip(np.floor(gx).astype(int), 0, nx - 2)
        j = np.clip(np.floor(gz).astype(int), 0, nz - 2)
        fx, fz = gx - i, gz - j
        H = self.H
        v = (H[j, i] * (1 - fx) + H[j, i + 1] * fx) * (1 - fz) + (H[j + 1, i] * (1 - fx) + H[j + 1, i + 1] * fx) * fz
        out = (gx < 0) | (gz < 0) | (gx > nx - 1) | (gz > nz - 1)
        return np.where(out, np.nan, v)


def least_water(surf, P, label_ground=False):
    """The least water over points P (Godot x, z): only where the surface is under the sea."""
    P = np.asarray(P, float)
    if not len(P):
        return {"least_water_m": None}
    v = surf.at(P[:, 0], P[:, 1])
    wet = ~np.isnan(v) & (v < SEA)
    if not wet.any():
        return {"least_water_m": None, "points": int(len(P))}
    k = np.nonzero(wet)[0][np.argmax(v[wet])]
    return {"least_water_m": round(float(SEA - v[k]), 2), "at_godot": [round(float(P[k, 0]), 1), round(float(P[k, 1]), 1)],
            "points": int(wet.sum())}


def measure(bed):
    inner, sea, ctx = bed.inner, bed.sea, bed.ctx
    surf = Surface(bed.H, inner.x0, inner.z0, inner.step)
    r = {}
    # the ferry's route, every 5 m, across its width
    F = np.array([(x, -y) for x, y in ctx["ferry"]])
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(F, axis=0).T))])
    pts = []
    for s in np.arange(0.0, cum[-1], 5.0):
        i = min(int(np.searchsorted(cum, s, side="right") - 1), len(F) - 2)
        u = (s - cum[i]) / max(cum[i + 1] - cum[i], 1e-9)
        p = F[i] + (F[i + 1] - F[i]) * u
        d = (F[i + 1] - F[i]) / np.linalg.norm(F[i + 1] - F[i])
        for off in (-FERRY_HALF + 5.0, -12.0, 0.0, 12.0, FERRY_HALF - 5.0):
            pts.append(p + np.array((-d[1], d[0])) * off)
    r["ferry_route"] = least_water(surf, pts)
    # the landing heads, 20 m round
    r["landing_heads"] = []
    for (hx, hy), name in zip(ctx["landing_heads"], ("beach town", "city")):
        P = [(hx + dx, -hy + dz) for dx in (-20.0, 0.0, 20.0) for dz in (-20.0, 0.0, 20.0)]
        r["landing_heads"].append(dict(least_water(surf, P), landing=name))
    # the harbour cove, every 3 m
    hx = [p[0] for p in HARBOUR]
    hz = [p[1] for p in HARBOUR]
    G = np.array([(x, z) for x in np.arange(min(hx), max(hx), 3.0) for z in np.arange(min(hz), max(hz), 3.0)])
    inside = polygon_signed_distance(HARBOUR, G[:, 0], G[:, 1]) > 0
    G = G[inside]
    # the cove's water: points whose cell has no corner above the sea (the shore's own cells excluded)
    c = np.floor((G[:, 0] - inner.x0) / inner.step).astype(int)
    rw = np.floor((G[:, 1] - inner.z0) / inner.step).astype(int)
    with np.errstate(invalid="ignore"):
        wet = np.ones(len(G), bool)
        for dr in (0, 1):
            for dc in (0, 1):
                v = bed.H[rw + dr, c + dc]
                wet &= ~np.isnan(v) & (v < SEA)
    r["harbour"] = least_water(surf, G[wet])
    r["harbour"]["shore_cells_left_out"] = int((~wet).sum())
    r["harbour"]["cliff_foot_nodes_lowered"] = bed.report["harbour_foot"]["nodes"]
    # the pier's sides, within 30 m of it
    pier = [(x, -y) for x, y in ctx["pier"]]
    P = []
    for t in np.linspace(0, 1, 40):
        q = (pier[0][0] + (pier[1][0] - pier[0][0]) * t, pier[0][1] + (pier[1][1] - pier[0][1]) * t)
        for off in (-PIER_SIDES + 2, -15.0, -6.0, 6.0, 15.0, PIER_SIDES - 2):
            P.append((q[0], q[1] + off))
    r["pier_sides"] = least_water(surf, P)
    # the sunset bearing, 294 degrees from the pier head, its first 2 km
    phx, phy = ctx["pier_head"]
    b = math.radians(294.0)
    P = [(phx + math.sin(b) * d, -phy - math.cos(b) * d) for d in np.arange(10.0, 2000.0, 5.0)]
    r["sunset_bearing_294_first_2km"] = least_water(surf, P)
    # the bridge's footings: the bed under each, against its bottom
    foot = []
    for (fx0, fx1, fy0, fy1, fbot), name in zip(ctx["footings"], ctx["footing_names"]):
        P = [(x, -y) for x in np.linspace(fx0, fx1, 5) for y in np.linspace(fy0, fy1, 5)]
        v = surf.at(np.array(P)[:, 0], np.array(P)[:, 1])
        top = float(np.nanmax(v))
        foot.append({"footing": name, "bottom": round(float(fbot), 3), "bed_top": round(top, 3),
                     "gap_m": round(float(fbot) - top, 3), "bed_under_it": [round(float(np.nanmin(v)), 3), round(top, 3)]})
    r["footings"] = foot
    # the park's box
    br, bc = bed.bed_rc
    x, z = inner.xs[bc], inner.zs[br]
    inz = sea.in_zone(x, -z)
    Z = bed.H[br, bc]
    r["park_box_bed"] = {"ha": round(float(inz.sum()) * inner.step ** 2 / 1e4, 2),
                         "highest": round(float(Z[inz].max()), 3) if inz.any() else None,
                         "under_the_shore_box_nodes": int(sea.overlap[br, bc].sum())}
    # nothing above -8.05 in the sea; the raised shelf never above its start
    with np.errstate(invalid="ignore"):
        raised = bed.changed & ~np.isnan(inner.H) & (bed.H > inner.H)
    r["highest_bed"] = round(float(Z.max()), 3)
    r["bed_nodes_above_cap"] = int((Z > CAP + 1e-6).sum())
    r["raised_shelf_highest"] = round(float(bed.H[raised].max()), 3) if raised.any() else None
    # the edges: where the bed meets the ground. Each bed node beside ground against the lowest ground
    # beside it (the rule), and against every ground node of its four neighbours (a step)
    nz, nx = bed.H.shape
    e = bed.edge_bed
    er, ec, ez = br[e], bc[e], Z[e].astype(float)
    G0 = np.where(np.isnan(inner.H), np.nan, bed.H)  # the ground the edit found, as the edit leaves it
    low = lowest_beside(G0, er, ec)
    gap = low - ez
    capped = low > START + 1e-6
    hi4 = np.full(len(er), -np.inf)
    lo4 = np.full(len(er), np.inf)
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = np.clip(er + dr, 0, nz - 1), np.clip(ec + dc, 0, nx - 1)
        g = G0[rr, cc].astype(float)
        hi4 = np.where(np.isnan(g), hi4, np.maximum(hi4, g))
        lo4 = np.where(np.isnan(g), lo4, np.minimum(lo4, g))
    step = np.where(np.isfinite(hi4), hi4 - ez, 0.0)
    big = (step > 0.25) & ~capped
    two = big & np.isfinite(lo4) & (hi4 - lo4 > 0.2)
    r["edges"] = {"bed_nodes_beside_ground": int(len(er)),
                  "under_the_lowest_ground_beside_it_m": [round(float(gap[~capped].min()), 4), round(float(gap[~capped].max()), 4)],
                  "held_at_cap_beside_ground_above_-8": int(capped.sum()),
                  "that_ground_m": [round(float(low[capped].min()), 2), round(float(low[capped].max()), 2)] if capped.any() else None,
                  "steps_over_0.25_m_elsewhere": int(big.sum()),
                  "of_them_between_ground_at_two_heights": int(two.sum()),
                  "steps_over_1_m_elsewhere": int(((step > 1.0) & ~capped).sum())}
    if big.any():
        k = np.nonzero(big)[0]
        worst = k[np.argsort(-step[k])[:6]]
        r["edges"]["worst"] = [[round(float(inner.xs[ec[i]]), 1), round(float(inner.zs[er[i]]), 1), round(float(step[i]), 2),
                               round(float(lo4[i]), 2), round(float(hi4[i]), 2)] for i in worst]
    # the bed by depth
    a = inner.step ** 2 / 1e6
    r["bed_area_by_depth_km2"] = {k: round(float(((Z <= hi) & (Z > lo)).sum()) * a, 2) for k, (lo, hi) in {
        "-8..-20": (-20, -8), "-20..-40": (-40, -20), "-40..-60": (-60, -40), "-60..-100": (-100, -60),
        "-100..-200": (-200, -100), "below -200": (-1e9, -200)}.items()}
    # the generator's buffer: ground that had ground before and changed, inside it
    cr, cc = np.nonzero(bed.changed & ~np.isnan(inner.H))
    gen, _ = generator_weight(sea.feet, sea, inner.xs[cc], inner.zs[cr])
    r["existing_ground_changed"] = {"nodes": int(len(cr)), "inside_the_generator_buffer": int((gen <= 0.0).sum()),
                                    "in_its_taper": int(((gen > 0.0) & (gen < 1.0)).sum())}
    r["beach_town"] = sea.report["beach_town_shore_cells"]
    r["shore_km"] = sea.report["shore_km"]
    return r


# --- writing: one recorded edit through the grid's own `apply_arrays` -----------------------------------

def write(bed, extra):
    """Records the bed, the raised shelf and the harbour's foot as one edit, `EDIT_NAME`, through
    `ground_grid_edit.apply_arrays` (`apply_values` for arrays, both tiers): heights where they
    changed, colours where they changed; the nodes that had ground are checked against what was read,
    and every file read must be as it was. Undo with `ground_grid_edit.py --undo`."""
    if not hasattr(gge, "apply_arrays"):
        raise SystemExit("seabed: tools/ground_grid_edit.py has no apply_arrays (the two-tier writer); "
                         "a seabed is too many nodes for apply_values")
    inner = bed.inner
    for hashes in [inner.hashes] + ([bed.outer.hashes] if bed.outer is not None else []):
        for path, h in hashes.items():
            if file_sha(path) != h:
                raise SystemExit("seabed: %s changed since it was read: run again" % path)
    r, c = np.nonzero(bed.changed)
    x = inner.xs[c].astype(np.float64)
    z = inner.zs[r].astype(np.float64)
    y = bed.H[r, c].astype(np.float64)
    expect = inner.H[r, c].astype(np.float64)
    given = ~np.isnan(expect)
    pr, pc = np.nonzero(bed.painted)
    cx = inner.xs[pc].astype(np.float64)
    cz = inner.zs[pr].astype(np.float64)
    col = bed.C[pr, pc, :3]
    cexp = inner.C[pr, pc]
    cgiven = inner.C[pr, pc, 3] == 255
    if bed.outer is not None:
        o = bed.outer
        orr, occ = bed.outer_rc
        x = np.concatenate([x, o.xs[occ].astype(np.float64)])
        z = np.concatenate([z, o.zs[orr].astype(np.float64)])
        y = np.concatenate([y, bed.outer_y.astype(np.float64)])
        expect = np.concatenate([expect, np.full(len(orr), np.nan)])
        given = np.concatenate([given, np.zeros(len(orr), bool)])
        cx = np.concatenate([cx, o.xs[occ].astype(np.float64)])
        cz = np.concatenate([cz, o.zs[orr].astype(np.float64)])
        col = np.concatenate([col, bed.outer_rgb])
        cexp = np.concatenate([cexp, np.zeros((len(orr), 4), np.uint8)])
        cgiven = np.concatenate([cgiven, np.zeros(len(orr), bool)])
    log("writing %d heights and %d colours" % (len(x), len(cx)))
    return gge.apply_arrays(bed.root, EDIT_NAME, EDIT_WHY, x, z, y, expect=expect, expect_given=given,
                            made_by="tools/blender/seabed_build.py", show=5, colour_x=cx, colour_z=cz, colour=col,
                            colour_expect=cexp, colour_expect_given=cgiven, extra=extra)


# --- the chart (plain Python with Pillow) ---------------------------------------------------------------

def srgb_to_linear(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=float), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


# The C3 proposals' chart: a depth ramp on a log scale, plain land, contours every 10 m to 100 m and
# every 100 m below; its domain the land's box and `MARGIN`, in whole 2.4 km cells.
DEPTH_RAMP = [(0.0, (0.86, 0.95, 0.96)), (10.0, (0.70, 0.88, 0.93)), (20.0, (0.56, 0.80, 0.90)), (40.0, (0.42, 0.69, 0.85)),
              (60.0, (0.31, 0.58, 0.79)), (100.0, (0.20, 0.44, 0.69)), (200.0, (0.13, 0.31, 0.56)),
              (400.0, (0.08, 0.19, 0.41)), (600.0, (0.04, 0.11, 0.28))]
LAND_CHART = (0.84, 0.81, 0.74)
CHART_CELL = 2400.0
CHART_PX = 1600


def depth_u(d):
    return np.log1p(np.maximum(d, 0.0) / 10.0) / math.log1p(600.0 / 10.0)


class GridSurface:
    """Both tiers' bilinear surface, Godot (x, z): the inner tier inside its domain, the outer beyond."""

    def __init__(self, root):
        self.inner = Inner(root)
        spec = json.load(open(os.path.join(root, "grid.json")))
        self.outer = Outer(root, self.inner) if "outer" in spec else None
        i = self.inner
        self.si = Surface(i.H, i.x0, i.z0, i.step)
        self.so = Surface(self.outer.with_inner(i.H, i), self.outer.x0, self.outer.z0, self.outer.step) \
            if self.outer is not None else None

    def at(self, x, z):
        b = self.inner.box
        inside = (x >= b[0]) & (x <= b[1]) & (z >= b[2]) & (z <= b[3])
        v = np.where(inside, self.si.at(x, z), np.nan)
        if self.so is not None:
            v = np.where(inside, v, self.so.at(x, z))
        return v


def chart(root, out, report_path):
    """The bathymetric chart of the grid as it stands, in the C3 proposals' style."""
    from PIL import Image, ImageDraw, ImageFont
    ctxg = json.load(open(report_path))["context"] if report_path else None
    gs = GridSurface(root)
    i = gs.inner
    with np.errstate(invalid="ignore"):
        gr, gcol = np.nonzero(~np.isnan(i.H) & (i.H > SEA))  # the land, as C3's chart framed it
    lx0, lx1 = i.xs[gcol].min(), i.xs[gcol].max()
    lz0, lz1 = i.zs[gr].min(), i.zs[gr].max()
    nx = int(math.ceil((lx1 - lx0 + 2 * MARGIN) / CHART_CELL))
    nz = int(math.ceil((lz1 - lz0 + 2 * MARGIN) / CHART_CELL))
    cx, cz = (lx0 + lx1) / 2, (lz0 + lz1) / 2
    X0, X1 = cx - nx * CHART_CELL / 2, cx + nx * CHART_CELL / 2
    Z0, Z1 = cz - nz * CHART_CELL / 2, cz + nz * CHART_CELL / 2
    W = CHART_PX
    Hpx = int(round(W * (Z1 - Z0) / (X1 - X0)))
    px = (X1 - X0) / W
    XS, ZS = np.meshgrid(X0 + (np.arange(W) + 0.5) * px, Z0 + (np.arange(Hpx) + 0.5) * px)
    h = gs.at(XS, ZS)
    depth = SEA - h
    under = ~np.isnan(h) & (depth > 0)
    us = [float(depth_u(d)) for d, _ in DEPTH_RAMP]
    u = depth_u(np.where(np.isnan(depth), 600.0, depth))
    img = np.stack([np.interp(u, us, [c[k] for _, c in DEPTH_RAMP]) for k in range(3)], -1)
    # the land, lit from the west-south-west as the proposals' sun was
    hz = np.where(np.isnan(h), SEA, h)
    gz, gx = np.gradient(hz, px)
    n = np.stack([-gx, np.ones_like(gx), -gz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    sun = np.array([-0.55, 0.62, 0.30])
    sun /= np.linalg.norm(sun)
    lit = np.clip((n * sun).sum(-1), 0.0, 1.0)
    land = ~np.isnan(h) & ~under
    grey = srgb_to_linear(np.array(LAND_CHART))
    shade = np.clip(0.35 + 0.85 * lit, 0.0, 1.1)
    img[land] = linear_to_srgb(grey[None, :] * shade[land][:, None])
    levels = [10.0 * k for k in range(1, 11)] + [100.0 * k for k in range(2, 7)]
    for L in levels:
        a = depth > L - 0.3
        e = np.zeros_like(a)
        e[1:, :] |= a[1:, :] != a[:-1, :]
        e[:, 1:] |= a[:, 1:] != a[:, :-1]
        e &= under
        major = (L % 100 == 0) or L == 50.0
        if major:
            e = dilate(e, 1) & under
        img[e] = (0.06, 0.13, 0.26) if major else (0.16, 0.27, 0.42)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)

    def P(x, z):
        return ((x - X0) / px, (z - Z0) / px)

    def line(pts, width_m, colour):
        dr.line([P(x, z) for x, z in pts], fill=colour, width=max(1, int(round(width_m / px))))

    if ctxg:
        zx0, zx1, zz0, zz1 = ctxg["zone"]
        line([(zx0, zz0), (zx1, zz0), (zx1, zz1), (zx0, zz1), (zx0, zz0)], 22.0, (217, 26, 140))
        line(ctxg["ferry"], 18.0, (242, 115, 13))
        for f in ctxg["footings"]:
            zc = (f["z"][0] + f["z"][1]) / 2
            line([(f["x"][0] - 15, zc), (f["x"][1] + 15, zc)], 30.0, (217, 13, 13))

    def font(size):
        for path in ("/System/Library/Fonts/Supplemental/GillSans.ttc", "/System/Library/Fonts/Helvetica.ttc"):
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    white = (242, 242, 242)
    Wm = X1 - X0
    tx, tz = X0 + 0.04 * Wm, Z0 + 0.04 * Wm
    dr.text(P(tx, tz), "Seabed C3 in the height grid", fill=white, font=font(int(380 / px)))
    dr.text(P(tx, tz + 600), "contours every 10 m to 100 m, then every 100 m\nmagenta: the park's west-shore box, with its own bed\n"
                               "orange: the ferry route   red: the bridge footings", fill=(235, 235, 235), font=font(int(150 / px)))
    stops = [0, 10, 20, 40, 60, 100, 200, 400, 600]
    seg = 0.055 * Wm
    ly = Z1 - 0.04 * Wm
    for k, d in enumerate(stops[:-1]):
        mid = float(depth_u((d + stops[k + 1]) / 2))
        col = [np.interp(mid, us, [c[j] for _, c in DEPTH_RAMP]) for j in range(3)]
        x0 = X0 + 0.04 * Wm + k * seg
        dr.rectangle([P(x0, ly - 480), P(x0 + seg, ly - 180)], fill=tuple(int(v * 255) for v in col))
        dr.text(P(x0 - 60, ly - 120), "%d" % d, fill=white, font=font(int(170 / px)))
    dr.text(P(X0 + 0.04 * Wm + 8 * seg - 160, ly - 120), "%d m" % stops[-1], fill=white, font=font(int(170 / px)))
    sx = X0 + 0.04 * Wm
    dr.rectangle([P(sx, ly - 930), P(sx + 2000, ly - 870)], fill=white)
    dr.text(P(sx + 2100, ly - 1010), "2 km", fill=white, font=font(int(170 / px)))
    im.save(out)
    print("seabed: chart %s, %d x %d, x %.0f..%.0f, z %.0f..%.0f" % (out, W, Hpx, X0, X1, Z0, Z1))


# --- the aerial (Blender) -------------------------------------------------------------------------------
# The C3 proposals' aerial: 820 m up over the bay's south-west, looking north-east at the park, the
# headland and the plug; the water as the game's sea shader reads it (tint by depth straight down,
# see-through over the first `CLARITY` m along the view, the darker deep step); grey stand-ins for the
# ground the grid does not hold (the road corridor, the park's own land and decks); the bridge, the
# ferries and their landings appended from the city source for the render only.
SHALLOW = (0.30, 0.50, 0.52)
DEEP = (0.34, 0.44, 0.52)
REACH = 12.0
CLARITY = 3.0
SURFACE = 0.25
DEEPER = (0.17, 0.27, 0.38)
DEEPER_FROM = 30.0
DEEPER_REACH = 80.0
WATER_GAIN = (2.65, 2.5, 2.25)
AERIAL = ((-1250.0, 820.0, 1750.0), (-180.0, -7.5, 250.0), 26.0)
# the meshes the frame is drawn from: every Nth node of each tier
AERIAL_STRIDE = {"inner": 3, "outer": 2}


def render_group():
    """The game's sea over the bed: tint by depth straight down, see-through near the surface."""
    import bpy
    ng = bpy.data.node_groups.new("KYT_seabed_render", "ShaderNodeTree")
    ng.interface.new_socket("Bed", in_out="INPUT", socket_type="NodeSocketShader")
    ng.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    N, Lk = ng.nodes, ng.links
    gin = N.new("NodeGroupInput")
    gout = N.new("NodeGroupOutput")
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Position"], sep.inputs[0])

    def op(kind, a=None, b=None, va=None, vb=None):
        m = N.new("ShaderNodeMath")
        m.operation = kind
        if a is not None:
            Lk.new(a, m.inputs[0])
        elif va is not None:
            m.inputs[0].default_value = va
        if b is not None:
            Lk.new(b, m.inputs[1])
        elif vb is not None:
            m.inputs[1].default_value = vb
        return m.outputs[0]

    depth = op("SUBTRACT", va=SEA, b=sep.outputs["Z"])
    under = op("GREATER_THAN", a=depth, vb=0.0)
    dpos = op("MAXIMUM", a=depth, vb=0.0)
    isep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Incoming"], isep.inputs[0])
    cosv = op("MAXIMUM", a=op("ABSOLUTE", a=isep.outputs["Z"]), vb=0.05)
    through = op("DIVIDE", a=dpos, b=cosv)
    cover = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=through, vb=-CLARITY)))
    alpha = N.new("ShaderNodeMix")
    alpha.data_type = "FLOAT"
    alpha.inputs[2].default_value = SURFACE
    alpha.inputs[3].default_value = 1.0
    Lk.new(cover, alpha.inputs[0])
    afac = op("MULTIPLY", a=alpha.outputs[0], b=under)
    rf = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=dpos, vb=-REACH)))
    gain = np.array(WATER_GAIN)
    tint = N.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.inputs[6].default_value = (*(srgb_to_linear(SHALLOW) * gain), 1.0)
    tint.inputs[7].default_value = (*(srgb_to_linear(DEEP) * gain), 1.0)
    Lk.new(rf, tint.inputs[0])
    r2 = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=op("MAXIMUM", a=op("SUBTRACT", a=dpos, vb=DEEPER_FROM), vb=0.0),
                                                             vb=-DEEPER_REACH)))
    tint2 = N.new("ShaderNodeMix")
    tint2.data_type = "RGBA"
    Lk.new(r2, tint2.inputs[0])
    Lk.new(tint.outputs[2], tint2.inputs[6])
    tint2.inputs[7].default_value = (*(srgb_to_linear(DEEPER) * gain), 1.0)
    wem = N.new("ShaderNodeEmission")
    Lk.new(tint2.outputs[2], wem.inputs["Color"])
    mix = N.new("ShaderNodeMixShader")
    Lk.new(afac, mix.inputs[0])
    Lk.new(gin.outputs["Bed"], mix.inputs[1])
    Lk.new(wem.outputs[0], mix.inputs[2])
    Lk.new(mix.outputs[0], gout.inputs["Shader"])
    return ng


def ground_material(ng, name="scratch_ground"):
    """The grid's colour (the mesh's `Col`, linear) lit as matte ground, through the water."""
    import bpy
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Color"])
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = ng
    nt.links.new(bsdf.outputs[0], g.inputs["Bed"])
    nt.links.new(g.outputs["Shader"], out.inputs["Surface"])
    return m


def flat_material(name, colour, ng=None, emit=True):
    import bpy
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if emit:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*srgb_to_linear(colour[:3]), 1.0)
        sh = em.outputs[0]
    else:
        df = nt.nodes.new("ShaderNodeBsdfDiffuse")
        df.inputs["Color"].default_value = (*srgb_to_linear(colour[:3]), 1.0)
        sh = df.outputs[0]
    if ng is not None:
        g = nt.nodes.new("ShaderNodeGroup")
        g.node_tree = ng
        nt.links.new(sh, g.inputs["Bed"])
        sh = g.outputs["Shader"]
    nt.links.new(sh, out.inputs["Surface"])
    return m


def grid_mesh(name, H, C, x0, z0, step, stride, mat, collection, keep=None):
    """A mesh of every `stride`th node with height, a quad for each cell with four; Blender (x, -z, y);
    `Col` the node's colour, linear."""
    import bpy
    Hs = H[::stride, ::stride]
    Cs = C[::stride, ::stride] if C is not None else None
    ok = ~np.isnan(Hs)
    if keep is not None:
        ok &= keep[::stride, ::stride]
    idx = -np.ones(Hs.shape, np.int64)
    idx[ok] = np.arange(int(ok.sum()))
    r, c = np.nonzero(ok)
    V = np.column_stack([x0 + step * stride * c, -(z0 + step * stride * r), Hs[r, c]]).astype(np.float32)
    q = ok[:-1, :-1] & ok[1:, :-1] & ok[1:, 1:] & ok[:-1, 1:]
    qr, qc = np.nonzero(q)
    F = np.column_stack([idx[qr, qc], idx[qr + 1, qc], idx[qr + 1, qc + 1], idx[qr, qc + 1]])  # up, seen from above
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    me.loops.add(4 * len(F))
    me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(len(F)) * 4)
    me.update()
    if Cs is not None:
        lin = srgb_to_linear(Cs[r, c, :3] / 255.0)
        col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        col.data.foreach_set("color", np.column_stack([lin, np.ones(len(lin))]).astype(np.float32).ravel())
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def aerial(bed, out):
    """The aerial frame of the grid after the edit (or as it would be, with `--dry`)."""
    import bpy
    from mathutils import Vector
    inner, sea = bed.inner, bed.sea
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    try:
        scene.eevee.taa_render_samples = 32
    except AttributeError:
        pass
    world = bpy.data.worlds.new("scratch_world")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*srgb_to_linear((0.62, 0.72, 0.85)), 1.0)
    bg.inputs[1].default_value = 0.9
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.2
    sun_data.angle = math.radians(1.0)
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (math.radians(52.0), 0.0, math.radians(-62.0))
    scene.collection.objects.link(sun)
    col = bpy.data.collections.new("scratch_aerial")
    scene.collection.children.link(col)
    ng = render_group()
    mat = ground_material(ng)
    log("aerial: meshes")
    grid_mesh("scratch_inner", bed.H, bed.C, inner.x0, inner.z0, inner.step, AERIAL_STRIDE["inner"], mat, col)
    if bed.outer is not None:
        o = bed.outer
        OH = o.with_inner(bed.H, inner)
        OC = np.zeros(OH.shape + (3,), np.uint8)
        r, c = np.nonzero(~o.own)
        OC[r, c] = bed.C[np.rint((o.zs[r] - inner.z0) / inner.step).astype(int), np.rint((o.xs[c] - inner.x0) / inner.step).astype(int), :3]
        orr, occ = bed.outer_rc
        OH[orr, occ] = bed.outer_y
        OC[orr, occ] = bed.outer_rgb
        # one cell in under the inner tier, so the two meet without a crack
        keep = o.own | dilate(o.own, AERIAL_STRIDE["outer"] + 1)
        OH = np.where(keep, OH, np.nan)
        grid_mesh("scratch_outer", OH, np.concatenate([OC, np.full(OH.shape + (1,), 255, np.uint8)], -1),
                  o.x0, o.z0, o.step, AERIAL_STRIDE["outer"], mat, col)
    # the void beyond the grid reads as the floor's water
    vme = bpy.data.meshes.new("scratch_void")
    R = 60000.0
    vme.from_pydata([(-R, -R, -3000.0), (R, -R, -3000.0), (R, R, -3000.0), (-R, R, -3000.0)], [], [(0, 1, 2, 3)])
    t1 = 1.0 - math.exp(-480.0 / REACH)
    cvoid = srgb_to_linear(SHALLOW) * (1 - t1) + srgb_to_linear(DEEP) * t1
    t2 = 1.0 - math.exp(-max(0.0, 480.0 - DEEPER_FROM) / DEEPER_REACH)
    cvoid = (cvoid * (1 - t2) + srgb_to_linear(DEEPER) * t2) * np.array(WATER_GAIN)
    vm = flat_material("scratch_void", (0, 0, 0))
    next(n_ for n_ in vm.node_tree.nodes if n_.type == "EMISSION").inputs["Color"].default_value = (*cvoid, 1.0)
    vme.materials.append(vm)
    col.objects.link(bpy.data.objects.new("scratch_void", vme))
    # grey stand-ins where the grid holds no ground and the game does: the road corridor and the
    # tunnel lids at the highway's height, the park's own land from its collision
    s = 2
    Hs = bed.H[::s, ::s]
    hole = np.isnan(Hs)
    rr, cc = np.nonzero(hole)
    X = inner.xs[::s][cc].astype(float)
    Z = inner.zs[::s][rr].astype(float)
    hw = bed.ctx["highway"]
    d_hw, arc = polyline_distance(hw[:, :2], X, -Z)
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(hw[:, :2], axis=0).T))])
    Zs = np.where(d_hw < 70.0, np.interp(arc, cum, hw[:, 2]) - 0.3, np.nan)
    ptop, inside = sea.park_at(X, -Z, sea.pk_top)
    Zs = np.where(inside & ~np.isnan(ptop), ptop, Zs)
    keep = ~np.isnan(Zs)
    X, Z, Zs = X[keep], Z[keep], Zs[keep]
    iz, ix = np.nonzero(sea.pk_struct)
    X = np.concatenate([X, sea.pk_x0 + ix * 4.0])
    Z = np.concatenate([Z, sea.pk_z0 + iz * 4.0])
    Zs = np.concatenate([Zs, sea.pk_top[iz, ix]])
    half = np.concatenate([np.full(int(keep.sum()), s * inner.step * 0.58), np.full(len(ix), 2.3)])
    n = len(X)
    sv = np.concatenate([np.column_stack([X + dx * half, -Z + dy * half, Zs]) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    sme = bpy.data.meshes.new("scratch_standin")
    sme.vertices.add(len(sv))
    sme.vertices.foreach_set("co", sv.astype(np.float32).ravel())
    sme.loops.add(4 * n)
    sme.loops.foreach_set("vertex_index", np.column_stack([np.arange(n) + k * n for k in range(4)]).ravel())
    sme.polygons.add(n)
    sme.polygons.foreach_set("loop_start", np.arange(n) * 4)
    sme.update()
    sme.materials.append(flat_material("scratch_standin", (0.62, 0.62, 0.6), ng, emit=False))
    col.objects.link(bpy.data.objects.new("scratch_standin", sme))
    with bpy.data.libraries.load(CITY_SOURCE, link=False) as (src, dst):
        dst.objects = [n_ for n_ in src.objects if n_.startswith(("bridge_", "city_ferry", "beach_town_ferry", "bay_ferry"))]
    for ob in dst.objects:
        if ob is not None:
            col.objects.link(ob)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_start = 2.0
    cam_data.clip_end = 60000.0
    eye, aim, lens = AERIAL
    cam_data.type = "PERSP"
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.lens = lens
    e = Vector((eye[0], -eye[2], eye[1]))
    a = Vector((aim[0], -aim[2], aim[1]))
    cam.location = e
    cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    scene.render.filepath = out
    log("aerial: rendering")
    bpy.ops.render.render(write_still=True)
    log("aerial: %s" % out)


# --- main ---------------------------------------------------------------------------------------------

def jsonable(o):
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]

    def opt(flag, default=None):
        return argv[argv.index(flag) + 1] if flag in argv else default

    root = os.path.abspath(opt("--root", GROUND))
    report_path = opt("--report")
    if "--chart" in argv:
        chart(root, opt("--chart"), report_path)
        return
    global DEAN_CARRIES_DOWN
    if "--as-drawn" in argv:
        DEAN_CARRIES_DOWN = False
    if "--carry-down" in argv:
        DEAN_CARRIES_DOWN = True
    stride = int(opt("--stride", "1"))
    dry = "--dry" in argv or stride > 1
    bed = Bed(root, stride)
    log("measuring")
    m = measure(bed)
    report = {"tool": "tools/blender/seabed_build.py", "date": datetime.date.today().isoformat(), "root": root,
              "dry": dry, "stride": stride, "profile_carries_down": DEAN_CARRIES_DOWN, "build": bed.report, "measured": m,
              "context": context_godot(bed.ctx, bed.sea)}
    print("seabed: %s" % json.dumps(m, default=jsonable))
    if not dry:
        summary = {"seabed": {"option": "C3", "bed_nodes": bed.report["inner"]["bed_nodes"],
                              "shelf_nodes_raised": bed.report["sandy_shelf"]["nodes_raised"],
                              "harbour_foot_nodes": bed.report["harbour_foot"]["nodes"]}}
        summary["seabed"]["profile_carries_down"] = DEAN_CARRIES_DOWN
        report["edit"] = write(bed, summary)
    if report_path:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=1, default=jsonable)
        log("report: %s" % report_path)
    if opt("--aerial"):
        aerial(bed, opt("--aerial"))


if __name__ == "__main__":
    main()
