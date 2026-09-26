"""The panel's Photoshop box: the prop's canvas and the save hook, from Blender.

Open texture in Photoshop is handback.py's (`prop_handback.py <prop> --open`).
The rest act on the canvas once it is open in Photoshop, through AppleScript's
`do javascript`, the way `prop_handback.py` exports it:

- **UV guide Show / Hide** and **Add patch layer** run
  `tools/photoshop/canvas_tools.jsx` on `<prop>_colour.psd`. They never start
  Photoshop or open the canvas themselves, and never save it.
- **Save updates the prop** is the save hook's switch (`on_save.jsx` on
  Photoshop's "Save Document" event). Its state is read from Photoshop's own
  settings file, `tw0001.dat` in `~/Library/Preferences/Adobe Photoshop <year>
  Settings/`, which Photoshop rewrites as soon as its script events change:
  "true" when events are enabled, then an "event,path," line each. So showing
  it never starts Photoshop. Switching it runs `tools/photoshop/live_update.sh`,
  which needs Photoshop and starts it if it isn't running.

A UXP panel inside Photoshop was tried first (2026-09-25) and dropped for
this: UXP can't start a process, and reaching ExtendScript from it takes an
undocumented call.

Each command runs on a thread, so Blender never waits on Photoshop; the answer
lands in the panel's report.
"""

import glob
import os
import re
import subprocess
import threading
import urllib.parse

import bpy

from . import checks

POLL_S = 0.3
_results = []  # (sentence) from finished commands, for the main thread
_pending = [0]


def canvas_paths(root, prop):
    folder = os.path.join(root, "assets", "source", "textures", prop)
    return os.path.join(folder, f"{prop}_colour.psd"), os.path.join(folder, f"{prop}_colour.png")


def photoshop_running():
    """The app itself, not one of the helpers inside its bundle (LogTransport2
    lingers after Photoshop quits)."""
    return subprocess.run(["pgrep", "-f", r"\.app/Contents/MacOS/Adobe Photoshop [0-9]+( |$)"],
                          capture_output=True).returncode == 0


def _quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _jsx(root, name, args, activate=False):
    jsx = os.path.join(root, "tools", "photoshop", name)
    lines = ['tell application id "com.adobe.Photoshop"']
    if activate:
        lines.append("activate")
    lines.append(f"do javascript file (POSIX file {_quote(jsx)}) with arguments "
                 "{" + ", ".join(_quote(a) for a in args) + "}")
    lines.append("end tell")
    return ["osascript", "-e", "\n".join(lines)]


