"""Proposals on a SCRATCH COPY of the world terrain master, never on the master itself
(2026-10-09, the coast/headland catalogue's fix 3): where range north meets coast north, the shore
from the headland's root north to z -1200, one owner per metre of shore.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/blender/world_terrain_proposals_headland_north_shore.py -- --out <folder> [--master <blend>] [--no-render]
    python3 tools/blender/world_terrain_proposals_headland_north_shore.py --plot <folder>

The Blender run copies the master into `<folder>/PROPOSAL_north_shore.blend` (refuses any output
under assets/, scenes/, scripts/ or tools/) and builds two variants beside the untouched originals,
each in its own hidden collection:

- C1, "the beach runs to the road": range north's beach and a gently rising backshore own the
  shore up to the corridor; coast north's thin wedge west of the corridor comes down into a dune
  slope from the beach to the corridor edge (its seam vertices fixed), and its west skirt goes.
- C2, "the coast keeps a low bluff": coast north's wedge stays; its west skirt becomes a rocky
  bank at 1:1.75 down to range north's sand, which stays low in front of it.

Both: range north's buried east body (under coast north, the reserve and the corridor) is cut
along a 4 m cell zone just inside the overlap, emptied and capped (Ground edit 1's method), its
visible island east of x 0 (catalogue G4) kept; its y 20 plateau comes down to the wedge where it
pokes through it; the internal slab (G17) in the zone goes; the coast shelf goes where land now
covers it (G15); the apron becomes a rising backshore; the straight south shore gets broad curves.
Nothing west of x -431 moves. Roads, the corridor seam, the anchors and the generator are not
touched; the corridor itself (not in the master) is stood in for, for the burial test and the
renders only, by a surface from its two seams to the road centreline.

Renders, sections and report.json go to the folder; `--plot` draws the sections with PIL.
"""

import json
import math
import os
import shutil
import sys
import time

import numpy as np

try:
    import bpy
    import bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import delaunay_2d_cdt
except ImportError:  # --plot runs under plain python3
    bpy = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DEFAULT_MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
NAME = "north_shore"
SEA = -7.5
RN = "background_distant_range_north"
CN = "terrain_world_coast_north"
SHELF = "terrain_coast_shelf"
LSHELF = "terrain_landform_shelf"
RESERVE = "terrain_world_mainland_reserve"
CURVE = "coast_highway_centreline"
# the zone (Godot x, z): the shore from the headland's root north to z -1200
ZONE = (-460.0, -40.0, -1200.0, -540.0)
WEST_LIMIT = -431.0      # nothing of range north moves west of this
WEST_FADE = 70.0         # the reshape fades in over this east of FADE_FROM (was 30: a 1:4 ramp)
NORTH_FADE = (-905.0, -945.0)     # every change fades out here: north of it range north's plateau
                                  # borders the corridor hole (2026-10-09, see HOLE_MARGIN)
HOLE_MARGIN, HOLE_FADE = 12.0, 20.0   # range north is held exactly within this of the corridor hole,
                                      # faded in over HOLE_FADE beyond it
STEP = 4.0               # the lattice the cut zone is drawn on
REFINE = 6.0             # the lattice range north's top is refined on in the zone
FADE_FROM = -428.0       # the last lattice line west of the limit: west of it the surface is exactly today's
BEACH_SLOPE = 1.0 / 8.0
CREST = -4.6             # the beach's crest (range north's `beach` heights, CAT step 4)
TOE_Y = 10.0             # the backshore rises to meet the existing toe slope where it reaches this
TOE_POWER = 1.8          # concave: the backshore stays low near the beach, then steepens to the toe
PLATEAU_RAMP = 110.0     # the lowered plateau rises back to its own height over this distance
DUNE = 3.0               # C1: the dune from the beach to the corridor edge, 1:3
BANK = 1.75              # C2: the rocky bank, 1:1.75
LAP = 0.12               # a coast north edge laid on range north sits this far under it
FOOT_DROP = 0.4          # C2: range north stays this far under the wedge's edge at the bluff's foot
SEAM_HOLD = (2.0, 6.0)   # coast north vertices within 2 m of the corridor seam never move
BURY = 0.5               # range north is "buried" where other ground stands this far over it
FLOOR = -11.0
ROAD_HALF = 8.0
# the shore curves: (centre x, half width, offset m; negative = landward, a cove)
CURVES = [(-372.0, 55.0, -13.0), (-292.0, 45.0, 9.0), (-222.0, 35.0, -7.0)]
CURVE_FADE = (-185.0, -170.0)
# materials (range north's own)
M_SAND = "distant_range_cove_sand"
M_PLANT = "distant_massif_toe_rock_forest_2"
TOE_BANDS = ((16.0, "distant_massif_toe_dark"), (32.0, "distant_massif_toe_rock"), (43.0, "distant_massif_toe_rock_forest_1"),
             (54.0, "distant_massif_toe_rock_forest_2"), (65.0, "distant_massif_toe_rock_forest_3"), (1e9, "distant_massif_forest"))
M_SHINGLE = "distant_range_cliff_blue_gray"   # the grey band between the beach crest and SHINGLE_TOP
SHINGLE_TOP = 3.5        # the untouched apron is grey from about -5 to +3.4, the toe dark above
HOLD_NEAR, HOLD_FAR = 3.0, 10.0   # ground under a seated rock is held within its radius plus these
C_SAND = (0.78, 0.72, 0.58)
C_ROCK = (0.40, 0.38, 0.34)
# views (Godot eye, aim, lens)
VIEWS = {
    "V2": ((-520.0, 200.0, -380.0), (-200.0, 0.0, -800.0), 35.0),
    "V1": ((-330.0, 170.0, -60.0), (-230.0, 0.0, -420.0), 35.0),
    "beach": ((-420.0, -4.0, -640.0), (-150.0, 0.0, -760.0), 35.0),
}
PLAN = (-460.0, -40.0, -1200.0, -540.0)
SECTIONS = {"x170": ("x", -170.0, (-1220.0, -540.0)), "z640": ("z", -640.0, (-460.0, -40.0)),
            "z1000": ("z", -1000.0, (-460.0, -40.0)), "z800": ("z", -800.0, (-460.0, -40.0))}
T0 = time.time()


def log(msg):
    print("[%6.1fs] north_shore: %s" % (time.time() - T0, msg), flush=True)


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def raised(x, c, hw):
    t = np.clip((np.asarray(x, dtype=float) - c) / hw, -1.0, 1.0)
    return 0.5 * (1.0 + np.cos(np.pi * t))


# --- reading the master -----------------------------------------------------------------------

