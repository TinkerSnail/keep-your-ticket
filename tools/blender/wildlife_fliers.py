"""The four flying ambient animals, a first pass (2026-10-03) from the
catalog's "Ambient wildlife" rows, which Christina asked for on 2026-09-29.
None has a photograph of hers; each is the plainest field-guide reading of its
species in the house style, at real size, for her to reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<animal>.blend --python tools/blender/wildlife_fliers.py -- \\
        [--replace] [--save] [--render <folder>]

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \\
        --python tools/blender/wildlife_fliers.py -- --lineup <folder>

`<animal>` is `bee` (PRP-WILD-006), `fly` (007), `hummingbird` (008) or
`butterfly` (009). The tool builds whichever the file is named for into
`export`, one object a part, head toward -Y here (+Z in Godot), real metres
(one Blender unit a metre, Z up), the lowest point on z = 0 and the plan
centred on the origin. It refuses while `export` holds anything (it may be
hers) unless `--replace`; it writes the file only with `--save`; `--render`
shoots a three-quarter view, orthographic front, side and top views and one
beside a 0.10 m ruler into the folder, after the save, so the render's
camera, sun, ground and ruler never reach the file. `--lineup` opens no prop
file: it appends the four saved animals, stands them in a row at true
relative size beside the ruler (`fliers.png`) and again each scaled to the
same size, its longest extent 0.12 m, labelled with its factor
(`fliers_enlarged.png`), both orthographic from in front and above so none
looks bigger for standing nearer, and saves nothing. Equal size rather than
equal height, because the butterfly lies flat: at the others' height it would
be several times wider than the frame.

**Articulation, no animation.** Every moving part hangs under an empty at its
joint, the gull's pattern (`assets/source/wildlife/gull_adult.blend`:
`head_pivot`, `wing_left`, `leg_left`): `head_pivot` at the neck (the eyes and
antennae ride on it), `wing_left_pivot` and `wing_right_pivot` at the wing
roots (a bee's or a butterfly's fore and hind wing on one, as they beat
together), one `leg_<side>_<front|mid|hind>_pivot` per insect leg at its coxa,
the hummingbird's `bill_upper_pivot` and `bill_lower_pivot` at the gape (under
`head_pivot`), `tail_pivot` and `leg_<side>_pivot`. A part's origin is its
pivot, so turning the empty swings the part at the joint. All of it hangs from
one root empty named for the animal, which carries the centring and, on the
hummingbird, the hover's pitch. Sides are the animal's own: facing -Y, its
left is +X (Blender's .L). No armature, no keyframes, nothing in Godot: how
each moves is a separate decision. Send to game merges every part into one
mesh unless the scene is marked `kyt_keep_parts`; that mark is not set here,
so the pivots are a modelling fact until that decision is made.

**Honey bee**, a worker (`bee`). About 15 mm from face to sting: a head 4.4 mm
wide, flattened front to back, with two tall oval eyes on its sides and
elbowed antennae; a round thorax 4.8 by 5.2 mm; an egg abdomen 5 mm across
and 7.8 mm long, behind a pinched waist, drooping 8 degrees. Wings spread out
to the sides mid-stroke, each a single card: the forewing 9.5 by 3.3 mm swept
back 22 degrees and raised 10, the hindwing 6.3 by 2.2 mm just behind and
under it, swept 48 and raised 5 (no two cards share a plane). Wingspan about
20 mm. Six legs standing, feet on the ground, the hind pair thicker (the
pollen baskets), so the same pose reads landed or hovering legs-down.
Stripes, fuzz and wing veins are paint.

**House fly** (`fly`). About 7.8 mm long: a wide head almost all eye (two big
red-brown compound eyes), a thorax 3.1 by 3.5 mm, a broad blunt abdomen
drooping 4 degrees.
Wings folded back over the abdomen in the resting V, each 6.2 by 2.2 mm,
25 degrees off the body's line (swept 65 from straight out) and raised 1.5,
just clear of the abdomen, the costa outward, tips just past it. Six legs standing. No
antennae or halteres (too small to read: paint). Thorax stripes, eye facets,
bristles and veins are paint.

**Anna's hummingbird**, a male (`hummingbird`), the resident of coastal San
Diego at latitude 32.75. Hovering: the root pitches the body 40 degrees
nose-up and `head_pivot` bends the head 25 degrees forward, so the bill points
15 degrees up; wings straight out to the sides mid-stroke, laid near level in
the world (swept back 4, raised 6, leading edge up 15), tail fanned and
dropped 15 degrees, feet tucked under the belly. In its own frame before the
pitch: body 40 mm long and 22 mm through; an oversized round head 17 mm with
domed bead eyes set into it; a straight closed bill 19 mm past the face in two halves (upper and
lower), each on its pivot at the gape; wings 52 mm long and 18.5 mm at the
widest as chunky 1.2 mm plates (a feathered panel, not a membrane); tail
31 mm as a notched fan plate. Bill tip to tail tip about 100 mm, wingspan
about 120 mm. The rose crown and gorget, the green back, the grey belly and
the flight-feather edges are paint; the head's stand-in is rose so it reads.

**Monarch butterfly** (`butterfly`). Basking, wings open flat with a slight
lift (forewing 6 degrees, hindwing 3, the forewing over the hindwing where
they overlap). Each wing is a single card whose outline is the monarch's: the
forewing 50 mm from base to its angled apex, a long straight costa and an
outer margin running back to the tornus; the rounded hindwing 38 mm out and
35 mm back. Wingspan about 101 mm. Body 25 mm, chunkier than life: head 4 mm with big
eyes, clubbed antennae reaching 12 mm ahead of it, thorax 5.2 by 7.6 mm,
abdomen 15 mm and 4 mm through, drooping 6 degrees, visible between the
hindwings. Four walking legs
standing (a nymphalid's forelegs are tucked and tiny, so they are left out).
Veins, the black borders, the white spots and the body's dots are paint.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied): few
big rounded forms, slightly oversized heads and eyes, chunky blunt legs;
nothing fine. Stand-in materials are flat colours by surface, a few per
animal, for the painting to replace; closed parts are single-sided and the
wing cards double-sided, seen from both sides like the plants' leaves
(`plant_blades.material`). Every part is `kyt_collision = "none"`: ambient
wildlife never blocks the player. Wing and tail sheets carry the unwrap hint
`planar`; the bodies carry none (`lathe` is for a part turned about an upright
axis through its origin, and these turn about their length), so their unwrap
is stage 3's question.
"""

