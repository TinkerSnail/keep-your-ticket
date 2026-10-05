"""The town's cottage kit, blocked out (2026-10-02) and made cartoony
(2026-10-04): the everyday one-storey houses of the South Shore plan's family
B, one body with the roof, porch, windows and trim swapped, each variant read
off one of Christina's photos in `documentation/reference/houses/`.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/cottage_kit.blend --python tools/blender/cottage_kit.py -- \\
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, nine variants into `export`, each marked
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
              a full-width porch on two posts under its own low roof, a
              hammock slung across it post to post, shutters.
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
              in butter yellow with white trim and a coral door, on stand-ins
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
deck or slab outside it) and is 2.12 m clear over it. Steps follow the park's
stair rule: a narrow ramp is the floor (`tools/gen_props.gd`, `_flight_ramp`),
the treads are scenery showing past it and do not collide
(`kyt_collision = none`). No two shapes share a plane: a part that meets
another laps 2 cm into it or stands proud. `report()` scans every variant for
coplanar overlapping face pairs.

**The cartoony build** (2026-10-04; Christina's "do the cottage kit next",
after the Victorians, and "these would be replacements and not variants").
Every variant was converted in place to the standard
(`documentation/prop-pipeline.md`, Standards applied, "Buildings are
cartoony"), its layout, footprint, features and colours kept, its own ideas
pushed (each builder's docstring says which): few, big pieces, the folksy
ones enlarged; the standard's fat corner boards (0.30, a centimetre off
plumb), single-piece casings 0.16 across, newels, square balusters and fat
rails, all `cartoon_kit`'s; a top-heavy roof of 0.30 slabs and 0.75 m eaves
and rakes (0.90 on the rafter-tail houses) sagging a few centimetres between
the rakes, on fat plain bargeboards; raised shingle clusters on the painted
shingle grid and a few vent pipes on the back half; trim under an eave that
carries an accent in its shade (`shade`); a seeded hand (`SEEDS`, a trim seed
and a shingle seed per variant), with decks, sills, thresholds and ramps
exact. The walls stay plumb. The bell-cast kick is on the steep classic pair
and the shake-roofed log cabin; the others stay plain (`cartoon_kit`'s
PlainRoof): rafter tails (bungalow, glass gable), a low roof where a kick of
half its pitch is a crease (hip, its garage, the ranch, whose porch roof
springs from the block's eave), and a metal roof (the porch cottage, which has
no raised shingles either). The doors' 2.12 m clear and the casings' fat
heads raised some eaves (the walls 2.4 to 2.8 m from floor to eave). The
pieces more than one house needs are in `cartoon_kit` (the plain roof, the
quarter turn for a roof whose ridge runs along X, rafter tails, knee braces,
round windows and plaques, shutters, the hammock, log ends, the stone stack,
the brick chimney); each house's composition is here.

Materials are flat stand-ins named `cottage_kit_<surface>`, the wall and trim
colours per photo; battens, laps, shingles, logs, stones and window bars are
painting. Everything the tool makes carries `kyt_cottage_kit`, so a rerun
removes and rebuilds its own work and keeps anything of hers; `export` holding
anything untagged refuses without `--replace`. `--save` writes the file;
`--render` shoots after the save, so no camera, light or stage reaches the
file; `cartoon_preview.py` renders the painted stand-ins.
"""

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartoon_kit as ck  # noqa: E402

TAG = "kyt_cottage_kit"
VARIANTS = ("classic", "bungalow", "hip", "hip_garage", "glass_gable", "porch", "log", "l_ranch", "classic_gable")

# --- the kit's constants ---------------------------------------------------
W, D = 6.0, 8.0            # the body: across the front, and deep
HW, HD = W / 2, D / 2
T = 0.20                   # wall thickness
BELOW = 0.05               # how far the walls reach below the ground
CORNER = 0.30              # the corner boards (the realistic kit's 0.26), 4 cm proud of the walls and a centimetre off plumb
PROUD = 0.04
E_IN = CORNER / 2 - PROUD  # the walls stop this short of the corners, under the boards
THRESHOLD = 0.01           # a door's sill over the floor outside it (the door is shut)
FIGURE_H = 1.70

# each variant's numbers, read off its photo; every one is a guess to be corrected
CLASSIC = dict(pitch=45.0, eave=2.85, floor=0.30, window=1.62, risers=2, grade=0.5,
               chimney=(0.76, 0.76, 1.9, 1.0),      # across, deep, y on the ridge, height over the ridge's top
               hood=(1.8, 1.0, 20.0, 0.15),         # the shed hoods' width, reach, pitch and slab
               sun_half=1.55, sunburst=(0.32, (20.0, 55.0, 90.0, 125.0, 160.0), (6.0, 9.5), 0.16),  # its hub's half-width of gable; hub, rays, wedges, collar
               door_y=(-2.3, -1.3), gable_door_x=(-0.5, 0.5), gable_side_door_y=(1.1, 2.1))
BUNGALOW = dict(pitch=20.0, eave=2.75, floor=0.30, eave_over=0.90, porch=(3.6, 1.8), sill=0.85, window_head=2.28,  # the sun porch across and deep
                tails=10, tail_past=0.10, brace=(0.72, 0.80), risers=2, grade=0.5,   # rafter tails a side, their ends past the eave; the knee braces' reach and drop
                header=(0.26, 0.08))                                  # the entry's header: under the eave, proud of the porch's face
HIP = dict(pitch=20.0, eave=3.00, floor=0.60, window=1.20, risers=3, grade=0.5,
           gable=(1.0, 40.0, 0.22, 0.22, 0.25, 0.12),   # the little gable: half span, pitch, slab, eave over, rake over, proud of the fascia
           vent=(0.70, 0.55, 0.68), stoop=(1.84, 1.2),  # vent: across, tall, its centre under the ridge's underside (its casing clear of the soffit); the stoop wide and deep
           flue=(0.46, 1.6, 1.5, 0.9))                  # across, x, y, height over the roof
HIP_GARAGE = dict(w=3.5, d=6.0, pitch=20.0, eave=2.40, door=(2.4, 2.12))   # the door across and clear
GLASS = dict(pitch=35.0, eave=2.50, floor=0.0, over=0.90, sill=0.90, window_head=2.00,  # the eaves and rakes deep
             mullions=(-1.0, 0.4), mullion=0.14, rake_band=0.16,   # the glass wall's fat bars: x, across; the band under the rakes
             tails=9, tail_past=0.10, brace=(0.85, 1.10))          # rafter tails a side, their ends past the eave; the knee braces' reach and drop
PORCH = dict(pitch=32.0, eave=3.25, floor=0.45, porch_d=2.1, risers=2, grade=0.5,
             window=(0.44, 4.12), shutter=0.32,                # the round window's radius and centre; the shutters across
             shed=(2.86, 0.07, 0.24), shed_over=0.40, shed_end=0.10,   # its underside at the wall, fall, slab; its eave past the beam, its ends past the walls
             post_in=0.35, posts_x=(-2.90, 2.90), beam=0.22, fascia=0.26,
             hammock=(1.75, 0.55, 0.95, 1.0))                  # its hooks over the deck, sag, width, and how far in from the hooks its bed begins
LOG = dict(pitch=28.0, eave=2.60, floor=0.15,
           main=(-1.5, 5.0), wing=(-5.0, -1.5, 1.6),             # 10 m across (Christina: "go wide"): the main block's x, the side block's x and its reach forward
           door_x=(0.25, 1.25),                                  # 15 cm east of the old, so the chimney's foot clears its casing
           chimney=(-1.35, -0.15, 0.70, 1.35), chimney_foot=0.16,  # chimney x0, x1, deep, height over the ridge's top; the foot wider each side (to the door's casing)
           shoulder=(1.30, 0.40), stones=[(1.72, 2.26), (4.15, 5.45)],  # the foot's top and the shoulder; the bands whole raised stones fit in, under the eaves and over the roof
           log_r=0.17, course=0.34,                              # fat log ends, a log every 0.34 m
           truss=((-0.10, 0.08), 0.16, 0.13))                    # the side gable's truss: its tie under and over the eave, king post, struts
RANCH = dict(w=8.0, pitch=20.0, eave=2.65, floor=0.15,
             wing=(0.55, 4.0, -4.0, -1.0), block=(-4.0, 4.0, -1.0, 4.0), porch_d=1.9,  # the wing flush with the block's end (Christina)
             porch_pitch=10.0, porch_over=0.30, porch_slab=0.22, fascia=0.24, posts_x=(-3.70, -2.10, -0.50))

PLAN_COLOURS = ("e8a68a", "9fc9d6", "f2d27a", "b9d39a", "e9b6c8")   # the plan's `.b-cot1` to `.b-cot5`


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


HEX = {
    "cottage_kit_walls": "bcd6e4",               # the classic's pale blue
    "cottage_kit_walls_white": "f1ede3",         # the bungalow's lap siding
    "cottage_kit_walls_sky": "62aee6",           # the hip cottage, the glass gable's shingle
    "cottage_kit_walls_pink": "f06d9a",
    "cottage_kit_walls_log": "5b3b2b",
    "cottage_kit_walls_blue": "4a78b0",          # the ranch's medium blue
    "cottage_kit_walls_batten": "6e4a35",        # the log cabin's board-and-batten gables: dark brown boards, as the photo's, a shade warmer than the logs (was a light tan, 2026-10-05)
    "cottage_kit_trim": "f4f1ea",
    "cottage_kit_trim_teal": "1c9fb3",
    "cottage_kit_trim_blue": "2a5c9c",
    "cottage_kit_trim_grey": "7f98aa",
    "cottage_kit_trim_orange": "f2a233",
    "cottage_kit_trim_mint": "7fd0b0",
    "cottage_kit_roof": "5a5047",                # grey shingle
    "cottage_kit_roof_shake": "6e5a3c",
    "cottage_kit_roof_metal": "8b9196",
    "cottage_kit_glass": "3e5566",
    "cottage_kit_door": "2e8b8f",
    "cottage_kit_door_cobalt": "1f3fbf",
    "cottage_kit_porch": "a67c52",
    "cottage_kit_base": "b8b4ac",
    "cottage_kit_brick": "9a4b3b",
    "cottage_kit_stone": "a9a08f",
    "cottage_kit_fabric": "e89ab4",
    "cottage_kit_concrete": "c6c2ba",
    "cottage_kit_vent": "7d8a94",               # the cartoony roofs' vent pipes, as the Victorians'
}
COLOURS = {k: srgb(v) for k, v in HEX.items()}


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


def shade(name, hex6=None):
    """A trim colour's shaded twin, `<name>_shade`, a shade darker (0.72 of
    it, as the Victorians' accent_shade), for the trim tucked under an eave,
    as if in its shadow (her "the red under the eves can be a little darker
    as if its in shadpw", 2026-10-04)."""
    hex6 = hex6 or HEX[name]
    dark = "".join(f"{round(int(hex6[i:i + 2], 16) * 0.72):02x}" for i in (0, 2, 4))
    return material(f"{name}_shade", srgb(dark))


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


def shell(prefix, x0, x1, y0, y1, z_foot, tops, openings, walls_mat, base_below, which=ALL_WALLS, lap=0.02, base_mat=None,
          e=None):
    """Walls as closed shells round the rectangle (x0, x1, y0, y1), their
    ends lost inside the corner boards (E_IN short of each corner). `tops`
    holds a Top per wall, `openings` per wall a list of (a0, a1, z0, z1) in
    world x (front, back) or world y (west, east) and absolute z. The side
    walls' feet are a centimetre lower than the end walls', because crossing
    shells may not share a bottom. A wall left out of `which` is another
    body's wall: the side walls then run `lap` into it instead. The faces
    below `base_below` take `base_mat`, the shared base unless given. `e`
    is how far short of the corners the walls stop, E_IN unless given."""
    base = base_mat or material("cottage_kit_base")
    e = E_IN if e is None else e
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


