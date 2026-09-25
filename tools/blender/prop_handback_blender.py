"""Blender's half of a prop hand-back (`tools/prop_handback.py` runs it).

    Blender --background <prop>.blend --python tools/blender/prop_handback_blender.py -- send
    Blender --background <prop>.blend --python tools/blender/prop_handback_blender.py -- render <folder> [--colour <png>]
    Blender --background <prop>.blend --python tools/blender/prop_handback_blender.py -- make [--save]
    Blender --background <prop>.blend --python tools/blender/prop_handback_blender.py -- rebuild [--save]

`send` runs the panel's Send to game (Check first) on the file as saved.
`render` renders the prop from four views worked out from its own size (three
quarters from the front left, straight on, from behind and low, and close over
the top) into <folder>, with the images the file points at, as they are on
disk, or with `--colour <png>` in place of the colour image (a preview of work
in progress). Nothing is saved.

`make` and `rebuild` are the panel's Make game mesh and Rebuild game mesh, on
the file as saved; `--save` saves the working file after (only when her
Blender doesn't hold it: she saves her own open file).
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "extensions"))
from kyt_tools import game_mesh, send  # noqa: E402


def export_bounds():
    pts = [o.matrix_world @ Vector(c) for o in bpy.data.collections["export"].all_objects
           if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def render(folder, colour=None):
    os.makedirs(folder, exist_ok=True)
    for img in bpy.data.images:
        if img.source == "FILE":
            if colour and img.name.endswith("_colour"):
                img.filepath = colour
            img.reload()
    for name in ("reference", "authored"):
        c = bpy.data.collections.get(name)
        if c:
            c.hide_render = True
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1200, 800
    world = bpy.data.worlds.new("handback")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.6
    # Measured before anything is added: a new object lands in the active
    # collection, which may be `export`.
    lo, hi = export_bounds()
    centre, size = (lo + hi) / 2, max((hi - lo).length, 0.3)
    plane = bpy.data.meshes.new("handback_ground")
    plane.from_pydata([(-20, -20, -0.0005), (20, -20, -0.0005), (20, 20, -0.0005), (-20, 20, -0.0005)],
                      [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("handback_ground", plane)
    sc.collection.objects.link(ground)
    gm = bpy.data.materials.new("handback_ground")
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.17, 0.16, 1)
    ground.data.materials.append(gm)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(45), 0, math.radians(-35))
    sun.data.energy = 3.5
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    # Props face -Y in Blender (+Z in Godot): "front" is -Y.
    views = {
        "three_quarter": (centre + Vector((-0.75, -1.0, 0.55)) * size, centre, 50),
        "front": (centre + Vector((0.0, -1.3, 0.25)) * size, centre, 50),
        "back_low": (centre + Vector((0.5, 1.2, 0.0)) * size, centre, 45),
        "close_top": (centre + Vector((-0.15, -0.45, 0.5)) * size, centre + Vector((-0.15, 0.0, 0.1)) * size, 45),
    }
    for name, (loc, target, lens) in views.items():
        loc.z = max(loc.z, lo.z + 0.15 * size)  # never under the ground
        cam.location = loc
        cam.data.lens = lens
        d = target - loc
        cam.rotation_euler = (math.atan2(math.hypot(d.x, d.y), -d.z), 0, math.atan2(d.y, d.x) - math.pi / 2)
        sc.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print("HANDBACK render", sc.render.filepath)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    if argv[0] == "send":
        ok, lines = send.run(bpy.context)
        for line in lines:
            print("HANDBACK send", line)
        print("HANDBACK send ok" if ok else "HANDBACK send failed")
    elif argv[0] in ("make", "rebuild"):
        ok, lines = (game_mesh.run if argv[0] == "make" else game_mesh.rebuild)(bpy.context)
        for line in lines:
            print(f"HANDBACK {argv[0]}", line)
        print(f"HANDBACK {argv[0]} ok" if ok else f"HANDBACK {argv[0]} failed")
        if ok and "--save" in argv:
            bpy.ops.wm.save_mainfile()
            print(f"HANDBACK {argv[0]} saved")
    elif argv[0] == "render":
        render(argv[1], argv[argv.index("--colour") + 1] if "--colour" in argv else None)


main()
