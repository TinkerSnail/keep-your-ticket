"""Authored edit 3 on the world terrain master: the park's water network (2026-10-01,
Christina: "let's do it"; recorded in park-rebuild-masterplan.md, "The park's water").

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_edit_water_network.py -- [--render <folder>] [--dry] [--undo]

What it does, in the same logged, reversible pattern as edits 1 and 2:
- TERRAIN (authored_edit = 3, small and exact): digs the five park ponds into their saucers
  (P3 at D6, P2 the Grove pond, P1a at D5, P1b at D4, D3) to the designed beds with 1:2 banks
  from the rim, and the 4 m shelf channel from the corner cascade to P3 (bed 1 m under the
  water line, 1:1 banks). Nothing else moves: the creeks follow the existing valleys, the
  culverts and ducts are underground, the cascades and weirs are later earthworks.
- WATER SURFACES: locked planes (kyt_collision none) at the designed levels for the hill
  lakes K1, L0, the tarn K2 and the five park ponds, each with a kyt_note.
- REFERENCE_WATER: a locked group with the whole network as curves in the colour key (azure
  surface water, darker azure at the invert for underground reaches), the spillways and
  flood paths, the D3 emergency overflow, the sluice towers and gates, the twelve springs
  and the E landing candidate.
- VERIFIES: protected vertex sets hash-identical (Plaza, NT-1, NT-2, the entrance precinct
  outside D3, the Boardwalk deck, the route surfaces, the Kiddieland rides, everything
  outside edit 3's set; edits 1 and 2 bit-identical), pond volumes against the design,
  water levels under the rims, flood paths traced on the edited mesh to the sea.
- LOGS to terrain_world["kyt_edits"] (the builder guard names it) and the in-file README.
- --undo restores exactly edit 3's vertices (height, flags, colours), removes everything it
  added and drops its log entry.

WORKING ASSUMPTIONS (flagged in the file and the report; Christina has not answered yet):
snowmelt case MEDIUM, hill lakes at their brims and spilling, the Grove pond spring-fed,
no pumps, the flume reading optional and not built.
"""
import hashlib
import json
import math
import os
import sys

import numpy as np

try:
    import bpy
    from mathutils import Vector
except ImportError:   # --sections runs under system Python (PIL)
    bpy = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world_terrain_water_network as WN   # noqa: E402  the design: reaches, ponds, lakes
import world_terrain_water_budget as WB    # noqa: E402  the springs

EDIT_ID = 3
EDIT_NAME = "water_network"
SEA = -7.5
ASSUMPTIONS = "snowmelt MEDIUM (15 km2, 400 mm); lakes at their brims and spilling; Grove pond spring-fed; no pumps; flume reading not built (Christina to confirm)"
PONDS = {r["id"]: r for r in WN.REACHES if r["kind"] == "pond" and r["id"] != "E"}
PONDS["P1a"] = dict(PONDS["P1a"], poly=[(152, 160), (189, 160), (189, 136), (152, 136)])   # shrunk to clear R14 (budget rework)
PONDS["P2"] = dict(PONDS["P2"], poly=[(-38, -136), (-14, -136), (-14, -100), (-38, -100)])    # the Grove pond stops at z -136: the mound rises beyond it (a 5.5 m cut otherwise)
LAKES = {r["id"]: r for r in WN.REACHES if r["kind"] == "lake" and r["id"] != "L-L1"}
SHELF = [r for r in WN.REACHES if r["id"] == "K-5"][0]
BANK = 2.0        # pond banks 1:2
CHANNEL_HALF = 2.0
PROTECT_BOXES = {"Plaza floor": (-52, 52, -52, 52), "NT-1 and its bluff": (-80, -50, -20, 17), "entrance precinct (outside D3)": (-48, 48, 83, 228),
                 "Boardwalk deck": (-108, -56, -230, 220), "R14 junior coaster": (131, 164, 78, 142)}
PROTECT_ELLIPSES = {"NT-2 (+5 m)": (86, 0, 47, 41), "R5 mini railway": (76.5, 107.8, 11.5, 9), "R6 tubs": (115.7, 120.2, 10, 10), "R7 carousel": (136, 67.5, 10, 10)}
ROUTES = {  # world x,z from the digest; 6 m either side is the protected surface
    "A": [(0, 219), (0, 162.1), (0, 137.2), (0, 104.7), (0, 67.5), (0, 34), (0, 18), (0, -18), (-1, -35), (-3, -52), (-6, -78.4), (-10, -104.7), (-13, -132.8), (-16, -150.9), (-30, -154.2), (-37, -172.3), (-31, -193.7), (-16, -203.6), (0, -195.4), (6, -174), (1, -155.8)],
    "B": [(-96, -68.5), (-96, 64.4), (-88, 70.6), (-82, 83), (-80, 101.6), (-75, 118.7), (-64, 128), (-53, 123.3), (-47, 110.9), (-48, 92.3)],
    "B north": [(-6, -78.4), (-22, -75), (-40, -68.5), (-44, -88), (-44, -111), (-44, -134), (-42, -161), (-42, -181), (-80, -205)],
    "C": [(-48, 92.3), (-58, 79.9), (-72, 89.2), (-78, 110.9), (-70, 138.8), (-52, 151.2), (-32, 145), (-18, 128), (-10, 107.8), (-22, 90.8), (-18, 67.5), (-13, 44), (-10, 28), (-12, 14)],
    "D": [(0, 104.7), (12, 98.5), (25, 89.2), (38, 79.9), (49, 76.8), (62, 56.6), (75, 51), (109.9, 58.2), (130.2, 78.3), (134.6, 104.7), (120, 131.1), (93.9, 143.4), (66.4, 138.8), (46, 120.2), (42, 98.5), (49, 76.8), (42, 55.1), (34, 39), (25, 25), (15, 14)],
    "E": [(18, 0), (46, 0), (48, -18), (55, -30), (70, -42), (90, -50), (108, -52), (118, -40), (122, -20), (112, 0), (120, 14), (119, 30), (108, 43), (91, 50), (74, 48), (58, 40), (49, 26), (46, 0)],
    "F": [(-6, -78.4), (4, -101.4), (20, -131.1), (47, -152.5), (78.1, -164.1), (109.1, -157.5), (136.1, -137.7), (155, -108), (160.4, -68.5), (118, -42), (107, -30), (94, -50), (119.9, -61.9), (98.3, -73.4), (71.3, -81.7), (45.7, -71.8), (20, -56.9), (-1, -61.9), (-6, -78.4)],
}
ROUTE_HALF = 6.0


