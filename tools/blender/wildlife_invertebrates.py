"""Six tide-pool and sea animals, a first model pass (2026-10-03) from
Christina's 2026-09-29 ask for ambient wildlife (`prop-library.md`, Ambient
wildlife, PRP-WILD-013 to 016, 022 and 025). None has a greybox or a
photograph of hers; each is the plainest reading of the real animal in the
house style for her to reshape. Card: `documentation/howto/model-the-tidepool-animals.md`.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<animal>.blend --python tools/blender/wildlife_invertebrates.py -- \\
        [--replace] [--save] [--render <folder>]

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \\
        --python tools/blender/wildlife_invertebrates.py -- --lineup <png> <animal>.blend ...

`<animal>` is `crab` (PRP-WILD-013), `starfish` (014), `sea_urchin` (015),
`scallop` (016), `jellyfish` (022) or `octopus` (025); the file is made first
with `new_prop.py -- <animal>`. The tool builds whichever the file is named
for into `export`, one object a part, in real metres, Z up, lowest point on
z = 0, centred on the origin in plan, head or front toward -Y (+Z in Godot),
so the animal's left is +X. It refuses while `export` holds anything (it may
be hers) unless `--replace`; it writes the file only with `--save`;
`--render` shoots three-quarter, front, side and top views and one beside a
0.30 m ruler into the folder, after the save, so the render's camera, sun,
ground and ruler never reach the file (a file in variants: each variant on
its own, and all of them in a row). `--lineup` runs with no file open: it
appends the `export` collections of the files named, stands every animal and
variant in a row at true relative size with the ruler and renders the row to
the PNG, and the ones under 0.10 m tall closer to `<png>_small.png`;
nothing is saved.

**Moving parts** sit under pivot empties at their joints, named for what
swings there, so motion can be added later without re-modelling: no
armature, no animation, no Godot behaviour here. A part's mesh origin is its
pivot, so rotating the pivot swings the part about its joint. Every part is
`kyt_collision = "none"`: nothing walks on a crab.

**Style.** Cartoony and chunky as the props and plants: few big rounded forms,
no fine realistic detail. Spots, bumps, suckers, the rock crab's black claw
tips, the scallop's eyes and purple hinge, the moon jelly's four rings, the
frills of the jellies' arms and the velella's rings are paint for later. The
urchin's spines are a few fat cones; the jellies' tentacles a few ribbons.

**Crab** (`crab`): Pacific red rock crab (Cancer productus), adult, standing.
Carapace 0.165 wide by 0.112 long by 0.046 m tall, a bun wider than long,
the rear narrowed, held 0.026 m off the rock; two stalked eyes at the front
edge; four walking legs a side, each one bent tapering tube from hip to
ground, under `leg_left_1_pivot` .. `leg_right_4_pivot` (1 is the foremost)
at its hip; two claws held folded in front at body height, each an arm
(`claw_<side>_arm`) and a hand (`claw_<side>_hand`: the palm and its fixed
finger) under `claw_<side>_pivot` at the shoulder, with the movable finger
(`claw_<side>_dactyl`) under `claw_<side>_dactyl_pivot` at the hand's far
end, so the pincers can open. The two claws are the same size (a rock
crab's are).

**Starfish** (`starfish`): ochre sea star (Pisaster ochraceus), five arms,
0.23 m across, lying flat on the rock, one part (`body`): a puffed star, flat
underneath, arms fat at the base and blunt, a little uneven in length, one
arm toward -Y. Nothing moves; the tube feet and the madreporite are paint.

**Sea urchin** (`sea_urchin`): purple sea urchin (Strongylocentrotus
purpuratus), test 0.075 across and 0.046 m tall, 37 fat six-sided spines all
over it (`spines`, one mesh) except the mouth underneath, standing on its
lower spines; two parts (`test`, `spines`), no pivots.

**Scallop** (`scallop`): rock scallop (Crassadoma gigantea, the purple-hinge
rock scallop), 0.14 m across, the lower valve cemented to the rock, shell
slightly open. Each valve is a lumpy dome over a slightly irregular round fan
(ten broad ribs as a wave in the rim and low ridges), closed underneath by a
flat face that stands for the orange mantle seen in the gap; small ears at the
hinge (+Y), the opening toward -Y. The lower valve (`valve_lower`) is a
shallow tray on the rock; the upper (`valve_upper`) hangs under
`valve_pivot` on the hinge line, modelled closed and opened 12 degrees by the
pivot's rotation, so closing it is turning the pivot back. A small ligament
block (`hinge`) sits between the ears.

**Jellyfish** (`jellyfish`), four `kyt_variant`s standing at the origin
together, each in its own collection under `export` and its parts named for
it, each with its own lowest point on z = 0:

- `moon`, the moon jelly (Aurelia labiata, the Pacific one; the lagoon plan
  names moon jellies): a broad shallow bell 0.25 m across and 0.06 tall with
  eight soft lobes at the rim, a short fringe (`moon_fringe`, one skirt whose
  strands are cut-out for later) and four short frilly oral arms. The bell,
  its mouth stalk and the fringe hang from `moon_bell_pivot` at the bell's
  axis on its rim plane; each arm under `moon_arm_<n>_pivot` at the stalk's
  foot.
- `sea_nettle`, the Pacific sea nettle (Chrysaora fuscescens): a taller bell
  0.24 m across and 0.145 tall with eight lobes, four long spiralling oral
  arms (0.65 m) and eight trailing tentacles (0.85 m) from the clefts of the
  rim, as `moon` with `sea_nettle_tentacle_<n>_pivot` at the rim. Real
  nettle tentacles trail metres; these read.
- `velella`, the by-the-wind sailor (Velella velella), floating: a flat oval
  float 0.07 m long, a stiff triangular sail standing diagonally across it
  and a short fringe of tentacles under the rim. `velella_float_pivot` at the
  float's centre carries the float and fringe and `velella_sail_pivot` at
  the sail's foot. `waterline_velella` in `reference` marks the water
  surface.
- `velella_stranded`, the same animal washed up on the sand: the float lying
  tipped a little, the sail bent over toward the sand, the fringe flattened.
  These are the blue strandings on California beaches; a mass stranding is
  many copies placed, not one mesh.

The swimmers (`moon`, `sea_nettle`) are built as they swim, bell up,
trailing down; the placement scene puts them in the water at whatever depth
and heading it wants. A jellyfish has no front; -Y is nominal.

**Octopus** (`octopus`): California two-spot octopus (Octopus bimaculoides),
resting on the rock with its arms spread, about 0.65 m across. Mantle a bulb
lying back at 15 degrees behind the head (`mantle`), head a flattened egg
(`head`) with two bulging eyes on top (`eye_left`, `eye_right`: a skin bump
and a dark pupil each), the siphon a short funnel on its right (`siphon`),
and eight arms as tapering tubes under `arm_<side>_<n>_pivot` where each
leaves the crown under the head, numbered as zoologists do, 1 the front pair
to 4 the back pair (`arm_left_1` is front-left), each reaching out, lying
along the rock and curling at its tip. Eyes toward -Y. The blue rings under
the eyes are paint.

Materials are flat stand-ins, two or three per animal, for the painting to
replace. Revolved parts carry `kyt_unwrap = "lathe"` for `unwrap_parts.py`;
the tubes and lofts are left to its own shape rules.
"""

import math
import os
import random
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

TAU = math.tau
ANIMALS = ("crab", "starfish", "sea_urchin", "scallop", "jellyfish", "octopus")
RULER = 0.30          # the scale bar in every render, metres
RULER_STEP = 0.05
BUDGETS = {"crab": 1500, "starfish": 800, "sea_urchin": 800, "scallop": 800, "octopus": 2500,
           "moon": 1200, "sea_nettle": 1200, "velella": 300, "velella_stranded": 300}


