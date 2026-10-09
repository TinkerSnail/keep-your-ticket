"""The drive-in table family and the information panel, a first pass from the
catalog notes (2026-10-02): four props that had only generated Godot scenes
and no photograph of Christina's.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<prop>.blend --python tools/blender/drive_in_tables.py -- \\
        [--replace] [--save] [--render <folder>]

`<prop>` is one of `drive_in_picnic_table_set` (PRP-PARK-020),
`circular_drive_in_picnic_table_set` (PRP-PARK-021),
`granite_circle_picnic_table` (PRP-PARK-022) or
`color_block_information_panel` (PRP-PARK-023). The tool builds whichever the
file is named for into `export`, one object a part, on z = 0 at the origin
facing -Y here (+Z in Godot), at the size and layout of the Godot greybox that
sits locked in `reference`. A part Christina has reshaped by hand is kept: a run
refuses while `export` holds anything, and `--replace` builds over it. Nothing
is saved without `--save`; `--render` writes three-quarter, front, side and top
views, one beside a 1.7 m box for scale, and the greybox from the first two
cameras for comparison. Each part is tagged for `unwrap_parts.py`
(`kyt_unwrap`).

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky tubes and bands, every edge rounded over, few big pieces. No colour here:
the materials are flat stand-ins by surface (painted metal, fabric, stone) for
the painting to replace. Fixings are the family bolt (`family_bolt.py`), 7 mm
proud on a part and 11 mm where a foot is bolted to the ground, each in its
part's paint 15% darker.

**Drive-in set.** Long axis along X. A turquoise perforated-metal top, 1.78 by
0.96 m at 0.77 m, and two attached benches 1.78 by 0.42 m with their tops at
0.51 m, each a thin solid plate inside a rounded band frame (the perforations
are a texture cut-out later, so the plate is solid here). A black tubular frame
of two H trestles at x = +-0.58: a crossbar across under both benches, a leg to
a round foot under each bench, a post up to the top, and a spine between the
two crossbars that holds the umbrella pole in a sleeve. The umbrella: a pole
through a collar in the top, one eight-panel canopy 2.68 m across whose rim
scallops in between the ribs, a straight valance and a ball finial. One canopy
form: the solid red, red/cream panels and sun-faded yellow are paint.
Assumed: the greybox's floating low stretcher at 0.16 m became the spine at
crossbar height, since nothing reached down to it; the canopy keeps the
greybox's spread and apex but its rim is 6 cm lower (2.15 m, the valance to
2.02 m), because the greybox's 14-degree cone read as a lid; no ribs are
modelled under it; bolts show where a bench sits on its leg, where the top
sits on its posts, and two anchors on each foot.

**Circular set.** The same parts round a centre: a round top 1.49 m across with
a rolled tubular rim at 0.77 m, four straight benches 0.92 by 0.42 m centred
1.0 m out on the axes with their tops at 0.51 m, a black centre pedestal that
carries the top and sockets the pole, four radial arms at crossbar height to a
leg and a foot under each bench, and the same umbrella. Assumed: one bolt where
each bench sits on its leg, two anchors a foot; the top is welded to the
pedestal, so none there.

**Granite circle table.** A dark perforated-metal disc 1.84 m across inside a
blue-green rolled rim at 0.79 m on one steel pedestal with a round flange
bolted down by four anchors, and three irregular granite seats, boulders with a
flat sawn top at 0.51 m, where the greybox's blocks stand (north-west,
north-east and south, with the greybox's small turns). Assumed: the boulders'
outlines are a seeded wobble on the greybox blocks' footprints, so each seat
differs; the seats are 1.3 to 1.6 m from the centre as the greybox has them.

**Information panel.** A slim dark frame 1.04 by 1.58 m, 0.11 m deep, standing
0.39 m off the ground on two round posts, with two fields raised 3 cm off its
face: the header, 0.90 by 0.74 m, whose bright colour is swapped per copy, and
the pale information field, 0.90 by 0.38 m, below it. The type bars are paint,
so there are none here. Assumed: no bolts show, since the posts enter the
frame's bottom edge.
"""

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

TAU = math.tau

