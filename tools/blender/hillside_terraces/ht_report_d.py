"""Design and measure D1 and D2 (the regrade) for the report."""

import numpy as np

import ht_metrics as M
import ht_metrics_d as MD
import ht_profile as P
import ht_views as V
from ht_site import HW_HALF, HW_VERGE, MEET
from ht_variant_d import formations, regrade, terraces
from ht_variants import hw_dist


def cutting(e, D, hw_line):
    """The ground beside a street that goes under the highway, over its last 40 m before the band and its whole run."""
    inb = np.nonzero(hw_dist(e["pts"], hw_line) <= HW_HALF + HW_VERGE)[0]
    end = int(inb[0]) if len(inb) else len(e["s"])
    sub = dict(e, pts=e["pts"][:end], s=e["s"][:end], h=e["h"][:end])
    return {"face_last_40m_m": MD.beside(sub, D, last=40.0), "face_whole_m": MD.beside(sub, D)}


def one_d(site, key, sha, master_vertices, abc):
    base, els = formations(key, site)
    E, X, Z = site.E, site.X, site.Z
    S, owner, prot, free = regrade(els, site)
    lots = MD.lots(els, S, owner, prot, X, Z)
    lot_wall = terraces(S, lots, owner)
    D = np.where(np.abs(S - E) > M.DIST_EPS, S, E)
    vol, moved = M.volumes(E, D)
    assert np.array_equal(D[prot], E[prot]), "the regrade moved the highway's protected ground"
    assert not (moved & prot).any() and np.array_equal(D[~moved], E[~moved])
    lines = [e["name"] for e in els if e["kind"] in ("street", "steps") and e["name"] != "street to the underpass"]
    under = next(e for e in els if e["name"] in ("leg down (street)", "street to the underpass"))
    ref = abc["A" if key == "D1" else "B"]
    res = {"variant": key, "meet_h": base["meet_h"], "meet_ground": site.Ef(*MEET), "checks": base["checks"],
           "profiles": base["profiles"], "lanes": [], "underpass": [u for u in base["underpass"] if u],
           "max_grades": {k: {"pct": round(100 * g, 2), "at_s": round(s, 1)} for k, (g, s) in base["grades"].items()},
           "elements": [{"name": e["name"], "kind": e["kind"], "half": e["half"], "lots": e["lots"], "pts": e["pts"].round(2),
                         "s": e["s"].round(2), "h": e["h"].round(2), "note": e["note"],
                         "ground": np.round(site.Ea(e["pts"][:, 0], e["pts"][:, 1]), 2)} for e in els],
           "volumes": vol, "slopes": MD.slopes(D, E, owner, prot, X), "walls": MD.jumps(D, E, prot),
           "lot_terrace_wall_max_m": round(lot_wall, 2),
           "lots": {"total": len(lots), "terrace": len(lots), "rects": [{k: v for k, v in l.items() if k != "cells"} for l in lots]},
           "lowered": dict(MD.lowering(els, D, E, site, lines), meeting_point_m=round(site.Ef(*MEET) - float(base["meet_h"]), 1)),
           "summit": MD.summit(D, E, X, Z),
           "cutting": dict(cutting(under, D, site.hw_line), before_walls_m=ref["walls"]["portal_wall_highest_m"],
                           before_on=ref["variant"]),
           "hashes": {"protected_existing": sha(E[prot]), "protected_designed": sha(D[prot]), "outside_existing": sha(E[~moved]),
                      "outside_designed": sha(D[~moved]), "protected_cells": int(prot.sum()), "footprint_cells": int(moved.sum())},
           "master_vertices": master_vertices(site, moved, prot)}
    res["views"] = V.compare(site, E, D, moved)
    res["sections"] = MD.sections(els, D, site)
    for e in els:
        if e["kind"] == "street" and e["name"] not in res["max_grades"]:
            g, s = P.max_grade(e["s"], e["h"])
            res["max_grades"][e["name"]] = {"pct": round(100 * g, 2), "at_s": round(s, 1)}
    return res, {"D": D, "moved": moved, "owner": owner, "prot": prot, "elements": els}
