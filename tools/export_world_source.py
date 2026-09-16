"""Derive a mounted world GLB from its editable Blender master.

Run from the project root, or from Blender's Text editor with the master open:

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/<master>.blend --python tools/export_world_source.py

`tools/export_world_source.sh <master.blend>` wraps that line. The GLB lands at
`assets/<master>.glb`, which is where every mounted wrapper already looks.
Serves the range (`range_forest_distinct_background.blend`) and the city
(`far_shore_city_relocation.blend`); a master with no rock collections simply
gets no rock cells.

What it does, and what it deliberately does not do
--------------------------------------------------
The master holds every visible object of its world piece: for the range the
terrain modules, canopy masses, volcanic plug and some 7,500 separately
selectable coastal boulders; for the city the peninsula, earthworks, roads,
bridge and ferry. Those objects are the art and they are never touched here. This script reads them, builds throwaway export-only objects
beside them, writes the GLB, and deletes what it built. It never calls
`save_mainfile`, so running it from inside Blender leaves the file exactly as
it was, including the selection.

Collision is derived, not authored. Before 2026-09-15 each boulder had a
hand-placed `_collision-colonly` twin object, which meant moving a boulder in
the viewport silently left its collision behind; eight of them had already
drifted that way. Now:

- A mesh object is exported under its own name with Godot's `-col` import
  hint, so the importer builds a concave collision body from the visible mesh
  itself. An object carrying the custom property `kyt_collision = "none"` (the
  canopy masses, the bridge, the ferry) is exported without the hint, and so is
  anything that is not a mesh: curves such as the bridge hangers export as
  meshes but never collide.
- Boulders are anything in a collection whose name contains `rock` or
  `boulder`, or whose own name does. They are baked in world space into one
  mesh per `CELL_M` plan cell, with each boulder's material becoming a surface
  of that cell mesh, so a recoloured boulder keeps its colour and a moved one
  moves. The cell mesh carries `-col`, so the same geometry is its collision.
  A boulder whose longest world dimension is under `COLLISION_MIN_SIZE_M`, or
  which carries `kyt_collision = "none"`, is drawn but left out of collision;
  a cell that has any such stone gets a separate `-colonly` mesh of the rest.

The cell size is a balance: larger cells mean fewer nodes and bodies, smaller
cells mean the renderer and the physics broadphase cull more of the field
from any one standpoint. 250 m gives about fifty cells for the current field.

A master that still contains a `-colonly` object is refused, because that is
the defect this script replaced and exporting it would put a twin and a
derived body under the same rock.
"""

import os
import re
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

EXPORTABLE = {"MESH", "CURVE", "SURFACE", "FONT", "META"}
CELL_M = 250.0
COLLISION_MIN_SIZE_M = 1.0
ROCK_WORD = re.compile(r"rock|boulder", re.IGNORECASE)
TWIN_SUFFIX = re.compile(r"-(?:conv)?col(?:only)?(?:\.\d+)?$")
EXPORT_TAG = "kyt_export_tmp"


def project_root() -> str:
    blend = bpy.data.filepath
    if not blend:
        raise SystemExit("export_world_source: no file is open; run against a master")
    return os.path.abspath(os.path.join(os.path.dirname(blend), os.pardir, os.pardir))


def output_path(root: str) -> str:
    argv = sys.argv
    if "--" in argv:
        rest = argv[argv.index("--") + 1:]
        if "--output" in rest:
            return os.path.abspath(rest[rest.index("--output") + 1])
    stem = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    return os.path.join(root, "assets", f"{stem}.glb")


def is_rock(obj: bpy.types.Object) -> bool:
    if obj.type != "MESH":
        return False
    if any(ROCK_WORD.search(c.name) for c in obj.users_collection):
        return True
    return bool(ROCK_WORD.search(obj.name))


def wants_collision(obj: bpy.types.Object) -> bool:
    if obj.type != "MESH":
        return False
    return str(obj.get("kyt_collision", "trimesh")).lower() != "none"


