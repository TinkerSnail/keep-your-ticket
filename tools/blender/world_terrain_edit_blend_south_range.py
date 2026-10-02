"""Blend the southern foothills wedge into the range below it, in the world
terrain master (2026-10-01, Christina: "blend it into one range").

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/world_terrain_master.blend \
        --python tools/blender/world_terrain_edit_blend_south_range.py -- [--render <folder>] [--suffix <tag>] [--undo] [--dry]

The wedge of hidden foothill tops (southern_city_range_foothills and the
authored range layers, x about -1750..400, z 2975..5500) ends in a wall at
z 5475/5500: up to 171 m in one 25 m step, where the range-connection strip
below it starts 140 m lower or there is no land at all. This edit is local
and reversible:

- Polygon: the lattice vertices inside `POLY` (Godot x, z). Nothing outside
  it moves; the script proves that by hashing the rest before and after.
- Method (the coastal-branch road box `NO_RAISE` is fixed ground, left as
  sampled, so the blend works round the road): (1) symmetric slope limiting, both ends of any lattice edge
  steeper than `SLOPE_MAX` move toward each other by equal parts until no
  edge exceeds it, so the plateau comes down and the strip (or the
  placeholder sea) comes up; (2) constrained Laplacian smoothing of the
  changed zone, dilated `SMOOTH_DILATE` cells, `SMOOTH_PASSES` passes at
  `SMOOTH_LAMBDA`, with everything else fixed, which turns the 1:1 ramps
  into longer, gentler slopes; (3) the limit passes again. The apron: after
  each 1:1 pass, edges whose lower end is under `TOE_BELOW` are limited to
  `TOE_SLOPE` (1:3) too, so the foot runs out gently into the strip and the
  placeholder sea (Christina: "gentler apron is fine"; this replaced the
  first toe, which was 1:1 plus smoothing only).
- Reversible: `height_pre_edit` (float) keeps every vertex's height before
  this edit, `authored_edit` (int, 1 = this blend) marks the moved vertices,
  `ground_y_sampled` is untouched. `--undo` restores them. The edit is logged
  in the object's `kyt_edits` and the in-file README; the builder's hash
  guard names it and refuses until `--replace` rebuilds, after which this
  script is run again.
- Verification printed: untouched vertices bit-identical (hash), lossless
  check of unedited sampled vertices, slope histogram inside the polygon
  before and after, the largest height jump across any lattice edge in the
  polygon before and after, the largest slope discontinuity across the
  polygon boundary before and after, land added (placeholder-sea vertices
  lifted above sea level) and the largest height change.
"""

import hashlib
import json
import os
import sys

import numpy as np

try:
    import bpy
    from mathutils import Vector
except ImportError:  # `--plot` runs under the system Python
    bpy = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
EDIT_ID = 1
EDIT_NAME = "blend_south_range"
STEP = 25.0
POLY = [(-1700.0, 5250.0), (600.0, 5250.0), (600.0, 6350.0), (-1700.0, 6350.0)]  # Godot x, z
NO_RAISE = (-1500.0, -1020.0, 3200.0, 5440.0)  # x0, x1, z0, z1: the coastal-branch road reference; fixed, never moved
SLOPE_MAX = 1.0          # rise over run, 1:1, the hard limit
# The apron (Christina, 2026-10-01: "gentler apron is fine"): where the wedge's
# land meets the strip or the placeholder sea, edges whose lower end is below
# TOE_BELOW are limited to TOE_SLOPE as well, so the foot of the blend runs out
# at about 1:3 instead of 1:1. This replaced the first toe (1:1 + smoothing).
TOE_SLOPE = 1.0 / 3.0
TOE_BELOW = 45.0
ROUNDS = 4  # apron pass then 1:1 pass, this many times; smoothing after the first
SMOOTH_DILATE = 3        # cells round the changed zone that smoothing may touch
SMOOTH_PASSES = 40
SMOOTH_LAMBDA = 0.5
SEA_LEVEL = -7.5


