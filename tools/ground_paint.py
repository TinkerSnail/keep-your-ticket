"""Paint the ground's height and colour in Photoshop (2026-10-14, height-grid Stage 3,
`documentation/terrain-height-grid-plan-2026-10-12.md`, section 3, "Photoshop").

    python3 tools/ground_paint.py open (--tiles x0_z-1,x1_z-1 | --area X0,Z0,X1,Z1) [--name NAME]
                                       [--window land|seabed|fit|LO,HI] [--show] [--replace] [--root DIR]
    python3 tools/ground_paint.py save <psd> [--dry] [--no-photoshop]
    python3 tools/ground_paint.py prove [--scratch DIR]

**Open** writes one Photoshop document for a region of the grid, `paint/<name>/<name>.psd` under
`assets/source/world_ground/` (git ignores `paint/` through its own `.gitignore`; Godot ignores all
of `assets/source/`). RGB, 16 bits, sRGB, one pixel per 2 m node, north up: row r is z = Z0 + 2 r,
column c is x = X0 + 2 c, as the tiles are. Two groups:
- `colour`, on top: the region's colour from `colour/`, each 8-bit value v held as 257 v.
- `height`: the region's heights as grey, black at the window's foot and white at its top, in
  Photoshop's 32,769 levels (0..32768): a node's level is round((y - low) / step), step = (high -
  low) / 32768. The window is `land`, -20..480 m (1.53 cm a level), by default; `seabed` is
  -640..0 m; `fit` is the region's own lowest and highest ground with a margin; `LO,HI` is given.
  A preset is widened to hold every node of the region; a given window that does not is refused.
  The height layer's name carries the window and the step.
Nodes with no ground are transparent in both, and both base layers have their transparency
locked, so a stroke on them cannot give ground by accident: new ground is painted on a layer of
her own. Beside it: `<name>.json` (region, window, saves, the edits made) and `<name>_synced.npz`
(the grid as the painting last matched it). An existing painting is never replaced (`--replace`
moves it to `<name>/replaced/`). `--show` opens it in Photoshop.

**Save** is what the save hook runs (`tools/photoshop/on_save.jsx` -> `ground_save.jsx`): Photoshop
has just written each group alone, whatever her view of it, as an uncompressed 16-bit TIFF in
`<name>/exports/`; this reads the newest pair and records one grid edit:
- **Height.** A node changes only where its level moved by more than one from the painting's
  last save, and as a change in metres: base y + (level - base level) x step, from the height and
  level it had when the region was opened (a node painted back to within a level of where it was
  gets its old value exactly). Every other node keeps its bytes. A transparent node painted
  opaque (alpha >= 50%) is new ground at low + level x step; a node with ground erased to
  transparent keeps its ground (counted; ground is never removed from Photoshop). Grey is the
  mean of R, G and B.
- **Colour.** A node's colour is written only where its 8-bit value (round(v16 x 255 / 65535))
  differs, and only on ground; colour painted where there is no ground is counted and dropped.
  New ground she gave no colour takes its neighbours' (`ground_grid_edit.new_colour`).
- **The record.** `ground_grid_edit.apply_values`, one edit per save, named
  `paint_<name>_<n>`; undone like any other (`ground_grid_edit.py --undo`). A node the grid no
  longer holds as the painting last saw it (another edit or an undo since) refuses the whole save,
  unless it already holds what she painted. Shared tile edges are written in every tile.
- It does not build the game's tiles: the Blender panel's **Send ground to game** does.
Without a fresh export (the hook off), `save` asks Photoshop for one through
`tools/photoshop/ground_export.jsx` (which starts Photoshop), unless `--no-photoshop`. Saves of
one painting are applied in order under a lock; a save whose export a later one already covers
is skipped, since the painting is cumulative. The log of the hook's runs is
`~/Library/Logs/Keep Your Ticket/ground_paint.log`.

**Prove** runs the proofs on a scratch copy of the grid, no Photoshop: Photoshop's open, save
and export are simulated (its 15-bit levels, two rounding conventions), the PSD read back by the
reader here. See `--scratch`.
"""

import argparse
import datetime
import fcntl
import glob
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ground_grid_edit as gge  # noqa: E402  (the grid, apply_values, undo)

GROUND = os.path.join(ROOT, "assets", "source", "world_ground")
LEVELS = 32768  # Photoshop's 16-bit mode: 0..32768
HALF = 32768    # alpha at or over half (of 65535) is ground
WINDOWS = {"land": (-20.0, 480.0), "seabed": (-640.0, 0.0)}
SRGB_ICC = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
NAME_RE = re.compile(r"[a-z0-9][a-z0-9_]{0,23}$")


# =============================================================== PSD, by hand
# Written as Photoshop writes a 16-bit document: the layers in an `Lr16` block after an empty
# layer info, channels uncompressed. Read: any compression Photoshop uses (raw, RLE, ZIP, ZIP
# with prediction), layers in the main section or in `Lr16`/`Lr32`.

def _pascal(text, pad):
    b = text.encode("ascii", "replace")[:255]
    s = bytes([len(b)]) + b
    return s + b"\0" * ((-len(s)) % pad)


def _block(key, data, pad=4):
    data += b"\0" * ((-len(data)) % pad)
    return b"8BIM" + key + struct.pack(">I", len(data)) + data


def _luni(text):
    return _block(b"luni", struct.pack(">I", len(text)) + text.encode("utf-16-be"))


def write_psd(path, width, height, stack, composite, icc=None):
    """`stack`, top first: (group name, layer name, RGBA uint16 (h, w, 4), lock transparency). Each entry becomes a group holding one pixel layer. `composite` is RGB uint16
    (h, w, 3), the preview other apps show."""
    records, data = [], []
    lid = [0]

    def record(name, rect, chans, blend, flags, blocks):
        lid[0] += 1
        top, left, bottom, right = rect
        r = struct.pack(">iiiiH", top, left, bottom, right, len(chans))
        for cid, blob in chans:
            r += struct.pack(">hI", cid, len(blob))
        r += b"8BIM" + blend + struct.pack(">BBBB", 255, 0, flags, 0)
        extra = struct.pack(">I", 0)                       # no layer mask
        ranges = b"\x00\x00\xff\xff" * 2 * 5               # composite and four channels, all open
        extra += struct.pack(">I", len(ranges)) + ranges
        extra += _pascal(name, 4)
        extra += _luni(name) + _block(b"lyid", struct.pack(">I", lid[0])) + blocks
        r += struct.pack(">I", len(extra)) + extra
        records.append(r)
        data.append(b"".join(blob for _, blob in chans))

    empty = [(cid, struct.pack(">H", 0)) for cid in (-1, 0, 1, 2)]
    for group, layer, rgba, lock in reversed(stack):      # records run bottom to top
        record("</Layer group>", (0, 0, 0, 0), empty, b"norm", 0x18,
               _block(b"lsct", struct.pack(">I", 3)))
        chans = []
        for cid, ch in ((-1, 3), (0, 0), (1, 1), (2, 2)):
            chans.append((cid, struct.pack(">H", 0) + np.ascontiguousarray(rgba[:, :, ch]).astype(">u2").tobytes()))
        record(layer, (0, 0, height, width), chans, b"norm", 0x08 | (0x01 if lock else 0),
               _block(b"lspf", struct.pack(">I", 1 if lock else 0)))
        record(group, (0, 0, 0, 0), empty, b"pass", 0x18,
               _block(b"lsct", struct.pack(">I", 1) + b"8BIMpass"))
    info = struct.pack(">h", len(records)) + b"".join(records) + b"".join(data)
    section = struct.pack(">I", 0) + struct.pack(">I", 0) + _block(b"Lr16", info)
    res = b""
    resources = [(1005, struct.pack(">IHHIHH", 72 << 16, 1, 1, 72 << 16, 1, 1))]
    if icc:
        resources.append((1039, icc))
    for rid, blob in resources:
        res += b"8BIM" + struct.pack(">H", rid) + b"\0\0" + struct.pack(">I", len(blob)) + blob + b"\0" * (len(blob) % 2)
    head = b"8BPS" + struct.pack(">H6xHIIHH", 1, 3, height, width, 16, 3)
    body = [head, struct.pack(">I", 0), struct.pack(">I", len(res)), res,
            struct.pack(">I", len(section)), section, struct.pack(">H", 0)]
    for ch in range(3):
        body.append(np.ascontiguousarray(composite[:, :, ch]).astype(">u2").tobytes())
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        for b in body:
            f.write(b)
    os.replace(tmp, path)


