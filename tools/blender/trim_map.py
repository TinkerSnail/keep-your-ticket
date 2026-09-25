"""Map a game mesh onto a trim sheet: a `trim` UV map, first, and the old unwrap kept second.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>.blend \
        --python tools/blender/trim_map.py -- <layout.json> [material=strip ...] [--save]

Each face goes to the strip its material names, `timber=timber_fresh` and so on
(the defaults below cover the park furniture sheet). How a face lands:

- **Projected by its direction.** A face is flattened along the world axis it
  faces most, and the prop's longest axis is laid along U, the strip's tiling
  direction, so grain and wear run the length of a slat or rail.
- **At the sheet's scale** (`px_per_metre`), so every prop on the sheet shares
  one texel density, and U runs as far as the part is long: the strip repeats.
- **Boards kept whole.** Faces of one material in one plane that touch anywhere
  move together into the strip (`plane_regions`), so a slat top cut into pieces
  by the fuse still reads as one board. Each board is placed at a stable
  pseudo-random height and offset within its strip, so parallel slats show
  different grain.
- **Cells, for materials mapped to a detail cell** (fixings to `bolt_round`):
  each connected piece is fitted to fill the cell, since a bolt head painted to
  fill 128 px is the picture of one bolt.

The unwrap made by Make game mesh stays as the second UV map, `unique`, for the
bench's own baked shading. Without `--save` the file is not written.
"""

import json
import os
import sys
import zlib

import bmesh
import bpy
from mathutils import Vector

DEFAULT_STRIPS = {"timber": "timber_fresh", "cast_iron": "iron_smooth", "fixings": "bolt_round",
                  "painted_steel": "iron_smooth", "powder_coat_green": "iron_smooth",
                  "perforated_steel": "iron_smooth"}
## A face looking along the prop's length is the cut end of a board, not its
## face, so it takes the end-grain strip instead.
END_STRIPS = {"timber": "timber_end_grain"}


def load_layout(path):
    layout = json.load(open(path))
    size = layout["size_px"]
    places = {}
    for row in layout["rows"]:
        if row.get("tiles"):
            places[row["id"]] = {"kind": "strip", "y": row["y"]}
        for cell in row.get("cells", []):
            places[cell["id"]] = {"kind": "cell", "x": cell["x"], "y": cell["y"]}
    return layout, size, places


def axes_for(normal, long_axis):
    """(u_axis, v_axis) world indices for a face pointing along `normal`."""
    n = [abs(c) for c in normal]
    facing = n.index(max(n))
    rest = [a for a in (0, 1, 2) if a != facing]
    u = long_axis if long_axis in rest else rest[0]
    v = [a for a in rest if a != u][0]
    return u, v


def regions(bm, uv_ok):
    """Groups of connected faces, same material and flat to each other."""
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        group, stack = [], [f]
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            group.append(cur)
            for e in cur.edges:
                for g in e.link_faces:
                    if g.index in seen or g.material_index != f.material_index:
                        continue
                    if uv_ok(f, g):
                        seen.add(g.index)
                        stack.append(g)
        out.append(group)
    return out


