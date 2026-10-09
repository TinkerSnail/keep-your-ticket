"""The plaza's four sign props, a first pass from the catalog notes (2026-10-02):
no photographs exist for these, so each is the plainest reading of its
description and its greybox, at real scale, in the house style, for Christina
to reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<prop>.blend --python tools/blender/plaza_signs.py -- \\
        [--replace] [--save] [--render <folder>]

`<prop>` is one of `picture_spot_sign`, `a_frame_sign`, `newspaper_box` or
`poster_case`; the tool builds whichever the file is named for into `export`,
one object a part, on z = 0 at the origin facing -Y here (+Z in Godot). It
refuses while `export` holds anything (it may be hers) unless `--replace`,
saves only with `--save`, and `--render <folder>` writes five views after the
save (three-quarter, front, side, top, and the prop beside a 1.7 m box for
scale) plus a sixth with the greybox as a wire overlay where the file has one.
Each part is tagged for `unwrap_parts.py` (`kyt_unwrap`).

**Picture spot sign** (PRP-PARK-003, "a low, player-readable sign that
suggests a subject without framing or scoring it"). Greybox: a 1.2 m post of
0.14 m with a 0.9 by 0.6 m board centred at 1.35 m and a dark rectangle for the
camera pictogram. Here: a round post on a bolted base plate, running up behind
a thick rounded board that is bolted through its face to the post, two family
bolts; and on the board a raised camera pictogram, one silhouette (body, prism
hump, shutter nub) with a lens ring and a lens disc inside it. No text, no
frame and no viewfinder shape: the game rule is that nothing frames a shot, so
the sign only points at a subject by facing it. Assumed: the board slightly
smaller than the greybox's (0.84 by 0.56 m) and set 0.1 m forward of the post
axis, so the post stays where the greybox's is.

**A-frame sign** (PRP-PARK-004, "portable day-state and operations notice").
Greybox: two 0.9 by 1.1 m panels leaning together at 11 degrees. Here: two
painted frames, each a rounded ring one band wide round a recessed blank
board (the notices are painted later), meeting at a round hinge rod along the
ridge, their feet cut flat on the ground, and on each side a flat folding stay
between the panels' edges, a family bolt through each of its ends. Assumed:
the greybox's size and lean, kept so the thing still fits where it stands.

**Newspaper box** (PRP-PARK-005). A 1990s coin-operated honour box. Greybox: a
0.45 by 0.4 m body 0.9 m tall under an oversailing lid; the Boardwalk scene
(`scenes/world/boardwalk_props/newspaper_box.tscn`) has the taller kind, a case
0.55 by 0.66 m on a pedestal with its top at 1.23 m. Here, between the two: a
cabinet 0.50 wide, 0.46 deep and 0.62 tall on a square pedestal and a base
plate bolted to the pavement with four family bolts, a soft lid oversailing it,
and on its front a glazed pull-down door (a frame one band wide, a window with
a pocket behind it where the paper is painted later, a hinge rod along its
bottom edge and a D-pull on its top rail) with the coin mechanism as a box at
the lower right below the door. The coin slot and return are paint, not shape.

**Poster case** (PRP-PARK-016, "framed poster or display case; recurs on
promenade and frontage walls; the printed campaign is a swappable graphic
layer"). No greybox of its own; the context frame
(`documentation/screenshots/boardwalk-density-2026-09-09/02_cafe_arcade_amenities.png`)
shows plain wall panels with no hood and no lamp, so it has neither. Here:
a frame one band wide and 0.09 m deep round a US one-sheet poster (27 by 40
in), a back panel for the poster and a glass pane set 14 mm behind the frame's
front; 0.82 by 1.15 m outside. Its bottom edge is on z = 0 and its back on the
plane y = 0, face toward -Y, so Check sees it grounded; the placement scene
lifts it onto a wall.

Cartoony as the rest of the park (`prop-pipeline.md`, Standards applied):
chunky, few big pieces, every edge rounded over, bolted parts sized off the
family bolt (`family_bolt.py`: bands 1.6 heads, bars 1.2 heads). No colour
here: the materials are flat stand-ins by surface (painted metal, board,
glass, bare steel, a dark raised shape) for the painting to replace.
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

# stand-in colours for the painting, one per kind of surface
PAINT = (0.16, 0.42, 0.46, 1.0)      # painted sheet metal
BOARD = (0.86, 0.80, 0.62, 1.0)      # a board face left blank for the notice or poster
DARK = (0.07, 0.07, 0.08, 1.0)       # a dark raised shape
STEEL = (0.38, 0.40, 0.42, 1.0)      # bare steel: rods, stays, a pedestal
GLASS = (0.60, 0.78, 0.82, 0.45)     # glazing, see-through in the render

BAND = family_bolt.BAND              # a bolted band or frame bar, 1.6 heads
BAR = family_bolt.BAR                # a bolted bar, 1.2 heads
HEAD = family_bolt.HEAD

BEVEL = 0.012


# --- building blocks -------------------------------------------------------

def material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        if mat.node_tree is None:
            mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = 0.2 if colour[3] < 1.0 else 0.75
        mat.diffuse_color = colour
        if colour[3] < 1.0:
            bsdf.inputs["Alpha"].default_value = colour[3]
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "BLENDED"
    return mat


def _export():
    return bpy.data.collections["export"]


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


def _bevel(obj, width, angle=35.0):
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = width
    mod.segments = 2                  # two steps round an edge: a small prop's budget
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle)
    mod.harden_normals = False
    apply_modifiers(obj)


def new_object(name, bm, mat, *, bevel=BEVEL, unwrap="facets", smooth=True):
    """Finish a bmesh into an object in `export`, with its bevel applied."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    _export().objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        _bevel(obj, bevel)
    if smooth:
        smooth_by_angle(obj)
    obj["kyt_unwrap"] = unwrap
    return obj


