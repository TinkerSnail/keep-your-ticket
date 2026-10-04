"""The coast's five ambient animals, a first model pass (2026-10-03) for the
prop library's PRP-WILD-010 pelican, 011 sea lion, 012 sea otter, 023 whale and
024 dolphin, which Christina asked for on 2026-09-29. None has a photograph of
hers or a greybox: each is the plainest readable reading of the species in the
house style, chunky and rounded (`prop-pipeline.md`, Standards applied), for
her to reshape. Card: `documentation/howto/model-the-coast-animals.md`.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<animal>.blend --python tools/blender/wildlife_coast.py -- \\
        [--replace] [--save] [--render <folder>]

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \\
        --python tools/blender/wildlife_coast.py -- --lineup <png> [--gull]

`<animal>` is `pelican`, `sea_lion`, `sea_otter`, `whale` or `dolphin`. The
tool builds whichever the file is named for into `export`, one object a part,
real metres, Z up, the head toward -Y (+Z in Godot), the lowest point on z = 0
and the plan centred on the origin. It refuses while `export` holds anything
(it may be hers) unless `--replace`; it writes the file only with `--save`;
`--render` shoots three-quarter, front, side and top views, one beside a 1.7 m
box for scale and, for a swimmer, one with a water plane at its waterline,
into the folder (after the save, so the render rig never reaches the file).
`--lineup` builds all five in memory and renders them side by side at true
relative size beside the 1.7 m box, turned side-on so their lengths show
(`--gull` adds the adult gull from `assets/source/wildlife/gull_adult.blend`,
read only, at the 0.47 its Godot scene scales it by), and a second picture of
the small ones without the whale (`<png stem>_small.png`); nothing is saved in
that mode.

**Articulation.** Like the gull (`assets/source/wildlife/gull_adult.blend`),
every moving part is parented under an empty at its joint, named
`<part>_pivot`, with the part's vertices in that pivot's frame, so turning the
pivot swings the part. Pivots are never rotated or scaled. No armature, no
animation: how each moves is a separate decision. A pivot that rides on
another is its child (`head_pivot` under `neck_pivot`, `fluke_pivot` under
`tail_pivot`). Every part is `kyt_collision = none`: ambient wildlife never
blocks the player. Left and right are the animal's own: facing -Y and
upright, its left is +X; the otter lies on its back, so its left is -X.

**Pelican** (PRP-WILD-010): a brown pelican, adult, standing as on a pier
piling: the body tipped up 24 degrees at the breast, the neck a thick S with
the head drawn back over the shoulders, the bill pointing forward and 30
degrees down with the pouch slack under it, the wings folded along the back,
their tips crossing over the short tail. About 0.95 m bill tip to tail tip as
it stands (1.1 m stretched), 0.80 m to the crown, the bill 0.33 m with a
hooked nail. The feet straddle the origin. Its pivots carry the gull's
names, the ones `scenes/wildlife/bird.gd` looks up (and the lagoon birds
share): `head_pivot`, `upper_pivot`, `lower_pivot`, `wing_left`,
`wing_right`, `leg_left`, `leg_right`. Parts: `body`; `neck` (`neck_pivot`);
`head`, `eye_left`, `eye_right` (`head_pivot`, under the neck's);
`bill_upper` (`upper_pivot`); `bill_lower`, `pouch` (`lower_pivot`), both
under the head's; `folded_wing_left`, `folded_wing_right` (`wing_left`,
`wing_right`, at the shoulders); `tail` (`tail_pivot`); `shin_left`,
`foot_left` and their right twins (`leg_left`, `leg_right`, at the hips).

**Sea lion** (PRP-WILD-011): a California sea lion, adult female size, about
1.8 m nose to tail, hauled out: the chest raised on long fore flippers that
come down under the shoulders and lie flat on the ground pointing out and
back, the long neck up, the head lifted nose-up, small rolled ear flaps behind
the eyes, the hind flippers turned forward under the hips as only sea lions
(not seals) can. The body and neck are one smooth form; the head turns at the
top of the neck. 1.0 m to the crown. Parts: `body`; `head`, `nose`,
`ear_left`, `ear_right`, `eye_left`, `eye_right` (`head_pivot`); `jaw`
(`jaw_pivot`, under the head's); `flipper_front_left`, `flipper_front_right`,
`flipper_rear_left`, `flipper_rear_right`, each under its own `_pivot` at its
shoulder or hip.

**Sea otter** (PRP-WILD-012): a southern sea otter, about 1.1 m with the tail,
floating on its back: the head raised and looking down its own chest, the
forepaws held together on the chest, the broad hind flippers up out of the
water at the rear, the flat tail lying on the water. The back is the lowest
point; the waterline sits at z = 0.12, with the tail lying on it. Parts:
`body`; `head`, `muzzle`, `nose`, `ear_left`, `ear_right`, `eye_left`,
`eye_right` (`head_pivot`); `arm_left`, `paw_left` and right
(`arm_left_pivot`, `arm_right_pivot`); `flipper_left`, `flipper_right`
(`leg_left_pivot`, `leg_right_pivot`); `tail` (`tail_pivot`).

**Whale** (PRP-WILD-023): a gray whale, the coast's migrating whale, adult,
13 m, swimming level. No dorsal fin: a low dorsal hump and a row of knuckles
down the tail stock; a narrow head, triangular from above, its top sloping
down to the snout, the lower jaw a separate lip under it with the arched
mouth line; paddle flippers; flukes 3.4 m across. The belly is the lowest
point; the waterline is at z = 2.2, which leaves the back from the blowholes
to the hump out. Parts: `body`, `eye_left`, `eye_right`; `jaw` (`jaw_pivot`);
`flipper_left`, `flipper_right` (their pivots); `tail_stock` with its knuckles
(`tail_pivot`); `flukes` (`fluke_pivot`, under the tail's).

**Dolphin** (PRP-WILD-024): a common bottlenose dolphin, adult, 2.7 m,
swimming level: a round melon stepping down to a short beak, the lower jaw a
touch ahead of the upper, a falcate dorsal fin, flukes 0.68 m across, the pale
belly its own material. The belly is the lowest point; the waterline is at
z = 0.45, the back and the dorsal fin out. Parts: `body`, `dorsal_fin`,
`eye_left`, `eye_right`; `jaw` (`jaw_pivot`); `flipper_left`,
`flipper_right` (their pivots); `tail_stock` (`tail_pivot`); `flukes`
(`fluke_pivot`, under the tail's).

Fur, feathers, mottling, barnacles, markings, mouth lines and eye highlights
are paint. The materials are flat stand-ins by surface, two to four an animal,
their colours given as they should look (sRGB) and stored linear. No part
carries a `kyt_unwrap` hint: these are lofted organic shapes, which
`unwrap_parts.py` seams at their sharp edges and reports.
"""

import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

TAU = math.tau
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
ANIMALS = ("pelican", "sea_lion", "sea_otter", "whale", "dolphin")
SWIMMERS = {"sea_otter": 0.12, "whale": 2.2, "dolphin": 0.45}   # the waterline, z, for the render and the card
GULL_BLEND = os.path.join(ROOT, "assets", "source", "wildlife", "gull_adult.blend")
GULL_SCALE = 0.47    # scenes/wildlife/gull.tscn scales the GLB by this

# colours are stand-ins for the painting, as they should look (sRGB)
PELICAN_PLUMAGE = (0.45, 0.42, 0.39, 1.0)   # grey-brown body and wings
PELICAN_PALE = (0.95, 0.92, 0.80, 1.0)      # the adult's pale head and neck
PELICAN_BILL = (0.80, 0.69, 0.50, 1.0)      # horn
PELICAN_DARK = (0.20, 0.19, 0.19, 1.0)      # pouch, legs, feet, eyes
SEA_LION_COAT = (0.66, 0.51, 0.35, 1.0)     # golden tan (she is dry)
SEA_LION_DARK = (0.24, 0.19, 0.16, 1.0)     # flippers, nose, eyes
OTTER_FUR = (0.38, 0.28, 0.21, 1.0)
OTTER_HEAD = (0.72, 0.62, 0.49, 1.0)        # the grizzled head, paler than the body
OTTER_PALE = (0.86, 0.80, 0.68, 1.0)        # the whisker pads
OTTER_DARK = (0.17, 0.14, 0.12, 1.0)        # nose, eyes, paws, flippers
WHALE_SKIN = (0.40, 0.42, 0.44, 1.0)        # slate; the mottling is paint
WHALE_DARK = (0.10, 0.10, 0.11, 1.0)
DOLPHIN_BACK = (0.46, 0.50, 0.56, 1.0)
DOLPHIN_BELLY = (0.86, 0.87, 0.88, 1.0)
DOLPHIN_DARK = (0.10, 0.10, 0.11, 1.0)


