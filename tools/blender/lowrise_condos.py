"""The beach town's old low-rise condo blocks, blocked out (2026-10-02): the
South Shore plan's colony (`documentation/maps/south-shore-plan.html`,
decision 5), from Christina's aerial `documentation/reference/houses/
beach_lot_aerial.webp`: "one of the rows should be like that chunky repeating
lowrises in the top left of this pic, others should be like the ones in the
forground".

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/lowrise_condos.blend --python tools/blender/lowrise_condos.py -- \
        [--replace] [--save] [--render <folder>] [--bluff LxD] [--street LxD]

Builds, from scratch every run, two `kyt_variant`s into `export`, both at the
origin (Send writes one prop per variant, `lowrise_condos_bluff_block` and
`lowrise_condos_street_block`, as the park lamp's three go):

- **bluff_block**, the photo's top left: the colony's sea-side row, the same
  block three times along the bluff over the track. 23 x 11 m, three storeys
  of grey-blue stucco under a thick white flat roof slab that overhangs
  1.2 m to the sea; two identical 11.5 m units joined, split by a stucco fin;
  each unit's sea face is one wide recessed balcony per floor behind a solid
  stucco parapet on a white slab nose, with a slider and a window in the
  recessed wall; the street face carries a 4.8 m garage door and an entry
  door per unit under two windows per upper floor, and a stair bulkhead per
  unit on the roof. The stepping along the bluff is placement, not geometry.
- **bluff_block_b** (2026-10-03, Christina's rule for houses: the questions
  are variations, "we want this AND that", so an alternative is an extra
  variant): the same 23 x 11 m three-storey block as **three** narrower units
  of 7.67 m in its own sand stucco (`lowrise_condos_stucco_sand`, her "on the
  variations lets change the colors"), white balcony fronts like the slab,
  garage doors in the sand, terracotta entry doors (her "can the doors be
  different colors too"), and no roof bulkheads. In
  `export/variant_bluff_block_b`, eye shut.
- **street_block**, the photo's foreground: the colony's land-side block and
  the hillside's two. 23 x 11 m, two storeys of peach stucco under a white
  roof edge: `UNIT_W` (5.75 m) townhouse units, each with a teal door and a
  wide window at the street and a paired window with a chunky mullion above;
  piers 0.3 m proud at the corners and between units; parking as 1960s
  tuck-under carports along the back under the upper floor, a back door per
  unit. `--street 26x9` builds the hillside's sizes: the unit width stays,
  the units are centred, and what is left over is blank end bays.

Into `authored/demo` go, never exported, the photo's arrangement: three bluff
blocks 1.5 m apart stepping 0.61 m each along a bluff edge, the middle one
the `b` variant (linked copies of the export blocks' meshes, so reshaping one
reshapes its copies) and a tan street block across a 10 m street. Into the locked `reference` collection go the
footprint outlines, a 1.7 m figure, the demo's sloping ground with its bluff
and beach, and the `ground_line` marker Check reads (the walls reach 5 cm
below z = 0 on purpose, like the hardscape kit's). Everything the tool makes
carries `kyt_lowrise_condos`, so a rerun removes and rebuilds its own work and
keeps anything of hers; `export` holding anything untagged refuses without
`--replace`.

**Frame.** Real metres, Z up, the ground at z = 0, the origin at the
footprint's centre. The sea face of the bluff block and the street face of
the street block are at -Y here, which the glTF export (`send.py`,
`export_yup=True`) turns into Godot's +Z, the project's "facing +Z".

**Contract** (the plan's "enclosing"): public faces, doors, windows and
balconies, no interior. Every opening is a real hole through a wall of real
thickness, and every door is its own leaf set in the hole at a flush
threshold (1 cm over the ground or floor it opens onto); the glass is a slab
in the hole, so nothing behind it needs to exist. No door needs a step: the
bluff block's entries and garages and the street block's doors are at street
grade, the carport floor sits 12 mm proud with no collision as the park's
paving does, so the stair rule has nothing to do here. No two shapes share a
plane: a part that meets another laps 2 cm into it or stands proud of it.
The corners are solved the stucco way: the end walls run the full depth and
stand 2 cm proud of the front and back walls, whose ends are tucked inside
them (the street block's front corners sit inside its piers instead).

**Style.** Cartoony as the rest of the park: few big pieces, chunky slabs,
fins and piers; no casings, sills or rails on a stucco box; busy is the
failure mode. Stand-in materials by surface, `lowrise_condos_<surface>`.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_lowrise_condos"
VARIANTS = ("bluff_block", "bluff_block_b", "street_block")

# --- the plan's numbers ----------------------------------------------------
T = 0.22                   # wall thickness
BELOW = 0.05               # how far the walls reach below the ground
THRESHOLD = 0.01           # a door's sill over the floor outside it (the door is shut)
PANE_RECESS = 0.08         # glass and door leaves sit this far into their hole
TUCK = 0.02                # a wall's end inside the wall it meets
TUCK_SLAB = 0.04           # a slab's end inside a wall: deeper than a wall's, so their end faces differ
DOOR_W, DOOR_H = 1.0, 2.10

# the bluff block
BLUFF_L, BLUFF_D = 23.0, 11.0
B_STOREY = 2.75
B_FLOORS = 3
B_ROOF_UNDER = B_STOREY * B_FLOORS      # the roof slab's underside, 8.25
B_ROOF_T = 0.65                         # the thick white slab
B_OVER_SEA, B_OVER_SIDE, B_OVER_STREET = 1.20, 0.50, 0.60
BALC_D = 1.80                           # the balcony recess, sea edge to the recessed wall
FIN_W = 0.60                            # the party fin between the two units
FIN_PROUD = 0.10                        # fins and end walls past the sea edge
NOSE = 0.05                             # the floor slabs' white noses past the sea edge
SLAB_T = 0.25                           # the balcony floor slabs
PARAPET_H, PARAPET_T = 1.10, 0.20
PATIO_Z = 0.12                          # the ground floor's patio, a plinth slab
GARAGE_W, GARAGE_H = 4.80, 2.30
B_SILL, B_HEAD = 0.90, 2.15             # over each floor
BULKHEAD = (3.0, 2.4, 1.1)              # a stair bulkhead per unit on the roof
# where each unit's openings sit, as offsets from the unit's left edge, by
# how many units the block has: two of 11.5 m (bluff_block) or three of
# 7.67 m (bluff_block_b)
BLUFF_LAYOUTS = {
    2: dict(slider=(1.2, 4.8), window=(6.3, 9.3), garage=(1.2, 1.2 + GARAGE_W), entry=7.4,
            upper=((1.6, 4.0), (7.2, 8.6))),
    3: dict(slider=(0.9, 3.9), window=(4.7, 6.7), garage=(0.9, 5.1), entry=5.9,
            upper=((1.2, 3.4), (5.6, 6.6))),
}

# the street block
STREET_L, STREET_D = 23.0, 11.0
UNIT_W = 5.75                           # the townhouse unit: 23 m is four of them
S_STOREY = 2.70
S_WALL_TOP = 2 * S_STOREY + 0.55        # the parapet, 5.95
S_ROOF_Z = 2 * S_STOREY                 # the roof deck's underside, 5.40
S_ROOF_T = 0.15
CAP_Z0, CAP_Z1 = S_WALL_TOP - 0.04, S_WALL_TOP + 0.10   # the white cap ring
CAP_OUT, CAP_IN = 0.08, T + 0.02        # past the wall's outer face, past its inner
PIER_W, PIER_PROUD = 0.60, 0.30
CARPORT_D = 5.00                        # the tuck-under carports, under the upper floor
S_SLAB_T = 0.25                         # the floor over them
POST = 0.30
S_SILL, S_HEAD = 0.90, 2.10             # over each floor
PAIR_W, MULLION = 2.30, 0.12

# the demo in `authored/demo`
DEMO_Y_BLUFF = -45.0                    # the bluff row's centre line
DEMO_GAP = 1.5                          # between the three blocks
DEMO_STEP = 0.61                        # each block down, going +X (the ground's 2.5 %)
DEMO_Y_STREET = DEMO_Y_BLUFF + BLUFF_D / 2 + 10.0 + STREET_D / 2   # across a 10 m street
DEMO_SLOPE = -0.025                     # the ground along X
BLUFF_EDGE_Y = DEMO_Y_BLUFF - BLUFF_D / 2 - 1.5
BEACH_Z = -7.0


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {
    "lowrise_condos_stucco_blue": srgb("8d9aa8"),
    "lowrise_condos_stucco_peach": srgb("e6bf98"),
    "lowrise_condos_stucco_tan": srgb("c9a979"),
    "lowrise_condos_stucco_sand": srgb("d6c59b"),
    "lowrise_condos_door_terracotta": srgb("b8542e"),
    "lowrise_condos_slab": srgb("f1efe8"),
    "lowrise_condos_glass": srgb("2f4150"),
    "lowrise_condos_door_teal": srgb("4aa39f"),
    "lowrise_condos_door_dark": srgb("4e4238"),
    "lowrise_condos_garage": srgb("9a948a"),
    "lowrise_condos_concrete": srgb("b5b0a6"),
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

def finish(name, bm, coll, mats, collide=True, flat=True, variant=None):
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
    if variant:
        obj["kyt_variant"] = variant
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


def ring_bm(outer, inner, z0, z1):
    """A flat ring between two rectangles (x0, x1, y0, y1), one mesh, so the
    cap round a parapet shares no face with itself at its corners."""
    def corners(r, z):
        x0, x1, y0, y1 = r
        return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    bm = bmesh.new()
    o0 = [bm.verts.new(v) for v in corners(outer, z0)]
    o1 = [bm.verts.new(v) for v in corners(outer, z1)]
    i0 = [bm.verts.new(v) for v in corners(inner, z0)]
    i1 = [bm.verts.new(v) for v in corners(inner, z1)]
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((o1[k], o1[j], i1[j], i1[k]))      # top
        bm.faces.new((i0[k], i0[j], o0[j], o0[k]))      # bottom
        bm.faces.new((o0[k], o0[j], o1[j], o1[k]))      # outside
        bm.faces.new((i1[k], i1[j], i0[j], i0[k]))      # inside
    return bm


class Kit:
    """Builds one block's parts into a collection with a name prefix and a
    variant tag, so the export block and the demo copies come from one code."""

    def __init__(self, coll, prefix="", variant=None):
        self.coll, self.prefix, self.variant = coll, prefix, variant
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)
        return obj

    def box(self, name, mat, x0, x1, y0, y1, z0, z1, collide=True):
        """An axis-aligned box, 12 triangles."""
        assert x1 > x0 and y1 > y0 and z1 > z0, (name, x0, x1, y0, y1, z0, z1)
        bm = prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)
        return self.add(finish(self.prefix + name, bm, self.coll, [mat], collide=collide, variant=self.variant))

    def wall(self, name, mat, facing, face_at, a0, a1, z0, z1, openings=()):
        """One straight wall as a closed shell: two skins, ends, bottom, top
        and a real reveal round every opening. `facing` is the outer face's
        direction, '-y', '+y', '-x' or '+x'; `face_at` the outer face's
        coordinate on that axis; `a0..a1` the wall's extent along the other
        axis in world coordinates, as are the openings' (a0, a1, z0, z1)."""
        if facing == "-y":
            origin, u_dir, v_dir, to_u = (a0, face_at, 0.0), (1, 0, 0), (0, 1, 0), lambda a: a - a0
        elif facing == "+y":
            origin, u_dir, v_dir, to_u = (a1, face_at, 0.0), (-1, 0, 0), (0, -1, 0), lambda a: a1 - a
        elif facing == "-x":
            origin, u_dir, v_dir, to_u = (face_at, a1, 0.0), (0, -1, 0), (1, 0, 0), lambda a: a1 - a
        else:
            origin, u_dir, v_dir, to_u = (face_at, a0, 0.0), (0, 1, 0), (-1, 0, 0), lambda a: a - a0
        length = a1 - a0
        ops = []
        for wa0, wa1, oz0, oz1 in openings:
            ua, ub = sorted((to_u(wa0), to_u(wa1)))
            ops.append((ua, ub, oz0, oz1))
        O, U, V = Vector(origin), Vector(u_dir), Vector(v_dir)
        us, zs = {0.0, length}, {z0, z1}
        for u0, u1, oz0, oz1 in ops:
            assert 0.0 < u0 < u1 < length and z0 < oz0 < oz1 < z1, (name, u0, u1, oz0, oz1)
            us.update((u0, u1))
            zs.update((oz0, oz1))
        us, zs = sorted(us), sorted(zs)
        nu, nz = len(us) - 1, len(zs) - 1
        bm = bmesh.new()
        verts = {}

        def vert(i, j, side):
            key = (i, j, side)
            if key not in verts:
                verts[key] = bm.verts.new(O + U * us[i] + V * (T if side else 0.0) + Vector((0.0, 0.0, zs[j])))
            return verts[key]

        def in_opening(i, j):
            um, zm = (us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            return any(u0 < um < u1 and oz0 < zm < oz1 for u0, u1, oz0, oz1 in ops)

        for i in range(nu):
            for j in range(nz):
                if in_opening(i, j):
                    continue
                bm.faces.new((vert(i, j, 0), vert(i + 1, j, 0), vert(i + 1, j + 1, 0), vert(i, j + 1, 0)))
                bm.faces.new((vert(i, j, 1), vert(i + 1, j, 1), vert(i + 1, j + 1, 1), vert(i, j + 1, 1)))
            bm.faces.new((vert(i, 0, 0), vert(i + 1, 0, 0), vert(i + 1, 0, 1), vert(i, 0, 1)))
            bm.faces.new((vert(i, nz, 0), vert(i + 1, nz, 0), vert(i + 1, nz, 1), vert(i, nz, 1)))
        for i in (0, nu):
            for j in range(nz):
                bm.faces.new((vert(i, j, 0), vert(i, j + 1, 0), vert(i, j + 1, 1), vert(i, j, 1)))
        for u0, u1, oz0, oz1 in ops:
            i0, i1, j0, j1 = us.index(u0), us.index(u1), zs.index(oz0), zs.index(oz1)
            for j in range(j0, j1):
                bm.faces.new((vert(i0, j, 0), vert(i0, j, 1), vert(i0, j + 1, 1), vert(i0, j + 1, 0)))
                bm.faces.new((vert(i1, j, 0), vert(i1, j + 1, 0), vert(i1, j + 1, 1), vert(i1, j, 1)))
            for i in range(i0, i1):
                bm.faces.new((vert(i, j0, 0), vert(i + 1, j0, 0), vert(i + 1, j0, 1), vert(i, j0, 1)))
                bm.faces.new((vert(i, j1, 0), vert(i, j1, 1), vert(i + 1, j1, 1), vert(i + 1, j1, 0)))
        return self.add(finish(self.prefix + name, bm, self.coll, [mat], variant=self.variant))

    def pane(self, name, mat, facing, face_at, a0, a1, z0, z1, recess=PANE_RECESS, thick=0.05, collide=True):
        """A slab set in an opening, recessed into the wall, 2 cm into the
        reveals all round."""
        outward = -1 if facing[0] == "-" else 1
        lo, hi = sorted((face_at - recess * outward, face_at - (recess + thick) * outward))
        if facing[1] == "y":
            return self.box(name, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, collide=collide)
        return self.box(name, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, collide=collide)

    def ring(self, name, mat, outer, inner, z0, z1, collide=True):
        return self.add(finish(self.prefix + name, ring_bm(outer, inner, z0, z1), self.coll, [mat],
                               collide=collide, variant=self.variant))


# --- the bluff block ---------------------------------------------------------

def build_bluff(coll, prefix="", variant=None, L=BLUFF_L, D=BLUFF_D, units_n=2,
                walls_mat=None, parapet_mat=None, garage_mat=None, door_mat=None, bulkheads=True):
    """The sea-side block at the origin, sea face to -Y, street face to +Y.
    `units_n` identical units of L/units_n each; three storeys; the end walls
    run the full depth as the balconies' outer cheeks, FIN_PROUD past the sea
    edge and 2 cm past the street wall, so no two shells meet face to face.
    `walls_mat`, `parapet_mat`, `garage_mat` and `door_mat` default to the
    grey-blue stucco, the same, the garage grey and the dark door;
    `bulkheads` puts a stair bulkhead per unit on the roof."""
    k = Kit(coll, prefix, variant)
    slab, glass, garage, concrete = (material(n) for n in (
        "lowrise_condos_slab", "lowrise_condos_glass", "lowrise_condos_garage", "lowrise_condos_concrete"))
    stucco = walls_mat or material("lowrise_condos_stucco_blue")
    door = door_mat or material("lowrise_condos_door_dark")
    parapet_mat = parapet_mat or stucco
    garage_mat = garage_mat or garage
    lay = BLUFF_LAYOUTS[units_n]
    hl, hd = L / 2, D / 2
    unit_w = L / units_n
    top = B_ROOF_UNDER + 0.03                 # the walls end inside the roof slab
    sea_wall_y = -hd + BALC_D                 # the recessed wall's outer face
    units = [(-hl + u * unit_w, -hl + (u + 1) * unit_w) for u in range(units_n)]
    floors = [f * B_STOREY for f in range(B_FLOORS)]
    floor_tops = [PATIO_Z] + floors[1:]       # where each floor's slider opens onto

    # the recessed sea wall: per unit per floor a slider and a window
    sea_ops = []
    for x0, x1 in units:
        for z in floor_tops:
            sea_ops.append((x0 + lay["slider"][0], x0 + lay["slider"][1], z + THRESHOLD, z + B_HEAD))
            sea_ops.append((x0 + lay["window"][0], x0 + lay["window"][1], z + B_SILL, z + B_HEAD))
    k.wall("sea_wall", stucco, "-y", sea_wall_y, -(hl - T + TUCK), hl - T + TUCK, -BELOW, top, sea_ops)
    # the street wall: a garage door and an entry per unit, two windows per upper floor
    street_ops, entries = [], []
    for x0, x1 in units:
        street_ops.append((x0 + lay["garage"][0], x0 + lay["garage"][1], THRESHOLD, GARAGE_H))
        entries.append((x0 + lay["entry"], x0 + lay["entry"] + DOOR_W, THRESHOLD, DOOR_H))
        for z in floors[1:]:
            for w0, w1 in lay["upper"]:
                street_ops.append((x0 + w0, x0 + w1, z + 0.95, z + B_HEAD))
    k.wall("street_wall", stucco, "+y", hd, -(hl - T + TUCK), hl - T + TUCK, -BELOW, top, street_ops + entries)
    # the end walls, full depth, a narrow window per floor near the sea end
    end_ops = [(sea_wall_y + 0.8, sea_wall_y + 1.8, z + 0.95, z + B_HEAD) for z in floors]
    k.wall("end_wall_w", stucco, "-x", -hl, -hd - FIN_PROUD, hd + 0.02, -BELOW - 0.01, top - 0.01, end_ops)
    k.wall("end_wall_e", stucco, "+x", hl, -hd - FIN_PROUD, hd + 0.02, -BELOW - 0.01, top - 0.01, end_ops)
    # the fins between the units, from the sea edge 2 cm into the recessed wall
    for u in range(1, units_n):
        xb = units[u][0]
        k.box("fin" if units_n == 2 else f"fin_{u}", stucco, xb - FIN_W / 2, xb + FIN_W / 2, -hd - FIN_PROUD,
              sea_wall_y + TUCK, -BELOW - 0.02, top - 0.02)
    # the balcony floors: a white slab per floor with a nose past the sea
    # edge, through the fin and 2 cm into the end walls and the recessed
    # wall; the ground floor's is the patio plinth; on each a solid stucco
    # parapet per unit, its foot in the slab, its ends in the fin and end wall
    for f, z in enumerate(floor_tops):
        z0 = -BELOW + 0.01 if f == 0 else z - SLAB_T
        k.box(f"floor_slab_{f}", slab if f else concrete, -(hl - T + TUCK_SLAB), hl - T + TUCK_SLAB,
              -hd - NOSE, sea_wall_y + TUCK_SLAB, z0, z)
        for u, (x0, x1) in enumerate(units):
            px0 = (x0 - T + 0.02) if u == 0 else (x0 + FIN_W / 2 - 0.02)
            px1 = (x1 + T - 0.02) if u == units_n - 1 else (x1 - FIN_W / 2 + 0.02)
            k.box(f"parapet_{f}_{u}", parapet_mat, px0, px1, -hd, -hd + PARAPET_T, z - 0.015, z + PARAPET_H)
    # the roof: the thick white slab, and a stair bulkhead per unit
    k.box("roof_slab", slab, -hl - B_OVER_SIDE, hl + B_OVER_SIDE, -hd - B_OVER_SEA, hd + B_OVER_STREET,
          B_ROOF_UNDER, B_ROOF_UNDER + B_ROOF_T)
    bw, bd, bh = BULKHEAD
    for u, (x0, x1) in enumerate(units if bulkheads else ()):
        xc = (x0 + x1) / 2
        k.box(f"bulkhead_{u}", stucco, xc - bw / 2, xc + bw / 2, hd - 1.2 - bd, hd - 1.2,
              B_ROOF_UNDER + B_ROOF_T - 0.02, B_ROOF_UNDER + B_ROOF_T + bh)
    # glass and leaves: sliders and windows on the sea, garage leaves, entry
    # doors and windows on the street, windows in the ends; a white hood
    # over each entry
    for n, (a0, a1, z0, z1) in enumerate(sea_ops):
        k.pane(f"sea_{'slider' if n % 2 == 0 else 'window'}_{n // 2}", glass, "-y", sea_wall_y, a0, a1, z0, z1)
    for n, (a0, a1, z0, z1) in enumerate(street_ops):
        kind = "garage_leaf" if z0 == THRESHOLD else "window"
        k.pane(f"street_{kind}_{n}", garage_mat if kind == "garage_leaf" else glass, "+y", hd, a0, a1, z0, z1,
               recess=0.10 if kind == "garage_leaf" else PANE_RECESS)
    for n, (a0, a1, z0, z1) in enumerate(entries):
        k.pane(f"entry_door_{n}", door, "+y", hd, a0, a1, z0, z1)
        k.box(f"entry_hood_{n}", slab, a0 - 0.30, a1 + 0.30, hd - 0.02, hd + 0.90, DOOR_H + 0.20, DOOR_H + 0.35,
              collide=False)
    for n, (a0, a1, z0, z1) in enumerate(end_ops):
        k.pane(f"end_window_w_{n}", glass, "-x", -hl, a0, a1, z0, z1)
        k.pane(f"end_window_e_{n}", glass, "+x", hl, a0, a1, z0, z1)
    return k.objects


# --- the street block ---------------------------------------------------------

def unit_edges(L):
    """The townhouse units' x ranges, UNIT_W each, centred; what is left over
    is a blank end bay either side."""
    n = max(1, int(L // UNIT_W))
    x0 = -n * UNIT_W / 2
    return [(x0 + u * UNIT_W, x0 + (u + 1) * UNIT_W) for u in range(n)]


def build_street(coll, prefix="", variant=None, L=STREET_L, D=STREET_D, walls_mat=None):
    """The land-side block at the origin, street face to -Y, carports to +Y."""
    k = Kit(coll, prefix, variant)
    stucco = walls_mat or material("lowrise_condos_stucco_peach")
    slab, glass, door, concrete = (material(n) for n in (
        "lowrise_condos_slab", "lowrise_condos_glass", "lowrise_condos_door_teal", "lowrise_condos_concrete"))
    hl, hd = L / 2, D / 2
    units = unit_edges(L)
    upper = S_STOREY
    carport_wall_y = hd - CARPORT_D            # the ground floor's back wall, carport side
    slab_z0, slab_z1 = upper - S_SLAB_T, upper  # the floor over the carports
    floor_top = 0.012                           # the carport floor, 12 mm proud, no collision

    # the street wall: per unit a door and a wide window, a paired window over
    front_ops, doors, pairs = [], [], []
    for x0, x1 in units:
        doors.append((x0 + 0.75, x0 + 0.75 + DOOR_W, THRESHOLD, DOOR_H))
        front_ops.append((x0 + 2.5, x0 + 4.6, S_SILL, S_HEAD))
        pairs.append((x0 + 4.6 - PAIR_W, x0 + 4.6, upper + S_SILL, upper + S_HEAD))
    k.wall("street_wall", stucco, "-y", -hd, -(hl - 0.02), hl - 0.02, -BELOW, S_WALL_TOP, front_ops + doors + pairs)
    # the end walls, blank party walls, their fronts inside the corner piers
    # and their backs 2 cm proud of the back walls
    k.wall("end_wall_w", stucco, "-x", -hl, -hd + 0.02, hd + 0.02, -BELOW - 0.01, S_WALL_TOP - 0.01)
    k.wall("end_wall_e", stucco, "+x", hl, -hd + 0.02, hd + 0.02, -BELOW - 0.01, S_WALL_TOP - 0.01)
    # the upper back wall over the carports, its foot in the floor slab, a window per unit
    back_ops = [(x0 + 2.0, x0 + 4.0, upper + S_SILL, upper + S_HEAD) for x0, x1 in units]
    k.wall("back_wall_upper", stucco, "+y", hd, -(hl - T + TUCK), hl - T + TUCK, slab_z1 - 0.02, S_WALL_TOP, back_ops)
    # the carports' back wall at the ground, a back door per unit onto the floor
    back_doors = [(x0 + 1.0, x0 + 1.0 + DOOR_W, floor_top + THRESHOLD, floor_top + DOOR_H) for x0, x1 in units]
    k.wall("back_wall_carport", stucco, "+y", carport_wall_y, -(hl - T + TUCK), hl - T + TUCK, -BELOW,
           slab_z0 + 0.02, back_doors)
    # the floor over the carports, a white nose past the back wall; posts at
    # the unit lines under its edge; the carport floor
    k.box("carport_slab", slab, -(hl - T + TUCK_SLAB), hl - T + TUCK_SLAB, carport_wall_y - TUCK_SLAB, hd + 0.05,
          slab_z0, slab_z1)
    for n, (x0, x1) in enumerate(units[1:]):
        k.box(f"carport_post_{n}", concrete, x0 - POST / 2, x0 + POST / 2, hd - 0.05 - POST, hd - 0.05,
              -BELOW - 0.02, slab_z0 + 0.02)
    k.box("carport_floor", concrete, -(hl - T + 0.03), hl - T + 0.03, carport_wall_y + 0.03, hd - 0.01,
          -0.04, floor_top, collide=False)
    # the roof: a white deck inside the parapet and the white cap ring on it
    k.box("roof_deck", slab, -(hl - T + TUCK_SLAB), hl - T + TUCK_SLAB, -(hd - T + TUCK_SLAB), hd - T + TUCK_SLAB,
          S_ROOF_Z, S_ROOF_Z + S_ROOF_T)
    k.ring("roof_cap", slab, (-hl - CAP_OUT, hl + CAP_OUT, -hd - CAP_OUT, hd + CAP_OUT),
           (-hl + CAP_IN, hl - CAP_IN, -hd + CAP_IN, hd - CAP_IN), CAP_Z0, CAP_Z1, collide=False)
    # the piers: a square one wrapping each street corner, and one on each
    # unit line, PIER_PROUD past the street face; their tops a centimetre
    # under the cap's
    pier_top = CAP_Z1 - 0.01
    for tag, x in (("w", -hl), ("e", hl)):
        k.box(f"corner_pier_{tag}", stucco, x - PIER_PROUD, x + PIER_PROUD, -hd - PIER_PROUD, -hd + PIER_PROUD,
              -BELOW - 0.03, pier_top)
    for n, (x0, x1) in enumerate(units[1:]):
        k.box(f"unit_pier_{n}", stucco, x0 - PIER_W / 2, x0 + PIER_W / 2, -hd - PIER_PROUD, -hd + 0.02,
              -BELOW - 0.03, pier_top)
    # leaves and glass: teal doors, windows, the paired windows with a chunky
    # white mullion 1 cm proud of the wall, 2 cm into the glass
    for n, (a0, a1, z0, z1) in enumerate(doors):
        k.pane(f"door_{n}", door, "-y", -hd, a0, a1, z0, z1, recess=0.06)
    for n, (a0, a1, z0, z1) in enumerate(front_ops):
        k.pane(f"window_{n}", glass, "-y", -hd, a0, a1, z0, z1)
    for n, (a0, a1, z0, z1) in enumerate(pairs):
        k.pane(f"pair_window_{n}", glass, "-y", -hd, a0, a1, z0, z1)
        xm = (a0 + a1) / 2
        k.box(f"pair_mullion_{n}", slab, xm - MULLION / 2, xm + MULLION / 2, -hd - 0.01, -hd + PANE_RECESS + 0.02,
              z0 + 0.01, z1 - 0.01, collide=False)
    for n, (a0, a1, z0, z1) in enumerate(back_ops):
        k.pane(f"back_window_{n}", glass, "+y", hd, a0, a1, z0, z1)
    for n, (a0, a1, z0, z1) in enumerate(back_doors):
        k.pane(f"back_door_{n}", door, "+y", carport_wall_y, a0, a1, z0, z1, recess=0.06)
    return k.objects


# --- the demo and the reference ------------------------------------------------

def demo_bluff_positions():
    pitch = BLUFF_L + DEMO_GAP
    return [((i - 1) * pitch, DEMO_Y_BLUFF, -(i - 1) * DEMO_STEP) for i in range(3)]


def build_demo(demo, export_bluff, export_bluff_b):
    """Three bluff blocks along the bluff edge as linked copies of the export
    blocks' parts, the middle one the b variant, and a tan street block
    across the street."""
    for i, (x, y, z) in enumerate(demo_bluff_positions()):
        for src in (export_bluff_b if i == 1 else export_bluff):
            dup = src.copy()                   # shares its mesh
            dup.name = f"demo_bluff_{i}_{src.name}"
            dup.location = (x, y, z)
            if "kyt_variant" in dup:
                del dup["kyt_variant"]
            demo.objects.link(dup)
    tan = material("lowrise_condos_stucco_tan")
    for o in build_street(demo, prefix="demo_street_", walls_mat=tan):
        o.location = (0.0, DEMO_Y_STREET, 0.0)


def demo_ground_z(x, y):
    """The demo's ground: a 2.5 % fall along X, level pads under each block
    with a 2 m ramp round them, the bluff dropping to the beach at -Y."""
    base = DEMO_SLOPE * x
    pads = [(bx, by, BLUFF_L / 2 + 0.75, BLUFF_D / 2 + 1.0, bz) for bx, by, bz in demo_bluff_positions()]
    pads.append((0.0, DEMO_Y_STREET, STREET_L / 2 + 1.0, STREET_D / 2 + 0.5, 0.0))
    pads.append((0.0, 0.0, STREET_L / 2 + 1.5, BLUFF_D / 2 + 2.0, 0.0))
    z, best = base, 1e9
    for px, py, hx, hy, pz in pads:
        d = max(abs(x - px) - hx, abs(y - py) - hy)
        if d < best:
            best = d
            z = pz if d <= 0 else (pz + (base - pz) * min(1.0, d / 2.0))
    if y < BLUFF_EDGE_Y:
        t = min(1.0, (BLUFF_EDGE_Y - y) / 4.0)
        z = z + (BEACH_Z - z) * t
    return z


def demo_ground(name, coll, step=2.0):
    """The reference ground as one mesh: grass, the street band and the sand
    as three slots by face position."""
    grass = material("reference_ground", (0.35, 0.45, 0.25, 1.0))
    street = material("reference_street", (0.22, 0.22, 0.24, 1.0))
    sand = material("reference_sand", (0.78, 0.70, 0.50, 1.0))
    xs = [-60.0 + i * step for i in range(int(120 / step) + 1)]
    ys = [-62.0 + j * step for j in range(int(80 / step) + 1)]
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, demo_ground_z(x, y))) for x in xs] for y in ys]
    street_y0 = DEMO_Y_BLUFF + BLUFF_D / 2 + 0.5
    street_y1 = DEMO_Y_STREET - STREET_D / 2 - 0.5
    for a, b in zip(rows, rows[1:]):
        for p, q in zip(range(len(xs) - 1), range(1, len(xs))):
            f = bm.faces.new((a[p], a[q], b[q], b[p]))
            yc = (a[p].co.y + b[p].co.y) / 2
            f.material_index = 2 if yc < BLUFF_EDGE_Y - 3.0 else (1 if street_y0 < yc < street_y1 else 0)
    # the beach on to the water line
    far = [bm.verts.new((x, -120.0, BEACH_Z)) for x in xs]
    for p in range(len(xs) - 1):
        f = bm.faces.new((far[p], far[p + 1], rows[0][p + 1], rows[0][p]))
        f.material_index = 2
    return finish(name, bm, coll, [grass, street, sand], collide=False, flat=False)


