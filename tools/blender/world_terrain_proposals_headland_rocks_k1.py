"""Beach rocks variant K1, "seat and tidy" (2026-10-09), on a SCRATCH COPY of the range source only.

    Blender --background <CAT>/SCRATCH_range_source.blend --python <this> -- --out <OUT> --stage build
    Blender --background <OUT>/PROPOSAL_beach_rocks.blend --python <this> -- --out <OUT> --stage render
    python3 <this> --out <OUT> --stage plan
    Blender --background <range source> --python <this> -- --out <OUT> --stage apply

`--master <blend>` reads the ground from another master (default: the catalogue's scratch copy).
`--remove-hers-inside` also removes Christina's rocks that lie wholly inside another rock (her
choice, 2026-10-09: "remove your 26 hidden ones"); her fully buried ones stay. apply opens the
range source itself (only inside a worktree), removes and lowers by <OUT>/report_K1.json, and saves.

build saves the opened range scratch as <OUT>/PROPOSAL_beach_rocks.blend before anything else, reads
Ground (master) and the 09-15 range (75ca425) in memory only, and adds hidden `K1_<collection>`
collections of linked copies (obj.copy(), shared meshes) of the rocks that stay, lowered where they
float. The originals are untouched. render toggles original/K1 and never saves. plan draws a PIL map
from report_K1.json. Godot (x, y up, z) = Blender (x, -z, y); sea level y -7.5.
"""

import json
import math
import os
import sys
import time

import numpy as np

try:
    import bpy
    from mathutils import Matrix, Vector
    from mathutils.bvhtree import BVHTree
except ImportError:  # the plan stage runs under the system python3
    bpy = None

MAIN = "/Users/christina/Dropbox/Mac/Documents/Keep Your Ticket"
CAT = os.path.join(MAIN, "documentation/screenshots/coast-headland-2026-10-08/catalogue")
MASTER = os.path.join(CAT, "SCRATCH_master_20261008-2049.blend")
THEN = os.path.join(CAT, "props_range_20260915_75ca425.blend")
PROPOSAL = "PROPOSAL_beach_rocks.blend"
ROCK_COLLS = ["range_main_beach_middle_band_rocks", "range_remaining_beach_rocks",
              "range_beach_rocks", "range_base_boulders"]
WIN_B = (-1400.0, 150.0, -50.0, 1200.0)        # Blender x0, x1, y0, y1 (Godot x -1400..150, z -1200..50)
TOE_B = (-280.0, 150.0, 700.0, 900.0)          # base boulders on range north's buried toe (Godot z -900..-700)
SEA = -7.5
GAP_MAX, GAP_LEFT, REST_REACH, HERS_TOL = 0.3, 0.1, 0.3, 0.01
T0 = time.time()

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.realpath(argv[argv.index("--out") + 1])
STAGE = argv[argv.index("--stage") + 1]
if "--master" in argv:
    MASTER = os.path.realpath(argv[argv.index("--master") + 1])
HERS_INSIDE = "--remove-hers-inside" in argv
for sub in ("assets", "scenes", "scripts", "tools"):
    p = os.path.realpath(os.path.join(MAIN, sub))
    if os.path.commonpath([OUT, p]) == p:
        raise SystemExit("k1: refusing output under %s" % p)
if os.path.commonpath([OUT, os.path.realpath(CAT)]) == os.path.realpath(CAT):
    raise SystemExit("k1: refusing output in the catalogue")


def log(*a):
    msg = "[%5.0fs] " % (time.time() - T0) + " ".join(str(x) for x in a)
    print(msg)
    sys.stdout.flush()


def progress(line):
    with open(os.path.join(OUT, "progress.md"), "a") as f:
        f.write("- K1 %s\n" % line)


def in_box(x, y, box):
    return box[0] <= x <= box[1] and box[2] <= y <= box[3]


def godot_xz(x, y):
    return round(float(x), 2), round(float(-y), 2)


def new_ids_since(before):
    """Every datablock added since `before` (a set of (kind, pointer))."""
    out = []
    for kind in ("objects", "meshes", "materials", "collections", "images", "node_groups", "textures"):
        for idb in getattr(bpy.data, kind):
            if (kind, idb.as_pointer()) not in before:
                out.append(idb)
    return out