def bvh(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def top(tree, x, z, up_only=True):
    """The topmost surface of `tree` over Godot (x, z), or None (optionally only up-facing hits)."""
    o = Vector((x, -z, 4000.0))
    d = Vector((0.0, 0.0, -1.0))
    while True:
        h = tree.ray_cast(o, d)
        if h[0] is None:
            return None
        if not up_only or h[1].z > 0.0:
            return h[0].z
        o = h[0] - Vector((0.0, 0.0, 1e-3))


def hits(tree, x, z, n=8):
    out = []
    o = Vector((x, -z, 4000.0))
    d = Vector((0.0, 0.0, -1.0))
    while len(out) < n:
        h = tree.ray_cast(o, d)
        if h[0] is None:
            break
        out.append((round(h[0].z, 3), 1 if h[1].z > 0 else -1))
        o = h[0] - Vector((0.0, 0.0, 1e-3))
    return out


class Lines:
    """Coast north's wedge and the corridor hole, read from coast north's open edges: the wedge's
    west edge (the shore wall cut at -8, under its -0.16 top), the wedge's east edge (the corridor
    seam) and the hill's west edge (the seam across the corridor), each as x and height by z."""

    def __init__(self, cn, curve):
        sp = curve.data.splines[0]
        cl = np.array([tuple(curve.matrix_world @ p.co.to_3d()) for p in sp.points])
        cl = cl[np.argsort(cl[:, 1])]
        self.cl_z = -cl[:, 1][::-1]
        self.cl_x = cl[:, 0][::-1]
        self.cl_y = cl[:, 2][::-1]
        order = np.argsort(self.cl_z)
        self.cl_z, self.cl_x, self.cl_y = self.cl_z[order], self.cl_x[order], self.cl_y[order]
        bm = bmesh.new()
        bm.from_mesh(cn.data)
        shore, seam = [], []
        for e in bm.edges:
            if not e.is_boundary:
                continue
            for v in e.verts:
                x, z, y = v.co.x, -v.co.y, v.co.z
                if not (-2000.0 < z < -500.0):
                    continue
                c = self.road_x(z)
                if abs(y + 8.0) < 0.05 and c - 160.0 < x < c - 5.0:
                    shore.append((z, x, y))
                elif y > -7.9 and c - 70.0 < x < c + 90.0:
                    seam.append((z, x, y))
        bm.free()
        self.seam_pts = np.array(seam)
        zb = np.arange(-2000.0, -499.0, 2.0)

        seam = [(z, x, y, self.road_x(z)) for z, x, y in seam]

        def binned(pts, pick, side):
            zs, xs, ys = [], [], []
            P = np.array([p[:3] for p in pts if side(p)]) if pts else np.zeros((0, 3))
            for z0 in zb:
                sel = np.nonzero(np.abs(P[:, 0] - z0) <= 1.5)[0] if len(P) else []
                m = [tuple(P[i]) for i in sel]
                if m:
                    k = pick([p[1] for p in m])
                    zs.append(z0)
                    xs.append(m[k][1])
                    ys.append(m[k][2])
            return np.array(zs), np.array(xs), np.array(ys)

        self.w_z, self.w_x, _ = binned(shore, lambda xs: int(np.argmax(xs)), lambda p: True)
        self.sw_z, self.sw_x, self.sw_y = binned(seam, lambda xs: int(np.argmax(xs)), lambda p: p[1] < p[3])
        self.se_z, self.se_x, self.se_y = binned(seam, lambda xs: int(np.argmin(xs)), lambda p: p[1] > p[3])

    def road_x(self, z):
        return float(np.interp(z, self.cl_z, self.cl_x))

    def road_y(self, z):
        return float(np.interp(z, self.cl_z, self.cl_y))

    def west(self, z):
        return float(np.interp(z, self.w_z, self.w_x))

    def seam_w(self, z):
        return float(np.interp(z, self.sw_z, self.sw_x)), float(np.interp(z, self.sw_z, self.sw_y))

    def seam_e(self, z):
        return float(np.interp(z, self.se_z, self.se_x)), float(np.interp(z, self.se_z, self.se_y))

    def standin(self, x, z):
        """The corridor stand-in: from the wedge's seam up (or down) to the road's edge, the road,
        and on to the hill's seam. None outside the hole."""
        if not (self.se_z[0] <= z <= self.se_z[-1] and self.sw_z[0] <= z <= self.sw_z[-1]):
            return None
        xw, yw = self.seam_w(z)
        xe, ye = self.seam_e(z)
        if not (xw < x < xe):
            return None
        c, r = self.road_x(z), self.road_y(z)
        a, b = max(xw + 1.0, c - ROAD_HALF), min(xe - 1.0, c + ROAD_HALF)
        if x <= a:
            return yw + (r - yw) * (x - xw) / max(a - xw, 1e-3)
        if x >= b:
            return r + (ye - r) * (x - b) / max(xe - b, 1e-3)
        return r

    def hole_floor(self, x, z):
        """Inside the corridor's hole, the lowest of its two seams and the road: whatever the
        generator builds there stands at least this high, so range north under it is buried."""
        if not (self.se_z[0] <= z <= self.se_z[-1] and self.sw_z[0] <= z <= self.sw_z[-1]):
            return None
        xw, yw = self.seam_w(z)
        xe, ye = self.seam_e(z)
        if not (xw < x < xe):
            return None
        return min(yw, ye, self.road_y(z))

    def seam_distance(self, x, z):
        d = np.hypot(self.seam_pts[:, 1] - x, self.seam_pts[:, 0] - z)
        return float(d.min())


# --- the design ---------------------------------------------------------------------------------

class Design:
    """Range north's designed top in the zone, per variant (heights in Godot y)."""

    def __init__(self, lines, rn_tree):
        self.L = lines
        self.tree = rn_tree
        # the current south shore: per column, where range north's top crosses the sea going south
        self.xs = np.arange(-480.0, -100.0, 2.0)
        zwl, zrim, ztoe = [], [], []
        for x in self.xs:
            col = [(z, top(rn_tree, x, z)) for z in np.arange(-1000.0, -520.0, 1.0)]
            wl = rim = toe = None
            for (z0, y0), (z1, y1) in zip(col, col[1:]):
                if y0 is not None and y1 is not None and y0 >= SEA > y1:
                    wl = z0 + (y0 - SEA) / (y0 - y1)
                if y0 is not None and y1 is None:
                    rim = z0
            for z0, y0 in reversed(col):
                if wl is not None and z0 < wl and y0 is not None and y0 >= TOE_Y:
                    toe = z0
                    break
            zwl.append(wl if wl is not None else np.nan)
            zrim.append(rim if rim is not None else np.nan)
            ztoe.append(toe if toe is not None else np.nan)
        self.zwl = self.fill(np.array(zwl, dtype=float))
        self.zrim = self.fill(np.array(zrim, dtype=float))
        self.ztoe = self.fill(np.array(ztoe, dtype=float))
        # the new waterline: the old one rounded (a 25 m Gaussian) plus broad curves, faded to the
        # old one at the west limit and towards the wedge
        sig = 25.0 / 2.0
        k = np.exp(-0.5 * (np.arange(-40, 41) / sig) ** 2)
        k /= k.sum()
        pad = np.pad(self.zwl, 40, mode="edge")
        smooth = np.convolve(pad, k, mode="same")[40:-40]
        c = sum(a * raised(self.xs, cx, hw) for cx, hw, a in CURVES)
        w = smoothstep(FADE_FROM, FADE_FROM + WEST_FADE, self.xs) * (1.0 - smoothstep(*CURVE_FADE, self.xs))
        zn = self.zwl + w * (smooth - self.zwl) + w * c
        # never closer than 8 m to range north's own rim (the beach must reach the floor inside it)
        self.zn = np.minimum(zn, self.zrim - 8.0)
        self.dc = (CREST - SEA) / BEACH_SLOPE

    @staticmethod
    def fill(a):
        ok = ~np.isnan(a)
        idx = np.arange(len(a))
        return np.interp(idx, idx[ok], a[ok])

    def col(self, arr, x):
        return float(np.interp(x, self.xs, arr))

    def base(self, x, z, E):
        """The shared design: beach, backshore, plateau lowering. E is today's height there."""
        zn = self.col(self.zn, x)
        delta = zn - z                      # metres inland of the new waterline
        T = E
        if delta < self.dc:
            T = max(SEA + delta * BEACH_SLOPE, FLOOR + 0.25)
        else:
            da = self.col(self.zn, x) - self.col(self.ztoe, x)
            if da > self.dc + 10.0 and delta < da + 20.0:
                t = min(1.0, (delta - self.dc) / (da - self.dc))
                B = CREST + (TOE_Y - CREST) * t ** TOE_POWER
                T = B + (E - B) * float(smoothstep(da, da + 20.0, delta)) if delta > da else B
        return T

    def plateau(self, x, z, E, h_join):
        """Where the plateau and the toe slope stand over the wedge's edge: down to `h_join` at the
        edge, back up to today's height over `PLATEAU_RAMP`."""
        xw = self.L.west(z)
        d = max(0.0, xw - x)
        P = h_join + (E - h_join) * float(smoothstep(0.0, PLATEAU_RAMP, d))
        return min(E, P)

    def wedge_width(self, z):
        return self.L.seam_w(z)[0] - self.L.west(z)


def design_height(D, variant, x, z, E):
    """Range north's new height at Godot (x, z) for the variant; E is today's height there."""
    L = D.L
    xw = L.west(z)
    xs, ys = L.seam_w(z)
    xq = min(x, xw)                      # under the wedge, the edge's value carries on, dipping
    Eq = E if x <= xw else (top(D.tree, xq, z) or E)
    if variant == "C1":
        h_join = ys - (xs - xw) / DUNE
    else:
        h_join = -0.16 - FOOT_DROP
    T = D.base(xq, z, Eq)
    # The plateau lowering is off (2026-10-09). Inside the corridor hole range north is the only
    # master ground, so lowering it there moved the generator's corridor batter by up to 13 m and
    # opened its stitch with coast north; north of z -944 the plateau borders the hole, so it stays.
    wP = 0.0
    if wP > 0.0:
        T = T + (min(T, D.plateau(xq, z, Eq, h_join)) - T) * wP
    if variant == "C1":
        dune = ys - (xs - xq) / DUNE
        if xq > xw - 40.0 and z > -960.0:
            T = max(T, dune)
    else:
        lim = -0.16 - FOOT_DROP
        if T > lim:
            T = T - (T - lim) * float(smoothstep(-15.0, 0.0, xq - xw))
    if x > xw:
        T = T - min(0.15 * (x - xw), 3.0)
    wN = float(smoothstep(NORTH_FADE[0], NORTH_FADE[1], z))
    wW = float(smoothstep(FADE_FROM, FADE_FROM + WEST_FADE, x))
    w = (1.0 - wN) * wW
    if w <= 0.0:
        return E
    return max(E + (T - E) * w, FLOOR + 0.25)


# --- mesh work ------------------------------------------------------------------------------------

def copy_object(ob, name, col):
    me = ob.data.copy()
    me.name = name
    nob = bpy.data.objects.new(name, me)
    for k in ob.keys():
        nob[k] = ob[k]
    nob["kyt_proposal"] = NAME
    col.objects.link(nob)
    return nob


def as_triangles(bm, me):
    """Every face as the triangles the exporter draws (Blender's loop triangles), so cuts and
    moves start from exactly the surface the game shows."""
    me.calc_loop_triangles()
    tris = {}
    for lt in me.loop_triangles:
        tris.setdefault(lt.polygon_index, []).append(tuple(lt.vertices))
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    held = [(bm.faces[pi], [[bm.verts[i] for i in t] for t in ts]) for pi, ts in tris.items()]
    gone = []
    for f, ts in held:
        if len(f.verts) == 3:
            continue
        for t in ts:
            nf = bm.faces.new(t)
            nf.material_index = f.material_index
            nf.smooth = f.smooth
        gone.append(f)
    bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')


def bisect_lines(bm, lines, pick):
    """Cut along vertical planes: `lines` is [(axis, c, lo, hi)] in Blender plan coordinates
    (axis 'x': the plane x = c for lo <= y <= hi). `pick(f)` limits which faces are cut. Faces are
    found through a 32 m hash, kept up to date as the cuts make new ones."""
    H = 32.0
    hmap = {}

    def add(f):
        xs = [v.co.x for v in f.verts]
        ys = [v.co.y for v in f.verts]
        for i in range(int(math.floor(min(xs) / H)), int(math.floor(max(xs) / H)) + 1):
            for j in range(int(math.floor(min(ys) / H)), int(math.floor(max(ys) / H)) + 1):
                hmap.setdefault((i, j), set()).add(f)
    for f in bm.faces:
        add(f)
    for axis, c, lo, hi in lines:
        k = int(math.floor(c / H))
        ks = (k - 1, k) if abs(c - k * H) < 1e-6 else (k,)
        found = set()
        for m in range(int(math.floor(lo / H)), int(math.floor(hi / H)) + 1):
            for kk in ks:
                found |= hmap.get((kk, m) if axis == "x" else (m, kk), set())
        cand = []
        for f in found:
            if not f.is_valid:
                continue
            if axis == "x":
                across = [v.co.x for v in f.verts]
                along = [v.co.y for v in f.verts]
            else:
                across = [v.co.y for v in f.verts]
                along = [v.co.x for v in f.verts]
            if min(across) < c - 1e-6 and max(across) > c + 1e-6 and max(along) > lo - 1e-6 and min(along) < hi + 1e-6:
                f.normal_update()
                if pick(f):
                    cand.append(f)
        if not cand:
            continue
        geom = set(cand)
        for f in cand:
            geom.update(f.edges)
            geom.update(f.verts)
        no = Vector((1.0, 0.0, 0.0)) if axis == "x" else Vector((0.0, 1.0, 0.0))
        co = Vector((c, 0.0, 0.0)) if axis == "x" else Vector((0.0, c, 0.0))
        cut = bmesh.ops.bisect_plane(bm, geom=list(geom), dist=1e-4, plane_co=co, plane_no=no)
        for v in cut["geom_cut"]:
            if isinstance(v, bmesh.types.BMVert):
                if axis == "x":
                    v.co.x = c
                else:
                    v.co.y = c
        for ele in cut["geom"]:
            if isinstance(ele, bmesh.types.BMFace):
                add(ele)
    ngons = [f for f in bm.faces if len(f.verts) > 3]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)


