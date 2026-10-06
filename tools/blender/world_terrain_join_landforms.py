"""The range's and city's landforms join the world terrain master's `Ground` (2026-10-06, the
"After" list of documentation/terrain-master-into-game-plan-2026-10-05.md; Christina approved
the master as the game's one ground, these landforms included, on 2026-10-05).

    Blender --background assets/source/world_terrain_master.blend --python \
        tools/blender/world_terrain_join_landforms.py -- --join
    Blender --background assets/source/range_forest_distinct_background.blend --python \
        tools/blender/world_terrain_join_landforms.py -- --strip
    Blender --background assets/source/far_shore_city_relocation.blend --python \
        tools/blender/world_terrain_join_landforms.py -- --strip
    Blender --background assets/source/world_terrain_master.blend --python \
        tools/blender/world_terrain_join_landforms.py -- --right-side-out

Lossless first, as Stage 0 was: `--join` appends `LANDFORMS` from their sources into the
master's `Ground` exactly as they are (every vertex, face, material and property, checked), and
`--strip` then deletes them from the source they came from, which keeps everything else: the
range's forest, canopy and rocks, the city's buildings, roads, earthworks, bridge and ferry
landings. Run `--join` first; `--strip` refuses while the master lacks any of them. Nothing in
the game moves: the same meshes are drawn and collide, from the master's GLB instead of
their own. Turning the inside-out shells right side out and dropping their buried parts
comes after, in the master.

`--right-side-out` (on the master, after the join) turns the joined landforms that came in
inside out the right way: a closed shell whose top, the faces with nothing of the shell above
them, mostly faces down has every face reversed. Twelve did, the southeast connector and
ridges, the southern connection lowland and ridges and the city's foothills, whose bottoms at
-11 faced up: that is the "-11 m plate" anything reading ground by its facing found. Nothing
moves and nothing looks different (their materials draw both sides); a shell already right
side out, or one with open edges, is left alone.

Undo is git: the three .blend files as committed before the join.
"""
import os
import re
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
GROUND = "Ground"
MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
# The landform meshes of each source: everything in them that is ground. What is not ground
# (forest, canopy, rocks, buildings, roads and their earthworks, the bridge, the ferry
# landings) stays in its source.
LANDFORMS = {
    os.path.join(ROOT, "assets", "source", "range_forest_distinct_background.blend"): [
        "background_distant_range_middle",
        "background_distant_range_north",
        "background_distant_range_north_inland_saddle",
        "background_distant_range_north_west_companion",
        "background_distant_range_south",
        "background_distant_range_southeast_connector",
        "north_plug_s_curve_sand_infill",
        "north_shore_volcanic_plug",
        "southeast_range_ridge_1",
        "southeast_range_ridge_2",
        "southeast_range_ridge_3",
        "southeast_range_ridge_4",
        "southern_range_connection_lowland",
        "southern_range_connection_ridge_0",
        "southern_range_connection_ridge_1",
        "southern_range_connection_ridge_2",
        "southern_range_connection_ridge_3",
        "southern_range_connection_ridge_4",
    ],
    os.path.join(ROOT, "assets", "source", "far_shore_city_relocation.blend"): [
        "relocated_city_peninsula",
        "relocated_city_peninsula_beaches",
        "southern_city_range_foothills",
        "southern_city_range_beaches",
    ],
}


def fingerprint(ob):
    """Everything about a mesh object the game sees: world positions, faces, materials per
    face, smooth flags, sharp edges and the object's own properties."""
    me = ob.data
    M = ob.matrix_world
    verts = tuple(tuple(round(c, 6) for c in (M @ v.co)) for v in me.vertices)
    faces = tuple((tuple(p.vertices), p.material_index, p.use_smooth) for p in me.polygons)
    # A second copy of a file's objects comes in with its materials renamed `.001`.
    mats = tuple(re.sub(r"\.\d{3}$", "", m.name) if m else None for m in me.materials)
    colours = tuple(tuple(round(c, 6) for c in m.diffuse_color) if m else None for m in me.materials)
    sharp = tuple(sorted(e.index for e in me.edges if e.use_edge_sharp))
    props = tuple(sorted((k, str(ob[k])) for k in ob.keys() if not k.startswith("_")))
    return (verts, faces, mats, colours, sharp, props)