def pane(name, mat, axis, face_at, outward, a0, a1, z0, z1, recess=0.08, thick=0.05, collide=True):
    """A slab set in an opening, recessed into the wall, 2 cm into the
    reveals all round."""
    lo, hi = sorted((face_at - recess * outward, face_at - (recess + thick) * outward))
    if axis == "x":
        return box(name, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, collide=collide)
    return box(name, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, collide=collide)


def mats(walls="cottage_kit_walls", trim="cottage_kit_trim", roof="cottage_kit_roof", door="cottage_kit_door"):
    """The stand-in materials a variant builds with, by surface."""
    return dict(walls=material(walls), trim=material(trim), roof=material(roof), door=material(door),
                glass=material("cottage_kit_glass"), porch=material("cottage_kit_porch"),
                base=material("cottage_kit_base"), concrete=material("cottage_kit_concrete"),
                vent=material("cottage_kit_vent"))


# --- the cartoony build (2026-10-04) -------------------------------------------
# The standard (`documentation/prop-pipeline.md`, Standards applied,
# "Buildings are cartoony"), as the Victorian took it: few, big pieces with
# the folksy ones enlarged, a top-heavy roof, a seeded hand. Its pieces are
# `cartoon_kit`'s (ck); each variant's own composition is in its builder.
CC_SLAB = 0.30             # the roof slab (the kit's 0.20)
CC_OVER = 0.75             # the eaves and rakes (the kit's 0.25 to 0.75)
CC_SAG = 0.04              # the ridge and eaves dip this much at mid-length
CC_KICK = dict(kick_at=0.10, kick_t=0.24, kick_in=0.35)   # the bell-cast kick, as the Victorian's; its pitch half the main's
CC_PANE_RECESS = 0.06
CC_HEAD = THRESHOLD + 2.12   # a door's head over its floor, 2.12 m clear (the kit's were 1.94 to 2.09); the windows' head line with it
CC_BARGE = (0.30, 0.10)    # a plain bargeboard's board and band, both the trim
CC_MEETING = 0.08          # a double-hung window's fat meeting rail, tall
CC_VENTS = ((-1, 2), (1, 1))   # vent pipes on the back half: two on the west slope, one on the east

# each variant's own hand and its own roof's (cartoon_kit's two seeds)
SEEDS = {"classic": (20261011, 20261012), "classic_gable": (20261013, 20261014), "hip": (20261015, 20261016),
         "hip_garage": (20261017, 20261018), "bungalow": (20261019, 20261020), "glass_gable": (20261021, 20261022),
         "porch": (20261023, 20261024), "l_ranch": (20261025, 20261026), "log": (20261027, 20261028)}


def wall_top_in(pitch_deg, slab=CC_SLAB):
    """A side wall's top over the eave, inside the slab at both its faces: the
    middle of where the slab's underside over the inner face and its top
    over the outer face leave room."""
    p = math.radians(pitch_deg)
    return round((T * math.tan(p) + slab / math.cos(p)) / 2, 2)


def cartoon_corners(rng, mat, x0, x1, y0, y1, z0, z1, which=("sw", "se", "nw", "ne"), prefix=""):
    """Fat corner boards, CORNER square and 4 cm proud of both faces, each
    sheared up to a centimetre off plumb (cartoon_kit's lathe, level rings),
    their feet in the ground and their tops in the roof."""
    h = CORNER / 2
    for sx, sy, tag in ((-1, -1, "sw"), (1, -1, "se"), (-1, 1, "nw"), (1, 1, "ne")):
        if tag not in which:
            continue
        cx = (x0 - PROUD + h) if sx < 0 else (x1 + PROUD - h)
        cy = (y0 - PROUD + h) if sy < 0 else (y1 + PROUD - h)
        ck.lathe(finish, f"{prefix}corner_{tag}", mat, cx, cy, [(h, h, z0), (h, h, z1)],
                 lean=(ck.jit(rng, 0.01) / (z1 - z0), ck.jit(rng, 0.01) / (z1 - z0)))


def cartoon_openings(rng, prefix, openings, rect, m, doors=(), lights=None, meeting=()):
    """A single-piece casing round every opening of `openings` (the shell's
    dict), the standard's 0.16 across with its fat head (cartoon_kit's),
    `lights` across by (face, index), and its pane or door leaf set in;
    doors (by (face, index)) have no sill. A window in `meeting` gets a fat
    meeting rail across its pane, the double-hung look."""
    x0, x1, y0, y1 = rect
    lights = lights or {}
    faces = {"front": ("x", y0, -1), "back": ("x", y1, 1), "west": ("y", x0, -1), "east": ("y", x1, 1)}
    for face, ops in openings.items():
        axis, at, out = faces[face]
        for k, (a0, a1, z0, z1) in enumerate(ops):
            door = (face, k) in doors
            ck.casing(finish, rng, f"{prefix}{face}{k}_casing", m["trim"], axis, at, out, a0, a1, z0, z1,
                      lights=lights.get((face, k), 1), sill=not door)
            pane(f"{prefix}{face}{k}_{'door' if door else 'pane'}", m["door"] if door else m["glass"], axis, at, out,
                 a0, a1, z0, z1, recess=CC_PANE_RECESS)
            if (face, k) in meeting:
                # 5 mm in front of the pane, 1.5 cm behind the wall's face, its
                # ends in the reveals and behind the casing's jambs
                lo, hi = sorted((at - 0.015 * out, at - 0.055 * out))
                zm = (z0 + z1) / 2
                if axis == "x":
                    box(f"{prefix}{face}{k}_rail", m["trim"], a0 - 0.01, a1 + 0.01, lo, hi, zm - CC_MEETING / 2, zm + CC_MEETING / 2,
                        collide=False)
                else:
                    box(f"{prefix}{face}{k}_rail", m["trim"], lo, hi, a0 - 0.01, a1 + 0.01, zm - CC_MEETING / 2, zm + CC_MEETING / 2,
                        collide=False)


def flight_x(prefix, mat, y0, y1, x_edge, out, z_top, risers, grade):
    """cartoon_kit's flight running along X (out -1 toward -X) from a deck's
    edge at x_edge, y0..y1 wide: built along Y in the quarter-turned frame
    (local x = -y, local y = x) and turned back."""
    return ck.flight(ck.quarter_turn(finish), prefix, mat, -y1, -y0, x_edge, out, z_top, risers, grade, BELOW)


def roof_dressing(rng, m, roof, avoid=None, scattered=3, vents=CC_VENTS, fin=None, part="roof_shingles", vent_part="roof_vent",
                  kick_avoid=None):
    """The bell (or plain) roof's raised shingle clusters and its vent pipes,
    from the variant's shingle seed (cartoon_kit's roof_clusters and
    roof_vents): a cluster at a rake and one on the eave of each slope, then
    `scattered` more; the vents on the back half, clear of every tab and of
    `avoid` (`kick_avoid` keeps the eave's cluster off what stands on it).
    Built through `fin` (a quarter-turned finish for a roof whose
    ridge runs along X). Returns (tabs, vents)."""
    fin = fin or finish
    bm = bmesh.new()
    tabs, mains = ck.roof_clusters(rng, bm, roof, avoid=avoid, scattered=scattered, kick_avoid=kick_avoid)
    fin(part, bm, [m["roof"]], collide=False)
    n = ck.roof_vents(fin, rng, [m["vent"], m["glass"]], roof, mains, counts=vents, part=vent_part) if vents else 0
    return tabs, n


def plain_barges(rng, m, roof, mat=None, fin=None, prefix="barge", band=None, names=("front", "back")):
    """Plain fat bargeboards (cartoon_kit's barge, no drops) over both rakes,
    following the roof's profile and its kick, in the trim (or `mat`; `band`
    for the band under it, the trim's shade when it carries an accent)."""
    fin = fin or finish
    mat = mat or m["trim"]
    for face, y_rake, out in ((names[0], roof.y0, -1), (names[1], roof.y1, 1)):
        knees = [roof.r_k] if roof.r_k > roof.half + 1e-6 else []
        ck.barge(fin, rng, f"{prefix}_{face}", [mat, band or mat], roof.profile, knees, roof.r_out + 0.05, roof.xc, y_rake, out,
                 CC_BARGE[0], CC_BARGE[1], ())


# --- classic: the steep gable with the sunburst ------------------------------

def sunburst(rng, m, roof, y_rake, zc, hub, rays, wedge, bar):
    """The classic's sunburst in its front peak, pushed (the photo's fine
    slats made five fat wedges): across the rake, behind the bargeboard,
    where the deep rake no longer hides it (as the Victorian's), one white
    plate of convex pieces welded on their shared edges: a collar bar across
    the gable at the hub's foot (`bar` deep, its ends 3 cm up in the slab's
    underside), a big half-disc hub (`hub` its radius) on it, and the rays,
    wedges `wedge` (half-angles at the hub and the tip) reaching to 3 cm up
    in the rakes' underside. Each ray a little different in angle, width and
    reach, as sawn by hand."""
    tan, half, eave = roof.tan, roof.half, roof.eave
    peak = eave + half * tan + 0.03          # the underside at the ridge, 3 cm up in it

    def x_at(z):                             # where the underside is 3 cm under z
        return half - (z - 0.03 - eave) / tan

    def pol(r, deg):
        return (r * math.cos(math.radians(deg)), zc + r * math.sin(math.radians(deg)))

    def tip(deg):                            # out along deg to 3 cm up in the underside
        a = math.radians(deg)
        return pol((peak - zc) / (math.sin(a) + abs(math.cos(a)) * tan), deg)
    drawn = [(th + ck.jit(rng, 2.0), wedge[0] + ck.jit(rng, 0.8), wedge[1] + ck.jit(rng, 1.2)) for th in rays]
    hub_pts = {0.0: (hub, zc), 180.0: (-hub, zc)}
    for t, a, b in drawn:
        hub_pts[t - a], hub_pts[t + a] = pol(hub, t - a), pol(hub, t + a)
    z0 = zc - bar
    polys = [([(-x_at(z0), z0), (x_at(z0), z0), (x_at(zc), zc), (hub, zc), (-hub, zc), (-x_at(zc), zc)], 0),
             ([hub_pts[d] for d in sorted(hub_pts)], 0)]
    for t, a, b in drawn:
        polys.append(([hub_pts[t - a], tip(t - b), tip(t + b), hub_pts[t + a]], 0))
    ck.plate(finish, "sunburst", [m["trim"]], polys, "y", y_rake + 0.03, y_rake + 0.10, collide=False)


def door_hood(rng, prefix, m, axis, face, out, c, z_wall, width, reach, pitch_deg, thick):
    """A shed hood over a door, pushed: a fat slab `thick` deep (plumb), from 2
    cm inside the wall at `face` (facing `out`) out `reach`, falling at
    pitch_deg, its underside at the wall z_wall (lapped into the door
    casing's head), `width` across centred on c, `axis` 'x' when the width
    runs along X; on two fat shaped brackets (cartoon_kit's) whose tops
    follow its underside, 2 cm up in it."""
    t = math.tan(math.radians(pitch_deg))
    a0, a1 = c - width / 2, c + width / 2

    def P(a, s, z):                          # a across, s out from the wall's face
        return (a, face + out * s, z) if axis == "x" else (face + out * s, a, z)

    def top(s):
        return z_wall + thick - s * t
    slab(f"{prefix}hood", m["roof"], (P(a0, -0.02, top(-0.02)), P(a1, -0.02, top(-0.02)), P(a1, reach, top(reach)),
                                      P(a0, reach, top(reach))), thick, collide=False)
    for tag, a in (("a", a0 + 0.12), ("b", a1 - 0.12)):       # clear of the door casing's jambs
        ck.shaped_bracket(finish, rng, f"{prefix}hood_bracket_{tag}", m["trim"], "y" if axis == "x" else "x", a, face, out,
                          z_wall + 0.02, 0.62, 0.58, width=0.12, foot=0.11, band=0.12, slope=t)


