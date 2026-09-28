#!/usr/bin/env python3
"""A prop's normal map from its bump map: the bump is what Christina paints.

    python3 tools/bump_to_normal.py <prop>

Reads `assets/source/textures/<prop>/<prop>_bump.png`, greyscale height (white
raised, black sunk, mid-grey level), and writes `<prop>_normal.png` beside it:
tangent space, OpenGL convention (green up the texture), which is what the
glTF export carries and Godot reads. glTF has no bump maps, so the game only
ever sees the normal map; `tools/prop_handback.py` runs this before every send
when a bump exists, so a painted bump always reaches the game.

`DEPTH_PX` is how far white stands above black, in canvas pixels: the
trunk's 4 mm at about 890 pixels a metre. `WRAP_U` props have textures that
wrap round their width (the trunk's bands go all the way round), so the left
and right edges are neighbours.

`normal_from_height` is also used by `tools/blender/paint_canvas.py`, inside
Blender, which has numpy but no Pillow.
"""

import os
import sys

import numpy as np

DEPTH_PX = {"palm_trunk": 3.5}
WRAP_U = {"palm_trunk"}


def normal_from_height(height, depth_px, wrap_u=False):
    """(h, w) heights 0..1, rows top to bottom, to (h, w, 3) normal colours 0..1."""
    h = height.astype(np.float32) * depth_px
    if wrap_u:
        du = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2.0
    else:
        p = np.pad(h, ((0, 0), (1, 1)), mode="edge")
        du = (p[:, 2:] - p[:, :-2]) / 2.0
    p = np.pad(h, ((1, 1), (0, 0)), mode="edge")
    # Rows run down the image, the texture's v runs up it.
    dv = -(p[2:, :] - p[:-2, :]) / 2.0
    n = np.stack([-du, -dv, np.ones_like(h)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def main():
    from PIL import Image

    prop = sys.argv[1]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(root, "assets", "source", "textures", prop)
    bump, normal = (os.path.join(folder, f"{prop}_{k}.png") for k in ("bump", "normal"))
    with Image.open(bump) as im:
        height = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    rgb = normal_from_height(height, DEPTH_PX.get(prop, 3.0), prop in WRAP_U)
    Image.fromarray(np.round(rgb * 255.0).astype(np.uint8), "RGB").save(normal)
    print(f"bump_to_normal: {os.path.relpath(normal, root)} from {os.path.basename(bump)} "
          f"({height.shape[1]}x{height.shape[0]}, {DEPTH_PX.get(prop, 3.0)} px deep"
          f"{', wrapping round' if prop in WRAP_U else ''})")


if __name__ == "__main__":
    main()
