#!/usr/bin/env python3
"""Dev tool: finds surfaces that will z-fight, across every world scene.

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
takes a couple of seconds, so it can run after every regeneration. It is also
the only check that sees hand-authored plaza.tscn and the generated scenes at
once, and the seams that actually go wrong are exactly the ones where two
authors meet.

**It covers MeshInstance3D as well as CSG since 2026-08-14c**, which is most of
what it now looks at: the park is 3,228 CSG shapes and 3,021 meshes, and every
one of the meshes is a person. Before that the first line read "if not
type.startswith('CSG'): continue", so it opened both crowd scenes, found nothing
in them, and reported zero pairs -- which was true and meant nothing. Guest
bodies had never been checked by it at all, including on the day the heels of
every guest in the park were found to be z-fighting by someone playing the game.

Covering meshes needed three things that CSG did not:

* **Parent transforms have to be composed.** No CSG node in this park is nested;
  every guest part is, three and four deep. A guest's shin is placed relative to
  a knee, relative to a hip, relative to a body.
* **Comparisons happen inside a frame, not in world space.** Every guest is
  rotated to its own heading, so composing to world would make all 3,021 meshes
  non-axis-aligned and skip the lot. Instead, a node whose own basis is not
  axis-aligned starts a new frame, and shapes are only compared with others in
  the same one. Two faces coplanar in a shared rigid frame are coplanar in the
  world; two faces in different frames belong to two different people standing
  near each other, which is a separation problem and not this tool's business.
* **A smaller area floor.** The heels bug was 21cm^2 per leg and plainly visible.
  The old floor was 200cm^2, so even with meshes parsed it would have been
  filtered out as a sliver.

Limits, stated because a check that overstates its coverage is worse than none:

* It only judges axis-aligned shapes, since a tilted box's bounding box has faces
  its geometry does not. It reports how many it skipped.
* A rotated node is its own frame, so its geometry is never compared with its
  siblings' -- a wheel is checked against its own parts and not against the
  chair it is bolted to.
* Instanced sub-scenes are read as their own files at their own origin. Nothing
  in this park instances one at an offset, and if something starts to, this will
  quietly measure it in the wrong place.
"""
import os
import re, glob, sys, itertools, math
from collections import defaultdict

# Reverse-Z with a float depth buffer resolves microns at forty metres, so
# anything a tenth of a millimetre apart is comfortably distinct.
EPS = float(os.environ.get("EPS", "0.00005"))

# Two floors, because the park is built at two scales. A building's wall and a
# guest's shoe are both real fights and 200cm^2 is the wrong threshold for one of
# them. A pair is judged by the smaller of the two, so a guest standing on the
# paving is held to the guest's floor.
MIN_AREA_CSG = 0.02      # 200cm^2 -- buildings, ground, props
MIN_AREA_MESH = 0.0015   # 15cm^2 -- bodies; the heels bug was 21cm^2

# Godot omits a property from the .tscn when it still holds its default, so a
# BoxMesh the generator left at 1x1x1 is written as a bare sub_resource with no
# size line at all. These are the defaults it is leaving out.
MESH_DEFAULTS = {
    'BoxMesh':      {'size': (1.0, 1.0, 1.0)},
    'PlaneMesh':    {'size': (2.0, 2.0)},
    'CylinderMesh': {'top_radius': 0.5, 'bottom_radius': 0.5, 'height': 2.0},
    'SphereMesh':   {'radius': 0.5, 'height': 1.0},
    'TorusMesh':    {'inner_radius': 0.5, 'outer_radius': 1.0},
    # A generated surface. It carries no size properties at all -- its extent is
    # the `aabb` inside `_surfaces`, which is what `mesh_half` reads. Added when
    # the rim stopped being 34 boxes and became one welded strip on 2026-08-18,
    # and the reason it is here rather than left unhandled is that an unknown
    # mesh type is dropped *silently*: the census went from 8682 shapes to 8614
    # and nothing anywhere said that a 340m ridge had stopped being looked at.
    'ArrayMesh':    {},
}