def _run(cmd, sentence):
    """Run `cmd` on a thread; `sentence(output)` becomes the report line."""
    def work():
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            said = (out.stdout + out.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            said = f"FAIL {exc}"
        _results.append(sentence(said))
    _pending[0] += 1
    threading.Thread(target=work, daemon=True).start()
    if not bpy.app.timers.is_registered(_poll):
        bpy.app.timers.register(_poll, first_interval=POLL_S, persistent=True)


def _poll():
    wm = bpy.context.window_manager
    while _results:
        _pending[0] -= 1
        if wm is not None:
            wm["kyt_last_report"] = _results.pop(0)
        else:
            _results.pop(0)
        for window in wm.windows if wm else []:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
    return POLL_S if _pending[0] > 0 else None


# ---- The save hook's state, from Photoshop's settings file ------------------

_settings = []  # found once: the panel asks on every redraw


def _settings_file():
    """Photoshop's script-events file for the newest installed version, or None."""
    if not _settings:
        folders = glob.glob(os.path.expanduser("~/Library/Preferences/Adobe Photoshop * Settings"))
        years = sorted((int(m.group(1)), f) for f in folders
                       if (m := re.search(r"Adobe Photoshop (\d{4}) Settings$", f)))
        _settings.append(os.path.join(years[-1][1], "tw0001.dat") if years else None)
    return _settings[0]


def hook_state(root):
    """'on', 'off', or None when Photoshop's settings can't be found."""
    path = _settings_file()
    if path is None:
        return None
    if not os.path.exists(path):
        return "off"
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [l for l in re.split(r"[\r\n]+", f.read()) if l]
    if not lines or lines[0].strip() != "true":
        return "off"
    ours = os.path.realpath(os.path.join(root, "tools", "photoshop", "on_save.jsx"))
    for line in lines[1:]:
        event, _, rest = line.partition(",")
        script = os.path.expanduser(urllib.parse.unquote(rest.split(",")[0]))
        if event == "save" and os.path.realpath(script) == ours:
            return "on"
    return "off"


# ---- Operators --------------------------------------------------------------

def _prop_and_root():
    """(prop, root, None) for a working prop file, or (None, None, why not)."""
    from . import handback  # the same rule as Hand back
    prop, why = handback.prop_of(bpy.data.filepath)
    return prop, (checks.project_root(bpy.data.filepath) if prop else None), why


def _canvas_open_or_why(root, prop):
    psd, _ = canvas_paths(root, prop)
    if not os.path.exists(psd):
        return "There's no PSD yet: Open texture in Photoshop makes it."
    if not photoshop_running():
        return "Photoshop isn't open: Open texture in Photoshop first."
    return None


def _canvas_reply(said):
    kind, _, rest = said.partition(" ")
    if kind == "GUIDE":
        return f"UV guide {rest} in Photoshop (not saved)."
    if kind == "PATCH":
        return f"Added the layer '{rest}' under the UV guide, selected; paint the patch on it."
    if kind == "NOTOPEN":
        return f"{rest} isn't open in Photoshop: Open texture in Photoshop first."
    if kind == "NOGUIDE":
        return rest + "."
    return f"Photoshop said: {said or 'nothing'}"


class KYT_OT_uv_guide(bpy.types.Operator):
    """Show or hide the UV guide layer in the prop's canvas, open in Photoshop"""
    bl_idname = "kyt.uv_guide"
    bl_label = "UV guide"

    show: bpy.props.BoolProperty(name="Show", default=False)

    def execute(self, context):
        prop, root, why = _prop_and_root()
        why = why or _canvas_open_or_why(root, prop)
        if why:
            context.window_manager["kyt_last_report"] = why
            self.report({"ERROR"}, why)
            return {"CANCELLED"}
        psd, _ = canvas_paths(root, prop)
        _run(_jsx(root, "canvas_tools.jsx", ["guide", psd, "show" if self.show else "hide"]), _canvas_reply)
        return {"FINISHED"}


class KYT_OT_patch_layer(bpy.types.Operator):
    """Add an empty '<name> patch' layer under the UV guide in the prop's canvas, for dressing such as gum"""
    bl_idname = "kyt.patch_layer"
    bl_label = "Add patch layer"

    def execute(self, context):
        prop, root, why = _prop_and_root()
        why = why or _canvas_open_or_why(root, prop)
        name = re.sub(r"[^A-Za-z0-9 _-]", "", context.scene.kyt_patch_name).strip()[:40] or "gum"
        if why:
            context.window_manager["kyt_last_report"] = why
            self.report({"ERROR"}, why)
            return {"CANCELLED"}
        psd, _ = canvas_paths(root, prop)
        _run(_jsx(root, "canvas_tools.jsx", ["patch", psd, name], activate=True), _canvas_reply)
        return {"FINISHED"}


class KYT_OT_save_hook(bpy.types.Operator):
    """Turn the Photoshop save hook on or off: while on, each save of a prop canvas writes its PNG and sends the prop"""
    bl_idname = "kyt.save_hook"
    bl_label = "Save updates the prop"

    on: bpy.props.BoolProperty(name="On", default=True)

    def execute(self, context):
        root = checks.project_root(bpy.data.filepath) if bpy.data.filepath else None
        if root is None:
            self.report({"ERROR"}, "Save the file inside the project first.")
            return {"CANCELLED"}
        script = os.path.join(root, "tools", "photoshop", "live_update.sh")
        on = self.on

        def sentence(said):
            if said.startswith("ON"):
                return "Save hook on: each save of a canvas PSD writes its PNG and sends the prop."
            if said.startswith("OFF"):
                return "Save hook off: saving a canvas PSD changes only the PSD."
            return f"The save hook didn't switch {'on' if on else 'off'}: {said or 'no answer'}"
        _run(["/bin/sh", script, "on" if on else "off"], sentence)
        context.window_manager["kyt_last_report"] = (
            f"Turning the save hook {'on' if on else 'off'}"
            + ("" if photoshop_running() else " (starting Photoshop first)") + "…")
        return {"FINISHED"}


CLASSES = (KYT_OT_uv_guide, KYT_OT_patch_layer, KYT_OT_save_hook)


def draw(layout, prop, root, open_texture):
    """The Photoshop box, once the prop has a canvas. `open_texture` draws the
    Open texture button (handback.py's operator, disabled while it runs)."""
    psd, png = canvas_paths(root, prop)
    if not (os.path.exists(psd) or os.path.exists(png)):
        return
    box = layout.box()
    box.label(text="Photoshop", icon="IMAGE_DATA")
    open_texture(box)
    row = box.row(align=True)
    row.label(text="UV guide")
    row.operator("kyt.uv_guide", text="Show").show = True
    row.operator("kyt.uv_guide", text="Hide").show = False
    row = box.row(align=True)
    row.prop(bpy.context.scene, "kyt_patch_name", text="")
    row.operator("kyt.patch_layer")
    state = hook_state(root)
    if state is not None:
        row = box.row(align=True)
        row.label(text=f"Save hook: {'On' if state == 'on' else 'Off'}",
                  icon="CHECKMARK" if state == "on" else "PANEL_CLOSE")
        row.operator("kyt.save_hook", text="Turn off" if state == "on" else "Turn on").on = state != "on"


def register():
    bpy.types.Scene.kyt_patch_name = bpy.props.StringProperty(
        name="Patch", default="gum", description="What the patch is for; the layer is '<name> patch'")
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    if bpy.app.timers.is_registered(_poll):
        bpy.app.timers.unregister(_poll)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.kyt_patch_name
