"""Keep Your Ticket tools for Blender: the sidebar panel for props.

Install once: Edit > Preferences > Get Extensions > Repositories (the drop-down
at the top right) > + > Add Local Repository, and choose the project's
`tools/blender/extensions` folder. Then enable "Keep Your Ticket" in the
Add-ons list. Because Blender loads it straight from the project, a tools update
pulled through git reaches Blender without reinstalling.

The panel lives in the 3D viewport's sidebar (N) under the "Keep Your Ticket"
tab: the Show reference switch (reference.py); Check (checks.py, with the UV
findings of uv_check.py once there is a game mesh), Make game mesh, Rebuild
game mesh, Send to game (which offers the prop's Godot scene the first time,
godot_scene.py); once the prop has a canvas, a Photoshop box with Open texture
in Photoshop (handback.py), the UV guide, Add patch layer and the save hook's
switch (photoshop.py); Hand back (handback.py); the "Reload textures on save"
switch (live.py); Open in Godot; and the findings of the last run.
"""

import importlib
import os
import subprocess
import sys

import bpy

# Switching the add-on off and on makes Blender reload this file only, and
# only if it changed; the modules it imports would stay as first loaded. So a
# reload of this file reloads them too, dependencies first (R10 in
# prop-pipeline.md). On the first load none is in sys.modules yet.
for _name in ("uv_check", "checks", "game_mesh", "send", "reference", "live", "godot_scene", "handback",
              "photoshop"):
    if f"{__name__}.{_name}" in sys.modules:
        importlib.reload(sys.modules[f"{__name__}.{_name}"])

from . import checks, game_mesh, godot_scene, handback, live, photoshop, reference, send  # noqa: E402

STAGES = [
    ("blockout", "Block-out", "Rough shape and proportions"),
    ("model", "Model", "Final shape; no textures yet"),
    ("texture", "Texture", "UVs and paint; Check requires UVs"),
]


def _store(context, lines):
    context.window_manager["kyt_last_report"] = "\n".join(lines)


class KYT_OT_check(bpy.types.Operator):
    """Check the prop against the game's rules (scale, ground, materials, budget, seats)"""
    bl_idname = "kyt.check"
    bl_label = "Check"

    def execute(self, context):
        findings = checks.run(context)
        lines = [f"{level.title()}: {text}" for level, text in findings if level != "NOTE"]
        if not lines:
            lines = ["All clear: ready to send to the game."]
        lines += [text for level, text in findings if level == "NOTE"]
        _store(context, lines)
        errors = sum(1 for level, _ in findings if level == "ERROR")
        self.report({"ERROR"} if errors else {"INFO"},
                    f"{errors} to fix" if errors else "All clear")
        return {"FINISHED"}


class KYT_OT_send(bpy.types.Operator):
    """Check the prop, then write its GLB into the project for Godot"""
    bl_idname = "kyt.send_to_game"
    bl_label = "Send to game"

    def execute(self, context):
        ok, lines = send.run(context)
        _store(context, lines)
        prop, _ = handback.prop_of(bpy.data.filepath)
        if ok and prop:
            godot_scene.after_send(checks.project_root(bpy.data.filepath), prop)
        self.report({"INFO"} if ok else {"ERROR"}, lines[0])
        return {"FINISHED"} if ok else {"CANCELLED"}


class KYT_OT_game_mesh(bpy.types.Operator):
    """Save the original as <name>_source.blend, then fuse this file's parts into one clean, unwrapped mesh"""
    bl_idname = "kyt.make_game_mesh"
    bl_label = "Make game mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ok, lines = game_mesh.run(context)
        _store(context, lines)
        self.report({"INFO"} if ok else {"ERROR"}, lines[0])
        return {"FINISHED"} if ok else {"CANCELLED"}