def to_blender(x, y, z):
    return (x, -z, y)


def point_in_poly(x, z, poly):
    inside = np.zeros(len(x), dtype=bool)
    n = len(poly)
    for i in range(n):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % n]
        cond = (z0 > z) != (z1 > z)
        xi = x0 + (z - z0) * (x1 - x0) / (z1 - z0) if z1 != z0 else np.full_like(z, np.inf)
        inside ^= cond & (xi > x)
    return inside


def lattice(me):
    """The 25 m lattice (grid 0) of terrain_world as 2D arrays."""
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    g = np.zeros(n, dtype=np.int32)
    me.attributes["grid"].data.foreach_get("value", g)
    sel = np.nonzero(g == 0)[0]
    x, z = co[sel, 0], -co[sel, 1]
    ux, uz = np.unique(x), np.unique(z)
    ix = np.rint((x - ux[0]) / STEP).astype(int)
    iz = np.rint((z - uz[0]) / STEP).astype(int)
    H = np.full((len(uz), len(ux)), np.nan)
    H[iz, ix] = co[sel, 2]
    idx = np.full(H.shape, -1, dtype=np.int64)
    idx[iz, ix] = sel
    return co, H, idx, ux, uz


def attr(me, name):
    a = me.attributes[name]
    out = np.zeros(len(me.vertices), dtype=bool if a.data_type == "BOOLEAN" else (np.int32 if a.data_type == "INT" else float))
    a.data.foreach_get("value", out)
    return out


def edge_stats(H, mask):
    """Height differences across lattice edges with both ends in `mask`."""
    dx = np.abs(np.diff(H, axis=1))
    dz = np.abs(np.diff(H, axis=0))
    mx = mask[:, :-1] & mask[:, 1:] & ~np.isnan(dx)
    mz = mask[:-1, :] & mask[1:, :] & ~np.isnan(dz)
    return np.concatenate([dx[mx], dz[mz]])


def histogram(diffs):
    s = diffs / STEP
    bins = [("<=1:4", (s <= 0.25).sum()), ("1:4..1:2", ((s > 0.25) & (s <= 0.5)).sum()),
            ("1:2..1:1", ((s > 0.5) & (s <= 1.0)).sum()), (">1:1", (s > 1.0).sum())]
    return {k: int(v) for k, v in bins}, float(s.max()) if len(s) else 0.0


def boundary_discontinuity(H, free):
    """Across the polygon boundary: the slope just inside against the slope
    just outside along the same axis, largest difference in rise/run."""
    worst = 0.0
    nz, nx = H.shape
    for axis in (0, 1):
        A = H if axis == 0 else H.T
        F = free if axis == 0 else free.T
        for j in range(1, A.shape[0] - 2):
            inside = F[j] & ~F[j - 1]  # j is free, j-1 fixed: boundary crossing between j-1 and j
            if inside.any():
                s_in = (A[j + 1] - A[j]) / STEP
                s_out = (A[j] - A[j - 1]) / STEP
                d = np.abs(s_in - s_out)[inside]
                d = d[~np.isnan(d)]
                if len(d):
                    worst = max(worst, float(d.max()))
            inside = F[j] & ~F[j + 1]
            if inside.any():
                s_in = (A[j] - A[j - 1]) / STEP
                s_out = (A[j + 1] - A[j]) / STEP
                d = np.abs(s_in - s_out)[inside]
                d = d[~np.isnan(d)]
                if len(d):
                    worst = max(worst, float(d.max()))
    return worst


