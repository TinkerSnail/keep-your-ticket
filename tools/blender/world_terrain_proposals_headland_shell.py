"""Range north's shell repair: proposals on a SCRATCH COPY of the world terrain master, never on
the master itself (2026-10-09, defects G6, G17 and G5 of the coast/headland ground catalogue,
documentation/screenshots/coast-headland-2026-10-08/catalogue/ground_catalogue.md).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/blender/world_terrain_proposals_headland_shell.py -- --out <folder> [--master <blend>] [--no-render]
    python3 tools/blender/world_terrain_proposals_headland_shell.py --sections <folder>

The Blender run copies the master into `<folder>/PROPOSAL_range_north_shell.blend` (it refuses any
folder under assets/), builds each variant as its own hidden copy of
`background_distant_range_north` in the collection `PROPOSAL_range_north_shell`, measures the
current state and each variant, proves each one can be put in and taken out exactly (the
whole-mesh history `world_terrain_ground_edit.py` keeps for edit 1), renders with scratch cameras
and writes `report.json` and the section segments. The second line draws the sections (PIL).

What range north is at the inlet (Godot x -842..-559, z -741..-562), read from the mesh:
- Its main piece is closed but for two long T-junction cracks (a vertex of one side sits on the
  other side's long edge, which no face shares): x -842..-759 and x -654..-559.
- The pocket beach is a separate 22-face sand sheet with no body: all 24 of its outline's edges
  are open. Its "upper rim" (y -4.8..-4.3) and "lower rim" (-10.9..-10.1) are its own two long
  sides. Its west third lies 0.4-0.9 m under the west lobe's top, its middle spans the inlet over
  nothing, its east end lies on the east lobe.
- The west lobe's shore face is folded under along x -761..-718: its foot (row A, at -11) lies
  41-47 m behind its lip (the toe's -5.08 row), so a slot opens under the lip, seen from the sea,
  over a zero-thickness floor plate at -11 that joins the lobes.
- The fold: four long quads from the toe's top row (y -2) to a row at -6 110 m east are a twisted
  ribbon, the two rows advancing opposite ways, and show their undersides from above.
- Three closed thin slabs (pocket-beach bodies, 158 faces) lie under the apron: G17.

Variants (each also fills both cracks, unfolds the fold, deletes the three slabs and the 21 wire
edges, which carry no faces):
- R1 "close as it lies": the folded shore face is stood up as a vertical wall under its lip (row
  A moved under the lip row, no new faces), and the sand sheet gets a body as it lies: a skirt
  straight down from its outline to a floor at `FLOOR`.
- R2 "close with a shore": row A moved seaward of the lip so the face runs from the lip down to
  -11 at 1:`SHORE_RUN`, the slope the sand sheet has; that face takes the sand, and the separate
  sheet goes.
The west companion's intersection with range north is measured and judged (see `companion`).
"""

import json
import math
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
NAME = "background_distant_range_north"
COMPANION = "background_distant_range_north_west_companion"
COLLECTION = "PROPOSAL_range_north_shell"
SEA = -7.5
FLOOR = -11.25  # the sand body's floor: under its lowest rim (-10.92), clear of the shells' -11 bases
SHORE_RUN = 4.5  # R2: horizontal metres per metre of fall, the sand sheet's own 1:4.3-1:6
# The inlet's rows (vertex indices of the scratch master's mesh, checked against their positions).
ROW_A = [1441, 1443, 1445, 1447, 1449, 1451]  # the folded shore face's foot at -11
LIP = [804, 806, 808, 810, 812, 814]  # its partner on the toe's -5.08 row, by rib edge
FOLD_WEST = [791, 793, 795, 797, 799]  # the toe's top row, one end of the twisted ribbon
FOLD_EAST = [416, 418, 420, 422, 424]  # the -6.0 row, its other end
WINDOW = (-1400.0, 150.0, -1200.0, 50.0)  # the catalogue's window, Godot x0 x1 z0 z1
INLET = (-900.0, -500.0, -780.0, -520.0)
FOLD_BOX = (-760.0, -540.0, -760.0, -600.0)
VIEWS = {
    "V2": ((-520.0, 200.0, -380.0), (-200.0, 0.0, -800.0), 35.0),
    "inlet": ((-700.0, 10.0, -480.0), (-670.0, -5.0, -620.0), 35.0),
}
SECTIONS = {"section_x669": ("x", -669.0, (-760.0, -540.0), (-12.0, 8.0)),
            "section_z640": ("z", -640.0, (-900.0, -520.0), (-12.0, 10.0)),
            "section_x170": ("x", -170.0, (-1000.0, -540.0), (-12.0, 25.0))}


# --- the sections, drawn by system python ----------------------------------------------------------

def draw_sections(folder):
    from PIL import Image, ImageDraw, ImageFont
    data = json.load(open(os.path.join(folder, "sections.json")))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except Exception:
        font = small = ImageFont.load_default()
    for variant in [v for v in data if v != "current"]:
        for key, (axis, value, (s0, s1), (y0, y1)) in SECTIONS.items():
            W, H, mx, my = 1600, 640, 70, 60
            img = Image.new("RGB", (W, H), (250, 250, 248))
            dr = ImageDraw.Draw(img)
            sx = lambda s: mx + (s - s0) / (s1 - s0) * (W - 2 * mx)
            sy = lambda y: H - my - (y - y0) / (y1 - y0) * (H - 2 * my)
            for yy in range(int(math.ceil(y0)), int(y1) + 1, 1 if y1 - y0 <= 25 else 5):
                dr.line([(mx, sy(yy)), (W - mx, sy(yy))], fill=(230, 230, 230))
                dr.text((8, sy(yy) - 8), "%d" % yy, fill=(120, 120, 120), font=small)
            step = 10 if s1 - s0 <= 400 else 50
            for ss in range(int(math.ceil(s0 / step) * step), int(s1) + 1, step):
                dr.line([(sx(ss), my), (sx(ss), H - my)], fill=(238, 238, 238))
                dr.text((sx(ss) - 16, H - my + 6), "%d" % ss, fill=(120, 120, 120), font=small)
            dr.line([(mx, sy(SEA)), (W - mx, sy(SEA))], fill=(60, 140, 230), width=2)
            dr.text((W - mx - 110, sy(SEA) + 4), "sea -7.5", fill=(60, 140, 230), font=small)
            # the other ground, thin grey; range north today, grey; the variant, coloured by facing
            for seg in data["current"][key]["other"]:
                dr.line([(sx(seg[0]), sy(seg[1])), (sx(seg[2]), sy(seg[3]))], fill=(185, 185, 185), width=2)
            for seg in data["current"][key]["rn"]:
                dr.line([(sx(seg[0]), sy(seg[1])), (sx(seg[2]), sy(seg[3]))], fill=(150, 150, 150), width=5)
            for seg in data[variant][key]["rn"]:
                col = (30, 120, 40) if seg[4] > 0.2 else ((210, 0, 160) if seg[4] < -0.2 else (40, 40, 40))
                if seg[5]:
                    col = (230, 120, 0)
                dr.line([(sx(seg[0]), sy(seg[1])), (sx(seg[2]), sy(seg[3]))], fill=col, width=2)
            along = "z, north left" if axis == "x" else "x, west left"
            dr.text((mx, 12), "%s %s: %s = %g (%s). Thick grey: range north today; thin: %s, green faces up, magenta down, "
                              "dark walls, orange changed or added" % ("range_north_shell", variant, axis, value, along, variant),
                    fill=(0, 0, 0), font=font)
            dr.text((mx, 36), "light grey: the other Ground objects", fill=(110, 110, 110), font=small)
            img.save(os.path.join(folder, "range_north_shell_%s_%s.png" % (variant, key)))
    # the current state alone
    for key, (axis, value, (s0, s1), (y0, y1)) in SECTIONS.items():
        W, H, mx, my = 1600, 640, 70, 60
        img = Image.new("RGB", (W, H), (250, 250, 248))
        dr = ImageDraw.Draw(img)
        sx = lambda s: mx + (s - s0) / (s1 - s0) * (W - 2 * mx)
        sy = lambda y: H - my - (y - y0) / (y1 - y0) * (H - 2 * my)
        for yy in range(int(math.ceil(y0)), int(y1) + 1, 1 if y1 - y0 <= 25 else 5):
            dr.line([(mx, sy(yy)), (W - mx, sy(yy))], fill=(230, 230, 230))
            dr.text((8, sy(yy) - 8), "%d" % yy, fill=(120, 120, 120), font=small)
        step = 10 if s1 - s0 <= 400 else 50
        for ss in range(int(math.ceil(s0 / step) * step), int(s1) + 1, step):
            dr.line([(sx(ss), my), (sx(ss), H - my)], fill=(238, 238, 238))
            dr.text((sx(ss) - 16, H - my + 6), "%d" % ss, fill=(120, 120, 120), font=small)
        dr.line([(mx, sy(SEA)), (W - mx, sy(SEA))], fill=(60, 140, 230), width=2)
        for seg in data["current"][key]["other"]:
            dr.line([(sx(seg[0]), sy(seg[1])), (sx(seg[2]), sy(seg[3]))], fill=(185, 185, 185), width=2)
        for seg in data["current"][key]["rn"]:
            col = (30, 120, 40) if seg[4] > 0.2 else ((210, 0, 160) if seg[4] < -0.2 else (40, 40, 40))
            if seg[6] == 4:
                col = (200, 160, 20)
            elif seg[6] in (1, 2, 3):
                col = (220, 40, 40)
            dr.line([(sx(seg[0]), sy(seg[1])), (sx(seg[2]), sy(seg[3]))], fill=col, width=3)
        along = "z, north left" if axis == "x" else "x, west left"
        dr.text((mx, 12), "range_north_shell today: %s = %g (%s). Green faces up, magenta down, dark walls; gold the loose sand "
                          "sheet, red the internal slabs" % (axis, value, along), fill=(0, 0, 0), font=font)
        dr.text((mx, 36), "light grey: the other Ground objects", fill=(110, 110, 110), font=small)
        img.save(os.path.join(folder, "range_north_shell_current_%s.png" % key))
    print("sections drawn")


