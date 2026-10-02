"""Route PROPOSALS for the coastal branch: a loop round the bay that rides on
the terrain (2026-10-01, Christina: reconnect the branch to the main highway
"by way of snaking along those ridges", at grade, no "deep crazy canyon").

Three phases, nothing touches the master, ParkPlan or the game:

    # 1. sample the current master into a 25 m raster and dump its reference geometry (Blender)
    Blender --background assets/source/world_terrain_master.blend \
        --python tools/blender/world_terrain_route_branch.py -- --sample <folder>
    # 2. route, profile, metrics, plots (system Python: numpy, PIL)
    python3 tools/blender/world_terrain_route_branch.py --route <folder>
    # 3. draw the routes on a scratch copy and render (Blender)
    Blender --background --factory-startup \
        --python tools/blender/world_terrain_route_branch.py -- --render <folder>

Method. A least-cost path on the 25 m raster (16 neighbours, so bearings
every 27 degrees or finer) from the branch's start at the city bypass to the
main highway's southern end. Step cost = length x (1 + SIDE_W x side slope)
+ CUT_W x (rise beyond the grade cap): the rise a road cannot take at its
grade is exactly what has to be cut or filled, so CUT_W is "metres of extra
road worth one metre of cut". Forbidden: the sea and a land margin under
SEA_MARGIN above sea level, the park envelope padded, the city peninsula
footprint padded (except round the start), the bridge deck and its landing
padded. The path is simplified (Douglas-Peucker) and filleted at the
project's radii (HIGHWAY_FILLET_R 120 m, HIGHWAY_FILLET_MIN_R 90 m). The
road's longitudinal profile is the ground profile limited to the grade cap
by symmetric 1D slope limiting with the two junction heights fixed, so cut
and fill share the difference. Cut/fill per 10 m station across a corridor
of CORRIDOR_W (the branch's strip width in the city GLB is about 9.6 m, two
3.6 m lanes with the project's shoulders; 12 m with verges), volumes as
width x depth x length (no side slopes, stated). Tunnel-worthy: cut deeper
than TUNNEL_CUT over a contiguous stretch.

Variants: the grade caps 1.9 % (the present rule, `_maximum_ribbon_grade`),
6 % and 8.3 % (1:12, HIGHWAY_MAX_GRADE), everything else equal.
"""

import heapq
import json
import math
import os
import shutil
import sys

import numpy as np

try:
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
except ImportError:
    bpy = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DEFAULT_MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
STEP = 25.0
SEA_LEVEL = -7.5
SEA_MARGIN = 3.0          # m above sea level the road must keep
BOX = (-1950.0, 1300.0, 2150.0, 6550.0)   # x0, x1, z0, z1 (Godot) sampled
VARIANTS = [("1.9%", 0.019, (0.90, 0.15, 0.15, 1.0)), ("6%", 0.06, (1.0, 0.65, 0.0, 1.0)), ("8.3%", 1.0 / 12.0, (0.15, 0.75, 0.2, 1.0))]
CUT_W = 25.0              # metres of road worth one metre of forced cut/fill
SIDE_W = 1.5              # side-slope weight (rise/run across the step)
FILLET_R = 120.0
FILLET_MIN_R = 90.0
CORRIDOR_W = 12.0
TUNNEL_CUT = 15.0
STATION = 10.0
DP_TOL = 35.0             # m: the lattice path is simplified to this before filleting, so legs are long enough for the radii
PENINSULA_PAD = 60.0
BRIDGE_PAD = 60.0
PARK_PAD = 100.0
START_FREE_R = 200.0      # round the start the peninsula padding does not apply
ENVELOPE = (-212.0, 222.0, -230.0, 220.0)
# Two families. "south": her description, the existing branch kept down the
# wedge's west flank to where it stops, then over the apron saddle at the
# wedge's southern end and north up the eastern range's flank. "bay": the
# free least-cost loop, which rounds the bay at its apex instead.
FAMILIES = {"south": [(-1450.0, 5424.0), (-300.0, 5675.0)], "bay": []}

NEIGHBOURS = [(dj, di) for dj in range(-2, 3) for di in range(-2, 3)
              if (dj, di) != (0, 0) and math.gcd(abs(dj), abs(di)) == 1]


def to_blender(x, y, z):
    return (x, -z, y)


# --- phase 1: sample ----------------------------------------------------------

def sample(folder):
    os.makedirs(folder, exist_ok=True)
    obj = bpy.data.objects["terrain_world"]
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    xs = np.arange(BOX[0], BOX[1] + STEP / 2, STEP)
    zs = np.arange(BOX[2], BOX[3] + STEP / 2, STEP)
    H = np.full((len(zs), len(xs)), np.nan)
    down = Vector((0.0, 0.0, -1.0))
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            hit = bvh.ray_cast(Vector((x, -z, 1000.0)), down, 5000.0)
            if hit[0] is None:
                for dx, dy in ((2e-3, 2e-3), (-2e-3, -2e-3)):
                    hit = bvh.ray_cast(Vector((x + dx, -z + dy, 1000.0)), down, 5000.0)
                    if hit[0] is not None:
                        break
            if hit[0] is not None:
                H[j, i] = hit[0].z
    refs = {}
    for name in ("coast_highway_centreline", "city_bypass_centreline", "coastal_highway_branch_centreline",
                 "city_peninsula_footprint", "bridge_main_deck_footprint", "bridge_approach_footprint",
                 "city_built_blocks_hull", "park_program_envelope", "approach_road_centreline"):
        o = bpy.data.objects.get(name)
        if o is None or o.type != "CURVE":
            continue
        pts = []
        for sp in o.data.splines:
            for p in sp.points:
                pts.append((float(p.co[0]), float(p.co[2]), float(-p.co[1])))  # Godot x, y, z
        refs[name] = pts
    np.savez(os.path.join(folder, "branch_raster.npz"), H=H, xs=xs, zs=zs)
    with open(os.path.join(folder, "branch_refs.json"), "w") as f:
        json.dump(refs, f)
    print(f"route_branch: sampled {H.shape[1]}x{H.shape[0]} cells, {int(np.isnan(H).sum())} without ground; refs {sorted(refs)}")


# --- geometry helpers ----------------------------------------------------------

def point_in_poly(x, z, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, z0 = poly[i][0], poly[i][1]
        x1, z1 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (z0 > z) != (z1 > z):
            xi = x0 + (z - z0) * (x1 - x0) / (z1 - z0)
            if xi > x:
                inside = not inside
    return inside


def dist_to_poly(x, z, poly, closed=True):
    best = math.inf
    n = len(poly)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        ax, az = poly[i][0], poly[i][1]
        bx, bz = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        vx, vz = bx - ax, bz - az
        L2 = vx * vx + vz * vz
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * vx + (z - az) * vz) / L2))
        best = min(best, math.hypot(x - (ax + t * vx), z - (az + t * vz)))
    return best


def bilinear(H, xs, zs, x, z):
    fx = (x - xs[0]) / STEP
    fz = (z - zs[0]) / STEP
    i0 = int(np.clip(math.floor(fx), 0, len(xs) - 2))
    j0 = int(np.clip(math.floor(fz), 0, len(zs) - 2))
    tx, tz = fx - i0, fz - j0
    q = H[j0:j0 + 2, i0:i0 + 2]
    if np.isnan(q).any():
        v = q[~np.isnan(q)]
        return float(v.mean()) if len(v) else math.nan
    return float((q[0, 0] * (1 - tx) + q[0, 1] * tx) * (1 - tz) + (q[1, 0] * (1 - tx) + q[1, 1] * tx) * tz)


def douglas_peucker(pts, tol):
    if len(pts) < 3:
        return pts
    ax, az = pts[0]
    bx, bz = pts[-1]
    L = math.hypot(bx - ax, bz - az)
    worst, k = 0.0, 0
    for m in range(1, len(pts) - 1):
        px, pz = pts[m]
        d = abs((bx - ax) * (az - pz) - (ax - px) * (bz - az)) / L if L > 0 else math.hypot(px - ax, pz - az)
        if d > worst:
            worst, k = d, m
    if worst > tol:
        return douglas_peucker(pts[:k + 1], tol)[:-1] + douglas_peucker(pts[k:], tol)
    return [pts[0], pts[-1]]