import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

TAU = math.tau
MM = 0.001
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
PROPS = os.path.join(ROOT, "assets", "source", "props")
ANIMALS = ("bee", "fly", "hummingbird", "butterfly")
BUDGET = {"bee": 400, "fly": 400, "hummingbird": 1200, "butterfly": 400}
# Facing -Y, an animal's own left is +X (Blender's .L convention).
SIDES = ((1, "left"), (-1, "right"))

# stand-in colours (linear), for the painting to replace
BEE_AMBER = (0.80, 0.50, 0.10, 1.0)
BEE_DARK = (0.05, 0.04, 0.03, 1.0)
INSECT_WING = (0.78, 0.82, 0.86, 1.0)
FLY_GREY = (0.22, 0.24, 0.26, 1.0)
FLY_DARK = (0.05, 0.05, 0.05, 1.0)
FLY_EYE = (0.55, 0.10, 0.06, 1.0)
HB_GREEN = (0.16, 0.42, 0.18, 1.0)
HB_ROSE = (0.72, 0.06, 0.26, 1.0)
HB_DARK = (0.07, 0.07, 0.07, 1.0)
EYE_BLACK = (0.01, 0.01, 0.01, 1.0)
MONARCH_ORANGE = (0.88, 0.36, 0.04, 1.0)
BUTTERFLY_BLACK = (0.04, 0.035, 0.03, 1.0)

POS = {}  # empty -> its position in the root's frame while building
ROUND = 180.0  # smooth every edge: the round parts and the limbs


# --- the file --------------------------------------------------------------------

