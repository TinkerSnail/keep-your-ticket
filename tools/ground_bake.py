#!/usr/bin/env python3
"""The height grid's own files: its EXR reader and writer, `Grid` (`grid.json`), the tiles as one
mosaic, and two checks.

Stage 1, Bake, of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-12) baked
`assets/source/world_ground/height/`, `baseline/` and `holes.json` from the faces the generator
measured the ground from, the world terrain master's pieces and their frozen copy, with this
file's `bake` and proved it with `points` and `prove`. Since Stage 5 (2026-10-15) the tiles are
the ground and the pieces are retired; the bake, its rasteriser and its proofs are in git up to
`a8cd64b`. What stays is the library the grid's tools import (`ground_grid_edit.py`,
`ground_follow.py`, `blender/ground_build.py`, `blender/seabed_build.py`, the Blender panel's
Ground box) and:

    python3 tools/ground_bake.py frames --out <dir> [--ground <dir>]
    Blender -b --factory-startup --python tools/ground_bake.py -- blender-read <abs>/assets/source/world_ground/height <blender>/height

`frames` draws a north-up hillshade of `height/` at 8 m a pixel with a 1 km grid, and
height - baseline over it. `blender-read`, run inside Blender, loads each EXR as a Blender image
and writes its first channel as raw float32, to hold Blender's reading against this file's (Godot's
is `tools/_ground_faces_dump.gd --read`).

An EXR here is one float32 channel named Y (OpenEXR's grey), ZIP-compressed,
scanlines from the north edge; written and read by this file alone (numpy and
zlib), and read bit for bit by OpenImageIO, Blender and Godot (Godot loads it
as RGBF with the value in each of r, g and b).
"""

import argparse
import json
import os
import struct
import sys
import zlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND = os.path.join(ROOT, "assets", "source", "world_ground")

# The plan cell the generator once indexed the ground's faces in; the grid's corner and spacing
# still fit it (`Grid`).
CELL = 8.0

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
    """The tiles back as one mosaic; where tiles share an edge, checks it bit for bit. A missing
    tile is no ground (`grid.json`, since Stage 4)."""
    out = np.full((grid.nz, grid.nx), np.nan, "<f4")
    seen = np.zeros((grid.nz, grid.nx), bool)
    bad = 0
    for tx, tz in grid.tiles():
        rows, cols = grid.window(tx, tz)
        path = os.path.join(folder, grid.name(tx, tz))
        if not os.path.exists(path):
            continue
        a = reader(path) if reader else read_exr(path)[0]
        if a.shape != (grid.n, grid.n):
            raise ValueError("%s is %s, not %d square" % (path, a.shape, grid.n))
        prev = out[rows, cols]
        s = seen[rows, cols]
        bad += int(np.count_nonzero(s & (prev.view("<u4") != a.view("<u4"))))
        out[rows, cols] = a
        seen[rows, cols] = True
    return out, bad


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
        cmd_frames(a)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
