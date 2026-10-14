#!/usr/bin/env python3
"""What stands on the ground follows it when it changes (height-grid plan, Stage 3, 2026-10-14).

    python3 tools/ground_follow.py --pending [--dry] [--only rocks,city,roosts] [--no-export]
    python3 tools/ground_follow.py --edit G8 [G9 ...] [--dry] ...
    python3 tools/ground_follow.py --since <commit> [--dry] ...
    python3 tools/ground_follow.py --before <height dir> [--after <height dir>] --id <name> [--dry] ...
    python3 tools/ground_follow.py --undo <id> [--dry] [--no-export]
    python3 tools/ground_follow.py --settle <G1 ... | id> [--why LINE] [--dry]
    python3 tools/ground_follow.py --list
    (each takes --root DIR: another copy of assets/source/world_ground, its follows.json with it)

The ground is the height grid, `assets/source/world_ground/height/`, read as its bilinear surface:
the source she edits, from which the tile meshes are built. Its change is taken node by node, after
less before, and is exactly zero wherever no node changed; a node with no ground before or after
changes by zero, as `WorldTerrainSource._grid_delta` reads it (without its held-outline sides:
nothing that follows stands on the corridor or the lids). The tiles are rebuilt from the grid and
re-triangulate whole tiles, within their zone's tolerance (`grid.json`), so measured on them a
follow would move things she never edited by the mesh's own error.

Before and after:
- `--pending`: every edit in `edits.json` (the grid's named edits, the panel's saves, the
  Photoshop paints) that no follow has followed yet; an edit is known by its tiles' hashes, since
  an id is reused after an undo, and a followed edit that has left the log (undone in the grid)
  stops it until its follow is undone. What "Send ground to game" runs.
- `--edit G8 [G9 ...]`: the change those grid edits made, from their `history/G<n>.npz` (each
  edit's new heights less its old, summed), whatever happened since.
- `--since <commit>`: the tiles at that commit (`git cat-file --filters`, through LFS) against the
  working tree's; only tiles whose bytes differ are read.
- `--before DIR [--after DIR]`: two folders of height tiles (after defaults to the tree's).

What follows, each by its own script, run with background Blender on its source and saved only
when something moved:
- **rocks**: `tools/blender/range_rocks_on_ground.py` on
  `assets/source/range_forest_distinct_background.blend`. Each rock in the four rock collections
  keeps its sink depth: it moves up or down by the ground's change under its foot, its lowest
  vertex, where the floater census measures it.
- **city**: `tools/blender/city_blocks_on_ground.py` on
  `assets/source/far_shore_city_relocation.blend`. Each block, skyline tower and the ferry
  terminal rises with the lowest ground under its footprint, and is only ever raised (a tower's
  glass with it); where the ground fell under one it stays, and the report names it.
- **roosts**: the gull roosts in `scenes/wildlife/wildlife.tscn`, y by the change under the
  marker, and every bird standing at a roost's position with it; only those `position` lines are
  rewritten.
Not followers: roads, earthworks, the bridge, the ferry landings (they keep the water), the
merged canopy, the lakes, and the generator's output, which follows the grid through `delta_y`
when the park is regenerated.

Each follow has an id (the edits', `G8` or `G8-G10`; `since_<commit>`; or `--id`): the rocks and
city objects it moved keep how far as a custom property under it, so `--undo <id>` puts back
exactly that follow, in any order; the roosts' moves are in the log,
`assets/source/world_ground/follows.json`, beside `edits.json`. A follow of an id already logged,
or of an edit already followed, is refused. `--settle` records edits (or a seat made by hand, under
an id of its own) as followed without moving anything, for followers put on the ground another way:
G1-G7 and the `stage2` seat, when the game first stood on the grid. After saving a source it re-exports its GLB with `tools/export_world_source.sh`
(`--no-export` to skip); Godot imports it at its next start or `Godot --headless --path . --import`.
It prints a short report and writes it to `--report FILE` when given.

Needs numpy (the system's python3 or Blender's own). The module is also the grid reader the two
Blender scripts import (`Change`, `Heights`).
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ground_bake as gb  # noqa: E402  (its EXR reader)

GROUND = os.path.join(ROOT, "assets", "source", "world_ground")
HEIGHT = os.path.join(GROUND, "height")
LOG = os.path.join(GROUND, "follows.json")
RANGE = os.path.join(ROOT, "assets", "source", "range_forest_distinct_background.blend")
CITY = os.path.join(ROOT, "assets", "source", "far_shore_city_relocation.blend")
WILDLIFE = os.path.join(ROOT, "scenes", "wildlife", "wildlife.tscn")
ROCKS_PY = os.path.join(HERE, "blender", "range_rocks_on_ground.py")
CITY_PY = os.path.join(HERE, "blender", "city_blocks_on_ground.py")
EXPORT = os.path.join(HERE, "export_world_source.sh")
BLENDER = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
# A roost moves when the ground under it moves by more than this (wildlife_test allows 0 to 0.2 m).
ROOST_MIN = 0.001


# --- the grid -----------------------------------------------------------------

class Spec:
    """`grid.json`'s lattice: tiles of `n` nodes a side sharing their edges, every `step` metres."""

    def __init__(self, root=None):
        g = json.load(open(os.path.join(root or GROUND, "grid.json")))
        self.step = float(g["spacing_m"])
        self.n = int(g["tile_samples"])
        self.per = self.n - 1
        self.tile_m = float(g["tile_m"])
        self.tx = list(range(g["tiles_x"][0], g["tiles_x"][1] + 1))
        self.tz = list(range(g["tiles_z"][0], g["tiles_z"][1] + 1))
        self.x0 = self.tile_m * self.tx[0]
        self.z0 = self.tile_m * self.tz[0]
        self.cols = self.per * len(self.tx)
        self.rows = self.per * len(self.tz)

    def keys(self):
        return ["x%d_z%d" % (tx, tz) for tz in self.tz for tx in self.tx]

    def cells(self, x, z):
        """For world points (Godot x, z; arrays): tile key index arrays and the cell's local column,
        row and fractions, or valid = False outside the grid. The domain's last row and column
        belong to the cell before them, at weight 1, as in `_grid_delta`."""
        x = np.asarray(x, np.float64)
        z = np.asarray(z, np.float64)
        gx = (x - self.x0) / self.step
        gz = (z - self.z0) / self.step
        valid = (gx >= 0) & (gz >= 0) & (gx <= self.cols) & (gz <= self.rows)
        c = np.minimum(np.floor(np.where(valid, gx, 0)).astype(np.int64), self.cols - 1)
        r = np.minimum(np.floor(np.where(valid, gz, 0)).astype(np.int64), self.rows - 1)
        ti, tj = c // self.per, r // self.per
        return valid, ti, tj, c - ti * self.per, r - tj * self.per, gx - c, gz - r

    def key(self, ti, tj):
        return "x%d_z%d" % (self.tx[0] + ti, self.tz[0] + tj)