def _unpackbits(src, n):
    out = bytearray()
    i = 0
    while len(out) < n and i < len(src):
        c = src[i]
        i += 1
        if c < 128:
            out += src[i:i + c + 1]
            i += c + 1
        elif c > 128:
            out += bytes([src[i]]) * (257 - c)
            i += 1
    return bytes(out[:n])


def _channel(blob, comp, rows, cols, depth, rle_counts=None):
    bpp = depth // 8
    dt = {1: ">u1", 2: ">u2", 4: ">f4"}[bpp]
    if comp == 0:
        raw = blob
    elif comp == 1:
        raw = b"".join(_unpackbits(s, cols * bpp) for s in rle_counts)
    elif comp in (2, 3):
        raw = zlib.decompress(blob)
    else:
        raise ValueError("PSD compression %d" % comp)
    if comp == 3:
        if bpp == 2:
            a = np.frombuffer(raw, ">u2").reshape(rows, cols).astype(np.uint32)
            return (np.cumsum(a, axis=1) % 65536).astype(np.uint16)
        if bpp == 1:
            a = np.frombuffer(raw, np.uint8).reshape(rows, cols).astype(np.uint32)
            return (np.cumsum(a, axis=1) % 256).astype(np.uint8)
        a = np.frombuffer(raw, np.uint8).reshape(rows, cols * 4).astype(np.uint32)
        a = (np.cumsum(a, axis=1) % 256).astype(np.uint8)
        return a.reshape(rows, 4, cols).transpose(0, 2, 1).copy().view(">f4").reshape(rows, cols)
    return np.frombuffer(raw, dt).reshape(rows, cols)


