"""Street and step profiles for the hillside terraces proposal.

A street here is always in cut (her lines climb the hill much faster than any
street may), so the best profile is the HIGHEST one the rules allow: the
pointwise minimum of grade cones from every fixed height (the street's start,
its end, the caps under the highway). Junction ends get a flatter landing.
"""

import numpy as np

from ht_site import G_LANDING, G_MAX, LANDING


def grade_limit(s, landing_start=False, landing_end=False, g=G_MAX):
    gl = np.full(len(s), g)
    if landing_start:
        gl[s <= LANDING] = G_LANDING
    if landing_end:
        gl[s >= s[-1] - LANDING] = G_LANDING
    return gl


def integral(s, gl):
    """I(s) = integral of the grade limit along s (trapezoid)."""
    return np.concatenate([[0.0], np.cumsum(0.5 * (gl[1:] + gl[:-1]) * np.diff(s))])


def highest(s, gl, fixed):
    """Highest profile with |grade| <= gl through the fixed (station, height) points (each is a cap
    from above; a fixed END is reached exactly when the profile is feasible). Returns h and
    whether every fixed point is met exactly (False = some end cannot be reached)."""
    I = integral(s, gl)
    h = np.full(len(s), np.inf)
    for sk, hk in fixed:
        Ik = np.interp(sk, s, I)
        h = np.minimum(h, hk + np.abs(I - Ik))
    return h


def lowest(s, gl, fixed):
    I = integral(s, gl)
    h = np.full(len(s), -np.inf)
    for sk, hk in fixed:
        Ik = np.interp(sk, s, I)
        h = np.maximum(h, hk - np.abs(I - Ik))
    return h


def street(s, gl, ends, caps=()):
    """Highest profile meeting both end heights (start, end) exactly and staying under every cap.
    ends: (h_start or None, h_end or None); caps: [(station, max height)]."""
    fixed = list(caps)
    if ends[0] is not None:
        fixed.append((s[0], ends[0]))
    if ends[1] is not None:
        fixed.append((s[-1], ends[1]))
    h = highest(s, gl, fixed)
    lo = lowest(s, gl, [(s[0], ends[0])] if ends[0] is not None else [])
    ok = True
    for k, e in ((0, ends[0]), (-1, ends[1])):
        if e is not None and abs(h[k] - e) > 1e-6:
            ok = False
    if (h < lo - 1e-6).any():
        ok = False
    return h, ok


def vertical_curves(s, h, length):
    """Round the grade breaks: moving average over `length`, ends restored by a linear correction."""
    if length <= 0 or len(s) < 5:
        return h.copy()
    step = s[1] - s[0]
    k = max(1, int(round(length / step / 2)))
    pad = np.r_[np.full(k, h[0]) + (h[0] - h[1: k + 1][::-1]), h, np.full(k, h[-1]) + (h[-1] - h[-k - 1:-1][::-1])]
    sm = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
    corr = (h[0] - sm[0]) + (s - s[0]) / max(s[-1] - s[0], 1e-9) * ((h[-1] - sm[-1]) - (h[0] - sm[0]))
    return sm + corr


def every(s, h, step=10.0):
    """Stations every `step` m (and the end) with height and the grade over the preceding interval."""
    marks = list(np.arange(0.0, s[-1], step)) + [float(s[-1])]
    hs = np.interp(marks, s, h)
    rows = []
    for k, (m, v) in enumerate(zip(marks, hs)):
        g = None if k == 0 else (v - hs[k - 1]) / max(m - marks[k - 1], 1e-9)
        rows.append({"s": round(float(m), 1), "h": round(float(v), 2), "grade_pct": None if g is None else round(100 * float(g), 1)})
    return rows


def max_grade(s, h, window=5.0):
    """Largest grade over any `window` m (so 1 m rounding noise does not count), and where."""
    step = s[1] - s[0]
    k = max(1, int(round(window / step)))
    if len(s) <= k:
        g = np.abs(np.diff(h)) / np.maximum(np.diff(s), 1e-9)
        return float(g.max()), float(s[int(g.argmax())])
    g = np.abs(h[k:] - h[:-k]) / (s[k:] - s[:-k])
    i = int(g.argmax())
    return float(g[i]), float(s[i] + window / 2)