class Zone:
    """A set of STEP cells (i, j) in Blender plan (cell [i, i+1] x [j, j+1] in steps) and its edge
    as straight runs, the zone on the left of each (as Ground edit 1's zone)."""

    def __init__(self, cells, step):
        self.cells = cells
        self.step = step
        edges = {}
        for (i, j) in cells:
            for a, b in (((i, j), (i + 1, j)), ((i + 1, j), (i + 1, j + 1)), ((i + 1, j + 1), (i, j + 1)), ((i, j + 1), (i, j))):
                if (b, a) in edges:
                    del edges[(b, a)]
                else:
                    edges[(a, b)] = True
        nxt = {}
        for a, b in edges:
            if a in nxt:
                raise SystemExit("the zone's edge touches itself at %s" % (a,))
            nxt[a] = b
        self.loops = []
        while nxt:
            start = next(iter(nxt))
            loop = [start]
            p = nxt.pop(start)
            while p != start:
                loop.append(p)
                p = nxt.pop(p)
            n = len(loop)
            keep = []
            for k in range(n):
                d0 = (loop[k][0] - loop[k - 1][0], loop[k][1] - loop[k - 1][1])
                d1 = (loop[(k + 1) % n][0] - loop[k][0], loop[(k + 1) % n][1] - loop[k][1])
                if d0 != d1:
                    keep.append((loop[k][0] * step, loop[k][1] * step))
            self.loops.append(keep)
        self.runs, self.by_line, self.perimeters = [], {}, []
        for li, corners in enumerate(self.loops):
            s = 0.0
            for k in range(len(corners)):
                (ax, ay), (bx, by) = corners[k], corners[(k + 1) % len(corners)]
                ax, ay, bx, by = float(ax), float(ay), float(bx), float(by)
                dx, dy = int(bx > ax) - int(bx < ax), int(by > ay) - int(by < ay)
                length = abs(bx - ax) + abs(by - ay)
                r = {"loop": li, "ax": ax, "ay": ay, "bx": bx, "by": by, "dx": dx, "dy": dy, "len": length, "s0": s,
                     "horizontal": dy == 0, "inside": (-dy, dx)}
                self.runs.append(r)
                key = ("y", round(ay / step)) if r["horizontal"] else ("x", round(ax / step))
                self.by_line.setdefault(key, []).append(len(self.runs) - 1)
                s += length
            self.perimeters.append(s)

    def inside(self, x, y):
        return (math.floor(x / self.step), math.floor(y / self.step)) in self.cells

    def on_edge(self, x, y, tol=1e-4):
        out = []
        for axis, c, along in (("y", y, x), ("x", x, y)):
            k = round(c / self.step)
            if abs(c - k * self.step) > tol:
                continue
            for ri in self.by_line.get((axis, k), ()):
                r = self.runs[ri]
                u = (x - r["ax"]) * r["dx"] + (y - r["ay"]) * r["dy"]
                if -tol <= u <= r["len"] + tol:
                    out.append((ri, min(max(u, 0.0), r["len"])))
        return out

    def face_inside(self, f):
        c = f.calc_center_median()
        for q in [c] + [c.lerp(v.co, 0.5) for v in f.verts]:
            if not self.on_edge(q.x, q.y, 1e-5):
                return self.inside(q.x, q.y)
        return self.inside(c.x, c.y)

    def run_lines(self):
        out = []
        for r in self.runs:
            if r["horizontal"]:
                out.append(("y", r["ay"], min(r["ax"], r["bx"]), max(r["ax"], r["bx"])))
            else:
                out.append(("x", r["ax"], min(r["ay"], r["by"]), max(r["ay"], r["by"])))
        return out


def cap(bm, zone, mat_index):
    """Close the shell again along the zone's edge: each rim loop unrolled along the edge (s, height)
    and filled by a constrained Delaunay triangulation, folded at the zone's corners (Ground edit
    1's caps). A rim that runs right round a piece of the zone (an island kept inside it) comes as
    two rings, top and floor; they are joined into one strip at a corner both pass."""
    rim = [e for e in bm.edges if e.is_boundary and all(zone.on_edge(v.co.x, v.co.y) for v in e.verts)]
    link = {}
    for e in rim:
        for v in e.verts:
            link.setdefault(v, []).append(e)
    if any(len(es) != 2 for es in link.values()):
        raise SystemExit("range north: its cut rim branches")
    seen, loops = set(), []
    for e0 in rim:
        if e0 in seen:
            continue
        loop = [e0.verts[0]]
        e, v = e0, e0.verts[1]
        seen.add(e0)
        while v is not loop[0]:
            loop.append(v)
            e = next(g for g in link[v] if g is not e)
            seen.add(e)
            v = e.other_vert(v)
        loops.append(loop)

    def s_of(v):
        ri, u = zone.on_edge(v.co.x, v.co.y)[0]
        return zone.runs[ri]["loop"], zone.runs[ri]["s0"] + u

    made = 0
    rings = {}
    plain = []
    for loop in loops:
        li = s_of(loop[0])[0]
        per = zone.perimeters[li]
        s = [s_of(loop[0])[1]]
        for v in loop[1:] + loop[:1]:
            d = s_of(v)[1] - s[-1] % per
            d = (d + 0.5 * per) % per - 0.5 * per
            s.append(s[-1] + d)
        wrap = s.pop() - s[0]
        if abs(wrap) > 1e-3:
            rings.setdefault(li, []).append(loop)
        else:
            plain.append((li, loop, s))

    def fill(li, verts, pts, polygon):
        nonlocal made
        per = zone.perimeters[li]
        lo, hi = min(p.x for p in pts), max(p.x for p in pts)
        cons = []
        for r in zone.runs:
            if r["loop"] != li:
                continue
            for k in range(int(math.floor((lo - r["s0"]) / per)) - 1, int(math.ceil((hi - r["s0"]) / per)) + 2):
                sc = r["s0"] + k * per
                at = sorted((i for i in range(len(pts)) if abs(pts[i].x - sc) < 1e-4), key=lambda i: pts[i].y)
                for i, j in zip(at, at[1:]):
                    m = Vector((sc, 0.5 * (pts[i].y + pts[j].y)))
                    inside = False
                    for k2 in range(len(polygon)):
                        p0, p1 = pts[polygon[k2]], pts[polygon[(k2 + 1) % len(polygon)]]
                        if (p0.y > m.y) != (p1.y > m.y) and m.x < p0.x + (m.y - p0.y) * (p1.x - p0.x) / (p1.y - p0.y):
                            inside = not inside
                    if inside:
                        cons.append((i, j))
        out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, cons, [polygon], 1, 1e-6, True)
        idx = []
        for k, ov in enumerate(orig_v):
            src = [i for i in ov if i < len(pts)]
            if not src:
                raise SystemExit("range north: its cap needed a point the rim does not have (s %.2f, y %.2f)" % (out_v[k].x, out_v[k].y))
            idx.append(src[0])
        for tri in out_f:
            vs = [verts[idx[i]] for i in tri]
            if len(set(vs)) < 3:
                continue
            try:
                nf = bm.faces.new(vs)
            except ValueError:
                continue
            nf.material_index = mat_index
            nf.smooth = False
            nf.normal_update()
            c = nf.calc_center_median()
            on = zone.on_edge(c.x, c.y, 1e-3)
            if on:
                best = zone.runs[on[0][0]]
            else:
                best = min(zone.runs, key=lambda r: abs((c.x - r["ax"]) * r["dy"] - (c.y - r["ay"]) * r["dx"])
                           if -1e-3 <= (c.x - r["ax"]) * r["dx"] + (c.y - r["ay"]) * r["dy"] <= r["len"] + 1e-3 else 1e9)
            if nf.normal.x * best["inside"][0] + nf.normal.y * best["inside"][1] < 0.0:
                nf.normal_flip()
            made += 1

    for li, loop, s in plain:
        pts = [Vector((s[k], loop[k].co.z)) for k in range(len(loop))]
        area = sum(pts[k].x * pts[(k + 1) % len(pts)].y - pts[(k + 1) % len(pts)].x * pts[k].y for k in range(len(pts)))
        order = list(range(len(loop))) if area > 0.0 else list(reversed(range(len(loop))))
        fill(li, loop, pts, order)
    ring_report = []
    for li, rs in rings.items():
        per = zone.perimeters[li]
        if len(rs) % 2:
            raise SystemExit("range north: %d rings round one piece of the zone (they should pair, top and floor)" % len(rs))
        rs = sorted(rs, key=lambda lp: -sum(v.co.z for v in lp) / len(lp))
        corners = [r["s0"] for r in zone.runs if r["loop"] == li]
        for A, B in zip(rs[0::2], rs[1::2]):
            sA = {v: s_of(v)[1] % per for v in A}
            sB = {v: s_of(v)[1] % per for v in B}
            sc = None
            for c in corners:
                a = [v for v in A if min(abs(sA[v] - c), abs(sA[v] - c - per), abs(sA[v] - c + per)) < 1e-4]
                b = [v for v in B if min(abs(sB[v] - c), abs(sB[v] - c - per), abs(sB[v] - c + per)) < 1e-4]
                if a and b:
                    sc, a0, b0 = c, a[0], b[0]
                    break
            if sc is None:
                raise SystemExit("range north: its island rings share no corner")

            def key(s_):
                k_ = (s_ - sc) % per
                return 0.0 if k_ > per - 1e-4 else k_
            ua = sorted(A, key=lambda v: (v is not a0, key(sA[v])))
            ub = sorted(B, key=lambda v: (v is not b0, key(sB[v])))
            pa = [Vector((sc + key(sA[v]), v.co.z)) for v in ua] + [Vector((sc + per, a0.co.z))]
            pb = [Vector((sc + key(sB[v]), v.co.z)) for v in ub] + [Vector((sc + per, b0.co.z))]
            verts = ua + [a0] + list(reversed(ub + [b0]))
            pts = pa + list(reversed(pb))
            polygon = list(range(len(pts)))
            area = sum(pts[k].x * pts[(k + 1) % len(pts)].y - pts[(k + 1) % len(pts)].x * pts[k].y for k in range(len(pts)))
            if area < 0:
                polygon.reverse()
            fill(li, verts, pts, polygon)
            ring_report.append({"loop": li, "perimeter_m": round(per, 1), "upper_ring_vertices": len(A), "lower_ring_vertices": len(B)})
    return made, ring_report


