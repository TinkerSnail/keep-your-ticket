"""Authored edit on the world terrain master: the hillside regrade's band beside
the coast highway refined (2026-10-03, Christina: "frees 14 lots ... if so than
yes"), following edit 5's way of refining (tools/blender/world_terrain_edit_falls.py).

Edit 6 (`hillside_regrade_D1`) had to hold every 10 m vertex whose faces reach the
highway's strip (centreline +- 17.6 m); the row they left stood above D1's
landform. Here the faces holding those vertices (on the hill's side) are dropped
and the band is re-triangulated at 3 m: the strip's part on today's surface
exactly (every old triangle edge inside the strip kept as a constraint, the
strip's edge too), the rest on D1's landform relaxed into the strip's edge and
edit 6's ground. No original vertex moves; the held ones stay, unused.

    Blender --background <master> --python tools/blender/world_terrain_edit_hillside_refine.py -- \\
        [--expect-sha <sha1 prefix>] [--dry] [--undo] [--render] [--report <json>]
"""

import hashlib
import json
import os
import sys

import numpy as np

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hillside_terraces"))
import ht_edit_checks as C  # noqa: E402
import ht_refine_apply as A  # noqa: E402
import ht_refine_checks as K  # noqa: E402
import ht_edit_refs as Rf  # noqa: E402
import ht_refine_design as RD  # noqa: E402
from ht_site import RENDERS  # noqa: E402

EDIT_NAME = "hillside_regrade_D1_refine"
NEEDS = "hillside_regrade_D1"
SCRIPT = "tools/blender/world_terrain_edit_hillside_refine.py"
TAG = "edit7_face"
GRID_NOTE = "hillside_refine_3m (edit 7, resampled from the master on the strip, D1 off it)"


def save():
    bpy.context.preferences.filepaths.save_version = 0
    assert not bpy.data.cameras and not bpy.data.lights, "a camera or light would be saved"
    bpy.ops.wm.save_mainfile()


def undo(obj, edits):
    entry = next((e for e in edits if e.get("name") == EDIT_NAME), None)
    if entry is None:
        raise SystemExit(f"{EDIT_NAME}: not applied, nothing to undo")
    me = obj.data
    n = A.undo(obj, me, TAG)
    Rf.remove(entry["id"])
    obj["kyt_grid_table"] = entry["grid_table_before"]
    obj["kyt_edits"] = entry["kyt_edits_before"]
    notes = bpy.data.texts.get("README")
    if notes:
        old = notes.as_string()[:entry["readme_len_before"]]
        notes.clear()
        notes.write(old)
    me.update()
    fp = C.fingerprint(obj)
    print(f"{EDIT_NAME}: undone, {n} faces restored; whole mesh {C.h12(C.mesh_co(me))}; content {fp} "
          f"(before {entry['fingerprint_before']}, equal {fp == entry['fingerprint_before']})")
    assert fp == entry["fingerprint_before"], "undo did not restore the file's content"
    save()