def build_classic(front_door=False):
    """The classic, cartoony (2026-10-04); with `front_door`, the
    `classic_gable` variant (Christina's rule, 3 Oct 2026: either/or questions
    become variants): the same body, roof, chimney, sunburst and trim, the
    front door on the gable face under a hood of its own up two steps, the
    side door moved back along the west side, and colours of its own. Pushed
    from the photo: the steep grey street gable (45 degrees, a 0.30 slab, a
    bell-cast kick of 22.5 to 0.75 m eaves and rakes, fat plain white
    bargeboards), its sunburst made five fat wedges on a collar across the
    rake, the brick chimney on the ridge fat and corbelled, the tall windows
    taller with a fat meeting rail, the side door's shed hood fat on shaped
    brackets."""
    V = CLASSIC
    v = "classic_gable" if front_door else "classic"
    if front_door:
        # its own stand-ins on every surface (Christina, 3 Oct 2026: "on the
        # variations lets change the colors", "can the doors be different
        # colors too"): butter-yellow walls, the plan's cottage yellow, white
        # trim, coral doors since the classic's are teal; the roof and the
        # brick the classic's colours, but materials of its own too
        m = dict(walls=own_material(v, "walls", hex6=PLAN_COLOURS[2]), trim=own_material(v, "trim", "cottage_kit_trim"),
                 roof=own_material(v, "roof", "cottage_kit_roof"), door=own_material(v, "door", hex6="ee7656"),
                 glass=own_material(v, "glass", "cottage_kit_glass"), base=own_material(v, "base", "cottage_kit_base"),
                 concrete=own_material(v, "concrete", "cottage_kit_concrete"), vent=own_material(v, "vent", "cottage_kit_vent"))
        brick = own_material(v, "brick", "cottage_kit_brick")
    else:
        m = mats()
        brick = material("cottage_kit_brick")
    trim_seed, shingle_seed = SEEDS[v]
    rng = random.Random(trim_seed)
    floor, eave, pitch = V["floor"], V["eave"], V["pitch"]
    tan = math.tan(math.radians(pitch))
    head = floor + CC_HEAD                   # the photo's doors and windows share a head line under the eave
    sill = head - V["window"]                # the tall double-hung windows, taller
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
    windows = {(f, k) for f, ops in openings.items() for k in range(len(ops)) if (f, k) not in doors}

    # -- the body: walls with gables front and back, fat corner boards,
    # single-piece casings, panes and doors, a fat meeting rail on each window
    top_in = wall_top_in(pitch)
    gable = Top(row=eave, gable=(HW - E_IN, HW, eave), pitch=pitch)
    flat = Top(row=eave, flat=eave + top_in)
    shell("", -HW, HW, -HD, HD, -BELOW, {"front": gable, "back": gable, "west": flat, "east": flat}, openings, m["walls"], floor,
          base_mat=m["base"])
    cartoon_corners(rng, m["trim"], -HW, HW, -HD, HD, -BELOW - 0.03, eave + top_in + 0.02)
    cartoon_openings(rng, "", openings, (-HW, HW, -HD, HD), m, doors=doors, meeting=windows)

    # -- the roof, the heavy part: cartoon_kit's bell roof, fat plain barges
    y0, y1 = -HD - CC_OVER, HD + CC_OVER
    roof = ck.bell_roof(finish, m["roof"], 0.0, HW, eave, math.radians(pitch), CC_SLAB, y0, y1, sag=CC_SAG,
                        kick_deg=pitch / 2, eave_over=CC_OVER, **CC_KICK)
    plain_barges(rng, m, roof)
    # the sunburst across the front rake, its hub where the gable is 3.1 m across
    sunburst(rng, m, roof, y0, eave + (HW - V["sun_half"]) * tan, *V["sunburst"])
    # the brick chimney straddling the ridge, fat and corbelled, its foot in the attic
    cw, cd, cy, ch = V["chimney"]
    ck.brick_chimney(finish, rng, "", [brick], 0.0, cy, cw / 2, cd / 2, roof.rt - 0.70, roof.rt + ch - 0.42, roof.rt + ch)

    # -- the side door under its fat shed hood, its landing and two risers
    hw_, hr, hp, ht = V["hood"]
    z_hood = head + 0.15                     # 2 cm or more into the casing's fat head
    door_hood(rng, "", m, "y", -HW, -1, (dy0 + dy1) / 2, z_hood, hw_, hr, hp, ht)
    box("landing", m["concrete"], -HW - 0.90, -HW + 0.02, dy0 - 0.10, dy1 + 0.10, -0.10, floor)
    # (the flights a centimetre in from the landing's sides, so the two share no face)
    flight_x("stair", m["concrete"], dy0 - 0.09, dy1 + 0.09, -HW - 0.90, -1, floor, V["risers"], V["grade"])
    if front_door:
        # the same hood, landing and flight on the gable face, under the sunburst
        door_hood(rng, "front_", m, "x", -HD, -1, (fx0 + fx1) / 2, z_hood, hw_, hr, hp, ht)
        box("front_landing", m["concrete"], fx0 - 0.10, fx1 + 0.10, -HD - 0.90, -HD + 0.02, -0.10, floor)
        ck.flight(finish, "front_stair", m["concrete"], fx0 - 0.09, fx1 + 0.09, -HD - 0.90, -1, floor, V["risers"], V["grade"], BELOW)

    # -- the roof's raised shingle clusters and vents, from its own seed, clear of the chimney
    box_ = (0.0, cw / 2 + 0.25, cy - cd / 2 - 0.25, cy + cd / 2 + 0.25)
    tabs, vents = roof_dressing(random.Random(shingle_seed), m, roof, avoid={1: [box_], -1: [box_]})
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=CC_OVER, rake_over=CC_OVER, kick=pitch / 2, tabs=tabs, vents=vents,
                door_clear=head - floor - THRESHOLD)


# --- bungalow: low gable, deep eaves, the glazed sun porch -------------------

def build_bungalow():
    """The craftsman bungalow, cartoony (2026-10-04), its ideas pushed: the
    deep eaves deeper (0.90) on fat rafter tails, few and big (ten a side,
    0.20 deep with a plumb cut over a bevel, their ends 10 cm out past the
    eave's edge so they show from the street), and four big knee braces at the
    gables' corners, all in the teal's shade under the eaves; the glazed sun
    porch at the front corner in few big lights between fat mullions; the
    covered entry on two fat timber posts under a fat header; fat teal
    barges. The roof is plain (a 0.30 slab at 20 degrees): a bell-cast kick
    would bend the eave away from its rafter tails."""
    V = BUNGALOW
    m = mats(walls="cottage_kit_walls_white", trim="cottage_kit_trim_teal")
    teal_shade = shade("cottage_kit_trim_teal")
    trim_seed, shingle_seed = SEEDS["bungalow"]
    rng = random.Random(trim_seed)
    floor, eave, pitch = V["floor"], V["eave"], V["pitch"]
    pw, pd = V["porch"]
    px0, px1, py0 = -HW, -HW + pw, -HD - pd           # the sun porch fills the front's west
    sill, head = V["sill"], floor + CC_HEAD
    wh = V["window_head"]                    # the windows' head, lower than the door's, so their casings clear the rafter tails
    openings = {
        "front": [(1.4, 2.4, floor + THRESHOLD, head)],
        "back": [(-2.2, -1.0, sill, wh), (1.0, 2.2, sill, wh)],
        "west": [(-2.0, -0.8, sill, wh), (1.0, 2.2, sill, wh)],
        "east": [(-3.0, -1.8, sill, wh), (0.6, 1.8, sill, wh)],
    }
    # -- the body: its front wall gabled too, since the entry bay looks up at it
    top_in = wall_top_in(pitch)
    gable = Top(row=eave, gable=(HW - E_IN, HW, eave), pitch=pitch)
    flat = Top(row=eave, flat=eave + top_in)
    shell("", -HW, HW, -HD, HD, -BELOW, {"front": gable, "back": gable, "west": flat, "east": flat}, openings, m["walls"], floor,
          base_mat=m["base"])
    cartoon_corners(rng, m["trim"], -HW, HW, -HD, HD, -BELOW - 0.03, eave + top_in + 0.02)
    cartoon_openings(rng, "", openings, (-HW, HW, -HD, HD), m, doors={("front", 0)})

    # -- the roof over the body, the sun porch and the entry bay, plain, with
    # its deep eaves; fat teal barges on its rakes
    tan = math.tan(math.radians(pitch))
    roof = ck.plain_roof(finish, m["roof"], 0.0, HW, eave, math.radians(pitch), CC_SLAB, py0 - CC_OVER, HD + CC_OVER,
                         sag=CC_SAG, eave_over=V["eave_over"])
    plain_barges(rng, m, roof)

    # -- the sun porch: a low wall under big windows on its front and west, its
    # east wall rising to the roof (the entry bay sees it), 2 cm into the body;
    # few big lights between fat mullions, its corner board
    porch_rect = (px0, px1, py0, -HD)
    # the porch's windows, their head under the header (which their casings' fat heads would run into)
    p_head = eave - V["header"][0] - ck.CASING_HEAD - 0.03
    low = Top(row=p_head + 0.15, flat=eave + 0.02)
    tall = Top(row=p_head + 0.15, flat=eave + (HW - px1 + T / 2) * tan + 0.03)
    p_open = {"front": [(px0 + 0.40, px1 - 0.40, sill, p_head)], "west": [(py0 + 0.45, -HD - 0.45, sill, p_head)]}
    shell("porch_", px0, px1, py0, -HD, -BELOW - 0.035, {"front": low, "west": low, "east": tall}, p_open, m["walls"], floor,
          which=("front", "west", "east"), base_mat=m["base"])
    cartoon_openings(rng, "porch_", p_open, porch_rect, m, lights={("front", 0): 3, ("west", 0): 2})
    cartoon_corners(rng, m["trim"], px0, px1, py0, -HD, -BELOW - 0.05, eave + 0.04, which=("sw",), prefix="porch_")
    # the gable wall over the porch and the entry bay, 3 cm behind the porch's
    # face and a centimetre short of its ends, its foot inside the fat header
    g = Top(row=eave, gable=(HW - E_IN - 0.01, HW, eave), pitch=pitch)
    wall("gable_front", (-HW + E_IN + 0.01, py0 + 0.03, 0.0), (1, 0, 0), (0, 1, 0), W - 2 * E_IN - 0.02, eave - 0.12, g, [],
         -1.0, [m["walls"], m["base"]])
    # the fat header across the porch and the entry, in the teal's shade under the rake
    hd_, hp_ = V["header"]
    box("header", teal_shade, -HW - 0.05, HW + 0.05, py0 - hp_, py0 + 0.26, eave - hd_, eave + 0.12, collide=False)

    # -- the entry bay: a landing up two risers, and fat timber posts at the
    # porch's corner and the body's, into the header
    lx0, lx1 = px1 - 0.02, HW - 0.02
    box("landing", m["concrete"], lx0, lx1, py0 + 0.02, -HD + 0.03, -0.10, floor)
    ck.flight(finish, "stair", m["concrete"], 1.3, 2.5, py0 + 0.02, -1, floor, V["risers"], V["grade"], BELOW)
    for tag, x in (("w", px1 - 0.01), ("e", HW - 0.11)):
        ck.timber_post(finish, rng, f"post_{tag}", m["trim"], x, py0 + 0.10, -BELOW, (floor + 0.10, floor + 0.16), eave - hd_,
                       eave - hd_ + 0.06, size=0.30, block=0.20, collar=0.18)

    # -- the deep eaves on fat rafter tails, ten a side, and the four big knee
    # braces at the gables' corners, in the teal's shade
    n = V["tails"]
    ys = [py0 + 0.40 + (HD - 0.40 - py0 - 0.40) * k / (n - 1) for k in range(n)]
    for tag, s in (("w", -1), ("e", 1)):
        ck.rafter_tails(finish, rng, f"tails_{tag}", teal_shade, roof, s, ys, short=-V["tail_past"])
        for face, y_face, y_out in (("front", py0, -1), ("back", HD, 1)):
            sag = ck.sag_at(roof.stations, y_face)
            ck.knee_brace(finish, rng, f"{face}_brace_{tag}", teal_shade, s * HW, s, y_face, y_out,
                          lambda x, sag=sag: roof.under(x) - sag, *V["brace"])

    tabs, vents = roof_dressing(random.Random(shingle_seed), m, roof)
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=V["eave_over"], rake_over=CC_OVER, kick=0.0, tabs=tabs,
                vents=vents, door_clear=head - floor - THRESHOLD, extra=f"; {n} rafter tails a side")


