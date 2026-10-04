"""Eight ambient fish, a first model pass (2026-10-03) for the prop library's
PRP-WILD-017 to 021 and 026 to 028: the salmon, trout and striped bass of the
fresh and brackish water (and the ocean, by season), and the halibut, surf
perch, tuna, rockfish and eel of the pier and the bay. None has a photograph of
Christina's; each is the plainest reading of its species in the house style,
for her to reshape. Card: `documentation/howto/model-the-fish.md`.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<fish>.blend --python tools/blender/wildlife_fish.py -- \\
        [--replace] [--save] [--render <folder>]

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \\
        --python tools/blender/wildlife_fish.py -- --lineup <folder>

`<fish>` is `salmon`, `trout`, `striped_bass`, `halibut`, `surf_perch`, `tuna`,
`rockfish` or `eel`. The tool builds whichever the file is named for into
`export`, one object a part, head toward -Y here (+Z in Godot), real metres,
Z up. It refuses while `export` holds anything (it may be hers) unless
`--replace`; it writes the file only with `--save`; `--render` shoots
three-quarter, front, side and top views, one beside a 1.0 m ruler and one
`posed` (tail swung, jaw dropped, pectorals out, the moray in an S) into the
folder, after the save, so the render's camera, sun, ground, ruler and pose
never reach the file. `--lineup` builds all eight in a throwaway scene and
renders `fish.png`, every fish side on at true relative size with the ruler,
and `fish_same_length.png`, every fish brought to one length so the shapes
compare; nothing is saved.

**One body, eight tables.** A fish is a loft: a table of cross-sections per
species (`SPECIES[...]["rows"]`: along the body from snout to the root of the
tail, each row a half-width, a back height and a belly depth, all fractions of
the fish's length) run through a Catmull-Rom spline and sampled into rings of
an egg-shaped section (the back pinched by `ridge`, round for the tuna, sharp
for the perch), a pole at the snout and a cap at the tail root. The fins are
thin plates whose outline is the silhouette: a dorsal or anal fin is drawn as
heights above the back or below the belly at stations along it, its base
sunk into the body; a paddle (pectoral, pelvic) is an outline in its own
plane, raked back from the body side; the caudal fin is an outline behind the
tail root. A free-edge point may carry a third number, the share of the usual
corner rounding it gets: the rockfish's spine tips and the tuna's crescent
tips are nearly sharp. The eyes are domed discs lying on the head's surface.
The lower jaw is a shell of the head's underside from the hinge to the snout,
a lip proud of the body at the front that sinks into it toward the hinge, so
the mouth reads as a line, nothing steps out at the hinge, and the jaw can
drop open; `jut` pushes its tip past the snout (the bass's and rockfish's
underbite). Scales, bars, stripes, spots, fin rays and spines are paint for
later: the spines and rays show in the texture's cut-out, not in triangles.

**The moray is different.** Its dorsal and anal fins are thick skin folds
that run unbroken from the nape round the tail to mid-belly, so they are not
plates: the body's own section grows a crest above and a keel below
(`crest`, heights along the body), and the body is five pieces in a chain.
Each piece after the head starts exactly where the one before ends, ring on
ring, and carries a short collar, a smaller ring tucked inside the piece in
front; when a joint bends, the opening on the outside of the bend shows that
collar, not a hole.

**Frame and pivots.** Lowest point on z = 0, centred on the origin in plan,
swimming level; the placement scene puts each in the water and turns it. The
moving parts hang under empties at their joints: `tail_pivot` at the tail
root (the caudal fin; swing about Z), `jaw_pivot` at the jaw hinge (the lower
jaw; swing about X), `pectoral_left_pivot` and `pectoral_right_pivot` at the
fin bases. Left is +X (the fish faces -Y). The moray's body hangs in a chain,
`segment_1_pivot` to `segment_4_pivot`, each the parent of the next, swinging
about Z, so a wave can run down it later. The halibut's pivots are turned
with its body as it is laid down, so on every fish a pivot's own axes mean
the same (its tail beats about its pivot's local Z, which points along world
-X once it lies flat). No armature, no animation.

**Sizes and assumptions** (typical adult, total length):

- `salmon`, Chinook salmon, ocean-bright adult, 0.90 m: fusiform, a small
  pointed head, one dorsal fin at mid-body, an adipose fin, a broad
  shallow-forked tail.
- `trout`, rainbow trout, 0.45 m: chunkier than the salmon for its length, a
  blunt round head with a bigger eye, an adipose fin, a near-square tail.
- `striped_bass`, striped bass, 0.75 m: a long head with a jutting lower
  jaw, an arched back, two separate dorsal fins (the spiny one a tall
  triangle), a deeply forked tail.
- `halibut`, California halibut, 0.70 m: built as an upright fish, very
  compressed and oval, then laid on its right (blind) side, the left-eyed
  form; both eyes on the up side, the dorsal and anal fins long fringes along
  both edges, a rounded tail, one pectoral fin lying flat on the eyed side
  (the blind side's is left out: it would lie under the body).
- `surf_perch`, barred surfperch, 0.30 m: a deep compressed disc, a small
  mouth and a big eye, one long dorsal with a dip between the spiny and soft
  parts, a forked tail.
- `tuna`, yellowfin tuna, 1.40 m: a torpedo with a round section and a conical
  head, a very narrow tail root, a lunate (crescent) tail, sickle second
  dorsal and anal fins, long sickle pectorals, eight finlets above and below.
- `rockfish`, vermilion rockfish, 0.50 m: a big deep head, a big eye, a big
  upturned mouth with the lower jaw jutting, a long spiny dorsal (five spine
  tips) running into a taller soft dorsal, big fan pectorals, a square tail.
- `eel`, California moray, 1.00 m: long and compressed, no pectoral or pelvic
  fins, a big head with a raised nape and a long mouth, a small eye, the fin
  crest from the nape round the pointed tail and forward under the belly to
  mid-body; five body pieces.

Budget: at most 1,200 triangles a fish, the tuna and moray 1,500 (counted by
the tool). Stand-in materials: skin, fin and the two eye materials. Every part
is `kyt_collision = "none"`: nothing walks into a fish.
"""

import math
import os
import sys
from bisect import bisect_right

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

TAU = math.tau
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))

# stand-in colours for the painting to replace
EYE_RING = (0.90, 0.85, 0.55, 1.0)
EYE_PUPIL = (0.02, 0.02, 0.02, 1.0)
SKIN = {"salmon": (0.55, 0.62, 0.66, 1.0), "trout": (0.45, 0.55, 0.42, 1.0),
        "striped_bass": (0.50, 0.56, 0.60, 1.0), "halibut": (0.42, 0.38, 0.30, 1.0),
        "surf_perch": (0.70, 0.68, 0.55, 1.0), "tuna": (0.22, 0.30, 0.45, 1.0),
        "rockfish": (0.75, 0.25, 0.16, 1.0), "eel": (0.35, 0.40, 0.25, 1.0)}
FIN = {"salmon": (0.38, 0.42, 0.46, 1.0), "trout": (0.50, 0.42, 0.36, 1.0),
       "striped_bass": (0.32, 0.36, 0.40, 1.0), "halibut": (0.34, 0.30, 0.24, 1.0),
       "surf_perch": (0.55, 0.50, 0.38, 1.0), "tuna": (0.80, 0.68, 0.20, 1.0),
       "rockfish": (0.60, 0.20, 0.14, 1.0), "eel": (0.22, 0.26, 0.15, 1.0)}

