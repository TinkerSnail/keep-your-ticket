"""The headland's sea cliff, its two coves and the shelf round it: proposals on a SCRATCH COPY of
the world terrain master, never on the master itself (2026-10-09, coast/headland catalogue G7, G8,
the headland part of G11, G13, G14).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/blender/world_terrain_proposals_headland_cliff.py -- --out <folder> [--master <blend>]
        [--no-render] [--quick]
    python3 tools/blender/world_terrain_proposals_headland_cliff.py --sections <folder>

The first copies the master into `<folder>/PROPOSAL_headland_cliff.blend` (refuses any output under
assets/, scenes/, scripts/, planning/ or tools/), builds both variants there as hidden objects in
their own collections, measures them, writes `report.json` and `sections.json`, saves the scratch
copy, and only then renders with a scratch camera and sun and render-only materials, which are
never saved. The second (plain Python with PIL, no Blender) draws the cross-sections from
`sections.json`.

Today `terrain_world_coast_north`'s sea cliff is the headland outline extruded straight down: one
tan slab from the harbour round the point and up the north-west face, and the two coves only
notches in the crown. Both variants hang a new face from the cliff top instead, keep every vertex
outside the edit exactly where it is (the corridor's stitched edge, the lighthouse table, the walk's
ground), and carry the coast shelf round the point and under the south face.

- A1, "same line": the cliff top, the plan silhouette and the waterline within 1.5 m of today
  except at the coves. The cliff top is today's outline with its corners rounded and a slow wave,
  never more than 1.45 m off; the face below it is a few fat facets (buttresses and recesses of
  about two metres, a batter, one ledge on each face), a grass lip at the top, rock, a dark wet
  band at the foot. The two coves are bites into the cliff with walls that wrap round: a pocket
  beach in the first, a boulder floor in the second. The waterline moves inland only there.
- A2, "toe and talus": A1's cliff top, face and coves, and at the foot round the point and up the
  north-west face a talus slope onto a wave-cut rock bench that stands 0.6 m out of the water, so a
  fringe of rock shows at the waterline. The waterline moves seaward by the toe's width.
- Both: the coast shelf runs on round the point and under the south face, in place of the radial
  cut at the park box, and stops short of the harbour's breakwater; its outer edge is a curve with
  no straight run over 40 m.

How each shape is made is written beside the code that builds it. Nothing writes to the master, the
GLB, or anything under assets/, scenes/, scripts/, planning/ or tools/.
"""

import json
import math
import os
import re
import shutil
import sys
import time

import numpy as np

try:
    import bmesh
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import delaunay_2d_cdt
    from mathutils.kdtree import KDTree
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
# documentation/ is not tracked, so a worktree reads it from the main tree it hangs off
MAIN = ROOT.split(os.sep + ".claude" + os.sep + "worktrees" + os.sep)[0]
DEFAULT_MASTER = os.path.join(MAIN, "documentation", "screenshots", "coast-headland-2026-10-08", "catalogue",
                              "SCRATCH_master_20261008-2049.blend")
PARK_CSV = os.path.join(MAIN, "documentation", "terrain", "heightfield_park_4m.csv")
SEABED_BLEND = os.path.join(MAIN, "documentation", "screenshots", "seabed-proposals-2026-10-08", "PROPOSAL_seabed.blend")
NAME = "headland_cliff"
COAST = "terrain_world_coast_north"
SHELF = "terrain_coast_shelf"
PROPOSAL_ID = 102  # the `authored_edit` face value the proposal's new faces carry (100 and 101 are the shelves)

# Heights are Godot y (Blender z). The sea (`SEA_LEVEL`, world_terrain_coast_extension.py), the
# coast shelf's wall cut half a metre under it (world_terrain_ground_edit.py `SHELF_UNDER`), and the
# generator's skirt foot inside the park box, where the shelf edit left the wall alone.
SEA = -7.5
CUT = -8.0
SKIRT_Z = -13.5
SHELF_W = 60.0
SHELF_DEPTH = -16.0

# Where the new face runs (Godot x, z): from the south face, just west of the harbour's breakwater
# root (-104, -236), round the point and up the north-west face to just short of the river K2's
# mouth, where the road corridor's and river's hole comes within 7 m of the shore. Each end is the
# today's top-edge vertex nearest these points.
FACE_FROM = (-110.0, -238.6)
FACE_TO = (-133.0, -395.5)
# The shelf stops on the south face here, 12 m west of the breakwater's root, tapering in over
# `SHELF_TAPER` before it so its whole band stands clear of the harbour.
SHELF_STOP = (-116.0, -240.4)
SHELF_TAPER = 70.0
# And it meets today's shelf again on the corridor-side fin, where range north's shore begins (the
# north-shore fix's ground from there on).
SHELF_STITCH_Z = -590.0

# The coves (park_plan `NORTH_COVES`, z -340 and -390). The first stands where planned. The second
# cannot: at z -390 the river's and corridor's hole is 15 m behind the shore (20 m along the inland
# normal), so it sits where the land is deep enough for a bite, its mouth's north corner still
# inside the old notch. Depth is the target; the script takes less where the rim would come within
# `RIM_CLEAR` of a vertex it must keep (the corridor's edge, the table, the walk's ground).
COVES = [
    {"name": "cove_1", "at": (-205.0, -340.0), "half_mouth": 15.0, "depth": 20.0, "floor": "beach",
     "head_y": -6.0, "slope": 0.18},
    {"name": "cove_2", "at": (-140.2, -380.5), "half_mouth": 11.0, "depth": 16.0, "floor": "boulders",
     "head_y": -6.3, "slope": 0.26},
]
RIM_CLEAR = 4.0
# Behind a cove's rim this much of today's crown is rebuilt with it.
COVE_BAND = 3.0
# The walk's ground (the regrade's `terrain_bed_half_width` 2.4 plus `terrain_outer_seaward` 6.0
# from its centreline, park_vertical_controls.tscn) and the lighthouse table (30.6-31.1, P1 and E2)
# with its rim: no vertex there moves.
WALK_KEEP = 6.0
TABLE_FROM_Y = 30.4
TABLE_REACH = 45.0
# The cliff top may move this far from today's line outside the coves (A1's limit is 1.5 m).
TOP_LIMIT = 1.4
# Today's top faces this close to the shore are rebuilt with the new cliff top.
BAND = 4.0
# The new cliff top and face are sampled this often along the shore.
STEP = 2.0

# The harbour (gen_props.gd `_rebuild_harbour`, generator-built, never touched): the breakwater's
# arc, 5 m wide, its head, the quay and the two boats, as plan boxes (centre x, z, size x, z, yaw).
BREAKWATER = [(-104.0, -236.0), (-101.0, -224.0), (-97.0, -213.0), (-93.0, -203.0)]
HARBOUR_BOXES = [("breakwater_head", -92.5, -201.5, 4.0, 4.0, 0.0), ("quay", -83.0, -208.0, 6.0, 16.0, 0.0),
                 ("boat_white", -90.0, -212.0, 2.2, 6.0, 0.3), ("boat_red", -88.5, -224.0, 2.2, 6.0, -0.2)]
# The pier (park_plan PIER_ROOT (SHORE_EDGE -108, PIER_Z 6), PIER_LENGTH 44, PIER_HALF_W 4) and NT-1's
# two datums (park_vertical_controls nt1_top, nt1_low).
PIER_BOX = (-152.0, -108.0, 2.0, 10.0)
NT1_POINTS = [(-58.0, -2.0), (-72.0, -2.0)]
# The seabed session's harbour cove, where their bed keeps 4 m of water (world_terrain_proposals_seabed.py).
SEABED_HARBOUR = [(-70.0, -178.0), (-116.0, -168.0), (-178.0, -212.0), (-176.0, -258.0), (-104.0, -252.0), (-68.0, -224.0)]

# Colours, as the generator writes them (display values; the game and the renders read them so).
GRASS = (0.358, 0.468, 0.308)
ROCK = (0.47, 0.44, 0.39)  # REBUILD_SEA_CLIFF_COLOUR
WET = (0.27, 0.26, 0.245)
TALUS = (0.56, 0.53, 0.48)
BENCH = (0.31, 0.33, 0.28)
SAND = (0.78, 0.72, 0.58)
WET_SAND = (0.62, 0.57, 0.46)
BOULDER = (0.40, 0.38, 0.35)
SEABED = (0.47, 0.44, 0.39)

# The standard views (Godot eye, aim, lens) and the plan box (x0, x1, z0, z1).
VIEWS = {"V1": ((-330.0, 170.0, -60.0), (-230.0, 0.0, -420.0), 35.0),
         "aerial": ((-420.0, 120.0, -150.0), (-200.0, 5.0, -320.0), 35.0),
         "V3": ((-430.0, -4.0, -470.0), (-200.0, 8.0, -330.0), 35.0),
         "V4": ((-40.0, 45.0, -60.0), (-230.0, 5.0, -290.0), 35.0)}
PLAN = (-340.0, -40.0, -480.0, -180.0)
# Sections (Godot): through the point along z -295, across the south face along z -262, and through
# each cove perpendicular to the face (built from the cove's own normal at run time).
SECTIONS = {"point_z295": ((-330.0, -295.0), (-150.0, -295.0)),
            "south_face_z262": ((-330.0, -262.0), (-150.0, -262.0))}

T0 = time.time()


def log(msg):
    print("[%6.1fs] %s" % (time.time() - T0, msg), flush=True)


def g2b(x, z):
    return (x, -z)


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# --- the plan's own numbers ------------------------------------------------------------------

def outline_godot():
    """COAST_NORTH_OUTLINE from scripts/park_plan.gd, as far as the corridor-side fin."""
    text = open(os.path.join(ROOT, "scripts", "park_plan.gd")).read()
    block = re.search(r"const COAST_NORTH_OUTLINE := \[(.*?)\n\]", text, re.S).group(1)
    pts = np.array(re.findall(r"Vector2\((-?[0-9.]+),\s*(-?[0-9.]+)\)", block), dtype=float)
    return pts[: np.nonzero(pts[:, 1] < -1400.0)[0][0] + 1]


def controls():
    """The walk (the approved Path3D, sampled every 0.5 m), P1, E2 and the loop, Godot."""
    text = open(os.path.join(ROOT, "scenes", "world", "park_vertical_controls.tscn")).read()
    raw = re.search(r'id="Curve3D_p1_broad_s"\]\s*_data = \{\s*"points": PackedVector3Array\(([^)]*)\)', text).group(1)
    v = np.array([float(a) for a in raw.split(",")]).reshape(-1, 3, 3)
    hin, hout, pos = v[:, 0], v[:, 1], v[:, 2]
    walk = []
    for i in range(len(pos) - 1):
        p0, p1, p2, p3 = pos[i], pos[i] + hout[i], pos[i + 1] + hin[i + 1], pos[i + 1]
        n = max(2, int(np.linalg.norm(p3 - p0) / 0.5))
        for t in np.linspace(0.0, 1.0, n, endpoint=False):
            walk.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    walk.append(pos[-1])

    def marker(name):
        m = re.search(r'\[node name="%s"[^\]]*\]\s*position = Vector3\(([^)]*)\)' % name, text)
        return tuple(float(a) for a in m.group(1).split(","))
    return np.array(walk), {k: marker(k) for k in ("p1_floor", "e2_floor", "headland_a_loop")}


# --- plan geometry (Blender plan: X = x, Y = -z) ---------------------------------------------

class Polyline:
    def __init__(self, P):
        self.P = np.asarray(P, dtype=float)
        self.D = np.diff(self.P, axis=0)
        self.L = np.linalg.norm(self.D, axis=1)
        self.cum = np.concatenate([[0.0], np.cumsum(self.L)])
        self.length = float(self.cum[-1])

    def project(self, Q):
        """Arc length, distance and side (negative = land, with the outline's own order) of
        each point."""
        Q = np.atleast_2d(np.asarray(Q, dtype=float))
        s_out = np.empty(len(Q))
        d_out = np.empty(len(Q))
        c_out = np.empty(len(Q))
        A, D, L2 = self.P[:-1], self.D, np.maximum(self.L ** 2, 1e-12)
        for a in range(0, len(Q), 4096):
            q = Q[a:a + 4096]
            t = np.clip(((q[:, None, :] - A[None]) * D[None]).sum(-1) / L2, 0.0, 1.0)
            C = A[None] + t[..., None] * D[None]
            d2 = ((q[:, None, :] - C) ** 2).sum(-1)
            k = np.argmin(d2, axis=1)
            r = np.arange(len(q))
            s_out[a:a + 4096] = self.cum[k] + t[r, k] * self.L[k]
            d_out[a:a + 4096] = np.sqrt(d2[r, k])
            c_out[a:a + 4096] = D[k, 0] * (q[:, 1] - A[k, 1]) - D[k, 1] * (q[:, 0] - A[k, 0])
        return s_out, d_out, c_out

    def at(self, s):
        s = np.clip(np.atleast_1d(np.asarray(s, dtype=float)), 0.0, self.length)
        k = np.clip(np.searchsorted(self.cum, s, side="right") - 1, 0, len(self.L) - 1)
        t = (s - self.cum[k]) / np.maximum(self.L[k], 1e-12)
        return self.P[k] + t[:, None] * self.D[k], self.D[k] / np.maximum(self.L[k], 1e-12)[:, None]

    def resample(self, step):
        n = max(2, int(math.ceil(self.length / step)) + 1)
        return self.at(np.linspace(0.0, self.length, n))[0]


