"""The world terrain master: the standing Godot ground, sampled, as a Blender
file Christina can sculpt (2026-10-01, her plan: all the terrain in Blender,
approved level by level, world then region then sub-region then earthworks,
buildings after).

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
        --python tools/blender/world_terrain.py -- --manifest <grids.json> [--plan <plan.json>] \
        [--out assets/source/world_terrain_master.blend] [--render <folder>] [--skip <grid>] [--up-source <grid>] [--replace]

The first file is LOSSLESS: every vertex sits at a height the game's own
collision answered (`tools/_heightfield_probe.gd`), so nothing changes until
she sculpts it. The build proves that, by re-sampling the finished mesh at
every probe point, and prints the largest error.

Inputs
- `--manifest`: a JSON list of heightfield grids. Either `{"grids": [...]}` or
  a bare list; each entry names its CSV under `csv` (or `file`/`path`),
  relative to the manifest, and may give `name`, `step` (or `step_m`) and
  `role` (or `region`); `--skip <name>` leaves a grid out. The CSV is
  the probe's: `x,z,top_y,top_owner,ground_y,ground_owner,peels`, Godot world
  coordinates. An empty `ground_y` is open sea: no collision exists there.
- `--plan`: `ParkPlan` dumped by `tools/plan_dump.gd`. Without it the
  Reference collection holds only what needs no plan, and the rest is listed
  as missing.
- The city package's GLB (`assets/far_shore_city_relocation.glb`) for the
  peninsula, bridge and city footprints, and the entrance landscaping map for
  the proposed lagoon. Both optional; both reported when absent.

What it builds
- `Terrain`: one grid mesh per manifest grid, a vertex per sampled cell,
  quads between neighbours. Per vertex: `owner` (int, see the object's
  `kyt_owner_table`), `placeholder_bathymetry` (bool), `sampled` (bool),
  `top_y`, `peels`, `kind` (`kyt_kind_table`), `surface_y` (what a person
  stands on, where the probe knew), `minus11_skirt` (the −11 m plate under
  open water that the probe manifest calls a source-mesh skirt, kept because
  it is sampled), and two colour attributes for review, `height_shade` and
  `owner_colour`; `ground_y_sampled` and `top_from_upray` carry the interim
  inside-out rule (below). `kyt_collision = "trimesh"`: collision is derived at export,
  never authored, no `-colonly` twins.
  Open-sea cells get a PLACEHOLDER seabed, because the game has none: a shelf
  falling 1:50 from the nearest shore, from 2 m under sea level to 40 m at
  most. It is flagged per vertex and on the object, and it is not a decision.
- `sea_level_water`: a plane at `ParkPlan.WATER_TOP` (−7.5 m), no collision.
- `Reference`: locked (no select) and never exported. The park program
  envelope and a padded one, the Plaza and its datum, the two protected
  anchors NT-1 and NT-2, the coast highway and approach roads as curves (so
  the earthworks layer can later be driven from curves), the coast outlines,
  the sunset-water wedge from the pier head, the lagoon proposal, the city
  peninsula and bridge footprints, towns, cliffs, the creek and the range toe.
  Flat plan lines are draped on the sampled ground; their heights are a
  visual aid, not data.

Inside-out meshes (interim). The manifest's `inside_out_meshes` lists meshes
whose faces point inward, so a ray from above falls through to their −11 m
base cap while a ray from below finds the top. Where a grid carries up-ray
columns, a vertex over such a mesh takes max(ground_y, up_y) and is flagged
`top_from_upray`; a grid without up columns borrows them from an `--up-source`
grid by bilinear interpolation, flagged `top_from_upray_interpolated`, only
where all four source corners have an inside-out top. A manifest entry with
`supersedes: <name>` replaces that grid, and once the sources are fixed the
rule finds nothing: no code change.

Seams. A coarse grid's cells strictly under a finer patch, inset by one
coarse step, are cut, so the coarse mesh reaches under the patch edge by up
to one cell (overlap, never a gap) and every vertex stays a sample.

Axes. Godot is Y-up, x east, z south; Blender is Z-up. The mapping, stated
on the scene as custom properties and proved on 20 cells each build:
    blender.x = godot.x,  blender.y = -godot.z,  blender.z = godot.y

A sculpted mesh is kept: a run refuses while any terrain mesh differs from
what this tool last built (`kyt_terrain_hash`), and names it, together with
the authored edits logged in the object's `kyt_edits` (scripts such as
`world_terrain_edit_blend_south_range.py`). `--replace` builds over it
anyway; the logged edit scripts are then run again, in order, on the rebuilt
file. The builder does not re-apply them itself, because an edit is only
right against the sampled ground it was made on and should be looked at
again when that ground changes. Collections other than `Terrain` and `Reference` are
left alone. Nothing here exports to the game.
"""

import csv
import hashlib
import json
import math
import os
import re
import struct
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DEFAULT_OUT = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
DEFAULT_CITY_GLB = os.path.join(ROOT, "assets", "far_shore_city_relocation.glb")
DEFAULT_MAP = os.path.join(ROOT, "documentation", "maps", "entrance-landscaping.html")

AXIS_MAP = "blender.x = godot.x; blender.y = -godot.z; blender.z = godot.y (metres)"

# The placeholder seabed. The game has no seabed collision at all, so these
# are a stand-in for her to replace, never a measurement.
SHELF_START_DEPTH = 2.0   # m under sea level at the shore
SHELF_SLOPE = 1.0 / 50.0  # fall per metre from the nearest sampled land
SHELF_MAX_DEPTH = 40.0    # m under sea level, the shelf's floor

# The park program envelope (park-rebuild-masterplan.md, "Expanded-world
# datum") and the pad drawn round it. The pad is this tool's own 50 m; no
# document gives one.
ENVELOPE = (-212.0, 222.0, -230.0, 220.0)  # x from, x to, z from, z to
ENVELOPE_PAD = 50.0

# The sunset-water wedge: azimuth 294° from the pier head stays open water;
# the wedge drawn is 280°..310°, out to this radius.
SUNSET_AZ = 294.0
SUNSET_WEDGE = (280.0, 310.0)
SUNSET_RADIUS = 3000.0

OPEN_SEA_OWNER = "open_sea_placeholder_bathymetry"

# Reference line thickness, a render aid only (curves without a bevel do not
# render): world-scale lines and park-scale lines.
BEVEL_WORLD = 6.0
BEVEL_PARK = 1.2

COLOURS = {
    "envelope": (1.0, 0.85, 0.2, 1.0),
    "plaza": (1.0, 1.0, 1.0, 1.0),
    "anchor": (1.0, 0.2, 0.2, 1.0),
    "highway": (0.1, 0.1, 0.1, 1.0),
    "highway_raw": (0.45, 0.45, 0.45, 1.0),
    "approach": (0.25, 0.2, 0.15, 1.0),
    "coast": (0.1, 0.5, 1.0, 1.0),
    "sunset": (1.0, 0.5, 0.0, 1.0),
    "proposal": (0.9, 0.3, 0.9, 1.0),
    "city": (0.6, 0.2, 0.8, 1.0),
    "town": (0.9, 0.6, 0.2, 1.0),
    "creek": (0.2, 0.7, 0.9, 1.0),
    "range": (0.2, 0.6, 0.2, 1.0),
    "cliff": (0.5, 0.35, 0.2, 1.0),
}


# --- coordinates ---------------------------------------------------------

def to_blender(x, y, z):
    """Godot (x east, y up, z south) to Blender (Z up)."""
    return (x, -z, y)


def to_godot(bx, by, bz):
    return (bx, bz, -by)


# --- inputs ---------------------------------------------------------------

def expand_names(items):
    """Manifest mesh names, with `name_0..4` ranges expanded to one name each,
    cut to their last path component."""
    out = set()
    for it in items:
        it = str(it).split("/")[-1]
        m = re.match(r"^(.*?)(\d+)\.\.(\d+)$", it)
        if m:
            for k in range(int(m.group(2)), int(m.group(3)) + 1):
                out.add(f"{m.group(1)}{k}")
        else:
            out.add(it)
    return out


def load_manifest(path, skip=(), up_sources=()):
    """The manifest's grids, split into terrain grids and up-ray sources.

    An entry is dropped when it is superseded: it carries `superseded_by` or
    `status: superseded`, or another entry's `supersedes` names it. So a
    `_fixed` grid that says `supersedes: world_25m` replaces the old one with
    no code change. An entry is an up-ray source only (its down columns are
    not built) when named in `--up-source`, or when it says `use: up_source`.
    Returns (grids, up_sources, inside_out_names, manifest_dict)."""
    with open(path) as f:
        data = json.load(f)
    entries = data["grids"] if isinstance(data, dict) and "grids" in data else data
    if isinstance(entries, dict):
        entries = entries.get("files") or entries.get("heightfields") or list(entries.values())
    base = os.path.dirname(os.path.abspath(path))
    grids = []
    superseded = set()
    for i, e in enumerate(entries):
        if isinstance(e, str):
            e = {"csv": e}
        rel = e.get("csv") or e.get("file") or e.get("path")
        if not rel:
            raise SystemExit(f"world_terrain: manifest entry {i} names no csv")
        full = rel if os.path.isabs(rel) else os.path.join(base, rel)
        name = re.sub(r"[^A-Za-z0-9_]+", "_", e.get("name") or os.path.splitext(os.path.basename(full))[0])
        sup = e.get("supersedes") or []
        if isinstance(sup, str):
            sup = [sup]
        superseded.update(re.sub(r"[^A-Za-z0-9_]+", "_", x) for x in sup)
        if e.get("superseded_by") or str(e.get("status", "")).lower() == "superseded":
            superseded.add(name)
        grids.append({"name": name, "csv": full, "step": e.get("step") or e.get("step_m"),
                      "role": e.get("role") or e.get("region", ""), "supersedes": list(sup),
                      "up_source": str(e.get("use", "")).lower() == "up_source" or name in up_sources})
    dropped = [g["name"] for g in grids if g["name"] in superseded or g["name"] in skip]
    grids = [g for g in grids if g["name"] not in superseded and g["name"] not in skip]
    ups = [g for g in grids if g["up_source"]]
    grids = [g for g in grids if not g["up_source"]]
    if not grids:
        raise SystemExit("world_terrain: the manifest lists no terrain grids")
    inside_out = set()
    if isinstance(data, dict):
        io = data.get("inside_out_meshes") or {}
        inside_out = expand_names(io.get("meshes", []) if isinstance(io, dict) else io)
    for g in grids + ups:
        g["dropped"] = dropped
    return grids, ups, inside_out, data if isinstance(data, dict) else {}


