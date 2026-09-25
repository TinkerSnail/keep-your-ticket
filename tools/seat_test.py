#!/usr/bin/env python3
"""Is every seated guest sitting on something?

Reads the generated scenes as text and checks that each guest carrying a
`seat_at` has a seat surface under it — a bench slat, a cafe chair, or the
fountain's coping.

This exists because seven of them were not. `ParkPlan.PLAZA_CAFE` holds the
terrace in *final* coordinates and `gen_props._cafe()` put it through the
plaza's dilation on top of that, moving every table, chair and umbrella from
radius 26.8 out to 40.8 — four metres inside the perimeter shopfronts.
`gen_crowd.gd` reads the same constant and does not dilate it, so the guests and
the walkability validator both stayed at 26.8 and only the furniture moved.

Which is precisely why nothing caught it. The graph was valid, the obstacle list
was right, the coplanar test had no opinion, and a screenshot of a guest sitting
on air is a screenshot of a guest. The only way to see it is to ask the two
files whether they agree, which is what this does.

Text rather than a Godot run, like `coplanar_test.py`, so it is instant and has
no scene to stand up.

Usage:  python3 tools/seat_test.py
"""

import re, sys, math

CROWD = "scenes/world/plaza_crowd.tscn"
# These tests parse node text rather than instantiating a scene, so they read
# the generated sources beneath the stable editor-owned wrappers.
PROPS = "scenes/world/generated/plaza_props.tscn"
FOUNTAIN = "scenes/world/generated/plaza_fountain.tscn"
# The plaza benches are hand-placed since 2026-09-24, and each carries its seat
# contract as markers, so their seats are exact points rather than slabs.
FURNITURE = "scenes/world/plaza_furniture.tscn"
BENCH = "scenes/world/park_furniture/plaza_bench.tscn"

# A seat is 0.42–0.55m across, so a guest more than this from the middle of one
# is not on it. Loose enough for the two-to-a-bench offset, which is 0.45.
REACH = 0.75
# A seat marker *is* the seat: the crowd reads it, so a guest is on it or wrong.
MARKER_REACH = 0.02

NODE = re.compile(
    r'\[node name="([^"]+)"[^\]]*\]\n((?:[a-z_0-9]+ = [^\n]*\n)*)')


def origins(path, want):
    out = []
    for m in NODE.finditer(open(path).read()):
        if not want(m.group(1)):
            continue
        t = re.search(r"transform = Transform3D\(([^)]*)\)", m.group(2))
        if not t:
            continue
        v = [float(x) for x in t.group(1).split(",")]
        out.append((m.group(1), v[9], v[11]))
    return out


def marker_seats():
    """World seats of every hand-placed bench: its transform times its markers.

    Godot writes Transform3D row by row, so the basis columns are
    (v0, v3, v6), (v1, v4, v7) and (v2, v5, v8)."""
    markers = []
    for m in NODE.finditer(open(BENCH).read()):
        p = re.search(r"position = Vector3\(([^)]*)\)", m.group(2))
        if m.group(1).startswith("seat_") and p:
            markers.append((m.group(1), [float(x) for x in p.group(1).split(",")]))
    out = []
    for m in NODE.finditer(open(FURNITURE).read()):
        t = re.search(r"transform = Transform3D\(([^)]*)\)", m.group(2))
        if not t:
            continue
        v = [float(x) for x in t.group(1).split(",")]
        for name, (mx, my, mz) in markers:
            x = v[9] + v[0] * mx + v[1] * my + v[2] * mz
            z = v[11] + v[6] * mx + v[7] * my + v[8] * mz
            out.append(("%s/%s" % (m.group(1), name), x, z))
    return out


def seated_guests(path):
    out = []
    for m in NODE.finditer(open(path).read()):
        body = m.group(2)
        s = re.search(r"seat_at = Vector3\(([^)]*)\)", body)
        if not s:
            continue
        v = [float(x) for x in s.group(1).split(",")]
        # A wheelchair guest brought their own seat, so "is there furniture
        # under them" is the wrong question — `_cafe_pull_up` deliberately parks
        # one at the third side of a table, the side with no chair on it. Asking
        # anyway made this test fail on the one guest it should be proudest of.
        if re.search(r"wheelchair = true", body):
            continue
        k = re.search(r'group_kind = "([^"]*)"', body)
        out.append((m.group(1), k.group(1) if k else "?", v[0], v[2]))
    return out


def main():
    # Bench slats and chair seats are furniture; the fountain's coping is a
    # seat too, and counting it here rather than special-casing the rim is what
    # keeps this from needing to know that the rim exists.
    surfaces = [(n, x, z, REACH) for n, x, z in origins(PROPS, lambda n: n.endswith("_seat"))]
    surfaces += [(n, x, z, REACH) for n, x, z in origins(FOUNTAIN, lambda n: n.startswith("coping_"))]
    surfaces += [(n, x, z, MARKER_REACH) for n, x, z in marker_seats()]
    guests = seated_guests(CROWD)
    print("%d seated guests on furniture, %d seat surfaces "
          "(wheelchair users excluded — they bring their own)"
          % (len(guests), len(surfaces)))

    bad = []
    for name, kind, gx, gz in guests:
        # On a seat when inside that seat's own reach; the report names the
        # nearest one either way.
        if any(math.hypot(gx - x, gz - z) <= r for _, x, z, r in surfaces):
            continue
        d, on = min((math.hypot(gx - x, gz - z), n) for n, x, z, _ in surfaces)
        bad.append((name, kind, gx, gz, d, on))
    for name, kind, gx, gz, d, on in bad:
        print("  FAIL %-10s %-7s at (%7.2f,%7.2f) — nearest seat %s is %.2fm away"
              % (name, kind, gx, gz, on, d))
    if bad:
        print("FAIL %d guests sitting on air" % len(bad))
    else:
        print("PASS every seated guest has a seat under them")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
