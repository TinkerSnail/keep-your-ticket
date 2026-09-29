"""The family bolt: the one fixing every Keep Your Ticket prop uses, and the
sizes it sets for what it fastens.

Christina's standard (2026-09-27): "standardize the size and scale of these
bolts since they are driving the scale of other elements".

- **The head:** 35 mm across, 18 mm deep, 12-sided: the bolt her benches
  were built with. One mesh, in `assets/source/kit/family_bolt.blend` (object
  `family_bolt`).
- **Its finish:** bare `fixings` metal, as on the benches; on a painted part
  it takes that part's paint, 15% darker (her words, 2026-09-27: "the bolts on
  these bins should be painted the same color as the bin they are on", then
  "lets make them like 15% darker"): `paint_of(material)`.
- **How far it stands proud** of what it holds: 11 mm where it fixes something
  to the ground, 7 mm everywhere else. The head is set by its centre, so the
  rest of it is buried: 7 mm proud is 11 mm in, 11 mm proud is 7 mm in.
- **What it drives:** a post or strap carrying a line of bolts is at least one
  head wide; a bolted band or trim is 1.6 heads wide; a bolted bar 1.2 heads
  tall; bolts along a run about 4.5 heads apart. Shapes that carry bolts take
  these from `HEAD`, never a typed number, so they stay in scale with it.

The benches made before the standard keep their bolts as she placed them (her
word, 2026-09-27): the plaza bench's stand 11 to 15 mm proud and eight on its
back are 22 mm deep.

Used from a Blender script run on a prop file:

    sys.path.insert(0, "<project>/tools/blender")
    import family_bolt
    family_bolt.place(collection, "bolt_post_0", point, normal)          # 7 mm
    family_bolt.place(collection, "bolt_foot_0", point, normal, ground=True)  # 11 mm
    family_bolt.place(collection, "bolt_trim_0", point, normal, material=family_bolt.paint_of(paint))

`place` finds the real surface along the normal (a bolt on a curved band sits
as proud as one on a flat post), gives each bolt its own copy of the mesh, as
the benches have, and tags it `kyt_family_bolt`.

Run as a script to write the kit file from a prop that already has the bolt:

    Blender --background --factory-startup --python tools/blender/family_bolt.py -- \\
        make-kit assets/source/props/perforated_metal_bench_source.blend seat_bolt_l_front
"""

import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HEAD = 0.035
DEPTH = 0.018
PROUD = 0.007
PROUD_GROUND = 0.011
TAG = "kyt_family_bolt"
DARKER = 0.15

POST = 1.0 * HEAD
BAND = 1.6 * HEAD
BAR = 1.2 * HEAD
SPACING = 4.5 * HEAD

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
KIT = os.path.join(ROOT, "assets", "source", "kit", "family_bolt.blend")
NAME = "family_bolt"

_mesh = None


def mesh():
    """The kit's bolt mesh, appended once per file and checked against the
    standard, so a kit that drifted stops the script rather than a prop."""
    global _mesh
    if _mesh is not None and _mesh.name in bpy.data.meshes:
        return _mesh
    with bpy.data.libraries.load(KIT, link=False) as (src, dst):
        dst.meshes = [NAME]
    _mesh = dst.meshes[0]
    ext = [max(v.co[i] for v in _mesh.vertices) - min(v.co[i] for v in _mesh.vertices) for i in range(3)]
    if abs(ext[0] - HEAD) > 1e-4 or abs(ext[1] - HEAD) > 1e-4 or abs(ext[2] - DEPTH) > 1e-4:
        raise SystemExit(f"family_bolt: the kit's bolt is {ext}, not {HEAD} x {HEAD} x {DEPTH}")
    return _mesh


def _to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def paint_of(material):
    """The bolts' paint on a part painted `material`: the same paint, `DARKER`
    darker as the colour picker shows it (sRGB), as `<material>_bolts`."""
    name = f"{material.name}_bolts"
    m = bpy.data.materials.get(name) or material.copy()
    m.name = name
    base = material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
    rgb = [_to_linear(_to_srgb(c) * (1.0 - DARKER)) for c in base[:3]]
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, base[3])
    m.diffuse_color = (*rgb, base[3])
    return m


def _surface(point, normal, against):
    """Where the surface under `point` actually is, looking back along the
    normal from a little outside it, or `point` itself if nothing is there."""
    if not against:
        return point
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in against:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in me.vertices]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    hit = BVHTree.FromPolygons(verts, polys).ray_cast(point + normal * 0.03, -normal, 0.06)
    return hit[0] if hit[0] is not None else point


def place(collection, name, point, normal, ground=False, against=None, material=None):
    """One family bolt, its axis along `normal`, standing the standard height
    proud of the surface at `point` (found on `against`, the objects it
    fastens, when given), in `fixings` or, on a painted part, `material`."""
    n = Vector(normal).normalized()
    at = _surface(Vector(point), n, against)
    proud = PROUD_GROUND if ground else PROUD
    ob = bpy.data.objects.new(name, mesh().copy())
    ob.data.name = name
    if material is not None:
        ob.data.materials.clear()
        ob.data.materials.append(material)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(n)
    ob.location = at + n * (proud - DEPTH / 2)
    ob[TAG] = True
    ob["kyt_bolt_proud_mm"] = round(proud * 1000)
    collection.objects.link(ob)
    return ob


def make_kit(source, obj_name):
    """Write the kit file from `obj_name` in `source`: the bolt at the origin,
    axis +Z, with the standard on it as custom properties."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(source, link=False) as (src, dst):
        dst.objects = [obj_name]
    loaded = dst.objects[0]
    me = loaded.data.copy()
    bpy.data.objects.remove(loaded, do_unlink=True)
    me.name = NAME
    kit = bpy.data.collections.new("kit")
    bpy.context.scene.collection.children.link(kit)
    ob = bpy.data.objects.new(NAME, me)
    kit.objects.link(ob)
    for k, v in (("kyt_head_mm", 35), ("kyt_depth_mm", 18), ("kyt_proud_mm", 7), ("kyt_proud_ground_mm", 11)):
        ob[k] = v
    me.use_fake_user = True
    os.makedirs(os.path.dirname(KIT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=KIT, compress=True)
    mesh_check = [max(v.co[i] for v in me.vertices) - min(v.co[i] for v in me.vertices) for i in range(3)]
    print(f"family_bolt: wrote {KIT}, bolt {[round(x * 1000, 1) for x in mesh_check]} mm")


if __name__ == "__main__" and "--" in sys.argv:
    argv = sys.argv[sys.argv.index("--") + 1:]
    if argv and argv[0] == "make-kit":
        make_kit(os.path.abspath(argv[1]), argv[2])