def cell_of(location: Vector) -> tuple:
    return (int(np.floor(location.x / CELL_M)), int(np.floor(location.y / CELL_M)))


def cell_name(cell: tuple) -> str:
    def part(axis: str, value: int) -> str:
        return f"{axis}{'m' if value < 0 else 'p'}{abs(value)}"
    return f"range_rocks_{part('x', cell[0])}_{part('y', cell[1])}"


class Batch:
    """Accumulates world-space triangles for one cell, one material per surface."""

    def __init__(self, cell: tuple):
        self.cell = cell
        self.centre = Vector(((cell[0] + 0.5) * CELL_M, (cell[1] + 0.5) * CELL_M, 0.0))
        self.verts = []
        self.tris = []
        self.mat_index = []
        self.smooth = []
        self.materials = []
        self.count = 0
        self.no_collision = []

    def add(self, obj: bpy.types.Object, depsgraph, collision: bool) -> None:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            n_v = len(mesh.vertices)
            n_t = len(mesh.loop_triangles)
            if n_v == 0 or n_t == 0:
                return
            co = np.empty(n_v * 3, dtype=np.float32)
            mesh.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3).astype(np.float64)
            m = np.array(obj.matrix_world, dtype=np.float64)
            world = co @ m[:3, :3].T + m[:3, 3]
            world -= np.array(self.centre, dtype=np.float64)
            tri = np.empty(n_t * 3, dtype=np.int32)
            mesh.loop_triangles.foreach_get("vertices", tri)
            tri = tri.reshape(-1, 3)
            poly_of_tri = np.empty(n_t, dtype=np.int32)
            mesh.loop_triangles.foreach_get("polygon_index", poly_of_tri)
            poly_mat = np.empty(len(mesh.polygons), dtype=np.int32)
            mesh.polygons.foreach_get("material_index", poly_mat)
            poly_smooth = np.empty(len(mesh.polygons), dtype=bool)
            mesh.polygons.foreach_get("use_smooth", poly_smooth)
            # A negative-determinant transform (mirror) flips winding; keep the
            # outward face by reversing those triangles.
            if np.linalg.det(m[:3, :3]) < 0:
                tri = tri[:, ::-1]
            slots = [s.material for s in obj.material_slots]
            remap = {}
            for i, mat in enumerate(slots):
                key = mat.name if mat else None
                if key not in [x.name if x else None for x in self.materials]:
                    self.materials.append(mat)
                remap[i] = [x.name if x else None for x in self.materials].index(key)
            if not slots:
                if None not in [x.name if x else None for x in self.materials]:
                    self.materials.append(None)
                remap[0] = [x.name if x else None for x in self.materials].index(None)
            tri_mat = np.array([remap.get(int(poly_mat[p]), remap.get(0, 0)) for p in poly_of_tri], dtype=np.int32)
            base = sum(len(v) for v in self.verts)
            self.verts.append(world.astype(np.float32))
            self.tris.append(tri + base)
            self.mat_index.append(tri_mat)
            self.smooth.append(poly_smooth[poly_of_tri])
            self.count += 1
            if not collision:
                self.no_collision.append((obj.name, len(self.verts) - 1))
        finally:
            evaluated.to_mesh_clear()

    def build(self, name: str, skip: set = frozenset()) -> bpy.types.Object:
        keep = [i for i in range(len(self.verts)) if i not in skip]
        verts = np.concatenate([self.verts[i] for i in keep])
        offsets = {}
        running = 0
        for i in keep:
            offsets[i] = running - sum(len(self.verts[j]) for j in range(i))
            running += len(self.verts[i])
        tris = np.concatenate([self.tris[i] + offsets[i] for i in keep])
        mats = np.concatenate([self.mat_index[i] for i in keep])
        smooth = np.concatenate([self.smooth[i] for i in keep])
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts.tolist(), [], tris.tolist())
        mesh.polygons.foreach_set("material_index", mats)
        mesh.polygons.foreach_set("use_smooth", smooth)
        for mat in self.materials:
            mesh.materials.append(mat)
        mesh.validate(verbose=False)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = self.centre
        obj[EXPORT_TAG] = True
        return obj


