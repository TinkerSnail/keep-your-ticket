"""Bring a prop's Godot courses into its Blender file, and bend a blade along each.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<name>.blend --python tools/blender/add_courses.py -- \
        assets/source/props/reference/<name>_courses.json [--blades] [--dead N]

The JSON comes from `tools/maquette_export.gd --courses`: every Path3D of the
Godot scene, in Godot's axes. Each becomes a Bezier curve object in
`authored/courses`, named `course_<name>`, with the same points and handles, so
the course is exactly the one the game draws today. Courses that shared one
Curve3D in Godot share one curve here: moving a point on `course_mature_0`
moves every frond made from that curve, as it did in the editor.

`--blades` (the palm crown) then adds what Christina shapes and what follows
from it:
- `authored/blades`: one blank blade per kind of frond (spear, young, mature,
  old, stub), lying along +Y from its base at y = 0, width along X, its top
  face +Z. The blank's outline is the envelope today's leaflet tips trace, so
  the starting crown has today's silhouette; the leaflets themselves are the
  texture's job, later.
- `export`: one object per course, named for it, whose `kyt_course_blade`
  geometry-nodes modifier bends that kind's blade along the course (length
  stretched to fit, width kept, the blade's X laid across the frond the way
  the Godot script spread its leaflets). Reshape a blade and every frond of
  its kind follows; reshape a course and its frond follows.
- `heart`: the crown's core, copied from the reference.

`--dead N` adds N brown dead fronds hanging against the trunk: `course_dead_<i>`
curves sharing one copy of `course_old_0`'s curve, turned `DEAD_DROP` further
down and spread evenly round the crown, a `blade_dead` copied from
`blade_old`, and `dead_<i>` in `export`. The game shows none to three of them
per tree. It works on a file that already has its courses.

Every frond and the heart are marked `kyt_collision = none` (a crown never
collides) and the scene `kyt_keep_parts`, so Send to game keeps each part a
node of its own and the game can choose fronds tree by tree, and
`kyt_godot_scene` names its Godot scene (`scenes/world/<file>.tscn`), so Send
doesn't offer to write the bench pattern.

Nothing she owns is replaced: curves are imported only into a file that has
none, and a blade or frond that exists is left alone. It reports how far each
curve lies from the baked points Godot draws, and saves. For files an agent has
prepared, never one Christina has open.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

GROUP = "kyt_course_blade"
# Godot is Y-up, Blender Z-up; glTF import makes the same turn, so the courses
# land on the reference: (x, y, z) in Godot is (x, -z, y) here.
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))

# Per kind: the Godot script's half span and droop (coastal_palm_crown.gd,
# retired 2026-09-25; in git at 58c9ca8), the stations along the blade, and
# the material it wore.
KINDS = {
    "spear": {"half": 0.14, "droop": 0.0, "stations": 18, "material": "frond_new"},
    "young": {"half": 0.28, "droop": 0.45, "stations": 18, "material": "frond_new"},
    "mature": {"half": 0.84, "droop": 1.0, "stations": 18, "material": "frond_mature"},
    "old": {"half": 0.70, "droop": 1.0, "stations": 18, "material": "frond_old"},
    "stub": {"half": 0.13, "droop": 0.0, "stations": 7, "material": "frond_stub"},
    "dead": {"half": 0.70, "droop": 1.0, "stations": 18, "material": "frond_dead"},
}
DEAD_DROP = math.radians(45)
# Godot albedo (sRGB) of each material in coastal_palm_crown.tscn (retired;
# in git at 58c9ca8).
MATERIALS = {
    "frond_new": (0.43, 0.64, 0.25),
    "frond_mature": (0.16, 0.39, 0.18),
    "frond_old": (0.27, 0.33, 0.12),
    "frond_stub": (0.31, 0.22, 0.11),
    "crown_heart": (0.32, 0.43, 0.16),
    "frond_dead": (0.47, 0.36, 0.21),
}
MIDRIB_HALF_WIDTH = 0.028


def g2b(v):
    return (C @ Vector((v[0], v[1], v[2], 1.0))).xyz


def kind_of(course):
    if course["group"] == "remnant_courses":
        return "stub"
    if course["name"] == "new_0":
        return "spear"
    age = course["meta"].get("age", "mature")
    return {"new": "young", "old": "old"}.get(age, "mature")


def child_collection(parent_name, name):
    parent = bpy.data.collections[parent_name]
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        parent.children.link(coll)
    return coll


def material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        srgb = MATERIALS[name]
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
        mat.diffuse_color = (*lin, 1.0)
        mat.use_backface_culling = False  # a frond is one sheet, seen from both sides
        bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.95
    return mat


def add_curves(data, courses_coll):
    shared = {}
    made = []
    for course in data["courses"]:
        cid = course["curve"]
        cu = shared.get(cid)
        if cu is None:
            cu = bpy.data.curves.new(cid, "CURVE")
            cu.dimensions = "3D"
            spline = cu.splines.new("BEZIER")
            pts = course["points"]
            spline.bezier_points.add(len(pts) - 1)
            for bp, p in zip(spline.bezier_points, pts):
                pos = Vector(p["position"])
                bp.co = pos.x, -pos.z, pos.y
                straight = not any(p["in"]) and not any(p["out"])
                if straight:
                    bp.handle_left_type = bp.handle_right_type = "VECTOR"
                else:
                    bp.handle_left_type = bp.handle_right_type = "FREE"
                    hl, hr = pos + Vector(p["in"]), pos + Vector(p["out"])
                    bp.handle_left = hl.x, -hl.z, hl.y
                    bp.handle_right = hr.x, -hr.z, hr.y
                bp.tilt = p["tilt"]
            shared[cid] = cu
        obj = bpy.data.objects.new(f"course_{course['name']}", cu)
        bx, by, bz, origin = (Vector(v) for v in course["transform"])
        t = Matrix((
            (bx.x, by.x, bz.x, origin.x),
            (bx.y, by.y, bz.y, origin.y),
            (bx.z, by.z, bz.z, origin.z),
            (0, 0, 0, 1)))
        obj.matrix_world = C @ t @ C.inverted()
        obj["kyt_course"] = course["name"]
        obj["kyt_kind"] = kind_of(course)
        for key, value in course["meta"].items():
            obj[f"kyt_{key}"] = value
        courses_coll.objects.link(obj)
        made.append((obj, course))
    return made


def curve_error(obj, course, depsgraph):
    """Largest distance, in metres, from Godot's baked points to this curve."""
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    try:
        m = obj.matrix_world
        pts = [m @ v.co for v in mesh.vertices]
    finally:
        ev.to_mesh_clear()
    worst = 0.0
    for b in course["baked"]:
        p = g2b(b)
        best = min((p - pts[0]).length, (p - pts[-1]).length)
        for a, c in zip(pts, pts[1:]):
            ab = c - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
            best = min(best, (p - (a + ab * t)).length)
        worst = max(worst, best)
    return worst


