"""Bake the land's colour onto the height grid (2026-10-12, Stage 1, Bake, of
`documentation/terrain-height-grid-plan-2026-10-12.md`).

    /Applications/Blender.app/Contents/MacOS/Blender --background <copy of the master>.blend \
        --python tools/ground_colour_bake.py -- [--out <dir>] [--report <json>] [--heights <npy>]
    python3 tools/ground_colour_bake.py --map <png> [--colour <dir>]     # the mosaic; needs Pillow

Reads `assets/source/world_ground/grid.json` and writes `colour/x{tx}_z{tz}.png` beside it (or
under `--out`): 501 x 501, 8-bit sRGB RGBA, north up, row r at z = 1000 tz + 2 r, column c at
x = 1000 tx + 2 c, shared edges equal. Each node holds the colour the game feeds the land's
shader at that point on the top upward face of the master's `Ground` (the highest face whose
normal is at least `MIN_UP` up, as `scripts/world_terrain_source.gd` reads the ground; a node
exactly on an edge takes the higher computed height, then the lower face number, so always the
same face). Where only a face turned down lies over a node (five nodes at `1926e71`), the node
takes that face, so the colour covers every node the height grid does. Alpha is 255 there and
0 where there is no `Ground`, with the colour 0, so the image is already premultiplied. The
master is only read, never saved.

What "the colour the game feeds the shader" is, read from the game's files at run time:
- `scenes/world/world_terrain.tscn` overrides some bodies' materials by name.
- `landscape_depth_vertex.tres` (`landscape_depth_palette.gdshader`) reads the mesh's vertex
  colour as sRGB. Godot keeps a vertex colour as four bytes, each the float times 255 cut
  down (not rounded): measured 2026-10-12 against every vertex the game loads. So a corner
  feeds floor(255 Col) / 255, the GPU interpolates those across the face, and the node stores
  that interpolation rounded to the nearest byte.
- `landscape_depth_plain.tres` (the same shader) feeds its `base_color`, as sRGB.
- A StandardMaterial3D (`ground_shoulder.tres`, and every landform material that comes
  through the GLB, whose albedo Godot sets to the sRGB of the Principled Base Color) feeds
  its albedo straight to lighting. The palette shader that will read this image multiplies
  green-dominant colours by its gain first, so these nodes store the byte colour that the
  palette turns back into the material's albedo (`encode_albedo`), nearest in sRGB.
The palette's gain is the same near and far (both materials set `far_gain` to `near_gain`),
so it does not depend on where a point is; the bake refuses if that ever changes.

`--heights` also saves the chosen face's height at every node (float32, NaN where none) for
comparing with the height tiles. The report (`--report`) has the proofs: every vertex-coloured
node against its interpolated corners, every albedo node against its material, a ray-cast
check of the chosen face, coverage by material and shader, and the tiles read back.

`--map` mode runs under plain Python with Pillow: a north-up mosaic of the colour tiles at
8 m a pixel with a 1 km grid and the main places named.
"""

import json
import math
import os
import re
import struct
import sys
import time
import zlib

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
GRID = os.path.join(ROOT, "assets", "source", "world_ground", "grid.json")
WRAPPER = os.path.join(ROOT, "scenes", "world", "world_terrain.tscn")
PALETTE = os.path.join(ROOT, "assets", "shaders", "landscape_depth_palette.gdshader")
GROUND = "Ground"
MIN_UP = 0.05          # as scripts/world_terrain_source.gd: flatter than this has no top
INSIDE_EPS = 1e-6      # as scripts/world_terrain_source.gd, in barycentric units
CHUNK = 6_000_000      # candidate nodes per rasterising pass
# The palette's green mask, `smoothstep(0.025, 0.09, g - max(r, b))`; checked against the shader.
MASK_LO, MASK_HI = 0.025, 0.09

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


# ---------------------------------------------------------------- the game's colour model

def _floats(text):
    return [float(v) for v in text.split(",")]


def palette_defaults(path=PALETTE):
    with open(path) as f:
        src = f.read()
    assert f"smoothstep({MASK_LO}, {MASK_HI}," in src, "the palette's green mask changed; update MASK_LO/HI"
    assert "COLOR.rgb : base_color.rgb" in src, "the palette no longer reads COLOR or base_color as before"
    d = {}
    for name, kind in (("near_gain", "vec3"), ("far_gain", "vec3"), ("base_color", "vec4")):
        m = re.search(rf"uniform {kind} {name} = {kind}\(([^)]*)\)", src)
        d[name] = _floats(m.group(1))
    m = re.search(r"uniform bool use_vertex_color = (true|false)", src)
    d["use_vertex_color"] = m.group(1) == "true"
    return d


