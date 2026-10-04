"""The tidal lagoon's three swimmers, a first model pass (2026-10-03) for the
prop library's PRP-WILD-034 harbor seal, 038 leopard shark and 039 bat ray,
which Christina added on 2026-10-03 ("lets add those too") from the lagoon
plan in `documentation/maps/entrance-landscaping.html`: harbor seals hauled out
on the mouth's sandbar, leopard sharks and bat rays over the eelgrass for the
glass-bottom boat. None has a photograph of hers or a greybox: each is the
plainest readable reading of the species in the house style, chunky and
rounded (`prop-pipeline.md`, Standards applied), for her to reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<animal>.blend --python tools/blender/wildlife_lagoon_swimmers.py -- \\
        [--replace] [--save] [--render <folder>]

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \\
        --python tools/blender/wildlife_lagoon_swimmers.py -- --lineup <png>

`<animal>` is `harbor_seal`, `leopard_shark` or `bat_ray`. The tool builds
whichever the file is named for into `export`, one object a part, real metres,
Z up, the head toward -Y (+Z in Godot), the lowest point on z = 0 and the plan
(the bounding box) centred on the origin. It refuses while `export` holds
anything (it may be hers) unless `--replace`; it writes the file only with
`--save`; `--render` shoots three-quarter, front, side and top views and one
beside a 1.7 m box (and for the seal a close look at its head) into the folder (saved first, so the render's camera, sun
and ground never reach the file). `--lineup` builds all three in memory and
renders them side by side at true relative size beside the 1.7 m box; nothing
is saved in that mode.

**Articulation.** As on the gull (`assets/source/wildlife/gull_adult.blend`),
every moving part hangs under an empty at its joint, named `<part>_pivot`,
unrotated and unscaled, with the part's vertices in that pivot's frame, so
turning the pivot swings the part about its joint. A pivot that rides on
another is its child. No armature, no animation, no behaviour: how each moves
is a separate decision. Every part is `kyt_collision = none`: ambient wildlife
never blocks the player. Left and right are the animal's own: facing -Y, its
left is +X (Blender's `.L` side), as on every other wildlife model.

**Harbor seal** (PRP-WILD-034): a Pacific harbor seal (Phoca vitulina
richardii), adult, 1.73 m from nose to the tips of the hind flippers (about
1.5 m nose to tail), 0.53 m across the lying body (0.64 m across the fore
flippers) and 0.41 m to the crown,
hauled out on sand lying on its belly, the head raised a little, the fore
flippers lying flat beside the chest, the hind flippers together behind it,
their tips just off the sand. What makes it a seal and not the sea lion beside
it: a fat sausage lying flat (it cannot prop itself up), a round, dog-like
head with a short muzzle and big eyes, no ear flaps (the ear holes are paint),
short fore flippers that only reach the sand, and hind flippers that point
backward for good. Parts: `body`; `head`, `nose`, `eye_left`, `eye_right`
(`head_pivot`, at the neck); `flipper_front_left`, `flipper_front_right`
(`flipper_front_left_pivot`, `flipper_front_right_pivot`, at the shoulders);
`flipper_rear_left`, `flipper_rear_right` (`flipper_rear_left_pivot`,
`flipper_rear_right_pivot`, at the ankles). Mottling, whiskers, claws, the ear
holes and the V of the nostrils are paint.

**Leopard shark** (PRP-WILD-038): Triakis semifasciata, adult, 1.40 m total
length, swimming level. A slender houndshark: short rounded snout, big oval
eyes, an underslung arched mouth, broad pectorals angled a little down, a
first dorsal over the gap between pectorals and pelvics, a second dorsal
nearly as big, a small anal fin, and a long low upper tail lobe with a
terminal lobe and a small lower lobe. 0.47 m across the pectorals, 0.27 m to
the first dorsal's tip. The lowest point is the pectorals' tips on z = 0; in
the game it swims, so its placement puts it in the water over the eelgrass. Parts: `body`, `eye_left`, `eye_right`, `dorsal_fin_first`,
`pelvic_fin_left`, `pelvic_fin_right`; `jaw` (`jaw_pivot`, at the mouth's
corners); `pectoral_fin_left`, `pectoral_fin_right` (`pectoral_left_pivot`,
`pectoral_right_pivot`); `tail`, `dorsal_fin_second`, `anal_fin`
(`tail_pivot`, behind the pelvics); `caudal_fin` (`caudal_pivot`, at the tail
stock, under `tail_pivot`). The saddles and spots, the gill slits and the
countershading's edge are paint.

**Bat ray** (PRP-WILD-039): Myliobatis californica, adult, 1.20 m across the
wings, 1.66 m from snout to tail tip, 0.125 m deep at the head, swimming level
with the wingtips lifted a little. The bat-like head stands up and out in front of the disc with the eyes
on its sides; the wings are pointed, their leading edges convex and their
trailing edges concave; small pelvic fins show behind them; the whip tail,
0.9 m, carries a small dorsal fin at its root (the sting behind it is left
out). The lowest point is the belly on z = 0; in the game it swims, so its
placement puts it in the water over the eelgrass. Parts: `body`, `eye_left`,
`eye_right`, `pelvic_fins`; `wing_left`, `wing_right` (`wing_left_pivot`,
`wing_right_pivot`, at the wing roots, to flap about Y); `tail`,
`tail_dorsal_fin` (`tail_pivot`).

Fins, flippers and wings are lofted plates whose outline is the silhouette;
fine outlines and markings go in the texture later. The materials are flat
stand-ins by surface, two or three an animal (a skin, a pale belly where the
animal is countershaded, dark eyes). No part carries a `kyt_unwrap` hint: these
are lofted organic shapes. Budgets: the seal 2,500 triangles, the shark 1,500,
the ray 1,200.
"""

import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

TAU = math.tau
X, Y, Z = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0))
ANIMALS = ("harbor_seal", "leopard_shark", "bat_ray")
BUDGET = {"harbor_seal": 2500, "leopard_shark": 1500, "bat_ray": 1200}

# colours are stand-ins for the painting
SEAL_COAT = (0.25, 0.245, 0.23, 1.0)      # grey; the spots and rings are paint
SEAL_DARK = (0.05, 0.05, 0.05, 1.0)      # eyes and nose
SHARK_SKIN = (0.23, 0.20, 0.16, 1.0)     # bronze-grey; the saddles are paint
SHARK_BELLY = (0.74, 0.71, 0.63, 1.0)
SHARK_EYE = (0.06, 0.06, 0.05, 1.0)
RAY_SKIN = (0.14, 0.12, 0.09, 1.0)       # dark olive-brown back
RAY_BELLY = (0.90, 0.89, 0.86, 1.0)
RAY_EYE = (0.04, 0.04, 0.04, 1.0)