def limit_slopes(H, free, no_raise, H0, max_iter=4000, slope=SLOPE_MAX, below=None):
    """Symmetric slope limiting: every edge steeper than `slope` pulls its
    two ends together by equal parts (a fixed end does not move, so the free
    end takes it all). With `below`, only edges whose lower end is under that
    height when the pass starts take part (the apron); the set is frozen for
    the pass so it converges, and the hard 1:1 pass always runs after it."""
    lim = slope * STEP
    valid = ~np.isnan(H)
    toe = None
    if below is not None:
        toe = [np.minimum(H[:-1, :], H[1:, :]) < below, np.minimum(H[:, :-1], H[:, 1:]) < below]
    for it in range(max_iter):
        adj = np.zeros_like(H)
        cnt = np.zeros_like(H)
        for axis in (0, 1):
            a = H[:-1, :] if axis == 0 else H[:, :-1]
            b = H[1:, :] if axis == 0 else H[:, 1:]
            fa = free[:-1, :] if axis == 0 else free[:, :-1]
            fb = free[1:, :] if axis == 0 else free[:, 1:]
            va = valid[:-1, :] if axis == 0 else valid[:, :-1]
            vb = valid[1:, :] if axis == 0 else valid[:, 1:]
            d = b - a
            excess = np.abs(d) - lim
            act = (excess > 1e-6) & va & vb & (fa | fb)
            if toe is not None:
                act &= toe[axis]
            if not act.any():
                continue
            share_a = np.where(fa & fb, 0.5, np.where(fa, 1.0, 0.0))
            share_b = np.where(fa & fb, 0.5, np.where(fb, 1.0, 0.0))
            move = np.where(act, excess, 0.0) * np.sign(d)  # a moves +, b moves - when d>0
            if axis == 0:
                adj[:-1, :] += move * share_a
                adj[1:, :] -= move * share_b
                cnt[:-1, :] += act & fa
                cnt[1:, :] += act & fb
            else:
                adj[:, :-1] += move * share_a
                adj[:, 1:] -= move * share_b
                cnt[:, :-1] += act & fa
                cnt[:, 1:] += act & fb
        if not cnt.any():
            return it
        H += np.where(cnt > 0, adj / np.maximum(cnt, 1), 0.0)
    return max_iter


def smooth(H, zone, no_raise, H0):
    valid = ~np.isnan(H)
    Hf = np.where(valid, H, 0.0)
    for _ in range(SMOOTH_PASSES):
        s = np.zeros_like(H)
        c = np.zeros_like(H)
        for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(Hf, (dz, dx), axis=(0, 1))
            vv = np.roll(valid, (dz, dx), axis=(0, 1))
            if dz == 1:
                vv[0, :] = False
            if dz == -1:
                vv[-1, :] = False
            if dx == 1:
                vv[:, 0] = False
            if dx == -1:
                vv[:, -1] = False
            s += np.where(vv, sh, 0.0)
            c += vv
        mean = np.where(c > 0, s / np.maximum(c, 1), Hf)
        upd = zone & valid & (c > 0)
        Hf[upd] += SMOOTH_LAMBDA * (mean[upd] - Hf[upd])
    H[valid] = Hf[valid]


