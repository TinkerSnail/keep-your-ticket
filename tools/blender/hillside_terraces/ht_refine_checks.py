"""Edit 7's measures on the refined mesh: the strip's surface before and after,
the lots that now stand on regraded ground, the leg down, the slopes, and
whether any held vertex still carries a face."""

import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from ht_geom import dist_to, inside, rect
from ht_refine_surface import STRIP, sample
from ht_site import LOT_DEPTH, LOT_FRONT, SEA_Y


def caster(obj):
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def g(x, z):
        h = bvh.ray_cast(Vector((float(x), float(-z), 400.0)), Vector((0.0, 0.0, -1.0)), 1400.0)
        return float(h[0].z) - SEA_Y if h[0] is not None else float("nan")
    return g


def strip_points(poly, hw_line, step=0.7):
    """Points inside the band and inside the strip (not on its edge), to compare the surface before and after."""
    P = np.asarray(poly)
    xs = np.arange(P[:, 0].min(), P[:, 0].max(), step)
    zs = np.arange(P[:, 1].min(), P[:, 1].max(), step)
    GX, GZ = np.meshgrid(xs, zs)
    gx, gz = GX.ravel(), GZ.ravel()
    k = inside(P, gx, gz) & (dist_to(hw_line, gx, gz) < STRIP - 0.05)
    return np.c_[gx[k], gz[k]]


def lots_on_regrade(lots, g, S0, hw_line, tol=1.0, wall=2.0):
    """D1's lots whose ground on the refined mesh follows D1 (mean within `tol`) and levels with walls <= `wall`."""
    ok = []
    for lot in lots:
        q = np.array(rect(lot["c"], lot["t"], LOT_FRONT - 1.0, LOT_DEPTH - 1.0) + [tuple(lot["c"])])
        h = np.array([g(x, z) for x, z in q])
        d = sample(S0, q)
        flat = max(h.max() - h.mean(), h.mean() - h.min()) <= wall
        ok.append(bool(flat and abs(h.mean() - d.mean()) <= tol and not (dist_to(hw_line, q[:, 0], q[:, 1]) <= STRIP).any()))
    return ok


def pad(lot, g):
    """A lot's terrace height: the mean of the ground under it."""
    q = rect(lot["c"], lot["t"], LOT_FRONT - 1.0, LOT_DEPTH - 1.0) + [tuple(lot["c"])]
    return float(np.mean([g(x, z) for x, z in q]))


def profile(el, g, hw_line):
    p = el["pts"][::3]
    d = np.array([g(x, z) - h for (x, z), h in zip(p, el["h"][::3])])
    r = dist_to(hw_line, p[:, 0], p[:, 1])
    return [{"s": round(float(s), 0), "street": round(float(h), 1), "mesh_minus_street": round(float(dd), 2), "from_centreline": round(float(rr), 1)}
            for s, h, dd, rr in zip(el["s"][::3], el["h"][::3], d, r)]


def slopes(me, tag, hw_line):
    """Slopes of the new faces off the strip: steepest, and how many and how much area exceed 1:3."""
    n = len(me.polygons)
    t = np.zeros(n, dtype=np.int64)
    me.attributes[tag].data.foreach_get("value", t)
    nrm, cen, area = np.empty(n * 3), np.empty(n * 3), np.empty(n)
    me.polygons.foreach_get("normal", nrm)
    me.polygons.foreach_get("center", cen)
    me.polygons.foreach_get("area", area)
    nz = np.abs(nrm.reshape(-1, 3)[:, 2])
    cen = cen.reshape(-1, 3)
    sl = np.sqrt(np.maximum(1 - nz ** 2, 0)) / np.maximum(nz, 1e-6)
    new = t > 0
    off = new.copy()
    idx = np.nonzero(new)[0]
    off[idx] = dist_to(hw_line, cen[idx, 0], -cen[idx, 1]) > STRIP + 0.5
    k = int(np.argmax(np.where(off, sl, -1)))
    steep = off & (sl > 0.36)
    return {"faces_new": int(new.sum()), "faces_off_strip": int(off.sum()), "steepest": round(float(sl[k]), 2),
            "steepest_at": [round(float(cen[k, 0]), 1), round(float(-cen[k, 1]), 1)],
            "over_1_3_faces": int(steep.sum()), "over_1_3_m2": round(float(area[steep].sum())),
            "over_1_3_where": sorted({(int(round(cen[i, 0], -1)), int(round(-cen[i, 1], -1))) for i in np.nonzero(steep)[0]})[:40]}


def held_in_faces(me, P):
    used = np.zeros(len(me.vertices), dtype=bool)
    loops = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("vertex_index", loops)
    used[loops] = True
    return int((used[: len(P)] & P).sum())
