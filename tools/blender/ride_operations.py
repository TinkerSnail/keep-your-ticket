"""The Boardwalk's ride-operation props, first passes from the catalog notes
(2026-10-02): the eight families that stand at the wheel's and the coaster's
stations in `scenes/world/boardwalk_operations.tscn`. None has a photograph of
hers; each is the plainest faithful reading of its catalog line and of the
authored composition (exported into its file's locked `reference`
collection), at the composition's size, in the house style, for Christina to
reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<prop>.blend --python tools/blender/ride_operations.py -- \\
        [--replace] [--save] [--render <folder>]

`<prop>` is `boarding_gate` (PRP-OPS-001), `wheel_operator_control` (002),
`wheel_boarding_lift` (003), `maintenance_locker` (004),
`coaster_brake_console` (005), `block_lamp_estop` (006), `hose_reel` (007) or
`specialist_work_cart` (008). The tool builds whichever the file is named for
into `export`, one object a part, on z = 0 at the origin in the composition's
own frame (the greybox's: the prop faces -Y here, +Z in Godot, unless the
composition turned it; the exceptions are said below). It refuses while
`export` holds anything (it may be hers) unless `--replace`; it writes the
file only with `--save`; `--render` shoots three-quarter, front, side and top
views and one beside a 1.7 m box for scale into the folder (saved first, so
the render's camera, sun and ground never reach the file).

**Boarding gate.** The maquette's `load_gate_post_n/s` are 0.16 m square
posts 1.25 m tall, 2.0 m apart along Y, with a 1.9 m bar between them at
0.675 m, in front of the posts. Built: two posts on base plates with two
anchor bolts each and caps, and one leaf hinged on the +Y post: a welded tube frame (42 mm tube,
1.2 bolt heads) whose top rail is the maquette's bar, a bottom rail at
0.14 m, a solid panel between them where LOAD or EXIT is painted, two strap
hinges with bolts, and a slide-bolt latch into a bolted keeper on the -Y
post. Assumed: a single leaf (the exit gate is the same prop in other paint);
the leaf's top rail at the maquette's 0.675 m, which is low for a ride gate
(`G_RAIL_Z` is the one number to raise); the sign the maquette floats at
1.28 m is paint on the panel, not a header, since a header at post height
could not be walked under.

**Wheel operator control.** The maquette's `operator_console` is a 1.15 by
0.72 m cabinet 1.18 m tall with a 0.58 by 0.55 m `operator_panel` on its +X
face and the `ready_lamp` (0.10 m) and `stop_button` (0.13 m) standing out
of that face at 0.89 m. Built as the maquette has it, panel toward +X: a
plinth, the cabinet, a lipped top, the panel plate 45 mm proud on four
bolts, a domed ready lamp in a bezel, the mushroom stop button on a yellow
legend plate, and three chunky push buttons below them. Assumed: the panel
stays vertical and faces +X as the composition places it (turn the prop
-90 degrees about Z if its front should be -Y); the maquette's stool stands
at the opposite end from the panel, which is the composition's to sort out.

**Wheel boarding lift.** The maquette's `step_free_lift`: a 1.5 m square
shaft plinth 0.18 m thick, four 0.12 m frame posts to 4.30 m, a 1.58 m
header at 4.33 to 4.49 m, a 1.28 m square car 0.21 to 0.93 m, a 1.1 m wide
bridge at 4.05 to 4.29 m running 2.5 m east (+X) from the shaft, and a
1.18 m rail on its north edge. The platform's size and the heights are kept
exactly. Built: the plinth on four ground bolts, the posts, the header, the
car (a floor at 0.27 m, three solid walls to 0.90 m with a capping rail at
0.93 m, and a hinged gate on the open +X side), the bridge deck centred on
the car's opening, a solid-panel rail with a capping tube on both edges of
the bridge, and a blank sign board bolted between the south posts at 2.29 m
where the maquette floats "STEP-FREE LIFT". Assumed: the bridge centred on
the car (the maquette's is 0.52 m south of it, meeting only 0.69 m of the
opening) and starting at the shaft's east posts; a rail on the bridge's
south edge too (the maquette has only the north one, and a 4 m drop); the
header kept at the maquette's height although the car's walls would reach
4.95 m at the top landing.

**Maintenance locker.** The maquette's `maintenance_chest` is a 1.6 by
0.78 m box 0.82 m tall under a 1.68 by 0.86 m lid 0.12 m thick: a job
chest. Built: the rounded body, a crowned lid overhanging 4 cm all round on
a piano-hinge barrel along the back, a hasp (a staple on a plate, a slotted
strap hanging from the lid) at the front centre, and a D handle on a bolted
plate at each end. Assumed: closed, no padlock (dressing later); the R2
`maintenance_locker`, an upright 0.8 by 1.4 by 2.05 m cabinet, is the
family's other silhouette and not built here.

**Coaster brake console.** The maquette's `brake_console` is a 0.82 by
1.25 m cabinet 1.32 m tall with a 1.0 by 0.65 m `brake_panel` on its -X
face, and it carries the block lamp and the emergency stop on that panel.
Built, panel toward -X as the composition places it: a plinth, the cabinet,
a lipped top, the panel plate 60 mm proud on four bolts with two gauges and
three push buttons, and the brake lever on top of the cabinet: a tube lever
with a ball grip leaning toward the operator between two quadrant plates,
its pivot a bolt through each plate. Assumed: the lamp and the stop are not
on this panel, because the catalog makes them their own family on a post
(PRP-OPS-006); the lever on the top edge, since a 1.32 m cabinet leaves no
room for a floor lever at its front; "BRAKE" is paint on the lower front.

**Block lamp and emergency stop.** The maquette gives only the two spheres,
a 0.10 m green lamp and a 0.14 m red stop at 0.95 m on the brake panel; the
catalog wants them on a post. Built: a round base plate on four ground
bolts, a 90 mm post, the block-signal head at 1.92 m (a drum housing with a
hood over a 0.10 m domed lens facing -Y), and at 1.05 m an emergency-stop
station on a bolted band: a box, a yellow legend plate and the mushroom
head, 0.12 m across, facing -Y. Assumed: one aspect, not two; the heights
(lamp above heads, stop at hand height); the station facing the same way as
the lamp.

**Hose reel.** The maquette's `hose_reel` is a squashed ring 0.62 m across
hung 2.75 m up the pier pavilion's service wall, out of reach. Built
standing on the deck against a wall at +Y, so it is placed by its foot like
every other prop: a bolted base plate, a rectangular standpipe post 1.35 m
tall, the drum on an axle out of the post's front, a hub between two open
five-spoked flanges 0.62 m across so the hose shows between them, the hose
wound on the hub as one scalloped coil (three turns of 47 mm hose; the
turns' lines are paint), a crank with a knob on the front boss, its axle
nut a bolt, and the hose's tail hanging in a loop to a brass nozzle held in
a clip on the post's side. Assumed: floor-standing against the wall rather
than wall-hung (a wall-hung reel has no ground to be placed by, and the
maquette's height was unreachable); the hose size.

**Specialist work cart.** The maquette's `SH1_before_opening_cart` is a 1.5
by 0.82 m body 0.62 m tall with a 0.72 m handle bar out of its +X end at
0.55 m. Built: a two-deck steel utility cart, a lipped tray at 0.62 m and a
shelf at 0.30 m on four tube posts, two fixed wheels 0.25 m across on an
axle at the -X end and two swivel castors at the +X end, a tongue rising to
a T grip at 1.0 m along X, pinned to the tray's end with a bolt, and the
load that names the job on the tray: a toolbox, an oil can with a bent
spout, a grease gun with its hose, and a coiled cable. Assumed: a tray cart
rather than a closed chest, so the load shows; the tongue rises to 0.68 m
so it is pulled by hand; the four items the lead named and nothing else.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, every edge rounded over, few big pieces. Fixings are the family
bolt (`family_bolt.py`) where a real one would show: base plates, panel
corners, hinge straps, pivots and axle nuts; each takes the paint of the
part it sits on, 15% darker. No colour here: the materials are flat
stand-ins by surface (painted steel, an accent paint, cream panels, dark
metal, galvanized, rubber, signal red and green, yellow, brass) for the
painting to replace. Every part passes `clean()` (merged doubles, no
degenerate faces), which `unwrap_parts.py` needs, and is tagged
`kyt_unwrap`: `facets` for the bevelled and cut shapes, `lathe` for the
turned ones, nothing for a true cylinder.
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
HEAD = family_bolt.HEAD      # 35 mm, the family bolt's head
POST = family_bolt.POST      # a post or strap carrying a bolt: one head wide
BAND = family_bolt.BAND      # a bolted band: 1.6 heads wide
BAR = family_bolt.BAR        # a bolted bar: 1.2 heads, 42 mm
SINK = 0.005                 # how far a part sinks into what it stands on, so no two faces share a plane

# colours are stand-ins for the painting
PAINT = (0.08, 0.41, 0.40, 1.0)        # painted steel, the operations layer's turquoise
ACCENT = (0.72, 0.45, 0.06, 1.0)       # an accent paint: the gate's panel, the cable, grips
CREAM = (0.80, 0.74, 0.58, 1.0)        # cream panel faces and sign boards
DARK = (0.055, 0.068, 0.073, 1.0)      # dark painted structural steel
GALV = (0.35, 0.39, 0.39, 1.0)         # galvanized decks and frames
RUBBER = (0.018, 0.022, 0.024, 1.0)    # tyres, hoses
GREEN = (0.08, 0.50, 0.22, 1.0)        # the signal lens
RED = (0.68, 0.07, 0.035, 1.0)         # the stop button, the toolbox, the brake grip
YELLOW = (0.85, 0.65, 0.05, 1.0)       # legend plates and caution bands
BRASS = (0.62, 0.48, 0.18, 1.0)        # the hose nozzle, the oil can

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


def mats():
    return {
        "paint": material("ops_paint", PAINT), "accent": material("ops_accent", ACCENT),
        "cream": material("ops_cream", CREAM), "dark": material("ops_dark_metal", DARK),
        "galv": material("ops_galvanized", GALV), "rubber": material("ops_rubber", RUBBER),
        "green": material("ops_signal_green", GREEN), "red": material("ops_signal_red", RED),
        "yellow": material("ops_yellow", YELLOW), "brass": material("ops_brass", BRASS),
    }


def export():
    return bpy.data.collections["export"]


def new_object(name, bm, mat, *, bevel=BEVEL, angle=35.0, segments=3, smooth=True, smooth_deg=40.0,
               unwrap="facets", collide=True):
    """Finish a bmesh into an object in `export`, with its bevel applied and
    the mesh cleaned."""
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
    # (the lead's fix in picnic_tables.py, 2026-10-02). The evaluated mesh keeps
    # the object's slots; only fill them if it came back without any.
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


def subtract(base_bm, cutters, name, mat, **kw):
    """Cut `cutters` (bmeshes) out of the shape `base_bm` and finish it."""
    base = new_object(name, base_bm, mat, bevel=0, smooth=False, unwrap=None)
    for i, cb in enumerate(cutters):
        cut = new_object(f"{name}_cut{i}", cb, mat, bevel=0, smooth=False, unwrap=None)
        mod = base.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        mod.solver = "EXACT"
        apply_modifiers(base)
        bpy.data.objects.remove(cut)
    bevel = kw.get("bevel", BEVEL)
    if bevel:
        mod = base.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = kw.get("segments", 3)
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35)
        apply_modifiers(base)
    clean(base)
    smooth_by_angle(base)
    base["kyt_unwrap"] = kw.get("unwrap", "facets")
    return base


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


def box_bm(centre, size):
    """A plain box by its centre and full size."""
    cx, cy, cz = centre
    sx, sy, sz = size
    return prism([(cx - sx / 2, cy - sy / 2), (cx + sx / 2, cy - sy / 2),
                  (cx + sx / 2, cy + sy / 2), (cx - sx / 2, cy + sy / 2)], "z", cz - sz / 2, cz + sz / 2)


def rbox_bm(cx, cy, z0, z1, hx, hy, r, per=4):
    """A rounded-rectangle prism along Z, by its plan centre and half sizes."""
    return move(prism(rounded_rect(hx, hy, r, per), "z", z0, z1), Matrix.Translation((cx, cy, 0)))


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


def aim(direction):
    """The rotation that turns +Z (a lathe's axis) along `direction`."""
    return Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_matrix().to_4x4()


def lathe_at(profile, at, direction, sides=24):
    """A lathe whose axis runs along `direction` from `at` (the profile's z = 0)."""
    return move(lathe(profile, sides), Matrix.Translation(at) @ aim(direction))


def dome_profile(r, n=6):
    """A hemisphere from a flat base at z = 0 to its pole at r."""
    return [(r * math.cos(math.radians(90.0 * i / n)), r * math.sin(math.radians(90.0 * i / n))) for i in range(n + 1)]


def sphere_profile(r, zc, n=10):
    return [(r * math.sin(math.pi * i / n), zc - r * math.cos(math.pi * i / n)) for i in range(n + 1)]


def band_profile(r_in, r_out, z0, z1, c=0.005):
    """A ring on a post for `lathe`, its outer edges chamfered so it needs no
    bevel; its inner caps are hidden in the post."""
    return [(r_in, z0), (r_out - c, z0), (r_out, z0 + c), (r_out, z1 - c), (r_out - c, z1), (r_in, z1)]


def sector(r_in, r_out, a0, a1, per_deg=10.0):
    """An annular sector, from angle a0 to a1 (degrees)."""
    n = max(3, int(abs(a1 - a0) / per_deg))
    outer = [(r_out * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
              r_out * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    inner = [(r_in * math.cos(math.radians(a1 - (a1 - a0) * i / n)),
              r_in * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return outer + inner


def ring_bm(axis, centre, r_in, r_out, lo, hi, sides=16):
    """A flat annulus (an open flange, a washer) extruded along an axis: two
    concentric polygons, walls on both and quads between them top and bottom."""
    bm = bmesh.new()

    def at(a, b, t):
        if axis == "x":
            return (t, a, b)
        if axis == "y":
            return (a, t, b)
        return (a, b, t)

    rings = {}
    for key, r, t in (("il", r_in, lo), ("ol", r_out, lo), ("ih", r_in, hi), ("oh", r_out, hi)):
        rings[key] = [bm.verts.new(at(centre[0] + r * math.cos(TAU * i / sides), centre[1] + r * math.sin(TAU * i / sides), t))
                      for i in range(sides)]
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((rings["ol"][i], rings["ol"][j], rings["oh"][j], rings["oh"][i]))
        bm.faces.new((rings["ih"][i], rings["ih"][j], rings["il"][j], rings["il"][i]))
        bm.faces.new((rings["il"][i], rings["il"][j], rings["ol"][j], rings["ol"][i]))
        bm.faces.new((rings["oh"][i], rings["oh"][j], rings["ih"][j], rings["ih"][i]))
    return bm


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


def tube_loop(points, radius, normal, sides=10):
    """A closed round tube round a planar loop (a welded frame): rings at every
    point, the last joined to the first, no caps. `normal` is the plane's."""
    pts = [Vector(p) for p in points]
    nrm = Vector(normal).normalized()
    n = len(pts)
    bm = bmesh.new()
    rings = []
    for i in range(n):
        t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        bin_ = t.cross(nrm).normalized()
        rings.append([bm.verts.new(pts[i] + radius * (math.cos(TAU * k / sides) * nrm + math.sin(TAU * k / sides) * bin_))
                      for k in range(sides)])
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(sides):
            j = (k + 1) % sides
            bm.faces.new((a[k], a[j], b[j], b[k]))
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


def bolt(name, point, normal, against, mat, ground=False):
    """A family bolt on `against`, in that part's paint 15% darker."""
    return family_bolt.place(export(), name, Vector(point), normal, ground=ground, against=[against],
                             material=family_bolt.paint_of(mat))


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


# --- the boarding gate ---------------------------------------------------------
#
# The maquette (boardwalk_operations.tscn, R1 `load_gate_*`): two 0.16 m posts
# 1.25 m tall at y = +-1.0, a 0.12 by 0.14 m bar 1.9 m long at 0.675 m in front
# of them (x -0.13..-0.01). The exit gate is the same shape in other paint.

G_POST, G_POST_Z = 0.16, 1.25
G_POST_Y = 1.0
G_PLATE, G_PLATE_T = 0.26, 0.02
G_LEAF_X = -0.115             # the leaf's plane: tube centres, 35 mm in front of the posts' front face
G_TUBE_R = BAR / 2            # 42 mm tube, a bolted bar's size
G_RAIL_Z = 0.675              # the top rail: the maquette's bar centre (a 1.0 m leaf is the usual height)
G_FOOT_Z = 0.14               # the bottom rail
G_STILE_Y = 0.86              # the stiles, 39 mm clear of the posts' inner faces
G_HINGE_Z = (0.26, 0.56)
G_LATCH_Z = 0.60


def build_gate():
    m = mats()
    for tag, sy in (("n", 1.0), ("s", -1.0)):
        y = sy * G_POST_Y
        plate = new_object(f"plate_{tag}", box_bm((0, y, G_PLATE_T / 2), (G_PLATE, G_PLATE, G_PLATE_T)), m["dark"],
                           bevel=0.006, segments=1)
        new_object(f"post_{tag}", rbox_bm(0, y, G_PLATE_T - SINK, G_POST_Z, G_POST / 2, G_POST / 2, 0.02, 2), m["dark"],
                   bevel=0.012, segments=2)
        new_object(f"cap_{tag}", rbox_bm(0, y, G_POST_Z - 0.01, G_POST_Z + 0.035, 0.095, 0.095, 0.03, 2), m["dark"],
                   bevel=0.015, segments=2)
        # two anchor bolts a plate, on the diagonal clear of the leaf
        for k, (sx, syy) in enumerate(((1, -1), (-1, 1))):
            bolt(f"bolt_plate_{tag}_{k}", (sx * 0.095, y + syy * 0.095, G_PLATE_T), (0, 0, 1), plate, m["dark"], ground=True)

    # the leaf: a welded tube frame with rounded corners, a panel in it
    X, H, R, F = G_LEAF_X, G_STILE_Y, G_RAIL_Z, G_FOOT_Z
    loop = fillet([(X, 0.0, F), (X, -H, F), (X, -H, R), (X, H, R), (X, H, F), (X, 0.0, F)], 0.07, 4)[1:-1]
    new_object("leaf_frame", tube_loop(loop, G_TUBE_R, (1, 0, 0), 8), m["paint"], bevel=0, smooth_deg=60)
    zc = (R + F) / 2
    panel = prism([(y, z + zc) for y, z in rounded_rect(H, (R - F) / 2, 0.06, 3)], "x", X - 0.015, X + 0.015)
    new_object("leaf_panel", panel, m["accent"], bevel=0.008, segments=2)

    # two strap hinges round the hinge stile, bolted to the +Y post's front face
    for tag, z in zip(("bottom", "top"), G_HINGE_Z):
        collar = cylinder_bm("z", (X, H), 0.034, z - 0.05, z + 0.05, 12)
        strap = box_bm(((-0.125 + -0.07) / 2, (H + 1.06) / 2, z), (0.055, 1.06 - H, 0.044))
        hinge = new_object(f"hinge_{tag}", join([collar, strap]), m["dark"], bevel=0.006, segments=1)
        bolt(f"bolt_hinge_{tag}", (-0.125, 1.0, z), (-1, 0, 0), hinge, m["dark"])

    # the latch: a slide bolt in a housing on the leaf, into a keeper on the -Y post
    z = G_LATCH_Z
    new_object("latch_housing", box_bm((X, -0.77, z), (0.06, 0.14, 0.07)), m["dark"], bevel=0.008, segments=1)
    new_object("latch_bar", cylinder_bm("y", (X, z), 0.011, -0.97, -0.74, 10), m["dark"], bevel=0, unwrap=None)
    new_object("latch_knob", cylinder_bm("z", (X, -0.77), 0.011, z, z + 0.065, 8), m["dark"], bevel=0.004, segments=1,
               unwrap=None)
    kx0, kx1 = X - 0.03, -0.07           # from the leaf's front to inside the post's front face
    keeper = new_object("latch_keeper", box_bm(((kx0 + kx1) / 2, -0.955, z), (kx1 - kx0, 0.06, 0.07)),
                        m["dark"], bevel=0.006, segments=1)
    bolt("bolt_keeper", (X - 0.03, -0.955, z), (-1, 0, 0), keeper, m["dark"])


def checks_gate():
    return [f"posts {G_POST:.2f} m square, {G_POST_Z:.2f} m tall, {2 * G_POST_Y:.1f} m apart; leaf top rail at "
            f"{G_RAIL_Z:.3f} m (the maquette's bar), {2 * G_STILE_Y + 2 * G_TUBE_R:.2f} m wide, hinged on the +Y post",
            f"tube {2 * G_TUBE_R * 1000:.0f} mm (1.2 heads); the sign is paint on the panel"]


# --- the wheel operator control -------------------------------------------------
#
# The maquette (R1 `operator_console`, `operator_panel`, `ready_lamp`,
# `stop_button`): a 1.15 by 0.72 m cabinet 1.18 m tall, x -0.645..0.505; the
# panel 0.58 by 0.55 m on its +X face at 0.515..1.065 m; the lamp 0.10 m at
# (y 0.18, z 0.89) and the stop 0.13 m at (y -0.22, z 0.89), standing out of it.

W_X0, W_X1, W_HY, W_Z = -0.645, 0.505, 0.36, 1.18
W_PLINTH, W_TOP_T, W_INSET = 0.08, 0.06, 0.03
W_PANEL_HY, W_PANEL_Z0, W_PANEL_Z1, W_PANEL_PROUD = 0.29, 0.515, 1.065, 0.045
W_LAMP, W_STOP = (0.18, 0.89), (-0.22, 0.89)   # (y, z) on the panel
W_BUTTONS = ((-0.12, 0.68), (0.0, 0.68), (0.12, 0.68))


def cabinet(m, x0, x1, hy, z_top, plinth, top_t, inset):
    cx, hx = (x0 + x1) / 2, (x1 - x0) / 2
    new_object("plinth", rbox_bm(cx, 0, 0, plinth, hx - inset, hy - inset, 0.03, 2), m["dark"], bevel=0.01, segments=1)
    new_object("cabinet", rbox_bm(cx, 0, plinth - SINK, z_top - top_t + SINK, hx, hy, 0.05, 3), m["paint"], bevel=0.025, segments=2)
    new_object("top", rbox_bm(cx, 0, z_top - top_t, z_top, hx + 0.02, hy + 0.02, 0.06, 3), m["paint"], bevel=0.02, segments=2)


def face_panel(m, name, x_face, sx, hy, z0, z1, proud, corner=0.03):
    """A panel plate standing proud of a cabinet's +-X face (`sx` is the face's
    outward sign), on four corner bolts."""
    zc = (z0 + z1) / 2
    poly = [(y, z + zc) for y, z in rounded_rect(hy, (z1 - z0) / 2, corner)]
    lo, hi = sorted((x_face - sx * SINK, x_face + sx * proud))
    panel = new_object(name, prism(poly, "x", lo, hi), m["cream"], bevel=0.008, segments=2)
    face = x_face + sx * proud
    for k, (yy, zz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        bolt(f"bolt_{name}_{k}", (face, yy * (hy - 0.045), zc + zz * ((z1 - z0) / 2 - 0.045)), (sx, 0, 0), panel, m["cream"])
    return face


def push_button(m, name, face, sx, y, z):
    """A chunky round push button in its bezel, one turned part; its cap's colour is paint."""
    prof = [(0.032, 0), (0.032, 0.014), (0.024, 0.014), (0.024, 0.028), (0.018, 0.034), (0.0, 0.034)]
    new_object(name, lathe_at(prof, (face - sx * 0.004, y, z), (sx, 0, 0), 12), m["dark"], bevel=0, unwrap="lathe")


def build_wheel_control():
    m = mats()
    cabinet(m, W_X0, W_X1, W_HY, W_Z, W_PLINTH, W_TOP_T, W_INSET)
    face = face_panel(m, "panel", W_X1, 1, W_PANEL_HY, W_PANEL_Z0, W_PANEL_Z1, W_PANEL_PROUD)
    # the ready lamp: a bezel and a domed lens
    y, z = W_LAMP
    new_object("lamp_bezel", lathe_at(band_profile(0.02, 0.062, 0.0, 0.03), (face - 0.004, y, z), (1, 0, 0), 16),
               m["dark"], bevel=0, unwrap="lathe")
    new_object("lamp_lens", lathe_at(dome_profile(0.05, 5), (face + 0.022, y, z), (1, 0, 0), 16), m["green"], bevel=0,
               unwrap="lathe")
    # the stop button: a mushroom head on a yellow legend plate
    y, z = W_STOP
    new_object("stop_plate", lathe_at([(0.0, 0), (0.075, 0), (0.075, 0.012), (0.0, 0.012)], (face - 0.004, y, z), (1, 0, 0), 16),
               m["yellow"], bevel=0.003, segments=1, unwrap="lathe")
    mushroom = [(0.025, 0), (0.065, 0), (0.065, 0.03), (0.06, 0.042), (0.045, 0.052), (0.025, 0.058), (0.0, 0.06)]
    new_object("stop_button", lathe_at(mushroom, (face + 0.005, y, z), (1, 0, 0), 16), m["red"], bevel=0, unwrap="lathe")
    for k, (y, z) in enumerate(W_BUTTONS):
        push_button(m, f"button_{k}", face, 1, y, z)


def checks_wheel_control():
    return [f"cabinet {W_X1 - W_X0:.2f} by {2 * W_HY:.2f} m, {W_Z:.2f} m tall; panel {2 * W_PANEL_HY:.2f} by "
            f"{W_PANEL_Z1 - W_PANEL_Z0:.2f} m on the +X face at {W_PANEL_Z0:.3f}..{W_PANEL_Z1:.3f} m, {W_PANEL_PROUD * 1000:.0f} mm proud",
            f"ready lamp 0.10 m at (y {W_LAMP[0]:+.2f}, z {W_LAMP[1]:.2f}), stop 0.13 m at (y {W_STOP[0]:+.2f}, z {W_STOP[1]:.2f}): the maquette's"]


# --- the wheel boarding lift ---------------------------------------------------
#
# The maquette (R1 `step_free_lift`), in the file's frame: the shaft centred at
# (-1.025, 0.13); plinth 1.5 m square 0.18 m thick; posts 0.12 m square at
# +-0.68 from the centre, to 4.30 m; header 1.58 m square at 4.33..4.49 m; car
# 1.28 m square at 0.21..0.93 m; bridge 2.52 by 1.1 m at 4.05..4.29 m running
# east to x 1.815; a 1.18 m rail on its north edge to 5.48 m; the sign at 2.29 m.

L_C = Vector((-1.025, 0.13, 0.0))
L_PLINTH, L_PLINTH_T = 1.5, 0.18
L_POST, L_POST_D, L_POST_Z1 = 0.12, 0.68, 4.30
L_HEADER, L_HEADER_Z0, L_HEADER_Z1 = 1.58, 4.33, 4.49
L_CAR, L_CAR_Z0, L_CAR_Z1, L_FLOOR_T, L_WALL_T = 1.28, 0.21, 0.93, 0.06, 0.03
L_BRIDGE_X1, L_BRIDGE_W, L_BRIDGE_Z0, L_BRIDGE_Z1 = 1.815, 1.10, 4.05, 4.29
L_RAIL_Z1, L_RAIL_T = 5.48, 0.04
L_SIGN_Z = 2.29
L_RAIL_R = 0.025


def build_lift():
    m = mats()
    cx, cy = L_C.x, L_C.y
    h = L_CAR / 2
    plinth = new_object("plinth", rbox_bm(cx, cy, 0, L_PLINTH_T, L_PLINTH / 2, L_PLINTH / 2, 0.04), m["dark"], bevel=0.02)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        bolt(f"bolt_plinth_{k}", (cx + sx * 0.40, cy + sy * 0.70, L_PLINTH_T), (0, 0, 1), plinth, m["dark"], ground=True)
        tag = ("s" if sy < 0 else "n") + ("w" if sx < 0 else "e")
        new_object(f"frame_{tag}", rbox_bm(cx + sx * L_POST_D, cy + sy * L_POST_D, L_PLINTH_T - 0.01, L_HEADER_Z0 + 0.01,
                                           L_POST / 2, L_POST / 2, 0.015), m["dark"], bevel=0.01)
    new_object("header", rbox_bm(cx, cy, L_HEADER_Z0, L_HEADER_Z1, L_HEADER / 2, L_HEADER / 2, 0.05), m["galv"], bevel=0.02)

    # the car at the lower landing: floor, three walls, a capping rail, a gate on +X
    z_floor = L_CAR_Z0 + L_FLOOR_T
    new_object("car_floor", rbox_bm(cx, cy, L_CAR_Z0, z_floor, h, h, 0.03), m["galv"], bevel=0.015)
    t = L_WALL_T
    u = [(h, h), (-h, h), (-h, -h), (h, -h), (h, -h + t), (-h + t, -h + t), (-h + t, h - t), (h, h - t)]
    walls = move(prism(u, "z", z_floor - 0.01, L_CAR_Z1 - 0.021), Matrix.Translation((cx, cy, 0)))
    new_object("car_walls", walls, m["paint"], bevel=0.01, segments=2)
    rail_z = L_CAR_Z1 - 0.021
    yw = h - t / 2
    path = fillet([(cx + h, cy + yw, rail_z), (cx - yw, cy + yw, rail_z), (cx - yw, cy - yw, rail_z), (cx + h, cy - yw, rail_z)], 0.06, 4)
    new_object("car_rail", tube_along(path, 0.021, 10), m["dark"], bevel=0, smooth_deg=60)
    gx = cx + h - t / 2
    new_object("car_gate", box_bm((gx, cy, (z_floor + 0.01 + rail_z) / 2), (t, L_CAR - 2 * t - 0.04, rail_z - z_floor - 0.01)),
               m["paint"], bevel=0.01, segments=2)
    new_object("car_gate_rail", cylinder_bm("y", (gx, rail_z), 0.021, cy - (h - t - 0.02), cy + (h - t - 0.02), 10), m["dark"],
               bevel=0.006, segments=2, unwrap=None)
    for tag, z in (("bottom", 0.42), ("top", 0.80)):
        new_object(f"gate_hinge_{tag}", cylinder_bm("z", (gx + 0.03, cy + h - t), 0.026, z - 0.04, z + 0.04, 12), m["dark"],
                   bevel=0.005, segments=2, unwrap=None)

    # the bridge from the shaft's east posts, centred on the car's opening, with a rail each side
    x0 = cx + L_POST_D
    bw = L_BRIDGE_W / 2
    bridge = prism([(x0, cy - bw), (L_BRIDGE_X1, cy - bw), (L_BRIDGE_X1, cy + bw), (x0, cy + bw)], "z", L_BRIDGE_Z0, L_BRIDGE_Z1)
    new_object("bridge_deck", bridge, m["galv"], bevel=0.02)
    for tag, sy in (("n", 1.0), ("s", -1.0)):
        yr = cy + sy * (bw - L_RAIL_T / 2 - 0.01)
        xa, xb = x0 + L_POST / 2, L_BRIDGE_X1 - 0.03
        panel = box_bm(((xa + xb) / 2, yr, (L_BRIDGE_Z1 - 0.01 + L_RAIL_Z1 - 2 * L_RAIL_R) / 2),
                       (xb - xa, L_RAIL_T, L_RAIL_Z1 - 2 * L_RAIL_R - L_BRIDGE_Z1 + 0.01))
        cap = cylinder_bm("x", (yr, L_RAIL_Z1 - L_RAIL_R), L_RAIL_R, xa, xb, 12)
        new_object(f"bridge_rail_{tag}", join([panel, cap]), m["dark"], bevel=0.008, segments=2)

    # the sign board between the south posts, where the maquette floats its label
    y_face = cy - L_POST_D - L_POST / 2
    sign = new_object("sign_board", box_bm((cx, y_face - 0.01 + SINK, L_SIGN_Z), (2 * L_POST_D + L_POST, 0.02, 0.18)), m["cream"],
                      bevel=0.005, segments=2)
    for tag, sx in (("w", -1.0), ("e", 1.0)):
        bolt(f"bolt_sign_{tag}", (cx + sx * L_POST_D, y_face - 0.02 + SINK, L_SIGN_Z), (0, -1, 0), sign, m["cream"])


def checks_lift():
    return [f"platform {L_CAR:.2f} m square, floor at {L_CAR_Z0 + L_FLOOR_T:.2f} m, walls to {L_CAR_Z1:.2f} m: the maquette's car",
            f"frame to {L_POST_Z1:.2f} m, header {L_HEADER_Z0:.2f}..{L_HEADER_Z1:.2f} m; bridge {L_BRIDGE_X1 - (L_C.x + L_POST_D):.2f} by "
            f"{L_BRIDGE_W:.1f} m at {L_BRIDGE_Z0:.2f}..{L_BRIDGE_Z1:.2f} m, rails to {L_RAIL_Z1:.2f} m; sign at {L_SIGN_Z:.2f} m",
            "the bridge is centred on the car's opening (the maquette's lies 0.52 m south of it) and rails both edges"]


# --- the maintenance locker ----------------------------------------------------
#
# The maquette (R1 `maintenance_chest`, `_lid`): a 1.6 by 0.78 m body 0.82 m
# tall under a 1.68 by 0.86 m lid 0.12 m thick, 0.80..0.92 m.

M_HX, M_HY, M_Z = 0.80, 0.39, 0.80
M_LID_HX, M_LID_HY, M_LID_Z0, M_LID_Z1 = 0.84, 0.43, 0.79, 0.92
M_HANDLE_Z = 0.55


def build_locker():
    m = mats()
    body = new_object("body", rbox_bm(0, 0, 0, M_Z, M_HX, M_HY, 0.05), m["paint"], bevel=0.03)
    new_object("lid", rbox_bm(0, 0, M_LID_Z0, M_LID_Z1, M_LID_HX, M_LID_HY, 0.06), m["paint"], bevel=0.035)
    new_object("hinge", cylinder_bm("x", (M_LID_HY - 0.015, M_LID_Z0 + 0.012), 0.021, -M_HX + 0.03, M_HX - 0.03, 14), m["dark"],
               bevel=0.005, segments=2, unwrap=None)
    # the hasp: a staple on its plate, a slotted strap hanging from the lid over it
    yf = -M_HY
    staple_plate = new_object("staple_plate", box_bm((0, yf - 0.015 + SINK, 0.69), (0.10, 0.03 + SINK, 0.10)), m["dark"],
                              bevel=0.004, segments=2)
    loop = move(torus_bm(0.03, 0.007, 14, 6), Matrix.Translation((0, yf - 0.03 + SINK, 0.69)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    new_object("staple", loop, m["dark"], bevel=0, smooth_deg=60)
    yl = -M_LID_HY
    strap = box_bm((0, yl - 0.007 + 0.003, (0.62 + 0.86) / 2), (0.08, 0.014, 0.86 - 0.62))
    slot = box_bm((0, yl, 0.69), (0.024, 0.06, 0.09))
    subtract(strap, [slot], "hasp_strap", m["dark"], bevel=0.003, segments=1)
    # D handles on bolted plates at the ends
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        xf = sx * M_HX
        plate = new_object(f"handle_plate_{tag}", box_bm((xf + sx * (0.017 - SINK) / 2, 0, M_HANDLE_Z), (0.017 + SINK, 0.16, 0.10)),
                           m["dark"], bevel=0.004, segments=2)
        xp = xf + sx * 0.017
        for k, yy in enumerate((-0.055, 0.055)):
            bolt(f"bolt_handle_{tag}_{k}", (xp, yy, M_HANDLE_Z), (sx, 0, 0), plate, m["dark"])
        # a chunky D pull: the bar 28 mm, standing 65 mm off the plate
        path = fillet([(xf, -0.045, M_HANDLE_Z), (xp + sx * 0.065, -0.045, M_HANDLE_Z), (xp + sx * 0.065, 0.045, M_HANDLE_Z),
                       (xf, 0.045, M_HANDLE_Z)], 0.03, 3)
        new_object(f"handle_{tag}", tube_along(path, 0.014, 10), m["dark"], bevel=0, smooth_deg=60)
    return body


def checks_locker():
    return [f"body {2 * M_HX:.2f} by {2 * M_HY:.2f} m, {M_Z:.2f} m tall; lid {2 * M_LID_HX:.2f} by {2 * M_LID_HY:.2f} m to {M_LID_Z1:.2f} m, "
            "hinged along the back (+Y), hasp at the front (-Y)"]


# --- the coaster brake console --------------------------------------------------
#
# The maquette (R2 `brake_console`, `brake_panel`): a 0.82 by 1.25 m cabinet
# 1.32 m tall, x -0.38..0.44; the panel 1.0 by 0.65 m on its -X face at
# 0.525..1.175 m. The block lamp and the stop the maquette puts on the panel
# are PRP-OPS-006's, on a post.

K_X0, K_X1, K_HY, K_Z = -0.38, 0.44, 0.625, 1.32
K_PLINTH, K_TOP_T, K_INSET = 0.08, 0.06, 0.03
K_PANEL_HY, K_PANEL_Z0, K_PANEL_Z1, K_PANEL_PROUD = 0.5, 0.525, 1.175, 0.06
K_GAUGES = ((0.25, 1.0), (-0.25, 1.0))      # (y, z)
K_BUTTONS = ((-0.14, 0.72), (0.0, 0.72), (0.14, 0.72))
K_PIVOT = (-0.22, 1.30)                     # (x, z): the lever's pivot, in the top slab
K_QUAD_R = 0.17
K_LEVER_L, K_LEVER_DEG = 0.50, 125.0        # from +X in the XZ plane: up and toward the operator at -X


def build_brake_console():
    m = mats()
    cabinet(m, K_X0, K_X1, K_HY, K_Z, K_PLINTH, K_TOP_T, K_INSET)
    face = face_panel(m, "panel", K_X0, -1, K_PANEL_HY, K_PANEL_Z0, K_PANEL_Z1, K_PANEL_PROUD)
    for tag, (y, z) in zip(("l", "r"), K_GAUGES):
        bezel = [(0.025, 0), (0.085, 0), (0.085, 0.03), (0.07, 0.03), (0.07, 0.016), (0.025, 0.016)]
        new_object(f"gauge_{tag}", lathe_at(bezel, (face + 0.004, y, z), (-1, 0, 0), 16), m["dark"], bevel=0, unwrap="lathe")
        new_object(f"gauge_{tag}_face", lathe_at([(0.0, 0), (0.068, 0), (0.068, 0.006), (0.0, 0.006)], (face - 0.013, y, z), (-1, 0, 0), 16),
                   m["cream"], bevel=0, unwrap="lathe")
    for k, (y, z) in enumerate(K_BUTTONS):
        push_button(m, f"button_{k}", face, -1, y, z)
    # the brake lever between two quadrant plates on the top, pivoted on a bolt through each
    px, pz = K_PIVOT
    quad = [(px, pz)] + [(px + K_QUAD_R * math.cos(math.radians(a)), pz + K_QUAD_R * math.sin(math.radians(a)))
                         for a in range(165, 94, -7)]
    for tag, sy in (("l", -1.0), ("r", 1.0)):
        lo, hi = sorted((sy * 0.03, sy * 0.07))
        plate = new_object(f"quadrant_{tag}", prism(quad, "y", lo, hi), m["dark"], bevel=0.006, segments=1)
        bolt(f"bolt_pivot_{tag}", (px, sy * 0.07, pz), (0, sy, 0), plate, m["dark"])
    d = Vector((math.cos(math.radians(K_LEVER_DEG)), 0, math.sin(math.radians(K_LEVER_DEG))))
    start = Vector((px, 0, pz)) - d * 0.06
    end = Vector((px, 0, pz)) + d * K_LEVER_L
    new_object("lever", tube_along([start, end], 0.016, 10), m["dark"], bevel=0, unwrap=None)
    new_object("lever_grip", move(lathe(sphere_profile(0.038, 0.0, 8), 12), Matrix.Translation(end + d * 0.02)), m["red"], bevel=0,
               unwrap="lathe")


def checks_brake_console():
    end = Vector((K_PIVOT[0], 0, K_PIVOT[1])) + Vector((math.cos(math.radians(K_LEVER_DEG)), 0, math.sin(math.radians(K_LEVER_DEG)))) * K_LEVER_L
    return [f"cabinet {K_X1 - K_X0:.2f} by {2 * K_HY:.2f} m, {K_Z:.2f} m tall; panel {2 * K_PANEL_HY:.1f} by {K_PANEL_Z1 - K_PANEL_Z0:.2f} m "
            f"on the -X face at {K_PANEL_Z0:.3f}..{K_PANEL_Z1:.3f} m, {K_PANEL_PROUD * 1000:.0f} mm proud",
            f"lever pivot at (x {K_PIVOT[0]:+.2f}, z {K_PIVOT[1]:.2f}), grip at (x {end.x:+.2f}, z {end.z:.2f}), leaning to the operator at -X"]


# --- the block lamp and emergency stop -----------------------------------------
#
# The maquette (R2 `block_lamp`, `emergency_stop`): a 0.10 m green sphere and a
# 0.14 m red one, side by side at 0.95 m on the brake panel. Here on a post.

S_PLATE_R, S_PLATE_T, S_BOLT_R = 0.13, 0.02, 0.10
S_POST_R = 0.045                 # 90 mm: chunky, well over the bolt rule's one head
S_HEAD_Z, S_HEAD_R, S_HEAD_HY = 1.92, 0.085, 0.08
S_LENS_R = 0.05
S_HOOD_Y = -0.20
S_STOP_Z = 1.05
S_BOX = (0.14, 0.09, 0.16)
S_MUSHROOM_R, S_LEGEND_R = 0.06, 0.075


def build_block_lamp():
    m = mats()
    plate = new_object("plate", lathe([(S_PLATE_R, 0.0), (S_PLATE_R, S_PLATE_T)], 16), m["dark"], bevel=0.008, segments=1, unwrap="lathe")
    for k in range(4):
        th = math.radians(45.0 + 90.0 * k)
        bolt(f"bolt_plate_{k}", (S_BOLT_R * math.cos(th), S_BOLT_R * math.sin(th), S_PLATE_T), (0, 0, 1), plate, m["dark"], ground=True)
    new_object("post", cylinder_bm("z", (0, 0), S_POST_R, S_PLATE_T - SINK, S_HEAD_Z - S_HEAD_R + 0.03, 16), m["dark"], bevel=0, unwrap=None)
    # the signal head: a drum along Y, a hood over the lens, the lens in a bezel, facing -Y
    new_object("lamp_housing", cylinder_bm("y", (0, S_HEAD_Z), S_HEAD_R, -S_HEAD_HY, S_HEAD_HY, 16), m["dark"], bevel=0.01, segments=2,
               unwrap="lathe")
    hood = move(prism(sector(S_HEAD_R, S_HEAD_R + 0.02, 0.0, 180.0, 18.0), "y", S_HOOD_Y, -S_HEAD_HY + SINK), Matrix.Translation((0, 0, S_HEAD_Z)))
    new_object("lamp_hood", hood, m["dark"], bevel=0.004, segments=1)
    yf = -S_HEAD_HY
    new_object("lamp_bezel", lathe_at(band_profile(0.02, 0.062, 0.0, 0.03), (0, yf + 0.004, S_HEAD_Z), (0, -1, 0), 16), m["dark"], bevel=0,
               unwrap="lathe")
    new_object("lamp_lens", lathe_at(dome_profile(S_LENS_R, 5), (0, yf - 0.022, S_HEAD_Z), (0, -1, 0), 16), m["green"], bevel=0, unwrap="lathe")
    # the emergency stop station on a bolted band: box, legend plate, mushroom head, facing -Y
    bx, by, bz = S_BOX
    y_back = -S_POST_R + 0.01
    station = new_object("stop_box", box_bm((0, y_back - by / 2, S_STOP_Z), (bx, by, bz)), m["dark"], bevel=0.012)
    y_front = y_back - by
    new_object("stop_plate", lathe_at([(0.0, 0), (S_LEGEND_R, 0), (S_LEGEND_R, 0.012), (0.0, 0.012)], (0, y_front + 0.004, S_STOP_Z), (0, -1, 0), 16),
               m["yellow"], bevel=0.003, segments=1, unwrap="lathe")
    mushroom = [(0.022, 0), (S_MUSHROOM_R, 0), (S_MUSHROOM_R, 0.028), (0.055, 0.04), (0.042, 0.05), (0.022, 0.056), (0.0, 0.058)]
    new_object("stop_button", lathe_at(mushroom, (0, y_front - 0.005, S_STOP_Z), (0, -1, 0), 16), m["red"], bevel=0, unwrap="lathe")
    band = new_object("stop_band", lathe(band_profile(S_POST_R - 0.002, S_POST_R + 0.012, S_STOP_Z - BAND / 2, S_STOP_Z + BAND / 2), 16),
                      m["dark"], bevel=0, unwrap="lathe")
    bolt("bolt_band", (0, S_POST_R + 0.012, S_STOP_Z), (0, 1, 0), band, m["dark"])
    _ = station


def checks_block_lamp():
    return [f"post {2 * S_POST_R * 1000:.0f} mm on a {2 * S_PLATE_R:.2f} m plate; lens {2 * S_LENS_R:.2f} m at {S_HEAD_Z:.2f} m facing -Y, "
            f"head top {S_HEAD_Z + S_HEAD_R + 0.02:.2f} m",
            f"stop head {2 * S_MUSHROOM_R:.2f} m on a {2 * S_LEGEND_R:.2f} m legend plate at {S_STOP_Z:.2f} m; band {BAND * 1000:.0f} mm (1.6 heads)"]


# --- the hose reel -------------------------------------------------------------
#
# The maquette (pier `hose_reel`): a squashed ring 0.62 m across on the
# pavilion's service wall at 2.75 m. Here a standpipe reel on the deck, its
# back flat against a wall at y = +0.05.

H_WALL_Y = 0.05
H_POST_X, H_POST_Y, H_POST_Z1 = 0.08, 0.10, 1.35
H_PLATE_X, H_PLATE_Y, H_PLATE_T = 0.30, 0.22, 0.02
H_DRUM_Z = 0.95
H_FLANGE_R, H_CORE_R = 0.31, 0.10
H_D_BACK, H_D_FRONT = 0.09, 0.295          # the flanges' depths from the post's front face
H_HOSE_R = 0.0235                          # 47 mm hose, three turns a layer
H_NOZZLE = (-0.13, -0.13, 0.50)


def build_hose_reel():
    m = mats()
    yf = H_WALL_Y - H_POST_Y                 # the post's front face
    plate = new_object("plate", box_bm((0, H_WALL_Y - H_PLATE_Y / 2, H_PLATE_T / 2), (H_PLATE_X, H_PLATE_Y, H_PLATE_T)), m["dark"],
                       bevel=0.006, segments=2)
    for k, (sx, yy) in enumerate(((-1, -0.135), (1, -0.135), (1, 0.005), (-1, 0.005))):
        bolt(f"bolt_plate_{k}", (sx * 0.105, yy, H_PLATE_T), (0, 0, 1), plate, m["dark"], ground=True)
    new_object("post", rbox_bm(0, H_WALL_Y - H_POST_Y / 2, H_PLATE_T - SINK, H_POST_Z1, H_POST_X / 2, H_POST_Y / 2, 0.012, 2), m["dark"],
               bevel=0.008, segments=2)
    new_object("post_cap", rbox_bm(0, H_WALL_Y - H_POST_Y / 2, H_POST_Z1 - 0.01, H_POST_Z1 + 0.025, 0.05, 0.06, 0.02, 2), m["dark"], bevel=0.01,
               segments=2)
    new_object("axle", cylinder_bm("y", (0, H_DRUM_Z), 0.02, -0.33, yf + 0.02, 12), m["galv"], bevel=0, unwrap=None)
    f, c, d0, d1 = H_FLANGE_R, H_CORE_R, H_D_BACK, H_D_FRONT
    # the drum: a hub with a boss at the front, and two open spoked flanges so
    # the hose shows between them
    hub = [(0.03, d0), (0.07, d0), (0.07, d1 + 0.01), (0.05, d1 + 0.01), (0.05, d1 + 0.025), (0.03, d1 + 0.03), (0.0, d1 + 0.03)]
    new_object("hub", lathe_at(hub, (0, yf, H_DRUM_Z), (0, -1, 0), 16), m["paint"], bevel=0, unwrap="lathe")
    for tag, da in (("back", d0), ("front", d1 - 0.04)):
        y0, y1 = yf - da - 0.04, yf - da
        pieces = [ring_bm("y", (0, H_DRUM_Z), f - 0.045, f, y0, y1, 16)]
        for k in range(5):
            th = TAU * k / 5 + math.radians(90)
            spoke = box_bm(((f - 0.045 + 0.06) / 2 + 0.005, 0, 0), (f - 0.045 - 0.06 + 0.02, POST, 0.04 - 2 * SINK))
            pieces.append(move(spoke, Matrix.Translation((0, (y0 + y1) / 2, H_DRUM_Z)) @ Matrix.Rotation(th, 4, "Y")))
        new_object(f"flange_{tag}", join(pieces), m["paint"], bevel=0)
    # the hose as one coil: three turns show as scallops on the outer layer
    inner, outer = d0 + 0.04 - SINK, d1 - 0.04 + SINK
    r_out = c + 6 * H_HOSE_R
    pitch = (outer - inner) / 3
    coil = [(0.06, inner), (r_out - 0.016, inner)]
    for k in range(3):
        dc = inner + pitch * (k + 0.5)
        coil += [(r_out, dc - 0.3 * pitch), (r_out, dc + 0.3 * pitch), (r_out - 0.016, dc + 0.5 * pitch)]
    coil += [(0.06, outer)]
    new_object("hose_coil", lathe_at(coil, (0, yf, H_DRUM_Z), (0, -1, 0), 16), m["rubber"], bevel=0, unwrap="lathe")
    # the crank on the front flange's hub: an arm one head wide, the axle nut, a knob
    y_hub = yf - (d1 + 0.03)
    th = math.radians(-40.0)
    arm = box_bm((0.10, 0, 0), (0.22, POST, 0.02))
    move(arm, Matrix.Translation((0, y_hub - 0.01 + SINK, H_DRUM_Z)) @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Rotation(th, 4, "Z"))
    crank = new_object("crank_arm", arm, m["dark"], bevel=0.006, segments=2)
    bolt("bolt_axle", (0, y_hub - 0.02 + SINK, H_DRUM_Z), (0, -1, 0), crank, m["dark"])
    kx, kz = 0.20 * math.cos(th), 0.20 * math.sin(th)
    new_object("crank_knob", cylinder_bm("y", (kx, H_DRUM_Z + kz), 0.021, y_hub - 0.10, y_hub - 0.015 + SINK, 12), m["dark"],
               bevel=0.008, segments=2, unwrap=None)
    # the hose's tail: off the coil's underside, a hanging loop, up into the nozzle in its clip
    nx, ny, nz = H_NOZZLE
    y_mid = yf - (inner + outer) / 2
    tail = [(0.06, y_mid, H_DRUM_Z - r_out + 0.01), (0.15, y_mid, H_DRUM_Z - r_out - 0.06), (0.20, y_mid + 0.01, 0.52),
            (0.17, y_mid + 0.03, 0.40), (0.09, ny - 0.01, 0.32), (-0.01, ny, 0.30), (-0.09, ny, 0.34), (nx, ny, 0.42), (nx, ny, nz + 0.02)]
    new_object("hose_tail", tube_along(fillet(tail, 0.03, 2), H_HOSE_R * 0.8, 8), m["rubber"], bevel=0, smooth_deg=60)
    nozzle = [(0.016, 0), (0.028, 0.02), (0.028, 0.10), (0.022, 0.13), (0.016, 0.16), (0.016, 0.185), (0.0, 0.185)]
    new_object("nozzle", lathe_at(nozzle, (nx, ny, nz), (0, 0, 1), 12), m["brass"], bevel=0, unwrap="lathe")
    cx0, cx1 = nx - 0.045, -H_POST_X / 2 + SINK      # from past the nozzle to inside the post's side
    clip = box_bm(((cx0 + cx1) / 2, ny, nz + 0.05), (cx1 - cx0, 0.07, 0.05))
    hole = cylinder_bm("z", (nx, ny), 0.031, nz, nz + 0.12, 12)
    subtract(clip, [hole], "nozzle_clip", m["dark"], bevel=0.005, segments=1)


def checks_hose_reel():
    return [f"spoked flanges {2 * H_FLANGE_R:.2f} m across at {H_DRUM_Z:.2f} m, coil {2 * (H_CORE_R + 6 * H_HOSE_R):.2f} m; post {H_POST_Z1:.2f} m, "
            f"its back flat at y = {H_WALL_Y:+.2f} (the wall)",
            f"hose {2 * H_HOSE_R * 1000:.0f} mm; nozzle in its clip at ({H_NOZZLE[0]:+.2f}, {H_NOZZLE[1]:+.2f}, {H_NOZZLE[2]:.2f})"]


# --- the specialist work cart ----------------------------------------------------
#
# The maquette (R2 `SH1_before_opening_cart`): a 1.5 by 0.82 m body 0.62 m
# tall, x -1.005..0.495, and a 0.72 m handle bar out of the +X end at
# 0.49..0.61 m, to x 1.005.

C_CX, C_HX, C_HY, C_TOP = -0.255, 0.75, 0.41, 0.62
C_DECK_Z0, C_DECK_T, C_LIP_T = 0.55, 0.035, 0.03
C_SHELF_Z0, C_SHELF_T = 0.27, 0.03
C_WHEEL_R, C_WHEEL_W, C_WHEEL_X, C_WHEEL_Y = 0.125, 0.05, 0.50, 0.385
C_POST_R, C_POST_X, C_POST_Y = 0.02, 0.50, 0.32
C_HANDLE_Z, C_HANDLE_X1, C_HANDLE_RISE = 0.56, 1.0, 15.0
C_TOOLBOX = (-0.655, 0.0)
C_OIL_CAN = (-0.15, -0.20)
C_GREASE_GUN = (0.05, 0.20)
C_CABLE = (0.25, -0.15)


def wheel(m, name, centre, hub_bolt=None):
    """A solid-disc wheel on its axle along Y: a tyre and a hub, two parts."""
    x, y, z = centre
    w = C_WHEEL_W / 2
    tyre = [(C_WHEEL_R - 0.045, -w), (C_WHEEL_R - 0.012, -w), (C_WHEEL_R, -w + 0.012), (C_WHEEL_R, w - 0.012), (C_WHEEL_R - 0.012, w),
            (C_WHEEL_R - 0.045, w)]
    new_object(f"{name}_tyre", lathe_at(tyre, (x, y, z), (0, 1, 0), 16), m["rubber"], bevel=0, unwrap="lathe")
    hub = new_object(f"{name}_hub", lathe_at([(0.0, -w + 0.006), (C_WHEEL_R - 0.04, -w + 0.006), (C_WHEEL_R - 0.04, w - 0.006), (0.0, w - 0.006)],
                                             (x, y, z), (0, 1, 0), 16), m["paint"], bevel=0.005, segments=1, unwrap="lathe")
    if hub_bolt is not None:
        bolt(f"bolt_{name}", (x, y + hub_bolt * (w - 0.006), z), (0, hub_bolt, 0), hub, m["paint"])


def build_work_cart():
    m = mats()
    cx = C_CX
    deck_top = C_DECK_Z0 + C_DECK_T
    new_object("tray", rbox_bm(cx, 0, C_DECK_Z0, deck_top, C_HX, C_HY, 0.05, 3), m["paint"], bevel=0.012, segments=2)
    lip = rbox_bm(cx, 0, deck_top - 0.01, C_TOP, C_HX, C_HY, 0.05, 3)
    cut = rbox_bm(cx, 0, deck_top - 0.02, C_TOP + 0.02, C_HX - C_LIP_T, C_HY - C_LIP_T, 0.03, 3)
    subtract(lip, [cut], "tray_lip", m["paint"], bevel=0.008, segments=1)
    new_object("shelf", rbox_bm(cx, 0, C_SHELF_Z0, C_SHELF_Z0 + C_SHELF_T, C_HX - 0.06, C_HY - 0.05, 0.04, 2), m["paint"], bevel=0.01, segments=2)
    for sx, tx in ((-1.0, "b"), (1.0, "f")):
        for sy, ty in ((-1.0, "r"), (1.0, "l")):
            x, y = cx + sx * C_POST_X, sy * C_POST_Y
            z0 = C_WHEEL_R - 0.02 if sx < 0 else 0.21
            new_object(f"post_{tx}{ty}", cylinder_bm("z", (x, y), C_POST_R, z0, C_DECK_Z0 + 0.01, 12), m["dark"], bevel=0, unwrap=None)
    # the back axle and its two fixed wheels, nuts outboard
    xb = cx - C_WHEEL_X
    new_object("axle", cylinder_bm("y", (xb, C_WHEEL_R), 0.016, -C_WHEEL_Y - 0.01, C_WHEEL_Y + 0.01, 12), m["dark"], bevel=0, unwrap=None)
    wheel(m, "wheel_bl", (xb, C_WHEEL_Y, C_WHEEL_R), hub_bolt=1.0)
    wheel(m, "wheel_br", (xb, -C_WHEEL_Y, C_WHEEL_R), hub_bolt=-1.0)
    # the front castors: a fork of two cheeks under a swivel plate, trailing the post
    xf = cx + C_WHEEL_X
    for sy, ty in ((-1.0, "r"), (1.0, "l")):
        y = sy * C_POST_Y
        fx = xf + 0.04
        cheeks = [box_bm((fx, y + s * 0.0375, 0.15), (0.045, 0.015, 0.13)) for s in (-1.0, 1.0)]
        bridge = box_bm((xf + 0.02, y, 0.215), (0.10, 0.09, 0.02))
        new_object(f"castor_fork_{ty}", join(cheeks + [bridge]), m["dark"], bevel=0.004, segments=1)
        wheel(m, f"wheel_f{ty}", (fx, y, C_WHEEL_R))
    # the tongue: pinned to the tray's end with a bolt, rising to a T grip
    bracket = new_object("tongue_bracket", box_bm((cx + C_HX + 0.03 - SINK, 0, C_HANDLE_Z), (0.08, 0.10, 0.08)), m["dark"], bevel=0.008,
                         segments=2)
    bolt("bolt_tongue", (cx + C_HX + 0.03 - SINK, -0.05, C_HANDLE_Z), (0, -1, 0), bracket, m["dark"])
    x0 = cx + C_HX + 0.04
    rise = math.tan(math.radians(C_HANDLE_RISE))
    z1 = C_HANDLE_Z + (C_HANDLE_X1 - x0) * rise
    new_object("tongue", tube_along([(x0, 0, C_HANDLE_Z), (C_HANDLE_X1, 0, z1)], BAR / 2, 12), m["dark"], bevel=0, unwrap=None)
    new_object("grip", cylinder_bm("y", (C_HANDLE_X1, z1), BAR / 2, -0.19, 0.19, 12), m["dark"], bevel=0.012, segments=3, unwrap=None)
    # the load: a toolbox, an oil can, a grease gun, a coiled cable
    tx, ty = C_TOOLBOX
    toolbox = new_object("toolbox", rbox_bm(tx, ty, deck_top - 0.003, deck_top + 0.17, 0.23, 0.10, 0.02, 2), m["red"], bevel=0.012, segments=2)
    new_object("toolbox_lid", rbox_bm(tx, ty, deck_top + 0.16, deck_top + 0.215, 0.235, 0.105, 0.03, 2), m["red"], bevel=0.02, segments=2)
    bail = fillet([(tx - 0.09, ty, deck_top + 0.20), (tx - 0.09, ty, deck_top + 0.27), (tx + 0.09, ty, deck_top + 0.27),
                   (tx + 0.09, ty, deck_top + 0.20)], 0.025, 3)
    new_object("toolbox_handle", tube_along(bail, 0.009, 10), m["dark"], bevel=0, smooth_deg=60)
    new_object("toolbox_latch", box_bm((tx, ty - 0.10 - 0.006, deck_top + 0.155), (0.05, 0.016, 0.06)), m["dark"], bevel=0.003, segments=1)
    _ = toolbox
    ox, oy = C_OIL_CAN
    can = [(0.0, 0), (0.07, 0), (0.078, 0.012), (0.078, 0.05), (0.05, 0.11), (0.03, 0.14), (0.03, 0.17), (0.02, 0.18), (0.0, 0.18)]
    new_object("oil_can", lathe_at(can, (ox, oy, deck_top - 0.003), (0, 0, 1), 16), m["brass"], bevel=0, unwrap="lathe")
    spout = fillet([(ox, oy, deck_top + 0.15), (ox - 0.02, oy - 0.01, deck_top + 0.26), (ox - 0.16, oy - 0.05, deck_top + 0.34)], 0.06, 3)
    new_object("oil_spout", tube_along(spout, 0.008, 8), m["brass"], bevel=0, smooth_deg=60)
    new_object("oil_thumb", box_bm((ox + 0.045, oy + 0.02, deck_top + 0.10), (0.05, 0.012, 0.09)), m["dark"], bevel=0.003, segments=1)
    gx, gy = C_GREASE_GUN
    new_object("grease_barrel", cylinder_bm("x", (gy, deck_top + 0.027), 0.028, gx - 0.17, gx + 0.15, 14), m["dark"], bevel=0.006, segments=2,
               unwrap=None)
    new_object("grease_head", box_bm((gx + 0.19, gy, deck_top + 0.037), (0.08, 0.056, 0.08)), m["dark"], bevel=0.008, segments=2)
    new_object("grease_lever", tube_along([(gx + 0.18, gy, deck_top + 0.07), (gx - 0.02, gy, deck_top + 0.13)], 0.009, 8), m["dark"], bevel=0,
               unwrap=None)
    hose = fillet([(gx + 0.23, gy, deck_top + 0.045), (gx + 0.33, gy, deck_top + 0.045), (gx + 0.36, gy - 0.05, deck_top + 0.03),
                   (gx + 0.30, gy - 0.10, deck_top + 0.012)], 0.03, 3)
    new_object("grease_hose", tube_along(hose, 0.007, 8), m["rubber"], bevel=0, smooth_deg=60)
    kx, ky = C_CABLE
    new_object("cable_coil", move(torus_bm(0.15, 0.03, 16, 6), Matrix.Translation((kx, ky, deck_top + 0.028))), m["accent"], bevel=0,
               smooth_deg=60)


def checks_work_cart():
    return [f"tray {2 * C_HX:.2f} by {2 * C_HY:.2f} m, lip top {C_TOP:.2f} m, shelf {C_SHELF_Z0:.2f} m; wheels {2 * C_WHEEL_R:.2f} m, "
            f"tongue to x {C_HANDLE_X1:.2f} rising {C_HANDLE_RISE:.0f} deg",
            "load: toolbox, oil can, grease gun, coiled cable, on the tray"]


# --- the file ----------------------------------------------------------------

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

    def points(objs):
        dg = bpy.context.evaluated_depsgraph_get()
        pts = []
        for o in objs:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            pts += [o.matrix_world @ v.co for v in me.vertices]
            ev.to_mesh_clear()
        return pts

    def shoot(tag, objs, direction, lens=40):
        """The camera along `direction` from the objects' centre, backed off
        until every vertex is in frame."""
        pts = points(objs)
        lo, hi = Vector(map(min, *pts)), Vector(map(max, *pts))
        centre = (lo + hi) / 2
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

    # the views look at the prop's working face: -Y for most, the panel's side
    # for the two consoles, which the composition turns
    front = Vector(FRONT.get(name, (0, -1, 0)))
    side = Vector((front.y, -front.x, 0))     # the prop's left as seen from its front: -X when it faces -Y
    shoot("three_quarter", parts, front * 1.0 + side * 0.75 + Vector((0, 0, 0.55)))
    shoot("front", parts, front * 1.0 + Vector((0, 0, 0.18)))
    shoot("side", parts, -side * 1.0 + Vector((0, 0, 0.18)))
    shoot("top", parts, (0.0, -0.001, 1.0))
    # beside a 1.7 m tall box, a guest's height, standing off the prop's side
    box = new_object("scale_box", prism(rounded_rect(0.225, 0.14, 0.03), "z", 0.0, 1.7), material("render_box", (0.35, 0.35, 0.38, 1)), bevel=0)
    export().objects.unlink(box)
    stage.objects.link(box)
    lo, hi = bounds(parts)
    centre = (lo + hi) / 2
    reach = abs((hi - lo).dot(side)) / 2 + 0.45 + 0.225
    box.location = (centre.x - side.x * reach, centre.y - side.y * reach, 0.0)
    shoot("scale", parts + [box], front * 1.0 + side * 0.6 + Vector((0, 0, 0.35)))


FRONT = {"wheel_operator_control": (1, 0, 0), "coaster_brake_console": (-1, 0, 0)}


BUILDERS = {
    "boarding_gate": (build_gate, checks_gate),
    "wheel_operator_control": (build_wheel_control, checks_wheel_control),
    "wheel_boarding_lift": (build_lift, checks_lift),
    "maintenance_locker": (build_locker, checks_locker),
    "coaster_brake_console": (build_brake_console, checks_brake_console),
    "block_lamp_estop": (build_block_lamp, checks_block_lamp),
    "hose_reel": (build_hose_reel, checks_hose_reel),
    "specialist_work_cart": (build_work_cart, checks_work_cart),
}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in BUILDERS:
        raise SystemExit(f"ride_operations: open one of {', '.join(BUILDERS)}, not {name}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"ride_operations: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    build, check = BUILDERS[name]
    build()
    parts = [o for o in coll.all_objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    print(f"ride_operations: {name}: {len(parts)} parts, {triangles(parts)} triangles, "
          f"{hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x D x H), x {lo.x:.3f}..{hi.x:.3f}, "
          f"y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.3f}..{hi.z:.3f}")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts if not o.get(family_bolt.TAG))
          + f"; bolts {sum(1 for o in parts if o.get(family_bolt.TAG))} x 144")
    for line in check():
        print("  " + line)
    ref = [o for o in bpy.data.collections["reference"].objects if o.type == "MESH" and o.name.startswith("greybox_")]
    if ref:
        glo, ghi = bounds(ref)
        print(f"  greybox: x {glo.x:.3f}..{ghi.x:.3f}, y {glo.y:.3f}..{ghi.y:.3f}, z {glo.z:.3f}..{ghi.z:.3f}")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