def load_grid(path, inside_out=None):
    """A probe CSV as a regular grid. Cells the CSV leaves out have no vertex;
    cells with no ground_y are open sea."""
    xs, zs, g, t, own, peels, kinds, surf, ups, upio = [], [], [], [], [], [], [], [], [], []
    inside_out = inside_out or set()
    with open(path, newline="") as f:
        rd = csv.DictReader(f)
        has_up = "up_y" in rd.fieldnames
        for row in rd:
            uy = row.get("up_y", "") if has_up else ""
            ups.append(float(uy) if uy not in ("", None) else math.nan)
            uo = row.get("up_owner", "") or ""
            upio.append(bool(uy) and any(part in inside_out for part in uo.split("/")))
            kinds.append(row.get("kind", "") or "")
            sy = row.get("surface_y", "")
            surf.append(float(sy) if sy not in ("", None) else math.nan)
            xs.append(float(row["x"]))
            zs.append(float(row["z"]))
            gy = row.get("ground_y", "")
            g.append(float(gy) if gy not in ("", None) else math.nan)
            ty = row.get("top_y", "")
            t.append(float(ty) if ty not in ("", None) else math.nan)
            own.append(row.get("ground_owner", "") or "")
            p = row.get("peels", "")
            peels.append(int(float(p)) if p not in ("", None) else 0)
    xs = np.array(xs)
    zs = np.array(zs)
    ux = np.unique(xs)
    uz = np.unique(zs)
    step_x = float(np.min(np.diff(ux))) if len(ux) > 1 else 0.0
    step_z = float(np.min(np.diff(uz))) if len(uz) > 1 else 0.0
    ix = np.searchsorted(ux, xs)
    iz = np.searchsorted(uz, zs)
    shape = (len(uz), len(ux))
    ground = np.full(shape, math.nan)
    top = np.full(shape, math.nan)
    present = np.zeros(shape, dtype=bool)
    peel = np.zeros(shape, dtype=np.int32)
    names = sorted(set(o for o in own if o))
    table = [OPEN_SEA_OWNER] + names
    index = {n: i for i, n in enumerate(table)}
    owner = np.zeros(shape, dtype=np.int32)
    kind_table = [""] + sorted(set(k for k in kinds if k))
    kind_index = {n: i for i, n in enumerate(kind_table)}
    kind = np.zeros(shape, dtype=np.int32)
    surface = np.full(shape, math.nan)
    up = np.full(shape, math.nan)
    up_io = np.zeros(shape, dtype=bool)
    for k in range(len(xs)):
        kind[iz[k], ix[k]] = kind_index[kinds[k]]
        surface[iz[k], ix[k]] = surf[k]
        up[iz[k], ix[k]] = ups[k]
        up_io[iz[k], ix[k]] = upio[k]
        ground[iz[k], ix[k]] = g[k]
        top[iz[k], ix[k]] = t[k]
        present[iz[k], ix[k]] = True
        peel[iz[k], ix[k]] = peels[k]
        owner[iz[k], ix[k]] = index[own[k]] if own[k] else 0
    return {"ux": ux, "uz": uz, "step": (step_x, step_z), "ground": ground, "top": top,
            "present": present, "peels": peel, "owner": owner, "owner_table": table,
            "kind": kind, "kind_table": kind_table, "surface": surface,
            "up": up, "up_inside_out": up_io, "has_up": has_up, "up_cell": present & has_up, "name": os.path.basename(path),
            "bounds": (float(ux[0]), float(ux[-1]), float(uz[0]), float(uz[-1])),
            "rows": len(xs), "path": path}


def apply_up_rays(grid, up_sources):
    """The interim inside-out rule. Rays from above fall through the meshes the
    manifest lists as inside out and stop on their -11 m base; rays from
    below find their tops. Visible top = max(ground_y, up_y) where up_owner is
    one of those meshes. A grid without up columns borrows them from an
    up-source grid by bilinear interpolation, which is flagged as such. Once
    the sources are fixed and re-sampled the rule finds nothing and is a
    no-op. Sets grid["visible"], grid["from_upray"], grid["upray_interp"]."""
    ground = grid["ground"]
    visible = ground.copy()
    flagged = np.zeros(ground.shape, dtype=bool)
    interp = np.zeros(ground.shape, dtype=bool)
    land = grid["present"] & ~np.isnan(ground)
    own = land & grid["up_cell"]
    cand = own & grid["up_inside_out"] & ~np.isnan(grid["up"]) & (grid["up"] > ground)
    visible[cand] = grid["up"][cand]
    flagged |= cand
    borrow = land & ~grid["up_cell"]
    if up_sources and borrow.any():
        src = up_sources[0]
        su = np.where(src["up_inside_out"] & ~np.isnan(src["up"]), src["up"], -math.inf)
        sux, suz = src["ux"], src["uz"]
        zz, xx = np.nonzero(borrow)
        px, pz = grid["ux"][xx], grid["uz"][zz]
        inside = (px >= sux[0]) & (px <= sux[-1]) & (pz >= suz[0]) & (pz <= suz[-1])
        if inside.any():
            fx = np.interp(px[inside], sux, np.arange(len(sux)))
            fz = np.interp(pz[inside], suz, np.arange(len(suz)))
            i0 = np.clip(np.floor(fx).astype(int), 0, len(sux) - 2)
            j0 = np.clip(np.floor(fz).astype(int), 0, len(suz) - 2)
            tx, tz = fx - i0, fz - j0
            corners = np.array([su[j0, i0], su[j0, i0 + 1], su[j0 + 1, i0], su[j0 + 1, i0 + 1]])
            weights = np.array([(1 - tx) * (1 - tz), tx * (1 - tz), (1 - tx) * tz, tx * tz])
            # Only where every corner that carries weight has an inside-out
            # top: no half-blended edges. A cell on the source lattice reads
            # one corner exactly and is not interpolated.
            # Corners without an inside-out top drop out and the rest are
            # renormalised, so the borrowed surface ends on a smooth edge
            # instead of a comb. A cell on the source lattice reads one
            # corner exactly and is not interpolated.
            used = (weights > 1e-9) & np.isfinite(corners)
            wsum = np.sum(np.where(used, weights, 0.0), axis=0)
            ok = wsum > 1e-9
            val = np.sum(np.where(used, corners * weights, 0.0), axis=0) / np.where(ok, wsum, 1.0)
            exact = np.sum(weights > 1e-9, axis=0) == 1
            sel_z, sel_x = zz[inside][ok], xx[inside][ok]
            better = val[ok] > ground[sel_z, sel_x]
            visible[sel_z[better], sel_x[better]] = val[ok][better]
            flagged[sel_z[better], sel_x[better]] = True
            interp[sel_z[better], sel_x[better]] = ~exact[ok][better]
    grid["visible"] = visible
    grid["from_upray"] = flagged
    grid["upray_interp"] = interp


def merge_aligned(grids):
    """Grids of one step whose lattices line up (the world box and its edge
    strips, which abut without overlap) become one grid, so no seam is left
    between them. Every sample keeps its place; nothing is interpolated."""
    out = []
    used = [False] * len(grids)
    for i, g in enumerate(grids):
        if used[i]:
            continue
        step = max(g["step"])
        group = [g]
        used[i] = True
        for j in range(i + 1, len(grids)):
            h = grids[j]
            if used[j] or max(h["step"]) != step or step <= 0:
                continue
            if abs((h["ux"][0] - g["ux"][0]) % step) > 1e-6 or abs((h["uz"][0] - g["uz"][0]) % step) > 1e-6:
                continue
            group.append(h)
            used[j] = True
        if len(group) == 1:
            out.append(g)
            continue
        ux = np.unique(np.concatenate([q["ux"] for q in group]))
        uz = np.unique(np.concatenate([q["uz"] for q in group]))
        ux = np.arange(ux[0], ux[-1] + step * 0.5, step)
        uz = np.arange(uz[0], uz[-1] + step * 0.5, step)
        shape = (len(uz), len(ux))
        owner_table = [OPEN_SEA_OWNER] + sorted(set(n for q in group for n in q["owner_table"][1:]))
        kind_table = [""] + sorted(set(n for q in group for n in q["kind_table"][1:]))
        m = {"ux": ux, "uz": uz, "step": (float(step), float(step)), "owner_table": owner_table, "kind_table": kind_table,
             "ground": np.full(shape, math.nan), "top": np.full(shape, math.nan), "surface": np.full(shape, math.nan),
             "up": np.full(shape, math.nan), "present": np.zeros(shape, dtype=bool), "up_inside_out": np.zeros(shape, dtype=bool),
             "peels": np.zeros(shape, dtype=np.int32), "owner": np.zeros(shape, dtype=np.int32), "kind": np.zeros(shape, dtype=np.int32),
             "has_up": any(q["has_up"] for q in group), "up_cell": np.zeros(shape, dtype=bool), "rows": sum(q["rows"] for q in group),
             "name": "+".join(q["name"] for q in group), "path": ", ".join(os.path.basename(q["path"]) for q in group),
             "bounds": (float(ux[0]), float(ux[-1]), float(uz[0]), float(uz[-1])), "merged_from": [q["name"] for q in group]}
        for q in group:
            ix = np.rint((q["ux"] - ux[0]) / step).astype(int)
            iz = np.rint((q["uz"] - uz[0]) / step).astype(int)
            sl = np.ix_(iz, ix)
            pm = q["present"]
            omap = np.array([owner_table.index(n) for n in q["owner_table"]])
            kmap = np.array([kind_table.index(n) for n in q["kind_table"]])
            for key in ("ground", "top", "surface", "up", "peels", "up_inside_out", "up_cell"):
                m[key][sl] = np.where(pm, q[key], m[key][sl])
            m["owner"][sl] = np.where(pm, omap[q["owner"]], m["owner"][sl])
            m["kind"][sl] = np.where(pm, kmap[q["kind"]], m["kind"][sl])
            m["present"][sl] |= pm
        out.append(m)
    return out


