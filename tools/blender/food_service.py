"""The Boardwalk food-service group, first pass from the catalog notes
(2026-10-02): the menu board, the pie display case, the concession counter
equipment, the service freezer, the delivery crate, the condiment set, the
used tray and the park refill cup. None has a reference photograph; each is a
plain reading of its catalog line and of the authored composition it already
stands as in a Boardwalk scene (exported into the file's `reference`
collection), at real scale, for Christina to review and reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<prop>.blend --python tools/blender/food_service.py -- \
        [--replace] [--save] [--render <folder>]

`<prop>` is `menu_board` (PRP-FOOD-001), `pie_display_case` (002),
`concession_equipment` (003), `service_freezer` (004), `delivery_crate` (005),
`condiment_set` (006), `used_tray` (007) or `refill_cup` (008). The tool builds
whichever the file is named for into `export`, one object a part, on z = 0 at
the origin facing -Y here (+Z in Godot). It refuses while `export` holds
anything (it may be hers) unless `--replace`; it writes the file only with
`--save`; `--render <folder>` shoots a three-quarter, front, side and top view,
one beside a 1.7 m box for scale (and beside a 0.3 m box when the prop is
small), and for a kit one close view of each variant, after any save, so
nothing the render adds reaches the file. Parts are tagged for
`unwrap_parts.py` (`kyt_unwrap`), and a kit's pieces for Send (`kyt_variant`).

**Sizes.** The fixtures keep the authored composition's envelope (the maquette
export in `reference`): the menu boards, the pie case, the freezer, the crates,
the counter and the candy jars. The hand-held things do not: the authored cups,
bottles, napkins and tray are two to three times a real one (a 62 cm squeeze
bottle, a 90 cm tray), readability blobs of the greybox, and every prop
Christina has approved so far stands at real size with chunky details, so the
refill cup, the squeeze bottles, the napkin dispenser, the straw holder and the
tray are built at real size, a little chunky. Each builder's constants say
which, and the report prints both numbers.

**Menu board.** Catalog: "menu content is a swappable graphic state". In I3 two
boards hang on the back wall behind the counter, 3.9 and 1.6 m wide, 1.35 m
tall and 0.1 m deep, their bottoms at 2.025 m. Built as a kit of two variants,
`wide` and `narrow`: a thick rounded frame round a recessed blank panel (the
menu is paint), the wide one divided into three bays by two mullions, and
family bolts through the frame's face at the corners (and the wide one's
mid-span), where a wall-mounted board shows them. Each stands on z = 0 by its
bottom edge; the placement lifts it to the wall. B4's two 0.9 by 1.2 m menus
beside its window are the same family at a third size, not built here.

**Pie display case.** Catalog: "authored composition in I3", a 1.8 by 0.75 m
box 0.55 m tall on the counter. Built: a stainless base, solid rounded ends,
one glass shell for the front and the top (the front rolling over into the top
in a quarter round), two sliding glass doors at the back for the server, one
glass shelf, and five chunky pies in foil tins, three below and two on the
shelf (the crimp and the filling are paint). z = 0 is the counter top.

**Concession equipment.** Catalog: "visible fixed counter tools, not the
building shell". B4's composition is its dark service window and three candy
jars 0.42 m across and 0.72 m tall. Built as a kit: `counter`, the window's
counter fitting, a 3.9 m laminate counter 0.45 m deep with a rounded nose on
three steel gussets, standing on z = 0 by the gussets' feet (its top 0.40 m up;
the placement hangs it under the window with the top at about 1.1 m); and
`taffy_jar`, a glass display jar at the authored size with a rolled foot, a
shoulder, a chrome domed lid with a knob, and a lumpy mass of taffy inside.
The three jars in the scene are one variant placed three times; their colours
are paint.

**Service freezer.** Catalog: "authored composition in I3", a metal box 2.1 by
0.8 m and 1.45 m tall. A chest whose lids are at 1.45 m cannot be reached
into, so the envelope is read as a chest 0.95 m tall with two sliding glass
lids in a frame, on a recessed kick, and a header panel at its back rising to
1.45 m on two short posts, bolted through its face (the header's graphic is
paint, and it is one part to delete if she wants the plain chest).

**Delivery crate.** Catalog: "reusable working residue for food and stock
thresholds"; I3 stacks two wooden boxes, 0.75 by 0.9 by 0.65 m and 0.7 by 0.75
by 0.5 m. Built as a kit of two slatted timber crates at those sizes, `large`
and `small`: four corner posts, three slats a side nailed outside them, a
boarded floor, open top. The stack is two placements, as the scene has it.

**Condiment set.** Catalog: "the café finish layer": two squeeze bottles (red
and yellow) and a napkin stack on B4's counter. Built as a kit at real size:
`bottle_red` and `bottle_yellow`, one squeeze-bottle shape twice (so each gets
its own paint), `napkin_dispenser`, the upright chrome two-faced kind with a
napkin tongue poking from its front slot, and `straw_holder`, a chrome cup with
seven straws, which the catalog line for the family asks for and the scene has
no greybox of.

**Used tray.** Catalog: "a recently vacated table clue, not generic litter".
Built at real size: a flared cafeteria tray 0.46 by 0.36 m, a paper plate on
it, and on the plate the remnant of a funnel cake, a tangle of batter with a
sector eaten away. The powdered sugar is paint.

**Refill cup.** Catalog: "its old-logo story variant remains planned under
PRP-STORY-006". Built at real size, a 44 oz souvenir cup: the tapered cup, a
domed lid with a straw collar, and a straw leaning out of it. The logo is
paint; the story variant is not built.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, every edge rounded over, few big pieces, the family bolt only where a
real one would show. No colour here: flat stand-in materials by surface for
the painting to replace.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_bolt  # noqa: E402

TAU = math.tau

# colours are stand-ins for the painting, one per kind of surface
PAINT_CREAM = (0.84, 0.80, 0.70, 1.0)
PAINT_WHITE = (0.88, 0.88, 0.86, 1.0)
PAINT_TEAL = (0.16, 0.42, 0.44, 1.0)
PANEL_DARK = (0.12, 0.13, 0.16, 1.0)
LAMINATE = (0.80, 0.74, 0.60, 1.0)
STEEL = (0.60, 0.61, 0.63, 1.0)
CHROME = (0.72, 0.73, 0.75, 1.0)
DARK_METAL = (0.26, 0.27, 0.29, 1.0)
GLASS = (0.68, 0.80, 0.86, 1.0)
TIMBER = (0.55, 0.40, 0.24, 1.0)
PASTRY = (0.78, 0.56, 0.28, 1.0)
FOIL = (0.75, 0.76, 0.78, 1.0)
TAFFY = (0.86, 0.60, 0.70, 1.0)
PLASTIC_RED = (0.70, 0.14, 0.12, 1.0)
PLASTIC_DARK = (0.22, 0.22, 0.26, 1.0)
PLASTIC_LIGHT = (0.86, 0.86, 0.86, 1.0)
PAPER = (0.92, 0.90, 0.84, 1.0)
TRAY_BROWN = (0.36, 0.20, 0.14, 1.0)
BATTER = (0.80, 0.60, 0.30, 1.0)
STRAW = (0.92, 0.30, 0.28, 1.0)


# --- building blocks -------------------------------------------------------

def material(name, colour, roughness=0.85, alpha=1.0):
    """A flat stand-in. A glass stand-in is see-through (`alpha`), so what a
    case or a jar holds shows in Blender and in the renders."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = roughness
        mat.diffuse_color = (*colour[:3], alpha)
        if alpha < 1.0:
            bsdf.inputs["Alpha"].default_value = alpha
            for attr, value in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND"),
                                ("use_transparency_overlap", True), ("show_transparent_back", True)):
                try:
                    setattr(mat, attr, value)
                except (AttributeError, TypeError):
                    pass
    return mat


