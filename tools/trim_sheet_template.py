#!/usr/bin/env python3
"""The painting template for a trim sheet, from its layout file.

    python3 tools/trim_sheet_template.py assets/source/textures/<sheet>/<sheet>.layout.json

Writes two PNGs beside the layout, to stack in Photoshop, Procreate or Blender:

- `<sheet>_base.png`: each strip filled with its starting colour. Paint on this.
- `<sheet>_guide.png`: transparent, to sit on top as a layer while painting and
  be hidden or deleted before saving: strip boundaries, names and notes, a tick
  every metre at the sheet's pixels-per-metre, the bleed margin, and a marker
  on both side edges of every tiling strip, whose left and right edges must
  continue into each other because the strip repeats sideways along a prop.

The layout file is the one source for where each strip is. The script that maps
a prop's parts onto the sheet reads the same file, so the painting and the
mapping cannot disagree. Refuses to overwrite a base PNG, which by then is
Christina's painting; the guide is always safe to rewrite.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main(layout_path):
    layout = json.load(open(layout_path))
    w, h = layout["size_px"]
    ppm = layout["px_per_metre"]
    bleed = layout["bleed_px"]
    folder = os.path.dirname(os.path.abspath(layout_path))
    name = layout["name"]

    base_path = os.path.join(folder, f"{name}_base.png")
    if os.path.exists(base_path):
        print(f"trim_sheet_template: {base_path} exists (it may be painted); leaving it alone")
    else:
        base = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(base)
        for row in layout["rows"]:
            y0, y1 = row["y"]
            draw.rectangle([0, y0, w - 1, y1 - 1], fill=hex_rgb(row["base"]))
        base.save(base_path)
        print(f"trim_sheet_template: wrote {base_path}")

    guide = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(guide)
    label = ImageFont.truetype(FONT, 22)
    small = ImageFont.truetype(FONT, 15)
    line = (255, 255, 255, 230)
    soft = (255, 255, 255, 110)
    bleed_c = (255, 80, 80, 120)
    for row in layout["rows"]:
        y0, y1 = row["y"]
        g.line([0, y0, w, y0], fill=line, width=2)
        g.rectangle([0, y0, w - 1, y0 + bleed - 1], fill=bleed_c)
        g.rectangle([0, y1 - bleed, w - 1, y1 - 1], fill=bleed_c)
        tall = y1 - y0
        # A row of cells is labelled in its last cell, clear of the small ones.
        lx = row["cells"][-1]["x"][0] + 12 if row.get("cells") else 12
        ly = y0 + (30 if row.get("cells") else 8)
        g.text((lx, ly), f"{row['id']}   ({tall} px = {tall / ppm * 100:.0f} cm)",
               font=label if tall >= 128 else small, fill=line)
        if tall >= 128:
            g.text((lx, ly + 28), row.get("note", ""), font=small, fill=soft)
        if row.get("tiles"):
            # A tick per metre along the strip, and the seam markers.
            for x in range(0, w, ppm):
                g.line([x, y1 - bleed - 14, x, y1 - bleed], fill=soft, width=2)
                g.text((x + 4, y1 - bleed - 30), f"{x // ppm} m", font=small, fill=soft)
            mid = (y0 + y1) // 2
            g.polygon([(0, mid - 10), (14, mid), (0, mid + 10)], fill=line)
            g.polygon([(w - 1, mid - 10), (w - 15, mid), (w - 1, mid + 10)], fill=line)
            g.text((w - 190, y0 + 8), "tiles left-right", font=small, fill=soft)
        for cell in row.get("cells", []):
            x0, x1 = cell["x"]
            cy0, cy1 = cell["y"]
            g.rectangle([x0, cy0, x1 - 1, cy1 - 1], outline=line, width=2)
            g.text((x0 + 6, cy0 + 6), cell["id"], font=small, fill=line)
    guide_path = os.path.join(folder, f"{name}_guide.png")
    guide.save(guide_path)
    print(f"trim_sheet_template: wrote {guide_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 tools/trim_sheet_template.py <layout.json>")
    main(sys.argv[1])
