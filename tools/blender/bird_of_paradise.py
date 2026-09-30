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
  halves folded up off a pale midrib that tapers out short of the tip, ribbed
  between fine side veins and lighter at the edge (`leaf_textures`), the young one narrower and folded
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
# red-mauve rim, the crest orange, the arrow blue. Near matte (her "way too
# plasticy": at 0.5 to 0.7 the ribs and petals caught hard highlights).
MATERIALS = {
    "bop_leaf": ((0.19, 0.42, 0.30), 0.9, True),
    "bop_midrib": ((0.55, 0.65, 0.42), 0.9, True),  # her "the central vein slightly darker": 0.88 of (0.62, 0.74, 0.48)
    "bop_young": ((0.33, 0.57, 0.33), 0.9, True),
    "bop_young_midrib": ((0.63, 0.72, 0.46), 0.9, True),  # 0.88 of (0.72, 0.82, 0.52)
    "bop_stalk": ((0.34, 0.50, 0.30), 0.9, False),
    "bop_sheath": ((0.42, 0.38, 0.22), 0.95, False),
    "bop_spathe": ((0.36, 0.47, 0.35), 0.85, True),
    "bop_spathe_rim": ((0.66, 0.29, 0.40), 0.85, True),
    "bop_sepal": ((1.0, 0.57, 0.08), 0.85, True),
    "bop_petal": ((0.16, 0.30, 0.86), 0.85, True),
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
# The midrib stops short of the tip (her "the vein shouldnt go all the way to
# the tip of the leaf"): full width to `RIB_TAPER` of the way along the paddle,
# narrowing to `RIB_THIN` of it at `RIB_END`, plain leaf beyond.
RIB_TAPER, RIB_END, RIB_THIN = 0.5, 0.84, 0.15
# Since her "ever so slightly blur the central vein" the midrib is painted in
# the leaf's texture (its strip in the geometry wears the leaf's material): the
# same width and taper, its colour `bop_midrib` (`bop_young_midrib`), its edge
# blurred by a Gaussian `RIB_BLUR` (m) wide, and ("have it kind of fade at the
# tip of the vein") its colour fading into the leaf between `RIB_FADE` shares of
# the paddle. Her "not blurry enough" of the first 1.5 mm: 5 mm.
RIB_BLUR, RIB_FADE = 0.005, (0.6, 0.86)
# The paddles' textures (`leaf_textures`), after her third photo (2026-09-29,
# "give the leaves this subtle rippling/ribbing", "make the edges a little
# brighter"): fine side veins leaving the midrib at about 60 degrees and
# curving toward the tip (`along = a * VEIN_SLANT[0] + a^2 * VEIN_SLANT[1]`, a
# the distance out from the midrib), `VEIN_M` apart, the leaf corrugated
# between them `RIPPLE_M` deep in a normal map (softly, `RIDGE` the profile's
# power: 1 a plain wave, below 1 a sharp crease at each vein), a little lighter on the ridges
# and along each vein; the margin lightened `EDGE_LIGHT` of the way toward
# `EDGE_TOWARD` at the edge, fading over `EDGE_M`. Metres, on a paddle
# `PADDLE_M` long; a paddle's widest half spans `UV_ACROSS` of U either side of
# its middle, V runs its length. Written to
# `assets/source/textures/bird_of_paradise/` (across by along pixels).
LEAF_TEX = (256, 512)
UV_ACROSS = 0.46
PADDLE_M = 0.75
# Her "these need to be larger and fewer": veins 55 mm apart (22 at first), a
# plain wave (a 0.7 crease at first); then "still too much": 1.2 mm deep (3),
# the shading on the ridges and the veins' lightening halved; then "closer but
# continue to make them fewer": 90 mm apart (55); then "the ridges slightly
# lighter": the rib lines lightened 6% (2.5).
VEIN_M, VEIN_SLANT = 0.09, (0.58, 1.5)
RIPPLE_M, RIDGE, RIPPLE_SHADE, VEIN_LIGHT = 0.0012, 1.0, 0.015, 0.06
# Her "blur those lines 12%": each rib line, `VEIN_LINE` of the spacing either
# side of its vein, blurred by a Gaussian `VEIN_BLUR` of the spacing (sharp at
# first), softer and wider; its middle kept as light as before the blur.
VEIN_LINE, VEIN_BLUR = 0.0804, 0.12
# And "they shouldnt reach the edge of the leaves": the ripples and veins fade
# out between these distances in from the margin (m), clear of the light rim.
RIPPLE_STOP = (0.015, 0.04)
# Her "blur and extend the bright edge of the leaf further into the body":
# the rim fades over 30 mm (12) on a soft S-curve (a steeper power curve first).
EDGE_M, EDGE_LIGHT, EDGE_TOWARD = 0.03, 0.4, (0.72, 0.84, 0.52)
TEXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
                        "assets", "source", "textures", "bird_of_paradise")
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


