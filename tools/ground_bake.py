#!/usr/bin/env python3
"""The ground's height grid, baked from the faces the generator measures it from.

Stage 1, Bake, of `documentation/terrain-height-grid-plan-2026-10-12.md`
(2026-10-12). Nothing in the game reads what this writes yet.

    Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --out=<faces>
    python3 tools/ground_bake.py bake --faces <faces>
    python3 tools/ground_bake.py points --faces <faces> --out <points.f32>
    Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --delta=<points.f32>,<delta.f64>
    Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --read=<abs>/assets/source/world_ground/height,<godot>/height
    Blender -b --factory-startup --python tools/ground_bake.py -- blender-read <abs>/assets/source/world_ground/height <blender>/height
    python3 tools/ground_bake.py prove --faces <faces> --probe documentation/terrain/heightfield-baseline-1926e71 \
        --delta <points.f32>,<delta.f64> --godot <godot> --blender <blender> --report <report.json>
    python3 tools/ground_bake.py frames --out <dir>

`bake` writes, to `assets/source/world_ground/` as its `grid.json` says:
  `height/`   the master's ground: at every node the height of the top face over
              it, exactly as `WorldTerrainSource._top` finds it;
  `baseline/` the same from the frozen copy the generator measures change from;
  `holes.json` the outlines of the ground the generator still holds (the road
              corridor, the tunnel lids, NT-2's earth and climb cuts), chained
              from their dumped open edges, every corner bit for bit; and the
              lines where the master's own open edges lie on the held solids
              that have none (the west shell, NT-1 and NT-2's CSG).
It never writes `colour/`.

The rasteriser mirrors `_top`, operation for operation, so a node reads what
the generator would read there: a face is skipped when its normal is flatter
than MIN_UP (|n.y| < 0.05 |n|, in float32 as Godot's Vector3 does it; up- and
down-facing faces alike), a node is tested only against faces indexed in its
8m cell, and the edge vectors are float32 while the barycentric weights and the
height are float64; the highest wins. The heights are stored float32. At every
node of a changed cell, H - B before that rounding is `delta_y` bit for bit.
`_top` takes a down-facing face as readily as an up-facing one, which the
game's one-sided collision does not: 86 nodes at `1926e71` (74 on the north
plug's sand infill, the rest on range north, the city's foothills and coast
north), 67 of them over 1 cm above the top up-facing face, at most 12.3 m.
The run is deterministic: the same dump writes the same bytes.

Every Godot path above is absolute; `Godot` and `Blender` are the apps' binaries.

An EXR here is one float32 channel named Y (OpenEXR's grey), ZIP-compressed,
scanlines from the north edge; written and read by this file alone (numpy and
zlib), and read bit for bit by OpenImageIO, Blender and Godot (Godot loads it
as RGBF with the value in each of r, g and b).

Run with `blender-read` inside Blender, the file is its own helper: it loads
each EXR as a Blender image and writes its first channel as raw float32.
"""

import argparse
import gzip
import json
import os
import struct
import sys
import time
import zlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND = os.path.join(ROOT, "assets", "source", "world_ground")

# `scripts/world_terrain_source.gd`'s constants.
CELL = 8.0
MIN_UP = 0.05
INSIDE_EPS = 1e-6
DEN_MIN = 1e-9

F32 = np.float32
F64 = np.float64


# --- EXR: one float32 channel, scanline, NONE / ZIPS / ZIP -------------------

EXR_MAGIC = 20000630
EXR_NONE, EXR_ZIPS, EXR_ZIP = 0, 2, 3
EXR_LINES = {EXR_NONE: 1, EXR_ZIPS: 1, EXR_ZIP: 16}
CHANNEL = "Y"


def _exr_attr(name, typ, data):
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<i", len(data)) + data


def _exr_zip(raw):
    """OpenEXR's ZIP: bytes split odd from even, a delta predictor, zlib."""
    b = np.frombuffer(raw, np.uint8)
    half = (len(b) + 1) // 2
    t = np.empty(len(b), np.int16)
    t[:half] = b[0::2]
    t[half:] = b[1::2]
    out = t.copy()
    out[1:] = (t[1:] - t[:-1] + 128 + 256) & 0xFF
    return zlib.compress(out.astype(np.uint8).tobytes(), 9)


def _exr_unzip(data, n):
    t = np.frombuffer(zlib.decompress(data), np.uint8).astype(np.int64)
    if len(t) != n:
        raise ValueError("EXR chunk inflates to %d bytes, not %d" % (len(t), n))
    t = (np.cumsum(np.concatenate([t[:1], t[1:] - 128])) & 0xFF).astype(np.uint8)
    half = (n + 1) // 2
    b = np.empty(n, np.uint8)
    b[0::2] = t[:half]
    b[1::2] = t[half:]
    return b.tobytes()


def write_exr(path, a, compression=EXR_ZIP):
    """`a` (rows, columns) as one float32 channel; row 0 is the image's top."""
    a = np.ascontiguousarray(a, "<f4")
    h, w = a.shape
    box = struct.pack("<iiii", 0, 0, w - 1, h - 1)
    head = struct.pack("<ii", EXR_MAGIC, 2)
    head += _exr_attr("channels", "chlist",
                      CHANNEL.encode() + b"\0" + struct.pack("<iB3xii", 2, 0, 1, 1) + b"\0")
    head += _exr_attr("compression", "compression", bytes([compression]))
    head += _exr_attr("dataWindow", "box2i", box)
    head += _exr_attr("displayWindow", "box2i", box)
    head += _exr_attr("lineOrder", "lineOrder", b"\0")
    head += _exr_attr("pixelAspectRatio", "float", struct.pack("<f", 1.0))
    head += _exr_attr("screenWindowCenter", "v2f", struct.pack("<ff", 0.0, 0.0))
    head += _exr_attr("screenWindowWidth", "float", struct.pack("<f", 1.0))
    head += b"\0"
    lines = EXR_LINES[compression]
    chunks = []
    for y in range(0, h, lines):
        raw = a[y:y + lines].tobytes()
        data = _exr_zip(raw) if compression != EXR_NONE else raw
        if len(data) >= len(raw):
            data = raw
        chunks.append(struct.pack("<ii", y, len(data)) + data)
    offset = len(head) + 8 * len(chunks)
    table = b""
    for c in chunks:
        table += struct.pack("<Q", offset)
        offset += len(c)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(head + table + b"".join(chunks))
    os.replace(tmp, path)


def read_exr(path):
    """A single-part scanline EXR of one float32 channel: (array, channel name)."""
    buf = open(path, "rb").read()
    magic, version = struct.unpack_from("<ii", buf, 0)
    if magic != EXR_MAGIC or (version & 0xFF) != 2 or version & 0x1A00:
        raise ValueError("%s: not a single-part scanline EXR" % path)
    p = 8
    attrs = {}
    while buf[p] != 0:
        e = buf.index(b"\0", p)
        name = buf[p:e].decode()
        p = e + 1
        e = buf.index(b"\0", p)
        typ = buf[p:e].decode()
        p = e + 1
        (n,) = struct.unpack_from("<i", buf, p)
        p += 4
        attrs[name] = (typ, buf[p:p + n])
        p += n
    p += 1
    chl = attrs["channels"][1]
    channels = []
    q = 0
    while chl[q] != 0:
        e = chl.index(b"\0", q)
        channels.append((chl[q:e].decode(), struct.unpack_from("<i", chl, e + 1)[0]))
        q = e + 1 + 16
    if len(channels) != 1 or channels[0][1] != 2:
        raise ValueError("%s: want one float32 channel, have %s" % (path, channels))
    comp = attrs["compression"][1][0]
    if comp not in EXR_LINES:
        raise ValueError("%s: compression %d not read here" % (path, comp))
    x0, y0, x1, y1 = struct.unpack("<iiii", attrs["dataWindow"][1])
    w, h = x1 - x0 + 1, y1 - y0 + 1
    lines = EXR_LINES[comp]
    n = (h + lines - 1) // lines
    offsets = struct.unpack_from("<%dQ" % n, buf, p)
    out = np.empty((h, w), "<f4")
    for o in offsets:
        y, size = struct.unpack_from("<ii", buf, o)
        rows = min(lines, y1 + 1 - y)
        raw_n = rows * w * 4
        data = buf[o + 8:o + 8 + size]
        raw = data if (comp == EXR_NONE or size == raw_n) else _exr_unzip(data, raw_n)
        out[y - y0:y - y0 + rows] = np.frombuffer(raw, "<f4").reshape(rows, w)
    return out, channels[0][0]


# --- the grid ---------------------------------------------------------------

