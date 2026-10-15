"""The land's colour on the height grid: its PNG reader and writer, and a map.

    python3 tools/ground_colour_bake.py --map <png> [--colour <dir>]     # the mosaic; needs Pillow

`assets/source/world_ground/colour/x{tx}_z{tz}.png`, one per tile as `grid.json` says: 501 x 501,
8-bit sRGB RGBA, north up, row r at z = 1000 tz + 2 r, column c at x = 1000 tx + 2 c, shared edges
equal, alpha 0 and colour 0 where there is no ground (premultiplied). Christina paints them; what
she paints is what the ground grid's shader (`assets/shaders/ground_grid.gdshader`) draws, with no
tint (her choice, 2026-10-13). `png_read` and `png_write`, by hand with zlib, are what
`tools/ground_grid_edit.py`, `tools/blender/seabed_build.py` and the Blender panel's Ground box use.

Stage 1, Bake, of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-12) baked these
images, inside Blender, from the top upward faces of the world terrain master's `Ground`, as the
game showed them then (vertex colours and landform albedo, the palette's tint baked in on
2026-10-13). Since Stage 5 (2026-10-15) the pieces are retired and the images are the colour; the
bake and its proofs are in git up to `a8cd64b`.

`--map` runs under plain Python with Pillow: a north-up mosaic of the colour tiles at 8 m a pixel
with a 1 km grid and the main places named.
"""

import json
import os
import struct
import sys
import zlib

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
GRID = os.path.join(ROOT, "assets", "source", "world_ground", "grid.json")

# Named places for the map, Godot (x, z): the measurement's gazetteer
# (screenshots/terrain-heightfield-measure-2026-10-12/report.json).
PLACES = [
    ("park plaza", 0, 0), ("beach town", -61, 412), ("north town", -302, -1882),
    ("city peninsula", -595, 2547), ("bridge", -55, 2450), ("city foothills", -576, 4030),
    ("the falls", 400, -290), ("lake K1", 570, -486), ("lake L0", 749, 225),
    ("hillside D1", 168, 570), ("north cove", -140, -400), ("south beach front", 110, 959),
    ("bluff shelf", 503, 1803), ("volcanic plug", -642, -2365), ("south range blend", -562, 5784),
    ("range north", -394, -1053), ("range middle", 1103, -398), ("range south", -649, 6458),
    ("connection lowland", 1081, 3184),
]


# ---------------------------------------------------------------- the grid

def grid_spec(path=GRID):
    with open(path) as f:
        g = json.load(f)
    sp, tile, n = float(g["spacing_m"]), float(g["tile_m"]), int(g["tile_samples"])
    assert abs((n - 1) * sp - tile) < 1e-9, "grid.json: tile_samples does not span tile_m"
    tx0, tx1 = g["tiles_x"]
    tz0, tz1 = g["tiles_z"]
    per = n - 1
    return {
        "spacing": sp, "tile": tile, "n": n, "per": per,
        "tiles_x": list(range(tx0, tx1 + 1)), "tiles_z": list(range(tz0, tz1 + 1)),
        "x0": tx0 * tile, "z0": tz0 * tile,
        "nx": (tx1 - tx0 + 1) * per + 1, "nz": (tz1 - tz0 + 1) * per + 1,
        "frozen_commit": g.get("frozen_commit"),
    }


def tile_slice(spec, tx, tz):
    """The tile's rows and columns in the whole lattice."""
    c0 = (tx - spec["tiles_x"][0]) * spec["per"]
    r0 = (tz - spec["tiles_z"][0]) * spec["per"]
    return slice(r0, r0 + spec["n"]), slice(c0, c0 + spec["n"])


# ---------------------------------------------------------------- PNG, by hand
# Blender's Python has no Pillow, and an image saved through bpy passes through
# its colour management; these write and read exactly the bytes given.

def png_write(path, rgba):
    h, w, _ = rgba.shape
    raw = rgba.astype(np.uint8)
    up = raw.astype(np.int16)
    up[1:] -= raw[:-1]
    rows = np.empty((h, 1 + w * 4), np.uint8)
    rows[:, 0] = 2  # filter Up
    rows[0, 0] = 0
    rows[0, 1:] = raw[0].reshape(-1)
    rows[1:, 1:] = (up[1:] % 256).astype(np.uint8).reshape(h - 1, -1)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    body = b"\x89PNG\r\n\x1a\n"
    body += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    body += chunk(b"sRGB", b"\x00")
    body += chunk(b"IDAT", zlib.compress(rows.tobytes(), 9))
    body += chunk(b"IEND", b"")
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(body)
    os.replace(tmp, path)


