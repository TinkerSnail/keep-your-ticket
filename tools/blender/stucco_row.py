"""The beach town's stucco row, blocked out (2026-10-02): Capitola's Venetian
Court (1920s) built as houses, a kit of four terrace units in loud colours.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/stucco_row.blend --python tools/blender/stucco_row.py -- \\
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, four unit variants into `export`, each in its
own child collection and every part marked `kyt_variant`, so Send writes one
prop per unit and a row is assembled from them later (`send.py`, Variants):

- `one_storey`: the beach-end unit of her first photo
  (`documentation/reference/houses/stucco_row_houses.webp`): a bay standing
  proud of two wings, a stepped parapet with a crest over the French doors,
  a short run of red clay tile on each wing's parapet, a stucco chimney on the
  front-left corner, a raised plaster ornament over the doors, a medallion on
  the crest and a tile plaque over the window.
- `one_storey_corner`: the end-of-row unit of her third photo (the README's
  "little hipped tile roofs on the corners"): a flat front with a blue door up
  two red steps, a planter by the door, and a square corner tower on the
  front-left corner under a small hipped (pyramid) tile roof.
- `two_storey`: a balcony on three carved brackets over the lane, French doors
  onto it, a door and planter below (`capitola_inner_lane.png`, the left side).
- `three_storey`: the inland end, an arched recess with the door inside it and
  a striped awning over a first-floor window.
- `one_storey_hipped` (2026-10-03, her rule that alternatives become extra
  variants): a one-storey unit under a hipped red tile roof over the whole
  unit, the other reading of the third photo's "little hipped tile roofs".
- `two_storey_iron`: the two-storey unit with the third photo's blue iron
  balcony, a thin plate on flat-bar scrolls with slender bars, in place of
  the timber one.

Each has two **end versions**, `<type>_end_west` and `<type>_end_east`,
identical but for sash windows in the side wall it exposes when it ends a
row (Christina, 2026-10-02: "end units can get side windows"), on -X or +X;
nothing else is mirrored, the chimney and the tower stay on the front-left
corner. Her first photo shows the pink end unit's lane-side window on the
chimney's side just behind it (the chimney stands at the exposed front
corner; mid-row units' chimneys stand at their party lines), so the west
version is the beach-end one there. Two bays down the 9 m depth
(`SIDE_BAYS`), one window per storey, the front's family.

Into `authored/demo_row`, 12 m east, go linked duplicates of the four laid as
a row of eight (`ROW`) stepping from one storey to three, each in its own
colour (an object-level material override on the shared mesh, so reshaping a
part in `export` reshapes every copy), with the lane in front. `reference`
holds the footprint outline, a 1.7 m figure and the `ground_line` marker
Check reads (the walls reach below z = 0 on purpose, like the hardscape
kit's). Everything the tool makes carries `kyt_stucco_row`, so a rerun removes
and rebuilds its own work and keeps anything of hers; `export` holding
anything untagged refuses without `--replace`.

**Frame.** Real metres, Z up, the ground at z = 0, each unit's origin at its
footprint's centre. The front (door, lane) faces -Y here, which the glTF
export (`send.py`, `export_yup=True`) turns into Godot's +Z, as the beach
cottage and `checks.py` say. Units are W wide (X) and D deep (Y) and stand at
pitch W; each party wall stands LAP past the pitch line so neighbours lap
2 cm into each other with no hairline between them.

**Contract** (enclosing): public faces, doors, windows, balconies, no
interior. Every opening is a real hole through a wall of real thickness with
its own leaf set in it; a door's sill is a centimetre or two below the ground
it opens onto, so the threshold is flush and the player meets the leaf. The
corner unit's two steps follow the park's stair rule: a narrow ramp collides,
the treads show past it and do not (`kyt_collision = none`). No two faces
share a plane: a part that meets another laps 2 cm into it or stands proud.

**The shell.** Each unit's walls are one closed mesh (`ring_shell`): a
right-angled plan ring of walls T thick with mitred corners, the parapet's
steps in its top, every opening with reveals. Its top slopes 2 cm inward and
its foot 1 cm inward (`CANT_T`, `CANT_B`), which is why two identical units
side by side never z-fight along the lap: their party walls' tops lean toward
their own roofs, so they are never in one plane. Two neighbours' fronts are in
one plane only if they stand at the same depth, so the row sets each unit a
little forward or back, as the photo's are (`ROW`'s third column).

**Sizes** read off the photos (every number is a constant below): the French
doors 1.4 by 2.1 m give the pink unit's front about 6 m: a 1.8 m wing with the
chimney and a window, a 3 m bay a quarter metre proud with a window and the
doors, a 1.2 m wing with a window. Depth 9 m is assumed (nothing in the photos
shows it; a 6 by 9 m unit is 54 m2, a Venetian Court cottage's size). Storeys
2.9 m, the wings' parapet 3.3 m over a storey's floor line, the bay's 0.5 m
higher, the crest 0.8 m. Cartoony, as the park's props: few big pieces, chunky
ornament and tile; the swirled stucco, the tile courses and the awning's
stripes are painting, not geometry.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

TAG = "kyt_stucco_row"
TYPES = ("one_storey", "one_storey_corner", "two_storey", "three_storey", "one_storey_hipped", "two_storey_iron")
END_SIDES = ("west", "east")
VARIANTS = TYPES + tuple(f"{t}_end_{side}" for side in END_SIDES for t in TYPES)

# --- the unit's numbers ----------------------------------------------------
W, D = 6.0, 9.0            # the footprint: across the front (X), and deep (Y)
HW, HD = W / 2, D / 2
T = 0.20                   # wall thickness
LAP = 0.01                 # each party wall past the pitch line: neighbours lap 2 cm
BELOW = 0.05               # the walls' outer foot under the ground
CANT_T, CANT_B = 0.02, 0.01  # the wall tops lean inward 2 cm, the feet 1 cm
S = 2.9                    # storey pitch: a floor line every S
PARAPET = 3.3              # the wings' parapet over the top storey's floor line
BAY_UP, CREST_UP = 0.5, 0.8  # the bay's parapet and the crest over the wings'
J = 0.25                   # the one-storey bay stands this far proud of its wings
BAY = (-1.2, 1.8)          # the bay's x range: a 1.8 m west wing, a 1.2 m east wing
DOOR_W, DOOR_H = 1.4, 2.1  # the French doors
SINGLE_W = 1.0             # a single door
BACK_W = 0.9               # the back door to the service lane
SASH_W, SASH_H, SILL = 0.7, 1.35, 0.75   # tall sashes sharing the doors' 2.1 m head line
THRESHOLD = 0.02           # a ground door's sill over the wall's foot (underground)
LEAF_RECESS, LEAF_T = 0.08, 0.05
GLASS_PROUD = 0.01         # the glass stands this far off a white leaf
CHIMNEY_W, CHIMNEY_D, CHIMNEY_TOP = 0.85, 0.70, 5.1
TOWER, TOWER_TOP, ROOF_RISE, ROOF_T, ROOF_OVER = 1.6, 4.5, 0.74, 0.12, 0.20
EAVE, HIP_PITCH, HIP_OVER = 3.0, math.radians(25), 0.30   # the hipped unit: eave, pitch, overhang
TILE_R, TILE_PITCH, TILE_OVER = 0.09, 0.21, 0.18   # the barrel tiles and the bed's overhang
TILE_BED = 0.16            # the bed's front edge over the parapet; it rises 0.12 more to the back
BALCONY_D, BALCONY_W, BRACKET_T = 0.9, 3.2, 0.14
RAIL_H, POST, BALUSTER = 1.0, 0.10, 0.07
PLANTER_L, PLANTER_D, PLANTER_H, PLANTER_T = 1.1, 0.45, 0.55, 0.08
RISER, GOING, STEP_W = 0.15, 0.30, 1.4
ARCH_HALF, ARCH_SPRING, ARCH_JAMB, RECESS_D = 0.95, 2.0, 0.27, 1.2
AWNING_OUT, AWNING_DROP, AWNING_VALANCE = 0.9, 0.5, 0.2

ROW_X = 12.0               # where the demo row's first unit stands
LANE_W = 3.5
# the demo row, west to east: variant, wall colour, set forward (-) or back (+).
# Neighbours' faces may not share a plane, so a stagger between two units is
# never 0, and beside a one-storey never 25 cm (its bay is that proud of its
# wings), 30 cm or 5 cm (its chimney is 30 cm proud of its wing, 5 cm of its bay)
ROW = (("one_storey_corner_end_west", "purple", 0.00), ("one_storey", "hot_pink", -0.20),
       ("one_storey", "orange", -0.05), ("one_storey_hipped", "turquoise", -0.10),
       ("two_storey", "peach", 0.05), ("two_storey_iron", "sunflower", -0.15),
       ("three_storey", "blue", 0.05), ("three_storey_end_east", "yellow", -0.20))
# the export variants' own colours
VARIANT_COLOUR = {"one_storey": "hot_pink", "one_storey_corner": "purple",
                  "two_storey": "peach", "three_storey": "blue",
                  "one_storey_hipped": "turquoise", "two_storey_iron": "sunflower"}
VARIANT_COLOUR.update({f"{t}_end_{side}": c for side in END_SIDES for t, c in list(VARIANT_COLOUR.items())})
SIDE_BAYS = (-2.0, 1.8)    # the side windows' centres down the depth (y): behind the chimney or tower, and aft


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


WALL_COLOURS = {"hot_pink": "ef3f9e", "mint": "a8e0b0", "orange": "f29a3c", "salmon": "f0937a",
                "brick_red": "b5482e", "purple": "9b6bc0", "blue": "4f8fd6", "peach": "f6b98f",
                "yellow": "f4d35e",
                "turquoise": "3fc1c9", "sunflower": "f6c310"}   # the hipped and the iron units' own (2026-10-03)
COLOURS = {
    "stucco_row_trim": srgb("f4f1ea"),       # white doors, sashes, rails
    "stucco_row_glass": srgb("3e5566"),
    "stucco_row_tile": srgb("b84a2b"),       # red clay tile, the red steps
    "stucco_row_ornament": srgb("4a86c8"),   # the raised plaster, painted blue
    "stucco_row_timber": srgb("8a5a33"),     # the balcony's brackets and rail
    "stucco_row_awning": srgb("c8402e"),     # one colour; the stripes are painting
    "stucco_row_soil": srgb("4a3826"),
    "stucco_row_door": srgb("2f5fa8"),       # the corner unit's blue door
    "stucco_row_flue": srgb("3a3634"),
    "stucco_row_iron": srgb("35598f"),       # the blue iron balcony
    "stucco_row_door_coral": srgb("ff6f61"),   # the hipped unit's doors (2026-10-03, "can the doors be different colors too")
    "stucco_row_door_cobalt": srgb("1f3fa8"),  # the iron unit's doors
}
for _name, _hex in WALL_COLOURS.items():
    COLOURS[f"stucco_row_walls_{_name}"] = srgb(_hex)


def material(name, colour=None):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour or COLOURS[name]
        bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def walls_material(colour):
    return material(f"stucco_row_walls_{colour}")


# --- building blocks -------------------------------------------------------

Z = Vector((0.0, 0.0, 1.0))


def finish(name, bm, coll, mats, variant=None, collide=True, flat=True, recalc=True):
    """A bmesh into an object in `coll`, tagged, with its material slots."""
    mesh = bpy.data.meshes.new(name)
    if recalc:
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
    if variant:
        obj["kyt_variant"] = variant
    if not collide:
        obj["kyt_collision"] = "none"
    coll.objects.link(obj)
    return obj


def face(bm, verts, hint):
    """A face wound so its normal points along `hint`."""
    a, b, c = verts[0].co, verts[1].co, verts[2].co
    if (b - a).cross(c - a).dot(hint) < 0:
        verts = list(reversed(verts))
    return bm.faces.new(verts)


def add_prism(bm, poly, axis, lo, hi, transform=None):
    """A 2D polygon extruded along `axis` ('x' gives (y, z) pairs, 'y' gives
    (x, z), 'z' gives (x, y)) into `bm`, through `transform` if given."""
    def at(a, b, t):
        p = Vector({"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis])
        return transform @ p if transform else p

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))


def prism_bm(poly, axis, lo, hi, transform=None):
    bm = bmesh.new()
    add_prism(bm, poly, axis, lo, hi, transform)
    return bm


def box(name, coll, mat, x0, x1, y0, y1, z0, z1, variant=None, collide=True):
    """An axis-aligned box, 12 triangles."""
    assert x1 > x0 and y1 > y0 and z1 > z0, (name, x0, x1, y0, y1, z0, z1)
    bm = prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)
    return finish(name, bm, coll, [mat], variant=variant, collide=collide)


def ngon(cx, cz, r, n, start=0.0):
    return [(cx + r * math.cos(start + math.tau * k / n), cz + r * math.sin(start + math.tau * k / n)) for k in range(n)]


def ring_shell(name, coll, mat, plan, foot, tops, openings, variant=None, closed=True, thick=T,
               cant_t=CANT_T, cant_b=CANT_B):
    """Walls T thick as one closed mesh along `plan`, a right-angled polygon
    (x, y) counter-clockwise from above; the walls' thickness lies to the left
    of each wall's direction (inside a closed ring). With `closed=False` the
    plan is an open polyline whose first and last walls get end faces.

    `tops[i]` is wall i's parapet profile, `[(u, h), ...]` from u = 0 along
    the wall: height h from that u on, a riser at every change; the two walls
    meeting at a corner must agree there. `openings[i]` is a list of
    (u0, u1, z0, z1) holes through wall i, each inside the wall's inner skin.
    The top faces lean cant_t inward and the bottom faces cant_b, so a unit's
    party wall never shares its neighbour's plane along the 2 cm lap."""
    n = len(plan)
    walls = n if closed else n - 1
    P = [Vector((x, y, 0.0)) for x, y in plan]
    U, L, V = [], [], []
    for i in range(walls):
        d = P[(i + 1) % n] - P[i]
        L.append(d.length)
        u = d / d.length
        U.append(u)
        V.append(Vector((-u.y, u.x, 0.0)))

    def convex(i):   # the corner at P[i], between wall i-1 and wall i
        return U[i - 1].cross(U[i]).z > 0

    bm = bmesh.new()
    verts = {}
    # every wall shares one set of rows, so two walls meet edge for edge at
    # their corner and the shell is watertight (no T-junctions)
    eps = 1e-6
    all_zs = sorted({z for ops in openings.values() for (_, _, z0, z1) in ops for z in (z0, z1)})
    all_hs = sorted({h for prof in tops.values() for _, h in prof})
    for ops in openings.values():
        for _, _, z0, z1 in ops:
            assert all(h > z1 + eps for h in all_hs), (name, "an opening reaches above a parapet", z1, all_hs)

    def vtx(p):
        key = (round(p.x, 5), round(p.y, 5), round(p.z, 5))
        if key not in verts:
            verts[key] = bm.verts.new(p)
        return verts[key]

    def rows_to(h):
        """The outer and inner skins' rows up to a column's top: the foot,
        every opening edge, every lower parapet height (so a riser meets
        split edges), then the top; the inner skin's foot and heights canted."""
        below = [x for x in all_hs if x < h - eps]
        outer = [foot] + all_zs + below + [h]
        inner = [foot + cant_b] + all_zs + [x - cant_t for x in below] + [h - cant_t]
        return outer, inner

    eps = 1e-6
    for i in range(walls):
        O, Ui, Vi, Li = P[i], U[i], V[i], L[i]
        start_end = (not closed) and i == 0
        end_end = (not closed) and i == walls - 1
        s = 0.0 if start_end else (thick if convex(i) else -thick)
        e = 0.0 if end_end else (thick if convex((i + 1) % n) else -thick)
        prof = tops[i]
        assert prof[0][0] == 0.0, (name, i, prof)
        ops = openings.get(i, ())

        def h_at(u):
            h = prof[0][1]
            for ub, hb in prof:
                if u >= ub - eps:
                    h = hb
            return h

        def pt(u, z, side):
            return O + Ui * u + (Vi * thick if side else Vector()) + Z * z

        us = {0.0, Li, s, Li - e}
        for ub, _ in prof[1:]:
            assert s - eps <= ub <= Li - e + eps and eps < ub < Li - eps, (name, i, "a step outside the inner skin", ub)
            us.add(ub)
        for u0, u1, z0, z1 in ops:
            assert s - eps <= u0 < u1 <= Li - e + eps, (name, i, "an opening outside the inner skin", u0, u1)
            assert foot + cant_b + eps < z0 < z1, (name, i, z0, z1)
            us.update((u0, u1))
        us = sorted(us)
        out, inw = -Vi, Vi

        def is_open(um, zm):
            return any(u0 < um < u1 and z0 < zm < z1 for u0, u1, z0, z1 in ops)

        prev_h = None
        for k in range(len(us) - 1):
            ua, ub = us[k], us[k + 1]
            um = (ua + ub) / 2
            h = h_at(um)
            has_outer = ua >= -eps and ub <= Li + eps
            has_inner = ua >= s - eps and ub <= Li - e + eps
            assert has_outer or has_inner, (name, i, ua, ub)
            rows_o, rows_i = rows_to(h)
            # the skins, a cell per row, left out where an opening is
            for r in range(len(rows_o) - 1):
                zao, zbo = rows_o[r], rows_o[r + 1]
                zai, zbi = rows_i[r], rows_i[r + 1]
                if is_open(um, (zao + zbo) / 2):
                    continue
                if has_outer:
                    face(bm, [vtx(pt(ua, zao, 0)), vtx(pt(ub, zao, 0)), vtx(pt(ub, zbo, 0)), vtx(pt(ua, zbo, 0))], out)
                if has_inner:
                    face(bm, [vtx(pt(ua, zai, 1)), vtx(pt(ub, zai, 1)), vtx(pt(ub, zbi, 1)), vtx(pt(ua, zbi, 1))], inw)
            # the top and the bottom: quads where both skins are, the mitre's
            # triangles at the corners
            top_o, top_i = h, h - cant_t
            bot_o, bot_i = foot, foot + cant_b
            if has_outer and has_inner:
                face(bm, [vtx(pt(ua, top_o, 0)), vtx(pt(ub, top_o, 0)), vtx(pt(ub, top_i, 1)), vtx(pt(ua, top_i, 1))], Z)
                face(bm, [vtx(pt(ua, bot_o, 0)), vtx(pt(ub, bot_o, 0)), vtx(pt(ub, bot_i, 1)), vtx(pt(ua, bot_i, 1))], -Z)
            elif has_outer:      # a convex corner's outer column
                ui = ub if ua < eps else ua
                face(bm, [vtx(pt(ua, top_o, 0)), vtx(pt(ub, top_o, 0)), vtx(pt(ui, top_i, 1))], Z)
                face(bm, [vtx(pt(ua, bot_o, 0)), vtx(pt(ub, bot_o, 0)), vtx(pt(ui, bot_i, 1))], -Z)
            else:                # a concave corner's inner column
                uo = ub if ub < eps else ua
                face(bm, [vtx(pt(uo, top_o, 0)), vtx(pt(ua, top_i, 1)), vtx(pt(ub, top_i, 1))], Z)
                face(bm, [vtx(pt(uo, bot_o, 0)), vtx(pt(ua, bot_i, 1)), vtx(pt(ub, bot_i, 1))], -Z)
            # a riser where the parapet steps
            if prev_h is not None and abs(prev_h - h) > eps:
                face(bm, [vtx(pt(ua, prev_h, 0)), vtx(pt(ua, h, 0)), vtx(pt(ua, h - cant_t, 1)), vtx(pt(ua, prev_h - cant_t, 1))],
                     -Ui if h > prev_h else Ui)
            prev_h = h
        # the reveals, split at the same rows as the skins beside them
        for u0, u1, z0, z1 in ops:
            rows = [z for z in sorted(set(all_zs) | set(all_hs)) if z0 - eps <= z <= z1 + eps]
            for r in range(len(rows) - 1):
                za, zb = rows[r], rows[r + 1]
                face(bm, [vtx(pt(u0, za, 0)), vtx(pt(u0, za, 1)), vtx(pt(u0, zb, 1)), vtx(pt(u0, zb, 0))], Ui)
                face(bm, [vtx(pt(u1, za, 0)), vtx(pt(u1, za, 1)), vtx(pt(u1, zb, 1)), vtx(pt(u1, zb, 0))], -Ui)
            cols = [u for u in us if u0 - eps <= u <= u1 + eps]
            for c in range(len(cols) - 1):
                ua, ub = cols[c], cols[c + 1]
                face(bm, [vtx(pt(ua, z1, 0)), vtx(pt(ub, z1, 0)), vtx(pt(ub, z1, 1)), vtx(pt(ua, z1, 1))], -Z)
                face(bm, [vtx(pt(ua, z0, 0)), vtx(pt(ub, z0, 0)), vtx(pt(ub, z0, 1)), vtx(pt(ua, z0, 1))], Z)
        # an open polyline's end faces
        for at_end, u in ((start_end, 0.0), (end_end, Li)):
            if not at_end:
                continue
            rows_o, rows_i = rows_to(h_at(u + (0.01 if u == 0.0 else -0.01)))
            for r in range(len(rows_o) - 1):
                face(bm, [vtx(pt(u, rows_o[r], 0)), vtx(pt(u, rows_i[r], 1)), vtx(pt(u, rows_i[r + 1], 1)), vtx(pt(u, rows_o[r + 1], 0))],
                     -Ui if u == 0.0 else Ui)
    loose = [e for e in bm.edges if not e.is_manifold]
    volume = bm.calc_volume(signed=True)
    assert not loose and volume > 0, (name, f"{len(loose)} non-manifold edges", f"volume {volume:.3f}")
    return finish(name, bm, coll, [mat], variant=variant, recalc=False)


