"""Proposals on a SCRATCH COPY of the world terrain master, never on the
master itself (2026-10-01, Christina's answers on the south range):

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/blender/world_terrain_proposals_south_range.py -- --out <folder> [--master <blend>]

Copies the master into `<folder>/PROPOSAL_south_range.blend` (refuses to
write anywhere under assets/) and renders, with scratch cameras:

- PROPOSAL A and B, a rounded coast for the wedge's south-west corner, where
  the inside-out mesh's straight base edge (z 5500) meets its diagonal west
  coast: the land mask is blurred and re-thresholded (every corner becomes a
  smooth curve) with raised-cosine biases that push a headland out and cut a
  cove in. Not noise. New land rises from sea level at the shore slope, no
  higher than the old land nearby plus a crown; land turned sea is cut to a
  shelf. A: beach, 1:10 shore, 60 m blur; B: rocky, 1:3 shore, 90 m blur,
  12 m crown. The current coast (white) and the proposed one (pink) are drawn
  as reference-style curves so she can judge them.
- The east face of the southern range connection ridges (x 200 -> -225 over
  z 5575 -> 6325): finds the foot (where the face crosses FOOT_HEIGHT) and
  the crest (the row's highest sample) per row, fits a least-squares line to
  each in plan, reports the largest deviation in metres, draws them, and
  previews ONE sinuous reshaping: each row is shifted sideways by a smooth
  offset d(z) (sum of two sines, amplitude <= TOL), resampled along x, which
  keeps every height and the x-slopes and only bends the lines in plan.

Everything here is a preview for approval. Nothing writes to the master.
"""

import json
import os
import shutil
import sys

import numpy as np

import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DEFAULT_MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
STEP = 25.0
SEA_LEVEL = -7.5

# the wedge's south-west corner: the straight base edge of the inside-out mesh
# (x about -1650..-1450 at z 5500 after the apron) meets its diagonal west
# coast in a sharp corner. The proposal rounds the corner into a headland
# with a cove beside it: the land mask is blurred (a Gaussian of SIGMA) and
# re-thresholded, which turns every corner into a smooth curve, and a
# raised-cosine bias on the threshold pulls one stretch in (a cove) and pushes
# one out (the headland). Heights then follow the new coast at the shore slope.
COAST_BOX = (-1900.0, -1300.0, 5150.0, 5750.0)  # x0, x1, z0, z1: where the coast may change
ROAD_BOX = (-1500.0, -1020.0, 3200.0, 5440.0)
COAST_OPTIONS = {
    "A": {"label": "beach", "shore_slope": 1.0 / 10.0, "sigma_m": 60.0, "crown": 4.0,
          "bias": [((-1560.0, 5560.0), 130.0, -0.22), ((-1740.0, 5420.0), 120.0, 0.18)],
          "note": "corner rounded with a 60 m blur; a low beach headland pushed out at the corner (x -1560, z 5560) and a "
                  "cove cut in on the west coast (x -1740, z 5420); 1:10 shore"},
    "B": {"label": "rocky", "shore_slope": 1.0 / 3.0, "sigma_m": 90.0, "crown": 12.0,
          "bias": [((-1520.0, 5580.0), 110.0, -0.25), ((-1700.0, 5470.0), 110.0, 0.2)],
          "note": "corner rounded with a 90 m blur; a rocky headland (x -1520, z 5580) with a 12 m crown and a cove west of it; "
                  "1:3 shore"},
}

# the east face
FACE_X = (-350.0, 350.0)
FACE_Z = (5550.0, 6350.0)
FOOT_HEIGHT = 50.0  # the steep face runs out at about this height; 20 m was a terrace on the coastal flat
TOL = 60.0  # m: the crest and foot may move this far in plan


def to_blender(x, y, z):
    return (x, -z, y)


def lattice(me):
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


def write_heights(me, co, H, idx, mask):
    sel = idx[mask]
    co[sel, 2] = H[mask]
    me.vertices.foreach_set("co", co.ravel())
    me.update()


def raised_cosine(x, centre, half_width, amp):
    t = np.clip((x - centre) / half_width, -1.0, 1.0)
    return amp * 0.5 * (1.0 + np.cos(np.pi * t))