# --- building blocks -------------------------------------------------------

# Where parts go while a builder runs: the export collection, or a variant's
# own collection under it with the variant's name on every part.
_ctx = {"coll": None, "variant": None}
_waterlines = {}       # variant -> (float part, fraction of its height the water reaches)


def material(name, colour):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = 0.75
    mat.diffuse_color = colour
    return mat


def export():
    return bpy.data.collections["export"]


def home():
    return _ctx["coll"] or export()


def named(name):
    return f"{_ctx['variant']}_{name}" if _ctx["variant"] else name


def begin_variant(tag):
    coll = bpy.data.collections.new(tag)
    export().children.link(coll)
    _ctx.update(coll=coll, variant=tag)


def end_variant():
    _ctx.update(coll=None, variant=None)


def world_loc(obj):
    """An object's world position while the tree is still unrotated (every
    pivot is placed before any is turned)."""
    loc = Vector((0.0, 0.0, 0.0))
    while obj is not None:
        loc += Vector(obj.location)
        obj = obj.parent
    return loc


def pivot(name, location, parent=None):
    """An empty at a joint, placed in world coordinates, under `parent`."""
    e = bpy.data.objects.new(named(name), None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.02
    home().objects.link(e)
    if parent is not None:
        e.parent = parent
        e.location = Vector(location) - world_loc(parent)
    else:
        e.location = Vector(location)
    if _ctx["variant"]:
        e["kyt_variant"] = _ctx["variant"]
    return e


def part(name, bm, mats, *, parent=None, origin=None, smooth_deg=70.0, unwrap=None):
    """Finish a bmesh (built in world coordinates) into an object in `export`.
    `mats` is one material or a list indexed by the faces' material_index.
    With `origin` (its joint) the mesh is written relative to it and the
    object sits there, under `parent`, so turning the pivot swings it."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    origin = Vector(origin) if origin is not None else Vector((0.0, 0.0, 0.0))
    if origin.length > 0:
        bmesh.ops.translate(bm, vec=-origin, verts=bm.verts)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(smooth_deg))
    mesh = bpy.data.meshes.new(named(name))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(named(name), mesh)
    home().objects.link(obj)
    for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
        mesh.materials.append(m)
    if parent is not None:
        obj.parent = parent
        obj.location = origin - world_loc(parent)
    else:
        obj.location = origin
    obj["kyt_collision"] = "none"
    if _ctx["variant"]:
        obj["kyt_variant"] = _ctx["variant"]
    if unwrap:
        obj["kyt_unwrap"] = unwrap
    return obj


def with_mat(bm, index):
    for f in bm.faces:
        f.material_index = index
    return bm


def join(bms):
    """Several bmeshes as one, their material indices kept."""
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


def lathe(profile, sides=24):
    """An (r, z) outline revolved about Z, in order. A point with r = 0 is a
    pole; a first or last point with r > 0 gets a flat cap."""
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


def lathe_loop(profile, sides):
    """A closed (r, z) outline revolved about Z: a ring with no caps (a
    jelly's fringe)."""
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(TAU * i / sides), r * math.sin(TAU * i / sides), z))
              for i in range(sides)] for r, z in profile]
    for a in range(len(rings)):
        A, B = rings[a], rings[(a + 1) % len(rings)]
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((A[i], A[j], B[j], B[i]))
    return bm


def lobed(bm, lobes, amp, r_rim, offset=0.0):
    """Scallop a revolved rim: radius times 1 + amp cos(lobes angle), full at
    the rim and fading toward the axis."""
    for v in bm.verts:
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-9:
            continue
        w = min(1.0, r / r_rim) ** 3
        f = 1 + amp * w * math.cos(lobes * (math.atan2(v.co.y, v.co.x) - offset))
        v.co.x *= f
        v.co.y *= f
    return bm


def sphere_profile(r, zc, n=12):
    return [(r * math.sin(math.pi * i / n), zc - r * math.cos(math.pi * i / n)) for i in range(n + 1)]


def ellipsoid(centre, radii, sides=14, rings=8):
    bm = lathe(sphere_profile(1.0, 0.0, rings), sides)
    return move(bm, Matrix.Translation(centre) @ Matrix.Diagonal((*radii, 1.0)))


def loft(rings, *, bottom_pole=None, top_pole=None, bottom_face=None):
    """Quads between successive rings of equal length; a fan to `bottom_pole`
    or `top_pole` (points), or a flat n-gon over the first ring with material
    index `bottom_face`."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if bottom_pole is not None:
        p = bm.verts.new(bottom_pole)
        for k in range(n):
            bm.faces.new((vs[0][(k + 1) % n], vs[0][k], p))
    if top_pole is not None:
        p = bm.verts.new(top_pole)
        for k in range(n):
            bm.faces.new((vs[-1][k], vs[-1][(k + 1) % n], p))
    if bottom_face is not None:
        f = bm.faces.new(list(reversed(vs[0])))
        f.material_index = bottom_face
    return bm


def tube(points, radii, sides=8, start="cap", end="pole", *, flatten=None, twist=None, up=None):
    """A tapering round tube along a polyline: one radius per point, its frame
    carried along so it never twists on its own. `flatten` (per point) squashes
    the section across its binormal into a ribbon; `twist` (radians per point)
    turns the section's frame about the tube, so a ribbon's broad face turns;
    `up` sets the first frame's normal (a ribbon's broad face lies along it). `start` and `end`:
    'cap' (flat), 'pole' (a point) or 'open'."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        t = pts[1] - pts[0] if i == 0 else pts[-1] - pts[-2] if i == n - 1 else pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    ref = Vector(up) if up is not None else Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i > 0:
            nrm = tangents[i - 1].rotation_difference(tangents[i]) @ nrm
            nrm = (nrm - tangents[i] * nrm.dot(tangents[i])).normalized()
        if (i == n - 1 and end == "pole") or (i == 0 and start == "pole"):
            rings.append([bm.verts.new(pts[i])])
            continue
        bin_ = tangents[i].cross(nrm).normalized()
        fl = flatten[i] if flatten else 1.0
        tw = twist[i] if twist else 0.0
        n2 = math.cos(tw) * nrm + math.sin(tw) * bin_
        b2 = -math.sin(tw) * nrm + math.cos(tw) * bin_
        rings.append([bm.verts.new(pts[i] + radii[i] * (math.cos(TAU * k / sides) * n2
                                                        + fl * math.sin(TAU * k / sides) * b2))
                      for k in range(sides)])
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            j = (k + 1) % sides
            if len(a) == 1:
                bm.faces.new((a[0], b[k], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[k], a[j], b[0]))
            else:
                bm.faces.new((a[k], a[j], b[j], b[k]))
    if start == "cap" and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if end == "cap" and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return bm


