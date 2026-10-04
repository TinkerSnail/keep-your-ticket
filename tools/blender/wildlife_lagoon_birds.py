"""The tidal lagoon's wading birds, a first model pass (2026-10-03) for the
prop library's PRP-WILD-035 heron, 036 egrets and 037 shorebirds, which
Christina added that day ("lets add those too", of the lagoon plan in
`documentation/maps/entrance-landscaping.html`: herons and egrets on the
marsh, shorebirds on the flats). None has a photograph of hers or a greybox:
each is the plainest readable reading of a Southern California species in the
house style, chunky and rounded (`prop-pipeline.md`, Standards applied), for
her to reshape.

    /Applications/Blender.app/Contents/MacOS/Blender --background \\
        assets/source/props/<bird>.blend --python tools/blender/wildlife_lagoon_birds.py -- \\
        [--replace] [--save] [--render <folder>]

    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \\
        --python tools/blender/wildlife_lagoon_birds.py -- --lineup <png>

`<bird>` is `heron` (PRP-WILD-035), `egret` (036) or `shorebird` (037). The tool
builds whichever the file is named for into `export`, one object a part, real
metres, Z up, the head toward -Y (+Z in Godot), the toes on z = 0 and the
plan centred on the origin. It refuses while `export` holds anything (it may be
hers) unless `--replace`; it writes the file only with `--save`; `--render`
shoots three-quarter, front, side and top views and one beside a 1.7 m box,
for every variant, and the variants side by side, into the folder (saved
first, so the render rig never reaches the file). `--lineup` builds all five
birds in an empty scene and renders them in a row at true relative size beside
the 1.7 m box and the adult gull, imported from `assets/wildlife/gull_adult.glb`
at the 0.47 its Godot scene (`scenes/wildlife/gull.tscn`) scales it by; nothing
is saved in that mode.

**Articulation.** As the gull (`assets/source/wildlife/gull_adult.blend`),
every moving part hangs under an empty at its joint, with the part's vertices
in that pivot's frame, so turning the pivot swings the part; pivots are never
rotated or scaled, so a part's local frame is the world's. The names are the
gull's: `head_pivot`, `upper_pivot` and `lower_pivot` (the bill's halves, both
at the gape), `wing_left`, `wing_right`, `leg_left`, `leg_right`; added for
the long necks and legs, `neck_pivot` at the neck's root in the chest,
`neck_upper_pivot` at the S-bend, and `ankle_left`, `ankle_right` at the
heel (the joint that bends backward). The chain is `neck_pivot` >
`neck_upper_pivot` > `head_pivot` > `upper_pivot`, `lower_pivot`; and
`leg_<side>` > `ankle_<side>`. Every bird has the same parts:

- `body` (no pivot);
- `neck_lower` (`neck_pivot`), `neck_upper` (`neck_upper_pivot`);
- `head`, `eye_left`, `eye_right` and any `plume_<n>` (`head_pivot`);
- `bill_upper` (`upper_pivot`), `bill_lower` (`lower_pivot`);
- `folded_wing_left`, `folded_wing_right` (`wing_left`, `wing_right`);
- `thigh_<side>` (`leg_<side>`), `shin_<side>` and `foot_<side>`
  (`ankle_<side>`).

Left is the bird's own left, +X here. The neck's segments, the legs' and the
head end in rounded caps that lie inside their neighbours, so a turned joint
shows no gap. No armature, no animation, no Godot behaviour: how each moves
is a separate decision. Every part is `kyt_collision = none`: ambient wildlife
never blocks the player. In a file built in variants, every part and pivot
also carries `kyt_variant` and ends in `_<variant>` (`head_pivot_great`), each
variant in its own `variant_<v>` collection under `export`, the second hidden
in the viewport because they stand in the same place.

**Heron** (PRP-WILD-035, `heron`): a great blue heron, adult, the lagoon's
big wader, standing in a neutral upright stance, the body tilted up about 30
degrees, the neck drawn into a clear S, the bill level and a little down.
About 1.04 m to the crown, 0.89 m from bill tip to wing tip; the bill
0.17 m from the gape, the tarsus (the bare shin) 0.2 m, the bare thigh
showing about 0.19 m below the belly. Two chunky occipital plumes trail off the
back of the head. Stand-ins: blue-grey plumage, yellow bill, olive legs, dark
eyes and plumes.

**Egret** (PRP-WILD-036, `egret`), two variants:
- `great`: a great egret, adult, 0.95 m to the crown and 0.69 m long, the
  heron's body plan but slimmer, with a longer, thinner neck in a deep S;
  white, with a yellow bill (0.12 m from the gape) and black legs and feet.
- `snowy`: a snowy egret, adult, the great egret's shape at 0.63 of its size
  (0.60 m to the crown, 0.43 m long), with a slimmer black bill, black legs
  thickened a little past scale so they still read, yellow feet, and three
  chunky plumes trailing back off the nape, their tips curling up (the
  breeding crest, read down to a few big pieces; the back and breast plumes
  are left out).

**Shorebird** (PRP-WILD-037, `shorebird`), two variants, both standing level:
- `sandpiper`: a western sandpiper, adult, small and plump, 0.11 m to the
  crown and 0.20 m from bill tip to wing tip; short black legs (the tarsus
  about 22 mm) and a short bill (about 28 mm past the forehead) drooping a
  little over its last third.
- `godwit`: a marbled godwit, adult, 0.33 m to the crown and 0.46 m from bill
  tip to wing tip; long dark grey legs (the tarsus about 80 mm) and a very
  long bill (0.12 m from the gape) curving slightly up, pink at the base (its
  black outer half is paint).

The legs are drawn chunkier than life (two to three times a real tarsus), so
they read at a distance; the heads are a little big and the necks a little
thick, for the same reason. Feather patterns, the heron's face stripes and
breast plumes, the egrets' lores, the shorebirds' streaks and white bellies,
the godwit's bill tip and every eye's iris are paint for later. The materials
are flat stand-ins by surface, four or five a bird.
"""

