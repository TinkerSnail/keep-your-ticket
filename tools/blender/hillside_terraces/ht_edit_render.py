"""Renders of the applied regrade, from temporary cameras added after the file
was saved (they are never written to it)."""

import os

import bpy
from mathutils import Vector

from ht_render import SHOTS, setup
from ht_site import RENDERS, SEA_Y

TOP = (-20.0, 340.0, 380.0, 770.0)


def run(prefix="applied_hillside_regrade_", folder=RENDERS):
    scene = bpy.context.scene
    cam = setup(scene, extra=("Reference_hillside",))
    out = []

    def shoot(name):
        scene.render.filepath = os.path.join(folder, f"{prefix}{name}.png")
        bpy.ops.render.render(write_still=True)
        out.append(scene.render.filepath)
        print(f"hillside_regrade: rendered {scene.render.filepath}")
    x0, x1, z0, z1 = TOP
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(x1 - x0, z1 - z0) * 1.02
    cam.location = ((x0 + x1) / 2, -(z0 + z1) / 2, 3000.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    scene.render.resolution_x = int(1800 * (x1 - x0) / (z1 - z0))
    scene.render.resolution_y = 1800
    shoot("top")
    cam.data.type = "PERSP"
    scene.render.resolution_x, scene.render.resolution_y = 2000, 1150
    for name in ("raised", "mouth"):
        s = SHOTS[name]
        e = Vector((s["eye"][0], -s["eye"][2], s["eye"][1] + SEA_Y))
        a = Vector((s["aim"][0], -s["aim"][2], s["aim"][1] + SEA_Y))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = s["lens"]
        near = [bpy.data.objects.get(n) for n in ("hillside_D1_footprint", "hillside_D1_lot_pads")] if name == "mouth" else []
        for o in near:
            if o is not None:
                o.hide_render = True          # at eye level by the mouth these run past the lens
        shoot(name)
        for o in near:
            if o is not None:
                o.hide_render = False
    return out
