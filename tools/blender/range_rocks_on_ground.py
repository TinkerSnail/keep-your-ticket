"""The range source's rocks keep their sink depth when the ground under them changes (2026-10-12;
on the height grid since 2026-10-14, height-grid plan Stage 3).

    Blender --background --factory-startup assets/source/range_forest_distinct_background.blend
        --python tools/blender/range_rocks_on_ground.py -- --id <id> --delta <change.npz> [--dry]
    ... -- --id <id> --keep-feet <census.json> --names <rock,rock,...> [--heights <dir>] [--dry]
    ... -- --id <id> --undo [--dry] [--missing-ok]      (-- --edit <n> --undo: the master's edits)

The ground is the height grid's bilinear surface (`tools/ground_follow.py`, which runs this with
`--delta`, the grid's change node by node, after less before). Each rock in `ROCKS` moves up or
down by the change under its foot, its lowest vertex, so the foot sits as deep in the new ground
as in the old; nothing moves in plan. The foot is where the floater census measures how deep a
rock sits. Not its centre: beach rock 0200 by the plug straddles the shore wall the 2 m grid made
a slope, and the ground rose 5.2 m under its centre and fell 2.7 m under its foot. Where the ground
moved unevenly under a rock (by more than `UNEVEN` between its vertices) no rigid move keeps every
part as it sat, and the result names it.

`--keep-feet` sets each named rock's foot on the grid's ground (`--heights`, default the tree's)
at the depth a floater census recorded for it: Stage 2's leftovers, recorded on the master's
ground at `1926e71`, were seated so (id `stage2`).

Each rock moved keeps how far as `kyt_ground_moved_<id>`; `--undo` puts back what that id moved,
in any order (the master's edits too: 106's as `kyt_ground_moved_m` with `kyt_ground_moved_by`).
Logged in the file's README text, saved only when something moved, and the last line printed is
`FOLLOW_RESULT {json}`. Re-export with `tools/export_world_source.sh` afterwards (ground_follow
does).
"""
import datetime
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import ground_follow as gf  # noqa: E402  (the grid's reader)

ROCKS = ("range_main_beach_middle_band_rocks", "range_remaining_beach_rocks", "range_beach_rocks", "range_base_boulders")
# Less than this is left where it is.
MIN_MOVE = 0.05
# The ground's change differing by more than this between a rock's vertices is named.
UNEVEN = 0.25


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def rocks():
    out = {}
    for name in ROCKS:
        for ob in bpy.data.collections[name].all_objects:
            if ob.type == 'MESH':
                out[ob.name] = ob
    return [out[n] for n in sorted(out)]


def vertices(obs):
    """World vertices of each rock, as Godot (x, z, y) arrays, and each one's lowest vertex."""
    dg = bpy.context.evaluated_depsgraph_get()
    per = []
    for ob in obs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
        m = np.array(ev.matrix_world)
        co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        per.append(np.stack([co[:, 0], -co[:, 1], co[:, 2]], axis=1))
    return per


def readme(line):
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n" + line + "\n")


def done(moved, saved, **extra):
    print("FOLLOW_RESULT " + json.dumps({"moved": {k: round(v, 3) for k, v in moved.items()}, "saved": saved, **extra}))


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()