class Grid:
    """`grid.json`: tiles of `tile_samples` nodes a side sharing their edges."""

    def __init__(self, path=os.path.join(GROUND, "grid.json")):
        g = json.load(open(path))
        self.spec = g
        self.step = float(g["spacing_m"])
        self.tile_m = float(g["tile_m"])
        self.n = int(g["tile_samples"])
        self.tx = list(range(g["tiles_x"][0], g["tiles_x"][1] + 1))
        self.tz = list(range(g["tiles_z"][0], g["tiles_z"][1] + 1))
        self.per = int(round(self.tile_m / self.step))
        assert self.per + 1 == self.n
        self.x0 = self.tile_m * self.tx[0]
        self.z0 = self.tile_m * self.tz[0]
        self.nx = self.per * len(self.tx) + 1
        self.nz = self.per * len(self.tz) + 1
        # `_top`'s cells are whole numbers of nodes from the grid's corner.
        self.cell_nodes = int(round(CELL / self.step))
        assert self.cell_nodes * self.step == CELL and (self.x0 / CELL).is_integer() \
            and (self.z0 / CELL).is_integer()

    def tiles(self):
        for tz in self.tz:
            for tx in self.tx:
                yield tx, tz

    def window(self, tx, tz):
        """The mosaic's rows and columns of tile (tx, tz)."""
        c = (tx - self.tx[0]) * self.per
        r = (tz - self.tz[0]) * self.per
        return slice(r, r + self.n), slice(c, c + self.n)

    def name(self, tx, tz):
        return "x%d_z%d.exr" % (tx, tz)

    def node_xz(self, i, j):
        return self.x0 + self.step * i, self.z0 + self.step * j


def write_tiles(mosaic, grid, folder):
    os.makedirs(folder, exist_ok=True)
    for tx, tz in grid.tiles():
        rows, cols = grid.window(tx, tz)
        write_exr(os.path.join(folder, grid.name(tx, tz)), mosaic[rows, cols].astype("<f4"))


def read_tiles(folder, grid, reader=None):
    """The tiles back as one mosaic; where tiles share an edge, checks it bit for bit."""
    out = np.full((grid.nz, grid.nx), np.nan, "<f4")
    seen = np.zeros((grid.nz, grid.nx), bool)
    bad = 0
    for tx, tz in grid.tiles():
        rows, cols = grid.window(tx, tz)
        path = os.path.join(folder, grid.name(tx, tz))
        a = reader(path) if reader else read_exr(path)[0]
        if a.shape != (grid.n, grid.n):
            raise ValueError("%s is %s, not %d square" % (path, a.shape, grid.n))
        prev = out[rows, cols]
        s = seen[rows, cols]
        bad += int(np.count_nonzero(s & (prev.view("<u4") != a.view("<u4"))))
        out[rows, cols] = a
        seen[rows, cols] = True
    return out, bad


# --- faces ------------------------------------------------------------------

def load_dump(folder):
    index = json.load(open(os.path.join(folder, "faces.json")))
    faces = {}
    for k in ("master", "baseline", "held"):
        faces[k] = np.fromfile(os.path.join(folder, k + ".f32"), "<f4").reshape(-1, 3, 3)
    faces["held_open"] = np.fromfile(os.path.join(folder, "held_open.f32"), "<f4").reshape(-1, 2, 3)
    return index, faces


def standing(F):
    """`_index`'s test, in float32 as Godot's Vector3 does it: the face carries a
    height unless |n.y| < |n| * MIN_UP. Also n.y (float32) and |n|."""
    a, b, c = F[:, 0], F[:, 1], F[:, 2]
    u = b - a
    w = c - a
    nx = u[:, 1] * w[:, 2] - u[:, 2] * w[:, 1]
    ny = u[:, 2] * w[:, 0] - u[:, 0] * w[:, 2]
    nz = u[:, 0] * w[:, 1] - u[:, 1] * w[:, 0]
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    keep = ~(np.abs(ny).astype(F64) < length.astype(F64) * MIN_UP)
    return keep, ny, length


def _expand(counts):
    counts = np.asarray(counts, np.int64)
    total = int(counts.sum())
    rep = np.repeat(np.arange(len(counts), dtype=np.int64), counts)
    starts = np.cumsum(counts) - counts
    return rep, np.arange(total, dtype=np.int64) - starts[rep]


def _chunks(counts, budget):
    cum = np.cumsum(counts)
    a = 0
    n = len(counts)
    base = 0
    while a < n:
        b = int(np.searchsorted(cum, base + budget, side="right"))
        b = min(max(b, a + 1), n)
        yield a, b
        base = cum[b - 1]
        a = b


def raster(F, ids, grid, budget=3_000_000):
    """Every (node, face) where a node of the grid lies over face `ids[k]` by
    `_top`'s rule, with the height there: yields (flat node, face, height f64).
    A node is tried against a face only if its 8m cell is one the face is
    indexed in (`_cells_of`), and only near the face's plan box."""
    A = F[ids]
    ax, ay, az = A[:, 0, 0].astype(F64), A[:, 0, 1].astype(F64), A[:, 0, 2].astype(F64)
    bx, by, bz = A[:, 1, 0].astype(F64), A[:, 1, 1].astype(F64), A[:, 1, 2].astype(F64)
    cx, cy, cz = A[:, 2, 0].astype(F64), A[:, 2, 1].astype(F64), A[:, 2, 2].astype(F64)
    # e0, e1 as Vector2: float64 differences rounded to float32.
    e0x = (bx - ax).astype(F32).astype(F64)
    e0z = (bz - az).astype(F32).astype(F64)
    e1x = (cx - ax).astype(F32).astype(F64)
    e1z = (cz - az).astype(F32).astype(F64)
    den = e0x * e1z - e1x * e0z
    dy1 = by - ay
    dy2 = cy - ay
    X = A[:, :, 0].astype(F64)
    Z = A[:, :, 2].astype(F64)
    xmin, xmax = X.min(1), X.max(1)
    zmin, zmax = Z.min(1), Z.max(1)
    # `_top` accepts a point within INSIDE_EPS of the face in barycentric terms:
    # no further out than 2 eps times its longest edge; the rest is float32
    # rounding of the edge vectors. The margin is generous on both.
    edge = np.sqrt(np.maximum.reduce([(X[:, i] - X[:, j]) ** 2 + (Z[:, i] - Z[:, j]) ** 2
                                      for i, j in ((0, 1), (1, 2), (2, 0))]))
    m = 1e-5 * edge + 0.01
    cn = grid.cell_nodes
    ox = int(round(grid.x0 / CELL))
    oz = int(round(grid.z0 / CELL))
    cx0 = np.floor(xmin / CELL).astype(np.int64) - ox
    cx1 = np.floor(xmax / CELL).astype(np.int64) - ox
    cz0 = np.floor(zmin / CELL).astype(np.int64) - oz
    cz1 = np.floor(zmax / CELL).astype(np.int64) - oz
    i_lo = np.maximum(cx0 * cn, np.ceil((xmin - m - grid.x0) / grid.step).astype(np.int64))
    i_hi = np.minimum(cx1 * cn + cn - 1, np.floor((xmax + m - grid.x0) / grid.step).astype(np.int64))
    j_lo = np.maximum(cz0 * cn, np.ceil((zmin - m - grid.z0) / grid.step).astype(np.int64))
    j_hi = np.minimum(cz1 * cn + cn - 1, np.floor((zmax + m - grid.z0) / grid.step).astype(np.int64))
    np.maximum(i_lo, 0, out=i_lo)
    np.minimum(i_hi, grid.nx - 1, out=i_hi)
    np.maximum(j_lo, 0, out=j_lo)
    np.minimum(j_hi, grid.nz - 1, out=j_hi)
    ni = i_hi - i_lo + 1
    nj = j_hi - j_lo + 1
    live = np.nonzero((ni > 0) & (nj > 0) & ~(np.abs(den) < DEN_MIN))[0]
    counts = ni[live] * nj[live]
    for a, b in _chunks(counts, budget):
        rep, local = _expand(counts[a:b])
        t = live[a:b][rep]
        nir = ni[t]
        ii = i_lo[t] + local % nir
        jj = j_lo[t] + local // nir
        px = grid.x0 + grid.step * ii
        pz = grid.z0 + grid.step * jj
        e2x = (px - ax[t]).astype(F32).astype(F64)
        e2z = (pz - az[t]).astype(F32).astype(F64)
        d = den[t]
        u = (e2x * e1z[t] - e1x[t] * e2z) / d
        v = (e0x[t] * e2z - e2x * e0z[t]) / d
        inside = ~((u < -INSIDE_EPS) | (v < -INSIDE_EPS) | (u + v > 1.0 + INSIDE_EPS))
        t = t[inside]
        h = (ay[t] + u[inside] * dy1[t]) + v[inside] * dy2[t]
        yield jj[inside] * grid.nx + ii[inside], ids[t], h


def top(F, grid, keep=None, extra=False):
    """The highest standing face over every node: heights (float64, NaN for
    none) shaped (nz, nx), and with `extra` the top face's index (-1 for none)
    and the highest up-facing one's height (Godot's front, the winding a
    one-sided collider stands on)."""
    if keep is None:
        keep = standing(F)[0]
    ids = np.nonzero(keep)[0]
    H = np.full(grid.nz * grid.nx, -np.inf)
    pairs = []
    for node, face, h in raster(F, ids, grid):
        np.maximum.at(H, node, h)
        if extra:
            pairs.append((node.astype(np.int32), face.astype(np.int32), h))
    out = {"height": np.where(np.isinf(H), np.nan, H).reshape(grid.nz, grid.nx)}
    if extra:
        _, ny, _ = standing(F)
        front_up = ny < 0  # Godot's face normal is (a - c) x (a - b), the reverse of ny's
        T = np.full(grid.nz * grid.nx, -1, np.int64)
        U = np.full(grid.nz * grid.nx, -np.inf)
        for node, face, h in pairs:
            at = h == H[node]
            np.maximum.at(T, node[at], face[at].astype(np.int64))
            up = front_up[face]
            np.maximum.at(U, node[up], h[up])
        out["face"] = T.reshape(grid.nz, grid.nx)
        out["up"] = np.where(np.isinf(U), np.nan, U).reshape(grid.nz, grid.nx)
        out["front_up"] = front_up
    return out