def png_read(path):
    """8-bit RGBA PNGs with filters None, Sub or Up (what png_write and most painters write
    for flat colour; others raise)."""
    with open(path, "rb") as f:
        b = f.read()
    assert b[:8] == b"\x89PNG\r\n\x1a\n", path
    pos, idat, w, h = 8, b"", None, None
    while pos < len(b):
        n = struct.unpack(">I", b[pos:pos + 4])[0]
        kind = b[pos + 4:pos + 8]
        data = b[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", data[:10])
            assert depth == 8 and ctype == 6, f"{path}: not 8-bit RGBA"
        elif kind == b"IDAT":
            idat += data
        pos += 12 + n
    raw = np.frombuffer(zlib.decompress(idat), np.uint8).reshape(h, 1 + w * 4)
    out = np.zeros((h, w * 4), np.uint8)
    for r in range(h):
        f, line = raw[r, 0], raw[r, 1:].astype(np.int32)
        if f == 0:
            out[r] = line
        elif f == 2:
            out[r] = (line + (out[r - 1] if r else 0)) % 256
        elif f == 1:
            acc = line.reshape(-1, 4)
            out[r] = (np.cumsum(acc, axis=0) % 256).reshape(-1)
        else:
            raise ValueError(f"{path}: PNG filter {f} not read here")
    return out.reshape(h, w, 4)


# ---------------------------------------------------------------- the command line

def opt(rest, name, default=None):
    return rest[rest.index(name) + 1] if name in rest else default


# ---------------------------------------------------------------- the map (plain Python)

def mosaic(out, colour_dir, step=4):
    from PIL import Image, ImageDraw, ImageFont
    spec = grid_spec()
    nz, nx = spec["nz"], spec["nx"]
    full = np.zeros((nz, nx, 4), np.uint8)
    for tz in spec["tiles_z"]:
        for tx in spec["tiles_x"]:
            rs, cs = tile_slice(spec, tx, tz)
            path = os.path.join(colour_dir, f"x{tx}_z{tz}.png")
            if os.path.exists(path):  # a missing tile is no ground (grid.json, since Stage 4)
                full[rs, cs] = png_read(path)
    # 8 m a pixel: the alpha-weighted mean of each 4 x 4 block of nodes.
    h, w = (nz - 1) // step, (nx - 1) // step
    blk = full[:h * step, :w * step].reshape(h, step, w, step, 4).astype(np.float64)
    a = blk[..., 3:4] / 255.0
    asum = a.sum((1, 3))
    rgb = (blk[..., :3] * a).sum((1, 3)) / np.maximum(asum, 1e-9)
    cover = asum[..., 0] / (step * step)
    sea = np.array([196, 214, 226], np.float64)
    pix = rgb * cover[..., None] + sea * (1 - cover[..., None])
    panel = 380
    img = Image.new("RGB", (w + panel, h), (255, 255, 255))
    img.paste(Image.fromarray(np.clip(pix + 0.5, 0, 255).astype(np.uint8)), (0, 0))
    d = ImageDraw.Draw(img)

    def font(size, bold=False):
        for p in (("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
                  "/System/Library/Fonts/Helvetica.ttc"):
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    px = spec["spacing"] * step
    for gxl in range(int(spec["x0"]), int(spec["x0"] + w * px) + 1, 1000):
        c = (gxl - spec["x0"]) / px
        d.line([(c, 0), (c, h)], fill=(70, 70, 70), width=1)
        d.text((c + 3, 3), f"x {gxl / 1000:g} km", fill=(30, 30, 30), font=font(12))
    for gzl in range(int(spec["z0"]), int(spec["z0"] + h * px) + 1, 1000):
        r = (gzl - spec["z0"]) / px
        d.line([(0, r), (w, r)], fill=(70, 70, 70), width=1)
        d.text((3, r + (18 if r < 1 else 2)), f"z {gzl / 1000:g} km", fill=(30, 30, 30), font=font(12))
    for name, x, z in PLACES:
        c, r = (x - spec["x0"]) / px, (z - spec["z0"]) / px
        d.ellipse([c - 2.5, r - 2.5, c + 2.5, r + 2.5], fill=(0, 0, 0))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                d.text((c + 5 + dx, r - 8 + dy), name, fill=(255, 255, 255), font=font(13, True))
        d.text((c + 5, r - 8), name, fill=(0, 0, 0), font=font(13, True))
    L = 1000 / px
    y0 = h - 30
    d.rectangle([20, y0, 20 + L, y0 + 6], fill=(0, 0, 0))
    d.rectangle([20 + L / 2, y0, 20 + L, y0 + 6], fill=(255, 255, 255), outline=(0, 0, 0))
    d.text((20, y0 + 9), "0", fill=(0, 0, 0), font=font(12))
    d.text((20 + L - 26, y0 + 9), "1 km", fill=(0, 0, 0), font=font(12))
    d.text((20, y0 - 18), f"North up (Godot -z), {px:g} m a pixel", fill=(0, 0, 0), font=font(12))
    d.line([(w, 0), (w, h)], fill=(0, 0, 0), width=2)
    x, y = w + 16, 16
    d.text((x, y), "The land's colour", fill=(0, 0, 0), font=font(22, True))
    y += 34
    for t in ("assets/source/world_ground/colour/, 66 tiles,",
              "the albedo the game shows today: the",
              "vertex colours with the palette's tint,",
              "and each landform material's albedo.",
              "The grid's shader draws it as it is.",
              f"Frozen master {spec['frozen_commit']}; {px:g} m a pixel,",
              "each pixel the mean of 4 x 4 nodes.",
              "Pale blue: no Ground (sea, and the",
              "generator's road corridor and anchors)."):
        d.text((x, y), t, fill=(50, 50, 50), font=font(13))
        y += 18
    img.save(out, optimize=True)
    print("wrote", out, img.size)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--map" not in argv:
        raise SystemExit(__doc__)
    mosaic(opt(argv, "--map"), opt(argv, "--colour", os.path.join(os.path.dirname(GRID), "colour")))