def fillet(pts, r, r_min):
    """Arcs of radius r (down to r_min) at every corner of a polyline, as the
    project's fillet_polyline does; corners whose legs are too short for
    r_min keep the corner and are counted."""
    out = [pts[0]]
    short = 0
    radii = []
    for k in range(1, len(pts) - 1):
        p0, p1, p2 = np.array(pts[k - 1]), np.array(pts[k]), np.array(pts[k + 1])
        d0, d2 = p0 - p1, p2 - p1
        L0, L2 = np.linalg.norm(d0), np.linalg.norm(d2)
        if L0 < 1e-6 or L2 < 1e-6:
            continue
        u0, u2 = d0 / L0, d2 / L2
        cosang = float(np.clip(np.dot(u0, u2), -1.0, 1.0))
        theta = math.acos(cosang)  # interior angle
        if theta > math.pi - 1e-3:
            out.append(tuple(p1))
            continue
        rr = r
        t = rr / math.tan(theta / 2)
        lim = min(L0, L2) * 0.5
        if t > lim:
            rr = max(r_min, lim * math.tan(theta / 2))
            t = rr / math.tan(theta / 2)
        if t > lim:
            short += 1
            out.append(tuple(p1))
            continue
        a, b = p1 + u0 * t, p1 + u2 * t
        bis = (u0 + u2)
        bis /= np.linalg.norm(bis)
        c = p1 + bis * (rr / math.sin(theta / 2))
        va, vb = a - c, b - c
        ang = math.atan2(va[0] * vb[1] - va[1] * vb[0], float(np.dot(va, vb)))
        n = max(3, int(abs(ang) * rr / 10.0))
        for s in range(n + 1):
            phi = ang * s / n
            ca, sa = math.cos(phi), math.sin(phi)
            out.append((float(c[0] + ca * va[0] - sa * va[1]), float(c[1] + sa * va[0] + ca * va[1])))
        radii.append(rr)
    out.append(pts[-1])
    return out, short, (min(radii) if radii else None)


def resample(pts, ds):
    seg = [math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(len(pts) - 1)]
    s = np.concatenate([[0.0], np.cumsum(seg)])
    stations = np.arange(0.0, s[-1], ds)
    stations = np.append(stations, s[-1])
    xs = np.interp(stations, s, [p[0] for p in pts])
    zs = np.interp(stations, s, [p[1] for p in pts])
    return stations, xs, zs


def limit_profile(ground, s, cap, h0, h1, max_iter=400000):
    """The road profile: the ground limited to |dh/ds| <= cap by symmetric
    1D slope limiting, both junction heights fixed."""
    h = ground.copy()
    h[0], h[-1] = h0, h1
    for it in range(max_iter):
        d = np.diff(h)
        ds = np.diff(s)
        lim = cap * ds
        excess = np.abs(d) - lim
        act = excess > 1e-4
        if not act.any():
            return h, it
        move = np.where(act, excess, 0.0) * np.sign(d) * 0.5
        adj = np.zeros_like(h)
        adj[:-1] += move
        adj[1:] -= move
        adj[0] = adj[-1] = 0.0
        h += adj
        h[1:-1] = np.maximum(h[1:-1], SEA_LEVEL + 1.0)  # a road never dips under the sea
    return h, max_iter


# --- phase 2: route -----------------------------------------------------------

