#!/usr/bin/env python3
"""Neutral gum shapes the game can tint any colour, from Christina's painted gum.

    python3 tools/gum_shapes.py

Reads the painted gum decals in `assets/source/textures/dressing/gum_*.png`
and writes `assets/props/dressing/gum_shape_<name>.png`: the same shape,
shading and shadow in light grey, so the bench's gum script can tint a copy
pink, blue, white or grey by multiplying (a pink gum can't be tinted blue; grey
can be tinted anything). The body's brighter half is lifted to near white; the
shadow stays dark, so it stays a shadow whatever the tint. Run again after
repainting or adding a gum.
"""

import glob
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "assets", "source", "textures", "dressing")
OUT = os.path.join(ROOT, "assets", "props", "dressing")
BODY_ALPHA = 0.8  # pixels at least this opaque are the gum itself, not its shadow
BRIGHT = 0.92  # the body's upper luminance is lifted to this


def main():
    os.makedirs(OUT, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(SOURCE, "gum_*.png"))):
        rgba = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255
        rgb, a = rgba[..., :3], rgba[..., 3]
        lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        body = a >= BODY_ALPHA
        top = np.percentile(lum[body], 90) if body.any() else lum.max()
        grey = np.clip(lum * (BRIGHT / max(top, 1e-3)), 0, 1)
        # The shadow keeps its own darkness: only the gum body is lifted.
        grey = np.where(body, grey, lum)
        out = np.dstack([grey, grey, grey, a])
        name = os.path.splitext(os.path.basename(path))[0].replace("gum_", "gum_shape_")
        dest = os.path.join(OUT, name + ".png")
        Image.fromarray((out * 255).round().astype(np.uint8), "RGBA").save(dest, optimize=True)
        print(f"gum_shapes: {os.path.relpath(dest, ROOT)} from {os.path.basename(path)}")


if __name__ == "__main__":
    main()
