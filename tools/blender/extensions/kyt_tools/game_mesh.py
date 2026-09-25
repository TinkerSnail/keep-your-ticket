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

**Rebuild game mesh** is for later: the parts in `<name>_source.blend` have
changed and the working file's game mesh should follow. It fuses them the same
way, in the working file, and swaps the result into the existing game-mesh
object, which keeps its name, its place and its material (a painted canvas's
single material goes on every face). The source file is only read. It reports
how far the shape moved and how far the UVs moved at the same points on the
surface, in texture pixels: a painted texture lines up only where they didn't.
Nothing is saved; the undo step takes it back.
"""

import json
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
LINES_UP_PX = 1.5  # a rebuilt piece this close to where it was keeps its painting


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
    UVs are affine across it). It records that part too, as the face attribute
    `kyt_part` indexing the mesh's `kyt_parts` list of names: the colour-ID a
    paint mask needs (the arms, the boards) once the parts are one mesh."""

    def __init__(self, objects, names):
        self.names = list(names)
        owner = []
        bm = bmesh.new()
        for index, o in enumerate(objects):
            part = bmesh.new()
            part.from_mesh(o.data)
            part.transform(o.matrix_world)
            bmesh.ops.triangulate(part, faces=part.faces)
            tmp = bpy.data.meshes.new("_kyt_uv_ref")
            part.to_mesh(tmp)
            part.free()
            bm.from_mesh(tmp)
            owner.extend([index] * len(tmp.polygons))
            bpy.data.meshes.remove(tmp)
        bm.faces.ensure_lookup_table()
        uv = bm.loops.layers.uv.active
        self.tris = [([l.vert.co.copy() for l in f.loops], [l[uv].uv.copy() for l in f.loops],
                      f.normal.copy(), owner[f.index]) for f in bm.faces]
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

    def apply(self, bm, mesh):
        uv = bm.loops.layers.uv.active
        part = bm.faces.layers.int.get("kyt_part") or bm.faces.layers.int.new("kyt_part")
        mesh["kyt_parts"] = json.dumps(self.names)
        for f in bm.faces:
            (a, b, c), (ua, ub, uc), _, f[part] = self.source_of(f)
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


def _fuse(context, parts, pack=True):
    """The parts, copied, fused into one mesh with their unwrap packed (or, with
    `pack` off, left in the parts' own loose layout); returns (the fused object,
    linked to the scene's own collection, and whether it kept the parts' own
    unwrap). The parts themselves are untouched."""
    scene = context.scene
    keep_uvs = all(o.get("kyt_unwrapped") for o in parts)
    if context.object and context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in context.view_layer.objects:
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
    part_uvs = _PartUVs(copies, [o.name for o in parts]) if keep_uvs else None
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
        part_uvs.apply(bm, fused.data)
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
    if keep_uvs and not pack:
        pass
    elif keep_uvs:
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
    return fused, keep_uvs


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

    fused, keep_uvs = _fuse(context, parts)

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


def _uv_islands(bm):
    """UV pieces of a bmesh: faces joined across edges whose UVs agree. Each is
    (faces, the part most of its faces came from, UV bounds min, max, area,
    the piece's centre on the model)."""
    uv = bm.loops.layers.uv.active
    part = bm.faces.layers.int.get("kyt_part")
    bm.faces.ensure_lookup_table()
    parent = list(range(len(bm.faces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        a, b = e.link_faces
        la = {l.vert: l[uv].uv for l in a.loops}
        lb = {l.vert: l[uv].uv for l in b.loops}
        if all(la[v] == lb[v] for v in e.verts):
            parent[find(a.index)] = find(b.index)
    groups = {}
    for f in bm.faces:
        groups.setdefault(find(f.index), []).append(f)
    out = []
    for faces in groups.values():
        pts = [l[uv].uv for f in faces for l in f.loops]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts)))
        area = 0.0
        for f in faces:
            poly = [l[uv].uv for l in f.loops]
            area += abs(sum(poly[k].x * poly[k - 1].y - poly[k - 1].x * poly[k].y
                            for k in range(len(poly)))) / 2
        owners = [f[part] for f in faces] if part else [0]
        centre = sum((f.calc_center_median() for f in faces), Vector()) / len(faces)
        out.append((faces, max(set(owners), key=owners.count), lo, hi, area, centre))
    return out


