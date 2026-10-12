"""The relocated city's blocks and towers set on the ground (2026-10-11, Christina: "model it on san
francisco loosly"). The world terrain master's city cut (`world_terrain_ground_edit.py -- --edit
city_cut`) left the foothills climbing through the city's southern rows at street grades, and every
block there, built with its base at 0 m on the flat peninsula, stood in the slope. Each block and
tower now stands on the lowest ground under it, so its downhill side meets the street and its uphill
side runs into the slope, as a building on a San Francisco hill does; a tower's glass moves with it.
Only raised, never lowered; nothing moves in plan.

    Blender --background assets/source/far_shore_city_relocation.blend --python
        tools/blender/city_blocks_on_ground.py -- [--dry] [--undo]

The ground is the world terrain master's `Ground`, linked for the read and let go before the save.
Each object moved keeps how far as `kyt_raised_m`; `--undo` takes them back down. Logged in the
file's README text. Re-export with `tools/export_world_source.sh` afterwards.
"""
import datetime
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "source", "world_terrain_master.blend"))
GROUND = "Ground"
BLOCKS = ("city_block_", "city_skyline_anchor_")
GLASS = "city_skyline_glass_"
# The footprint is sampled on this spacing, its edges included.
SAMPLE = 2.0
# Less than this is left where it is.
MIN_RAISE = 0.05


def ground_tree():
    libs = set(bpy.data.libraries)
    with bpy.data.libraries.load(MASTER, link=True) as (src, dst):
        dst.collections = [GROUND]
    coll = dst.collections[0]
    vs, ps = [], []

    def world(ob):
        # Linked objects no scene evaluates keep an identity matrix_world: composed here.
        if ob.parent is None:
            return ob.matrix_basis
        return world(ob.parent) @ ob.matrix_parent_inverse @ ob.matrix_basis

    for ob in coll.all_objects:
        if ob.type != 'MESH' or ob.get("kyt_collision") == "none":
            continue
        m = world(ob)
        base = len(vs)
        vs.extend(m @ v.co for v in ob.data.vertices)
        ps.extend(tuple(base + i for i in p.vertices) for p in ob.data.polygons)
    for lib in set(bpy.data.libraries) - libs:
        bpy.data.libraries.remove(lib)
    if set(bpy.data.libraries) != libs:
        raise SystemExit("the world terrain master is still linked")
    return BVHTree.FromPolygons(vs, ps)


def footprint_ground(tree, ob):
    """The lowest and highest ground under the object's bottom face, and its base."""
    co = [ob.matrix_world @ v.co for v in ob.data.vertices]
    base = min(c.z for c in co)
    bottom = sorted(co, key=lambda c: c.z)[:4]
    # The bottom's corners in order round it, for a bilinear sweep over the face.
    centre = sum((c for c in bottom), Vector()) / 4.0
    bottom.sort(key=lambda c: math.atan2(c.y - centre.y, c.x - centre.x))
    a, b, c, d = bottom
    nu = max(1, int(math.ceil((b - a).length / SAMPLE)))
    nv = max(1, int(math.ceil((d - a).length / SAMPLE)))
    lo, hi = math.inf, -math.inf
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = i / nu, j / nv
            p = a.lerp(b, u).lerp(d.lerp(c, u), v)
            h = tree.ray_cast(Vector((p.x, p.y, 5000.0)), Vector((0.0, 0.0, -1.0)))
            if h[0] is None:
                continue
            lo = min(lo, h[0].z)
            hi = max(hi, h[0].z)
    return base, lo, hi


def readme(line):
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n" + line + "\n")


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    dry, back = "--dry" in a, "--undo" in a
    if back:
        moved = [ob for ob in bpy.data.objects if "kyt_raised_m" in ob]
        if not moved:
            raise SystemExit("nothing was raised")
        for ob in moved:
            ob.location.z -= ob["kyt_raised_m"]
            del ob["kyt_raised_m"]
        readme("%s: city_blocks_on_ground undone; %d objects taken back down." % (datetime.date.today().isoformat(), len(moved)))
        print("city_blocks_on_ground: %d objects taken back down" % len(moved))
    else:
        if any("kyt_raised_m" in ob for ob in bpy.data.objects):
            raise SystemExit("blocks are already raised; --undo first")
        tree = ground_tree()
        raised = {}
        steep = {}
        for ob in sorted(bpy.data.objects, key=lambda o: o.name):
            if ob.type != 'MESH' or not ob.name.startswith(BLOCKS):
                continue
            base, lo, hi = footprint_ground(tree, ob)
            if lo == float("inf"):
                continue
            if lo - base > MIN_RAISE:
                raised[ob.name] = lo - base
                steep[ob.name] = hi - lo
        for name, dz in list(raised.items()):
            if name.startswith("city_skyline_anchor_"):
                glass = bpy.data.objects.get(GLASS + name[len("city_skyline_anchor_"):])
                if glass is not None:
                    raised[glass.name] = dz
        for name, dz in sorted(raised.items()):
            print("  %-26s raised %5.1f m%s" % (name, dz, ("; the slope under it climbs %.1f m" % steep[name]) if name in steep else ""))
        print("city_blocks_on_ground: %d objects raised, up to %.1f m; the most a footprint's ground climbs is %.1f m" % (
            len(raised), max(raised.values(), default=0.0), max(steep.values(), default=0.0)))
        if dry:
            print("city_blocks_on_ground: --dry; nothing saved")
            return
        for name, dz in raised.items():
            ob = bpy.data.objects[name]
            ob.location.z += dz
            ob["kyt_raised_m"] = dz
        readme("%s: city_blocks_on_ground (tools/blender/city_blocks_on_ground.py): %d blocks, towers and tower glass "
               "raised onto the lowest ground under them (the world terrain master's Ground, after its city cut), up to "
               "%.1f m; never lowered, nothing moved in plan. Undo: -- --undo." % (
                   datetime.date.today().isoformat(), len(raised), max(raised.values(), default=0.0)))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()


main()
