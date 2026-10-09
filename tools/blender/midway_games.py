"""The Boardwalk's six midway game families, a first pass from the catalog
notes (2026-10-02): each already stands in the game as an authored greybox
composition in `scenes/world/boardwalk_scenery.tscn` or `boardwalk_finish.tscn`,
exported and locked in its file's `reference`; none has a photograph of
Christina's. Each is the plainest faithful reading of its composition at its
authored size, in the house style, for her to reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<prop>.blend --python tools/blender/midway_games.py -- \\
        [--replace] [--save] [--render <folder>]

`<prop>` is `arcade_cabinet` (PRP-GAME-001), `derby_race_lane` (002),
`derby_prize_display` (003), `coin_pitch_table` (004), `basket_toss` (005) or
`prize_rail_shelf` (006). The tool builds whichever the file is named for into
`export`, one object a part, facing -Y here (+Z in Godot), real metres. It
refuses while `export` holds anything (it may be hers) unless `--replace`; it
writes the file only with `--save`; `--render` shoots three-quarter, front,
side and top views, one beside a 1.7 m box for scale, and for a kit each piece
and the pieces arranged as the Boardwalk composition, into the folder (saved
first, so the render's camera, sun, ground and wall never reach the file).

**Frames.** The exporter put each greybox on the ground at the centre of its
footprint with the booth's public (west) side toward -X; these props turn a
quarter so the public side is -Y, the house rule. A piece that lives on a booth
counter in the game (the alley, the pitch table: the authored ones stand about
1.2 m above the deck on counters that belong to the frontage) sits with its own
bottom on z = 0, as its greybox does, and the placement scene lifts it. A piece
hung on a wall (the prize rail, the shelf, the basket, the derby display) sits
with its lowest point on z = 0 and its back on y = 0, as the poster case does,
and the scene lifts it to its wall height.

**Arcade cabinet.** The greybox is a 0.82 by 0.80 by 1.72 m box with a 0.58 by
0.48 m screen on its front at 0.90 to 1.38 m. Built: one late-1990s upright,
0.82 wide, 0.80 deep, 1.72 m tall, its side profile the classic one (a straight
lower front with the coin door, a control panel jutting out at 0.88 m, a
monitor bezel leaning back 8 degrees with the screen glass set in it, a
marquee leaning back above it); a joystick and six buttons on the panel. The
side art, the marquee's picture, the screen's picture, the speaker grille and
the T-moulding are paint; the screen and the marquee are their own materials
so they can be lit later. Assumed: a two-row six-button panel for one player.

**Derby race lane.** Five greybox alleys 3.70 by 0.42 by 0.12 m at 0.78 m pitch,
each with a 0.55 by 0.30 by 0.40 m horse block at its own place along it (the
race in progress). A kit of two `kyt_variant`s at the origin together: `alley`,
the player's roll lane (a bed with two side rails, a backstop and four blind
ball holes at the far end; the player stands at -Y and rolls toward +Y), and
`horse`, the racing target that runs along it: a flat painted-tin horse with
its jockey, one chunky cut-out on a sled that rides the bed between the rails,
nose toward +Y, at the alley's middle. Assumed: a roll lane with holes rather
than a squirt target, since "derby race" at a late-1990s boardwalk is the
roll-a-ball kind; the lane number, start and finish lines are paint.

**Derby prize display.** B1's prize rail, a 0.12 m bar 3.55 m long with four
0.5 by 0.7 to 0.8 m plush under it at 0.9 m pitch. Built as one prop: a round
pipe rail on three bolted wall brackets, and four plush of three generic
kinds (a round-eared bear, a long-eared bunny, a floppy-eared pup; no
characters, no brands) hanging plumb from it by ring clips, each at the
authored width and height, the tallest reaching z = 0. The rail is the same
piece as `prize_rail_shelf`'s `rail`, built by the same function.

**Coin pitch table.** B2's slab 3.45 by 3.75 by 0.18 m with nine plates on it in
a 3 by 3 grid at 1.1 m pitch. Built: the slab 3.75 m across the front and
3.45 m deep with a coin lip round its top edge, and nine glass dishes in two
shapes, five wide plates (0.42 to 0.46 m) and four small deep dishes (0.32 to
0.34 m), each at its authored place and size, sitting on the slab (the
greybox's float 2 cm over it).

**Basket toss.** B3's three hoops, tori 0.62 m across standing 0.1 m off the
backboard wall at 2.35 and 2.70 m, and three 0.46 m balls; the finish layer adds
a 0.5 by 1.65 m ball rack with three balls stacked in front of it. A kit of
three `kyt_variant`s: `basket`, a horizontal rim 0.62 m across (the carnival
kind, barely wider than the ball) with a net under it, on an arm from a
bolted backplate (back on y = 0, the net's bottom on z = 0); `ball`, 0.46 m;
and `rack`, a galvanized stand 0.5 m wide and 1.65 m tall that holds three balls
in a column behind two front rails. Assumed: the greybox's rings stand
vertical, facing the player; read with the catalog's "basket" and the booth's
"backboard wall" as a hoop-shot basket, so the rim is horizontal here. The
rim's hole is 0.52 m, so the authored ball passes.

**Prize rail and shelf.** The fixture the midway's prizes hang on and sit along,
a kit of two `kyt_variant`s, both wall-mounted: `rail`, B1's 3.55 m rail as a
70 mm pipe on three bolted wall brackets, and `shelf`, B2's 3.2 by 0.55 m plank
on three knee brackets. B2's hanging prize tubes are prizes, not the fixture,
and are left out.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, every edge rounded over, few big pieces. Fixings are the family bolt
(`family_bolt.py`) where a real one shows: the wall plates of the rail
brackets and the basket's backplate. No colour here: the materials are flat
stand-ins by surface for the painting to replace. Every part is tagged for
`unwrap_parts.py` (`kyt_unwrap`): `facets` for the bevelled or cut boxes, the
net and the clips, `lathe` for the turned parts and spheres; the true
cylinders (pipes, arms, tube frames) and the rim ring are left to its own
shape rules.
"""

import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_bolt  # noqa: E402

TAU = math.tau
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
HEAD = family_bolt.HEAD      # 35 mm, the family bolt's head
BAND = family_bolt.BAND      # a bolted band or strap: 1.6 heads wide

