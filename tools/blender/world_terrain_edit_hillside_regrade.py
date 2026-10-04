"""Authored edit on the world terrain master: the hillside regrade, variant D1
(2026-10-02, Christina: "yes apply D1"), in the logged, reversible pattern of
edits 1-5.

Her three lines across the coast highway from the beach town become ordinary
streets (A's profiles, <= 11 %, meeting at 25.8 m over the sea) on a hill
reshaped round them: no ground steeper than 1:3 where it can be helped,
blended into today's ground over 15 m. The master is a 10 m lattice there, too
coarse for a 9 m street or an 8 x 7 m terrace, so its vertices move onto the
smooth landform (the regrade before the lots are levelled), and the streets,
the meeting, the lot pads, her lines and the footprint go into the locked
collection `Reference_hillside` for the earthworks layer. Design:
`tools/blender/world_terrain_proposals_hillside_terraces.py` (variant D1).

    Blender --background <master> --python tools/blender/world_terrain_edit_hillside_regrade.py -- \\
        [--expect-sha <sha1 of the file on disk>] [--dry] [--undo] [--render] [--report <json>]

The edit id is the next after the master's logged edits. Only vertices in the
footprint move; the coast highway's strip, the ramps, edits 1-5 and every
vertex outside are asserted hash-equal. `authored_edit` marks the moved
vertices, `height_pre_edit` holds their old heights, `kyt_edits` logs the edit
and README notes it; --undo restores the content exactly (checked by a content
fingerprint, since Blender never saves the same bytes twice).
"""

import hashlib
import json
import os
import sys

import numpy as np

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hillside_terraces"))
import ht_edit_checks as C  # noqa: E402
import ht_edit_design as Dz  # noqa: E402
import ht_edit_refs as Rf  # noqa: E402
from ht_site import RENDERS  # noqa: E402

EDIT_NAME = "hillside_regrade_D1"
SCRIPT = "tools/blender/world_terrain_edit_hillside_regrade.py"
REVIEW = (0.09, 0.20, 0.05, 1.0)   # review colour of the regraded vertices (linear), like edit 4's blue


def save():
    bpy.context.preferences.filepaths.save_version = 0      # no .blend1 beside the master
    assert not bpy.data.cameras and not bpy.data.lights, "a camera or light would be saved"
    bpy.ops.wm.save_mainfile()


def undo(obj, edits):
    entry = next((e for e in edits if e.get("name") == EDIT_NAME), None)
    if entry is None:
        raise SystemExit(f"{EDIT_NAME}: not applied, nothing to undo")
    if any(e.get("name") == "hillside_regrade_D1_refine" for e in edits):
        raise SystemExit(f"{EDIT_NAME}: edit hillside_regrade_D1_refine is built on this one; undo it first")
    eid, me = entry["id"], obj.data
    co, aid, pre = C.mesh_co(me), C.attr(me, "authored_edit", np.int32), C.attr(me, "height_pre_edit", np.float32)
    sel = aid == eid
    co[sel, 2] = pre[sel]
    me.vertices.foreach_set("co", co.ravel())
    aid[sel] = 0
    me.attributes["authored_edit"].data.foreach_set("value", aid)
    bak = f"height_shade_pre_edit{eid}"
    n = len(me.vertices)
    c, cur = np.empty(n * 4), np.empty(n * 4)
    me.color_attributes[bak].data.foreach_get("color", c)
    me.color_attributes["height_shade"].data.foreach_get("color", cur)
    c, cur = c.reshape(-1, 4), cur.reshape(-1, 4)
    cur[sel] = c[sel]
    me.color_attributes["height_shade"].data.foreach_set("color", cur.ravel())
    me.color_attributes.remove(me.color_attributes[bak])
    me.color_attributes.active_color_name = entry["active_color"]
    Rf.remove(eid)
    obj["kyt_edits"] = entry["kyt_edits_before"]
    notes = bpy.data.texts.get("README")
    if notes:
        old = notes.as_string()[:entry["readme_len_before"]]
        notes.clear()
        notes.write(old)
    me.update()
    fp = C.fingerprint(obj)
    print(f"{EDIT_NAME}: undone on {int(sel.sum())} vertices; whole mesh {C.h12(C.mesh_co(me))}; "
          f"content {fp} (before the edit {entry['fingerprint_before']}, equal {fp == entry['fingerprint_before']})")
    assert fp == entry["fingerprint_before"], "undo did not restore the file's content"
    save()


