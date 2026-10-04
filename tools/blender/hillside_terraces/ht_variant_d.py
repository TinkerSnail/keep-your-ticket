"""Variant D: regrade the hill so her lines run on it as ordinary streets.

D1 carries A's streets (all three legs, the meeting at A's height); D2 carries
B's (two streets, steps down, pass 13's street to the underpass). Pass 10's
terrace streets at 25 and 35 m, which her lines continue, are held on grade.
Every street, head and flight of steps is a fixed formation; round them the
ground may rise or fall at most D_SLOPE (a cone envelope: the highest ground
the rule allows, cut out of today's hill), then the creases are relaxed
(free cells averaged with their neighbours, D_PASSES times, within D_BLEND of
the change) so the hill reads as one smooth slope and meets today's ground
without an edge. Lots are then levelled as low terraces. The highway's
protected strip keeps today's ground throughout."""

import numpy as np

from ht_geom import chaikin, cum, dist_to, nearest, resample
from ht_site import D_BLEND, D_PASSES, D_REACH_X, D_SLOPE, STREET_HALF, TERRACE_25, TERRACE_35
from ht_surface import element, protected
from ht_variants import build as build_abc

TERRACE_NOTE = "pass 10's terrace street, held on grade by the regrade"


def formations(key, site):
    base = build_abc("A" if key == "D1" else "B", site.Ef, site.hw_line)
    els = list(base["elements"])
    for nm, pl, h in (("terrace street 25", TERRACE_25, 25.0), ("terrace street 35", TERRACE_35, 35.0)):
        pts, s = resample(chaikin(pl, 2), 1.0)
        els.append(element(nm, "context", pts, s, np.full(len(s), h), STREET_HALF, False, TERRACE_NOTE,
                           open_start=True, open_end=True))
    return base, els


def cone(e, X, Z, k):
    """Ceiling and floor of one formation for the regrade: its height, then rising/falling at k."""
    d, st, _ = nearest(e["pts"], e["s"], X, Z)
    h = np.interp(st, e["s"], e["h"])
    out = np.maximum(d - e["half"], 0.0)
    ceil, floor = h + k * out, h - k * out
    if e["kind"] == "context":                 # the terrace streets only hold their ground; they reshape nothing
        ceil = np.where(out > 0, np.inf, h)
        floor = np.where(out > 0, -np.inf, h)
    P = e["pts"]
    for flag, sgn in (("open_start", -1.0), ("open_end", 1.0)):
        if e.get(flag) and len(P) > 1:
            k0, t = (-1, P[-1] - P[-2]) if sgn > 0 else (0, P[1] - P[0])
            past = sgn * ((X - P[k0][0]) * t[0] + (Z - P[k0][1]) * t[1]) > 1e-6
            past &= (st >= e["s"][-1] - 1e-6) if sgn > 0 else (st <= e["s"][0] + 1e-6)
            ceil, floor, d = np.where(past, np.inf, ceil), np.where(past, -np.inf, floor), np.where(past, np.inf, d)
    return ceil, floor, d, h


def dilate(m, r):
    out = m.copy()
    for _ in range(int(r)):
        n = out.copy()
        n[1:, :] |= out[:-1, :]
        n[:-1, :] |= out[1:, :]
        n[:, 1:] |= out[:, :-1]
        n[:, :-1] |= out[:, 1:]
        out = n
    return out


def regrade(els, site, hold=0.0):
    """`hold`: also keep today's ground within this distance of the highway's centreline (the edit uses it for the
    master's 10 m faces that reach the highway's strip, so the landform blends into the vertices they hold)."""
    X, Z, E = site.X, site.Z, site.E
    C = np.full(E.shape, np.inf)
    F = np.full(E.shape, -np.inf)
    H = np.zeros(E.shape)
    near = np.full(E.shape, np.inf)
    terr = np.full(E.shape, -1)
    for k, e in enumerate(els):
        c, f, d, h = cone(e, X, Z, D_SLOPE)
        C = np.minimum(C, c)
        edge = d - e["half"]
        win = edge < near
        F, H, terr = np.where(win, f, F), np.where(win, h, H), np.where(win, k, terr)
        near = np.minimum(near, edge)
    owner = np.where(near <= 0.0, terr, -1)
    prot = protected(X, Z, site.hw_line)
    # the regrade is the hill's: the town side of the highway keeps its ground, except round the street's own approach to J3
    hw = np.asarray(site.hw_line, float)
    _, _, side = nearest(hw, cum(hw), X, Z)
    town = (side < 0) & (near > 12.0)
    keep = prot | (X > D_REACH_X) | town
    if hold > 0:
        keep |= dist_to(hw, X, Z) <= hold
    S = np.maximum(F, np.minimum(E, C))
    S = np.where(owner >= 0, H, S)
    S = np.where(keep, E, S)
    fixed = (owner >= 0) | keep
    free = dilate(np.abs(S - E) > 0.05, D_BLEND) & ~fixed
    free[0, :] = free[-1, :] = free[:, 0] = free[:, -1] = False
    for _ in range(D_PASSES):
        avg = 0.25 * (np.roll(S, 1, 0) + np.roll(S, -1, 0) + np.roll(S, 1, 1) + np.roll(S, -1, 1))
        S = np.where(free, avg, S)
    return S, owner, prot, free


def terraces(S, lots, owner):
    """Level each lot as a low terrace at its mean height; returns the highest terrace wall."""
    top = 0.0
    for lot in lots:
        jj, ii = lot["cells"]
        keep = owner[jj, ii] < 0
        jj, ii = jj[keep], ii[keep]
        if len(jj) == 0:
            continue
        pad = float(S[jj, ii].mean())
        top = max(top, float(S[jj, ii].max() - pad), float(pad - S[jj, ii].min()))
        S[jj, ii] = pad
        lot["base"] = pad
    return top
