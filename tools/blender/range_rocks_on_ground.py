"""The range source's rocks moved with the ground under them (2026-10-12). A ground edit carried onto the
world terrain master's `Ground` (`world_terrain_ground_edit.py`) moves the ground under rocks the range
source places on it; each rock in `ROCKS` moves up or down by as much as the ground under its centre moved,
so it sits on the new ground as it sat on the old. Nothing moves in plan.

    Blender --background assets/source/range_forest_distinct_background.blend --python
        tools/blender/range_rocks_on_ground.py -- --edit <id> [--dry] [--undo] [--master <blend>]

The ground before is `Ground` with the edit's faces swapped back for the faces it replaced, kept in
`Ground_history` as `<object>__before_edit<id>`; both are linked from the master for the read and let go
before the save. Each rock moved keeps how far and by which edit as `kyt_ground_moved_m` and
`kyt_ground_moved_by`; `--undo` puts them back. Logged in the file's README text. Re-export with
`tools/export_world_source.sh` afterwards.
"""
import datetime
import sys
import os

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "source", "world_terrain_master.blend"))
ROCKS = ("range_main_beach_middle_band_rocks", "range_remaining_beach_rocks", "range_beach_rocks", "range_base_boulders")
# Less than this is left where it is.
MIN_MOVE = 0.05


def world(ob):
    # Linked objects no scene evaluates keep an identity matrix_world: composed here.
    if ob.parent is None:
        return ob.matrix_basis
    return world(ob.parent) @ ob.matrix_parent_inverse @ ob.matrix_basis


def grounds(edit, master):
    """BVH trees of the master's Ground as it stands and as it stood before edit `edit`."""
    libs = set(bpy.data.libraries)
    with bpy.data.libraries.load(master, link=True) as (src, dst):
        dst.collections = ["Ground", "Ground_history"]
    ground, history = dst.collections
    trees = {}
    for which in ("after", "before"):
        vs, ps = [], []
        for ob in ground.all_objects:
            if ob.type != 'MESH' or ob.get("kyt_collision") == "none":
                continue
            m = world(ob)
            me = ob.data
            fa = me.attributes.get("authored_edit")
            mine = [False] * len(me.polygons)
            if which == "before" and fa is not None:
                mine = [d.value == edit for d in fa.data]
            base = len(vs)
            vs.extend(m @ v.co for v in me.vertices)
            ps.extend(tuple(base + i for i in p.vertices) for p in me.polygons if not mine[p.index])
            if which == "before" and any(mine):
                hob = history.all_objects.get("%s__before_edit%d" % (ob.name, edit))
                if hob is None:
                    raise SystemExit("the master keeps no faces from before edit %d for %s" % (edit, ob.name))
                hm = world(hob)
                base = len(vs)
                vs.extend(hm @ v.co for v in hob.data.vertices)
                ps.extend(tuple(base + i for i in p.vertices) for p in hob.data.polygons)
        trees[which] = BVHTree.FromPolygons(vs, ps)
    for lib in set(bpy.data.libraries) - libs:
        bpy.data.libraries.remove(lib)
    if set(bpy.data.libraries) != libs:
        raise SystemExit("the world terrain master is still linked")
    return trees


def top(tree, x, y):
    hit = tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
    return None if hit[0] is None else hit[0].z


def readme(line):
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n" + line + "\n")


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    dry, back = "--dry" in a, "--undo" in a
    edit = int(a[a.index("--edit") + 1])
    master = os.path.abspath(a[a.index("--master") + 1]) if "--master" in a else MASTER
    rocks = [ob for name in ROCKS for ob in bpy.data.collections[name].all_objects if ob.type == 'MESH']
    if back:
        moved = [ob for ob in rocks if ob.get("kyt_ground_moved_by") == edit]
        if not moved:
            raise SystemExit("no rock was moved by edit %d" % edit)
        for ob in moved:
            ob.location.z -= ob["kyt_ground_moved_m"]
            del ob["kyt_ground_moved_m"]
            del ob["kyt_ground_moved_by"]
        readme("%s: range_rocks_on_ground for edit %d undone; %d rocks put back." % (datetime.date.today().isoformat(), edit, len(moved)))
        print("range_rocks_on_ground: %d rocks put back" % len(moved))
    else:
        if any("kyt_ground_moved_by" in ob for ob in rocks):
            raise SystemExit("rocks already moved by edit %s; --undo it first" % sorted({ob["kyt_ground_moved_by"] for ob in rocks if "kyt_ground_moved_by" in ob}))
        trees = grounds(edit, master)
        moves = {}
        for ob in rocks:
            co = [ob.matrix_world @ v.co for v in ob.data.vertices]
            c = sum(co, Vector()) / len(co)
            t0, t1 = top(trees["before"], c.x, c.y), top(trees["after"], c.x, c.y)
            if t0 is None or t1 is None or abs(t1 - t0) <= MIN_MOVE:
                continue
            moves[ob.name] = t1 - t0
        ups = [d for d in moves.values() if d > 0]
        downs = [d for d in moves.values() if d < 0]
        print("range_rocks_on_ground: edit %d moves %d rocks: %d up, by up to %.1f m; %d down, by up to %.1f m" % (
            edit, len(moves), len(ups), max(ups, default=0.0), len(downs), -min(downs, default=0.0)))
        for name, d in sorted(moves.items()):
            print("  %-48s %+6.2f m" % (name, d))
        if dry:
            print("range_rocks_on_ground: --dry; nothing saved")
            return
        for name, d in moves.items():
            ob = bpy.data.objects[name]
            if ob.parent is not None:
                raise SystemExit("%s has a parent; its move would not be straight up" % name)
            ob.location.z += d
            ob["kyt_ground_moved_m"] = d
            ob["kyt_ground_moved_by"] = edit
        readme("%s: range_rocks_on_ground (tools/blender/range_rocks_on_ground.py): %d rocks moved with the ground "
               "Ground edit %d moved under them (%d up, by up to %.1f m; %d down, by up to %.1f m), each by the ground's "
               "change under its centre; nothing moved in plan. Undo: -- --edit %d --undo." % (
                   datetime.date.today().isoformat(), len(moves), edit, len(ups), max(ups, default=0.0), len(downs),
                   -min(downs, default=0.0), edit))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()


main()