def _bilinear(spec, tiles, x, z, nan_as_zero):
    """Bilinear over the four nodes round each point, from `tiles` {key: (n, n) array}; a tile not
    there reads `nan_as_zero` ? 0 : NaN."""
    valid, ti, tj, c, r, fx, fz = spec.cells(x, z)
    out = np.full(valid.shape, 0.0 if nan_as_zero else np.nan)
    for (a, b) in set(zip(ti[valid].tolist(), tj[valid].tolist())):
        t = tiles.get(spec.key(a, b))
        if t is None:
            continue
        m = valid & (ti == a) & (tj == b)
        cc, rr = c[m], r[m]
        q00, q10, q01, q11 = t[rr, cc], t[rr, cc + 1], t[rr + 1, cc], t[rr + 1, cc + 1]
        if nan_as_zero:
            q00, q10, q01, q11 = (np.nan_to_num(q, nan=0.0) for q in (q00, q10, q01, q11))
        u, v = fx[m], fz[m]
        out[m] = (q00 * (1 - u) + q10 * u) * (1 - v) + (q01 * (1 - u) + q11 * u) * v
    return out


class Change:
    """The ground's change, after less before, node by node in the tiles that changed (float64,
    zero where either had no ground); `at` is bilinear between nodes."""

    def __init__(self, spec, tiles=None):
        self.spec = spec
        self.tiles = tiles or {}

    def at(self, x, z):
        return _bilinear(self.spec, self.tiles, x, z, True)

    def add(self, key, idx, before, after):
        t = self.tiles.setdefault(key, np.zeros((self.spec.n, self.spec.n), np.float64))
        d = np.asarray(after, np.float64) - np.asarray(before, np.float64)
        t.reshape(-1)[idx] += np.nan_to_num(d, nan=0.0)

    def add_tile(self, key, before, after):
        d = np.nan_to_num(after.astype(np.float64) - before.astype(np.float64), nan=0.0)
        if np.any(d):
            self.tiles[key] = d

    def summary(self):
        nodes, lo, hi = 0, 0.0, 0.0
        for t in self.tiles.values():
            nz = t[t != 0]
            nodes += int(nz.size)
            if nz.size:
                lo, hi = min(lo, float(nz.min())), max(hi, float(nz.max()))
        return {"tiles": sorted(k for k, t in self.tiles.items() if np.any(t)), "nodes": nodes,
                "lowest_m": round(lo, 3), "highest_m": round(hi, 3)}

    def save(self, path):
        np.savez_compressed(path, **{k: v for k, v in self.tiles.items() if np.any(v)})

    @classmethod
    def load(cls, path, spec=None):
        with np.load(path) as f:
            return cls(spec or Spec(), {k: f[k].astype(np.float64) for k in f.files})


