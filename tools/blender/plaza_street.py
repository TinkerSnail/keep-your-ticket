"""The plaza's street furniture, a first pass from the catalog notes
(2026-10-02): the queue stanchion, the bollard, the park lamp and the cafe
table set. None of them has a reference photograph yet; each is the plainest
faithful reading of its catalog line and its greybox, at real scale, in the
house style, for Christina to reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<prop>.blend --python tools/blender/plaza_street.py -- \\
        [--replace] [--save] [--render <folder>]

`<prop>` is `queue_stanchion` (PRP-PARK-014), `bollard` (PRP-PARK-015),
`park_lamp` (PRP-LITE-001) or `cafe_table_set` (PRP-PARK-013). The tool builds
whichever the file is named for into `export`, one object a part, on z = 0 at
the origin facing -Y here (+Z in Godot). It refuses while `export` holds
anything (it may be hers) unless `--replace`; it writes the file only with
`--save`; `--render` shoots three-quarter, front, side and top views and one
beside a 1.7 m box for scale into the folder (saved first, so the render's
camera, sun and ground never reach the file).

**Queue stanchion.** The plaza's `stanchion_0..4` are 1.0 m posts 0.12 m
across, 1.4 m apart, with a straight rope box 0.05 m square at 0.80 m between
each pair (`gen_props.gd`, `_queue`). Two variants, tagged `kyt_variant`, stand
at the origin together: `post`, a weighted round base, a 60 mm post, a brass
collar carrying four rope rings and a ball top, 1.0 m tall;
and `rope`, one span as long as the plaza's post spacing, running along Y here
(the maquette's ropes run along Godot Z, unrotated): a ferrule and an open
snap hook at each end, hooked round the bottom bar of the facing ring, sagging
to the maquette's 0.80 m at mid-span. The rope does not collide
(`kyt_collision = none`), as the maquette's did not. Assumed: a ball-top
four-way stanchion with velvet rope, the common park kind; no bolts, since a
real one shows none.

**Bollard.** `bollard_n_0..4` are 0.9 m cylinders 0.26 m across. One cast
post 0.22 m across with a flared foot, a band 1.6 heads wide under a domed
cap, standing on a round surface plate with four anchor bolts (the one place
a real bolt shows). Assumed: a surface-mounted removable bollard rather than
one set in the paving.

**Park lamp.** The greybox is a 4.2 m pole 0.18 m across with a 0.5 m head
box centred at 4.13 m; the scene's light `lamp_0_pool` sits at 3.98 m and
stays in Godot. A small family (Christina, 2 Oct 2026: "we want more than
one"), three `kyt_variant`s sharing one bolted plate: `globe`, the plaza's
plain standard, a cast bell base, tapered pole, cup fitter and a globe 0.50 m
across centred on the light, 4.23 m to its top; `acorn`, from her second
photograph as the lead described it, a slim pole on a plain ring foot (the
base is provisional until she says how it differs), a collar, and a post-top
head 0.75 m tall and 0.35 m across, a dark neck, teardrop glass widest just
under a crown cap, and a pointed finial, 4.47 m to the tip, its light at
4.05 m in the glass; and `pier`, from her photograph
`documentation/reference/park_lamp/pier_gooseneck_lamp.png`, a tall dark
pole with a shepherd's-crook arm and a curl at the turn, a wide shallow bell
shade hanging 0.84 m out lit from beneath (light 4.66 m), and a blank banner on two
banded arms on the far side, 5.96 m to the crook's apex; the photo's small
box on the pole is left out. Each variant is complete: the plate and its
bolts are built once for `globe` and the others get linked copies (one mesh
each, so reshaping one reshapes all), the way the kits duplicate pieces, and
Send writes one set per variant. The acorn's and pier's parts stand in
`export/variant_acorn` and `variant_pier`, hidden in the viewport (click
their eyes), as the oak's b and c do.

**Cafe table set.** The greybox is a 1.2 m round top at 0.78 m on a post, an
umbrella pole and an open 3.0 m canopy disc at 2.3 m, with two pedestal
chairs at `ParkPlan.CAFE_CHAIRS`, (0.95, 0.2) and (-0.9, -0.35) from the
table in Godot's x and z. Built: the top 1.2 m across with a thick rounded
edge at 0.76 m on a weighted pedestal, the umbrella pole through it to an
eight-panel domed canopy 3.0 m across (rim 2.15 m, hub 2.55 m) with ribs and
a finial, and two bent-tube chairs at those offsets, each a one-piece tube
frame, a rounded seat whose top is at 0.51 m (`guest.gd` `seat_height`) and a
curved back, the seat and back bolted to the frame where a real one is.
Assumed: both chairs face the table. The generator turns each chair by the
table's theta plus 30 or 60 degrees, which puts chair_00's back to the table;
that reads as a formula rather than a pose, so it was not copied. The chairs'
offsets are world-axis in the generator (not turned with the table's theta):
place the set with no yaw to match the maquette. The chair greybox
(`reference/cafe_chair_greybox.glb`) is imported into `reference` at the
maquette's two places and yaws, tagged `kyt_reference_import`, for comparison.
The canopy, its ribs and hub do not collide: nothing reaches them.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, every edge rounded over, few big pieces. Fixings are the family bolt
(`family_bolt.py`), and the sizes it sets: posts one head wide, bands 1.6
heads. No colour here: the materials are flat stand-ins by surface (painted
metal, brass, rope, glass, table top, fabric, seat) for the painting to replace.
"""

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_bolt  # noqa: E402

TAU = math.tau
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
HEAD = family_bolt.HEAD      # 35 mm, the family bolt's head
POST = family_bolt.POST      # a post carrying a line of bolts: one head wide
BAND = family_bolt.BAND      # a band: 1.6 heads wide

# colours are stand-ins for the painting
PAINT = (0.05, 0.17, 0.11, 1.0)      # painted cast and tube metal, a park green
BRASS = (0.62, 0.48, 0.18, 1.0)      # brass accents: the stanchion's cap and rings, the bollard's band
ROPE = (0.42, 0.04, 0.07, 1.0)       # velvet rope
GLASS = (0.95, 0.94, 0.88, 1.0)      # the lamp's globe
TOP = (0.88, 0.87, 0.82, 1.0)        # the cafe table's top
FABRIC = (0.70, 0.12, 0.10, 1.0)     # the umbrella's canopy
SEAT = (0.80, 0.78, 0.72, 1.0)       # the chairs' seat and back
BANNER = (0.55, 0.12, 0.14, 1.0)     # the pier lamp's banner, blank until painted

BEVEL = 0.012