def left_normals(P):
    T = np.gradient(P, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1), 1e-12)[:, None]
    return np.column_stack([-T[:, 1], T[:, 0]]), T


def gauss_smooth(P, sigma_n, pin=True):
    """Gaussian smoothing of a polyline's points, sigma in samples, ends pinned."""
    if sigma_n <= 0:
        return P.copy()
    r = int(3 * sigma_n)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_n) ** 2)
    k /= k.sum()
    pad = np.concatenate([np.repeat(P[:1], r, 0), P, np.repeat(P[-1:], r, 0)])
    out = np.stack([np.convolve(pad[:, c], k, mode="valid") for c in range(P.shape[1])], axis=1)
    if pin:
        out[0], out[-1] = P[0], P[-1]
    return out


def point_in_poly(Q, poly):
    Q = np.atleast_2d(Q)
    x, y = Q[:, 0], Q[:, 1]
    inside = np.zeros(len(Q), dtype=bool)
    px, py = poly[:, 0], poly[:, 1]
    j = len(poly) - 1
    for i in range(len(poly)):
        cond = ((py[i] > y) != (py[j] > y))
        xint = (px[j] - px[i]) * (y - py[i]) / np.where(py[j] - py[i] == 0, 1e-12, py[j] - py[i]) + px[i]
        inside ^= cond & (x < xint)
        j = i
    return inside


def seg_distance(Q, P):
    """Distance from each point to an open polyline."""
    Q = np.atleast_2d(Q)
    A, B = P[:-1], P[1:]
    D = B - A
    L2 = np.maximum((D ** 2).sum(1), 1e-12)
    best = np.full(len(Q), np.inf)
    for a in range(0, len(Q), 2048):
        q = Q[a:a + 2048]
        t = np.clip(((q[:, None, :] - A[None]) * D[None]).sum(-1) / L2, 0.0, 1.0)
        C = A[None] + t[..., None] * D[None]
        best[a:a + 2048] = np.sqrt(((q[:, None, :] - C) ** 2).sum(-1).min(1))
    return best


def straight_runs(P, tol=0.25, over=40.0):
    """Douglas-Peucker at `tol`, the simplified runs longer than `over` (Godot x, z)."""
    def dp(a, b):
        if b - a < 2:
            return [a, b]
        A, B = P[a], P[b]
        ab = B - A
        L = np.hypot(*ab)
        d = np.abs(ab[0] * (P[a + 1:b, 1] - A[1]) - ab[1] * (P[a + 1:b, 0] - A[0])) / max(L, 1e-9)
        i = int(np.argmax(d))
        if d[i] > tol:
            left = dp(a, a + 1 + i)
            return left[:-1] + dp(a + 1 + i, b)
        return [a, b]
    idx = dp(0, len(P) - 1)
    runs = []
    for a, b in zip(idx[:-1], idx[1:]):
        L = float(np.hypot(*(P[b] - P[a])))
        if L > over:
            runs.append({"from": [round(float(P[a, 0]), 1), round(float(-P[a, 1]), 1)],
                         "to": [round(float(P[b, 0]), 1), round(float(-P[b, 1]), 1)], "len_m": round(L, 1)})
    return runs, max([float(np.hypot(*(P[b] - P[a]))) for a, b in zip(idx[:-1], idx[1:])] or [0.0])


def knots(seed, length, spacing, lo, hi):
    """Values at irregular knots along a run, linearly interpolated: the facets' plan offsets."""
    rng = np.random.default_rng(seed)
    xs = [0.0]
    while xs[-1] < length:
        xs.append(xs[-1] + spacing * rng.uniform(0.75, 1.3))
    xs = np.array(xs)
    vs = rng.uniform(lo, hi, len(xs))
    return lambda u: np.interp(u, xs, vs), xs


def tone(i, j, lo=0.86, hi=1.1):
    """A facet's tone, the same for the same knot and row band every run."""
    h = math.sin(i * 12.9898 + j * 78.233) * 43758.5453
    return lo + (hi - lo) * (h - math.floor(h))


def scaled(c, f):
    return (min(1.0, c[0] * f), min(1.0, c[1] * f), min(1.0, c[2] * f), 1.0)


def mix(a, b, t):
    t = float(np.clip(t, 0.0, 1.0))
    return tuple(a[k] * (1 - t) + b[k] * t for k in range(3))


def grain(x, y):
    return 1.0 + math.sin(x * 0.37) * math.sin(-y * 0.41) * 0.05


# --- the master's meshes ---------------------------------------------------------------------

