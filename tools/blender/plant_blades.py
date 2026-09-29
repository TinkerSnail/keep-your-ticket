"""Give a plant drawn along Godot courses its blades, and bend one along each.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<plant>.blend --python tools/blender/plant_blades.py -- <plant>

Run after `add_courses.py` (without `--blades`, which is the palm crown's) has
brought the plant's Godot courses in exactly. For a plant in `PLANTS` (the fern
fan and the Hakone grass) it makes what Christina shapes and what follows from
it, the palm crown's arrangement:

- `authored/blades`: one blade per kind of leaf, lying flat along +Y from its
  base at y = 0, across along X, its top face +Z. Each is built with the
  formulas the plant's Godot script used, laid into that flat frame, so the
  first bend reproduces today's plant; reshape a blade and every leaf of its
  kind follows.
- `export`: one object per leaf, named as the Godot script named it, whose
  `kyt_course_blade` modifier bends its kind's blade along its course (length
  stretched to fit). Its inputs carry what the script varied leaf by leaf:
  Width (the course's own span against the blade's), and for the grass's three
  blades to a course, Offset, Sway and Reach. Reshape a course and its leaves
  follow. A second modifier sets the normals as Godot had them (below).
- `plant_base` in `reference`: an empty at the origin, the soil line. Check
  reads it as "placed here", since the leaves may start a little above it.
- the materials the Godot scene wore (same colours, double-sided), and
  `kyt_collision = none` on every part: planting never collided. The scene's
  `kyt_godot_scene` names the Godot scene that already places the plant, so
  Send doesn't offer to write the bench pattern. Leaves only some placements
  show carry `kyt_merge_group`, and go to the game as their own mesh.

Then it measures every leaf against the Godot one in `reference`
(`greybox_<leaf>`), both ways, nearest surface to each vertex, and saves.
Nothing that exists is replaced. For files an agent has prepared, never one
Christina has open.
"""

import math
import os
import statistics
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_courses  # noqa: E402  (the course-bending group; its main() is guarded)
from add_courses import link  # noqa: E402


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name, srgb, roughness, double_sided=True):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        lin = (*(srgb_to_linear(c) for c in srgb), 1.0)
        mat.diffuse_color = lin
        mat.roughness = roughness
        # A leaf is one sheet, seen from both sides; a stem or a petal is closed.
        mat.use_backface_culling = not double_sided
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = lin
            bsdf.inputs["Roughness"].default_value = roughness
    return mat


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def mesh_from(name, verts, faces, mats, uvs, materials):
    """A mesh with one UV per face corner (`uvs`, parallel to the corners of
    `faces`) and each face's material slot."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for poly, face_uvs in zip(me.polygons, uvs):
        for li, co in zip(poly.loop_indices, face_uvs):
            uv.data[li].uv = co
    for m in materials:
        me.materials.append(m)
    for poly, m in zip(me.polygons, mats):
        poly.material_index = m
    return me


def course_length(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    try:
        pts = [obj.matrix_world @ v.co for v in mesh.vertices]
    finally:
        ev.to_mesh_clear()
    return sum((b - a).length for a, b in zip(pts, pts[1:]))


def course_scale(obj):
    return obj.matrix_world.to_scale().x


def make_blade(name, build):
    """The blade `name` in authored/blades, built by `build()` if missing."""
    blade = bpy.data.objects.get(name)
    if blade is None:
        blade = bpy.data.objects.new(name, build())
        add_courses.child_collection("authored", "blades").objects.link(blade)
    return blade


def lay_out_blades(blades):
    """Side by side along +X, clear of the plant."""
    x = 1.0
    for blade in blades:
        blade.location = (x, 0.0, 0.0)
        x += blade.dimensions.x + 0.3


# Godot's front face is clockwise, Blender's and glTF's counter-clockwise, so
# every triangle and quad the scripts emitted goes in reversed: the same side
# stays its front, which the normals modifiers need to light it as Godot did.


# --- The fern fan (PRP-PLANT-011) -------------------------------------------
#
# `coastal_palm_fern_fill.gd` (retired to Blender 2026-09-27; git holds it)
# built each frond in its course's own frame: pinnae at fractions of the
# course's length, reaching `half_span` across, canted forward along the
# rachis and drooping, and a 14 mm rachis ribbon. Its across was horizontal and
# square to the line from the fan's centre to the frond's tip, which is the
# group's X; its tangent is our Y and its `side x tangent` our +Z. Its normals
# were each triangle's own, turned to face the sky: `kyt_normals_up`.

FERN_PAIRS = 11  # the scene's `pinnae_pairs`, which no placement overrode
FERN_RACHIS_HALF_WIDTH = 0.007
FERN_MATERIALS = {
    "fern_leaf": ((0.105, 0.305, 0.105), 0.98),
    "fern_young": ((0.245, 0.445, 0.14), 0.96),
    "fern_rachis": ((0.135, 0.255, 0.075), 0.99),
}


def fern_blade(name, length, half_span, scale, leaf, rachis):
    """A flat fern frond `length` long reaching `half_span` across; `scale` is
    the Godot course's own, which every fixed offset in the script grew by."""
    verts, faces, mats, uvs = [], [], [], []

    def uv(v):
        return (0.5 + v.x / length, v.y / length)

    def tri(a, b, c, m):
        base = len(verts)
        verts.extend((a, b, c))
        faces.append((base, base + 2, base + 1))
        mats.append(m)
        uvs.append((uv(a), uv(c), uv(b)))

    for index in range(FERN_PAIRS):
        for sign in (-1.0, 1.0):
            t = min(0.96, max(0.05, (index + 0.9) / (FERN_PAIRS + 0.9) + sign * 0.009))
            y = length * t
            envelope = math.sin(math.pi * t) ** 0.68 * (1.0 - 0.26 * t)
            rhythm = 0.94 if (index + (0 if sign < 0 else 1)) % 3 == 0 else 1.0
            span = half_span * envelope * rhythm
            root = Vector((0.0, y, 0.0))
            tip = Vector((sign * span, y + (0.018 + 0.014 * t) * scale,
                          -(0.008 + 0.012 * t) * scale))
            shoulder = root.lerp(tip, 0.42)
            half_width = (0.014 + 0.006 * math.sin(math.pi * t)) \
                * (0.88 if index % 4 == 0 else 1.0) * scale
            flank_a = shoulder + Vector((0.0, half_width, 0.0))
            flank_b = shoulder - Vector((0.0, half_width, 0.0))
            tri(root, flank_a, tip, 0)
            tri(root, tip, flank_b, 0)

    samples = FERN_PAIRS // 2 + 3
    first = len(verts)
    for i in range(samples):
        t = i / (samples - 1)
        w = FERN_RACHIS_HALF_WIDTH * lerp(1.0, 0.28, t) * scale
        verts += [Vector((-w, length * t, 0.0)), Vector((w, length * t, 0.0))]
    for i in range(samples - 1):
        b = first + i * 2
        for face in ((b, b + 1, b + 2), (b + 1, b + 3, b + 2)):
            faces.append(face)
            mats.append(1)
            uvs.append(tuple(uv(verts[k]) for k in face))
    return mesh_from(name, verts, faces, mats, uvs, [leaf, rachis])


