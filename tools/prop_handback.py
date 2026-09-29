#!/usr/bin/env python3
"""One hand-back for a painted prop: from Christina's saved PSD to tested in the game.

    python3 tools/prop_handback.py <prop> [--no-export] [--allow-unsaved] [--no-tests] [--no-renders]
    python3 tools/prop_handback.py <prop> --open      # open (or make) the canvas PSD in Photoshop
    python3 tools/prop_handback.py <prop> --preview   # render her work in progress; nothing sent

Stage 8 of `documentation/prop-pipeline.md`, run in order, stopping at the
first thing that fails:

1. **Export.** `assets/source/textures/<prop>/<prop>_colour.psd` through
   Photoshop (`tools/photoshop/export_canvas.jsx`): a flattened copy, every
   "UV guide" layer hidden, over `<prop>_colour.png`. A crown's "cut-out"
   layer is exported beside it as `<prop>_cutout.png` and goes into its
   alpha; a perforated prop's holes do from `<prop>_holes.png`
   (`tools/blender/apply_holes.py`). Refused if the PSD has
   unsaved changes, so the PNG always matches a saved PSD (`--allow-unsaved`
   overrides; `--no-export` skips the step for a PNG exported by hand).
2. **Normal map**, when the prop has a bump (`<prop>_bump.png`, greyscale,
   hers to paint): `tools/bump_to_normal.py` makes `<prop>_normal.png` from
   it, since glTF and Godot read normal maps, not bumps.
3. **Shrink** the colour, ORM and normal PNGs (`tools/optimize_png.py`: pixel-identical
   or left alone). Blender embeds the PNG's own bytes, so the GLB shrinks too.
4. **Send to game** from the saved `assets/source/props/<prop>.blend`, headless
   (Check first). If Blender is open, unsaved changes there are not included.
5. **Import** in Godot, headless.
6. **Verify** that Godot's extracted copies in `assets/props/` match the PNGs
   pixel for pixel and are VRAM-compressed with mipmaps; the import setting is
   put right (and imported again) if not.
7. **Test:** `seat_test.py` (or the prop's own, `PROP_TESTS`: the palm
   crown's are the palm and catalog tests), `clearance_test`, `budget_test`,
   `ground_contact_test` (failing only on its known standing surfaces,
   `KNOWN_GROUND`, counts as passing).
8. **Render** the prop from four views into
   `documentation/screenshots/handbacks/<prop>-<time>/`, with this report as
   its README.

It never commits: that is Christina's word. Mac only (Photoshop through
AppleScript). Set BLENDER or GODOT to use other binaries.

`--cutout-layer` puts a crown's re-cut leaflets (`paint_canvas.py --leaflets
--cutout-only`) into its PSD's cut-out layer, unsaved, for her to look at.

`--shading-layer` puts a crown's painted starting look (`paint_canvas.py
--leaflets --shading-only`) into its PSD as "shading (Claude)" above `paint`,
unsaved.

`--hole-layers` refreshes a perforated prop's two hole layers in its PSD (the
canvas under the paint, the holes as a guide on top) after the holes are cut
again with `paint_canvas.py --holes-only`; `--open` adds them to a new PSD.

`--open` is stage 6's set-up: the prop's PSD opened in Photoshop, made first
if there isn't one (colour PNG as the `paint` layer, the UV guide locked on
top, and a crown's cut-out layer; an existing PSD is never replaced). `--preview` is "preview": the open
document (saved or not) exported to a scratch file and rendered on the prop
from the same four views into `documentation/screenshots/handbacks/
<prop>-preview-<time>/`; the PNG, the game and her document are untouched.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from optimize_png import optimize  # noqa: E402

BLENDER = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
GODOT = os.environ.get("GODOT", "/Applications/Godot.app/Contents/MacOS/Godot")
# ground_contact_test's standing failures, by the name of the surface a guest
# was found in or over, as of 2026-09-25 (that day's journal has the census).
# A prop that puts a guest into itself shows up under its own name, not here.
KNOWN_GROUND = (
    # NT-2's slopes: a guest's wander offset slides each leg along itself.
    "wing_", "climb_", "landing_deck", "shelf_deck", "cascade_apron", "(no floor)",
    # The east end: the terraces crowd still walks the pre-rebuild layout.
    "east_", "hill_", "crest_court", "junction_j9", "route_f", "embankment_route_f",
    "R10_", "terrain_T2",
    # The boardwalk crowd through the Grand Circuit lane, and one plaza bin
    # (a generated cylinder until 2026-09-27, `bin_1_lid`; now the placed prop).
    "grand_tram_boardwalk_", "lane_cart", "bin_1/",
)


# A prop's own tests, run in place of seat_test.py, which is for seats. The
# palm crown and trunk are on all 34 coastal palms and the two catalog palms.
PROP_TESTS = {
    "palm_crown": ("coastal_palm_test", "tree_catalog_test", "coastal_plant_catalog_test"),
    "palm_trunk": ("coastal_palm_test", "tree_catalog_test", "coastal_plant_catalog_test"),
    "fern_fan": ("coastal_palm_test", "coastal_plant_catalog_test"),
    "hakone_grass": ("coastal_palm_test", "coastal_plant_catalog_test"),
    "purple_heart_sprig": ("coastal_palm_test", "coastal_plant_catalog_test"),
}


class Stop(Exception):
    pass


class Report:
    def __init__(self, prop):
        self.prop, self.lines = prop, []

    def say(self, ok, step, detail):
        mark = {True: "ok  ", False: "FAIL", None: "note"}[ok]
        line = f"{mark} {step}: {detail}"
        self.lines.append(line)
        print(line, flush=True)
        if ok is False:
            raise Stop(line)


def run(cmd, timeout=600):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def same_pixels(a, b):
    with Image.open(a) as x, Image.open(b) as y:
        return x.size == y.size and x.convert("RGBA").tobytes() == y.convert("RGBA").tobytes()


def export(r, psd, png, allow_unsaved):
    jsx = os.path.join(ROOT, "tools", "photoshop", "export_canvas.jsx")
    script = (f'tell application id "com.adobe.Photoshop" to do javascript file (POSIX file "{jsx}") '
              f'with arguments {{"{psd}", "{png}", "{1 if allow_unsaved else 0}"}}')
    before = os.path.getmtime(png) if os.path.exists(png) else 0
    out = run(["osascript", "-e", script], timeout=300)
    said = (out.stdout + out.stderr).strip()
    if not said.startswith("EXPORTED") or os.path.getmtime(png) <= before:
        r.say(False, "export", said or "Photoshop gave no answer")
    with Image.open(png) as im:
        r.say(True, "export", f"{said[len('EXPORTED '):]} -> {os.path.relpath(png, ROOT)} ({im.size[0]}x{im.size[1]})")


def holes(r, png, textures):
    """The cut-out back into an exported colour PNG's alpha (the PSD's flattened
    export has none): a crown's painted cut-out, which the export has just
    written from the PSD's "cut-out" layer beside the PNG (or the canvas's own,
    before there is a PSD), or a perforated prop's holes; nothing for a prop
    with neither."""
    stem = os.path.basename(png)[:-len("_colour.png")]
    found = [m for m in (png.replace("_colour.png", "_cutout.png"),
                         os.path.join(textures, f"{stem}_cutout.png"),
                         os.path.join(textures, f"{stem}_holes.png")) if os.path.exists(m)]
    if not found:
        return
    holes_png = found[0]
    out = run([BLENDER, "--background", "--factory-startup", "--python",
               os.path.join(ROOT, "tools", "blender", "apply_holes.py"), "--", png, holes_png])
    said = next((l[len("apply_holes: "):] for l in out.stdout.splitlines() if l.startswith("apply_holes: ")), None)
    r.say(bool(said) and not said.startswith("FAIL"), "holes", said or out.stderr[-300:])


def send(r, blend):
    if run(["pgrep", "-x", "Blender"]).returncode == 0:
        r.say(None, "send", "Blender is open: this sends the file as saved on disk")
    out = run([BLENDER, "--background", blend, "--python",
               os.path.join(ROOT, "tools", "blender", "prop_handback_blender.py"), "--", "send"])
    said = [l[len("HANDBACK send "):] for l in out.stdout.splitlines() if l.startswith("HANDBACK send ")]
    r.say("ok" in said, "send", "; ".join(s for s in said if s not in ("ok", "failed")) or out.stderr[-300:])


def godot_import(r):
    out = run([GODOT, "--headless", "--path", ROOT, "--import"], timeout=900)
    errors = [l for l in out.stdout.splitlines() + out.stderr.splitlines() if "ERROR" in l]
    r.say(not errors, "import", "Godot imported the project" if not errors else errors[0])


def verify(r, prop, sources):
    fixed = False
    for src in sources:
        kind = src.rsplit("_", 1)[-1]  # colour.png, orm.png, normal.png
        copy = os.path.join(ROOT, "assets", "props", f"{prop}_{prop}_{kind}")
        if not os.path.exists(copy):
            r.say(False, "verify", f"Godot did not extract {os.path.relpath(copy, ROOT)}")
        if not same_pixels(src, copy):
            r.say(False, "verify", f"{os.path.relpath(copy, ROOT)} differs from {os.path.basename(src)}")
        settings = copy + ".import"
        text = open(settings).read()
        if "compress/mode=2" not in text or "mipmaps/generate=true" not in text:
            text = re.sub(r"^compress/mode=\d+$", "compress/mode=2", text, flags=re.M)
            text = re.sub(r"^mipmaps/generate=\w+$", "mipmaps/generate=true", text, flags=re.M)
            text = re.sub(r"^detect_3d/compress_to=\d+$", "detect_3d/compress_to=0", text, flags=re.M)
            open(settings, "w").write(text)
            fixed = True
        msg = optimize(copy)
        r.say(True, "verify", f"{os.path.basename(copy)} matches pixel for pixel; {msg.split(': ', 1)[-1]}")
    if fixed:
        r.say(None, "verify", "set VRAM compression and mipmaps on the extracted textures; importing again")
        godot_import(r)


def tests(r, prop):
    own = PROP_TESTS.get(prop)
    if own is None:
        out = run([sys.executable, os.path.join(ROOT, "tools", "seat_test.py")])
        last = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-200:]
        r.say(last.startswith("PASS"), "seat_test", last)
    for name in own or ():
        out = run([GODOT, "--headless", "--fixed-fps", "60", "--path", ROOT, "tools/run.tscn", "--", name])
        verdict = next((l for l in out.stdout.splitlines() if l.startswith(("PASS", "FAIL"))),
                       (out.stdout + out.stderr)[-300:])
        r.say(out.returncode == 0 and verdict.startswith("PASS"), name, verdict[:160])

    out = run([GODOT, "--headless", "--path", ROOT, "--script", "res://tools/clearance_test.gd"])
    pairs = re.search(r"--- (\d+) pairs of (\d+) assemblies ---", out.stdout)
    r.say(bool(pairs) and pairs.group(1) == "0", "clearance_test",
          f"{pairs.group(1)} pairs of {pairs.group(2)} assemblies" if pairs else out.stdout[-300:])

    out = run([GODOT, "--headless", "--fixed-fps", "60", "--path", ROOT, "tools/run.tscn", "--", "budget_test"])
    verdict = next((l for l in out.stdout.splitlines() if l.startswith(("PASS", "FAIL"))), out.stdout[-300:])
    r.say(verdict.startswith("PASS"), "budget_test", verdict)

    out = run([GODOT, "--headless", "--fixed-fps", "60", "--path", ROOT, "tools/run.tscn", "--", "ground_contact_test"])
    # One line per failing surface: "FAIL: <n> samples on <surface>, gap ...".
    surfaces = {}
    for line in out.stdout.splitlines():
        m = re.match(r"FAIL: (\d+) samples on (.+?), gap", line)
        if m:
            surfaces[m.group(2)] = int(m.group(1))
    passed = any(l.startswith("PASS") for l in out.stdout.splitlines())
    unknown = {k: v for k, v in surfaces.items() if not k.startswith(KNOWN_GROUND)}
    if surfaces:
        r.say(not unknown, "ground_contact_test",
              f"only known standing failures ({len(surfaces)} surfaces)" if not unknown
              else f"new failures: {unknown}")
    else:
        r.say(passed, "ground_contact_test", "PASS" if passed else out.stdout[-300:])


def open_canvas(r, colour, guide, psd):
    with Image.open(guide) as g:
        box = g.getchannel("A").getbbox() or (0, 0, 0, 0)
    jsx = os.path.join(ROOT, "tools", "photoshop", "open_canvas.jsx")
    script = (f'tell application id "com.adobe.Photoshop"\nactivate\n'
              f'do javascript file (POSIX file "{jsx}") with arguments '
              f'{{"{colour}", "{guide}", "{psd}", "{box[0]}", "{box[1]}"}}\nend tell')
    out = run(["osascript", "-e", script], timeout=300)
    said = (out.stdout + out.stderr).strip()
    if said.startswith("CREATED") and f"at {box[0]},{box[1]}" not in said:
        r.say(False, "open", f"{said}; the guide should be at {box[0]},{box[1]}")
    r.say(said.startswith(("CREATED", "OPEN")), "open", said or "Photoshop gave no answer")
    if said.startswith("CREATED"):
        hole_layers(r, colour, psd, save=True)
        cutout_layers(r, colour, psd)


def cutout_layers(r, colour, psd):
    """A crown's new PSD gets its cut-out (`tools/photoshop/cutout_layers.jsx`):
    the canvas colour, opaque, under the paint, and the canvas's own
    `<prop>_cutout.png` as a "cut-out" layer at Multiply above it, which she
    paints and every export writes back. Nothing for a prop without one."""
    cutout_png = colour.replace("_colour.png", "_cutout.png")
    if not os.path.exists(cutout_png):
        return
    under = os.path.join(tempfile.mkdtemp(prefix="kyt_cutout_"), "underlay.png")
    with Image.open(colour) as im:
        im.convert("RGB").save(under)
    jsx = os.path.join(ROOT, "tools", "photoshop", "cutout_layers.jsx")
    script = (f'tell application id "com.adobe.Photoshop" to do javascript file (POSIX file "{jsx}") '
              f'with arguments {{"{psd}", "{under}", "{cutout_png}"}}')
    out = run(["osascript", "-e", script], timeout=300)
    said = (out.stdout + out.stderr).strip()
    r.say(said.startswith(("LAYERS", "KEPT")), "cut-out layers", said or "Photoshop gave no answer")


def cutout_layer(r, psd, cutout_png):
    """Replaces the pixels of the PSD's cut-out layer with `<prop>_cutout.png`
    (made again by `paint_canvas.py --leaflets --cutout-only`), keeping the
    layer's name, place and blend mode, and doesn't save: she looks at the
    leaflets in Photoshop and saves them, or takes them back with its history."""
    jsx = os.path.join(ROOT, "tools", "photoshop", "cutout_layers.jsx")
    script = (f'tell application id "com.adobe.Photoshop" to do javascript file (POSIX file "{jsx}") '
              f'with arguments {{"{psd}", "", "{cutout_png}", "replace"}}')
    out = run(["osascript", "-e", script], timeout=300)
    said = (out.stdout + out.stderr).strip()
    r.say(said.startswith("REPLACED"), "cut-out layer", said or "Photoshop gave no answer")


def shading_layer(r, psd, shading_png):
    """Puts a crown's painted starting look (`paint_canvas.py --leaflets
    --shading-only`) into its PSD as "shading (Claude)", directly above her
    `paint` layer, replacing an earlier one, and doesn't save: she can hide it,
    paint over it or delete it."""
    jsx = os.path.join(ROOT, "tools", "photoshop", "layer_from_png.jsx")
    script = (f'tell application id "com.adobe.Photoshop" to do javascript file (POSIX file "{jsx}") '
              f'with arguments {{"{psd}", "{shading_png}", "shading (Claude)", "paint"}}')
    out = run(["osascript", "-e", script], timeout=300)
    said = (out.stdout + out.stderr).strip()
    r.say(said.startswith(("ADDED", "REPLACED")), "shading layer", said or "Photoshop gave no answer")


def base_layer(r, psd, png, kind):
    """Puts `<prop>_<kind>_base.png` (`paint_canvas.py --leaflets --base-fade`)
    into the PSD as "<kind> base (Claude)" at Color blend, above "shading
    (Claude)" if there is one and otherwise above `paint`, and doesn't save."""
    with Image.open(psd) as doc:
        names = [layer[0] for layer in getattr(doc, "layers", [])]
    above = "shading (Claude)" if "shading (Claude)" in names else "paint"
    jsx = os.path.join(ROOT, "tools", "photoshop", "layer_from_png.jsx")
    script = (f'tell application id "com.adobe.Photoshop" to do javascript file (POSIX file "{jsx}") '
              f'with arguments {{"{psd}", "{png}", "{kind} base (Claude)", "{above}", "COLORBLEND"}}')
    out = run(["osascript", "-e", script], timeout=300)
    said = (out.stdout + out.stderr).strip()
    r.say(said.startswith(("ADDED", "REPLACED")), "base layer", said or "Photoshop gave no answer")


def spread_into_gaps(rgba, fallback, reach=24):
    """`rgba` (h, w, 4) with its see-through pixels given the colours of the
    opaque ones beside them, spread up to `reach` pixels in; anything still
    unreached takes `fallback` (h, w, 3). Returns opaque RGB, uint8."""
    import numpy as np
    have = rgba[..., 3] >= 255
    col = np.where(have[..., None], rgba[..., :3].astype(np.float32), 0.0)
    for _ in range(reach):
        if have.all():
            break
        acc = np.zeros_like(col)
        cnt = np.zeros(have.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            sh = np.roll(np.roll(have, dy, 0), dx, 1)
            acc += np.roll(np.roll(col, dy, 0), dx, 1) * sh[..., None]
            cnt += sh
        new = ~have & (cnt > 0)
        col[new] = acc[new] / cnt[new][:, None]
        have |= new
    col[~have] = fallback[~have]
    return np.clip(col + 0.5, 0, 255).astype(np.uint8)


def paint_underlay(r, colour, psd, out):
    """The "metal under the holes (Claude)" layer's pixels, into `out`: her
    `paint` layer's own colours spread into its see-through spots, the canvas
    colour where there is no paint to spread. A PSD made before the holes were
    cut again keeps the old holes as see-through spots in her paint; under the
    plain canvas colour they showed as marks of the old holes (the street
    bin's old quatrefoils, grey plus signs through her green, 2026-09-27).
    Returns whether it came from her paint."""
    import numpy as np
    with Image.open(colour) as im:
        canvas = np.asarray(im.convert("RGB"))
    work = tempfile.mkdtemp(prefix="kyt_paint_")
    paint_png = os.path.join(work, "paint.png")
    said = ""
    if os.path.exists(psd):
        jsx = os.path.join(ROOT, "tools", "photoshop", "layer_export.jsx")
        script = (f'tell application id "com.adobe.Photoshop" to do javascript file (POSIX file "{jsx}") '
                  f'with arguments {{"{psd}", "{paint_png}", "paint"}}')
        out_ = run(["osascript", "-e", script], timeout=300)
        said = (out_.stdout + out_.stderr).strip()
    if said.startswith("LAYER") and os.path.exists(paint_png):
        with Image.open(paint_png) as p:
            paint = np.asarray(p.convert("RGBA"))
        if paint.shape[:2] == canvas.shape[:2]:
            Image.fromarray(spread_into_gaps(paint, canvas)).save(out)
            return True
    Image.fromarray(canvas).save(out)
    return False


def hole_layers(r, colour, psd, save=False):
    """A perforated prop's PSD gets (or has refreshed) its two hole layers
    (`tools/photoshop/hole_layers.jsx`): opaque, under the paint, the paint's
    own colours spread into its see-through spots (`paint_underlay`; the
    canvas colour where there is none), so a see-through spot exports as the
    metal round it and the holes can be cut again without the painting going
    white or keeping marks of the old holes; and the holes, translucent, on
    top as a locked "UV guide: holes (Claude)". Nothing for a prop without
    holes. A new PSD is saved with them; an existing one is left for her."""
    holes_png = colour.replace("_colour.png", "_holes.png")
    if not os.path.exists(holes_png):
        return
    work = tempfile.mkdtemp(prefix="kyt_holes_")
    under, guide = os.path.join(work, "underlay.png"), os.path.join(work, "holes_guide.png")
    from_paint = paint_underlay(r, colour, psd, under)
    with Image.open(holes_png) as h:
        metal = h.convert("L")
    alpha = metal.point(lambda v: (255 - v) * 110 // 255)
    Image.merge("RGBA", (Image.new("L", metal.size, 255), Image.new("L", metal.size, 0),
                         Image.new("L", metal.size, 255), alpha)).save(guide)
    jsx = os.path.join(ROOT, "tools", "photoshop", "hole_layers.jsx")
    script = (f'tell application id "com.adobe.Photoshop" to do javascript file (POSIX file "{jsx}") '
              f'with arguments {{"{psd}", "{under}", "{guide}", "{"save" if save else "nosave"}"}}')
    out = run(["osascript", "-e", script], timeout=300)
    said = (out.stdout + out.stderr).strip()
    r.say(said.startswith("LAYERS"), "hole layers", (said or "Photoshop gave no answer")
          + ("; under the paint: her paint spread into its see-through spots" if from_paint
             else "; under the paint: the canvas colour"))


def renders(r, blend, folder, colour=None):
    extra = ["--colour", colour] if colour else []
    out = run([BLENDER, "--background", blend, "--python",
               os.path.join(ROOT, "tools", "blender", "prop_handback_blender.py"), "--", "render", folder] + extra)
    shots = [l.split()[-1] for l in out.stdout.splitlines() if l.startswith("HANDBACK render")]
    r.say(len(shots) == 4, "renders", f"{len(shots)} views in {os.path.relpath(folder, ROOT)}")


def main():
    ap = argparse.ArgumentParser(description="One hand-back for a painted prop.")
    ap.add_argument("prop")
    ap.add_argument("--no-export", action="store_true", help="the PNG was exported by hand")
    ap.add_argument("--allow-unsaved", action="store_true", help="export even if the PSD has unsaved changes")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--no-renders", action="store_true")
    ap.add_argument("--open", action="store_true", help="open (or make) the canvas PSD in Photoshop")
    ap.add_argument("--preview", action="store_true", help="render the work in progress; nothing sent")
    ap.add_argument("--hole-layers", action="store_true",
                    help="refresh a perforated prop's hole layers in its PSD after the holes are cut again")
    ap.add_argument("--cutout-layer", action="store_true",
                    help="put a crown's re-cut <prop>_cutout.png into its PSD's cut-out layer, unsaved")
    ap.add_argument("--base-layer", metavar="KIND",
                    help="put a crown's <prop>_<kind>_base.png into its PSD at Color blend, unsaved")
    ap.add_argument("--shading-layer", action="store_true",
                    help="put a crown's <prop>_shading.png into its PSD as 'shading (Claude)', unsaved")
    args = ap.parse_args()
    prop = args.prop
    textures = os.path.join(ROOT, "assets", "source", "textures", prop)
    psd = os.path.join(textures, f"{prop}_colour.psd")
    colour = os.path.join(textures, f"{prop}_colour.png")
    orm = os.path.join(textures, f"{prop}_orm.png")
    blend = os.path.join(ROOT, "assets", "source", "props", f"{prop}.blend")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    folder = os.path.join(ROOT, "documentation", "screenshots", "handbacks", f"{prop}-{stamp}")
    r = Report(prop)
    ok = True
    if args.base_layer:
        try:
            base_layer(r, psd, os.path.join(textures, f"{prop}_{args.base_layer}_base.png"), args.base_layer)
            print("Base layer in the PSD, not saved: look, and save it if it's right.")
        except Stop:
            sys.exit(1)
        sys.exit(0)
    if args.shading_layer:
        try:
            shading_layer(r, psd, os.path.join(textures, f"{prop}_shading.png"))
            print("Shading layer in the PSD above her paint, not saved: look, and save it if it's right.")
        except Stop:
            sys.exit(1)
        sys.exit(0)
    if args.cutout_layer:
        try:
            cutout_layer(r, psd, os.path.join(textures, f"{prop}_cutout.png"))
            print("Cut-out layer replaced in the PSD, not saved: look, and save it if it's right.")
        except Stop:
            sys.exit(1)
        sys.exit(0)
    if args.hole_layers:
        try:
            hole_layers(r, colour, psd)
            print("Hole layers refreshed in the PSD; she saves it.")
        except Stop:
            sys.exit(1)
        sys.exit(0)
    if args.open or args.preview:
        try:
            if args.open:
                open_canvas(r, colour, os.path.join(textures, f"{prop}_uv_guide.png"), psd)
                print("Canvas open in Photoshop: paint, save, and say \"handed back\".")
            else:
                folder = folder.replace(f"{prop}-{stamp}", f"{prop}-preview-{stamp}")
                scratch = os.path.join(tempfile.mkdtemp(prefix="kyt_preview_"), f"{prop}_colour.png")
                export(r, psd, scratch, allow_unsaved=True)
                holes(r, scratch, textures)
                renders(r, blend, folder, colour=scratch)
                with open(os.path.join(folder, "README.md"), "w") as f:
                    f.write(f"# Preview: {prop}, {stamp}\n\nWork in progress from the open PSD; nothing sent.\n\n"
                            + "\n".join(f"- {l}" for l in r.lines) + "\n")
                print(f"Preview: {os.path.relpath(folder, ROOT)}")
        except Stop:
            sys.exit(1)
        sys.exit(0)
    try:
        if not os.path.exists(blend):
            r.say(False, "prop", f"no {os.path.relpath(blend, ROOT)}")
        if args.no_export or not os.path.exists(psd):
            r.say(None, "export", "skipped" if args.no_export else "no PSD; using the PNG as it is")
        else:
            export(r, psd, colour, args.allow_unsaved)
        holes(r, colour, textures)
        normal = os.path.join(textures, f"{prop}_normal.png")
        if os.path.exists(os.path.join(textures, f"{prop}_bump.png")):
            out = run([sys.executable, os.path.join(ROOT, "tools", "bump_to_normal.py"), prop])
            said = next((l[len("bump_to_normal: "):] for l in out.stdout.splitlines()
                         if l.startswith("bump_to_normal: ")), None)
            r.say(bool(said), "normal", said or out.stderr[-300:])
        for png in (colour, orm, normal):
            if os.path.exists(png):
                r.say(True, "shrink", optimize(png).split(": ", 1)[-1] + f" ({os.path.basename(png)})")
        send(r, blend)
        godot_import(r)
        verify(r, prop, [p for p in (colour, orm, normal) if os.path.exists(p)])
        if not args.no_tests:
            tests(r, prop)
        if not args.no_renders:
            renders(r, blend, folder)
    except Stop:
        ok = False
    except subprocess.TimeoutExpired as e:
        r.lines.append(f"FAIL timeout: {' '.join(map(str, e.cmd))[:120]}")
        print(r.lines[-1])
        ok = False
    if os.path.isdir(folder):
        with open(os.path.join(folder, "README.md"), "w") as f:
            f.write(f"# Hand-back: {prop}, {stamp}\n\n`python3 tools/prop_handback.py {' '.join(sys.argv[1:])}`\n\n")
            f.write("\n".join(f"- {l}" for l in r.lines) + "\n\n")
            f.write("Views: three_quarter, front, back_low, close_top (from the prop's own size).\n")
    print(("Hand-back complete: nothing committed." if ok else "Hand-back stopped.") + " "
          + (f"Renders and report: {os.path.relpath(folder, ROOT)}" if os.path.isdir(folder) else ""))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