class Heights:
    """The grid's heights from a folder of tiles, read when first asked; `at` is bilinear, NaN
    where any of the four nodes has no ground."""

    def __init__(self, folder=None, spec=None):
        self.folder = folder or HEIGHT
        self.spec = spec or Spec()
        self.tiles = {}

    def at(self, x, z):
        valid, ti, tj, *_ = self.spec.cells(x, z)
        for (a, b) in set(zip(ti[valid].tolist(), tj[valid].tolist())):
            k = self.spec.key(a, b)
            if k not in self.tiles:
                p = os.path.join(self.folder, k + ".exr")
                self.tiles[k] = gb.read_exr(p)[0].astype(np.float64) if os.path.exists(p) else None
        return _bilinear(self.spec, {k: v for k, v in self.tiles.items() if v is not None}, x, z, False)


# --- before and after ---------------------------------------------------------

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_log():
    if os.path.exists(LOG):
        return json.load(open(LOG))
    return {"about": "Follows of the height grid by tools/ground_follow.py, in order: what moved with the "
                     "ground, by id. The rocks and city objects keep their own moves as kyt_ground_moved_<id> "
                     "and kyt_ground_raised_<id>; the roosts' and birds' are here. Undo: --undo <id>.",
            "follows": []}


def save_log(log):
    tmp = LOG + ".tmp"
    with open(tmp, "w") as f:
        json.dump(log, f, indent=1)
        f.write("\n")
    os.replace(tmp, LOG)


def edit_log():
    return json.load(open(os.path.join(GROUND, "edits.json")))["edits"]


def signature(e):
    """An edit's identity: its tiles' hashes before and after. Ids are reused after an undo."""
    return hashlib.sha256(json.dumps([[f["tile"], f["height_sha_before"], f["height_sha_after"]]
                                      for f in e["files"]]).encode()).hexdigest()[:16]


def followed_edits(log):
    return {(e["id"], e["sig"]) for f in log["follows"] for e in f.get("edits", [])}


def pending(log):
    """The logged grid edits no follow has followed yet, in order; refuses when a followed edit has
    left edits.json (undone in the grid), whose follow must be undone first."""
    edits = edit_log()
    now = {(e["id"], signature(e)) for e in edits}
    gone = sorted(i for i, sig in followed_edits(log) if (i, sig) not in now)
    if gone:
        raise SystemExit("ground_follow: %s was followed but is no longer in edits.json (undone?): "
                         "ground_follow.py --undo it first" % ", ".join(gone))
    done = followed_edits(log)
    return [e["id"] for e in edits if (e["id"], signature(e)) not in done]


def change_from_edits(ids, spec):
    edits = {e["id"]: e for e in edit_log()}
    ch = Change(spec)
    for gid in ids:
        if gid not in edits:
            raise SystemExit("ground_follow: no edit %s in edits.json" % gid)
        with np.load(os.path.join(GROUND, edits[gid]["history"])) as h:
            for name in h.files:
                m = re.match(r"h_(x-?\d+_z-?\d+)_idx$", name)
                if m:
                    k = m.group(1)
                    ch.add(k, h[name], h["h_%s_old" % k], h["h_%s_new" % k])
    return ch