# --- building blocks -------------------------------------------------------

def material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = colour
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
        mat.diffuse_color = colour
    return mat


def export():
    return bpy.data.collections["export"]


def layer_collection(name, root=None):
    """The view layer's entry for a collection, whose `hide_viewport` is its eye."""
    root = root or bpy.context.view_layer.layer_collection
    if root.name == name:
        return root
    for child in root.children:
        found = layer_collection(name, child)
        if found:
            return found
    return None


def new_object(name, bm, mat, *, bevel=BEVEL, angle=35.0, segments=3, smooth=True, smooth_deg=40.0,
               unwrap=None, variant=None, collide=True):
    """Finish a bmesh into an object in `export`, with its bevel applied."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    export().objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.harden_normals = False
        apply_modifiers(obj)
    if smooth:
        smooth_by_angle(obj, smooth_deg)
    if unwrap:
        obj["kyt_unwrap"] = unwrap
    if variant:
        obj["kyt_variant"] = variant
    if not collide:
        obj["kyt_collision"] = "none"
    return obj


def apply_modifiers(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    # Slot by slot, never `materials.clear()`: in Blender 5 clearing resets every
    # face's material index to 0, so a two-material part comes out all one
    # (the sky ride gondola's tub, 2026-10-02). The evaluated mesh keeps the
    # object's slots; only fill them if it came back without any.
    if len(new.materials) == 0:
        for m in old.materials:
            new.materials.append(m)
    bpy.data.meshes.remove(old)


def smooth_by_angle(obj, deg=40.0):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(deg))
    bm.to_mesh(mesh)
    bm.free()


def prism(poly, axis, lo, hi):
    """A 2D polygon extruded along an axis: `poly` is (a, b) pairs, the plane's
    two axes in X, Y, Z order with `axis` left out ('x' gives (y, z), 'y' gives
    (x, z), 'z' gives (x, y))."""
    bm = bmesh.new()

    def at(a, b, t):
        if axis == "x":
            return (t, a, b)
        if axis == "y":
            return (a, t, b)
        return (a, b, t)

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    n = len(poly)
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return bm


def cylinder_bm(axis, centre, radius, lo, hi, sides=32):
    poly = [(centre[0] + radius * math.cos(TAU * i / sides),
             centre[1] + radius * math.sin(TAU * i / sides)) for i in range(sides)]
    return prism(poly, axis, lo, hi)


def rounded_rect(hx, hy, r, per=6):
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def lathe(profile, sides=32):
    """An (r, z) outline revolved about Z, bottom to top. A point with r = 0 is
    a pole; a first or last point with r > 0 gets a flat cap."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(TAU * i / sides), r * math.sin(TAU * i / sides), z))
                          for i in range(sides)])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(sides):
            j = (i + 1) % sides
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return bm


def arc(cx, cz, r, a0, a1, n):
    """Points of a circle in an (r, z) profile, from angle a0 to a1 (degrees)."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def band_profile(r_in, r_out, z0, z1, c=0.006):
    """A ring on a post for `lathe`, its outer edges chamfered so it needs no
    bevel: (r, z) from inside the post, out, up and back in."""
    return [(r_in, z0), (r_out - c, z0), (r_out, z0 + c), (r_out, z1 - c), (r_out - c, z1), (r_in, z1)]


def sphere_profile(r, zc, n=12):
    return [(r * math.sin(math.pi * i / n), zc - r * math.cos(math.pi * i / n)) for i in range(n + 1)]


def torus_bm(R, r, major=16, minor=8):
    """A ring in the XY plane about the origin, R to the bar's centre, bar radius r."""
    bm = bmesh.new()
    rings = []
    for i in range(major):
        u = TAU * i / major
        rings.append([bm.verts.new(((R + r * math.cos(v)) * math.cos(u), (R + r * math.cos(v)) * math.sin(u),
                                    r * math.sin(v))) for v in (TAU * j / minor for j in range(minor))])
    for i in range(major):
        a, b = rings[i], rings[(i + 1) % major]
        for j in range(minor):
            k = (j + 1) % minor
            bm.faces.new((a[j], a[k], b[k], b[j]))
    return bm


def fillet(points, radius, segs=4):
    """A polyline with each inside corner rounded to an arc of `radius` (one
    number, or one per corner)."""
    pts = [Vector(p) for p in points]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p, a, b = pts[i], pts[i - 1], pts[i + 1]
        r = radius[i - 1] if isinstance(radius, (list, tuple)) else radius
        d1, d2 = (a - p).normalized(), (b - p).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if r <= 0 or ang > math.radians(179.0):
            out.append(p)
            continue
        t = r / math.tan(ang / 2)
        c = p + (d1 + d2).normalized() * (r / math.sin(ang / 2))
        v0, v1 = p + d1 * t - c, p + d2 * t - c
        axis = v0.cross(v1)
        if axis.length < 1e-9:
            out.append(p)
            continue
        axis.normalize()
        total = v0.angle(v1)
        for s in range(segs + 1):
            out.append(c + Matrix.Rotation(total * s / segs, 3, axis) @ v0)
    out.append(pts[-1])
    return out