# --- what changed since the copy (`_compare`, `_mark`) -----------------------

def _face_keys(F):
    """`_key`: a face's corners' float32 bytes, started at the smallest corner."""
    b = np.ascontiguousarray(F.astype("<f4")).view(np.uint8).reshape(-1, 3, 12)
    # Bytes compare as their hex text does, nibble for nibble.
    k = [np.frombuffer(np.ascontiguousarray(b[:, i]).tobytes(), "S12") for i in range(3)]
    a0 = (k[0] <= k[1]) & (k[0] <= k[2])
    a1 = ~a0 & (k[1] <= k[0]) & (k[1] <= k[2])
    start = np.where(a0, 0, np.where(a1, 1, 2))
    order = (start[:, None] + np.arange(3)[None, :]) % 3
    rolled = np.take_along_axis(b, order[:, :, None], axis=1).reshape(-1, 36)
    return np.ascontiguousarray(rolled).view("S36").ravel()


def changed_faces(M, B):
    """Faces the master has that the copy does not (added, master indices) and
    the reverse (removed, copy indices), as multisets."""
    km = _face_keys(M)
    kb = _face_keys(B)
    allk = np.concatenate([km, kb])
    uniq, inv = np.unique(allk, return_inverse=True)
    im, ib = inv[:len(km)], inv[len(km):]
    nb = np.bincount(ib, minlength=len(uniq))
    nm = np.bincount(im, minlength=len(uniq))
    # The i-th copy of a key on one side is matched if the other side has > i.
    def rank(ix):
        o = np.argsort(ix, kind="stable")
        s = ix[o]
        first = np.searchsorted(s, s, side="left")
        r = np.empty(len(ix), np.int64)
        r[o] = np.arange(len(ix)) - first
        return r
    added = np.nonzero(rank(im) >= nb[im])[0]
    removed = np.nonzero(rank(ib) >= nm[ib])[0]
    return added, removed