def plate(fn, nu, nv, thick):
    """A thin closed plate over a (u, v) grid: `fn(u, v)` (each 0..1) is a
    point of its mid-surface, the two faces `thick` apart along the surface's
    normal (the velella's sail)."""
    P = [[Vector(fn(i / (nu - 1), j / (nv - 1))) for j in range(nv)] for i in range(nu)]

    def normal(i, j):
        du = P[min(i + 1, nu - 1)][j] - P[max(i - 1, 0)][j]
        dv = P[i][min(j + 1, nv - 1)] - P[i][max(j - 1, 0)]
        n = du.cross(dv)
        return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))

    bm = bmesh.new()
    A = [[bm.verts.new(P[i][j] - normal(i, j) * thick / 2) for j in range(nv)] for i in range(nu)]
    B = [[bm.verts.new(P[i][j] + normal(i, j) * thick / 2) for j in range(nv)] for i in range(nu)]
    for i in range(nu - 1):
        for j in range(nv - 1):
            bm.faces.new((A[i][j], A[i][j + 1], A[i + 1][j + 1], A[i + 1][j]))
            bm.faces.new((B[i][j], B[i + 1][j], B[i + 1][j + 1], B[i][j + 1]))
    loop = ([(i, 0) for i in range(nu)] + [(nu - 1, j) for j in range(1, nv)]
            + [(i, nv - 1) for i in range(nu - 2, -1, -1)] + [(0, j) for j in range(nv - 2, 0, -1)])
    for k in range(len(loop)):
        (i0, j0), (i1, j1) = loop[k], loop[(k + 1) % len(loop)]
        bm.faces.new((A[i0][j0], A[i1][j1], B[i1][j1], B[i0][j0]))
    return bm


def taper(n, r0, r1, power=1.0):
    return [r0 + (r1 - r0) * (i / (n - 1)) ** power for i in range(n)]


def spline(ctrl, n):
    """A Catmull-Rom curve through the control points, sampled at n points."""
    pts = [Vector(p) for p in ctrl]
    P = [pts[0]] + pts + [pts[-1]]
    segs = len(pts) - 1
    out = []
    for i in range(n):
        u = i / (n - 1) * segs
        s = min(int(u), segs - 1)
        t = u - s
        p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    return out


def fillet(points, radius, segs=4):
    """A polyline with each inside corner rounded to an arc of `radius`."""
    pts = [Vector(p) for p in points]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p, a, b = pts[i], pts[i - 1], pts[i + 1]
        d1, d2 = (a - p).normalized(), (b - p).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if radius <= 0 or ang > math.radians(179.0):
            out.append(p)
            continue
        t = radius / math.tan(ang / 2)
        c = p + (d1 + d2).normalized() * (radius / math.sin(ang / 2))
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


def box(x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    v = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    for idx in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[i] for i in idx])
    return bm


def meshes(objs=None):
    return [o for o in (objs if objs is not None else export().all_objects) if o.type == "MESH"]


def bounds(objs):
    bpy.context.view_layer.update()
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
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
        ev.to_mesh_clear()
    return n


def units(coll=None):
    """(variant, objects) for each variant of a collection, or ('', all) for
    an animal without variants."""
    objs = list((coll or export()).all_objects)
    tags = sorted({str(o.get("kyt_variant", "")) for o in objs})
    return [(t, [o for o in objs if str(o.get("kyt_variant", "")) == t]) for t in tags]


def roots(objs):
    return [o for o in objs if o.parent is None or o.parent not in objs]


def shift(objs, offset):
    """Move a group by `offset`: a loose part moves in its mesh so its origin
    stays put, a root pivot moves so it stays at its joint."""
    for o in roots(objs):
        if o.type == "MESH" and o.parent is None and o.location.length < 1e-9:
            o.data.transform(Matrix.Translation(offset))
            o.data.update()
        else:
            o.location += offset


def settle(objs):
    """The group's lowest point onto z = 0."""
    lo, _ = bounds(meshes(objs))
    if abs(lo.z) > 1e-7:
        shift(objs, Vector((0.0, 0.0, -lo.z)))


# --- the crab ----------------------------------------------------------------
#
# Cancer productus: a broad bun of a carapace, widest at mid-length, the rear
# half narrowing; stalked eyes at the front edge; the claws carried folded in
# front at body height, the walking legs arching to the knee about level with
# the shell's top and dropping to the rock. Left is +X.

CR_W, CR_L, CR_H = 0.165, 0.112, 0.046
CR_STAND = 0.026              # carapace underside over the rock
CR_TAPER = 0.22               # the rear half narrows to this much less at the tail
CR_SHELL = (0.60, 0.16, 0.09, 1.0)
CR_TIP = (0.12, 0.06, 0.05, 1.0)
CR_EYE = (0.05, 0.04, 0.04, 1.0)
# per leg, front to back: hip angle on the rim, the leg's heading (both
# degrees from the front), thigh length, shin reach
CR_LEGS = ((64, 74, 0.060, 0.036), (84, 94, 0.066, 0.040), (104, 116, 0.062, 0.038), (124, 140, 0.052, 0.032))
CR_LEG_RISE = 32.0            # degrees the thigh climbs from the hip
CR_LEG_R = (0.0140, 0.0055)   # leg radius at the hip and the foot
CR_CLAW_ANGLE = 27.0


def crab_rim(angle_from_front, side, inset=0.96, height=0.30):
    """A point on the carapace's flank, `angle` degrees from the front (-Y)
    toward `side`'s flank, at `height` of the shell."""
    a = math.radians(angle_from_front)
    x = side * (CR_W / 2) * inset * math.sin(a)
    y = -(CR_L / 2) * inset * math.cos(a)
    x *= 1 - CR_TAPER * max(0.0, y / (CR_L / 2))
    return Vector((x, y, CR_STAND + CR_H * height))


def build_crab():
    shell = material("crab_shell", CR_SHELL)
    tip = material("crab_claw_tip", CR_TIP)
    eye = material("crab_eye", CR_EYE)
    bun = [(0, 0), (0.45, 0.0), (0.80, 0.05), (0.97, 0.20), (1.0, 0.42), (0.93, 0.63), (0.72, 0.81), (0.40, 0.94), (0, 1.0)]
    bm = lathe([(r, z * CR_H) for r, z in bun], 18)
    for v in bm.verts:
        x, y = v.co.x * CR_W / 2, v.co.y * CR_L / 2
        v.co = Vector((x * (1 - CR_TAPER * max(0.0, y / (CR_L / 2))), y, v.co.z + CR_STAND))
    part("carapace", bm, shell, unwrap="lathe")

    for side, sname in ((1, "left"), (-1, "right")):
        # eyes on short stalks at the front edge
        base = Vector((side * 0.030, -CR_L / 2 * 0.78, CR_STAND + CR_H * 0.60))
        knob = base + Vector((side * 0.004, -0.013, 0.009))
        stalk = with_mat(tube([base, knob], [0.0045, 0.0045], 6, "cap", "cap"), 0)
        ball = with_mat(ellipsoid(knob + Vector((0, -0.003, 0.003)), (0.0080, 0.0080, 0.0080), 8, 4), 1)
        part(f"eye_{sname}", join([stalk, ball]), [shell, eye])

        # walking legs: one bent tapering tube each, hip to rock
        for i, (ang, heading, thigh, shin) in enumerate(CR_LEGS, 1):
            hip = crab_rim(ang, side)
            d = Vector((side * math.sin(math.radians(heading)), -math.cos(math.radians(heading)), 0.0))
            rise = math.radians(CR_LEG_RISE)
            knee = hip + d * thigh * math.cos(rise) + Vector((0, 0, thigh * math.sin(rise)))
            foot = Vector((knee.x + d.x * shin, knee.y + d.y * shin, 0.0))
            path = fillet([hip, knee, foot], 0.018, 2)
            piv = pivot(f"leg_{sname}_{i}_pivot", hip)
            part(f"leg_{sname}_{i}", tube(path, taper(len(path), *CR_LEG_R, 1.3), 6, "cap", "pole"),
                 shell, parent=piv, origin=hip)

        # the claw: arm from the shoulder, hand with its fixed finger, and the
        # movable finger hinged at the hand's far end
        hip = crab_rim(CR_CLAW_ANGLE, side)
        elbow = hip + Vector((side * 0.052, -0.030, 0.012))
        wrist = elbow + Vector((side * 0.004, -0.040, -0.004))
        piv = pivot(f"claw_{sname}_pivot", hip)
        arm = fillet([hip, elbow, wrist], 0.016, 2)
        part(f"claw_{sname}_arm", tube(arm, taper(len(arm), 0.0150, 0.0135), 7, "cap", "cap"),
             shell, parent=piv, origin=hip)
        ahead = Vector((-side * 0.42, -1.0, -0.12)).normalized()
        hand_len = 0.060
        hc = wrist + ahead * hand_len * 0.5
        palm = ellipsoid((0, 0, 0), (0.015, 0.022, hand_len * 0.5), 10, 6)
        move(palm, Matrix.Translation(hc) @ ahead.to_track_quat("Z", "Y").to_matrix().to_4x4())
        inward = Vector((-side, 0.0, 0.0))
        f0 = hc + ahead * hand_len * 0.40 + Vector((0, 0, -0.008))
        f1 = f0 + ahead * 0.018 + inward * 0.004
        f2 = f0 + ahead * 0.031 + inward * 0.013 + Vector((0, 0, 0.004))
        finger = tube(spline([f0, f1, f2], 4), taper(4, 0.0110, 0.0040), 6, "cap", "pole")
        part(f"claw_{sname}_hand", join([with_mat(palm, 0), with_mat(finger, 1)]), [shell, tip],
             parent=piv, origin=hip)
        h0 = hc + ahead * hand_len * 0.40 + Vector((0, 0, 0.010))
        dpiv = pivot(f"claw_{sname}_dactyl_pivot", h0, parent=piv)
        d1 = h0 + ahead * 0.018 + inward * 0.003 + Vector((0, 0, 0.001))
        d2 = h0 + ahead * 0.031 + inward * 0.013 + Vector((0, 0, -0.005))
        part(f"claw_{sname}_dactyl", tube(spline([h0, d1, d2], 4), taper(4, 0.0100, 0.0040), 6, "cap", "pole"),
             tip, parent=dpiv, origin=h0)


