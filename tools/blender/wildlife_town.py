"""The town's five animals, a first pass (2026-10-03): the raccoon, the cat,
the mouse, the rat and the dog of the back lots, bins and streets round the
park. Christina asked for them on 2026-09-29; they stand in `prop-library.md`
as PRP-WILD-029 to 033. None has a photograph of hers; each is the ordinary
adult of its kind at real size, in the house style, for her to reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<animal>.blend --python tools/blender/wildlife_town.py -- \\
        [--replace] [--save] [--render <folder>]

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \\
        --python tools/blender/wildlife_town.py -- --lineup <png>

`<animal>` is `raccoon` (PRP-WILD-029), `cat` (030), `mouse` (031), `rat` (032)
or `dog` (033). The tool builds whichever the file is named for into `export`,
one object a part, head toward -Y here (+Z in Godot), feet on z = 0, the plan's
bounding box centred on the origin, real metres. It refuses while `export`
holds anything (it may be hers) unless `--replace`; it writes the file only
with `--save`; `--render` shoots three-quarter, front, side and top views and
one beside a 1.7 m box for scale into the folder (saved first, so the render's
camera, sun and ground never reach the file). `--lineup` opens no prop file: it
appends the five saved animals into an empty scene, stands them in a row
beside the 1.7 m box at true relative size and renders one picture; nothing is
saved.

**One kit, five bodies.** Every animal is the same quadruped kit read from its
own proportions (`SPECIES`), each form drawn as a side profile and a plan
width so it reads as a drawing would:

- `body`: the trunk and neck as one shell, lofted rump to throat through
  stations of (y, top, bottom, half width), a smooth curve through them and a
  round cap at each end. One shell, so the neck has no seam.
- `head`: the skull and muzzle as one shell lofted the same way, back of the
  skull to the tip of the nose. `nose`, `eye_left` and `eye_right` are balls
  seated on its surface (found by casting at it, so they sit on the head
  however it is reshaped); the ears' bases are found the same way.
- `jaw`: the lower jaw, a flattened tube under the muzzle whose underside
  shows as the chin.
- `ear_left`, `ear_right`: a forward-facing pad ("round", the rodents), a
  thin cone ("point", the cat), a rounded cone ("blunt", the raccoon) or a
  pad hanging down the side of the head ("flop", the dog).
- `leg_front_left` and the other three: a tapering tube from the shoulder or
  hip down through the elbow or knee, with the paw, an egg whose lowest point
  is exactly z = 0, joined on.
- `tail_base`, `tail_mid` (the cat), `tail_tip`: one smooth curve cut into
  segments; each segment starts a little thinner than the last ended, so the
  round ends nest at the joint instead of sharing a surface.

Left and right are the animal's own: it faces -Y, so its left is +X (Blender's
`.L` side), the rule the gull keeps facing +Y. Every moving part hangs under an
empty at its joint, so motion can be added
later without re-cutting anything (the gull's idea,
`assets/source/wildlife/gull_adult.blend`): `head_pivot` where the neck meets
the skull; `jaw_pivot` at the jaw hinge, `ear_left_pivot` and `ear_right_pivot`
at the ear bases, all children of `head_pivot`; `leg_front_left_pivot`,
`leg_front_right_pivot` at the shoulders and `leg_hind_left_pivot`,
`leg_hind_right_pivot` at the hips; `tail_pivot` at the tail's root with
`tail_mid_pivot` (the cat) and `tail_tip_pivot` nested down it. A root empty
named for the animal holds the body and the pivots. No armature, no
animation: how each moves is a separate decision. Every part carries
`kyt_collision = "none"`; ambient wildlife does not block the player.

**Raccoon.** Adult *Procyon lotor*, standing on all fours, back arched, the
hips higher than the shoulders, head low and level with the back. Head and
body 0.60 m, tail 0.27 m hanging in a curve, 0.26 m at the shoulder and 0.32 m
at the arch. A broad face with cheek ruffs narrowing to a short pointed
muzzle, rounded ears upright on top, a thick bushy tail, long flat hind feet.
The mask and the tail's rings are paint.

**Cat.** Adult domestic shorthair, standing on all fours, tail up with a
hooked tip (the greeting carriage). Head and body 0.51 m, tail 0.30 m, 0.25 m
at the shoulder. Round head with full cheeks and a short muzzle, big upright
triangular ears, slim legs, small round paws. The coat is paint and its colour
a per-placement choice, so the fur stand-in is a neutral warm grey.

**Mouse.** Adult house mouse *Mus musculus*, on all fours. Head and body
0.085 m, a thin tail as long again trailing on the ground, 0.035 m at the back.
Pear-shaped, compact; a pointed snout; big bulging eyes; big round ears about
two thirds the head's height. Ears and tail wear the skin stand-in.

**Rat.** Adult Norway rat *Rattus norvegicus*, the back-lot rat (the roof rat
is slighter, with a longer tail and bigger ears). On all fours, head and body
0.23 m, a thick tapering tail 0.21 m, shorter than the body, 0.085 m at the
back. Against the mouse: nearly three times the length, a long heavy body, a
longer head with a blunt snout, small eyes, small ears about a third of the
head's height, and a tail three times as thick. Ears and tail skin-coloured.

**Dog.** A generic medium mixed-breed dog, no recognisable breed and no
character: 0.55 m at the withers, head and body 0.96 m, standing square, a
deep chest and a tuck-up at the loin, a medium muzzle with a stop, drop ears
and a 0.33 m tail hanging relaxed. About 20 kg.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
few big rounded forms, slightly simplified proportions (heads and paws a
little large, legs a little thick), no fine detail; fur, whiskers, claws,
markings, the mask and the inside of the ears are paint. Materials are flat
stand-ins by surface: `<animal>_fur`, `<animal>_dark` (eyes and nose) and, for
the mouse and rat, `<animal>_skin` (ears and tail). Budgets asked for: mouse
and rat 1,200 triangles each, cat and raccoon 2,500, dog 3,000; the tool
prints the real counts. The balls (eyes, nose) are tagged `lathe` for
`unwrap_parts.py`; the lofted and tube parts are left to its own shape rules.
"""