def pane(name, coll, mat, axis, face_at, outward, a0, a1, z0, z1, variant, recess=LEAF_RECESS, thick=LEAF_T,
         collide=True):
    """A slab set in an opening, recessed into the wall, 2 cm into the
    reveals all round."""
    lo = face_at - recess * outward
    hi = face_at - (recess + thick) * outward
    if lo > hi:
        lo, hi = hi, lo
    if axis == "x":
        return box(name, coll, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, variant=variant, collide=collide)
    return box(name, coll, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, variant=variant, collide=collide)


def glazing(prefix, coll, axis, face_at, outward, panels, variant):
    """Glass panes standing GLASS_PROUD off a white leaf's face, their backs
    inside it. `panels`: (a0, a1, z0, z1) each, in the leaf's plane."""
    glass = material("stucco_row_glass")
    leaf_face = face_at - LEAF_RECESS * outward
    lo, hi = sorted((leaf_face + GLASS_PROUD * outward, leaf_face - 0.02 * outward))
    for k, (a0, a1, z0, z1) in enumerate(panels):
        if axis == "x":
            box(f"{prefix}_glass{k}", coll, glass, a0, a1, lo, hi, z0, z1, variant=variant, collide=False)
        else:
            box(f"{prefix}_glass{k}", coll, glass, lo, hi, a0, a1, z0, z1, variant=variant, collide=False)