def apply(obj, edits, dry, render, report):
    me = obj.data
    if any(e.get("name") == EDIT_NAME for e in edits):
        raise SystemExit(f"{EDIT_NAME}: already applied; run with --undo first")
    eid = max([e.get("id", 0) for e in edits] + [0]) + 1
    fp0 = C.fingerprint(obj)
    site = Dz.site_from(obj)
    base, els, S, owner, prot, lots = Dz.landform(site)
    co, aid, pre = C.mesh_co(me), C.attr(me, "authored_edit", np.int32), C.attr(me, "height_pre_edit", np.float32)
    tgt, moved, _ = Dz.targets(co, S, site)
    masks = C.sets(me, co, aid, site.hw_line)
    held = moved & masks[C.STRIP]            # their faces reach into the highway's strip: they keep today's height
    moved &= ~held
    tgt[held] = co[held, 2]
    overlap = {k: int((m & moved).sum()) for k, m in masks.items()}
    assert not any(overlap.values()), f"the regrade reaches a protected set: {overlap}"
    assert np.array_equal(pre[moved], co[moved, 2].astype(np.float32)), "height_pre_edit differs on a vertex to move"
    hb = C.hashes(co, masks, moved)
    dz = S - site.E
    summary = {"id": eid, "name": EDIT_NAME, "script": SCRIPT, "date": "2026-10-02", "vertices": int(moved.sum()),
               "max_lowered_m": round(float((co[:, 2] - tgt)[moved].max()), 2), "max_raised_m": round(float((tgt - co[:, 2])[moved].max()), 2),
               "cut_m3": round(float(-dz[dz < 0].sum())), "fill_m3": round(float(dz[dz > 0].sum())),
               "footprint_ha": round(float((np.abs(dz) > Dz.EPS).sum()) / 1e4, 2), "meet_h": base["meet_h"], "lots": len(lots),
               "held_at_the_strip": int(held.sum()),
               "protected_overlap": overlap, "hashes_before": hb}
    print(f"{EDIT_NAME}: edit {eid}, " + json.dumps({k: v for k, v in summary.items() if k != "hashes_before"}))
    if dry:
        return
    readme = bpy.data.texts.get("README")
    entry = dict(summary, kyt_edits_before=obj.get("kyt_edits", "[]"), readme_len_before=len(readme.as_string()) if readme else 0,
                 active_color=me.color_attributes.active_color_name, fingerprint_before=fp0)
    n = len(me.vertices)
    cur = np.empty(n * 4)
    me.color_attributes["height_shade"].data.foreach_get("color", cur)
    me.color_attributes.new(f"height_shade_pre_edit{eid}", "FLOAT_COLOR", "POINT").data.foreach_set("color", cur)
    me.color_attributes.active_color_name = entry["active_color"]
    cur = cur.reshape(-1, 4)
    cur[moved] = REVIEW
    me.color_attributes["height_shade"].data.foreach_set("color", cur.ravel())
    co[moved, 2] = tgt[moved]
    me.vertices.foreach_set("co", co.ravel())
    aid[moved] = eid
    me.attributes["authored_edit"].data.foreach_set("value", aid)
    me.update()
    Rf.build(eid, els, S, np.abs(dz) > Dz.EPS, lots)
    entry["fidelity"] = Dz.fidelity(obj, els, Dz.moved_faces(me, moved), site.hw_line)
    co2 = C.mesh_co(me)
    ha = C.hashes(co2, masks, moved)
    for k in hb:
        if k != "whole mesh":
            assert hb[k] == ha[k], f"protected set changed: {k}"
    entry["hashes_after"] = ha
    edits.append(entry)
    obj["kyt_edits"] = json.dumps(edits)
    if readme:
        readme.write(f"\nAUTHORED EDIT {eid} ({EDIT_NAME}), {SCRIPT}, 2026-10-02: the hill across the coast highway from the beach town "
                     f"regraded round her three lines as streets (D1: meeting at {base['meet_h']:.1f} m over the sea, <= 11 %), no ground "
                     f"steeper than 1:3 where it can be helped; {int(moved.sum())} vertices of the 10 m lattice moved onto the smooth landform "
                     f"(lowered up to {summary['max_lowered_m']:.1f} m), cut {summary['cut_m3'] / 1e3:.0f}k m3. Streets, meeting, {len(lots)} lot pads, "
                     f"her lines and the footprint in Reference_hillside (locked). --undo restores exactly.\n")
    with open(report, "w") as f:
        json.dump({k: v for k, v in entry.items() if k != "kyt_edits_before"}, f, indent=1)
    save()
    print(f"{EDIT_NAME}: hashes before {hb}")
    print(f"{EDIT_NAME}: hashes after {ha}")
    print(f"{EDIT_NAME}: fidelity {json.dumps(entry['fidelity'])}")
    print(f"{EDIT_NAME}: applied as edit {eid}, saved {bpy.data.filepath}; content {fp0} -> {C.fingerprint(obj)}")
    if render:
        import ht_edit_render
        ht_edit_render.run()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    path = bpy.data.filepath
    if "--expect-sha" in argv:
        want = argv[argv.index("--expect-sha") + 1]
        with open(path, "rb") as f:
            got = hashlib.sha1(f.read()).hexdigest()
        if not got.startswith(want):
            raise SystemExit(f"{EDIT_NAME}: {path} has sha1 {got}, expected {want}: not writing")
    obj = bpy.data.objects["terrain_world"]
    edits = json.loads(obj.get("kyt_edits", "[]"))
    if "--undo" in argv:
        undo(obj, edits)
    else:
        report = argv[argv.index("--report") + 1] if "--report" in argv else os.path.join(RENDERS, "applied_hillside_regrade_report.json")
        apply(obj, edits, "--dry" in argv, "--render" in argv, report)


if __name__ == "__main__":
    main()
