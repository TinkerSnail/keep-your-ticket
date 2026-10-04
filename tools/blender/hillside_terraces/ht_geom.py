"""Plan geometry for the hillside terraces proposal: polylines, resampling,
and nearest-point fields over a raster (no shapely or scipy on this Mac)."""

import math

import numpy as np


def chaikin(pl, passes=2):
    """Corner-cutting smoothing that keeps both ends."""
    p = [tuple(map(float, q)) for q in pl]
    for _ in range(passes):
        out = [p[0]]
        for a, b in zip(p, p[1:]):
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        out.append(p[-1])
        p = out
    return p


def cum(pl):
    pl = np.asarray(pl, float)
    return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pl, axis=0).T))])


def resample(pl, step=1.0):
    """Points every `step` m along the polyline, ends kept; returns (pts, s)."""
    pl = np.asarray(pl, float)
    c = cum(pl)
    n = max(1, int(round(c[-1] / step)))
    s = np.linspace(0.0, c[-1], n + 1)
    return np.c_[np.interp(s, c, pl[:, 0]), np.interp(s, c, pl[:, 1])], s


def tangents(pts):
    t = np.gradient(np.asarray(pts, float), axis=0)
    return t / np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-9)[:, None]


def offset(pts, d):
    """Offset sideways by d (left of travel on a north-up plan with z south: normal (t_z, -t_x))."""
    t = tangents(pts)
    return np.asarray(pts, float) + d * np.c_[t[:, 1], -t[:, 0]]


def nearest(pts, s, X, Z):
    """For raster coordinates X, Z (same shape): distance to the polyline, station of the foot,
    and signed offset (+ on the left of travel, as `offset`)."""
    P = np.asarray(pts, float)
    x, z = X.ravel(), Z.ravel()
    best = np.full(x.shape, np.inf)
    st = np.zeros(x.shape)
    sg = np.zeros(x.shape)
    for k in range(len(P) - 1):
        a, b = P[k], P[k + 1]
        ab = b - a
        L2 = max(float(ab @ ab), 1e-12)
        t = np.clip(((x - a[0]) * ab[0] + (z - a[1]) * ab[1]) / L2, 0.0, 1.0)
        fx, fz = a[0] + t * ab[0], a[1] + t * ab[1]
        d = np.hypot(x - fx, z - fz)
        m = d < best
        best[m] = d[m]
        st[m] = s[k] + t[m] * (s[k + 1] - s[k])
        cr = ab[0] * (z - a[1]) - ab[1] * (x - a[0])     # z-south plan: cross > 0 is right of travel
        sg[m] = np.where(cr[m] > 0, -1.0, 1.0)
    return best.reshape(X.shape), st.reshape(X.shape), sg.reshape(X.shape)


def dist_to(pl, X, Z):
    P = np.asarray(pl, float)
    d, _, _ = nearest(P, cum(P), X, Z)
    return d


def point_dist(pl, p):
    P = np.asarray(pl, float)
    best = math.inf
    for a, b in zip(P, P[1:]):
        ab = b - a
        t = min(1.0, max(0.0, float((np.asarray(p) - a) @ ab) / max(float(ab @ ab), 1e-12)))
        best = min(best, float(np.hypot(*(np.asarray(p) - (a + t * ab)))))
    return best


def bilinear(A, x0, z0, step, x, z):
    """Bilinear sample of raster A (rows z, cols x) at arrays x, z."""
    fi = (np.asarray(x, float) - x0) / step
    fj = (np.asarray(z, float) - z0) / step
    i0 = np.clip(np.floor(fi).astype(int), 0, A.shape[1] - 2)
    j0 = np.clip(np.floor(fj).astype(int), 0, A.shape[0] - 2)
    tx, tz = fi - i0, fj - j0
    a, b = A[j0, i0], A[j0, i0 + 1]
    c, d = A[j0 + 1, i0], A[j0 + 1, i0 + 1]
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz


def rect(c, t, along, across, shift=0.0):
    """Rectangle (4 corners) centred `shift` m to the left of c, axis t, along x across."""
    t = np.asarray(t, float) / max(np.hypot(*t), 1e-9)
    n = np.array([t[1], -t[0]])
    c = np.asarray(c, float) + shift * n
    h, w = along / 2, across / 2
    return [tuple(c + sa * h * t + sb * w * n) for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def inside(P, X, Z):
    """Mask of raster points inside polygon P (even-odd)."""
    P = np.asarray(P, float)
    m = np.zeros(X.shape, dtype=bool)
    for (x1, z1), (x2, z2) in zip(P, np.roll(P, -1, axis=0)):
        c = ((z1 > Z) != (z2 > Z)) & (X < (x2 - x1) * (Z - z1) / np.where(z2 == z1, 1e-12, z2 - z1) + x1)
        m ^= c
    return m
