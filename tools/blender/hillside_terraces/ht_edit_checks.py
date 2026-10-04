"""Edit 6's checks: vertex hashes of the protected sets, and a content
fingerprint of the whole file (Blender never writes the same bytes twice, so
the round trip is proved on content: the terrain's vertices, every attribute,
the faces, the edit log, the README and every data-block's name)."""

import hashlib

import numpy as np

import bpy

from ht_geom import dist_to
from ht_site import HW_HALF, HW_VERGE, RAMP_ZMAX

WIDTH = {"FLOAT": 1, "INT": 1, "BOOLEAN": 1, "INT8": 1, "FLOAT_VECTOR": 3, "FLOAT2": 2, "INT32_2D": 2,
         "FLOAT_COLOR": 4, "BYTE_COLOR": 4, "QUATERNION": 4, "FLOAT4X4": 16}


def h12(a):
    return hashlib.sha1(np.ascontiguousarray(a).tobytes()).hexdigest()[:12]


def mesh_co(me):
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def attr(me, name, dtype):
    out = np.zeros(len(me.vertices), dtype=dtype)
    me.attributes[name].data.foreach_get("value", out)
    return out


STRIP = "coast highway strip (every vertex of a face reaching it)"


def strip_vertices(me, hw_line, box):
    """Vertices of every face that reaches the highway's strip (centreline +- HW_HALF + HW_VERGE): on a 10 m
    lattice a vertex outside the strip still shapes the ground inside it through its faces."""
    n = len(me.polygons)
    cen = np.empty(n * 3)
    me.polygons.foreach_get("center", cen)
    cen = cen.reshape(-1, 3)
    x0, x1, z0, z1 = box
    cand = np.nonzero((cen[:, 0] > x0) & (cen[:, 0] < x1) & (-cen[:, 1] > z0) & (-cen[:, 1] < z1))[0]
    near = cand[dist_to(hw_line, cen[cand, 0], -cen[cand, 1]) <= HW_HALF + HW_VERGE + 7.1]   # 7.1: half a cell's diagonal
    start = np.empty(n, dtype=np.int64)
    total = np.empty(n, dtype=np.int64)
    me.polygons.foreach_get("loop_start", start)
    me.polygons.foreach_get("loop_total", total)
    loops = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("vertex_index", loops)
    out = np.zeros(len(me.vertices), dtype=bool)
    for f in near:
        out[loops[start[f]:start[f] + total[f]]] = True
    return out


def sets(me, co, aid, hw_line):
    """The protected vertex sets: the coast highway's strip, the ramps' latitude, edits 1-5."""
    X, Z = co[:, 0], -co[:, 1]
    box = (X > -150) & (X < 450) & (Z > 300) & (Z < 900)
    out = {STRIP: strip_vertices(me, hw_line, (-150, 450, 300, 900)),
           "interchange ramps (z <= %g, x -150..450)" % RAMP_ZMAX: box & (Z <= RAMP_ZMAX)}
    for e in range(1, int(aid.max()) + 1):
        out[f"edit {e}"] = aid == e
    return out


def hashes(co, masks, moved):
    out = {k: h12(co[m]) for k, m in masks.items()}
    out["outside the footprint"] = h12(co[~moved])
    out["whole mesh"] = h12(co)
    return out


def fingerprint(obj):
    me = obj.data
    parts = [h12(mesh_co(me))]
    for a in sorted(me.attributes, key=lambda a: a.name):
        w = WIDTH.get(a.data_type)
        if w is None:
            parts.append(f"{a.name}:{a.data_type}")
            continue
        n = len(a.data) * w
        buf = np.empty(n)
        for key in ("color", "vector", "value"):
            try:
                a.data.foreach_get(key, buf)
                parts.append(f"{a.name}:{a.domain}:{key}:{h12(buf)}")
                break
            except (AttributeError, TypeError, RuntimeError):
                continue
        else:
            parts.append(f"{a.name}:{a.data_type}:{len(a.data)}")
    loops = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("vertex_index", loops)
    parts.append(h12(loops))
    parts.append(str(me.color_attributes.active_color_name) + "|" + str(me.color_attributes.render_color_index))
    parts.append(hashlib.sha1(str(obj.get("kyt_edits", "")).encode()).hexdigest()[:12])
    t = bpy.data.texts.get("README")
    parts.append(hashlib.sha1((t.as_string() if t else "").encode()).hexdigest()[:12])
    for coll in (bpy.data.objects, bpy.data.collections, bpy.data.materials, bpy.data.curves, bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
        parts.append(",".join(sorted(x.name for x in coll)))
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:12]
