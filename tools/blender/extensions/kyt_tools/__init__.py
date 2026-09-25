"""Keep Your Ticket tools for Blender: the sidebar panel for props.

Install once: Edit > Preferences > Get Extensions > Repositories (the drop-down
at the top right) > + > Add Local Repository, and choose the project's
`tools/blender/extensions` folder. Then enable "Keep Your Ticket" in the
Add-ons list. Because Blender loads it straight from the project, a tools update
pulled through git reaches Blender without reinstalling.

The panel lives in the 3D viewport's sidebar (N) under the "Keep Your Ticket"
tab: Check, Make game mesh, Rebuild game mesh, Send to game, Open in Godot, and
the findings of the last run.
"""

import os
import subprocess
import sys

import bpy

from . import checks, game_mesh, send

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
        if not findings:
            lines = ["All clear: ready to send to the game."]
        else:
            lines = [f"{level.title()}: {text}" for level, text in findings]
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
        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("kyt.check", icon="CHECKMARK")
        col.operator("kyt.make_game_mesh", icon="MOD_BOOLEAN")
        col.operator("kyt.rebuild_game_mesh", icon="FILE_REFRESH")
        col.operator("kyt.send_to_game", icon="EXPORT")
        layout.operator("kyt.open_godot", icon="WINDOW")
        report = context.window_manager.get("kyt_last_report")
        if report:
            box = layout.box()
            for line in report.split("\n"):
                for chunk in _wrap(line, 42):
                    box.label(text=chunk)


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


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.kyt_stage