def read_material(res_path):
    """A .tres the wrapper names: what it feeds, as {'kind': ..., ...}."""
    path = os.path.join(ROOT, res_path.replace("res://", ""))
    with open(path) as f:
        src = f.read()
    name = os.path.basename(path)
    if 'type="StandardMaterial3D"' in src:
        m = re.search(r"albedo_color = Color\(([^)]*)\)", src)
        alb = _floats(m.group(1))[:3] if m else [1.0, 1.0, 1.0]
        assert "albedo_texture" not in src and "vertex_color_use_as_albedo" not in src, name
        return {"kind": "albedo", "name": name, "albedo_srgb": alb}
    if 'type="ShaderMaterial"' in src and "landscape_depth_palette.gdshader" in src:
        d = palette_defaults()
        for key in ("near_gain", "far_gain"):
            m = re.search(rf"shader_parameter/{key} = Vector3\(([^)]*)\)", src)
            if m:
                d[key] = _floats(m.group(1))
        m = re.search(r"shader_parameter/base_color = Color\(([^)]*)\)", src)
        if m:
            d["base_color"] = _floats(m.group(1))
        m = re.search(r"shader_parameter/use_vertex_color = (true|false)", src)
        if m:
            d["use_vertex_color"] = m.group(1) == "true"
        if max(abs(a - b) for a, b in zip(d["near_gain"], d["far_gain"])) > 0:
            raise SystemExit(f"{name}: far_gain differs from near_gain, so the palette's tint depends on "
                             "where a point is and one image cannot stand for it; refusing")
        kind = "palette_vertex" if d["use_vertex_color"] else "palette_base"
        return {"kind": kind, "name": name, "gain": d["near_gain"], "base_srgb": d["base_color"][:3]}
    raise SystemExit(f"{name}: a material the bake does not know how to read")


def wrapper_overrides(path=WRAPPER):
    """{node name: material res path} from the mounted wrapper's material_override lines."""
    with open(path) as f:
        src = f.read()
    ext = dict((m.group(2), m.group(1)) for m in
               re.finditer(r'\[ext_resource type="Material" path="([^"]+)" id="([^"]+)"\]', src))
    out = {}
    for m in re.finditer(r'\[node name="([^"]+)"[^\]]*\]\n((?:[^\[\n].*\n)*)', src):
        o = re.search(r'material_override = ExtResource\("([^"]+)"\)', m.group(2))
        if o:
            out[m.group(1)] = ext[o.group(1)]
    return out


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def palette_tint(s, gain):
    """The palette's sRGB colour before linearising, for input s (..., 3) in 0..1."""
    s = np.asarray(s, np.float64)
    m = smoothstep(MASK_LO, MASK_HI, s[..., 1] - np.maximum(s[..., 0], s[..., 2]))
    g = 1.0 + (np.asarray(gain, np.float64) - 1.0) * m[..., None]
    return np.clip(s * g, 0.0, 1.0)


def encode_albedo(target, gain):
    """The byte colour whose palette tint is nearest `target` (sRGB 0..1), worst channel first."""
    t = np.asarray(target, np.float64)
    centres = [np.rint(t * 255), np.rint(t / np.asarray(gain) * 255)]
    r = np.arange(-4, 5)
    cand = []
    for c in centres:
        g = np.stack(np.meshgrid(c[0] + r, c[1] + r, c[2] + r, indexing="ij"), -1).reshape(-1, 3)
        cand.append(g)
    cand = np.unique(np.clip(np.concatenate(cand), 0, 255), axis=0)
    out = palette_tint(cand / 255.0, gain)
    err = np.abs(out - t)
    key = np.lexsort((cand[:, 2], cand[:, 1], cand[:, 0], (err ** 2).sum(1), err.max(1)))
    best = cand[key[0]].astype(np.uint8)
    return best, float(err[key[0]].max() * 255)


def linear_to_srgb32(c):
    """Godot's Color.linear_to_srgb in float32, as the GLB importer sets albedo_color."""
    c = np.asarray(c, np.float32)
    lo = c * np.float32(12.92)
    hi = np.float32(1.055) * np.power(c, np.float32(1.0 / 2.4)) - np.float32(0.055)
    return np.where(c < np.float32(0.0031308), lo, hi).astype(np.float32)


