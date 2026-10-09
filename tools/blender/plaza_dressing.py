"""The plaza dressing group, first pass from the catalog notes (2026-10-02):
the flagpole with its banner, the balloon pair, the litter kit and the service
cart. None of these has a reference photograph; each is a plain reading of its
catalog line and its generated greybox, at real scale, for Christina to
review and reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<prop>.blend --python tools/blender/plaza_dressing.py -- \
        [--replace] [--save] [--render <folder>]

`<prop>` is `flagpole_banner` (PRP-PARK-006), `balloon_cluster` (PRP-PARK-010),
`park_litter` (PRP-PARK-011) or `service_cart` (PRP-PARK-007). The tool builds
whichever the file is named for into `export`, one object a part, on z = 0 at
the origin facing -Y here (+Z in Godot). It refuses while `export` holds
anything (it may be hers) unless `--replace`; it writes the file only with
`--save`; `--render <folder>` shoots a three-quarter, front, side and top view
and one beside a 1.7 m box for scale, after any save, so nothing the render
adds reaches the file. Parts are tagged for `unwrap_parts.py` (`kyt_unwrap`).

**Flagpole and banner.** Catalog: "a navigation and park-identity marker,
distinct from seasonal pennants". Greybox: a 6 m pole 0.14 m across and a
0.7 by 2.2 m banner hung off it from 3.5 to 5.7 m, reaching toward -Y. Built:
a round footing plinth with four anchor bolts and a collar, a tapered pole
(0.14 m at the foot, 0.10 m at the top), a brass ball finial on a neck, and
at the banner's top and bottom a clamp band round the pole with its bolt and
an arm reaching out to a ball cap; the banner is a thick fabric slab with a
rounded hem sleeve over each arm, bellying 5 cm toward +X as if in a breeze,
blank for the painting. Assumed: the pole stands at the origin (the greybox's
pole stands 0.32 m behind it, because the maquette export centred the pair's
footprint); the banner keeps the greybox's side, toward -Y, its faces to +-X.

**Balloon cluster.** Catalog: "the current family is a tied pair; the old
loose bollard balloon is retired". Greybox: two 0.52 m spheres at 1.07 and
1.36 m on 2 cm strings down to the floor. Built: two latex balloons 0.42 m
across and 0.59 m tall, teardrop with a neck and knot, each leaning along its
own string, their centres where the greybox's are above the origin; two
1.6 cm strings with a slight bow; and the tie, at Christina's word ("tie the
balloons to the bench rail", 2 Oct 2026): a loop of string wrapped round the
plaza bench's top back slat (5 by 9 cm, running along X here) with the knot
on top, both strings leaving it. The loop's lowest point is the origin, so the
prop stands on z = 0 for Check; the placement puts that point at the slat's
underside at the tie, where `_balloons` in gen_props.gd ties the pair today.
The whole prop is marked not to collide, as the greybox was. (The first pass
of the same day stood the pair on a ground weight; it was replaced.)

**Park litter.** Catalog: "small cups and paper-like pieces used sparingly as
caused residue, not uniform grime". No greybox in the file: the plaza's thirty
pieces are upright cups (0.11 m across, 0.12 m tall) and flat 0.22 by 0.16 m
boxes 12 mm thick. Built as a kit of five pieces, each its own variant
(`kyt_variant`) at the origin, none colliding: `cup_lidded`, a crushed cup
with a lid and a straw lying on its flattened side; `cup_upright`, an empty
paper cup standing (the greybox's cylinder); `napkin`, a folded square with a
lifted corner; `ticket_stub`, a small curled ticket; `wrapper`, the 0.22 by
0.16 m flattened wrapper, crumpled. Nothing lies flat on the ground: every
piece touches it along a line or at points, so nothing z-fights the paving.
Each piece is a few dozen to a few hundred triangles.

**Service cart.** Catalog: "the shared wheeled work cart; local stock, tackle
and photo carts are separate families where their contents make their job
legible". Greybox: a 2.0 by 1.1 by 1.2 m body, a 2.4 by 1.5 m roof slab at
1.5 m, two 0.44 m wheels at one end, and the park's `cart_lamp` light 1.8 m
above the body's centre. Built: a rounded box body with a lipped lid at 1.0 m
on an axle with two big solid wheels (0.60 m, rubber tyres, hub nuts) at the +X
end and a swivel castor under the -X end, a U push handle at 0.92 m on two
bolted flanges, four posts to a barrel-vaulted canopy (2.3 by 1.44 m, eaves
at 1.90 m, crown at 2.07 m) on two eave beams, and under its middle a hanging
lamp on a cross bar, its bulb centred at 1.80 m where the game's light is.
Assumed: the canopy was raised from the greybox's 1.6 m so a pusher sees
under it and the lamp hangs under the canopy rather than on top of it; a
castor rather than a stand leg, so the covered cart rolls without tipping.
Nothing on it says what job it does.

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
PAINT_WHITE = (0.86, 0.86, 0.83, 1.0)
PAINT_CREAM = (0.84, 0.80, 0.70, 1.0)
PAINT_ROOF = (0.55, 0.20, 0.18, 1.0)
FABRIC = (0.58, 0.20, 0.18, 1.0)
BRASS = (0.62, 0.48, 0.18, 1.0)
LATEX = (0.80, 0.16, 0.14, 1.0)
STRING = (0.90, 0.88, 0.82, 1.0)
PLASTIC_DARK = (0.22, 0.22, 0.26, 1.0)
PLASTIC_LIGHT = (0.86, 0.86, 0.86, 1.0)
PAPER = (0.92, 0.90, 0.84, 1.0)
RUBBER = (0.07, 0.07, 0.07, 1.0)
BARE_METAL = (0.55, 0.56, 0.58, 1.0)
BULB = (1.0, 0.86, 0.60, 1.0)


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


def new_object(name, bm, mat, *, bevel=0.0, segments=3, angle=35.0, smooth=True, smooth_deg=40.0):
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


def transform(objs, matrix):
    """Move the vertices of `objs` by `matrix`, keeping their objects at the origin."""
    for o in objs:
        for v in o.data.vertices:
            v.co = matrix @ v.co
        o.data.update()


def settle(objs):
    """Lower (or raise) a set of parts together so their lowest vertex is on z = 0."""
    lo = min(v.co.z for o in objs for v in o.data.vertices)
    transform(objs, Matrix.Translation((0.0, 0.0, -lo)))


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


def rounded_rect(hx, hy, r, per=5):
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def lathe_bm(profile, sides=24, axis="z", closed=False):
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


def sphere_profile(centre_t, radius, a0=-90.0, a1=90.0, step=22.5):
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
        n, b = normal, t.cross(normal)
        rings.append([bm.verts.new(p + (n * math.cos(TAU * i / sides) + b * math.sin(TAU * i / sides)) * radius)
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


def bezier(p0, c, p2, n):
    pts = []
    for k in range(n + 1):
        s = k / n
        pts.append((1 - s) ** 2 * Vector(p0) + 2 * (1 - s) * s * Vector(c) + s ** 2 * Vector(p2))
    return pts


def sheet_bm(hx, hy, t, nx, ny, height):
    """A thin sheet of paper lying on the ground, `t` thick: `height(u, v)`
    (u, v in 0..1) lifts its underside, and its lowest point is put on z = 0,
    so it touches the ground at points or along a line and never shares the
    paving's plane."""
    hs = [[height(i / nx, j / ny) for j in range(ny + 1)] for i in range(nx + 1)]
    lo = min(min(col) for col in hs)
    bm = bmesh.new()
    bot = [[bm.verts.new((-hx + 2 * hx * i / nx, -hy + 2 * hy * j / ny, hs[i][j] - lo))
            for j in range(ny + 1)] for i in range(nx + 1)]
    top = [[bm.verts.new((-hx + 2 * hx * i / nx, -hy + 2 * hy * j / ny, hs[i][j] - lo + t))
            for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
            bm.faces.new((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    ring = ([(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)]
            + [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)])
    for k in range(len(ring)):
        (i0, j0), (i1, j1) = ring[k], ring[(k + 1) % len(ring)]
        bm.faces.new((bot[i0][j0], bot[i1][j1], top[i1][j1], top[i0][j0]))
    return bm


def tag(objs, **props):
    for o in objs:
        for k, v in props.items():
            o[k] = v


# --- the flagpole and banner -------------------------------------------------
#
# The greybox pole is 6 m tall and 0.14 m across; the banner 0.08 by 0.7 by
# 2.2 m, from 3.5 to 5.7 m, reaching toward -Y, its faces to +-X. The pole
# stands at the origin here (the greybox's is 0.315 m toward +Y, the maquette
# export having centred the pole-and-banner footprint). Sizes that carry bolts
# come from the family bolt: the clamp bands are BAND wide, the arms BAR thick.

F_POLE_R0, F_POLE_R1 = 0.07, 0.05   # the pole at its foot and under the finial
F_POLE_Z0, F_POLE_TOP = 0.30, 6.0
F_PLINTH_R, F_PLINTH_H = 0.22, 0.08
F_COLLAR_R0, F_COLLAR_TOP = 0.14, 0.36
F_BANNER_W, F_BANNER_Z0, F_BANNER_Z1 = 0.68, 3.5, 5.7
F_BANNER_IN = 0.12              # the banner's inner edge from the pole's axis
F_BANNER_T = 0.03
F_BELLY = 0.05                  # how far the fabric bellies toward +X
F_ARM_R = family_bolt.BAR / 2
F_ARM_END = F_BANNER_IN + F_BANNER_W + 0.04
F_SLEEVE_R = 0.045
F_FINIAL_R = 0.10


def pole_radius(z):
    return F_POLE_R0 + (F_POLE_R1 - F_POLE_R0) * (z - F_POLE_Z0) / (F_POLE_TOP - F_POLE_Z0)


def build_flagpole():
    paint = material("flagpole_paint", PAINT_WHITE)
    fabric = material("flagpole_fabric", FABRIC, 0.95)
    brass = material("flagpole_brass", BRASS, 0.45)
    bolt_paint = family_bolt.paint_of(paint)

    # the footing: a plinth, its underside recessed so it meets the paving on
    # its rim and not face to face, and a collar the pole rises out of. The
    # rounding is in the profile: a bevel modifier on a lathe costs every ring
    base = new_object("base", lathe_bm([
        (0.0, 0.004), (F_PLINTH_R - 0.03, 0.004), (F_PLINTH_R, 0.0), (F_PLINTH_R, F_PLINTH_H - 0.02),
        (F_PLINTH_R - 0.02, F_PLINTH_H), (F_COLLAR_R0 + 0.015, F_PLINTH_H), (F_COLLAR_R0, F_PLINTH_H + 0.015),
        (F_COLLAR_R0, F_PLINTH_H + 0.03), (0.085, F_COLLAR_TOP), (0.0, F_COLLAR_TOP),
    ], 20), paint)
    base["kyt_unwrap"] = "lathe"
    for i in range(4):
        a = math.radians(45.0 + 90.0 * i)
        r = (F_PLINTH_R + F_COLLAR_R0) / 2
        family_bolt.place(export(), f"bolt_foot_{i}", Vector((r * math.cos(a), r * math.sin(a), F_PLINTH_H)),
                          (0, 0, 1), ground=True, against=[base], material=bolt_paint)

    pole = new_object("pole", lathe_bm([(0.0, F_POLE_Z0), (F_POLE_R0, F_POLE_Z0),
                                        (F_POLE_R1, F_POLE_TOP), (0.0, F_POLE_TOP)], 20), paint)
    pole["kyt_unwrap"] = "lathe"

    # the finial: a collar on the pole's top, a neck, a brass ball
    neck_top = F_POLE_TOP + 0.08
    finial = new_object("finial", lathe_bm(
        [(0.0, F_POLE_TOP - 0.02), (F_POLE_R1 + 0.012, F_POLE_TOP - 0.02), (F_POLE_R1 + 0.012, F_POLE_TOP + 0.04),
         (0.03, F_POLE_TOP + 0.06), (0.03, neck_top)]
        + sphere_profile(neck_top + F_FINIAL_R * 0.95, F_FINIAL_R, -72.0, 90.0, 27.0), 12), brass)
    finial["kyt_unwrap"] = "lathe"

    for tag_, z in (("top", F_BANNER_Z1), ("bottom", F_BANNER_Z0)):
        # a clamp band round the pole, BAND wide, with the one bolt a hinged
        # clamp closes with, on its +X side
        r_in, r_out, hw = pole_radius(z) - 0.005, pole_radius(z) + 0.014, family_bolt.BAND / 2
        band = new_object(f"band_{tag_}", lathe_bm([
            (r_in, z - hw), (r_out - 0.006, z - hw), (r_out, z - hw + 0.006),
            (r_out, z + hw - 0.006), (r_out - 0.006, z + hw), (r_in, z + hw)], 16, closed=True), paint)
        band["kyt_unwrap"] = "lathe"
        family_bolt.place(export(), f"bolt_band_{tag_}", Vector((r_out, 0.0, z)), (1, 0, 0),
                          against=[band], material=bolt_paint)
        # the arm, from inside the pole out past the banner, and its ball cap
        new_object(f"arm_{tag_}", tube_bm([(0.0, 0.0, z), (0.0, -F_ARM_END, z)], F_ARM_R, 12), paint)
        cap = new_object(f"arm_cap_{tag_}", lathe_bm(sphere_profile(-F_ARM_END, 0.035, -90.0, 90.0, 36.0), 8, "y"),
                         paint, smooth_deg=60.0)
        transform([cap], Matrix.Translation((0.0, 0.0, z)))
        cap["kyt_unwrap"] = "lathe"
        # the banner's sleeve over the arm: a rounded hem the fabric wraps round it with
        sleeve = new_object(f"sleeve_{tag_}", tube_bm([(0.0, -F_BANNER_IN, z), (0.0, -(F_BANNER_IN + F_BANNER_W), z)],
                                                      F_SLEEVE_R, 14), fabric)
        sleeve["kyt_unwrap"] = "lathe"

    # the banner: a thick fabric slab between the sleeves, bellying toward +X
    n = 6
    outer, inner = [], []
    for i in range(n + 1):
        s = i / n
        y = -(F_BANNER_IN + F_BANNER_W * s)
        x = F_BELLY * math.sin(math.pi * s)
        outer.append((x + F_BANNER_T / 2, y))
        inner.append((x - F_BANNER_T / 2, y))
    banner = new_object("banner", prism(outer + list(reversed(inner)), "z", F_BANNER_Z0 + 0.02, F_BANNER_Z1 - 0.02),
                        fabric, bevel=0.012, segments=2, angle=60.0)
    banner["kyt_unwrap"] = "facets"


def checks_flagpole():
    return [
        f"pole {F_POLE_TOP:.1f} m to the finial's collar, {2 * F_POLE_R0 * 100:.0f} cm across at the foot and "
        f"{2 * F_POLE_R1 * 100:.0f} at the top; finial ball {2 * F_FINIAL_R * 100:.0f} cm",
        f"banner {F_BANNER_W:.2f} m wide, {F_BANNER_Z1 - F_BANNER_Z0:.1f} m tall from {F_BANNER_Z0:.1f} m, "
        f"its inner edge {F_BANNER_IN - F_POLE_R0:.2f} m off the pole, bellying {F_BELLY * 100:.0f} cm toward +X",
        f"clamp bands {family_bolt.BAND * 1000:.0f} mm wide, arms {family_bolt.BAR * 1000:.0f} mm thick; "
        f"footing {2 * F_PLINTH_R:.2f} m across, four anchor bolts",
    ]


# --- the balloon cluster -----------------------------------------------------
#
# The greybox has two 0.26 m spheres with their centres at (0.215, -0.025,
# 1.07) and (-0.215, 0.025, 1.36) and 2 cm strings running to the floor. The
# balloons here keep those centres; each leans along its own string from the
# knot on the rail, as a tied balloon does.
#
# The tie (Christina, 2 Oct 2026: "tie the balloons to the bench rail"). In
# the plaza `_balloons` in gen_props.gd ties the pair to the photo hut bench's
# back rail, strings from `HUT_BENCH_RAIL` (0.98 m, the greybox back's top) at
# x 0.84 and 0.42 along the bench. On the modelled plaza bench
# (plaza_bench_source.blend) that rail is the top back slat `back_3`: a flat
# timber slat 0.05 m thick and 0.09 m tall, 2.02 m long along the bench's X,
# its top at 1.005 m, between end uprights that rise to 1.017 m. So the tie is
# a loop of string wrapped round a 5 by 9 cm slat running along X here, with
# the knot on top and both strings leaving it. The loop's lowest point is the
# prop's origin: the placement puts it at the slat's underside at the tie.

B_R = 0.21                       # a balloon's greatest radius (0.42 m across)
B_CENTRES = ((0.215, -0.025, 1.07), (-0.215, 0.025, 1.36))
B_STRING_R = 0.008
B_RAIL_Y, B_RAIL_Z = 0.05, 0.09   # the slat the loop wraps: across the bench, and tall
B_SLACK = 0.003                   # the loop's play round the slat


def balloon_profile():
    """A latex balloon, (r, z) about its centre: round-shouldered at the top,
    tapering to a neck and a knot at the bottom, about 1.4 times as tall as wide."""
    k = B_R / 0.21
    return [(r * k, z * k) for r, z in (
        (0.0, 0.265), (0.085, 0.25), (0.15, 0.205), (0.195, 0.13), (0.21, 0.03), (0.2, -0.07),
        (0.165, -0.155), (0.11, -0.215), (0.06, -0.25), (0.036, -0.27), (0.03, -0.285),
        (0.042, -0.298), (0.04, -0.31), (0.02, -0.32), (0.0, -0.325))]


def build_balloons():
    latex = material("balloon_latex", LATEX, 0.35)
    string = material("balloon_string", STRING, 0.9)
    made = []

    # the tie: a loop of string round the slat's section (in the YZ plane, the
    # slat running along X), its underside on z = 0, and the knot on top of it
    hy = B_RAIL_Y / 2 + B_SLACK + B_STRING_R
    hz = B_RAIL_Z / 2 + B_SLACK + B_STRING_R
    zc = B_STRING_R + hz
    loop = new_object("tie_loop", tube_bm([(0.0, a, b + zc) for a, b in rounded_rect(hy, hz, 0.018, 3)],
                                          B_STRING_R, 8, closed=True), string, smooth_deg=60.0)
    knot_z = zc + hz + B_STRING_R + 0.006
    knot = new_object("tie_knot", lathe_bm([(0.017 * math.cos(math.radians(a)), knot_z + 0.013 * math.sin(math.radians(a)))
                                            for a in range(-90, 91, 30)], 12), string, smooth_deg=70.0)
    knot["kyt_unwrap"] = "lathe"
    made += [loop, knot]

    tie = Vector((0.0, 0.0, knot_z + 0.008))
    for i, c in enumerate(B_CENTRES):
        centre = Vector(c)
        d = (centre - tie).normalized()           # the string's line, the balloon's axis
        balloon = new_object(f"balloon_{i}", lathe_bm(balloon_profile(), 18), latex, smooth_deg=70.0)
        transform([balloon], Matrix.Translation(centre) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4())
        balloon["kyt_unwrap"] = "lathe"
        knot = centre - d * (0.30 * B_R / 0.21)
        out = Vector((d.x, d.y, 0.0)).normalized()
        mid = (tie + knot) / 2 + out * 0.025
        made += [balloon, new_object(f"string_{i}", tube_bm(bezier(tie, mid, knot, 5), B_STRING_R, 8), string, smooth_deg=60.0)]
    tag(made, kyt_collision="none")


def checks_balloons():
    gap = (Vector(B_CENTRES[0]) - Vector(B_CENTRES[1])).length - 2 * B_R
    slat_top = 2 * B_STRING_R + B_SLACK + B_RAIL_Z    # the slat's top above the origin, inside the loop
    return [
        f"balloons {2 * B_R:.2f} m across, {0.59 * B_R / 0.21:.2f} m tall with the knot, centres "
        + " and ".join(f"{c[2]:.2f} m" for c in B_CENTRES) + f" above the loop's bottom, {gap * 100:.0f} cm apart at their closest",
        f"the loop wraps a {B_RAIL_Y * 100:.0f} by {B_RAIL_Z * 100:.0f} cm slat along X whose top is {slat_top * 100:.1f} cm above "
        f"the origin, so the centres are " + " and ".join(f"{c[2] - slat_top:.2f} m" for c in B_CENTRES)
        + " above the rail's top (the generator's 1.07 and 1.36)",
        f"strings {B_STRING_R * 2000:.0f} mm; nothing collides",
    ]


# --- the litter kit ----------------------------------------------------------
#
# The plaza's litter is thirty single CSG nodes: upright cylinders 0.11 m
# across and 0.12 m tall (the cups) and flat 0.22 by 0.16 by 0.012 m boxes
# (the paper). The kit replaces both with pieces that read, each its own
# variant at the origin and none colliding (a centimetre of lip is a wall).

L_CUP_R_BASE, L_CUP_R_RIM, L_CUP_H = 0.034, 0.048, 0.125
L_SQUASH = 0.72                  # the crushed cup's section, across its flattened side


def cup_profile(open_top):
    """A paper cup, (r, z): a rolled foot ring that touches the ground (the
    floor is recessed), a tapering wall and a rolled rim; `open_top` adds an
    inner wall down to the floor, for a cup without a lid."""
    pts = [(0.0, 0.005), (L_CUP_R_BASE - 0.006, 0.005), (L_CUP_R_BASE, 0.0), (L_CUP_R_BASE + 0.002, 0.006),
           (L_CUP_R_RIM - 0.003, L_CUP_H - 0.01), (L_CUP_R_RIM, L_CUP_H - 0.004), (L_CUP_R_RIM - 0.001, L_CUP_H)]
    if open_top:
        pts += [(L_CUP_R_RIM - 0.006, L_CUP_H - 0.003), (L_CUP_R_RIM - 0.008, L_CUP_H - 0.012),
                (L_CUP_R_BASE - 0.003, 0.014), (0.0, 0.014)]
    else:
        pts += [(0.0, L_CUP_H)]
    return pts


def build_litter():
    paper = material("litter_paper", PAPER, 0.9)
    plastic = material("litter_plastic", PLASTIC_LIGHT, 0.5)
    pieces = {}

    # a crushed cup with its lid and straw, lying on its flattened side
    cup = new_object("cup_lidded_cup", lathe_bm(cup_profile(False), 12), paper, smooth_deg=50.0)
    lid = new_object("cup_lidded_lid", lathe_bm([
        (0.0, L_CUP_H - 0.006), (L_CUP_R_RIM + 0.004, L_CUP_H - 0.006), (L_CUP_R_RIM + 0.004, L_CUP_H + 0.008),
        (L_CUP_R_RIM - 0.004, L_CUP_H + 0.012), (0.012, L_CUP_H + 0.012), (0.0, L_CUP_H + 0.012)], 12), plastic,
        smooth_deg=50.0)
    straw = new_object("cup_lidded_straw", tube_bm([(0.0, 0.0, L_CUP_H - 0.03), (0.0, 0.0, L_CUP_H + 0.01),
                                                     (0.028, 0.055, L_CUP_H + 0.13)], 0.005, 8), plastic, smooth_deg=60.0)
    squash = Matrix.Rotation(math.radians(90.0), 4, "X") @ Matrix.Diagonal((1.0, L_SQUASH, 1.0, 1.0))
    transform([cup, lid, straw], squash)
    settle([cup, lid, straw])
    pieces["cup_lidded"] = [cup, lid, straw]
    for o in (cup, lid):
        o["kyt_unwrap"] = "lathe"

    # an empty cup standing, the greybox's cylinder
    up = new_object("cup_upright", lathe_bm(cup_profile(True), 12), paper, smooth_deg=50.0)
    up["kyt_unwrap"] = "lathe"
    pieces["cup_upright"] = [up]

    # a folded napkin, one corner lifting
    def napkin_h(u, v):
        return 0.03 * max(0.0, (u + v - 1.1) / 0.9) ** 2 + 0.002 * math.sin(3.0 * u) * math.cos(2.5 * v)
    nap = new_object("napkin", sheet_bm(0.065, 0.065, 0.006, 6, 6, napkin_h), paper, smooth_deg=50.0)
    pieces["napkin"] = [nap]

    # a ticket stub, curled up at both ends
    def ticket_h(u, v):
        return 0.012 * (2 * u - 1) ** 2
    ticket = new_object("ticket_stub", sheet_bm(0.045, 0.0225, 0.003, 6, 2, ticket_h), paper, smooth_deg=50.0)
    pieces["ticket_stub"] = [ticket]

    # the flattened wrapper, crumpled, one corner lifting
    def wrapper_h(u, v):
        crumple = 0.010 * (0.5 + 0.5 * math.sin(3 * math.pi * u + 0.7) * math.cos(1.2 * math.pi * v + 0.3))
        return crumple + 0.025 * max(0.0, (u + v - 1.5) / 0.5) ** 2
    wrap = new_object("wrapper", sheet_bm(0.11, 0.08, 0.004, 8, 6, wrapper_h), paper, smooth_deg=50.0)
    pieces["wrapper"] = [wrap]

    for key, objs in pieces.items():
        tag(objs, kyt_variant=key, kyt_collision="none")
        for o in objs:
            if "kyt_unwrap" not in o:
                o["kyt_unwrap"] = "facets"


def checks_litter():
    return [f"cups {2 * L_CUP_R_RIM * 100:.1f} cm across the rim, {L_CUP_H * 100:.1f} cm tall; the crushed one "
            f"{L_SQUASH * 2 * L_CUP_R_RIM * 100:.1f} cm thick lying down; wrapper 22 by 16 cm, napkin 13 cm "
            "square, ticket 9 by 4.5 cm; nothing collides"]


# --- the service cart --------------------------------------------------------
#
# The greybox body is 2.0 by 1.1 m and 1.2 m tall, its roof 2.4 by 1.5 m at
# 1.5 m, its wheels 0.44 m across at x = +0.6, and the park's `cart_lamp`
# light 1.8 m above the body's centre. The body here is a box on an axle;
# the canopy is raised so a pusher sees under it, and the lamp hangs from
# its middle with the bulb where the light is.

C_BODY_X, C_BODY_Y = 0.90, 0.48      # half length and half width
C_BODY_Z0, C_BODY_Z1 = 0.42, 1.00    # the box's underside and its lid
C_LID_T = 0.04
C_WHEEL_R, C_WHEEL_W = 0.30, 0.10
C_AXLE_X = 0.55
C_WHEEL_Y = C_BODY_Y + 0.06 + C_WHEEL_W / 2
C_HUB_R, C_HUB_W = 0.06, 0.09
C_CASTOR_X, C_CASTOR_R = -0.72, 0.085
C_HANDLE_Z, C_HANDLE_X, C_HANDLE_Y = 0.92, 1.16, 0.34
C_HANDLE_R = family_bolt.BAR / 2
C_FLANGE_R = 0.06
C_POST = max(0.06, family_bolt.POST)    # the posts and beams, chunky against the box
C_POST_X, C_POST_Y = 0.80, 0.40
C_ROOF_X, C_ROOF_Y = 1.15, 0.72
C_EAVE_Z, C_ROOF_RISE, C_ROOF_T = 1.90, 0.12, 0.05
C_LAMP_Z = 1.80                       # the bulb's centre: where the game's light is


def roof_under(y):
    return C_EAVE_Z + C_ROOF_RISE * (1.0 - (y / C_ROOF_Y) ** 2)


def build_cart():
    paint = material("cart_paint", PAINT_CREAM)
    roof_paint = material("cart_paint_roof", PAINT_ROOF)
    rubber = material("cart_rubber", RUBBER, 0.95)
    metal = material("cart_metal", BARE_METAL, 0.4)
    bulb_mat = material("cart_bulb", BULB, 0.2)
    bolt_paint = family_bolt.paint_of(paint)

    # the body: a rounded box, and its lid a hair wider, a lip all round
    body = new_object("body", prism(rounded_rect(C_BODY_X, C_BODY_Y, 0.06), "z", C_BODY_Z0, C_BODY_Z1), paint,
                      bevel=0.03, segments=2)
    lid = new_object("lid", prism(rounded_rect(C_BODY_X + 0.02, C_BODY_Y + 0.02, 0.07), "z",
                                  C_BODY_Z1 - 0.01, C_BODY_Z1 + C_LID_T), paint, bevel=0.018, segments=2)
    for o in (body, lid):
        o["kyt_unwrap"] = "facets"

    # the axle under the wheel end, held to the body by two brackets
    axle = new_object("axle", tube_bm([(C_AXLE_X, -C_WHEEL_Y - C_HUB_W / 2, C_WHEEL_R),
                                       (C_AXLE_X, C_WHEEL_Y + C_HUB_W / 2, C_WHEEL_R)], 0.022, 12), metal)
    for side, sy in (("l", -1.0), ("r", 1.0)):
        br = new_object(f"axle_bracket_{side}", box_bm(C_AXLE_X - 0.05, C_AXLE_X + 0.05, sy * 0.38 - 0.04, sy * 0.38 + 0.04,
                                                       C_WHEEL_R - 0.045, C_BODY_Z0 + 0.01), paint, bevel=0.01, segments=2)
        br["kyt_unwrap"] = "facets"
        # the wheel: a rubber tyre (its round section in the profile) round a
        # flat disc with a hub, and the axle nut
        hw = C_WHEEL_W / 2
        tyre = new_object(f"wheel_{side}_tyre", lathe_bm([
            (C_WHEEL_R - 0.085, hw), (C_WHEEL_R - 0.03, hw), (C_WHEEL_R - 0.006, hw * 0.7), (C_WHEEL_R, 0.0),
            (C_WHEEL_R - 0.006, -hw * 0.7), (C_WHEEL_R - 0.03, -hw), (C_WHEEL_R - 0.085, -hw)], 20, "y", closed=True),
            rubber)
        disc = new_object(f"wheel_{side}", lathe_bm([
            (0.0, C_HUB_W / 2), (C_HUB_R - 0.012, C_HUB_W / 2), (C_HUB_R, C_HUB_W / 2 - 0.012), (C_HUB_R, 0.015),
            (C_WHEEL_R - 0.08, 0.015), (C_WHEEL_R - 0.08, -0.015), (C_HUB_R, -0.015), (C_HUB_R, -C_HUB_W / 2 + 0.012),
            (C_HUB_R - 0.012, -C_HUB_W / 2), (0.0, -C_HUB_W / 2)], 20, "y"), paint)
        transform([tyre, disc], Matrix.Translation((C_AXLE_X, sy * C_WHEEL_Y, C_WHEEL_R)))
        for o in (tyre, disc):
            o["kyt_unwrap"] = "lathe"
        family_bolt.place(export(), f"bolt_hub_{side}", Vector((C_AXLE_X, sy * (C_WHEEL_Y + C_HUB_W / 2), C_WHEEL_R)),
                          (0, sy, 0), against=[disc])

    # the castor under the handle end: a stem, a fork, a small wheel
    new_object("castor_stem", tube_bm([(C_CASTOR_X, 0.0, C_BODY_Z0 + 0.02), (C_CASTOR_X, 0.0, 0.22)], 0.02, 12), metal)
    fork = new_object("castor_fork", prism([
        (-0.07, 0.06), (-0.07, 0.25), (0.07, 0.25), (0.07, 0.06), (0.04, 0.06), (0.04, 0.21), (-0.04, 0.21), (-0.04, 0.06)],
        "x", C_CASTOR_X - 0.03, C_CASTOR_X + 0.03), metal, bevel=0.008, segments=2)
    fork["kyt_unwrap"] = "facets"
    cw = new_object("castor_wheel", lathe_bm([(0.0, 0.025), (C_CASTOR_R - 0.012, 0.025), (C_CASTOR_R, 0.013),
                                              (C_CASTOR_R, -0.013), (C_CASTOR_R - 0.012, -0.025), (0.0, -0.025)],
                                             12, "y"), rubber)
    transform([cw], Matrix.Translation((C_CASTOR_X, 0.0, C_CASTOR_R)))
    cw["kyt_unwrap"] = "lathe"

    # the push handle: a U of BAR-thick tube on two flanges bolted to the end
    x0 = -C_BODY_X + 0.03
    new_object("handle", tube_bm(rounded_path([(x0, -C_HANDLE_Y, C_HANDLE_Z), (-C_HANDLE_X, -C_HANDLE_Y, C_HANDLE_Z),
                                               (-C_HANDLE_X, C_HANDLE_Y, C_HANDLE_Z), (x0, C_HANDLE_Y, C_HANDLE_Z)], 0.08),
                                 C_HANDLE_R, 12), paint)
    for side, sy in (("l", -1.0), ("r", 1.0)):
        fl = new_object(f"handle_flange_{side}", lathe_bm([(0.0, -C_BODY_X + 0.004), (C_FLANGE_R, -C_BODY_X + 0.004),
                                                           (C_FLANGE_R, -C_BODY_X - 0.008), (C_FLANGE_R - 0.004, -C_BODY_X - 0.012),
                                                           (0.0, -C_BODY_X - 0.012)], 12, "x"), paint)
        transform([fl], Matrix.Translation((0.0, sy * C_HANDLE_Y, C_HANDLE_Z)))
        fl["kyt_unwrap"] = "lathe"
        for k, dz in (("u", 0.038), ("d", -0.038)):
            family_bolt.place(export(), f"bolt_handle_{side}_{k}", Vector((-C_BODY_X - 0.012, sy * C_HANDLE_Y, C_HANDLE_Z + dz)),
                              (-1, 0, 0), against=[fl], material=bolt_paint)

    # the canopy: four posts into the lid, two eave beams, the vaulted roof on them
    beam_top = roof_under(C_POST_Y)
    for sx, tx in ((-1.0, "l"), (1.0, "r")):
        for sy, ty in ((-1.0, "f"), (1.0, "b")):
            p = new_object(f"post_{ty}{tx}", box_bm(sx * C_POST_X - C_POST / 2, sx * C_POST_X + C_POST / 2,
                                                    sy * C_POST_Y - C_POST / 2, sy * C_POST_Y + C_POST / 2,
                                                    C_BODY_Z1 - 0.02, beam_top - 0.02), paint, bevel=0.008, segments=2)
            p["kyt_unwrap"] = "facets"
    for sy, ty in ((-1.0, "f"), (1.0, "b")):
        b = new_object(f"beam_{ty}", box_bm(-C_POST_X - 0.08, C_POST_X + 0.08, sy * C_POST_Y - C_POST / 2,
                                            sy * C_POST_Y + C_POST / 2, beam_top - 0.055, beam_top), paint, bevel=0.008, segments=2)
        b["kyt_unwrap"] = "facets"
    bar = new_object("cross_bar", box_bm(-0.02, 0.02, -C_POST_Y, C_POST_Y, beam_top - 0.045, beam_top - 0.008),
                     paint, bevel=0.006, segments=2)
    bar["kyt_unwrap"] = "facets"
    n = 12
    top, under = [], []
    for i in range(n + 1):
        y = -C_ROOF_Y + 2 * C_ROOF_Y * i / n
        under.append((y, roof_under(y)))
        top.append((y, roof_under(y) + C_ROOF_T))
    roof = new_object("roof", prism(top + list(reversed(under)), "x", -C_ROOF_X, C_ROOF_X), roof_paint,
                      bevel=0.02, segments=2, angle=60.0)
    roof["kyt_unwrap"] = "facets"

    # the lamp under the canopy's middle: a stem from the cross bar, a shade, the bulb
    new_object("lamp_stem", tube_bm([(0.0, 0.0, beam_top - 0.02), (0.0, 0.0, C_LAMP_Z + 0.062)], 0.012, 10), metal)
    shade = new_object("lamp_shade", lathe_bm([
        (0.0, C_LAMP_Z + 0.072), (0.03, C_LAMP_Z + 0.072), (0.135, C_LAMP_Z - 0.005), (0.135, C_LAMP_Z - 0.015),
        (0.12, C_LAMP_Z - 0.01), (0.034, C_LAMP_Z + 0.055), (0.0, C_LAMP_Z + 0.055)], 16), metal)
    shade["kyt_unwrap"] = "lathe"
    bulb = new_object("lamp_bulb", lathe_bm(sphere_profile(C_LAMP_Z, 0.035, -90.0, 50.0, 20.0)
                                            + [(0.018, C_LAMP_Z + 0.035), (0.018, C_LAMP_Z + 0.06), (0.0, C_LAMP_Z + 0.06)], 12),
                      bulb_mat, smooth_deg=70.0)
    bulb["kyt_unwrap"] = "lathe"


def checks_cart():
    return [
        f"body {2 * C_BODY_X:.2f} by {2 * C_BODY_Y:.2f} m, lid at {C_BODY_Z1 + C_LID_T:.2f} m; wheels {2 * C_WHEEL_R:.2f} m across "
        f"at x = {C_AXLE_X:+.2f}, {2 * C_WHEEL_Y + C_HUB_W:.2f} m hub to hub; castor {2 * C_CASTOR_R:.2f} m at x = {C_CASTOR_X:+.2f}",
        f"handle at {C_HANDLE_Z:.2f} m, {C_HANDLE_R * 2000:.0f} mm tube, {2 * C_HANDLE_Y:.2f} m wide, reaching x = {-C_HANDLE_X:.2f}",
        f"canopy {2 * C_ROOF_X:.2f} by {2 * C_ROOF_Y:.2f} m, eaves {C_EAVE_Z:.2f} m, crown {roof_under(0.0) + C_ROOF_T:.2f} m; "
        f"lamp bulb centred {C_LAMP_Z:.2f} m up, under the canopy",
    ]


# --- the file ----------------------------------------------------------------

BUILDERS = {
    "flagpole_banner": (build_flagpole, checks_flagpole),
    "balloon_cluster": (build_balloons, checks_balloons),
    "park_litter": (build_litter, checks_litter),
    "service_cart": (build_cart, checks_cart),
}


def parts():
    return [o for o in export().all_objects if o.type == "MESH"]


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
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
    print(f"plaza_dressing: {name}: {len(objs)} parts, {faces} faces, {tris} triangles")
    print("  " + ", ".join(f"{o.name} {len(o.data.loop_triangles)}" for o in sorted(objs, key=lambda o: o.name)))
    groups = variants(objs)
    for key in sorted(groups):
        lo, hi = bounds(groups[key])
        t = 0
        for o in groups[key]:
            t += len(o.data.loop_triangles)
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
    scene.render.engine = "BLENDER_EEVEE"
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
        gap = 0.06
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

    def add(name_, mesh_or_none, mat=None):
        ob = bpy.data.objects.new(name_, mesh_or_none)
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
        "three_quarter": (Vector((-0.9, -1.1, 0.6)), centre + Vector((0, 0, 0.0)), points),
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
        raise SystemExit(f"plaza_dressing: open one of {', '.join(BUILDERS)}.blend, not {name}")
    if export().objects:
        if "--replace" not in argv:
            raise SystemExit(f"plaza_dressing: export already holds {[o.name for o in export().objects][:4]}...; "
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