def id_snapshot():
    s = set()
    for kind in ("objects", "meshes", "materials", "collections", "images", "node_groups", "textures"):
        s.update((kind, idb.as_pointer()) for idb in getattr(bpy.data, kind))
    return s


def world_verts(ob, M=None):
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    Mw = np.array(M if M is not None else ob.matrix_world)
    return co.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]


# --- ground and the 09-15 range, in memory only ---------------------------------------------------

def load_ground(margin=60.0):
    """One BVH over the world triangles of the master's `Ground` objects that reach the window
    (a ray inside the window cannot hit anything else). Returns (tree, new datablocks, link coll)."""
    before = id_snapshot()
    with bpy.data.libraries.load(MASTER, link=False) as (src, dst):
        if "Ground" not in src.collections:
            raise SystemExit("k1: the master has no Ground collection")
        dst.collections = ["Ground"]
    coll = dst.collections[0]
    X0, X1, Y0, Y1 = WIN_B[0] - margin, WIN_B[1] + margin, WIN_B[2] - margin, WIN_B[3] + margin
    verts, polys, base, used = [], [], 0, 0
    for o in coll.all_objects:
        if o.type != "MESH" or not len(o.data.polygons):
            continue
        w = world_verts(o)
        if w[:, 0].max() < X0 or w[:, 0].min() > X1 or w[:, 1].max() < Y0 or w[:, 1].min() > Y1:
            continue
        o.data.calc_loop_triangles()
        tri = np.empty(len(o.data.loop_triangles) * 3, np.int64)
        o.data.loop_triangles.foreach_get("vertices", tri)
        verts.extend(w.tolist())
        polys.extend((tri.reshape(-1, 3) + base).tolist())
        base += len(w)
        used += 1
    log("ground: %d objects, %d verts, %d triangles in reach" % (used, len(verts), len(polys)))
    tree = BVHTree.FromPolygons(verts, polys, all_triangles=True)
    return tree, new_ids_since(before), coll


def ground_under(tree, XY):
    """First hit of a ray straight down from z +500 at each plan point; NaN where nothing is hit."""
    out = np.full(len(XY), np.nan)
    down = Vector((0.0, 0.0, -1.0))
    for i, (x, y) in enumerate(XY):
        loc = tree.ray_cast(Vector((x, y, 500.0)), down, 2000.0)[0]
        if loc is not None:
            out[i] = loc.z
    return out


def load_then_matrices(names):
    """{name: world location} of the named objects in the 09-15 range, then removed again."""
    before = id_snapshot()
    with bpy.data.libraries.load(THEN, link=False) as (src, dst):
        have = set(src.objects)
        want = [n for n in names if n in have]
        dst.objects = want
    locs = {}
    for n, o in zip(want, dst.objects):
        if o is not None:
            locs[n] = np.array(o.matrix_world.translation)
    bpy.data.batch_remove(new_ids_since(before))
    return locs


# --- rocks ----------------------------------------------------------------------------------------

class Rock:
    def __init__(self, ob, coll):
        self.ob, self.name, self.coll = ob, ob.name, coll
        self.M0 = Matrix(ob.matrix_world)
        self.drop = 0.0
        self.polys = [tuple(p.vertices) for p in ob.data.polygons]
        self.tris = sum(len(p) - 2 for p in self.polys)
        self.hers = ""
        self.fate = "kept"        # kept / lowered / removed_buried / removed_inside / removed_toe
        self.question = ""
        self.set_geometry()

    def set_geometry(self):
        M = Matrix.Translation((0.0, 0.0, -self.drop)) @ self.M0
        self.W = world_verts(self.ob, M)
        self.lo, self.hi = self.W.min(0), self.W.max(0)
        self._tree = None

    @property
    def tree(self):
        if self._tree is None:
            self._tree = BVHTree.FromPolygons(self.W.tolist(), self.polys)
        return self._tree

    def contains(self, p):
        """Odd number of crossings on a +X ray: p is inside this (closed) rock."""
        if not (self.lo[0] <= p[0] <= self.hi[0] and self.lo[1] <= p[1] <= self.hi[1]
                and self.lo[2] <= p[2] <= self.hi[2]):
            return False
        o, d, n = Vector(p), Vector((1.0, 0.0, 0.0)), 0
        for _ in range(64):
            loc = self.tree.ray_cast(o, d, 1e4)[0]
            if loc is None:
                break
            n += 1
            o = loc + d * 1e-4
        return n % 2 == 1

    def godot(self):
        t = self.M0.translation
        return godot_xz(t.x, t.y)