def _num(chunk, key, fallback):
    m = re.search(r'\b%s = ([\d.eE+-]+)' % key, chunk)
    return float(m.group(1)) if m else fallback


def _vec(chunk, key, fallback):
    m = re.search(r'\b%s = Vector([23])\(([^)]*)\)' % key, chunk)
    if not m:
        return fallback
    return tuple(float(x) for x in m.group(2).split(','))


# Which of a shape's own axes it actually has a flat face on. A cylinder is flat
# on its ends and curved round its side; a sphere and a torus are curved
# everywhere and have no faces at all.
#
# **This is the difference between a fight and a tangent.** Without it a sphere
# is judged as its bounding box, and the box's underside coincides with whatever
# the sphere is resting in -- which is one point of contact, not a shared plane.
# It cost three false positives on the prams the first time this ran, and the
# same flaw was in the CSG path from the beginning.
FLAT_AXES = {
    'BoxMesh': {0, 1, 2}, 'PlaneMesh': {0, 1, 2},
    # No flat face by construction, which is the honest answer rather than a
    # convenience: an ArrayMesh here is a landform, and the whole point of it is
    # that no part of it is an axis-aligned plane. It is counted in the census
    # and in the "no flat face at all" line, and never compared -- the same
    # treatment a sphere gets, for the same reason.
    'ArrayMesh': set(),
    'CylinderMesh': {1}, 'SphereMesh': set(), 'TorusMesh': set(),
    'CSGBox3D': {0, 1, 2}, 'CSGCylinder3D': {1},
    'CSGSphere3D': set(), 'CSGTorus3D': set(),
}


def mesh_half(typ, chunk):
    """Half-extents of a unit-placed mesh, before the node's own scale."""
    d = MESH_DEFAULTS.get(typ)
    if d is None:
        return None
    if typ == 'ArrayMesh':
        # AABB is position-then-size, and the position is in the mesh's own
        # space rather than centred on it -- so a half-extent alone would put
        # the shape in the wrong place. Nothing here is ever compared, so the
        # bound only has to be big enough to be honest about what it covers.
        m = re.search(r'"aabb": AABB\(([^)]*)\)', chunk)
        if not m:
            return None
        v = [float(x) for x in m.group(1).split(',')]
        return [v[3] / 2, v[4] / 2, v[5] / 2]
    if typ == 'BoxMesh':
        s = _vec(chunk, 'size', d['size'])
        return [s[0] / 2, s[1] / 2, s[2] / 2]
    if typ == 'PlaneMesh':
        # Flat in XZ with no thickness at all, which the pair test has to know
        # about: two coincident planes never interpenetrate, and the check that
        # rejects "the same slab seen twice" would throw them away.
        s = _vec(chunk, 'size', d['size'])
        return [s[0] / 2, 0.0, s[1] / 2]
    if typ == 'CylinderMesh':
        r = max(_num(chunk, 'top_radius', d['top_radius']),
                _num(chunk, 'bottom_radius', d['bottom_radius']))
        return [r, _num(chunk, 'height', d['height']) / 2, r]
    if typ == 'SphereMesh':
        r = _num(chunk, 'radius', d['radius'])
        return [r, _num(chunk, 'height', d['height']) / 2, r]
    if typ == 'TorusMesh':
        outer = _num(chunk, 'outer_radius', d['outer_radius'])
        inner = _num(chunk, 'inner_radius', d['inner_radius'])
        return [outer, (outer - inner) / 2, outer]
    return None


IDENTITY = ([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], [0.0, 0.0, 0.0])


