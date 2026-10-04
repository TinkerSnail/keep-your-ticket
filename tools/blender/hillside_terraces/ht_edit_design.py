"""Edit 6 (Blender): the D1 landform designed on the open master, sampled at its
vertices, and measured on the edited mesh.

The master is a 10 m lattice in the footprint, too coarse to carry a 9 m
street or an 8 x 7 m lot terrace, so the edit moves its vertices onto the
smooth 1:3 landform (the regrade with the streets held at their heights,
before the lots are levelled); the streets, the lot pads and the footprint go
in as reference curves for the earthworks layer."""

import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import ht_metrics_d as MD
from ht_load import Site
from ht_sample import curve_points, raster
from ht_geom import dist_to
from ht_site import FAR, HW_HALF, HW_VERGE, MEET, NEAR, REF_CURVES, SEA_Y
from ht_variant_d import formations, regrade, terraces

EPS = 0.05
HOLD_REACH = 14.1       # a 10 m cell's diagonal: vertices this far beyond the strip still have faces in it


def site_from(obj):
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    nx, nz, NH = raster(bvh, NEAR)
    fx, fz, FH = raster(bvh, FAR)
    refs = {n: curve_points(n) for n in REF_CURVES if curve_points(n)}
    return Site.from_arrays(nx, nz, NH, fx, fz, FH, refs)


def landform(site):
    """D1: the streets and their regrade (no lot terraces), snapped to today's ground under 5 cm."""
    base, els = formations("D1", site)
    S, owner, prot, _ = regrade(els, site, hold=HW_HALF + HW_VERGE + HOLD_REACH)
    pads = S.copy()
    lots = MD.lots(els, pads, owner, prot, site.X, site.Z)
    terraces(pads, lots, owner)
    S = np.where(np.abs(S - site.E) > EPS, S, site.E)
    return base, els, S, owner, prot, lots


def targets(co, S, site):
    """Each master vertex's target height (Godot) on the landform, and which vertices move."""
    X, Z = co[:, 0], -co[:, 1]
    i = np.round((X - NEAR["x0"]) / NEAR["step"]).astype(int)
    j = np.round((Z - NEAR["z0"]) / NEAR["step"]).astype(int)
    inside = (i >= 0) & (i < S.shape[1]) & (j >= 0) & (j < S.shape[0])
    on_cell = inside & (np.abs(X - (NEAR["x0"] + i * NEAR["step"])) < 1e-3) & (np.abs(Z - (NEAR["z0"] + j * NEAR["step"])) < 1e-3)
    tgt = co[:, 2].copy()
    ii, jj = np.clip(i, 0, S.shape[1] - 1), np.clip(j, 0, S.shape[0] - 1)
    new = S[jj, ii] + SEA_Y
    moved = inside & (np.abs(S[jj, ii] - site.E[jj, ii]) > EPS)
    assert not (moved & ~on_cell).any(), "a moving vertex is off the 1 m raster's cells"
    tgt[moved] = new[moved]
    return tgt, moved, (X, Z)


def fidelity(obj, els, moved_faces, hw_line):
    """How the edited 10 m mesh carries D1: deviation along each street and at the meeting point, mesh slopes."""
    me = obj.data
    me.update()
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def gy(x, z):
        h = bvh.ray_cast(Vector((float(x), float(-z), 2000.0)), Vector((0.0, 0.0, -1.0)), 6000.0)
        return float(h[0].z) - SEA_Y if h[0] is not None else float("nan")
    out = {}
    for e in els:
        if e["kind"] not in ("street", "head"):
            continue
        p = e["pts"][::2]
        d = np.array([gy(x, z) - h for (x, z), h in zip(p, e["h"][::2])])
        r = dist_to(hw_line, p[:, 0], p[:, 1])
        zones = {"free": r > HW_HALF + HW_VERGE + 14.1, "beside the strip (vertices held)": (r > HW_HALF + HW_VERGE) & (r <= HW_HALF + HW_VERGE + 14.1),
                 "under the highway": r <= HW_HALF + HW_VERGE}
        rec = {}
        for zn, m in zones.items():
            if m.any():
                rec[zn] = {"m": int(2 * m.sum()), "max_abs_m": round(float(np.nanmax(np.abs(d[m]))), 2),
                           "mean_abs_m": round(float(np.nanmean(np.abs(d[m]))), 2), "mesh_above_m": round(float(np.nanmax(d[m])), 2)}
        out[e["name"]] = rec
    out["meeting_point_m"] = round(gy(*MEET) - float(next(e for e in els if e["name"] == "meeting")["h"][0]), 2)
    nrm = np.empty(len(me.polygons) * 3)
    me.polygons.foreach_get("normal", nrm)
    nz = np.abs(nrm.reshape(-1, 3)[:, 2])
    slope = np.sqrt(np.maximum(1.0 - nz ** 2, 0.0)) / np.maximum(nz, 1e-6)
    inner, rim = moved_faces
    for key, sel in (("inside", inner), ("rim", rim)):
        if sel.any():
            k = int(np.argmax(np.where(sel, slope, -1)))
            c = me.polygons[k].center
            out[f"steepest_face_{key}"] = {"slope": round(float(slope[k]), 2), "at": [round(c.x, 1), round(-c.y, 1)]}
            out[f"faces_{key}_over_1_3"] = int((sel & (slope > 0.36)).sum())
            out[f"faces_{key}"] = int(sel.sum())
    return out


def moved_faces(me, moved):
    """Faces with every vertex moved (inside) and faces with some moved (the rim, where the edit meets today's mesh)."""
    n = len(me.polygons)
    loops = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("vertex_index", loops)
    start = np.empty(n, dtype=np.int64)
    total = np.empty(n, dtype=np.int64)
    me.polygons.foreach_get("loop_start", start)
    me.polygons.foreach_get("loop_total", total)
    mv = moved[loops].astype(np.int64)
    cnt = np.add.reduceat(mv, start)
    return cnt == total, (cnt > 0) & (cnt < total)
