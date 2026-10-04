"""The beach town's cottage, blocked out (2026-10-02): the plan's zone H homes,
"small, close and in colour" (Christina), Capitola's way.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/beach_cottage.blend --python tools/blender/beach_cottage.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, into `export` the **court cottage** (the
bungalow court's seven, `documentation/maps/beach-town-plan.html`, class
`b-cottage`: an 8 x 6 m plan, one storey, a porch to the lane) and into
`authored/hillside_variant`, 12 m east, the **hillside cottage** (the terraced
hillside's fifty: the same body over a garage storey, a deck to the view).
Into the locked `reference` collection go the plan's footprint outlines, a
1.7 m figure, the hillside's ground slope and the `ground_line` marker Check
reads (the walls reach below z = 0 on purpose, like the hardscape kit's).
Everything the tool makes carries `kyt_cottage`, so a rerun removes and
rebuilds its own work and keeps anything of hers; `export` holding anything
untagged refuses without `--replace`.

**Frame.** Real metres, Z up, the ground at z = 0, the origin at the
footprint's centre. The front (porch, door) faces -Y here, which the glTF
export (`send.py`, `export_yup=True`) turns into Godot's +Z, the project's
"facing +Z": the plaza bench's seat markers sit at -Y and `checks.py` says the
same. On the plan the court's cottages stand 8 m deep with their 6 m side to
the lane, so the body is 6 m across (X) and 8 m deep (Y), and the ridge runs
front to back: a gable faces the lane, as a bungalow court's do.

**Contract** (the plan's decision 6, enclosing): public faces, porches and
windows, no interior. Every opening is a real hole through a wall of real
thickness; the door and the panes are solid slabs set in the holes, so nothing
behind them needs to exist. The porch floor is walkable from its steps, and
the steps follow the park's stair rule: a narrow ramp is the floor
(`tools/gen_props.gd`, `_flight_ramp`), the treads are scenery showing past it
on both sides and do not collide (`kyt_collision = none`). No two shapes share
a plane: a part that meets another laps 2 cm into it or stands proud of it.

**No photograph of a cottage yet** (`documentation/reference/beach_cottage/`
is empty), so this is massing with block-out detail only, nothing invented
from prose. What is here comes from the plan's numbers and from Christina's
two Avila Beach photographs (`documentation/reference/beach_town/`): the
hillside's houses are boxes stepping down the slope, each with a deck and a
white railing to the view, low gable roofs, white trim, pale walls. The house
is cartoony-ish, as the rest of the park: few big pieces, chunky trim, roof
and posts; busy is the failure mode.

**The kit.** The body (four walls, roof, corner boards) is the constant; what
swaps for variety is the porch (half-width shed porch here; a full-width porch
or a gabled one are the next), the roof's turn (ridge front to back here; the
eaves-to-the-lane turn is a rebuild of the same slabs), the opening pattern,
the wall colour (`cottage_walls`, one of the plan's five), and on the hill the
deck and the garage storey.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_cottage"

# --- the plan's numbers ----------------------------------------------------
W, D = 6.0, 8.0            # the footprint: across the front, and deep
T = 0.20                   # wall thickness
FLOOR = 0.45               # the raised floor, the porch deck, the door's sill
EAVE = 3.15                # the roof's underside at the side walls' outer face
PITCH = math.radians(26.57)  # 6:12, the photographs' low gables
RISE = (W / 2) * math.tan(PITCH)       # the ridge over the eave
ROOF_T = 0.20              # the roof slab, perpendicular to its slope
ROOF_VT = ROOF_T / math.cos(PITCH)     # and measured vertically
EAVE_OVER, RAKE_OVER = 0.45, 0.50
RIDGE_TOP = EAVE + RISE + ROOF_VT
WALL_TOP = EAVE + 0.15     # the side walls end inside the slab
BELOW = 0.05               # how far the walls reach below the ground
CORNER = 0.26              # the corner boards, 4 cm proud of the walls
PROUD = 0.04
PORCH_W, PORCH_D = 3.6, 1.8
PORCH_X0 = -3.0            # the porch fills the west of the front
STEP_W, RISER, GOING = 1.2, 0.15, 0.30
DOOR_W, DOOR_H = 1.0, 2.1
THRESHOLD = 0.01           # a door's sill over the floor outside it (the door is shut)
POST = 0.24
RAIL_H = 0.88
GARAGE_H = 2.70            # the hillside's lower storey: the body is lifted by this
JOINT = GARAGE_H - 0.10    # where the lower storey's walls stop, under the band
HILL_X = 12.0              # where the hillside variant stands
HILL_SLOPE = 0.35          # the stage's and reference's ground, falling to +Y
DECK_D = 2.4               # the deck, and the lower storey, past the body's back wall
HILL_Z0 = -4.0             # the hillside walls' foot, buried under the deck's far edge

# the plan's five colours, `.b-cot1` to `.b-cot5`
PLAN_COLOURS = ("e8a68a", "9fc9d6", "f2d27a", "b9d39a", "e9b6c8")


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {
    "cottage_walls": srgb(PLAN_COLOURS[0]),
    "cottage_trim": srgb("f4f1ea"),
    "cottage_roof": srgb("5a5047"),
    "cottage_glass": srgb("3e5566"),
    "cottage_door": srgb("2e8b8f"),
    "cottage_porch": srgb("a67c52"),
    "cottage_base": srgb("b8b4ac"),
}


def material(name, colour=None):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour or COLOURS[name]
        bsdf.inputs["Roughness"].default_value = 0.85
    return mat


# --- building blocks -------------------------------------------------------

def finish(name, bm, coll, mats, collide=True, flat=True):
    """A bmesh into an object in `coll`, tagged, with its material slots."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if flat:
        for f in bm.faces:
            f.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    for m in mats:
        mesh.materials.append(m)
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    if not collide:
        obj["kyt_collision"] = "none"
    coll.objects.link(obj)
    return obj