# --- hip: the low side gable with the little gable over the stoop -------------

def louvred_vent(rng, prefix, mat, side, out, vw, vh, zc, slats=3):
    """A louvred vent near a side gable's peak, pushed fat: cartoon_kit's
    single-piece casing round it and `slats` fat louvre blades, each a wedge
    thin at its head and proud at its foot, as a louvre tilts, their ends in
    the casing's jambs and their backs 2 cm into the wall (at x = side,
    facing `out`); all in `mat`, the trim's shade, as it is under the rake
    (the blades were the walls' colour, and vanished into the wall)."""
    z0, z1 = zc - vh / 2, zc + vh / 2
    ck.casing(finish, rng, f"{prefix}", mat, "y", side, out, -vw / 2, vw / 2, z0, z1)
    p = (vh - 0.04) / slats
    for k in range(slats):
        zb, zt = z0 + 0.02 + k * p + 0.015, z0 + 0.02 + (k + 1) * p - 0.015
        sec = [(side - out * 0.02, zt), (side + out * 0.015, zt), (side + out * 0.055, zb), (side - out * 0.02, zb)]
        ck.prism(finish, f"{prefix}_slat{k}", mat, sec, "y", -vw / 2 + 0.01, vw / 2 - 0.01, collide=False)


def build_hip():
    """Named `hip` for its photo, `blue_hip_roof_cottage.png`, but read
    again (2 Oct 2026) its main roof is a low side gable: the ridge runs
    along the street, the eaves along the front and back, each side wall
    rising into a low triangle with a louvred vent near the peak, and the
    little entry gable over the stoop. Cartoony (2026-10-04), its ideas
    pushed: the little front gable steep (40 degrees, its 20), sitting on
    the main eave as the photo's does, the eave running on under it, a fat
    round plaque in a blue ring on its face over a fat base band; the
    louvred vents fat, their blades wedges; the white-railed stoop as the
    Victorians' (fat newels with caps and knobs, square balusters at 0.30
    under fat sagging rails) and a little wider, so its rails pass beside
    the door's casing; the main roof the standard's, plain (at 20 degrees
    a kick of 10 is a crease, not a flare), its rakes on fat white barges;
    the flue fat and capped."""
    V = HIP
    m = mats(walls="cottage_kit_walls_sky", trim="cottage_kit_trim_blue")
    white = material("cottage_kit_trim")       # the photo's rails, barges and plaque are white against the dark blue trim
    blue_shade = shade("cottage_kit_trim_blue")
    trim_seed, shingle_seed = SEEDS["hip"]
    rng = random.Random(trim_seed)
    floor, eave, pitch = V["floor"], V["eave"], V["pitch"]
    tan = math.tan(math.radians(pitch))
    head = floor + CC_HEAD
    sill = head - V["window"]
    door_x = (0.9, 1.9)
    xr = sum(door_x) / 2
    openings = {
        "front": [(door_x[0], door_x[1], floor + THRESHOLD, head), (-2.4, -0.8, sill, head)],
        "back": [(-2.2, -1.0, sill, head), (1.0, 2.2, sill, head)],
        "west": [(-2.6, -1.6, sill, head), (-0.4, 0.6, sill, head), (1.6, 2.6, sill, head)],
        "east": [(-2.6, -1.6, sill, head), (0.8, 2.0, sill, head)],
    }
    # -- the body: eave walls front and back, gables at the sides
    top_in = wall_top_in(pitch)
    flat = Top(row=eave, flat=eave + top_in)
    gable_side = Top(row=eave, gable=(HD - E_IN, HD, eave), pitch=pitch)
    shell("", -HW, HW, -HD, HD, -BELOW, {"front": flat, "back": flat, "west": gable_side, "east": gable_side}, openings,
          m["walls"], floor, base_mat=m["base"])
    cartoon_corners(rng, m["trim"], -HW, HW, -HD, HD, -BELOW - 0.03, eave + top_in + 0.02)
    cartoon_openings(rng, "", openings, (-HW, HW, -HD, HD), m, doors={("front", 0)})

    # -- the main roof, plain, its ridge along X: built in the quarter-turned
    # frame (local x = -y), where its slopes fall along local X as the kit's
    # do; its rakes at the sides on fat white barges
    turned = ck.quarter_turn(finish)
    roof = ck.plain_roof(turned, m["roof"], 0.0, HD, eave, math.radians(pitch), CC_SLAB, -HW - CC_OVER, HW + CC_OVER,
                         sag=CC_SAG, eave_over=CC_OVER)
    plain_barges(rng, m, roof, mat=white, fin=turned, names=("west", "east"))
    # the louvred vents near each peak, under the rakes
    vw, vh, vd = V["vent"]
    for side, out, tag in ((-HW, -1, "w"), (HW, 1, "e")):
        louvred_vent(rng, f"vent_{tag}", blue_shade, side, out, vw, vh, eave + HD * tan - vd)

    # -- the little gable over the stoop, sitting on the main eave as the
    # photo's does: its face just proud of the main roof's fascia, its foot on
    # the fascia's top, its own steep roof running back into the main slope
    # until the main roof's top has risen over its ridge (the end buried in
    # the slab and the attic), its rake on a white barge
    hl, hp, ht, ho, hr, hproud = V["gable"]
    tl = math.tan(math.radians(hp))
    edge_y = -HD - CC_OVER                                 # the main roof's fascia
    sag = ck.sag_at(roof.stations, xr)
    z_le = roof.rt - roof.r_out * tan - sag                # the fascia's top, at the gable
    face = edge_y - hproud
    little_top = z_le + hl * tl + ht / math.cos(math.radians(hp)) + 0.08
    y_back = -(roof.rt - CC_SAG - little_top - 0.08) / tan
    little = ck.plain_roof(finish, m["roof"], xr, hl, z_le, math.radians(hp), ht, face - hr, y_back, sag=0.0, eave_over=ho,
                           ridge=0.16, part="gable_roof", ridge_part="gable_ridge_cap")
    ck.barge(finish, rng, "gable_barge", [white, white], little.profile, [], little.r_out + 0.04, xr, little.y0, -1, 0.19, 0.07, ())

    def U(x):                                              # 3 cm up in the little roof's underside
        return z_le + (hl - abs(x - xr)) * tl + 0.03
    xa, xb = xr - hl + 0.02, xr + hl - 0.02
    # the gable's face, its foot 5 cm down over the fascia and its back 3 cm into the main slab
    ck.prism(finish, "gable_face", m["walls"], [(xa, z_le - 0.05), (xb, z_le - 0.05), (xb, U(xb)), (xr, U(xr)), (xa, U(xa))],
             "y", face, edge_y + 0.03, collide=False)
    # a fat base band across its foot, in the blue's shade under the little rake
    box("gable_band", blue_shade, xr - hl - 0.04, xr + hl + 0.04, face - 0.04, face + 0.02, z_le - 0.07, z_le + 0.12, collide=False)
    # the round plaque, pushed: a white disc in a fat blue ring
    ck.round_window(finish, rng, "gable_plaque", [m["trim"], white], "x", xr, z_le + 0.40, 0.16, face, -1, frame=0.09,
                    proud=0.05, sunk=0.03)

    # -- the stoop: a landing up three chunky risers at the four's grade,
    # white-railed as the photo's: the stair's railings (cartoon_kit's) on
    # the landing's side rails' lines, beside the door's casing, and the side
    # rails from the stair's top newels back to the wall
    sw, sd = V["stoop"]
    sx0, sx1, sy0 = xr - sw / 2, xr + sw / 2, -HD - sd
    box("landing", m["concrete"], sx0, sx1, sy0, -HD + 0.02, -0.10, floor)
    rails = (("w", sx0 + 0.03 + ck.NEWEL / 2), ("e", sx1 - 0.03 - ck.NEWEL / 2))
    n, riser, going = ck.flight(finish, "stair", m["concrete"], rails[0][1] + 0.03, rails[1][1] - 0.03, sy0, -1, floor,
                                V["risers"], V["grade"], BELOW)
    ck.stair_rails(finish, rng, "stair_rail", white, rails, sy0, -1, floor, n, riser, going)
    ny = sy0 + 0.03 + ck.NEWEL / 2
    for tag, x in rails:
        ck.straight_rail(finish, rng, f"landing_rail_{tag}", white, "y", x, ny + 0.055, -HD + 0.08, ny + ck.NEWEL / 2, -HD, floor)
    # the flue on the back slope, fat and capped, in the roof's colour with a blue cap
    fw, fx, fy, fh = V["flue"]
    z_surf = roof.rt - fy * tan - ck.sag_at(roof.stations, fx)
    ck.brick_chimney(finish, rng, "", [own_material("hip", "flue", "cottage_kit_roof"), m["trim"]], fx, fy, fw / 2, fw / 2,
                     z_surf - 0.8, z_surf + fh - 0.32, z_surf + fh)

    # -- the main roof's raised shingle clusters and vents, from its own seed
    # (in the turned frame: r is -y on the front slope, y is x), clear of the
    # flue and of the little gable, the eave's cluster too
    gab = (abs(y_back) - 0.2, -little.y0 + 0.2, xr - hl - ho - 0.2, xr + hl + ho + 0.2)
    flue = (fy - fw / 2 - 0.25, fy + fw / 2 + 0.25, fx - fw / 2 - 0.25, fx + fw / 2 + 0.25)
    tabs, vents = roof_dressing(random.Random(shingle_seed), m, roof, avoid={1: [gab], -1: [flue]}, kick_avoid={1: [gab]},
                                vents=((-1, 2),), fin=turned)
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=CC_OVER, rake_over=CC_OVER, kick=0.0, tabs=tabs, vents=vents,
                door_clear=head - floor - THRESHOLD,
                extra=f"; little gable {hp:.0f} deg on the fascia at {z_le:.2f}, back to y {y_back:.2f}; {n} risers of {riser:.3f} on {going:.3f}")


# --- hip_garage: the hip cottage's detached one-car garage -------------------

