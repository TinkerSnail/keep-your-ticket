"""The town's cottage kit, blocked out (2026-10-02): the everyday one-storey
houses of the South Shore plan's family B, one body with the roof, porch,
windows and trim swapped, each variant read off one of Christina's photos in
`documentation/reference/houses/`.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/cottage_kit.blend --python tools/blender/cottage_kit.py -- \\
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, eight variants into `export`, each marked
`kyt_variant` so Send writes each as a prop of its own
(`cottage_kit_<variant>`), the way `plaza_street.py` lays out the park lamp's
three: the first, `classic`, stands in `export` itself and the others in
`export/variant_<name>` with their eyes shut, all at the origin together.

- `classic`   `classic_little_cottage.png`: steep grey gable to the street
              with a sunburst in the peak, a brick chimney on the ridge, tall
              double-hung windows, the side door under a shed hood.
- `bungalow`  `teal_trim_bungalow.png`: low front gable, deep eaves on rafter
              tails with brackets, an enclosed glazed sun porch at the front
              corner, the door in a covered entry beside it, chunky trim.
- `hip`       `blue_hip_roof_cottage.png`: a low side gable, the ridge along
              the street with a louvred vent in each gable end, a small front
              gable with a round plaque over the stoop, white-railed stoop
              (named for the photo; the roof was read as a hip at first).
- `hip_garage` the hip cottage's detached one-car garage, 3.5 x 6 m, gable
              to the drive, painted to match.
- `glass_gable` `glass_gable_shingle_cottage.webp`: steep front gable glazed
              up into the peak over a shingled sill band, deep eaves on rafter
              tails, a knee brace at each gable corner, the door at the right.
- `porch`     `pink_hammock_cottage.webp`: front gable with a round window,
              a full-width porch on chunky posts under its own low roof, a
              hammock slung across it, shutters.
- `log`       `log_cabin_cottage.webp`: 10 m wide as the photo (Christina:
              "go wide"), a 6.5 m main gable beside a 3.5 m side block whose
              lower gable comes forward, the tall fieldstone chimney between
              them, chunky log ends at the corners (the logs are paint).
- `l_ranch`   `blue_l_shaped_ranch.png`: 8 m wide: a gabled wing forward to
              the street, flush with the block's end, the rest set back under
              a low side gable with a porch along it.
- `classic_gable` the classic again with its front door on the sunburst
              gable under a hood of its own, up two steps, and the side door
              moved back along the west side (the either/or became a variant),
              in butter yellow with white trim and a teal door, on stand-ins
              of its own (`cottage_kit_classic_gable_<surface>`).

**Frame.** Real metres, Z up, the ground at z = 0, the origin at the body's
footprint centre. The front faces -Y here, which the glTF export (`send.py`,
`export_yup=True`) turns into Godot's +Z, the project's "facing +Z". The body
is 6 m across (X) by 8 m deep (Y) as `beach_cottage` has it, so a gable faces
the street on a 9 m lot with the driveway beside it; the ranch is 8 m wide
and the log cabin 10 m, each wanting a wider lot (11 and 13 m with a drive).

**Contract** (the plan's decision 6, enclosing): public faces, porches and
windows, no interior. Every opening is a real hole through a wall of real
thickness; the door and the panes are solid slabs set in the holes. Every door
opens onto a floor at a flush threshold (the leaf's sill THRESHOLD above the
deck or slab outside it). Steps follow the park's stair rule: a narrow ramp is
the floor (`tools/gen_props.gd`, `_flight_ramp`), the treads are scenery
showing past it and do not collide (`kyt_collision = none`). No two shapes
share a plane: a part that meets another laps 2 cm into it or stands proud.
`report()` scans every variant for coplanar overlapping face pairs.

**Style.** Cartoony-ish as the rest of the park: few big pieces, chunky trim,
roof and posts; busy is the failure mode. Battens, laps, shingles, logs and
window bars are painting. Materials are flat stand-ins named
`cottage_kit_<surface>`, the wall and trim colours per photo.

Everything the tool makes carries `kyt_cottage_kit`, so a rerun removes and
rebuilds its own work and keeps anything of hers; `export` holding anything
untagged refuses without `--replace`. `--save` writes the file; `--render`
shoots after the save, so no camera, light or stage reaches the file.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_cottage_kit"
VARIANTS = ("classic", "bungalow", "hip", "hip_garage", "glass_gable", "porch", "log", "l_ranch", "classic_gable")

# --- the kit's constants ---------------------------------------------------
W, D = 6.0, 8.0            # the body: across the front, and deep
HW, HD = W / 2, D / 2
T = 0.20                   # wall thickness
BELOW = 0.05               # how far the walls reach below the ground
ROOF_T = 0.20              # the roof slab, perpendicular to its slope
CORNER = 0.26              # the corner boards, 4 cm proud of the walls
PROUD = 0.04
E_IN = CORNER / 2 - PROUD  # the walls stop this short of the corners, under the boards
WALL_OVER = 0.15           # the side walls end this far inside the roof slab
RISER, GOING = 0.15, 0.30
DOOR_W, DOOR_H = 1.0, 2.1
THRESHOLD = 0.01           # a door's sill over the floor outside it (the door is shut)
POST = 0.22                # a chunky porch post
RAIL_H = 0.88
TRIM_W = 0.12              # casing boards
FIGURE_H = 1.70

# each variant's numbers, read off its photo; every one is a guess to be corrected
CLASSIC = dict(pitch=42.0, eave=2.55, floor=0.30, eave_over=0.25, rake_over=0.45,
               chimney=(0.6, 0.6, 1.9, 0.9),        # across, deep, y on the ridge, height over the ridge
               hood=(1.6, 0.8), door_y=(-2.3, -1.3),  # the shed hood's width and reach; the side door along Y
               gable_door_x=(-0.5, 0.5), gable_side_door_y=(1.1, 2.1))  # classic_gable: the front door on the gable, the side door further back
BUNGALOW = dict(pitch=18.43, eave=2.60, floor=0.30, eave_over=0.70, rake_over=0.60,
                porch=(3.6, 1.8), sill=0.85, head=2.30, tail_pitch=0.60)  # the sun porch across and deep
HIP = dict(pitch=18.43, eave=2.60, floor=0.60, over=0.45,   # a low side gable, the ridge along the street (Christina, 2 Oct 2026), gable ends both sides
           hood=(1.8, 1.0, 20.0, 2.70), vent=(0.50, 0.40, 0.55),   # hood: across, reach, pitch, eave; vent: across, tall, below the ridge
           stoop=(1.6, 1.2), flue=(0.35, 1.5, 0.9))  # the stoop's width and depth; the flue across, y, height over the roof
HIP_GARAGE = dict(w=3.5, d=6.0, pitch=18.43, eave=2.40, eave_over=0.30, rake_over=0.35, door=(2.4, 2.1))
GLASS = dict(pitch=33.69, eave=2.50, floor=0.0, eave_over=0.75, rake_over=0.60, sill=0.90, head=2.10,
             tail_pitch=0.60, mullions=(-1.0, 0.4, 1.8))  # the glass wall's vertical bars, x
PORCH = dict(pitch=30.0, eave=2.90, floor=0.45, eave_over=0.40, rake_over=0.45, porch_d=2.1,
             porch_roof=(2.60, 2.35), window_r=0.40, window_z=3.70, hammock=(1.55, 0.80))  # roof at the wall and the edge; hammock ends and middle
LOG = dict(pitch=26.57, eave=2.50, floor=0.15, eave_over=0.45, rake_over=0.50,
           main=(-1.5, 5.0), wing=(-5.0, -1.5, 1.6),             # 10 m across (Christina: "go wide"): the main block's x, the side block's x and its reach forward
           chimney=(-1.35, -0.15, 0.70, 1.0), log_r=0.14, course=0.28)  # chimney x0, x1, deep, height over the ridge
RANCH = dict(w=8.0, pitch=18.43, eave=2.55, floor=0.15, eave_over=0.45, rake_over=0.45,
             wing=(0.55, 4.0, -4.0, -1.0), block=(-4.0, 4.0, -1.0, 4.0), porch_d=1.9, porch_pitch=12.0)  # the wing flush with the block's end (Christina)

PLAN_COLOURS = ("e8a68a", "9fc9d6", "f2d27a", "b9d39a", "e9b6c8")   # the plan's `.b-cot1` to `.b-cot5`


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {
    "cottage_kit_walls": srgb("bcd6e4"),          # the classic's pale blue
    "cottage_kit_walls_white": srgb("f1ede3"),    # the bungalow's lap siding
    "cottage_kit_walls_sky": srgb("62aee6"),      # the hip cottage, the glass gable's shingle
    "cottage_kit_walls_pink": srgb("f06d9a"),
    "cottage_kit_walls_log": srgb("5b3b2b"),
    "cottage_kit_walls_blue": srgb("4a78b0"),     # the ranch's medium blue
    "cottage_kit_walls_batten": srgb("c9b8a0"),   # the log cabin's board-and-batten gable
    "cottage_kit_trim": srgb("f4f1ea"),
    "cottage_kit_trim_teal": srgb("1c9fb3"),
    "cottage_kit_trim_blue": srgb("2a5c9c"),
    "cottage_kit_trim_grey": srgb("7f98aa"),
    "cottage_kit_trim_orange": srgb("f2a233"),
    "cottage_kit_trim_mint": srgb("7fd0b0"),
    "cottage_kit_roof": srgb("5a5047"),           # grey shingle
    "cottage_kit_roof_shake": srgb("6e5a3c"),
    "cottage_kit_roof_metal": srgb("8b9196"),
    "cottage_kit_glass": srgb("3e5566"),
    "cottage_kit_door": srgb("2e8b8f"),
    "cottage_kit_door_cobalt": srgb("1f3fbf"),
    "cottage_kit_porch": srgb("a67c52"),
    "cottage_kit_base": srgb("b8b4ac"),
    "cottage_kit_brick": srgb("9a4b3b"),
    "cottage_kit_stone": srgb("a9a08f"),
    "cottage_kit_fabric": srgb("e89ab4"),
    "cottage_kit_concrete": srgb("c6c2ba"),
}


def material(name, colour=None):
    """A flat stand-in by name. The colour is set on every build, on an
    existing material too, so the builder's constants always win: a saved
    file had kept `classic_gable`'s door teal through a recolour (3 Oct)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = colour or COLOURS[name]
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def own_material(variant, surface, like=None, hex6=None):
    """A stand-in of one variant's own, `cottage_kit_<variant>_<surface>`,
    in the colour of the shared material `like` or of `hex6`, so recolouring
    it touches no other variant."""
    return material(f"cottage_kit_{variant}_{surface}", srgb(hex6) if hex6 else COLOURS[like])


# --- where parts go: the collection, variant and name prefix being built ----
_ctx = {"coll": None, "variant": None, "prefix": ""}


def building(coll, variant, prefix=None):
    _ctx.update(coll=coll, variant=variant, prefix=f"{variant}_" if prefix is None else prefix)


# --- building blocks -------------------------------------------------------

def finish(name, bm, mats, collide=True, flat=True):
    """A bmesh into an object in the current collection, tagged and marked
    with the current variant, with its material slots."""
    mesh = bpy.data.meshes.new(_ctx["prefix"] + name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if flat:
        for f in bm.faces:
            f.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(_ctx["prefix"] + name, mesh)
    for m in mats:
        mesh.materials.append(m)
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    if _ctx["variant"]:
        obj["kyt_variant"] = _ctx["variant"]
    if not collide:
        obj["kyt_collision"] = "none"
    _ctx["coll"].objects.link(obj)
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


def box(name, mat, x0, x1, y0, y1, z0, z1, collide=True):
    """An axis-aligned box, 12 triangles."""
    assert x1 > x0 and y1 > y0 and z1 > z0, (name, x0, x1, y0, y1, z0, z1)
    return finish(name, prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1), [mat], collide=collide)


