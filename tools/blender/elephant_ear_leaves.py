"""Give the elephant ear's leaves the bird of paradise's leaf treatment.

    Blender --background assets/source/props/elephant_ear.blend \
        --python tools/blender/elephant_ear_leaves.py [-- --no-save]

Her "take the example of the leaves from the bird of paradise ... and apply
that to these leaves" (2026-09-30). The bird of paradise's leaves
(`bird_of_paradise.py`, `leaf_textures`) were tuned on her word through the
night of 2026-09-29: near matte; a colour and a normal map per leaf kind; side
veins leaving the midrib at about 60 degrees and bending toward the tip, 90 mm
apart, each a soft rib line 6% lighter, blurred 12% of the spacing; a 1.2 mm
ripple between them, faintly shaded, stopping 15 to 40 mm short of the edge;
the edge brightened 40% toward a pale green, fading over 30 mm; the central
vein painted rather than a hard strip, 0.88 as light as its pale green, its
edge blurred 1.5 mm, narrowing from halfway and fading out short of the tip.
The same values here, on the elephant ear's own veins: the side veins off the
midrib, and in each lobe a basal vein from the notch toward the lobe's end
with side veins of its own; the first vein out from the notch divides the two.
Since her "scallop the edges a bit more to enhance the ripples", the edge is
cut into a shallow scallop between each pair of veins (the colour's alpha,
clipped), and the ripples' stop follows the cut edge. Since her "the reverse
where the leaf starts light in the center and gets darker towards the edges",
the bright rim is turned round: the leaf lightens toward its middle and
darkens toward its edge, across its whole width. The red varietal's leaf
materials (`RED`), whose leaves bend the same blades, get their own colour
maps drawn the same way in their own colours, their darker parts tinted
toward plum, and share the green normal maps.

For each blade in `authored/blades` (`blade_mature`, `blade_young`), read from
the file as it is, so it follows her reshaping:
- the leaf's UVs, laid flat as the blade is seen from its front: U across (its
  widest half spans `UV_ACROSS` either side of the middle), V along from the
  lobes' ends to the tip. The stalk keeps its own material and no texture.
- `assets/source/textures/elephant_ear/elephant_ear_<kind>_colour.png` and
  `_normal.png`, `LEAF_TEX` pixels, drawn from the leaf's outline (its mesh's
  open edges), its notch and size (`kyt_leaf_*`) and its material's colour,
  and worn by that material.

The texture is drawn, not painted: running this again redraws it. Once she
paints a leaf by hand, stop running it on that kind. Saves unless --no-save.
"""

import math
import os
import sys

import bpy

TEXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
                        "assets", "source", "textures", "elephant_ear")
LEAF_TEX = (512, 512)  # across by along; about 1.7 mm a pixel on the mature leaf
UV_ACROSS, UV_MARGIN = 0.46, 0.02

# The bird of paradise's values (`bird_of_paradise.py`, each her call on its
# leaves). The side veins' bend: along = a * 0.58 + a^2 * 1.5 there, on a
# paddle 0.15 m in half-width; here the 1.5 is scaled to the leaf's half-width
# (`VEIN_BEND` / W), so a vein meets the margin at the same angle.
VEIN_M, VEIN_SLANT, VEIN_BEND = 0.09, 0.58, 0.225
RIPPLE_M, RIDGE, RIPPLE_SHADE, VEIN_LIGHT = 0.0012, 1.0, 0.015, 0.06
VEIN_LINE, VEIN_BLUR = 0.0804, 0.12
RIPPLE_STOP = (0.015, 0.04)
# Her "maybe lets do the reverse where the leaf starts light in the center
# and gets darker towards the edges" (2026-09-30), in place of the bird of
# paradise's bright rim (40% toward pale green over 30 mm): across the leaf,
# from its middle line (the midrib; a lobe's basal vein) to its edge, the
# colour runs from `CENTRE_LIGHT` of the way toward the pale green to
# `EDGE_DARK` darker, evenly.
CENTRE_LIGHT, EDGE_DARK = 0.3, 0.2
RIB_TAPER, RIB_END, RIB_THIN = 0.5, 0.84, 0.15
RIB_BLUR, RIB_FADE, RIB_DARK = 0.0015, (0.6, 0.86), 0.88
# Her "soften the central vein a bit more" (2026-09-30): the midrib's edge
# blurred by a Gaussian this wide (m), the bird of paradise's RIB_BLUR before;
# the basal veins keep RIB_BLUR.
MIDRIB_BLUR = 0.004
BASAL = 0.8  # a basal vein's width against the midrib's
# Her "scallop the edges a bit more to enhance the ripples" (2026-09-30): the
# edge cut into shallow arcs, one between each pair of side veins, meeting in
# a cusp `SCALLOP_M` in from the leaf's outline where a vein reaches it, so
# the ripples run out into the scallops. Cut into the colour's alpha, which the
# material clips (glTF alpha mask, Godot alpha scissor), as the palm crown's
# torn edges are; the tip and the notch keep their outline (`SCALLOP_CLEAR`).
SCALLOP_M, SCALLOP_CLEAR = 0.015, 0.08

