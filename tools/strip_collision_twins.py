"""Remove authored collision-twin objects from a Blender master, once.

    /Applications/Blender.app/Contents/MacOS/Blender --background <master.blend> \
        --python tools/strip_collision_twins.py            # dry run, prints the plan
    /Applications/Blender.app/Contents/MacOS/Blender --background <master.blend> \
        --python tools/strip_collision_twins.py -- --save  # does it and saves

Why this exists. Until 2026-09-15 the range master carried one selectable
`_collision-colonly` object per visible boulder, 7,554 twins beside 7,556
visible meshes. A twin holds no information of its own, it is the visible mesh
again, and it turned every ordinary edit into two edits: move a boulder and its
collision stays behind, duplicate one and the copy has none. Eight boulders
had already drifted from their twins by the time this was written. Collision
is now derived at export by `tools/export_world_source.py` from the
visible objects, so the twins are simply deleted.

Three further things it does so that the visible objects stand on their own:

- A visible object that had no twin is marked `kyt_collision = "none"`, so the
  exporter keeps honouring the intent that it not collide (the canopy masses).
- A boulder whose material is linked to its mesh data is switched to link the
  same material on the object instead. Some 3,800 boulders share one of 179
  mesh forms, and with data-linked materials recolouring one recoloured every
  boulder of that form. The appearance does not change; the material slot
  simply becomes the object's.
- Custom properties that described the twin contract are dropped or reworded.

Checkpoint the master before running with `--save`; this script does not.
"""

import re
import sys

import bpy

TWIN_SUFFIX = re.compile(r"-(?:conv)?col(?:only)?(?:\.\d+)?$")
ROCK_WORD = re.compile(r"rock|boulder", re.IGNORECASE)
SAVE = "--" in sys.argv and "--save" in sys.argv[sys.argv.index("--") + 1:]


def is_rock(obj: bpy.types.Object) -> bool:
    if obj.type != "MESH":
        return False
    if any(ROCK_WORD.search(c.name) for c in obj.users_collection):
        return True
    return bool(ROCK_WORD.search(obj.name))


def visible_of(twin_name: str, by_name: dict):
    base = TWIN_SUFFIX.sub("", twin_name)
    for candidate in (base[: -len("_collision")] if base.endswith("_collision") else base, base):
        if candidate in by_name:
            return by_name[candidate]
    return None


def main() -> None:
    by_name = {o.name: o for o in bpy.data.objects}
    twins = [o for o in bpy.data.objects if TWIN_SUFFIX.search(o.name)]
    visible = [o for o in bpy.data.objects if o.type == "MESH" and not TWIN_SUFFIX.search(o.name)]
    had_twin = set()
    unpaired = []
    for t in twins:
        v = visible_of(t.name, by_name)
        if v is None:
            unpaired.append(t.name)
        else:
            had_twin.add(v.name)
    no_collision = [o for o in visible if o.name not in had_twin]
    rocks = [o for o in visible if is_rock(o)]
    relink = [o for o in rocks if any(s.link == "DATA" and s.material for s in o.material_slots)]
    handoff_texts = {}
    for o in visible:
        text = o.get("editor_handoff")
        if text and re.search(r"twin|colonly|collision", str(text), re.IGNORECASE):
            handoff_texts.setdefault(str(text), []).append(o.name)
    scene_props = [k for k in bpy.context.scene.keys() if re.search(r"collision", k, re.IGNORECASE)]

    print("strip_collision_twins", "(saving)" if SAVE else "(dry run)")
    print(f"  file          {bpy.data.filepath}")
    print(f"  twins         {len(twins)} to delete, {len(unpaired)} without a visible partner")
    for name in unpaired[:10]:
        print(f"    unpaired: {name}")
    print(f"  visible       {len(visible)} kept, {len(no_collision)} marked kyt_collision=none: "
          + ", ".join(o.name for o in no_collision))
    print(f"  rocks         {len(rocks)}, {len(relink)} with data-linked materials to move onto the object")
    for text, names in handoff_texts.items():
        print(f"  editor_handoff on {len(names)} visible objects mentions the twin contract:\n    {text!r}")
    print(f"  scene props   {scene_props}")

    if not SAVE:
        print("  dry run only; add `-- --save` to apply")
        return

    for o in no_collision:
        o["kyt_collision"] = "none"
    for o in relink:
        for slot in o.material_slots:
            mat = slot.material
            if slot.link == "DATA" and mat:
                slot.link = "OBJECT"
                slot.material = mat
    for o in twins:
        bpy.data.objects.remove(o, do_unlink=True)
    orphans = [m for m in bpy.data.meshes if m.users == 0]
    for m in orphans:
        bpy.data.meshes.remove(m)
    for text, names in handoff_texts.items():
        for name in names:
            by_name[name]["editor_handoff"] = re.sub(
                r"[^.;]*(twin|colonly)[^.;]*[.;]?\s*", "", str(text), flags=re.IGNORECASE).strip() \
                or "Directly editable; collision is derived from this object at export."
    for k in scene_props:
        del bpy.context.scene[k]
    bpy.context.scene["collision_contract"] = (
        "Collision is derived from visible objects by tools/export_world_source.py; "
        "there are no collision objects in this file. kyt_collision=none opts an object out.")
    bpy.ops.wm.save_mainfile()
    print(f"  saved         {bpy.data.filepath}: {len(twins)} twins removed, {len(orphans)} orphan meshes removed, "
          f"{len(relink)} rocks relinked, {len(bpy.data.objects)} objects remain")


main()