def removal_zone(lines, rn_tree, cn_tree, res_tree, box_b):
    """The cells of range north to cut away: where the reserve, coast north or the corridor stand-in
    stands BURY or more over it, eroded by one cell (so the cut lies just inside the overlap, its
    cap hidden), kept islands of under 0.2 ha that poke less than 2 m out added to it."""
    x0, x1, y0, y1 = box_b
    i0, i1 = int(math.floor(x0 / STEP)), int(math.ceil(x1 / STEP))
    j0, j1 = int(math.floor(y0 / STEP)), int(math.ceil(y1 / STEP))
    ni, nj = i1 - i0, j1 - j0
    has = np.zeros((nj, ni), bool)
    bur = np.zeros((nj, ni), bool)
    poke = np.zeros((nj, ni))
    guard = np.zeros((nj, ni), bool)   # never cut: the corridor's ground and its margin (2026-10-09)
    for j in range(nj):
        for i in range(ni):
            X = (i0 + i + 0.5) * STEP
            Y = (j0 + j + 0.5) * STEP
            x, z = X, -Y
            r = top(rn_tree, x, z)
            if r is None:
                continue
            has[j, i] = True
            cov = [t for t in (top(cn_tree, x, z), top(res_tree, x, z)) if t is not None]
            s = lines.hole_floor(x, z)
            if s is not None:
                cov.append(s)
            c = max(cov) if cov else None
            dh = hole_distance(lines, x, z)
            guard[j, i] = in_corridor_mask(x, z) or (dh is not None and dh <= HOLE_MARGIN)
            if c is not None and c > r + BURY and x > -470.0 and (dh is None or dh > HOLE_MARGIN) \
                    and not in_corridor_mask(x, z):
                bur[j, i] = True
            poke[j, i] = r - (c if c is not None else -1e9)
    ok = bur | ~has
    pad = np.pad(ok, 1, constant_values=True)
    er = np.ones_like(ok)
    for dj in (0, 1, 2):
        for di in (0, 1, 2):
            er &= pad[dj:dj + nj, di:di + ni]
    padb = np.pad(bur, 3, constant_values=False)
    near = np.zeros_like(bur)
    for dj in range(7):
        for di in range(7):
            near |= padb[dj:dj + nj, di:di + ni]
    rem = er & near
    # kept islands inside the removal: label kept RN cells
    kept = has & ~rem
    lab = -np.ones((nj, ni), int)
    comps = []
    for j in range(nj):
        for i in range(ni):
            if kept[j, i] and lab[j, i] < 0:
                stack = [(j, i)]
                lab[j, i] = len(comps)
                cells = []
                while stack:
                    a, b = stack.pop()
                    cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        c_, d_ = a + da, b + db
                        if 0 <= c_ < nj and 0 <= d_ < ni and kept[c_, d_] and lab[c_, d_] < 0:
                            lab[c_, d_] = len(comps)
                            stack.append((c_, d_))
                comps.append(cells)
    comps.sort(key=len, reverse=True)
    islands = []
    for cells in comps[1:]:
        a = np.array(cells)
        area = len(cells) * STEP * STEP
        mx = float(poke[a[:, 0], a[:, 1]].max())
        cx = (i0 + a[:, 1].mean() + 0.5) * STEP
        cz = -(j0 + a[:, 0].mean() + 0.5) * STEP
        dropped = area < 2000.0 and (mx < 2.0 or mx > 1e8)
        islands.append({"x": round(cx), "z": round(cz), "area_m2": area, "pokes_out_m": round(mx, 2) if mx < 1e8 else "no cover (a gap at the seam)",
                        "dropped": dropped})
        if dropped:
            keep = ~guard[a[:, 0], a[:, 1]]
            rem[a[keep, 0], a[keep, 1]] = True
    rem &= ~guard
    # cells meeting only at a corner are joined, so the edge is simple loops
    passes = 0
    while True:
        a, b, c, d = rem[:-1, :-1], rem[1:, 1:], rem[:-1, 1:], rem[1:, :-1]
        p1 = a & b & ~c & ~d
        p2 = c & d & ~a & ~b
        if not p1.any() and not p2.any():
            break
        # join a corner-only pair by adding a free cell beside it, or by dropping one of the pair,
        # never by cutting into the guard
        ga, gb, gc, gd = guard[:-1, :-1], guard[1:, 1:], guard[:-1, 1:], guard[1:, :-1]
        rem[:-1, 1:] |= p1 & ~gc
        rem[1:, :-1] |= p1 & gc & ~gd
        rem[1:, 1:] &= ~(p1 & gc & gd)
        q = p2 & ~p1
        rem[:-1, :-1] |= q & ~ga
        rem[1:, 1:] |= q & ga & ~gb
        rem[1:, :-1] &= ~(q & ga & gb)
        passes += 1
        if passes > 5000:
            raise SystemExit("north_shore: the zone's corners would not settle")
    cells = {(int(i0 + i), int(j0 + j)) for j, i in zip(*np.nonzero(rem))}
    stats = {"cells": len(cells), "area_ha": round(len(cells) * STEP * STEP / 1e4, 2),
             "buried_ha": round(float(bur.sum()) * STEP * STEP / 1e4, 2), "islands_kept_or_dropped": islands[:20],
             "main_kept_ha": round(len(comps[0]) * STEP * STEP / 1e4, 2) if comps else 0}
    return cells, stats


# --- building a variant ---------------------------------------------------------------------------

def hole_distance(L, x, z):
    """Plan distance west of the corridor hole (negative inside it), or None outside its rows."""
    if not (L.sw_z[0] <= z <= L.sw_z[-1] and L.se_z[0] <= z <= L.se_z[-1]):
        return None
    xw, _ = L.seam_w(z)
    xe, _ = L.seam_e(z)
    if x > xe:
        return x - xe
    return xw - x


_CMASK = None   # the generator's corridor and tunnel-lid ground, widened by HOLE_MARGIN


def load_corridor_mask(master):
    """`corridor_mask.npz` beside the master (xs, zs, step, mask over Godot x, z): every cell the
    game's road corridor or tunnel lids cover, widened by HOLE_MARGIN, rasterised from their meshes.
    The seam lines read from coast north stop short of the hole's south end at the river mouth."""
    global _CMASK
    path = os.path.join(os.path.dirname(master), "corridor_mask.npz")
    if os.path.exists(path):
        f = np.load(path)
        _CMASK = (f["xs"], f["zs"], float(f["step"]), f["mask"])
    return _CMASK is not None


