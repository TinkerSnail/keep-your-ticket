"""Authored edit 4 on the world terrain master: the enlarged hill lakes (2026-10-02,
Christina: "let's finish the lakes"; the lakes can be much deeper and wider, they are in
uninhabited hills; K1 is the headwater lake above the Bridalveil-style falls, its outlet the
fall's lip; the lakes are managed reservoirs with sluice towers; no pumps).

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_edit_hill_lakes.py -- [--dry] [--undo] [--render <folder>]
        [--k1 R CAP] [--l0 R CAP]

Same logged, reversible pattern as edits 1-3 (they stay bit-identical and independently
undoable; the builder guard names all four; --undo restores exactly edit 4's vertices,
flags and colours and removes what it added).

Design: each lake keeps its SPILL ELEVATION and spill point (K1 +79.7 at (520,-410), L0
+92 at (660,110)) and the K-1 / L-1 reach geometry below it. The lake is widened by
EXCAVATING the gentler slopes around the natural basin (never by raising a rim, which
would move the spill): every vertex within R of the basin's centre whose natural ground
lies between the brim and brim + CAP, connected to the basin, is cut to a bowl surface
brim - 0.5 - d_in / 3 (1:3 shores), floored at brim - DEPTH; the basin floor is deepened
to the same floor. Vertices within 45 m of the spill, within 35 m of the downstream creek,
and any cell whose neighbour is a below-brim cell outside the basin (the downstream
valley) are never cut, so the rim stays above the brim all round except at the spill.
K2 (+119.9) is left as it is.
"""
import hashlib
import json
import math
import os
import sys
from collections import deque

import numpy as np

import bpy
from mathutils import Vector

EDIT_ID = 4
EDIT_NAME = "hill_lakes"
SEA = -7.5
LAKES = {
    "K1": {"centre": (600, -471), "brim": 79.7, "spill": (520, -410), "creek": [(480, -370), (440, -330), (400, -290), (360, -250)], "R": 300.0, "CAP": 25.0, "DEPTH": 35.0,
           "note": "K1, the headwater lake above the falls: spill +79.7 at (520,-410) is the fall's lip and the sluice tower's site (invert +74)"},
    "L0": {"centre": (730, 206), "brim": 92.0, "spill": (660, 110), "creek": [(610, 200), (560, 200), (500, 200)], "R": 280.0, "CAP": 25.0, "DEPTH": 35.0,
           "note": "L0, creek L's reservoir: spill +92 at (660,110), sluice tower invert +86"},
}
SHORE = 3.0
PROTECT_BOXES = {"Plaza floor": (-52, 52, -52, 52), "NT-1 and its bluff": (-80, -50, -20, 17), "entrance precinct": (-48, 48, 83, 228), "Boardwalk deck": (-108, -56, -230, 220),
                 "park program envelope": (-212, 222, -230, 220), "R14": (131, 164, 78, 142)}
PROTECT_ELLIPSES = {"NT-2 (+5 m)": (86, 0, 47, 41)}


def attr(me, name, dtype):
    out = np.zeros(len(me.vertices), dtype=dtype)
    me.attributes[name].data.foreach_get("value", out)
    return out


def vertex_hash(co, sel=None):
    return hashlib.sha1((co if sel is None else co[sel]).tobytes()).hexdigest()


def ref_curve(coll, name, pts3, colour, bevel, note, closed=False):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = 0
    m = bpy.data.materials.new(f"ref_{name}")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = colour
    nt.links.new(em.outputs[0], o_.inputs[0])
    m["kyt_reference"] = True
    cu.materials.append(m)
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts3) - 1)
    for i, (x, y, z) in enumerate(pts3):
        sp.points[i].co = (x, -z, y, 1.0)
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu)
    o["kyt_reference"] = True
    o["kyt_collision"] = "none"
    o["kyt_edit_id"] = EDIT_ID
    o["kyt_note"] = note
    o.hide_select = True
    coll.objects.link(o)
    return o