# --- the starfish -----------------------------------------------------------
#
# Pisaster ochraceus, lying flat: a star outline (a broad disc, stout arms
# with straight edges from web to a round blunt tip) lofted up as a puffed
# cushion, the arms pulled in faster than the disc as the rings rise so they
# slope to the rock and the disc stays high. One arm toward -Y, the five a
# little uneven.

SF_R_ARM, SF_R_WEB, SF_R_TIP = 0.125, 0.058, 0.017   # arm reach, web radius, tip roundness
SF_ARM_LEN = (1.0, 0.95, 1.03, 0.97, 0.92)    # each arm's reach, from the one toward -Y round counterclockwise
SF_RINGS = ((0.92, 0.92, 0.0), (1.0, 1.0, 0.009), (0.95, 0.92, 0.019), (0.86, 0.74, 0.029),
            (0.70, 0.50, 0.037), (0.46, 0.26, 0.043))   # disc scale, arm scale, z
SF_TOP = 0.046
SF_SKIN = (0.86, 0.40, 0.10, 1.0)


def starfish_outline():
    """Ten points an arm, counterclockwise from the web before the arm
    toward -Y: the web, two along the edge, five round the tip, two back."""
    out = []
    for k in range(5):
        th = -math.pi / 2 + TAU * k / 5
        a = Vector((math.cos(th), math.sin(th)))
        p = Vector((-a.y, a.x))
        web = Vector((math.cos(th - TAU / 10), math.sin(th - TAU / 10))) * SF_R_WEB
        c = a * (SF_R_ARM * SF_ARM_LEN[k] - SF_R_TIP)
        t1, t2 = c - p * SF_R_TIP, c + p * SF_R_TIP
        nxt = Vector((math.cos(th + TAU / 10), math.sin(th + TAU / 10))) * SF_R_WEB
        out.append(web)
        out += [web.lerp(t1, f) for f in (0.38, 0.72)]
        out += [c + (math.cos(g) * a + math.sin(g) * p) * SF_R_TIP
                for g in (-math.pi / 2, -math.pi / 4, 0.0, math.pi / 4, math.pi / 2)]
        out += [t2.lerp(nxt, f) for f in (0.28, 0.62)]
    return out


def build_starfish():
    skin = material("starfish_skin", SF_SKIN)
    outline = starfish_outline()

    def ring(sd, sa, z):
        pts = []
        for q in outline:
            r = q.length
            k = SF_R_WEB * sd + (r - SF_R_WEB) * sa
            pts.append((q.x / r * k, q.y / r * k, z))
        return pts

    bm = loft([ring(*p) for p in SF_RINGS], bottom_pole=(0, 0, 0), top_pole=(0, 0, SF_TOP))
    part("body", bm, skin)


# --- the sea urchin -----------------------------------------------------------
#
# Strongylocentrotus purpuratus: a flattened ball of a test with fat spines
# radiating from it on a golden spiral, the mouth underneath left bare, the
# bottom spines standing it off the rock.

UR_R, UR_H = 0.0375, 0.046
UR_SPINES = 40
UR_SPINE_L, UR_SPINE_R = 0.022, 0.0068
UR_MOUTH = -0.86               # spiral points below this (of the unit sphere) are the bare mouth
UR_TEST = (0.33, 0.13, 0.40, 1.0)
UR_SPINE = (0.46, 0.20, 0.56, 1.0)


def build_urchin():
    test_m = material("urchin_test", UR_TEST)
    spine_m = material("urchin_spine", UR_SPINE)
    bm = lathe(sphere_profile(1.0, 0.0, 8), 16)
    move(bm, Matrix.Translation((0, 0, UR_H / 2)) @ Matrix.Diagonal((UR_R, UR_R, UR_H / 2, 1.0)))
    part("test", bm, test_m, unwrap="lathe")
    rng = random.Random(15)
    golden = math.pi * (3 - math.sqrt(5))
    cones = []
    for i in range(UR_SPINES):
        zc = 1 - 2 * (i + 0.5) / UR_SPINES
        if zc < UR_MOUTH:
            continue
        rc = math.sqrt(max(0.0, 1 - zc * zc))
        phi = i * golden
        n = Vector((rc * math.cos(phi), rc * math.sin(phi), zc))
        on = Vector((UR_R * n.x, UR_R * n.y, UR_H / 2 * n.z + UR_H / 2))
        out = Vector((n.x / UR_R, n.y / UR_R, n.z / (UR_H / 2))).normalized()
        jitter = Matrix.Rotation(math.radians(rng.uniform(-9, 9)), 3, "X") @ Matrix.Rotation(math.radians(rng.uniform(-9, 9)), 3, "Y")
        out = (jitter @ out).normalized()
        length = UR_SPINE_L * (0.82 if zc > 0.72 else 1.0) * rng.uniform(0.9, 1.08)
        cones.append(tube([on - out * 0.004, on + out * length], [UR_SPINE_R, 0.0], 6, "cap", "pole"))
    part("spines", join(cones), spine_m)


# --- the scallop ------------------------------------------------------------
#
# Crassadoma gigantea, the rock scallop: each valve an even dome over a fan
# outline, the fan a slightly irregular circle centred below the umbo, the
# hinge line with its two small ears across the top; eight broad ribs as a
# wave in the rim and low ridges fanning from the umbo. Inside, a shell lip
# and a shallow dished cavity in the mantle's orange, which is what shows in
# the gap. The lower valve, cemented to the rock in life, is the shallower.

