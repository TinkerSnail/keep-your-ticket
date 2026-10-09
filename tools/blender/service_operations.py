"""The service and operations group, first pass from the catalog notes
(2026-10-02): the funhouse entry turnstile, the funhouse operator box, the
staff service door, the pier's fish-cleaning sink, tackle cart, rod rack and
cleanup bin, and the folded stock cart with its empty crate. None has a
reference photograph; each is a plain reading of its catalog line and of the
authored composition in `scenes/world/boardwalk_operations.tscn` (exported into
each file's `reference` collection), at real scale, for Christina to review
and reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<prop>.blend --python tools/blender/service_operations.py -- \
        [--replace] [--save] [--render <folder>]

`<prop>` is `funhouse_turnstile` (PRP-OPS-009), `funhouse_operator_box`
(PRP-OPS-010), `service_door` (PRP-OPS-011), `fish_cleaning_sink`
(PRP-OPS-012), `tackle_cart` (PRP-OPS-013), `rod_rack` (PRP-OPS-014),
`cleanup_bin` (PRP-OPS-015) or `folded_stock_cart` (PRP-OPS-016). The tool
builds whichever the file is named for into `export`, one object a part, on
z = 0 at the origin facing -Y here (+Z in Godot). It refuses while `export`
holds anything (it may be hers) unless `--replace`; it writes the file only
with `--save`; `--render <folder>` shoots a three-quarter, front, side and
top view and one beside a 1.7 m box for scale, after any save, so nothing the
render adds reaches the file. Parts are tagged for `unwrap_parts.py`
(`kyt_unwrap`): `facets` for bevelled and cut boxes and for turned parts on a
horizontal axis, `lathe` for turned parts standing upright (their object
origin on their axis, as that layout needs), nothing for a straight or bent
tube, which the unwrapper reads as a cylinder on its own.

**Axes.** The maquette export keeps the composition's world axes, so the P2
pieces (turnstile, operator box, service door), which face Godot's -X in the
funhouse front, arrive in `reference` facing -X here. They are built facing
-Y, the prop convention, a quarter turn from their reference. The pier pieces
already face -Y (the sink's back board toward +Y) and the tackle cart keeps
the greybox's frame (wheels toward -X, handle toward +X).

**Funhouse turnstile.** Greybox: a 0.22 m post 1.55 m tall and one 1.0 by 0.1 m
arm at 1.23 m reaching out of the entry. Built: a round pedestal with four
anchor bolts and a collar, the 1.55 m post with a domed cap, a drum hub at
waist height (0.98 m) and three arms of 50 mm tube with ball ends at 120
degrees, one toward -Y (the approach), each 1.0 m from the axis as the
greybox's arm was. The post stands on the origin (the greybox's stands 0.445 m
off it, the export having centred post and arm together).

**Funhouse operator box.** Greybox: a 1.0 by 1.25 m box 1.48 m tall, a 1.0 by
0.72 m panel 0.06 m proud of the face toward the entry from 0.61 to 1.33 m,
and a 0.13 m red ball on it. Built: a kick plinth, a rounded cabinet 1.25 m
across the front and 1.0 m deep with a lipped cap at 1.48 m, the panel on the
front face with four bolts, and the show stop as a yellow collar and a red
mushroom head 0.13 m across where the ball was (0.2 m left of centre, 1.09 m
up). The panel is blank: its controls are paint.

**Service door.** Greybox: a 2.2 by 4.35 m slab 0.08 m thick with STAFF across
its middle. Built: a steel frame (0.12 m jambs, 0.14 m head) standing 0.07 m
proud of the wall plane y = 0, its feet on z = 0, two leaves 4.19 m tall in
it, a kick plate and a pull bar of 42 mm tube on each, and a blank notice
plate 0.42 by 0.30 m with four bolts on the right leaf at 1.65 m (eye level;
the greybox's label sat at 2.3 m, the slab's middle). Everything lies on the
public side of the wall plane; nothing is buried in the wall.

**Fish-cleaning sink.** Greybox: a 2.45 by 1.05 m cabinet 1.35 m tall, a basin
on top of it, a 2.65 m back board to 2.085 m, a faucet post and a cutting
board. Built as the catalog's station on legs: four 7 cm legs, the back two
rising to 2.0 m to carry the back board (bolted to them), a 2.45 by 1.05 m
counter at 0.98 m with a 2.12 by 0.78 m trough let into it (floor at 0.76 m,
a drain and a drain pipe to the deck), a gooseneck faucet with a lever at the
back, and a 0.52 by 0.72 m cutting board lying across the trough at its right
end. The work height is the pass's: the greybox's 1.35 m counter was chest
high. The sign on the back board is paint.

**Tackle cart.** Greybox: a 2.1 by 1.0 m body from 0.07 to 0.99 m under a
2.2 by 1.1 m lid, a handle bar out of the +X end at 0.69 m, two 0.42 m wheels
at the -X end. Built: a rounded chest on the greybox's footprint with a lipped
lid at 1.08 m, two spoked-disc wheels with rubber tyres on an axle through
the chest's bottom at x = -0.98, two stub legs with pads under the handle
end, a U handle of 42 mm tube welded on at two bosses, and on the lid what
makes its job legible, a tackle box with a carry handle and a bait cooler;
nothing branded. The catalog calls the cart small; the composition's size is
kept.

**Rod rack.** Greybox: a 0.72 by 0.3 m rack 3.0 m tall and three 4 m rods
0.08 m thick standing through it. Built: a timber rack of two 10 cm posts on a
foot board, two rails with holes the rods stand through, bolted at their ends,
and three rods (3.7, 4.0 and 3.85 m, grip, blank, two guides and a spinning
reel each), chunky enough to read at 4 m. The rods stand upright inside the
rack 0.21 m apart (the greybox's straddled it 0.4 m apart).

**Cleanup bin.** Greybox: a 0.82 m drum 1.4 m tall and a 0.52 m bucket 0.72 m
tall beside it. Built: an open galvanised bin with a rolled rim and two swage
bands, and an open tapered bucket with two ears and a wire bail dropped down
its side, each where the greybox stood them.

**Folded stock cart.** No greybox: the scene's `S1_folded_cart` is a 0.35 by
1.25 m box 0.9 m tall at the S1 stock door and `S2_empty_crate` a 0.92 m
square box 0.72 m tall at S2. Built as two variants (`kyt_variant`) at the
origin: `cart`, a platform truck stood on its long edge and leaning 4 degrees
back as if against a wall (+Y), its underside toward -Y with two chassis rails
and four castors, the deck and the push handle folded flat over it on two
bolted pivots toward the wall; `crate`, an open timber crate on two skids with
four corner battens, its slats paint.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, every edge rounded over, few big pieces, the family bolt only where a
real one would show. No colour here: flat stand-in materials by surface for
the painting to replace.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_bolt  # noqa: E402

TAU = math.tau

# colours are stand-ins for the painting, one per kind of surface
PAINT_DARK = (0.16, 0.17, 0.19, 1.0)
PAINT_CREAM = (0.84, 0.80, 0.70, 1.0)
PAINT_TURQUOISE = (0.10, 0.42, 0.40, 1.0)
PAINT_CORAL = (0.63, 0.20, 0.14, 1.0)
PAINT_MUSTARD = (0.72, 0.47, 0.08, 1.0)
PAINT_GREY = (0.50, 0.54, 0.54, 1.0)
GALVANIZED = (0.58, 0.61, 0.61, 1.0)
DARK_METAL = (0.22, 0.24, 0.26, 1.0)
STEEL = (0.66, 0.68, 0.70, 1.0)
RUBBER = (0.07, 0.07, 0.07, 1.0)
TIMBER = (0.42, 0.28, 0.16, 1.0)
TIMBER_PALE = (0.70, 0.56, 0.36, 1.0)
SIGNAL_RED = (0.72, 0.08, 0.05, 1.0)
SIGNAL_YELLOW = (0.85, 0.65, 0.08, 1.0)
PLASTIC_WHITE = (0.88, 0.88, 0.86, 1.0)
PLASTIC_BLUE = (0.16, 0.30, 0.55, 1.0)
CORK = (0.72, 0.56, 0.36, 1.0)


# --- building blocks -------------------------------------------------------

def material(name, colour, roughness=0.85):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = roughness
        mat.diffuse_color = colour
    return mat


def export():
    return bpy.data.collections["export"]


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


def clean(obj):
    """Merge coincident vertices and drop faces with no area. A boolean and a
    bevel leave slivers; unwrap_parts.py works on a merged copy and needs the
    same faces in the same order, so a part must already be clean."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bad = [f for f in bm.faces if f.calc_area() < 1e-9]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


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


