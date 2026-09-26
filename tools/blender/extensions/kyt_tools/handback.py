"""Open texture in Photoshop and Hand back: `tools/prop_handback.py` from the panel.

Open texture in Photoshop is `prop_handback.py <prop> --open` (the canvas PSD
opened, or made from the canvas first). Hand back is `prop_handback.py <prop>`, stage 8
of `documentation/prop-pipeline.md`: export, shrink, send, import, verify,
tests and renders, which takes minutes. Both run in the background, so Blender
stays usable; the panel shows each `ok`/`FAIL`/`note` line as it arrives and,
at the end, the renders folder with a button to open it.

Hand back reads the files as saved, so it refuses while this file has unsaved
changes. One command runs at a time.

**Which python.** `prop_handback.py` needs Pillow. Blender started from the
Dock or Finder has only the system's PATH, whose `/usr/bin/python3` has no
Pillow on Christina's Mac, so the first python here that can import it is used
(`KYT_PYTHON` names one explicitly).
"""

import os
import shutil
import subprocess
import threading
import time

import bpy

from . import checks, game_mesh

PYTHONS = ("/opt/homebrew/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3")
SHOWN = ("ok ", "FAIL", "note", "Hand-back ", "Canvas open", "Preview:")
POLL_S = 0.5

_python = None
_job = None  # the command running now, or the last one


def find_python():
    """The first python3 that can import Pillow, or None."""
    global _python
    if _python:
        return _python
    candidates = [os.environ.get("KYT_PYTHON")] + list(PYTHONS) + [shutil.which("python3")]
    for exe in dict.fromkeys(c for c in candidates if c and os.path.exists(c)):
        try:
            ok = subprocess.run([exe, "-c", "import PIL"], capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
        if ok:
            _python = exe
            return exe
    return None


def prop_of(blend_path):
    """(prop name, None) for a working prop file, or (None, why not)."""
    if not blend_path:
        return None, "Save the file first."
    root = checks.project_root(blend_path)
    if root is None:
        return None, "This file isn't inside the Keep Your Ticket project."
    stem = os.path.splitext(os.path.basename(blend_path))[0]
    if stem.endswith(game_mesh.SOURCE_SUFFIX):
        working = stem[:-len(game_mesh.SOURCE_SUFFIX)]
        return None, (f"This is the source file. Hand back from {working}.blend "
                      "(Rebuild game mesh there first if the parts changed).")
    return stem, None


class Job:
    """One prop_handback.py run: its output read on a thread, shown by a timer."""

    def __init__(self, title, prop, cmd, cwd):
        self.title, self.prop, self.cwd = title, prop, cwd
        self.output = []
        self.code = None
        self.started, self.ended = time.time(), None
        self.drawn_final = False  # the panel has shown how it ended
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        env["PYTHONUNBUFFERED"] = "1"
        self.proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            self.output.append(line.rstrip("\n"))
        self.code = self.proc.wait()
        self.ended = time.time()

    @property
    def running(self):
        return self.ended is None

    def lines(self):
        """The lines worth showing: each step's verdict and the last word."""
        out = list(self.output)
        shown = [l for l in out if l.startswith(SHOWN)]
        if not self.running and self.code and not any(l.startswith("FAIL") for l in shown):
            shown += [f"FAIL {l}" for l in out[-3:]] or [f"FAIL exit {self.code}"]
        return shown

    def folder(self):
        """The renders folder the run reported, absolute, once it exists."""
        for line in reversed(self.output):
            for marker in ("Renders and report: ", "Preview: "):
                if marker in line:
                    path = os.path.join(self.cwd, line.split(marker, 1)[1].strip())
                    return path if os.path.isdir(path) else None
        return None

    def status(self):
        elapsed = (self.ended or time.time()) - self.started
        clock = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
        if self.running:
            return f"{self.title}: running, {clock}"
        verdict = "done" if self.code == 0 else "stopped"
        return f"{self.title}: {verdict} in {clock}"


def current():
    return _job


def start(title, prop, args):
    """Run prop_handback.py for `prop` with `args`; returns an error sentence or None."""
    global _job
    if _job is not None and _job.running:
        return f"{_job.title} is still running."
    root = checks.project_root(bpy.data.filepath)
    python = find_python()
    if python is None:
        return ("No python3 with Pillow found (tried " + ", ".join(PYTHONS) + "). "
                "Install Pillow for one, or set KYT_PYTHON.")
    script = os.path.join(root, "tools", "prop_handback.py")
    try:
        _job = Job(title, prop, [python, script, prop] + args, root)
    except OSError as exc:
        return f"Couldn't start {os.path.relpath(script, root)}: {exc}"
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=POLL_S, persistent=True)
    return None