if __name__ == "__main__" and "--sections" in sys.argv:
    draw_sections(os.path.abspath(sys.argv[sys.argv.index("--sections") + 1]))
    sys.exit(0)


import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

DEFAULT_MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")


def log(folder, msg):
    print("headland_shell: " + msg, flush=True)
    with open(os.path.join(folder, "progress.md"), "a") as f:
        f.write("- (script) %s\n" % msg)


def B(x, y, z):
    """Godot (x, y, z) to Blender."""
    return Vector((x, -z, y))


# --- the mesh -------------------------------------------------------------------------------------

def pieces_of(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f in seen:
            continue
        seen.add(f)
        stack, piece = [f], []
        while stack:
            g = stack.pop()
            piece.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen:
                        seen.add(h)
                        stack.append(h)
        out.append(piece)
    out.sort(key=len, reverse=True)
    return out


def topology(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    r = {"vertices": len(bm.verts), "faces": len(bm.faces),
         "open_edges": sum(1 for e in bm.edges if len(e.link_faces) == 1),
         "nonmanifold_edges": sum(1 for e in bm.edges if len(e.link_faces) > 2),
         "wire_edges": sum(1 for e in bm.edges if not e.link_faces),
         "edges_wound_against": sum(1 for e in bm.edges if len(e.link_faces) == 2 and not e.is_contiguous),
         "nonmanifold_vertices": sum(1 for v in bm.verts if v.link_faces and not v.is_manifold),
         "pieces": [len(p) for p in pieces_of(bm)]}
    bm.free()
    me.calc_loop_triangles()
    r["triangles"] = len(me.loop_triangles)
    r["closed"] = r["open_edges"] == 0 and r["nonmanifold_edges"] == 0 and r["wire_edges"] == 0
    return r


def grid(box, step):
    x0, x1, z0, z1 = box
    return np.arange(x0 + step / 2, x1, step), np.arange(z0 + step / 2, z1, step)


def all_hits(tree, x, z, start=5000.0, skip=1e-4):
    """Every surface straight down at Godot (x, z): (y, normal y, face), as the catalogue read them
    (each next cast starts `skip` under the last hit, so two coincident faces count once)."""
    out, y = [], start
    while True:
        h = tree.ray_cast(B(x, y, z), Vector((0.0, 0.0, -1.0)))
        if h[0] is None:
            return out
        out.append((h[0].z, h[1].z, h[2]))
        y = h[0].z - skip


def faces_seen(ob, box, step, sea=SEA):
    """Down-facing tops above water, the catalogue's measure: area by face, and where a ray enters
    the shell and never leaves (its last surface faces up)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    xs, zs = grid(box, step)
    down, never = {}, 0
    cell = step * step
    for x in xs:
        for z in zs:
            hits = all_hits(tree, x, z)
            if not hits:
                continue
            if hits[0][0] > sea and hits[0][1] <= 0.0:
                down[hits[0][2]] = down.get(hits[0][2], 0.0) + cell
            if hits[-1][1] > 0.0:
                never += 1
    return {"down_top_above_sea_m2": round(sum(down.values()), 1), "down_top_faces": {int(k): round(v, 1) for k, v in down.items()},
            "enter_never_leave_m2": round(never * cell, 1), "step_m": step}


def tag_original(me):
    """Each vertex's own index as an attribute, so a variant can be compared vertex by vertex."""
    a = me.attributes.get("kyt_orig") or me.attributes.new("kyt_orig", 'INT', 'POINT')
    a.data.foreach_set("value", np.arange(len(me.vertices), dtype=np.int32))


def copy_object(src, name, coll):
    me = src.data.copy()
    me.name = name
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.hide_render = True
    ob.hide_set(True)
    ob["kyt_proposal"] = "range_north_shell"
    return ob


def fingerprint(me):
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    faces = tuple((tuple(p.vertices), p.material_index, p.use_smooth) for p in me.polygons)
    return (co.tobytes(), faces, tuple(m.name if m else None for m in me.materials))


# --- the repairs ----------------------------------------------------------------------------------

def check_rows(V):
    """V: original index -> BMVert. The rows must stand where the scratch master has them."""
    for a, l in zip(ROW_A, LIP):
        va, vl = V[a], V[l]
        if abs(va.co.z + 11.0) > 1e-3 or abs(vl.co.z + 5.08) > 1e-2:
            raise SystemExit("row A / lip vertices are not where the scratch master had them (%d %s, %d %s)" % (a, va.co, l, vl.co))
        if not any(e.other_vert(va) is vl for e in va.link_edges):
            raise SystemExit("vertex %d has no rib edge to %d" % (a, l))


def fill_cracks(bm, changed):
    """The two T-junction cracks: each a loop of three open edges, filled with one triangle wound
    as its neighbours are."""
    made = []
    open_edges = {e for e in bm.edges if len(e.link_faces) == 1}
    loops = []
    while open_edges:
        e = open_edges.pop()
        loop = [e]
        grew = True
        while grew:
            grew = False
            ends = {v for x in loop for v in x.verts}
            for o in list(open_edges):
                if any(v in ends for v in o.verts):
                    loop.append(o)
                    open_edges.discard(o)
                    grew = True
        loops.append(loop)
    for loop in loops:
        if len(loop) != 3:
            continue
        vs = list({v for e in loop for v in e.verts})
        if len(vs) != 3:
            continue
        f = bm.faces.new(vs)
        f.material_index = loop[0].link_faces[0].material_index
        f.normal_update()
        if not all(e.is_contiguous for e in f.edges):
            f.normal_flip()
        if not all(e.is_contiguous for e in f.edges):
            raise SystemExit("a crack's triangle cannot be wound with its neighbours")
        changed.add(f)
        made.append({"area_m2": round(f.calc_area(), 3), "longest_m": round(max(e.calc_length() for e in f.edges), 1),
                     "at": [round(c, 1) for c in f.calc_center_median()]})
    return made


def delete_slabs_and_sand(bm, keep_sand):
    """Pieces 2.. of the shell: the three closed thin slabs (G17) and, unless kept, the loose sand
    sheet. Returns what went, per piece."""
    gone = []
    for piece in pieces_of(bm)[1:]:
        open_n = sum(1 for f in piece for e in f.edges if len(e.link_faces) == 1)
        is_sand = open_n > 0
        if is_sand and keep_sand:
            continue
        co = np.array([v.co[:] for f in piece for v in f.verts])
        gone.append({"faces": len(piece), "open_edges": open_n, "sand_sheet": is_sand,
                     "x": [round(co[:, 0].min(), 1), round(co[:, 0].max(), 1)],
                     "z_godot": [round(-co[:, 1].max(), 1), round(-co[:, 1].min(), 1)],
                     "y_godot": [round(co[:, 2].min(), 2), round(co[:, 2].max(), 2)],
                     "area_m2": round(sum(f.calc_area() for f in piece), 1)})
        bmesh.ops.delete(bm, geom=piece, context='FACES')
    return gone


def sand_body(bm, changed, lay, slope):
    """The loose sand sheet gets a body as it lies: a skirt from every open edge of its outline down
    to `FLOOR`, and a floor there. Its top does not move. R1 (`slope` False): the skirt hangs
    straight down. R2: where the outline is exposed (nothing of range north over it) the skirt runs
    out from it at 1:SHORE_RUN, a shore face instead of a wall; where it lies under the lobe it
    stays straight."""
    sand = [p for p in pieces_of(bm)[1:] if any(len(e.link_faces) == 1 for f in p for e in f.edges)]
    if len(sand) != 1:
        raise SystemExit("expected one open piece (the sand sheet), found %d" % len(sand))
    piece = sand[0]
    mat = piece[0].material_index
    rim = [e for f in piece for e in f.edges if len(e.link_faces) == 1]
    # the outline as one loop, in the order its own faces wind it
    nxt = {}
    for e in rim:
        f = e.link_faces[0]
        for lp in f.loops:
            if lp.edge is e:
                nxt[lp.vert] = lp.link_loop_next.vert
    start = next(iter(nxt))
    loop, v = [start], nxt[start]
    while v is not start:
        loop.append(v)
        v = nxt[v]
    if len(loop) != len(rim):
        raise SystemExit("the sand sheet's outline is not one loop")
    sloped = 0
    offsets = {}
    if slope:
        others = [f for f in bm.faces if f not in set(piece)]
        tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in others]) if False else None
        bm.verts.index_update()
        verts = [v.co.copy() for v in bm.verts]
        tree = BVHTree.FromPolygons(verts, [[v.index for v in f.verts] for f in others])
        n = len(loop)
        for i, v in enumerate(loop):
            a, b = loop[i - 1].co, loop[(i + 1) % n].co
            d = Vector((b.x - a.x, b.y - a.y))
            d.normalize()
            out = Vector((d.y, -d.x))  # the sheet winds its outline anticlockwise from above: out is to the right
            over = tree.ray_cast(Vector((v.co.x, v.co.y, v.co.z + 0.05)), Vector((0.0, 0.0, 1.0)))[0] is not None
            if over:
                continue
            offsets[v] = out * ((v.co.z - FLOOR) * SHORE_RUN)
        # the floor's outline must not cross itself: shorten the runs until it does not
        def crossing(pts):
            m = len(pts)
            def cr(p, q, r):
                return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
            for i in range(m):
                p, q = pts[i], pts[(i + 1) % m]
                for j in range(i + 2, m):
                    if (j + 1) % m == i:
                        continue
                    r, t = pts[j], pts[(j + 1) % m]
                    if cr(p, q, r) * cr(p, q, t) < 0 and cr(r, t, p) * cr(r, t, q) < 0:
                        return True
            return False
        k = 1.0
        while k > 0.0:
            pts = [(v.co.x + offsets.get(v, Vector((0, 0))).x * k, v.co.y + offsets.get(v, Vector((0, 0))).y * k) for v in loop]
            if not crossing(pts):
                break
            k -= 0.05
        offsets = {v: o * k for v, o in offsets.items()}
        sloped = len(offsets)
    low = {}
    for v in loop:
        o = offsets.get(v, Vector((0.0, 0.0)))
        low[v] = bm.verts.new(Vector((v.co.x + o.x, v.co.y + o.y, FLOOR)))
    for nv in low.values():
        nv[lay] = -1
    n = len(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        # the sheet winds a->b; the skirt below shares that edge, so it winds b->a
        f = bm.faces.new([b, a, low[a], low[b]])
        f.material_index = mat
        changed.add(f)
    floor = bm.faces.new([low[v] for v in reversed(loop)])
    floor.material_index = mat
    changed.add(floor)
    res = bmesh.ops.triangulate(bm, faces=[floor])
    for f in res["faces"]:
        changed.add(f)
    bm.normal_update()
    for f in list(changed):
        if f.is_valid and not all(e.is_contiguous for e in f.edges if len(e.link_faces) == 2):
            raise SystemExit("the sand body's faces wind against their neighbours")
    return {"skirt_faces": n, "floor_faces": len(res["faces"]), "new_vertices": n, "floor_y": FLOOR,
            "outline_vertices_sloped": sloped, "slope_run": SHORE_RUN if slope else 0.0,
            "longest_run_m": round(max((o.length for o in offsets.values()), default=0.0), 1)}


def plan_area(f):
    p = [Vector((v.co.x, v.co.y)) for v in f.verts]
    return sum(p[i].x * p[(i + 1) % len(p)].y - p[(i + 1) % len(p)].x * p[i].y for i in range(len(p))) / 2.0


def unfold_shore(bm, V, mode, changed, moved):
    """Row A, the folded shore face's foot, set out from its lip: `vertical` straight under it (R1),
    `shore` seaward of it at 1:SHORE_RUN (R2). Seaward is square to the lip row, away from the
    lobe. The feet carry the floor plate at -11 (an up-facing layer and a down-facing one on the
    same plane, in long needle triangles out to row B). A foot whose move would turn any face it
    holds over in plan (but the folded quads themselves) is moved less: the feet are walked out
    together, the middle ones first, as far as that allows."""
    lip = [V[i] for i in LIP]
    feet = [V[i] for i in ROW_A]
    fs, lips = set(feet), set(lip)
    targets = []
    for k, (va, vl) in enumerate(zip(feet, lip)):
        a = lip[max(k - 1, 0)].co
        b = lip[min(k + 1, len(lip) - 1)].co
        d = Vector((b.x - a.x, b.y - a.y))
        d.normalize()
        # Blender plan: x east, y north; the lobe lies to the left of the lip row (it runs east
        # then north), the sea to its right
        n = Vector((d.y, -d.x))
        if mode == "vertical":
            targets.append(Vector((vl.co.x, vl.co.y, -11.0)))
        else:
            run = (vl.co.z + 11.0) * SHORE_RUN
            targets.append(Vector((vl.co.x + n.x * run, vl.co.y + n.y * run, -11.0)))
    old = [v.co.copy() for v in feet]
    plate = {f for v in feet for f in v.link_faces if max(u.co.z for u in f.verts) - min(u.co.z for u in f.verts) < 1e-3}
    rib = {f for v in feet for f in v.link_faces if sum(u in fs for u in f.verts) == 2 and sum(u in lips for u in f.verts) == 2}
    slopes = [(f, plan_area(f) > 0) for v in feet for f in v.link_faces if f not in rib and abs(plan_area(f)) > 1e-6]

    def flips():
        return sum(1 for f, was in slopes if abs(plan_area(f)) > 1e-6 and (plan_area(f) > 0) != was)
    share = [0.0] * len(feet)
    for _ in range(12):
        for k in sorted(range(len(feet)), key=lambda k: abs(k - (len(feet) - 1) / 2.0)):
            best = share[k]
            t = 1.0
            while t > share[k] + 1e-9:
                feet[k].co = old[k].lerp(targets[k], t)
                if flips() == 0:
                    best = t
                    break
                t -= 0.05
            share[k] = best
            feet[k].co = old[k].lerp(targets[k], best)
    relaid = {"note": "not laid again: the plate's needle triangles limit the feet (share_of_move)"}
    bm.normal_update()
    out = []
    for k, (va, vl) in enumerate(zip(feet, lip)):
        moved[va] = (old[k], va.co.copy())
        for f in va.link_faces:
            changed.add(f)
        out.append({"vertex": ROW_A[k], "from_godot": [round(old[k].x, 2), round(old[k].z, 2), round(-old[k].y, 2)],
                    "to_godot": [round(va.co.x, 2), round(va.co.z, 2), round(-va.co.y, 2)],
                    "moved_m": round((va.co - old[k]).length, 2), "share_of_move": round(share[k], 2),
                    "lip_godot": [round(vl.co.x, 2), round(vl.co.z, 2), round(-vl.co.y, 2)],
                    "lip_to_foot_m": round(Vector((va.co.x - vl.co.x, va.co.y - vl.co.y)).length, 2)})
    out.append({"plate_relaid": relaid})
    return out


def seen_down(bm, box, step):
    tree = BVHTree.FromBMesh(bm)
    xs, zs = grid(box, step)
    area = 0.0
    for x in xs:
        for z in zs:
            h = tree.ray_cast(B(x, 500.0, z), Vector((0.0, 0.0, -1.0)))
            if h[0] is not None and h[0].z > SEA and h[1].z <= 0.0:
                area += step * step
    return area


def unfold_fold(bm, V, changed, moved):
    """The fold: the toe's top row and the -6 row 110 m east advance opposite ways, so the four
    quads between them are a twisted ribbon showing its underside. The top row's last four
    vertices are walked north, each a step more than the last, until no face shows its underside
    from above; then anything still showing is lowered in 0.1 m steps (its own vertices only)."""
    west = [V[i] for i in FOLD_WEST]
    start = [v.co.copy() for v in west]
    bm.faces.index_update()
    bm.faces.ensure_lookup_table()
    before = seen_down(bm, FOLD_BOX, 0.5)
    best = None
    for s in list(np.arange(0.0, 3.01, 0.5)) + list(np.arange(3.1, 6.01, 0.1)):
        for k, v in enumerate(west):
            v.co = start[k] + Vector((0.0, s * k, 0.0))  # Blender +y is north
        bm.normal_update()
        a = seen_down(bm, FOLD_BOX, 0.5)
        if best is None or a < best[1] - 1e-6:
            best = (s, a)
        if a == 0.0:
            break
    s = best[0]
    for k, v in enumerate(west):
        v.co = start[k] + Vector((0.0, s * k, 0.0))
        if (v.co - start[k]).length > 0:
            moved[v] = (start[k], v.co.copy())
            for f in v.link_faces:
                changed.add(f)
    bm.normal_update()
    lowered = []
    tree = BVHTree.FromBMesh(bm)
    for _ in range(30):
        xs, zs = grid(FOLD_BOX, 0.25)
        show = set()
        tree = BVHTree.FromBMesh(bm)
        for x in xs:
            for z in zs:
                h = tree.ray_cast(B(x, 500.0, z), Vector((0.0, 0.0, -1.0)))
                if h[0] is not None and h[0].z > SEA and h[1].z <= 0.0:
                    show.add(h[2])
        if not show:
            break
        bm.faces.ensure_lookup_table()
        for fi in show:
            f = bm.faces[fi]
            top = max(f.verts, key=lambda v: v.co.z)
            if top not in moved:
                moved[top] = (top.co.copy(), None)
            top.co.z -= 0.1
            for g in top.link_faces:
                changed.add(g)
            lowered.append(top)
        bm.normal_update()
    for v, (old, _) in list(moved.items()):
        moved[v] = (old, v.co.copy())
    after = seen_down(bm, FOLD_BOX, 0.25)
    return {"north_step_m": float(s), "top_row_moved_m": [round(s * k, 2) for k in range(len(west))],
            "seen_down_before_m2_at_0.5m": before, "seen_down_after_m2_at_0.25m": after,
            "lowered_vertices": len(set(lowered)), "lowered_steps": len(lowered)}


def build(src, coll, variant):
    ob = copy_object(src, "%s_%s" % (COLLECTION, variant), coll)
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.verts.layers.int["kyt_orig"]
    V = {v[lay]: v for v in bm.verts}
    check_rows(V)
    changed, moved = set(), {}
    report = {}
    wires = [e for e in bm.edges if not e.link_faces]
    report["wire_edges_deleted"] = len(wires)
    nv0 = len(bm.verts)
    bmesh.ops.delete(bm, geom=wires, context='EDGES')
    if len(bm.verts) != nv0:
        raise SystemExit("deleting the wire edges took vertices with them")
    report["cracks"] = fill_cracks(bm, changed)
    report["fold"] = unfold_fold(bm, V, changed, moved)
    if False:
        # the unfolded shore face takes the sand from the sheet it replaces
        sand_mat = next(i for i, m in enumerate(me.materials) if m and m.name.startswith("distant_range_cove_sand"))
        feet = {V[i] for i in ROW_A}
        lips = {V[i] for i in LIP}
        shore = [f for f in bm.faces if len(f.verts) == 4 and sum(v in feet for v in f.verts) == 2 and sum(v in lips for v in f.verts) == 2]
        for f in shore:
            f.material_index = sand_mat
            changed.add(f)
        report["shore_faces_to_sand"] = len(shore)
    report["deleted_pieces"] = delete_slabs_and_sand(bm, keep_sand=True)
    report["sand_body"] = sand_body(bm, changed, lay, slope=(variant == "R2"))
    bm.normal_update()
    # the faces this variant made or reshaped, marked for review
    fl = bm.faces.layers.int.get("kyt_proposal_changed") or bm.faces.layers.int.new("kyt_proposal_changed")
    for f in bm.faces:
        f[fl] = 1 if (f in changed or any(v in moved for v in f.verts)) else 0
    report["moved_vertices"] = {int(v[lay]): round((b - a).length, 3) for v, (a, b) in moved.items() if v.is_valid}
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob, report


# --- proofs ---------------------------------------------------------------------------------------

def compare(src_me, var_me):
    """Every vertex the variant kept, against the scratch master's (new vertices carry -1)."""
    n0 = len(src_me.vertices)
    c0 = np.zeros(n0 * 3)
    src_me.vertices.foreach_get("co", c0)
    c0 = c0.reshape(-1, 3)
    n1 = len(var_me.vertices)
    c1 = np.zeros(n1 * 3)
    var_me.vertices.foreach_get("co", c1)
    c1 = c1.reshape(-1, 3)
    orig = np.zeros(n1, dtype=np.int64)
    var_me.attributes["kyt_orig"].data.foreach_get("value", orig)
    chg = np.zeros(len(var_me.polygons), dtype=np.int32)
    var_me.attributes["kyt_proposal_changed"].data.foreach_get("value", chg)
    in_changed = set()
    for p in var_me.polygons:
        if chg[p.index]:
            in_changed.update(p.vertices)
    new = orig < 0
    kept = np.nonzero(~new)[0]
    same = np.all(c1[kept] == c0[orig[kept]], axis=1)
    moved = kept[~same]
    outside = [i for i in kept if i not in in_changed]
    identical = int(sum(1 for i in outside if np.array_equal(c1[i], c0[orig[i]])))
    return {"vertices_before": n0, "vertices_after": n1, "new_vertices": int(new.sum()),
            "deleted_vertices": int(n0 - len(set(orig[kept].tolist()))),
            "vertices_outside_changed_faces": len(outside), "of_them_identical": identical,
            "moved_vertices": int(len(moved)), "moved_all_in_changed_faces": bool(all(i in in_changed for i in moved)),
            "max_move_m": round(float(max((np.linalg.norm(c1[i] - c0[orig[i]]) for i in moved), default=0.0)), 3)}


def undo_proof(src, var):
    """The variant put in as an edit and taken out, as `world_terrain_ground_edit.py` keeps edit 1:
    the object's mesh kept whole in a hidden history object (`kyt_whole`), swapped back on undo."""
    me0 = src.data.copy()
    probe = bpy.data.objects.new("scratch_undo_probe", me0)
    before = fingerprint(probe.data)
    hist = bpy.data.objects.new("scratch_undo_probe__before_edit", probe.data.copy())
    hist["kyt_whole"] = True
    old = probe.data
    probe.data = var.data.copy()
    applied = fingerprint(probe.data) != before
    # undo, exactly as ground_edit's undo does for a kept-whole history
    cur = probe.data
    probe.data = hist.data
    bpy.data.objects.remove(hist)
    bpy.data.meshes.remove(cur)
    after = fingerprint(probe.data)
    ok = after == before
    m = probe.data
    bpy.data.objects.remove(probe)
    for mm in (m, old):
        if mm.users == 0:
            bpy.data.meshes.remove(mm)
    return {"applied_differs": applied, "undo_restores_exactly": ok}


def section_segments(objs, axis, value, srange, rn, piece_of=None, changed=None):
    """Where the vertical plane cuts the triangles: (s0, y0, s1, y1, normal y, changed, piece)."""
    out_rn, out_other = [], []
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        n = len(me.vertices)
        co = np.zeros(n * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        G = np.column_stack([co[:, 0], co[:, 2], -co[:, 1]])
        nt = len(me.loop_triangles)
        tv = np.zeros(nt * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", tv)
        tv = tv.reshape(-1, 3)
        tp = np.zeros(nt, dtype=np.int64)
        me.loop_triangles.foreach_get("polygon_index", tp)
        chg = None
        if ob is rn and "kyt_proposal_changed" in me.attributes:
            chg = np.zeros(len(me.polygons), dtype=np.int32)
            me.attributes["kyt_proposal_changed"].data.foreach_get("value", chg)
        P = G[tv]
        a = 0 if axis == "x" else 2
        b = 2 if axis == "x" else 0
        d = P[:, :, a] - value
        sel = np.nonzero((d.min(1) < 0) & (d.max(1) > 0) & (P[:, :, b].max(1) >= srange[0]) & (P[:, :, b].min(1) <= srange[1]))[0]
        nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)[:, None]
        for k in sel:
            pts = []
            for i, j in ((0, 1), (1, 2), (2, 0)):
                di, dj = d[k, i], d[k, j]
                if (di < 0) != (dj < 0):
                    t = di / (di - dj)
                    p = P[k, i] + t * (P[k, j] - P[k, i])
                    pts.append((float(p[b]), float(p[1])))
            if len(pts) != 2:
                continue
            if ob is rn:
                pc = piece_of.get(int(tp[k]), 0) if piece_of else 0
                out_rn.append([pts[0][0], pts[0][1], pts[1][0], pts[1][1], float(nrm[k, 1]),
                               int(chg[tp[k]]) if chg is not None else 0, pc])
            else:
                out_other.append([pts[0][0], pts[0][1], pts[1][0], pts[1][1]])
    return {"rn": out_rn, "other": out_other}


def topmost_map(objs, box, step):
    """The topmost Ground over a plan box: heights (nan where none) and which object."""
    trees = []
    for k, ob in enumerate(objs):
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        if max(b.x for b in bb) < box[0] or min(b.x for b in bb) > box[1] or max(-b.y for b in bb) < box[2] or min(-b.y for b in bb) > box[3]:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        trees.append((k, BVHTree.FromBMesh(bm)))
        bm.free()
    xs, zs = grid(box, step)
    H = np.full((len(zs), len(xs)), np.nan)
    W = np.full((len(zs), len(xs)), -1, dtype=np.int32)
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            for k, t in trees:
                h = t.ray_cast(B(x, 5000.0, z), Vector((0.0, 0.0, -1.0)))
                if h[0] is not None and (np.isnan(H[j, i]) or h[0].z > H[j, i]):
                    H[j, i] = h[0].z
                    W[j, i] = k
    return xs, zs, H, W


def contour(xs, zs, H, level):
    """Marching squares on a height map (nan = no ground = deep water): Godot (x, z) segments."""
    F = np.where(np.isnan(H), -100.0, H)
    segs = []
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            v = [F[j, i], F[j, i + 1], F[j + 1, i + 1], F[j + 1, i]]
            c = [(xs[i], zs[j]), (xs[i + 1], zs[j]), (xs[i + 1], zs[j + 1]), (xs[i], zs[j + 1])]
            pts = []
            for k in range(4):
                a, b = v[k], v[(k + 1) % 4]
                if (a >= level) != (b >= level):
                    t = (level - a) / (b - a)
                    pts.append((c[k][0] + t * (c[(k + 1) % 4][0] - c[k][0]), c[k][1] + t * (c[(k + 1) % 4][1] - c[k][1])))
            if len(pts) == 2:
                segs.append(pts)
            elif len(pts) == 4:
                segs += [pts[:2], pts[2:]]
    return segs


def waterline_shift(segs_a, segs_b):
    """How far each of B's waterline points lies from A's line: the largest and where."""
    if not segs_a or not segs_b:
        return None
    A = np.array([p for s in segs_a for p in s])
    best = (0.0, None)
    for s in segs_b:
        for p in s:
            d = np.min(np.hypot(A[:, 0] - p[0], A[:, 1] - p[1]))
            if d > best[0]:
                best = (float(d), [round(p[0], 1), round(p[1], 1)])
    Bp = np.array([p for s in segs_b for p in s])
    best_a = (0.0, None)
    for p in A:
        d = np.min(np.hypot(Bp[:, 0] - p[0], Bp[:, 1] - p[1]))
        if d > best_a[0]:
            best_a = (float(d), [round(p[0], 1), round(p[1], 1)])
    return {"proposed_off_current_max_m": round(best[0], 1), "at": best[1],
            "current_off_proposed_max_m": round(best_a[0], 1), "at_current": best_a[1]}


def companion(rn, comp):
    """G5: where range north and its west companion cross. Each object's top over the other's
    footprint, which one stands over the other where, and where their crossing runs."""
    box = (-1100.0, -960.0, -1060.0, -850.0)
    xs, zs = grid(box, 2.0)
    trees = []
    for ob in (rn, comp):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        trees.append(BVHTree.FromBMesh(bm))
        bm.free()
    both = rn_top = comp_top = 0
    rn_over, comp_over, comp_buried_x = [], [], []
    comp_tops = []
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            hs = []
            for t in trees:
                h = t.ray_cast(B(x, 5000.0, z), Vector((0.0, 0.0, -1.0)))
                hs.append(h[0].z if h[0] is not None else None)
            if hs[0] is None or hs[1] is None or max(hs) <= SEA:
                continue
            both += 1
            if hs[0] > hs[1]:
                rn_top += 1
                rn_over.append(hs[0] - hs[1])
                comp_buried_x.append(x)
            else:
                comp_top += 1
                comp_over.append(hs[1] - hs[0])
            comp_tops.append(hs[1])
    # the companion's own footprint: where along x it ends
    cbm = bmesh.new()
    cbm.from_mesh(comp.data)
    cx = [v.co.x for v in cbm.verts]
    near_sea = sum(1 for v in cbm.verts if v.co.x > -1060 and abs(v.co.z + 11.0) < 0.6)
    cbm.free()
    return {"box": box, "cells_2m_both_above_sea": both, "rn_on_top_m2": rn_top * 4, "companion_on_top_m2": comp_top * 4,
            "rn_over_companion_max_m": round(max(rn_over), 2) if rn_over else 0.0,
            "rn_over_companion_median_m": round(float(np.median(rn_over)), 2) if rn_over else 0.0,
            "companion_over_rn_max_m": round(max(comp_over), 2) if comp_over else 0.0,
            "where_rn_is_on_top_x": [round(min(comp_buried_x), 1), round(max(comp_buried_x), 1)] if comp_buried_x else None,
            "companion_east_end_x": round(max(cx), 1), "companion_west_end_x": round(min(cx), 1),
            "companion_vertices_at_its_base_east_of_-1060": near_sea}


# --- rendering (the seabed proposals' look: tools/blender/world_terrain_proposals_seabed.py) -----

SHALLOW = (0.30, 0.50, 0.52)
DEEP = (0.34, 0.44, 0.52)
REACH = 12.0
CLARITY = 3.0
SURFACE = 0.25
DEEPER = (0.17, 0.27, 0.38)
DEEPER_FROM = 30.0
DEEPER_REACH = 80.0
WATER_GAIN = (2.65, 2.5, 2.25)


def srgb_to_linear(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def render_group():
    """The seabed renders' water over each ground material: see-through over CLARITY m along the
    view, its colour by depth straight down over REACH, the deep step past DEEPER_FROM."""
    ng = bpy.data.node_groups.new("KYT_shell_render", "ShaderNodeTree")
    ng.interface.new_socket("Bed", in_out="INPUT", socket_type="NodeSocketShader")
    ng.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    N, Lk = ng.nodes, ng.links
    gin = N.new("NodeGroupInput")
    gout = N.new("NodeGroupOutput")
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Position"], sep.inputs[0])

    def op(kind, a=None, b=None, va=None, vb=None):
        m = N.new("ShaderNodeMath")
        m.operation = kind
        if a is not None:
            Lk.new(a, m.inputs[0])
        elif va is not None:
            m.inputs[0].default_value = va
        if b is not None:
            Lk.new(b, m.inputs[1])
        elif vb is not None:
            m.inputs[1].default_value = vb
        return m.outputs[0]

    depth = op("SUBTRACT", va=SEA, b=sep.outputs["Z"])
    under = op("GREATER_THAN", a=depth, vb=0.0)
    dpos = op("MAXIMUM", a=depth, vb=0.0)
    isep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Incoming"], isep.inputs[0])
    cosv = op("MAXIMUM", a=op("ABSOLUTE", a=isep.outputs["Z"]), vb=0.05)
    through = op("DIVIDE", a=dpos, b=cosv)
    cover = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=through, vb=-CLARITY)))
    alpha = N.new("ShaderNodeMix")
    alpha.data_type = "FLOAT"
    alpha.inputs[2].default_value = SURFACE
    alpha.inputs[3].default_value = 1.0
    Lk.new(cover, alpha.inputs[0])
    afac = op("MULTIPLY", a=alpha.outputs[0], b=under)
    rf = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=dpos, vb=-REACH)))
    tint = N.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    gain = np.array(WATER_GAIN)
    tint.inputs[6].default_value = (*(srgb_to_linear(SHALLOW) * gain), 1.0)
    tint.inputs[7].default_value = (*(srgb_to_linear(DEEP) * gain), 1.0)
    Lk.new(rf, tint.inputs[0])
    r2 = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=op("MAXIMUM", a=op("SUBTRACT", a=dpos, vb=DEEPER_FROM), vb=0.0),
                                                             vb=-DEEPER_REACH)))
    tint2 = N.new("ShaderNodeMix")
    tint2.data_type = "RGBA"
    Lk.new(r2, tint2.inputs[0])
    Lk.new(tint.outputs[2], tint2.inputs[6])
    tint2.inputs[7].default_value = (*(srgb_to_linear(DEEPER) * gain), 1.0)
    wem = N.new("ShaderNodeEmission")
    Lk.new(tint2.outputs[2], wem.inputs["Color"])
    mix = N.new("ShaderNodeMixShader")
    Lk.new(afac, mix.inputs[0])
    Lk.new(gin.outputs["Bed"], mix.inputs[1])
    Lk.new(wem.outputs[0], mix.inputs[2])
    Lk.new(mix.outputs[0], gout.inputs["Shader"])
    return ng