def in_corridor_mask(x, z):
    if _CMASK is None:
        return False
    xs, zs, st, m = _CMASK
    i, j = int((x - xs[0]) // st), int((z - zs[0]) // st)
    return 0 <= j < m.shape[0] and 0 <= i < m.shape[1] and bool(m[j, i])


def hole_guard(L, x, z, E, T):
    """Range north is the only master ground inside the road corridor's hole, and the generator
    builds the corridor's batters on the master's change there: hold it exactly within HOLE_MARGIN
    of the hole and fade the design in beyond, so the corridor regenerates unchanged."""
    if in_corridor_mask(x, z):
        return E
    d = hole_distance(L, x, z)
    if d is None:
        return T
    return E + (T - E) * float(smoothstep(HOLE_MARGIN, HOLE_MARGIN + HOLE_FADE, d))


def rock_hold(ctx, x, z, E, T):
    """Ground under a seated rock is held: never raised over 40 % of the rock's height above its
    base, never lowered under a tenth of it, faded out between its radius + HOLD_NEAR and
    + HOLD_FAR. Christina laid rocks along the apron/toe seam by hand (2026-09-16); the backshore's
    rise must not bury them, nor the plateau's lowering leave them standing in the air."""
    kd = ctx.get("rock_kd")
    if kd is None:
        from mathutils.kdtree import KDTree
        seated = [r for r in ctx.get("rocks", []) if not r.get("fully_buried") and r.get("buried_frac", 0.0) < 0.8]
        kd = KDTree(max(1, len(seated)))
        for i, r in enumerate(seated):
            kd.insert((r["gx"], r["gz"], 0.0), i)
        kd.balance()
        ctx["rock_kd"], ctx["rock_seated"], ctx["rock_held"] = kd, seated, 0
    if abs(T - E) < 1e-4:
        return T
    T0_ = T
    for _, i, d in kd.find_range((x, z, 0.0), 50.0):
        r = ctx["rock_seated"][i]
        rad = 0.5 * r["size"]
        w = 1.0 - float(smoothstep(rad + HOLD_NEAR, rad + HOLD_FAR, d))
        if w <= 0.0:
            continue
        hi = max(E, r["ymin"] + 0.4 * r["height"])
        lo = min(E, r["ymin"] + 0.1 * r["height"])
        if T > hi:
            T = T - w * (T - hi)
        elif T < lo:
            T = T + w * (lo - T)
    if abs(T - T0_) > 1e-4:
        ctx["rock_held"] += 1
    return T


def build_variant(V, ctx):
    L, D = ctx["lines"], ctx["design"]
    col = bpy.data.collections.new("PROPOSAL_north_shore_%s" % V)
    bpy.context.scene.collection.children.link(col)
    rn0, cn0, sh0 = bpy.data.objects[RN], bpy.data.objects[CN], bpy.data.objects[SHELF]
    rn = copy_object(rn0, "PROPOSAL_%s_%s" % (V, RN), col)
    cn = copy_object(cn0, "PROPOSAL_%s_%s" % (V, CN), col)
    sh = copy_object(sh0, "PROPOSAL_%s_%s" % (V, SHELF), col)
    rep = {"objects": [rn.name, cn.name, sh.name]}
    mats = [m.name for m in rn.data.materials]
    mi = {n: k for k, n in enumerate(mats)}

    # 1. range north: the exporter's triangles; the internal slab in the zone goes (G17)
    me = rn.data
    bm = bmesh.new()
    bm.from_mesh(me)
    as_triangles(bm, me)
    bm.faces.ensure_lookup_table()
    faces_before = len(me.polygons)
    tris_before = sum(len(p.vertices) - 2 for p in me.polygons)
    seen, slab = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        comp, stack = [], [f]
        seen.add(f.index)
        while stack:
            g = stack.pop()
            comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        xs = [v.co.x for g in comp for v in g.verts]
        ys = [-v.co.y for g in comp for v in g.verts]
        zs = [v.co.z for g in comp for v in g.verts]
        if len(comp) < 200 and min(xs) > -350.0 and max(xs) < 100.0 and min(ys) > -980.0 and max(ys) < -550.0 and max(zs) < -4.0:
            slab.extend(comp)
    # The slab is kept (2026-10-09): under the road corridor at the river mouth it is the only
    # master ground, and the generator's corridor follows whatever replaces it. It stays exactly
    # there and is sunk out of sight under the new ground everywhere else (step 3).
    rep["slab_faces_removed"] = 0
    slab_geom = [([v.co.copy() for v in f.verts], f.material_index, f.smooth, f.normal.z) for f in slab]
    slab_verts = set()
    bmesh.ops.delete(bm, geom=slab, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')

    # 2. the top refined on the lattice west of the wedge (and the beach east to the corridor)
    zx0, zx1, zz0, zz1 = FADE_FROM - REFINE, -140.0, -1310.0, -556.0

    def pick(f):
        if f.normal.z < 0.05:
            return False
        c = f.calc_center_median()
        x, z = c.x, -c.y
        return min(v.co.x for v in f.verts) < L.west(z) + 14.0 and max(v.co.x for v in f.verts) > zx0 - 1 and \
            zz0 - 1 < -max(v.co.y for v in f.verts) and -min(v.co.y for v in f.verts) < zz1 + 1
    lines = [("x", float(x), -zz1, -zz0) for x in np.arange(math.ceil(zx0 / REFINE) * REFINE, zx1 + 1e-6, REFINE)]
    lines += [("y", float(-z), zx0, zx1) for z in np.arange(math.ceil(zz0 / REFINE) * REFINE, zz1 + 1e-6, REFINE)]
    bm.normal_update()
    bisect_lines(bm, lines, pick)
    bm.normal_update()
    log("%s: range north refined to %d faces" % (V, len(bm.faces)))

    # 3. heights
    # Every vertex of a face that reaches into the corridor hole or its margin is frozen: holding
    # only the vertices inside left long faces spanning the seam to tilt with their outer corners,
    # which moved range north under the corridor by up to 3 m (2026-10-09).
    def near_hole(x, z):
        if in_corridor_mask(x, z):
            return True
        d = hole_distance(L, x, z)
        return d is not None and d <= HOLE_MARGIN
    frozen = set()
    for f in bm.faces:
        c = f.calc_center_median()
        pts = [(v.co.x, -v.co.y) for v in f.verts] + [(c.x, -c.y)]
        pts += [((a.co.x + b.co.x) / 2.0, -(a.co.y + b.co.y) / 2.0) for a, b in
                ((e.verts[0], e.verts[1]) for e in f.edges)]
        if any(near_hole(x, z) for x, z in pts):
            frozen.update(f.verts)
    rep["vertices_frozen_at_corridor"] = len(frozen)
    moved = []
    moved_set = set()
    dzmax = 0.0
    west_moved = 0
    for v in bm.verts:
        x, z, y = v.co.x, -v.co.y, v.co.z
        if not (zx0 - 2 < x < zx1 + 2 and zz0 - 2 < z < zz1 + 2):
            continue
        if not v.link_faces or any(f.normal.z < 0.05 for f in v.link_faces):
            continue
        if v in frozen or v in slab_verts:
            continue
        T = design_height(D, V, x, z, y)
        T = rock_hold(ctx, x, z, y, T)
        T = hole_guard(L, x, z, y, T)
        if abs(T - y) > 1e-4:
            if x < WEST_LIMIT:
                west_moved += 1
            moved.append((x, z, y, T))
            moved_set.add(v)
            dzmax = max(dzmax, abs(T - y))
            v.co.z = T
    bm.normal_update()
    if slab:
        pass   # the slab goes back, sunk, after the cut (step 6)
    bm.normal_update()
    flipped = sum(1 for f in bm.faces if f.normal.z < -0.05 and all(zx0 < v.co.x < zx1 and zz0 < -v.co.y < zz1 for v in f.verts)
                  and f.material_index != mi.get("distant_range_cliff_blue_gray"))
    rep["range_north_top"] = {"vertices_moved": len(moved), "max_height_change_m": round(dzmax, 2),
                              "raised_max_m": round(max([T - y for _, _, y, T in moved] or [0]), 2),
                              "lowered_max_m": round(-min([T - y for _, _, y, T in moved] or [0]), 2),
                              "vertices_moved_west_of_-431": west_moved, "faces_turned_down": flipped}
    # 4. materials by height, cut along their contours. Each band limit is a horizontal plane the
    #    zone's top faces are bisected on, so a colour edge follows the ground's own contour (a
    #    lattice-cell rule drew them as stair-steps). The rule is the one the untouched landform
    #    follows (sand to the crest, grey shingle to SHINGLE_TOP, the toe bands above), so the
    #    zone's own edge does not show either.
    def zone_top(f):
        if f.normal.z < 0.05:
            return False
        c = f.calc_center_median()
        return zx0 < c.x < zx1 and zz0 < -c.y < zz1
    for h in [CREST + 1.2, SHINGLE_TOP] + [lim for lim, _ in TOE_BANDS[:-1]]:
        fs = [f for f in bm.faces if zone_top(f)]
        es = list({e for f in fs for e in f.edges})
        vs = list({v for f in fs for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=fs + es + vs, dist=1e-4, plane_co=(0.0, 0.0, h), plane_no=(0.0, 0.0, 1.0))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.normal_update()
    banded = 0
    # ground held low under a rock inland of the beach reads as a sand bed under that cluster;
    # a per-face exception there drew jagged grey patches instead (tried 2026-10-09)
    for f in bm.faces:
        if not zone_top(f):
            continue
        c = f.calc_center_median()
        y = c.z
        if y < CREST + 1.2:
            name = M_SAND
        elif y < SHINGLE_TOP:
            name = M_SHINGLE
        else:
            name = next(n for lim, n in TOE_BANDS if y < lim)
        if f.material_index != mi[name]:
            f.material_index = mi[name]
            banded += 1
    rep["faces_rebanded"] = banded
    rep["vertices_held_by_rocks"] = ctx.get("rock_held", 0)

    # 5. coast north's wedge
    cme = cn.data
    corner_n = {}
    cme_normals = cme.corner_normals if hasattr(cme, "corner_normals") else None
    cbm = bmesh.new()
    cbm.from_mesh(cme)
    cbm.verts.ensure_lookup_table()
    cbm.faces.ensure_lookup_table()
    if cme_normals is not None:
        for p in cme.polygons:
            c = p.center
            for li in p.loop_indices:
                v = cme.vertices[cme.loops[li].vertex_index].co
                corner_n[(round(v.x, 3), round(v.y, 3), round(v.z, 3), round(c.x, 2), round(c.y, 2), round(c.z, 2))] = tuple(cme_normals[li].vector)
    col_layer = cbm.loops.layers.float_color.get("Col")
    held, cmoved, cdz = 0, 0, 0.0
    skirt_gone, bank_moved = [], 0
    bank_done = set()
    in_front = {}

    def land_front(z):
        k = round(z * 2.0) / 2.0
        if k not in in_front:
            xw = L.west(z)
            in_front[k] = top(ctx["rn_new_probe"], xw - 3.0, z)
        return in_front[k]

    def edge_height(z):
        xw = L.west(z)
        return top(ctx["rn_new_probe"], xw - 0.25, z)
    foot_cache = {}

    def bank_foot(z):
        """C2's bank foot, laid off the wedge's edge curve rather than each skirt face's own normal,
        its height averaged along the edge, so the foot is one even line (per-face normals and raw
        ground samples made it a row of teeth). Returns the plan normal (x, z) and the foot."""
        def normal(zq):
            dw = (L.west(zq + 2.0) - L.west(zq - 2.0)) / 4.0
            n = math.hypot(1.0, dw)
            return -1.0 / n, dw / n

        def raw(zq):
            k = round(zq / 4.0) * 4.0
            if k not in foot_cache:
                nx_, nz_ = normal(k)
                g = top(ctx["rn_new_probe"], L.west(k) + nx_ * 6.0, k + nz_ * 6.0)
                foot_cache[k] = (g if g is not None else (land_front(k) or SEA + 0.3)) - 0.3
            return foot_cache[k]
        nx, nz = normal(z)
        foot = sum(raw(z + d) for d in (-8.0, -4.0, 0.0, 4.0, 8.0)) / 5.0
        return nx, nz, min(foot, -0.16 - 0.5 / BANK)
    # a probe of the new range north for "land in front"
    tmp = bpy.data.meshes.new("tmp_rn")
    bm.to_mesh(tmp)
    tbm = bmesh.new()
    tbm.from_mesh(tmp)
    ctx["rn_new_probe"] = BVHTree.FromBMesh(tbm)
    tbm.free()
    bpy.data.meshes.remove(tmp)
    wedge_rows = {}
    for v in cbm.verts:
        x, z, y = v.co.x, -v.co.y, v.co.z
        if not (-1310.0 < z < -548.0):
            continue
        xw = L.west(z)
        xs, ys = L.seam_w(z)
        if not (xw - 1.0 <= x <= xs + 0.5) or y < -8.2 or y > ys + 3.0:
            continue
        lf = land_front(z)
        if lf is None or lf < SEA + 0.3:
            continue
        wN = float(smoothstep(NORTH_FADE[0], NORTH_FADE[1], z))
        if wN >= 1.0:
            continue
        dseam = L.seam_distance(x, z)
        ws = float(smoothstep(*SEAM_HOLD, dseam))
        if ws <= 0.0:
            held += 1
            continue
        is_bottom = abs(y + 8.0) < 0.05
        eh = edge_height(z)
        h_e = min((eh if eh is not None else lf) - LAP, ys - 0.5)
        old_e = -0.16
        if V == "C1":
            if is_bottom:
                continue
            new = ys - (ys - y) * (ys - h_e) / max(ys - old_e, 0.3)
        else:
            if not is_bottom:
                continue
            new = None
        if new is not None:
            new = y + (new - y) * ws * (1.0 - wN)
            if abs(new - y) > 1e-4:
                cdz = max(cdz, abs(new - y))
                v.co.z = new
                cmoved += 1
    cbm.normal_update()
    if V == "C1":
        # The west skirt is kept (2026-10-09). Deleted, it left the wedge's edge an open edge lapped
        # under range north, which footprint_test counts; kept, it runs from the lowered edge down to
        # -8 inside range north, hidden, and the surface stays closed above the water.
        pass
    else:
        # the skirt's foot goes out and up into a rocky bank on range north's sand
        for f in cbm.faces:
            if abs(f.normal.z) > 0.2:
                continue
            c = f.calc_center_median()
            x, z = c.x, -c.y
            if not (-1310.0 < z < -548.0) or abs(x - L.west(z)) > 1.5:
                continue
            lf = land_front(z)
            if lf is None or lf < SEA + 0.3:
                continue
            if float(smoothstep(NORTH_FADE[0], NORTH_FADE[1], z)) > 0.5:
                continue
            for v in f.verts:
                if abs(v.co.z + 8.0) < 0.05 and v not in bank_done:
                    bank_done.add(v)
                    if L.seam_distance(v.co.x, -v.co.y) < SEAM_HOLD[0]:
                        held += 1
                        continue
                    vz = -v.co.y
                    nx, nz, foot = bank_foot(vz)
                    run = max(0.5, (-0.16 - foot) * BANK)
                    v.co.x = L.west(vz) + nx * run
                    v.co.y = -(vz + nz * run)
                    cdz = max(cdz, abs(foot + 8.0))
                    v.co.z = foot
                    bank_moved += 1
            for l in f.loops:
                if col_layer is not None:
                    l[col_layer] = (*C_ROCK, 1.0)
        cbm.normal_update()
    # colours of the lowered wedge (C1): sand low, the wedge's own green higher
    if V == "C1" and col_layer is not None:
        for f in cbm.faces:
            c = f.calc_center_median()
            x, z = c.x, -c.y
            if not (-1310.0 < z < -548.0) or not (L.west(z) - 1.0 <= x <= L.seam_w(z)[0] + 0.5):
                continue
            for l in f.loops:
                y = l.vert.co.z
                t = float(smoothstep(-3.0, -0.6, y))
                old = l[col_layer]
                l[col_layer] = (C_SAND[0] + (old[0] - C_SAND[0]) * t, C_SAND[1] + (old[1] - C_SAND[1]) * t,
                                C_SAND[2] + (old[2] - C_SAND[2]) * t, 1.0)
    cfaces_before = len(cme.polygons)
    cbm.to_mesh(cme)
    cbm.free()
    # custom normals: kept where nothing moved, the new surface's own elsewhere
    if corner_n and hasattr(cme, "normals_split_custom_set"):
        try:
            cme.update()
            vn = [tuple(v.normal) for v in cme.vertices]
            newn = []
            for p in cme.polygons:
                c = p.center
                for li in p.loop_indices:
                    vi = cme.loops[li].vertex_index
                    v = cme.vertices[vi].co
                    key = (round(v.x, 3), round(v.y, 3), round(v.z, 3), round(c.x, 2), round(c.y, 2), round(c.z, 2))
                    newn.append(corner_n.get(key, vn[vi]))
            cme.normals_split_custom_set(newn)
        except Exception as exc:  # the proposal's shading only
            log("custom normals not kept: %s" % exc)
    rep["coast_north_wedge"] = {"vertices_moved": cmoved + bank_moved, "max_height_change_m": round(cdz, 2),
                                "skirt_faces_removed": len(skirt_gone), "bank_foot_vertices_moved": bank_moved,
                                "vertices_held_at_seam": held, "faces_before": cfaces_before, "faces_after": len(cme.polygons)}
    cn_tree = bvh(cn)
    log("%s: coast north wedge done %s" % (V, rep["coast_north_wedge"]))

    # 6. the cut: range north's buried east body
    tmp = bpy.data.meshes.new("tmp_rn2")
    bm.to_mesh(tmp)
    tbm = bmesh.new()
    tbm.from_mesh(tmp)
    rn_tree_new = BVHTree.FromBMesh(tbm)
    tbm.free()
    bpy.data.meshes.remove(tmp)
    bb = [v.co for v in bm.verts]
    box_b = (min(v.x for v in bb) - STEP, max(v.x for v in bb) + STEP, min(v.y for v in bb) - STEP, max(v.y for v in bb) + STEP)
    cells, zstats = removal_zone(L, rn_tree_new, cn_tree, ctx["res_tree"], box_b)
    zone = Zone(cells, STEP)
    log("%s: removal zone %s, %d loops, %d runs" % (V, zstats["area_ha"], len(zone.loops), len(zone.runs)))
    bisect_lines(bm, zone.run_lines(), lambda f: True)
    gone = [f for f in bm.faces if zone.face_inside(f)]
    gone_area = sum(f.calc_area() for f in gone if f.normal.z > 0.05)
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    made, rings = cap(bm, zone, mi["distant_range_cliff_blue_gray"])
    open_on_edge = sum(1 for e in bm.edges if e.is_boundary and all(zone.on_edge(v.co.x, v.co.y) for v in e.verts))
    nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    rep["cut"] = dict(zstats, faces_removed=len(gone), top_area_removed_ha=round(gone_area / 1e4, 2), cap_faces=made,
                      island_rings=rings, open_edges_left_on_cut=open_on_edge, edges_with_3_faces=nonman,
                      open_edges_total=sum(1 for e in bm.edges if e.is_boundary))
    # the slab back: unchanged where the corridor reads it, sunk 0.25 m under the finished ground
    # everywhere else, every copy of a corner moved alike so it stays closed
    if slab_geom:
        def tree_of(polys):
            pts, ids, idx = [], [], {}
            for poly in polys:
                row = []
                for co in poly:
                    k = (round(co.x, 4), round(co.y, 4), round(co.z, 4))
                    if k not in idx:
                        idx[k] = len(pts)
                        pts.append(co)
                    row.append(idx[k])
                ids.append(row)
            return BVHTree.FromPolygons(pts, ids)
        bm.normal_update()
        bm.verts.index_update()
        t_slab = tree_of([g[0] for g in slab_geom if g[3] > 0.05])
        t_main = BVHTree.FromPolygons([v.co.copy() for v in bm.verts],
                                      [[v.index for v in f.verts] for f in bm.faces if f.normal.z > 0.05])
        down = Vector((0.0, 0.0, -1.0))
        new_v, sunk = {}, 0
        # a slab face reaching into the corridor guard keeps every corner, as the shell's do
        held_keys = set()
        for poly, _m, _s, _nz in slab_geom:
            pts = [(co.x, -co.y) for co in poly]
            pts += [((poly[i].x + poly[i - 1].x) / 2.0, -(poly[i].y + poly[i - 1].y) / 2.0) for i in range(len(poly))]
            pts.append((sum(co.x for co in poly) / len(poly), -sum(co.y for co in poly) / len(poly)))
            if any(near_hole(x, z) for x, z in pts):
                held_keys.update((round(co.x, 4), round(co.y, 4), round(co.z, 4)) for co in poly)
        for poly, mat, smooth, _nz in slab_geom:
            vs = []
            for co in poly:
                k = (round(co.x, 4), round(co.y, 4), round(co.z, 4))
                if k not in new_v:
                    c = co.copy()
                    if k not in held_keys and not near_hole(c.x, -c.y):
                        hs = t_slab.ray_cast(Vector((c.x, c.y, 1000.0)), down, 3000.0)[0]
                        hm = t_main.ray_cast(Vector((c.x, c.y, 1000.0)), down, 3000.0)[0]
                        if hs is not None and hm is not None and hs.z > hm.z - 0.25:
                            c.z -= hs.z - (hm.z - 0.25)
                            sunk += 1
                    new_v[k] = bm.verts.new(c)
                vs.append(new_v[k])
            nf = bm.faces.new(vs)
            nf.material_index = mat
            nf.smooth = smooth
        rep["slab_vertices_sunk"] = sunk
        rep["slab_faces_kept"] = len(slab_geom)
    bm.to_mesh(me)
    bm.free()
    me.update()
    up_faces = {}
    for p_ in me.polygons:
        for vi in p_.vertices:
            up_faces[vi] = up_faces.get(vi, True) and p_.normal.z > 0.05
    ch = []
    for v in me.vertices:
        if not up_faces.get(v.index):
            continue
        h0 = top(ctx["rn_tree"], v.co.x, -v.co.y)
        if h0 is not None and abs(h0 - v.co.z) > 1e-3:
            ch.append((v.co.x, -v.co.y, v.co.z - h0))
    rep["range_north_top_after_cut"] = {"top_vertices_moved": len(ch), "raised_max_m": round(max([c[2] for c in ch] or [0]), 2),
                                        "lowered_max_m": round(-min([c[2] for c in ch] or [0]), 2),
                                        "moved_west_of_-431": sum(1 for c in ch if c[0] < WEST_LIMIT),
                                        "x_range": [round(min(c[0] for c in ch), 1), round(max(c[0] for c in ch), 1)] if ch else None,
                                        "z_range": [round(min(c[1] for c in ch), 1), round(max(c[1] for c in ch), 1)] if ch else None}
    rep["range_north_faces"] = {"before": faces_before, "after": len(me.polygons), "tris_before": tris_before,
                                "tris_after": sum(len(p.vertices) - 2 for p in me.polygons)}
    log("%s: cut %s" % (V, rep["cut"]))

    # 7. the coast shelf goes where land now covers it
    rn_tree_v = bvh(rn)
    sbm = bmesh.new()
    sbm.from_mesh(sh.data)
    covered = []
    for f in sbm.faces:
        ok = True
        for v in f.verts:
            x, z = v.co.x, -v.co.y
            if not (-480.0 < x < 0.0 and -1260.0 < z < -540.0):
                ok = False
                break
            t = max([t for t in (top(rn_tree_v, x, z), top(cn_tree, x, z)) if t is not None] or [-1e9])
            if t < SEA or t < v.co.z + 0.2:
                ok = False
                break
        if ok:
            covered.append(f)
    sarea = sum(f.calc_area() for f in covered)
    sfb = len(sbm.faces)
    bmesh.ops.delete(sbm, geom=covered, context='FACES')
    bmesh.ops.delete(sbm, geom=[v for v in sbm.verts if not v.link_faces], context='VERTS')
    sbm.to_mesh(sh.data)
    sbm.free()
    rep["coast_shelf"] = {"faces_removed": len(covered), "area_removed_ha": round(sarea / 1e4, 3), "faces_before": sfb,
                          "faces_after": len(sh.data.polygons)}
    col.hide_render = True
    col.hide_viewport = True
    return {"col": col, "rn": rn, "cn": cn, "sh": sh, "rep": rep, "zone": zone}


# --- measuring --------------------------------------------------------------------------------------

def grid_tops(trees, x0, x1, z0, z1, step):
    xs = np.arange(x0, x1 + 1e-6, step)
    zs = np.arange(z0, z1 + 1e-6, step)
    G = {k: np.full((len(zs), len(xs)), np.nan, np.float32) for k in trees}
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            for k, t in trees.items():
                if t is None:
                    continue
                if callable(t):
                    h = t(x, z)
                else:
                    h = top(t, x, z)
                if h is not None:
                    G[k][j, i] = h
    return xs, zs, G


def topmost(G):
    st = np.stack([g for g in G.values()])
    return np.nanmax(np.where(np.isnan(st), -1e9, st), axis=0)


def contour(F, xs, zs, level):
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
            if len(pts) >= 2:
                segs.append((pts[0], pts[1]))
            if len(pts) == 4:
                segs.append((pts[2], pts[3]))
    return segs


def shore_line(Ftop, xs, zs, xr=(-440.0, -172.0)):
    """Per x column, the waterline's z: the first crossing from land to sea going south from z -720."""
    out = {}
    for i, x in enumerate(xs):
        if not (xr[0] <= x <= xr[1]):
            continue
        col = Ftop[:, i]
        best = None
        for j in range(len(zs) - 1):
            if zs[j] < -760.0:
                continue
            if col[j] >= SEA > col[j + 1]:
                best = zs[j] + (col[j] - SEA) / (col[j] - col[j + 1]) * (zs[j + 1] - zs[j])
                break
        out[float(x)] = best
    return out


def section_data(objs, standin, lines):
    trees = {k: bvh(o) for k, o in objs.items()}
    out = {}
    for sname, (axis, c, (a, b)) in SECTIONS.items():
        rows = []
        for u in np.arange(a, b + 1e-6, 1.0):
            x, z = (c, u) if axis == "x" else (u, c)
            row = {"u": float(u), "hits": {k: hits(t, x, z) for k, t in trees.items()}}
            s = lines.standin(x, z)
            if s is not None and -1300.0 <= z <= -540.0:
                row["standin"] = round(s, 3)
            rows.append(row)
        out[sname] = rows
    return out


def rocks_report(rocks, cur_top, var_top):
    out = []
    for r in rocks:
        x, z = r["gx"], r["gz"]
        if not (-480.0 < x < 1200.0 and -1960.0 < z < -530.0):
            continue
        a, b = cur_top(x, z), var_top(x, z)
        if a is None or b is None:
            continue
        d = b - a
        if abs(d) > 1.0:
            state = ("floats %.1f m over the new ground" % (r["ymin"] - b)) if d < 0 else ("buried %.1f m deeper" % d)
            out.append({"name": r["name"], "coll": r["coll"], "x": round(x, 1), "z": round(z, 1), "ground_before": round(a, 2),
                        "ground_after": round(b, 2), "change_m": round(d, 2), "ymin": r["ymin"], "ymax": r["ymax"], "state": state})
    return out


# --- rendering (the seabed proposals' look: water by depth in every material) --------------------------

SHALLOW = (0.30, 0.50, 0.52)
DEEP = (0.34, 0.44, 0.52)
REACH = 12.0
CLARITY = 3.0
SURFACE = 0.25
WATER_GAIN = (2.65, 2.5, 2.25)


def srgb_to_linear(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def render_group():
    ng = bpy.data.node_groups.new("KYT_north_shore_render", "ShaderNodeTree")
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
    wem = N.new("ShaderNodeEmission")
    Lk.new(tint.outputs[2], wem.inputs["Color"])
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
            outs = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output]
            if not outs or not outs[0].inputs["Surface"].links:
                continue
            link = outs[0].inputs["Surface"].links[0]
            src = link.from_socket
            nt.links.remove(link)
            g = nt.nodes.new("ShaderNodeGroup")
            g.node_tree = ng
            nt.links.new(src, g.inputs["Bed"])
            nt.links.new(g.outputs["Shader"], outs[0].inputs["Surface"])


def flat_material(name, colour, emit=True):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if emit:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*srgb_to_linear(colour[:3]), 1.0)
    else:
        em = nt.nodes.new("ShaderNodeBsdfDiffuse")
        em.inputs["Color"].default_value = (*srgb_to_linear(colour[:3]), 1.0)
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def ribbon_object(name, segments, width, z, colour, collection):
    if not len(segments):
        return None
    S = np.asarray(segments, dtype=float)
    a, b = S[:, 0, :], S[:, 1, :]
    d = b - a
    ln = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
    u = d / ln[:, None]
    n = np.column_stack([-u[:, 1], u[:, 0]]) * (width / 2)
    a2, b2 = a - u * (width / 2), b + u * (width / 2)
    m = len(S)
    V = np.concatenate([a2 + n, a2 - n, b2 - n, b2 + n], axis=0)
    V3 = np.column_stack([V, np.full(len(V), z)])
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V3))
    me.vertices.foreach_set("co", V3.ravel())
    me.loops.add(4 * m)
    me.loops.foreach_set("vertex_index", np.column_stack([np.arange(m) + k * m for k in range(4)]).ravel())
    me.polygons.add(m)
    me.polygons.foreach_set("loop_start", np.arange(m) * 4)
    me.update()
    me.materials.append(flat_material(name, colour))
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def standin_object(lines, collection):
    """The corridor, stood in for in the renders only: grey, from its seams to the road."""
    pts, faces = [], []
    idx = {}
    zs = np.arange(-1300.0, -540.0 + 1e-6, 4.0)
    for j, z in enumerate(zs):
        xw, _ = lines.seam_w(z)
        xe, _ = lines.seam_e(z)
        xs = np.linspace(xw + 0.05, xe - 0.05, 24)
        for i, x in enumerate(xs):
            s = lines.standin(x, z)
            idx[(j, i)] = len(pts)
            pts.append((x, -z, (s if s is not None else 0.0) + 0.05))
    for j in range(len(zs) - 1):
        for i in range(23):
            faces.append((idx[(j, i)], idx[(j, i + 1)], idx[(j + 1, i + 1)], idx[(j + 1, i)]))
    me = bpy.data.meshes.new("scratch_corridor_standin")
    me.from_pydata(pts, [], faces)
    me.materials.append(flat_material("scratch_corridor_standin", (0.62, 0.62, 0.60), emit=False))
    ob = bpy.data.objects.new("scratch_corridor_standin", me)
    collection.objects.link(ob)
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
        try:
            world.use_nodes = True
        except Exception:
            pass
        bg = world.node_tree.nodes.get("Background")
        bg.inputs[0].default_value = (*srgb_to_linear((0.62, 0.72, 0.85)), 1.0)
        bg.inputs[1].default_value = 0.9
        sun_data = bpy.data.lights.new("scratch_sun", "SUN")
        sun_data.energy = 3.2
        sun_data.angle = math.radians(1.0)
        self.sun = bpy.data.objects.new("scratch_sun", sun_data)
        # about 13:00, from the south-west, 55 degrees up
        self.sun.rotation_euler = (math.radians(35.0), 0.0, math.radians(-45.0))
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
        log("rendered %s" % name)

    def top_down(self, name, box, px=1400):
        x0, x1, z0, z1 = box
        ex, ez = x1 - x0, z1 - z0
        self.cam_data.type = "ORTHO"
        self.cam_data.ortho_scale = max(ex, ez)
        self.cam_data.sensor_fit = "VERTICAL" if ez > ex else "HORIZONTAL"
        self.cam.location = ((x0 + x1) / 2, -(z0 + z1) / 2, 3000.0)
        self.cam.rotation_euler = (0.0, 0.0, 0.0)
        if ez > ex:
            self.scene.render.resolution_y = px
            self.scene.render.resolution_x = int(round(px * ex / ez))
        else:
            self.scene.render.resolution_x = px
            self.scene.render.resolution_y = int(round(px * ez / ex))
        self.shoot(name)

    def oblique(self, name, eye, aim, lens, px=(1600, 1000)):
        self.cam_data.type = "PERSP"
        self.cam_data.sensor_fit = "HORIZONTAL"
        self.cam_data.lens = lens
        e = Vector((eye[0], -eye[2], eye[1]))
        a = Vector((aim[0], -aim[2], aim[1]))
        self.cam.location = e
        self.cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        self.scene.render.resolution_x, self.scene.render.resolution_y = px
        self.shoot(name)