import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

TAU = math.tau
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
GULL_GLB = os.path.join(ROOT, "assets", "wildlife", "gull_adult.glb")
GULL_GAME_SCALE = 0.47      # scenes/wildlife/gull.tscn's `visual` node

# colours are stand-ins for the painting
COLOURS = {
    "plumage_blue_grey": (0.33, 0.40, 0.50, 1.0),
    "plumage_white": (0.92, 0.92, 0.89, 1.0),
    "plumage_grey_brown": (0.50, 0.44, 0.37, 1.0),
    "plumage_cinnamon": (0.64, 0.46, 0.28, 1.0),
    "bill_yellow": (0.92, 0.68, 0.10, 1.0),
    "bill_black": (0.035, 0.035, 0.035, 1.0),
    "bill_pink": (0.80, 0.48, 0.46, 1.0),
    "legs_olive": (0.38, 0.36, 0.24, 1.0),
    "legs_black": (0.045, 0.045, 0.045, 1.0),
    "legs_dark_grey": (0.20, 0.21, 0.22, 1.0),
    "feet_yellow": (0.95, 0.76, 0.08, 1.0),
    "eye_dark": (0.025, 0.025, 0.03, 1.0),
}

BUDGET = {"heron": 2000, "egret": 1500, "shorebird": 1500}   # triangles, each variant

# Resolution: sides round each kind of part, and Catmull-Rom samples a span.
RES_HERON = {"body": 12, "body_per": 2, "neck": 8, "neck_per": 2, "head": 8, "head_per": 2,
             "bill": 4, "bill_per": 2, "eye": (8, 4), "wing": 6, "wing_per": 2, "leg": 6, "toe": 4,
             "plume": 4, "plume_per": 2}
RES_EGRET = {"body": 12, "body_per": 1, "neck": 8, "neck_per": 2, "head": 8, "head_per": 2,
             "bill": 4, "bill_per": 2, "eye": (6, 4), "wing": 6, "wing_per": 2, "leg": 6, "toe": 3,
             "plume": 4, "plume_per": 1}
RES_SNOWY = dict(RES_EGRET, body=10)
RES_SHORE = dict(RES_EGRET, neck_per=1)

# --- the birds -------------------------------------------------------------
#
# Each bird is written once, in its own frame: x across (the bird's left +X),
# y along (the head toward -Y), z up. `body` runs tail to chest, (y, z, half
# width, half height); `neck` from its root inside the chest to the head,
# (y, z, radius), split at control `kink` into the two segments; `head` back
# to front, (y, z, half width, half height); `bill` gape to tip, (y, z, half
# width, upper half height, lower half height), its spine the mouth line;
# `eye` the left eye's (x, y, z, radius); `wing` the left folded wing,
# shoulder to tip, (x, y, z, half thickness, half height), leaning in at the
# top by `wing_lean`; `leg` the left leg, hip to heel to the foot's ground
# point, (x, y, z, radius); `toes` (front length, hind length, radius, spread
# in degrees); `plumes` tapering tubes (x, y, z, radius) off the head. After
# building, the bird is moved so its toes are on z = 0 and its plan is
# centred on the origin.

HERON = {
    "res": RES_HERON,
    "mats": {"plumage": "plumage_blue_grey", "bill": "bill_yellow", "legs": "legs_olive",
             "feet": "legs_olive", "eye": "eye_dark", "plume": "eye_dark"},
    "seam": 0.0015, "pivot_size": 0.035,
    "body": [(0.38, 0.35, 0.040, 0.014), (0.29, 0.395, 0.066, 0.044), (0.17, 0.46, 0.092, 0.088),
             (0.05, 0.525, 0.100, 0.102), (-0.06, 0.595, 0.093, 0.098), (-0.13, 0.655, 0.076, 0.080)],
    # the S: out of the breast and forward, back at the bend, forward again
    # into the head
    "neck": [(-0.09, 0.64, 0.058), (-0.17, 0.69, 0.048), (-0.235, 0.739, 0.042), (-0.25, 0.797, 0.037),
             (-0.215, 0.851, 0.034), (-0.17, 0.896, 0.032), (-0.165, 0.941, 0.032), (-0.19, 0.968, 0.032),
             (-0.215, 0.977, 0.031)],
    "kink": 4,
    "head": [(-0.19, 0.985, 0.030, 0.032), (-0.232, 0.990, 0.044, 0.047), (-0.282, 0.985, 0.039, 0.040),
             (-0.318, 0.976, 0.026, 0.027)],
    "bill": [(-0.30, 0.970, 0.018, 0.018, 0.0125), (-0.36, 0.960, 0.0145, 0.0135, 0.0105),
             (-0.42, 0.948, 0.0095, 0.0085, 0.0065), (-0.465, 0.937, 0.0, 0.0, 0.0)],
    "eye": (0.033, -0.275, 0.998, 0.012),
    "plumes": [[(0.010, -0.195, 1.012, 0.010), (0.013, -0.15, 1.005, 0.008), (0.015, -0.10, 0.985, 0.0055),
                (0.016, -0.06, 0.96, 0.0)],
               [(-0.010, -0.195, 1.012, 0.010), (-0.013, -0.15, 1.005, 0.008), (-0.015, -0.10, 0.985, 0.0055),
                (-0.016, -0.06, 0.96, 0.0)]],
    "wing": [(0.068, -0.11, 0.64, 0.022, 0.045), (0.084, -0.02, 0.605, 0.028, 0.080),
             (0.088, 0.10, 0.542, 0.026, 0.088), (0.075, 0.22, 0.47, 0.020, 0.066),
             (0.055, 0.33, 0.402, 0.013, 0.036), (0.035, 0.425, 0.35, 0.0, 0.0)],
    "wing_lean": 0.55,
    "leg": {"thigh": [(0.045, 0.060, 0.47, 0.040), (0.047, 0.072, 0.355, 0.023), (0.048, 0.082, 0.235, 0.0195)],
            "shin": [(0.048, 0.082, 0.235, 0.0195), (0.049, 0.058, 0.13, 0.016), (0.050, 0.032, 0.032, 0.017)],
            "foot": (0.050, 0.030)},
    "toes": (0.105, 0.05, 0.0095, 32.0),
}