def garage_door(rng, m, mat, a0, a1, z0, z1, face, sections=4):
    """A chunky panelled garage door in the opening (a0..a1, z0..z1) of the
    gable wall at y = face (facing -Y): the leaf recessed 10 cm, and over it,
    3 cm proud of the leaf, one fat frame of stiles and rails round two
    panels in each of `sections` sections, the panels the leaf showing
    through, as a sectional door's; its rails a centimetre uneven."""
    pane("door0_door", mat, "x", face, -1, a0, a1, z0, z1, recess=0.10, collide=True)
    st, rl = 0.12, 0.10                         # the stiles across, the rails deep
    x0, x1, xm = a0 + 0.01, a1 - 0.01, (a0 + a1) / 2
    zs = [z0 - 0.01 + (z1 - z0 + 0.02) * k / sections for k in range(sections + 1)]
    zs = [zs[0]] + [z + ck.jit(rng, 0.01) for z in zs[1:-1]] + [zs[-1]]
    bands = [(zs[0], zs[0] + rl)] + [(z - rl / 2, z + rl / 2) for z in zs[1:-1]] + [(zs[-1] - rl, zs[-1])]
    inner = [z for zb, zt in bands for z in (zb, zt)]
    ls = [(x0, inner[0])] + [(x0 + st, z) for z in inner] + [(x0, inner[-1])]
    polys = [([(x0, inner[0]), (x0 + st, inner[0])] + [(x0 + st, z) for z in inner[1:-1]] + [(x0 + st, inner[-1]), (x0, inner[-1])], 0),
             ([(x1 - st, inner[0]), (x1, inner[0]), (x1, inner[-1]), (x1 - st, inner[-1])] + [(x1 - st, z) for z in reversed(inner[1:-1])], 0),
             ([(xm - st / 2, z) for z in inner] + [(xm + st / 2, z) for z in reversed(inner)], 0)]
    del ls
    for zb, zt in bands:
        # each rail in two pieces between the stiles, welded to them on their shared points
        polys.append(([(x0 + st, zb), (xm - st / 2, zb), (xm - st / 2, zt), (x0 + st, zt)], 0))
        polys.append(([(xm + st / 2, zb), (x1 - st, zb), (x1 - st, zt), (xm + st / 2, zt)], 0))
    ck.plate(finish, "door0_panels", [mat], polys, "y", face - 0.07, face - 0.04, collide=False)


def build_hip_garage():
    """The hip cottage's detached one-car garage, gable to the drive, painted
    to match: cartoony (2026-10-04), its ideas pushed: a chunky sectional
    garage door (a fat frame of stiles and rails round eight panels over the
    leaf) in a fat casing, 0.20 across with a deeper head; the roof the
    standard's as the hip's (plain at 20 degrees, a 0.30 slab, 0.75 eaves and
    rakes, fat white barges), a cluster at a rake and one on the eave of
    each slope and no vent pipe (a garage has no plumbing)."""
    V = HIP_GARAGE
    m = mats(walls="cottage_kit_walls_sky", trim="cottage_kit_trim_blue")
    white = material("cottage_kit_trim")       # the photo's door, its trim and barges are white
    trim_seed, shingle_seed = SEEDS["hip_garage"]
    rng = random.Random(trim_seed)
    gw, gd = V["w"], V["d"]
    eave, pitch = V["eave"], V["pitch"]
    hw, hd = gw / 2, gd / 2
    rect = (-hw, hw, -hd, hd)
    dw, dh = V["door"]
    openings = {
        "front": [(-dw / 2, dw / 2, THRESHOLD, THRESHOLD + dh)],
        "west": [(-0.6, 0.6, 1.25, 2.0)],
        "back": [(-0.5, 0.5, THRESHOLD, CC_HEAD)],
    }
    top_in = wall_top_in(pitch)
    gable = Top(row=eave, gable=(hw - E_IN, hw, eave), pitch=pitch)
    flat = Top(row=eave, flat=eave + top_in)
    shell("", -hw, hw, -hd, hd, -BELOW, {"front": gable, "back": gable, "west": flat, "east": flat}, openings, m["walls"], 0.0,
          base_mat=m["base"])
    cartoon_corners(rng, m["trim"], -hw, hw, -hd, hd, -BELOW - 0.03, eave + top_in + 0.02)
    # the garage door's fat white casing, 0.20 across with a deeper head, and the door itself
    a0, a1, z0, z1 = openings["front"][0]
    ck.casing(finish, rng, "front0_casing", white, "x", -hd, -1, a0, a1, z0, z1, sill=False, width=0.20, head=0.24)
    garage_door(rng, m, white, a0, a1, z0, z1, -hd)
    # the side window and the back door, the standard's casings
    cartoon_openings(rng, "", {"west": openings["west"], "back": openings["back"]}, rect, dict(m, door=white),
                     doors={("back", 0)})
    roof = ck.plain_roof(finish, m["roof"], 0.0, hw, eave, math.radians(pitch), CC_SLAB, -hd - CC_OVER, hd + CC_OVER,
                         sag=0.03, eave_over=CC_OVER)
    plain_barges(rng, m, roof, mat=white)
    tabs, vents = roof_dressing(random.Random(shingle_seed), m, roof, scattered=0, vents=())
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=CC_OVER, rake_over=CC_OVER, kick=0.0, tabs=tabs, vents=vents,
                door_clear=dh, extra=f"; the garage door {dw:.1f} x {dh:.2f} m")


# --- glass_gable: the front gable glazed into the peak -----------------------

def build_glass_gable():
    """The glass-gable cottage, cartoony (2026-10-04), its ideas pushed: the
    front gable glazed up into the peak behind a fat white frame (a sill
    board either side of the door, a transom on the door's head line right
    across, two fat mullions up into a fat rake band under the roof), the
    door in its own fat casing; deep eaves and rakes (0.90) on fat white
    rafter tails, nine a side, their ends 10 cm out past the eave's edge so
    they show from the street, and a big knee brace at each front gable
    corner; fat white barges. The roof is plain (a 0.30 slab at 35
    degrees): a bell-cast kick would bend the eave away from its rafter
    tails. (The old sill board ran across the door at 0.9 m; it stops at the
    door's casing now.)"""
    V = GLASS
    m = mats(walls="cottage_kit_walls_sky", door="cottage_kit_door_cobalt")
    trim_seed, shingle_seed = SEEDS["glass_gable"]
    rng = random.Random(trim_seed)
    floor, sill, eave, pitch = V["floor"], V["sill"], V["eave"], V["pitch"]
    head = floor + CC_HEAD
    wh = V["window_head"]                    # the windows' head, lower than the door's, so their casings clear the rafter tails
    tan = math.tan(math.radians(pitch))
    door_x = (1.5, 2.5)
    side_sill = 1.10
    openings = {
        "back": [(-2.0, -1.0, sill, wh), (1.0, 2.0, sill, wh)],
        "west": [(-2.2, -1.0, side_sill, wh), (0.8, 2.0, side_sill, wh)],
        "east": [(-2.8, -1.6, side_sill, wh), (0.8, 2.0, side_sill, wh)],
    }
    # -- the body without its front wall; the side walls stop at the front
    # corners as if it were there
    top_in = wall_top_in(pitch)
    gable = Top(row=eave, gable=(HW - E_IN, HW, eave), pitch=pitch)
    flat = Top(row=eave, flat=eave + top_in)
    shell("", -HW, HW, -HD, HD, -BELOW, {"back": gable, "west": flat, "east": flat}, openings, m["walls"], floor,
          which=("back", "west", "east"), lap=-E_IN, base_mat=m["base"])
    cartoon_corners(rng, m["trim"], -HW, HW, -HD, HD, -BELOW - 0.03, eave + top_in + 0.02)
    cartoon_openings(rng, "", openings, (-HW, HW, -HD, HD), m)
    roof = ck.plain_roof(finish, m["roof"], 0.0, HW, eave, math.radians(pitch), CC_SLAB, -HD - V["over"], HD + V["over"],
                         sag=CC_SAG, eave_over=V["over"])
    plain_barges(rng, m, roof)

    def under(x):                            # the roof's underside over the front's plane
        return eave + (HW - abs(x)) * tan - ck.sag_at(roof.stations, -HD)

    # -- the front: a sill band either side of the door, its ends the door's
    # reveals; one glass slab the shape of the gable from the band up into
    # the roof; the door leaf in its slot, in its own fat casing
    band = Top(row=sill - 0.10, flat=sill)
    wall("band_w", (-HW + E_IN, -HD, 0.0), (1, 0, 0), (0, 1, 0), door_x[0] + HW - E_IN, -BELOW, band, [], floor,
         [m["walls"], m["base"]])
    wall("band_e", (door_x[1], -HD, 0.0), (1, 0, 0), (0, 1, 0), HW - E_IN - door_x[1], -BELOW, band, [], floor,
         [m["walls"], m["base"]])
    xg = HW - E_IN - 0.01
    glass = [(-xg, sill - 0.02), (xg, sill - 0.02), (xg, under(xg) + 0.03), (0.0, under(0.0) + 0.03), (-xg, under(-xg) + 0.03)]
    finish("glass_gable", prism_bm(glass, "y", -HD + 0.08, -HD + 0.13), [m["glass"]])
    # (the leaf 2.5 cm in and 3.5 thick, clear of the casing's back at 7 and the glass at 8)
    pane("door", m["door"], "x", -HD, -1, door_x[0], door_x[1], THRESHOLD, head, recess=0.025, thick=0.035)
    ck.casing(finish, rng, "door_casing", m["trim"], "x", -HD, -1, door_x[0], door_x[1], THRESHOLD, head, sill=False)
    # the fat white frame over the glass, each member at its own depth: the
    # sill boards either side of the door's casing (5 cm proud), the transom
    # across on the door's head line (4.5), the rake band under the roof
    # (5.5, its top 3 cm up in the underside), the mullions up into it (3.5)
    ca = door_x[0] - 0.02 - ck.CASING + 0.03     # 3 cm into the door casing's jambs
    cb = door_x[1] + 0.02 + ck.CASING - 0.03
    # (their ends 2 cm into the corner boards, past the sill band's ends; the transom a centimetre over the door's leaf)
    box("sill_board_w", m["trim"], -xg - 0.02, ca, -HD - 0.05, -HD + 0.01, sill - 0.10, sill + 0.06, collide=False)
    box("sill_board_e", m["trim"], cb, xg + 0.02, -HD - 0.05, -HD + 0.01, sill - 0.10, sill + 0.06, collide=False)
    box("transom", m["trim"], -xg - 0.02, xg + 0.02, -HD - 0.045, -HD + 0.075, head + 0.03, head + 0.17, collide=False)
    rb = V["rake_band"]
    ck.plate(finish, "rake_band", [m["trim"]], [([(-xg, under(-xg) + 0.03 - rb), (0.0, under(0.0) + 0.03 - rb),
                                                  (0.0, under(0.0) + 0.03), (-xg, under(-xg) + 0.03)], 0),
                                                ([(0.0, under(0.0) + 0.03 - rb), (xg, under(xg) + 0.03 - rb),
                                                  (xg, under(xg) + 0.03), (0.0, under(0.0) + 0.03)], 0)],
             "y", -HD - 0.055, -HD + 0.07, collide=False)
    mw = V["mullion"]
    for k, x in enumerate(V["mullions"]):
        poly = [(x - mw / 2, sill + 0.04), (x + mw / 2, sill + 0.04), (x + mw / 2, under(x + mw / 2) - rb + 0.06),
                (x - mw / 2, under(x - mw / 2) - rb + 0.06)]
        finish(f"mullion_{k}", prism_bm(poly, "y", -HD - 0.035, -HD + 0.072), [m["trim"]], collide=False)

    # -- the deep eaves on fat white rafter tails, and a big knee brace at each front gable corner
    n = V["tails"]
    ys = [-HD + 0.45 + (D - 0.90) * k / (n - 1) for k in range(n)]
    for tag, s in (("w", -1), ("e", 1)):
        ck.rafter_tails(finish, rng, f"tails_{tag}", m["trim"], roof, s, ys, short=-V["tail_past"])
        ck.knee_brace(finish, rng, f"front_brace_{tag}", m["trim"], s * HW, s, -HD, -1, under, *V["brace"])

    tabs, vents = roof_dressing(random.Random(shingle_seed), m, roof, vents=((-1, 1), (1, 1)))
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=V["over"], rake_over=V["over"], kick=0.0, tabs=tabs,
                vents=vents, door_clear=head - floor - THRESHOLD, extra=f"; {n} rafter tails a side")


# --- porch: the pink cottage with the full-width porch and the hammock -------