def dilate(mask, k):
    out = mask.copy()
    for _ in range(k):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render_dir = argv[argv.index("--render") + 1] if "--render" in argv else None
    suffix = argv[argv.index("--suffix") + 1] if "--suffix" in argv else ""
    undo = "--undo" in argv
    dry = "--dry" in argv
    obj = bpy.data.objects.get("terrain_world")
    if obj is None:
        raise SystemExit("blend_south_range: no terrain_world in this file")
    me = obj.data
    n = len(me.vertices)
    co_all = np.empty(n * 3)
    me.vertices.foreach_get("co", co_all)
    co_all = co_all.reshape(-1, 3)

    if undo:
        if "height_pre_edit" not in me.attributes or "authored_edit" not in me.attributes:
            raise SystemExit("blend_south_range: nothing to undo")
        pre = attr(me, "height_pre_edit")
        aid = attr(me, "authored_edit")
        sel = aid == EDIT_ID
        co_all[sel, 2] = pre[sel]
        me.vertices.foreach_set("co", co_all.ravel())
        me.attributes["authored_edit"].data.foreach_set("value", np.where(sel, 0, aid).astype(np.int32))
        edits = [e for e in json.loads(obj.get("kyt_edits", "[]")) if e.get("id") != EDIT_ID]
        obj["kyt_edits"] = json.dumps(edits)
        me["kyt_terrain_hash"] = me.get("kyt_terrain_hash")
        me.update()
        bpy.ops.wm.save_mainfile()
        print(f"blend_south_range: undone on {int(sel.sum())} vertices and saved")
        return

    existing = json.loads(obj.get("kyt_edits", "[]"))
    if any(e.get("id") == EDIT_ID for e in existing):
        raise SystemExit("blend_south_range: this edit is already applied (kyt_edits); run with --undo first")

    co, H0, idx, ux, uz = lattice(me)
    H = H0.copy()
    valid = ~np.isnan(H)
    X, Z = np.meshgrid(ux, uz)
    inpoly = point_in_poly(X.ravel(), Z.ravel(), POLY).reshape(H.shape) & valid
    nr = (X >= NO_RAISE[0]) & (X <= NO_RAISE[1]) & (Z >= NO_RAISE[2]) & (Z <= NO_RAISE[3]) & inpoly
    free = inpoly & ~nr  # the road box stays as sampled; the edit works round it
    sampled = np.zeros(H.shape, dtype=bool)
    sampled[idx >= 0] = attr(me, "sampled")[idx[idx >= 0]]
    sea = valid & ~sampled

    # before
    d_before = edge_stats(H0, inpoly)
    hist_before, max_before = histogram(d_before)
    disc_before = boundary_discontinuity(H0, inpoly)
    outside_hash_before = hashlib.sha1(co_all[np.setdiff1d(np.arange(n), idx[inpoly])].tobytes()).hexdigest()

    # the edit
    land0 = sampled & (H0 > SEA_LEVEL)

    def keep_land():  # the apron may not drown sampled land
        low = free & land0 & (H < SEA_LEVEL + 0.5)
        H[low] = SEA_LEVEL + 0.5

    iters = []
    for rnd in range(ROUNDS):
        iters.append(limit_slopes(H, free, nr, H0, slope=TOE_SLOPE, below=TOE_BELOW))
        keep_land()
        iters.append(limit_slopes(H, free, nr, H0))
        keep_land()
        if rnd == 0:
            changed = free & (np.abs(H - H0) > 0.01)
            zone = dilate(changed, SMOOTH_DILATE) & free
            smooth(H, zone, nr, H0)
            keep_land()
    iters.append(limit_slopes(H, free, nr, H0))  # the hard limit has the last word
    changed = free & (np.abs(H - H0) > 1e-6)
    assert not (np.abs(H - H0)[nr] > 0).any(), "a vertex in the road box moved"
    # what is still steeper than the limit, and why
    lim = SLOPE_MAX * STEP
    for axis in (0, 1):
        d = np.abs(np.diff(H, axis=axis))
        m = (inpoly[:-1, :] & inpoly[1:, :]) if axis == 0 else (inpoly[:, :-1] & inpoly[:, 1:])
        steep = np.nonzero(m & (d > lim + 1e-6))
        for j, i in zip(*steep):
            print(f"blend_south_range: still steep {'z' if axis == 0 else 'x'}-edge at ({ux[i]:g}, {uz[j]:g}) drop {d[j, i]:.1f} m "
                  f"no_raise {bool(nr[j, i] or (nr[j + 1, i] if axis == 0 else nr[j, i + 1]))}")

    # after
    d_after = edge_stats(H, inpoly)
    hist_after, max_after = histogram(d_after)
    disc_after = boundary_discontinuity(H, inpoly)
    delta = H - H0
    land_added = sea & changed & (H > SEA_LEVEL)
    land_lost = sampled & changed & (H0 > SEA_LEVEL) & (H <= SEA_LEVEL)
    report = {
        "id": EDIT_ID, "name": EDIT_NAME, "script": "tools/blender/world_terrain_edit_blend_south_range.py",
        "polygon_godot_xz": POLY, "no_raise_box_godot": NO_RAISE, "slope_max": SLOPE_MAX,
        "apron": {"slope": TOE_SLOPE, "below_m": TOE_BELOW,
                  "replaces": "the first toe of 2026-10-01 (1:1 limit + smoothing only), undone before this run"},
        "smoothing": {"passes": SMOOTH_PASSES, "lambda": SMOOTH_LAMBDA, "dilate_cells": SMOOTH_DILATE},
        "vertices_in_polygon": int(inpoly.sum()), "vertices_changed": int(changed.sum()),
        "max_raise_m": float(delta[changed].max()) if changed.any() else 0.0,
        "max_lower_m": float(-delta[changed].min()) if changed.any() else 0.0,
        "mean_abs_change_m": float(np.abs(delta[changed]).mean()) if changed.any() else 0.0,
        "land_added_vertices": int(land_added.sum()), "land_added_ha": float(land_added.sum() * STEP * STEP / 1e4),
        "land_lost_vertices": int(land_lost.sum()),
        "max_edge_jump_before_m": float(max_before * STEP), "max_edge_jump_after_m": float(max_after * STEP),
        "slope_hist_before": hist_before, "slope_hist_after": hist_after,
        "boundary_slope_discontinuity_before": disc_before, "boundary_slope_discontinuity_after": disc_after,
        "limit_iterations": [int(i) for i in iters], "rounds": ROUNDS, "road_box_vertices_fixed": int(nr.sum()),
    }
    for k, v in report.items():
        print(f"blend_south_range: {k}: {v}")
    if dry:
        return

    # write back
    pre = co_all[:, 2].copy()
    sel = idx[changed]
    co_all[sel, 2] = H[changed]
    me.vertices.foreach_set("co", co_all.ravel())
    if "height_pre_edit" not in me.attributes:
        me.attributes.new("height_pre_edit", "FLOAT", "POINT")
        me.attributes["height_pre_edit"].data.foreach_set("value", pre)
    aid = attr(me, "authored_edit") if "authored_edit" in me.attributes else np.zeros(n, dtype=np.int32)
    if "authored_edit" not in me.attributes:
        me.attributes.new("authored_edit", "INT", "POINT")
    aid[sel] = EDIT_ID
    me.attributes["authored_edit"].data.foreach_set("value", aid.astype(np.int32))
    me.update()

    # verify on the mesh itself
    co2 = np.empty(n * 3)
    me.vertices.foreach_get("co", co2)
    co2 = co2.reshape(-1, 3)
    outside = np.setdiff1d(np.arange(n), idx[inpoly])
    outside_hash_after = hashlib.sha1(co2[outside].tobytes()).hexdigest()
    assert outside_hash_after == outside_hash_before, "vertices outside the polygon changed"
    unedited = (aid == 0)
    assert np.array_equal(co2[unedited], co_all[unedited]) and np.array_equal(co2[unedited, 2], pre[unedited]), "an unedited vertex moved"
    gs = attr(me, "ground_y_sampled")
    smp = attr(me, "sampled")
    up = attr(me, "top_from_upray")
    chk = unedited & smp & ~up
    lossless = float(np.abs(co2[chk, 2] - gs[chk]).max())
    report["untouched_hash"] = outside_hash_after
    report["lossless_unedited_max_error_m"] = lossless
    print(f"blend_south_range: untouched hash {outside_hash_after} (equal before and after); unedited sampled vertices "
          f"against ground_y_sampled: {lossless:.2e} m")

    existing.append(report)
    obj["kyt_edits"] = json.dumps(existing)
    notes = bpy.data.texts.get("README")
    if notes:
        notes.write("\nAUTHORED EDIT 1, blend_south_range (tools/blender/world_terrain_edit_blend_south_range.py):\n"
                    f"  polygon x {POLY[0][0]:g}..{POLY[1][0]:g}, z {POLY[0][1]:g}..{POLY[2][1]:g}; {int(changed.sum())} vertices moved, "
                    f"max raise {report['max_raise_m']:.1f} m, max lower {report['max_lower_m']:.1f} m, slopes limited to 1:{1 / SLOPE_MAX:g}, "
                    f"the apron below {TOE_BELOW:g} m to 1:{1 / TOE_SLOPE:g} (replaces the first 1:1-and-smoothing toe, undone first);\n"
                    "  height_pre_edit keeps the heights before it, authored_edit = 1 marks the moved vertices; --undo restores.\n"
                    "  The road-box cliff on the coastal branch and the wedge's west face are untouched: Christina decided\n"
                    "  (2026-10-01) road wins, the hill is cut, tunnels per stretch to be decided in the earthworks pass.\n")
    bpy.ops.wm.save_mainfile()
    print(f"blend_south_range: saved {bpy.data.filepath}")

    if render_dir:
        render(render_dir, obj, H0, H, ux, uz, inpoly, suffix)
        with open(os.path.join(render_dir, f"world_terrain_south_range_blend_report{suffix}.json"), "w") as f:
            json.dump(report, f, indent=1)


