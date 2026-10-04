"""Small PIL helpers for the hillside terraces drawings (no matplotlib here)."""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial Unicode.ttf",
              "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")


def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def hillshade(H, step=1.0, az=315.0, alt=45.0):
    """Lambertian shade 0..1 of a height raster (rows z south, cols x east); light from the north-west."""
    gz, gx = np.gradient(H, step)
    nx, ny, nz = -gx, np.ones_like(H), -gz
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    a, b = np.radians(az), np.radians(alt)
    lx, ly, lz = np.sin(a) * np.cos(b), np.sin(b), -np.cos(a) * np.cos(b)
    return np.clip((nx * lx + ny * ly + nz * lz) / n, 0.0, 1.0)


def ramp(v, stops):
    """Piecewise-linear colour ramp: stops [(value, (r, g, b)), ...] -> uint8 image array."""
    v = np.asarray(v, float)
    vals = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    out = np.zeros(v.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(v, vals, cols[:, c])
    return out


GROUND = [(0.0, (196, 205, 170)), (30.0, (214, 200, 150)), (60.0, (204, 170, 120)), (90.0, (186, 140, 100))]
CUT = [(0.0, (255, 255, 255)), (5.0, (250, 215, 160)), (15.0, (240, 150, 90)), (30.0, (200, 70, 60)), (50.0, (120, 20, 60))]


def terrain_rgb(E, D, step=1.0):
    """Ground coloured by height, the cut tinted by its depth, all hill-shaded."""
    base = ramp(D, GROUND)
    cut = E - D
    tint = ramp(cut, CUT)
    w = np.clip(cut / 3.0, 0.0, 1.0)[..., None]
    fill = np.clip((D - E) / 2.0, 0.0, 1.0)[..., None]
    col = base * (1 - w) + tint * w
    col = col * (1 - fill) + np.array([120, 160, 220]) * fill
    sh = hillshade(D, step)[..., None]
    return np.clip(col * (0.45 + 0.75 * sh), 0, 255).astype(np.uint8)


class Frame:
    """World (x, z) to pixel for a raster box drawn at `ppm` pixels per metre with an offset."""

    def __init__(self, x0, z0, ppm, ox=0, oy=0):
        self.x0, self.z0, self.ppm, self.ox, self.oy = x0, z0, ppm, ox, oy

    def __call__(self, x, z):
        return (self.ox + (x - self.x0) * self.ppm, self.oy + (z - self.z0) * self.ppm)

    def pts(self, pl):
        return [self(float(p[0]), float(p[1])) for p in pl]


def contours(dr, H, fr, origin, step, levels, colour, width=1, every_bold=None, bold=None):
    """Marching-squares contour segments of H (raster origin `origin` = (x0, z0), `step` m) drawn in frame fr."""
    for lv in levels:
        a = H - lv
        s00, s10, s01, s11 = a[:-1, :-1], a[:-1, 1:], a[1:, :-1], a[1:, 1:]
        cross = ((s00 > 0) != (s10 > 0)) | ((s00 > 0) != (s01 > 0)) | ((s11 > 0) != (s10 > 0)) | ((s11 > 0) != (s01 > 0))
        jj, ii = np.nonzero(cross)
        col = bold if (every_bold and bold and abs(lv % every_bold) < 1e-6) else colour
        for j, i in zip(jj, ii):
            v = [a[j, i], a[j, i + 1], a[j + 1, i + 1], a[j + 1, i]]
            c = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            p = []
            for k in range(4):
                u, w = v[k], v[(k + 1) % 4]
                if (u > 0) != (w > 0):
                    t = u / (u - w)
                    p.append((c[k][0] + t * (c[(k + 1) % 4][0] - c[k][0]), c[k][1] + t * (c[(k + 1) % 4][1] - c[k][1])))
            if len(p) >= 2:
                q = [fr(origin[0] + px * step, origin[1] + pz * step) for px, pz in p[:2]]
                dr.line(q, fill=col, width=width)


def new(w, h, bg=(250, 250, 247)):
    img = Image.new("RGB", (w, h), bg)
    return img, ImageDraw.Draw(img)