ORDER = ("tuna", "eel", "salmon", "striped_bass", "halibut", "rockfish", "trout", "surf_perch")
BUDGET = {"tuna": 1500, "eel": 1500}
BUDGET_DEFAULT = 1200

# --- the species tables ------------------------------------------------------
#
# Everything is a fraction of the fish's total length L. `rows` run along the
# body from the snout (u = 0, a pole) to the tail root (u = 1): (u, half-width,
# back height above the axis, belly depth below it). `body` is the body's
# share of L; the caudal fin takes the rest. A dorsal or anal fin is
# (name, u0, u1, [(u, height[, rounding]), ...]) with the free edge listed
# from the rear forward; a paddle is (name, u, elevation, direction, plane
# hint, length, width, pivot); the caudal is its free outline as (behind the
# root, height[, rounding]), top lobe first. The eye is (u, elevation,
# radius); the jaw is (hinge u, hinge depth as a share of the belly there,
# jut ahead of the snout).

SPECIES = {
    "salmon": dict(
        length=0.90, body=0.82, ridge=0.25, sides=14, stations=16, snout_z=0.0,
        rows=[(0, 0, 0, 0), (0.03, 0.024, 0.026, 0.024), (0.10, 0.044, 0.060, 0.056),
              (0.22, 0.058, 0.090, 0.085), (0.40, 0.062, 0.110, 0.100), (0.60, 0.055, 0.095, 0.085),
              (0.78, 0.040, 0.060, 0.052), (0.92, 0.024, 0.036, 0.032), (1.0, 0.020, 0.032, 0.028)],
        dorsal=[("dorsal_fin", 0.42, 0.56, [(0.58, 0.035), (0.50, 0.085), (0.43, 0.095)]),
                ("adipose_fin", 0.80, 0.85, [(0.86, 0.018), (0.84, 0.034), (0.81, 0.024)])],
        anal=[("anal_fin", 0.64, 0.76, [(0.78, 0.030), (0.70, 0.065), (0.65, 0.075)])],
        paddles=[("pectoral", 0.25, -35, (0.45, 0.85, -0.25), (0.30, 0.0, 1.0), 0.12, 0.050, True),
                 ("pelvic", 0.52, -62, (0.35, 0.85, -0.35), (0.55, 0.0, 0.8), 0.08, 0.036, False)],
        caudal=[(0.04, 0.090), (0.18, 0.135, 0.6), (0.13, 0.0), (0.18, -0.135, 0.6), (0.04, -0.090)],
        eye=(0.08, 15, 0.024), jaw=(0.17, 0.5, 0.0)),
    "trout": dict(
        length=0.45, body=0.82, ridge=0.22, sides=14, stations=16, snout_z=0.0,
        rows=[(0, 0, 0, 0), (0.03, 0.034, 0.038, 0.032), (0.10, 0.056, 0.082, 0.072),
              (0.23, 0.064, 0.112, 0.098), (0.42, 0.066, 0.125, 0.108), (0.60, 0.058, 0.105, 0.090),
              (0.78, 0.040, 0.066, 0.056), (0.92, 0.027, 0.042, 0.036), (1.0, 0.023, 0.038, 0.032)],
        dorsal=[("dorsal_fin", 0.40, 0.55, [(0.57, 0.040), (0.50, 0.090), (0.42, 0.095)]),
                ("adipose_fin", 0.79, 0.85, [(0.86, 0.020), (0.84, 0.040), (0.80, 0.028)])],
        anal=[("anal_fin", 0.62, 0.75, [(0.77, 0.035), (0.70, 0.075), (0.63, 0.080)])],
        paddles=[("pectoral", 0.24, -35, (0.45, 0.85, -0.25), (0.30, 0.0, 1.0), 0.13, 0.058, True),
                 ("pelvic", 0.50, -62, (0.35, 0.85, -0.35), (0.55, 0.0, 0.8), 0.09, 0.042, False)],
        caudal=[(0.04, 0.105), (0.16, 0.130), (0.15, 0.0), (0.16, -0.130), (0.04, -0.105)],
        eye=(0.085, 18, 0.034), jaw=(0.17, 0.5, 0.0)),
    "striped_bass": dict(
        length=0.75, body=0.82, ridge=0.28, sides=14, stations=16, snout_z=0.0,
        rows=[(0, 0, 0, 0), (0.03, 0.028, 0.034, 0.030), (0.10, 0.050, 0.084, 0.068),
              (0.22, 0.064, 0.128, 0.098), (0.38, 0.070, 0.150, 0.110), (0.55, 0.062, 0.130, 0.100),
              (0.72, 0.046, 0.085, 0.068), (0.90, 0.028, 0.046, 0.040), (1.0, 0.024, 0.040, 0.034)],
        dorsal=[("dorsal_fin_spiny", 0.28, 0.43, [(0.44, 0.020), (0.33, 0.125, 0.4), (0.29, 0.060)]),
                ("dorsal_fin_soft", 0.50, 0.64, [(0.66, 0.035), (0.60, 0.075), (0.52, 0.090), (0.505, 0.060)])],
        anal=[("anal_fin", 0.60, 0.72, [(0.74, 0.030), (0.66, 0.070), (0.61, 0.080)])],
        paddles=[("pectoral", 0.27, -20, (0.45, 0.85, -0.25), (0.30, 0.0, 1.0), 0.13, 0.055, True),
                 ("pelvic", 0.34, -62, (0.35, 0.85, -0.35), (0.55, 0.0, 0.8), 0.09, 0.040, False)],
        caudal=[(0.03, 0.075), (0.18, 0.145, 0.3), (0.09, 0.0), (0.18, -0.145, 0.3), (0.03, -0.075)],
        eye=(0.085, 22, 0.026), jaw=(0.22, 0.5, 0.012)),
    "halibut": dict(
        length=0.70, body=0.84, ridge=0.20, sides=14, stations=16, snout_z=0.0, pose="flat",
        rows=[(0, 0, 0, 0), (0.03, 0.014, 0.040, 0.035), (0.10, 0.024, 0.100, 0.085),
              (0.25, 0.030, 0.165, 0.145), (0.45, 0.030, 0.190, 0.170), (0.62, 0.028, 0.170, 0.155),
              (0.78, 0.024, 0.110, 0.100), (0.92, 0.018, 0.050, 0.045), (1.0, 0.016, 0.040, 0.036)],
        dorsal=[("dorsal_fin", 0.10, 0.90, [(0.91, 0.020), (0.80, 0.070), (0.55, 0.100), (0.30, 0.090), (0.12, 0.040)])],
        anal=[("anal_fin", 0.35, 0.90, [(0.91, 0.020), (0.80, 0.070), (0.55, 0.090), (0.36, 0.050)])],
        paddles=[("pectoral", 0.30, 10, (0.10, 0.95, 0.20), (1.0, 0.0, 0.0), 0.10, 0.045, "left")],
        caudal=[(0.03, 0.080), (0.11, 0.115), (0.140, 0.040), (0.140, -0.040), (0.11, -0.115), (0.03, -0.080)],
        eye=(0.09, 20, 0.028), eye_b=(0.13, 62, 0.028), jaw=(0.22, 0.5, 0.0)),
    "surf_perch": dict(
        length=0.30, body=0.80, ridge=0.35, sides=14, stations=16, snout_z=0.0,
        rows=[(0, 0, 0, 0), (0.03, 0.018, 0.035, 0.032), (0.10, 0.034, 0.090, 0.080),
              (0.25, 0.044, 0.170, 0.140), (0.45, 0.046, 0.225, 0.190), (0.62, 0.040, 0.190, 0.160),
              (0.78, 0.030, 0.110, 0.095), (0.92, 0.020, 0.050, 0.045), (1.0, 0.018, 0.042, 0.038)],
        dorsal=[("dorsal_fin", 0.30, 0.80, [(0.81, 0.030), (0.72, 0.090), (0.62, 0.065), (0.52, 0.060), (0.42, 0.060), (0.32, 0.045)])],
        anal=[("anal_fin", 0.55, 0.80, [(0.81, 0.030), (0.72, 0.080), (0.57, 0.060)])],
        paddles=[("pectoral", 0.30, -15, (0.45, 0.85, -0.20), (0.30, 0.0, 1.0), 0.10, 0.045, True),
                 ("pelvic", 0.42, -65, (0.35, 0.85, -0.35), (0.55, 0.0, 0.8), 0.06, 0.030, False)],
        caudal=[(0.03, 0.060), (0.17, 0.120, 0.5), (0.11, 0.0), (0.17, -0.120, 0.5), (0.03, -0.060)],
        eye=(0.10, 25, 0.040), jaw=(0.12, 0.35, 0.0)),
    "tuna": dict(
        length=1.40, body=0.84, ridge=0.10, sides=16, stations=18, snout_z=0.0,
        rows=[(0, 0, 0, 0), (0.03, 0.028, 0.028, 0.028), (0.10, 0.062, 0.062, 0.060),
              (0.27, 0.092, 0.110, 0.100), (0.42, 0.098, 0.125, 0.115), (0.60, 0.085, 0.105, 0.095),
              (0.78, 0.052, 0.062, 0.056), (0.92, 0.022, 0.028, 0.026), (1.0, 0.016, 0.020, 0.018)],
        dorsal=[("dorsal_fin_spiny", 0.36, 0.48, [(0.49, 0.020), (0.38, 0.090), (0.37, 0.070)]),
                ("dorsal_fin_soft", 0.58, 0.63, [(0.64, 0.030), (0.72, 0.090), (0.76, 0.140, 0.3), (0.66, 0.110), (0.59, 0.050)])],
        anal=[("anal_fin", 0.61, 0.66, [(0.67, 0.030), (0.75, 0.090), (0.79, 0.130, 0.3), (0.69, 0.100), (0.62, 0.050)])],
        finlets=[("dorsal_finlets", "dorsal", 0.67, 0.90, 8, 0.024), ("anal_finlets", "anal", 0.69, 0.90, 8, 0.022)],
        paddles=[("pectoral", 0.27, -10, (0.30, 0.92, -0.12), (0.25, 0.0, 1.0), 0.22, 0.050, True),
                 ("pelvic", 0.33, -62, (0.35, 0.85, -0.35), (0.55, 0.0, 0.8), 0.06, 0.030, False)],
        caudal=[(0.03, 0.070), (0.10, 0.140), (0.16, 0.170, 0.3), (0.12, 0.100), (0.07, 0.020),
                (0.07, -0.020), (0.12, -0.100), (0.16, -0.170, 0.3), (0.10, -0.140), (0.03, -0.070)],
        eye=(0.10, 10, 0.022), jaw=(0.17, 0.4, 0.0)),
    "rockfish": dict(
        length=0.50, body=0.82, ridge=0.28, sides=14, stations=16, snout_z=0.016,
        rows=[(0, 0, 0, 0), (0.03, 0.034, 0.044, 0.036), (0.10, 0.066, 0.112, 0.092),
              (0.24, 0.080, 0.168, 0.138), (0.38, 0.078, 0.178, 0.142), (0.56, 0.064, 0.150, 0.125),
              (0.75, 0.046, 0.098, 0.082), (0.92, 0.030, 0.060, 0.052), (1.0, 0.026, 0.052, 0.046)],
        dorsal=[("dorsal_fin_spiny", 0.27, 0.58, [(0.59, 0.050), (0.555, 0.088, 0.3), (0.53, 0.058, 0.0),
                                                   (0.495, 0.098, 0.3), (0.465, 0.064, 0.0), (0.43, 0.104, 0.3),
                                                   (0.40, 0.066, 0.0), (0.365, 0.102, 0.3), (0.335, 0.064, 0.0),
                                                   (0.30, 0.090, 0.3), (0.28, 0.050)]),
                ("dorsal_fin_soft", 0.60, 0.78, [(0.79, 0.050), (0.73, 0.100), (0.65, 0.095), (0.605, 0.070)])],
        anal=[("anal_fin", 0.62, 0.76, [(0.77, 0.050), (0.72, 0.095), (0.64, 0.085)])],
        paddles=[("pectoral", 0.33, -22, (0.50, 0.80, -0.30), (0.30, 0.0, 1.0), 0.17, 0.100, True),
                 ("pelvic", 0.40, -62, (0.35, 0.85, -0.35), (0.55, 0.0, 0.8), 0.09, 0.045, False)],
        caudal=[(0.03, 0.080), (0.15, 0.115), (0.145, 0.0), (0.15, -0.115), (0.03, -0.080)],
        eye=(0.12, 28, 0.052), jaw=(0.25, 0.55, 0.014)),
    "eel": dict(
        length=1.00, body=1.0, ridge=0.20, sides=12, rings_per_u=30, snout_z=0.0, eye_sides=8,
        rows=[(0, 0, 0, 0), (0.012, 0.016, 0.016, 0.016), (0.03, 0.028, 0.034, 0.030),
              (0.06, 0.036, 0.052, 0.044), (0.10, 0.040, 0.062, 0.050), (0.15, 0.040, 0.062, 0.050),
              (0.24, 0.036, 0.052, 0.046), (0.40, 0.032, 0.047, 0.044), (0.60, 0.026, 0.044, 0.041),
              (0.78, 0.018, 0.038, 0.036), (0.90, 0.010, 0.028, 0.026), (0.96, 0.005, 0.016, 0.015),
              (1.0, 0, 0, 0)],
        # the fleshy base the fins rise from: (u, ridge over the back, keel under the belly)
        crest=[(0.0, 0.0, 0.0), (0.12, 0.0, 0.0), (0.20, 0.006, 0.0), (0.48, 0.006, 0.0),
               (0.56, 0.006, 0.006), (1.0, 0.004, 0.004)],
        crest_power=12,
        # the fin plates over it: (u, dorsal height, anal depth); dorsal from the
        # nape, anal from mid-body, both round the tail tip
        fin=[(0.0, 0.0, 0.0), (0.13, 0.0, 0.0), (0.22, 0.014, 0.0), (0.50, 0.018, 0.0),
             (0.58, 0.019, 0.012), (0.85, 0.024, 0.020), (0.95, 0.020, 0.018), (1.0, 0.014, 0.014)],
        fin_from=(0.13, 0.50),
        segments=[(0.0, 0.20), (0.20, 0.40), (0.40, 0.60), (0.60, 0.80), (0.80, 1.0)],
        collar=0.03,
        eye=(0.05, 36, 0.014), jaw=(0.12, 0.45, 0.0)),
}


