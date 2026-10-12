"""Carry approved coast/headland proposal variants into a world terrain master (2026-10-09).

Christina approved, on 2026-10-09, the recommended variants of the coast/headland proposals in
`documentation/screenshots/coast-headland-2026-10-08/proposals/`: range north's shell R1, the
north shore C1 (built on R1), the headland cliff A1 (built on both) with its shelf stopped at
x -178 under the south face. Each proposal builder writes its variants as separate objects in its
own scratch copy of the master; this swaps a variant's mesh into the named `Ground` object of the
master opened here, keeps the replaced mesh whole in `Ground_history` as
`<target>__before_<tag>`, and maps the variant's materials back onto the master's own, so the
export's material names stay what the game's wrapper expects.

    Blender --background <in.blend> --python tools/blender/world_terrain_apply_headland_coast.py -- \\
        --out <out.blend> --tag <tag> --swap <proposal.blend>:<variant object>=<target object> [...]
        [--trim-shelf <x0>,<x1>,<z0>,<z1>] [--add-piece <src.blend>:<object>:<x0>,<x1>,<z0>,<z1>]
    Blender --background <in.blend> --python ... -- --out <out.blend> --undo <tag>

`--trim-shelf x0,x1,z0,z1` deletes `terrain_coast_shelf` faces whose centre lies in that Godot box:
A1's band under the headland's south face stops at x -178 so the seabed session's harbour keeps its
4 m (her choice, 2026-10-09). The box must stay local: the shelf runs round every coast.
`--add-piece` copies back, from <src.blend>'s object of that name, every separate piece (connected
faces) lying wholly inside the Godot box: R1 deleted range north's internal slab "piece 1", which is
the only master ground under part of the road corridor at the river mouth, and without it the
generator's corridor follows the apron 1-2 m lower; it goes back, and C1 sinks it out of sight
everywhere but there. Refuses to write into the main
checkout's assets/, scenes/, scripts/ or tools/ (only a worktree's). Godot (x, y, z) = Blender
(x, -z, y).
"""

import os
import re
import sys

import bmesh
import bpy

MAIN = "/Users/christina/Dropbox/Mac/Documents/Keep Your Ticket"
SHELF = "terrain_coast_shelf"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, many=False):
    vals = [argv[i + 1] for i, a in enumerate(argv) if a == name and i + 1 < len(argv)]
    return vals if many else (vals[0] if vals else None)


def refuse(path):
    real = os.path.realpath(path)
    if "/.claude/worktrees/" in real:
        return
    for sub in ("assets", "scenes", "scripts", "tools"):
        root = os.path.realpath(os.path.join(MAIN, sub))
        if os.path.commonpath([real, root]) == root:
            raise SystemExit("apply: refusing to write %s in the main checkout" % real)


def log(msg):
    print("apply_headland_coast: " + msg)
    sys.stdout.flush()


