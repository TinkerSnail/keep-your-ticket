"""The bird of paradise (Strelitzia reginae), built the way the Hakone grass and
the palm crown are: one course per leaf that she can grab and reshape, and a
blade per kind of leaf bent along it (`kyt_course_blade`), so reshaping a blade
reshapes every leaf of its kind. After her two photos
(`documentation/reference/bird_of_paradise/`, 2026-09-29) in the park's
cartoony planting style: a clump of broad paddle leaves, each on a long stiff
stalk, fanning up and out from a sheathed base, the young ones upright in the
middle; flowers on their own stalks, each head a beak (the spathe, green with a
red-mauve rim) holding a crest of three orange sepals and a blue arrow.

    Blender --background assets/source/props/bird_of_paradise.blend \
        --python tools/blender/bird_of_paradise.py -- [--replace]

Two variants (her "keep both", 2026-09-29), sharing the blades and materials:
a, few and big (15 leaves, 4 flowers), in `export` with its courses in
`authored/courses`; b, fuller like her photo (21 narrower leaves, 7 flowers),
its parts named `..._b` in `export/variant_b` and its courses in
`authored/courses/variant_b`, both hidden in the viewport (click their eyes).
Each has low outer leaves drooping over the soil (`droop`). Every part carries
`kyt_variant`, so Send writes each as `<prop>_<variant>...` and the Godot
wrapper shows one.

Makes, in the file `new_prop.py` started:
- `authored/courses`: `course_leaf_<i>`, `course_young_<i>`, `course_droop_<i>`
  and `course_flower_<i>`, Bezier curves from the base up. A leaf's stalk is the
  first `stalk` share of its course and stays straight; the paddle bends out
  over the rest.
- `authored/blades`: `blade_mature` and `blade_young` (along +Y from y = 0 to
  1, across along X, the face +Z, as the Hakone's): a three-sided stalk, flat
  on top and keeled below, then the paddle, a round base and a soft point, its
  halves folded up off a pale midrib, the young one narrower and folded
  tighter. `blade_flower`: one flower head, the stalk's tip at the origin, its
  beak along +Y, crest up +Z.
- `export`: a leaf per course (`kyt_course_blade`); per flower a `stalk_<i>`
  drawn along its course (`kyt_course_stem`) and a `head_<i>` carrying
  `blade_flower` to the course's tip (`kyt_head_at_course_tip`: its beak
  pointed out from the plant's middle, turned by Turn and raised by Tilt, both
  degrees, and sized by Scale); `sheath`, the clump's base. Every part
  `kyt_collision = none`, as all planting.
- `plant_base` in `reference`, the soil line Check places it by, and the scene's
  `kyt_godot_scene`.

`--replace` clears the courses, blades and export first (the file's own
previous build); without it, a file that already holds courses is left alone.
Saves.
"""

import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_courses  # noqa: E402
import plant_blades  # noqa: E402
from add_courses import link  # noqa: E402
from plant_blades import lerp, material, mesh_from  # noqa: E402

GODOT_SCENE = "res://scenes/world/landscape_kit/bird_of_paradise.tscn"
SEED = 63

# sRGB, roughness, double-sided. Leaves after her photos: a blue-leaning green
# with a pale midrib, the young a step lighter; the flower's beak green with a
# red-mauve rim, the crest orange, the arrow blue.
MATERIALS = {
    "bop_leaf": ((0.19, 0.42, 0.30), 0.6, True),
    "bop_midrib": ((0.62, 0.74, 0.48), 0.6, True),
    "bop_young": ((0.33, 0.57, 0.33), 0.6, True),
    "bop_young_midrib": ((0.72, 0.82, 0.52), 0.6, True),
    "bop_stalk": ((0.34, 0.50, 0.30), 0.7, False),
    "bop_sheath": ((0.42, 0.38, 0.22), 0.9, False),
    "bop_spathe": ((0.36, 0.47, 0.35), 0.6, True),
    "bop_spathe_rim": ((0.66, 0.29, 0.40), 0.6, True),
    "bop_sepal": ((1.0, 0.57, 0.08), 0.5, True),
    "bop_petal": ((0.16, 0.30, 0.86), 0.5, True),
}