def read_transform(chunk):
    """Godot serialises Transform3D ROW-major: the first triple is row 0.

    This said the opposite until 2026-08-20 -- "three basis *vectors*, that is,
    columns" -- and built the transpose of every basis in the park. It is an
    easy thing to believe, because `Basis.x` in GDScript *is* a column and the
    text looks like three vectors; the resolution is that the text is not those
    vectors. Measured rather than argued: `_xform(PI/2, -0.18)` prints
    `basis.x = (0, 0, -1)`, and the node it emits serialises as
    `Transform3D(-4.4e-08, -0.179, 0.9838, ...)`. That triple is row 0.

    **The transpose hid four real fights and could only ever hide them in one
    place.** For an axis-aligned box the transpose of a signed permutation maps
    a symmetric extent onto the same world box, so every wall, kerb and slab in
    the park came out identical either way -- which is why this survived from
    the day the tool was written. Guest parts are nested three and four deep
    inside frames rotated to a heading, and there `compose` was evaluating
    `A^T B^T`, which is `(BA)^T`: the composition in the wrong order. Reading it
    correctly turned up `leg_l`/`leg_r` against `tyre` on `guest_09`.

    The lesson generalises past this file: any check that parses `.tscn`
    transforms has this decision to get wrong, and it fails by *quietly
    agreeing* everywhere the geometry is axis-aligned.
    """
    tr = re.search(r'transform = Transform3D\(([^)]*)\)', chunk)
    if not tr:
        return IDENTITY
    v = [float(x) for x in tr.group(1).split(',')]
    return [v[0:3], v[3:6], v[6:9]], v[9:12]


def compose(parent, child):
    """parent o child, as (basis, origin)."""
    pm, po = parent
    cm, co = child
    m = [[sum(pm[r][k] * cm[k][c] for k in range(3)) for c in range(3)]
         for r in range(3)]
    o = [sum(pm[r][k] * co[k] for k in range(3)) + po[r] for r in range(3)]
    return m, o


def axis_aligned(m):
    """True when the basis is a permutation of the axes with a scale on each.

    Not the same question as "is it unrotated". A mesh node carries its size in
    the basis -- `Basis.IDENTITY.scaled(size)` -- so a diagonal of 0.3 is a
    perfectly axis-aligned box, and the old test rejected it for not being 1.
    What actually matters is that each axis still maps to an axis, because then
    the shape's bounding box is the shape.
    """
    used = set()
    for c in range(3):
        col = [m[r][c] for r in range(3)]
        big = [r for r in range(3) if abs(col[r]) > 1e-6]
        if len(big) != 1:
            return False
        scale = abs(col[big[0]])
        if any(abs(col[r]) > scale * 1e-3 for r in range(3) if r != big[0]):
            return False
        used.add(big[0])
    return len(used) == 3


