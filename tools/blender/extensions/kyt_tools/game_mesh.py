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
5. The mesh is unwrapped ready for the bake and paint-over. If every part was
   unwrapped in the source file (`tools/blender/unwrap_parts.py`, which marks
   each `kyt_unwrapped`), each fused face takes its UVs back from the part face
   it was cut from, and what survives is packed onto the texture at one scale;
   otherwise Smart UV Project.

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
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import checks

SOURCE_SUFFIX = "_source"
GROUND_EPS = 0.0005
WELD_M = 0.0005
UV_MARGIN = 4 / 1024  # 4 px between pieces on a 1024 texture, 8 on a 2048
UV_SNAP = 1e-5  # in the parts' layout; a seam is at least a piece's margin apart


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


class _PartUVs:
    """The parts' own unwrap, kept aside to give back to the fused mesh.

    The exact boolean does not carry UVs across faithfully: it split the plaza
    bench's 1,489 seams into 2,917, every leg facet its own piece. But every face
    it outputs lies inside one face of one part, so each fused face looks up the
    part face it came from and takes its UVs from there, exactly (a triangle's
    UVs are affine across it)."""

    def __init__(self, objects):
        bm = bmesh.new()
        for o in objects:
            part = bmesh.new()
            part.from_mesh(o.data)
            part.transform(o.matrix_world)
            bmesh.ops.triangulate(part, faces=part.faces)
            tmp = bpy.data.meshes.new("_kyt_uv_ref")
            part.to_mesh(tmp)
            part.free()
            bm.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
        bm.faces.ensure_lookup_table()
        uv = bm.loops.layers.uv.active
        self.tris = [([l.vert.co.copy() for l in f.loops], [l[uv].uv.copy() for l in f.loops],
                      f.normal.copy()) for f in bm.faces]
        self.tree = BVHTree.FromBMesh(bm)
        bm.free()

    def source_of(self, face):
        """The part triangle `face` was cut from: the one it lies in. Only where two
        lie equally close (the two sides of a thin part) does facing decide; on a
        curve, a neighbouring triangle can face nearer the same way and is wrong."""
        c = face.calc_center_median()
        hits = self.tree.find_nearest_range(c, 0.002) or [self.tree.find_nearest(c)]
        near = min(h[3] for h in hits)
        best = max((h for h in hits if h[3] <= near + 1e-5),
                   key=lambda h: self.tris[h[2]][2].dot(face.normal))
        return self.tris[best[2]]

    def apply(self, bm):
        uv = bm.loops.layers.uv.active
        for f in bm.faces:
            (a, b, c), (ua, ub, uc), _ = self.source_of(f)
            e1, e2 = b - a, c - a
            d11, d12, d22 = e1.dot(e1), e1.dot(e2), e2.dot(e2)
            det = d11 * d22 - d12 * d12
            for loop in f.loops:
                p = loop.vert.co - a
                p1, p2 = p.dot(e1), p.dot(e2)
                s = (d22 * p1 - d12 * p2) / det
                t = (d11 * p2 - d12 * p1) / det
                loop[uv].uv = ua + (ub - ua) * s + (uc - ua) * t
        # Two faces meeting at a corner work its UV out from different part
        # triangles, and agree only to rounding. The packer joins pieces only
        # where UVs are exactly equal, so make agreeing corners identical.
        for v in bm.verts:
            kept = []
            for loop in v.link_loops:
                p = loop[uv].uv
                same = next((k for k in kept if (k - p).length < UV_SNAP), None)
                if same is None:
                    kept.append(p.copy())
                else:
                    loop[uv].uv = same


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
    keep_uvs = all(o.get("kyt_unwrapped") for o in parts)
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
    part_uvs = _PartUVs(copies) if keep_uvs else None
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
    if part_uvs:
        part_uvs.apply(bm)
    bm.to_mesh(fused.data)
    bm.free()

    # The union cuts a new edge wherever two pieces meet (round every bolt where
    # it enters the wood), which alone added more triangles than the hidden
    # faces saved. Dissolving edges between faces that are flat to within a
    # degree merges those slivers back into the face they came from, without
    # changing the shape or merging across a material boundary (or, when the
    # parts came unwrapped, across a UV seam).
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(1.0), use_dissolve_boundaries=False,
                                  delimit={"MATERIAL", "NORMAL", "UV"} if keep_uvs
                                  else {"MATERIAL", "NORMAL"})
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    if keep_uvs:
        # The pieces keep their shape, scale and turn (grain along U); packing
        # only moves them, and scales all of them together to fill the square.
        # Mirrored twins lie on top of each other by design and move as one.
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(rotate=False, scale=True, merge_overlap=True,
                                margin_method="FRACTION", margin=UV_MARGIN,
                                shape_method="CONCAVE")
    else:
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
             "Stage set to Texture. The mesh is unwrapped and ready to bake."
             + (" It kept the parts' own unwrap." if keep_uvs else "")]
    if open_edges:
        lines.append(f"Note: {open_edges} open edges (where the floor faces were removed, "
                     "or thin parts). Harmless for a prop on the ground.")
    return True, lines