def fern_fan(courses, depsgraph):
    mats = {k: material(k, *v) for k, v in FERN_MATERIALS.items()}
    info = []
    for obj in courses:
        scale = course_scale(obj)
        info.append({"course": obj, "young": bool(obj.get("kyt_young", False)),
                     "length": course_length(obj, depsgraph),
                     "span": float(obj.get("kyt_half_span", 0.15)) * scale, "scale": scale})

    blades = {}
    for kind, young in (("mature", False), ("young", True)):
        own = [i for i in info if i["young"] == young]
        if not own:
            continue
        length = statistics.mean(i["length"] for i in own)
        span = statistics.mean(i["span"] for i in own)
        scale = statistics.mean(i["scale"] for i in own)
        blade = make_blade(f"blade_{kind}", lambda: fern_blade(
            f"blade_{kind}", length, span, scale,
            mats["fern_young" if young else "fern_leaf"], mats["fern_rachis"]))
        print(f"plant_blades: blade_{kind}, {length:.3f} m long, {span:.3f} m half span "
              f"(the mean of {len(own)} course{'s' if len(own) != 1 else ''})")
        blades[young] = (blade, span)
    lay_out_blades(b for b, _ in blades.values())
    return [{"name": i["course"]["kyt_course"], "course": i["course"],
             "blade": blades[i["young"]][0],
             "inputs": {"Width": i["span"] / blades[i["young"]][1]}}
            for i in info]


# --- Lemon Zest Hakone grass (PRP-PLANT-018 to 021) ---------------------------
#
# `hakone_grass.gd` (moved to Blender 2026-09-27; git holds the script that
# built the blades) drew three blades along each course, fanned sideways
# (`copy_spread`), bowed (`rhythm`) and each 4% shorter than the last. A blade
# is three strips across, the green edges and the lemon stripe, nine stations
# long, holding its width through the arch and ending in a fine point, with a
# shallow fold down its middle. Its normals were the frame's up at each
# station, not the strips' own: `kyt_frame_normals`. The six young courses show
# only in the vB clump; they go to the game as their own mesh.