def export():
    return bpy.data.collections["export"]


def new_object(name, bm, mat, *, bevel=0.0, segments=3, angle=35.0, smooth=True, smooth_deg=40.0,
               unwrap="facets"):
    """Finish a bmesh into an object in `export`, with its bevel applied,
    cleaned (every part must be: unwrap_parts.py works on a merged copy and
    needs the same faces in the same order), and tagged for the unwrap:
    `facets` for a bevelled or cut solid, `lathe` for a turned part, "" for
    a true cylinder, which the unwrap's own shape rules handle."""
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


def subtract(bm, cutters, name, mat, *, bevel=0.0, segments=3, angle=35.0, smooth_deg=40.0, unwrap="facets"):
    """Cut `cutters` (bmeshes) out of the shape `bm` and finish it, the bevel
    last, on the cut shape."""
    base = new_object(name, bm, mat, bevel=0, smooth=False, unwrap=unwrap)
    for i, cb in enumerate(cutters):
        cut = new_object(f"{name}_cut{i}", cb, mat, bevel=0, smooth=False, unwrap="")
        mod = base.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        mod.solver = "EXACT"
        apply_modifiers(base)
        bpy.data.objects.remove(cut)
    if bevel:
        mod = base.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        apply_modifiers(base)
    clean(base)
    smooth_by_angle(base, smooth_deg)
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


def transform(objs, matrix):
    """Move the vertices of `objs` by `matrix`, keeping their objects at the origin."""
    for o in objs:
        for v in o.data.vertices:
            v.co = matrix @ v.co
        o.data.update()


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