def attr(me, name, dtype):
    out = np.zeros(len(me.vertices), dtype=dtype)
    me.attributes[name].data.foreach_get("value", out)
    return out


def vertex_hash(co, sel=None):
    return hashlib.sha1((co if sel is None else co[sel]).tobytes()).hexdigest()


def inside_poly(x, z, poly):
    inside = False
    m = len(poly)
    for i in range(m):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % m]
        if (z0 > z) != (z1 > z) and x0 + (z - z0) * (x1 - x0) / (z1 - z0) > x:
            inside = not inside
    return inside


def dist_to_poly_edge(x, z, poly):
    best = 1e9
    m = len(poly)
    for i in range(m):
        a, b = np.array(poly[i]), np.array(poly[(i + 1) % m])
        ab = b - a
        t = float(np.clip(np.dot(np.array([x, z]) - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1))
        best = min(best, float(np.linalg.norm(np.array([x, z]) - (a + ab * t))))
    return best


def dist_to_polyline(x, z, pts):
    best, tb = 1e9, 0.0
    s = 0.0
    total = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        ab = b - a
        L = float(np.linalg.norm(ab))
        t = float(np.clip(np.dot(np.array([x, z]) - a, ab) / max(L * L, 1e-9), 0, 1))
        d = float(np.linalg.norm(np.array([x, z]) - (a + ab * t)))
        if d < best:
            best, tb = d, (s + t * L) / max(total, 1e-9)
        s += L
    return best, tb


def protected_masks(X, Z):
    masks = {}
    for name, (x0, x1, z0, z1) in PROTECT_BOXES.items():
        m = (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
        if "entrance" in name:
            d3 = PONDS["D3"]["poly"]
            m &= ~np.array([inside_poly(x, z, d3) or dist_to_poly_edge(x, z, d3) < BANK * 2.0 for x, z in zip(X, Z)]) | ~m
            m = ((X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)) & ~np.array([inside_poly(x, z, d3) or (dist_to_poly_edge(x, z, d3) < 4.0) for x, z in zip(X, Z)])
        masks[name] = m
    for name, (cx, cz, rx, rz) in PROTECT_ELLIPSES.items():
        masks[name] = ((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2 <= 1.0
    park = (X >= -220) & (X <= 230) & (Z >= -240) & (Z <= 240)
    idx = np.nonzero(park)[0]
    rm = np.zeros(len(X), dtype=bool)
    for name, pts in ROUTES.items():
        for v in idx:
            if not rm[v] and dist_to_polyline(X[v], Z[v], pts)[0] <= ROUTE_HALF:
                rm[v] = True
    masks["routes A-F surfaces (6 m)"] = rm
    return masks


def ref_curve(coll, name, pts3, colour, bevel, note, closed=False, dashed=False):
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
    if dashed:
        # one spline per dash so the underground reaches read as dashed
        pts3 = list(pts3)
        for i in range(len(pts3) - 1):
            a, b = np.array(pts3[i]), np.array(pts3[i + 1])
            L = float(np.linalg.norm(b - a))
            n = max(1, int(L / 6.0))
            for k in range(0, n, 2):
                t0, t1 = k / n, min(1.0, (k + 1) / n)
                sp = cu.splines.new("POLY")
                sp.points.add(1)
                p0, p1 = a + (b - a) * t0, a + (b - a) * t1
                sp.points[0].co = (p0[0], -p0[2], p0[1], 1.0)
                sp.points[1].co = (p1[0], -p1[2], p1[1], 1.0)
    else:
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


def circle(cx, cz, r, n=48):
    return [(cx + r * math.cos(a), cz + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render_dir = argv[argv.index("--render") + 1] if "--render" in argv else None
    undo = "--undo" in argv
    dry = "--dry" in argv
    obj = bpy.data.objects.get("terrain_world")
    if obj is None:
        raise SystemExit(f"{EDIT_NAME}: no terrain_world in this file")
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    aid = attr(me, "authored_edit", np.int32) if "authored_edit" in me.attributes else np.zeros(n, dtype=np.int32)
    pre = attr(me, "height_pre_edit", float) if "height_pre_edit" in me.attributes else co[:, 2].copy()
    edits = json.loads(obj.get("kyt_edits", "[]"))

    if undo:
        sel = aid == EDIT_ID
        if not sel.any():
            raise SystemExit(f"{EDIT_NAME}: nothing to undo")
        co[sel, 2] = pre[sel]
        me.vertices.foreach_set("co", co.ravel())
        aid[sel] = 0
        me.attributes["authored_edit"].data.foreach_set("value", aid)
        if "height_shade_pre_edit3" in me.color_attributes:
            c = np.empty(n * 4)
            me.color_attributes["height_shade_pre_edit3"].data.foreach_get("color", c)
            cur = np.empty(n * 4)
            me.color_attributes["height_shade"].data.foreach_get("color", cur)
            c, cur = c.reshape(-1, 4), cur.reshape(-1, 4)
            cur[sel] = c[sel]
            me.color_attributes["height_shade"].data.foreach_set("color", cur.ravel())
            me.color_attributes.remove(me.color_attributes["height_shade_pre_edit3"])
        for o in list(bpy.data.objects):
            if o.get("kyt_edit_id") == EDIT_ID:
                data = o.data
                bpy.data.objects.remove(o)
                if data and data.users == 0:
                    (bpy.data.meshes if isinstance(data, bpy.types.Mesh) else bpy.data.curves).remove(data)
        for cname in ("Reference_water", "Water_surfaces"):
            c = bpy.data.collections.get(cname)
            if c is not None and len(c.objects) == 0:
                bpy.data.collections.remove(c)
        obj["kyt_edits"] = json.dumps([e for e in edits if e.get("id") != EDIT_ID])
        notes = bpy.data.texts.get("README")
        if notes:
            notes.write(f"\nAUTHORED EDIT {EDIT_ID} ({EDIT_NAME}) UNDONE on {int(sel.sum())} vertices.\n")
        me.update()
        bpy.ops.wm.save_mainfile()
        print(f"{EDIT_NAME}: undone on {int(sel.sum())} vertices and saved")
        return

    if "--fix-river" in argv:
        # 2026-10-02: the river centreline's first points lay on the highway's own course at the corner (the road was built in
        # the thalweg); they move to the valley side, 18 m north-west of the carriageway. Reference curves only, no vertex moves.
        h0 = vertex_hash(co)
        RIVER = [(318, -246), (285, -272), (245, -316), (200, -340), (160, -362), (128, -373), (80, -379), (0, -371), (-56, -389), (-80, -395), (-100, -400), (-120, -402), (-140, -402)]
        from mathutils.bvhtree import BVHTree as _B
        bvh_r = _B.FromObject(obj, bpy.context.evaluated_depsgraph_get())

        def ground_y(x, z):
            hit = bvh_r.ray_cast(Vector((x, -z, 1000.0)), Vector((0, 0, -1)), 5000.0)
            return float(hit[0].z) if hit[0] is not None else 0.0

        def offset_line(pts, off):
            outp = []
            for i, (x, z) in enumerate(pts):
                a = np.array(pts[max(0, i - 1)]); b = np.array(pts[min(len(pts) - 1, i + 1)])
                d = b - a; d = d / max(np.linalg.norm(d), 1e-9); nrm = np.array([-d[1], d[0]])
                outp.append((float(x + nrm[0] * off), float(z + nrm[1] * off)))
            return outp
        rw = bpy.data.collections["Reference_water"]
        for nm, off in (("water_K2_river_centreline", 0.0), ("water_K2_river_bank_N", -4.5), ("water_K2_river_bank_S", 4.5), ("water_K2_flood_extent_N", -25.0), ("water_K2_flood_extent_S", 25.0)):
            o = bpy.data.objects.get(nm)
            if o is None:
                continue
            pts = RIVER if off == 0.0 else offset_line(RIVER, off)
            sp = o.data.splines[0]
            o.data.splines.remove(sp)
            sp = o.data.splines.new("POLY")
            sp.points.add(len(pts) - 1)
            for i, (x, z) in enumerate(pts):
                sp.points[i].co = (x, -z, ground_y(x, z) + (0.4 if off == 0.0 else 0.3), 1.0)
            o["kyt_note"] = str(o.get("kyt_note", "")) + " | first points moved off the highway's course onto the valley side (2026-10-02)"
        co_chk = np.empty(n * 3)
        me.vertices.foreach_get("co", co_chk)
        assert vertex_hash(co_chk.reshape(-1, 3)) == h0, "a vertex moved"
        notes = bpy.data.texts.get("README")
        if notes:
            notes.write("\nREFERENCE FIX (2026-10-02): water_K2_river_* curves: the river's first points lay on the coast highway's course at the park's corner; moved 18 m onto the valley side. No vertex moved.\n")
        bpy.ops.wm.save_mainfile()
        print(f"{EDIT_NAME}: fix-river done; vertex hash {h0} unchanged; saved")
        return
    if any(e.get("id") == EDIT_ID for e in edits):
        raise SystemExit(f"{EDIT_NAME}: edit 3 is already applied (kyt_edits); run with --undo first")

    X, Z = co[:, 0], -co[:, 1]
    park = (X >= -260) & (X <= 260) & (Z >= -360) & (Z <= 360)
    masks = protected_masks(X, Z)
    prot_any = np.zeros(n, dtype=bool)
    for m_ in masks.values():
        prot_any |= m_
    idx = np.nonzero(park & ~prot_any)[0]   # protected surfaces are never in the dig set: the banks stop at them
    target = co[:, 2].copy()
    changed = np.zeros(n, dtype=bool)
    owner = np.zeros(n, dtype=np.int32)   # 1..5 ponds, 6 channel
    pond_ids = list(PONDS)
    for pi, pid in enumerate(pond_ids):
        p = PONDS[pid]
        poly, bed, level = p["poly"], p["bed"], p["level"]
        xs_ = [q[0] for q in poly]
        zs_ = [q[1] for q in poly]
        pad = (level + 0.3 - bed) * BANK + 1.0
        for v in idx:
            x, z = X[v], Z[v]
            if not (min(xs_) - pad <= x <= max(xs_) + pad and min(zs_) - pad <= z <= max(zs_) + pad):
                continue
            inside = inside_poly(x, z, poly)
            d = dist_to_poly_edge(x, z, poly)
            # the rim at level + 0.3 (freeboard) on the polygon edge; 1:2 banks inward to the bed
            t = max(bed, (level + 0.3) - d / BANK) if inside else (level + 0.3) + d / BANK
            if t < co[v, 2] - 1e-3:
                target[v] = t
                changed[v] = True
                owner[v] = pi + 1
    # the shelf channel: bed 1 m under the water line, 1:1 banks over 1 m beyond the 2 m half width
    wl0, wl1 = SHELF["wl"]
    for v in idx:
        x, z = X[v], Z[v]
        if not (40 <= x <= 160 and -240 <= z <= -190):
            continue
        d, t = dist_to_polyline(x, z, SHELF["pts"])
        wl = wl0 + (wl1 - wl0) * t
        bed = wl - 1.0
        if d <= CHANNEL_HALF:
            tt = bed
        elif d <= CHANNEL_HALF + 1.5:
            tt = bed + (d - CHANNEL_HALF)
        else:
            continue
        if tt < target[v] - 1e-3 and owner[v] == 0:
            target[v] = tt
            changed[v] = True
            owner[v] = 6
    sel = changed
    assert not (sel & (aid == 1)).any(), "edit 3 would touch an edit 1 vertex"
    assert not (sel & (aid == 2)).any(), "edit 3 would touch an edit 2 vertex"
    assert np.array_equal(pre[sel], co[sel, 2]), "height_pre_edit differs from the current height on an edit 3 vertex"
    overlap = {k: int((m & sel).sum()) for k, m in masks.items()}
    assert all(v == 0 for v in overlap.values()), f"edit 3 touches a protected set: {overlap}"
    hashes_before = {k: vertex_hash(co, m) for k, m in masks.items()}
    hashes_before["outside edit 3"] = vertex_hash(co, ~sel)
    hashes_before["edit 1 (blend_south_range)"] = vertex_hash(co, aid == 1)
    hashes_before["edit 2 (coast_extension_B)"] = vertex_hash(co, aid == 2)
    hashes_before["whole mesh"] = vertex_hash(co)
    grid = attr(me, "grid", np.int32)
    cell = np.select([grid == 0, grid == 1, grid == 2], [625.0, 100.0, 16.0], 16.0)
    volumes = {}
    for pi, pid in enumerate(pond_ids):
        m = owner == pi + 1
        volumes[pid] = {"vertices": int(m.sum()), "dug_m3": float(((co[m, 2] - target[m]) * cell[m]).sum()), "design_bed": PONDS[pid]["bed"], "level": PONDS[pid]["level"],
                        "deepest_cut_m": float((co[m, 2] - target[m]).max()) if m.any() else 0.0, "cell_m2": sorted(set(cell[m].tolist()))}
    mch = owner == 6
    volumes["K-5 shelf channel"] = {"vertices": int(mch.sum()), "dug_m3": float(((co[mch, 2] - target[mch]) * cell[mch]).sum()), "deepest_cut_m": float((co[mch, 2] - target[mch]).max()) if mch.any() else 0.0}
    report = {"id": EDIT_ID, "name": EDIT_NAME, "script": "tools/blender/world_terrain_edit_water_network.py", "assumptions": ASSUMPTIONS, "vertices_moved": int(sel.sum()),
              "max_change_m": float((co[:, 2] - target)[sel].max()) if sel.any() else 0.0, "volumes": volumes, "protected_overlap": overlap, "hashes_before": hashes_before}
    for k in ("vertices_moved", "max_change_m", "volumes", "protected_overlap"):
        print(f"{EDIT_NAME}: {k}: {json.dumps(report[k])[:600]}")
    if dry:
        return

    # colours before, for the undo
    cur = np.empty(n * 4)
    me.color_attributes["height_shade"].data.foreach_get("color", cur)
    cur = cur.reshape(-1, 4)
    keep = me.color_attributes.new("height_shade_pre_edit3", "FLOAT_COLOR", "POINT")
    keep.data.foreach_set("color", cur.ravel())
    # apply
    co[sel, 2] = target[sel]
    me.vertices.foreach_set("co", co.ravel())
    aid[sel] = EDIT_ID
    if "authored_edit" not in me.attributes:
        me.attributes.new("authored_edit", "INT", "POINT")
    me.attributes["authored_edit"].data.foreach_set("value", aid)
    if "height_pre_edit" not in me.attributes:
        me.attributes.new("height_pre_edit", "FLOAT", "POINT")
        me.attributes["height_pre_edit"].data.foreach_set("value", pre)
    col = cur.copy()
    col[sel] = (0.35, 0.55, 0.85, 1.0)
    me.color_attributes["height_shade"].data.foreach_set("color", col.ravel())
    me.update()

    # --- water surfaces
    ref = bpy.data.collections["Reference"]
    ws = bpy.data.collections.get("Water_surfaces") or bpy.data.collections.new("Water_surfaces")
    if ws.name not in [c.name for c in ref.children]:
        ref.children.link(ws)
    ws.hide_select = True
    for lid, lk in LAKES.items():
        r = math.sqrt(lk["area_ha"] * 1e4 / math.pi)
        water_plane(ws, f"water_{lid}", circle(lk["centre"][0], lk["centre"][1], r), lk["level"], lk["name"] + f" | WORKING ASSUMPTION: at the brim and spilling ({ASSUMPTIONS})")
    for pid, p in PONDS.items():
        water_plane(ws, f"water_{pid}", p["poly"], p["level"], p["name"] + (" | spring-fed (working assumption)" if pid == "P2" else ""))
    # --- reference curves
    rw = bpy.data.collections.get("Reference_water") or bpy.data.collections.new("Reference_water")
    if rw.name not in [c.name for c in ref.children]:
        ref.children.link(rw)
    rw.hide_select = True
    AZ = (0.0, 0.45, 1.0, 1.0)
    AZD = (0.0, 0.28, 0.65, 1.0)
    for r in WN.REACHES:
        if r["kind"] in ("lake", "pond"):
            continue
        nm = f"water_{r['id']}"
        k = len(r["pts"])
        if r["kind"] == "duct":
            pts3 = [(x, r["invert"][0] + (r["invert"][1] - r["invert"][0]) * i / max(1, k - 1), z) for i, (x, z) in enumerate(r["pts"])]
            ref_curve(rw, nm, pts3, AZD, 0.8, r["name"] + " | UNDERGROUND, drawn at the invert; regulated baseflow only", dashed=True)
        else:
            pts3 = [(x, r["wl"][0] + (r["wl"][1] - r["wl"][0]) * i / max(1, k - 1) + 0.3, z) for i, (x, z) in enumerate(r["pts"])]
            ref_curve(rw, nm, pts3, AZ if r["kind"] != "cascade" else (0.0, 0.3, 0.9, 1.0), 1.5 if r["kind"] != "creek" else 1.2, r["name"])
    extras = [
        ("water_P3_spillway", [(30, -0.1, -200), (0, -0.2, -215), (-40, -0.5, -215), (-80, -3.0, -205), (-108, -7.2, -205)], "P3 spillway: weir -0.1 on the west bank, flood path west along the shelf to the Boardwalk's north end and the sea"),
        ("water_D3_emergency_overflow", [(-32, -1.2, 174), (-60, -2.0, 172), (-88, -6.5, 170)], "D3 emergency overflow: weir -0.1 into a 0.6 m pipe west to the shore band at (-88,170); drawn at the invert"),
        ("water_L_fork_sidespill", [(265, 9.6, 228), (255, 9.3, 240)], "L fork side weir: the creek's surplus returns to the main stem; sluice 0.5 x 0.5 m caps the Kiddieland chain at 0.2 m3/s"),
        ("water_K_takeoff_sidespill", [(300, 9.4, -230), (290, 9.3, -242)], "K take-off side weir: surplus returns to the main stem; sluice 0.6 x 0.6 m caps the park chain at 0.3 m3/s"),
    ]
    for nm, pts3, note in extras:
        ref_curve(rw, nm, pts3, AZ, 1.0, note, dashed=("overflow" in nm))
    # K as the beefy river (Christina 2026-10-01): centreline on the valley floor 18 m north of the coast highway's centreline, banks +-4.5 m, flood extent +-25 m; reference only, no terrain cut in this edit
    RIVER = [(300, -232), (280, -254), (240, -294), (200, -340), (160, -362), (128, -373), (80, -379), (0, -371), (-56, -389), (-80, -395), (-100, -400), (-120, -402), (-140, -402)]
    def ground_y(x, z):
        hit = bvh_r.ray_cast(Vector((x, -z, 1000.0)), Vector((0, 0, -1)), 5000.0)
        return float(hit[0].z) if hit[0] is not None else 0.0
    from mathutils.bvhtree import BVHTree as _B
    bvh_r = _B.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    cl = [(x, ground_y(x, z) + 0.4, z) for x, z in RIVER]
    ref_curve(rw, "water_K2_river_centreline", cl, AZ, 2.0, "K-2 the river: centreline from the take-off to the north cove on the valley floor's north side, 18 m north of the coast highway; 6 m bed, 1:2 banks 1.25 m high, 1.3 % then steeper to the mouth; mean 0.46 m3/s, spring 1.1, rain-on-snow design 13.6 m3/s at 0.75 m depth; the channel cut is for the earthworks pass")
    for side, off in (("north", -4.5), ("south", 4.5)), :
        pass
    def offset_line(pts, off):
        outp = []
        for i, (x, z) in enumerate(pts):
            a = np.array(pts[max(0, i - 1)]); b = np.array(pts[min(len(pts) - 1, i + 1)])
            d = b - a; d = d / max(np.linalg.norm(d), 1e-9); nrm = np.array([-d[1], d[0]])
            outp.append((float(x + nrm[0] * off), float(z + nrm[1] * off)))
        return outp
    for nm, off, note in (("water_K2_river_bank_N", -4.5, "K-2 river bank (north), top of the 1:2 bank, 1.25 m over the bed"), ("water_K2_river_bank_S", 4.5, "K-2 river bank (south), 18 m from the highway centreline leaves 13 m of verge"),
                          ("water_K2_flood_extent_N", -25.0, "K-2 flood extent (north), the 100-year assumption: 25 m either side"), ("water_K2_flood_extent_S", 25.0, "K-2 flood extent (south): stays north of the highway except at its two crossings; the +17 ridge and the sluice cap keep the park dry")):
        ref_curve(rw, nm, [(x, ground_y(x, z) + 0.3, z) for x, z in offset_line(RIVER, off)], (0.0, 0.3, 0.9, 1.0) if "bank" in nm else (0.3, 0.6, 1.0, 1.0), 0.8 if "bank" in nm else 0.5, note)
    for nm, (x, z), note in (("water_K_highway_bridge_takeoff", (330, -230), "coast highway crosses creek K-1 just above the take-off: bridge span 12 m, deck 1.5 m over the bed (rain-on-snow 13.6 m3/s at 0.75 m, freeboard 0.75 m)"),
                             ("water_K_highway_bridge_mouth", (-92, -398), "coast highway crosses the river K-2 at the cove: bridge span 14 m, deck 1.5 m over the bed; the river mouth opens into the north cove below"),
                             ("water_K_mouth_estuary", (-131, -400), "K's mouth at the north cove: a small river mouth with a gravel bar and a brackish pool behind it (plan language)")):
        ref_curve(rw, nm, [(x - 7, ground_y(x, z) + 0.6, z), (x + 7, ground_y(x, z) + 0.6, z)], (0.9, 0.3, 0.3, 1.0), 1.2, note)
    markers = [("water_sluice_tower_K1", (520, 79.7, -410), "K1 reservoir sluice tower at the spill saddle: 0.6 m valve, invert +74, usable 137 k m3 | ASSUMPTION: held at the brim"),
               ("water_sluice_tower_L0", (660, 92.0, 110), "L0 reservoir sluice tower at the spill: 0.6 m valve, invert +86, usable 173 k m3 | ASSUMPTION: held at the brim"),
               ("water_sluice_K_takeoff", (300, 8.9, -230), "take-off sluice gate 0.6 x 0.6 m, max 0.3 m3/s"), ("water_sluice_L_fork", (265, 9.3, 228), "fork sluice gate 0.5 x 0.5 m, max 0.2 m3/s"),
               ("water_sluice_siphon_intake", (96, 2.9, 165), "entrance siphon intake sluice at P1b: 0.1 m3/s, regulated baseflow only"),
               ("water_E_landing_basin_candidate", (-69, -7.2, 311), "E landing basin on the lagoon's north-west corner: CANDIDATE, not built")]
    for nm, (x, y, z), note in markers:
        ref_curve(rw, nm, [(x - 4, y + 0.5, z), (x + 4, y + 0.5, z)], (0.0, 0.45, 1.0, 1.0), 1.5, note)
    for name, (x, z), q, sy, feeds, plan in WB.SPRINGS:
        hit_y = None
        from mathutils.bvhtree import BVHTree
        bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
        hit = bvh.ray_cast(Vector((x, -z, 1000.0)), Vector((0, 0, -1)), 5000.0)
        hit_y = float(hit[0].z) if hit[0] is not None else 0.0
        ref_curve(rw, "spring_" + name.split()[0], circle(x, z, 2.5, 12), (0.35, 0.75, 0.6, 1.0), 0.6, f"{name}: {q * 0.4:.1f} / {q} / {q * 2:.1f} L/s (LOW/MED/HIGH) -> {feeds}; {plan} | springs are an assumption",
                  closed=True) if False else None
        cu_pts = [(x + 2.5 * math.cos(a), hit_y + 0.3, z + 2.5 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
        ref_curve(rw, "spring_" + name.split()[0], cu_pts, (0.35, 0.75, 0.6, 1.0), 0.6, f"{name}: {q * 0.4:.1f} / {q} / {q * 2:.1f} L/s (LOW/MED/HIGH) -> {feeds}; {plan} | springs are an assumption", closed=True)

    # --- verification on the edited mesh
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    co2 = co2.reshape(-1, 3)
    hashes_after = {k: vertex_hash(co2, m) for k, m in masks.items()}
    hashes_after["outside edit 3"] = vertex_hash(co2, ~sel)
    hashes_after["edit 1 (blend_south_range)"] = vertex_hash(co2, aid == 1)
    hashes_after["edit 2 (coast_extension_B)"] = vertex_hash(co2, aid == 2)
    hashes_after["whole mesh"] = vertex_hash(co2)
    for k in hashes_before:
        if k != "whole mesh":
            assert hashes_before[k] == hashes_after[k], f"protected set changed: {k}"
    report["hashes_after"] = hashes_after
    report["protected_identical"] = bool(all(hashes_before[k] == hashes_after[k] for k in hashes_before if k != "whole mesh"))
    # rims vs water levels and the flood-path trace on the edited mesh (4 m ray grid over the park)
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    gx = np.arange(-260.0, 261.0, 4.0)
    gz = np.arange(-360.0, 361.0, 4.0)
    G = np.full((len(gz), len(gx)), np.nan)
    for j, z in enumerate(gz):
        for i, x in enumerate(gx):
            hit = bvh.ray_cast(Vector((x, -z, 1000.0)), Vector((0, 0, -1)), 5000.0)
            if hit[0] is not None:
                G[j, i] = hit[0].z

    def g_at(x, z):
        return float(G[int(round((z - gz[0]) / 4)), int(round((x - gx[0]) / 4))])
    rims = {}
    built_levels = {}
    for pid, p in PONDS.items():
        ring = []
        poly = p["poly"]
        cx, cz = np.mean([q[0] for q in poly]), np.mean([q[1] for q in poly])
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            for t in np.linspace(0, 1, 10, endpoint=False):
                x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                vx, vz = x - cx, z - cz
                L = math.hypot(vx, vz)
                x5, z5 = x + vx / L * 5.0, z + vz / L * 5.0   # 5 m outside the rim
                ring.append((g_at(x5, z5), round(x5), round(z5)))
        rmin = min(ring)
        built = min(p["level"], rmin[0] - 0.2)
        if built < p["bed"] + 0.3:
            built = p["bed"] + 0.3   # the present rim holds nothing: a puddle on the bed until the pond is banked
        built_levels[pid] = built
        rims[pid] = {"rim_min_5m_outside": rmin[0], "rim_min_at": [rmin[1], rmin[2]], "rim_max": max(r[0] for r in ring), "design_level": p["level"], "built_level": built,
                     "rim_above_design_level": bool(rmin[0] >= p["level"] - 0.05), "berm_needed_m": round(max(0.0, p["level"] + 0.3 - rmin[0]), 2),
                     "note": "the water plane is built at the level the present rim holds; the berm (fill) to reach the design level is an earthworks item" if built < p["level"] else "rim holds the design level"}
    report["rims"] = rims
    for pid, built in built_levels.items():
        wp = bpy.data.objects.get(f"water_{pid}")
        if wp is not None and built < PONDS[pid]["level"]:
            for v in wp.data.vertices:
                v.co.z = built
            wp["kyt_water_level"] = float(built)
            wp["kyt_note"] = str(wp["kyt_note"]) + f" | BUILT at {built:+.2f}: the present rim (min {rims[pid]['rim_min_5m_outside']:+.2f} at {rims[pid]['rim_min_at']}) holds no more; a berm of {rims[pid]['berm_needed_m']} m reaches the design level {PONDS[pid]['level']:+.1f} (earthworks)"
    spill_pts = {"P3": (24, -200), "P2": (-42, -138), "P1a": (146, 152), "P1b": (112, 184), "D3": (-38, 174)}
    import world_terrain_hydrology as WH
    Gf = np.where(np.isnan(G), SEA - 20.0, G)
    Ffill = WH.priority_flood(Gf, Gf <= SEA + 0.05)
    G_raw = G
    G = Ffill   # descend on the filled surface so the trace does not stop in the next saucer
    boxes = {"Plaza": (-52, 52, -52, 52), "entrance": (-48, 48, 83, 228), "NT-1": (-80, -50, -20, 17), "Kiddieland rides": (131, 164, 78, 142)}
    traces = {}
    for pid, (x, z) in spill_pts.items():
        path = [(x, z, g_at(x, z))]
        seen = set()
        for _ in range(600):
            best = None
            for dx in (-4, 0, 4):
                for dz in (-4, 0, 4):
                    if dx == 0 and dz == 0:
                        continue
                    xx, zz = x + dx, z + dz
                    if not (gx[0] <= xx <= gx[-1] and gz[0] <= zz <= gz[-1]):
                        continue
                    h = g_at(xx, zz)
                    if h == h and (best is None or h < best[2]):
                        best = (xx, zz, h)
            if best is None or best[2] >= path[-1][2] - 1e-6 or (best[0], best[1]) in seen:
                break
            seen.add((best[0], best[1]))
            path.append(best)
            x, z = best[0], best[1]
            if best[2] <= SEA + 0.1 or xx <= gx[0] or zz >= gz[-1]:
                break
        hits = [nm for nm, (x0, x1, z0, z1) in boxes.items() if any(x0 <= px <= x1 and z0 <= pz <= z1 for px, pz, _ in path[1:])]
        if pid == "D3":
            hits = [h for h in hits if h != "entrance"]   # D3 itself sits in the precinct; its overflow pipe is the designed path
        traces[pid] = {"surface": "priority-flood filled 4 m grid of the edited mesh", "from": [float(x), float(z)], "end": [float(path[-1][0]), float(path[-1][1]), float(path[-1][2])], "steps": len(path), "reaches_sea_or_edge": bool(path[-1][2] <= SEA + 0.1 or len(path) > 2 and (path[-1][0] <= gx[0] + 4 or path[-1][1] >= gz[-1] - 4)),
                       "enters_protected": hits, "path_every_10": [(float(a), float(b), round(c, 1)) for a, b, c in path[::10]]}
    report["flood_traces"] = traces
    G = G_raw
    report["cameras_or_lights"] = [o.name for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]
    # log
    edits.append({"id": EDIT_ID, "name": EDIT_NAME, "script": report["script"], "date": "2026-10-01", "vertices": int(sel.sum()), "volumes": {k: round(v["dug_m3"]) for k, v in volumes.items()},
                  "assumptions": ASSUMPTIONS, "hash_before": hashes_before["whole mesh"], "hash_after": hashes_after["whole mesh"]})
    obj["kyt_edits"] = json.dumps(edits)
    notes = bpy.data.texts.get("README")
    if notes:
        notes.write(f"\nAUTHORED EDIT {EDIT_ID} ({EDIT_NAME}), {report['script']}, 2026-10-01: the park's water network (masterplan 'The park's water').\n"
                    f"  Ponds dug: " + ", ".join(f"{k} {round(v['dug_m3'])} m3 (bed {v.get('design_bed', '-')}, level {v.get('level', '-')})" for k, v in volumes.items()) +
                    f"; {int(sel.sum())} vertices, max change {report['max_change_m']:.2f} m. Water planes in Water_surfaces, the network in Reference_water (azure; darker dashed = underground at the invert).\n"
                    f"  WORKING ASSUMPTIONS: {ASSUMPTIONS}.\n  Protected sets hash-identical: {report['protected_identical']}. --undo restores exactly.\n")
    bpy.ops.wm.save_mainfile()
    with open(os.path.join(render_dir or os.path.dirname(bpy.data.filepath), "built_water_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    for k in ("hashes_before", "hashes_after", "protected_identical", "rims", "cameras_or_lights"):
        print(f"{EDIT_NAME}: {k}: {json.dumps(report[k])[:900]}")
    for pid, t in traces.items():
        print(f"{EDIT_NAME}: flood trace {pid}: from {t['from']} to {t['end']} in {t['steps']} steps, sea/edge {t['reaches_sea_or_edge']}, protected {t['enters_protected']}")
    print(f"{EDIT_NAME}: applied, saved {bpy.data.filepath}; mesh hash {hashes_before['whole mesh']} -> {hashes_after['whole mesh']}")
    if render_dir:
        render(render_dir, obj, G, gx, gz, co, co2, sel)


def render(folder, obj, G, gx, gz, co_before, co_after, sel):
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

    def top_down(name, x0, x1, z0, z1, px=2400):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = (cx, -cz, 3000.0)
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

    top_down("built_water_park_top.png", -260.0, 330.0, -300.0, 380.0)
    for pid, (cx, cz) in {"P1": (140, 150), "P2": (-28, -125), "P3": (54, -200), "D3": (-18, 174)}.items():
        top_down(f"built_water_pond_{pid}_top.png", cx - 60, cx + 60, cz - 60, cz + 60, px=1600)
    top_down("built_water_hill_lakes_top.png", 150.0, 1000.0, -800.0, 400.0)
    oblique("built_water_park_oblique_from_north.png", (60.0, 140.0, -520.0), (20.0, -2.0, 40.0), lens=35.0)
    oblique("built_water_grove_pond_oblique.png", (-120.0, 30.0, -200.0), (-26.0, -1.0, -125.0), lens=40.0)
    # sections as plots (system PIL is not in Blender): write the data for --sections
    secs = {}
    for name, (x0, z0, x1, z1) in {"grove_pond_z-125": (-80, -125, 30, -125), "D3_z174": (-60, 174, 30, 174), "P1_z152": (70, 152, 200, 152), "P3_z-200": (10, -200, 100, -200)}.items():
        pts = []
        for t in np.linspace(0, 1, 120):
            x, z = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
            j, i = int(round((z - gz[0]) / 4)), int(round((x - gx[0]) / 4))
            pts.append((x, z, float(G[j, i])))
        secs[name] = pts
    with open(os.path.join(folder, "built_water_sections.json"), "w") as f:
        json.dump(secs, f)


def sections(folder):
    from PIL import Image, ImageDraw
    secs = json.load(open(os.path.join(folder, "built_water_sections.json")))
    levels = {"grove_pond_z-125": -0.6, "D3_z174": -0.3, "P1_z152": 2.9, "P3_z-200": -0.2}
    for name, pts in secs.items():
        W, Hh, pad = 1400, 360, 50
        img = Image.new("RGB", (W, Hh + pad), (250, 250, 248))
        dr = ImageDraw.Draw(img)
        xs_ = [p[0] for p in pts]
        hs = [p[2] for p in pts]
        hmin, hmax = min(hs) - 1, max(hs) + 1
        sx = lambda x: pad + (x - xs_[0]) / (xs_[-1] - xs_[0]) * (W - 2 * pad)
        sy = lambda h: pad // 2 + Hh - 30 - (h - hmin) / (hmax - hmin) * (Hh - 40)
        dr.rectangle([pad, pad // 2, W - pad, pad // 2 + Hh - 30], outline=(120, 120, 120))
        for hv in range(int(hmin), int(hmax) + 1):
            dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
            dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
        dr.line([(sx(x), sy(h)) for x, _, h in pts], fill=(60, 60, 60), width=3)
        lv = levels[name]
        dr.line([pad, sy(lv), W - pad, sy(lv)], fill=(0, 115, 255), width=2)
        dr.text((pad + 6, pad // 2 + Hh - 24), f"built_water_section_{name}: the edited master along the line (x from {xs_[0]:.0f} to {xs_[-1]:.0f}), water level {lv:+.1f} in azure; heights Godot m", fill=(20, 20, 20))
        img.save(os.path.join(folder, f"built_water_section_{name}.png"))
        print(f"{EDIT_NAME}: wrote built_water_section_{name}.png")


if __name__ == "__main__":
    if "--sections" in sys.argv:
        sections(sys.argv[sys.argv.index("--sections") + 1])
    else:
        main()