def wrap_materials(objs, ng):
    done = set()
    for ob in objs:
        for slot in ob.material_slots:
            m = slot.material
            if m is None or m.name in done or not m.use_nodes:
                continue
            done.add(m.name)
            nt = m.node_tree
            for vc in [n for n in nt.nodes if n.type == "VERTEX_COLOR"]:
                for link in list(vc.outputs["Color"].links):
                    gm = nt.nodes.new("ShaderNodeGamma")
                    gm.inputs[1].default_value = 2.2
                    to = link.to_socket
                    nt.links.remove(link)
                    nt.links.new(vc.outputs["Color"], gm.inputs[0])
                    nt.links.new(gm.outputs[0], to)
            out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
            if out is None or not out.inputs["Surface"].links:
                continue
            link = out.inputs["Surface"].links[0]
            src = link.from_socket
            nt.links.remove(link)
            g = nt.nodes.new("ShaderNodeGroup")
            g.node_tree = ng
            nt.links.new(src, g.inputs["Bed"])
            nt.links.new(g.outputs["Shader"], out.inputs["Surface"])


def flat_material(name, colour):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*srgb_to_linear(colour[:3]), 1.0)
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def ribbon_object(name, segments, width, y_godot, colour, coll):
    if not segments:
        return None
    verts, faces = [], []
    for (a, b) in segments:
        ax, az = a
        bx, bz = b
        dx, dz = bx - ax, bz - az
        ln = math.hypot(dx, dz) or 1e-9
        ux, uz = dx / ln, dz / ln
        nx, nz = -uz * width / 2, ux * width / 2
        ax2, az2, bx2, bz2 = ax - ux * width / 2, az - uz * width / 2, bx + ux * width / 2, bz + uz * width / 2
        k = len(verts)
        verts += [B(ax2 + nx, y_godot, az2 + nz), B(ax2 - nx, y_godot, az2 - nz), B(bx2 - nx, y_godot, bz2 - nz), B(bx2 + nx, y_godot, bz2 + nz)]
        faces.append((k, k + 1, k + 2, k + 3))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(flat_material(name, colour))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