def ring_prism(outer, inner, axis, lo, hi):
    """A frame: the region between two polygons with the same point count
    (outer and inner, in step), extruded along an axis as `prism` does."""
    bm = bmesh.new()

    def at(a, b, t):
        if axis == "x":
            return (t, a, b)
        if axis == "y":
            return (a, t, b)
        return (a, b, t)

    n = len(outer)
    assert n == len(inner)
    o_lo = [bm.verts.new(at(a, b, lo)) for a, b in outer]
    i_lo = [bm.verts.new(at(a, b, lo)) for a, b in inner]
    o_hi = [bm.verts.new(at(a, b, hi)) for a, b in outer]
    i_hi = [bm.verts.new(at(a, b, hi)) for a, b in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((o_lo[i], o_lo[j], i_lo[j], i_lo[i]))
        bm.faces.new((o_hi[i], i_hi[i], i_hi[j], o_hi[j]))
        bm.faces.new((o_lo[i], o_hi[i], o_hi[j], o_lo[j]))
        bm.faces.new((i_lo[i], i_lo[j], i_hi[j], i_hi[i]))
    return bm


def loft_bm(poly_lo, poly_hi, z_lo, z_hi):
    """Two plan polygons with the same point count joined by side quads, along z."""
    bm = bmesh.new()
    lo = [bm.verts.new((a, b, z_lo)) for a, b in poly_lo]
    hi = [bm.verts.new((a, b, z_hi)) for a, b in poly_hi]
    n = len(lo)
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def box_bm(x0, x1, y0, y1, z0, z1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def rounded_rect(hx, hy, r, per=5, cx=0.0, cy=0.0):
    pts = []
    for ox, oy, a0 in ((hx - r, hy - r, 0.0), (-hx + r, hy - r, 90.0),
                       (-hx + r, -hy + r, 180.0), (hx - r, -hy + r, 270.0)):
        for i in range(per + 1):
            a = math.radians(a0 + 90.0 * i / per)
            pts.append((cx + ox + r * math.cos(a), cy + oy + r * math.sin(a)))
    return pts


def arc(cx, cy, r, a0, a1, n):
    """Points on a circle from angle a0 to a1 (degrees), n segments."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def lathe_bm(profile, sides=24, axis="z", closed=False, bump=None):
    """A profile of (radius, position along the axis) pairs revolved round the
    axis. An end point at radius 0 becomes the pole vertex; an end at a radius
    is capped with a disc. `closed` joins the last point back to the first (a
    band or a ring), with no caps. `bump(ring, i, r, t)` may return a radius
    factor per vertex, for a lumpy turned shape."""
    bm = bmesh.new()

    def at(r, t, a):
        c, s = r * math.cos(a), r * math.sin(a)
        if axis == "z":
            return (c, s, t)
        if axis == "y":
            return (c, t, s)
        return (t, c, s)

    rings = []
    for k, (r, t) in enumerate(profile):
        if abs(r) < 1e-9:
            rings.append([bm.verts.new(at(0.0, t, 0.0))])
        else:
            ring = []
            for i in range(sides):
                rr = r * (bump(k, i, r, t) if bump else 1.0)
                ring.append(bm.verts.new(at(rr, t, TAU * i / sides)))
            rings.append(ring)
    pairs = list(zip(rings, rings[1:]))
    if closed:
        pairs.append((rings[-1], rings[0]))
    for a, b in pairs:
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
    if not closed:
        if len(rings[0]) > 1:
            bm.faces.new(rings[0])
        if len(rings[-1]) > 1:
            bm.faces.new(list(reversed(rings[-1])))
    return bm


def tube_into(bm, points, radius, sides=8):
    """Add a round tube swept along a polyline to `bm`, its rings turned with
    the path (parallel transport), capped at both ends."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tangents.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    normal = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    rings = []
    for p, t in zip(pts, tangents):
        normal = (normal - t * normal.dot(t)).normalized()
        nn, b = normal, t.cross(normal)
        rings.append([bm.verts.new(p + (nn * math.cos(TAU * i / sides) + b * math.sin(TAU * i / sides)) * radius)
                      for i in range(sides)])
    for a, c in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((a[i], a[j], c[j], c[i]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    return bm


def tube_bm(points, radius, sides=8):
    return tube_into(bmesh.new(), points, radius, sides)


def tag(objs, **props):
    for o in objs:
        for k, v in props.items():
            o[k] = v


# --- the menu board ----------------------------------------------------------
#
# I3's two boards hang on the back wall behind the counter: 3.9 by 1.35 m and
# 1.6 by 1.35 m, 0.1 m deep, their bottoms at 2.025 m, their faces toward the
# service windows (the scene's -Z; here the face is -Y and the placement turns
# it). The reference has them standing on z = 0, which is how they are built:
# the origin is the bottom edge's middle, the depth centred on y = 0.

MB_H = 1.35
MB_D = 0.10
MB_WIDTHS = {"wide": 3.9, "narrow": 1.6}
MB_BAYS = {"wide": 3, "narrow": 1}
MB_FRAME = 0.08                 # the frame's width, over two bolt heads
MB_R = 0.06                     # the outer corners' radius
MB_PANEL_SET = 0.025            # the panel's face behind the frame's
MB_PANEL_T = 0.03
MB_MULLION = 0.06


def build_menu_board():
    frame_mat = material("menu_board_frame", PAINT_TEAL)
    panel_mat = material("menu_board_panel", PANEL_DARK, 0.6)
    bolt_mat = family_bolt.paint_of(frame_mat)
    for key, width in MB_WIDTHS.items():
        hx, hz = width / 2, MB_H / 2
        made = []
        outer = [(x, z + hz) for x, z in rounded_rect(hx, hz, MB_R)]
        inner = [(x, z + hz) for x, z in rounded_rect(hx - MB_FRAME, hz - MB_FRAME, 0.015)]
        frame = new_object(f"{key}_frame", ring_prism(outer, inner, "y", -MB_D / 2, MB_D / 2), frame_mat,
                           bevel=0.012, segments=2)
        made.append(frame)
        # the panel: a slab behind the frame's face, its edges buried in the frame
        front = -MB_D / 2 + MB_PANEL_SET
        made.append(new_object(f"{key}_panel", box_bm(-(hx - MB_FRAME) - 0.01, hx - MB_FRAME + 0.01, front,
                                                      front + MB_PANEL_T, MB_FRAME - 0.01, MB_H - MB_FRAME + 0.01),
                               panel_mat, bevel=0.006, segments=1))
        # mullions divide the wide board into bays, set a hair behind the frame's face
        bays = MB_BAYS[key]
        w_in = width - 2 * MB_FRAME
        bay = (w_in - (bays - 1) * MB_MULLION) / bays
        for k in range(1, bays):
            xc = -w_in / 2 + k * bay + (k - 0.5) * MB_MULLION
            made.append(new_object(f"{key}_mullion_{k - 1}", box_bm(xc - MB_MULLION / 2, xc + MB_MULLION / 2,
                                                                     -MB_D / 2 + 0.004, front + 0.005,
                                                                     MB_FRAME - 0.01, MB_H - MB_FRAME + 0.01),
                                   frame_mat, bevel=0.008, segments=1))
        # bolts through the frame's face: the corners, and the wide board's mid-span
        xs = [-(hx - MB_FRAME / 2), hx - MB_FRAME / 2] + ([0.0] if bays > 1 else [])
        for i, x in enumerate(xs):
            for j, z in enumerate((MB_FRAME / 2, MB_H - MB_FRAME / 2)):
                made.append(family_bolt.place(export(), f"{key}_bolt_{i}{j}", Vector((x, -MB_D / 2, z)), (0, -1, 0),
                                              against=[frame], material=bolt_mat))
        tag(made, kyt_variant=key, kyt_collision="none")


def checks_menu_board():
    return [f"boards {MB_H:.2f} m tall and {MB_D * 100:.0f} cm deep, standing on their bottom edge: " +
            ", ".join(f"{k} {w:.2f} m wide in {MB_BAYS[k]} bay{'s' if MB_BAYS[k] > 1 else ''}" for k, w in MB_WIDTHS.items()),
            f"frame {MB_FRAME * 100:.0f} cm wide ({MB_FRAME / family_bolt.HEAD:.1f} bolt heads), panel face "
            f"{MB_PANEL_SET * 100:.1f} cm behind it; I3 hangs them with their bottoms at 2.025 m; nothing collides"]


# --- the pie display case ----------------------------------------------------
#
# I3's case is a 1.8 by 0.75 m box 0.55 m tall on the counter, its customer
# side toward the service windows. z = 0 is the counter top. The hood is set
# in 4 mm from the base's edges and buried 1 cm into it, so no face shares
# the base's planes.

PC_X, PC_Y, PC_Z = 0.90, 0.375, 0.55
PC_BASE_H = 0.07
PC_GLASS_T = 0.012
PC_END_T = 0.03
PC_ARC_R = 0.16
PC_SHELF_Z = 0.30
PC_INSET = 0.004
PC_BURY = 0.01
PC_PIE_R = 0.131                # the crust's rolled rim, a hair over the tin's 0.13
PC_PIE_H = 0.11
PC_PIES = ((-0.58, 0.01, "deck"), (0.0, -0.03, "deck"), (0.58, 0.02, "deck"), (-0.30, -0.01, "shelf"), (0.30, 0.01, "shelf"))


def hood_section(yf, yb, zb, zt, r):
    """The case's end in section (y, z): up the front, over the quarter round,
    across the top and down the back."""
    return [(yf, zb), (yf, zt - r)] + arc(yf + r, zt - r, r, 180.0, 90.0, 6)[1:] + [(yb, zt), (yb, zb)]


def glass_section(yf, yb, zb, zt, r, t):
    """The front-and-top glass in section: the hood's front and top, `t` thick."""
    outer = [(yf, zb), (yf, zt - r)] + arc(yf + r, zt - r, r, 180.0, 90.0, 6)[1:] + [(yb, zt)]
    inner = [(yf + t, zb), (yf + t, zt - r)] + arc(yf + r, zt - r, r - t, 180.0, 90.0, 6)[1:] + [(yb, zt - t)]
    return outer + list(reversed(inner))


def build_pie_case():
    steel = material("pie_case_steel", STEEL, 0.4)
    glass = material("pie_case_glass", GLASS, 0.1, alpha=0.3)
    tin = material("pie_case_tin", FOIL, 0.35)
    pastry = material("pie_case_pastry", PASTRY, 0.9)

    new_object("base", prism(rounded_rect(PC_X, PC_Y, 0.03), "z", 0.0, PC_BASE_H), steel, bevel=0.012, segments=2)
    yf, yb = -PC_Y + PC_INSET, PC_Y - PC_INSET
    zb = PC_BASE_H - PC_BURY
    x_end = PC_X - PC_INSET
    for side, sx in (("l", -1.0), ("r", 1.0)):
        x0, x1 = sorted((sx * x_end, sx * (x_end - PC_END_T)))
        new_object(f"end_{side}", prism(hood_section(yf, yb, zb, PC_Z, PC_ARC_R), "x", x0, x1), steel,
                   bevel=0.008, segments=2)
    x_in = x_end - PC_END_T + PC_BURY       # glass runs this far into the ends
    hood = new_object("hood", prism(glass_section(yf, yb, zb, PC_Z, PC_ARC_R, PC_GLASS_T), "x", -x_in, x_in), glass)
    # the back: two sliding glass doors, the outer one a little behind the inner,
    # neither in the plane of the hood's back edge
    doors = [new_object("door_l", box_bm(-x_in, 0.02, yb - 0.019, yb - 0.007, zb, PC_Z - 0.005), glass),
             new_object("door_r", box_bm(-0.02, x_in, yb - 0.034, yb - 0.022, zb, PC_Z - 0.005), glass)]
    shelf = new_object("shelf", box_bm(-x_in, x_in, yf + 0.08, yb - 0.10, PC_SHELF_Z, PC_SHELF_Z + PC_GLASS_T), glass)
    tag([hood, shelf] + doors, kyt_unwrap="facets")

    # the pies, chunky: a deep foil tin with a recessed foot, and in it a crust
    # with a fat rolled rim bulging over the tin's edge and a high dome
    tin_profile = [(0.0, 0.002), (0.085, 0.002), (0.095, 0.0), (0.118, 0.042), (0.130, 0.044), (0.130, 0.052),
                   (0.108, 0.053), (0.0, 0.053)]
    crust_profile = [(0.0, 0.046), (0.120, 0.046), (0.130, 0.055), (PC_PIE_R, 0.064), (0.124, 0.074), (0.110, 0.078),
                     (0.098, 0.082), (0.072, 0.096), (0.040, 0.106), (0.0, PC_PIE_H)]
    for i, (x, y, where) in enumerate(PC_PIES):
        z = PC_BASE_H if where == "deck" else PC_SHELF_Z + PC_GLASS_T
        t = new_object(f"pie_{i}_tin", lathe_bm(tin_profile, 14), tin, unwrap="lathe")
        c = new_object(f"pie_{i}_crust", lathe_bm(crust_profile, 14), pastry, smooth_deg=60.0, unwrap="lathe")
        for o in (t, c):
            o.location = (x, y, z)
            o["kyt_collision"] = "none"


def checks_pie_case():
    return [f"case {2 * PC_X:.2f} by {2 * PC_Y:.2f} m, {PC_Z:.2f} m tall on the counter; base {PC_BASE_H * 100:.0f} cm, "
            f"shelf at {PC_SHELF_Z:.2f} m, glass {PC_GLASS_T * 1000:.0f} mm, front rolling over at r = {PC_ARC_R:.2f} m",
            f"{len(PC_PIES)} pies {2 * PC_PIE_R:.2f} m across, {PC_PIE_H * 100:.0f} cm tall, {sum(1 for p in PC_PIES if p[2] == 'deck')} on "
            f"the deck and {sum(1 for p in PC_PIES if p[2] == 'shelf')} on the shelf; the pies don't collide"]


# --- the concession equipment ------------------------------------------------
#
# B4's composition: a dark service window 3.9 m wide and three candy jars 0.42
# across and 0.72 m tall standing at 1.09 m. The window is the building's; the
# family is the counter fitting under it and the jars. The counter variant
# stands on z = 0 by its gussets' feet, its top 0.40 m up, so the placement
# hangs it on the wall with the top at about 1.1 m; the back edge is +Y.

CE_COUNTER_W = 3.9
CE_COUNTER_D = 0.45
CE_COUNTER_T = 0.06
CE_DROP = 0.34                  # the gussets' reach down the wall
CE_GUSSET_T = 0.05
CE_GUSSET_XS = (-1.5, 0.0, 1.5)
CE_JAR_R = 0.21
CE_JAR_TOP = 0.72


def build_concession():
    laminate = material("concession_laminate", LAMINATE, 0.5)
    steel = material("concession_steel", STEEL, 0.4)
    glass = material("concession_glass", GLASS, 0.1, alpha=0.3)
    chrome = material("concession_chrome", CHROME, 0.3)
    taffy = material("concession_taffy", TAFFY, 0.7)

    # the counter: a laminate slab with a rounded nose, on three steel gussets
    hw, hd = CE_COUNTER_W / 2, CE_COUNTER_D / 2
    counter = [new_object("counter_top", prism(rounded_rect(hw, hd, 0.03), "z", CE_DROP, CE_DROP + CE_COUNTER_T),
                          laminate, bevel=0.015, segments=3)]
    wall = hd - 0.004                     # the gussets' back, just off the slab's back plane
    gusset = [(wall, CE_DROP + 0.01), (-hd + 0.07, CE_DROP + 0.01), (-hd + 0.07, CE_DROP - 0.05), (wall - 0.05, 0.0),
              (wall, 0.0)]
    for i, x in enumerate(CE_GUSSET_XS):
        counter.append(new_object(f"gusset_{i}", prism(gusset, "x", x - CE_GUSSET_T / 2, x + CE_GUSSET_T / 2), steel,
                                  bevel=0.008, segments=2))
    tag(counter, kyt_variant="counter")

    # the jar: a glass vessel with a rolled foot and a shoulder, a chrome domed
    # lid with a knob, and the taffy heaped inside it
    r = CE_JAR_R
    jar_profile = [(0.0, 0.004), (0.14, 0.004), (0.15, 0.0), (0.19, 0.03), (r, 0.12), (r, 0.40), (0.195, 0.47),
                   (0.165, 0.515), (0.155, 0.53), (0.155, 0.56), (0.143, 0.56), (0.143, 0.53), (0.153, 0.515),
                   (0.183, 0.47), (0.198, 0.40), (0.198, 0.12), (0.18, 0.04), (0.12, 0.02), (0.0, 0.02)]
    jar = new_object("jar", lathe_bm(jar_profile, 20), glass, unwrap="lathe")
    lid_profile = [(0.0, 0.552), (0.17, 0.552), (0.17, 0.578), (0.16, 0.59), (0.12, 0.64), (0.07, 0.675), (0.04, 0.685),
                   (0.035, 0.70), (0.045, 0.71), (0.045, CE_JAR_TOP), (0.0, CE_JAR_TOP)]
    lid = new_object("lid", lathe_bm(lid_profile, 24), chrome, smooth_deg=50.0, unwrap="lathe")

    def lump(ring, i, rr, t):
        if t < 0.30:
            return 1.0
        return 1.0 + 0.035 * math.sin(i * 2.3 + ring * 1.7) * math.cos(i * 1.1 - ring * 0.9) + 0.02 * math.sin(i * 0.9 + ring)

    fill_profile = [(0.0, 0.02), (0.185, 0.02), (0.185, 0.30), (0.183, 0.36), (0.15, 0.40), (0.10, 0.43), (0.05, 0.45),
                    (0.0, 0.46)]
    fill = new_object("taffy", lathe_bm(fill_profile, 16, bump=lump), taffy, smooth_deg=60.0, unwrap="lathe")
    tag([jar, lid, fill], kyt_variant="taffy_jar", kyt_collision="none")


def checks_concession():
    return [f"counter {CE_COUNTER_W:.2f} m long, {CE_COUNTER_D:.2f} m deep, {CE_COUNTER_T * 100:.0f} cm thick, its top "
            f"{CE_DROP + CE_COUNTER_T:.2f} m above the gussets' feet (the origin); {len(CE_GUSSET_XS)} gussets",
            f"jar {2 * CE_JAR_R:.2f} m across, {CE_JAR_TOP:.2f} m tall with the lid (the authored size; a real display "
            f"jar is about half that); the jar doesn't collide, the counter does"]


# --- the service freezer -----------------------------------------------------
#
# I3's box is 2.1 by 0.8 m and 1.45 m tall. Read as a chest 0.95 m tall with
# sliding glass lids and a header panel at its back to 1.45 m. The back is +Y.
# The lid frame oversails the body by 1 cm and is the envelope's 2.1 by 0.8.

SF_X, SF_Y = 1.04, 0.39
SF_KICK_H = 0.10
SF_BODY_TOP = 0.90
SF_FRAME_H = 0.05
SF_WALL = 0.06
SF_FLOOR_Z = 0.30
SF_HEADER_Z0, SF_HEADER_Z1 = 1.00, 1.45
SF_HEADER_T = 0.06
SF_POST = 0.06
SF_POST_X = SF_X - 0.14


def build_freezer():
    shell = material("freezer_shell", PAINT_WHITE, 0.5)
    trim = material("freezer_trim", DARK_METAL, 0.5)
    glass = material("freezer_glass", GLASS, 0.1, alpha=0.3)
    plastic = material("freezer_plastic", PLASTIC_DARK, 0.6)
    bolt_mat = family_bolt.paint_of(shell)

    new_object("kick", prism(rounded_rect(SF_X - 0.04, SF_Y - 0.04, 0.03), "z", 0.0, SF_KICK_H + 0.01), trim,
               bevel=0.01, segments=2)
    cavity = box_bm(-(SF_X - SF_WALL), SF_X - SF_WALL, -(SF_Y - SF_WALL), SF_Y - SF_WALL, SF_FLOOR_Z, SF_BODY_TOP + 0.1)
    subtract(prism(rounded_rect(SF_X, SF_Y, 0.05), "z", SF_KICK_H, SF_BODY_TOP), [cavity], "body", shell,
             bevel=0.02, segments=2)
    # the lid frame: a ring oversailing the body by 1 cm, its hole lipping over the cavity
    hole_x, hole_y = SF_X - SF_WALL - 0.02, SF_Y - SF_WALL - 0.02
    z0 = SF_BODY_TOP - 0.01
    frame = new_object("lid_frame", ring_prism(rounded_rect(SF_X + 0.01, SF_Y + 0.01, 0.06),
                                               rounded_rect(hole_x, hole_y, 0.02), "z", z0, z0 + SF_FRAME_H), trim,
                       bevel=0.012, segments=2)
    # two sliding glass lids in the frame's channel, one over the other, with a pull each
    lids = [new_object("lid_l", box_bm(-hole_x - 0.02, 0.03, -hole_y - 0.02, hole_y + 0.02, 0.905, 0.917), glass),
            new_object("lid_r", box_bm(-0.03, hole_x + 0.02, -hole_y - 0.02, hole_y + 0.02, 0.920, 0.932), glass)]
    for name, xc, z in (("pull_l", -0.25, 0.915), ("pull_r", 0.25, 0.930)):
        new_object(name, box_bm(xc - 0.07, xc + 0.07, -0.015, 0.015, z, z + 0.012), plastic, bevel=0.004, segments=1)
    # the header at the back, on two short posts rising from the frame, bolted through its face
    y1 = SF_Y + 0.005
    header = new_object("header", box_bm(-SF_X, SF_X, y1 - SF_HEADER_T, y1, SF_HEADER_Z0, SF_HEADER_Z1), shell,
                        bevel=0.015, segments=2)
    for side, sx in (("l", -1.0), ("r", 1.0)):
        x = sx * SF_POST_X
        new_object(f"header_post_{side}", box_bm(x - SF_POST / 2, x + SF_POST / 2, y1 - SF_HEADER_T + 0.005, y1 - 0.005,
                                                 z0 + SF_FRAME_H - 0.01, SF_HEADER_Z1 - 0.15), trim, bevel=0.006, segments=1)
        for k, z in enumerate((SF_HEADER_Z0 + 0.08, SF_HEADER_Z1 - 0.20)):
            family_bolt.place(export(), f"bolt_header_{side}_{k}", Vector((x, y1 - SF_HEADER_T, z)), (0, -1, 0),
                              against=[header], material=bolt_mat)
    tag(lids, kyt_unwrap="facets")


def checks_freezer():
    return [f"chest {2 * SF_X:.2f} by {2 * SF_Y:.2f} m, lids in a frame topping out at {SF_BODY_TOP - 0.01 + SF_FRAME_H:.2f} m, "
            f"cavity floor at {SF_FLOOR_Z:.2f} m, walls {SF_WALL * 100:.0f} cm",
            f"header {SF_HEADER_Z0:.2f} to {SF_HEADER_Z1:.2f} m at the back (the authored height), {SF_HEADER_T * 100:.0f} cm thick, "
            f"four bolts; the whole collides"]


# --- the delivery crate ------------------------------------------------------
#
# I3 stacks two wooden boxes at its east service face: 0.75 by 0.9 by 0.65 m
# and, on it, 0.7 by 0.75 by 0.5 m. Each is a slatted timber crate here, its
# long slats outside the corner posts and the short ones recessed 4 mm
# between them, so nothing shares a plane.

DC_SIZES = {"large": (0.75, 0.90, 0.65), "small": (0.70, 0.75, 0.50)}
DC_POST = 0.05
DC_SLAT_T = 0.02
DC_GAP = 0.04
DC_SLATS = 3


def build_crates():
    timber = material("crate_timber", TIMBER, 0.9)
    for key, (sx, sy, h) in DC_SIZES.items():
        hx, hy, t = sx / 2, sy / 2, DC_SLAT_T
        made = []
        # four corner posts inside the slats
        px, py = hx - t - DC_POST / 2 - 0.002, hy - t - DC_POST / 2 - 0.002
        for i, (ax, ay) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            made.append(new_object(f"{key}_post_{i}", box_bm(ax * px - DC_POST / 2, ax * px + DC_POST / 2,
                                                            ay * py - DC_POST / 2, ay * py + DC_POST / 2, 0.0, h - 0.01),
                                   timber, bevel=0.006, segments=1))
        # three slats a side: the long sides' run the full length, the short
        # sides' sit 4 mm in and run 6 mm into them
        w = (h - 0.01 - (DC_SLATS - 1) * DC_GAP) / DC_SLATS
        for k in range(DC_SLATS):
            z0 = 0.01 + k * (w + DC_GAP)
            for side, s in (("f", -1.0), ("b", 1.0)):
                y0, y1 = sorted((s * hy, s * (hy - t)))
                made.append(new_object(f"{key}_slat_{side}_{k}", box_bm(-hx, hx, y0, y1, z0, z0 + w), timber,
                                       bevel=0.006, segments=1))
            for side, s in (("l", -1.0), ("r", 1.0)):
                x0, x1 = sorted((s * (hx - 0.004), s * (hx - 0.004 - t)))
                made.append(new_object(f"{key}_slat_{side}_{k}", box_bm(x0, x1, -(hy - t) - 0.006, hy - t + 0.006, z0, z0 + w),
                                       timber, bevel=0.006, segments=1))
        # the floor: three boards across, run into the long slats
        inner_x = hx - 0.004 - t
        bw = (2 * inner_x - 2 * DC_GAP) / 3
        for k in range(3):
            x0 = -inner_x + k * (bw + DC_GAP)
            made.append(new_object(f"{key}_floor_{k}", box_bm(x0, x0 + bw, -(hy - t) - 0.006, hy - t + 0.006, 0.015, 0.035),
                                   timber, bevel=0.004, segments=1))
        tag(made, kyt_variant=key)


def checks_crates():
    return [", ".join(f"{k} {sx:.2f} by {sy:.2f} m, {h:.2f} m tall" for k, (sx, sy, h) in DC_SIZES.items())
            + f"; posts {DC_POST * 100:.0f} cm, slats {DC_SLAT_T * 100:.0f} cm thick with {DC_GAP * 100:.0f} cm gaps; "
            "open tops; both collide"]


# --- the condiment set -------------------------------------------------------
#
# B4's counter has two squeeze bottles (cylinders 0.22 across and 0.62 m tall)
# and a napkin stack (0.42 by 0.5 by 0.16 m): three times a real one. Built at
# real size: the bottle 9 cm across and 25 cm tall, the dispenser 16 by 11 by
# 20 cm, the straw holder 9 cm across with straws to 22 cm.

CS_BOTTLE_R, CS_BOTTLE_H = 0.045, 0.255
CS_ND_X, CS_ND_Y, CS_ND_H = 0.08, 0.055, 0.20      # the dispenser's half width, half depth, height
CS_SH_R, CS_SH_H = 0.045, 0.11
CS_STRAWS = 7


def build_condiments():
    plastic = material("condiment_plastic", PLASTIC_RED, 0.6)
    chrome = material("condiment_chrome", CHROME, 0.25)
    paper = material("condiment_paper", PAPER, 0.9)
    straw = material("condiment_straw", PLASTIC_LIGHT, 0.5)

    r = CS_BOTTLE_R
    bottle = [(0.0, 0.003), (r - 0.009, 0.003), (r - 0.003, 0.0), (r, 0.014), (r, 0.15), (r - 0.007, 0.172),
              (0.026, 0.186), (0.026, 0.20), (0.031, 0.202), (0.031, 0.214), (0.011, 0.25), (0.0, CS_BOTTLE_H)]
    for key in ("bottle_red", "bottle_yellow"):
        o = new_object(key, lathe_bm(bottle, 16), plastic, smooth_deg=55.0, unwrap="lathe")
        tag([o], kyt_variant=key, kyt_collision="none")

    # the napkin dispenser: a chrome frame with a window through it each way,
    # a face plate set into each window in two pieces, the slot the gap between
    # them, the napkins behind showing in the slots, and the next napkin's
    # tongue poking from the front one. No booleans: a cut recess bevelled
    # into a serrated edge (round 1).
    hx, hy, h = CS_ND_X, CS_ND_Y, CS_ND_H
    wx, wz0, wz1 = hx - 0.018, 0.025, h - 0.025
    slot_z0, slot_z1 = 0.030, 0.052
    dispenser = [new_object("dispenser_frame", ring_prism([(-hx, 0.0), (hx, 0.0), (hx, h), (-hx, h)],
                                                          [(-wx, wz0), (wx, wz0), (wx, wz1), (-wx, wz1)], "y", -hy, hy),
                            chrome, bevel=0.005, segments=2)]
    for side, s in (("f", -1.0), ("b", 1.0)):
        y0, y1 = sorted((s * (hy - 0.008), s * (hy - 0.012)))
        for part, z0, z1 in (("u", slot_z1, wz1 + 0.01), ("l", wz0 - 0.01, slot_z0)):
            dispenser.append(new_object(f"dispenser_plate_{side}{part}", box_bm(-wx - 0.01, wx + 0.01, y0, y1, z0, z1),
                                        chrome, bevel=0.002, segments=1))
    dispenser.append(new_object("dispenser_napkins", box_bm(-(wx - 0.004), wx - 0.004, -(hy - 0.02), hy - 0.02, 0.01, h - 0.02),
                                paper))
    tongue = new_object("dispenser_tongue", box_bm(-0.04, 0.04, -(hy + 0.012), -(hy - 0.014), 0.033, 0.049), paper,
                        bevel=0.003, segments=1)
    transform([tongue], Matrix.Translation((0, -hy, 0.04)) @ Matrix.Rotation(math.radians(-18.0), 4, "X")
              @ Matrix.Translation((0, hy, -0.04)))
    dispenser.append(tongue)
    tag(dispenser, kyt_variant="napkin_dispenser", kyt_collision="none")

    # the straw holder: a chrome cup, and a bundle of straws leaning in it
    r = CS_SH_R
    holder = new_object("straw_cup", lathe_bm([(0.0, 0.003), (r - 0.007, 0.003), (r, 0.0), (r, CS_SH_H), (r - 0.005, CS_SH_H),
                                               (r - 0.005, 0.012), (0.0, 0.012)], 16), chrome, unwrap="lathe")
    bm = bmesh.new()
    for i in range(CS_STRAWS):
        a = TAU * i / CS_STRAWS + 0.4
        foot = Vector((0.02 * math.cos(a), 0.02 * math.sin(a), 0.014))
        lean = Vector((math.cos(a + 0.5), math.sin(a + 0.5), 0.0)) * (0.012 + 0.006 * (i % 3))
        top = foot + Vector((0, 0, 0.206 + 0.008 * (i % 2))) + lean
        tube_into(bm, [foot, top], 0.004, 6)
    straws = new_object("straws", bm, straw, smooth_deg=60.0, unwrap="")
    tag([holder, straws], kyt_variant="straw_holder", kyt_collision="none")


def checks_condiments():
    return [f"bottles {2 * CS_BOTTLE_R * 100:.0f} cm across, {CS_BOTTLE_H * 100:.1f} cm tall (the authored cylinders are "
            f"22 by 62 cm); dispenser {2 * CS_ND_X * 100:.0f} by {2 * CS_ND_Y * 100:.0f} by {CS_ND_H * 100:.0f} cm "
            f"(the authored napkin stack 42 by 50 by 16); straw holder {2 * CS_SH_R * 100:.0f} cm across, "
            f"{CS_STRAWS} straws to about 22 cm; nothing collides"]


# --- the used tray -----------------------------------------------------------
#
# The café's tray is a 0.72 by 0.9 m slab with a 0.6 m torus on it: twice a
# real tray. Built at real size: a flared tray 0.46 by 0.36 m, a paper plate,
# and the remnant of a funnel cake on the plate.

UT_X, UT_Y = 0.23, 0.18
UT_H = 0.03
UT_FLARE = 0.02
UT_WALL = 0.006
UT_PLATE_R = 0.118
UT_PLATE_AT = (-0.03, 0.01)
UT_STRAND_R = 0.0075
UT_EATEN = (230.0, 330.0)       # the sector of the cake that is gone, degrees: toward the front


def build_tray():
    plastic = material("tray_plastic", TRAY_BROWN, 0.5)
    paper = material("tray_paper", PAPER, 0.9)
    batter = material("tray_batter", BATTER, 0.8)

    lo = rounded_rect(UT_X - UT_FLARE, UT_Y - UT_FLARE, 0.05)
    hi = rounded_rect(UT_X, UT_Y, 0.06)
    cav_lo = rounded_rect(UT_X - UT_FLARE - UT_WALL, UT_Y - UT_FLARE - UT_WALL, 0.05)
    cav_hi = rounded_rect(UT_X - UT_WALL + 0.007, UT_Y - UT_WALL + 0.007, 0.06)
    foot = rounded_rect(UT_X - UT_FLARE - 0.012, UT_Y - UT_FLARE - 0.012, 0.045)
    tray = subtract(loft_bm(lo, hi, 0.0, UT_H), [loft_bm(cav_lo, cav_hi, UT_WALL, UT_H + 0.01),
                                                 loft_bm(foot, foot, -0.01, 0.003)], "tray", plastic, bevel=0.003, segments=1)

    # the plate: a flat floor, a fluted rim rising, a hair recessed under
    pr = UT_PLATE_R
    plate = new_object("plate", lathe_bm([(0.0, 0.001), (0.075, 0.001), (0.085, 0.0), (0.095, 0.004), (pr - 0.003, 0.016),
                                          (pr, 0.019), (pr - 0.006, 0.019), (0.093, 0.007), (0.080, 0.004), (0.0, 0.004)], 16),
                       paper, smooth_deg=50.0, unwrap="lathe")
    plate.location = (UT_PLATE_AT[0], UT_PLATE_AT[1], UT_WALL)

    # the funnel cake: two spirals of batter laid over each other, each with
    # wobble and rising and falling so the strands cross, the eaten sector left
    # out of both, so what is left is a tangle of strands with torn ends
    bm = bmesh.new()
    runs = []
    for turns, n, r0, r1, phase, lift in ((3.4, 80, 0.012, 0.085, 0.0, 0.0), (2.2, 48, 0.030, 0.080, 0.37, 0.011)):
        run = []
        for k in range(n + 1):
            s = k / n
            ang = turns * 360.0 * s + phase * 360.0
            if UT_EATEN[0] <= ang % 360.0 <= UT_EATEN[1]:
                if len(run) >= 3:
                    runs.append(run)
                run = []
                continue
            rad = r0 + (r1 - r0) * s + 0.009 * math.sin(9.0 * s * TAU + phase * 5)
            z = UT_STRAND_R + 0.0035 + lift + 0.006 * (1.0 + math.sin(6.7 * s * TAU + 1.0 + phase * 7)) / 2
            run.append((rad * math.cos(math.radians(ang)), rad * math.sin(math.radians(ang)), z))
        if len(run) >= 3:
            runs.append(run)
    for pts in runs:
        tube_into(bm, pts, UT_STRAND_R, 8)
    cake = new_object("funnel_cake", bm, batter, smooth_deg=60.0)
    cake.location = (UT_PLATE_AT[0], UT_PLATE_AT[1], UT_WALL + 0.004)
    tag([tray, plate, cake], kyt_collision="none")


def checks_tray():
    return [f"tray {2 * UT_X:.2f} by {2 * UT_Y:.2f} m at the rim, {UT_H * 100:.0f} cm deep (the authored slab is 0.72 by "
            f"0.90 m); plate {2 * UT_PLATE_R * 100:.0f} cm; funnel cake about 19 cm across, strands "
            f"{UT_STRAND_R * 2000:.0f} mm, the {UT_EATEN[0]:.0f}-{UT_EATEN[1]:.0f} degree sector (the front) eaten; "
            "nothing collides"]


# --- the refill cup ----------------------------------------------------------
#
# The café's cups are 0.18 m cylinders 0.42 m tall: twice a real one. Built at
# real size, a 44 oz souvenir cup: 10 cm at the rim, 21.5 cm tall, the lid to
# 25 cm and the straw to 34 cm.

RC_R0, RC_R1, RC_H = 0.034, 0.050, 0.215
RC_LID_TOP = 0.254
RC_STRAW_TOP = 0.34
RC_STRAW_LEAN = 6.0


def build_cup():
    plastic = material("cup_plastic", PLASTIC_LIGHT, 0.55)
    lid_mat = material("cup_lid", PAINT_WHITE, 0.4)
    straw_mat = material("cup_straw", STRAW, 0.5)
    r0, r1, h = RC_R0, RC_R1, RC_H
    cup = new_object("cup", lathe_bm([(0.0, 0.004), (r0 - 0.004, 0.004), (r0, 0.0), (r0 + 0.002, 0.01), (r1 - 0.001, h - 0.01),
                                      (r1, h), (r1 - 0.006, h), (r1 - 0.007, h - 0.015), (r0 - 0.002, 0.012), (0.0, 0.012)], 16),
                     plastic, unwrap="lathe")
    lid = new_object("lid", lathe_bm([(0.0, h - 0.003), (r1 - 0.004, h - 0.003), (r1 - 0.004, h - 0.015), (r1 + 0.004, h - 0.015),
                                      (r1 + 0.004, h + 0.007), (r1, h + 0.014), (0.030, h + 0.028), (0.011, h + 0.034),
                                      (0.011, RC_LID_TOP), (0.0, RC_LID_TOP)], 16), lid_mat, smooth_deg=50.0, unwrap="lathe")
    k = math.tan(math.radians(RC_STRAW_LEAN))
    straw = new_object("straw", tube_bm([(0.0, (RC_LID_TOP - 0.03) * k, 0.03), (0.0, -(RC_STRAW_TOP - RC_LID_TOP) * k, RC_STRAW_TOP)],
                                        0.0045, 8), straw_mat, smooth_deg=60.0, unwrap="")
    tag([cup, lid, straw], kyt_collision="none")


def checks_cup():
    return [f"cup {2 * RC_R1 * 100:.0f} cm at the rim, {2 * RC_R0 * 100:.1f} at the foot, {RC_H * 100:.1f} cm tall; lid to "
            f"{RC_LID_TOP * 100:.1f} cm, straw to {RC_STRAW_TOP * 100:.0f} cm leaning {RC_STRAW_LEAN:.0f} degrees toward the "
            "front (the authored cylinders are 18 by 42 cm); nothing collides"]


# --- the file ----------------------------------------------------------------

BUILDERS = {
    "menu_board": (build_menu_board, checks_menu_board),
    "pie_display_case": (build_pie_case, checks_pie_case),
    "concession_equipment": (build_concession, checks_concession),
    "service_freezer": (build_freezer, checks_freezer),
    "delivery_crate": (build_crates, checks_crates),
    "condiment_set": (build_condiments, checks_condiments),
    "used_tray": (build_tray, checks_tray),
    "refill_cup": (build_cup, checks_cup),
}


def parts():
    return [o for o in export().all_objects if o.type == "MESH"]


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def variants(objs):
    groups = {}
    for o in objs:
        groups.setdefault(str(o.get("kyt_variant", "")), []).append(o)
    return groups


def report(name):
    bpy.context.view_layer.update()        # placed parts' matrices are stale until then
    objs = parts()
    tris = 0
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    faces = sum(len(o.data.polygons) for o in objs)
    print(f"food_service: {name}: {len(objs)} parts, {faces} faces, {tris} triangles")
    print("  " + ", ".join(f"{o.name} {len(o.data.loop_triangles)}" for o in sorted(objs, key=lambda o: o.name)))
    groups = variants(objs)
    for key in sorted(groups):
        lo, hi = bounds(groups[key])
        t = sum(len(o.data.loop_triangles) for o in groups[key])
        label = f"  variant {key}: " if key else "  "
        print(f"{label}{hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m "
              f"(x {lo.x:+.3f}..{hi.x:+.3f}, y {lo.y:+.3f}..{hi.y:+.3f}, z {lo.z:+.3f}..{hi.z:+.3f}), "
              f"{len(groups[key])} parts, {t} triangles")


def render(folder, name):
    """Frames into `folder`: three-quarter, front (-Y), side (+X), top, the
    front beside a 1.7 m box (and beside a 0.3 m box for a small prop), and
    for a kit one close three-quarter of each variant. A kit is laid out in a
    row for the whole-kit frames; the file is never saved after this."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    try:
        scene.eevee.taa_render_samples = 32
    except AttributeError:
        pass
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

    bpy.context.view_layer.update()
    objs = parts()
    groups = variants(objs)
    moved = []
    if len(groups) > 1:
        gap = 0.15
        widths = {k: bounds(v)[1].x - bounds(v)[0].x for k, v in groups.items()}
        x = -(sum(widths.values()) + gap * (len(groups) - 1)) / 2
        for key in sorted(groups):
            lo, hi = bounds(groups[key])
            shift = x + widths[key] / 2 - (lo.x + hi.x) / 2
            for o in groups[key]:
                o.location.x += shift
                moved.append((o, shift))
            x += widths[key] + gap
        bpy.context.view_layer.update()

    def add(name_, data, mat=None):
        ob = bpy.data.objects.new(name_, data)
        scene.collection.objects.link(ob)
        if mat is not None:
            ob.data.materials.append(mat)
        return ob

    lo, hi = bounds(objs)
    ground = bpy.data.meshes.new("render_ground")
    g = max(12.0, 4.0 * (hi - lo).length)
    ground.from_pydata([(-g, -g, -0.001), (g, -g, -0.001), (g, g, -0.001), (-g, g, -0.001)], [], [(0, 1, 2, 3)])
    add("render_ground", ground, material("render_ground", (0.55, 0.52, 0.46, 1)))
    sun = add("render_sun", bpy.data.lights.new("render_sun", "SUN"))
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(35))
    cam = add("render_cam", bpy.data.cameras.new("render_cam"))
    cam.data.lens = 45
    scene.camera = cam

    def figure(height, x):
        bm = box_bm(x, x + height * 0.27, -height * 0.09, height * 0.09, 0.0, height)
        me = bpy.data.meshes.new(f"render_figure_{height}")
        bm.to_mesh(me)
        bm.free()
        ob = add(me.name, me, material("render_figure", (0.25, 0.27, 0.32, 1)))
        ob.hide_render = True
        return ob

    from bpy_extras.object_utils import world_to_camera_view

    def shoot(tag_, direction, target, pts, filename):
        span = max((Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
                    - Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))).length, 0.25)
        d = direction.normalized()
        loc = target + d * span * 1.4
        loc.z = max(loc.z, 0.12 * span + 0.05)
        for _ in range(40):
            cam.location = loc
            look = target - loc
            cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            if all(0.03 <= c.x <= 0.97 and 0.03 <= c.y <= 0.97
                   for c in (world_to_camera_view(scene, cam, p) for p in pts)):
                break
            loc = target + (loc - target) * 1.08
        scene.render.filepath = os.path.join(folder, filename)
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)

    def points_of(objs_):
        dg = bpy.context.evaluated_depsgraph_get()
        return [o.matrix_world @ v.co for o in objs_ for v in o.evaluated_get(dg).data.vertices]

    pts = points_of(objs)
    centre = (lo + hi) / 2
    for tag_, direction in (("three_quarter", Vector((-0.9, -1.1, 0.6))), ("front", Vector((0.0, -1.5, 0.25))),
                            ("side", Vector((1.5, 0.0, 0.25))), ("top", Vector((0.0, -0.02, 1.6)))):
        shoot(tag_, direction, centre, pts, f"{name}_{tag_}.png")
    scales = [("scale", 1.7)] + ([("scale_small", 0.3)] if hi.z - lo.z < 0.6 else [])
    for tag_, height in scales:
        fig = figure(height, hi.x + 0.25)
        fig.hide_render = False
        fpts = [fig.matrix_world @ Vector(c) for c in fig.bound_box]
        allp = pts + fpts
        lo2 = Vector((min(p.x for p in allp), min(p.y for p in allp), min(p.z for p in allp)))
        hi2 = Vector((max(p.x for p in allp), max(p.y for p in allp), max(p.z for p in allp)))
        shoot(tag_, Vector((0.0, -1.5, 0.25)), (lo2 + hi2) / 2, allp, f"{name}_{tag_}.png")
        fig.hide_render = True
    if len(groups) > 1:
        for key in sorted(groups):
            for o in objs:
                o.hide_render = o not in groups[key]
            vlo, vhi = bounds(groups[key])
            shoot(key, Vector((-0.9, -1.1, 0.6)), (vlo + vhi) / 2, points_of(groups[key]), f"{name}_{key}.png")
        for o in objs:
            o.hide_render = False
    for o, shift in moved:
        o.location.x -= shift


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in BUILDERS:
        raise SystemExit(f"food_service: open one of {', '.join(BUILDERS)}.blend, not {name}")
    if export().objects:
        if "--replace" not in argv:
            raise SystemExit(f"food_service: export already holds {[o.name for o in export().objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(export().all_objects):
            bpy.data.objects.remove(o)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
        # and the stand-ins the old parts wore, so a changed stand-in is remade
        for m in [m for m in bpy.data.materials if m.users == 0]:
            bpy.data.materials.remove(m)
    build, check = BUILDERS[name]
    build()
    report(name)
    for line in check():
        print("  " + line)
    if "--save" in argv:
        # no .blend1 beside the prop: the file is Christina's, and its backup is hers to make
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
