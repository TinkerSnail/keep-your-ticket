"""Edit 7 on the mesh, in edit 5's way: the band's 10 m faces are dropped (their
vertices stay, unused), the new vertices and triangles added and tagged; the
dropped faces, with their index and face values, are stored on the object so
--undo rebuilds them in their old order and the file's content returns exact."""

import json

import numpy as np

import bmesh

FACE_LAYERS = ("edit5_face",)


def apply(obj, me, faces, pl, tris, tag):
    n_v, n_e = len(me.vertices), len(me.edges)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    layers = {n: bm.faces.layers.int.get(n) for n in FACE_LAYERS}
    stored = []
    for f in sorted(faces):
        bf = bm.faces[f]
        stored.append({"i": f, "v": [v.index for v in bf.verts], "mat": bf.material_index, "smooth": bool(bf.smooth),
                       "sel": bool(bf.select), "hide": bool(bf.hide), **{n: (bf[l] if l is not None else 0) for n, l in layers.items()}})
    for bf in [bm.faces[f] for f in faces]:
        bm.faces.remove(bf)
    lay = bm.faces.layers.int.new(tag)
    bm.verts.ensure_lookup_table()
    verts = []
    for (x, z), o, h in zip(pl.xz, pl.orig, pl.h):
        verts.append(bm.verts[o] if o >= 0 else bm.verts.new((x, -z, h)))
    smooth = stored[0]["smooth"] if stored else False
    made = 0
    for t in tris:
        vs = [verts[i] for i in t]
        if len(set(vs)) < 3:
            continue
        f = bm.faces.new(vs)
        f[lay] = 1
        f.smooth = smooth
        made += 1
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj[f"kyt_{tag}_removed_faces"] = json.dumps(stored)
    obj[f"kyt_{tag}_n_orig"] = json.dumps([n_v, n_e])
    return n_v, made


def undo(obj, me, tag):
    stored = json.loads(obj[f"kyt_{tag}_removed_faces"])
    n_v, n_e = json.loads(obj[f"kyt_{tag}_n_orig"])
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.faces.layers.int.get(tag)
    for f in [f for f in bm.faces if f[lay] > 0]:
        bm.faces.remove(f)
    bm.edges.ensure_lookup_table()
    for e in [e for e in bm.edges if e.index >= n_e]:
        bm.edges.remove(e)
    bm.verts.ensure_lookup_table()
    for v in [v for v in bm.verts if v.index >= n_v]:
        bm.verts.remove(v)
    bm.verts.ensure_lookup_table()
    bm.faces.layers.int.remove(lay)
    layers = {n: bm.faces.layers.int.get(n) for n in FACE_LAYERS}
    bm.faces.ensure_lookup_table()
    n_kept = len(bm.faces)
    total = n_kept + len(stored)
    gone = set(s["i"] for s in stored)
    order = [i for i in range(total) if i not in gone]          # the kept faces' old indices, in order
    key = {}
    for k, f in enumerate(bm.faces):
        key[f] = order[k]
    for s in stored:
        f = bm.faces.new([bm.verts[i] for i in s["v"]])
        f.material_index, f.smooth, f.select, f.hide = s["mat"], s["smooth"], s["sel"], s["hide"]
        for n, l in layers.items():
            if l is not None:
                f[l] = s[n]
        key[f] = s["i"]
    bm.faces.sort(key=lambda f: key[f])
    bm.to_mesh(me)
    bm.free()
    me.update()
    del obj[f"kyt_{tag}_removed_faces"]
    del obj[f"kyt_{tag}_n_orig"]
    return len(stored)