# Per blade kind: the stalk's share of the leaf's length, the paddle's
# half-width (m), how far its halves fold up (edge rise per metre out from the
# midrib), the stalk's radius at its foot and where it meets the paddle (m).
KINDS = {
    "mature": dict(stalk=0.46, half=0.15, fold=0.32, stalk_r=(0.022, 0.015),
                   leaf="bop_leaf", rib="bop_midrib"),
    "young": dict(stalk=0.45, half=0.10, fold=0.85, stalk_r=(0.018, 0.013),
                  leaf="bop_young", rib="bop_young_midrib"),
}
MIDRIB = 0.012  # the pale midrib's half-width, m
PADDLE = [0.0, 0.05, 0.15, 0.3, 0.5, 0.68, 0.84, 0.95, 1.0]  # stations along the paddle

# A clump's leaves: (heading deg, lean, length m, width share). Lean runs from
# 0, upright, to 1, far out; past 1 the leaf droops, its paddle arching down
# over the soil (the `droop` leaves: her "add the low drooping outer leaves").
# Flowers: (heading deg, rise deg, height m, turn deg, tilt deg, scale). Each
# variant is jittered from SEED; its `width` narrows every mature leaf. The
# droop leaves are drawn after the flowers, so adding them moved nothing else.
LEANS_A = (0.3, 0.75, 0.45, 0.9, 0.35, 0.65, 0.5, 0.85, 0.3, 0.7, 0.55, 0.95, 0.4)
LEANS_B = (0.25, 0.65, 0.9, 0.4, 0.8, 0.3, 0.95, 0.55, 0.2, 0.75, 0.45, 0.9, 0.35, 0.7, 0.25, 0.85, 0.5, 0.95)
VARIANTS = {
    # Few and big.
    "a": dict(width=1.0,
              mature=[(i * 360.0 / len(LEANS_A), lean, 1.30 + 0.25 * lean, 1.0) for i, lean in enumerate(LEANS_A)],
              young=[(40.0, 0.05, 1.25, 1.0), (220.0, 0.12, 1.35, 1.0)],
              droop=[(18.0 + i * 72.0, 1.45 + 0.1 * (i % 2), 1.08, 1.0) for i in range(5)],
              flowers=[(30.0, 72.0, 1.18, -15.0, 6.0, 0.88), (128.0, 76.0, 1.36, 20.0, 2.0, 0.92),
                       (212.0, 70.0, 1.26, -8.0, 9.0, 0.84), (298.0, 74.0, 1.40, 12.0, 4.0, 0.88)]),
    # Fuller, like her photo: more and narrower leaves, more flowers held out.
    "b": dict(width=0.13 / 0.15,
              mature=[(i * 360.0 / len(LEANS_B), lean, 1.25 + 0.3 * lean, 1.0) for i, lean in enumerate(LEANS_B)],
              young=[(40.0, 0.05, 1.3, 1.0), (160.0, 0.1, 1.4, 1.0), (280.0, 0.08, 1.25, 1.0)],
              droop=[(25.0 + i * 360.0 / 7, 1.4 + 0.1 * (i % 3), 1.05, 1.0) for i in range(7)],
              flowers=[(10.0, 66.0, 1.12, -10.0, 4.0, 0.86), (62.0, 72.0, 1.38, 14.0, 2.0, 0.9),
                       (115.0, 64.0, 1.05, -6.0, 6.0, 0.84), (165.0, 70.0, 1.30, 10.0, 3.0, 0.88),
                       (215.0, 66.0, 1.18, -14.0, 5.0, 0.86), (265.0, 73.0, 1.44, 6.0, 2.0, 0.9),
                       (318.0, 65.0, 1.10, 12.0, 6.0, 0.84)]),
}


