"""Unwrap a prop's source parts for its own painted texture: each part laid out whole.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>_source.blend \
        --python tools/blender/unwrap_parts.py -- [--ring-seam=inside|inboard] [--save]

Runs on the source file (every part separate), before Make game mesh. Each part
in `export` is cut open along seams placed on its hidden side and laid flat by
Blender's unwrap, at true scale (one metre is the same size in UV on every
part), its long side along U, so a board's grain or a rail's wear runs left to
right on the texture. Make game mesh keeps these UVs through the fuse and packs
the pieces that survive it onto the prop's texture.

Seams, by the shape of the part (found from its topology, not its name):

- **Box** (a slat, rail, armrest, foot): cut round both ends, which become
  their own end-grain pieces, and along the one long edge that faces most down
  and back. The other three long faces stay joined, so grain wraps unbroken
  over the top, front and back of a board.
- **Capped cylinder** (a leg, upright, bolt): cut round both caps and down the
  one line of the wall that faces most back, down and inboard.
- **Ring** (a closed tube, an arm loop or scroll): cut along the inside of the
  ring (its shortest lengthwise loop, which also lays the tube out as a straight
  strip rather than an arc) and once across the tube where it lies closest to
  another part, usually inside it. `--ring-seam=inboard` cuts along the side
  facing the prop's middle instead: better hidden, laid out as an arc.

Anything else is unwrapped with seams at its sharp edges and reported, to seam
by hand. The parts keep their own vertices and custom normals: the unwrap is
worked out on a welded copy and written back face by face. A part marked
`kyt_unwrapped` has a unwrap Make game mesh can keep; reshape a part and its
unwrap is stale, so run this again. Without `--save` the file is not written.
"""

import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SHARP_DEG = 50.0
GAP_M = 0.02  # between pieces in the loose layout, in metres


def hidden_dir(p):
    """Which way is out of sight from a point on the prop: down, back (+y is the
    back of a bench, which faces -y) and in towards the prop's middle."""
    inboard = -1.0 if p.x > 0.01 else (1.0 if p.x < -0.01 else 0.0)
    return Vector((0.6 * inboard, 0.8, -1.0)).normalized()