def build_porch():
    """The pink hammock cottage, cartoony (2026-10-04), its ideas pushed:
    the round window in the gable big and fat-framed with a muntin cross;
    the full-width porch on two fat orange timber posts at its corners, as
    the photo's (the old build's two middle posts would stand in the
    hammock's way), under a fat beam in the orange's shade and its own low
    metal shed roof with a fat orange fascia; the hammock chunky and
    sagging deep, slung post to post across the front on fat cords and
    spreader bars; fat shutters with louvred panels in the mint's shade
    beside the front windows; fat mint barges. The roof is metal and plain
    (a 0.30 slab at 32 degrees, 0.75 eaves and rakes): a bell-cast kick or
    raised shingles belong to a shingled roof, so it has neither, only its
    vent pipes."""
    V = PORCH
    m = mats(walls="cottage_kit_walls_pink", trim="cottage_kit_trim_mint", roof="cottage_kit_roof_metal")
    orange, fabric = material("cottage_kit_trim_orange"), material("cottage_kit_fabric")
    orange_shade, mint_shade = shade("cottage_kit_trim_orange"), shade("cottage_kit_trim_mint")
    trim_seed, shingle_seed = SEEDS["porch"]
    rng = random.Random(trim_seed)
    floor, eave, pitch, pd = V["floor"], V["eave"], V["pitch"], V["porch_d"]
    head = floor + CC_HEAD
    sill = head - 1.40
    openings = {
        "front": [(-0.5, 0.5, floor + THRESHOLD, head), (-2.2, -1.2, sill, head), (1.2, 2.2, sill, head)],
        "back": [(-2.0, -1.0, sill, head), (1.0, 2.0, sill, head)],
        "west": [(-2.4, -1.4, sill, head), (0.6, 1.6, sill, head)],
        "east": [(-2.4, -1.4, sill, head), (0.6, 1.6, sill, head)],
    }
    # -- the body, gables front and back
    top_in = wall_top_in(pitch)
    gable = Top(row=eave, gable=(HW - E_IN, HW, eave), pitch=pitch)
    flat = Top(row=eave, flat=eave + top_in)
    shell("", -HW, HW, -HD, HD, -BELOW, {"front": gable, "back": gable, "west": flat, "east": flat}, openings, m["walls"], floor,
          base_mat=m["base"])
    cartoon_corners(rng, m["trim"], -HW, HW, -HD, HD, -BELOW - 0.03, eave + top_in + 0.02)
    cartoon_openings(rng, "", openings, (-HW, HW, -HD, HD), m, doors={("front", 0)})
    # fat shutters either side of the front windows, lapped 2 cm into the casings, their louvres in the mint's shade
    sw = V["shutter"]
    for k, (a0, a1, z0, z1) in enumerate(openings["front"][1:]):
        for tag, x in (("a", a0 + 0.02 - ck.CASING + 0.02 - sw), ("b", a1 - 0.02 + ck.CASING - 0.02)):
            ck.shutter(finish, rng, f"shutter_{k}{tag}", [m["trim"], mint_shade], "x", -HD, -1, x, x + sw, z0 - 0.04, z1 + 0.04)
    # the round window in the gable, big, in a fat mint ring with a muntin cross
    wr, wz = V["window"]
    ck.round_window(finish, rng, "round", [m["trim"], m["glass"]], "x", 0.0, wz, wr, -HD, -1, frame=0.13, cross=0.07)

    # -- the roof, metal and plain, fat mint barges, vent pipes on the back half
    roof = ck.plain_roof(finish, m["roof"], 0.0, HW, eave, math.radians(pitch), CC_SLAB, -HD - CC_OVER, HD + CC_OVER,
                         sag=CC_SAG, eave_over=CC_OVER)
    plain_barges(rng, m, roof)

    # -- the porch: a deck the body's width, two fat timber posts at its front
    # corners, a fat beam on them, a low metal shed roof from the wall over
    # the beam to a fat orange fascia, its ends clear under the main rakes;
    # the steps at the door
    px0, px1, py0 = -HW - 0.06, HW + 0.06, -HD - pd - 0.06
    box("deck", m["porch"], px0, px1, py0, -HD + 0.02, -0.10, floor)
    z_wall, slope, sh = V["shed"]                  # its underside at the wall (over the casings' heads), fall per metre, slab
    post_y, posts_x = py0 + V["post_in"], V["posts_x"]

    def under(y):                                  # the shed's underside
        return z_wall - (-HD - y) * slope
    bd = V["beam"]
    beam1 = under(post_y) + 0.04                   # the beam 4 cm up in the shed's underside
    beam0 = beam1 - bd
    xe = HW + V["shed_end"]
    y_edge = post_y - 0.13 - V["shed_over"]
    slab("porch_roof", m["roof"], ((-xe, y_edge, under(y_edge) + sh), (xe, y_edge, under(y_edge) + sh),
                                   (xe, -HD + 0.02, under(-HD + 0.02) + sh), (-xe, -HD + 0.02, under(-HD + 0.02) + sh)), sh)
    box("porch_beam", orange_shade, -posts_x[1] - 0.22, posts_x[1] + 0.22, post_y - 0.13, post_y + 0.13, beam0, beam1, collide=False)
    zf = under(y_edge) + sh - 0.02
    box("porch_fascia", orange, -xe - 0.02, xe + 0.02, y_edge - 0.05, y_edge + 0.02, zf - V["fascia"], zf, collide=False)
    for k, x in enumerate(posts_x):
        ck.timber_post(finish, rng, f"post_{k}", orange, x, post_y, floor - 0.02, (floor + 0.14, floor + 0.20), beam0, beam0 + 0.04,
                       size=0.30, block=0.20, collar=0.18)
    ck.flight(finish, "stair", m["porch"], -0.70, 0.70, py0, -1, floor, V["risers"], V["grade"], BELOW)
    # the hammock, chunky and sagging, slung across the front from hooks on
    # the posts' inner faces, its line at their backs so the bed lies over the deck
    hz, hsag, hw_, hg = V["hammock"]
    ck.hammock(finish, rng, "hammock", [fabric, orange_shade], posts_x[0] + 0.15, posts_x[1] - 0.15, post_y + 0.15, floor + hz, hsag,
               width=hw_, gather=hg)

    tabs, vents = 0, ck.roof_vents(finish, random.Random(shingle_seed), [m["vent"], m["glass"]], roof,
                                   {s: roof.slope(s) for s in (1, -1)}, counts=((-1, 1), (1, 1)))
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=CC_OVER, rake_over=CC_OVER, kick=0.0, tabs=tabs, vents=vents,
                door_clear=head - floor - THRESHOLD,
                extra=f"; porch beam {beam0 - floor:.2f} m clear over the deck, shed {math.degrees(math.atan(slope)):.1f} deg")


# --- log: two front gables and the fieldstone chimney ------------------------