# colours are stand-ins for the painting
CABINET = (0.05, 0.12, 0.42, 1.0)    # the cabinet's laminate, the greybox's cobalt
SCREEN = (0.02, 0.03, 0.04, 1.0)     # the screen glass, lit later
MARQUEE = (0.95, 0.80, 0.35, 1.0)    # the marquee's translucent panel, lit later
BLACK = (0.03, 0.03, 0.03, 1.0)      # bezel, marquee frame, joystick
PANEL = (0.75, 0.72, 0.65, 1.0)      # the control panel overlay
STEEL = (0.55, 0.56, 0.58, 1.0)      # the coin door
BUTTON = (0.75, 0.10, 0.08, 1.0)
LANE = (0.86, 0.80, 0.62, 1.0)       # the alley's cream laminate
LANE_TRIM = (0.16, 0.14, 0.12, 1.0)  # its rails, backstop and the sled
HORSE = (0.70, 0.26, 0.18, 1.0)      # the painted-tin horse (the jockey is paint)
DARK_METAL = (0.06, 0.065, 0.065, 1.0)   # the prize rail and its brackets
PLUSH = {"blue": (0.16, 0.30, 0.62, 1.0), "mustard": (0.78, 0.60, 0.16, 1.0),
         "coral": (0.78, 0.30, 0.22, 1.0), "green": (0.22, 0.48, 0.26, 1.0)}
SLAB = (0.105, 0.47, 0.45, 1.0)      # the pitch table's turquoise top
LIP = (0.12, 0.10, 0.09, 1.0)        # its coin lip
GLASS = {"cream": (0.92, 0.90, 0.80, 1.0), "mustard": (0.85, 0.66, 0.22, 1.0), "coral": (0.80, 0.34, 0.26, 1.0)}
RIM = (0.85, 0.30, 0.10, 1.0)        # the basket's rim, orange
BACKPLATE = (0.90, 0.90, 0.88, 1.0)
NET = (0.92, 0.92, 0.90, 1.0)
BALL = (0.80, 0.36, 0.14, 1.0)       # rubber ball
GALVANIZED = (0.55, 0.58, 0.60, 1.0)
TIMBER = (0.80, 0.74, 0.60, 1.0)     # the shelf's bleached plank

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


def new_object(name, bm, mat, *, bevel=BEVEL, angle=35.0, segments=3, smooth=True, smooth_deg=40.0,
               unwrap="facets", variant=None, collide=True):
    """Finish a bmesh into an object in `export`, with its bevel applied and
    the part cleaned (every part passes through `clean`)."""
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
    clean(obj)
    if smooth:
        smooth_by_angle(obj, smooth_deg)
    if unwrap:
        obj["kyt_unwrap"] = unwrap
    if variant:
        obj["kyt_variant"] = variant
    if not collide:
        obj["kyt_collision"] = "none"
    return obj


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


