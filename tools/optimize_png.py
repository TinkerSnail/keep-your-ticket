#!/usr/bin/env python3
"""Make PNGs smaller without changing a single pixel.

    python3 tools/optimize_png.py <file.png> [<file.png> ...]

For each file: drops channels that carry nothing (an alpha that is opaque
everywhere, colour that is grey everywhere), strips metadata (text, dates,
EXIF; an embedded colour profile is kept), and re-encodes at maximum lossless
compression. The new file replaces the old only if it decodes to exactly the
same pixels and is smaller; otherwise the original is left alone. Reports the
saving per file.

Run it on a painted texture after exporting it and before Send to game, so the
smaller file is what the GLB carries.
"""

import os
import shutil
import sys
import tempfile

from PIL import Image


def slimmest(im):
    """The same pixels in the fewest channels."""
    if im.mode in ("RGBA", "LA") and im.getchannel("A").getextrema() == (255, 255):
        im = im.convert("RGB" if im.mode == "RGBA" else "L")
    if im.mode == "RGB":
        r, g, b = im.split()
        if r.tobytes() == g.tobytes() == b.tobytes():
            im = r
    return im


def same_pixels(a, b):
    return a.size == b.size and a.convert("RGBA").tobytes() == b.convert("RGBA").tobytes()


def optimize(path):
    before = os.path.getsize(path)
    with Image.open(path) as src:
        src.load()
        icc = src.info.get("icc_profile")
        if src.mode in ("I;16", "I", "F"):
            return f"{path}: {src.mode} left alone (only 8-bit images are re-encoded)"
        out = slimmest(src)
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(suffix=".png", dir=folder)
    os.close(fd)
    try:
        kwargs = {"optimize": True}
        if icc:
            kwargs["icc_profile"] = icc
        out.save(tmp, "PNG", **kwargs)
        with Image.open(path) as a, Image.open(tmp) as b:
            if not same_pixels(a, b):
                return f"{path}: re-encoded pixels differ; left alone"
        after = os.path.getsize(tmp)
        if after >= before:
            return f"{path}: already as small ({before // 1024} KB); left alone"
        shutil.copymode(path, tmp)  # the temporary file starts private; keep the original's permissions
        os.replace(tmp, path)
        tmp = None
        return (f"{path}: {before // 1024} KB -> {after // 1024} KB "
                f"({100 * (before - after) // before}% smaller, {out.mode})")
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python3 tools/optimize_png.py <file.png> [...]")
    for p in sys.argv[1:]:
        print("optimize_png:", optimize(p))