HAKONE_SAMPLES = 9
HAKONE_STRIPE = 0.68
HAKONE_MATERIALS = {
    "hakone_edge": ((0.18, 0.4, 0.03), 0.96),
    "hakone_lemon": ((0.6, 0.79, 0.075), 0.93),
    "hakone_young_edge": ((0.34, 0.57, 0.045), 0.94),
    "hakone_young_lemon": ((0.76, 0.9, 0.16), 0.91),
}


def hakone_blade(name, length, half_width, fold, edge, lemon):
    verts, faces, mats, uvs = [], [], [], []
    for u0, u1, m in ((-1.0, -HAKONE_STRIPE, 0), (HAKONE_STRIPE, 1.0, 0),
                      (-HAKONE_STRIPE, HAKONE_STRIPE, 1)):
        base = len(verts)
        for k in range(HAKONE_SAMPLES):
            t = k / (HAKONE_SAMPLES - 1)
            envelope = lerp(0.52, 1.0, smoothstep(0.0, 0.18, t)) * max(0.0, 1.0 - t) ** 0.24
            for u in (u0, u1):
                verts.append(Vector((u * half_width * envelope, length * t,
                                     fold * (1.0 - abs(u)) * math.sin(math.pi * t))))
        for k in range(HAKONE_SAMPLES - 1):
            a, d = base + 2 * k, base + 2 * k + 1
            b, c = a + 2, d + 2
            t0, t1 = k / (HAKONE_SAMPLES - 1), (k + 1) / (HAKONE_SAMPLES - 1)
            s0, s1 = (u0 + 1.0) * 0.5, (u1 + 1.0) * 0.5
            # The script's (a, b, c) and (a, c, d), reversed; its UVs kept.
            faces += [(a, c, b), (a, d, c)]
            uvs += [((s0, t0), (s1, t1), (s0, t1)), ((s0, t0), (s1, t0), (s1, t1))]
            mats += [m, m]
    return mesh_from(name, verts, faces, mats, uvs, [edge, lemon])


def hakone_grass(courses, depsgraph):
    mats = {k: material(k, *v) for k, v in HAKONE_MATERIALS.items()}
    info = []
    for obj in courses:
        scale = course_scale(obj)
        half_width = float(obj.get("kyt_half_width", 0.027)) * 0.78
        info.append({"course": obj, "young": bool(obj.get("kyt_young", False)),
                     "length": course_length(obj, depsgraph), "scale": scale,
                     "half_width": half_width * scale,
                     "fold": float(obj.get("kyt_fold_depth", 0.012)) * scale,
                     "copies": int(obj.get("kyt_blade_copies", 3)),
                     "spread": float(obj.get("kyt_copy_spread", half_width * 0.9)),
                     "rhythm": int(obj.get("kyt_rhythm", 0)),
                     "variant_min": int(obj.get("kyt_variant_min", 0))})

    blades = {}
    for kind, young in (("mature", False), ("young", True)):
        own = [i for i in info if i["young"] == young]
        if not own:
            continue
        length = statistics.mean(i["length"] for i in own)
        half_width = statistics.mean(i["half_width"] for i in own)
        fold = statistics.mean(i["fold"] for i in own)
        prefix = "hakone_young_" if young else "hakone_"
        blade = make_blade(f"blade_{kind}", lambda: hakone_blade(
            f"blade_{kind}", length, half_width, fold,
            mats[prefix + "edge"], mats[prefix + "lemon"]))
        print(f"plant_blades: blade_{kind}, {length:.3f} m long, {half_width * 1000:.1f} mm "
              f"half width (the mean of {len(own)} courses)")
        blades[young] = (blade, half_width)
    lay_out_blades(b for b, _ in blades.values())

    leaves = []
    for i in info:
        blade, half_width = blades[i["young"]]
        for copy in range(i["copies"]):
            share = copy / max(i["copies"] - 1, 1)
            sway = (0.012 if copy % 2 == 0 else -0.014) * (1 + i["rhythm"] % 3)
            leaves.append({
                "name": f"{i['course']['kyt_course']}_blade_{copy}",
                "course": i["course"], "blade": blade,
                "inputs": {"Width": i["half_width"] / half_width,
                           "Offset": lerp(-i["spread"], i["spread"], share) * i["scale"],
                           "Sway": sway * i["scale"],
                           "Reach": 1.0 - 0.04 * copy},
                "merge_group": "young" if i["variant_min"] >= 1 else ""})
    return leaves


