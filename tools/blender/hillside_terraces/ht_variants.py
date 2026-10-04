"""Variants A, B and C as lists of formations (streets, heads, steps), each with
its centreline in plan and its profile. Everything inside the highway's
protected band (the underpass and its approach) is kept as an `underpass`
record for the clearance check and the drawings, not as ground."""

import numpy as np

import ht_profile as P
from ht_geom import chaikin, point_dist, resample
from ht_site import (DOWN, HW_CLEAR, HW_DECK, HW_HALF, HW_PAVED_HALF, HW_VERGE, J3, J3_H, LINE1, LINE2, LOW_CTRL,
                     LOWER_TERRACE_H, MEET, STEPS_HALF, STREET_HALF, UPPER_TERRACE_H, VC_LEN, WALL_MAX)
from ht_surface import element, head

HEAD_R = 9.0            # turning head / junction radius
PORTAL_WALLED = 40.0    # m of walled cutting before the highway's band on a street that goes under it
WALL_FULL = 200.0       # "a wall to the top": no planted slope
C_FACE_MAX = 10.0       # C: a street runs on while the cut face behind its lots stays within one wall and 6 m of slope


def line(pl, passes=2):
    return resample(chaikin(pl, passes), 1.0)


def hw_dist(pts, hw_line):
    return np.array([point_dist(hw_line, p) for p in pts])


def caps_under(pts, s, Ef, hw_line):
    """(station, max street height) wherever the street is under a carriageway: road surface less clear height and deck."""
    d = hw_dist(pts, hw_line)
    return [(float(s[k]), float(Ef(*pts[k]) - HW_CLEAR - HW_DECK)) for k in range(len(s)) if d[k] <= HW_PAVED_HALF]


def portal(pts, hw_line, half):
    """First station index where the formation edge reaches the highway's protected band."""
    d = hw_dist(pts, hw_line)
    hit = np.nonzero(d <= HW_HALF + HW_VERGE + half)[0]
    return int(hit[0]) if len(hit) else len(pts)


def push_out(ctrl, hw_line):
    """Pass 13's line ran on the highway's shoulder (14-22 m from its centreline at z 534-616): every control
    point before the turn under the highway is moved out until the street's edge clears the protected band."""
    dmin = HW_HALF + HW_VERGE + STREET_HALF + 0.5
    turn = int(np.argmax([p[0] for p in ctrl]))         # the most easterly point: there it turns under
    H = np.asarray(hw_line, float)
    out = []
    for k, p in enumerate(ctrl):
        p = np.asarray(p, float)
        if k < turn:
            best = None
            for a, b in zip(H, H[1:]):
                ab = b - a
                t = min(1.0, max(0.0, float((p - a) @ ab) / float(ab @ ab)))
                f = a + t * ab
                if best is None or np.hypot(*(p - f)) < np.hypot(*(p - best)):
                    best = f
            d = float(np.hypot(*(p - best)))
            if d < dmin:
                p = best + (p - best) / max(d, 1e-9) * dmin
        out.append(tuple(p))
    return out


def finish(s, h_raw):
    return np.minimum(P.vertical_curves(s, h_raw, VC_LEN), h_raw)


def low_profile(s):
    """Pass 13's lower street: 25.0 at the terrace, up 5 % to 27.5, level, down to 19.6 at the portal
    (37 m before J3), easing to J3 at 18.2 (design13.py profile_low, unchanged)."""
    L = s[-1]
    s_portal = L - 37.0
    out = np.where(s <= 50.0, 25.0 + 2.5 * s / 50.0, 27.5)
    fall = 27.5 + (19.6 - 27.5) * (s - 70.0) / (s_portal - 70.0)
    out = np.where(s > 70.0, fall, out)
    return np.where(s > s_portal, 19.6 + (J3_H - 19.6) * (s - s_portal) / (L - s_portal), out)


def split(name, kind, pts, s, h, half, lots, hw_line, note, open_start=False, walled=False):
    """The whole street as one formation to J3 (open there: Beach Road goes on); the stretch inside the
    highway's band is also kept as the underpass record. The band's ground itself stays protected, so the
    street's cut stops at its edge: the jump there is the underpass's wing walls."""
    d = hw_dist(pts, hw_line)
    inb = np.nonzero(d <= HW_HALF + HW_VERGE)[0]
    # the approach to the underpass runs into the hill's west face, steeper than 1:1 there: a 1:1 slope from its
    # toe would take the whole face, so its last PORTAL_WALLED m before the band are a walled cutting (the portal's wing walls)
    wall = np.full(len(s), WALL_FULL if walled else WALL_MAX)
    if len(inb):
        wall[s >= s[inb[0]] - PORTAL_WALLED] = WALL_FULL
    el = [element(name, kind, pts, s, h, half, lots, note, open_start=open_start, open_end=True, wall=wall)]
    under = None
    if len(inb):
        a, b = int(inb[0]), int(inb[-1]) + 1
        under = {"name": name, "pts": pts[a:b].tolist(), "s": s[a:b].tolist(), "h": h[a:b].tolist()}
    return el, under