def water_plane(coll, name, pts_xz, level, note):
    me = bpy.data.meshes.new(name)
    verts = [(x, -z, level) for x, z in pts_xz]
    me.from_pydata(verts, [], [list(range(len(verts)))])
    me.update()
    # fill by ear-clipping triangulation: a concave shoreline as one n-gon renders across its bays
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="EAR_CLIP")
    bm.to_mesh(me)
    bm.free()
    me.update()
    m = bpy.data.materials.new(f"water_{name}")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.0, 0.45, 1.0, 1.0)
    nt.links.new(em.outputs[0], o_.inputs[0])
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    o["kyt_reference"] = True
    o["kyt_collision"] = "none"
    o["kyt_water_level"] = float(level)
    o["kyt_edit_id"] = EDIT_ID
    o["kyt_note"] = note
    o.hide_select = True
    coll.objects.link(o)
    return o


def outline_of(mask_xz, step=12.0):
    """A polygon of the lake's edge: the boundary cells ordered by angle about the centroid (good enough for a reference outline)."""
    pts = np.array(mask_xz)
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    bins = {}
    for p, a in zip(pts, ang):
        k = int((a + math.pi) / (2 * math.pi) * 72)
        r = math.hypot(p[0] - c[0], p[1] - c[1])
        if k not in bins or r > bins[k][0]:
            bins[k] = (r, p)
    return [tuple(bins[k][1]) for k in sorted(bins)]


def true_outline(X, Z, Hv, lk, radius=520.0, step=25.0):
    """The lake's shoreline at the brim as a contour of the lattice heights Hv (current or pre-edit) around the
    centre: marching squares at the brim on the 25 m world lattice, the loop that encloses the basin's centre."""
    cx, cz = lk["centre"]
    brim = lk["brim"]
    sel = np.nonzero((np.abs(X - cx) <= radius) & (np.abs(Z - cz) <= radius))[0]
    xs = np.unique(np.round(X[sel] / step) * step)
    zs = np.unique(np.round(Z[sel] / step) * step)
    H = np.full((len(zs), len(xs)), np.nan)
    ix = {v: i for i, v in enumerate(xs)}
    iz = {v: j for j, v in enumerate(zs)}
    for v in sel:
        xr, zr = round(X[v] / step) * step, round(Z[v] / step) * step
        if abs(X[v] - xr) < 1e-3 and abs(Z[v] - zr) < 1e-3:
            H[iz[zr], ix[xr]] = Hv[v]
    H = np.where(np.isnan(H), brim + 50.0, H)
    # flood the below-brim cells connected to the centre, through edges; the spill disc and the downstream creek band
    # are walls (the saddle is wider than one lattice cell, and every cell down the K-1 valley is below the brim)
    GX, GZ = np.meshgrid(xs, zs)
    wall = np.hypot(GX - lk["spill"][0], GZ - lk["spill"][1]) < 45.0
    for px_, pz_ in lk["creek"]:
        wall |= np.hypot(GX - px_, GZ - pz_) < 45.0
    below = (H < brim - 1e-6) & ~wall
    j0, i0 = int(np.argmin(np.abs(zs - cz))), int(np.argmin(np.abs(xs - cx)))
    lake = np.zeros_like(below)
    q = deque([(j0, i0)])
    lake[j0, i0] = True
    while q:
        j, i = q.popleft()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jj, ii = j + dj, i + di
            if 0 <= jj < len(zs) and 0 <= ii < len(xs) and below[jj, ii] and not lake[jj, ii]:
                lake[jj, ii] = True
                q.append((jj, ii))
    # marching squares on the field f = lake ? H : brim + 1 (so the contour hugs the connected lake only)
    F = np.where(lake, H, brim + 1.0)
    segs = []

    def interp(p, q_, fp, fq):
        t = (brim - fp) / (fq - fp) if fq != fp else 0.5
        return (p[0] + (q_[0] - p[0]) * t, p[1] + (q_[1] - p[1]) * t)
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            c = [(xs[i], zs[j]), (xs[i + 1], zs[j]), (xs[i + 1], zs[j + 1]), (xs[i], zs[j + 1])]
            f = [F[j, i], F[j, i + 1], F[j + 1, i + 1], F[j + 1, i]]
            inside = [v < brim for v in f]
            pts = []
            for k in range(4):
                a, b = k, (k + 1) % 4
                if inside[a] != inside[b]:
                    pts.append(interp(c[a], c[b], f[a], f[b]))
            if len(pts) == 2:
                segs.append((pts[0], pts[1]))
            elif len(pts) == 4:
                segs.append((pts[0], pts[1]))
                segs.append((pts[2], pts[3]))
    # link the segments into loops
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    adj = {}
    for a, b in segs:
        adj.setdefault(key(a), []).append(key(b))
        adj.setdefault(key(b), []).append(key(a))
    used = set()
    loops = []
    for start in adj:
        if start in used:
            continue
        loop = [start]
        used.add(start)
        prev, cur = None, start
        while True:
            nxt = [v for v in adj[cur] if v != prev and v not in used]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            used.add(cur)
            loop.append(cur)
        loops.append(loop)
    # the loop enclosing the centre (even-odd test), else the largest
    def encloses(loop, px_, pz_):
        inside_ = False
        m = len(loop)
        for k in range(m):
            x0, z0 = loop[k]
            x1, z1 = loop[(k + 1) % m]
            if (z0 > pz_) != (z1 > pz_) and x0 + (pz_ - z0) * (x1 - x0) / (z1 - z0) > px_:
                inside_ = not inside_
        return inside_
    best = [lp for lp in loops if len(lp) > 3 and encloses(lp, cx, cz)]
    loop = max(best or loops, key=len)
    area = abs(sum(loop[k][0] * loop[(k + 1) % len(loop)][1] - loop[(k + 1) % len(loop)][0] * loop[k][1] for k in range(len(loop)))) / 2.0
    return [(float(x), float(z)) for x, z in loop], float(area / 1e4)