# --- the rounded shoreline --------------------------------------------------

def gaussian_blur(mask, sigma_cells):
    r = int(np.ceil(3 * sigma_cells))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_cells) ** 2)
    k /= k.sum()
    out = mask.astype(float)
    pad = np.pad(out, ((r, r), (0, 0)), mode="edge")
    out = sum(k[i] * pad[i:i + out.shape[0], :] for i in range(2 * r + 1))
    pad = np.pad(out, ((0, 0), (r, r)), mode="edge")
    out = sum(k[i] * pad[:, i:i + out.shape[1]] for i in range(2 * r + 1))
    return out


def contour_segments(F, ux, uz, level):
    """Marching squares: the `level` contour of F as a list of segments in
    Godot (x, z)."""
    segs = []
    nz, nx = F.shape
    for j in range(nz - 1):
        for i in range(nx - 1):
            v = [F[j, i], F[j, i + 1], F[j + 1, i + 1], F[j + 1, i]]
            if any(np.isnan(v)):
                continue
            pts = []
            corners = [(ux[i], uz[j]), (ux[i + 1], uz[j]), (ux[i + 1], uz[j + 1]), (ux[i], uz[j + 1])]
            for k in range(4):
                a, b = v[k], v[(k + 1) % 4]
                if (a >= level) != (b >= level):
                    t = (level - a) / (b - a)
                    pa, pb = corners[k], corners[(k + 1) % 4]
                    pts.append((pa[0] + t * (pb[0] - pa[0]), pa[1] + t * (pb[1] - pa[1])))
            if len(pts) == 2:
                segs.append((pts[0], pts[1]))
            elif len(pts) == 4:
                segs.append((pts[0], pts[1]))
                segs.append((pts[2], pts[3]))
    return segs


