#!/usr/bin/env python3
"""Which way did the water move?

Reads the frame sequences `tools/flow_probe.gd` saves and cross-correlates each
consecutive pair vertically. Positive means the pattern travelled *down* the
screen; negative means up.

This exists because a still frame of water going up and a still frame of water
going down are the same picture. `water_fall.gdshader` ran backwards for its
whole life and four rounds of screenshots never showed it: the sheets under each
basin climbed their own lip. The only way to see a direction is to look at two
frames and subtract them, and the only way to keep seeing it is to have
something do that on demand.

Usage:  python3 tools/flow_probe.py [user-data-dir]

Finds Godot's user-data folder itself on macOS, Linux and Windows; the argument
and $GODOT_USER_DIR override it, in that order.
"""

import sys, os, glob, re

try:
    from PIL import Image
except ImportError:
    sys.exit("needs Pillow: python3 -m pip install pillow")

def project_name(root):
    """The project's name, read from project.godot rather than written twice.

    It is what Godot names the user-data folder after, so a rename over there
    silently moves the frames this reads. Falling back to the literal keeps the
    tool working if the file is ever unreadable, but the file is the truth.
    """
    try:
        with open(os.path.join(root, "project.godot"), encoding="utf-8") as f:
            m = re.search(r'^config/name="([^"]*)"', f.read(), re.M)
            if m:
                return m.group(1)
    except OSError:
        pass
    return "Keep Your Ticket"


def user_dirs(root):
    """Where Godot puts `user://` on this platform, best guess first.

    Three platforms and three different answers, and the tool used to know only
    one of them: it had the macOS path hardcoded, so on Linux it found nothing,
    said "no frames" three times, and then printed FAIL - which is the same thing
    it prints when the water really is going the wrong way. A missing directory
    and a broken shader are not the same result and should not look alike.

    Godot's own rule, from `OS::get_user_data_dir`: the platform's app-data root,
    then `Godot/app_userdata/<project name>`. Linux follows the XDG spec and
    lowercases the `godot`; macOS and Windows do not.
    """
    name = project_name(root)
    out = []
    if sys.platform == "darwin":
        out.append(os.path.expanduser(
            "~/Library/Application Support/Godot/app_userdata/" + name))
    elif os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            out.append(os.path.join(appdata, "Godot", "app_userdata", name))
    else:
        xdg = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        out.append(os.path.join(xdg, "godot", "app_userdata", name))
    # The others anyway, last, so a folder copied between machines still reads.
    for extra in (
        os.path.expanduser("~/Library/Application Support/Godot/app_userdata/" + name),
        os.path.expanduser("~/.local/share/godot/app_userdata/" + name),
    ):
        if extra not in out:
            out.append(extra)
    return out


def resolve_dir(root, argv):
    """An explicit path, then `$GODOT_USER_DIR`, then the platform's own.

    Says which paths it tried when none of them is there, because the failure
    this replaces was a silent one.
    """
    if len(argv) > 1:
        return argv[1]
    env = os.environ.get("GODOT_USER_DIR")
    if env:
        return env
    tried = user_dirs(root)
    for d in tried:
        if os.path.isdir(d):
            return d
    sys.exit("no Godot user-data folder found. Tried:\n  "
             + "\n  ".join(tried)
             + "\n\nRun the probe first:\n"
               "  godot --path . tools/run.tscn -- flow_probe\n"
             + "or name the folder: python3 tools/flow_probe.py <dir>")


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# How far to search, in pixels. Wider than one frame of travel and narrower than
# half the band spacing — beyond that the match wraps onto the next band and the
# sign flips for no reason. At the probe's 35ms gap the three views travel about
# 13, 20 and 11 pixels and their bands are 161, 141 and 62 apart.
#
# The gap this is sized for is `GAP` in `tools/flow_probe.gd`, and for a long
# while it was not: that file said 0.09 while this paragraph said 35ms, and the
# two had never agreed. At 90ms the jets travel about 51 pixels, which is outside
# this window entirely — the correlation cannot reach the real peak and returns
# whatever is at the edge of its range instead. `GAP` is 0.035 now. If it moves
# again, this number has to move with it or stop meaning anything.
#
# **It does exceed the plume's own wrap point of 31**, and that is knowingly
# left. Narrowing to 31 would cost the jets their margin at the far end, and the
# plume is reported rather than asserted for exactly this sort of reason: it is a
# sliver against open sky whose bands are 62 apart, and it is covered by the jet
# row anyway — same shader family, same sign of `flow`.
SEARCH = 34