# --- building blocks -------------------------------------------------------

def material(name, colour, rough=0.75):
    """A stand-in material; its colour is reset on every run."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Roughness"].default_value = rough
    mat.diffuse_color = colour
    return mat


def export():
    return bpy.data.collections["export"]


class Mesher:
    """A bmesh whose vertices weld by position, so a loft ring that shrinks to
    a point (a pole) or to a line (a thin edge) closes itself."""

    def __init__(self):
        self.bm = bmesh.new()
        self.cache = {}

    def v(self, p):
        key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
        vert = self.cache.get(key)
        if vert is None:
            vert = self.bm.verts.new(p)
            self.cache[key] = vert
        return vert

    def face(self, verts):
        out = []
        for v in verts:
            if not out or out[-1] is not v:
                out.append(v)
        while len(out) > 1 and out[0] is out[-1]:
            out.pop()
        if len(out) < 3 or len(set(out)) != len(out):
            return None
        try:
            return self.bm.faces.new(out)
        except ValueError:
            return None


def loft(m, rings, cap_first=False, cap_last=False):
    """Faces between successive rings of points; a ring of one point is a
    pole. Rings of equal length, all wound the same way."""
    vr = [[m.v(p) for p in ring] for ring in rings]
    for a, b in zip(vr, vr[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        n = max(len(a), len(b))
        for k in range(n):
            j = (k + 1) % n
            if len(a) == 1:
                m.face((a[0], b[j], b[k]))
            elif len(b) == 1:
                m.face((a[k], a[j], b[0]))
            else:
                m.face((a[k], a[j], b[j], b[k]))
    if cap_first and len(vr[0]) > 2:
        m.face(list(reversed(vr[0])))
    if cap_last and len(vr[-1]) > 2:
        m.face(vr[-1])


def ring(centre, a, bt, bb, sides, pt=2.0, pb=2.0, u=X, w=Z):
    """A section `a` wide each side, `bt` above and `bb` below its centre, a
    superellipse of power `pt` above and `pb` below (2 is an ellipse, more is
    squarer: a belly flattened on the sand)."""
    pts = []
    for k in range(sides):
        th = TAU * k / sides
        c, s = math.cos(th), math.sin(th)
        e = 2.0 / (pt if s >= 0 else pb)
        cu = math.copysign(abs(c) ** e, c)
        sw = math.copysign(abs(s) ** e, s)
        pts.append(Vector(centre) + u * (a * cu) + w * ((bt if s >= 0 else bb) * sw))
    return pts


def body_loft(m, front, stations, back, sides, pt=2.0):
    """A body along Y from the pole `front` to the pole `back` through
    stations (y, half-width, bottom z, widest z, top z, belly power)."""
    rings = [[Vector(front)]]
    for y, a, bot, wid, top, pb in stations:
        rings.append(ring((0.0, y, wid), a, top - wid, wid - bot, sides, pt, pb))
    rings.append([Vector(back)])
    loft(m, rings)


def surface_bottom(stations, x, y):
    """The underside of a `body_loft` at (x, y): z, by its stations."""
    for (y0, a0, b0, w0, t0, p0), (y1, a1, b1, w1, t1, p1) in zip(stations, stations[1:]):
        if y0 <= y <= y1:
            f = (y - y0) / (y1 - y0)
            a, bot, wid, pb = a0 + (a1 - a0) * f, b0 + (b1 - b0) * f, w0 + (w1 - w0) * f, p0 + (p1 - p0) * f
            r = min(abs(x) / a, 1.0) ** pb
            return wid - (wid - bot) * (1.0 - r) ** (1.0 / pb)
    raise ValueError(f"y {y} outside the stations")


def surface_side(stations, y, z):
    """The side of a `body_loft` at height z over (0, y): its x, by its stations."""
    for (y0, a0, b0, w0, t0, p0), (y1, a1, b1, w1, t1, p1) in zip(stations, stations[1:]):
        if min(y0, y1) <= y <= max(y0, y1):
            f = (y - y0) / (y1 - y0)
            a, bot, wid, top, pb = (a0 + (a1 - a0) * f, b0 + (b1 - b0) * f, w0 + (w1 - w0) * f,
                                    t0 + (t1 - t0) * f, p0 + (p1 - p0) * f)
            b, p = (top - wid, 2.0) if z >= wid else (wid - bot, pb)
            r = min(abs(z - wid) / b, 1.0) ** p
            return a * (1.0 - r) ** (1.0 / p)
    raise ValueError(f"y {y} outside the stations")


def foil(m, lead, trail, thick, normal, sides=8, lag=None, cap_root=True):
    """A fin, flipper or wing lofted along its span: at each station a lens
    from `lead` to `trail` (its chord) `thick` thick each side along `normal`.
    A station whose lead and trail meet with no thickness is the tip's point;
    one with no thickness is a sharp edge. `lag` holds the middle of a station
    back along the span by that much (the notch between a flipper's toes)."""
    n = len(lead)
    centres = [(Vector(a) + Vector(b)) / 2 for a, b in zip(lead, trail)]
    rings = []
    cd_prev = None
    for i in range(n):
        L, T = Vector(lead[i]), Vector(trail[i])
        chord = T - L
        hc = chord.length / 2
        cd = chord.normalized() if hc > 1e-7 else cd_prev
        cd_prev = cd
        nd = Vector(normal)
        td = (nd - cd * nd.dot(cd)).normalized()
        sd = (centres[min(i + 1, n - 1)] - centres[max(i - 1, 0)]).normalized()
        pts = []
        for k in range(sides):
            th = TAU * k / sides
            c, s = math.cos(th), math.sin(th)
            p = centres[i] + cd * (hc * c) + td * (thick[i] * s)
            if lag:
                p = p - sd * (lag[i] * (1.0 - c * c))
            pts.append(p)
        rings.append(pts)
    loft(m, rings, cap_first=cap_root)


def ellipsoid(m, centre, radii, sides=10, rings=6, axis=None):
    """An egg of half-sizes `radii` (x, y, z) at `centre`; `axis`, if given,
    turns its z half-size to point along that direction."""
    rot = axis.to_track_quat("Z", "Y").to_matrix() if axis is not None else None
    out = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        r, z = math.sin(phi), -math.cos(phi)
        if r < 1e-6:
            pts = [Vector((0.0, 0.0, z * radii[2]))]
        else:
            pts = [Vector((radii[0] * r * math.cos(TAU * k / sides), radii[1] * r * math.sin(TAU * k / sides), z * radii[2]))
                   for k in range(sides)]
        out.append([Vector(centre) + (rot @ p if rot is not None else p) for p in pts])
    loft(m, out)


def tube(m, points, radii, sides=6, cap_start=True):
    """A round tube along a polyline, its radius per point; a last radius of
    0 is a pole, any other end is capped flat."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        t = pts[1] - pts[0] if i == 0 else pts[-1] - pts[-2] if i == n - 1 else pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    ref = Z if abs(tangents[0].z) < 0.9 else X
    nrm = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    rings = []
    for i in range(n):
        if i > 0:
            nrm = tangents[i - 1].rotation_difference(tangents[i]) @ nrm
            nrm = (nrm - tangents[i] * nrm.dot(tangents[i])).normalized()
        bi = tangents[i].cross(nrm).normalized()
        if radii[i] < 1e-7:
            rings.append([pts[i]])
        else:
            rings.append([pts[i] + radii[i] * (math.cos(TAU * k / sides) * nrm + math.sin(TAU * k / sides) * bi)
                          for k in range(sides)])
    loft(m, rings, cap_first=cap_start, cap_last=len(rings[-1]) > 1)


def world_location(obj):
    """A pivot's world position: pivots are never rotated or scaled, so it is
    the sum of the locations up its chain."""
    loc = Vector((0.0, 0.0, 0.0))
    while obj is not None:
        loc += Vector(obj.location)
        obj = obj.parent
    return loc


def pivot(name, at, parent=None):
    """An empty at the joint `at` (world), under `parent` if given."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SPHERE"
    e.empty_display_size = 0.04
    export().objects.link(e)
    e.parent = parent
    e.location = Vector(at) - (world_location(parent) if parent is not None else Vector((0.0, 0.0, 0.0)))
    return e


def new_object(name, m, mats, *, under=None, smooth_deg=60.0, belly_below=None):
    """Finish a Mesher (built in world coordinates) into an object in
    `export`. Under a pivot, the vertices move into the pivot's frame so the
    pivot turns the part about its joint. With two materials, faces whose
    normal points down past `belly_below` take the second (the pale belly)."""
    bm = m.bm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if under is not None:
        bmesh.ops.translate(bm, verts=bm.verts, vec=-world_location(under))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    export().objects.link(obj)
    mats = mats if isinstance(mats, (list, tuple)) else [mats]
    for mat in mats:
        obj.data.materials.append(mat)
    if under is not None:
        obj.parent = under
    clean(obj)
    smooth_by_angle(obj, smooth_deg)
    if belly_below is not None and len(mats) > 1:
        for poly in obj.data.polygons:
            poly.material_index = 1 if poly.normal.z < belly_below else 0
    obj["kyt_collision"] = "none"
    return obj


def clean(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bad = [f for f in bm.faces if f.calc_area() < 1e-10]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def smooth_by_angle(obj, deg):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(deg))
    bm.to_mesh(mesh)
    bm.free()


def bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
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


def lerp(a, b, f):
    return Vector(a) + (Vector(b) - Vector(a)) * f


def mirror(p):
    return Vector((-p[0], p[1], p[2]))


# --- the harbor seal ----------------------------------------------------------
#
# Built nose toward -Y about where it ends up; `settle` then centres it. The
# body's stations are (y, half-width, bottom, widest, top, belly power): the
# belly is flat on the sand under the chest and middle (power 3), rounder at
# the neck and tail, and the section is widest low down, a slumped sausage.

SEAL_BODY = [
    (-0.56, 0.115, 0.140, 0.245, 0.355, 2.0),
    (-0.48, 0.150, 0.072, 0.210, 0.375, 2.2),
    (-0.38, 0.198, 0.020, 0.170, 0.374, 2.6),
    (-0.27, 0.235, 0.000, 0.150, 0.372, 3.0),
    (-0.14, 0.258, 0.000, 0.140, 0.372, 3.2),
    (0.00, 0.266, 0.000, 0.135, 0.358, 3.2),
    (0.13, 0.250, 0.000, 0.130, 0.333, 3.0),
    (0.25, 0.210, 0.004, 0.125, 0.292, 2.8),
    (0.36, 0.160, 0.020, 0.120, 0.243, 2.5),
    (0.46, 0.108, 0.045, 0.120, 0.196, 2.2),
    (0.54, 0.070, 0.070, 0.124, 0.166, 2.0),
    (0.60, 0.042, 0.090, 0.128, 0.155, 2.0),
]
SEAL_BODY_FRONT = (0.0, -0.60, 0.245)
SEAL_BODY_BACK = (0.0, 0.64, 0.126)
SEAL_NECK = (0.0, -0.52, 0.25)          # head_pivot
# The head, raised a little: the crown at 0.41 m, the chin 0.2 m off the sand.
SEAL_HEAD = [
    (-0.500, 0.090, 0.150, 0.245, 0.335, 2.0),   # inside the neck: the head grows out of it
    (-0.535, 0.115, 0.145, 0.258, 0.372, 2.0),
    (-0.570, 0.132, 0.150, 0.268, 0.398, 2.0),
    (-0.620, 0.138, 0.162, 0.275, 0.410, 2.0),
    (-0.670, 0.124, 0.177, 0.280, 0.400, 2.0),
    (-0.715, 0.100, 0.193, 0.275, 0.372, 2.0),   # the stop, under the brow
    (-0.750, 0.093, 0.203, 0.270, 0.337, 2.4),   # the whisker pads, broad
    (-0.790, 0.083, 0.213, 0.265, 0.316, 2.4),
    (-0.820, 0.062, 0.223, 0.262, 0.302, 2.2),
    (-0.840, 0.033, 0.238, 0.262, 0.290, 2.0),
]
SEAL_HEAD_BACK = (0.0, -0.47, 0.25)
SEAL_NOSE_TIP = (0.0, -0.848, 0.264)
SEAL_EYE = (-0.695, 0.335)             # y, z; set into the head's side surface
SEAL_EYE_R = 0.029
SEAL_SHOULDER = (0.18, -0.29, 0.10)     # flipper_front_*_pivot (x mirrored)
SEAL_FORE_LEN = 0.20                    # root to tip; about 0.13 shows
SEAL_FORE_SPLAY = 38.0                  # degrees out from straight back
SEAL_ANKLE = (0.035, 0.58, 0.115)       # flipper_rear_*_pivot (x mirrored)
SEAL_HIND_LEN = 0.30
SEAL_HIND_SPLAY, SEAL_HIND_RISE, SEAL_HIND_TILT = 13.0, 10.0, 12.0


def seal_fore_flipper(side):
    """A short flat paddle from the shoulder back and out, lying on the sand,
    its tip rounded (the five claws are paint)."""
    sx = 1.0 if side == "left" else -1.0
    root = Vector((sx * SEAL_SHOULDER[0], SEAL_SHOULDER[1], SEAL_SHOULDER[2]))
    a = math.radians(SEAL_FORE_SPLAY)
    along = Vector((sx * math.sin(a), math.cos(a), 0.0))
    across = Vector((along.y, -along.x, 0.0))
    us = (0.0, 0.2, 0.4, 0.6, 0.75, 0.86, 0.94, 1.0)
    lead, trail, thick = [], [], []
    for u in us:
        c = root + along * (SEAL_FORE_LEN * u)
        c.z = SEAL_SHOULDER[2] - 0.082 * u ** 0.7     # down onto the sand
        w = 0.030 + 0.016 * u
        if u > 0.72:
            w *= math.sqrt(max(0.0, 1.0 - ((u - 0.72) / 0.28) ** 2))
        t = 0.026 - 0.016 * u if u < 1.0 else 0.0
        lead.append(c - across * w)
        trail.append(c + across * w)
        thick.append(t)
    m = Mesher()
    foil(m, lead, trail, thick, Z, sides=10)
    return m


def seal_hind_flipper(side):
    """A fan from the ankle straight back, the toes' webbing spread with a
    notch in the middle of its end (the outer toes longest), the tip lifted a
    little off the sand and the inner edge tipped up."""
    sx = 1.0 if side == "left" else -1.0
    root = Vector((sx * SEAL_ANKLE[0], SEAL_ANKLE[1], SEAL_ANKLE[2]))
    sp, ri, ti = (math.radians(v) for v in (SEAL_HIND_SPLAY, SEAL_HIND_RISE, SEAL_HIND_TILT))
    along = Vector((sx * math.sin(sp) * math.cos(ri), math.cos(sp) * math.cos(ri), math.sin(ri)))
    flat = Vector((sx * math.cos(sp), -math.sin(sp), 0.0))       # outward, level
    across = (flat * math.cos(ti) - Z * math.sin(ti)).normalized()  # outer edge down
    us = (-0.06, 0.1, 0.28, 0.46, 0.62, 0.76, 0.86, 0.94, 1.0)
    lead, trail, thick, lag = [], [], [], []
    for u in us:
        c = root + along * (SEAL_HIND_LEN * u)
        w = 0.024 if u < 0 else 0.036 + 0.066 * u ** 1.2
        if u > 0.8:   # the outer toes end round, not in points
            w *= math.sqrt(1.0 - 0.5 * ((u - 0.8) / 0.2) ** 2)
        t = 0.026 if u < 0 else 0.030 - 0.020 * u
        lead.append(c - across * w)
        trail.append(c + across * w)
        thick.append(t if u < 1.0 else 0.0)
        lag.append(0.032 * max(u, 0.0) ** 4)
    m = Mesher()
    foil(m, lead, trail, thick, Z, sides=12, lag=lag)
    return m


def build_seal():
    coat = material("seal_coat", SEAL_COAT)
    dark = material("seal_eye_nose", SEAL_DARK, rough=0.3)
    m = Mesher()
    body_loft(m, SEAL_BODY_FRONT, SEAL_BODY, SEAL_BODY_BACK, sides=20)
    new_object("body", m, coat)

    head_pv = pivot("head_pivot", SEAL_NECK)
    m = Mesher()
    body_loft(m, SEAL_HEAD_BACK, SEAL_HEAD, SEAL_NOSE_TIP, sides=18)
    new_object("head", m, coat, under=head_pv)
    m = Mesher()
    ellipsoid(m, (0.0, -0.834, 0.297), (0.027, 0.017, 0.016), sides=10, rings=5)
    new_object("nose", m, dark, under=head_pv)
    for side, sx in (("left", 1.0), ("right", -1.0)):
        m = Mesher()
        y, z = SEAL_EYE
        c = Vector((sx * (surface_side(SEAL_HEAD, y, z) - 0.5 * SEAL_EYE_R), y, z))
        out = Vector((sx * 0.8, -0.55, 0.2)).normalized()
        ellipsoid(m, c, (SEAL_EYE_R, SEAL_EYE_R, SEAL_EYE_R * 0.8), sides=10, rings=6, axis=out)
        new_object(f"eye_{side}", m, dark, under=head_pv)

    for side, sx in (("left", 1.0), ("right", -1.0)):
        pv = pivot(f"flipper_front_{side}_pivot", (sx * SEAL_SHOULDER[0], SEAL_SHOULDER[1], SEAL_SHOULDER[2]))
        new_object(f"flipper_front_{side}", seal_fore_flipper(side), coat, under=pv)
    for side, sx in (("left", 1.0), ("right", -1.0)):
        pv = pivot(f"flipper_rear_{side}_pivot", (sx * SEAL_ANKLE[0], SEAL_ANKLE[1], SEAL_ANKLE[2]))
        new_object(f"flipper_rear_{side}", seal_hind_flipper(side), coat, under=pv)


def checks_seal():
    out = []
    head = bpy.data.objects["head"]
    lo, hi = bounds([head])
    out.append(f"head {hi.x - lo.x:.3f} wide, crown at {hi.z:.3f} m, chin at {lo.z:.3f} m off the sand")
    for side in ("left", "right"):
        f = bpy.data.objects[f"flipper_front_{side}"]
        flo, fhi = bounds([f])
        out.append(f"fore flipper {side}: lowest {flo.z * 1000:.1f} mm, reaches x {flo.x:.3f}..{fhi.x:.3f}")
        r = bpy.data.objects[f"flipper_rear_{side}"]
        rlo, rhi = bounds([r])
        out.append(f"hind flipper {side}: lowest {rlo.z * 1000:.1f} mm, tip at y {rhi.y:.3f}")
    out.append("no ear flaps: the ear holes are paint")
    return out


# --- the leopard shark --------------------------------------------------------
#
# Total length 1.40 m, the snout at y = -0.70 and the upper tail lobe's tip at
# +0.70, built about z = 0.1 and settled onto z = 0 by its lowest point. One
# profile runs from the snout to the tail stock, (y, half-width, bottom,
# widest, top, belly power): a depressed head wider than deep, a back rising to
# the first dorsal, a flattish belly. `split_body` cuts it at the tail's joint.

SHARK_PROFILE = [
    (-0.690, 0.026, 0.083, 0.095, 0.106, 2.0),
    (-0.670, 0.048, 0.070, 0.093, 0.118, 2.2),
    (-0.635, 0.068, 0.058, 0.092, 0.132, 2.4),
    (-0.580, 0.082, 0.048, 0.092, 0.148, 2.4),
    (-0.500, 0.090, 0.042, 0.094, 0.163, 2.4),
    (-0.400, 0.094, 0.040, 0.097, 0.175, 2.4),
    (-0.280, 0.095, 0.040, 0.100, 0.183, 2.4),
    (-0.150, 0.090, 0.043, 0.102, 0.185, 2.4),
    (-0.030, 0.080, 0.050, 0.104, 0.180, 2.3),
    (0.070, 0.068, 0.058, 0.106, 0.170, 2.2),
    (0.160, 0.056, 0.068, 0.110, 0.157, 2.2),
    (0.220, 0.046, 0.076, 0.111, 0.148, 2.2),
    (0.290, 0.036, 0.085, 0.113, 0.141, 2.1),
    (0.360, 0.026, 0.093, 0.115, 0.136, 2.0),
    (0.420, 0.019, 0.099, 0.117, 0.134, 2.0),
    (0.470, 0.012, 0.104, 0.118, 0.131, 2.0),
]
SHARK_NOSE = (0.0, -0.700, 0.095)
SHARK_TAIL_END = (0.0, 0.500, 0.118)
SHARK_TAIL_JOINT_Y = 0.100                # tail_pivot, just behind the pelvics
SHARK_CAUDAL_JOINT = (0.0, 0.400, 0.116)  # caudal_pivot, at the tail stock
SHARK_CAUDAL_BASE = (0.0, 0.385, 0.124)   # the upper lobe's dorsal margin starts here
SHARK_TIP = (0.0, 0.700, 0.205)           # and ends at the tip
# The caudal fin's depth below that margin, square to it, along it (0 at the
# base, 1 at the tip): the small lower lobe's point at 0.345, the notch under
# the tip at 0.8 and the terminal lobe at 0.9.
SHARK_CAUDAL_DEPTH = [(0.0, 0.030), (0.112, 0.042), (0.2, 0.075), (0.28, 0.108), (0.325, 0.126),
                      (0.345, 0.131), (0.365, 0.124), (0.4, 0.098), (0.44, 0.070), (0.484, 0.050),
                      (0.58, 0.040), (0.68, 0.032), (0.76, 0.022), (0.8, 0.020), (0.86, 0.029),
                      (0.9, 0.031), (0.95, 0.019), (1.0, 0.0)]
SHARK_JAW_JOINT = (0.0, -0.585, 0.058)    # jaw_pivot, between the mouth's corners
SHARK_PECTORAL_ROOT = (0.075, -0.430, 0.068)


def station_at(stations, y):
    for s0, s1 in zip(stations, stations[1:]):
        if s0[0] <= y <= s1[0]:
            f = (y - s0[0]) / (s1[0] - s0[0])
            return tuple(a + (b - a) * f for a, b in zip(s0, s1))
    raise ValueError(f"y {y} outside the stations")


def scaled(st, k):
    """A station grown or shrunk by k about its widest line."""
    y, a, bot, wid, top, pb = st
    return (y, a * k, wid - (wid - bot) * k, wid, wid + (top - wid) * k, pb)


def split_body(stations, front, back, joint_y, sides):
    """One profile as two lofts meeting at `joint_y`, so the back one can
    turn: the front closes in a dome just behind the joint, hidden in the
    back, whose rim there is 2.5% larger and whose own dome hides in the
    front. The same sides on both, so the seam is one clean ring."""
    fm = Mesher()
    head = [s for s in stations if s[0] < joint_y - 1e-6] + [station_at(stations, joint_y)]
    dome = [scaled(station_at(stations, joint_y + d), k) for d, k in ((0.02, 0.85), (0.035, 0.55))]
    pole = (0.0, joint_y + 0.045, station_at(stations, joint_y + 0.045)[3])
    body_loft(fm, front, head + dome, pole, sides)
    bm = Mesher()
    lead_in = [scaled(station_at(stations, joint_y + d), k) for d, k in ((-0.03, 0.55), (-0.015, 0.88))]
    pole = (0.0, joint_y - 0.04, station_at(stations, joint_y - 0.04)[3])
    rest = [scaled(s, 1.0 + 0.025 * max(0.0, 1.0 - (s[0] - joint_y) / 0.06)) for s in stations if s[0] > joint_y + 1e-6]
    body_loft(bm, pole, lead_in + [scaled(station_at(stations, joint_y), 1.025)] + rest, back, sides)
    return fm, bm


def round_tip(lead, trail, us, start):
    """Narrow each chord past `start` along the span as a quarter circle, so
    a fin ends round, not in a point."""
    for i, u in enumerate(us):
        if u > start:
            k = math.sqrt(max(0.0, 1.0 - ((u - start) / (1.0 - start)) ** 2))
            mid = (lead[i] + trail[i]) / 2
            lead[i], trail[i] = mid + (lead[i] - mid) * k, mid + (trail[i] - mid) * k


def shark_fin_vertical(base_lead, base_trail, apex, us, thick0, lead_pow=1.5, trail_pow=0.6, round_from=0.7):
    """A dorsal or anal fin in the YZ plane: the leading edge convex from its
    base to the apex, the trailing edge concave, the apex rounded."""
    lead, trail, thick = [], [], []
    bl, bt, ap = Vector(base_lead), Vector(base_trail), Vector(apex)
    for u in us:
        lead.append(Vector((0.0, bl.y + (ap.y - bl.y) * u ** lead_pow, bl.z + (ap.z - bl.z) * u)))
        trail.append(Vector((0.0, bt.y + (ap.y - bt.y) * u ** trail_pow, bt.z + (ap.z - bt.z) * u)))
        thick.append((thick0 + 0.002) * (1.0 - u) ** 0.8)
    round_tip(lead, trail, us, round_from)
    return lead, trail, thick


def build_shark():
    skin = material("shark_skin", SHARK_SKIN)
    belly = material("shark_belly", SHARK_BELLY)
    eye = material("shark_eye", SHARK_EYE, rough=0.3)
    front, back = split_body(SHARK_PROFILE, SHARK_NOSE, SHARK_TAIL_END, SHARK_TAIL_JOINT_Y, 12)
    new_object("body", front, [skin, belly], belly_below=-0.45)

    for side, sx in (("left", 1.0), ("right", -1.0)):
        m = Mesher()
        y, z = -0.600, 0.112
        c = Vector((sx * (surface_side(SHARK_PROFILE, y, z) - 0.006), y, z))
        out = Vector((sx * 0.9, -0.25, 0.25)).normalized()
        ellipsoid(m, c, (0.016, 0.022, 0.012), sides=8, rings=4, axis=out)
        new_object(f"eye_{side}", m, eye)

    # the first dorsal: over the gap between the pectorals and the pelvics
    lead, trail, thick = shark_fin_vertical((0.0, -0.170, 0.172), (0.0, -0.022, 0.176), (0.0, -0.080, 0.288),
                                            (0.0, 0.3, 0.55, 0.72, 0.84, 0.93, 1.0), 0.016)
    m = Mesher()
    foil(m, lead, trail, thick, X, sides=8)
    new_object("dorsal_fin_first", m, skin)

    # the pelvic fins, under the body, down and back
    for side, sx in (("left", 1.0), ("right", -1.0)):
        root_lead = Vector((sx * 0.028, 0.000, 0.066))
        root_trail = Vector((sx * 0.028, 0.085, 0.070))
        tip = Vector((sx * 0.080, 0.135, 0.033))
        us = (0.0, 0.35, 0.7, 1.0)
        lead = [lerp(root_lead, tip, u) for u in us]
        trail = [lerp(root_trail, tip, u ** 0.7) for u in us]
        m = Mesher()
        foil(m, lead, trail, [0.012 * (1 - u) for u in us], Vector((sx * 0.6, 0.0, 1.0)), sides=6)
        new_object(f"pelvic_fin_{side}", m, skin)

    jaw_pv = pivot("jaw_pivot", SHARK_JAW_JOINT)
    pts = []
    for i in range(5):
        t = math.radians(-90.0 + 180.0 * i / 4)
        x, y = 0.052 * math.sin(t), -0.585 - 0.058 * math.cos(t)
        pts.append((x, y, surface_bottom(SHARK_PROFILE, x, y) - 0.001))
    m = Mesher()
    tube(m, pts, [0.0075] * 5, sides=6)
    new_object("jaw", m, belly, under=jaw_pv)

    for side, sx in (("left", 1.0), ("right", -1.0)):
        pv = pivot(f"pectoral_{side}_pivot", (sx * SHARK_PECTORAL_ROOT[0], SHARK_PECTORAL_ROOT[1], SHARK_PECTORAL_ROOT[2]))
        us = (0.0, 0.2, 0.4, 0.55, 0.7, 0.82, 0.92, 1.0)
        lead, trail, thick = [], [], []
        for u in us:
            x = sx * (0.055 + 0.180 * u)
            z = 0.068 - 0.046 * u
            lead.append(Vector((x, -0.445 + 0.135 * u ** 1.35, z)))
            trail.append(Vector((x, -0.340 + 0.030 * u ** 0.8, z)))
            thick.append(0.016 * (1.0 - u) ** 0.8)
        round_tip(lead, trail, us, 0.55)
        normal = Vector((sx * 0.046, 0.0, 0.180)).normalized()
        m = Mesher()
        foil(m, lead, trail, thick, normal, sides=8)
        new_object(f"pectoral_fin_{side}", m, [skin, belly], under=pv, belly_below=-0.6)

    tail_pv = pivot("tail_pivot", (0.0, SHARK_TAIL_JOINT_Y, station_at(SHARK_PROFILE, SHARK_TAIL_JOINT_Y)[3]))
    new_object("tail", back, [skin, belly], under=tail_pv, belly_below=-0.45)
    lead, trail, thick = shark_fin_vertical((0.0, 0.190, 0.139), (0.0, 0.292, 0.134), (0.0, 0.266, 0.220),
                                            (0.0, 0.35, 0.65, 0.82, 0.93, 1.0), 0.013)
    m = Mesher()
    foil(m, lead, trail, thick, X, sides=8)
    new_object("dorsal_fin_second", m, skin, under=tail_pv)
    lead, trail, thick = shark_fin_vertical((0.0, 0.272, 0.093), (0.0, 0.352, 0.100), (0.0, 0.336, 0.048),
                                            (0.0, 0.4, 0.75, 0.92, 1.0), 0.010)
    m = Mesher()
    foil(m, lead, trail, thick, X, sides=6)
    new_object("anal_fin", m, skin, under=tail_pv)

    # The caudal fin, one plate: sections square to the upper lobe's straight
    # dorsal margin, each reaching down to the outline in SHARK_CAUDAL_DEPTH.
    caudal_pv = pivot("caudal_pivot", SHARK_CAUDAL_JOINT, tail_pv)
    base, tip = Vector(SHARK_CAUDAL_BASE), Vector(SHARK_TIP)
    d = (tip - base).normalized()
    down = Vector((0.0, d.z, -d.y))
    lead, trail, thick = [], [], []
    for u, depth in SHARK_CAUDAL_DEPTH:
        a = lerp(base, tip, u)
        lead.append(a)
        trail.append(a + down * depth)
        thick.append(0.0 if u >= 1.0 else 0.003 + 0.011 * (1.0 - u) ** 1.2)
    m = Mesher()
    foil(m, lead, trail, thick, X, sides=8)
    new_object("caudal_fin", m, skin, under=caudal_pv)


def checks_shark():
    out = []
    for name in ("dorsal_fin_first", "dorsal_fin_second", "anal_fin", "caudal_fin"):
        lo, hi = bounds([bpy.data.objects[name]])
        out.append(f"{name}: y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.3f}..{hi.z:.3f}")
    lo, hi = bounds([bpy.data.objects["pectoral_fin_left"], bpy.data.objects["pectoral_fin_right"]])
    out.append(f"pectorals span {hi.x - lo.x:.3f} m, lowest {lo.z:.3f}")
    return out


# --- the bat ray --------------------------------------------------------------
#
# 1.20 m across the wings, the snout at y = -0.385, the tail's tip at +1.27,
# built about z = 0.06 and settled onto z = 0 by the belly. The body's stations
# are (y, half-width, bottom, widest, top, belly power): a raised head with a
# dome over the eyes, a dip behind them, the back high over the disc.

RAY_BODY = [
    (-0.375, 0.045, 0.045, 0.070, 0.095, 2.0),
    (-0.350, 0.075, 0.030, 0.070, 0.110, 2.0),
    (-0.310, 0.092, 0.020, 0.068, 0.130, 2.2),
    (-0.260, 0.100, 0.015, 0.066, 0.136, 2.4),   # the head's dome, the eyes on its sides
    (-0.210, 0.110, 0.012, 0.062, 0.112, 2.6),   # the dip behind them
    (-0.140, 0.140, 0.010, 0.060, 0.115, 2.8),
    (-0.050, 0.160, 0.008, 0.058, 0.120, 3.0),
    (0.050, 0.160, 0.008, 0.058, 0.118, 3.0),
    (0.150, 0.145, 0.010, 0.058, 0.110, 2.8),
    (0.250, 0.110, 0.015, 0.058, 0.098, 2.6),
    (0.330, 0.075, 0.025, 0.058, 0.088, 2.2),
    (0.400, 0.042, 0.035, 0.058, 0.080, 2.0),
]
RAY_SNOUT = (0.0, -0.385, 0.070)
RAY_BODY_END = (0.0, 0.440, 0.058)
RAY_HALF_SPAN = 0.60
RAY_WING_ROOT_X = 0.04
RAY_WING_JOINT = (0.130, 0.060, 0.058)    # wing_*_pivot (x mirrored), at the body's edge
RAY_TAIL_JOINT = (0.0, 0.400, 0.058)      # tail_pivot
RAY_TAIL_TIP_Y = 1.27
RAY_EYE_AT = (-0.262, 0.100)          # y, z; set into the head's side surface


def ray_wing(sx):
    """The wing from inside the body out to its pointed tip: the leading edge
    convex, the trailing edge concave, thickest at the root, the tip lifted a
    little."""
    us = (0.0, 0.12, 0.25, 0.4, 0.55, 0.7, 0.82, 0.92, 1.0)
    lead, trail, thick = [], [], []
    for u in us:
        x = sx * (RAY_WING_ROOT_X + (RAY_HALF_SPAN - RAY_WING_ROOT_X) * u)
        z = 0.058 + 0.030 * u ** 2
        ly = -0.250 + 0.300 * u ** 1.6
        ty = 0.360 - 0.310 * u ** 0.65
        lead.append(Vector((x, ly, z)))
        trail.append(Vector((x, ty, z)))
        thick.append(0.040 * (1.0 - u) ** 0.9 if u < 1.0 else 0.0)
    m = Mesher()
    foil(m, lead, trail, thick, Z, sides=10)
    return m


def build_ray():
    skin = material("ray_skin", RAY_SKIN)
    belly = material("ray_belly", RAY_BELLY)
    eye = material("ray_eye", RAY_EYE, rough=0.3)
    m = Mesher()
    body_loft(m, RAY_SNOUT, RAY_BODY, RAY_BODY_END, sides=14)
    new_object("body", m, [skin, belly], belly_below=-0.6)
    for side, sx in (("left", 1.0), ("right", -1.0)):
        m = Mesher()
        out = Vector((sx * 0.9, -0.2, 0.35)).normalized()
        y, z = RAY_EYE_AT
        c = Vector((sx * (surface_side(RAY_BODY, y, z) - 0.008), y, z))
        ellipsoid(m, c, (0.019, 0.019, 0.015), sides=8, rings=4, axis=out)
        new_object(f"eye_{side}", m, eye)

    # the pelvic fins: two rounded flaps behind the wings, low on the body
    m = Mesher()
    for sx in (-1.0, 1.0):
        us = (0.0, 0.35, 0.65, 0.85, 1.0)
        lead, trail, thick = [], [], []
        for u in us:
            x = sx * (0.03 + 0.08 * u)
            mid = 0.370 + 0.035 * u
            half = 0.045 * math.sqrt(max(0.0, 1.0 - u ** 3))
            lead.append(Vector((x, mid - half, 0.030)))
            trail.append(Vector((x, mid + half, 0.030)))
            thick.append(0.013 * (1.0 - u) + 0.004 * (1.0 - u))
        foil(m, lead, trail, thick, Z, sides=8)
    new_object("pelvic_fins", m, [skin, belly], belly_below=-0.3)

    for side, sx in (("left", 1.0), ("right", -1.0)):
        pv = pivot(f"wing_{side}_pivot", (sx * RAY_WING_JOINT[0], RAY_WING_JOINT[1], RAY_WING_JOINT[2]))
        new_object(f"wing_{side}", ray_wing(sx), [skin, belly], under=pv, belly_below=-0.3)

    tail_pv = pivot("tail_pivot", RAY_TAIL_JOINT)
    ys = (0.37, 0.43, 0.52, 0.65, 0.80, 0.95, 1.10, RAY_TAIL_TIP_Y)
    radii = (0.026, 0.021, 0.015, 0.011, 0.0085, 0.0062, 0.0042, 0.0)
    pts = [(0.0, y, 0.058 - 0.018 * ((y - 0.37) / (RAY_TAIL_TIP_Y - 0.37)) ** 2) for y in ys]
    m = Mesher()
    tube(m, pts, radii, sides=6)
    new_object("tail", m, skin, under=tail_pv)
    lead, trail, thick = [], [], []
    for u in (0.0, 0.5, 1.0):
        lead.append(Vector((0.0, 0.425 + 0.045 * u ** 1.4, 0.072 + 0.040 * u)))
        trail.append(Vector((0.0, 0.505 - 0.035 * u ** 0.6, 0.068 + 0.044 * u)))
        thick.append(0.007 * (1.0 - u))
    m = Mesher()
    foil(m, lead, trail, thick, X, sides=6)
    new_object("tail_dorsal_fin", m, skin, under=tail_pv)


def checks_ray():
    out = []
    lo, hi = bounds([bpy.data.objects["wing_left"], bpy.data.objects["wing_right"]])
    out.append(f"wingspan {hi.x - lo.x:.3f} m, wing tips up to z {hi.z:.3f}")
    lo, hi = bounds([bpy.data.objects["tail"]])
    out.append(f"tail y {lo.y:.3f}..{hi.y:.3f} ({hi.y - lo.y:.3f} m)")
    return out


BUILDERS = {"harbor_seal": (build_seal, checks_seal),
            "leopard_shark": (build_shark, checks_shark),
            "bat_ray": (build_ray, checks_ray)}


# --- the frame -------------------------------------------------------------------

def settle():
    """The lowest point exactly on z = 0 and the plan's bounding box centred
    on the origin, moving every root object of the animal (a root mesh by its
    vertices, so its origin stays at the world's)."""
    parts = [o for o in export().all_objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    shift = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    for o in [o for o in export().all_objects if o.parent is None]:
        if o.type == "MESH":
            for v in o.data.vertices:
                v.co += shift
            o.data.update()
        else:
            o.location += shift
    bpy.context.view_layer.update()
    return shift


def report(name):
    parts = [o for o in export().all_objects if o.type == "MESH"]
    pivots = [o for o in export().all_objects if o.type == "EMPTY"]
    lo, hi = bounds(parts)
    tris = triangles(parts)
    print(f"wildlife_lagoon_swimmers: {name}: {len(parts)} parts, {len(pivots)} pivots, {tris} triangles "
          f"(budget {BUDGET[name]}{', OVER' if tris > BUDGET[name] else ''})")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts))
    print("  pivots: " + ", ".join(o.name + (f" < {o.parent.name}" if o.parent else "")
                                   + f" at ({world_location(o).x:.3f}, {world_location(o).y:.3f}, {world_location(o).z:.3f})"
                                   for o in pivots))
    print(f"  size: {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x L x H), x {lo.x:.3f}..{hi.x:.3f}, "
          f"y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.4f}..{hi.z:.3f}")
    print("  materials: " + ", ".join(sorted({s.material.name for o in parts for s in o.material_slots})))
    for line in BUILDERS[name][1]():
        print("  " + line)