def connector(Ef, hw_line, out):
    """Pass 13's lower street from the lower terrace's west end to J3 (B and C)."""
    pts, s = line(push_out(LOW_CTRL, hw_line), 1)
    h = low_profile(s)
    caps = caps_under(pts, s, Ef, hw_line)
    out["checks"]["connector_clearance_min_m"] = min((cap + HW_CLEAR - hk for (sk, cap), hk in
                                                      zip(caps, np.interp([c[0] for c in caps], s, h))), default=None)
    # no lots on it: its west side is the highway's band, its east side line 1's cut face (they run 15-20 m apart)
    el, under = split("street to the underpass", "street", pts, s, h, STREET_HALF, False, hw_line,
                      "pass 13's lower street, its profile unchanged, moved off the highway's shoulder", open_start=True,
                      walled=True)     # it runs at the foot of a face steeper than 1:1 all the way: pass 13's walled cutting
    out["underpass"].append(under)
    out["profiles"]["street to the underpass"] = P.every(s, h)
    out["grades"]["street to the underpass"] = P.max_grade(s, h)
    return el, (pts, s, h)


def build(variant, Ef, hw_line):
    out = {"variant": variant, "elements": [], "underpass": [], "profiles": {}, "grades": {}, "checks": {}, "lanes": []}
    p1, s1 = line(LINE1 + [MEET])
    p2, s2 = line(LINE2 + [MEET])
    if variant == "A":
        pd, sd = line(DOWN + [J3])
        caps = caps_under(pd, sd, Ef, hw_line)
        hd, ok = P.street(sd, P.grade_limit(sd, True, True), (None, J3_H), caps)
        hd = finish(sd, hd)
        HM = float(hd[0])
        out["checks"]["down_leg_reaches_J3"] = ok
        el, under = split("leg down (street)", "street", pd, sd, hd, STREET_HALF, True, hw_line, "her leg down, a street")
        out["elements"] += el
        out["underpass"].append(under)
        out["profiles"]["leg down (street)"] = P.every(sd, hd)
        out["grades"]["leg down (street)"] = P.max_grade(sd, hd)
        out["checks"]["down_leg_clearance_min_m"] = min((cap + HW_CLEAR - hk for (sk, cap), hk in
                                                         zip(caps, np.interp([c[0] for c in caps], sd, hd))), default=None)
    else:
        h1, ok = P.street(s1, P.grade_limit(s1, False, True), (LOWER_TERRACE_H, None))
        HM = float(finish(s1, h1)[-1])
    lines = {}
    for nm, (pp, ss, h0) in (("line 1", (p1, s1, LOWER_TERRACE_H)), ("line 2", (p2, s2, UPPER_TERRACE_H))):
        h, ok = P.street(ss, P.grade_limit(ss, False, True), (h0, HM))
        h = finish(ss, h)
        out["checks"][f"{nm}_feasible"] = ok
        lines[nm] = (pp, ss, h)
    out["meet_h"] = HM
    if variant in ("A", "B"):
        for nm, (pp, ss, h) in lines.items():
            out["elements"].append(element(nm, "street", pp, ss, h, STREET_HALF, True, f"her {nm}, a street", open_start=True))
            out["profiles"][nm] = P.every(ss, h)
            out["grades"][nm] = P.max_grade(ss, h)
        out["elements"].append(head("meeting", MEET, HM, HEAD_R, "where her lines meet"))
    if variant in ("B", "C"):
        el, low = connector(Ef, hw_line, out)
        out["elements"] += el
    if variant == "B":
        steps(out, low, HM, hw_line)
    if variant == "C":
        from ht_variant_c import lanes_variant
        lanes_variant(out, lines, Ef)
    return out


def steps(out, low, HM, hw_line):
    """B: public steps down her leg from the meeting to the street to the underpass."""
    pd, sd = line(DOWN, 1)
    k = portal(pd, hw_line, STEPS_HALF)
    lp, ls, lh = low
    ok = hw_dist(lp, hw_line) > HW_HALF + HW_VERGE + STREET_HALF      # land where the street is still outside the band
    dd = np.where(ok, np.hypot(lp[:, 0] - pd[k - 1, 0], lp[:, 1] - pd[k - 1, 1]), np.inf)
    j = int(np.argmin(dd))
    pts, s = resample(np.r_[pd[:k], lp[j:j + 1]], 1.0)
    h = HM + (lh[j] - HM) * s / s[-1]
    out["elements"].append(element("steps down", "steps", pts, s, h, STEPS_HALF, False, "public steps on her leg down"))
    out["profiles"]["steps down"] = P.every(s, h)
    out["checks"]["steps_drop_m"] = float(HM - lh[j])
    out["checks"]["steps_plan_m"] = float(s[-1])
    out["grades"]["steps down"] = P.max_grade(s, h)