class Renderer:
    def __init__(self, folder):
        self.folder = folder
        scene = bpy.context.scene
        self.scene = scene
        scene.render.engine = "BLENDER_EEVEE"
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
        try:
            scene.eevee.taa_render_samples = 32
        except AttributeError:
            pass
        world = bpy.data.worlds.new("scratch_world")
        scene.world = world
        world.use_nodes = True
        self.bg = world.node_tree.nodes.get("Background")
        self.bg.inputs[0].default_value = (*srgb_to_linear((0.62, 0.72, 0.85)), 1.0)
        self.bg.inputs[1].default_value = 0.9
        sun_data = bpy.data.lights.new("scratch_sun", "SUN")
        sun_data.energy = 3.2
        sun_data.angle = math.radians(1.0)
        self.sun = bpy.data.objects.new("scratch_sun", sun_data)
        # 13:00-ish from the south-west, 50 degrees up
        self.sun.rotation_euler = (math.radians(40.0), 0.0, math.radians(-45.0))
        scene.collection.objects.link(self.sun)
        self.cam_data = bpy.data.cameras.new("scratch_camera")
        self.cam = bpy.data.objects.new("scratch_camera", self.cam_data)
        scene.collection.objects.link(self.cam)
        scene.camera = self.cam
        self.cam_data.clip_start = 1.0
        self.cam_data.clip_end = 60000.0
        self.outputs = []

    def shoot(self, name):
        self.scene.render.filepath = os.path.join(self.folder, name)
        bpy.ops.render.render(write_still=True)
        self.outputs.append(name)
        print("headland_shell: rendered %s" % name, flush=True)

    def top_down(self, name, box, px=1600):
        x0, x1, z0, z1 = box
        ex, ez = x1 - x0, z1 - z0
        self.cam_data.type = "ORTHO"
        self.cam_data.ortho_scale = max(ex, ez)
        self.cam_data.sensor_fit = "VERTICAL" if ez > ex else "HORIZONTAL"
        self.cam.location = B((x0 + x1) / 2, 3000.0, (z0 + z1) / 2)
        self.cam.rotation_euler = (0.0, 0.0, 0.0)
        self.scene.render.resolution_x = px
        self.scene.render.resolution_y = int(round(px * ez / ex))
        self.shoot(name)

    def oblique(self, name, eye, aim, lens, px=(1600, 1000)):
        self.cam_data.type = "PERSP"
        self.cam_data.sensor_fit = "HORIZONTAL"
        self.cam_data.lens = lens
        e, a = B(*eye), B(*aim)
        self.cam.location = e
        self.cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        self.scene.render.resolution_x, self.scene.render.resolution_y = px
        self.shoot(name)