def dirty_cells(grid, *face_sets):
    """`_mark`: every 8m cell a changed face's plan box touches, as a grid of
    cells over the domain (True: dirty)."""
    ncx = (grid.nx - 1) // grid.cell_nodes + 1
    ncz = (grid.nz - 1) // grid.cell_nodes + 1
    out = np.zeros((ncz, ncx), bool)
    ox = int(round(grid.x0 / CELL))
    oz = int(round(grid.z0 / CELL))
    for F in face_sets:
        if len(F) == 0:
            continue
        X = F[:, :, 0].astype(F64)
        Z = F[:, :, 2].astype(F64)
        x0 = np.floor(X.min(1) / CELL).astype(np.int64) - ox
        x1 = np.floor(X.max(1) / CELL).astype(np.int64) - ox
        z0 = np.floor(Z.min(1) / CELL).astype(np.int64) - oz
        z1 = np.floor(Z.max(1) / CELL).astype(np.int64) - oz
        x0, x1 = np.clip(x0, 0, ncx - 1), np.clip(x1, 0, ncx - 1)
        z0, z1 = np.clip(z0, 0, ncz - 1), np.clip(z1, 0, ncz - 1)
        nx = x1 - x0 + 1
        nz = z1 - z0 + 1
        rep, local = _expand(nx * nz)
        out[z0[rep] + local // nx[rep], x0[rep] + local % nx[rep]] = True
    return out


def node_cells(grid, dirty):
    """Per node, whether its `_top` cell is dirty."""
    cn = grid.cell_nodes
    j = np.arange(grid.nz) // cn
    i = np.arange(grid.nx) // cn
    return dirty[j][:, i]


# --- holes ------------------------------------------------------------------

def _vkeys(P):
    return np.ascontiguousarray(P.astype("<f4")).view("S12").reshape(P.shape[:-1])


def chain(E):
    """Open edges into chains, corners matched bit for bit: a list of (corner
    indices into the unique corners, closed), the corners, and how many corners
    more than two open edges meet at. A closed chain's last corner joins its
    first; every open edge is in exactly one chain, once."""
    keys = _vkeys(E)
    uniq, inv = np.unique(keys.ravel(), return_inverse=True)
    corners = np.frombuffer(uniq.tobytes(), "<f4").reshape(-1, 3)
    ends = inv.reshape(-1, 2)
    adj = {}
    for e, (a, b) in enumerate(ends):
        adj.setdefault(int(a), []).append(e)
        adj.setdefault(int(b), []).append(e)
    pinches = sum(1 for v in adj.values() if len(v) > 2)
    used = np.zeros(len(ends), bool)

    def walk(cur, stop):
        out = []
        while True:
            free = [e for e in adj[cur] if not used[e]]
            if not free:
                return out, False
            e = min(free)
            used[e] = True
            x, y = int(ends[e][0]), int(ends[e][1])
            cur = y if x == cur else x
            if cur == stop:
                return out, True
            out.append(cur)

    chains = []
    for e0 in range(len(ends)):
        if used[e0]:
            continue
        used[e0] = True
        a, b = int(ends[e0][0]), int(ends[e0][1])
        ahead, closed = walk(b, a)
        path = [a, b] + ahead
        if not closed:
            behind, _ = walk(a, path[-1])
            path = behind[::-1] + path
        chains.append((path, closed))
    return chains, corners, pinches


def chain_edges(chains, corners):
    """The chains back as edges (n, 2, 3), for the check that they are the dump's."""
    out = []
    for path, closed in chains:
        idx = path + [path[0]] if closed else path
        for a, b in zip(idx[:-1], idx[1:]):
            out.append((corners[a], corners[b]))
    return np.array(out, "<f4").reshape(-1, 2, 3)


def same_edges(E1, E2):
    """Whether two edge lists hold the same undirected edges, bit for bit, as multisets."""
    def k(E):
        a, b = _vkeys(E[:, 0]), _vkeys(E[:, 1])
        lo = np.where(a <= b, a, b)
        hi = np.where(a <= b, b, a)
        return np.sort(np.char.add(lo.astype("S12"), hi.astype("S12")).astype(object))
    return len(E1) == len(E2) and bool(np.all(k(E1) == k(E2)))


def _seg_dist(P, A, B):
    """Distance from points P (n,3) to segments A-B (n,3) each."""
    d = B - A
    t = np.clip(np.einsum("ij,ij->i", P - A, d) / np.maximum(np.einsum("ij,ij->i", d, d), 1e-18), 0, 1)
    return np.linalg.norm(P - (A + t[:, None] * d), axis=1)


def master_open_edges(M):
    """The master's edges one face uses, corners matched bit for bit."""
    keys = _vkeys(M)
    uniq, inv = np.unique(keys.ravel(), return_inverse=True)
    t = inv.reshape(-1, 3)
    e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    s = np.sort(e, axis=1)
    k = s[:, 0].astype(np.int64) * len(uniq) + s[:, 1]
    uk, cnt = np.unique(k, return_counts=True)
    once = np.isin(k, uk[cnt == 1])
    P = np.frombuffer(uniq.tobytes(), "<f4").reshape(-1, 3)
    return P[e[once]]


class Buckets:
    """Items with plan boxes, bucketed by plan cell, for nearest queries."""

    def __init__(self, xmin, xmax, zmin, zmax, cell=4.0, big=400):
        self.cell = cell
        x0 = np.floor(xmin / cell).astype(np.int64)
        x1 = np.floor(xmax / cell).astype(np.int64)
        z0 = np.floor(zmin / cell).astype(np.int64)
        z1 = np.floor(zmax / cell).astype(np.int64)
        self.b = {}
        self.big = []
        for s in range(len(x0)):
            if (x1[s] - x0[s] + 1) * (z1[s] - z0[s] + 1) > big:
                self.big.append(s)
                continue
            for x in range(x0[s], x1[s] + 1):
                for z in range(z0[s], z1[s] + 1):
                    self.b.setdefault((x, z), []).append(s)

    def near(self, x, z, ring=1):
        cx, cz = int(np.floor(x / self.cell)), int(np.floor(z / self.cell))
        out = list(self.big)
        for i in range(cx - ring, cx + ring + 1):
            for j in range(cz - ring, cz + ring + 1):
                out += self.b.get((i, j), [])
        return np.array(sorted(set(out)), np.int64)


def nearest_segments(P, A, B):
    """Distance from each point to the nearest segment, and which (3D)."""
    A64, B64 = A.astype(F64), B.astype(F64)
    bk = Buckets(np.minimum(A64[:, 0], B64[:, 0]), np.maximum(A64[:, 0], B64[:, 0]),
                 np.minimum(A64[:, 2], B64[:, 2]), np.maximum(A64[:, 2], B64[:, 2]))
    out = np.full(len(P), np.inf)
    who = np.full(len(P), -1, np.int64)
    for k, p in enumerate(P.astype(F64)):
        cand = bk.near(p[0], p[2])
        if len(cand):
            d = _seg_dist(np.repeat(p[None], len(cand), 0), A64[cand], B64[cand])
            j = int(np.argmin(d))
            out[k], who[k] = d[j], cand[j]
    return out, who


def nearest_faces(P, H):
    """Distance from each point to the nearest face, and which (3D)."""
    X = H[:, :, 0].astype(F64)
    Z = H[:, :, 2].astype(F64)
    bk = Buckets(X.min(1), X.max(1), Z.min(1), Z.max(1))
    out = np.full(len(P), np.inf)
    who = np.full(len(P), -1, np.int64)
    for k, p in enumerate(P.astype(F64)):
        cand = bk.near(p[0], p[2], ring=0)
        if len(cand):
            d = _point_tri(p, H[cand].astype(F64))
            j = int(np.argmin(d))
            out[k], who[k] = d[j], cand[j]
    return out, who


def _point_tri(p, T):
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    best = np.full(len(T), np.inf)
    for u, v in ((a, b), (b, c), (c, a)):
        best = np.minimum(best, _seg_dist(np.repeat(p[None], len(T), 0), u, v))
    n = np.cross(b - a, c - a)
    nn = np.linalg.norm(n, axis=1)
    nu = n / np.maximum(nn, 1e-18)[:, None]
    dist = np.einsum("ij,ij->i", p - a, nu)
    q = p - dist[:, None] * nu
    v0, v1, v2 = c - a, b - a, q - a
    d00 = np.einsum("ij,ij->i", v0, v0)
    d01 = np.einsum("ij,ij->i", v0, v1)
    d11 = np.einsum("ij,ij->i", v1, v1)
    d20 = np.einsum("ij,ij->i", v2, v0)
    d21 = np.einsum("ij,ij->i", v2, v1)
    den = d00 * d11 - d01 * d01
    with np.errstate(all="ignore"):
        uu = (d11 * d20 - d01 * d21) / den
        vv = (d00 * d21 - d01 * d20) / den
    inside = (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (nn > 1e-12)
    return np.where(inside, np.minimum(best, np.abs(dist)), best)


EDGE_TOL = 0.005   # a master open edge runs along a held one: midpoint within 5 mm
SOLID_TOL = 0.05   # a master open edge lies on a held solid: midpoint within 5 cm of its faces


def build_holes(index, faces):
    """holes.json's content: per held body with open edges, its chains; and
    the master's open edges that lie on a held solid with none."""
    E = faces["held_open"]
    H = faces["held"]
    ME = master_open_edges(faces["master"])
    lens_m = np.linalg.norm(ME[:, 0].astype(F64) - ME[:, 1].astype(F64), axis=1)
    mid = (ME[:, 0].astype(F64) + ME[:, 1].astype(F64)) / 2
    d_open, who = nearest_segments(mid, E[:, 0], E[:, 1])
    along = d_open <= EDGE_TOL
    met_by = np.zeros(len(E))
    np.add.at(met_by, who[along], lens_m[along])
    holes = []
    for rec in index["held_open"]:
        if rec["count"] == 0:
            continue
        Ei = E[rec["first"]:rec["first"] + rec["count"]]
        chains, corners, pinches = chain(Ei)
        lens = np.linalg.norm(Ei[:, 0].astype(F64) - Ei[:, 1].astype(F64), axis=1)
        out = []
        for path, closed in chains:
            P = corners[path]
            x, z = P[:, 0].astype(F64), P[:, 2].astype(F64)
            area = 0.5 * abs(float(np.sum(x * np.roll(z, -1) - np.roll(x, -1) * z))) if closed else 0.0
            ring = np.concatenate([P, P[:1]]) if closed else P
            seg = np.linalg.norm(np.diff(ring.astype(F64), axis=0), axis=1)
            out.append({"closed": closed, "corners": len(path), "length_m": round(float(seg.sum()), 3),
                        "plan_area_m2": round(area, 3), "points": P})
        holes.append({"name": rec["name"], "open_edges": rec["count"], "pinch_corners": pinches,
                      "length_m": round(float(lens.sum()), 3),
                      "master_meets_m": round(float(met_by[rec["first"]:rec["first"] + rec["count"]].sum()), 3),
                      "chains": out, "_edges": Ei, "_chains": chains, "_corners": corners})
    # The master's open edges on held solids, which have no open edges of their own.
    solid = {r["name"] for r in index["held"]} - {r["name"] for r in index["held_open"] if r["count"]}
    fid = np.zeros(len(H), np.int64)
    names = []
    for k, r in enumerate(index["held"]):
        fid[r["first"]:r["first"] + r["count"]] = k
        names.append(r["name"])
    rest = np.nonzero(~along)[0]
    d_face, f = nearest_faces(mid[rest], H)
    on = {}
    for k, e in enumerate(rest):
        if d_face[k] <= SOLID_TOL and names[fid[f[k]]] in solid:
            on.setdefault(names[fid[f[k]]], []).append((int(e), float(d_face[k])))
    meets = []
    for name in sorted(on):
        es = np.array([e for e, _ in on[name]])
        meets.append({"name": name, "edges": len(es), "length_m": round(float(lens_m[es].sum()), 3),
                      "max_distance_m": round(max(d for _, d in on[name]), 4), "segments": ME[es]})
    stats = {"master_open_edges": int(len(ME)), "master_open_length_m": round(float(lens_m.sum()), 1),
             "along_held_open_edges": int(along.sum()),
             "along_held_open_edges_m": round(float(lens_m[along].sum()), 1),
             "on_held_solids": int(sum(m["edges"] for m in meets)),
             "on_held_solids_m": round(float(sum(m["length_m"] for m in meets)), 1),
             "edge_tolerance_m": EDGE_TOL, "solid_tolerance_m": SOLID_TOL}
    return holes, meets, stats


def _num(v):
    return str(F32(v))


def write_holes(path, holes, meets, stats, header):
    """JSON with every corner as its float32 value's shortest text."""
    def pts(P):
        return "[" + ", ".join("[%s, %s, %s]" % (_num(p[0]), _num(p[1]), _num(p[2])) for p in P) + "]"
    L = ["{"]
    L.append('  "about": %s,' % json.dumps(
        "Where the ground the generator still holds meets the master's (height-grid Stage 1, "
        "tools/ground_bake.py from tools/_ground_faces_dump.gd's dump). holes: each held body with "
        "open edges, its open edges chained, every corner its dumped float32 value, Godot world "
        "metres (x east, y up, z south); a closed chain's last corner joins its first; together the "
        "chains are the body's open edges exactly, each once. master_meets_m: how much of the "
        "master's own open edge runs along the body's (midpoint within edge_tolerance_m). meets: the "
        "master's open edges lying on a held solid (CSG, closed, so no open edges of its own), two "
        "corners each, the master's values."))
    L.append('  "source": %s,' % json.dumps(header))
    L.append('  "stats": %s,' % json.dumps(stats))
    L.append('  "holes": [')
    for hi, h in enumerate(holes):
        L.append("    {")
        for k in ("name", "open_edges", "pinch_corners", "length_m", "master_meets_m"):
            L.append('      "%s": %s,' % (k, json.dumps(h[k])))
        L.append('      "chains": [')
        for ci, c in enumerate(h["chains"]):
            meta = ", ".join('"%s": %s' % (k, json.dumps(c[k])) for k in ("closed", "corners", "length_m", "plan_area_m2"))
            L.append('        {%s, "points": %s}%s' % (meta, pts(c["points"]), "," if ci + 1 < len(h["chains"]) else ""))
        L.append("      ]")
        L.append("    }%s" % ("," if hi + 1 < len(holes) else ""))
    L.append("  ],")
    L.append('  "meets": [')
    for mi, m in enumerate(meets):
        segs = "[" + ", ".join(pts(s) for s in m["segments"]) + "]"
        L.append('    {"name": %s, "edges": %d, "length_m": %s, "max_distance_m": %s, "segments": %s}%s' % (
            json.dumps(m["name"]), m["edges"], json.dumps(m["length_m"]), json.dumps(m["max_distance_m"]),
            segs, "," if mi + 1 < len(meets) else ""))
    L.append("  ]")
    L.append("}")
    tmp = path + ".part"
    with open(tmp, "w") as f:
        f.write("\n".join(L) + "\n")
    os.replace(tmp, path)


def read_holes(path):
    """holes.json's chains as float32 edges per body, and its meets."""
    j = json.load(open(path))
    out = {}
    for h in j["holes"]:
        edges = []
        for c in h["chains"]:
            P = np.array(c["points"], F64).astype(F32)
            ring = np.concatenate([P, P[:1]]) if c["closed"] else P
            edges.append(np.stack([ring[:-1], ring[1:]], 1))
        out[h["name"]] = np.concatenate(edges) if edges else np.zeros((0, 2, 3), F32)
    return out, j


# --- the game's ray, for reading the Stage 0 record ------------------------

def physics_ray_y(F, ids, px, pz, top=2500.0, bottom=-1000.0):
    """The height at which a ray straight down from `top` to `bottom` meets
    face `ids[k]` over (px[k], pz[k]), as the game's physics computes it: Jolt's
    `RayTriangle` in float32 (Moeller-Trumbore, its dot products summed in
    pairs as NEON does) and Godot's `from + (to - from) * fraction`, float32.
    `tools/_height_grid_probe.gd` recorded its heights this way, to about
    0.25 mm and, on some faces, a few mm off the face's true height."""
    f32 = F32
    V = F[ids].astype(f32)
    n = len(ids)
    O = np.stack([px.astype(f32), np.full(n, top, f32), pz.astype(f32)], 1)
    D = np.tile(np.array([0.0, bottom - top, 0.0], f32), (n, 1))

    def cross(a, b):
        return np.stack([a[:, 1] * b[:, 2] - a[:, 2] * b[:, 1],
                         a[:, 2] * b[:, 0] - a[:, 0] * b[:, 2],
                         a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]], 1)

    def dot(a, b):
        m = a * b
        return (m[:, 0] + m[:, 1]) + (m[:, 2] + f32(0))

    e1 = V[:, 1] - V[:, 0]
    e2 = V[:, 2] - V[:, 0]
    det = dot(e1, cross(D, e2))
    q = cross(O - V[:, 0], e1)
    with np.errstate(all="ignore"):
        t = dot(e2, q) / det
    return (f32(top) + D[:, 1] * t).astype(f32)


def _cells_of_faces(F):
    X = F[:, :, 0].astype(F64)
    Z = F[:, :, 2].astype(F64)
    return (np.floor(X.min(1) / CELL), np.floor(X.max(1) / CELL),
            np.floor(Z.min(1) / CELL), np.floor(Z.max(1) / CELL))


# --- proofs -----------------------------------------------------------------

def _read_probe(probe):
    h = json.load(open(os.path.join(probe, "header.json")))
    s = h["sets"]["nodes"]
    nx, nz = s["nx"], s["nz"]

    def rd(name, t):
        return np.frombuffer(gzip.open(os.path.join(probe, s["files"][name]["name"])).read(), t).reshape(nz, nx)
    return h, s, rd("class", "u1"), rd("terrain_y", "<f4")


def proof_heights(grid, M, res, probe):
    """1. Where the Stage 0 probe's first hit is the master's, the bake's height
    equals the probe's within 1 mm; and why not where it does not."""
    h, s, cls, ter = _read_probe(probe)
    nx, nz = s["nx"], s["nz"]
    oi = int(round((s["origin"][0] - grid.x0) / grid.step))
    oj = int(round((s["origin"][1] - grid.z0) / grid.step))
    H = res["height"][oj:oj + nz, oi:oi + nx]
    T = res["face"][oj:oj + nz, oi:oi + nx]
    c1 = cls == 1
    d = H.astype(F32).astype(F64) - ter.astype(F64)
    with np.errstate(invalid="ignore"):
        agree = c1 & (np.abs(d) <= 0.001)
    bad = c1 & ~agree
    j, i = np.nonzero(bad)
    px = (s["origin"][0] + s["step"] * i).astype(F32)
    pz = (s["origin"][1] + s["step"] * j).astype(F32)
    has = ~np.isnan(H[j, i])
    yj = np.full(len(j), np.nan, F32)
    yj[has] = physics_ray_y(M, T[j, i][has], px[has], pz[has])
    # A down-facing top is not a face the game's one-sided collision meets.
    up_top = np.ones(len(j), bool)
    if res.get("front_up") is not None:
        up_top[has] = res["front_up"][T[j, i][has]]
    phys = has & up_top & (np.abs(yj.astype(F64) - ter[j, i]) <= 0.001)
    # The rest, one by one, against every face indexed in the node's cell.
    keep, _, _ = standing(M)
    front_up = res.get("front_up")
    cx0, cx1, cz0, cz1 = _cells_of_faces(M)
    fname = np.empty(len(M), object)
    nudged = {(float(a[0]), float(a[1])) for a in h["tallies"]["nodes"]["cast_again_off_a_face_in_the_ray"]}
    rows = []
    for k in np.nonzero(~phys)[0]:
        x, z = float(px[k]), float(pz[k])
        probe_y = float(ter[j[k], i[k]])
        top_y = float(H[j[k], i[k]])
        t_top = int(T[j[k], i[k]])
        cx, cz = np.floor(x / CELL), np.floor(z / CELL)
        cand = np.nonzero((cx0 <= cx) & (cx <= cx1) & (cz0 <= cz) & (cz <= cz1))[0]
        V = M[cand].astype(F64)
        e0 = V[:, 1] - V[:, 0]
        e1 = V[:, 2] - V[:, 0]
        ex, ez = x - V[:, 0, 0], z - V[:, 0, 2]
        den = e0[:, 0] * e1[:, 2] - e1[:, 0] * e0[:, 2]
        with np.errstate(all="ignore"):
            u = (ex * e1[:, 2] - e1[:, 0] * ez) / den
            v = (e0[:, 0] * ez - ex * e0[:, 2]) / den
            exact = V[:, 0, 1] + u * e0[:, 1] + v * e1[:, 1]
        yc = physics_ray_y(M, cand, np.full(len(cand), x, F32), np.full(len(cand), z, F32)).astype(F64)
        miss = np.where(np.isfinite(yc), np.abs(yc - probe_y), np.inf)
        b = int(np.argmin(miss)) if len(cand) else -1
        hit = int(cand[b]) if b >= 0 else -1
        inside = (u >= -INSIDE_EPS) & (v >= -INSIDE_EPS) & (u + v <= 1.0 + INSIDE_EPS)
        at_top = cand == t_top
        down_top = t_top >= 0 and front_up is not None and not front_up[t_top]
        if (x, z) in nudged:
            why = "cast again 1 cm east: the ray lay in a vertical face"
        elif down_top and probe_y < top_y - 0.001:
            why = "down-facing top: _top takes it, the game's one-sided collision does not"
        elif b < 0 or miss[b] > 0.01:
            why = "the probe's height is on no face here"
        elif not keep[hit]:
            why = "a steep face, which _top skips (|n.y| < 0.05|n|), is the first hit" + (
                "; no standing face here" if np.isnan(top_y) else "")
        elif not inside[b]:
            why = "float32 ray caught a face the node lies just outside (an edge)"
        elif abs(exact[b] - top_y) <= 0.001:
            why = "float32 ray on another face meeting at the node (shared edge or corner)"
        elif exact[b] > top_y + 0.001:
            why = "a standing face above the top that the rasteriser did not take"
        elif yc[b] < top_y - 0.001:
            edge = float(min(u[at_top][0], v[at_top][0], 1 - u[at_top][0] - v[at_top][0])) if at_top.any() else np.nan
            why = ("pinhole: the ray slipped through the top face at its edge" if edge < 1e-3
                   else "the ray passed through the top face")
        else:
            why = "float32 ray error lifted a lower face's hit above the top"
        rows.append({"x": x, "z": z, "probe_y": round(probe_y, 4),
                     "bake_y": None if np.isnan(top_y) else round(top_y, 4), "why": why,
                     "top_mesh": _mesh_of(t_top), "hit_mesh": _mesh_of(hit)})
    ad = np.abs(d[c1])
    ad = ad[~np.isnan(ad)]
    reasons = {}
    for r in rows:
        reasons[r["why"]] = reasons.get(r["why"], 0) + 1
    return {
        "probe": probe, "probe_commit": h["commit"], "nodes": int(nx * nz), "class_1": int(c1.sum()),
        "within_1mm": int(agree.sum()), "over_1mm": int(bad.sum()),
        "share_within_1mm": round(float(agree.sum()) / float(c1.sum()), 6),
        "abs_error_m": {"max_of_agreeing": float(np.abs(d[agree]).max()),
                        "p99_of_agreeing": float(np.percentile(np.abs(d[agree]), 99)),
                        "over": {str(t): int(np.count_nonzero(ad > t)) for t in (0.001, 0.002, 0.005, 0.01, 0.05, 0.25, 1.0, 10.0)}},
        "bake_none_where_probe_hit": int(np.count_nonzero(c1 & np.isnan(H))),
        "bake_ground_where_probe_none": _pinholes(grid, M, res, s, cls, H, T),
        "explained_by_the_physics_float32_ray_on_the_top_face": int(phys.sum()),
        "the_rest": {"count": len(rows), "why": reasons},
        "the_rest_rows": rows,
    }


def _pinholes(grid, M, res, s, cls, H, T):
    """Nodes where the probe's ray met nothing at all but the bake has the
    master's ground: how near each lies to its top face's edge."""
    j, i = np.nonzero((cls == 0) & ~np.isnan(H))
    rows = []
    for jj, ii in zip(j, i):
        x = s["origin"][0] + s["step"] * ii
        z = s["origin"][1] + s["step"] * jj
        V = M[T[jj, ii]].astype(F64)
        e0 = V[1] - V[0]
        e1 = V[2] - V[0]
        den = e0[0] * e1[2] - e1[0] * e0[2]
        u = ((x - V[0, 0]) * e1[2] - e1[0] * (z - V[0, 2])) / den
        v = (e0[0] * (z - V[0, 2]) - (x - V[0, 0]) * e0[2]) / den
        rows.append({"x": float(x), "z": float(z), "bake_y": round(float(H[jj, ii]), 3),
                     "edge": float(min(u, v, 1 - u - v)), "mesh": _mesh_of(int(T[jj, ii]))})
    return {"count": len(rows), "on_the_top_face_edge_within_1e-3": sum(r["edge"] < 1e-3 for r in rows),
            "rows": rows}


_MESH_NAMES = None


def _mesh_of(t):
    if t < 0 or _MESH_NAMES is None:
        return ""
    return _MESH_NAMES[t]


def _set_mesh_names(index):
    global _MESH_NAMES
    n = sum(r["count"] for r in index["master"])
    _MESH_NAMES = np.empty(n, object)
    for r in index["master"]:
        _MESH_NAMES[r["first"]:r["first"] + r["count"]] = r["name"]


def points_for(grid, M, B, n_random=100_000, near=4.0, seed=20261012):
    """Where `delta_y` is asked: every node within `near` metres (plan) of a
    changed face, then `n_random` uniform points over the grid's domain."""
    added, removed = changed_faces(M, B)
    C = np.concatenate([M[added], B[removed]]).astype(F64)
    X, Z = C[:, :, 0], C[:, :, 2]
    i0 = np.ceil((X.min(1) - near - grid.x0) / grid.step).astype(np.int64)
    i1 = np.floor((X.max(1) + near - grid.x0) / grid.step).astype(np.int64)
    j0 = np.ceil((Z.min(1) - near - grid.z0) / grid.step).astype(np.int64)
    j1 = np.floor((Z.max(1) + near - grid.z0) / grid.step).astype(np.int64)
    i0, i1 = np.clip(i0, 0, grid.nx), np.clip(i1, -1, grid.nx - 1)
    j0, j1 = np.clip(j0, 0, grid.nz), np.clip(j1, -1, grid.nz - 1)
    ni = np.maximum(i1 - i0 + 1, 0)
    nj = np.maximum(j1 - j0 + 1, 0)
    cnt = ni * nj
    mask = np.zeros((grid.nz, grid.nx), bool)
    for a, b in _chunks(cnt, 4_000_000):
        rep, loc = _expand(cnt[a:b])
        t = np.arange(a, b)[rep]
        ii = i0[t] + loc % ni[t]
        jj = j0[t] + loc // ni[t]
        px = grid.x0 + grid.step * ii
        pz = grid.z0 + grid.step * jj
        T = C[t]
        best = np.full(len(t), np.inf)
        for p, q in ((0, 1), (1, 2), (2, 0)):
            ax, az = T[:, p, 0], T[:, p, 2]
            dx, dz = T[:, q, 0] - ax, T[:, q, 2] - az
            tt = np.clip(((px - ax) * dx + (pz - az) * dz) / np.maximum(dx * dx + dz * dz, 1e-18), 0, 1)
            best = np.minimum(best, np.hypot(px - ax - tt * dx, pz - az - tt * dz))
        e0x, e0z = T[:, 1, 0] - T[:, 0, 0], T[:, 1, 2] - T[:, 0, 2]
        e1x, e1z = T[:, 2, 0] - T[:, 0, 0], T[:, 2, 2] - T[:, 0, 2]
        den = e0x * e1z - e1x * e0z
        with np.errstate(all="ignore"):
            u = ((px - T[:, 0, 0]) * e1z - e1x * (pz - T[:, 0, 2])) / den
            v = (e0x * (pz - T[:, 0, 2]) - (px - T[:, 0, 0]) * e0z) / den
            inside = (u >= 0) & (v >= 0) & (u + v <= 1)
        ok = (best <= near) | inside
        mask[jj[ok], ii[ok]] = True
    j, i = np.nonzero(mask)
    nodes = np.stack([grid.x0 + grid.step * i, grid.z0 + grid.step * j], 1).astype(F32)
    rng = np.random.default_rng(seed)
    rand = np.stack([rng.uniform(grid.x0, grid.x0 + grid.step * (grid.nx - 1), n_random),
                     rng.uniform(grid.z0, grid.z0 + grid.step * (grid.nz - 1), n_random)], 1).astype(F32)
    return nodes, rand


def _d_or_zero(h, b):
    """`delta_y`'s rule: no ground either side reads 0."""
    with np.errstate(invalid="ignore"):
        return np.where(np.isnan(h) | np.isnan(b), 0.0, h.astype(F64) - b.astype(F64))


def proof_change(grid, M, B, HM, HB, points, delta, n_nodes):
    """2. Unchanged ground reads exactly 0; and the grid against the
    generator's own `delta_y` at nodes near change and at random points."""
    added, removed = changed_faces(M, B)
    dirty = dirty_cells(grid, M[added], B[removed])
    nd = node_cells(grid, dirty)
    H32, B32 = HM.astype(F32), HB.astype(F32)
    same = H32.view("<u4") == B32.view("<u4")
    clean = ~nd
    with np.errstate(invalid="ignore"):
        diff = H32.astype(F64) - B32.astype(F64)
    out = {"faces_added": int(len(added)), "faces_removed": int(len(removed)),
           "dirty_cells_8m": int(dirty.sum()), "nodes": int(H32.size),
           "nodes_in_dirty_cells": int(nd.sum()), "nodes_in_clean_cells": int(clean.sum()),
           "clean_nodes_not_bit_identical": int(np.count_nonzero(clean & ~same)),
           "clean_nodes_with_ground_and_difference_not_0": int(np.count_nonzero(clean & ~np.isnan(diff) & (diff != 0))),
           "clean_nodes_no_ground_either": int(np.count_nonzero(clean & np.isnan(H32) & np.isnan(B32))),
           "dirty_nodes_bit_identical": int(np.count_nonzero(nd & same))}
    # At the nodes near change: the rasteriser's float64 against delta_y, bit
    # for bit, and the float32 tiles within their rounding.
    P = points[:n_nodes]
    dy = delta[:n_nodes]
    i = np.round((P[:, 0].astype(F64) - grid.x0) / grid.step).astype(np.int64)
    j = np.round((P[:, 1].astype(F64) - grid.z0) / grid.step).astype(np.int64)
    d64 = _d_or_zero(HM[j, i], HB[j, i])
    d32 = _d_or_zero(H32[j, i], B32[j, i])
    e32 = np.abs(d32 - dy)
    dn = nd[j, i]
    out["nodes_near_change"] = {
        "points": int(n_nodes), "in_dirty_cells": int(dn.sum()),
        "float64_rasteriser_bit_equal_to_delta_y_in_dirty_cells": int(np.count_nonzero(dn & (d64 == dy))),
        "float64_rasteriser_max_error_m_in_dirty_cells": float(np.abs(d64 - dy)[dn].max()) if dn.any() else 0.0,
        "in_clean_cells_delta_y_0": int(np.count_nonzero(~dn & (dy == 0))),
        "in_clean_cells_float32_tiles_identical": int(np.count_nonzero(~dn & (H32[j, i].view("<u4") == B32[j, i].view("<u4")))),
        "in_clean_cells_float64_not_identical": int(np.count_nonzero(~dn & (d64 != 0))),
        "float64_rasteriser_max_error_m": float(np.abs(d64 - dy).max()),
        "float32_tiles_equal": int(np.count_nonzero(e32 == 0)),
        "float32_tiles_max_error_m": float(e32.max()), "float32_tiles_p99_error_m": float(np.percentile(e32, 99)),
        "delta_y_nonzero": int(np.count_nonzero(dy))}
    # At random points: bilinear between the four nodes against the exact.
    R = points[n_nodes:].astype(F64)
    dr = delta[n_nodes:]
    fx = (R[:, 0] - grid.x0) / grid.step
    fz = (R[:, 1] - grid.z0) / grid.step
    i0 = np.minimum(np.floor(fx).astype(np.int64), grid.nx - 2)
    j0 = np.minimum(np.floor(fz).astype(np.int64), grid.nz - 2)
    tx, tz = fx - i0, fz - j0
    D = _d_or_zero(H32, B32)
    bil = (D[j0, i0] * (1 - tx) * (1 - tz) + D[j0, i0 + 1] * tx * (1 - tz)
           + D[j0 + 1, i0] * (1 - tx) * tz + D[j0 + 1, i0 + 1] * tx * tz)
    corner_dirty = nd[j0, i0] | nd[j0, i0 + 1] | nd[j0 + 1, i0] | nd[j0 + 1, i0 + 1]
    e = np.abs(bil - dr)
    ec = e[corner_dirty]
    out["random_points"] = {
        "points": int(len(R)),
        "all_four_nodes_clean": int(np.count_nonzero(~corner_dirty)),
        "clean_not_exactly_0": int(np.count_nonzero(~corner_dirty & ((bil != 0) | (dr != 0)))),
        "with_a_dirty_node": int(corner_dirty.sum()),
        "of_those_delta_y_nonzero": int(np.count_nonzero(corner_dirty & (dr != 0))),
        "bilinear_error_m": {"max": float(ec.max()) if len(ec) else 0.0,
                             "p50": float(np.percentile(ec, 50)) if len(ec) else 0.0,
                             "p99": float(np.percentile(ec, 99)) if len(ec) else 0.0,
                             "rms": float(np.sqrt(np.mean(ec ** 2))) if len(ec) else 0.0,
                             "over_0.01": int(np.count_nonzero(ec > 0.01)),
                             "over_0.25": int(np.count_nonzero(ec > 0.25)),
                             "over_1": int(np.count_nonzero(ec > 1.0))}}
    return out


def proof_holes(grid, index, faces, HM, holes_path):
    """3. The chains in holes.json are the dumped open edges exactly; and what
    of the master's height stands inside each held surface's plan."""
    chains, j = read_holes(holes_path)
    E = faces["held_open"]
    out = {"bodies": {}}
    for rec in index["held_open"]:
        if rec["count"] == 0:
            continue
        mine = E[rec["first"]:rec["first"] + rec["count"]]
        out["bodies"][rec["name"]] = {"open_edges": rec["count"],
                                      "chains_are_the_open_edges_bit_for_bit": same_edges(chains[rec["name"]], mine)}
    out["every_body_with_open_edges_in_holes_json"] = set(chains) == set(out["bodies"])
    # Each held collider's standing faces over the nodes: its top there, and
    # the master's height at the same node.
    Hf = faces["held"]
    fid = np.zeros(len(Hf), np.int64)
    names = []
    for k, r in enumerate(index["held"]):
        fid[r["first"]:r["first"] + r["count"]] = k
        names.append(r["name"])
    keep = standing(Hf)[0]
    nodes, bodies, hs = [], [], []
    for node, face, h in raster(Hf, np.nonzero(keep)[0], grid):
        nodes.append(node)
        bodies.append(fid[face])
        hs.append(h)
    node = np.concatenate(nodes)
    body = np.concatenate(bodies)
    h = np.concatenate(hs)
    key = body * (grid.nx * grid.nz) + node
    o = np.lexsort((h, key))
    key, h, node, body = key[o], h[o], node[o], body[o]
    last = np.r_[key[1:] != key[:-1], True]
    node, body, h = node[last], body[last], h[last]
    mh = HM.ravel()[node]
    has = ~np.isnan(mh)
    above = has & (mh > h + 0.001)
    # Distance in plan from such a node to its body's open edges, if it has any.
    per = {}
    for k in np.unique(body):
        name = names[k]
        sel = body == k
        rec = {"nodes_covered": int(sel.sum()), "with_master_height": int((sel & has).sum()),
               "master_above_by_over_1mm": int((sel & above).sum()),
               "master_below_by_over_1mm": int((sel & has & (mh < h - 0.001)).sum())}
        if rec["master_above_by_over_1mm"]:
            rec["master_above_max_m"] = round(float((mh - h)[sel & above].max()), 3)
        if rec["with_master_height"] and name in chains and len(chains[name]):
            idx = np.nonzero(sel & has)[0]
            px = grid.x0 + grid.step * (node[idx] % grid.nx)
            pz = grid.z0 + grid.step * (node[idx] // grid.nx)
            P = np.stack([px, np.zeros(len(idx)), pz], 1)
            A = chains[name][:, 0].astype(F64).copy()
            B = chains[name][:, 1].astype(F64).copy()
            A[:, 1] = 0
            B[:, 1] = 0
            dist, _ = nearest_segments(P, A, B)
            rec["of_those_on_the_outline_within_1cm"] = int(np.count_nonzero(dist <= 0.01))
            rec["of_those_inside"] = int(np.count_nonzero(dist > 0.01))
            ins = idx[dist > 0.01]
            if len(ins):
                rec["inside_master_minus_held_m"] = {
                    "min": round(float((mh[ins] - h[ins]).min()), 3), "max": round(float((mh[ins] - h[ins]).max()), 3)}
                rec["inside_examples"] = [[float(grid.x0 + grid.step * (node[q] % grid.nx)),
                                           float(grid.z0 + grid.step * (node[q] // grid.nx)),
                                           round(float(mh[q]), 3), round(float(h[q]), 3)] for q in ins[:5]]
        if rec["with_master_height"] or name in chains:
            per[name] = rec
    out["held_surfaces"] = per
    tot = lambda k: sum(r.get(k, 0) for r in per.values())
    out["totals"] = {"held_colliders_over_nodes": int(len(np.unique(body))),
                     "nodes_covered": int(len(node)),
                     "with_master_height": tot("with_master_height"),
                     "master_above_by_over_1mm": tot("master_above_by_over_1mm"),
                     "master_below_by_over_1mm": tot("master_below_by_over_1mm")}
    out["holes_json_stats"] = j["stats"]
    return out


def _raw_f32(path, n):
    a = np.fromfile(path, "<f4")
    return a.reshape(n, n)


def proof_round_trips(grid, HM, HB, out_dir, godot=None, blender=None):
    """4. Every tile read back bit for bit: here, in Blender, in Godot; shared
    edges identical; and the writer deterministic."""
    import tempfile
    res = {}
    for folder, mosaic in (("height", HM), ("baseline", HB)):
        ref = mosaic.astype(F32)
        path = os.path.join(out_dir, folder)
        back, edge_bad = read_tiles(path, grid)
        r = {"tiles": len(list(grid.tiles())),
             "python_read_bit_exact": bool(np.array_equal(back.view("<u4"), ref.view("<u4"))),
             "shared_edges_differing": int(edge_bad)}
        # Written again, the same bytes.
        same = 0
        with tempfile.TemporaryDirectory() as tmp:
            for tx, tz in grid.tiles():
                rows, cols = grid.window(tx, tz)
                p = os.path.join(tmp, "t.exr")
                write_exr(p, ref[rows, cols])
                same += open(p, "rb").read() == open(os.path.join(path, grid.name(tx, tz)), "rb").read()
        r["rewritten_byte_identical"] = int(same)
        for app, base in (("godot", godot), ("blender", blender)):
            if not base:
                continue
            ok = 0
            extra = 0
            for tx, tz in grid.tiles():
                rows, cols = grid.window(tx, tz)
                want = ref[rows, cols].view("<u4")
                stem = os.path.join(base, folder, grid.name(tx, tz)[:-4])
                if app == "godot":
                    meta = json.load(open(stem + ".json"))
                    a = np.fromfile(stem + ".bin", "<f4")
                    ch = {"RF": 1, "RGF": 2, "RGBF": 3, "RGBAF": 4}[meta["format_name"]]
                    a = a.reshape(meta["height"], meta["width"], ch)
                    ok += bool(np.array_equal(a[..., 0].view("<u4"), want))
                    extra += all(np.array_equal(a[..., c].view("<u4"), want) for c in range(1, min(ch, 3)))
                    r["godot_format"] = meta["format_name"]
                else:
                    a = _raw_f32(stem + ".f32", grid.n)
                    ok += bool(np.array_equal(a.view("<u4"), want))
            r[app + "_read_bit_exact"] = int(ok)
            if app == "godot":
                r["godot_g_and_b_equal_r"] = int(extra)
        res[folder] = r
    return res


def _du(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    return sum(os.path.getsize(os.path.join(path, f)) for f in os.listdir(path))


# --- frames -----------------------------------------------------------------

def frames(grid, out_dir, folder, step_px=4):
    """A north-up hillshade of height/ at 8 m a pixel with a 1 km grid, and
    height - baseline over it. PIL draws the labels."""
    from PIL import Image, ImageDraw
    H, _ = read_tiles(os.path.join(folder, "height"), grid)
    B, _ = read_tiles(os.path.join(folder, "baseline"), grid)
    h = H[::step_px, ::step_px].astype(F64)
    px = grid.step * step_px
    filled = np.where(np.isnan(h), -7.5, h)
    gz, gx = np.gradient(filled, px)
    # Sun from the north-west, 45 degrees up; north is -z, image row 0.
    az, alt = np.radians(315.0), np.radians(45.0)
    sx, sz, sy = np.sin(az) * np.cos(alt), -np.cos(az) * np.cos(alt), np.sin(alt)
    shade = np.clip((-gx * sx - gz * sz + sy) / np.sqrt(gx * gx + gz * gz + 1), 0, 1)
    # Low land green, high land brown, white at the top; below the sea blue.
    t = np.clip(filled / 450.0, 0, 1)[..., None]
    land = (1 - t) * np.array([118, 150, 92]) + t * np.array([214, 200, 172])
    sea = np.array([96, 124, 150]) + np.clip(filled + 7.5, -60, 0)[..., None] * 0.6
    base = np.where((filled < -7.5)[..., None], sea, land)
    rgb = base * (0.35 + 0.65 * shade[..., None])
    rgb[np.isnan(h)] = (30, 36, 48)
    hill = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    # height - baseline: the largest change in each pixel's 4 x 4 nodes.
    with np.errstate(invalid="ignore"):
        d = H.astype(F64) - B.astype(F64)
    came = np.isnan(H) != np.isnan(B)
    nz_, nx_ = (grid.nz + step_px - 1) // step_px, (grid.nx + step_px - 1) // step_px
    pad = lambda a, v: np.pad(a, ((0, nz_ * step_px - a.shape[0]), (0, nx_ * step_px - a.shape[1])), constant_values=v)
    dd = pad(np.nan_to_num(d, nan=0.0), 0.0).reshape(nz_, step_px, nx_, step_px)
    big = np.take_along_axis(dd.transpose(0, 2, 1, 3).reshape(nz_, nx_, -1),
                             np.abs(dd.transpose(0, 2, 1, 3).reshape(nz_, nx_, -1)).argmax(-1)[..., None], -1)[..., 0]
    flip = pad(came, False).reshape(nz_, step_px, nx_, step_px).any(axis=(1, 3))
    grey = (np.asarray(hill, F64).mean(-1, keepdims=True) * 0.55 + 20).repeat(3, -1)[:nz_, :nx_]
    lit = np.clip((np.log10(np.maximum(np.abs(big), 1e-9)) + 2.0) / 3.0, 0, 1)[..., None]  # 1 cm .. 10 m
    up = np.array([255, 70, 40]) * (0.45 + 0.55 * lit)
    down = np.array([50, 120, 255]) * (0.45 + 0.55 * lit)
    rgb2 = np.where((big > 0)[..., None], up, np.where((big < 0)[..., None], down, grey))
    rgb2[flip] = (255, 0, 255)
    diff = Image.fromarray(np.clip(rgb2, 0, 255).astype(np.uint8))
    out = []
    for img, name, title in (
            (hill, "height_hillshade.png", "height/: hillshade, 8 m a pixel, north up; 1 km grid, x east, z south"),
            (diff, "height_minus_baseline.png",
             "height - baseline: red up, blue down (1 cm dim .. 10 m bright); magenta: ground came or went")):
        W, Ht = img.size
        m = 34
        canvas = Image.new("RGB", (W + 2 * m, Ht + 2 * m + 18), (16, 16, 20))
        canvas.paste(img, (m, m + 18))
        dr = ImageDraw.Draw(canvas)
        dr.text((m, 6), title, fill=(230, 230, 230))
        for k in range(int(grid.x0), int(grid.x0 + grid.step * (grid.nx - 1)) + 1, 1000):
            x = m + int(round((k - grid.x0) / px))
            dr.line([(x, m + 18), (x, m + 18 + Ht - 1)], fill=(255, 255, 255), width=1)
            dr.text((x - 10, m + 20 + Ht), "%d" % k, fill=(220, 220, 220))
        for k in range(int(grid.z0), int(grid.z0 + grid.step * (grid.nz - 1)) + 1, 1000):
            y = m + 18 + int(round((k - grid.z0) / px))
            dr.line([(m, y), (m + W - 1, y)], fill=(255, 255, 255), width=1)
            dr.text((2, y - 5), "%d" % k, fill=(220, 220, 220))
        p = os.path.join(out_dir, name)
        canvas.save(p)
        out.append(p)
    return out


# --- commands ---------------------------------------------------------------

def cmd_bake(args):
    t0 = time.time()
    grid = Grid()
    index, faces = load_dump(args.faces)
    times = {}
    for name, folder in (("master", "height"), ("baseline", "baseline")):
        t = time.time()
        H = top(faces[name], grid)["height"]
        write_tiles(H, grid, os.path.join(args.out, folder))
        times[folder] = round(time.time() - t, 1)
        print("%s: %d of %d nodes hold ground; %.1fs" % (folder, int(np.count_nonzero(~np.isnan(H))), H.size, times[folder]))
    t = time.time()
    holes, meets, stats = build_holes(index, faces)
    write_holes(os.path.join(args.out, "holes.json"), holes, meets, stats, index["header"])
    times["holes"] = round(time.time() - t, 1)
    print("holes: %d bodies, %d chains (%d closed); master's open edges on %d held solids; %.1fs" % (
        len(holes), sum(len(h["chains"]) for h in holes),
        sum(c["closed"] for h in holes for c in h["chains"]), len(meets), times["holes"]))
    print("bake: %.1fs in all %s" % (time.time() - t0, json.dumps(times)))


def cmd_points(args):
    grid = Grid()
    _, faces = load_dump(args.faces)
    nodes, rand = points_for(grid, faces["master"], faces["baseline"])
    np.concatenate([nodes, rand]).astype("<f4").tofile(args.out)
    json.dump({"nodes_near_change": int(len(nodes)), "random": int(len(rand))}, open(args.out + ".json", "w"))
    print("points: %d nodes within 4 m of a changed face, %d random; %s" % (len(nodes), len(rand), args.out))


def cmd_prove(args):
    t0 = time.time()
    grid = Grid()
    index, faces = load_dump(args.faces)
    _set_mesh_names(index)
    M, B = faces["master"], faces["baseline"]
    rm = top(M, grid, extra=True)
    rb = top(B, grid)
    HM, HB = rm["height"], rb["height"]
    report = {"grid": os.path.join(args.out, "grid.json"), "dump": index["header"]}
    report["1_heights_against_the_game"] = proof_heights(grid, M, rm, args.probe)
    print("1. heights:", json.dumps({k: v for k, v in report["1_heights_against_the_game"].items() if k != "the_rest_rows"}))
    if args.delta:
        pts, dl = args.delta.split(",")
        meta = json.load(open(pts + ".json"))
        points = np.fromfile(pts, "<f4").reshape(-1, 2)
        delta = np.fromfile(dl, "<f8")
        assert len(points) == len(delta)
        report["2_unchanged_reads_0"] = proof_change(grid, M, B, HM, HB, points, delta, meta["nodes_near_change"])
        print("2. change:", json.dumps(report["2_unchanged_reads_0"]))
    report["3_holes"] = proof_holes(grid, index, faces, HM, os.path.join(args.out, "holes.json"))
    print("3. holes:", json.dumps(report["3_holes"]["totals"]), json.dumps(report["3_holes"]["bodies"]))
    report["4_round_trips"] = proof_round_trips(grid, HM, HB, args.out, args.godot, args.blender)
    print("4. round trips:", json.dumps(report["4_round_trips"]))
    report["5_sizes_bytes"] = {k: _du(os.path.join(args.out, k)) for k in ("height", "baseline", "holes.json")}
    print("5. sizes:", json.dumps(report["5_sizes_bytes"]))
    report["seconds"] = round(time.time() - t0, 1)
    if args.report:
        json.dump(report, open(args.report, "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("prove: %.1fs" % report["seconds"])


def cmd_frames(args):
    for p in frames(Grid(), args.out, args.ground):
        print("frame:", p)


def blender_read(src, out):
    """Inside Blender: each EXR loaded as a Blender image, its first channel
    written as raw float32, north row first."""
    import bpy
    os.makedirs(out, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(src)):
        if not f.endswith(".exr"):
            continue
        img = bpy.data.images.load(os.path.join(src, f))
        img.colorspace_settings.name = "Non-Color"
        w, h = img.size
        ch = img.channels
        a = np.empty(w * h * ch, np.float32)
        img.pixels.foreach_get(a)
        a = a.reshape(h, w, ch)[::-1]  # Blender's rows run from the bottom
        np.ascontiguousarray(a[..., 0]).astype("<f4").tofile(os.path.join(out, f[:-4] + ".f32"))
        bpy.data.images.remove(img)
        n += 1
    print("blender-read: %d EXR from %s into %s" % (n, src, out))


def main(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bake", help="write height/, baseline/ and holes.json")
    b.add_argument("--faces", required=True, help="the dump folder")
    b.add_argument("--out", default=GROUND)
    pt = sub.add_parser("points", help="where the proof asks delta_y")
    pt.add_argument("--faces", required=True)
    pt.add_argument("--out", required=True)
    pr = sub.add_parser("prove", help="the Stage 1 proofs")
    pr.add_argument("--faces", required=True)
    pr.add_argument("--out", default=GROUND)
    pr.add_argument("--probe", required=True, help="the Stage 0 height grid record")
    pr.add_argument("--delta", help="<points.f32>,<delta.f64>")
    pr.add_argument("--godot", help="the --read output folder, with height/ and baseline/")
    pr.add_argument("--blender", help="the blender-read output folder, with height/ and baseline/")
    pr.add_argument("--report", help="write the proofs as JSON")
    fr = sub.add_parser("frames", help="the hillshade and the difference map")
    fr.add_argument("--out", required=True)
    fr.add_argument("--ground", default=GROUND)
    br = sub.add_parser("blender-read", help="(inside Blender) read EXR as Blender images")
    br.add_argument("src")
    br.add_argument("dst")
    a = p.parse_args(argv)
    if a.cmd == "blender-read":
        blender_read(a.src, a.dst)
    else:
        {"bake": cmd_bake, "points": cmd_points, "prove": cmd_prove, "frames": cmd_frames}[a.cmd](a)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
