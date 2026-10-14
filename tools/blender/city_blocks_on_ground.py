"""The relocated city's blocks and towers stand on the ground (2026-10-11, Christina: "model it on
san francisco loosly"; on the height grid since 2026-10-14, height-grid plan Stage 3). The world
terrain master's city cut (`world_terrain_ground_edit.py -- --edit city_cut`) left the foothills
climbing through the city's southern rows at street grades, and every block there, built with its
base at 0 m on the flat peninsula, stood in the slope. Each block and tower stands on the lowest
ground under it, so its downhill side meets the street and its uphill side runs into the slope, as
a building on a San Francisco hill does; a tower's glass moves with it. Only raised, never lowered
(where the ground falls away under one, as at the peninsula's north edge, its street holds it);
nothing moves in plan.

    Blender --background --factory-startup assets/source/far_shore_city_relocation.blend --python
        tools/blender/city_blocks_on_ground.py -- --id <id> --delta <change.npz> [--heights <dir>] [--dry]
    ... -- --id <id> --keep-feet <census.json> --names <block,...> [--heights <dir>] [--dry]
    ... -- --id <id> --undo [--dry] [--missing-ok]
    ... -- --undo        (the city cut's raise, 2026-10-11, kept as kyt_raised_m)

The ground is the height grid's bilinear surface (`--heights`, default
`assets/source/world_ground/height/`), swept at `SAMPLE` over each footprint, edges included.
What stands: every `city_block_*`, `city_skyline_anchor_*` and the ferry terminal.
`tools/ground_follow.py` runs this with `--delta`, the grid's change node by node (after less
before): where the lowest ground under a footprint rises, the object rises with it, and a block its
street holds above the ground (the peninsula's north edge) rises only once the ground reaches its
base: raised by max(0, min(L1 - L0, L1 - base)), L0 and L1 the lowest ground under it before and
after. Where the ground falls under one it stays, and the result names it. Measured as a change,
not as a height, so a block keeps how it met the ground it stood on, whatever the grid's 2 m
lattice makes of the creases under it.

`--keep-feet` raises each named block until it stands as deep in the grid's ground as a floater
census recorded (base less the lowest ground): Stage 2's buried block 34, recorded on the master's
ground at `1926e71`, was seated so (id `stage2`). Never lowered.

Each object raised keeps how far as `kyt_ground_raised_<id>`; `--undo` takes back that id's raise,
in any order. Logged in the file's README text, saved only when something moved, and the last line
printed is `FOLLOW_RESULT {json}`. Re-export with `tools/export_world_source.sh` afterwards
(ground_follow does).
"""
import datetime
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import ground_follow as gf  # noqa: E402  (the grid's reader)

BLOCKS = ("city_block_", "city_skyline_anchor_", "city_ferry_terminal")
GLASS = "city_skyline_glass_"
# The footprint is sampled on this spacing, its edges included.
SAMPLE = 2.0
# Less than this is left where it is.
MIN_RAISE = 0.05


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def footprint(ob):
    """The object's base and the Godot (x, z) of its bottom face's samples."""
    co = [ob.matrix_world @ v.co for v in ob.data.vertices]
    base = min(c.z for c in co)
    bottom = sorted(co, key=lambda c: c.z)[:4]
    # The bottom's corners in order round it, for a bilinear sweep over the face.
    centre = sum((c for c in bottom), Vector()) / 4.0
    bottom.sort(key=lambda c: math.atan2(c.y - centre.y, c.x - centre.x))
    a, b, c, d = bottom
    nu = max(1, int(math.ceil((b - a).length / SAMPLE)))
    nv = max(1, int(math.ceil((d - a).length / SAMPLE)))
    pts = []
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = i / nu, j / nv
            p = a.lerp(b, u).lerp(d.lerp(c, u), v)
            pts.append((p.x, -p.y))
    return base, np.array(pts)


def readme(line):
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n" + line + "\n")


def done(moved, saved, **extra):
    print("FOLLOW_RESULT " + json.dumps({"moved": {k: round(v, 3) for k, v in moved.items()}, "saved": saved, **extra}))


def save():
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()


