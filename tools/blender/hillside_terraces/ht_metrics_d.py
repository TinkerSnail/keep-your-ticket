"""Measures of the regrade variants (D1, D2), taken off the designed raster."""

import numpy as np

from ht_geom import bilinear, inside, nearest, rect, tangents
from ht_site import D_BLEND, D_LOT_WALL, D_SLOPE, LOT_DEPTH, LOT_FRONT, NEAR, STREET_HALF, SUMMIT_BOX
from ht_surface import protected

HEAD_KEEP = 16.0


def cell_of(x, z):
    return int(round(z - NEAR["z0"])), int(round(x - NEAR["x0"]))


def lots(els, S, owner, prot, X, Z):
    """Low-terrace lots along the streets: walls of at most D_LOT_WALL once each lot is levelled at its mean."""
    occ = np.zeros(S.shape, dtype=bool)
    heads = [e for e in els if e["kind"] == "head"]
    out = []
    for e in [e for e in els if e["lots"]]:
        pts, s = e["pts"], e["s"]
        t = tangents(pts)
        for st in np.arange(LOT_FRONT / 2 + 2.0, s[-1] - LOT_FRONT / 2 - 1.0, LOT_FRONT):
            k = int(np.argmin(np.abs(s - st)))
            for side in (1.0, -1.0):
                c = pts[k] + side * (e["half"] + LOT_DEPTH / 2) * np.array([t[k][1], -t[k][0]])
                if any(np.hypot(*(c - h["pts"][0])) < h["half"] + LOT_DEPTH for h in heads):
                    continue
                poly = rect(c, t[k], LOT_FRONT, LOT_DEPTH)
                j0, i0 = cell_of(c[0] - 8, c[1] - 8)
                j1, i1 = cell_of(c[0] + 8, c[1] + 8)
                if j0 < 0 or i0 < 0 or j1 >= S.shape[0] or i1 >= S.shape[1]:
                    continue
                win = inside(poly, X[j0:j1, i0:i1], Z[j0:j1, i0:i1])
                jj, ii = np.nonzero(win)
                jj, ii = jj + j0, ii + i0
                if prot[jj, ii].any() or (owner[jj, ii] >= 0).any() or occ[jj, ii].any():
                    continue
                v = S[jj, ii]
                wall = max(float(v.max() - v.mean()), float(v.mean() - v.min()))
                if wall > D_LOT_WALL:
                    continue
                occ[jj, ii] = True
                out.append({"kind": "terrace", "c": [float(c[0]), float(c[1])], "t": [float(t[k][0]), float(t[k][1])],
                            "wall": wall, "cells": (jj, ii)})
    return out


def slopes(D, E, owner, prot, X):
    """Slope classes over the regraded ground (changed by more than 1 m); the rim is within D_BLEND of unchanged ground."""
    gz, gx = np.gradient(D, NEAR["step"])
    sl = np.hypot(gx, gz)
    reg = (np.abs(D - E) > 1.0) & (owner < 0) & ~prot
    calm = np.abs(D - E) <= 0.05
    near_calm = np.zeros(D.shape, dtype=bool)
    near_calm[:] = calm
    for _ in range(int(D_BLEND)):
        n = near_calm.copy()
        n[1:, :] |= near_calm[:-1, :]
        n[:-1, :] |= near_calm[1:, :]
        n[:, 1:] |= near_calm[:, :-1]
        n[:, :-1] |= near_calm[:, 1:]
        near_calm = n
    steep, vsteep = reg & (sl > D_SLOPE * 1.08), reg & (sl > 0.5)
    k = int(np.argmax(np.where(reg & ~near_calm, sl, 0)))
    j, i = np.unravel_index(k, D.shape)
    return {"regraded_m2": int(reg.sum()), "over_1_3_m2": int(steep.sum()), "over_1_2_m2": int(vsteep.sum()),
            "over_1_3_at_rim_m2": int((steep & near_calm).sum()), "over_1_3_inside_m2": int((steep & ~near_calm).sum()),
            "steepest_inside": round(float(sl[j, i]), 2), "steepest_inside_at": [float(X[0, i]), float(NEAR["z0"] + j)]}