def new_object(name, bm, mat, *, bevel=0.0, segments=2, angle=35.0, smooth=True, smooth_deg=40.0,
               at=(0.0, 0.0, 0.0), unwrap="facets"):
    """Finish a bmesh into an object in `export`, with its bevel applied and
    cleaned. `at` is the object's origin: the bmesh is relative to it, so a
    turned part can keep its origin on its own axis."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    export().objects.link(obj)
    obj.data.materials.append(mat)
    obj.location = at
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.harden_normals = False
        apply_modifiers(obj)
    clean(obj)
    if smooth:
        smooth_by_angle(obj, smooth_deg)
    if unwrap:
        obj["kyt_unwrap"] = unwrap
    return obj


def cut(obj, cutters, mat):
    """Take `cutters` (bmeshes, relative to the object's origin) out of a
    finished part: a hole through a rail that is already rounded over, so the
    bevel does not run round every hole's rim."""
    for i, cb in enumerate(cutters):
        cmesh = bpy.data.meshes.new(f"{obj.name}_cut{i}")
        bmesh.ops.recalc_face_normals(cb, faces=cb.faces)
        cb.to_mesh(cmesh)
        cb.free()
        cmesh.materials.append(mat)
        cutter = bpy.data.objects.new(f"{obj.name}_cut{i}", cmesh)
        cutter.location = obj.location
        bpy.context.scene.collection.objects.link(cutter)
        mod = obj.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cutter
        mod.solver = "EXACT"
        apply_modifiers(obj)
        bpy.data.objects.remove(cutter)
        bpy.data.meshes.remove(cmesh)
    clean(obj)
    smooth_by_angle(obj)
    return obj


def subtract(base_bm, cutters, name, mat, *, bevel=0.0, segments=2, angle=35.0, smooth_deg=40.0,
             at=(0.0, 0.0, 0.0), unwrap="facets"):
    """Cut `cutters` (bmeshes, relative to `at` like the base) out of the shape
    `base_bm` and finish it, the bevel last, on the cut shape."""
    base = new_object(name, base_bm, mat, bevel=0, smooth=False, at=at, unwrap=None)
    cut(base, cutters, mat)
    if bevel:
        mod = base.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.harden_normals = False
        apply_modifiers(base)
    clean(base)
    smooth_by_angle(base, smooth_deg)
    if unwrap:
        base["kyt_unwrap"] = unwrap
    return base


def transform(objs, matrix):
    """Move the vertices of `objs` by `matrix`, keeping their objects where they are."""
    for o in objs:
        for v in o.data.vertices:
            v.co = matrix @ v.co
        o.data.update()


def settle(objs):
    """Lower (or raise) a set of parts together so their lowest vertex is on z = 0."""
    lo = bounds(objs)[0].z
    for o in objs:
        o.location.z -= lo


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


def box_bm(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def rounded_rect(hx, hy, r, per=4, cx=0.0, cy=0.0):
    pts = []
    for ax, ay, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + ax + r * math.cos(a), cy + ay + r * math.sin(a)))
    return pts


def circle(cx, cy, r, sides):
    return [(cx + r * math.cos(TAU * i / sides), cy + r * math.sin(TAU * i / sides)) for i in range(sides)]


def cylinder_bm(axis, centre, radius, lo, hi, sides=16):
    return prism(circle(centre[0], centre[1], radius, sides), axis, lo, hi)


def lathe_bm(profile, sides=16, axis="z", closed=False):
    """A profile of (radius, position along the axis) pairs revolved round the
    axis. An end point at radius 0 becomes the pole vertex; an end at a radius
    is capped with a disc. `closed` joins the last point back to the first (a
    band or a ring), with no caps."""
    bm = bmesh.new()

    def at(r, t, a):
        c, s = r * math.cos(a), r * math.sin(a)
        if axis == "z":
            return (c, s, t)
        if axis == "y":
            return (c, t, s)
        return (t, c, s)

    rings = []
    for r, t in profile:
        if abs(r) < 1e-9:
            rings.append([bm.verts.new(at(0.0, t, 0.0))])
        else:
            rings.append([bm.verts.new(at(r, t, TAU * i / sides)) for i in range(sides)])
    pairs = list(zip(rings, rings[1:]))
    if closed:
        pairs.append((rings[-1], rings[0]))
    for a, b in pairs:
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
    if not closed:
        if len(rings[0]) > 1:
            bm.faces.new(rings[0])
        if len(rings[-1]) > 1:
            bm.faces.new(list(reversed(rings[-1])))
    return bm


def sphere_profile(centre_t, radius, a0=-90.0, a1=90.0, step=30.0):
    """The (r, t) points of a ball from angle a0 to a1 (-90 is the bottom)."""
    pts = []
    a = a0
    while a < a1 - 1e-6:
        pts.append((radius * math.cos(math.radians(a)), centre_t + radius * math.sin(math.radians(a))))
        a += step
    pts.append((radius * math.cos(math.radians(a1)), centre_t + radius * math.sin(math.radians(a1))))
    return pts