# ---------------------------------------------------------------- reading Ground (Blender)

def gather_ground(bpy, overrides, gain_default):
    """Every triangle of Ground as Godot sees it, with what it feeds the shader."""
    coll = bpy.data.collections[GROUND]
    objs = sorted((o for o in coll.all_objects if o.type == "MESH"), key=lambda o: o.name)
    tris, corner_bytes, corner_raw, kind, mat_id, obj_id = [], [], [], [], [], []
    materials = []      # one entry per game material: name, shader, kind, encoded byte colour
    mat_index = {}
    objects = []
    palette = None

    def material(key, entry):
        if key not in mat_index:
            mat_index[key] = len(materials)
            materials.append(entry)
        return mat_index[key]

    for oi, o in enumerate(objs):
        me = o.data
        if not np.allclose(np.array(o.matrix_world), np.eye(4)):
            raise SystemExit(f"{o.name}: not at the identity; the bake reads mesh coordinates as world")
        if o.modifiers:
            raise SystemExit(f"{o.name}: has modifiers; the bake reads the mesh as stored")
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        loops = np.zeros(nt * 3, np.int32)
        me.loop_triangles.foreach_get("loops", loops)
        verts = np.zeros(nt * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", verts)
        polys = np.zeros(nt, np.int32)
        me.loop_triangles.foreach_get("polygon_index", polys)
        co = np.zeros(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        pmat = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", pmat)
        tmat = pmat[polys]
        p = co[verts].reshape(nt, 3, 3)
        objects.append({"name": o.name, "triangles": nt})
        over = overrides.get(o.name)
        if over:
            info = read_material(over)
            if info["kind"] == "palette_vertex":
                palette = info
                ca = me.color_attributes.get("Col")
                if ca is None or ca.domain != "CORNER":
                    raise SystemExit(f"{o.name}: wears {info['name']} but has no corner colour 'Col'")
                c = np.zeros(len(me.loops) * 4, np.float32)
                ca.data.foreach_get("color", c)
                c = c.reshape(-1, 4)[:, :3][loops].reshape(nt, 3, 3)
                cb = np.floor(c.astype(np.float64) * 255.0)
                if cb.min() < 0 or cb.max() > 255:
                    raise SystemExit(f"{o.name}: corner colours outside 0..1")
                mid = material(info["name"], {"name": info["name"], "shader": "landscape_depth_palette (vertex colour)",
                                             "kind": "palette_vertex", "byte": None})
                corner_bytes.append(cb.astype(np.uint8))
                corner_raw.append(c)
                kind.append(np.zeros(nt, np.uint8))
                mat_id.append(np.full(nt, mid, np.int32))
            else:
                if info["kind"] == "palette_base":
                    palette = palette or info
                    byte = np.floor(np.asarray(info["base_srgb"]) * 255.0 + 0.5).astype(np.uint8)
                    entry = {"name": info["name"], "shader": "landscape_depth_palette (base colour)",
                             "kind": "palette_base", "byte": byte, "feeds_srgb": info["base_srgb"]}
                else:
                    entry = {"name": info["name"], "shader": "StandardMaterial3D (albedo)", "kind": "albedo",
                             "albedo_srgb": info["albedo_srgb"], "byte": None}
                mid = material(info["name"], entry)
                corner_bytes.append(np.zeros((nt, 3, 3), np.uint8))
                corner_raw.append(np.zeros((nt, 3, 3), np.float32))
                kind.append(np.ones(nt, np.uint8))
                mat_id.append(np.full(nt, mid, np.int32))
        else:
            ids = np.zeros(nt, np.int32)
            for slot, m in enumerate(me.materials):
                use = tmat == slot
                if not use.any():
                    continue
                if m is None:
                    raise SystemExit(f"{o.name}: faces in an empty material slot")
                bsdf = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
                if bsdf is None or bsdf.inputs["Base Color"].is_linked:
                    raise SystemExit(f"{m.name}: not a plain Principled colour; the bake cannot read it")
                lin = list(bsdf.inputs["Base Color"].default_value)[:3]
                alb = [float(v) for v in linear_to_srgb32(lin)]
                ids[use] = material(m.name, {"name": m.name, "shader": "StandardMaterial3D (albedo)", "kind": "albedo",
                                             "albedo_srgb": alb, "base_linear": lin, "byte": None})
            corner_bytes.append(np.zeros((nt, 3, 3), np.uint8))
            corner_raw.append(np.zeros((nt, 3, 3), np.float32))
            kind.append(np.ones(nt, np.uint8))
            mat_id.append(ids)
        tris.append(p)
        obj_id.append(np.full(nt, oi, np.int32))

    gain = palette["gain"] if palette else gain_default
    for m in materials:
        if m["kind"] == "albedo":
            m["byte"], m["residual_levels"] = encode_albedo(m["albedo_srgb"], gain)
            m["palette_of_byte_srgb"] = [float(v) for v in palette_tint(m["byte"] / 255.0, gain)]
        elif m["kind"] == "palette_base":
            m["residual_levels"] = float(np.abs(m["byte"] / 255.0 - np.asarray(m["feeds_srgb"])).max() * 255)
    P = np.concatenate(tris).astype(np.float64)            # Blender (x, y, z)
    G = np.stack([P[..., 0], P[..., 2], -P[..., 1]], -1)   # Godot (x, y, z), exact
    return {
        "godot": G, "blender": P, "bytes": np.concatenate(corner_bytes), "raw": np.concatenate(corner_raw),
        "kind": np.concatenate(kind), "mat": np.concatenate(mat_id), "obj": np.concatenate(obj_id),
        "materials": materials, "objects": objects, "gain": gain,
    }


# ---------------------------------------------------------------- rasterising

def upward(Pb, sign=1.0):
    """Faces whose normal is at least MIN_UP up (sign -1: down), Blender's winding being the
    game's front."""
    n = np.cross(Pb[:, 1] - Pb[:, 0], Pb[:, 2] - Pb[:, 0])
    ln = np.linalg.norm(n, axis=1)
    return (ln > 0) & (sign * n[:, 2] >= MIN_UP * ln)


def barycentric(G, px, pz):
    a, b, c = G[:, 0], G[:, 1], G[:, 2]
    e0x, e0z = b[:, 0] - a[:, 0], b[:, 2] - a[:, 2]
    e1x, e1z = c[:, 0] - a[:, 0], c[:, 2] - a[:, 2]
    e2x, e2z = px - a[:, 0], pz - a[:, 2]
    den = e0x * e1z - e1x * e0z
    ok = np.abs(den) >= 1e-9
    den = np.where(ok, den, 1.0)
    u = (e2x * e1z - e1x * e2z) / den
    v = (e0x * e2z - e2x * e0z) / den
    h = a[:, 1] + u * (b[:, 1] - a[:, 1]) + v * (c[:, 1] - a[:, 1])
    return u, v, h, ok


def rasterise(G, use, spec, log, what="upward"):
    """Per node: the top upward face (index into G) and its height; -1 / NaN where none."""
    nx, nz, sp, x0, z0 = spec["nx"], spec["nz"], spec["spacing"], spec["x0"], spec["z0"]
    best_h = np.full(nx * nz, -np.inf)
    best_t = np.full(nx * nz, -1, np.int64)
    ids = np.nonzero(use)[0]
    X, Z = G[ids, :, 0], G[ids, :, 2]
    pad = 1e-6
    i0 = np.maximum(np.ceil((X.min(1) - pad - x0) / sp), 0).astype(np.int64)
    i1 = np.minimum(np.floor((X.max(1) + pad - x0) / sp), nx - 1).astype(np.int64)
    j0 = np.maximum(np.ceil((Z.min(1) - pad - z0) / sp), 0).astype(np.int64)
    j1 = np.minimum(np.floor((Z.max(1) + pad - z0) / sp), nz - 1).astype(np.int64)
    ni, nj = np.maximum(i1 - i0 + 1, 0), np.maximum(j1 - j0 + 1, 0)
    cnt = ni * nj
    keep = cnt > 0
    ids, i0, j0, ni, cnt = ids[keep], i0[keep], j0[keep], ni[keep], cnt[keep]
    cum = np.cumsum(cnt)
    start, total, passes = 0, int(cum[-1]) if len(cum) else 0, 0
    while start < len(ids):
        base = cum[start - 1] if start else 0
        stop = int(np.searchsorted(cum, base + CHUNK, side="right"))
        stop = max(stop, start + 1)
        sl = slice(start, stop)
        c = cnt[sl]
        rep = np.repeat(np.arange(start, stop), c)
        off = np.arange(int(c.sum())) - np.repeat(np.cumsum(c) - c, c)
        ii = i0[rep] + off % ni[rep]
        jj = j0[rep] + off // ni[rep]
        t = ids[rep]
        u, v, h, ok = barycentric(G[t], x0 + sp * ii, z0 + sp * jj)
        inside = ok & (u >= -INSIDE_EPS) & (v >= -INSIDE_EPS) & (u + v <= 1.0 + INSIDE_EPS)
        node = (jj * nx + ii)[inside]
        h, t = h[inside], t[inside]
        order = np.lexsort((t, -h, node))
        node, h, t = node[order], h[order], t[order]
        first = np.ones(len(node), bool)
        first[1:] = node[1:] != node[:-1]
        node, h, t = node[first], h[first], t[first]
        cur_h, cur_t = best_h[node], best_t[node]
        better = (h > cur_h) | ((h == cur_h) & (t < cur_t))
        best_h[node[better]] = h[better]
        best_t[node[better]] = t[better]
        passes += 1
        start = stop
    log(f"  rasterised {len(ids):,} {what} faces touching the lattice, {total:,} candidate nodes in {passes} passes")
    best_h[best_t < 0] = np.nan
    return best_t, best_h


def node_colours(D, best_t, spec):
    """RGBA per node, and the interpolated byte colour (float) on vertex-coloured nodes."""
    nx = spec["nx"]
    n = len(best_t)
    rgba = np.zeros((n, 4), np.uint8)
    interp = np.full((n, 3), np.nan)
    interp_raw = np.full((n, 3), np.nan)
    have = np.nonzero(best_t >= 0)[0]
    const = np.array([m["byte"] if m["byte"] is not None else (0, 0, 0) for m in D["materials"]], np.uint8)
    for s in range(0, len(have), 2_000_000):
        nodes = have[s:s + 2_000_000]
        t = best_t[nodes]
        ii, jj = nodes % nx, nodes // nx
        u, v, _, _ = barycentric(D["godot"][t], spec["x0"] + spec["spacing"] * ii, spec["z0"] + spec["spacing"] * jj)
        w = np.stack([1.0 - u - v, u, v], 1)
        w = np.clip(w, 0.0, None)
        w /= w.sum(1, keepdims=True)
        vc = D["kind"][t] == 0
        c = np.einsum("nk,nkc->nc", w[vc], D["bytes"][t[vc]].astype(np.float64))
        cr = np.einsum("nk,nkc->nc", w[vc], D["raw"][t[vc]].astype(np.float64)) * 255.0
        interp[nodes[vc]] = c
        interp_raw[nodes[vc]] = cr
        rgb = np.empty((len(nodes), 3), np.uint8)
        rgb[vc] = np.clip(np.floor(c + 0.5), 0, 255).astype(np.uint8)
        rgb[~vc] = const[D["mat"][t[~vc]]]
        rgba[nodes, :3] = rgb
        rgba[nodes, 3] = 255
    return rgba, interp, interp_raw


# ---------------------------------------------------------------- proofs

def ray_check(bpy, D, best_t, best_h, spec, samples, log):
    """An independent look at the chosen face: Blender's BVH, a ray straight down at sampled
    nodes, skipping faces that are not upward, against the rasteriser's face and height."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    P = D["blender"]
    T = len(P)
    verts = P.reshape(-1, 3)
    tree = BVHTree.FromPolygons([tuple(v) for v in verts], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(T)],
                                all_triangles=True, epsilon=0.0)
    up = upward(P)
    down = upward(P, -1.0)
    rng = np.random.default_rng(20261012)
    nx = spec["nx"]
    pick = rng.choice(len(best_t), size=samples, replace=False)
    same_face = same_h = miss_both = disagree = outer_edge = slipped = 0
    worst = 0.0
    examples = []

    def cast(x, z):
        origin = Vector((x, -z, 2000.0))
        first_down = (-1, None)
        for _ in range(64):
            loc, nrm, idx, dist = tree.ray_cast(origin, Vector((0, 0, -1)))
            if loc is None:
                break
            if up[idx]:
                return idx, loc.z
            if down[idx] and first_down[0] < 0:
                first_down = (idx, loc.z)
            origin = Vector((x, -z, loc.z - 1e-4))
        return first_down

    for node in pick:
        ii, jj = node % nx, node // nx
        gx, gz = spec["x0"] + spec["spacing"] * ii, spec["z0"] + spec["spacing"] * jj
        hit_t, hit_h = cast(gx, gz)
        t = best_t[node]
        if t < 0 and hit_t < 0:
            miss_both += 1
            continue
        offsets = ((1e-3, 0), (-1e-3, 0), (0, 1e-3), (0, -1e-3))

        def beside(t, h):
            """A ray 1 mm off meets the chosen face, or ground within 5 mm of its height."""
            for dx, dz in offsets:
                ht, hh = cast(gx + dx, gz + dz)
                if ht == t or (ht >= 0 and abs(hh - h) <= 5e-3):
                    return True
            return False
        if t >= 0 and hit_t < 0:
            # A node exactly on Ground's outer edge: the rasteriser takes it (inside within
            # INSIDE_EPS, as the generator's reader does); a ray there can slip past. Count it
            # as such only if a ray 1 mm off meets the same surface.
            if beside(t, best_h[node]):
                outer_edge += 1
                continue
        if t >= 0 and hit_t >= 0:
            d = abs(best_h[node] - hit_h)
            if hit_t == t:
                same_face += 1
                worst = max(worst, d)
            elif d <= 1e-3:
                same_h += 1
                worst = max(worst, d)
            elif hit_h < best_h[node] and beside(t, best_h[node]):
                # The ray slipped through an edge of the chosen face and met ground below;
                # 1 mm off it meets the chosen surface.
                slipped += 1
            else:
                disagree += 1
                if len(examples) < 10:
                    examples.append({"x": gx, "z": gz, "raster_h": float(best_h[node]), "ray_h": float(hit_h)})
        else:
            disagree += 1
            if len(examples) < 10:
                examples.append({"x": gx, "z": gz, "raster": int(t), "ray": int(hit_t)})
    res = {"samples": int(samples), "same_face": same_face, "other_face_same_height_1mm": same_h,
           "on_outer_edge": outer_edge, "slipped_through_an_edge": slipped, "no_ground_both": miss_both,
           "disagree": disagree,
           "worst_height_diff_m_same_face_or_height": worst, "examples": examples}
    log(f"  ray check: {samples:,} nodes, same face {same_face:,}, another face at the same height {same_h:,}, "
        f"on Ground's outer edge {outer_edge}, slipped through an edge {slipped}, no ground {miss_both:,}, "
        f"disagree {disagree}")
    return res


def proofs(D, best_t, rgba, interp, interp_raw, spec):
    have = best_t >= 0
    t = best_t[have]
    vc = D["kind"][t] == 0
    stored = rgba[have, :3].astype(np.float64)
    out = {}
    d_game = np.abs(stored[vc] - interp[have][vc])
    d_raw = np.abs(stored[vc] - interp_raw[have][vc])
    out["vertex_colour_nodes"] = int(vc.sum())
    out["vs_game_corners_max_levels"] = float(d_game.max()) if vc.any() else 0.0
    out["vs_game_corners_over_1_level"] = int((d_game.max(1) > 1.0).sum()) if vc.any() else 0
    out["vs_raw_Col_max_levels"] = float(d_raw.max()) if vc.any() else 0.0
    out["vs_raw_Col_over_1_level"] = int((d_raw.max(1) > 1.0 + 1e-9).sum()) if vc.any() else 0
    mats = D["mat"][t[~vc]]
    const = np.array([m["byte"] if m["byte"] is not None else (0, 0, 0) for m in D["materials"]], np.uint8)
    wrong = (rgba[have, :3][~vc] != const[mats]).any(1)
    out["albedo_or_base_nodes"] = int((~vc).sum())
    out["albedo_or_base_nodes_not_their_material"] = int(wrong.sum())
    out["alpha"] = {"255_with_ground": int((rgba[have, 3] == 255).sum()), "0_without": int((rgba[~have, 3] == 0).sum()),
                    "rgb_zero_without": int((rgba[~have, :3] == 0).all(1).sum()), "nodes_without": int((~have).sum())}
    return out


def coverage(D, best_t, spec):
    cell_ha = spec["spacing"] ** 2 / 1e4
    t = best_t[best_t >= 0]
    by_mat = np.bincount(D["mat"][t], minlength=len(D["materials"]))
    mats = []
    for m, n in zip(D["materials"], by_mat):
        mats.append({"material": m["name"], "shader": m["shader"], "nodes": int(n), "ha": round(float(n) * cell_ha, 2),
                     "byte": [int(v) for v in m["byte"]] if m["byte"] is not None else None})
    shaders = {}
    for m in mats:
        s = shaders.setdefault(m["shader"], {"nodes": 0, "ha": 0.0})
        s["nodes"] += m["nodes"]
        s["ha"] = round(s["ha"] + m["ha"], 2)
    by_obj = np.bincount(D["obj"][t], minlength=len(D["objects"]))
    objs = [{"object": o["name"], "nodes": int(n), "ha": round(float(n) * cell_ha, 2)} for o, n in zip(D["objects"], by_obj)]
    return {"by_material": sorted(mats, key=lambda r: -r["nodes"]), "by_shader": shaders,
            "by_object": sorted(objs, key=lambda r: -r["nodes"]),
            "nodes_with_ground": int(len(t)), "nodes_total": int(len(best_t)), "ha_with_ground": round(len(t) * cell_ha, 1)}


# ---------------------------------------------------------------- main (Blender)

def args_after_dashes():
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else []


def opt(rest, name, default=None):
    return rest[rest.index(name) + 1] if name in rest else default


def bake():
    import bpy
    started = time.time()
    rest = args_after_dashes()
    spec = grid_spec()
    out_dir = os.path.abspath(opt(rest, "--out", os.path.join(os.path.dirname(GRID), "colour")))
    report_path = opt(rest, "--report")
    heights_path = opt(rest, "--heights")
    samples = int(opt(rest, "--ray-samples", "200000"))
    lines = []

    def log(s):
        print(s, flush=True)
        lines.append(s)
    log("ground_colour_bake")
    log(f"  master   {bpy.data.filepath}")
    log(f"  lattice  {spec['nx']} x {spec['nz']} nodes, x {spec['x0']:.0f}.., z {spec['z0']:.0f}.., "
        f"{len(spec['tiles_x']) * len(spec['tiles_z'])} tiles")
    overrides = wrapper_overrides()
    D = gather_ground(bpy, overrides, palette_defaults()["near_gain"])
    G = D["godot"]
    use = upward(D["blender"])
    gx, gz = G[..., 0], G[..., 2]
    outside = int(((gx.min(1) < spec["x0"]) | (gx.max(1) > spec["x0"] + spec["spacing"] * (spec["nx"] - 1)) |
                   (gz.min(1) < spec["z0"]) | (gz.max(1) > spec["z0"] + spec["spacing"] * (spec["nz"] - 1))).sum())
    log(f"  Ground   {len(D['objects'])} objects, {len(G):,} triangles, {int(use.sum()):,} upward; "
        f"{outside} reach outside the grid; x {gx.min():.1f}..{gx.max():.1f}, z {gz.min():.1f}..{gz.max():.1f}")
    best_t, best_h = rasterise(G, use, spec, log)
    # Where no upward face lies over a node but a downward one does (a top face turned
    # down), the node takes that face, so the colour covers every node the height grid does.
    down_t, down_h = rasterise(G, upward(D["blender"], -1.0), spec, log, "downward")
    fill = (best_t < 0) & (down_t >= 0)
    over = (best_t >= 0) & (down_t >= 0) & (down_h > best_h)
    best_t[fill], best_h[fill] = down_t[fill], down_h[fill]
    log(f"  {int(fill.sum())} nodes have only a downward face over them and take its colour; "
        f"{int(over.sum())} have a downward face above the top upward one and keep the upward one's")
    del down_t, down_h
    rgba, interp, interp_raw = node_colours(D, best_t, spec)
    P = proofs(D, best_t, rgba, interp, interp_raw, spec)
    C = coverage(D, best_t, spec)
    R = ray_check(bpy, D, best_t, best_h, spec, samples, log) if samples > 0 else None

    os.makedirs(out_dir, exist_ok=True)
    img = rgba.reshape(spec["nz"], spec["nx"], 4)
    written = []
    for tz in spec["tiles_z"]:
        for tx in spec["tiles_x"]:
            rs, cs = tile_slice(spec, tx, tz)
            path = os.path.join(out_dir, f"x{tx}_z{tz}.png")
            png_write(path, img[rs, cs])
            written.append((tx, tz, path))
    # Read back: each file holds its slice of the lattice, and shared edges are equal.
    back_ok, edges_ok, edges = True, True, 0
    tiles = {}
    for tx, tz, path in written:
        a = png_read(path)
        rs, cs = tile_slice(spec, tx, tz)
        back_ok &= bool(np.array_equal(a, img[rs, cs]))
        tiles[(tx, tz)] = a
    for (tx, tz), a in tiles.items():
        if (tx + 1, tz) in tiles:
            edges_ok &= bool(np.array_equal(a[:, -1], tiles[(tx + 1, tz)][:, 0]))
            edges += 1
        if (tx, tz + 1) in tiles:
            edges_ok &= bool(np.array_equal(a[-1], tiles[(tx, tz + 1)][0]))
            edges += 1
    sizes = sum(os.path.getsize(p) for _, _, p in written)
    land_tiles = sum(1 for a in tiles.values() if a[..., 3].any())
    log(f"  wrote    {len(written)} tiles to {out_dir} ({sizes / 1e6:.1f} MB; {land_tiles} hold ground); "
        f"read back equal: {back_ok}; {edges} shared edges equal: {edges_ok}")
    log(f"  vertex-coloured nodes {P['vertex_colour_nodes']:,}: stored vs the game's interpolated corners, "
        f"max {P['vs_game_corners_max_levels']:.3f} of 255 ({P['vs_game_corners_over_1_level']} over 1); "
        f"vs Blender's raw Col, max {P['vs_raw_Col_max_levels']:.3f} ({P['vs_raw_Col_over_1_level']} over 1)")
    log(f"  material nodes {P['albedo_or_base_nodes']:,}: {P['albedo_or_base_nodes_not_their_material']} not their material's byte colour")
    for m in D["materials"]:
        if m["byte"] is not None:
            log(f"    {m['name']:<36} {m['shader']:<38} byte {tuple(int(v) for v in m['byte'])}  "
                f"residual {m.get('residual_levels', 0):.3f} of 255")
    for s, v in C["by_shader"].items():
        log(f"  {s:<44} {v['nodes']:>11,} nodes  {v['ha']:>9.1f} ha")
    if heights_path:
        np.save(heights_path, best_h.reshape(spec["nz"], spec["nx"]).astype(np.float32))
        log(f"  heights  {heights_path}")
    if report_path:
        rep = {"master": bpy.data.filepath, "frozen_commit": spec["frozen_commit"], "grid": {k: spec[k] for k in
               ("spacing", "n", "nx", "nz", "x0", "z0", "tiles_x", "tiles_z")},
               "triangles": len(G), "upward": int(use.sum()), "triangles_outside_grid": outside,
               "nodes_only_downward": int(fill.sum()), "nodes_downward_above_upward": int(over.sum()),
               "palette_gain": [float(v) for v in D["gain"]],
               "materials": [{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in m.items()} for m in D["materials"]],
               "proofs": P, "ray_check": R, "coverage": C,
               "files": {"tiles": len(written), "bytes": sizes, "with_ground": land_tiles,
                         "read_back_equal": back_ok, "shared_edges": edges, "shared_edges_equal": edges_ok},
               "seconds": round(time.time() - started, 1), "log": lines}
        with open(report_path, "w") as f:
            json.dump(rep, f, indent=1)
        log(f"  report   {report_path}")
    log(f"  {time.time() - started:.1f} s; the master was not saved")
    if not (back_ok and edges_ok and P["vs_game_corners_over_1_level"] == 0
            and P["albedo_or_base_nodes_not_their_material"] == 0):
        raise SystemExit("ground_colour_bake: a proof failed")


# ---------------------------------------------------------------- the map (plain Python)

def mosaic(out, colour_dir, step=4):
    from PIL import Image, ImageDraw, ImageFont
    spec = grid_spec()
    nz, nx = spec["nz"], spec["nx"]
    full = np.zeros((nz, nx, 4), np.uint8)
    for tz in spec["tiles_z"]:
        for tx in spec["tiles_x"]:
            rs, cs = tile_slice(spec, tx, tz)
            full[rs, cs] = png_read(os.path.join(colour_dir, f"x{tx}_z{tz}.png"))
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
              "as the palette shader will read it: the",
              "vertex colours the game interpolates today,",
              "and each landform material's albedo,",
              "encoded so the palette returns it.",
              f"Frozen master {spec['frozen_commit']}; {px:g} m a pixel,",
              "each pixel the mean of 4 x 4 nodes.",
              "Pale blue: no Ground (sea, and the",
              "generator's road corridor and anchors)."):
        d.text((x, y), t, fill=(50, 50, 50), font=font(13))
        y += 18
    img.save(out, optimize=True)
    print("wrote", out, img.size)


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
        IN_BLENDER = True
    except ImportError:
        IN_BLENDER = False
    if IN_BLENDER:
        bake()
    else:
        argv = sys.argv[1:]
        if "--map" not in argv:
            raise SystemExit(__doc__)
        mosaic(opt(argv, "--map"), opt(argv, "--colour", os.path.join(os.path.dirname(GRID), "colour")))
