"""Put a perforated prop's holes back into its colour PNG after an export.

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
        --python tools/blender/apply_holes.py -- <prop>_colour.png [<prop>_holes.png]

`paint_canvas.py --perforate` bakes the holes into the colour PNG's alpha and
into `<prop>_holes.png` beside it (white metal, black hole). Christina paints
in a PSD, and its flattened export has no alpha, so every export runs this
after it (`prop_handback.py` and the Photoshop save hook): the colour's alpha
becomes the holes image, and each hole's colour becomes the metal round it, so
filtering and mipmaps never pull the flattened background into a hole's edge.
Metal pixels keep their colour exactly, and running it twice changes nothing.
With no holes image it leaves the PNG alone, so it is safe for any prop.
"""

import os
import sys

import bpy
import numpy as np

SPREAD_PX = 8  # how far each pass carries the metal's colour into a hole
PASSES = 4


def box(a, r):
    """Box blur of an (h, w, c) array, radius r, edges clamped."""
    for axis in (0, 1):
        a = np.moveaxis(a, axis, 0)
        pad = [(r + 1, r)] + [(0, 0)] * (a.ndim - 1)
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=0)
        n = a.shape[0]
        a = np.moveaxis((c[2 * r + 1:2 * r + 1 + n] - c[:n]) / (2 * r + 1), 0, axis)
    return a


def pixels(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    png = os.path.abspath(argv[0])
    holes_png = os.path.abspath(argv[1]) if len(argv) > 1 else png.replace("_colour.png", "_holes.png")
    if not os.path.exists(holes_png):
        print(f"apply_holes: no {os.path.basename(holes_png)}; {os.path.basename(png)} left alone")
        return
    px, mask = pixels(png), pixels(holes_png)[..., 0]
    if px.shape[:2] != mask.shape:
        print(f"apply_holes: FAIL {os.path.basename(png)} is {px.shape[1]}x{px.shape[0]}, "
              f"the holes {mask.shape[1]}x{mask.shape[0]}")
        return
    rgb = px[..., :3].copy()
    known = (mask >= 0.5).astype(np.float32)[..., None]
    for _ in range(PASSES):
        num, den = box(rgb * known, SPREAD_PX), box(known, SPREAD_PX)
        grow = (known[..., 0] == 0) & (den[..., 0] > 1e-4)
        rgb[grow] = num[grow] / den[grow]
        known[grow] = 1.0
    px[..., :3] = rgb
    px[..., 3] = mask
    h, w = mask.shape
    out = bpy.data.images.new("apply_holes", w, h, alpha=True)
    out.pixels.foreach_set(px.ravel())
    out.filepath_raw = png
    out.file_format = "PNG"
    out.save()
    print(f"apply_holes: {os.path.basename(png)} takes its alpha from {os.path.basename(holes_png)} "
          f"({(mask < 0.5).mean():.0%} holes), hole colours carried in from the metal")


main()
