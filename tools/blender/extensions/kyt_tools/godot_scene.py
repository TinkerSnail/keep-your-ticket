"""The prop's Godot scene, offered on its first Send to game.

Every prop is placed in the game through `scenes/world/park_furniture/<prop>.tscn`,
an editor-owned scene that wraps `assets/props/<prop>.glb` and holds the
contract markers the crowd and the tests read. `backless_timber_bench.tscn` is
the pattern: a `Node3D` named for the prop, the GLB instanced as `model`, and
for a seat, `seat_l` and `seat_r` as `Marker3D`s.

After a Send, if that scene doesn't wrap the GLB yet, the panel offers to
write it, with the seat markers taken from this file's `seat_l`/`seat_r`
(Blender's x, y, z is Godot's x, z, -y). Nothing is written without the
button, and a scene that already exists is replaced only after the panel has
said what it holds and she has confirmed; its `editor_description` is kept.
Once the scene wraps the GLB it is hers, and this never touches it again.
"""

import os
import re
import subprocess
import time

import bpy

from . import checks

FOLDER = ("scenes", "world", "park_furniture")

_offer = {}  # prop -> the scene's state after its last Send


def scene_path(root, prop):
    return os.path.join(root, *FOLDER, f"{prop}.tscn")


def glb_res(prop):
    return f"res://assets/props/{prop}.glb"


def state(root, prop):
    """'wraps', 'missing' or 'other' (exists and doesn't use the GLB)."""
    path = scene_path(root, prop)
    if not os.path.exists(path):
        return "missing"
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return "wraps" if f'path="{glb_res(prop)}"' in text else "other"


