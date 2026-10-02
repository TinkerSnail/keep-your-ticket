"""The water and shore colour key of the world terrain master's reference layers (2026-10-01,
Christina: the generator's coast outlines "look the same as the canal proposals").

Recolours and re-bevels reference curves only; no terrain vertex moves (the terrain_world
hash is asserted equal). The palette (also in PALETTE below, and drawn by --key):

  generator shoreline reference  coast_north_outline, coast_south_outline   slate grey  (0.45, 0.50, 0.55)  bevel 1.5
  Coastal Creek (05A)            coastal_creek                               pale sky    (0.55, 0.78, 0.95)  bevel 1.5
  canal proposals and markers    PROPOSAL_canal*, PROPOSAL_water_*           azure       (0.00, 0.45, 1.00)  bevel 4-5
  ferry route                    ferry_route_beach_town_to_city              teal        (0.00, 0.80, 0.80)  bevel 4
  sightlines                     sunset_water_wedge_280_310, sunset_bearing  lilac       (0.75, 0.60, 1.00)  bevel 2
  lagoon proposals (plan)        PROPOSAL_tidal_lagoon, _lagoon_*            magenta     (0.90, 0.30, 0.90)
  new beach-front waterline      coast_extension_B_shoreline                 orange      (1.00, 0.55, 0.10)  bevel 4
  rail, plan lines               rail_*                                      plum        (0.45, 0.20, 0.60)
  rail, bluff shelf              rail_bluff_shelf_centreline                 wine        (0.60, 0.15, 0.30)
  rail, proposals                PROPOSAL_rail_viaduct_spur, _deck_stub      pink        (1.00, 0.55, 0.95)

PROPOSAL_rail_deck_stub was magenta (0.9, 0.3, 0.9), the lagoon proposals' colour: the one
hue collision found, fixed by giving it the rail proposals' pink. The canal option curves
themselves stay in the proposal scratch copy; none is added to the master until chosen.

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_reference_palette.py -- --out documentation/terrain/renders
    python3 tools/blender/world_terrain_reference_palette.py --key documentation/terrain/renders
"""
import hashlib
import json
import os
import sys

import numpy as np

PALETTE = [
    ("generator shoreline reference", "coast_north_outline, coast_south_outline", (0.45, 0.50, 0.55), 1.5),
    ("Coastal Creek (05A)", "coastal_creek", (0.55, 0.78, 0.95), 1.5),
    ("canal proposals and water markers", "PROPOSAL_canal<A..E>_*, PROPOSAL_water_*", (0.00, 0.45, 1.00), 4.0),
    ("ferry route", "ferry_route_beach_town_to_city", (0.00, 0.80, 0.80), 4.0),
    ("sightlines", "sunset_water_wedge_280_310, sunset_bearing_294", (0.75, 0.60, 1.00), 2.0),
    ("lagoon proposals (entrance plan)", "PROPOSAL_tidal_lagoon, PROPOSAL_lagoon_*", (0.90, 0.30, 0.90), 1.2),
    ("new beach-front waterline (edit 2 B)", "coast_extension_B_shoreline", (1.00, 0.55, 0.10), 4.0),
    ("rail, plan lines", "rail_*", (0.45, 0.20, 0.60), 3.0),
    ("rail, bluff shelf", "rail_bluff_shelf_centreline", (0.60, 0.15, 0.30), 3.0),
    ("rail, proposals (viaduct, deck stub)", "PROPOSAL_rail_*", (1.00, 0.55, 0.95), 3.0),
]
RECOLOUR = {  # object name -> (colour, bevel or None, note suffix)
    "coast_north_outline": ((0.45, 0.50, 0.55, 1.0), 1.5, "generator shoreline reference (ParkPlan outline), not water: slate, thin (2026-10-01)"),
    "coast_south_outline": ((0.45, 0.50, 0.55, 1.0), 1.5, "generator shoreline reference (ParkPlan outline), not water: slate, thin; still sunk under the beach front (2026-10-01)"),
    "coastal_creek": ((0.55, 0.78, 0.95, 1.0), 1.5, "Coastal Creek (05A): pale sky blue, thin (2026-10-01)"),
    "PROPOSAL_water_lagoon_canal_outlet": ((0.0, 0.45, 1.0, 1.0), 5.0, "canal marker: azure (2026-10-01)"),
    "PROPOSAL_water_creek_outlet_mid": ((0.0, 0.45, 1.0, 1.0), 5.0, "canal/water marker: azure (2026-10-01)"),
    "PROPOSAL_water_south_green_inlet": ((0.0, 0.45, 1.0, 1.0), 5.0, "canal/water marker: azure (2026-10-01)"),
    "PROPOSAL_rail_deck_stub": ((1.0, 0.55, 0.95, 1.0), None, "rail proposal pink, was magenta like the lagoon proposals (2026-10-01)"),
}