class KYT_OT_rebuild_game_mesh(bpy.types.Operator):
    """Rebuild the game mesh from <name>_source.blend after its parts changed, keeping this mesh's material"""
    bl_idname = "kyt.rebuild_game_mesh"
    bl_label = "Rebuild game mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ok, lines = game_mesh.rebuild(context)
        _store(context, lines)
        self.report({"INFO"} if ok else {"ERROR"}, lines[0])
        return {"FINISHED"} if ok else {"CANCELLED"}


class KYT_OT_open_godot(bpy.types.Operator):
    """Open this project in the Godot editor"""
    bl_idname = "kyt.open_godot"
    bl_label = "Open in Godot"

    def execute(self, context):
        root = checks.project_root(bpy.data.filepath) if bpy.data.filepath else None
        if root is None:
            self.report({"ERROR"}, "Save the file inside the project first.")
            return {"CANCELLED"}
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-n", "-a", "Godot", "--args", "--path", root, "-e"])
        else:
            self.report({"ERROR"}, "Open Godot yourself on this computer; only the Mac is wired up so far.")
            return {"CANCELLED"}
        return {"FINISHED"}


class KYT_PT_panel(bpy.types.Panel):
    bl_label = "Keep Your Ticket"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Keep Your Ticket"

    def draw(self, context):
        layout = self.layout
        name = os.path.splitext(os.path.basename(bpy.data.filepath))[0] if bpy.data.filepath else "(unsaved)"
        layout.label(text=f"Prop: {name}")
        layout.prop(context.scene, "kyt_stage", text="Stage")
        row = layout.row()
        if reference.has_greybox():
            shown = context.scene.kyt_show_reference
            row.prop(context.scene, "kyt_show_reference", toggle=True,
                     icon="HIDE_OFF" if shown else "HIDE_ON")
        else:
            row.label(text="Reference: floor and seats only", icon="HIDE_OFF")
        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("kyt.check", icon="CHECKMARK")
        col.operator("kyt.make_game_mesh", icon="MOD_BOOLEAN")
        col.operator("kyt.rebuild_game_mesh", icon="FILE_REFRESH")
        col.operator("kyt.send_to_game", icon="EXPORT")
        godot_scene.draw(layout, name)
        job = handback.current()
        idle = job is None or not job.running
        prop, _ = handback.prop_of(bpy.data.filepath)
        if prop:
            def open_texture(box):
                row = box.row()
                row.scale_y = 1.3
                row.enabled = idle
                row.operator("kyt.open_texture", icon="BRUSH_DATA")
            photoshop.draw(layout, prop, checks.project_root(bpy.data.filepath), open_texture)
        row = layout.row()
        row.scale_y = 1.3
        row.enabled = idle
        row.operator("kyt.hand_back", icon="LOOP_FORWARDS")
        width = _chars(context)
        handback.draw(layout, lambda text: _wrap(text, width - 3))
        layout.prop(context.scene, "kyt_reload_textures")
        layout.operator("kyt.open_godot", icon="WINDOW")
        report = context.window_manager.get("kyt_last_report")
        if report:
            box = layout.box()
            for line in report.split("\n"):
                for chunk in _wrap(line, width):
                    box.label(text=chunk)


def _chars(context):
    """About how many characters fit across the sidebar, for wrapping."""
    # The system scale already includes a Retina screen's factor of two.
    return max(24, int(context.region.width / (context.preferences.system.ui_scale * 7)) - 2)


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width and line:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out or [""]


CLASSES = (KYT_OT_check, KYT_OT_game_mesh, KYT_OT_rebuild_game_mesh, KYT_OT_send,
           KYT_OT_open_godot, KYT_PT_panel)


def register():
    bpy.types.Scene.kyt_stage = bpy.props.EnumProperty(name="Stage", items=STAGES, default="blockout")
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    reference.register()
    godot_scene.register()
    handback.register()
    photoshop.register()
    live.register()


def unregister():
    live.unregister()
    photoshop.unregister()
    handback.unregister()
    godot_scene.unregister()
    reference.unregister()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.kyt_stage