def tube_along(points, radius, sides=10, caps=True):
    """A round tube swept along a polyline, its frame carried along so it
    never twists; flat caps at both ends."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        t = pts[1] - pts[0] if i == 0 else pts[-1] - pts[-2] if i == n - 1 else pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i > 0:
            nrm = tangents[i - 1].rotation_difference(tangents[i]) @ nrm
            nrm = (nrm - tangents[i] * nrm.dot(tangents[i])).normalized()
        bin_ = tangents[i].cross(nrm).normalized()
        rings.append([bm.verts.new(pts[i] + radius * (math.cos(TAU * k / sides) * nrm + math.sin(TAU * k / sides) * bin_))
                      for k in range(sides)])
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            j = (k + 1) % sides
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return bm


def join(bms):
    """Several bmeshes as one (a welded tube frame is one part)."""
    out = bmesh.new()
    for bm in bms:
        me = bpy.data.meshes.new("_join")
        bm.to_mesh(me)
        bm.free()
        out.from_mesh(me)
        bpy.data.meshes.remove(me)
    return out


def move(bm, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return bm


# --- the queue stanchion -------------------------------------------------------
#
# The plaza's posts (`_queue` in gen_props.gd): 1.0 m tall, 1.4 m apart, the
# rope's middle at 0.80 m. The rope hooks the ring that faces the next post,
# round that ring's bottom bar, so the clip height follows the ring.

S_PITCH = 1.4                 # post spacing, hut.y - 2.8 .. hut.y + 2.8 in 1.4 m steps
S_HEIGHT = 1.0
S_BASE_R, S_BASE_H = 0.17, 0.085
S_POST_R = 0.03               # the post: chunkier than the bolt rule's one head, as a stanchion is
S_COLLAR_R = 0.038            # slim under the ball, so the ball reads as the top
S_COLLAR_Z0, S_COLLAR_Z1 = 0.86, 0.93
S_BALL_R = 0.05               # the ball top, its top the post's 1.0 m
S_HOOK_Z = 0.90               # the rings' centres
S_RING_R, S_RING_T = 0.020, 0.007   # ring radius to the bar's centre, and the bar
S_RING_C = S_COLLAR_R + S_RING_T - 0.004   # the ring's plane, sunk 4 mm into the collar
S_ROPE_R = 0.0225
S_ROPE_LOW = 0.80             # the maquette's rope height at mid-span
S_HOOK_T, S_HOOK_A = 0.008, 0.020   # the snap hook's bar, and its bend round the ring's bar
S_FERRULE_R, S_FERRULE_L = 0.028, 0.075
S_STEM = 0.035                # the hook's straight stem out of the ferrule
Z_ARC = S_HOOK_Z - S_RING_R   # the ring's bottom bar, which the hook wraps
Z_STEM = Z_ARC - S_HOOK_A     # the stem's and the ferrule's axis
Y_BAR = S_PITCH / 2 - S_RING_C   # that bar's distance from mid-span


def build_stanchion():
    paint = material("street_paint", PAINT)
    brass = material("street_brass", BRASS)
    rope = material("street_rope", ROPE)

    # the post: base, post, the ring collar, four rings, a ball top
    base = [(S_BASE_R, 0.0), (S_BASE_R, 0.03), (0.16, 0.05), (0.13, 0.068), (0.09, 0.08),
            (0.05, S_BASE_H), (S_POST_R - 0.002, S_BASE_H)]
    new_object("base", lathe(base, 24), paint, bevel=0.015, segments=2, unwrap="lathe", variant="post")
    new_object("post", cylinder_bm("z", (0, 0), S_POST_R, 0.06, S_COLLAR_Z0 + 0.01, 16), paint,
               bevel=0, unwrap="lathe", variant="post")
    collar = [(S_POST_R - 0.002, S_COLLAR_Z0), (S_COLLAR_R, S_COLLAR_Z0), (S_COLLAR_R, S_COLLAR_Z1),
              (S_POST_R - 0.002, S_COLLAR_Z1)]
    new_object("collar", lathe(collar, 24), brass, bevel=0.008, segments=2, unwrap="lathe", variant="post")
    new_object("cap", lathe(sphere_profile(S_BALL_R, S_HEIGHT - S_BALL_R, 10), 20), brass, bevel=0,
               unwrap="lathe", variant="post")
    rings = []
    for k in range(4):
        th = TAU * k / 4
        # a vertical ring, its plane tangent to the collar, its axis radial
        m = Matrix.Translation((S_RING_C * math.cos(th), S_RING_C * math.sin(th), S_HOOK_Z)) \
            @ Vector((0, 0, 1)).rotation_difference(Vector((math.cos(th), math.sin(th), 0))).to_matrix().to_4x4()
        rings.append(move(torus_bm(S_RING_R, S_RING_T, 12, 6), m))
    new_object("rings", join(rings), brass, bevel=0, smooth_deg=65, variant="post")

    # the rope: a span between the two facing rings, with a ferrule and an open
    # snap hook at each end
    y_mouth = Y_BAR - S_STEM - S_FERRULE_L
    sag = Z_STEM - S_ROPE_LOW
    path = [(0, -(y_mouth + S_FERRULE_L / 2), Z_STEM)]
    path += [(0, y, Z_STEM - sag * (1 - (y / y_mouth) ** 2))
             for y in (-y_mouth + 2 * y_mouth * i / 20 for i in range(21))]
    path += [(0, y_mouth + S_FERRULE_L / 2, Z_STEM)]
    new_object("rope", tube_along(path, S_ROPE_R, 10), rope, bevel=0, smooth_deg=60, variant="rope", collide=False)
    for tag, s in (("f", -1.0), ("b", 1.0)):
        y0, y1 = s * y_mouth, s * (y_mouth + S_FERRULE_L)
        new_object(f"ferrule_{tag}", cylinder_bm("y", (0, Z_STEM), S_FERRULE_R, min(y0, y1), max(y0, y1), 12),
                   brass, bevel=0.006, segments=2, variant="rope", collide=False)
        # the hook: a stem, then a bend round the ring's bottom bar, open at the top
        hook = [Vector((0, y1 - s * 0.004, Z_STEM))]
        for i in range(11):
            a = math.radians(-90.0 + 280.0 * i / 10)
            hook.append(Vector((0, s * Y_BAR + s * S_HOOK_A * math.cos(a), Z_ARC + S_HOOK_A * math.sin(a))))
        new_object(f"hook_{tag}", tube_along(hook, S_HOOK_T, 8), brass, bevel=0, smooth_deg=60,
                   variant="rope", collide=False)


def checks_stanchion():
    return [
        f"post {2 * S_BASE_R:.2f} m across the base, {S_HEIGHT:.2f} m tall, post {2 * S_POST_R * 1000:.0f} mm across",
        f"rings at {S_HOOK_Z:.2f} m; the rope clips at {Z_STEM:.3f} m and sags to {S_ROPE_LOW:.2f} m, "
        f"span {S_PITCH:.1f} m between post centres (the plaza's spacing)",
    ]


# --- the bollard ---------------------------------------------------------------

B_HEIGHT = 0.90
B_PLATE_R, B_PLATE_T = 0.18, 0.03
B_FOOT_R, B_SHAFT_R = 0.13, 0.11
B_BAND_Z = 0.66
B_BOLT_R = 0.155


def build_bollard():
    paint = material("street_paint", PAINT)
    brass = material("street_brass", BRASS)
    plate = new_object("plate", lathe([(B_PLATE_R, 0.0), (B_PLATE_R, B_PLATE_T)], 24), paint,
                       bevel=0.01, segments=2, unwrap="lathe")
    post = [(B_FOOT_R, 0.02), (B_FOOT_R, 0.10), (B_SHAFT_R, 0.14), (B_SHAFT_R, 0.78), (0.10, 0.80)]
    post += arc(0.0, 0.80, B_HEIGHT - 0.80, 15.0, 90.0, 5)
    new_object("post", lathe(post, 24), paint, bevel=0.012, segments=2, unwrap="lathe")
    new_object("band", lathe([(B_SHAFT_R - 0.005, B_BAND_Z), (B_SHAFT_R + 0.012, B_BAND_Z),
                              (B_SHAFT_R + 0.012, B_BAND_Z + BAND), (B_SHAFT_R - 0.005, B_BAND_Z + BAND)], 24),
               brass, bevel=0.006, segments=2, unwrap="lathe")
    bolts = family_bolt.paint_of(paint)
    for k in range(4):
        th = math.radians(45.0 + 90.0 * k)
        family_bolt.place(export(), f"bolt_{k}", Vector((B_BOLT_R * math.cos(th), B_BOLT_R * math.sin(th), B_PLATE_T)),
                          (0, 0, 1), ground=True, against=[plate], material=bolts)


def checks_bollard():
    return [f"plate {2 * B_PLATE_R:.2f} m across, shaft {2 * B_SHAFT_R:.2f} m, {B_HEIGHT:.2f} m tall; "
            f"band {BAND * 1000:.0f} mm wide (1.6 heads) at {B_BAND_Z:.2f} m"]


# --- the park lamp -------------------------------------------------------------

L_PLATE_R, L_PLATE_T = 0.24, 0.03
L_BOLT_R = 0.205
L_LIGHT_Z = 3.98              # the OmniLight lamp_0_pool, which stays in Godot: the globe's centre
L_VARIANTS = ("globe", "acorn", "pier")

# globe: the plaza's plain standard
L_POLE_R0, L_POLE_R1 = 0.066, 0.050
L_POLE_Z1 = 3.50
L_GLOBE_R = 0.25

# acorn (her second photograph, as the lead described it; the base is
# provisional until she says how it differs): a slim black pole on a plain
# round foot with a ring, a collar a short way below a post-top head about
# 0.75 m tall and 0.35 m across: a dark neck, teardrop glass widest just under
# a crown cap, and a pointed finial
A_POLE_R = 0.045
A_COLLAR_Z = 3.45
A_NECK_Z = 3.72               # where the glass meets the pole
A_GLASS_R, A_GIRTH_Z = 0.175, 4.12
A_LIGHT_Z = 4.05              # in the glass body, between its mid-height and its girth
A_TIP_Z = 4.47

# pier (her photograph, documentation/reference/park_lamp/pier_gooseneck_lamp.png):
# a tall dark pole, a shepherd's-crook arm with a curl at the turn, a bell
# lantern hanging from its end lit from beneath, and a banner on two short
# arms on the side away from the sweep. Sized so the banner is a standard 24
# by 54 in pole banner (0.6 by 1.36 m), which puts the pole top at 5.5 m and
# the person in the photo, further down the pier, at about 1.7 m; the railing
# hides the lowest 1.1 m, so the foot is assumed to stand on the deck's plate.
P_POLE_R = 0.07
P_TOP = 5.5                   # the straight pole's top, where the crook leaves it
P_CROOK_R = 0.42              # the crook's radius: it reaches 2 R out to the hanger
P_ARM_R = 0.035
P_HANGER_Z = 5.05             # the crook's leg ends here; the lantern hangs from it
P_BELL_R = 0.30               # the bell's rim radius: a wide, shallow shade, as the photo's
P_BELL_RIM_Z, P_BELL_TOP_Z = 4.60, 4.95
P_LIGHT_Z = 4.66              # the bulb, just inside the rim
P_BANNER_W, P_BANNER_Z0, P_BANNER_Z1 = 0.60, 2.61, 3.99
P_ARM_Z = (2.60, 4.00)        # the banner's two arms


def build_lamp():
    paint = material("street_paint", PAINT)
    glass = material("street_glass", GLASS)
    banner = material("street_banner", BANNER)
    bolts = family_bolt.paint_of(paint)

    # shared by the family: the plate and its anchor bolts, built once for
    # `globe`; the others get linked copies below (one mesh each: reshape one
    # and all follow), the way the kits duplicate pieces
    plate = new_object("plate", lathe([(L_PLATE_R, 0.0), (L_PLATE_R, L_PLATE_T)], 24), paint,
                       bevel=0.01, segments=2, unwrap="lathe", variant="globe")
    shared = [plate]
    for k in range(4):
        th = math.radians(45.0 + 90.0 * k)
        bolt = family_bolt.place(export(), f"bolt_{k}", Vector((L_BOLT_R * math.cos(th), L_BOLT_R * math.sin(th), L_PLATE_T)),
                                 (0, 0, 1), ground=True, against=[plate], material=bolts)
        bolt["kyt_variant"] = "globe"
        shared.append(bolt)

    # globe: cast bell base, tapered pole, cup fitter, a plain sphere centred on the light
    base = [(0.17, 0.02), (0.17, 0.10), (0.155, 0.16), (0.12, 0.26), (0.105, 0.40), (0.105, 0.52),
            (0.085, 0.58), (0.075, 0.64), (0.075, 0.72), (0.06, 0.72)]
    new_object("base", lathe(base, 24), paint, bevel=0.012, segments=2, unwrap="lathe", variant="globe")
    # the pole's ends are buried in the base and the fitter: no bevel
    new_object("pole", lathe([(L_POLE_R0, 0.70), (L_POLE_R1, L_POLE_Z1)], 16), paint, bevel=0,
               unwrap="lathe", variant="globe")
    fitter = [(0.049, L_POLE_Z1 - 0.03), (0.075, L_POLE_Z1 - 0.03), (0.075, 3.55), (0.10, 3.64),
              (0.16, 3.72), (0.19, 3.78), (0.19, 3.81), (0.15, 3.81)]
    new_object("fitter", lathe(fitter, 24), paint, bevel=0.01, segments=2, unwrap="lathe", variant="globe")
    new_object("globe", lathe(sphere_profile(L_GLOBE_R, L_LIGHT_Z, 12), 24), glass, bevel=0, unwrap="lathe", variant="globe")

    # acorn: ring foot (provisional), slim pole, collar, neck, teardrop glass, crown, finial
    # (these small turned parts carry their rounding in their outlines: no bevel)
    r = A_POLE_R - 0.003
    new_object("acorn_foot", lathe([(0.10, 0.02), (0.10, 0.12), (0.095, 0.15), (0.08, 0.18), (0.055, 0.20), (r, 0.20)], 20), paint,
               bevel=0, unwrap="lathe", variant="acorn")
    new_object("acorn_ring", lathe(band_profile(r, 0.062, 0.28, 0.34), 20), paint, bevel=0, unwrap="lathe", variant="acorn")
    new_object("acorn_pole", cylinder_bm("z", (0, 0), A_POLE_R, 0.18, A_NECK_Z + 0.02, 16), paint, bevel=0,
               unwrap="lathe", variant="acorn")
    new_object("acorn_collar", lathe(band_profile(r, 0.062, A_COLLAR_Z, A_COLLAR_Z + 0.05), 20), paint, bevel=0,
               unwrap="lathe", variant="acorn")
    neck = [(r, A_NECK_Z - 0.04), (0.07, A_NECK_Z - 0.02), (0.075, A_NECK_Z + 0.02), (0.06, A_NECK_Z + 0.05), (0.045, A_NECK_Z + 0.07)]
    new_object("acorn_neck", lathe(neck, 20), paint, bevel=0, unwrap="lathe", variant="acorn")
    body = [(0.0, A_NECK_Z + 0.03), (0.05, A_NECK_Z + 0.08), (0.09, 3.86), (0.13, 3.95), (0.16, 4.04),
            (A_GLASS_R, A_GIRTH_Z), (0.165, 4.18), (0.14, 4.22), (0.115, 4.24)]
    new_object("acorn", lathe(body, 20), glass, bevel=0, unwrap="lathe", variant="acorn")
    crown = [(0.11, 4.22), (0.18, 4.225), (0.19, 4.235), (0.185, 4.25), (0.16, 4.27), (0.12, 4.29), (0.08, 4.31),
             (0.05, 4.33), (0.04, 4.35)]
    new_object("acorn_cap", lathe(crown, 20), paint, bevel=0, unwrap="lathe", variant="acorn")
    finial = [(0.036, 4.34), (0.045, 4.355), (0.04, 4.375), (0.025, 4.41), (0.012, 4.44), (0.0, A_TIP_Z)]
    new_object("acorn_finial", lathe(finial, 16), paint, bevel=0, unwrap="lathe", variant="acorn")

    # pier: foot collar, pole with a domed top, the crook and its curl, the
    # hollow bell with its bulb, two banded banner arms, a blank banner
    r = P_POLE_R - 0.003
    new_object("pier_foot", lathe([(0.10, 0.02), (0.10, 0.18), (0.095, 0.22), (0.085, 0.25), (r, 0.27)], 20), paint,
               bevel=0, unwrap="lathe", variant="pier")
    new_object("pier_pole", cylinder_bm("z", (0, 0), P_POLE_R, 0.18, P_TOP, 16), paint, bevel=0, unwrap="lathe", variant="pier")
    new_object("pier_pole_cap", lathe([(r, P_TOP - 0.01), (0.078, P_TOP)] + arc(0.0, P_TOP, 0.078, 15.0, 90.0, 5), 20), paint,
               bevel=0, unwrap="lathe", variant="pier")
    crook = [Vector((0, 0, P_TOP - 0.12))]
    for i in range(13):   # up out of the pole, over the top, and down the far side
        a = math.radians(180.0 - 180.0 * i / 12)
        crook.append(Vector((P_CROOK_R + P_CROOK_R * math.cos(a), 0, P_TOP + P_CROOK_R * math.sin(a))))
    crook.append(Vector((2 * P_CROOK_R, 0, P_HANGER_Z)))
    new_object("pier_arm", tube_along(crook, P_ARM_R, 8), paint, bevel=0, smooth_deg=60, variant="pier")
    curl = []
    for i in range(21):   # the curl at the turn: from the crook's inner side, in and round 1.25 turns
        t = i / 20
        th = math.radians(90.0 - 450.0 * t)
        rr = 0.17 - 0.13 * t
        curl.append(Vector((P_CROOK_R + rr * math.cos(th), 0, P_TOP + 0.20 + rr * math.sin(th))))
    new_object("pier_curl", tube_along(curl, 0.018, 6), paint, bevel=0, smooth_deg=70, variant="pier")
    out = Matrix.Translation((2 * P_CROOK_R, 0, 0))
    # the shade: a hanger stem, a small collar, a rounded shoulder flaring to a
    # wide rim, and the inside surface back up to the top: a hollow bell
    bell = [(0.02, P_HANGER_Z + 0.03), (0.02, P_BELL_TOP_Z + 0.02), (0.05, P_BELL_TOP_Z), (0.10, 4.93), (0.17, 4.87),
            (0.23, 4.79), (0.27, 4.70), (0.295, 4.63), (P_BELL_R, P_BELL_RIM_Z), (P_BELL_R, P_BELL_RIM_Z - 0.015),
            (0.27, P_BELL_RIM_Z - 0.01), (0.235, 4.67), (0.185, 4.76), (0.12, 4.83), (0.06, 4.875), (0.0, 4.885)]
    new_object("pier_lantern", move(lathe(bell, 20), out), paint, bevel=0, unwrap="lathe", variant="pier")
    new_object("pier_bulb", move(lathe(sphere_profile(0.055, P_LIGHT_Z, 8), 12), out), glass, bevel=0, unwrap="lathe", variant="pier")
    for z, tag in zip(P_ARM_Z, ("bottom", "top")):
        band = new_object(f"pier_band_{tag}", lathe(band_profile(r, 0.086, z - BAND / 2, z + BAND / 2), 20),
                          paint, bevel=0, unwrap="lathe", variant="pier")
        new_object(f"pier_banner_arm_{tag}", tube_along([(-0.05, 0, z), (-(P_BANNER_W + 0.06), 0, z)], 0.016, 8), paint,
                   bevel=0, smooth_deg=60, variant="pier")
        bolt = family_bolt.place(export(), f"pier_bolt_band_{tag}", Vector((0, -0.086, z)), (0, -1, 0), against=[band], material=bolts)
        bolt["kyt_variant"] = "pier"
    slab = prism(rounded_rect(P_BANNER_W / 2, (P_BANNER_Z1 - P_BANNER_Z0) / 2, 0.02, 3), "y", -0.008, 0.008)
    move(slab, Matrix.Translation((-(0.06 + P_BANNER_W / 2), 0, (P_BANNER_Z0 + P_BANNER_Z1) / 2)))
    new_object("pier_banner", slab, banner, bevel=0.004, segments=1, unwrap="planar", variant="pier", collide=False)

    # the shared plate and bolts for the other two, and each variant's own
    # collection with its eye shut, standing at the origin with the globe's,
    # as the oak's b and c do
    for v in L_VARIANTS[1:]:
        for src in shared:
            dup = src.copy()  # shares its mesh
            dup.name = f"{src.name}_{v}"
            dup["kyt_variant"] = v
            export().objects.link(dup)
        sub = bpy.data.collections.new(f"variant_{v}")
        export().children.link(sub)
        for o in [o for o in export().objects if o.get("kyt_variant") == v]:
            export().objects.unlink(o)
            sub.objects.link(o)
    bpy.context.view_layer.update()
    for v in L_VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True


def checks_lamp():
    return [f"globe: light {L_LIGHT_Z:.2f} m (lamp_0_pool), globe {2 * L_GLOBE_R:.2f} m across centred on it, "
            f"top {L_LIGHT_Z + L_GLOBE_R:.2f} m; bell base, pole {2 * L_POLE_R0 * 1000:.0f} to {2 * L_POLE_R1 * 1000:.0f} mm",
            f"acorn: light {A_LIGHT_Z:.2f} m in the glass (body {A_NECK_Z + 0.03:.2f}..4.24 m, girth {A_GIRTH_Z:.2f} m, "
            f"{2 * A_GLASS_R:.2f} m across), tip {A_TIP_Z:.2f} m; pole {2 * A_POLE_R * 1000:.0f} mm on a provisional ring foot",
            f"pier: light {P_LIGHT_Z:.2f} m, the bulb under the bell (rim {P_BELL_RIM_Z:.2f} m, {2 * P_BELL_R:.2f} m across) "
            f"hanging {2 * P_CROOK_R:.2f} m out; pole top {P_TOP:.1f} m, crook apex {P_TOP + P_CROOK_R + P_ARM_R:.2f} m; "
            f"banner {P_BANNER_W:.2f} by {P_BANNER_Z1 - P_BANNER_Z0:.2f} m at {P_BANNER_Z0:.2f}..{P_BANNER_Z1:.2f} m; "
            f"sized to a 24 by 54 in banner, the foot assumed on the deck's plate",
            f"plate {2 * L_PLATE_R:.2f} m across, shared with its bolts as linked copies per variant"]


# --- the cafe table set ----------------------------------------------------------
#
# The chairs' places are ParkPlan.CAFE_CHAIRS, Godot (x, z) -> Blender (x, -z).
# Each chair is built facing -Y at the origin and turned to face the table.

C_TOP_R, C_TOP_Z, C_TOP_T = 0.60, 0.76, 0.05
C_UMB_R, C_HUB_Z, C_RIM_Z = 1.50, 2.55, 2.15
C_SEAT_Z, C_SEAT_T, C_SEAT_H = 0.51, 0.04, 0.21   # seat top: guest.gd seat_height
C_TUBE_R = POST / 2
C_RAIL_Z = C_SEAT_Z - C_SEAT_T - C_TUBE_R + 0.003   # the rails sunk 3 mm into the seat
C_LEG_X, C_FRONT_Y, C_BACK_Y = 0.19, -0.17, 0.19
C_POST_TOP = (0.235, 0.90)    # the back posts' top: (y, z), leaning back a little
C_BACK_Z, C_BACK_HZ, C_BACK_HX, C_BACK_T = 0.78, 0.10, 0.215, 0.03
CHAIRS = [(0.95, -0.20), (-0.90, 0.35)]
CHAIRS_MAQUETTE_YAW = [45.0, 75.0]   # the generator's: table theta 15 + 30 (j + 1)


def canopy_z(r):
    return C_HUB_Z - (C_HUB_Z - C_RIM_Z) * (r / C_UMB_R) ** 1.6


def chair_yaw(x, y):
    """The yaw (about Z) that turns a chair built facing -Y toward the origin."""
    f = -Vector((x, y)).normalized()
    return math.atan2(f.x, -f.y)


def build_chair(j, x, y):
    paint = material("cafe_paint", PAINT)
    seat_mat = material("cafe_seat", SEAT)
    m = Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(chair_yaw(x, y), 4, "Z")
    lx, fy, by, rz = C_LEG_X, C_FRONT_Y, C_BACK_Y, C_RAIL_Z
    ty, tz = C_POST_TOP
    tubes = []
    # the front hoop: leg, rail across under the seat's front, leg
    tubes.append(tube_along(fillet([(-lx, fy, 0), (-lx, fy, rz), (lx, fy, rz), (lx, fy, 0)], 0.05, 3), C_TUBE_R, 8))
    # the back hoop: leg, post, the back's top rail, post, leg
    tubes.append(tube_along(fillet([(-lx, by, 0), (-lx, by, rz), (-lx, ty, tz), (lx, ty, tz), (lx, by, rz), (lx, by, 0)],
                                   [0.04, 0.07, 0.07, 0.04], 3), C_TUBE_R, 8))
    # the side rails, joining the hoops under the seat
    for sx in (-1.0, 1.0):
        tubes.append(tube_along([(sx * lx, fy + 0.02, rz), (sx * lx, by - 0.02, rz)], C_TUBE_R, 8))
    new_object(f"chair_{j}_frame", move(join(tubes), m), paint, bevel=0, smooth_deg=60)
    seat = new_object(f"chair_{j}_seat", move(prism(rounded_rect(C_SEAT_H, C_SEAT_H, 0.06, 4), "z", C_SEAT_Z - C_SEAT_T, C_SEAT_Z), m),
                      seat_mat, bevel=0.012, segments=2, unwrap="facets")
    back = prism(rounded_rect(C_BACK_HX, C_BACK_HZ, 0.04, 4), "y", ty - C_TUBE_R - C_BACK_T + 0.002, ty - C_TUBE_R + 0.002)
    for v in back.verts:   # bowed: its middle 3 cm further back than its ends
        v.co.z += C_BACK_Z
        v.co.y += 0.03 * (1.0 - (v.co.x / C_BACK_HX) ** 2)
    back = new_object(f"chair_{j}_back", move(back, m), seat_mat, bevel=0.01, segments=2, unwrap="facets")
    bolts = family_bolt.paint_of(seat_mat)
    up, fwd = m.to_3x3() @ Vector((0, 0, 1)), m.to_3x3() @ Vector((0, -1, 0))
    for sx, tag in ((-1.0, "l"), (1.0, "r")):
        for yy, where in ((fy + 0.07, "front"), (by - 0.07, "back")):
            family_bolt.place(export(), f"chair_{j}_bolt_seat_{tag}_{where}", m @ Vector((sx * lx, yy, C_SEAT_Z)), up,
                              against=[seat], material=bolts)
        family_bolt.place(export(), f"chair_{j}_bolt_back_{tag}", m @ Vector((sx * lx, ty - C_TUBE_R - C_BACK_T, C_BACK_Z)),
                          fwd, against=[back], material=bolts)


def build_cafe():
    paint = material("cafe_paint", PAINT)
    top = material("cafe_top", TOP)
    fabric = material("cafe_fabric", FABRIC)

    # the table: a thick rounded top on a weighted pedestal
    new_object("top", cylinder_bm("z", (0, 0), C_TOP_R, C_TOP_Z - C_TOP_T, C_TOP_Z, 36), top, bevel=0.02, unwrap="lathe")
    pedestal = [(0.30, 0.0), (0.30, 0.03), (0.22, 0.07), (0.10, 0.10), (0.06, 0.16), (0.06, 0.66),
                (0.085, 0.70), (0.085, C_TOP_Z - C_TOP_T + 0.005)]
    new_object("pedestal", lathe(pedestal, 24), paint, bevel=0.012, segments=2, unwrap="lathe")

    # the umbrella: pole, eight-panel domed canopy, ribs under its seams, hub and
    # finial; the pole's ends are buried in the pedestal and the hub
    new_object("umbrella_pole", cylinder_bm("z", (0, 0), 0.03, 0.60, C_HUB_Z - 0.03, 12), paint, bevel=0, unwrap="lathe")
    radii = (0.06, 0.55, 1.05, C_UMB_R)
    bm = bmesh.new()
    sheets = []
    for dz in (0.0, -0.012):
        rings = [[bm.verts.new((r * math.cos(TAU * k / 8), r * math.sin(TAU * k / 8), canopy_z(r) + dz)) for k in range(8)]
                 for r in radii]
        bm.faces.new(rings[0])
        for a, b in zip(rings, rings[1:]):
            for k in range(8):
                bm.faces.new((a[k], a[(k + 1) % 8], b[(k + 1) % 8], b[k]))
        sheets.append(rings[-1])
    for k in range(8):
        bm.faces.new((sheets[0][k], sheets[0][(k + 1) % 8], sheets[1][(k + 1) % 8], sheets[1][k]))
    new_object("canopy", bm, fabric, bevel=0.006, segments=2, smooth_deg=70, collide=False)
    ribs = []
    for k in range(8):
        th = TAU * k / 8
        path = [(r * math.cos(th), r * math.sin(th), canopy_z(r) - 0.012 - 0.012) for r in (0.05, 0.5, 1.0, C_UMB_R - 0.02)]
        ribs.append(tube_along(path, 0.012, 6))
    new_object("ribs", join(ribs), paint, bevel=0, smooth_deg=70, collide=False)
    hub = [(0.05, C_HUB_Z - 0.05), (0.05, C_HUB_Z + 0.035), (0.03, C_HUB_Z + 0.05), (0.038, C_HUB_Z + 0.065),
           (0.04, C_HUB_Z + 0.08), (0.035, C_HUB_Z + 0.10), (0.02, C_HUB_Z + 0.115), (0.0, C_HUB_Z + 0.12)]
    new_object("hub", lathe(hub, 16), paint, bevel=0.006, segments=2, unwrap="lathe", collide=False)

    for j, (x, y) in enumerate(CHAIRS):
        build_chair(j, x, y)
    import_chair_reference()


def import_chair_reference():
    """The chair greybox at the maquette's two places and yaws, into the locked
    `reference` collection, once."""
    ref = bpy.data.collections["reference"]
    if any(o.get("kyt_chair_reference") for o in ref.objects):
        return
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    glb = os.path.join(root, "assets", "source", "props", "reference", "cafe_chair_greybox.glb")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]
    # the three greybox parts, their places in the chair's frame, and their
    # bare names (the set's own reference already has a greybox_post)
    parts = [(o, o.matrix_world.copy(), o.name.split("greybox_")[-1].split(".")[0])
             for o in new if o.type == "MESH" and not o.name.startswith("floor")]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
    for o, _, _ in parts:
        o.parent = None
    for o in new:
        if all(o is not p for p, _, _ in parts):
            bpy.data.objects.remove(o, do_unlink=True)
    for j, ((x, y), yaw) in enumerate(zip(CHAIRS, CHAIRS_MAQUETTE_YAW)):
        m = Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
        for src, local, base in parts:
            o = src if j == 0 else src.copy()   # shares its mesh
            o.name = f"greybox_chair_{j}_{base}"
            o["kyt_reference_import"] = True
            o["kyt_chair_reference"] = True
            ref.objects.link(o)
            o.matrix_world = m @ local


def checks_cafe():
    out = [f"top {2 * C_TOP_R:.2f} m across at {C_TOP_Z:.2f} m, {C_TOP_Z - C_TOP_T:.2f} m under it; pedestal 0.60 m across",
           f"canopy {2 * C_UMB_R:.1f} m across, rim {C_RIM_Z:.2f} m, hub {C_HUB_Z:.2f} m, finial {C_HUB_Z + 0.12:.2f} m",
           f"seat tops {C_SEAT_Z:.2f} m (guest.gd seat_height), back top {C_POST_TOP[1]:.2f} m, tubes {2 * C_TUBE_R * 1000:.0f} mm"]
    for j, (x, y) in enumerate(CHAIRS):
        out.append(f"chair_{j} at ({x:+.2f}, {y:+.2f}) here = Godot ({x:+.2f}, {-y:+.2f}), {math.hypot(x, y):.2f} m from the "
                   f"table's centre, facing it (yaw {math.degrees(chair_yaw(x, y)):.1f} deg; the maquette's {CHAIRS_MAQUETTE_YAW[j]:.0f})")
    return out


# --- the file ----------------------------------------------------------------

ALTERNATIVES = ("park_lamp",)   # props whose variants are alternative silhouettes


def bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            w = o.matrix_world @ v.co
            lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
        ev.to_mesh_clear()
    return lo, hi


def triangles(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
        ev.to_mesh_clear()
    return n


def side_by_side(left, right, out, height=900):
    """Her photograph beside the render, both brought to one height."""
    def pixels(path):
        img = bpy.data.images.load(path, check_existing=True)
        w, h = img.size
        arr = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(arr)
        return arr.reshape(h, w, 4)

    def fit(arr):
        h, w = arr.shape[:2]
        nw = max(1, round(w * height / h))
        ys = (np.arange(height) * h / height).astype(int)
        xs = (np.arange(nw) * w / nw).astype(int)
        return arr[ys][:, xs]

    a, b = fit(pixels(left)), fit(pixels(right))
    a[..., 3] = 1.0
    b[..., 3] = 1.0
    canvas = np.concatenate([a, np.ones((height, 16, 4), dtype=np.float32), b], axis=1)
    img = bpy.data.images.new("side_by_side", canvas.shape[1], height, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(canvas).ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    print("rendered", out)


def render(folder, name):
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    try:
        scene.eevee.taa_render_samples = 24
    except AttributeError:
        pass
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.72, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    ground = bpy.data.objects.new("ground", bpy.data.meshes.new("ground"))
    bm = prism([(-40, -40), (40, -40), (40, 40), (-40, 40)], "z", -0.02, -0.001)
    bm.to_mesh(ground.data)
    bm.free()
    ground.data.materials.append(material("render_ground", (0.50, 0.48, 0.44, 1)))
    stage.objects.link(ground)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.4
    sun.rotation_euler = (math.radians(50), math.radians(12), math.radians(40))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    stage.objects.link(cam)
    scene.camera = cam

    parts = [o for o in export().all_objects if o.type == "MESH"]
    variants = sorted({str(o.get("kyt_variant", "")) for o in parts})
    by_variant = {v: [o for o in parts if str(o.get("kyt_variant", "")) == v] for v in variants}
    first = by_variant[variants[0]]
    others = [o for o in parts if o not in first]
    # variants that are alternative silhouettes (the lamp's globe and acorn)
    # are each shown in full; a prop whose variants are its pieces (the
    # stanchion's post and rope) shows its first, as the handback tool does
    alternatives = name in ALTERNATIVES

    def only(objs):
        for o in parts:
            o.hide_render = o not in objs

    def points(objs):
        dg = bpy.context.evaluated_depsgraph_get()
        pts = []
        for o in objs:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            pts += [o.matrix_world @ v.co for v in me.vertices]
            ev.to_mesh_clear()
        return pts

    def shoot(tag, objs, direction, target=None, lens=40):
        """The camera along `direction` from the objects' centre, backed off
        until every vertex is in frame."""
        pts = points(objs)
        lo = Vector(map(min, *pts)) if len(pts) > 1 else pts[0]
        hi = Vector(map(max, *pts)) if len(pts) > 1 else pts[0]
        centre = (lo + hi) / 2 if target is None else Vector(target)
        d = Vector(direction).normalized()
        dist = max((hi - lo).length * 0.9, 0.5)
        cam.data.lens = lens
        for _ in range(60):
            cam.location = centre + d * dist
            cam.location.z = max(cam.location.z, 0.12)
            look = centre - cam.location
            cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            if all(0.04 <= c.x <= 0.96 and 0.04 <= c.y <= 0.96 for c in (world_to_camera_view(scene, cam, p) for p in pts)):
                break
            dist *= 1.08
        scene.render.filepath = os.path.join(folder, f"{name}_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)

    shown = [(v, by_variant[v]) for v in variants] if alternatives else [("", first)]
    for v, objs in shown:
        only(objs)
        tag = f"{v}_" if v else ""
        shoot(f"{tag}three_quarter", objs, (-0.75, -1.0, 0.55))
        shoot(f"{tag}front", objs, (0.0, -1.0, 0.18))
        shoot(f"{tag}side", objs, (1.0, 0.0, 0.18))
        shoot(f"{tag}top", objs, (0.0, -0.001, 1.0))
    # beside a 1.7 m tall box, a guest's height; alternatives stand in a row
    box = new_object("scale_box", prism(rounded_rect(0.225, 0.14, 0.03), "z", 0.0, 1.7), material("render_box", (0.35, 0.35, 0.38, 1)), bevel=0)
    export().objects.unlink(box)
    stage.objects.link(box)
    if alternatives:
        only([])
        row, x = [], 0.0
        for v, objs in shown:   # side by side, half a metre apart
            lo, hi = bounds(objs)
            for o in objs:
                c = o.copy()
                c.location.x += x - lo.x
                c.hide_render = False
                stage.objects.link(c)
                row.append(c)
            x += hi.x - lo.x + 0.5
        box.location = (x + 0.225, 0.0, 0.0)
        shoot("scale", row + [box], (-0.6, -1.0, 0.35))
        for c in row:
            c.hide_render = True
    else:
        lo, hi = bounds(first)
        box.location = (hi.x + 0.45 + 0.225, 0.0, 0.0)
        shoot("scale", first + [box], (-0.6, -1.0, 0.35))
    box.hide_render = True
    if name == "queue_stanchion":
        # the span: two posts the plaza's pitch apart, with the rope between
        only(others)
        copies = []
        for s in (-1.0, 1.0):
            for o in first:
                c = o.copy()
                c.location.y += s * S_PITCH / 2
                c.hide_render = False
                stage.objects.link(c)
                copies.append(c)
        shoot("span", copies + others, (-1.0, -0.7, 0.45))
    if name == "cafe_table_set":
        only(first)
        chair = [o for o in first if o.name.startswith("chair_0_")]
        shoot("chair", chair, (-0.9, -1.0, 0.5), lens=50)
    if name == "park_lamp" and "pier" in by_variant:
        # her photograph's standpoint: on the beach near deck height, the
        # banner toward us and the arm sweeping to the right, sky behind
        only(by_variant["pier"])
        ground.hide_render = True
        shoot("pier_photo_angle", by_variant["pier"], (-0.5, -1.0, -0.33), target=(0.15, 0.0, 3.1), lens=35)
        ground.hide_render = False
        photo = os.path.join(ROOT, "documentation", "reference", "park_lamp", "pier_gooseneck_lamp.png")
        if os.path.exists(photo):
            side_by_side(photo, os.path.join(folder, f"{name}_pier_photo_angle.png"),
                         os.path.join(folder, f"{name}_pier_vs_photo.png"))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    builders = {"queue_stanchion": (build_stanchion, checks_stanchion),
                "bollard": (build_bollard, checks_bollard),
                "park_lamp": (build_lamp, checks_lamp),
                "cafe_table_set": (build_cafe, checks_cafe)}
    if name not in builders:
        raise SystemExit(f"plaza_street: open one of {', '.join(builders)}, not {name}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"plaza_street: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for child in list(coll.children):   # a variant's own collection
            bpy.data.collections.remove(child)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    build, check = builders[name]
    build()
    parts = [o for o in coll.all_objects if o.type == "MESH"]
    variants = sorted({str(o.get("kyt_variant", "")) for o in parts})
    print(f"plaza_street: {name}: {len(parts)} parts, {triangles(parts)} triangles")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts if not o.get(family_bolt.TAG))
          + f"; bolts {sum(triangles([o]) for o in parts if o.get(family_bolt.TAG))}")
    for v in variants:
        group = [o for o in parts if str(o.get("kyt_variant", "")) == v]
        lo, hi = bounds(group)
        label = f"variant {v}" if v else "size"
        print(f"  {label}: {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x D x H), "
              f"z {lo.z:.3f}..{hi.z:.3f}, {len(group)} parts, {triangles(group)} triangles")
    for line in check():
        print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