def colour(name, srgb, rough, double):
    """The material, made or brought up to MATERIALS (a rebuild keeps the file's
    materials, so a changed colour is set again)."""
    mat = material(name, srgb, rough, double)
    lin = (*(plant_blades.srgb_to_linear(c) for c in srgb), 1.0)
    mat.diffuse_color, mat.roughness, mat.use_backface_culling = lin, rough, not double
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = lin
        bsdf.inputs["Roughness"].default_value = rough
    return mat


def outline(s):
    """The paddle's half-width along it, 0 to 1: a round base, full from about
    a fifth of the way, then easing to a soft point."""
    base = math.sin(math.pi / 2 * min(s / 0.22, 1.0)) ** 0.7
    tip = max(0.0, 1.0 - ((max(s, 0.5) - 0.5) / 0.5) ** 2.2) ** 0.55
    return base * tip


def leaf_blade(name, spec, mats):
    """The stalk, a three-sided prism flat on top, then the folded paddle."""
    verts, faces, fmat, uvs = [], [], [], []
    leaf, rib, stalk_m = 0, 1, 2
    p = spec["stalk"]
    r0, r1 = spec["stalk_r"]
    ring = [(-1.0, 0.35), (1.0, 0.35), (0.0, -1.0)]
    ys = [0.0, p * 0.5, p + 0.04]
    for y in ys:
        r = lerp(r0, r1, y / ys[-1])
        verts += [Vector((a * r, y, b * r)) for a, b in ring]
    for k in range(len(ys) - 1):
        for j in range(3):
            a, b = k * 3 + j, k * 3 + (j + 1) % 3
            faces.append((a, b, b + 3, a + 3))
            u0, u1 = 0.9 + j * 0.03, 0.93 + j * 0.03
            uvs.append(((u0, ys[k]), (u1, ys[k]), (u1, ys[k + 1]), (u0, ys[k + 1])))
            fmat.append(stalk_m)

    hw = spec["half"]
    rows = []
    for s in PADDLE:
        y = p + s * (1.0 - p)
        w = hw * outline(s)
        if w < 1e-4:
            rows.append([len(verts)])
            verts.append(Vector((0.0, y, 0.0)))
            continue
        m = min(MIDRIB, 0.4 * w)
        row = []
        for x in (-w, -m, m, w):
            row.append(len(verts))
            verts.append(Vector((x, y, spec["fold"] * max(abs(x) - m, 0.0))))
        rows.append(row)

    def uv(i):
        v = verts[i]
        return (0.45 + 0.4 * v.x / hw, v.y)

    for r0_, r1_ in zip(rows, rows[1:]):
        if len(r0_) == 1:
            for j in range(3):
                faces.append((r0_[0], r1_[j + 1], r1_[j]))
                fmat.append(rib if j == 1 else leaf)
        elif len(r1_) == 1:
            for j in range(3):
                faces.append((r0_[j], r0_[j + 1], r1_[0]))
                fmat.append(rib if j == 1 else leaf)
        else:
            for j in range(3):
                faces.append((r0_[j], r0_[j + 1], r1_[j + 1], r1_[j]))
                fmat.append(rib if j == 1 else leaf)
        for f in faces[len(uvs):]:
            uvs.append(tuple(uv(i) for i in f))
    me = mesh_from(name, verts, faces, fmat, uvs,
                   [mats[spec["leaf"]], mats[spec["rib"]], mats["bop_stalk"]])
    for poly in me.polygons:
        poly.use_smooth = True
    return me


def folded_card(verts, faces, fmat, base, along, up, length, half, fold, m, stations):
    """A pointed petal from `base` along `along`, its face toward `up`, folded
    along its middle so it keeps some body seen edge-on."""
    side = along.cross(up).normalized()
    face = side.cross(along).normalized()
    rows = []
    for s, w in stations:
        c = base + along * (s * length)
        if w <= 0.0:
            rows.append([len(verts)])
            verts.append(c)
            continue
        row = []
        for u in (-1.0, 0.0, 1.0):
            row.append(len(verts))
            verts.append(c + side * (u * w * half) - face * (fold * w * half * (1.0 - abs(u))))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        if len(r1) == 1:
            for j in range(2):
                faces.append((r0[j], r0[j + 1], r1[0]))
                fmat.append(m)
        else:
            for j in range(2):
                faces.append((r0[j], r0[j + 1], r1[j + 1], r1[j]))
                fmat.append(m)


