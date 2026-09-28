"""Give a prop file its own editable parts, copied exactly from the maquette.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<name>.blend --python tools/blender/parts_from_maquette.py -- <name>

For an assembly the generator built out of many shapes (the plaza fountain,
2026-09-27: 208 CSG boxes and drums), the lossless first step of moving it to
Blender: the maquette's own shapes, put in `export` as parts she can select,
move and reshape, so the game shows exactly what it showed before and every
change after is hers. Reads what `add_reference.py` put in `reference` (the
maquette parts, `greybox_<part>`) and `assets/source/props/reference/<name>_parts.json`
(each part's material, collision and shadow, written by the prop's migration
probe, `tools/_fountain_migration_probe.gd materials` for the fountain).

- **One object per ring.** Parts whose names differ only in a two-digit index
  (`kerb_00` … `kerb_35`, `jet_00_a` … `jet_11_a`) are one ring of repeated
  shapes, and become one object (`kerb`, `jet_a`); every other part is its own
  object under its own name. A ring's parts must agree on material, collision
  and shadow, or this stops.
- **Every vertex where it was,** in the maquette's world frame (the fountain
  stands at the park's origin). Each shape's split corners are welded, so a box
  is one closed box to edit, and faces lying in one plane become one face
  (a drum's cap, a box's side). An edge is marked sharp exactly where the
  maquette's normals split, and everything else is smooth, so a drum's side
  shades round and a box shades flat, as in the game. Custom normals are not
  kept: they would go stale the first time she moves a vertex.
- **UVs** come across where a face was one face already, but not as a promise:
  Godot's CSG gives a drum's caps a mapping that changes from one triangle to
  the next, and a cap joined into one face keeps one triangle's. Nothing in the
  fountain reads UVs (its stone is plain colour and its water is mapped in
  world space), so a part is unwrapped when it is first textured.
- **Origins** at the centre of each object's bounds, so scaling a drum scales
  it about itself.
- **Materials** by the generator's names, coloured for Blender's viewport. The
  game does not use these: the GLB's import settings map each name to the
  material of that name in `assets/materials/<name>/`.
- **Collision and shadow** as custom properties: `kyt_collision = "none"` on a
  part that never collided, `kyt_shadow = "off"` on one that cast no shadow
  (the water, and anything under half a metre). Duplicating an object copies
  them.
- The scene gets `kyt_keep_parts`, so Send writes every object as its own node
  (water must be its own node to cast no shadow), and `kyt_godot_scene`.

Refuses a file whose `export` already holds a mesh: it never replaces her
parts. Saves the file, so it is for a file an agent has prepared, never one
Christina has open.
"""

import json
import math
import os
import re
import sys

import bmesh
import bpy
from mathutils import Vector

RING = re.compile(r"_\d\d(?=_|$)")
REFERENCE_TAG = "kyt_reference_import"
NORMAL_SPLIT = 1e-3  # corner normals further apart than this are a sharp edge


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name, look):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    rgb = [srgb_to_linear(c) for c in look["srgb"]]
    alpha = look["alpha"]
    mat.diffuse_color = (*rgb, alpha)
    mat.metallic = look["metallic"]
    mat.roughness = look["roughness"]
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Metallic"].default_value = look["metallic"]
        bsdf.inputs["Roughness"].default_value = look["roughness"]
        bsdf.inputs["Alpha"].default_value = alpha
    if alpha < 1.0:
        mat.surface_render_method = "BLENDED"
    return mat


def add_part(bm, src):
    """Append `src` to `bm` in world space, its corners welded, carrying each
    corner's maquette normal in the loop layer `kyt_n`."""
    part = bmesh.new()
    part.from_mesh(src.data)
    layer = part.loops.layers.float_vector.new("kyt_n")
    corner = src.data.corner_normals
    turn = src.matrix_world.to_3x3().inverted().transposed()
    for face in part.faces:
        start = src.data.polygons[face.index].loop_start
        for k, loop in enumerate(face.loops):
            loop[layer] = (turn @ corner[start + k].vector).normalized()
    part.transform(src.matrix_world)
    bmesh.ops.remove_doubles(part, verts=part.verts[:], dist=1e-6)
    tmp = bpy.data.meshes.new("kyt_tmp")
    part.to_mesh(tmp)
    part.free()
    bm.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)


