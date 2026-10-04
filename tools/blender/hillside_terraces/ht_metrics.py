"""Measures of one designed variant: volumes, the deepest cut, the area
disturbed, the walls (from fine cross-sections), the lots and the sections."""

import numpy as np

from ht_geom import nearest, tangents
from ht_site import LOT_DEPTH, LOT_FRONT, LOT_MAX_DROP, LOT_RISE, NEAR, WALL_MAX
from ht_surface import design

DIST_EPS = 0.05          # a cell is disturbed when the design moves it more than this


def volumes(E, D, cell=1.0):
    dz = D - E
    cut = np.maximum(-dz, 0.0)
    fill = np.maximum(dz, 0.0)
    moved = np.abs(dz) > DIST_EPS
    j, i = np.unravel_index(int(np.argmax(cut)), cut.shape)
    return {"cut_m3": float(cut.sum() * cell), "fill_m3": float(fill.sum() * cell), "deepest_cut_m": float(cut.max()),
            "deepest_cut_at": [float(NEAR["x0"] + i * NEAR["step"]), float(NEAR["z0"] + j * NEAR["step"])],
            "deepest_fill_m": float(fill.max()), "disturbed_m2": float(moved.sum() * cell)}, moved


def section_points(e, s_at, reach, du):
    """Points across element e at station s_at, from -reach to +reach (u + is the left of travel)."""
    k = int(np.argmin(np.abs(e["s"] - s_at)))
    c = e["pts"][k]
    t = tangents(e["pts"])[k]
    n = np.array([t[1], -t[0]])
    u = np.arange(-reach, reach + du / 2, du)
    return u, c[0] + u * n[0], c[1] + u * n[1], float(np.interp(s_at, e["s"], e["h"]))


def walls_along(variant, Ea, hw_line, k_h, every=2.0, reach=45.0, du=0.25):
    """Walls found on cross-sections every `every` m along each street and steps: a wall is a run of steps
    steeper than 1:1 where the design, not the hill, made the ground (designed on at least one side)."""
    out = []
    for e in variant["elements"]:
        if e["kind"] == "head" or e["s"][-1] < 2.0:
            continue
        sts = np.arange(0.0, e["s"][-1] + 1e-6, every)
        U, XX, ZZ, HH = [], [], [], []
        for st in sts:
            u, x, z, h = section_points(e, st, reach, du)
            U.append(u)
            XX.append(x)
            ZZ.append(z)
            HH.append(h)
        X, Z = np.array(XX), np.array(ZZ)
        E = Ea(X, Z)
        D, owner, prot = design(variant["elements"], X, Z, E, hw_line, k_h)
        dz = np.diff(D, axis=1)
        designed = (np.abs(D - E) > DIST_EPS)
        des_pair = designed[:, 1:] | designed[:, :-1]
        prot_pair = prot[:, 1:] | prot[:, :-1]
        steep = (np.abs(dz) > 1.2 * du) & des_pair
        for r, st in enumerate(sts):
            for side in (1, -1):
                cols = np.arange(len(U[r]) - 1)
                cols = cols[(U[r][cols] * side) >= 0]
                if side < 0:
                    cols = cols[::-1]
                run, verge = 0.0, False
                for c in cols:
                    if steep[r, c]:
                        run += abs(dz[r, c]) - du      # less the slope's own rise over the sample
                        verge |= bool(prot_pair[r, c])
                    elif run > 0:
                        own = abs(U[r][c]) <= e["half"] + (LOT_DEPTH if e["lots"] else 0.0) + 1.5
                        if own or verge:      # each wall counted once, by the formation it stands at
                            out.append({"element": e["name"], "s": float(st), "side": side, "u": float(U[r][c]),
                                        "h_m": float(run), "x": float(X[r, c]), "z": float(Z[r, c]), "verge": verge,
                                        "portal": bool(np.interp(st, e["s"], e["wall"]) > WALL_MAX + 0.1)})
                        run, verge = 0.0, False
    return out


def wall_summary(walls, every=2.0, garage=LOT_RISE):
    """Highest wall and lengths, garage fronts (one storey at a lot's front) apart, verge walls apart."""
    ret = [w for w in walls if not w["verge"] and not w["portal"] and not (abs(w["h_m"] - garage) < 0.4)]
    verge = [w for w in walls if w["verge"]]
    portal = [w for w in walls if w["portal"] and not w["verge"]]
    top = max(ret, key=lambda w: w["h_m"]) if ret else None
    return {"highest_wall_m": round(top["h_m"], 1) if top else 0.0,
            "highest_wall_at": [round(top["x"], 1), round(top["z"], 1)] if top else None,
            "highest_wall_on": top["element"] if top else None,
            "wall_length_m": round(every * sum(1 for w in ret if w["h_m"] > 0.5), 0),
            "wall_over_4m_length_m": round(every * sum(1 for w in ret if w["h_m"] > 4.3), 0),
            "garage_front_length_m": round(every * sum(1 for w in walls if not w["verge"] and abs(w["h_m"] - garage) < 0.4), 0),
            "verge_wall_highest_m": round(max((w["h_m"] for w in verge), default=0.0), 1),
            "verge_wall_length_m": round(every * len(verge), 0),
            "portal_wall_highest_m": round(max((w["h_m"] for w in portal), default=0.0), 1),
            "portal_wall_length_m": round(every * sum(1 for w in portal if w["h_m"] > 0.5), 0)}