def placeholder_seabed(grid, sea_level):
    """Heights for the open-sea cells: a shelf falling from the nearest sampled
    land. Returns the filled height array and the mask of filled cells."""
    ground = grid.get("visible", grid["ground"])
    present = grid["present"]
    sea = present & np.isnan(ground)
    land = present & ~np.isnan(ground)
    filled = ground.copy()
    if not sea.any():
        return filled, sea
    if not land.any():
        filled[sea] = sea_level - SHELF_MAX_DEPTH
        return filled, sea
    # Shore cells: land with a sea neighbour (or on the grid's edge beside sea
    # outside the grid is unknowable, so only neighbours count).
    shore = np.zeros_like(land)
    for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        shifted = np.roll(sea, (dz, dx), axis=(0, 1))
        if dz == 1:
            shifted[0, :] = False
        if dz == -1:
            shifted[-1, :] = False
        if dx == 1:
            shifted[:, 0] = False
        if dx == -1:
            shifted[:, -1] = False
        shore |= land & shifted
    if not shore.any():
        shore = land
    ux, uz = grid["ux"], grid["uz"]
    sz, sx = np.nonzero(shore)
    shore_pts = np.stack([ux[sx], uz[sz]], axis=1)
    shore_h = ground[sz, sx]
    qz, qx = np.nonzero(sea)
    sea_pts = np.stack([ux[qx], uz[qz]], axis=1)
    heights = np.empty(len(qz))
    chunk = 4096
    for s in range(0, len(qz), chunk):
        p = sea_pts[s:s + chunk]
        d2 = ((p[:, None, :] - shore_pts[None, :, :]) ** 2).sum(axis=2)
        j = np.argmin(d2, axis=1)
        dist = np.sqrt(d2[np.arange(len(p)), j])
        start = np.minimum(shore_h[j], sea_level - SHELF_START_DEPTH)
        heights[s:s + chunk] = np.maximum(start - dist * SHELF_SLOPE, sea_level - SHELF_MAX_DEPTH)
    filled[qz, qx] = heights
    return filled, sea


# --- colours for review ---------------------------------------------------

def height_shade(h, sea_level, is_sea):
    """A review ramp: sea by depth, shore sand, lowland green, hills to white."""
    out = np.empty((len(h), 4))
    out[:, 3] = 1.0
    depth = np.clip((sea_level - h) / SHELF_MAX_DEPTH, 0.0, 1.0)
    out[:, 0] = 0.10 - 0.08 * depth
    out[:, 1] = 0.35 - 0.25 * depth
    out[:, 2] = 0.65 - 0.35 * depth
    land = ~is_sea
    stops = [(-12.0, (0.85, 0.80, 0.60)), (0.0, (0.80, 0.78, 0.55)), (15.0, (0.40, 0.62, 0.30)),
             (80.0, (0.30, 0.48, 0.22)), (220.0, (0.55, 0.47, 0.32)), (360.0, (0.62, 0.60, 0.58)),
             (470.0, (0.97, 0.97, 0.97))]
    hs = np.array([s[0] for s in stops])
    cs = np.array([s[1] for s in stops])
    hl = np.clip(h[land], hs[0], hs[-1])
    for c in range(3):
        out[land, c] = np.interp(hl, hs, cs[:, c])
    return out


def owner_palette(table):
    cols = []
    for i, name in enumerate(table):
        if i == 0:
            cols.append((0.05, 0.08, 0.20, 1.0))
            continue
        hsh = int(hashlib.sha1(name.encode()).hexdigest()[:6], 16)
        hue = (hsh % 360) / 360.0
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.9)
        cols.append((r, g, b, 1.0))
    return np.array(cols)


# --- meshes ----------------------------------------------------------------

def shape_hash(me):
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    return hashlib.sha1(np.round(co, 5).tobytes()).hexdigest()[:16]


def grid_arrays(grid, sea_level):
    """One grid's vertices (Blender axes), quads and per-vertex attributes,
    in local indices; `vid` maps lattice cell to local index (-1 = none)."""
    heights, sea = placeholder_seabed(grid, sea_level)
    present = grid["present"]
    vid = np.full(present.shape, -1, dtype=np.int64)
    vid[present] = np.arange(int(present.sum()))
    zz, xx = np.nonzero(present)
    gx, gz, gy = grid["ux"][xx], grid["uz"][zz], heights[zz, xx]
    verts = np.stack([gx, -gz, gy], axis=1)
    a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, 1:], vid[1:, :-1]
    ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
    faces = np.stack([a[ok], d[ok], c[ok], b[ok]], axis=1)  # CCW from above
    sampled_ground = grid["ground"][zz, xx]
    top = grid["top"][zz, xx]
    surface = grid["surface"][zz, xx]
    attrs = {
        "owner": grid["owner"][zz, xx].astype(np.int32),
        "placeholder_bathymetry": sea[zz, xx],
        "sampled": ~sea[zz, xx],
        "top_y": np.where(np.isnan(top), gy, top),
        "peels": grid["peels"][zz, xx].astype(np.int32),
        "kind": grid["kind"][zz, xx].astype(np.int32),
        "surface_y": np.where(np.isnan(surface), gy, surface),
        "minus11_skirt": (~sea[zz, xx]) & (np.abs(sampled_ground - (-11.0)) < 1e-6),
        "ground_y_sampled": np.where(np.isnan(sampled_ground), gy, sampled_ground),
        "top_from_upray": grid["from_upray"][zz, xx],
        "top_from_upray_interpolated": grid["upray_interp"][zz, xx],
        "height_shade": height_shade(gy, sea_level, sea[zz, xx]),
    }
    return {"verts": verts, "faces": faces, "vid": vid, "attrs": attrs, "sea": sea[zz, xx], "zz": zz, "xx": xx}


def fine_boundary(grid):
    """Boundary edges of a grid's present lattice: edges of its quads that have
    a quad on one side only. Returns a set of ((j, i), (j, i)) cell pairs."""
    p = grid["present"]
    face = p[:-1, :-1] & p[:-1, 1:] & p[1:, 1:] & p[1:, :-1]
    nz, nx = p.shape
    edges = set()
    fz = np.zeros((nz, nx - 1), dtype=np.int32)  # horizontal edge (j,i)-(j,i+1): faces above and below
    fz[:-1, :] += face
    fz[1:, :] += face
    hor = (p[:, :-1] & p[:, 1:]) & (fz == 1)
    for j, i in zip(*np.nonzero(hor)):
        edges.add(((j, i), (j, i + 1)))
    fx = np.zeros((nz - 1, nx), dtype=np.int32)  # vertical edge (j,i)-(j+1,i): faces left and right
    fx[:, :-1] += face
    fx[:, 1:] += face
    ver = (p[:-1, :] & p[1:, :]) & (fx == 1)
    for j, i in zip(*np.nonzero(ver)):
        edges.add(((j, i), (j + 1, i)))
    return edges