def shade(bm):
    """Sharp exactly where the maquette's normals split, then planar faces joined."""
    layer = bm.loops.layers.float_vector.get("kyt_n")
    for edge in bm.edges:
        faces = edge.link_faces
        if len(faces) != 2:
            continue
        smooth = True
        for v in edge.verts:
            a = next(l for l in faces[0].loops if l.vert is v)
            b = next(l for l in faces[1].loops if l.vert is v)
            if (Vector(a[layer]) - Vector(b[layer])).length > NORMAL_SPLIT:
                smooth = False
        edge.smooth = smooth
    # Vertices too: a drum's cap arrives as a fan round a centre vertex, and a
    # cap is one face to edit. Only vertices inside a flat region, or on a
    # straight edge, go, so the surface is the same surface. Not delimited by
    # UV: the maquette's cap UVs change from one triangle of the fan to the
    # next, and a joined face keeps one of them (see the module note).
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), use_dissolve_boundaries=False,
                             verts=bm.verts[:], edges=bm.edges[:], delimit={"SHARP"})
    for face in bm.faces:
        face.smooth = True
    bm.loops.layers.float_vector.remove(layer)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        raise SystemExit("parts_from_maquette: give the prop's name after --")
    name = argv[0]
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    table_path = os.path.join(root, "assets", "source", "props", "reference", f"{name}_parts.json")
    table = json.load(open(table_path))

    export = bpy.data.collections.get("export")
    if export is None:
        raise SystemExit("parts_from_maquette: no 'export' collection; start the file with new_prop.py")
    if any(o.type == "MESH" for o in export.all_objects):
        raise SystemExit("parts_from_maquette: 'export' already holds parts; not replacing them")
    maquette = {o.name[len("greybox_"):]: o for o in bpy.data.objects
                if o.get(REFERENCE_TAG) and o.type == "MESH" and o.name.startswith("greybox_")}

    rings = {}
    for row in table["parts"]:
        if row["name"] not in maquette:
            raise SystemExit(f"parts_from_maquette: '{row['name']}' is not in the reference; run add_reference.py")
        rings.setdefault(RING.sub("", row["name"]), []).append(row)
    materials = {n: material(n, look) for n, look in table["materials"].items()}

    for ring, rows in rings.items():
        for key in ("material", "collide", "cast_shadow"):
            if len({r[key] for r in rows}) != 1:
                raise SystemExit(f"parts_from_maquette: the parts of '{ring}' disagree on {key}")
        bm = bmesh.new()
        for row in rows:
            add_part(bm, maquette[row["name"]])
        shade(bm)
        low = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
        high = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
        centre = (low + high) / 2
        bmesh.ops.translate(bm, vec=-centre, verts=bm.verts[:])
        mesh = bpy.data.meshes.new(ring)
        bm.to_mesh(mesh)
        bm.free()
        for attr in [a.name for a in mesh.attributes if a.name == "custom_normal"]:
            mesh.attributes.remove(mesh.attributes[attr])
        mesh.materials.append(materials[rows[0]["material"]])
        obj = bpy.data.objects.new(ring, mesh)
        obj.location = centre
        if not rows[0]["collide"]:
            obj["kyt_collision"] = "none"
        if not rows[0]["cast_shadow"]:
            obj["kyt_shadow"] = "off"
        export.objects.link(obj)
        print(f"parts_from_maquette: {ring}: {len(rows)} part{'s' if len(rows) > 1 else ''}, "
              f"{len(mesh.polygons)} faces, {rows[0]['material']}"
              f"{'' if rows[0]['collide'] else ', no collision'}"
              f"{'' if rows[0]['cast_shadow'] else ', no shadow'}")

    scene = bpy.context.scene
    scene["kyt_keep_parts"] = True
    scene["kyt_godot_scene"] = f"res://scenes/world/{name}.tscn"
    view_layer = bpy.context.view_layer
    for o in maquette.values():
        if view_layer.objects.get(o.name) is o:
            o.hide_set(True, view_layer=view_layer)
    bpy.ops.wm.save_mainfile()
    print(f"parts_from_maquette: {len(rings)} objects from {len(table['parts'])} maquette parts into 'export'")


main()