def render_all(out, ctx, variants, wl):
    scene = bpy.context.scene
    ng = render_group()
    ground = [o for o in bpy.data.collections["Ground"].all_objects if o.type == "MESH"]
    var_objs = [o for v in variants.values() for o in (v["rn"], v["cn"], v["sh"])]
    for v in variants.values():
        v["col"].hide_render = False
    rc = bpy.data.collections.new("scratch_render")
    scene.collection.children.link(rc)
    standin = standin_object(ctx["lines"], rc)
    vme = bpy.data.meshes.new("scratch_void")
    R = 60000.0
    vme.from_pydata([(-R, -R, -300.0), (R, -R, -300.0), (R, R, -300.0), (-R, R, -300.0)], [], [(0, 1, 2, 3)])
    c = srgb_to_linear(SHALLOW) * math.exp(-30.0 / REACH) + srgb_to_linear(DEEP) * (1 - math.exp(-30.0 / REACH))
    vm = bpy.data.materials.new("scratch_void")
    try:
        vm.use_nodes = True
    except Exception:
        pass
    for n in list(vm.node_tree.nodes):
        vm.node_tree.nodes.remove(n)
    o_ = vm.node_tree.nodes.new("ShaderNodeOutputMaterial")
    em = vm.node_tree.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*(c * np.array(WATER_GAIN)), 1.0)
    vm.node_tree.links.new(em.outputs[0], o_.inputs[0])
    vme.materials.append(vm)
    void = bpy.data.objects.new("scratch_void", vme)
    rc.objects.link(void)
    wrap_materials(ground + var_objs, ng)
    keep = {o.name for o in ground + var_objs} | {standin.name, void.name}
    for ob in scene.objects:
        if ob.name not in keep and ob.type in ("MESH", "CURVE", "FONT", "EMPTY", "SURFACE", "META"):
            ob.hide_render = True
    rd = Renderer(out)
    # waterline ribbons for the plans
    ribs = {}
    for k, segs in wl.items():
        colr = (1.0, 1.0, 1.0) if k == "current" else (1.0, 0.25, 0.75)
        ribs[k] = ribbon_object("scratch_waterline_%s" % k, [((a[0], -a[1]), (b[0], -b[1])) for a, b in segs], 2.2 if k == "current" else 1.6,
                                900.0 if k == "current" else 901.0, colr, rc)
        if ribs[k]:
            ribs[k].hide_render = True
    states = ["current"] + list(variants)
    for st in states:
        for ob in ground:
            ob.hide_render = st != "current" and ob.name in (RN, CN, SHELF)
        for k, v in variants.items():
            for ob in (v["rn"], v["cn"], v["sh"]):
                ob.hide_render = k != st
        for vname, (eye, aim, lens) in VIEWS.items():
            rd.oblique("%s_%s_%s.png" % (NAME, st, vname), eye, aim, lens)
        for k, r in ribs.items():
            if r:
                r.hide_render = not (k == "current" or k == st)
        rd.top_down("%s_%s_plan.png" % (NAME, st), PLAN)
        for r in ribs.values():
            if r:
                r.hide_render = True
    return rd.outputs


