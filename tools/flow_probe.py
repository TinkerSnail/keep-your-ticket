#!/usr/bin/env python3
"""Which way did the water move?

Reads the frame sequences `tools/_flow_probe.gd` saves and cross-correlates each
consecutive pair vertically. Positive means the pattern travelled *down* the
screen; negative means up.

This exists because a still frame of water going up and a still frame of water
going down are the same picture. `water_fall.gdshader` ran backwards for its
whole life and four rounds of screenshots never showed it: the sheets under each
basin climbed their own lip. The only way to see a direction is to look at two
frames and subtract them, and the only way to keep seeing it is to have
something do that on demand.

Usage:  python3 tools/flow_probe.py [user-data-dir]
"""

import sys, os, glob, re

try:
    from PIL import Image
except ImportError:
    sys.exit("needs Pillow: python3 -m pip install pillow")

DEFAULT_DIR = os.path.expanduser(
    "~/Library/Application Support/Godot/app_userdata/Keep Your Ticket")

# How far to search, in pixels. Wider than one frame of travel and narrower than
# half the band spacing — beyond that the match wraps onto the next band and the
# sign flips for no reason. At the probe's 35ms gap the three views travel about
# 13, 20 and 11 pixels and their bands are 161, 141 and 62 apart, so the
# tightest wrap point is 31 and this sits under it.
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
    folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR
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