def _redraw():
    wm = bpy.context.window_manager
    for window in wm.windows if wm else []:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _tick():
    """Redraw while the command runs, and until the panel has drawn how it
    ended (a redraw tagged as it finishes can be missed), or for a few seconds
    if the panel isn't showing."""
    _redraw()
    if _job is None:
        return None
    if _job.running:
        return POLL_S
    if not _job.drawn_final and time.time() - _job.ended < 5:
        return POLL_S
    return None


def canvas_missing(root, prop):
    """Why Open texture in Photoshop can't start yet, or None."""
    textures = os.path.join(root, "assets", "source", "textures", prop)
    if os.path.exists(os.path.join(textures, f"{prop}_colour.psd")):
        return None
    if all(os.path.exists(os.path.join(textures, f"{prop}_{kind}.png")) for kind in ("colour", "uv_guide")):
        return None
    return ("There's no canvas yet: it comes after the game mesh and the unwrap "
            "(stage 5, paint_canvas.py).")


class KYT_OT_open_texture(bpy.types.Operator):
    """Open the prop's texture (its canvas PSD) in Photoshop, making the PSD from the canvas first if there isn't one"""
    bl_idname = "kyt.open_texture"
    bl_label = "Open texture in Photoshop"

    def execute(self, context):
        prop, why = prop_of(bpy.data.filepath)
        why = why or canvas_missing(checks.project_root(bpy.data.filepath), prop)
        why = why or start("Open texture", prop, ["--open"])
        if why:
            context.window_manager["kyt_last_report"] = why
            self.report({"ERROR"}, why)
            return {"CANCELLED"}
        return {"FINISHED"}


class KYT_OT_hand_back(bpy.types.Operator):
    """Hand the prop back: export the PSD, send, import in Godot, test and render (tools/prop_handback.py), in the background. Uses the files as saved"""
    bl_idname = "kyt.hand_back"
    bl_label = "Hand back"

    def execute(self, context):
        prop, why = prop_of(bpy.data.filepath)
        if not why and bpy.data.is_dirty:
            why = "Save first: the hand-back uses this file as saved, and it has unsaved changes."
        why = why or start("Hand back", prop, [])
        if why:
            context.window_manager["kyt_last_report"] = why
            self.report({"ERROR"}, why)
            return {"CANCELLED"}
        return {"FINISHED"}


class KYT_OT_open_handback_folder(bpy.types.Operator):
    """Open the hand-back's renders and report in Finder"""
    bl_idname = "kyt.open_handback_folder"
    bl_label = "Open renders"

    def execute(self, context):
        folder = _job.folder() if _job else None
        if not folder:
            self.report({"ERROR"}, "No renders folder yet.")
            return {"CANCELLED"}
        subprocess.Popen(["open", folder])
        return {"FINISHED"}


CLASSES = (KYT_OT_open_texture, KYT_OT_hand_back, KYT_OT_open_handback_folder)


def draw(layout, wrap):
    """The running or last command's box in the panel; `wrap(text)` splits a
    line. An `ok` line keeps to one line (the whole report is in the renders
    folder's README); a FAIL or a note is shown in full."""
    job = _job
    if job is None or job.prop != os.path.splitext(os.path.basename(bpy.data.filepath))[0]:
        return
    if not job.running:
        job.drawn_final = True
    box = layout.box()
    box.label(text=job.status(), icon="SORTTIME" if job.running else
              ("CHECKMARK" if job.code == 0 else "ERROR"))
    icons = {"ok": "CHECKMARK", "FAIL": "ERROR", "note": "INFO"}
    for line in job.lines():
        line = line.split(" Renders and report: ", 1)[0]  # the folder is shown below
        mark, _, rest = line.partition(" ")
        icon = icons.get(mark)
        text = rest.strip() if icon else line
        chunks = [text] if mark == "ok" else wrap(text)
        for i, chunk in enumerate(chunks):
            box.label(text=chunk, icon=(icon if i == 0 else "BLANK1") if icon else "NONE")
    folder = job.folder()
    if folder:
        box.label(text=os.path.basename(folder), icon="FILE_FOLDER")
        box.operator("kyt.open_handback_folder")


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