SC_RC, SC_CY = 0.066, -0.061          # the fan's circle, radius and centre y below the hinge corner
SC_EAR_X, SC_HINGE_Y = 0.030, 0.010
SC_RIBS, SC_RIB_AMP, SC_RIB_H = 8, 0.030, 0.13   # ribs: count, wave in the rim, ridge height (of the dome) at the rim
SC_WOBBLE = ((2, 0.040, 0.7), (3, 0.025, 2.1))   # lumps in the outline: (waves round it, amount, phase)
SC_APEX = Vector((0.0, -0.030))       # the umbo, where the ribs fan from and the dome is highest
SC_DOME_UP, SC_DOME_LOW = 0.024, 0.015
SC_LEVELS = ((1.0, 0.0), (1.0, 0.14), (0.70, 0.62), (0.36, 0.92))   # outside: scale toward the umbo, height fraction
SC_INSIDE = ((0.90, 0.0), (0.52, 0.45))      # the cavity: scale toward the umbo, depth fraction into the dome
SC_OPEN = 12.0                        # degrees the upper valve is raised
SC_SHELL = (0.58, 0.46, 0.38, 1.0)
SC_FLESH = (0.95, 0.55, 0.20, 1.0)


def scallop_outline():
    """(point, rib) pairs round the valve, counterclockwise from the left
    hinge corner: `rib` is the rib wave at that point, 0 on the ears."""
    x_i = math.sqrt(SC_RC ** 2 - SC_CY ** 2)
    phi1 = math.atan2(-SC_CY, -x_i)
    phi2 = math.atan2(-SC_CY, x_i) + TAU
    n_arc = SC_RIBS * 3 + 1
    out = []
    for k in range(n_arc):
        u = k / (n_arc - 1)
        phi = phi1 + (phi2 - phi1) * u
        rib = math.cos(TAU * SC_RIBS * u)
        lump = sum(a * math.sin(w * math.pi * u + p) for w, a, p in SC_WOBBLE) * math.sin(math.pi * u)
        r = SC_RC * (1 + SC_RIB_AMP * rib + lump)
        out.append((Vector((r * math.cos(phi), SC_CY + r * math.sin(phi))), rib))
    for p in ((SC_EAR_X, 0.0), (SC_EAR_X, SC_HINGE_Y), (-SC_EAR_X, SC_HINGE_Y), (-SC_EAR_X, 0.0)):
        out.append((Vector(p), 0.0))
    return out


def valve_bm(dome):
    """One valve, rim on z = 0, the dome up: outside in shell (material 0)
    from the inner lip over the top to the umbo; the cavity under it in
    mantle (material 1)."""
    outline = scallop_outline()

    def ring(s, z_of):
        return [(SC_APEX + (p - SC_APEX) * s).to_3d() + Vector((0, 0, z_of(rib))) for p, rib in outline]

    inner = [ring(s, lambda rib, h=h: dome * h) for s, h in reversed(SC_INSIDE)]
    # the ridges strongest at the rim, fading toward the umbo they fan from
    outer = [ring(s, lambda rib, h=h, s=s: dome * (h + SC_RIB_H * rib * s ** 2 * (h > 0))) for s, h in SC_LEVELS]
    bm = loft(inner + outer, bottom_pole=(SC_APEX.x, SC_APEX.y, dome * (SC_INSIDE[-1][1] + 0.08)),
              top_pole=(SC_APEX.x, SC_APEX.y, dome))
    # loft makes the bands ring by ring, then the bottom fan, then the top
    # fan: the cavity is the bands between the inner rings and the bottom fan
    n, total = len(outline), len(bm.faces)
    for i, f in enumerate(bm.faces):
        f.material_index = 1 if i < n * (len(SC_INSIDE) - 1) or total - 2 * n <= i < total - n else 0
    return bm


def build_scallop():
    shell = material("scallop_shell", SC_SHELL)
    flesh = material("scallop_mantle", SC_FLESH)
    # the shell centred in plan: the fan's middle on the origin
    centre_y = (SC_HINGE_Y + SC_CY - SC_RC) / 2
    to_centre = Matrix.Translation((0.0, -centre_y, 0.0))
    lower = valve_bm(SC_DOME_LOW)
    move(lower, to_centre @ Matrix.Translation((0, 0, SC_DOME_LOW)) @ Matrix.Diagonal((1.0, 1.0, -1.0, 1.0)))
    part("valve_lower", lower, [shell, flesh])
    hinge = Vector((0.0, SC_HINGE_Y - centre_y, SC_DOME_LOW))
    piv = pivot("valve_pivot", hinge)
    upper = valve_bm(SC_DOME_UP)
    move(upper, to_centre @ Matrix.Translation((0, 0, SC_DOME_LOW)))
    part("valve_upper", upper, [shell, flesh], parent=piv, origin=hinge)
    piv.rotation_euler = (math.radians(-SC_OPEN), 0.0, 0.0)
    part("hinge", move(with_mat(box(-0.014, 0.014, 0.004, SC_HINGE_Y + 0.001,
                                    SC_DOME_LOW - 0.004, SC_DOME_LOW + 0.005), 0), to_centre),
         shell, smooth_deg=30.0)


# --- the jellyfish -----------------------------------------------------------
#
# Four variants at the origin together. The two swimmers as they swim: the
# bell a solid of revolution, inner cavity and outer dome in one profile,
# rim on z = 0 locally, lobed at the rim; the mouth stalk under it; ribbon
# oral arms from the stalk's foot and, on the nettle, strand tentacles from
# the clefts of the rim, every one on its own pivot under the bell's. The
# velella floating and stranded: an oval float, a diagonal sail and a short
# fringe under the rim.

JELLY_VARIANTS = ("moon", "sea_nettle", "velella", "velella_stranded")
SWIMMERS = {
    "moon": dict(
        bell=((0, 0.014), (0.060, 0.011), (0.105, 0.005), (0.125, 0.0), (0.127, 0.004), (0.118, 0.016),
              (0.098, 0.031), (0.066, 0.044), (0.032, 0.052), (0, 0.055)),
        lobes=0.022, stalk=((0, 0.014), (0.026, 0.011), (0.020, -0.004), (0, -0.010)),
        fringe=0.010,
        arms=dict(length=0.085, r=(0.022, 0.015), flatten=0.32, points=6, sides=6, spread=0.016,
                  wiggle=0.30, turn=0.10, end="cap", curl=0.020),
        tentacles=None,
        colours=dict(bell=(0.80, 0.84, 0.95, 1.0), arms=(0.92, 0.74, 0.84, 1.0))),
    "sea_nettle": dict(
        bell=((0, 0.040), (0.050, 0.034), (0.090, 0.020), (0.118, 0.0), (0.123, 0.022), (0.116, 0.060),
              (0.096, 0.100), (0.060, 0.130), (0, 0.145)),
        lobes=0.035, stalk=((0, 0.040), (0.032, 0.034), (0.026, 0.0), (0.030, -0.026), (0, -0.034)),
        fringe=None,
        arms=dict(length=0.65, r=(0.030, 0.012), flatten=0.22, points=8, sides=6, spread=0.050,
                  wiggle=0.6, turn=0.55, end="pole", curl=0.0),
        tentacles=dict(count=8, length=0.85, r=(0.0060, 0.0022), flatten=0.50, points=8, sides=3),
        colours=dict(bell=(0.86, 0.52, 0.22, 1.0), arms=(0.95, 0.86, 0.74, 1.0), tentacle=(0.45, 0.12, 0.14, 1.0))),
}
JELLY_SIDES, JELLY_LOBES = 24, 8

# by-the-wind sailor (Velella velella)
VE_L, VE_W, VE_T = 0.070, 0.046, 0.0055       # float length, width and thickness
VE_SAIL_H, VE_SAIL_L, VE_SAIL_T = 0.036, 0.060, 0.0018
VE_SAIL_TURN = 42.0                            # degrees the sail's line is turned off the float's length
VE_FRINGE = 0.0045
VE_SIDES = 12
VE_FLOAT_C = (0.12, 0.28, 0.72, 1.0)
VE_SAIL_C = (0.82, 0.88, 0.94, 1.0)
VE_FRINGE_C = (0.07, 0.13, 0.40, 1.0)
VE_WATERLINE = 0.45                            # of the float's thickness, from its underside


