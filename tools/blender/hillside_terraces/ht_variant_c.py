"""Variant C: her lines kept in plan, streets only as far as the hill lets a
street stay a street, stepped lanes beyond.

Each line is a street (B's profile, from its terrace end at <= 11 %) while
the cut face behind its lots stays within one wall and a short planted slope
(C_FACE_MAX); there it ends in a turning head with the garages, and her line
goes on as a stepped lane 4 m wide on the natural ground, houses either side
on their own stairs, up to the meeting point and down her leg as steps
(switching back within the leg's band) to the street to the underpass."""

import numpy as np

import ht_profile as P
from ht_geom import offset
from ht_site import DOWN, LOT_DEPTH, LOT_RISE, STEPS_HALF, STREET_HALF
from ht_surface import element, head
from ht_variants import C_FACE_MAX, HEAD_R, line


def face_behind(pts, h, Ef):
    """Height of the cut face behind the lots, the higher side, per station."""
    back = STREET_HALF + LOT_DEPTH
    out = []
    for side in (1.0, -1.0):
        q = offset(pts, side * back)
        out.append(np.array([Ef(*p) for p in q]) - (h + LOT_RISE))
    return np.maximum(out[0], out[1])


def lanes_variant(out, lines, Ef):
    for nm, (pp, ss, h) in lines.items():
        face = face_behind(pp, h, Ef)
        over = np.nonzero((face > C_FACE_MAX) & (ss > 5.0))[0]
        k = int(over[0]) if len(over) else len(ss) - 1
        k = max(k - int(round(HEAD_R)), 2)          # the head's far edge, not its centre, at the limit
        out["elements"].append(element(f"{nm} (street)", "street", pp[:k + 1], ss[:k + 1], h[:k + 1], STREET_HALF, True,
                                       f"her {nm}, a street to the turning head", open_start=True))
        out["elements"].append(head(f"{nm} head", pp[k], float(h[k]), HEAD_R, "turning head, the lane's garages"))
        out["profiles"][f"{nm} (street)"] = P.every(ss[:k + 1], h[:k + 1])
        out["grades"][f"{nm} (street)"] = P.max_grade(ss[:k + 1], h[:k + 1])
        k2 = min(k + int(round(HEAD_R)), len(ss) - 2)    # the lane leaves from the head's edge, up its own steps
        lp, ls = pp[k2:], ss[k2:] - ss[k2]
        lh = np.array([Ef(*p) for p in lp])
        out["lanes"].append(lane_record(f"{nm} (stepped lane)", lp, ls, lh, STEPS_HALF))
        out["elements"].append(element(f"{nm} (stepped lane)", "lane", lp, ls, lh, STEPS_HALF, False, "stepped lane on the hill"))
        out["checks"][f"{nm}_street_m"] = float(ss[k])
        out["checks"][f"{nm}_lane_m"] = float(ls[-1])
    pd, sd = line(DOWN, 1)
    hd = np.array([Ef(*p) for p in pd])
    out["lanes"].append(lane_record("leg down (steps, switching back)", pd, sd, hd, 5.0))
    out["elements"].append(element("leg down (steps, switching back)", "lane", pd, sd, hd, 2.5, False, "steps on the hill, switching back"))
    out["meet_h"] = float(Ef(*pd[0]))


def lane_record(name, pts, s, h, half):
    rise = float(abs(h[-1] - h[0]))
    run = float(s[-1])
    g = np.abs(np.diff(h)) / np.maximum(np.diff(s), 1e-9)
    # 1:2 flights with a 1.5 m landing every 12 risers climb 1.8 m in 5.1 m: 35 %; steeper ground switches back
    switchbacks = int(max(0, np.ceil(rise / 0.353 / max(run, 1e-9)) - 1))
    return {"name": name, "pts": np.asarray(pts).tolist(), "s": np.asarray(s).tolist(), "h": np.asarray(h).tolist(),
            "half": half, "rise_m": round(rise, 1), "run_m": round(run, 1), "mean_grade_pct": round(100 * rise / max(run, 1e-9), 1),
            "max_grade_pct": round(100 * float(g.max()), 1) if len(g) else 0.0, "switchbacks": switchbacks}