def lots(variant, X, Z, E, D, prot):
    """Lots of LOT_FRONT x LOT_DEPTH along the streets (and, for C, the lanes), each classed by its ground."""
    occ = np.zeros(E.shape, dtype=bool)
    res = {"cut_pad": 0, "natural_uphill": 0, "natural_downhill": 0, "lane": 0, "rects": []}
    heads = [e for e in variant["elements"] if e["kind"] == "head"]
    others = [e for e in variant["elements"] if e["kind"] != "head"]
    for e in [e for e in others if e["lots"]] + [dict(l, lane=True) for l in variant.get("lanes", []) if "lane" in l["name"]]:
        pts, s, h = np.asarray(e["pts"]), np.asarray(e["s"]), np.asarray(e["h"])
        t = tangents(pts)
        for st in np.arange(LOT_FRONT / 2 + 2.0, s[-1] - LOT_FRONT / 2 - 1.0, LOT_FRONT):
            k = int(np.argmin(np.abs(s - st)))
            for side in (1.0, -1.0):
                cu = e["half"] + LOT_DEPTH / 2
                c = pts[k] + side * cu * np.array([t[k][1], -t[k][0]])
                if any(np.hypot(*(c - hd["pts"][0])) < hd["half"] + LOT_DEPTH for hd in heads):
                    continue
                along = np.linspace(-LOT_FRONT / 2 + 0.5, LOT_FRONT / 2 - 0.5, 4)
                across = np.linspace(-LOT_DEPTH / 2 + 0.5, LOT_DEPTH / 2 - 0.5, 4)
                qx = c[0] + np.add.outer(along * t[k][0], side * across * t[k][1]).ravel()
                qz = c[1] + np.add.outer(along * t[k][1], -side * across * t[k][0]).ravel()
                ii = np.clip(np.round((qx - NEAR["x0"]) / NEAR["step"]).astype(int), 0, E.shape[1] - 1)
                jj = np.clip(np.round((qz - NEAR["z0"]) / NEAR["step"]).astype(int), 0, E.shape[0] - 1)
                if prot[jj, ii].any() or occ[jj, ii].mean() > 0.2:
                    continue
                if any((nearest(o["pts"], o["s"], qx, qz)[0] < o["half"] + 0.5).any() for o in others
                       if o is not e and o["name"] != e["name"]):
                    continue
                d, e_ = D[jj, ii], E[jj, ii]
                hh = np.interp(nearest(pts, s, qx, qz)[1], s, h)      # the street beside each sample (it climbs)
                if e.get("lane"):
                    calm = np.mean(np.abs(d - e_) < DIST_EPS) >= 0.75   # a lane lot stands on (nearly all) untouched ground
                    kind = "lane" if calm and (e_.max() - e_.min()) / LOT_DEPTH <= 1.0 else None
                elif np.all(np.abs(d - (hh + LOT_RISE)) < 0.3):
                    kind = "cut_pad"
                elif np.all(np.abs(d - e_) < DIST_EPS) and np.all(e_ >= hh - LOT_MAX_DROP) and np.all(e_ <= hh + LOT_RISE + 0.5):
                    kind = "natural_uphill" if e_.mean() >= hh.mean() else "natural_downhill"
                else:
                    kind = None
                if kind:
                    res[kind] += 1
                    occ[jj, ii] = True
                    res["rects"].append({"kind": kind, "c": [float(c[0]), float(c[1])], "t": [float(t[k][0]), float(t[k][1])],
                                         "base": float(d.min())})
    res["total"] = res["cut_pad"] + res["natural_uphill"] + res["natural_downhill"] + res["lane"]
    return res


def sections(variant, Ea, hw_line, k_h, spacing=35.0, reach=60.0, du=0.5):
    """Cross-sections every `spacing` m along each street and the steps, for the drawings."""
    out = []
    for e in variant["elements"]:
        if e["kind"] == "head":
            continue
        L = e["s"][-1]
        for st in np.arange(min(15.0, L / 2), L, spacing):
            u, x, z, h = section_points(e, st, reach, du)
            E = Ea(x, z)
            D, _, prot = design(variant["elements"], x, z, E, hw_line, k_h)
            out.append({"element": e["name"], "s": round(float(st), 1), "h": round(h, 2), "x": round(float(x[len(x) // 2]), 1),
                        "z": round(float(z[len(z) // 2]), 1), "east": 1 if x[-1] > x[0] else -1, "u": u.round(2).tolist(), "E": E.round(2).tolist(),
                        "D": D.round(2).tolist(), "prot": prot.tolist()})
    return out