def welded_copy(me):
    """A bmesh of the part with split vertices merged, faces in the same order."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    return bm


def edge_loops(bm, edges):
    """Split `edges` of a quad grid into loops: across each vertex, a loop goes on
    by the edge that shares no face with the edge it came in by."""
    left = set(edges)
    loops = []
    while left:
        e0 = left.pop()
        loop = [e0]
        for start in e0.verts:
            prev, v = e0, start
            while True:
                nxt = [e for e in v.link_edges if e is not prev
                       and not set(e.link_faces) & set(prev.link_faces)]
                if len(nxt) != 1 or nxt[0] not in left:
                    break
                e = nxt[0]
                left.discard(e)
                loop.append(e)
                prev, v = e, e.other_vert(v)
        loops.append(loop)
    return loops


def loop_length(loop):
    return sum(e.calc_length() for e in loop)


def classify(bm):
    quads = [f for f in bm.faces if len(f.verts) == 4]
    tris = [f for f in bm.faces if len(f.verts) == 3]
    poles = [v for v in bm.verts if len(v.link_edges) > 4]
    closed = all(e.is_manifold for e in bm.edges)
    if not closed:
        return "other"
    if len(bm.faces) == 6 and len(quads) == 6:
        return "box"
    if len(poles) == 2 and all(len(v.link_edges) == 4 for v in bm.verts if v not in poles) \
            and all(any(p in f.verts for p in poles) for f in tris):
        return "cylinder"
    if not tris and not poles and all(len(v.link_edges) == 4 for v in bm.verts):
        return "ring"
    return "other"


def seams_box(bm, mw):
    long_len = max(e.calc_length() for e in bm.edges)
    long_edges = [e for e in bm.edges if e.calc_length() > 0.99 * long_len]
    axis = (long_edges[0].verts[1].co - long_edges[0].verts[0].co).normalized()
    seams = [e for f in bm.faces if abs(f.normal.dot(axis)) > 0.9 for e in f.edges]
    rot = mw.to_3x3()

    def score(e):
        out = rot @ (e.link_faces[0].normal + e.link_faces[1].normal)
        mid = mw @ ((e.verts[0].co + e.verts[1].co) / 2)
        return out.normalized().dot(hidden_dir(mid))
    return seams + [max(long_edges, key=score)]


def seams_cylinder(bm, mw):
    poles = [v for v in bm.verts if len(v.link_edges) > 4]
    axis = (poles[1].co - poles[0].co).normalized()
    centre = (poles[0].co + poles[1].co) / 2
    cap = {f for f in bm.faces if len(f.verts) == 3}
    rims = [e for e in bm.edges if len({f in cap for f in e.link_faces}) == 2]
    wall = [e for e in bm.edges if not any(f in cap for f in e.link_faces)]
    along = [e for e in wall
             if abs((e.verts[1].co - e.verts[0].co).normalized().dot(axis)) > 0.5]
    rot = mw.to_3x3()

    def score(loop):
        mid = sum(((e.verts[0].co + e.verts[1].co) / 2 for e in loop), Vector()) / len(loop)
        radial = mid - centre
        radial -= axis * radial.dot(axis)
        return (rot @ radial).normalized().dot(hidden_dir(mw @ mid))
    lines = edge_loops(bm, along)
    return rims + max(lines, key=score)


def seams_ring(bm, mw, others, where="inside"):
    bm.normal_update()
    loops = edge_loops(bm, list(bm.edges))
    lengths = [loop_length(l) for l in loops]
    cut = (min(lengths) + max(lengths)) / 2
    along = [l for l, n in zip(loops, lengths) if n > cut]
    across = [l for l, n in zip(loops, lengths) if n <= cut]
    if where == "inboard":
        # The side facing the prop's middle (the seat): better hidden, but the
        # tube's two edges then differ in length and it unrolls as an arc.
        rot = mw.to_3x3()

        def facing(loop):
            verts = {v for e in loop for v in e.verts}
            out = rot @ sum((v.normal for v in verts), Vector())
            mid = mw @ (sum((v.co for v in verts), Vector()) / len(verts))
            inboard = Vector((-1.0 if mid.x > 0 else 1.0, 0.0, 0.0))
            return out.normalized().dot(inboard)
        inside = max(along, key=facing)
    else:
        inside = min(along, key=loop_length)

    def closeness(loop):
        if others is None:
            return 0.0
        pts = [mw @ v.co for e in loop for v in e.verts]
        return min(others.find_nearest(p)[3] for p in pts)
    return inside + min(across, key=closeness)


def seams_sharp(bm):
    return [e for e in bm.edges if not e.is_manifold
            or e.calc_face_angle(0.0) > math.radians(SHARP_DEG)]


def unwrap_welded(bm, method):
    """Unwrap a seamed bmesh with Blender's own unwrap; returns uv per face loop."""
    me = bpy.data.meshes.new("_unwrap_tmp")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("_unwrap_tmp", me)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method=method, margin=0.0, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    uv = me.uv_layers.active.data
    out = [[uv[i].uv.copy() for i in p.loop_indices] for p in me.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return out


def islands(bm):
    """Groups of faces joined across edges that are not seams."""
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        group, stack = [], [f]
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            group.append(cur.index)
            for e in cur.edges:
                if e.seam:
                    continue
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        out.append(group)
    return out


def min_area_angle(pts):
    """The rotation that fits `pts` in the smallest axis-aligned rectangle."""
    pts = sorted({(round(p.x, 7), round(p.y, 7)) for p in pts})
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    best = (float("inf"), 0.0)
    for i in range(len(hull)):
        (x0, y0), (x1, y1) = hull[i], hull[(i + 1) % len(hull)]
        angle = math.atan2(y1 - y0, x1 - x0)
        cs, sn = math.cos(-angle), math.sin(-angle)
        xs = [x * cs - y * sn for x, y in hull]
        ys = [x * sn + y * cs for x, y in hull]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if area < best[0]:
            best = (area, angle)
    return best[1]


def fit_island(bm, mw, uvs, faces):
    """True scale, long side along U, lower-left corner at the origin. Returns size.

    The piece is squared to its tightest bounding rectangle, then turned so a
    clear long side (a board's strip, a ring's tube) lies along U and the part's
    longest 3D direction runs to +U, so like parts read the same way round and a
    squarish piece (a leg's wall, a foot) is placed by the part, not by chance."""
    pts3 = {}
    area3d = 0.0
    for i in faces:
        f = bm.faces[i]
        w = [mw @ v.co for v in f.verts]
        for k, v in enumerate(f.verts):
            pts3[(i, k)] = w[k]
        area3d += sum(((w[k] - w[0]).cross(w[k + 1] - w[0])).length / 2
                      for k in range(1, len(w) - 1))
    area_uv = 0.0
    for i in faces:
        poly = uvs[i]
        area_uv += abs(sum(poly[k].x * poly[k - 1].y - poly[k - 1].x * poly[k].y
                           for k in range(len(poly)))) / 2
    k = math.sqrt(area3d / area_uv) if area_uv > 1e-12 else 1.0
    keys = [(i, n) for i in faces for n in range(len(uvs[i]))]
    uv = [uvs[i][n] * k for i, n in keys]
    c = sum(uv, Vector((0, 0))) / len(uv)
    # The part's longest 3D direction, and which way it runs across the island:
    # least squares s ~ a*u + b*v, where s is distance along that direction.
    p3 = [pts3[key] for key in keys]
    c3 = sum(p3, Vector()) / len(p3)
    cov = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    for p in p3:
        d = p - c3
        for r in range(3):
            for q in range(3):
                cov[r][q] += d[r] * d[q]
    axis = Vector((1, 0, 0))
    for _ in range(30):
        axis = (cov @ axis).normalized() if (cov @ axis).length > 1e-12 else axis
    s3 = [(p - c3).dot(axis) for p in p3]
    suu = sum((p.x - c.x) ** 2 for p in uv)
    svv = sum((p.y - c.y) ** 2 for p in uv)
    suv = sum((p.x - c.x) * (p.y - c.y) for p in uv)
    su = sum((p.x - c.x) * t for p, t in zip(uv, s3))
    sv = sum((p.y - c.y) * t for p, t in zip(uv, s3))
    det = suu * svv - suv * suv
    grad = Vector(((su * svv - sv * suv) / det, (sv * suu - su * suv) / det)) \
        if abs(det) > 1e-18 else Vector((1, 0))
    # Square the piece up by its tightest bounding rectangle (a rectangular
    # piece comes out exactly square to the axes), then of its four quarter
    # turns take one with the long side along U when it has a clear long side,
    # and the part's 3D direction running to +U.
    base = min_area_angle(uv)
    best = None
    for quarter in range(4):
        angle = base + quarter * math.pi / 2
        r = Matrix.Rotation(-angle, 2)
        q = [r @ p for p in uv]
        w = max(p.x for p in q) - min(p.x for p in q)
        h = max(p.y for p in q) - min(p.y for p in q)
        along = (r @ grad).x
        lying = w >= h if max(w, h) > 1.5 * min(w, h) else True
        score = (lying, along)
        if best is None or score > best[0]:
            best = (score, angle)
    angle = best[1]
    rot = Matrix.Rotation(-angle, 2)
    for i in faces:
        uvs[i] = [rot @ (p * k - c) for p in uvs[i]]
    pts = [p for i in faces for p in uvs[i]]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts)))
    for i in faces:
        uvs[i] = [p - lo for p in uvs[i]]
    pts = [p for i in faces for p in uvs[i]]
    return Vector((max(p.x for p in pts), max(p.y for p in pts)))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ring_seam = next((a.split("=", 1)[1] for a in argv if a.startswith("--ring-seam=")), "inside")
    parts = [o for o in bpy.data.collections["export"].all_objects if o.type == "MESH"]
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    pieces = []  # (size, part, faces, uvs)
    report = {"box": [], "cylinder": [], "ring": [], "other": []}
    for part in parts:
        others = [o for o in parts if o is not part]
        tree = None
        if others:
            obm = bmesh.new()
            for o in others:
                tmp = bmesh.new()
                tmp.from_mesh(o.data)
                tmp.transform(o.matrix_world)
                tme = bpy.data.meshes.new("_t")
                tmp.to_mesh(tme)
                obm.from_mesh(tme)
                bpy.data.meshes.remove(tme)
                tmp.free()
            tree = BVHTree.FromBMesh(obm)
            obm.free()
        mw = part.matrix_world
        bm = welded_copy(part.data)
        # The shape is read off a quad copy (the parts arrive as triangles);
        # the seams it picks are edges the triangle mesh has too.
        qb = bm.copy()
        bmesh.ops.join_triangles(qb, faces=qb.faces, angle_face_threshold=math.radians(40),
                                 angle_shape_threshold=math.radians(40), cmp_seam=False,
                                 cmp_sharp=False, cmp_uvs=False, cmp_vcols=False,
                                 cmp_materials=True)
        kind = classify(qb)
        if kind == "box":
            cut = seams_box(qb, mw)
        elif kind == "cylinder":
            cut = seams_cylinder(qb, mw)
        elif kind == "ring":
            cut = seams_ring(qb, mw, tree, ring_seam)
        else:
            cut = seams_sharp(qb)
        keys = {frozenset(v.co.to_tuple() for v in e.verts) for e in cut}
        qb.free()
        for e in bm.edges:
            e.seam = frozenset(v.co.to_tuple() for v in e.verts) in keys
        report[kind].append(part.name)
        # Boards and cylinders unroll flat exactly, which the angle-based unwrap
        # finds; a ring cannot, and minimum stretch spreads its error most evenly.
        uvs = unwrap_welded(bm, "MINIMUM_STRETCH" if kind in ("ring", "other") else "ANGLE_BASED")
        for faces in islands(bm):
            size = fit_island(bm, mw, uvs, faces)
            pieces.append((size, part, faces, uvs))
        bm.free()

    # A loose shelf layout in metres; Make game mesh repacks what survives the fuse.
    total = sum((s.x + GAP_M) * (s.y + GAP_M) for s, *_ in pieces)
    width = max(max(s.x for s, *_ in pieces) + GAP_M, math.sqrt(total * 1.3))
    x = y = shelf = 0.0
    offsets = []
    for size, part, faces, uvs in sorted(pieces, key=lambda t: -t[0].y):
        if x + size.x > width:
            x, y, shelf = 0.0, y + shelf + GAP_M, 0.0
        offsets.append((Vector((x, y)), part, faces, uvs))
        x += size.x + GAP_M
        shelf = max(shelf, size.y)
    side = max(width, y + shelf)

    for part in parts:
        me = part.data
        while len(me.uv_layers) > 1:
            me.uv_layers.remove(me.uv_layers[-1])
        layer = me.uv_layers[0] if me.uv_layers else me.uv_layers.new()
        layer.name = "UVMap"
    for off, part, faces, uvs in offsets:
        me = part.data
        data = me.uv_layers[0].data
        for i in faces:
            for li, p in zip(me.polygons[i].loop_indices, uvs[i]):
                data[li].uv = (p + off) / side
    for part in parts:
        part["kyt_unwrapped"] = True

    print(f"unwrap_parts: {len(parts)} parts, {len(pieces)} pieces, layout {side:.2f} m square "
          f"({1024 / side:.0f} px/m at 1024, {2048 / side:.0f} at 2048 before the fuse trims it)")
    for kind, names in report.items():
        if names:
            print(f"  {kind}: {len(names)}" + (f"  {', '.join(names)}" if kind == "other" else ""))
    if report["other"]:
        print("  (other: cut at sharp edges; worth seaming by hand)")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


main()
