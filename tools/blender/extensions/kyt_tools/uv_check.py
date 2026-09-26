"""Check's UV findings, once a prop has a game mesh (R8 in prop-pipeline.md).

Painting a prop goes wrong in two quiet ways, and neither shows in the
viewport until the paint is on:

- **Overlaps.** Two UV pieces on the same spot of the canvas wear the same
  paint. That is the point for mirror twins (a right-hand end takes its left
  twin's space, so a chip on one arm is on the other), and a fault anywhere
  else: gum painted on a slat turns up on a bracket.
- **Texel density.** How many canvas pixels a metre of the prop gets. The
  texture standard is 256 px per metre; the benches are recorded exceptions
  (about 576 and 814 at 2048). A part far off the prop's own figure is
  stretched or squashed, and its paint will look coarser or finer than its
  neighbours'.

Overlaps are found by sampling the canvas on a grid (`GRID` points a side):
every triangle marks the points inside it, with the place on the model each
one lands. Points on a triangle's edge count for neither side, so pieces that
merely touch don't overlap. Where two triangles mark one point *and land on
the same place on the model* (within `SAME_SPOT_M`), paint goes to one place
and nothing is wrong: that is a face the fuse left buried against another,
facing the other way, as under the backless bench's bolt heads. Otherwise:
- two parts sharing nearly all of their space (`TWIN_SHARE` of the larger)
  either side of the middle (x) are mirror twins;
- any other two parts sharing points overlap;
- one part landing twice on a point folds.

The parts come from the `kyt_part` face record Make game mesh leaves; a mesh
without it counts as one part.
"""

import json

import numpy as np

GRID = 1024
TWIN_SHARE = 0.8
SAME_SPOT_M = 0.001
STRETCH = 0.15  # a part this far off the prop's px/m is stretched or squashed
MIN_EDGE_M = 0.002
MIN_OVERLAP_PX = 4  # in canvas pixels; less is a speck at a shared corner
LISTED = 4


def canvas_size(mesh):
    """(width of the canvas image the materials read, whether one was found)."""
    for m in mesh.materials:
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image and n.image.size[0]:
                    return n.image.size[0], True
    return 2048, False


def _arrays(mesh):
    """Triangles as (UVs n×3×2, positions n×3×3, part per triangle, names)."""
    mesh.calc_loop_triangles()
    n = len(mesh.loop_triangles)
    loops = np.empty(n * 3, dtype=np.int32)
    mesh.loop_triangles.foreach_get("loops", loops)
    verts = np.empty(n * 3, dtype=np.int32)
    mesh.loop_triangles.foreach_get("vertices", verts)
    polys = np.empty(n, dtype=np.int32)
    mesh.loop_triangles.foreach_get("polygon_index", polys)
    uv = np.empty(len(mesh.loops) * 2, dtype=np.float64)
    mesh.uv_layers.active.data.foreach_get("uv", uv)
    co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    uv, co = uv.reshape(-1, 2), co.reshape(-1, 3)
    attr = mesh.attributes.get("kyt_part")
    if attr is not None and attr.domain == "FACE":
        per_poly = np.empty(len(mesh.polygons), dtype=np.int32)
        attr.data.foreach_get("value", per_poly)
        part = per_poly[polys]
    else:
        part = np.zeros(n, dtype=np.int32)
    names = json.loads(mesh.get("kyt_parts", "[]"))
    return uv[loops].reshape(n, 3, 2), co[verts].reshape(n, 3, 3), part, names