# --- main -----------------------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--out" not in argv:
        raise SystemExit("headland_shell: --out <folder> is required")
    out = os.path.abspath(argv[argv.index("--out") + 1])
    master = os.path.abspath(argv[argv.index("--master") + 1]) if "--master" in argv else DEFAULT_MASTER
    assets = os.path.join(ROOT, "assets")
    for root in {assets, os.path.join(os.path.dirname(master), os.pardir, os.pardir, "assets")}:
        root = os.path.abspath(root)
        if os.path.commonpath([out, root]) == root:
            raise SystemExit("headland_shell: the output folder may not be under assets/")
    os.makedirs(out, exist_ok=True)
    scratch = os.path.join(out, "PROPOSAL_range_north_shell.blend")
    if os.path.abspath(scratch) == os.path.abspath(master):
        raise SystemExit("headland_shell: the scratch copy would overwrite the master")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    log(out, "scratch copy %s of %s opened" % (os.path.basename(scratch), master))
    src = bpy.data.objects[NAME]
    comp = bpy.data.objects[COMPANION]
    if src.matrix_world != src.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin" % NAME)
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)
    # the original vertex index on every vertex, on a copy kept as the reference (`_current`)
    fp0 = fingerprint(src.data)
    tag_original(src.data)
    report = {"master": master, "scratch": scratch, "object": NAME}
    piece_of = {}
    bm = bmesh.new()
    bm.from_mesh(src.data)
    for k, p in enumerate(pieces_of(bm)):
        for f in p:
            piece_of[f.index] = k
    bm.free()

    ground = [o for o in bpy.data.collections["Ground"].all_objects if o.type == 'MESH']
    others = [o for o in ground if o.name != NAME]
    report["current"] = {"topology": topology(src.data), "window": faces_seen(src, WINDOW, 4.0),
                         "inlet_fine": faces_seen(src, INLET, 1.0), "whole_object": faces_seen(src, (-1100, 1200, -1930, -530), 8.0)}
    log(out, "current: %s" % json.dumps(report["current"]["topology"]))
    log(out, "current window (4 m): down tops above sea %.0f m2, enter-never-leave %.0f m2" % (
        report["current"]["window"]["down_top_above_sea_m2"], report["current"]["window"]["enter_never_leave_m2"]))
    # the slabs: are they anyone's top?
    xs, zs, H, Wo = topmost_map(ground, (-720.0, 620.0, -980.0, -550.0), 2.0)
    rn_k = ground.index(src)
    expo = {}
    bmr = bmesh.new()
    bmr.from_mesh(src.data)
    rtree = BVHTree.FromBMesh(bmr)
    bmr.free()
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            if Wo[j, i] != rn_k:
                continue
            h = rtree.ray_cast(B(x, 5000.0, z), Vector((0.0, 0.0, -1.0)))
            if h[0] is None:
                continue
            pc = piece_of.get(h[2], 0)
            if pc in (1, 2, 3, 4):
                key = "piece%d_%s" % (pc, "above_sea" if h[0].z > SEA else "under_sea")
                expo[key] = expo.get(key, 0) + 4
                expo.setdefault("piece%d_highest_exposed_y" % pc, -99.0)
                expo["piece%d_highest_exposed_y" % pc] = max(expo["piece%d_highest_exposed_y" % pc], round(h[0].z, 2))
    report["exposure_of_pieces_m2"] = expo
    log(out, "the pieces as anyone's top (2 m): %s" % json.dumps(expo))
    # face 2436, the one down-facing top outside the window
    f2436 = src.data.polygons[2436]
    c = f2436.center
    over = []
    for o in others:
        bmo = bmesh.new()
        bmo.from_mesh(o.data)
        t = BVHTree.FromBMesh(bmo)
        bmo.free()
        h = t.ray_cast(Vector((c.x, c.y, 5000.0)), Vector((0.0, 0.0, -1.0)))
        if h[0] is not None and h[0].z > c.z:
            over.append((o.name, round(h[0].z - c.z, 1)))
    report["face_2436"] = {"centre_godot": [round(c.x, 1), round(c.z, 2), round(-c.y, 1)], "area_m2": round(f2436.area, 1),
                           "normal_y": round(f2436.normal.z, 3), "ground_over_it": over}
    log(out, "face 2436 (down-facing top outside the window): %s" % json.dumps(report["face_2436"]))
    report["companion"] = companion(src, comp)
    log(out, "companion: %s" % json.dumps(report["companion"]))

    variants = {}
    for v in ("R1", "R2"):
        ob, r = build(src, coll, v)
        r["topology"] = topology(ob.data)
        r["window"] = faces_seen(ob, WINDOW, 4.0)
        r["inlet_fine"] = faces_seen(ob, INLET, 1.0)
        r["whole_object"] = faces_seen(ob, (-1100, 1200, -1930, -530), 8.0)
        r["vertices"] = compare(src.data, ob.data)
        r["undo"] = undo_proof(src, ob)
        r["triangle_delta"] = r["topology"]["triangles"] - report["current"]["topology"]["triangles"]
        r["face_delta"] = r["topology"]["faces"] - report["current"]["topology"]["faces"]
        variants[v] = ob
        report[v] = r
        log(out, "%s: topology %s" % (v, json.dumps(r["topology"])))
        log(out, "%s: window down tops %.0f m2, enter-never-leave %.0f m2; inlet (1 m) %.0f / %.0f; vertices %s; undo %s; cracks %s; "
            "fold %s; shore %s" % (v, r["window"]["down_top_above_sea_m2"], r["window"]["enter_never_leave_m2"],
                                   r["inlet_fine"]["down_top_above_sea_m2"], r["inlet_fine"]["enter_never_leave_m2"],
                                   json.dumps(r["vertices"]), json.dumps(r["undo"]), json.dumps(r["cracks"]),
                                   json.dumps({k: r["fold"][k] for k in ("north_step_m", "seen_down_after_m2_at_0.25m", "lowered_steps")}),
                                   json.dumps(r["sand_body"])))

    # the waterline: the topmost Ground's -7.5 contour, today and with each variant
    def state(objs_rn):
        return [o for o in others] + [objs_rn]
    wl = {}
    hm = {}
    for key, rn in (("current", src), ("R1", variants["R1"]), ("R2", variants["R2"])):
        xs, zs, H, Wo = topmost_map(state(rn), INLET, 1.0)
        wl[key] = contour(xs, zs, H, SEA)
        hm[key] = H
    for v in ("R1", "R2"):
        sh = waterline_shift(wl["current"], wl[v])
        land = np.nan_to_num(hm[v], nan=-100.0) > SEA
        land0 = np.nan_to_num(hm["current"], nan=-100.0) > SEA
        diff = np.abs(np.nan_to_num(hm[v], nan=-100.0) - np.nan_to_num(hm["current"], nan=-100.0))
        vis = diff > 0.01
        report[v]["waterline"] = sh
        report[v]["visible_top_changed_m2_1m"] = int(vis.sum())
        report[v]["visible_top_max_change_m"] = round(float(np.max(np.where(vis & (np.nan_to_num(hm[v], nan=-100) > -60) & (np.nan_to_num(hm["current"], nan=-100) > -60), diff, 0.0))), 2)
        report[v]["land_added_m2"] = int((land & ~land0).sum())
        report[v]["land_removed_m2"] = int((~land & land0).sum())
        log(out, "%s: waterline %s; visible top changed over %d m2 (max %.2f m); land +%d / -%d m2" % (
            v, json.dumps(sh), report[v]["visible_top_changed_m2_1m"], report[v]["visible_top_max_change_m"],
            report[v]["land_added_m2"], report[v]["land_removed_m2"]))

    # sections
    sec = {}
    for key, rn in (("current", src), ("R1", variants["R1"]), ("R2", variants["R2"])):
        sec[key] = {}
        for name, (axis, value, srange, _) in SECTIONS.items():
            sec[key][name] = section_segments(others + [rn], axis, value, srange, rn, piece_of if key == "current" else None)
    with open(os.path.join(out, "sections.json"), "w") as f:
        json.dump(sec, f)

    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)
    # the scratch file keeps each variant as its own hidden object; the original is untouched
    # in it but for the `kyt_orig` vertex attribute, removed again here
    src.data.attributes.remove(src.data.attributes["kyt_orig"])
    if fingerprint(src.data) != fp0:
        raise SystemExit("the scratch copy's range north changed while the variants were built")
    for ob in variants.values():
        if "kyt_orig" in ob.data.attributes:
            ob.data.attributes.remove(ob.data.attributes["kyt_orig"])
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n2026-10-09 PROPOSAL (scratch copy only): range north's shell repair, variants R1 and R2 as hidden objects in "
            "the collection %s (tools/blender/world_terrain_proposals_headland_shell.py). Not the master.\n" % COLLECTION)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    log(out, "scratch file saved with the variants hidden in %s" % COLLECTION)

    if "--no-render" not in argv:
        render(out, src, variants, others, wl)
        # never save the render setup into the scratch file: reopen nothing, just stop
    subprocess.run(["/usr/bin/env", "python3", os.path.abspath(__file__), "--sections", out], check=False)
    log(out, "done")