def gable_truss(rng, part, mat, xc, half, eave, pitch_deg, y_lo, y_hi, tie, king, strut):
    """The log cabin's gable truss, pushed and set across the rake under the
    bargeboard, where the deep rake no longer hides it (as the classic's
    sunburst and the Victorian's): one plate of convex pieces welded on their
    shared points, a fat tie beam across the gable `tie` (bottom, top) over
    the eave, its ends 3 cm up in the slab's underside; a fat king post
    `king` across from it up to 3 cm into the underside at the peak; and two
    fat struts `strut` across from near the tie's ends up to the king
    post's sides, each a centimetre different, as hewn by hand."""
    tan = math.tan(math.radians(pitch_deg))

    def U(x):                                # 3 cm up in the underside
        return eave + (half - abs(x - xc)) * tan + 0.03

    def X(z):                                # where U is z
        return half - (z - 0.03 - eave) / tan
    zb, zt = eave + tie[0], eave + tie[1]
    k = king / 2
    z_peak = U(xc)
    s1 = X(zt) - 0.10 + ck.jit(rng, 0.02)    # the struts' outer feet, just in from the tie's ends
    s0 = s1 - strut * 1.4
    a = zt + (z_peak - zt) * 0.52 + ck.jit(rng, 0.02)
    b = a + strut * 1.4
    polys = [([(xc - X(zb), zb), (xc + X(zb), zb), (xc + X(zt), zt), (xc + s1, zt), (xc + s0, zt), (xc + k, zt), (xc - k, zt),
               (xc - s0, zt), (xc - s1, zt), (xc - X(zt), zt)], 0),
             ([(xc - k, zt), (xc + k, zt), (xc + k, a), (xc + k, b), (xc + k, U(xc + k)), (xc, z_peak), (xc - k, U(xc - k)),
               (xc - k, b), (xc - k, a)], 0),
             ([(xc + s0, zt), (xc + s1, zt), (xc + k, a), (xc + k, b)], 0),
             ([(xc - s1, zt), (xc - s0, zt), (xc - k, b), (xc - k, a)], 0)]
    return ck.plate(finish, part, [mat], polys, "y", y_lo, y_hi, collide=False)


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
    each one's eave there running on under the other, inside the attic.

    Cartoony (2026-10-04), its ideas pushed: fat round log ends at the five
    outside corners, a log every 0.34 m (the logs between stay paint), each
    end chamfered and a few centimetres different; the tall fieldstone
    chimney taller, with a broad foot, a sloped shoulder, a fat cap and a few
    patches of stones standing out of it, as the roofs' shingles lift; the
    side gable's truss fat and set across its rake. The roofs are the
    standard's, shake with a bell-cast kick (the storybook cabin wants the
    flare): 0.30 slabs at 28 degrees, kicks of 14 to 0.75 m eaves and rakes,
    fat grey barges, each stopping where it runs into the other roof."""
    V = LOG
    m = mats(walls="cottage_kit_walls_log", trim="cottage_kit_trim_grey", roof="cottage_kit_roof_shake")
    stone, batten = material("cottage_kit_stone"), material("cottage_kit_walls_batten")
    trim_seed, shingle_seed = SEEDS["log"]
    rng = random.Random(trim_seed)
    floor, eave, pitch = V["floor"], V["eave"], V["pitch"]
    head = floor + CC_HEAD
    sill = head - 1.15
    mx0, mx1 = V["main"]
    wx0, wx1, reach = V["wing"]
    cx0, cx1, cdeep, cover = V["chimney"]
    tn = math.tan(math.radians(pitch))
    m_half, m_ridge = (mx1 - mx0) / 2, (mx0 + mx1) / 2
    w_half, w_ridge = (wx1 - wx0) / 2, (wx0 + wx1) / 2
    w_eave = eave - 0.04
    yf = -HD - reach                                   # the wing's front
    wall_mats = [m["walls"], m["base"]]
    door_x = V["door_x"]
    e = E_IN
    top_in = wall_top_in(pitch)
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
         Top(row=w_eave, flat=w_eave + top_in - 0.01), lambda y: HD - e - y, ("y", wx0, -1), west),
        # the east side
        ("wall_east", (mx1, -HD + e, 0.0), (0, 1, 0), (-1, 0, 0), D - 2 * e, -BELOW - 0.01,
         Top(row=eave, flat=eave + top_in - 0.01), lambda y: y + HD - e, ("y", mx1, 1), east),
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
            ck.casing(finish, rng, f"{name}{k}_casing", m["trim"], axis, at, out, a0, a1, z0, z1, sill=not is_door)
            pane(f"{name}{k}_{'door' if is_door else 'pane'}", m["door"] if is_door else m["glass"], axis, at, out,
                 a0, a1, z0, z1, recess=CC_PANE_RECESS)

    # -- the logs on the wall faces, the cabin's own idea (her "the log cabin
    # walls need some work", 2026-10-05: painted on flat walls they read as
    # siding): round logs in the corners' rhythm, 5 cm proud with chinking
    # creases between, up to each block's eave, broken round the casings and
    # behind the chimney; on a generator of their own, so they move nothing
    # after them
    log_rng = random.Random(trim_seed + 101)
    c_hy = cdeep / 2 + 0.015
    c_cy = -HD + 0.03 - c_hy
    c_foot = V["chimney_foot"] + 0.02
    behind = {"wall_front": [(cx0 - c_foot, cx1 + c_foot, -1.0, 99.0)],
              "wing_wall_east": [(c_cy - c_hy - c_foot, c_cy + c_hy + c_foot, -1.0, 99.0)]}
    for name, origin, u_dir, v_dir, length, foot, top, to_u, (axis, at, out), ops in walls:
        ia = 0 if axis == "x" else 1
        ends = sorted((origin[ia], origin[ia] + u_dir[ia] * length))
        gaps = [(a0 - ck.CASING, a1 + ck.CASING, z0 - (0.03 if is_door else ck.CASING), z1 + ck.CASING_HEAD)
                for a0, a1, z0, z1, is_door in ops] + behind.get(name, [])
        # the top course too, up under the eave and the gable's boards (logs
        # stopping a course short left a flat strip under them), its top
        # into the roof's slab or behind the boards
        z_hi = eave if name in ("wall_front", "wall_east", "wall_back") else w_eave
        ck.log_courses(finish, log_rng, f"{name}_logs", m["walls"], axis, at, out, ends[0], ends[1], 0.0, z_hi + 0.15,
                       gaps=gaps, r=V["log_r"], course=V["course"])

    # -- the two roofs, bell-cast, the side block's back rake 3.5 cm short of
    # the main's so its end shares no face with the main's barge; fat grey barges, each
    # roof's stopping on the junction side where it runs into the other
    main = ck.bell_roof(finish, m["roof"], m_ridge, m_half, eave, math.radians(pitch), CC_SLAB, -HD - CC_OVER, HD + CC_OVER,
                        sag=CC_SAG, kick_deg=pitch / 2, eave_over=CC_OVER, **CC_KICK)
    side = ck.bell_roof(finish, m["roof"], w_ridge, w_half, w_eave, math.radians(pitch), CC_SLAB, yf - CC_OVER,
                        HD + CC_OVER - 0.035, sag=CC_SAG, kick_deg=pitch / 2, eave_over=CC_OVER, part="side_roof",
                        ridge_part="side_ridge_cap", **CC_KICK)
    junction = m_half + 0.05                         # the main's west side stops just past the junction wall, under the side roof
    for face, y_rake, out in (("front", main.y0, -1), ("back", main.y1, 1)):
        ck.barge(finish, rng, f"barge_{face}", [m["trim"], m["trim"]], main.profile, [main.r_k], main.r_out + 0.05, m_ridge, y_rake,
                 out, CC_BARGE[0], CC_BARGE[1], (), r_ends={-1: junction})
    ck.barge(finish, rng, "side_barge_front", [m["trim"], m["trim"]], side.profile, [side.r_k], side.r_out + 0.05, w_ridge, side.y0,
             -1, CC_BARGE[0], CC_BARGE[1], ())
    ck.barge(finish, rng, "side_barge_back", [m["trim"], m["trim"]], side.profile, [side.r_k], side.r_out + 0.05, w_ridge, side.y1,
             1, CC_BARGE[0], CC_BARGE[1], (), r_ends={1: w_half + 0.05})
    # the side gable: its board-and-batten panel on the wall, 5 cm inside the
    # slab (the wall's own top is 3) and a centimetre short of the wall's
    # ends, and its fat truss across the rake under the barge
    peak = w_eave + w_half * tn
    pe = e + 0.01
    panel = [(wx0 + pe, w_eave - 0.05), (wx1 - pe, w_eave - 0.05), (wx1 - pe, w_eave + pe * tn + 0.05),
             (w_ridge, peak + 0.05), (wx0 + pe, w_eave + pe * tn + 0.05)]
    finish("wing_gable_panel", prism_bm(panel, "y", yf - 0.010, yf + 0.02), [batten], collide=False)
    # the other three gables the same board-and-batten over the logs' wall
    # (her "the log cabin walls need some work", 2026-10-05: the main front
    # gable was the log wall painted on, over modelled logs), as the photo's
    # main gable is boards
    m_peak = eave + m_half * tn
    # (each 1.3 cm further in on the junction side, where the other block's
    # roof runs past: flush there, its end shared a plane with that slab)
    for gname, xa, xb, ia, ib, ridge_x, eave_z, peak_z, ylo, yhi in (
            ("gable_panel_front", mx0, mx1, pe + 0.013, pe, m_ridge, eave, m_peak, -HD - 0.010, -HD + 0.02),
            ("gable_panel_back", mx0, mx1, pe + 0.013, pe, m_ridge, eave, m_peak, HD - 0.02, HD + 0.010),
            ("wing_gable_panel_back", wx0, wx1, pe, pe + 0.013, w_ridge, w_eave, peak, HD - 0.01, HD + 0.020)):
        g = [(xa + ia, eave_z - 0.05), (xb - ib, eave_z - 0.05), (xb - ib, eave_z + ib * tn + 0.05),
             (ridge_x, peak_z + 0.05), (xa + ia, eave_z + ia * tn + 0.05)]
        finish(gname, prism_bm(g, "y", ylo, yhi), [batten], collide=False)
    gable_truss(rng, "wing_truss", m["trim"], w_ridge, w_half, w_eave, pitch, side.y0 + 0.03, side.y0 + 0.12, *V["truss"])

    # -- the tall fieldstone chimney on the front at the junction: a broad
    # foot, its west face 5 cm into the wing's east wall, a sloped shoulder,
    # the shaft up through the main roof's rake and the side roof's eave, a
    # fat cap; a few patches of stones standing out of it, under the eaves
    # and over the roof
    hx, hy = (cx1 - cx0) / 2, cdeep / 2 + 0.015
    ccx, ccy = (cx0 + cx1) / 2, -HD + 0.03 - hy
    ridge_top = main.rt
    foot = V["chimney_foot"]
    ck.stone_stack(finish, rng, "", stone, ccx, ccy, hx, hy, -BELOW - 0.02, V["shoulder"][0], ridge_top + cover, foot=foot,
                   shoulder=V["shoulder"][1], clusters=4, faces=(("y", -1), ("x", 1)), z_stones=V["stones"])

    # -- fat log ends at the five outside corners (the junction is an inside corner)
    for cx, cy, sx, sy, tag, top in ((mx1, -HD, 1, -1, "se", eave), (wx0, HD, -1, 1, "nw", w_eave), (mx1, HD, 1, 1, "ne", eave),
                                     (wx0, yf, -1, -1, "wing_sw", w_eave), (wx1, yf, 1, -1, "wing_se", w_eave)):
        ck.log_ends(finish, rng, f"logs_{tag}", m["walls"], cx, cy, sx, sy, top - 0.05, r=V["log_r"], course=V["course"])
    # one step up to the door: the slab's edge is the step, clear of the chimney's foot
    box("landing", m["concrete"], door_x[0] - 0.10, door_x[1] + 0.10, -HD - 0.85, -HD + 0.02, -0.10, floor)
    ramp_step("stair", m["concrete"], door_x[0] - 0.10, door_x[1] + 0.10, -HD - 0.85, -1, floor, 0.5)

    # -- raised shake clusters on both roofs and vent pipes on the main's
    # back half, from the shingle seed, each roof's keeping off the valley
    # and off its eave buried under the other, the main's off the chimney
    srng = random.Random(shingle_seed)
    chim = (m_ridge - (cx1 + 0.3), m_ridge - (cx0 - 0.3), ccy - hy - 0.3, ccy + hy + 0.3)
    valley = (m_half - 0.4, 9.0, -9.0, 9.0)
    tabs, vents = roof_dressing(srng, m, main, avoid={-1: [chim, valley]}, kick_avoid={-1: [valley]}, vents=((-1, 1), (1, 1)))
    bm = bmesh.new()
    s_valley = (w_half - 0.4, 9.0, -HD - CC_OVER - 0.2, 9.0)
    t2, _ = ck.roof_clusters(srng, bm, side, avoid={1: [s_valley]}, scattered=1, kick_avoid={1: [s_valley]})
    finish("side_roof_shingles", bm, [m["roof"]], collide=False)
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=CC_OVER, rake_over=CC_OVER, kick=pitch / 2, tabs=tabs + t2,
                vents=vents, door_clear=head - floor - THRESHOLD,
                extra=f"; chimney top {ridge_top + cover:.2f}, logs every {V['course']:.2f} m, {V['log_r']:.2f} m round")


# --- l_ranch: the L-shaped ranch, 8 m wide --------------------------------------

def notched_gable(name, mat, xc, half, eave, pitch_deg, slab, stations, sections):
    """A plain gable roof along Y (its ridge over x = xc, its underside at
    `eave` `half` either side) whose eaves step in along its length, one
    closed piece with every face welded: `stations` y0 < y1 < ..., and for
    each interval between them a (west, east) pair of edge x's, the full
    eave or cut back just proud of a wall, where the roof runs on into
    another roof's gable end or a lean-to meets its wall; at a step the
    slab's end returns as a fascia. The slab is `slab` thick, its edges
    plumb, its faces planar (the points a step adds lie on their edges)."""
    tan = math.tan(math.radians(pitch_deg))
    vt = slab / math.cos(math.radians(pitch_deg))

    def under(x):
        return eave + (half - abs(x - xc)) * tan
    bm = bmesh.new()
    cache = {}

    def V(j, x, top):
        key = (j, round(x, 5), top)
        if key not in cache:
            cache[key] = bm.verts.new((x, stations[j], under(x) + (vt if top else 0.0)))
        return cache[key]
    n = len(sections)
    X = []                                   # the x's each station carries: every edge of the intervals either side
    for j in range(n + 1):
        xs = {xc}
        for k in (j - 1, j):
            if 0 <= k < n:
                xs.update(sections[k])
        X.append(sorted(xs))

    def span(j, lo, hi):
        return [x for x in X[j] if lo - 1e-9 <= x <= hi + 1e-9]
    for k, (xw, xe) in enumerate(sections):
        for top in (False, True):
            for lo, hi in ((xw, xc), (xc, xe)):
                bm.faces.new([V(k, x, top) for x in span(k, lo, hi)] + [V(k + 1, x, top) for x in reversed(span(k + 1, lo, hi))])
        for x in (xw, xe):                   # the plumb fascias
            bm.faces.new((V(k, x, False), V(k + 1, x, False), V(k + 1, x, True), V(k, x, True)))
    for j, k in ((0, 0), (n, n - 1)):        # the two ends
        xs = span(j, *sections[k])
        bm.faces.new([V(j, x, False) for x in xs] + [V(j, x, True) for x in reversed(xs)])
    for j in range(1, n):                    # the returns where an eave steps in
        (aw, ae), (bw, be) = sections[j - 1], sections[j]
        for lo, hi in (sorted((aw, bw)), sorted((ae, be))):
            if hi - lo > 1e-6:
                bm.faces.new((V(j, lo, False), V(j, hi, False), V(j, hi, True), V(j, lo, True)))
    return finish(name, bm, [mat])


def ramp_step(prefix, mat, x0, x1, y_edge, out, z_top, grade):
    """A single riser's step: the deck's or slab's own edge is the step, and
    the park's narrow colliding ramp (as cartoon_kit's flight lays it) runs
    from that edge down to the ground at the house's grade."""
    going = z_top / grade

    def y(s):
        return y_edge + out * s
    ramp = [(y(going + 0.05), -BELOW - 0.02), (y(going), 0.0), (y(0.0), z_top), (y(-0.06), -BELOW - 0.02)]
    return ck.prism(finish, f"{prefix}_ramp", mat, ramp, "x", x0 + 0.10, x1 - 0.10)