def material(name, colour, sheet=False):
    """A flat stand-in colour. A `sheet` material is seen from both sides (a
    wing card is one face); a closed part's is single-sided. Set every time,
    so a --replace over an older build takes the current colour."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if mat.node_tree is None:  # Blender 5 gives a new material its nodes
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = 0.75
    mat.diffuse_color = colour
    mat.use_backface_culling = not sheet
    return mat


def export():
    return bpy.data.collections["export"]


def empty(name, pos, parent):
    """A pivot at `pos` (the root's frame, metres), hanging under `parent`."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.004
    export().objects.link(e)
    pos = Vector(pos)
    if parent is not None:
        e.parent = parent
        e.location = pos - POS[parent]
    else:
        e.location = pos
    POS[e] = pos
    return e


def part(name, bm, mat, pivot, *, unwrap=None, sheet=False, smooth_deg=ROUND):
    """Finish a bmesh built in the root's frame into a part under `pivot`,
    its origin at the pivot so the joint turns it. A `sheet` is a single
    face kept pointing up (+Z in the build frame)."""
    bmesh.ops.transform(bm, matrix=Matrix.Translation(-POS[pivot]), verts=bm.verts)
    mesh = bpy.data.meshes.new(name)
    if sheet:
        bm.normal_update()
        if sum(f.normal.z for f in bm.faces) < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    else:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    export().objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = pivot
    clean(obj)
    smooth_by_angle(obj, smooth_deg)
    obj["kyt_collision"] = "none"
    if unwrap:
        obj["kyt_unwrap"] = unwrap
    return obj


def clean(obj):
    """Merge coincident vertices and drop faces with no area, as every prop
    part does (`unwrap_parts.py` needs the same faces in the same order)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-8, edges=bm.edges)
    bad = [f for f in bm.faces if f.calc_area() < 1e-13]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
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


# --- shapes, all in millimetres until `mm()` --------------------------------------

def mm(bm):
    bmesh.ops.scale(bm, vec=(MM, MM, MM), verts=bm.verts)
    return bm


def move(bm, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return bm


def rings_mesh(rings, start_pole=None, end_pole=None, caps=True):
    """Quads between successive rings of equal length; a pole point or a flat
    cap closes each end."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if start_pole is not None:
        p = bm.verts.new(start_pole)
        for k in range(n):
            bm.faces.new((vs[0][(k + 1) % n], vs[0][k], p))
    elif caps:
        bm.faces.new(list(reversed(vs[0])))
    if end_pole is not None:
        p = bm.verts.new(end_pole)
        for k in range(n):
            bm.faces.new((vs[-1][k], vs[-1][(k + 1) % n], p))
    elif caps:
        bm.faces.new(vs[-1])
    return bm


def revolve_y(profile, sides):
    """An (r, y) outline revolved about the Y axis, front (-Y) to back. An
    end with r = 0 is a pole; one with r > 0 gets a flat cap."""
    rings, poles = [], [None, None]
    for i, (r, y) in enumerate(profile):
        if r < 1e-9:
            poles[0 if i == 0 else 1] = (0.0, y, 0.0)
        else:
            rings.append([(r * math.cos(TAU * k / sides), y, r * math.sin(TAU * k / sides)) for k in range(sides)])
    return rings_mesh(rings, poles[0], poles[1])


def tilt_x(bm, about, deg):
    """Turn a shape about an X axis through `about`: positive drops +Y."""
    about = Vector(about)
    return move(bm, Matrix.Translation(about) @ Matrix.Rotation(math.radians(-deg), 4, "X") @ Matrix.Translation(-about))


def lathe(profile, sides, z, tilt=0.0):
    """A body segment: the (r, y) profile revolved about a fore-and-aft axis
    at height `z`, drooping `tilt` degrees from its front end."""
    bm = move(revolve_y(profile, sides), Matrix.Translation((0.0, 0.0, z)))
    if tilt:
        tilt_x(bm, (0.0, profile[0][1], z), tilt)
    return bm


def ellipsoid(centre, radii, sides, rings):
    """A ball at `centre` stretched to `radii` (x, y, z), its poles on Y."""
    prof = [(math.sin(math.pi * i / rings), -math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    bm = revolve_y(prof, sides)
    return move(bm, Matrix.Translation(centre) @ Matrix.Diagonal((*radii, 1.0)))


def sweep(points, radii, sides):
    """A round tube along a polyline, its radius set at each point (0 at an
    end makes a point, more than 0 a blunt cap), its frame carried along so
    it never twists."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        t = pts[1] - pts[0] if i == 0 else pts[-1] - pts[-2] if i == n - 1 else pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    rings, poles = [], [None, None]
    for i in range(n):
        if i > 0:
            nrm = tangents[i - 1].rotation_difference(tangents[i]) @ nrm
            nrm = (nrm - tangents[i] * nrm.dot(tangents[i])).normalized()
        bin_ = tangents[i].cross(nrm).normalized()
        if radii[i] < 1e-9:
            poles[0 if i == 0 else 1] = tuple(pts[i])
            continue
        rings.append([tuple(pts[i] + radii[i] * (math.cos(TAU * k / sides) * nrm + math.sin(TAU * k / sides) * bin_))
                      for k in range(sides)])
    return rings_mesh(rings, poles[0], poles[1])


def basis(origin, u_dir, v_dir):
    """The matrix taking a shape drawn in (u, v, n) to the world, u and v
    along the given directions and n their normal."""
    u = Vector(u_dir).normalized()
    v = Vector(v_dir)
    v = (v - u * v.dot(u)).normalized()
    n = u.cross(v)
    o = Vector(origin)
    return Matrix(((u.x, v.x, n.x, o.x), (u.y, v.y, n.y, o.y), (u.z, v.z, n.z, o.z), (0.0, 0.0, 0.0, 1.0)))


def wing_frame(root, sweep_deg, raise_deg, side, roll_deg=0.0):
    """A wing's frame at its root: u out from the body (side +1 is +X),
    swept back (toward +Y) by `sweep_deg` from straight out and raised
    `raise_deg`; v forward across it, toward the leading edge, turned
    `roll_deg` about u so a positive roll lifts the leading edge. The two
    sides are mirror images, so one outline serves both."""
    out = Vector((side, 0.0, 0.0))
    back = Vector((0.0, 1.0, 0.0))
    up = Vector((0.0, 0.0, 1.0))
    s, r = math.radians(sweep_deg), math.radians(raise_deg)
    u = ((out * math.cos(s) + back * math.sin(s)) * math.cos(r) + up * math.sin(r)).normalized()
    v = -back * math.cos(s) + out * math.sin(s)
    v = (v - u * v.dot(u)).normalized()
    if roll_deg:
        w = u.cross(v)
        w = w if w.z >= 0 else -w  # the side of the wing that faces up
        a = math.radians(roll_deg)
        v = v * math.cos(a) + w * math.sin(a)
    return basis(root, u, v)


def sheet(outline, frame):
    """One face: the outline (u, v) laid in `frame`."""
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(frame @ Vector((u, v, 0.0))) for u, v in outline])
    return bm


def plate(outline, thickness, frame):
    """The outline (u, v) as a slab `thickness` thick about its plane."""
    bm = bmesh.new()
    h = thickness / 2
    lo = [bm.verts.new(frame @ Vector((u, v, -h))) for u, v in outline]
    hi = [bm.verts.new(frame @ Vector((u, v, h))) for u, v in outline]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def plan_wing(outline, hinge_x, hinge_z, raise_deg, side):
    """A butterfly wing card drawn in plan: `outline` is (x, y) for the +X
    wing (x out from the midline, y toward the tail), laid at `hinge_z` and
    lifted `raise_deg` about the fore-and-aft hinge line at `hinge_x`; side -1
    is its mirror image."""
    a = math.radians(raise_deg)
    pts = []
    for x, y in outline:
        d = x - hinge_x
        pts.append(Vector((side * (hinge_x + d * math.cos(a)), y, hinge_z + d * math.sin(a))))
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in pts])
    return bm


def legs(root_empty, names, coxae, knees, feet, radii, sides, mat):
    """Standing legs, one pivot each at the coxa: coxa, knee, foot as given
    for the +X (left) leg, mirrored for the right. `radii` is one (coxa,
    knee, foot) tuple per leg; the foot's radius makes it a blunt pad."""
    for name, coxa, knee, foot, rad in zip(names, coxae, knees, feet, radii):
        for side, tag in SIDES:
            c = Vector((coxa[0] * side, coxa[1], coxa[2]))
            k = Vector((knee[0] * side, knee[1], knee[2]))
            f = Vector((foot[0] * side, foot[1], foot[2]))
            piv = empty(f"leg_{tag}_{name}_pivot", c * MM, root_empty)
            part(f"leg_{tag}_{name}", mm(sweep([c, k, f], rad, sides)), mat, piv)


# --- the bee ---------------------------------------------------------------------

BEE_ABDOMEN = [(0, 2.0), (1.6, 2.9), (2.5, 4.7), (2.25, 6.9), (1.2, 8.8), (0, 9.8)]
BEE_FORE = [(0, 0.8), (1.5, 1.4), (4.0, 1.7), (7.0, 1.4), (9.0, 0.7), (9.5, -0.2), (8.4, -1.2), (5.5, -1.6),
            (2.5, -1.3), (0, -0.6)]
BEE_HIND = [(0, 0.5), (1.5, 0.9), (3.5, 1.05), (5.6, 0.6), (6.3, -0.2), (5.2, -0.9), (2.8, -1.1), (0.6, -0.8)]


def build_bee():
    amber, dark = material("bee_amber", BEE_AMBER), material("bee_dark", BEE_DARK)
    wing = material("insect_wing", INSECT_WING, sheet=True)
    root = empty("bee", (0, 0, 0), None)
    part("thorax", mm(ellipsoid((0, 0, 5.0), (2.4, 2.6, 2.3), 8, 4)), amber, root)
    part("abdomen", mm(lathe(BEE_ABDOMEN, 8, 4.6, tilt=8)), amber, root)
    head = empty("head_pivot", Vector((0, -2.5, 5.2)) * MM, root)
    part("head", mm(ellipsoid((0, -3.9, 5.3), (2.2, 1.5, 2.1), 8, 4)), amber, head)
    for side, tag in SIDES:
        part(f"eye_{tag}", mm(ellipsoid((1.9 * side, -4.0, 5.6), (0.75, 1.15, 1.5), 6, 3)), dark, head)
        # elbowed: the scape up and forward from the face, the flagellum on out
        bm = sweep([(0.55 * side, -5.1, 6.1), (0.95 * side, -6.4, 7.5), (1.9 * side, -8.6, 7.1)], (0.26, 0.24, 0.22), 3)
        part(f"antenna_{tag}", mm(bm), dark, head)
    for side, tag in SIDES:
        fore_root = (1.25 * side, -0.9, 6.8)
        piv = empty(f"wing_{tag}_pivot", Vector(fore_root) * MM, root)
        part(f"wing_{tag}_fore", mm(sheet(BEE_FORE, wing_frame(fore_root, 22, 10, side))),
             wing, piv, unwrap="planar", sheet=True)
        part(f"wing_{tag}_hind", mm(sheet(BEE_HIND, wing_frame((1.25 * side, -0.1, 6.6), 48, 5, side))),
             wing, piv, unwrap="planar", sheet=True)
    legs(root, ("front", "mid", "hind"),
         coxae=((1.0, -1.5, 3.5), (1.2, -0.2, 3.1), (1.0, 1.2, 3.4)),
         knees=((2.9, -2.9, 3.9), (3.4, 0.0, 3.7), (3.0, 2.8, 3.7)),
         feet=((3.4, -4.4, 0.3), (4.4, 0.4, 0.3), (3.8, 5.4, 0.3)),
         radii=((0.36, 0.30, 0.26), (0.36, 0.30, 0.26), (0.40, 0.44, 0.30)), sides=4, mat=dark)
    return root


# --- the fly ---------------------------------------------------------------------

FLY_ABDOMEN = [(0, 1.0), (1.35, 1.6), (1.6, 2.6), (1.4, 3.6), (0.75, 4.3), (0, 4.6)]
FLY_WING = [(0, 0.45), (1.0, 0.85), (3.0, 1.1), (5.0, 0.9), (6.2, 0.2), (6.0, -0.5), (4.8, -1.0), (2.8, -1.1),
            (1.0, -0.8), (0, -0.35)]


def build_fly():
    grey, dark, eye = material("fly_grey", FLY_GREY), material("fly_dark", FLY_DARK), material("fly_eye", FLY_EYE)
    wing = material("insect_wing", INSECT_WING, sheet=True)
    root = empty("fly", (0, 0, 0), None)
    part("thorax", mm(ellipsoid((0, 0, 3.0), (1.55, 1.75, 1.45), 8, 4)), grey, root)
    part("abdomen", mm(lathe(FLY_ABDOMEN, 8, 2.85, tilt=4)), grey, root)
    head = empty("head_pivot", Vector((0, -1.5, 3.1)) * MM, root)
    part("head", mm(ellipsoid((0, -2.25, 3.15), (1.35, 0.95, 1.25), 8, 4)), grey, head)
    for side, tag in SIDES:
        part(f"eye_{tag}", mm(ellipsoid((1.0 * side, -2.4, 3.3), (0.8, 0.9, 1.1), 8, 4)), eye, head)
    for side, tag in SIDES:
        # folded back in the resting V over the abdomen, the costa outward
        wing_root = (0.7 * side, -0.4, 4.35)
        piv = empty(f"wing_{tag}_pivot", Vector(wing_root) * MM, root)
        part(f"wing_{tag}", mm(sheet(FLY_WING, wing_frame(wing_root, 65, 1.5, side))),
             wing, piv, unwrap="planar", sheet=True)
    legs(root, ("front", "mid", "hind"),
         coxae=((0.7, -0.9, 2.0), (0.8, 0.0, 1.9), (0.7, 0.8, 2.0)),
         knees=((1.9, -1.7, 2.5), (2.2, 0.1, 2.5), (1.9, 1.9, 2.4)),
         feet=((2.4, -2.9, 0.2), (3.0, 0.4, 0.2), (2.5, 3.6, 0.2)),
         radii=((0.24, 0.21, 0.18),) * 3, sides=4, mat=dark)
    return root


# --- the hummingbird -------------------------------------------------------------

HB_BODY = [(0, -18.0), (6.0, -16.5), (9.5, -12.0), (11.0, -5.0), (10.6, 3.0), (8.6, 10.0), (5.6, 16.0),
           (2.8, 20.0), (0, 22.0)]
HB_WING = [(0, 5.0), (8, 6.5), (18, 7.0), (30, 6.5), (40, 5.0), (47, 3.0), (51, 0.5), (52, -2.0), (50.5, -5.0),
           (45, -8.0), (36, -10.5), (26, -11.5), (16, -11.0), (8, -9.5), (0, -6.0)]
HB_TAIL = [(0, 3.2), (8, 6.5), (16, 9.5), (24, 12.5), (29, 13.0), (31, 9.5), (30, 4.5), (28.5, 0),
           (30, -4.5), (31, -9.5), (29, -13.0), (24, -12.5), (16, -9.5), (8, -6.5), (0, -3.2)]
HB_PITCH = 40.0  # degrees nose-up, hovering, on the root
HB_HEAD_BEND = 25.0  # degrees the head bends forward on head_pivot


def build_hummingbird():
    green, rose, dark, black = (material("hummingbird_green", HB_GREEN), material("hummingbird_rose", HB_ROSE),
                                material("hummingbird_dark", HB_DARK), material("eye_black", EYE_BLACK))
    root = empty("hummingbird", (0, 0, 0), None)
    part("body", mm(revolve_y(HB_BODY, 16)), green, root)
    head = empty("head_pivot", Vector((0, -17.5, 3.0)) * MM, root)
    part("head", mm(ellipsoid((0, -23.0, 4.5), (8.6, 8.6, 8.6), 14, 7)), rose, head)
    for side, tag in SIDES:
        part(f"eye_{tag}", mm(ellipsoid((7.2 * side, -25.6, 6.3), (1.4, 2.3, 2.3), 8, 4)), black, head)
    # closed: the lower half tucked up into the upper, their tips together
    gape = Vector((0, -30.5, 4.0)) * MM
    upper = empty("bill_upper_pivot", gape, head)
    part("bill_upper", mm(sweep([(0, -29.0, 4.7), (0, -40.0, 4.1), (0, -50.5, 3.4)], (1.5, 0.95, 0.0), 8)), dark, upper)
    lower = empty("bill_lower_pivot", gape, head)
    part("bill_lower", mm(sweep([(0, -29.0, 3.2), (0, -40.0, 3.05), (0, -50.0, 3.05)], (1.25, 0.8, 0.0), 8)), dark, lower)
    # Wings straight out mid-stroke, near level in the world: drawn in the
    # world's terms and turned back through the root's pitch.
    unpitch = Matrix.Rotation(math.radians(HB_PITCH), 4, "X")
    for side, tag in SIDES:
        shoulder = Vector((7.5 * side, -8.5, 6.5))
        piv = empty(f"wing_{tag}_pivot", shoulder * MM, root)
        frame = Matrix.Translation(shoulder) @ unpitch @ wing_frame((0, 0, 0), 4, 6, side, roll_deg=15)
        part(f"wing_{tag}", mm(plate(HB_WING, 1.2, frame)), dark, piv, unwrap="planar", smooth_deg=60)
    tail = empty("tail_pivot", Vector((0, 19.5, -0.5)) * MM, root)
    drop = math.radians(15)
    tail_frame = basis((0, 19.5, -0.5), (0, math.cos(drop), -math.sin(drop)), (1, 0, 0))
    part("tail", mm(plate(HB_TAIL, 1.2, tail_frame)), dark, tail, unwrap="planar", smooth_deg=60)
    for side, tag in SIDES:
        hip = Vector((3.2 * side, 2.0, -8.5))
        piv = empty(f"leg_{tag}_pivot", hip * MM, root)
        bm = sweep([hip, (3.8 * side, -0.5, -10.6), (4.2 * side, -2.6, -10.9)], (0.9, 0.7, 0.55), 4)
        part(f"foot_{tag}", mm(bm), dark, piv)
    head.rotation_euler = (math.radians(HB_HEAD_BEND), 0.0, 0.0)
    root.rotation_euler = (math.radians(-HB_PITCH), 0.0, 0.0)
    return root


# --- the butterfly ---------------------------------------------------------------

# plan outlines of the +X wings (x out, y toward the tail), from a set monarch
MONARCH_FORE = [(1.2, -2.8), (10, -6.0), (22, -9.3), (34, -11.8), (44, -12.9), (49.5, -11.2), (50.5, -7.0),
                (48.0, -0.5), (43.5, 6.5), (37.5, 11.5), (27, 10.5), (15, 7.5), (6, 3.5), (1.2, 0.5)]
MONARCH_HIND = [(1.2, -0.3), (10, 2.0), (22, 4.5), (32, 7.5), (37, 12.5), (38, 19.5), (35.5, 26.0), (29.5, 31.5),
                (21, 34.5), (13, 33.5), (7.5, 29.5), (3.5, 22.5), (2.0, 13.5), (1.2, 5.0)]
MONARCH_ABDOMEN = [(0, 2.2), (2.0, 3.8), (1.9, 9.0), (1.2, 14.5), (0, 17.5)]


def build_butterfly():
    black = material("butterfly_black", BUTTERFLY_BLACK)
    orange = material("monarch_orange", MONARCH_ORANGE, sheet=True)
    root = empty("butterfly", (0, 0, 0), None)
    part("thorax", mm(ellipsoid((0, -0.5, 4.3), (2.6, 3.8, 2.5), 8, 4)), black, root)
    part("abdomen", mm(lathe(MONARCH_ABDOMEN, 8, 4.0, tilt=6)), black, root)
    head = empty("head_pivot", Vector((0, -4.0, 4.5)) * MM, root)
    part("head", mm(ellipsoid((0, -5.6, 4.7), (2.0, 1.7, 1.9), 8, 4)), black, head)
    for side, tag in SIDES:
        part(f"eye_{tag}", mm(ellipsoid((1.55 * side, -5.9, 4.9), (0.85, 1.0, 1.1), 6, 3)), black, head)
        # a thin shaft swelling to a club at the tip
        bm = sweep([(0.5 * side, -6.4, 6.0), (2.4 * side, -13.5, 7.7), (3.2 * side, -16.6, 8.05),
                    (3.6 * side, -18.0, 8.15), (3.9 * side, -19.4, 8.2)], (0.2, 0.18, 0.22, 0.5, 0.3), 3)
        part(f"antenna_{tag}", mm(bm), black, head)
    for side, tag in SIDES:
        piv = empty(f"wing_{tag}_pivot", Vector((1.2 * side, -1.0, 5.1)) * MM, root)
        part(f"wing_{tag}_fore", mm(plan_wing(MONARCH_FORE, 1.2, 5.2, 6, side)),
             orange, piv, unwrap="planar", sheet=True)
        part(f"wing_{tag}_hind", mm(plan_wing(MONARCH_HIND, 1.2, 4.9, 3, side)),
             orange, piv, unwrap="planar", sheet=True)
    legs(root, ("mid", "hind"),
         coxae=((0.9, -2.0, 2.7), (0.9, 0.8, 2.7)),
         knees=((4.0, -3.4, 3.5), (4.0, 1.8, 3.4)),
         feet=((5.6, -5.6, 0.25), (5.4, 4.6, 0.25)),
         radii=((0.30, 0.26, 0.22),) * 2, sides=4, mat=black)
    return root


BUILDERS = {"bee": build_bee, "fly": build_fly, "hummingbird": build_hummingbird, "butterfly": build_butterfly}


# --- measuring -------------------------------------------------------------------

def meshes(objs):
    return [o for o in objs if o.type in ("MESH", "FONT")]


def points(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes(objs):
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def bounds(objs):
    pts = points(objs)
    return Vector(map(min, *pts)), Vector(map(max, *pts))


def triangles(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in meshes(objs):
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
        ev.to_mesh_clear()
    return n


def ground_and_centre(root, parts):
    """The root moved so the lowest point is on z = 0 and the plan is centred
    on the origin (the pose, rotations on the empties, is applied first)."""
    bpy.context.view_layer.update()
    lo, hi = bounds(parts)
    c = (lo + hi) / 2
    root.location = Vector(root.location) - Vector((c.x, c.y, lo.z))
    bpy.context.view_layer.update()


def sheet_planes_apart(parts):
    """No two single-face parts (the wing cards) in one plane."""
    planes = []
    for o in parts:
        if len(o.data.polygons) != 1:
            continue
        f = o.data.polygons[0]
        n = (o.matrix_world.to_3x3() @ f.normal).normalized()
        p = o.matrix_world @ o.data.vertices[f.vertices[0]].co
        planes.append((o.name, n, n.dot(p)))
    for i, (a, na, da) in enumerate(planes):
        for b, nb, db in planes[i + 1:]:
            if abs(abs(na.dot(nb)) - 1.0) < 1e-6 and abs(abs(da) - abs(db)) < 1e-6:
                print(f"  {a} and {b} share a plane")
                return False
    return True


def report(name, parts):
    lo, hi = bounds(parts)
    tris = triangles(parts)
    print(f"wildlife_fliers: {name}: {len(parts)} parts, {tris} triangles (target {BUDGET[name]})")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts))
    print(f"  size: {(hi.x - lo.x) * 1000:.1f} x {(hi.y - lo.y) * 1000:.1f} x {(hi.z - lo.z) * 1000:.1f} mm (W x D x H), "
          f"x {lo.x * 1000:.1f}..{hi.x * 1000:.1f}, y {lo.y * 1000:.1f}..{hi.y * 1000:.1f}, z {lo.z * 1000:.1f}..{hi.z * 1000:.1f} mm")
    pivots = [o for o in export().all_objects if o.type == "EMPTY"]
    print("  pivots: " + ", ".join(p.name for p in pivots))
    print("  materials: " + ", ".join(sorted({s.material.name for o in parts for s in o.material_slots})))
    lines = []
    lines.append(("budget", tris <= BUDGET[name]))
    lines.append(("lowest point on z = 0", abs(lo.z) < 1e-6))
    lines.append(("plan centred on the origin", abs(lo.x + hi.x) < 1e-6 and abs(lo.y + hi.y) < 1e-6))
    head = next(o for o in parts if o.name == "head")
    trunk = next(o for o in parts if o.name in ("thorax", "body"))
    lines.append(("head toward -Y", bounds([head])[0].y < bounds([trunk])[0].y))
    lines.append(("every part collides with nothing", all(str(o.get("kyt_collision")) == "none" for o in parts)))
    lines.append(("every part hangs from a pivot", all(o.parent is not None and o.parent.type == "EMPTY" for o in parts)))
    lines.append(("no part carries a scale", all(abs(c - 1.0) < 1e-6 for o in parts for c in o.scale)))
    lines.append(("no two wing cards share a plane", sheet_planes_apart(parts)))
    left = [o for o in parts if "_left" in o.name]
    right = [o for o in parts if "_right" in o.name]
    if left and right:
        ll, lh = bounds(left)
        rl, rh = bounds(right)
        lines.append(("the left side is +X", ll.x + lh.x > 0 > rl.x + rh.x))
        lines.append(("left and right mirror", abs(ll.x + rh.x) < 1e-6 and abs(lh.x + rl.x) < 1e-6
                      and abs(ll.z - rl.z) < 1e-6 and abs(ll.y - rl.y) < 1e-6))
    for text, ok in lines:
        print(f"  {'ok  ' if ok else 'FAIL'} {text}")
    return all(ok for _, ok in lines)


# --- rendering -------------------------------------------------------------------

def stage_setup(folder):
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
        scene.eevee.taa_render_samples = 32
    except AttributeError:
        pass
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.72, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.6
    sun.data.angle = math.radians(2.0)
    sun.rotation_euler = (math.radians(50), math.radians(12), math.radians(40))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 50
    cam.data.clip_start = 0.0005
    cam.data.clip_end = 100.0
    stage.objects.link(cam)
    scene.camera = cam
    return scene, stage, cam


def stage_mesh(stage, name, bm, colour):
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(name, mesh)
    o.data.materials.append(material(f"render_{name}", colour))
    stage.objects.link(o)
    return o


def box(x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    lo = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))]
    hi = [bm.verts.new(p) for p in ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def ruler(stage, x0, y, length=0.10, step=0.01, width=0.006, height=0.0015):
    """A scale bar along X from x0: alternating pale and dark 10 mm segments."""
    out = []
    for i in range(int(round(length / step))):
        bm = box(x0 + i * step, x0 + (i + 1) * step, y - width / 2, y + width / 2, 0.0, height)
        out.append(stage_mesh(stage, f"ruler_{i}", bm, (0.92, 0.92, 0.90, 1) if i % 2 == 0 else (0.10, 0.10, 0.11, 1)))
    return out


def ground(stage, size, z=-0.0001):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in ((-size, -size, z), (size, -size, z), (size, size, z), (-size, size, z))])
    return stage_mesh(stage, "ground", bm, (0.50, 0.48, 0.44, 1))