# --- measuring ------------------------------------------------------------------------------------

class Index:
    """Plan grid over rock bounding boxes, for overlap candidates."""
    CELL = 20.0

    def __init__(self, rocks):
        self.cells = {}
        for r in rocks:
            for k in self.keys(r.lo, r.hi):
                self.cells.setdefault(k, []).append(r)

    def keys(self, lo, hi):
        c = self.CELL
        for i in range(int(math.floor(lo[0] / c)), int(math.floor(hi[0] / c)) + 1):
            for j in range(int(math.floor(lo[1] / c)), int(math.floor(hi[1] / c)) + 1):
                yield (i, j)

    def overlapping(self, r, live=None, pad=0.0):
        seen, out = set(), []
        lo, hi = r.lo - pad, r.hi + pad
        for k in self.keys(lo, hi):
            for o in self.cells.get(k, ()):
                if o is r or id(o) in seen or (live is not None and o.fate.startswith("removed")):
                    continue
                seen.add(id(o))
                if (o.lo <= hi).all() and (o.hi >= lo).all():
                    out.append(o)
        return out


def measure_ground(r, tree):
    """Ground under every vertex (computed once; lowering moves nothing in plan)."""
    if getattr(r, "G", None) is None:
        r.G = ground_under(tree, r.W[:, :2])
    return r.G


def gap_of(r):
    """Minimum (vertex height - ground) over the lowest 20 % of vertices; None if no ground there."""
    z = r.W[:, 2]
    n = max(1, int(math.ceil(0.2 * len(z))))
    low = np.argsort(z)[:n]
    d = z[low] - r.G[low]
    d = d[~np.isnan(d)]
    return float(d.min()) if len(d) else None


def fully_buried(r):
    ok = ~np.isnan(r.G)
    return bool(ok.all() and (r.W[:, 2] < r.G).all())


def inside_host(r, index):
    """A single other, not removed, rock that holds every vertex of r, or None."""
    for o in index.overlapping(r, live=True):
        if not ((o.lo <= r.lo).all() and (o.hi >= r.hi).all()):
            continue          # a rock not inside o's box cannot be inside o
        if all(o.contains(p) for p in r.W):
            return o
    return None


def rests_on(r, index):
    """The rock a ray down from r's lowest vertex meets within REST_REACH (or the rock that lowest
    vertex already sits inside), or None."""
    p = r.W[int(np.argmin(r.W[:, 2]))]
    down = Vector((0.0, 0.0, -1.0))
    best = None
    for o in index.overlapping(r, live=True, pad=REST_REACH):
        if not (o.lo[0] <= p[0] <= o.hi[0] and o.lo[1] <= p[1] <= o.hi[1]):
            continue
        if o.lo[2] > p[2] + 1e-6 or o.hi[2] < p[2] - REST_REACH:
            continue
        if o.contains(p):
            return o
        hit = o.tree.ray_cast(Vector(p), down, REST_REACH)
        if hit[0] is not None and (best is None or hit[3] < best[1]):
            best = (o, hit[3])
    return best[0] if best else None


def stats(rocks, index):
    """Per collection: count, triangles, floaters (gap > 0.3 and not on a rock), fully buried,
    over open water (base below sea with no ground within 1 m under its lowest fifth)."""
    out = {}
    for r in rocks:
        if r.fate.startswith("removed"):
            continue
        s = out.setdefault(r.coll, {"rocks": 0, "triangles": 0, "floaters": 0, "buried": 0, "open_water": 0})
        s["rocks"] += 1
        s["triangles"] += r.tris
        g = gap_of(r)
        if g is not None and g > GAP_MAX and rests_on(r, index) is None:
            s["floaters"] += 1
        if fully_buried(r):
            s["buried"] += 1
        if r.lo[2] < SEA and (g is None or g > 1.0):
            s["open_water"] += 1
    return out