def bar(name, mat, axis, p0, p1, width, lo, hi, collide=False):
    """A straight bar between two points of the section plane ('y': (x, z)
    pairs), `width` across, extruded along `axis` from `lo` to `hi`: a
    sunburst ray, a knee brace, a sloped handrail. Its ends are square to
    its run."""
    (a0, b0), (a1, b1) = p0, p1
    d = Vector((a1 - a0, b1 - b0)).normalized()
    n = Vector((-d.y, d.x)) * (width / 2)
    poly = [(a0 + n.x, b0 + n.y), (a1 + n.x, b1 + n.y), (a1 - n.x, b1 - n.y), (a0 - n.x, b0 - n.y)]
    return finish(name, prism_bm(poly, axis, lo, hi), [mat], collide=collide)


def slab(name, mat, corners, thick, collide=True):
    """A flat slab whose top is the quad `corners` ((x, y, z) in order) and
    whose underside is `thick` straight below it: a shed roof, a hood."""
    bm = bmesh.new()
    tops = [bm.verts.new(c) for c in corners]
    unders = [bm.verts.new((c[0], c[1], c[2] - thick)) for c in corners]
    bm.faces.new(tops)
    bm.faces.new(list(reversed(unders)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((tops[i], tops[j], unders[j], unders[i]))
    return finish(name, bm, [mat], collide=collide)


def cylinder_bm(axis, c_a, c_b, r, lo, hi, sides=8):
    """An `sides`-gon tube along `axis`, centred at (c_a, c_b) in the section plane."""
    ring = [(c_a + r * math.cos(math.tau * (i + 0.5) / sides), c_b + r * math.sin(math.tau * (i + 0.5) / sides))
            for i in range(sides)]
    return prism_bm(ring, axis, lo, hi)


def disc(name, mat, axis, c_a, c_b, r, lo, hi, sides=12, collide=False, half=False):
    """A flat disc (or the upper half of one) standing proud of a wall."""
    if half:
        ring = [(c_a + r * math.cos(math.pi * i / sides), c_b + r * math.sin(math.pi * i / sides)) for i in range(sides + 1)]
    else:
        ring = [(c_a + r * math.cos(math.tau * i / sides), c_b + r * math.sin(math.tau * i / sides)) for i in range(sides)]
    return finish(name, prism_bm(ring, axis, lo, hi), [mat], collide=collide)


def ring(name, mat, axis, c_a, c_b, r_in, r_out, lo, hi, sides=12, collide=False):
    """An annulus standing proud of a wall: a round window's frame."""
    bm = bmesh.new()

    def at(a, b, t):
        return {"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis]

    def verts(r, t):
        return [bm.verts.new(at(c_a + r * math.cos(math.tau * i / sides), c_b + r * math.sin(math.tau * i / sides), t))
                for i in range(sides)]

    i_lo, o_lo, i_hi, o_hi = verts(r_in, lo), verts(r_out, lo), verts(r_in, hi), verts(r_out, hi)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((i_lo[i], o_lo[i], o_lo[j], i_lo[j]))
        bm.faces.new((i_hi[j], o_hi[j], o_hi[i], i_hi[i]))
        bm.faces.new((o_lo[i], o_hi[i], o_hi[j], o_lo[j]))
        bm.faces.new((i_lo[j], i_hi[j], i_hi[i], i_lo[i]))
    return finish(name, bm, [mat], collide=collide)


class Top:
    """A wall's top edge: flat, or a gable following the roof's underside
    3 cm higher (inside the slab, so the two never share a plane)."""

    def __init__(self, row, flat=None, gable=None, pitch=None):
        self.row = row          # the z where the top row of cells begins
        self.flat = flat
        self.gable = gable      # (u of the ridge, half span, eave z)
        self.pitch = math.radians(pitch) if pitch is not None else None
        self.breaks = () if gable is None else (gable[0],)

    def z(self, u):
        if self.gable is None:
            return self.flat
        ridge_u, half, eave = self.gable
        return eave + (half - abs(u - ridge_u)) * math.tan(self.pitch) + 0.03


class MixedTop(Top):
    """A wall top for one wall running under two roofs: flat where one
    roof's eave runs along it, a gable where the other's gable end stands
    over it; the higher of the two, with the kinks as columns so the top
    never cuts a corner above a slab."""

    def __init__(self, row, flat, gable, pitch):
        super().__init__(row, flat=flat, gable=gable, pitch=pitch)
        ridge_u, half, eave = gable
        reach = half - (flat - 0.03 - eave) / math.tan(self.pitch)   # from the ridge to where the gable meets the flat
        self.breaks = (ridge_u - reach, ridge_u, ridge_u + reach)

    def z(self, u):
        return max(self.flat, Top.z(self, u))


def wall(name, origin, u_dir, v_dir, length, z0, top, openings, base_below, mats):
    """One wall as a closed shell: two skins, ends, bottom, top, and a real
    reveal round every opening. `origin` is the outer face's start, `u_dir`
    runs along it, `v_dir` into the wall. An opening is (u0, u1, z0, z1).
    Faces below `base_below` take the second material (the base)."""
    O, U, V = Vector(origin), Vector(u_dir), Vector(v_dir)
    us, zs = {0.0, length}, {z0, top.row}
    for u0, u1, oz0, oz1 in openings:
        assert 0.0 < u0 < u1 < length and z0 < oz0 < oz1 <= top.row, (name, u0, u1, oz0, oz1, length, top.row)
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
    return finish(name, bm, mats)


ALL_WALLS = ("front", "back", "west", "east")


def shell(prefix, x0, x1, y0, y1, z_foot, tops, openings, walls_mat, base_below, which=ALL_WALLS, lap=0.02, base_mat=None):
    """Walls as closed shells round the rectangle (x0, x1, y0, y1), their
    ends lost inside the corner boards (E_IN short of each corner). `tops`
    holds a Top per wall, `openings` per wall a list of (a0, a1, z0, z1) in
    world x (front, back) or world y (west, east) and absolute z. The side
    walls' feet are a centimetre lower than the end walls', because crossing
    shells may not share a bottom. A wall left out of `which` is another
    body's wall: the side walls then run `lap` into it instead. The faces
    below `base_below` take `base_mat`, the shared base unless given."""
    base = base_mat or material("cottage_kit_base")
    e = E_IN
    sy0 = y0 + e if "front" in which else y0 - lap
    sy1 = y1 - e if "back" in which else y1 + lap
    spec = {
        "front": ((x0 + e, y0, 0.0), (1, 0, 0), (0, 1, 0), (x1 - x0) - 2 * e, lambda a: a - x0 - e),
        "back": ((x1 - e, y1, 0.0), (-1, 0, 0), (0, -1, 0), (x1 - x0) - 2 * e, lambda a: x1 - e - a),
        "west": ((x0, sy1, 0.0), (0, -1, 0), (1, 0, 0), sy1 - sy0, lambda a: sy1 - a),
        "east": ((x1, sy0, 0.0), (0, 1, 0), (-1, 0, 0), sy1 - sy0, lambda a: a - sy0),
    }
    out = {}
    for key in which:
        origin, u_dir, v_dir, length, to_u = spec[key]
        ops = []
        for a0, a1, z0, z1 in openings.get(key, ()):
            ua, ub = sorted((to_u(a0), to_u(a1)))
            ops.append((ua, ub, z0, z1))
        top = tops[key]
        foot = z_foot
        if key in ("west", "east"):
            # a centimetre lower at the foot and, when flat, at the top:
            # four shells cross in the corners and may share neither
            foot -= 0.01
            if top.gable is None:
                top = Top(row=top.row, flat=top.flat - 0.01)
        out[key] = wall(f"{prefix}wall_{key}", origin, u_dir, v_dir, length, foot, top, ops,
                        base_below, [walls_mat, base])
    return out


def corner_boards(prefix, mat, x0, x1, y0, y1, z0, z1, which=("sw", "se", "nw", "ne")):
    """Corner boards 4 cm proud of both faces, their feet and tops past the
    walls' (inside the ground, the slab or the deck)."""
    for sx, sy, tag in ((-1, -1, "sw"), (1, -1, "se"), (-1, 1, "nw"), (1, 1, "ne")):
        if tag not in which:
            continue
        cx = (x0 - PROUD + CORNER / 2) if sx < 0 else (x1 + PROUD - CORNER / 2)
        cy = (y0 - PROUD + CORNER / 2) if sy < 0 else (y1 + PROUD - CORNER / 2)
        box(f"{prefix}corner_{tag}", mat, cx - CORNER / 2, cx + CORNER / 2, cy - CORNER / 2, cy + CORNER / 2, z0, z1)


def gable_roof(name, mat, axis, ridge_at, half, eave_z, pitch, over, lo, hi, collide=True):
    """The gable roof as one piece: its section, an inverted V of ROOF_T
    thickness whose underside passes through `eave_z` at the walls' outer
    faces (`half` from the ridge) and runs `over` past them, extruded along
    `axis` from `lo` to `hi` (the rake overhangs included). 'y': the ridge
    runs along Y at x = ridge_at; 'x': along X at y = ridge_at. One mesh, so
    the two slopes share nothing but their ridge line."""
    tn, vt = math.tan(math.radians(pitch)), ROOF_T / math.cos(math.radians(pitch))

    def under(a):
        return eave_z + (half - abs(a - ridge_at)) * tn

    a0, a1 = ridge_at - half - over, ridge_at + half + over
    section = [(a0, under(a0)), (ridge_at, under(ridge_at)), (a1, under(a1)),
               (a1, under(a1) + vt), (ridge_at, under(ridge_at) + vt), (a0, under(a0) + vt)]
    return finish(name, prism_bm(section, axis, lo, hi), [mat], collide=collide)


def gable_roof_notched(name, mat, ridge_at, half, eave_z, pitch, over, lo, hi, y_step, x_cut):
    """A gable roof along Y, as `gable_roof`, whose east eave overhang stops
    at `y_step`: beyond it the east slope is cut off vertically at `x_cut`,
    just proud of the wall under it, so where the roof runs on into another
    roof's gable end its fascia returns instead of running under the rake.
    One mesh."""
    tn, vt = math.tan(math.radians(pitch)), ROOF_T / math.cos(math.radians(pitch))

    def under(a):
        return eave_z + (half - abs(a - ridge_at)) * tn

    a0, a1 = ridge_at - half - over, ridge_at + half + over
    bm = bmesh.new()

    def ring(y, xs):
        return ([bm.verts.new((x, y, under(x))) for x in xs], [bm.verts.new((x, y, under(x) + vt)) for x in xs])

    L0, U0 = ring(lo, [a0, ridge_at, a1])
    L1, U1 = ring(y_step, [a0, ridge_at, x_cut, a1])
    L2, U2 = ring(hi, [a0, ridge_at, x_cut])
    bm.faces.new([L0[0], L0[1], L0[2], U0[2], U0[1], U0[0]])          # the end at lo
    bm.faces.new([L0[0], L0[1], L1[1], L1[0]])                        # west slope, under and top
    bm.faces.new([L1[0], L1[1], L2[1], L2[0]])
    bm.faces.new([U0[0], U0[1], U1[1], U1[0]])
    bm.faces.new([U1[0], U1[1], U2[1], U2[0]])
    bm.faces.new([L0[1], L0[2], L1[3], L1[2], L1[1]])                 # east slope to the step
    bm.faces.new([U0[1], U0[2], U1[3], U1[2], U1[1]])
    bm.faces.new([L1[1], L1[2], L2[2], L2[1]])                        # east slope beyond it, to the cut
    bm.faces.new([U1[1], U1[2], U2[2], U2[1]])
    bm.faces.new([L0[0], U0[0], U1[0], L1[0]])                        # west fascia
    bm.faces.new([L1[0], U1[0], U2[0], L2[0]])
    bm.faces.new([L0[2], U0[2], U1[3], L1[3]])                        # east fascia to the step
    bm.faces.new([L1[2], L1[3], U1[3], U1[2]])                        # the fascia's return at the step
    bm.faces.new([L1[2], U1[2], U2[2], L2[2]])                        # the cut face along x_cut
    bm.faces.new([L2[0], L2[1], L2[2], U2[2], U2[1], U2[0]])          # the end at hi
    return finish(name, bm, [mat])


def ridge_cap(name, mat, axis, ridge_at, z_top, lo, hi):
    """A chunky cap along the ridge, its foot inside the slab."""
    if axis == "y":
        box(name, mat, ridge_at - 0.20, ridge_at + 0.20, lo - 0.02, hi + 0.02, z_top - 0.10, z_top + 0.05, collide=False)
    else:
        box(name, mat, lo - 0.02, hi + 0.02, ridge_at - 0.20, ridge_at + 0.20, z_top - 0.10, z_top + 0.05, collide=False)


def rafter_tails(prefix, mat, side_x, outward, eave_z, pitch, over, y0, y1, spacing, depth=0.14, width=0.09):
    """Exposed rafter tails under a side eave: parallelograms following the
    slope, 2 cm inside the slab's underside, from 5 cm inside the wall to
    10 cm short of the eave edge, every `spacing` along the wall."""
    tn = math.tan(math.radians(pitch))
    n = max(1, int((y1 - y0) / spacing))
    for k in range(n + 1):
        y = y0 + (y1 - y0) * k / n
        xa, xb = side_x - outward * 0.05, side_x + outward * (over - 0.10)

        def zt(x):
            return eave_z - abs(x - side_x) * tn + 0.02

        poly = [(xa, zt(xa)), (xb, zt(xb)), (xb, zt(xb) - depth), (xa, zt(xa) - depth)]
        finish(f"{prefix}tail_{'w' if outward < 0 else 'e'}{k}", prism_bm(poly, "y", y - width / 2, y + width / 2),
               [mat], collide=False)


def knee_brace(prefix, mat, x_wall, outward, y_face, y_out, z_foot, eave_z, pitch, over, size=0.10):
    """A craftsman gable bracket in the rake overhang: a post standing proud
    of the gable wall (2 cm into it) and a diagonal from the post's foot up
    to the rake's underside near the eave edge, 2 cm into the slab."""
    tn = math.tan(math.radians(pitch))
    # the bracket's slice of Y: 2 cm into the wall's face, `size` proud of it
    y_lo, y_hi = sorted((y_face - y_out * 0.02, y_face + y_out * size))
    # the post: from 5 cm inside the wall's side face to `size` beyond it,
    # its top 2 cm over the eave line, inside the slab along its whole width
    x_in = x_wall - outward * 0.05
    x_post0, x_post1 = sorted((x_in, x_in + outward * (size + 0.05)))
    box(f"{prefix}brace_post_{'w' if outward < 0 else 'e'}", mat, x_post0, x_post1, y_lo, y_hi,
        z_foot, eave_z + 0.02, collide=False)
    x_tip = x_wall + outward * (over - 0.12)
    z_tip = eave_z - abs(x_tip - x_wall) * tn + 0.03
    bar(f"{prefix}brace_diag_{'w' if outward < 0 else 'e'}", mat, "y", (x_in + outward * 0.03, z_foot + 0.04),
        (x_tip, z_tip), size, y_lo + 0.005, y_hi - 0.005)


def opening_trim(prefix, mat, axis, face_at, outward, a0, a1, z0, z1, sill=True):
    """Chunky craftsman casing round an opening: a head board over two jambs
    (and a sill board), 3.5 cm proud, the back sunk 1 cm into the wall, the
    jambs lapping 2 cm over the opening's edge and 2 cm into the head and sill.
    `axis` is 'x' when the opening's width runs along X (a wall facing +-Y)."""
    w = TRIM_W

    def part(name, a_lo, a_hi, b_lo, b_hi, sunk, proud):
        lo, hi = sorted((face_at - sunk * outward, face_at + proud * outward))
        if axis == "x":
            return box(name, mat, a_lo, a_hi, lo, hi, b_lo, b_hi, collide=False)
        return box(name, mat, lo, hi, a_lo, a_hi, b_lo, b_hi, collide=False)

    # every board laps 2 cm over the opening's edge, so none meets a reveal
    # edge-on; the head and sill stand a centimetre prouder than the jambs
    # and sit a half-centimetre shallower, so the lapped boards share no face
    part(f"{prefix}_head", a0 - w - 0.04, a1 + w + 0.04, z1 - 0.02, z1 + w, 0.010, 0.045)
    part(f"{prefix}_jamb_a", a0 - w, a0 + 0.02, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
    part(f"{prefix}_jamb_b", a1 - 0.02, a1 + w, z0 - 0.02, z1 + 0.02, 0.015, 0.035)
    if sill:
        part(f"{prefix}_sill", a0 - w - 0.04, a1 + w + 0.04, z0 - w, z0 + 0.02, 0.010, 0.045)


def pane(name, mat, axis, face_at, outward, a0, a1, z0, z1, recess=0.08, thick=0.05, collide=True):
    """A slab set in an opening, recessed into the wall, 2 cm into the
    reveals all round."""
    lo, hi = sorted((face_at - recess * outward, face_at - (recess + thick) * outward))
    if axis == "x":
        return box(name, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, collide=collide)
    return box(name, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, collide=collide)


def meeting_rail(name, mat, axis, face_at, outward, a0, a1, z):
    """A double-hung window's meeting rail: a chunky bar across the pane,
    clear of it and of the casing."""
    lo, hi = sorted((face_at - 0.040 * outward, face_at - 0.072 * outward))
    if axis == "x":
        return box(name, mat, a0 - 0.01, a1 + 0.01, lo, hi, z - 0.03, z + 0.03, collide=False)
    return box(name, mat, lo, hi, a0 - 0.01, a1 + 0.01, z - 0.03, z + 0.03, collide=False)


def mullion(name, mat, axis, face_at, outward, a, z0, z1, w=0.16):
    """A chunky upright dividing a wide window's pane, clear of the pane
    behind it, its ends inside the sill and head boards."""
    lo, hi = sorted((face_at - 0.030 * outward, face_at - 0.070 * outward))
    if axis == "x":
        return box(name, mat, a - w / 2, a + w / 2, lo, hi, z0 - 0.01, z1 + 0.01, collide=False)
    return box(name, mat, lo, hi, a - w / 2, a + w / 2, z0 - 0.01, z1 + 0.01, collide=False)


def fit_openings(prefix, openings, rect, trim, glass, door, doors=(), rails=True, recess_door=0.08):
    """Casings, panes and doors in every opening of `openings` (the shell's
    dict). `doors` names (face, index) pairs that are doors: no sill board,
    the door material. `rails` adds a meeting rail to windows taller than
    they are wide (the double-hung look)."""
    x0, x1, y0, y1 = rect
    faces = {"front": ("x", y0, -1), "back": ("x", y1, 1), "west": ("y", x0, -1), "east": ("y", x1, 1)}
    for face, ops in openings.items():
        axis, at, out = faces[face]
        for k, (a0, a1, z0, z1) in enumerate(ops):
            is_door = (face, k) in doors
            opening_trim(f"{prefix}{face}{k}_trim", trim, axis, at, out, a0, a1, z0, z1, sill=not is_door)
            pane(f"{prefix}{face}{k}_{'door' if is_door else 'pane'}", door if is_door else glass, axis, at, out,
                 a0, a1, z0, z1, recess=recess_door if is_door else 0.08)
            if rails and not is_door and (z1 - z0) > (a1 - a0) * 1.1:
                meeting_rail(f"{prefix}{face}{k}_rail", trim, axis, at, out, a0, a1, (z0 + z1) / 2)


def steps(prefix, mat, along, c0, c1, front, floor_z, sign=-1):
    """A flight down from a deck edge at `front` (a coordinate along `along`)
    going `sign`-ward, `c0..c1` wide across. The treads are one stepped
    block, scenery (no collision), lapping 2 cm into the deck; the narrow
    ramp on the nosing line is the floor, flush with the deck's edge and
    ending inside the deck, its foot 2 cm below the treads' so the two share
    no plane; nosing strips 3 cm proud of the ramp mark each tread. One
    riser is a short ramp alone."""
    axis = "x" if along == "y" else "y"
    n = max(1, round(floor_z / RISER))
    riser = floor_z / n

    def at(k):
        return front + sign * k * GOING

    foot = at(n)
    if n > 1:
        profile = [(foot, -BELOW)]
        for k in range(1, n):
            profile += [(at(n - k + 1), k * riser), (at(n - k), k * riser)]
        profile += [(front - sign * 0.02, (n - 1) * riser), (front - sign * 0.02, -BELOW)]
        # the treads a half-centimetre narrower than the deck they lap into
        finish(f"{prefix}steps", prism_bm(profile, axis, c0 + 0.005, c1 - 0.005), [mat], collide=False)
    ramp = [(foot + sign * 0.05, -BELOW - 0.02), (foot, 0.0), (front, floor_z), (front - sign * 0.06, -BELOW - 0.02)]
    finish(f"{prefix}step_ramp", prism_bm(ramp, axis, c0 + 0.10, c1 - 0.10), [mat])
    for k in range(1, n):
        nose = at(n - k + 1)
        lo, hi = sorted((nose + sign * 0.01, nose - sign * 0.05))
        if along == "y":
            box(f"{prefix}step_nosing_{k}", mat, c0 + 0.012, c1 - 0.012, lo, hi, k * riser - 0.01, k * riser + 0.03, collide=False)
        else:
            box(f"{prefix}step_nosing_{k}", mat, lo, hi, c0 + 0.012, c1 - 0.012, k * riser - 0.01, k * riser + 0.03, collide=False)


def rail(prefix, mat, axis, at, a0, a1, z_floor, panel=0.06, cap=0.14):
    """A deck rail as a solid panel with a cap: the panel is the paint pass's
    picket cut-out later. Ends lap 2 cm into the posts either side, the cap
    a centimetre less; the panel's foot 1.5 cm into the deck (the posts go 2)."""
    z0, z1 = z_floor - 0.015, z_floor + RAIL_H
    if axis == "x":
        box(f"{prefix}_panel", mat, a0, a1, at - panel / 2, at + panel / 2, z0, z1)
        box(f"{prefix}_cap", mat, a0 + 0.01, a1 - 0.01, at - cap / 2, at + cap / 2, z1 - 0.03, z1 + 0.05, collide=False)
    else:
        box(f"{prefix}_panel", mat, at - panel / 2, at + panel / 2, a0, a1, z0, z1)
        box(f"{prefix}_cap", mat, at - cap / 2, at + cap / 2, a0 + 0.01, a1 - 0.01, z1 - 0.03, z1 + 0.05, collide=False)


def chimney(prefix, mat, x0, x1, y0, y1, z_foot, z_top):
    """A chimney stack with a cap slab proud all round, lapped 2 cm down."""
    box(f"{prefix}chimney", mat, x0, x1, y0, y1, z_foot, z_top)
    box(f"{prefix}chimney_cap", mat, x0 - 0.07, x1 + 0.07, y0 - 0.07, y1 + 0.07, z_top - 0.02, z_top + 0.08, collide=False)


def purlin(name, mat, x0, x1, zt, depth, y0, y1):
    """A square timber along Y whose top follows the roof's underside across
    X (`zt(x)`): a purlin end under a rake, a rafter tail."""
    poly = [(x0, zt(x0)), (x1, zt(x1)), (x1, zt(x1) - depth), (x0, zt(x0) - depth)]
    return finish(name, prism_bm(poly, "y", y0, y1), [mat], collide=False)


def mats(walls="cottage_kit_walls", trim="cottage_kit_trim", roof="cottage_kit_roof", door="cottage_kit_door"):
    """The stand-in materials a variant builds with, by surface."""
    return dict(walls=material(walls), trim=material(trim), roof=material(roof), door=material(door),
                glass=material("cottage_kit_glass"), porch=material("cottage_kit_porch"),
                base=material("cottage_kit_base"), concrete=material("cottage_kit_concrete"))


def gable_body(V, openings, m, floor, rect=(-HW, HW, -HD, HD), which=ALL_WALLS, roof_lo=None, roof_hi=None,
               boards=True, corner_which=("sw", "se", "nw", "ne"), front_gable=True, lap=0.02):
    """The kit's constant: four walls with gables front and back (the ridge
    running front to back), corner boards, the gable roof and its ridge cap.
    Returns the roof's numbers."""
    x0, x1, y0, y1 = rect
    eave, pitch = V["eave"], V["pitch"]
    half, ridge_x = (x1 - x0) / 2, (x0 + x1) / 2
    wall_top = eave + WALL_OVER
    gable = Top(row=eave, gable=(half - E_IN, half, eave), pitch=pitch)
    flat = Top(row=eave, flat=wall_top)
    tops = {"front": gable if front_gable else flat, "back": gable, "west": flat, "east": flat}
    shell("", x0, x1, y0, y1, -BELOW, tops, openings, m["walls"], floor, which=which, lap=lap, base_mat=m["base"])
    if boards:
        corner_boards("", m["trim"], x0, x1, y0, y1, -BELOW - 0.03, wall_top + 0.02, which=corner_which)
    lo = y0 - V["rake_over"] if roof_lo is None else roof_lo
    hi = y1 + V["rake_over"] if roof_hi is None else roof_hi
    gable_roof("roof", m["roof"], "y", ridge_x, half, eave, pitch, V["eave_over"], lo, hi)
    vt = ROOF_T / math.cos(math.radians(pitch))
    ridge_under = eave + half * math.tan(math.radians(pitch))
    ridge_cap("ridge_cap", m["roof"], "y", ridge_x, ridge_under + vt, lo, hi)
    return dict(ridge_under=ridge_under, ridge_top=ridge_under + vt, wall_top=wall_top, vt=vt, lo=lo, hi=hi,
                under=lambda x: eave + (half - abs(x - ridge_x)) * math.tan(math.radians(pitch)))


def stoop(prefix, m, x0, x1, y0, y1, floor, along, front, c0, c1, sign):
    """A concrete landing at `floor`, lapped 2 cm into the wall it serves,
    and its flight down from the edge `front`."""
    box(f"{prefix}landing", m["concrete"], x0, x1, y0, y1, -0.10, floor)
    steps(prefix, m["concrete"], along, c0, c1, front, floor, sign=sign)


# --- classic: the steep gable with the sunburst ------------------------------

def build_classic(front_door=False):
    """The classic; with `front_door`, the `classic_gable` variant (Christina's
    rule, 3 Oct 2026: either/or questions become variants): the same body,
    roof, chimney, sunburst, trim and colours, the front door on the gable
    face under a hood of its own with a stoop and steps, and the side door
    moved back along the west side."""
    V = CLASSIC
    if front_door:
        # its own stand-ins on every surface (Christina, 3 Oct 2026: "on the
        # variations lets change the colors", "can the doors be different
        # colors too"): butter-yellow walls, the plan's cottage yellow, white
        # trim, coral doors since the classic's are teal; the roof and the
        # brick the classic's colours, but materials of its own too
        v = "classic_gable"
        m = dict(walls=own_material(v, "walls", hex6=PLAN_COLOURS[2]), trim=own_material(v, "trim", "cottage_kit_trim"),
                 roof=own_material(v, "roof", "cottage_kit_roof"), door=own_material(v, "door", hex6="ee7656"),
                 glass=own_material(v, "glass", "cottage_kit_glass"), base=own_material(v, "base", "cottage_kit_base"),
                 concrete=own_material(v, "concrete", "cottage_kit_concrete"))
        brick = own_material(v, "brick", "cottage_kit_brick")
    else:
        m = mats()
        brick = material("cottage_kit_brick")
    floor = V["floor"]
    head = floor + 1.95                      # the photo's doors and windows share a head line under the eave
    sill = head - 1.50                       # tall double-hung windows
    dy0, dy1 = V["gable_side_door_y"] if front_door else V["door_y"]
    if front_door:
        fx0, fx1 = V["gable_door_x"]
        openings = {
            "front": [(fx0, fx1, floor + THRESHOLD, head), (-2.4, -1.5, sill, head), (1.5, 2.4, sill, head)],
            "back": [(-2.0, -1.1, sill, head), (1.1, 2.0, sill, head)],
            "west": [(dy0, dy1, floor + THRESHOLD, head), (-2.7, -1.8, sill, head), (-0.7, 0.2, sill, head)],
            "east": [(-2.7, -1.8, sill, head), (-0.45, 0.45, sill, head), (1.8, 2.7, sill, head)],
        }
        doors = {("front", 0), ("west", 0)}
    else:
        openings = {
            "front": [(-0.45, 0.45, sill, head)],
            "back": [(-2.0, -1.1, sill, head), (1.1, 2.0, sill, head)],
            "west": [(dy0, dy1, floor + THRESHOLD, head), (-0.4, 0.5, sill, head), (1.6, 2.5, sill, head)],
            "east": [(-2.7, -1.8, sill, head), (-0.45, 0.45, sill, head), (1.8, 2.7, sill, head)],
        }
        doors = {("west", 0)}
    R = gable_body(V, openings, m, floor)
    fit_openings("", openings, (-HW, HW, -HD, HD), m["trim"], m["glass"], m["door"], doors=doors)
    # the sunburst in the peak: a collar board across the gable, a half-disc
    # hub on it and five rays to the rakes, each a little less proud than the
    # hub and than the ray before it, so no two share a face
    zc = R["ridge_under"] - 1.5 * math.tan(math.radians(V["pitch"]))
    half_c = (R["ridge_under"] - zc) / math.tan(math.radians(V["pitch"]))
    box("sunburst_collar", m["trim"], -half_c - 0.02, half_c + 0.02, -HD - 0.040, -HD + 0.010, zc - 0.12, zc, collide=False)
    disc("sunburst_hub", m["trim"], "y", 0.0, zc - 0.02, 0.22, -HD - 0.055, -HD + 0.005, sides=8, half=True)
    for k, deg in enumerate((20.0, 55.0, 90.0, 125.0, 160.0)):
        th = math.radians(deg)
        z0 = zc + 0.02                       # the rays spring from inside the hub, clear of the collar's top
        reach = (R["ridge_under"] + 0.03 - z0) / (math.sin(th) + abs(math.cos(th)) * math.tan(math.radians(V["pitch"])))
        proud = 0.045 + 0.002 * k
        bar(f"sunburst_ray_{k}", m["trim"], "y", (0.0, z0), (reach * math.cos(th), z0 + reach * math.sin(th)), 0.08,
            -HD - proud, -HD + 0.015 - 0.002 * k)
    # purlin ends under both rakes
    for yf, sign in ((-HD, -1), (HD, 1)):
        for k, x in enumerate((-2.3, -1.1, 1.1, 2.3)):
            y0, y1 = sorted((yf - sign * 0.02, yf + sign * (V["rake_over"] - 0.06)))
            purlin(f"purlin_{'f' if sign < 0 else 'b'}{k}", m["trim"], x - 0.05, x + 0.05, lambda u: R["under"](u) + 0.02, 0.10, y0, y1)
    # the brick chimney straddling the ridge, its foot in the attic
    cw, cd, cy, ch = V["chimney"]
    chimney("", brick, -cw / 2, cw / 2, cy - cd / 2, cy + cd / 2, R["ridge_top"] - 0.45, R["ridge_top"] + ch)
    # the side door under its shed hood on two brackets, the stoop and steps
    hw, hr = V["hood"]
    hy0, hy1 = (dy0 + dy1) / 2 - hw / 2, (dy0 + dy1) / 2 + hw / 2
    z_wall, drop = head + 0.14, hr * math.tan(math.radians(20.0))   # under the eave's edge, over the head board
    slab("hood", m["roof"], ((-HW + 0.02, hy0, z_wall), (-HW - hr, hy0, z_wall - drop),
                              (-HW - hr, hy1, z_wall - drop), (-HW + 0.02, hy1, z_wall)), 0.10, collide=False)
    for tag, y in (("a", hy0 + 0.10), ("b", hy1 - 0.10)):
        bar(f"hood_bracket_{tag}", m["trim"], "y", (-HW + 0.02, z_wall - 0.55), (-HW - hr + 0.14, z_wall - drop - 0.02), 0.08,
            y - 0.04, y + 0.04)
    stoop("", m, -HW - 0.90, -HW + 0.02, dy0 - 0.10, dy1 + 0.10, floor, "x", -HW - 0.90, dy0 - 0.10, dy1 + 0.10, -1)
    if front_door:
        # the same hood and stoop again on the gable face, under the sunburst
        gx0, gx1 = (fx0 + fx1) / 2 - hw / 2, (fx0 + fx1) / 2 + hw / 2
        slab("front_hood", m["roof"], ((gx0, -HD + 0.02, z_wall), (gx1, -HD + 0.02, z_wall),
                                        (gx1, -HD - hr, z_wall - drop), (gx0, -HD - hr, z_wall - drop)), 0.10, collide=False)
        for tag, x in (("a", gx0 + 0.10), ("b", gx1 - 0.10)):
            bar(f"front_hood_bracket_{tag}", m["trim"], "x", (-HD + 0.02, z_wall - 0.55), (-HD - hr + 0.14, z_wall - drop - 0.02), 0.08,
                x - 0.04, x + 0.04)
        stoop("front_", m, fx0 - 0.10, fx1 + 0.10, -HD - 0.90, -HD + 0.02, floor, "y", -HD - 0.90, fx0 - 0.10, fx1 + 0.10, -1)


# --- bungalow: low gable, deep eaves, the glazed sun porch -------------------

def build_bungalow():
    V = BUNGALOW
    m = mats(walls="cottage_kit_walls_white", trim="cottage_kit_trim_teal")
    floor = V["floor"]
    pw, pd = V["porch"]
    px0, px1, py0 = -HW, -HW + pw, -HD - pd           # the sun porch fills the front's west
    sill, head = V["sill"], V["head"]
    body_rect = (-HW, HW, -HD, HD)
    openings = {
        "front": [(1.4, 2.4, floor + THRESHOLD, head)],
        "back": [(-2.2, -1.0, sill, head), (1.0, 2.2, sill, head)],
        "west": [(-2.0, -0.8, sill, head), (1.0, 2.2, sill, head)],
        "east": [(-3.0, -1.8, sill, head), (0.6, 1.8, sill, head)],
    }
    # the body: its front wall gabled too, since the entry bay looks up at it
    R = gable_body(V, openings, m, floor, roof_lo=py0 - V["rake_over"])
    fit_openings("", openings, body_rect, m["trim"], m["glass"], m["door"], doors={("front", 0)}, rails=False)
    # the sun porch: a low wall under big windows on its front and west, its
    # east wall rising to the roof (the entry bay sees it), 2 cm into the body
    eave = V["eave"]
    porch_rect = (px0, px1, py0, -HD)
    low = Top(row=head + 0.15, flat=eave + 0.02)
    tall = Top(row=head + 0.15, flat=R["under"](px1 - T / 2) + 0.03)
    p_open = {"front": [(px0 + 0.40, px1 - 0.40, sill, head)],
              "west": [(py0 + 0.45, -HD - 0.45, sill, head)]}
    shell("porch_", px0, px1, py0, -HD, -BELOW - 0.035, {"front": low, "west": low, "east": tall}, p_open, m["walls"], floor,
          which=("front", "west", "east"))
    fit_openings("porch_", p_open, porch_rect, m["trim"], m["glass"], m["door"], rails=False)
    mullion("porch_front_mullion", m["trim"], "x", py0, -1, (px0 + px1) / 2, sill, head)
    corner_boards("porch_", m["trim"], px0, px1, py0, -HD, -BELOW - 0.05, eave + 0.04, which=("sw",))
    # the gable wall over the porch and the entry bay, 3 cm behind the porch's
    # face and a centimetre short of its ends, its foot inside the chunky
    # band that is the entry's header
    gable = Top(row=eave, gable=(HW - E_IN - 0.01, HW, eave), pitch=V["pitch"])
    wall("gable_front", (-HW + E_IN + 0.01, py0 + 0.03, 0.0), (1, 0, 0), (0, 1, 0), W - 2 * E_IN - 0.02, eave - 0.10, gable, [], -1.0,
         [m["walls"], m["base"]])
    box("band", m["trim"], -HW - 0.05, HW + 0.05, py0 - 0.05, py0 + 0.24, eave - 0.20, eave + 0.14, collide=False)
    # the entry bay: a landing with two steps, chunky posts at the porch's
    # corner (the house number's) and the body's, 1 cm prouder than the band
    lx0, lx1 = px1 - 0.02, HW - 0.02
    box("landing", m["concrete"], lx0, lx1, py0 + 0.02, -HD + 0.03, -0.10, floor)
    steps("", m["concrete"], "y", 1.3, 2.5, py0 + 0.02, floor)
    for tag, x in (("w", px1 - 0.16), ("e", HW - 0.26)):
        box(f"post_{tag}", m["trim"], x, x + 0.30, py0 - 0.06, py0 + 0.25, floor - 0.02, eave - 0.18)
    # deep eaves on rafter tails, brackets under both rakes
    for side, out in ((-HW, -1), (HW, 1)):
        rafter_tails("", m["trim"], side, out, eave, V["pitch"], V["eave_over"], py0 + 0.4, HD - 0.4, V["tail_pitch"])
        knee_brace("front_", m["trim"], side, out, py0, -1, eave - 0.60, eave, V["pitch"], V["eave_over"])
        knee_brace("back_", m["trim"], side, out, HD, 1, eave - 0.60, eave, V["pitch"], V["eave_over"])


# --- hip: the low side gable with the little gable over the stoop -------------

def build_hip():
    """Named `hip` for its photo, `blue_hip_roof_cottage.png`, but read
    again (2 Oct 2026) its main roof is a low side gable: the ridge runs
    along the street, the eaves along the front and back, each side wall
    rising into a low triangle with a louvred vent near the peak, and the
    little entry gable breaking the front eave over the stoop."""
    V = HIP
    m = mats(walls="cottage_kit_walls_sky", trim="cottage_kit_trim_blue")
    floor, eave, pitch = V["floor"], V["eave"], V["pitch"]
    head = floor + 1.95
    sill = head - 1.20
    door_x = (0.9, 1.9)
    openings = {
        "front": [(door_x[0], door_x[1], floor + THRESHOLD, head), (-2.4, -0.8, sill, head)],
        "back": [(-2.2, -1.0, sill, head), (1.0, 2.2, sill, head)],
        "west": [(-2.6, -1.6, sill, head), (-0.4, 0.6, sill, head), (1.6, 2.6, sill, head)],
        "east": [(-2.6, -1.6, sill, head), (0.8, 2.0, sill, head)],
    }
    wall_top = eave + WALL_OVER
    flat = Top(row=eave, flat=wall_top)
    gable_side = Top(row=eave, gable=(HD - E_IN, HD, eave), pitch=pitch)
    shell("", -HW, HW, -HD, HD, -BELOW, {"front": flat, "back": flat, "west": gable_side, "east": gable_side}, openings,
          m["walls"], floor)
    corner_boards("", m["trim"], -HW, HW, -HD, HD, -BELOW - 0.03, wall_top + 0.02)
    tn_m = math.tan(math.radians(pitch))
    vt_m = ROOF_T / math.cos(math.radians(pitch))
    gable_roof("roof", m["roof"], "x", 0.0, HD, eave, pitch, V["over"], -HW - V["over"], HW + V["over"])
    ridge_cap("ridge_cap", m["roof"], "x", 0.0, eave + HD * tn_m + vt_m, -HW - V["over"], HW + V["over"])
    fit_openings("", openings, (-HW, HW, -HD, HD), m["trim"], m["glass"], m["door"], doors={("front", 0)}, rails=False)
    # a louvred vent near each peak: a frame panel and three slats, each a
    # little prouder than the last
    vw, vh, vd = V["vent"]
    vz = eave + HD * tn_m - vd
    for side, out in ((-HW, -1), (HW, 1)):
        lo, hi = sorted((side + out * 0.030, side - out * 0.010))
        box(f"vent_{'w' if out < 0 else 'e'}", m["trim"], lo, hi, -vw / 2, vw / 2, vz - vh / 2, vz + vh / 2, collide=False)
        for k, dz in enumerate((-0.10, 0.0, 0.10)):
            lo, hi = sorted((side + out * (0.045 + 0.002 * k), side + out * 0.020))
            box(f"vent_slat_{'w' if out < 0 else 'e'}{k}", m["walls"], lo, hi, -vw / 2 + 0.05, vw / 2 - 0.05,
                vz + dz - 0.02, vz + dz + 0.02, collide=False)
    # the little gable over the stoop: its own roof slab from a metre out
    # into the main roof's front slope, a thin gable face with a round
    # plaque, two brackets to the wall
    hw_, reach, hpitch, heave = V["hood"]
    xr = (door_x[0] + door_x[1]) / 2
    tn = math.tan(math.radians(hpitch))
    vt = ROOF_T / math.cos(math.radians(hpitch))
    # its back end is where the main roof's top has risen over the hood's
    # cap, so the end face is inside the slab
    hood_hi = -HD - V["over"] + (heave + hw_ / 2 * tn + vt + 0.05 - (eave - V["over"] * tn_m + vt_m)) / tn_m + 0.05
    gable_roof("hood_roof", m["roof"], "y", xr, hw_ / 2, heave, hpitch, 0.15, -HD - reach, hood_hi)
    ridge_cap("hood_cap", m["roof"], "y", xr, heave + hw_ / 2 * tn + vt, -HD - reach, hood_hi)
    tri = [(xr - hw_ / 2 - 0.02, heave - 0.05), (xr + hw_ / 2 + 0.02, heave - 0.05), (xr + hw_ / 2 + 0.02, heave + 0.03),
           (xr, heave + hw_ / 2 * tn + 0.03), (xr - hw_ / 2 - 0.02, heave + 0.03)]
    finish("hood_gable", prism_bm(tri, "y", -HD - reach + 0.03, -HD - reach + 0.15), [m["walls"]], collide=False)
    disc("hood_plaque", m["trim"], "y", xr, heave + 0.15, 0.11, -HD - reach + 0.01, -HD - reach + 0.05, sides=12)
    for tag, x in (("w", xr - hw_ / 2 + 0.08), ("e", xr + hw_ / 2 - 0.08)):
        bar(f"hood_bracket_{tag}", m["trim"], "x", (-HD + 0.02, head + 0.20), (-HD - reach + 0.22, heave + 0.12), 0.09,
            x - 0.045, x + 0.045)
    # the stoop: a landing up four steps with white rails both sides and a
    # handrail down each side of the flight
    white = material("cottage_kit_trim")       # the photo's rails are white against the dark blue trim
    sw, sd = V["stoop"]
    sx0, sx1 = xr - sw / 2, xr + sw / 2
    sy0 = -HD - sd
    stoop("", m, sx0, sx1, sy0, -HD + 0.02, floor, "y", sy0, sx0 + 0.2, sx1 - 0.2, -1)
    foot = sy0 - round(floor / RISER) * GOING
    for tag, x in (("w", sx0 + 0.01), ("e", sx1 - 0.11)):
        box(f"newel_{tag}", white, x, x + 0.10, sy0 + 0.01, sy0 + 0.11, floor - 0.02, floor + RAIL_H + 0.10)
        rail(f"stoop_rail_{tag}", white, "y", x + 0.05, sy0 + 0.09, -HD + 0.03, floor, panel=0.05, cap=0.09)
        box(f"foot_post_{tag}", white, x, x + 0.10, foot - 0.02, foot + 0.08, -BELOW, RAIL_H + 0.06)
        bar(f"handrail_{tag}", white, "x", (sy0 - 0.03, floor + RAIL_H + 0.02), (foot + 0.03, RAIL_H + 0.02), 0.08,
            x + 0.01, x + 0.09)
    # a slim flue on the back slope
    fw, fy, fh = V["flue"]
    fx = 1.6
    z_surf = eave + (HD - fy) * tn_m + vt_m
    box("flue", m["roof"], fx - fw / 2, fx + fw / 2, fy - fw / 2, fy + fw / 2, eave - 0.3, z_surf + fh)
    box("flue_cap", m["trim"], fx - fw / 2 - 0.05, fx + fw / 2 + 0.05, fy - fw / 2 - 0.05, fy + fw / 2 + 0.05,
        z_surf + fh - 0.02, z_surf + fh + 0.06, collide=False)


# --- hip_garage: the hip cottage's detached one-car garage -------------------

def build_hip_garage():
    V = HIP_GARAGE
    m = mats(walls="cottage_kit_walls_sky", trim="cottage_kit_trim_blue")
    gw, gd = V["w"], V["d"]
    rect = (-gw / 2, gw / 2, -gd / 2, gd / 2)
    dw, dh = V["door"]
    openings = {
        "front": [(-dw / 2, dw / 2, THRESHOLD, THRESHOLD + dh)],
        "west": [(-0.6, 0.6, 1.3, 2.0)],
        "back": [(-0.5, 0.5, THRESHOLD, 2.0)],
    }
    gable_body(V, openings, m, 0.0, rect=rect)
    fit_openings("", openings, rect, m["trim"], m["glass"], material("cottage_kit_trim"), doors={("front", 0), ("back", 0)},
                 rails=False, recess_door=0.10)       # the photo's door is white


# --- glass_gable: the front gable glazed into the peak -----------------------

def build_glass_gable():
    V = GLASS
    m = mats(walls="cottage_kit_walls_sky", door="cottage_kit_door_cobalt")
    floor, sill, head, eave = V["floor"], V["sill"], V["head"], V["eave"]
    door_x = (1.5, 2.5)
    side_sill = 1.10
    openings = {
        "back": [(-2.0, -1.0, sill, head), (1.0, 2.0, sill, head)],
        "west": [(-2.2, -1.0, side_sill, head), (0.8, 2.0, side_sill, head)],
        "east": [(-2.8, -1.6, side_sill, head), (0.8, 2.0, side_sill, head)],
    }
    # the body without its front wall; the side walls stop at the front
    # corners as if it were there
    R = gable_body(V, openings, m, floor, which=("back", "west", "east"), lap=-E_IN)
    fit_openings("", openings, (-HW, HW, -HD, HD), m["trim"], m["glass"], m["door"], rails=False)
    # the front: a sill band either side of the door, its ends the door's
    # reveals; one glass slab the shape of the gable from the band up into
    # the roof; the door leaf in its slot, proud of the glass; casing round
    # the door and a grid of chunky white bars over the glass, each at its
    # own depth
    band = Top(row=sill - 0.10, flat=sill)
    wall("band_w", (-HW + E_IN, -HD, 0.0), (1, 0, 0), (0, 1, 0), door_x[0] + HW - E_IN, -BELOW, band, [], floor, [m["walls"], m["base"]])
    wall("band_e", (door_x[1], -HD, 0.0), (1, 0, 0), (0, 1, 0), HW - E_IN - door_x[1], -BELOW, band, [], floor, [m["walls"], m["base"]])
    xg = HW - E_IN - 0.01
    glass = [(-xg, sill - 0.02), (xg, sill - 0.02), (xg, R["under"](xg) + 0.03), (0.0, R["ridge_under"] + 0.03),
             (-xg, R["under"](-xg) + 0.03)]
    finish("glass_gable", prism_bm(glass, "y", -HD + 0.08, -HD + 0.13), [m["glass"]])
    pane("door", m["door"], "x", -HD, -1, door_x[0], door_x[1], THRESHOLD, head, recess=0.02)
    opening_trim("door_trim", m["trim"], "x", -HD, -1, door_x[0], door_x[1], THRESHOLD, head, sill=False)
    # the boards' depths each their own: sill 4.5 cm proud, head 4.2, the
    # corner boards 4, the jambs 3.5, the mullions 3 and a little more each
    box("sill_board", m["trim"], -xg - 0.005, xg + 0.005, -HD - 0.045, -HD + 0.010, sill - 0.04, sill + 0.08, collide=False)
    box("head_bar", m["trim"], -xg - 0.005, xg + 0.005, -HD - 0.042, -HD + 0.075, head - 0.06, head + 0.06, collide=False)
    for k, x in enumerate(V["mullions"]):
        if door_x[0] - 0.2 < x < door_x[1] + 0.2:
            continue
        poly = [(x - 0.05, sill - 0.02), (x + 0.05, sill - 0.02), (x + 0.05, R["under"](x + 0.05) + 0.03), (x - 0.05, R["under"](x - 0.05) + 0.03)]
        finish(f"mullion_{k}", prism_bm(poly, "y", -HD - 0.030 - 0.002 * k, -HD + 0.072 - 0.002 * k), [m["trim"]], collide=False)
    # deep eaves on rafter tails, a knee brace at each front gable corner
    for side, out in ((-HW, -1), (HW, 1)):
        rafter_tails("", m["trim"], side, out, eave, V["pitch"], V["eave_over"], -HD + 0.4, HD - 0.4, V["tail_pitch"])
        knee_brace("front_", m["trim"], side, out, -HD, -1, eave - 0.70, eave, V["pitch"], V["eave_over"])


# --- porch: the pink cottage with the full-width porch and the hammock -------

def hammock(name, mat, x0, x1, y, z_end, z_mid, width, stations=12):
    """A hammock slung between two posts: a ribbon sagging to `z_mid` at
    its middle, gathered to a point at each end, 3 cm thick."""
    bm = bmesh.new()
    rows = []
    for i in range(stations + 1):
        t = i / stations
        x = x0 + (x1 - x0) * t
        z = z_end - (z_end - z_mid) * (1.0 - (2 * t - 1) ** 2)
        w = 0.06 + (width - 0.06) * math.sin(math.pi * t)
        rows.append([bm.verts.new((x, y - w / 2, z)), bm.verts.new((x, y + w / 2, z)),
                     bm.verts.new((x, y + w / 2, z - 0.03)), bm.verts.new((x, y - w / 2, z - 0.03))])
    for a, b in zip(rows, rows[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rows[0])
    bm.faces.new(list(reversed(rows[-1])))
    return finish(name, bm, [mat], collide=False)


def build_porch():
    V = PORCH
    m = mats(walls="cottage_kit_walls_pink", trim="cottage_kit_trim_mint", roof="cottage_kit_roof_metal")
    orange, fabric = material("cottage_kit_trim_orange"), material("cottage_kit_fabric")
    floor, eave, pd = V["floor"], V["eave"], V["porch_d"]
    head = floor + 2.0
    sill = head - 1.30
    openings = {
        "front": [(-0.5, 0.5, floor + THRESHOLD, head), (-2.3, -1.3, sill, head), (1.3, 2.3, sill, head)],
        "back": [(-2.0, -1.0, sill, head), (1.0, 2.0, sill, head)],
        "west": [(-2.4, -1.4, sill, head), (0.6, 1.6, sill, head)],
        "east": [(-2.4, -1.4, sill, head), (0.6, 1.6, sill, head)],
    }
    gable_body(V, openings, m, floor)
    fit_openings("", openings, (-HW, HW, -HD, HD), m["trim"], m["glass"], m["door"], doors={("front", 0)}, rails=False)
    # louvred shutters either side of the front windows, lapped 2 cm into the casings
    for k, (a0, a1, z0, z1) in enumerate(openings["front"][1:]):
        for tag, x in (("a", a0 - TRIM_W - 0.30), ("b", a1 + TRIM_W - 0.02)):
            box(f"shutter_{k}{tag}", m["trim"], x, x + 0.32, -HD - 0.030, -HD + 0.005, z0 - 0.03, z1 + 0.03, collide=False)
    # the round window in the gable: a frame ring and a glass disc lapped under it
    wr, wz = V["window_r"], V["window_z"]
    ring("round_frame", m["trim"], "y", 0.0, wz, wr - 0.04, wr + 0.06, -HD - 0.040, -HD + 0.010)
    disc("round_glass", m["glass"], "y", 0.0, wz, wr - 0.02, -HD - 0.020, -HD + 0.015, sides=12)
    # the porch: a deck the body's width, four chunky posts, a low roof slab
    # of its own under the gable, the hammock between the outer posts, steps
    px0, px1, py0 = -HW - 0.06, HW + 0.06, -HD - pd - 0.06
    box("deck", m["porch"], px0, px1, py0, -HD + 0.02, -0.10, floor)
    z_wall, z_edge = V["porch_roof"]
    rx0, rx1, ry = px0 - 0.30, px1 + 0.30, py0 - 0.30
    slab("porch_roof", m["roof"], ((rx0, ry, z_edge), (rx1, ry, z_edge), (rx1, -HD + 0.02, z_wall), (rx0, -HD + 0.02, z_wall)), 0.16)
    post_y = py0 + 0.04
    posts_x = (-2.90, -0.95, 0.95, 2.90)
    for k, x in enumerate(posts_x):
        z_under = z_wall - (z_wall - z_edge) * (-HD + 0.02 - (post_y + POST / 2)) / (-HD + 0.02 - ry) - 0.16
        box(f"post_{k}", orange, x - POST / 2, x + POST / 2, post_y, post_y + POST, floor - 0.02, z_under + 0.02)
    box("fascia", orange, rx0 + 0.01, rx1 - 0.01, ry - 0.03, ry + 0.02, z_edge - 0.19, z_edge - 0.01, collide=False)
    zh0, zh1 = V["hammock"]
    hammock("hammock", fabric, posts_x[0] + 0.08, posts_x[-1] - 0.08, -HD - pd / 2 - 0.1, zh0, zh1, 1.05)
    steps("", m["porch"], "y", -0.70, 0.70, py0, floor)


# --- log: two front gables and the fieldstone chimney ------------------------

def log_corners(prefix, mat, corners, z_top, r, course):
    """Chunky log ends at each corner: one object per corner, a course of
    half-round ends every `course` up the wall, along X and along Y by
    turns, protruding 0.3 m past the corner and 0.3 m into the wall."""
    for cx, cy, sx, sy, tag in corners:
        bm = bmesh.new()
        k = 0
        while r + k * course < z_top:
            z = r + k * course
            if k % 2 == 0:
                lo, hi = sorted((cx + sx * 0.30, cx - sx * 0.27))
                part = cylinder_bm("x", cy - sy * (T / 2), z, r, lo, hi)
            else:
                lo, hi = sorted((cy + sy * 0.30, cy - sy * 0.27))
                part = cylinder_bm("y", cx - sx * (T / 2), z, r, lo, hi)
            bmesh.ops.recalc_face_normals(part, faces=part.faces)
            temp = bpy.data.meshes.new("_log_tmp")
            part.to_mesh(temp)
            part.free()
            bm.from_mesh(temp)
            bpy.data.meshes.remove(temp)
            k += 1
        finish(f"{prefix}logs_{tag}", bm, [mat], collide=False)


def build_log():
    """Ten metres across, as the photo (Christina, 2 Oct 2026: "go wide"):
    a 6.5 m main block with its gable to the street beside a 3.5 m side
    block whose own lower gable comes 1.6 m forward, the fieldstone chimney
    on the front at their junction. The walls are laid out one by one: the
    main block has no west wall and the side block no east wall behind the
    junction, since those would stand back to back inside the house; the
    side block's gable wall carries on as the wing's east face, 2 cm into
    the main's front wall. The back is two walls meeting at the junction,
    the side block's a centimetre proud so the two share no face. The two
    roofs meet in a valley: the side block's eave is 4 cm lower, its east
    slope and the main's west slope cross just inside the junction wall,
    and the main's eave overhang runs on under the side roof, inside the
    attic."""
    V = LOG
    m = mats(walls="cottage_kit_walls_log", trim="cottage_kit_trim_grey", roof="cottage_kit_roof_shake")
    stone, batten = material("cottage_kit_stone"), material("cottage_kit_walls_batten")
    floor, eave, pitch = V["floor"], V["eave"], V["pitch"]
    head = floor + 2.0
    sill = head - 1.15
    mx0, mx1 = V["main"]
    wx0, wx1, reach = V["wing"]
    cx0, cx1, cdeep, cover = V["chimney"]
    tn = math.tan(math.radians(pitch))
    vt = ROOF_T / math.cos(math.radians(pitch))
    m_half, m_ridge = (mx1 - mx0) / 2, (mx0 + mx1) / 2
    w_half, w_ridge = (wx1 - wx0) / 2, (wx0 + wx1) / 2
    w_eave = eave - 0.04
    yf = -HD - reach                                   # the wing's front
    wall_mats = [m["walls"], m["base"]]
    door_x = (0.1, 1.1)
    e = E_IN
    # (name, origin, u_dir, v_dir, length, foot, top, openings in u, and the
    # same openings in world (axis, face_at, outward, a0, a1, z0, z1, door))
    main_front = [(door_x[0], door_x[1], floor + THRESHOLD, head, True), (2.0, 3.0, sill, head, False), (3.4, 4.4, sill, head, False)]
    wing_front = [(w_ridge - 1.0, w_ridge + 1.0, sill, head, False)]
    west = [(-2.6, -1.4, sill, head, False), (1.0, 2.2, sill, head, False)]
    east = [(-3.0, -1.4, sill, head, False), (0.6, 1.8, sill, head, False)]
    back_main = [(-1.0, 0.2, sill, head, False), (2.0, 3.2, sill, head, False)]
    back_side = [(-3.8, -2.6, sill, head, False)]
    walls = [
        # the main block's front, from 2 cm inside the wing's east wall
        ("wall_front", (mx0 - 0.02, -HD, 0.0), (1, 0, 0), (0, 1, 0), mx1 - e - (mx0 - 0.02), -BELOW,
         Top(row=eave, gable=(m_ridge - (mx0 - 0.02), m_half, eave), pitch=pitch), lambda x: x - (mx0 - 0.02),
         ("x", -HD, -1), main_front),
        # the wing's front, under its own gable
        ("wing_wall_front", (wx0 + e, yf, 0.0), (1, 0, 0), (0, 1, 0), (wx1 - wx0) - 2 * e, -BELOW,
         Top(row=w_eave, gable=(w_half - e, w_half, w_eave), pitch=pitch), lambda x: x - wx0 - e,
         ("x", yf, -1), wing_front),
        # the wing's east face, into the main's front wall
        ("wing_wall_east", (wx1, yf + e, 0.0), (0, 1, 0), (-1, 0, 0), (-HD + 0.02) - (yf + e), -BELOW - 0.01,
         Top(row=head + 0.10, flat=w_eave + 0.08), lambda y: y - (yf + e), ("y", wx1, 1), []),
        # the whole west side, one wall
        ("wall_west", (wx0, HD - e, 0.0), (0, -1, 0), (1, 0, 0), (HD - e) - (yf + e), -BELOW - 0.01,
         Top(row=w_eave, flat=w_eave + WALL_OVER - 0.01), lambda y: HD - e - y, ("y", wx0, -1), west),
        # the east side
        ("wall_east", (mx1, -HD + e, 0.0), (0, 1, 0), (-1, 0, 0), D - 2 * e, -BELOW - 0.01,
         Top(row=eave, flat=eave + WALL_OVER - 0.01), lambda y: y + HD - e, ("y", mx1, 1), east),
        # the back: the main block's, running 6 cm past the junction, and the
        # side block's a centimetre proud, lapping 6 cm the other way
        ("wall_back", (mx1 - e, HD, 0.0), (-1, 0, 0), (0, -1, 0), (mx1 - e) - (mx0 - 0.06), -BELOW,
         Top(row=eave, gable=(mx1 - e - m_ridge, m_half, eave), pitch=pitch), lambda x: mx1 - e - x, ("x", HD, 1), back_main),
        ("wing_wall_back", (mx0 + 0.06, HD + 0.01, 0.0), (-1, 0, 0), (0, -1, 0), (mx0 + 0.06) - (wx0 + e), -BELOW - 0.02,
         Top(row=w_eave, gable=(mx0 + 0.06 - w_ridge, w_half, w_eave), pitch=pitch), lambda x: mx0 + 0.06 - x,
         ("x", HD + 0.01, 1), back_side),
    ]
    for name, origin, u_dir, v_dir, length, foot, top, to_u, (axis, at, out), ops in walls:
        u_ops = [tuple(sorted((to_u(a0), to_u(a1)))) + (z0, z1) for a0, a1, z0, z1, _ in ops]
        wall(name, origin, u_dir, v_dir, length, foot, top, u_ops, floor, wall_mats)
        for k, (a0, a1, z0, z1, is_door) in enumerate(ops):
            opening_trim(f"{name}{k}_trim", m["trim"], axis, at, out, a0, a1, z0, z1, sill=not is_door)
            pane(f"{name}{k}_{'door' if is_door else 'pane'}", m["door"] if is_door else m["glass"], axis, at, out,
                 a0, a1, z0, z1)
    # the two roofs and their caps; the side roof's back rake 2 cm short of
    # the main's, so the two gable ends share no face
    gable_roof("roof", m["roof"], "y", m_ridge, m_half, eave, pitch, V["eave_over"], -HD - V["rake_over"], HD + V["rake_over"])
    ridge_top = eave + m_half * tn + vt
    ridge_cap("ridge_cap", m["roof"], "y", m_ridge, ridge_top, -HD - V["rake_over"], HD + V["rake_over"])
    w_lo, w_hi = yf - V["rake_over"], HD + V["rake_over"] - 0.02
    gable_roof("side_roof", m["roof"], "y", w_ridge, w_half, w_eave, pitch, V["eave_over"], w_lo, w_hi)
    ridge_cap("side_cap", m["roof"], "y", w_ridge, w_eave + w_half * tn + vt, w_lo, w_hi)
    # the wing's board-and-batten gable: a panel 5 cm inside the roof slab
    # (the wall's own top is 3) and a centimetre short of the wall's ends,
    # a king post and two struts, each at its own depth
    peak = w_eave + w_half * tn
    pe = e + 0.01
    panel = [(wx0 + pe, w_eave - 0.05), (wx1 - pe, w_eave - 0.05), (wx1 - pe, w_eave + pe * tn + 0.05),
             (w_ridge, peak + 0.05), (wx0 + pe, w_eave + pe * tn + 0.05)]
    finish("wing_gable_panel", prism_bm(panel, "y", yf - 0.010, yf + 0.02), [batten], collide=False)
    box("wing_king_post", m["trim"], w_ridge - 0.05, w_ridge + 0.05, yf - 0.052, yf + 0.012, w_eave - 0.02, peak + 0.02, collide=False)
    for k, xa in enumerate((wx0 + 0.45, wx1 - 0.45)):
        bar(f"wing_strut_{k}", m["trim"], "y", (xa, w_eave + 0.04), (w_ridge, peak - 0.08), 0.08,
            yf - 0.040 - 0.004 * k, yf + 0.009 - 0.004 * k)
    # the fieldstone chimney on the front at the junction: a broad foot
    # whose west face is inside the wing's east wall, the shaft through the
    # main roof's rake overhang and the side roof's eave, a cap
    box("chimney_foot", stone, cx0 - 0.20, cx1 + 0.20, -HD - cdeep - 0.20, -HD + 0.05, -BELOW - 0.02, 1.50)
    chimney("", stone, cx0, cx1, -HD - cdeep, -HD + 0.03, 1.48, ridge_top + cover)
    # log ends at the five outside corners (the junction is an inside corner)
    corners = [(mx1, -HD, 1, -1, "se"), (wx0, HD, -1, 1, "nw"), (mx1, HD, 1, 1, "ne"),
               (wx0, yf, -1, -1, "wing_sw"), (wx1, yf, 1, -1, "wing_se")]
    log_corners("", m["walls"], corners, eave - 0.05, V["log_r"], V["course"])
    # one step up to the door, the slab's edge clear of the chimney foot's
    stoop("", m, door_x[0] - 0.10, door_x[1] + 0.10, -HD - 0.85, -HD + 0.02, floor, "y", -HD - 0.85, door_x[0] - 0.10,
          door_x[1] + 0.10, -1)


# --- l_ranch: the L-shaped ranch, 8 m wide --------------------------------------

def build_l_ranch():
    V = RANCH
    m = mats(walls="cottage_kit_walls_blue")
    floor, eave, pitch = V["floor"], V["eave"], V["pitch"]
    head = floor + 2.0
    sill = head - 1.10
    bx0, bx1, by0, by1 = V["block"]
    wx0, wx1, wy0, wy1 = V["wing"]
    tn = math.tan(math.radians(pitch))
    vt = ROOF_T / math.cos(math.radians(pitch))
    wall_top = eave + WALL_OVER
    # the block: side gables, the ridge along X
    half_b, ridge_y = (by1 - by0) / 2, (by0 + by1) / 2
    gable_side = Top(row=eave, gable=(half_b - E_IN, half_b, eave), pitch=pitch)
    flat = Top(row=eave, flat=wall_top)
    door_x = (-1.6, -0.6)
    b_open = {
        "front": [(door_x[0], door_x[1], floor + THRESHOLD, head), (-3.6, -2.3, sill, head)],
        "back": [(-3.0, -1.8, sill, head), (-0.4, 0.8, sill, head), (2.0, 3.2, sill, head)],
        "west": [(0.3, 1.5, sill, head), (2.3, 3.5, sill, head)],
    }
    # the block without its east wall: the wing is flush with that end, so
    # the whole east side is one wall below
    shell("", bx0, bx1, by0, by1, -BELOW, {"front": flat, "back": flat, "west": gable_side}, b_open, m["walls"], floor,
          which=("front", "back", "west"))
    corner_boards("", m["trim"], bx0, bx1, by0, by1, -BELOW - 0.03, wall_top + 0.02, which=("sw", "nw", "ne"))
    gable_roof("roof", m["roof"], "x", ridge_y, half_b, eave, pitch, V["eave_over"], bx0 - V["rake_over"], bx1 + V["rake_over"])
    ridge_cap("ridge_cap", m["roof"], "x", ridge_y, eave + half_b * tn + vt, bx0 - V["rake_over"], bx1 + V["rake_over"])
    fit_openings("", b_open, (bx0, bx1, by0, by1), m["trim"], m["glass"], m["door"], doors={("front", 0)}, rails=False)
    # the wing forward to the street, flush with the block's east end
    # (Christina, 2 Oct 2026), its front and west walls here and its east
    # face part of the one east wall; its gable roof runs back into the
    # block's until the block's top has risen over its ridge, and its east
    # eave overhang stops 2 cm short of the block's front eave, returning
    # there, so it never runs on under the block's rake
    w_half, w_ridge = (wx1 - wx0) / 2, (wx0 + wx1) / 2
    wg = Top(row=eave, gable=(w_half - E_IN, w_half, eave), pitch=pitch)
    wf = Top(row=eave, flat=wall_top - 0.01)
    w_open = {"front": [(w_ridge - 0.7, w_ridge + 0.7, sill, head)],
              "west": [(-3.2, -2.0, sill, head)]}
    shell("wing_", wx0, wx1, wy0, wy1, -BELOW - 0.02, {"front": wg, "west": wf}, w_open, m["walls"], floor,
          which=("front", "west"))
    corner_boards("wing_", m["trim"], wx0, wx1, wy0, wy1, -BELOW - 0.05, wall_top + 0.01, which=("sw", "se"))
    fit_openings("wing_", w_open, (wx0, wx1, wy0, wy1), m["trim"], m["glass"], m["door"], rails=False)
    # the east wall, one shell from the wing's front corner to the block's
    # back corner: flat under the wing's eave, a gable under the block's
    e = E_IN
    east_ops = [(-3.0, -1.8, sill, head), (1.0, 2.2, sill, head)]

    def to_u(y):
        return y - (wy0 + e)

    wall("wall_east", (bx1, wy0 + e, 0.0), (0, 1, 0), (-1, 0, 0), (by1 - e) - (wy0 + e), -BELOW - 0.01,
         MixedTop(row=eave, flat=wall_top - 0.01, gable=(to_u(ridge_y), half_b, eave), pitch=pitch),
         [tuple(sorted((to_u(a0), to_u(a1)))) + (z0, z1) for a0, a1, z0, z1 in east_ops], floor, [m["walls"], m["base"]])
    for k, (a0, a1, z0, z1) in enumerate(east_ops):
        opening_trim(f"east{k}_trim", m["trim"], "y", bx1, 1, a0, a1, z0, z1)
        pane(f"east{k}_pane", m["glass"], "y", bx1, 1, a0, a1, z0, z1)
    w_lo = wy0 - V["rake_over"]
    w_hi = by0 + w_half + 0.05 / tn + 0.02      # where the block's top has risen over the wing's ridge cap
    gable_roof_notched("wing_roof", m["roof"], w_ridge, w_half, eave, pitch, V["eave_over"], w_lo, w_hi,
                       by0 - V["eave_over"] - 0.02, wx1 + 0.02)
    ridge_cap("wing_cap", m["roof"], "y", w_ridge, eave + w_half * tn + vt, w_lo, w_hi)
    disc("wing_plaque", m["trim"], "y", w_ridge, head + 0.55, 0.14, wy0 - 0.045, wy0 + 0.010, sides=12)
    # the porch along the set-back front: a slab, three posts, a low shed
    # roof emerging from the block's eave fascia
    pd = V["porch_d"]
    sx0, sx1, sy0 = bx0 - 0.06, wx0 + 0.02, by0 - pd - 0.06
    box("porch_slab", m["concrete"], sx0, sx1, sy0, by0 + 0.03, -0.10, floor)
    ptn = math.tan(math.radians(V["porch_pitch"]))
    y_fascia = by0 - V["eave_over"]
    z_fascia_top = eave - V["eave_over"] * tn + vt - 0.01          # the shed's top meets the fascia a centimetre under its top
    ry = sy0 - 0.30

    def shed_top(y):
        return z_fascia_top + (y - y_fascia) * ptn

    slab("porch_roof", m["roof"], ((bx0 - V["rake_over"] + 0.05, ry, shed_top(ry)), (sx1, ry, shed_top(ry)),
                                   (sx1, by0 + 0.03, shed_top(by0 + 0.03)), (bx0 - V["rake_over"] + 0.05, by0 + 0.03, shed_top(by0 + 0.03))), 0.15)
    post_y = sy0 + 0.04
    for k, x in enumerate((bx0 + 0.10, (bx0 + wx0) / 2, wx0 - 0.30)):
        z_under = shed_top(post_y + 0.16) - 0.15
        box(f"post_{k}", m["trim"], x, x + 0.16, post_y, post_y + 0.16, floor - 0.02, z_under + 0.02)
    steps("", m["concrete"], "y", door_x[0] - 0.10, door_x[1] + 0.10, sy0, floor)


BUILDERS = {"classic": build_classic, "bungalow": build_bungalow, "hip": build_hip, "hip_garage": build_hip_garage,
            "glass_gable": build_glass_gable, "porch": build_porch, "log": build_log, "l_ranch": build_l_ranch,
            "classic_gable": lambda: build_classic(front_door=True)}


# --- reference ---------------------------------------------------------------

def figure(name, x, y, z=0.0, height=FIGURE_H, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring_ = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm = prism_bm(ring_, "z", 0.0, height - 0.40)
    body_verts = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:
        if v not in body_verts:
            v.co.z += height - 0.17
    obj = finish(name, bm, [mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0))], collide=False, flat=False)
    obj.location = (x, y, z)
    return obj


def outline(name, x0, x1, y0, y1, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    for i in range(4):
        bm.edges.new((vs[i], vs[(i + 1) % 4]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    _ctx["coll"].objects.link(obj)
    return obj


def build_reference(reference):
    building(reference, None, prefix="")
    outline("footprint_6x8_body", -HW, HW, -HD, HD)
    outline("footprint_8x8_l_ranch", -RANCH["w"] / 2, RANCH["w"] / 2, -HD, HD)
    outline("footprint_10x8_log", LOG["wing"][0], LOG["main"][1], -HD, HD)
    outline("footprint_garage", -HIP_GARAGE["w"] / 2, HIP_GARAGE["w"] / 2, -HIP_GARAGE["d"] / 2, HIP_GARAGE["d"] / 2)
    figure("figure_1p7m", -4.6, -6.2)
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
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            us = [q.dot(e1) for q in pts]
            vs = [q.dot(e2) for q in pts]
            faces.append((o.name, n, d, min(us), max(us), min(vs), max(vs)))
    # bucket by the plane's normal, rounded, so only candidates are compared
    buckets = {}
    for f in faces:
        n = f[1]
        key = tuple(round(c, 2) for c in n)
        buckets.setdefault(key, []).append(f)
        anti = tuple(round(-c, 2) for c in n)
        if anti != key:
            buckets.setdefault(anti, []).append(f)
    found, seen = [], set()
    for group in buckets.values():
        for i in range(len(group)):
            oi, ni, di, u0, u1, v0, v1 = group[i]
            for j in range(i + 1, len(group)):
                oj, nj, dj, w0, w1, x0, x1 = group[j]
                if oi == oj:
                    continue
                same = (ni - nj).length < 1e-3 and abs(di - dj) < tol
                flipped = (ni + nj).length < 1e-3 and abs(di + dj) < tol
                if not (same or flipped):
                    continue
                if flipped:
                    x0, x1 = -x1, -x0
                ou = min(u1, w1) - max(u0, w0)
                ov = min(v1, x1) - max(v0, x0)
                if ou > 1e-3 and ov > 1e-3:
                    key = (oi, oj, round(di, 4), round(u0, 3), round(w0, 3))
                    if key not in seen:
                        seen.add(key)
                        found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def report(variant, objs):
    bpy.context.view_layer.update()
    objs = [o for o in objs if o.type == "MESH"]
    tris = triangles(objs)
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    pairs = coplanar_pairs(objs)
    used = sorted({s.material.name for o in objs for s in o.material_slots if s.material})
    print(f"cottage_kit: {variant}: {len(objs)} parts, {tris} triangles, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, z {min(zs):.2f}..{max(zs):.2f}; "
          f"{len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    print(f"cottage_kit: {variant}: materials {', '.join(n.replace('cottage_kit_', '') for n in used)}")
    return tris, pairs


# --- renders -----------------------------------------------------------------

LINEUP = (("classic_gable", -39.5), ("classic", -30.0), ("bungalow", -20.5), ("hip", -11.0), ("glass_gable", -1.5),
          ("porch", 8.0), ("log", 19.5), ("l_ranch", 31.5))      # the 10 m cabin and the 8 m ranch on wider lots
GARAGE_BEHIND = (2.3, 10.5)      # the garage's offset from the hip cottage in the lineup


def render(folder, by_variant):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    building(stage, None, prefix="_")
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    ground = mat("_ground", (0.36, 0.44, 0.26))
    lane = mat("_lane", (0.30, 0.30, 0.32))
    box("ground", ground, -80, 80, -80, 80, -0.30, -0.01, collide=False)
    box("lane", lane, -80, 80, -13.5, -8.5, -0.30, 0.0, collide=False)
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
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

    def shoot(name, eye, target, lens=32, size=(1600, 1000)):
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "PERSP"
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 500
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"cottage_kit: rendered {scene.render.filepath}")

    def show(variant):
        for v, objs in by_variant.items():
            for o in objs:
                o.hide_render = v != variant

    # each variant alone, three-quarter from the street at eye height, from
    # the side its photo was taken (the classic's door and the ranch's
    # porch are on the west)
    views = {"hip_garage": ((6.5, -10.0, 1.6), (0.0, -1.0, 1.8), 30), "l_ranch": ((-10.5, -14.0, 1.6), (0.5, -1.5, 2.0), 30),
             "classic": ((-8.0, -13.0, 1.6), (0.0, -2.0, 2.2), 30), "log": ((11.0, -15.5, 1.6), (0.0, -1.5, 2.3), 30),
             "classic_gable": ((-8.0, -13.0, 1.6), (0.0, -2.0, 2.2), 30)}
    for v in VARIANTS:
        show(v)
        eye, target, lens = views.get(v, ((8.0, -13.0, 1.6), (0.0, -2.0, 2.2), 30))
        shoot(f"{v}_three_quarter", eye, target, lens=lens)
    # the classic beside the figure
    show("classic")
    f = figure("figure", -4.3, -6.6, mat=fig)
    shoot("classic_with_figure", (6.5, -11.5, 1.6), (-1.0, -2.5, 2.0), lens=32)
    bpy.data.objects.remove(f, do_unlink=True)
    # the lineup: every variant copied into a row along the lane, the
    # garage behind the hip cottage with its drive beside it
    show(None)
    row = bpy.data.collections.new("_row")
    stage.children.link(row)
    offsets = dict(LINEUP)
    offsets["hip_garage"] = None
    for v, objs in by_variant.items():
        if v == "hip_garage":
            dx, dy = offsets["hip"] + GARAGE_BEHIND[0], GARAGE_BEHIND[1]
        else:
            dx, dy = offsets[v], 0.0
        for o in objs:
            dup = o.copy()
            dup.hide_render = False
            dup.location.x += dx
            dup.location.y += dy
            row.objects.link(dup)
    drive = mat("_drive", (0.62, 0.60, 0.56))
    box("drive", drive, offsets["hip"] + 4.0, offsets["hip"] + 7.0, -8.5, 7.0, -0.012, 0.0, collide=False)
    figure("figure_row", -46.0, -7.5, mat=fig)
    shoot("lineup_street", (-60.0, -19.0, 1.7), (-17.0, -3.0, 2.0), lens=26, size=(2000, 1000))
    shoot("lineup_front", (-4.0, -60.0, 11.0), (-4.0, 0.0, 2.0), lens=26, size=(2000, 1000))
    shoot("lineup_high", (-26.0, -43.0, 26.0), (-4.0, 2.0, 1.0), lens=30, size=(2000, 1000))
    show(None)
    for v, objs in by_variant.items():
        for o in objs:
            o.hide_render = False


# --- main ----------------------------------------------------------------------

def layer_collection(name, root=None):
    root = root or bpy.context.view_layer.layer_collection
    if root.name == name:
        return root
    for child in root.children:
        hit = layer_collection(name, child)
        if hit is not None:
            return hit
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != "cottage_kit":
        raise SystemExit(f"cottage_kit: open cottage_kit.blend, not {name}")
    export, authored, reference = (bpy.data.collections[n] for n in ("export", "authored", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"cottage_kit: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    for v in VARIANTS:
        building(export, v)
        BUILDERS[v]()
    build_reference(reference)
    # the first variant stands in `export` itself; each of the others in its
    # own collection with its eye shut, all at the origin together
    for v in VARIANTS[1:]:
        sub = bpy.data.collections.new(f"variant_{v}")
        export.children.link(sub)
        for o in [o for o in export.objects if o.get("kyt_variant") == v]:
            export.objects.unlink(o)
            sub.objects.link(o)
    bpy.context.view_layer.update()
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    by_variant = {v: [o for o in export.all_objects if o.get("kyt_variant") == v] for v in VARIANTS}
    total, bad = 0, 0
    for v in VARIANTS:
        tris, pairs = report(v, by_variant[v])
        total += tris
        bad += len(pairs)
    print(f"cottage_kit: {len(VARIANTS)} variants, {total} triangles in all, {bad} coplanar pairs in all; "
          f"body {W:.1f} x {D:.1f} m, walls {T:.2f} m thick, ranch {RANCH['w']:.1f} m wide, "
          f"garage {HIP_GARAGE['w']:.1f} x {HIP_GARAGE['d']:.1f} m")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("cottage_kit: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], by_variant)


main()