def undo(fid, dry, missing_ok):
    key = "kyt_ground_raised_%s" % fid if fid else "kyt_raised_m"
    moved = {ob.name: -ob[key] for ob in bpy.data.objects if key in ob}
    if not moved:
        if missing_ok:
            print("city_blocks_on_ground: nothing was raised by %s" % (fid or "the city cut"))
            return done({}, False)
        raise SystemExit("nothing was raised by %s" % (fid or "the city cut"))
    print("city_blocks_on_ground: %s undone; %d objects taken back down" % (fid or "the city cut", len(moved)))
    if dry:
        return done(moved, False)
    for name, dz in moved.items():
        ob = bpy.data.objects[name]
        ob.location.z += dz
        del ob[key]
    readme("%s: city_blocks_on_ground for %s undone; %d objects taken back down." % (
        datetime.date.today().isoformat(), fid or "the city cut", len(moved)))
    save()
    done(moved, True)


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    dry = "--dry" in a
    fid = opt(a, "--id")
    if "--undo" in a:
        return undo(fid, dry, "--missing-ok" in a)
    if not fid:
        raise SystemExit("name the run: --id <id>")
    key = "kyt_ground_raised_%s" % fid
    if any(key in ob for ob in bpy.data.objects):
        raise SystemExit("already raised by %s; --undo it first" % fid)
    heights = gf.Heights(opt(a, "--heights", gf.HEIGHT))
    raised, steep, left = {}, {}, {}
    followers = [ob for ob in sorted(bpy.data.objects, key=lambda o: o.name)
                 if ob.type == 'MESH' and ob.name.startswith(BLOCKS)]
    if "--delta" in a:
        change = gf.Change.load(opt(a, "--delta"))
        for ob in followers:
            base, pts = footprint(ob)
            d = change.at(pts[:, 0], pts[:, 1])
            if not np.any(d):
                continue
            h1 = heights.at(pts[:, 0], pts[:, 1])
            if np.all(np.isnan(h1)):
                continue
            lo0, lo1 = float(np.nanmin(h1 - d)), float(np.nanmin(h1))
            up = min(lo1 - lo0, lo1 - base)
            if up > MIN_RAISE:
                raised[ob.name] = up
                steep[ob.name] = float(np.nanmax(h1)) - lo1
            elif lo1 - lo0 < -MIN_RAISE:
                left[ob.name] = round(lo0 - lo1, 3)
        how = "with the lowest ground under them (the height grid's change; tools/ground_follow.py)"
    elif "--keep-feet" in a:
        census = json.load(open(opt(a, "--keep-feet")))
        recorded = {i["name"]: i.get("foot") for i in census["kinds"]["city_blocks"]["items"]}
        by = {ob.name: ob for ob in followers}
        for name in opt(a, "--names", "").split(","):
            if name not in by or recorded.get(name) is None:
                raise SystemExit("%s: no such block, or no foot recorded for it" % name)
            base, pts = footprint(by[name])
            h1 = heights.at(pts[:, 0], pts[:, 1])
            if np.all(np.isnan(h1)):
                print("  %s: no ground of the grid under it; left" % name)
                continue
            lo1 = float(np.nanmin(h1))
            up = lo1 + recorded[name] - base
            print("  %-26s foot %+.3f on the grid, %+.3f recorded" % (name, base - lo1, recorded[name]))
            if up > MIN_RAISE:
                raised[name] = up
                steep[name] = float(np.nanmax(h1)) - lo1
            elif up < -MIN_RAISE:
                left[name] = round(-up, 3)
        how = "until each stands as deep in the height grid as %s recorded" % os.path.basename(opt(a, "--keep-feet"))
    else:
        raise SystemExit("say how: --delta <change.npz> or --keep-feet <census.json> --names ...")
    for name, dz in list(raised.items()):
        if name.startswith("city_skyline_anchor_"):
            glass = bpy.data.objects.get(GLASS + name[len("city_skyline_anchor_"):])
            if glass is not None:
                raised[glass.name] = dz
    for name, dz in sorted(raised.items()):
        print("  %-26s raised %6.2f m%s" % (name, dz, ("; the slope under it climbs %.1f m" % steep[name]) if name in steep else ""))
    for name, fall in sorted(left.items()):
        print("  %-26s left standing: the ground under it fell %.2f m (never lowered)" % (name, fall))
    print("city_blocks_on_ground: %s raises %d objects, up to %.2f m" % (fid, len(raised), max(raised.values(), default=0.0)))
    if dry or not raised:
        print("city_blocks_on_ground: %s" % ("--dry; nothing saved" if dry else "nothing raised; nothing saved"))
        return done(raised, False, left=left)
    for name, dz in raised.items():
        ob = bpy.data.objects[name]
        ob.location.z += dz
        ob[key] = dz
    readme("%s: city_blocks_on_ground (tools/blender/city_blocks_on_ground.py) %s: %d blocks, towers and tower glass "
           "raised %s, up to %.2f m; never lowered, nothing moved in plan. Undo: -- --id %s --undo." % (
               datetime.date.today().isoformat(), fid, len(raised), how, max(raised.values(), default=0.0), fid))
    save()
    done(raised, True, left=left)


main()
