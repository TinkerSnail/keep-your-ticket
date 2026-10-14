"""The ground's tile meshes, built from the height grid.

Stage 2 of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-13):
Blender's job of turning the grid, `assets/source/world_ground/height/`, into the
ordinary meshes the game loads. No Godot terrain system.

    Blender --background --factory-startup --python tools/blender/ground_build.py -- \
        [--tiles all|x0_z0,...] [--force] [--out DIR] [--held DUMP] [--no-seam]
        [--census PATH.blend] [--prove PATH.json] [--no-build] [--write-zones]

About 100 s for all 50 tiles from nothing (one core), and a few seconds more
for the held ground's faces, which it dumps with a headless Godot run of
`tools/_ground_faces_dump.gd` unless `--held` names a dump. A build that
changes nothing writes no file. The build is deterministic: the same heights,
zones and held ground give the same bytes.

It writes `assets/world_ground/tiles/x{tx}_z{tz}.glb`, one per tile that holds
ground, each one mesh object `ground_x{tx}_z{tz}`, then `manifest.json` and, when
every tile is written, an empty `BUILD_DONE` (deleted when a build starts).

What a tile's mesh is
---------------------
- **Vertices only on grid nodes**, at the node's height exactly as stored
  (float32), except the stitch band's (below). Tile-local: the object sits at the tile's (x0, 0, z0) in Godot
  terms, Blender (x0, -z0, 0), and a node (c, r) is the vertex (2c, H, 2r) in
  Godot, (2c, -2r, H) in Blender; the exporter turns Z up into Y up.
- **Collision**: the object is exported as `ground_x{tx}_z{tz}-col`, the hint
  `tools/export_world_source.py` gives the master's meshes, so Godot's importer
  builds a concave body from the visible mesh and names the node without it.
- **Every triangle faces up** (collision is one-sided).
- **UV0** = ((x - x0)/1000, (z - z0)/1000), the colour PNG's orientation in
  `grid.json` (row r is z0 + 2r); Blender's V is stored flipped because glTF's
  runs down the image.
- **Normals**: smooth, from the grid itself by central differences over the
  whole mosaic (one-sided beside a hole), so a node shared by two tiles has the
  same normal in both. Written as Blender's free per-vertex custom normals,
  which are exact.
- **Adaptive**: error-driven greedy insertion (Garland-Heckbert) through
  Blender's `delaunay_2d_cdt`. Every round, each triangle that is out of
  tolerance inserts one node, the worst; the round's points are triangulated
  again. Error is measured against the grid's bilinear surface on the half-node
  lattice, every node, edge midpoint and cell centre a triangle covers.
- **Tolerance by zone**, from `grid.json`'s `tolerance_zones`: a point takes the
  smallest tolerance of the zones that hold it. At a cell centre the bound is the
  zone's tolerance or the cell's own |twist|/4 (z00 + z11 - z10 - z01, over 4),
  whichever is larger: that is how far the bilinear centre lies from either
  diagonal, so it is what even the full grid mesh is off by, and no mesh with
  vertices only on nodes can do better there.
- **The data's own edge**: the region a mesh may cover is every full-grid
  triangle whose three nodes hold ground (a cell with four, or the half of a
  cell with three). Its boundary is fed to the triangulation as constraint
  edges, so no triangle touches a NaN node and the edge follows the data node
  for node. The tile's border is the triangulation's hull.
- **No cracks**: two tiles share a border line of 501 nodes. Each tile is first
  refined on its own with its borders free (phase 1); the nodes it put on each
  border are its requests. A shared line's vertex set is the union of both
  tiles' requests, refined along the line in one dimension until every segment
  holds the tolerance there. Each tile is then built again (phase 2) with its
  border sets fixed and no other border node allowed, so both sides draw the
  same segments. Where phase 2 cannot meet the tolerance without another border
  node it asks for it; the node is added to that line for both tiles and both
  are built again (an "augmentation"; counted in the manifest).
- **Where the generator's held ground meets it** (the road corridor, the tunnel
  lids, NT-2's earth and cuts; and the west shell's and the anchors' solids
  through `holes.json`'s meets), the grid is carved and stitched so it meets
  each held edge exactly, as the master did: see "the ground the generator
  still holds" below. `--no-seam` builds the grid alone.
- **The open sea's edge**: where the grid's outer edge would end above the
  water, its first ring of open-sea no-data nodes runs it on down to -16 m (see
  `SKIRT_Y`), as the master's coasts ran on under the water.

Re-export only what changed
---------------------------
`manifest.json` records per tile the inputs its mesh is a function of, hashed:
its own heights as carved, the row beyond each side (normals), its four border
sets, the held faces and edges over it and the pieces it is stitched to, the
zones, and this file's core and export versions. A tile whose hash and GLB are
unchanged is not built or written again. Phase 1's requests are cached by the
tile's own EXR and the zones. `--force` builds everything from nothing.
`--tiles` limits the build to the tiles named, and adds any neighbour whose
border set changed with them, so no crack opens.

Other modes
-----------
- `--write-zones` (re)derives `tolerance_zones` and writes it into `grid.json`:
  the park's envelope from `ParkPlan.REBUILD_FOOTPRINT_*` plus 45 m; the road
  centrelines (`ParkPlan.highway_path()`, `approach_road_points()`, the front
  road, `town_streets()`) and the towns' outlines (`north_town_outline()`,
  `BEACH_TOWN_OUTLINE`) by a headless Godot run of a throwaway script; the
  city's road ribbons (`city_highway_extension`, `bridge_main_deck`,
  `bridge_city_intersection`, `bridge_city_southern_offramp`,
  `southern_city_bypass_centreline`, `southern_coastal_highway_extension_centreline`)
  and its extent (the hull of `city_block_*`, `city_skyline_anchor_*` and
  `city_ferry_terminal`) from `assets/source/far_shore_city_relocation.blend`.
- `--census PATH.blend` imports every tile GLB from the output folder into a
  collection `Ground`, world coordinates (Blender's: x, -z, y), transforms
  applied, and saves it there; for the floater census. Never into the tree.
- `--prove PATH.json` measures the written GLBs, read back by this file's own
  reader: triangles per tile and zone, error against the bilinear grid per zone
  (nodes, edge midpoints, centres, and a quarter-node lattice), the shared edges
  and normals, unpaired edges (on the data's edge, on a held edge, or at a
  band's end) and T-junctions, faces up, sizes.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
SRC = os.path.join(ROOT, "assets", "source", "world_ground")
OUT = os.path.join(ROOT, "assets", "world_ground", "tiles")
GODOT = os.environ.get("GODOT", "/Applications/Godot.app/Contents/MacOS/Godot")
CITY_BLEND = os.path.join(ROOT, "assets", "source", "far_shore_city_relocation.blend")

CORE_VERSION = "ground_build core 3"
EXPORT_VERSION = "ground_build export 1"
SIDES = ("n", "s", "w", "e")
OPPOSITE = {"n": "s", "s": "n", "w": "e", "e": "w"}
STEP = {"n": (0, -1), "s": (0, 1), "w": (-1, 0), "e": (1, 0)}
RATIO_EPS = 1e-9
CHUNK = 1_500_000
PARK_MARGIN_M = 45.0
WALK_WITHIN_M = 300.0

# Godot's import settings for a tile, those of `assets/world_terrain_master.glb`:
# no LODs, and no vertex compression, which would quantise positions to 16 bits
# of the tile's bounds (1.5 cm over a kilometre) and open the shared edges.
IMPORT_FILE = """[remap]

importer="scene"
importer_version=1
type="PackedScene"

[params]