# --- building blocks -------------------------------------------------------

def linear(colour):
    """An sRGB colour as Blender's shader inputs take it."""
    return tuple(c ** 2.2 if i < 3 else c for i, c in enumerate(colour))


def material(name, colour):
    """A stand-in material; its colour is reset on every run, so a rebuild
    shows the builder's colours even though a material survives --replace."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    lin = linear(colour)
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = lin
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.75
    mat.diffuse_color = lin
    return mat


def export():
    return bpy.data.collections["export"]


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


def new_object(name, bm, mats, *, under=None, bevel=0.0, segments=2, smooth_deg=80.0):
    """Finish a bmesh (built in world coordinates) into an object in `export`.
    Under a pivot, the vertices are moved into the pivot's frame so the pivot
    turns the part about its joint."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if under is not None:
        bmesh.ops.translate(bm, verts=bm.verts, vec=-world_location(under))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    export().objects.link(obj)
    for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
        obj.data.materials.append(m)
    if under is not None:
        obj.parent = under
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35.0)
        apply_modifiers(obj)
    clean(obj)
    smooth_by_angle(obj, smooth_deg)
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
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def apply_modifiers(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    if len(new.materials) == 0:
        for m in old.materials:
            new.materials.append(m)
    bpy.data.meshes.remove(old)


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


def catmull(stations, per):
    """A Catmull-Rom curve through equal-length tuples, `per` steps a gap, the
    originals kept: a few hand-placed sections become a smooth body."""
    pts = [list(map(float, s)) for s in stations]
    if len(pts) < 2 or per < 1:
        return pts
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
        out.append(p1)
        for j in range(1, per):
            t = j / per
            out.append([0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                        for a, b, c, d in zip(p0, p1, p2, p3)])
    out.append(pts[-1])
    return out


def loft_rings(rings, tags=None, belly=None, cap_start=False, cap_end=False):
    """Quads between successive rings of points; a one-point ring is a pole
    and gets a fan. With `tags` (a number per point) and `belly`, a face whose
    points' mean tag is below `belly` takes material slot 1."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    faces = []
    for i, (a, b) in enumerate(zip(vs, vs[1:])):
        ta = tags[i] if tags else None
        tb = tags[i + 1] if tags else None
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            n = len(b)
            for k in range(n):
                j = (k + 1) % n
                faces.append((bm.faces.new((a[0], b[j], b[k])), [tb[k], tb[j]] if tags else None))
        elif len(b) == 1:
            n = len(a)
            for k in range(n):
                j = (k + 1) % n
                faces.append((bm.faces.new((a[k], a[j], b[0])), [ta[k], ta[j]] if tags else None))
        else:
            n = len(a)
            for k in range(n):
                j = (k + 1) % n
                faces.append((bm.faces.new((a[k], a[j], b[j], b[k])), [ta[k], ta[j], tb[j], tb[k]] if tags else None))
    if cap_start and len(vs[0]) > 2:
        bm.faces.new(list(reversed(vs[0])))
    if cap_end and len(vs[-1]) > 2:
        bm.faces.new(vs[-1])
    if belly is not None:
        for f, t in faces:
            if t and sum(t) / len(t) < belly:
                f.material_index = 1
    return bm


def tube_y(stations, sides=16, per=2, belly=None):
    """A body lofted along Y from elliptical sections, head toward -Y. A
    station is (y, cz, rx, rz_up, rz_down[, cx]); rx = 0 at an end is a pole.
    The sections are run through a Catmull-Rom so the few given read as one
    smooth form. `belly` marks the faces below that fraction of the section's
    height (sin of the ring angle) for the second material."""
    st = catmull([list(s) + [0.0] * (6 - len(s)) for s in stations], per)
    rings, tags = [], []
    last = len(st) - 1
    for i, (y, cz, rx, rzu, rzd, cx) in enumerate(st):
        if i in (0, last) and rx <= 1e-6:
            rings.append([(cx, y, cz)])
            tags.append([0.0])
            continue
        rx, rzu, rzd = max(rx, 0.003), max(rzu, 0.003), max(rzd, 0.003)
        ring, tag = [], []
        for k in range(sides):
            th = TAU * k / sides
            s, c = math.sin(th), math.cos(th)
            ring.append((cx + rx * c, y, cz + (rzu if s >= 0 else rzd) * s))
            tag.append(s)
        rings.append(ring)
        tags.append(tag)
    return loft_rings(rings, tags, belly, cap_start=len(rings[0]) > 1, cap_end=len(rings[-1]) > 1)


def paddle(stations, sides=10, per=2):
    """A flat tapered limb in its own frame: the span along +X, the chord
    along Y, the thickness along Z. A station is (s, chord_centre,
    chord_half, thick_half[, z_offset]); chord_half = 0 at the end is the
    tip. Place it with `frame()`."""
    st = catmull([list(s) + [0.0] * (5 - len(s)) for s in stations], per)
    rings = []
    last = len(st) - 1
    for i, (s, cc, ch, th, dz) in enumerate(st):
        if i in (0, last) and ch <= 1e-6:
            rings.append([(s, cc, dz)])
            continue
        ch, th = max(ch, 0.002), max(th, 0.001)
        rings.append([(s, cc + ch * math.cos(TAU * k / sides), dz + th * math.sin(TAU * k / sides)) for k in range(sides)])
    return loft_rings(rings, cap_start=len(rings[0]) > 1, cap_end=len(rings[-1]) > 1)


def frame(origin, span, chord):
    """The matrix placing a paddle: its +X along `span`, its +Y along `chord`
    (made perpendicular), from `origin`."""
    x = Vector(span).normalized()
    y = Vector(chord)
    y = (y - x * y.dot(x)).normalized()
    z = x.cross(y)
    return Matrix(((x.x, y.x, z.x, origin[0]), (x.y, y.y, z.y, origin[1]), (x.z, y.z, z.z, origin[2]), (0.0, 0.0, 0.0, 1.0)))


def limb(origin, tip, chord, stations, sides=10, per=2):
    """A paddle from `origin` to `tip` (world), the stations' spans as a
    fraction 0..1 of that length."""
    length = (Vector(tip) - Vector(origin)).length
    st = [(s * length, *rest) for s, *rest in stations]
    return move(paddle(st, sides, per), frame(origin, Vector(tip) - Vector(origin), chord))


def blade(stations, sides=10, per=2):
    """A flat limb along a bent path, for a flipper that comes down from the
    shoulder and lies flat on the ground, or a wing laid round a flank. A
    station is (x, y, z, cx, cy, cz, chord_half, thick_half): the path point,
    the direction the chord spans there (made square to the path), and the
    half-sizes; the thin direction is square to both. chord_half = 0 at an
    end is a tip; otherwise the end is capped flat."""
    st = catmull([list(s) for s in stations], per)
    pts = [Vector(s[:3]) for s in st]
    n = len(pts)
    rings = []
    for i, s in enumerate(st):
        t = (pts[1] - pts[0]) if i == 0 else (pts[-1] - pts[-2]) if i == n - 1 else (pts[i + 1] - pts[i - 1])
        t.normalize()
        c = Vector(s[3:6])
        c = (c - t * c.dot(t)).normalized()
        nn = t.cross(c)
        ch, th = s[6], s[7]
        if i in (0, n - 1) and ch <= 1e-6:
            rings.append([pts[i]])
            continue
        ch, th = max(ch, 0.002), max(th, 0.001)
        rings.append([pts[i] + c * (ch * math.cos(TAU * k / sides)) + nn * (th * math.sin(TAU * k / sides)) for k in range(sides)])
    return loft_rings(rings, cap_start=len(rings[0]) > 1, cap_end=len(rings[-1]) > 1)


def tube_var(points, sides=12, per=2):
    """A round tube along a smooth curve: a point is (x, y, z, r[, flat]),
    `flat` scaling its vertical radius; r = 0 at an end is a pole. The frame
    is carried along so the tube never twists."""
    st = catmull([list(p) + [1.0] * (5 - len(p)) for p in points], per)
    pts = [Vector(p[:3]) for p in st]
    n = len(pts)
    tangents = []
    for i in range(n):
        t = pts[1] - pts[0] if i == 0 else pts[-1] - pts[-2] if i == n - 1 else pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((0, -1, 0))
    nrm = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    rings = []
    for i in range(n):
        if i > 0:
            nrm = tangents[i - 1].rotation_difference(tangents[i]) @ nrm
            nrm = (nrm - tangents[i] * nrm.dot(tangents[i])).normalized()
        bin_ = tangents[i].cross(nrm).normalized()
        r, flat = st[i][3], st[i][4]
        if i in (0, n - 1) and r <= 1e-6:
            rings.append([pts[i]])
            continue
        r = max(r, 0.002)
        rings.append([pts[i] + r * (flat * math.cos(TAU * k / sides) * nrm + math.sin(TAU * k / sides) * bin_) for k in range(sides)])
    return loft_rings(rings, cap_start=len(rings[0]) > 1, cap_end=len(rings[-1]) > 1)


def ellipsoid(centre, radii, sides=12, rings=8, rot=None):
    """A sphere stretched to `radii`, turned by `rot` (a matrix) and moved to
    `centre`."""
    rs = []
    for i in range(rings + 1):
        a = math.pi * i / rings
        r, z = math.sin(a), -math.cos(a)
        if i in (0, rings):
            rs.append([(0.0, 0.0, z)])
        else:
            rs.append([(r * math.cos(TAU * k / sides), r * math.sin(TAU * k / sides), z) for k in range(sides)])
    bm = loft_rings(rs)
    m = Matrix.Translation(centre) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*radii, 1.0))
    return move(bm, m)


def prism(poly, z0, z1):
    """A plan polygon extruded from z0 to z1."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in poly]
    hi = [bm.verts.new((x, y, z1)) for x, y in poly]
    n = len(poly)
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def cylinder(centre_xy, r, z0, z1, sides=10):
    return prism([(centre_xy[0] + r * math.cos(TAU * k / sides), centre_xy[1] + r * math.sin(TAU * k / sides)) for k in range(sides)], z0, z1)


def rounded_rect(hx, hy, r, per=4):
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0), (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def move(bm, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return bm


def mirror_x(bm):
    """The same shape on the other side of the animal."""
    out = bm.copy()
    move(out, Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0)))
    return out