def mesh_arrays(me):
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    ls = np.zeros(len(me.polygons), dtype=np.int64)
    lt = np.zeros(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    vi = np.zeros(len(me.loops), dtype=np.int64)
    me.loops.foreach_get("vertex_index", vi)
    if not np.all(lt == 3):
        raise SystemExit("%s is not all triangles" % me.name)
    F = vi.reshape(-1, 3)
    return V, F


def face_normals(V, F):
    P = V[F]
    N = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    A = np.linalg.norm(N, axis=1)
    return N / np.maximum(A, 1e-12)[:, None], A / 2.0


def boundary_vertices(F):
    E = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    u, c = np.unique(E, axis=0, return_counts=True)
    return np.unique(u[c == 1].ravel())


def bvh_of(V, F, mask=None):
    if mask is not None:
        F = F[mask]
    return BVHTree.FromPolygons([Vector(v) for v in V], [tuple(int(i) for i in f) for f in F], all_triangles=True)


def top_at(tree, x, y, start=400.0):
    hit = tree.ray_cast(Vector((x, y, start)), Vector((0.0, 0.0, -1.0)), 2000.0)
    return None if hit[0] is None else hit[0].z


def all_hits(trees, x, y, start=400.0):
    """Every surface the vertical line meets: [(z, up-facing, owner)] from the top."""
    out = []
    for owner, tree in trees.items():
        z = start
        for _ in range(12):
            hit = tree.ray_cast(Vector((x, y, z)), Vector((0.0, 0.0, -1.0)), 2000.0)
            if hit[0] is None:
                break
            out.append((hit[0].z, hit[1].z > 0.0, owner))
            z = hit[0].z - 0.02
    return sorted(out, key=lambda h: -h[0])


# --- the shared plan: the cliff top and the coves ---------------------------------------------

class Plan:
    """Everything both variants share: today's cliff, which of its faces go, the new cliff top."""

    def __init__(self):
        self.ob = bpy.data.objects[COAST]
        self.V, self.F = mesh_arrays(self.ob.data)
        V, F = self.V, self.F
        self.N, self.area = face_normals(V, F)
        up = self.N[:, 2]
        self.top = up > 0.1
        vertical = (np.abs(up) < 0.1) & (self.area > 1e-4)
        self.outline = Polyline(np.array([g2b(x, z) for x, z in outline_godot()]))
        walk, marks = controls()
        self.walk_g = walk
        self.walk = np.column_stack([walk[:, 0], -walk[:, 2]])
        self.marks = marks
        # today's top edge and foot: the vertices the vertical skirt panels hang between
        vv = np.unique(F[vertical].ravel())
        s, d, c = self.outline.project(V[vv, :2])
        near = d < 0.8
        edge = vv[near & (V[vv, 2] > -7.0)]
        foot = vv[near & (V[vv, 2] <= -7.9)]
        se, _, _ = self.outline.project(V[edge, :2])
        sf, _, _ = self.outline.project(V[foot, :2])
        tA = edge[np.argmin(np.hypot(*(V[edge, :2] - np.array(g2b(*FACE_FROM))).T))]
        tB = edge[np.argmin(np.hypot(*(V[edge, :2] - np.array(g2b(*FACE_TO))).T))]
        self.sA = float(se[edge == tA][0])
        self.sB = float(se[edge == tB][0])
        self.tA, self.tB = int(tA), int(tB)
        rng = (se >= self.sA - 1e-6) & (se <= self.sB + 1e-6)
        self.edge_out = edge[~rng]
        order = np.argsort(se[rng])
        self.edge = edge[rng][order]
        self.edge_s = se[rng][order]
        frng = (sf >= self.sA - 0.05) & (sf <= self.sB + 0.05)
        self.foot = foot[frng]
        self.foot_s = sf[frng]
        # the foot straight under each end
        self.fA = int(self.foot[np.argmin(np.hypot(*(V[self.foot, :2] - V[tA, :2]).T))])
        self.fB = int(self.foot[np.argmin(np.hypot(*(V[self.foot, :2] - V[tB, :2]).T))])
        # the corridor's and river's hole (its edge is stitched to the generator's ground) and the
        # mesh's other open edges above the water
        bnd = boundary_vertices(F)
        bnd = bnd[V[bnd, 2] > -7.0]
        self.hole = bnd[~np.isin(bnd, edge)]
        # vertices that must not move: the walk's ground, the table, the hole's edge
        dw = seg_distance(V[:, :2], self.walk)
        p1 = np.array(g2b(marks["p1_floor"][0], marks["p1_floor"][2]))
        e2 = np.array(g2b(marks["e2_floor"][0], marks["e2_floor"][2]))
        dt = np.minimum(np.hypot(*(V[:, :2] - p1).T), np.hypot(*(V[:, :2] - e2).T))
        self.table = (V[:, 2] >= TABLE_FROM_Y) & (dt < TABLE_REACH)
        self.protected = (dw < WALK_KEEP) | self.table
        self.protected[self.hole] = True
        # the walk's ground and the corridor's edge keep their faces; the table's vertices keep
        # their places, but where a cove's band reaches a table triangle (8 m deep there) the
        # triangle is rebuilt round the same vertices
        self.hard = self.protected & ~self.table
        self.top_tree = bvh_of(V, F, self.top)
        self.edge_kd = KDTree(len(self.edge))
        for i, v in enumerate(self.edge):
            self.edge_kd.insert(Vector((V[v, 0], V[v, 1], 0.0)), i)
        self.edge_kd.balance()
        log("plan: face from s %.1f to %.1f (%d top-edge vertices, %d foot), %d protected vertices, %d hole-edge vertices"
            % (self.sA, self.sB, len(self.edge), len(self.foot), int(self.protected.sum()), len(self.hole)))
        self.design_top_line()
        self.choose_faces()

    def height(self, x, y):
        z = top_at(self.top_tree, x, y)
        if z is None:
            _, i, _ = self.edge_kd.find(Vector((x, y, 0.0)))
            z = float(self.V[self.edge[i], 2])
        return z

    # -- the new cliff top
    def design_top_line(self):
        V = self.V
        base = Polyline(V[self.edge, :2])
        self.base = base
        U = base.length
        u = np.linspace(0.0, U, int(U / 0.25) + 1)
        B, _ = base.at(u)
        # the corners rounded: the line smoothed (sigma 7 m), held within the limit
        Bs = gauss_smooth(B, 7.0 / 0.25)
        n0, _ = left_normals(Bs)
        f_end = smoothstep(0.0, 12.0, u) * smoothstep(0.0, 12.0, U - u)
        # no change where the walk is near: its shoreline margin is 8.8 m at x -112 today
        dwalk = seg_distance(B, self.walk)
        f_walk = smoothstep(9.0, 14.0, dwalk)
        # a slow wave along the line, so no side reads straight
        wave = 0.85 * np.sin(2 * np.pi * u / 43.0 + 0.4) + 0.45 * np.sin(2 * np.pi * u / 17.0 + 1.9)
        disp = (Bs - B) + n0 * wave[:, None]
        mag = np.linalg.norm(disp, axis=1)
        disp *= (np.minimum(1.0, TOP_LIMIT / np.maximum(mag, 1e-9)) * f_end * f_walk)[:, None]
        L = B + disp
        n1, _ = left_normals(gauss_smooth(L, 3.0 / 0.25))
        # the coves: bites into the cliff along the inland normal, a rounded U whose sides stand
        # square to the shore at the mouth (a superellipse, power 2.5)
        bite = np.zeros_like(u)
        self.coves = []
        for cv in COVES:
            sc, _, _ = base.project(np.array([g2b(*cv["at"])]))
            uc = float(sc[0])
            depth = self.cove_depth(cv, L, n1, u, uc)
            t = np.clip(np.abs(u - uc) / cv["half_mouth"], 0.0, 1.0)
            b = depth * (1.0 - t ** 2.5) ** (1.0 / 2.5) * (t < 1.0)
            bite = np.maximum(bite, b)
            pc, _ = base.at(uc)
            self.coves.append(dict(cv, u=uc, depth_m=round(depth, 2), centre_b=pc[0].tolist()))
        L = L - n1 * bite[:, None]
        self.top_disp_dense = np.einsum("ij,ij->i", L - B, n1)  # + seaward
        self.bite_dense = bite
        self.u_dense = u
        # resampled by arc length; the ends are today's end vertices exactly
        line = Polyline(L)
        Lr = line.resample(STEP)
        Lr[0], Lr[-1] = V[self.tA, :2], V[self.tB, :2]
        sr, _, _ = line.project(Lr)
        # each sample's place along the old line (for the knots) and its cove, if any
        k = np.clip(np.searchsorted(line.cum, sr) , 0, len(u) - 1)
        self.L = Lr
        self.Lu = u[k]
        self.Lbite = bite[k]
        self.Ltop = self.top_disp_dense[k]
        self.Lcove = np.full(len(Lr), -1)
        for ci, cv in enumerate(self.coves):
            self.Lcove[np.abs(self.Lu - cv["u"]) < cv["half_mouth"]] = ci
        n, _ = left_normals(gauss_smooth(Lr, 1.0))
        self.Ln = n
        self.Lz = np.array([self.height(x, y) for x, y in Lr])
        self.Lz[0], self.Lz[-1] = V[self.tA, 2], V[self.tB, 2]
        outside = self.Lcove < 0
        self.top_shift_max = float(np.abs(self.Ltop[outside]).max())
        log("plan: new cliff top %d points, %.1f m long; outside the coves it moves at most %.2f m; coves %s"
            % (len(Lr), line.length, self.top_shift_max, [(c["name"], c["depth_m"]) for c in self.coves]))

    def cove_depth(self, cv, L, n1, u, uc):
        """The deepest bite, up to the target, whose rim keeps RIM_CLEAR off every vertex that
        must stay."""
        V = self.V
        keep = np.nonzero(self.protected)[0]
        kp = V[keep, :2]
        near = np.hypot(*(kp - L[np.argmin(np.abs(u - uc))]).T) < cv["depth"] + 60.0
        kp = kp[near]
        for depth in np.arange(cv["depth"], 3.0, -0.5):
            t = np.clip(np.abs(u - uc) / cv["half_mouth"], 0.0, 1.0)
            b = depth * (1.0 - t ** 2.5) ** (1.0 / 2.5) * (t < 1.0)
            sel = b > 0.0
            rim = L[sel] - n1[sel] * b[sel, None]
            if not len(kp):
                return float(depth)
            d = np.sqrt(((rim[:, None, :] - kp[None]) ** 2).sum(-1)).min()
            if d >= RIM_CLEAR + COVE_BAND:
                return float(depth)
        return 3.0

    # -- which of today's faces go
    def choose_faces(self):
        V, F = self.V, self.F
        cen = V[F].mean(axis=1)
        # a face goes if any corner lies in the band: the crown's lattice is 8 m deep north of
        # z -325, and a centroid test left whole triangles standing across a cove's rim
        sbv, dv, _ = self.base.project(V[:, :2])
        band_v = np.maximum(BAND + 1.0, np.interp(sbv, self.u_dense, self.bite_dense) + COVE_BAND)
        vin = (dv < band_v) & (sbv > 0.05) & (sbv < self.base.length - 0.05)
        edge_set = np.zeros(len(V), dtype=bool)
        edge_set[self.edge] = True
        inner_edge = edge_set.copy()
        inner_edge[[self.tA, self.tB]] = False
        zone = edge_set.copy()
        zone[self.foot] = True
        prot_face = self.hard[F].any(axis=1)
        touch_out = np.isin(F, self.edge_out).any(axis=1)
        ring = self.top & inner_edge[F].any(axis=1) & ~touch_out
        R = self.top & vin[F].any(axis=1) & ~prot_face & ~touch_out
        R |= ring
        if (ring & prot_face).any():
            bad = np.nonzero(ring & prot_face)[0]
            raise SystemExit("a face on the cliff edge holds a vertex that must stay: %s" % V[F[bad[0]]].tolist())
        skirt = zone[F].all(axis=1) & ~self.top
        # a sliver along the edge whose corners are all edge vertices goes too
        skirt |= zone[F].all(axis=1) & (self.area < 1e-3)
        self.R = np.nonzero(R & ~skirt)[0]
        self.skirt = np.nonzero(skirt)[0]
        # the band's inner boundary: R's edges no other R face shares, less today's edge itself
        E = np.sort(np.concatenate([F[self.R][:, [0, 1]], F[self.R][:, [1, 2]], F[self.R][:, [2, 0]]]), axis=1)
        u_, cnt = np.unique(E, axis=0, return_counts=True)
        bd = u_[cnt == 1]
        rank = {int(v): i for i, v in enumerate(self.edge)}
        outer = np.array([(a in rank and b in rank and abs(rank[a] - rank[b]) == 1) for a, b in bd])
        inner = bd[~outer]
        adj = {}
        for a, b in inner:
            adj.setdefault(int(a), []).append(int(b))
            adj.setdefault(int(b), []).append(int(a))
        ends = [v for v, w in adj.items() if len(w) == 1]
        if sorted(ends) != sorted([self.tA, self.tB]) or any(len(w) > 2 for w in adj.values()):
            bad = [v for v, w in adj.items() if len(w) != 2]
            raise SystemExit("the band's inner boundary is not one chain from end to end: ends %s, odd vertices %s"
                             % (ends, [V[v].round(2).tolist() for v in bad[:8]]))
        chain = [self.tA]
        prev = None
        while chain[-1] != self.tB:
            nxt = [w for w in adj[chain[-1]] if w != prev]
            prev = chain[-1]
            chain.append(nxt[0])
        self.chain = chain
        # table vertices the rebuilt faces enclose: put back exactly where they were
        on_boundary = set(chain) | set(int(v) for v in self.edge)
        inside = np.unique(F[self.R].ravel())
        keep_faces = np.ones(len(F), dtype=bool)
        keep_faces[self.R] = False
        keep_faces[self.skirt] = False
        still_used = np.zeros(len(V), dtype=bool)
        still_used[np.unique(F[keep_faces].ravel())] = True
        self.fixed = [int(v) for v in inside if self.table[v] and not still_used[v] and v not in on_boundary]
        log("plan: %d table vertices inside the rebuilt band are put back where they were" % len(self.fixed))
        log("plan: %d top faces rebuilt, %d skirt faces replaced, inner boundary %d vertices"
            % (len(self.R), len(self.skirt), len(chain)))


# --- building a variant ----------------------------------------------------------------------

class Builder:
    """A variant's coast copy: today's coast_north less the replaced faces, plus the new top band,
    face, coves and (A2) toe."""

    def __init__(self, plan, variant, collection):
        self.plan = plan
        self.variant = variant
        me = plan.ob.data.copy()
        me.name = "PROPOSAL_%s_%s_coast_north" % (NAME, variant)
        self.ob = bpy.data.objects.new(me.name, me)
        self.ob["kyt_proposal"] = "headland cliff %s (2026-10-09), a scratch proposal; never exported" % variant
        collection.objects.link(self.ob)
        self.bm = bmesh.new()
        self.bm.from_mesh(me)
        self.bm.verts.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        self.col = self.bm.loops.layers.float_color["Col"]
        self.uv = self.bm.loops.layers.uv["UVMap"]
        self.tag = self.bm.faces.layers.int.get("authored_edit") or self.bm.faces.layers.int.new("authored_edit")
        self.new_faces = 0
        self.removed_faces = 0
        self.coef = plan_uv(plan.ob.data)

    def vert(self, x, y, z):
        return self.bm.verts.new((float(x), float(y), float(z)))

    def face(self, vs, colour, smooth=True, up=None, out=None):
        """A triangle, dropped if degenerate, turned to face up (or out along a plan normal)."""
        if len({id(v) for v in vs}) < 3:
            return None
        a, b, c = (v.co for v in vs)
        n = (b - a).cross(c - a)
        if n.length < 1e-5:
            return None
        if up is not None and (n.z < 0) == up:
            vs = [vs[0], vs[2], vs[1]]
        elif out is not None and (n.x * out[0] + n.y * out[1]) < 0:
            vs = [vs[0], vs[2], vs[1]]
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = 0
        f.smooth = smooth
        f[self.tag] = PROPOSAL_ID
        for lp in f.loops:
            lp[self.col] = colour if len(colour) == 4 else (*colour, 1.0)
            co = lp.vert.co
            uvv = np.array([co.x, co.y, 1.0]) @ self.coef
            lp[self.uv].uv = (float(uvv[0]), float(uvv[1]))
        self.new_faces += 1
        return f

    def quad(self, a, b, c, d, colour, **kw):
        out = []
        for tri in ((a, b, c), (a, c, d)):
            f = self.face(list(tri), colour, **kw)
            if f is not None:
                out.append(f)
        return out

    def finish(self):
        self.bm.normal_update()
        self.bm.to_mesh(self.ob.data)
        self.bm.free()
        self.ob.data.update()


def plan_uv(me):
    """The mesh's texture coordinates as a plan projection (world_terrain_ground_edit.py's way)."""
    uvl = me.uv_layers["UVMap"]
    fit = []
    for poly in me.polygons:
        if poly.normal.z < 0.3:
            continue
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            fit.append((co.x, co.y, uvl.data[li].uv.x, uvl.data[li].uv.y))
        if len(fit) > 6000:
            break
    Fa = np.array(fit)
    coef, *_ = np.linalg.lstsq(np.c_[Fa[:, 0], Fa[:, 1], np.ones(len(Fa))], Fa[:, 2:], rcond=None)
    return coef


def ring_crossings(P):
    """Pairs of a closed ring's edges that cross (a grid of cells keeps it quick)."""
    n = len(P)
    A, B = P, np.roll(P, -1, axis=0)
    cell = 6.0
    buckets = {}
    for i in range(n):
        x0, y0 = np.minimum(A[i], B[i]) // cell
        x1, y1 = np.maximum(A[i], B[i]) // cell
        for gx in range(int(x0), int(x1) + 1):
            for gy in range(int(y0), int(y1) + 1):
                buckets.setdefault((gx, gy), []).append(i)

    def cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    out = set()
    for ids in buckets.values():
        for a_ in range(len(ids)):
            for b_ in range(a_ + 1, len(ids)):
                i, j = ids[a_], ids[b_]
                if abs(i - j) <= 1 or {i, j} == {0, n - 1}:
                    continue
                if cr(A[j], B[j], A[i]) * cr(A[j], B[j], B[i]) < 0 and cr(A[i], B[i], A[j]) * cr(A[i], B[i], B[j]) < 0:
                    out.add((min(i, j), max(i, j)))
    return sorted(out)


def cdt_fill(builder, ring, fill_step, height, colour, clear=1.0, smooth=True, fixed=()):
    """Triangulate a closed plan ring of BMVerts (constrained Delaunay), with lattice points inside
    at `fill_step` (heights from `height(x, y)`) and `fixed` points (x, y, z) kept exactly, keeping
    the triangles inside the ring."""
    P = np.array([(v.co.x, v.co.y) for v in ring])
    pts = [Vector((float(x), float(y))) for x, y in P]
    zs = [v.co.z for v in ring]
    verts = list(ring)
    n = len(P)
    edges = [(i, (i + 1) % n) for i in range(n)]
    FX = np.array(fixed, dtype=float).reshape(-1, 3)
    for x, y, z in FX:
        pts.append(Vector((float(x), float(y))))
        zs.append(float(z))
        verts.append(None)
    if fill_step:
        x0, y0 = P.min(0)
        x1, y1 = P.max(0)
        gx, gy = np.meshgrid(np.arange(x0 + fill_step / 2, x1, fill_step), np.arange(y0 + fill_step / 2, y1, fill_step))
        G = np.column_stack([gx.ravel(), gy.ravel()])
        if len(G):
            G = G[point_in_poly(G, P)]
        if len(G):
            closed = np.vstack([P, P[:1]])
            G = G[seg_distance(G, closed) > clear]
        if len(G) and len(FX):
            G = G[cloud_distance(G, FX[:, :2]) > clear]
        for x, y in G:
            z = height(x, y)
            pts.append(Vector((float(x), float(y))))
            zs.append(z)
            verts.append(None)
    crossing = ring_crossings(P)
    if crossing:
        dbg = os.environ.get("KYT_DEBUG_DIR")
        if dbg:
            json.dump({"ring": P.tolist()}, open(os.path.join(dbg, "ring_debug.json"), "w"))
        raise SystemExit("the fill's ring crosses itself near %s (Godot x, z)" % [(round(P[i][0], 1), round(-P[i][1], 1)) for i, _ in crossing[:3]])
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, edges, [], 0, 1e-6, True)
    vmap = []
    for k, p in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(pts)]
        if not src:
            dbg = os.environ.get("KYT_DEBUG_DIR")
            if dbg:
                json.dump({"ring": P.tolist(), "z": [v.co.z for v in ring]}, open(os.path.join(dbg, "ring_debug.json"), "w"))
            raise SystemExit("the fill's triangulation added a point at (%.2f, %.2f)" % (p.x, p.y))
        i = src[0]
        if verts[i] is None:
            verts[i] = builder.vert(pts[i].x, pts[i].y, zs[i])
        vmap.append(verts[i])
    made = 0
    for tri in out_f:
        c = np.mean([(out_v[i].x, out_v[i].y) for i in tri], axis=0)
        if not point_in_poly(c[None], P)[0]:
            continue
        vs = [vmap[i] for i in tri]
        cz = sum(v.co.z for v in vs) / 3.0
        f = builder.face(vs, colour(c[0], c[1], cz), smooth=smooth, up=True)
        made += f is not None
    return made


