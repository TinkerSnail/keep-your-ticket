"""Put a maquette reference into a prop file's locked `reference` collection.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<name>.blend --python tools/blender/add_reference.py -- \
        assets/source/props/reference/<name>.glb

The GLB comes from `tools/maquette_export.gd`: the greybox prop in its own frame
(on the ground, at the origin, facing -Y here), any contract markers such as a
bench's `seat_l` and `seat_r`, the existing version beside it and a floor plane.
Everything it brings in goes into `reference`, which the template locks
against selection and never exports. A previous reference import is replaced,
so running this again refreshes it rather than stacking a second copy.

The markers keep their names, because the Check button looks for `seat_l` and
`seat_r` by name; they are drawn as small arrows so they read as points to fit
to rather than as parts of the model.

This saves the prop file, so it is for files an agent has prepared, never for
one Christina has open.
"""

import os
import sys

import bpy

TAG = "kyt_reference_import"
MARKER_NAMES = ("seat_l", "seat_r", "trunk_top")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        raise SystemExit("add_reference: give the reference GLB path after --")
    glb = os.path.abspath(argv[0])
    reference = bpy.data.collections.get("reference")
    if reference is None:
        raise SystemExit("add_reference: this file has no 'reference' collection; start it with new_prop.py")

    for obj in [o for o in bpy.data.objects if o.get(TAG)]:
        bpy.data.objects.remove(obj, do_unlink=True)

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    imported = [o for o in bpy.data.objects if o not in before]

    for obj in imported:
        for coll in list(obj.users_collection):
            coll.objects.unlink(obj)
        reference.objects.link(obj)
        obj[TAG] = True
        # The glTF root carries the prop's name; the markers and parts sit under it.
        base = obj.name.split(".")[0]
        if base in MARKER_NAMES and obj.type == "EMPTY":
            obj.name = base
            obj.empty_display_type = "SINGLE_ARROW"
            obj.empty_display_size = 0.25

    missing = [n for n in MARKER_NAMES[:2] if n not in bpy.data.objects]
    bpy.ops.wm.save_mainfile()
    print(f"add_reference: {len(imported)} objects from {os.path.basename(glb)} into 'reference'")
    if missing:
        print(f"add_reference: no {', '.join(missing)} in this reference (fine for props without seats)")
    if "trunk_top" in bpy.data.objects:
        print("add_reference: trunk_top at the origin: this prop hangs from it")


main()
