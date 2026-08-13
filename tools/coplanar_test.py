#!/usr/bin/env python3
"""Dev tool: finds surfaces that will z-fight, across all six world scenes.

    python3 tools/coplanar_test.py

Shapes are meant to overlap. A coplanar butt leaves a zero-width seam for the
capsule to catch on, so parts run into each other rather than meeting edge to
edge. What they must not also do is *share a plane*: two faces pointing the same
way at the same depth is z-fighting, and it is what "vibration in the ground"
turned out to be.

Two boxes that merely touch are safe -- A's top against B's bottom point
opposite ways and one is culled. The fight needs both faces pointing the SAME
way, at the same depth, over a shared footprint.

This reads the .tscn text rather than loading Godot, which is the point: it
takes a second, so it can run after every regeneration. It is also the only
check that sees hand-authored plaza.tscn and the generated scenes at once, and
the seams that actually go wrong are exactly the ones where two authors meet.

Limits, stated because a check that overstates its coverage is worse than none:
it only judges axis-aligned shapes, since a tilted box's bounding box has faces
its geometry does not. It reports how many it skipped.
"""
import os
import re, glob, sys, itertools, math
from collections import defaultdict

# Reverse-Z with a float depth buffer resolves microns at forty metres, so
# anything a tenth of a millimetre apart is comfortably distinct.
EPS = float(os.environ.get("EPS", "0.00005"))
MIN_AREA = 0.02    # ignore slivers

def parse(path):
    txt = open(path).read()
    out = []
    for chunk in re.split(r'\n\[node ', txt)[1:]:
        head = chunk.split('\n')[0]
        m = re.search(r'name="([^"]+)"', head)
        t = re.search(r'type="([^"]+)"', head)
        if not m or not t:
            continue
        name, typ = m.group(1), t.group(1)
        if not typ.startswith('CSG'):
            continue
        tr = re.search(r'transform = Transform3D\(([^)]*)\)', chunk)
        if tr:
            v = [float(x) for x in tr.group(1).split(',')]
            basis = [v[0:3], v[3:6], v[6:9]]
            org = v[9:12]
        else:
            basis = [[1,0,0],[0,1,0],[0,0,1]]
            org = [0,0,0]
        if typ == 'CSGBox3D':
            s = re.search(r'size = Vector3\(([^)]*)\)', chunk)
            half = [float(x)/2 for x in s.group(1).split(',')] if s else [0.5,0.5,0.5]
        elif typ in ('CSGCylinder3D',):
            r = float((re.search(r'radius = ([\d.eE+-]+)', chunk) or [0,'0.5'])[1])
            h = float((re.search(r'height = ([\d.eE+-]+)', chunk) or [0,'2.0'])[1])
            half = [r, h/2, r]
        elif typ == 'CSGSphere3D':
            r = float((re.search(r'radius = ([\d.eE+-]+)', chunk) or [0,'0.5'])[1])
            half = [r, r, r]
        else:
            continue
        # world AABB from the 8 transformed corners
        lo = [1e9]*3; hi = [-1e9]*3
        for sx in (-1,1):
            for sy in (-1,1):
                for sz in (-1,1):
                    l = [sx*half[0], sy*half[1], sz*half[2]]
                    for a in range(3):
                        w = basis[a][0]*l[0] + basis[a][1]*l[1] + basis[a][2]*l[2] + org[a]
                        lo[a] = min(lo[a], w); hi[a] = max(hi[a], w)
        aligned = all(abs(abs(basis[r][c]) - (1.0 if r == c else 0.0)) < 1e-3
                      or abs(basis[r][c]) < 1e-3 or abs(abs(basis[r][c]) - 1.0) < 1e-3
                      for r in range(3) for c in range(3))
        mat = re.search(r'material = SubResource\("([^"]+)"\)', chunk)
        out.append(dict(name=name, typ=typ, lo=lo, hi=hi, aligned=aligned,
                        mat=mat.group(1) if mat else None, scene=path))
    return out

AX = 'XYZ'