def build_variant(plan, variant, collection):
    """One variant's coast copy and the shelf's inner line it hands on."""
    V = plan.V
    b = Builder(plan, variant, collection)
    bm = b.bm
    BV = bm.verts
    tA, tB, fA, fB = BV[plan.tA], BV[plan.tB], BV[plan.fA], BV[plan.fB]
    chain = [BV[i] for i in plan.chain]
    # today's faces that go
    dead = [bm.faces[int(i)] for i in np.concatenate([plan.R, plan.skirt])]
    b.removed_faces = len(dead)
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    N = len(plan.L)
    U = plan.Lu
    toe = variant == "A2"

    # --- the new cliff top, and the band behind it (constrained Delaunay between today's kept
    # edge of the band and the new line, heights from today's crown)
    top = [tA] + [b.vert(x, y, z) for (x, y), z in zip(plan.L[1:-1], plan.Lz[1:-1])] + [tB]

    def crown(x, y, z):
        return scaled(GRASS, grain(x, y))
    ring = chain + top[-2:0:-1]
    band_faces = cdt_fill(b, ring, 2.0, plan.height, crown, clear=0.9, fixed=[tuple(V[i]) for i in plan.fixed])

    # --- the face. Each column hangs from a cliff-top point along that point's seaward normal;
    # rows at fractions of its height. Plan offsets along the normal come from knots 7-12 m apart
    # (so the face is a few fat facets, each nearly planar), tapered to nothing at both ends, where
    # the face meets today's skirt on its own vertical edge.
    seed = 7
    relA, kxa = knots(seed, U[-1] + 20, 10.0, -1.6, 2.4)
    relB, kxb = knots(seed + 1, U[-1] + 20, 10.0, -1.4, 2.2)
    wl_noise, _ = knots(seed + 2, U[-1] + 20, 13.0, -0.55, 0.65)
    taper = smoothstep(0.0, 10.0, U - U[0]) * smoothstep(0.0, 10.0, U[-1] - U)
    in_cove = plan.Lcove >= 0
    cove_scale = np.where(in_cove, 0.35, 1.0)
    # the walk's margin: within 14 m of it the foot may only move seaward
    dwalk = seg_distance(plan.L, plan.walk)
    # the waterline: today's +-1.45 m, mostly a little seaward so the face has a batter
    wl = np.clip(plan.Ltop + 0.7 + wl_noise(U), -TOP_LIMIT, TOP_LIMIT)
    wl = np.where(dwalk < 14.0, np.maximum(wl, np.maximum(plan.Ltop, 0.0)), wl)
    foot_off = np.where(in_cove, 0.3, wl - plan.Ltop) * taper
    # one ledge on each face: the point's south face and between the point and the first cove
    ledge = np.zeros(N)
    for lo, hi in ((plan.coves[0]["u"] - 75.0, plan.coves[0]["u"] - 28.0), (60.0, 105.0)):
        ledge = np.maximum(ledge, 3.0 * smoothstep(lo, lo + 8.0, U) * smoothstep(hi, hi - 8.0, U))
    ledge *= taper
    # the foot's height: under the water at the shelf's cut; inside the park box east of the shelf's
    # stop, today's skirt depth; on a cove's floor, that floor; on A2's toe, the talus top
    s_stop, _, _ = plan.base.project(np.array([g2b(*SHELF_STOP)]))
    u_stop = float(s_stop[0])
    yfoot = np.where(U < u_stop - 2.0, SKIRT_Z, CUT)
    yfoot = np.where((U >= u_stop - 2.0) & (U < u_stop), SKIRT_Z + (CUT - SKIRT_Z) * (U - (u_stop - 2.0)) / 2.0, yfoot)
    yfoot[0] = V[plan.fA, 2]
    yfoot[-1] = V[plan.fB, 2]
    for ci, cv in enumerate(plan.coves):
        m = plan.Lcove == ci
        frac = np.clip(plan.Lbite[m] / max(cv["depth_m"], 1e-6), 0.0, 1.0) ** 1.5
        yfoot[m] = CUT + (cv["head_y"] - CUT) * frac
    # A2's toe weight: round the point and up the north-west face, fading out towards the harbour,
    # into each cove's mouth and at the river's end
    s_point, _, _ = plan.base.project(np.array([g2b(-242.0, -295.0)]))
    u_point = float(s_point[0])
    tau = np.zeros(N)
    if toe:
        tau = smoothstep(u_point - 95.0, u_point - 60.0, U) * smoothstep(U[-1] - 4.0, U[-1] - 22.0, U)
        for cv in plan.coves:
            tau *= 1.0 - smoothstep(cv["half_mouth"] + 20.0, cv["half_mouth"] + 1.0, np.abs(U - cv["u"]))
        tau[in_cove] = 0.0
    talus_top, _ = knots(seed + 3, U[-1] + 20, 11.0, -5.3, -4.2)
    bench_w, _ = knots(seed + 4, U[-1] + 20, 14.0, 1.5, 3.5)
    lump, _ = knots(seed + 5, U[-1] + 20, 5.0, 0.0, 0.8)
    yt = talus_top(U)
    yfoot = np.where(tau > 0, CUT + tau * (yt - CUT), yfoot)

    rows_t = [0.0, None, 0.38, 0.56, 0.60, None, 1.0]
    cols = []
    for j in range(N):
        x, y = plan.L[j]
        n = plan.Ln[j]
        ztop = plan.Lz[j]
        H = ztop - yfoot[j]
        t_lip = min(0.3, 1.1 / max(H, 1e-3))
        y_wet = max(yfoot[j] + 0.3, -6.2)
        t_wet = float(np.clip((ztop - y_wet) / max(H, 1e-3), 0.62, 0.97))
        ts = [0.0, t_lip, 0.38, 0.56, 0.60, t_wet, 1.0]
        tp = taper[j] * cove_scale[j]
        offs = [0.0, -0.3 * taper[j],
                tp * relA(U[j]) + foot_off[j] * 0.38,
                tp * relB(U[j]) + foot_off[j] * 0.56 - ledge[j] / 2.0,
                tp * relB(U[j]) + foot_off[j] * 0.60 + ledge[j] / 2.0,
                foot_off[j] - 0.15 * taper[j],
                foot_off[j]]
        col = []
        for r, (t, o) in enumerate(zip(ts, offs)):
            z = ztop - t * H
            if r == 0:
                col.append(top[j])
            elif j in (0, N - 1) and r == 6:
                col.append(fA if j == 0 else fB)
            else:
                col.append((x + n[0] * o, y + n[1] * o, z))
        cols.append(col)
    # the end columns lie on today's skirt edges: split those edges so the new face shares them
    for j, (tv, fv) in ((0, (tA, fA)), (N - 1, (tB, fB))):
        e = next((e for e in tv.link_edges if fv in e.verts), None)
        col = cols[j]
        cur = tv
        for r in range(1, 6):
            z = col[r][2]
            if e is None:
                col[r] = b.vert(*col[r])
                continue
            fac = (cur.co.z - z) / max(cur.co.z - fv.co.z, 1e-6)
            ne, nv = bmesh.utils.edge_split(e, cur, float(np.clip(fac, 1e-4, 1 - 1e-4)))
            nv.co.z = z
            col[r] = nv
            e = next(ed for ed in nv.link_edges if fv in ed.verts)
            cur = nv
    for j in range(1, N - 1):
        cols[j] = [cols[j][0]] + [b.vert(*p) for p in cols[j][1:]]
    # face colours: grass lip (the lid), rock facets by knot and row band, the wet band at the
    # foot. A ledge's tread is rock with grass in random clumps of 2-6 m, never a running band
    # (Christina dislikes straight bands on greenery)
    ka = np.searchsorted(kxa, U)
    clump_rng = np.random.default_rng(seed + 9)
    clump = np.zeros(N, dtype=bool)
    j = 0
    while j < N:
        run = int(clump_rng.integers(1, 4))
        clump[j:j + run] = clump_rng.random() < 0.4
        j += run
    for j in range(N - 1):
        for r in range(6):
            if r == 0:
                c = GRASS
            elif r == 5:
                c = WET
            elif r == 3 and min(ledge[j], ledge[j + 1]) > 1.2:
                c = scaled(GRASS, 0.92) if clump[j] else scaled(ROCK, 1.12)
            else:
                c = scaled(ROCK, tone(int(ka[j]), r))
            b.quad(cols[j][r], cols[j + 1][r], cols[j + 1][r + 1], cols[j][r + 1], c, smooth=False)
    foot = [cols[j][6] for j in range(N)]

    # --- the coves' floors: between the wall's foot (the U) and a chord across the mouth at the
    # shelf's cut, a heightfield falling from the head at the floor's own slope, flat at the cut
    # beyond. The first is a pocket beach, the second a boulder floor (fat lumps).
    chords = {}
    cove_report = []
    for ci, cv in enumerate(plan.coves):
        js = np.nonzero(plan.Lcove == ci)[0]
        ja, jb = int(js[0]) - 1, int(js[-1]) + 1
        U_foot = [foot[j] for j in range(ja, jb + 1)]
        A2d = np.array([(v.co.x, v.co.y) for v in U_foot])
        a, c_ = A2d[0], A2d[-1]
        L_ch = float(np.hypot(*(c_ - a)))
        nch = max(2, int(L_ch / 2.0))
        chord = [b.vert(*(c_ + (a - c_) * k / nch), CUT) for k in range(1, nch)]
        chords[ci] = (ja, jb, chord)
        ys = np.array([v.co.z for v in U_foot])
        rng = np.random.default_rng(31 + ci)
        bumps = []
        if cv["floor"] == "boulders":
            cx0, cy0 = A2d.min(0)
            cx1, cy1 = A2d.max(0)
            for _ in range(26):
                bumps.append((rng.uniform(cx0, cx1), rng.uniform(cy0, cy1), rng.uniform(0.5, 1.0), rng.uniform(1.4, 2.6)))

        def floor_h(x, y, A2d=A2d, ys=ys, cv=cv, bumps=bumps):
            d = np.hypot(A2d[:, 0] - x, A2d[:, 1] - y)
            k = int(np.argmin(d))
            h = max(CUT, ys[k] - cv["slope"] * d[k])
            for bx, by, amp, rad in bumps:
                h += amp * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (rad * rad)) * (h > CUT + 0.05)
            return min(h, ys[k])

        def floor_colour(x, y, z, cv=cv):
            gr = grain(x, y)
            if cv["floor"] == "beach":
                c = SAND if z > -6.9 else (WET_SAND if z > SEA - 0.15 else mix(WET_SAND, SEABED, (SEA - z) / 0.5))
            else:
                c = mix(BOULDER, scaled(BOULDER, 1.25), (z - CUT) / 2.0) if z > SEA else mix(WET, SEABED, (SEA - z) / 0.5)
            return scaled(c, gr)
        ring = U_foot + chord
        made = cdt_fill(b, ring, 1.8, floor_h, floor_colour, clear=0.7, smooth=(cv["floor"] == "beach"))
        cove_report.append({"name": cv["name"], "floor": cv["floor"], "faces": made, "mouth_m": round(L_ch, 1)})

    # --- A2's toe: from the face's foot (the talus top) a talus slope to a wave-cut bench 0.6 m out
    # of the water, 2-5.5 m wide, and a lip down to the shelf's cut, all scaled by the toe weight
    # so it grows out of nothing at its ends. The talus carries lumps, so it reads as broken rock.
    shelf_line = []
    toe_outer = list(foot)
    if toe:
        nt, _ = left_normals(gauss_smooth(plan.L, 4.0))
        yb = -6.9
        prof = []
        for j in range(N):
            w_t = (yt[j] - yb) / 0.75
            w_b = bench_w(U[j])
            prof.append([(0.0, yt[j]), (0.5 * w_t, 0.5 * (yt[j] + yb) + lump(U[j]) * 0.6), (w_t, yb),
                         (w_t + w_b, yb - 0.25), (w_t + w_b + 1.3, CUT)])
        trows = []
        for j in range(N):
            if tau[j] <= 1e-3:
                trows.append([foot[j]] * 5)
                continue
            fx, fy = foot[j].co.x, foot[j].co.y
            col = [foot[j]]
            for d, h in prof[j][1:]:
                dd = d * tau[j]
                col.append(b.vert(fx + nt[j][0] * dd, fy + nt[j][1] * dd, CUT + tau[j] * (h - CUT)))
            trows.append(col)
        for j in range(N - 1):
            if tau[j] <= 1e-3 and tau[j + 1] <= 1e-3:
                continue
            for r in range(4):
                c = scaled(TALUS, tone(int(ka[j]) + 50, r)) if r < 2 else (BENCH if r == 2 else WET)
                b.quad(trows[j][r], trows[j + 1][r], trows[j + 1][r + 1], trows[j][r + 1], c, smooth=False, up=True)
        toe_outer = [trows[j][4] for j in range(N)]

    # --- the shelf's inner line: the foot (A1) or the toe's outer edge (A2), the chord across each
    # cove's mouth, from the shelf's stop on the south face to the face's north end
    j0 = int(np.argmin(np.abs(U - u_stop)))
    j = j0
    while j < N:
        hit = [ci for ci, (ja, jb, _) in chords.items() if ja == j]
        if hit:
            ja, jb, chord = chords[hit[0]]
            shelf_line.append(toe_outer[ja].co.copy())
            shelf_line.extend(v.co.copy() for v in reversed(chord))
            j = jb
            continue
        shelf_line.append(toe_outer[j].co.copy())
        j += 1
    b.finish()
    # flat-shaded facets meet the smooth crown on a sharp edge
    me = b.ob.data
    report = {"faces_removed": b.removed_faces, "faces_added": b.new_faces, "band_faces": band_faces,
              "coves": cove_report, "triangles_before": len(plan.F), "triangles_after": len(me.polygons),
              "vertices_before": len(V), "vertices_after": len(me.vertices)}
    return b.ob, np.array([(p.x, p.y) for p in shelf_line]), report