# Per leaf material: the veins' pale green (before RIB_DARK) and the pale
# green the leaf's middle lightens toward, sRGB, the elephant ear's own.
PALE = {
    "elephant_ear_leaf": ((0.64, 0.79, 0.32), (0.72, 0.86, 0.40)),
    "elephant_ear_young_leaf": ((0.76, 0.88, 0.42), (0.80, 0.90, 0.50)),
    # The red varietal (her "then make a redder varietal", 2026-09-30):
    # rose-pink veins, the middle lightening toward copper.
    "elephant_ear_red_leaf": ((0.90, 0.52, 0.48), (0.84, 0.42, 0.34)),
    "elephant_ear_red_young_leaf": ((0.95, 0.62, 0.55), (0.90, 0.52, 0.42)),
}
# A green leaf material's twin in the red varietal, whose leaves bend the same
# blades: the same veins, ripples and scallops (the same normal map) in its
# own colours, `elephant_ear_red_<kind>_colour.png`.
# Her "give the darker parts a purply tint" (2026-09-30, the red varietal):
# as a red leaf darkens toward its edge it leans toward plum, all the way to
# `PURPLE` of the way there at the edge and none in its copper middle; a
# per-channel tint, so the ripples and vein lines keep their detail under it.
PURPLE = {"elephant_ear_red_leaf": (0.30, 0.10, 0.32),
          "elephant_ear_red_young_leaf": (0.44, 0.17, 0.42)}
PURPLE_TINT = 0.6
RED = {"elephant_ear_leaf": "elephant_ear_red_leaf",
       "elephant_ear_young_leaf": "elephant_ear_red_young_leaf"}


def rib_half(s, mid, w):
    """The midrib's half-width `s` along the leaf from the notch (0) to the tip
    (1), `mid` at the notch and the leaf `w` wide there: full to RIB_TAPER,
    narrowing to RIB_THIN of it at RIB_END (the bird of paradise's, her "the
    vein shouldnt go all the way to the tip of the leaf")."""
    narrow = 1.0 - (1.0 - RIB_THIN) * min(max((s - RIB_TAPER) / (RIB_END - RIB_TAPER), 0.0), 1.0)
    return min(mid * narrow, 0.45 * w)


def linear_to_srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def leaf_parts(blade):
    """The blade's leaf material, its leaf faces and their open edges."""
    me = blade.data
    slot = next(i for i, m in enumerate(me.materials) if m and m.name in PALE)
    faces = [p for p in me.polygons if p.material_index == slot]
    count = {}
    for p in faces:
        for e in p.edge_keys:
            count[e] = count.get(e, 0) + 1
    edges = [e for e, n in count.items() if n == 1]
    return me.materials[slot], slot, faces, edges


def lay_uvs(blade, slot, faces, frame):
    xmax, ymin, ymax = frame
    me = blade.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for p in faces:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (0.5 + UV_ACROSS * co.x / xmax,
                              UV_MARGIN + (1.0 - 2.0 * UV_MARGIN) * (co.y - ymin) / (ymax - ymin))


