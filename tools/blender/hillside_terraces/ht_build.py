"""Phase 4 (Blender, on the scratch copy only): the designed ground as 1 m
patches in a hole cut in `terrain_world`, the streets as reference curves,
the hash checks, and the obliques from the town.

The hole removes FACES only, on the 10 m lattice, so not one master vertex
moves; each patch's rim samples the master's own edges, so it closes the hole
exactly. The scratch copy is saved with the patches (hidden but today's)
before any camera or light exists; the renders come after and are not saved."""

import hashlib
import json
import os

import bmesh
import bpy
import numpy as np

from ht_build_curves import curves_for, her_lines
from ht_site import HW_HALF, HW_VERGE, SEA_Y

LATTICE = 10.0
KEYS = ("today", "D1", "D2", "A", "B", "C")


def vhash(co, sel=None):
    a = co if sel is None else co[sel]
    return hashlib.sha1(np.ascontiguousarray(a).tobytes()).hexdigest()[:12]


def mesh_co(me):
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def hashes(obj, hw_line):
    me = obj.data
    co = mesh_co(me)
    aid = np.zeros(len(me.vertices), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", aid)
    X, Z = co[:, 0], -co[:, 1]
    near = (X > -100) & (X < 250) & (Z > 300) & (Z < 800)
    hw = np.zeros(len(X), dtype=bool)
    H = np.asarray(hw_line)
    for v in np.nonzero(near)[0]:
        hw[v] = np.min(np.hypot(H[:, 0] - X[v], H[:, 1] - Z[v])) <= HW_HALF + HW_VERGE + 10.0
    out = {"whole_mesh": vhash(co), "highway_band_vertices": vhash(co, hw), "highway_band_count": int(hw.sum())}
    for e in range(1, 6):
        out[f"edit_{e}"] = vhash(co, aid == e)
    return out, len(me.polygons)


def cut_hole(obj, r):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    x0, x1, z0, z1 = r
    gone = [f for f in bm.faces if all(x0 - 1e-4 <= v.co.x <= x1 + 1e-4 and z0 - 1e-4 <= -v.co.y <= z1 + 1e-4 for v in f.verts)]
    bmesh.ops.delete(bm, geom=gone, context="FACES_ONLY")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(gone)


# display (sRGB) colours of the designed classes, stored linear like the master's height_shade:
# street asphalt, steps, lot pads, walls (concrete), planted cut slopes (a darker green than the hill's)
CLASS_SRGB = {1: (0.33, 0.33, 0.35), 2: (0.55, 0.42, 0.30), 3: (0.86, 0.80, 0.66), 4: (0.80, 0.80, 0.78), 5: (0.36, 0.52, 0.26)}
CLASS_RGB = {k: tuple(c ** 2.2 for c in v) for k, v in CLASS_SRGB.items()}


def lattice_colours(obj, r):
    """The master's own height_shade at its 10 m lattice nodes over the hole, as a grid."""
    me = obj.data
    co = mesh_co(me)
    col = np.empty(len(me.vertices) * 4)
    me.color_attributes["height_shade"].data.foreach_get("color", col)
    col = col.reshape(-1, 4)
    x0, x1, z0, z1 = r
    nx, nz = int(round((x1 - x0) / LATTICE)) + 1, int(round((z1 - z0) / LATTICE)) + 1
    grid = np.full((nz, nx, 4), np.nan)
    i = np.round((co[:, 0] - x0) / LATTICE).astype(int)
    j = np.round((-co[:, 1] - z0) / LATTICE).astype(int)
    on = (i >= 0) & (i < nx) & (j >= 0) & (j < nz) & (np.abs(co[:, 0] - (x0 + i * LATTICE)) < 1e-3) & (np.abs(-co[:, 1] - (z0 + j * LATTICE)) < 1e-3)
    grid[j[on], i[on]] = col[on]
    assert not np.isnan(grid).any(), "the hole is not on the master's 10 m lattice"
    return grid


def patch(name, D, cls, r, step, lat, coll, mat):
    x0, x1, z0, z1 = r
    nz, nx = D.shape
    xs, zs = np.meshgrid(x0 + np.arange(nx) * step, z0 + np.arange(nz) * step)
    verts = np.c_[xs.ravel(), -zs.ravel(), (D + SEA_Y).ravel()]
    idx = np.arange(nz * nx).reshape(nz, nx)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    h = D.ravel()
    # split each cell along the diagonal whose ends differ least, so a wall crossing it on the slant is one clean step
    ac = np.abs(h[a] - h[c]) <= np.abs(h[b] - h[d])
    faces = np.r_[np.c_[a, b, c][ac], np.c_[a, c, d][ac], np.c_[a, b, d][~ac], np.c_[b, c, d][~ac]]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    fi, fj = (xs - x0) / LATTICE, (zs - z0) / LATTICE
    i0 = np.clip(np.floor(fi).astype(int), 0, lat.shape[1] - 2)
    j0 = np.clip(np.floor(fj).astype(int), 0, lat.shape[0] - 2)
    tx, tz = (fi - i0)[..., None], (fj - j0)[..., None]
    base = (lat[j0, i0] * (1 - tx) + lat[j0, i0 + 1] * tx) * (1 - tz) + (lat[j0 + 1, i0] * (1 - tx) + lat[j0 + 1, i0 + 1] * tx) * tz
    base = base.reshape(-1, 4)
    c = cls.ravel()
    for k, rgb in CLASS_RGB.items():
        base[c == k] = (*rgb, 1.0)
    ca = me.color_attributes.new("height_shade", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", base.ravel())
    me.materials.append(mat)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob["kyt_note"] = "PROPOSAL (scratch copy only): hillside terraces along Christina's lines, 0.5 m patch; not in the master"
    ob["kyt_collision"] = "none"
    coll.objects.link(ob)
    return ob


def run(folder):
    obj = bpy.data.objects["terrain_world"]
    Z = np.load(os.path.join(folder, "ht_design.npz"))
    R = json.load(open(os.path.join(folder, "ht_report.json")))
    hw_line = R["hw_line"]
    before, nf = hashes(obj, hw_line)
    r = tuple(float(v) for v in Z["fine_rect"])
    lat = lattice_colours(obj, r)
    gone = cut_hole(obj, r)
    after, nf2 = hashes(obj, hw_line)
    assert before == after, f"a master vertex moved: {before} vs {after}"
    root = bpy.data.collections.new("Proposal_hillside_terraces")
    bpy.data.collections["Reference_proposals"].children.link(root)
    mat = obj.data.materials[0]
    objs = {}
    for k in KEYS:
        coll = bpy.data.collections.new(f"hillside_terraces_{k}")
        root.children.link(coll)
        H = Z["E"] if k == "today" else Z[f"D_{k}"]
        D = Z["fine_E"] if k == "today" else Z[f"fine_D_{k}"]
        cls = np.zeros(D.shape, dtype=np.int8) if k == "today" else Z[f"fine_cls_{k}"]
        step = float(Z[f"fine_step_{k}"])
        objs[k] = [patch(f"PROPOSAL_hillside_terraces_{k}_ground", D, cls, r, step, lat, coll, mat)]
        objs[k] += her_lines(coll, H, k)
        if k != "today":
            objs[k] += curves_for(coll, R["variants"][k], k)
    for k in KEYS:
        for o in objs[k]:
            o.hide_set(k != "today")
            o.hide_render = k != "today"
    assert not bpy.data.cameras and not bpy.data.lights
    bpy.ops.wm.save_mainfile()
    log = {"rect": r, "faces_removed": gone, "faces_before": nf, "faces_after": nf2, "hashes_before": before, "hashes_after": after,
           "saved": bpy.data.filepath}
    with open(os.path.join(folder, "ht_build.json"), "w") as f:
        json.dump(log, f, indent=1)
    print(f"hillside_terraces: hole {r} ({gone} faces), hashes equal {before == after}, saved {bpy.data.filepath}")
    import ht_render
    ht_render.run(objs, KEYS, R)