def _git(*args, binary=False):
    p = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True)
    if p.returncode:
        return None
    return p.stdout if binary else p.stdout.decode()


def change_since(commit, spec, work):
    if _git("rev-parse", "--verify", commit + "^{commit}") is None:
        raise SystemExit("ground_follow: %s is not a commit" % commit)
    ch = Change(spec)
    for k in spec.keys():
        rel = "assets/source/world_ground/height/%s.exr" % k
        now = os.path.join(ROOT, rel)
        if not os.path.exists(now):
            continue
        ptr = _git("cat-file", "-p", "%s:%s" % (commit, rel), binary=True)
        if ptr is None:
            continue  # no tile then: no ground, no change
        m = re.search(rb"oid sha256:([0-9a-f]{64})", ptr[:200])
        if (m.group(1).decode() if m else hashlib.sha256(ptr).hexdigest()) == sha256(now):
            continue
        data = _git("cat-file", "--filters", "%s:%s" % (commit, rel), binary=True) if m else ptr
        tmp = os.path.join(work, "then_%s.exr" % k)
        with open(tmp, "wb") as f:
            f.write(data)
        ch.add_tile(k, gb.read_exr(tmp)[0], gb.read_exr(now)[0])
    return ch


def change_between(before, after, spec):
    ch = Change(spec)
    for k in spec.keys():
        a, b = os.path.join(before, k + ".exr"), os.path.join(after, k + ".exr")
        if os.path.exists(a) and os.path.exists(b) and sha256(a) != sha256(b):
            ch.add_tile(k, gb.read_exr(a)[0], gb.read_exr(b)[0])
    return ch


# --- the roosts ---------------------------------------------------------------

NODE = re.compile(r'^\[node name="([^"]+)"[^\]]*parent="gull_colony/(roosts|birds)"')
POS = re.compile(r"^(position = Vector3\()([^,]+), ([^,]+), ([^)]+)(\).*)$")


def _fmt(v):
    s = "%.3f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _wildlife_positions(lines):
    """{name: (kind, line index, x text, y text, z text)} for the roosts and the birds."""
    out, cur = {}, None
    for i, line in enumerate(lines):
        if line.startswith("["):
            m = NODE.match(line)
            cur = (m.group(1), m.group(2)) if m else None
            continue
        if cur is not None:
            p = POS.match(line)
            if p:
                out[cur[0]] = (cur[1], i, p.group(2), p.group(3), p.group(4))
                cur = None
    return out


def follow_roosts(change, dry, path=None, restore=None):
    """Moves each roost by the change under it, and the birds at its position with it; or, with
    `restore` {name: y text}, puts those nodes' y back (an undo). Returns {name: [dy, old y, new y]}
    and the birds left (at a roost's x and z with another y)."""
    path = path or WILDLIFE
    lines = open(path).read().split("\n")
    pos = _wildlife_positions(lines)
    roosts = {n: v for n, v in pos.items() if v[0] == "roosts"}
    birds = {n: v for n, v in pos.items() if v[0] == "birds"}
    done, left = {}, []
    if restore is None:
        names = sorted(roosts)
        dys = change.at([float(roosts[n][2]) for n in names], [float(roosts[n][4]) for n in names]) if names else []
        todo = {}
        for n, dy in zip(names, dys):
            if abs(dy) <= ROOST_MIN:
                continue
            todo[n] = float(dy)
            _, _, x, y, z = roosts[n]
            for b, (_, _, bx, by, bz) in sorted(birds.items()):
                if bx == x and bz == z:
                    if by == y:
                        todo[b] = float(dy)
                    else:
                        left.append(b)
    else:
        todo = {n: float(t) - float(pos[n][3]) for n, t in restore.items() if n in pos}
    for n, dy in todo.items():
        if n not in pos:
            raise SystemExit("ground_follow: no %s in %s" % (n, path))
        _, i, x, y, z = pos[n]
        new = restore[n] if restore is not None else _fmt(float(y) + dy)
        done[n] = [round(dy, 3), y, new]
        p = POS.match(lines[i])
        lines[i] = "%s%s, %s, %s%s" % (p.group(1), x, new, z, p.group(5))
    if done and not dry:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            f.write("\n".join(lines))
        os.replace(tmp, path)
    return done, left


