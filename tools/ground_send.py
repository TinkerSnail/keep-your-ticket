#!/usr/bin/env python3
"""Send ground to game: the height grid's files, as they are on disk, into the game.

Stage 3 of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-14). The Blender
panel's **Send ground to game** runs this in the background and shows its lines; it can be run by
hand the same way. Python's standard library only, so Blender's own Python runs it.

    python3 tools/ground_send.py [--blender PATH] [--godot PATH] [--logs DIR] [--import-lock DIR] [--no-follow]

The chain, in order, stopping at the first step that fails:

1. **build**: the tiles whose heights changed since they were last built (their EXR's hash in
   `assets/source/world_ground/height/` against the one `assets/world_ground/tiles/manifest.json`
   recorded), by `tools/blender/ground_build.py --tiles ...`, which adds any neighbour whose shared
   edge changed with them. Skipped when no tile's heights changed.
2. **follow**: what stands on the ground follows it, `tools/ground_follow.py --pending` (the range's
   rocks, the city's blocks, the gull roosts; it re-exports a source it moved something in). First,
   a follow of an edit that has since been undone in the grid is put back (`--undo <its id>`), so
   Undo last ground edit and a Send take the edit out of the game whole. Skipped with `--no-follow`,
   or when the tool isn't there.
3. **import**: `Godot --headless --import`, so Godot has the new tile GLBs (and any re-exported
   source's).
4. **mount**: `tools/ground_mount.gd` (each tile's colour texture and `scenes/world/world_ground.tscn`;
   a run that changes nothing writes nothing), then its `--check` on what is written.
5. **delta**: `tools/world_terrain_delta.gd`, what the generator will follow; its summary is shown.
6. **generate**: `tools/gen_props.gd`, then `tools/gen_crowd.gd`. Like any generator run, this
   publishes every uncommitted change in the tree into the generated scenes.
7. **seam** (Stage 6, 2026-10-15): the generator cuts the road corridor's sides to the grid's
   ground, so an edit beside or across a road moves the corridor's edges, and the tiles the build
   stitched to the old edges are built again against the new (`ground_build.py` over every tile,
   which rebuilds only those whose held edges changed), then imported and mounted again. Skipped
   when no tile needed it.

It prints `step <name>: ...` as a step starts and `ok <name>: ...` or `FAIL <name>: ...` as it ends,
and `note ...` for what is worth reading; the panel shows those. A Godot step fails on a non-zero
exit, on a script or parse error in its output, or when its own last word is missing; one that
stops printing to its log for the step's time limit is stopped. Each step's whole output is in the
logs folder, named at the end (default: a new folder under the system's temporary folder).

`--import-lock DIR` takes a `mkdir` lock around the import, waiting for it (for agents sharing the
tree, whose sessions keep one); the panel does not pass it.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "assets", "source", "world_ground")
TILES = os.path.join(ROOT, "assets", "world_ground", "tiles")
GODOT = os.environ.get("GODOT", "/Applications/Godot.app/Contents/MacOS/Godot")
BLENDER = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")

## Seconds a step may run, and may go without writing to its log, before it is stopped. gen_props
## takes about six minutes (2026-10-13); the build about two for all fifty tiles.
LIMITS = {"build": (1800, 900), "follow": (2400, 1200), "follow_undo": (2400, 1200), "import": (1800, 900), "mount": (900, 600), "check": (900, 600),
          "delta": (600, 300), "gen_props": (2400, 900), "gen_crowd": (900, 600)}
ERRORS = ("SCRIPT ERROR", "Parse Error", "Failed to load script")


def say(*a):
    print(*a, flush=True)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def clock(seconds):
    return "%d:%02d" % (seconds // 60, seconds % 60)


class Failed(Exception):
    pass


def changed_tiles():
    """Tiles the last build holds whose heights' file has changed since, and the manifest's count."""
    man_path = os.path.join(TILES, "manifest.json")
    if not os.path.exists(man_path):
        raise Failed("build: there is no %s; build every tile once first (ground_build.py)" %
                     os.path.relpath(man_path, ROOT))
    tiles = json.load(open(man_path)).get("tiles", {})
    out = []
    for name in sorted(tiles):
        exr = os.path.join(SOURCE, "height", name + ".exr")
        if os.path.exists(exr) and sha_file(exr) != tiles[name].get("height_sha256"):
            out.append(name)
    return out, len(tiles)


def run(name, cmd, logs, marker=None, errors=True, tag=None):
    """Runs one step's command, its output to `<logs>/<name>.log`; returns that output and the
    seconds it took. Raises Failed with a sentence when it fails: a non-zero exit, a script or
    parse error in its output (unless `errors` is false), or no `marker` in it."""
    limit, quiet = LIMITS[name]
    log = os.path.join(logs, name + ("_" + tag if tag else "") + ".log")
    start = time.time()
    with open(log, "w") as out:
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, env=env)
        last_size, last_change = 0, time.time()
        while proc.poll() is None:
            time.sleep(0.5)
            size = os.path.getsize(log)
            if size != last_size:
                last_size, last_change = size, time.time()
            now = time.time()
            if now - start > limit or now - last_change > quiet:
                proc.kill()
                proc.wait()
                raise Failed("%s: stopped after %s (%s); its log is %s" % (
                    name, clock(now - start), "too long" if now - start > limit else "nothing printed for %s" %
                    clock(now - last_change), log))
    text = open(log, errors="replace").read()
    bad = [l.strip() for l in text.splitlines() if errors and any(e in l for e in ERRORS)]
    if proc.returncode != 0 or bad or (marker and not re.search(marker, text)):
        why = bad[0] if bad else ("exit %d" % proc.returncode if proc.returncode else "it did not finish its work")
        tail = [l for l in text.splitlines() if l.strip()][-2:]
        raise Failed("%s: %s. Last lines: %s. Its log is %s" % (name, why, " / ".join(tail) or "none", log))
    return text, time.time() - start


def follow_signature(e):
    """An edit's identity as `tools/ground_follow.py`'s `signature` gives it (its tiles' hashes
    before and after; ids are reused after an undo). Kept the same as that one."""
    return hashlib.sha256(json.dumps([[f["tile"], f.get("height_sha_before"), f.get("height_sha_after")]
                                      for f in e["files"]]).encode()).hexdigest()[:16]


def undone_follows():
    """The ids of logged follows (`follows.json`) of edits no longer in `edits.json`, newest first."""
    log = os.path.join(SOURCE, "follows.json")
    if not os.path.exists(log):
        return []
    now = {(e["id"], follow_signature(e)) for e in json.load(open(os.path.join(SOURCE, "edits.json")))["edits"]}
    gone = [f["id"] for f in json.load(open(log)).get("follows", [])
            if any((e["id"], e["sig"]) not in now for e in f.get("edits", []))]
    return gone[::-1]


def godot(*args):
    return [GODOT, "--headless", "--path", ROOT] + list(args)


def take_lock(path):
    while True:
        try:
            os.mkdir(path)
            return
        except FileExistsError:
            time.sleep(2)


def main(argv):
    global GODOT
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--blender", default=BLENDER)
    ap.add_argument("--godot", default=GODOT)
    ap.add_argument("--logs", help="where each step's output goes (default: a new temporary folder)")
    ap.add_argument("--import-lock", help="a directory to mkdir as a lock around the import")
    ap.add_argument("--no-follow", action="store_true", help="skip ground_follow.py")
    a = ap.parse_args(argv)
    GODOT = a.godot
    for exe, what in ((a.blender, "Blender"), (GODOT, "Godot")):
        if not os.path.exists(exe):
            say("FAIL %s is not at %s" % (what, exe))
            return 1
    logs = a.logs or tempfile.mkdtemp(prefix="kyt_ground_send_%s_" % time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(logs, exist_ok=True)
    t0 = time.time()
    try:
        # 1. build
        tiles, held = changed_tiles()
        if tiles:
            say("step build: rebuilding %s (and any neighbour whose shared edge changed)" % ", ".join(tiles))
            text, s = run("build", [a.blender, "--background", "--factory-startup", "--python-exit-code", "1",
                                    "--python", os.path.join(ROOT, "tools", "blender", "ground_build.py"), "--",
                                    "--tiles", ",".join(tiles)], logs, r"ground_build: built \d+ tiles")
            built = sorted(set(re.findall(r"phase 2 (x-?\d+_z-?\d+):", text)))
            say("ok build: %s rebuilt in %s" % (", ".join(built) if built else "no tile needed to be", clock(s)))
        else:
            say("ok build: no tile's heights changed since its last build (%d tiles)" % held)
        # 2. follow
        follow = os.path.join(ROOT, "tools", "ground_follow.py")
        if a.no_follow or not os.path.exists(follow):
            say("ok follow: skipped (%s)" % ("--no-follow" if a.no_follow else "tools/ground_follow.py isn't there"))
        else:
            os.environ["BLENDER"] = a.blender  # ground_follow.py runs its own background Blender
            for fid in undone_follows():
                say("step follow: putting back %s, whose edit was undone" % fid)
                text, s = run("follow_undo", [sys.executable, follow, "--undo", fid], logs, tag=fid)
                say("ok follow: %s put back in %s" % (fid, clock(s)))
            say("step follow: what stands on the ground follows it")
            text, s = run("follow", [sys.executable, follow, "--pending"], logs)
            report = [l.strip() for l in text.splitlines() if l.startswith(("ground_follow", "  "))]
            say("ok follow: %s" % (report[0] if report else "done in %s" % clock(s)))
            for l in report[1:4]:
                say("note " + l)
        # 3. import
        say("step import: Godot imports the tiles")
        if a.import_lock:
            take_lock(a.import_lock)
        try:
            # Only its exit counts: an import reports every script in the project, other
            # sessions' unfinished ones too, and the mount's check proves the tiles imported.
            _, s = run("import", godot("--import"), logs, errors=False)
        finally:
            if a.import_lock:
                shutil.rmtree(a.import_lock, ignore_errors=True)
        say("ok import: %s" % clock(s))
        # 4. mount
        say("step mount: the tiles and their colour into scenes/world/world_ground.tscn")
        text, s = run("mount", godot("--script", "res://tools/ground_mount.gd"), logs, r"ground_mount: \d+ tiles, PASS")
        textures = re.findall(r"wrote res://(\S+\.res)$", text, re.M)
        scene = "unchanged" if "unchanged: res://scenes/world/world_ground.tscn" in text else "written"
        say("ok mount: the scene %s; %s" % (scene, "%d colour texture%s written" % (len(textures), "" if len(textures) == 1 else "s")
                                            if textures else "no colour changed"))
        text, s = run("check", godot("--script", "res://tools/ground_mount.gd", "--", "--check"), logs,
                      r"ground_mount: \d+ tiles, PASS")
        say("ok check: %s" % re.search(r"ground_mount: (\d+ tiles), PASS", text).group(1))
        # 5. delta
        say("step delta: what the generator will follow")
        text, s = run("delta", godot("--script", "res://tools/world_terrain_delta.gd"), logs,
                      r"world_terrain_delta: read")
        summary = [l for l in text.splitlines() if l.startswith("world terrain")]
        say("ok delta: read in %s" % clock(s))
        for l in summary:
            say("note " + l)
        # 6. generate
        say("step generate: gen_props.gd (about six minutes)")
        text, s = run("gen_props", godot("--script", "res://tools/gen_props.gd"), logs, r"wrote \d+ nodes to res://")
        say("ok gen_props: %d scenes written in %s" % (len(re.findall(r"wrote \d+ nodes to res://", text)), clock(s)))
        say("step generate: gen_crowd.gd")
        text, s = run("gen_crowd", godot("--script", "res://tools/gen_crowd.gd"), logs, r"wrote \d+ guests")
        crowds = len(re.findall(r"wrote \d+ guests", text))
        say("ok gen_crowd: %d crowd%s written in %s" % (crowds, "" if crowds == 1 else "s", clock(s)))
        # 7. seam
        say("step seam: the tiles stitched to the road corridor as the generator has just cut it")
        text, s = run("build", [a.blender, "--background", "--factory-startup", "--python-exit-code", "1",
                                "--python", os.path.join(ROOT, "tools", "blender", "ground_build.py")],
                      logs, r"ground_build: built \d+ tiles", tag="seam")
        built = sorted(set(re.findall(r"phase 2 (x-?\d+_z-?\d+):", text)))
        if not built:
            say("ok seam: no tile's seam changed (%s)" % clock(s))
        else:
            say("ok seam: %s rebuilt in %s" % (", ".join(built), clock(s)))
            if a.import_lock:
                take_lock(a.import_lock)
            try:
                _, s = run("import", godot("--import"), logs, errors=False, tag="seam")
            finally:
                if a.import_lock:
                    shutil.rmtree(a.import_lock, ignore_errors=True)
            text, s = run("mount", godot("--script", "res://tools/ground_mount.gd"), logs,
                          r"ground_mount: \d+ tiles, PASS", tag="seam")
            run("check", godot("--script", "res://tools/ground_mount.gd", "--", "--check"), logs,
                r"ground_mount: \d+ tiles, PASS", tag="seam")
            say("ok seam: imported and mounted again")
    except Failed as e:
        say("FAIL " + str(e))
        say("note Logs: " + logs)
        return 1
    say("Ground sent in %s. Godot shows it the next time its window is focused or it starts." % clock(time.time() - t0))
    say("note Logs: " + logs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
