"""The Send to game button: write the prop's GLB where Godot looks for it.

`assets/source/props/<name>.blend` goes to `assets/props/<name>.glb`. The rule
is the same one `tools/export_world_source.py` follows for the range and the
city: collision is derived from the visible mesh on export, never authored
beside it. Each exported mesh travels as a throwaway copy named `<name>-col`,
which Godot's importer turns into the mesh plus a concave collision body on
physics layer 1, the layer seated guests and the player stand on. A mesh with
the custom property `kyt_collision = "none"` goes without the hint.

The .blend is never saved here and the copies are removed afterwards, so the
file, its selection and its undo history are as they were.
"""

import os

import bpy

from . import checks

EXPORT_TAG = "kyt_send_tmp"


def output_path(blend_path, root):
    stem = os.path.splitext(os.path.basename(blend_path))[0]
    return os.path.join(root, "assets", "props", f"{stem}.glb")


def wants_collision(obj):
    return str(obj.get("kyt_collision", "trimesh")).lower() != "none"


def run(context):
    """Check, then export. Returns (ok, lines) for the panel and the report."""
    findings = checks.run(context)
    errors = [text for level, text in findings if level == "ERROR"]
    if errors:
        return False, ["Not sent: fix these first."] + errors

    scene = context.scene
    root = checks.project_root(bpy.data.filepath)
    out = output_path(bpy.data.filepath, root)
    objects = checks.export_objects(scene)

    previous_selection = [o for o in scene.objects if o.select_get()]
    previous_active = context.view_layer.objects.active
    for o in [o for o in bpy.data.objects if o.get(EXPORT_TAG)]:
        bpy.data.objects.remove(o, do_unlink=True)

    temp, export_set = [], []
    for obj in objects:
        if wants_collision(obj):
            copy = obj.copy()
            copy.name = f"{obj.name}-col"
            copy[EXPORT_TAG] = True
            # Keep the world transform when the original has a parent.
            copy.parent = None
            copy.matrix_world = obj.matrix_world
            scene.collection.objects.link(copy)
            temp.append(copy)
            export_set.append(copy)
        else:
            export_set.append(obj)

    try:
        for o in scene.objects:
            o.select_set(False)
        for o in export_set:
            o.select_set(True)
        context.view_layer.objects.active = export_set[0]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.export_scene.gltf(
            filepath=out,
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_animations=False,
            export_cameras=False,
            export_lights=False,
            export_materials="EXPORT",
            export_normals=True,
            export_texcoords=True,
            export_tangents=False,
            export_skins=False,
            export_morph=False,
            export_extras=False,
        )
    finally:
        for o in temp:
            bpy.data.objects.remove(o, do_unlink=True)
        for o in scene.objects:
            o.select_set(o in previous_selection)
        context.view_layer.objects.active = previous_active

    size_kb = os.path.getsize(out) / 1024
    lines = [f"Sent to {os.path.relpath(out, root)} ({size_kb:.0f} KB)."]
    lines += [text for level, text in findings if level == "WARNING"]
    lines.append("Godot picks it up the next time its window is focused or it starts.")
    return True, lines