def build_swimmer(tag):
    spec = SWIMMERS[tag]
    c = spec["colours"]
    bell_m = material(f"{tag}_bell", c["bell"])
    arm_m = material(f"{tag}_arms", c["arms"])
    rim_r = spec["bell"][3][0]
    root = pivot("bell_pivot", (0, 0, 0))
    part("bell", lobed(lathe(spec["bell"], JELLY_SIDES), JELLY_LOBES, spec["lobes"], rim_r),
         bell_m, parent=root, origin=(0, 0, 0), unwrap="lathe")
    part("manubrium", lathe(spec["stalk"], 8), arm_m, parent=root, origin=(0, 0, 0), unwrap="lathe")
    if spec["fringe"]:
        # one skirt hanging inside the rim; its strands are a cut-out for later
        L = spec["fringe"]
        ring = ((rim_r - 0.002, 0.001), (rim_r * 1.025, -L), (rim_r - 0.005, 0.001))
        part("fringe", lobed(lathe_loop(ring, JELLY_SIDES), JELLY_LOBES, spec["lobes"], rim_r),
             arm_m, parent=root, origin=(0, 0, 0), smooth_deg=89.0)
    rng = random.Random(22 if tag == "sea_nettle" else 23)
    foot_z = spec["stalk"][-1][1]
    a_spec = spec["arms"]
    L = a_spec["length"]
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = Vector((-d.y, d.x, 0.0))
        s0 = d * 0.014 + Vector((0, 0, foot_z + 0.004))
        w, wig = a_spec["spread"], a_spec["wiggle"]
        ctrl = [s0,
                s0 + d * w * 0.7 + Vector((0, 0, -0.25 * L)),
                s0 + d * w * 0.9 + side * w * wig * rng.uniform(0.6, 1.3) + Vector((0, 0, -0.52 * L)),
                s0 + d * w * 1.0 - side * w * wig * rng.uniform(0.6, 1.3) + Vector((0, 0, -0.78 * L)),
                s0 + d * (w * 0.8 + a_spec["curl"]) + side * w * wig * 0.6
                + Vector((0, 0, -L + a_spec["curl"] * 0.5))]
        n = a_spec["points"]
        path = spline(ctrl, n)
        piv = pivot(f"arm_{k + 1}_pivot", s0, parent=root)
        # the broad face toward the bell's axis, turning as it hangs
        ribbon = tube(path, taper(n, *a_spec["r"]), a_spec["sides"], "cap", a_spec["end"], up=side,
                      flatten=[a_spec["flatten"]] * n, twist=[i * a_spec["turn"] for i in range(n)])
        part(f"arm_{k + 1}", ribbon, arm_m, parent=piv, origin=s0)
    t_spec = spec["tentacles"]
    if t_spec:
        tent_m = material(f"{tag}_tentacle", c["tentacle"])
        L = t_spec["length"]
        cleft_r = rim_r * (1 - spec["lobes"]) - 0.006
        for k in range(t_spec["count"]):
            a = math.radians(22.5 + 360 / t_spec["count"] * k)      # the clefts between the lobes
            d = Vector((math.cos(a), math.sin(a), 0.0))
            side = Vector((-d.y, d.x, 0.0))
            t0 = d * cleft_r + Vector((0, 0, 0.004))
            wob = rng.uniform(0.7, 1.3)
            ctrl = [t0,
                    t0 + d * 0.028 * wob + Vector((0, 0, -0.30 * L)),
                    t0 + d * 0.012 + side * 0.026 * wob + Vector((0, 0, -0.66 * L)),
                    t0 - d * 0.008 + side * 0.008 + Vector((0, 0, -L * rng.uniform(0.93, 1.0)))]
            n = t_spec["points"]
            path = spline(ctrl, n)
            piv = pivot(f"tentacle_{k + 1}_pivot", t0, parent=root)
            part(f"tentacle_{k + 1}", tube(path, taper(n, *t_spec["r"]), t_spec["sides"], "cap", "pole",
                                           up=side, flatten=[t_spec["flatten"]] * n),
                 tent_m, parent=piv, origin=t0)


def velella_float_bm():
    """The oval float, its underside on z = 0, long along Y: a low dome with a
    rounded edge, its concentric rings paint."""
    profile = ((0, 0.0), (0.80, 0.0), (0.97, 0.0012), (1.0, 0.0030), (0.86, 0.0048), (0.45, VE_T), (0, VE_T + 0.0004))
    bm = lathe(profile, VE_SIDES)
    for v in bm.verts:
        v.co.x *= VE_W / 2
        v.co.y *= VE_L / 2
    return bm


def velella_fringe_bm(hang):
    """The tentacle fringe, one closed skirt under the float's rim, hanging
    `hang` below it (its strands are a cut-out for later)."""
    ring = ((0.90, 0.0005), (0.97, -hang), (0.83, 0.0005))
    bm = lathe_loop(ring, VE_SIDES)
    for v in bm.verts:
        v.co.x *= VE_W / 2
        v.co.y *= VE_L / 2
    return bm


def velella_sail_fn(bend=0.0):
    """The sail's mid-surface: along its foot (u) on a line through the float's
    middle turned VE_SAIL_TURN off its length, up its height (v). `bend`
    (radians) curls it over toward +X' as it rises, as a stranded sail
    flops."""
    turn = math.radians(VE_SAIL_TURN)
    along = Vector((math.sin(turn), -math.cos(turn), 0.0))
    across = Vector((math.cos(turn), math.sin(turn), 0.0))

    def height(u):
        # a rounded triangle, its peak a little behind the middle
        peak = 0.42
        t = u / peak if u < peak else (1 - u) / (1 - peak)
        return max(0.10, math.sin(t * math.pi / 2) ** 0.9) * VE_SAIL_H

    def fn(u, v):
        s = (u - 0.5) * VE_SAIL_L * (0.92 + 0.08 * math.sin(math.pi * u))
        h = height(u) * v
        if bend > 1e-6:
            # the sail curls over on an arc whose total turn is `bend` at the top
            rho = VE_SAIL_H / bend
            phi = h / rho
            off, up = rho * (1 - math.cos(phi)), rho * math.sin(phi)
        else:
            off, up = 0.0, h
        return along * s + across * off + Vector((0, 0, up))

    return fn


def build_velella(stranded):
    float_m = material("velella_float", VE_FLOAT_C)
    sail_m = material("velella_sail", VE_SAIL_C)
    fringe_m = material("velella_fringe", VE_FRINGE_C)
    if not stranded:
        lift = Vector((0, 0, VE_FRINGE))               # the fringe hangs from the float to z = 0
        root = pivot("float_pivot", lift + Vector((0, 0, VE_T / 2)))
        flt = part("float", move(velella_float_bm(), Matrix.Translation(lift)), float_m,
                   parent=root, origin=root.location, unwrap="lathe")
        part("fringe", move(velella_fringe_bm(VE_FRINGE), Matrix.Translation(lift)), fringe_m,
             parent=root, origin=root.location, smooth_deg=89.0)
        foot = lift + Vector((0, 0, VE_T - 0.0008))
        spiv = pivot("sail_pivot", foot, parent=root)
        part("sail", move(plate(velella_sail_fn(), 6, 2, VE_SAIL_T), Matrix.Translation(foot)), sail_m,
             parent=spiv, origin=foot, smooth_deg=40.0)
        _waterlines["velella"] = (flt, VE_WATERLINE)
        return
    # stranded: the float lying on the sand tipped a little onto one long
    # edge, the fringe squashed flat round it, the sail curled over toward
    # the low side so its tip nearly reaches the sand
    tip = Matrix.Rotation(math.radians(-7.0), 4, "Y")
    root = pivot("float_pivot", (0, 0, VE_T / 2))
    part("float", move(velella_float_bm(), tip), float_m, parent=root, origin=root.location, unwrap="lathe")
    part("fringe", move(velella_fringe_bm(0.0012), tip), fringe_m, parent=root, origin=root.location,
         smooth_deg=89.0)
    foot = tip @ Vector((0, 0, VE_T - 0.0008))
    spiv = pivot("sail_pivot", foot, parent=root)
    sail = plate(velella_sail_fn(bend=math.radians(80)), 6, 4, VE_SAIL_T)
    move(sail, Matrix.Translation(foot) @ tip @ Matrix.Rotation(math.radians(180), 4, "Z"))
    part("sail", sail, sail_m, parent=spiv, origin=foot, smooth_deg=40.0)


