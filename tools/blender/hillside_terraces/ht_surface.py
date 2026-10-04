"""The designed ground of a variant: each street, head or flight of steps is a
formation at its profile height with a ceiling and a floor round it.

Ceiling (how high the ground may stay): the formation; on a street with lots,
a 7 m lot zone either side as a pad one garage storey up (LOT_RISE); then a
wall of at most WALL_MAX and a planted cut slope rising at 1:k. Floor (how low
it may fall): the formation, then fill at 1:FILL_SLOPE. The designed ground
is max(floor, min(existing, ceiling)) over all elements, so every formation
keeps its height and the natural ground survives wherever no rule reaches it.
The highway's ground is protected: it keeps the existing height, and any
jump at its edge is reported as a wall holding the highway's verge.
"""

import numpy as np

from ht_geom import nearest, dist_to
from ht_site import FILL_SLOPE, HW_HALF, HW_VERGE, LOT_DEPTH, LOT_RISE, RAMP_ZMAX, WALL_MAX


def element(name, kind, pts, s, h, half, lots=False, note="", open_start=False, open_end=False, wall=None):
    """A formation. An OPEN end goes on as something not modelled here (the terrace street it continues,
    or the underpass beyond the highway's band): no cut or fill reaches past it. `wall` is the highest
    retaining wall per station (default WALL_MAX); a walled cutting has no slope above its wall."""
    s = np.asarray(s, float)
    return {"name": name, "kind": kind, "pts": np.asarray(pts, float), "s": s,
            "h": np.asarray(h, float), "half": float(half), "lots": bool(lots), "note": note,
            "open_start": bool(open_start), "open_end": bool(open_end),
            "wall": np.full(len(s), WALL_MAX) if wall is None else np.asarray(wall, float)}


def head(name, centre, h, radius, note=""):
    """A turning head: a level disc (a one-point polyline)."""
    c = np.asarray(centre, float)
    return {"name": name, "kind": "head", "pts": np.array([c, c + [1e-3, 0.0]]), "s": np.array([0.0, 1e-3]),
            "h": np.array([h, h]), "half": float(radius), "lots": False, "note": note}


def bounds(e, X, Z, k_h):
    """Ceiling and floor of one element at points X, Z (any shape); the cut slope is 1:k_h (k_h m across per m up)."""
    d, st, _ = nearest(e["pts"], e["s"], X, Z)
    h = np.interp(st, e["s"], e["h"])
    wm = np.interp(st, e["s"], e["wall"]) if "wall" in e else WALL_MAX
    half = e["half"]
    out = np.maximum(d - half, 0.0)
    if e["lots"]:
        beyond = np.maximum(d - half - LOT_DEPTH, 0.0)
        ceil = np.where(d <= half, h, np.where(d <= half + LOT_DEPTH, h + LOT_RISE,
                                                h + LOT_RISE + wm + beyond / k_h))
    else:
        ceil = np.where(d <= half, h, h + wm + out / k_h)
    floor = h - out / FILL_SLOPE
    if e["kind"] == "lane":                  # a stepped lane lies on the hill: its own strip only, no cut or fill beyond
        ceil = np.where(d <= half, h, np.inf)
        floor = np.where(d <= half, h, -np.inf)
    P = e["pts"]
    for flag, k, sgn in (("open_start", 0, -1.0), ("open_end", -1, 1.0)):
        if e.get(flag) and len(P) > 1:
            t = P[-1] - P[-2] if sgn > 0 else P[1] - P[0]
            past = sgn * ((X - P[k][0]) * t[0] + (Z - P[k][1]) * t[1]) > 1e-6
            past &= (st >= e["s"][-1] - 1e-6) if sgn > 0 else (st <= e["s"][0] + 1e-6)
            ceil = np.where(past, np.inf, ceil)
            floor = np.where(past, -np.inf, floor)
            d = np.where(past, np.inf, d)
    return ceil, floor, d


def protected(X, Z, hw_line):
    """The coast highway's ground (both carriageways, shoulders and a verge) and the ramps."""
    return (dist_to(hw_line, X, Z) <= HW_HALF + HW_VERGE) | (Z <= RAMP_ZMAX)


def design(elements, X, Z, E, hw_line, k_h, cutter=False):
    """Designed ground D at points X, Z over existing E; also which element formation owns each point
    (-1 none) and the protected mask; with cutter=True also the element whose ceiling binds each point."""
    # ceilings combine over every element (a cut from any of them lowers the ground); a floor holds only
    # in its own element's territory (nearest formation edge), so a higher street's fill never buries a
    # lower bench: where they meet the jump is a wall, measured like any other
    C = np.full(X.shape, np.inf)
    F = np.full(X.shape, -np.inf)
    H = np.zeros(X.shape)
    near = np.full(X.shape, np.inf)
    terr = np.full(X.shape, -1)
    cut_by = np.full(X.shape, -1)
    for k, e in enumerate(elements):
        c, f, d = bounds(e, X, Z, k_h)
        cut_by = np.where(c < C, k, cut_by)
        C = np.minimum(C, c)
        edge = d - e["half"]
        win = edge < near
        F = np.where(win, f, F)
        H = np.where(win, c, H)          # inside its formation the ceiling is the formation height
        terr = np.where(win, k, terr)
        near = np.minimum(near, edge)
    D = np.maximum(F, np.minimum(E, C))
    owner = np.where(near <= 0.0, terr, -1)
    D = np.where(owner >= 0, H, D)
    prot = protected(X, Z, hw_line)
    D = np.where(prot, E, D)
    if cutter:
        return D, owner, prot, np.where(owner >= 0, owner, cut_by)
    return D, owner, prot
