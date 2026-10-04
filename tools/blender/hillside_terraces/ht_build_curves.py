"""Reference curves and house massing for the hillside terraces patches
(Blender, scratch copy only)."""

import bpy
import numpy as np

from ht_geom import bilinear, chaikin, rect, resample
from ht_site import DOWN, LINE1, LINE2, MEET, NEAR, SEA_Y

HOUSE_COLS = [(0.93, 0.62, 0.55), (0.55, 0.75, 0.85), (0.95, 0.85, 0.45), (0.60, 0.80, 0.60), (0.85, 0.65, 0.85)]


def material(name, rgb):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*rgb, 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
    return m


def curve(coll, name, pts3, rgb, bevel, note):
    """pts3: (x, y over the sea, z) world points."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts3) - 1)
    for p, (x, y, z) in zip(sp.points, pts3):
        p.co = (float(x), float(-z), float(y + SEA_Y), 1.0)
    cu.materials.append(material(f"ht_mat_{rgb}", rgb))
    ob = bpy.data.objects.new(name, cu)
    ob["kyt_note"] = note
    ob["kyt_collision"] = "none"
    coll.objects.link(ob)
    return ob


def drape(H, pl, lift):
    pts, _ = resample(chaikin(pl, 1), 1.0)
    y = bilinear(H, NEAR["x0"], NEAR["z0"], NEAR["step"], pts[:, 0], pts[:, 1]) + lift
    return [(p[0], v, p[1]) for p, v in zip(pts, y)]


def her_lines(coll, H, key):
    out = []
    for nm, pl in (("line1", LINE1 + [MEET]), ("line2", LINE2 + [MEET]), ("down", DOWN)):
        out.append(curve(coll, f"PROPOSAL_hillside_terraces_{key}_her_{nm}", drape(H, pl, 0.6), (0.85, 0.08, 0.08), 0.35,
                         "Christina's red line from her sketch, draped"))
    return out


def houses(coll, res, key):
    """A simple block (7 x 6 m, 6.5 m tall: a storey over the garage) on each counted lot."""
    verts, faces, mats = [], [], []
    for n, lot in enumerate(res["lots"]["rects"]):
        c, t = np.array(lot["c"]), np.array(lot["t"])
        base = lot.get("base")
        if base is None:
            continue
        tall = 6.5 if lot["kind"] != "lane" else 5.5
        corners = rect(c, t, 7.0, 6.0)
        k = len(verts)
        for x, z in corners:
            verts.append((x, -z, base + SEA_Y))
        for x, z in corners:
            verts.append((x, -z, base + SEA_Y + tall))
        faces += [(k, k + 1, k + 2, k + 3), (k + 4, k + 7, k + 6, k + 5), (k, k + 4, k + 5, k + 1),
                  (k + 1, k + 5, k + 6, k + 2), (k + 2, k + 6, k + 7, k + 3), (k + 3, k + 7, k + 4, k)]
        mats += [n % len(HOUSE_COLS)] * 6
    if not verts:
        return []
    me = bpy.data.meshes.new(f"PROPOSAL_hillside_terraces_{key}_houses")
    me.from_pydata(verts, [], faces)
    for i, col in enumerate(HOUSE_COLS):
        me.materials.append(material(f"ht_house_{i}", col))
    me.polygons.foreach_set("material_index", np.array(mats, dtype=np.int32))
    me.update()
    ob = bpy.data.objects.new(me.name, me)
    ob["kyt_note"] = "PROPOSAL massing: one block per counted lot, for the obliques only"
    ob["kyt_collision"] = "none"
    coll.objects.link(ob)
    return [ob]


def curves_for(coll, res, key):
    out = []
    for e in res["elements"]:
        pts, h = np.array(e["pts"]), np.array(e["h"])
        if e["kind"] == "head":
            a = np.linspace(0, 2 * np.pi, 33)
            ring = [(pts[0][0] + e["half"] * np.cos(t), h[0] + 0.3, pts[0][1] + e["half"] * np.sin(t)) for t in a]
            out.append(curve(coll, f"PROPOSAL_hillside_terraces_{key}_{e['name']}", ring, (0.15, 0.15, 0.15), 0.25, e["note"]))
            continue
        if e["kind"] in ("lane", "context"):
            continue                          # lanes are drawn from their records below; the terrace streets are context
        rgb = (0.45, 0.28, 0.12) if e["kind"] == "steps" else (0.12, 0.12, 0.12)
        out.append(curve(coll, f"PROPOSAL_hillside_terraces_{key}_{e['name']}", [(p[0], v + 0.3, p[1]) for p, v in zip(pts, h)],
                         rgb, 0.3, e["note"]))
    for ln in res.get("lanes", []):
        out.append(curve(coll, f"PROPOSAL_hillside_terraces_{key}_{ln['name']}",
                         [(p[0], v + 0.4, p[1]) for p, v in zip(ln["pts"], ln["h"])], (0.45, 0.28, 0.12), 0.3, "stepped lane on natural ground"))
    for u in res.get("underpass", []):
        out.append(curve(coll, f"PROPOSAL_hillside_terraces_{key}_underpass", [(p[0], v + 0.3, p[1]) for p, v in zip(u["pts"], u["h"])],
                         (0.1, 0.1, 0.45), 0.3, "the street under the highway (not cut: the underpass)"))
    out += houses(coll, res, key)
    return out