# --- build ----------------------------------------------------------------------------------------

def window_rocks():
    rocks, outside = [], []
    for cn in ROCK_COLLS:
        col = bpy.data.collections.get(cn)
        if col is None:
            raise SystemExit("k1: no collection %s" % cn)
        for o in col.all_objects:
            if o.type != "MESH":
                continue
            t = o.matrix_world.translation
            (rocks if in_box(t.x, t.y, WIN_B) else outside).append((o, cn))
    return [Rock(o, cn) for o, cn in rocks], outside


def decide(rocks, tree):
    """Fates in a fixed order: the toe line, then fully buried, then wholly inside another rock,
    then lowering what floats. Christina's rocks are only ever lowered, never removed."""
    index = Index(rocks)
    for r in rocks:
        measure_ground(r, tree)
    for r in rocks:
        x, y = r.M0.translation.x, r.M0.translation.y
        if r.coll == "range_base_boulders" and in_box(x, y, TOE_B):
            if r.hers:
                r.question = "hers, on the buried toe line"
            else:
                r.fate = "removed_toe"
    for r in rocks:
        if r.fate == "kept" and fully_buried(r):
            if r.hers:
                r.question = "hers, fully buried"
            else:
                r.fate = "removed_buried"
    for r in rocks:
        if r.fate == "kept":
            host = inside_host(r, index)
            if host is not None:
                if r.hers and not HERS_INSIDE:
                    r.question = "hers, wholly inside %s" % host.name
                else:
                    r.fate = "removed_inside"
    # lowest first, so a rock lowered onto a neighbour finds the neighbour already seated
    for r in sorted(rocks, key=lambda q: q.lo[2]):
        if r.fate != "kept":
            continue
        g = gap_of(r)
        if g is not None and g > GAP_MAX and rests_on(r, index) is None:
            r.drop = g - GAP_LEFT
            r.fate = "lowered"
            r.set_geometry()
    return index


def k1_collections(rocks, outside):
    """Hidden K1_<collection> beside each original, holding linked copies of every rock that stays
    (rocks outside the window unchanged), so the variant replaces the originals one for one."""
    out = {}
    for cn in ROCK_COLLS:
        src = bpy.data.collections[cn]
        k = bpy.data.collections.new("K1_" + cn)
        bpy.context.scene.collection.children.link(k)
        k.hide_viewport = True
        k.hide_render = True
        out[cn] = k
    for r in rocks:
        if r.fate.startswith("removed"):
            continue
        c = r.ob.copy()
        c.matrix_world = Matrix.Translation((0.0, 0.0, -r.drop)) @ r.M0
        out[r.coll].objects.link(c)
    for o, cn in outside:
        out[cn].objects.link(o.copy())
    return out