def trace_loops(edges):
    """Closed loops from a set of undirected edges (vertex keys hashable)."""
    adj = {}
    for u, v in edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    seen = set()
    loops = []
    for start in adj:
        if start in seen:
            continue
        loop = [start]
        seen.add(start)
        prev, cur = None, start
        while True:
            nxt = [w for w in adj[cur] if w != prev and w not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        loops.append(loop)
    return loops


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def point_in_loop(pt, loop_xy):
    inside = False
    n = len(loop_xy)
    for i in range(n):
        x0, y0 = loop_xy[i]
        x1, y1 = loop_xy[(i + 1) % n]
        if (y0 > pt[1]) != (y1 > pt[1]):
            xi = x0 + (pt[1] - y0) * (x1 - x0) / (y1 - y0)
            if xi > pt[0]:
                inside = not inside
    return inside


def covered_mask(fine, x, z):
    """True where the plan point (Godot x, z) lies inside the fine patch: in
    its bounds, boundary line included, with its enclosing fine cell present."""
    fs = max(fine["step"])
    fp = fine["present"]
    fux, fuz = fine["ux"], fine["uz"]
    sat = fine.get("_sat")
    if sat is None:
        sat = np.zeros((fp.shape[0] + 1, fp.shape[1] + 1), dtype=np.int64)
        sat[1:, 1:] = fp.astype(np.int64).cumsum(0).cumsum(1)
        fine["_sat"] = sat
    eps = 1e-6
    inside = (x >= fux[0] - eps) & (x <= fux[-1] + eps) & (z >= fuz[0] - eps) & (z <= fuz[-1] + eps)
    i0 = np.clip(np.floor((x - fux[0]) / fs + eps).astype(int), 0, fp.shape[1] - 1)
    i1 = np.clip(np.ceil((x - fux[0]) / fs - eps).astype(int), 0, fp.shape[1] - 1)
    j0 = np.clip(np.floor((z - fuz[0]) / fs + eps).astype(int), 0, fp.shape[0] - 1)
    j1 = np.clip(np.ceil((z - fuz[0]) / fs - eps).astype(int), 0, fp.shape[0] - 1)
    total = sat[j1 + 1, i1 + 1] - sat[j0, i1 + 1] - sat[j1 + 1, i0] + sat[j0, i0]
    return inside & (total == (j1 - j0 + 1) * (i1 - i0 + 1))


def seam_jump(coarse, fine, f_arr, sea_level):
    """The patch's boundary heights against the coarse surface (bilinear on
    its lattice, placeholder sea filled): what the stitch has to absorb."""
    c_h, _ = placeholder_seabed(coarse, sea_level)
    cp = coarse["present"]
    fux, fuz = fine["ux"], fine["uz"]
    bverts = sorted(set(v for e in fine_boundary(fine) for v in e))
    jumps = []
    for (j, i) in bverts:
        px, pz = fux[i], fuz[j]
        if not (coarse["ux"][0] <= px <= coarse["ux"][-1] and coarse["uz"][0] <= pz <= coarse["uz"][-1]):
            continue
        tx = np.interp(px, coarse["ux"], np.arange(len(coarse["ux"])))
        tz = np.interp(pz, coarse["uz"], np.arange(len(coarse["uz"])))
        a0, b0 = int(np.clip(np.floor(tx), 0, len(coarse["ux"]) - 2)), int(np.clip(np.floor(tz), 0, len(coarse["uz"]) - 2))
        wx, wz = tx - a0, tz - b0
        q = c_h[b0:b0 + 2, a0:a0 + 2]
        if np.isnan(q).any() or not cp[b0:b0 + 2, a0:a0 + 2].all():
            continue
        h = (q[0, 0] * (1 - wx) + q[0, 1] * wx) * (1 - wz) + (q[1, 0] * (1 - wx) + q[1, 1] * wx) * wz
        jumps.append(abs(f_arr["verts"][f_arr["vid"][j, i], 2] - h))
    jumps = np.array(jumps) if jumps else np.zeros(1)
    return len(bverts), float(jumps.max()), float(jumps.mean())


def stitch_all(coarse, fines, c_arr, f_arrs, c_off, f_offs, sea_level, xy):
    """Connect every finer patch into a coarser lattice without a step or gap.

    Every coarse sample inside a patch (boundary line included) is dropped,
    which opens holes in the coarse lattice up to one coarse cell wider than
    the patches; a hole may hold several patches. Each hole is then
    triangulated by constrained Delaunay (`mathutils.geometry`) with the
    patches' boundary loops as constraints, and the triangles inside a patch
    are discarded. No vertex is added or moved, so every vertex is still a
    sample. Returns (dropped mask, triangles as global index tuples, metrics)."""
    from mathutils import geometry
    cp = coarse["present"]
    cz, cx = np.nonzero(cp)
    x, z = coarse["ux"][cx], coarse["uz"][cz]
    drop = np.zeros_like(cp)
    per_patch = []
    for fine, f_arr in zip(fines, f_arrs):
        cov = covered_mask(fine, x, z)
        m = np.zeros_like(cp)
        m[cz, cx] = cov
        drop |= m
        nb, jmax, jmean = seam_jump(coarse, fine, f_arr, sea_level)
        per_patch.append({"seam": f"{fine['name']} into {coarse['name']}", "boundary_vertices": nb,
                          "jump_before_max_m": jmax, "jump_before_mean_m": jmean, "jump_after_max_m": 0.0,
                          "coarse_dropped": int(cov.sum())})
    keep = cp & ~drop

    def face_count(mask):
        face = mask[:-1, :-1] & mask[:-1, 1:] & mask[1:, 1:] & mask[1:, :-1]
        nz, nx = mask.shape
        hz = np.zeros((nz, nx - 1), dtype=np.int32)
        hz[:-1, :] += face
        hz[1:, :] += face
        vx = np.zeros((nz - 1, nx), dtype=np.int32)
        vx[:, :-1] += face
        vx[:, 1:] += face
        return hz, vx

    hb, vb = face_count(cp)
    ha, va = face_count(keep)
    c_edges = set()
    for j, i in zip(*np.nonzero((hb == 2) & (ha == 1))):
        c_edges.add(((j, i), (j, i + 1)))
    for j, i in zip(*np.nonzero((vb == 2) & (va == 1))):
        c_edges.add(((j, i), (j + 1, i)))
    hole_loops = [[c_off + c_arr["vid"][j, i] for (j, i) in lp] for lp in trace_loops(c_edges)]
    fine_loops = []  # (patch index, loop of global indices)
    for k, (fine, f_arr, f_off) in enumerate(zip(fines, f_arrs, f_offs)):
        for lp in trace_loops(fine_boundary(fine)):
            fine_loops.append((k, [f_off + f_arr["vid"][j, i] for (j, i) in lp]))
    tris = []
    notes = []
    unused = set(range(len(fine_loops)))
    for hl in hole_loops:
        if len(hl) < 3:
            continue
        hxy = [tuple(xy[v]) for v in hl]
        inner = [k for k in unused if point_in_loop(tuple(xy[fine_loops[k][1][0]]), hxy)]
        unused -= set(inner)
        verts = list(hl)
        edges = []
        for k in inner:
            lp = fine_loops[k][1]
            base = len(verts)
            verts += lp
            edges += [(base + i, base + (i + 1) % len(lp)) for i in range(len(lp))]
        coords = [Vector((float(xy[v][0]), float(xy[v][1]))) for v in verts]
        out = geometry.delaunay_2d_cdt(coords, edges, [list(range(len(hl)))], 1, 1e-5)
        o_faces, orig_v = out[2], out[3]
        bad = [i for i, ov in enumerate(orig_v) if len(ov) != 1]
        if bad:
            notes.append(f"hole at {hxy[0]}: {len(bad)} triangulation vertices are not single samples; hole left open")
            continue
        gmap = [verts[ov[0]] for ov in orig_v]
        kept = 0
        for f in o_faces:
            if len(f) != 3:
                continue
            g = [gmap[i] for i in f]
            cxp = sum(xy[v][0] for v in g) / 3.0
            cyp = sum(xy[v][1] for v in g) / 3.0
            cxg, czg = np.array([cxp]), np.array([-cyp])
            if any(covered_mask(fine, cxg, czg)[0] for fine in fines):
                continue
            p0, p1, p2 = xy[g[0]], xy[g[1]], xy[g[2]]
            cr = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
            if abs(cr) < 1e-9:
                continue
            tris.append(tuple(g) if cr > 0 else (g[0], g[2], g[1]))
            kept += 1
        notes.append(f"hole with {len(hl)} coarse samples holds {len(inner)} patch loop(s): {kept} triangles")
    if unused:
        notes.append(f"{len(unused)} patch loop(s) found no hole round them")
    metrics = {"patches": per_patch, "holes": notes, "triangles": len(tris), "coarse_dropped": int(drop.sum())}
    return drop, tris, metrics


def assemble_mesh(name, loaded, sea_level):
    """All grids as one connected mesh: finer patches stitched into coarser
    lattices, every vertex a sample. Returns (object, stats, lossless, checks)."""
    order = sorted(range(len(loaded)), key=lambda k: -max(loaded[k]["step"]))  # coarse first
    grids = [loaded[k] for k in order]
    arrs = [grid_arrays(g, sea_level) for g in grids]
    offs = []
    n = 0
    for ar in arrs:
        offs.append(n)
        n += len(ar["verts"])
    allverts = np.concatenate([ar["verts"] for ar in arrs])
    xy = allverts[:, :2]
    tris_all = []
    seams = []
    drops = [np.zeros(g["present"].shape, dtype=bool) for g in grids]
    for ci, coarse in enumerate(grids):
        fins = []
        for fi, fine in enumerate(grids):
            if fi == ci or max(fine["step"]) >= max(coarse["step"]):
                continue
            if fine["bounds"][1] < coarse["bounds"][0] or fine["bounds"][0] > coarse["bounds"][1] or \
               fine["bounds"][3] < coarse["bounds"][2] or fine["bounds"][2] > coarse["bounds"][3]:
                continue
            fins.append(fi)
        if not fins:
            continue
        drop, tris, metrics = stitch_all(coarse, [grids[k] for k in fins], arrs[ci], [arrs[k] for k in fins],
                                         offs[ci], [offs[k] for k in fins], sea_level, xy)
        drops[ci] |= drop
        tris_all += tris
        seams.append(metrics)
    # Faces: a coarse quad survives only with all four corners kept.
    faces = []
    kept_vertex = []
    for g, ar, dr, off in zip(grids, arrs, drops, offs):
        vid = ar["vid"]
        keep = g["present"] & ~dr
        kv = np.zeros(len(ar["verts"]), dtype=bool)
        kv[vid[keep]] = True
        kept_vertex.append(kv)
        a, b, c, d = keep[:-1, :-1], keep[:-1, 1:], keep[1:, 1:], keep[1:, :-1]
        vv = vid
        ok = a & b & c & d
        q = np.stack([vv[:-1, :-1][ok], vv[1:, :-1][ok], vv[1:, 1:][ok], vv[:-1, 1:][ok]], axis=1) + off
        faces += [tuple(int(v) for v in f) for f in q.tolist()]
    faces += [tuple(int(v) for v in t) for t in tris_all]
    # Compact: drop vertices nobody uses (the dropped coarse samples).
    used = np.zeros(n, dtype=bool)
    for f in faces:
        for v in f:
            used[v] = True
    remap = np.full(n, -1, dtype=np.int64)
    remap[used] = np.arange(int(used.sum()))
    verts = allverts[used]
    faces = [tuple(int(remap[v]) for v in f) for f in faces]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts.tolist()], [], faces)
    me.update()
    me.validate(verbose=False)
    # attributes, concatenated and compacted
    grid_idx = np.concatenate([np.full(len(ar["verts"]), k, dtype=np.int32) for k, ar in enumerate(arrs)])[used]
    at = me.attributes.new("grid", "INT", "POINT")
    at.data.foreach_set("value", grid_idx)
    owner_tables = [g["owner_table"] for g in grids]
    owner_table = [OPEN_SEA_OWNER] + sorted(set(nm for t in owner_tables for nm in t[1:]))
    kind_table = [""] + sorted(set(nm for g in grids for nm in g["kind_table"][1:]))
    owner_all = np.concatenate([np.array([owner_table.index(nm) for nm in g["owner_table"]])[ar["attrs"]["owner"]]
                                for g, ar in zip(grids, arrs)])[used]
    kind_all = np.concatenate([np.array([kind_table.index(nm) for nm in g["kind_table"]])[ar["attrs"]["kind"]]
                               for g, ar in zip(grids, arrs)])[used]
    at = me.attributes.new("owner", "INT", "POINT")
    at.data.foreach_set("value", owner_all.astype(np.int32))
    at = me.attributes.new("kind", "INT", "POINT")
    at.data.foreach_set("value", kind_all.astype(np.int32))
    for key, kind in (("placeholder_bathymetry", "BOOLEAN"), ("sampled", "BOOLEAN"), ("top_y", "FLOAT"), ("peels", "INT"),
                      ("surface_y", "FLOAT"), ("minus11_skirt", "BOOLEAN"), ("ground_y_sampled", "FLOAT"),
                      ("top_from_upray", "BOOLEAN"), ("top_from_upray_interpolated", "BOOLEAN")):
        vals = np.concatenate([ar["attrs"][key] for ar in arrs])[used]
        at = me.attributes.new(key, kind, "POINT")
        at.data.foreach_set("value", vals.astype(np.int32) if kind == "INT" else vals)
    ca = me.color_attributes.new("height_shade", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", np.concatenate([ar["attrs"]["height_shade"] for ar in arrs])[used].ravel())
    pal = owner_palette(owner_table)
    ca = me.color_attributes.new("owner_colour", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", pal[owner_all].ravel())
    me.shade_flat()
    obj = bpy.data.objects.new(name, me)
    obj["kyt_terrain"] = True
    obj["kyt_collision"] = "trimesh"
    obj["kyt_grid_table"] = json.dumps([g["name"] for g in grids])
    obj["kyt_grid_steps_m"] = [float(max(g["step"])) for g in grids]
    obj["kyt_grid_sources"] = json.dumps([g["path"] for g in grids])
    obj["kyt_owner_table"] = json.dumps(owner_table)
    obj["kyt_kind_table"] = json.dumps(kind_table)
    obj["kyt_placeholder_bathymetry"] = (
        f"open-sea cells have no game collision; their heights are a stand-in shelf falling 1:{int(1 / SHELF_SLOPE)} "
        f"from the nearest sampled land, {SHELF_START_DEPTH:g} m to {SHELF_MAX_DEPTH:g} m under sea level; "
        "see the per-vertex attribute of the same name")
    obj["kyt_inside_out_rule"] = ("interim: vertex height = max(ground_y, up_y) where the up ray's owner is a mesh the "
                                  "manifest lists as inside out; ground_y_sampled keeps the probe's reading; a no-op once "
                                  "the sources are fixed and re-sampled")
    obj["kyt_seams"] = json.dumps(seams)
    obj["kyt_stitch"] = ("finer patches are stitched into coarser lattices: coarse samples under a patch are dropped and each "
                         "the strip between the patch's boundary loop and the hole's boundary loop is zipped with triangles; "
                         "no vertex is added or moved")
    obj["kyt_axis_map"] = AXIS_MAP
    me["kyt_terrain_hash"] = shape_hash(me)
    sampled = np.concatenate([ar["attrs"]["sampled"] for ar in arrs])[used]
    from_up = np.concatenate([ar["attrs"]["top_from_upray"] for ar in arrs])[used]
    interp = np.concatenate([ar["attrs"]["top_from_upray_interpolated"] for ar in arrs])[used]
    skirt = np.concatenate([ar["attrs"]["minus11_skirt"] for ar in arrs])[used]
    stats = {"name": name, "vertices": int(len(verts)), "faces": int(len(faces)), "ngons": len(tris_all),
             "sampled": int(sampled.sum()), "placeholder_sea": int((~sampled).sum()), "top_from_upray": int(from_up.sum()),
             "top_from_upray_interpolated": int(interp.sum()), "minus11_skirt": int(skirt.sum()),
             "minus11_skirt_without_hidden_top": int((skirt & ~from_up).sum()),
             "dropped_coarse_samples": int(sum(d.sum() for d in drops)),
             "visible_max": float(verts[sampled, 2].max()) if sampled.any() else None,
             "height_min": float(verts[sampled, 2].min()) if sampled.any() else None,
             "height_max": float(verts[sampled, 2].max()) if sampled.any() else None,
             "step_m": [float(max(g["step"])) for g in grids], "grids": [g["name"] for g in grids],
             "per_grid_vertices": [int(kv.sum()) for kv in kept_vertex]}
    return obj, stats, seams, grids


def lossless_check(obj, grids):
    """Every sampled point of every grid that still has a vertex: the vertex at
    that plan position (kd-tree, exact) and a ray dropped from above."""
    import mathutils
    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    kd = mathutils.kdtree.KDTree(len(co))
    for i, v in enumerate(co):
        kd.insert((v[0], v[1], 0.0), i)
    kd.balance()
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    down = Vector((0.0, 0.0, -1.0))
    nudges = ((2e-3, 2e-3), (-2e-3, 2e-3), (2e-3, -2e-3), (-2e-3, -2e-3))
    top = float(np.nanmax(co[:, 2])) + 100.0
    points = checked = 0
    vert_err = ray_err = nudged_err = 0.0
    nudged = misses = dropped = 0
    worst = []
    for g in grids:
        land = g["present"] & ~np.isnan(g["ground"])
        zz, xx = np.nonzero(land)
        for k in range(len(zz)):
            x, z, y = float(g["ux"][xx[k]]), float(g["uz"][zz[k]]), float(g["visible"][zz[k], xx[k]])
            points += 1
            loc, idx, dist = kd.find((x, -z, 0.0))
            if dist > 1e-3:
                dropped += 1  # a coarse sample under a finer patch
                continue
            checked += 1
            vert_err = max(vert_err, abs(co[idx, 2] - y))
            hit = bvh.ray_cast(Vector((x, -z, top)), down, 10000.0)
            if hit[0] is not None:
                e = abs(hit[0].z - y)
                if e > 1e-3:
                    worst.append((e, g["name"], x, z, y, float(hit[0].z), int(hit[2])))
                ray_err = max(ray_err, e)
                continue
            for dx, dy in nudges:
                hit = bvh.ray_cast(Vector((x + dx, -z + dy, top)), down, 10000.0)
                if hit[0] is not None:
                    nudged += 1
                    nudged_err = max(nudged_err, abs(hit[0].z - y))
                    break
            else:
                misses += 1
    worst.sort(reverse=True)
    for e, gname, x, z, y, hz, fidx in worst[:8]:
        f = me.polygons[fidx]
        print(f"world_terrain: ray mismatch {e:.2f} m at ({x:g}, {z:g}) in {gname}: vertex {y:.2f}, hit {hz:.2f} on face {fidx} "
              f"with {len(f.vertices)} vertices, grids {sorted(set(int(me.attributes['grid'].data[v].value) for v in f.vertices))}: "
              + "; ".join(f"({co[v, 0]:g}, {-co[v, 1]:g}, {co[v, 2]:.1f})" for v in f.vertices))
    return {"points": points, "checked": checked, "dropped_under_patch": dropped, "vertex_max_error_m": vert_err,
            "ray_max_error_m": ray_err, "ray_nudged": nudged, "ray_nudged_max_error_m": nudged_err, "ray_misses": misses,
            "ray_mismatches": len(worst)}


def round_trip_check(grid, count=20):
    present = grid["present"] & ~np.isnan(grid["ground"])
    zz, xx = np.nonzero(present)
    rng = np.random.default_rng(2026)
    pick = rng.choice(len(zz), size=min(count, len(zz)), replace=False)
    worst = 0.0
    for k in pick:
        g = (float(grid["ux"][xx[k]]), float(grid["ground"][zz[k], xx[k]]), float(grid["uz"][zz[k]]))
        b = to_blender(*g)
        back = to_godot(*b)
        worst = max(worst, max(abs(back[i] - g[i]) for i in range(3)))
    assert worst < 0.01, f"axis round trip failed: {worst} m"
    return {"cells": int(len(pick)), "max_error_m": worst}


# --- reference layer -------------------------------------------------------

class Ref:
    """Builds the locked Reference collection and keeps the missing list."""

    def __init__(self, root_coll, bvh_sampler, sea_level):
        self.root = root_coll
        self.sample = bvh_sampler
        self.sea = sea_level
        self.missing = []
        self.sourced = []
        self.mats = {}
        self.subs = {}

    def sub(self, name):
        if name not in self.subs:
            c = bpy.data.collections.new(f"Reference_{name}")
            c.hide_select = True
            self.root.children.link(c)
            self.subs[name] = c
        return self.subs[name]

    def material(self, key):
        if key in self.mats:
            return self.mats[key]
        m = bpy.data.materials.new(f"ref_{key}")
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = COLOURS[key]
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(em.outputs[0], out.inputs[0])
        m.diffuse_color = COLOURS[key]
        m["kyt_reference"] = True
        self.mats[key] = m
        return m

    def drape(self, x, z, lift=1.0):
        h = self.sample(x, z)
        return (h if h is not None else self.sea) + lift

    def _tag(self, obj, sub, key, note, source):
        obj["kyt_reference"] = True
        obj["kyt_collision"] = "none"
        obj["kyt_source"] = source
        if note:
            obj["kyt_note"] = note
        obj.hide_select = True
        obj.color = COLOURS[key]
        self.sub(sub).objects.link(obj)
        self.sourced.append(f"{obj.name} <- {source}")
        return obj

    def curve(self, name, pts_godot, sub, key, closed=False, bevel=BEVEL_WORLD, drape=None, note="", source=""):
        """pts_godot: list of (x, y, z) or, with drape, (x, z) pairs."""
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = bevel
        cu.bevel_resolution = 0
        cu.materials.append(self.material(key))
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts_godot) - 1)
        for i, p in enumerate(pts_godot):
            if drape is not None:
                x, z = (p[0], p[2]) if len(p) == 3 else (p[0], p[1])
                y = self.drape(x, z, drape)
            else:
                x, y, z = p
            sp.points[i].co = (*to_blender(x, y, z), 1.0)
        sp.use_cyclic_u = closed
        obj = bpy.data.objects.new(name, cu)
        if drape is not None:
            obj["kyt_heights"] = f"draped on the sampled ground +{drape:g} m; a visual aid, not data"
        return self._tag(obj, sub, key, note, source)

    def rect(self, name, x0, x1, z0, z1, y, sub, key, **kw):
        return self.curve(name, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], sub, key, closed=True, **kw)

    def circle(self, name, cx, cz, r, y, sub, key, n=48, **kw):
        pts = [(cx + r * math.cos(2 * math.pi * i / n), y, cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        return self.curve(name, pts, sub, key, closed=True, **kw)

    def marker(self, name, x, y, z, sub, key, size=10.0, note="", source=""):
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = size
        obj.location = to_blender(x, y, z)
        return self._tag(obj, sub, key, note, source)


def glb_meshes(path):
    """Node name -> (world-space vertex array (x, y, z) in Godot axes, extras)
    for every mesh node of a GLB. glTF shares Godot's axes."""
    with open(path, "rb") as f:
        data = f.read()
    length = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20:20 + length])
    bin_off = 20 + length + 8
    out = {}
    accs, views = js["accessors"], js["bufferViews"]
    for node in js["nodes"]:
        if "mesh" not in node:
            continue
        tr = np.array(node.get("translation", [0.0, 0.0, 0.0]))
        pts = []
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            a = accs[prim["attributes"]["POSITION"]]
            v = views[a["bufferView"]]
            off = bin_off + v.get("byteOffset", 0) + a.get("byteOffset", 0)
            arr = np.frombuffer(data, dtype="<f4", count=a["count"] * 3, offset=off).reshape(-1, 3)
            pts.append(arr.astype(np.float64) + tr)
        out[node["name"]] = np.concatenate(pts) if pts else np.zeros((0, 3))
    return out