def poly_area_ha(pts):
    return abs(sum(pts[k][0] * pts[(k + 1) % len(pts)][1] - pts[(k + 1) % len(pts)][0] * pts[k][1] for k in range(len(pts)))) / 2.0 / 1e4


def design_lake(key, lk, X, Z, co, grid_cell):
    """Vertex selection and target heights for one lake on the real mesh."""
    cx, cz = lk["centre"]
    brim, R, CAP, DEPTH = lk["brim"], lk["R"], lk["CAP"], lk["DEPTH"]
    n = len(X)
    near = np.hypot(X - cx, Z - cz) <= R + 60
    idx = np.nonzero(near)[0]
    # the natural basin: vertices below the brim connected to the centre (through below-brim neighbours within 40 m)
    sub = idx
    pos = np.stack([X[sub], Z[sub]], axis=1)
    below = co[sub, 2] < brim
    start = int(np.argmin(np.hypot(X[sub] - cx, Z[sub] - cz)))
    basin = np.zeros(len(sub), dtype=bool)
    basin[start] = True
    q = deque([start])
    while q:
        a = q.popleft()
        d = np.hypot(pos[:, 0] - pos[a, 0], pos[:, 1] - pos[a, 1])
        nb = np.nonzero((d <= 40.0) & below & ~basin)[0]
        for b in nb:
            # never cross the spill saddle: the spill disc is a wall for the basin search
            if math.hypot(pos[b, 0] - lk["spill"][0], pos[b, 1] - lk["spill"][1]) < 25.0:
                continue
            basin[b] = True
            q.append(b)
    low_out = below & ~basin
    excl = np.hypot(pos[:, 0] - lk["spill"][0], pos[:, 1] - lk["spill"][1]) < 45.0
    for px_, pz_ in lk["creek"]:
        excl |= np.hypot(pos[:, 0] - px_, pos[:, 1] - pz_) < 35.0
    inside = np.hypot(pos[:, 0] - cx, pos[:, 1] - cz) <= R
    cand = inside & (co[sub, 2] >= brim) & (co[sub, 2] <= brim + CAP) & ~excl
    # a candidate next to a below-brim outside cell would leak: drop it
    if low_out.any():
        lo = pos[low_out]
        for k in np.nonzero(cand)[0]:
            if np.min(np.hypot(lo[:, 0] - pos[k, 0], lo[:, 1] - pos[k, 1])) <= 40.0:
                cand[k] = False
    # connectivity of the cut to the basin
    lake = basin.copy()
    q = deque(np.nonzero(basin)[0].tolist())
    while q:
        a = q.popleft()
        d = np.hypot(pos[:, 0] - pos[a, 0], pos[:, 1] - pos[a, 1])
        for b in np.nonzero((d <= 40.0) & cand & ~lake)[0]:
            lake[b] = True
            q.append(b)
    # distance inside the lake's edge
    lake_idx = np.nonzero(lake)[0]
    out_pts = pos[~lake]
    din = np.array([np.min(np.hypot(out_pts[:, 0] - pos[k, 0], out_pts[:, 1] - pos[k, 1])) for k in lake_idx])
    T = brim - 0.5 - np.minimum(DEPTH, din / SHORE)
    cur = co[sub[lake_idx], 2]
    target = np.minimum(cur, T)
    target[excl[lake_idx]] = cur[excl[lake_idx]]   # the spill disc and the downstream creek band are never touched, basin floor included
    moved = target < cur - 1e-3
    sel_global = sub[lake_idx[moved]]
    cells = grid_cell[sub[lake_idx]]
    cut_m3 = float(((cur - target) * cells).sum())
    water_m3 = float(((brim - target) * cells).sum())
    area_ha = float(cells.sum() / 1e4)
    edge_pts = [tuple(pos[k]) for k in lake_idx if np.min(np.hypot(out_pts[:, 0] - pos[k, 0], out_pts[:, 1] - pos[k, 1])) <= 30.0]
    basin_pts = [tuple(pos[k]) for k in np.nonzero(basin)[0]]
    return {"sel": sel_global, "target": target[moved], "lake_global": sub[lake_idx], "area_ha": area_ha, "cut_m3": cut_m3, "storage_m3": water_m3,
            "floor": float(target.min()), "max_cut_m": float((cur - target).max()) if moved.any() else 0.0, "basin_area_ha": float(grid_cell[sub[basin]].sum() / 1e4),
            "edge": edge_pts, "basin_edge": basin_pts, "vertices": int(moved.sum())}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    undo = "--undo" in argv
    dry = "--dry" in argv
    render_dir = argv[argv.index("--render") + 1] if "--render" in argv else None
    for key in ("k1", "l0"):
        if f"--{key}" in argv:
            i = argv.index(f"--{key}")
            LAKES[key.upper()]["R"], LAKES[key.upper()]["CAP"] = float(argv[i + 1]), float(argv[i + 2])
    obj = bpy.data.objects.get("terrain_world")
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    aid = attr(me, "authored_edit", np.int32)
    pre = attr(me, "height_pre_edit", float)
    edits = json.loads(obj.get("kyt_edits", "[]"))
    if undo:
        sel = aid == EDIT_ID
        if not sel.any():
            raise SystemExit(f"{EDIT_NAME}: nothing to undo")
        co[sel, 2] = pre[sel]
        me.vertices.foreach_set("co", co.ravel())
        aid[sel] = 0
        me.attributes["authored_edit"].data.foreach_set("value", aid)
        if "height_shade_pre_edit4" in me.color_attributes:
            c = np.empty(n * 4)
            me.color_attributes["height_shade_pre_edit4"].data.foreach_get("color", c)
            cur = np.empty(n * 4)
            me.color_attributes["height_shade"].data.foreach_get("color", cur)
            c, cur = c.reshape(-1, 4), cur.reshape(-1, 4)
            cur[sel] = c[sel]
            me.color_attributes["height_shade"].data.foreach_set("color", cur.ravel())
            me.color_attributes.remove(me.color_attributes["height_shade_pre_edit4"])
        for o in list(bpy.data.objects):
            if o.get("kyt_edit_id") == EDIT_ID:
                data = o.data
                bpy.data.objects.remove(o)
                if data and data.users == 0:
                    (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.curves).remove(data)
        for o in bpy.data.objects:
            if o.get("kyt_edit4_hidden"):
                o.hide_render = False
                o.hide_viewport = False
                del o["kyt_edit4_hidden"]
        obj["kyt_edits"] = json.dumps([e for e in edits if e.get("id") != EDIT_ID])
        notes = bpy.data.texts.get("README")
        if notes:
            notes.write(f"\nAUTHORED EDIT {EDIT_ID} ({EDIT_NAME}) UNDONE on {int(sel.sum())} vertices.\n")
        me.update()
        bpy.ops.wm.save_mainfile()
        print(f"{EDIT_NAME}: undone on {int(sel.sum())} vertices and saved")
        return
    if "--replanes" in argv:
        X, Z = co[:, 0], -co[:, 1]
        h0 = vertex_hash(co)
        ref = bpy.data.collections["Reference"]
        ws = bpy.data.collections.get("Water_surfaces")
        rw = bpy.data.collections.get("Reference_water")
        out = {}
        for k, lk in LAKES.items():
            old = bpy.data.objects.get(f"water_{k}_enlarged")
            old_area = poly_area_ha([(v.co.x, -v.co.y) for v in old.data.vertices]) if old is not None else None
            outline, area_after = true_outline(X, Z, co[:, 2], lk)
            before, area_before = true_outline(X, Z, pre, lk)
            for nm in (f"water_{k}_enlarged", f"lake_{k}_outline_after", f"lake_{k}_outline_before"):
                o = bpy.data.objects.get(nm)
                if o is not None:
                    data = o.data
                    bpy.data.objects.remove(o)
                    if data.users == 0:
                        (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.curves).remove(data)
            water_plane(ws, f"water_{k}_enlarged", outline, lk["brim"], f"{lk['note']}; enlarged by edit 4 to {area_after:.1f} ha at the brim (true shoreline by marching squares, rebuilt 2026-10-02); WORKING ASSUMPTION: held at the brim and spilling")
            ref_curve(rw, f"lake_{k}_outline_after", [(x, lk["brim"] + 0.3, z) for x, z in outline], (0.0, 0.45, 1.0, 1.0), 1.5, f"{k} shoreline at the brim after edit 4 ({area_after:.1f} ha, true contour)", closed=True)
            ref_curve(rw, f"lake_{k}_outline_before", [(x, lk["brim"] + 0.3, z) for x, z in before], (0.6, 0.6, 0.6, 1.0), 1.0, f"{k} natural basin at the brim before edit 4 ({area_before:.1f} ha, true contour of height_pre_edit)", closed=True)
            out[k] = {"old_plane_ha": old_area, "new_plane_ha": area_after, "before_ha": area_before, "outline_points": len(outline)}
        co3 = np.empty(n * 3)
        me.vertices.foreach_get("co", co3)
        assert vertex_hash(co3) == h0, "a vertex moved"
        notes = bpy.data.texts.get("README")
        if notes:
            notes.write("\nEDIT 4 PLANES REBUILT (2026-10-02): water_K1_enlarged / water_L0_enlarged and the outline curves follow the true shoreline at the brim (marching squares on the lattice) and are filled by ear-clipping triangulation, not one n-gon; the angle-binned outlines overshot the shore. " + json.dumps(out) + "\n")
        bpy.ops.wm.save_mainfile()
        print(f"{EDIT_NAME}: replanes {json.dumps(out)}; vertex hash {h0} unchanged; cameras {[o.name for o in bpy.data.objects if o.type in ('CAMERA', 'LIGHT')]}; saved")
        return
    if any(e.get("id") == EDIT_ID for e in edits):
        raise SystemExit(f"{EDIT_NAME}: edit 4 is already applied; run with --undo first")
    X, Z = co[:, 0], -co[:, 1]
    grid = attr(me, "grid", np.int32)
    cell = np.select([grid == 0, grid == 1, grid == 2], [625.0, 100.0, 16.0], 16.0)
    designs = {k: design_lake(k, lk, X, Z, co, cell) for k, lk in LAKES.items()}
    sel = np.zeros(n, dtype=bool)
    target = co[:, 2].copy()
    for k, d in designs.items():
        sel[d["sel"]] = True
        target[d["sel"]] = d["target"]
    assert not (sel & (aid > 0)).any(), "edit 4 would touch an earlier edit's vertex"
    assert np.array_equal(pre[sel], co[sel, 2]), "height_pre_edit differs on an edit 4 vertex"
    # protected sets
    masks = {}
    for name, (x0, x1, z0, z1) in PROTECT_BOXES.items():
        masks[name] = (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
    for name, (cx, cz, rx, rz) in PROTECT_ELLIPSES.items():
        masks[name] = ((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2 <= 1.0
    hw = bpy.data.objects["coast_highway_centreline"]
    hwp = np.array([(p.co[0], -p.co[1]) for s in hw.data.splines for p in s.points])
    near_hw = np.zeros(n, dtype=bool)
    box = (X > 100) & (X < 1000) & (Z > -800) & (Z < 500)
    for v in np.nonzero(box)[0]:
        if np.min(np.hypot(hwp[:, 0] - X[v], hwp[:, 1] - Z[v])) <= 25.0:
            near_hw[v] = True
    masks["coast highway ground (25 m)"] = near_hw
    for k, lk in LAKES.items():
        m = np.zeros(n, dtype=bool)
        for px_, pz_ in [lk["spill"]] + lk["creek"]:
            m |= np.hypot(X - px_, Z - pz_) <= 30.0
        masks[f"{k} spill and downstream creek (30 m)"] = m
    overlap = {k: int((m & sel).sum()) for k, m in masks.items()}
    assert all(v == 0 for v in overlap.values()), f"edit 4 touches a protected set: {overlap}"
    hb = {k: vertex_hash(co, m) for k, m in masks.items()}
    hb["outside edit 4"] = vertex_hash(co, ~sel)
    for e in (1, 2, 3):
        hb[f"edit {e}"] = vertex_hash(co, aid == e)
    hb["whole mesh"] = vertex_hash(co)
    report = {"id": EDIT_ID, "name": EDIT_NAME, "script": "tools/blender/world_terrain_edit_hill_lakes.py", "params": {k: {"R": lk["R"], "CAP": lk["CAP"], "DEPTH": lk["DEPTH"]} for k, lk in LAKES.items()},
              "lakes": {k: {kk: v for kk, v in d.items() if kk not in ("sel", "target", "lake_global", "edge", "basin_edge")} for k, d in designs.items()},
              "vertices_moved": int(sel.sum()), "max_change_m": float((co[:, 2] - target)[sel].max()) if sel.any() else 0.0, "protected_overlap": overlap, "hashes_before": hb}
    print(f"{EDIT_NAME}: " + json.dumps(report["lakes"]))
    print(f"{EDIT_NAME}: vertices {report['vertices_moved']}, max change {report['max_change_m']:.1f} m, overlap {overlap}")
    if dry:
        return
    cur = np.empty(n * 4)
    me.color_attributes["height_shade"].data.foreach_get("color", cur)
    cur = cur.reshape(-1, 4)
    keep = me.color_attributes.new("height_shade_pre_edit4", "FLOAT_COLOR", "POINT")
    keep.data.foreach_set("color", cur.ravel())
    co[sel, 2] = target[sel]
    me.vertices.foreach_set("co", co.ravel())
    aid[sel] = EDIT_ID
    me.attributes["authored_edit"].data.foreach_set("value", aid)
    col = cur.copy()
    col[sel] = (0.3, 0.5, 0.8, 1.0)
    me.color_attributes["height_shade"].data.foreach_set("color", col.ravel())
    me.update()
    # water planes (replace edit 3's lake planes: hide them, restored by --undo) and outlines
    ref = bpy.data.collections["Reference"]
    ws = bpy.data.collections.get("Water_surfaces") or bpy.data.collections.new("Water_surfaces")
    if ws.name not in [c.name for c in ref.children]:
        ref.children.link(ws)
    rw = bpy.data.collections.get("Reference_water") or bpy.data.collections.new("Reference_water")
    if rw.name not in [c.name for c in ref.children]:
        ref.children.link(rw)
    for k, lk in LAKES.items():
        old = bpy.data.objects.get(f"water_K-L1" if k == "K1" else "water_L-L0")
        if old is not None:
            old.hide_render = True
            old.hide_viewport = True
            old["kyt_edit4_hidden"] = True
        d = designs[k]
        co_now = np.empty(n * 3)
        me.vertices.foreach_get("co", co_now)
        co_now = co_now.reshape(-1, 3)
        outline, area_after = true_outline(X, Z, co_now[:, 2], lk)
        before, area_before = true_outline(X, Z, pre, lk)
        water_plane(ws, f"water_{k}_enlarged", outline, lk["brim"], f"{lk['note']}; enlarged by edit 4 to {area_after:.1f} ha at the brim (true shoreline by marching squares), floor {d['floor']:.1f}, storage {d['storage_m3'] / 1e6:.2f} M m3; WORKING ASSUMPTION: held at the brim and spilling")
        ref_curve(rw, f"lake_{k}_outline_after", [(x, lk["brim"] + 0.3, z) for x, z in outline], (0.0, 0.45, 1.0, 1.0), 1.5, f"{k} shoreline at the brim after edit 4 ({area_after:.1f} ha, true contour)", closed=True)
        ref_curve(rw, f"lake_{k}_outline_before", [(x, lk["brim"] + 0.3, z) for x, z in before], (0.6, 0.6, 0.6, 1.0), 1.0, f"{k} natural basin at the brim before edit 4 ({area_before:.1f} ha, true contour of height_pre_edit)", closed=True)
    # verification
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    co2 = co2.reshape(-1, 3)
    ha = {k: vertex_hash(co2, m) for k, m in masks.items()}
    ha["outside edit 4"] = vertex_hash(co2, ~sel)
    for e in (1, 2, 3):
        ha[f"edit {e}"] = vertex_hash(co2, aid == e)
    ha["whole mesh"] = vertex_hash(co2)
    for k in hb:
        if k != "whole mesh":
            assert hb[k] == ha[k], f"protected set changed: {k}"
    report["hashes_after"] = ha
    report["protected_identical"] = True
    # rim check: ground 15 m outside the lake outline, all round, must be >= brim except near the spill
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    def gy(x, z):
        h = bvh.ray_cast(Vector((x, -z, 2000.0)), Vector((0, 0, -1)), 6000.0)
        return float(h[0].z) if h[0] is not None else float("nan")
    rims = {}
    for k, lk in LAKES.items():
        d = designs[k]
        lake_v = d["lake_global"]
        lm = np.zeros(n, dtype=bool)
        lm[lake_v] = True
        near = np.nonzero((np.hypot(X - lk["centre"][0], Z - lk["centre"][1]) <= lk["R"] + 80) & ~lm)[0]
        lows = []
        LX, LZ = X[lake_v], Z[lake_v]
        for v in near:
            if np.min(np.hypot(LX - X[v], LZ - Z[v])) <= 40.0 and co2[v, 2] < lk["brim"] and math.hypot(X[v] - lk["spill"][0], Z[v] - lk["spill"][1]) > 60.0:
                lows.append((round(float(X[v])), round(float(Z[v])), round(float(co2[v, 2]), 1)))
        rims[k] = {"method": "every non-lake vertex within 40 m of a lake vertex must stand at or above the brim, except within 60 m of the spill", "low_rim_vertices": lows, "holds": len(lows) == 0}
    report["rims"] = rims
    # spill flood path: the K-1 / L-1 lines down to the sea follow the existing creeks: sampled heights
    report["spill_paths"] = {k: [(px_, pz_, round(gy(px_, pz_), 1)) for px_, pz_ in [lk["spill"]] + lk["creek"]] for k, lk in LAKES.items()}
    report["cameras_or_lights"] = [o.name for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]
    edits.append({"id": EDIT_ID, "name": EDIT_NAME, "script": report["script"], "date": "2026-10-02", "vertices": int(sel.sum()),
                  "lakes": {k: {"area_ha": round(d["area_ha"], 1), "cut_m3": round(d["cut_m3"]), "storage_m3": round(d["storage_m3"]), "floor": round(d["floor"], 1)} for k, d in designs.items()},
                  "hash_before": hb["whole mesh"], "hash_after": ha["whole mesh"]})
    obj["kyt_edits"] = json.dumps(edits)
    notes = bpy.data.texts.get("README")
    if notes:
        notes.write(f"\nAUTHORED EDIT {EDIT_ID} ({EDIT_NAME}), {report['script']}, 2026-10-02: the hill lakes enlarged by excavation, spills unchanged.\n  " +
                    "; ".join(f"{k}: {d['area_ha']:.1f} ha (was {d['basin_area_ha']:.1f}), floor {d['floor']:.1f}, cut {d['cut_m3'] / 1e6:.2f} M m3, storage {d['storage_m3'] / 1e6:.2f} M m3" for k, d in designs.items()) +
                    f"; {int(sel.sum())} vertices, max change {report['max_change_m']:.1f} m. Water planes water_K1_enlarged / water_L0_enlarged (edit 3's lake planes hidden), outlines before/after in Reference_water. --undo restores exactly.\n")
    bpy.ops.wm.save_mainfile()
    out_dir = render_dir or os.path.dirname(bpy.data.filepath)
    with open(os.path.join(out_dir, "built_lakes_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(f"{EDIT_NAME}: hashes before {hb}")
    print(f"{EDIT_NAME}: hashes after {ha}")
    print(f"{EDIT_NAME}: rims {rims}; spill paths {report['spill_paths']}; cameras {report['cameras_or_lights']}")
    print(f"{EDIT_NAME}: applied, saved {bpy.data.filepath}; mesh {hb['whole mesh']} -> {ha['whole mesh']}")
    if render_dir:
        render(render_dir, obj, designs)


def render(folder, obj, designs):
    scene = bpy.context.scene
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.7854, 0.0, -2.0944)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0

    def shoot(name):
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        print(f"{EDIT_NAME}: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2000):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = (cx, -cz, 4000.0)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            scene.render.resolution_x, scene.render.resolution_y = px, int(px * ez / ex)
        else:
            scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
        shoot(name)

    def oblique(name, eye, aim, lens=35.0):
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector((eye[0], -eye[2], eye[1])), Vector((aim[0], -aim[2], aim[1]))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
        shoot(name)
    top_down("built_lakes_hills_top.png", 150.0, 1050.0, -850.0, 500.0)
    top_down("built_lakes_K1_top.png", 250.0, 950.0, -800.0, -150.0)
    top_down("built_lakes_L0_top.png", 400.0, 1050.0, -100.0, 500.0)
    oblique("built_lakes_K1_oblique.png", (200.0, 260.0, -100.0), (600.0, 60.0, -470.0), lens=35.0)
    oblique("built_lakes_L0_oblique.png", (350.0, 280.0, 500.0), (730.0, 70.0, 200.0), lens=35.0)
    oblique("built_lakes_K1_from_fall_lip.png", (515.0, 84.0, -404.0), (640.0, 70.0, -520.0), lens=28.0)


if __name__ == "__main__":
    main()
