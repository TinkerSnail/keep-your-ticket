"""Lay a crown's blades out on its one canvas: one island per blade, shared by every frond bent from it.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>.blend \
        --python tools/blender/unwrap_blades.py -- [--size 2048] [--overwrite] [--save]

For a prop whose parts the game chooses (`kyt_keep_parts`, the palm crown),
or a plant whose leaves bend blades along courses (`plant_blades.py`, the fern
fan), the unwrap stage of `prop-pipeline.md` for its blades. The fronds in `export`
are not unwrapped: each takes its geometry, UVs included, from its blade in
`authored/blades` through `kyt_course_blade`, so all 21 mature fronds wear the
mature blade's island. There is no game mesh to fuse and Make game mesh does
not apply.

Each blade is laid flat as seen from above, at true scale: U across it (its
x), V along it (its y) from the base at the bottom of the canvas to the tip at
the top, so a leaflet drawn on the canvas lands where it was drawn and the
island's outline is the blade's own. The flat blank blades fold only a few
degrees, so that view stretches nothing measurable. The other meshes in
`export` (the `heart`) keep their own unwrap, scaled to the same metres.

The islands are packed bottom-left, tallest first, `GAP_PX` apart and from the
canvas edge, at the largest texel density that fits the `--size` canvas; the
report gives it in px per metre. Every island's object is marked
`kyt_unwrapped`.

Run it once, before the canvas. After that, reshaping a blade carries its UVs
with its vertices, so painting stays on the leaf; running this again would
move islands under a painting, and it refuses while the canvas PNG exists
unless `--overwrite` (for a canvas nobody has painted). Without `--save` the
file is not written.
"""

import os
import sys

import bpy

GAP_PX = 16  # between islands and from the canvas edge: mipmaps down to 1/16 stay apart


def arg(argv, name, default):
    return int(argv[argv.index(name) + 1]) if name in argv else default


def edge_scales(me):
    """(metres per UV unit along U, along V) for a mesh that already has a
    unwrap, fitted over its edges, so a grid unwrap (the heart's) can be taken to
    true scale without redrawing it."""
    uv = me.uv_layers.active.data
    rows = []
    for p in me.polygons:
        loops = list(p.loop_indices)
        for a, b in zip(loops, loops[1:] + loops[:1]):
            du = uv[b].uv[0] - uv[a].uv[0]
            dv = uv[b].uv[1] - uv[a].uv[1]
            length = (me.vertices[me.loops[b].vertex_index].co - me.vertices[me.loops[a].vertex_index].co).length
            if abs(du) + abs(dv) > 1e-6 and length > 1e-6:
                rows.append((du * du, dv * dv, length * length))
    # Least squares for (su^2, sv^2) in su^2 du^2 + sv^2 dv^2 = L^2.
    a11 = sum(r[0] * r[0] for r in rows)
    a12 = sum(r[0] * r[1] for r in rows)
    a22 = sum(r[1] * r[1] for r in rows)
    b1 = sum(r[0] * r[2] for r in rows)
    b2 = sum(r[1] * r[2] for r in rows)
    det = a11 * a22 - a12 * a12
    su2 = (b1 * a22 - b2 * a12) / det
    sv2 = (a11 * b2 - a12 * b1) / det
    return max(su2, 1e-12) ** 0.5, max(sv2, 1e-12) ** 0.5


def metres(obj, planar):
    """Each loop's UV in metres, lower-left corner at 0, and the island's (w, h):
    the top view for a blade (`planar`), its own unwrap scaled otherwise."""
    me = obj.data
    scale = obj.scale
    if not planar:
        if not me.uv_layers:
            raise SystemExit(f"unwrap_blades: '{obj.name}' has no unwrap of its own to scale")
        su, sv = edge_scales(me)
        uv = me.uv_layers.active.data
        pts = [(uv[k].uv[0] * su, uv[k].uv[1] * sv) for k in range(len(me.loops))]
    elif "kyt_flat_xy" in me.attributes:
        # A blade that is not nearly flat (a bush's semi-dome, `leaf_skin.py`)
        # carries its own flattening, in metres along its surface.
        flat = me.attributes["kyt_flat_xy"].data
        pts = [(flat[l.vertex_index].vector[0] * scale.x, flat[l.vertex_index].vector[1] * scale.y)
               for l in me.loops]
    else:
        pts = [(me.vertices[l.vertex_index].co.x * scale.x, me.vertices[l.vertex_index].co.y * scale.y)
               for l in me.loops]
    x0 = min(p[0] for p in pts)
    y0 = min(p[1] for p in pts)
    pts = [(x - x0, y - y0) for x, y in pts]
    return pts, (max(p[0] for p in pts), max(p[1] for p in pts))


