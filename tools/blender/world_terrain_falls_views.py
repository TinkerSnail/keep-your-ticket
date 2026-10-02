"""Driver's-eye views of the falls from the coast highway, rendered from the master with scratch
cameras that are never saved (2026-10-02). Headless only; the file is not written.

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_falls_views.py -- --out documentation/terrain/renders [--eye 1.2]

Frames (prefix falls_built_): driver_first_sight_SB, driver_best_view_SB, driver_last_sight_SB,
driver_reveal_NB (southbound = east up the valley then south; northbound the reverse), the
turnout view, and an oblique of the fall with its ribbon from above the turnout. Smooth shading
is set on the terrain for the render only. `--eye` sets the eye height (1.2 m default; 4 m is
the honest alternative when the 3 m patch reads as facets at 1.2 m).
"""
import os
import sys

import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

LIP = (400.0, -290.0, 41.9)
POOL_Y = 11.9


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[argv.index("--out") + 1]
    eye_h = float(argv[argv.index("--eye") + 1]) if "--eye" in argv else 1.2
    tag = "" if abs(eye_h - 1.2) < 1e-6 else f"_eye{eye_h:g}m"
    obj = bpy.data.objects["terrain_world"]
    me = obj.data
    me.polygons.foreach_set("material_index", np.zeros(len(me.polygons), dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), dtype=bool))
    me.update()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.75, 0.82, 0.92, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.9, 0.0, -2.3)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0
    cam_data.clip_start = 0.5
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def g(x, z):
        h = bvh.ray_cast(Vector((x, -z, 2000.0)), Vector((0, 0, -1)), 6000.0)
        return float(h[0].z) if h[0] is not None else 0.0

    def shoot(name, eye, aim, lens=28.0):
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector((eye[0], -eye[1], eye[2])), Vector((aim[0], -aim[1], aim[2]))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1350
        scene.render.filepath = os.path.join(out, name)
        bpy.ops.render.render(write_still=True)
        print(f"falls_views: rendered {scene.render.filepath}")
    aim = (LIP[0], LIP[1], LIP[2] - 15.0)
    for name, (x, z) in (("first_sight_SB", (104, -361)), ("best_view_SB", (270, -265)), ("last_sight_SB", (296, -232)), ("reveal_NB", (337, -132))):
        shoot(f"falls_built_driver_{name}{tag}.png", (x, z, g(x, z) + eye_h), aim)
    shoot(f"falls_built_turnout_view{tag}.png", (266, -278, g(266, -278) + eye_h + 0.4), aim, lens=35.0)
    shoot("falls_built_turnout_oblique.png", (255, -290, g(255, -290) + 25.0), (LIP[0], LIP[1], 25.0), lens=35.0)
    print("falls_views: cameras, sun and smoothing were not saved")


if __name__ == "__main__":
    main()
