"""Start a new prop file from the project's prop template.

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
        --python tools/blender/new_prop.py -- <name>

Writes `assets/source/props/<name>.blend` and refuses to overwrite one that
exists. The file is the template every prop starts from:

- metric units at real scale, one Blender unit a metre, Z up;
- a `reference` collection, locked against selection and never exported, for
  the greybox, the neighbouring floor and dimension markers that the
  maquette exporter (tool 2) puts there;
- an `authored` collection for work in progress, also never exported;
- an `export` collection, which is exactly what Send to game sends;
- the prop sits on z = 0 at the origin, which is where the game places it.
"""

import os
import re
import sys

import bpy

NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or not NAME.match(argv[0]):
        raise SystemExit("new_prop: give one snake_case name, e.g. -- plaza_bench")
    name = argv[0]
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    out = os.path.join(root, "assets", "source", "props", f"{name}.blend")
    if os.path.exists(out):
        raise SystemExit(f"new_prop: {out} already exists; not overwriting it")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = name
    units = scene.unit_settings
    units.system = "METRIC"
    units.scale_length = 1.0
    units.length_unit = "METERS"

    for coll_name in ("reference", "authored", "export"):
        coll = bpy.data.collections.new(coll_name)
        scene.collection.children.link(coll)
    bpy.data.collections["reference"].hide_select = True
    bpy.data.collections["reference"].hide_render = True
    bpy.data.collections["authored"].hide_render = True

    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print(f"new_prop: wrote {out}")


main()