def join():
    if "kyt_landforms_joined" in bpy.context.scene:
        raise SystemExit("the master already holds the joined landforms")
    ground = bpy.data.collections[GROUND]
    report = []
    for path, names in LANDFORMS.items():
        clash = [n for n in names if n in bpy.data.objects]
        if clash:
            raise SystemExit("the master already has %s" % clash)
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            missing = [n for n in names if n not in src.objects]
            if missing:
                raise SystemExit("%s has no %s" % (os.path.basename(path), missing))
            source_materials = set(src.materials)
            dst.objects = list(names)
        for ob in dst.objects:
            if ob.name not in names:
                raise SystemExit("%s came in renamed as %s" % (names, ob.name))
            for m in ob.data.materials:
                if m is not None and m.name not in source_materials:
                    raise SystemExit("%s's material came in renamed as %s, clashing with one in the master" % (ob.name, m.name))
            ground.objects.link(ob)
            report.append((ob.name, len(ob.data.polygons)))
    # Each joined object exactly as it is in its source: a second copy, which comes in renamed
    # (`.001`), compared and dropped.
    for path, names in LANDFORMS.items():
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = list(names)
        for ob in dst.objects:
            name = ob.name.rsplit(".", 1)[0]
            if fingerprint(ob) != fingerprint(bpy.data.objects[name]):
                raise SystemExit("%s differs from its source after the join" % name)
            me = ob.data
            bpy.data.objects.remove(ob)
            if me.users == 0:
                bpy.data.meshes.remove(me)
    bpy.context.scene["kyt_landforms_joined"] = "2026-10-06: %s from the range and city sources, unchanged" % len(report)
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\nLandforms joined 2026-10-06 (tools/blender/world_terrain_join_landforms.py): %s, appended into Ground "
            "exactly as they stood in range_forest_distinct_background.blend and far_shore_city_relocation.blend, "
            "and deleted there. Right side out and their buried parts dropped come after.\n" % ", ".join(n for n, _ in report))
    for name, faces in report:
        print("  joined %-46s %6d faces" % (name, faces))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    print("world_terrain_join_landforms: %d landforms joined into Ground, each identical to its source" % len(report))


def strip(master):
    path = os.path.abspath(bpy.data.filepath)
    names = next((n for p, n in LANDFORMS.items() if os.path.basename(p) == os.path.basename(path)), None)
    if names is None:
        raise SystemExit("%s is not a source of joined landforms" % path)
    # The master must hold every one of them, identical, before the source lets go.
    with bpy.data.libraries.load(master, link=False) as (src, dst):
        missing = [n for n in names if n not in src.objects]
        if missing:
            raise SystemExit("the master lacks %s; run --join on it first" % missing)
        dst.objects = list(names)
    for ob in dst.objects:
        name = ob.name.rsplit(".", 1)[0] if ob.name not in names else ob.name
        here = bpy.data.objects[name] if name in bpy.data.objects and bpy.data.objects[name] is not ob else None
        if here is None:
            raise SystemExit("%s is not in this source" % name)
        if fingerprint(ob) != fingerprint(here):
            raise SystemExit("%s in the master differs from this source; not stripping" % name)
        me = ob.data
        bpy.data.objects.remove(ob)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    keep = {ob.name: fingerprint(ob) for ob in bpy.data.objects if ob.type == 'MESH' and ob.name not in names}
    for name in names:
        ob = bpy.data.objects[name]
        me = ob.data
        bpy.data.objects.remove(ob)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for name, fp in keep.items():
        if fingerprint(bpy.data.objects[name]) != fp:
            raise SystemExit("%s changed while stripping" % name)
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n2026-10-06: the landforms %s moved to assets/source/world_terrain_master.blend's Ground "
            "(tools/blender/world_terrain_join_landforms.py); this source keeps everything that is not ground.\n" % ", ".join(names))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    print("world_terrain_join_landforms: %d landforms removed from %s; %d other meshes unchanged" % (
        len(names), os.path.basename(path), len(keep)))


def facing(bm):
    """How many of a shell's top faces (nothing of the shell above their centre) face up and
    down."""
    tree = BVHTree.FromBMesh(bm)
    up = down = 0
    for f in bm.faces:
        c = f.calc_center_median()
        if tree.ray_cast(c + Vector((0.0, 0.0, 0.01)), Vector((0.0, 0.0, 1.0)))[0] is None:
            if f.normal.z > 0.0:
                up += 1
            else:
                down += 1
    return up, down


def right_side_out():
    if "kyt_landforms_joined" not in bpy.context.scene:
        raise SystemExit("the landforms have not joined this master")
    flipped = []
    for names in LANDFORMS.values():
        for name in names:
            ob = bpy.data.objects[name]
            me = ob.data
            before = [v.co.copy() for v in me.vertices]
            bm = bmesh.new()
            bm.from_mesh(me)
            if any(e.is_boundary for e in bm.edges):
                bm.free()
                continue
            up, down = facing(bm)
            if down <= up:
                bm.free()
                continue
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            bm.normal_update()
            up2, down2 = facing(bm)
            if down2 >= up2:
                raise SystemExit("%s: still %d of its top faces face down after reversing" % (name, down2))
            bm.to_mesh(me)
            bm.free()
            me.update()
            if [v.co for v in me.vertices] != before:
                raise SystemExit("%s moved while reversing" % name)
            flipped.append("%s (%d of %d top faces were facing down)" % (name, down, up + down))
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n2026-10-06: joined landforms turned right side out (world_terrain_join_landforms.py --right-side-out): %s.\n"
            % "; ".join(flipped))
    bpy.context.scene["kyt_landforms_joined"] = str(bpy.context.scene["kyt_landforms_joined"]) + "; %d right side out" % len(flipped)
    for f in flipped:
        print("  reversed " + f)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    print("world_terrain_join_landforms: %d joined landforms turned right side out" % len(flipped))


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--join" in a:
        join()
    elif "--right-side-out" in a:
        right_side_out()
    elif "--strip" in a:
        # `--master <path>` checks against another copy of the master (a scratch run).
        strip(a[a.index("--master") + 1] if "--master" in a else MASTER)
    else:
        raise SystemExit("--join (on the master) or --strip (on a source)")


main()