GREAT_EGRET = {
    "res": RES_EGRET,
    "mats": {"plumage": "plumage_white", "bill": "bill_yellow", "legs": "legs_black",
             "feet": "legs_black", "eye": "eye_dark", "plume": "plumage_white"},
    "seam": 0.0012, "pivot_size": 0.03,
    "body": [(0.30, 0.42, 0.030, 0.011), (0.23, 0.455, 0.050, 0.034), (0.13, 0.505, 0.069, 0.069),
             (0.03, 0.555, 0.075, 0.077), (-0.06, 0.61, 0.068, 0.071), (-0.11, 0.65, 0.054, 0.058)],
    # a longer, thinner S than the heron's
    "neck": [(-0.08, 0.64, 0.044), (-0.155, 0.70, 0.032), (-0.19, 0.775, 0.027), (-0.165, 0.84, 0.025),
             (-0.13, 0.885, 0.024), (-0.138, 0.915, 0.023), (-0.165, 0.926, 0.021)],
    "kink": 3,
    "head": [(-0.138, 0.922, 0.020, 0.022), (-0.168, 0.926, 0.028, 0.029), (-0.203, 0.922, 0.025, 0.025),
             (-0.228, 0.915, 0.017, 0.018)],
    "bill": [(-0.213, 0.912, 0.012, 0.012, 0.009), (-0.258, 0.905, 0.0098, 0.0095, 0.0072),
             (-0.30, 0.897, 0.0063, 0.006, 0.0045), (-0.335, 0.890, 0.0, 0.0, 0.0)],
    "eye": (0.021, -0.199, 0.929, 0.0078),
    "plumes": [],
    "wing": [(0.053, -0.09, 0.638, 0.018, 0.036), (0.064, 0.0, 0.605, 0.022, 0.064),
             (0.062, 0.13, 0.54, 0.020, 0.064), (0.045, 0.255, 0.465, 0.012, 0.034),
             (0.026, 0.35, 0.412, 0.0, 0.0)],
    "wing_lean": 0.55,
    "leg": {"thigh": [(0.035, 0.050, 0.50, 0.030), (0.037, 0.068, 0.215, 0.0145)],
            "shin": [(0.037, 0.068, 0.22, 0.0165), (0.038, 0.046, 0.12, 0.0125), (0.040, 0.024, 0.027, 0.013)],
            "foot": (0.040, 0.022)},
    "toes": (0.088, 0.04, 0.0078, 32.0),
}

SNOWY_SCALE = 0.63
SNOWY_PLUMES = [   # in the great egret's frame, scaled with it: back off the nape, tips curling up
    [(0.0, -0.150, 0.945, 0.013), (0.0, -0.115, 0.950, 0.011), (0.0, -0.085, 0.938, 0.008), (0.0, -0.066, 0.946, 0.0)],
    [(0.013, -0.145, 0.935, 0.012), (0.020, -0.112, 0.932, 0.010), (0.024, -0.085, 0.918, 0.007), (0.026, -0.068, 0.926, 0.0)],
    [(-0.013, -0.145, 0.935, 0.012), (-0.020, -0.112, 0.932, 0.010), (-0.024, -0.085, 0.918, 0.007), (-0.026, -0.068, 0.926, 0.0)],
]

SANDPIPER = {
    "res": RES_SHORE,
    "mats": {"plumage": "plumage_grey_brown", "bill": "bill_black", "legs": "legs_black",
             "feet": "legs_black", "eye": "eye_dark", "plume": "plumage_grey_brown"},
    "seam": 0.0004, "pivot_size": 0.008,
    "body": [(0.082, 0.062, 0.010, 0.004), (0.056, 0.064, 0.021, 0.016), (0.026, 0.066, 0.028, 0.026),
             (-0.006, 0.068, 0.029, 0.028), (-0.034, 0.072, 0.025, 0.024)],
    # thinner than the head everywhere it shows, so no collar
    "neck": [(-0.030, 0.078, 0.0150), (-0.040, 0.084, 0.0118), (-0.047, 0.089, 0.0102), (-0.052, 0.093, 0.0092),
             (-0.056, 0.096, 0.0085)],
    "kink": 2,
    "head": [(-0.044, 0.097, 0.0120, 0.0125), (-0.057, 0.099, 0.0145, 0.0145), (-0.069, 0.0975, 0.0122, 0.0120),
             (-0.077, 0.095, 0.0080, 0.0080)],
    # straight, drooping only over its last third
    "bill": [(-0.071, 0.0935, 0.0040, 0.0037, 0.0027), (-0.083, 0.0918, 0.0031, 0.0029, 0.0021),
             (-0.094, 0.0897, 0.0023, 0.0021, 0.0015), (-0.103, 0.0868, 0.0014, 0.0013, 0.0009),
             (-0.109, 0.0835, 0.0, 0.0, 0.0)],
    "eye": (0.0115, -0.060, 0.1005, 0.0033),
    "plumes": [],
    # the wing's front tucked behind the breast, not out on the shoulder
    "wing": [(0.015, -0.016, 0.080, 0.0055, 0.0095), (0.022, 0.002, 0.080, 0.0072, 0.0160),
             (0.023, 0.030, 0.076, 0.0070, 0.0155), (0.018, 0.058, 0.070, 0.0050, 0.0095),
             (0.011, 0.086, 0.066, 0.0, 0.0)],
    "wing_lean": 0.6,
    "leg": {"thigh": [(0.012, 0.004, 0.050, 0.0090), (0.012, 0.011, 0.025, 0.0039)],
            "shin": [(0.012, 0.011, 0.026, 0.0043), (0.0125, 0.006, 0.0145, 0.0035), (0.013, 0.001, 0.0045, 0.0036)],
            "foot": (0.013, 0.0)},
    "toes": (0.021, 0.006, 0.0023, 35.0),
}