def read_psd(path, pixels=True, layers=True):
    """Header, image resources and layers (each: name, rect, flags, blend, lsct kind, channels by
    id). Layers' pixels only with `pixels`; without `layers`, stops after the resources (all a save
    reads of her document)."""
    b = open(path, "rb").read()
    if b[:4] != b"8BPS":
        raise ValueError("%s is not a Photoshop document" % path)
    version, nch, h, w, depth, mode = struct.unpack_from(">H6xHIIHH", b, 4)
    big = version == 2
    p = 26
    p += 4 + struct.unpack_from(">I", b, p)[0]
    n = struct.unpack_from(">I", b, p)[0]
    p += 4
    end, resources = p + n, {}
    while p < end:
        rid = struct.unpack_from(">H", b, p + 4)[0]
        q = p + 6 + ((1 + b[p + 6] + 1) // 2) * 2          # the name, a Pascal string padded to even
        size = struct.unpack_from(">I", b, q)[0]
        resources[rid] = b[q + 4:q + 4 + size]
        p = q + 4 + size + size % 2
    info = {"version": version, "channels": nch, "height": h, "width": w, "depth": depth,
            "mode": mode, "resources": resources, "layers": []}
    if not layers:
        return info
    L = ">Q" if big else ">I"
    ln = struct.calcsize(L)
    sec = struct.unpack_from(L, b, p)[0]
    p += ln
    sec_end = p + sec
    li = struct.unpack_from(L, b, p)[0]
    blobs = []
    if li:
        blobs.append(b[p + ln:p + ln + li])
    p += ln + li
    if p < sec_end:
        gm = struct.unpack_from(">I", b, p)[0]
        p += 4 + gm
    while p + 12 <= sec_end:
        if b[p:p + 4] not in (b"8BIM", b"8B64"):
            p += 1
            continue
        key = b[p + 4:p + 8]
        wide = big and key in (b"LMsk", b"Lr16", b"Lr32", b"Layr", b"Mt16", b"Mt32", b"Mtrn", b"Alph",
                               b"FMsk", b"lnk2", b"FEid", b"FXid", b"PxSD")
        size = struct.unpack_from(">Q" if wide else ">I", b, p + 8)[0]
        q = p + 8 + (8 if wide else 4)
        if key in (b"Lr16", b"Lr32", b"Layr"):
            blobs.append(b[q:q + size])
        p = q + size          # any padding after a block is skipped by the search for the next
    for blob in blobs:
        info["layers"] += _layers(blob, big, depth, pixels)
    return info


def _layers(blob, big, depth, pixels):
    count = abs(struct.unpack_from(">h", blob, 0)[0])
    p = 2
    out = []
    for _ in range(count):
        top, left, bottom, right, nch = struct.unpack_from(">iiiiH", blob, p)
        p += 18
        chans = []
        for _ in range(nch):
            cid = struct.unpack_from(">h", blob, p)[0]
            size = struct.unpack_from(">Q" if big else ">I", blob, p + 2)[0]
            p += 2 + (8 if big else 4)
            chans.append((cid, size))
        blend = blob[p + 4:p + 8]
        opacity, clip, flags = blob[p + 8], blob[p + 9], blob[p + 10]
        p += 12
        extra = struct.unpack_from(">I", blob, p)[0]
        p += 4
        e_end = p + extra
        m = struct.unpack_from(">I", blob, p)[0]
        p += 4 + m
        r = struct.unpack_from(">I", blob, p)[0]
        p += 4 + r
        nlen = blob[p]
        name = blob[p + 1:p + 1 + nlen].decode("latin-1")
        p += ((1 + nlen + 3) // 4) * 4
        lsct = None
        while p + 12 <= e_end:
            key = blob[p + 4:p + 8]
            size = struct.unpack_from(">I", blob, p + 8)[0]
            data = blob[p + 12:p + 12 + size]
            if key == b"luni":
                k = struct.unpack_from(">I", data, 0)[0]
                name = data[4:4 + 2 * k].decode("utf-16-be")
            elif key == b"lsct":
                lsct = struct.unpack_from(">I", data, 0)[0]
            p += 12 + size
        p = e_end
        out.append({"name": name, "rect": (top, left, bottom, right), "blend": blend, "opacity": opacity,
                    "flags": flags, "lsct": lsct, "chans": chans, "data": {}})
    for layer in out:
        top, left, bottom, right = layer["rect"]
        rows, cols = bottom - top, right - left
        for cid, size in layer["chans"]:
            blob_c = blob[p:p + size]
            p += size
            if not pixels or rows <= 0 or cols <= 0 or cid < -1:
                continue
            comp = struct.unpack_from(">H", blob_c, 0)[0]
            body = blob_c[2:]
            counts = None
            if comp == 1:
                cw = 4 if big else 2
                lens = struct.unpack_from(">%d%s" % (rows, "I" if big else "H"), body, 0)
                q = rows * cw
                counts = []
                for k in lens:
                    counts.append(body[q:q + k])
                    q += k
            layer["data"][cid] = _channel(body, comp, rows, cols, depth, counts)
    return out


def icc_name(icc):
    """The profile's description ('desc' or 'mluc'), or None."""
    if not icc or len(icc) < 132:
        return None
    n = struct.unpack_from(">I", icc, 128)[0]
    for i in range(n):
        sig, off, size = struct.unpack_from(">4sII", icc, 132 + 12 * i)
        if sig != b"desc":
            continue
        t = icc[off:off + size]
        if t[:4] == b"desc":
            k = struct.unpack_from(">I", t, 8)[0]
            return t[12:12 + k].rstrip(b"\0").decode("latin-1")
        if t[:4] == b"mluc":
            rec, rsz = struct.unpack_from(">II", t, 8)
            ln, o = struct.unpack_from(">II", t, 16 + 4)
            return t[o:o + ln].decode("utf-16-be")
    return None


# =============================================================== TIFF, by hand
# What the hook asks Photoshop for: uncompressed, little-endian, interleaved, 16 bits, with the
# transparency as an extra sample. Deflate (with or without the horizontal predictor) is read too.

TIFF_TYPES = {1: ("B", 1), 2: ("c", 1), 3: ("H", 2), 4: ("I", 4), 5: ("I", 8), 6: ("b", 1), 7: ("B", 1),
              8: ("h", 2), 9: ("i", 4), 10: ("i", 8), 11: ("f", 4), 12: ("d", 8), 16: ("Q", 8)}


def read_tiff(path):
    """(RGB uint16 (h, w, 3), alpha uint16 (h, w), ICC bytes or None). Unassociated alpha as it is;
    associated alpha is divided out."""
    b = open(path, "rb").read()
    e = {b"II": "<", b"MM": ">"}.get(b[:2])
    if e is None or struct.unpack_from(e + "H", b, 2)[0] != 42:
        raise ValueError("%s: not a TIFF (or a BigTIFF)" % path)
    ifd = struct.unpack_from(e + "I", b, 4)[0]
    tags = {}
    for i in range(struct.unpack_from(e + "H", b, ifd)[0]):
        tag, typ, cnt = struct.unpack_from(e + "HHI", b, ifd + 2 + 12 * i)
        fmt, size = TIFF_TYPES.get(typ, ("B", 1))
        total = size * cnt
        off = ifd + 2 + 12 * i + 8 if total <= 4 else struct.unpack_from(e + "I", b, ifd + 2 + 12 * i + 8)[0]
        if typ in (1, 2, 7):
            tags[tag] = b[off:off + cnt]
        elif typ in (5, 10):
            tags[tag] = struct.unpack_from(e + "%d%s" % (2 * cnt, fmt), b, off)
        else:
            tags[tag] = struct.unpack_from(e + "%d%s" % (cnt, fmt), b, off)
    w, h = tags[256][0], tags[257][0]
    spp = tags.get(277, (1,))[0]
    bps = tags.get(258, (1,))
    comp = tags.get(259, (1,))[0]
    photometric = tags.get(262, (2,))[0]
    planar = tags.get(284, (1,))[0]
    predictor = tags.get(317, (1,))[0]
    if any(v != 16 for v in bps) or tags.get(339, (1,))[0] != 1:
        raise ValueError("%s: want 16-bit unsigned samples, have %s" % (path, bps))
    if photometric not in (1, 2):
        raise ValueError("%s: want RGB or grey, have photometric %d" % (path, photometric))
    if 322 in tags:
        raise ValueError("%s: tiled TIFF not read here" % path)
    raw = b""
    for off, n in zip(tags[273], tags[279]):
        s = b[off:off + n]
        if comp in (8, 32946):
            s = zlib.decompress(s)
        elif comp != 1:
            raise ValueError("%s: TIFF compression %d not read here; export it uncompressed" % (path, comp))
        raw += s
    a = np.frombuffer(raw, e + "u2")
    if planar == 2:
        a = a.reshape(spp, h, w).transpose(1, 2, 0)
    else:
        a = a.reshape(h, w, spp)
    if predictor == 2:
        a = (np.cumsum(a.astype(np.uint32), axis=1) % 65536)
    a = a.astype(np.uint16)
    colour = 3 if photometric == 2 else 1
    rgb = a[:, :, :colour]
    if colour == 1:
        rgb = np.repeat(rgb, 3, axis=2)
    if spp > colour:
        alpha = a[:, :, colour].copy()
        if tags.get(338, (0,))[0] == 1:  # associated: divide it out
            safe = np.maximum(alpha, 1).astype(np.float64)
            rgb = np.clip(np.rint(rgb.astype(np.float64) * 65535.0 / safe[:, :, None]), 0, 65535).astype(np.uint16)
    else:
        alpha = np.full((h, w), 65535, np.uint16)
    return np.ascontiguousarray(rgb), alpha, tags.get(34675)


def write_tiff(path, rgba, extra=2, icc=None):
    """RGBA uint16 as Photoshop's uncompressed little-endian TIFF with transparency (the proofs'
    stand-in for its export)."""
    h, w, _ = rgba.shape
    pix = np.ascontiguousarray(rgba).astype("<u2").tobytes()
    entries = [(256, 4, [w]), (257, 4, [h]), (258, 3, [16] * 4), (259, 3, [1]), (262, 3, [2]),
               (273, 4, [0]), (277, 3, [4]), (278, 4, [h]), (279, 4, [len(pix)]), (284, 3, [1]),
               (338, 3, [extra]), (339, 3, [1] * 4)]
    if icc:
        entries.append((34675, 7, icc))
    n = len(entries)
    ifd_off = 8
    data_off = ifd_off + 2 + 12 * n + 4
    blobs = []
    for tag, typ, vals in entries:
        if typ == 7:
            payload = bytes(vals)
        else:
            payload = struct.pack("<%d%s" % (len(vals), TIFF_TYPES[typ][0]), *vals)
        blobs.append(payload)
    heap = b""
    ifd = struct.pack("<H", n)
    pos = data_off
    for (tag, typ, vals), payload in zip(entries, blobs):
        if len(payload) <= 4:
            ifd += struct.pack("<HHI", tag, typ, len(vals)) + payload + b"\0" * (4 - len(payload))
        else:
            ifd += struct.pack("<HHII", tag, typ, len(vals), pos)
            heap += payload + b"\0" * (len(payload) % 2)
            pos += len(payload) + len(payload) % 2
    ifd += struct.pack("<I", 0)
    pix_off = data_off + len(heap)
    ifd = bytearray(ifd)
    k = [t for t, _, _ in entries].index(273)
    struct.pack_into("<I", ifd, 2 + 12 * k + 8, pix_off)
    with open(path, "wb") as f:
        f.write(b"II" + struct.pack("<HI", 42, ifd_off) + bytes(ifd) + heap + pix)


# =============================================================== the region

def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def grid_extent(g):
    return (g.tx[0] * g.tile_m, g.tz[0] * g.tile_m, (g.tx[-1] + 1) * g.tile_m, (g.tz[-1] + 1) * g.tile_m)


def read_region(g, x0, z0, w, h):
    """Heights (float32, NaN for none) and colours (RGBA uint8) of the nodes in the region."""
    H = np.full((h, w), np.nan, np.float32)
    C = np.zeros((h, w, 4), np.uint8)
    X0, Z0 = g.tx[0] * g.tile_m, g.tz[0] * g.tile_m
    i0, j0 = int(round((x0 - X0) / g.step)), int(round((z0 - Z0) / g.step))
    for tz in g.tz:
        for tx in g.tx:
            ti, tj = (tx - g.tx[0]) * g.per, (tz - g.tz[0]) * g.per
            a, b2 = max(ti, i0), min(ti + g.per, i0 + w - 1)
            c, d = max(tj, j0), min(tj + g.per, j0 + h - 1)
            if a > b2 or c > d:
                continue
            H[c - j0:d - j0 + 1, a - i0:b2 - i0 + 1] = g.heights(tx, tz)[c - tj:d - tj + 1, a - ti:b2 - ti + 1]
            C[c - j0:d - j0 + 1, a - i0:b2 - i0 + 1] = g.colour(tx, tz)[c - tj:d - tj + 1, a - ti:b2 - ti + 1]
    return H, C


def region_tiles(g, x0, z0, x1, z1):
    return ["x%d_z%d" % (tx, tz) for tz in g.tz for tx in g.tx
            if tx * g.tile_m <= x1 and (tx + 1) * g.tile_m >= x0 and tz * g.tile_m <= z1 and (tz + 1) * g.tile_m >= z0]


def levels_of(H, lo, step):
    k = np.full(H.shape, -1, np.int64)
    m = ~np.isnan(H)
    k[m] = np.clip(np.rint((H[m].astype(np.float64) - lo) / step), 0, LEVELS).astype(np.int64)
    return k


def to16(k):
    """Photoshop's level k (0..32768) as a 16-bit file value."""
    return np.rint(np.asarray(k, np.float64) * 65535.0 / LEVELS).astype(np.uint16)


def from16(u):
    return np.rint(np.asarray(u, np.float64) * LEVELS / 65535.0).astype(np.int64)


def painting_paths(psd):
    d = os.path.dirname(os.path.abspath(psd))
    name = os.path.splitext(os.path.basename(psd))[0]
    return d, name, os.path.join(d, name + ".json"), os.path.join(d, name + "_synced.npz")


def layer_images(H, C, k, lo):
    h, w = H.shape
    ground = k >= 0
    hl = np.zeros((h, w, 4), np.uint16)
    u = to16(np.where(ground, k, 0))
    hl[:, :, 0] = hl[:, :, 1] = hl[:, :, 2] = np.where(ground, u, 0)
    hl[:, :, 3] = np.where(ground, 65535, 0)
    cl = np.zeros((h, w, 4), np.uint16)
    cg = C[:, :, 3] == 255
    cl[:, :, :3] = np.where(cg[:, :, None], C[:, :, :3].astype(np.uint16) * 257, 0)
    cl[:, :, 3] = np.where(cg, 65535, 0)
    comp = np.full((h, w, 3), 65535, np.uint16)
    comp = np.where((hl[:, :, 3] > 0)[:, :, None], hl[:, :, :3], comp)
    comp = np.where(cg[:, :, None], cl[:, :, :3], comp)
    return hl, cl, comp


def height_layer_name(lo, hi, step):
    return "height as opened (%g to %g m, %.2f cm a level)" % (lo, hi, step * 100)


def cmd_open(a):
    g = gge.Grid(a.root)
    ex0, ez0, ex1, ez1 = grid_extent(g)
    if bool(a.tiles) == bool(a.area):
        raise SystemExit("give --tiles or --area")
    if a.tiles:
        ts = []
        for t in a.tiles.split(","):
            m = re.match(r"^x(-?\d+)_z(-?\d+)$", t.strip())
            if not m:
                raise SystemExit("a tile is x<i>_z<j>, not %r" % t)
            ts.append((int(m.group(1)), int(m.group(2))))
        x0 = min(t[0] for t in ts) * g.tile_m
        z0 = min(t[1] for t in ts) * g.tile_m
        x1 = (max(t[0] for t in ts) + 1) * g.tile_m
        z1 = (max(t[1] for t in ts) + 1) * g.tile_m
        default = "_".join(t.strip().replace("-", "m") for t in a.tiles.split(","))
    else:
        v = [float(s) for s in a.area.split(",")]
        if len(v) != 4:
            raise SystemExit("--area is x0,z0,x1,z1 in world metres")
        x0 = np.floor(min(v[0], v[2]) / g.step) * g.step
        x1 = np.ceil(max(v[0], v[2]) / g.step) * g.step
        z0 = np.floor(min(v[1], v[3]) / g.step) * g.step
        z1 = np.ceil(max(v[1], v[3]) / g.step) * g.step
        default = ("x%d_z%d_%dx%dm" % (x0, z0, x1 - x0, z1 - z0)).replace("-", "m")
    x0, z0 = max(x0, ex0), max(z0, ez0)
    x1, z1 = min(x1, ex1), min(z1, ez1)
    if x1 <= x0 or z1 <= z0:
        raise SystemExit("the region lies outside the grid (x %g..%g, z %g..%g)" % (ex0, ex1, ez0, ez1))
    name = a.name or default
    if not NAME_RE.match(name):
        raise SystemExit("the painting's name is short snake_case (a-z, 0-9, _, up to 24): %r" % name)
    w = int(round((x1 - x0) / g.step)) + 1
    h = int(round((z1 - z0) / g.step)) + 1
    H, C = read_region(g, x0, z0, w, h)
    ground = ~np.isnan(H)
    if not ground.any():
        raise SystemExit("the region has no ground")
    gmin, gmax = float(np.nanmin(H)), float(np.nanmax(H))
    win = a.window
    if win in WINDOWS:
        lo, hi = WINDOWS[win]
        if gmin < lo or gmax > hi:
            lo = min(lo, np.floor((gmin - 5.0) / 10.0) * 10.0)
            hi = max(hi, np.ceil((gmax + 5.0) / 10.0) * 10.0)
            print("the region's ground runs %.2f..%.2f m, so the %s window widens to %g..%g m" % (gmin, gmax, win, lo, hi))
    elif win == "fit":
        margin = max(5.0, 0.05 * (gmax - gmin))
        lo, hi = np.floor(gmin - margin), np.ceil(gmax + margin)
    else:
        try:
            lo, hi = (float(s) for s in win.split(","))
        except ValueError:
            raise SystemExit("--window is land, seabed, fit or LO,HI")
        if not (lo < hi):
            raise SystemExit("the window's foot must be under its top")
        if gmin < lo or gmax > hi:
            raise SystemExit("the region's ground runs %.2f..%.2f m, outside %g..%g m: widen the window" % (gmin, gmax, lo, hi))
    lo, hi = float(lo), float(hi)
    step = (hi - lo) / LEVELS
    folder = os.path.join(a.root, "paint")
    os.makedirs(folder, exist_ok=True)
    gi = os.path.join(folder, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w") as f:
            f.write("# Ground paintings (tools/ground_paint.py): working files, never committed; the grid holds what they made.\n*\n")
    d = os.path.join(folder, name)
    psd = os.path.join(d, name + ".psd")
    _, _, side, synced = painting_paths(psd)
    if os.path.exists(psd):
        if not a.replace:
            raise SystemExit("%s exists and may hold her painting: choose another --name, or --replace "
                             "(which moves it to %s/replaced/)" % (psd, d))
        keep = os.path.join(d, "replaced", time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(keep, exist_ok=True)
        for p in (psd, side, synced):
            if os.path.exists(p):
                shutil.move(p, keep)
        print("the old painting is in %s" % keep)
    os.makedirs(os.path.join(d, "exports"), exist_ok=True)
    k = levels_of(H, lo, step)
    hl, cl, comp = layer_images(H, C, k, lo)
    icc = open(SRGB_ICC, "rb").read() if os.path.exists(SRGB_ICC) else None
    write_psd(psd, w, h, [("colour", "colour as opened", cl, True),
                          ("height", height_layer_name(lo, hi, step), hl, True)], comp, icc)
    np.savez_compressed(synced, base_height=H, base_level=k, height=H, level=k, colour=C)
    meta = {
        "about": "A ground painting made by tools/ground_paint.py open; its saves become grid edits (ground_paint.py save).",
        "name": name, "psd": name + ".psd",
        "region": {"x0": float(x0), "z0": float(z0), "x1": float(x1), "z1": float(z1), "width": w, "height": h,
                   "step_m": g.step, "axes": "north up: row r is z = z0 + step r, column c is x = x0 + step c",
                   "tiles": region_tiles(g, x0, z0, x1, z1)},
        "window": {"preset": win, "low_m": lo, "high_m": hi, "levels": LEVELS, "level_m": step,
                   "level": "round((y - low_m) / level_m); a 16-bit file value is round(level x 65535 / 32768)"},
        "opened": datetime.datetime.now().isoformat(timespec="seconds"),
        "grid_edits_at_open": len(gge.load_log(a.root)["edits"]),
        "saves": 0, "edits": [], "last_export": None, "last_save": None,
    }
    with open(side, "w") as f:
        json.dump(meta, f, indent=1)
        f.write("\n")
    nodes = int(ground.sum())
    print("OPENED %s: %d x %d nodes (x %g..%g, z %g..%g), %d with ground, %d without; window %g..%g m, "
          "%.2f cm a level; ground here runs %.2f..%.2f m" % (psd, w, h, x0, x1, z0, z1, nodes, w * h - nodes,
                                                             lo, hi, step * 100, gmin, gmax))
    if a.show:
        subprocess.run(["open", "-b", "com.adobe.Photoshop", psd], check=False)
    return psd


# =============================================================== save

def newest_export(d):
    best = None
    for p in glob.glob(os.path.join(d, "exports", "height-*.tif")):
        stamp = os.path.basename(p)[len("height-"):-len(".tif")]
        c = os.path.join(d, "exports", "colour-%s.tif" % stamp)
        if stamp.isdigit() and os.path.exists(c) and (best is None or int(stamp) > int(best[0])):
            best = (stamp, p, c)
    return best


def drop_exports(d, upto):
    for p in glob.glob(os.path.join(d, "exports", "*-*.tif")):
        s = os.path.basename(p).split("-", 1)[1][:-4]
        if s.isdigit() and int(s) <= int(upto):
            os.remove(p)


def photoshop_export(psd):
    script = os.path.join(HERE, "photoshop", "ground_export.jsx")
    r = subprocess.run(["osascript", "-e", 'tell application id "com.adobe.Photoshop" to do javascript file '
                        '(POSIX file "%s") with arguments {"%s"}' % (script, psd)], capture_output=True, text=True)
    print((r.stdout or r.stderr).strip())
    return r.returncode == 0 and r.stdout.startswith("EXPORTED")


def check_profile(where, icc):
    name = icc_name(icc) if icc else None
    if icc and (name is None or "srgb" not in name.lower()):
        raise SystemExit("%s carries the colour profile %r, not sRGB: the document was converted, so every value "
                         "moved; nothing was written. Convert it back to sRGB, or open the region again" % (where, name))


def cmd_save(a):
    psd = os.path.abspath(a.psd)
    d, name, side, synced = painting_paths(psd)
    if not os.path.exists(side) or not os.path.exists(synced):
        raise SystemExit("%s has no %s beside it: open regions with tools/ground_paint.py open" % (psd, os.path.basename(side)))
    root = os.path.dirname(os.path.dirname(d))
    with open(os.path.join(d, ".save.lock"), "w") as lockf:
        fcntl.flock(lockf, fcntl.LOCK_EX)
        a.stamp_used = None
        try:
            return _save(a, psd, d, name, side, synced, root)
        except SystemExit as x:
            # Refused or failed: say so in the sidecar (the hook's only trace besides its log), and
            # clear the export it read; the painting itself is untouched and saves again whole.
            if not a.dry:
                meta = json.load(open(side))
                meta["last_save"] = {"time": datetime.datetime.now().isoformat(timespec="seconds"),
                                     "result": str(x) if str(x).startswith("REFUSED") else "FAILED: %s" % x}
                with open(side + ".part", "w") as f:
                    json.dump(meta, f, indent=1)
                    f.write("\n")
                os.replace(side + ".part", side)
                if a.stamp_used:
                    drop_exports(d, a.stamp_used)
            raise


def _save(a, psd, d, name, side, synced, root):
    meta = json.load(open(side))
    R = meta["region"]
    w, h = R["width"], R["height"]
    lo, step = meta["window"]["low_m"], meta["window"]["level_m"]
    info = read_psd(psd, layers=False)
    if (info["width"], info["height"]) != (w, h) or info["mode"] != 3 or info["depth"] != 16:
        raise SystemExit("%s is %dx%d, mode %d, %d bits; its painting is %dx%d RGB 16 bits: it was resized or "
                         "converted, and nothing was written" % (psd, info["width"], info["height"], info["mode"],
                                                                  info["depth"], w, h))
    check_profile(psd, info["resources"].get(1039))
    # The painting is cumulative, so only the newest export matters: a run that finds its own
    # export already applied, by another save's run that took the lock first, has nothing to do.
    exp = newest_export(d)
    last = meta.get("last_export")
    if exp is not None and last is not None and int(exp[0]) <= int(last):
        drop_exports(d, exp[0])
        exp = None
    mtime = os.path.getmtime(psd)
    if exp is None and last is not None and int(last) / 1000.0 >= mtime - 0.5:
        print("SKIPPED %s: its last save is applied already (export %s)" % (name, last))
        return None
    fresh = exp is not None and int(exp[0]) / 1000.0 >= mtime - 0.5
    if not fresh:
        if a.no_photoshop:
            raise SystemExit("no export of %s newer than its last save: save it in Photoshop with the save hook on "
                             "(tools/photoshop/live_update.sh on), or run this without --no-photoshop" % psd)
        if not photoshop_export(psd):
            raise SystemExit("Photoshop did not export %s" % psd)
        exp = newest_export(d)
    stamp, hp, cp = exp
    a.stamp_used = stamp
    hrgb, ha, hicc = read_tiff(hp)
    crgb, ca, cicc = read_tiff(cp)
    for p, arr in ((hp, hrgb), (cp, crgb)):
        if arr.shape[:2] != (h, w):
            raise SystemExit("%s is %dx%d, the painting %dx%d" % (p, arr.shape[1], arr.shape[0], w, h))
    check_profile(cp, cicc)
    S = dict(np.load(synced))
    base_h, base_k = S["base_height"], S["base_level"]
    syn_h, syn_k, syn_c = S["height"], S["level"], S["colour"]

    # --- height
    grey = hrgb.astype(np.float64).mean(axis=2)
    kp = from16(grey)
    spread = from16(hrgb.max(axis=2)) - from16(hrgb.min(axis=2))
    opaque = ha >= HALF
    has = syn_k >= 0
    touched = has & opaque & (np.abs(kp - syn_k) > 1)
    born = ~has & opaque
    erased_n = int((has & ~opaque).sum())
    new_y = np.where(base_k >= 0,
                     np.where(np.abs(kp - base_k) <= 1, base_h.astype(np.float64),
                              base_h.astype(np.float64) + (kp - base_k) * step),
                     lo + kp * step).astype(np.float32)
    # --- colour
    c8 = np.rint(crgb.astype(np.float64) * 255.0 / 65535.0).astype(np.uint8)
    copaque = ca >= HALF
    ground_after = has | born
    cpaint = copaque & (np.any(c8 != syn_c[:, :, :3], axis=2) | (syn_c[:, :, 3] == 0))
    cwrite = cpaint & ground_after
    cdrop = int((cpaint & ~ground_after).sum())

    # --- what the grid holds now, for the nodes to write
    g = gge.Grid(root)
    Hn, Cn = read_region(g, R["x0"], R["z0"], w, h)
    hw = touched | born
    same_now = np.where(hw, (Hn.view(np.uint32) == syn_h.view(np.uint32)) | (np.isnan(Hn) & np.isnan(syn_h)), True)
    kn = levels_of(Hn, lo, step)
    there = hw & ~same_now & (kn >= 0) & (np.abs(kn - kp) <= 1)
    stale_h = hw & ~same_now & ~there
    cnow_same = np.all(Cn == syn_c, axis=2)
    want_c = np.concatenate([c8, np.full((h, w, 1), 255, np.uint8)], axis=2)
    cthere = cwrite & ~cnow_same & np.all(Cn == want_c, axis=2)
    stale_c = cwrite & ~cnow_same & ~cthere
    if stale_h.any() or stale_c.any():
        raise SystemExit("REFUSED %s: %d height and %d colour nodes she painted changed in the grid since this "
                         "painting last saw them (another edit, or an undo): nothing was written. Open the region "
                         "again under a new name and paint them there" % (name, int(stale_h.sum()), int(stale_c.sum())))
    hw = hw & ~there
    cw = cwrite & ~cthere
    rr, cc = np.nonzero(hw)
    xs = R["x0"] + g.step * cc
    zs = R["z0"] + g.step * rr
    values = {(float(x), float(z)): float(new_y[r, c]) for x, z, r, c in zip(xs, zs, rr, cc)}
    expect = {(float(x), float(z)): float(syn_h[r, c]) for x, z, r, c in zip(xs, zs, rr, cc)}
    cr, ccc = np.nonzero(cw)
    colours = {(float(R["x0"] + g.step * c), float(R["z0"] + g.step * r)): want_c[r, c] for r, c in zip(cr, ccc)}
    cexpect = {(float(R["x0"] + g.step * c), float(R["z0"] + g.step * r)): syn_c[r, c] for r, c in zip(cr, ccc)}
    n = meta["saves"] + 1
    dy = new_y[hw].astype(np.float64) - syn_h[hw].astype(np.float64)   # NaN where new ground
    parts = []
    if values:
        fin = dy[np.isfinite(dy)]
        newn = int((hw & ~has).sum())
        said = [s for s in ("%+.2f..%+.2f m" % (fin.min(), fin.max()) if fin.size else "",
                            "%d new ground" % newn if newn else "") if s]
        parts.append("%d nodes' height%s" % (len(values), " (%s)" % ", ".join(said) if said else ""))
    if colours:
        parts.append("%d nodes' colour" % len(colours))
    why = "painted in Photoshop, %s.psd save %d: %s" % (name, n, ", ".join(parts) or "nothing")
    notes = []
    if erased_n:
        notes.append("%d nodes erased to under half: they keep their ground" % erased_n)
    if cdrop:
        notes.append("%d nodes' colour painted where there is no ground: dropped" % cdrop)
    tinted = int((hw & (spread > 1)).sum())
    if tinted:
        notes.append("%d height nodes painted in a colour, not grey: their grey is the mean of R, G and B" % tinted)
    for s in notes:
        print("  note: " + s)
    entry = None
    if values or colours:
        entry = gge.apply_values(root, "paint_%s_%d" % (name, n), why, values, expect, dry=a.dry,
                                 made_by="tools/ground_paint.py save", colours=colours, colour_expect=cexpect,
                                 extra={"painting": os.path.relpath(psd, root), "save": n,
                                        "window_m": [lo, meta["window"]["high_m"]], "level_m": step,
                                        "colour_nodes": len(colours), "export": stamp})
    if a.dry:
        print("dry: nothing written")
        return entry
    # --- the painting's record of what the grid now holds
    g = gge.Grid(root)
    Hn, Cn = read_region(g, R["x0"], R["z0"], w, h)
    sync = touched | born
    syn_h = np.where(sync, Hn, syn_h).astype(np.float32)
    syn_k = np.where(sync, kp, syn_k)
    syn_c = np.where((cwrite | born)[:, :, None], Cn, syn_c)
    np.savez_compressed(synced + ".part.npz", base_height=base_h, base_level=base_k, height=syn_h, level=syn_k, colour=syn_c)
    os.replace(synced + ".part.npz", synced)
    if entry:
        meta["saves"] = n
        meta["edits"].append(entry["id"])
    meta["last_export"] = stamp
    result = ("SAVED %s %s: %s" % (entry["id"], entry["name"], why)) if entry else "NO CHANGE: nothing moved by more than a level, no colour changed; no edit"
    meta["last_save"] = {"time": datetime.datetime.now().isoformat(timespec="seconds"), "result": result, "notes": notes}
    with open(side + ".part", "w") as f:
        json.dump(meta, f, indent=1)
        f.write("\n")
    os.replace(side + ".part", side)
    drop_exports(d, stamp)
    print(result)
    if entry:
        print("  next: the Blender panel's Send ground to game builds the touched tiles (%s)" % ", ".join(entry["tiles"]))
    return entry


# =============================================================== proofs

def ps_open(psd):
    """Photoshop opening the PSD: each pixel layer's 16-bit values as its levels (0..32768).
    Returns (header, {layer name: RGBA levels})."""
    info = read_psd(psd)
    out = {}
    for L in info["layers"]:
        if L["lsct"] in (1, 2, 3) or not L["data"]:
            continue
        rgba = np.stack([L["data"][0], L["data"][1], L["data"][2], L["data"][-1]], axis=2)
        out[L["name"]] = from16(rgba)
    return info, out


def ps_write16(k, convention):
    if convention == "round":
        return to16(k)
    return np.minimum(np.asarray(k, np.int64) * 2, 65535).astype(np.uint16)  # "2k, capped"


def ps_save_and_export(psd, layers_k, convention, stamp=None):
    """Her save (the PSD rewritten with the layers' levels) and the hook's export of each group."""
    info = read_psd(psd, layers=False)
    w, h = info["width"], info["height"]
    names = list(layers_k)
    hname = [n for n in names if n.startswith("height")][0]
    cname = [n for n in names if n.startswith("colour")][0]
    hl = ps_write16(layers_k[hname], convention)
    cl = ps_write16(layers_k[cname], convention)
    comp = np.where((cl[:, :, 3] > 0)[:, :, None], cl[:, :, :3], np.where((hl[:, :, 3] > 0)[:, :, None], hl[:, :, :3], 65535))
    icc = info["resources"].get(1039)
    write_psd(psd, w, h, [("colour", cname, cl, True), ("height", hname, hl, True)], comp.astype(np.uint16), icc)
    time.sleep(0.01)
    stamp = stamp or str(int(time.time() * 1000) + 1500)
    d = os.path.dirname(psd)
    write_tiff(os.path.join(d, "exports", "height-%s.tif" % stamp), hl, icc=icc)
    write_tiff(os.path.join(d, "exports", "colour-%s.tif" % stamp), cl, icc=icc)
    return stamp


def tile_shas(root):
    return {os.path.relpath(p, root): sha(p) for p in sorted(glob.glob(os.path.join(root, "height", "*.exr")) +
                                                             glob.glob(os.path.join(root, "colour", "*.png")))}


def cmd_prove(a):
    scratch = os.path.abspath(a.scratch)
    root = os.path.join(scratch, "world_ground")
    if os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(root)
    for f in ("grid.json", "holes.json", "edits.json"):
        shutil.copy2(os.path.join(GROUND, f), root)
    for f in ("height", "colour", "history"):
        shutil.copytree(os.path.join(GROUND, f), os.path.join(root, f))
    start = tile_shas(root)
    log0 = open(os.path.join(root, "edits.json"), "rb").read()
    report = {"scratch": root}

    class A:
        pass

    def opened(name, area, window="land"):
        o = A()
        o.root, o.tiles, o.area, o.name, o.window, o.show, o.replace = root, None, area, name, window, False, True
        return cmd_open(o)

    def saved(psd, dry=False):
        o = A()
        o.psd, o.dry, o.no_photoshop = psd, dry, True
        return cmd_save(o)

    # 1. No-op, both conventions, over a region with holes, sea and the park.
    print("\n=== proof 1: open, save untouched")
    for conv in ("round", "2k"):
        psd = opened("noop_" + conv[0], "-1200,-1400,1400,400")
        info, lay = ps_open(psd)
        ps_save_and_export(psd, lay, conv)
        e = saved(psd)
        same = tile_shas(root) == start and open(os.path.join(root, "edits.json"), "rb").read() == log0
        print("no-op (%s): edit %s; every tile and the log bit for bit: %s" % (conv, e and e["id"], same))
        assert e is None and same
        report["noop_" + conv] = {"edit": None, "bit_exact": same, "pixels": int(info["width"] * info["height"])}

    # 2. A 30 m brush stroke raising 2 m, north-east of the park, across the corner of four tiles.
    print("\n=== proof 2a: a 30 m height stroke raising 2 m")
    area = (600.0, -1400.0, 1400.0, -600.0)
    psd = opened("stroke", ",".join("%g" % v for v in area))
    meta = json.load(open(painting_paths(psd)[2]))
    lo, step = meta["window"]["low_m"], meta["window"]["level_m"]
    info, lay = ps_open(psd)
    hname = [n for n in lay if n.startswith("height")][0]
    w, h = info["width"], info["height"]
    xs = area[0] + 2.0 * np.arange(w)
    zs = area[1] + 2.0 * np.arange(h)
    X, Z = np.meshgrid(xs, zs)
    path = np.array([[820.0, -1130.0], [940.0, -1050.0], [1000.0, -1000.0], [1080.0, -930.0], [1180.0, -880.0]])
    dist = np.full(X.shape, np.inf)
    for (ax, az), (bx, bz) in zip(path[:-1], path[1:]):
        vx, vz = bx - ax, bz - az
        t = np.clip(((X - ax) * vx + (Z - az) * vz) / (vx * vx + vz * vz), 0, 1)
        dist = np.minimum(dist, np.hypot(X - (ax + t * vx), Z - (az + t * vz)))
    radius, raise_m = 15.0, 2.0
    want = np.where(dist < radius, raise_m * 0.5 * (1 + np.cos(np.pi * dist / radius)), 0.0)  # soft round brush
    dk = np.rint(want / step).astype(np.int64)
    k = lay[hname].copy()
    paint = (k[:, :, 3] > 0)                                   # transparency locked
    for ch in range(3):
        k[:, :, ch] = np.where(paint, np.clip(k[:, :, ch] + dk, 0, LEVELS), k[:, :, ch])
    lay[hname] = k
    S0 = dict(np.load(painting_paths(psd)[3]))
    g = gge.Grid(root)
    H0, C0 = read_region(g, area[0], area[1], w, h)
    ps_save_and_export(psd, lay, "round")
    e = saved(psd)
    g = gge.Grid(root)
    H1, C1 = read_region(g, area[0], area[1], w, h)
    changed = H1.view(np.uint32) != H0.view(np.uint32)
    expect_set = paint & (np.abs(dk) > 1)
    expect_y = (H0.astype(np.float64) + dk * step).astype(np.float32)
    ok_set = np.array_equal(changed, expect_set)
    ok_val = np.array_equal(H1[expect_set].view(np.uint32), expect_y[expect_set].view(np.uint32))
    touched_err = np.abs(H1[expect_set].astype(np.float64) - (H0[expect_set].astype(np.float64) + want[expect_set]))
    faint = paint & (want > 0) & ~expect_set
    faint_err = np.abs(want[faint]) if faint.any() else np.array([0.0])
    tiles_now = tile_shas(root)
    other_same = all(tiles_now[p] == start[p] for p in start
                     if not any(("height/%s.exr" % t) == p for t in e["tiles"]))
    # shared edges: each touched node in every tile holding it
    edge_ok = True
    for (r, c) in zip(*np.nonzero(expect_set)):
        x, z = area[0] + 2.0 * c, area[1] + 2.0 * r
        vals = {g.heights(tx, tz)[rr, cc2].tobytes() for (tx, tz), rr, cc2 in g.homes(x, z)}
        edge_ok &= len(vals) == 1
    on_edges = int(sum(len(g.homes(area[0] + 2.0 * c, area[1] + 2.0 * r)) > 1 for (r, c) in zip(*np.nonzero(expect_set))))
    print("stroke: edit %s %s in %s; nodes changed %d, as expected %s; values = old + levels x step, bit for bit %s; "
          "every other node of every tile bit for bit %s; shared edges equal %s (%d nodes on tile edges)"
          % (e["id"], e["name"], e["tiles"], int(changed.sum()), ok_set, ok_val, other_same, edge_ok, on_edges))
    print("precision: touched nodes, worst |written - (old + brush)| %.4f m (half a level %.4f m); the stroke's faint "
          "edge under 1.5 levels left alone, at most %.4f m" % (touched_err.max(), step / 2, faint_err.max()))
    stroke_id = e["id"]
    r = subprocess.run([sys.executable, os.path.join(HERE, "ground_grid_edit.py"), "--undo", "--root", root],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    undone = tile_shas(root) == start and open(os.path.join(root, "edits.json"), "rb").read() == log0
    print("undo %s: every tile and the log bit for bit as before: %s" % (stroke_id, undone))
    assert ok_set and ok_val and other_same and edge_ok and undone
    report["stroke"] = {"edit": stroke_id, "nodes": int(changed.sum()), "tiles": e["tiles"], "edge_nodes": on_edges,
                        "worst_touched_m": float(touched_err.max()), "level_m": step,
                        "faint_edge_dropped_max_m": float(faint_err.max()), "undo_bit_exact": undone}

    # 2b. A colour stroke: a sandy path 12 m wide, hard edged, the same way; and colour on no ground.
    print("\n=== proof 2b: a colour stroke")
    psd = opened("colour_stroke", ",".join("%g" % v for v in area))
    info, lay = ps_open(psd)
    cname = [n for n in lay if n.startswith("colour")][0]
    sand = np.array([226, 205, 160])
    kc = lay[cname].copy()
    band = (dist < 6.0) & (kc[:, :, 3] > 0)
    for ch in range(3):
        kc[:, :, ch] = np.where(band, from16(np.uint16(sand[ch] * 257)), kc[:, :, ch])
    lay[cname] = kc
    ps_save_and_export(psd, lay, "2k")
    e = saved(psd)
    g = gge.Grid(root)
    H2, C2 = read_region(g, area[0], area[1], w, h)
    cchanged = np.any(C2 != C0, axis=2)
    cexp = band & np.any(C0[:, :, :3] != sand, axis=2)
    ok_c = np.array_equal(cchanged, cexp) and np.all(C2[cexp][:, :3] == sand)
    heights_same = np.array_equal(H2.view(np.uint32), H0.view(np.uint32))
    print("colour: edit %s, %d nodes' colour changed, exactly the stroke's %s; heights untouched %s"
          % (e["id"], int(cchanged.sum()), ok_c, heights_same))
    r = subprocess.run([sys.executable, os.path.join(HERE, "ground_grid_edit.py"), "--undo", "--root", root],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    undone_c = tile_shas(root) == start and open(os.path.join(root, "edits.json"), "rb").read() == log0
    print("undo: every tile and the log bit for bit as before: %s" % undone_c)
    assert ok_c and heights_same and undone_c
    report["colour"] = {"edit": e["id"], "nodes": int(cchanged.sum()), "undo_bit_exact": undone_c}

    # 2c. Both in one save, then painted back: one edit each; painting back restores the old values exactly.
    print("\n=== proof 2c: height and colour in one save, then painted back")
    psd = opened("both", ",".join("%g" % v for v in area))
    info, lay0 = ps_open(psd)
    lay = {n: v.copy() for n, v in lay0.items()}
    k = lay[hname]
    for ch in range(3):
        k[:, :, ch] = np.where(paint, np.clip(k[:, :, ch] + dk, 0, LEVELS), k[:, :, ch])
    kc = lay[cname].copy()
    for ch in range(3):
        kc[:, :, ch] = np.where(band, from16(np.uint16(sand[ch] * 257)), kc[:, :, ch])
    lay[cname] = kc
    ps_save_and_export(psd, lay, "round")
    e1 = saved(psd)
    ps_save_and_export(psd, lay0, "round")
    e2 = saved(psd)
    back = tile_shas(root)
    hb = all(back[p] == start[p] for p in start if p.startswith("height/"))
    g = gge.Grid(root)
    H3, C3 = read_region(g, area[0], area[1], w, h)
    cb = np.array_equal(C3, C0)
    print("one save, one edit: %s (%d height, %d colour nodes); painted back, edit %s: heights bit for bit as at "
          "the start %s, colours as at the start %s" % (e1["id"], e1["nodes"], e1.get("colour_nodes", 0),
                                                       e2 and e2["id"], hb, cb))
    for _ in range(2):
        subprocess.run([sys.executable, os.path.join(HERE, "ground_grid_edit.py"), "--undo", "--root", root],
                       capture_output=True, text=True)
    undone_b = tile_shas(root) == start and open(os.path.join(root, "edits.json"), "rb").read() == log0
    print("both undone: every tile and the log bit for bit as before: %s" % undone_b)
    assert hb and cb and undone_b
    report["both"] = {"edits": [e1["id"], e2 and e2["id"]], "painted_back_bit_exact": hb and cb, "undo_bit_exact": undone_b}

    # 2d. Masked nodes: new ground painted into the transparency (on a layer of her own: the group's
    # composite is what is exported), colour painted where there is no ground, an erase; then an
    # undo behind the painting's back, and a save over those nodes refused.
    print("\n=== proof 2d: masked nodes, an erase, and a refused save")
    marea = (-1000.0, -1000.0, -600.0, -600.0)
    psd = opened("masked", ",".join("%g" % v for v in marea))
    meta = json.load(open(painting_paths(psd)[2]))
    info, lay = ps_open(psd)
    hname = [n for n in lay if n.startswith("height")][0]
    cname = [n for n in lay if n.startswith("colour")][0]
    w2, h2 = info["width"], info["height"]
    g = gge.Grid(root)
    H0, C0 = read_region(g, marea[0], marea[1], w2, h2)
    none = np.isnan(H0)
    nb = np.zeros_like(none)
    nb[1:, :] |= ~none[:-1, :]
    nb[:-1, :] |= ~none[1:, :]
    nb[:, 1:] |= ~none[:, :-1]
    nb[:, :-1] |= ~none[:, 1:]
    rim = np.argwhere(none & nb)
    newg = [tuple(p) for p in rim[:20]]
    cpaint = [tuple(p) for p in rim[40:60]]
    land = np.argwhere(~none)
    erase = [tuple(p) for p in land[:5]]
    lvl = int(np.rint((-5.0 - meta["window"]["low_m"]) / meta["window"]["level_m"]))
    k = lay[hname].copy()
    for (r, c) in newg:
        k[r, c] = [lvl, lvl, lvl, LEVELS]
    for (r, c) in erase:
        k[r, c, 3] = 0
    lay[hname] = k
    kc = lay[cname].copy()
    for (r, c) in cpaint:
        kc[r, c] = list(from16((sand * 257).astype(np.uint16))) + [LEVELS]
    lay[cname] = kc
    ps_save_and_export(psd, lay, "round")
    e = saved(psd)
    g = gge.Grid(root)
    H1, C1 = read_region(g, marea[0], marea[1], w2, h2)
    born_ok = all(H1[r, c] == np.float32(meta["window"]["low_m"] + lvl * meta["window"]["level_m"]) and C1[r, c, 3] == 255
                  for (r, c) in newg)
    changed = (H1.view(np.uint32) != H0.view(np.uint32))
    only_born = set(map(tuple, np.argwhere(changed))) == set(newg)
    dropped = all(C1[r, c, 3] == 0 and np.isnan(H1[r, c]) for (r, c) in cpaint)
    kept = all(H1[r, c] == H0[r, c] for (r, c) in erase)
    print("new ground at -5 m on %d painted nodes, coloured from their neighbours: %s; nothing else moved: %s; "
          "colour painted on %d nodes without ground dropped: %s; %d erased nodes keep their ground: %s"
          % (len(newg), born_ok, only_born, len(cpaint), dropped, len(erase), kept))
    subprocess.run([sys.executable, os.path.join(HERE, "ground_grid_edit.py"), "--undo", "--root", root],
                   capture_output=True, text=True)
    k = lay[hname].copy()
    for (r, c) in newg:
        k[r, c] = [lvl + 400, lvl + 400, lvl + 400, LEVELS]
    lay[hname] = k
    ps_save_and_export(psd, lay, "round")
    try:
        saved(psd)
        refused = False
    except SystemExit as x:
        refused = str(x).startswith("REFUSED")
        print(str(x))
    undone_m = tile_shas(root) == start and open(os.path.join(root, "edits.json"), "rb").read() == log0
    print("after an undo behind its back, the painting's save over those nodes is refused: %s; every tile and the "
          "log as before: %s" % (refused, undone_m))
    assert born_ok and only_born and dropped and kept and refused and undone_m
    report["masked"] = {"edit": e["id"], "new_ground": len(newg), "colour_dropped": len(cpaint),
                        "erased_kept": len(erase), "stale_refused": refused, "bit_exact_after": undone_m}
    with open(os.path.join(scratch, "ground_paint_proofs.json"), "w") as f:
        json.dump(report, f, indent=1)
    print("\nPROOFS PASS; %s" % os.path.join(scratch, "ground_paint_proofs.json"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("open")
    o.add_argument("--tiles")
    o.add_argument("--area")
    o.add_argument("--name")
    o.add_argument("--window", default="land")
    o.add_argument("--show", action="store_true")
    o.add_argument("--replace", action="store_true")
    o.add_argument("--root", default=GROUND)
    s = sub.add_parser("save")
    s.add_argument("psd")
    s.add_argument("--dry", action="store_true")
    s.add_argument("--no-photoshop", action="store_true")
    p = sub.add_parser("prove")
    p.add_argument("--scratch", default=os.path.join(os.environ.get("TMPDIR", "/tmp"), "ground_paint_proofs"))
    a = ap.parse_args()
    {"open": cmd_open, "save": cmd_save, "prove": cmd_prove}[a.cmd](a)


if __name__ == "__main__":
    main()