# --- the shelf --------------------------------------------------------------------------------

def shelf_depth(d):
    """The coast shelf's profile (world_terrain_ground_edit.py `coast_shelf`): from the cut at the
    wall to SHELF_DEPTH at SHELF_W out, steepest at the wall."""
    t = np.clip(np.asarray(d, dtype=float) / SHELF_W, 0.0, 1.0)
    return CUT + (SHELF_DEPTH - CUT) * (1.0 - (1.0 - t) ** 2)


def build_shelf(plan, variant, inner, collection):
    """A copy of terrain_coast_shelf with the headland's part rebuilt: from the variant's inner line
    round the point and under the south face, and on north along the corridor-side fin to where it
    meets today's shelf again; the outer edge a curve."""
    src = bpy.data.objects[SHELF]
    me = src.data.copy()
    me.name = "PROPOSAL_%s_%s_coast_shelf" % (NAME, variant)
    ob = bpy.data.objects.new(me.name, me)
    ob["kyt_proposal"] = "coast shelf for headland cliff %s (2026-10-09), a scratch proposal; never exported" % variant
    collection.objects.link(ob)
    SV, SF = mesh_arrays(me)
    V = plan.V
    # on north along the fin: today's foot vertices from the face's end to the stitch
    fin = plan.outline
    cand = np.nonzero((np.abs(V[:, 2] - CUT) < 0.05))[0]
    s, d, _ = fin.project(V[cand, :2])
    s_tb, _, _ = fin.project(V[[plan.fB], :2])
    s_end, _, _ = fin.project(np.array([g2b(-150.0, SHELF_STITCH_Z)]))
    sel = (d < 0.8) & (s > s_tb[0] + 0.5) & (s <= s_end[0])
    fin_pts = V[cand[sel]][np.argsort(s[sel])]
    # snap the stitch to one of today's shelf vertices on its inner edge
    sv_inner = np.nonzero(np.abs(SV[:, 2] - CUT) < 0.02)[0]
    last = fin_pts[-1]
    kk = sv_inner[np.argmin(np.hypot(*(SV[sv_inner, :2] - last[:2]).T))]
    fin_pts = fin_pts[:-1]
    Sh = np.vstack([inner, fin_pts[:, :2], SV[kk, :2][None]])
    # drop near-duplicates (the chord's ends meet the foot)
    keep = np.concatenate([[True], np.hypot(*np.diff(Sh, axis=0).T) > 0.3])
    Sh = Sh[keep]
    line = Polyline(Sh)
    sA = line.cum
    S = sA[-1]
    # rows out along normals of the heavily smoothed line (sigma 30 m), so the coves and the
    # river's corner do not fold the band; the first rows bend from the true line to the smooth one
    step = np.median(line.L)
    Shs = gauss_smooth(Sh, 30.0 / max(step, 0.5))
    ns, _ = left_normals(gauss_smooth(Sh, 30.0 / max(step, 0.5)))
    # the outer edge: a slow undulation of the width (two waves), none at the stitch, tapering in to
    # the wall at the harbour stop
    wave = 1.0 + (0.13 * np.sin(2 * np.pi * sA / 150.0 + 0.7) + 0.07 * np.sin(2 * np.pi * sA / 61.0 + 2.3)
                  + 0.04 * np.sin(2 * np.pi * sA / 37.0 + 1.1)) * smoothstep(0.0, 30.0, S - sA)
    W = SHELF_W * wave * smoothstep(0.0, SHELF_TAPER, sA)
    D = [0.0, 3.0, 8.0, 15.0, 25.0, 40.0]
    beta = [0.0, 0.35, 0.75, 1.0, 1.0, 1.0, 1.0]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    col = bm.loops.layers.float_color["Col"]
    uvl = bm.loops.layers.uv["UVMap"]
    tag = bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
    coef = plan_uv(bpy.data.objects["terrain_world_mainland_reserve"].data)
    # today's headland shelf goes: every face whose centroid lies before the stitch along the coast
    cen = SV[SF].mean(axis=1)
    sc, dc, cc = fin.project(cen[:, :2])
    s_kk, _, _ = fin.project(SV[[kk], :2])
    n_kk = ns[-1]
    along = (cen[:, 0] - SV[kk, 0]) * n_kk[1] - (cen[:, 1] - SV[kk, 1]) * n_kk[0]
    gx, gz = cen[:, 0], -cen[:, 1]
    region = (gx > -380) & (gx < -40) & (gz > -660) & (gz < -150) & (dc < 90.0)
    dead_idx = np.nonzero(region & (along < 0.0))[0]
    bmesh.ops.delete(bm, geom=[bm.faces[int(i)] for i in dead_idx], context="FACES")
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    # the band's vertices
    nrow = 7
    grid = []
    for j in range(len(Sh)):
        colv = []
        w = W[j]
        k = min(1.0, w / SHELF_W)
        last_o = 0.0
        for r in range(nrow):
            if r == 0:
                dist = 0.0
            elif r < 6:
                dist = D[r] * k
            else:
                dist = w
            base = Sh[j] * (1 - beta[r] * k) + Shs[j] * beta[r] * k
            p = base + ns[j] * dist
            # each row stands seaward of the one before along the normal, so no quad folds
            o = float((p - Sh[j]) @ ns[j])
            if r > 0 and o < last_o + 0.6 * k:
                p = p + ns[j] * (last_o + 0.6 * k - o)
                o = last_o + 0.6 * k
            last_o = o
            colv.append((p[0], p[1], 0.0))
        grid.append(colv)
    # rows further out are relaxed along their own length only (ends held), so columns that
    # converge on a bay corner spread out again without the row shrinking off a point; then each
    # row is held seaward of the one before; each point's depth is the profile at its distance to
    # the line
    G = np.array(grid, dtype=float)
    for r, iters in zip(range(1, nrow), (6, 10, 14, 18, 22, 26)):
        P = G[:, r, :2].copy()
        for _ in range(iters):
            T = P[2:] - P[:-2]
            T /= np.maximum(np.linalg.norm(T, axis=1), 1e-9)[:, None]
            Lp = 0.5 * (P[:-2] + P[2:]) - P[1:-1]
            P[1:-1] += 0.6 * (Lp * T).sum(1)[:, None] * T
        G[:, r, :2] = P
    for j in range(len(Sh)):
        k = min(1.0, W[j] / SHELF_W)
        last_o = 0.0
        for r in range(1, nrow):
            o = float((G[j, r, :2] - Sh[j]) @ ns[j])
            if o < last_o + 0.6 * k:
                G[j, r, :2] += ns[j] * (last_o + 0.6 * k - o)
                o = last_o + 0.6 * k
            last_o = o
    dist = seg_distance(G[:, :, :2].reshape(-1, 2), Sh).reshape(len(Sh), nrow)
    G[:, :, 2] = shelf_depth(dist)
    G[:, 0, 2] = CUT
    grid = [[tuple(G[j, r]) for r in range(nrow)] for j in range(len(Sh))]
    # the stitch column takes today's vertices where it falls on them
    old_list = list(bm.verts)
    old_kd = KDTree(len(old_list))
    for i, v in enumerate(old_list):
        old_kd.insert(v.co, i)
    old_kd.balance()
    verts = []
    for j, colv in enumerate(grid):
        row = []
        for r, p in enumerate(colv):
            if j == len(grid) - 1:
                co, idx, dist = old_kd.find(Vector(p))
                if dist < 1.2 and old_list[idx].is_valid and old_list[idx].link_faces:
                    row.append(old_list[idx])
                    continue
            if r > 0 and np.hypot(p[0] - colv[0][0], p[1] - colv[0][1]) < 0.05:
                row.append(row[0])
                continue
            row.append(bm.verts.new(p))
        verts.append(row)

    def colour(x, y, z):
        g = grain(x, y)
        return (SEABED[0] * g, SEABED[1] * g, SEABED[2] * g, 1.0)
    made = 0
    flips = 0
    flip_at = []
    for j in range(len(verts) - 1):
        for r in range(nrow - 1):
            a, b_, c, d_ = verts[j][r], verts[j + 1][r], verts[j + 1][r + 1], verts[j][r + 1]
            for tri in ((a, b_, c), (a, c, d_)):
                if len({id(v) for v in tri}) < 3:
                    continue
                n = (tri[1].co - tri[0].co).cross(tri[2].co - tri[0].co)
                if n.length < 1e-6:
                    continue
                vs = list(tri)
                if n.z < 0:
                    vs = [vs[0], vs[2], vs[1]]
                    flips += 1
                    flip_at.append([round(float(tri[0].co.x), 1), round(float(-tri[0].co.y), 1)])
                try:
                    f = bm.faces.new(vs)
                except ValueError:
                    continue
                f.smooth = True
                f[tag] = PROPOSAL_ID
                for lp in f.loops:
                    co = lp.vert.co
                    lp[col] = colour(co.x, co.y, co.z)
                    uv = np.array([co.x, co.y, 1.0]) @ coef
                    lp[uvl].uv = (float(uv[0]), float(uv[1]))
                made += 1
    # the gap between the band's last column and today's shelf, triangulated
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    gap = 0
    lastcol = verts[-1]
    opened = [e for e in bm.edges if e.is_boundary and e.is_valid and all(v.co.z < CUT + 0.01 for v in e.verts)]
    # the open edges of today's shelf next to the last column, not on its true outer or inner edge
    lc = np.array([(v.co.x, v.co.y) for v in lastcol])
    near = []
    for e in opened:
        m = (e.verts[0].co.xy + e.verts[1].co.xy) / 2
        if seg_distance(np.array([[m.x, m.y]]), lc)[0] < 12.0 and not any(v in lastcol for v in e.verts if False):
            near.append(e)
    # chain the edges whose both ends were inside today's shelf (not on its inner or outer edge)
    ends_inner = {v for e in near for v in e.verts if abs(v.co.z - CUT) < 0.02}
    cand = [e for e in near if not all(abs(v.co.z - CUT) < 0.02 for v in e.verts)
            and not all(abs(v.co.z - SHELF_DEPTH) < 0.02 for v in e.verts)
            and not all(v in lastcol for v in e.verts)]
    adj = {}
    for e in cand:
        a, c = e.verts
        adj.setdefault(a, []).append(c)
        adj.setdefault(c, []).append(a)
    ends = [v for v, w in adj.items() if len(w) == 1]
    stitch_note = "no gap"
    if len(ends) == 2:
        start = min(ends, key=lambda v: abs(v.co.z - CUT))
        ch = [start]
        prev = None
        while True:
            nxt = [w for w in adj[ch[-1]] if w is not prev]
            if not nxt:
                break
            prev = ch[-1]
            ch.append(nxt[0])
        ring = []
        for v in lastcol:
            if not ring or ring[-1] is not v:
                ring.append(v)
        tail = list(reversed(ch))
        if tail and tail[0] is ring[-1]:
            tail = tail[1:]
        if tail and tail[-1] is ring[0]:
            tail = tail[:-1]
        ring.extend(tail)
        P = np.array([(v.co.x, v.co.y) for v in ring])
        pts = [Vector((float(x), float(y))) for x, y in P]
        n = len(pts)
        out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, [(i, (i + 1) % n) for i in range(n)], [], 0, 1e-6, True)
        for tri in out_f:
            src = [orig_v[i][0] if orig_v[i] else None for i in tri]
            if None in src or max(src) >= n:
                continue
            c = np.mean([(pts[i].x, pts[i].y) for i in src], axis=0)
            if not point_in_poly(c[None], P)[0]:
                continue
            vs = [ring[i] for i in src]
            nrm = (vs[1].co - vs[0].co).cross(vs[2].co - vs[0].co)
            if nrm.length < 1e-6:
                continue
            if nrm.z < 0:
                vs = [vs[0], vs[2], vs[1]]
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            f.smooth = True
            f[tag] = PROPOSAL_ID
            for lp in f.loops:
                co = lp.vert.co
                lp[col] = colour(co.x, co.y, co.z)
                uv = np.array([co.x, co.y, 1.0]) @ coef
                lp[uvl].uv = (float(uv[0]), float(uv[1]))
            gap += 1
        stitch_note = "filled with %d triangles" % gap
    else:
        stitch_note = "the band's last column meets today's shelf directly (%d chain ends)" % len(ends)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    # the outer edge, for its straight runs (Godot x, z)
    outer = np.array([(r[6][0], r[6][1]) for r in grid])
    runs, longest = straight_runs(outer, 0.25, 40.0)
    outer_wide = outer[W > 20.0]
    rep = {"faces_removed": int(len(dead_idx)), "faces_added": made + gap, "band_faces": made, "stitch": stitch_note,
           "inner_line_m": round(float(S), 1), "band_columns": len(Sh), "folded_triangles": flips, "folded_at": flip_at[:12],
           "outer_edge_straight_runs_over_40m": runs, "outer_edge_longest_simplified_run_m": round(longest, 1),
           "width_m": [round(float(W[W > 1].min()), 1), round(float(W.max()), 1)],
           "triangles_before": len(SF), "triangles_after": len(me.polygons)}
    return ob, rep, outer, Sh