def _samples(tri_uv):
    """Every grid point strictly inside a triangle: (flat point index, triangle
    index, and the point's two barycentric weights toward corners 1 and 2)."""
    pix, owner, ws, wt = [], [], [], []
    for t, (a, b, c) in enumerate(tri_uv * GRID):
        denom = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(denom) < 1e-9:
            continue
        x0, x1 = int(np.floor(min(a[0], b[0], c[0]) - 0.5)), int(np.ceil(max(a[0], b[0], c[0]) - 0.5))
        y0, y1 = int(np.floor(min(a[1], b[1], c[1]) - 0.5)), int(np.ceil(max(a[1], b[1], c[1]) - 0.5))
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, GRID - 1), min(y1, GRID - 1)
        if x1 < x0 or y1 < y0:
            continue
        ix, iy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        ix, iy = ix.ravel(), iy.ravel()
        px, py = ix + 0.5 - a[0], iy + 0.5 - a[1]
        s = (px * (c[1] - a[1]) - py * (c[0] - a[0])) / denom
        w = ((b[0] - a[0]) * py - (b[1] - a[1]) * px) / denom
        inside = (s > 1e-7) & (w > 1e-7) & (1 - s - w > 1e-7)
        if inside.any():
            pix.append(iy[inside].astype(np.int64) * GRID + ix[inside])
            owner.append(np.full(int(inside.sum()), t, dtype=np.int32))
            ws.append(s[inside])
            wt.append(w[inside])
    if not pix:
        return np.empty(0, np.int64), np.empty(0, np.int32), np.empty(0), np.empty(0)
    return np.concatenate(pix), np.concatenate(owner), np.concatenate(ws), np.concatenate(wt)


def _one_per_spot(pix, tri, s, t, tri_co):
    """Keep one sample per (grid point, place on the model): a second triangle
    landing on the same place as an earlier one at that point is dropped."""
    order = np.argsort(pix, kind="stable")
    pix, tri, s, t = pix[order], tri[order], s[order], t[order]
    starts = np.flatnonzero(np.r_[True, pix[1:] != pix[:-1]])
    lengths = np.diff(np.r_[starts, len(pix)])
    keep = np.ones(len(pix), dtype=bool)
    crowded = np.repeat(lengths > 1, lengths)
    if crowded.any():
        idx = np.flatnonzero(crowded)
        a = tri_co[tri[idx], 0]
        pos = np.empty((len(pix), 3))
        pos[idx] = a + s[idx, None] * (tri_co[tri[idx], 1] - a) + t[idx, None] * (tri_co[tri[idx], 2] - a)
        # Two samples at a point (mirror twins, nearly all of them) at once.
        two = starts[lengths == 2]
        keep[two + 1] = np.linalg.norm(pos[two + 1] - pos[two], axis=1) > SAME_SPOT_M
        for st, n in zip(starts[lengths > 2], lengths[lengths > 2]):
            for j in range(st + 1, st + n):
                if np.any(np.linalg.norm(pos[st:j][keep[st:j]] - pos[j], axis=1) <= SAME_SPOT_M):
                    keep[j] = False
    return pix[keep], tri[keep]


def _px_per_metre(tri_uv, tri_co, tex_px):
    """Canvas pixels per metre along each triangle edge longer than MIN_EDGE_M."""
    uv_len = np.linalg.norm(tri_uv - np.roll(tri_uv, 1, axis=1), axis=2)
    co_len = np.linalg.norm(tri_co - np.roll(tri_co, 1, axis=1), axis=2)
    keep = co_len > MIN_EDGE_M
    return (uv_len[keep] / co_len[keep]) * tex_px, keep