def parse(path):
    txt = open(path).read()

    meshes = {}
    for block in re.split(r'\n\[sub_resource ', '\n' + txt)[1:]:
        head = block.split('\n')[0]
        t = re.search(r'type="([^"]+)"', head)
        i = re.search(r'id="([^"]+)"', head)
        if not t or not i:
            continue
        half = mesh_half(t.group(1), block.split('[node ')[0])
        if half is not None:
            meshes[i.group(1)] = (t.group(1), half)

    out = []
    # path -> (frame id, transform within that frame). Godot writes parents
    # before children, so one pass in document order is enough.
    frames = {}
    root_path = None

    for chunk in re.split(r'\n\[node ', txt)[1:]:
        head = chunk.split('\n')[0]
        body = chunk.split('\n[')[0]
        m = re.search(r'name="([^"]+)"', head)
        t = re.search(r'type="([^"]+)"', head)
        p = re.search(r'parent="([^"]+)"', head)
        if not m:
            continue
        name = m.group(1)
        typ = t.group(1) if t else None

        if p is None:
            node_path = '.'
            root_path = '.'
            parent_frame, parent_tf = 'world', IDENTITY
        else:
            parent = p.group(1)
            node_path = name if parent == '.' else parent + '/' + name
            parent_frame, parent_tf = frames.get(parent, ('world', IDENTITY))

        local = read_transform(body)
        if axis_aligned(local[0]):
            frame, tf = parent_frame, compose(parent_tf, local)
        else:
            # Its own frame, and identity within it. Everything below inherits
            # that frame, so a guest's parts are compared to each other in the
            # guest's own space and the heading it happens to be facing drops
            # out of the question entirely.
            frame, tf = '%s:%s' % (path, node_path), IDENTITY
        frames[node_path] = (frame, tf)

        if typ is None:
            continue

        kind = None
        # What the shape actually *is*. For CSG the node type says so; for a
        # mesh the node is always MeshInstance3D and the answer is in the
        # resource it points at. Keying the flat-face table on the node type
        # made every sphere in the park report as a box.
        shape_typ = typ
        if typ.startswith('CSG'):
            kind = 'csg'
            if typ == 'CSGBox3D':
                s = _vec(body, 'size', (2.0, 2.0, 2.0))
                half = [s[0] / 2, s[1] / 2, s[2] / 2]
            elif typ == 'CSGCylinder3D':
                r = _num(body, 'radius', 0.5)
                half = [r, _num(body, 'height', 2.0) / 2, r]
            elif typ == 'CSGSphere3D':
                r = _num(body, 'radius', 0.5)
                half = [r, r, r]
            elif typ == 'CSGTorus3D':
                outer = _num(body, 'outer_radius', 1.0)
                inner = _num(body, 'inner_radius', 0.5)
                half = [outer, (outer - inner) / 2, outer]
            else:
                continue
            mat = re.search(r'\bmaterial = SubResource\("([^"]+)"\)', body)
        elif typ == 'MeshInstance3D':
            kind = 'mesh'
            ref = re.search(r'\bmesh = SubResource\("([^"]+)"\)', body)
            if not ref or ref.group(1) not in meshes:
                continue
            shape_typ, half = meshes[ref.group(1)]
            half = list(half)
            mat = re.search(r'\bmaterial_override = SubResource\("([^"]+)"\)', body)
        else:
            continue

        basis, org = tf
        aligned = axis_aligned(basis)
        # Exact for a scaled permutation, which is the only case we keep.
        ext = [sum(abs(basis[r][c]) * half[c] for c in range(3)) for r in range(3)]
        lo = [org[r] - ext[r] for r in range(3)]
        hi = [org[r] + ext[r] for r in range(3)]

        # The shape's own flat axes, carried through the permutation into the
        # frame's axes -- a cylinder laid on its side is flat along X, not Y.
        faces = set()
        if aligned:
            for c in FLAT_AXES.get(shape_typ, {0, 1, 2}):
                for r in range(3):
                    if abs(basis[r][c]) > 1e-6:
                        faces.add(r)

        out.append(dict(name=node_path, typ=typ, kind=kind, lo=lo, hi=hi,
                        aligned=aligned, frame=frame, faces=faces,
                        mat=mat.group(1) if mat else None, scene=path,
                        floor=MIN_AREA_CSG if kind == 'csg' else MIN_AREA_MESH))
    return out


AX = 'XYZ'

# Which section each scene stands in. Two scenes that are never mounted together
# cannot fight -- there is only ever one of them to draw.
#
# **Stated as membership rather than as a list of pairs**, which is how this
# started. Every new scene needed a row against each of the nine it excluded, and
# when boardwalk_crowd.tscn arrived it got none of them: its guests would have
# been compared against the whole plaza, which stands in the same coordinates
# with nothing mounted between them.
#
# The west is deliberately in both. `west_shell` and `west_stair` are mounted by
# the plaza and by the boardwalk, because the seam is at the arch and the ground
# either side of it has to be the same ground.
SECTION = {
    'plaza.tscn': 'plaza',
    'plaza_props.tscn': 'plaza',
    'plaza_frontage.tscn': 'plaza',
    'plaza_paving.tscn': 'plaza',
    'plaza_skyline.tscn': 'plaza',
    'plaza_crowd.tscn': 'plaza',
    'plaza_fountain.tscn': 'plaza',
    'entrance.tscn': 'plaza',
    'thresholds.tscn': 'plaza',
    'west_far.tscn': 'plaza',
    'boardwalk.tscn': 'boardwalk',
    'boardwalk_crowd.tscn': 'boardwalk',
    'west_shell.tscn': 'both',
    'west_stair.tscn': 'both',
}
# Anything unlisted is treated as standing in both, which over-reports rather
# than under-reports. A new scene shows up as noise here, not as silence.
UNKNOWN = 'both'