# --- measuring --------------------------------------------------------------------------------

def object_tris(ob):
    V, F = mesh_arrays(ob.data) if all(p.loop_total == 3 for p in ob.data.polygons) else triangulated(ob)
    return V, F


def triangulated(ob):
    me = ob.data
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    tris = []
    for p in me.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1):
            tris.append((vs[0], vs[k], vs[k + 1]))
    return V, np.array(tris, dtype=np.int64)


def contour(V, F, level, box):
    """The `level` contour of a triangle mesh's surfaces as plan segments, inside a plan box
    (Blender x0, x1, y0, y1)."""
    P = V[F]
    zmin, zmax = P[:, :, 2].min(1), P[:, :, 2].max(1)
    cx, cy = P[:, :, 0].mean(1), P[:, :, 1].mean(1)
    m = (zmin < level) & (zmax > level) & (cx > box[0]) & (cx < box[1]) & (cy > box[2]) & (cy < box[3])
    segs = []
    for tri in P[m]:
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            za, zb = tri[a, 2], tri[b, 2]
            if (za < level) != (zb < level):
                t = (level - za) / (zb - za)
                pts.append(tri[a, :2] + t * (tri[b, :2] - tri[a, :2]))
        if len(pts) == 2:
            segs.append((pts[0], pts[1]))
    return np.array(segs).reshape(-1, 2, 2)


def raster(trees, box, step):
    """The topmost surface over a plan grid, Blender box (x0, x1, y0, y1)."""
    xs = np.arange(box[0] + step / 2, box[1], step)
    ys = np.arange(box[2] + step / 2, box[3], step)
    H = np.full((len(ys), len(xs)), np.nan)
    for i, y in enumerate(ys):
        for k, x in enumerate(xs):
            best = None
            for tree in trees:
                z = top_at(tree, x, y)
                if z is not None and (best is None or z > best):
                    best = z
            if best is not None:
                H[i, k] = best
    return xs, ys, H


def cloud_distance(Q, C):
    """Distance from each point to the nearest of a dense point cloud."""
    out = np.empty(len(Q))
    for a in range(0, len(Q), 1024):
        out[a:a + 1024] = np.sqrt(((Q[a:a + 1024, None, :] - C[None]) ** 2).sum(-1).min(1))
    return out


def seg_points(segs, step=0.5):
    out = []
    for a, b in segs:
        n = max(1, int(np.hypot(*(b - a)) / step))
        for t in np.linspace(0, 1, n + 1):
            out.append(a + (b - a) * t)
    return np.array(out).reshape(-1, 2)


def box_dist(Q, box):
    cx, cz, sx, sz, yaw = box
    c, s = math.cos(yaw), math.sin(yaw)
    d = Q - np.array(g2b(cx, cz))
    # Godot yaw about y: rotate the plan offset into the box's frame (z flips sign in Blender plan)
    lx = d[:, 0] * c + (-d[:, 1]) * (-s)
    lz = d[:, 0] * s + (-d[:, 1]) * c
    ex = np.maximum(np.abs(lx) - sx / 2, 0.0)
    ez = np.maximum(np.abs(lz) - sz / 2, 0.0)
    return np.hypot(ex, ez)


def harbour_boxes():
    boxes = []
    for i in range(len(BREAKWATER) - 1):
        a, b = np.array(BREAKWATER[i]), np.array(BREAKWATER[i + 1])
        mid = (a + b) / 2
        theta = math.atan2(b[0] - a[0], b[1] - a[1])
        boxes.append(("breakwater_%d" % i, mid[0], mid[1], 5.0, float(np.hypot(*(b - a))) + 1.2, theta))
    return boxes + HARBOUR_BOXES


def measure(plan, states, out):
    """Waterlines, cliff tops, areas, the walk's margins, the harbour's clearances."""
    rep = {}
    walk = plan.walk
    zone = (-300.0, -95.0, 190.0, 425.0)  # Blender x0, x1, y0, y1 (Godot z -425..-190)
    lines = {}
    for name, (coast, shelf) in states.items():
        V, F = object_tris(coast)
        segs = contour(V, F, SEA, zone)
        lines[name] = segs
    pts_cur = seg_points(lines["current"])
    # today's land, for which side of today's waterline a new one stands
    trees_cur = [bvh_of(*object_tris(states["current"][0]))]
    xs, ys, Hc = raster(trees_cur, zone, 0.5)
    rep["raster_m"] = 0.5
    for name, (coast, shelf) in states.items():
        r = {}
        pts = seg_points(lines[name])
        if name != "current":
            # how far each new waterline point stands from today's, seaward (+) or inland (-)
            dcur = cloud_distance(pts, pts_cur)
            ix = np.clip(((pts[:, 0] - zone[0]) / 0.5).astype(int), 0, len(xs) - 1)
            iy = np.clip(((pts[:, 1] - zone[2]) / 0.5).astype(int), 0, len(ys) - 1)
            was_land = Hc[iy, ix] > SEA
            signed = np.where(was_land, -dcur, dcur)
            r["waterline_moved_seaward_max_m"] = round(float(signed.max()), 2)
            r["waterline_moved_inland_max_m"] = round(float(-signed.min()), 2)
            r["waterline_seaward_max_at"] = [round(float(pts[np.argmax(signed), 0]), 1), round(float(-pts[np.argmax(signed), 1]), 1)]
            r["waterline_inland_max_at"] = [round(float(pts[np.argmin(signed), 0]), 1), round(float(-pts[np.argmin(signed), 1]), 1)]
            # by stretch: where it moved more than 1.5 m
            moved = np.abs(signed) > 1.5
            r["waterline_points_moved_over_1_5m_share"] = round(float(moved.mean()), 3)
            tr = [bvh_of(*object_tris(coast))]
            _, _, Hn = raster(tr, zone, 0.5)
            gained = (Hn > SEA) & ~(Hc > SEA)
            lost = (Hc > SEA) & ~(Hn > SEA)
            r["land_gained_m2"] = round(float(gained.sum() * 0.25), 1)
            r["land_lost_m2"] = round(float(lost.sum() * 0.25), 1)
            dH = Hn - Hc
            ok = ~np.isnan(dH)
            r["height_change_max_raise_m"] = round(float(np.nanmax(dH[ok])), 2)
            r["height_change_max_cut_m"] = round(float(-np.nanmin(dH[ok])), 2)
            r["area_changed_over_5cm_m2"] = round(float((np.abs(dH[ok]) > 0.05).sum() * 0.25), 1)
            # the waterline's stretches that moved, as plan runs for the seabed
            np.save(os.path.join(out, "waterline_%s.npy" % name), np.column_stack([pts[:, 0], -pts[:, 1], signed]))
        r["walk_to_waterline_min_m"] = round(float(seg_distance(pts, walk).min()), 2) if len(pts) else None
        r["waterline_length_m"] = round(float(np.hypot(*(lines[name][:, 1] - lines[name][:, 0]).T).sum()), 1)
        rep[name] = r
    return rep, lines


def face_stats(ob, plan):
    """The steep faces' mean slope and the share within 1 degree of vertical, in the face's run."""
    V, F = object_tris(ob)
    N, A = face_normals(V, F)
    cen = V[F].mean(1)
    s, d, c = plan.outline.project(cen[:, :2])
    m = (s > plan.sA) & (s < plan.sB) & (d < 30.0) & (np.abs(N[:, 2]) < 0.7) & (A > 1e-3) & (cen[:, 2] > SEA)
    slope = np.degrees(np.arccos(np.clip(np.abs(N[m, 2]), 0, 1)))
    w = A[m]
    return {"steep_face_area_m2": round(float(w.sum()), 1), "mean_slope_deg": round(float((slope * w).sum() / w.sum()), 1),
            "share_within_1deg_of_vertical": round(float(w[slope > 89.0].sum() / w.sum()), 3)}


def sections(plan, states, cove_lines):
    """Every surface along each section line at 0.5 m, per state."""
    out = {}
    lines = dict(SECTIONS)
    lines.update(cove_lines)
    for key, (a, b) in lines.items():
        a, b = np.array(a), np.array(b)
        L = float(np.hypot(*(b - a)))
        n = int(L / 0.5) + 1
        rows = {}
        for name, objs in states.items():
            trees = {("shelf" if "shelf" in o.name else "coast"): bvh_of(*object_tris(o)) for o in objs}
            col = []
            for k in range(n):
                p = a + (b - a) * k / (n - 1)
                hits = all_hits(trees, p[0], -p[1])
                col.append([round(float(k * L / (n - 1)), 2), [[round(h[0], 3), h[1], h[2]] for h in hits]])
            rows[name] = col
        out[key] = {"a": a.tolist(), "b": b.tolist(), "rows": rows}
    return out


# --- rendering (the seabed proposals' look: world_terrain_proposals_seabed.py) -----------------

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
    """The game's sea over the bed (the seabed proposals' aerial mode): see-through over CLARITY m
    along the view, its colour by depth straight down over REACH."""
    ng = bpy.data.node_groups.new("KYT_headland_render", "ShaderNodeTree")
    ng.interface.new_socket("Bed", in_out="INPUT", socket_type="NodeSocketShader")
    ng.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    Nn, Lk = ng.nodes, ng.links
    gin = Nn.new("NodeGroupInput")
    gout = Nn.new("NodeGroupOutput")
    geo = Nn.new("ShaderNodeNewGeometry")
    sep = Nn.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Position"], sep.inputs[0])

    def op(kind, a=None, b=None, va=None, vb=None):
        m = Nn.new("ShaderNodeMath")
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
    isep = Nn.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Incoming"], isep.inputs[0])
    cosv = op("MAXIMUM", a=op("ABSOLUTE", a=isep.outputs["Z"]), vb=0.05)
    through = op("DIVIDE", a=dpos, b=cosv)
    cover = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=through, vb=-CLARITY)))
    alpha = Nn.new("ShaderNodeMix")
    alpha.data_type = "FLOAT"
    alpha.inputs[2].default_value = SURFACE
    alpha.inputs[3].default_value = 1.0
    Lk.new(cover, alpha.inputs[0])
    afac = op("MULTIPLY", a=alpha.outputs[0], b=under)
    rf = op("SUBTRACT", va=1.0, b=op("EXPONENT", a=op("DIVIDE", a=dpos, vb=-REACH)))
    tint = Nn.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    gain = np.array(WATER_GAIN)
    tint.inputs[6].default_value = (*(srgb_to_linear(SHALLOW) * gain), 1.0)
    tint.inputs[7].default_value = (*(srgb_to_linear(DEEP) * gain), 1.0)
    Lk.new(rf, tint.inputs[0])
    wem = Nn.new("ShaderNodeEmission")
    Lk.new(tint.outputs[2], wem.inputs["Color"])
    mixs = Nn.new("ShaderNodeMixShader")
    Lk.new(afac, mixs.inputs[0])
    Lk.new(gin.outputs["Bed"], mixs.inputs[1])
    Lk.new(wem.outputs[0], mixs.inputs[2])
    Lk.new(mixs.outputs[0], gout.inputs["Shader"])
    return ng


def wrap_materials(objs, ng):
    done = set()
    for ob in objs:
        for slot in ob.material_slots:
            m = slot.material
            if m is None or m.name in done or m.node_tree is None:
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
            outn = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
            if outn is None or not outn.inputs["Surface"].links:
                continue
            link = outn.inputs["Surface"].links[0]
            src = link.from_socket
            nt.links.remove(link)
            g = nt.nodes.new("ShaderNodeGroup")
            g.node_tree = ng
            nt.links.new(src, g.inputs["Bed"])
            nt.links.new(g.outputs["Shader"], outn.inputs["Surface"])


