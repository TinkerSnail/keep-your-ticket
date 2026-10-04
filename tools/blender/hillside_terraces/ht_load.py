"""Load the sampled master for the design phase (system Python)."""

import json
import os

import numpy as np

from ht_geom import bilinear
from ht_site import NEAR, FAR, over_sea


class Site:
    def __init__(self, folder):
        S = np.load(os.path.join(folder, "ht_sample.npz"))
        self.nx, self.nz = S["nx"], S["nz"]
        self.E = over_sea(S["NH"])                 # the design raster, metres over the sea
        self.fx, self.fz = S["fx"], S["fz"]
        self.FE = over_sea(S["FH"])                # the backdrop
        self.X, self.Z = np.meshgrid(self.nx, self.nz)
        self.verts = {k[2:]: S[k] for k in S.files if k.startswith("v_")}
        with open(os.path.join(folder, "ht_refs.json")) as f:
            self.refs = json.load(f)
        self.hw_line = np.array([(p[0], p[1]) for p in self.refs["coast_highway_centreline"]])

    @classmethod
    def from_arrays(cls, nx, nz, NH, fx, fz, FH, refs):
        """The same site from rasters sampled in Blender (Godot heights), for the edit tool."""
        self = cls.__new__(cls)
        self.nx, self.nz, self.E = nx, nz, over_sea(NH)
        self.fx, self.fz, self.FE = fx, fz, over_sea(FH)
        self.X, self.Z = np.meshgrid(self.nx, self.nz)
        self.verts = {}
        self.refs = refs
        self.hw_line = np.array([(p[0], p[1]) for p in refs["coast_highway_centreline"]])
        return self

    def Ef(self, x, z):
        """Existing ground over the sea at a point (the design raster, else the backdrop)."""
        if NEAR["x0"] <= x <= NEAR["x1"] - 1 and NEAR["z0"] <= z <= NEAR["z1"] - 1:
            return float(bilinear(self.E, NEAR["x0"], NEAR["z0"], NEAR["step"], x, z))
        return float(bilinear(self.FE, FAR["x0"], FAR["z0"], FAR["step"], x, z))

    def Ea(self, x, z):
        """Vectorised: existing ground at arrays x, z (near raster where inside, backdrop elsewhere)."""
        x, z = np.asarray(x, float), np.asarray(z, float)
        inn = (x >= NEAR["x0"]) & (x <= NEAR["x1"] - 1) & (z >= NEAR["z0"]) & (z <= NEAR["z1"] - 1)
        out = bilinear(self.FE, FAR["x0"], FAR["z0"], FAR["step"], x, z)
        if inn.any():
            out = np.where(inn, bilinear(self.E, NEAR["x0"], NEAR["z0"], NEAR["step"], x, z), out)
        return out
