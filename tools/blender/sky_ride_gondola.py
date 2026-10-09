"""The sky ride's car, the midway gondola, a first model pass from the lead's
reading of Christina's Santa Cruz Sky Glider photograph (2026-10-02; the
photograph itself had not reached disk, so check `documentation/reference/
sky_ride_gondola/` before trusting any proportion here).

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/sky_ride_gondola.blend --python tools/blender/sky_ride_gondola.py -- \\
        [--replace] [--save] [--render <folder>]

Builds into `export`, one object a part, in the greybox's frame: the car's
lowest point on z = 0 at the origin, the riders facing -Y here (+Z in Godot).
The ride hangs the car from the cable grip at the top of the hanger, GRIP_Z
above the origin, the greybox's 2.71 m; `checks()` prints it. Once the car has
a game mesh its parts live in `sky_ride_gondola_source.blend`: run this there,
then Rebuild game mesh. Each part is tagged for `unwrap_parts.py`.

**The car, as the photograph was described:** an open two-seat chair car, one
bright colour each, three stacked pieces. A domed hood on top, an upturned
bowl about as wide as the car, pale underneath. An open middle where two
riders sit side by side on a bench, a slim upright at each side joining the
hood to the tub. A rounded tub below holding the bench, with the big white car
number on its front face (paint) and a bar across the front. One short dark
hanger from the hood's top to a small grip housing on the cable.

**What is kept from the greybox** (`sky_cabin_0`, `_sky_ride_cabin` in
`tools/gen_props.gd`), so the car still fits the ride's spacing: the tub's
1.45 by 1.18 m footprint and 0.72 m height, the hood's 1.65 by 1.38 m at 1.76 m,
and the cable grip 2.71 m above the tub's bottom (the generator's 2.35 m drop
from the cable to the tub's middle).

**Assumed, for Christina to confirm against the photo:** the riders' legs are
inside the tub, on its floor, with the seat 0.48 m above it (the greybox's seat
figure as the lead read it); the bar across the front is a footrest or bumper
outside the tub at a third of its height; the hood is one moulded piece with a
flat crown; the uprights stand on the rim just behind the middle of each side;
nothing lights up on the car (the greybox carries a bulb on its canopy that
this pass leaves out).

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, few pieces, every edge rounded over. The family bolt only where a real
one would show: two on each upright's foot, four on the hanger's foot plate.
The materials are flat stand-ins by surface, car paint, hood underside, seat,
dark metal; the colourways (blue, teal, red, orange) are painting. A part
Christina has reshaped by hand is kept: a run refuses while `export` holds
anything, and `--replace` builds over it.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_bolt  # noqa: E402

TAU = math.tau

# colours are stand-ins for the painting
PAINT = (0.06, 0.28, 0.72, 1.0)          # one bright car colour; blue here
HOOD_UNDER = (0.86, 0.84, 0.76, 1.0)     # the pale underside of the hood
SEAT = (0.93, 0.80, 0.38, 1.0)           # the bench and the tub's inside
METAL = (0.07, 0.075, 0.085, 1.0)        # hanger, grip, uprights, bar

BEVEL = 0.025

# --- the car's measurements -----------------------------------------------------
#
# The greybox's footprint and heights (reference collection, z from the tub's
# bottom): tub 1.45 x 1.18 x 0.72, hood 1.65 x 1.38 at 1.766, cable 2.71.

TUB_X, TUB_Y = 0.725, 0.59    # the tub's half width (across the riders) and half depth
TUB_H = 0.72                  # the rim's height
TUB_R = 0.30                  # the plan's corner radius at the rim: the front flat
                              # between the corners, 0.85 m, carries the number
ROUND_R = 0.20                # the rounded bottom edge, a quarter circle
FLARE = 0.04                  # the walls lean out this much from the rounding to the rim
WALL = 0.06                   # the tub's wall and rim
FLOOR_Z = 0.07                # the tub's floor, inside
SEAT_Z = FLOOR_Z + 0.48       # the seat's top: 0.48 m above the floor, a chair's height
SEAT_X = 0.56                 # the bench's half width: two riders
SEAT_FRONT_Y = 0.10           # the seat's front edge; the backrest stands behind it
BACK_TOP_Z = 1.05             # the backrest's top, shoulder height for a seated rider
BACK_LEAN = math.radians(8.0)

UPRIGHT_T = family_bolt.HEAD  # the slim uprights: flat straps one bolt head thick
UPRIGHT_W = 0.09              # and this wide along the travel, so a bolt sits in them
UPRIGHT_Y = 0.10              # just behind the middle of the side, so the riders
                              # ahead of them are clear from the side
UPRIGHT_FOOT_Z = 0.46         # the strap runs down the tub's outer wall to here,
                              # two bolts SPACING apart holding it
UPRIGHT_IN = 0.025            # how far the strap sinks into the wall at the rim

HOOD_X, HOOD_Y = 0.825, 0.69  # the hood's half sizes at the eave
HOOD_R = 0.32                 # its plan corner radius at the eave
HOOD_Z = 1.76                 # the underside
EAVE = 0.05                   # the eave's upright edge
DOME_H = 0.30                 # the dome's rise above the eave
DOME_CROWN = 0.28             # the crown's size as a fraction of the eave's: the dome
                              # draws in to a small flat top the hanger plate sits on
HOOD_TOP_Z = HOOD_Z + EAVE + DOME_H

PLATE_R = 0.13                # the hanger's foot plate on the crown, with four bolts
PLATE_T = 0.03
HANGER_X, HANGER_Y = 0.035, 0.06   # the hanger bar's half section: a flat bar along the travel
GRIP_Z = 2.71                 # the cable's centre, where the ride hangs the car
GRIP_HALF = 0.08              # the grip housing's half width and half height
GRIP_LEN = 0.32               # along the cable

BAR_R = 0.025                 # the bar across the front
BAR_Z = 0.30
BAR_STANDOFF = 0.10           # how far it stands off the tub's front face
BAR_X = 0.55                  # its half length
BRACKET_X = 0.42
BRACKET_R = 0.02


# --- building blocks -------------------------------------------------------------

def material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = colour
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
        mat.diffuse_color = colour
    return mat


def new_object(name, bm, mats, *, bevel=BEVEL, segments=3, angle=35.0, smooth=True, bevel_material=-1):
    """Finish a bmesh into an object in `export`, with its bevel applied.
    `mats` is one material or a list, indexed by the faces' material_index;
    `bevel_material` is the slot the bevel's new faces take, -1 for whichever
    face they grew from."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections["export"].objects.link(obj)
    for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
        obj.data.materials.append(m)
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.harden_normals = False
        mod.material = bevel_material
        apply_modifiers(obj)
    clean(obj)
    if smooth:
        smooth_by_angle(obj)
    return obj