def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm = prism_bm(ring, "z", 0.0, height - 0.40)
    body_verts = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:
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


def build_reference(reference, bluff, street):
    bl, bd = bluff
    sl, sd = street
    outline(f"footprint_{bl:g}x{bd:g}_bluff", reference, -bl / 2, bl / 2, -bd / 2, bd / 2)
    outline(f"footprint_{sl:g}x{sd:g}_street", reference, -sl / 2, sl / 2, -sd / 2, sd / 2, z=0.002)
    figure("figure_1p7m", reference, 3.5, 8.5)
    demo_ground("demo_ground_reference", reference)
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
                x0, x1 = -x1, -x0
            ou = min(u1, w1) - max(u0, w0)
            ov = min(v1, x1) - max(v0, x0)
            if ou > 1e-3 and ov > 1e-3:
                found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def report(objs, label):
    bpy.context.view_layer.update()
    objs = [o for o in objs if o.type == "MESH"]
    tris = triangles(objs)
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    print(f"lowrise_condos: {label}: {len(objs)} parts, {tris} triangles, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, z {min(zs):.2f}..{max(zs):.2f}")
    pairs = coplanar_pairs(objs)
    print(f"lowrise_condos: {label}: {len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    return tris


# --- renders -----------------------------------------------------------------

def render(folder, export_bluff, export_bluff_b, export_street, demo):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    reference = bpy.data.collections["reference"]
    authored = bpy.data.collections["authored"]
    authored.hide_render = False
    reference.hide_render = False
    for o in reference.all_objects:
        o.hide_render = not o.name.startswith("demo_ground")

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    k = Kit(stage)
    sea = k.box("_sea", mat("_sea", (0.16, 0.36, 0.52)), -400, 400, -420, BLUFF_EDGE_Y - 20.0, BEACH_Z - 0.6, BEACH_Z - 0.3,
                collide=False)
    fig_mat = mat("_figure_stage", (0.30, 0.22, 0.40))
    fig = figure("_figure", stage, 3.5, 8.5, mat=fig_mat)
    fig_demo = figure("_figure_demo", stage, -6.0, DEMO_Y_STREET - STREET_D / 2 - 3.0, demo_ground_z(-6.0, -31.0), mat=fig_mat)

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

    # a snapshot: setting a property while iterating a collection's live
    # `all_objects` stops the loop after a couple of objects
    demo_objects = list(demo.all_objects)

    def show(bluff=False, street=False, demo_on=False, figure_on=False, bluff_b=False):
        for o in export_bluff:
            o.hide_render = not bluff
        for o in export_bluff_b:
            o.hide_render = not bluff_b
        for o in export_street:
            o.hide_render = not street
        for o in demo_objects:
            o.hide_render = not demo_on
        fig.hide_render = not figure_on
        fig_demo.hide_render = not demo_on

    def shoot(name, eye, target, lens=32, size=(1600, 1000), ortho=None):
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 900
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"lowrise_condos: rendered {scene.render.filepath}")

    # the demo from the air at the photo's angle: inland, high, looking over
    # the street block to the bluff row and the sea
    show(demo_on=True)
    shoot("demo_aerial_photo_angle", (-66.0, 10.0, 34.0), (10.0, -44.0, 0.0), lens=35)
    # the bluff row from the beach below
    shoot("bluff_row_from_beach", (16.0, -92.0, -5.6), (-2.0, -46.0, 3.0), lens=30)
    # each export block three-quarter from its street, and elevations
    show(bluff=True)
    shoot("bluff_block_from_street", (17.0, 21.0, 1.7), (0.0, 4.5, 4.0), lens=28)
    shoot("bluff_block_sea_elevation", (0.0, -80.0, 4.5), (0.0, 0.0, 4.5), ortho=28.0)
    shoot("bluff_block_street_elevation", (0.0, 80.0, 4.5), (0.0, 0.0, 4.5), ortho=28.0)
    shoot("bluff_block_sea_three_quarter", (-19.0, -22.0, 2.0), (0.0, -4.0, 4.0), lens=28)
    show(bluff=True, figure_on=True)
    shoot("bluff_block_beside_figure", (13.0, 18.0, 1.6), (2.5, 5.5, 3.6), lens=28)
    # the b variant from the sea and from the street
    show(bluff_b=True)
    shoot("bluff_block_b_from_sea", (-19.0, -22.0, 2.0), (0.0, -4.0, 4.0), lens=28)
    shoot("bluff_block_b_from_street", (17.0, 21.0, 1.7), (0.0, 4.5, 4.0), lens=28)
    show(street=True)
    shoot("street_block_from_street", (-17.0, -20.0, 1.7), (0.0, -4.0, 3.0), lens=28)
    shoot("street_block_street_elevation", (0.0, -80.0, 3.0), (0.0, 0.0, 3.0), ortho=28.0)
    shoot("street_block_carports", (-15.0, 22.0, 1.7), (0.0, 6.0, 2.5), lens=28)
    show(street=True, figure_on=True)
    fig.location = (-4.0, -8.0, 0.0)
    shoot("street_block_beside_figure", (-9.0, -14.0, 1.6), (-1.0, -5.5, 2.4), lens=32)
    # plans with a metre grid and a 5 m bar
    ink = mat("_ink", (0.02, 0.02, 0.02))
    for gx in range(-13, 14):
        k.box(f"_grid_x{gx}", ink, gx - 0.015, gx + 0.015, -9.0, 9.0, -0.012, -0.004, collide=False)
    for gy in range(-9, 10):
        k.box(f"_grid_y{gy}", ink, -13.0, 13.0, gy - 0.015, gy + 0.015, -0.012, -0.004, collide=False)
    k.box("_bar", ink, -12.5, -7.5, -8.4, -8.2, -0.012, 0.03, collide=False)
    for n in range(6):
        k.box(f"_bar_tick{n}", ink, -12.5 + n - 0.03, -12.5 + n + 0.03, -8.7, -7.9, -0.012, 0.03, collide=False)
    show(bluff=True)
    shoot("bluff_block_plan", (0.0, 0.0, 80.0), (0.0, 0.0, 0.0), size=(1400, 1000), ortho=30.0)
    show(street=True)
    shoot("street_block_plan", (0.0, 0.0, 80.0), (0.0, 0.0, 0.0), size=(1400, 1000), ortho=30.0)
    show(demo_on=True)
    for o in list(stage.objects):
        if o.name.startswith(("_grid", "_bar")):
            bpy.data.objects.remove(o, do_unlink=True)
    shoot("demo_plan", (0.0, -30.0, 150.0), (0.0, -30.0, 0.0), size=(1400, 1000), ortho=95.0)