def prism_bm(poly, axis, lo, hi):
    """A 2D polygon extruded along `axis` ('x' gives (y, z) pairs, 'y' gives
    (x, z), 'z' gives (x, y))."""
    bm = bmesh.new()

    def at(a, b, t):
        return {"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis]

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return bm


def box(name, coll, mat, x0, x1, y0, y1, z0, z1, collide=True):
    """An axis-aligned box, 12 triangles."""
    assert x1 > x0 and y1 > y0 and z1 > z0, (name, x0, x1, y0, y1, z0, z1)
    bm = prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)
    return finish(name, bm, coll, [mat], collide=collide)


class Top:
    """A wall's top edge: flat, or a gable following the roof's underside
    3 cm higher (inside the slab, so the two never share a plane)."""

    def __init__(self, row, flat=None, gable=None):
        self.row = row          # the z where the top row of cells begins
        self.flat = flat
        self.gable = gable      # (u of the ridge, half span, eave z)
        self.breaks = () if gable is None else (gable[0],)

    def z(self, u):
        if self.gable is None:
            return self.flat
        ridge_u, half, eave = self.gable
        return eave + (half - abs(u - ridge_u)) * math.tan(PITCH) + 0.03


def wall(name, coll, origin, u_dir, v_dir, length, z0, top, openings, base_below, mats):
    """One wall as a closed shell: two skins, ends, bottom, top, and a real
    reveal round every opening. `origin` is the outer face's start, `u_dir`
    runs along it, `v_dir` into the wall. An opening is (u0, u1, z0, z1).
    Faces below `base_below` take the second material (the base)."""
    O, U, V = Vector(origin), Vector(u_dir), Vector(v_dir)
    us, zs = {0.0, length}, {z0, top.row}
    for u0, u1, oz0, oz1 in openings:
        assert 0.0 < u0 < u1 < length and z0 < oz0 < oz1 <= top.row, (name, u0, u1, oz0, oz1)
        us.update((u0, u1))
        zs.update((oz0, oz1))
    us.update(b for b in top.breaks if 0.0 < b < length)
    us, zs = sorted(us), sorted(zs)
    nu, nz = len(us) - 1, len(zs) - 1
    bm = bmesh.new()
    verts = {}

    def vert(i, j, side):
        key = (i, j, side)
        if key not in verts:
            u = us[i]
            z = top.z(u) if j == "top" else zs[j]
            verts[key] = bm.verts.new(O + U * u + V * (T if side else 0.0) + Vector((0.0, 0.0, z)))
        return verts[key]

    def in_opening(i, j):
        um, zm = (us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
        return any(u0 < um < u1 and oz0 < zm < oz1 for u0, u1, oz0, oz1 in openings)

    def face(vs, zmid):
        f = bm.faces.new(vs)
        f.material_index = 1 if zmid < base_below else 0

    for i in range(nu):
        for j in range(nz):
            if in_opening(i, j):
                continue
            zm = (zs[j] + zs[j + 1]) / 2
            face((vert(i, j, 0), vert(i + 1, j, 0), vert(i + 1, j + 1, 0), vert(i, j + 1, 0)), zm)
            face((vert(i, j, 1), vert(i + 1, j, 1), vert(i + 1, j + 1, 1), vert(i, j + 1, 1)), zm)
        zm = zs[nz] + 0.01
        face((vert(i, nz, 0), vert(i + 1, nz, 0), vert(i + 1, "top", 0), vert(i, "top", 0)), zm)
        face((vert(i, nz, 1), vert(i + 1, nz, 1), vert(i + 1, "top", 1), vert(i, "top", 1)), zm)
        face((vert(i, 0, 0), vert(i + 1, 0, 0), vert(i + 1, 0, 1), vert(i, 0, 1)), zs[0])
        face((vert(i, "top", 0), vert(i + 1, "top", 0), vert(i + 1, "top", 1), vert(i, "top", 1)), zm)
    for i in (0, nu):
        for j in range(nz):
            face((vert(i, j, 0), vert(i, j + 1, 0), vert(i, j + 1, 1), vert(i, j, 1)), (zs[j] + zs[j + 1]) / 2)
        face((vert(i, nz, 0), vert(i, "top", 0), vert(i, "top", 1), vert(i, nz, 1)), zs[nz] + 0.01)
    for u0, u1, oz0, oz1 in openings:
        i0, i1, j0, j1 = us.index(u0), us.index(u1), zs.index(oz0), zs.index(oz1)
        zm = (oz0 + oz1) / 2
        for j in range(j0, j1):
            face((vert(i0, j, 0), vert(i0, j, 1), vert(i0, j + 1, 1), vert(i0, j + 1, 0)), zm)
            face((vert(i1, j, 0), vert(i1, j + 1, 0), vert(i1, j + 1, 1), vert(i1, j, 1)), zm)
        for i in range(i0, i1):
            face((vert(i, j0, 0), vert(i + 1, j0, 0), vert(i + 1, j0, 1), vert(i, j0, 1)), zm)
            face((vert(i, j1, 0), vert(i, j1, 1), vert(i + 1, j1, 1), vert(i + 1, j1, 0)), zm)
    return finish(name, bm, coll, mats)


def roof(name, coll, mat, y0, y1, lift):
    """The gable roof as one piece: its section, an inverted V of ROOF_T
    thickness whose underside passes through z = EAVE + lift at the side
    walls' outer faces and peaks over x = 0, extruded from rake to rake.
    One mesh, so the two slopes share nothing but their ridge line."""
    def under(x):
        return EAVE + lift + (W / 2 - abs(x)) * math.tan(PITCH)
    xe = W / 2 + EAVE_OVER
    section = [(-xe, under(-xe)), (0.0, under(0.0)), (xe, under(xe)),
               (xe, under(xe) + ROOF_VT), (0.0, under(0.0) + ROOF_VT), (-xe, under(-xe) + ROOF_VT)]
    return finish(name, prism_bm(section, "y", y0, y1), coll, [mat])


def opening_trim(prefix, coll, mat, axis, face_at, outward, a0, a1, z0, z1, sill=True):
    """Chunky craftsman casing round an opening: a head board over two jambs
    (and a sill board), 3.5 cm proud, the back sunk 1 cm into the wall, the
    jambs lapping 2 cm over the opening's edge and 2 cm into the head and sill.
    `axis` is 'x' when the opening's width runs along X (a wall facing +-Y)."""
    w = 0.12

    def part(name, a_lo, a_hi, b_lo, b_hi, sunk, proud):
        lo, hi = sorted((face_at - sunk * outward, face_at + proud * outward))
        if axis == "x":
            return box(name, coll, mat, a_lo, a_hi, lo, hi, b_lo, b_hi, collide=False)
        return box(name, coll, mat, lo, hi, a_lo, a_hi, b_lo, b_hi, collide=False)

    # every board laps 2 cm over the opening's edge, so none meets a reveal
    # edge-on; the jambs' feet go 2 cm into the sill board, or into the deck
    # or ground a door stands on; the head and sill stand a centimetre
    # prouder than the jambs and sit a half-centimetre shallower, so the
    # lapped boards share no face
    part(f"{prefix}_head", a0 - w - 0.04, a1 + w + 0.04, z1 - 0.02, z1 + w, 0.010, 0.045)
    part(f"{prefix}_jamb_a", a0 - w, a0 + 0.02, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
    part(f"{prefix}_jamb_b", a1 - 0.02, a1 + w, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
    if sill:
        part(f"{prefix}_sill", a0 - w - 0.04, a1 + w + 0.04, z0 - w, z0 + 0.02, 0.010, 0.045)


def pane(name, coll, mat, axis, face_at, outward, a0, a1, z0, z1, recess=0.08, thick=0.05, collide=True):
    """A slab set in an opening, recessed into the wall, 2 cm into the
    reveals all round."""
    lo = face_at - recess * outward
    hi = face_at - (recess + thick) * outward
    if lo > hi:
        lo, hi = hi, lo
    if axis == "x":
        return box(name, coll, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, collide=collide)
    return box(name, coll, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, collide=collide)


def rail(prefix, coll, mat, axis, at, a0, a1, z_floor, panel=0.06, cap=0.14):
    """A deck rail as a solid panel with a cap: the panel is the paint pass's
    picket cut-out later. Ends lap 2 cm into the posts either side, the cap
    a centimetre less; the panel's foot 1.5 cm into the deck (the posts go 2)."""
    z0, z1 = z_floor - 0.015, z_floor + RAIL_H
    if axis == "x":
        box(f"{prefix}_panel", coll, mat, a0, a1, at - panel / 2, at + panel / 2, z0, z1)
        box(f"{prefix}_cap", coll, mat, a0 + 0.01, a1 - 0.01, at - cap / 2, at + cap / 2, z1 - 0.03, z1 + 0.05, collide=False)
    else:
        box(f"{prefix}_panel", coll, mat, at - panel / 2, at + panel / 2, a0, a1, z0, z1)
        box(f"{prefix}_cap", coll, mat, at - cap / 2, at + cap / 2, a0 + 0.01, a1 - 0.01, z1 - 0.03, z1 + 0.05, collide=False)


# --- the cottage -----------------------------------------------------------

E_IN = CORNER / 2 - PROUD      # the walls stop this short of the corners, under the boards


def shell(coll, prefix, y_back, z_foot, tops, openings, walls_mat, base_below):
    """Four walls as closed shells between the front (y = -D/2) and `y_back`,
    their ends lost inside the corner boards. `tops` holds a Top per wall,
    `openings` per wall ('front', 'back', 'west', 'east') a list of
    (a0, a1, z0, z1) in world x (front, back) or world y (west, east) and
    absolute z. The side walls' feet are a centimetre lower than the end
    walls', because crossing shells may not share a bottom."""
    base = material("cottage_base")
    hw, hd, e = W / 2, D / 2, E_IN
    depth = y_back + hd
    spec = {
        "front": ((-hw + e, -hd, 0.0), (1, 0, 0), (0, 1, 0), W - 2 * e, lambda a: a + hw - e),
        "back": ((hw - e, y_back, 0.0), (-1, 0, 0), (0, -1, 0), W - 2 * e, lambda a: hw - e - a),
        "west": ((-hw, y_back - e, 0.0), (0, -1, 0), (1, 0, 0), depth - 2 * e, lambda a: y_back - e - a),
        "east": ((hw, -hd + e, 0.0), (0, 1, 0), (-1, 0, 0), depth - 2 * e, lambda a: a + hd - e),
    }
    for key, (origin, u_dir, v_dir, length, to_u) in spec.items():
        ops = []
        for a0, a1, z0, z1 in openings.get(key, ()):
            ua, ub = sorted((to_u(a0), to_u(a1)))
            ops.append((ua, ub, z0, z1))
        foot = z_foot - (0.01 if key in ("west", "east") else 0.0)
        wall(f"{prefix}wall_{key}", coll, origin, u_dir, v_dir, length, foot, tops[key], ops,
             base_below, [walls_mat, base])


def corner_boards(coll, prefix, y_back, z0, z1, which=("sw", "se", "nw", "ne")):
    """Corner boards 4 cm proud of both faces, their feet and tops past the
    walls' (inside the ground, the slab or the deck)."""
    trim = material("cottage_trim")
    hw, hd = W / 2, D / 2
    for sx, sy, tag in ((-1, -1, "sw"), (1, -1, "se"), (-1, 1, "nw"), (1, 1, "ne")):
        if tag not in which:
            continue
        cx = sx * (hw + PROUD - CORNER / 2)
        cy = -hd - PROUD + CORNER / 2 if sy < 0 else y_back + PROUD - CORNER / 2
        box(f"{prefix}corner_{tag}", coll, trim, cx - CORNER / 2, cx + CORNER / 2,
            cy - CORNER / 2, cy + CORNER / 2, z0, z1)


def body(coll, prefix, dz, z_foot, openings, walls_mat, base_below, board_foot=None):
    """The cottage body: four walls with gables front and back, corner
    boards, the gable roof and its ridge cap, lifted by `dz` (the
    hillside's lower storey). `board_foot` lets the corner boards run on
    down past the walls (over a lower storey)."""
    roof_mat = material("cottage_roof")
    hw, hd, e = W / 2, D / 2, E_IN
    eave, wall_top = EAVE + dz, WALL_TOP + dz
    gable = Top(row=eave, gable=(hw - e, hw, eave))
    flat = Top(row=eave, flat=wall_top)
    shell(coll, prefix, hd, z_foot, {"front": gable, "back": gable, "west": flat, "east": flat},
          openings, walls_mat, base_below)
    corner_boards(coll, prefix, hd, (z_foot if board_foot is None else board_foot) - 0.03, wall_top + 0.02)
    # the roof, with a chunky cap along the ridge; rake overhang past the
    # gables, eaves past the sides
    y0, y1 = -hd - RAKE_OVER, hd + RAKE_OVER
    roof(f"{prefix}roof", coll, roof_mat, y0, y1, dz)
    rt = RIDGE_TOP + dz
    box(f"{prefix}ridge_cap", coll, roof_mat, -0.20, 0.20, y0 - 0.02, y1 + 0.02, rt - 0.10, rt + 0.05, collide=False)


BAND_END_X = W / 2 - CORNER + PROUD + 0.02   # a band's end, 2 cm inside the corner board
BAND_END_Y = D / 2 - CORNER + PROUD + 0.02


def band(prefix, coll, mat, z, segments, tall=0.12):
    """The belly band at the floor line, 3 cm proud, 1 cm into the wall; its
    ends inside the corner boards. `segments`: (face, a0, a1)."""
    hw, hd = W / 2, D / 2
    for k, (face, a0, a1) in enumerate(segments):
        if face in ("front", "back"):
            y = -hd if face == "front" else hd
            lo, hi = (y - 0.03, y + 0.01) if face == "front" else (y - 0.01, y + 0.03)
            box(f"{prefix}band_{face}{k}", coll, mat, a0, a1, lo, hi, z - tall / 2, z + tall / 2, collide=False)
        else:
            x = -hw if face == "west" else hw
            lo, hi = (x - 0.03, x + 0.01) if face == "west" else (x - 0.01, x + 0.03)
            box(f"{prefix}band_{face}{k}", coll, mat, lo, hi, a0, a1, z - tall / 2, z + tall / 2, collide=False)


def build_court(coll, prefix="", walls_mat=None):
    """The court cottage at the origin: body, porch, steps, openings."""
    walls_mat = walls_mat or material("cottage_walls")
    trim, glass, door, porch, base = (material(n) for n in
                                      ("cottage_trim", "cottage_glass", "cottage_door", "cottage_porch", "cottage_base"))
    hw, hd = W / 2, D / 2
    head = FLOOR + DOOR_H                      # one head line for door and windows
    sill = FLOOR + 0.90
    door_x = (-1.3, -0.3)
    # a door's sill stands THRESHOLD above the floor it opens onto: the deck
    # laps into the wall at floor level and may not share the sill's plane
    openings = {
        "front": [(door_x[0], door_x[1], FLOOR + THRESHOLD, head), (-2.5, -1.7, head - 1.0, head), (1.0, 2.6, sill, head)],
        "back": [(-2.2, -1.0, sill, head), (1.0, 2.2, sill, head)],
        "west": [(-2.4, -1.2, sill, head), (1.2, 2.4, sill, head)],
        "east": [(-2.4, -1.2, sill, head), (1.2, 2.4, sill, head)],
    }
    body(coll, prefix, 0.0, -BELOW, openings, walls_mat, FLOOR)
    # casings, panes and the door
    for face, axis, at, out in (("front", "x", -hd, -1), ("back", "x", hd, 1), ("west", "y", -hw, -1), ("east", "y", hw, 1)):
        for k, (a0, a1, z0, z1) in enumerate(openings[face]):
            is_door = face == "front" and k == 0
            opening_trim(f"{prefix}{face}{k}_trim", coll, trim, axis, at, out, a0, a1, z0, z1, sill=not is_door)
            pane(f"{prefix}{face}{k}_{'door' if is_door else 'pane'}", coll, door if is_door else glass,
                 axis, at, out, a0, a1, z0, z1)
    # the belly band at the floor line, clear of the porch
    band(prefix, coll, trim, FLOOR, [("front", PORCH_X0 + PORCH_W + 0.1, BAND_END_X),
                                     ("back", -BAND_END_X, BAND_END_X),
                                     ("west", -BAND_END_Y, BAND_END_Y),
                                     ("east", -BAND_END_Y, BAND_END_Y)])
    # the porch: a deck 2 cm into the wall, posts at its front corners, a
    # shed roof off the gable, rails with newels either side of the steps
    px0, px1 = PORCH_X0 - 0.06, PORCH_X0 + PORCH_W + 0.06
    py0, py1 = -hd - PORCH_D - 0.06, -hd + 0.02
    box(f"{prefix}porch_deck", coll, porch, px0, px1, py0, py1, -0.10, FLOOR)
    roof_z_wall, roof_z_edge = 3.0, 2.6
    edge_y = py0 - 0.30
    for tag, x in (("w", px0 + 0.03), ("e", px1 - 0.03 - POST)):
        box(f"{prefix}porch_post_{tag}", coll, trim, x, x + POST, py0 + 0.03, py0 + 0.03 + POST, FLOOR - 0.02, 2.75)
    bm = bmesh.new()
    verts = [bm.verts.new(v) for v in ((px0 - 0.30, edge_y, roof_z_edge), (px1 + 0.30, edge_y, roof_z_edge),
                                       (px1 + 0.30, -hd + 0.10, roof_z_wall), (px0 - 0.30, -hd + 0.10, roof_z_wall))]
    up = Vector((0, 0, 0.18))
    tops = [bm.verts.new(v.co + up) for v in verts]
    bm.faces.new(verts)
    bm.faces.new(list(reversed(tops)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((verts[i], verts[j], tops[j], tops[i]))
    finish(f"{prefix}porch_roof", bm, coll, [material("cottage_roof")])
    sx0, sx1 = door_x[0] - (STEP_W - DOOR_W) / 2, door_x[1] + (STEP_W - DOOR_W) / 2
    post_y = py0 + 0.03 + POST / 2
    # side rails from inside the posts to 3 cm into the wall (the deck goes 2)
    rail(f"{prefix}porch_rail_w", coll, trim, "y", px0 + 0.03 + POST / 2, py0 + POST + 0.01, -hd + 0.03, FLOOR)
    rail(f"{prefix}porch_rail_e", coll, trim, "y", px1 - 0.03 - POST / 2, py0 + POST + 0.01, -hd + 0.03, FLOOR)
    for tag, x in (("w", sx0 - POST), ("e", sx1)):
        box(f"{prefix}porch_newel_{tag}", coll, trim, x, x + POST, post_y - POST / 2, post_y + POST / 2,
            FLOOR - 0.02, FLOOR + RAIL_H + 0.12)
    rail(f"{prefix}porch_rail_fw", coll, trim, "x", post_y, px0 + 0.03 + POST - 0.02, sx0 - POST + 0.02, FLOOR)
    rail(f"{prefix}porch_rail_fe", coll, trim, "x", post_y, sx1 + POST - 0.02, px1 - 0.03 - POST + 0.02, FLOOR)
    # the steps: the treads are one stepped block, scenery (no collision),
    # lapping 2 cm into the deck; the narrow ramp on the nosing line is the
    # floor, flush with the deck's edge and ending inside the deck, its foot
    # 2 cm below the treads' so the two share no plane
    n = round(FLOOR / RISER)
    front = py0
    foot = front - n * GOING
    profile = [(foot, -BELOW)]
    for k in range(1, n):
        profile += [(foot + (k - 1) * GOING, k * RISER), (foot + k * GOING, k * RISER)]
    profile += [(front + 0.02, (n - 1) * RISER), (front + 0.02, -BELOW)]
    finish(f"{prefix}steps", prism_bm(profile, "x", sx0, sx1), coll, [porch], collide=False)
    ramp = [(foot - 0.05, -BELOW - 0.02), (foot, 0.0), (front, FLOOR), (front + 0.06, -BELOW - 0.02)]
    finish(f"{prefix}step_ramp", prism_bm(ramp, "x", sx0 + 0.10, sx1 - 0.10), coll, [porch])
    # and the park's nosing strips, 3 cm proud of the ramp at each tread's
    # edge, scenery, so the flight reads as steps at any distance
    for k in range(1, n):
        nose = foot + (k - 1) * GOING
        box(f"{prefix}step_nosing_{k}", coll, porch, sx0 + 0.005, sx1 - 0.005, nose - 0.01, nose + 0.05,
            k * RISER - 0.01, k * RISER + 0.03, collide=False)


def build_hillside(coll, prefix="hill_", walls_mat=None):
    """The hillside cottage, the Avila photograph's massing: the court
    cottage's body over a lower storey that runs on DECK_D further down the
    slope, the deck to the view on that storey's roof, the garage and the
    front door at the street. Built in place at HILL_X (its ground: z = 0 at
    the street, falling toward +Y). The lower storey's walls stop at JOINT
    and the body's start 5 cm higher; the belly band covers the joint and
    the front corner boards run the full height, so the two shells share no
    face."""
    walls_mat = walls_mat or material("cottage_walls")
    trim, glass, door, porch = (material(n) for n in ("cottage_trim", "cottage_glass", "cottage_door", "cottage_porch"))
    hw, hd = W / 2, D / 2
    dz = GARAGE_H
    floor = FLOOR + dz
    head, sill = floor + DOOR_H, floor + 0.90
    y_back = hd + DECK_D
    # the lower storey: garage and front door to the street; downhill, where
    # the ground falls HILL_SLOPE * (D + DECK_D) = 3.6 m across the depth, its
    # exposed face is two storeys under the deck, with windows to the view
    # in both, and foundation only below the lowest row
    garage = (0.1, 2.7, THRESHOLD, 2.2)
    entry = (-2.3, -1.3, THRESHOLD, 2.1)
    low_row = (-2.0, -0.8)
    lower = {
        "front": [garage, entry],
        "back": [(-1.6, 1.6, 0.6, 1.8), (-1.6, 1.6, *low_row)],
        "west": [(3.4, 4.6, 0.6, 1.8), (0.6, 1.8, 0.6, 1.8), (3.4, 4.6, *low_row)],
        "east": [(3.4, 4.6, 0.6, 1.8), (0.6, 1.8, 0.6, 1.8), (3.4, 4.6, *low_row)],
    }
    # the side walls' tops a centimetre lower than the end walls', as their
    # feet are: four flat shells cross in the corners
    ends, sides = Top(row=JOINT - 0.3, flat=JOINT), Top(row=JOINT - 0.3, flat=JOINT - 0.01)
    shell(coll, prefix + "lower_", y_back, HILL_Z0, {"front": ends, "back": ends, "west": sides, "east": sides},
          lower, walls_mat, low_row[0] - 0.6)
    corner_boards(coll, prefix + "lower_", y_back, HILL_Z0 - 0.03, JOINT + 0.02, which=("nw", "ne"))
    # the body on it, its front corner boards running down to the ground
    slider = (-0.9, 0.9, floor + THRESHOLD, head)
    upper = {
        "front": [(-2.2, -1.0, sill, head), (1.0, 2.2, sill, head)],
        "back": [slider, (1.5, 2.5, sill, head)],
        "west": [(-2.4, -1.2, sill, head), (1.2, 2.4, sill, head)],
        "east": [(-2.4, -1.2, sill, head), (1.2, 2.4, sill, head)],
    }
    body(coll, prefix, dz, JOINT + 0.05, upper, walls_mat, 0.0, board_foot=HILL_Z0)
    faces = (("front", "x", -hd, -1), ("back", "x", hd, 1), ("west", "y", -hw, -1), ("east", "y", hw, 1))
    for storey, openings in (("lower_", lower), ("", upper)):
        for face, axis, at, out in faces:
            if storey == "lower_" and face == "back":
                at = y_back
            for k, (a0, a1, z0, z1) in enumerate(openings[face]):
                kind = "pane"
                if storey == "lower_" and face == "front":
                    kind = ("garage_door", "door")[k]
                elif storey == "" and face == "back" and k == 0:
                    kind = "slider"
                opening_trim(f"{prefix}{storey}{face}{k}_trim", coll, trim, axis, at, out, a0, a1, z0, z1,
                             sill=kind == "pane")
                mat = {"garage_door": trim, "door": door, "slider": glass, "pane": glass}[kind]
                pane(f"{prefix}{storey}{face}{k}_{kind}", coll, mat, axis, at, out, a0, a1, z0, z1,
                     recess=0.10 if kind == "garage_door" else 0.08)
    # a hood over the entry, lapped into the wall
    box(f"{prefix}entry_hood", coll, trim, entry[0] - 0.25, entry[1] + 0.25, -hd - 0.70, -hd + 0.02, 2.36, 2.48, collide=False)
    # the belly band over the joint of the two storeys
    band(prefix, coll, trim, JOINT + 0.04, [("front", -BAND_END_X, BAND_END_X),
                                            ("west", -BAND_END_Y, BAND_END_Y),
                                            ("east", -BAND_END_Y, BAND_END_Y)], tall=0.20)
    # the deck: the lower storey's roof as a chunky floor plate, 5 cm proud
    # of its walls, flush with the floor, 2 cm into the body's back wall;
    # short posts at its outer corners and rails on three sides
    dx0, dx1 = -hw - 0.05, hw + 0.05
    dy0, dy1 = hd - 0.02, y_back + 0.05
    box(f"{prefix}deck", coll, porch, dx0, dx1, dy0, dy1, JOINT - 0.05, floor)
    for tag, x in (("w", dx0 + 0.04), ("e", dx1 - 0.04 - POST)):
        box(f"{prefix}deck_post_{tag}", coll, trim, x, x + POST, dy1 - 0.04 - POST, dy1 - 0.04,
            floor - 0.02, floor + RAIL_H + 0.12)
    post_y = dy1 - 0.04 - POST / 2
    rail(f"{prefix}deck_rail_back", coll, trim, "x", post_y, dx0 + 0.04 + POST - 0.02, dx1 - 0.04 - POST + 0.02, floor)
    # the side rails 2 cm in from the posts' centres: their panels then clear
    # the body's back wall's end face (x = +-2.91) where they enter the wall
    rail(f"{prefix}deck_rail_w", coll, trim, "y", dx0 + 0.06 + POST / 2, hd - 0.03, post_y - POST / 2 + 0.02, floor)
    rail(f"{prefix}deck_rail_e", coll, trim, "y", dx1 - 0.06 - POST / 2, hd - 0.03, post_y - POST / 2 + 0.02, floor)


# --- reference ---------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm = prism_bm(ring, "z", 0.0, height - 0.40)     # the body, its foot on the ground
    body_verts = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:                                # the head, its crown at `height`
        if v not in body_verts:
            v.co.z += height - 0.17
    obj = finish(name, bm, coll, [mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0))], collide=False, flat=False)
    obj.location = (x, y, z)
    return obj


def outline(name, coll, x0, x1, y0, y1, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    for i in range(4):
        bm.edges.new((vs[i], vs[(i + 1) % 4]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def hill_ground_z(y_local):
    return 0.0 if y_local <= -D / 2 else -HILL_SLOPE * (y_local + D / 2)


def slope_mesh(name, coll, mat, x0, x1, y0, y1, ox=0.0, thick=None):
    """The hillside's ground: the street level to the front wall, then the
    slope; as a thin solid when `thick` is given (for renders)."""
    ys = sorted({y0, -D / 2, y1})
    bm = bmesh.new()
    rows = [[bm.verts.new((ox + x, y, hill_ground_z(y))) for x in (x0, x1)] for y in ys]
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    if thick:
        under = [[bm.verts.new((ox + x, y, hill_ground_z(y) - thick)) for x in (x0, x1)] for y in ys]
        for a, b in zip(under, under[1:]):
            bm.faces.new((b[0], b[1], a[1], a[0]))
        for k in range(len(ys)):
            if k + 1 < len(ys):
                bm.faces.new((rows[k][0], under[k][0], under[k + 1][0], rows[k + 1][0]))
                bm.faces.new((rows[k][1], rows[k + 1][1], under[k + 1][1], under[k][1]))
        bm.faces.new((rows[0][0], rows[0][1], under[0][1], under[0][0]))
        bm.faces.new((rows[-1][0], under[-1][0], under[-1][1], rows[-1][1]))
    return finish(name, bm, coll, [mat], collide=False)


def build_reference(reference):
    outline("footprint_8x6_court", reference, -W / 2, W / 2, -D / 2, D / 2)
    outline("footprint_8x6_hillside", reference, HILL_X - W / 2, HILL_X + W / 2, -D / 2, D / 2)
    figure("figure_1p7m", reference, -4.6, -6.2)
    slope_mesh("hillside_ground_reference", reference, material("reference_ground", (0.35, 0.45, 0.25, 1.0)),
               -8.0, 8.0, -12.0, 12.0, ox=HILL_X)
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        reference.objects.link(marker)


# --- checks ------------------------------------------------------------------

def triangles(objs):
    total = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            total += len(o.data.loop_triangles)
    return total


def coplanar_pairs(objs, tol=1e-4):
    """Pairs of faces from different objects lying in one plane and
    overlapping in area (by their bounds in the plane): the z-fights."""
    faces = []
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        for p in o.data.polygons:
            n = (mw.to_3x3() @ p.normal).normalized()
            pts = [mw @ o.data.vertices[i].co for i in p.vertices]
            d = n.dot(pts[0])
            # a 2D frame in the plane
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            us = [q.dot(e1) for q in pts]
            vs = [q.dot(e2) for q in pts]
            faces.append((o.name, n, d, min(us), max(us), min(vs), max(vs)))
    found = []
    for i in range(len(faces)):
        oi, ni, di, u0, u1, v0, v1 = faces[i]
        for j in range(i + 1, len(faces)):
            oj, nj, dj, w0, w1, x0, x1 = faces[j]
            if oi == oj:
                continue
            same = (ni - nj).length < 1e-3 and abs(di - dj) < tol
            flipped = (ni + nj).length < 1e-3 and abs(di + dj) < tol
            if not (same or flipped):
                continue
            if flipped:
                # the frame's e1 is the same for -n and e2 is negated, so j's
                # v bounds mirror
                x0, x1 = -x1, -x0
            ou = min(u1, w1) - max(u0, w0)
            ov = min(v1, x1) - max(v0, x0)
            if ou > 1e-3 and ov > 1e-3:
                found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def report(coll, label):
    bpy.context.view_layer.update()
    objs = [o for o in coll.all_objects if o.type == "MESH"]
    tris = triangles(objs)
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    print(f"beach_cottage: {label}: {len(objs)} parts, {tris} triangles, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, z {min(zs):.2f}..{max(zs):.2f}")
    return tris


# --- renders -----------------------------------------------------------------

def render(folder):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = False
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    ground = mat("_ground", (0.36, 0.44, 0.26))
    lane = mat("_lane", (0.30, 0.30, 0.32))
    ink = mat("_ink", (0.02, 0.02, 0.02))
    # the court's flat ground and its lane 2.5 m off the front; the hillside's
    # slope and its street: one set shows per shot
    flat = [box("_ground_court", stage, ground, -60, 60, -60, 60, -0.30, -0.01, collide=False),
            box("_lane", stage, lane, -60, 60, -11.5, -6.5, -0.30, 0.0, collide=False)]
    # the slope's west end sits just in front of the side elevation's
    # camera, deep, so that view shows the ground as a cut section
    hilly = [slope_mesh("_ground_hill", stage, ground, -29.9, 40.0, -40.0, 40.0, ox=HILL_X, thick=8.0),
             box("_ground_hill_street", stage, lane, HILL_X - 40, HILL_X + 40, -9.5, -5.5, -0.30, 0.005, collide=False)]

    def grounds(hill):
        for o in flat:
            o.hide_render = hill
        for o in hilly:
            o.hide_render = not hill

    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    figures = []
    for k, (x, y) in enumerate(((-4.6, -6.2), (HILL_X - 4.5, -6.0), (HILL_X + 4.6, 9.0))):
        figures.append(figure(f"_figure_{k}", stage, x, y, hill_ground_z(y) if k == 2 else 0.0, mat=fig))

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.45, -0.70, 0.55)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 48
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False

    def shoot(name, eye, target, lens=32, size=(1600, 1000), ortho=None):
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 500
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"beach_cottage: rendered {scene.render.filepath}")

    # the court cottage from across the lane at eye height, and its elevation
    grounds(False)
    bpy.data.collections["authored"].hide_render = True
    shoot("court_three_quarter", (8.0, -13.0, 1.6), (0.0, -2.0, 2.2), lens=30)
    shoot("court_front_elevation", (0.0, -40.0, 2.4), (0.0, 0.0, 2.4), ortho=9.5)
    shoot("court_side_elevation", (-40.0, 0.0, 2.4), (0.0, 0.0, 2.4), ortho=12.0)
    # the hillside cottage from downhill and from its street
    grounds(True)
    bpy.data.collections["authored"].hide_render = False
    bpy.data.collections["export"].hide_render = True
    shoot("hillside_from_downhill", (HILL_X + 10.0, 22.0, -2.5), (HILL_X, 2.0, 2.4), lens=30)
    shoot("hillside_from_street", (HILL_X - 8.0, -13.5, 1.6), (HILL_X, -2.0, 3.2), lens=28)
    shoot("hillside_side_elevation", (HILL_X - 30.0, 1.0, 1.4), (HILL_X, 1.0, 1.4), ortho=17.0)
    # plans with a metre grid and a 5 m bar
    grounds(False)
    bpy.data.collections["export"].hide_render = False
    bpy.data.collections["authored"].hide_render = True
    for gx in range(-7, 8):
        box(f"_grid_x{gx}", stage, ink, gx - 0.015, gx + 0.015, -9.0, 7.0, -0.012, -0.004, collide=False)
    for gy in range(-9, 8):
        box(f"_grid_y{gy}", stage, ink, -7.0, 7.0, gy - 0.015, gy + 0.015, -0.012, -0.004, collide=False)
    box("_bar", stage, ink, -6.5, -1.5, -7.9, -7.7, -0.012, 0.03, collide=False)
    for k in range(6):
        box(f"_bar_tick{k}", stage, ink, -6.5 + k - 0.03, -6.5 + k + 0.03, -8.2, -7.4, -0.012, 0.03, collide=False)
    curve = bpy.data.curves.new("_label", "FONT")
    curve.body = "5 m bar, 1 m grid"
    curve.size = 0.5
    curve.align_x = "LEFT"
    label = bpy.data.objects.new("_label", curve)
    label.location = (-1.0, -8.0, 0.02)
    curve.materials.append(ink)
    stage.objects.link(label)
    shoot("court_plan", (0.0, -1.0, 60.0), (0.0, -1.0, 0.0), size=(1200, 1200), ortho=15.0)
    grounds(True)
    bpy.data.collections["authored"].hide_render = False
    bpy.data.collections["export"].hide_render = True
    for o in list(stage.objects):
        if o.name.startswith(("_grid", "_bar", "_label")):
            o.location.x += HILL_X
    shoot("hillside_plan", (HILL_X, -1.0, 60.0), (HILL_X, -1.0, 0.0), size=(1200, 1200), ortho=15.0)
    for o in list(stage.objects):
        if o.name.startswith(("_grid", "_bar", "_label")):
            bpy.data.objects.remove(o, do_unlink=True)
    # the court as a row: five cottages 1.5 m apart in the plan's five colours
    grounds(False)
    bpy.data.collections["authored"].hide_render = True
    row = bpy.data.collections.new("_row")
    stage.children.link(row)
    pitch = W + 1.5
    for k, hex6 in enumerate(PLAN_COLOURS):
        one = bpy.data.collections.new(f"_row_{k}")
        row.children.link(one)
        build_court(one, prefix=f"_row{k}_", walls_mat=mat(f"_row_walls_{k}", srgb(hex6)[:3]))
        for o in one.objects:
            o.location.x += (k - 2) * pitch
    for o in figures:
        bpy.data.objects.remove(o, do_unlink=True)
    figure("_figure_row", stage, -9.0, -8.0, mat=fig)
    shoot("court_row_five", (-6.0, -17.5, 1.6), (6.0, -1.0, 2.2), lens=24)
    shoot("court_row_five_street", (-21.0, -9.0, 1.6), (12.0, -5.0, 2.2), lens=28)


# --- main ----------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != "beach_cottage":
        raise SystemExit(f"beach_cottage: open beach_cottage.blend, not {name}")
    export, authored, reference = (bpy.data.collections[n] for n in ("export", "authored", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"beach_cottage: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("hillside_variant", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    hill = bpy.data.collections.new("hillside_variant")
    authored.children.link(hill)
    build_court(export)
    build_hillside(hill)
    for o in hill.objects:
        o.location.x += HILL_X
    build_reference(reference)

    court_tris = report(export, "court cottage (export)")
    hill_tris = report(hill, "hillside cottage (authored/hillside_variant)")
    print(f"beach_cottage: footprint {W:.1f} x {D:.1f} m, walls {T:.2f} m thick, floor {FLOOR:.2f}, "
          f"eave {EAVE:.2f}, ridge top {RIDGE_TOP:.2f} (pitch {math.degrees(PITCH):.1f} deg), "
          f"porch {PORCH_W:.1f} x {PORCH_D:.1f} m at {FLOOR:.2f}; hillside floor {FLOOR + GARAGE_H:.2f}, "
          f"eave {EAVE + GARAGE_H:.2f}, ridge top {RIDGE_TOP + GARAGE_H:.2f}, deck {W:.1f} x {DECK_D:.1f} m")
    for label, coll in (("court", export), ("hillside", hill)):
        pairs = coplanar_pairs(list(coll.all_objects))
        print(f"beach_cottage: {label}: {len(pairs)} coplanar overlapping face pairs" +
              ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("beach_cottage: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1])


main()