def coexist(a, b):
    a = SECTION.get(a.split('/')[-1], UNKNOWN)
    b = SECTION.get(b.split('/')[-1], UNKNOWN)
    return a == b or a == 'both' or b == 'both'


shapes = []
for f in sorted(glob.glob('scenes/world/*.tscn')):
    shapes.extend(parse(f))
n_csg = sum(1 for s in shapes if s['kind'] == 'csg')
n_mesh = len(shapes) - n_csg
print(f"{len(shapes)} shapes across {len(set(s['scene'] for s in shapes))} scenes "
      f"({n_csg} CSG, {n_mesh} mesh)\n")

shapes = [s for s in shapes if s['aligned']]

# What is genuinely not being looked at, counted rather than asserted. A shape
# alone in its frame has nothing it could be compared with -- that is a rotated
# wheel or a tilted sign, and it is the honest cost of refusing to judge a
# tilted box by its bounding box.
per_frame = defaultdict(int)
for s in shapes:
    per_frame[s['frame']] += 1
alone = sum(1 for s in shapes if per_frame[s['frame']] == 1)
round_only = sum(1 for s in shapes if not s['faces'])
print(f"{len(per_frame) - 1} local frames (a rotated node and everything under it)")
print(f"{alone} shapes alone in a frame, so never compared")
print(f"{round_only} shapes with no flat face at all (spheres, tori)\n")

# Bucket by each of the 6 face planes, and by frame -- shapes in different
# frames are never comparable, so keeping the frame in the key is what stops
# 140 guests' worth of shoes from meeting each other in one bucket.
buckets = defaultdict(list)
for s in shapes:
    for a in s['faces']:
        for side in ('lo', 'hi'):
            val = s[side][a]
            buckets[(s['frame'], a, side, round(val / EPS))].append(s)
            buckets[(s['frame'], a, side, round(val / EPS) + 1)].append(s)

seen = set()
hits = []
for key, group in buckets.items():
    _, a, side, _ = key
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
        if area < min(A['floor'], B['floor']):
            continue
        # The volumes must actually interpenetrate on the face axis too,
        # otherwise the two faces are the same slab seen twice. Shapes with no
        # thickness are exempt: two coincident planes never interpenetrate and
        # fight all the same, which is the whole reason the water is a worry.
        lo = max(A['lo'][a], B['lo'][a]); hi = min(A['hi'][a], B['hi'][a])
        flat = min(A['hi'][a] - A['lo'][a], B['hi'][a] - B['lo'][a]) <= 1e-4
        if hi - lo <= 1e-4 and not flat:
            continue
        k = tuple(sorted([A['name'] + A['scene'], B['name'] + B['scene']])) + (a, side)
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
        face = f"{'+' if side == 'hi' else '-'}{AX[a]}"
        # The frame is printed because "shin <-> shoe" is not an address when
        # the park holds a hundred and forty people with a shin and a shoe each.
        where = A['frame'].split(':')[-1] if A['frame'] != 'world' else 'world'
        print(f"{area:9.4f} m^2  {face} @ {A[side][a]:>8.3f}  "
              f"{A['scene'].split('/')[-1]:<22} {where:<12} "
              f"{A['name'].split('/')[-1]} <-> {B['name'].split('/')[-1]}"
              f"{'' if A['mat'] == B['mat'] else '   [diff mat]'}")
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