def render(out, src, variants, others, wl):
    scene = bpy.context.scene
    ng = render_group()
    allobjs = others + [src] + list(variants.values())
    wrap_materials(allobjs, ng)
    for ob in scene.objects:
        ob.hide_render = True
    for ob in others + [src]:
        ob.hide_render = False
    rc = bpy.data.collections.new("scratch_render")
    scene.collection.children.link(rc)
    # the void: where no ground is under the sea, 30 m of water (the game's `open_depth`)
    vme = bpy.data.meshes.new("scratch_void")
    R = 60000.0
    vme.from_pydata([(-R, -R, -3000.0), (R, -R, -3000.0), (R, R, -3000.0), (-R, R, -3000.0)], [], [(0, 1, 2, 3)])
    t1 = 1.0 - math.exp(-30.0 / REACH)
    col = (srgb_to_linear(SHALLOW) * (1 - t1) + srgb_to_linear(DEEP) * t1) * np.array(WATER_GAIN)
    vm = bpy.data.materials.new("scratch_void")
    vm.use_nodes = True
    for n in list(vm.node_tree.nodes):
        vm.node_tree.nodes.remove(n)
    o_ = vm.node_tree.nodes.new("ShaderNodeOutputMaterial")
    e_ = vm.node_tree.nodes.new("ShaderNodeEmission")
    e_.inputs["Color"].default_value = (*col, 1.0)
    vm.node_tree.links.new(e_.outputs[0], o_.inputs[0])
    vme.materials.append(vm)
    void = bpy.data.objects.new("scratch_void", vme)
    rc.objects.link(void)
    rd = Renderer(out)
    lines = {"current": ribbon_object("wl_current", wl["current"], 1.6, SEA + 0.2, (1.0, 1.0, 1.0), rc)}
    for v in ("R1", "R2"):
        lines[v] = ribbon_object("wl_%s" % v, wl[v], 1.6, SEA + 0.3, (1.0, 0.2, 0.75), rc)
    for k, ob in lines.items():
        if ob:
            ob.hide_render = True

    def show(key):
        src.hide_render = key != "current"
        for v, ob in variants.items():
            ob.hide_render = v != key
            ob.hide_set(False)

    for key in ("current", "R1", "R2"):
        show(key)
        for name, (eye, aim, lens) in VIEWS.items():
            rd.oblique("range_north_shell_%s_%s.png" % (key, name), eye, aim, lens)
        lines["current"].hide_render = False
        if key != "current" and lines[key]:
            lines[key].hide_render = False
        rd.top_down("range_north_shell_%s_plan.png" % key, INLET)
        for ob in lines.values():
            if ob:
                ob.hide_render = True


if __name__ == "__main__":
    main()