# How much of the frame's width to average over, per view. A row average is the
# right shape of measurement — the pattern is horizontal banding, so collapsing
# each row to one number keeps the signal and drops the sideways detail — but
# only if the row is *on the water*. A sheet fills the middle third of its frame
# and the plume fills about a fortieth of it, so one width for both averaged the
# plume away to nothing and reported no motion at all.
BAND = {"fall": 0.14, "jet": 0.14, "plume": 0.025}


def column_profile(im, half):
    """Mean brightness per row, over a centred column of the frame."""
    w, h = im.size
    px = im.convert("L").load()
    x0, x1 = int(w * (0.5 - half)), int(w * (0.5 + half))
    return [sum(px[x, y] for x in range(x0, x1)) / (x1 - x0) for y in range(h)]


def moving_part(profiles):
    """Each profile with the static scene taken out of it.

    Necessary, not tidying. The raw row profile is dominated by the *stone* —
    basin rims, the pedestal, the buildings behind — all of which is motionless
    and enormous next to a translucent band, so correlating raw profiles just
    matches the background to itself and reports a shift of zero. That is what
    the first version of this did, on frames where the water was plainly there.
    Subtracting the per-row mean across all frames leaves only what changed,
    which is the travelling band and nothing else.
    """
    n = len(profiles[0])
    mean = [sum(p[y] for p in profiles) / len(profiles) for y in range(n)]
    return [[p[y] - mean[y] for y in range(n)] for p in profiles]


def best_shift(a, b):
    """The vertical offset that best lines b up with a, by least squares."""
    n = len(a)
    best, best_err = 0, None
    for s in range(-SEARCH, SEARCH + 1):
        lo, hi = max(0, s), min(n, n + s)
        if hi - lo < n // 3:
            continue
        err = sum((a[y] - b[y - s]) ** 2 for y in range(lo, hi)) / (hi - lo)
        if best_err is None or err < best_err:
            best, best_err = s, err
    return best


def run(folder, tag):
    files = sorted(glob.glob(os.path.join(folder, "flow_%s_*.png" % tag)))
    if len(files) < 2:
        print("%-6s no frames" % tag)
        return
    half = BAND.get(tag, 0.14)
    profiles = moving_part([column_profile(Image.open(f), half) for f in files])
    shifts = [best_shift(profiles[i], profiles[i + 1])
              for i in range(len(profiles) - 1)]
    # The median, not the mean: a frame the compositor delivered late shows up
    # as one wild shift, and one wild value moves a mean of seven.
    ordered = sorted(shifts)
    median = ordered[len(ordered) // 2]
    if median > 1:
        way = "DOWN"
    elif median < -1:
        way = "UP"
    else:
        way = "still / indeterminate"
    print("%-6s shifts %-34s median %+3d px -> %s"
          % (tag, str(shifts), median, way))
    return way


if __name__ == "__main__":
    folder = resolve_dir(PROJECT_ROOT, sys.argv)
    print("reading %s" % folder)
    print("A band moving down the screen is positive.\n")
    got = {t: run(folder, t) for t in ("fall", "jet", "plume")}
    print()
    # **Only the sheet and the jets are asserted, and the plume is reported.**
    #
    # Not a cop-out — a limit of this instrument, stated rather than hidden. The
    # plume is a 0.6m column and the nearest the camera can stand is the kerb at
    # 9.4m, so it is a sliver against open sky and the correlation is noise. Its
    # `grain` is 3.0, giving a band every 33cm, which caps the usable frame gap
    # so low that the travel never clears that noise.
    #
    # It is covered anyway: the plume wears the same shader as the jets with
    # `flow` of the same sign, so "jets rise" and "the plume rises" are one
    # fact. If the sign is ever flipped again the jet row catches it.
    ok = got.get("fall") == "DOWN" and got.get("jet") == "UP"
    print("PASS the sheets fall and the jets rise" if ok
          else "FAIL the water is not going where it should")
    print("     (plume: %s — reported only, too thin at this range to resolve)"
          % got.get("plume"))
    sys.exit(0 if ok else 1)