def summary(root, prop):
    """What an existing scene holds, in a few words, for the confirmation."""
    with open(scene_path(root, prop), encoding="utf-8") as f:
        text = f.read()
    kinds = {}
    for kind in re.findall(r'^\[node name="[^"]*" type="(\w+)"', text, flags=re.M):
        kinds[kind] = kinds.get(kind, 0) + 1
    nodes = sum(kinds.values())
    listed = ", ".join(f"{n} {k}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])[:3])
    return f"{nodes} node{'s' if nodes != 1 else ''} ({listed})"


def tracked(root, path):
    try:
        return subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", path],
                              capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def markers():
    """{name: (x, y, z) in Godot} for the seat markers in this file."""
    out = {}
    for name in checks.SEAT_MARKERS:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            x, y, z = obj.matrix_world.translation
            out[name] = (x, z, -y)
    return out


def _num(v):
    text = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def text_for(prop, seats, description):
    """The scene's text; `description` is already quoted."""
    title = prop.replace("_", " ")
    comment = [f"The {title}, as the game places it. Editor-owned: written by the",
               f"Keep Your Ticket panel at its first Send to game ({time.strftime('%Y-%m-%d')});",
               "edit it in Godot from here on."]
    if seats:
        comment += ["", "The two Marker3Ds are the seat contract, the plaza bench's: a seated guest",
                    "sits at a marker's position, facing the bench's +Z. They match `seat_l` and",
                    "`seat_r` in the prop's Blender reference layer, which the Check button",
                    "measures the modelled seat against; move them only together with the model."]
    comment += ["", f"The model is `assets/props/{prop}.glb`, sent from",
                f"`assets/source/props/{prop}.blend` with the Keep Your Ticket",
                "panel. Its collision is derived on export, on layer 1. Not placed",
                "anywhere yet."]
    lines = ["[gd_scene load_steps=2 format=3]", ""] + [f"; {c}".rstrip() for c in comment] + [
        "", f'[ext_resource type="PackedScene" path="{glb_res(prop)}" id="1_model"]', "",
        f'[node name="{prop}" type="Node3D"]', f"editor_description = {description}", "",
        '[node name="model" parent="." instance=ExtResource("1_model")]']
    for name, (x, y, z) in seats.items():
        lines += ["", f'[node name="{name}" type="Marker3D" parent="."]',
                  f"position = Vector3({_num(x)}, {_num(y)}, {_num(z)})"]
    return "\n".join(lines) + "\n"


def _description(root, prop):
    """The existing scene's editor_description, quoted as it is written, or None."""
    path = scene_path(root, prop)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        m = re.search(r'^editor_description = ("(?:[^"\\]|\\.)*")$', f.read(), flags=re.M)
    return m.group(1) if m else None


def default_description(prop, seats):
    title = prop.replace("_", " ")
    return _quote(f"{title[0].upper()}{title[1:]}. Faces local +Z." + (
        " seat_l and seat_r are the seat contract every seated guest and the Blender check "
        "rely on; move them only together with the model." if seats else ""))


def write(root, prop):
    """Write the scene; returns the sentence for the report."""
    seats = markers()
    text = text_for(prop, seats, _description(root, prop) or default_description(prop, seats))
    path = scene_path(root, prop)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    where = os.path.relpath(path, root)
    if seats:
        at = "; ".join(f"{n} at ({', '.join(_num(c) for c in v)})" for n, v in seats.items())
        return f"Wrote {where}: the GLB as 'model', {at}."
    return f"Wrote {where}: the GLB as 'model' (no seat markers in this file)."


def _wrap(text, width):
    out, line = [], ""
    for word in text.split():
        if line and len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return out + [line] if line else out


def _quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def after_send(root, prop):
    """Remember whether to offer the scene, after a Send of `prop`."""
    # A prop whose file names its own Godot scene (the palm crown's
    # `scenes/world/palm_crown.tscn`, which picks fronds per tree) is not
    # offered the bench pattern.
    if bpy.context.scene.get("kyt_godot_scene"):
        _offer.pop(prop, None)
        return
    s = state(root, prop)
    if s == "wraps":
        _offer.pop(prop, None)
    else:
        _offer[prop] = s


def offer(prop):
    return _offer.get(prop)


class KYT_OT_write_godot_scene(bpy.types.Operator):
    """Write the prop's Godot scene so it wraps the GLB, with the seat markers from this file"""
    bl_idname = "kyt.write_godot_scene"
    bl_label = "Write Godot scene"

    def _where(self):
        root = checks.project_root(bpy.data.filepath)
        prop = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        return root, prop

    def invoke(self, context, event):
        root, prop = self._where()
        if root is None or state(root, prop) != "other":
            return self.execute(context)
        return context.window_manager.invoke_props_dialog(
            self, width=420, title=f"Replace {prop}.tscn?", confirm_text="Replace")

    def draw(self, context):
        root, prop = self._where()
        path = os.path.relpath(scene_path(root, prop), root)
        keep = ("Git keeps the current version." if tracked(root, path)
                else "It isn't in git, so the current version will be gone.")
        text = (f"{path} is editor-owned. It holds {summary(root, prop)} and doesn't use the GLB. "
                f"The new scene wraps assets/props/{prop}.glb with this file's seat markers "
                f"and keeps its description. {keep}")
        col = self.layout.column(align=True)
        for i, chunk in enumerate(_wrap(text, 58)):
            col.label(text=chunk, icon="ERROR" if i == 0 else "BLANK1")

    def execute(self, context):
        root, prop = self._where()
        if root is None:
            self.report({"ERROR"}, "Save the file inside the project first.")
            return {"CANCELLED"}
        if state(root, prop) == "wraps":
            _offer.pop(prop, None)
            self.report({"INFO"}, "The scene already wraps the GLB.")
            return {"CANCELLED"}
        line = write(root, prop)
        _offer.pop(prop, None)
        context.window_manager["kyt_last_report"] = line + " Godot shows it the next time its window is focused."
        self.report({"INFO"}, line)
        return {"FINISHED"}


def draw(layout, prop):
    s = offer(prop)
    if s is None:
        return
    box = layout.box()
    if s == "missing":
        box.label(text="No Godot scene for it yet.", icon="INFO")
        box.operator("kyt.write_godot_scene", icon="FILE_NEW")
    else:
        box.label(text="Its Godot scene lacks the GLB.", icon="INFO")
        box.operator("kyt.write_godot_scene", text="Replace Godot scene…", icon="FILE_REFRESH")


def register():
    bpy.utils.register_class(KYT_OT_write_godot_scene)


def unregister():
    bpy.utils.unregister_class(KYT_OT_write_godot_scene)