import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

TAU = math.tau
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))

# colours are stand-ins for the painting
FUR = {"raccoon": (0.36, 0.34, 0.32, 1.0),    # a grizzled grey; the mask and rings are paint
       "cat": (0.50, 0.46, 0.40, 1.0),        # neutral warm grey; the coat is chosen per placement
       "mouse": (0.40, 0.36, 0.32, 1.0),      # grey-brown
       "rat": (0.36, 0.28, 0.21, 1.0),        # brown
       "dog": (0.62, 0.46, 0.28, 1.0)}        # tan
DARK = (0.03, 0.03, 0.035, 1.0)               # eyes and nose
SKIN = (0.80, 0.56, 0.52, 1.0)                # a rodent's ears and tail


# --- building blocks -------------------------------------------------------

def material(name, colour):
    """A flat stand-in; the colour is set on every run so a re-run picks up a
    change (a material survives `--replace`)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = colour
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    mat.diffuse_color = colour
    return mat


def export():
    return bpy.data.collections["export"]


def clean(obj):
    """Merge coincident vertices and drop faces with no area, so a joined part
    is one clean shell per piece (unwrap_parts.py needs it so)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=bm.edges)
    bad = [f for f in bm.faces if f.calc_area() < 1e-12]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def smooth_all(obj, deg=75.0):
    """Everything here is a rounded form: every face smooth, only a real
    crease (over `deg`) left sharp."""
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(deg))
    bm.to_mesh(mesh)
    bm.free()