def _uv_per_metre(mesh):
    """UV units per metre along the mesh's edges (the median)."""
    uv = mesh.uv_layers.active.data
    ratios = []
    for p in mesh.polygons:
        idx = list(p.loop_indices)
        for k in range(len(idx)):
            a, b = idx[k - 1], idx[k]
            d3 = (mesh.vertices[mesh.loops[a].vertex_index].co - mesh.vertices[mesh.loops[b].vertex_index].co).length
            if d3 > 0.002:
                ratios.append((uv[a].uv - uv[b].uv).length / d3)
    ratios.sort()
    return ratios[len(ratios) // 2] if ratios else 1.0


def _keep_layout(old_mesh, new_mesh, texture_px):
    """Put each new UV piece where the same piece sat in the old mesh's layout,
    so painting stays on it; pack only new or reshaped pieces, into the space
    left, at the same scale. Returns (pieces kept, pieces repacked)."""
    names_old = json.loads(old_mesh.get("kyt_parts", "[]"))
    names_new = json.loads(new_mesh.get("kyt_parts", "[]"))
    ratio = _uv_per_metre(old_mesh) / _uv_per_metre(new_mesh)
    tol = 2.0 / texture_px  # a piece is the same if its bounds agree to 2 px

    obm = bmesh.new()
    obm.from_mesh(old_mesh)
    old_pieces = {}
    for faces, owner, lo, hi, area, centre in _uv_islands(obm):
        name = names_old[owner] if owner < len(names_old) else None
        old_pieces.setdefault(name, []).append((lo, hi, area, centre))
    obm.free()
    used = set()

    bm = bmesh.new()
    bm.from_mesh(new_mesh)
    uv = bm.loops.layers.uv.active
    kept = repacked = 0
    for faces, owner, lo, hi, area, centre in _uv_islands(bm):
        name = names_new[owner] if owner < len(names_new) else None
        size = (hi - lo) * ratio
        scaled_area = area * ratio * ratio
        # Among the part's old pieces of the same shape (a board's two end caps
        # are alike), the one that sat nearest this piece on the model.
        match, best = None, None
        for i, (olo, ohi, oarea, ocentre) in enumerate(old_pieces.get(name, [])):
            osize = ohi - olo
            if (name, i) in used:
                continue
            if abs(osize.x - size.x) <= tol and abs(osize.y - size.y) <= tol \
                    and abs(oarea - scaled_area) <= 0.05 * max(oarea, 1e-9):
                d = (ocentre - centre).length
                if best is None or d < best[0]:
                    best = (d, i, olo)
        if best:
            used.add((name, best[1]))
            match = best[2]
        for f in faces:
            for l in f.loops:
                if match is not None:
                    l[uv].uv = (l[uv].uv - lo) * ratio + match
                    l[uv].pin_uv = True
                else:
                    l[uv].uv = l[uv].uv * ratio
                    l[uv].pin_uv = False
        kept += match is not None
        repacked += match is None
    bm.to_mesh(new_mesh)
    bm.free()
    return kept, repacked


def _surface(mesh):
    """A BVH over a mesh's triangles, with each triangle's corners, UVs, normal
    and part name (from `kyt_part`, which triangulating copies to each piece)."""
    names = json.loads(mesh.get("kyt_parts", "[]"))
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    uv = bm.loops.layers.uv.active
    part = bm.faces.layers.int.get("kyt_part")
    tris = [([l.vert.co.copy() for l in f.loops], [l[uv].uv.copy() for l in f.loops] if uv else None,
             f.normal.copy(), names[f[part]] if part and f[part] < len(names) else None)
            for f in bm.faces]
    tree = BVHTree.FromBMesh(bm)
    verts = [v.co.copy() for v in bm.verts]
    bm.free()
    return tree, tris, verts


def _uv_at(tri, p):
    (a, b, c), (ua, ub, uc) = tri[0], tri[1]
    e1, e2 = b - a, c - a
    d11, d12, d22 = e1.dot(e1), e1.dot(e2), e2.dot(e2)
    det = d11 * d22 - d12 * d12
    if abs(det) < 1e-18:
        return ua
    r = p - a
    s = (d22 * r.dot(e1) - d12 * r.dot(e2)) / det
    t = (d11 * r.dot(e2) - d12 * r.dot(e1)) / det
    return ua + (ub - ua) * s + (uc - ua) * t


def _compare(old_mesh, new_mesh, texture_px):
    """(how far the shape moved, in metres; the UV shift at matching points on
    the surface, in texture pixels: the largest and the 99th percentile; how many
    of the new faces have no match in the old shape)."""
    old_tree, old_tris, old_verts = _surface(old_mesh)
    new_tree, _, new_verts = _surface(new_mesh)
    moved = max(max((old_tree.find_nearest(v)[3] for v in new_verts), default=0.0),
                max((new_tree.find_nearest(v)[3] for v in old_verts), default=0.0))
    shifts, unmatched = [], 0
    uv = new_mesh.uv_layers.active.data if new_mesh.uv_layers else None
    new_names = json.loads(new_mesh.get("kyt_parts", "[]"))
    new_part = new_mesh.attributes.get("kyt_part")
    # A point surely on each face: the middle of its first triangle (a notched
    # face's centre can lie off the face).
    new_mesh.calc_loop_triangles()
    first = {}
    for t in new_mesh.loop_triangles:
        first.setdefault(t.polygon_index, t)
    for p in new_mesh.polygons:
        t = first[p.index]
        c = sum((new_mesh.vertices[v].co for v in t.vertices), Vector()) / 3
        name = new_names[new_part.data[p.index].value] if new_part and new_names else None
        hits = old_tree.find_nearest_range(c, 0.001)
        hits = [h for h in hits if old_tris[h[2]][2].dot(p.normal) >= 0.9
                and (name is None or old_tris[h[2]][3] == name)]
        if not hits or uv is None or old_tris[hits[0][2]][1] is None:
            unmatched += 1
            continue
        index = min(hits, key=lambda h: h[3])[2]
        mine = sum((uv[i].uv for i in t.loops), Vector((0.0, 0.0))) / 3
        shifts.append((mine - _uv_at(old_tris[index], c)).length * texture_px)
    shifts.sort()
    top = shifts[-1] if shifts else 0.0
    p99 = shifts[int(len(shifts) * 0.99) - 1] if shifts else 0.0
    return moved, top, p99, unmatched


def _texture_px(mesh):
    """The width of the first image the mesh's materials read (its canvas)."""
    for m in mesh.materials:
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image and n.image.size[0]:
                    return n.image.size[0]
    return 2048


def rebuild(context):
    """Rebuild the working file's game mesh from `<name>_source.blend`.
    Returns (ok, lines) for the panel and the report."""
    path = bpy.data.filepath
    if not path:
        return False, ["Save the file first."]
    stem = os.path.splitext(os.path.basename(path))[0]
    if stem.endswith(SOURCE_SUFFIX):
        return False, ["This is the original (source) file. Rebuild from the working file."]
    export = bpy.data.collections.get(checks.EXPORT_COLLECTION)
    game = next((o for o in export.objects if o.get("kyt_game_mesh")), None) if export else None
    if game is None:
        return False, ["This file has no game mesh yet: use Make game mesh."]
    source = source_path(path)
    if not os.path.exists(source):
        return False, [f"{os.path.basename(source)} isn't beside this file; nothing to rebuild from."]

    objects_before, meshes_before = set(bpy.data.objects), set(bpy.data.meshes)
    materials_before, collections_before = set(bpy.data.materials), set(bpy.data.collections)
    with bpy.data.libraries.load(source, link=False) as (theirs, ours):
        ours.collections = [c for c in theirs.collections if c == checks.EXPORT_COLLECTION]
    loaded = ours.collections[0] if ours.collections else None
    parts = [o for o in loaded.all_objects if o.type == "MESH"] if loaded else []
    if not parts:
        return False, [f"{os.path.basename(source)} has no parts in its export collection."]
    # A loaded object's world matrix is only worked out once it is in a scene;
    # until then every part reads as standing at the origin.
    context.scene.collection.children.link(loaded)
    context.view_layer.update()
    before = _triangles(parts)

    old = game.data
    texture_px = _texture_px(old)
    keep_layout = bool(old.uv_layers) and "kyt_parts" in old
    fused, keep_uvs = _fuse(context, parts, pack=not keep_layout)
    kept = repacked = 0
    if keep_uvs and keep_layout:
        kept, repacked = _keep_layout(old, fused.data, texture_px)
        if repacked:
            for o in context.view_layer.objects:
                o.select_set(False)
            fused.select_set(True)
            context.view_layer.objects.active = fused
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.select_all(action="SELECT")
            bpy.ops.uv.pack_islands(rotate=False, scale=False, merge_overlap=True,
                                    margin_method="FRACTION", margin=UV_MARGIN,
                                    shape_method="CONCAVE", pin=True, pin_method="LOCKED")
            bpy.ops.object.mode_set(mode="OBJECT")
        bm = bmesh.new()
        bm.from_mesh(fused.data)
        pin = bm.loops.layers.uv.active
        for f in bm.faces:
            for l in f.loops:
                l[pin].pin_uv = False
        bm.to_mesh(fused.data)
        bm.free()
    moved, uv_top, uv_p99, unmatched = _compare(old, fused.data, texture_px)

    # The material stays the game mesh's own. A painted canvas is one material
    # for every face; part materials are matched by name.
    by_name = {m.name: m for m in materials_before}
    if len(old.materials) == 1:
        fused.data.materials.clear()
        fused.data.materials.append(old.materials[0])
        for p in fused.data.polygons:
            p.material_index = 0
    else:
        for i, m in enumerate(fused.data.materials):
            base = m.name.rsplit(".", 1)[0] if m and m.name.rsplit(".", 1)[-1].isdigit() else (m.name if m else None)
            if base in by_name:
                fused.data.materials[i] = by_name[base]

    mesh = fused.data
    game.data = mesh
    bpy.data.meshes.remove(old)
    mesh.name = stem
    bpy.data.objects.remove(fused, do_unlink=True)
    # Everything the load brought in: the source's parts, their meshes, its
    # export collection and materials no one uses now.
    for o in set(bpy.data.objects) - objects_before:
        bpy.data.objects.remove(o, do_unlink=True)
    for c in set(bpy.data.collections) - collections_before:
        bpy.data.collections.remove(c)
    for m in set(bpy.data.meshes) - meshes_before:
        if m.users == 0:
            bpy.data.meshes.remove(m)
    for m in set(bpy.data.materials) - materials_before:
        if m.users == 0:
            bpy.data.materials.remove(m)
    context.view_layer.objects.active = game
    game.select_set(True)

    after = _triangles([game])
    lines = [f"Game mesh rebuilt from {os.path.basename(source)}: {len(parts)} parts, "
             f"{before:,} → {after:,} triangles.",
             f"The shape moved at most {moved * 1000:.1f} mm."]
    if not keep_uvs:
        lines.append("Warning: the parts aren't all unwrapped for their own texture, so this "
                     "used Smart UV Project; any painting on the old layout won't line up.")
    else:
        if kept or repacked:
            lines.append(f"{kept} UV pieces kept their place in the old layout"
                         + (f"; {repacked} new or reshaped pieces were packed into the space left, "
                            "with no painting yet." if repacked else "."))
        if uv_p99 <= LINES_UP_PX:
            lines.append("Where the surface didn't change, the painting lines up "
                         f"(99% within {uv_p99:.1f} px).")
        else:
            lines.append(f"Warning: the unwrap moved: 99% of the surface within {uv_p99:.1f} px, "
                         f"at most {uv_top:.1f} px. Painting lines up only where it didn't move.")
    if unmatched:
        lines.append(f"{unmatched} faces are new or reshaped; they have no painting yet.")
    lines.append("Nothing is saved: check it, then save.")
    return True, lines