# --- Purple Heart sprig (PRP-PLANT-015 to 017) --------------------------------
#
# `purple_heart_sprig.gd` (moved to Blender 2026-09-28; git holds the script
# that built the sprig) drew a four-sided stem along one course, leaf pairs up
# it (from 17% to 82% of the way, each pair turned 1.37 radians from the last,
# rising a little more toward the tip, the top pair young: smaller, paler) and,
# on a flowered sprig, three petals and a centre at the tip. A placement chose
# how many pairs (4 to 7) and whether it flowered, so the sprig goes to the
# game as a stem, one mesh of leaves for each pair count (`pairs_<n>`) and the
# flower, and its Godot scene shows the ones it wants. The leaves are one leaf
# and one young leaf in `authored/blades`, placed along the stem by
# `kyt_leaves_on_course` from each leaf's share of the way up, turn, rise and
# length kept on the points of `leaves_<n>`: reshape the stem course and the
# leaves follow it; reshape a blade and every leaf of its kind follows. A
# leaf's length scales it across and along, never its arch, as in Godot. The
# script's leaf frame is left-handed (across = up x along); a blade is built
# mirrored across and its triangles reversed, so the same side stays its front.

PH_PAIRS = (4, 5, 6, 7)
PH_BLADE_M = 0.24  # the length a blade is drawn at; each leaf scales from it
PH_MATERIALS = {  # name: (sRGB, roughness, double-sided)
    "ph_stem": ((0.28, 0.1, 0.37), 0.93, False),
    "ph_leaf": ((0.22, 0.105, 0.34), 0.91, True),
    "ph_young": ((0.39, 0.17, 0.49), 0.9, True),
    "ph_flower": ((0.9, 0.35, 0.72), 0.88, False),
    "ph_flower_centre": ((1.0, 0.72, 0.9), 0.86, False),
}