# --- rendering ---------------------------------------------------------------------

def stage_scene():
    """A review scene: EEVEE, a sky, a sun and a camera in a `_review`
    collection that is never saved."""
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
    world = bpy.data.worlds.new("_review")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.72, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    stage.objects.link(cam)
    scene.camera = cam
    return scene, stage, cam


def stage_mesh(stage, tag, verts, faces, colour):
    me = bpy.data.meshes.new(tag)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(tag, me)
    o.data.materials.append(material(f"_review_{tag}", colour))
    stage.objects.link(o)
    return o


def ground(stage, reach):
    return stage_mesh(stage, "ground", [(-reach, -reach, -0.001), (reach, -reach, -0.001), (reach, reach, -0.001),
                                        (-reach, reach, -0.001)], [(0, 1, 2, 3)], (0.62, 0.57, 0.46, 1))


def scale_box(stage):
    """The 1.7 m box, a guest's height, 0.45 by 0.28 m."""
    hx, hy, h = 0.225, 0.14, 1.7
    v = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0), (-hx, -hy, h), (hx, -hy, h), (hx, hy, h), (-hx, hy, h)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return stage_mesh(stage, "scale_box", v, f, (0.35, 0.35, 0.38, 1))


def mesh_points(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def shoot(scene, cam, path, objs, direction, target=None, lens=40, margin=0.05):
    """The camera along `direction` from the objects' centre, backed off
    until every vertex is in the picture."""
    pts = mesh_points(objs)
    lo, hi = Vector(map(min, *pts)), Vector(map(max, *pts))
    centre = (lo + hi) / 2 if target is None else Vector(target)
    d = Vector(direction).normalized()
    dist = max((hi - lo).length * 0.6, 0.4)
    cam.data.lens = lens
    for _ in range(90):
        cam.location = centre + d * dist
        cam.location.z = max(cam.location.z, 0.06)
        look = centre - cam.location
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if all(margin <= c.x <= 1 - margin and margin <= c.y <= 1 - margin and c.z > 0
               for c in (world_to_camera_view(scene, cam, p) for p in pts)):
            break
        dist *= 1.06
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def render(folder, name):
    os.makedirs(folder, exist_ok=True)
    for coll_name in ("reference", "authored"):
        c = bpy.data.collections.get(coll_name)
        if c is not None:
            c.hide_render = True
    scene, stage, cam = stage_scene()
    parts = [o for o in export().all_objects if o.type == "MESH"]
    floor = ground(stage, 30.0)
    box = scale_box(stage)
    box.hide_render = True
    views = (("three_quarter", (-0.75, -1.0, 0.55)), ("front", (0.0, -1.0, 0.15)),
             ("side", (1.0, 0.0, 0.12)), ("top", (0.0, -0.001, 1.0)))
    for tag, d in views:
        shoot(scene, cam, os.path.join(folder, f"{name}_{tag}.png"), parts, d)
    if name == "harbor_seal":
        head = [o for o in parts if o.parent is not None and o.parent.name == "head_pivot"]
        shoot(scene, cam, os.path.join(folder, f"{name}_head.png"), head, (-0.55, -1.0, 0.25), lens=50)
    # beside a 1.7 m tall box, a guest's height
    lo, hi = bounds(parts)
    box.hide_render = False
    box.location = (hi.x + 0.35 + 0.225, 0.0, 0.0)
    bpy.context.view_layer.update()
    shoot(scene, cam, os.path.join(folder, f"{name}_scale.png"), parts + [box], (-0.6, -1.0, 0.35))
    floor.hide_render = False


def lineup(path):
    """All three built in memory, side by side along X facing -Y, the 1.7 m
    box at the left. Nothing is saved."""
    for o in list(bpy.data.objects):     # the factory scene's cube, light and camera
        bpy.data.objects.remove(o)
    for coll_name in ("reference", "authored", "export"):
        if bpy.data.collections.get(coll_name) is None:
            bpy.context.scene.collection.children.link(bpy.data.collections.new(coll_name))
    scene, stage, cam = stage_scene()
    scene.render.resolution_x, scene.render.resolution_y = 2200, 1000
    ground(stage, 40.0)
    box = scale_box(stage)
    x = 0.225 + 0.5
    shown = [box]
    for name in ANIMALS:
        BUILDERS[name][0]()
        settle()
        objs = list(export().all_objects)
        root = bpy.data.objects.new(f"lineup_{name}", None)
        stage.objects.link(root)
        for o in objs:
            if o.parent is None:
                o.parent = root
            export().objects.unlink(o)
            stage.objects.link(o)
        meshes = [o for o in objs if o.type == "MESH"]
        lo, hi = bounds(meshes)
        root.location.x = x - lo.x
        bpy.context.view_layer.update()
        x += (hi.x - lo.x) + 0.5
        shown += meshes
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    shoot(scene, cam, os.path.abspath(path), shown, (-0.35, -1.0, 0.45), lens=45, margin=0.04)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--lineup" in argv:
        lineup(argv[argv.index("--lineup") + 1])
        return
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name not in BUILDERS:
        raise SystemExit(f"wildlife_lagoon_swimmers: open one of {', '.join(BUILDERS)}, not {name or 'an unsaved file'}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"wildlife_lagoon_swimmers: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for me in [me for me in bpy.data.meshes if me.users == 0]:
            bpy.data.meshes.remove(me)
    BUILDERS[name][0]()
    settle()
    report(name)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