def french_doors(prefix, coll, face_at, x0, x1, z0, z1, variant, leaf_mat=None):
    """A pair of glazed doors in a front wall: a white leaf, two glass
    panels either side of the meeting stiles, a plinth below the glass."""
    trim = leaf_mat or material("stucco_row_trim")
    pane(f"{prefix}_leaf", coll, trim, "x", face_at, -1, x0, x1, z0, z1, variant)
    xm = (x0 + x1) / 2
    glazing(prefix, coll, "x", face_at, -1, [(x0 + 0.12, xm - 0.05, z0 + 0.35, z1 - 0.12),
                                               (xm + 0.05, x1 - 0.12, z0 + 0.35, z1 - 0.12)], variant)


def sash_window(prefix, coll, axis, face_at, outward, a0, a1, z0, z1, variant, sill_board=True):
    """A white sash window: the frame as a leaf, the two sashes' glass proud
    of it with the meeting rail between, a chunky sill board under it."""
    trim = material("stucco_row_trim")
    pane(f"{prefix}_frame", coll, trim, axis, face_at, outward, a0, a1, z0, z1, variant)
    zm = (z0 + z1) / 2
    glazing(prefix, coll, axis, face_at, outward, [(a0 + 0.07, a1 - 0.07, z0 + 0.07, zm - 0.03),
                                                   (a0 + 0.07, a1 - 0.07, zm + 0.03, z1 - 0.07)], variant)
    if sill_board:
        lo, hi = sorted((face_at + 0.045 * outward, face_at - 0.015 * outward))   # 1.5 cm in: a neighbour's face lies 2 cm in
        if axis == "x":
            box(f"{prefix}_sill", coll, trim, a0 - 0.05, a1 + 0.05, lo, hi, z0 - 0.07, z0 - 0.01, variant=variant, collide=False)
        else:
            box(f"{prefix}_sill", coll, trim, lo, hi, a0 - 0.05, a1 + 0.05, z0 - 0.07, z0 - 0.01, variant=variant, collide=False)


def tile_run(name, coll, x0, x1, y_face, z_top, variant):
    """A short run of red clay barrel tile on a parapet: a sloping bed 2 cm
    into the wall's top, TILE_OVER proud of its face, and half-round tiles
    laid down the slope, sunk a centimetre into the bed. One mesh."""
    yf, yb = y_face - TILE_OVER, y_face + T + 0.02
    zf0, zb0 = z_top - 0.02, z_top - 0.02
    zf1, zb1 = z_top + TILE_BED, z_top + TILE_BED + 0.12
    bm = bmesh.new()
    add_prism(bm, [(yf, zf0), (yb, zb0), (yb, zb1), (yf, zf1)], "x", x0, x1)
    # the slope's frame: along it from the front edge, and its normal
    ang = math.atan2(zb1 - zf1, yb - yf)
    along = Vector((0.0, math.cos(ang), math.sin(ang)))
    normal = Vector((0.0, -math.sin(ang), math.cos(ang)))
    length = math.hypot(yb - yf, zb1 - zf1)
    origin = Vector((0.0, yf, zf1))
    frame = Matrix((Vector((1.0, 0.0, 0.0)), along, normal)).transposed().to_4x4()
    frame.translation = origin
    arc = [(TILE_R * math.cos(math.pi * k / 6), TILE_R * math.sin(math.pi * k / 6) - 0.01) for k in range(7)]
    count = int((x1 - x0 - 0.04) / TILE_PITCH)
    margin = (x1 - x0 - count * TILE_PITCH) / 2
    for k in range(count):
        cx = x0 + margin + (k + 0.5) * TILE_PITCH
        add_prism(bm, [(cx + a, b) for a, b in arc], "y", 0.02, length - 0.02, frame)
    return finish(name, bm, coll, [material("stucco_row_tile")], variant=variant, collide=False)


def chimney(prefix, coll, walls, x_left, y_face, variant):
    """A stucco chimney on a front corner: the shaft a centimetre proud of
    the side wall and CHIMNEY_D/2 of the front, a wider cap, a dark flue."""
    x0, x1 = x_left, x_left + CHIMNEY_W
    y0, y1 = y_face - CHIMNEY_D / 2, y_face + CHIMNEY_D / 2
    box(f"{prefix}chimney", coll, walls, x0, x1, y0, y1, -BELOW - 0.02, CHIMNEY_TOP, variant=variant)
    box(f"{prefix}chimney_cap", coll, walls, x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04,
        CHIMNEY_TOP - 0.15, CHIMNEY_TOP + 0.05, variant=variant, collide=False)
    box(f"{prefix}chimney_flue", coll, material("stucco_row_flue"), x0 + 0.2, x1 - 0.2, y0 + 0.17, y1 - 0.17,
        CHIMNEY_TOP + 0.03, CHIMNEY_TOP + 0.28, variant=variant, collide=False)