# --- main -------------------------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--out" not in argv:
        raise SystemExit("north_shore: --out <folder> is required")
    out = os.path.abspath(argv[argv.index("--out") + 1])
    master = os.path.abspath(argv[argv.index("--master") + 1]) if "--master" in argv else DEFAULT_MASTER
    for root in {ROOT, os.path.abspath(os.path.join(os.path.dirname(master), os.pardir, os.pardir))}:
        for forbidden in ("assets", "scenes", "scripts", "tools"):
            f = os.path.join(root, forbidden)
            if os.path.commonpath([out, f]) == f:
                raise SystemExit("north_shore: no output may go under %s" % f)
    if "%sassets%s" % (os.sep, os.sep) in out + os.sep:
        raise SystemExit("north_shore: no output may go under an assets/ folder")
    os.makedirs(out, exist_ok=True)
    scratch = os.path.join(out, "PROPOSAL_%s.blend" % NAME)
    if os.path.abspath(scratch) == master:
        raise SystemExit("north_shore: the scratch copy may not be the master")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    log("opened the scratch copy %s" % scratch)
    rn0, cn0 = bpy.data.objects[RN], bpy.data.objects[CN]
    lines = Lines(cn0, bpy.data.objects[CURVE])
    ctx = {"lines": lines, "rn_tree": bvh(rn0), "res_tree": bvh(bpy.data.objects[RESERVE])}
    ctx["design"] = Design(lines, ctx["rn_tree"])
    D = ctx["design"]
    report = {"master": master, "scratch": scratch, "date": "2026-10-09", "zone_godot_x_z": ZONE,
              "lines": {"wedge_west_edge": [[float(z), float(lines.west(z))] for z in np.arange(-1200.0, -539.0, 50.0)],
                        "seam_wedge": [[float(z), *map(float, lines.seam_w(z))] for z in np.arange(-1200.0, -539.0, 50.0)],
                        "seam_hill": [[float(z), *map(float, lines.seam_e(z))] for z in np.arange(-1200.0, -539.0, 50.0)]},
              "south_shore_new_waterline": [[float(x), round(float(a), 1), round(float(b), 1)] for x, a, b in zip(D.xs[::10], D.zwl[::10], D.zn[::10])],
              "variants": {}}
    log("lines read; west edge at z -1000: %.1f, seam %s" % (lines.west(-1000.0), lines.seam_w(-1000.0)))
    # today's state, measured before anything is built
    gtrees = {o.name: bvh(o) for o in bpy.data.collections["Ground"].all_objects
              if o.type == "MESH" and o.name not in (RN, CN, SHELF, LSHELF)
              and overlaps_zone(o)}
    zone_box = (-470.0, -30.0, -1220.0, -530.0)
    cur_trees = dict(gtrees)
    cur_trees.update({RN: ctx["rn_tree"], CN: bvh(cn0), SHELF: bvh(bpy.data.objects[SHELF]), LSHELF: bvh(bpy.data.objects[LSHELF])})
    cur_trees["corridor_standin"] = lambda x, z: lines.standin(x, z) if -1300.0 <= z <= -540.0 else None
    xs, zs, Gc = grid_tops(cur_trees, *zone_box, 2.0)
    XX, ZZ = np.meshgrid(xs, zs)
    hole = np.zeros(XX.shape, bool)
    for j, z in enumerate(zs):
        a_, b_ = lines.seam_w(z)[0] - 3.0, lines.seam_e(z)[0] + 3.0
        hole[j] = (xs > a_) & (xs < b_)

    def topmost_h(G):
        F = topmost(G)
        return np.where((F < -1e8) & hole, 100.0, F)
    Fc = topmost_h(Gc)
    wl = {"current": contour(np.where(Fc < -1e8, -50.0, Fc), xs, zs, SEA)}
    shore_c = shore_line(Fc, xs, zs)
    sect = {"current": section_data({RN: rn0, CN: cn0, SHELF: bpy.data.objects[SHELF], LSHELF: bpy.data.objects[LSHELF],
                                     RESERVE: bpy.data.objects[RESERVE]}, None, lines)}
    variants = {}
    rocks = json.load(open(ctx_rocks_path(master)))["rocks"] if ctx_rocks_path(master) else []
    log("corridor mask: %s" % ("loaded" if load_corridor_mask(master) else "none beside the master"))
    ctx["rocks"] = rocks
    for V in ("C1", "C2"):
        log("building %s" % V)
        b = build_variant(V, ctx)
        variants[V] = b
        rep = b["rep"]
        vt = dict(gtrees)
        vt.update({RN: bvh(b["rn"]), CN: bvh(b["cn"]), SHELF: bvh(b["sh"]), LSHELF: cur_trees[LSHELF],
                   "corridor_standin": cur_trees["corridor_standin"]})
        _, _, Gv = grid_tops(vt, *zone_box, 2.0)
        Fv = topmost_h(Gv)
        wl[V] = contour(np.where(Fv < -1e8, -50.0, Fv), xs, zs, SEA)
        shore_v = shore_line(Fv, xs, zs)
        moves = [(x, shore_c[x], shore_v.get(x)) for x in shore_c if shore_c[x] is not None and shore_v.get(x) is not None]
        dz = [(x, b_ - a) for x, a, b_ in moves]
        rep["waterline_south_shore"] = {
            "columns": len(dz), "seaward_max_m": round(max([d for _, d in dz] or [0]), 1),
            "seaward_max_at_x": max(dz, key=lambda t: t[1])[0] if dz else None,
            "landward_max_m": round(-min([d for _, d in dz] or [0]), 1),
            "landward_max_at_x": min(dz, key=lambda t: t[1])[0] if dz else None,
            "per_20m": [[x, round(a, 1), round(b_, 1), round(b_ - a, 1)] for x, a, b_ in moves if int(x) % 20 == 0]}
        # overlaps above water in the zone: two objects above water, the lower buried by > 0.3 m
        keys = [RN, CN]
        A = np.stack([Gv[k] for k in keys])
        both = np.all(~np.isnan(A), axis=0) & np.all(np.nan_to_num(A, nan=-99) > SEA, axis=0) & (np.abs(A[0] - A[1]) > 0.3)
        rep["overlap_rn_cn_above_water_ha"] = round(float(both.sum()) * 4.0 / 1e4, 3)
        south = (zs > NORTH_FADE[0])[:, None]
        rep["overlap_rn_cn_above_water_ha_south_of_-1150"] = round(float((both & south).sum()) * 4.0 / 1e4, 3)
        Ac = np.stack([Gc[k] for k in keys])
        bothc = np.all(~np.isnan(Ac), axis=0) & np.all(np.nan_to_num(Ac, nan=-99) > SEA, axis=0) & (np.abs(Ac[0] - Ac[1]) > 0.3)
        rep["overlap_rn_cn_above_water_ha_today"] = round(float(bothc.sum()) * 4.0 / 1e4, 3)
        west = xs < WEST_LIMIT
        dW = np.nan_to_num(Gv[RN][:, west], nan=0) - np.nan_to_num(Gc[RN][:, west], nan=0)
        rep["max_change_west_of_-431_m"] = round(float(np.abs(dW).max()), 4)
        land_c = (Fc > SEA)
        land_v = (Fv > SEA)
        rep["land_gained_ha"] = round(float((land_v & ~land_c).sum()) * 4.0 / 1e4, 3)
        rep["land_lost_ha"] = round(float((~land_v & land_c).sum()) * 4.0 / 1e4, 3)
        # vertices that moved within 2 m of the corridor seam
        near = 0
        for k_, (ob0, ob1) in {"cn": (cn0, b["cn"])}.items():
            co0 = {tuple(round(c_, 3) for c_ in v.co) for v in ob0.data.vertices}
            for v in ob1.data.vertices:
                key = tuple(round(c_, 3) for c_ in v.co)
                if key not in co0 and -1250 < -v.co.y < -540 and lines.seam_distance(v.co.x, -v.co.y) < 2.0:
                    near += 1
        rn_near, rn_new = 0, 0
        rme = b["rn"].data
        upf = {}
        for p_ in rme.polygons:
            for vi in p_.vertices:
                upf[vi] = upf.get(vi, True) and p_.normal.z > 0.05
        old_rn = {tuple(round(c_, 3) for c_ in v.co) for v in rn0.data.vertices}
        for v in rme.vertices:
            if -1320 < -v.co.y < -530 and lines.seam_distance(v.co.x, -v.co.y) < 2.0:
                if upf.get(v.index):
                    h0 = top(ctx["rn_tree"], v.co.x, -v.co.y)
                    if h0 is None or abs(h0 - v.co.z) > 1e-3:
                        rn_near += 1
                elif tuple(round(c_, 3) for c_ in v.co) not in old_rn:
                    rn_new += 1
        rep["vertices_moved_within_2m_of_corridor_seam"] = {"coast_north": near, "range_north_top_moved": rn_near,
                                                            "range_north_new_cut_or_cap_vertices": rn_new}
        def any_top(trees, x, z):
            hs = [(t_(x, z) if callable(t_) else top(t_, x, z)) for t_ in trees.values()]
            hs = [h for h in hs if h is not None]
            return max(hs) if hs else None
        cur_top = lambda x, z: any_top(cur_trees, x, z)
        var_top = lambda x, z: any_top(vt, x, z)
        rr = rocks_report(rocks, cur_top, var_top)
        rep["rocks_moved_ground_over_1m"] = {"count": len(rr), "by_collection": {}, "list": rr}
        rn_v_tree = vt[RN]
        gone_under = {}
        for r in rocks:
            x, z = r["gx"], r["gz"]
            if top(ctx["rn_tree"], x, z) is not None and top(rn_v_tree, x, z) is None:
                k_ = r["coll"]
                gone_under[k_] = gone_under.get(k_, 0) + 1
        rep["rocks_whose_range_north_ground_was_cut_away"] = gone_under
        for r in rr:
            k_ = r["coll"] + (" floats" if r["change_m"] < 0 else " buried")
            rep["rocks_moved_ground_over_1m"]["by_collection"][k_] = rep["rocks_moved_ground_over_1m"]["by_collection"].get(k_, 0) + 1
        sect[V] = section_data({RN: b["rn"], CN: b["cn"], SHELF: b["sh"], LSHELF: bpy.data.objects[LSHELF],
                                RESERVE: bpy.data.objects[RESERVE]}, None, lines)
        report["variants"][V] = rep
        log("%s measured: %s" % (V, json.dumps({k: v for k, v in rep.items() if k not in ("rocks_moved_ground_over_1m",)}, default=str)[:3000]))
        with open(os.path.join(out, "report.json"), "w") as f:
            json.dump(report, f, indent=1, default=str)
    with open(os.path.join(out, "sections.json"), "w") as f:
        json.dump({"sections": {k: list(v) for k, v in SECTIONS.items()}, "data": sect}, f)
    with open(os.path.join(out, "waterlines.json"), "w") as f:
        json.dump({k: [[list(a), list(b)] for a, b in v] for k, v in wl.items()}, f)
    # the scratch copy keeps the variants, hidden; the render setup below is never saved
    for v in variants.values():
        v["col"].hide_render = True
        v["col"].hide_viewport = True
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    log("saved the scratch copy (the master is untouched)")
    if "--no-render" in argv:
        return
    report["renders"] = render_all(out, ctx, variants, wl)
    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)
    log("done")