def skyline(sizes, side, height=None):
    """Bottom-left skyline packing of pixel rectangles, in the order given, into
    a `side`-wide canvas (`height` tall, square if not given) with `GAP_PX`
    round each. Positions, or None if they don't fit."""
    height = side if height is None else height
    line = [(GAP_PX, side - GAP_PX, GAP_PX)]  # (x, width, y) segments
    at = []
    for w, h in sizes:
        best = None
        for i, (x, _, _) in enumerate(line):
            if x + w + GAP_PX > side:
                break
            top, reach = 0, x + w + GAP_PX
            for sx, sw, sy in line[i:]:
                if sx >= reach:
                    break
                top = max(top, sy)
            if best is None or top < best[1]:
                best = (x, top)
        if best is None or best[1] + h + GAP_PX > height:
            return None
        x, y = best
        at.append((x, y))
        new = []
        right = x + w + GAP_PX
        for sx, sw, sy in line:
            if sx + sw <= x or sx >= right:
                new.append((sx, sw, sy))
                continue
            if sx < x:
                new.append((sx, x - sx, sy))
            if sx + sw > right:
                new.append((right, sx + sw - right, sy))
        new.append((x, right - x, y + h + GAP_PX))
        new.sort()
        merged = [new[0]]
        for seg in new[1:]:
            px, pw, py = merged[-1]
            if py == seg[2] and px + pw == seg[0]:
                merged[-1] = (px, pw + seg[1], py)
            else:
                merged.append(seg)
        line = merged
    return at


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    size = arg(argv, "--size", 2048)
    scene = bpy.context.scene
    # The palm crown (kyt_keep_parts), or a plant whose leaves bend blades along
    # courses, or placed along one, and go to the game merged (plant_blades.py:
    # the fern fan; the Purple Heart's leaves, `kyt_leaf_blades`).
    bent = any(o.get("kyt_course_blade") or o.get("kyt_leaf_blades")
               for o in bpy.data.collections["export"].all_objects) \
        if "export" in bpy.data.collections else False
    if not (scene.get("kyt_keep_parts") or bent) or "blades" not in bpy.data.collections:
        raise SystemExit("unwrap_blades: this file has no blades bent along courses; "
                         "use unwrap_parts.py")
    blend = bpy.data.filepath
    name = os.path.splitext(os.path.basename(blend))[0]
    root = blend[:blend.index(os.sep + "assets" + os.sep)]
    colour = os.path.join(root, "assets", "source", "textures", name, f"{name}_colour.png")
    if os.path.exists(colour) and "--overwrite" not in argv:
        raise SystemExit(f"unwrap_blades: {os.path.relpath(colour, root)} exists (it may be painted); "
                         "moving islands would slide the painting off the leaves. Nothing changed")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    blades = [o for o in bpy.data.collections["blades"].objects if o.type == "MESH"]
    others = [o for o in bpy.data.collections["export"].objects
              if o.type == "MESH" and not any(m.type == "NODES" for m in o.modifiers)]
    islands = [(o, *metres(o, True)) for o in blades] + [(o, *metres(o, False)) for o in others]
    # Tallest first, then the order the file lists them, so the long blades
    # stand side by side along the bottom and the short ones fill in above.
    islands.sort(key=lambda t: -t[2][1])
    # A slotted blade (a bush's bloom card, `kyt_slots`: one copy of its island
    # per colourway, painted a `1 / slots` of the canvas apart) goes top left,
    # no wider than its slot; the rest pack into the canvas below it.
    slotted = [t for t in islands if t[0].get("kyt_slots")]
    islands = [t for t in islands if not t[0].get("kyt_slots")]

    # Up to 16 px per millimetre: a small plant's leaves (the Purple Heart's,
    # 0.36 m) would otherwise stop at one pixel a millimetre, most of the canvas empty.
    lo, hi = 1.0, float(size) * 16
    fit = None
    for _ in range(40):
        d = (lo + hi) / 2
        band = 0
        for _, _, (w, h) in slotted:
            if int(w * d) + 1 + 2 * GAP_PX > size // int(slotted[0][0]["kyt_slots"]):
                band = size  # too wide for its slot
            band += int(h * d) + 1 + GAP_PX
        at = skyline([(int(w * d) + 1, int(h * d) + 1) for _, _, (w, h) in islands], size, size - band) \
            if band < size else None
        if at is not None:
            top = size - GAP_PX
            for _, _, (w, h) in slotted:
                top -= int(h * d) + 1
                at.append((GAP_PX, top))
                top -= GAP_PX
        if at is None:
            hi = d
        else:
            lo, fit = d, (d, at)
    if fit is None:
        raise SystemExit("unwrap_blades: the islands don't fit any canvas")
    d, at = fit
    islands += slotted

    for (obj, pts, _), (x, y) in zip(islands, at):
        me = obj.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        uv = me.uv_layers.active.data
        for k, (u, v) in enumerate(pts):
            uv[k].uv = ((x + u * d) / size, (y + v * d) / size)
        obj["kyt_unwrapped"] = True
    used = sum((int(w * d) + 1) * (int(h * d) + 1) for _, _, (w, h) in islands) / (size * size)
    print(f"unwrap_blades: {len(islands)} islands at {d:.0f} px/m on a {size} canvas "
          f"({used:.0%} of it in their bounding boxes): "
          + ", ".join(f"{o.name} {w:.2f} x {h:.2f} m at ({x}, {y})"
                      for (o, _, (w, h)), (x, y) in zip(islands, at)))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


main()
