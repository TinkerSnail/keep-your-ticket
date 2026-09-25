#!/usr/bin/env python3
"""One hand-back for a painted prop: from Christina's saved PSD to tested in the game.

    python3 tools/prop_handback.py <prop> [--no-export] [--allow-unsaved] [--no-tests] [--no-renders]
    python3 tools/prop_handback.py <prop> --open      # open (or make) the canvas PSD in Photoshop
    python3 tools/prop_handback.py <prop> --preview   # render her work in progress; nothing sent

Stage 8 of `documentation/prop-pipeline.md`, run in order, stopping at the
first thing that fails:

1. **Export.** `assets/source/textures/<prop>/<prop>_colour.psd` through
   Photoshop (`tools/photoshop/export_canvas.jsx`): a flattened copy, every
   "UV guide" layer hidden, over `<prop>_colour.png`. Refused if the PSD has
   unsaved changes, so the PNG always matches a saved PSD (`--allow-unsaved`
   overrides; `--no-export` skips the step for a PNG exported by hand).
2. **Shrink** the colour and ORM PNGs (`tools/optimize_png.py`: pixel-identical
   or left alone). Blender embeds the PNG's own bytes, so the GLB shrinks too.
3. **Send to game** from the saved `assets/source/props/<prop>.blend`, headless
   (Check first). If Blender is open, unsaved changes there are not included.
4. **Import** in Godot, headless.
5. **Verify** that Godot's extracted copies in `assets/props/` match the PNGs
   pixel for pixel and are VRAM-compressed with mipmaps; the import setting is
   put right (and imported again) if not.
6. **Test:** `seat_test.py`, `clearance_test`, `budget_test`,
   `ground_contact_test` (failing only on the known east-wing ramps counts as
   passing).
7. **Render** the prop from four views into
   `documentation/screenshots/handbacks/<prop>-<time>/`, with this report as
   its README.

It never commits: that is Christina's word. Mac only (Photoshop through
AppleScript). Set BLENDER or GODOT to use other binaries.

`--open` is stage 6's set-up: the prop's PSD opened in Photoshop, made first
if there isn't one (colour PNG as the `paint` layer, the UV guide locked on
top; an existing PSD is never replaced). `--preview` is "preview": the open
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
# ground_contact_test has failed on the east wing's ramps since 2026-09-10.
KNOWN_GROUND = ("wing_",)


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
        kind = src.rsplit("_", 1)[-1]  # colour.png, orm.png
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


def tests(r):
    out = run([sys.executable, os.path.join(ROOT, "tools", "seat_test.py")])
    last = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-200:]
    r.say(last.startswith("PASS"), "seat_test", last)

    out = run([GODOT, "--headless", "--path", ROOT, "--script", "res://tools/clearance_test.gd"])
    pairs = re.search(r"--- (\d+) pairs of (\d+) assemblies ---", out.stdout)
    r.say(bool(pairs) and pairs.group(1) == "0", "clearance_test",
          f"{pairs.group(1)} pairs of {pairs.group(2)} assemblies" if pairs else out.stdout[-300:])

    out = run([GODOT, "--headless", "--fixed-fps", "60", "--path", ROOT, "tools/run.tscn", "--", "budget_test"])
    verdict = next((l for l in out.stdout.splitlines() if l.startswith(("PASS", "FAIL"))), out.stdout[-300:])
    r.say(verdict.startswith("PASS"), "budget_test", verdict)

    out = run([GODOT, "--headless", "--fixed-fps", "60", "--path", ROOT, "tools/run.tscn", "--", "ground_contact_test"])
    surfaces = {}
    for line in out.stdout.splitlines():
        m = re.search(r"from (\S+) at", line)
        if line.startswith("FAIL") and m:
            name = re.sub(r"_\d+$", "", m.group(1))
            surfaces[name] = surfaces.get(name, 0) + 1
    unknown = {k: v for k, v in surfaces.items() if not k.startswith(KNOWN_GROUND)}
    r.say(not unknown, "ground_contact_test",
          "only the known east-wing ramps" if surfaces and not unknown
          else ("PASS" if not surfaces else f"new failures: {unknown}"))


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
    if args.open or args.preview:
        try:
            if args.open:
                open_canvas(r, colour, os.path.join(textures, f"{prop}_uv_guide.png"), psd)
                print("Canvas open in Photoshop: paint, save, and say \"handed back\".")
            else:
                folder = folder.replace(f"{prop}-{stamp}", f"{prop}-preview-{stamp}")
                scratch = os.path.join(tempfile.mkdtemp(prefix="kyt_preview_"), f"{prop}_colour.png")
                export(r, psd, scratch, allow_unsaved=True)
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
        for png in (colour, orm):
            if os.path.exists(png):
                r.say(True, "shrink", optimize(png).split(": ", 1)[-1] + f" ({os.path.basename(png)})")
        send(r, blend)
        godot_import(r)
        verify(r, prop, [p for p in (colour, orm) if os.path.exists(p)])
        if not args.no_tests:
            tests(r)
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