# --- building blocks ---------------------------------------------------------

def material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Roughness"].default_value = 0.6
    mat.diffuse_color = colour
    return mat


def export():
    return bpy.data.collections["export"]


def cr_spline(rows):
    """Catmull-Rom through `rows` of (u, *values), knots at the rows' own u,
    the ends held; returns f(u) -> tuple, every value clamped at zero."""
    us = [r[0] for r in rows]
    vals = [tuple(r[1:]) for r in rows]
    n = len(rows)

    def f(u):
        u = min(max(u, us[0]), us[-1])
        i = max(0, min(n - 2, bisect_right(us, u) - 1))
        i0, i1, i2, i3 = max(i - 1, 0), i, i + 1, min(i + 2, n - 1)
        t1, t2 = us[i1], us[i2]
        t0 = us[i0] if i0 != i1 else t1 - (t2 - t1)
        t3 = us[i3] if i3 != i2 else t2 + (t2 - t1)
        out = []
        for k in range(len(vals[0])):
            p0, p1, p2, p3 = vals[i0][k], vals[i1][k], vals[i2][k], vals[i3][k]
            a1 = (t1 - u) / (t1 - t0) * p0 + (u - t0) / (t1 - t0) * p1
            a2 = (t2 - u) / (t2 - t1) * p1 + (u - t1) / (t2 - t1) * p2
            a3 = (t3 - u) / (t3 - t2) * p2 + (u - t2) / (t3 - t2) * p3
            b1 = (t2 - u) / (t2 - t0) * a1 + (u - t0) / (t2 - t0) * a2
            b2 = (t3 - u) / (t3 - t1) * a2 + (u - t1) / (t3 - t1) * a3
            out.append(max((t2 - u) / (t2 - t1) * b1 + (u - t1) / (t2 - t1) * b2, 0.0))
        return tuple(out)
    return f


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def round_corners(points, radii, segs=2):
    """A closed polygon with each corner of radius > 0 replaced by an arc. The
    trim never takes more than 45% of either neighbouring edge."""
    n = len(points)
    out = []
    for i, p in enumerate(points):
        r = radii[i]
        a, b = points[i - 1], points[(i + 1) % n]
        da, db = (a - p), (b - p)
        la, lb = da.length, db.length
        if r <= 0 or la < 1e-9 or lb < 1e-9:
            out.append(p)
            continue
        da, db = da / la, db / lb
        cosang = max(-0.999, min(0.999, da.dot(db)))
        ang = math.acos(cosang)
        if ang > math.radians(176):
            out.append(p)
            continue
        trim = r / math.tan(ang / 2)
        trim = min(trim, 0.45 * la, 0.45 * lb)
        pa, pb = p + da * trim, p + db * trim
        # the arc as a quadratic bezier through the corner, close enough
        for k in range(segs + 1):
            t = k / segs
            out.append((1 - t) ** 2 * pa + 2 * (1 - t) * t * p + t ** 2 * pb)
    return out