def rib_half(s, w):
    """The midrib's half-width at `s` along the paddle, where it is `w` wide."""
    narrow = 1.0 - (1.0 - RIB_THIN) * min(max((s - RIB_TAPER) / (RIB_END - RIB_TAPER), 0.0), 1.0)
    return min(MIDRIB * narrow, 0.4 * w)


def leaf_blade(name, spec, mats):
    """The stalk, a three-sided prism flat on top, then the folded paddle."""
    verts, faces, fmat, uvs = [], [], [], []
    leaf, stalk_m = 0, 1
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
        m = rib_half(s, w)
        row = []
        for x in (-w, -m, m, w):
            row.append(len(verts))
            verts.append(Vector((x, y, spec["fold"] * max(abs(x) - m, 0.0))))
        rows.append(row)

    def uv(i):
        v = verts[i]
        if v.y < p - 1e-6 or i < 3 * len(ys):
            return (0.9 + 0.1 * (v.x / r0 + 1.0) * 0.5, v.y)
        return (0.5 + UV_ACROSS * v.x / hw, (v.y - p) / (1.0 - p))

    for r0_, r1_ in zip(rows, rows[1:]):
        if len(r0_) == 1:
            for j in range(3):
                faces.append((r0_[0], r1_[j + 1], r1_[j]))
        elif len(r1_) == 1:
            for j in range(3):
                faces.append((r0_[j], r0_[j + 1], r1_[0]))
        else:
            for j in range(3):
                faces.append((r0_[j], r0_[j + 1], r1_[j + 1], r1_[j]))
        fmat += [leaf] * 3
        for f in faces[len(uvs):]:
            uvs.append(tuple(uv(i) for i in f))
    me = mesh_from(name, verts, faces, fmat, uvs, [mats[spec["leaf"]], mats["bop_stalk"]])
    for poly in me.polygons:
        poly.use_smooth = True
    return me