def ornament(prefix, coll, y_face, cx, z_base, variant):
    """The raised plaster over the French doors, chunky: a central vase 5 cm
    proud, a round scroll either side 4 cm proud, a tail each 3 cm proud,
    every piece 2 cm into the wall."""
    mat = material("stucco_row_ornament")
    vase = [(-0.10, 0.0), (0.10, 0.0), (0.15, 0.10), (0.08, 0.22), (0.17, 0.34), (0.24, 0.46), (0.09, 0.54),
            (-0.09, 0.54), (-0.24, 0.46), (-0.17, 0.34), (-0.08, 0.22), (-0.15, 0.10)]
    finish(f"{prefix}ornament_vase", prism_bm([(cx + a, z_base + b) for a, b in vase], "y", y_face - 0.05, y_face + 0.02),
           coll, [mat], variant=variant, collide=False)
    # each piece ends at its own depth inside the wall: three proud faces, three hidden backs, none in one plane
    for tag, sx in (("w", -1), ("e", 1)):
        finish(f"{prefix}ornament_scroll_{tag}", prism_bm(ngon(cx + sx * 0.40, z_base + 0.22, 0.15, 10), "y", y_face - 0.04, y_face + 0.025),
               coll, [mat], variant=variant, collide=False)
        finish(f"{prefix}ornament_tail_{tag}", prism_bm(ngon(cx + sx * 0.60, z_base + 0.07, 0.085, 8), "y", y_face - 0.03, y_face + 0.015),
               coll, [mat], variant=variant, collide=False)


def medallion(prefix, coll, y_face, cx, cz, variant):
    """A round medallion on the crest: a disc 4 cm proud with a boss 2 cm prouder."""
    mat = material("stucco_row_ornament")
    finish(f"{prefix}medallion", prism_bm(ngon(cx, cz, 0.22, 12, math.pi / 12), "y", y_face - 0.04, y_face + 0.02),
           coll, [mat], variant=variant, collide=False)
    finish(f"{prefix}medallion_boss", prism_bm(ngon(cx, cz, 0.10, 8, math.pi / 8), "y", y_face - 0.06, y_face - 0.02),
           coll, [mat], variant=variant, collide=False)


def plaque(name, coll, y_face, cx, cz, variant, size=0.26):
    """A small square tile plaque, 3 cm proud."""
    box(name, coll, material("stucco_row_tile"), cx - size / 2, cx + size / 2, y_face - 0.03, y_face + 0.02,
        cz - size / 2, cz + size / 2, variant=variant, collide=False)


def planter(prefix, coll, walls, x0, x1, y_face, variant):
    """A built-in stucco planter against the wall by the door: a ring of
    walls PLANTER_T thick, 2 cm into the house wall, soil 7 cm below the rim."""
    y0 = y_face - PLANTER_D
    y1 = y_face + 0.02
    plan = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    rim = PLANTER_H
    ring_shell(f"{prefix}planter", coll, walls, plan, -0.02, {i: [(0.0, rim)] for i in range(4)}, {}, variant=variant,
               thick=PLANTER_T, cant_t=0.01, cant_b=0.005)
    box(f"{prefix}planter_soil", coll, material("stucco_row_soil"), x0 + PLANTER_T - 0.02, x1 - PLANTER_T + 0.02,
        y0 + PLANTER_T - 0.02, y1 - PLANTER_T + 0.02, 0.10, rim - 0.07, variant=variant, collide=False)


def steps(prefix, coll, mat, x0, x1, y_face, n, variant):
    """`n` steps up to a door's sill at n * RISER, by the stair rule: the
    treads one stepped block, scenery, 2 cm into the wall; the ramp on the
    nosing line is the floor, narrower, ending inside the wall; nosing strips
    3 cm proud of the ramp so the flight reads as steps at any distance."""
    foot = y_face - n * GOING
    profile = [(foot, -BELOW - 0.03)]
    for k in range(1, n + 1):
        profile += [(foot + (k - 1) * GOING, k * RISER), (foot + k * GOING, k * RISER)]
    profile += [(y_face + 0.02, n * RISER), (y_face + 0.02, -BELOW - 0.03)]
    # the top tread's two points coincide with the wall line: drop the duplicate
    cleaned = [p for k, p in enumerate(profile) if k == 0 or p != profile[k - 1]]
    finish(f"{prefix}steps", prism_bm(cleaned, "x", x0, x1), coll, [mat], variant=variant, collide=False)
    ramp = [(foot - 0.05, -BELOW - 0.05), (foot, 0.0), (y_face, n * RISER), (y_face + 0.06, -BELOW - 0.05)]
    finish(f"{prefix}step_ramp", prism_bm(ramp, "x", x0 + 0.10, x1 - 0.10), coll, [mat], variant=variant)
    for k in range(1, n + 1):
        nose = foot + (k - 1) * GOING
        box(f"{prefix}step_nosing_{k}", coll, mat, x0 + 0.005, x1 - 0.005, nose - 0.01, nose + 0.05,
            k * RISER - 0.01, k * RISER + 0.03, variant=variant, collide=False)