def flower_blade(name, mats):
    """One flower head, the stalk's tip at the origin: the spathe, a canoe with
    its beak along +Y and a red-mauve band under its rim, and out of its
    opening a fan of three orange sepals and a blue arrow pointing forward."""
    verts, faces, fmat = [], [], []
    green, rim, sepal, petal = 0, 1, 2, 3
    # (y, half-width, keel z, rim z) from the heel to the beak's tip.
    # Narrow and deep, as a beak is: the stalk meets it near the heel.
    stations = [(-0.045, 0.012, 0.0, 0.045), (-0.015, 0.022, -0.040, 0.052), (0.04, 0.025, -0.050, 0.046),
                (0.11, 0.021, -0.043, 0.032), (0.19, 0.014, -0.028, 0.017), (0.26, 0.007, -0.012, 0.006),
                (0.31, 0.0, -0.002, 0.0)]
    heel = len(verts)
    verts.append(Vector((0.0, -0.06, 0.025)))
    rows = []
    for y, w, keel, top in stations:
        if w <= 0.0:
            rows.append([len(verts)])
            verts.append(Vector((0.0, y, 0.0)))
            continue
        low = keel + 0.55 * (top - keel)
        row = []
        for x, z in ((-0.8 * w, top), (-w, low), (0.0, keel), (w, low), (0.8 * w, top)):
            row.append(len(verts))
            verts.append(Vector((x, y, z)))
        rows.append(row)
    for j in range(4):
        faces.append((heel, rows[0][j], rows[0][j + 1]))
        fmat.append(rim if j in (0, 3) else green)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(4):
            if len(r1) == 1:
                faces.append((r0[j + 1], r0[j], r1[0]))
            else:
                faces.append((r0[j + 1], r0[j], r1[j], r1[j + 1]))
            fmat.append(rim if j in (0, 3) else green)

    card = [(0.0, 0.3), (0.35, 1.0), (0.75, 0.7), (1.0, 0.0)]
    up = Vector((0.0, 0.0, 1.0))
    # Sepals: (lean from the beak's line toward up, deg; yaw, deg; length; base y).
    for pitch, yaw, length, y in ((52.0, -12.0, 0.20, 0.06), (78.0, 4.0, 0.22, 0.03), (104.0, 14.0, 0.18, 0.0)):
        p, a = math.radians(pitch), math.radians(yaw)
        along = Vector((math.sin(a) * math.cos(p), math.cos(a) * math.cos(p), math.sin(p)))
        normal = Vector((math.cos(a), -math.sin(a), 0.0))
        folded_card(verts, faces, fmat, Vector((0.0, y, 0.045)), along, normal,
                    length, 0.030, 0.5, sepal, card)
    for pitch, yaw, length, y, half in ((30.0, -4.0, 0.17, 0.09, 0.022), (60.0, 8.0, 0.12, 0.07, 0.016)):
        p, a = math.radians(pitch), math.radians(yaw)
        along = Vector((math.sin(a) * math.cos(p), math.cos(a) * math.cos(p), math.sin(p)))
        normal = Vector((math.cos(a), -math.sin(a), 0.0))
        folded_card(verts, faces, fmat, Vector((0.0, y, 0.04)), along, normal,
                    length, half, 0.6, petal, card)
    uvs = [tuple((0.5 + verts[i].x, 0.5 + verts[i].y) for i in f) for f in faces]
    me = mesh_from(name, verts, faces, fmat, uvs,
                   [mats["bop_spathe"], mats["bop_spathe_rim"], mats["bop_sepal"], mats["bop_petal"]])
    for poly in me.polygons:
        poly.use_smooth = True
    return me