def main() -> None:
    started = time.time()
    root = project_root()
    out = output_path(root)
    scene = bpy.context.scene
    twins = [o.name for o in bpy.data.objects if TWIN_SUFFIX.search(o.name)]
    if twins:
        raise SystemExit(
            f"export_world_source: refusing, the master still holds {len(twins)} collision twin(s) "
            f"such as {twins[0]}; collision is derived here, run tools/strip_collision_twins.py first")
    leftover = [o for o in bpy.data.objects if o.get(EXPORT_TAG)]
    for o in leftover:
        bpy.data.objects.remove(o, do_unlink=True)

    previous_selection = [o for o in scene.objects if o.select_get()]
    previous_active = bpy.context.view_layer.objects.active
    depsgraph = bpy.context.evaluated_depsgraph_get()

    visible = [o for o in scene.objects if o.type in EXPORTABLE and not o.hide_render]
    rocks = [o for o in visible if is_rock(o)]
    terrain = [o for o in visible if not is_rock(o)]

    temp_objects = []
    temp_meshes = []
    export_set = []

    for obj in terrain:
        if wants_collision(obj):
            copy = obj.copy()
            copy.name = f"{obj.name}-col"
            copy[EXPORT_TAG] = True
            scene.collection.objects.link(copy)
            temp_objects.append(copy)
            export_set.append(copy)
        else:
            export_set.append(obj)

    batches = {}
    omitted = []
    for obj in rocks:
        size = max(obj.dimensions)
        collision = wants_collision(obj) and size >= COLLISION_MIN_SIZE_M
        if not collision:
            omitted.append((obj.name, round(size, 2)))
        cell = cell_of(obj.matrix_world.translation)
        batches.setdefault(cell, Batch(cell)).add(obj, depsgraph, collision)

    chunk_lines = []
    for cell in sorted(batches):
        batch = batches[cell]
        base = cell_name(cell)
        if batch.no_collision:
            visual = batch.build(base)
            skip = {index for _, index in batch.no_collision}
            body = batch.build(f"{base}-colonly", skip)
            made = [visual, body]
        else:
            visual = batch.build(f"{base}-col")
            made = [visual]
        for o in made:
            scene.collection.objects.link(o)
            temp_objects.append(o)
            temp_meshes.append(o.data)
            export_set.append(o)
        chunk_lines.append(
            f"  {base:<28} rocks {batch.count:5d}  surfaces {len(batch.materials):2d}  "
            f"tris {sum(len(t) for t in batch.tris):7d}  no_collision {len(batch.no_collision)}")

    for o in scene.objects:
        o.select_set(False)
    for o in export_set:
        o.select_set(True)
    bpy.context.view_layer.objects.active = export_set[0] if export_set else None

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

    for o in temp_objects:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in temp_meshes:
        if m.users == 0:
            bpy.data.meshes.remove(m)
    for o in scene.objects:
        o.select_set(o in previous_selection)
    bpy.context.view_layer.objects.active = previous_active

    size_mb = os.path.getsize(out) / 1e6
    print("export_world_source")
    print(f"  master   {bpy.data.filepath}")
    print(f"  output   {out}  ({size_mb:.1f} MB, {time.time() - started:.1f} s)")
    print(f"  objects  {len(terrain)} exported as themselves, {sum(1 for o in terrain if wants_collision(o))} with derived collision")
    print(f"  rocks    {len(rocks)} boulders in {len(batches)} cells of {CELL_M:.0f} m; "
          f"{len(omitted)} drawn without collision (under {COLLISION_MIN_SIZE_M} m or kyt_collision=none)")
    for line in chunk_lines:
        print(line)
    for name, size in omitted[:20]:
        print(f"  no collision: {name} ({size} m)")
    print("  master not saved; nothing in it was changed")


main()