def clean(obj):
    """Merge coincident vertices and drop faces with no area. unwrap_parts.py
    works on a merged copy and needs the same faces in the same order, so a
    part must already be clean."""
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
    """Bake the modifiers into a new mesh. `new_from_object` brings the
    material slots with it; clearing and re-appending them, as the older
    builders do, zeroes every face's material index, which on a two-material
    part (the tub, the hood) painted the inside the outside's colour. Only
    slots that are missing are appended."""
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new
    for m in list(old.materials)[len(new.materials):]:
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


def cylinder_bm(axis, centre, radius, lo, hi, sides=16):
    poly = [(centre[0] + radius * math.cos(TAU * i / sides),
             centre[1] + radius * math.sin(TAU * i / sides)) for i in range(sides)]
    return prism(poly, axis, lo, hi)


def box_bm(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def rounded_rect(hx, hy, r, per=6):
    """A rounded rectangle in plan, counter-clockwise, 4 * (per + 1) points.
    Offsetting one inward by d is rounded_rect(hx - d, hy - d, r - d): the
    corner centres stay put, so the rings of a loft nest without crossing."""
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def loft(rings, band_material, cap_lo=0, cap_hi=0):
    """A closed solid skinned over `rings`, a list of (z, points) with equal
    point counts in order along the surface: bands between neighbours, a cap
    on the first ring and on the last. `band_material(k)` gives band k's
    material index; the caps take `cap_lo` and `cap_hi`. Rings may go back
    down (a tub's inner wall after its rim) as long as they never cross."""
    bm = bmesh.new()
    layers = [[bm.verts.new((x, y, z)) for x, y in pts] for z, pts in rings]
    n = len(layers[0])
    for k in range(len(layers) - 1):
        a, b = layers[k], layers[k + 1]
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.material_index = band_material(k)
    f = bm.faces.new(layers[0])
    f.material_index = cap_lo
    f = bm.faces.new(list(reversed(layers[-1])))
    f.material_index = cap_hi
    return bm


# --- the parts -------------------------------------------------------------------

def tub_inset(z):
    """How far the tub's outer wall sits inside its rim line at height z:
    the walls flare FLARE from the rounding up to the rim, and below ROUND_R
    the bottom turns in on a quarter circle to a flat base."""
    if z >= ROUND_R:
        return FLARE * (TUB_H - z) / (TUB_H - ROUND_R)
    c = (ROUND_R - z) / ROUND_R
    return FLARE + ROUND_R * (1.0 - math.sqrt(max(0.0, 1.0 - c * c)))


def tub_ring(inset):
    return rounded_rect(TUB_X - inset, TUB_Y - inset, TUB_R - inset)


def build_tub(paint, inside):
    """The tub: a rounded-bottomed bucket with flaring walls, a flat rim WALL
    wide, and inside it a floor at FLOOR_Z. One shell: outer wall up, across
    the rim, inner wall down to the floor, so no boolean. The bevel rounds the
    rim and fillets the floor; the plan corners and the bottom's quarter
    circle are polygonal already. The flat of the front face between the
    corner rounds, 0.85 m wide from the bar up to the rim, is where the car
    number is painted."""
    outer_z = [0.0] + [ROUND_R * (1.0 - math.cos(math.radians(a))) for a in (18, 36, 54, 72)] + [ROUND_R, TUB_H]
    inner_z = [TUB_H, ROUND_R, ROUND_R * (1.0 - math.cos(math.radians(72))), FLOOR_Z]
    rings = [(z, tub_ring(tub_inset(z))) for z in outer_z]
    rings += [(z, tub_ring(tub_inset(z) + WALL)) for z in inner_z]
    outer_bands = len(outer_z)   # the outer bands and the rim annulus
    return new_object("tub", loft(rings, lambda k: 0 if k < outer_bands else 1, cap_lo=0, cap_hi=1),
                      [paint, inside], bevel=BEVEL)


def build_bench(seat):
    """The bench for two: a seat slab on a moulded plinth, one piece, and a
    backrest leaning back BACK_LEAN. The plinth stands inside the floor's
    rounding (the tub narrows toward its floor), and the seat's back and the
    backrest are pushed into the tub's back wall so nothing shares a plane
    with it."""
    back_y = TUB_Y - WALL + 0.01   # buried in the back wall at the seat's height
    plinth_y0, plinth_y1 = 0.18, 0.42
    slab = [(SEAT_FRONT_Y, SEAT_Z), (back_y, SEAT_Z), (back_y, SEAT_Z - 0.08),
            (plinth_y1, SEAT_Z - 0.08), (plinth_y1, FLOOR_Z - 0.03), (plinth_y0, FLOOR_Z - 0.03),
            (plinth_y0, SEAT_Z - 0.08), (SEAT_FRONT_Y, SEAT_Z - 0.08)]
    new_object("seat", prism(slab, "x", -SEAT_X, SEAT_X), seat, bevel=0.03)

    t = math.tan(BACK_LEAN)
    y0, y1, z0 = back_y - 0.09, back_y, SEAT_Z - 0.05
    rise = BACK_TOP_Z - z0
    back = [(y0, z0), (y1, z0), (y1 + rise * t, BACK_TOP_Z), (y0 + rise * t, BACK_TOP_Z)]
    new_object("backrest", prism(back, "x", -SEAT_X, SEAT_X), seat, bevel=0.03)


def build_uprights(metal):
    """The two slim uprights: flat straps standing on the outside of the tub's
    walls, from UPRIGHT_FOOT_Z up into the hood, each held to the wall by two
    family bolts where a real one would show from the ground. The strap's
    inner face sits UPRIGHT_IN inside the wall at the rim; the wall leans
    FLARE outward on its way up, so the strap stays buried to its foot and
    never shares a plane with it."""
    export = bpy.data.collections["export"]
    x0, x1 = TUB_X - UPRIGHT_IN, TUB_X - UPRIGHT_IN + UPRIGHT_T
    y0, y1 = UPRIGHT_Y - UPRIGHT_W / 2, UPRIGHT_Y + UPRIGHT_W / 2
    for side, sx in (("l", -1.0), ("r", 1.0)):
        strap = new_object(f"upright_{side}", box_bm(min(sx * x0, sx * x1), max(sx * x0, sx * x1),
                                                     y0, y1, UPRIGHT_FOOT_Z, HOOD_Z + 0.02),
                           metal, bevel=0.008, segments=2)
        for k, dz in enumerate((0.06, 0.06 + family_bolt.SPACING)):
            family_bolt.place(export, f"bolt_foot_{side}_{k}",
                              Vector((sx * x1, UPRIGHT_Y, UPRIGHT_FOOT_Z + dz)),
                              (sx, 0.0, 0.0), against=[strap])


def build_hood(paint, under):
    """The hood: an upturned bowl over the car, a short upright eave then a
    dome rising DOME_H on a quarter ellipse to a small flat crown DOME_CROWN
    the size of the eave, on the greybox's 1.65 by 1.38 m. The dome's rings
    are the eave's outline scaled, not offset (an offset cannot draw in past
    the corner radius, which left the first pass a flat-topped pillow). Its
    underside is one flat pale face; the bevel rounds the eave's lower edge
    in the paint, so the pale stops at the edge."""
    def ring(s):
        return rounded_rect(HOOD_X * s, HOOD_Y * s, HOOD_R * s)
    rings = [(HOOD_Z, ring(1.0)), (HOOD_Z + EAVE, ring(1.0))]
    for a in range(15, 91, 15):
        phi = math.radians(a)
        rings.append((HOOD_Z + EAVE + DOME_H * math.sin(phi), ring(1.0 - (1.0 - DOME_CROWN) * (1.0 - math.cos(phi)))))
    return new_object("hood", loft(rings, lambda k: 0, cap_lo=1, cap_hi=0), [paint, under], bevel=0.03,
                      bevel_material=0)


def build_hanger(metal):
    """The hanger: a round foot plate clamped to the hood's crown with four
    family bolts, a flat bar rising from it, and the grip housing on the
    cable, a rounded block the cable runs through along the travel. The
    cable itself is the ride's."""
    export = bpy.data.collections["export"]
    plate = new_object("hanger_plate", cylinder_bm("z", (0.0, 0.0), PLATE_R, HOOD_TOP_Z - 0.01,
                                                   HOOD_TOP_Z - 0.01 + PLATE_T, sides=16),
                       metal, bevel=0.008, segments=2)
    for k in range(4):
        a = math.radians(45.0 + 90.0 * k)
        family_bolt.place(export, f"bolt_plate_{k}",
                          Vector((0.09 * math.cos(a), 0.09 * math.sin(a), HOOD_TOP_Z - 0.01 + PLATE_T)),
                          (0.0, 0.0, 1.0), against=[plate])
    bar = rounded_rect(HANGER_X, HANGER_Y, 0.015, per=3)
    new_object("hanger", prism(bar, "z", HOOD_TOP_Z + 0.01, GRIP_Z - GRIP_HALF + 0.05), metal, bevel=0)
    grip = [(x, GRIP_Z + z) for x, z in rounded_rect(GRIP_HALF, GRIP_HALF, 0.05, per=4)]
    new_object("grip", prism(grip, "y", -GRIP_LEN / 2, GRIP_LEN / 2), metal, bevel=0.02)


def build_bar(metal):
    """The bar across the front, standing off the tub on two short brackets
    sunk into its wall: the footrest or bumper the photograph shows under the
    number."""
    front = -(TUB_Y - tub_inset(BAR_Z))          # the tub's front face at the bar's height
    bar_y = front - BAR_STANDOFF
    new_object("footrest", cylinder_bm("x", (bar_y, BAR_Z), BAR_R, -BAR_X, BAR_X, sides=12), metal, bevel=0.01)
    for side, sx in (("l", -1.0), ("r", 1.0)):
        new_object(f"footrest_bracket_{side}",
                   cylinder_bm("y", (sx * BRACKET_X, BAR_Z), BRACKET_R, bar_y, front + WALL - 0.01, sides=12),
                   metal, bevel=0)


def build():
    paint = material("gondola_paint", PAINT)
    under = material("gondola_hood_underside", HOOD_UNDER)
    seat = material("gondola_seat", SEAT)
    metal = material("gondola_metal", METAL)
    build_tub(paint, seat)
    build_bench(seat)
    build_uprights(metal)
    build_hood(paint, under)
    build_hanger(metal)
    build_bar(metal)


def checks():
    front_flat = 2 * (TUB_X - TUB_R)
    return [
        f"cable grip (the ride hangs the car here): {GRIP_Z:.2f} m above the tub's bottom; "
        f"hanger shows {GRIP_Z - GRIP_HALF - HOOD_TOP_Z:.2f} m between the hood's crown ({HOOD_TOP_Z:.2f} m) and the grip",
        f"tub {2 * TUB_X:.2f} by {2 * TUB_Y:.2f} m, rim {TUB_H:.2f} m, floor {FLOOR_Z:.2f} m; "
        f"seat top {SEAT_Z:.2f} m ({SEAT_Z - FLOOR_Z:.2f} above the floor), backrest to {BACK_TOP_Z:.2f} m",
        f"hood {2 * HOOD_X:.2f} by {2 * HOOD_Y:.2f} m, underside {HOOD_Z:.2f} m, crown {HOOD_TOP_Z:.2f} m; "
        f"headroom over the seat {HOOD_Z - SEAT_Z:.2f} m",
        f"number field on the front: {front_flat:.2f} m wide between the corner rounds, from the bar "
        f"({BAR_Z:.2f} m) to the rim bevel; uprights {UPRIGHT_T * 1000:.0f} by {UPRIGHT_W * 1000:.0f} mm straps "
        f"outside the walls at y {UPRIGHT_Y:.2f}, feet at {UPRIGHT_FOOT_Z:.2f} m",
    ]


# --- renders -----------------------------------------------------------------------

def render(folder, name):
    """Seven frames into `folder`: three-quarter, front (-Y), side (+X), top,
    from below (how the player sees it, hung overhead), the front beside a
    1.7 m box, and the three-quarter against the greybox. The greybox in
    `reference` is turned in the file (the maquette export took the hanger
    strut's yaw, not the car's); for its frame only, its parent empty is
    turned back so both face -Y. Nothing is saved after this."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    scene.render.resolution_percentage = 100
    world = bpy.data.worlds.new("render_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    scene.world = world
    for cname in ("reference", "authored"):
        c = bpy.data.collections.get(cname)
        if c:
            c.hide_render = True

    objs = [o for o in bpy.data.collections["export"].objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre, size = (lo + hi) / 2, max((hi - lo).length, 0.3)

    def add(name_, data, mat=None):
        ob = bpy.data.objects.new(name_, data)
        scene.collection.objects.link(ob)
        if mat is not None:
            ob.data.materials.append(mat)
        return ob

    ground = bpy.data.meshes.new("render_ground")
    g = max(12.0, 4.0 * size)
    ground.from_pydata([(-g, -g, -0.001), (g, -g, -0.001), (g, g, -0.001), (-g, g, -0.001)], [], [(0, 1, 2, 3)])
    ground = add("render_ground", ground, material("render_ground", (0.55, 0.52, 0.46, 1)))
    sun = add("render_sun", bpy.data.lights.new("render_sun", "SUN"))
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    # a fill from below for the frame looking up, so the undersides, which the
    # player sees most, keep their colour instead of the sky's
    fill = add("render_fill", bpy.data.lights.new("render_fill", "SUN"))
    fill.data.energy = 1.2
    fill.rotation_euler = (math.radians(150), math.radians(-10), math.radians(20))
    cam = add("render_cam", bpy.data.cameras.new("render_cam"))
    cam.data.lens = 45
    scene.camera = cam
    # the 1.7 m figure for scale: a box beside the prop, on the ground
    fig = bpy.data.meshes.new("render_figure")
    box_bm(hi.x + 0.45, hi.x + 0.9, -0.15, 0.15, 0.0, 1.7).to_mesh(fig)
    figure = add("render_figure", fig, material("render_figure", (0.25, 0.27, 0.32, 1)))

    # the greybox, turned to face -Y like the new car, for its frame only
    reference = bpy.data.collections.get("reference")
    greybox = [o for o in (reference.all_objects if reference else []) if o.type == "MESH" and o.name != "floor"]
    bucket = bpy.data.objects.get("greybox_bucket")
    turned = None
    if bucket is not None and bucket.parent is not None:
        turned = bucket.parent
        turned.rotation_euler.z -= bucket.matrix_world.to_euler().z
    for o in (reference.all_objects if reference else []):
        o.hide_render = o.name == "floor" or o not in greybox

    from bpy_extras.object_utils import world_to_camera_view
    dg = bpy.context.evaluated_depsgraph_get()
    points = [o.matrix_world @ v.co for o in objs for v in o.evaluated_get(dg).data.vertices]
    fig_points = [Vector(c) for c in figure.bound_box]
    views = {
        "three_quarter": (Vector((-0.9, -1.1, 0.6)), centre, points),
        "front": (Vector((0.0, -1.5, 0.25)), centre, points),
        "side": (Vector((1.5, 0.0, 0.25)), centre, points),
        "top": (Vector((0.0, -0.02, 1.6)), centre, points),
        "below": (Vector((0.9, -1.1, -0.8)), centre, points),
        "scale": (Vector((0.0, -1.5, 0.25)), None, points + fig_points),
        "vs_greybox": (Vector((-0.9, -1.1, 0.6)), centre, points),
    }
    for tag_, (direction, target, fit) in views.items():
        figure.hide_render = tag_ != "scale"
        ground.hide_render = tag_ == "below"
        fill.hide_render = tag_ != "below"
        if reference:
            reference.hide_render = tag_ != "vs_greybox"
        if tag_ == "scale":
            hi2 = Vector((hi.x + 0.9, hi.y, max(hi.z, 1.7)))
            target = (lo + hi2) / 2
            span = max((hi2 - lo).length, 0.3)
        else:
            span = size
        d = direction.normalized()
        loc = target + d * span * 1.4
        if tag_ != "below":
            loc.z = max(loc.z, 0.12 * span + 0.1)
        for _ in range(40):
            cam.location = loc
            look = target - loc
            cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            if all(0.03 <= c.x <= 0.97 and 0.03 <= c.y <= 0.97
                   for c in (world_to_camera_view(scene, cam, p) for p in fit)):
                break
            loc = target + (loc - target) * 1.08
        scene.render.filepath = os.path.join(folder, f"{name}_{tag_}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)
    if turned is not None:
        turned.rotation_euler.z = 0.0


# --- the file ----------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name != "sky_ride_gondola":
        raise SystemExit(f"sky_ride_gondola: open sky_ride_gondola.blend, not {name}")
    export = bpy.data.collections["export"]
    if export.objects:
        if "--replace" not in argv:
            raise SystemExit(f"sky_ride_gondola: export already holds {[o.name for o in export.objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(export.objects):
            bpy.data.objects.remove(o)
    build()
    # how unwrap_parts.py lays each part out: the lofted and bevelled solids
    # facet by facet; the true cylinders (uprights, plate, bar, brackets) and
    # the family bolts are left for it to classify
    cylinders = ("upright_", "hanger_plate", "footrest")
    for o in export.objects:
        if not o.get("kyt_family_bolt") and not o.name.startswith(cylinders):
            o["kyt_unwrap"] = "facets"
    tris = 0
    for o in export.objects:
        o.data.calc_loop_triangles()
        n = len(o.data.loop_triangles)
        tris += n
        print(f"  {o.name}: {n} triangles")
    print(f"sky_ride_gondola: {len(export.objects)} parts, {tris} triangles")
    for line in checks():
        print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
