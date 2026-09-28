"""Turn a ring of copies into one part and a radial array.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/<name>.blend --python tools/blender/radial_array.py -- <ring> [<ring> ...] [--axis X,Y]

A ring in a prop file (`kerb` in the plaza fountain: one object holding 36
separate blocks, as `parts_from_maquette.py` made it) becomes its first block
and the **KYT radial array** Geometry Nodes modifier, which places Count copies
of that block round the object's origin, turned by equal steps. Edit the one
block (Tab) and every copy follows; the modifier's Count sets how many. Send to
game applies the modifier, so the game still gets the whole ring. The plaza
fountain's nine rings, 2026-09-28.

**Lossless but for the generator's nudges.** `gen_props.gd` moved every shape it
made a fraction of a millimetre along Godot's (1, 1, 1), by build order (`_add`,
up to 5 mm), so that no two overlapping shapes shared a plane. The nudges
differ block to block, so a generated ring is not a ring of exact copies. This
finds each block's nudge along (1, -1, 1), Godot's (1, 1, 1) in Blender's axes,
by least squares about the ring's axis (`--axis`, the vertical through the
park's origin by default, where the fountain stands: a nudge of the first
block sideways cannot otherwise be told from a shift of the axis); puts the
first block back on its plan position; and stops if what is left is more than
0.01 mm from exact turned copies, or if a nudge comes out beyond the
generator's 5 mm, which is what a wrong axis looks like. The nudge's job is then done by the modifier's **Lift**: where
neighbouring blocks overlap, every other copy stands 0.5 mm higher, so their
tops never share a plane; where they don't overlap (falls, jets), Lift is 0.
With Lift set, keep Count even, or the last copy and the first share a plane.

The object's origin goes to the ring's axis at the block's mid-height, because
the copies turn about it. Its custom properties (`kyt_collision`, `kyt_shadow`)
and material stay. Refuses an object that already has the modifier. Saves the
file, so it is for a file an agent has prepared, never one Christina has open.
"""

import math
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

GROUP = "KYT radial array"
MODIFIER = "Radial array"
LIFT = 0.0005
NUDGE = Vector((1.0, -1.0, 1.0))  # Godot's (1, 1, 1) in Blender's axes
EXACT = 1e-5  # 0.01 mm
MOST_NUDGE = 0.0051  # the generator's largest, 20 x 0.25 mm, and a hair


def node_group():
    """The shared modifier: Count copies of the input, turned about Z, every
    other one raised by Lift, realized so Send and Check see plain geometry."""
    ng = bpy.data.node_groups.get(GROUP)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(GROUP, "GeometryNodeTree")
    ng.description = "Copies of this object's own mesh round its origin, turned by equal steps (tools/blender/radial_array.py)"
    iface = ng.interface
    iface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    count = iface.new_socket("Count", in_out="INPUT", socket_type="NodeSocketInt")
    count.default_value = 12
    count.min_value = 1
    count.description = "How many copies round the ring, the one you edit included. Keep it even when Lift is set"
    lift = iface.new_socket("Lift", in_out="INPUT", socket_type="NodeSocketFloat")
    lift.default_value = 0.0
    lift.min_value = 0.0
    lift.subtype = "DISTANCE"
    lift.description = "Every other copy stands this much higher, so overlapping neighbours never share a plane"
    iface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    n, link = ng.nodes, ng.links.new
    gin = n.new("NodeGroupInput")
    gout = n.new("NodeGroupOutput")
    points = n.new("GeometryNodePoints")
    link(gin.outputs["Count"], points.inputs["Count"])
    index = n.new("GeometryNodeInputIndex")
    share = n.new("ShaderNodeMath")
    share.operation = "DIVIDE"
    link(index.outputs[0], share.inputs[0])
    link(gin.outputs["Count"], share.inputs[1])
    angle = n.new("ShaderNodeMath")
    angle.operation = "MULTIPLY"
    angle.inputs[1].default_value = 2.0 * math.pi
    link(share.outputs[0], angle.inputs[0])
    euler = n.new("ShaderNodeCombineXYZ")
    link(angle.outputs[0], euler.inputs["Z"])
    turn = n.new("FunctionNodeEulerToRotation")
    link(euler.outputs[0], turn.inputs[0])
    copies = n.new("GeometryNodeInstanceOnPoints")
    link(points.outputs[0], copies.inputs["Points"])
    link(gin.outputs["Geometry"], copies.inputs["Instance"])
    link(turn.outputs[0], copies.inputs["Rotation"])

    parity = n.new("ShaderNodeMath")
    parity.operation = "FLOORED_MODULO"
    parity.inputs[1].default_value = 2.0
    link(index.outputs[0], parity.inputs[0])
    rise = n.new("ShaderNodeMath")
    rise.operation = "MULTIPLY"
    link(parity.outputs[0], rise.inputs[0])
    link(gin.outputs["Lift"], rise.inputs[1])
    up = n.new("ShaderNodeCombineXYZ")
    link(rise.outputs[0], up.inputs["Z"])
    lifted = n.new("GeometryNodeTranslateInstances")
    link(copies.outputs[0], lifted.inputs["Instances"])
    link(up.outputs[0], lifted.inputs["Translation"])
    if "Local Space" in lifted.inputs:
        lifted.inputs["Local Space"].default_value = False
    real = n.new("GeometryNodeRealizeInstances")
    link(lifted.outputs[0], real.inputs["Geometry"])
    link(real.outputs["Geometry"], gout.inputs["Geometry"])

    for x, row in enumerate([[gin], [points, index], [share, parity], [angle, rise],
                             [euler, up], [turn], [copies], [lifted], [real], [gout]]):
        for y, node in enumerate(row):
            node.location = (x * 200.0, -y * 220.0)
    bad = [l for l in ng.links if not l.is_valid]
    if bad:
        raise SystemExit(f"radial_array: {len(bad)} invalid links in the node group")
    return ng