# --- running the Blender scripts ----------------------------------------------

def blender(script, blend, args):
    cmd = [BLENDER, "--background", "--factory-startup", blend, "--python", script, "--"] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    result = None
    for line in p.stdout.splitlines():
        if line.startswith("FOLLOW_RESULT "):
            result = json.loads(line[len("FOLLOW_RESULT "):])
    if p.returncode or result is None:
        sys.stderr.write(p.stdout[-4000:] + p.stderr[-2000:])
        raise SystemExit("ground_follow: %s failed on %s" % (os.path.basename(script), os.path.basename(blend)))
    return result


def export(blend):
    p = subprocess.run(["sh", EXPORT, os.path.relpath(blend, ROOT)], cwd=ROOT, capture_output=True, text=True)
    if p.returncode:
        sys.stderr.write(p.stdout[-3000:] + p.stderr[-3000:])
        raise SystemExit("ground_follow: export of %s failed" % os.path.basename(blend))
    glb = os.path.join("assets", os.path.splitext(os.path.basename(blend))[0] + ".glb")
    return glb


# --- the report ---------------------------------------------------------------

def _range(d):
    ups = [v for v in d.values() if v > 0]
    downs = [v for v in d.values() if v < 0]
    parts = []
    if ups:
        parts.append("%d up by up to %.2f m" % (len(ups), max(ups)))
    if downs:
        parts.append("%d down by up to %.2f m" % (len(downs), -min(downs)))
    return ", ".join(parts) or "none"


def report_lines(entry):
    dry = ", dry: nothing written" if entry.get("dry") else ""
    if entry.get("settled"):
        return ["ground_follow %s %s%s" % (entry["id"], entry["from"], (": edits " + ", ".join(
            e["id"] for e in entry["edits"])) if entry.get("edits") else "")]
    if entry["from"] == "undo":
        out = ["ground_follow %s undone%s" % (entry["id"], dry)]
        for k, label in (("rocks", "rocks put back"), ("city", "city objects taken back down"),
                         ("roosts", "roosts and birds put back")):
            if k in entry:
                moved = entry[k].get("moved", entry[k].get("raised", {}))
                out.append("  %s: %d" % (label, len(moved)))
        if entry.get("exported"):
            out.append("  re-exported: %s; Godot imports them at its next start, or Godot --headless --path . --import"
                       % ", ".join(entry["exported"]))
        return out
    out = ["ground_follow %s (%s)%s" % (entry["id"], entry["from"], dry)]
    g = entry["ground"]
    if not g["nodes"]:
        return out + ["  the ground did not change: nothing to follow"]
    out.append("  the ground: %d nodes in %s, %+.2f to %+.2f m" % (
        g["nodes"], ", ".join(g["tiles"]), g["lowest_m"], g["highest_m"]))
    r = entry.get("rocks")
    if r is not None:
        out.append("  rocks: %d moved, %s" % (len(r["moved"]), _range(r["moved"])))
        if r.get("uneven"):
            out.append("    the ground moved unevenly under %d (look at them): %s" % (
                len(r["uneven"]), ", ".join("%s %.2f m" % (n, v) for n, v in sorted(r["uneven"].items(), key=lambda i: -i[1])[:8])))
    c = entry.get("city")
    if c is not None:
        out.append("  city: %d raised%s" % (len(c["raised"]), (" (" + ", ".join("%s +%.2f m" % i for i in sorted(c["raised"].items())) + ")") if c["raised"] else ""))
        if c.get("left"):
            out.append("    the ground fell under %d, left standing (only ever raised): %s" % (
                len(c["left"]), ", ".join("%s %.2f m" % i for i in sorted(c["left"].items()))))
    ro = entry.get("roosts")
    if ro is not None:
        out.append("  roosts and birds: %d moved%s" % (len(ro["moved"]), (": " + ", ".join(
            "%s %+.2f m" % (n, v[0]) for n, v in sorted(ro["moved"].items()))) if ro["moved"] else ""))
        if ro.get("left"):
            out.append("    at a roost but not on it, left: %s" % ", ".join(ro["left"]))
    if entry.get("exported"):
        out.append("  re-exported: %s; Godot imports them at its next start, or Godot --headless --path . --import"
                   % ", ".join(entry["exported"]))
    return out


