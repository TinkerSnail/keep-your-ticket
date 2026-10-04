"""Edit 7: the new triangulation of the band.

Points: the band's outline (original vertices), the original vertices inside
the strip, the strip's edge every 3 m and where old triangle edges cross it
(on today's surface), and the 3 m lattice outside the strip (D1, relaxed).
Constraints: the outline, every old triangle edge inside the strip (cut at its
edge) and the strip's edge itself, so each new triangle inside the strip lies
within one old triangle and reproduces its plane."""

import numpy as np

from mathutils import Vector, geometry

from ht_geom import dist_to, inside
from ht_refine_surface import STRIP


def seg_cross(p, q, a, b):
    """Parameter t on p->q where it crosses a->b, or None."""
    r, s = q - p, b - a
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    w = a - p
    t = (w[0] * s[1] - w[1] * s[0]) / den
    u = (w[0] * r[1] - w[1] * r[0]) / den
    return t if (-1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9) else None


class Plan:
    """Points (x, z), their source (original vertex index or -1), heights for new ones, and constraint pairs."""

    def __init__(self):
        self.xz, self.orig, self.h, self.kind, self.cons = [], [], [], [], []
        self.at = {}

    def add(self, x, z, orig=-1, h=float("nan"), kind="orig"):
        key = orig if orig >= 0 else (round(float(x), 4), round(float(z), 4))
        if key in self.at:
            return self.at[key]
        self.at[key] = len(self.xz)
        self.xz.append((float(x), float(z)))
        self.orig.append(int(orig))
        self.h.append(float(h))
        self.kind.append(kind)
        return self.at[key]


def build(co, loop, tris, edge_pts, lattice, lattice_h, today, hw_line):
    """today(x, z) -> height on the current surface. Returns the Plan."""
    pl = Plan()
    X, Z = co[:, 0], -co[:, 1]
    ring = [pl.add(X[v], Z[v], v) for v in loop]
    pl.cons += list(zip(ring, ring[1:] + ring[:1]))
    poly = np.array([pl.xz[i] for i in ring])
    vin = {}
    for t in tris:
        for v in t:
            if v not in vin:
                vin[v] = dist_to(hw_line, np.array([X[v]]), np.array([Z[v]]))[0] <= STRIP
    E = [e for e in edge_pts if inside(poly, np.array([e[0]]), np.array([e[1]]))[0]]
    E = np.array(E) if E else np.zeros((0, 2))
    chain = []                                            # (distance along the edge, point id)
    seen = set()
    for t in tris:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (min(a, b), max(a, b))
            if k in seen:
                continue
            seen.add(k)
            if vin[a] and vin[b]:
                pl.cons.append((pl.add(X[a], Z[a], a), pl.add(X[b], Z[b], b)))
            elif vin[a] != vin[b]:
                i, o = (a, b) if vin[a] else (b, a)
                p, q = np.array([X[i], Z[i]]), np.array([X[o], Z[o]])
                for m in range(len(edge_pts) - 1):
                    tt = seg_cross(p, q, edge_pts[m], edge_pts[m + 1])
                    if tt is not None:
                        c = p + tt * (q - p)
                        xid = pl.add(c[0], c[1], h=today(c[0], c[1]), kind="cut")
                        pl.cons.append((pl.add(X[i], Z[i], i), xid))
                        chain.append((m + float(np.hypot(*(c - edge_pts[m]))) / 3.0, xid))
                        break
    for m, e in enumerate(edge_pts):
        if len(E) and inside(poly, np.array([e[0]]), np.array([e[1]]))[0]:
            near = min(np.hypot(pl.xz[c][0] - e[0], pl.xz[c][1] - e[1]) for _, c in chain) if chain else 9.0
            ring_d = dist_to(np.vstack([poly, poly[:1]]), np.array([e[0]]), np.array([e[1]]))[0]
            if near > 0.75 and ring_d > 0.75:
                chain.append((float(m), pl.add(e[0], e[1], h=today(e[0], e[1]), kind="edge")))
    chain.sort()
    for (sa, a), (sb, b) in zip(chain, chain[1:]):
        mid = (np.array(pl.xz[a]) + np.array(pl.xz[b])) / 2
        if sb - sa < 2.5 and inside(poly, np.array([mid[0]]), np.array([mid[1]]))[0]:
            pl.cons.append((a, b))
    for (x, z), h in zip(lattice, lattice_h):
        pl.add(x, z, h=h, kind="lattice")
    return pl, ring, poly


def triangulate(pl, ring, poly, today):
    """CDT of the plan; triangles as point ids (new points from the CDT get today's height: they lie on old edges)."""
    coords = [Vector((x, -z)) for x, z in pl.xz]
    face = list(ring)
    area = sum(coords[a].x * coords[b].y - coords[b].x * coords[a].y for a, b in zip(face, face[1:] + face[:1]))
    if area < 0:
        face = face[::-1]
    out = geometry.delaunay_2d_cdt(coords, pl.cons, [face], 1, 1e-6)
    vco, _, ofaces, overts = out[0], out[1], out[2], out[3]
    ids = []
    for k, v in enumerate(vco):
        if overts[k]:
            ids.append(overts[k][0])
        else:
            ids.append(pl.add(v.x, -v.y, h=today(v.x, -v.y), kind="cdt"))
    tris = []
    for f in ofaces:
        c = np.mean([[vco[i].x, -vco[i].y] for i in f], axis=0)
        if inside(poly, np.array([c[0]]), np.array([c[1]]))[0]:
            tris.append([ids[i] for i in f])
    return tris
