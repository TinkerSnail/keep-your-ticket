"""Turn a stack of drums into one lathe: a drawn outline spun round the axis.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<name>.blend --python tools/blender/lathe_from_drums.py -- \
        <lathe>=<drum>+<drum>+... [<lathe>=...] [--axis X,Y]

Each `<lathe>` becomes one object in `export`: a line of vertices, the stack's
outline in section (radius out along the object's X, height up its Z, from
the axis at the bottom round to the axis at the top), and a **Screw**
modifier that spins it a full turn into the solid, then **Smooth by Angle**
(30°) so the sides shade round and the ledges stay sharp. Reshaping is moving
points on that line; Send applies both modifiers, so the game gets the solid.
The drums it replaces leave `export` (the maquette's are still in
`reference`). The plaza fountain's pedestal and basin undersides, 2026-09-28.

**What it keeps.** The outline is the union of the drums in section, at their
plan sizes: every radius and height the drums had, with the generator's
nudges taken out (each drum stood up to 5 mm along Godot's (1, 1, 1) from the
plan, by build order; its centre's offset from `--axis`, the park's origin by
default, says how far). Where drums overlapped, the faces hidden inside the
overlap are gone: a lathe is one closed outline. Drums must share a material.

**What it changes.** A lathe has one number of sides: the largest of its
drums', so no drum gets coarser, and the spin starts where the drums' corners
did, so a drum that keeps its count keeps its corners. A drum with fewer
sides gains some; its faces move by at most their sagitta, radius times
(1 − cos(π / sides)). The Screw modifier's Steps sets the count afterwards.

Refuses an object name already in the file. Saves the file, so it is for a
file an agent has prepared, never one Christina has open.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

NUDGE = Vector((1.0, -1.0, 1.0))  # Godot's (1, 1, 1) in Blender's axes
MOST_NUDGE = 0.0051
SMOOTH_ANGLE = math.radians(30.0)


def drum(obj, axis):
    """A drum object's plan size: sides, radius, bottom, top, phase, material."""
    ws = [obj.matrix_world @ v.co for v in obj.data.vertices]
    centre = sum(ws, Vector()) / len(ws)
    s = centre.x - axis.x
    if abs(centre.y - axis.y + s) > 1e-5 or abs(s) > MOST_NUDGE:
        raise SystemExit(f"lathe_from_drums: '{obj.name}' is not a drum on the axis, "
                         f"centre ({centre.x:.5f}, {centre.y:.5f})")
    low = min(w.z for w in ws)
    rim = [w for w in ws if abs(w.z - low) < 1e-6]
    sides = len(rim)
    radius = max(math.hypot(w.x - centre.x, w.y - centre.y) for w in rim)
    step = 2 * math.pi / sides
    first = min(rim, key=lambda w: math.atan2(w.y - centre.y, w.x - centre.x) % step)
    phase = math.atan2(first.y - centre.y, first.x - centre.x) % step
    if phase > step / 2:
        phase -= step
    mats = {slot.material.name for slot in obj.material_slots if slot.material}
    if len(mats) != 1:
        raise SystemExit(f"lathe_from_drums: '{obj.name}' has {len(mats)} materials")
    return {"name": obj.name, "sides": sides, "radius": radius, "low": low - s,
            "high": max(w.z for w in ws) - s, "phase": phase, "material": mats.pop(),
            "nudge": s, "object": obj}


def outline(drums):
    """The union of the drums in section: (radius, height) from the axis at the
    bottom, round the outside, to the axis at the top."""
    cuts = sorted({d["low"] for d in drums} | {d["high"] for d in drums})
    bands = []
    for lo, hi in zip(cuts, cuts[1:]):
        mid = (lo + hi) / 2
        r = max((d["radius"] for d in drums if d["low"] <= mid <= d["high"]), default=0.0)
        if r == 0.0:
            raise SystemExit("lathe_from_drums: the drums leave a gap; they must stack")
        if bands and abs(bands[-1][2] - r) < 1e-7:
            bands[-1][1] = hi
        else:
            bands.append([lo, hi, r])
    pts = [(0.0, bands[0][0])]
    for lo, hi, r in bands:
        pts += [(r, lo), (r, hi)]
    pts.append((0.0, bands[-1][1]))
    return pts