def shoot(scene, cam, folder, filename, framed, direction, lens=70, floor=None, top=False, ortho=False):
    """The camera along `direction` from the framed objects' centre, backed
    off until every vertex is in frame. `top` looks straight down with the
    head (-Y) at the top of the picture. `ortho` is an orthographic view,
    fitted to the framed vertices: a flat animal seen from the side in
    perspective shows its far wing above its near one."""
    pts = points(framed)
    lo, hi = Vector(map(min, *pts)), Vector(map(max, *pts))
    centre = (lo + hi) / 2
    size = (hi - lo).length
    d = Vector(direction).normalized()
    cam.data.type = "ORTHO" if ortho else "PERSP"
    cam.data.lens = lens
    if ortho:
        # beyond the ground's edge, so none of it lies behind the camera
        cam.location = centre + d * 30.0
        cam.rotation_euler = (0.0, 0.0, math.pi) if top else \
            (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        cs = [inv @ p for p in pts]
        x0, x1 = min(c.x for c in cs), max(c.x for c in cs)
        y0, y1 = min(c.y for c in cs), max(c.y for c in cs)
        cam.location = cam.matrix_world @ Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0.0))
        aspect = scene.render.resolution_x / scene.render.resolution_y
        cam.data.ortho_scale = max(x1 - x0, (y1 - y0) * aspect) / 0.88
        bpy.context.view_layer.update()
    else:
        dist = size * 0.8
        for _ in range(80):
            cam.location = centre + d * dist
            cam.location.z = max(cam.location.z, floor if floor is not None else lo.z + 0.12 * size)
            cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            if all(0.05 <= c.x <= 0.95 and 0.05 <= c.y <= 0.95
                   for c in (world_to_camera_view(scene, cam, p) for p in pts)):
                break
            dist *= 1.06
    scene.render.filepath = os.path.join(folder, filename)
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath)


