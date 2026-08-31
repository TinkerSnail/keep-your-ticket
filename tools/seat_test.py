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

# A seat is 0.42–0.55m across, so a guest more than this from the middle of one
# is not on it. Loose enough for the two-to-a-bench offset, which is 0.45.
REACH = 0.75

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
    surfaces = origins(PROPS, lambda n: n.endswith("_seat"))
    surfaces += origins(FOUNTAIN, lambda n: n.startswith("coping_"))
    guests = seated_guests(CROWD)
    print("%d seated guests on furniture, %d seat surfaces "
          "(wheelchair users excluded — they bring their own)"
          % (len(guests), len(surfaces)))

    bad = []
    for name, kind, gx, gz in guests:
        d, on = min((math.hypot(gx - x, gz - z), n) for n, x, z in surfaces)
        if d > REACH:
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
