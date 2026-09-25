"""The paint canvas for a prop's own texture, and its one material.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>.blend \
        --python tools/blender/paint_canvas.py -- [--size 2048] [--orm-size 1024] [--guide-only] [--save]

Runs on the game-ready working file (after Make game mesh), whose game mesh is
unwrapped for its own texture. Writes three images to
`assets/source/textures/<prop>/`:

- `<prop>_colour.png`: each piece filled with the colour its material has now,
  and spread a few pixels past its edge so mipmaps don't pull in the gaps.
  **Paint on this**, in Blender texture paint or over the PNG in Photoshop or
  Procreate.
- `<prop>_orm.png`: occlusion, roughness and metalness packed in red, green
  and blue (the glTF and Godot convention), from the materials' values; no
  occlusion yet (red is white).
- `<prop>_uv_guide.png`: transparent, the outline of every piece in white, to
  lay over the colour as a locked top layer in Photoshop or Procreate and hide
  before exporting. Drawn from the mesh, so always safe to redraw:
  `--guide-only` redraws it and touches nothing else.

Then the game mesh's materials (timber, cast iron, fixings) are replaced by one
material named after the prop that reads both images, so each placement is one
draw and the prop looks as it did until the colour is painted. Refuses to
overwrite the colour or ORM PNG: by then it may be Christina's painting. Without `--save`
the file is not written.
"""

import os
import sys

import bmesh
import bpy
import numpy as np

MARGIN_PX = 16


def arg(argv, name, default):
    return int(argv[argv.index(name) + 1]) if name in argv else default


def bake_emission(obj, image, value_of):
    """Bake each material's `value_of(principled)` colour into `image` as emission."""
    saved = []
    for slot in obj.material_slots:
        mat = slot.material
        nt = mat.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = value_of(bsdf)
        target = nt.nodes.new("ShaderNodeTexImage")
        target.image = image
        nt.nodes.active = target
        was = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
        nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
        saved.append((nt, out, was, emit, target))
    bpy.ops.object.bake(type="EMIT", margin=MARGIN_PX, margin_type="EXTEND", use_clear=True)
    for nt, out, was, emit, target in saved:
        if was is not None:
            nt.links.new(was, out.inputs["Surface"])
        nt.nodes.remove(emit)
        nt.nodes.remove(target)


def write_uv_guide(obj, path, size):
    """The outline of every UV piece, white on transparent: edges where the two
    faces disagree in UV, or that have one face. Mirrored twins share outlines."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    segs = []
    for e in bm.edges:
        ends = []
        for f in e.link_faces:
            at = {l.vert: l[uv].uv.copy() for l in f.loops}
            ends.append((at[e.verts[0]], at[e.verts[1]]))
        if len(ends) == 2 and all((ends[0][i] - ends[1][i]).length < 1e-6 for i in (0, 1)):
            continue
        segs.extend(ends)
    bm.free()
    px = np.zeros((size, size, 4), dtype=np.float32)
    for a, b in segs:
        n = int(max(abs(b.x - a.x), abs(b.y - a.y)) * size * 2) + 2
        t = np.linspace(0.0, 1.0, n)
        x = np.clip(((a.x + (b.x - a.x) * t) * size).astype(int), 0, size - 1)
        y = np.clip(((a.y + (b.y - a.y) * t) * size).astype(int), 0, size - 1)
        for dx in (0, 1):
            for dy in (0, 1):
                px[np.clip(y + dy, 0, size - 1), np.clip(x + dx, 0, size - 1)] = (1.0, 1.0, 1.0, 1.0)
    img = bpy.data.images.new(os.path.basename(path), size, size, alpha=True)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    size = arg(argv, "--size", 2048)
    orm_size = arg(argv, "--orm-size", 1024)
    blend = bpy.data.filepath
    name = os.path.splitext(os.path.basename(blend))[0]
    root = blend[:blend.index(os.sep + "assets" + os.sep)]
    folder = os.path.join(root, "assets", "source", "textures", name)
    colour_path = os.path.join(folder, f"{name}_colour.png")
    orm_path = os.path.join(folder, f"{name}_orm.png")
    guide_path = os.path.join(folder, f"{name}_uv_guide.png")
    if "--guide-only" in argv:
        obj = next(o for o in bpy.data.collections["export"].objects if o.get("kyt_game_mesh"))
        write_uv_guide(obj, guide_path, size)
        print(f"paint_canvas: redrew {os.path.relpath(guide_path, root)}")
        return
    for path in (colour_path, orm_path):
        if os.path.exists(path):
            raise SystemExit(f"paint_canvas: {path} exists (it may be painted); leaving everything alone")
    obj = next(o for o in bpy.data.collections["export"].objects if o.get("kyt_game_mesh"))
    if not obj.data.uv_layers:
        raise SystemExit("paint_canvas: the game mesh has no UVs; make the game mesh first")
    os.makedirs(folder, exist_ok=True)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    scene.cycles.device = "CPU"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    colour = bpy.data.images.new(f"{name}_colour", size, size, alpha=False)
    bake_emission(obj, colour, lambda b: tuple(b.inputs["Base Color"].default_value))
    colour.filepath_raw = colour_path
    colour.file_format = "PNG"
    colour.save()

    orm = bpy.data.images.new(f"{name}_orm", orm_size, orm_size, alpha=False)
    orm.colorspace_settings.name = "Non-Color"
    bake_emission(obj, orm, lambda b: (1.0, b.inputs["Roughness"].default_value,
                                       b.inputs["Metallic"].default_value, 1.0))
    orm.filepath_raw = orm_path
    orm.file_format = "PNG"
    orm.save()
    write_uv_guide(obj, guide_path, size)
    for img, path in ((colour, colour_path), (orm, orm_path)):
        img.filepath = bpy.path.relpath(path)
        img.source = "FILE"
        img.reload()

    # One material reading both: colour to base colour; the ORM's green and blue
    # to roughness and metalness, the wiring the glTF exporter recognises.
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = obj.data.uv_layers[0].name
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = colour
    orm_node = nt.nodes.new("ShaderNodeTexImage")
    orm_node.image = orm
    split = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(uv.outputs["UV"], col.inputs["Vector"])
    nt.links.new(uv.outputs["UV"], orm_node.inputs["Vector"])
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(orm_node.outputs["Color"], split.inputs["Color"])
    nt.links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    for n, x in ((uv, -900), (col, -600), (orm_node, -600), (split, -300), (bsdf, 0), (out, 300)):
        n.location = (x, -320 if n is orm_node or n is split else 0)
    nt.nodes.active = col  # texture paint paints the colour image
    mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)

    me = obj.data
    for p in me.polygons:
        p.material_index = 0
    me.materials.clear()
    me.materials.append(mat)
    scene.render.engine = "BLENDER_EEVEE"
    print(f"paint_canvas: {os.path.relpath(colour_path, root)} ({size} px), "
          f"{os.path.relpath(orm_path, root)} ({orm_size} px), and its UV guide; "
          f"'{obj.name}' now wears one material, '{name}'")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


main()
