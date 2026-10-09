"""The park's two concrete picnic tables, modelled from her photographs
(2026-10-01).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<prop>.blend --python tools/blender/picnic_tables.py -- \
        [--replace] [--save] [--render <folder>]

`<prop>` is `concrete_picnic_table` (PRP-PARK-028, the trestle table,
`documentation/reference/concrete_picnic_table/`) or `round_picnic_table`
(PRP-PARK-029, the round café table, `.../round_picnic_table/`); the tool builds
whichever the file is named for, into `export`, one object a part, on z = 0 at
the origin facing -Y here (+Z in Godot). Once a table has a game mesh, its
parts live in `<prop>_source.blend`: run this there, then Rebuild game mesh.
Each part is tagged for `unwrap_parts.py` (`kyt_unwrap`).

**Trestle table.** Long axis along X. Two heavy cast trestles set in from the
top's ends, each a footing with horns, a slender waist between the
photograph's two round cut-outs and a brass disc, a thick softly rounded top
on them, and on each long side one bench of three timber slats as long as the
top, its ends flush with the top's, running past both trestles, lying on the
horns and bolted to them. Measured off the photo; see the trestle constants.

**Round table.** One round top on a pedestal that is a flat-faced wall along X
(flat for the medallion) rising to a waisted column with the photograph's small
round hole through it, and two crescent benches, thick curved slabs concentric
with the top, cast into the pedestal's foot on opposite sides (left and right,
along X). The other two sides, front and back, are open.

**The space for wheelchairs** (her note: both tables have it, the trestle one by
the way it is built, the round one by deliberate design) is measured against the
usual accessible figures, which are a check and not hers: knee room under the top
at least 0.69 m high, 0.76 m wide and 0.48 m deep, and a clear floor space at the
open sides. The checks print the numbers. The round table meets them; the
trestle table, built as the photograph, does not (its long sides carry the
benches, and at its ends knees reach only 0.21 m under the top before the
trestle), which is her call to make.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, every edge rounded over. No colour here: the materials are flat
stand-ins, the aggregate, the stained timber and a brass-coloured disc, for the
painting to replace. A part Christina has reshaped by hand is kept: a run
refuses while `export` holds anything, and `--replace` builds over it.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAU = math.tau

# colours are stand-ins for the painting
AGGREGATE = (0.62, 0.55, 0.45, 1.0)
TIMBER = (0.13, 0.065, 0.04, 1.0)
BRASS = (0.62, 0.48, 0.18, 1.0)
EMBLEM = (0.16, 0.34, 0.24, 1.0)

BEVEL = 0.03


# --- building blocks -------------------------------------------------------

def material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = colour
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    return mat


def new_object(name, bm, mat, *, bevel=BEVEL, angle=35.0, smooth=True):
    """Finish a bmesh into an object in `export`, with its bevel applied."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections["export"].objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.harden_normals = False
        apply_modifiers(obj)
    clean(obj)
    if smooth:
        smooth_by_angle(obj)
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


def cylinder_bm(axis, centre, radius, lo, hi, sides=40):
    poly = [(centre[0] + radius * math.cos(TAU * i / sides),
             centre[1] + radius * math.sin(TAU * i / sides)) for i in range(sides)]
    return prism(poly, axis, lo, hi)


def subtract(obj_bm_pairs, cutters, name, mat, **kw):
    """Cut `cutters` (bmeshes) out of the shape `obj_bm_pairs` and finish it."""
    base = new_object(name, obj_bm_pairs, mat, bevel=0, smooth=False)
    for i, cb in enumerate(cutters):
        cut = new_object(f"{name}_cut{i}", cb, mat, bevel=0, smooth=False)
        mod = base.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        mod.solver = "EXACT"
        apply_modifiers(base)
        bpy.data.objects.remove(cut)
    # the bevel last, on the cut shape
    mod = base.modifiers.new("bevel", "BEVEL")
    mod.width = kw.get("bevel", BEVEL)
    mod.segments = 3
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(35)
    apply_modifiers(base)
    clean(base)
    smooth_by_angle(base)
    return base


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


