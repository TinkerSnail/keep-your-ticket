"""The obliques from the town, rendered after the scratch copy was saved: the
temporary camera and sun are never written to any file."""

import math
import os

import bpy
from mathutils import Vector

from ht_site import PREFIX, RENDERS, SEA_Y

# eye heights are metres over the sea; the views look at the hill's face across the highway
SHOTS = {
    "oblique": {"eye": (-61.2, 8.6 + 0.0, 440.0), "aim": (80.0, 42.0, 565.0), "lens": 30.0,
                "label": "from Beach Road at the row, eye level"},
    "raised": {"eye": (-75.0, 48.0, 430.0), "aim": (82.0, 38.0, 570.0), "lens": 32.0,
               "label": "from 40 m over Beach Road at the row"},
    "mouth": {"eye": (22.0, 24.0, 462.0), "aim": (75.0, 38.0, 600.0), "lens": 18.0,
              "label": "from Second Street's underpass mouth, on the hill side of the highway, eye level",
              "keys": ("today", "D1", "D2", "B", "C")},
}


def layer_colls(lc, out):
    out[lc.name] = lc
    for c in lc.children:
        layer_colls(c, out)
    return out


def setup(scene, extra=()):
    lcs = layer_colls(bpy.context.view_layer.layer_collection, {})
    for name, lc in lcs.items():
        keep = name in ("Terrain", "Water", "Water_surfaces", "Reference", "Reference_proposals", "Proposal_hillside_terraces") \
            or name.startswith("hillside_terraces_") or name in extra
        lc.exclude = not keep
        if keep:
            lc.hide_viewport = False
            lc.collection.hide_render = False
    for o in bpy.data.collections["Reference_proposals"].objects:
        o.hide_render = True
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.66, 0.74, 0.84, 1.0)
        bg.inputs[1].default_value = 0.3
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 2.2
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (math.radians(55.0), 0.0, math.radians(-120.0))   # afternoon light from the south-west
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam_data.clip_start, cam_data.clip_end = 0.5, 20000.0
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 2000, 1150
    return cam


def run(objs, keys, R):
    scene = bpy.context.scene
    cam = setup(scene)
    for k in keys:
        for kk in keys:
            for o in objs[kk]:
                o.hide_render = kk != k
                o.hide_set(kk != k)
        for shot, s in SHOTS.items():
            if k not in s.get("keys", keys):
                continue
            e = Vector((s["eye"][0], -s["eye"][2], s["eye"][1] + SEA_Y))
            a = Vector((s["aim"][0], -s["aim"][2], s["aim"][1] + SEA_Y))
            cam.location = e
            cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
            cam.data.lens = s["lens"]
            scene.render.filepath = os.path.join(RENDERS, f"{PREFIX}{shot}_{k}.png")
            bpy.ops.render.render(write_still=True)
            print(f"hillside_terraces: rendered {scene.render.filepath}")