def plate(points, normal, thick):
    """A closed planar outline thickened into a slab, `thick` across `normal`."""
    bm = bmesh.new()
    n = Vector(normal).normalized()
    near = [bm.verts.new(p - n * (thick / 2)) for p in points]
    far = [bm.verts.new(p + n * (thick / 2)) for p in points]
    bm.faces.new(list(reversed(near)))
    bm.faces.new(far)
    m = len(points)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return bm


def join(bms):
    out = bmesh.new()
    for bm in bms:
        me = bpy.data.meshes.new("_join")
        bm.to_mesh(me)
        bm.free()
        out.from_mesh(me)
        bpy.data.meshes.remove(me)
    return out


def lathe(profile, sides, mats=None):
    """An (r, z) outline revolved about Z, bottom to top; a point with r = 0
    is a pole. `mats` gives each band between rings a material index."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(TAU * i / sides), r * math.sin(TAU * i / sides), z))
                          for i in range(sides)])
    for b, (ra, rb) in enumerate(zip(rings, rings[1:])):
        for i in range(sides):
            j = (i + 1) % sides
            if len(ra) == 1 and len(rb) == 1:
                continue
            if len(ra) == 1:
                f = bm.faces.new((ra[0], rb[i], rb[j]))
            elif len(rb) == 1:
                f = bm.faces.new((ra[i], ra[j], rb[0]))
            else:
                f = bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
            if mats:
                f.material_index = mats[b]
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return bm


def transform(bm, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return bm


def frame_matrix(origin, z_axis, hint=Vector((0.0, 1.0, 0.0))):
    """A frame at `origin` with local Z along `z_axis`."""
    z = Vector(z_axis).normalized()
    x = hint.cross(z)
    if x.length < 1e-6:
        x = Vector((1.0, 0.0, 0.0)).cross(z)
    x.normalize()
    y = z.cross(x)
    m = Matrix.Identity(4)
    m.col[0][:3], m.col[1][:3], m.col[2][:3], m.col[3][:3] = x, y, z, Vector(origin)
    return m


def free_edge(item):
    """A free-edge point (a, b[, rounding]) as (a, b, rounding)."""
    return item[0], item[1], (item[2] if len(item) > 2 else 1.0)


# --- the fish ----------------------------------------------------------------

class Fish:
    """The parts and pivots of one fish, in metres, built in a frame with the
    snout at -L/2 on the Y axis and the body's axis on z = 0; `finish` shifts
    the lot onto the house frame."""

    def __init__(self, name, spec):
        self.name = name
        self.spec = spec
        self.L = spec["length"]
        self.Lb = self.L * spec["body"]
        self.y0 = -self.L / 2
        self.profile = cr_spline(spec["rows"])
        self.crest = cr_spline(spec["crest"]) if "crest" in spec else None
        # fins are thin plates: thick enough to read as a fin edge-on, never a slab
        self.thick = min(max(0.008 * self.L, 0.003), 0.010)
        self.sink = 0.6 * self.thick + 0.008 * self.L
        self.parts = []      # (name, bmesh, material names, pivot name or None)
        self.pivots = []     # (name, location, parent name or None), parents first
        self.sagittal = 0    # a different thickness for every plate in the x = 0 plane

    # the body as a surface -----------------------------------------------

    def y(self, u):
        return self.y0 + u * self.Lb

    def zc(self, u):
        """The axis: level, with the snout lifted for an upturned mouth."""
        return self.L * self.spec["snout_z"] * max(0.0, 1.0 - u / 0.3) ** 2

    def section(self, u, scale=1.0):
        w, zt, zb = (v * self.L * scale for v in self.profile(u))
        return w, zt, zb

    def point(self, u, th, scale=1.0):
        """The surface point at station u, angle th round the section (0 at
        the left side, +X; pi/2 at the back). A moray's section grows its fin
        crest at the back and its keel at the belly."""
        w, zt, zb = self.section(u, scale)
        c, s = math.cos(th), math.sin(th)
        x = w * c * (1.0 - self.spec["ridge"] * max(s, 0.0) ** 2)
        z = (zt if s >= 0 else zb) * s
        if self.crest:
            top, keel = (v * self.L * scale for v in self.crest(u))
            g = abs(s) ** self.spec["crest_power"]
            z += (top if s >= 0 else -keel) * g
        return Vector((x, self.y(u), z + self.zc(u)))

    def normal(self, u, th):
        d = 0.004
        du = self.point(min(u + d, 1.0), th) - self.point(max(u - d, 0.002), th)
        dt = self.point(u, th + d) - self.point(u, th - d)
        n = du.cross(dt).normalized()
        p = self.point(u, th)
        if n.dot(Vector((p.x, 0.0, p.z - self.zc(u)))) < 0:
            n = -n
        return n

    def back(self, u):
        return self.zc(u) + self.section(u)[1]

    def belly(self, u):
        return self.zc(u) - self.section(u)[2]

    def ring(self, u, scale=1.0):
        return [self.point(u, TAU * i / self.spec["sides"], scale) for i in range(self.spec["sides"])]

    def loft(self, us, front, back, scale=None, sharp_at=None):
        """Rings at the stations `us`; `front` and `back` are 'pole' or 'cap'.
        The edges of the ring at station `sharp_at` are marked sharp, so the
        shading breaks there (a moray piece's front edge, over its collar)."""
        bm = bmesh.new()
        rings = []
        if front == "pole":
            rings.append([bm.verts.new(self.point(0.0, 0.0))])
        for u in us:
            s = scale(u) if scale else 1.0
            rings.append([bm.verts.new(p) for p in self.ring(u, s)])
        if back == "pole":
            rings.append([bm.verts.new(self.point(1.0, 0.0))])
        sides = self.spec["sides"]
        for ra, rb in zip(rings, rings[1:]):
            for i in range(sides):
                j = (i + 1) % sides
                if len(ra) == 1:
                    bm.faces.new((ra[0], rb[j], rb[i]))
                elif len(rb) == 1:
                    bm.faces.new((ra[i], ra[j], rb[0]))
                else:
                    bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
        if front == "cap":
            bm.faces.new(rings[0])
        if back == "cap":
            bm.faces.new(list(reversed(rings[-1])))
        if sharp_at is not None:
            ring = rings[us.index(sharp_at) + (1 if front == "pole" else 0)]
            for i in range(sides):
                e = bm.edges.get((ring[i], ring[(i + 1) % sides]))
                if e:
                    e.smooth = False
        return bm

    def stations(self, u0, u1, count, ease_front, ease_back):
        """`count` stations from u0 to u1, open at a pole end so the pole
        itself is not among them; cosine-eased toward an eased end."""
        out = []
        for i in range(count + 1):
            t = i / count
            if ease_front and ease_back:
                t = 0.5 * (1 - math.cos(math.pi * t))
            elif ease_front:
                t = 1 - math.cos(0.5 * math.pi * t)
            elif ease_back:
                t = math.sin(0.5 * math.pi * t)
            out.append(u0 + (u1 - u0) * t)
        if ease_front:
            out = out[1:]
        if ease_back:
            out = out[:-1]
        return out

    # parts ----------------------------------------------------------------

    def add(self, name, bm, mats, pivot=None):
        self.parts.append((name, bm, mats, pivot))

    def pivot(self, name, loc, parent=None):
        self.pivots.append((name, Matrix.Translation(Vector(loc)), parent))

    def body(self):
        us = self.stations(0.0, 1.0, self.spec["stations"], True, False)
        self.add("body", self.loft(us, "pole", "cap"), ["skin"])

    def sagittal_plate(self, name, pts, mats=("fin",), pivot=None, thick=None):
        """A fin in the fish's own plane (x = 0); each a hair different in
        thickness so no two ever share a face where they overlap inside."""
        self.sagittal += 1
        t = (thick or self.thick) * (1.0 + 0.015 * self.sagittal)
        self.add(name, plate(pts, (1.0, 0.0, 0.0), t), list(mats), pivot)

    def dorsal(self, name, u0, u1, free, below=False):
        """A fin along the back (or the belly with `below`): its base sunk
        along the body line between u0 and u1, its free edge the given
        (u, height[, rounding]) points from the rear forward, corners rounded."""
        sgn = -1.0 if below else 1.0
        line = self.belly if below else self.back
        nb = max(2, int(round((u1 - u0) * 12)))
        pts, radii = [], []
        for k in range(nb + 1):
            u = u0 + (u1 - u0) * k / nb
            pts.append(Vector((0.0, self.y(u), line(u) - sgn * self.sink)))
            radii.append(0.0)
        r = 0.012 * self.L
        for item in free:
            u, h, k = free_edge(item)
            pts.append(Vector((0.0, self.y(u), line(min(u, 1.0)) + sgn * h * self.L)))
            radii.append(r * k)
        self.sagittal_plate(name, round_corners(pts, radii))

    def finlets(self, name, where, u0, u1, count, h):
        """A row of small swept triangles between the second dorsal (or anal)
        and the tail, one part; plain triangles, too small to round."""
        below = where == "anal"
        sgn = -1.0 if below else 1.0
        line = self.belly if below else self.back
        bms = []
        self.sagittal += 1
        t = self.thick * (0.8 + 0.03 * self.sagittal)
        half = 0.012 * self.L
        for k in range(count):
            u = u0 + (u1 - u0) * k / (count - 1)
            pts = [Vector((0.0, self.y(u) - half, line(u) - sgn * self.sink)),
                   Vector((0.0, self.y(u) + half, line(u) - sgn * self.sink)),
                   Vector((0.0, self.y(u) + 1.6 * half, line(u) + sgn * h * self.L))]
            bms.append(plate(pts, (1.0, 0.0, 0.0), t))
        self.add(name, join(bms), ["fin"])

    def caudal(self, free):
        """The tail fin behind the tail root, hung on `tail_pivot`."""
        u_end = 1.0
        y_end = self.y(u_end)
        _, zt, zb = self.section(u_end)
        root = Vector((0.0, y_end, self.zc(u_end)))
        self.pivot("tail_pivot", root - Vector((0.0, 0.02 * self.L, 0.0)))
        pts = [Vector((0.0, y_end - 0.03 * self.L, self.zc(u_end) + zt * 0.55))]
        radii = [0.0]
        for item in free:
            d, z, k = free_edge(item)
            pts.append(Vector((0.0, y_end + d * self.L, self.zc(u_end) + z * self.L)))
            radii.append(0.010 * self.L * k)
        pts.append(Vector((0.0, y_end - 0.03 * self.L, self.zc(u_end) - zb * 0.55)))
        radii.append(0.0)
        self.sagittal_plate("caudal_fin", round_corners(pts, radii), pivot="tail_pivot")

    def paddle(self, name, u, elev, direction, plane, length, width, pivot):
        """A pectoral or pelvic fin: an outline in its own plane, raked back
        from the body side at station u, `elev` degrees above the lateral
        line. `pivot` True hangs each under `<name>_<side>_pivot`; "left"
        builds the left one only."""
        sides = ("left",) if pivot == "left" else ("left", "right")
        # the left fin, in its frame: `a` out along the fin, `h` across it in
        # its plane, `n` the plane's normal; the right one is its mirror
        base = self.point(u, math.radians(elev))
        a = Vector(direction).normalized()
        h = Vector(plane).cross(a).normalized()
        n = a.cross(h).normalized()
        Lf, W = length * self.L, width * self.L
        outline = [(-self.sink, 0.5 * W), (0.55 * Lf, 0.55 * W), (Lf, 0.08 * W), (0.6 * Lf, -0.42 * W), (-self.sink, -0.5 * W)]
        left = round_corners([base + a * p + h * q for p, q in outline], [0.0, 0.25 * W, 0.12 * W, 0.25 * W, 0.0])
        for side in sides:
            if side == "left":
                pts, normal, origin = left, n, base
            else:
                pts = [Vector((-p.x, p.y, p.z)) for p in reversed(left)]
                normal, origin = Vector((-n.x, n.y, n.z)), Vector((-base.x, base.y, base.z))
            piv = None
            if pivot:
                piv = f"{name}_{side}_pivot"
                self.pivot(piv, origin)
            self.add(f"{name}_fin_{side}", plate(pts, normal, self.thick * 0.9), ["fin"], piv)

    def eye(self, name, u, elev, r, side):
        """A domed disc on the head's surface, pupil in the middle."""
        th = math.radians(elev) if side == "left" else math.pi - math.radians(elev)
        p, n = self.point(u, th), self.normal(u, th)
        R = r * self.L
        dome = 0.45 * R
        profile = [(0.0, dome), (0.45 * R, 0.86 * dome), (0.80 * R, 0.5 * dome), (R, 0.0), (0.92 * R, -0.5 * R)]
        bm = lathe(profile, self.spec.get("eye_sides", 10), mats=[1, 0, 0, 0])
        transform(bm, frame_matrix(p - n * 0.02 * R, n))
        self.add(name, bm, ["eye_ring", "eye_pupil"])

    def jaw(self, u_hinge, depth, jut=0.0, pivot="jaw_pivot"):
        """The lower jaw: the head's underside from the hinge to the snout as
        a shell, its top the mouth line, a plane from the snout down to the
        hinge. Along the front it stands a lip proud of the body; toward the
        hinge it sinks just inside it, so nothing steps out there and an open
        jaw keeps its back end in the head. `jut` (a share of L) pushes the
        tip ahead of the snout, an underbite."""
        K, S = 9, 6
        z_hinge = self.zc(u_hinge) - depth * self.section(u_hinge)[2]
        z_snout = self.zc(0.0) - 0.004 * self.L
        u_nose = 0.025
        bm = bmesh.new()
        rings = []
        for s in range(S + 1):
            t = s / S
            u = u_nose + (u_hinge - u_nose) * t
            w, zt, zb = self.section(u)
            z_top = z_snout + (z_hinge - z_snout) * (u / u_hinge)
            sink = smoothstep(0.5, 1.0, t)
            proud = 1.04 - 0.07 * sink              # 4% proud at the lip, 3% inside at the hinge
            off = 0.003 * self.L * (1.0 - sink)
            y = self.y(u) - jut * self.L * (1.0 - t) ** 1.5
            s0 = max(0.0, min(0.95, (self.zc(u) - z_top) / max(zb, 1e-6)))
            phi0 = math.asin(s0)
            ring = []
            for k in range(K):
                phi = phi0 + (math.pi - 2 * phi0) * k / (K - 1)
                x = (w * proud + off) * math.cos(phi)
                z = self.zc(u) - (zb * proud + off) * math.sin(phi)
                if k in (0, K - 1):
                    z = z_top
                ring.append(bm.verts.new((x, y, z)))
            rings.append(ring)
        for ra, rb in zip(rings, rings[1:]):
            for k in range(K - 1):
                bm.faces.new((ra[k], ra[k + 1], rb[k + 1], rb[k]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        lid = [r[0] for r in rings] + [r[K - 1] for r in reversed(rings)]
        bm.faces.new(lid)
        self.pivot(pivot, (0.0, self.y(u_hinge), z_hinge))
        self.add("lower_jaw", bm, ["skin"], pivot)

    # the species ----------------------------------------------------------

    def build(self):
        sp = self.spec
        if "segments" in sp:
            self.build_segments()
        else:
            self.body()
            self.caudal(sp["caudal"])
        for name, u0, u1, free in sp.get("dorsal", ()):
            self.dorsal(name, u0, u1, free)
        for name, u0, u1, free in sp.get("anal", ()):
            self.dorsal(name, u0, u1, free, below=True)
        for name, where, u0, u1, count, h in sp.get("finlets", ()):
            self.finlets(name, where, u0, u1, count, h)
        for name, u, elev, direction, plane, length, width, pivot in sp.get("paddles", ()):
            self.paddle(name, u, elev, direction, plane, length, width, pivot)
        eu, ee, er = sp["eye"]
        if "eye_b" in sp:   # a flatfish: both eyes on the one side
            bu, be, br = sp["eye_b"]
            self.eye("eye_left", eu, ee, er, "left")
            self.eye("eye_right", bu, be, br, "left")
        else:
            self.eye("eye_left", eu, ee, er, "left")
            self.eye("eye_right", eu, ee, er, "right")
        self.jaw(*sp["jaw"])

    def build_segments(self):
        """The moray: the body in pieces at the joints, its fleshy fin base
        (`crest`) part of each piece's section. A piece after the head starts
        on the ring where the one before ends and reaches forward inside it
        as a collar, a ring at 85% of the section, so a bent joint opens onto
        skin, not a hole. Each piece hangs on a pivot at its front joint, the
        parent of the next, and carries its own stretch of fin plate; the
        plates meet end to end at the joints, never overlapping, so no two
        share a face."""
        sp = self.spec
        segs = sp["segments"]
        d_from, a_from = sp["fin_from"]
        parent = None
        for k, (ua, ub) in enumerate(segs):
            first, last = k == 0, k == len(segs) - 1
            count = max(3, int(round((ub - ua) * sp["rings_per_u"])))
            us = self.stations(ua, ub, count, first, last)
            scale, sharp = None, None
            piv = None
            if not first:
                us = [ua - sp["collar"]] + us
                scale = (lambda u, ua=ua: 0.85 if u < ua - 1e-9 else 1.0)
                sharp = ua
                piv = f"segment_{k}_pivot"
                self.pivot(piv, (0.0, self.y(ua), self.zc(ua)), parent)
                parent = piv
            part = "head" if first else ("tail" if last else f"segment_{k}")
            self.add(part, self.loft(us, "pole" if first else "cap", "pole" if last else "cap",
                                     scale, sharp), ["skin"], piv)
            if last:
                self.moray_tail_fin(ua, piv)
                continue
            if ub > d_from:
                self.ribbon(f"dorsal_fin_{k}", max(ua, d_from), ub, False, piv)
            if ub > a_from:
                self.ribbon(f"anal_fin_{k}", max(ua, a_from), ub, True, piv)

    def fin_line(self, u, below):
        """The top of the moray's dorsal fin (or the bottom of its anal fin)
        at station u, and the body line its base sinks under."""
        top, keel = (v * self.L for v in self.crest(u))
        hd, ha = (v * self.L for v in cr_spline(self.spec["fin"])(u))
        if below:
            return self.belly(u) - keel - ha, self.belly(u) + self.sink
        return self.back(u) + top + hd, self.back(u) - self.sink

    def ribbon(self, name, u0, u1, below, pivot):
        n = max(2, int(round((u1 - u0) * 20)))
        us = [u0 + (u1 - u0) * i / n for i in range(n + 1)]
        base = [Vector((0.0, self.y(u), self.fin_line(u, below)[1])) for u in us]
        edge = [Vector((0.0, self.y(u), self.fin_line(u, below)[0])) for u in reversed(us)]
        self.sagittal_plate(name, base + edge, pivot=pivot)

    def moray_tail_fin(self, ua, pivot):
        """The dorsal and anal fins of the last piece, one leaf round the
        pointed tail: along the back to the tip, round it, forward under the
        belly, its inner edge a line down through the body at the joint."""
        n = 5
        us = [ua + (1.0 - ua) * math.sin(0.5 * math.pi * i / n) for i in range(n + 1)]
        top = [Vector((0.0, self.y(u), self.fin_line(u, False)[0])) for u in us]
        bottom = [Vector((0.0, self.y(u), self.fin_line(u, True)[0])) for u in reversed(us)]
        z_top, z_bot = top[-1].z, bottom[0].z
        r = 0.5 * (z_top - z_bot)
        zm = 0.5 * (z_top + z_bot)
        tip = [Vector((0.0, self.y(1.0) + r * math.sin(a), zm + r * math.cos(a)))
               for a in (math.pi * i / 4 for i in range(1, 4))]
        inner = [Vector((0.0, self.y(ua), self.fin_line(ua, True)[1])),
                 Vector((0.0, self.y(ua), self.fin_line(ua, False)[1]))]
        self.sagittal_plate("tail_fin", top + tip + bottom + inner, pivot=pivot)

    # finishing -------------------------------------------------------------

    def finish(self):
        """Lay a flatfish on its side, bring the whole fish, snout to tail
        tip, to exactly its stated length, then put the lowest point on z = 0
        and the plan centre on the origin."""
        if self.spec.get("pose") == "flat":
            # the left (eyed) side up: +X to +Z
            rot = Matrix.Rotation(math.radians(-90.0), 4, "Y")
            for _, bm, _, _ in self.parts:
                transform(bm, rot)
            # the pivots turn with it, so on every fish a pivot's own axes
            # mean the same: the tail and pectorals swing about local Z, the
            # jaw opens about local X
            self.pivots = [(n, rot @ m, p) for n, m, p in self.pivots]

        def extent():
            lo = Vector((1e9, 1e9, 1e9))
            hi = Vector((-1e9, -1e9, -1e9))
            for _, bm, _, _ in self.parts:
                for v in bm.verts:
                    lo = Vector(map(min, lo, v.co))
                    hi = Vector(map(max, hi, v.co))
            return lo, hi

        lo, hi = extent()
        k = self.L / (hi.y - lo.y)
        for _, bm, _, _ in self.parts:
            transform(bm, Matrix.Scale(k, 4))
        self.pivots = [(n, Matrix.Translation(m.translation * k) @ m.to_3x3().to_4x4(), p)
                       for n, m, p in self.pivots]
        lo, hi = extent()
        shift = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
        for _, bm, _, _ in self.parts:
            transform(bm, Matrix.Translation(shift))
        self.pivots = [(n, Matrix.Translation(shift) @ m, p) for n, m, p in self.pivots]
        return hi - lo

    def realize(self, collection, prefix=""):
        """Objects in `collection`: empties at the pivots (parents first) and
        a mesh per part, its vertices relative to its pivot."""
        mats = {"skin": material(f"{self.name}_skin", SKIN[self.name]),
                "fin": material(f"{self.name}_fin", FIN[self.name]),
                "eye_ring": material("fish_eye_ring", EYE_RING),
                "eye_pupil": material("fish_eye_pupil", EYE_PUPIL)}
        empties, where = {}, {}
        for name, m, parent in self.pivots:
            e = bpy.data.objects.new(prefix + name, None)
            e.empty_display_type = "PLAIN_AXES"
            e.empty_display_size = 0.06 * self.L
            collection.objects.link(e)
            where[name] = m
            if parent:
                e.parent = empties[parent]
                e.matrix_basis = where[parent].inverted() @ m
            else:
                e.matrix_basis = m
            e["kyt_collision"] = "none"
            empties[name] = e
        objects = []
        for name, bm, mat_names, pivot in self.parts:
            if pivot:
                transform(bm, where[pivot].inverted())
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            for f in bm.faces:
                f.smooth = True
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(40.0):
                    e.smooth = False
            me = bpy.data.meshes.new(prefix + name)
            bm.to_mesh(me)
            bm.free()
            for m in mat_names:
                me.materials.append(mats[m])
            o = bpy.data.objects.new(prefix + name, me)
            collection.objects.link(o)
            if pivot:
                o.parent = empties[pivot]
            o["kyt_collision"] = "none"
            objects.append(o)
        return objects, list(empties.values())


def build(name, collection, prefix=""):
    fish = Fish(name, SPECIES[name])
    fish.build()
    size = fish.finish()
    objects, empties = fish.realize(collection, prefix)
    return fish, objects, empties, size


# --- measuring ---------------------------------------------------------------

def triangles(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
        ev.to_mesh_clear()
    return n


def points(objs):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def bounds(objs):
    pts = points(objs)
    return Vector(map(min, *pts)), Vector(map(max, *pts))


def report(name, objects, empties):
    parts = [o for o in objects if o.type == "MESH"]
    total = triangles(parts)
    lo, hi = bounds(parts)
    budget = BUDGET.get(name, BUDGET_DEFAULT)
    print(f"wildlife_fish: {name}: {len(parts)} parts, {len(empties)} pivots, {total} triangles (budget {budget})")
    print("  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts))
    print("  pivots: " + ", ".join(f"{e.name}" + (f" under {e.parent.name}" if e.parent else "") for e in empties))
    print(f"  size: {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x L x H), "
          f"x {lo.x:.3f}..{hi.x:.3f}, y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.3f}..{hi.z:.3f}")
    checks = []
    if total > budget:
        checks.append(f"FAIL over budget: {total} > {budget}")
    if abs(lo.z) > 0.002:
        checks.append(f"FAIL lowest point at z = {lo.z:.4f}")
    if abs((lo.x + hi.x) / 2) > 0.002 or abs((lo.y + hi.y) / 2) > 0.002:
        checks.append("FAIL not centred in plan")
    head = next(o for o in parts if o.name.endswith("lower_jaw"))
    hp = bounds([head])
    if hp[0].y > 0:
        checks.append("FAIL the jaw is not toward -Y")
    for o in list(parts) + list(empties):
        if o.get("kyt_collision") != "none":
            checks.append(f"FAIL {o.name} collides")
    for line in checks or ["checks ok"]:
        print("  " + line)
    return total


# --- renders ---------------------------------------------------------------

def stage_scene():
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
    try:
        scene.eevee.taa_render_samples = 24
    except AttributeError:
        pass
    world = bpy.data.worlds.new("w")
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.80, 0.80, 0.78, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.4
    sun.rotation_euler = (math.radians(50), math.radians(12), math.radians(40))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 40
    stage.objects.link(cam)
    scene.camera = cam
    return scene, stage, cam


def stage_mesh(stage, name, bm, colour):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material(f"render_{name}", colour))
    o = bpy.data.objects.new(name, me)
    stage.objects.link(o)
    return o


def box(x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[i] for i in f])
    return bm


def ruler(stage, at, along="y", tag=""):
    """A 1.0 m bar of ten decimetres in two colours, from `at` along +Y (or +X)."""
    out = []
    for i in range(10):
        a, b = i * 0.1, (i + 1) * 0.1
        if along == "y":
            bm = box(at[0] - 0.015, at[0] + 0.015, at[1] + a, at[1] + b, at[2], at[2] + 0.03)
        else:
            bm = box(at[0] + a, at[0] + b, at[1] - 0.015, at[1] + 0.015, at[2], at[2] + 0.03)
        colour = (0.12, 0.12, 0.13, 1) if i % 2 == 0 else (0.92, 0.90, 0.85, 1)
        out.append(stage_mesh(stage, f"ruler{tag}_{i}", bm, colour))
    return out


def label(stage, text, at, size, colour=(0.08, 0.08, 0.09, 1)):
    """Text facing +X (the side camera), reading along +Y, standing on Z."""
    cu = bpy.data.curves.new("label", type="FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    cu.extrude = 0.0
    o = bpy.data.objects.new("label", cu)
    o.data.materials.append(material("render_label", colour))
    o.location = at
    o.rotation_euler = (math.radians(90), 0.0, math.radians(90))
    stage.objects.link(o)
    return o


def shoot(scene, cam, folder, tag, objs, direction, lens=40, top=False):
    """Back the camera off along `direction` from the middle of `objs` until
    they all fit with a margin. `top` looks straight down, the fish lying
    across the frame with its head to the left as in the side view."""
    pts = points(objs)
    lo, hi = Vector(map(min, *pts)), Vector(map(max, *pts))
    centre = (lo + hi) / 2
    d = Vector(direction).normalized()
    dist = max((hi - lo).length * 0.4, 0.15)
    cam.data.type = "PERSP"
    cam.data.lens = lens
    for _ in range(200):
        cam.location = centre + d * dist
        if top:
            cam.rotation_euler = (0.0, 0.0, math.radians(90))
        else:
            cam.location.z = max(cam.location.z, 0.03)
            cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if all(0.06 <= c.x <= 0.94 and 0.06 <= c.y <= 0.94 and c.z > 0
               for c in (world_to_camera_view(scene, cam, p) for p in pts)):
            break
        dist *= 1.04
    scene.render.filepath = os.path.join(folder, f"{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath)


def render(folder, name, objects):
    os.makedirs(folder, exist_ok=True)
    scene, stage, cam = stage_scene()
    scene.render.resolution_x, scene.render.resolution_y = 1400, 900
    parts = [o for o in objects if o.type == "MESH"]
    lo, hi = bounds(parts)
    ground = stage_mesh(stage, "ground", box(-40, 40, -40, 40, -0.02, -0.001), (0.56, 0.55, 0.52, 1))
    for tag, d in (("three_quarter", (-0.75, -1.0, 0.55)), ("front", (0.0, -1.0, 0.12)),
                   ("side", (1.0, 0.0, 0.12))):
        shoot(scene, cam, folder, f"{name}_{tag}", parts, d)
    shoot(scene, cam, folder, f"{name}_top", parts, (0.0, 0.0, 1.0), top=True)
    bar = ruler(stage, (hi.x + 0.12, -0.5, 0.0))
    shoot(scene, cam, folder, f"{name}_scale", parts + bar, (1.0, -0.45, 0.45))
    for o in bar:
        bpy.data.objects.remove(o)
    # the pivots at work, for review only (the file was saved straight): the
    # tail swung, the jaw dropped, the pectorals out, the moray in an S
    swings = {"tail_pivot": ("Z", 25), "jaw_pivot": ("X", 22),
              "pectoral_left_pivot": ("Z", -30), "pectoral_right_pivot": ("Z", 30),
              "segment_1_pivot": ("Z", 18), "segment_2_pivot": ("Z", -26),
              "segment_3_pivot": ("Z", -22), "segment_4_pivot": ("Z", 30)}
    for e in export().all_objects:
        if e.type == "EMPTY" and e.name in swings:
            axis, deg = swings[e.name]
            e.matrix_basis = e.matrix_basis @ Matrix.Rotation(math.radians(deg), 4, axis)
    shoot(scene, cam, folder, f"{name}_posed", parts, (-0.55, -1.0, 0.9))
    bpy.data.objects.remove(ground)


def lineup(folder):
    """All eight in one throwaway scene, side on, heads to the left, in two
    rows (the four longest above), each fish standing on its row's line."""
    os.makedirs(folder, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.data.collections.new("export")
    bpy.context.scene.collection.children.link(coll)
    scene, stage, cam = stage_scene()
    scene.render.resolution_x = 3000
    roots = {}
    for name in ORDER:
        fish, objects, empties, size = build(name, coll, prefix=f"{name}__")
        report(name, objects, empties)
        root = bpy.data.objects.new(f"{name}_root", None)
        coll.objects.link(root)
        for o in objects + empties:
            if o.parent is None:
                o.parent = root
        if name == "halibut":
            # lies flat in its file; stood on its edge here so its shape shows
            root.rotation_euler = (0.0, math.radians(90.0), 0.0)
        roots[name] = (root, objects)
    cam.data.type = "ORTHO"
    rows = (ORDER[:4], ORDER[4:])
    gap, text, label_room = 0.22, 0.06, 0.34

    def place(same_length):
        """Lay the rows out from the top down; returns the meshes framed."""
        framed = []
        top = 0.0
        for r, row in enumerate(rows):
            sized = []
            for name in row:
                root, objects = roots[name]
                s = (1.0 / SPECIES[name]["length"]) if same_length else 1.0
                root.location = (0.0, 0.0, 0.0)
                root.scale = (s, s, s)
                lo, hi = bounds(objects)
                sized.append((name, root, objects, lo, hi))
            base = top - max(hi.z - lo.z for *_, lo, hi in sized)
            y = 0.0
            for name, root, objects, lo, hi in sized:
                root.location = (0.0, y - lo.y, base - lo.z)
                words = f"{name.replace('_', ' ')}\n{SPECIES[name]['length']:.2f} m"
                if name == "halibut":
                    words += "\n(on edge here)"
                label(stage, words, (0.0, y + (hi.y - lo.y) / 2, base - 0.10), text)
                framed += objects
                y += (hi.y - lo.y) + gap
            if r == len(rows) - 1 and not same_length:
                framed += ruler(stage, (0.0, y, base))
                label(stage, "1.0 m ruler", (0.0, y + 0.5, base - 0.10), text)
                y += 1.0
            framed.append(stage_mesh(stage, f"ruler_line_{r}", box(-0.01, 0.01, -0.1, y - gap + 0.1, base - 0.004, base - 0.001),
                                     (0.45, 0.44, 0.42, 1)))
            top = base - label_room
        return framed

    for same, tag in ((False, "fish"), (True, "fish_same_length")):
        for o in [o for o in stage.objects if o.name.startswith(("label", "ruler"))]:
            bpy.data.objects.remove(o)
        pts = points(place(same))
        lo, hi = Vector(map(min, *pts)), Vector(map(max, *pts))
        z_lo, z_hi = lo.z - label_room + 0.06, hi.z + 0.08
        span = hi.y - lo.y + 0.4
        # the frame as tall as the rows and their labels need, no taller
        scene.render.resolution_y = int(round(scene.render.resolution_x * (z_hi - z_lo) / span))
        cam.data.ortho_scale = span
        cam.location = (6.0, (lo.y + hi.y) / 2, (z_lo + z_hi) / 2)
        cam.rotation_euler = (math.radians(90), 0.0, math.radians(90))
        scene.render.filepath = os.path.join(folder, f"{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--lineup" in argv:
        lineup(argv[argv.index("--lineup") + 1])
        return
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    name = name[:-len("_source")] if name.endswith("_source") else name
    if name not in SPECIES:
        raise SystemExit(f"wildlife_fish: open one of {', '.join(SPECIES)}, not {name!r}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"wildlife_fish: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    fish, objects, empties, size = build(name, coll)
    report(name, objects, empties)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name, objects)


main()