def build_jellyfish():
    for tag in JELLY_VARIANTS:
        begin_variant(tag)
        if tag in SWIMMERS:
            build_swimmer(tag)
        else:
            build_velella(stranded=tag.endswith("_stranded"))
        end_variant()
    # one variant shown in the viewport at a time; click a collection's eye
    layers = bpy.context.view_layer.layer_collection.children["export"].children
    for tag in JELLY_VARIANTS[1:]:
        layers[tag].hide_viewport = True


def place_waterlines():
    """An empty in `reference` at each floating variant's water surface."""
    ref = bpy.data.collections.get("reference")
    for tag, (flt, frac) in _waterlines.items():
        lo, hi = bounds([flt])
        e = bpy.data.objects.new(f"waterline_{tag}", None)
        e.empty_display_type = "PLAIN_AXES"
        e.empty_display_size = 0.05
        e.location = (0.0, 0.0, lo.z + frac * (hi.z - lo.z))
        e["kyt_note"] = f"the water surface for {tag}: the placement puts this height on the water"
        ref.objects.link(e)
        print(f"  waterline_{tag} at z = {e.location.z:.4f} (the float {lo.z:.4f}..{hi.z:.4f})")


# --- the octopus -------------------------------------------------------------
#
# Octopus bimaculoides at rest: the mantle a bulb lying back behind the head,
# the head a flattened egg with two eye bumps on top, the siphon on its right,
# eight arms from a crown under the head reaching out, lying along the rock
# and curling at the tip. Eyes toward -Y, so its left is +X.

OC_HEAD_C, OC_HEAD_R = Vector((0.0, -0.010, 0.052)), (0.052, 0.050, 0.042)
OC_MANTLE_BASE, OC_MANTLE_TILT = Vector((0.0, 0.030, 0.050)), 15.0
OC_MANTLE = ((0, 0), (0.045, 0.012), (0.062, 0.045), (0.066, 0.080), (0.057, 0.115), (0.038, 0.140), (0, 0.152))
OC_CROWN_R, OC_CROWN_Z = 0.042, 0.030
OC_ARM_R0, OC_ARM_R1, OC_ARM_L = 0.024, 0.0035, 0.29
# plan bearings from +X, front (1) to back (4): left arms toward +X
OC_ARMS = (("left", 1, -67.5), ("left", 2, -22.5), ("left", 3, 22.5), ("left", 4, 60.0),
           ("right", 1, -112.5), ("right", 2, -157.5), ("right", 3, 157.5), ("right", 4, 120.0))
OC_SKIN = (0.50, 0.33, 0.22, 1.0)
OC_EYE = (0.08, 0.06, 0.05, 1.0)


def build_octopus():
    skin = material("octopus_skin", OC_SKIN)
    eye_m = material("octopus_eye", OC_EYE)
    bm = lathe(OC_MANTLE, 16)
    move(bm, Matrix.Translation(OC_MANTLE_BASE) @ Matrix.Rotation(math.radians(-(90 - OC_MANTLE_TILT)), 4, "X"))
    part("mantle", bm, skin, unwrap="lathe")
    part("head", ellipsoid(OC_HEAD_C, OC_HEAD_R, 14, 7), skin, unwrap="lathe")
    for side, sname in ((1, "left"), (-1, "right")):
        c = OC_HEAD_C + Vector((side * 0.036, -0.012, 0.030))
        bump = with_mat(ellipsoid(c, (0.018, 0.017, 0.016), 12, 6), 0)
        pupil = with_mat(ellipsoid(c + Vector((side * 0.011, -0.009, 0.006)), (0.0075, 0.0075, 0.0075), 8, 4), 1)
        part(f"eye_{sname}", join([bump, pupil]), [skin, eye_m], unwrap="lathe")
    siphon = tube([Vector((-0.040, 0.030, 0.030)), Vector((-0.078, -0.004, 0.028))], [0.012, 0.009], 7, "cap", "cap")
    part("siphon", siphon, skin)
    rng = random.Random(25)
    for sname, num, bearing in OC_ARMS:
        a = math.radians(bearing)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = Vector((d.y, -d.x, 0.0))           # to the arm's right: every tip curls clockwise
        L = OC_ARM_L * rng.uniform(0.9, 1.1)
        curl = rng.uniform(0.7, 1.3)
        p0 = Vector((OC_CROWN_R * d.x, OC_CROWN_R * d.y - 0.010, OC_CROWN_Z))
        drop = Vector((0, 0, -OC_CROWN_Z))
        ctrl = [p0,
                p0 + d * 0.15 * L + Vector((0, 0, -0.012)),
                p0 + d * 0.40 * L + side * 0.01 + drop + Vector((0, 0, 0.015)),
                p0 + d * 0.675 * L + side * 0.05 * curl + drop + Vector((0, 0, 0.010)),
                p0 + d * 0.825 * L + side * 0.11 * curl + drop + Vector((0, 0, 0.007)),
                p0 + d * 0.775 * L + side * 0.15 * curl + drop + Vector((0, 0, 0.012))]
        path = spline(ctrl, 12)
        radii = taper(len(path), OC_ARM_R0, OC_ARM_R1, 1.0)
        for i, p in enumerate(path):
            p.z = max(p.z, radii[i] + 0.001)      # lying on the rock by its own thickness
        piv = pivot(f"arm_{sname}_{num}_pivot", p0)
        part(f"arm_{sname}_{num}", tube(path, radii, 8, "cap", "pole"), skin, parent=piv, origin=p0)


BUILDERS = {"crab": build_crab, "starfish": build_starfish, "sea_urchin": build_urchin,
            "scallop": build_scallop, "jellyfish": build_jellyfish, "octopus": build_octopus}


# --- renders ------------------------------------------------------------------

def stage_scene():
    """Engine, world, a review collection with ground, sun and camera."""
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
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.72, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)

    def stage_object(tag, bm, colour):
        mesh = bpy.data.meshes.new(tag)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        o = bpy.data.objects.new(tag, mesh)
        mesh.materials.append(material(f"render_{tag}", colour))
        stage.objects.link(o)
        return o

    stage_object("ground", box(-40, 40, -40, 40, -0.02, -0.0005), (0.50, 0.48, 0.44, 1))
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.4
    sun.rotation_euler = (math.radians(50), math.radians(12), math.radians(40))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    cam.data.clip_start = 0.005
    stage.objects.link(cam)
    scene.camera = cam
    return scene, stage, cam, stage_object