def hull_xz(pts):
    """Convex hull (monotone chain) of the plan positions of 3D points."""
    p = sorted(set((round(float(a[0]), 2), round(float(a[2]), 2)) for a in pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in p:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(p):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def centreline_from_strip(pts, axis=2, every=1):
    """A thin centreline mesh's vertices, paired along its long axis."""
    order = np.argsort(pts[:, axis])
    s = pts[order]
    if len(s) % 2:
        s = s[:-1]
    mid = (s[0::2] + s[1::2]) * 0.5
    return [tuple(map(float, m)) for m in mid[::every]]


def svg_polys(path, group_class, want):
    """`points` polygons/polylines in an SVG group whose <title> starts with
    one of `want`; the map's viewBox is in metres, x east, y = z south."""
    with open(path) as f:
        html = f.read()
    m = re.search(r'<g class="%s">(.*?)</g>' % re.escape(group_class), html, re.S)
    if not m:
        return {}
    found = {}
    for el in re.finditer(r'<(polygon|polyline)([^>]*)>(?:<title>([^<]*)</title>)?', m.group(1)):
        title = el.group(3) or ""
        pts = re.search(r'points="([^"]+)"', el.group(2))
        for w in want:
            if title.startswith(w) and pts:
                found[w] = ([tuple(map(float, q.split(","))) for q in pts.group(1).split()],
                            el.group(1) == "polygon", title)
    return found


def build_reference(scene, ref, plan, city_glb, map_path, sea_level):
    # Park: envelope, pad, plaza, datum.
    x0, x1, z0, z1 = ENVELOPE
    ref.rect("park_program_envelope", x0, x1, z0, z1, 0.0, "park", "envelope", bevel=BEVEL_PARK, drape=2.0,
             note="x -212..222, z -230..220, park-rebuild-masterplan.md 'Expanded-world datum'",
             source="park-rebuild-masterplan.md")
    p = ENVELOPE_PAD
    ref.rect("park_program_envelope_padded", x0 - p, x1 + p, z0 - p, z1 + p, 0.0, "park", "envelope",
             bevel=BEVEL_PARK, drape=2.0, note=f"the envelope with this tool's own {p:g} m pad; no document gives a pad value",
             source="world_terrain.py ENVELOPE_PAD (assumed)")
    if plan:
        half = plan["PLAZA_HALF"]
        c = plan["PLAZA_CENTRE"]
        ref.rect("plaza_104m", c[0] - half, c[0] + half, c[1] - half, c[1] + half, 0.3, "park", "plaza",
                 bevel=BEVEL_PARK, note="the Plaza, 104 m, brick floor at the datum", source="ParkPlan.PLAZA_HALF, PLAZA_CENTRE")
        ref.circle("fountain_rim", c[0], c[1], plan["FOUNTAIN_RIM_SEAT_R"], 0.3, "park", "plaza", bevel=BEVEL_PARK,
                   source="ParkPlan.FOUNTAIN_RIM_SEAT_R")
        ref.marker("plaza_datum_0m", c[0], 0.0, c[1], "park", "plaza", size=30.0,
                   note="the Plaza datum, +0.00 m; the fountain at the origin", source="ParkPlan")
        # Protected anchors. The west foot is STAIR_FOOT; the east is the
        # west translated (never mirrored), so its foot sits the same distance
        # from its top as the west's.
        foot_dx = plan["STAIR_FOOT"][0] - plan["CASCADE_WEST"]["top_x"]
        for tag, key in (("NT-1_west_stair", "CASCADE_WEST"), ("NT-2_east_cascade", "CASCADE_EAST")):
            cw = plan[key]
            z = cw["axis_z"]
            pts = [(cw["top_x"], cw["head_y"], z), (cw["wall_x"], cw["head_y"], z),
                   (cw["top_x"] + foot_dx, cw["floor_y"], z)]
            ref.curve(f"{tag}_axis", pts, "park", "anchor", bevel=BEVEL_PARK,
                      note=f"protected anchor; head {cw['head_y']:g} m at x {cw['top_x']:g}, floor {cw['floor_y']:g} m; geometry locked",
                      source=f"ParkPlan.{key}, STAIR_FOOT")
            ref.marker(tag, cw["top_x"], cw["head_y"], z, "park", "anchor", size=20.0,
                       note="protected anchor: its geometry, elevations, approaches, water, terrain and sightlines do not change",
                       source=f"ParkPlan.{key}")
        # Shore, pier, wheel and the sunset wedge.
        pr = plan["PIER_ROOT"]
        hw = plan["PIER_HALF_W"]
        head_x = pr[0] - plan["PIER_LENGTH"]
        ref.rect("pier", head_x, pr[0], pr[1] - hw, pr[1] + hw, plan["SHORE_TOP"], "park", "plaza", bevel=BEVEL_PARK,
                 source="ParkPlan.PIER_ROOT, PIER_LENGTH, PIER_HALF_W, SHORE_TOP")
        ref.circle("wheel_footprint", plan["WHEEL_AT"][0], plan["WHEEL_AT"][1], plan["WHEEL_RADIUS"], plan["SHORE_TOP"],
                   "park", "plaza", bevel=BEVEL_PARK, source="ParkPlan.WHEEL_AT, WHEEL_RADIUS")
        head = (head_x, pr[1])
        y = sea_level + 0.5

        def ray(az):
            a = math.radians(az)
            return (head[0] + SUNSET_RADIUS * math.sin(a), y, head[1] - SUNSET_RADIUS * math.cos(a))

        arc = [ray(SUNSET_WEDGE[0] + (SUNSET_WEDGE[1] - SUNSET_WEDGE[0]) * i / 24) for i in range(25)]
        ref.curve("sunset_water_wedge_280_310", [(head[0], y, head[1])] + arc, "park", "sunset", closed=True,
                  note="azimuth 280..310 from the pier head stays open water; sunset is 294 (AGENTS.md composition decisions)",
                  source="ParkPlan pier head; bearing from AGENTS.md")
        ref.curve("sunset_bearing_294", [(head[0], y, head[1]), ray(SUNSET_AZ)], "park", "sunset",
                  source="AGENTS.md: sunset is azimuth 294")
        ref.marker("pier_head", head[0], plan["SHORE_TOP"], head[1], "park", "sunset", size=15.0, source="ParkPlan pier")

        # Roads as curves, the future earthworks drivers.
        ref.curve("coast_highway_centreline", plan["highway_path"], "roads", "highway", drape=1.5,
                  note="ParkPlan.highway_path(), the filleted control line; the road surface is derived by code and its "
                       "heights are the generator's, so this is draped",
                  source="ParkPlan.highway_path()")
        ref.curve("coast_highway_control_raw", plan["highway_path_raw"], "roads", "highway_raw", drape=1.0,
                  bevel=BEVEL_WORLD * 0.5, note="the unfilleted control polyline", source="ParkPlan.highway_path_raw()")
        ref.curve("approach_road_centreline", plan["approach_road_points"], "roads", "approach", bevel=BEVEL_PARK * 2,
                  note="heights are ParkPlan's own (1:12 from the front road); ends in the interchange stub",
                  source="ParkPlan.approach_road_points() <- scenes/world/approach_roads_layout.tscn")
        fz = plan["FRONT_ROAD_Z"]
        fh = plan["FRONT_ROAD_HALF_X"]
        ref.curve("front_road_centreline", [(-fh, 0.0, fz), (fh, 0.0, fz)], "roads", "approach", bevel=BEVEL_PARK * 2,
                  source="ParkPlan.FRONT_ROAD_Z, FRONT_ROAD_HALF_X <- approach_roads_layout.tscn")
        for xk in plan["LOT_ENTRY_XS"]:
            ref.curve(f"lot_entry_x{int(xk):+d}", [(xk, 0.0, fz), (xk, 0.0, fz - 20.0)], "roads", "approach",
                      bevel=BEVEL_PARK, note="the lot entry's 20 m stub north of the front road, drawn as a direction only",
                      source="ParkPlan.LOT_ENTRY_XS")
        hj = plan["HIGHWAY_JUNCTION"]
        ref.marker("highway_junction", hj[0], plan["approach_crossing"][1], hj[1], "roads", "highway", size=30.0,
                   note="the diamond interchange: approach road over the highway", source="ParkPlan.HIGHWAY_JUNCTION, approach_crossing()")
        for st in plan["town_streets"]:
            ref.curve(f"street_{st['id']}", st["points"], "roads", "town", drape=1.0, bevel=BEVEL_PARK * 2,
                      note=f"width {st['width']:g} m, grade cap {st['grade']:g}", source="ParkPlan.town_streets()")

        # Coasts and water.
        for nm, key, far in (("coast_north_outline", "COAST_NORTH_OUTLINE", "COAST_NORTH_FAR_FROM"),
                             ("coast_south_outline", "COAST_SOUTH_OUTLINE", "COAST_SOUTH_FAR_FROM")):
            ref.curve(nm, [(q[0], sea_level + 0.3, q[1]) for q in plan[key]], "coast", "coast",
                      note=f"the generator's shoreline control; points from index {plan[far]} on are the far coast",
                      source=f"ParkPlan.{key}")
        ref.curve("coastal_creek", plan["rebuild_coastal_creek"], "coast", "creek", drape=0.5, bevel=BEVEL_PARK,
                  source="ParkPlan.rebuild_coastal_creek()")
        lf = plan["REBUILD_WORLD_LAND_FROM_X"]
        ref.rect("land_reserve", lf, plan["REBUILD_WORLD_LAND_TO_X"], plan["REBUILD_WORLD_LAND_FROM_Z"],
                 plan["REBUILD_WORLD_LAND_TO_Z"], sea_level, "coast", "envelope", bevel=BEVEL_WORLD * 0.5,
                 note="the land reserve the mainland generator fills", source="ParkPlan.REBUILD_WORLD_LAND_*")

        # Beyond the park: towns, range toe, cliffs.
        ref.curve("beach_town_outline", plan["BEACH_TOWN_OUTLINE"], "world_beyond", "town", closed=True, drape=1.0,
                  bevel=BEVEL_PARK * 2, source="ParkPlan.BEACH_TOWN_OUTLINE")
        ref.curve("north_town_outline", plan["north_town_outline"], "world_beyond", "town", closed=True, drape=1.0,
                  source="ParkPlan.north_town_outline()")
        ref.curve("range_toe_line", plan["range_toe_line"], "world_beyond", "range", drape=1.0, bevel=BEVEL_PARK * 2,
                  note="where the generator's rim range first rises above the ground", source="ParkPlan.range_toe_line()")
        for i, cl in enumerate(plan["WORLD_CLIFFS"]):
            ref.circle(f"world_cliff_{i}", cl["at"][0], cl["at"][1], cl["radius"], 0.0, "world_beyond", "cliff",
                       drape=1.0, n=32, note=f"height {cl['height']:g} m", source="ParkPlan.WORLD_CLIFFS")
    else:
        ref.missing += ["Plaza, anchors, pier, wheel, roads, coasts, towns, cliffs: no --plan given"]

    # The city package: footprints read off the mounted GLB.
    meshes = None
    if city_glb and os.path.exists(city_glb):
        for attempt in (1, 2):
            try:
                meshes = glb_meshes(city_glb)
                if not meshes:
                    raise ValueError("no mesh nodes")
                break
            except Exception as exc:  # the GLB may be rewritten mid-run; one retry
                print(f"world_terrain: reading {city_glb} failed on attempt {attempt}: {exc}")
                meshes = None
        if meshes is None:
            ref.missing.append(f"city GLB {os.path.relpath(city_glb, ROOT)} could not be read twice; footprints missing")
    if meshes:
        src = os.path.relpath(city_glb, ROOT)

        def footprint(nm, names, y, key, note=""):
            pts = [meshes[n] for n in names if n in meshes]
            if not pts:
                ref.missing.append(f"{nm}: none of {names} in {src}")
                return
            h = hull_xz(np.concatenate(pts))
            ref.curve(nm, [(q[0], y, q[1]) for q in h], "city", key, closed=True,
                      note=note or "convex hull of the mesh's plan footprint", source=f"{src}: {', '.join(n for n in names if n in meshes)}")

        footprint("city_peninsula_footprint", ["relocated_city_peninsula-col", "relocated_city_peninsula_beaches"], 0.5, "city",
                  "the city's own peninsula, as mounted; the masterplan has decided its approach spit becomes water")
        footprint("city_built_blocks_hull", [n for n in meshes if n.startswith("city_block_")], 1.0, "city")
        footprint("bridge_main_deck_footprint", ["bridge_main_deck"], 30.0, "city",
                  "the 410 m suspension span as mounted; decided to lengthen to about 720 m, not built")
        footprint("bridge_approach_footprint", ["city_highway_extension"], 1.0, "city")
        footprint("southern_city_foothills_footprint", ["southern_city_range_foothills-col"], 1.0, "city")
        for nm, mesh_name in (("city_bypass_centreline", "southern_city_bypass_centreline"),
                              ("coastal_highway_branch_centreline", "southern_coastal_highway_extension_centreline")):
            if mesh_name in meshes:
                pts = centreline_from_strip(meshes[mesh_name])
                ref.curve(nm, [(q[0], q[1] + 1.0, q[2]) for q in pts], "city", "highway",
                          note="paired strip vertices of the mounted centreline mesh, approximate", source=f"{src}: {mesh_name}")
            else:
                ref.missing.append(f"{nm}: {mesh_name} not in {src}")
        for nm in ("city_ferry_landing", "beach_town_ferry_landing", "bay_ferry_hull"):
            if nm in meshes:
                c = meshes[nm].mean(axis=0)
                ref.marker(f"{nm}_marker", float(c[0]), float(c[1]), float(c[2]), "city", "city", size=20.0, source=f"{src}: {nm}")
    elif not (city_glb and os.path.exists(city_glb)):
        ref.missing.append("city peninsula, bridge, bypass and coastal branch: city GLB not found")

    # The lagoon and waterfront: a proposal (P) on the entrance landscaping map, not in ParkPlan.
    if map_path and os.path.exists(map_path):
        src = os.path.relpath(map_path, ROOT)
        lake = svg_polys(map_path, "lake", ["The tidal lagoon"])
        front = svg_polys(map_path, "lakefront", ["Bluff-top walk", "Lagoon beach"])
        if "The tidal lagoon" in lake:
            pts, closed, title = lake["The tidal lagoon"]
            ref.curve("PROPOSAL_tidal_lagoon", [(q[0], sea_level, q[1]) for q in pts], "proposals", "proposal", closed=closed,
                      bevel=BEVEL_PARK * 2, note="(P) proposal for review, pass 18; sea level behind tide gates; not in ParkPlan", source=src)
        else:
            ref.missing.append(f"tidal lagoon polygon not found in {src}")
        for key, nm in (("Bluff-top walk", "PROPOSAL_lagoon_bluff_walk"), ("Lagoon beach", "PROPOSAL_lagoon_beach")):
            if key in front:
                pts, closed, title = front[key]
                y = sea_level + 0.35 if key == "Lagoon beach" else None
                if y is None:
                    ref.curve(nm, pts, "proposals", "proposal", closed=closed, drape=1.0, bevel=BEVEL_PARK,
                              note="(P) proposal; " + title[:120], source=src)
                else:
                    ref.curve(nm, [(q[0], y, q[1]) for q in pts], "proposals", "proposal", closed=closed, bevel=BEVEL_PARK,
                              note="(P) proposal; " + title[:120], source=src)
            else:
                ref.missing.append(f"{key} not found in {src}")
        ref.missing.append("entrance waterfront beyond the lagoon walk and beach (bathhouse, docks, boating centre): map proposals only, not drawn")
    else:
        ref.missing.append("tidal lagoon and entrance waterfront: not in ParkPlan and the map was not found")

    ref.missing += [
        "padded envelope: no pad value in any document; 50 m assumed here",
        "tunnel bores and portals: only the tunnel-lid ground cells are sampled; the bore geometry is the generator's",
        "north town harbour, lighthouse and headland: no ParkPlan source; the mounted range source holds them",
        "south bluff (SOUTH_BLUFF_Z 240..300, 20 m): a generator parameter without a drawn footprint",
        "seabed: none exists in the game; the shelf under open-sea cells is a placeholder",
        "the decided (not built) peninsula shoreline west of the highway's south end and the 720 m bridge: on the detailed world map, not in ParkPlan",
    ]


# --- scene -----------------------------------------------------------------

def make_material_terrain(name, attr):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 1.0
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = attr
    nt.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    m["kyt_review_material"] = attr
    return m


def make_material_water():
    m = bpy.data.materials.new("sea_level_water")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.12, 0.42, 0.72, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.15
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    m.diffuse_color = (0.12, 0.42, 0.72, 1.0)
    return m


def clear_previous(scene):
    """Remove what this tool built last time; keep everything else."""
    gone = 0
    for obj in list(bpy.data.objects):
        if obj.get("kyt_terrain") or obj.get("kyt_reference") or obj.get("kyt_water"):
            data = obj.data
            bpy.data.objects.remove(obj)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
            gone += 1
    for coll in list(bpy.data.collections):
        if coll.name.startswith("Reference_") and not coll.objects and not coll.children:
            bpy.data.collections.remove(coll)
    for m in list(bpy.data.materials):
        if (m.get("kyt_reference") or m.get("kyt_review_material") or m.name == "sea_level_water") and m.users == 0:
            bpy.data.materials.remove(m)
    return gone


def get_collection(scene, name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    return coll


def guard(replace):
    edited = [o.name for o in bpy.data.objects
              if o.type == "MESH" and o.get("kyt_terrain") and o.data.get("kyt_terrain_hash") not in (None, shape_hash(o.data))]
    if edited and not replace:
        logged = []
        for o in bpy.data.objects:
            if o.get("kyt_terrain") and o.get("kyt_edits"):
                logged += [f"{e.get('name')} ({e.get('script')})" for e in json.loads(o["kyt_edits"])]
        raise SystemExit("world_terrain: these terrain meshes were reshaped since the last build and would be lost: "
                         + ", ".join(sorted(edited))
                         + (". Logged authored edits (kyt_edits): " + "; ".join(logged) if logged else "")
                         + ". Run with --replace to build over them" + (", then run each edit script again." if logged else "."))
    return edited


def build(args):
    grids, up_sources, inside_out, manifest = load_manifest(args["manifest"], args.get("skip", ()), args.get("up_source", ()))
    plan = None
    if args.get("plan"):
        with open(args["plan"]) as f:
            plan = json.load(f)
    sea_level = plan["WATER_TOP"] if plan else -7.5
    out = args.get("out") or DEFAULT_OUT

    existed = os.path.exists(out)
    if existed:
        bpy.ops.wm.open_mainfile(filepath=out)
        replaced = guard(args.get("replace", False))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        replaced = []
    scene = bpy.context.scene
    scene.name = "world_terrain"
    units = scene.unit_settings
    units.system = "METRIC"
    units.scale_length = 1.0
    units.length_unit = "METERS"
    scene["kyt_axis_map"] = AXIS_MAP
    scene["kyt_axis_blender_from_godot"] = "(x, y, z)_blender = (x, -z, y)_godot"
    scene["kyt_axis_godot_from_blender"] = "(x, y, z)_godot = (x, z, -y)_blender"
    scene["kyt_sea_level_m"] = sea_level
    scene["kyt_plaza_datum_m"] = 0.0
    scene["kyt_built_by"] = "tools/blender/world_terrain.py"
    scene["kyt_manifest"] = os.path.relpath(os.path.abspath(args["manifest"]), ROOT)

    cleared = clear_previous(scene)
    terrain_coll = get_collection(scene, "Terrain")
    ref_coll = get_collection(scene, "Reference")
    ref_coll.hide_select = True
    water_coll = get_collection(scene, "Water")

    mat_height = make_material_terrain("terrain_height_shade", "height_shade")
    mat_owner = make_material_terrain("terrain_owner_colour", "owner_colour")

    report = {"grids": [], "lossless": [], "round_trip": [], "file": out, "replaced_edits": replaced,
              "cleared_objects": cleared, "sea_level_m": sea_level, "inside_out_meshes": sorted(inside_out),
              "up_sources": [u["name"] for u in up_sources], "dropped_grids": grids[0]["dropped"] if grids else []}
    loaded = []
    for g in grids:
        grid = load_grid(g["csv"], inside_out)
        grid["name"] = g["name"]
        grid["role"] = g["role"]
        loaded.append(grid)
    loaded = merge_aligned(loaded)
    report["merged"] = {g["name"]: g["merged_from"] for g in loaded if g.get("merged_from")}
    for k, v in report["merged"].items():
        print(f"world_terrain: merged {', '.join(v)} into one grid (aligned lattices, no seam)")
    ups = [load_grid(u["csv"], inside_out) for u in up_sources]
    for grid in loaded:
        apply_up_rays(grid, ups)
    all_min = [min(g["ux"][0] for g in loaded), min(g["uz"][0] for g in loaded)]
    all_max = [max(g["ux"][-1] for g in loaded), max(g["uz"][-1] for g in loaded)]
    obj, stats, seams, ordered = assemble_mesh("terrain_world", loaded, sea_level)
    obj.data.materials.append(mat_height)
    obj.data.materials.append(mat_owner)
    terrain_coll.objects.link(obj)
    objs = [obj]
    bpy.context.view_layer.update()
    chk = lossless_check(obj, ordered)
    rts = []
    for grid in ordered:
        rt = round_trip_check(grid)
        rt["grid"] = grid["name"]
        rts.append(rt)
    if chk["vertex_max_error_m"] > 1e-3 or chk["ray_max_error_m"] > 1e-3 or chk["ray_misses"]:
        raise SystemExit(f"world_terrain: the terrain is not lossless: {chk}")
    report["grids"].append(stats)
    report["lossless"].append(chk)
    report["round_trip"] = rts
    report["seams"] = seams
    for sm in seams:
        for pt in sm["patches"]:
            print(f"world_terrain: seam {pt['seam']}: {pt['boundary_vertices']} boundary samples, jump before max "
                  f"{pt['jump_before_max_m']:.2f} m (mean {pt['jump_before_mean_m']:.2f}), after {pt['jump_after_max_m']:.2f} m "
                  f"(connected), {pt['coarse_dropped']} coarse samples dropped")
        for nt in sm["holes"]:
            print(f"world_terrain: stitch: {nt}")
    print(f"world_terrain: terrain_world: {stats['vertices']} vertices, {stats['faces']} faces ({stats['ngons']} stitch triangles), "
          f"{stats['sampled']} sampled, {stats['placeholder_sea']} placeholder sea, {stats['top_from_upray']} tops from up rays "
          f"({stats['top_from_upray_interpolated']} interpolated), {stats['minus11_skirt_without_hidden_top']} -11 samples with no "
          f"hidden top; lossless vertex {chk['vertex_max_error_m']:.2e} m, ray {chk['ray_max_error_m']:.2e} m "
          f"({chk['ray_nudged']} nudged 2 mm, their error {chk['ray_nudged_max_error_m']:.2e} m, {chk['ray_misses']} misses, "
          f"{chk['dropped_under_patch']} coarse samples under patches); round trip max {max(r['max_error_m'] for r in rts):.2e} m")

    # The water plane, over the grids plus a margin.
    pad = 500.0
    wx0, wx1 = all_min[0] - pad, all_max[0] + pad
    wz0, wz1 = all_min[1] - pad, all_max[1] + pad
    me = bpy.data.meshes.new("sea_level_water")
    me.from_pydata([to_blender(wx0, sea_level, wz0), to_blender(wx1, sea_level, wz0),
                    to_blender(wx1, sea_level, wz1), to_blender(wx0, sea_level, wz1)], [], [(0, 3, 2, 1)])
    me.update()
    me.materials.append(make_material_water())
    water = bpy.data.objects.new("sea_level_water", me)
    water["kyt_water"] = True
    water["kyt_collision"] = "none"
    water["kyt_note"] = f"sea level, ParkPlan.WATER_TOP = {sea_level:g} m; the game's water is its own; this plane is for sculpting against"
    water_coll.objects.link(water)

    # Reference, draped on the coarsest grid (the first one, by convention the world).
    bpy.context.view_layer.update()
    base = objs[0]
    bvh = BVHTree.FromObject(base, bpy.context.evaluated_depsgraph_get())
    top = (report["grids"][0]["height_max"] or 500.0) + 100.0

    def sampler(x, z):
        hit = bvh.ray_cast(Vector((x, -z, top)), Vector((0.0, 0.0, -1.0)), 10000.0)
        return None if hit[0] is None else hit[0].z

    ref = Ref(ref_coll, sampler, sea_level)
    build_reference(scene, ref, plan, args.get("city_glb", DEFAULT_CITY_GLB), args.get("map", DEFAULT_MAP), sea_level)
    for sub in ref.subs.values():
        sub.hide_select = True
    report["reference_sourced"] = ref.sourced
    report["reference_missing"] = ref.missing

    # Notes inside the file.
    notes = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    notes.clear()
    notes.write(readme_text(report, grids, sea_level))

    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print(f"world_terrain: {'rebuilt' if existed else 'wrote'} {out}")
    return report, objs, water, (wx0, wx1, wz0, wz1)


def readme_text(report, grids, sea_level):
    lines = [
        "world_terrain_master.blend, built by tools/blender/world_terrain.py", "",
        f"Axes: {AXIS_MAP}.",
        f"Sea level: ParkPlan.WATER_TOP = {sea_level:g} m. Plaza datum: 0.00 m at the fountain.", "",
        "Terrain: one mesh per sampled grid, LOSSLESS against the game's collision at build time; the first grid is the world.",
        "Finer grids are patches over coarser ones: the coarse cells strictly under a patch (inset one coarse step) are cut,",
        "so the coarse mesh overlaps the patch edge by up to one cell and no vertex is interpolated.",
        "INSIDE-OUT RULE (interim): where the manifest lists a mesh as inside out, the vertex height is max(ground_y, up_y);",
        "top_from_upray flags it, ground_y_sampled keeps the probe's reading (-11 m there is the mesh's base cap, not ground).",
        "Vertex attributes: owner (int; kyt_owner_table on the object), placeholder_bathymetry, sampled, top_y, peels,",
        "height_shade and owner_colour (review colours). kyt_collision = trimesh: collision is derived at export.", "",
        "PLACEHOLDER BATHYMETRY: the game has no seabed. Open-sea cells carry a stand-in shelf falling",
        f"1:{int(1 / SHELF_SLOPE)} from the nearest sampled land, {SHELF_START_DEPTH:g} m to {SHELF_MAX_DEPTH:g} m under sea level. Not a decision.", "",
        "Reference: locked, never exported, kyt_collision = none. Flat plan lines are draped on the ground; their heights are a visual aid.",
        "The protected anchors NT-1 and NT-2, the Plaza and the park ground are locked reference; never reshape them.", "",
        "Grids:",
    ]
    for s in report["grids"]:
        lines.append(f"  {s['name']}: {s['vertices']} vertices from grids {s['grids']} (steps {s['step_m']} m), {s['sampled']} sampled, "
                     f"{s['placeholder_sea']} placeholder sea cells, {s['top_from_upray']} tops from up rays, {s['ngons']} stitch triangles")
    for sm in report.get("seams", []):
        for pt in sm["patches"]:
            lines.append(f"  seam {pt['seam']}: jump before {pt['jump_before_max_m']:.2f} m max, stitched (0 m)")
    lines += ["Grid files: " + ", ".join(os.path.relpath(g["csv"], ROOT) if g["csv"].startswith(ROOT) else g["csv"] for g in grids)]

    lines += ["", "Reference layers sourced:"] + [f"  {s}" for s in report["reference_sourced"]]
    lines += ["", "Missing (not invented):"] + [f"  {s}" for s in report["reference_missing"]]
    return "\n".join(lines) + "\n"


# --- renders (scratch; after the save, never saved) ------------------------

def render_views(folder, objs, water, bounds, report):
    """Scratch renders after the save: a camera and a sun that are never saved."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    try:
        scene.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
        bg.inputs[1].default_value = 1.0
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (math.radians(45.0), 0.0, math.radians(-120.0))
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0
    outputs = []

    def materials(index):
        for o in objs:
            o.data.polygons.foreach_set("material_index", np.full(len(o.data.polygons), index, dtype=np.int32))
            o.data.update()

    def shoot(name):
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        outputs.append(scene.render.filepath)

    def top_down(name, x0, x1, z0, z1, material_index=0, show_water=True, px=2400):
        """Orthographic, north up, over the Godot box x0..x1, z0..z1."""
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = to_blender(cx, 5000.0, cz)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            scene.render.resolution_x, scene.render.resolution_y = px, int(px * ez / ex)
        else:
            scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
        materials(material_index)
        water.hide_render = not show_water
        shoot(name)

    def oblique(name, eye, aim, lens=35.0, show_water=True):
        """Perspective from Godot `eye` (x, y, z) at Godot `aim`."""
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector(to_blender(*eye)), Vector(to_blender(*aim))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
        materials(0)
        water.hide_render = not show_water
        shoot(name)

    wx0, wx1, wz0, wz1 = bounds
    gx0, gx1, gz0, gz1 = wx0 + 500.0, wx1 - 500.0, wz0 + 500.0, wz1 - 500.0
    top_down("world_terrain_top_height.png", gx0, gx1, gz0, gz1, 0, True)
    top_down("world_terrain_top_owner.png", gx0, gx1, gz0, gz1, 1, False)
    oblique("world_terrain_oblique_park_coast.png", (-1500.0, 650.0, 1500.0), (60.0, 0.0, 150.0))
    # The south coast strip, highway to shore, looking north-east from over the bay.
    oblique("world_terrain_oblique_south_coast.png", (-900.0, 450.0, 2900.0), (300.0, 20.0, 1500.0), lens=40.0)
    # The city peninsula and the bridge reference, looking north-east.
    oblique("world_terrain_oblique_city_peninsula.png", (-1500.0, 500.0, 3500.0), (-400.0, 0.0, 2500.0), lens=40.0)

    # The former cut south of the city, close up: the city patch's south edge at
    # z 3000 against the 25 m lattice, top-down and oblique.
    top_down("world_terrain_closeup_city_south_seam_top.png", -1100.0, -200.0, 2750.0, 3350.0, 0, True, px=1800)
    oblique("world_terrain_closeup_city_south_seam.png", (-350.0, 260.0, 3450.0), (-650.0, 10.0, 2950.0), lens=35.0)

    # The former -11 m plate: before (the probe's ground_y) and after (the
    # up-ray tops), over the manifest's south slab box.
    flagged = [(o, np.array([v for v in range(len(o.data.vertices))])) for o in objs]
    saved = {}
    for o in objs:
        at = o.data.attributes.get("top_from_upray")
        gs = o.data.attributes.get("ground_y_sampled")
        if at is None or gs is None:
            continue
        flag = np.zeros(len(o.data.vertices), dtype=bool)
        at.data.foreach_get("value", flag)
        if not flag.any():
            continue
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        orig = np.empty(len(o.data.vertices))
        gs.data.foreach_get("value", orig)
        saved[o.name] = co.copy()
        before = co.reshape(-1, 3).copy()
        before[flag, 2] = orig[flag]
        o.data.vertices.foreach_set("co", before.ravel())
        o.data.update()
    px0, px1, pz0, pz1 = -1900.0, 2600.0, 2400.0, 6000.0
    if saved:
        top_down("world_terrain_plate_before_upray.png", px0, px1, pz0, pz1, 0, True, px=1800)
        for o in objs:
            if o.name in saved:
                o.data.vertices.foreach_set("co", saved[o.name])
                o.data.update()
        top_down("world_terrain_plate_after_upray.png", px0, px1, pz0, pz1, 0, True, px=1800)
    report["renders"] = outputs
    for pth in outputs:
        print(f"world_terrain: rendered {pth}")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = {"replace": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--replace":
            args["replace"] = True
            i += 1
            continue
        if a in ("--skip", "--up-source"):
            args.setdefault(a[2:].replace("-", "_"), []).append(argv[i + 1])
            i += 2
            continue
        if a in ("--manifest", "--plan", "--out", "--render", "--city-glb", "--map", "--report"):
            if i + 1 >= len(argv):
                raise SystemExit(f"world_terrain: {a} needs a value")
            args[a[2:].replace("-", "_")] = argv[i + 1]
            i += 2
            continue
        raise SystemExit(f"world_terrain: unknown argument {a}")
    if "manifest" not in args:
        raise SystemExit("world_terrain: --manifest <grids.json> is required")
    return args


def main():
    args = parse_args()
    report, objs, water, bounds = build(args)
    if args.get("render"):
        render_views(args["render"], objs, water, bounds, report)
    rep_path = args.get("report") or (os.path.join(args["render"], "world_terrain_report.json") if args.get("render") else None)
    if rep_path:
        with open(rep_path, "w") as f:
            json.dump(report, f, indent=1)
        print(f"world_terrain: report {rep_path}")
    print("world_terrain: missing (not invented):")
    for m in report["reference_missing"]:
        print(f"  - {m}")


if __name__ == "__main__":
    main()