def rounded_rect(hx, hy, r, per=6):
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sector(r_in, r_out, a0, a1, per_deg=4.0, end_round=0.0):
    """An annular sector in plan, from angle a0 to a1 (degrees)."""
    n = max(4, int(abs(a1 - a0) / per_deg))
    outer = [(r_out * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
              r_out * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    inner = [(r_in * math.cos(math.radians(a1 - (a1 - a0) * i / n)),
              r_in * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return outer + inner


def disc(name, mat, centre, normal_axis, radius, thickness, sign=1.0):
    """A thin round plaque lying on a face: its back at `centre`."""
    bm = cylinder_bm({"x": "x", "y": "y", "z": "z"}[normal_axis], (0, 0), radius, 0.0, thickness, 32)
    obj = new_object(name, bm, mat, bevel=0.003, smooth=True)
    return obj


# --- the trestle table -------------------------------------------------------
#
# Measured off her photograph (documentation/reference/concrete_picnic_table/)
# by solving the camera and the table together from 27 points read off it (the
# top's corners, the trestle's disc, feet and round cut-outs, the benches' ends
# and bolt lines), scaled so the top stands at TOP_Z: the top about 1.94 m by
# 0.74 m; two trestles set in about 0.2 m from its ends, each a footing with
# horns, a slender waist between two round cut-outs and a brass disc; and on
# each long side one bench of three timber slats AS LONG AS THE TOP, its ends
# flush with the top's, so it runs past each trestle by about 0.18 m, lying on
# the horns with a bolt through each slat into each horn. (The first pass built
# short stubs across the horns; the second ended the benches inside the
# trestles under a longer top. Both were misreadings.)

TOP_X, TOP_Y = 0.97 + 0.08, 0.37   # the top's half length and half width: the photo's
                                   # 0.97, 3 in longer at each end (her word, 2 Oct 2026)
TOP_Z = 0.79                  # its upper face: wheelchair knee room under it
TOP_T = 0.09
TRESTLE_X = 0.64 - 0.08       # a trestle's centre from the middle, along X: the photo's
                              # 0.64, brought 3 in toward the middle (her word, 2 Oct 2026)
TRESTLE_T = 0.24              # its thickness along X
FOOT_Y = 0.59                 # the footing's half width on the ground
HORN_Y = 0.79                 # and at the horn tip, where the bench lies
SHELF_Z = 0.40                # the horn's flat top, the bench's underside
SCOOP_Y, SCOOP_Z, SCOOP_R = 0.27, 0.43, 0.21   # the round cut-outs
BENCH_Y = 0.63                # a bench's centre line from the middle line
BENCH_X = 0.97                # its half length: the photo's, flush with the photo's top
SLAT_W, SLAT_GAP, SLAT_T = 0.095, 0.012, 0.05
BENCH_W = 3 * SLAT_W + 2 * SLAT_GAP
FLANK_Y = BENCH_Y - BENCH_W / 2 - 0.01   # the column's edge at the bench, just inside it
SEAT_Z = SHELF_Z + SLAT_T     # the benches' upper face
UNDER_Z = TOP_Z - TOP_T       # the top's underside, where a trestle meets it
# The trestles lean: tops stay where they are, feet set in toward the middle,
# far enough that at each end the top overhangs a foot by 0.48 m at the floor,
# room for a wheelchair's footrests and toes; at knee height the room is what
# the top's overhang of the trestle's top gives. A shear, so the trestle's top
# stays flat to the underside and its foot flat on the ground (her word, 2 Oct
# 2026: "feet move in, tops stay where they are").
FEET_IN = 0.48 - (TOP_X - TRESTLE_X - TRESTLE_T / 2)


def lean(sx, z):
    """How far a trestle's section at height z is set in toward the middle."""
    return -sx * FEET_IN * (1.0 - z / UNDER_Z)


def trestle_outline():
    """The trestle in section across the table, (y, z): a footing with feet
    and horns, the horn's flat top the bench lies on, the column's flank, and
    the flare into the top. The round cut-outs are taken out after."""
    under = TOP_Z - TOP_T + 0.01
    half = [(0.20, 0.0), (0.26, 0.04), (0.42, 0.04), (0.48, 0.0), (FOOT_Y, 0.0),
            (0.66, 0.16), (0.74, 0.30), (HORN_Y, SHELF_Z), (FLANK_Y, SHELF_Z),
            (FLANK_Y, SHELF_Z + 0.07), (TOP_Y - 0.02, under)]
    return [(-y, z) for y, z in reversed(half)] + half


def build_trestle_table():
    agg = material("picnic_aggregate", AGGREGATE)
    wood = material("picnic_timber", TIMBER)
    brass = material("picnic_brass", BRASS)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import family_bolt

    # the top: a thick, rounded slab
    bm = prism(rounded_rect(TOP_X, TOP_Y, 0.10), "z", TOP_Z - TOP_T, TOP_Z)
    new_object("top", bm, agg, bevel=0.03)

    for side, sx in (("l", -1.0), ("r", 1.0)):
        x0, x1 = sx * TRESTLE_X - TRESTLE_T / 2, sx * TRESTLE_X + TRESTLE_T / 2
        cuts = [cylinder_bm("x", (cy, SCOOP_Z), SCOOP_R, x0 - 0.05, x1 + 0.05) for cy in (-SCOOP_Y, SCOOP_Y)]
        trestle = subtract(prism(trestle_outline(), "x", x0, x1), cuts, f"trestle_{side}", agg, bevel=0.03)
        for v in trestle.data.vertices:
            v.co.x += lean(sx, v.co.z)
        trestle.data.update()
        clean(trestle)

        # the brass disc on the trestle's outer face, low on the column, lying
        # on the leaning face: its axis along the face's outward normal
        z = 0.20
        normal = Vector((sx, 0.0, -FEET_IN / UNDER_Z)).normalized()
        d = disc(f"plaque_{side}", brass, (0, 0, 0), "x", 0.045, 0.012)
        d.rotation_mode = "QUATERNION"
        d.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(normal)
        d.location = Vector((sx * (TRESTLE_X + TRESTLE_T / 2) + lean(sx, z), 0.0, z)) - normal * 0.003

    # the benches: three slats each, along the table, on the horns
    pitch = SLAT_W + SLAT_GAP
    slats = []
    for sy, tag in ((-1.0, "f"), (1.0, "b")):
        for i, k in enumerate((-1, 0, 1)):
            yc = sy * BENCH_Y + k * pitch
            bm = prism([(yc - SLAT_W / 2, SHELF_Z), (yc + SLAT_W / 2, SHELF_Z),
                        (yc + SLAT_W / 2, SEAT_Z), (yc - SLAT_W / 2, SEAT_Z)], "x", -BENCH_X, BENCH_X)
            slats.append((new_object(f"slat_{tag}_{i}", bm, wood, bevel=0.014, smooth=True), yc))
    # a family bolt through each slat into each horn
    export = bpy.data.collections["export"]
    for o, yc in slats:
        for sx in (-1.0, 1.0):
            family_bolt.place(export, f"bolt_{o.name[5:]}_{'l' if sx < 0 else 'r'}",
                              Vector((sx * TRESTLE_X + lean(sx, SHELF_Z), yc, SEAT_Z)), (0, 0, 1), against=[o])


def checks_trestle():
    gap = 2 * (BENCH_Y - BENCH_W / 2)
    face = TRESTLE_X + TRESTLE_T / 2

    def depth(z):
        return TOP_X - (face + lean(1.0, z))
    return [
        f"under the top: {UNDER_Z:.2f} m high (need 0.69); between the trestles "
        f"{2 * (TRESTLE_X - TRESTLE_T / 2):.2f} m at the top, {2 * (TRESTLE_X - TRESTLE_T / 2 - FEET_IN):.2f} m at the feet",
        f"at each end: {gap:.2f} m clear between the bench ends (need 0.76); under the top before the trestle: "
        f"{depth(0.0):.2f} m at the floor, {depth(0.23):.2f} m at 0.23 m (toes), {depth(UNDER_Z - 0.01):.2f} m at knee height",
        f"trestles lean {math.degrees(math.atan2(FEET_IN, UNDER_Z)):.1f} deg, feet {FEET_IN:.2f} m in; top {2 * TOP_X:.2f} by "
        f"{2 * TOP_Y:.2f} m at {TOP_Z:.2f} m, seat {SEAT_Z:.2f} m, bench {2 * BENCH_X:.2f} m long, {BENCH_W:.2f} m wide",
    ]


# --- the round table ---------------------------------------------------------

R_TOP = 0.66
R_TOP_Z = 0.80
R_TOP_T = 0.11
R_BASE_Y = 0.17      # pedestal half thickness


def build_round_table():
    agg = material("picnic_aggregate", AGGREGATE)
    emb = material("picnic_emblem", EMBLEM)

    # the top: a thick, softly rounded disc
    bm = cylinder_bm("z", (0, 0), R_TOP, R_TOP_Z - R_TOP_T, R_TOP_Z, 64)
    new_object("top", bm, agg, bevel=0.04)

    # the pedestal: a flat-faced wall along X that waists into a column, with
    # a small round hole through the column near the top
    col_top = R_TOP_Z - R_TOP_T + 0.01
    prof = [(-0.80, 0.0), (0.80, 0.0), (0.80, 0.24), (0.62, 0.28), (0.44, 0.35), (0.31, 0.45),
            (0.24, 0.58), (0.24, col_top), (-0.24, col_top), (-0.24, 0.58), (-0.31, 0.45),
            (-0.44, 0.35), (-0.62, 0.28), (-0.80, 0.24)]
    hole = cylinder_bm("y", (0.0, 0.56), 0.05, -R_BASE_Y - 0.05, R_BASE_Y + 0.05, 24)
    subtract(prism(prof, "y", -R_BASE_Y, R_BASE_Y), [hole], "pedestal", agg, bevel=0.028)

    # the medallion's flat disc on the pedestal's front face
    d = disc("medallion", emb, (0, 0, 0), "y", 0.115, 0.012)
    # the disc is built along +Y from its back; the front face is -Y
    d.location = (0.0, -R_BASE_Y - 0.009, 0.30)

    # the two crescent benches, concentric with the top, left and right
    for side, mid in (("l", 180.0), ("r", 0.0)):
        span = 48.0
        a0, a1 = mid - span, mid + span
        seat = sector(0.66, 1.10, a0, a1)
        new_object(f"crescent_{side}", prism(seat, "z", 0.30, 0.46), agg, bevel=0.05)
        support = sector(0.80, 0.98, mid - 38.0, mid + 38.0)
        new_object(f"crescent_support_{side}", prism(support, "z", 0.0, 0.32), agg, bevel=0.03)


def checks_round():
    a = 48.0
    inner_gap = 2 * 0.66 * math.cos(math.radians(a))
    return [
        f"knee room under the top: {R_TOP_Z - R_TOP_T:.2f} m high (need 0.69), the column "
        f"0.48 m wide at its waist, {R_TOP - R_BASE_Y:.2f} m deep from the top's edge to the pedestal's face (need 0.48)",
        f"open sides: {inner_gap:.2f} m between the benches' inner ends, "
        f"{2 * 1.10 * math.cos(math.radians(a)):.2f} m at their outer corners",
        f"top {R_TOP_Z:.2f} m, seat {0.46:.2f} m",
    ]


# --- the file ----------------------------------------------------------------

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
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    scene.world = world
    # ground, and a sun
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.001))
    ground = bpy.context.active_object
    ground.data.materials.append(material("render_ground", (0.55, 0.52, 0.46, 1)))
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.2
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    scene.collection.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    scene.collection.objects.link(cam)
    scene.camera = cam
    views = {
        "three_quarter": ((3.0, -3.2, 1.9), (0, 0, 0.4)),
        "end": ((4.2, 0.0, 1.0), (0, 0, 0.4)),
        "front": ((0.0, -4.2, 1.0), (0, 0, 0.4)),
        "plan": ((0.0, -0.01, 5.0), (0, 0, 0.0)),
    }
    for tag, (loc, target) in views.items():
        cam.location = loc
        d = Vector(target) - Vector(loc)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(folder, f"{name}_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    builders = {"concrete_picnic_table": (build_trestle_table, checks_trestle),
                "round_picnic_table": (build_round_table, checks_round)}
    if name not in builders:
        raise SystemExit(f"picnic_tables: open concrete_picnic_table.blend or round_picnic_table.blend, not {name}")
    export = bpy.data.collections["export"]
    if export.objects:
        if "--replace" not in argv:
            raise SystemExit(f"picnic_tables: export already holds {[o.name for o in export.objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(export.objects):
            bpy.data.objects.remove(o)
    build, check = builders[name]
    build()
    # how unwrap_parts.py lays each part out: every part here is a bevelled
    # or cut solid, the discs included (laid flat whole, a disc's bevelled rim
    # folds over its face), laid flat facet by facet; the family bolts are
    # cylinders to it
    for o in export.objects:
        if not o.get("kyt_family_bolt"):
            o["kyt_unwrap"] = "facets"
    tris = sum(len(o.data.polygons) for o in export.objects)
    print(f"picnic_tables: {name}: {len(export.objects)} parts, {tris} faces")
    for line in check():
        print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
