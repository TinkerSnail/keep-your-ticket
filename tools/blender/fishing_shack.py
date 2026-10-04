"""The beach town's fishing shack: one shell for the plaza's three older
fishing shacks, block-out (2026-10-02).

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
        assets/source/props/fishing_shack.blend --python tools/blender/fishing_shack.py -- \
        [--tenant bait|market|smokehouse] [--replace] [--save] [--render <folder>]

The file starts from `new_prop.py -- fishing_shack`. This tool builds the
shack into `export`, one object a part, and the plan's footprint, a 1.7 m
figure and the `ground_line` mount into the locked `reference`; rerunning it
rebuilds everything it made (tagged `kyt_shack`) from scratch, and refuses
while `export` holds anything it did not make, unless `--replace`.

**The plan.** `documentation/maps/beach-town-plan.html`, zone C: three shacks
side by side on the plaza's north side at the ferry landing (1.8 m over the
sea), each 5.5 m along the shore by 7 m deep with 0.5 m between them: bait
and tackle, a fish market, a smokehouse. Decision 6: a real counter or
service window and a real customer door on the plaza face, each door a true
threshold (an opening in a wall with thickness, closed by its own leaf), a
service door on the back; no interior yet. The plan's "back street" is a
2 m strip between the shacks and the plaza's north edge.

**Frame.** Real metres, Z up, origin at the footprint's centre, the floor
(the threshold level) at z = 0. The plaza face is -Y here, which the glTF
export (Y-up) turns into Godot's +Z, the prop convention (`checks.py`: the
plaza bench's back lies toward +Y). +X is the viewer's right from the
plaza. Walls and floor go below z = 0 on purpose, so uneven paving never
shows a gap under them: `ground_line` at the origin tells Check so.

**The shell.** Walls 0.15 m thick as one solid (a pentagon tube with end
walls, cut by booleans) so no corner or gable seam shares a plane; the ridge
runs front to back, so each shack shows the plaza a gable with a sign on it
and three in a row read as three; the side eaves are 0.15 m, which two
neighbours fit in the plan's 0.5 m gap. Every opening is a hole through the
wall: the customer door, the counter hatch, the service door. The floor is
one slab whose top is z = 0 with a tongue through each door opening to 2 cm
past the wall, so the threshold is flush and step-free (no step-up in
`CharacterBody3D`). The counter is a slab filling the hatch opening's foot
(its sill), 1.05 m high, with a shelf outside. The roof is one chevron slab
with the outer slope of the walls 3 cm inside it. Nothing shares a plane:
parts overlap into their neighbours instead (the sign 2 cm into the gable,
the awning 3 cm into the wall, the floor 5 cm into the walls).

**Scale and character** from her Avila Beach photographs
(`documentation/reference/beach_town/`): single-storey, eave about 2.7 m,
a low grey shingle roof, walls in one strong paint colour with white trim
(the gable end white, as the blue cottage's), a small awning over the
counter. No photo of a fishing shack itself yet
(`documentation/reference/fishing_shack/` is empty): the fronts are a plain
block-out to be shaped when it comes, not invented detail. Cartoony as the
rest of the park: chunky, few big pieces, edges rounded over.

**Tenants.** One shell; `TENANTS` holds the small front differences (which
side the door is, the hatch's width, the awning, the smokehouse's stack and
its colour). The file keeps `bait`; the others are rendered beside it.
Materials are flat stand-ins named by part, for the painting to replace.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_shack"

# --- the plan's numbers ----------------------------------------------------

WIDTH, DEPTH = 5.5, 7.0            # the plan rectangle, along the shore by deep
HX, HY = WIDTH / 2, DEPTH / 2
WALL = 0.15                         # wall thickness
BELOW = 0.20                        # walls reach this far below the threshold
EAVE = 2.70                         # the side walls' top
PITCH = 5.0 / 12.0                  # rise over run
RIDGE = EAVE + PITCH * HX           # the wall shell's apex
SLOPE_T = WALL / math.cos(math.atan(PITCH))   # the sloped wall's vertical thickness
ROOF_T = 0.18                       # the roof slab, vertical
ROOF_SINK = 0.03                    # the wall's slope this far inside the slab
OH_SIDE, OH_END = 0.15, 0.35        # eave and rake overhangs
FLOOR_T = 0.15
NOSE = 0.02                         # the threshold past the wall face
DOOR_W, DOOR_H = 1.0, 2.1
HATCH_SILL, HATCH_TOP = 1.05, 2.15  # the counter's top, the hatch's head
COUNTER_T, COUNTER_OUT, COUNTER_IN = 0.12, 0.35, 0.05
LEAF_T, CLEAR, LEAF_SET = 0.05, 0.01, 0.05   # leaves: thickness, reveal, set back from the face
AWNING_Z, AWNING_DROP, AWNING_OUT, AWNING_T = 2.35, 0.30, 0.90, 0.06
SIGN_W, SIGN_H, SIGN_T = 2.4, 0.5, 0.06
BEVEL = 0.025

TENANTS = {
    # door_x: the customer door's centre; the service door sits opposite.
    "bait": dict(door_x=-1.6, hatch_x=0.7, hatch_w=2.0, awning=True, stack=False,
                 walls=(0.35, 0.62, 0.85, 1.0)),
    "market": dict(door_x=1.6, hatch_x=-0.6, hatch_w=2.6, awning=True, stack=False,
                   walls=(0.92, 0.86, 0.70, 1.0)),
    "smokehouse": dict(door_x=-1.6, hatch_x=0.7, hatch_w=1.6, awning=False, stack=True,
                       walls=(0.60, 0.24, 0.17, 1.0)),
}

COLOURS = {
    "shack_trim": (0.93, 0.93, 0.90, 1.0),
    "shack_roof": (0.36, 0.37, 0.38, 1.0),
    "shack_door": (0.12, 0.34, 0.44, 1.0),
    "shack_counter": (0.48, 0.31, 0.16, 1.0),
    "shack_floor": (0.56, 0.54, 0.51, 1.0),
    "shack_awning": (0.16, 0.36, 0.70, 1.0),
    "shack_sign": (0.14, 0.24, 0.32, 1.0),
    "shack_metal": (0.20, 0.20, 0.22, 1.0),
    "reference_figure": (0.55, 0.42, 0.60, 1.0),
    "reference_footprint": (0.85, 0.20, 0.15, 1.0),
}


# --- building blocks ---------------------------------------------------------

def material(name, colour):
    """A flat stand-in material, recoloured on every run (a tenant's walls)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def prism(poly, axis, lo, hi):
    """A 2D polygon extruded along an axis: `poly` is (a, b) pairs, the plane's
    two axes in X, Y, Z order with `axis` left out ('x' gives (y, z), 'y' gives
    (x, z), 'z' gives (x, y)). Counter-clockwise polygons face outward."""
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
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def box(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def cylinder(axis, centre, radius, lo, hi, sides=10):
    poly = [(centre[0] + radius * math.cos(math.tau * i / sides),
             centre[1] + radius * math.sin(math.tau * i / sides)) for i in range(sides)]
    return prism(poly, axis, lo, hi)


def finish(name, bm, mat, coll, *, bevel=BEVEL, segments=2):
    """A bmesh into an object in `coll`, bevelled and smoothed by angle."""
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    mesh.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35)
        apply_modifiers(obj)
    smooth_by_angle(obj)
    return obj


def apply_modifiers(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    # Slot by slot, never `materials.clear()`: clearing resets every
    # polygon's material index to 0 (the gables lost their trim that way).
    # An exact boolean appends the cutter's empty slot and points the hole's
    # faces at it; those faces are the wall's, slot 0, and the slot goes.
    n_old = len(old.materials)
    for p in new.polygons:
        if p.material_index >= n_old:
            p.material_index = 0
    while len(new.materials) > n_old:
        new.materials.pop(index=len(new.materials) - 1)
    for i, m in enumerate(old.materials):
        if i < len(new.materials):
            new.materials[i] = m
        else:
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


def subtract(obj, cutters):
    """Cut each bmesh in `cutters` out of `obj`, exact booleans, in place."""
    for i, cb in enumerate(cutters):
        mesh = bpy.data.meshes.new(f"_cut{i}")
        cb.to_mesh(mesh)
        cb.free()
        cut = bpy.data.objects.new(f"_cut{i}", mesh)
        bpy.context.scene.collection.objects.link(cut)
        mod = obj.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        mod.solver = "EXACT"
        apply_modifiers(obj)
        bpy.data.objects.remove(cut, do_unlink=True)
        bpy.data.meshes.remove(mesh)


def tilted_bar(name, mat, coll, a, b, size, x0, x1):
    """A square bar from point a to point b in the (y, z) plane, `size`
    across, spanning x0..x1: four corners of a rectangle along the bar."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    n = Vector((-d.y, d.x)) * (size / 2)
    poly = [tuple(a - n), tuple(b - n), tuple(b + n), tuple(a + n)]
    return finish(name, prism(poly, "x", x0, x1), mat, coll, bevel=0.008, segments=1)


# --- the shack ---------------------------------------------------------------

def roof_top_at(x):
    """The roof slab's top surface height over the slope at |x|."""
    return RIDGE - ROOF_SINK + ROOF_T - PITCH * abs(x)


def build(tenant, coll, mats, suffix=""):
    """The shack's parts for `tenant` into `coll`, at the origin."""
    t = TENANTS[tenant]
    walls_mat = mats["walls"]
    door_x, hatch_x, hatch_w = t["door_x"], t["hatch_x"], t["hatch_w"]
    service_x = -door_x

    # The walls: a pentagon tube along Y with end walls, hollowed, and every
    # opening cut through. Doors are cut to the bottom, so the floor's tongue
    # is the threshold; the hatch's foot is cut 2 cm below the counter's
    # underside so the counter's slab swallows that face.
    outer = [(-HX, -BELOW), (HX, -BELOW), (HX, EAVE), (0.0, RIDGE), (-HX, EAVE)]
    inner_eave = EAVE + PITCH * WALL - SLOPE_T
    inner = [(-HX + WALL, -BELOW - 0.1), (HX - WALL, -BELOW - 0.1), (HX - WALL, inner_eave),
             (0.0, RIDGE - SLOPE_T), (-HX + WALL, inner_eave)]
    walls = finish(f"walls{suffix}", prism(outer, "y", -HY, HY), walls_mat, coll, bevel=0)
    deep = (-HY - 0.1, -HY + WALL + 0.1)   # through the front wall
    back = (HY - WALL - 0.1, HY + 0.1)      # through the back wall
    counter_foot = HATCH_SILL - COUNTER_T + 0.02
    subtract(walls, [
        prism(inner, "y", -HY + WALL, HY - WALL),
        box(door_x - DOOR_W / 2, door_x + DOOR_W / 2, *deep, -BELOW - 0.1, DOOR_H),
        box(hatch_x - hatch_w / 2, hatch_x + hatch_w / 2, *deep, counter_foot, HATCH_TOP),
        box(service_x - DOOR_W / 2, service_x + DOOR_W / 2, *back, -BELOW - 0.1, DOOR_H),
    ])
    # The gable ends wear the trim colour, as the blue cottage's white gable:
    # the boolean leaves each end wall one face from footing to apex, so each
    # is split along the eave line first, between its two eave corners (a
    # plane bisect does nothing there: the plane meets vertices, not edges).
    bm = bmesh.new()
    bm.from_mesh(walls.data)
    for y in (-HY, HY):
        corners = [v for v in bm.verts if abs(v.co.y - y) < 1e-4 and abs(v.co.z - EAVE) < 1e-4
                   and abs(abs(v.co.x) - HX) < 1e-4]
        if len(corners) == 2:
            bmesh.ops.connect_vert_pair(bm, verts=corners)
    bm.to_mesh(walls.data)
    bm.free()
    walls.data.materials.append(mats["trim"])
    gables = 0
    for p in walls.data.polygons:
        if abs(p.normal.y) > 0.9 and p.center.z > EAVE + 0.01:
            p.material_index = 1
            gables += 1
    print(f"  gable faces in trim: {gables}")
    # rounded over, now that the shape is cut
    mod = walls.modifiers.new("bevel", "BEVEL")
    mod.width, mod.segments, mod.limit_method, mod.angle_limit = BEVEL, 2, "ANGLE", math.radians(35)
    apply_modifiers(walls)
    smooth_by_angle(walls)

    # The roof: one chevron slab, the walls' outer slope ROOF_SINK inside it,
    # overhanging the sides a little (the neighbour is 0.5 m away) and the
    # gables more.
    ex = HX + OH_SIDE
    under_e = EAVE - ROOF_SINK - PITCH * OH_SIDE
    under_r = RIDGE - ROOF_SINK
    chevron = [(-ex, under_e), (0.0, under_r), (ex, under_e),
               (ex, under_e + ROOF_T), (0.0, under_r + ROOF_T), (-ex, under_e + ROOF_T)]
    finish(f"roof{suffix}", prism(chevron, "y", -HY - OH_END, HY + OH_END), mats["roof"], coll, bevel=0.03)

    # The floor: top at z = 0, into the walls by COUNTER_IN, a tongue through
    # each door opening to NOSE past the wall's face: the thresholds.
    fx, fy = HX - WALL + 0.05, HY - WALL + 0.05
    tw = DOOR_W / 2 + 0.02
    floor = [(-fx, -fy), (door_x - tw, -fy), (door_x - tw, -HY - NOSE), (door_x + tw, -HY - NOSE),
             (door_x + tw, -fy), (fx, -fy), (fx, fy), (service_x + tw, fy),
             (service_x + tw, HY + NOSE), (service_x - tw, HY + NOSE), (service_x - tw, fy), (-fx, fy)]
    finish(f"floor{suffix}", prism(floor, "z", -FLOOR_T, 0.0), mats["floor"], coll, bevel=0)

    # The leaves: each its own object, closed, a reveal all round, set into
    # the wall's thickness so no face lies on the wall's.
    lw, lh = DOOR_W - 2 * CLEAR, DOOR_H - 2 * CLEAR
    finish(f"door_front{suffix}", box(door_x - lw / 2, door_x + lw / 2, -HY + LEAF_SET, -HY + LEAF_SET + LEAF_T,
                                      CLEAR, CLEAR + lh), mats["door"], coll, bevel=0.01, segments=1)
    finish(f"door_service{suffix}", box(service_x - lw / 2, service_x + lw / 2, HY - LEAF_SET - LEAF_T,
                                        HY - LEAF_SET, CLEAR, CLEAR + lh), mats["door"], coll, bevel=0.01, segments=1)
    hw = hatch_w - 2 * CLEAR
    finish(f"hatch{suffix}", box(hatch_x - hw / 2, hatch_x + hw / 2, -HY + LEAF_SET, -HY + LEAF_SET + LEAF_T,
                                 HATCH_SILL + CLEAR, HATCH_TOP - CLEAR), mats["door"], coll, bevel=0.01, segments=1)

    # The counter: the hatch's sill, a slab through the wall with a shelf
    # outside, its ends in the jambs.
    cw = hatch_w / 2 + 0.05
    finish(f"counter{suffix}", box(hatch_x - cw, hatch_x + cw, -HY - COUNTER_OUT, -HY + WALL + COUNTER_IN,
                                   HATCH_SILL - COUNTER_T, HATCH_SILL), mats["counter"], coll, bevel=0.02)

    # The sign board on the gable, its back in the wall.
    finish(f"sign{suffix}", box(-SIGN_W / 2, SIGN_W / 2, -HY - SIGN_T, -HY + 0.02, EAVE + 0.05, EAVE + 0.05 + SIGN_H),
           mats["sign"], coll, bevel=0.01, segments=1)

    # The awning over the counter: a sloped slab into the wall, on two bars.
    if t["awning"]:
        aw = hatch_w / 2 + 0.25
        y_in, y_out = -HY + 0.03, -HY - AWNING_OUT
        slab = [(y_in, AWNING_Z), (y_out, AWNING_Z - AWNING_DROP),
                (y_out, AWNING_Z - AWNING_DROP + AWNING_T), (y_in, AWNING_Z + AWNING_T)]
        finish(f"awning{suffix}", prism(slab, "x", hatch_x - aw, hatch_x + aw), mats["awning"], coll,
               bevel=0.01, segments=1)
        for side, sx in (("l", -1.0), ("r", 1.0)):
            x = hatch_x + sx * (aw - 0.12)
            tilted_bar(f"awning_bar_{side}{suffix}", mats["metal"], coll,
                       (y_in, AWNING_Z - 0.55), (y_out + 0.12, AWNING_Z - AWNING_DROP + 0.03), 0.06,
                       x - 0.03, x + 0.03)

    # The smokehouse's stack through the back of the right slope, capped.
    if t["stack"]:
        sx, sy = 1.4, 2.0
        top = roof_top_at(sx) + 1.1
        finish(f"stack{suffix}", cylinder("z", (sx, sy), 0.14, roof_top_at(sx) - 0.5, top), mats["metal"], coll,
               bevel=0)
        finish(f"stack_cap{suffix}", cylinder("z", (sx, sy), 0.24, top - 0.02, top + 0.05), mats["metal"], coll,
               bevel=0)


def build_reference(coll):
    """The plan's footprint, a 1.7 m figure and the ground mount."""
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        coll.objects.link(marker)
    # the footprint: a thin ring just outside the walls, on the ground
    w = 0.08
    ring = finish("plan_footprint", prism([(-HX - w, -HY - w), (HX + w, -HY - w), (HX + w, HY + w), (-HX - w, HY + w)],
                                          "z", 0.003, 0.006), material("reference_footprint", COLOURS["reference_footprint"]),
                  coll, bevel=0)
    subtract(ring, [box(-HX, HX, -HY, HY, -0.1, 0.1)])
    # a 1.7 m person, beside the door
    mat = material("reference_figure", COLOURS["reference_figure"])
    body = cylinder("z", (0.0, 0.0), 0.20, 0.0, 1.30, 16)
    finish("figure_body", body, mat, coll, bevel=0)
    head = bpy.data.meshes.new("figure_head")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.16)
    bmesh.ops.translate(bm, vec=(0.0, 0.0, 1.54), verts=bm.verts)
    bm.to_mesh(head)
    bm.free()
    obj = bpy.data.objects.new("figure_head", head)
    obj[TAG] = True
    head.materials.append(mat)
    coll.objects.link(obj)
    smooth_by_angle(obj, 60)
    for o in (bpy.data.objects["figure_body"], obj):
        o.location = (-2.4, -4.6, 0.0)


# --- renders -----------------------------------------------------------------

def render(folder, tenant):
    """Temporary cameras, lights, ground and neighbours into a `_review`
    collection; never saved."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["reference"].hide_render = False
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.50, 0.66, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((0.45, -0.6, 0.65)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(sun)

    def flat(name, colour):
        return material(f"_{name}", colour)

    # the plaza, and a 1 m grid and a 5 m scale bar for the plan view
    finish("_plaza", box(-40, 40, -40, 40, -0.2, -0.002), flat("plaza", (0.62, 0.60, 0.56, 1.0)), stage, bevel=0)
    grid_mat = flat("grid", (0.30, 0.30, 0.32, 1.0))
    grid = [finish(f"_gx{i}", box(i - 0.01, i + 0.01, -9, 9, -0.0015, 0.0), grid_mat, stage, bevel=0)
            for i in range(-7, 8)]
    grid += [finish(f"_gy{j}", box(-7, 7, j - 0.01, j + 0.01, -0.0015, 0.0), grid_mat, stage, bevel=0)
             for j in range(-9, 10)]
    bar = [finish(f"_bar{k}", box(-2.5 + k, -1.5 + k, -6.3, -6.0, 0.001, 0.02),
                  flat("bar_dark" if k % 2 == 0 else "bar_light",
                       (0.05, 0.05, 0.05, 1.0) if k % 2 == 0 else (0.98, 0.98, 0.98, 1.0)),
                  stage, bevel=0) for k in range(5)]

    # The neighbours, for the row: the other two tenants in the plan's order
    # (from the plaza, west is on the left: bait, market, smokehouse) at the
    # plan's pitch, this file's tenant at the origin.
    order = list(TENANTS)
    others = [n for n in order if n != tenant]
    for name in others:
        mats = dict(walls=material(f"_walls_{name}", TENANTS[name]["walls"]),
                    **{k: material(f"shack_{k}", COLOURS[f"shack_{k}"])
                       for k in ("trim", "roof", "door", "counter", "floor", "awning", "sign", "metal")})
        build(name, stage, mats, suffix=f"_{name}")
        for o in stage.objects:
            if o.name.endswith(f"_{name}"):
                o.location.x = (order.index(name) - order.index(tenant)) * (WIDTH + 0.5)
    neighbours = [o for o in stage.objects if any(o.name.endswith(f"_{n}") for n in others)]
    row_mid = (1.0 - order.index(tenant)) * (WIDTH + 0.5)
    figure = [bpy.data.objects[n] for n in ("figure_body", "figure_head")]
    roof = bpy.data.objects["roof"]

    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    front_figure = (-2.4, -4.6, 0.0)
    views = {
        # from the plaza, eye height, three-quarter, about 13 m off
        "front_three_quarter": dict(loc=(7.0, -11.5, 1.6), at=(0.0, 0.0, 1.9), lens=35, row=False,
                                    figure=front_figure),
        # orthographic, its lower frame edge on the ground so the buried
        # footing stays buried
        "front_elevation": dict(loc=(0.0, -25.0, 2.66), at=(0.0, 0.0, 2.66), ortho=8.5, row=False,
                                figure=front_figure),
        "back_three_quarter": dict(loc=(-6.5, 10.5, 1.6), at=(0.3, 0.0, 1.9), lens=35, row=False,
                                   figure=(0.5, 4.5, 0.0)),
        # a section at 1.5 m: the camera's near clip cuts the walls, so the
        # openings, the counter, the leaves and the floor show, with the
        # 1 m grid and the 5 m bar
        "plan": dict(loc=(0.0, -0.001, 30.0), at=(0.0, 0.0, 0.0), ortho=15.0, row=False, portrait=True,
                     figure=front_figure, no_roof=True, section=1.5, bar=True),
        "row_from_plaza": dict(loc=(row_mid + 11.0, -17.0, 1.6), at=(row_mid, 0.0, 2.2), lens=28, row=True,
                               figure=front_figure),
    }
    sun_dir = Vector((0.45, -0.6, 0.65))
    for tag, v in views.items():
        for o in neighbours:
            o.hide_render = not v["row"]
        for o in figure:
            o.location = v["figure"]
        for o in bar:
            o.hide_render = not v.get("bar")
        # the section is lit straight down and without shadows, or the wall
        # shell's own top (clipped, still casting) shades the whole floor
        sun.rotation_euler = (Vector((0.0, 0.0, 1.0)) if v.get("section") else sun_dir).to_track_quat("Z", "Y").to_euler()
        sun.data.use_shadow = not v.get("section")
        for o in grid:
            o.hide_render = "ortho" in v and not v.get("section")
        roof.hide_render = bool(v.get("no_roof"))
        cam.data.clip_start = v["loc"][2] - v["section"] if v.get("section") else 0.1
        cam.data.clip_end = 200.0
        cam.data.type = "ORTHO" if "ortho" in v else "PERSP"
        if "ortho" in v:
            cam.data.ortho_scale = v["ortho"]
        else:
            cam.data.lens = v["lens"]
        cam.location = v["loc"]
        d = Vector(v["at"]) - Vector(v["loc"])
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        if v.get("portrait"):
            scene.render.resolution_x, scene.render.resolution_y = 1200, 1500
        else:
            scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
        scene.render.filepath = os.path.join(folder, f"fishing_shack_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)


# --- the file ----------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != "fishing_shack":
        raise SystemExit(f"fishing_shack: open fishing_shack.blend, not {name}")
    tenant = argv[argv.index("--tenant") + 1] if "--tenant" in argv else "bait"
    if tenant not in TENANTS:
        raise SystemExit(f"fishing_shack: tenant is one of {', '.join(TENANTS)}, not {tenant}")
    export = bpy.data.collections["export"]
    authored = bpy.data.collections["authored"]
    reference = bpy.data.collections["reference"]

    hers = [o.name for o in list(export.all_objects) + list(authored.all_objects) if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"fishing_shack: export/authored hold {hers[:4]}..., which may be hers; --replace builds over them")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        if o.name == "ground_line":
            continue
        bpy.data.objects.remove(o, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    mats = dict(walls=material("shack_walls", TENANTS[tenant]["walls"]),
                **{k: material(f"shack_{k}", COLOURS[f"shack_{k}"])
                   for k in ("trim", "roof", "door", "counter", "floor", "awning", "sign", "metal")})
    build(tenant, export, mats)
    build_reference(reference)
    for o in export.objects:
        o["kyt_unwrap"] = "facets"

    tris = 0
    for o in export.objects:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    lo = min((o.matrix_world @ v.co).z for o in export.objects for v in o.data.vertices)
    hi = max((o.matrix_world @ v.co).z for o in export.objects for v in o.data.vertices)
    print(f"fishing_shack: {tenant}: {len(export.objects)} parts, {tris} triangles")
    print(f"  footprint {WIDTH} x {DEPTH} m, walls {WALL} m, eave {EAVE} m (roof edge top "
          f"{EAVE - ROOF_SINK - PITCH * OH_SIDE + ROOF_T:.2f} m), ridge {RIDGE:.2f} m (roof top {roof_top_at(0):.2f} m), "
          f"pitch {PITCH * 12:.0f}:12; lowest {lo:.2f} m, highest {hi:.2f} m")
    print(f"  door {DOOR_W} x {DOOR_H} m at x {TENANTS[tenant]['door_x']:+.1f}, service door at x {-TENANTS[tenant]['door_x']:+.1f}; "
          f"hatch {TENANTS[tenant]['hatch_w']} m wide, counter {HATCH_SILL} m, head {HATCH_TOP} m")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], tenant)


main()