def ring_loft(rings):
    """Faces between successive rings. A ring is a list of points, or a single
    point (a Vector) for a pole; quads between two rings, a fan to a pole."""
    bm = bmesh.new()
    vs = []
    for ring in rings:
        if isinstance(ring, Vector):
            vs.append([bm.verts.new(ring)])
        else:
            vs.append([bm.verts.new(p) for p in ring])
    for a, b in zip(vs, vs[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        n = max(len(a), len(b))
        for i in range(n):
            j = (i + 1) % n
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    return bm


def lathe(profile, sides=16):
    """An (r, z) outline revolved about Z, bottom to top; r = 0 is a pole."""
    rings = []
    for r, z in profile:
        if r < 1e-9:
            rings.append(Vector((0.0, 0.0, z)))
        else:
            rings.append([(r * math.cos(TAU * i / sides), r * math.sin(TAU * i / sides), z) for i in range(sides)])
    return ring_loft(rings)


def sphere_profile(r, zc, n=8):
    return [(r * math.sin(math.pi * i / n), zc - r * math.cos(math.pi * i / n)) for i in range(n + 1)]


def ellipsoid(centre, radii, sides=14, rings=8):
    """A unit sphere stretched to `radii` at `centre`; exact poles top and
    bottom, so a paw's lowest point is exactly its centre less its height."""
    bm = lathe(sphere_profile(1.0, 0.0, rings), sides)
    return move(bm, Matrix.Translation(centre) @ Matrix.Diagonal((*radii, 1.0)))


def catmull(stations, per):
    """A Catmull-Rom curve through tuples of numbers (any length: a point and
    its radii), `per` samples a span, both ends included."""
    pts = [tuple(s) for s in stations]
    ext = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for k in range(per):
            t = k / per
            out.append(tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                    + (3 * b - a - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(pts[-1])
    return out


def _spow(v, e):
    return math.copysign(abs(v) ** e, v)


def profile_loft(stations, sides, per=2, power=2.2, cap_rings=3):
    """A rounded form drawn as a side profile and a plan width: stations of
    (y, top, bottom, half width) from the back (+Y) to the front (-Y), a smooth
    curve through them, each ring a vertical superellipse (`power` 2 is an
    ellipse; a little over 2 fills it out, the chunky look), and a round cap
    of `cap_rings` at each end, as deep as the end's smaller radius."""
    samples = catmull(stations, per)

    def ring(y, top, bot, hw, scale=1.0):
        zc, hz = (top + bot) / 2, (top - bot) / 2 * scale
        e = 2.0 / power
        return [(hw * scale * _spow(math.cos(TAU * i / sides), e), y,
                 zc + hz * _spow(math.sin(TAU * i / sides), e)) for i in range(sides)]

    def cap(sample, direction):
        """Pole first, then rings growing back to the end station."""
        y, top, bot, hw = sample
        depth = 0.92 * min(hw, (top - bot) / 2)
        out = [Vector((0.0, y + direction * depth, (top + bot) / 2))]
        for k in range(cap_rings - 1, 0, -1):
            phi = (math.pi / 2) * k / cap_rings
            out.append(ring(y + direction * depth * math.sin(phi), top, bot, hw, math.cos(phi)))
        return out

    rings = cap(samples[0], +1.0)
    rings += [ring(*s) for s in samples]
    rings += list(reversed(cap(samples[-1], -1.0)))
    return ring_loft(rings)


def sausage(points, radii, sides=12, start="round", end="round", aspect=(1.0, 1.0), cap_rings=3):
    """A round tube along a polyline with a radius at each point, its frame
    carried along so it never twists; each end a hemisphere ("round"), a flat
    disc ("flat") or left open. `aspect` scales the ring's vertical and
    sideways axes, for a flattened jaw."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        t = pts[1] - pts[0] if i == 0 else pts[-1] - pts[-2] if i == n - 1 else pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    frames = []
    for i in range(n):
        if i > 0:
            nrm = tangents[i - 1].rotation_difference(tangents[i]) @ nrm
            nrm = (nrm - tangents[i] * nrm.dot(tangents[i])).normalized()
        frames.append((nrm.copy(), tangents[i].cross(nrm).normalized()))

    def ring(centre, r, frame):
        u, v = frame
        return [centre + r * (aspect[0] * math.cos(TAU * k / sides) * u + aspect[1] * math.sin(TAU * k / sides) * v)
                for k in range(sides)]

    def cap(centre, r, frame, direction, outward):
        """Hemisphere rings from the end ring out to a pole along `direction`."""
        out = []
        for k in range(1, cap_rings):
            phi = (math.pi / 2) * k / cap_rings
            out.append(ring(centre + direction * (r * math.sin(phi)), r * math.cos(phi), frame))
        out.append(centre + direction * r)
        return out if outward else list(reversed(out))

    rings = []
    if start == "round":
        rings += cap(pts[0], radii[0], frames[0], -tangents[0], False)
    elif start == "flat":
        rings.append(pts[0].copy())
    for i in range(n):
        rings.append(ring(pts[i], radii[i], frames[i]))
    if end == "round":
        rings += cap(pts[-1], radii[-1], frames[-1], tangents[-1], True)
    elif end == "flat":
        rings.append(pts[-1].copy())
    return ring_loft(rings)


def join(bms):
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


def copy_bm(bm):
    me = bpy.data.meshes.new("_copy")
    bm.to_mesh(me)
    out = bmesh.new()
    out.from_mesh(me)
    bpy.data.meshes.remove(me)
    return out


def cast(bm, origin, toward):
    """Where a ray from `origin` toward `toward` first meets the shell."""
    tree = BVHTree.FromBMesh(bm)
    origin, toward = Vector(origin), Vector(toward)
    hit = tree.ray_cast(origin, (toward - origin).normalized())[0]
    if hit is None:
        raise SystemExit(f"wildlife_town: a ray from {tuple(origin)} toward {tuple(toward)} missed the head")
    return hit


def prism(poly, z0, z1):
    """A plan polygon of (x, y) extruded from z0 to z1, capped (the render
    rig's ground slab and scale box; nothing of the animals)."""
    bm = ring_loft([[(x, y, z0) for x, y in poly], [(x, y, z1) for x, y in poly]])
    low = [v for v in bm.verts if v.co.z < (z0 + z1) / 2]
    bm.faces.new(list(reversed(low)))
    bm.faces.new([v for v in bm.verts if v.co.z >= (z0 + z1) / 2])
    return bm


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


# --- the rig: pivots and parts --------------------------------------------------

class Rig:
    """The animal's objects: a root empty, pivot empties at the joints and
    the mesh parts under them. Geometry is built in the animal's coordinates,
    shifted by `shift` (which centres the plan on the origin) and moved into
    its pivot's frame, so every object's own transform is clean (location
    zero under its parent, no rotation, unit scale: Check wants scale
    applied) and rotating a pivot swings its part about the joint."""

    def __init__(self, name, pivot_size, shift=Vector((0.0, 0.0, 0.0))):
        self.world = {}            # pivot name -> world position
        self.pivot_size = pivot_size
        self.shift = Vector(shift)
        self.root = bpy.data.objects.new(name, None)
        self.root.empty_display_type = "PLAIN_AXES"
        self.root.empty_display_size = pivot_size * 3
        export().objects.link(self.root)
        self.world[name] = Vector((0.0, 0.0, 0.0))
        self.parents = {name: self.root}

    def pivot(self, name, at, parent=None):
        parent_obj = self.parents[parent] if parent else self.root
        parent_at = self.world[parent] if parent else Vector((0.0, 0.0, 0.0))
        o = bpy.data.objects.new(name, None)
        o.empty_display_type = "SPHERE"
        o.empty_display_size = self.pivot_size
        o.parent = parent_obj
        o.location = Vector(at) + self.shift - parent_at
        export().objects.link(o)
        self.world[name] = Vector(at) + self.shift
        self.parents[name] = o
        return o

    def part(self, name, bm, mat, pivot=None, unwrap=None):
        """A mesh part under `pivot` (or the root), its vertices moved from
        the animal's coordinates into the pivot's frame."""
        parent = self.parents[pivot] if pivot else self.root
        at = self.world[pivot] if pivot else Vector((0.0, 0.0, 0.0))
        move(bm, Matrix.Translation(self.shift - at))
        mesh = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        obj.parent = parent
        obj.location = (0.0, 0.0, 0.0)
        export().objects.link(obj)
        obj.data.materials.append(mat)
        clean(obj)
        smooth_all(obj)
        if unwrap:
            obj["kyt_unwrap"] = unwrap
        obj["kyt_collision"] = "none"      # ambient wildlife never blocks the player
        return obj


# --- the quadruped kit ------------------------------------------------------------
#
# Each species is one dict of proportions in metres, head toward -Y, feet on
# z = 0, before the plan is centred. `body` and `head` are profile stations
# (y, top, bottom, half width), back to front. `eye` is found by a level ray
# at height `z` aimed at the head's axis at `y`, coming in `yaw` degrees round
# from straight sideways toward the front, and sunk `sink` of its radius into
# the head; `nose` by a level ray from the front at height `z`; an ear's base
# by a ray straight down at (x, y) onto the head (or given outright, `at`, for
# the dog's drop ear, which hangs from the skull's side). A leg's polyline is
# given from its pivot (shoulder or hip) down; the foot's height is the paw's,
# so the paw's lowest point is exactly z = 0. A tail is a curve of
# (x, y, z, radius) points, sampled `per` a span and cut into segments at
# `cuts` (sample indices); a sample is never lower than its radius, so a tail
# that lies on the ground lies on it.

# the detail levels: how many sides and rings each kind of part spends, so the
# mouse and rat stay under 1,200 triangles, the cat and raccoon under 2,500 and
# the dog under 3,000
BIG = dict(sides=16, per=2, head_sides=14, head_per=2, leg_sides=10, tail_sides=10, tail_per=3,
           cap_rings=3, dot_sides=8, dot_rings=4, ear_sides=10, ear_rings=5, paw_rings=5, jaw_sides=8)
SMALL = dict(sides=10, per=2, head_sides=10, head_per=2, leg_sides=6, tail_sides=6, tail_per=2,
             cap_rings=2, dot_sides=6, dot_rings=3, ear_sides=8, ear_rings=4, paw_rings=3, jaw_sides=6)

SPECIES = {
    "raccoon": dict(
        label="PRP-WILD-029", pivot_size=0.02, detail=dict(BIG, leg_sides=8, tail_per=2), power=2.3,
        # arched: rump low, the back rising to 0.32 over the loin, falling to
        # 0.26 at the shoulders and on down the short neck into the low head
        body=[(0.205, 0.255, 0.135, 0.072), (0.15, 0.305, 0.105, 0.1), (0.05, 0.32, 0.095, 0.11),
              (-0.05, 0.295, 0.095, 0.106), (-0.13, 0.262, 0.105, 0.098), (-0.18, 0.24, 0.12, 0.078),
              (-0.21, 0.225, 0.135, 0.062)],
        head_pivot=(0, -0.20, 0.18),
        # a broad face with cheek ruffs, narrowing hard to a short pointed muzzle
        head=[(-0.19, 0.232, 0.142, 0.05), (-0.215, 0.252, 0.128, 0.068), (-0.245, 0.243, 0.126, 0.075),
              (-0.272, 0.214, 0.134, 0.042), (-0.30, 0.192, 0.141, 0.025), (-0.318, 0.182, 0.146, 0.017)],
        nose=dict(z=0.170, r=0.012),
        eye=dict(y=-0.25, z=0.214, yaw=32, r=0.0095, sink=0.45),
        jaw_pivot=(0, -0.255, 0.142),
        jaw=dict(points=[(0, -0.262, 0.142), (0, -0.305, 0.144)], radii=[0.02, 0.012], aspect=(0.55, 1.0)),
        ear=dict(kind="blunt", x=0.038, y=-0.218, w=0.044, depth=0.013, h=0.045, sink=0.012,
                 splay=22, lean=8, turn=15),
        legs=dict(
            front=dict(pivot=(0.058, -0.125, 0.16), points=[(0, 0, 0), (0, 0.01, -0.075), (0, -0.005, -0.13)],
                       foot=(0, -0.01), radii=[0.042, 0.03, 0.022, 0.021], paw=(0.026, 0.034, 0.016), paw_fwd=0.012),
            hind=dict(pivot=(0.062, 0.135, 0.20), points=[(0, 0, 0), (0, -0.035, -0.09), (0, 0.035, -0.15)],
                      foot=(0, 0.03), radii=[0.058, 0.036, 0.024, 0.022], paw=(0.026, 0.052, 0.016), paw_fwd=0.022)),
        # the bushy tail, fullest a third of the way along, hangs in a curve
        tail=dict(points=[(0, 0.195, 0.255, 0.036), (0, 0.255, 0.235, 0.05), (0, 0.32, 0.19, 0.055),
                          (0, 0.365, 0.13, 0.048), (0, 0.39, 0.085, 0.032)], cuts=[6]),
    ),
    "cat": dict(
        label="PRP-WILD-030", pivot_size=0.015, detail=dict(BIG, sides=14, leg_sides=8, tail_sides=8, tail_per=2),
        power=2.2,
        # a long level back at 0.25, a slight rise at the hips, a short thick
        # neck carrying the head a little above the back
        body=[(0.165, 0.226, 0.142, 0.054), (0.125, 0.256, 0.122, 0.069), (0.04, 0.252, 0.114, 0.071),
              (-0.05, 0.248, 0.114, 0.069), (-0.115, 0.253, 0.122, 0.064), (-0.16, 0.274, 0.148, 0.054),
              (-0.195, 0.3, 0.188, 0.046), (-0.218, 0.312, 0.216, 0.04)],
        head_pivot=(0, -0.205, 0.264),
        # a round skull, full cheeks low on the face, a short blunt muzzle
        head=[(-0.195, 0.322, 0.246, 0.036), (-0.22, 0.342, 0.234, 0.051), (-0.25, 0.34, 0.231, 0.053),
              (-0.276, 0.319, 0.236, 0.04), (-0.294, 0.295, 0.245, 0.025), (-0.303, 0.285, 0.25, 0.018)],
        nose=dict(z=0.286, r=0.0078),
        eye=dict(y=-0.262, z=0.306, yaw=30, r=0.0115, sink=0.45),
        jaw_pivot=(0, -0.258, 0.249),
        jaw=dict(points=[(0, -0.264, 0.246), (0, -0.293, 0.249)], radii=[0.017, 0.012], aspect=(0.55, 1.0)),
        ear=dict(kind="point", x=0.029, y=-0.226, w=0.045, depth=0.011, h=0.048, sink=0.012,
                 splay=24, lean=6, turn=12),
        legs=dict(
            front=dict(pivot=(0.04, -0.115, 0.18), points=[(0, 0, 0), (0, 0.005, -0.085), (0, -0.004, -0.15)],
                       foot=(0, -0.008), radii=[0.035, 0.025, 0.02, 0.02], paw=(0.023, 0.028, 0.017), paw_fwd=0.008),
            hind=dict(pivot=(0.044, 0.115, 0.178), points=[(0, 0, 0), (0, -0.042, -0.058), (0, 0.035, -0.128)],
                      foot=(0, 0.022), radii=[0.042, 0.029, 0.021, 0.02], paw=(0.023, 0.031, 0.017), paw_fwd=0.01)),
        # up from the rump, a long straight rise, then the hook forward
        tail=dict(points=[(0, 0.16, 0.222, 0.0175), (0, 0.19, 0.27, 0.017), (0, 0.207, 0.34, 0.0165),
                          (0, 0.207, 0.41, 0.0155), (0, 0.19, 0.46, 0.0145), (0, 0.165, 0.478, 0.0135),
                          (0, 0.145, 0.472, 0.0125)], cuts=[4, 8]),
    ),
    "mouse": dict(
        label="PRP-WILD-031", pivot_size=0.004, detail=SMALL, power=2.1,
        # compact and pear-shaped: the haunch the highest and widest point
        body=[(0.03, 0.025, 0.009, 0.012), (0.02, 0.035, 0.006, 0.0175), (0.006, 0.034, 0.006, 0.0165),
              (-0.008, 0.029, 0.008, 0.0135), (-0.018, 0.025, 0.010, 0.010)],
        head_pivot=(0, -0.015, 0.018),
        # a cone from the ears to a pointed snout
        head=[(-0.012, 0.027, 0.010, 0.0095), (-0.02, 0.0285, 0.0085, 0.0115), (-0.03, 0.0235, 0.0085, 0.0082),
              (-0.039, 0.0178, 0.0088, 0.0046), (-0.044, 0.015, 0.0092, 0.0028)],
        nose=dict(z=0.0118, r=0.0022),
        eye=dict(y=-0.025, z=0.021, yaw=25, r=0.0032, sink=0.35),
        jaw_pivot=(0, -0.026, 0.0095),
        jaw=dict(points=[(0, -0.029, 0.0095), (0, -0.04, 0.0098)], radii=[0.0042, 0.0026], aspect=(0.55, 1.0)),
        # big round ears, about two thirds the head's height
        ear=dict(kind="round", x=0.0068, y=-0.0165, w=0.0135, depth=0.0022, h=0.0145, sink=0.003,
                 splay=30, lean=12, turn=22),
        legs=dict(
            front=dict(pivot=(0.0085, -0.007, 0.011), points=[(0, 0, 0), (0, -0.002, -0.006)],
                       foot=(0, -0.002), radii=[0.0045, 0.0029, 0.0024], paw=(0.0028, 0.0042, 0.0018), paw_fwd=0.0018),
            hind=dict(pivot=(0.0115, 0.018, 0.013), points=[(0, 0, 0), (0, -0.005, -0.0055)],
                      foot=(0, -0.004), radii=[0.0075, 0.0042, 0.0026], paw=(0.0032, 0.0075, 0.0018), paw_fwd=0.004)),
        # a thin tail, as long as the body, down to the ground and trailing in a lazy S
        tail=dict(points=[(0, 0.03, 0.013, 0.0019), (0, 0.045, 0.0055, 0.0017), (0.003, 0.068, 0.002, 0.0015),
                          (0.001, 0.092, 0.002, 0.0013), (-0.004, 0.115, 0.002, 0.001)], cuts=[4]),
    ),
    "rat": dict(
        label="PRP-WILD-032", pivot_size=0.008, detail=SMALL, power=2.2,
        # long and heavy, humped over the haunch, the shoulders lower
        body=[(0.085, 0.062, 0.024, 0.034), (0.06, 0.085, 0.014, 0.046), (0.015, 0.087, 0.013, 0.048),
              (-0.03, 0.076, 0.017, 0.041), (-0.058, 0.066, 0.024, 0.031), (-0.072, 0.06, 0.03, 0.025)],
        head_pivot=(0, -0.06, 0.045),
        # a longer head than the mouse's, the snout blunt
        head=[(-0.05, 0.067, 0.029, 0.025), (-0.068, 0.071, 0.026, 0.03), (-0.09, 0.064, 0.025, 0.025),
              (-0.108, 0.055, 0.026, 0.019), (-0.121, 0.049, 0.028, 0.015)],
        nose=dict(z=0.0405, r=0.0052),
        eye=dict(y=-0.083, z=0.058, yaw=40, r=0.0045, sink=0.45),
        jaw_pivot=(0, -0.083, 0.03),
        jaw=dict(points=[(0, -0.088, 0.029), (0, -0.117, 0.03)], radii=[0.011, 0.0075], aspect=(0.55, 1.0)),
        # small ears, about two fifths of the head's height
        ear=dict(kind="round", x=0.018, y=-0.062, w=0.0175, depth=0.0045, h=0.018, sink=0.004,
                 splay=35, lean=15, turn=20),
        legs=dict(
            front=dict(pivot=(0.024, -0.035, 0.033), points=[(0, 0, 0), (0, -0.004, -0.02)],
                       foot=(0, -0.004), radii=[0.012, 0.008, 0.006], paw=(0.0072, 0.01, 0.005), paw_fwd=0.004),
            hind=dict(pivot=(0.032, 0.058, 0.04), points=[(0, 0, 0), (0, -0.016, -0.018)],
                      foot=(0, 0.004), radii=[0.021, 0.011, 0.0065], paw=(0.0085, 0.02, 0.005), paw_fwd=0.009)),
        # a thick tail, tapering, shorter than the body, along the ground
        tail=dict(points=[(0, 0.088, 0.035, 0.0078), (0, 0.112, 0.016, 0.0068), (0.004, 0.15, 0.0075, 0.0057),
                          (0.007, 0.2, 0.006, 0.0046), (0.0, 0.25, 0.0045, 0.0035), (-0.008, 0.285, 0.0035, 0.0025)],
                  cuts=[4]),
    ),
    "dog": dict(
        label="PRP-WILD-033", pivot_size=0.04, detail=dict(BIG, sides=16, head_sides=14), power=2.25,
        # withers at 0.55, a deep chest to 0.28, the tuck-up at the loin, the
        # neck rising from the withers to the head
        body=[(0.28, 0.52, 0.385, 0.088), (0.21, 0.548, 0.35, 0.11), (0.10, 0.536, 0.36, 0.113),
              (-0.02, 0.535, 0.318, 0.12), (-0.12, 0.547, 0.28, 0.128), (-0.22, 0.57, 0.3, 0.12),
              (-0.285, 0.632, 0.385, 0.106), (-0.325, 0.677, 0.475, 0.093), (-0.36, 0.712, 0.565, 0.08)],
        head_pivot=(0, -0.36, 0.65),
        # the skull, a stop, a medium muzzle
        head=[(-0.345, 0.738, 0.608, 0.058), (-0.395, 0.775, 0.592, 0.078), (-0.45, 0.768, 0.592, 0.075),
              (-0.485, 0.72, 0.597, 0.053), (-0.545, 0.702, 0.603, 0.045), (-0.585, 0.693, 0.613, 0.039)],
        nose=dict(z=0.68, r=0.021),
        eye=dict(y=-0.452, z=0.724, yaw=30, r=0.0135, sink=0.45),
        jaw_pivot=(0, -0.44, 0.62),
        jaw=dict(points=[(0, -0.455, 0.616), (0, -0.565, 0.607)], radii=[0.031, 0.026], aspect=(0.55, 1.0)),
        # drop ears: a pad from the top corner of the skull hanging down its side
        ear=dict(kind="flop", at=(0.067, -0.40, 0.753), w=0.075, depth=0.02, h=0.125, sink=0.022,
                 splay=28, lean=-12, turn=0),
        legs=dict(
            front=dict(pivot=(0.078, -0.165, 0.44), points=[(0, 0, 0), (0, 0.01, -0.15), (0, -0.005, -0.33)],
                       foot=(0, -0.015), radii=[0.062, 0.047, 0.038, 0.036], paw=(0.047, 0.058, 0.032), paw_fwd=0.016),
            hind=dict(pivot=(0.078, 0.195, 0.43), points=[(0, 0, 0), (0, -0.06, -0.14), (0, 0.055, -0.31)],
                      foot=(0, 0.045), radii=[0.076, 0.053, 0.038, 0.036], paw=(0.047, 0.059, 0.032), paw_fwd=0.016)),
        # hanging relaxed from the croup, out and down
        tail=dict(points=[(0, 0.275, 0.50, 0.034), (0, 0.345, 0.468, 0.03), (0, 0.395, 0.39, 0.026),
                          (0, 0.413, 0.305, 0.022), (0, 0.407, 0.235, 0.018)], cuts=[6]),
    ),
}


def ear_bm(spec, side, base):
    """One ear on its base point, `side` +1 the animal's own left (+X: it faces
    -Y) or -1 its right. Built upright
    at the origin (or hanging, the dog's), turned outward about Z, splayed
    about Y, leaned about X, then put on its base. "round" is a flattened egg
    facing forward (mouse, rat); "point" a cat's cone, thinned front to back;
    "blunt" a rounder cone (raccoon); "flop" a flat pad hanging down beside
    the head (dog), its top in the skull."""
    e = spec["ear"]
    d = spec["detail"]
    w, depth, h = e["w"], e["depth"], e["h"]
    es, er = d["ear_sides"], d["ear_rings"]
    if e["kind"] == "round":
        bm = ellipsoid((0, 0, h / 2), (w / 2, depth / 2, h / 2), es, er)
        splay = side * e["splay"]
    elif e["kind"] in ("point", "blunt"):
        shape = ((1.0, 0.0), (0.96, 0.22), (0.66, 0.58), (0.28, 0.88)) if e["kind"] == "point" else \
                ((1.0, 0.0), (0.97, 0.3), (0.8, 0.62), (0.45, 0.88))
        prof = [(0.0, 0.0)] + [(w / 2 * f, t * h) for f, t in shape] + [(0.0, h)]
        bm = move(lathe(prof, es), Matrix.Diagonal((1.0, depth / w, 1.0, 1.0)))
        splay = side * e["splay"]
    else:   # flop: hangs from its top, so the splay that swings it out is the other way
        bm = ellipsoid((0, 0, -h / 2 + e["sink"]), (depth / 2, w / 2, h / 2), es, er)
        splay = -side * e["splay"]
    rot = (Matrix.Rotation(math.radians(splay), 4, "Y") @ Matrix.Rotation(math.radians(-e["lean"]), 4, "X")
           @ Matrix.Rotation(math.radians(-side * e["turn"]), 4, "Z"))
    return move(bm, Matrix.Translation(base) @ rot)


def leg_bm(leg, side, sides, detail):
    """One leg from its pivot down, a tapering tube along the hip-knee-hock
    (or shoulder-elbow-wrist) line, flat at the foot, with the paw egg joined
    on so the paw's lowest point is exactly z = 0. The top is round and hidden
    in the body, so a swung leg still shows a rounded shoulder."""
    px, py, pz = leg["pivot"]
    paw_rx, paw_ry, paw_rz = leg["paw"]
    pts = [Vector((side * (px + dx), py + dy, pz + dz)) for dx, dy, dz in leg["points"]]
    fx, fy = leg["foot"]
    foot = Vector((side * (px + fx), py + fy, paw_rz))      # the foot's height comes from the paw
    pts.append(foot)
    leg_mesh = sausage(pts, leg["radii"], sides, start="round", end="flat", cap_rings=detail["cap_rings"])
    paw = ellipsoid((foot.x, foot.y - leg["paw_fwd"], paw_rz), (paw_rx, paw_ry, paw_rz), sides, detail["paw_rings"])
    return join([leg_mesh, paw])


def tail_samples(spec):
    """The tail's curve sampled, each sample (point, radius), never lower
    than its own radius (a tail on the ground lies on it)."""
    out = []
    for x, y, z, r in catmull(spec["tail"]["points"], spec["detail"]["tail_per"]):
        out.append((Vector((x, y, max(z, r * 1.08 + 0.0004))), r))
    return out


def build_animal(name, shift=Vector((0.0, 0.0, 0.0))):
    spec = SPECIES[name]
    d = spec["detail"]
    fur = material(f"{name}_fur", FUR[name])
    dark = material(f"{name}_dark", DARK)
    skin = material(f"{name}_skin", SKIN) if name in ("mouse", "rat") else fur
    rig = Rig(name, spec["pivot_size"], shift)
    caps = d["cap_rings"]

    # the body and neck, one shell
    rig.part("body", profile_loft(spec["body"], d["sides"], d["per"], spec["power"], caps), fur)

    # the head: skull and muzzle one shell, under the pivot where the neck meets it
    rig.pivot("head_pivot", spec["head_pivot"])
    head = profile_loft(spec["head"], d["head_sides"], d["head_per"], spec["power"], caps)
    probe = copy_bm(head)                      # the head as built, to seat things on
    rig.part("head", head, fur, "head_pivot")

    n = spec["nose"]
    tip = cast(probe, (0.0, -10.0, n["z"]), (0.0, 0.0, n["z"]))
    rig.part("nose", ellipsoid(tip + Vector((0.0, n["r"] * 0.45, 0.0)), (n["r"],) * 3, d["dot_sides"], d["dot_rings"]),
             dark, "head_pivot", unwrap="lathe")
    e = spec["eye"]
    for side, tag in ((1, "left"), (-1, "right")):
        yaw = math.radians(e["yaw"])
        aim = Vector((0.0, e["y"], e["z"]))
        start = aim + Vector((side * math.cos(yaw), -math.sin(yaw), 0.0))
        hit = cast(probe, start, aim)
        centre = hit + (aim - start).normalized() * (e["r"] * e["sink"])
        rig.part(f"eye_{tag}", ellipsoid(centre, (e["r"],) * 3, d["dot_sides"], d["dot_rings"]), dark,
                 "head_pivot", unwrap="lathe")

    # the lower jaw, a flattened tube under the muzzle, hinged under the skull
    rig.pivot("jaw_pivot", spec["jaw_pivot"], "head_pivot")
    j = spec["jaw"]
    rig.part("jaw", sausage(j["points"], j["radii"], d["jaw_sides"], aspect=j["aspect"], cap_rings=caps), fur,
             "jaw_pivot")

    # the ears, each on a pivot at its base
    ear = spec["ear"]
    for side, tag in ((1, "left"), (-1, "right")):
        if "at" in ear:
            ax, ay, az = ear["at"]
            base = Vector((side * ax, ay, az))
        else:
            top = cast(probe, (side * ear["x"], ear["y"], 10.0), (side * ear["x"], ear["y"], 0.0))
            base = top - Vector((0.0, 0.0, ear["sink"]))
        rig.pivot(f"ear_{tag}_pivot", base, "head_pivot")
        rig.part(f"ear_{tag}", ear_bm(spec, side, base), skin, f"ear_{tag}_pivot")
    probe.free()

    # four legs, each with its paw, on a pivot at the shoulder or hip
    for end in ("front", "hind"):
        leg = spec["legs"][end]
        px, py, pz = leg["pivot"]
        for side, tag in ((1, "left"), (-1, "right")):
            rig.pivot(f"leg_{end}_{tag}_pivot", (side * px, py, pz))
            rig.part(f"leg_{end}_{tag}", leg_bm(leg, side, d["leg_sides"], d), fur, f"leg_{end}_{tag}_pivot")

    # the tail: one curve cut into segments nested down from the root; a
    # segment starts a little thinner than the last ended so the two round
    # ends nest at the joint rather than sharing a surface
    samples = tail_samples(spec)
    cuts = [0] + spec["tail"]["cuts"] + [len(samples) - 1]
    names = ["base", "tip"] if len(cuts) == 3 else ["base", "mid", "tip"]
    parent, prev_r = None, None
    for (a, b), tag in zip(zip(cuts, cuts[1:]), names):
        seg = samples[a:b + 1]
        pivot = "tail_pivot" if tag == "base" else f"tail_{tag}_pivot"
        rig.pivot(pivot, seg[0][0], parent)
        radii = [r for _, r in seg]
        if prev_r is not None:
            radii[0] = min(radii[0], prev_r * 0.96)
        rig.part(f"tail_{tag}", sausage([p for p, _ in seg], radii, d["tail_sides"], cap_rings=caps), skin, pivot)
        prev_r = radii[-1]
        parent = pivot
    return rig


def clear_export():
    coll = export()
    for o in list(coll.all_objects):
        bpy.data.objects.remove(o)
    for child in list(coll.children):
        bpy.data.collections.remove(child)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)


def build_centred(name):
    """Build once to measure, then again shifted so the plan's bounding box is
    centred on the origin (the feet stay on z = 0)."""
    build_animal(name)
    bpy.context.view_layer.update()
    lo, hi = bounds([o for o in export().all_objects if o.type == "MESH"])
    clear_export()
    build_animal(name, Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, 0.0)))
    bpy.context.view_layer.update()


def checks(name):
    """Measurements worth reading back against the real animal."""
    spec = SPECIES[name]
    parts = [o for o in export().all_objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    shift_y = bpy.data.objects["head_pivot"].matrix_world.translation.y - spec["head_pivot"][1]
    body = bpy.data.objects["body"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    front_y = spec["legs"]["front"]["pivot"][1] + shift_y
    band = 0.025 * (hi.y - lo.y)
    shoulder = max((body.matrix_world @ v.co).z for v in me.vertices if abs((body.matrix_world @ v.co).y - front_y) < band)
    ev.to_mesh_clear()
    blo, bhi = bounds([body])
    hlo, hhi = bounds([bpy.data.objects["head"]])
    nlo, _ = bounds([bpy.data.objects["nose"]])
    samples = tail_samples(spec)
    tail_len = sum((b[0] - a[0]).length for a, b in zip(samples, samples[1:]))
    head_h = hhi.z - hlo.z
    ear_h = spec["ear"]["h"]
    return [f"shoulder {shoulder:.3f} m (the back over the front legs), body and neck's highest {bhi.z:.3f} m, "
            f"highest point {hi.z:.3f} m (ears or tail included)",
            f"head and body {bhi.y - nlo.y:.3f} m nose to rump, tail {tail_len:.3f} m, overall {hi.y - lo.y:.3f} m long, "
            f"{hi.x - lo.x:.3f} m wide",
            f"head {hhi.y - hlo.y:.3f} long, {hhi.x - hlo.x:.3f} wide, {head_h:.3f} high; ear {ear_h * 1000:.1f} mm "
            f"({ear_h / head_h:.2f} of the head's height); tail root radius {samples[0][1] * 1000:.1f} mm, "
            f"tip {samples[-1][1] * 1000:.1f} mm",
            f"lowest point z {lo.z:.4f} (the paws), plan centre ({(lo.x + hi.x) / 2:+.4f}, {(lo.y + hi.y) / 2:+.4f})"]


# --- the render rig ------------------------------------------------------------------

def stage_setup(scene):
    """A sky, a sun, a ground and a camera in a `_review` collection that is
    never saved (the render runs after the save)."""
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
    try:
        scene.eevee.taa_render_samples = 24
    except AttributeError:
        pass
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.72, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)

    def stage_mesh(tag, bm, colour):
        mesh = bpy.data.meshes.new(tag)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        o = bpy.data.objects.new(tag, mesh)
        o.data.materials.append(material(f"render_{tag}", colour))
        stage.objects.link(o)
        return o

    stage_mesh("ground", prism([(-40, -40), (40, -40), (40, 40), (-40, 40)], -0.02, -0.0003), (0.30, 0.29, 0.27, 1))
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.2
    sun.rotation_euler = (math.radians(48), math.radians(10), math.radians(35))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    cam.data.clip_start = 0.002
    stage.objects.link(cam)
    scene.camera = cam
    return stage, stage_mesh, cam


def points_of(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def shoot(scene, cam, path, objs, direction, target=None, lens=40, frame=None, floor=None, ortho=False):
    """The camera along `direction` from the objects' centre, backed off until
    every vertex of `frame` (or the objects) is in the picture; it never drops
    below `floor` (a tenth of the subject's size unless given). `ortho` shoots
    without perspective, so things side by side show at true relative size
    however near the camera each stands (the scale box, the lineup)."""
    pts = points_of(frame or objs)
    lo = Vector(map(min, *pts))
    hi = Vector(map(max, *pts))
    centre = (lo + hi) / 2 if target is None else Vector(target)
    d = Vector(direction).normalized()
    size = (hi - lo).length
    dist = max(size * (3.0 if ortho else 0.6), 0.02)
    floor = size * 0.1 if floor is None else floor
    cam.data.type = "ORTHO" if ortho else "PERSP"
    cam.data.ortho_scale = size * 0.4
    cam.data.clip_end = max(100.0, size * 10)
    cam.data.lens = lens
    for _ in range(160):
        cam.location = centre + d * dist
        cam.location.z = max(cam.location.z, floor)
        look = centre - cam.location
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if all(0.04 <= c.x <= 0.96 and 0.04 <= c.y <= 0.96 for c in (world_to_camera_view(scene, cam, p) for p in pts)):
            break
        if ortho:
            cam.data.ortho_scale *= 1.04
        else:
            dist *= 1.05
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def scale_box_bm(x, y):
    """A 1.7 m tall rounded block, a guest's height, standing at (x, y)."""
    hx, hy, r, per = 0.225, 0.14, 0.03, 3
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0), (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((x + cx + r * math.cos(a), y + cy + r * math.sin(a)))
    return prism(pts, 0.0, 1.7)


def render(folder, name):
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    stage, stage_mesh, cam = stage_setup(scene)
    parts = [o for o in export().all_objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    for tag, d in (("three_quarter", (-0.75, -1.0, 0.5)), ("front", (0.0, -1.0, 0.15)), ("side", (1.0, 0.0, 0.12)),
                   ("top", (0.0, -0.001, 1.0))):
        shoot(scene, cam, os.path.join(folder, f"{name}_{tag}.png"), parts, d, floor=0.15 * (hi.z - lo.z))
    # beside a 1.7 m box, a guest's height
    gap = max(0.12, 0.3 * (hi.y - lo.y))
    box = stage_mesh("scale_box", scale_box_bm(hi.x + gap + 0.225, 0.0), (0.35, 0.35, 0.38, 1))
    shoot(scene, cam, os.path.join(folder, f"{name}_scale.png"), parts + [box], (-0.6, -1.0, 0.35), floor=0.3,
          ortho=True)


def lineup(png):
    """The five saved animals in a row beside the 1.7 m box, at true relative
    size, in a fresh scene that is never saved."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 2400, 1000
    stage, stage_mesh, cam = stage_setup(scene)
    order = ("dog", "raccoon", "cat", "rat", "mouse")
    x = 0.0
    shown = []
    for name in order:
        path = os.path.join(ROOT, "assets", "source", "props", f"{name}.blend")
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.collections = [c for c in src.collections if c == "export"]
        coll = dst.collections[0]
        scene.collection.children.link(coll)
        root = next(o for o in coll.all_objects if o.parent is None and o.type == "EMPTY")
        parts = [o for o in coll.all_objects if o.type == "MESH"]
        bpy.context.view_layer.update()
        lo, hi = bounds(parts)
        root.location.x = x - lo.x
        x += (hi.x - lo.x) + 0.18
        shown += parts
        print(f"lineup: {name} {hi.y - lo.y:.3f} long, {hi.z:.3f} tall, {triangles(parts)} triangles")
    box = stage_mesh("scale_box", scale_box_bm(x + 0.225, 0.0), (0.35, 0.35, 0.38, 1))
    os.makedirs(os.path.dirname(os.path.abspath(png)), exist_ok=True)
    # the animals turned three quarters to the camera so each shows its profile
    # and face; no perspective, so their sizes against the box are true
    shoot(scene, cam, png, shown + [box], (-0.55, -1.0, 0.16), floor=0.2, ortho=True)


# --- the file --------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--lineup" in argv:
        lineup(argv[argv.index("--lineup") + 1])
        return
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in SPECIES:
        raise SystemExit(f"wildlife_town: open one of {', '.join(SPECIES)}, not {name}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"wildlife_town: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        clear_export()
    build_centred(name)
    parts = [o for o in coll.all_objects if o.type == "MESH"]
    pivots = [o for o in coll.all_objects if o.type == "EMPTY" and o.name.endswith("_pivot")]
    lo, hi = bounds(parts)
    print(f"wildlife_town: {name} ({SPECIES[name]['label']}): {len(parts)} parts, {len(pivots)} pivots, "
          f"{triangles(parts)} triangles")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts))
    print("  pivots: " + ", ".join(o.name for o in pivots))
    print(f"  size: {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x D x H), "
          f"x {lo.x:.3f}..{hi.x:.3f}, y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.4f}..{hi.z:.3f}")
    for line in checks(name):
        print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