# colours are stand-ins for the painting, one per surface
TURQUOISE = (0.02, 0.45, 0.47, 1.0)      # the drive-in family's painted metal
BLACK_PAINT = (0.02, 0.022, 0.025, 1.0)  # the tubular frames
FABRIC = (0.80, 0.06, 0.07, 1.0)         # the canopy, the solid red default
DARK_MESH = (0.03, 0.07, 0.075, 1.0)     # the granite table's perforated disc
BLUE_GREEN = (0.04, 0.33, 0.37, 1.0)     # its weathered rim
STEEL = (0.03, 0.045, 0.05, 1.0)         # its pedestal
GRANITE = (0.33, 0.34, 0.36, 1.0)
FRAME_DARK = (0.035, 0.09, 0.12, 1.0)    # the panel's frame and posts
HEADER = (0.02, 0.62, 0.70, 1.0)         # the panel's header, cyan by default
FIELD = (0.78, 0.83, 0.81, 1.0)          # the panel's information field

BEVEL = 0.02
SIDES = 16        # a tube's facets
SEAT_Z = 0.51     # every bench top in this family (the catalog's 0.51 m)
LIP = 0.005       # a rim stands this much proud of the plate inside it
PLATE_T = 0.01    # a perforated plate, solid here
PLATE_LAP = 0.02  # how far a plate runs under its rim


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


def new_object(name, bm, mat, *, bevel=BEVEL, angle=35.0, segments=3, smooth=True, unwrap="facets"):
    """Finish a bmesh into an object in `export`, with its bevel applied."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    export().objects.link(obj)
    obj.data.materials.append(mat)
    obj["kyt_unwrap"] = unwrap
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.harden_normals = False
        apply_modifiers(obj)
    if smooth:
        smooth_by_angle(obj)
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


def circle(centre, radius, sides=SIDES, phase=0.0):
    return [(centre[0] + radius * math.cos(phase + TAU * i / sides),
             centre[1] + radius * math.sin(phase + TAU * i / sides)) for i in range(sides)]


def cylinder_bm(axis, centre, radius, lo, hi, sides=SIDES):
    return prism(circle(centre, radius, sides), axis, lo, hi)


def tube_bm(a, b, radius, sides=SIDES):
    """A round bar from point a to point b, built in place (no object rotation)."""
    a, b = Vector(a), Vector(b)
    axis = b - a
    q = Vector((0, 0, 1)).rotation_difference(axis.normalized())
    bm = cylinder_bm("z", (0, 0), radius, 0.0, axis.length, sides)
    for v in bm.verts:
        v.co = a + q @ v.co
    return bm


def rounded_rect(hx, hy, r, per=4, centre=(0.0, 0.0)):
    """Counter-clockwise, corners first quadrant round."""
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((centre[0] + cx + r * math.cos(a), centre[1] + cy + r * math.sin(a)))
    return pts


def sweep(path, profile):
    """A closed profile swept round a closed plan path: `path` is (x, y) points
    counter-clockwise, `profile` (u, w) points, u outward from the path and w
    up. A torus is a circle swept round a circle; a bench's band frame is a
    rectangle swept round a rounded rectangle. Corners are mitred so the band
    keeps its width."""
    bm = bmesh.new()
    n, m = len(path), len(profile)
    rings = []
    for i in range(n):
        p, a, b = Vector(path[i]), Vector(path[i - 1]), Vector(path[(i + 1) % n])
        t1, t2 = (p - a).normalized(), (b - p).normalized()
        n1, n2 = Vector((t1.y, -t1.x)), Vector((t2.y, -t2.x))
        bis = (n1 + n2).normalized()
        out = bis / max(bis.dot(n1), 0.5)
        rings.append([bm.verts.new((p.x + out.x * u, p.y + out.y * u, w)) for u, w in profile])
    for i in range(n):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for j in range(m):
            bm.faces.new((r0[j], r1[j], r1[(j + 1) % m], r0[(j + 1) % m]))
    return bm


def band_bm(outer_hx, outer_hy, width, z0, z1, corner=None):
    """A rectangular rim: a `width` by (z1 - z0) bar run round a rounded
    rectangle whose outside is 2 outer_hx by 2 outer_hy."""
    corner = width * 0.75 if corner is None else corner   # the band's centre-line radius
    path = rounded_rect(outer_hx - width / 2, outer_hy - width / 2, corner, per=3)
    profile = [(-width / 2, z0), (width / 2, z0), (width / 2, z1), (-width / 2, z1)]
    return sweep(path, profile)


def torus_bm(ring_r, tube_r, z, ring_sides=32, tube_sides=10):
    path = circle((0.0, 0.0), ring_r, ring_sides)
    profile = [(tube_r * math.cos(TAU * j / tube_sides), z + tube_r * math.sin(TAU * j / tube_sides))
               for j in range(tube_sides)]
    return sweep(path, profile)


def lathe_bm(profile, sides=SIDES, scale_by_side=None, centre=(0.0, 0.0)):
    """A closed (r, z) profile turned round the vertical through `centre`.
    Points on the axis (r = 0) merge into one. `scale_by_side` scales the
    radius per facet (the canopy's scalloped rim)."""
    bm = bmesh.new()
    rings = []
    for k in range(sides):
        a = TAU * k / sides
        s = 1.0 if scale_by_side is None else scale_by_side[k % len(scale_by_side)]
        rings.append([bm.verts.new((centre[0] + r * s * math.cos(a), centre[1] + r * s * math.sin(a), z))
                      for r, z in profile])
    m = len(profile)
    for k in range(sides):
        r0, r1 = rings[k], rings[(k + 1) % sides]
        for j in range(m):
            vs = (r0[j], r1[j], r1[(j + 1) % m], r0[(j + 1) % m])
            if len({(round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)) for v in vs}) >= 3:
                bm.faces.new(vs)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return bm