def box(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def cylinder_bm(axis, centre, radius, lo, hi, sides=24):
    poly = [(centre[0] + radius * math.cos(TAU * i / sides),
             centre[1] + radius * math.sin(TAU * i / sides)) for i in range(sides)]
    return prism(poly, axis, lo, hi)


def rounded_rect(hx, hy, r, per=4):
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def lathe(profile, sides=24):
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


def sphere_profile(r, zc, n=12):
    return [(r * math.sin(math.pi * i / n), zc - r * math.cos(math.pi * i / n)) for i in range(n + 1)]


def ellipsoid(centre, radii, sides=14, rings=8):
    """A sphere of radius 1 stretched to `radii` and moved to `centre`."""
    bm = lathe(sphere_profile(1.0, 0.0, rings), sides)
    return move(bm, Matrix.Translation(centre) @ Matrix.Diagonal((*radii, 1.0)))


def torus_bm(R, r, major=24, minor=10):
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


def loft(rings, close_end=False):
    """Quads between successive rings of equal length (lists of points), open
    at both ends unless `close_end` caps the last."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if close_end:
        bm.faces.new(vs[-1])
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


def subtract(bm, cutters, name, mat, **kw):
    """Cut `cutters` (bmeshes) out of the shape `bm` and finish it."""
    kw.setdefault("bevel", BEVEL)
    base = new_object(name, bm, mat, bevel=0, smooth=False, unwrap=None)
    for i, cb in enumerate(cutters):
        cut = new_object(f"{name}_cut{i}", cb, mat, bevel=0, smooth=False, unwrap=None)
        mod = base.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        mod.solver = "EXACT"
        apply_modifiers(base)
        bpy.data.objects.remove(cut)
    # the bevel last, on the cut shape
    if kw["bevel"]:
        mod = base.modifiers.new("bevel", "BEVEL")
        mod.width = kw["bevel"]
        mod.segments = kw.get("segments", 3)
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(kw.get("angle", 35.0))
        apply_modifiers(base)
    clean(base)
    smooth_by_angle(base, kw.get("smooth_deg", 40.0))
    base["kyt_unwrap"] = kw.get("unwrap", "facets")
    if kw.get("variant"):
        base["kyt_variant"] = kw["variant"]
    if not kw.get("collide", True):
        base["kyt_collision"] = "none"
    return base


def frame_bm(hx, hy, width, r, lo, hi, per=3):
    """A rounded-rectangle picture frame `width` wide, as outer and inner prisms
    for `subtract`: the hole is cut a little taller so the boolean is clean."""
    outer = prism(rounded_rect(hx, hy, r, per), "z", lo, hi)
    inner = prism(rounded_rect(hx - width, hy - width, max(r - width, 0.004), per), "z", lo - 0.01, hi + 0.01)
    return outer, inner


def face_frame(p0, p1):
    """The frame of a part lying on a face of a side profile: the face runs up
    from (y0, z0) to (y1, z1) in the YZ plane, across the whole width in X.
    Local X is world X, local Y runs up the face, local Z is its outward
    normal; the origin is the face's middle."""
    (y0, z0), (y1, z1) = p0, p1
    d = Vector((0.0, y1 - y0, z1 - z0)).normalized()
    n = Vector((0.0, -d.z, d.y))
    m = Matrix((
        (1.0, 0.0, 0.0, 0.0),
        (0.0, d.y, n.y, (y0 + y1) / 2),
        (0.0, d.z, n.z, (z0 + z1) / 2),
        (0.0, 0.0, 0.0, 1.0)))
    return m, n


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


# --- the arcade cabinet ----------------------------------------------------------
#
# The greybox box is 0.82 wide (X), 0.80 deep and 1.72 m tall, its screen box
# 0.58 by 0.48 m at 0.90 to 1.38 m on the front. The side profile below is the
# classic upright, in (y, z) with the front toward -Y: the back is one flat
# face at AC_BACK, the depth to the control panel's lip is the greybox's 0.80.

AC_W = 0.82
AC_H = 1.72
AC_BACK = 0.38
AC_FRONT = -0.33                  # the lower front face (coin door)
AC_PANEL_LIP = (-0.42, 0.80, 0.88)   # the control panel's front edge: y, z bottom, z top
AC_PANEL_BACK = (-0.18, 0.92)     # where the panel meets the bezel
AC_BEZEL_TOP = (-0.095, 1.47)     # the monitor bezel leans back to here
AC_MARQUEE = ((-0.125, 1.49), (-0.06, AC_H))   # the marquee face, bottom and top
AC_SCREEN_W, AC_SCREEN_H = 0.58, 0.48
AC_BEZEL_W = 0.035
AC_MARQUEE_W, AC_MARQUEE_H = 0.70, 0.16
AC_MARQUEE_FRAME_W = 0.025
AC_COIN_W, AC_COIN_H, AC_COIN_Z = 0.26, 0.30, 0.55
AC_STICK_X = -0.17
AC_BUTTON_R = 0.02
AC_BUTTONS_X = (0.02, 0.10, 0.18)
AC_BUTTONS_U = (0.035, -0.035)    # the two rows, up and down the panel from its middle


def arcade_profile():
    lip_y, lip_z0, lip_z1 = AC_PANEL_LIP
    return [(AC_BACK, 0.0), (AC_FRONT, 0.0), (AC_FRONT, lip_z0 - 0.02), (lip_y, lip_z0), (lip_y, lip_z1),
            AC_PANEL_BACK, AC_BEZEL_TOP, AC_MARQUEE[0], AC_MARQUEE[1], (AC_BACK, AC_H)]


def build_arcade():
    cab = material("arcade_cabinet", CABINET)
    screen = material("arcade_screen", SCREEN)
    marquee = material("arcade_marquee", MARQUEE)
    black = material("arcade_black", BLACK)
    panel = material("arcade_panel", PANEL)
    steel = material("arcade_steel", STEEL)
    button = material("arcade_button", BUTTON)
    hw = AC_W / 2

    # the body: the side profile across the whole width, every edge rounded
    new_object("body", prism(arcade_profile(), "x", -hw, hw), cab, bevel=0.02)

    # the monitor: a black bezel frame proud of the leaning face, the glass set
    # in it 4 mm proud of the face
    m, _ = face_frame(AC_PANEL_BACK, AC_BEZEL_TOP)
    outer, inner = frame_bm(AC_SCREEN_W / 2 + AC_BEZEL_W, AC_SCREEN_H / 2 + AC_BEZEL_W, AC_BEZEL_W, 0.05, -0.004, 0.016)
    subtract(move(outer, m), [move(inner, m)], "bezel", black, bevel=0.005, segments=1, collide=False)
    new_object("screen", move(prism(rounded_rect(AC_SCREEN_W / 2, AC_SCREEN_H / 2, 0.015), "z", -0.004, 0.004), m),
               screen, bevel=0.002, segments=1, collide=False)

    # the marquee: a frame and a translucent panel on the leaning top face
    m, _ = face_frame(*AC_MARQUEE)
    outer, inner = frame_bm(AC_MARQUEE_W / 2 + AC_MARQUEE_FRAME_W, AC_MARQUEE_H / 2 + AC_MARQUEE_FRAME_W,
                            AC_MARQUEE_FRAME_W, 0.035, -0.004, 0.014)
    subtract(move(outer, m), [move(inner, m)], "marquee_frame", black, bevel=0.005, segments=1, collide=False)
    new_object("marquee", move(prism(rounded_rect(AC_MARQUEE_W / 2, AC_MARQUEE_H / 2, 0.012), "z", -0.004, 0.006), m),
               marquee, bevel=0.003, segments=1, collide=False)

    # the control panel: an overlay slab on the sloping face, with the stick
    # and six buttons standing up its normal
    lip_y, _, lip_z1 = AC_PANEL_LIP
    m, n = face_frame((lip_y, lip_z1), AC_PANEL_BACK)
    face_len = (Vector(AC_PANEL_BACK) - Vector((lip_y, lip_z1))).length
    # the overlay stops 3 cm short of the lip so its thickness never shows
    # past the lip's face, and 1.5 cm short of the bezel
    overlay = prism(rounded_rect(0.38, (face_len - 0.045) / 2, 0.03), "z", -0.004, 0.02)
    new_object("control_panel", move(move(overlay, Matrix.Translation((0.0, 0.0075, 0.0))), m),
               panel, bevel=0.008, segments=2, collide=False)
    # the stick: a shaft up into a ball top (the shaft meets the ball where
    # the ball is as wide as the shaft)
    shaft_r, ball_r, ball_z = 0.011, 0.03, 0.107
    a0 = math.asin(shaft_r / ball_r)
    stick = [(0.0, 0.0), (shaft_r, 0.0), (shaft_r, ball_z - ball_r * math.cos(a0))] + \
            [(ball_r * math.sin(a), ball_z - ball_r * math.cos(a)) for a in (a0 + (math.pi - a0) * i / 8 for i in range(1, 9))]
    new_object("joystick", move(lathe(stick, 12), m @ Matrix.Translation((AC_STICK_X, 0.0, 0.016))), black,
               bevel=0, unwrap="lathe", collide=False)
    for i, bx in enumerate(AC_BUTTONS_X):
        for j, u in enumerate(AC_BUTTONS_U):
            prof = [(0.0, 0.0), (AC_BUTTON_R, 0.0), (AC_BUTTON_R, 0.008), (AC_BUTTON_R - 0.004, 0.013),
                    (AC_BUTTON_R - 0.012, 0.016), (0.0, 0.017)]
            new_object(f"button_{j}{i}", move(lathe(prof, 12), m @ Matrix.Translation((bx, u, 0.016))), button,
                       bevel=0, unwrap="lathe", collide=False)

    # the coin door: a steel plate proud of the lower front
    m, _ = face_frame((AC_FRONT, AC_COIN_Z - 0.5), (AC_FRONT, AC_COIN_Z + 0.5))
    new_object("coin_door", move(prism(rounded_rect(AC_COIN_W / 2, AC_COIN_H / 2, 0.02), "z", -0.004, 0.012), m),
               steel, bevel=0.005, segments=2, collide=False)


def checks_arcade():
    return [f"cabinet {AC_W:.2f} wide, {AC_BACK - AC_PANEL_LIP[0]:.2f} deep, {AC_H:.2f} m tall; the greybox's 0.82 by 0.80 by 1.72",
            f"screen {AC_SCREEN_W:.2f} by {AC_SCREEN_H:.2f} m on a bezel leaning "
            f"{math.degrees(math.atan2(AC_BEZEL_TOP[0] - AC_PANEL_BACK[0], AC_BEZEL_TOP[1] - AC_PANEL_BACK[1])):.0f} deg, "
            f"its middle {(AC_PANEL_BACK[1] + AC_BEZEL_TOP[1]) / 2:.2f} m up (the greybox's 1.14)",
            f"control panel lip {AC_PANEL_LIP[2]:.2f} m, marquee {AC_MARQUEE[0][1]:.2f}..{AC_H:.2f} m, "
            f"coin door {AC_COIN_W:.2f} by {AC_COIN_H:.2f} at {AC_COIN_Z:.2f} m"]


# --- the derby race lane ---------------------------------------------------------
#
# The greybox alleys are 3.70 (along the race) by 0.42 by 0.12 m at 0.78 m
# pitch; a horse block 0.55 by 0.30 by 0.40 m sits on each. Here the race runs
# along +Y from the player at -Y; the horse variant stands at the alley's
# middle, its progress is the placement's.

DL_LEN, DL_W, DL_H = 3.70, 0.42, 0.12
DL_PITCH = 0.78
DL_BED_T = 0.07
DL_RAIL_W = 0.045
DL_HOLE_R = 0.05
DL_HOLES = ((-0.105, 1.42), (0.0, 1.42), (0.105, 1.42), (0.0, 1.64))
DH_LEN, DH_W = 0.55, 0.30
DH_SLED_T = 0.05
DH_PLATE_T = 0.06
# the horse and jockey in profile, (y forward, z up from the sled's top), one
# chunky cut-out like a painted-tin derby horse: nose, front leg stretched
# forward, belly, hind leg stretched back, tail, back, the jockey hunched over
# the withers, crest, ears, forehead
DH_PROFILE = [(0.29, 0.255), (0.28, 0.235), (0.25, 0.245), (0.215, 0.265), (0.165, 0.19), (0.145, 0.15),
              (0.20, 0.09), (0.255, 0.02), (0.265, 0.0), (0.22, 0.0), (0.17, 0.07), (0.125, 0.105),
              (0.0, 0.09), (-0.12, 0.105), (-0.17, 0.06), (-0.235, 0.0), (-0.275, 0.0), (-0.23, 0.065),
              (-0.185, 0.14), (-0.16, 0.20), (-0.20, 0.215), (-0.275, 0.215), (-0.265, 0.24), (-0.18, 0.255),
              (-0.08, 0.26), (-0.03, 0.27), (-0.02, 0.32), (0.0, 0.36), (0.03, 0.385), (0.065, 0.37),
              (0.062, 0.34), (0.075, 0.315), (0.12, 0.33), (0.175, 0.355), (0.19, 0.36), (0.20, 0.395),
              (0.215, 0.355), (0.25, 0.32), (0.28, 0.28)]
# the greybox horses' progress along their alleys, from each alley's middle
# (B1_derby_race: horse x less lane x), and the alleys' places across
DL_RACE = ((-1.56, -1.0), (-0.78, 0.1), (0.0, 0.65), (0.78, -0.35), (1.56, 0.95))


def build_derby_lane():
    lane = material("derby_lane", LANE)
    trim = material("derby_trim", LANE_TRIM)
    horse = material("derby_horse", HORSE)
    hw, hl = DL_W / 2, DL_LEN / 2

    # the alley: a bed with four blind ball holes at the far end, two side
    # rails sunk a centimetre into it, and a backstop between them
    holes = [cylinder_bm("z", (x, y), DL_HOLE_R, DL_BED_T - 0.05, DL_BED_T + 0.05, 16) for x, y in DL_HOLES]
    subtract(box(-hw, hw, -hl, hl, 0.0, DL_BED_T), holes, "bed", lane, bevel=0.012, variant="alley")
    for tag, s in (("l", -1.0), ("r", 1.0)):
        x_out, x_in = s * (hw - 0.005), s * (hw - 0.005 - DL_RAIL_W)
        new_object(f"rail_{tag}", box(min(x_out, x_in), max(x_out, x_in), -hl + 0.005, hl - 0.005, DL_BED_T - 0.01, DL_H),
                   trim, bevel=0.01, variant="alley")
    new_object("backstop", box(-(hw - 0.005 - DL_RAIL_W) + 0.002, hw - 0.005 - DL_RAIL_W - 0.002, hl - 0.07, hl - 0.012,
                               DL_BED_T - 0.01, DL_H + HEAD), trim, bevel=0.01, variant="alley")

    # the horse: a sled riding the bed between the rails, the cut-out horse
    # standing on it with its hooves sunk 5 mm in
    sled_z0 = DL_BED_T - 0.005
    new_object("sled", box(-DH_W / 2, DH_W / 2, -DH_LEN / 2, DH_LEN / 2, sled_z0, sled_z0 + DH_SLED_T), trim,
               bevel=0.012, variant="horse", collide=False)
    plate = prism([(y, z + sled_z0 + DH_SLED_T - 0.005) for y, z in DH_PROFILE], "x", -DH_PLATE_T / 2, DH_PLATE_T / 2)
    new_object("horse", plate, horse, bevel=0.012, segments=2, variant="horse", collide=False)


def checks_derby_lane():
    top = DL_BED_T - 0.005 + DH_SLED_T - 0.005 + max(z for _, z in DH_PROFILE)
    return [f"alley {DL_LEN:.2f} by {DL_W:.2f} by {DL_H:.2f} m (rails {DL_RAIL_W * 1000:.0f} mm, backstop {DL_H + HEAD:.3f} m), "
            f"holes {2 * DL_HOLE_R * 1000:.0f} mm at y {DL_HOLES[0][1]:.2f} and {DL_HOLES[3][1]:.2f}",
            f"horse {max(y for y, _ in DH_PROFILE) - min(y for y, _ in DH_PROFILE):.2f} long, sled {DH_W:.2f} wide, "
            f"plate {DH_PLATE_T * 1000:.0f} mm, top {top:.2f} m (the greybox's 0.49); the race runs toward +Y",
            f"the game's five alleys are {DL_PITCH:.2f} m apart; the greybox's horses stand "
            + ", ".join(f"{p:+.2f}" for _, p in DL_RACE) + " m from their alleys' middles"]


# --- the prize rail, the shelf and the derby prize display -----------------------
#
# B1_prize_rail: a 0.12 m bar 3.55 m long with four plush under it at 0.9 m
# pitch. B2_prize_shelf: 3.2 by 0.55 by 0.10 m. Both hang on a wall here: back
# on y = 0, lowest point on z = 0.

PR_LEN = 3.55
PR_R = 0.035                       # the pipe: 70 mm, two heads
PR_OFF = 0.33                      # its axis from the wall: a hanging plush clears it
PR_BRACKETS = (-1.40, 0.0, 1.40)
PR_PLATE_W, PR_PLATE_H, PR_PLATE_T = 0.08, 0.12, 0.012
PR_ARM_R = 0.021
SH_LEN, SH_D, SH_T = 3.20, 0.55, 0.10
SH_BRACKET_D, SH_BRACKET_H, SH_BRACKET_T = 0.40, 0.14, 0.05
SH_BRACKETS = (-1.30, 0.0, 1.30)
# the plush: (x, width, height, kind, colour), the greybox's four at 0.9 m
# pitch, each at its box's width and height
PD_PLUSH = ((-1.35, 0.52, 0.78, "bear", "blue"), (-0.45, 0.48, 0.68, "bunny", "mustard"),
            (0.45, 0.54, 0.82, "pup", "coral"), (1.35, 0.50, 0.72, "bear", "green"))
PD_GAP = 0.03                      # between the tallest plush and the rail


def build_rail(z_axis, variant=None, prefix=""):
    """The pipe rail on its three bolted wall brackets, its axis at z_axis."""
    metal = material("prize_metal", DARK_METAL)
    bolts = family_bolt.paint_of(metal)
    rail = new_object(f"{prefix}rail", tube_along([(-PR_LEN / 2, -PR_OFF, z_axis), (PR_LEN / 2, -PR_OFF, z_axis)], PR_R, 24),
                      metal, bevel=0, unwrap=None, smooth_deg=60, variant=variant)
    for i, x in enumerate(PR_BRACKETS):
        plate = box(x - PR_PLATE_W / 2, x + PR_PLATE_W / 2, -PR_PLATE_T, 0.0, z_axis - PR_PLATE_H / 2, z_axis + PR_PLATE_H / 2)
        arm = tube_along([(x, -PR_PLATE_T + 0.004, z_axis), (x, -PR_OFF + PR_R - 0.01, z_axis)], PR_ARM_R, 12)
        bracket = new_object(f"{prefix}bracket_{i}", join([plate, arm]), metal, bevel=0.004, segments=1,
                             smooth_deg=60, variant=variant)
        for k, dz in enumerate((-0.04, 0.04)):
            bolt = family_bolt.place(export(), f"{prefix}bolt_{i}_{k}", Vector((x, -PR_PLATE_T, z_axis + dz)), (0, -1, 0),
                                     against=[bracket], material=bolts)
            if variant:
                bolt["kyt_variant"] = variant
    return rail


def build_shelf(variant="shelf"):
    timber = material("shelf_timber", TIMBER)
    metal = material("prize_metal", DARK_METAL)
    z0 = SH_BRACKET_H - 0.005      # the plank sits 5 mm into the brackets' tops
    new_object("plank", box(-SH_LEN / 2, SH_LEN / 2, -SH_D - 0.005, -0.005, z0, z0 + SH_T), timber, bevel=0.03, variant=variant)
    # a solid knee gusset, its tip rounded; a real one's screws sit behind its
    # wall leg, so none show
    # (a short flat foot at the bottom, so the bevel leaves its base on z = 0)
    gusset = fillet([(0.0, 0.0, 0.0), (0.0, SH_BRACKET_H, 0.0), (-SH_BRACKET_D, SH_BRACKET_H, 0.0), (-0.03, 0.0, 0.0)], [0.0, 0.06], 4)
    gusset = [(p.x, p.y) for p in gusset]
    for i, x in enumerate(SH_BRACKETS):
        new_object(f"shelf_bracket_{i}", prism(gusset, "x", x - SH_BRACKET_T / 2, x + SH_BRACKET_T / 2), metal,
                   bevel=0.008, segments=2, variant=variant)


def build_rail_shelf():
    build_rail(0.06, variant="rail")
    build_shelf("shelf")


def checks_rail_shelf():
    return [f"rail {PR_LEN:.2f} m, {2 * PR_R * 1000:.0f} mm pipe, axis {PR_OFF:.2f} m off the wall at z {0.06:.2f} "
            f"(plates {PR_PLATE_W * 1000:.0f} by {PR_PLATE_H * 1000:.0f} mm, two bolts each); back on y = 0",
            f"shelf {SH_LEN:.2f} by {SH_D:.2f} m plank {SH_T:.2f} thick, top {SH_BRACKET_H - 0.005 + SH_T:.3f} m above its "
            f"brackets' feet; the greybox's shelf top is 2.85 m over the deck, the rail's middle 3.45 m"]


def plush(tag, x, w, h, kind, colour, z0):
    """One hanging plush of a generic kind at the authored width and height,
    its bottom at z0 and its top at z0 + h, plumb under the rail."""
    mat = material(f"plush_{colour}", PLUSH[colour])
    y = -PR_OFF
    kw = dict(bevel=0, unwrap="lathe", collide=False, smooth_deg=70)
    parts = []
    if kind == "bunny":
        parts.append(("body", ellipsoid((x, y, z0 + 0.28 * h), (0.5 * w, 0.42 * w, 0.28 * h), 16, 10)))
        parts.append(("head", ellipsoid((x, y - 0.02, z0 + 0.66 * h), (0.19 * h, 0.19 * h, 0.19 * h), 14, 8)))
        for s, side in ((-1.0, "l"), (1.0, "r")):
            ear = ellipsoid((0, 0, 0), (0.06 * h, 0.04 * h, 0.17 * h), 10, 6)
            m = Matrix.Translation((x + s * 0.09 * h, y, z0 + 0.83 * h)) @ Matrix.Rotation(math.radians(-s * 12.0), 4, "Y")
            parts.append((f"ear_{side}", move(ear, m)))
        snout = ellipsoid((x, y - 0.02 - 0.17 * h, z0 + 0.63 * h), (0.07 * h, 0.05 * h, 0.055 * h), 10, 6)
        parts.append(("snout", snout))
    else:
        parts.append(("body", ellipsoid((x, y, z0 + 0.30 * h), (0.5 * w, 0.45 * w, 0.30 * h), 16, 10)))
        parts.append(("head", ellipsoid((x, y - 0.02, z0 + 0.78 * h), (0.22 * h, 0.22 * h, 0.22 * h), 14, 8)))
        if kind == "bear":
            for s, side in ((-1.0, "l"), (1.0, "r")):
                parts.append((f"ear_{side}", ellipsoid((x + s * 0.17 * h, y - 0.02, z0 + 0.95 * h), (0.08 * h,) * 3, 10, 6)))
            parts.append(("snout", ellipsoid((x, y - 0.02 - 0.20 * h, z0 + 0.74 * h), (0.09 * h, 0.06 * h, 0.07 * h), 10, 6)))
        else:   # pup: floppy ears down the head's sides, a bigger snout
            for s, side in ((-1.0, "l"), (1.0, "r")):
                parts.append((f"ear_{side}", ellipsoid((x + s * 0.22 * h, y - 0.02, z0 + 0.72 * h), (0.035 * h, 0.08 * h, 0.14 * h), 10, 6)))
            parts.append(("snout", ellipsoid((x, y - 0.02 - 0.21 * h, z0 + 0.72 * h), (0.10 * h, 0.08 * h, 0.08 * h), 10, 6)))
    for s, side in ((-1.0, "l"), (1.0, "r")):
        parts.append((f"arm_{side}", ellipsoid((x + s * 0.48 * w, y - 0.05, z0 + 0.42 * h), (0.07 * w, 0.07 * w, 0.11 * h), 10, 6)))
        parts.append((f"foot_{side}", ellipsoid((x + s * 0.22 * w, y - 0.30 * w, z0 + 0.08 * h), (0.10 * w, 0.12 * w, 0.08 * h), 10, 6)))
    for name, bm in parts:
        new_object(f"{tag}_{name}", bm, mat, **kw)
    return z0 + h   # the hanging point, the head's top


def build_prize_display():
    metal = material("prize_metal", DARK_METAL)
    h_max = max(h for _, _, h, _, _ in PD_PLUSH)
    # the tallest plush hangs from the rail's underside less the gap and
    # reaches z = 0; the others hang shorter
    z_axis = h_max + PD_GAP + PR_R
    build_rail(z_axis)
    for i, (x, w, h, kind, colour) in enumerate(PD_PLUSH):
        # every plush hangs from the same rail, so its top is at h_max and a
        # shorter one ends higher off the ground
        top = plush(f"prize_{i}", x, w, h, kind, colour, h_max - h)
        # the clip: a ring round the rail and a link down into the head
        ring = move(torus_bm(PR_R + 0.008, 0.006, 16, 8), Matrix.Translation((x, -PR_OFF, z_axis)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        link = tube_along([(x, -PR_OFF, z_axis - PR_R - 0.012), (x, -PR_OFF, top - 0.02)], 0.005, 8)
        new_object(f"clip_{i}", join([ring, link]), metal, bevel=0, smooth_deg=60, collide=False)


def checks_prize_display():
    h_max = max(h for _, _, h, _, _ in PD_PLUSH)
    z_axis = h_max + PD_GAP + PR_R
    return [f"rail axis {z_axis:.3f} m above the lowest plush, {PR_OFF:.2f} m off the wall; the greybox's rail middle is "
            f"3.45 m over the deck and its lowest plush 2.56 m",
            "plush " + ", ".join(f"{kind} {w:.2f} by {h:.2f} ({colour})" for _, w, h, kind, colour in PD_PLUSH)
            + f", at {PD_PLUSH[1][0] - PD_PLUSH[0][0]:.1f} m pitch, hanging plumb"]


# --- the coin pitch table ---------------------------------------------------------
#
# B2's slab is 3.45 deep (Godot x) by 3.75 across (Godot z) by 0.18 m, its
# plates a 3 by 3 grid 1.1 m apart. Across is X here, deep is Y, the player at
# -Y. Each plate's (x, y) is the greybox's (z, x - 0.2) from the anchor.

CP_W, CP_D, CP_H = 3.75, 3.45, 0.18
CP_LIP_W, CP_LIP_H = 0.07, 0.05
CP_PLATES = ((-1.1, -1.0, 0.42, "cream"), (0.0, -1.0, 0.32, "mustard"), (1.1, -1.0, 0.45, "cream"),
             (-1.1, 0.05, 0.32, "coral"), (0.0, 0.05, 0.46, "cream"), (1.1, 0.05, 0.34, "mustard"),
             (-1.1, 0.95, 0.44, "cream"), (0.0, 0.95, 0.34, "coral"), (1.1, 0.95, 0.42, "cream"))


def dish_profile(d):
    """A wide shallow plate (d over 0.38 m) or a small deep dish, (r, z)."""
    R = d / 2
    if d > 0.38:
        return [(0.0, 0.0), (0.55 * R, 0.0), (0.78 * R, 0.012), (0.95 * R, 0.045), (R, 0.055), (0.93 * R, 0.055),
                (0.86 * R, 0.03), (0.6 * R, 0.015), (0.0, 0.015)]
    return [(0.0, 0.0), (0.5 * R, 0.0), (0.8 * R, 0.025), (0.96 * R, 0.07), (R, 0.08), (0.9 * R, 0.08),
            (0.8 * R, 0.055), (0.45 * R, 0.02), (0.0, 0.02)]


def build_coin_pitch():
    slab = material("pitch_slab", SLAB)
    lip = material("pitch_lip", LIP)
    hw, hd = CP_W / 2, CP_D / 2
    # the slab's top edge rolls over 3 cm; the lip stands inside that roll,
    # sunk a centimetre into the top
    new_object("slab", prism(rounded_rect(hw, hd, 0.08), "z", 0.0, CP_H), slab, bevel=0.03)
    inset = 0.035
    outer = prism(rounded_rect(hw - inset, hd - inset, 0.05), "z", CP_H - 0.01, CP_H + CP_LIP_H)
    inner = prism(rounded_rect(hw - inset - CP_LIP_W, hd - inset - CP_LIP_W, 0.02), "z", CP_H - 0.02, CP_H + CP_LIP_H + 0.01)
    subtract(outer, [inner], "lip", lip, bevel=0.015, segments=2)
    for i, (x, y, d, colour) in enumerate(CP_PLATES):
        glass = material(f"pitch_glass_{colour}", GLASS[colour])
        kind = "plate" if d > 0.38 else "dish"
        new_object(f"{kind}_{i + 1}", move(lathe(dish_profile(d), 20), Matrix.Translation((x, y, CP_H - 0.002))), glass,
                   bevel=0, unwrap="lathe", smooth_deg=60, collide=False)


def checks_coin_pitch():
    return [f"slab {CP_W:.2f} across by {CP_D:.2f} deep by {CP_H:.2f} m, lip {CP_LIP_W * 1000:.0f} mm wide {CP_LIP_H * 1000:.0f} mm up",
            "plates " + ", ".join(f"{d:.2f}" for _, _, d, _ in CP_PLATES) + " m at 1.1 m pitch, on the slab top; "
            "the greybox's slab top is 1.37 m over the deck"]


# --- the basket toss ---------------------------------------------------------------
#
# B3's hoops are 0.62 m tori 0.15 m off the backboard at 2.35 and 2.70 m over
# the deck (the wall starts at 1.05, a counter's height); the balls are 0.46 m;
# the finish layer's rack is 0.5 by 1.65 m with three balls stacked before it.

BT_RIM_R, BT_RIM_T = 0.285, 0.025       # 0.62 across outside, 0.52 inside
BT_RIM_OFF = 0.10                       # the rim's back from the wall
BT_NET_L = 0.42
BT_PLATE_W, BT_PLATE_H, BT_PLATE_T = 0.36, 0.30, 0.02
BT_BALL_R = 0.23
BT_RACK_W, BT_RACK_H = 0.50, 1.65
BT_RACK_TUBE = HEAD / 2                 # a one-head tube
BT_RACK_Y = -0.26                       # the ball column's axis from the back frame
BT_RACK_BALLS = 3
# the game's three hoops across the wall and their rim heights over the counter
BT_HOOPS = ((-1.25, 1.30), (0.0, 1.65), (1.25, 1.30))


def build_basket_toss():
    rim = material("toss_rim", RIM)
    plate = material("toss_backplate", BACKPLATE)
    net = material("toss_net", NET)
    ball = material("toss_ball", BALL)
    galv = material("toss_rack", GALVANIZED)

    # the basket: rim, net, arm, backplate with four bolts; the net's bottom on z = 0
    z_rim = BT_NET_L + BT_RIM_T
    y_rim = -(BT_RIM_OFF + BT_RIM_R + BT_RIM_T)
    new_object("rim", move(torus_bm(BT_RIM_R, BT_RIM_T, 28, 12), Matrix.Translation((0, y_rim, z_rim))), rim,
               bevel=0, unwrap=None, smooth_deg=60, variant="basket")
    rings = []
    for k, (r, z) in enumerate(((BT_RIM_R - 0.012, z_rim - 0.012), (0.24, z_rim - 0.12), (0.17, z_rim - 0.27), (0.12, 0.0))):
        rings.append([(r * math.cos(TAU * i / 16), y_rim + r * math.sin(TAU * i / 16), z) for i in range(16)])
    new_object("net", loft(rings), net, bevel=0, smooth=True, smooth_deg=80, variant="basket", collide=False)
    arm = tube_along([(0, -BT_PLATE_T + 0.004, z_rim), (0, y_rim + BT_RIM_R + 0.008, z_rim)], 0.016, 12)
    new_object("arm", arm, rim, bevel=0, unwrap=None, smooth_deg=60, variant="basket")
    back = new_object("backplate", box(-BT_PLATE_W / 2, BT_PLATE_W / 2, -BT_PLATE_T, 0.0, z_rim - 0.10, z_rim - 0.10 + BT_PLATE_H),
                      plate, bevel=0.008, segments=2, variant="basket")
    bolts = family_bolt.paint_of(plate)
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        b = family_bolt.place(export(), f"plate_bolt_{k}", Vector((sx * (BT_PLATE_W / 2 - 0.04), -BT_PLATE_T, z_rim + 0.05 + sz * 0.10)),
                              (0, -1, 0), against=[back], material=bolts)
        b["kyt_variant"] = "basket"

    # the ball
    sphere = new_object("ball", lathe(sphere_profile(BT_BALL_R, BT_BALL_R, 12), 20), ball, bevel=0, unwrap="lathe",
                        smooth_deg=70, variant="ball")

    # the rack: a back frame, two feet, a front cage holding a column of balls
    hw, t = BT_RACK_W / 2, BT_RACK_TUBE
    # one closed tube round the rectangle: the path starts and ends mid-way
    # along the bottom bar heading the same way, so `clean` welds the loop
    loop = [(0, 0, t), (-hw + t, 0, t), (-hw + t, 0, BT_RACK_H - t), (hw - t, 0, BT_RACK_H - t), (hw - t, 0, t), (0, 0, t)]
    frame = tube_along(fillet(loop, 0.06, 3), t, 10, caps=False)
    frame = move(frame, Matrix.Translation((0, -t, 0)))
    new_object("rack_frame", frame, galv, bevel=0, unwrap=None, smooth_deg=60, variant="rack")
    y_front = BT_RACK_Y - BT_BALL_R - t + 0.01
    cage = []
    for s in (-1.0, 1.0):
        x = s * (hw - t)
        cage.append(tube_along([(x, -2 * t, 0.10), (x, y_front, 0.10), (x, y_front, BT_RACK_H - 0.10), (x, -2 * t, BT_RACK_H - 0.10)], 0.012, 8))
    cage.append(tube_along([(-hw + t, y_front, 0.10), (hw - t, y_front, 0.10)], 0.012, 8))
    cage.append(tube_along([(-hw + t, y_front, BT_RACK_H - 0.10), (hw - t, y_front, BT_RACK_H - 0.10)], 0.012, 8))
    new_object("rack_cage", join(cage), galv, bevel=0, unwrap=None, smooth_deg=60, variant="rack")
    for s, side in ((-1.0, "l"), (1.0, "r")):
        x = s * (hw - t)
        new_object(f"rack_foot_{side}", box(x - 0.04, x + 0.04, y_front - 0.06, 0.0, 0.0, 0.02), galv, bevel=0.006, segments=2, variant="rack")
    for k in range(BT_RACK_BALLS):
        dup = sphere.copy()   # shares the ball's mesh: reshape one and all follow
        dup.name = f"rack_ball_{k}"
        dup["kyt_variant"] = "rack"
        dup.location = (0, BT_RACK_Y, 0.02 + 2 * BT_BALL_R * k)
        export().objects.link(dup)


def checks_basket_toss():
    z_rim = BT_NET_L + BT_RIM_T
    return [f"basket: rim {2 * (BT_RIM_R + BT_RIM_T):.2f} m outside, {2 * (BT_RIM_R - BT_RIM_T):.2f} inside, axis {z_rim:.3f} m "
            f"above the net's bottom and {BT_RIM_OFF + BT_RIM_R + BT_RIM_T:.2f} m off the wall; the game's rims sit "
            + " and ".join(f"{z:.2f}" for _, z in BT_HOOPS[:2]) + " m over the counter",
            f"ball {2 * BT_BALL_R:.2f} m; rack {BT_RACK_W:.2f} wide, {BT_RACK_H:.2f} tall, "
            f"{-(BT_RACK_Y - BT_BALL_R - BT_RACK_TUBE) + 0.06:.2f} deep, {BT_RACK_BALLS} balls in a column"]


# --- the file ------------------------------------------------------------------

KITS = {"derby_race_lane": ("alley", "horse"), "basket_toss": ("basket", "ball", "rack"), "prize_rail_shelf": ("rail", "shelf")}
ON_WALL = {"derby_prize_display", "basket_toss", "prize_rail_shelf"}


def group_variants(name):
    """Each piece of a kit after the first in its own `variant_<v>` collection,
    visible, so Christina can turn a piece off while she shapes another."""
    for v in KITS.get(name, ())[1:]:
        sub = bpy.data.collections.new(f"variant_{v}")
        export().children.link(sub)
        for o in [o for o in export().objects if o.get("kyt_variant") == v]:
            export().objects.unlink(o)
            sub.objects.link(o)


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

    def stage_object(tag, bm, colour):
        o = new_object(tag, bm, material(f"render_{tag}", colour), bevel=0, unwrap=None)
        export().objects.unlink(o)
        stage.objects.link(o)
        return o

    ground = stage_object("ground", prism([(-40, -40), (40, -40), (40, 40), (-40, 40)], "z", -0.02, -0.001), (0.50, 0.48, 0.44, 1))
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.4
    sun.rotation_euler = (math.radians(50), math.radians(12), math.radians(40))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    stage.objects.link(cam)
    scene.camera = cam

    parts = [o for o in export().all_objects if o.type == "MESH"]
    variants = list(KITS.get(name, ("",)))
    by_variant = {v: [o for o in parts if str(o.get("kyt_variant", "")) == v] for v in variants}
    first = by_variant[variants[0]]
    extras = []

    def only(objs):
        for o in parts + extras:
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

    def shoot(tag, objs, direction, target=None, lens=40, frame=None):
        """The camera along `direction` from the objects' centre, backed off
        until every vertex of `frame` (or the objects) is in frame."""
        pts = points(frame or objs)
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

    def wall(x0, x1, z0, z1, y=0.0):
        """A wall patch behind a wall-mounted piece, its face on y."""
        w = stage_object(f"wall_{len(extras)}", box(x0, x1, y, y + 0.08, z0, z1), (0.72, 0.63, 0.43, 1))
        extras.append(w)
        return w

    def copies(objs, offset, tag):
        out = []
        for o in objs:
            c = o.copy()
            c.name = f"{tag}_{o.name}"
            c.location = Vector(c.location) + Vector(offset)
            stage.objects.link(c)
            extras.append(c)
            out.append(c)
        return out

    # the standard views of the whole (a kit: its first piece, with its
    # other pieces where they stand in the file)
    whole = parts if name in ("derby_race_lane",) else first
    if name in ON_WALL:
        lo, hi = bounds(whole)
        w = wall(lo.x - 0.4, hi.x + 0.4, 0.0, hi.z + 0.4)
        views = whole + [w]
    else:
        views = whole
    only(views)
    for tag, d in (("three_quarter", (-0.75, -1.0, 0.55)), ("front", (0.0, -1.0, 0.18)), ("side", (1.0, 0.0, 0.18)), ("top", (0.0, -0.001, 1.0))):
        shoot(tag, views, d, frame=whole)
    # each other piece of a kit on its own
    for v in variants[1:]:
        objs = by_variant[v]
        views = objs
        if name in ON_WALL and v in ("rail", "shelf", "basket"):
            lo, hi = bounds(objs)
            views = objs + [wall(lo.x - 0.4, hi.x + 0.4, 0.0, hi.z + 0.4)]
        only(views)
        shoot(f"{v}_three_quarter", views, (-0.75, -1.0, 0.55), frame=objs)
    # beside a 1.7 m tall box, a guest's height
    only(whole)
    lo, hi = bounds(whole)
    scale_box = stage_object("scale_box", prism(rounded_rect(0.225, 0.14, 0.03), "z", 0.0, 1.7), (0.35, 0.35, 0.38, 1))
    extras.append(scale_box)
    scale_box.location = (hi.x + 0.45 + 0.225, min(lo.y, 0.0) - 0.3 if name in ON_WALL else 0.0, 0.0)
    only(whole + [scale_box])
    shoot("scale", whole + [scale_box], (-0.6, -1.0, 0.35))

    # the Boardwalk composition each came from
    if name == "arcade_cabinet":
        row = copies(first, (-2.15, 0, 0), "l") + copies(first, (2.15, 0, 0), "r")
        only(first + row)
        shoot("set", first + row, (-0.8, -1.0, 0.45))
    elif name == "derby_race_lane":
        set_objs = []
        for i, (x, progress) in enumerate(DL_RACE):
            set_objs += copies(by_variant["alley"], (x, 0, 0), f"a{i}") + copies(by_variant["horse"], (x, progress, 0), f"h{i}")
        only(set_objs)
        shoot("set", set_objs, (-0.7, -1.0, 0.6))
        only(by_variant["horse"])
        shoot("horse_side", by_variant["horse"], (1.0, 0.0, 0.15), lens=60)
    elif name == "basket_toss":
        wall_z0 = 0.0
        w = wall(-2.1, 2.1, wall_z0, 2.8)
        set_objs = [w]
        z_rim = BT_NET_L + BT_RIM_T
        for i, (x, z) in enumerate(BT_HOOPS):
            set_objs += copies(by_variant["basket"], (x, 0, z - z_rim), f"b{i}")
        # the greybox's rack stands at 1.55 across, overlapping its hoop;
        # shown clear of it here
        set_objs += copies(by_variant["rack"], (1.95, -0.02, 0.0), "rk")
        for i, (x, y) in enumerate(((-0.55, -1.6), (0.1, -1.1), (0.75, -1.4))):
            set_objs += copies(by_variant["ball"], (x, y, 0.0), f"bl{i}")
        only(set_objs)
        shoot("set", set_objs, (-0.6, -1.0, 0.5))
    elif name == "prize_rail_shelf":
        w = wall(-2.2, 2.2, 0.0, 3.8)
        set_objs = [w] + copies(by_variant["rail"], (0, 0, 3.39 - 0.06), "r") + copies(by_variant["shelf"], (0, 0, 2.60), "s")
        only(set_objs)
        shoot("set", set_objs, (-0.6, -1.0, 0.2), target=(0, -0.3, 2.6))
    elif name == "derby_prize_display":
        w = wall(-2.2, 2.2, 0.0, 3.8)
        set_objs = [w] + copies(first, (0, 0, 2.56), "d")
        only(set_objs)
        shoot("set", set_objs, (-0.6, -1.0, 0.0), target=(0, -0.3, 2.8))
        only(first)
        shoot("plush", first, (-0.4, -1.0, 0.2), target=(-0.9, -PR_OFF, 0.45), lens=60,
              frame=[o for o in first if o.name.startswith(("prize_0_", "prize_1_"))])


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    builders = {"arcade_cabinet": (build_arcade, checks_arcade),
                "derby_race_lane": (build_derby_lane, checks_derby_lane),
                "derby_prize_display": (build_prize_display, checks_prize_display),
                "coin_pitch_table": (build_coin_pitch, checks_coin_pitch),
                "basket_toss": (build_basket_toss, checks_basket_toss),
                "prize_rail_shelf": (build_rail_shelf, checks_rail_shelf)}
    if name not in builders:
        raise SystemExit(f"midway_games: open one of {', '.join(builders)}, not {name}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"midway_games: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for child in list(coll.children):   # a variant's own collection
            bpy.data.collections.remove(child)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    build, check = builders[name]
    build()
    group_variants(name)
    parts = [o for o in coll.all_objects if o.type == "MESH"]
    variants = sorted({str(o.get("kyt_variant", "")) for o in parts})
    print(f"midway_games: {name}: {len(parts)} parts, {triangles(parts)} triangles")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts if not o.get(family_bolt.TAG))
          + f"; bolts {sum(triangles([o]) for o in parts if o.get(family_bolt.TAG))}")
    for v in variants:
        group = [o for o in parts if str(o.get("kyt_variant", "")) == v]
        lo, hi = bounds(group)
        label = f"variant {v}" if v else "size"
        print(f"  {label}: {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x D x H), "
              f"x {lo.x:.3f}..{hi.x:.3f}, y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.3f}..{hi.z:.3f}, {len(group)} parts, {triangles(group)} triangles")
    for line in check():
        print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
