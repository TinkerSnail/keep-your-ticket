"""Edit 6's reference layer: `Reference_hillside`, locked curves for her lines,
the D1 street centrelines with their profiles, the meeting, the lot pads and
the regrade's footprint; everything tagged `kyt_edit_id` so --undo removes it."""

from collections import defaultdict

import numpy as np

import bpy

from ht_geom import bilinear, chaikin, rect, resample
from ht_site import DOWN, LINE1, LINE2, LOT_DEPTH, LOT_FRONT, MEET, NEAR, SEA_Y

COLL = "Reference_hillside"


def material(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba
    nt.links.new(em.outputs[0], out.inputs[0])
    m["kyt_reference"] = True
    return m


def curve(coll, edit_id, name, splines, rgba, bevel, note):
    """splines: lists of (x, height over the sea, z), each with a closed flag."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = 0
    m = material(f"ref_{name}", rgba)
    m["kyt_edit_id"] = edit_id
    cu.materials.append(m)
    for pts, closed in splines:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for k, (x, y, z) in enumerate(pts):
            sp.points[k].co = (float(x), float(-z), float(y + SEA_Y), 1.0)
        sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu)
    for k, v in (("kyt_reference", True), ("kyt_collision", "none"), ("kyt_edit_id", edit_id), ("kyt_note", note)):
        o[k] = v
    o.hide_select = True
    coll.objects.link(o)
    return o


def outline(mask, step=2):
    """The footprint's outer boundary: marching squares on the mask at `step` m, the longest joined loop."""
    m = mask[::step, ::step].astype(float)
    segs = []
    for j in range(m.shape[0] - 1):
        for i in range(m.shape[1] - 1):
            v = [m[j, i], m[j, i + 1], m[j + 1, i + 1], m[j + 1, i]]
            if min(v) == max(v):
                continue
            c = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            p = [((c[k][0] + c[(k + 1) % 4][0]) / 2, (c[k][1] + c[(k + 1) % 4][1]) / 2) for k in range(4) if v[k] != v[(k + 1) % 4]]
            if len(p) == 2:
                segs.append((p[0], p[1]))
            elif len(p) == 4:
                segs += [(p[0], p[1]), (p[2], p[3])]
    adj = defaultdict(list)
    for a, b in segs:
        adj[a].append(b)
        adj[b].append(a)
    seen, best = set(), []
    for start in list(adj):
        if start in seen:
            continue
        loop, cur, prev = [start], start, None
        seen.add(start)
        while True:
            nxt = [q for q in adj[cur] if q != prev and q not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) > len(best):
            best = loop
    return [(NEAR["x0"] + x * step * NEAR["step"], NEAR["z0"] + z * step * NEAR["step"]) for x, z in best]


def build(edit_id, els, S, moved, lots):
    ref = bpy.data.collections["Reference"]
    coll = bpy.data.collections.new(COLL)
    ref.children.link(coll)
    coll.hide_select = True
    on = lambda x, z, lift: float(bilinear(S, NEAR["x0"], NEAR["z0"], NEAR["step"], x, z)) + lift
    for nm, pl in (("line_1", LINE1 + [MEET]), ("line_2", LINE2 + [MEET]), ("leg_down", DOWN)):
        pts, _ = resample(pl, 2.0)
        curve(coll, edit_id, f"hillside_her_{nm}", [([(x, on(x, z, 0.6), z) for x, z in pts], False)], (0.9, 0.1, 0.1, 1.0), 0.35,
              "Christina's red line from her sketch on the beach town plan (2026-10-02), draped on the regraded ground")
    for e in els:
        if e["kind"] == "street":
            k = np.arange(0, len(e["s"]), 2)
            pts = [(e["pts"][i][0], e["h"][i], e["pts"][i][1]) for i in k] + [(e["pts"][-1][0], e["h"][-1], e["pts"][-1][1])]
            curve(coll, edit_id, f"hillside_D1_street_{e['name'].replace(' (street)', '').replace(' ', '_')}", [(pts, False)],
                  (0.1, 0.1, 0.1, 1.0), 0.4, f"D1 street centreline at its profile (9 m street, <= 11 %): {e['note']}")
        elif e["kind"] == "head":
            a = np.linspace(0, 2 * np.pi, 33)[:-1]
            c, h = e["pts"][0], e["h"][0]
            curve(coll, edit_id, "hillside_D1_meeting", [([(c[0] + e["half"] * np.cos(t), h, c[1] + e["half"] * np.sin(t)) for t in a], True)],
                  (0.1, 0.1, 0.1, 1.0), 0.3, f"where her lines meet: a 9 m radius junction at {h:.1f} m over the sea")
    pads = [([(x, lot["base"], z) for x, z in rect(lot["c"], lot["t"], LOT_FRONT, LOT_DEPTH)], True) for lot in lots]
    curve(coll, edit_id, "hillside_D1_lot_pads", pads, (0.15, 0.45, 0.85, 1.0), 0.15,
          f"{len(lots)} lots of 8 x 7 m, each a low terrace at its pad height (walls <= 2 m), garage at the street")
    ring = chaikin(outline(moved), 1)
    curve(coll, edit_id, "hillside_D1_footprint", [([(x, on(x, z, 0.5), z) for x, z in ring], True)], (0.9, 0.5, 0.1, 1.0), 0.4,
          "the regrade's footprint (ground moved by more than 5 cm on the 1 m design grid)")
    return coll


def remove(edit_id):
    for o in list(bpy.data.objects):
        if o.get("kyt_edit_id") == edit_id and o.type == "CURVE":
            data = o.data
            bpy.data.objects.remove(o)
            if data.users == 0:
                bpy.data.curves.remove(data)
    for m in list(bpy.data.materials):
        if m.get("kyt_edit_id") == edit_id and m.users == 0:
            bpy.data.materials.remove(m)
    c = bpy.data.collections.get(COLL)
    if c is not None and not c.objects and not c.children:
        bpy.data.collections.remove(c)