def seat_height_at(points, exclude_prefix="bolt"):
    """Ray down at each (x, y) onto everything in `export` but the bolts, so
    the checks measure the emitted seats, not the constants."""
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in export().objects:
        if o.type != "MESH" or o.name.startswith(exclude_prefix):
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in me.vertices]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)
    out = []
    for x, y in points:
        # from below the canopy, so the ray finds the seat and not the umbrella
        hit = bvh.ray_cast(Vector((x, y, 1.2)), Vector((0, 0, -1)), 2.0)
        out.append(hit[0].z if hit[0] is not None else float("nan"))
    return out


def bounds():
    pts = [o.matrix_world @ Vector(c) for o in export().objects if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def bolts():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import family_bolt
    return family_bolt


# --- the shared pieces: perforated panels, tubular frames, the umbrella ---------

def rect_panel(tag, cx, cy, hx, hy, top, band_w, band_h, mat):
    """A perforated panel in a rounded band frame centred at (cx, cy): the
    band's top at `top`, the solid plate a lip below it, lapping under the
    band."""
    band = new_object(f"{tag}_rim", shift(band_bm(hx, hy, band_w, top - band_h, top), cx, cy), mat, bevel=0.02, segments=2)
    plate_poly = rounded_rect(hx - band_w + PLATE_LAP, hy - band_w + PLATE_LAP, 0.02, centre=(cx, cy))
    plate = new_object(f"{tag}_plate", prism(plate_poly, "z", top - LIP - PLATE_T, top - LIP), mat,
                       bevel=0, smooth=False, unwrap="planar")
    return band, plate


def shift(bm, dx, dy, dz=0.0):
    for v in bm.verts:
        v.co.x += dx
        v.co.y += dy
        v.co.z += dz
    return bm


def round_plate_top(ring_z, tube_r):
    """A round top's plate sits a little above its rolled rim's centre line,
    as the greybox discs do, so the rim rolls up past it."""
    return ring_z + 0.4 * tube_r


def round_panel(tag, radius, ring_z, tube_r, rim_mat, plate_mat, ring_sides=32):
    """A perforated disc in a rolled tubular rim `radius` to its outside, the
    tube's centre line at `ring_z`."""
    ring_r = radius - tube_r
    rim = new_object(f"{tag}_rim", torus_bm(ring_r, tube_r, ring_z, ring_sides), rim_mat,
                     bevel=0, unwrap="lathe")
    top = round_plate_top(ring_z, tube_r)
    plate = new_object(f"{tag}_plate", cylinder_bm("z", (0, 0), ring_r + PLATE_LAP, top - PLATE_T, top, ring_sides),
                       plate_mat, bevel=0, smooth=False, unwrap="planar")
    return rim, plate


FOOT_R, FOOT_H = 0.13, 0.05


def foot(tag, x, y, mat, anchors_along, fb):
    """A round foot plate with two family bolts anchoring it to the ground,
    set either side of the leg along `anchors_along` (a unit plan vector)."""
    prof = [(0.0, 0.0), (FOOT_R, 0.0), (FOOT_R, FOOT_H - 0.022), (FOOT_R - 0.008, FOOT_H - 0.006),
            (FOOT_R - 0.024, FOOT_H), (0.0, FOOT_H)]
    plate = new_object(f"foot_{tag}", lathe_bm(prof, SIDES, centre=(x, y)), mat, bevel=0, unwrap="lathe")
    paint = fb.paint_of(mat)
    for k, s in enumerate((-1.0, 1.0)):
        fb.place(export(), f"bolt_foot_{tag}_{k}",
                 Vector((x + s * 0.09 * anchors_along[0], y + s * 0.09 * anchors_along[1], FOOT_H)),
                 (0, 0, 1), ground=True, against=[plate], material=paint)
    return plate


LEG_R, BAR_R, POST_R, POLE_R = 0.065, 0.06, 0.06, 0.04
BAR_Z = 0.40                    # the crossbars' and arms' centre line
# The canopy keeps the greybox's spread and apex; its rim is 6 cm lower than
# the greybox's flat cone, for a rise that reads as an umbrella and not a lid.
CANOPY_R, CANOPY_RIM_Z, CANOPY_APEX_Z, VALANCE = 1.34, 2.15, 2.55, 0.13
CANOPY_PANELS, CANOPY_PER_PANEL = 8, 4
POLE_TOP = 2.60                 # the pole ends inside the finial
FINIAL_R = 0.085


def umbrella(top_z, pole_from, black, fabric):
    """The pole from `pole_from` up through a collar on the top at `top_z`,
    one canopy and a ball finial."""
    new_object("pole", cylinder_bm("z", (0, 0), POLE_R, pole_from, POLE_TOP), black, bevel=0.01, segments=1, unwrap="lathe")
    collar = [(POLE_R + 0.004, top_z), (POLE_R + 0.045, top_z), (POLE_R + 0.045, top_z + 0.038),
              (POLE_R + 0.03, top_z + 0.052), (POLE_R + 0.004, top_z + 0.055)]
    new_object("pole_collar", lathe_bm(collar, SIDES), black, bevel=0, unwrap="lathe")

    # The canopy: a softly convex cone, z = rim + rise * (1 - (r/R)^1.35), 2 cm
    # of cloth, a straight valance hanging from the rim, and the rim drawn in
    # 6% between the ribs, so eight scalloped panels read with no ribs modelled.
    rise = CANOPY_APEX_Z - CANOPY_RIM_Z

    def dome(r, drop=0.0):
        return CANOPY_RIM_Z + rise * (1.0 - (r / CANOPY_R) ** 1.35) - drop

    outer = [(r, dome(r)) for r in (0.0, 0.45, 0.85, 1.15, CANOPY_R)]
    skirt = [(CANOPY_R + 0.01, CANOPY_RIM_Z - VALANCE), (CANOPY_R - 0.01, CANOPY_RIM_Z - VALANCE),
             (CANOPY_R - 0.02, CANOPY_RIM_Z - 0.01)]
    inner = [(r, dome(r, 0.02)) for r in (1.15, 0.85, 0.45, 0.0)]
    scallop = [1.0 - 0.06 * math.sin(math.pi * k / CANOPY_PER_PANEL) for k in range(CANOPY_PER_PANEL)]
    new_object("canopy", lathe_bm(outer + skirt + inner, CANOPY_PANELS * CANOPY_PER_PANEL, scale_by_side=scallop),
               fabric, bevel=0, unwrap="lathe")

    zc = CANOPY_APEX_Z + FINIAL_R - 0.01
    ball = [(FINIAL_R * math.sin(math.radians(a)), zc - FINIAL_R * math.cos(math.radians(a))) for a in range(0, 181, 22)]
    new_object("finial", lathe_bm(ball, SIDES), fabric, bevel=0, unwrap="lathe")


# --- the drive-in set ----------------------------------------------------------

TOP_HX, TOP_HY, TOP_Z = 0.89, 0.48, 0.775      # the top's rim: 1.78 by 0.96 m, its top face
BENCH_HX, BENCH_HY, BENCH_Y = 0.89, 0.21, 0.79   # a bench 1.78 by 0.42 m, centred 0.79 m out
TRESTLE_X = 0.58
BAND_TOP, BAND_BENCH = 0.08, 0.07


def build_drive_in():
    turquoise = material("paint_turquoise", TURQUOISE)
    black = material("paint_black", BLACK_PAINT)
    fabric = material("umbrella_fabric", FABRIC)
    fb = bolts()

    rect_panel("top", 0.0, 0.0, TOP_HX, TOP_HY, TOP_Z, BAND_TOP, BAND_TOP, turquoise)
    benches = {}
    for tag, sy in (("front", -1.0), ("back", 1.0)):
        benches[tag] = rect_panel(f"bench_{tag}", 0.0, sy * BENCH_Y, BENCH_HX, BENCH_HY,
                                  SEAT_Z + LIP, BAND_BENCH, 0.075, turquoise)

    # Two H trestles: crossbar under both benches, legs to feet, post to the top.
    bar_end = BENCH_Y + BENCH_HY - 0.05
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        x = sx * TRESTLE_X
        new_object(f"crossbar_{tag}", tube_bm((x, -bar_end, BAR_Z), (x, bar_end, BAR_Z), BAR_R), black,
                   bevel=0.012, segments=1, unwrap="lathe")
        new_object(f"post_{tag}", cylinder_bm("z", (x, 0.0), POST_R, BAR_Z, TOP_Z - LIP - PLATE_T + 0.005), black,
                   bevel=0.01, segments=1, unwrap="lathe")
        for btag, sy in (("front", -1.0), ("back", 1.0)):
            y = sy * BENCH_Y
            new_object(f"leg_{tag}_{btag}", cylinder_bm("z", (x, y), LEG_R, FOOT_H - 0.02, SEAT_Z - PLATE_T + 0.005), black,
                       bevel=0.01, segments=1, unwrap="lathe")
            foot(f"{tag}_{btag}", x, y, black, (1.0, 0.0), fb)
    # the spine between the crossbars, with the pole's sleeve in its middle
    new_object("spine", tube_bm((-TRESTLE_X, 0.0, BAR_Z), (TRESTLE_X, 0.0, BAR_Z), 0.05), black,
               bevel=0.012, segments=1, unwrap="lathe")
    sleeve = [(POLE_R + 0.004, BAR_Z - 0.09), (POLE_R + 0.016, BAR_Z - 0.086), (POLE_R + 0.02, BAR_Z - 0.08),
              (POLE_R + 0.02, BAR_Z + 0.08), (POLE_R + 0.016, BAR_Z + 0.086), (POLE_R + 0.004, BAR_Z + 0.09)]
    new_object("pole_sleeve", lathe_bm(sleeve, SIDES), black, bevel=0, unwrap="lathe")
    umbrella(TOP_Z, 0.0, black, fabric)

    # bolts: a bench on its leg, the top on its posts
    paint = fb.paint_of(turquoise)
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        for btag, sy in (("front", -1.0), ("back", 1.0)):
            fb.place(export(), f"bolt_bench_{btag}_{tag}", Vector((sx * TRESTLE_X, sy * BENCH_Y, SEAT_Z)),
                     (0, 0, 1), against=[benches[btag][1]], material=paint)
        fb.place(export(), f"bolt_top_{tag}", Vector((sx * TRESTLE_X, 0.0, TOP_Z - LIP)), (0, 0, 1),
                 against=[bpy.data.objects["top_plate"]], material=paint)


def checks_drive_in():
    seats = seat_height_at([(0.0, -BENCH_Y), (0.0, BENCH_Y), (0.45, -BENCH_Y), (-0.45, BENCH_Y)])
    lo, hi = bounds()
    return [
        f"size {hi.x - lo.x:.2f} by {hi.y - lo.y:.2f} by {hi.z - lo.z:.2f} m; table {2 * TOP_HX:.2f} by {2 * TOP_HY:.2f} m "
        f"at {TOP_Z - LIP:.3f} m, benches to y = +-{BENCH_Y + BENCH_HY:.2f}",
        "seat tops measured: " + ", ".join(f"{z:.3f}" for z in seats) + f" m (want {SEAT_Z:.2f})",
        f"canopy {2 * CANOPY_R:.2f} m across, rim {CANOPY_RIM_Z - VALANCE:.2f} to {CANOPY_RIM_Z:.2f} m, apex {CANOPY_APEX_Z:.2f} m",
    ]


# --- the circular set ------------------------------------------------------------

ROUND_R, ROUND_RING_Z, ROUND_TUBE = 0.745, 0.745, 0.045   # the rolled rim's outside, its centre line, its tube
CBENCH_HX, CBENCH_HY, CBENCH_D = 0.46, 0.21, 1.0        # a bench 0.92 by 0.42 m, 1.0 m out
PEDESTAL_R = 0.11
AXES = (("front", (0.0, -1.0)), ("back", (0.0, 1.0)), ("right", (1.0, 0.0)), ("left", (-1.0, 0.0)))


def build_circular():
    turquoise = material("paint_turquoise", TURQUOISE)
    black = material("paint_black", BLACK_PAINT)
    fabric = material("umbrella_fabric", FABRIC)
    fb = bolts()

    round_panel("top", ROUND_R, ROUND_RING_Z, ROUND_TUBE, turquoise, turquoise)
    plate_top = round_plate_top(ROUND_RING_Z, ROUND_TUBE)
    plate_under = plate_top - PLATE_T
    pedestal = [(0.0, 0.0), (0.15, 0.0), (0.15, 0.025), (0.14, 0.035), (PEDESTAL_R, 0.06), (PEDESTAL_R, plate_under - 0.05),
                (0.19, plate_under - 0.024), (0.20, plate_under - 0.012), (0.20, plate_under + 0.004),
                (0.0, plate_under + 0.004)]
    new_object("pedestal", lathe_bm(pedestal, SIDES), black, bevel=0, unwrap="lathe")

    plates = {}
    for tag, (dx, dy) in AXES:
        cx, cy = dx * CBENCH_D, dy * CBENCH_D
        hx, hy = (CBENCH_HX, CBENCH_HY) if dx == 0 else (CBENCH_HY, CBENCH_HX)
        plates[tag] = rect_panel(f"bench_{tag}", cx, cy, hx, hy, SEAT_Z + LIP, BAND_BENCH, 0.075, turquoise)[1]
        new_object(f"arm_{tag}", tube_bm((dx * (PEDESTAL_R - 0.02), dy * (PEDESTAL_R - 0.02), BAR_Z),
                                         (dx * (CBENCH_D + 0.05), dy * (CBENCH_D + 0.05), BAR_Z), 0.05), black,
                   bevel=0.012, segments=1, unwrap="lathe")
        new_object(f"leg_{tag}", cylinder_bm("z", (cx, cy), LEG_R, FOOT_H - 0.02, SEAT_Z - PLATE_T + 0.005), black,
                   bevel=0.01, segments=1, unwrap="lathe")
        foot(tag, cx, cy, black, (dy, dx), fb)   # anchors across the arm's line
    umbrella(plate_top, 0.5, black, fabric)

    paint = fb.paint_of(turquoise)
    for tag, (dx, dy) in AXES:
        fb.place(export(), f"bolt_bench_{tag}", Vector((dx * CBENCH_D, dy * CBENCH_D, SEAT_Z)), (0, 0, 1),
                 against=[plates[tag]], material=paint)


def checks_circular():
    pts = [(dx * CBENCH_D + dy * 0.2, dy * CBENCH_D + dx * 0.2) for _, (dx, dy) in AXES]
    seats = seat_height_at(pts)
    lo, hi = bounds()
    return [
        f"size {hi.x - lo.x:.2f} by {hi.y - lo.y:.2f} by {hi.z - lo.z:.2f} m; top {2 * ROUND_R:.2f} m across, plate at "
        f"{round_plate_top(ROUND_RING_Z, ROUND_TUBE):.3f} m, rim to {ROUND_RING_Z + ROUND_TUBE:.3f} m, "
        f"benches from {CBENCH_D - CBENCH_HY:.2f} to {CBENCH_D + CBENCH_HY:.2f} m out",
        "seat tops measured (beside the bolt): " + ", ".join(f"{z:.3f}" for z in seats) + f" m (want {SEAT_Z:.2f})",
    ]


# --- the granite circle table --------------------------------------------------------

G_R, G_RING_Z, G_TUBE = 0.985, 0.77, 0.06   # the rolled rim's outside, its centre line, its tube
# the greybox's three blocks: centre, half sizes, yaw (Godot's turn about up is the
# same turn about Blender's Z), with the seat's top at SEAT_Z
G_SEATS = (("northwest", (-1.05, 0.72), (0.375, 0.29), -0.13),
           ("northeast", (1.07, 0.68), (0.355, 0.31), 0.18),
           ("south", (0.03, -1.28), (0.385, 0.295), -0.08))


def boulder_bm(seed, centre, half, yaw):
    """A rough block with a flat sawn top: a wobbled eight-sided outline in
    plan, lofted through a few rings so the sides lean in a little toward the
    foot and the top, each ring turned and wobbled on its own so the facets
    are irregular, then softened by a small bevel. Stone, not a cushion: few
    big facets, edges only just rounded."""
    rng = random.Random(seed)
    n = 8

    def outline(scale, spin):
        pts = []
        for i in range(n):
            a = TAU * i / n + spin + math.radians(rng.uniform(-7.0, 7.0))
            r = half[0] * half[1] / math.hypot(half[1] * math.cos(a), half[0] * math.sin(a))
            r *= scale * (1.0 + rng.uniform(-0.10, 0.10))
            pts.append((r * math.cos(a), r * math.sin(a)))
        return pts

    levels = ((0.0, 0.90), (0.16, 1.0), (0.38, 0.99), (SEAT_Z, 0.90))
    bm = bmesh.new()
    rot = Matrix.Rotation(yaw, 2)
    rings = []
    for z, s in levels:
        ring = []
        for x, y in outline(s, math.radians(rng.uniform(-4.0, 4.0))):
            p = rot @ Vector((x, y))
            ring.append(bm.verts.new((centre[0] + p.x, centre[1] + p.y, z)))
        rings.append(ring)
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
    return bm


def build_granite():
    mesh_mat = material("perforated_dark", DARK_MESH)
    rim_mat = material("paint_blue_green", BLUE_GREEN)
    steel = material("steel_dark", STEEL)
    granite = material("granite", GRANITE)
    fb = bolts()

    round_panel("top", G_R, G_RING_Z, G_TUBE, rim_mat, mesh_mat, ring_sides=36)
    plate_under = round_plate_top(G_RING_Z, G_TUBE) - PLATE_T
    pedestal = [(0.0, 0.0), (0.30, 0.0), (0.30, 0.03), (0.29, 0.04), (0.26, 0.06), (0.19, 0.08), (0.19, 0.12),
                (0.13, 0.55), (0.13, plate_under - 0.07), (0.27, plate_under - 0.045), (0.28, plate_under - 0.03),
                (0.28, plate_under + 0.004), (0.0, plate_under + 0.004)]
    flange = new_object("pedestal", lathe_bm(pedestal, 20), steel, bevel=0, unwrap="lathe")
    paint = fb.paint_of(steel)
    for k in range(4):
        a = math.radians(45.0 + 90.0 * k)
        fb.place(export(), f"bolt_flange_{k}", Vector((0.245 * math.cos(a), 0.245 * math.sin(a), 0.035)),
                 (0, 0, 1), ground=True, against=[flange], material=paint)
    for k, (tag, centre, half, yaw) in enumerate(G_SEATS):
        new_object(f"seat_{tag}", boulder_bm(22 + k, centre, half, yaw), granite, bevel=0.022, angle=20.0, segments=1)


def checks_granite():
    seats = seat_height_at([c for _, c, _, _ in G_SEATS])
    lo, hi = bounds()
    plate_top = round_plate_top(G_RING_Z, G_TUBE)
    return [
        f"size {hi.x - lo.x:.2f} by {hi.y - lo.y:.2f} by {hi.z - lo.z:.2f} m; top {2 * G_R:.2f} m across, "
        f"disc at {plate_top:.3f} m, rim to {G_RING_Z + G_TUBE:.2f} m",
        "seat tops measured: " + ", ".join(f"{t}: {z:.3f}" for (t, _, _, _), z in zip(G_SEATS, seats)) + f" m (want {SEAT_Z:.2f})",
        f"under the top: {plate_top - PLATE_T - 0.07:.2f} m to the spreader's underside, the pedestal 0.26 m wide at the waist",
    ]


# --- the information panel ------------------------------------------------------------

P_HX, P_HZ, P_ZC, P_DEPTH = 0.52, 0.79, 1.18, 0.11
P_FIELD_PROUD = 0.03
P_POST_X, P_POST_R = 0.36, 0.055


def build_panel():
    frame_mat = material("paint_frame_dark", FRAME_DARK)
    header_mat = material("paint_header", HEADER)
    field_mat = material("paint_field_pale", FIELD)

    face = -P_DEPTH / 2
    new_object("frame", prism(rounded_rect(P_HX, P_HZ, 0.06, per=6, centre=(0.0, P_ZC)), "y", face, -face),
               frame_mat, bevel=0.03)
    for name, hz, zc, mat in (("header_field", 0.37, 1.48, header_mat), ("information_field", 0.19, 0.89, field_mat)):
        new_object(name, prism(rounded_rect(0.45, hz, 0.03, per=4, centre=(0.0, zc)), "y", face - P_FIELD_PROUD, face + 0.01),
                   mat, bevel=0.01, segments=2)
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        new_object(f"post_{tag}", cylinder_bm("z", (sx * P_POST_X, 0.0), P_POST_R, 0.0, P_ZC - P_HZ + 0.03),
                   frame_mat, bevel=0.01, segments=2, unwrap="lathe")


def checks_panel():
    lo, hi = bounds()
    return [
        f"size {hi.x - lo.x:.2f} by {hi.y - lo.y:.2f} by {hi.z - lo.z:.2f} m; frame {2 * P_HX:.2f} by {2 * P_HZ:.2f} m "
        f"from {P_ZC - P_HZ:.2f} to {P_ZC + P_HZ:.2f} m, fields {P_FIELD_PROUD * 100:.0f} cm proud of its face",
    ]


# --- the file -----------------------------------------------------------------------

def render(folder, name):
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("render_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    scene.world = world
    # ground, a sun and the camera, linked to the scene itself, never to export
    ground_me = bpy.data.meshes.new("render_ground")
    ground_me.from_pydata([(-20, -20, -0.001), (20, -20, -0.001), (20, 20, -0.001), (-20, 20, -0.001)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("render_ground", ground_me)
    ground.data.materials.append(material("render_ground", (0.55, 0.52, 0.46, 1)))
    scene.collection.objects.link(ground)
    sun = bpy.data.objects.new("render_sun", bpy.data.lights.new("render_sun", "SUN"))
    sun.data.energy = 2.2
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    scene.collection.objects.link(sun)
    cam = bpy.data.objects.new("render_cam", bpy.data.cameras.new("render_cam"))
    cam.data.lens = 40
    scene.collection.objects.link(cam)
    scene.camera = cam

    from bpy_extras.object_utils import world_to_camera_view

    lo, hi = bounds()
    centre = (lo + hi) / 2
    size = (hi - lo).length

    def corners(a, b):
        return [Vector((x, y, z)) for x in (a.x, b.x) for y in (a.y, b.y) for z in (a.z, b.z)]

    def shoot(tag, direction, boxes, aim=None):
        d = Vector(direction).normalized()
        pts = [c for a, b in boxes for c in corners(a, b)]
        target = aim or sum((Vector(c) for c in pts), Vector()) / len(pts)
        dist = size
        while dist < 60.0:
            cam.location = target + d * dist
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            if all(0.05 <= c.x <= 0.95 and 0.05 <= c.y <= 0.95 for c in (world_to_camera_view(scene, cam, p) for p in pts)):
                break
            dist *= 1.08
        scene.render.filepath = os.path.join(folder, f"{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)

    prop = [(lo, hi)]
    views = {"three_quarter": (0.8, -1.0, 0.55), "front": (0.0, -1.0, 0.2), "side": (1.0, 0.0, 0.2),
             "top": (0.0, -0.001, 1.0)}
    for tag, direction in views.items():
        shoot(tag, direction, prop)
    # beside a 1.7 m box, a person's height
    bx = hi.x + 0.6
    box = bpy.data.objects.new("render_scale_box",
                               bpy.data.meshes.new("render_scale_box"))
    bm = prism(rounded_rect(0.2, 0.125, 0.04), "z", 0.0, 1.7)
    shift(bm, bx, 0.0)
    bm.to_mesh(box.data)
    bm.free()
    box.data.materials.append(material("render_scale", (0.9, 0.88, 0.8, 1)))
    scene.collection.objects.link(box)
    shoot("scale", views["three_quarter"], prop + [(Vector((bx - 0.2, -0.125, 0.0)), Vector((bx + 0.2, 0.125, 1.7)))])
    bpy.data.objects.remove(box)
    # the greybox from the same two cameras, for comparison
    reference = bpy.data.collections.get("reference")
    if reference is not None:
        reference.hide_render = False
        for o in export().objects:
            o.hide_render = True
        for tag in ("three_quarter", "front"):
            shoot(f"greybox_{tag}", views[tag], prop)
        for o in export().objects:
            o.hide_render = False
        reference.hide_render = True


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    builders = {"drive_in_picnic_table_set": (build_drive_in, checks_drive_in),
                "circular_drive_in_picnic_table_set": (build_circular, checks_circular),
                "granite_circle_picnic_table": (build_granite, checks_granite),
                "color_block_information_panel": (build_panel, checks_panel)}
    if name not in builders:
        raise SystemExit(f"drive_in_tables: open one of {', '.join(builders)}, not {name}")
    coll = export()
    if coll.objects:
        if "--replace" not in argv:
            raise SystemExit(f"drive_in_tables: export already holds {[o.name for o in coll.objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.objects):
            bpy.data.objects.remove(o)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    build, check = builders[name]
    build()
    total = 0
    rows = []
    for o in coll.objects:
        o.data.calc_loop_triangles()
        t = len(o.data.loop_triangles)
        total += t
        rows.append((t, o.name))
    print(f"drive_in_tables: {name}: {len(coll.objects)} parts, {total} triangles")
    for t, n in sorted(rows, reverse=True)[:12]:
        print(f"  {t:5d}  {n}")
    for line in check():
        print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