def join(bms):
    out = bmesh.new()
    for bm in bms:
        me = bpy.data.meshes.new("_join")
        bm.to_mesh(me)
        bm.free()
        out.from_mesh(me)
        bpy.data.meshes.remove(me)
    return out


def rot_x(deg):
    return Matrix.Rotation(math.radians(deg), 4, "X")


def rot_y(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Y")


def station_at(stations, y):
    """The (cz, rx, rz_up, rz_down) of a tube_y body at `y`, linearly
    between its smoothed sections: where a bump sits on a ridge."""
    st = catmull([list(s) + [0.0] * (6 - len(s)) for s in stations], 4)
    st.sort(key=lambda s: s[0])
    for a, b in zip(st, st[1:]):
        if a[0] <= y <= b[0] or b[0] <= y <= a[0]:
            t = 0.0 if b[0] == a[0] else (y - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in (1, 2, 3, 4))
    return tuple(st[-1][i] for i in (1, 2, 3, 4))


def on_body(stations, y, phi_deg, push=0.0):
    """A point on a tube_y body's +X side at `y`, `phi_deg` up from its
    widest line, pushed `push` out along the surface's normal; with the
    normal and the direction straight down the surface from there."""
    cz, rx, rzu, rzd = station_at(stations, y)
    phi = math.radians(phi_deg)
    rz = rzu if phi >= 0 else rzd
    n = Vector((math.cos(phi) / rx, 0.0, math.sin(phi) / rz)).normalized()
    p = Vector((rx * math.cos(phi), y, cz + rz * math.sin(phi))) + n * push
    down = Vector((rx * math.sin(phi), 0.0, -rz * math.cos(phi))).normalized()
    return p, n, down


def mesh_points(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def bounds(objs):
    pts = mesh_points(objs)
    return Vector(map(min, *pts)), Vector(map(max, *pts))


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


def eye_pair(mat, left, r, under=None, matrix=None, sides=8, rings=5):
    """Two eyes, `left` the animal's left one in its head's own frame (+X is
    left for a head facing -Y), placed by `matrix`."""
    m = matrix or Matrix.Identity(4)
    for name, p in (("eye_left", left), ("eye_right", (-left[0], left[1], left[2]))):
        new_object(name, ellipsoid(m @ Vector(p), (r, r, r), sides, rings), mat, under=under)


# --- the pelican ---------------------------------------------------------------
#
# Brown pelican, adult: 1.0 to 1.2 m long stretched out, the bill 0.3 m. On a
# piling it stands hunched: the body tipped up at the breast, the neck a thick
# S drawn back so the head sits over the shoulders, the long bill forward and
# down with the pouch slack under it. Short thick legs, big webbed feet; the
# feet straddle the origin and the body balances over them.

# the body in its own frame (y back, z up), then tipped and placed
PEL_BODY = [(-0.30, 0.0, 0.0, 0.0, 0.0), (-0.27, 0.0, 0.08, 0.085, 0.095), (-0.17, 0.0, 0.14, 0.14, 0.16),
            (-0.02, 0.0, 0.155, 0.15, 0.165), (0.13, 0.01, 0.14, 0.13, 0.14), (0.25, 0.03, 0.085, 0.08, 0.08),
            (0.32, 0.04, 0.0, 0.0, 0.0)]
PEL_BODY_AT = (0.0, 0.03, 0.29)
PEL_BODY_TILT = -24.0        # the breast up
# the folded wing on the body's +X flank: (y, degrees up the flank, chord
# half, thickness half), then the primaries' tips crossing over the tail
PEL_WING = [(-0.22, 30.0, 0.04, 0.016), (-0.13, 30.0, 0.09, 0.022), (0.0, 38.0, 0.11, 0.024), (0.12, 46.0, 0.10, 0.022),
            (0.22, 56.0, 0.075, 0.018)]
PEL_WING_TIPS = [((0.050, 0.31, 0.095), 0.045, 0.012), ((0.004, 0.40, 0.080), 0.022, 0.008), ((-0.02, 0.45, 0.07), 0.0, 0.0)]
PEL_SHOULDER = (0.10, -0.20, 0.09)        # in the body's frame
PEL_TAIL = [((0.0, 0.25, 0.035), 0.04, 0.018), ((0.0, 0.33, 0.035), 0.06, 0.014), ((0.0, 0.41, 0.028), 0.07, 0.010),
            ((0.0, 0.44, 0.025), 0.06, 0.008)]
PEL_NECK = [(0.0, -0.13, 0.38, 0.085), (0.0, -0.20, 0.48, 0.075), (0.0, -0.225, 0.57, 0.066), (0.0, -0.20, 0.65, 0.06),
            (0.0, -0.17, 0.705, 0.056), (0.0, -0.155, 0.725, 0.0)]
PEL_NECK_BASE = (0.0, -0.15, 0.41)
PEL_HEAD_AT = (0.0, -0.17, 0.735)
PEL_HEAD_PITCH = 30.0        # the bill points forward and down
# the head and bill in the head's own frame (y back to front, z up)
PEL_HEAD = [(0.075, 0.0, 0.0, 0.0, 0.0), (0.05, 0.0, 0.05, 0.05, 0.05), (0.0, 0.005, 0.06, 0.062, 0.058),
            (-0.05, 0.0, 0.05, 0.05, 0.045), (-0.085, -0.01, 0.03, 0.03, 0.025), (-0.10, -0.012, 0.0, 0.0, 0.0)]
PEL_BILL_UPPER = [(-0.06, -0.005, 0.032, 0.020, 0.012), (-0.16, -0.012, 0.030, 0.014, 0.010), (-0.28, -0.018, 0.024, 0.011, 0.008),
                  (-0.35, -0.022, 0.017, 0.010, 0.008), (-0.375, -0.034, 0.010, 0.008, 0.010), (-0.385, -0.05, 0.0, 0.0, 0.0)]
PEL_BILL_LOWER = [(-0.06, -0.028, 0.030, 0.008, 0.008), (-0.20, -0.032, 0.026, 0.006, 0.006), (-0.33, -0.034, 0.016, 0.005, 0.005),
                  (-0.37, -0.036, 0.0, 0.0, 0.0)]
PEL_POUCH = [(-0.02, -0.035, 0.0, 0.0, 0.0), (-0.06, -0.040, 0.026, 0.010, 0.050), (-0.15, -0.040, 0.024, 0.008, 0.075),
             (-0.25, -0.036, 0.020, 0.006, 0.055), (-0.32, -0.034, 0.012, 0.004, 0.020), (-0.355, -0.034, 0.0, 0.0, 0.0)]
PEL_BILL_JOINT = (0.0, -0.06, -0.01)      # the gape, in the head's frame
PEL_EYE = (0.047, -0.03, 0.025)           # the left eye, in the head's frame
PEL_HIP = (0.075, 0.07, 0.17)             # the left hip
PEL_SHIN_R = 0.022
PEL_FOOT_T = 0.018
# the webbed foot, toes toward -Y, round the ankle: four toes, all webbed
PEL_FOOT = [(0.0, 0.035), (0.03, 0.025), (0.065, -0.05), (0.045, -0.08), (0.022, -0.105), (0.0, -0.09),
            (-0.022, -0.105), (-0.045, -0.08), (-0.065, -0.05), (-0.03, 0.025)]


def pelican_wing():
    """The +X folded wing in the body's frame: laid along the flank, its
    inner face on the feathers, the primaries running on over the tail."""
    st = []
    for y, phi, ch, th in PEL_WING:
        p, n, down = on_body(PEL_BODY, y, phi, th * 0.6)
        st.append((*p, *down, ch, th))
    for p, ch, th in PEL_WING_TIPS:
        st.append((*p, 1.0, 0.0, -0.25, ch, th))
    return blade(st, 10)


def build_pelican():
    plumage = material("pelican_plumage", PELICAN_PLUMAGE)
    pale = material("pelican_pale", PELICAN_PALE)
    bill = material("pelican_bill", PELICAN_BILL)
    dark = material("pelican_dark", PELICAN_DARK)
    body_m = Matrix.Translation(PEL_BODY_AT) @ rot_x(PEL_BODY_TILT)

    new_object("body", move(tube_y(PEL_BODY, 14), body_m), plumage)
    neck_pivot = pivot("neck_pivot", PEL_NECK_BASE)
    new_object("neck", tube_var(PEL_NECK, 12), pale, under=neck_pivot)
    head_pivot = pivot("head_pivot", PEL_HEAD_AT, neck_pivot)
    head_m = Matrix.Translation(PEL_HEAD_AT) @ rot_x(PEL_HEAD_PITCH)
    new_object("head", move(tube_y(PEL_HEAD, 12), head_m), pale, under=head_pivot)
    eye_pair(dark, PEL_EYE, 0.013, head_pivot, head_m)
    upper_pivot = pivot("upper_pivot", head_m @ Vector(PEL_BILL_JOINT), head_pivot)
    new_object("bill_upper", move(tube_y(PEL_BILL_UPPER, 10), head_m), bill, under=upper_pivot)
    lower_pivot = pivot("lower_pivot", head_m @ Vector((0.0, PEL_BILL_JOINT[1], PEL_BILL_JOINT[2] - 0.02)), head_pivot)
    new_object("bill_lower", move(tube_y(PEL_BILL_LOWER, 10), head_m), bill, under=lower_pivot)
    new_object("pouch", move(tube_y(PEL_POUCH, 10), head_m), dark, under=lower_pivot)

    wing = move(pelican_wing(), body_m)
    for side, bm, sx in (("left", wing, 1.0), ("right", mirror_x(wing), -1.0)):
        p = pivot(f"wing_{side}", body_m @ Vector((sx * PEL_SHOULDER[0], PEL_SHOULDER[1], PEL_SHOULDER[2])))
        new_object(f"folded_wing_{side}", bm, plumage, under=p)
    tail_pivot = pivot("tail_pivot", body_m @ Vector(PEL_TAIL[0][0]))
    tail = blade([(*p, 1.0, 0.0, 0.0, ch, th) for p, ch, th in PEL_TAIL], 8)
    new_object("tail", move(tail, body_m), plumage, under=tail_pivot)

    for side, sx in (("left", 1.0), ("right", -1.0)):
        hip = (sx * PEL_HIP[0], PEL_HIP[1], PEL_HIP[2])
        p = pivot(f"leg_{side}", hip)
        new_object(f"shin_{side}", cylinder((hip[0], hip[1]), PEL_SHIN_R, 0.010, hip[2], 8), dark, under=p, smooth_deg=50)
        foot = move(prism(PEL_FOOT, 0.0, PEL_FOOT_T), Matrix.Translation((hip[0] + sx * 0.01, hip[1], 0.0)))
        new_object(f"foot_{side}", foot, dark, under=p, smooth_deg=40)


def checks_pelican():
    return [f"bill {abs(PEL_BILL_UPPER[-1][0] - PEL_BILL_UPPER[0][0]):.2f} m, pouch hanging "
            f"{max(rzd for _, _, _, _, rzd in PEL_POUCH):.3f} m under it; the feet straddle the origin",
            "species: brown pelican, adult, standing hunched as on a piling, wings folded"]


# --- the sea lion --------------------------------------------------------------
#
# California sea lion, adult female: about 1.8 m, 100 kg. Hauled out: the
# belly on the ground from the waist back, the chest raised on the fore
# flippers, the long neck up and the head lifted. What says sea lion and not
# seal: the long fore flippers it props itself on, the small rolled ear flaps,
# the long neck, and the hind flippers turned forward under the hips.

# the body and neck as one form along a spine: (x, y, z, r, height/width)
SL_SPINE = [(0.0, 0.93, 0.08, 0.0, 0.8), (0.0, 0.84, 0.09, 0.075, 0.8), (0.0, 0.62, 0.14, 0.17, 0.85),
            (0.0, 0.30, 0.215, 0.245, 0.9), (0.0, -0.02, 0.28, 0.255, 0.95), (0.0, -0.28, 0.39, 0.225, 1.0),
            (0.0, -0.45, 0.55, 0.165, 1.0), (0.0, -0.54, 0.71, 0.125, 1.0), (0.0, -0.58, 0.81, 0.10, 1.0),
            (0.0, -0.59, 0.85, 0.0, 1.0)]
SL_HEAD_AT = (0.0, -0.63, 0.87)
SL_HEAD_PITCH = -20.0        # nose up
# the head in its own frame (y back to front, z up)
SL_HEAD = [(0.12, 0.02, 0.0, 0.0, 0.0), (0.085, 0.02, 0.09, 0.095, 0.09), (0.0, 0.02, 0.115, 0.115, 0.10),
           (-0.085, 0.01, 0.095, 0.09, 0.085), (-0.165, -0.005, 0.06, 0.055, 0.052), (-0.235, -0.01, 0.042, 0.038, 0.035),
           (-0.265, -0.012, 0.0, 0.0, 0.0)]
SL_JAW = [(-0.05, -0.048, 0.06, 0.018, 0.036), (-0.14, -0.048, 0.05, 0.014, 0.031), (-0.225, -0.036, 0.034, 0.010, 0.019),
          (-0.255, -0.034, 0.0, 0.0, 0.0)]
SL_JAW_AT = (0.0, -0.024, -0.036)
SL_NOSE = ((0.0, -0.255, 0.0), (0.034, 0.024, 0.026))
# the left ear flap: from inside the head out, back and a little down
SL_EAR = [((0.075, 0.04, 0.055), 0.020, 0.011), ((0.108, 0.08, 0.048), 0.021, 0.010), ((0.13, 0.12, 0.035), 0.0, 0.0)]
SL_EYE = (0.074, -0.085, 0.048)
# the left fore flipper: down from inside the chest, then flat on the ground
# pointing out and back; the chord runs fore and aft
SL_FRONT = [((0.10, -0.30, 0.34), 0.10, 0.05), ((0.19, -0.33, 0.20), 0.10, 0.045), ((0.27, -0.35, 0.06), 0.10, 0.035),
            ((0.39, -0.33, 0.025), 0.10, 0.022), ((0.52, -0.28, 0.018), 0.085, 0.015), ((0.62, -0.235, 0.016), 0.05, 0.010),
            ((0.665, -0.215, 0.016), 0.0, 0.0)]
SL_SHOULDER = (0.12, -0.31, 0.32)
# the left hind flipper: out of the hip and turned forward on the ground
SL_REAR = [((0.10, 0.62, 0.11), 0.05, 0.035), ((0.20, 0.57, 0.045), 0.055, 0.025), ((0.30, 0.45, 0.018), 0.07, 0.015),
           ((0.37, 0.33, 0.016), 0.085, 0.012), ((0.395, 0.28, 0.016), 0.085, 0.010)]
SL_HIP = (0.11, 0.62, 0.11)


def build_sea_lion():
    coat = material("sea_lion_coat", SEA_LION_COAT)
    dark = material("sea_lion_dark", SEA_LION_DARK)

    new_object("body", tube_var(SL_SPINE, 18), coat)
    head_pivot = pivot("head_pivot", SL_HEAD_AT)
    head_m = Matrix.Translation(SL_HEAD_AT) @ rot_x(SL_HEAD_PITCH)
    rot = head_m.to_3x3().to_4x4()
    new_object("head", move(tube_y(SL_HEAD, 14), head_m), coat, under=head_pivot)
    new_object("nose", ellipsoid(head_m @ Vector(SL_NOSE[0]), SL_NOSE[1], 8, 5, rot), dark, under=head_pivot)
    ear = blade([(*p, 0.0, 0.0, 1.0, ch, th) for p, ch, th in SL_EAR], 6)
    for name, bm in (("ear_left", ear), ("ear_right", mirror_x(ear))):
        new_object(name, move(bm, head_m), coat, under=head_pivot)
    eye_pair(dark, SL_EYE, 0.024, head_pivot, head_m)
    jaw_pivot = pivot("jaw_pivot", head_m @ Vector(SL_JAW_AT), head_pivot)
    new_object("jaw", move(tube_y(SL_JAW, 10), head_m), coat, under=jaw_pivot)

    for place, table, at, chord in (("front", SL_FRONT, SL_SHOULDER, (0.0, 1.0, 0.0)), ("rear", SL_REAR, SL_HIP, (1.0, 0.0, 0.0))):
        bm = blade([(*p, *chord, ch, th) for p, ch, th in table], 10)
        for side, sx in (("left", 1.0), ("right", -1.0)):
            p = pivot(f"flipper_{place}_{side}_pivot", (sx * at[0], at[1], at[2]))
            new_object(f"flipper_{place}_{side}", bm.copy() if sx > 0 else mirror_x(bm), dark, under=p)
        bm.free()


def checks_sea_lion():
    return ["species: California sea lion, adult female size, hauled out on the fore flippers, "
            "hind flippers turned forward"]


# --- the sea otter -------------------------------------------------------------
#
# Southern sea otter: about 1.1 m with the tail, floating on its back, the
# head toward -Y and raised to look down its chest, forepaws together on the
# chest, the broad hind flippers up at the rear, the flat tail on the water.
# The back is the lowest point (z = 0); the water sits at z = 0.12.

OT_BODY = [(-0.32, 0.15, 0.0, 0.0, 0.0), (-0.30, 0.15, 0.09, 0.08, 0.09), (-0.20, 0.14, 0.15, 0.13, 0.13),
           (0.0, 0.13, 0.17, 0.13, 0.13), (0.20, 0.12, 0.15, 0.11, 0.12), (0.32, 0.12, 0.10, 0.08, 0.09),
           (0.38, 0.12, 0.0, 0.0, 0.0)]
OT_HEAD_AT = (0.0, -0.36, 0.25)
OT_NOSE_UP = 50.0            # the face's lift above +Y: it looks down its chest at its paws
# the head in its own frame, as if upright (y back to front, z the crown);
# rolled over and lifted by `otter_head_matrix`
OT_HEAD = [(0.075, 0.0, 0.0, 0.0, 0.0), (0.05, 0.0, 0.07, 0.07, 0.065), (0.0, 0.0, 0.088, 0.08, 0.075),
           (-0.05, -0.005, 0.078, 0.065, 0.06), (-0.085, -0.015, 0.05, 0.04, 0.04), (-0.10, -0.02, 0.0, 0.0, 0.0)]
OT_MUZZLE = ((0.0, -0.09, -0.024), (0.052, 0.045, 0.038))
OT_NOSE = ((0.0, -0.13, -0.002), (0.026, 0.016, 0.018))
OT_EAR = ((0.072, 0.015, 0.05), (0.018, 0.014, 0.02))
OT_EYE = (0.048, -0.062, 0.035)
# the otter's left is -X: it lies on its back
OT_SHOULDER = (-0.11, -0.22, 0.17)
OT_ARM = [(-0.11, -0.22, 0.17, 0.04), (-0.13, -0.14, 0.245, 0.034), (-0.07, -0.095, 0.29, 0.03), (-0.05, -0.09, 0.295, 0.0)]
OT_PAW = ((-0.042, -0.085, 0.30), (0.042, 0.036, 0.024))
OT_HIP = (-0.09, 0.28, 0.14)
OT_FLIPPER = [((-0.09, 0.28, 0.14), 0.03, 0.025), ((-0.11, 0.32, 0.20), 0.04, 0.02), ((-0.13, 0.32, 0.26), 0.06, 0.015),
              ((-0.15, 0.31, 0.32), 0.07, 0.012), ((-0.155, 0.305, 0.34), 0.065, 0.010)]
OT_TAIL = [((0.0, 0.30, 0.12), 0.05, 0.035), ((0.0, 0.40, 0.12), 0.06, 0.03), ((0.0, 0.52, 0.12), 0.06, 0.025),
           ((0.0, 0.62, 0.12), 0.045, 0.02), ((0.0, 0.645, 0.12), 0.03, 0.015), ((0.0, 0.66, 0.12), 0.0, 0.0)]


def otter_head_matrix():
    """The head rolled onto its back (crown down) and lifted so the nose
    points `OT_NOSE_UP` degrees above +Y."""
    return Matrix.Translation(OT_HEAD_AT) @ rot_x(-(180.0 - OT_NOSE_UP)) @ rot_y(180.0)


def build_sea_otter():
    fur = material("sea_otter_fur", OTTER_FUR)
    head_fur = material("sea_otter_head", OTTER_HEAD)
    pale = material("sea_otter_pale", OTTER_PALE)
    dark = material("sea_otter_dark", OTTER_DARK)

    new_object("body", tube_y(OT_BODY, 14), fur)
    head_pivot = pivot("head_pivot", OT_HEAD_AT)
    head_m = otter_head_matrix()
    rot = head_m.to_3x3().to_4x4()
    new_object("head", move(tube_y(OT_HEAD, 12), head_m), head_fur, under=head_pivot)
    new_object("muzzle", ellipsoid(head_m @ Vector(OT_MUZZLE[0]), OT_MUZZLE[1], 10, 6, rot), pale, under=head_pivot)
    new_object("nose", ellipsoid(head_m @ Vector(OT_NOSE[0]), OT_NOSE[1], 8, 4, rot), dark, under=head_pivot)
    # in the head's own frame +X is its left; rolled over, that lands on -X
    for name, lx in (("ear_left", OT_EAR[0][0]), ("ear_right", -OT_EAR[0][0])):
        new_object(name, ellipsoid(head_m @ Vector((lx, OT_EAR[0][1], OT_EAR[0][2])), OT_EAR[1], 8, 4, rot), fur, under=head_pivot)
    eye_pair(dark, OT_EYE, 0.016, head_pivot, head_m)

    flipper = blade([(*p, 1.0, 0.0, 0.0, ch, th) for p, ch, th in OT_FLIPPER], 10)
    for side, sx in (("left", 1.0), ("right", -1.0)):
        p = pivot(f"arm_{side}_pivot", (sx * OT_SHOULDER[0], OT_SHOULDER[1], OT_SHOULDER[2]))
        new_object(f"arm_{side}", tube_var([(sx * x, y, z, r) for x, y, z, r in OT_ARM], 8), fur, under=p)
        new_object(f"paw_{side}", ellipsoid((sx * OT_PAW[0][0], OT_PAW[0][1], OT_PAW[0][2]), OT_PAW[1], 8, 5), dark, under=p)
        q = pivot(f"leg_{side}_pivot", (sx * OT_HIP[0], OT_HIP[1], OT_HIP[2]))
        new_object(f"flipper_{side}", flipper.copy() if sx > 0 else mirror_x(flipper), dark, under=q)
    flipper.free()
    tail_pivot = pivot("tail_pivot", OT_TAIL[0][0])
    new_object("tail", blade([(*p, 1.0, 0.0, 0.0, ch, th) for p, ch, th in OT_TAIL], 10), fur, under=tail_pivot)


def checks_sea_otter():
    return [f"waterline z = {SWIMMERS['sea_otter']:.2f}, the tail lying on it",
            "species: southern sea otter, floating on its back"]


# --- the gray whale ------------------------------------------------------------
#
# Gray whale, adult, 13 m, swimming level: no dorsal fin, a hump and knuckles
# down the tail stock, the narrow head sloping to the snout with the lower jaw
# under it, paddle flippers, flukes 3.4 m across. The belly is the lowest
# point.

WH_BODY = [(-6.45, 1.30, 0.0, 0.0, 0.0), (-6.25, 1.29, 0.20, 0.15, 0.17), (-5.70, 1.30, 0.45, 0.40, 0.42),
           (-4.80, 1.32, 0.76, 0.70, 0.72), (-3.60, 1.35, 1.06, 1.00, 1.05), (-2.00, 1.35, 1.25, 1.18, 1.32),
           (0.00, 1.35, 1.22, 1.18, 1.30), (1.80, 1.40, 0.98, 0.98, 1.02), (3.20, 1.45, 0.62, 0.66, 0.66),
           (3.50, 1.45, 0.0, 0.0, 0.0)]
WH_TAIL_AT = (0.0, 3.2, 1.45)
WH_STOCK = [(3.0, 1.45, 0.62, 0.67, 0.67), (4.2, 1.45, 0.40, 0.55, 0.50), (5.3, 1.40, 0.22, 0.30, 0.28), (5.7, 1.38, 0.15, 0.17, 0.17),
            (5.9, 1.38, 0.0, 0.0, 0.0)]
WH_HUMP = (2.0, (0.30, 0.60, 0.20))           # y, radii, on the body's ridge
WH_KNUCKLES = ((2.7, "body"), (3.3, "stock"), (3.75, "stock"), (4.2, "stock"), (4.65, "stock"), (5.1, "stock"))
WH_KNUCKLE_R = (0.16, 0.22, 0.12)
WH_FLUKE_AT = (0.0, 5.75, 1.38)
# each lobe from the fluke pivot: (span, chord centre behind the pivot, chord
# half, thickness half); the trailing edge bows back from a median notch
WH_FLUKE = [(0.0, 0.20, 0.45, 0.12), (0.5, 0.30, 0.50, 0.10), (1.1, 0.40, 0.40, 0.07), (1.5, 0.55, 0.22, 0.04), (1.7, 0.65, 0.0, 0.0)]
WH_SHOULDER = (1.0, -3.3, 0.60)
WH_FLIPPER_TIP = (2.4, -2.1, 0.35)
WH_FLIPPER = [(0.0, 0.0, 0.45, 0.22), (0.27, 0.10, 0.42, 0.16), (0.65, 0.25, 0.32, 0.09), (0.90, 0.40, 0.18, 0.04), (1.0, 0.50, 0.0, 0.0)]
# the lower jaw: a lip a little wider than the head over it, its top the
# arched mouth line, its bottom running on into the throat
WH_JAW_AT = (0.0, -3.9, 0.95)
WH_JAW = [(-3.70, 0.62, 0.0, 0.0, 0.0), (-3.90, 0.68, 0.98, 0.27, 0.40), (-4.80, 0.80, 0.80, 0.27, 0.40),
          (-5.70, 0.97, 0.49, 0.17, 0.32), (-6.25, 1.12, 0.23, 0.08, 0.17), (-6.52, 1.17, 0.0, 0.0, 0.0)]
WH_EYE = (-4.0, -22.0, 0.11)            # y, degrees round the flank, radius


def build_whale():
    skin = material("whale_skin", WHALE_SKIN)
    dark = material("whale_dark", WHALE_DARK)

    body = [tube_y(WH_BODY, 20)]
    cz, _, rzu, _ = station_at(WH_BODY, WH_HUMP[0])
    body.append(ellipsoid((0.0, WH_HUMP[0], cz + rzu - 0.10), WH_HUMP[1], 12, 6))
    stock = [tube_y(WH_STOCK, 16)]
    for y, on in WH_KNUCKLES:
        cz, _, rzu, _ = station_at(WH_BODY if on == "body" else WH_STOCK, y)
        (body if on == "body" else stock).append(ellipsoid((0.0, y, cz + rzu - 0.05), WH_KNUCKLE_R, 8, 5))
    new_object("body", join(body), skin)
    eye_pair(dark, on_body(WH_BODY, WH_EYE[0], WH_EYE[1], -WH_EYE[2] * 0.35)[0], WH_EYE[2])
    jaw_pivot = pivot("jaw_pivot", WH_JAW_AT)
    new_object("jaw", tube_y(WH_JAW, 18), skin, under=jaw_pivot)
    tail_pivot = pivot("tail_pivot", WH_TAIL_AT)
    new_object("tail_stock", join(stock), skin, under=tail_pivot)
    fluke_pivot = pivot("fluke_pivot", WH_FLUKE_AT, tail_pivot)
    lobe = move(paddle(WH_FLUKE, 10), frame(WH_FLUKE_AT, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    new_object("flukes", join([lobe.copy(), mirror_x(lobe)]), skin, under=fluke_pivot)
    lobe.free()
    flipper = limb(WH_SHOULDER, WH_FLIPPER_TIP, (0.0, 1.0, 0.0), WH_FLIPPER, 12)
    for side, sx in (("left", 1.0), ("right", -1.0)):
        p = pivot(f"flipper_{side}_pivot", (sx * WH_SHOULDER[0], WH_SHOULDER[1], WH_SHOULDER[2]))
        new_object(f"flipper_{side}", flipper.copy() if sx > 0 else mirror_x(flipper), skin, under=p)
    flipper.free()


def checks_whale():
    return [f"flukes {2 * WH_FLUKE[-1][0]:.1f} m across, waterline z = {SWIMMERS['whale']:.2f}",
            "species: gray whale, adult, swimming level"]


# --- the bottlenose dolphin ----------------------------------------------------
#
# Common bottlenose dolphin, adult, 2.7 m: a round melon stepping down to a
# short beak, the falcate dorsal fin at mid-body, flukes 0.68 m across, the
# pale belly. The belly is the lowest point.

DO_BODY = [(-1.32, 0.255, 0.0, 0.0, 0.0), (-1.29, 0.255, 0.04, 0.028, 0.024), (-1.21, 0.26, 0.055, 0.038, 0.032),
           (-1.15, 0.27, 0.068, 0.05, 0.042), (-1.08, 0.30, 0.14, 0.15, 0.10), (-0.92, 0.32, 0.21, 0.24, 0.17),
           (-0.60, 0.33, 0.27, 0.30, 0.25), (-0.20, 0.33, 0.29, 0.31, 0.32), (0.25, 0.34, 0.25, 0.28, 0.29),
           (0.65, 0.36, 0.16, 0.21, 0.20), (0.90, 0.38, 0.09, 0.14, 0.12), (1.0, 0.38, 0.0, 0.0, 0.0)]
DO_TAIL_AT = (0.0, 0.90, 0.38)
DO_STOCK = [(0.85, 0.38, 0.10, 0.15, 0.13), (1.05, 0.39, 0.065, 0.10, 0.09), (1.18, 0.39, 0.045, 0.06, 0.055), (1.25, 0.39, 0.0, 0.0, 0.0)]
DO_FLUKE_AT = (0.0, 1.18, 0.39)
DO_FLUKE = [(0.0, 0.02, 0.10, 0.04), (0.10, 0.05, 0.12, 0.03), (0.22, 0.10, 0.085, 0.018), (0.30, 0.15, 0.04, 0.010), (0.34, 0.18, 0.0, 0.0)]
DO_DORSAL_AT = (0.0, -0.05, 0.58)
DO_DORSAL = [(0.0, 0.0, 0.22, 0.045), (0.08, 0.03, 0.17, 0.035), (0.16, 0.09, 0.10, 0.022), (0.22, 0.15, 0.05, 0.012), (0.25, 0.18, 0.0, 0.0)]
DO_SHOULDER = (0.20, -0.70, 0.17)
DO_FLIPPER_TIP = (0.56, -0.42, 0.06)
DO_FLIPPER = [(0.0, 0.0, 0.09, 0.04), (0.26, 0.03, 0.085, 0.03), (0.60, 0.07, 0.055, 0.016), (0.85, 0.11, 0.025, 0.008), (1.0, 0.13, 0.0, 0.0)]
DO_JAW_AT = (0.0, -1.06, 0.24)
DO_JAW = [(-1.04, 0.235, 0.075, 0.025, 0.06), (-1.15, 0.225, 0.062, 0.02, 0.045), (-1.24, 0.222, 0.048, 0.015, 0.03),
          (-1.31, 0.225, 0.032, 0.01, 0.02), (-1.345, 0.228, 0.0, 0.0, 0.0)]
DO_EYE = (-0.99, -12.0, 0.022)            # y, degrees round the flank from its widest line, radius
DO_BELLY = -0.15


def build_dolphin():
    back = material("dolphin_back", DOLPHIN_BACK)
    belly = material("dolphin_belly", DOLPHIN_BELLY)
    dark = material("dolphin_dark", DOLPHIN_DARK)

    new_object("body", tube_y(DO_BODY, 18, belly=DO_BELLY), [back, belly])
    new_object("dorsal_fin", move(paddle(DO_DORSAL, 10), frame(DO_DORSAL_AT, (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))), back)
    eye_pair(dark, on_body(DO_BODY, DO_EYE[0], DO_EYE[1], -DO_EYE[2] * 0.35)[0], DO_EYE[2])
    jaw_pivot = pivot("jaw_pivot", DO_JAW_AT)
    new_object("jaw", tube_y(DO_JAW, 12, belly=0.6), [back, belly], under=jaw_pivot)
    tail_pivot = pivot("tail_pivot", DO_TAIL_AT)
    new_object("tail_stock", tube_y(DO_STOCK, 14, belly=DO_BELLY), [back, belly], under=tail_pivot)
    fluke_pivot = pivot("fluke_pivot", DO_FLUKE_AT, tail_pivot)
    lobe = move(paddle(DO_FLUKE, 10), frame(DO_FLUKE_AT, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    new_object("flukes", join([lobe.copy(), mirror_x(lobe)]), back, under=fluke_pivot)
    lobe.free()
    flipper = limb(DO_SHOULDER, DO_FLIPPER_TIP, (0.0, 1.0, 0.0), DO_FLIPPER, 10)
    for side, sx in (("left", 1.0), ("right", -1.0)):
        p = pivot(f"flipper_{side}_pivot", (sx * DO_SHOULDER[0], DO_SHOULDER[1], DO_SHOULDER[2]))
        new_object(f"flipper_{side}", flipper.copy() if sx > 0 else mirror_x(flipper), back, under=p)
    flipper.free()


def checks_dolphin():
    return [f"flukes {2 * DO_FLUKE[-1][0]:.2f} m across, dorsal fin {DO_DORSAL[-1][0]:.2f} m, "
            f"waterline z = {SWIMMERS['dolphin']:.2f}",
            "species: common bottlenose dolphin, adult, swimming level"]


BUILDERS = {"pelican": (build_pelican, checks_pelican), "sea_lion": (build_sea_lion, checks_sea_lion),
            "sea_otter": (build_sea_otter, checks_sea_otter), "whale": (build_whale, checks_whale),
            "dolphin": (build_dolphin, checks_dolphin)}
BUDGETS = {"pelican": 2500, "sea_lion": 3000, "sea_otter": 2500, "whale": 4000, "dolphin": 2500}
FEET_AT_ORIGIN = {"pelican"}   # placed by where it stands, not by its outline's centre


# --- the frame -------------------------------------------------------------------

def settle(name):
    """The lowest point exactly on z = 0 (a smoothed section can overshoot a
    few millimetres) and the plan centred on the origin (the pelican keeps
    its feet there instead), moving every root object of the animal; then the
    waterline marker for a swimmer, in `reference`, at the height chosen for
    it in that settled frame."""
    parts = [o for o in export().all_objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    shift = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    if name in FEET_AT_ORIGIN:
        shift.x = shift.y = 0.0
    if shift.length > 1e-6:
        for o in [o for o in export().all_objects if o.parent is None]:
            if o.type == "MESH":
                me = o.data
                for v in me.vertices:
                    v.co += shift
                me.update()
            else:
                o.location += shift
        print(f"wildlife_coast: moved ({shift.x * 1000:+.1f}, {shift.y * 1000:+.1f}, {shift.z * 1000:+.1f}) mm "
              "to stand on z = 0 centred on the origin")
    ref = bpy.data.collections.get("reference")
    if name in SWIMMERS and ref is not None:
        old = bpy.data.objects.get("waterline")
        if old is not None:
            bpy.data.objects.remove(old)
        w = bpy.data.objects.new("waterline", None)
        w.empty_display_type = "PLAIN_AXES"
        w.empty_display_size = 0.5
        w.location = (0.0, 0.0, SWIMMERS[name])
        ref.objects.link(w)


def report(name):
    parts = [o for o in export().all_objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    pivots = [o for o in export().all_objects if o.type == "EMPTY"]
    tris = triangles(parts)
    print(f"wildlife_coast: {name}: {len(parts)} parts, {len(pivots)} pivots, {tris} triangles "
          f"(budget {BUDGETS[name]}{', OVER' if tris > BUDGETS[name] else ''})")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts))
    print("  pivots: " + ", ".join(f"{o.name}" + (f" < {o.parent.name}" if o.parent else "") for o in pivots))
    print(f"  size: {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x L x H), x {lo.x:.3f}..{hi.x:.3f}, "
          f"y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.4f}..{hi.z:.3f}; plan centre ({(lo.x + hi.x) / 2:.3f}, {(lo.y + hi.y) / 2:.3f})")
    for o in parts:
        plo, phi = bounds([o])
        if plo.z < 0.03:
            print(f"  {o.name} reaches down to z = {plo.z:.4f}")
    if name in SWIMMERS:
        print(f"  waterline z = {SWIMMERS[name]:.3f}: {SWIMMERS[name] / (hi.z - lo.z):.0%} of the height under water")
    for line in BUILDERS[name][1]():
        print("  " + line)


# --- rendering ---------------------------------------------------------------------

def stage_scene():
    """A review scene: EEVEE, a sky, a ground, a sun and a camera in a
    `_review` collection that is never saved."""
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
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.70, 0.74, 0.80, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)

    def stage_object(tag, bm, colour):
        o = new_object(tag, bm, material(f"render_{tag}", colour))
        export().objects.unlink(o)
        stage.objects.link(o)
        del o["kyt_collision"]
        return o

    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), math.radians(12), math.radians(40))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    cam.data.clip_end = 1000.0
    stage.objects.link(cam)
    scene.camera = cam
    return scene, stage, stage_object, cam


def shoot(scene, cam, path, objs, direction, target=None, lens=40, frame=None, margin=0.04):
    """The camera along `direction` from the objects' centre, backed off
    until every vertex of `frame` (or the objects) is in the picture."""
    pts = mesh_points(frame or objs)
    lo, hi = Vector(map(min, *pts)), Vector(map(max, *pts))
    centre = (lo + hi) / 2 if target is None else Vector(target)
    d = Vector(direction).normalized()
    dist = max((hi - lo).length * 0.6, 0.5)
    cam.data.lens = lens
    for _ in range(80):
        cam.location = centre + d * dist
        cam.location.z = max(cam.location.z, 0.12)
        look = centre - cam.location
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if all(margin <= c.x <= 1 - margin and margin <= c.y <= 1 - margin
               for c in (world_to_camera_view(scene, cam, p) for p in pts)):
            break
        dist *= 1.05
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def render(folder, name):
    os.makedirs(folder, exist_ok=True)
    scene, stage, stage_object, cam = stage_scene()
    parts = [o for o in export().all_objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    reach = max(hi.x - lo.x, hi.y - lo.y) * 3 + 10
    ground = stage_object("ground", prism([(-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)], -0.02, -0.001), (0.62, 0.60, 0.56, 1))
    extras = [ground]

    def only(objs):
        for o in parts + extras:
            o.hide_render = o not in objs

    only(parts + [ground])
    for tag, d in (("three_quarter", (-0.75, -1.0, 0.55)), ("front", (0.0, -1.0, 0.18)), ("side", (1.0, 0.0, 0.18)), ("top", (0.0, -0.001, 1.0))):
        shoot(scene, cam, os.path.join(folder, f"{name}_{tag}.png"), parts, d)
    # beside a 1.7 m tall box, a guest's height, level with the head so the
    # whale's body never hides it
    scale_box = stage_object("scale_box", prism(rounded_rect(0.225, 0.14, 0.03), 0.0, 1.7), (0.45, 0.45, 0.50, 1))
    extras.append(scale_box)
    scale_box.location = (hi.x + 0.45 + 0.225, lo.y + 0.14, 0.0)
    only(parts + [ground, scale_box])
    shoot(scene, cam, os.path.join(folder, f"{name}_scale.png"), parts + [scale_box], (-0.6, -1.0, 0.35))
    # a swimmer at its waterline: the water hides what is under it
    if name in SWIMMERS:
        z = SWIMMERS[name]
        water = stage_object("water", prism([(-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)], z - 0.01, z), (0.30, 0.52, 0.62, 1))
        extras.append(water)
        only(parts + [water])
        above = [Vector(p) for p in mesh_points(parts) if p.z >= z]
        target = sum(above, Vector()) / len(above) if above else None
        shoot(scene, cam, os.path.join(folder, f"{name}_water.png"), parts, (-0.75, -1.0, 0.45), target=target, frame=parts)
        only(parts + [ground, scale_box])


def lineup(path, with_gull):
    """All five built in memory and turned side-on (heads toward +X, the
    camera on their right), in a row along X beside the 1.7 m box. Nothing is
    saved."""
    for o in list(bpy.data.objects):      # the factory scene's cube, light and camera
        bpy.data.objects.remove(o)
    for coll_name in ("reference", "authored", "export"):
        if bpy.data.collections.get(coll_name) is None:
            coll = bpy.data.collections.new(coll_name)
            bpy.context.scene.collection.children.link(coll)
    scene, stage, stage_object, cam = stage_scene()
    scene.render.resolution_x, scene.render.resolution_y = 3000, 1000
    order = ["whale", "dolphin", "sea_lion", "box", "pelican", "sea_otter"]
    if with_gull:
        order.insert(order.index("pelican") + 1, "gull")
    groups = {}
    for name in order:
        if name == "box":
            box = stage_object("scale_box", prism(rounded_rect(0.225, 0.14, 0.03), 0.0, 1.7), (0.45, 0.45, 0.50, 1))
            root = bpy.data.objects.new("lineup_box", None)
            stage.objects.link(root)
            box.parent = root
            groups[name] = [root, box]
            continue
        if name == "gull":
            groups[name] = append_gull(stage)
            continue
        BUILDERS[name][0]()
        settle(name)
        objs = list(export().all_objects)
        root = bpy.data.objects.new(f"lineup_{name}", None)
        stage.objects.link(root)
        root.rotation_euler = (0.0, 0.0, math.pi / 2)     # -Y, the head, to +X
        for o in objs:
            if o.parent is None:
                o.parent = root
            export().objects.unlink(o)
            stage.objects.link(o)
        groups[name] = [root] + objs
    bpy.context.view_layer.update()
    x = 0.0
    everything = []
    for name in order:
        objs = groups[name]
        meshes = [o for o in objs if o.type == "MESH"]
        lo, hi = bounds(meshes)
        root = objs[0]
        root.location.x += x - lo.x
        root.location.y -= (lo.y + hi.y) / 2
        bpy.context.view_layer.update()
        x += (hi.x - lo.x) + 0.8
        everything += meshes
    lo, hi = bounds(everything)
    for name in order:
        groups[name][0].location.x -= (lo.x + hi.x) / 2
    bpy.context.view_layer.update()
    reach = (hi.x - lo.x) * 2 + 20
    stage_object("ground", prism([(-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)], -0.02, -0.001), (0.62, 0.60, 0.56, 1))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shoot(scene, cam, path, everything, (0.0, -1.0, 0.22), lens=60, margin=0.03)
    # the small ones close, without the whale
    small = [o for name in order if name != "whale" for o in groups[name] if o.type == "MESH"]
    for o in groups["whale"]:
        if o.type == "MESH":
            o.hide_render = True
    stem, ext = os.path.splitext(path)
    scene.render.resolution_x, scene.render.resolution_y = 2400, 1000
    shoot(scene, cam, f"{stem}_small{ext}", small, (0.0, -1.0, 0.22), lens=60, margin=0.03)


def append_gull(stage):
    """The adult gull's objects from its blend (read only: appended, never
    linked back), under a root scaled to its Godot size and turned head to +X
    like the lineup's animals (the gull's bill points +Y in its file)."""
    with bpy.data.libraries.load(GULL_BLEND, link=False) as (data_from, data_to):
        data_to.objects = list(data_from.objects)
    objs = [o for o in data_to.objects if o is not None]
    root = bpy.data.objects.new("lineup_gull", None)
    stage.objects.link(root)
    root.scale = (GULL_SCALE,) * 3
    root.rotation_euler = (0.0, 0.0, -math.pi / 2)
    for o in objs:
        stage.objects.link(o)
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    # the gull's feet sit a little above its origin; settle it like the others
    meshes = [o for o in objs if o.type == "MESH" and not o.name.startswith("tail_dark")]
    for o in objs:
        if o.type == "MESH" and o.name.startswith("tail_dark"):
            o.hide_render = True
    lo, hi = bounds(meshes)
    root.location.z -= lo.z
    bpy.context.view_layer.update()
    return [root] + meshes


# --- the file ----------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--lineup" in argv:
        lineup(argv[argv.index("--lineup") + 1], "--gull" in argv)
        return
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in BUILDERS:
        raise SystemExit(f"wildlife_coast: open one of {', '.join(BUILDERS)}, not {name!r}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"wildlife_coast: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for child in list(coll.children):
            bpy.data.collections.remove(child)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    BUILDERS[name][0]()
    settle(name)
    report(name)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
