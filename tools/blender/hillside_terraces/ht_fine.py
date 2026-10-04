"""The patch rasters for the scratch copy: today's ground and each variant's
design at 0.5 m over the hole (a 10 m lattice rectangle round all three
footprints), with each cell classed for colour. Volumes stay on the 1 m grid."""

import numpy as np

from ht_geom import bilinear
from ht_site import NEAR
from ht_surface import design

LATTICE = 10.0
FINE = 0.5
CLASSES = ("natural", "street", "steps", "pad", "wall", "slope")


def rect_of(moved_masks):
    m = np.zeros_like(moved_masks[0])
    for k in moved_masks:
        m |= k
    jj, ii = np.nonzero(m)
    x0 = np.floor((NEAR["x0"] + ii.min()) / LATTICE) * LATTICE - LATTICE
    x1 = np.ceil((NEAR["x0"] + ii.max()) / LATTICE) * LATTICE + LATTICE
    z0 = np.floor((NEAR["z0"] + jj.min()) / LATTICE) * LATTICE - LATTICE
    z1 = np.ceil((NEAR["z0"] + jj.max()) / LATTICE) * LATTICE + LATTICE
    return float(max(x0, NEAR["x0"])), float(min(x1, NEAR["x1"])), float(max(z0, NEAR["z0"])), float(min(z1, NEAR["z1"]))


def classify(E, D, owner, kinds, step, pad_slope=0.6):
    gz, gx = np.gradient(D, step)
    slope = np.hypot(gx, gz)
    moved = np.abs(D - E) > 0.05
    cls = np.zeros(D.shape, dtype=np.int8)                  # natural
    own = owner >= 0
    k_of = np.array(kinds + ["street"])[np.where(own, owner, len(kinds))]
    cls[moved & ~own & (slope <= pad_slope)] = 3             # pad
    cls[moved & ~own & (slope > pad_slope)] = 5              # planted slope
    cls[moved & ~own & (slope > 2.5)] = 4                    # wall
    stepped = (k_of == "steps") | (k_of == "lane")
    cls[own & ~stepped] = 1
    cls[own & stepped] = 2
    return cls


def grid(r, step):
    xs = np.arange(r[0], r[1] + 1e-6, step)
    zs = np.arange(r[2], r[3] + 1e-6, step)
    return np.meshgrid(xs, zs)


def fine(site, variants, moved_masks, regrades):
    """variants: {key: elements} designed at FINE; regrades: {key: (D raster, owner raster, elements)} at 1 m (smooth
    ground needs no finer). Today's patch is at 1 m too. Returns arrays for the npz."""
    r = rect_of(moved_masks)
    X, Z = grid(r, FINE)
    E = bilinear(site.E, NEAR["x0"], NEAR["z0"], NEAR["step"], X, Z)
    X1, Z1 = grid(r, 1.0)
    E1 = bilinear(site.E, NEAR["x0"], NEAR["z0"], NEAR["step"], X1, Z1)
    out = {"fine_rect": np.array(r), "fine_E": E1, "fine_step_today": 1.0}
    for v, els in variants.items():
        D, owner, prot = design(els, X, Z, E, site.hw_line, 1.0)
        D = np.where(np.abs(D - E) > 0.05, D, E)
        assert np.array_equal(D[prot], E[prot])
        out[f"fine_D_{v}"] = D
        out[f"fine_step_{v}"] = FINE
        out[f"fine_cls_{v}"] = classify(E, D, owner, [e["kind"] for e in els], FINE)
    i0, j0 = int(r[0] - NEAR["x0"]), int(r[2] - NEAR["z0"])
    for v, (Dr, own, els) in regrades.items():
        D = Dr[j0:j0 + E1.shape[0], i0:i0 + E1.shape[1]]
        ow = own[j0:j0 + E1.shape[0], i0:i0 + E1.shape[1]]
        ctx = np.array([e["kind"] == "context" for e in els] + [False])
        ow = np.where(ctx[np.where(ow >= 0, ow, len(els))], -1, ow)      # the terrace streets are context, not drawn as new
        out[f"fine_D_{v}"] = D
        out[f"fine_step_{v}"] = 1.0
        out[f"fine_cls_{v}"] = classify(E1, D, ow, [e["kind"] for e in els], 1.0, pad_slope=0.05)
    return out
