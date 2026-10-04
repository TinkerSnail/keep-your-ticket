"""Edit 7: where the new vertices go and how high.

Outside the strip a 3 m lattice follows D1's landform (designed, as edit 6's,
on the ground before edit 6, but without edit 6's hold), relaxed so it meets
the strip's edge and the band's outline (edit 6's ground) without a step;
D1's streets keep their profiles. On the strip's edge and inside it every new
vertex lies on today's surface."""

import numpy as np

from ht_geom import bilinear, dist_to, inside
from ht_site import HW_HALF, HW_VERGE, NEAR

STRIP = HW_HALF + HW_VERGE
STEP = 3.0          # edit 5's patch step
CLEAR = 1.5         # lattice points keep this far from the strip's edge and the outline
PASSES = 80


def band_mask(me, faces, shape):
    m = np.zeros(shape, dtype=bool)
    for f in faces:
        xs = [me.vertices[v].co.x for v in me.polygons[f].vertices]
        zs = [-me.vertices[v].co.y for v in me.polygons[f].vertices]
        i0, i1 = int(round(min(xs) - NEAR["x0"])), int(round(max(xs) - NEAR["x0"]))
        j0, j1 = int(round(min(zs) - NEAR["z0"])), int(round(max(zs) - NEAR["z0"]))
        m[j0:j1 + 1, i0:i1 + 1] = True
    return m


def field(S0, own, M, band, X, Z, hw_line, cut):
    """The heights for the lattice: D1 inside the band (off the strip), today's/edit 6's ground elsewhere, relaxed.
    Over the leg down's last stretch to the highway (`cut`) the ground is not lowered to the street: it starts
    from today's and is only smoothed, and the walled cutting stays the earthworks layer's."""
    strip = dist_to(hw_line, X, Z) <= STRIP
    T = np.where(band & ~strip & ~cut, S0, M)
    fixed = ~band | strip | ((own >= 0) & ~cut)
    for _ in range(PASSES):
        avg = 0.25 * (np.roll(T, 1, 0) + np.roll(T, -1, 0) + np.roll(T, 1, 1) + np.roll(T, -1, 1))
        T = np.where(fixed, T, avg)
    return T


def strip_edge(hw_line, z0, z1, step=STEP):
    """The strip's edge on the hill's side (left of the centreline's travel, x growing east, z south), every `step` m."""
    H = np.asarray(hw_line, float)
    out = []
    for a, b in zip(H, H[1:]):
        if max(a[1], b[1]) < z0 - 20 or min(a[1], b[1]) > z1 + 20:
            continue
        d = b - a
        L = float(np.hypot(*d))
        t = d / L
        n = np.array([t[1], -t[0]])
        if n[0] < 0:
            n = -n                                        # the hill lies east of the highway here
        for s in np.arange(0.0, L, step):
            out.append(a + s * t + STRIP * n)
    return np.array(out)


def lattice(loop_xz, hw_line):
    """3 m lattice points inside the outline, clear of the strip's edge and the outline."""
    P = np.asarray(loop_xz, float)
    xs = np.arange(np.floor(P[:, 0].min() / STEP) * STEP, P[:, 0].max() + STEP, STEP)
    zs = np.arange(np.floor(P[:, 1].min() / STEP) * STEP, P[:, 1].max() + STEP, STEP)
    GX, GZ = np.meshgrid(xs, zs)
    gx, gz = GX.ravel(), GZ.ravel()
    keep = inside(P, gx, gz) & (dist_to(hw_line, gx, gz) > STRIP + CLEAR)
    gx, gz = gx[keep], gz[keep]
    edge = dist_to(np.vstack([P, P[:1]]), gx, gz)
    keep = edge > CLEAR
    return np.c_[gx[keep], gz[keep]]


def sample(A, pts):
    return bilinear(A, NEAR["x0"], NEAR["z0"], NEAR["step"], pts[:, 0], pts[:, 1])
