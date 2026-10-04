"""Edit 7 (Blender): put the band, its heights and its triangulation together,
and give the new vertices their attributes."""

import json

import numpy as np

import bpy

import ht_metrics_d as MD
import ht_refine_mesh as RM
import ht_refine_region as RR
import ht_refine_surface as RS
from ht_edit_checks import attr, mesh_co
from ht_load import Site
from ht_sample import curve_points, raster
from ht_site import FAR, NEAR, REF_CURVES, SEA_Y
from ht_variant_d import formations, regrade, terraces

GRID_ID = 4
CUT_REACH = 14.1      # the leg down's stretch whose faces reached the strip: the walled cutting's, not regraded here
CUT_HALF = 8.0        # half the width left for that cutting (the street and its sidewalks, and a margin)
REVIEW = (0.09, 0.20, 0.05, 1.0)      # edit 6's review colour for ground D1 moved


def design(obj):
    me = obj.data
    co = mesh_co(me)
    aid = attr(me, "authored_edit", np.int32)
    pre = attr(me, "height_pre_edit", np.float32)
    co0 = co.copy()
    co0[aid == 6, 2] = pre[aid == 6]                     # the ground D1 was designed on: before edit 6
    bvh0 = RR.bvh_with(co0, me)
    refs = {n: curve_points(n) for n in REF_CURVES if curve_points(n)}
    nx, nz, NH = raster(bvh0, NEAR)
    fx, fz, FH = raster(bvh0, FAR)
    site = Site.from_arrays(nx, nz, NH, fx, fz, FH, refs)
    base, els = formations("D1", site)
    S0, own, prot, _ = regrade(els, site, hold=0.0)      # D1 as designed, without edit 6's hold
    pads = S0.copy()
    lots = MD.lots(els, pads, own, prot, site.X, site.Z)
    terraces(pads, lots, own)
    bvh = RR.BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    _, _, MH = raster(bvh, NEAR)
    M = MH - SEA_Y                                       # today's mesh (after edit 6), over the sea
    X, Z = co[:, 0], -co[:, 1]
    i = np.clip(np.round(X - NEAR["x0"]).astype(int), 0, S0.shape[1] - 1)
    j = np.clip(np.round(Z - NEAR["z0"]).astype(int), 0, S0.shape[0] - 1)
    inb = (X >= NEAR["x0"]) & (X <= NEAR["x1"]) & (Z >= NEAR["z0"]) & (Z <= NEAR["z1"])
    wanted = inb & (np.abs(S0[j, i] - (co[:, 2] - SEA_Y)) > 0.5)      # today's ground is not D1's there
    P, faces = RR.band(me, co, wanted, site.hw_line)
    loops, fset = RR.outline(me, faces)
    assert len(loops) == 1, f"the band's outline is {len(loops)} loops"
    loop = loops[0]
    tris = RR.old_triangles(me, fset)
    bm_mask = RS.band_mask(me, faces, S0.shape)
    leg = next(e for e in els if e["name"] == "leg down (street)")
    r_leg = RR.dist_to(site.hw_line, leg["pts"][:, 0], leg["pts"][:, 1])
    near_hw = leg["pts"][r_leg <= RR.STRIP + CUT_REACH]
    cut = bm_mask & (RR.dist_to(near_hw, site.X, site.Z) <= CUT_HALF) if len(near_hw) > 1 else np.zeros(S0.shape, dtype=bool)
    T = RS.field(S0, own, M, bm_mask, site.X, site.Z, site.hw_line, cut)
    loop_xz = [(X[v], Z[v]) for v in loop]
    latt = RS.lattice(loop_xz, site.hw_line)
    latt_h = RS.sample(T, latt) + SEA_Y
    zs = [z for _, z in loop_xz]
    edge = RS.strip_edge(site.hw_line, min(zs), max(zs))

    def today(x, z):
        return RR.ground(bvh, x, z)
    pl, ring, poly = RM.build(co, loop, tris, edge, latt, latt_h, today, site.hw_line)
    tri_ids = RM.triangulate(pl, ring, poly, today)
    today_at_new = np.array([today(x, z) if o < 0 else np.nan for (x, z), o in zip(pl.xz, pl.orig)])
    today_at_new = today_at_new[np.array(pl.orig) < 0]
    return {"S0": S0, "lots": lots, "hw": site.hw_line, "poly": poly, "faces": faces, "P": P, "plan": pl, "tris": tri_ids,
            "today_at_new": today_at_new, "leg": leg, "co": co}


def attributes(me, n0, d, eid, note, obj):
    """The new vertices: grid 4; authored_edit on those that left today's surface; their old ground in height_pre_edit;
    owner, kind and colours from the nearest original vertex (edit 6's review colour where D1 moved the ground)."""
    n = len(me.vertices)
    new_kind = [k for k, o in zip(d["plan"].kind, d["plan"].orig) if o < 0]
    lat = np.array([k == "lattice" for k in new_kind])
    co = mesh_co(me)
    X, Z = co[:, 0], -co[:, 1]
    src = np.nonzero((X[:n0] > X[n0:].min() - 15) & (X[:n0] < X[n0:].max() + 15) & (Z[:n0] > Z[n0:].min() - 15) & (Z[:n0] < Z[n0:].max() + 15))[0]
    near = np.array([src[int(np.argmin(np.hypot(X[src] - X[k], Z[src] - Z[k])))] for k in range(n0, n)])
    for name, values in (("grid", np.full(n - n0, GRID_ID)), ("authored_edit", np.where(lat, eid, 0)),
                         ("height_pre_edit", d["today_at_new"]), ("resampled_from_master", np.ones(n - n0)),
                         ("sampled", np.zeros(n - n0))):
        dt = me.attributes[name].data_type
        a = attr(me, name, {"INT": np.int32, "FLOAT": np.float32, "BOOLEAN": bool}[dt])
        a[n0:] = values
        me.attributes[name].data.foreach_set("value", a)
    for name in ("owner", "kind"):
        a = attr(me, name, np.int32)
        a[n0:] = a[near]
        me.attributes[name].data.foreach_set("value", a)
    for name in ("height_shade", "owner_colour"):
        c = np.empty(n * 4)
        me.color_attributes[name].data.foreach_get("color", c)
        c = c.reshape(-1, 4)
        c[n0:] = c[near]
        if name == "height_shade":
            c[n0:][lat] = REVIEW
        me.color_attributes[name].data.foreach_set("color", c.ravel())
    tbl = json.loads(obj.get("kyt_grid_table", "[]"))
    tbl.append(note)
    obj["kyt_grid_table"] = json.dumps(tbl)
    me.update()