def render(folder, obj, H0, H, ux, uz, inpoly, suffix=""):
    """Scratch renders after the save; the camera and sun are never saved."""
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
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
    water = bpy.data.objects.get("sea_level_water")
    obj.data.polygons.foreach_set("material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
    obj.data.update()

    def shoot(name):
        scene.render.filepath = os.path.join(folder, name)
        bpy.ops.render.render(write_still=True)
        print(f"blend_south_range: rendered {scene.render.filepath}")

    def top_down(name, x0, x1, z0, z1, px=1800):
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

    top_down(f"world_terrain_south_range_blend_after{suffix}.png", -1900.0, 2600.0, 2400.0, 6000.0)
    top_down(f"world_terrain_south_range_blend_closeup_top{suffix}.png", -1750.0, 650.0, 5050.0, 6400.0)
    oblique(f"world_terrain_south_range_blend_oblique_north{suffix}.png", (-700.0, 420.0, 6500.0), (-800.0, 120.0, 5350.0), lens=32.0)
    profiles_png(os.path.join(folder, f"world_terrain_south_range_blend_profiles{suffix}.png"), H0, H, ux, uz)


def profiles_png(path, H0, H, ux, uz):
    """Height against z at five x, before (grey) and after (red), drawn with
    PIL because this Blender has no matplotlib."""
    xs = [-1200.0, -900.0, -600.0, -300.0, 0.0]
    # the numbers first, so the plot can be drawn outside Blender too
    data = {}
    for xv in xs:
        i = int(np.argmin(np.abs(ux - xv)))
        data[f"{xv:g}"] = [(float(uz[j]), None if np.isnan(H0[j, i]) else float(H0[j, i]), None if np.isnan(H[j, i]) else float(H[j, i]))
                           for j in range(len(uz)) if 5000.0 <= uz[j] <= 6350.0]
    with open(os.path.splitext(path)[0] + ".json", "w") as f:
        json.dump(data, f)
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("blend_south_range: PIL missing in Blender's Python; plot the .json with tools/blender/world_terrain_edit_blend_south_range.py --plot")
        return
    z0, z1 = 5000.0, 6350.0
    W, Hh, pad = 1800, 300, 50
    img = Image.new("RGB", (W, Hh * len(xs) + pad), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    jz = (uz >= z0) & (uz <= z1)
    for k, xv in enumerate(xs):
        i = int(np.argmin(np.abs(ux - xv)))
        top = k * Hh + pad // 2
        hmin, hmax = -20.0, 300.0
        dr.rectangle([pad, top, W - pad, top + Hh - 30], outline=(120, 120, 120))
        for hv in (0.0, 100.0, 200.0):
            yy = top + Hh - 30 - (hv - hmin) / (hmax - hmin) * (Hh - 30)
            dr.line([pad, yy, W - pad, yy], fill=(220, 220, 220))
            dr.text((2, yy - 6), f"{hv:g}", fill=(90, 90, 90))
        for arr, col in ((H0, (150, 150, 150)), (H, (200, 40, 40))):
            pts = []
            for j in np.nonzero(jz)[0]:
                v = arr[j, i]
                if np.isnan(v):
                    continue
                px = pad + (uz[j] - z0) / (z1 - z0) * (W - 2 * pad)
                py = top + Hh - 30 - (min(max(v, hmin), hmax) - hmin) / (hmax - hmin) * (Hh - 30)
                pts.append((px, py))
            if len(pts) > 1:
                dr.line(pts, fill=col, width=2)
        dr.text((pad + 4, top + 4), f"x = {xv:g}   grey: before   red: after   (z {z0:g}..{z1:g}, sea level -7.5)", fill=(30, 30, 30))
    for zv in range(int(z0), int(z1) + 1, 250):
        px = pad + (zv - z0) / (z1 - z0) * (W - 2 * pad)
        dr.text((px - 10, Hh * len(xs) + 4), f"z {zv}", fill=(60, 60, 60))
    img.save(path)
    print(f"blend_south_range: wrote {path}")


def plot_from_json(path):
    """`python3 ... --plot <profiles.json>`: the same plot drawn with the
    system Python's PIL when Blender's has none."""
    from PIL import Image, ImageDraw
    with open(path) as f:
        data = json.load(f)
    z0, z1 = 5000.0, 6350.0
    W, Hh, pad = 1800, 300, 50
    img = Image.new("RGB", (W, Hh * len(data) + pad), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for k, (xv, rows) in enumerate(data.items()):
        top = k * Hh + pad // 2
        hmin, hmax = -20.0, 300.0
        dr.rectangle([pad, top, W - pad, top + Hh - 30], outline=(120, 120, 120))
        for hv in (0.0, 100.0, 200.0):
            yy = top + Hh - 30 - (hv - hmin) / (hmax - hmin) * (Hh - 30)
            dr.line([pad, yy, W - pad, yy], fill=(220, 220, 220))
            dr.text((2, yy - 6), f"{hv:g}", fill=(90, 90, 90))
        ys = top + Hh - 30 - (-7.5 - hmin) / (hmax - hmin) * (Hh - 30)
        dr.line([pad, ys, W - pad, ys], fill=(120, 170, 230))
        for col, which in (((150, 150, 150), 1), ((200, 40, 40), 2)):
            pts = []
            for row in rows:
                v = row[which]
                if v is None:
                    if len(pts) > 1:
                        dr.line(pts, fill=col, width=2)
                    pts = []
                    continue
                px = pad + (row[0] - z0) / (z1 - z0) * (W - 2 * pad)
                py = top + Hh - 30 - (min(max(v, hmin), hmax) - hmin) / (hmax - hmin) * (Hh - 30)
                pts.append((px, py))
            if len(pts) > 1:
                dr.line(pts, fill=col, width=2)
        dr.text((pad + 4, top + 4), f"x = {xv}   grey: before   red: after   blue: sea level   (z {z0:g}..{z1:g}, heights -20..300 m)", fill=(30, 30, 30))
    for zv in range(int(z0), int(z1) + 1, 250):
        px = pad + (zv - z0) / (z1 - z0) * (W - 2 * pad)
        dr.text((px - 10, Hh * len(data) + 4), f"z {zv}", fill=(60, 60, 60))
    out = os.path.splitext(path)[0] + ".png"
    img.save(out)
    print(f"blend_south_range: wrote {out}")


if __name__ == "__main__":
    if "--plot" in sys.argv:
        plot_from_json(sys.argv[sys.argv.index("--plot") + 1])
    else:
        main()