# --- main ---------------------------------------------------------------------

def run_follow(a):
    spec = Spec()
    log = load_log()
    work = tempfile.mkdtemp(prefix="ground_follow_")
    try:
        covered = []
        if a.edit or a.pending:
            ids = a.edit or pending(log)
            if not ids:
                return {"id": "-", "date": datetime.date.today().isoformat(), "from": "no edit pending",
                        "ground": Change(spec).summary()}
            by = {e["id"]: e for e in edit_log()}
            covered = [{"id": i, "name": by[i]["name"], "sig": signature(by[i])} for i in ids if i in by]
            again = [c["id"] for c in covered if (c["id"], c["sig"]) in followed_edits(log)]
            if again:
                raise SystemExit("ground_follow: %s already followed; --undo that follow first" % ", ".join(again))
            fid = a.id or (ids[0] if len(ids) == 1 else "%s-%s" % (ids[0], ids[-1]))
            src = "edits " + ", ".join(ids)
            ch = change_from_edits(ids, spec)
        elif a.since:
            fid = a.id or "since_%s" % (_git("rev-parse", "--short", a.since) or a.since).strip()
            src = "since " + a.since
            ch = change_since(a.since, spec, work)
        else:
            if not a.id:
                raise SystemExit("ground_follow: --before needs an --id")
            fid = a.id
            src = "%s to %s" % (a.before, a.after)
            ch = change_between(a.before, a.after, spec)
        if not re.match(r"^[A-Za-z0-9_.-]+$", fid):
            raise SystemExit("ground_follow: the id %r must be letters, digits, '_', '-' or '.'" % fid)
        if any(f["id"] == fid for f in log["follows"]) and not a.dry:
            raise SystemExit("ground_follow: %s is already followed; --undo %s first" % (fid, fid))
        entry = {"id": fid, "date": datetime.date.today().isoformat(), "from": src, "ground": ch.summary()}
        if covered:
            entry["edits"] = covered
        only = set(a.only.split(",")) if a.only else {"rocks", "city", "roosts"}
        changed = []
        if ch.summary()["nodes"]:
            npz = os.path.join(work, "change.npz")
            ch.save(npz)
            common = ["--id", fid, "--delta", npz] + (["--dry"] if a.dry else [])
            if "rocks" in only:
                res = blender(ROCKS_PY, RANGE, common)
                entry["rocks"] = {"moved": res["moved"], "uneven": res.get("uneven", {})}
                if res["saved"]:
                    changed.append(RANGE)
            if "city" in only:
                res = blender(CITY_PY, CITY, common + ["--heights", a.after or HEIGHT])
                entry["city"] = {"raised": res["moved"], "left": res.get("left", {})}
                if res["saved"]:
                    changed.append(CITY)
            if "roosts" in only:
                done, left = follow_roosts(ch, a.dry)
                entry["roosts"] = {"moved": done, "left": left}
        if a.dry:
            entry["dry"] = True
        elif not a.no_export:
            entry["exported"] = [export(b) for b in changed]
        if not a.dry and (entry["ground"]["nodes"] or covered):
            log["follows"].append(entry)
            save_log(log)
        return entry
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_settle(a):
    """Records grid edits, or a seat made by hand (an id not in edits.json, like `stage2`), as
    followed already, moving nothing: what stood on the ground was put on it some other way."""
    log = load_log()
    by = {e["id"]: e for e in edit_log()}
    edits = [i for i in a.settle if i in by]
    others = [i for i in a.settle if i not in by]
    done = followed_edits(log)
    again = [i for i in edits if (i, signature(by[i])) in done] + [i for i in others if any(f["id"] == i for f in log["follows"])]
    if again:
        raise SystemExit("ground_follow: %s already in the log" % ", ".join(again))
    entries = []
    today = datetime.date.today().isoformat()
    why = a.why or "settled: what stands on the ground was put on it another way"
    if edits:
        fid = a.id or (edits[0] if len(edits) == 1 else "%s-%s" % (edits[0], edits[-1]))
        entries.append({"id": fid, "date": today, "from": "settled, " + why, "settled": True,
                        "ground": change_from_edits(edits, Spec()).summary(),
                        "edits": [{"id": i, "name": by[i]["name"], "sig": signature(by[i])} for i in edits]})
    for i in others:
        entries.append({"id": i, "date": today, "from": "settled, " + why, "settled": True,
                        "ground": Change(Spec()).summary()})
    for e in entries:
        print("ground_follow: %s settled (%s)%s" % (e["id"], e["from"], ", dry: nothing written" if a.dry else ""))
    if not a.dry:
        log["follows"].extend(entries)
        save_log(log)
    return None


