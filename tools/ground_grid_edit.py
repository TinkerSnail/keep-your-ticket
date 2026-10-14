"""Named edits to the ground's height grid, logged and undoable.

Stage 2 of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-13): the first edits to
the grid itself, `assets/source/world_ground/height/`. Each is a named function below that says
which nodes it changes and to what, computed from the grid as it stands, so running it again on
the same grid gives the same bytes. `baseline/` is the frozen copy and is never touched: an edit
reads as a change in `WorldTerrainSource.delta_y`, and what the generator places on the ground
follows it.

    python3 tools/ground_grid_edit.py --list
    python3 tools/ground_grid_edit.py <edit> [--dry] [--root DIR]
    python3 tools/ground_grid_edit.py --values FILE.npz --name NAME --why "LINE" [--dry] [--root DIR]
    python3 tools/ground_grid_edit.py --undo [--dry] [--root DIR]

- **`--values`** (2026-10-14, Stage 3) records an edit from new heights rather than from a named
  function here: the nodes' world `x` and `z` (even metres) and new heights `y`, as arrays in an
  `.npz`, optionally `expect`, the heights the editor started from. It is how an editor's save
  becomes an edit like G1-G7 (the Blender panel's Save tiles calls `apply_values` in-process). Only
  nodes whose height moves by more than `MIN_CHANGE` (1 mm) are written, so every other node stays
  bit for bit; a node with `expect` that the grid no longer holds is refused, as is a node off the
  lattice or outside the grid, and a height that is not finite (ground is never removed this way).
  The name is short snake_case and the why one line, both the editor's own words. Colours may come
  in the same edit (Photoshop's save, `tools/ground_paint.py`, calls `apply_values` with
  `colours`): in the `.npz`, `colour_x`, `colour_z` and `colour` (N x 3 bytes), optionally
  `colour_expect` (N x 4); only for ground, and only where the colour changes. A tile whose colour
  alone changes has no height record, and undo restores its PNG's bytes.

- **The log.** Each edit appends to `edits.json`: its id (G1, G2, ...), name, date, why (one line),
  the tiles it touched and how many nodes, and how many of them it gave ground that had none. The
  nodes' previous values go to `history/G<n>.npz`, with each touched tile's file hash before and
  after, and the previous bytes of every colour PNG it touched.
- **Colour.** Where an edit gives ground to a node that had none (NaN), the node takes the mean
  colour of its nearest coloured neighbours, alpha 255, in `colour/`; that is recorded too.
- **Shared edges.** A node on a tile's edge is written in every tile that holds it.
- **`--dry`** says what would change and writes nothing.
- **`--undo`** takes back the last edit (LIFO) from its history: the nodes' old values and, where the
  tile has not been touched since, its bytes exactly (checked against the recorded hash); a colour
  PNG whose pixels are back to what they were gets its old bytes back. It removes the log entry and
  its history file.
- **`--root DIR`** works on another copy of `assets/source/world_ground/` (a proof's scratch copy).

After an edit: rebuild the touched tiles (`Blender -b --factory-startup --python
tools/blender/ground_build.py -- --tiles ...`), import, run `tools/ground_mount.gd`, and read
`tools/world_terrain_delta.gd -- --grid` before regenerating.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ground_bake as gb  # noqa: E402  (its EXR reader and writer)
import ground_colour_bake as gc  # noqa: E402  (its PNG reader and writer)

GROUND = os.path.join(ROOT, "assets", "source", "world_ground")


# --- the grid -----------------------------------------------------------------

class Grid:
    """`grid.json`'s lattice; nodes addressed by world (x, z) on even metres."""

    def __init__(self, root):
        self.root = root
        spec = json.load(open(os.path.join(root, "grid.json")))
        self.step = float(spec["spacing_m"])
        self.n = int(spec["tile_samples"])
        self.per = self.n - 1
        self.tile_m = float(spec["tile_m"])
        self.tx = range(spec["tiles_x"][0], spec["tiles_x"][1] + 1)
        self.tz = range(spec["tiles_z"][0], spec["tiles_z"][1] + 1)
        self.h = {}
        self.c = {}

    def path(self, folder, tx, tz, ext):
        return os.path.join(self.root, folder, "x%d_z%d.%s" % (tx, tz, ext))

    def heights(self, tx, tz):
        if (tx, tz) not in self.h:
            self.h[(tx, tz)] = gb.read_exr(self.path("height", tx, tz, "exr"))[0].copy()
        return self.h[(tx, tz)]

    def colour(self, tx, tz):
        if (tx, tz) not in self.c:
            self.c[(tx, tz)] = gc.png_read(self.path("colour", tx, tz, "png")).copy()
        return self.c[(tx, tz)]

    def homes(self, x, z):
        """Every (tile, row, column) holding the node at world (x, z)."""
        c = int(round(x / self.step))
        r = int(round(z / self.step))
        assert abs(c * self.step - x) < 1e-9 and abs(r * self.step - z) < 1e-9, "not a node: %r" % ((x, z),)
        out = []
        for tx in {c // self.per, (c - 1) // self.per}:
            for tz in {r // self.per, (r - 1) // self.per}:
                if tx in self.tx and tz in self.tz:
                    cc, rr = c - tx * self.per, r - tz * self.per
                    if 0 <= cc < self.n and 0 <= rr < self.n:
                        out.append(((tx, tz), rr, cc))
        return sorted(out)

    def get(self, x, z):
        homes = self.homes(x, z)
        if not homes:
            return np.nan
        (tx, tz), r, c = homes[0]
        return float(self.heights(tx, tz)[r, c])

    def rgba(self, x, z):
        (tx, tz), r, c = self.homes(x, z)[0]
        return self.colour(tx, tz)[r, c]


def ring(x, z, step, k=1, diagonal=True):
    for dx in range(-k, k + 1):
        for dz in range(-k, k + 1):
            if (dx or dz) and (diagonal or not (dx and dz)):
                yield x + dx * step, z + dz * step


# --- the edits ----------------------------------------------------------------
# Each takes the grid and returns {(x, z): new height}. Nodes are listed where they were found
# (2026-10-13, from the faces Godot loads and the grid), so the edit is the same every run.

def r7_slot(g):
    """G1. Two cracks in T6 along the feet of its risers by R7 and route D, a metre or less wide,
    through which only T2's base sheet at -0.06 m showed: in the faces an embankment dived into
    them; in the grid the nodes there carry the risers' faces or a pit. Each crack node takes the
    level of the foot ground beside it (the mean of its non-crack neighbours within 1 m of the
    lowest of them), so the foot runs level to the riser and the riser stands on it."""
    nodes = [(134, 76), (134, 78), (136, 80), (136, 82), (138, 86), (138, 88), (130, 90), (130, 92)]
    out = {}
    for (x, z) in nodes:
        nb = [g.get(a, b) for (a, b) in ring(x, z, g.step) if (a, b) not in nodes]
        nb = [v for v in nb if not np.isnan(v)]
        lo = min(nb)
        out[(x, z)] = float(np.mean([v for v in nb if v <= lo + 1.0]))
    return out


def _fill_land(g, nodes, land_from=-1.0):
    """Each node, nearest the land first, takes the mean of its four neighbours that are land
    (ground at or above `land_from`), counting nodes already filled."""
    out = {}
    todo = list(nodes)
    while todo:
        done = []
        for (x, z) in todo:
            nb = []
            for (a, b) in ring(x, z, g.step, diagonal=False):
                v = out.get((a, b), g.get(a, b))
                if not np.isnan(v) and v >= land_from:
                    nb.append(v)
            if nb:
                done.append(((x, z), float(np.mean(nb))))
        if not done:
            raise SystemExit("no land beside %s" % todo)
        for k, v in done:
            out[k] = v
            todo.remove(k)
    return out


def route_c_gap(g):
    """G2. Route C's gap at the west shell: a strip of nodes with no ground (x -54..-52, z 74..86)
    between the coast's -6.1 m and the reserve's -0.2 m, all under the bluff's top (-0.01 m, x -58
    to -51). They take the land beside them, under the bluff's top, so the strip has ground."""
    nodes = [(-54, z) for z in range(74, 85, 2)] + [(-52, z) for z in range(74, 87, 2)]
    assert all(np.isnan(g.get(x, z)) for (x, z) in nodes), "route C's gap is no longer empty"
    return _fill_land(g, nodes)


def west_shell_step(g):
    """G3. The S2/C step at the west shell: where the coast's -6 m runs on inside the bluff
    (x -58 to -51) to the node at x -56, the grid ramps the 6 m step across the cell inside the
    bluff, and a bank's toe follows it down. Those nodes (route C, z 72..84; S2, z 166..172) take
    the land beside them, so the step lies in the cell at the bluff's sea face (x -58..-56), inside
    the solid, and the land runs to it."""
    nodes = [(-56, z) for z in range(72, 85, 2)] + [(-56, z) for z in range(166, 173, 2)]
    assert all(g.get(x, z) < -1.0 for (x, z) in nodes), "the step at the west shell has moved"
    return _fill_land(g, nodes)


## The margin a floor's ground is held under its top by: 2 cm, and 2 cm more for the tiles, which
## follow the grid's bilinear surface to within 2 cm in the park.
FLOOR_MARGIN = 0.04


def _hold_under(g, nodes, floor_y):
    """Each node takes the floor's foot level: its lowest four-neighbour, but no higher than the
    floor's top less `FLOOR_MARGIN` and no lower than 10 cm under that. The nodes were found by
    sampling the floor's walkable collision tops every 10 cm and along every edge (2026-10-13),
    lowering, cell by cell, the node that put the grid's bilinear surface highest over them, until
    none stood within the margin."""
    limit = floor_y - FLOOR_MARGIN
    out = {}
    for (x, z) in nodes:
        nb = [g.get(a, b) for (a, b) in ring(x, z, g.step, diagonal=False)]
        out[(x, z)] = float(max(min(limit, min(v for v in nb if not np.isnan(v))), limit - 0.1))
    return out


def r5_queue(g):
    """G4. R5's queue (x 46.0..53.4, z 106.6..109.0, floor 0.0048 m) ends 0.6 m short of the east
    shoulder's riser, whose foot the master held at the queue's edge; the grid's cell from x 52 to
    54 ramped up across that edge, 0.43 m over the floor. The riser's foot row at x 54 over the
    queue takes the queue's ground level, so the riser starts at x 54."""
    return _hold_under(g, [(54, 106), (54, 108), (54, 110)], 0.0048)


def r10_queue(g):
    """G5. R10's queue winds along a hollow in the east shoulder (floor 10.87..10.92 m) whose banks
    meet its edges within a metre; the grid's cells round the hollow carried the banks up to
    0.39 m over the floor. The nodes the banks stood on take the hollow's floor level."""
    nodes = [(84, -94), (84, -92), (86, -98), (86, -96), (86, -94), (88, -100), (88, -90), (88, -88),
             (88, -86), (90, -100), (90, -98), (90, -96), (90, -94), (90, -92), (92, -98)]
    return _hold_under(g, nodes, 10.8710)


def r7_queue_end_bed(g):
    """G6. The stone bed at the end of R7's queue (a disc of 1.1 m round (131.65, 69.05), top
    4.9455 m) stands at the foot of T6's batter; the master's batter rose 0.11 m over its edge, the
    grid's 0.53 m. The batter's foot nodes round it take the bed's foot level."""
    return _hold_under(g, [(130, 68), (132, 66), (132, 68), (134, 68), (134, 70)], 4.9455)


def _mosaic(g):
    """The whole lattice as one array, row r at z = Z0 + 2r, column c at x = X0 + 2c."""
    nx = len(g.tx) * g.per + 1
    nz = len(g.tz) * g.per + 1
    H = np.full((nz, nx), np.nan, np.float32)
    for tz in g.tz:
        for tx in g.tx:
            r0 = (tz - g.tz[0]) * g.per
            c0 = (tx - g.tx[0]) * g.per
            H[r0:r0 + g.n, c0:c0 + g.n] = g.heights(tx, tz)
    return H, g.tx[0] * g.tile_m, g.tz[0] * g.tile_m


def _held_mask(g, shape, x0, z0):
    """Nodes strictly inside a held body's outline in `holes.json`, even-odd per body, odd plan
    corners joined nearest first, as `WorldTerrainSource` reads them."""
    held = np.zeros(shape, bool)
    for body in json.load(open(os.path.join(g.root, "holes.json")))["holes"]:
        edges = []
        degree = {}
        for ch in body["chains"]:
            P = [(p[0], p[2]) for p in ch["points"]]
            n = len(P)
            for e in range(n if ch["closed"] else n - 1):
                a, b = P[e], P[(e + 1) % n]
                edges.append((a, b))
                degree[a] = degree.get(a, 0) + 1
                degree[b] = degree.get(b, 0) + 1
        odd = [k for k, v in degree.items() if v % 2]
        while len(odd) > 1:
            a = odd.pop()
            j = min(range(len(odd)), key=lambda i: (odd[i][0] - a[0]) ** 2 + (odd[i][1] - a[1]) ** 2)
            edges.append((a, odd.pop(j)))
        rows = {}
        for (a, b) in edges:
            if a[1] == b[1]:
                continue
            for r in range(int(np.ceil((min(a[1], b[1]) - z0) / g.step)), int(np.floor((max(a[1], b[1]) - z0) / g.step)) + 1):
                z = z0 + g.step * r
                if (a[1] <= z < b[1]) or (b[1] <= z < a[1]):
                    rows.setdefault(r, []).append(a[0] + (z - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
        for r, xs in rows.items():
            if not 0 <= r < shape[0]:
                continue
            xs.sort()
            for m in range(len(xs) - 1):
                if (len(xs) - m - 1) % 2 == 0:
                    continue
                for c in range(max(0, int(np.floor((xs[m] - x0) / g.step))), min(shape[1] - 1, int(np.ceil((xs[m + 1] - x0) / g.step))) + 1):
                    if xs[m] < x0 + g.step * c < xs[m + 1]:
                        held[r, c] = True
    return held


## `ParkPlan.REBUILD_FOOTPRINT_*`: x min, x max, z min, z max.
PARK_ENVELOPE = (-212.0, 222.0, -230.0, 220.0)


def interior_pinholes(g):
    """G7. Nodes with no ground enclosed by ground: where the master had a face too steep for
    `_top` (a near-vertical riser at a regrade cut's edge, a seam), the bake left a hole that is a
    real hole in the game's ground. A no-data region is filled when it does not reach the edge of
    the grid (the sea beyond the shelves stays empty) and holds no node inside a held body's outline
    (the corridor, the lids and NT-2's earth stay holes, and so does any region joined to them).
    Nor is a region that reaches into the developed park (`PARK_ENVELOPE`): the park's ground is
    unedited, and its open cuts are where the generator lays floors in them (route B's north return
    runs down through one to the boardwalk; filled, it was buried up to 10 m). The fill: each node, from the region's rim inward, takes the mean of its four neighbours that
    hold ground (its eight where no four-neighbour does yet)."""
    import collections
    H, x0, z0 = _mosaic(g)
    nz, nx = H.shape
    nan = np.isnan(H)
    outer = np.zeros_like(nan)
    q = collections.deque()
    edge = np.zeros_like(nan)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    for r, c in np.argwhere(nan & edge):
        outer[r, c] = True
        q.append((int(r), int(c)))
    while q:
        r, c = q.popleft()
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= rr < nz and 0 <= cc < nx and nan[rr, cc] and not outer[rr, cc]:
                outer[rr, cc] = True
                q.append((rr, cc))
    held = _held_mask(g, H.shape, x0, z0)
    enclosed = nan & ~outer
    seen = np.zeros_like(nan)
    fill = []
    for r0, c0 in np.argwhere(enclosed):
        r0, c0 = int(r0), int(c0)
        if seen[r0, c0]:
            continue
        seen[r0, c0] = True
        q = collections.deque([(r0, c0)])
        members = []
        while q:
            r, c = q.popleft()
            members.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < nz and 0 <= cc < nx and enclosed[rr, cc] and not seen[rr, cc]:
                        seen[rr, cc] = True
                        q.append((rr, cc))
        in_park = any(PARK_ENVELOPE[0] <= x0 + g.step * c <= PARK_ENVELOPE[1]
                      and PARK_ENVELOPE[2] <= z0 + g.step * r <= PARK_ENVELOPE[3] for r, c in members)
        if not in_park and not any(held[r, c] for r, c in members):
            fill.extend(members)
    todo = set(fill)
    V = H.astype(np.float64)
    while todo:
        done = {}
        for (r, c) in todo:
            nb = [V[rr, cc] for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                  if 0 <= rr < nz and 0 <= cc < nx and not np.isnan(V[rr, cc])]
            if nb:
                done[(r, c)] = float(np.mean(nb))
        if not done:
            for (r, c) in todo:
                nb = [V[rr, cc] for rr in (r - 1, r, r + 1) for cc in (c - 1, c, c + 1)
                      if 0 <= rr < nz and 0 <= cc < nx and not np.isnan(V[rr, cc])]
                if nb:
                    done[(r, c)] = float(np.mean(nb))
        if not done:
            raise SystemExit("a pinhole region has no ground round it")
        for k, v in done.items():
            V[k] = v
            todo.discard(k)
    return {(x0 + g.step * c, z0 + g.step * r): float(V[r, c]) for (r, c) in fill}


EDITS = {
    "r7_slot": (r7_slot, "fill the cracks at the feet of T6's risers by R7 so the foot runs level"),
    "route_c_gap": (route_c_gap, "give route C's empty strip under the west shell's bluff the land beside it"),
    "west_shell_step": (west_shell_step, "hold the land to the bluff's sea face at S2 and route C"),
    "r5_queue": (r5_queue, "hold the ground 2 cm under R5's queue: the riser's foot row moves to x 54"),
    "r10_queue": (r10_queue, "hold the ground 2 cm under R10's queue in its hollow"),
    "r7_queue_end_bed": (r7_queue_end_bed, "hold the ground 2 cm under the stone bed at R7's queue end"),
    "interior_pinholes": (interior_pinholes, "fill the no-data regions enclosed by ground and clear of held outlines"),
}


# --- applying and undoing -----------------------------------------------------

def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_log(root):
    p = os.path.join(root, "edits.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {"about": "Named edits to the height grid, in order, by tools/ground_grid_edit.py; "
                     "history/<id>.npz keeps each edit's previous values. Undo is LIFO.",
            "edits": []}


def save_log(root, log):
    p = os.path.join(root, "edits.json")
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(log, f, indent=1)
        f.write("\n")
    os.replace(tmp, p)


def new_colour(g, x, z, filled):
    """Mean colour of the nearest coloured neighbours (alpha 255), widening the ring until some."""
    for k in range(1, 13):
        cols = []
        for (a, b) in ring(x, z, g.step, k):
            if max(abs(a - x), abs(b - z)) != k * g.step or (a, b) in filled:
                continue
            if not g.homes(a, b):
                continue
            p = g.rgba(a, b)
            if p[3] == 255:
                cols.append(p[:3].astype(np.float64))
        if cols:
            rgb = np.clip(np.rint(np.mean(cols, axis=0)), 0, 255).astype(np.uint8)
            return np.array([rgb[0], rgb[1], rgb[2], 255], np.uint8)
    raise SystemExit("no coloured node near (%g, %g)" % (x, z))


def apply(root, name, dry):
    fn, why = EDITS[name]
    g = Grid(root)
    return record(g, name, why, fn(g), dry)


def record(g, name, why, changes, dry, extra=None, show=None, paint=None):
    """Writes `changes`, {(x, z): new height}, into the grid as the next edit, with its history and
    its log entry (plus `extra`'s fields); prints the first `show` nodes (all when None). Returns
    the log entry, or None when `dry`. `paint`, {(x, z): RGBA bytes} (2026-10-14, the Photoshop
    save), sets those nodes' colour too, whether or not their height changes; a node given ground
    without one takes its neighbours' (`new_colour`). A tile only painted has no height record."""
    root = g.root
    log = load_log(root)
    gid = "G%d" % (len(log["edits"]) + 1)
    per_tile = {}
    made = []
    for (x, z), v in sorted(changes.items()):
        old = g.get(x, z)
        if np.isnan(old):
            made.append((x, z))
        for (tx, tz), r, c in g.homes(x, z):
            per_tile.setdefault((tx, tz), []).append((r, c, np.float32(v), (x, z)))
    paint = paint or {}
    colours = {(x, z): new_colour(g, x, z, set(made)) for (x, z) in made if (x, z) not in paint}
    colours.update({k: np.asarray(v, np.uint8) for k, v in paint.items()})
    per_colour = {}
    for (x, z), rgba in sorted(colours.items()):
        for (tx, tz), r, c in g.homes(x, z):
            per_colour.setdefault((tx, tz), []).append((r, c, rgba))
    tiles = sorted(set(per_tile) | set(per_colour))
    print("%s %s: %d nodes in %s; %d given ground that had none; %swhy: %s" % (
        gid, name, len(changes), ", ".join("x%d_z%d" % t for t in tiles), len(made),
        "%d nodes' colour painted; " % len(paint) if paint else "", why))
    for k, ((x, z), v) in enumerate(sorted(changes.items())):
        if show is not None and k == show:
            print("  ... and %d more" % (len(changes) - show))
            break
        print("  (%g, %g): %s -> %.3f%s" % (x, z, "none" if np.isnan(g.get(x, z)) else "%.3f" % g.get(x, z), v,
                                           "  colour %s" % [int(v) for v in colours[(x, z)]] if (x, z) in colours else ""))
    if dry:
        print("dry: nothing written")
        return None
    hist = {}
    record_tiles = []
    for (tx, tz) in tiles:
        key = "x%d_z%d" % (tx, tz)
        if (tx, tz) in per_tile:
            h = g.heights(tx, tz)
            hp = g.path("height", tx, tz, "exr")
            before = sha(hp)
            rows = np.array([e[0] for e in per_tile[(tx, tz)]], np.int32)
            cols = np.array([e[1] for e in per_tile[(tx, tz)]], np.int32)
            hist["h_%s_idx" % key] = rows * g.n + cols
            hist["h_%s_old" % key] = h[rows, cols].copy()
            h[rows, cols] = np.array([e[2] for e in per_tile[(tx, tz)]], np.float32)
            hist["h_%s_new" % key] = h[rows, cols].copy()
            gb.write_exr(hp, h)
            rec = {"tile": key, "nodes": int(len(rows)), "height_sha_before": before, "height_sha_after": sha(hp)}
        else:
            rec = {"tile": key, "nodes": 0}
        cidx = per_colour.get((tx, tz), [])
        if cidx:
            cp = g.path("colour", tx, tz, "png")
            hist["c_%s_png" % key] = np.frombuffer(open(cp, "rb").read(), np.uint8)
            img = g.colour(tx, tz)
            cr = np.array([e[0] for e in cidx], np.int32)
            cc = np.array([e[1] for e in cidx], np.int32)
            hist["c_%s_idx" % key] = cr * g.n + cc
            hist["c_%s_old" % key] = img[cr, cc].copy()
            img[cr, cc] = np.array([e[2] for e in cidx], np.uint8)
            hist["c_%s_new" % key] = img[cr, cc].copy()
            gc.png_write(cp, img)
            rec["colour_nodes"] = int(len(cidx))
        record_tiles.append(rec)
    os.makedirs(os.path.join(root, "history"), exist_ok=True)
    hpath = os.path.join(root, "history", gid + ".npz")
    np.savez_compressed(hpath, **hist)
    entry = {
        "id": gid, "name": name, "date": datetime.date.today().isoformat(), "why": why,
        "tiles": [r["tile"] for r in record_tiles], "nodes": len(changes), "new_ground_nodes": len(made),
        "history": "history/%s.npz" % gid, "files": record_tiles,
    }
    entry.update(extra or {})
    log["edits"].append(entry)
    save_log(root, log)
    print("%s written: %s, %s" % (gid, ", ".join(r["tile"] for r in record_tiles), hpath))
    return entry


## The least a node must move for an editor's save to write it; a node that moves less keeps its
## bytes exactly.
MIN_CHANGE = 0.001
NAME_RE = re.compile(r"[a-z0-9][a-z0-9_]{0,39}$")


def apply_values(root, name, why, values, expect=None, dry=False, min_change=MIN_CHANGE, made_by=None,
                 show=40, colours=None, colour_expect=None, extra=None):
    """Records new heights as the next edit: `values` {(x, z): height}, world metres, x and z on
    the lattice. `expect` {(x, z): height} is what the editor read at those nodes; a node the grid
    no longer holds at that value (float32, bit for bit, in every tile holding it) is refused, so a
    save never overwrites what changed on disk since it was read. A node within `min_change` of
    the grid is left out. Returns the log entry, or None when nothing moved (or `dry`). Raises
    SystemExit with a sentence for anything refused, before writing anything.

    `colours` {(x, z): RGB or RGBA bytes} (2026-10-14, the Photoshop save, `ground_paint.py`) are
    new colours in the same edit, alpha 255; only for nodes with ground (now or by this edit), and
    a colour the grid already holds is left out. `colour_expect` {(x, z): RGBA} is what the editor
    read there, refused like `expect`. `extra` adds fields to the log entry."""
    if not NAME_RE.match(name or ""):
        raise SystemExit("the edit's name must be short snake_case (a-z, 0-9 and _, up to 40), not %r" % (name,))
    why = " ".join((why or "").split())
    if not why:
        raise SystemExit("say in one line why the edit is made")
    g = Grid(root)
    changes = {}
    stale = []
    for (x, z), v in values.items():
        x, z, v = float(x), float(z), float(v)
        if not np.isfinite(v):
            raise SystemExit("(%g, %g): the new height is not a number; ground is never removed this way" % (x, z))
        if x / g.step != round(x / g.step) or z / g.step != round(z / g.step):
            raise SystemExit("(%g, %g) is not a node of the grid (every %g m)" % (x, z, g.step))
        homes = g.homes(x, z)
        if not homes:
            raise SystemExit("(%g, %g) is outside the grid" % (x, z))
        held = [g.heights(tx, tz)[r, c] for (tx, tz), r, c in homes]
        if expect is not None and (x, z) in expect:
            e = np.float32(expect[(x, z)]).tobytes()
            if any(np.float32(h).tobytes() != e for h in held):
                stale.append((x, z))
                continue
        old = float(held[0])
        if np.isnan(old) or abs(float(np.float32(v)) - old) > min_change:
            changes[(x, z)] = float(np.float32(v))
    paint = {}
    for (x, z), v in (colours or {}).items():
        x, z = float(x), float(z)
        rgba = np.array([int(v[0]), int(v[1]), int(v[2]), 255], np.uint8)
        if x / g.step != round(x / g.step) or z / g.step != round(z / g.step):
            raise SystemExit("(%g, %g) is not a node of the grid (every %g m)" % (x, z, g.step))
        homes = g.homes(x, z)
        if not homes:
            raise SystemExit("(%g, %g) is outside the grid" % (x, z))
        if np.isnan(g.get(x, z)) and (x, z) not in changes:
            raise SystemExit("(%g, %g) has no ground to colour" % (x, z))
        held = [g.colour(tx, tz)[r, c] for (tx, tz), r, c in homes]
        if colour_expect is not None and (x, z) in colour_expect:
            e = np.asarray(colour_expect[(x, z)], np.uint8)
            if any(not np.array_equal(h, e) for h in held):
                stale.append((x, z))
                continue
        if not np.array_equal(held[0], rgba):
            paint[(x, z)] = rgba
    if stale:
        tiles = sorted({"x%d_z%d" % t for (x, z) in stale for t, _, _ in g.homes(x, z)})
        raise SystemExit("%d of the nodes changed in %s since they were read (another edit, an undo or "
                         "a Photoshop save): read them again before saving" % (len(stale), ", ".join(tiles)))
    if not changes and not paint:
        print("nothing moved by more than %g m%s: no edit recorded" % (
            min_change, " and no colour changed" if colours else ""))
        return None
    extra_all = {"kind": "values", "min_change_m": min_change}
    if made_by:
        extra_all["made_by"] = made_by
    extra_all.update(extra or {})
    return record(g, name, why, changes, dry, extra_all, show, paint=paint)


def undo(root, dry):
    log = load_log(root)
    if not log["edits"]:
        raise SystemExit("nothing to undo")
    e = log["edits"][-1]
    g = Grid(root)
    hist = np.load(os.path.join(root, e["history"]))
    print("undo %s %s: %d nodes in %s" % (e["id"], e["name"], e["nodes"], ", ".join(e["tiles"])))
    if dry:
        print("dry: nothing written")
        return
    for rec in e["files"]:
        key = rec["tile"]
        tx, tz = (int(v) for v in key[1:].split("_z"))
        if "h_%s_idx" % key in hist.files:  # a tile only painted has no heights to restore
            hp = g.path("height", tx, tz, "exr")
            untouched = sha(hp) == rec["height_sha_after"]
            h = g.heights(tx, tz)
            idx = hist["h_%s_idx" % key]
            h.reshape(-1)[idx] = hist["h_%s_old" % key]
            gb.write_exr(hp, h)
            back = sha(hp) == rec["height_sha_before"]
            print("  %s heights: %d nodes restored; %s" % (key, len(idx), "the tile bit for bit" if back else (
                "the tile was changed since, so only these nodes" if not untouched else "BYTES DIFFER")))
            if not back and untouched:
                raise SystemExit("undo of %s did not restore %s exactly" % (e["id"], hp))
        if "c_%s_png" % key in hist.files:
            cp = g.path("colour", tx, tz, "png")
            img = g.colour(tx, tz)
            cidx = hist["c_%s_idx" % key]
            img.reshape(-1, 4)[cidx] = hist["c_%s_old" % key]
            old_bytes = hist["c_%s_png" % key].tobytes()
            tmp = cp + ".undo"
            with open(tmp, "wb") as f:
                f.write(old_bytes)
            same = np.array_equal(gc.png_read(tmp), img)
            if same:
                os.replace(tmp, cp)
            else:
                os.remove(tmp)
                gc.png_write(cp, img)
            print("  %s colour: %d nodes restored; %s" % (key, len(cidx), "its old bytes" if same else
                                                          "painted since, so only these nodes"))
    os.remove(os.path.join(root, e["history"]))
    log["edits"].pop()
    save_log(root, log)
    print("undone: %s" % e["id"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("edit", nargs="?", choices=sorted(EDITS))
    ap.add_argument("--undo", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--values", help="an .npz of x, z, y (and optionally expect): record those heights as an edit")
    ap.add_argument("--name", help="with --values: the edit's short snake_case name")
    ap.add_argument("--why", help="with --values: one line, why")
    ap.add_argument("--root", default=GROUND)
    a = ap.parse_args()
    if a.list:
        for k, (fn, why) in EDITS.items():
            print("%-16s %s" % (k, why))
        for e in load_log(a.root)["edits"]:
            print("%s %s %s: %d nodes in %s" % (e["id"], e["date"], e["name"], e["nodes"], ", ".join(e["tiles"])))
        return
    if a.undo:
        undo(a.root, a.dry)
    elif a.values:
        d = np.load(a.values)
        keys = list(zip(d["x"].astype(np.float64).tolist(), d["z"].astype(np.float64).tolist()))
        values = dict(zip(keys, d["y"].astype(np.float64).tolist()))
        expect = dict(zip(keys, d["expect"].tolist())) if "expect" in d.files else None
        colours = colour_expect = None
        if "colour" in d.files:
            ck = list(zip(d["colour_x"].astype(np.float64).tolist(), d["colour_z"].astype(np.float64).tolist()))
            colours = dict(zip(ck, d["colour"].astype(np.uint8)))
            if "colour_expect" in d.files:
                colour_expect = dict(zip(ck, d["colour_expect"].astype(np.uint8)))
        apply_values(a.root, a.name, a.why, values, expect, a.dry, made_by="ground_grid_edit.py --values",
                     colours=colours, colour_expect=colour_expect)
    elif a.edit:
        apply(a.root, a.edit, a.dry)
    else:
        ap.error("name an edit, or --values, --undo or --list")


if __name__ == "__main__":
    main()