def build():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, PROPOSAL))
    tree, ground_ids, _ = load_ground()
    rocks, outside = window_rocks()
    log("rocks in the window: %d (outside: %d)" % (len(rocks), len(outside)))
    # Christina's hand edits of 2026-09-15..17 (295 `.001` copies, 521 moved), from the per-commit
    # history pass (progress.md step 1); an unlinked object's matrix_world in the 09-15 file is not
    # evaluated, so comparing against it here would flag every parented rock.
    hers = set(json.load(open(os.path.join(OUT, "hers_2026-09-15_to_17.json"))))
    for r in rocks:
        if r.name in hers:
            r.hers = "copied" if r.name.endswith(".001") else "moved"
    log("hers: %d" % sum(1 for r in rocks if r.hers))
    index0 = Index(rocks)
    for r in rocks:
        measure_ground(r, tree)
    before = stats(rocks, index0)
    index = decide(rocks, tree)
    after = stats(rocks, index)
    log("before", json.dumps(before))
    log("after", json.dumps(after))
    k1_collections(rocks, outside)
    fates = {}
    for r in rocks:
        fates[r.fate] = fates.get(r.fate, 0) + 1
    rep = {
        "source": "catalogue/SCRATCH_range_source.blend", "ground": "catalogue/SCRATCH_master_20261008-2049.blend",
        "window_godot": "x -1400..150, z -1200..50", "rocks_in_window": len(rocks),
        "fates": fates, "hers_in_window": sum(1 for r in rocks if r.hers),
        "hers_lowered": [dict(name=r.name, xz=r.godot(), drop=round(r.drop, 2)) for r in rocks if r.hers and r.fate == "lowered"],
        "questions_for_christina": [dict(name=r.name, xz=r.godot(), why=r.question) for r in rocks if r.question],
        "before": before, "after": after,
        "triangles_window_before": sum(r.tris for r in rocks),
        "triangles_window_after": sum(r.tris for r in rocks if not r.fate.startswith("removed")),
        "rocks": [dict(name=r.name, coll=r.coll, xz=r.godot(),
                       radius=round(float(max(r.hi[0] - r.lo[0], r.hi[1] - r.lo[1]) / 2.0), 2),
                       fate=r.fate, hers=bool(r.hers), drop=round(r.drop, 2)) for r in rocks],
    }
    with open(os.path.join(OUT, "report_K1.json"), "w") as f:
        json.dump(rep, f, indent=1)
    bpy.data.batch_remove(ground_ids)
    bpy.ops.wm.save_mainfile()
    progress("build: %s; hers lowered %d, questions %d; window triangles %d -> %d" % (
        json.dumps(fates), len(rep["hers_lowered"]), len(rep["questions_for_christina"]),
        rep["triangles_window_before"], rep["triangles_window_after"]))
    log("saved", os.path.join(OUT, PROPOSAL))


# --- render (never saves) -------------------------------------------------------------------------

VIEWS = {"beach": ((-420.0, -4.0, -640.0), (-150.0, 0.0, -760.0), 35.0),
         "toe": ((-760.0, 10.0, -520.0), (-705.0, -4.0, -630.0), 35.0),
         "V2": ((-520.0, 200.0, -380.0), (-200.0, 0.0, -800.0), 35.0)}


def g2b(p):
    return Vector((p[0], -p[2], p[1]))