def ruler(stage_object, origin, vertical=False, tag="ruler"):
    """A 0.30 m bar of alternating 0.05 m light and dark steps, lying along X
    from `origin` or standing up from it."""
    out = []
    w = 0.012
    for i in range(int(round(RULER / RULER_STEP))):
        a, b = origin[0] + i * RULER_STEP, origin[0] + (i + 1) * RULER_STEP
        if vertical:
            bm = box(origin[0], origin[0] + w, origin[1], origin[1] + w, origin[2] + i * RULER_STEP, origin[2] + (i + 1) * RULER_STEP)
        else:
            bm = box(a, b, origin[1], origin[1] + w, origin[2], origin[2] + w)
        out.append(stage_object(f"{tag}_{i}", bm, (0.95, 0.95, 0.92, 1) if i % 2 == 0 else (0.12, 0.12, 0.12, 1)))
    return out


def points_of(objs):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def shoot(scene, cam, path, frame, direction, lens=40, min_z=0.02, margin=0.05):
    """The camera along `direction` from the framed objects' centre, backed
    off until every vertex is in frame, then rendered to `path`."""
    pts = points_of(frame)
    lo, hi = Vector(map(min, *pts)), Vector(map(max, *pts))
    centre = (lo + hi) / 2
    d = Vector(direction).normalized()
    dist = max((hi - lo).length * 0.9, 0.12)
    cam.data.lens = lens
    for _ in range(120):
        cam.location = centre + d * dist
        cam.location.z = max(cam.location.z, min_z)
        look = centre - cam.location
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if all(margin <= c.x <= 1 - margin and margin <= c.y <= 1 - margin
               for c in (world_to_camera_view(scene, cam, p) for p in pts)):
            break
        dist *= 1.07
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


VIEWS = (("three_quarter", (-0.75, -1.0, 0.55)), ("front", (0.0, -1.0, 0.18)),
         ("side", (1.0, 0.0, 0.18)), ("top", (0.0, -0.001, 1.0)))


def scale_bar(stage_object, parts, tag="ruler"):
    lo, hi = bounds(parts)
    if hi.z - lo.z > 0.45:
        return ruler(stage_object, (hi.x + 0.10, 0.0, 0.0), vertical=True, tag=tag)
    return ruler(stage_object, ((lo.x + hi.x) / 2 - RULER / 2, lo.y - 0.05, 0.0), tag=tag)


def render(folder, name):
    os.makedirs(folder, exist_ok=True)
    scene, stage, cam, stage_object = stage_scene()
    groups = units()
    every = meshes()
    for tag, objs in groups:
        parts = meshes(objs)
        for o in every:
            o.hide_render = o not in parts
        stem = f"{name}_{tag}" if tag else name
        for view, d in VIEWS:
            shoot(scene, cam, os.path.join(folder, f"{stem}_{view}.png"), parts, d)
        bar = scale_bar(stage_object, parts)
        shoot(scene, cam, os.path.join(folder, f"{stem}_scale.png"), parts + bar, (-0.6, -1.0, 0.45))
        for o in bar:
            bpy.data.objects.remove(o)
    if len(groups) > 1:
        # every variant in a row, at true relative size, beside the ruler
        for o in every:
            o.hide_render = False
        x = 0.0
        for tag, objs in groups:
            lo, hi = bounds(meshes(objs))
            shift(objs, Vector((x - lo.x, 0.0, 0.0)))
            x += hi.x - lo.x + 0.08
        bar = ruler(stage_object, (x + 0.02, 0.0, 0.0), vertical=True)
        shoot(scene, cam, os.path.join(folder, f"{name}_all.png"), every + bar, (-0.35, -1.0, 0.30), margin=0.03)


SMALL = 0.10          # the lineup's close view: the animals lower than this


def lineup(png, files):
    """The animals and their variants in a row at true relative size, lowest
    first, with the ruler and their names, from a fresh empty session:
    nothing is saved."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene, stage, cam, stage_object = stage_scene()
    groups = []
    for f in files:
        stem = os.path.splitext(os.path.basename(f))[0]
        with bpy.data.libraries.load(os.path.abspath(f), link=False) as (src, dst):
            dst.collections = [c for c in src.collections if c == "export"]
        coll = dst.collections[0]
        coll.name = f"lineup_{stem}"
        scene.collection.children.link(coll)
        for layer in bpy.context.view_layer.layer_collection.children[coll.name].children:
            layer.hide_viewport = False
        for tag, objs in units(coll):
            lo, hi = bounds(meshes(objs))
            groups.append((tag.replace("_", " ") if tag else stem.replace("_", " "), objs, hi.z - lo.z))
    groups.sort(key=lambda g: g[2])
    label_m = material("render_label", (0.10, 0.10, 0.10, 1))
    x = 0.0
    shown, small = [], []
    gap = 0.10
    for label_text, objs, height in groups:
        parts = meshes(objs)
        lo, hi = bounds(parts)
        shift(objs, Vector((x - lo.x, -(lo.y + hi.y) / 2, 0.0)))
        lo, hi = bounds(parts)
        curve = bpy.data.curves.new(f"label_{label_text}", "FONT")
        curve.body = label_text
        curve.size = 0.035
        curve.align_x = "CENTER"
        label = bpy.data.objects.new(f"label_{label_text}", curve)
        label.data.materials.append(label_m)
        label.rotation_euler = (math.radians(90), 0.0, 0.0)
        label.location = ((lo.x + hi.x) / 2, lo.y - 0.04, 0.0)
        stage.objects.link(label)
        shown += parts
        if height <= SMALL:
            small += parts + [label]
        x = max(hi.x, label.location.x + 0.035 * len(label_text) * 0.3) + gap
    bar = ruler(stage_object, (x, 0.0, 0.0), vertical=True)
    os.makedirs(os.path.dirname(os.path.abspath(png)), exist_ok=True)
    shoot(scene, cam, png, shown + bar, (-0.15, -1.0, 0.28), margin=0.03)
    if small and len(small) < len(shown):
        stem, ext = os.path.splitext(png)
        lo, hi = bounds([o for o in small if o.type == "MESH"])
        flat = ruler(stage_object, (lo.x, lo.y - 0.10, 0.0), tag="ruler_flat")
        shoot(scene, cam, f"{stem}_small{ext}", small + flat, (-0.25, -1.0, 0.55), margin=0.03)


# --- main ----------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--lineup" in argv:
        i = argv.index("--lineup")
        lineup(argv[i + 1], argv[i + 2:])
        return
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in BUILDERS:
        raise SystemExit(f"wildlife_invertebrates: open one of {', '.join(BUILDERS)}, not {name!r}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"wildlife_invertebrates: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for child in list(coll.children):     # a variant's own collection
            bpy.data.collections.remove(child)
        for o in [o for o in bpy.data.objects if o.name.startswith("waterline_")]:
            bpy.data.objects.remove(o)        # this tool's markers in `reference`
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    BUILDERS[name]()
    for tag, objs in units():
        settle(objs)
    if _waterlines:
        place_waterlines()
    for tag, objs in units():
        parts = meshes(objs)
        pivots = [o for o in objs if o.type == "EMPTY"]
        lo, hi = bounds(parts)
        tris = triangles(parts)
        label = tag or name
        print(f"wildlife_invertebrates: {label}: {len(parts)} parts, {len(pivots)} pivots, {tris} triangles "
              f"(budget {BUDGETS[label]}{', OVER' if tris > BUDGETS[label] else ''})")
        print(f"  size {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x D x H), "
              f"x {lo.x:.3f}..{hi.x:.3f}, y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.4f}..{hi.z:.3f}")
        print("  parts: " + ", ".join(f"{o.name} {triangles([o])}" for o in parts))
        if pivots:
            print("  pivots: " + ", ".join(f"{o.name} ({'/'.join(f'{v:.3f}' for v in o.matrix_world.translation)})" for o in pivots))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