nodes/root_type=""
nodes/root_name=""
nodes/root_script=null
mesh_library/use_node_names_as_mesh_names=false
array_mesh/deduplicate_surfaces=true
nodes/apply_root_scale=true
nodes/root_scale=1.0
nodes/import_as_skeleton_bones=false
nodes/use_name_suffixes=true
nodes/use_node_type_suffixes=true
meshes/ensure_tangents=true
meshes/generate_lods=false
meshes/create_shadow_meshes=true
meshes/light_baking=1
meshes/lightmap_texel_size=0.2
meshes/force_disable_compression=true
skins/use_named_skins=true
animation/import=false
animation/fps=30
animation/trimming=false
animation/remove_immutable_tracks=true
animation/import_rest_as_RESET=false
import_script/path=""
materials/extract=0
materials/extract_format=0
materials/extract_path=""
_subresources={}
gltf/naming_version=2
gltf/embedded_image_handling=1
gltf/texture_map_mode=1
"""


def log(*a):
    print("ground_build:", *a, flush=True)


def _bake():
    """`tools/ground_bake.py`, the grid's own EXR reader and `Grid`."""
    spec = importlib.util.spec_from_file_location("ground_bake", os.path.join(ROOT, "tools", "ground_bake.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def tile_name(tx, tz):
    return "x%d_z%d" % (tx, tz)


# --- zones -------------------------------------------------------------------

class Zones:
    """`grid.json`'s `tolerance_zones`, evaluated on regular grids of points."""

    PARK, WALK, ELSE = 0, 1, 2
    NAMES = ("park", "walkable", "elsewhere")

    def __init__(self, spec):
        self.spec = spec
        zones = {z["name"]: z for z in spec["zones"]}
        park, walk = zones["park"], zones["walkable"]
        self.tol = np.array([float(park["tolerance_m"]), float(walk["tolerance_m"]), float(spec["default_m"])])
        self.rect = [float(v) for v in park["rect"]]
        self.within = float(walk["within_m"])
        segs = []
        for line in walk["lines"].values():
            p = np.asarray(line, np.float64)
            segs.append(np.concatenate([p[:-1], p[1:]], 1))
        self.segs = np.concatenate(segs) if segs else np.zeros((0, 4))
        self.polys = [np.asarray(p, np.float64) for p in walk["polygons"].values()]
        self.sha = sha_json(spec)

    def grid(self, xs, zs):
        """Zone ids (uint8) at every (x, z) of ascending coordinate vectors,
        shaped (len(zs), len(xs))."""
        xs = np.asarray(xs, np.float64)
        zs = np.asarray(zs, np.float64)
        walk = np.zeros((len(zs), len(xs)), bool)
        w = self.within
        for ax, az, bx, bz in self.segs:
            i0 = np.searchsorted(xs, min(ax, bx) - w, "left")
            i1 = np.searchsorted(xs, max(ax, bx) + w, "right")
            j0 = np.searchsorted(zs, min(az, bz) - w, "left")
            j1 = np.searchsorted(zs, max(az, bz) + w, "right")
            if i0 >= i1 or j0 >= j1:
                continue
            px = xs[i0:i1][None, :] - ax
            pz = zs[j0:j1][:, None] - az
            dx, dz = bx - ax, bz - az
            l2 = dx * dx + dz * dz
            t = np.clip((px * dx + pz * dz) / l2, 0.0, 1.0) if l2 > 0 else 0.0
            walk[j0:j1, i0:i1] |= (px - t * dx) ** 2 + (pz - t * dz) ** 2 <= w * w
        for poly in self.polys:
            px = xs[None, :]
            pz = zs[:, None]
            inside = np.zeros_like(walk)
            n = len(poly)
            for k in range(n):
                x1, z1 = poly[k]
                x2, z2 = poly[(k + 1) % n]
                if z1 == z2:
                    continue
                cross = (z1 > pz) != (z2 > pz)
                xint = x1 + (pz - z1) * (x2 - x1) / (z2 - z1)
                inside ^= cross & (px < xint)
            walk |= inside
        x0, z0, x1, z1 = self.rect
        park = ((xs >= x0) & (xs <= x1))[None, :] & ((zs >= z0) & (zs <= z1))[:, None]
        out = np.full(walk.shape, self.ELSE, np.uint8)
        out[walk] = self.WALK
        out[park] = self.PARK
        return out


# --- one tile's grid ----------------------------------------------------------

class TileData:
    """A tile's heights, the region its mesh may cover, the reference surface
    and tolerance on the half-node lattice, and the region's boundary."""

    def __init__(self, tx, tz, H, zones, spacing=2.0, tile_m=1000.0):
        n = H.shape[0]
        self.tx, self.tz, self.n = tx, tz, n
        self.spacing = spacing
        self.x0, self.z0 = tile_m * tx, tile_m * tz
        self.H = H.astype(np.float32)
        V = np.isfinite(self.H)
        Z = self.H.astype(np.float64)
        self.V, self.Z = V, Z
        a, b, c, d = V[:-1, :-1], V[:-1, 1:], V[1:, :-1], V[1:, 1:]
        nv = a.astype(np.int8) + b + c + d
        self.c4 = nv == 4
        self.c3 = nv == 3
        # The NaN corner of a three-node cell: 0 (c, r), 1 (c+1, r), 2 (c, r+1), 3 (c+1, r+1).
        nanc = np.where(~a, 0, np.where(~b, 1, np.where(~c, 2, 3)))
        self.nanc = np.where(self.c3, nanc, -1).astype(np.int8)
        S = 2 * n - 1
        self.S = S
        R = np.full((S, S), np.nan)
        R[0::2, 0::2] = Z
        R[0::2, 1::2] = (Z[:, :-1] + Z[:, 1:]) / 2
        R[1::2, 0::2] = (Z[:-1, :] + Z[1:, :]) / 2
        z00, z10, z01, z11 = Z[:-1, :-1], Z[:-1, 1:], Z[1:, :-1], Z[1:, 1:]
        with np.errstate(invalid="ignore"):
            cen4 = (z00 + z10 + z01 + z11) / 4
            # A three-node cell's centre lies on its hypotenuse, between the two
            # corners beside the NaN one.
            hyp_bc = (z10 + z01) / 2
            hyp_ad = (z00 + z11) / 2
            cen3 = np.where((nanc == 0) | (nanc == 3), hyp_bc, hyp_ad)
            R[1::2, 1::2] = np.where(self.c4, cen4, np.where(self.c3, cen3, np.nan))
            floor = np.where(self.c4, np.abs(z00 + z11 - z10 - z01) / 4, 0.0)
        self.R = R
        self.floor = floor
        xs = self.x0 + np.arange(S) * spacing / 2
        zs = self.z0 + np.arange(S) * spacing / 2
        self.zid = zones.grid(xs, zs)
        T = zones.tol[self.zid]
        T[1::2, 1::2] = np.maximum(T[1::2, 1::2], floor * (1 + 1e-9) + 1e-6)
        self.T = T
        self.tol = zones.tol[self.zid]
        self._boundary()

    def _boundary(self):
        n = self.n
        c4, c3, nanc = self.c4, self.c3, self.nanc
        cov_top = c4 | (c3 & (nanc != 0) & (nanc != 1))
        cov_bot = c4 | (c3 & (nanc != 2) & (nanc != 3))
        cov_left = c4 | (c3 & (nanc != 0) & (nanc != 2))
        cov_right = c4 | (c3 & (nanc != 1) & (nanc != 3))
        edges = []
        # Horizontal sides on the lines r = 1 .. n-2, between cells r-1 and r.
        hb = cov_bot[:-1, :] ^ cov_top[1:, :]
        r, c = np.nonzero(hb)
        r = r + 1
        edges.append(np.stack([r * n + c, r * n + c + 1], 1))
        # Vertical sides on the lines c = 1 .. n-2, between cells c-1 and c.
        vb = cov_right[:, :-1] ^ cov_left[:, 1:]
        r, c = np.nonzero(vb)
        c = c + 1
        edges.append(np.stack([r * n + c, (r + 1) * n + c], 1))
        # Every three-node cell's hypotenuse.
        r, c = np.nonzero(c3)
        k = nanc[r, c]
        anti = (k == 0) | (k == 3)
        p = np.where(anti, r * n + c + 1, r * n + c)
        q = np.where(anti, (r + 1) * n + c, (r + 1) * n + c + 1)
        edges.append(np.stack([p, q], 1))
        self.cons = np.concatenate(edges).astype(np.int64) if edges else np.zeros((0, 2), np.int64)
        req = np.zeros(n * n, bool)
        req[self.cons.ravel()] = True
        for cr in ((0, 0), (n - 1, 0), (0, n - 1), (n - 1, n - 1)):
            if self.V[cr[1], cr[0]]:
                req[cr[1] * n + cr[0]] = True
        self.required = req

    def has_ground(self):
        return bool(self.c4.any() or self.c3.any())

    def in_region(self, T):
        """Whether each triangle (node indices) lies in the region, by the cell
        holding its centroid (exact, in thirds of a node)."""
        n = self.n
        c = T % n
        r = T // n
        sc = c.sum(1)
        sr = r.sum(1)
        cc = sc // 3
        rr = sr // 3
        u = sc - 3 * cc
        v = sr - 3 * rr
        cc = np.minimum(cc, n - 2)
        rr = np.minimum(rr, n - 2)
        k = self.nanc[rr, cc]
        half = np.where(k == 0, u + v > 3, np.where(k == 1, v > u, np.where(k == 2, u > v, u + v < 3)))
        return self.c4[rr, cc] | (self.c3[rr, cc] & half)

    def border_nodes(self, side):
        """Node indices along a side, in order of position 0 .. n-1."""
        n = self.n
        k = np.arange(n)
        return {"n": k, "s": (n - 1) * n + k, "w": k * n, "e": k * n + n - 1}[side]


# --- triangulation ------------------------------------------------------------

def triangulate(nodes, n, cons_nodes):
    """Constrained Delaunay triangulation of the nodes (flat indices into an
    n-wide grid) with constraint edges between nodes; triangles as node indices."""
    from mathutils.geometry import delaunay_2d_cdt
    pos = np.full(n * n, -1, np.int64)
    pos[nodes] = np.arange(len(nodes))
    pts = list(zip((nodes % n).astype(np.float64).tolist(), (nodes // n).astype(np.float64).tolist()))
    cons = pos[cons_nodes]
    if (cons < 0).any():
        raise RuntimeError("a constraint edge ends at a node that is not a vertex")
    out = delaunay_2d_cdt(pts, cons.tolist(), [], 0, 1e-6, False)
    ov = np.array([tuple(v) for v in out[0]], np.float64)
    if len(ov) != len(nodes):
        raise RuntimeError("delaunay_2d_cdt merged or added vertices (%d in, %d out)" % (len(nodes), len(ov)))
    oc = np.rint(ov[:, 0]).astype(np.int64)
    orr = np.rint(ov[:, 1]).astype(np.int64)
    if np.abs(ov[:, 0] - oc).max() > 1e-6 or np.abs(ov[:, 1] - orr).max() > 1e-6:
        raise RuntimeError("delaunay_2d_cdt moved a vertex off its node")
    node_of = orr * n + oc
    faces = out[2]
    if any(len(f) != 3 for f in faces):
        raise RuntimeError("delaunay_2d_cdt returned a face that is not a triangle")
    return node_of[np.array(faces, np.int64).reshape(-1, 3)]


def _expand(counts):
    counts = np.asarray(counts, np.int64)
    rep = np.repeat(np.arange(len(counts), dtype=np.int64), counts)
    starts = np.cumsum(counts) - counts
    local = np.arange(int(counts.sum()), dtype=np.int64) - starts[rep]
    return rep, local, starts


def scan(td, T, q):
    """Every point of the lattice with `q` points per node spacing that lies in
    each triangle (node indices; edges included), by scanline, so a sliver costs
    its area and not its bounding box. Yields chunks of (triangle index, x, y,
    height on the triangle's plane), grouped by triangle in order."""
    n = td.n
    zf = td.Z.ravel()
    ax, ay = q * (T[:, 0] % n), q * (T[:, 0] // n)
    bx, by = q * (T[:, 1] % n), q * (T[:, 1] // n)
    cx, cy = q * (T[:, 2] % n), q * (T[:, 2] // n)
    D = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    flip = D < 0
    bx, cx = np.where(flip, cx, bx), np.where(flip, bx, cx)
    by, cy = np.where(flip, cy, by), np.where(flip, by, cy)
    D = np.abs(D)
    za = zf[T[:, 0]]
    zb = np.where(flip, zf[T[:, 2]], zf[T[:, 1]])
    zc = np.where(flip, zf[T[:, 1]], zf[T[:, 2]])
    x_lo = np.minimum(np.minimum(ax, bx), cx)
    x_hi = np.maximum(np.maximum(ax, bx), cx)
    y_lo = np.minimum(np.minimum(ay, by), cy)
    y_hi = np.maximum(np.maximum(ay, by), cy)
    # Pick's bound on the points a triangle holds, to size the chunks.
    est = D / 2 + np.hypot(bx - ax, by - ay) + np.hypot(cx - bx, cy - by) + np.hypot(ax - cx, ay - cy) + 3
    cum = np.cumsum(est)
    edges = ((ax, ay, bx, by), (bx, by, cx, cy), (cx, cy, ax, ay))
    a = 0
    while a < len(T):
        b = int(np.searchsorted(cum, (cum[a - 1] if a else 0) + CHUNK, "right"))
        b = max(b, a + 1)
        idx = np.arange(a, b)
        rep, local, _ = _expand(y_hi[idx] - y_lo[idx] + 1)
        t = idx[rep]
        y = y_lo[t] + local
        lo = x_lo[t].copy()
        hi = x_hi[t].copy()
        for (x1, y1, x2, y2) in edges:
            # Inside where (x2 - x1)(y - y1) - (y2 - y1)(x - x1) >= 0: beta x + gamma >= 0.
            beta = -(y2[t] - y1[t])
            gamma = (x2[t] - x1[t]) * (y - y1[t]) + (y2[t] - y1[t]) * x1[t]
            pos = beta > 0
            neg = beta < 0
            lo = np.where(pos, np.maximum(lo, -(gamma // np.where(pos, beta, 1))), lo)
            hi = np.where(neg, np.minimum(hi, gamma // np.where(neg, -beta, 1)), hi)
            hi = np.where((beta == 0) & (gamma < 0), lo - 1, hi)
        cnt = np.maximum(hi - lo + 1, 0)
        rep2, local2, _ = _expand(cnt)
        tt = t[rep2]
        px = lo[rep2] + local2
        py = y[rep2]
        e0 = (bx[tt] - ax[tt]) * (py - ay[tt]) - (by[tt] - ay[tt]) * (px - ax[tt])
        e1 = (cx[tt] - bx[tt]) * (py - by[tt]) - (cy[tt] - by[tt]) * (px - bx[tt])
        e2 = (ax[tt] - cx[tt]) * (py - cy[tt]) - (ay[tt] - cy[tt]) * (px - cx[tt])
        if (e0 < 0).any() or (e1 < 0).any() or (e2 < 0).any():
            raise RuntimeError("scanline produced a point outside its triangle")
        z = (e1 * za[tt] + e2 * zb[tt] + e0 * zc[tt]) / D[tt]
        yield tt, px, py, z
        a = b


def evaluate(td, T):
    """For each triangle (node indices): the largest ratio of error to bound
    over the half-node lattice samples it covers (edges included), and that
    sample's flat index. Also the number of samples with no reference (bugs)."""
    S = td.S
    Rf = td.R.ravel()
    Tf = td.T.ravel()
    worst = np.full(len(T), -1.0)
    worst_at = np.zeros(len(T), np.int64)
    nan_hits = 0
    for tt, px, py, z in scan(td, T, 2):
        s = py * S + px
        ref = Rf[s]
        bad = np.isnan(ref)
        nan_hits += int(bad.sum())
        ratio = np.where(bad, -1.0, np.abs(z - ref) / Tf[s])
        first_t = int(tt[0])
        k = tt - first_t
        cnt = np.bincount(k)
        if (cnt == 0).any():
            raise RuntimeError("a triangle covers no lattice point")
        starts = np.cumsum(cnt) - cnt
        mx = np.maximum.reduceat(ratio, starts)
        at = np.where(ratio == np.repeat(mx, cnt), np.arange(len(ratio)), len(ratio))
        first = np.minimum.reduceat(at, starts)
        worst[first_t:first_t + len(cnt)] = mx
        worst_at[first_t:first_t + len(cnt)] = s[first]
    return worst, worst_at, nan_hits


def plane_at(td, T, nodes):
    """Each triangle's plane, extended, at one node per triangle."""
    n = td.n
    zf = td.Z.ravel()
    P = [(T[:, k] % n, T[:, k] // n) for k in range(3)]
    px, py = nodes % n, nodes // n
    (ax, ay), (bx, by), (cx, cy) = P
    D = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    e0 = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    e1 = (cx - bx) * (py - by) - (cy - by) * (px - bx)
    e2 = (ax - cx) * (py - cy) - (ay - cy) * (px - cx)
    return (e1 * zf[T[:, 0]] + e2 * zf[T[:, 1]] + e0 * zf[T[:, 2]]) / D


def choose(td, T, s, vmask, forbidden):
    """For failing triangles and their worst samples, the node to insert: the
    sample itself if it is a node, else the corner of its edge or cell that is
    not yet a vertex and lies furthest from the triangle's plane. Returns
    (allowed choice or -1, forbidden choice or -1)."""
    n, S = td.n, td.S
    sx, sy = s % S, s // S
    cx0, cy0 = sx // 2, sy // 2
    ox, oy = sx & 1, sy & 1
    cand = np.full((len(T), 4), -1, np.int64)
    for k, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        ok = (dx <= ox) & (dy <= oy)
        c = np.minimum(cx0 + dx, n - 1)
        r = np.minimum(cy0 + dy, n - 1)
        cand[:, k] = np.where(ok, r * n + c, -1)
    flat_ok = cand >= 0
    cf = np.where(flat_ok, cand, 0)
    usable = flat_ok & td.V.ravel()[cf] & ~vmask[cf]
    score = np.zeros(cand.shape)
    for k in range(4):
        pz = plane_at(td, T, cf[:, k])
        tol = td.tol[2 * (cf[:, k] // n), 2 * (cf[:, k] % n)]
        score[:, k] = np.abs(pz - td.Z.ravel()[cf[:, k]]) / tol
    forb = forbidden[cf]
    allowed = usable & ~forb
    sa = np.where(allowed, score, -1.0)
    ka = np.argmax(sa, 1)
    pick = np.where(sa[np.arange(len(T)), ka] >= 0, cf[np.arange(len(T)), ka], -1)
    sf = np.where(usable & forb, score, -1.0)
    kf = np.argmax(sf, 1)
    want = np.where((pick < 0) & (sf[np.arange(len(T)), kf] >= 0), cf[np.arange(len(T)), kf], -1)
    return pick, want


def refine(td, start, forbidden):
    """Greedy insertion from the `start` vertex mask until every triangle in the
    region holds its tolerance. Returns (vertex mask, triangles in the region,
    border nodes it wanted but may not have, stats)."""
    n = td.n
    vmask = start.copy() & td.V.ravel()
    cons = td.cons
    prev_keys = np.zeros(0, np.int64)
    prev_worst = np.zeros(0)
    prev_at = np.zeros(0, np.int64)
    rounds = 0
    nan_total = 0
    wants = np.zeros(0, np.int64)
    t_cdt = t_eval = 0.0
    while True:
        rounds += 1
        nodes = np.flatnonzero(vmask)
        t0 = time.time()
        T = triangulate(nodes, n, cons)
        T = T[td.in_region(T)]
        t_cdt += time.time() - t0
        t0 = time.time()
        srt = np.sort(T, 1)
        keys = (srt[:, 0] << 36) | (srt[:, 1] << 18) | srt[:, 2]
        worst = np.zeros(len(T))
        at = np.zeros(len(T), np.int64)
        if len(prev_keys):
            idx = np.searchsorted(prev_keys, keys)
            idx = np.minimum(idx, len(prev_keys) - 1)
            hit = prev_keys[idx] == keys
        else:
            hit = np.zeros(len(T), bool)
            idx = np.zeros(len(T), np.int64)
        worst[hit] = prev_worst[idx[hit]]
        at[hit] = prev_at[idx[hit]]
        new = ~hit
        if new.any():
            w, a, nh = evaluate(td, T[new])
            worst[new] = w
            at[new] = a
            nan_total += nh
        order = np.argsort(keys)
        prev_keys, prev_worst, prev_at = keys[order], worst[order], at[order]
        t_eval += time.time() - t0
        fail = worst > 1.0 + RATIO_EPS
        if not fail.any():
            wants = np.zeros(0, np.int64)
            break
        pick, want = choose(td, T[fail], at[fail], vmask, forbidden)
        add = np.unique(pick[pick >= 0])
        wants = np.unique(want[(pick < 0) & (want >= 0)])
        if len(add) == 0:
            break
        vmask[add] = True
    stats = {"rounds": rounds, "vertices": int(vmask.sum()), "triangles": int(len(T)),
             "unfixed_triangles": int(fail.sum()) if fail.any() else 0, "nan_samples": nan_total,
             "seconds_triangulate": round(t_cdt, 2), "seconds_measure": round(t_eval, 2)}
    return vmask, T, wants, stats


# --- borders ------------------------------------------------------------------

def line_close(z, tol_nodes, tol_mids, positions):
    """Refine a border line's vertex positions in one dimension until every
    segment holds the tolerance at the nodes and midpoints between its ends.
    `z` is the line's heights (NaN where no ground)."""
    pos = sorted(set(int(p) for p in positions if np.isfinite(z[p])))
    while True:
        add = []
        for p, q in zip(pos[:-1], pos[1:]):
            if q - p < 2 or not np.isfinite(z[p:q + 1]).all():
                continue
            k = np.arange(p, q + 1)
            chord = z[p] + (z[q] - z[p]) * (k - p) / (q - p)
            dn = chord - z[p:q + 1]
            en = np.abs(dn) / tol_nodes[p:q + 1]
            em = np.abs((dn[:-1] + dn[1:]) / 2) / tol_mids[p:q]
            if max(en.max(), em.max()) <= 1.0 + RATIO_EPS:
                continue
            if en.max() >= em.max():
                add.append(p + int(np.argmax(en)))
            else:
                m = int(np.argmax(em))
                add.append(p + m + (1 if en[m + 1] > en[m] else 0))
        add = [a for a in add if a not in pos]
        if not add:
            return pos
        pos = sorted(set(pos) | set(add))


# --- the ground the generator still holds -------------------------------------
#
# The grid's ground stops where the bake found none of the master's: up to a
# cell short of the road corridor's outline, the tunnel lids' and the anchors',
# because a triangle with a NaN corner is dropped; and where the master's shore
# wall stood under the corridor's edge, the grid's cell runs down from the edge
# to the shelf. Two derived steps close both, and never write `height/`:
#
# - **Stitch.** Where a held body's open edge (its collider's, from the faces
#   dump; or, for a closed solid, the master's old edge along it, `holes.json`'s
#   `meets`) lies wholly outside the grid's region and within `STITCH_REACH` of
#   the region's edge, a band of triangles joins the region's boundary nodes to
#   the held edge's own vertices, so the ground meets it exactly as the master
#   did. Band vertices are the only ones off the grid's nodes.
# - **Carve.** First, a node lying more than `CARVE_MARGIN` under the road
#   corridor or the tunnel lids, the lowest of their surfaces over it, is
#   dropped (`height/` keeps it): the master's buried floors under the road on the
#   north coast and its ground under the fills, which no 2 m grid can raise to a
#   road edge standing on an 80 m cut, are hidden under held ground anyway. What
#   the plan's Stage 1 notes say the build does: "drops only the cells that lie
#   wholly under held ground by more than a margin". Then the held edge lies in
#   a gap, and the stitch closes it exactly. Nothing above held ground is ever
#   touched, so the hill over the tunnels stands; nothing under the anchors'
#   solids is carved.

STITCH_REACH = 3.0
CARVE_MARGIN = 0.30
CARVE_UNDER = ("terrain_road_corridor", "terrain_tunnel_lids")

# The open sea's edge. The bake's last node with ground is up to a cell inland
# of where the master ran its coasts on down under the water, so the grid's
# outer edge could end in the air: a ledge seen from the sea (the city's
# beaches, the south-east ridges, the south massif, the east coast). Every
# no-data node of the open sea (a no-data region reaching the grid's border or
# touching ground at sea level, so never a hill lake's or a pinhole's) beside
# a node with ground above
# SKIRT_FROM takes SKIRT_Y, in the build only: the ground runs on down to the
# shelf's own floor, the deepest the bake reads anywhere (-16 m, under 8.5 m of
# water), so a skirt's foot is no shallower than any shelf's outer edge and the
# clear shallow water shows no lip; Stage 4's seabed will bury it. Never beside
# held ground (under it, or within SKIRT_HELD_CLEAR of a held edge): the seam
# meets that. Never in the developed park's zone (its envelope plus 45 m).
SKIRT_Y = -16.0
SKIRT_FROM = -6.5
SKIRT_HELD_CLEAR = 6.0
HELD_CELL = 4.0


class Held:
    """The held colliders' faces and open edges (`tools/_ground_faces_dump.gd`'s
    `held.f32`, `held_open.f32`, `faces.json`) and `holes.json`'s meets, with a
    plan index of the faces flatter than `_top`'s cut."""

    def __init__(self, folder):
        fj = json.load(open(os.path.join(folder, "faces.json")))
        F = np.fromfile(os.path.join(folder, "held.f32"), "<f4").reshape(-1, 3, 3)
        E = np.fromfile(os.path.join(folder, "held_open.f32"), "<f4").reshape(-1, 2, 3)
        piece = np.zeros(len(F), np.int64)
        kinds = []
        for i, p in enumerate(fj["held"]):
            piece[p["first"]:p["first"] + p["count"]] = i
            kinds.append(p["kind"])
        holes = json.load(open(os.path.join(SRC, "holes.json")))
        meets = np.array([s for m in holes["meets"] for s in m["segments"]], np.float64).reshape(-1, 2, 3)
        segs = np.concatenate([E.astype(np.float64), meets])
        plan = np.hypot(segs[:, 1, 0] - segs[:, 0, 0], segs[:, 1, 2] - segs[:, 0, 2])
        segs = segs[plan > 1e-3]
        # One copy of an edge two pieces share.
        a = np.round(segs[:, 0], 4)
        b = np.round(segs[:, 1], 4)
        swap = (a[:, 0] > b[:, 0]) | ((a[:, 0] == b[:, 0]) & (a[:, 2] > b[:, 2]))
        lo = np.where(swap[:, None], b, a)
        hi = np.where(swap[:, None], a, b)
        _, first = np.unique(np.concatenate([lo, hi], 1), axis=0, return_index=True)
        self.segs = segs[np.sort(first)]
        h = hashlib.sha256()
        for name in ("held.f32", "held_open.f32", "faces.json"):
            h.update(open(os.path.join(folder, name), "rb").read())
        h.update(json.dumps(holes["meets"], sort_keys=True).encode())
        self.sha = h.hexdigest()
        F = F.astype(np.float64)
        n = np.cross(F[:, 1] - F[:, 0], F[:, 2] - F[:, 0])
        keep = np.abs(n[:, 1]) >= 0.05 * np.linalg.norm(n, axis=1)
        self.F = F[keep]
        self.fpiece = piece[keep]
        self.fsheet = np.array([kinds[p] == "body" for p in self.fpiece], bool)
        names = [p["name"] for p in fj["held"]]
        self.fcarve = np.array([names[p].endswith(CARVE_UNDER) for p in self.fpiece], bool)
        self.npieces = len(kinds)
        X, Z = self.F[:, :, 0], self.F[:, :, 2]
        B = HELD_CELL
        self.ox, self.oz = float(X.min()) - B, float(Z.min()) - B
        self.nbx = int((X.max() - self.ox) // B) + 2
        self.nbz = int((Z.max() - self.oz) // B) + 2
        bx0 = ((X.min(1) - self.ox) // B).astype(np.int64)
        bx1 = ((X.max(1) - self.ox) // B).astype(np.int64)
        bz0 = ((Z.min(1) - self.oz) // B).astype(np.int64)
        bz1 = ((Z.max(1) - self.oz) // B).astype(np.int64)
        w = bx1 - bx0 + 1
        rep, local, _ = _expand(w * (bz1 - bz0 + 1))
        keys = (bz0[rep] + local // w[rep]) * self.nbx + bx0[rep] + local % w[rep]
        order = np.argsort(keys, kind="stable")
        self.reg = rep[order]
        self.start = np.searchsorted(keys[order], np.arange(self.nbx * self.nbz + 1))

    def hits(self, px, pz):
        """Every (point, face, height) where a face lies over a plan point."""
        px = np.asarray(px, np.float64)
        pz = np.asarray(pz, np.float64)
        bx = ((px - self.ox) // HELD_CELL).astype(np.int64)
        bz = ((pz - self.oz) // HELD_CELL).astype(np.int64)
        ok = (bx >= 0) & (bx < self.nbx) & (bz >= 0) & (bz < self.nbz)
        key = np.where(ok, bz * self.nbx + bx, 0)
        s = self.start[key]
        cnt = np.where(ok, self.start[key + 1] - s, 0)
        rep, local, _ = _expand(cnt)
        f = self.reg[s[rep] + local]
        A, Bv, C = self.F[f, 0], self.F[f, 1], self.F[f, 2]
        qx, qz = px[rep], pz[rep]
        d = (Bv[:, 0] - A[:, 0]) * (C[:, 2] - A[:, 2]) - (Bv[:, 2] - A[:, 2]) * (C[:, 0] - A[:, 0])
        w1 = ((qx - A[:, 0]) * (C[:, 2] - A[:, 2]) - (qz - A[:, 2]) * (C[:, 0] - A[:, 0])) / d
        w2 = ((Bv[:, 0] - A[:, 0]) * (qz - A[:, 2]) - (Bv[:, 2] - A[:, 2]) * (qx - A[:, 0])) / d
        inside = (w1 >= -1e-9) & (w2 >= -1e-9) & (w1 + w2 <= 1 + 1e-9)
        y = A[:, 1] + w1 * (Bv[:, 1] - A[:, 1]) + w2 * (C[:, 1] - A[:, 1])
        return rep[inside], f[inside], y[inside]

    def surfaces(self, px, pz):
        """Per plan point: the lowest held surface over it (a sheet's any face, a
        solid's top), the highest, and whether any stands over it at all."""
        n = len(px)
        pi, f, y = self.hits(px, pz)
        low = np.full(n, np.inf)
        high = np.full(n, -np.inf)
        sh = self.fsheet[f]
        np.minimum.at(low, pi[sh], y[sh])
        np.maximum.at(high, pi[sh], y[sh])
        if (~sh).any():
            k = pi[~sh] * self.npieces + self.fpiece[f[~sh]]
            uk, inv = np.unique(k, return_inverse=True)
            top = np.full(len(uk), -np.inf)
            np.maximum.at(top, inv, y[~sh])
            np.minimum.at(low, uk // self.npieces, top)
            np.maximum.at(high, uk // self.npieces, top)
        anyh = np.isfinite(low)
        return np.where(anyh, low, np.nan), np.where(anyh, high, np.nan), anyh

    def faces_sha(self, xa, za, xb, zb):
        """The faces and edges over a plan box, hashed: what a tile's seam reads."""
        X, Z = self.F[:, :, 0], self.F[:, :, 2]
        m = (X.max(1) >= xa) & (X.min(1) <= xb) & (Z.max(1) >= za) & (Z.min(1) <= zb)
        S = self.segs
        k = (np.maximum(S[:, 0, 0], S[:, 1, 0]) >= xa) & (np.minimum(S[:, 0, 0], S[:, 1, 0]) <= xb) & \
            (np.maximum(S[:, 0, 2], S[:, 1, 2]) >= za) & (np.minimum(S[:, 0, 2], S[:, 1, 2]) <= zb)
        return hashlib.sha256(self.F[m].tobytes() + self.fsheet[m].tobytes() + S[k].tobytes()).hexdigest()


def held_dump(folder=None):
    """The held faces: from `folder`, or dumped now by a headless Godot run of
    `tools/_ground_faces_dump.gd` into a temporary folder."""
    if folder:
        return Held(folder), folder
    tmp = tempfile.mkdtemp(prefix="ground_build_held_")
    r = subprocess.run([GODOT, "--headless", "--path", ROOT, "--script", "res://tools/_ground_faces_dump.gd",
                        "--", "--out=" + tmp], capture_output=True, text=True, timeout=600)
    if not os.path.exists(os.path.join(tmp, "held.f32")):
        raise SystemExit("ground_build: the held faces dump wrote nothing:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    held = Held(tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    return held, "dumped by Godot"


def carve_under_held(M, held, grid):
    """`M` without the nodes lying more than CARVE_MARGIN under the corridor or
    the lids (the lowest of their surfaces over the node), and what was done."""
    nz, nx = M.shape
    F = held.F[held.fcarve]
    X, Z, Y = F[:, :, 0], F[:, :, 2], F[:, :, 1]
    c0 = np.ceil((X.min(1) - grid.x0) / grid.step).astype(np.int64)
    c1 = np.floor((X.max(1) - grid.x0) / grid.step).astype(np.int64)
    r0 = np.ceil((Z.min(1) - grid.z0) / grid.step).astype(np.int64)
    r1 = np.floor((Z.max(1) - grid.z0) / grid.step).astype(np.int64)
    c0, r0 = np.maximum(c0, 0), np.maximum(r0, 0)
    c1, r1 = np.minimum(c1, nx - 1), np.minimum(r1, nz - 1)
    w = np.maximum(c1 - c0 + 1, 0)
    hgt = np.maximum(r1 - r0 + 1, 0)
    low = np.full(nz * nx, np.inf)
    rep, local, _ = _expand(w * hgt)
    for a in range(0, len(rep), 4_000_000):
        f = rep[a:a + 4_000_000]
        lc = local[a:a + 4_000_000]
        c = c0[f] + lc % w[f]
        r = r0[f] + lc // w[f]
        px = grid.x0 + grid.step * c
        pz = grid.z0 + grid.step * r
        A, B, C = F[f, 0], F[f, 1], F[f, 2]
        d = (B[:, 0] - A[:, 0]) * (C[:, 2] - A[:, 2]) - (B[:, 2] - A[:, 2]) * (C[:, 0] - A[:, 0])
        w1 = ((px - A[:, 0]) * (C[:, 2] - A[:, 2]) - (pz - A[:, 2]) * (C[:, 0] - A[:, 0])) / d
        w2 = ((B[:, 0] - A[:, 0]) * (pz - A[:, 2]) - (B[:, 2] - A[:, 2]) * (px - A[:, 0])) / d
        ins = (w1 >= -1e-9) & (w2 >= -1e-9) & (w1 + w2 <= 1 + 1e-9)
        y = A[:, 1] + w1 * (B[:, 1] - A[:, 1]) + w2 * (C[:, 1] - A[:, 1])
        np.minimum.at(low, (r * nx + c)[ins], y[ins])
    low = low.reshape(nz, nx)
    drop = np.isfinite(M) & np.isfinite(low) & (M < low - CARVE_MARGIN)
    # Ground standing over the corridor or the lids (the hill over the tunnels)
    # keeps the ring of nodes round it, so it runs on into them as it always
    # did instead of ending in a new edge over the road.
    above = np.isfinite(M) & np.isfinite(low) & (M > low)
    ring = above.copy()
    ring[1:, :] |= above[:-1, :]
    ring[:-1, :] |= above[1:, :]
    ring[:, 1:] |= ring[:, :-1].copy()
    ring[:, :-1] |= ring[:, 1:].copy()
    near_hill = drop & ring
    drop &= ~ring
    out = M.copy()
    out[drop] = np.nan
    under = np.isfinite(M) & np.isfinite(low)
    stats = {"nodes_under_corridor_or_lids": int(under.sum()), "nodes_carved": int(drop.sum()),
             "nodes_kept_within_margin": int((under & ~drop & (M <= low)).sum()),
             "nodes_above_held_kept": int((under & (M > low)).sum()),
             "nodes_kept_beside_them": int(near_hill.sum())}
    return out, drop, stats


def open_sea(M):
    """The open sea's no-data: every region of no-data nodes (4-way connected;
    rows' runs joined by union-find) that reaches the grid's own border or
    touches ground at sea level (below SKIRT_FROM), so the gaps between a
    coast's end and its shelf count, and a hill lake's or a pinhole's do not."""
    N = ~np.isfinite(M)
    nz, nx = N.shape
    starts, ends = [], []
    for r in range(nz):
        d = np.diff(np.concatenate([[0], N[r].astype(np.int8), [0]]))
        starts.append(np.flatnonzero(d == 1))
        ends.append(np.flatnonzero(d == -1) - 1)
    off = np.cumsum([0] + [len(x) for x in starts])
    parent = list(range(int(off[-1])))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for r in range(nz - 1):
        s1, e1, s2, e2 = starts[r], ends[r], starts[r + 1], ends[r + 1]
        if not len(s1) or not len(s2):
            continue
        lo = np.searchsorted(e2, s1, "left")
        hi = np.searchsorted(s2, e1, "right")
        for i in range(len(s1)):
            for j in range(int(lo[i]), int(hi[i])):
                a, b = find(int(off[r] + i)), find(int(off[r + 1] + j))
                if a != b:
                    parent[max(a, b)] = min(a, b)
    label = np.full((nz, nx), -1, np.int64)
    for r in range(nz):
        for i in range(len(starts[r])):
            label[r, starts[r][i]:ends[r][i] + 1] = find(int(off[r] + i))
    sea = np.zeros(int(off[-1]), bool)
    for r in range(nz):
        for i in range(len(starts[r])):
            if r == 0 or r == nz - 1 or starts[r][i] == 0 or ends[r][i] == nx - 1:
                sea[find(int(off[r] + i))] = True
    low = np.isfinite(M) & (M < SKIRT_FROM)
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a = low[max(dr, 0):nz + min(dr, 0), max(dc, 0):nx + min(dc, 0)]
        b = label[max(-dr, 0):nz + min(-dr, 0), max(-dc, 0):nx + min(-dc, 0)]
        sea[np.unique(b[a & (b >= 0)])] = True
    return (label >= 0) & sea[np.maximum(label, 0)]


def skirt_open_sea(M, held, grid, park):
    """`M` with the open sea's first ring of no-data nodes, beside ground above
    SKIRT_FROM, set to SKIRT_Y (see above), and what was done."""
    V = np.isfinite(M)
    sea = open_sea(M)
    high = V & (M > SKIRT_FROM)
    near = high.copy()
    near[1:, :] |= high[:-1, :]
    near[:-1, :] |= high[1:, :]
    near[:, 1:] |= near[:, :-1].copy()
    near[:, :-1] |= near[:, 1:].copy()
    ring = sea & near
    # Never in the developed park (its zone: the envelope plus 45 m), where the
    # open cut by the west shell is no-data reaching the sea and a wall dropped
    # into it blocks route B (footprint_walk_test, 2026-10-14).
    xs = grid.x0 + grid.step * np.arange(M.shape[1])
    zs = grid.z0 + grid.step * np.arange(M.shape[0])
    in_park = ((zs >= park[1]) & (zs <= park[3]))[:, None] & ((xs >= park[0]) & (xs <= park[2]))[None, :]
    park_kept = int((ring & in_park).sum())
    ring &= ~in_park
    # Not beside held ground: under it, or near a held edge.
    rr, cc = np.nonzero(ring)
    if held is not None and len(rr):
        _, _, anyh = held.surfaces(grid.x0 + grid.step * cc, grid.z0 + grid.step * rr)
        clear = ~anyh
        mark = np.zeros(M.shape, bool)
        S = held.segs
        L = np.hypot(S[:, 1, 0] - S[:, 0, 0], S[:, 1, 2] - S[:, 0, 2])
        ns = np.maximum(2, np.ceil(L / 1.0).astype(np.int64) + 1)
        rep, local, _ = _expand(ns)
        t = local / (ns[rep] - 1)
        px = S[rep, 0, 0] + t * (S[rep, 1, 0] - S[rep, 0, 0])
        pz = S[rep, 0, 2] + t * (S[rep, 1, 2] - S[rep, 0, 2])
        ci = np.clip(np.rint((px - grid.x0) / grid.step).astype(np.int64), 0, M.shape[1] - 1)
        ri = np.clip(np.rint((pz - grid.z0) / grid.step).astype(np.int64), 0, M.shape[0] - 1)
        mark[ri, ci] = True
        for _ in range(int(np.ceil(SKIRT_HELD_CLEAR / grid.step))):
            m2 = mark.copy()
            m2[1:, :] |= mark[:-1, :]
            m2[:-1, :] |= mark[1:, :]
            m2[:, 1:] |= mark[:, :-1]
            m2[:, :-1] |= mark[:, 1:]
            mark = m2
        clear &= ~mark[rr, cc]
        ring[rr[~clear], cc[~clear]] = False
    out = M.copy()
    out[ring] = np.float32(SKIRT_Y)
    stats = {"skirt_nodes": int(ring.sum()), "kept_out_of_the_park": park_kept,
             "open_sea_nodes": int(sea.sum()), "skirt_y_m": SKIRT_Y,
             "beside_ground_above_m": SKIRT_FROM}
    return out, ring, stats


def stitch_pieces(world, held):
    """The held edges the grid is stitched to, split at the tile lines: per tile,
    an (k, 2, 3) array of world segments. An edge qualifies when no point of it
    lies in the grid's region and some lies within STITCH_REACH of a node on the
    region's edge."""
    g = world.grid
    M = world.mosaic
    S = held.segs
    V = np.isfinite(M)
    P = np.pad(V, 1, constant_values=False)
    edge = np.zeros_like(V)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            edge |= ~P[1 + dr:1 + dr + V.shape[0], 1 + dc:1 + dc + V.shape[1]]
    edge &= V
    reach = int(np.ceil(STITCH_REACH / g.step))
    near = edge.copy()
    for _ in range(reach):
        m = near.copy()
        m[1:, :] |= near[:-1, :]
        m[:-1, :] |= near[1:, :]
        m[:, 1:] |= near[:, :-1]
        m[:, :-1] |= near[:, 1:]
        near = m
    L = np.hypot(S[:, 1, 0] - S[:, 0, 0], S[:, 1, 2] - S[:, 0, 2])
    ns = np.maximum(2, np.ceil(L / 0.25).astype(np.int64) + 1)
    rep, local, _ = _expand(ns)
    t = local / (ns[rep] - 1)
    px = S[rep, 0, 0] + t * (S[rep, 1, 0] - S[rep, 0, 0])
    pz = S[rep, 0, 2] + t * (S[rep, 1, 2] - S[rep, 0, 2])
    cf = (px - g.x0) / g.step
    rf = (pz - g.z0) / g.step
    inside = world_in_region(world, cf, rf)
    ci = np.clip(np.rint(cf).astype(np.int64), 0, M.shape[1] - 1)
    ri = np.clip(np.rint(rf).astype(np.int64), 0, M.shape[0] - 1)
    close = near[ri, ci]
    any_in = np.zeros(len(S), bool)
    np.logical_or.at(any_in, rep, inside)
    any_close = np.zeros(len(S), bool)
    np.logical_or.at(any_close, rep, close)
    keep = S[~any_in & any_close]
    # Split at the tile lines, computing each crossing once, in world metres.
    out = {}
    tm = g.tile_m
    for a, b in zip(keep[:, 0], keep[:, 1]):
        ts = [0.0, 1.0]
        for axis in (0, 2):
            lo, hi = sorted((a[axis], b[axis]))
            for k in range(int(np.floor(lo / tm)) + 1, int(np.ceil(hi / tm))):
                ts.append((k * tm - a[axis]) / (b[axis] - a[axis]))
        ts = sorted(set(ts))
        pts = []
        for tv in ts:
            p = a + tv * (b - a)
            for axis in (0, 2):
                k = np.rint(p[axis] / tm)
                if abs(p[axis] - k * tm) < 1e-6:
                    p[axis] = k * tm
            pts.append(p)
        for p, q in zip(pts[:-1], pts[1:]):
            if np.hypot(q[0] - p[0], q[2] - p[2]) < 1e-3:
                continue
            m = (p + q) / 2
            tkey = (int(np.floor(m[0] / tm)), int(np.floor(m[2] / tm)))
            out.setdefault(tkey, []).append(np.stack([p, q]))
    return {k: np.array(v) for k, v in out.items()}, int(len(keep)), float(L[~any_in & any_close].sum())


def _cross2(ax, az, bx, bz):
    return ax * bz - az * bx


def _proper_cross(p, q, A, B):
    """Whether segment p-q crosses each segment A-B properly (not at a shared end)."""
    d1 = _cross2(q[0] - p[0], q[1] - p[1], A[:, 0] - p[0], A[:, 1] - p[1])
    d2 = _cross2(q[0] - p[0], q[1] - p[1], B[:, 0] - p[0], B[:, 1] - p[1])
    d3 = _cross2(B[:, 0] - A[:, 0], B[:, 1] - A[:, 1], p[0] - A[:, 0], p[1] - A[:, 1])
    d4 = _cross2(B[:, 0] - A[:, 0], B[:, 1] - A[:, 1], q[0] - A[:, 0], q[1] - A[:, 1])
    eps = 1e-9
    return (((d1 > eps) & (d2 < -eps)) | ((d1 < -eps) & (d2 > eps))) & \
           (((d3 > eps) & (d4 < -eps)) | ((d3 < -eps) & (d4 > eps)))


def band_tile(world, t, td, held, pieces, vmask):
    """The stitch band of one tile: vertices (world metres, float64) and
    triangles indexing nodes (0 .. n*n-1) or band vertices (n*n + k). `vmask`
    is the tile's grid mesh's vertices: on a tile line the band takes its points
    from them (the line's shared set) and the pieces' crossings, and judges
    nearness by the held edges of this tile and its neighbours, so the two
    tiles of a line draw the same segments along it."""
    if pieces is None or not len(pieces):
        return None
    n = td.n
    h = world.grid.step
    x0, z0 = td.x0, td.z0
    cons = td.cons
    near = [world.pieces[u] for u in ((t[0] + i, t[1] + j) for i in (-1, 0, 1) for j in (-1, 0, 1))
            if u in world.pieces]
    near = np.concatenate(near)
    line = np.zeros(n * n, bool)
    for side in SIDES:
        line[td.border_nodes(side)] = True
    cn = np.unique(np.concatenate([cons.ravel(), np.flatnonzero(line & vmask)]))
    nx_, nz_ = x0 + h * (cn % n), z0 + h * (cn // n)
    # Nodes of the region's edge near a piece, and the region's edges near one.
    dmin = np.full(len(cn), np.inf)
    for p, q in zip(near[:, 0], near[:, 1]):
        dx, dz = q[0] - p[0], q[2] - p[2]
        tt = np.clip(((nx_ - p[0]) * dx + (nz_ - p[2]) * dz) / (dx * dx + dz * dz), 0, 1)
        dmin = np.minimum(dmin, np.hypot(nx_ - p[0] - tt * dx, nz_ - p[2] - tt * dz))
    sel_nodes = cn[dmin <= STITCH_REACH + 0.5]
    wide = cn[dmin <= 3 * STITCH_REACH]
    wset = np.zeros(n * n, bool)
    wset[wide] = True
    ce = cons[wset[cons[:, 0]] & wset[cons[:, 1]]]
    nodes = np.unique(np.concatenate([sel_nodes, ce.ravel()]))
    # Drop pieces that cross a region edge or each other: they would need a
    # vertex of their own on it.
    A = np.stack([x0 + h * (ce[:, 0] % n), z0 + h * (ce[:, 0] // n)], 1)
    B = np.stack([x0 + h * (ce[:, 1] % n), z0 + h * (ce[:, 1] // n)], 1)
    P2 = pieces[:, :, [0, 2]]
    ok = np.ones(len(pieces), bool)
    for i in range(len(pieces)):
        p, q = P2[i, 0], P2[i, 1]
        if len(A) and _proper_cross(p, q, A, B).any():
            ok[i] = False
            continue
        if _proper_cross(p, q, P2[:, 0], P2[:, 1]).any():
            ok[i] = False
    pieces = pieces[ok]
    # Edges stacked in plan (a lid's over the road's at a portal; a wall's top
    # over its foot) are a tunnel or a wall, not a seam to stitch: leave them.
    ends2 = np.round(pieces[:, :, [0, 2]].reshape(-1, 2), 4)
    _, kinv = np.unique(ends2, axis=0, return_inverse=True)
    kinv = kinv.ravel()
    ylo = np.full(kinv.max() + 1 if len(kinv) else 0, np.inf)
    yhi = np.full(len(ylo), -np.inf)
    ys = pieces[:, :, 1].ravel()
    np.minimum.at(ylo, kinv, ys)
    np.maximum.at(yhi, kinv, ys)
    stacked = (yhi - ylo > 1e-4)[kinv].reshape(-1, 2).any(1)
    pieces = pieces[~stacked]
    for attempt in range(6):
        if not len(pieces):
            return None
        res = _band_cdt(world, t, td, held, pieces, nodes, ce)
        if isinstance(res, dict) or res is None:
            return res
        pieces = pieces[res]
    raise RuntimeError("tile %s: the stitch band's triangulation keeps merging vertices" % tile_name(*t))


def _band_cdt(world, t, td, held, pieces, nodes, ce):
    """One try at the band: its triangles, or a mask of the pieces to keep when
    the triangulation merged points (pieces touching a merged point dropped)."""
    from mathutils.geometry import delaunay_2d_cdt
    n = td.n
    h = world.grid.step
    x0, z0 = td.x0, td.z0
    # The band's points: the pieces' ends (deduplicated exactly) and the nodes.
    ends = pieces.reshape(-1, 3)
    uniq, inv = np.unique(np.round(ends, 6), axis=0, return_inverse=True)
    inv = inv.ravel()
    first = np.zeros(len(uniq), np.int64)
    first[inv[::-1]] = np.arange(len(inv))[::-1]
    bverts = ends[first]
    node_xz = np.stack([h * (nodes % n), h * (nodes // n)], 1).astype(np.float64)
    pts = np.concatenate([np.stack([bverts[:, 0] - x0, bverts[:, 2] - z0], 1), node_xz])
    # A piece's end on a node: the node stands for it.
    nb = len(bverts)
    pos_of_node = {int(k): nb + i for i, k in enumerate(nodes.tolist())}
    key_xz = {}
    for i, (x, z) in enumerate(node_xz.tolist()):
        key_xz[(round(x, 6), round(z, 6))] = nb + i
    alias = np.arange(len(pts))
    for i in range(nb):
        k = (round(pts[i, 0], 6), round(pts[i, 1], 6))
        if k in key_xz:
            alias[i] = key_xz[k]
    seg_idx = alias[inv.reshape(-1, 2)]
    cons_idx = np.array([[pos_of_node[int(a)], pos_of_node[int(b)]] for a, b in ce], np.int64).reshape(-1, 2)
    edges = np.concatenate([seg_idx, cons_idx])
    edges = edges[edges[:, 0] != edges[:, 1]]
    live = np.unique(np.concatenate([alias, np.arange(nb, len(pts))]))
    remap = np.full(len(pts), -1, np.int64)
    remap[live] = np.arange(len(live))
    out = delaunay_2d_cdt([tuple(p) for p in pts[live].tolist()], remap[edges].tolist(), [], 0, 1e-7, True)
    if len(out[0]) != len(live) or any(len(o) != 1 for o in out[3]):
        bad = set()
        keep = np.ones(len(pieces), bool)
        for v, o in zip(out[0], out[3]):
            if len(o) > 1:
                bad.update(int(live[k]) for k in o)
            elif not o:
                # A vertex of its own where two constraints cross: drop the
                # pieces that pass within a centimetre of it.
                px, pz = v[0] + x0, v[1] + z0
                a2, b2 = pieces[:, 0][:, [0, 2]], pieces[:, 1][:, [0, 2]]
                d2 = b2 - a2
                tt = np.clip(((px - a2[:, 0]) * d2[:, 0] + (pz - a2[:, 1]) * d2[:, 1]) / (d2 ** 2).sum(1), 0, 1)
                keep &= np.hypot(px - a2[:, 0] - tt * d2[:, 0], pz - a2[:, 1] - tt * d2[:, 1]) > 0.01
        piece_pts = alias[inv.reshape(-1, 2)]
        keep &= ~np.isin(piece_pts, sorted(bad)).any(1)
        if keep.all():
            raise RuntimeError("tile %s: the stitch band's triangulation changed its points" % tile_name(*t))
        return keep
    orig = np.array([o[0] for o in out[3]], np.int64)
    tri = live[orig[np.array(out[2], np.int64).reshape(-1, 3)]]
    # World plan positions and heights of every band point.
    Wx = np.concatenate([bverts[:, 0], x0 + node_xz[:, 0]])
    Wz = np.concatenate([bverts[:, 2], z0 + node_xz[:, 1]])
    Wy = np.concatenate([bverts[:, 1], td.H.ravel()[nodes].astype(np.float64)])
    tx_, tz_ = Wx[tri], Wz[tri]
    # Keep a triangle that lies outside the region and the held bodies, and
    # spans no more than a band does.
    cx, cz = tx_.mean(1), tz_.mean(1)
    span = np.max(np.hypot(tx_ - np.roll(tx_, 1, 1), tz_ - np.roll(tz_, 1, 1)), 1)
    area = 0.5 * np.abs((tx_[:, 1] - tx_[:, 0]) * (tz_[:, 2] - tz_[:, 0]) - (tz_[:, 1] - tz_[:, 0]) * (tx_[:, 2] - tx_[:, 0]))
    g = world.grid
    keep = (span <= 2 * STITCH_REACH) & (area > 1e-6) & (tri < nb).any(1)
    keep &= ~world_in_region(world, (cx - g.x0) / g.step, (cz - g.z0) / g.step)
    for k in range(3):
        sx = (2 * cx + tx_[:, k]) / 3
        sz = (2 * cz + tz_[:, k]) / 3
        _, _, anyh = held.surfaces(np.concatenate([cx, sx]), np.concatenate([cz, sz]))
        keep &= ~anyh[:len(cx)] & ~anyh[len(cx):]
    tri = tri[keep]
    if not len(tri):
        return None
    # Index: nodes by node id, the rest after n*n.
    is_node = tri >= nb
    node_ids = np.where(is_node, nodes[np.clip(tri - nb, 0, len(nodes) - 1)], -1)
    used_b = np.unique(tri[~is_node])
    bmap = np.full(nb, -1, np.int64)
    bmap[used_b] = np.arange(len(used_b))
    ids = np.where(is_node, node_ids, n * n + bmap[np.clip(tri, 0, nb - 1)])
    return {"verts": np.stack([Wx[used_b], Wy[used_b], Wz[used_b]], 1), "tris": ids,
            "pieces": int(len(pieces)), "length_m": float(np.hypot(*(pieces[:, 1] - pieces[:, 0])[:, [0, 2]].T).sum())}


# --- the build ----------------------------------------------------------------

class World:
    def __init__(self, out_dir, held_dir=None, seam=True):
        gb = _bake()
        self.gb = gb
        self.grid = gb.Grid(os.path.join(SRC, "grid.json"))
        g = self.grid
        self.spec = g.spec
        if "tolerance_zones" not in self.spec:
            raise SystemExit("ground_build: grid.json has no tolerance_zones; run with --write-zones first")
        self.zones = Zones(self.spec["tolerance_zones"])
        self.raw, bad = gb.read_tiles(os.path.join(SRC, "height"), g)
        if bad:
            raise SystemExit("ground_build: %d shared-edge nodes differ between height tiles" % bad)
        self.mosaic = self.raw
        self.exr_sha = {}
        for tx, tz in g.tiles():
            self.exr_sha[(tx, tz)] = sha_file(os.path.join(SRC, "height", g.name(tx, tz)))
        self.held = None
        self.pieces = {}
        self.seam = {"applied": False}
        if seam:
            self.held, src = held_dump(held_dir)
            self.mosaic, self.carved, cs = carve_under_held(self.raw, self.held, g)
            self.mosaic, self.skirt, ks = skirt_open_sea(self.mosaic, self.held, g, self.zones.rect)
            self.pieces, ns, ln = stitch_pieces(self, self.held)
            self.seam = {"applied": True, "held": src, "held_sha256": self.held.sha,
                         "held_edges": int(len(self.held.segs)), "stitched_edges": ns, "stitched_m": round(ln, 1),
                         "carve": cs, "skirt": ks,
                         "rules": {"stitch_reach_m": STITCH_REACH, "carve_margin_m": CARVE_MARGIN,
                                   "carve_under": list(CARVE_UNDER), "skirt_y_m": SKIRT_Y,
                                   "skirt_beside_ground_above_m": SKIRT_FROM,
                                   "skirt_held_clear_m": SKIRT_HELD_CLEAR}}
        # What each tile's mesh reads of the heights: the stored ones, raised.
        self.tile_sha = {}
        for tx, tz in g.tiles():
            rows, cols = g.window(tx, tz)
            self.tile_sha[(tx, tz)] = hashlib.sha256(np.ascontiguousarray(self.mosaic[rows, cols]).tobytes()).hexdigest()
        self.out = out_dir
        self.n = g.n
        self.tiles = []
        for tx, tz in g.tiles():
            rows, cols = g.window(tx, tz)
            H = self.mosaic[rows, cols]
            V = np.isfinite(H)
            # A tile holds ground when some full-grid triangle has three nodes.
            nv = V[:-1, :-1].astype(np.int8) + V[:-1, 1:] + V[1:, :-1] + V[1:, 1:]
            if (nv >= 3).any():
                self.tiles.append((tx, tz))
        self.tileset = set(self.tiles)

    def heights(self, t):
        rows, cols = self.grid.window(*t)
        return self.mosaic[rows, cols]

    def neighbour(self, t, side):
        dx, dz = STEP[side]
        u = (t[0] + dx, t[1] + dz)
        return u if u in self.tileset else None

    def tiledata(self, t):
        return TileData(t[0], t[1], self.heights(t), self.zones, self.grid.step, self.grid.tile_m)

    def line(self, t, side):
        """A border line's heights and its tolerances at nodes and midpoints."""
        td_n = self.n
        H = self.heights(t)
        x0, z0 = self.grid.tile_m * t[0], self.grid.tile_m * t[1]
        h = self.grid.step
        k = np.arange(2 * td_n - 1) * h / 2
        if side in ("n", "s"):
            z = H[0 if side == "n" else -1, :].astype(np.float64)
            zid = self.zones.grid(x0 + k, [z0 + (0 if side == "n" else self.grid.tile_m)])[0]
        else:
            z = H[:, 0 if side == "w" else -1].astype(np.float64)
            zid = self.zones.grid([x0 + (0 if side == "w" else self.grid.tile_m)], z0 + k)[:, 0]
        tol = self.zones.tol[zid]
        return z, tol[0::2], tol[1::2]

    def normals(self, t):
        """Per-node normals of a tile in Godot axes, from the whole mosaic."""
        g = self.grid
        rows, cols = g.window(*t)
        r0, c0 = rows.start, cols.start
        M = self.mosaic
        n = self.n
        ra = max(r0 - 1, 0)
        rb = min(r0 + n + 1, M.shape[0])
        ca = max(c0 - 1, 0)
        cb = min(c0 + n + 1, M.shape[1])
        W = np.full((n + 2, n + 2), np.nan)
        W[ra - r0 + 1:rb - r0 + 1, ca - c0 + 1:cb - c0 + 1] = M[ra:rb, ca:cb]
        C = W[1:-1, 1:-1]
        L, Rt = W[1:-1, :-2], W[1:-1, 2:]
        U, Dn = W[:-2, 1:-1], W[2:, 1:-1]
        h = g.step

        def diff(lo, hi):
            both = np.isfinite(lo) & np.isfinite(hi)
            only_hi = ~np.isfinite(lo) & np.isfinite(hi)
            only_lo = np.isfinite(lo) & ~np.isfinite(hi)
            with np.errstate(invalid="ignore"):
                return np.where(both, (hi - lo) / (2 * h),
                                np.where(only_hi, (hi - C) / h, np.where(only_lo, (C - lo) / h, 0.0)))

        dx = diff(L, Rt)
        dz = diff(U, Dn)
        N = np.stack([-dx, np.ones_like(dx), -dz], -1)
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        return N

    def normal_near(self, xw, zw):
        """A stitch vertex's normal: the grid's at the nearest node with ground,
        the same whichever tile asks."""
        g = self.grid
        M = self.mosaic
        out = np.zeros((len(xw), 3))
        for i, (x, z) in enumerate(zip(xw, zw)):
            c = int(np.rint((x - g.x0) / g.step))
            r = int(np.rint((z - g.z0) / g.step))
            best = None
            for rad in range(0, 5):
                for dr in range(-rad, rad + 1):
                    for dc in range(-rad, rad + 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < M.shape[0] and 0 <= cc < M.shape[1] and np.isfinite(M[rr, cc]):
                            d = (g.x0 + g.step * cc - x) ** 2 + (g.z0 + g.step * rr - z) ** 2
                            if best is None or d < best[0] or (d == best[0] and (rr, cc) < best[1]):
                                best = (d, (rr, cc))
                if best is not None:
                    break
            if best is None:
                out[i] = (0.0, 1.0, 0.0)
                continue
            rr, cc = best[1]
            hgt = M[rr, cc]

            def at(a, b):
                return M[a, b] if 0 <= a < M.shape[0] and 0 <= b < M.shape[1] and np.isfinite(M[a, b]) else np.nan

            def diff(lo, hi):
                if np.isfinite(lo) and np.isfinite(hi):
                    return (hi - lo) / (2 * g.step)
                if np.isfinite(hi):
                    return (hi - hgt) / g.step
                if np.isfinite(lo):
                    return (hgt - lo) / g.step
                return 0.0
            dx = diff(at(rr, cc - 1), at(rr, cc + 1))
            dz = diff(at(rr - 1, cc), at(rr + 1, cc))
            v = np.array([-dx, 1.0, -dz])
            out[i] = v / np.linalg.norm(v)
        return out


def build_tile_mesh(world, t, td, T, band=None):
    """Vertices (Godot axes, tile-local), triangles facing up, normals, UVs;
    the stitch band's triangles after the grid's."""
    n = td.n
    BT = band["tris"] if band is not None else np.zeros((0, 3), np.int64)
    used = np.unique(np.concatenate([T.ravel(), BT[BT < n * n]]))
    remap = np.full(n * n, -1, np.int64)
    remap[used] = np.arange(len(used))
    c = used % n
    r = used // n
    h = world.grid.step
    pos = np.stack([c * h, td.H.ravel()[used].astype(np.float64), r * h], 1)
    N = world.normals(t).reshape(-1, 3)[used]
    # `delaunay_2d_cdt` returns its triangles counter-clockwise in the plane it
    # was given, (c, r) = (x/2, z/2) for the grid and (x, z) for the band.
    # Godot's axes are right-handed with y up, so seen from above x runs right
    # and z runs down the page: a triangle counter-clockwise in (x, z) has
    # (b - a) x (c - a) pointing down (y < 0). glTF's front is counter-clockwise
    # about the normal, so every triangle is reversed once here to face up; the
    # check below proves the rule held.
    tris = remap[T][:, ::-1]
    nb = 0
    if band is not None:
        bv = band["verts"]
        nb = len(bv)
        pos = np.concatenate([pos, bv - np.array([td.x0, 0.0, td.z0])])
        N = np.concatenate([N, world.normal_near(bv[:, 0], bv[:, 2])])
        bt = np.where(BT < n * n, remap[np.clip(BT, 0, n * n - 1)], len(used) + BT - n * n)
        tris = np.concatenate([tris, bt[:, ::-1]])
    pos = pos.astype(np.float32)
    P = pos.astype(np.float64)
    a, b, cc = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    ny = (b[:, 2] - a[:, 2]) * (cc[:, 0] - a[:, 0]) - (b[:, 0] - a[:, 0]) * (cc[:, 2] - a[:, 2])
    if (ny <= 0).any():
        raise RuntimeError("tile %s: %d triangles do not face up in Godot's axes" % (tile_name(*t), int((ny <= 0).sum())))
    uv = (P[:, [0, 2]] / world.grid.tile_m).astype(np.float32)
    return {"pos": pos, "tris": tris.astype(np.int64), "normals": N.astype(np.float32), "uv": uv, "nodes": used,
            "band_vertices": nb, "band_triangles": int(len(BT))}


def export_glb(mesh, t, x0, z0, path):
    import bpy
    name = "ground_%s" % tile_name(*t)
    pos = mesh["pos"]
    # Blender: (x, -z, y).
    bverts = np.stack([pos[:, 0], -pos[:, 2], pos[:, 1]], 1)
    # Godot (x, y, z) -> Blender (x, -z, y) is a rotation about x (determinant
    # +1), not a mirror, so a triangle keeps its order: up in Godot is up here,
    # and the exporter's rotation back keeps it up in glTF.
    btris = mesh["tris"]
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(bverts))
    me.vertices.foreach_set("co", bverts.astype(np.float32).ravel())
    me.loops.add(3 * len(btris))
    me.loops.foreach_set("vertex_index", btris.astype(np.int32).ravel())
    me.polygons.add(len(btris))
    me.polygons.foreach_set("loop_start", np.arange(0, 3 * len(btris), 3, dtype=np.int32))
    me.update(calc_edges=True)
    if me.validate(verbose=False):
        raise RuntimeError("%s: Blender changed the mesh while validating it" % name)
    up = np.empty(len(me.polygons) * 3, np.float32)
    me.polygons.foreach_get("normal", up)
    if (up.reshape(-1, 3)[:, 2] <= 0).any():
        raise RuntimeError("%s: a face points down in Blender" % name)
    me.shade_smooth()
    nb = mesh["normals"]
    attr = me.attributes.new("custom_normal", "FLOAT_VECTOR", "POINT")
    attr.data.foreach_set("vector", np.stack([nb[:, 0], -nb[:, 2], nb[:, 1]], 1).astype(np.float32).ravel())
    uvl = me.uv_layers.new(name="UVMap")
    uv = mesh["uv"].copy()
    uv[:, 1] = 1.0 - uv[:, 1]
    uvl.data.foreach_set("uv", uv[btris.ravel()].astype(np.float32).ravel())
    obj = bpy.data.objects.new(name + "-col", me)
    obj.location = (x0, -z0, 0.0)
    scene = bpy.context.scene
    scene.collection.objects.link(obj)
    for o in scene.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    tmp = path + ".part.glb"
    bpy.ops.export_scene.gltf(
        filepath=tmp, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
        export_animations=False, export_cameras=False, export_lights=False, export_materials="NONE",
        export_normals=True, export_texcoords=True, export_tangents=False, export_skins=False,
        export_morph=False, export_extras=False, export_vertex_color="NONE", export_attributes=False)
    os.replace(tmp, path)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(me)


def zone_counts(td, mesh):
    """Triangles by the zone at their centroid."""
    P = mesh["pos"].astype(np.float64)
    tr = mesh["tris"]
    cen = P[tr].mean(1)
    sx = np.clip(np.rint(cen[:, 0]).astype(np.int64), 0, td.S - 1)
    sz = np.clip(np.rint(cen[:, 2]).astype(np.int64), 0, td.S - 1)
    z = td.zid[sz, sx]
    return {Zones.NAMES[k]: int((z == k).sum()) for k in range(3)}


def run_build(args):
    import bpy
    t_start = time.time()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    done = os.path.join(out, "BUILD_DONE")
    if os.path.exists(done):
        os.remove(done)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    world = World(out, args.held, not args.no_seam)
    if world.seam["applied"]:
        log("seam: %d held edges (%s); %d stitched, %.0f m; carve %s" % (
            world.seam["held_edges"], world.seam["held"], world.seam["stitched_edges"], world.seam["stitched_m"],
            world.seam["carve"]))
    log("%d tiles hold ground of %d; zones %s" % (len(world.tiles), len(list(world.grid.tiles())), world.zones.sha[:12]))
    man_path = os.path.join(out, "manifest.json")
    manifest = {} if args.force or not os.path.exists(man_path) else json.load(open(man_path))
    m_tiles = manifest.get("tiles", {})
    m_p1 = manifest.get("phase1", {})
    m_aug = {} if args.force else manifest.get("augmentations", {})
    if args.tiles == "all":
        wanted = set(world.tiles)
    else:
        wanted = set()
        for s in args.tiles.split(","):
            s = s.strip()
            tx, tz = s.split("_")
            t = (int(tx[1:]), int(tz[1:]))
            if t not in world.tileset:
                raise SystemExit("ground_build: %s holds no ground" % s)
            wanted.add(t)

    # Phase 1: each tile on its own, borders free, for its border requests.
    p1 = {}
    t1 = time.time()
    p1_built = 0
    for t in world.tiles:
        key = sha_json([world.tile_sha[t], world.zones.sha, CORE_VERSION, "phase1"])
        cached = m_p1.get(tile_name(*t))
        if cached and cached.get("key") == key and not args.force:
            p1[t] = cached
            continue
        td = world.tiledata(t)
        start = td.required.copy()
        vmask, T, _, st = refine(td, start, np.zeros(td.n * td.n, bool))
        req = {}
        for side in SIDES:
            nodes = td.border_nodes(side)
            req[side] = [int(k) for k in np.flatnonzero(vmask[nodes])]
        p1[t] = {"key": key, "requests": req, "stats": st}
        p1_built += 1
        log("phase 1 %s: %d rounds, %d vertices, %d triangles, %.1f s (triangulate %.1f, measure %.1f)" % (
            tile_name(*t), st["rounds"], st["vertices"], st["triangles"],
            st["seconds_triangulate"] + st["seconds_measure"], st["seconds_triangulate"], st["seconds_measure"]))
    t1 = time.time() - t1

    # The shared lines: union of both sides' requests, closed in one dimension.
    def edge_key(t, side):
        u = world.neighbour(t, side)
        if u is None:
            return None
        lo, hi = sorted([(t, side), (u, OPPOSITE[side])])
        return "%s:%s|%s:%s" % (tile_name(*lo[0]), lo[1], tile_name(*hi[0]), hi[1])

    def border_set(t, side):
        u = world.neighbour(t, side)
        if u is None:
            return None
        k = edge_key(t, side)
        pos = set(p1[t]["requests"][side]) | set(p1[u]["requests"][OPPOSITE[side]]) | set(m_aug.get(k, []))
        z, tn, tm = world.line(t, side)
        return line_close(z, tn, tm, pos)

    borders = {}
    for t in world.tiles:
        for side in SIDES:
            borders[(t, side)] = border_set(t, side)

    def outside_line(t, side):
        """The heights one node beyond a side, all a tile's normals read of its
        neighbour (central differences at its border nodes)."""
        rows, cols = world.grid.window(*t)
        M = world.mosaic
        r0, r1, c0, c1 = rows.start, rows.stop, cols.start, cols.stop
        sl = {"n": (r0 - 1, slice(c0, c1)), "s": (r1, slice(c0, c1)),
              "w": (slice(r0, r1), c0 - 1), "e": (slice(r0, r1), c1)}[side]
        k = sl[0] if side in ("n", "s") else sl[1]
        if k < 0 or k >= (M.shape[0] if side in ("n", "s") else M.shape[1]):
            return None
        return hashlib.sha256(np.ascontiguousarray(M[sl]).tobytes()).hexdigest()

    def input_hash(t):
        parts = [world.tile_sha[t]]
        if world.held is not None:
            x0, z0 = world.grid.tile_m * t[0], world.grid.tile_m * t[1]
            parts.append(world.held.faces_sha(x0 - 10, z0 - 10, x0 + world.grid.tile_m + 10, z0 + world.grid.tile_m + 10))
            pc = world.pieces.get(t)
            parts.append(hashlib.sha256(pc.tobytes()).hexdigest() if pc is not None else None)
        for side in SIDES:
            parts.append(outside_line(t, side))
            parts.append(borders[(t, side)])
        return sha_json(parts + [world.zones.sha, CORE_VERSION, EXPORT_VERSION])

    # Which tiles to build: those asked for whose inputs changed (or all, forced),
    # and any neighbour whose shared line changed with them.
    todo = set()
    for t in world.tiles:
        prev = m_tiles.get(tile_name(*t))
        glb = os.path.join(out, tile_name(*t) + ".glb")
        stale = (args.force or prev is None or prev.get("input_hash") != input_hash(t)
                 or not os.path.exists(glb) or prev.get("glb_sha256") != sha_file(glb))
        if t in wanted and stale:
            todo.add(t)
    for t in list(todo):
        for side in SIDES:
            u = world.neighbour(t, side)
            if u is None or u in todo:
                continue
            prev = m_tiles.get(tile_name(*u))
            if not os.path.exists(os.path.join(out, tile_name(*u) + ".glb")):
                continue  # never written: nothing on disk to crack against
            if prev is None or prev.get("input_hash") != input_hash(u):
                if u not in wanted:
                    log("also building %s: its line with %s changed" % (tile_name(*u), tile_name(*t)))
                todo.add(u)

    # Phase 2: each tile with its border sets fixed; augment where it must.
    results = {}
    augmented = {}
    t2 = time.time()
    queue = sorted(todo)
    while queue:
        again = set()
        for t in queue:
            td = world.tiledata(t)
            start = td.required.copy()
            forbidden = np.zeros(td.n * td.n, bool)
            for side in SIDES:
                b = borders[(t, side)]
                if b is None:
                    continue
                nodes = td.border_nodes(side)
                start[nodes[b]] = True
                f = np.ones(td.n, bool)
                f[b] = False
                forbidden[nodes[f]] = True
            vmask, T, wants, st = refine(td, start, forbidden)
            results[t] = (td, vmask, T, st)
            log("phase 2 %s: %d rounds, %d vertices, %d triangles, %.1f s%s" % (
                tile_name(*t), st["rounds"], st["vertices"], st["triangles"],
                st["seconds_triangulate"] + st["seconds_measure"],
                ("; wants %d border nodes" % len(wants)) if len(wants) else ""))
            for k in wants:
                c, r = int(k % td.n), int(k // td.n)
                for side in SIDES:
                    p = {"n": c if r == 0 else None, "s": c if r == td.n - 1 else None,
                         "w": r if c == 0 else None, "e": r if c == td.n - 1 else None}[side]
                    if p is None or borders[(t, side)] is None:
                        continue
                    ek = edge_key(t, side)
                    m_aug.setdefault(ek, [])
                    if p not in m_aug[ek]:
                        m_aug[ek].append(p)
                        augmented[ek] = augmented.get(ek, 0) + 1
                    u = world.neighbour(t, side)
                    borders[(t, side)] = border_set(t, side)
                    borders[(u, OPPOSITE[side])] = border_set(u, OPPOSITE[side])
                    again.add(t)
                    again.add(u)
        queue = sorted(again)
    t2 = time.time() - t2

    # Write.
    t3 = time.time()
    m_tiles_new = dict(m_tiles) if not args.force else {}
    for t in sorted(results):
        td, vmask, T, st = results[t]
        if st["unfixed_triangles"]:
            raise SystemExit("ground_build: %s left %d triangles out of tolerance" % (tile_name(*t), st["unfixed_triangles"]))
        if st["nan_samples"]:
            raise SystemExit("ground_build: %s measured %d samples with no reference" % (tile_name(*t), st["nan_samples"]))
        band = band_tile(world, t, td, world.held, world.pieces.get(t), vmask) if world.held is not None else None
        mesh = build_tile_mesh(world, t, td, T, band)
        path = os.path.join(out, tile_name(*t) + ".glb")
        export_glb(mesh, t, td.x0, td.z0, path)
        imp = path + ".import"
        if not os.path.exists(imp):
            with open(imp, "w") as f:
                f.write(IMPORT_FILE)
        m_tiles_new[tile_name(*t)] = {
            "input_hash": input_hash(t), "glb": os.path.basename(path), "glb_sha256": sha_file(path),
            "glb_bytes": os.path.getsize(path), "height_sha256": world.exr_sha[t],
            "vertices": int(len(mesh["pos"])), "triangles": int(len(mesh["tris"])),
            "stitch_band": {"triangles": mesh["band_triangles"], "vertices": mesh["band_vertices"],
                            "pieces": band["pieces"] if band else 0, "length_m": round(band["length_m"], 1) if band else 0.0},
            "triangles_by_zone": zone_counts(td, mesh),
            "y_range": [float(mesh["pos"][:, 1].min()), float(mesh["pos"][:, 1].max())],
            "build": {"rounds": st["rounds"], "seconds": round(st["seconds_triangulate"] + st["seconds_measure"], 2)},
        }
    # Tiles that no longer hold ground lose their files.
    for f in sorted(os.listdir(out)):
        if f.endswith(".glb") and f[:-4] not in {tile_name(*t) for t in world.tiles}:
            os.remove(os.path.join(out, f))
            if os.path.exists(os.path.join(out, f + ".import")):
                os.remove(os.path.join(out, f + ".import"))
            m_tiles_new.pop(f[:-4], None)
            log("removed %s: the tile holds no ground" % f)
    t3 = time.time() - t3
    missing = [tile_name(*t) for t in world.tiles if tile_name(*t) not in m_tiles_new
               or not os.path.exists(os.path.join(out, tile_name(*t) + ".glb"))]
    manifest = {
        "about": "tools/blender/ground_build.py's record: per tile, the hash of every input its mesh is "
                 "a function of; a tile whose hash and GLB match is not built again.",
        "core_version": CORE_VERSION, "export_version": EXPORT_VERSION,
        "grid": "assets/source/world_ground/grid.json", "zones_sha256": world.zones.sha,
        "tolerances_m": dict(zip(Zones.NAMES, world.zones.tol.tolist())),
        "seam": world.seam,
        "tiles": {k: m_tiles_new[k] for k in sorted(m_tiles_new)},
        "phase1": {tile_name(*t): {"key": p1[t]["key"], "requests": p1[t]["requests"]} for t in sorted(p1)},
        "borders": {edge_key(t, s): borders[(t, s)] for t in sorted(world.tiles) for s in SIDES
                    if borders[(t, s)] is not None and (t, s) == min((t, s), (world.neighbour(t, s), OPPOSITE[s]))},
        "augmentations": {k: sorted(v) for k, v in sorted(m_aug.items()) if v},
        "totals": {"tiles": len(m_tiles_new), "triangles": sum(v["triangles"] for v in m_tiles_new.values()),
                   "vertices": sum(v["vertices"] for v in m_tiles_new.values()),
                   "triangles_by_zone": {z: sum(v["triangles_by_zone"][z] for v in m_tiles_new.values())
                                         for z in Zones.NAMES},
                   "glb_bytes": sum(v["glb_bytes"] for v in m_tiles_new.values())},
        "last_build": {"tiles_built": sorted(tile_name(*t) for t in results), "phase1_built": p1_built,
                       "augmented_lines": augmented, "seconds": {"phase1": round(t1, 1), "phase2": round(t2, 1),
                                                                  "export": round(t3, 1),
                                                                  "total": round(time.time() - t_start, 1)}},
    }
    # Nothing built and nothing removed: leave the record as it is, so a build
    # that changes nothing changes no file.
    old = json.load(open(man_path)) if os.path.exists(man_path) else None
    if old is not None and not results and {k: v for k, v in old.items() if k != "last_build"} == \
            {k: v for k, v in manifest.items() if k != "last_build"}:
        manifest = old
    else:
        tmp = man_path + ".part"
        with open(tmp, "w") as f:
            json.dump(manifest, f, indent=1)
            f.write("\n")
        os.replace(tmp, man_path)
    if missing:
        log("not every tile is written (%s); BUILD_DONE withheld" % ", ".join(missing))
    elif args.no_done:
        log("every tile is written; BUILD_DONE left for the caller (--no-done)")
    else:
        open(done, "w").close()
    log("built %d tiles (phase 1 %d) in %.1f s: phase 1 %.1f, phase 2 %.1f, export %.1f; %d triangles in all; "
        "augmented lines %d" % (len(results), p1_built, time.time() - t_start, t1, t2, t3,
                                manifest["totals"]["triangles"], len(augmented)))
    return manifest


# --- reading a tile GLB back ---------------------------------------------------

def read_glb(path):
    """The one mesh of a tile GLB: node name and translation, positions,
    normals, UVs and triangles, as stored."""
    buf = open(path, "rb").read()
    magic, version, length = struct.unpack_from("<III", buf, 0)
    if magic != 0x46546C67 or version != 2:
        raise ValueError("%s is not a glTF 2 binary" % path)
    p = 12
    js = binb = None
    while p < length:
        clen, ctype = struct.unpack_from("<II", buf, p)
        data = buf[p + 8:p + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(data.decode())
        elif ctype == 0x004E4942:
            binb = data
        p += 8 + clen
    comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}

    def accessor(i):
        a = js["accessors"][i]
        bv = js["bufferViews"][a["bufferView"]]
        dt = np.dtype(comp[a["componentType"]]).newbyteorder("<")
        k = width[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 0) or dt.itemsize * k
        raw = np.frombuffer(binb, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * k, offset=off)
        if stride == dt.itemsize * k:
            return np.frombuffer(raw.tobytes(), dt).reshape(a["count"], k)
        return np.stack([np.frombuffer(raw[i * stride:i * stride + dt.itemsize * k].tobytes(), dt)
                         for i in range(a["count"])])

    if len(js["meshes"]) != 1 or len(js["meshes"][0]["primitives"]) != 1:
        raise ValueError("%s: want one mesh of one primitive" % path)
    prim = js["meshes"][0]["primitives"][0]
    nodes = [nd for nd in js["nodes"] if "mesh" in nd]
    node = nodes[0]
    out = {"name": node.get("name"), "translation": node.get("translation", [0, 0, 0]),
           "rotation": node.get("rotation"), "scale": node.get("scale"), "nodes": len(js["nodes"]),
           "pos": accessor(prim["attributes"]["POSITION"]),
           "normal": accessor(prim["attributes"]["NORMAL"]) if "NORMAL" in prim["attributes"] else None,
           "uv": accessor(prim["attributes"]["TEXCOORD_0"]) if "TEXCOORD_0" in prim["attributes"] else None,
           "tris": accessor(prim["indices"]).astype(np.int64).reshape(-1, 3),
           "mode": prim.get("mode", 4), "material": prim.get("material")}
    return out


# --- proofs -------------------------------------------------------------------

def run_prove(args, world=None):
    """Measure the written GLBs (read back by `read_glb`)."""
    t0 = time.time()
    out = os.path.abspath(args.out)
    world = world or World(out, args.held, not args.no_seam)
    n = world.n
    h = world.grid.step
    g = world.grid
    rep = {"tiles": {}, "zones": {z: {} for z in Zones.NAMES}}
    zmax = {z: {"node": 0.0, "edge_midpoint": 0.0, "centre": 0.0, "quarter": 0.0,
                "excess_over_tolerance": -1.0, "centres_floor_over_tolerance": 0, "centre_floor_max": 0.0,
                "triangles": 0} for z in Zones.NAMES}
    border_normals = {}
    normal_mismatch = 0
    faces_down = 0
    band_tris = 0
    band_verts = 0
    raised_verts = 0
    skirt_verts = 0
    uv_err = 0.0
    world_pts = []
    world_tris = []
    is_grid_vertex = []
    offset = 0
    total_tris = 0
    for t in world.tiles:
        path = os.path.join(out, tile_name(*t) + ".glb")
        if not os.path.exists(path):
            rep["tiles"][tile_name(*t)] = {"missing": True}
            continue
        m = read_glb(path)
        td = world.tiledata(t)
        x0, z0 = td.x0, td.z0
        P = m["pos"].astype(np.float64)
        tr = m["tris"]
        # Every face up in Godot's axes (glTF's counter-clockwise front).
        a, b, c = P[tr[:, 0]], P[tr[:, 1]], P[tr[:, 2]]
        nrm = np.cross(b - a, c - a)
        faces_down += int((nrm[:, 1] <= 0).sum())
        # A grid vertex stands on a node at the node's height (as raised); any
        # other is the stitch band's.
        cc = P[:, 0] / h
        rr = P[:, 2] / h
        ci = np.rint(cc).astype(np.int64)
        ri = np.rint(rr).astype(np.int64)
        on = (cc == ci) & (rr == ri) & (ci >= 0) & (ci < n) & (ri >= 0) & (ri < n)
        node = np.where(on, ri * n + ci, 0)
        on &= m["pos"][:, 1] == td.H.ravel()[node]
        rw = world.raw[g.window(*t)].ravel()
        raised_verts += int((on & np.isfinite(rw[node]) & (m["pos"][:, 1] != rw[node])).sum())  # must stay 0
        skirt_verts += int((on & ~np.isfinite(rw[node])).sum())
        band_verts += int((~on).sum())
        grid_t = on[tr].all(1)
        band_tris += int((~grid_t).sum())
        uv_err = max(uv_err, float(np.abs(m["uv"][:, 0] - P[:, 0] / g.tile_m).max()),
                     float(np.abs(m["uv"][:, 1] - P[:, 2] / g.tile_m).max()))
        T = node[tr[grid_t]]
        # Error against the (raised) bilinear grid on the half-node lattice; the
        # band has no grid under it and is counted apart.
        w, at, nan_hits = evaluate(td, T)
        stats = lattice_errors(td, T)
        zc = zone_counts(td, {"pos": m["pos"], "tris": tr})
        for z in Zones.NAMES:
            zmax[z]["triangles"] += zc[z]
            for k in ("node", "edge_midpoint", "centre", "quarter"):
                zmax[z][k] = max(zmax[z][k], stats[z][k])
            zmax[z]["excess_over_tolerance"] = max(zmax[z]["excess_over_tolerance"], stats[z]["excess"])
            zmax[z]["centres_floor_over_tolerance"] += stats[z]["floor_over"]
            zmax[z]["centre_floor_max"] = max(zmax[z]["centre_floor_max"], stats[z]["floor_max"])
        W = P + np.array([x0, 0.0, z0])
        world_pts.append(W)
        world_tris.append(tr + offset)
        is_grid_vertex.append(on)
        offset += len(W)
        # Normals shared across tiles must be equal.
        for k in np.flatnonzero((P[:, 0] == 0) | (P[:, 0] == g.tile_m) | (P[:, 2] == 0) | (P[:, 2] == g.tile_m)):
            key = tuple(W[k].tolist())
            v = tuple(m["normal"][k].tolist())
            if key in border_normals and border_normals[key] != v:
                normal_mismatch += 1
            border_normals.setdefault(key, v)
        total_tris += len(tr)
        rep["tiles"][tile_name(*t)] = {
            "triangles": int(len(tr)), "band_triangles": int((~grid_t).sum()), "vertices": int(len(P)),
            "triangles_by_zone": zc, "max_ratio": float(w.max()) if len(w) else 0.0, "nan_samples": nan_hits,
            "glb_bytes": os.path.getsize(path), "node_name": m["name"], "translation": m["translation"],
            "error_by_zone": {z: {k: round(stats[z][k], 4) for k in ("node", "edge_midpoint", "centre", "quarter")}
                              for z in Zones.NAMES if stats[z]["samples"]},
        }
    # The seams, by world position: every vertex once, every edge by its ends.
    WP = np.concatenate(world_pts)
    ON = np.concatenate(is_grid_vertex)
    uniq_p, vid = np.unique(WP, axis=0, return_inverse=True)
    vid = vid.ravel()
    TR = vid[np.concatenate(world_tris)]
    E = np.sort(np.concatenate([TR[:, [0, 1]], TR[:, [1, 2]], TR[:, [2, 0]]]), 1)
    key = E[:, 0] * len(uniq_p) + E[:, 1]
    uniq, cnt = np.unique(key, return_counts=True)
    single = uniq[cnt == 1]
    over = int((cnt > 2).sum())
    pa, pb = uniq_p[single // len(uniq_p)], uniq_p[single % len(uniq_p)]
    grid_of = np.zeros(len(uniq_p), bool)
    grid_of[vid[ON]] = True
    both_grid = grid_of[single // len(uniq_p)] & grid_of[single % len(uniq_p)]
    # Unpaired grid edges must lie on the data's edge: ground on one side only.
    mc = ((pa[:, 0] + pb[:, 0]) / 2 - g.x0) / h
    mr = ((pa[:, 2] + pb[:, 2]) / 2 - g.z0) / h
    dc, dr = (pb[:, 0] - pa[:, 0]) / h, (pb[:, 2] - pa[:, 2]) / h
    ln = np.hypot(dc, dr)
    oc, orr = -dr / ln * 0.01, dc / ln * 0.01
    side1 = world_in_region(world, mc + oc, mr + orr)
    side2 = world_in_region(world, mc - oc, mr - orr)
    cracks = int((both_grid & side1 & side2).sum())
    # Unpaired band edges: on a held edge (the stitch, as meant) or not.
    held_keys = set()
    for pcs in world.pieces.values():
        for p_, q_ in zip(pcs[:, 0], pcs[:, 1]):
            k1 = tuple(np.round(p_, 4).tolist())
            k2 = tuple(np.round(q_, 4).tolist())
            held_keys.add((k1, k2))
            held_keys.add((k2, k1))
    on_held = np.array([(tuple(np.round(x, 4).tolist()), tuple(np.round(y, 4).tolist())) in held_keys
                        for x, y in zip(pa, pb)], bool) if len(pa) else np.zeros(0, bool)
    # A T-junction: an unpaired edge whose midpoint lies on another unpaired
    # edge (one side drew the segment whole, the other in pieces).
    tj = 0
    if len(pa):
        mids = (pa + pb) / 2
        cell = np.floor(mids[:, [0, 2]] / 4.0).astype(np.int64)
        buckets = {}
        lo = np.floor(np.minimum(pa, pb)[:, [0, 2]] / 4.0).astype(np.int64)
        hi = np.floor(np.maximum(pa, pb)[:, [0, 2]] / 4.0).astype(np.int64)
        for i in range(len(pa)):
            for cx in range(lo[i, 0], hi[i, 0] + 1):
                for cz in range(lo[i, 1], hi[i, 1] + 1):
                    buckets.setdefault((cx, cz), []).append(i)
        for i in range(len(pa)):
            for j in buckets.get((cell[i, 0], cell[i, 1]), []):
                if j == i:
                    continue
                d = pb[j] - pa[j]
                tt = np.dot(mids[i] - pa[j], d) / np.dot(d, d)
                if 1e-9 < tt < 1 - 1e-9 and np.linalg.norm(pa[j] + tt * d - mids[i]) < 1e-4:
                    tj += 1
                    break
    rep["seams"] = {"edges": int(len(uniq)), "unpaired": int(len(single)), "t_junctions": tj,
                    "unpaired_grid_edges": int(both_grid.sum()), "unpaired_grid_inside_ground": cracks,
                    "unpaired_on_held_edges": int(on_held.sum()),
                    "unpaired_band_other": int((~both_grid & ~on_held).sum()),
                    "edges_used_more_than_twice": over, "shared_vertex_normals_differing": normal_mismatch}
    rep["faces_not_up"] = faces_down
    rep["band"] = {"triangles": band_tris, "vertices": band_verts}
    rep["vertices_off_stored_height"] = raised_verts
    rep["skirt_vertices"] = skirt_verts
    rep["uv_max_error"] = uv_err
    rep["zones"] = zmax
    rep["triangles"] = total_tris
    rep["seam"] = world.seam
    rep["seconds"] = round(time.time() - t0, 1)
    if args.prove:
        with open(args.prove, "w") as f:
            json.dump(rep, f, indent=1)
    log("prove: %d triangles (band %d); unpaired edges %d: grid %d (inside ground %d), on held edges %d, band other %d; "
        "T-junctions %d; faces not up %d; normals differing %d; %.1f s" % (
            total_tris, band_tris, len(single), int(both_grid.sum()), cracks, int(on_held.sum()),
            int((~both_grid & ~on_held).sum()), tj, faces_down, normal_mismatch, time.time() - t0))
    for z in Zones.NAMES:
        d = zmax[z]
        log("  %-9s tol %.2f: max error node %.4f, midpoint %.4f, centre %.4f, quarter-node %.4f; "
            "excess over bound %.2g; centres whose own floor beats the tolerance %d (largest %.3f m)" % (
                z, world.zones.tol[Zones.NAMES.index(z)], d["node"], d["edge_midpoint"], d["centre"], d["quarter"],
                d["excess_over_tolerance"], d["centres_floor_over_tolerance"], d["centre_floor_max"]))
    return rep


def world_in_region(world, c, r):
    """Whether global fractional node coordinates lie in the grid's region."""
    M = world.mosaic
    V = np.isfinite(M)
    ci = np.clip(np.floor(c).astype(np.int64), 0, M.shape[1] - 2)
    ri = np.clip(np.floor(r).astype(np.int64), 0, M.shape[0] - 2)
    u, v = c - ci, r - ri
    a, b, cc, d = V[ri, ci], V[ri, ci + 1], V[ri + 1, ci], V[ri + 1, ci + 1]
    nv = a.astype(np.int8) + b + cc + d
    inside = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    k = np.where(~a, 0, np.where(~b, 1, np.where(~cc, 2, 3)))
    half = np.where(k == 0, u + v > 1, np.where(k == 1, v > u, np.where(k == 2, u > v, u + v < 1)))
    return inside & ((nv == 4) | ((nv == 3) & half))


def lattice_errors(td, T):
    """Largest |mesh - bilinear grid| by zone at nodes, edge midpoints, cell
    centres and a quarter-node lattice; the largest excess over the bound; and
    the centres whose own floor exceeds the zone's tolerance."""
    n = td.n
    out = {z: {"node": 0.0, "edge_midpoint": 0.0, "centre": 0.0, "quarter": 0.0, "excess": -1.0,
               "floor_over": 0, "floor_max": 0.0, "samples": 0} for z in Zones.NAMES}
    Z = td.Z
    for q in (2, 4):  # samples per node spacing: half-node and quarter-node lattices
        for t, px, py, z in scan(td, T, q):
            if q == 2:
                S = td.S
                s = py * S + px
                ref = td.R.ravel()[s]
                err = np.abs(z - ref)
                bound = td.T.ravel()[s]
                zid = td.zid.ravel()[s]
                kind = np.where((px % 2 == 0) & (py % 2 == 0), 0, np.where((px % 2 == 1) & (py % 2 == 1), 2, 1))
                for zi, zn in enumerate(Zones.NAMES):
                    m = zid == zi
                    if not m.any():
                        continue
                    out[zn]["samples"] += int(m.sum())
                    for ki, kn in enumerate(("node", "edge_midpoint", "centre")):
                        mk = m & (kind == ki)
                        if mk.any():
                            out[zn][kn] = max(out[zn][kn], float(np.nanmax(err[mk])))
                    out[zn]["excess"] = max(out[zn]["excess"], float(np.nanmax(err[m] - bound[m])))
            else:
                # Bilinear (or, in a three-node cell, its triangle's plane) at quarter points.
                fc, fr = px / 4.0, py / 4.0
                ci = np.minimum((px // 4), n - 2)
                ri = np.minimum((py // 4), n - 2)
                u, v = fc - ci, fr - ri
                z00, z10 = Z[ri, ci], Z[ri, ci + 1]
                z01, z11 = Z[ri + 1, ci], Z[ri + 1, ci + 1]
                bil = z00 * (1 - u) * (1 - v) + z10 * u * (1 - v) + z01 * (1 - u) * v + z11 * u * v
                k3 = td.nanc[ri, ci]
                # Three-node cell: the plane of its three nodes.
                pl = np.where(k3 == 0, z10 + z01 - z11 + (z11 - z01) * u + (z11 - z10) * v,
                     np.where(k3 == 1, z00 + (z11 - z01) * u + (z01 - z00) * v,
                     np.where(k3 == 2, z00 + (z10 - z00) * u + (z11 - z10) * v,
                              z00 + (z10 - z00) * u + (z01 - z00) * v)))
                ref = np.where(td.c3[ri, ci], pl, bil)
                err = np.abs(z - ref)
                zid = td.zid[np.minimum(py // 2, td.S - 1), np.minimum(px // 2, td.S - 1)]
                for zi, zn in enumerate(Zones.NAMES):
                    m = (zid == zi) & np.isfinite(err)
                    if m.any():
                        out[zn]["quarter"] = max(out[zn]["quarter"], float(err[m].max()))
    # Centres where the cell's own floor is over the zone's tolerance.
    tolc = td.tol[1::2, 1::2]
    over = td.c4 & (td.floor > tolc)
    zc = td.zid[1::2, 1::2]
    for zi, zn in enumerate(Zones.NAMES):
        m = over & (zc == zi)
        out[zn]["floor_over"] = int(m.sum())
        out[zn]["floor_max"] = float(td.floor[m].max()) if m.any() else 0.0
    return out


# --- the census blend ------------------------------------------------------------

def run_census(args):
    import bpy
    out = os.path.abspath(args.out)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.data.collections.new("Ground")
    bpy.context.scene.collection.children.link(coll)
    names = sorted(f for f in os.listdir(out) if f.endswith(".glb"))
    tris = 0
    for f in names:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(out, f))
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            if o.type != "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
                continue
            o.data.transform(o.matrix_world)
            o.matrix_world.identity()
            o.name = o.name.replace("-col", "")
            o.data.name = o.name
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coll.objects.link(o)
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.census), compress=True)
    log("census blend %s: %d tiles, %d triangles, world coordinates in collection Ground" % (args.census, len(names), tris))


# --- zones from the project's own data ----------------------------------------

DUMP_GD = r'''extends SceneTree
## Written and run by tools/blender/ground_build.py --write-zones, then deleted.
const Plan = preload("res://scripts/park_plan.gd")

func _v2(a: Array) -> Array:
	var out: Array = []
	for p in a:
		if p is Vector3:
			out.append([p.x, p.z])
		else:
			out.append([p.x, p.y])
	return out

func _init() -> void:
	var out := {}
	out["highway"] = _v2(Plan.highway_path())
	out["approach_road"] = _v2(Plan.approach_road_points())
	out["front_road"] = _v2([Vector2(Plan.FRONT_ROAD_HALF_X, Plan.FRONT_ROAD_Z), Vector2(-Plan.FRONT_ROAD_HALF_X, Plan.FRONT_ROAD_Z)])
	var streets := {}
	for s in Plan.town_streets():
		streets[s["id"]] = _v2(s["points"])
	out["town_streets"] = streets
	out["north_town_outline"] = _v2(Plan.north_town_outline())
	out["beach_town_outline"] = _v2(Plan.BEACH_TOWN_OUTLINE)
	out["park_footprint"] = [Plan.REBUILD_FOOTPRINT_MIN_X, Plan.REBUILD_FOOTPRINT_MIN_Z, Plan.REBUILD_FOOTPRINT_MAX_X, Plan.REBUILD_FOOTPRINT_MAX_Z]
	var f := FileAccess.open(OS.get_cmdline_user_args()[0], FileAccess.WRITE)
	f.store_string(JSON.stringify(out))
	f.close()
	quit()
'''

CITY_RIBBONS = ["city_highway_extension", "bridge_main_deck", "bridge_city_southern_offramp",
                "southern_city_bypass_centreline", "southern_coastal_highway_extension_centreline"]
CITY_PADS = ["bridge_city_intersection"]
CITY_EXTENT = ("city_block_", "city_skyline_anchor_", "city_ferry_terminal")


def _r(v):
    return round(float(v), 2)


def _hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def run_write_zones(args):
    import bpy
    tmp = tempfile.mkdtemp(prefix="ground_build_zones_")
    try:
        gd = os.path.join(tmp, "dump_roads.gd")
        js = os.path.join(tmp, "roads.json")
        with open(gd, "w") as f:
            f.write(DUMP_GD)
        r = subprocess.run([GODOT, "--headless", "--path", ROOT, "--script", gd, "--", js],
                           capture_output=True, text=True, timeout=300)
        if not os.path.exists(js):
            raise SystemExit("ground_build: the Godot dump wrote nothing:\n" + r.stdout[-2000:] + r.stderr[-2000:])
        plan = json.load(open(js))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bpy.ops.wm.open_mainfile(filepath=CITY_BLEND)
    lines = {}
    lines["highway"] = plan["highway"]
    lines["approach_road"] = plan["approach_road"]
    lines["front_road"] = plan["front_road"]
    for k, v in sorted(plan["town_streets"].items()):
        lines[k] = v
    for name in CITY_RIBBONS:
        o = bpy.data.objects[name]
        mw = o.matrix_world
        co = [mw @ v.co for v in o.data.vertices]
        if name == "bridge_main_deck":
            # A box: its long axis, the mean of each end's four corners.
            xs = sorted(co, key=lambda v: v.x)
            ends = [xs[:4], xs[-4:]]
            pts = [[sum(v.x for v in e) / 4, -sum(v.y for v in e) / 4] for e in ends]
        else:
            # A ribbon: vertex pairs across the road, in order along it.
            pts = [[(co[i].x + co[i + 1].x) / 2, -(co[i].y + co[i + 1].y) / 2] for i in range(0, len(co) - 1, 2)]
            if len(co) % 2:
                pts.append([co[-1].x, -co[-1].y])
        lines[name] = pts
    for name in CITY_PADS:
        o = bpy.data.objects[name]
        mw = o.matrix_world
        pts = [[(mw @ v.co).x, -(mw @ v.co).y] for v in o.data.vertices]
        lines[name] = pts + [pts[0]]
    ext = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith(CITY_EXTENT):
            mw = o.matrix_world
            ext += [((mw @ v.co).x, -(mw @ v.co).y) for v in o.data.vertices]
    city = _hull([(_r(x), _r(z)) for x, z in ext])
    fx0, fz0, fx1, fz1 = plan["park_footprint"]
    zones = {
        "about": "Vertical tolerance of the ground's tile meshes (tools/blender/ground_build.py) against the "
                 "grid's bilinear surface, at every node, edge midpoint and cell centre a triangle covers; at a "
                 "centre, or the cell's own |z00 + z11 - z10 - z01| / 4 where that is larger, which even the full "
                 "grid mesh is off by. A point takes the smallest tolerance of the zones that hold it; plan "
                 "metres, Godot x and z. Written by `ground_build.py --write-zones`.",
        "default_m": 0.25,
        "zones": [
            {"name": "park", "tolerance_m": 0.02,
             "source": "ParkPlan.REBUILD_FOOTPRINT_MIN_X, _MAX_X, _MIN_Z, _MAX_Z (the developed park's "
                       "envelope, %g..%g, %g..%g) plus %g m" % (fx0, fx1, fz0, fz1, PARK_MARGIN_M),
             "rect": [fx0 - PARK_MARGIN_M, fz0 - PARK_MARGIN_M, fx1 + PARK_MARGIN_M, fz1 + PARK_MARGIN_M]},
            {"name": "walkable", "tolerance_m": 0.05, "within_m": WALK_WITHIN_M,
             "source": "Within within_m of any road centreline in lines, or inside polygons. ParkPlan: "
                       "highway_path(), approach_road_points(), the front road (FRONT_ROAD_Z, _HALF_X), "
                       "town_streets(); north_town_outline(), BEACH_TOWN_OUTLINE. "
                       "assets/source/far_shore_city_relocation.blend: the road ribbons' centres ("
                       + ", ".join(CITY_RIBBONS) + "; bridge_city_intersection's outline) and the city, "
                       "the plan hull of city_block_*, city_skyline_anchor_* and city_ferry_terminal.",
             "lines": {k: [[_r(x), _r(z)] for x, z in v] for k, v in lines.items()},
             "polygons": {"north_town": [[_r(x), _r(z)] for x, z in plan["north_town_outline"]],
                          "beach_town": [[_r(x), _r(z)] for x, z in plan["beach_town_outline"]],
                          "city": [[x, z] for x, z in city]}},
        ],
    }
    path = os.path.join(SRC, "grid.json")
    spec = json.load(open(path))
    spec["tolerance_zones"] = zones
    with open(path + ".part", "w") as f:
        f.write(_format_json(spec) + "\n")
    os.replace(path + ".part", path)
    log("tolerance_zones written to %s: %d lines, %d polygons" % (path, len(lines), 3))


def _format_json(obj, indent=0):
    """grid.json's own layout: objects indented, lists on one line."""
    pad = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = ['%s  %s: %s' % (pad, json.dumps(k), _format_json(v, indent + 1)) for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(obj, list) and any(isinstance(v, dict) for v in obj):
        items = ["%s  %s" % (pad, _format_json(v, indent + 1)) for v in obj]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    return json.dumps(obj, ensure_ascii=False)


# --- main ---------------------------------------------------------------------

def main(argv):
    p = argparse.ArgumentParser(prog="ground_build.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tiles", default="all", help="all, or tiles as x0_z0,x1_z0")
    p.add_argument("--force", action="store_true", help="build every asked tile from nothing")
    p.add_argument("--out", default=OUT, help="where the tiles go (default assets/world_ground/tiles)")
    p.add_argument("--census", help="after building, write the tiles into this .blend (never in the tree)")
    p.add_argument("--prove", help="after building, measure the written tiles into this JSON")
    p.add_argument("--no-build", action="store_true", help="skip the build (with --census or --prove)")
    p.add_argument("--held", help="a faces dump folder to read the held ground from (default: dump it now with Godot)")
    p.add_argument("--no-seam", action="store_true", help="build without the carve and stitch (the grid alone)")
    p.add_argument("--no-done", action="store_true", help="do not write BUILD_DONE (the caller writes it after importing)")
    p.add_argument("--write-zones", action="store_true", help="derive tolerance_zones into grid.json and stop")
    a = p.parse_args(argv)
    if a.write_zones:
        run_write_zones(a)
        return
    if not a.no_build:
        run_build(a)
    if a.prove:
        run_prove(a)
    if a.census:
        if os.path.abspath(a.census).startswith(ROOT + os.sep):
            raise SystemExit("ground_build: the census blend never goes in the tree")
        run_census(a)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