def ph_blade(name, half_ratio, mat):
    """The script's leaf, 5 stations along and 3 across, laid in its own frame."""
    ts, us = [k / 4 for k in range(5)], (-1.0, 0.0, 1.0)
    verts = []
    for t in ts:
        envelope = math.sin(math.pi * t) ** 0.62 * (1.0 - 0.12 * t)
        for u in us:
            z = 0.032 * math.sin(math.pi * t) - 0.025 * t * t \
                + 0.012 * (1.0 - abs(u)) * math.sin(math.pi * t)
            verts.append(Vector((-u * PH_BLADE_M * half_ratio * envelope, PH_BLADE_M * t, z)))
    faces, uvs = [], []
    for k in range(4):
        for j in range(2):
            a, b = k * 3 + j, (k + 1) * 3 + j
            c, d = b + 1, a + 1
            for face in ((a, c, b), (a, d, c)):  # the script's (a, b, c), (a, c, d), reversed
                faces.append(face)
                uvs.append(tuple(((us[i % 3] + 1.0) * 0.5, ts[i // 3]) for i in face))
    return mesh_from(name, verts, faces, [0] * len(faces), uvs, [mat])


def _node_group(name, sockets):
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng, None
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for sname, stype, default in sockets:
        s = ng.interface.new_socket(sname, in_out="INPUT", socket_type=stype)
        if default is not None:
            s.default_value = default
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    return ng, (ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput"))


def _tidy(ng):
    for i, node in enumerate(ng.nodes):
        node.location = (i % 6 * 220, -(i // 6) * 240)


def course_stem_group():
    """A round-ish stem drawn along the Course: resampled to Stations points,
    its radius running from Base radius to Tip radius, Sides flat sides."""
    ng, io = _node_group("kyt_course_stem", (
        ("Course", "NodeSocketObject", None), ("Material", "NodeSocketMaterial", None),
        ("Base radius", "NodeSocketFloat", 0.012), ("Tip radius", "NodeSocketFloat", 0.0065),
        ("Sides", "NodeSocketInt", 4), ("Stations", "NodeSocketInt", 9)))
    if io is None:
        return ng
    gin, gout = io
    N = ng.nodes.new
    info = N("GeometryNodeObjectInfo")
    info.transform_space = "RELATIVE"
    link(ng, gin, "Course", info, "Object")
    resample = N("GeometryNodeResampleCurve")
    link(ng, info, "Geometry", resample, "Curve")
    link(ng, gin, "Stations", resample, "Count")
    param = N("GeometryNodeSplineParameter")
    radius = N("ShaderNodeMapRange")
    link(ng, param, "Factor", radius, "Value")
    link(ng, gin, "Base radius", radius, "To Min")
    link(ng, gin, "Tip radius", radius, "To Max")
    circle = N("GeometryNodeCurvePrimitiveCircle")
    circle.inputs["Radius"].default_value = 1.0
    link(ng, gin, "Sides", circle, "Resolution")
    # Curve to Mesh sizes the profile by its Scale input (Blender 5), not the
    # curve's radius.
    tube = N("GeometryNodeCurveToMesh")
    link(ng, resample, "Curve", tube, "Curve")
    link(ng, circle, "Curve", tube, "Profile Curve")
    link(ng, radius, "Result", tube, "Scale")
    smooth = N("GeometryNodeSetShadeSmooth")
    link(ng, tube, "Mesh", smooth, "Mesh")
    setm = N("GeometryNodeSetMaterial")
    link(ng, smooth, "Mesh", setm, "Geometry")
    link(ng, gin, "Material", setm, "Material")
    link(ng, setm, "Geometry", gout, "Geometry")
    _tidy(ng)
    return ng


def leaves_on_course_group():
    """A Leaf (or, where `kyt_young`, the Young leaf) on every point of this
    object's mesh, at `kyt_along` of the way along the Course, pointing out at
    the turn `kyt_turn` and rise `kyt_lift`, its face turned up, scaled across
    and along to `kyt_length` from the Blade length, never up."""
    ng, io = _node_group("kyt_leaves_on_course", (
        ("Course", "NodeSocketObject", None), ("Leaf", "NodeSocketObject", None),
        ("Young leaf", "NodeSocketObject", None), ("Blade length", "NodeSocketFloat", PH_BLADE_M)))
    if io is None:
        return ng
    gin, gout = io
    N = ng.nodes.new

    def attr(name, kind="FLOAT"):
        a = N("GeometryNodeInputNamedAttribute")
        a.data_type = kind
        a.inputs["Name"].default_value = name
        return a

    def scalar(op, a, a_out, b=None, b_out=None, value=None):
        node = N("ShaderNodeMath")
        node.operation = op
        link(ng, a, a_out, node, 0)
        if b is not None:
            link(ng, b, b_out, node, 1)
        elif value is not None:
            node.inputs[1].default_value = value
        return node

    course = N("GeometryNodeObjectInfo")
    course.transform_space = "RELATIVE"
    link(ng, gin, "Course", course, "Object")
    at = N("GeometryNodeSampleCurve")
    at.mode = "FACTOR"
    link(ng, course, "Geometry", at, "Curves")
    link(ng, attr("kyt_along"), "Attribute", at, "Factor")
    placed = N("GeometryNodeSetPosition")
    link(ng, gin, "Geometry", placed, "Geometry")
    link(ng, at, "Position", placed, "Position")

    turn = attr("kyt_turn")
    out = N("ShaderNodeCombineXYZ")  # Godot's (cos, rise, sin), in Blender's axes
    link(ng, scalar("COSINE", turn, "Attribute"), "Value", out, "X")
    link(ng, scalar("MULTIPLY", scalar("SINE", turn, "Attribute"), "Value", value=-1.0), "Value", out, "Y")
    link(ng, attr("kyt_lift"), "Attribute", out, "Z")
    along = N("FunctionNodeAlignRotationToVector")
    along.axis = "Y"
    link(ng, out, "Vector", along, "Vector")
    up = N("FunctionNodeAlignRotationToVector")
    up.axis, up.pivot_axis = "Z", "Y"
    link(ng, along, "Rotation", up, "Rotation")
    up.inputs["Vector"].default_value = (0.0, 0.0, 1.0)
    s = scalar("DIVIDE", attr("kyt_length"), "Attribute", gin, "Blade length")
    size = N("ShaderNodeCombineXYZ")
    link(ng, s, "Value", size, "X")
    link(ng, s, "Value", size, "Y")
    size.inputs["Z"].default_value = 1.0

    young = attr("kyt_young", "BOOLEAN")
    mature = N("FunctionNodeBooleanMath")
    mature.operation = "NOT"
    link(ng, young, "Attribute", mature, 0)
    join = N("GeometryNodeJoinGeometry")
    for which, sel, sel_out in (("Leaf", mature, "Boolean"), ("Young leaf", young, "Attribute")):
        info = N("GeometryNodeObjectInfo")
        info.transform_space = "ORIGINAL"
        link(ng, gin, which, info, "Object")
        inst = N("GeometryNodeInstanceOnPoints")
        link(ng, placed, "Geometry", inst, "Points")
        link(ng, sel, sel_out, inst, "Selection")
        link(ng, info, "Geometry", inst, "Instance")
        link(ng, up, "Rotation", inst, "Rotation")
        link(ng, size, "Vector", inst, "Scale")
        link(ng, inst, "Instances", join, "Geometry")
    real = N("GeometryNodeRealizeInstances")
    link(ng, join, "Geometry", real, "Geometry")
    link(ng, real, "Geometry", gout, "Geometry")
    _tidy(ng)
    return ng


def at_course_tip_group():
    """This object's own mesh, moved from the origin to the Course's tip."""
    ng, io = _node_group("kyt_at_course_tip", (("Course", "NodeSocketObject", None),))
    if io is None:
        return ng
    gin, gout = io
    N = ng.nodes.new
    course = N("GeometryNodeObjectInfo")
    course.transform_space = "RELATIVE"
    link(ng, gin, "Course", course, "Object")
    tip = N("GeometryNodeSampleCurve")
    tip.mode = "FACTOR"
    tip.inputs["Factor"].default_value = 1.0
    link(ng, course, "Geometry", tip, "Curves")
    move = N("GeometryNodeTransform")
    link(ng, gin, "Geometry", move, "Geometry")
    link(ng, tip, "Position", move, "Translation")
    link(ng, move, "Geometry", gout, "Geometry")
    _tidy(ng)
    return ng


def _set(mod, ng, values):
    for key, value in values.items():
        mod[add_courses.socket_id(ng, key)] = value


def _export(name, mesh, group=""):
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections["export"].objects.link(obj)
    obj["kyt_collision"] = "none"
    if group:
        obj["kyt_merge_group"] = group
    return obj


def purple_heart_sprig(courses, depsgraph):
    mats = {k: material(k, srgb, rough, double) for k, (srgb, rough, double) in PH_MATERIALS.items()}
    course = courses[0]
    leaf = make_blade("blade_leaf", lambda: ph_blade("blade_leaf", 0.27, mats["ph_leaf"]))
    young = make_blade("blade_young", lambda: ph_blade("blade_young", 0.25, mats["ph_young"]))
    lay_out_blades([leaf, young])
    made = []

    if bpy.data.objects.get("stem") is None:
        me = bpy.data.meshes.new("stem")
        me.materials.append(mats["ph_stem"])
        stem = _export("stem", me)
        ng = course_stem_group()
        mod = stem.modifiers.new(ng.name, "NODES")
        mod.node_group = ng
        _set(mod, ng, {"Course": course, "Material": mats["ph_stem"]})
        made.append("stem")

    for n in PH_PAIRS:
        name = f"leaves_{n}"
        if bpy.data.objects.get(name) is not None:
            continue
        rows = []
        for i in range(n):
            share = i / max(n - 1, 1)
            for side in (0, 1):
                length = (0.24 + 0.04 * math.sin(i * 2.1 + side)) * (0.78 if i >= n - 1 else 1.0)
                rows.append((0.17 + (0.82 - 0.17) * share, 0.42 + i * 1.37 + (math.pi if side else 0.0),
                             0.07 + (0.22 - 0.07) * share, length, i >= n - 1))
        me = bpy.data.meshes.new(name)
        me.from_pydata([(0.0, 0.0, 0.0)] * len(rows), [], [])
        for key, col, kind in (("kyt_along", 0, "FLOAT"), ("kyt_turn", 1, "FLOAT"),
                               ("kyt_lift", 2, "FLOAT"), ("kyt_length", 3, "FLOAT"),
                               ("kyt_young", 4, "BOOLEAN")):
            a = me.attributes.new(key, kind, "POINT")
            a.data.foreach_set("value", [r[col] for r in rows])
        me.materials.append(mats["ph_leaf"])
        me.materials.append(mats["ph_young"])
        obj = _export(name, me, f"pairs_{n}")
        obj["kyt_leaf_blades"] = True  # unwrap_blades.py lays out the blades it places
        ng = leaves_on_course_group()
        mod = obj.modifiers.new(ng.name, "NODES")
        mod.node_group = ng
        _set(mod, ng, {"Course": course, "Leaf": leaf, "Young leaf": young})
        up = normals_up_group()
        obj.modifiers.new(up.name, "NODES").node_group = up
        made.append(name)

    if bpy.data.objects.get("flower") is None:
        # The petals and centre as the script placed them, from the reference,
        # moved to the origin; `kyt_at_course_tip` puts them back at the tip.
        ev = course.evaluated_get(depsgraph).to_mesh()
        tip = course.matrix_world @ ev.vertices[-1].co
        course.evaluated_get(depsgraph).to_mesh_clear()
        parts = [o for o in bpy.data.objects
                 if o.name.startswith(("greybox_petal_", "greybox_flower_center"))]
        me = bpy.data.meshes.new("flower")
        me.materials.append(mats["ph_flower"])
        me.materials.append(mats["ph_flower_centre"])
        bm = bmesh.new()
        for part in parts:
            src = part.data.copy()
            src.transform(Matrix.Translation(-tip) @ part.matrix_world)
            first = len(bm.faces)
            bm.from_mesh(src)
            centre = part.name.startswith("greybox_flower_center")
            for f in list(bm.faces)[first:]:
                f.material_index = 1 if centre else 0
            bpy.data.meshes.remove(src)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        flower = _export("flower", me, "flower")
        ng = at_course_tip_group()
        mod = flower.modifiers.new(ng.name, "NODES")
        mod.node_group = ng
        _set(mod, ng, {"Course": course})
        made.append("flower")
    print(f"plant_blades: {', '.join(made) or 'nothing new'} in export")

    def refs(prefix):
        return [o for o in bpy.data.objects if o.name.startswith(prefix)]
    return {"leaves": [], "measure": [
        ("stem", [bpy.data.objects["stem"]], refs("greybox_segment_")),
        ("leaves_6", [bpy.data.objects["leaves_6"]], refs("greybox_leaf_")),
        ("flower", [bpy.data.objects["flower"]], refs("greybox_petal_") + refs("greybox_flower_center"))]}


PLANTS = {
    "fern_fan": {
        "build": fern_fan,
        "godot_scene": "res://scenes/world/coastal_palm_fern_fill.tscn",
        "normals": "up",
    },
    "hakone_grass": {
        "build": hakone_grass,
        "godot_scene": "res://scenes/world/hakone_grass.tscn",
        "normals": "frame",
    },
    "purple_heart_sprig": {
        "build": purple_heart_sprig,
        "godot_scene": "res://scenes/world/purple_heart_sprig.tscn",
    },
}


# --- Normals as Godot had them --------------------------------------------------

def _flip_up(ng, vector_socket):
    """The vector, reversed when it points below the horizon."""
    N = ng.nodes.new
    xyz = N("ShaderNodeSeparateXYZ")
    ng.links.new(vector_socket, xyz.inputs["Vector"])
    below = N("ShaderNodeMath")
    below.operation = "LESS_THAN"
    link(ng, xyz, "Z", below, 0)
    below.inputs[1].default_value = 0.0
    sign = N("ShaderNodeMath")  # 1 - 2 * below: -1 for a vector turned down
    sign.operation = "MULTIPLY_ADD"
    link(ng, below, "Value", sign, 0)
    sign.inputs[1].default_value = -2.0
    sign.inputs[2].default_value = 1.0
    up = N("ShaderNodeVectorMath")
    up.operation = "SCALE"
    ng.links.new(vector_socket, up.inputs[0])
    link(ng, sign, "Value", up, "Scale")
    return up.outputs["Vector"]


def _normals_group(name, domain, source):
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gin, gout = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    setn = ng.nodes.new("GeometryNodeSetMeshNormal")
    setn.mode, setn.domain = "FREE", domain
    link(ng, gin, "Geometry", setn, "Mesh")
    ng.links.new(_flip_up(ng, source(ng)),
                 next(s for s in setn.inputs if s.type == "VECTOR"))
    link(ng, setn, "Mesh", gout, "Geometry")
    for i, node in enumerate(ng.nodes):
        node.location = (i * 200, 0)
    return ng


def normals_up_group():
    """Every face's own normal, turned to face the sky, as the fern script did
    (`if normal.dot(Vector3.UP) < 0.0: normal = -normal`) while leaving half
    its triangles wound the other way. Godot lights the back of a double-sided
    face with its normal reversed, so from above those faces show dark: the
    fern's two-tone fishbone. Removing the modifier lights both sides alike."""
    return _normals_group("kyt_normals_up", "FACE",
                          lambda ng: ng.nodes.new("GeometryNodeInputNormal").outputs["Normal"])


def frame_normals_group():
    """The leaf's own up at each point along its course (`kyt_frame_up`, which
    the bend keeps), turned to face the sky, as the Hakone script shaded its
    blades: the arch shades as one curve and the fold doesn't facet it.
    Removing the modifier shades each strip by its own slope."""
    def source(ng):
        attr = ng.nodes.new("GeometryNodeInputNamedAttribute")
        attr.data_type = "FLOAT_VECTOR"
        attr.inputs["Name"].default_value = "kyt_frame_up"
        return attr.outputs["Attribute"]
    return _normals_group("kyt_frame_normals", "POINT", source)


NORMALS = {"up": normals_up_group, "frame": frame_normals_group}


# --- Shared --------------------------------------------------------------------

def add_leaf(leaf, normals):
    """The leaf in export, bending its blade along its course; 1 if added, 0 if
    it was already there."""
    name = leaf["name"]
    if bpy.data.objects.get(name) is not None:
        return 0
    ng = add_courses.course_blade_group()
    me = bpy.data.meshes.new(name)
    for m in leaf["blade"].data.materials:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    bpy.data.collections["export"].objects.link(obj)
    mod = obj.modifiers.new(add_courses.GROUP, "NODES")
    mod.node_group = ng
    mod[add_courses.socket_id(ng, "Course")] = leaf["course"]
    mod[add_courses.socket_id(ng, "Blade")] = leaf["blade"]
    for key, value in leaf["inputs"].items():
        mod[add_courses.socket_id(ng, key)] = value
    if normals:
        group = NORMALS[normals]()
        obj.modifiers.new(group.name, "NODES").node_group = group
    obj["kyt_course_blade"] = leaf["blade"].name.removeprefix("blade_")
    obj["kyt_collision"] = "none"
    if leaf.get("merge_group"):
        obj["kyt_merge_group"] = leaf["merge_group"]
    return 1


def world_mesh(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    try:
        m = obj.matrix_world
        verts = [m @ v.co for v in mesh.vertices]
        polys = [list(p.vertices) for p in mesh.polygons]
    finally:
        ev.to_mesh_clear()
    return verts, polys


def gap(a, b):
    """Distances from every vertex of `a` to the nearest surface of `b`."""
    tree = BVHTree.FromPolygons(*b)
    return [(v - tree.find_nearest(v)[0]).length for v in a[0]]


def joined(objs, depsgraph):
    verts, polys = [], []
    for obj in objs:
        v, p = world_mesh(obj, depsgraph)
        polys += [[i + len(verts) for i in poly] for poly in p]
        verts += v
    return verts, polys


def measure(pairs, depsgraph):
    """`pairs`: (label, object or objects, Godot reference object or objects)."""
    worst, all_d = (0.0, ""), []
    for name, obj, ref in pairs:
        a = joined(obj if isinstance(obj, list) else [obj], depsgraph)
        b = joined(ref if isinstance(ref, list) else [ref], depsgraph)
        d = gap(a, b) + gap(b, a)
        all_d += d
        worst = max(worst, (max(d), name))
        print(f"plant_blades:   {name}: largest {max(d) * 1000:.1f} mm, "
              f"median {statistics.median(d) * 1000:.2f} mm")
    print(f"plant_blades: against the Godot plant ({len(pairs)} leaves), largest gap "
          f"{worst[0] * 1000:.1f} mm ({worst[1]}), median {statistics.median(all_d) * 1000:.2f} mm")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in PLANTS:
        raise SystemExit(f"plant_blades: give one of {', '.join(PLANTS)} after --")
    plant = PLANTS[argv[0]]
    coll = bpy.data.collections.get("courses")
    if coll is None or not len(coll.objects):
        raise SystemExit("plant_blades: no courses here; run add_courses.py first")
    courses = sorted(coll.objects, key=lambda o: o.name)
    depsgraph = bpy.context.evaluated_depsgraph_get()

    built = plant["build"](courses, depsgraph)
    # A builder returns the leaves to bend along courses, or (the Purple Heart,
    # which makes its own parts) those and what to measure against Godot's.
    leaves = built["leaves"] if isinstance(built, dict) else built
    added = sum(add_leaf(leaf, plant.get("normals")) for leaf in leaves)
    print(f"plant_blades: {added} leaves in export, each bending its blade along its course")

    if bpy.data.objects.get("plant_base") is None:
        base = bpy.data.objects.new("plant_base", None)
        base.empty_display_type = "PLAIN_AXES"
        base.empty_display_size = 0.1
        bpy.data.collections["reference"].objects.link(base)
    bpy.context.scene["kyt_godot_scene"] = plant["godot_scene"]

    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    pairs = [(leaf["name"], bpy.data.objects[leaf["name"]],
              bpy.data.objects.get(f"greybox_{leaf['name']}")) for leaf in leaves]
    if isinstance(built, dict):
        pairs += built["measure"]
    measure([p for p in pairs if p[2]], depsgraph)
    missing = [p[0] for p in pairs if p[2] is None]
    if missing:
        print(f"plant_blades: no Godot leaf to measure against for {', '.join(missing)}")
    bpy.ops.wm.save_mainfile()
    print("plant_blades: saved")


if __name__ == "__main__":
    main()