def undo(fid, dry, missing_ok):
    key = "kyt_ground_moved_%s" % fid
    legacy = int(fid) if fid.isdigit() else None
    obs = rocks()
    moved = {}
    for ob in obs:
        if key in ob:
            moved[ob.name] = -ob[key]
        elif legacy is not None and ob.get("kyt_ground_moved_by") == legacy:
            moved[ob.name] = -ob["kyt_ground_moved_m"]
    if not moved:
        if missing_ok:
            print("range_rocks_on_ground: no rock was moved by %s" % fid)
            return done({}, False)
        raise SystemExit("no rock was moved by %s" % fid)
    print("range_rocks_on_ground: %s undone; %d rocks put back" % (fid, len(moved)))
    if dry:
        return done(moved, False)
    for ob in obs:
        if ob.name not in moved:
            continue
        ob.location.z += moved[ob.name]
        if key in ob:
            del ob[key]
        else:
            del ob["kyt_ground_moved_m"]
            del ob["kyt_ground_moved_by"]
    readme("%s: range_rocks_on_ground for %s undone; %d rocks put back." % (datetime.date.today().isoformat(), fid, len(moved)))
    save()
    done(moved, True)


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    dry = "--dry" in a
    fid = opt(a, "--id") or opt(a, "--edit")
    if not fid:
        raise SystemExit("name the follow: --id <id>")
    if "--undo" in a:
        return undo(fid, dry, "--missing-ok" in a)
    key = "kyt_ground_moved_%s" % fid
    obs = rocks()
    if any(key in ob for ob in obs):
        raise SystemExit("rocks already moved by %s; --undo it first" % fid)
    per = vertices(obs)
    feet = np.array([v[int(np.argmin(v[:, 2]))] for v in per])
    moves, uneven, how = {}, {}, ""
    if "--delta" in a:
        change = gf.Change.load(opt(a, "--delta"))
        flat = np.concatenate(per)
        d_all = change.at(flat[:, 0], flat[:, 1])
        d_feet = change.at(feet[:, 0], feet[:, 1])
        start = 0
        for ob, v, d in zip(obs, per, d_feet):
            dv = d_all[start:start + len(v)]
            start += len(v)
            if not np.any(dv) and d == 0.0:
                continue
            if dv.max() - dv.min() > UNEVEN:
                uneven[ob.name] = round(float(dv.max() - dv.min()), 3)
            if abs(d) > MIN_MOVE:
                moves[ob.name] = float(d)
        how = "with the ground's change under its foot (the height grid; tools/ground_follow.py)"
    elif "--keep-feet" in a:
        census = json.load(open(opt(a, "--keep-feet")))
        recorded = {i["name"]: i.get("foot") for i in census["kinds"]["range_rocks"]["items"]}
        names = opt(a, "--names", "").split(",")
        heights = gf.Heights(opt(a, "--heights", gf.HEIGHT))
        by = {ob.name: k for k, ob in enumerate(obs)}
        for name in names:
            if name not in by or recorded.get(name) is None:
                raise SystemExit("%s: no such rock, or no foot recorded for it" % name)
            f = feet[by[name]]
            g = float(heights.at([f[0]], [f[1]])[0])
            if np.isnan(g):
                print("  %s: no ground of the grid under its foot; left" % name)
                continue
            d = recorded[name] - (f[2] - g)
            print("  %-48s foot %+.3f on the grid, %+.3f recorded" % (name, f[2] - g, recorded[name]))
            if abs(d) > MIN_MOVE:
                moves[name] = d
        how = "so its foot sits on the height grid as deep as %s recorded" % os.path.basename(opt(a, "--keep-feet"))
    else:
        raise SystemExit("say how: --delta <change.npz> or --keep-feet <census.json> --names ...")
    ups = [d for d in moves.values() if d > 0]
    downs = [d for d in moves.values() if d < 0]
    print("range_rocks_on_ground: %s moves %d rocks: %d up, by up to %.2f m; %d down, by up to %.2f m" % (
        fid, len(moves), len(ups), max(ups, default=0.0), len(downs), -min(downs, default=0.0)))
    for name, d in sorted(moves.items()):
        print("  %-48s %+7.3f m" % (name, d))
    for name, s in sorted(uneven.items(), key=lambda i: -i[1]):
        print("  uneven: the ground's change under %s spans %.2f m" % (name, s))
    if dry or not moves:
        print("range_rocks_on_ground: %s" % ("--dry; nothing saved" if dry else "nothing moved; nothing saved"))
        return done(moves, False, uneven=uneven)
    for name, d in moves.items():
        ob = bpy.data.objects[name]
        if ob.parent is not None:
            raise SystemExit("%s has a parent; its move would not be straight up" % name)
        ob.location.z += d
        ob[key] = d
    readme("%s: range_rocks_on_ground (tools/blender/range_rocks_on_ground.py) %s: %d rocks moved %s (%d up, by up "
           "to %.2f m; %d down, by up to %.2f m); nothing moved in plan. Undo: -- --id %s --undo." % (
               datetime.date.today().isoformat(), fid, len(moves), how, len(ups), max(ups, default=0.0), len(downs),
               -min(downs, default=0.0), fid))
    save()
    done(moves, True, uneven=uneven)


main()