def render(folder, name):
    scene, stage, cam = stage_setup(folder)
    parts = meshes(export().all_objects)
    lo, hi = bounds(parts)
    ground(stage, 20.0)  # past the orthographic views' frame, inside their camera
    shoot(scene, cam, folder, f"{name}_three_quarter.png", parts, (-0.75, -1.0, 0.55))
    shoot(scene, cam, folder, f"{name}_front.png", parts, (0.0, -1.0, 0.03), ortho=True)
    shoot(scene, cam, folder, f"{name}_side.png", parts, (1.0, 0.0, 0.03), ortho=True)
    shoot(scene, cam, folder, f"{name}_top.png", parts, (0.0, 0.0, 1.0), top=True, ortho=True)
    # beside a 0.10 m ruler, laid in front of the animal
    bar = ruler(stage, -0.05, lo.y - 0.012)
    shoot(scene, cam, folder, f"{name}_scale.png", parts + bar, (-0.45, -1.0, 0.6))


def label(stage, text, x, y, size):
    """A caption lying flat on the ground, its top edge on `y`, read from in
    front: an upright one behind an animal is hidden by it."""
    curve = bpy.data.curves.new(f"label_{text}", "FONT")
    curve.body = text
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "TOP"
    o = bpy.data.objects.new(f"label_{text}", curve)
    o.location = (x, y, 0.0002)
    o.data.materials.append(material("render_label", (0.05, 0.05, 0.06, 1)))
    stage.objects.link(o)
    return o