def apply(obj, edits, dry, render, report):
    me = obj.data
    if not any(e.get("name") == NEEDS for e in edits):
        raise SystemExit(f"{EDIT_NAME}: edit {NEEDS} is not applied")
    if any(e.get("name") == EDIT_NAME for e in edits):
        raise SystemExit(f"{EDIT_NAME}: already applied; run with --undo first")
    eid = max(e.get("id", 0) for e in edits) + 1
    fp0 = C.fingerprint(obj)
    d = RD.design(obj)
    g0 = K.caster(obj)
    lots_before = K.lots_on_regrade(d["lots"], g0, d["S0"], d["hw"])
    strip_xz = K.strip_points(d["poly"], d["hw"])
    strip_before = np.array([g0(x, z) for x, z in strip_xz])
    co = C.mesh_co(me)
    aid = C.attr(me, "authored_edit", np.int32)
    masks = C.sets(me, co, aid, d["hw"])
    hb = C.hashes(co, masks, np.zeros(len(co), dtype=bool))
    kinds = {k: d["plan"].kind.count(k) for k in sorted(set(d["plan"].kind))}
    summary = {"id": eid, "name": EDIT_NAME, "script": SCRIPT, "date": "2026-10-03", "faces_refined": len(d["faces"]),
               "held_vertices_freed": int(d["P"].sum()), "points": kinds, "triangles": len(d["tris"]),
               "lots_on_regrade_before": int(sum(lots_before)), "lots_d1": len(d["lots"])}
    print(f"{EDIT_NAME}: edit {eid}, " + json.dumps(summary))
    if dry:
        return
    readme = bpy.data.texts.get("README")
    entry = dict(summary, kyt_edits_before=obj.get("kyt_edits", "[]"), readme_len_before=len(readme.as_string()) if readme else 0,
                 grid_table_before=obj.get("kyt_grid_table", "[]"), fingerprint_before=fp0)
    n0, made = A.apply(obj, me, d["faces"], d["plan"], d["tris"], TAG)
    RD.attributes(me, n0, d, eid, GRID_NOTE, obj)
    co2 = C.mesh_co(me)
    ha = C.hashes(co2[:n0], {k: m for k, m in masks.items()}, np.zeros(n0, dtype=bool))
    assert all(hb[k] == ha[k] for k in hb), f"an original vertex moved: {hb} vs {ha}"
    g1 = K.caster(obj)
    strip_after = np.array([g1(x, z) for x, z in strip_xz])
    lots_after = K.lots_on_regrade(d["lots"], g1, d["S0"], d["hw"])
    new_h = co2[n0:, 2]
    freed = [lot for lot, b, a in zip(d["lots"], lots_before, lots_after) if a and not b]
    pads = [([(x, K.pad(lot, g1), z) for x, z in Rf.rect(lot["c"], lot["t"], Rf.LOT_FRONT, Rf.LOT_DEPTH)], True) for lot in freed]
    if pads:
        Rf.curve(bpy.data.collections[Rf.COLL], eid, "hillside_D1_lot_pads_refined", pads, (0.15, 0.45, 0.85, 1.0), 0.15,
                 f"{len(pads)} more of D1's lots on regraded ground once edit {eid} refined the band (low terraces, walls <= 2 m)")
    entry.update({"vertices_added": int(len(co2) - n0), "faces_added": made, "hashes": ha,
                  "strip_surface": {"points": int(len(strip_xz)), "max_abs_change_m": float(np.nanmax(np.abs(strip_after - strip_before)))},
                  "max_lowered_from_edit6_ground_m": round(float(np.max(d["today_at_new"] - new_h)), 2),
                  "max_raised_from_edit6_ground_m": round(float(np.max(new_h - d["today_at_new"])), 2),
                  "lots_on_regrade_after": int(sum(lots_after)), "lots_freed": len(freed),
                  "lots_not_on_regrade": [[round(v, 1) for v in lot["c"]] for lot, a in zip(d["lots"], lots_after) if not a],
                  "held_vertices_still_in_faces": K.held_in_faces(me, d["P"]),
                  "slopes": K.slopes(me, TAG, d["hw"]), "leg_down": K.profile(d["leg"], g1, d["hw"])})
    edits.append(entry)
    obj["kyt_edits"] = json.dumps(edits)
    if readme:
        readme.write(f"\nAUTHORED EDIT {eid} ({EDIT_NAME}), {SCRIPT}, 2026-10-03: edit 6's band beside the coast highway refined at 3 m "
                     f"(grid 4): {len(d['faces'])} faces of the 10 m lattice dropped (their {int(d['P'].sum())} held vertices left unused, none moved), "
                     f"{entry['vertices_added']} vertices and {made} triangles added; on the highway's strip they carry today's surface exactly, "
                     f"off it D1's landform. --undo restores exactly.\n")
    with open(report, "w") as f:
        json.dump({k: v for k, v in entry.items() if k not in ("kyt_edits_before", "grid_table_before")}, f, indent=1)
    save()
    print(f"{EDIT_NAME}: " + json.dumps({k: entry[k] for k in ("vertices_added", "faces_added", "strip_surface", "max_lowered_from_edit6_ground_m",
                                                               "lots_on_regrade_after", "held_vertices_still_in_faces", "slopes")}))
    print(f"{EDIT_NAME}: hashes {ha}; content {fp0} -> {C.fingerprint(obj)}; saved {bpy.data.filepath}")
    if render:
        import ht_edit_render
        ht_edit_render.run(prefix="applied_hillside_refine_")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--expect-sha" in argv:
        want = argv[argv.index("--expect-sha") + 1]
        with open(bpy.data.filepath, "rb") as f:
            got = hashlib.sha1(f.read()).hexdigest()
        if not got.startswith(want):
            raise SystemExit(f"{EDIT_NAME}: {bpy.data.filepath} has sha1 {got}, expected {want}: not writing")
    obj = bpy.data.objects["terrain_world"]
    edits = json.loads(obj.get("kyt_edits", "[]"))
    if "--undo" in argv:
        undo(obj, edits)
    else:
        report = argv[argv.index("--report") + 1] if "--report" in argv else os.path.join(RENDERS, "applied_hillside_refine_report.json")
        apply(obj, edits, "--dry" in argv, "--render" in argv, report)


if __name__ == "__main__":
    main()