def run_undo(a):
    log = load_log()
    match = [f for f in log["follows"] if f["id"] == a.undo]
    entry = match[-1] if match else {"id": a.undo}
    out = {"id": a.undo, "date": datetime.date.today().isoformat(), "from": "undo", "ground": {
        "tiles": [], "nodes": 0, "lowest_m": 0.0, "highest_m": 0.0}}
    common = ["--id", a.undo, "--undo"] + (["--dry"] if a.dry else [])
    changed = []
    if "rocks" not in entry or entry["rocks"].get("moved"):
        res = blender(ROCKS_PY, RANGE, common + ["--missing-ok"])
        out["rocks"] = {"moved": res["moved"]}
        if res["saved"]:
            changed.append(RANGE)
    if "city" not in entry or entry["city"].get("raised"):
        res = blender(CITY_PY, CITY, common + ["--missing-ok"])
        out["city"] = {"raised": res["moved"]}
        if res["saved"]:
            changed.append(CITY)
    if entry.get("roosts", {}).get("moved"):
        back = {n: v[1] for n, v in entry["roosts"]["moved"].items()}
        lines = open(WILDLIFE).read().split("\n")
        pos = _wildlife_positions(lines)
        stale = [n for n, v in entry["roosts"]["moved"].items() if n in pos and pos[n][3] != v[2]]
        if stale:
            raise SystemExit("ground_follow: moved since the follow, not undone: %s" % ", ".join(stale))
        done, _ = follow_roosts(None, a.dry, restore=back)
        out["roosts"] = {"moved": done}
    if a.dry:
        out["dry"] = True
    else:
        if not a.no_export:
            out["exported"] = [export(b) for b in changed]
        if match:
            log["follows"].remove(entry)
            save_log(log)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--pending", action="store_true", help="follow every logged grid edit not yet followed")
    src.add_argument("--edit", nargs="+", metavar="G<n>", help="follow these grid edits, from their history")
    src.add_argument("--since", metavar="COMMIT", help="follow every change to the grid since this commit")
    src.add_argument("--before", metavar="DIR", help="follow from this folder of height tiles")
    src.add_argument("--undo", metavar="ID", help="put back what the follow with this id moved")
    src.add_argument("--list", action="store_true", help="the follows logged")
    src.add_argument("--settle", nargs="+", metavar="ID", help="record these edits (or a hand seat's id) as followed, moving nothing")
    ap.add_argument("--after", metavar="DIR", help="with --before: the tiles after (default the grid's)")
    ap.add_argument("--why", help="with --settle: one line, how the followers were put on the ground")
    ap.add_argument("--root", help="another copy of assets/source/world_ground (its follows.json too)")
    ap.add_argument("--id", help="the follow's id (default from the edits or the commit)")
    ap.add_argument("--only", help="rocks, city, roosts (comma-separated; default all)")
    ap.add_argument("--dry", action="store_true", help="say what would move; write nothing")
    ap.add_argument("--no-export", action="store_true", help="do not re-export the sources' GLBs")
    ap.add_argument("--report", metavar="FILE", help="also write the report here")
    a = ap.parse_args()
    global GROUND, HEIGHT, LOG
    if a.root:
        GROUND = os.path.abspath(a.root)
        HEIGHT = os.path.join(GROUND, "height")
        LOG = os.path.join(GROUND, "follows.json")
    a.after = a.after or HEIGHT
    if a.settle:
        return run_settle(a)
    if a.list:
        for f in load_log()["follows"]:
            print("\n".join(report_lines(f)))
        return
    if not (a.pending or a.edit or a.since or a.before or a.undo):
        ap.error("name --pending, --edit, --since, --before, --undo or --list")
    entry = run_undo(a) if a.undo else run_follow(a)
    text = "\n".join(report_lines(entry))
    print(text)
    if a.report:
        with open(a.report, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