def sheath_mesh(name, mats):
    """The clump's base: the leaves' sheathing feet, a fluted cone."""
    n, verts, faces = 10, [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 0.17 if i % 2 == 0 else 0.14
        verts.append(Vector((r * math.cos(a), r * math.sin(a), -0.02)))
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        verts.append(Vector((0.075 * math.cos(a), 0.075 * math.sin(a), 0.2)))
    verts.append(Vector((0.0, 0.0, 0.24)))
    for i in range(n):
        j = (i + 1) % n
        faces += [(i, j, n + i), (j, n + j, n + i), (n + i, n + j, 2 * n)]
    uvs = [tuple((0.5 + verts[i].x, 0.5 + verts[i].y) for i in f) for f in faces]
    me = mesh_from(name, verts, faces, [0] * len(faces), uvs, [mats["bop_sheath"]])
    for poly in me.polygons:
        poly.use_smooth = True
    return me


def head_group():
    """This object's Head, carried to the Course's tip: its beak turned out
    from the plant's middle by the tip's bearing and Turn, raised by Tilt
    (both degrees), sized by Scale."""
    ng, io = plant_blades._node_group("kyt_head_at_course_tip", (
        ("Course", "NodeSocketObject", None), ("Head", "NodeSocketObject", None),
        ("Turn", "NodeSocketFloat", 0.0), ("Tilt", "NodeSocketFloat", 0.0), ("Scale", "NodeSocketFloat", 1.0)))
    if io is None:
        return ng
    gin, gout = io
    N = ng.nodes.new

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
    head = N("GeometryNodeObjectInfo")
    head.transform_space = "ORIGINAL"
    link(ng, gin, "Head", head, "Object")
    tip = N("GeometryNodeSampleCurve")
    tip.mode = "FACTOR"
    tip.inputs["Factor"].default_value = 1.0
    link(ng, course, "Geometry", tip, "Curves")
    xyz = N("ShaderNodeSeparateXYZ")
    link(ng, tip, "Position", xyz, "Vector")
    bearing = N("ShaderNodeMath")
    bearing.operation = "ARCTAN2"
    link(ng, xyz, "Y", bearing, 0)
    link(ng, xyz, "X", bearing, 1)
    # The beak is +Y: turn it by the bearing less a quarter turn, plus Turn.
    yaw = scalar("ADD", scalar("ADD", bearing, "Value", value=-math.pi / 2), "Value",
                 scalar("RADIANS", gin, "Turn"), "Value")
    euler = N("ShaderNodeCombineXYZ")
    link(ng, scalar("RADIANS", gin, "Tilt"), "Value", euler, "X")
    link(ng, yaw, "Value", euler, "Z")
    rot = N("FunctionNodeEulerToRotation")
    link(ng, euler, "Vector", rot, "Euler")
    size = N("ShaderNodeCombineXYZ")
    for axis in "XYZ":
        link(ng, gin, "Scale", size, axis)
    move = N("GeometryNodeTransform")
    link(ng, head, "Geometry", move, "Geometry")
    link(ng, tip, "Position", move, "Translation")
    link(ng, rot, "Rotation", move, "Rotation")
    link(ng, size, "Vector", move, "Scale")
    link(ng, move, "Geometry", gout, "Geometry")
    plant_blades._tidy(ng)
    return ng


def bezier(name, pts, props, coll):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 24
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, co in zip(sp.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, cu)
    coll.objects.link(obj)
    for k, v in props.items():
        obj[k] = v
    return obj


def leaf_course(name, heading, lean, length, stalk, base, kind, coll):
    """Straight up the stalk at a steep rise, then the paddle bending out and
    over, more the further the leaf leans."""
    rise0 = math.radians(lerp(86.0, 62.0, lean))
    rise1 = math.radians(lerp(72.0, 2.0, lean))
    h = Vector((math.cos(math.radians(heading)), math.sin(math.radians(heading)), 0.0))
    up = Vector((0.0, 0.0, 1.0))
    p, pts, steps = base.copy(), [base.copy()], 48
    for k in range(steps):
        s = (k + 0.5) / steps
        ang = rise0 if s < stalk else rise0 + (rise1 - rise0) * ((s - stalk) / (1.0 - stalk)) ** 1.2
        p += (h * math.cos(ang) + up * math.sin(ang)) * (length / steps)
        pts.append(p.copy())
    picks = [0, round(steps * stalk * 0.5), round(steps * stalk), round(steps * (stalk + (1 - stalk) / 3)),
             round(steps * (stalk + 2 * (1 - stalk) / 3)), steps]
    return bezier(name, [pts[i] for i in picks], {"kyt_course": name.removeprefix("course_"), "kyt_kind": kind},
                  coll)


def flower_course(name, heading, rise, height, base, coll):
    """A stiff stalk, bowing a little outward near the top."""
    h = Vector((math.cos(math.radians(heading)), math.sin(math.radians(heading)), 0.0))
    up = Vector((0.0, 0.0, 1.0))
    r = math.radians(rise)
    length = height / math.sin(r)
    pts = [base + (h * math.cos(r) + up * math.sin(r)) * (length * t) + h * (0.04 * t * t) for t in (0, 0.5, 1)]
    return bezier(name, pts, {"kyt_course": name.removeprefix("course_"), "kyt_kind": "flower"}, coll)


def clear():
    for coll in ("courses", "blades", "export"):
        c = bpy.data.collections.get(coll)
        if c is not None:
            for o in list(c.all_objects):
                bpy.data.objects.remove(o)
    for pool in (bpy.data.meshes, bpy.data.curves):
        for block in list(pool):
            if block.users == 0:
                pool.remove(block)


def build(v, sfx, home, lines, blades, head, mats, stem_ng, head_ng, sheath):
    """One variant's leaves, flowers and sheath, into `home`, its courses into
    `lines`; its parts' names end in `sfx`."""
    rng = random.Random(SEED)

    def leaf_row(kind, table, prefix):
        made = []
        for i, (heading, lean, length, width) in enumerate(table):
            heading += rng.uniform(-9.0, 9.0)
            a = math.radians(heading + rng.uniform(-40.0, 40.0))
            base = Vector((math.cos(a), math.sin(a), 0.0)) * rng.uniform(0.03, 0.09) + Vector((0, 0, 0.02))
            c = leaf_course(f"course_{prefix}_{i:02d}{sfx}", heading, lean, length * rng.uniform(0.95, 1.05),
                            KINDS[kind]["stalk"], base, kind, lines)
            share = width * (v["width"] if kind == "mature" else 1.0)
            made.append({"name": f"{prefix}_{i:02d}{sfx}", "course": c, "blade": blades[kind],
                         "inputs": {"Width": share * rng.uniform(0.92, 1.08), "Offset": 0.0,
                                    "Sway": rng.uniform(-0.05, 0.05), "Reach": 1.0}})
        return made

    leaves = leaf_row("mature", v["mature"], "leaf") + leaf_row("young", v["young"], "young")
    for i, (heading, rise, height, turn, tilt, scale) in enumerate(v["flowers"]):
        heading += rng.uniform(-8.0, 8.0)
        a = math.radians(heading)
        base = Vector((math.cos(a), math.sin(a), 0.0)) * 0.05 + Vector((0, 0, 0.02))
        c = flower_course(f"course_flower_{i:02d}{sfx}", heading, rise, height, base, lines)
        me = bpy.data.meshes.new(f"stalk_{i:02d}{sfx}")
        me.materials.append(mats["bop_stalk"])
        stalk = part(f"stalk_{i:02d}{sfx}", me, home)
        mod = stalk.modifiers.new(stem_ng.name, "NODES")
        mod.node_group = stem_ng
        plant_blades._set(mod, stem_ng, {"Course": c, "Material": mats["bop_stalk"], "Base radius": 0.016,
                                         "Tip radius": 0.012, "Sides": 5, "Stations": 5})
        me = bpy.data.meshes.new(f"head_{i:02d}{sfx}")
        for m in head.data.materials:
            me.materials.append(m)
        obj = part(f"head_{i:02d}{sfx}", me, home)
        mod = obj.modifiers.new(head_ng.name, "NODES")
        mod.node_group = head_ng
        plant_blades._set(mod, head_ng, {"Course": c, "Head": head, "Turn": turn, "Tilt": tilt, "Scale": scale})
        obj["kyt_flower_head"] = True
    leaves += leaf_row("mature", v["droop"], "droop")
    for leaf in leaves:
        plant_blades.add_leaf(leaf, None)
        obj = bpy.data.objects[leaf["name"]]
        if home is not bpy.data.collections["export"]:
            bpy.data.collections["export"].objects.unlink(obj)
            home.objects.link(obj)
    part(f"sheath{sfx}", sheath, home)


def part(name, mesh, home):
    obj = bpy.data.objects.new(name, mesh)
    home.objects.link(obj)
    obj["kyt_collision"] = "none"
    return obj


def report(tag, home):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts, tris, low = [], 0, {}
    for o in home.objects:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        vs = [o.matrix_world @ vv.co for vv in me.vertices]
        pts += vs
        if o.name.startswith("droop_"):
            low[o.name] = (min(p.z for p in vs), max(p.z for p in vs), max(p.xy.length for p in vs))
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        ev.to_mesh_clear()
    v = VARIANTS[tag]
    print(f"bird_of_paradise {tag}: {len(v['mature'])} leaves, {len(v['young'])} young, {len(v['droop'])} drooping, "
          f"{len(v['flowers'])} flowers; {max(p.z for p in pts):.2f} m tall, "
          f"{2 * max(p.xy.length for p in pts):.2f} m across, {tris} triangles")
    for name, (lo, hi, out) in low.items():
        print(f"bird_of_paradise {tag}:   {name}: {lo:.2f} to {hi:.2f} m up, reaching {out:.2f} m out")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    courses = bpy.data.collections.get("courses")
    if courses is not None and len(courses.objects) and "--replace" not in argv:
        raise SystemExit("bird_of_paradise: this file has courses already; --replace rebuilds them")
    clear()
    mats = {k: colour(k, srgb, rough, double) for k, (srgb, rough, double) in MATERIALS.items()}
    blades_coll = add_courses.child_collection("authored", "blades")
    blades = {}
    for kind, spec in KINDS.items():
        blades[kind] = bpy.data.objects.new(f"blade_{kind}", leaf_blade(f"blade_{kind}", spec, mats))
        blades_coll.objects.link(blades[kind])
    head = bpy.data.objects.new("blade_flower", flower_blade("blade_flower", mats))
    blades_coll.objects.link(head)
    plant_blades.lay_out_blades([blades["mature"], blades["young"], head])

    stem_ng, head_ng = plant_blades.course_stem_group(), head_group()
    export = bpy.data.collections["export"]
    courses = add_courses.child_collection("authored", "courses")
    sheath = sheath_mesh("sheath", mats)
    for tag, v in VARIANTS.items():
        sfx = "" if tag == "a" else f"_{tag}"
        home, lines = export, courses
        if tag != "a":
            home = bpy.data.collections.get(f"variant_{tag}") or bpy.data.collections.new(f"variant_{tag}")
            lines = bpy.data.collections.get(f"variant_{tag}_courses") or \
                bpy.data.collections.new(f"variant_{tag}_courses")
            if home.name not in export.children:
                export.children.link(home)
            if lines.name not in courses.children:
                courses.children.link(lines)
        build(v, sfx, home, lines, blades, head, mats, stem_ng, head_ng, sheath)
        for o in home.objects:
            o["kyt_variant"] = tag
        report(tag, home)
    layers = bpy.context.view_layer.layer_collection
    for tag in VARIANTS:
        if tag != "a":
            layers.children["export"].children[f"variant_{tag}"].hide_viewport = True
            layers.children["authored"].children["courses"].children[f"variant_{tag}_courses"].hide_viewport = True
    if bpy.data.objects.get("plant_base") is None:
        base = bpy.data.objects.new("plant_base", None)
        base.empty_display_type = "PLAIN_AXES"
        base.empty_display_size = 0.1
        bpy.data.collections["reference"].objects.link(base)
    bpy.context.scene["kyt_godot_scene"] = GODOT_SCENE

    bpy.ops.wm.save_mainfile()


if __name__ == "__main__":
    main()