GODWIT = {
    "res": RES_SHORE,
    "mats": {"plumage": "plumage_cinnamon", "bill": "bill_pink", "legs": "legs_dark_grey",
             "feet": "legs_dark_grey", "eye": "eye_dark", "plume": "plumage_cinnamon"},
    "seam": 0.0008, "pivot_size": 0.018,
    "body": [(0.185, 0.200, 0.020, 0.007), (0.135, 0.210, 0.041, 0.030), (0.065, 0.220, 0.055, 0.055),
             (-0.005, 0.230, 0.057, 0.058), (-0.062, 0.245, 0.048, 0.049)],
    # thinner than the head everywhere it shows, so no collar
    "neck": [(-0.056, 0.252, 0.030), (-0.076, 0.270, 0.0215), (-0.090, 0.284, 0.0180), (-0.100, 0.296, 0.0160),
             (-0.112, 0.304, 0.0145)],
    "kink": 2,
    "head": [(-0.094, 0.306, 0.0190, 0.0200), (-0.114, 0.309, 0.0225, 0.0225), (-0.135, 0.306, 0.019, 0.019),
             (-0.150, 0.301, 0.0125, 0.0125)],
    # long and curving a little up over its outer half
    "bill": [(-0.143, 0.297, 0.0070, 0.0070, 0.0052), (-0.177, 0.290, 0.0058, 0.0057, 0.0043),
             (-0.212, 0.286, 0.0045, 0.0044, 0.0033), (-0.242, 0.287, 0.0031, 0.0030, 0.0023),
             (-0.263, 0.292, 0.0, 0.0, 0.0)],
    "eye": (0.018, -0.124, 0.313, 0.0052),
    "plumes": [],
    # the wing's front tucked behind the breast, not out on the shoulder
    "wing": [(0.034, -0.038, 0.258, 0.010, 0.017), (0.047, 0.000, 0.256, 0.0145, 0.034),
             (0.050, 0.050, 0.247, 0.0140, 0.035), (0.040, 0.110, 0.231, 0.0100, 0.022),
             (0.026, 0.160, 0.218, 0.0070, 0.012), (0.015, 0.200, 0.208, 0.0, 0.0)],
    "wing_lean": 0.6,
    "leg": {"thigh": [(0.024, 0.010, 0.195, 0.020), (0.026, 0.024, 0.088, 0.0085)],
            "shin": [(0.026, 0.024, 0.090, 0.0095), (0.027, 0.012, 0.050, 0.0075), (0.028, 0.002, 0.0115, 0.0080)],
            "foot": (0.028, 0.0)},
    "toes": (0.044, 0.012, 0.0046, 33.0),
}


def snowy_egret():
    """The great egret at 0.63, with a black bill, yellow feet and its crest."""
    k = SNOWY_SCALE
    s = dict(GREAT_EGRET)
    s["res"] = RES_SNOWY
    s["mats"] = dict(GREAT_EGRET["mats"], bill="bill_black", feet="feet_yellow")
    s["seam"] = GREAT_EGRET["seam"] * k
    s["pivot_size"] = 0.02
    s["body"] = [tuple(v * k for v in c) for c in GREAT_EGRET["body"]]
    s["neck"] = [tuple(v * k for v in c) for c in GREAT_EGRET["neck"]]
    s["head"] = [tuple(v * k for v in c) for c in GREAT_EGRET["head"]]
    # a slimmer bill than the great egret's, the same length for its size
    s["bill"] = [(y * k, z * k, w * k * 0.85, u * k * 0.85, d * k * 0.85) for y, z, w, u, d in GREAT_EGRET["bill"]]
    s["eye"] = tuple(v * k for v in GREAT_EGRET["eye"])
    s["wing"] = [tuple(v * k for v in c) for c in GREAT_EGRET["wing"]]
    # the legs a touch thicker than scale, so they still read
    s["leg"] = {"thigh": [(x * k, y * k, z * k, r * k * 1.12) for x, y, z, r in GREAT_EGRET["leg"]["thigh"]],
                "shin": [(x * k, y * k, z * k, r * k * 1.12) for x, y, z, r in GREAT_EGRET["leg"]["shin"]],
                "foot": tuple(v * k for v in GREAT_EGRET["leg"]["foot"])}
    fl, hl, r, spread = GREAT_EGRET["toes"]
    s["toes"] = (fl * k, hl * k, r * k * 1.12, spread)
    s["plumes"] = [[(x * k, y * k, z * k, r * k) for x, y, z, r in pl] for pl in SNOWY_PLUMES]
    return s


# file name: [(variant, spec, label for the lineup)]
BIRDS = {
    "heron": [("", lambda: HERON, "great blue heron")],
    "egret": [("great", lambda: GREAT_EGRET, "great egret"), ("snowy", snowy_egret, "snowy egret")],
    "shorebird": [("sandpiper", lambda: SANDPIPER, "western sandpiper"), ("godwit", lambda: GODWIT, "marbled godwit")],
}


# --- building blocks -------------------------------------------------------

TARGET = [None]   # the collection new parts go into
MADE = []         # what the current bird has made, pivots and parts


def export():
    return bpy.data.collections["export"]


