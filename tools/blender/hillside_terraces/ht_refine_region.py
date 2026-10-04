"""Edit 7 (Blender): the band to refine and what pins it.

The band is every 10 m face holding a vertex that edit 6 had to keep (its faces
reach the highway's strip) though the D1 landform wanted it moved. Its outline
runs along original edges; inside the strip the old surface is carried exactly
by keeping every old triangle edge there as a constraint, cut at the strip's
edge, so each new triangle lies inside one old triangle."""

import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from ht_geom import cum, dist_to, nearest
from ht_site import HW_HALF, HW_VERGE

STRIP = HW_HALF + HW_VERGE


def bvh_with(co, me):
    """A BVH of the mesh with the given vertex heights (to read the ground before edit 6)."""
    polys = [tuple(p.vertices) for p in me.polygons]
    return BVHTree.FromPolygons([tuple(v) for v in co], polys)


def ground(bvh, x, z, top=400.0):
    """Height of the surface under (x, z); cast from `top` (Godot y), low so float32 keeps sub-millimetre precision."""
    h = bvh.ray_cast(Vector((float(x), float(-z), top)), Vector((0.0, 0.0, -1.0)), top + 1000.0)
    return float(h[0].z) if h[0] is not None else float("nan")


def band(me, co, wanted, hw_line):
    """Faces to replace: every face with a vertex outside the strip whose ground is not D1's: those edit 6 held
    (their faces reach the strip) and those its landform raised to blend into them."""
    X, Z = co[:, 0], -co[:, 1]
    r = np.full(len(X), np.inf)
    idx = np.nonzero(wanted)[0]
    r[idx] = dist_to(hw_line, X[idx], Z[idx])
    _, _, side = nearest(np.asarray(hw_line, float), cum(np.asarray(hw_line, float)), X, Z)
    P = (r > STRIP) & wanted & (side > 0)      # the hill's side only: the town side is the underpass's approach
    faces = [p.index for p in me.polygons if any(P[v] for v in p.vertices)]
    return P, faces


def outline(me, faces):
    """The band's boundary loop (original edges between a band face and a kept face, or open edges)."""
    fset = set(faces)
    count = {}
    for f in faces:
        for e in me.polygons[f].edge_keys:
            count[e] = count.get(e, 0) + 1
    edges = [e for e, c in count.items() if c == 1]
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [v for v in adj[cur] if v != prev and v not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        loops.append(loop)
    assert all(len(adj[v]) == 2 for v in adj), "the band's outline is not a simple loop"
    return loops, fset


def old_triangles(me, fset):
    """Blender's own tessellation of the band's faces (what the ray casts and the export use)."""
    me.calc_loop_triangles()
    return [tuple(t.vertices) for t in me.loop_triangles if t.polygon_index in fset]


def strip_cut(a, b, hw_line, iters=40):
    """Where the segment a->b (a inside the strip, b outside) crosses the strip's edge."""
    lo, hi = 0.0, 1.0
    for _ in range(iters):
        m = 0.5 * (lo + hi)
        p = a + m * (b - a)
        if dist_to(hw_line, np.array([p[0]]), np.array([p[1]]))[0] <= STRIP:
            lo = m
        else:
            hi = m
    return a + lo * (b - a)