# Scenes that are never in the tree at the same time, so two faces of theirs
# sharing a plane cannot fight — there is only ever one of them to draw.
#
# The west is built twice on purpose: `west_far.tscn` is the tableau the plaza
# looks at and `boardwalk.tscn` is the same frontage, pier and wheel with a floor
# under them, standing in the same coordinates. They are alternatives, and
# `boardwalk.tscn` also fills the stair well that `west_stair.tscn` cuts open.
# Without this the report is dominated by pairs that describe the design working.
EXCLUSIVE = [
    {'boardwalk.tscn', 'west_far.tscn'},
    {'boardwalk.tscn', 'west_stair.tscn'},
    {'boardwalk.tscn', 'plaza.tscn'},
    {'boardwalk.tscn', 'plaza_props.tscn'},
    {'boardwalk.tscn', 'plaza_skyline.tscn'},
    {'boardwalk.tscn', 'entrance.tscn'},
    {'boardwalk.tscn', 'thresholds.tscn'},
    {'boardwalk.tscn', 'plaza_crowd.tscn'},
]


def coexist(a, b):
    a = a.split('/')[-1]
    b = b.split('/')[-1]
    return a == b or {a, b} not in EXCLUSIVE


boxes = []
for f in sorted(glob.glob('scenes/world/*.tscn')):
    boxes.extend(parse(f))
print(f"{len(boxes)} CSG shapes across {len(set(b['scene'] for b in boxes))} scenes\n")

# bucket by each of the 6 face planes so we only compare candidates
buckets = defaultdict(list)
skipped = [b for b in boxes if not b['aligned']]
boxes = [b for b in boxes if b['aligned']]
print(f"{len(skipped)} rotated shapes skipped (a tilted box's bounding box has faces it does not)\n")
for b in boxes:
    for a in range(3):
        for side, val in (('lo', b['lo'][a]), ('hi', b['hi'][a])):
            buckets[(a, side, round(val/EPS))].append(b)
            buckets[(a, side, round(val/EPS)+1)].append(b)

seen = set()
hits = []
for key, group in buckets.items():
    a, side, _ = key
    for A, B in itertools.combinations(group, 2):
        if A is B:
            continue
        if abs(A[side][a] - B[side][a]) > EPS:
            continue
        if not coexist(A['scene'], B['scene']):
            continue
        o = [i for i in range(3) if i != a]
        # must overlap with real area in the plane of the face
        ext = []
        for i in o:
            lo = max(A['lo'][i], B['lo'][i]); hi = min(A['hi'][i], B['hi'][i])
            ext.append(hi - lo)
        if min(ext) <= 1e-4:
            continue
        area = ext[0] * ext[1]
        if area < MIN_AREA:
            continue
        # the volumes must actually interpenetrate on the face axis too,
        # otherwise the two faces are the same slab seen twice
        lo = max(A['lo'][a], B['lo'][a]); hi = min(A['hi'][a], B['hi'][a])
        if hi - lo <= 1e-4:
            continue
        k = tuple(sorted([A['name']+A['scene'], B['name']+B['scene']])) + (a, side)
        if k in seen:
            continue
        seen.add(k)
        hits.append((area, a, side, A, B))

hits.sort(key=lambda h: -h[0])
print(f"{len(hits)} coplanar same-facing overlapping face pairs\n")
same_mat = [h for h in hits if h[3]['mat'] == h[4]['mat']]
diff_mat = [h for h in hits if h[3]['mat'] != h[4]['mat']]
print(f"  {len(diff_mat)} between DIFFERENT materials (visible colour fight)")
print(f"  {len(same_mat)} between the same material (fights, but reads as one surface)\n")

def show(lst, n, title):
    print(f"--- {title} (top {n} by area) ---")
    for area, a, side, A, B in lst[:n]:
        face = f"{'+' if side=='hi' else '-'}{AX[a]}"
        print(f"{area:8.1f} m^2  {face} @ {A[side][a]:>8.3f}  "
              f"{A['scene'].split('/')[-1]:<20} {A['name']} <-> {B['name']}"
              f"{'' if A['mat']==B['mat'] else '   [diff mat]'}")
    print()

show(diff_mat, 30, "different materials")
show(same_mat, 15, "same material")

byscene = defaultdict(int)
for area, a, side, A, B in hits:
    byscene[(A['scene'].split('/')[-1], B['scene'].split('/')[-1])] += 1
print("--- pairs by scene ---")
for k, v in sorted(byscene.items(), key=lambda x: -x[1]):
    print(f"  {v:5d}  {k[0]} <-> {k[1]}")

raise SystemExit(1 if hits else 0)
