"""What the town sees: the hill's skyline from each viewpoint before and after,
and how much of the disturbed ground is in view (terrain only: buildings, the
highway's deck and planting are not in the master)."""

import math

import numpy as np

from ht_geom import bilinear
from ht_site import EYE, FAR, NEAR, VIEWS


class Ground:
    """Designed ground D inside the design raster, the backdrop outside."""

    def __init__(self, site, D):
        self.site, self.D = site, D

    def __call__(self, x, z):
        x, z = np.asarray(x, float), np.asarray(z, float)
        out = bilinear(self.site.FE, FAR["x0"], FAR["z0"], FAR["step"], x, z)
        inn = (x >= NEAR["x0"]) & (x <= NEAR["x1"] - 1) & (z >= NEAR["z0"]) & (z <= NEAR["z1"] - 1)
        return np.where(inn, bilinear(self.D, NEAR["x0"], NEAR["z0"], NEAR["step"], x, z), out)


def eye_of(site, key):
    x, z = VIEWS[key]["xz"]
    return x, site.Ef(x, z) + EYE, z


def bearing(dx, dz):
    """Compass bearing (deg) of a plan direction: x east, z south."""
    return math.degrees(math.atan2(dx, -dz)) % 360.0


def skyline(G, eye, az, dmax=1600.0):
    """Highest elevation angle (deg) along each bearing in `az`, and the distance where it is reached."""
    ex, ey, ez = eye
    d = np.r_[np.arange(3.0, 400.0, 1.0), np.arange(400.0, dmax, 5.0)]
    a = np.radians(az)[:, None]
    X = ex + np.sin(a) * d[None, :]
    Z = ez - np.cos(a) * d[None, :]
    ang = np.degrees(np.arctan2(G(X, Z) - ey, d[None, :]))
    k = ang.argmax(axis=1)
    return ang.max(axis=1), d[k]


def visible(G, eye, px, pz, tol=0.3, step=1.0):
    """Which target points (on the ground G) can be seen from the eye."""
    ex, ey, ez = eye
    ty = G(px, pz) + 0.2
    L = np.hypot(px - ex, pz - ez)
    vis = np.ones(len(px), dtype=bool)
    n = int(L.max() / step) + 1
    for k in range(1, n):
        f = np.minimum(k * step / np.maximum(L, 1e-9), 1.0)
        live = (f < 0.995) & vis
        if not live.any():
            break
        x = ex + f * (px - ex)
        z = ez + f * (pz - ez)
        line_y = ey + f * (ty - ey)
        g = G(x[live], z[live])
        blocked = g > line_y[live] + tol
        idx = np.nonzero(live)[0]
        vis[idx[blocked]] = False
    return vis


def compare(site, D_existing, D, moved, k_sub=2):
    """Per viewpoint: the skyline change over the hill's bearings and the disturbed area in view."""
    G0, G1 = Ground(site, D_existing), Ground(site, D)
    jj, ii = np.nonzero(moved[::k_sub, ::k_sub])
    px = NEAR["x0"] + ii * k_sub * NEAR["step"]
    pz = NEAR["z0"] + jj * k_sub * NEAR["step"]
    out = {}
    for key in VIEWS:
        eye = eye_of(site, key)
        if len(px) == 0:
            out[key] = {"visible_disturbed_m2": 0.0}
            continue
        brg = np.array([bearing(x - eye[0], z - eye[2]) for x, z in zip(px, pz)])
        az = np.arange(brg.min() - 5.0, brg.max() + 5.0, 0.25)
        s0, d0 = skyline(G0, eye, az)
        s1, d1 = skyline(G1, eye, az)
        drop = s0 - s1
        k = int(drop.argmax())
        vis = visible(G1, eye, px, pz)
        steep = np.abs(np.gradient(D, axis=0)) + np.abs(np.gradient(D, axis=1))
        face = steep[jj * k_sub, ii * k_sub] > 0.7
        out[key] = {"eye": [round(v, 1) for v in eye], "label": VIEWS[key]["label"],
                    "bearings": [round(float(az[0]), 1), round(float(az[-1]), 1)],
                    "skyline_max_drop_deg": round(float(drop.max()), 2), "at_bearing": round(float(az[k]), 1),
                    "skyline_before_deg": round(float(s0[k]), 2), "skyline_after_deg": round(float(s1[k]), 2),
                    "skyline_distance_before_m": round(float(d0[k]), 0), "skyline_distance_after_m": round(float(d1[k]), 0),
                    "skyline_changed_over_deg": round(0.25 * float((drop > 0.05).sum()), 2),
                    "visible_disturbed_m2": float(vis.sum() * k_sub * k_sub),
                    "visible_faces_m2": float((vis & face).sum() * k_sub * k_sub),
                    "az": az.round(2).tolist(), "sky0": s0.round(3).tolist(), "sky1": s1.round(3).tolist()}
    return out