def cut(name, bm, cutters, mat, *, bevel=BEVEL, unwrap="facets"):
    """Take `cutters` (bmeshes) out of the shape `bm` and finish it, the bevel
    last, on the cut shape."""
    base = new_object(name, bm, mat, bevel=0, smooth=False, unwrap=unwrap)
    for i, cb in enumerate(cutters):
        cutter = new_object(f"{name}_cut{i}", cb, mat, bevel=0, smooth=False)
        mod = base.modifiers.new(f"cut{i}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cutter
        mod.solver = "EXACT"
        apply_modifiers(base)
        bpy.data.objects.remove(cutter)
    if bevel:
        _bevel(base, bevel)
    smooth_by_angle(base)
    return base


def _dedupe(poly):
    out = []
    for p in poly:
        if not out or (abs(p[0] - out[-1][0]) > 1e-7 or abs(p[1] - out[-1][1]) > 1e-7):
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-7 and abs(out[0][1] - out[-1][1]) < 1e-7:
        out.pop()
    return out


def prism(poly, axis, lo, hi):
    """A 2D polygon extruded along an axis: `poly` is (a, b) pairs, the plane's
    two axes in X, Y, Z order with `axis` left out ('x' gives (y, z), 'y' gives
    (x, z), 'z' gives (x, y))."""
    bm = bmesh.new()
    poly = _dedupe(poly)

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


def box(x0, x1, y0, y1, z0, z1, r=0.0, per=4):
    """An axis-aligned box, its corners rounded in plan when `r` is given."""
    hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
    if r > 0:
        poly = rounded_rect(hx, hy, min(r, hx * 0.999, hy * 0.999), per)
    else:
        poly = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    poly = [(a + x0 + hx, b + y0 + hy) for a, b in poly]
    return prism(poly, "z", z0, z1)


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


def stadium(half_len, half_h, per=6):
    """A bar's outline with round ends, long axis first."""
    return rounded_rect(half_len, half_h, half_h, per)


def ring_bm(axis, lo, hi, hx, hy, bar, r_out, r_in):
    """A rounded rectangular frame of `bar` width, as (outer, cutter)."""
    outer = prism(rounded_rect(hx, hy, r_out), axis, lo, hi)
    inner = prism(rounded_rect(hx - bar, hy - bar, r_in), axis, lo - 0.05, hi + 0.05)
    return outer, inner


def transform(bm, m):
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return bm


def shift(bm, dx=0.0, dy=0.0, dz=0.0):
    return transform(bm, Matrix.Translation((dx, dy, dz)))


# --- the picture spot sign ---------------------------------------------------
#
# A post behind a board, the way a street sign is built, so the board can be
# thin and the post round: the greybox's post stays where it is and the board
# moves 0.1 m forward of its axis. The pictogram is raised, not painted, so it
# reads as a shape at ten metres with no text.

PS_POST_R = 0.065                                  # 130 mm round, near the greybox's 140
PS_BOARD_W, PS_BOARD_H, PS_BOARD_T = 0.84, 0.56, 0.05
PS_BOARD_Z = 1.35                                  # the board's centre, as the greybox
PS_BOARD_BACK = -(PS_POST_R - 0.005)               # lapped 5 mm into the post
PS_BOARD_FRONT = PS_BOARD_BACK - PS_BOARD_T
PS_POST_TOP = PS_BOARD_Z + PS_BOARD_H / 2 - 0.03   # hidden behind the board
PS_PLATE_R, PS_PLATE_T = 0.16, 0.03
PS_BOLT_DZ = 0.23                                  # the two face bolts, above and below the pictogram
PS_CAM_W, PS_CAM_H = 0.34, 0.24                    # the pictogram's body: the greybox icon's size
PS_CAM_PROUD = 0.016
PS_LENS_R = 0.075


def camera_outline():
    """A camera's silhouette in (x, z) about its centre: a rounded body, a
    prism hump in the middle of its top and a shutter nub at the right."""
    hx, hz, r = PS_CAM_W / 2, PS_CAM_H / 2, 0.035
    hump_hx, hump_h, hr = 0.06, 0.045, 0.014
    nub_x0, nub_x1, nub_h, nr = 0.098, 0.128, 0.018, 0.007

    def arc(cx, cz, rad, a0, a1, n=4):
        return [(cx + rad * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cz + rad * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    pts = []
    pts += arc(hx - r, -hz + r, r, 270, 360)           # bottom right corner
    pts += arc(hx - r, hz - r, r, 0, 90)               # top right corner
    pts += [(nub_x1, hz)]                              # along the top to the nub
    pts += arc(nub_x1 - nr, hz + nub_h - nr, nr, 0, 90, 2)
    pts += arc(nub_x0 + nr, hz + nub_h - nr, nr, 90, 180, 2)
    pts += [(nub_x0, hz), (hump_hx, hz)]               # on to the hump
    pts += arc(hump_hx - hr, hz + hump_h - hr, hr, 0, 90, 3)
    pts += arc(-hump_hx + hr, hz + hump_h - hr, hr, 90, 180, 3)
    pts += [(-hump_hx, hz)]
    pts += arc(-hx + r, hz - r, r, 90, 180)            # top left corner
    pts += arc(-hx + r, -hz + r, r, 180, 270)          # bottom left corner
    return pts


def build_picture_spot_sign():
    paint = material("signs_paint", PAINT)
    board_mat = material("signs_board", BOARD)
    dark = material("signs_dark", DARK)
    glass = material("signs_glass", GLASS)
    export = _export()

    # the base plate, bolted to the pavement
    plate = new_object("base_plate", cylinder_bm("z", (0, 0), PS_PLATE_R, 0.0, PS_PLATE_T, 32), paint,
                       bevel=0.01, unwrap="lathe")
    r = (PS_PLATE_R + PS_POST_R) / 2               # the bolts' ring, between the post and the rim
    for i in range(4):
        a = math.radians(45 + 90 * i)
        family_bolt.place(export, f"bolt_base_{i}", Vector((r * math.cos(a), r * math.sin(a), PS_PLATE_T)),
                          (0, 0, 1), ground=True, against=[plate], material=family_bolt.paint_of(paint))

    # the post, its top rounded, hidden behind the board
    new_object("post", cylinder_bm("z", (0, 0), PS_POST_R, PS_PLATE_T - 0.01, PS_POST_TOP, 24), paint,
               bevel=0.02, unwrap="lathe")

    # the board: a thick rounded slab in front of the post
    bm = prism(rounded_rect(PS_BOARD_W / 2, PS_BOARD_H / 2, 0.07), "y", PS_BOARD_FRONT, PS_BOARD_BACK)
    board = new_object("board", shift(bm, dz=PS_BOARD_Z), board_mat, bevel=0.012)
    # two bolts through its face into the post, above and below the pictogram
    for tag, dz in (("upper", PS_BOLT_DZ), ("lower", -PS_BOLT_DZ)):
        family_bolt.place(export, f"bolt_board_{tag}", Vector((0.0, PS_BOARD_FRONT, PS_BOARD_Z + dz)),
                          (0, -1, 0), against=[board], material=family_bolt.paint_of(board_mat))

    # the camera pictogram: one raised silhouette, a lens ring, a lens disc
    front = PS_BOARD_FRONT + 0.002                      # 2 mm into the board's face
    body_front = front - PS_CAM_PROUD
    # (the pictogram's parts are too thin for a bevel to show, so none)
    bm = prism(camera_outline(), "y", body_front, front)
    new_object("pictogram", shift(bm, dz=PS_BOARD_Z), dark, bevel=0.0)
    ring_front = body_front - 0.012
    outer = cylinder_bm("y", (0.0, PS_BOARD_Z), PS_LENS_R, ring_front, body_front + 0.002, 24)
    inner = cylinder_bm("y", (0.0, PS_BOARD_Z), PS_LENS_R - 0.025, ring_front - 0.05, front + 0.05, 16)
    cut("lens_ring", outer, [inner], dark, bevel=0.0, unwrap="lathe")
    new_object("lens", cylinder_bm("y", (0.0, PS_BOARD_Z), PS_LENS_R - 0.021, ring_front + 0.007, body_front + 0.004, 16),
               glass, bevel=0.0, unwrap="lathe")


def checks_picture_spot_sign():
    return [
        f"post {2 * PS_POST_R * 1000:.0f} mm round ({2 * PS_POST_R / HEAD:.1f} heads) to {PS_POST_TOP:.2f} m; "
        f"board {PS_BOARD_W:.2f} by {PS_BOARD_H:.2f} by {PS_BOARD_T:.2f} m, {PS_BOARD_Z - PS_BOARD_H / 2:.2f} to "
        f"{PS_BOARD_Z + PS_BOARD_H / 2:.2f} m, its face {-PS_BOARD_FRONT:.3f} m forward of the post axis",
        f"pictogram {PS_CAM_W:.2f} by {PS_CAM_H:.2f} m, {PS_CAM_PROUD * 1000:.0f} mm proud; "
        f"face bolts at {PS_BOARD_Z - PS_BOLT_DZ:.2f} and {PS_BOARD_Z + PS_BOLT_DZ:.2f} m",
    ]


# --- the A-frame sign --------------------------------------------------------
#
# Each panel is a frame round a recessed board, built upright with its outer
# face on its local y = 0 and then leaned: the top-inner edges of the two meet
# on the hinge line at y = 0, the outer-bottom corners stand on the ground, and
# the inner-bottom corners, which the lean would lift, are cut flat to it.

AF_W, AF_L, AF_T = 0.90, 1.10, 0.045
AF_LEAN = math.radians(11.0)
AF_RIM = BAND
AF_FACE_T = 0.02
AF_FACE_SET = 0.012                   # the board's face behind the frame's front
AF_ROD_R = 0.024
AF_STAY_Z = 0.40                      # the folding stays' height
AF_STAY_T = 0.012
AF_TY = -(AF_T * math.cos(AF_LEAN) + AF_L * math.sin(AF_LEAN))   # panel a's outer foot, in y
AF_APEX = AF_L * math.cos(AF_LEAN) - AF_T * math.sin(AF_LEAN)    # where the top-inner edges meet


def panel_matrix(side):
    """Where a panel stands: panel a (side -1) toward -Y with its outer face
    at local y = 0 and its board behind that; panel b (side +1) the same shape
    turned half round, so its outer face also looks out."""
    turn = Matrix.Rotation(math.pi, 4, "Z") if side > 0 else Matrix.Identity(4)
    lean = Matrix.Rotation(-AF_LEAN, 4, "X")
    return turn @ Matrix.Translation((0, AF_TY, 0)) @ lean


def build_a_frame_sign():
    paint = material("signs_paint", PAINT)
    board_mat = material("signs_board", BOARD)
    steel = material("signs_steel", STEEL)
    export = _export()

    for tag, side in (("a", -1), ("b", 1)):
        m = panel_matrix(side)
        outer, window = ring_bm("y", 0.0, AF_T, AF_W / 2, AF_L / 2, AF_RIM, 0.03, 0.015)
        shift(outer, dz=AF_L / 2)
        shift(window, dz=AF_L / 2)
        ground = box(-1.0, 1.0, -1.0, 1.0, -0.5, 0.0)
        cut(f"frame_{tag}", transform(outer, m), [transform(window, m), ground], paint, bevel=0.01)
        face = prism(rounded_rect(AF_W / 2 - AF_RIM + 0.012, AF_L / 2 - AF_RIM + 0.012, 0.02), "y",
                     AF_FACE_SET, AF_FACE_SET + AF_FACE_T)
        new_object(f"face_{tag}", transform(shift(face, dz=AF_L / 2), m), board_mat, bevel=0.004)

    # the hinge: a rod along the ridge, half sunk in the two panels' tops
    new_object("hinge_rod", cylinder_bm("x", (0.0, AF_APEX + 0.008), AF_ROD_R, -AF_W / 2 + 0.03, AF_W / 2 - 0.03, 16),
               steel, bevel=0.008, unwrap="lathe")

    # the folding stays: a flat bar across each side between the panels' edges,
    # a bolt through each end into the edge
    y_out = -AF_TY - AF_STAY_Z * math.tan(AF_LEAN)        # panel b's outer face at the stay (a's is -y_out)
    edge_mid = y_out - AF_T / (2 * math.cos(AF_LEAN))      # the middle of a panel's edge there
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        x0, x1 = sx * (AF_W / 2 - 0.003), sx * (AF_W / 2 + AF_STAY_T)
        bm = prism(stadium(y_out + 0.012, BAR / 2, 4), "x", min(x0, x1), max(x0, x1))
        stay = new_object(f"stay_{tag}", shift(bm, dz=AF_STAY_Z), steel, bevel=0.004)
        for end, sy in (("a", -1.0), ("b", 1.0)):
            family_bolt.place(export, f"bolt_stay_{tag}_{end}", Vector((x1, sy * edge_mid, AF_STAY_Z)),
                              (sx, 0, 0), against=[stay])


def checks_a_frame_sign():
    return [
        f"panels {AF_W:.2f} by {AF_L:.2f} by {AF_T:.3f} m leaning {math.degrees(AF_LEAN):.0f} deg, frame {AF_RIM * 1000:.0f} mm "
        f"({AF_RIM / HEAD:.1f} heads), feet {2 * -AF_TY:.2f} m apart outside, ridge at {AF_APEX:.2f} m",
        f"stays {BAR * 1000:.0f} mm tall ({BAR / HEAD:.1f} heads) at {AF_STAY_Z:.2f} m; hinge rod {2 * AF_ROD_R * 1000:.0f} mm",
    ]


# --- the newspaper box -------------------------------------------------------
#
# A cabinet on a pedestal, the honour-box kind, sized between the greybox and
# the Boardwalk scene's: the door is the upper front, hinged at its bottom
# edge, with the window's pocket cut into the cabinet behind it.

NB_W, NB_D = 0.50, 0.46
NB_Z0, NB_Z1 = 0.56, 1.18             # the cabinet's bottom and top
NB_LID_T = 0.05
NB_FRONT = -NB_D / 2
NB_POST = 0.14
NB_FOOT, NB_FOOT_T = 0.36, 0.025
NB_DOOR_W, NB_DOOR_Z0, NB_DOOR_Z1 = 0.42, 0.72, 1.12
NB_DOOR_T = 0.025
NB_POCKET_D = 0.05
NB_COIN = (0.08, 0.20, 0.58, 0.70)    # x0, x1, z0, z1
NB_COIN_PROUD = 0.05


def build_newspaper_box():
    paint = material("signs_paint", PAINT)
    steel = material("signs_steel", STEEL)
    glass = material("signs_glass", GLASS)
    export = _export()

    # the base plate and the pedestal
    h = NB_FOOT / 2
    foot = new_object("foot", box(-h, h, -h, h, 0.0, NB_FOOT_T), steel, bevel=0.01)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        family_bolt.place(export, f"bolt_foot_{i}", Vector((sx * 0.13, sy * 0.13, NB_FOOT_T)), (0, 0, 1),
                          ground=True, against=[foot])
    p = NB_POST / 2
    new_object("pedestal", box(-p, p, -p, p, NB_FOOT_T - 0.01, NB_Z0 + 0.01), steel, bevel=0.018)

    # the cabinet, with the window's pocket cut into its front
    hw, hd = NB_W / 2, NB_D / 2
    dz = (NB_DOOR_Z0 + NB_DOOR_Z1) / 2
    win_hx, win_hz = NB_DOOR_W / 2 - BAND, (NB_DOOR_Z1 - NB_DOOR_Z0) / 2 - BAND
    pocket = prism(rounded_rect(win_hx + 0.01, win_hz + 0.01, 0.015), "y", NB_FRONT - 0.05, NB_FRONT + NB_POCKET_D)
    cut("cabinet", box(-hw, hw, -hd, hd, NB_Z0, NB_Z1, r=0.03), [shift(pocket, dz=dz)], paint, bevel=0.02)
    # the lid, a soft slab oversailing it
    new_object("lid", box(-hw - 0.02, hw + 0.02, -hd - 0.02, hd + 0.02, NB_Z1 - 0.01, NB_Z1 - 0.01 + NB_LID_T, r=0.05),
               paint, bevel=0.02)

    # the door: a frame one band wide, its glass set in it, a hinge rod along
    # its bottom edge and a D-pull on its top rail
    door_front = NB_FRONT - NB_DOOR_T
    outer, window = ring_bm("y", door_front, NB_FRONT + 0.005, NB_DOOR_W / 2, (NB_DOOR_Z1 - NB_DOOR_Z0) / 2,
                            BAND, 0.03, 0.012)
    cut("door_frame", shift(outer, dz=dz), [shift(window, dz=dz)], paint, bevel=0.008)
    pane = prism(rounded_rect(win_hx + 0.011, win_hz + 0.011, 0.012), "y", door_front + 0.009, door_front + 0.015)
    new_object("door_glass", shift(pane, dz=dz), glass, bevel=0.0, unwrap="planar")
    new_object("door_hinge", cylinder_bm("x", (NB_FRONT - 0.010, NB_DOOR_Z0 - 0.004), 0.013,
                                         -NB_DOOR_W / 2, NB_DOOR_W / 2, 12), steel, bevel=0.0, unwrap="lathe")
    rail_z = NB_DOOR_Z1 - BAND / 2
    pull_y = door_front - 0.03                         # the pull's back face
    for tag, sx in (("l", -1.0), ("r", 1.0)):
        new_object(f"pull_stub_{tag}", cylinder_bm("y", (sx * 0.08, rail_z), 0.011, pull_y - 0.008, door_front + 0.004, 8),
                   steel, bevel=0.0, unwrap="lathe")
    new_object("pull", shift(prism(stadium(0.11, BAR / 2, 4), "y", pull_y - 0.016, pull_y), dz=rail_z), steel, bevel=0.005)

    # the coin mechanism: a box at the lower right, below the door
    x0, x1, z0, z1 = NB_COIN
    new_object("coin_box", box(x0, x1, NB_FRONT - NB_COIN_PROUD, NB_FRONT + 0.005, z0, z1), paint, bevel=0.012)


def checks_newspaper_box():
    return [
        f"cabinet {NB_W:.2f} by {NB_D:.2f} by {NB_Z1 - NB_Z0:.2f} m, {NB_Z0:.2f} to {NB_Z1:.2f} m, lid to "
        f"{NB_Z1 - 0.01 + NB_LID_T:.2f} m; pedestal {NB_POST:.2f} m square on a {NB_FOOT:.2f} m plate",
        f"door {NB_DOOR_W:.2f} by {NB_DOOR_Z1 - NB_DOOR_Z0:.2f} m, frame {BAND * 1000:.0f} mm ({BAND / HEAD:.1f} heads), "
        f"window {NB_DOOR_W - 2 * BAND:.2f} by {NB_DOOR_Z1 - NB_DOOR_Z0 - 2 * BAND:.2f} m; coin box "
        f"{NB_COIN[1] - NB_COIN[0]:.2f} by {NB_COIN[3] - NB_COIN[2]:.2f} m, {NB_COIN_PROUD * 1000:.0f} mm proud",
    ]


# --- the poster case ---------------------------------------------------------
#
# Sized round a US one-sheet, 27 by 40 in, with 10 mm round it: the
# promenade's lit movie-poster case without the light. Back on y = 0, bottom
# on z = 0; the placement scene lifts it to its wall height.

PC_POSTER_W, PC_POSTER_H = 27 * 0.0254, 40 * 0.0254
PC_CLEAR = 0.010
PC_W = PC_POSTER_W + 2 * PC_CLEAR + 2 * BAND
PC_H = PC_POSTER_H + 2 * PC_CLEAR + 2 * BAND
PC_D = 0.09
PC_GLASS_SET = 0.014                  # the glass behind the frame's front


def build_poster_case():
    paint = material("signs_paint", PAINT)
    board_mat = material("signs_board", BOARD)
    glass = material("signs_glass", GLASS)

    hx, hz = PC_W / 2, PC_H / 2
    outer, window = ring_bm("y", -PC_D, 0.0, hx, hz, BAND, 0.03, 0.012)
    cut("frame", shift(outer, dz=hz), [shift(window, dz=hz)], paint, bevel=0.012)
    lap = 0.012
    back = prism(rounded_rect(hx - BAND + lap, hz - BAND + lap, 0.02), "y", -0.025, -0.010)
    new_object("back_panel", shift(back, dz=hz), board_mat, bevel=0.004)
    pane = prism(rounded_rect(hx - BAND + lap, hz - BAND + lap, 0.02), "y",
                 -PC_D + PC_GLASS_SET, -PC_D + PC_GLASS_SET + 0.006)
    new_object("glass", shift(pane, dz=hz), glass, bevel=0.0, unwrap="planar")


def checks_poster_case():
    return [
        f"case {PC_W:.2f} by {PC_H:.2f} by {PC_D:.2f} m round a {PC_POSTER_W:.2f} by {PC_POSTER_H:.2f} m poster, "
        f"frame {BAND * 1000:.0f} mm ({BAND / HEAD:.1f} heads), glass {PC_GLASS_SET * 1000:.0f} mm behind the front",
        "back on y = 0, bottom edge on z = 0: the placement scene lifts it onto its wall",
    ]


# --- renders -----------------------------------------------------------------

def _bounds(objects):
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def _points(objects):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objects:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts.extend(o.matrix_world @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    return pts


def _scene_object(name, bm, colour):
    """A render-only object, in the scene collection and never in `export`."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material(f"render_{name}", colour))
    return obj


def render(folder, name):
    from bpy_extras.object_utils import world_to_camera_view
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
    world = bpy.data.worlds.new("w")
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    scene.world = world
    _scene_object("ground", box(-8, 8, -8, 8, -0.02, -0.001), (0.55, 0.52, 0.46, 1))
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.4
    sun.rotation_euler = (math.radians(48), math.radians(12), math.radians(35))
    scene.collection.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 45
    scene.collection.objects.link(cam)
    scene.camera = cam

    parts = [o for o in _export().all_objects if o.type == "MESH"]
    # a wall-hung prop is shown on a wall, lifted to where a case hangs
    on_wall = name == "poster_case"
    if on_wall:
        _scene_object("wall", box(-1.4, 1.4, 0.003, 0.25, -0.02, 2.6), (0.80, 0.74, 0.60, 1))
        for o in parts:
            o.location.z += 0.95
        bpy.context.view_layer.update()
    lo, hi = _bounds(parts)
    centre = (lo + hi) / 2
    points = _points(parts)
    views = {
        "three_quarter": Vector((-0.8, -1.0, 0.55)),
        "front": Vector((0.0, -1.0, 0.12)),
        "side": Vector((1.0, -0.35, 0.10)) if on_wall else Vector((1.0, 0.0, 0.10)),
        "top": Vector((0.0, -0.001, 1.0)),
        "scale": Vector((-0.8, -1.0, 0.45)),
    }
    reference = bpy.data.collections.get("reference")
    if reference and any(o.type == "MESH" and len(o.data.polygons) > 2 for o in reference.all_objects):
        views["greybox"] = views["three_quarter"]

    def frame(direction, pts, target):
        d = direction.normalized()
        dist = max((hi - lo).length, 0.3)
        for _ in range(80):
            cam.location = target + d * dist
            cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            if all(0.07 <= c.x <= 0.93 and 0.07 <= c.y <= 0.93
                   for c in (world_to_camera_view(scene, cam, p) for p in pts)):
                break
            dist *= 1.06

    for tag, direction in views.items():
        extra, pts, target = [], points, centre.copy()
        if tag == "scale":
            # a 1.7 m box, a tall person's height, standing beside the prop
            x = hi.x + 0.35 + 0.225
            y = -0.25 if on_wall else 0.0
            extra.append(_scene_object("scale_box", box(x - 0.225, x + 0.225, y - 0.15, y + 0.15, 0.0, 1.7),
                                       (0.92, 0.92, 0.90, 1)))
            pts = points + [o.matrix_world @ Vector(c) for o in extra for c in o.bound_box]
            target = Vector(((lo.x + x + 0.225) / 2, centre.y, max(0.85, centre.z * 0.9)))
        if tag == "greybox":
            # the greybox as a magenta ghost over the model: render-only
            # copies of its meshes, since the imported objects themselves
            # ignore a material change under some glTF imports
            ghost = material("render_ghost", (1.0, 0.1, 0.8, 0.35))
            for o in reference.all_objects:
                if o.type != "MESH" or len(o.data.polygons) <= 2:
                    continue
                me = o.data.copy()
                me.materials.clear()
                me.materials.append(ghost)
                copy = bpy.data.objects.new(f"{o.name}_ghost", me)
                copy.matrix_world = o.matrix_world.copy()
                scene.collection.objects.link(copy)
                extra.append(copy)
        frame(direction, pts, target)
        if tag == "top":
            cam.rotation_euler = (0.0, 0.0, 0.0)
        scene.render.filepath = os.path.join(folder, f"{name}_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)
        for o in extra:
            bpy.data.objects.remove(o)


# --- the file ----------------------------------------------------------------

BUILDERS = {
    "picture_spot_sign": (build_picture_spot_sign, checks_picture_spot_sign),
    "a_frame_sign": (build_a_frame_sign, checks_a_frame_sign),
    "newspaper_box": (build_newspaper_box, checks_newspaper_box),
    "poster_case": (build_poster_case, checks_poster_case),
}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in BUILDERS:
        raise SystemExit(f"plaza_signs: open one of {', '.join(BUILDERS)}, not {name}")
    export = bpy.data.collections.get("export")
    if export is None:
        raise SystemExit("plaza_signs: this file has no 'export' collection; start it with new_prop.py")
    if export.objects:
        if "--replace" not in argv:
            raise SystemExit(f"plaza_signs: export already holds {[o.name for o in export.objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(export.objects):
            bpy.data.objects.remove(o)
    build, check = BUILDERS[name]
    build()
    bpy.context.view_layer.update()
    parts = [o for o in export.objects if o.type == "MESH"]
    dg = bpy.context.evaluated_depsgraph_get()
    tris, per_part = 0, []
    for o in parts:
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        per_part.append(f"{o.name} {len(me.loop_triangles)}")
        o.evaluated_get(dg).to_mesh_clear()
    lo, hi = _bounds(parts)
    size = hi - lo
    print(f"plaza_signs: {name}: {len(parts)} parts, {tris} triangles, "
          f"{size.x:.3f} wide by {size.y:.3f} deep by {size.z:.3f} tall, "
          f"x {lo.x:.3f}..{hi.x:.3f}, y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.4f}..{hi.z:.3f}")
    print("  triangles by part: " + ", ".join(per_part))
    for line in check():
        print("  " + line)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


main()