def topology(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    open_edges = sum(1 for e in bm.edges if e.is_boundary)
    wire = sum(1 for e in bm.edges if e.is_wire)
    bm.free()
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    return {"verts": len(me.vertices), "faces": len(me.polygons), "tris": tris, "open_edges": open_edges, "wire": wire}


def history_collection():
    col = bpy.data.collections.get("Ground_history")
    if col is None:
        col = bpy.data.collections.new("Ground_history")
        bpy.context.scene.collection.children.link(col)
    return col


def remap_materials(me):
    """A variant brought in from another file carries copies of the master's materials
    (`name.001`); point its slots back at the master's own and drop the copies."""
    for i, m in enumerate(me.materials):
        if m is None:
            continue
        base = re.sub(r"\.\d{3}$", "", m.name)
        own = bpy.data.materials.get(base)
        if own is not None and own is not m:
            me.materials[i] = own
            if m.users == 0:
                bpy.data.materials.remove(m)


def swap(spec, tag):
    src, rest = spec.rsplit(":", 1)
    variant, target = rest.split("=")
    ob = bpy.data.objects.get(target)
    if ob is None or ob.name not in bpy.data.collections["Ground"].all_objects:
        raise SystemExit("apply: no Ground object %s" % target)
    hname = "%s__before_%s" % (target, tag)
    if hname in bpy.data.objects:
        raise SystemExit("apply: %s already in history; undo it first" % hname)
    with bpy.data.libraries.load(src, link=False) as (data_from, data_to):
        if variant not in data_from.objects:
            raise SystemExit("apply: %s has no object %s" % (src, variant))
        data_to.objects = [variant]
    vob = data_to.objects[0]
    new_me = vob.data
    remap_materials(new_me)
    before = topology(ob.data)
    old_me = ob.data
    hist = bpy.data.objects.new(hname, old_me)
    history_collection().objects.link(hist)
    hist.matrix_world = ob.matrix_world
    hist.hide_viewport = hist.hide_render = True
    old_me.name = hname
    ob.data = new_me
    new_me.name = target
    bpy.data.objects.remove(vob)
    log("%s <- %s:%s  before %s  after %s" % (target, os.path.basename(src), variant, before, topology(new_me)))


def trim_shelf(x0, x1, z0, z1):
    me = bpy.data.objects[SHELF].data
    bm = bmesh.new()
    bm.from_mesh(me)
    gone = [f for f in bm.faces if (lambda c: x0 < c.x < x1 and z0 < -c.y < z1)(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()
    log("%s: %d faces in x %.1f..%.1f, z %.1f..%.1f removed; now %s" % (SHELF, len(gone), x0, x1, z0, z1, topology(me)))


def add_piece(spec):
    src, name, box = spec.split(":")
    x0, x1, z0, z1 = (float(v) for v in box.split(","))
    with bpy.data.libraries.load(src, link=False) as (data_from, data_to):
        data_to.objects = [name]
    sob = data_to.objects[0]
    sbm = bmesh.new()
    sbm.from_mesh(sob.data)
    seen, pieces = set(), []
    for f in sbm.faces:
        if f.index in seen:
            continue
        comp, stack = [], [f]
        seen.add(f.index)
        while stack:
            g = stack.pop()
            comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        vs = {v for g in comp for v in g.verts}
        if all(x0 <= v.co.x <= x1 and z0 <= -v.co.y <= z1 for v in vs):
            pieces.append(comp)
    ob = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mat_names = [m.name if m else None for m in ob.data.materials]
    smat = [m.name if m else None for m in sob.data.materials]
    vmap, added = {}, 0
    for comp in pieces:
        for g in comp:
            nv = []
            for v in g.verts:
                if v not in vmap:
                    vmap[v] = bm.verts.new(v.co)
                nv.append(vmap[v])
            nf = bm.faces.new(nv)
            base = re.sub(r"\.\d{3}$", "", smat[g.material_index] or "")
            nf.material_index = mat_names.index(base) if base in mat_names else g.material_index
            nf.smooth = g.smooth
            added += 1
    bm.to_mesh(ob.data)
    bm.free()
    sbm.free()
    smesh, smats = sob.data, [m for m in sob.data.materials if m is not None]
    bpy.data.objects.remove(sob)
    bpy.data.meshes.remove(smesh)
    for m in smats:
        if m.users == 0:
            bpy.data.materials.remove(m)
    ob.data.update()
    log("%s: %d pieces, %d faces added back from %s; now %s" % (name, len(pieces), added, os.path.basename(src), topology(ob.data)))


def undo(tag):
    suffix = "__before_%s" % tag
    found = [o for o in bpy.data.collections["Ground_history"].objects if o.name.endswith(suffix)]
    if not found:
        raise SystemExit("apply: nothing in Ground_history for %s" % tag)
    for hist in found:
        target = hist.name[: -len(suffix)]
        ob = bpy.data.objects[target]
        cur = ob.data
        ob.data = hist.data
        hist.data.name = target
        bpy.data.objects.remove(hist)
        bpy.data.meshes.remove(cur)
        log("%s restored from history (%s)" % (target, topology(ob.data)))


def main():
    out = opt("--out")
    if not out:
        raise SystemExit("apply: --out <blend> is required")
    refuse(out)
    bpy.context.preferences.filepaths.save_version = 0
    if opt("--undo"):
        undo(opt("--undo"))
    else:
        tag = opt("--tag")
        if not tag:
            raise SystemExit("apply: --tag is required")
        for spec in opt("--swap", many=True):
            swap(spec, tag)
        if opt("--add-piece"):
            add_piece(opt("--add-piece"))
        if opt("--trim-shelf"):
            trim_shelf(*(float(v) for v in opt("--trim-shelf").split(",")))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
    log("saved %s" % os.path.abspath(out))


main()