def overlaps_zone(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
    z0, z1 = min(-v.y for v in bb), max(-v.y for v in bb)
    return not (x1 < -500.0 or x0 > 50.0 or z1 < -1320.0 or z0 > -500.0)


def ctx_rocks_path(master):
    p = os.path.join(os.path.dirname(master), "props_rocks.json")
    return p if os.path.exists(p) else None


# --- sections, drawn with PIL (python3 --plot <folder>) ------------------------------------------------

def plot(folder):
    from PIL import Image, ImageDraw
    d = json.load(open(os.path.join(folder, "sections.json")))
    colours = {RN: (226, 128, 40), CN: (128, 70, 200), SHELF: (190, 180, 30), LSHELF: (60, 190, 190), RESERVE: (60, 160, 70)}
    labels = {RN: "range_north", CN: "coast_north", SHELF: "coast_shelf", LSHELF: "landform_shelf", RESERVE: "mainland_reserve"}
    for sname, (axis, c, (a, b)) in d["sections"].items():
        for st, data in d["data"].items():
            rows = data[sname]
            ys = [h[0] for r in rows for hs in r["hits"].values() for h in hs] + [SEA]
            ylo, yhi = max(min(ys), -18.0), min(max(ys), 60.0 if sname != "z1000" else 150.0)
            ylo, yhi = math.floor(ylo / 5) * 5 - 2, math.ceil(yhi / 5) * 5 + 2
            W, H = 1500, 560
            ml, mr, mt, mb = 70, 20, 60, 50
            sx = (W - ml - mr) / (b - a)
            vert = 2.0 if (yhi - ylo) < 60 else 1.0
            sy = min((H - mt - mb) / (yhi - ylo), sx * vert)
            H = int(mt + mb + sy * (yhi - ylo))
            im = Image.new("RGB", (W, H), (255, 255, 255))
            dr = ImageDraw.Draw(im)
            X = lambda u: ml + (u - a) * sx
            Y = lambda y: mt + (yhi - y) * sy
            dr.rectangle([X(a), Y(SEA), X(b), Y(ylo)], fill=(214, 232, 247))
            dr.line([X(a), Y(SEA), X(b), Y(SEA)], fill=(40, 90, 200), width=2)
            for yv in range(int(ylo), int(yhi) + 1, 5 if yhi - ylo < 80 else 10):
                dr.line([ml - 6, Y(yv), ml, Y(yv)], fill=(0, 0, 0))
                dr.text((ml - 40, Y(yv) - 6), "%d" % yv, fill=(0, 0, 0))
            step_u = 50 if b - a > 400 else 20
            for uv in np.arange(math.ceil(a / step_u) * step_u, b + 1e-6, step_u):
                dr.line([X(uv), H - mb, X(uv), H - mb + 5], fill=(0, 0, 0))
                lab = ("%d,%d" % (c, uv)) if axis == "x" else ("%d,%d" % (uv, c))
                dr.text((X(uv) - 22, H - mb + 8), lab, fill=(0, 0, 0))
            prev_s = None
            for r in rows:
                s = r.get("standin")
                if s is not None and prev_s is not None and int(r["u"]) % 2 == 0:
                    dr.line([X(r["u"] - 1), Y(prev_s[1]), X(r["u"]), Y(s)], fill=(150, 150, 150), width=1)
                prev_s = (r["u"], s) if s is not None else None
            for k, colr in colours.items():
                prev = None
                for r in rows:
                    hs = r["hits"].get(k, [])
                    upn = [h for h in hs if h[1] > 0]
                    t = upn[0][0] if upn else None
                    for h in hs[1:] if upn else hs:
                        if h[0] >= ylo:
                            dr.point((X(r["u"]), Y(h[0])), fill=tuple(int(cc * 0.5) for cc in colr))
                    if t is not None and prev is not None and abs(t - prev[1]) < 40:
                        dr.line([X(prev[0]), Y(prev[1]), X(r["u"]), Y(t)], fill=colr, width=3)
                    elif t is not None and prev is not None:
                        dr.line([X(prev[0]), Y(prev[1]), X(r["u"]), Y(t)], fill=colr, width=1)
                    prev = (r["u"], t) if t is not None else None
            title = "%s  %s: along %s = %d  (vertical x%.1f)" % (NAME, st, axis, c, sy / sx)
            dr.text((ml, 12), title, fill=(0, 0, 0))
            dr.text((ml, 30), "lines: each object's topmost up-facing surface; dots: its other surfaces; grey: corridor stand-in (generator-built, not in the master)",
                    fill=(80, 80, 80))
            lx = W - 220
            for n_, (k, colr) in enumerate(colours.items()):
                dr.rectangle([lx, 50 + n_ * 16, lx + 12, 62 + n_ * 16], fill=colr)
                dr.text((lx + 18, 50 + n_ * 16), labels[k], fill=(0, 0, 0))
            im.save(os.path.join(folder, "%s_%s_section_%s.png" % (NAME, st, sname)))
    print("north_shore: sections drawn")


if __name__ == "__main__":
    if bpy is None:
        if "--plot" in sys.argv:
            plot(os.path.abspath(sys.argv[sys.argv.index("--plot") + 1]))
        else:
            raise SystemExit("north_shore: run in Blender, or with --plot <folder> under python3")
    else:
        main()