# --- main ----------------------------------------------------------------------

def parse_size(argv, flag, default):
    if flag in argv:
        l, d = argv[argv.index(flag) + 1].lower().split("x")
        return float(l), float(d)
    return default


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != "lowrise_condos":
        raise SystemExit(f"lowrise_condos: open lowrise_condos.blend, not {name}")
    bluff = parse_size(argv, "--bluff", (BLUFF_L, BLUFF_D))
    street = parse_size(argv, "--street", (STREET_L, STREET_D))
    export, authored, reference = (bpy.data.collections[n] for n in ("export", "authored", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"lowrise_condos: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "demo", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    # the two variants at the origin: the bluff block in `export` itself, the
    # street block in `export/variant_street_block` with its eye shut, as the
    # park lamp's acorn and pier stand beside its globe
    export_bluff = build_bluff(export, variant="bluff_block", L=bluff[0], D=bluff[1])
    sub_b = bpy.data.collections.new("variant_bluff_block_b")
    export.children.link(sub_b)
    sand = material("lowrise_condos_stucco_sand")
    export_bluff_b = build_bluff(sub_b, variant="bluff_block_b", L=bluff[0], D=bluff[1], units_n=3,
                                 walls_mat=sand, parapet_mat=material("lowrise_condos_slab"),
                                 garage_mat=sand, door_mat=material("lowrise_condos_door_terracotta"),
                                 bulkheads=False)
    sub = bpy.data.collections.new("variant_street_block")
    export.children.link(sub)
    export_street = build_street(sub, variant="street_block", L=street[0], D=street[1])
    demo = bpy.data.collections.new("demo")
    authored.children.link(demo)
    build_demo(demo, export_bluff, export_bluff_b)
    build_reference(reference, bluff, street)
    bpy.context.view_layer.update()
    for lc in bpy.context.view_layer.layer_collection.children["export"].children:
        if lc.name.startswith("variant_"):
            lc.hide_viewport = True

    report(export_bluff, "bluff_block (export)")
    report(export_bluff_b, "bluff_block_b (export/variant_bluff_block_b)")
    report(export_street, "street_block (export/variant_street_block)")
    report(list(demo.all_objects), "demo (authored/demo)")
    units = unit_edges(street[0])
    print(f"lowrise_condos: bluff block {bluff[0]:g} x {bluff[1]:g} m, {B_FLOORS} storeys at {B_STOREY:.2f}, "
          f"roof slab {B_ROOF_UNDER:.2f}..{B_ROOF_UNDER + B_ROOF_T:.2f} overhanging {B_OVER_SEA:.1f} m to the sea, "
          f"balconies {BALC_D:.1f} m deep, parapets {PARAPET_H:.2f}; two units of {bluff[0] / 2:g} m, "
          f"or three of {bluff[0] / 3:.2f} m in b, sand stucco, white fronts, garage leaves in the sand, "
          f"terracotta entry doors, no bulkheads")
    print(f"lowrise_condos: street block {street[0]:g} x {street[1]:g} m, 2 storeys at {S_STOREY:.2f}, "
          f"parapet {S_WALL_TOP:.2f}, cap to {CAP_Z1:.2f}; {len(units)} units of {UNIT_W:g} m "
          f"(end bays {(street[0] - len(units) * UNIT_W) / 2:.2f} m); carports {CARPORT_D:.1f} m deep at the back")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("lowrise_condos: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], export_bluff, export_bluff_b, export_street, demo)


main()