def to_blender(x, y, z):
    return (x, -z, y)


def draw_key(folder):
    from PIL import Image, ImageDraw
    W, row = 1100, 44
    img = Image.new("RGB", (W, row * (len(PALETTE) + 2) + 30), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    dr.text((20, 14), "world_terrain_master.blend: water and shore reference colour key (2026-10-01)", fill=(20, 20, 20))
    for i, (label, names, col, bevel) in enumerate(PALETTE):
        y = 50 + i * row
        rgb = tuple(int(c * 255) for c in col)
        h = max(4, int(bevel * 4))
        dr.rectangle([20, y + 20 - h // 2, 220, y + 20 + h // 2], fill=rgb)
        dr.text((240, y + 6), f"{label}", fill=(20, 20, 20))
        dr.text((240, y + 22), f"{names}   RGB ({col[0]:.2f}, {col[1]:.2f}, {col[2]:.2f})   bevel {bevel:g} m", fill=(90, 90, 90))
    path = os.path.join(folder, "colour_key.png")
    img.save(path)
    print(f"palette: wrote {path}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--key" in argv:
        draw_key(argv[argv.index("--key") + 1])
        return
    import bpy
    from mathutils import Vector
    out_dir = argv[argv.index("--out") + 1]
    obj = bpy.data.objects["terrain_world"]
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    hash_before = hashlib.sha1(co.tobytes()).hexdigest()

    def emission(mat, colour):
        mat.use_nodes = True
        nt = mat.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        o_ = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = colour
        nt.links.new(em.outputs[0], o_.inputs[0])

    done = []
    for name, (colour, bevel, suffix) in RECOLOUR.items():
        o = bpy.data.objects.get(name)
        if o is None or o.type != "CURVE":
            print(f"palette: missing {name}")
            continue
        if bevel is not None:
            o.data.bevel_depth = bevel
        for mat in o.data.materials:
            emission(mat, colour)
        o["kyt_note"] = (str(o.get("kyt_note", "")) + " | " + suffix).strip(" |")
        done.append(name)
    notes = bpy.data.texts.get("README")
    if notes:
        notes.write("\nCOLOUR KEY, water and shore (tools/blender/world_terrain_reference_palette.py, 2026-10-01; renders/colour_key.png):\n")
        for label, names, col, bevel in PALETTE:
            notes.write(f"  {label}: {names}  RGB ({col[0]:.2f}, {col[1]:.2f}, {col[2]:.2f})  bevel {bevel:g}\n")
        notes.write("  Canal option curves (A..E) live only in the proposal scratch copies until one is chosen.\n")
    scene = bpy.context.scene
    scene["kyt_reference_notes"] = json.dumps(json.loads(scene.get("kyt_reference_notes", "[]")) +
                                              [{"group": "palette", "script": "tools/blender/world_terrain_reference_palette.py", "date": "2026-10-01", "recoloured": done}])
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    hash_after = hashlib.sha1(co2.tobytes()).hexdigest()
    assert hash_after == hash_before, "the terrain moved"
    cams = [ob.name for ob in bpy.data.objects if ob.type in ("CAMERA", "LIGHT")]
    bpy.ops.wm.save_mainfile()
    print(f"palette: recoloured {done}; cameras/lights {cams}; terrain hash {hash_before} == {hash_after}; saved {bpy.data.filepath}")

    # re-render the ferry top-down with the new colours (same frame as world_terrain_reference_ferry.py)
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.7854, 0.0, -2.0944)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0
    x0, x1, z0, z1, px = -1100.0, 800.0, -300.0, 2700.0, 2400
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(ex, ez)
    cam.location = to_blender(cx, 5000.0, cz)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
    scene.render.filepath = os.path.join(out_dir, "reference_ferry_top.png")
    bpy.ops.render.render(write_still=True)
    print(f"palette: rendered {scene.render.filepath}")


if __name__ == "__main__":
    main()
