#!/usr/bin/env python3
"""The road corridor's natural ground and the hill over the tunnels, into the height grid.

Stage 6 of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-15). Until it, the
generator's road corridor (`terrain_road_corridor`) cut its sides to its own formula's natural
ground, blended towards the world terrain master's `Earthworks` sheet where Ground edit 6 reshaped
the hill by the coast highway, and its tunnel lids (`terrain_tunnel_lids`) laid the hill back over
each bore. The grid held whatever the master had under them: buried floors, mostly, and in the
cutting between the north tunnels the range standing over the corridor's batters. This writes,
once, as one recorded grid edit (`tools/ground_grid_edit.py`, undoable):

- **The open corridor** (grid nodes under the corridor's faces, outside every tunnel): the natural
  ground its sides are cut to, `_road_natural_y` as the generator read it (the formula, and edit
  6's sheet), into `height/`; or, where the grid's own ground stood more than `ABOVE` over the
  corridor and higher than that (so the game showed it, the range by the north tunnels), that
  ground, kept. The frozen copy, `baseline/`, takes the generator's own natural ground there,
  `_rebuild_natural_y`, so the grid's change is what the generator's corridor follows from now
  on: `WorldTerrainSource.road_natural` adds it, and the master's sheet retires. Where the copy
  counts a node outside the corridor's outline (`holes.json`; a node on the corridor's very edge),
  the copy keeps the change the node had, so nothing outside the corridor reads anything new.
- **Over the tunnels** (nodes under the lids' strip): the lid's top, or the grid's own ground where
  that stood more than `ABOVE` over it (the range over tunnel 1's west side), into both `height/`
  and `baseline/`, so the change there starts at zero; the lid's own colour where the lid was
  the top. From here the generator builds only the tunnels' portal faces and the grid is the hill.
- **Colour.** Each re-based node of the open corridor takes the generator's ground colour at its
  new height (`_rebuild_ground_colour`, sRGB), where the grid's own ground was not kept: the
  ground never shows there (the corridor does), but Christina sees and paints it.

    python3 tools/ground_corridor_bake.py [--held DIR] [--lids FILE] [--natural FILE] [--root DIR]
        [--dry] [--report FILE]

`--held` a `tools/_ground_faces_dump.gd` dump (else one is made); `--lids` the lid mesh as
`tools/_corridor_natural_dump.gd --lids` writes it (else made); `--natural` that tool's `--nodes`
reading for the same nodes, in the order this writes them (else made); `--root` another copy of
`assets/source/world_ground/`; `--report` writes the counts as JSON. It needs the generator and
reader as they stood before Stage 6 (the lids, and the master's sheet): it is the record of how
edit G9 was made, at `f5a7b4b` with this file and its two dumps.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ground_grid_edit as ge  # noqa: E402

GODOT = os.environ.get("GODOT", "/Applications/Godot.app/Contents/MacOS/Godot")
CORRIDOR = "places/park_groundworks/terrain_road_corridor"
## The grid's ground counts as shown over the corridor or a lid, and is kept, when it stands this
## far over it: the build's own margin (`ground_build.py`'s CARVE_MARGIN) the other way.
ABOVE = 0.30
NAME = "corridor_natural"
WHY = ("Stage 6: the road corridor's natural ground and the hill over the tunnels join the grid; "
       "the frozen copy re-based to the generator's natural ground there")


def godot(args, what):
    r = subprocess.run([GODOT, "--headless", "--path", ROOT, "--script"] + args, capture_output=True,
                       text=True, timeout=1800)
    out = r.stdout + r.stderr
    if r.returncode != 0 or "SCRIPT ERROR" in out or "Parse Error" in out:
        raise SystemExit("ground_corridor_bake: %s failed:\n%s" % (what, out[-3000:]))
    return out


def upward(F):
    n = np.cross(F[:, 1] - F[:, 0], F[:, 2] - F[:, 0])
    return np.abs(n[:, 1]) >= 0.05 * np.linalg.norm(n, axis=1)


def raster(F, step, extra=None):
    """Every lattice node (even metres) a face covers in plan: (columns, rows) as x / step, z / step,
    the highest face's height there, and `extra` (per corner, (n, 3, k)) interpolated on that face."""
    X, Z = F[:, :, 0], F[:, :, 2]
    c0 = np.ceil(X.min(1) / step).astype(np.int64)
    c1 = np.floor(X.max(1) / step).astype(np.int64)
    r0 = np.ceil(Z.min(1) / step).astype(np.int64)
    r1 = np.floor(Z.max(1) / step).astype(np.int64)
    w = np.maximum(c1 - c0 + 1, 0)
    h = np.maximum(r1 - r0 + 1, 0)
    cnt = w * h
    rep = np.repeat(np.arange(len(F)), cnt)
    local = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    c = c0[rep] + local % w[rep]
    r = r0[rep] + local // w[rep]
    px, pz = c * step, r * step
    A, B, C = F[rep, 0], F[rep, 1], F[rep, 2]
    d = (B[:, 0] - A[:, 0]) * (C[:, 2] - A[:, 2]) - (B[:, 2] - A[:, 2]) * (C[:, 0] - A[:, 0])
    w1 = ((px - A[:, 0]) * (C[:, 2] - A[:, 2]) - (pz - A[:, 2]) * (C[:, 0] - A[:, 0])) / d
    w2 = ((B[:, 0] - A[:, 0]) * (pz - A[:, 2]) - (B[:, 2] - A[:, 2]) * (px - A[:, 0])) / d
    ins = (w1 >= -1e-9) & (w2 >= -1e-9) & (w1 + w2 <= 1 + 1e-9)
    y = A[:, 1] + w1 * (B[:, 1] - A[:, 1]) + w2 * (C[:, 1] - A[:, 1])
    key = (c[ins] + 50000) * 200003 + (r[ins] + 50000)
    order = np.lexsort((-y[ins], key))
    k = key[order]
    first = np.ones(len(k), bool)
    first[1:] = k[1:] != k[:-1]
    sel = np.flatnonzero(ins)[order][first]
    out = {"c": c[sel], "r": r[sel], "y": y[sel]}
    if extra is not None:
        E = extra[rep[sel]]
        a, b = w1[sel][:, None], w2[sel][:, None]
        out["extra"] = E[:, 0] + a * (E[:, 1] - E[:, 0]) + b * (E[:, 2] - E[:, 0])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--held")
    ap.add_argument("--lids")
    ap.add_argument("--natural")
    ap.add_argument("--root", default=ge.GROUND)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    work = tempfile.mkdtemp(prefix="ground_corridor_bake_")
    held = a.held
    if not held:
        held = os.path.join(work, "held")
        godot(["res://tools/_ground_faces_dump.gd", "--", "--out=" + held], "the held faces dump")
    lids = a.lids
    if not lids:
        lids = os.path.join(work, "lids.f32")
        godot(["res://tools/_corridor_natural_dump.gd", "--", "--lids=" + lids], "the lids dump")

    fj = json.load(open(os.path.join(held, "faces.json")))
    F = np.fromfile(os.path.join(held, "held.f32"), "<f4").reshape(-1, 3, 3).astype(np.float64)
    piece = next(p for p in fj["held"] if p["name"] == CORRIDOR)
    corridor = F[piece["first"]:piece["first"] + piece["count"]]
    corridor = corridor[upward(corridor)]
    L = np.fromfile(lids, "<f4").reshape(-1, 3, 6).astype(np.float64)
    L = L[upward(L[:, :, :3])]

    g = ge.Grid(a.root)
    step = g.step
    cor = raster(corridor, step)
    lid = raster(L[:, :, :3], step, extra=L[:, :, 3:])
    ck = (cor["c"] + 50000) * 200003 + (cor["r"] + 50000)
    lk = (lid["c"] + 50000) * 200003 + (lid["r"] + 50000)
    open_ = ~np.isin(ck, lk)
    oc, orow, otop = cor["c"][open_], cor["r"][open_], cor["y"][open_]
    sc, srow, stop, scol = lid["c"], lid["r"], lid["y"], lid["extra"]

    X = np.concatenate([oc, sc]) * step
    Z = np.concatenate([orow, srow]) * step
    n_open = len(oc)
    inside = g.tier_of(X, Z) == 0
    if not inside.all():
        raise SystemExit("%d corridor nodes lie outside the inner tiles" % int((~inside).sum()))
    nodes = os.path.join(work, "nodes.f32")
    np.stack([X, Z], 1).astype("<f4").tofile(nodes)
    natural = a.natural
    log = ""
    if not natural:
        natural = os.path.join(work, "natural.f32")
        log = godot(["res://tools/_corridor_natural_dump.gd", "--", "--nodes=" + nodes, "--out=" + natural],
                    "the natural ground dump")
    V = np.fromfile(natural, "<f4").reshape(-1, 6).astype(np.float64)
    if len(V) != len(X):
        raise SystemExit("the natural ground dump returned %d points for %d" % (len(V), len(X)))
    N, S, RGB, mark = V[:, 0], V[:, 1], V[:, 2:5], V[:, 5] > 0.5
    now = ge._first_values(g.inner, X, Z)
    rgba = ge._first_values(g.inner, X, Z, colour=True)
    then = np.full(len(X), np.nan)
    pi, tx, tz, r, c = g.inner.homes_of(X, Z)
    keys, inv = ge._tiles_of(tx, tz)
    for j, key in enumerate(keys):
        m = inv == j
        then[pi[m]] = ge.gb.read_exr(g.inner.path("baseline", key[0], key[1], "exr"))[0][r[m], c[m]]

    top = np.concatenate([otop, stop])
    is_open = np.arange(len(X)) < n_open
    with np.errstate(invalid="ignore"):
        shown = np.isfinite(now) & (now > top + ABOVE)
    # The open corridor: the natural ground its sides are cut to, or the grid's own where the game
    # showed it standing higher still. Over a tunnel: the lid, or the grid's own over it.
    new = np.where(is_open, S, top)
    keep = shown & (now > new)
    new = np.where(keep, now, new)
    base = np.where(is_open, N, new)
    # A node the reader counts outside every held outline keeps the change it had, so no point
    # outside the corridor reads a new one.
    old_change = np.where(np.isfinite(now) & np.isfinite(then), now - then, 0.0)
    outside = ~mark
    base = np.where(outside, new - old_change, base)

    colour = np.where(is_open[:, None], RGB, np.concatenate([np.zeros((n_open, 3)), scol]))
    colour = np.clip(np.rint(colour * 255.0), 0, 255).astype(np.uint8)
    paint = ~keep
    colour_x, colour_z, colour_v = X[paint], Z[paint], colour[paint]

    report = {
        "nodes": int(len(X)), "open_corridor": int(n_open), "over_tunnels": int(len(X) - n_open),
        "kept_grid_open": int((keep & is_open).sum()), "kept_grid_tunnels": int((keep & ~is_open).sum()),
        "reader_outside": int(outside.sum()), "had_no_ground": int(np.isnan(now).sum()),
        "change_after_open": {
            "nonzero": int((np.abs(new - base)[is_open & ~outside] > 1e-3).sum()),
            "max": float(np.max(new - base, initial=0.0, where=is_open & ~outside)),
            "min": float(np.min(new - base, initial=0.0, where=is_open & ~outside)),
        },
        "sheet_nodes": int((np.abs(S - N)[is_open] > 1e-3).sum()),
        "dump": [ln for ln in log.splitlines() if ln.startswith("corridor natural dump")],
    }
    print(json.dumps(report, indent=1))
    if a.report:
        json.dump(report, open(a.report, "w"), indent=1)
    entry = ge.apply_arrays(
        a.root, NAME, WHY, X, Z, new, dry=a.dry, made_by="ground_corridor_bake.py", show=12,
        colour_x=colour_x, colour_z=colour_z, colour=colour_v,
        base_x=X, base_z=Z, base_y=base,
        extra={"stage": 6, "open_corridor_nodes": int(n_open), "tunnel_nodes": int(len(X) - n_open),
               "kept_grid_nodes": int(keep.sum())})
    if entry:
        print("%s: %d nodes, %d of the frozen copy re-based" % (entry["id"], entry["nodes"],
                                                                entry.get("baseline_nodes", 0)))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
