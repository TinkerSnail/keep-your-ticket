"""Phase 1 (Blender): sample a scratch copy of the world terrain master.

Ray-casts `terrain_world` on the 1 m design raster and the 5 m backdrop,
reads the master's vertices inside the design box (with `authored_edit`) and
the reference curves near the site. Opens only the copy it is given.
"""

import json
import os

import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from ht_site import FAR, NEAR, REF_CURVES


def curve_points(name):
    """(x, z, y) Godot points of a reference curve, or None."""
    o = bpy.data.objects.get(name)
    if o is None or o.type != "CURVE":
        return None
    mw = o.matrix_world
    out = []
    for sp in o.data.splines:
        pts = sp.points if len(sp.points) else sp.bezier_points
        for p in pts:
            c = mw @ Vector(p.co[:3])
            out.append((float(c[0]), float(-c[1]), float(c[2])))
    return out


def raster(bvh, box):
    xs = np.arange(box["x0"], box["x1"] + 1e-6, box["step"])
    zs = np.arange(box["z0"], box["z1"] + 1e-6, box["step"])
    H = np.full((len(zs), len(xs)), np.nan)
    down = Vector((0.0, 0.0, -1.0))
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            hit = bvh.ray_cast(Vector((float(x), float(-z), 2000.0)), down, 5000.0)
            if hit[0] is None:
                hit = bvh.ray_cast(Vector((float(x) + 1e-3, float(-z) + 1e-3, 2000.0)), down, 5000.0)
            if hit[0] is not None:
                H[j, i] = hit[0].z
    return xs, zs, H


def run(folder):
    obj = bpy.data.objects["terrain_world"]
    me = obj.data
    assert obj.matrix_world.is_identity, "terrain_world carries a transform"
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    nx, nz, NH = raster(bvh, NEAR)
    fx, fz, FH = raster(bvh, FAR)
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    aid = np.zeros(n, dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", aid)
    grid = np.zeros(n, dtype=np.int32)
    me.attributes["grid"].data.foreach_get("value", grid)
    X, Z = co[:, 0], -co[:, 1]
    box = (X >= NEAR["x0"]) & (X <= NEAR["x1"]) & (Z >= NEAR["z0"]) & (Z <= NEAR["z1"])
    idx = np.nonzero(box)[0]
    np.savez(os.path.join(folder, "ht_sample.npz"), nx=nx, nz=nz, NH=NH, fx=fx, fz=fz, FH=FH,
             v_idx=idx, v_x=X[idx], v_z=Z[idx], v_y=co[idx, 2], v_edit=aid[idx], v_grid=grid[idx])
    refs = {}
    for name in REF_CURVES:
        pts = curve_points(name)
        if pts:
            refs[name] = pts
    with open(os.path.join(folder, "ht_refs.json"), "w") as f:
        json.dump(refs, f)
    nan = int(np.isnan(NH).sum())
    print(f"hillside_terraces: sampled near {NH.shape} (nan {nan}), far {FH.shape}, "
          f"{len(idx)} master vertices in the box (edits {sorted(set(aid[idx].tolist()))}, grids {sorted(set(grid[idx].tolist()))}); "
          f"refs {sorted(refs)}")