def chain_segments(segs):
    """Segments into polylines (the longest first)."""
    from collections import defaultdict
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    adj = defaultdict(list)
    for a, b in segs:
        adj[key(a)].append(key(b))
        adj[key(b)].append(key(a))
    seen = set()
    lines = []
    for start in list(adj):
        if start in seen:
            continue
        # walk to an end first
        prev, cur = None, start
        for _ in range(len(adj)):
            nxt = [w for w in adj[cur] if w != prev]
            if not nxt or nxt[0] == start:
                break
            prev, cur = cur, nxt[0]
        line = [cur]
        seen.add(cur)
        prev = None
        while True:
            nxt = [w for w in adj[cur] if w != prev and w not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            line.append(cur)
        lines.append(line)
    lines.sort(key=len, reverse=True)
    return lines


def apply_coast(H, ux, uz, option):
    """A rounded coast for the south-west corner: the land mask inside the
    box is blurred and re-thresholded (threshold 0.5 plus the option's
    raised-cosine biases: below 0.5 the coast moves out, above it moves in).
    New land rises from sea level at the shore slope, never above the nearby
    old land plus the crown; land turned sea is cut to a shelf; land that
    stays keeps its height except a ramp within one cell of the water."""
    X, Z = np.meshgrid(ux, uz)
    valid = ~np.isnan(H)
    box = (X >= COAST_BOX[0]) & (X <= COAST_BOX[1]) & (Z >= COAST_BOX[2]) & (Z <= COAST_BOX[3]) & valid
    was_land = valid & (H > SEA_LEVEL)
    F = gaussian_blur(np.where(valid, was_land, 0.0), option["sigma_m"] / STEP)
    thr = np.full(H.shape, 0.5)
    for (cx, cz), radius, amp in option["bias"]:
        d = np.hypot(X - cx, Z - cz)
        thr += amp * 0.5 * (1.0 + np.cos(np.pi * np.clip(d / radius, 0.0, 1.0))) * (d < radius)
    G = F - thr
    is_land = np.where(box, G > 0.0, was_land)
    # distance to the new coast, by the blurred field's gradient (approximate) -> use a simple BFS distance in cells
    dist = np.full(H.shape, np.inf)
    coast_cells = box & is_land & ~(np.roll(is_land, 1, 0) & np.roll(is_land, -1, 0) & np.roll(is_land, 1, 1) & np.roll(is_land, -1, 1))
    cz_, cx_ = np.nonzero(coast_cells)
    if len(cz_):
        bz, bx = np.nonzero(box)
        d2 = ((ux[bx][:, None] - ux[cx_][None, :]) ** 2 + (uz[bz][:, None] - uz[cz_][None, :]) ** 2)
        dist[bz, bx] = np.sqrt(d2.min(axis=1))
    slope = option["shore_slope"]
    # the old land's height nearby, for the crown: nearest old-land sample
    oz, ox = np.nonzero(box & was_land)
    H2 = H.copy()
    new_land = box & is_land & ~was_land
    if new_land.any() and len(oz):
        nz_, nx_ = np.nonzero(new_land)
        d2 = ((ux[nx_][:, None] - ux[ox][None, :]) ** 2 + (uz[nz_][:, None] - uz[oz][None, :]) ** 2)
        near_h = H[oz, ox][np.argmin(d2, axis=1)]
        ramp = SEA_LEVEL + 0.3 + slope * dist[nz_, nx_]
        H2[nz_, nx_] = np.minimum(ramp, near_h + option["crown"])
    kept = box & is_land & was_land & (dist <= STEP * 1.5)
    H2[kept] = np.minimum(H[kept], np.maximum(SEA_LEVEL + 0.3 + slope * dist[kept], SEA_LEVEL + 0.3))
    new_sea = box & ~is_land & was_land
    H2[new_sea] = np.maximum(SEA_LEVEL - 0.5 - slope * dist[new_sea], SEA_LEVEL - 40.0)
    changed = box & (np.abs(H2 - H) > 1e-6)
    added = int(new_land.sum())
    removed = int(new_sea.sum())
    lines = chain_segments(contour_segments(np.where(box, G, np.nan), ux, uz, 0.0))
    return H2, changed, added, removed, lines


# --- the east face -----------------------------------------------------------

def face_lines(H, ux, uz):
    """Per row: the foot (the easternmost crossing of FOOT_HEIGHT on the east
    face) and the crest (the row's highest sample) in the face box."""
    jx = (ux >= FACE_X[0]) & (ux <= FACE_X[1])
    cols = np.nonzero(jx)[0]
    foot, crest = [], []
    for j in np.nonzero((uz >= FACE_Z[0]) & (uz <= FACE_Z[1]))[0]:
        row = H[j, cols]
        if np.all(np.isnan(row)):
            continue
        k = int(np.nanargmax(row))
        crest.append((float(ux[cols[k]]), float(uz[j])))
        # walk east from the crest to the first sample under FOOT_HEIGHT
        for m in range(k, len(cols) - 1):
            a, b = row[m], row[m + 1]
            if np.isnan(a) or np.isnan(b):
                break
            if a >= FOOT_HEIGHT > b:
                t = (a - FOOT_HEIGHT) / (a - b)
                foot.append((float(ux[cols[m]] + t * STEP), float(uz[j])))
                break
    return foot, crest


def fit_line(points):
    """Least squares x = a*z + b; returns (a, b, max deviation in metres)."""
    p = np.array(points)
    z, x = p[:, 1], p[:, 0]
    A = np.stack([z, np.ones_like(z)], axis=1)
    (a, b), *_ = np.linalg.lstsq(A, x, rcond=None)
    dev = np.abs(x - (a * z + b)) / np.sqrt(1.0 + a * a)
    return float(a), float(b), float(dev.max()), float(dev.mean())


def sinuous_offset(z):
    """A smooth sideways offset for the face rows: two sines, zero and flat
    at the box ends, never more than TOL."""
    t = (z - FACE_Z[0]) / (FACE_Z[1] - FACE_Z[0])
    window = np.sin(np.pi * t) ** 2
    raw = 0.7 * np.sin(2 * np.pi * t * 1.5 + 0.4) + 0.3 * np.sin(2 * np.pi * t * 3.2 + 2.0)
    return TOL * window * raw / 1.0


def apply_face(H, ux, uz):
    """Shift each face row sideways by the offset, resampling along x; the
    heights and x-slopes are kept, the lines bend in plan."""
    H2 = H.copy()
    jx = (ux >= FACE_X[0]) & (ux <= FACE_X[1])
    cols = np.nonzero(jx)[0]
    changed = np.zeros(H.shape, dtype=bool)
    for j in np.nonzero((uz >= FACE_Z[0]) & (uz <= FACE_Z[1]))[0]:
        d = float(sinuous_offset(np.array([uz[j]]))[0])
        row = H[j, :]
        valid = ~np.isnan(row)
        if valid.sum() < 2:
            continue
        src = ux[cols] - d  # the sample that moves to this column
        new = np.interp(src, ux[valid], row[valid])
        H2[j, cols] = new
        changed[j, cols] = np.abs(new - row[cols]) > 1e-6
    return H2, changed


# --- scene helpers -----------------------------------------------------------

def ref_curve(name, pts_godot, colour, bevel=6.0):
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
    sp.points.add(len(pts_godot) - 1)
    for i, p in enumerate(pts_godot):
        sp.points[i].co = (*to_blender(*p), 1.0)
    obj = bpy.data.objects.new(name, cu)
    obj["kyt_proposal"] = True
    bpy.context.scene.collection.objects.link(obj)
    return obj


class Renderer:
    def __init__(self, folder):
        self.folder = folder
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
        self.cam_data = bpy.data.cameras.new("scratch_camera")
        self.cam = bpy.data.objects.new("scratch_camera", self.cam_data)
        scene.collection.objects.link(self.cam)
        scene.camera = self.cam
        self.cam_data.clip_end = 50000.0
        self.scene = scene
        self.outputs = []

    def shoot(self, name):
        self.scene.render.filepath = os.path.join(self.folder, name)
        bpy.ops.render.render(write_still=True)
        self.outputs.append(self.scene.render.filepath)
        print(f"proposals: rendered {self.scene.render.filepath}")

    def top_down(self, name, x0, x1, z0, z1, px=1800):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        ex, ez = (x1 - x0) * 1.04, (z1 - z0) * 1.04
        self.cam_data.type = "ORTHO"
        self.cam_data.ortho_scale = max(ex, ez)
        self.cam.location = to_blender(cx, 5000.0, cz)
        self.cam.rotation_euler = (0.0, 0.0, 0.0)
        if ex >= ez:
            self.scene.render.resolution_x, self.scene.render.resolution_y = px, int(px * ez / ex)
        else:
            self.scene.render.resolution_x, self.scene.render.resolution_y = int(px * ex / ez), px
        self.shoot(name)

    def oblique(self, name, eye, aim, lens=35.0):
        self.cam_data.type = "PERSP"
        self.cam_data.lens = lens
        e, a = Vector(to_blender(*eye)), Vector(to_blender(*aim))
        self.cam.location = e
        self.cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
        self.scene.render.resolution_x, self.scene.render.resolution_y = 2400, 1500
        self.shoot(name)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--out" not in argv:
        raise SystemExit("proposals: --out <folder> is required")
    out = os.path.abspath(argv[argv.index("--out") + 1])
    master = argv[argv.index("--master") + 1] if "--master" in argv else DEFAULT_MASTER
    assets = os.path.join(ROOT, "assets")
    if os.path.commonpath([out, assets]) == assets:
        raise SystemExit("proposals: the output folder may not be under assets/")
    os.makedirs(out, exist_ok=True)
    scratch = os.path.join(out, "PROPOSAL_south_range.blend")
    shutil.copyfile(master, scratch)
    bpy.ops.wm.open_mainfile(filepath=scratch)
    obj = bpy.data.objects["terrain_world"]
    me = obj.data
    me.polygons.foreach_set("material_index", np.zeros(len(me.polygons), dtype=np.int32))
    me.update()
    co, H, idx, ux, uz = lattice(me)
    H_master = H.copy()
    rd = Renderer(out)
    report = {"master": master, "scratch": scratch}

    # --- (2) the rounded shoreline: before, then A and B
    coast_box = (-1950.0, -1250.0, 5150.0, 5750.0)
    rd.top_down("PROPOSAL_coast_before_top.png", *coast_box)
    rd.oblique("PROPOSAL_coast_before_oblique.png", (-1850.0, 260.0, 6150.0), (-1550.0, 20.0, 5450.0), lens=35.0)
    road = ref_curve("PROPOSAL_road_box", [(ROAD_BOX[0], 5.0, ROAD_BOX[2]), (ROAD_BOX[1], 5.0, ROAD_BOX[2]), (ROAD_BOX[1], 5.0, ROAD_BOX[3]),
                                           (ROAD_BOX[0], 5.0, ROAD_BOX[3]), (ROAD_BOX[0], 5.0, ROAD_BOX[2])], (1.0, 0.5, 0.0, 1.0), bevel=4.0)
    # the current coast, for reference, white
    X, Z = np.meshgrid(ux, uz)
    inbox = (X >= COAST_BOX[0]) & (X <= COAST_BOX[1]) & (Z >= COAST_BOX[2]) & (Z <= COAST_BOX[3])
    cur_lines = chain_segments(contour_segments(np.where(inbox, H_master - SEA_LEVEL, np.nan), ux, uz, 0.0))
    cur_curves = [ref_curve(f"PROPOSAL_coast_current_{k}", [(x, SEA_LEVEL + 1.0, z) for x, z in ln], (1.0, 1.0, 1.0, 1.0), bevel=3.0)
                  for k, ln in enumerate(cur_lines[:3]) if len(ln) > 1]
    for key, option in COAST_OPTIONS.items():
        H2, changed, added, removed, lines = apply_coast(H_master, ux, uz, option)
        write_heights(me, co, H2, idx, ~np.isnan(H2))
        curves = [ref_curve(f"PROPOSAL_coast_{key}_{k}", [(x, SEA_LEVEL + 1.5, z) for x, z in ln], (1.0, 0.1, 0.8, 1.0), bevel=5.0)
                  for k, ln in enumerate(lines[:3]) if len(ln) > 1]
        pts = [p for ln in lines[:3] for p in ln]
        dist_road = float(min(np.hypot(max(ROAD_BOX[0] - x, 0, x - ROAD_BOX[1]), max(ROAD_BOX[2] - z, 0, z - ROAD_BOX[3])) for x, z in pts)) if pts else None
        vol = float(np.nansum((H2 - H_master)[changed]) * STEP * STEP)
        report[f"coast_{key}"] = {"label": option["label"], "note": option["note"], "shore_slope": option["shore_slope"],
                                  "blur_sigma_m": option["sigma_m"], "bias": [list(b[0]) + [b[1], b[2]] for b in option["bias"]],
                                  "vertices_changed": int(changed.sum()), "land_added_ha": added * STEP * STEP / 1e4,
                                  "land_removed_ha": removed * STEP * STEP / 1e4, "volume_change_m3": vol,
                                  "min_distance_to_road_box_m": dist_road, "coast_polyline_points": len(pts),
                                  "max_height_change_m": float(np.abs(H2 - H_master)[changed].max()) if changed.any() else 0.0}
        print(f"proposals: coast {key}: {report[f'coast_{key}']}")
        rd.top_down(f"PROPOSAL_coast_{key}_top.png", *coast_box)
        rd.oblique(f"PROPOSAL_coast_{key}_oblique.png", (-1850.0, 260.0, 6150.0), (-1550.0, 20.0, 5450.0), lens=35.0)
        for c in curves:
            c.hide_render = True
        write_heights(me, co, H_master, idx, ~np.isnan(H_master))
    for c in cur_curves:
        c.hide_render = True
    road.hide_render = True

    # --- (3) the east face: lines, fit, preview
    foot, crest = face_lines(H_master, ux, uz)
    fa, fb, fdev, fmean = fit_line(foot)
    ca, cb, cdev, cmean = fit_line(crest)
    report["east_face"] = {"foot_points": len(foot), "foot_fit_x_eq_a_z_plus_b": [fa, fb], "foot_max_deviation_m": fdev,
                           "foot_mean_deviation_m": fmean, "crest_points": len(crest), "crest_fit": [ca, cb],
                           "crest_max_deviation_m": cdev, "crest_mean_deviation_m": cmean, "foot_height_m": FOOT_HEIGHT,
                           "face_box": [FACE_X, FACE_Z], "tolerance_m": TOL}
    print(f"proposals: east face: {report['east_face']}")
    hz = lambda pts, y: [(x, y, z) for x, z in pts]
    c_foot = ref_curve("PROPOSAL_face_foot", hz(foot, FOOT_HEIGHT + 2.0), (0.1, 0.9, 1.0, 1.0), bevel=4.0)
    c_crest = ref_curve("PROPOSAL_face_crest", [(x, float(H_master[np.argmin(np.abs(uz - z)), np.argmin(np.abs(ux - x))]) + 2.0, z) for x, z in crest],
                        (1.0, 0.9, 0.1, 1.0), bevel=4.0)
    zz = np.array([FACE_Z[0], FACE_Z[1]])
    c_ffit = ref_curve("PROPOSAL_face_foot_fit", [(fa * z + fb, FOOT_HEIGHT + 3.0, z) for z in zz], (1.0, 1.0, 1.0, 1.0), bevel=2.5)
    c_cfit = ref_curve("PROPOSAL_face_crest_fit", [(ca * z + cb, 300.0, z) for z in zz], (1.0, 1.0, 1.0, 1.0), bevel=2.5)
    face_box = (-500.0, 500.0, 5450.0, 6450.0)
    rd.top_down("PROPOSAL_face_annotated_before_top.png", *face_box)
    rd.oblique("PROPOSAL_face_before_oblique.png", (900.0, 350.0, 6100.0), (-50.0, 80.0, 5950.0), lens=35.0)
    for c in (c_foot, c_crest, c_ffit, c_cfit):
        c.hide_render = True
    H3, changed = apply_face(H_master, ux, uz)
    write_heights(me, co, H3, idx, ~np.isnan(H3))
    foot2, crest2 = face_lines(H3, ux, uz)
    fa2, fb2, fdev2, fmean2 = fit_line(foot2)
    vol = float(np.nansum((H3 - H_master)[changed]) * STEP * STEP)
    was_land, is_land = H_master > SEA_LEVEL, H3 > SEA_LEVEL
    report["east_face_preview"] = {"vertices_changed": int(changed.sum()), "max_height_change_m": float(np.abs(H3 - H_master)[changed].max()),
                                   "volume_change_m3": vol, "land_added_ha": float((changed & ~was_land & is_land).sum() * STEP * STEP / 1e4),
                                   "land_removed_ha": float((changed & was_land & ~is_land).sum() * STEP * STEP / 1e4),
                                   "foot_max_deviation_after_m": fdev2, "foot_mean_deviation_after_m": fmean2,
                                   "offset_max_m": float(np.abs(sinuous_offset(np.linspace(FACE_Z[0], FACE_Z[1], 400))).max())}
    print(f"proposals: east face preview: {report['east_face_preview']}")
    c_foot2 = ref_curve("PROPOSAL_face_foot_after", hz(foot2, FOOT_HEIGHT + 2.0), (0.1, 0.9, 1.0, 1.0), bevel=4.0)
    c_crest2 = ref_curve("PROPOSAL_face_crest_after", [(x, float(H3[np.argmin(np.abs(uz - z)), np.argmin(np.abs(ux - x))]) + 2.0, z) for x, z in crest2],
                         (1.0, 0.9, 0.1, 1.0), bevel=4.0)
    c_ffit.hide_render = False
    c_cfit.hide_render = False
    rd.top_down("PROPOSAL_face_preview_after_top.png", *face_box)
    rd.oblique("PROPOSAL_face_preview_after_oblique.png", (900.0, 350.0, 6100.0), (-50.0, 80.0, 5950.0), lens=35.0)

    report["renders"] = rd.outputs
    with open(os.path.join(out, "PROPOSAL_south_range_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    # the scratch file keeps the previews and curves for her to open; never the master
    bpy.ops.wm.save_mainfile()
    print(f"proposals: scratch file {scratch} (the master is untouched)")


if __name__ == "__main__":
    main()