def tube_bm(points, radius, sides=10, closed=False):
    """A round tube swept along a polyline, its rings turned with the path
    (parallel transport), capped at both ends; `closed` joins the last point
    back to the first instead (a loop), with no caps."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        if closed:
            t = (pts[(i + 1) % n] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        elif i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tangents.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    normal = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    bm = bmesh.new()
    rings = []
    for p, t in zip(pts, tangents):
        normal = (normal - t * normal.dot(t)).normalized()
        nn, b = normal, t.cross(normal)
        rings.append([bm.verts.new(p + (nn * math.cos(TAU * i / sides) + b * math.sin(TAU * i / sides)) * radius)
                      for i in range(sides)])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, c in pairs:
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((a[i], a[j], c[j], c[i]))
    if not closed:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    return bm


def rounded_path(points, r, per=3):
    """A polyline with each inner corner replaced by an arc of `per` segments."""
    pts = [Vector(p) for p in points]
    out = [pts[0]]
    for a, p, b in zip(pts, pts[1:], pts[2:]):
        u, w = (a - p).normalized(), (b - p).normalized()
        p0, p1 = p + u * r, p + w * r
        for k in range(per + 1):
            s = k / per
            out.append((1 - s) ** 2 * p0 + 2 * (1 - s) * s * p + s ** 2 * p1)
    out.append(pts[-1])
    return out


def tag(objs, **props):
    for o in objs:
        for k, v in props.items():
            o[k] = v


# --- the funhouse turnstile --------------------------------------------------
#
# The greybox post is 0.22 m across and 1.55 m tall with one 1.0 by 0.1 m arm
# at 1.23 m reaching out of the entry (toward -X in the funhouse front; -Y
# here). The post stands on the origin; the greybox's stands 0.445 m toward +X
# because the maquette export centred post and arm together. Three arms at
# 120 degrees about the post, one toward the approach, at waist height.

T_POST_R, T_POST_TOP = 0.11, 1.55
T_PED_R, T_PED_H = 0.27, 0.10
T_HUB_Z, T_HUB_R, T_HUB_H = 0.98, 0.17, 0.16
T_ARM_L, T_ARM_R, T_BALL_R = 1.0, 0.035, 0.055
T_ARM_ANGLES = (-90.0, 30.0, 150.0)


def build_turnstile():
    paint = material("turnstile_paint", PAINT_GREY, 0.6)
    dark = material("turnstile_dark", PAINT_DARK, 0.7)
    bolt_paint = family_bolt.paint_of(paint)

    # the pedestal: a round plinth, its underside recessed so it meets the deck
    # on its rim and not face to face, a chamfer, and a collar the post rises
    # from. The rounding is in the profile: a bevel on a lathe costs every ring
    collar_r = T_POST_R + 0.03
    ped = new_object("pedestal", lathe_bm([
        (0.0, 0.004), (T_PED_R - 0.03, 0.004), (T_PED_R, 0.0), (T_PED_R, T_PED_H - 0.03),
        (T_PED_R - 0.03, T_PED_H), (collar_r + 0.015, T_PED_H), (collar_r, T_PED_H + 0.015),
        (collar_r, T_PED_H + 0.05), (collar_r - 0.018, T_PED_H + 0.065), (0.0, T_PED_H + 0.065)], 20),
        paint, unwrap="lathe")
    for i in range(4):
        a = math.radians(45.0 + 90.0 * i)
        r = T_PED_R - 0.065
        family_bolt.place(export(), f"bolt_foot_{i}", Vector((r * math.cos(a), r * math.sin(a), T_PED_H)),
                          (0, 0, 1), ground=True, against=[ped], material=bolt_paint)

    # the post, with a domed cap
    new_object("post", lathe_bm([
        (0.0, T_PED_H + 0.04), (T_POST_R, T_PED_H + 0.04), (T_POST_R, T_POST_TOP - 0.05),
        (T_POST_R - 0.01, T_POST_TOP - 0.03), (0.075, T_POST_TOP - 0.01), (0.04, T_POST_TOP - 0.002),
        (0.0, T_POST_TOP)], 20), paint, unwrap="lathe")

    # the hub: a drum round the post at waist height
    z0, z1 = T_HUB_Z - T_HUB_H / 2, T_HUB_Z + T_HUB_H / 2
    new_object("hub", lathe_bm([
        (0.0, z0), (T_HUB_R - 0.02, z0), (T_HUB_R, z0 + 0.02), (T_HUB_R, z1 - 0.02),
        (T_HUB_R - 0.02, z1), (0.0, z1)], 20), dark, unwrap="lathe")

    # three arms with ball ends, from inside the hub to inside the ball
    for i, deg in enumerate(T_ARM_ANGLES):
        d = Vector((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0))
        new_object(f"arm_{i}", tube_bm([d * (T_HUB_R - 0.03) + Vector((0, 0, T_HUB_Z)),
                                        d * (T_ARM_L - 0.02) + Vector((0, 0, T_HUB_Z))], T_ARM_R, 12), dark, unwrap=None)
        new_object(f"arm_ball_{i}", lathe_bm(sphere_profile(0.0, T_BALL_R, -90.0, 90.0, 30.0), 12), dark,
                   at=(d.x * T_ARM_L, d.y * T_ARM_L, T_HUB_Z), unwrap="lathe", smooth_deg=70.0)


def checks_turnstile():
    return [
        f"post {2 * T_POST_R:.2f} m across, {T_POST_TOP:.2f} m tall on a {2 * T_PED_R:.2f} m pedestal with four anchor bolts",
        f"three arms {T_ARM_L:.2f} m from the axis at {T_HUB_Z:.2f} m, {T_ARM_R * 2000:.0f} mm tube with {T_BALL_R * 2000:.0f} mm "
        f"balls, one toward -Y; the hub {2 * T_HUB_R:.2f} m across",
        "the greybox's one arm was at 1.23 m, 1.0 m long; the post stands on the origin, not the greybox's x = +0.445",
    ]


# --- the funhouse operator box -----------------------------------------------
#
# The greybox box is 1.0 m (toward the entry) by 1.25 m and 1.48 m tall; its
# panel 0.06 m proud of the entry-side face, 1.0 m wide from 0.61 to 1.33 m;
# the show stop a 0.13 m ball on the panel 0.2 m to one side. Turned to face
# -Y: 1.25 m across the front, 1.0 m deep; the stop at x = -0.2.

O_X, O_Y = 0.625, 0.50
O_Z0, O_Z1, O_CAP_T = 0.08, 1.40, 0.08
O_PANEL_X, O_PANEL_Z0, O_PANEL_Z1, O_PANEL_T = 0.50, 0.61, 1.33, 0.06
O_STOP_X, O_STOP_Z = -0.20, 1.09


def build_operator_box():
    paint = material("opbox_paint", PAINT_DARK, 0.7)
    panel_paint = material("opbox_panel", PAINT_CREAM)
    red = material("opbox_stop", SIGNAL_RED, 0.4)
    yellow = material("opbox_collar", SIGNAL_YELLOW, 0.5)

    new_object("plinth", prism(rounded_rect(O_X - 0.04, O_Y - 0.04, 0.04), "z", 0.0, O_Z0 + 0.01), paint,
               bevel=0.01, segments=1)
    new_object("body", prism(rounded_rect(O_X, O_Y, 0.06), "z", O_Z0, O_Z1 + 0.01), paint, bevel=0.03)
    new_object("cap", prism(rounded_rect(O_X + 0.02, O_Y + 0.02, 0.07), "z", O_Z1, O_Z1 + O_CAP_T), paint, bevel=0.02)
    # the panel: a plate on the front face, set a centimetre into the body so
    # nothing shares its plane, with a bolt at each corner
    front = -O_Y - O_PANEL_T
    panel = new_object("panel", box_bm(-O_PANEL_X, O_PANEL_X, front, -O_Y + 0.01, O_PANEL_Z0, O_PANEL_Z1),
                       panel_paint, bevel=0.012)
    bolt_paint = family_bolt.paint_of(panel_paint)
    for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        x = sx * (O_PANEL_X - 0.07)
        z = O_PANEL_Z0 + 0.07 if sz < 0 else O_PANEL_Z1 - 0.07
        family_bolt.place(export(), f"bolt_panel_{i}", Vector((x, front, z)), (0, -1, 0), against=[panel],
                          material=bolt_paint)
    # the show stop: a yellow collar on the panel and the red mushroom head,
    # both turned on an axis pointing out of the panel (-Y)
    new_object("stop_collar", lathe_bm([
        (0.0, front + 0.005), (0.085, front + 0.005), (0.085, front - 0.03), (0.072, front - 0.04),
        (0.0, front - 0.04)], 16, "y"), yellow, at=(O_STOP_X, 0.0, O_STOP_Z), unwrap="facets")
    new_object("stop_button", lathe_bm([
        (0.0, front - 0.03), (0.036, front - 0.03), (0.036, front - 0.05), (0.06, front - 0.054),
        (0.065, front - 0.068), (0.055, front - 0.082), (0.03, front - 0.09), (0.0, front - 0.092)], 16, "y"),
        red, at=(O_STOP_X, 0.0, O_STOP_Z), unwrap="facets", smooth_deg=50.0)


def checks_operator_box():
    return [
        f"cabinet {2 * O_X:.2f} m across the front, {2 * O_Y:.2f} m deep, cap at {O_Z1 + O_CAP_T:.2f} m",
        f"panel {2 * O_PANEL_X:.2f} m wide from {O_PANEL_Z0:.2f} to {O_PANEL_Z1:.2f} m, {O_PANEL_T * 100:.0f} cm proud, four bolts",
        f"show stop {0.13:.2f} m across at x = {O_STOP_X:+.2f}, {O_STOP_Z:.2f} m up, on a yellow collar",
    ]


# --- the service door --------------------------------------------------------
#
# The greybox is a 2.2 by 4.35 m slab 0.08 m thick with STAFF on it. The wall
# plane is y = 0; the frame stands proud of it toward -Y, the leaves inside
# the frame, so nothing is buried in the building's wall.

D_W, D_H = 2.20, 4.35
D_JAMB, D_HEAD, D_DEPTH = 0.12, 0.14, 0.07
D_LEAF_T, D_LEAF_FRONT = 0.05, -0.055
D_PULL_Z0, D_PULL_Z1, D_PULL_X = 0.95, 1.55, 0.14
D_KICK_H = 0.30
D_NOTICE = (0.30, 0.72, 1.50, 1.80)     # x0, x1, z0, z1 on the right leaf


def build_service_door():
    frame_paint = material("door_frame", PAINT_DARK, 0.7)
    leaf_paint = material("door_leaf", PAINT_GREY, 0.7)
    steel = material("door_steel", STEEL, 0.4)
    notice_paint = material("door_notice", PLASTIC_WHITE, 0.5)
    bolt_paint = family_bolt.paint_of(notice_paint)

    hx, ix = D_W / 2, D_W / 2 - D_JAMB
    top = D_H - D_HEAD
    new_object("frame", prism([(-hx, 0.0), (-hx, D_H), (hx, D_H), (hx, 0.0), (ix, 0.0), (ix, top), (-ix, top), (-ix, 0.0)],
                              "y", -D_DEPTH, 0.0), frame_paint, bevel=0.02)
    y0, y1 = D_LEAF_FRONT, D_LEAF_FRONT + D_LEAF_T
    for side, sx in (("l", -1.0), ("r", 1.0)):
        x_in, x_out = sx * 0.01, sx * (ix - 0.005)
        x0, x1 = min(x_in, x_out), max(x_in, x_out)
        leaf = new_object(f"leaf_{side}", box_bm(x0, x1, y0, y1, 0.02, top - 0.02), leaf_paint, bevel=0.02)
        new_object(f"kick_{side}", box_bm(x0 + 0.04, x1 - 0.04, y0 - 0.008, y0 + 0.004, 0.04, 0.04 + D_KICK_H),
                   steel, bevel=0.003, segments=1)
        x = sx * D_PULL_X
        new_object(f"pull_{side}", tube_bm(rounded_path([(x, y0 + 0.005, D_PULL_Z0), (x, y0 - 0.085, D_PULL_Z0),
                                                         (x, y0 - 0.085, D_PULL_Z1), (x, y0 + 0.005, D_PULL_Z1)], 0.04),
                                           family_bolt.BAR / 2, 10), steel, unwrap=None)
    nx0, nx1, nz0, nz1 = D_NOTICE
    notice = new_object("notice", box_bm(nx0, nx1, y0 - 0.012, y0 + 0.004, nz0, nz1), notice_paint,
                        bevel=0.004, segments=1)
    for i, (x, z) in enumerate(((nx0 + 0.05, nz0 + 0.05), (nx1 - 0.05, nz0 + 0.05),
                                (nx0 + 0.05, nz1 - 0.05), (nx1 - 0.05, nz1 - 0.05))):
        family_bolt.place(export(), f"bolt_notice_{i}", Vector((x, y0 - 0.012, z)), (0, -1, 0), against=[notice],
                          material=bolt_paint)


def checks_service_door():
    return [
        f"frame {D_W:.2f} by {D_H:.2f} m, {D_DEPTH * 100:.0f} cm proud of the wall plane y = 0, feet on z = 0",
        f"two leaves {D_W / 2 - D_JAMB - 0.015:.2f} m wide and {D_H - D_HEAD - 0.04:.2f} m tall, {D_LEAF_T * 100:.0f} cm thick; "
        f"pulls of {family_bolt.BAR * 1000:.0f} mm tube from {D_PULL_Z0:.2f} to {D_PULL_Z1:.2f} m; kick plates {D_KICK_H:.2f} m",
        f"notice {D_NOTICE[1] - D_NOTICE[0]:.2f} by {D_NOTICE[3] - D_NOTICE[2]:.2f} m centred {(D_NOTICE[2] + D_NOTICE[3]) / 2:.2f} m up "
        "on the right leaf, four bolts; the greybox's label sat at 2.3 m",
    ]


# --- the fish-cleaning sink --------------------------------------------------
#
# The greybox cabinet is 2.45 by 1.05 m and 1.35 m tall, its basin 2.12 by
# 0.78 m on top, the back board 2.65 m wide to 2.085 m, the faucet post at
# x = -0.15 and the cutting board 0.72 by 0.52 m at x = +0.45. The counter
# here is centred on the origin in plan (the greybox's is 3 cm toward -Y, the
# export having centred counter and back board together).

S_X, S_Y = 1.225, 0.525
S_TOP, S_TOP_T = 0.98, 0.06
S_TUB_X, S_TUB_Y, S_TUB_WALL = 1.06, 0.39, 0.06
S_TUB_Z0, S_TUB_FLOOR = 0.70, 0.76
S_LEG = 0.09
S_LEG_X, S_LEG_Y = S_X - 0.13, S_Y - 0.13
S_POST_TOP = 2.0
S_BACK_X, S_BACK_T, S_BACK_Z0, S_BACK_Z1 = 1.325, 0.12, 0.90, 2.085
S_BACK_Y0 = S_LEG_Y + S_LEG / 2 - 0.005      # the back board's face, 5 mm into the back legs
S_FAUCET_X, S_FAUCET_Y = -0.15, 0.42
S_BOARD_X, S_BOARD_HX, S_BOARD_HY, S_BOARD_T = 0.45, 0.26, 0.36, 0.05


def build_fish_sink():
    steel = material("sink_steel", GALVANIZED, 0.45)
    fittings = material("sink_fittings", DARK_METAL, 0.4)
    paint = material("sink_paint", PAINT_CREAM)
    timber = material("sink_timber", TIMBER_PALE)

    # the counter with the trough let into it: the slab's hole is a centimetre
    # smaller than the trough's inside, so the slab laps the trough's wall top
    # and nothing shares a plane; the trough's rim top stops inside the slab
    hole_x, hole_y = S_TUB_X - S_TUB_WALL - 0.01, S_TUB_Y - S_TUB_WALL - 0.01
    subtract(prism(rounded_rect(S_X, S_Y, 0.08), "z", S_TOP - S_TOP_T, S_TOP),
             [prism(rounded_rect(hole_x, hole_y, 0.05), "z", S_TOP - S_TOP_T - 0.05, S_TOP + 0.05)],
             "counter", steel, bevel=0.015)
    subtract(prism(rounded_rect(S_TUB_X, S_TUB_Y, 0.08), "z", S_TUB_Z0, S_TOP - 0.005),
             [prism(rounded_rect(S_TUB_X - S_TUB_WALL, S_TUB_Y - S_TUB_WALL, 0.05), "z", S_TUB_FLOOR, S_TOP + 0.05)],
             "trough", steel, bevel=0.01)
    new_object("drain", lathe_bm([(0.0, S_TUB_FLOOR - 0.004), (0.05, S_TUB_FLOOR - 0.004), (0.05, S_TUB_FLOOR + 0.005),
                                  (0.04, S_TUB_FLOOR + 0.008), (0.0, S_TUB_FLOOR + 0.008)], 12), fittings, unwrap="lathe")
    new_object("drain_pipe", lathe_bm([(0.0, 0.0), (0.03, 0.0), (0.03, S_TUB_Z0 + 0.02), (0.0, S_TUB_Z0 + 0.02)], 12),
               fittings, unwrap=None)

    # four legs, the back two rising as posts for the back board; a stretcher
    # between front and back on each side
    legs = {}
    for sx, tx in ((-1.0, "l"), (1.0, "r")):
        for sy, ty in ((-1.0, "f"), (1.0, "b")):
            top = S_POST_TOP if sy > 0 else S_TOP - 0.03
            legs[(tx, ty)] = new_object(f"leg_{ty}{tx}", box_bm(sx * S_LEG_X - S_LEG / 2, sx * S_LEG_X + S_LEG / 2,
                                                                 sy * S_LEG_Y - S_LEG / 2, sy * S_LEG_Y + S_LEG / 2,
                                                                 0.0, top), steel, bevel=0.01, segments=1)
        new_object(f"stretcher_{tx}", box_bm(sx * S_LEG_X - 0.03, sx * S_LEG_X + 0.03, -S_LEG_Y, S_LEG_Y, 0.27, 0.33),
                   steel, bevel=0.008, segments=1)
    new_object("back_board", box_bm(-S_BACK_X, S_BACK_X, S_BACK_Y0, S_BACK_Y0 + S_BACK_T, S_BACK_Z0, S_BACK_Z1),
               paint, bevel=0.02)
    for tx, sx in (("l", -1.0), ("r", 1.0)):
        for k, z in (("lo", 1.25), ("hi", 1.90)):
            family_bolt.place(export(), f"bolt_post_{tx}_{k}", Vector((sx * S_LEG_X, S_LEG_Y - S_LEG / 2, z)), (0, -1, 0),
                              against=[legs[(tx, "b")]])

    # the faucet: a flange on the counter, a gooseneck of 48 mm pipe over the
    # trough, and a lever on its side
    fx, fy = S_FAUCET_X, S_FAUCET_Y
    new_object("faucet_base", lathe_bm([(0.0, S_TOP - 0.005), (0.05, S_TOP - 0.005), (0.05, S_TOP + 0.02),
                                        (0.035, S_TOP + 0.035), (0.0, S_TOP + 0.035)], 14), fittings,
               at=(fx, fy, 0.0), unwrap="lathe")
    new_object("faucet", tube_bm(rounded_path([(fx, fy, S_TOP), (fx, fy, 1.42), (fx, 0.08, 1.42), (fx, 0.08, 1.24)],
                                              0.10, 4), 0.024, 12), fittings, unwrap=None)
    new_object("faucet_lever", tube_bm([(fx + 0.015, fy, 1.07), (fx + 0.14, fy - 0.07, 1.11)], 0.012, 8), fittings,
               unwrap=None)
    new_object("faucet_knob", lathe_bm(sphere_profile(0.0, 0.024, -90.0, 90.0, 30.0), 10), fittings,
               at=(fx + 0.14, fy - 0.07, 1.11), unwrap="lathe", smooth_deg=70.0)

    # the cutting board, lying across the trough at its right end, 3 mm into
    # the counter so their tops are not one plane
    new_object("cutting_board", box_bm(S_BOARD_X - S_BOARD_HX, S_BOARD_X + S_BOARD_HX, -S_BOARD_HY, S_BOARD_HY,
                                       S_TOP - 0.003, S_TOP + S_BOARD_T), timber, bevel=0.012)
    # the back board's sign is paint


def checks_fish_sink():
    return [
        f"counter {2 * S_X:.2f} by {2 * S_Y:.2f} m at {S_TOP:.2f} m on {S_LEG * 100:.0f} cm legs; trough {2 * S_TUB_X:.2f} by "
        f"{2 * S_TUB_Y:.2f} m, floor at {S_TUB_FLOOR:.2f} m; the greybox's counter was at 1.35 m",
        f"back board {2 * S_BACK_X:.2f} m wide, top at {S_BACK_Z1:.3f} m, bolted to the back legs (four bolts)",
        f"faucet at x = {S_FAUCET_X:+.2f}, spout {1.42:.2f} m up; cutting board {2 * S_BOARD_HX:.2f} by {2 * S_BOARD_HY:.2f} m "
        f"at x = {S_BOARD_X:+.2f} across the trough",
    ]


# --- the tackle cart ---------------------------------------------------------
#
# The greybox body is 2.1 by 1.0 m from 0.07 to 0.99 m, its lid 2.2 by 1.1 m
# to 1.10 m, centred at x = -0.362 (the footprint, handle included, is centred
# on the origin); the handle bar reaches to x = +1.462 at 0.69 m; the wheels
# 0.42 m across at x = -0.982. The frame is kept: wheels toward -X.

C_X0 = -0.362
C_HX, C_HY = 1.05, 0.50
C_Z0, C_Z1, C_LID_T = 0.18, 0.98, 0.10
C_WHEEL_X, C_WHEEL_R, C_WHEEL_HW = -0.982, 0.21, 0.08
C_WHEEL_Y = C_HY + 0.03 + C_WHEEL_HW
C_HUB_R = 0.05
C_LEG_X = C_X0 + C_HX - 0.12
C_HANDLE_Z, C_HANDLE_END, C_HANDLE_HY = 0.69, 1.462, 0.30
C_BOX_X, C_COOLER_X = C_X0 - 0.55, C_X0 + 0.45


def build_tackle_cart():
    paint = material("tackle_paint", PAINT_TURQUOISE)
    lid_paint = material("tackle_lid_paint", PAINT_CREAM)
    metal = material("tackle_metal", DARK_METAL, 0.4)
    rubber = material("tackle_rubber", RUBBER, 0.95)
    box_plastic = material("tackle_box_plastic", PLASTIC_BLUE, 0.5)
    cooler_plastic = material("tackle_cooler_plastic", PLASTIC_WHITE, 0.5)
    top = C_Z1 + C_LID_T

    # the chest and its lipped lid
    new_object("body", prism(rounded_rect(C_HX, C_HY, 0.06, cx=C_X0), "z", C_Z0, C_Z1 + 0.01), paint, bevel=0.03)
    new_object("lid", prism(rounded_rect(C_HX + 0.05, C_HY + 0.05, 0.08, cx=C_X0), "z", C_Z1, top), lid_paint, bevel=0.02)

    # the axle through the chest's bottom, and a wheel each side: a rubber tyre
    # round a disc with a hub, the hub longer outward where the nut is
    hw = C_WHEEL_HW
    new_object("axle", tube_bm([(C_WHEEL_X, -C_WHEEL_Y - hw, C_WHEEL_R), (C_WHEEL_X, C_WHEEL_Y + hw, C_WHEEL_R)], 0.022, 12),
               metal, unwrap=None)
    for side, sy in (("l", -1.0), ("r", 1.0)):
        at = (C_WHEEL_X, sy * C_WHEEL_Y, C_WHEEL_R)
        new_object(f"wheel_{side}_tyre", lathe_bm([
            (C_WHEEL_R - 0.07, sy * hw), (C_WHEEL_R - 0.025, sy * hw), (C_WHEEL_R - 0.005, sy * hw * 0.6), (C_WHEEL_R, 0.0),
            (C_WHEEL_R - 0.005, -sy * hw * 0.6), (C_WHEEL_R - 0.025, -sy * hw), (C_WHEEL_R - 0.07, -sy * hw)],
            16, "y", closed=True), rubber, at=at, unwrap="facets")
        disc = new_object(f"wheel_{side}", lathe_bm([
            (0.0, sy * (hw + 0.03)), (C_HUB_R, sy * (hw + 0.03)), (C_HUB_R, sy * 0.012), (C_WHEEL_R - 0.065, sy * 0.012),
            (C_WHEEL_R - 0.065, -sy * 0.012), (C_HUB_R, -sy * 0.012), (C_HUB_R, -sy * (hw + 0.01)), (0.0, -sy * (hw + 0.01))],
            16, "y"), paint, at=at, unwrap="facets")
        family_bolt.place(export(), f"bolt_hub_{side}", Vector((C_WHEEL_X, sy * (C_WHEEL_Y + hw + 0.03), C_WHEEL_R)),
                          (0, sy, 0), against=[disc])

    # two stub legs with pads under the handle end
    for side, sy in (("l", -1.0), ("r", 1.0)):
        new_object(f"leg_{side}", box_bm(C_LEG_X - 0.03, C_LEG_X + 0.03, sy * 0.38 - 0.03, sy * 0.38 + 0.03, 0.015, C_Z0 + 0.01),
                   metal, bevel=0.006, segments=1)
        new_object(f"pad_{side}", box_bm(C_LEG_X - 0.055, C_LEG_X + 0.055, sy * 0.38 - 0.055, sy * 0.38 + 0.055, 0.0, 0.025),
                   rubber, bevel=0.006, segments=1)

    # the U handle out of the +X end, welded on at two round bosses (a welded
    # handle shows no bolts; the hub nuts are this cart's)
    xe = C_X0 + C_HX
    new_object("handle", tube_bm(rounded_path([(xe - 0.02, -C_HANDLE_HY, C_HANDLE_Z), (C_HANDLE_END, -C_HANDLE_HY, C_HANDLE_Z),
                                               (C_HANDLE_END, C_HANDLE_HY, C_HANDLE_Z), (xe - 0.02, C_HANDLE_HY, C_HANDLE_Z)], 0.08),
                                 family_bolt.BAR / 2, 10), metal, unwrap=None)
    for side, sy in (("l", -1.0), ("r", 1.0)):
        new_object(f"handle_boss_{side}", lathe_bm([(0.0, xe - 0.004), (0.05, xe - 0.004), (0.05, xe + 0.012),
                                                    (0.04, xe + 0.018), (0.0, xe + 0.018)], 12, "x"), paint,
                   at=(0.0, sy * C_HANDLE_HY, C_HANDLE_Z), unwrap="facets")

    # on the lid: a tackle box with its carry handle, and a bait cooler
    bx = C_BOX_X
    new_object("tackle_box", prism(rounded_rect(0.25, 0.14, 0.03, 2, cx=bx), "z", top - 0.005, 1.30), box_plastic,
               bevel=0.012, segments=1)
    new_object("tackle_box_lid", prism(rounded_rect(0.26, 0.15, 0.035, 2, cx=bx), "z", 1.29, 1.37), box_plastic,
               bevel=0.012, segments=1)
    new_object("tackle_box_handle", tube_bm(rounded_path([(bx - 0.10, 0.0, 1.355), (bx - 0.10, 0.0, 1.43),
                                                          (bx + 0.10, 0.0, 1.43), (bx + 0.10, 0.0, 1.355)], 0.03, 2), 0.012, 6),
               box_plastic, unwrap=None)
    cx = C_COOLER_X
    new_object("cooler", prism(rounded_rect(0.30, 0.20, 0.05, 3, cx=cx), "z", top - 0.005, 1.40), cooler_plastic, bevel=0.02)
    new_object("cooler_lid", prism(rounded_rect(0.315, 0.215, 0.06, 3, cx=cx), "z", 1.39, 1.47), cooler_plastic,
               bevel=0.02, segments=1)


def checks_tackle_cart():
    return [
        f"chest {2 * C_HX:.2f} by {2 * C_HY:.2f} m from {C_Z0:.2f} m up, lid at {C_Z1 + C_LID_T:.2f} m; wheels {2 * C_WHEEL_R:.2f} m "
        f"at x = {C_WHEEL_X:+.2f}, {2 * C_WHEEL_Y:.2f} m apart; legs at x = {C_LEG_X:+.2f}",
        f"handle {family_bolt.BAR * 1000:.0f} mm tube at {C_HANDLE_Z:.2f} m, {2 * C_HANDLE_HY:.2f} m wide, reaching x = {C_HANDLE_END:+.2f}",
        f"on the lid: tackle box 0.50 by 0.28 m to 1.43 m at x = {C_BOX_X:+.2f}, cooler 0.60 by 0.40 m to 1.47 m at x = {C_COOLER_X:+.2f}",
    ]


# --- the rod rack ------------------------------------------------------------
#
# The greybox rack is 0.72 by 0.3 m and 3.0 m tall, the three rods 4 m long
# and 0.08 m thick at x = -0.35, +0.05 and +0.45 (straddling the rack) and
# y = +0.1. Here the rods stand inside the rack, 0.21 m apart, through holes
# in its rails; the rack is centred on the origin.

R_POST_X, R_POST, R_POST_Y, R_H = 0.31, 0.10, 0.05, 3.0
R_BASE_HY, R_BASE_H = 0.15, 0.12
R_RAIL_Y0, R_RAIL_Y1, R_RAIL_H = -0.06, 0.14, 0.12
R_RAILS = (1.45, 2.80)
R_ROD_X, R_ROD_Y = (-0.21, 0.0, 0.21), 0.02
R_ROD_LEN = (3.70, 4.00, 3.85)
R_GUIDES = (1.6, 2.4)


def build_rod_rack():
    timber = material("rack_timber", TIMBER)
    blank = material("rod_blank", PAINT_DARK, 0.5)
    cork = material("rod_grip", CORK)
    reel = material("reel_metal", DARK_METAL, 0.4)

    hx = R_POST_X + R_POST / 2
    new_object("base", box_bm(-hx, hx, -R_BASE_HY, R_BASE_HY, 0.0, R_BASE_H), timber, bevel=0.015)
    for side, sx in (("l", -1.0), ("r", 1.0)):
        new_object(f"post_{side}", box_bm(sx * R_POST_X - R_POST / 2, sx * R_POST_X + R_POST / 2, R_POST_Y - R_POST / 2,
                                          R_POST_Y + R_POST / 2, R_BASE_H - 0.01, R_H), timber, bevel=0.012, segments=1)
    for i, zc in enumerate(R_RAILS):
        # rounded over first, the holes cut after, so the bevel stays off the
        # holes' rims (hidden under the rods, and a hundred triangles each)
        rail = new_object(f"rail_{i}", box_bm(-hx + 0.005, hx - 0.005, R_RAIL_Y0, R_RAIL_Y1, zc - R_RAIL_H / 2, zc + R_RAIL_H / 2),
                          timber, bevel=0.012, segments=1)
        cut(rail, [cylinder_bm("z", (rx, R_ROD_Y), 0.045, zc - 0.1, zc + 0.1, 10) for rx in R_ROD_X], timber)
        for side, sx in (("l", -1.0), ("r", 1.0)):
            family_bolt.place(export(), f"bolt_rail_{i}_{side}", Vector((sx * R_POST_X, R_RAIL_Y0, zc)), (0, -1, 0),
                              against=[rail])
    for k, (rx, length) in enumerate(zip(R_ROD_X, R_ROD_LEN)):
        at = (rx, R_ROD_Y, 0.0)
        # the rod: a cork grip with the reel seat, the blank tapering to the tip
        z0 = R_BASE_H
        new_object(f"rod_{k}_grip", lathe_bm([(0.0, z0), (0.022, z0), (0.027, z0 + 0.015), (0.027, z0 + 0.28), (0.031, z0 + 0.30),
                                              (0.031, z0 + 0.38), (0.027, z0 + 0.40), (0.027, z0 + 0.50), (0.0, z0 + 0.50)], 8),
                   cork, at=at, unwrap="lathe")
        tip = z0 + length
        new_object(f"rod_{k}_blank", lathe_bm([(0.0, z0 + 0.48), (0.022, z0 + 0.48), (0.019, z0 + 1.4), (0.015, tip * 0.72),
                                               (0.011, tip - 0.03), (0.011, tip), (0.0, tip)], 8), blank, at=at, unwrap="lathe")
        for g, gz in enumerate(R_GUIDES):
            yc = R_ROD_Y - 0.016 - 0.026
            ring = [(rx, yc + 0.026 * math.sin(TAU * i / 5), gz + 0.026 * math.cos(TAU * i / 5)) for i in range(5)]
            new_object(f"rod_{k}_guide_{g}", tube_bm(ring, 0.007, 4, closed=True), reel, unwrap="facets", smooth_deg=70.0)
        # the spinning reel, big enough to read from the deck: a stem from the
        # seat, a round body, the spool above it and a crank on its side, all
        # facing the front
        rz, ry = z0 + 0.34, R_ROD_Y - 0.095
        new_object(f"reel_{k}_stem", box_bm(rx - 0.014, rx + 0.014, ry, R_ROD_Y, rz - 0.014, rz + 0.014), reel,
                   bevel=0.004, segments=1)
        new_object(f"reel_{k}_body", lathe_bm(sphere_profile(0.0, 0.05, -90.0, 90.0, 30.0), 10), reel, at=(rx, ry, rz),
                   unwrap="lathe", smooth_deg=70.0)
        new_object(f"reel_{k}_spool", lathe_bm([(0.0, rz + 0.04), (0.04, rz + 0.04), (0.046, rz + 0.048), (0.046, rz + 0.13),
                                                (0.04, rz + 0.138), (0.0, rz + 0.138)], 8), reel, at=(rx, ry, 0.0),
                   unwrap="lathe")
        new_object(f"reel_{k}_crank", tube_bm(rounded_path([(rx + 0.04, ry, rz), (rx + 0.10, ry, rz), (rx + 0.10, ry, rz - 0.06)],
                                                           0.015, 2), 0.008, 6), reel, unwrap=None)


def checks_rod_rack():
    return [
        f"rack {2 * (R_POST_X + R_POST / 2):.2f} m wide, {R_RAIL_Y1 - R_RAIL_Y0:.2f} m deep at the rails, {R_H:.2f} m tall; rails at "
        + " and ".join(f"{z:.2f}" for z in R_RAILS) + " m with holes, bolted at their ends",
        "rods " + ", ".join(f"{L:.2f}" for L in R_ROD_LEN) + f" m long from {R_BASE_H:.2f} m, grips {0.054 * 100:.1f} cm thick, "
        f"blanks 4.4 to 2.2 cm; {R_ROD_X[1] - R_ROD_X[0]:.2f} m apart (the greybox's were 0.4 m apart, outside the rack)",
    ]


# --- the cleanup bin ---------------------------------------------------------
#
# The greybox bin is a cylinder 0.82 m across and 1.4 m tall at x = +0.25, the
# bucket 0.52 m across and 0.72 m tall at x = -0.40, y = -0.05 (and 6 cm off
# the deck). Both stand where they were, on the deck.

B_X, B_R0, B_R1, B_H = 0.25, 0.39, 0.41, 1.40
K_X, K_Y, K_R0, K_R1, K_H = -0.40, -0.05, 0.20, 0.26, 0.72


def build_cleanup_bin():
    metal = material("bin_metal", GALVANIZED, 0.5)
    plastic = material("bucket_plastic", PLASTIC_BLUE, 0.6)
    wire = material("bin_wire", DARK_METAL, 0.4)

    def band(z, r):
        return [(r, z - 0.03), (r + 0.015, z - 0.012), (r + 0.015, z + 0.012), (r, z + 0.03)]

    def r_at(z):
        return B_R0 + (B_R1 - B_R0) * z / B_H

    # the bin: an open can, its floor recessed so it meets the deck on its rim,
    # two swage bands, a rolled rim, and the inside wall down to its floor
    prof = [(0.0, 0.004), (B_R0 - 0.03, 0.004), (B_R0, 0.0)]
    prof += band(0.45, r_at(0.45)) + band(0.95, r_at(0.95))
    prof += [(B_R1, B_H - 0.05), (B_R1 + 0.02, B_H - 0.03), (B_R1 + 0.02, B_H - 0.006), (B_R1 - 0.004, B_H),
             (B_R1 - 0.02, B_H - 0.03), (B_R1 - 0.025, B_H - 0.06), (B_R0 - 0.02, 0.08), (0.0, 0.08)]
    new_object("bin", lathe_bm(prof, 20), metal, at=(B_X, 0.0, 0.0), unwrap="lathe")

    # the bucket: tapered, a rolled rim, open, two ears and the bail dropped
    # down its +Y side
    new_object("bucket", lathe_bm([
        (0.0, 0.004), (K_R0 - 0.02, 0.004), (K_R0, 0.0), (K_R1 - 0.012, K_H - 0.04), (K_R1, K_H - 0.03),
        (K_R1 + 0.012, K_H - 0.016), (K_R1 + 0.004, K_H), (K_R1 - 0.012, K_H), (K_R1 - 0.02, K_H - 0.03),
        (K_R0 - 0.012, 0.05), (0.0, 0.05)], 16), plastic, at=(K_X, K_Y, 0.0), unwrap="lathe")
    ear_z = K_H - 0.07
    for side, sx in (("l", -1.0), ("r", 1.0)):
        new_object(f"bucket_ear_{side}", lathe_bm([(0.0, sx * -0.006), (0.022, sx * -0.006), (0.022, sx * 0.012),
                                                   (0.012, sx * 0.016), (0.0, sx * 0.016)], 10, "x"), plastic,
                   at=(K_X + sx * (K_R1 - 0.004), K_Y, ear_z), unwrap="facets")
    reach, tilt = 0.30, math.radians(62.0)   # the bail's reach from ear to apex, and how far it has dropped
    pts = []
    for i in range(13):
        a = math.pi * i / 12
        s = math.sin(a)
        pts.append((K_X + (K_R1 + 0.022) * math.cos(a), K_Y + reach * s * math.cos(tilt) + 0.012 * s,
                    ear_z - reach * s * math.sin(tilt)))
    new_object("bucket_bail", tube_bm(pts, 0.009, 6), wire, unwrap=None)


def checks_cleanup_bin():
    return [
        f"bin {2 * B_R1:.2f} m across the rim, {B_H:.2f} m tall at x = {B_X:+.2f}; bucket {2 * K_R1:.2f} m across, {K_H:.2f} m tall "
        f"at ({K_X:+.2f}, {K_Y:+.2f}), its bail dropped toward +Y",
    ]


# --- the folded stock cart and the empty crate -------------------------------
#
# No greybox. `S1_folded_cart` in boardwalk_operations.tscn is a 0.35 by 1.25 m
# box 0.9 m tall at the S1 door; `S2_empty_crate` a 0.92 m square box 0.72 m
# tall at S2. Two variants at the origin.

F_HX, F_H, F_BED_T = 0.625, 0.90, 0.06
F_CASTOR_R, F_CASTOR_W, F_CASTOR_Y = 0.065, 0.04, 0.13
F_HANDLE_R, F_HANDLE_X0, F_HANDLE_X1 = 0.016, 0.54, -0.30
F_HANDLE_Z = (0.15, 0.75)
F_LEAN_DEG = 4.0
X_HX, X_H, X_WALL, X_FLOOR = 0.46, 0.72, 0.04, 0.05
X_BATTEN = 0.075


def build_folded_cart():
    paint = material("stock_cart_paint", PAINT_TURQUOISE)
    metal = material("stock_cart_metal", DARK_METAL, 0.4)
    rubber = material("stock_cart_rubber", RUBBER, 0.95)
    timber = material("crate_timber", TIMBER_PALE)
    bolt_paint = family_bolt.paint_of(paint)
    cart = []

    # the bed stood on its long edge, its underside toward -Y: the chassis rails
    # and four castors face the deck's walker, which is what says "cart"; the
    # deck and the handle folded over it face the wall (+Y). The first pass
    # stood it the other way and read as a board with a handle
    bed = new_object("bed", prism(rounded_rect(F_HX, F_H / 2, 0.04, cy=F_H / 2), "y", -F_BED_T / 2, F_BED_T / 2), paint,
                     bevel=0.012)
    cart.append(bed)
    under = -F_BED_T / 2
    for k, (za, zb) in (("lo", (0.02, 0.08)), ("hi", (F_H - 0.08, F_H - 0.02))):
        cart.append(new_object(f"chassis_{k}", box_bm(-F_HX + 0.02, F_HX - 0.02, under - 0.04, under + 0.005, za, zb), metal,
                               bevel=0.006, segments=1))
    for i, (sx, sz) in enumerate(((-1, 0), (1, 0), (-1, 1), (1, 1))):
        cx, cz = sx * (F_HX - 0.12), 0.16 + sz * (F_H - 0.32)
        cart.append(new_object(f"castor_{i}_plate", box_bm(cx - 0.05, cx + 0.05, under - 0.012, under + 0.005,
                                                             cz - 0.05, cz + 0.05), metal, bevel=0.004, segments=1))
        cart.append(new_object(f"castor_{i}_yoke", box_bm(cx - 0.032, cx + 0.032, -F_CASTOR_Y + 0.02, under - 0.008,
                                                            cz - 0.032, cz + 0.032), metal, bevel=0.006, segments=1))
        wheel = new_object(f"castor_{i}_wheel", lathe_bm([
            (0.0, -F_CASTOR_W / 2), (F_CASTOR_R - 0.012, -F_CASTOR_W / 2), (F_CASTOR_R, -F_CASTOR_W / 2 + 0.012),
            (F_CASTOR_R, F_CASTOR_W / 2 - 0.012), (F_CASTOR_R - 0.012, F_CASTOR_W / 2), (0.0, F_CASTOR_W / 2)], 12, "x"),
            rubber, unwrap="facets")
        transform([wheel], Matrix.Translation((cx, -F_CASTOR_Y, cz)))
        cart.append(wheel)
    # the handle folded flat over the deck on two pivot blocks, a bolt each
    hy = F_BED_T / 2 + 0.028
    z0, z1 = F_HANDLE_Z
    cart.append(new_object("handle", tube_bm(rounded_path([(F_HANDLE_X0, hy, z0), (F_HANDLE_X1, hy, z0), (F_HANDLE_X1, hy, z1),
                                                           (F_HANDLE_X0, hy, z1)], 0.05), F_HANDLE_R, 10), metal, unwrap=None))
    for k, z in zip(("lo", "hi"), F_HANDLE_Z):
        block = new_object(f"pivot_{k}", box_bm(F_HANDLE_X0 - 0.035, F_HANDLE_X0 + 0.035, F_BED_T / 2 - 0.005, F_BED_T / 2 + 0.05,
                                                z - 0.035, z + 0.035), paint, bevel=0.006, segments=1)
        cart.append(block)
        cart.append(family_bolt.place(export(), f"bolt_pivot_{k}", Vector((F_HANDLE_X0, F_BED_T / 2 + 0.05, z)), (0, 1, 0),
                                      against=[block], material=bolt_paint))
    # leaning back as if against a wall, then set on the deck. The parts hold
    # their shape in world coordinates and turn by their vertices; a bolt is
    # the kit's mesh placed by its transform, so it turns by that
    rot = Matrix.Rotation(math.radians(-F_LEAN_DEG), 4, "X")
    for o in cart:
        if o.get(family_bolt.TAG):
            o.matrix_world = rot @ o.matrix_world
        else:
            transform([o], rot)
    settle(cart)
    tag(cart, kyt_variant="cart")

    # the crate: an open box on two skids with a batten up each corner
    crate = [subtract(box_bm(-X_HX, X_HX, -X_HX, X_HX, 0.02, X_H),
                      [box_bm(-X_HX + X_WALL, X_HX - X_WALL, -X_HX + X_WALL, X_HX - X_WALL, 0.02 + X_FLOOR, X_H + 0.1)],
                      "crate", timber, bevel=0.012)]
    for side, sy in (("f", -1.0), ("b", 1.0)):
        crate.append(new_object(f"skid_{side}", box_bm(-X_HX + 0.01, X_HX - 0.01, sy * 0.40 - 0.04, sy * 0.40 + 0.04, 0.0, 0.03),
                                timber, bevel=0.006, segments=1))
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        crate.append(new_object(f"batten_{i}", box_bm(min(sx * X_HX + sx * 0.005, sx * (X_HX - X_BATTEN + 0.005)),
                                                      max(sx * X_HX + sx * 0.005, sx * (X_HX - X_BATTEN + 0.005)),
                                                      min(sy * X_HX + sy * 0.005, sy * (X_HX - X_BATTEN + 0.005)),
                                                      max(sy * X_HX + sy * 0.005, sy * (X_HX - X_BATTEN + 0.005)),
                                                      0.02, X_H + 0.015), timber, bevel=0.01, segments=1))
    tag(crate, kyt_variant="crate")


def checks_folded_cart():
    return [
        f"cart: bed {2 * F_HX:.2f} by {F_H:.2f} m stood on its long edge, leaning {F_LEAN_DEG:.0f} degrees toward +Y, "
        f"castors {2 * F_CASTOR_R:.2f} m toward -Y, handle folded over the deck toward +Y (the wall)",
        f"crate: {2 * X_HX:.2f} m square, {X_H:.2f} m tall, walls {X_WALL * 100:.0f} cm, open; slats are paint",
    ]


# --- the file ----------------------------------------------------------------

BUILDERS = {
    "funhouse_turnstile": (build_turnstile, checks_turnstile),
    "funhouse_operator_box": (build_operator_box, checks_operator_box),
    "service_door": (build_service_door, checks_service_door),
    "fish_cleaning_sink": (build_fish_sink, checks_fish_sink),
    "tackle_cart": (build_tackle_cart, checks_tackle_cart),
    "rod_rack": (build_rod_rack, checks_rod_rack),
    "cleanup_bin": (build_cleanup_bin, checks_cleanup_bin),
    "folded_stock_cart": (build_folded_cart, checks_folded_cart),
}


def parts():
    return [o for o in export().all_objects if o.type == "MESH"]


def bounds(objs):
    """World-space extents from the parts' own vertices. The view layer is
    brought up to date first: an object placed since the last evaluation still
    reports an identity `matrix_world`, and its `bound_box` is stale too."""
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def variants(objs):
    groups = {}
    for o in objs:
        groups.setdefault(str(o.get("kyt_variant", "")), []).append(o)
    return groups


def report(name):
    objs = parts()
    tris = 0
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    faces = sum(len(o.data.polygons) for o in objs)
    print(f"service_operations: {name}: {len(objs)} parts, {faces} faces, {tris} triangles")
    print("  " + ", ".join(f"{o.name} {len(o.data.loop_triangles)}" for o in sorted(objs, key=lambda o: o.name)))
    groups = variants(objs)
    for key in sorted(groups):
        lo, hi = bounds(groups[key])
        t = sum(len(o.data.loop_triangles) for o in groups[key])
        label = f"  variant {key}: " if key else "  "
        print(f"{label}{hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m "
              f"(x {lo.x:+.3f}..{hi.x:+.3f}, y {lo.y:+.3f}..{hi.y:+.3f}, z {lo.z:+.3f}..{hi.z:+.3f}), "
              f"{len(groups[key])} parts, {t} triangles")


def render(folder, name):
    """Five frames into `folder`: three-quarter, front (-Y), side (+X), top,
    and the front again beside a 1.7 m box. A kit (variants) is laid out in
    a row for them; the file is never saved after this."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    scene.render.resolution_percentage = 100
    world = bpy.data.worlds.new("render_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    scene.world = world
    for cname in ("reference", "authored"):
        c = bpy.data.collections.get(cname)
        if c:
            c.hide_render = True

    objs = parts()
    groups = variants(objs)
    moved = []
    if len(groups) > 1:
        gap = 0.25
        widths = {k: bounds(v)[1].x - bounds(v)[0].x for k, v in groups.items()}
        x = -(sum(widths.values()) + gap * (len(groups) - 1)) / 2
        for key in sorted(groups):
            lo, hi = bounds(groups[key])
            shift = x + widths[key] / 2 - (lo.x + hi.x) / 2
            for o in groups[key]:
                o.location.x += shift
                moved.append((o, shift))
            x += widths[key] + gap
        bpy.context.view_layer.update()

    lo, hi = bounds(objs)
    centre, size = (lo + hi) / 2, max((hi - lo).length, 0.3)

    def add(name_, data, mat=None):
        ob = bpy.data.objects.new(name_, data)
        scene.collection.objects.link(ob)
        if mat is not None:
            ob.data.materials.append(mat)
        return ob

    ground = bpy.data.meshes.new("render_ground")
    g = max(12.0, 4.0 * size)
    ground.from_pydata([(-g, -g, -0.001), (g, -g, -0.001), (g, g, -0.001), (-g, g, -0.001)], [], [(0, 1, 2, 3)])
    add("render_ground", ground, material("render_ground", (0.55, 0.52, 0.46, 1)))
    sun = add("render_sun", bpy.data.lights.new("render_sun", "SUN"))
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    cam = add("render_cam", bpy.data.cameras.new("render_cam"))
    cam.data.lens = 45
    scene.camera = cam
    # the 1.7 m figure for scale: a box beside the prop, on the ground
    fig = box_bm(hi.x + 0.45, hi.x + 0.45 + 0.45, -0.15, 0.15, 0.0, 1.7)
    fig_mesh = bpy.data.meshes.new("render_figure")
    fig.to_mesh(fig_mesh)
    fig.free()
    figure = add("render_figure", fig_mesh, material("render_figure", (0.25, 0.27, 0.32, 1)))
    figure.hide_render = True

    from bpy_extras.object_utils import world_to_camera_view
    dg = bpy.context.evaluated_depsgraph_get()
    points = [o.matrix_world @ v.co for o in objs for v in o.evaluated_get(dg).data.vertices]
    fig_points = [Vector(c) for c in figure.bound_box]
    views = {
        "three_quarter": (Vector((-0.9, -1.1, 0.6)), centre, points),
        "front": (Vector((0.0, -1.5, 0.25)), centre, points),
        "side": (Vector((1.5, 0.0, 0.25)), centre, points),
        "top": (Vector((0.0, -0.02, 1.6)), centre, points),
        "scale": (Vector((0.0, -1.5, 0.25)), None, points + fig_points),
    }
    for tag_, (direction, target, pts) in views.items():
        figure.hide_render = tag_ != "scale"
        if tag_ == "scale":
            lo2, hi2 = lo, Vector((hi.x + 0.9, hi.y, max(hi.z, 1.7)))
            target = (lo2 + hi2) / 2
            span = max((hi2 - lo2).length, 0.3)
        else:
            span = size
        d = direction.normalized()
        loc = target + d * span * 1.4
        loc.z = max(loc.z, 0.12 * span + 0.1)
        for _ in range(40):
            cam.location = loc
            look = target - loc
            cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            if all(0.03 <= c.x <= 0.97 and 0.03 <= c.y <= 0.97
                   for c in (world_to_camera_view(scene, cam, p) for p in pts)):
                break
            loc = target + (loc - target) * 1.08
        scene.render.filepath = os.path.join(folder, f"{name}_{tag_}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)
    for o, shift in moved:
        o.location.x -= shift


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in BUILDERS:
        raise SystemExit(f"service_operations: open one of {', '.join(BUILDERS)}.blend, not {name}")
    if export().objects:
        if "--replace" not in argv:
            raise SystemExit(f"service_operations: export already holds {[o.name for o in export().objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(export().all_objects):
            bpy.data.objects.remove(o)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    build, check = BUILDERS[name]
    build()
    report(name)
    for line in check():
        print("  " + line)
    if "--save" in argv:
        # no .blend1 beside the prop: the file is Christina's, and its backup is hers to make
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
