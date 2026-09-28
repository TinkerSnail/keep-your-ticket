"""A GLB's meshes as triangles in the scene's frame, for the tests that read
files as text instead of starting Godot (`seat_test.py`).

    from glb_mesh import triangles
    tris = triangles("assets/props/plaza_fountain.glb")   # {"coping": [(a, b, c), ...], ...}

Written on 2026-09-27 when the plaza fountain moved from a generated scene to a
GLB sent from Blender: the fountain's coping had been `coping_NN` nodes the
text tests could read, and is now one mesh inside a binary file. Axes are
glTF's, which are Godot's (Y up). A node's name loses the `-col` suffix Send
gives a colliding part, as Godot's importer does.

Handles what Send writes: node translation, rotation and scale or a matrix,
nested nodes, float positions and unsigned integer indices, no Draco. Anything
else is refused rather than read wrongly.
"""

import json
import math
import struct

_COMPONENTS = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def _read(path):
    data = open(path, "rb").read()
    magic, _version, _length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise ValueError(f"{path} is not a GLB")
    offset, doc, blob = 12, None, b""
    while offset < len(data):
        size, kind = struct.unpack_from("<I4s", data, offset)
        chunk = data[offset + 8:offset + 8 + size]
        if kind == b"JSON":
            doc = json.loads(chunk)
        elif kind == b"BIN\0":
            blob = chunk
        offset += 8 + size
    return doc, blob


def _accessor(doc, blob, index):
    acc = doc["accessors"][index]
    if "sparse" in acc:
        raise ValueError("sparse accessors are not read")
    view = doc["bufferViews"][acc["bufferView"]]
    fmt, size = _COMPONENTS[acc["componentType"]]
    width = _WIDTH[acc["type"]]
    stride = view.get("byteStride") or size * width
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    out = []
    for i in range(acc["count"]):
        values = struct.unpack_from("<" + fmt * width, blob, start + i * stride)
        out.append(values if width > 1 else values[0])
    return out


def _matmul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def _local(node):
    if "matrix" in node:
        m = node["matrix"]  # column-major
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    tx, ty, tz = node.get("translation", (0.0, 0.0, 0.0))
    x, y, z, w = node.get("rotation", (0.0, 0.0, 0.0, 1.0))
    sx, sy, sz = node.get("scale", (1.0, 1.0, 1.0))
    rot = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    scale = (sx, sy, sz)
    m = [[rot[r][c] * scale[c] for c in range(3)] + [(tx, ty, tz)[r]] for r in range(3)]
    return m + [[0.0, 0.0, 0.0, 1.0]]


def _apply(m, p):
    return tuple(m[r][0] * p[0] + m[r][1] * p[1] + m[r][2] * p[2] + m[r][3] for r in range(3))


def triangles(path):
    """{node name: [(a, b, c), ...]} for every node with a mesh, in the GLB's frame."""
    doc, blob = _read(path)
    if doc.get("extensionsRequired"):
        raise ValueError(f"{path} requires {doc['extensionsRequired']}")
    out = {}

    def walk(index, parent):
        node = doc["nodes"][index]
        world = _matmul(parent, _local(node))
        if "mesh" in node:
            name = node.get("name", f"node_{index}")
            if name.endswith("-col"):
                name = name[:-4]
            tris = out.setdefault(name, [])
            for prim in doc["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    raise ValueError("only triangle lists are read")
                points = [_apply(world, p) for p in _accessor(doc, blob, prim["attributes"]["POSITION"])]
                order = (_accessor(doc, blob, prim["indices"]) if "indices" in prim
                         else list(range(len(points))))
                tris.extend((points[order[i]], points[order[i + 1]], points[order[i + 2]])
                            for i in range(0, len(order), 3))
        for child in node.get("children", []):
            walk(child, world)

    identity = [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]
    for root in doc["scenes"][doc.get("scene", 0)]["nodes"]:
        walk(root, identity)
    return out


def normal(tri):
    a, b, c = tri
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    length = math.sqrt(sum(x * x for x in n)) or 1.0
    return tuple(x / length for x in n)


def covers_xz(tri, x, z):
    """True when the point (x, z) lies inside the triangle seen from above."""
    (ax, _, az), (bx, _, bz), (cx, _, cz) = tri
    d1 = (x - bx) * (az - bz) - (ax - bx) * (z - bz)
    d2 = (x - cx) * (bz - cz) - (bx - cx) * (z - cz)
    d3 = (x - ax) * (cz - az) - (cx - ax) * (z - az)
    has_neg = d1 < 0 or d2 < 0 or d3 < 0
    has_pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (has_neg and has_pos)