def corner_tower(prefix, coll, walls, x_out, y_face, variant):
    """The corner unit's square tower on its front-left corner, 10 cm proud
    of both faces, under a hipped tile roof: a pyramid ROOF_T thick with a
    fascia, overhanging ROOF_OVER, the tower's top lost inside it."""
    x0, x1 = x_out - 0.10, x_out - 0.10 + TOWER
    y0, y1 = y_face - 0.10, y_face - 0.10 + TOWER
    box(f"{prefix}tower", coll, walls, x0, x1, y0, y1, -BELOW - 0.02, TOWER_TOP, variant=variant)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = TOWER / 2 + ROOF_OVER
    ze = TOWER_TOP - 0.10          # the eave: the roof's underside at the tower's wall is above its top
    bm = bmesh.new()
    corners = [Vector((cx + sx * half, cy + sy * half, 0.0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    top = [bm.verts.new(c + Z * ze) for c in corners]
    bot = [bm.verts.new(c + Z * (ze - ROOF_T)) for c in corners]
    apex = bm.verts.new(Vector((cx, cy, ze + ROOF_RISE)))
    apex_b = bm.verts.new(Vector((cx, cy, ze + ROOF_RISE - ROOF_T)))
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((top[k], top[j], apex))
        bm.faces.new((bot[j], bot[k], apex_b))
        bm.faces.new((top[k], bot[k], bot[j], top[j]))
    finish(f"{prefix}tower_roof", bm, coll, [material("stucco_row_tile")], variant=variant)
    # the hips' ridge tiles, chunky: a square bar down each hip from a
    # knob on the apex (the bars stop inside the knob: two opposite hips'
    # bars lie in one pair of planes and may not meet)
    apex_z = ze + ROOF_RISE
    box(f"{prefix}tower_knob", coll, material("stucco_row_tile"), cx - 0.10, cx + 0.10, cy - 0.10, cy + 0.10,
        apex_z - 0.12, apex_z + 0.12, variant=variant, collide=False)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        a = Vector((cx, cy, apex_z + 0.03))
        b = Vector((cx + sx * half, cy + sy * half, ze + 0.03))
        d = b - a
        length = d.length
        dn = d / length
        side = Vector((-sy, sx, 0.0)).normalized() * 0.05
        up = dn.cross(side).normalized() * 0.05
        if up.z < 0:
            up = -up
        bm = bmesh.new()
        ring = [a - side - up, a + side - up, a + side + up, a - side + up]
        near = [bm.verts.new(v + dn * 0.14) for v in ring]
        far = [bm.verts.new(v + d) for v in ring]
        bm.faces.new(near)
        bm.faces.new(list(reversed(far)))
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((near[k], near[j], far[j], far[k]))
        finish(f"{prefix}tower_hip_{'w' if sx < 0 else 'e'}{'s' if sy < 0 else 'n'}", bm, coll,
               [material("stucco_row_tile")], variant=variant, collide=False)


BALCONY_KINDS = {
    # the timber one (the lane photo's), and the third photo's blue iron one:
    # a thin plate on flat-bar scrolls, slender bars; same plan, same height
    "timber": dict(mat="stucco_row_timber", rail="stucco_row_trim", slab_t=0.15, bracket_t=BRACKET_T, bracket_up=0.0,
                   post=POST, top_rail=0.08, bot_rail=0.06, baluster=BALUSTER, pitch=0.22, post_up=0.08),
    # (posts a centimetre wider than the rails they hold, the bottom rail
    # 2 cm deeper than the balusters' feet, so nothing lapped shares a face)
    "iron": dict(mat="stucco_row_iron", rail="stucco_row_iron", slab_t=0.06, bracket_t=0.03, bracket_up=0.09,
                 post=0.05, top_rail=0.04, bot_rail=0.04, baluster=0.025, pitch=0.13, post_up=0.04),
}


def balcony(prefix, coll, y_face, cx, z_floor, variant, kind="timber"):
    """A balcony over the lane on three carved brackets: the slab 2 cm into
    the wall, the brackets' tops inside it, posts and a rail of square
    balusters round three sides; `kind` picks the timber or the iron sizes."""
    k = BALCONY_KINDS[kind]
    timber = material(k["mat"])
    trim = material(k["rail"])
    post_w = k["post"]
    x0, x1 = cx - BALCONY_W / 2, cx + BALCONY_W / 2
    y0, y1 = y_face - BALCONY_D, y_face + 0.02
    box(f"{prefix}balcony_slab", coll, timber, x0, x1, y0, y1, z_floor - k["slab_t"], z_floor, variant=variant)
    # the brackets: a scroll from the wall down and out to the slab's edge,
    # with a carved lobe, as a profile in (y, z) relative to the wall and floor
    scroll = [(0.03, -0.13), (-0.84, -0.13), (-0.84, -0.20), (-0.78, -0.24), (-0.70, -0.22), (-0.62, -0.30),
              (-0.50, -0.40), (-0.46, -0.52), (-0.36, -0.60), (-0.22, -0.62), (-0.10, -0.58), (-0.04, -0.46),
              (-0.08, -0.36), (0.03, -0.32)]
    up = k["bracket_up"]
    for n, bx in enumerate((x0 + 0.25, cx, x1 - 0.25)):
        finish(f"{prefix}balcony_bracket_{n}", prism_bm([(y_face + a, z_floor + b + up) for a, b in scroll], "x",
                                                        bx - k["bracket_t"] / 2, bx + k["bracket_t"] / 2),
               coll, [timber], variant=variant, collide=False)
    # posts at the outer corners and against the wall, rails between, balusters
    z1 = z_floor + RAIL_H
    posts = [(x0 + 0.03, y0 + 0.03), (x1 - 0.03 - post_w, y0 + 0.03), (x0 + 0.03, y1 - 0.04 - post_w), (x1 - 0.03 - post_w, y1 - 0.04 - post_w)]
    for n, (px, py) in enumerate(posts):
        box(f"{prefix}balcony_post_{n}", coll, timber, px, px + post_w, py, py + post_w, z_floor - 0.02, z1 + k["post_up"], variant=variant)
    runs = [("front", (x0 + 0.03 + post_w - 0.02, x1 - 0.03 - post_w + 0.02), y0 + 0.03 + post_w / 2, "x"),
            ("w", (y0 + 0.03 + post_w - 0.02, y1 - 0.04 - post_w + 0.02), x0 + 0.03 + post_w / 2, "y"),
            ("e", (y0 + 0.03 + post_w - 0.02, y1 - 0.04 - post_w + 0.02), x1 - 0.03 - post_w / 2, "y")]
    bal = k["baluster"]
    for tag, (a0, a1), at, axis in runs:
        lift = 0.0 if tag == "front" else 0.01   # the side rails meet the front rail inside a post, a centimetre up
        for rz, rt, name in ((z1 - k["top_rail"] + 0.02 + lift, k["top_rail"], "top"), (z_floor + 0.08 + lift, k["bot_rail"], "bottom")):
            if axis == "x":
                box(f"{prefix}balcony_rail_{tag}_{name}", coll, trim, a0, a1, at - rt / 2, at + rt / 2, rz, rz + rt, variant=variant,
                    collide=name == "top")
            else:
                box(f"{prefix}balcony_rail_{tag}_{name}", coll, trim, at - rt / 2, at + rt / 2, a0, a1, rz, rz + rt, variant=variant,
                    collide=name == "top")
        span = a1 - a0 - 0.04
        count = max(1, int(span / k["pitch"]))
        pitch = span / count
        zb0, zb1 = z_floor + 0.08 + k["bot_rail"] - 0.02, z1 - k["top_rail"] + 0.04
        for n in range(count):
            c = a0 + 0.02 + (n + 0.5) * pitch
            if axis == "x":
                box(f"{prefix}balcony_baluster_{tag}_{n}", coll, trim, c - bal / 2, c + bal / 2, at - bal / 2, at + bal / 2,
                    zb0, zb1, variant=variant, collide=False)
            else:
                box(f"{prefix}balcony_baluster_{tag}_{n}", coll, trim, at - bal / 2, at + bal / 2, c - bal / 2, c + bal / 2,
                    zb0, zb1, variant=variant, collide=False)


def hip_roof(prefix, coll, x0, x1, y0, y1, ze, variant):
    """A hipped tile roof over the whole unit: the eave rectangle at `ze`,
    the ridge along Y at HIP_PITCH, a slab ROOF_T thick with a fascia; a
    square bar along the ridge and down each hip from a knob at each ridge
    end (the bars stop inside the knobs, as the tower's do)."""
    tile = material("stucco_row_tile")
    half = (x1 - x0) / 2
    assert y1 - y0 > x1 - x0, "the ridge runs along the depth"
    cx = (x0 + x1) / 2
    rise = half * math.tan(HIP_PITCH)
    zr = ze + rise
    eave = [Vector((x0, y0, 0)), Vector((x1, y0, 0)), Vector((x1, y1, 0)), Vector((x0, y1, 0))]
    ridge = [Vector((cx, y0 + half, 0)), Vector((cx, y1 - half, 0))]
    bm = bmesh.new()
    for dz, flip in ((0.0, False), (-ROOF_T, True)):
        e = [bm.verts.new(v + Z * (ze + dz)) for v in eave]
        r = [bm.verts.new(v + Z * (zr + dz)) for v in ridge]
        faces = [(e[0], e[1], r[0]), (e[1], e[2], r[1], r[0]), (e[2], e[3], r[1]), (e[3], e[0], r[0], r[1])]
        for f in faces:
            bm.faces.new(tuple(reversed(f)) if flip else f)
        if not flip:
            top = e
        else:
            for k in range(4):
                j = (k + 1) % 4
                bm.faces.new((top[k], e[k], e[j], top[j]))
    finish(f"{prefix}roof", bm, coll, [tile], variant=variant)
    for n, rp in enumerate(ridge):
        box(f"{prefix}roof_knob_{n}", coll, tile, rp.x - 0.12, rp.x + 0.12, rp.y - 0.12, rp.y + 0.12, zr - 0.12, zr + 0.12,
            variant=variant, collide=False)
    box(f"{prefix}roof_ridge", coll, tile, cx - 0.05, cx + 0.05, ridge[0].y + 0.10, ridge[1].y - 0.10, zr - 0.02, zr + 0.08,
        variant=variant, collide=False)
    for n, (rp, corner) in enumerate(((ridge[0], eave[0]), (ridge[0], eave[1]), (ridge[1], eave[2]), (ridge[1], eave[3]))):
        a = rp + Z * (zr + 0.03)
        b = corner + Z * (ze + 0.03)
        d = b - a
        dn = d / d.length
        side = Vector((-dn.y, dn.x, 0.0)).normalized() * 0.05
        up = dn.cross(side).normalized() * 0.05
        if up.z < 0:
            up = -up
        bm = bmesh.new()
        ring = [a - side - up, a + side - up, a + side + up, a - side + up]
        near = [bm.verts.new(v + dn * 0.14) for v in ring]
        far = [bm.verts.new(v + d) for v in ring]
        bm.faces.new(near)
        bm.faces.new(list(reversed(far)))
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((near[k], near[j], far[j], far[k]))
        finish(f"{prefix}roof_hip_{n}", bm, coll, [tile], variant=variant, collide=False)


def awning(prefix, coll, y_face, x0, x1, z_top, variant):
    """A striped awning over a window: a sloped sheet with a valance hanging
    from its front edge, one closed prism along X, 2 cm into the wall."""
    yf = y_face - AWNING_OUT
    zf = z_top - AWNING_DROP
    profile = [(y_face + 0.02, z_top), (yf, zf), (yf, zf - AWNING_VALANCE), (yf + 0.04, zf - AWNING_VALANCE),
               (yf + 0.04, zf - 0.04), (y_face + 0.02, z_top - 0.04)]
    finish(f"{prefix}awning", prism_bm(profile, "x", x0, x1), coll, [material("stucco_row_awning")], variant=variant,
           collide=False)


def arch_frame(prefix, coll, mat, y_face, cx, variant):
    """The raised surround of the arched recess: an inverted U with a
    round head, 4 cm proud of the wall, through it and 2 cm into the recess,
    its outer edge 2 cm into the opening's reveals."""
    a, A = ARCH_HALF, ARCH_HALF + ARCH_JAMB
    zb, zt = -BELOW + 0.005, ARCH_SPRING + a + ARCH_JAMB
    poly = [(cx - A, zb), (cx - a, zb), (cx - a, ARCH_SPRING)]
    for k in range(1, 16):
        th = math.pi - math.pi * k / 16
        poly.append((cx + a * math.cos(th), ARCH_SPRING + a * math.sin(th)))
    poly += [(cx + a, ARCH_SPRING), (cx + a, zb), (cx + A, zb), (cx + A, zt), (cx - A, zt)]
    finish(f"{prefix}arch", prism_bm(poly, "y", y_face - 0.04, y_face + T + 0.02), coll, [mat], variant=variant)


# --- the units -------------------------------------------------------------

def shell_plan(bay):
    """The unit's plan ring, counter-clockwise from the front-left corner:
    a bay J proud between two wings when `bay`, else a plain rectangle."""
    x0, x1 = -HW - LAP, HW + LAP
    if not bay:
        return [(x0, -HD), (x1, -HD), (x1, HD), (x0, HD)]
    b0, b1 = BAY
    return [(x0, -HD + J), (b0, -HD + J), (b0, -HD), (b1, -HD), (b1, -HD + J), (x1, -HD + J), (x1, HD), (x0, HD)]


def back_openings(storeys, u_of):
    """The back wall's door and a window per storey, in wall u (the back
    wall runs east to west, so each pair is sorted)."""
    def span(x0, x1, z0, z1):
        return tuple(sorted((u_of(x0), u_of(x1)))) + (z0, z1)
    ops = [span(-1.0, -1.0 + BACK_W, -BELOW + THRESHOLD, DOOR_H), span(0.8, 0.8 + SASH_W, SILL, SILL + SASH_H)]
    for n in range(1, storeys):
        for x in (-1.5, 0.8):
            ops.append(span(x, x + SASH_W, n * S + SILL, n * S + SILL + SASH_H))
    return ops


def side_openings(storeys, u_of):
    """An end version's side windows: one per storey in each of SIDE_BAYS."""
    ops = []
    for n in range(storeys):
        for yc in SIDE_BAYS:
            ops.append(tuple(sorted((u_of(yc - SASH_W / 2), u_of(yc + SASH_W / 2)))) + (n * S + SILL, n * S + SILL + SASH_H))
    return ops


def side_fittings(prefix, coll, storeys, variant, side):
    x = -HW - LAP if side == "west" else HW + LAP
    for n in range(storeys):
        for k, yc in enumerate(SIDE_BAYS):
            sash_window(f"{prefix}side_window{n}{k}", coll, "y", x, -1 if side == "west" else 1,
                        yc - SASH_W / 2, yc + SASH_W / 2, n * S + SILL, n * S + SILL + SASH_H, variant)


def side_wall(plan, side):
    """The index of the exposed side wall in `plan` and its u for a y."""
    n = len(plan)
    x_side = -HW - LAP if side == "west" else HW + LAP
    for i in range(n):
        (x0, y0), (x1, y1) = plan[i], plan[(i + 1) % n]
        if abs(x0 - x1) < 1e-9 and abs(x0 - x_side) < 1e-9:   # the party line, not a bay's return
            return i, (lambda y, y0=y0: abs(y - y0))
    raise AssertionError("no side wall")


def back_fittings(prefix, coll, storeys, variant, door_mat=None):
    pane(f"{prefix}back_door", coll, door_mat or material("stucco_row_trim"), "x", HD, 1, -1.0, -1.0 + BACK_W,
         -BELOW + THRESHOLD, DOOR_H, variant)
    sash_window(f"{prefix}back_window0", coll, "x", HD, 1, 0.8, 0.8 + SASH_W, SILL, SILL + SASH_H, variant)
    for n in range(1, storeys):
        for k, x in enumerate((-1.5, 0.8)):
            sash_window(f"{prefix}back_window{n}{k}", coll, "x", HD, 1, x, x + SASH_W, n * S + SILL, n * S + SILL + SASH_H, variant)


def build_one_storey(coll, variant="one_storey", prefix="", end=None):
    """The pink unit: wings, a proud bay, the stepped parapet, chimney, tile
    runs, ornament, medallion, plaque, French doors and three sash windows."""
    walls = walls_material(VARIANT_COLOUR["one_storey"])
    plan = shell_plan(True)
    b0, b1 = BAY
    wing, bay, crest = PARAPET, PARAPET + BAY_UP, PARAPET + CREST_UP
    yw, yb = -HD + J, -HD
    door = (0.15, 0.15 + DOOR_W)
    crest_x = (door[0] + 0.1, door[1] - 0.1)
    win_w, win_b, win_e = (-2.0, -2.0 + 0.6), (-0.95, -0.95 + SASH_W), (2.05, 2.05 + SASH_W)
    head = SILL + SASH_H
    tops = {0: [(0.0, wing)], 1: [(0.0, wing)],
            2: [(0.0, wing), (T, bay), (crest_x[0] - b0, crest), (crest_x[1] - b0, bay), (b1 - b0 - T, wing)],
            3: [(0.0, wing)], 4: [(0.0, wing)], 5: [(0.0, wing)], 6: [(0.0, wing)], 7: [(0.0, wing)]}
    x_w0 = plan[0][0]
    openings = {
        0: [(win_w[0] - x_w0, win_w[1] - x_w0, SILL, head)],
        2: [(win_b[0] - b0, win_b[1] - b0, SILL, head), (door[0] - b0, door[1] - b0, -BELOW + THRESHOLD, DOOR_H)],
        4: [(win_e[0] - b1, win_e[1] - b1, SILL, head)],
        6: back_openings(1, lambda x: HW + LAP - x),
    }
    if end:
        wall_i, u_side = side_wall(plan, end)
        openings[wall_i] = side_openings(1, u_side)
    ring_shell(f"{prefix}shell", coll, walls, plan, -BELOW, tops, openings, variant=variant)
    if end:
        side_fittings(prefix, coll, 1, variant, end)
    sash_window(f"{prefix}window_w", coll, "x", yw, -1, *win_w, SILL, head, variant)
    sash_window(f"{prefix}window_bay", coll, "x", yb, -1, *win_b, SILL, head, variant)
    sash_window(f"{prefix}window_e", coll, "x", yw, -1, *win_e, SILL, head, variant)
    french_doors(f"{prefix}doors", coll, yb, *door, -BELOW + THRESHOLD, DOOR_H, variant)
    back_fittings(prefix, coll, 1, variant)
    chimney(prefix, coll, walls, x_w0 - 0.01, yw, variant)
    tile_run(f"{prefix}tile_w", coll, x_w0 + CHIMNEY_W + 0.08, b0 - 0.08, yw, wing, variant)
    tile_run(f"{prefix}tile_e", coll, b1 + 0.08, HW - 0.12, yw, wing, variant)
    ornament(prefix, coll, yb, (door[0] + door[1]) / 2, DOOR_H + 0.25, variant)
    medallion(prefix, coll, yb, (door[0] + door[1]) / 2, crest - 0.38, variant)
    plaque(f"{prefix}plaque", coll, yb, (win_b[0] + win_b[1]) / 2, head + 0.45, variant)


def build_corner(coll, variant="one_storey_corner", prefix="", end=None):
    """The purple end unit: a flat front, the tower on the front-left corner
    under its hipped tile roof, a blue door up two red steps, a planter, a
    window, a tile run and a plaque."""
    walls = walls_material(VARIANT_COLOUR["one_storey_corner"])
    plan = shell_plan(False)
    x_w0 = plan[0][0]
    yf = -HD
    wing, crest = PARAPET, PARAPET + 0.4
    door = (-0.9, -0.9 + SINGLE_W)
    win = (0.9, 0.9 + SASH_W)
    head = SILL + SASH_H
    sill_z = 2 * RISER + 0.01
    u = lambda x: x - x_w0
    tops = {0: [(0.0, wing), (u(door[0] - 0.4), crest), (u(door[1] + 0.4), wing)], 1: [(0.0, wing)],
            2: [(0.0, wing)], 3: [(0.0, wing)]}
    openings = {0: [(u(door[0]), u(door[1]), sill_z, sill_z + DOOR_H), (u(win[0]), u(win[1]), SILL, head)],
                2: back_openings(1, lambda x: HW + LAP - x)}
    if end:
        wall_i, u_side = side_wall(plan, end)
        openings[wall_i] = side_openings(1, u_side)
    ring_shell(f"{prefix}shell", coll, walls, plan, -BELOW, tops, openings, variant=variant)
    if end:
        side_fittings(prefix, coll, 1, variant, end)
    pane(f"{prefix}door", coll, material("stucco_row_door"), "x", yf, -1, *door, sill_z, sill_z + DOOR_H, variant)
    steps(prefix, coll, material("stucco_row_tile"), (door[0] + door[1]) / 2 - STEP_W / 2, (door[0] + door[1]) / 2 + STEP_W / 2,
          yf, 2, variant)
    sash_window(f"{prefix}window", coll, "x", yf, -1, *win, SILL, head, variant)
    back_fittings(prefix, coll, 1, variant)
    corner_tower(prefix, coll, walls, x_w0, yf, variant)
    planter(prefix, coll, walls, win[0] - 0.2, win[0] - 0.2 + PLANTER_L, yf, variant)
    tile_run(f"{prefix}tile", coll, 1.6, HW - 0.12, yf, wing, variant)
    plaque(f"{prefix}plaque", coll, yf, (door[0] + door[1]) / 2, sill_z + DOOR_H + 0.35, variant)
    medallion(prefix, coll, yf, (door[0] + door[1]) / 2, crest - 0.3, variant)


def build_two_storey(coll, variant="two_storey", prefix="", end=None, balcony_kind="timber", door_mat=None):
    """The peach unit: a door and planter below, French doors onto a
    bracketed balcony above, a window each floor, a crest with a medallion."""
    walls = walls_material(VARIANT_COLOUR[variant.split("_end_")[0]])
    plan = shell_plan(False)
    x_w0 = plan[0][0]
    yf = -HD
    wing, crest = S + PARAPET, S + PARAPET + 0.4
    door = (-1.7, -1.7 + SINGLE_W)
    win0 = (0.9, 0.9 + SASH_W)
    bdoor = (-DOOR_W / 2, DOOR_W / 2)
    win1 = (1.7, 1.7 + SASH_W)
    head0 = SILL + SASH_H
    floor1 = S
    bsill = floor1 + 0.01
    u = lambda x: x - x_w0
    tops = {0: [(0.0, wing), (u(-1.0), crest), (u(1.0), wing)], 1: [(0.0, wing)], 2: [(0.0, wing)], 3: [(0.0, wing)]}
    openings = {0: [(u(door[0]), u(door[1]), -BELOW + THRESHOLD, DOOR_H), (u(win0[0]), u(win0[1]), SILL, head0),
                    (u(bdoor[0]), u(bdoor[1]), bsill, bsill + DOOR_H), (u(win1[0]), u(win1[1]), S + SILL, S + head0)],
                2: back_openings(2, lambda x: HW + LAP - x)}
    if end:
        wall_i, u_side = side_wall(plan, end)
        openings[wall_i] = side_openings(2, u_side)
    ring_shell(f"{prefix}shell", coll, walls, plan, -BELOW, tops, openings, variant=variant)
    if end:
        side_fittings(prefix, coll, 2, variant, end)
    leaf = door_mat or material("stucco_row_trim")
    pane(f"{prefix}door", coll, leaf, "x", yf, -1, *door, -BELOW + THRESHOLD, DOOR_H, variant)
    sash_window(f"{prefix}window0", coll, "x", yf, -1, *win0, SILL, head0, variant)
    french_doors(f"{prefix}balcony_doors", coll, yf, *bdoor, bsill, bsill + DOOR_H, variant, leaf_mat=leaf)
    sash_window(f"{prefix}window1", coll, "x", yf, -1, *win1, S + SILL, S + head0, variant)
    back_fittings(prefix, coll, 2, variant, door_mat=door_mat)
    balcony(prefix, coll, yf, 0.0, floor1, variant, kind=balcony_kind)
    planter(prefix, coll, walls, door[0] - 0.15 - PLANTER_L, door[0] - 0.15, yf, variant)
    tile_run(f"{prefix}tile_w", coll, -HW + 0.12, -1.1, yf, wing, variant)
    tile_run(f"{prefix}tile_e", coll, 1.1, HW - 0.12, yf, wing, variant)
    plaque(f"{prefix}plaque", coll, yf, (door[0] + door[1]) / 2, DOOR_H + 0.35, variant)
    medallion(prefix, coll, yf, 0.0, crest - 0.3, variant)


def build_three_storey(coll, variant="three_storey", prefix="", end=None):
    """The blue inland unit: an arched recess with the door in its back
    wall, a window beside it, two windows a floor above with a striped awning
    over the first floor's west one, a crest with a medallion."""
    walls = walls_material(VARIANT_COLOUR["three_storey"])
    plan = shell_plan(False)
    x_w0 = plan[0][0]
    yf = -HD
    wing, crest = 2 * S + PARAPET, 2 * S + PARAPET + 0.4
    cx = -0.7
    A = ARCH_HALF + ARCH_JAMB
    arch_top = ARCH_SPRING + ARCH_HALF + ARCH_JAMB
    win0 = (1.3, 1.3 + SASH_W)
    head = SILL + SASH_H
    wins = ((-1.8, -1.8 + 1.0, 1.5), (0.95, 0.95 + SASH_W, SASH_H))   # x0, x1, tall
    u = lambda x: x - x_w0
    tops = {0: [(0.0, wing), (u(-1.0), crest), (u(1.0), wing)], 1: [(0.0, wing)], 2: [(0.0, wing)], 3: [(0.0, wing)]}
    front = [(u(cx - A + 0.02), u(cx + A - 0.02), -BELOW + THRESHOLD, arch_top - 0.02), (u(win0[0]), u(win0[1]), SILL, head)]
    for n in (1, 2):
        for w0, w1, tall in wins:
            front.append((u(w0), u(w1), n * S + SILL, n * S + SILL + tall))
    openings = {0: front, 2: back_openings(3, lambda x: HW + LAP - x)}
    if end:
        wall_i, u_side = side_wall(plan, end)
        openings[wall_i] = side_openings(3, u_side)
    ring_shell(f"{prefix}shell", coll, walls, plan, -BELOW, tops, openings, variant=variant)
    if end:
        side_fittings(prefix, coll, 3, variant, end)
    arch_frame(prefix, coll, material("stucco_row_ornament"), yf, cx, variant)
    # the recess: its two sides and back as one open shell whose visible
    # skin faces the recess, the door in the back, a ceiling slab over it
    r0, r1 = cx - ARCH_HALF - 0.02, cx + ARCH_HALF + 0.02
    yr0, yr1 = yf + T - 0.02, yf + T + RECESS_D
    crown = ARCH_SPRING + ARCH_HALF
    rplan = [(r0, yr0), (r0, yr1), (r1, yr1), (r1, yr0)]
    rdoor = (cx - SINGLE_W / 2, cx + SINGLE_W / 2)
    ring_shell(f"{prefix}recess", coll, walls, rplan, -BELOW - 0.01,
               {0: [(0.0, crown + 0.06)], 1: [(0.0, crown + 0.06)], 2: [(0.0, crown + 0.06)]},
               {1: [(rdoor[0] - r0, rdoor[1] - r0, -BELOW + THRESHOLD, DOOR_H)]}, variant=variant, closed=False)
    pane(f"{prefix}door", coll, material("stucco_row_trim"), "x", yr1, -1, *rdoor, -BELOW + THRESHOLD, DOOR_H, variant)
    box(f"{prefix}recess_ceiling", coll, walls, r0 - T - 0.02, r1 + T + 0.02, yr0 - 0.02, yr1 + T + 0.02,
        crown + 0.02, crown + 0.22, variant=variant)
    sash_window(f"{prefix}window0", coll, "x", yf, -1, *win0, SILL, head, variant)
    for n in (1, 2):
        for k, (w0, w1, tall) in enumerate(wins):
            sash_window(f"{prefix}window{n}{k}", coll, "x", yf, -1, w0, w1, n * S + SILL, n * S + SILL + tall, variant)
    awning(prefix, coll, yf, wins[0][0] - 0.2, wins[0][1] + 0.2, S + SILL + wins[0][2] + 0.12, variant)
    back_fittings(prefix, coll, 3, variant)
    tile_run(f"{prefix}tile_w", coll, -HW + 0.12, -1.1, yf, wing, variant)
    tile_run(f"{prefix}tile_e", coll, 1.1, HW - 0.12, yf, wing, variant)
    medallion(prefix, coll, yf, 0.0, crest - 0.3, variant)


def build_hipped(coll, variant="one_storey_hipped", prefix="", end=None):
    """The mint unit under a hipped tile roof over the whole unit: a flat
    front with a blue door, a window with a planter under it, a plaque, the
    walls ending inside the roof slab."""
    walls = walls_material(VARIANT_COLOUR[variant.split("_end_")[0]])
    plan = shell_plan(False)
    x_w0 = plan[0][0]
    yf = -HD
    top = EAVE + 0.08   # 2 cm inside the slab at the walls' outer face
    door = (-0.9, -0.9 + SINGLE_W)
    win = (0.9, 0.9 + SASH_W)
    head = SILL + SASH_H
    u = lambda x: x - x_w0
    tops = {i: [(0.0, top)] for i in range(4)}
    openings = {0: [(u(door[0]), u(door[1]), -BELOW + THRESHOLD, DOOR_H), (u(win[0]), u(win[1]), SILL, head)],
                2: back_openings(1, lambda x: HW + LAP - x)}
    if end:
        wall_i, u_side = side_wall(plan, end)
        openings[wall_i] = side_openings(1, u_side)
    ring_shell(f"{prefix}shell", coll, walls, plan, -BELOW, tops, openings, variant=variant)
    if end:
        side_fittings(prefix, coll, 1, variant, end)
    coral = material("stucco_row_door_coral")
    pane(f"{prefix}door", coll, coral, "x", yf, -1, *door, -BELOW + THRESHOLD, DOOR_H, variant)
    sash_window(f"{prefix}window", coll, "x", yf, -1, *win, SILL, head, variant)
    back_fittings(prefix, coll, 1, variant, door_mat=coral)
    planter(prefix, coll, walls, win[0] - 0.2, win[0] - 0.2 + PLANTER_L, yf, variant)
    plaque(f"{prefix}plaque", coll, yf, (door[0] + door[1]) / 2, DOOR_H + 0.35, variant)
    hip_roof(prefix, coll, -HW - HIP_OVER, HW + HIP_OVER, -HD - HIP_OVER, HD + HIP_OVER, EAVE, variant)


BUILDERS = {"one_storey": build_one_storey, "one_storey_corner": build_corner,
            "two_storey": build_two_storey, "three_storey": build_three_storey,
            "one_storey_hipped": build_hipped,
            "two_storey_iron": (lambda coll, variant="two_storey_iron", end=None:
                                build_two_storey(coll, variant=variant, end=end, balcony_kind="iron",
                                                 door_mat=material("stucco_row_door_cobalt")))}
BUILDERS.update({f"{t}_end_{side}": (lambda coll, b=b, t=t, side=side: b(coll, variant=f"{t}_end_{side}", end=side))
                 for side in END_SIDES for t, b in list(BUILDERS.items())})


# --- reference and the demo row -------------------------------------------

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


def outline(name, coll, pts, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in pts]
    for i in range(len(vs)):
        bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def build_reference(reference):
    outline("footprint_6x9", reference, [(-HW, -HD), (HW, -HD), (HW, HD), (-HW, HD)])
    figure("figure_1p7m", reference, -4.6, -6.0)
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        reference.objects.link(marker)


def place_row(coll, parts, x0=ROW_X, y0=0.0, turn=0.0, order=ROW):
    """Linked duplicates of each variant's parts along a row at pitch W,
    each unit set forward or back by its stagger, in its own wall colour."""
    made = []
    for k, (variant, colour, dy) in enumerate(order):
        wall_mat = walls_material(colour)
        unit_x = x0 + k * W
        for src in parts[variant]:
            dup = src.copy()
            dup.name = f"row{k}_{src.name}"
            dup.rotation_euler = (0.0, 0.0, turn)
            local = Vector((0.0, dy, 0.0))
            dup.location = Vector((unit_x, y0, 0.0)) + Matrix.Rotation(turn, 3, "Z") @ local
            for key in ("kyt_variant",):
                if key in dup:
                    del dup[key]
            dup[TAG] = True
            for slot in dup.material_slots:
                if slot.material and slot.material.name.startswith("stucco_row_walls_"):
                    slot.link = "OBJECT"
                    slot.material = wall_mat
            coll.objects.link(dup)
            made.append(dup)
    return made


def build_demo_row(authored, parts):
    row = bpy.data.collections.new("demo_row")
    authored.children.link(row)
    made = place_row(row, parts)
    # an end version's windows must look out of the row, not into a neighbour
    for k, (variant, _, _) in enumerate(ROW):
        if "_end_" not in variant:
            continue
        side = variant.rsplit("_", 1)[1]
        neighbour = k - 1 if side == "west" else k + 1
        covered = 0 <= neighbour < len(ROW)
        print(f"stucco_row: demo row: row{k} {variant}: side windows on the {side} "
              + (f"FACE row{neighbour} {ROW[neighbour][0]}" if covered else "are exposed"))
        assert not covered, (k, variant, "its side windows face a neighbour")
    # the lane in front, its top the ground, under the row's footprint too
    # (the recess has no floor of its own: the ground is its floor)
    x0, x1 = ROW_X - HW - 2.0, ROW_X + (len(ROW) - 1) * W + HW + 2.0
    lane = material("stucco_row_lane", (0.55, 0.50, 0.47, 1.0))
    made.append(box("demo_lane", row, lane, x0, x1, -HD - 0.3 - LANE_W, HD + 0.3, -0.30, 0.0, collide=False))
    return made


# --- checks ------------------------------------------------------------------

def triangles(objs):
    total = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            total += len(o.data.loop_triangles)
    return total


def coplanar_pairs(objs, tol=1e-4):
    """Pairs of faces from different objects lying in one plane (either way
    up) and overlapping in area, by their bounds in the plane: the z-fights.
    Faces are keyed by their plane, so a row of units scans in seconds."""
    faces = []
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        for p in o.data.polygons:
            n = (mw.to_3x3() @ p.normal).normalized()
            pts = [mw @ o.data.vertices[i].co for i in p.vertices]
            for c in (n.x, n.y, n.z):      # one orientation per plane
                if abs(c) > 1e-6:
                    if c < 0:
                        n = -n
                    break
            d = n.dot(pts[0])
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            us = [q.dot(e1) for q in pts]
            vs = [q.dot(e2) for q in pts]
            faces.append(((round(n.x, 2), round(n.y, 2), round(n.z, 2)), d, o.name, min(us), max(us), min(vs), max(vs)))
    faces.sort(key=lambda f: (f[0], f[1]))
    found = []
    for i in range(len(faces)):
        ki, di, oi, u0, u1, v0, v1 = faces[i]
        j = i + 1
        while j < len(faces) and faces[j][0] == ki and faces[j][1] - di < tol:
            kj, dj, oj, w0, w1, x0, x1 = faces[j]
            j += 1
            if oi == oj:
                continue
            ou = min(u1, w1) - max(u0, w0)
            ov = min(v1, x1) - max(v0, x0)
            if ou > 1e-3 and ov > 1e-3:
                found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def bounds(objs):
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def report(label, objs):
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == "MESH"]
    lo, hi = bounds(meshes)
    tris = triangles(meshes)
    print(f"stucco_row: {label}: {len(meshes)} parts, {tris} triangles, "
          f"x {lo.x:.2f}..{hi.x:.2f}, y {lo.y:.2f}..{hi.y:.2f}, z {lo.z:.2f}..{hi.z:.2f}")
    return tris


# --- renders -----------------------------------------------------------------

def render(folder, parts, row_objs):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = False
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    ground = mat("_ground", (0.62, 0.58, 0.52))
    paving = mat("_paving", (0.66, 0.56, 0.54))
    sand = mat("_sand", (0.86, 0.80, 0.64))
    sea = mat("_sea", (0.30, 0.50, 0.62))
    wall = mat("_seawall", (0.70, 0.68, 0.64))
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    box("_ground", stage, ground, -80, 120, -80, 80, -0.50, -0.01, collide=False)
    x0, x1 = ROW_X - HW - 30, ROW_X + (len(ROW) - 1) * W + HW + 30
    # the beach walk: paving from the lane to a low sea wall, sand and sea beyond
    walk = [box("_walk", stage, paving, x0, x1, -HD - 0.3 - LANE_W - 6.0, -HD - 0.3 - LANE_W + 0.02, -0.30, -0.005, collide=False),
            box("_seawall", stage, wall, x0, x1, -HD - 0.3 - LANE_W - 6.4, -HD - 0.3 - LANE_W - 6.0, -0.30, 0.95, collide=False),
            box("_sand", stage, sand, x0, x1, -HD - 60, -HD - 0.3 - LANE_W - 6.3, -1.60, -1.20, collide=False),
            box("_sea", stage, sea, x0 - 100, x1 + 100, -HD - 200, -HD - 40, -1.80, -1.50, collide=False)]
    # the facing row for the lane shot: the same eight turned about, their
    # fronts across the lane
    facing = place_row(stage, parts, x0=ROW_X, y0=-D - 0.6 - LANE_W, turn=math.pi, order=tuple(reversed(ROW)))

    def show(objs, on):
        for o in objs:
            o.hide_render = not on

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.35, -0.75, 0.60)).to_track_quat("Z", "Y").to_euler()
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
        cam.data.clip_end = 600
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"stucco_row: rendered {scene.render.filepath}")

    export_parts = [o for v in VARIANTS for o in parts[v]]
    # the row from the beach walk, her first photo's standpoint: on the walk
    # near the row's west end, looking along the fronts with the sea at right
    show(export_parts, False)
    show(facing, False)
    show(walk, True)
    wx = ROW_X - HW
    shoot("row_from_beach_walk", (wx - 2.5, -HD - 6.0, 1.5), (wx + 11.0, -HD - 1.0, 3.0), lens=22)
    shoot("row_from_beach_walk_far", (wx - 14.0, -HD - 14.0, 1.6), (wx + 24.0, -HD - 1.0, 4.0), lens=28)
    # down the lane, as her inner-lane photo: the facing row across it
    show(walk, False)
    show(facing, True)
    ly = -HD - 0.3 - LANE_W / 2
    shoot("row_down_the_lane", (wx - 1.0, ly - 0.4, 1.5), (wx + 20.0, ly + 1.4, 2.6), lens=26)
    show(facing, False)
    # the row's front elevation
    rx = ROW_X + (len(ROW) - 1) * W / 2
    shoot("row_front_elevation", (rx, -60.0, 4.5), (rx, 0.0, 4.5), ortho=54.0, size=(2400, 900))
    # each variant on its own three-quarter, and the one-storey beside a figure
    bpy.data.collections["authored"].hide_render = True
    for v in VARIANTS:
        show(export_parts, False)
        show(parts[v], True)
        lo, hi = bounds(parts[v])
        h = hi.z
        # an end version is shot from its windowed side
        sx = -1.0 if v.endswith("_end_west") else 1.0
        shoot(f"{v}_three_quarter", (sx * 9.5, -13.5 - h * 0.6, 1.6 + h * 0.12), (0.0, -1.0, h * 0.45), lens=30)
    show(export_parts, False)
    show(parts["one_storey"], True)
    f = figure("_figure", stage, -3.6, -5.6, mat=fig)
    shoot("one_storey_with_figure", (-7.5, -12.0, 1.6), (-0.5, -2.0, 2.0), lens=30)
    bpy.data.objects.remove(f, do_unlink=True)
    show(export_parts, True)
    bpy.data.collections["authored"].hide_render = False