def plane_regions(bm, mw, long_axis, touch_m=0.001):
    """Boards: faces of one material lying in one plane and touching anywhere.

    The fuse cuts a slat's top into pieces that often meet only at a corner or
    part-way along an edge (T-junctions), so grouping by shared edges split one
    board into many and gave each its own grain. Here pieces are grouped by
    plane, then joined wherever their footprints in that plane touch; separate
    slats, with a gap between them, stay separate boards."""
    by_plane = {}
    for f in bm.faces:
        n = (mw.to_3x3() @ f.normal).normalized()
        p = mw @ f.verts[0].co
        key = (f.material_index, tuple(round(c, 2) for c in n), round(n.dot(p), 3))
        by_plane.setdefault(key, []).append(f)
    out = []
    for key, faces in by_plane.items():
        n = Vector(key[1])
        ua, va = axes_for(n, long_axis)
        boxes = []
        for f in faces:
            pts = [mw @ v.co for v in f.verts]
            boxes.append((min(p[ua] for p in pts), max(p[ua] for p in pts),
                          min(p[va] for p in pts), max(p[va] for p in pts)))
        parent = list(range(len(faces)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(faces)):
            a = boxes[i]
            for j in range(i + 1, len(faces)):
                b = boxes[j]
                if a[0] <= b[1] + touch_m and b[0] <= a[1] + touch_m \
                        and a[2] <= b[3] + touch_m and b[2] <= a[3] + touch_m:
                    parent[find(i)] = find(j)
        groups = {}
        for i, f in enumerate(faces):
            groups.setdefault(find(i), []).append(f)
        out.extend(groups.values())
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        raise SystemExit("trim_map: give the layout json after --")
    layout, (w, h), places = load_layout(argv[0])
    strips = dict(DEFAULT_STRIPS)
    for a in argv[1:]:
        if "=" in a:
            k, v = a.split("=", 1)
            strips[k] = v
    ppm = layout["px_per_metre"]
    bleed = layout["bleed_px"]

    obj = next(o for o in bpy.data.collections["export"].objects if o.type == "MESH")
    me = obj.data
    if "unique" not in me.uv_layers:
        me.uv_layers[0].name = "unique"
    trim = me.uv_layers.get("trim") or me.uv_layers.new(name="trim")
    # glTF's TEXCOORD_0 is the first map: make `trim` first by rebuilding the order.
    names = [l.name for l in me.uv_layers]
    if names[0] != "trim":
        data = {l.name: [d.uv.copy() for d in l.data] for l in me.uv_layers}
        while me.uv_layers:
            me.uv_layers.remove(me.uv_layers[0])
        for n in ["trim"] + [x for x in names if x != "trim"]:
            layer = me.uv_layers.new(name=n)
            for d, uv in zip(layer.data, data[n]):
                d.uv = uv

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    uv = bm.loops.layers.uv["trim"]
    mw = obj.matrix_world
    dims = obj.dimensions
    long_axis = list(dims).index(max(dims))
    mat_names = [s.material.name if s.material else "" for s in obj.material_slots]
    placed = {"strip": 0, "cell": 0, "unmapped": 0}
    for group in plane_regions(bm, mw, long_axis):
        mat = mat_names[group[0].material_index]
        place = places.get(strips.get(mat, ""))
        if place is None:
            placed["unmapped"] += len(group)
            continue
        if place["kind"] == "cell":
            continue  # cells are fitted per connected piece below
        normal = sum((f.normal for f in group), Vector()).normalized()
        n = [abs(c) for c in normal]
        if n.index(max(n)) == long_axis and mat in END_STRIPS:
            place = places[END_STRIPS[mat]]
        ua, va = axes_for(normal, long_axis)
        pts = [(mw @ l.vert.co) for f in group for l in f.loops]
        vmin = min(p[va] for p in pts)
        vmax = max(p[va] for p in pts)
        y0, y1 = place["y"]
        room = (y1 - y0 - 2 * bleed) - (vmax - vmin) * ppm
        seed = zlib.crc32(f"{round(pts[0][0], 2)},{round(pts[0][1], 2)},{round(pts[0][2], 2)}".encode())
        top = y0 + bleed + (seed % max(1, int(room)) if room > 0 else 0)
        u_off = (seed >> 8) % w
        for f in group:
            for l in f.loops:
                p = mw @ l.vert.co
                px_u = u_off + p[ua] * ppm
                px_v = top + (vmax - p[va]) * ppm
                l[uv].uv = (px_u / w, 1.0 - px_v / h)
        placed["strip"] += len(group)

    # Detail cells: each connected piece of a cell material fills its cell.
    for group in regions(bm, lambda a, b: True):
        mat = mat_names[group[0].material_index]
        place = places.get(strips.get(mat, ""))
        if place is None or place["kind"] != "cell":
            continue
        normal = sum((f.normal * f.calc_area() for f in group), Vector()).normalized()
        ua, va = axes_for(normal, long_axis)
        pts = [(mw @ l.vert.co) for f in group for l in f.loops]
        umin, umax = min(p[ua] for p in pts), max(p[ua] for p in pts)
        vmin, vmax = min(p[va] for p in pts), max(p[va] for p in pts)
        span = max(umax - umin, vmax - vmin, 1e-6)
        (x0, x1), (y0, y1) = place["x"], place["y"]
        side = min(x1 - x0, y1 - y0) - 2 * bleed
        for f in group:
            for l in f.loops:
                p = mw @ l.vert.co
                px_u = x0 + bleed + (p[ua] - umin) / span * side
                px_v = y0 + bleed + (vmax - p[va]) / span * side
                l[uv].uv = (px_u / w, 1.0 - px_v / h)
        placed["cell"] += len(group)

    bm.to_mesh(me)
    bm.free()
    print(f"trim_map: {placed['strip']} faces on strips, {placed['cell']} on detail cells, "
          f"{placed['unmapped']} unmapped; UV maps now {[l.name for l in me.uv_layers]}")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


main()