def material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        colour = COLOURS[name]
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour
        bsdf.inputs["Roughness"].default_value = 0.8
        mat.diffuse_color = colour
    return mat


def world_of(obj):
    """A pivot's world position: pivots are never rotated or scaled, so it is
    the sum of the locations up its chain."""
    p = Vector((0.0, 0.0, 0.0))
    while obj is not None:
        p += obj.location
        obj = obj.parent
    return p


def pivot(name, at, size, parent=None):
    """An empty at the joint `at` (world), under `parent` if given."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SPHERE"
    e.empty_display_size = size
    TARGET[0].objects.link(e)
    e.parent = parent
    e.location = Vector(at) - (world_of(parent) if parent is not None else Vector((0.0, 0.0, 0.0)))
    MADE.append(e)
    return e


def new_object(name, bm, mat, under=None, smooth_deg=70.0):
    """Finish a bmesh (built in world coordinates) into a part. Under a pivot,
    its vertices move into the pivot's frame so the pivot turns it about the
    joint. Smooth shaded, sharp only where faces meet at more than
    `smooth_deg` (the bill's mouth line, its hidden base)."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bad = [f for f in bm.faces if f.calc_area() < 1e-12]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if under is not None:
        bmesh.ops.translate(bm, verts=bm.verts, vec=-world_of(under))
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(smooth_deg))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    TARGET[0].objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = under
    obj["kyt_collision"] = "none"
    MADE.append(obj)
    return obj


def spline(ctrl, per):
    """Catmull-Rom through control tuples (a point and its radii together),
    `per` samples a span; control i is sample i * per."""
    pts = [tuple(c) for c in ctrl]
    n = len(pts)
    out = []
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
        for k in range(per):
            t = k / per
            out.append(tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                    + (3 * b - a - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(pts[-1])
    return out


def sweep(rings, sides, lateral=(1.0, 0.0, 0.0), caps=(2, 2), half=None, cap_len=1.0):
    """A tube through `rings`, each (point, rx, rz): rx across `lateral` (made
    square to the spine), rz across the third axis, spine x lateral. A ring of
    zero radius is a point (a pointed tip). A cap is a number (a rounded dome
    of that many rings and a pole, reaching out by the end's radius times
    `cap_len`), "flat" or "none". `half` is "up" or "down": only that half of
    each ring, closed by a flat face along the spine (a bill's two halves)."""
    pts = [Vector(r[0]) for r in rings]
    n = len(pts)
    hint = Vector(lateral).normalized()
    frames = []
    for i in range(n):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        s = (hint - t * hint.dot(t)).normalized()
        frames.append((t, s, t.cross(s)))
    if half == "up":
        angles = [math.pi * k / sides for k in range(sides + 1)]
    elif half == "down":
        angles = [math.pi + math.pi * k / sides for k in range(sides + 1)]
    else:
        angles = [TAU * k / sides for k in range(sides)]

    def ring(p, s, u, rx, rz):
        rx, rz = max(rx, 0.0), max(rz, 0.0)
        if rx < 1e-7 and rz < 1e-7:
            return [p.copy()]
        return [p + s * (rx * math.cos(a)) + u * (rz * math.sin(a)) for a in angles]

    def cap(i, sign, count):
        t, s, u = frames[i]
        rx, rz = rings[i][1], rings[i][2]
        reach = 0.5 * (rx + rz) * cap_len
        out = []
        for j in range(1, count + 1):
            th = 0.5 * math.pi * j / (count + 1)
            out.append(ring(pts[i] + t * (sign * reach * math.sin(th)), s, u, rx * math.cos(th), rz * math.cos(th)))
        out.append([pts[i] + t * (sign * reach)])
        return out

    loops = [ring(pts[i], frames[i][1], frames[i][2], rings[i][1], rings[i][2]) for i in range(n)]
    c0, c1 = caps
    if isinstance(c1, int) and len(loops[-1]) > 1:
        loops = loops + cap(n - 1, 1.0, c1)
    if isinstance(c0, int) and len(loops[0]) > 1:
        loops = list(reversed(cap(0, -1.0, c0))) + loops
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in loop] for loop in loops]
    m = len(angles)
    for a, b in zip(vs, vs[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for k in range(m):
            j = (k + 1) % m
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[k]))
            elif len(b) == 1:
                bm.faces.new((a[k], a[j], b[0]))
            else:
                bm.faces.new((a[k], a[j], b[j], b[k]))
    if len(vs[0]) > 1:
        bm.faces.new(list(reversed(vs[0])))
    if len(vs[-1]) > 1:
        bm.faces.new(vs[-1])
    return bm


def ball(centre, r, segs):
    """A small sphere with its poles across (an eye looks out sideways)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs[0], v_segments=segs[1], radius=r,
                              matrix=Matrix.Translation(centre) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    return bm


def mirrored(bm):
    """A copy of a left-side part for the right side (x to -x)."""
    out = bm.copy()
    bmesh.ops.transform(out, matrix=Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0)), verts=out.verts)
    return out


def foot_bm(foot, toes, sides):
    """Three front toes splayed from the foot's ground point and one hind toe,
    each a slightly flat tube lying on z = 0 with a rounded tip; their bases
    meet under the shin's end."""
    fx, fy = foot
    front, hind, r, spread = toes
    rv, rh = r * 0.8, r
    parts = []
    for ang, length in ((-spread, front), (0.0, front * 1.06), (spread, front), (180.0, hind)):
        a = math.radians(ang)
        d = Vector((math.sin(a), -math.cos(a), 0.0))
        start = Vector((fx, fy, rv)) + d * (r * 0.3)
        tip = start + d * length
        tip.z = rv * 0.75
        parts.append(sweep([(start, rv, rh), (tip, rv * 0.75, rh * 0.75)], sides,
                           lateral=(0.0, 0.0, 1.0), caps=("flat", 1), cap_len=1.2))
    out = bmesh.new()
    for bm in parts:
        me = bpy.data.meshes.new("_join")
        bm.to_mesh(me)
        bm.free()
        out.from_mesh(me)
        bpy.data.meshes.remove(me)
    return out