def lineup(folder):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene, stage, cam = stage_setup(folder)
    roots = {}
    for name in ANIMALS:
        path = os.path.join(PROPS, f"{name}.blend")
        if not os.path.exists(path):
            raise SystemExit(f"wildlife_fliers: {path} is not built yet")
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.collections = ["export"]
        coll = dst.collections[0]
        scene.collection.children.link(coll)
        root = [o for o in coll.all_objects if o.parent is None]
        if len(root) != 1:
            raise SystemExit(f"wildlife_fliers: {name} has {len(root)} root objects, expected one")
        roots[name] = (root[0], meshes(coll.all_objects))
    ground(stage, 4.0)

    def place(root, parts, x, k=1.0):
        root.scale = (k, k, k)
        bpy.context.view_layer.update()
        lo, hi = bounds(parts)
        root.location = Vector(root.location) + Vector((x - (lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
        bpy.context.view_layer.update()
        return bounds(parts)

    def recentre(order, extras):
        lo, hi = bounds([p for n in order for p in roots[n][1]])
        shift = Vector((-(lo.x + hi.x) / 2, 0, 0))
        for n in order:
            roots[n][0].location = Vector(roots[n][0].location) + shift
        for e in extras:
            e.location = Vector(e.location) + shift
        bpy.context.view_layer.update()

    def captions(order, texts, size):
        """One flat caption under each animal, all on one line in front."""
        boxes = {n: bounds(roots[n][1]) for n in order}
        y = min(b[0].y for b in boxes.values()) - 0.004
        return [label(stage, texts[n], (boxes[n][0].x + boxes[n][1].x) / 2, y, size) for n in order], y - size

    # Both lineups are orthographic, from in front and above, so nothing
    # looks bigger for standing nearer the camera.
    view = (0.0, -1.0, 0.7)

    # true relative size, smallest to largest, 20 mm apart
    order = sorted(ANIMALS, key=lambda n: (lambda b: (b[1] - b[0]).length)(bounds(roots[n][1])))
    x = 0.0
    for name in order:
        root, parts = roots[name]
        w = (lambda b: b[1].x - b[0].x)(bounds(parts))
        lo, hi = place(root, parts, x + w / 2)
        x = hi.x + 0.02
    recentre(order, [])
    extras, front = captions(order, {n: n for n in order}, 0.007)
    framed = [p for n in order for p in roots[n][1]]
    bar = ruler(stage, -0.05, front - 0.012)
    shoot(scene, cam, folder, "fliers.png", framed + bar + extras, view, ortho=True)

    # each scaled to the same size: its longest extent 0.12 m
    for o in bar + extras:
        bpy.data.objects.remove(o)
    x, texts = 0.0, {}
    target = 0.12
    for name in order:
        root, parts = roots[name]
        root.scale = (1, 1, 1)
        bpy.context.view_layer.update()
        lo, hi = bounds(parts)
        k = target / max(hi - lo)
        texts[name] = f"{name} x{k:.1f}"
        lo, hi = place(root, parts, 0.0, k)
        lo, hi = place(root, parts, x + (hi.x - lo.x) / 2, k)
        x = hi.x + 0.03
    recentre(order, [])
    extras, _ = captions(order, texts, 0.009)
    shoot(scene, cam, folder, "fliers_enlarged.png", framed + extras, view, ortho=True)


# --- main ------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--lineup" in argv:
        lineup(argv[argv.index("--lineup") + 1])
        return
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in BUILDERS:
        raise SystemExit(f"wildlife_fliers: open one of {', '.join(BUILDERS)}, not {name!r}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"wildlife_fliers: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    POS.clear()
    root = BUILDERS[name]()
    parts = meshes(coll.all_objects)
    ground_and_centre(root, parts)
    ok = report(name, parts)
    if not ok:
        print("wildlife_fliers: a check failed; not saving")
        return
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
