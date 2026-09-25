"""Reload the prop's textures when they change on disk, so a save in Photoshop
shows in the viewport a moment later.

`tools/photoshop/on_save.jsx` writes `<prop>_colour.png` whenever Christina
saves the canvas PSD, and sends the prop to the game headless. This is the
Blender half. Once a second it looks at the image files the `export`
collection's materials read; a file whose time or size changed, and then held
still for one more look (so a PNG still being written isn't read half done),
is reloaded. Nothing is saved or sent from here, so the open file doesn't turn
modified. An image with unsaved paint on it in Blender is left alone, so a
reload never throws painting away. The panel's "Reload textures on save"
switch turns it off for a file.
"""

import os
import time

import bpy
from bpy.app.handlers import persistent

from . import checks

POLL_S = 1.0
_seen = {}  # image file -> (mtime, size) it was last loaded at
_pending = {}  # image file -> (mtime, size) seen changed once, waiting to hold still


def _images():
    export = bpy.data.collections.get(checks.EXPORT_COLLECTION)
    found = {}
    for obj in export.all_objects if export else []:
        for slot in obj.material_slots:
            tree = slot.material.node_tree if slot.material else None
            for node in tree.nodes if tree else []:
                img = node.image if node.type == "TEX_IMAGE" else None
                if img and img.source == "FILE" and img.filepath:
                    found[os.path.normpath(bpy.path.abspath(img.filepath, library=img.library))] = img
    return found


def _stamp(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    return st.st_mtime_ns, st.st_size


def _check(context):
    if context.scene is None or not context.scene.kyt_reload_textures:
        return
    reloaded, held = [], []
    for path, img in _images().items():
        stamp = _stamp(path)
        if stamp is None:
            continue
        if path not in _seen:
            _seen[path] = stamp
            continue
        if stamp == _seen[path]:
            _pending.pop(path, None)
            continue
        if _pending.get(path) != stamp:
            _pending[path] = stamp
            continue
        _seen[path] = stamp
        del _pending[path]
        if img.is_dirty:
            held.append(os.path.basename(path))
            continue
        img.reload()
        reloaded.append(os.path.basename(path))
    if not (reloaded or held):
        return
    lines = []
    if reloaded:
        lines.append(f"{time.strftime('%H:%M:%S')}: reloaded {', '.join(reloaded)} from disk.")
    if held:
        lines.append(f"{', '.join(held)} changed on disk, but has unsaved paint in Blender; "
                     "not reloaded.")
    context.window_manager["kyt_last_report"] = "\n".join(lines)
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in ("VIEW_3D", "IMAGE_EDITOR"):
                area.tag_redraw()


def _tick():
    try:
        _check(bpy.context)
    except Exception as exc:  # a timer that raises is dropped for the session
        print(f"Keep Your Ticket: reload textures: {exc}")
    return POLL_S


@persistent
def _on_load(_):
    _seen.clear()
    _pending.clear()


def register():
    bpy.types.Scene.kyt_reload_textures = bpy.props.BoolProperty(
        name="Reload textures on save", default=True,
        description="Reload the prop's textures when they change on disk, as when the canvas "
                    "is saved in Photoshop")
    bpy.app.handlers.load_post.append(_on_load)
    bpy.app.timers.register(_tick, first_interval=POLL_S, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    del bpy.types.Scene.kyt_reload_textures
