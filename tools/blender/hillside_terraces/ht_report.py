"""Phase 2 (system Python): design A, B and C on the sampled master, measure
them, assert the protected ground, and write the JSON and the rasters."""

import hashlib
import json
import os

import numpy as np

import ht_metrics as M
import ht_metrics_d as MD
import ht_views as V
from ht_fine import fine
from ht_load import Site
from ht_report_d import one_d
from ht_site import CUT_SLOPES, MEET, NEAR, PREFIX, RENDERS
from ht_surface import design
from ht_variants import build


def sha(a):
    return hashlib.sha1(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()[:12]


def jsonable(o):
    if isinstance(o, dict):
        return {k: jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, (np.floating, float)):
        return round(float(o), 3)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def master_vertices(site, moved, prot):
    """The master's 10 m vertices that a later edit would have to move (nearest raster cell moved)."""
    v = site.verts
    ii = np.clip(np.round((v["x"] - NEAR["x0"]) / NEAR["step"]).astype(int), 0, moved.shape[1] - 1)
    jj = np.clip(np.round((v["z"] - NEAR["z0"]) / NEAR["step"]).astype(int), 0, moved.shape[0] - 1)
    inside = moved[jj, ii]
    assert not (inside & (v["edit"] > 0)).any(), "the footprint reaches a vertex of an earlier authored edit"
    assert not (inside & prot[jj, ii]).any(), "the footprint reaches a protected master vertex"
    return {"in_footprint": int(inside.sum()), "earlier_edits_in_box": int((v["edit"] > 0).sum()),
            "earlier_edits_in_footprint": 0, "hash_box_vertices": sha(np.c_[v["x"], v["z"], v["y"]])}


def one(site, v):
    var = build(v, site.Ef, site.hw_line)
    res = {"variant": v, "meet_h": var["meet_h"], "meet_ground": site.Ef(*MEET), "checks": var["checks"], "profiles": var["profiles"],
           "max_grades": {k: {"pct": round(100 * g, 2), "at_s": round(s, 1)} for k, (g, s) in var["grades"].items()},
           "elements": [{"name": e["name"], "kind": e["kind"], "half": e["half"], "lots": e["lots"],
                         "pts": e["pts"].round(2), "s": e["s"].round(2), "h": e["h"].round(2), "note": e["note"],
                         "ground": np.round(site.Ea(e["pts"][:, 0], e["pts"][:, 1]), 2)}
                        for e in var["elements"]],
           "lanes": var["lanes"], "underpass": [u for u in var["underpass"] if u]}
    rasters = {}
    for k_h in CUT_SLOPES:
        D, owner, prot, cut_by = design(var["elements"], site.X, site.Z, site.E, site.hw_line, k_h, cutter=True)
        D = np.where(np.abs(D - site.E) > M.DIST_EPS, D, site.E)       # under 5 cm is no change
        vol, moved = M.volumes(site.E, D)
        assert np.array_equal(D[prot], site.E[prot]), "the design moved the highway's protected ground"
        assert not (moved & prot).any() and np.array_equal(D[~moved], site.E[~moved])
        tag = f"1:{k_h:g}"
        res[f"volumes_{tag}"] = vol
        dz = D - site.E
        vol["by_element"] = {e["name"]: {"cut_m3": round(float(-dz[(cut_by == k) & (dz < 0)].sum())),
                                         "fill_m3": round(float(dz[(cut_by == k) & (dz > 0)].sum()))}
                             for k, e in enumerate(var["elements"])}
        res[f"hashes_{tag}"] = {"protected_existing": sha(site.E[prot]), "protected_designed": sha(D[prot]),
                                "outside_existing": sha(site.E[~moved]), "outside_designed": sha(D[~moved]),
                                "protected_cells": int(prot.sum()), "footprint_cells": int(moved.sum())}
        if k_h == CUT_SLOPES[0]:
            rasters = {"D": D, "moved": moved, "owner": owner, "prot": prot}
            res["master_vertices"] = master_vertices(site, moved, prot)
    # the street to the underpass is common to B and C: its volume alone, and the terraces' without it
    conn = [e for e in var["elements"] if e["name"] == "street to the underpass"]
    if conn:
        rest = [e for e in var["elements"] if e["name"] != "street to the underpass"]
        for key, els in (("connector_only", conn), ("terraces_without_connector", rest)):
            Dx = design(els, site.X, site.Z, site.E, site.hw_line, CUT_SLOPES[0])[0]
            res[f"volumes_{key}"] = M.volumes(site.E, np.where(np.abs(Dx - site.E) > M.DIST_EPS, Dx, site.E))[0]
    D, moved, prot = rasters["D"], rasters["moved"], rasters["prot"]
    res["summit"] = MD.summit(D, site.E, site.X, site.Z)
    walls = M.walls_along(var, site.Ea, site.hw_line, CUT_SLOPES[0])
    res["walls"] = M.wall_summary(walls)
    res["wall_list"] = [w for w in walls if w["h_m"] > 0.5]
    res["lots"] = M.lots(var, site.X, site.Z, site.E, D, prot)
    res["views"] = V.compare(site, site.E, D, moved)
    res["sections"] = M.sections(var, site.Ea, site.hw_line, CUT_SLOPES[0])
    rasters["elements"] = var["elements"]
    return res, rasters


def run(folder):
    site = Site(folder)
    out = {"tool": "tools/blender/world_terrain_proposals_hillside_terraces.py", "datum": "metres over the sea = Godot y + 7.5",
           "near_raster": NEAR, "hw_line": site.hw_line.tolist(), "variants": {}}
    npz = {"E": site.E, "nx": site.nx, "nz": site.nz}
    els = {}
    for v in ("A", "B", "C"):
        res, r = one(site, v)
        out["variants"][v] = res
        els[v] = r.pop("elements")
        for k, a in r.items():
            npz[f"{k}_{v}"] = a
        vol = res["volumes_1:1"]
        print(f"hillside_terraces {v}: meet {res['meet_h']:.1f}, cut {vol['cut_m3']:.0f} m3, fill {vol['fill_m3']:.0f} m3, "
              f"deepest {vol['deepest_cut_m']:.1f} m, disturbed {vol['disturbed_m2']:.0f} m2, wall {res['walls']['highest_wall_m']} m, "
              f"lots {res['lots']['total']} {dict((k, res['lots'][k]) for k in ('cut_pad', 'natural_uphill', 'natural_downhill', 'lane'))}")
    regrades = {}
    for v in ("D1", "D2"):
        res, r = one_d(site, v, sha, master_vertices, out["variants"])
        out["variants"][v] = res
        regrades[v] = (r["D"], r["owner"], r.pop("elements"))
        for k, a in r.items():
            npz[f"{k}_{v}"] = a
        vol, sm = res["volumes"], res["summit"]
        print(f"hillside_terraces {v}: meet {res['meet_h']:.1f}, cut {vol['cut_m3']:.0f} m3, fill {vol['fill_m3']:.0f} m3, "
              f"deepest {vol['deepest_cut_m']:.1f} m, footprint {vol['disturbed_m2']:.0f} m2, summit {sm['before_m']} -> {sm['there_after_m']}, "
              f"lots {res['lots']['total']}, slopes {res['slopes']}")
    order = ["D1", "D2", "A", "B", "C"]
    out["variants"] = {v: out["variants"][v] for v in order}
    npz.update(fine(site, els, [npz[f"moved_{v}"] for v in order], regrades))
    np.savez_compressed(os.path.join(folder, "ht_design.npz"), **npz)
    with open(os.path.join(folder, "ht_report.json"), "w") as f:
        json.dump(jsonable(out), f)
    slim = jsonable({k: v for k, v in out.items() if k != "variants"})
    slim["variants"] = {v: {k: x for k, x in jsonable(r).items() if k not in ("sections", "wall_list")} for v, r in out["variants"].items()}
    for r in slim["variants"].values():
        for vw in r["views"].values():
            for k in ("az", "sky0", "sky1"):
                vw.pop(k, None)
    with open(os.path.join(RENDERS, PREFIX + "report.json"), "w") as f:
        json.dump(slim, f, indent=1)
    print(f"hillside_terraces: wrote {os.path.join(RENDERS, PREFIX + 'report.json')}")
