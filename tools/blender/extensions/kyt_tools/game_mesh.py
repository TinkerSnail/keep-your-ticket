"""The Make game mesh button: the prop's parts become one clean, unwrapped mesh.

This is the step between modelling and texturing. While modelling, a prop is
many overlapping pieces: a leg passes through its foot, a slat's ends sit inside
the rail, a bolt is pushed into the wood. The game never sees most of those
faces, but it would still draw them, and at the texture stage every face takes
room on the UV map. So:

1. The parts in `export` are copied (modifiers and transforms applied) and
   joined into one object.
2. That object is unioned with itself (Blender's exact boolean), which fuses
   intersecting pieces into one surface and deletes every face inside another
   piece: the leg inside the foot, the slat ends inside the rail.
3. Faces lying on the ground (z = 0) and facing down are deleted, since the
   floor hides them.
4. Vertices closer than half a millimetre are merged.
5. The mesh is unwrapped (Smart UV Project) ready for the bake and paint-over.

Material assignments survive, so timber stays timber.

**Two files, and the original is never replaced.** Before anything changes, the
whole file as it stands is saved as `<name>_source.blend` beside it: the
original, every part separate and editable. The current file then becomes the
game-ready working file: the parts leave it, the fused mesh goes into `export`
under the prop's name, and the Stage becomes Texture. It keeps its name, so it
still sends to the same `assets/props/<name>.glb` and nothing in Godot moves.
Nothing here saves the working file; Christina saves it when she's happy.

A second press on a working file that already holds a game mesh does nothing
but say so, and the button refuses to run inside a `_source` file, so the
original can't be fused by accident.
"""

import math
import os

import bmesh
import bpy

from . import checks

SOURCE_SUFFIX = "_source"
GROUND_EPS = 0.0005
WELD_M = 0.0005


def source_path(blend_path):
    folder, name = os.path.split(blend_path)
    stem, ext = os.path.splitext(name)
    return os.path.join(folder, f"{stem}{SOURCE_SUFFIX}{ext}")


def _triangles(objects):
    n = 0
    for o in objects:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


def run(context):
    """Returns (ok, lines) for the panel and the report."""
    scene = context.scene
    path = bpy.data.filepath
    if not path:
        return False, ["Save the file first."]
    stem = os.path.splitext(os.path.basename(path))[0]
    if stem.endswith(SOURCE_SUFFIX):
        return False, ["This is the original (source) file; it stays as separate parts. "
                       "Make the game mesh from the working file."]
    export = bpy.data.collections.get(checks.EXPORT_COLLECTION)
    if export is None:
        return False, ["There is no 'export' collection."]
    if any(o.get("kyt_game_mesh") for o in export.objects):
        return False, ["This file already holds the game mesh. The original parts are in "
                       f"{os.path.basename(source_path(path))}."]
    parts = [o for o in export.objects if o.type == "MESH"]
    if not parts:
        return False, ["Nothing to fuse: put the prop's parts in 'export' first."]
    source = source_path(path)
    if os.path.exists(source):
        return False, [f"{os.path.basename(source)} already exists; not overwriting the original. "
                       "Move or rename it first if you mean to start over."]
    before = _triangles(parts)
    meshes_before = set(bpy.data.meshes)
    part_meshes = {o.data for o in parts}

    # The original, whole, before anything changes.
    bpy.ops.wm.save_as_mainfile(filepath=source, copy=True)

    if context.object and context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in scene.objects:
        o.select_set(False)

    copies = []
    for obj in parts:
        c = obj.copy()
        c.data = obj.data.copy()
        c.parent = None
        c.matrix_world = obj.matrix_world.copy()
        scene.collection.objects.link(c)
        c.select_set(True)
        copies.append(c)
    context.view_layer.objects.active = copies[0]
    bpy.ops.object.convert(target="MESH")
    if len(copies) > 1:
        bpy.ops.object.join()
    fused = context.view_layer.objects.active
    fused.data.transform(fused.matrix_world)
    fused.matrix_world.identity()

    # Self-union: fuses intersecting pieces and drops every interior face.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.intersect_boolean(operation="UNION", use_self=True, solver="EXACT")
    bpy.ops.object.mode_set(mode="OBJECT")

    bm = bmesh.new()
    bm.from_mesh(fused.data)
    floor = [f for f in bm.faces
             if f.normal.z < -0.99 and all(v.co.z <= GROUND_EPS for v in f.verts)]
    bmesh.ops.delete(bm, geom=floor, context="FACES")
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD_M)
    bm.to_mesh(fused.data)
    bm.free()

    # The union cuts a new edge wherever two pieces meet (round every bolt where
    # it enters the wood), which alone added more triangles than the hidden
    # faces saved. Dissolving edges between faces that are flat to within a
    # degree merges those slivers back into the face they came from, without
    # changing the shape or merging across a material boundary.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(1.0), use_dissolve_boundaries=False,
                                  delimit={"MATERIAL", "NORMAL"})
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    # The parts now live in the source file; here the fused mesh replaces them.
    for obj in parts:
        bpy.data.objects.remove(obj, do_unlink=True)
    # The parts' meshes and everything the copy, convert and join left behind.
    for mesh in (set(bpy.data.meshes) - meshes_before) | part_meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for coll in list(fused.users_collection):
        coll.objects.unlink(fused)
    export.objects.link(fused)
    fused.name = stem
    fused.data.name = stem
    fused["kyt_game_mesh"] = True
    if hasattr(scene, "kyt_stage"):
        scene.kyt_stage = "texture"

    after = _triangles([fused])
    bm = bmesh.new()
    bm.from_mesh(fused.data)
    open_edges = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    lines = [f"Game mesh made: {len(parts)} parts fused into one, "
             f"{before:,} → {after:,} triangles.",
             f"The original is saved as {os.path.basename(source)}. This file is now the "
             "game-ready working file; save it when you're happy.",
             "Stage set to Texture. The mesh is unwrapped and ready to bake."]
    if open_edges:
        lines.append(f"Note: {open_edges} open edges (where the floor faces were removed, "
                     "or thin parts). Harmless for a prop on the ground.")
    return True, lines
