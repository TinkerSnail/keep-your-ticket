"""The Send to game button: write the prop's GLB where Godot looks for it.

`assets/source/props/<name>.blend` goes to `assets/props/<name>.glb`.

**One prop, one object.** However the prop is split up in Blender, the game gets
it merged: every mesh in `export` is copied, its modifiers applied, and the
copies joined into a single object at the origin, keeping one material slot per
material and every UV map. Christina keeps parts separate while she works; the
game draws a bench as one thing rather than four, which is six draws for the
plaza's six benches instead of twenty-four.

**Collision is derived, never authored,** the rule `tools/export_world_source.py`
follows for the range and the city. The merged object is named `<name>-col`,
which Godot's importer turns into the mesh plus a concave collision body on
physics layer 1, the layer seated guests and the player stand on. Parts with the
custom property `kyt_collision = "none"` are merged into a second object,
`<name>_visual`, that carries no hint and so never collides.

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


def _merged(context, parts, name):
    """Copies of `parts`, modifiers applied, joined into one object at the origin.

    Returns the object, or None when `parts` is empty. The copies' mesh data is
    their own, so nothing in the prop file is touched."""
    if not parts:
        return None
    scene = context.scene
    copies = []
    for obj in parts:
        copy = obj.copy()
        copy.data = obj.data.copy()
        copy.parent = None
        copy.matrix_world = obj.matrix_world.copy()
        copy[EXPORT_TAG] = True
        scene.collection.objects.link(copy)
        copies.append(copy)
    for o in scene.objects:
        o.select_set(False)
    for c in copies:
        c.select_set(True)
    context.view_layer.objects.active = copies[0]
    # Applying modifiers first, because a join takes each part's base mesh.
    bpy.ops.object.convert(target="MESH")
    if len(copies) > 1:
        bpy.ops.object.join()
    merged = context.view_layer.objects.active
    merged.name = name
    merged.data.name = name
    merged[EXPORT_TAG] = True
    # The join keeps the first part's origin; the game places a prop by the
    # origin, so bake the transform into the vertices and stand it at zero.
    merged.data.transform(merged.matrix_world)
    merged.matrix_world.identity()
    return merged


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
    previous_mode = context.object.mode if context.object else "OBJECT"
    if previous_mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in [o for o in bpy.data.objects if o.get(EXPORT_TAG)]:
        bpy.data.objects.remove(o, do_unlink=True)
    # Every mesh the copies, the conversion and the join make is ours to remove.
    meshes_before = set(bpy.data.meshes)

    stem =os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    solid = _merged(context, [o for o in objects if wants_collision(o)], f"{stem}-col")
    visual = _merged(context, [o for o in objects if not wants_collision(o)], f"{stem}_visual")
    temp = [o for o in (solid, visual) if o is not None]
    export_set = list(temp)

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
        for mesh in set(bpy.data.meshes) - meshes_before:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for o in scene.objects:
            o.select_set(o in previous_selection)
        context.view_layer.objects.active = previous_active
        if previous_mode != "OBJECT" and previous_active is not None:
            bpy.ops.object.mode_set(mode=previous_mode)

    size_kb = os.path.getsize(out) / 1024
    lines = [f"Sent to {os.path.relpath(out, root)} ({size_kb:.0f} KB), "
             f"{len(objects)} part{'s' if len(objects) != 1 else ''} merged into one."]
    lines += [text for level, text in findings if level == "WARNING"]
    lines.append("Godot picks it up the next time its window is focused or it starts.")
    return True, lines