def blank_blade(kind, length):
    k = KINDS[kind]
    verts, faces, uvs = [], [], []
    n = k["stations"]
    for i in range(n):
        t = i / (n - 1)
        if kind == "stub":
            w = k["half"] + (0.035 - k["half"]) * t
        elif kind == "spear":
            w = k["half"] * max(0.12, math.sin(math.pi * t))
        else:
            w = max(MIDRIB_HALF_WIDTH, k["half"] * math.sin(math.pi * t))
        droop = -(0.07 + 0.075 * t) * k["droop"] * (w / k["half"])
        y = length * t
        verts += [(-w, y, droop), (0.0, y, 0.0), (w, y, droop)]
        if i:
            a = 3 * (i - 1)
            faces += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
    me = bpy.data.meshes.new(f"blade_{kind}")
    me.from_pydata(verts, [], faces)
    # True-scale planar UVs, U across and V along: the unwrap stage lays these
    # out properly; this only keeps the texture running along the blade.
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = verts[me.loops[li].vertex_index]
            uv.data[li].uv = (0.5 + co[0] / length, co[1] / length)
    me.materials.append(material(k["material"]))
    return me


def link(ng, a, out, b, inp):
    ng.links.new(a.outputs[out], b.inputs[inp])


def course_blade_group():
    """Bend the Blade object's own mesh along the Course: its Y runs base to tip
    (stretched to the course's length), its X across the frond, its Z off the
    frond's face. Across is horizontal and square to the line from the crown's
    centre to the course's tip, as `_frond_side` has it in Godot."""
    ng = bpy.data.node_groups.get(GROUP)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(GROUP, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Course", in_out="INPUT", socket_type="NodeSocketObject")
    ng.interface.new_socket("Blade", in_out="INPUT", socket_type="NodeSocketObject")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes.new
    gin, gout = N("NodeGroupInput"), N("NodeGroupOutput")
    course, blade = N("GeometryNodeObjectInfo"), N("GeometryNodeObjectInfo")
    course.transform_space, blade.transform_space = "RELATIVE", "ORIGINAL"
    link(ng, gin, "Course", course, "Object")
    link(ng, gin, "Blade", blade, "Object")

    pos = N("GeometryNodeInputPosition")
    xyz = N("ShaderNodeSeparateXYZ")
    link(ng, pos, "Position", xyz, "Vector")
    length = N("GeometryNodeAttributeStatistic")
    link(ng, blade, "Geometry", length, "Geometry")
    link(ng, xyz, "Y", length, "Attribute")
    factor = N("ShaderNodeMath")
    factor.operation, factor.use_clamp = "DIVIDE", True
    link(ng, xyz, "Y", factor, 0)
    link(ng, length, "Max", factor, 1)

    along = N("GeometryNodeSampleCurve")
    along.mode = "FACTOR"
    link(ng, course, "Geometry", along, "Curves")
    link(ng, factor, "Value", along, "Factor")
    tip = N("GeometryNodeSampleCurve")
    tip.mode = "FACTOR"
    tip.inputs["Factor"].default_value = 1.0
    link(ng, course, "Geometry", tip, "Curves")

    # Across, before squaring to the tangent: (tip.y, -tip.x, 0), normalised.
    tip_xyz = N("ShaderNodeSeparateXYZ")
    link(ng, tip, "Position", tip_xyz, "Vector")
    neg_x = N("ShaderNodeMath")
    neg_x.operation = "MULTIPLY"
    link(ng, tip_xyz, "X", neg_x, 0)
    neg_x.inputs[1].default_value = -1.0
    side0 = N("ShaderNodeCombineXYZ")
    link(ng, tip_xyz, "Y", side0, "X")
    link(ng, neg_x, "Value", side0, "Y")

    def vmath(op, a, a_out, b=None, b_out=None):
        node = N("ShaderNodeVectorMath")
        node.operation = op
        link(ng, a, a_out, node, 0)
        if b is not None:
            link(ng, b, b_out, node, 1)
        return node

    face = vmath("NORMALIZE", vmath("CROSS_PRODUCT", side0, "Vector", along, "Tangent"), "Vector")
    side = vmath("NORMALIZE", vmath("CROSS_PRODUCT", along, "Tangent", face, "Vector"), "Vector")
    across = N("ShaderNodeVectorMath")
    across.operation = "SCALE"
    link(ng, side, "Vector", across, 0)
    link(ng, xyz, "X", across, "Scale")
    lift = N("ShaderNodeVectorMath")
    lift.operation = "SCALE"
    link(ng, face, "Vector", lift, 0)
    link(ng, xyz, "Z", lift, "Scale")
    moved = vmath("ADD", vmath("ADD", along, "Position", across, "Vector"), "Vector", lift, "Vector")

    setpos = N("GeometryNodeSetPosition")
    link(ng, blade, "Geometry", setpos, "Geometry")
    link(ng, moved, "Vector", setpos, "Position")
    link(ng, setpos, "Geometry", gout, "Geometry")
    for i, node in enumerate(ng.nodes):
        node.location = (i % 6 * 220, -(i // 6) * 260)
    return ng


def socket_id(ng, name):
    return next(s.identifier for s in ng.interface.items_tree
                if getattr(s, "in_out", "") == "INPUT" and s.name == name)


def add_frond(name, course_obj, blade, kind):
    """`name` in export, bending `blade` along `course_obj`; 1 if added, 0 if it
    was already there."""
    if bpy.data.objects.get(name) is not None:
        return 0
    ng = course_blade_group()
    me = bpy.data.meshes.new(name)
    me.materials.append(blade.data.materials[0])
    frond = bpy.data.objects.new(name, me)
    bpy.data.collections["export"].objects.link(frond)
    mod = frond.modifiers.new(GROUP, "NODES")
    mod.node_group = ng
    mod[socket_id(ng, "Course")] = course_obj
    mod[socket_id(ng, "Blade")] = blade
    frond["kyt_course_blade"] = kind
    return 1


def add_dead(count):
    """`count` dead fronds hanging from the crown: one shared copy of old_0's
    curve, each turned DEAD_DROP down about its own heading and spread evenly
    round the crown from old_0's heading."""
    source = bpy.data.objects.get("course_old_0")
    old_blade = bpy.data.objects.get("blade_old")
    if source is None or old_blade is None:
        raise SystemExit("add_courses: --dead needs course_old_0 and blade_old (run --blades first)")
    blade = bpy.data.objects.get("blade_dead")
    if blade is None:
        me = old_blade.data.copy()
        me.name = "blade_dead"
        me.materials.clear()
        me.materials.append(material("frond_dead"))
        blade = bpy.data.objects.new("blade_dead", me)
        child_collection("authored", "blades").objects.link(blade)
        last = max((o for o in bpy.data.collections["blades"].objects if o is not blade),
                   key=lambda o: o.location.x)
        blade.location = (last.location.x + 2 * KINDS["old"]["half"] + 1.0, 0.0, 0.0)
        print("add_courses: blade_dead, a copy of blade_old in brown")
    data = None
    tip = source.matrix_world @ source.data.splines[0].bezier_points[-1].co
    heading = Vector((tip.x, tip.y, 0.0)).normalized()
    courses_coll = child_collection("authored", "courses")
    added = 0
    for i in range(count):
        name = f"dead_{i}"
        course = bpy.data.objects.get(f"course_{name}")
        if course is None:
            if data is None:
                data = next((o.data for o in courses_coll.objects if o.name.startswith("course_dead_")), None)
                if data is None:
                    data = source.data.copy()
                    data.name = "Curve3D_dead"
            turn = Matrix.Rotation(2 * math.pi * i / count, 4, "Z")
            # Down about the horizontal axis square to the frond's heading:
            # turning by +angle about heading x Z lifts it, so drop is negative.
            drop = Matrix.Rotation(-DEAD_DROP, 4, heading.cross(Vector((0, 0, 1))))
            course = bpy.data.objects.new(f"course_{name}", data)
            course.matrix_world = turn @ drop @ source.matrix_world
            course["kyt_course"] = name
            course["kyt_kind"] = "dead"
            courses_coll.objects.link(course)
        added += add_frond(name, course, blade, "dead")
    print(f"add_courses: {added} dead fronds in export, hanging {math.degrees(DEAD_DROP):.0f}° below old_0's line")


def mark_crown():
    """A crown never collides, and the game picks its fronds one by one."""
    for obj in bpy.data.collections["export"].all_objects:
        if obj.type == "MESH":
            obj["kyt_collision"] = "none"
    bpy.context.scene["kyt_keep_parts"] = True
    stem = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    bpy.context.scene["kyt_godot_scene"] = f"res://scenes/world/{stem}.tscn"


def add_blades(made):
    blades_coll = child_collection("authored", "blades")
    export = bpy.data.collections["export"]
    lengths = {}
    for obj, course in made:
        if course["group"] in ("frond_courses", "remnant_courses"):
            pts = [g2b(b) for b in course["baked"]]
            lengths.setdefault(kind_of(course), []).append(
                sum((b - a).length for a, b in zip(pts, pts[1:])))
    blades, x = {}, 7.0
    for kind in KINDS:
        if kind not in lengths:
            continue
        obj = bpy.data.objects.get(f"blade_{kind}")
        if obj is None:
            length = sum(lengths[kind]) / len(lengths[kind])
            obj = bpy.data.objects.new(f"blade_{kind}", blank_blade(kind, length))
            blades_coll.objects.link(obj)
            print(f"add_courses: blade_{kind}, {length:.2f} m (the mean of {len(lengths[kind])} courses)")
        obj.location = (x, 0.0, 0.0)
        x += 2 * KINDS[kind]["half"] + 1.0
        blades[kind] = obj

    added = sum(add_frond(course["name"], obj, blades[kind_of(course)], kind_of(course))
                for obj, course in made)
    print(f"add_courses: {added} fronds in export, each bending its blade along its course")

    if bpy.data.objects.get("heart") is None:
        source = next((o for o in bpy.data.objects
                       if o.type == "MESH" and o.name.startswith("greybox_crown_heart")), None)
        if source is not None:
            me = source.data.copy()
            me.name = "heart"
            me.materials.clear()
            me.materials.append(material("crown_heart"))
            heart = bpy.data.objects.new("heart", me)
            heart.matrix_world = source.matrix_world
            export.objects.link(heart)
            print("add_courses: heart copied from the reference")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    paths = [a for i, a in enumerate(argv)
             if not a.startswith("--") and (i == 0 or argv[i - 1] != "--dead")]
    if len(paths) != 1:
        raise SystemExit("add_courses: give the courses JSON path after --")
    with open(os.path.abspath(paths[0]), encoding="utf-8") as f:
        data = json.load(f)
    if data.get("axes") != "godot":
        raise SystemExit("add_courses: expected a maquette_export --courses file (axes: godot)")
    if "authored" not in bpy.data.collections:
        raise SystemExit("add_courses: this file has no 'authored' collection; start it with new_prop.py")

    courses_coll = child_collection("authored", "courses")
    dead = int(argv[argv.index("--dead") + 1]) if "--dead" in argv else 0
    if len(courses_coll.objects):
        if not dead:
            raise SystemExit("add_courses: this file already has courses; not replacing them")
        print("add_courses: courses already here; kept as they are")
    else:
        made = add_curves(data, courses_coll)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        worst = max((curve_error(o, c, depsgraph), o.name) for o, c in made)
        print(f"add_courses: {len(made)} courses in authored/courses, "
              f"{len({c['curve'] for _, c in made})} curves shared among them; "
              f"farthest from Godot's baked points: {worst[0] * 1000:.2f} mm ({worst[1]})")
        if "--blades" in argv:
            add_blades(made)
    if dead:
        add_dead(dead)
    if "--blades" in argv or dead:
        mark_crown()
    bpy.ops.wm.save_mainfile()
    print("add_courses: saved")


main()