def flat_material(name, colour, emit=True):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except AttributeError:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if emit:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*srgb_to_linear(colour[:3]), 1.0)
        nt.links.new(em.outputs[0], out.inputs[0])
    else:
        bs = nt.nodes.new("ShaderNodeBsdfDiffuse")
        bs.inputs["Color"].default_value = (*srgb_to_linear(colour[:3]), 1.0)
        nt.links.new(bs.outputs[0], out.inputs[0])
    return m


def ribbon(name, segs, width, z, colour, coll):
    if not len(segs):
        return None
    S = np.asarray(segs, dtype=float)
    a, b = S[:, 0, :], S[:, 1, :]
    d = b - a
    ln = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
    u = d / ln[:, None]
    n = np.column_stack([-u[:, 1], u[:, 0]]) * (width / 2)
    a2, b2 = a - u * (width / 2), b + u * (width / 2)
    m = len(S)
    Vr = np.concatenate([a2 + n, a2 - n, b2 - n, b2 + n], axis=0)
    V3 = np.column_stack([Vr, np.full(len(Vr), z)])
    me = bpy.data.meshes.new(name)
    me.from_pydata(V3.tolist(), [], [(k, k + m, k + 2 * m, k + 3 * m) for k in range(m)])
    me.materials.append(flat_material(name, colour))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def box_object(name, cx, cz, y0, y1, sx, sz, yaw, colour, coll):
    me = bpy.data.meshes.new(name)
    hx, hz = sx / 2, sz / 2
    c, s = math.cos(yaw), math.sin(yaw)
    pts = []
    for lx, lz in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)):
        gx = cx + lx * c + lz * s
        gz = cz - lx * s + lz * c
        pts.append((gx, -gz))
    V3 = [(x, y, y0) for x, y in pts] + [(x, y, y1) for x, y in pts]
    me.from_pydata(V3, [], [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    me.materials.append(flat_material(name, colour, emit=False))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


class Renderer:
    def __init__(self, folder, quick=False):
        self.folder = folder
        scene = bpy.context.scene
        self.scene = scene
        scene.render.engine = "BLENDER_EEVEE"
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
        try:
            scene.eevee.taa_render_samples = 4 if quick else 32
        except AttributeError:
            pass
        if quick:
            scene.render.resolution_percentage = 40
        world = bpy.data.worlds.new("scratch_world")
        scene.world = world
        try:
            world.use_nodes = True
        except AttributeError:
            pass
        bg = world.node_tree.nodes.get("Background")
        bg.inputs[0].default_value = (*srgb_to_linear((0.62, 0.72, 0.85)), 1.0)
        bg.inputs[1].default_value = 0.9
        sun_data = bpy.data.lights.new("scratch_sun", "SUN")
        sun_data.energy = 3.2
        sun_data.angle = math.radians(1.0)
        sun = bpy.data.objects.new("scratch_sun", sun_data)
        # 13:00-ish from the south-west, 50 degrees up (the brief's standard light)
        sun.rotation_euler = (math.radians(40.0), 0.0, math.radians(-45.0))
        scene.collection.objects.link(sun)
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

    def top_down(self, name, box, px=1500):
        x0, x1, z0, z1 = box
        ex, ez = x1 - x0, z1 - z0
        self.cam_data.type = "ORTHO"
        self.cam_data.ortho_scale = max(ex, ez)
        self.cam_data.sensor_fit = "VERTICAL" if ez > ex else "HORIZONTAL"
        self.cam.location = ((x0 + x1) / 2, -(z0 + z1) / 2, 3000.0)
        self.cam.rotation_euler = (0.0, 0.0, 0.0)
        self.scene.render.resolution_x = px if ex >= ez else int(round(px * ex / ez))
        self.scene.render.resolution_y = int(round(px * ez / ex)) if ex >= ez else px
        self.shoot(name)


def context_objects(coll):
    """Render-only context, never saved: a grey stand-in where Ground has holes the generator fills
    (the road corridor, the river, the park), the harbour's boxes, the pier."""
    ground = [o for o in bpy.data.collections["Ground"].all_objects if o.type == "MESH"]
    trees = [bvh_of(*object_tris(o)) for o in ground if o.name not in (SHELF, "terrain_landform_shelf")]
    hw = np.array([(p.co.x, p.co.y, p.co.z) for p in curve_points("coast_highway_centreline")])
    tiles = []
    park = {}
    if os.path.exists(PARK_CSV):
        import csv
        for r in csv.DictReader(open(PARK_CSV)):
            if r["kind"] != "open" and r["top_y"]:
                park[(int(round(float(r["x"]))), int(round(float(r["z"]))))] = float(r["top_y"])
    for gz in np.arange(-900.0, 120.0, 4.0):
        for gx in np.arange(-360.0, 160.0, 4.0):
            x, y = gx, -gz
            if any(top_at(t, x, y) is not None for t in trees):
                continue
            key = (int(gx), int(gz))
            if key in park and park[key] > SEA:
                tiles.append((x, y, park[key]))
                continue
            if len(hw):
                d = np.hypot(hw[:, 0] - x, hw[:, 1] - y)
                k = int(np.argmin(d))
                if d[k] < 42.0:
                    tiles.append((x, y, hw[k, 2] - 0.3))
    if tiles:
        T = np.array(tiles)
        s = 2.3
        n = len(T)
        sv = np.concatenate([np.column_stack([T[:, 0] + dx * s, T[:, 1] + dy * s, T[:, 2]]) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        me = bpy.data.meshes.new("scratch_standin")
        me.vertices.add(len(sv))
        me.vertices.foreach_set("co", sv.ravel())
        me.loops.add(4 * n)
        me.loops.foreach_set("vertex_index", np.column_stack([np.arange(n) + k * n for k in range(4)]).ravel())
        me.polygons.add(n)
        me.polygons.foreach_set("loop_start", np.arange(n) * 4)
        me.update()
        me.materials.append(flat_material("scratch_standin", (0.62, 0.62, 0.6), emit=False))
        ob = bpy.data.objects.new("scratch_standin", me)
        coll.objects.link(ob)
    for nm, cx, cz, sx, sz, yaw in harbour_boxes():
        y0, y1 = (-10.4, -6.0) if nm.startswith("breakwater") else ((-7.9, -3.1) if nm == "breakwater_head" else
                                                                   ((-7.2, -5.8) if nm == "quay" else (-7.7, -6.2)))
        colr = (0.55, 0.53, 0.5) if nm.startswith("breakwater") else ((0.55, 0.42, 0.3) if nm == "quay" else
                                                                       ((0.95, 0.95, 0.95) if "white" in nm else (0.8, 0.2, 0.15)))
        box_object("scratch_" + nm, cx, cz, y0, y1, sx, sz, yaw, colr, coll)
    box_object("scratch_pier", (PIER_BOX[0] + PIER_BOX[1]) / 2, (PIER_BOX[2] + PIER_BOX[3]) / 2, -4.5, -3.8,
               PIER_BOX[1] - PIER_BOX[0], PIER_BOX[3] - PIER_BOX[2], 0.0, (0.55, 0.42, 0.3), coll)


def curve_points(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return []
    if ob.type == "MESH":
        return [type("P", (), {"co": ob.matrix_world @ v.co}) for v in ob.data.vertices]
    if ob.type != "CURVE":
        return []
    pts = []
    for sp in ob.data.splines:
        for p in (sp.bezier_points if sp.type == "BEZIER" else sp.points):
            pts.append(type("P", (), {"co": ob.matrix_world @ Vector(p.co[:3])}))
    return pts


def render_all(rd, plan, states, lines, collections, out, seabed=None):
    scene = bpy.context.scene
    ng = render_group()
    ground = [o for o in bpy.data.collections["Ground"].all_objects if o.type == "MESH"]
    variant_objs = [o for c in collections.values() for o in c.objects]
    wrap_materials(ground + variant_objs, ng)
    keep = {o.name for o in ground + variant_objs}
    for ob in scene.objects:
        if ob.name not in keep and ob.type in ("MESH", "CURVE", "FONT", "EMPTY", "GPENCIL"):
            ob.hide_render = True
    ctx = bpy.data.collections.new("scratch_render")
    scene.collection.children.link(ctx)
    context_objects(ctx)
    # the void: where nothing stands under the water, the game reads 30 m of it
    vme = bpy.data.meshes.new("scratch_void")
    R = 60000.0
    vme.from_pydata([(-R, -R, -37.5), (R, -R, -37.5), (R, R, -37.5), (-R, R, -37.5)], [], [(0, 1, 2, 3)])
    t1 = 1.0 - math.exp(-30.0 / REACH)
    c = srgb_to_linear(SHALLOW) * (1 - t1) + srgb_to_linear(DEEP) * t1
    vme.materials.append(flat_material("scratch_void", (0, 0, 0)))
    vem = next(n for n in vme.materials[0].node_tree.nodes if n.type == "EMISSION")
    vem.inputs["Color"].default_value = (*(c * np.array(WATER_GAIN)), 1.0)
    void = bpy.data.objects.new("scratch_void", vme)
    ctx.objects.link(void)
    # the waterlines for the plan: today's in white, the proposal's in pink
    marks = bpy.data.collections.new("scratch_marks")
    scene.collection.children.link(marks)
    wl = {k: ribbon("scratch_wl_" + k, v, 0.9 if k == "current" else 1.1, 80.0 if k == "current" else 81.0,
                    (1, 1, 1) if k == "current" else (1.0, 0.25, 0.75), marks) for k, v in lines.items()}
    walk_segs = np.stack([plan.walk[:-1], plan.walk[1:]], axis=1)
    walk_rib = ribbon("scratch_walk", walk_segs, 0.8, 82.0, (0.95, 0.1, 0.1), marks)
    cur_coast, cur_shelf = bpy.data.objects[COAST], bpy.data.objects[SHELF]
    for state, (coast, shelf) in states.items():
        for o in (cur_coast, cur_shelf):
            o.hide_render = state != "current"
        for k, colc in collections.items():
            for o in colc.objects:
                o.hide_render = k != state
            colc.hide_render = k != state
        for k, o in wl.items():
            if o:
                o.hide_render = True
        walk_rib.hide_render = True
        for view, (eye, aim, lens) in VIEWS.items():
            rd.oblique("%s_%s_%s.png" % (NAME, state, view), eye, aim, lens)
        wl["current"].hide_render = False
        if state != "current" and wl.get(state):
            wl[state].hide_render = False
        walk_rib.hide_render = False
        rd.top_down("%s_%s_plan.png" % (NAME, state), PLAN)
    for k, o in wl.items():
        if o:
            o.hide_render = True
    walk_rib.hide_render = True
    # the seabed session's B bed beside A2's shelf, if it loads
    if seabed is not None:
        state = "A2"
        for o in (cur_coast, cur_shelf):
            o.hide_render = True
        for k, colc in collections.items():
            colc.hide_render = k != state
            for o in colc.objects:
                o.hide_render = k != state
        seabed.hide_render = False
        wrap_materials([seabed], ng)
        rd.oblique("%s_A2_withbedB_V3.png" % NAME, *VIEWS["V3"])
        rd.oblique("%s_A2_withbedB_V1.png" % NAME, *VIEWS["V1"])
        seabed.hide_render = True


def load_seabed(coll):
    """The seabed session's option B bed, read from its scratch file (never written)."""
    if not os.path.exists(SEABED_BLEND):
        return None
    try:
        with bpy.data.libraries.load(SEABED_BLEND, link=False) as (src, dst):
            names = [n for n in src.objects if n == "PROPOSAL_seabed_B"]
            dst.objects = names
        for ob in dst.objects:
            if ob is not None:
                coll.objects.link(ob)
                ob.hide_render = True
                return ob
    except Exception as exc:  # the bed is a courtesy; its absence never stops the proposal
        log("seabed bed not loaded: %s" % exc)
    return None


# --- main ---------------------------------------------------------------------------------------

def blender_main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--out" not in argv:
        raise SystemExit("headland cliff proposals: --out <folder> is required")
    out = os.path.abspath(argv[argv.index("--out") + 1])
    master = os.path.abspath(argv[argv.index("--master") + 1]) if "--master" in argv else DEFAULT_MASTER
    for forbidden in ("assets", "scenes", "scripts", "planning", "tools"):
        for base in {ROOT, MAIN}:
            f = os.path.join(base, forbidden)
            if os.path.commonpath([out, f]) == f:
                raise SystemExit("headland cliff proposals: no output may go under %s/" % forbidden)
    os.makedirs(out, exist_ok=True)
    scratch = os.path.join(out, "PROPOSAL_%s.blend" % NAME)
    if os.path.abspath(scratch) == os.path.abspath(master):
        raise SystemExit("headland cliff proposals: the scratch copy may not be the master")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    plan = Plan()
    report = {"master": master, "scratch": scratch, "date": "2026-10-09",
              "face_run": {"from_godot": [round(float(plan.V[plan.tA, 0]), 2), round(float(-plan.V[plan.tA, 1]), 2)],
                           "to_godot": [round(float(plan.V[plan.tB, 0]), 2), round(float(-plan.V[plan.tB, 1]), 2)],
                           "length_m": round(plan.base.length, 1)},
              "cliff_top_max_shift_outside_coves_m": round(plan.top_shift_max, 2),
              "coves": [{"name": c["name"], "planned_at_godot": list(c["at"]), "depth_m": c["depth_m"],
                         "mouth_m": 2 * c["half_mouth"], "floor": c["floor"]} for c in plan.coves],
              "protected_vertices": int(plan.protected.sum()), "variants": {}}
    collections = {}
    states = {"current": (bpy.data.objects[COAST], bpy.data.objects[SHELF])}
    shelves = {}
    for variant in ("A1", "A2"):
        coll = bpy.data.collections.new("PROPOSAL_%s_%s" % (NAME, variant))
        bpy.context.scene.collection.children.link(coll)
        collections[variant] = coll
        log("building %s" % variant)
        coast, inner, rep = build_variant(plan, variant, coll)
        shelf, srep, outer, Sh = build_shelf(plan, variant, inner, coll)
        shelves[variant] = (outer, Sh)
        rep["shelf"] = srep
        rep.update(face_stats(coast, plan))
        report["variants"][variant] = rep
        states[variant] = (coast, shelf)
        log("%s: %s" % (variant, json.dumps({k: v for k, v in rep.items() if k != "shelf"})))
        log("%s shelf: %s" % (variant, json.dumps(srep)))
    report["current"] = face_stats(bpy.data.objects[COAST], plan)
    # every vertex outside the edit stays: compare the copies' surviving vertices with today's
    for variant, (coast, _) in states.items():
        if variant == "current":
            continue
        Vn = np.zeros(len(coast.data.vertices) * 3)
        coast.data.vertices.foreach_get("co", Vn)
        Vn = Vn.reshape(-1, 3)
        kd = KDTree(len(Vn))
        for i, v in enumerate(Vn):
            kd.insert(tuple(v), i)
        kd.balance()
        prot = np.nonzero(plan.protected)[0]
        worst = 0.0
        for i in prot:
            _, _, d = kd.find(tuple(plan.V[i]))
            worst = max(worst, d)
        report["variants"][variant]["protected_vertices_max_move_m"] = round(float(worst), 6)
    log("measuring")
    meas, lines = measure(plan, states, out)
    for k, v in meas.items():
        if k in report["variants"]:
            report["variants"][k]["waterline"] = v
    report["current_waterline"] = meas["current"]
    # the walk to the cliff top (today's top edge, the new cliff-top line), and to the shore
    cur_top = plan.V[plan.edge, :2]
    report["walk_to_cliff_top_min_m"] = {"current": round(float(seg_distance(cur_top, plan.walk).min()), 2),
                                         "A1_and_A2": round(float(seg_distance(plan.L, plan.walk).min()), 2)}
    # the table and the loop: their vertices, by measurement
    p1 = plan.marks["p1_floor"]
    e2 = plan.marks["e2_floor"]
    tb = plan.top_tree
    report["table_heights"] = {"P1_ground_y": round(float(top_at(tb, p1[0], -p1[2])), 3),
                               "E2_ground_y": round(float(top_at(tb, e2[0], -e2[2])), 3)}
    for variant in ("A1", "A2"):
        coast = states[variant][0]
        t = bvh_of(*object_tris(coast))
        report["variants"][variant]["table_heights"] = {"P1_ground_y": round(float(top_at(t, p1[0], -p1[2])), 3),
                                                        "E2_ground_y": round(float(top_at(t, e2[0], -e2[2])), 3)}
        # the walk's ground under every sample, today against the variant
        dz = []
        for w in plan.walk_g:
            a = top_at(tb, w[0], -w[2])
            bq = top_at(t, w[0], -w[2])
            if a is not None and bq is not None:
                dz.append(abs(a - bq))
        report["variants"][variant]["walk_ground_max_change_m"] = round(float(max(dz) if dz else 0.0), 6)
        # the shelf against the harbour, the pier and NT-1
        sV, sF = object_tris(states[variant][1])
        new = []
        me = states[variant][1].data
        tagl = me.attributes.get("authored_edit")
        vals = np.zeros(len(me.polygons), dtype=np.int64)
        tagl.data.foreach_get("value", vals)
        newf = sF[vals == PROPOSAL_ID]
        pts = sV[np.unique(newf.ravel()), :2]
        clear = {}
        for nm, cx, cz, sx, sz, yaw in harbour_boxes():
            clear[nm] = round(float(box_dist(pts, (cx, cz, sx, sz, yaw)).min()), 1)
        px0, px1, pz0, pz1 = PIER_BOX
        pq = np.column_stack([pts[:, 0], -pts[:, 1]])
        clear["pier"] = round(float(np.hypot(np.maximum(np.maximum(px0 - pq[:, 0], pq[:, 0] - px1), 0),
                                             np.maximum(np.maximum(pz0 - pq[:, 1], pq[:, 1] - pz1), 0)).min()), 1)
        clear["NT1_datums"] = round(float(min(np.hypot(pq[:, 0] - x, pq[:, 1] - z).min() for x, z in NT1_POINTS)), 1)
        # inside the seabed session's harbour polygon: how much of the new shelf has under 4 m of water
        hp = np.array([g2b(x, z) for x, z in SEABED_HARBOUR])
        cen = sV[newf].mean(1)
        inside = point_in_poly(cen[:, :2], hp)
        Nn, An = face_normals(sV, newf)
        shallow = inside & (cen[:, 2] > SEA - 4.0)
        clear["shelf_in_seabed_harbour_polygon_m2"] = round(float(An[inside].sum()), 1)
        clear["of_which_under_4m_water_m2"] = round(float(An[shallow].sum()), 1)
        report["variants"][variant]["shelf"]["clearances_m"] = clear
    cove_lines = {}
    for c in plan.coves:
        pc = np.array(c["centre_b"])
        s, _, _ = plan.base.project(pc[None])
        _, tng = plan.base.at(s)
        n = np.array([-tng[0, 1], tng[0, 0]])
        a = pc + n * 55.0
        b = pc - n * 50.0
        cove_lines["%s_z%d" % (c["name"], int(round(-c["at"][1])))] = ((a[0], -a[1]), (b[0], -b[1]))
    report["section_lines_godot"] = {k: [list(map(float, v[0])), list(map(float, v[1]))] for k, v in {**SECTIONS, **cove_lines}.items()}
    log("sections")
    sec = sections(plan, {"current": [bpy.data.objects[COAST], bpy.data.objects[SHELF]],
                          "A1": list(states["A1"]), "A2": list(states["A2"])}, cove_lines)
    with open(os.path.join(out, "sections.json"), "w") as f:
        json.dump(sec, f)
    # the waterline moves, by stretch, for the seabed
    for variant in ("A1", "A2"):
        W_ = np.load(os.path.join(out, "waterline_%s.npy" % variant))
        report["variants"][variant]["waterline_moves_for_seabed"] = stretches(W_)
    # hide the variants by default; today's objects stay as they were
    for k, coll in collections.items():
        for o in coll.objects:
            o.hide_set(True)
            o.hide_render = True
        coll.hide_render = True
    report["shelf_outer_edges_godot"] = {k: [[round(float(x), 2), round(float(-y), 2)] for x, y in v[0][::3]] for k, v in shelves.items()}
    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(report, f, indent=1)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    log("scratch file %s saved (the master is untouched)" % scratch)
    if "--no-render" in argv:
        return
    for k, coll in collections.items():
        for o in coll.objects:
            o.hide_set(False)
    rd = Renderer(out, quick="--quick" in argv)
    bedc = bpy.data.collections.new("scratch_bed")
    bpy.context.scene.collection.children.link(bedc)
    seabed = load_seabed(bedc) if "--no-bed" not in argv else None
    render_all(rd, plan, states, lines, collections, out, seabed)
    report["renders"] = rd.outputs
    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(report, f, indent=1)


def stretches(W_):
    """Runs along the new waterline that moved more than 1 m, with their extent and largest move
    (Godot x, z)."""
    out = []
    if not len(W_):
        return out
    order = np.argsort(np.arctan2(W_[:, 1] + 300.0, W_[:, 0] + 170.0))
    P = W_[order]
    moved = np.abs(P[:, 2]) > 1.0
    k = 0
    while k < len(P):
        if not moved[k]:
            k += 1
            continue
        j = k
        while j + 1 < len(P) and moved[j + 1]:
            j += 1
        seg = P[k:j + 1]
        if len(seg) > 6:
            i = int(np.argmax(np.abs(seg[:, 2])))
            out.append({"from": [round(float(seg[0, 0]), 1), round(float(seg[0, 1]), 1)],
                        "to": [round(float(seg[-1, 0]), 1), round(float(seg[-1, 1]), 1)],
                        "largest_m": round(float(seg[i, 2]), 2), "at": [round(float(seg[i, 0]), 1), round(float(seg[i, 1]), 1)],
                        "direction": "seaward" if seg[i, 2] > 0 else "inland"})
        k = j + 1
    return out


# --- the sections, drawn with PIL (plain Python) -------------------------------------------------

def draw_sections(folder):
    from PIL import Image, ImageDraw, ImageFont
    sec = json.load(open(os.path.join(folder, "sections.json")))

    def font(s=14):
        try:
            return ImageFont.load_default(size=s)
        except Exception:
            return ImageFont.load_default()
    colours = {"current": (90, 90, 90), "A1": (200, 40, 140), "A2": (30, 120, 200)}
    for key, s in sec.items():
        for variant in ("A1", "A2"):
            Wd, Hd = 1500, 620
            im = Image.new("RGB", (Wd, Hd), (255, 255, 255))
            d = ImageDraw.Draw(im)
            L0, R0, T0_, B0 = 70, 30, 60, 60
            rows = s["rows"]
            smax = rows["current"][-1][0]
            ylo, yhi = -18.0, 34.0
            sc = min((Wd - L0 - R0) / smax, (Hd - T0_ - B0) / (yhi - ylo))
            sx_eff = sy = sc

            def P(u, y):
                return (L0 + u * sx_eff, Hd - B0 - (y - ylo) * sy)
            d.rectangle([P(0, SEA), P(smax, ylo)], fill=(214, 232, 247))
            d.line([P(0, SEA), P(smax, SEA)], fill=(40, 90, 200), width=2)
            d.text((P(smax, SEA)[0] - 90, P(smax, SEA)[1] - 16), "sea y = -7.5", fill=(40, 90, 200), font=font(13))
            for y in range(-15, 35, 5):
                d.line([P(0, y), (L0 - 6, P(0, y)[1])], fill=0)
                d.text((8, P(0, y)[1] - 7), "%d" % y, fill=0, font=font(12))
            for state in ("current", variant):
                pts = [(u, hits[0][0]) for u, hits in rows[state] if hits]
                seg = []
                prev_u = None
                for u, y in pts:
                    if prev_u is not None and u - prev_u > 0.75:
                        if len(seg) > 1:
                            d.line([P(*p) for p in seg], fill=colours[state], width=3 if state != "current" else 2)
                        seg = []
                    seg.append((u, y))
                    prev_u = u
                if len(seg) > 1:
                    d.line([P(*p) for p in seg], fill=colours[state], width=3 if state != "current" else 2)
            a, b = s["a"], s["b"]
            d.text((L0, 10), "%s: %s against today (grey) -- vertical x1.0" % (key, variant), fill=0, font=font(16))
            d.text((L0, 32), "from (%.0f, %.0f) to (%.0f, %.0f), Godot x, z; the topmost ground along the line" % (a[0], a[1], b[0], b[1]),
                   fill=(60, 60, 60), font=font(12))
            for u in range(0, int(smax) + 1, 20):
                p = P(u, ylo)
                d.line([p, (p[0], p[1] + 5)], fill=0)
                d.text((p[0] - 8, p[1] + 8), "%d" % u, fill=0, font=font(12))
            d.text((Wd // 2 - 80, Hd - 24), "metres along the line", fill=0, font=font(12))
            d.rectangle([Wd - 250, 52, Wd - 236, 64], fill=colours["current"])
            d.text((Wd - 230, 50), "today", fill=0, font=font(13))
            d.rectangle([Wd - 250, 72, Wd - 236, 84], fill=colours[variant])
            d.text((Wd - 230, 70), variant, fill=0, font=font(13))
            im.save(os.path.join(folder, "%s_%s_section_%s.png" % (NAME, variant, key)))
        # today's alone
        print("drew", key)


if __name__ == "__main__":
    if IN_BLENDER:
        blender_main()
    else:
        if "--sections" not in sys.argv:
            raise SystemExit("plain Python draws the sections: --sections <folder>")
        draw_sections(os.path.abspath(sys.argv[sys.argv.index("--sections") + 1]))