def bounds(objs):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            w = o.matrix_world @ v.co
            lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
        ev.to_mesh_clear()
    return lo, hi


def triangles(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
        ev.to_mesh_clear()
    return n


# --- one bird --------------------------------------------------------------

def build_bird(spec, variant=""):
    """Build one bird into `export` (a variant into its own `variant_<v>`),
    toes on z = 0, plan centred on the origin. Returns what it made."""
    sfx = f"_{variant}" if variant else ""
    if variant:
        coll = bpy.data.collections.get(f"variant_{variant}") or bpy.data.collections.new(f"variant_{variant}")
        if coll.name not in export().children:
            export().children.link(coll)
        TARGET[0] = coll
    else:
        TARGET[0] = export()
    MADE.clear()
    res, size = spec["res"], spec["pivot_size"]

    def mat(role):
        return material(spec["mats"][role])

    # body, tail to chest: a flat round tail end, a full dome at the chest
    body = [((0.0, y, z), rx, rz) for y, z, rx, rz in spline(spec["body"], res["body_per"])]
    new_object("body" + sfx, sweep(body, res["body"], caps=(1, 2)), mat("plumage"))

    # the neck in two segments, the S's lower curve and its upper
    neck = spline([(0.0, y, z, r) for y, z, r in spec["neck"]], res["neck_per"])
    k = spec["kink"] * res["neck_per"]
    neck_p = pivot("neck_pivot" + sfx, neck[0][:3], size)
    upper_p = pivot("neck_upper_pivot" + sfx, neck[k][:3], size, neck_p)
    head_p = pivot("head_pivot" + sfx, neck[-1][:3], size, upper_p)
    new_object("neck_lower" + sfx, sweep([(p[:3], p[3], p[3]) for p in neck[:k + 1]], res["neck"], caps=(1, 1)),
               mat("plumage"), neck_p)
    new_object("neck_upper" + sfx, sweep([(p[:3], p[3], p[3]) for p in neck[k:]], res["neck"], caps=(1, 1)),
               mat("plumage"), upper_p)

    # the head, an egg along the bill's line, and its eyes
    head = [((0.0, y, z), rx, rz) for y, z, rx, rz in spline(spec["head"], res["head_per"])]
    new_object("head" + sfx, sweep(head, res["head"], caps=(1, 2)), mat("plumage"), head_p)
    ex, ey, ez, er = spec["eye"]
    for side, label in ((1.0, "left"), (-1.0, "right")):
        new_object(f"eye_{label}" + sfx, ball((side * ex, ey, ez), er, res["eye"]), mat("eye"), head_p)

    # the bill: two halves hinged at the gape, the lower a hair narrower and
    # lower so their flat faces never share a plane
    bill = spline(spec["bill"], res["bill_per"])
    gape = (0.0, spec["bill"][0][0], spec["bill"][0][1])
    up_p = pivot("upper_pivot" + sfx, gape, size * 0.6, head_p)
    lo_p = pivot("lower_pivot" + sfx, gape, size * 0.6, head_p)
    gap = spec["seam"]
    new_object("bill_upper" + sfx,
               sweep([((0.0, y, z), w, u) for y, z, w, u, d in bill], res["bill"], caps=("flat", "none"), half="up"),
               mat("bill"), up_p)
    new_object("bill_lower" + sfx,
               sweep([((0.0, y, z - gap), w * 0.92, d) for y, z, w, u, d in bill], res["bill"],
                     caps=("flat", "none"), half="down"),
               mat("bill"), lo_p)

    for i, plume in enumerate(spec.get("plumes", ())):
        rings = [((x, y, z), r * 0.8, r) for x, y, z, r in spline(plume, res["plume_per"])]
        new_object(f"plume_{i + 1}" + sfx, sweep(rings, res["plume"], caps=(1, "none")), mat("plume"), head_p)

    # the folded wings, lying on the body's sides and over its back
    wing = [((x, y, z), rx, rz) for x, y, z, rx, rz in spline(spec["wing"], res["wing_per"])]
    left = sweep(wing, res["wing"], lateral=(1.0, 0.0, spec["wing_lean"]), caps=(1, "none"))
    w0 = spec["wing"][0]
    for side, label in ((1.0, "left"), (-1.0, "right")):
        p = pivot(f"wing_{label}" + sfx, (side * w0[0], w0[1], w0[2]), size)
        new_object(f"folded_wing_{label}" + sfx, left.copy() if side > 0 else mirrored(left), mat("plumage"), p)
    left.free()

    # the legs: the bare thigh from the hip (inside the belly) to the heel,
    # the shin from the heel to the foot, and the toes
    leg = spec["leg"]
    thigh = sweep([((x, y, z), r, r) for x, y, z, r in leg["thigh"]], res["leg"], caps=(1, 1))
    shin = sweep([((x, y, z), r, r) for x, y, z, r in leg["shin"]], res["leg"], caps=(1, 1))
    foot = foot_bm(leg["foot"], spec["toes"], res["toe"])
    hip, heel = leg["thigh"][0], leg["shin"][0]
    for side, label in ((1.0, "left"), (-1.0, "right")):
        leg_p = pivot(f"leg_{label}" + sfx, (side * hip[0], hip[1], hip[2]), size)
        ankle_p = pivot(f"ankle_{label}" + sfx, (side * heel[0], heel[1], heel[2]), size * 0.7, leg_p)
        for part, bm, role, under in (("thigh", thigh, "legs", leg_p), ("shin", shin, "legs", ankle_p),
                                      ("foot", foot, "feet", ankle_p)):
            new_object(f"{part}_{label}" + sfx, bm.copy() if side > 0 else mirrored(bm), mat(role), under)
    for bm in (thigh, shin, foot):
        bm.free()

    # toes on z = 0, the plan centred on the origin
    made = list(MADE)
    lo, hi = bounds([o for o in made if o.type == "MESH"])
    delta = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    for o in made:
        if o.parent is None:
            if o.type == "MESH":
                o.data.transform(Matrix.Translation(delta))
            else:
                o.location += delta
    if variant:
        for o in made:
            o["kyt_variant"] = variant
    bpy.context.view_layer.update()
    return made


def describe(name, variant, made):
    parts = [o for o in made if o.type == "MESH"]
    pivots = [o for o in made if o.type == "EMPTY"]
    lo, hi = bounds(parts)
    tris = triangles(parts)
    budget = BUDGET[name]
    label = f"{name} {variant}".strip()
    feet = [o for o in parts if o.name.startswith("foot_left")]
    flo, fhi = bounds(feet)
    shin = [o for o in parts if o.name.startswith("shin_left")]
    slo, shi = bounds(shin)
    head = [o for o in parts if o.name.startswith("head")]
    hlo, hhi = bounds(head)
    lines = [f"{label}: {len(parts)} parts, {len(pivots)} pivots, {tris} triangles (budget {budget}: "
             f"{'ok' if tris <= budget else 'OVER'}), materials "
             f"{sorted({s.material.name for o in parts for s in o.material_slots})}",
             f"  {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} x {hi.z - lo.z:.3f} m (W x L x H); "
             f"x {lo.x:.3f}..{hi.x:.3f}, y {lo.y:.3f}..{hi.y:.3f}, z {lo.z:.4f}..{hi.z:.3f}",
             f"  crown {hhi.z:.3f} m; the left foot's toes y {flo.y:.3f}..{fhi.y:.3f}, z {flo.z:.4f}..{fhi.z:.4f}; "
             f"the shin {2 * (shi.x - slo.x) / 2:.3f} m across at its widest",
             "  " + ", ".join(f"{o.name} {triangles([o])}" for o in parts)]
    return lines


# --- renders ---------------------------------------------------------------

def stage_setup(resolution):
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    try:
        scene.eevee.taa_render_samples = 32
    except AttributeError:
        pass
    world = bpy.data.worlds.new("_review")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.72, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.world = world
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    ground = bpy.data.meshes.new("_ground")
    g = 60.0
    ground.from_pydata([(-g, -g, -0.0005), (g, -g, -0.0005), (g, g, -0.0005), (-g, g, -0.0005)], [], [(0, 1, 2, 3)])
    gobj = bpy.data.objects.new("_ground", ground)
    gm = bpy.data.materials.new("_ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.50, 0.47, 0.42, 1)
    ground.materials.append(gm)
    stage.objects.link(gobj)
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(48), math.radians(10), math.radians(35))
    stage.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    return scene, stage, cam


def all_points(objs):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def shoot(scene, cam, path, objs, direction, lens=50, margin=0.05):
    """The camera along `direction` from the objects' centre, backed off until
    every vertex is in frame."""
    pts = all_points(objs)
    lo = Vector(map(min, *pts))
    hi = Vector(map(max, *pts))
    centre = (lo + hi) / 2
    d = Vector(direction).normalized()
    dist = max((hi - lo).length * 0.6, 0.05)
    cam.data.lens = lens
    cam.data.clip_start = max(dist * 0.01, 0.001)
    for _ in range(80):
        cam.location = centre + d * dist
        cam.location.z = max(cam.location.z, 0.01)
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if all(margin <= c.x <= 1 - margin and margin <= c.y <= 1 - margin
               for c in (world_to_camera_view(scene, cam, p) for p in pts)):
            break
        dist *= 1.06
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def scale_box(stage, at):
    """A 1.7 m box, a guest's height, 0.45 by 0.28 m, standing at `at`."""
    me = bpy.data.meshes.new("_scale_box")
    x, y = 0.225, 0.14
    me.from_pydata([(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (-x, -y, 1.7), (x, -y, 1.7), (x, y, 1.7), (-x, y, 1.7)],
                   [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    box = bpy.data.objects.new("_scale_box", me)
    box.location = at
    m = bpy.data.materials.new("_scale_box")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.35, 0.38, 1)
    me.materials.append(m)
    stage.objects.link(box)
    return box


VIEWS = (("three_quarter", (-0.75, -1.0, 0.55)), ("front", (0.0, -1.0, 0.12)),
         ("side", (1.0, 0.0, 0.12)), ("top", (0.0, -0.001, 1.0)))


def move_bird(made, offset):
    """Move a whole bird by moving its roots (in memory only: the lineup, or
    a render after the save)."""
    for o in made:
        if o.parent is None:
            o.location = Vector(o.location) + Vector(offset)
    bpy.context.view_layer.update()


def render(folder, name):
    """Run after any save: it adds the rig and moves variants apart."""
    os.makedirs(folder, exist_ok=True)
    layers = bpy.context.view_layer.layer_collection.children["export"]
    for child in layers.children:
        child.hide_viewport = False
    scene, stage, cam = stage_setup((1400, 900))
    every = list(export().all_objects)
    parts = [o for o in every if o.type == "MESH"]
    variants = [v for v, _, _ in BIRDS[name]]
    extras = []

    def only(objs):
        for o in parts + extras:
            o.hide_render = o not in objs

    groups = {v: [o for o in parts if str(o.get("kyt_variant", "")) == v] for v in variants}
    for v, objs in groups.items():
        tag = f"{name}_{v}" if v else name
        only(objs)
        for view, d in VIEWS:
            shoot(scene, cam, os.path.join(folder, f"{tag}_{view}.png"), objs, d)
        lo, hi = bounds(objs)
        box = scale_box(stage, (hi.x + 0.12 + 0.2, 0.0, 0.0))
        extras.append(box)
        only(objs + [box])
        shoot(scene, cam, os.path.join(folder, f"{tag}_scale.png"), objs + [box], (-0.55, -1.0, 0.3))
    if len(variants) > 1:
        # the variants side by side, left to right, the first where it stands
        shown = [o for v in variants for o in groups[v]]
        only(shown)
        for tag, axis, direction in (("variants", 0, (-0.6, -1.0, 0.3)), ("variants_side", 1, (1.0, 0.0, 0.12))):
            lo, hi = bounds(groups[variants[0]])
            at, moved = hi[axis], []
            for v in variants[1:]:
                vlo, vhi = bounds(groups[v])
                offset = Vector((0.0, 0.0, 0.0))
                offset[axis] = at + 0.25 * (hi.z - lo.z) - vlo[axis]
                bird = [o for o in every if str(o.get("kyt_variant", "")) == v]
                move_bird(bird, offset)
                moved.append((bird, offset))
                at = offset[axis] + vhi[axis]
            # a long lens, so the nearer bird isn't drawn bigger than it is
            shoot(scene, cam, os.path.join(folder, f"{name}_{tag}.png"), shown, direction, lens=150)
            for bird, offset in moved:
                move_bird(bird, -offset)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--lineup" in argv:
        lineup(argv[argv.index("--lineup") + 1])
        return
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name not in BIRDS:
        raise SystemExit(f"wildlife_lagoon_birds: open one of {', '.join(BIRDS)}, not {name or 'an unsaved file'}")
    coll = export()
    if coll.all_objects:
        if "--replace" not in argv:
            raise SystemExit(f"wildlife_lagoon_birds: export already holds {[o.name for o in coll.all_objects][:4]}...; "
                             "it may be hers. --replace builds over it")
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o)
        for child in list(coll.children):
            bpy.data.collections.remove(child)
        for me in [m for m in bpy.data.meshes if m.users == 0]:
            bpy.data.meshes.remove(me)
    for v, make, _ in BIRDS[name]:
        made = build_bird(make(), v)
        for line in describe(name, v, made):
            print(line)
    # variants stand in the same place: all but the first hidden in the viewport
    layers = bpy.context.view_layer.layer_collection.children["export"]
    for v, _, _ in BIRDS[name][1:]:
        layers.children[f"variant_{v}"].hide_viewport = True
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print("saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], name)


def label_text(stage, text, at, size):
    """A label standing on the ground, facing +X, reading toward +Y."""
    curve = bpy.data.curves.new("_label", "FONT")
    curve.body = text
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "BOTTOM"
    obj = bpy.data.objects.new("_label", curve)
    obj.rotation_euler = (math.pi / 2, 0.0, math.pi / 2)
    obj.location = at
    m = bpy.data.materials.get("_label") or bpy.data.materials.new("_label")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
    curve.materials.append(m)
    stage.objects.link(obj)
    return obj


def lineup(png):
    """All five birds in a row at true relative size, tallest first, with the
    1.7 m box and the adult gull at its game size; nothing is saved."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.collection.children.link(bpy.data.collections.new("export"))
    birds = []
    for name in ("heron", "egret", "shorebird"):
        for v, make, label in BIRDS[name]:
            made = build_bird(make(), v)
            birds.append((label, made, [o for o in made if o.type == "MESH"]))
    scene, stage, cam = stage_setup((2400, 900))

    # the adult gull, from its GLB, at its game scale, turned to face -Y
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GULL_GLB)
    gull = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new("_gull", None)
    stage.objects.link(holder)
    for o in gull:
        if o.parent is None:
            o.parent = holder
    holder.scale = (GULL_GAME_SCALE,) * 3
    gull_meshes = [o for o in gull if o.type == "MESH" and not o.hide_render]
    bill = [o for o in gull_meshes if "bill" in o.name]
    blo, bhi = bounds(bill)
    glo, ghi = bounds(gull_meshes)
    if (blo.y + bhi.y) / 2 > (glo.y + ghi.y) / 2:
        holder.rotation_euler = (0.0, 0.0, math.pi)
    glo, ghi = bounds(gull_meshes)
    holder.location = Vector((-(glo.x + ghi.x) / 2, -(glo.y + ghi.y) / 2, -glo.z))
    birds.append(("adult gull (game size)", [holder], gull_meshes))
    birds.sort(key=lambda b: -bounds(b[2])[1].z)   # tallest first

    # left to right as seen from +X: the box, then the birds, -Y to +Y
    box = scale_box(stage, (0.0, 0.0, 0.0))
    shown = [box]
    at = 0.2
    labels = []
    for label, made, meshes in birds:
        lo, hi = bounds(meshes)
        offset = at + 0.22 - lo.y
        move_bird(made, (0.0, offset, 0.0))
        lo, hi = bounds(meshes)
        # in front of the birds and below their feet as the camera sees it
        labels.append(label_text(stage, f"{label} {hi.z:.2f} m", (0.6, (lo.y + hi.y) / 2, 0.0), 0.045))
        print(f"lineup: {label} {hi.z:.3f} m tall, {hi.y - lo.y:.3f} m long")
        shown += meshes
        at = hi.y
    labels.append(label_text(stage, "1.7 m box", (0.6, 0.0, 0.0), 0.045))
    for o in bpy.data.objects:
        if o.type in ("MESH", "FONT"):
            o.hide_render = o not in shown + labels and o.name != "_ground"
    os.makedirs(os.path.dirname(os.path.abspath(png)), exist_ok=True)
    shoot(scene, cam, os.path.abspath(png), shown + labels, (1.0, -0.12, 0.26), lens=135, margin=0.03)


main()