def jumps(D, E, prot, near=6):
    """Walls: steps between neighbouring cells where the design made the ground; those within `near` m of the
    highway's band are the underpass portal's wing walls and the verge, the rest anything else."""
    out = {"verge": 0.0, "other": 0.0}
    band = prot.copy()
    for _ in range(near):
        n = band.copy()
        n[1:, :] |= band[:-1, :]
        n[:-1, :] |= band[1:, :]
        n[:, 1:] |= band[:, :-1]
        n[:, :-1] |= band[:, 1:]
        band = n
    for ax in (0, 1):
        dd = np.abs(np.diff(D, axis=ax))
        des = (np.abs(np.diff(D - E, axis=ax)) > 0.05)
        pv = (band[1:, :] | band[:-1, :]) if ax == 0 else (band[:, 1:] | band[:, :-1])
        out["verge"] = max(out["verge"], float(np.where(des & pv, dd, 0).max()))
        out["other"] = max(out["other"], float(np.where(des & ~pv, dd, 0).max()))
    return {k: round(v, 1) for k, v in out.items()}


def lowering(els, D, E, site, names):
    out = {}
    for e in els:
        if e["name"] not in names:
            continue
        p = e["pts"]
        d = site.Ea(p[:, 0], p[:, 1]) - bilinear(D, NEAR["x0"], NEAR["z0"], NEAR["step"], p[:, 0], p[:, 1])
        out[e["name"]] = {"max_m": round(float(d.max()), 1), "mean_m": round(float(d.mean()), 1)}
    return out


def summit(D, E, X, Z):
    x0, x1, z0, z1 = SUMMIT_BOX
    m = (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
    j0, i0 = np.unravel_index(int(np.argmax(np.where(m, E, -1e9))), E.shape)
    j1, i1 = np.unravel_index(int(np.argmax(np.where(m, D, -1e9))), E.shape)
    return {"before_m": round(float(E[j0, i0]), 1), "before_at": [float(X[j0, i0]), float(Z[j0, i0])],
            "there_after_m": round(float(D[j0, i0]), 1), "drop_m": round(float(E[j0, i0] - D[j0, i0]), 1),
            "highest_in_box_after_m": round(float(D[j1, i1]), 1), "highest_in_box_after_at": [float(X[j1, i1]), float(Z[j1, i1])]}


def beside(e, D, last=None):
    """Highest ground over the street within 3-10 m of its formation edge (the face a wall would hold), over its
    last `last` m before the highway's band or its whole length."""
    s = e["s"]
    sel = np.ones(len(s), dtype=bool) if last is None else (s >= s[-1] - last)
    t = tangents(e["pts"])
    best = 0.0
    for k in np.nonzero(sel)[0][::2]:
        for side in (1.0, -1.0):
            for u in np.arange(e["half"] + 3.0, e["half"] + 10.0, 1.0):
                q = e["pts"][k] + side * u * np.array([t[k][1], -t[k][0]])
                best = max(best, float(bilinear(D, NEAR["x0"], NEAR["z0"], NEAR["step"], q[0], q[1]) - e["h"][k]))
    return round(best, 1)


def sections(els, D, site, spacing=35.0, reach=60.0, du=0.5):
    out = []
    for e in els:
        if e["kind"] in ("head", "context"):
            continue
        L = e["s"][-1]
        for st in np.arange(min(15.0, L / 2), L, spacing):
            k = int(np.argmin(np.abs(e["s"] - st)))
            c, t = e["pts"][k], tangents(e["pts"])[k]
            u = np.arange(-reach, reach + du / 2, du)
            x, z = c[0] + u * t[1], c[1] - u * t[0]
            E = site.Ea(x, z)
            Dv = bilinear(D, NEAR["x0"], NEAR["z0"], NEAR["step"], x, z)
            out.append({"element": e["name"], "s": round(float(st), 1), "h": round(float(e["h"][k]), 2), "x": round(float(c[0]), 1),
                        "z": round(float(c[1]), 1), "east": 1 if x[-1] > x[0] else -1, "u": u.round(2).tolist(),
                        "E": E.round(2).tolist(), "D": Dv.round(2).tolist(), "prot": protected(x, z, site.hw_line).tolist()})
    return out