def run(obj):
    """Findings for a game mesh: [(level, sentence)], level WARNING or NOTE."""
    mesh = obj.data
    if not mesh.uv_layers:
        return []
    tex_px, from_canvas = canvas_size(mesh)
    tri_uv, tri_co, part, names = _arrays(mesh)
    if not len(tri_uv):
        return []
    name = lambda i: names[i] if 0 <= i < len(names) else f"part {i}"  # noqa: E731
    scale = (tex_px / GRID) ** 2  # canvas pixels per grid point
    found = []

    pix, tri, s, t = _samples(tri_uv)
    pix, tri = _one_per_spot(pix, tri, s, t, tri_co)
    owner = part[tri].astype(np.int64)
    parts = np.unique(part)

    # Folds: one part landing on two places from one grid point.
    key = owner * GRID * GRID + pix
    uniq, counts = np.unique(key, return_counts=True)
    fold_parts, fold_n = np.unique(uniq[counts > 1] // (GRID * GRID), return_counts=True)
    folds = [(name(p), n * scale) for p, n in zip(fold_parts, fold_n) if n * scale >= MIN_OVERLAP_PX]

    # Each part's own points once, then the points two or more parts share.
    own_part, own_pix = uniq // (GRID * GRID), uniq % (GRID * GRID)
    area = dict(zip(*np.unique(own_part, return_counts=True)))
    order = np.lexsort((own_part, own_pix))
    p_sorted, x_sorted = own_part[order], own_pix[order]
    starts = np.flatnonzero(np.r_[True, x_sorted[1:] != x_sorted[:-1]])
    lengths = np.diff(np.r_[starts, len(x_sorted)])
    shared = {}
    two = starts[lengths == 2]
    pair_keys = p_sorted[two] * 100_000 + p_sorted[two + 1]
    for k, n in zip(*np.unique(pair_keys, return_counts=True)):
        shared[(int(k // 100_000), int(k % 100_000))] = int(n)
    for st, n in zip(starts[lengths > 2], lengths[lengths > 2]):
        members = p_sorted[st:st + n]
        for i in range(n):
            for j in range(i + 1, n):
                pair = (int(members[i]), int(members[j]))
                shared[pair] = shared.get(pair, 0) + 1

    centre_x = {int(p): float(tri_co[part == p][:, :, 0].mean()) for p in parts}
    pairs_twin, overlaps = 0, []
    for (a, b), n in sorted(shared.items(), key=lambda kv: -kv[1]):
        if n >= TWIN_SHARE * max(area.get(a, 0), area.get(b, 0)) and centre_x[a] * centre_x[b] < 0:
            pairs_twin += 1
        elif n * scale >= MIN_OVERLAP_PX:
            overlaps.append((name(a), name(b), n * scale))

    if overlaps:
        listed = "; ".join(f"'{a}' and '{b}' ({px:,.0f} px)" for a, b, px in overlaps[:LISTED])
        more = f"; and {len(overlaps) - LISTED} more" if len(overlaps) > LISTED else ""
        found.append(("WARNING", f"UV pieces overlap, so paint on one shows on the other: {listed}{more}. "
                                 "Only mirror twins should share."))
    if folds:
        listed = "; ".join(f"'{p}' ({px:,.0f} px)" for p, px in folds[:LISTED])
        found.append(("WARNING", f"UV pieces fold over themselves: {listed}. Paint there lands in two places."))

    # Texel density, the prop's and each part's.
    ratios, keep = _px_per_metre(tri_uv, tri_co, tex_px)
    edge_part = np.repeat(part, 3).reshape(-1, 3)[keep]
    density = float(np.median(ratios)) if len(ratios) else 0.0
    off = []
    for p in parts:
        mine = ratios[edge_part == p]
        if len(mine) and density:
            d = float(np.median(mine))
            if abs(d / density - 1) > STRETCH:
                off.append((name(p), d))
    if off:
        listed = "; ".join(f"'{p}' {d:,.0f}" for p, d in off[:LISTED])
        more = f"; and {len(off) - LISTED} more" if len(off) > LISTED else ""
        found.append(("WARNING", f"Parts off the prop's texel density ({density:,.0f} px/m): {listed}{more}. "
                                 "Their paint will look coarser or finer than the rest."))

    used = len(np.unique(pix)) / (GRID * GRID)
    canvas = f"the {tex_px} canvas" if from_canvas else f"{tex_px} (no canvas yet)"
    twin_text = (f"{pairs_twin} mirror pair{'s' if pairs_twin != 1 else ''} share space"
                 if pairs_twin else "no mirror pairs")
    clean = "" if overlaps or folds else ", nothing else overlaps"
    found.append(("NOTE", f"UVs: {twin_text}{clean}; {used:.0%} of the square used; "
                          f"{density:,.0f} px per metre at {canvas}."))
    return found