def islands(bm):
    """Vertex index lists of the mesh's loose parts, in vertex order."""
    bm.verts.ensure_lookup_table()
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        group, stack = [], [v]
        seen.add(v.index)
        while stack:
            u = stack.pop()
            group.append(u.index)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        out.append(sorted(group))
    return out


def turn_z(angle):
    return Matrix.Rotation(angle, 3, "Z")


def fit(pos, parts, axis):
    """Each part k as a turned copy of part 0 about `axis`: its step, and by
    least squares part 0's nudge s0 and part k's nudge sk, from
    centroid_k = R_k (centroid_0 - s0 N - c) + c + sk N."""
    cents = [sum((pos[i] for i in p), Vector()) / len(p) for p in parts]
    count = len(parts)
    a0 = math.atan2(cents[0].y - axis.y, cents[0].x - axis.x)
    steps = []
    for c in cents:
        a = math.atan2(c.y - axis.y, c.x - axis.x) - a0
        steps.append(round((a % (2 * math.pi)) / (2 * math.pi / count)) % count)
    if sorted(steps) != list(range(count)):
        raise SystemExit("radial_array: the parts are not evenly spaced round the axis")
    rows, rhs = [], []
    for k in range(1, count):
        r = turn_z(steps[k] * 2 * math.pi / count)
        t = cents[k] - r @ cents[0] - (Matrix.Identity(3) - r) @ axis
        rn = r @ NUDGE
        for i in range(3):
            row = [0.0] * count
            row[0] = -rn[i]           # s0
            row[k] = NUDGE[i]         # sk
            rows.append(row)
            rhs.append(t[i])
    nudges = [float(n) for n in np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)[0]]
    if max(abs(n) for n in nudges) > MOST_NUDGE:
        raise SystemExit(f"radial_array: a nudge of {max(abs(n) for n in nudges) * 1000:.2f} mm: "
                         "is the axis right (--axis)?")
    return steps, nudges


def arrange(obj, axis):
    if any(m.type == "NODES" and m.node_group and m.node_group.name == GROUP for m in obj.modifiers):
        raise SystemExit(f"radial_array: '{obj.name}' already has the radial array")
    world = obj.matrix_world.copy()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(world)
    parts = islands(bm)
    count = len(parts)
    pos = [v.co.copy() for v in bm.verts]
    steps, nudges = fit(pos, parts, axis)
    c = axis

    # How exact are the copies once the nudges are out? Every vertex of part k
    # against part 0 turned, nearest-vertex both ways.
    base = [pos[i] - nudges[0] * NUDGE for i in parts[0]]
    worst = 0.0
    for k in range(1, count):
        r = turn_z(steps[k] * 2 * math.pi / count)
        want = [r @ (p - c) + c + nudges[k] * NUDGE for p in base]
        tree = KDTree(len(want))
        for i, p in enumerate(want):
            tree.insert(p, i)
        tree.balance()
        worst = max(worst, max(tree.find(pos[i])[2] for i in parts[k]))
    if worst > EXACT:
        raise SystemExit(f"radial_array: '{obj.name}' parts are {worst * 1000:.3f} mm from exact copies")

    # Lift where neighbours overlap: part 0 against the part one step on.
    nxt = steps.index(1)
    def tree_of(ids):
        idset = set(ids)
        faces = [[v.index for v in f.verts] for f in bm.faces if f.verts[0].index in idset]
        return BVHTree.FromPolygons([v.co for v in bm.verts], faces)
    lift = LIFT if tree_of(parts[0]).overlap(tree_of(parts[nxt])) else 0.0

    # Keep part 0, back on its plan position, with the origin on the axis.
    keep = set(parts[0])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context="VERTS")
    bmesh.ops.translate(bm, vec=-nudges[0] * NUDGE, verts=bm.verts[:])
    zs = [v.co.z for v in bm.verts]
    origin = Vector((c.x, c.y, (min(zs) + max(zs)) / 2))
    bmesh.ops.translate(bm, vec=-origin, verts=bm.verts[:])
    bm.to_mesh(obj.data)
    bm.free()
    obj.matrix_world = Matrix.Translation(origin)

    ng = node_group()
    mod = obj.modifiers.new(MODIFIER, "NODES")
    mod.node_group = ng
    for item in ng.interface.items_tree:
        if getattr(item, "in_out", None) == "INPUT" and item.name == "Count":
            mod[item.identifier] = count
        elif getattr(item, "in_out", None) == "INPUT" and item.name == "Lift":
            mod[item.identifier] = lift
    moved = max(abs(s) for s in nudges) * NUDGE.length * 1000
    print(f"radial_array: {obj.name}: {count} copies, "
          f"copies exact to {worst * 1000:.4f} mm once the nudges are out, largest nudge {moved:.2f} mm, "
          f"lift {lift * 1000:.1f} mm")
    return count, lift


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    axis = Vector((0.0, 0.0, 0.0))
    if "--axis" in argv:
        i = argv.index("--axis")
        x, y = (float(v) for v in argv[i + 1].split(","))
        axis = Vector((x, y, 0.0))
        del argv[i:i + 2]
    if not argv:
        raise SystemExit("radial_array: name the ring objects after --")
    for name in argv:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            raise SystemExit(f"radial_array: no mesh object '{name}'")
        arrange(obj, axis)
    bpy.ops.wm.save_mainfile()
    print(f"radial_array: {len(argv)} rings saved")


main()
