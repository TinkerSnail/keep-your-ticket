"""The Check button: what a prop must satisfy before it goes to the game.

Every finding is a sentence Christina can act on without reading code. An
"error" stops Send to game; a "warning" does not; a "note" is a measurement
(the UVs' texel density, from `uv_check.py`). The ceilings come from
`tools/budget_test.gd`, which holds any scene placed three or more times to
`PLACEMENT_TRIANGLES` and `PLACEMENT_SURFACES`; raising them is her decision,
so they are copied here rather than loosened here.

Axes. Godot's +Z is Blender's -Y after the glTF export (Y-up), so a prop that
faces +Z in Godot, as the plaza bench does, faces -Y here and its back lies
toward +Y.
"""

import os

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import uv_check

LEVELS = ("ERROR", "WARNING", "NOTE")
PLACEMENT_TRIANGLES = 50_000
PLACEMENT_SURFACES = 60
GROUND_TOLERANCE_M = 0.005
CENTRE_TOLERANCE_M = 0.5
SEAT_TOLERANCE_M = 0.015
SEAT_MARKERS = ("seat_l", "seat_r")
# A prop placed by the point it hangs from, not the ground it stands on: a palm
# crown sits on its trunk's top, and its fronds droop below it. A small plant
# is placed by `plant_base`, the soil line its leaves spring from, which they
# may start a little above (the fern fan's fronds begin 2.5 cm up). A prop set
# into the ground is placed by `ground_line`, the ground it stands in, which it
# goes below on purpose (the hardscape kit's walls, curbs and fence posts, so
# uneven ground never shows a gap under them). A boat (or a swimming animal) is
# placed by `waterline`, the water's surface it floats at, and goes below it by
# its draft.
MOUNT_MARKERS = ("trunk_top", "plant_base", "ground_line", "waterline")
EXPORT_COLLECTION = "export"
REFERENCE_COLLECTION = "reference"


def project_root(blend_path: str):
    """The folder holding project.godot above this file, or None."""
    folder = os.path.dirname(os.path.abspath(blend_path))
    while True:
        if os.path.isfile(os.path.join(folder, "project.godot")):
            return folder
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        folder = parent


def export_objects(scene):
    """Every object the game will get: the export collection and its children."""
    coll = bpy.data.collections.get(EXPORT_COLLECTION)
    if coll is None:
        return []
    return [o for o in coll.all_objects if o.type == "MESH" and not o.hide_render]


def library_names(root):
    """Material names the Godot library defines, or None before it exists.

    The library is its own folder: `assets/materials/` itself also holds the
    generator's lit materials (bulbs, windows), which are not for props."""
    folder = os.path.join(root, "assets", "materials", "library") if root else None
    if not folder or not os.path.isdir(folder):
        return None
    return {os.path.splitext(f)[0] for f in os.listdir(folder) if f.endswith(".tres")}


def _world_bvh(objects, depsgraph):
    """One BVH over the evaluated meshes, in world space, for seat rays."""
    verts, polys = [], []
    for obj in objects:
        ev = obj.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        try:
            base = len(verts)
            m = obj.matrix_world
            verts.extend(m @ v.co for v in mesh.vertices)
            polys.extend([base + i for i in p.vertices] for p in mesh.polygons)
        finally:
            ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys) if polys else None, verts