# --- main ----------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != "stucco_row":
        raise SystemExit(f"stucco_row: open stucco_row.blend, not {name}")
    export, authored, reference = (bpy.data.collections[n] for n in ("export", "authored", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"stucco_row: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(VARIANTS + ("demo_row", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    parts = {}
    for v in VARIANTS:
        coll = bpy.data.collections.new(v)
        export.children.link(coll)
        BUILDERS[v](coll)
        parts[v] = [o for o in coll.objects if o.type == "MESH"]
        for o in parts[v]:
            assert str(o.get("kyt_variant")) == v, (o.name, o.get("kyt_variant"))
    row_objs = build_demo_row(authored, parts)
    build_reference(reference)
    # the viewport shows one variant at the origin and the row; the other
    # three stand at the origin too (click their eyes)
    layer = bpy.context.view_layer.layer_collection.children.get("export")
    if layer is not None:
        for v in VARIANTS[1:]:
            child = layer.children.get(v)
            if child is not None:
                child.hide_viewport = True

    print(f"stucco_row: unit {W:.1f} x {D:.1f} m, walls {T:.2f} m thick (party walls {LAP * 100:.0f} cm past the "
          f"pitch line), storeys {S:.1f} m, wings' parapet {PARAPET:.1f} m over the top floor line, bay +{BAY_UP:.1f}, "
          f"crest +{CREST_UP:.1f}; French doors {DOOR_W:.1f} x {DOOR_H:.1f}, sash {SASH_W:.1f} x {SASH_H:.1f} at {SILL:.1f}")
    for v in VARIANTS:
        report(f"{v} (export/{v})", parts[v])
        pairs = coplanar_pairs(parts[v])
        print(f"stucco_row: {v}: {len(pairs)} coplanar overlapping face pairs" +
              ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    report("demo row (authored/demo_row)", row_objs)
    pairs = coplanar_pairs(row_objs)
    print(f"stucco_row: demo row: {len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs[:30])))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("stucco_row: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], parts, row_objs)


main()