def dijkstra(H, forbidden, grad, s_node, e_node, cap, sources=None):
    """Least-cost lattice path; `sources` (a list of nodes) makes a multi-source
    search, the path then starting at whichever source wins."""
    nz, nx = H.shape
    dist = np.full(H.shape, np.inf)
    prev = {}
    pq = []
    for src in (sources or [s_node]):
        dist[src] = 0.0
        pq.append((0.0, src))
    heapq.heapify(pq)
    starts = set(sources or [s_node])
    while pq:
        dcur, u = heapq.heappop(pq)
        if dcur > dist[u]:
            continue
        if u == e_node:
            break
        for dj, di in NEIGHBOURS:
            v = (u[0] + dj, u[1] + di)
            if not (0 <= v[0] < nz and 0 <= v[1] < nx) or forbidden[v]:
                continue
            if abs(dj) == 2 or abs(di) == 2:  # knight moves must not jump a forbidden cell
                mid = (u[0] + dj // 2 if abs(dj) == 2 else u[0] + dj, u[1] + di // 2 if abs(di) == 2 else u[1] + di)
                m2 = (u[0] + (dj - dj // 2) if abs(dj) == 2 else u[0], u[1] + (di - di // 2) if abs(di) == 2 else u[1])
                if forbidden[mid] or forbidden[m2]:
                    continue
            L = STEP * math.hypot(dj, di)
            rise = abs(H[v] - H[u])
            forced = max(0.0, rise - cap * L)
            along = rise / L
            side = max(0.0, grad[v] - along)
            c = L * (1.0 + SIDE_W * side) + CUT_W * forced
            nd = dcur + c
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if not np.isfinite(dist[e_node]):
        return None
    path = [e_node]
    while path[-1] not in starts:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def route(folder, family="bay"):
    d = np.load(os.path.join(folder, "branch_raster.npz"))
    H, xs, zs = d["H"], d["xs"], d["zs"]
    with open(os.path.join(folder, "branch_refs.json")) as f:
        refs = json.load(f)
    nz, nx = H.shape
    X, Z = np.meshgrid(xs, zs)
    land = ~np.isnan(H) & (H > SEA_LEVEL + SEA_MARGIN)

    # start: the branch where it leaves the bypass (its northernmost point); end: the highway's southern end
    branch = refs["coastal_highway_branch_centreline"]
    bypass = refs["city_bypass_centreline"]
    start = min(branch, key=lambda p: p[2])
    highway = refs["coast_highway_centreline"]
    end = max(highway, key=lambda p: p[2])
    peninsula = [(p[0], p[2]) for p in refs["city_peninsula_footprint"]]
    bridge = [(p[0], p[2]) for p in refs["bridge_main_deck_footprint"]]
    approach = [(p[0], p[2]) for p in refs["bridge_approach_footprint"]]

    forbidden = ~land
    for j in range(nz):
        for i in range(nx):
            if forbidden[j, i]:
                continue
            x, z = xs[i], zs[j]
            if ENVELOPE[0] - PARK_PAD <= x <= ENVELOPE[1] + PARK_PAD and ENVELOPE[2] - PARK_PAD <= z <= ENVELOPE[3] + PARK_PAD:
                forbidden[j, i] = True
                continue
            near_start = math.hypot(x - start[0], z - start[2]) < START_FREE_R
            if not near_start and (point_in_poly(x, z, peninsula) or dist_to_poly(x, z, peninsula) < PENINSULA_PAD):
                forbidden[j, i] = True
                continue
            if point_in_poly(x, z, bridge) or dist_to_poly(x, z, bridge) < BRIDGE_PAD:
                forbidden[j, i] = True
                continue
            if point_in_poly(x, z, approach) or dist_to_poly(x, z, approach) < BRIDGE_PAD:
                forbidden[j, i] = True

    def node(p):
        return (int(round((p[2] - zs[0]) / STEP)), int(round((p[0] - xs[0]) / STEP)))

    s_node, e_node = node(start), node(end)
    way_nodes = [node((w[0], 0.0, w[1])) for w in FAMILIES[family]]
    for nd, nm in [(s_node, "start"), (e_node, "end")] + [(w, f"waypoint {k}") for k, w in enumerate(way_nodes)]:
        if forbidden[nd]:
            # the junction itself may sit on a protected cell; free its 3x3
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    if 0 <= nd[0] + dj < nz and 0 <= nd[1] + di < nx and not np.isnan(H[nd[0] + dj, nd[1] + di]):
                        forbidden[nd[0] + dj, nd[1] + di] = False
            print(f"route_branch: {nm} cell was protected; freed its 3x3")

    # side slope per cell: gradient magnitude
    gz, gx = np.gradient(np.where(np.isnan(H), SEA_LEVEL, H), STEP)
    grad = np.hypot(gx, gz)

    results = {"family": family, "waypoints_godot_xz": FAMILIES[family], "start_godot": start, "end_godot": end,
               "variants": [], "raster_box": BOX, "step_m": STEP,
               "corridor_w_m": CORRIDOR_W, "sea_margin_m": SEA_MARGIN, "cut_weight": CUT_W, "side_weight": SIDE_W,
               "fillet_r_m": [FILLET_R, FILLET_MIN_R], "tunnel_cut_m": TUNNEL_CUT}
    for label, cap, colour in VARIANTS:
        legs = [s_node] + way_nodes + [e_node]
        path = []
        failed = False
        for a_, b_ in zip(legs[:-1], legs[1:]):
            leg = dijkstra(H, forbidden, grad, a_, b_, cap)
            if leg is None:
                failed = True
                break
            path += leg if not path else leg[1:]
        if failed:
            results["variants"].append({"label": label, "cap": cap, "error": "no path"})
            print(f"route_branch: {family} {label}: no path")
            continue
        raw = [(float(xs[i]), float(zs[j])) for j, i in path]
        simple = douglas_peucker(raw, DP_TOL)
        smooth, short, rmin = fillet(simple, FILLET_R, FILLET_MIN_R)
        st, px, pz = resample(smooth, STATION)
        ground = np.array([bilinear(H, xs, zs, x, z) for x, z in zip(px, pz)])
        # corridor: ground at +-w/2 across
        tx = np.gradient(px)
        tz = np.gradient(pz)
        nrm = np.hypot(tx, tz)
        tx, tz = tx / np.maximum(nrm, 1e-9), tz / np.maximum(nrm, 1e-9)
        offs = (-CORRIDOR_W / 2, CORRIDOR_W / 2)
        gside = np.array([[bilinear(H, xs, zs, x - tz_ * o, z + tx_ * o) for o in offs] for x, z, tx_, tz_ in zip(px, pz, tx, tz)])
        h0 = bilinear(H, xs, zs, start[0], start[2])
        h1 = bilinear(H, xs, zs, end[0], end[2])
        road, iters = limit_profile(ground, st, cap, h0, h1)
        g_all = np.column_stack([ground, gside])
        cut = np.maximum(0.0, np.nanmax(g_all, axis=1) - road)       # ground above road
        fill = np.maximum(0.0, road - np.nanmin(g_all, axis=1))      # road above ground
        ds = np.gradient(st)
        cut_vol = float(np.nansum(cut * CORRIDOR_W * ds))
        fill_vol = float(np.nansum(fill * CORRIDOR_W * ds))
        deep = cut > TUNNEL_CUT
        stretches = []
        k = 0
        while k < len(deep):
            if deep[k]:
                m = k
                while m < len(deep) and deep[m]:
                    m += 1
                stretches.append({"from_m": float(st[k]), "to_m": float(st[m - 1]), "length_m": float(st[m - 1] - st[k]),
                                  "max_cut_m": float(cut[k:m].max()),
                                  "at_godot_xz": [float(px[k + int(np.argmax(cut[k:m]))]), float(pz[k + int(np.argmax(cut[k:m]))])]})
                k = m
            else:
                k += 1
        grade = np.abs(np.diff(road) / np.diff(st))
        climb = float(np.sum(np.maximum(0.0, np.diff(road))))
        descent = float(np.sum(np.maximum(0.0, -np.diff(road))))
        # the existing branch: how much of it the route keeps (within 40 m)
        near = np.array([dist_to_poly(x, z, [(p[0], p[2]) for p in branch], closed=False) for x, z in zip(px, pz)])
        kept = near < 40.0
        # crest following: stations where the ground is a local max across the corridor and ridge-like
        ridge = (ground >= gside.max(axis=1) - 0.5) & (grad[np.clip(((pz - zs[0]) / STEP).round().astype(int), 0, nz - 1),
                                                           np.clip(((px - xs[0]) / STEP).round().astype(int), 0, nx - 1)] > 0.1)
        v = {"label": label, "cap": cap, "colour": colour, "length_m": float(st[-1]), "stations": len(st),
             "climb_m": climb, "descent_m": descent, "max_grade_profile": float(grade.max()) if len(grade) else 0.0,
             "max_cut_m": float(np.nanmax(cut)), "max_fill_m": float(np.nanmax(fill)), "cut_volume_m3": cut_vol,
             "fill_volume_m3": fill_vol, "mean_cut_m": float(np.nanmean(cut)), "mean_fill_m": float(np.nanmean(fill)),
             "stations_cut_over_5m": int((cut > 5).sum()), "stations_fill_over_5m": int((fill > 5).sum()),
             "tunnel_worthy_stretches": stretches, "tunnel_worthy_length_m": float(sum(s_["length_m"] for s_ in stretches)),
             "fillet_corners_under_min_radius": short, "min_fillet_radius_m": rmin, "profile_iterations": iters,
             "existing_branch_kept_share": float(kept.mean()), "existing_branch_kept_m": float(kept.sum() * STATION),
             "crest_share": float(ridge.mean()), "junction_start_godot": start, "junction_end_godot": end,
             "start_height_m": h0, "end_height_m": h1, "lowest_road_m": float(road.min()), "highest_road_m": float(road.max()),
             "route_godot_xz": [[float(a), float(b)] for a, b in zip(px, pz)], "road_height": [float(a) for a in road],
             "ground_height": [float(a) for a in ground], "cut": [float(a) for a in cut], "fill": [float(a) for a in fill],
             "station": [float(a) for a in st], "kept_existing": [bool(a) for a in kept]}
        results["variants"].append(v)
        print(f"route_branch: {family} {label}: length {v['length_m']:.0f} m, climb {climb:.0f} m, max cut {v['max_cut_m']:.1f} m, "
              f"max fill {v['max_fill_m']:.1f} m, cut {cut_vol / 1e6:.2f} Mm3, fill {fill_vol / 1e6:.2f} Mm3, tunnel-worthy "
              f"{len(stretches)} stretch(es) {v['tunnel_worthy_length_m']:.0f} m, existing branch kept {kept.mean() * 100:.0f} %, "
              f"crest {ridge.mean() * 100:.0f} %, corners under min radius {short}, min radius {rmin}")
    with open(os.path.join(folder, f"proposal_branch_routes_{family}.json"), "w") as f:
        json.dump(results, f)
    plots(folder, results, family)


def plots(folder, results, family):
    from PIL import Image, ImageDraw
    W, Hh, pad = 2000, 420, 60
    vs = [v for v in results["variants"] if "error" not in v]
    img = Image.new("RGB", (W, Hh * len(vs) + pad), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for k, v in enumerate(vs):
        top = k * Hh + pad // 2
        st = np.array(v["station"])
        g = np.array(v["ground_height"])
        r = np.array(v["road_height"])
        hmin, hmax = -20.0, max(300.0, float(np.nanmax(g)) + 20.0)
        s1 = st[-1]
        sx = lambda s: pad + s / s1 * (W - 2 * pad)
        sy = lambda h: top + Hh - 40 - (min(max(h, hmin), hmax) - hmin) / (hmax - hmin) * (Hh - 50)
        dr.rectangle([pad, top, W - pad, top + Hh - 40], outline=(120, 120, 120))
        for hv in range(0, int(hmax), 50):
            dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
            dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
        dr.line([pad, sy(SEA_LEVEL), W - pad, sy(SEA_LEVEL)], fill=(120, 170, 230))
        # cut shaded (ground above road) in red, fill in blue
        for m in range(len(st) - 1):
            x0, x1 = sx(st[m]), sx(st[m + 1])
            if g[m] > r[m]:
                dr.rectangle([x0, sy(g[m]), x1 + 1, sy(r[m])], fill=(235, 150, 150))
            elif r[m] > g[m]:
                dr.rectangle([x0, sy(r[m]), x1 + 1, sy(g[m])], fill=(160, 190, 235))
        dr.line([(sx(s), sy(h)) for s, h in zip(st, g)], fill=(90, 90, 90), width=2)
        dr.line([(sx(s), sy(h)) for s, h in zip(st, r)], fill=tuple(int(c * 255) for c in v["colour"][:3]), width=3)
        dr.text((pad + 6, top + 4), f"{family} loop, grade cap {v['label']}: length {v['length_m']:.0f} m, climb {v['climb_m']:.0f} m, max cut {v['max_cut_m']:.1f} m "
                f"(red), max fill {v['max_fill_m']:.1f} m (blue), cut {v['cut_volume_m3'] / 1e6:.2f} Mm3, fill {v['fill_volume_m3'] / 1e6:.2f} Mm3, "
                f"tunnel-worthy {len(v['tunnel_worthy_stretches'])} x {v['tunnel_worthy_length_m']:.0f} m. grey: ground, colour: road", fill=(20, 20, 20))
        for s in range(0, int(s1) + 1, 1000):
            dr.text((sx(s) - 10, top + Hh - 36), f"{s / 1000:.0f} km", fill=(60, 60, 60))
    img.save(os.path.join(folder, f"proposal_branch_profiles_{family}.png"))
    # metrics table
    rows = [("grade cap", "length m", "climb m", "max cut m", "max fill m", "cut Mm3", "fill Mm3", "tunnel-worthy", "existing kept", "crest share")]
    for v in vs:
        rows.append((v["label"], f"{v['length_m']:.0f}", f"{v['climb_m']:.0f}", f"{v['max_cut_m']:.1f}", f"{v['max_fill_m']:.1f}",
                     f"{v['cut_volume_m3'] / 1e6:.2f}", f"{v['fill_volume_m3'] / 1e6:.2f}",
                     f"{len(v['tunnel_worthy_stretches'])} / {v['tunnel_worthy_length_m']:.0f} m",
                     f"{v['existing_branch_kept_share'] * 100:.0f} % ({v['existing_branch_kept_m']:.0f} m)", f"{v['crest_share'] * 100:.0f} %"))
    cw = 150
    timg = Image.new("RGB", (cw * len(rows[0]) + 20, 30 * len(rows) + 20), (250, 250, 248))
    td = ImageDraw.Draw(timg)
    for rI, row in enumerate(rows):
        for cI, cell in enumerate(row):
            td.text((10 + cI * cw, 10 + rI * 30), str(cell), fill=(20, 20, 20) if rI else (90, 40, 40))
    timg.save(os.path.join(folder, f"proposal_branch_metrics_{family}.png"))
    print(f"route_branch: wrote profiles and metrics PNGs in {folder}")


# --- phase 3: render ----------------------------------------------------------

def render(folder, master=DEFAULT_MASTER):
    fams = {}
    for fam in FAMILIES:
        pth = os.path.join(folder, f"proposal_branch_routes_{fam}.json")
        if os.path.exists(pth):
            with open(pth) as f:
                fams[fam] = json.load(f)
    scratch = os.path.join(folder, "PROPOSAL_branch_routes.blend")
    assets = os.path.join(ROOT, "assets")
    if os.path.commonpath([os.path.abspath(folder), assets]) == assets:
        raise SystemExit("route_branch: the folder may not be under assets/")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    scene = bpy.context.scene
    obj = bpy.data.objects["terrain_world"]
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()

    def curve(name, pts, colour, bevel):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = bevel
        cu.bevel_resolution = 0
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = colour
        nt.links.new(em.outputs[0], out.inputs[0])
        cu.materials.append(m)
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*to_blender(*p), 1.0)
        o = bpy.data.objects.new(name, cu)
        o["kyt_proposal"] = True
        scene.collection.objects.link(o)
        return o

    curves = []  # (family, variant, object); the south family thick, the bay family thin
    for fam, results in fams.items():
        for v in results["variants"]:
            if "error" in v:
                continue
            pts = [(x, h + 3.0, z) for (x, z), h in zip(v["route_godot_xz"], v["road_height"])]
            curves.append((fam, v, curve(f"PROPOSAL_branch_{fam}_{v['label']}", pts, tuple(v["colour"]), 10.0 if fam == "south" else 5.0)))
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.7854, 0.0, -2.0944)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0
    outputs = []

    def shoot(name):
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        outputs.append(scene.render.filepath)
        print(f"route_branch: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2400):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = to_blender(cx, 5000.0, cz)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            scene.render.resolution_x, scene.render.resolution_y = px, int(px * ez / ex)
        else:
            scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
        shoot(name)

    def oblique(name, eye, aim, lens=35.0):
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector(to_blender(*eye)), Vector(to_blender(*aim))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
        shoot(name)

    top_down("proposal_branch_ring_top.png", BOX[0], BOX[1], BOX[2], BOX[3])
    for fam in fams:
        for f2, v, o in curves:
            o.hide_render = f2 != fam
        top_down(f"proposal_branch_ring_top_{fam}.png", BOX[0], BOX[1], BOX[2], BOX[3])
    best = None
    for fam, results in fams.items():
        if results.get("best_label"):
            best = (fam, results["best_label"])
    for f2, v, o in curves:
        o.hide_render = best is not None and (f2, v["label"]) != best
    if best:
        oblique("proposal_branch_best_oblique.png", (1400.0, 700.0, 6900.0), (-300.0, 60.0, 4600.0), lens=30.0)
        oblique("proposal_branch_best_oblique_west.png", (-2300.0, 650.0, 6300.0), (-400.0, 60.0, 4300.0), lens=30.0)
    bpy.ops.wm.save_mainfile()
    with open(os.path.join(folder, "proposal_branch_renders.json"), "w") as f:
        json.dump({"renders": outputs, "best": best}, f)


# --- phase 4: the bay-loop alignment (Christina's choice, 2026-10-01) --------

SHORE_MARGIN = 15.0       # m from the water's edge the centreline should keep; at 25 m resolution reported as "on the last land cell"
CHORD_DEV = 10.0          # m: a straightened leg may not leave the ground by more than this (no slicing of spurs)
JUNCTION_BACK = 70.0      # m: the branch meets the highway this far before its end, clear of the bridge landing
K_VERTICAL = 12.0         # m per % of grade change, crest and sag: a 60 km/h scenic road, not a trunk highway (K 30 flattened every summit into a cut)
SIDE_SLOPE = 2.0          # 1:2 cut and fill side slopes
SCENIC_D = 60.0           # m from the water that counts as "on the water"


def allowed_chord(a, b, allowed, xs, zs, H=None):
    """Every 5 m of the chord a-b lies on an allowed cell, and, with H, the
    ground along it stays within CHORD_DEV of the line between its ends (a
    straightened leg may not slice through a spur or bridge a gully)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(L / 5.0))
    ga = gb = None
    if H is not None:
        ga, gb = bilinear(H, xs, zs, a[0], a[1]), bilinear(H, xs, zs, b[0], b[1])
    for k in range(n + 1):
        t = k / n
        x, z = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        i = int(round((x - xs[0]) / STEP))
        j = int(round((z - zs[0]) / STEP))
        if not (0 <= i < len(xs) and 0 <= j < len(zs)) or not allowed[j, i]:
            return False
        if H is not None:
            g = bilinear(H, xs, zs, x, z)
            if not np.isnan(g) and abs(g - (ga + t * (gb - ga))) > CHORD_DEV:
                return False
    return True


def relax_alignment(pts, allowed, xs, zs, r, r_min, H=None):
    """Remove polyline vertices whose corner cannot take a fillet of r_min
    while the new chord stays on allowed ground, until every corner fillets
    (r preferred, r_min at least). Returns (points, exceptions)."""
    pts = list(pts)
    for _ in range(500):
        _, short, _, bad = fillet_with_radii(pts, r, r_min)
        if not bad:
            return pts, []
        removed = False
        for k in sorted(bad, key=lambda k: -k):  # from the end, indices stay valid
            if 0 < k < len(pts) - 1 and allowed_chord(pts[k - 1], pts[k + 1], allowed, xs, zs, H):
                del pts[k]
                removed = True
                break
        if not removed:
            # try moving the corner to the midpoint of its neighbours instead
            moved = False
            for k in bad:
                if 0 < k < len(pts) - 1:
                    m = ((pts[k - 1][0] + pts[k + 1][0]) / 2, (pts[k - 1][1] + pts[k + 1][1]) / 2)
                    if allowed_chord(pts[k - 1], m, allowed, xs, zs, H) and allowed_chord(m, pts[k + 1], allowed, xs, zs, H):
                        pts[k] = m
                        moved = True
                        break
            if not moved:
                break
    _, short, _, bad = fillet_with_radii(pts, r, r_min)
    return pts, bad


def fillet_with_radii(pts, r, r_min):
    """As fillet(), but also returns per-point radii (inf on tangents) and
    the indices of corners that could not take r_min."""
    out = [pts[0]]
    rad = [math.inf]
    short = 0
    bad = []
    radii = []
    for k in range(1, len(pts) - 1):
        p0, p1, p2 = np.array(pts[k - 1]), np.array(pts[k]), np.array(pts[k + 1])
        d0, d2 = p0 - p1, p2 - p1
        L0, L2 = np.linalg.norm(d0), np.linalg.norm(d2)
        if L0 < 1e-6 or L2 < 1e-6:
            continue
        u0, u2 = d0 / L0, d2 / L2
        theta = math.acos(float(np.clip(np.dot(u0, u2), -1.0, 1.0)))
        if theta > math.pi - 1e-3:
            out.append(tuple(p1))
            rad.append(math.inf)
            continue
        rr = r
        t = rr / math.tan(theta / 2)
        lim = min(L0, L2) * 0.5
        if t > lim:
            rr = max(r_min, lim * math.tan(theta / 2))
            t = rr / math.tan(theta / 2)
        if t > lim:
            short += 1
            bad.append(k)
            out.append(tuple(p1))
            rad.append(0.0)
            continue
        a, b = p1 + u0 * t, p1 + u2 * t
        bis = (u0 + u2)
        bis /= np.linalg.norm(bis)
        c = p1 + bis * (rr / math.sin(theta / 2))
        va, vb = a - c, b - c
        ang = math.atan2(va[0] * vb[1] - va[1] * vb[0], float(np.dot(va, vb)))
        n = max(3, int(abs(ang) * rr / 10.0))
        for s_ in range(n + 1):
            phi = ang * s_ / n
            ca, sa = math.cos(phi), math.sin(phi)
            out.append((float(c[0] + ca * va[0] - sa * va[1]), float(c[1] + sa * va[0] + ca * va[1])))
            rad.append(rr)
        radii.append(rr)
    out.append(pts[-1])
    rad.append(math.inf)
    return (out, rad), short, (min(radii) if radii else None), bad


def vertical_curves(road, s, cap, k_per_pct):
    """Parabolic crest and sag curves: the grade series is limited to a rate
    of change of 1 % per k_per_pct metres, then integrated back with the
    ends held; the grade cap is re-imposed and both repeated."""
    h = road.copy()
    for _ in range(3):
        ds = np.diff(s)
        g = np.diff(h) / ds * 100.0  # percent
        rate = 1.0 / k_per_pct      # % per metre
        for it in range(20000):
            dg = np.diff(g)
            lim = rate * (ds[:-1] + ds[1:]) / 2
            excess = np.abs(dg) - lim
            act = excess > 1e-6
            if not act.any():
                break
            move = np.where(act, excess, 0.0) * np.sign(dg) * 0.5
            g[:-1] += move
            g[1:] -= move
        g = np.clip(g, -cap * 100.0, cap * 100.0)
        h2 = h[0] + np.concatenate([[0.0], np.cumsum(g / 100.0 * ds)])
        # hold the end: spread the closing error linearly
        err = h2[-1] - h[-1]
        h = h2 - err * (s - s[0]) / (s[-1] - s[0])
        h, _ = limit_profile(h, s, cap, h[0], h[-1])
    return h


def align(folder):
    d = np.load(os.path.join(folder, "branch_raster.npz"))
    H, xs, zs = d["H"], d["xs"], d["zs"]
    with open(os.path.join(folder, "branch_refs.json")) as f:
        refs = json.load(f)
    with open(os.path.join(folder, "proposal_branch_routes_bay.json")) as f:
        bay = json.load(f)
    v83 = [v for v in bay["variants"] if v["label"] == "8.3%"][0]
    cap = v83["cap"]
    nz, nx = H.shape
    X, Z = np.meshgrid(xs, zs)
    land = ~np.isnan(H) & (H > SEA_LEVEL + SEA_MARGIN)
    # the shoreline: land cells with a non-land 4-neighbour; distance field to it
    shore = land & ~(np.roll(land, 1, 0) & np.roll(land, -1, 0) & np.roll(land, 1, 1) & np.roll(land, -1, 1))
    sz, sx = np.nonzero(shore)
    shore_pts = np.stack([xs[sx], zs[sz]], axis=1)
    wz, wx = np.nonzero(~land)
    water_pts = np.stack([xs[wx], zs[wz]], axis=1)

    def d_shore(x, z):
        return float(np.min(np.hypot(shore_pts[:, 0] - x, shore_pts[:, 1] - z)))

    def water_bearing(x, z):
        dd = np.hypot(water_pts[:, 0] - x, water_pts[:, 1] - z)
        k = int(np.argmin(dd))
        return float((math.degrees(math.atan2(water_pts[k, 0] - x, -(water_pts[k, 1] - z))) + 360.0) % 360.0), float(dd[k])

    # allowed cells: the route's forbidden set plus the shore margin
    start = bay["start_godot"]
    highway_pts = sorted(refs["coast_highway_centreline"], key=lambda p: p[2])
    # the junction: back along the highway from its end by JUNCTION_BACK, clear of the bridge landing
    acc, end = 0.0, highway_pts[-1]
    for a_, b_ in zip(highway_pts[::-1][:-1], highway_pts[::-1][1:]):
        seg = math.hypot(b_[0] - a_[0], b_[2] - a_[2])
        if acc + seg >= JUNCTION_BACK:
            t = (JUNCTION_BACK - acc) / seg
            end = [a_[0] + t * (b_[0] - a_[0]), a_[1], a_[2] + t * (b_[2] - a_[2])]
            break
        acc += seg
    hw_tangent_prev = highway_pts[-3]
    peninsula = [(p[0], p[2]) for p in refs["city_peninsula_footprint"]]
    bridge = [(p[0], p[2]) for p in refs["bridge_main_deck_footprint"]]
    approach = [(p[0], p[2]) for p in refs["bridge_approach_footprint"]]
    allowed = land.copy()
    for j in range(nz):
        for i in range(nx):
            if not allowed[j, i]:
                continue
            x, z = xs[i], zs[j]
            near_start = math.hypot(x - start[0], z - start[2]) < START_FREE_R
            near_end = math.hypot(x - end[0], z - end[2]) < START_FREE_R
            if ENVELOPE[0] - PARK_PAD <= x <= ENVELOPE[1] + PARK_PAD and ENVELOPE[2] - PARK_PAD <= z <= ENVELOPE[3] + PARK_PAD:
                allowed[j, i] = False
            elif not near_start and (point_in_poly(x, z, peninsula) or dist_to_poly(x, z, peninsula) < PENINSULA_PAD):
                allowed[j, i] = False
            elif not near_end and (point_in_poly(x, z, bridge) or dist_to_poly(x, z, bridge) < BRIDGE_PAD
                                   or point_in_poly(x, z, approach) or dist_to_poly(x, z, approach) < BRIDGE_PAD):
                allowed[j, i] = False
            # shore cells stay allowed: at 25 m the water-side bench is often one cell wide and
            # forbidding it pushed the road over the wedge's shoulder; the margin is reported instead
    # the raw lattice path again (the search is cheap), then the relaxation
    gz, gx = np.gradient(np.where(np.isnan(H), SEA_LEVEL, H), STEP)
    grad = np.hypot(gx, gz)
    forbidden = ~allowed

    def node(p):
        return (int(round((p[2] - zs[0]) / STEP)), int(round((p[0] - xs[0]) / STEP)))

    s_node, e_node = node(start), node(end)
    # the departure may be anywhere along the bypass (cells within 40 m of its centreline,
    # not within 150 m of the bridge approach), the search picks it
    bypass_line = [(p[0], p[2]) for p in sorted(refs["city_bypass_centreline"], key=lambda p: p[2])]
    sources = []
    for j in range(nz):
        for i in range(nx):
            if np.isnan(H[j, i]):
                continue
            x, z = xs[i], zs[j]
            if dist_to_poly(x, z, bypass_line, closed=False) < 40.0 and dist_to_poly(x, z, approach) > 150.0:
                sources.append((j, i))
                forbidden[j, i] = False
    for nd in (s_node, e_node):
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                if 0 <= nd[0] + dj < nz and 0 <= nd[1] + di < nx and not np.isnan(H[nd[0] + dj, nd[1] + di]):
                    forbidden[nd[0] + dj, nd[1] + di] = False
    allowed = ~forbidden
    path = dijkstra(H, forbidden, grad, s_node, e_node, cap, sources=sources)
    dep = (float(xs[path[0][1]]), float(zs[path[0][0]]))
    # the departure on the bypass itself: the nearest bypass point, and its chainage from the bridge landing
    k_dep = int(np.argmin([math.hypot(q[0] - dep[0], q[1] - dep[1]) for q in bypass_line]))
    start = [bypass_line[k_dep][0], 0.0, bypass_line[k_dep][1]]
    chain = sum(math.hypot(bypass_line[k + 1][0] - bypass_line[k][0], bypass_line[k + 1][1] - bypass_line[k][1]) for k in range(k_dep))
    bypass_total = sum(math.hypot(bypass_line[k + 1][0] - bypass_line[k][0], bypass_line[k + 1][1] - bypass_line[k][1]) for k in range(len(bypass_line) - 1))
    print(f"route_branch: departure from the bypass at ({start[0]:.0f}, {start[2]:.0f}), {chain:.0f} m from the bridge landing of {bypass_total:.0f} m; "
          f"{bypass_total - chain:.0f} m of the bypass beyond it and the whole old branch become free")
    raw = [(float(xs[i]), float(zs[j])) for j, i in path]
    simple = douglas_peucker(raw, DP_TOL)
    # the bypass's last tangent in front and the highway's tangent behind, so both junction bends are filleted
    # the bypass tangent 60 m before the departure (towards the bridge landing)
    acc, bp_back = 0.0, bypass_line[max(k_dep - 1, 0)]
    for k in range(k_dep, 0, -1):
        a_, b_ = bypass_line[k], bypass_line[k - 1]
        seg = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        if acc + seg >= 60.0:
            t = (60.0 - acc) / seg
            bp_back = (a_[0] + t * (b_[0] - a_[0]), a_[1] + t * (b_[1] - a_[1]))
            break
        acc += seg
    simple = [bp_back, (start[0], start[2])] + simple + [(hw_tangent_prev[0], hw_tangent_prev[2])]
    relaxed, exceptions = relax_alignment(simple, allowed, xs, zs, FILLET_R, FILLET_MIN_R, H)
    (smooth, rad_pts), short, rmin, bad = fillet_with_radii(relaxed, FILLET_R, FILLET_MIN_R)
    st, px, pz = resample(smooth, STATION)
    # radius per station: nearest smoothed point's radius
    sp = np.array(smooth)
    radius = []
    for x, z in zip(px, pz):
        k = int(np.argmin(np.hypot(sp[:, 0] - x, sp[:, 1] - z)))
        radius.append(rad_pts[k])
    radius = np.array(radius)
    ground = np.array([bilinear(H, xs, zs, x, z) for x, z in zip(px, pz)])
    tx, tz = np.gradient(px), np.gradient(pz)
    nrm = np.maximum(np.hypot(tx, tz), 1e-9)
    tx, tz = tx / nrm, tz / nrm
    h0 = bilinear(H, xs, zs, start[0], start[2])
    h1 = bilinear(H, xs, zs, end[0], end[2])
    road0, _ = limit_profile(ground, st, cap, h0, h1)
    road = vertical_curves(road0, st, cap, K_VERTICAL)
    grade = np.concatenate([[0.0], np.diff(road) / np.diff(st)])
    dcut = np.maximum(0.0, ground - road)
    dfill = np.maximum(0.0, road - ground)
    ds = np.gradient(st)
    cut_area = CORRIDOR_W * dcut + SIDE_SLOPE * dcut ** 2   # two 1:2 side triangles of area d*(2d)/2 each
    fill_area = CORRIDOR_W * dfill + SIDE_SLOPE * dfill ** 2
    cut_vol, fill_vol = float(np.sum(cut_area * ds)), float(np.sum(fill_area * ds))
    # corridor edges on land / margins
    shore_d = np.array([d_shore(x, z) for x, z in zip(px, pz)])
    wb = [water_bearing(x, z) for x, z in zip(px, pz)]
    w_bearing = np.array([b for b, _ in wb])
    w_dist = np.array([dd for _, dd in wb])
    on_water = w_dist <= SCENIC_D
    view_wsw = on_water & (w_bearing >= 180.0) & (w_bearing <= 315.0)
    # stretches away from the water
    away = []
    k = 0
    while k < len(st):
        if not on_water[k]:
            m = k
            while m < len(st) and not on_water[m]:
                m += 1
            if st[m - 1] - st[k] >= 50.0:
                away.append({"from_m": float(st[k]), "to_m": float(st[m - 1]), "at_godot_xz": [float(px[k]), float(pz[k])],
                             "max_dist_to_water_m": float(w_dist[k:m].max())})
            k = m
        else:
            k += 1
    # stations on the last land cell (a water cell is a neighbour): the corridor's seaward edge would then be within ~6 m of the water
    on_shore_cell = np.array([bool(shore[int(np.clip(round((z - zs[0]) / STEP), 0, nz - 1)), int(np.clip(round((x - xs[0]) / STEP), 0, nx - 1))]) for x, z in zip(px, pz)])
    margin_viol = int(on_shore_cell.sum())
    below_margin = int((ground < SEA_LEVEL + SEA_MARGIN).sum())
    # drainage crossings: ground lower at the centreline than 25 m either side across the road by > 3 m
    cross_l = np.array([bilinear(H, xs, zs, x - tz_ * 25.0, z + tx_ * 25.0) for x, z, tx_, tz_ in zip(px, pz, tx, tz)])
    cross_r = np.array([bilinear(H, xs, zs, x + tz_ * 25.0, z - tx_ * 25.0) for x, z, tx_, tz_ in zip(px, pz, tx, tz)])
    along_l = np.array([bilinear(H, xs, zs, x - tx_ * 25.0, z - tz_ * 25.0) for x, z, tx_, tz_ in zip(px, pz, tx, tz)])
    along_r = np.array([bilinear(H, xs, zs, x + tx_ * 25.0, z + tz_ * 25.0) for x, z, tx_, tz_ in zip(px, pz, tx, tz)])
    valley = (np.minimum(cross_l, cross_r) > ground + 3.0) | (np.minimum(along_l, along_r) > ground + 3.0)
    drainage = []
    k = 0
    while k < len(st):
        if valley[k]:
            m = k
            while m < len(st) and valley[m]:
                m += 1
            kk = k + int(np.argmin(ground[k:m]))
            drainage.append({"station_m": float(st[kk]), "at_godot_xz": [float(px[kk]), float(pz[kk])], "ground_m": float(ground[kk]),
                             "depth_m": float(min(np.minimum(cross_l, cross_r)[kk], np.minimum(along_l, along_r)[kk]) - ground[kk])})
            k = m
        else:
            k += 1
    # conflicts: distances to the references
    def min_dist_to(name, closed):
        if name not in refs:
            return None
        poly = [(p[0], p[2]) for p in refs[name]]
        return float(min(dist_to_poly(x, z, poly, closed) for x, z in zip(px[::5], pz[::5])))
    conflicts = {"city_peninsula_footprint_m": min_dist_to("city_peninsula_footprint", True),
                 "bridge_main_deck_m": min_dist_to("bridge_main_deck_footprint", True),
                 "bridge_approach_m": min_dist_to("bridge_approach_footprint", True),
                 "city_bypass_centreline_m": min_dist_to("city_bypass_centreline", False),
                 "park_envelope_m": float(min(max(ENVELOPE[0] - x, 0, x - ENVELOPE[1], ENVELOPE[2] - z, z - ENVELOPE[3]) for x, z in zip(px, pz))),
                 "coast_outline_note": "COAST_SOUTH_OUTLINE ends at z 2700 and COAST_NORTH_OUTLINE at the north shore: neither reaches the bay"}
    # retaining wall candidates: fill over 6 m on a cross slope steeper than 1:3, or cut over 8 m
    cross_slope = np.abs(cross_l - cross_r) / 50.0
    walls = []
    k = 0
    flag = ((dfill > 6.0) & (cross_slope > 1 / 3)) | (dcut > 8.0)
    while k < len(st):
        if flag[k]:
            m = k
            while m < len(st) and flag[m]:
                m += 1
            walls.append({"from_m": float(st[k]), "to_m": float(st[m - 1]), "max_fill_m": float(dfill[k:m].max()),
                          "max_cut_m": float(dcut[k:m].max()), "at_godot_xz": [float(px[k]), float(pz[k])]})
            k = m
        else:
            k += 1
    # junctions: bearings (azimuth from north, clockwise; Godot +z is south)
    def bearing(a, b):
        return float((math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1]))) + 360.0) % 360.0)

    highway = refs["coast_highway_centreline"]
    hw_sorted = sorted(highway, key=lambda p: p[2])
    hw_end, hw_prev = hw_sorted[-1], hw_sorted[-2]
    bp_end = (start[0], 0.0, start[2])
    bp_prev = (bp_back[0], 0.0, bp_back[1])
    junctions = {
        "highway_T": {"at_godot_xz": [float(end[0]), float(end[2])], "highway_bearing_in": bearing((hw_prev[0], hw_prev[2]), (hw_end[0], hw_end[2])),
                      "branch_bearing_arriving": bearing((px[-25], pz[-25]), (px[-15], pz[-15])),
                      "road_height_m": float(road[-1]), "ground_m": float(ground[-1]), "junction_back_from_highway_end_m": JUNCTION_BACK,
                      "bridge_landing_x": 580.0, "distance_to_bridge_approach_m": conflicts["bridge_approach_m"],
                      "note": "the branch arrives nearly parallel to the highway from the east: a Y merge on the seaward side, not a right-angle T"},
        "bypass_departure": {"at_godot_xz": [float(start[0]), float(start[2])], "bypass_bearing_out": bearing((bp_prev[0], bp_prev[2]), (bp_end[0], bp_end[2])),
                             "branch_bearing_leaving": bearing((px[15], pz[15]), (px[25], pz[25])), "road_height_m": float(road[0]),
                             "chainage_from_bridge_landing_m": chain, "bypass_length_m": bypass_total, "bypass_freed_beyond_m": bypass_total - chain},
    }
    for jn in junctions.values():
        a = jn.get("branch_bearing_arriving", jn.get("branch_bearing_leaving"))
        b = jn.get("highway_bearing_in", jn.get("bypass_bearing_out"))
        dev = abs((a - b + 180.0) % 360.0 - 180.0)
        jn["deflection_deg"] = dev
    # the old branch: how much of its first kilometre the new route reuses
    old = [(p[0], p[2]) for p in sorted(refs["coastal_highway_branch_centreline"], key=lambda p: p[2])]
    reuse = [dist_to_poly(x, z, old, closed=False) < 40.0 for x, z in zip(px, pz)]
    out = {"family": "bay", "cap": cap, "length_m": float(st[-1]), "climb_m": float(np.sum(np.maximum(0, np.diff(road)))),
           "descent_m": float(np.sum(np.maximum(0, -np.diff(road)))), "max_grade": float(np.abs(grade).max()),
           "K_vertical_m_per_pct": K_VERTICAL, "side_slope": "1:2 cut and fill", "corridor_w_m": CORRIDOR_W,
           "min_radius_m": float(np.min(radius[np.isfinite(radius) & (radius > 0)])) if np.isfinite(radius).any() else None,
           "radius_exceptions": [{"index": k, "at_godot_xz": [relaxed[k][0], relaxed[k][1]]} for k in exceptions],
           "corners_total": int(np.sum([1 for r_ in rad_pts if r_ not in (math.inf, 0.0)]) > 0), "fillet_min_used_m": rmin,
           "max_cut_m": float(dcut.max()), "max_fill_m": float(dfill.max()), "cut_volume_m3": cut_vol, "fill_volume_m3": fill_vol,
           "stations_cut_over_5m": int((dcut > 5).sum()), "stations_fill_over_5m": int((dfill > 5).sum()),
           "scenic_within_60m_share": float(on_water.mean()), "scenic_view_wsw_share": float(view_wsw.mean()),
           "scenic_within_60m_m": float(on_water.sum() * STATION), "leaves_water": away,
           "shore_margin_m": SHORE_MARGIN, "stations_on_last_land_cell": margin_viol, "stations_on_last_land_cell_m": margin_viol * STATION,
           "sea_margin_violations": below_margin,
           "drainage_crossings": drainage, "conflicts": conflicts, "retaining_wall_candidates": walls, "junctions": junctions,
           "old_branch_reused_m": float(sum(reuse) * STATION),
           "stations": [{"s": float(a), "x": float(b), "z": float(c), "road_y": float(d_), "ground_y": float(e), "cut": float(f_),
                         "fill": float(g_), "radius": (None if not np.isfinite(r_) else float(r_)), "grade": float(gr), "dist_water": float(dw)}
                        for a, b, c, d_, e, f_, g_, r_, gr, dw in zip(st, px, pz, road, ground, dcut, dfill, radius, grade, w_dist)]}
    with open(os.path.join(folder, "proposal_bayloop_alignment.json"), "w") as f:
        json.dump(out, f)
    print(f"route_branch: bay loop alignment: {out['length_m']:.0f} m, climb {out['climb_m']:.0f} m, max grade {out['max_grade'] * 100:.2f} %, "
          f"min radius {out['min_radius_m']}, exceptions {len(exceptions)}, max cut {out['max_cut_m']:.1f} m, max fill {out['max_fill_m']:.1f} m, "
          f"cut {cut_vol / 1e6:.3f} Mm3, fill {fill_vol / 1e6:.3f} Mm3 (1:2 side slopes), on the water {on_water.mean() * 100:.0f} % "
          f"(view W/SW {view_wsw.mean() * 100:.0f} %), leaves the water {len(away)} time(s), drainage crossings {len(drainage)}, "
          f"wall candidates {len(walls)}, stations on the last land cell {margin_viol} ({margin_viol * STATION:.0f} m), old branch reused {out['old_branch_reused_m']:.0f} m")
    print(f"route_branch: junctions {json.dumps(junctions)}")
    print(f"route_branch: radius exceptions {out['radius_exceptions']}; leaves the water {json.dumps(away)}; drainage {json.dumps(drainage)}; walls {json.dumps(walls)}")
    print(f"route_branch: conflicts {json.dumps(conflicts)}")
    align_profile_png(folder, out)


def align_profile_png(folder, out):
    from PIL import Image, ImageDraw
    W, Hh, pad = 2400, 520, 60
    img = Image.new("RGB", (W, Hh + pad), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    stt = out["stations"]
    st = np.array([q["s"] for q in stt])
    g = np.array([q["ground_y"] for q in stt])
    r = np.array([q["road_y"] for q in stt])
    hmin, hmax = -20.0, float(np.nanmax(g)) + 20.0
    s1 = st[-1]
    sx = lambda s_: pad + s_ / s1 * (W - 2 * pad)
    sy = lambda h: pad // 2 + Hh - 40 - (min(max(h, hmin), hmax) - hmin) / (hmax - hmin) * (Hh - 50)
    dr.rectangle([pad, pad // 2, W - pad, pad // 2 + Hh - 40], outline=(120, 120, 120))
    for hv in range(0, int(hmax), 25):
        dr.line([pad, sy(hv), W - pad, sy(hv)], fill=(225, 225, 225))
        dr.text((4, sy(hv) - 6), f"{hv}", fill=(90, 90, 90))
    dr.line([pad, sy(SEA_LEVEL), W - pad, sy(SEA_LEVEL)], fill=(120, 170, 230))
    for m in range(len(st) - 1):
        x0, x1 = sx(st[m]), sx(st[m + 1])
        if g[m] > r[m]:
            dr.rectangle([x0, sy(g[m]), x1 + 1, sy(r[m])], fill=(235, 150, 150))
        elif r[m] > g[m]:
            dr.rectangle([x0, sy(r[m]), x1 + 1, sy(g[m])], fill=(160, 190, 235))
    dr.line([(sx(s_), sy(h)) for s_, h in zip(st, g)], fill=(90, 90, 90), width=2)
    dr.line([(sx(s_), sy(h)) for s_, h in zip(st, r)], fill=(30, 160, 50), width=3)
    for dcx in out["drainage_crossings"]:
        dr.line([sx(dcx["station_m"]), sy(hmin), sx(dcx["station_m"]), sy(hmax)], fill=(90, 90, 220))
    dr.text((pad + 6, pad // 2 + 4), f"bay loop, 8.3 % cap, K {out['K_vertical_m_per_pct']:g} m/%: length {out['length_m']:.0f} m, climb {out['climb_m']:.0f} m, "
            f"max cut {out['max_cut_m']:.1f} m (red), max fill {out['max_fill_m']:.1f} m (blue), cut {out['cut_volume_m3'] / 1e6:.3f} Mm3, "
            f"fill {out['fill_volume_m3'] / 1e6:.3f} Mm3 with 1:2 side slopes; blue ticks: drainage crossings; grey ground, green road", fill=(20, 20, 20))
    for s_ in range(0, int(s1) + 1, 500):
        dr.text((sx(s_) - 10, pad // 2 + Hh - 36), f"{s_ / 1000:.1f} km", fill=(60, 60, 60))
    img.save(os.path.join(folder, "proposal_bayloop_profile.png"))
    print(f"route_branch: wrote {os.path.join(folder, 'proposal_bayloop_profile.png')}")


def render_align(folder, master=DEFAULT_MASTER):
    with open(os.path.join(folder, "proposal_bayloop_alignment.json")) as f:
        out = json.load(f)
    scratch = os.path.join(folder, "PROPOSAL_bay_loop.blend")
    assets = os.path.join(ROOT, "assets")
    if os.path.commonpath([os.path.abspath(folder), assets]) == assets:
        raise SystemExit("route_branch: the folder may not be under assets/")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    scene = bpy.context.scene
    obj = bpy.data.objects["terrain_world"]
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()
    coll = bpy.data.collections.get("Reference_proposals")
    if coll is None:
        coll = bpy.data.collections.new("Reference_proposals")
        bpy.data.collections["Reference"].children.link(coll)

    def curve(name, pts, colour, bevel, note=""):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = bevel
        cu.bevel_resolution = 0
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        o_ = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = colour
        nt.links.new(em.outputs[0], o_.inputs[0])
        cu.materials.append(m)
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*to_blender(*p), 1.0)
        o = bpy.data.objects.new(name, cu)
        o["kyt_proposal"] = True
        o["kyt_reference"] = True
        o["kyt_collision"] = "none"
        if note:
            o["kyt_note"] = note
        coll.objects.link(o)
        return o

    stt = out["stations"]
    centre = curve("PROPOSAL_bay_loop_centreline", [(q["x"], q["road_y"] + 2.0, q["z"]) for q in stt], (0.15, 0.8, 0.25, 1.0), 7.0,
                   "the bay loop, 8.3 % cap, heights = road profile; see proposal_bayloop_alignment.json")
    # corridor edges
    xs_ = np.array([q["x"] for q in stt])
    zs_ = np.array([q["z"] for q in stt])
    tx, tz = np.gradient(xs_), np.gradient(zs_)
    nrm = np.maximum(np.hypot(tx, tz), 1e-9)
    tx, tz = tx / nrm, tz / nrm
    for sign, nm in ((1, "left"), (-1, "right")):
        pts = [(q["x"] - sign * tz_ * CORRIDOR_W / 2, q["road_y"] + 2.0, q["z"] + sign * tx_ * CORRIDOR_W / 2) for q, tx_, tz_ in zip(stt, tx, tz)]
        curve(f"PROPOSAL_bay_loop_edge_{nm}", pts, (0.15, 0.8, 0.25, 1.0), 1.5)
    for k, dcx in enumerate(out["drainage_crossings"]):
        x, z = dcx["at_godot_xz"]
        curve(f"PROPOSAL_bay_loop_culvert_{k}", [(x - 20, dcx["ground_m"] + 3, z), (x + 20, dcx["ground_m"] + 3, z)], (0.3, 0.3, 1.0, 1.0), 4.0)
    for k, w in enumerate(out["retaining_wall_candidates"]):
        x, z = w["at_godot_xz"]
        curve(f"PROPOSAL_bay_loop_wall_{k}", [(x, 0.0, z), (x, 60.0, z)], (1.0, 0.2, 0.2, 1.0), 4.0)
    jn = out["junctions"]
    for key, col in (("highway_T", (1.0, 1.0, 1.0, 1.0)), ("bypass_departure", (1.0, 1.0, 1.0, 1.0))):
        x, z = jn[key]["at_godot_xz"]
        n = 24
        curve(f"PROPOSAL_bay_loop_junction_{key}", [(x + 40 * math.cos(2 * math.pi * i / n), jn[key]["road_height_m"] + 3.0, z + 40 * math.sin(2 * math.pi * i / n)) for i in range(n)], col, 2.5)
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.6, 0.6, 0.6, 1.0)
    sun_data = bpy.data.lights.new("scratch_sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("scratch_sun", sun_data)
    sun.rotation_euler = (0.7854, 0.0, -2.0944)
    scene.collection.objects.link(sun)
    cam_data = bpy.data.cameras.new("scratch_camera")
    cam = bpy.data.objects.new("scratch_camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 50000.0
    outputs = []

    def shoot(name):
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        outputs.append(scene.render.filepath)
        print(f"route_branch: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=2400):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(ex, ez)
        cam.location = to_blender(cx, 5000.0, cz)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            scene.render.resolution_x, scene.render.resolution_y = px, int(px * ez / ex)
        else:
            scene.render.resolution_x, scene.render.resolution_y = int(px * ex / ez), px
        shoot(name)

    def oblique(name, eye, aim, lens=35.0):
        cam_data.type = "PERSP"
        cam_data.lens = lens
        e, a = Vector(to_blender(*eye)), Vector(to_blender(*aim))
        cam.location = e
        cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1500
        shoot(name)

    xmin, xmax = min(q["x"] for q in stt) - 300, max(q["x"] for q in stt) + 300
    zmin, zmax = min(q["z"] for q in stt) - 300, max(q["z"] for q in stt) + 300
    top_down("proposal_bayloop_top.png", xmin, xmax, zmin, zmax)
    apex = min(stt, key=lambda q: -q["z"])
    oblique("proposal_bayloop_oblique_apex.png", (apex["x"] + 300.0, 260.0, apex["z"] - 900.0), (apex["x"], apex["road_y"], apex["z"]), lens=35.0)
    hx, hz = jn["highway_T"]["at_godot_xz"]
    oblique("proposal_bayloop_oblique_junction.png", (hx + 500.0, 220.0, hz + 500.0), (hx, 0.0, hz), lens=35.0)
    top_down("proposal_bayloop_junction_highway_closeup.png", hx - 250, hx + 250, hz - 250, hz + 250, px=1600)
    bx, bz = jn["bypass_departure"]["at_godot_xz"]
    top_down("proposal_bayloop_junction_bypass_closeup.png", bx - 250, bx + 250, bz - 250, bz + 250, px=1600)
    bpy.ops.wm.save_mainfile()
    with open(os.path.join(folder, "proposal_bayloop_renders.json"), "w") as f:
        json.dump({"renders": outputs}, f)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--sample" in argv:
        sample(argv[argv.index("--sample") + 1])
    elif "--route" in argv:
        folder = argv[argv.index("--route") + 1]
        fam = argv[argv.index("--family") + 1] if "--family" in argv else "bay"
        route(folder, fam)
    elif "--render" in argv:
        folder = argv[argv.index("--render") + 1]
        master = argv[argv.index("--master") + 1] if "--master" in argv else DEFAULT_MASTER
        render(folder, master)
    elif "--align" in argv:
        align(argv[argv.index("--align") + 1])
    elif "--render-align" in argv:
        folder = argv[argv.index("--render-align") + 1]
        master = argv[argv.index("--master") + 1] if "--master" in argv else DEFAULT_MASTER
        render_align(folder, master)
    elif "--best" in argv:
        folder, fam, label = argv[argv.index("--best") + 1:argv.index("--best") + 4]
        pth = os.path.join(folder, f"proposal_branch_routes_{fam}.json")
        with open(pth) as f:
            results = json.load(f)
        results["best_label"] = label
        with open(pth, "w") as f:
            json.dump(results, f)
    else:
        raise SystemExit("route_branch: --sample | --route [--family] | --best | --render | --align <folder> | --render-align <folder>")


if __name__ == "__main__":
    main()