def run(context):
    """Return a list of (level, sentence) findings, errors first."""
    found = []

    def error(text):
        found.append(("ERROR", text))

    def warn(text):
        found.append(("WARNING", text))

    path = bpy.data.filepath
    if not path:
        error("Save the file first: it has to live in assets/source/props/ in the project.")
        return found
    root = project_root(path)
    if root is None:
        error("This file is not inside the Keep Your Ticket project folder.")
    elif os.path.normpath(os.path.dirname(path)) != os.path.normpath(
            os.path.join(root, "assets", "source", "props")):
        warn("Props are expected in assets/source/props/; this file is somewhere else.")

    objects = export_objects(context.scene)
    if bpy.data.collections.get(EXPORT_COLLECTION) is None:
        error(f"There is no '{EXPORT_COLLECTION}' collection. Put the finished prop in one with that name.")
        return found
    if not objects:
        error(f"The '{EXPORT_COLLECTION}' collection has no visible mesh in it, so nothing would go to the game.")
        return found

    # Bring world matrices and modifiers up to date before measuring anything.
    context.view_layer.update()
    depsgraph = context.evaluated_depsgraph_get()
    library = library_names(root)
    # A file of variants (`kyt_variant`) sends each as a prop of its own
    # (send.py), and the game shows one at a time, so each is measured on its
    # own: the placement budget, the ground or mount and the centre belong to
    # one placed prop, not to the file. Parts with no variant are one prop.
    stats = {}
    materials = set()

    for obj in objects:
        s = obj.matrix_world.to_scale()
        if any(abs(abs(c) - 1.0) > 1e-4 for c in obj.scale):
            error(f"'{obj.name}' has unapplied scale. Select it and press Ctrl+A, then Scale.")
        if s.x * s.y * s.z < 0:
            error(f"'{obj.name}' is mirrored (negative scale), which turns its faces inside out in the game.")
        if obj.name.endswith(("-col", "-colonly")) or "-col." in obj.name:
            error(f"'{obj.name}' is named like a collision twin. Collision is made for you on export; rename it.")
        if not obj.material_slots or any(slot.material is None for slot in obj.material_slots):
            error(f"'{obj.name}' has a face with no material. Give every slot a material.")
        st = stats.setdefault(str(obj.get("kyt_variant", "")), {
            "triangles": 0, "materials": set(),
            "low": Vector((1e9, 1e9, 1e9)), "high": Vector((-1e9, -1e9, -1e9))})
        for slot in obj.material_slots:
            if slot.material is None:
                continue
            materials.add(slot.material.name)
            st["materials"].add(slot.material.name)

        ev = obj.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        try:
            mesh.calc_loop_triangles()
            st["triangles"] += len(mesh.loop_triangles)
            m = obj.matrix_world
            low, high = st["low"], st["high"]
            for v in mesh.vertices:
                w = m @ v.co
                low = Vector((min(low.x, w.x), min(low.y, w.y), min(low.z, w.z)))
                high = Vector((max(high.x, w.x), max(high.y, w.y), max(high.z, w.z)))
            st["low"], st["high"] = low, high
            if getattr(context.scene, "kyt_stage", "") == "texture" and not mesh.uv_layers:
                error(f"'{obj.name}' has no UVs yet; it needs them at the texture stage.")
        finally:
            ev.to_mesh_clear()

    if library is not None:
        for name in sorted(materials - library):
            warn(f"Material '{name}' is not in the game's material library yet.")

    mount = next((bpy.data.objects[n] for n in MOUNT_MARKERS if n in bpy.data.objects), None)
    named = len(stats) > 1
    if named:
        total = sum(st["triangles"] for st in stats.values())
        found.append(("NOTE", f"{len(stats)} variants, {total:,} triangles and {len(materials)} materials "
                              "in the file; each is checked as the prop it is sent as."))
    # Ground contact stays a property of the set: a variant may rest on another
    # one (the queue rope hangs between its posts, the derby horse rides its
    # lane), so only the file's lowest point must meet the ground.
    floor = min(st["low"].z for st in stats.values())
    off_centre = []
    for variant, st in sorted(stats.items()):
        triangles, used, low, high = st["triangles"], st["materials"], st["low"], st["high"]
        prop = f"Variant '{variant}'" if named else "The prop"
        if triangles > PLACEMENT_TRIANGLES:
            error(f"{prop} has {triangles:,} triangles; a repeated prop may have at most {PLACEMENT_TRIANGLES:,}.")
        if len(used) > PLACEMENT_SURFACES:
            error(f"{prop} uses {len(used)} materials; a repeated prop may have at most {PLACEMENT_SURFACES}.")
        counts = f"{triangles:,} triangles, {len(used)} material{'s' if len(used) != 1 else ''}"
        placed = None
        if mount is not None and mount.name == "plant_base":
            placed = (f"The plant stands on '{mount.name}' at the origin: its leaves "
                      f"start {low.z * 100:.1f} cm above it and reach {high.z:.2f} m.")
        elif mount is not None and mount.name == "ground_line":
            placed = (f"The prop is set into the ground at '{mount.name}': it goes "
                      f"{-low.z * 100:.1f} cm below it and reaches {high.z:.2f} m above.")
        elif mount is not None and mount.name == "waterline":
            placed = (f"It floats at '{mount.name}': its draft is {-low.z + 0.0:.2f} m "
                      f"and it reaches {high.z:.2f} m above the water.")
        elif mount is not None:
            placed = (f"The prop hangs from '{mount.name}' at the origin: it reaches "
                      f"{high.z:.2f} m above it and {-low.z:.2f} m below.")
        elif named and low.z - floor > GROUND_TOLERANCE_M:
            placed = f"It starts {low.z * 100:.1f} cm above the ground, resting on another part of the set."
        if named:
            tail = f" {placed}" if placed else ""
            found.append(("NOTE", f"{prop}: {counts}.{tail}"))
        else:
            found.append(("NOTE", f"{counts}."))
            if placed:
                found.append(("NOTE", placed))
        centre = (low + high) / 2
        if Vector((centre.x, centre.y)).length > CENTRE_TOLERANCE_M:
            off_centre.append((Vector((centre.x, centre.y)).length, variant))
    if mount is None and abs(floor) > GROUND_TOLERANCE_M:
        where = "above" if floor > 0 else "below"
        lowest = "The prop's lowest point" if not named else "The file's lowest point"
        error(f"{lowest} is {abs(floor) * 100:.1f} cm {where} the ground (z = 0). It should sit on it.")
    if off_centre and not named:
        warn(f"The prop is {off_centre[0][0]:.2f} m off the origin. "
             "The game places it by the origin, so keep it centred there.")
    elif off_centre:
        far, worst = max(off_centre)
        names = [v for _, v in sorted(off_centre, key=lambda c: c[1])]
        listed = ", ".join(names[:8]) + (f" and {len(names) - 8} more" if len(names) > 8 else "")
        warn(f"{len(names)} variant{'s are' if len(names) != 1 else ' is'} more than {CENTRE_TOLERANCE_M} m "
             f"off the origin, '{worst}' farthest at {far:.2f} m: {listed}. The game places each by the "
             "origin, so keep it centred there unless it is placed by a point of its own.")

    markers = [bpy.data.objects.get(name) for name in SEAT_MARKERS]
    if all(markers):
        bvh, world_verts = _world_bvh(objects, depsgraph)
        # Anything well above the seat is taken to be the back (or arms); its
        # average depth says which way the bench faces.
        backrest = [v for v in world_verts if v.z > markers[0].matrix_world.translation.z + 0.1]
        for marker in markers:
            target = marker.matrix_world.translation
            hit = bvh.ray_cast(target + Vector((0, 0, 1.0)), Vector((0, 0, -1))) if bvh else (None,)
            if hit[0] is None:
                error(f"Nothing is under the seat marker '{marker.name}'. Someone would sit on air.")
                continue
            gap = hit[0].z - target.z
            if abs(gap) > SEAT_TOLERANCE_M:
                where = "above" if gap > 0 else "below"
                error(f"The seat under '{marker.name}' is {abs(gap) * 100:.1f} cm {where} the seat height "
                      f"({target.z:.2f} m). Seated guests are placed at that height.")
        if backrest:
            mean_y = sum(v.y for v in backrest) / len(backrest)
            if mean_y < markers[0].matrix_world.translation.y:
                error("The backrest is on the wrong side: the prop should face -Y here (it faces +Z in the game).")

    # Once there is a game mesh, its unwrap: overlaps and texel density.
    game = next((o for o in objects if o.get("kyt_game_mesh")), None)
    if game is not None:
        found.extend(uv_check.run(game))

    found.sort(key=lambda f: LEVELS.index(f[0]))
    return found