def smooth_by_angle(obj):
    """Blender's own Smooth by Angle modifier, the one Shade Auto Smooth adds,
    from its bundled Essentials (the operator needs a window to run)."""
    group = bpy.data.node_groups.get("Smooth by Angle")
    if group is None:
        path = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "nodes",
                            "geometry_nodes_essentials.blend")
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            if "Smooth by Angle" not in src.node_groups:
                raise SystemExit("lathe_from_drums: no Smooth by Angle in Blender's Essentials")
            dst.node_groups = ["Smooth by Angle"]
        group = bpy.data.node_groups["Smooth by Angle"]
    mod = obj.modifiers.new("Smooth by Angle", "NODES")
    mod.node_group = group
    for item in group.interface.items_tree:
        if getattr(item, "in_out", None) == "INPUT" and item.name == "Angle":
            mod[item.identifier] = SMOOTH_ANGLE
    return mod


def make(name, drums, export):
    if name in bpy.data.objects:
        raise SystemExit(f"lathe_from_drums: '{name}' already exists")
    mats = {d["material"] for d in drums}
    if len(mats) != 1:
        raise SystemExit(f"lathe_from_drums: {name}'s drums have materials {sorted(mats)}")
    sides = max(d["sides"] for d in drums)
    keeper = next(d for d in drums if d["sides"] == sides)
    pts = outline(drums)
    mid = (pts[0][1] + pts[-1][1]) / 2
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(r, 0.0, z - mid) for r, z in pts],
                     [(i, i + 1) for i in range(len(pts) - 1)], [])
    mesh.materials.append(bpy.data.materials[mats.pop()])
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (AXIS.x, AXIS.y, mid)
    obj.rotation_euler = (0.0, 0.0, keeper["phase"])
    for key in ("kyt_collision", "kyt_shadow"):
        values = {d["object"].get(key) for d in drums}
        if len(values) != 1:
            raise SystemExit(f"lathe_from_drums: {name}'s drums disagree on {key}")
        if values != {None}:
            obj[key] = values.pop()
    export.objects.link(obj)

    screw = obj.modifiers.new("Lathe", "SCREW")
    screw.axis = "Z"
    screw.angle = 2 * math.pi
    screw.steps = sides
    screw.render_steps = sides
    screw.use_merge_vertices = True
    screw.merge_threshold = 1e-4
    screw.use_smooth_shade = True
    screw.use_normal_calculate = True
    smooth_by_angle(obj)

    # Faces outward: the bottom's normal points down, whichever way the
    # outline was drawn.
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    m = ev.to_mesh()
    bottom = min(m.polygons, key=lambda p: p.center.z)
    if (obj.matrix_world.to_3x3() @ bottom.normal).z > 0:
        screw.use_normal_flip = True
    ev.to_mesh_clear()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    m = ev.to_mesh()
    tris = sum(len(p.vertices) - 2 for p in m.polygons)
    ev.to_mesh_clear()

    for d in drums:
        grow = d["radius"] * (1 - math.cos(math.pi / d["sides"])) if d["sides"] != sides else 0.0
        print(f"lathe_from_drums: {name} <- {d['name']}: r {d['radius']:.4f}, {d['low']:.4f}..{d['high']:.4f} m, "
              f"sides {d['sides']} -> {sides}{f' (faces move up to {grow * 1000:.1f} mm)' if grow else ''}, "
              f"nudge {abs(d['nudge']) * NUDGE.length * 1000:.2f} mm out")
    print(f"lathe_from_drums: {name}: outline of {len(pts)} points, {sides} sides, {tris} triangles, "
          f"{mesh.materials[0].name}")
    return obj


def main():
    global AXIS
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    AXIS = Vector((0.0, 0.0, 0.0))
    if "--axis" in argv:
        i = argv.index("--axis")
        x, y = (float(v) for v in argv[i + 1].split(","))
        AXIS = Vector((x, y, 0.0))
        del argv[i:i + 2]
    if not argv:
        raise SystemExit("lathe_from_drums: give <lathe>=<drum>+<drum> ...")
    export = bpy.data.collections["export"]
    plans = []
    for arg in argv:
        name, parts = arg.split("=", 1)
        objs = []
        for p in parts.split("+"):
            o = bpy.data.objects.get(p)
            if o is None or o.name not in export.all_objects:
                raise SystemExit(f"lathe_from_drums: no '{p}' in export")
            objs.append(o)
        plans.append((name, [drum(o, AXIS) for o in objs]))
    for name, drums in plans:
        make(name, drums, export)
        for d in drums:
            mesh = d["object"].data
            bpy.data.objects.remove(d["object"], do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
    bpy.ops.wm.save_mainfile()
    print(f"lathe_from_drums: {len(plans)} lathes saved")


AXIS = Vector((0.0, 0.0, 0.0))
main()