def render():
    with bpy.data.libraries.load(MASTER, link=False) as (src, dst):
        dst.collections = ["Ground"]
    bpy.context.scene.collection.children.link(dst.collections[0])
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1600, 1000, 100
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("k1_world")
    sc.world.color = (0.55, 0.68, 0.85)
    sea_me = bpy.data.meshes.new("k1_sea")
    sea_me.from_pydata([(-3000, -3000, SEA), (3000, -3000, SEA), (3000, 3000, SEA), (-3000, 3000, SEA)], [], [(0, 1, 2, 3)])
    sea = bpy.data.objects.new("k1_sea", sea_me)
    sc.collection.objects.link(sea)
    mat = bpy.data.materials.new("k1_sea")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.25, 0.45, 0.55, 1.0)
    b.inputs["Alpha"].default_value = 0.55
    try:
        mat.surface_render_method = "BLENDED"
    except AttributeError:
        mat.blend_method = "BLEND"
    sea_me.materials.append(mat)
    sun = bpy.data.objects.new("k1_sun", bpy.data.lights.new("k1_sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(-135))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("k1_cam", bpy.data.cameras.new("k1_cam"))
    cam.data.clip_end = 6000.0
    sc.collection.objects.link(cam)
    sc.camera = cam
    for variant in ("current", "K1"):
        for cn in ROCK_COLLS:
            bpy.data.collections[cn].hide_render = variant != "current"
            bpy.data.collections["K1_" + cn].hide_render = variant == "current"
        for name, (eye, aim, lens) in VIEWS.items():
            e, a = g2b(eye), g2b(aim)
            cam.location = e
            cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
            cam.data.lens = lens
            sc.render.filepath = os.path.join(OUT, "beach_rocks_%s_%s.png" % (variant, name))
            bpy.ops.render.render(write_still=True)
            log("rendered", sc.render.filepath)
    progress("render: current and K1 x %s" % ", ".join(VIEWS))


# --- plan (system python3 + PIL) ------------------------------------------------------------------

COLOURS = {"kept": (150, 150, 150), "lowered": (40, 110, 230), "removed_buried": (20, 20, 20),
           "removed_inside": (240, 150, 30), "removed_toe": (210, 40, 40)}


def plan():
    from PIL import Image, ImageDraw
    rep = json.load(open(os.path.join(OUT, "report_K1.json")))
    x0, x1, z0, z1, s = -1400.0, 150.0, -1200.0, 50.0, 1.0
    W, H = int((x1 - x0) * s), int((z1 - z0) * s)
    im = Image.new("RGB", (W + 260, H + 40), (246, 244, 238))
    d = ImageDraw.Draw(im)
    def px(x, z):
        return (x - x0) * s, (z - z0) * s
    for gx in range(-1400, 151, 100):
        d.line([px(gx, z0), px(gx, z1)], fill=(225, 222, 214))
        d.text((px(gx, z1)[0] + 2, H + 4), str(gx), fill=(80, 80, 80))
    for gz in range(-1200, 51, 100):
        d.line([px(x0, gz), px(x1, gz)], fill=(225, 222, 214))
        d.text((2, px(x0, gz)[1] + 2), str(gz), fill=(80, 80, 80))
    order = ["kept", "lowered", "removed_inside", "removed_buried", "removed_toe"]
    for fate in order:
        for r in rep["rocks"]:
            if r["fate"] != fate:
                continue
            cx, cy = px(*r["xz"])
            rad = max(1.5, r["radius"] * s)
            d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=COLOURS[fate],
                      fill=None if fate == "kept" else COLOURS[fate])
    for q in rep["questions_for_christina"]:
        cx, cy = px(*q["xz"])
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=(220, 0, 220), width=2)
    ly = 20
    d.text((W + 12, ly), "K1 seat and tidy (north up, Godot m)", fill=(0, 0, 0))
    for fate in order:
        ly += 22
        d.ellipse([W + 12, ly, W + 24, ly + 12], fill=COLOURS[fate])
        d.text((W + 30, ly), "%s: %d" % (fate, rep["fates"].get(fate, 0)), fill=(0, 0, 0))
    ly += 22
    d.ellipse([W + 12, ly, W + 24, ly + 12], outline=(220, 0, 220), width=2)
    d.text((W + 30, ly), "hers, a question: %d" % len(rep["questions_for_christina"]), fill=(0, 0, 0))
    im.save(os.path.join(OUT, "beach_rocks_K1_plan.png"))
    print("plan written")


def apply():
    """Carry report_K1.json into the range source opened here (a worktree's only): removed rocks
    go, lowered rocks drop straight down in world space; every other object stays."""
    src = os.path.realpath(bpy.data.filepath)
    if "/.claude/worktrees/" not in src:
        raise SystemExit("k1: apply only runs on a worktree's range source, not %s" % src)
    bpy.context.preferences.filepaths.save_version = 0
    rep = json.load(open(os.path.join(OUT, "report_K1.json")))
    gone = lowered = missing = 0
    for r in rep["rocks"]:
        o = bpy.data.objects.get(r["name"])
        if o is None:
            missing += 1
            continue
        if r["fate"].startswith("removed"):
            bpy.data.objects.remove(o)
            gone += 1
        elif r["fate"] == "lowered" and r["drop"] > 0.0:
            o.matrix_world = Matrix.Translation((0.0, 0.0, -r["drop"])) @ o.matrix_world
            lowered += 1
    if missing:
        raise SystemExit("k1: %d rocks of the report are not in %s; nothing saved" % (missing, src))
    bpy.ops.wm.save_mainfile()
    log("applied: %d removed, %d lowered, saved %s" % (gone, lowered, src))


if STAGE == "build":
    build()
elif STAGE == "apply":
    apply()
elif STAGE == "render":
    render()
elif STAGE == "plan":
    plan()
else:
    raise SystemExit("k1: unknown stage %s" % STAGE)