def leaf_textures(kind, spec):
    """The paddle's colour and normal map (see LEAF_TEX), in its blade's UVs."""
    import numpy as np
    W, H = LEAF_TEX
    hw = spec["half"]
    uu, s = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)  # rows bottom first, as Blender's
    a = np.abs(uu - 0.5) / UV_ACROSS * hw
    edge_w = hw * np.interp(s, PADDLE, [outline(x) for x in PADDLE])
    in_from_edge = edge_w - a
    phase = (s * PADDLE_M - (a * VEIN_SLANT[0] + a * a * VEIN_SLANT[1])) / VEIN_M
    ridge = np.abs(np.sin(np.pi * phase)) ** RIDGE  # 0 in a vein, 1 between
    stop = np.clip((in_from_edge - RIPPLE_STOP[0]) / (RIPPLE_STOP[1] - RIPPLE_STOP[0]), 0.0, 1.0)
    inner = np.clip((a - MIDRIB) / 0.01, 0.0, 1.0) * stop * stop * (3.0 - 2.0 * stop)
    height = RIPPLE_M * ridge * inner
    dx, dy = hw / UV_ACROSS / W, PADDLE_M / H
    n = np.dstack((-np.gradient(height, axis=1) / dx, -np.gradient(height, axis=0) / dy, np.ones_like(height)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)

    base = np.array(MATERIALS[spec["leaf"]][0], dtype=np.float32)
    rgb = base * (1.0 + RIPPLE_SHADE * (2.0 * ridge - 1.0) * inner)[..., None]
    off = np.abs(phase - np.round(phase))  # share of the spacing from the nearest vein
    erf = np.vectorize(math.erf)
    reach = VEIN_BLUR * math.sqrt(2.0)
    vein = 0.5 * (erf((off + VEIN_LINE) / reach) - erf((off - VEIN_LINE) / reach)) * inner
    vein /= math.erf(VEIN_LINE / reach)  # the blurred line's middle back to full
    rgb = rgb + (1.0 - rgb) * (VEIN_LIGHT * vein)[..., None]
    t = np.clip(in_from_edge / EDGE_M, 0.0, 1.0)
    rim = 1.0 - t * t * (3.0 - 2.0 * t)
    rgb = rgb + (np.array(EDGE_TOWARD, dtype=np.float32) - rgb) * (EDGE_LIGHT * rim)[..., None]
    halves = [rib_half(x, hw * outline(x)) if hw * outline(x) >= 1e-4 else 0.0 for x in PADDLE]
    m = np.interp(s, PADDLE, halves)  # as the geometry's strip, straight between stations
    f = np.clip((s - RIB_FADE[0]) / (RIB_FADE[1] - RIB_FADE[0]), 0.0, 1.0)
    rib = 0.5 * (1.0 - erf((a - m) / (RIB_BLUR * math.sqrt(2.0)))) * (1.0 - f * f * (3.0 - 2.0 * f))
    rgb = rgb + (np.array(MATERIALS[spec["rib"]][0], dtype=np.float32) - rgb) * rib[..., None]
    return (save_image(f"bird_of_paradise_{kind}_colour", rgb, True),
            save_image(f"bird_of_paradise_{kind}_normal", n * 0.5 + 0.5, False))


def save_image(name, rgb, colour_data):
    """`rgb` (rows bottom first; sRGB for a colour) as a PNG in TEXTURES, loaded
    back from the file so the GLB carries the file's own bytes."""
    import numpy as np
    os.makedirs(TEXTURES, exist_ok=True)
    path = os.path.abspath(os.path.join(TEXTURES, f"{name}.png"))
    for old in [i for i in bpy.data.images if i.name == name or bpy.path.abspath(i.filepath) == path]:
        bpy.data.images.remove(old)
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=False)
    if not colour_data:
        img.colorspace_settings.name = "Non-Color"
    rgba = np.concatenate((np.clip(rgb, 0.0, 1.0), np.ones((h, w, 1))), axis=2).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw, img.file_format = path, "PNG"
    img.save()
    bpy.data.images.remove(img)
    img = bpy.data.images.load(path)
    img.name = name
    img.filepath = bpy.path.relpath(path)
    if not colour_data:
        img.colorspace_settings.name = "Non-Color"
    return img


def wear(mat, colour_img, normal_img):
    """The material's colour from `colour_img` and its relief from `normal_img`."""
    nt = mat.node_tree
    for node in [n for n in nt.nodes if n.name.startswith("kyt_")]:
        nt.nodes.remove(node)
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.name, tex.image, tex.location = "kyt_colour", colour_img, (-600, 300)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    ntex = nt.nodes.new("ShaderNodeTexImage")
    ntex.name, ntex.image, ntex.location = "kyt_normal_image", normal_img, (-600, -200)
    relief = nt.nodes.new("ShaderNodeNormalMap")
    relief.name, relief.location = "kyt_normal", (-300, -200)
    nt.links.new(ntex.outputs["Color"], relief.inputs["Color"])
    nt.links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])


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
    for kind, spec in KINDS.items():
        wear(mats[spec["leaf"]], *leaf_textures(kind, spec))
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