def leaf_texture(kind, blade, mat, edges, frame, tag=""):
    import numpy as np
    xmax, ymin, ymax = frame
    J, Lb = blade["kyt_leaf_notch_m"], blade["kyt_leaf_length_m"]
    W, mid = blade["kyt_leaf_half_width_m"], blade["kyt_leaf_midrib_m"]
    verts = blade.data.vertices
    Wpx, Hpx = LEAF_TEX
    u, v = np.meshgrid((np.arange(Wpx) + 0.5) / Wpx, (np.arange(Hpx) + 0.5) / Hpx)  # rows bottom first
    x = (u - 0.5) * xmax / UV_ACROSS
    y = ymin + (v - UV_MARGIN) / (1.0 - 2.0 * UV_MARGIN) * (ymax - ymin)
    a, py = np.abs(x), y - J  # out from the midrib, along from the notch

    # How far in from the leaf's edge: the nearest open edge of its mesh,
    # negative outside it (a crossing count), where the texture is its edge's
    # colour, so nothing darker bleeds in as it is seen smaller, and clear.
    in_from_edge = np.full(x.shape, np.inf)
    inside = np.zeros(x.shape, dtype=bool)
    for i, j in edges:
        p, q = verts[i].co, verts[j].co
        dx, dy = q.x - p.x, q.y - p.y
        t = np.clip(((x - p.x) * dx + (y - p.y) * dy) / max(dx * dx + dy * dy, 1e-12), 0.0, 1.0)
        in_from_edge = np.minimum(in_from_edge, np.hypot(x - p.x - t * dx, y - p.y - t * dy))
        spans = (p.y > y) != (q.y > y)
        cross_x = p.x + (y - p.y) * dx / (dy if abs(dy) > 1e-12 else 1e-12)
        inside ^= spans & (x < cross_x)
    in_from_edge = np.where(inside, in_from_edge, -in_from_edge)

    # The lobe's axis, from the notch to its end (the leaf's lowest point on
    # the +x half), and the first vein out from the notch, halfway between
    # the midrib and that axis, which divides the two sets of side veins.
    lobe_end = min((vt.co for vt in verts if vt.co.x > 1e-4 and any(vt.index in e for e in edges)),
                   key=lambda co: co.y)
    lx, ly = lobe_end.x, lobe_end.y - J
    lobe_len = math.hypot(lx, ly)
    lx, ly = lx / lobe_len, ly / lobe_len
    bx, by = lx, ly + 1.0
    bn = math.hypot(bx, by)
    bx, by = bx / bn, by / bn
    side = bx * py - by * a  # > 0 toward the tip, < 0 toward the lobe
    off_first = np.where(a * bx + py * by > 0.0, np.abs(side), np.inf)

    def slant(off):
        return off * VEIN_SLANT + off * off * VEIN_BEND / W

    # Where the dividing vein meets the edge (the ray from the notch leaves the
    # leaf last there). Each set of side veins is shifted, by under half a
    # spacing, to end a vein there too: two cusps side by side would leave a
    # sliver of scallop between them.
    reach_out = 0.0
    for i, j in edges:
        p, q = verts[i].co, verts[j].co
        ex, ey = q.x - p.x, q.y - p.y
        den = bx * ey - by * ex
        if abs(den) < 1e-12:
            continue
        t_ray = ((p.x) * ey - (p.y - J) * ex) / den
        t_edge = ((p.x) * by - (p.y - J) * bx) / den
        if 0.0 <= t_edge <= 1.0 and t_ray > reach_out:
            reach_out = t_ray
    da, dp = bx * reach_out, by * reach_out

    def aligned(ph, at):
        return ph - (at - round(at))

    s = py / Lb
    m_main = np.array([rib_half(t, mid, W) for t in np.clip(s, 0.0, 1.0).ravel()]).reshape(s.shape)
    phase_main = aligned((py - slant(a)) / VEIN_M, (dp - slant(da)) / VEIN_M)
    along_l = a * lx + py * ly
    off_l = np.abs(lx * py - ly * a)
    t_l = along_l / lobe_len
    m_lobe = BASAL * mid * (1.0 - (1.0 - RIB_THIN) * np.clip((t_l - RIB_TAPER) / (RIB_END - RIB_TAPER), 0.0, 1.0))
    phase_lobe = aligned((along_l - slant(off_l)) / VEIN_M,
                         ((da * lx + dp * ly) - slant(abs(lx * dp - ly * da))) / VEIN_M)
    main = side > 0.0
    phase = np.where(main, phase_main, phase_lobe)
    clear = np.where(main, a - m_main, off_l - m_lobe)  # out from the vein the side veins leave

    share = np.abs(phase - np.round(phase))  # of the spacing, from the nearest side vein
    share = np.minimum(share, off_first / VEIN_M)  # the dividing vein is one of them
    # The scallops: how far in the edge is cut here, none midway between two
    # veins, SCALLOP_M where one meets the edge, a quarter ellipse between;
    # none at the tip, round the notch or at the lobes' ends.
    keep = (np.clip((1.0 - s) * Lb / SCALLOP_CLEAR, 0.0, 1.0)
            * np.clip(np.hypot(a, py) / SCALLOP_CLEAR, 0.0, 1.0)
            * np.clip(np.hypot(a - lx * lobe_len, py - ly * lobe_len) / SCALLOP_CLEAR, 0.0, 1.0))
    cut = SCALLOP_M * keep * (1.0 - np.sqrt(np.clip(1.0 - (1.0 - 2.0 * np.minimum(share, 0.5)) ** 2, 0.0, 1.0)))
    in_from_edge = in_from_edge - cut
    alpha = np.clip(in_from_edge / (xmax / UV_ACROSS / Wpx) + 0.5, 0.0, 1.0)  # a pixel's soft edge

    stop = np.clip((in_from_edge - RIPPLE_STOP[0]) / (RIPPLE_STOP[1] - RIPPLE_STOP[0]), 0.0, 1.0)
    inner = np.clip(clear / 0.01, 0.0, 1.0) * stop * stop * (3.0 - 2.0 * stop)
    ridge = np.abs(np.sin(np.pi * np.minimum(share, 0.5))) ** RIDGE  # 0 in a vein, 1 between
    height = RIPPLE_M * ridge * inner
    dx, dy = xmax / UV_ACROSS / Wpx, (ymax - ymin) / (1.0 - 2.0 * UV_MARGIN) / Hpx
    n = np.dstack((-np.gradient(height, axis=1) / dx, -np.gradient(height, axis=0) / dy, np.ones_like(height)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)

    base = np.array([linear_to_srgb(c) for c in mat.diffuse_color[:3]], dtype=np.float32)
    pale, toward = (np.array(c, dtype=np.float32) for c in PALE[mat.name])
    rgb = base * (1.0 + RIPPLE_SHADE * (2.0 * ridge - 1.0) * inner)[..., None]
    erf = np.vectorize(math.erf)
    reach = VEIN_BLUR * math.sqrt(2.0)
    vein = 0.5 * (erf((share + VEIN_LINE) / reach) - erf((share - VEIN_LINE) / reach)) * inner
    vein /= math.erf(VEIN_LINE / reach)  # the blurred line's middle back to full
    rgb = rgb + (1.0 - rgb) * (VEIN_LIGHT * vein)[..., None]
    # 1 on the middle line, 0 at the (cut) edge, evenly between.
    middle = np.where(main, a, off_l)
    g = np.clip(in_from_edge / np.maximum(in_from_edge + middle, 1e-6), 0.0, 1.0)
    rgb = rgb + (toward - rgb) * (CENTRE_LIGHT * g)[..., None]
    rgb = rgb * (1.0 - EDGE_DARK * (1.0 - g))[..., None]
    if mat.name in PURPLE:
        towards = np.array(PURPLE[mat.name], dtype=np.float32) / (base * (1.0 - EDGE_DARK))
        rgb = rgb * (1.0 + (towards - 1.0) * (PURPLE_TINT * (1.0 - g))[..., None])

    def fading(share_along):
        f = np.clip((share_along - RIB_FADE[0]) / (RIB_FADE[1] - RIB_FADE[0]), 0.0, 1.0)
        return 1.0 - f * f * (3.0 - 2.0 * f)

    rib = 0.5 * (1.0 - erf((a - m_main) / (MIDRIB_BLUR * math.sqrt(2.0)))) * fading(s) * (py >= 0.0)
    basal = 0.5 * (1.0 - erf((off_l - m_lobe) / (RIB_BLUR * math.sqrt(2.0)))) * fading(t_l) * (along_l >= 0.0) * ~main
    rgb = rgb + (pale * RIB_DARK - rgb) * np.maximum(rib, basal)[..., None]
    return (save_image(f"elephant_ear_{tag}{kind}_colour", rgb, True, alpha),
            None if tag else save_image(f"elephant_ear_{kind}_normal", n * 0.5 + 0.5, False))


# `save_image` and `wear` as `bird_of_paradise.py` has them (kept apart while
# that file is still being worked on), with the scallops' alpha and its clip.

def save_image(name, rgb, colour_data, alpha=None):
    """`rgb` (rows bottom first; sRGB for a colour) and any `alpha` as a PNG in
    TEXTURES, loaded back from the file so the GLB carries the file's own
    bytes."""
    import numpy as np
    os.makedirs(TEXTURES, exist_ok=True)
    path = os.path.abspath(os.path.join(TEXTURES, f"{name}.png"))
    for old in [i for i in bpy.data.images if i.name == name or bpy.path.abspath(i.filepath) == path]:
        bpy.data.images.remove(old)
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=alpha is not None)
    if not colour_data:
        img.colorspace_settings.name = "Non-Color"
    a = np.ones((h, w, 1)) if alpha is None else alpha[..., None]
    rgba = np.concatenate((np.clip(rgb, 0.0, 1.0), a), axis=2).astype(np.float32)
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
    """The material's colour from `colour_img`, its relief from `normal_img`,
    clipped by the colour's alpha."""
    nt = mat.node_tree
    for node in [n for n in nt.nodes if n.name.startswith("kyt_")]:
        nt.nodes.remove(node)
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.name, tex.image, tex.location = "kyt_colour", colour_img, (-600, 300)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    # Alpha through Round is the clip the glTF exporter writes as alphaMode
    # MASK, cutoff 0.5 (`paint_canvas.py`'s); Godot imports it as alpha scissor.
    clip = nt.nodes.new("ShaderNodeMath")
    clip.name, clip.operation, clip.location = "kyt_clip", "ROUND", (-300, 300)
    nt.links.new(tex.outputs["Alpha"], clip.inputs[0])
    nt.links.new(clip.outputs[0], bsdf.inputs["Alpha"])
    mat.surface_render_method = "DITHERED"
    ntex = nt.nodes.new("ShaderNodeTexImage")
    ntex.name, ntex.image, ntex.location = "kyt_normal_image", normal_img, (-600, -200)
    relief = nt.nodes.new("ShaderNodeNormalMap")
    relief.name, relief.location = "kyt_normal", (-300, -200)
    nt.links.new(ntex.outputs["Color"], relief.inputs["Color"])
    nt.links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for kind in ("mature", "young"):
        blade = bpy.data.objects.get(f"blade_{kind}")
        if blade is None:
            continue
        mat, slot, faces, edges = leaf_parts(blade)
        leaf_verts = {i for p in faces for i in p.vertices}
        cos = [blade.data.vertices[i].co for i in leaf_verts]
        frame = (max(abs(c.x) for c in cos), min(c.y for c in cos), max(c.y for c in cos))
        lay_uvs(blade, slot, faces, frame)
        colour_img, normal_img = leaf_texture(kind, blade, mat, edges, frame)
        wear(mat, colour_img, normal_img)
        red = bpy.data.materials.get(RED[mat.name])
        if red is not None:
            red_img, _ = leaf_texture(kind, blade, red, edges, frame, "red_")
            wear(red, red_img, normal_img)
            print(f"elephant_ear_leaves: {red_img.filepath} on {red.name}")
        print(f"elephant_ear_leaves: blade_{kind}: {len(faces)} leaf faces, {len(edges)} edges round it, "
              f"{frame[0] * 2:.2f} by {frame[2] - frame[1]:.2f} m, "
              f"{LEAF_TEX[1] * (1 - 2 * UV_MARGIN) / (frame[2] - frame[1]):.0f} px/m along; "
              f"{colour_img.filepath}, {normal_img.filepath} on {mat.name}")
    if "--no-save" not in argv:
        bpy.ops.wm.save_mainfile()
        print("elephant_ear_leaves: saved")


if __name__ == "__main__":
    main()