def build_l_ranch():
    """The L-shaped ranch, cartoony (2026-10-04), its two ideas pushed: the
    forward gabled wing (flush with the block's end, as Christina set it),
    its gable on a fat white barge with a fat round plaque over a window of
    two big lights, its roof running back into the block's until buried;
    and the porch along the set-back block, its low shed roof springing
    from the block's eave fascia over three fat timber posts to a fat white
    fascia, stopping just short of the wing's west eave, whose fascia meets
    the block's in a valley corner (the old porch roof ran on into the
    wing's side window). The roofs are plain
    (0.30 slabs at 20 degrees, 0.75 eaves and rakes): a low ranch's eaves
    stay straight; a kick would also break the porch roof's line from the
    block's eave. The wing's roof steps in where it meets the block's east
    rake (`notched_gable`)."""
    V = RANCH
    m = mats(walls="cottage_kit_walls_blue")
    trim_seed, shingle_seed = SEEDS["l_ranch"]
    rng = random.Random(trim_seed)
    floor, eave, pitch, over = V["floor"], V["eave"], V["pitch"], CC_OVER
    head = floor + CC_HEAD
    sill = head - 1.10
    bx0, bx1, by0, by1 = V["block"]
    wx0, wx1, wy0, wy1 = V["wing"]
    tan = math.tan(math.radians(pitch))
    top_in = wall_top_in(pitch)
    wall_top = eave + top_in
    e = E_IN
    # -- the block: side gables, the ridge along X
    half_b, ridge_y = (by1 - by0) / 2, (by0 + by1) / 2
    gable_side = Top(row=eave, gable=(half_b - e, half_b, eave), pitch=pitch)
    flat = Top(row=eave, flat=wall_top)
    door_x = (-1.6, -0.6)
    b_open = {
        # (the front window 10 cm in from the old, its casing clear of the fatter corner board)
        "front": [(door_x[0], door_x[1], floor + THRESHOLD, head), (-3.5, -2.2, sill, head)],
        "back": [(-3.0, -1.8, sill, head), (-0.4, 0.8, sill, head), (2.0, 3.2, sill, head)],
        "west": [(0.3, 1.5, sill, head), (2.3, 3.5, sill, head)],
    }
    # the block without its east wall: the wing is flush with that end, so
    # the whole east side is one wall below
    shell("", bx0, bx1, by0, by1, -BELOW, {"front": flat, "back": flat, "west": gable_side}, b_open, m["walls"], floor,
          which=("front", "back", "west"), base_mat=m["base"], e=e)
    cartoon_corners(rng, m["trim"], bx0, bx1, by0, by1, -BELOW - 0.03, wall_top + 0.02, which=("sw", "nw", "ne"))
    cartoon_openings(rng, "", b_open, (bx0, bx1, by0, by1), m, doors={("front", 0)})
    # its roof, plain, built in the quarter-turned frame (local x = -y), fat white barges on its rakes
    turned = ck.quarter_turn(finish)
    block = ck.plain_roof(turned, m["roof"], -ridge_y, half_b, eave, math.radians(pitch), CC_SLAB, bx0 - over, bx1 + over,
                          sag=CC_SAG, eave_over=over)
    plain_barges(rng, m, block, fin=turned, names=("west", "east"))

    # -- the wing forward to the street, flush with the block's east end
    # (Christina, 2 Oct 2026), its front and west walls here and its east
    # face part of the one east wall
    w_half, w_ridge = (wx1 - wx0) / 2, (wx0 + wx1) / 2
    wg = Top(row=eave, gable=(w_half - e, w_half, eave), pitch=pitch)
    wf = Top(row=eave, flat=wall_top - 0.01)
    w_open = {"front": [(w_ridge - 0.7, w_ridge + 0.7, sill, head)], "west": [(-3.2, -2.0, sill, head)]}
    shell("wing_", wx0, wx1, wy0, wy1, -BELOW - 0.02, {"front": wg, "west": wf}, w_open, m["walls"], floor,
          which=("front", "west"), base_mat=m["base"], e=e)
    cartoon_corners(rng, m["trim"], wx0, wx1, wy0, wy1, -BELOW - 0.05, wall_top + 0.01, which=("sw", "se"), prefix="wing_")
    cartoon_openings(rng, "wing_", w_open, (wx0, wx1, wy0, wy1), m, lights={("front", 0): 2})
    # the east wall, one shell from the wing's front corner to the block's
    # back corner: flat under the wing's eave, a gable under the block's
    # (the wing's window 20 cm forward of the old, its casing's head clear of the block's deeper front eave)
    east_ops = [(-3.2, -2.0, sill, head), (1.0, 2.2, sill, head)]

    def to_u(y):
        return y - (wy0 + e)
    wall("wall_east", (bx1, wy0 + e, 0.0), (0, 1, 0), (-1, 0, 0), (by1 - e) - (wy0 + e), -BELOW - 0.01,
         MixedTop(row=eave, flat=wall_top - 0.01, gable=(to_u(ridge_y), half_b, eave), pitch=pitch),
         [tuple(sorted((to_u(a0), to_u(a1)))) + (z0, z1) for a0, a1, z0, z1 in east_ops], floor, [m["walls"], m["base"]])
    cartoon_openings(rng, "", {"east": east_ops}, (bx0, bx1, wy0, by1), m)
    # a fat round plaque in the wing's gable
    ck.round_window(finish, rng, "wing_plaque", [m["trim"], m["trim"]], "x", w_ridge, head + 0.54, 0.12, wy0, -1, frame=0.08,
                    proud=0.05, sunk=0.03)

    # -- the porch along the set-back front: a slab to the wing's wall, three
    # fat timber posts, a low shed roof springing from the block's eave
    # fascia (its top a centimetre under the fascia's lowest, where the block
    # sags most) out to a fat white fascia, its east end 5 cm short of the
    # wing's west eave, which covers the rest of the slab
    pd = V["porch_d"]
    sx0, sx1, sy0 = bx0 - 0.06, wx0 + 0.02, by0 - pd - 0.06
    box("porch_slab", m["concrete"], sx0, sx1, sy0, by0 + 0.03, -0.10, floor)
    ptn = math.tan(math.radians(V["porch_pitch"]))
    y_fascia = by0 - over
    z_fascia_top = block.rt - block.r_out * tan - CC_SAG - 0.01

    def shed_top(y):
        return z_fascia_top + (y - y_fascia) * ptn
    ry = sy0 - V["porch_over"]
    pt = V["porch_slab"]
    px0, px1 = bx0 - over + 0.05, wx0 - over - 0.05
    slab("porch_roof", m["roof"], ((px0, ry, shed_top(ry)), (px1, ry, shed_top(ry)), (px1, by0 + 0.03, shed_top(by0 + 0.03)),
                                   (px0, by0 + 0.03, shed_top(by0 + 0.03))), pt)
    zf = shed_top(ry) - 0.02
    box("porch_fascia", m["trim"], px0 - 0.02, px1 + 0.02, ry - 0.05, ry + 0.02, zf - V["fascia"], zf, collide=False)
    post_y = sy0 + 0.22
    for k, x in enumerate(V["posts_x"]):
        z_u = shed_top(post_y) - pt
        ck.timber_post(finish, rng, f"post_{k}", m["trim"], x, post_y, floor - 0.02, (floor + 0.14, floor + 0.20), z_u, z_u + 0.04,
                       size=0.26, block=0.17, collar=0.165)
    ramp_step("stair", m["concrete"], door_x[0] - 0.10, door_x[1] + 0.10, sy0, -1, floor, 0.5)

    # -- the wing's roof: from its front rake back into the block's until the
    # block's top has risen over its ridge roll, its west eave meeting the
    # block's in a valley; its east eave stops 2 cm short of the block's
    # front eave, so it never runs on under the block's east rake
    rt_w = eave + w_half * tan + CC_SLAB / math.cos(math.radians(pitch))
    w_lo = wy0 - over
    w_hi = ridge_y - (block.rt - rt_w - 0.08 - CC_SAG - 0.06) / tan
    y_e = by0 - over - 0.02
    notched_gable("wing_roof", m["roof"], w_ridge, w_half, eave, pitch, CC_SLAB, [w_lo, y_e, w_hi],
                  [(wx0 - over, wx1 + over), (wx0 - over, wx1 + 0.02)])
    wing = ck.PlainRoof(w_ridge, w_half, eave, math.radians(pitch), CC_SLAB, w_lo, w_hi, 0.0, over)
    h = 0.24
    ck.swept(finish, "wing_ridge_cap", m["roof"], [(w_ridge - h, wing.top(w_ridge - h) - 0.03), (w_ridge, wing.rt - 0.03),
                                                    (w_ridge + h, wing.top(w_ridge + h) - 0.03), (w_ridge + h, wing.top(w_ridge + h) + 0.07),
                                                    (w_ridge, wing.rt + 0.08), (w_ridge - h, wing.top(w_ridge - h) + 0.07)],
             [(w_lo - 0.02, 0.0), (w_hi - 0.02, 0.0)], collide=False)
    ck.barge(finish, rng, "wing_barge", [m["trim"], m["trim"]], wing.profile, [], wing.r_out + 0.05, w_ridge, w_lo, -1,
             CC_BARGE[0], CC_BARGE[1], ())

    # -- raised shingle clusters on both roofs, from the shingle seed, and
    # vent pipes on the block's back slope: the block's front slope keeps off
    # the wing's roof and its eave off the porch roof and the wing; the
    # wing's keep off where it runs into the block and its stepped eaves
    srng = random.Random(shingle_seed)
    wing_box = (ridge_y - w_hi - 0.2, ridge_y - by0 + over + 0.2, wx0 - over - 0.1, wx1 + over + 0.1)
    front_eave = (half_b - 0.1, block.r_out + 0.2, bx0 - over - 1.0, bx1 + over + 1.0)
    tabs, vents = roof_dressing(srng, m, block, avoid={1: [wing_box]}, kick_avoid={1: [front_eave]}, vents=((-1, 2),), fin=turned)
    bm = bmesh.new()
    buried = (0.0, wing.r_out + 0.2, by0 - 0.4, w_hi + 1.0)
    t2, _ = ck.roof_clusters(srng, bm, wing, avoid={1: [buried], -1: [buried]}, scattered=1,
                             kick_avoid={1: [(0.0, wing.r_out + 0.2, y_e - 0.1, w_hi + 1.0)],
                                         -1: [(0.0, wing.r_out + 0.2, by0 - over - 0.1, w_hi + 1.0)]})
    finish("wing_roof_shingles", bm, [m["roof"]], collide=False)
    return dict(pitch=pitch, eave=eave, slab=CC_SLAB, eave_over=over, rake_over=over, kick=0.0, tabs=tabs + t2, vents=vents,
                door_clear=head - floor - THRESHOLD,
                extra=f"; porch roof {V['porch_pitch']:.0f} deg, {shed_top(post_y) - pt - floor:.2f} m clear at its posts; "
                      f"the wing's roof back to y {w_hi:.2f}")


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

    built = {}
    for v in VARIANTS:
        building(export, v)
        built[v] = BUILDERS[v]()
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
        b = built[v]
        if b:
            print(f"cottage_kit: {v} (cartoony): pitch {b['pitch']:.1f} deg, eave {b['eave']:.2f}, slab {b['slab']:.2f}, "
                  f"eave over {b['eave_over']:.2f}, rake over {b['rake_over']:.2f}, "
                  + (f"a {b['kick']:.1f} deg kick" if b.get("kick") else "no kick")
                  + f"; doors {b['door_clear']:.2f} m clear; {b['tabs']} shingle tabs, {b['vents']} vents" + b.get("extra", ""))
    print(f"cottage_kit: {len(VARIANTS)} variants, {total} triangles in all, {bad} coplanar pairs in all; "
          f"body {W:.1f} x {D:.1f} m, walls {T:.2f} m thick, ranch {RANCH['w']:.1f} m wide, "
          f"garage {HIP_GARAGE['w']:.1f} x {HIP_GARAGE['d']:.1f} m")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("cottage_kit: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], by_variant)


main()


