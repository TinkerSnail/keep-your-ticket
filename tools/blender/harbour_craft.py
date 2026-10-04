"""The harbour craft, blocked out (2026-10-03): the boats that bring the ships
into the new container port across the water from the city (the boats
brief, `boats-2026-10-03`; Christina's "we need to add boats to our props"
and "lets add a modern port near the city").

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/harbour_craft.blend --python tools/blender/harbour_craft.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, three craft, all standing at the origin, each
marked `kyt_variant` so Send writes each as a prop of its own (`send.py`):

- **tug**, in `export`: a late-1990s US West Coast azimuth-stern-drive (ASD)
  harbour tug, 30 x 11 m, 5 m draft to the bottom of its drive nozzles. A
  full round bow in plan behind a heavy rubber fender (a big cylinder along
  the bulwark top over W-block aprons down to the waterline), W-blocks on
  the stern quarters with a cylinder across the transom, a round D-fender
  along each side; a low bulwark with a cap
  rail; the towing winch and an H-bitt on the foredeck, a staple at the
  stem, a second H-bitt aft; the deckhouse with a tall wheelhouse set well
  forward on it, windows all round, a visor roof and a mast with its towing
  lights, radar and searchlight; twin raked stacks aft of the wheelhouse;
  two life-raft canisters; under water a box skeg and the two Z-drive legs
  with their nozzles.
- **pilot_boat**, in `export/variant_pilot_boat` with its eye shut: a 16.5 m
  deep-V pilot boat of the period, a forward-set cabin with big windows and
  a raked-back windscreen, a rubber collar round the sheer, rails all round
  the deck for the pilot, a mast, radar and searchlight on the cabin top, an
  unlettered band on each side where a real one says PILOT, and under water
  a keel skeg, twin propellers on shafts and struts and twin rudders.
- **tug_conventional**, in `export/variant_tug_conventional` with its eye
  shut: an older single-screw harbour tug, 26 x 8 m, 3.6 m draft at its drag
  keel: a model bow with a strong sheer, a rope bow pudding on the stem, a
  round fantail stern with its own fender, the deckhouse straddling midships
  with the pilothouse at its forward end, one big stack, the towing hook on
  its post aft of the house and two tow bows arching over the after deck;
  under water the deadwood, keel shoe, one propeller and a rudder.

Four more (2026-10-03, Christina's "build all the offered variants"), each
in `export/variant_<name>` with its eye shut, built from its source's meshes
as linked copies wherever a part is unchanged (moved parts are linked copies
with their own placement), so reshaping a shared part reshapes every craft
that carries it:

- **tug_escort**: the tug with its wheelhouse raised on a second tier (small
  windows, a ledge roof), mast and stacks lifted with it; 17.0 m air draft.
  New: the tier, wheelhouse, roof, mast, stacks.
- **tug_tractor**: the tug driven from forward, her Z-drives moved forward to
  y 5.0, a big skeg aft, the hawser winch moved to the after deck and the
  staple to the stern so she works over the stern, the after bitt gone from
  the towline's path. New: the skeg (the rest are the tug's meshes, moved).
- **pilot_boat_b**: the pilot boat with a reverse-raked windscreen, a white
  hull and an orange band. New: the cabin, its glass and roof; the hull and
  bands are copies of the pilot boat's meshes in the new colours.
- **tug_conventional_b**: the old tug with her whole house moved 4.2 m aft
  (deckhouse, pilothouse, stack, rafts), a long foredeck with a tall
  foremast hinged in a tabernacle, the towing hook moved aft of the house,
  one tow bow, and truck-tyre fenders hung over the rubbing strakes. New:
  the foremast and tabernacle, the tow bow, the tyres (one mesh).

The tug's radar stood 0.65 m behind its roof's after edge in the first pass
(y -0.80, in the air); since 2026-10-03 it stands on the roof at
`RADAR_ROOF_Y` like the escort's and the tractor's.

Into the locked `reference` collection go each craft's `waterline` outline
(the hull cut at z = 0), its length-by-beam outline, and a 1.7 m figure on
the tug's after deck. Everything the tool makes carries `kyt_harbour_craft`,
so a rerun removes and rebuilds its own work and keeps anything of hers;
`export` holding anything untagged refuses without `--replace`.

**Frame** (the boats brief). Real metres, Z up. z = 0 is the waterline; the
hull goes below it by its draft as a closed form down to the keel. The bow is
+Y, which the glTF export turns into Godot's -Z, the forward of
`Basis.looking_at` (as `scenes/world/ride_vehicle.gd` turns its trains). The
origin is on the centreline, midships, at the waterline. Starboard is +X.

**Contract** (scenery block-out): closed shells, silhouette first, no
interiors. The windows of every wheelhouse, cabin and deckhouse are dark
slabs set 4 cm proud of their walls and sunk 3 cm into them, not holes: the
craft are seen from the water and the quay, and nothing behind the glass
exists. Every part is `kyt_collision = none` this pass; collision and
boarding are decided when the boats are placed and scheduled. No two shapes
share a plane: a part that meets another laps 2 cm or more into it or stands
proud of it, and parts that bury themselves in a deck or a roof bury to
depths of their own so their hidden faces never coincide either.

**How it is built.** A hull is a loft of cross-sections at stations along Y
(a half-profile from the keel to the sheer, mirrored, with a crowned deck
between), capped at the transom and the stem, then cut at z = 0 so the
bottom paint ends exactly on the waterline; the cut's edges are the
`waterline` outline. The bulwark, cap rail and deck rails are walls along
the deck edge, mitred at every station. Fenders that hug the hull (the
W-block aprons, the pilot boat's band) are found by casting rays at the hull
from outside, so they follow its flare; round fenders are tubes swept along
the deck edge. Wheelhouses are lofts of a chamfered plan through a sill and
a head ring; a raked windscreen moves the head ring's forward points along
Y only, so every facet stays planar and every window slab lies flat on its
facet. The fittings the craft share (H-bitt, life-raft canister, radar,
searchlight, navigation light) are one mesh each with linked copies, so
reshaping one reshapes them all. Stand-in materials by surface,
`harbour_craft_<surface>` for the tug, `harbour_craft_pilot_<surface>` and
`harbour_craft_conventional_<surface>` for the others, the shared ones
(bottom paint, rubber, glass, soot, fittings, raft, light) unprefixed. No
names, logos, flags or lettering anywhere; colour is Christina's.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TAG = "kyt_harbour_craft"
PROP = "harbour_craft"
VARIANTS = ("tug", "pilot_boat", "tug_conventional", "tug_escort", "tug_tractor", "pilot_boat_b",
            "tug_conventional_b")


def V(x, y, z):
    return Vector((x, y, z))


# --- the ASD tug -------------------------------------------------------------
# Size: the task's 30 x 11 m, 5 m draft, read against Crowley's Harbor class
# (Nichols Brothers, 1998-99, six 4,800 hp ship-assist tractors for the West
# Coast): 103 x 36 x 15 ft, 31.4 x 11.0 x 4.6 m. The hull runs to +-14.3 m;
# the bow and stern fenders bring the length over all to about 30 m, the
# D-fenders the beam to about 11 m.
# Each station: (y, [(half-breadth, z) from the bottom's flat edge, the
# bilge, the waterline, to the sheer]). Chosen to that size: a 10.5 m hull,
# a 3.4 m canoe body, a full round bow in plan (the ASD kind, built to push
# on a ship's side), a 1 m immersed transom over the drives, the sheer from
# 1.2 m aft to 2.9 m at the stem.
TUG_STATIONS = (
    (-14.30, ((1.60, -1.00), (3.40, -0.60), (4.40, 0.00), (4.70, 1.20))),   # the transom
    (-13.30, ((1.40, -1.50), (3.70, -0.90), (4.80, 0.00), (5.05, 1.20))),
    (-11.80, ((1.20, -2.20), (3.90, -1.40), (4.95, 0.00), (5.22, 1.22))),
    (-9.00, ((0.90, -3.00), (4.30, -2.30), (5.10, 0.00), (5.25, 1.25))),
    (-6.00, ((0.80, -3.35), (4.50, -2.60), (5.15, 0.00), (5.25, 1.30))),
    (-3.00, ((0.80, -3.40), (4.50, -2.65), (5.15, 0.00), (5.25, 1.36))),
    (0.00, ((0.80, -3.40), (4.50, -2.65), (5.15, 0.00), (5.25, 1.44))),
    (3.00, ((0.80, -3.40), (4.40, -2.60), (5.10, 0.00), (5.25, 1.55))),
    (6.00, ((0.70, -3.30), (4.00, -2.50), (4.95, 0.00), (5.20, 1.72))),
    (8.00, ((0.60, -3.15), (3.60, -2.40), (4.70, 0.00), (5.10, 1.88))),
    (9.90, ((0.40, -2.90), (2.90, -2.10), (4.20, 0.00), (4.80, 2.10))),
    (11.30, ((0.30, -2.50), (2.10, -1.80), (3.50, 0.00), (4.35, 2.32))),
    (12.30, ((0.20, -1.90), (1.40, -1.30), (2.70, 0.00), (3.80, 2.50))),
    (13.20, ((0.12, -1.00), (0.70, -0.60), (1.60, 0.00), (3.05, 2.68))),
    (13.85, ((0.08, 0.10), (0.35, 0.40), (0.80, 0.90), (2.05, 2.82))),
    (14.30, ((0.05, 1.20), (0.20, 1.50), (0.40, 2.10), (0.90, 2.92))),      # the stem's face
)
TUG_CAMBER = 0.15            # the deck's crown at the centreline (chosen)
TUG_BULWARK_H = 0.95         # "a low bulwark" (task); about a metre on US harbour tugs
TUG_BULWARK_T = 0.20         # chosen, chunky
BULWARK_INSET = 0.04         # the bulwark stands 4 cm inside the hull's sheer line (no shared plane)
CAP_T, CAP_H = 0.26, 0.10    # the cap rail over the bulwark, 3 cm proud each side
# the fenders: a 1 m cylinder along the bulwark top round the bow over an
# apron of W-block fenders down toward the waterline (the usual US ASD fit),
# W-blocks on the stern quarters under a cylinder across the transom, a
# 0.4 m D-fender along each side between them
TUG_BOW_FENDER_FROM_Y = 9.9     # from the bow's shoulder, so the beam over fenders stays 11 m
TUG_STERN_FENDER_TO_Y = -13.3   # the quarters' W-blocks; the cylinder runs across the transom only
TUG_STERN_TUBE_Y = -14.3
TUG_BOW_TUBE_R, TUG_BOW_TUBE_OUT = 0.48, 0.15
TUG_STERN_TUBE_R, TUG_STERN_TUBE_OUT = 0.42, 0.10
TUG_APRON_T = 0.40           # the W-blocks stand 40 cm off the plating
TUG_APRON_LOW = 0.45         # their foot over the waterline at the bow
TUG_STERN_APRON_LOW = 0.30
TUG_D_FENDER_R = 0.20
# the deckhouse and wheelhouse (chosen; "a tall wheelhouse with all-round
# windows set well forward", the task)
TUG_HOUSE = ((2.60, 4.60), (3.60, 3.60), (3.60, -5.10), (3.10, -5.60),
             (-3.10, -5.60), (-3.60, -5.10), (-3.60, 3.60), (-2.60, 4.60))
TUG_HOUSE_TOP = 4.30
TUG_WH_PLAN = ((1.90, 4.40), (2.90, 3.40), (2.90, 0.70), (2.40, 0.20),
               (-2.40, 0.20), (-2.90, 0.70), (-2.90, 3.40), (-1.90, 4.40))
TUG_WH_SILL, TUG_WH_HEAD, TUG_WH_TOP = 5.45, 7.25, 7.50   # 1.8 m of glass all round, the eye at about 7 m
TUG_WH_RAKE = 0.30           # the windscreen leans out at the top, as tug wheelhouses do
TUG_ROOF_OVER, TUG_ROOF_T = 0.35, 0.24
TUG_MAST_AT = (0.0, 1.30)
TUG_MAST_TOP = 14.20         # chosen: towing lights well clear of the wheelhouse
TUG_STACK_X, TUG_STACK_Y = 2.25, -2.40
TUG_STACK_PLAN = (0.75, 1.15)    # across, along: slim exhaust casings, not funnels
TUG_STACK_TOP, TUG_STACK_RAKE = 8.70, 0.35
TUG_STACK_BAND, TUG_STACK_SOOT = (7.30, 7.80), 8.35
TUG_WINCH_SPAN = (5.70, 7.30)    # the hawser winch's bed along Y, ahead of the house
TUG_STAPLE_Y = 13.25             # the bow staple, inside the bulwark at the stem
TUG_RAIL_PATH = ((3.48, 3.40), (3.48, -5.00), (3.00, -5.48), (-3.00, -5.48), (-3.48, -5.00), (-3.48, 3.40))
# the drives (a Z-drive leg and its nozzle each side, about 2 m propellers)
TUG_DRIVE_X, TUG_DRIVE_Y = 2.70, -11.40
TUG_NOZZLE_R, TUG_NOZZLE_HL = 1.00, 0.80
TUG_NOZZLE_Z = -4.00         # its foot at -5.0, the task's draft
TUG_SKEG = ((3.00, -3.00), (0.50, -4.30), (-7.00, -4.30), (-8.60, -2.60))   # (y, z), x +-0.3

# --- the pilot boat ------------------------------------------------------------
# Size: the task's 16-17 m; the Ray Hunt deep-V pilot boats of the period (the
# 52 ft Chesapeake class that followed in 2003: 15.9-16.0 m, 5.2 m beam, 1.5 m
# draft). Each station: (y, [(keel), (chine), (sheer)]), deadrise about 20
# degrees at the transom and 24 midships, the chine rising forward.
PILOT_STATIONS = (
    (-8.05, ((0.06, -0.80), (2.26, -0.02), (2.36, 1.25))),    # the transom
    (-6.00, ((0.06, -0.88), (2.30, -0.04), (2.42, 1.28))),
    (-3.00, ((0.06, -0.98), (2.32, -0.04), (2.42, 1.33))),
    (0.00, ((0.06, -1.04), (2.30, -0.02), (2.42, 1.40))),
    (2.50, ((0.06, -1.02), (2.16, 0.06), (2.37, 1.50))),
    (4.50, ((0.06, -0.92), (1.88, 0.20), (2.20, 1.63))),
    (6.00, ((0.06, -0.70), (1.46, 0.38), (1.88, 1.78))),
    (7.00, ((0.05, -0.40), (1.00, 0.55), (1.46, 1.90))),
    (7.60, ((0.05, -0.05), (0.58, 0.75), (1.02, 1.98))),
    (8.05, ((0.04, 0.55), (0.12, 1.05), (0.30, 2.05))),       # the stem's top
)
PILOT_CAMBER = 0.08
PILOT_COLLAR_R = 0.16        # the rubber collar round the sheer (chosen, chunky)
PILOT_CABIN = ((1.25, 3.40), (1.75, 2.90), (1.75, -1.30), (1.45, -1.60),
               (-1.45, -1.60), (-1.75, -1.30), (-1.75, 2.90), (-1.25, 3.40))
PILOT_CABIN_BASE = 1.25
PILOT_SILL, PILOT_HEAD, PILOT_TOP = 2.35, 3.25, 3.50
PILOT_RAKE = -0.30           # the windscreen raked back (chosen; a reverse rake is an alternative)
PILOT_ROOF_OVER, PILOT_ROOF_T = 0.12, 0.13
PILOT_RAIL_H, PILOT_MID_RAIL = 0.95, 0.50
PILOT_RAIL_INSET = 0.22      # inside the collar, clear of the cabin's 0.67 m side decks
PILOT_MAST_AT = (0.0, -0.90)
PILOT_MAST_TOP = 7.40
PILOT_BAND = (-6.00, 4.50, 0.75, 0.40)   # y from, y to, its foot and head under the sheer
PILOT_SKEG = ((0.50, -0.85), (-1.50, -1.30), (-6.40, -1.30), (-7.00, -0.70))
PILOT_PROP_X, PILOT_PROP_Y, PILOT_PROP_Z, PILOT_PROP_R = 1.00, -6.60, -1.08, 0.40

# --- the conventional tug -------------------------------------------------------
# Size (chosen, after US single-screw harbour tugs of the 1950s and 60s,
# 85-100 ft by 24-27 ft): a 25.6 m hull, 7.6 m beam, 3.6 m at the drag keel;
# a model bow with a strong sheer (3.6 m at the stem, 1.05 m aft) and a
# round fantail stern.
CONV_STATIONS = (
    (-12.80, ((0.20, 0.55), (0.70, 0.75), (1.00, 0.95), (1.15, 1.05))),    # the fantail's tip
    (-12.40, ((0.25, 0.05), (1.40, 0.25), (2.10, 0.60), (2.45, 1.05))),
    (-11.60, ((0.30, -0.90), (2.20, -0.50), (3.00, 0.10), (3.30, 1.05))),
    (-10.40, ((0.30, -2.00), (2.70, -1.30), (3.50, -0.20), (3.72, 1.05))),
    (-8.00, ((0.40, -2.60), (3.00, -1.80), (3.70, -0.40), (3.80, 1.07))),
    (-4.00, ((0.50, -2.75), (3.10, -1.90), (3.75, -0.40), (3.80, 1.15))),
    (0.00, ((0.50, -2.75), (3.10, -1.90), (3.75, -0.40), (3.80, 1.32))),
    (4.00, ((0.45, -2.70), (2.90, -1.85), (3.65, -0.30), (3.75, 1.62))),
    (7.00, ((0.35, -2.55), (2.40, -1.70), (3.25, -0.20), (3.45, 2.05))),
    (9.30, ((0.25, -2.20), (1.60, -1.45), (2.60, -0.10), (3.00, 2.55))),
    (10.90, ((0.15, -1.50), (0.90, -0.90), (1.80, 0.10), (2.35, 3.00))),
    (11.90, ((0.10, -0.60), (0.45, -0.20), (1.05, 0.50), (1.65, 3.30))),
    (12.50, ((0.07, 0.40), (0.22, 0.70), (0.55, 1.40), (1.00, 3.48))),
    (12.80, ((0.05, 1.40), (0.12, 1.80), (0.30, 2.50), (0.45, 3.56))),     # the stem's top
)
CONV_CAMBER = 0.12
CONV_BULWARK_H, CONV_BULWARK_T = 0.75, 0.16
CONV_PUDDING_R, CONV_PUDDING_FROM_Y = 0.40, 10.0
CONV_STERN_R, CONV_STERN_TO_Y = 0.30, -10.4
CONV_GUARD_R = 0.14
CONV_HOUSE = ((2.00, 4.20), (2.60, 3.60), (2.60, -4.60), (2.20, -5.00),
              (-2.20, -5.00), (-2.60, -4.60), (-2.60, 3.60), (-2.00, 4.20))
CONV_HOUSE_TOP = 3.95
CONV_WH_PLAN = ((1.35, 3.90), (1.90, 3.35), (1.90, 1.30), (1.60, 1.00),
                (-1.60, 1.00), (-1.90, 1.30), (-1.90, 3.35), (-1.35, 3.90))
CONV_WH_SILL, CONV_WH_HEAD, CONV_WH_TOP = 4.95, 5.90, 6.10
CONV_ROOF_OVER, CONV_ROOF_T = 0.30, 0.20
CONV_MAST_AT = (0.0, 3.20)
CONV_MAST_TOP = 11.20
CONV_STACK_Y = -1.80
CONV_STACK_PLAN = (1.40, 2.20)
CONV_STACK_TOP, CONV_STACK_RAKE = 8.00, 0.50
CONV_TOW_POST_Y = -6.00      # the towing hook, aft of the house and of midships
CONV_TOW_BOWS_Y = (-7.80, -10.00)
CONV_TOW_BOW_RISE = 0.90
CONV_SKEG = ((-2.00, -2.50), (-5.00, -3.60), (-9.90, -3.60), (-9.90, -1.40))
CONV_PROP_Y, CONV_PROP_Z, CONV_PROP_R = -10.60, -2.15, 1.25

# --- the variants Christina asked for (2026-10-03, "build all the offered
# variants"); each shares its source's unchanged parts as linked meshes ------
# tug_escort: the ASD with its wheelhouse raised on a second tier, about 17 m
# air draft, the escort tugs' high eye over a ship's flare (chosen)
ESCORT_TIER_OUT = 0.15           # the tier stands 15 cm outside the wheelhouse's plan
ESCORT_TIER_SILL, ESCORT_TIER_HEAD, ESCORT_TIER_TOP = 5.30, 6.10, 6.90   # its rooms' windows
ESCORT_LEDGE_OVER, ESCORT_LEDGE_T = 0.15, 0.15   # the ledge roof the wheelhouse stands on
ESCORT_MAST_TOP = 16.80          # the masthead light's top then about 17 m over the water
RADAR_ROOF_Y = 0.45              # on the roof between the mast and its after edge
# tug_tractor: the same tug driven from forward, her drives about a third of
# her length from the bow, a big skeg aft, the towing winch on the after
# deck and a staple at the stern, so she works over the stern (chosen)
TRACTOR_DRIVE_Y = 5.00
TRACTOR_SKEG = ((-1.00, -3.00), (-4.50, -4.60), (-12.40, -4.60), (-13.60, -1.20))   # (y, z)
TRACTOR_SKEG_HALF = 0.40
TRACTOR_WINCH_Y = -8.00          # the winch's middle on the after deck
TRACTOR_STAPLE_Y = -13.30        # inside the transom's bulwark
# pilot_boat_b: the windscreen leaning out at the top (a reverse rake, which
# throws glare down), a white hull with an orange band (chosen)
PILOT_B_RAKE = 0.30
# tug_conventional_b: the whole house aft of midships (the deckhouse,
# pilothouse, stack and rafts moved aft so the house's forward end is at
# midships), a long foredeck with a tall foremast hinged in a tabernacle,
# tyre fenders hung along both sides (chosen)
CONV_B_SHIFT = -4.20
CONV_B_TOW_POST_Y = -9.95        # aft of the moved house
CONV_B_TOW_BOW_Y = -11.50        # one tow bow over the short after deck
CONV_B_FOREMAST_Y = 6.00
CONV_B_FOREMAST_TOP = 14.00
CONV_B_HEEL_UP, CONV_B_HINGE_UP, CONV_B_CHEEK_UP = 0.45, 1.45, 1.75   # over the deck
CONV_B_TYRE_YS = (-8.00, -5.50, -3.00, -0.50, 2.00, 4.50, 7.00)
CONV_B_TYRE_R, CONV_B_TYRE_T = 0.38, 0.24   # a truck tyre, about 0.76 m across
CONV_B_TYRE_DROP = 0.45          # its middle under the sheer: hung over the rubbing strake, as
                                 # real ones are, its foot then clear of the water even aft
                                 # where the freeboard is 1.05 m

# --- shared fittings (chosen, chunky) ----------------------------------------------
NAVLIGHT = (0.20, 0.20, 0.22)    # a masthead or towing light's housing
RAIL_BAR = 0.06                  # a rail's section


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


# stand-ins only: generic tug colours (a black hull, white house, buff
# stacks with a coloured band), the pilot boat's orange and black, the old
# tug's green and cream; no fleet's livery
COLOURS = {
    f"{PROP}_hull": srgb("24364f"),          # dark navy
    f"{PROP}_deck": srgb("6e3a30"),
    f"{PROP}_house": srgb("f2f1ea"),
    f"{PROP}_band": srgb("2f62a8"),
    f"{PROP}_stack": srgb("d9b56c"),
    f"{PROP}_rails": srgb("f2f1ea"),
    f"{PROP}_pilot_hull": srgb("3a3f46"),    # charcoal
    f"{PROP}_pilot_deck": srgb("8a8f8b"),
    f"{PROP}_pilot_house": srgb("e8641e"),
    f"{PROP}_pilot_band": srgb("f2f1ea"),
    f"{PROP}_pilot_stack": srgb("e8641e"),
    f"{PROP}_pilot_rails": srgb("c8ccca"),
    f"{PROP}_pilot_b_hull": srgb("f0efe8"),  # pilot_boat_b: white hull
    f"{PROP}_pilot_b_band": srgb("e8641e"),  # and an orange band
    f"{PROP}_conventional_hull": srgb("1f3a2d"),
    f"{PROP}_conventional_deck": srgb("7a6a55"),
    f"{PROP}_conventional_house": srgb("f1ece0"),
    f"{PROP}_conventional_band": srgb("b3352a"),
    f"{PROP}_conventional_stack": srgb("d6ad5c"),
    f"{PROP}_conventional_rails": srgb("f1ece0"),
    # shared by all three
    f"{PROP}_bottom": srgb("8b2c22"),      # antifouling red under the waterline
    f"{PROP}_rubber": srgb("141414"),
    f"{PROP}_glass": srgb("1e2b35"),
    f"{PROP}_soot": srgb("141414"),
    f"{PROP}_fittings": srgb("4a4f52"),
    f"{PROP}_raft": srgb("f4f4f0"),
    f"{PROP}_light": srgb("f5e6a8"),
}
OWN = ("hull", "deck", "house", "band", "stack", "rails")
SHARED = ("bottom", "rubber", "glass", "soot", "fittings", "raft", "light")


def material(name, colour=None):
    """A stand-in material by name; a rerun resets the builder's colours."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour or COLOURS[name]
        bsdf.inputs["Roughness"].default_value = 0.8
    elif name in COLOURS and mat.node_tree is not None:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = COLOURS[name]
    return mat


def mats(tag=""):
    """The craft's own surfaces, `harbour_craft_<tag><surface>`, and the shared ones."""
    out = {k: material(f"{PROP}_{tag}{k}") for k in OWN}
    out.update({k: material(f"{PROP}_{k}") for k in SHARED})
    return out


# --- building blocks -------------------------------------------------------

def tag(obj, variant):
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    obj["kyt_collision"] = "none"
    if variant:
        obj["kyt_variant"] = variant
    return obj


def make_mesh(name, bm, mat_list, flat=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = not flat
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for m in mat_list:
        mesh.materials.append(m)
    return mesh


def finish(name, bm, coll, mat_list, variant, loc=None, flat=True):
    """A bmesh into a tagged object in `coll`."""
    obj = bpy.data.objects.new(name, make_mesh(name, bm, mat_list, flat))
    if loc is not None:
        obj.location = loc
    coll.objects.link(obj)
    return tag(obj, variant)


def place(name, mesh, coll, loc, variant):
    """A linked copy of a shared fitting: the same mesh, its own place."""
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    coll.objects.link(obj)
    return tag(obj, variant)


def loft_bm(rings, closed=False, caps=True, bm=None):
    """Rings of equal length joined in order into quads; capped at both ends
    unless the path is closed. Every ring is itself a closed loop."""
    bm = bm or bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    m, n = len(rings[0]), len(rings)
    made = []
    for i in range(n if closed else n - 1):
        a, b = vs[i], vs[(i + 1) % n]
        for k in range(m):
            made.append(bm.faces.new((a[k], a[(k + 1) % m], b[(k + 1) % m], b[k])))
    if caps and not closed:
        made.append(bm.faces.new(vs[0]))
        made.append(bm.faces.new(list(reversed(vs[-1]))))
    return bm, made


def box_bm(x0, x1, y0, y1, z0, z1, bm=None):
    assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
    lo = [V(x0, y0, z0), V(x1, y0, z0), V(x1, y1, z0), V(x0, y1, z0)]
    hi = [V(p.x, p.y, z1) for p in lo]
    return loft_bm([lo, hi], bm=bm)


def box(name, coll, mat, x0, x1, y0, y1, z0, z1, variant):
    bm, _ = box_bm(x0, x1, y0, y1, z0, z1)
    return finish(name, bm, coll, [mat], variant)


def prism_bm(poly, z0, z1, bm=None):
    """A plan polygon (x, y) extruded from z0 to z1."""
    return loft_bm([[V(x, y, z0) for x, y in poly], [V(x, y, z1) for x, y in poly]], bm=bm)


def yz_prism(name, coll, mat, poly, x0, x1, variant):
    """A side-elevation polygon (y, z) extruded across from x0 to x1."""
    bm, _ = loft_bm([[V(x0, y, z) for y, z in poly], [V(x1, y, z) for y, z in poly]])
    return finish(name, bm, coll, [mat], variant)


def cylinder_bm(axis, c, r, hl, sides, bm=None):
    """A closed cylinder along 'x', 'y' or 'z' about centre `c`, half-length
    `hl`, with flat faces top and bottom (a half-step phase)."""
    rings = []
    for t in (-hl, hl):
        ring = []
        for k in range(sides):
            a = math.tau * (k + 0.5) / sides
            u, v = r * math.cos(a), r * math.sin(a)
            ring.append({"x": V(c[0] + t, c[1] + u, c[2] + v),
                         "y": V(c[0] + u, c[1] + t, c[2] + v),
                         "z": V(c[0] + u, c[1] + v, c[2] + t)}[axis])
        rings.append(ring)
    return loft_bm(rings, bm=bm)


def tube_bm(pts, r, sides, closed=False, phase=0.5):
    """A tube of `sides` facets swept along a 3D polyline, each ring square to
    the path; capped unless closed."""
    n = len(pts)
    rings = []
    for i in range(n):
        if closed:
            t = pts[(i + 1) % n] - pts[i - 1]
        else:
            t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        t.normalize()
        side = t.cross(Vector((0, 0, 1)))
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(t).normalized()
        ring = []
        for k in range(sides):
            a = math.tau * (k + phase) / sides
            ring.append(pts[i] + (side * math.cos(a) + up * math.sin(a)) * r)
        rings.append(ring)
    bm, _ = loft_bm(rings, closed=closed, caps=not closed)
    return bm


def plan_normals(pts):
    """Outward mitre vectors of a closed anticlockwise plan loop: moving a
    vertex by d times its mitre moves both its edges out by d."""
    n = len(pts)
    out = []
    for i in range(n):
        d0 = (pts[i] - pts[i - 1]).normalized()
        d1 = (pts[(i + 1) % n] - pts[i]).normalized()
        n0, n1 = Vector((d0.y, -d0.x)), Vector((d1.y, -d1.x))
        out.append((n0 + n1) / (1.0 + n0.dot(n1)))
    return out


def offset_poly(poly, d):
    """A plan polygon moved outward by d, whichever way it runs."""
    pts = [Vector(p) for p in poly]
    area = sum(a.x * b.y - b.x * a.y for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        d = -d
    return [tuple(p + m * d) for p, m in zip(pts, plan_normals(pts))]


def bvh_of(objs):
    """A BVH over the meshes' own triangles: a twisted quad split along the
    other diagonal bulges centimetres off the one that is drawn, enough to
    swallow a band hugging it (the pilot boat's, 2026-10-03)."""
    verts, tris = [], []
    for o in objs:
        mw = o.matrix_world
        base = len(verts)
        o.data.calc_loop_triangles()
        verts.extend(mw @ v.co for v in o.data.vertices)
        tris.extend([base + i for i in t.vertices] for t in o.data.loop_triangles)
    return BVHTree.FromPolygons(verts, tris)


def hull_hit(bvh, p, n, z, reach=4.0):
    """Where a level ray from outside, along -n at height z, meets the hull."""
    origin = V(p.x + n.x * reach, p.y + n.y * reach, z)
    hit = bvh.ray_cast(origin, V(-n.x, -n.y, 0.0), reach * 3)[0]
    return hit


# --- hulls and what follows their deck edge --------------------------------------

class Hull:
    """A hull lofted from its stations, with its deck edge as a loop."""

    def __init__(self, stations, camber):
        self.stations, self.camber = stations, camber
        self.ys = [y for y, _ in stations]
        self.loop = ([Vector((prof[-1][0], y)) for y, prof in stations] +
                     [Vector((-prof[-1][0], y)) for y, prof in reversed(stations)])
        self.loop_z = ([prof[-1][1] for _, prof in stations] +
                       [prof[-1][1] for _, prof in reversed(stations)])
        self.normals = plan_normals(self.loop)
        self.bvh = None

    def deck_z(self, y):
        """The sheer's height at y, between stations."""
        st = self.stations
        if y <= st[0][0]:
            return st[0][1][-1][1]
        for (y0, p0), (y1, p1) in zip(st, st[1:]):
            if y0 <= y <= y1:
                t = (y - y0) / (y1 - y0)
                return p0[-1][1] + (p1[-1][1] - p0[-1][1]) * t
        return st[-1][1][-1][1]

    def half_breadth(self, y):
        st = self.stations
        for (y0, p0), (y1, p1) in zip(st, st[1:]):
            if y0 <= y <= y1:
                t = (y - y0) / (y1 - y0)
                return p0[-1][0] + (p1[-1][0] - p0[-1][0]) * t
        return st[-1][1][-1][0] if y > 0 else st[0][1][-1][0]

    def build(self, name, coll, m, variant):
        rings = []
        for y, prof in self.stations:
            stb = [V(b, y, z) for b, z in prof]
            crown = V(0.0, y, prof[-1][1] + self.camber)
            port = [V(-b, y, z) for b, z in reversed(prof)]
            rings.append(stb + [crown] + port)
        bm, _ = loft_bm(rings)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                               plane_co=(0, 0, 0), plane_no=(0, 0, 1))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        for f in bm.faces:
            c = f.calc_center_median()
            f.material_index = 1 if c.z < 0 else (2 if f.normal.z > 0.5 else 0)
        self.waterline = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in bm.edges
                          if abs(e.verts[0].co.z) < 1e-4 and abs(e.verts[1].co.z) < 1e-4]
        obj = finish(name, bm, coll, [m["hull"], m["bottom"], m["deck"]], variant)
        self.obj = obj
        self.bvh = bvh_of([obj])
        return obj

    def indices(self, keep):
        """Loop indices, in loop order, whose point passes `keep(point)`,
        as one run (the loop is rotated so a run that wraps stays whole)."""
        n = len(self.loop)
        flags = [keep(p) for p in self.loop]
        start = next(i for i in range(n) if flags[i] and not flags[i - 1])
        run = []
        i = start
        while flags[i % n] and len(run) < n:
            run.append(i % n)
            i += 1
        return run

    def samples(self, idxs, step=None):
        """(plan point, outward normal, deck z) at each loop station of a
        run, and with `step` also between them at no more than `step`
        apart, along the deck edge's straight runs."""
        out = []
        for a, b in zip(idxs, idxs[1:]):
            pa, pb = self.loop[a], self.loop[b]
            na, nb = self.normals[a].normalized(), self.normals[b].normalized()
            za, zb = self.loop_z[a], self.loop_z[b]
            k = max(1, math.ceil((pb - pa).length / step)) if step else 1
            for t in range(k):
                f = t / k
                out.append((pa.lerp(pb, f), na.lerp(nb, f).normalized(), za + (zb - za) * f))
        last = idxs[-1]
        out.append((self.loop[last], self.normals[last].normalized(), self.loop_z[last]))
        return out

    def wall(self, name, coll, mat, inset, thick, z0f, z1f, variant, skip_ends=0):
        """A wall standing on the deck edge loop, mitred at every station."""
        loop = self.loop
        if skip_ends:
            # drop the stem's station (it is too narrow to walk round)
            keep = [i for i, p in enumerate(loop) if abs(p.y - self.ys[-1]) > 1e-6]
            pts = [loop[i] for i in keep]
            zs = [self.loop_z[i] for i in keep]
            ns = plan_normals(pts)
        else:
            pts, zs, ns = loop, self.loop_z, self.normals
        rings = []
        for p, zd, nv in zip(pts, zs, ns):
            o, i = p - nv * inset, p - nv * (inset + thick)
            z0, z1 = z0f(zd), z1f(zd)
            rings.append([V(o.x, o.y, z0), V(o.x, o.y, z1), V(i.x, i.y, z1), V(i.x, i.y, z0)])
        bm, _ = loft_bm(rings, closed=True)
        return finish(name, bm, coll, [mat], variant), pts, zs, ns

    def apron(self, name, coll, mat, idxs, zlo, zhi, nz, thick, lap, variant, bvh=None, step=None):
        """A band that hugs the hull's side, found by level rays from outside
        at nz heights from zlo(deck z) to zhi(deck z) at each loop station
        (and every `step` between, for a thin band the hull's twisted
        quads would otherwise bulge through)."""
        bvh = bvh or self.bvh
        rings = []
        for p, nv, zd in self.samples(idxs, step):
            lo, hi = zlo(zd), zhi(zd)
            outer, inner, last = [], [], None
            for j in range(nz):
                z = lo + (hi - lo) * j / (nz - 1)
                hit = hull_hit(bvh, p, nv, z)
                if hit is None:
                    hit = V(last.x, last.y, z) if last is not None else V(p.x, p.y, z)
                last = hit
                n3 = V(nv.x, nv.y, 0.0)
                outer.append(hit + n3 * thick)
                inner.append(hit - n3 * lap)
            rings.append(outer + list(reversed(inner)))
        bm, _ = loft_bm(rings)
        return finish(name, bm, coll, [mat], variant)

    def tube_along(self, name, coll, mat, idxs, r, out, zf, sides, variant, closed=False, hug=None):
        """A round fender swept along the deck edge: its centre `out` beyond the
        deck edge at zf(deck z), or, with `hug`, `out` beyond the hull's
        side at that height (found by ray)."""
        pts = []
        for i in idxs:
            p, nv = self.loop[i], self.normals[i].normalized()
            z = zf(self.loop_z[i])
            base = p
            if hug is not None:
                hit = hull_hit(hug, p, nv, z)
                if hit is not None:
                    base = Vector((hit.x, hit.y))
            c = base + nv * out
            pts.append(V(c.x, c.y, z))
        return finish(name, tube_bm(pts, r, sides, closed=closed), coll, [mat], variant)


def waterline_marker(name, segs, coll):
    """The hull's cut at z = 0, as edges, for the reference collection."""
    bm = bmesh.new()
    index = {}

    def vert(p):
        key = (round(p.x, 4), round(p.y, 4))
        if key not in index:
            index[key] = bm.verts.new((p.x, p.y, 0.0))
        return index[key]

    for a, b in segs:
        va, vb = vert(a), vert(b)
        if va is not vb and bm.edges.get((va, vb)) is None:
            bm.edges.new((va, vb))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


# --- superstructure ---------------------------------------------------------------

def facet_panes(prefix, coll, mat, A, B, Ah, Bh, centre, spans, variant, vins=0.07, proud=0.04, sunk=0.03):
    """Dark glass slabs on one planar facet (sill A-B, head Ah-Bh): each span
    (s0, s1) along the facet from sill to head less `vins`, set `proud` out
    of the wall and `sunk` into it."""
    n = (B - A).cross(Ah - A).normalized()
    mid = (A + B + Ah + Bh) / 4
    if n.dot(mid - V(centre.x, centre.y, mid.z)) < 0:
        n = -n
    H = (Ah - A).length
    t0, t1 = vins / H, 1.0 - vins / H

    def P(s, t):
        return A.lerp(B, s).lerp(Ah.lerp(Bh, s), t)

    out = []
    for k, (s0, s1) in enumerate(spans):
        quad = [P(s0, t0), P(s1, t0), P(s1, t1), P(s0, t1)]
        bm, _ = loft_bm([[q - n * sunk for q in quad], [q + n * proud for q in quad]])
        out.append(finish(f"{prefix}_{k}", bm, coll, [mat], variant))
    return out


def pane_spans(width, pitch, ins=0.12, gap=0.16, least=0.45):
    """Equal panes across a facet `width` wide, about `pitch` each, a
    `gap` mullion between them and `ins` of wall at each end."""
    if width - 2 * ins < least:
        return []
    count = max(1, round((width - 2 * ins) / pitch))
    pane = (width - 2 * ins - (count - 1) * gap) / count
    return [((ins + k * (pane + gap)) / width, (ins + k * (pane + gap) + pane) / width) for k in range(count)]


def wheelhouse(prefix, coll, m, plan, z_base, z_sill, z_head, z_top, rake, variant, pitch,
               roof_over, roof_t, skip_facets=(), body="wheelhouse", glass="wh_glass", roof_name="roof",
               spans_fn=None):
    """A wheelhouse lofted through base, sill, head and top rings; `rake`
    moves the head ring's forward points along Y (out if positive), which
    keeps every facet planar. Glass slabs on every facet wide enough, a
    visor roof over it all. Returns the roof's top height."""
    chamfer_y = sorted({y for _, y in plan})[-2]       # the front chamfers' aft ends
    base = [V(x, y, z_base) for x, y in plan]
    sill = [V(x, y, z_sill) for x, y in plan]
    head = [V(x, y + (rake if y >= chamfer_y - 1e-6 else 0.0), z_head) for x, y in plan]
    top = [V(p.x, p.y, z_top) for p in head]
    bm, _ = loft_bm([base, sill, head, top])
    finish(f"{prefix}{body}", bm, coll, [m["house"]], variant)
    cx = sum(x for x, _ in plan) / len(plan)
    cy = sum(y for _, y in plan) / len(plan)
    centre = V(cx, cy, 0.0)
    n = len(plan)
    for i in range(n):
        if i in skip_facets:
            continue
        j = (i + 1) % n
        width = (sill[j] - sill[i]).length
        spans = spans_fn(width) if spans_fn else pane_spans(width, pitch)
        if spans:
            facet_panes(f"{prefix}{glass}_{i}", coll, m["glass"], sill[i], sill[j], head[i], head[j],
                        centre, spans, variant)
    roof = offset_poly([(p.x, p.y) for p in head], roof_over)
    bm, _ = prism_bm(roof, z_top - 0.02, z_top + roof_t)
    finish(f"{prefix}{roof_name}", bm, coll, [m["house"]], variant)
    return z_top + roof_t


def window_spans(width, w=0.70, pitch=1.40, ins=0.30):
    """Small windows `w` wide at `pitch`, centred on a facet, none on a
    facet too narrow for one with `ins` of wall each side."""
    count = int((width - 2 * ins + (pitch - w)) // pitch)
    if count < 1:
        return []
    s0 = (width - (count * w + (count - 1) * (pitch - w))) / 2
    return [((s0 + k * pitch) / width, (s0 + k * pitch + w) / width) for k in range(count)]


def stack(name, coll, m, x, y, plan_wh, z0, z1, rake, band, soot, variant):
    """A raked funnel: a chamfered rectangle lofted from z0 to z1, its top
    `rake` aft, with a coloured band and a soot cap as rings 3 cm proud."""
    w, h = plan_wh[0] / 2, plan_wh[1] / 2
    c = min(w, h) * 0.45
    poly = [(w - c, h), (w, h - c), (w, -h + c), (w - c, -h), (-w + c, -h), (-w, -h + c), (-w, h - c), (-w + c, h)]

    def ring(z, d=0.0):
        s = -rake * (z - z0) / (z1 - z0)
        return [V(x + px, y + py + s, z) for px, py in offset_poly(poly, d)]

    bm, _ = loft_bm([ring(z0), ring(z1)])
    finish(name, bm, coll, [m["stack"]], variant)
    bm, _ = loft_bm([ring(band[0], 0.03), ring(band[1], 0.03)])
    finish(f"{name}_band", bm, coll, [m["band"]], variant)
    bm, _ = loft_bm([ring(soot, 0.03), ring(z1 + 0.03, 0.03)])
    finish(f"{name}_soot", bm, coll, [m["soot"]], variant)


def mast(prefix, coll, m, x, y, z0, z1, w0, w1, yard_z, yard_hl, variant, mat_key="house"):
    """A tapered square pole and a yard across it."""
    def sq(z, w):
        return [V(x - w, y - w, z), V(x + w, y - w, z), V(x + w, y + w, z), V(x - w, y + w, z)]
    bm, _ = loft_bm([sq(z0, w0 / 2), sq(z1, w1 / 2)])   # z0 is 6 cm into the roof
    finish(f"{prefix}mast", bm, coll, [m[mat_key]], variant)
    box(f"{prefix}mast_yard", coll, m[mat_key], x - yard_hl, x + yard_hl, y - 0.06, y + 0.06,
        yard_z - 0.06, yard_z + 0.06, variant)
    # the mast's width at a height, for hanging lights on its front
    return lambda z: w0 + (w1 - w0) * (z - z0) / (z1 - z0)


def rail_path(name, coll, mat, pts2d, z0, z1, half, variant):
    """A bar along an open plan path, mitred at its corners, capped at its ends."""
    pts = [Vector(p) for p in pts2d]
    n = len(pts)
    rings = []
    for i in range(n):
        if i == 0:
            d = (pts[1] - pts[0]).normalized()
            nv = Vector((d.y, -d.x))
        elif i == n - 1:
            d = (pts[-1] - pts[-2]).normalized()
            nv = Vector((d.y, -d.x))
        else:
            d0, d1 = (pts[i] - pts[i - 1]).normalized(), (pts[i + 1] - pts[i]).normalized()
            n0, n1 = Vector((d0.y, -d0.x)), Vector((d1.y, -d1.x))
            nv = (n0 + n1) / (1 + n0.dot(n1))
        a, b = pts[i] + nv * half, pts[i] - nv * half
        rings.append([V(a.x, a.y, z0), V(a.x, a.y, z1), V(b.x, b.y, z1), V(b.x, b.y, z0)])
    bm, _ = loft_bm(rings)
    return finish(name, bm, coll, [mat], variant)


def posts_along(prefix, coll, mat, pts2d, z0f, z1f, w, spacing, variant):
    """Square posts at every corner of a path and between them at no more
    than `spacing`; z0f and z1f give each post's foot and head by (x, y)."""
    spots = []
    pts = [Vector(p) for p in pts2d]
    for a, b in zip(pts, pts[1:]):
        k = max(1, math.ceil((b - a).length / spacing))
        spots.extend(a.lerp(b, t / k) for t in range(k))
    spots.append(pts[-1])
    for i, p in enumerate(spots):
        box(f"{prefix}_{i:02d}", coll, mat, p.x - w / 2, p.x + w / 2, p.y - w / 2, p.y + w / 2,
            z0f(p), z1f(p), variant)
    return len(spots)


# --- shared fittings (one mesh each, linked copies) ------------------------------------

def fitting_meshes(m):
    """The fittings the craft share, each one mesh about its own foot."""
    out = {}
    # an H-bitt: two 0.36 m posts 1.5 m apart and a crossbar through them,
    # standing 1.05 m over its foot, buried 0.12 m into the deck
    bm, _ = box_bm(-0.93, -0.57, -0.18, 0.18, -0.12, 1.05)
    box_bm(0.57, 0.93, -0.18, 0.18, -0.12, 1.05, bm=bm)
    box_bm(-1.10, 1.10, -0.13, 0.13, 0.60, 0.86, bm=bm)
    out["bitt"] = make_mesh("harbour_craft_bitt", bm, [m["fittings"]])
    # a life-raft canister on its cradle, foot buried 0.07 m
    bm, _ = box_bm(-0.45, 0.45, -0.70, 0.70, -0.07, 0.22)
    _, cyl = cylinder_bm("y", (0.0, 0.0, 0.52), 0.33, 0.62, 10, bm=bm)
    for f in cyl:
        f.material_index = 1
    out["raft"] = make_mesh("harbour_craft_raft", bm, [m["fittings"], m["raft"]])
    # a radar scanner on its pedestal, foot buried 0.04 m
    bm, _ = box_bm(-0.18, 0.18, -0.18, 0.18, -0.04, 0.36)
    box_bm(-1.00, 1.00, -0.11, 0.11, 0.34, 0.48, bm=bm)
    out["radar"] = make_mesh("harbour_craft_radar", bm, [m["fittings"]])
    # a searchlight: a post and a lamp pointing forward, foot buried 0.05 m
    bm, _ = box_bm(-0.06, 0.06, -0.06, 0.06, -0.05, 0.38)
    cylinder_bm("y", (0.0, 0.02, 0.50), 0.17, 0.20, 8, bm=bm)
    out["searchlight"] = make_mesh("harbour_craft_searchlight", bm, [m["fittings"]])
    # a navigation light's housing
    lx, ly, lz = NAVLIGHT
    bm, _ = box_bm(-lx / 2, lx / 2, -ly / 2, ly / 2, 0.0, lz)
    out["navlight"] = make_mesh("harbour_craft_navlight", bm, [m["light"]])
    return out


def lights_on_mast(prefix, coll, fit, x, y, width_at, heights, top, variant):
    """Towing lights hung on the mast's forward face, 2 cm into it, and one on its top."""
    for k, z in enumerate(heights):
        front = y + width_at(z + NAVLIGHT[2] / 2) / 2
        place(f"{prefix}towing_light_{k}", fit["navlight"], coll, (x, front + NAVLIGHT[1] / 2 - 0.02, z), variant)
    place(f"{prefix}masthead_light", fit["navlight"], coll, (x, y, top - 0.02), variant)


# --- the ASD tug -----------------------------------------------------------------

def build_tug(coll, m, fit, variant="tug", prefix=""):
    hull = Hull(TUG_STATIONS, TUG_CAMBER)
    hull.build(f"{prefix}hull", coll, m, variant)
    bul, *_ = hull.wall(f"{prefix}bulwark", coll, m["hull"], BULWARK_INSET, TUG_BULWARK_T,
                        lambda z: z - 0.15, lambda z: z + TUG_BULWARK_H, variant)
    hull.wall(f"{prefix}cap_rail", coll, m["band"], BULWARK_INSET - 0.03, TUG_BULWARK_T + 0.06,
              lambda z: z + TUG_BULWARK_H - 0.03, lambda z: z + TUG_BULWARK_H + CAP_H - 0.03, variant)
    both = bvh_of([hull.obj, bul])
    # the bow and stern fenders: aprons of W-blocks hugging the plating and
    # the bulwark, a big cylinder along the bulwark's top over them
    bow = hull.indices(lambda p: p.y >= TUG_BOW_FENDER_FROM_Y - 1e-6)
    hull.apron(f"{prefix}bow_fender_blocks", coll, m["rubber"], bow,
               lambda z: TUG_APRON_LOW, lambda z: z + TUG_BULWARK_H - 0.35, 5, TUG_APRON_T, 0.08, variant, bvh=both)
    hull.tube_along(f"{prefix}bow_fender", coll, m["rubber"], bow, TUG_BOW_TUBE_R, TUG_BOW_TUBE_OUT,
                    lambda z: z + TUG_BULWARK_H - 0.12, 8, variant)
    stern = hull.indices(lambda p: p.y <= TUG_STERN_FENDER_TO_Y + 1e-6)
    hull.apron(f"{prefix}stern_fender_blocks", coll, m["rubber"], stern,
               lambda z: TUG_STERN_APRON_LOW, lambda z: z + TUG_BULWARK_H - 0.35, 4, TUG_APRON_T - 0.05, 0.08,
               variant, bvh=both)
    transom = hull.indices(lambda p: p.y <= TUG_STERN_TUBE_Y + 1e-6)
    hull.tube_along(f"{prefix}stern_fender", coll, m["rubber"], transom, TUG_STERN_TUBE_R, TUG_STERN_TUBE_OUT,
                    lambda z: z + TUG_BULWARK_H - 0.12, 8, variant)
    # the D-fender along each side, its ends buried in the bow and stern blocks
    for side, sgn in (("s", 1), ("p", -1)):
        run = hull.indices(lambda p, s=sgn: p.x * s > 0 and TUG_STERN_FENDER_TO_Y - 0.5 <= p.y <= TUG_BOW_FENDER_FROM_Y + 0.5)
        hull.tube_along(f"{prefix}d_fender_{side}", coll, m["rubber"], run, TUG_D_FENDER_R, 0.06,
                        lambda z: z - 0.35, 6, variant, hug=hull.bvh)

    # the deckhouse, its doors and windows
    house_base = hull.deck_z(min(y for _, y in TUG_HOUSE)) - 0.12
    bm, _ = prism_bm(TUG_HOUSE, house_base, TUG_HOUSE_TOP)
    finish(f"{prefix}deckhouse", bm, coll, [m["house"]], variant)
    hw = max(x for x, _ in TUG_HOUSE)
    for side, sgn in (("s", 1), ("p", -1)):
        x0, x1 = (hw - 0.03, hw + 0.04) if sgn > 0 else (-hw - 0.04, -hw + 0.03)
        dz = hull.deck_z(-4.3)
        box(f"{prefix}house_door_{side}", coll, m["glass"], x0, x1, -4.30, -3.40, dz + 0.06, dz + 2.05, variant)
        for k, (y0, y1) in enumerate(((-1.60, -0.70), (0.60, 1.50), (2.20, 3.10))):
            box(f"{prefix}house_window_{side}{k}", coll, m["glass"], x0, x1, y0, y1, 2.75, 3.55, variant)
    fy = max(y for _, y in TUG_HOUSE)
    for k, (a, b) in enumerate(((-1.90, -0.90), (0.90, 1.90))):
        box(f"{prefix}house_front_window_{k}", coll, m["glass"], a, b, fy - 0.03, fy + 0.04, 2.90, 3.60, variant)
    ay = min(y for _, y in TUG_HOUSE)
    dz = hull.deck_z(ay)
    box(f"{prefix}house_aft_door", coll, m["glass"], -0.45, 0.45, ay - 0.04, ay + 0.03, dz + 0.06, dz + 2.05, variant)

    # the wheelhouse, well forward on the house, glass all round
    roof_top = wheelhouse(prefix, coll, m, TUG_WH_PLAN, TUG_HOUSE_TOP - 0.05, TUG_WH_SILL, TUG_WH_HEAD, TUG_WH_TOP,
                          TUG_WH_RAKE, variant, pitch=1.15, roof_over=TUG_ROOF_OVER, roof_t=TUG_ROOF_T)
    # the house top's rail round the wheelhouse
    rail_path(f"{prefix}house_rail", coll, m["rails"], TUG_RAIL_PATH, TUG_HOUSE_TOP + 0.97,
              TUG_HOUSE_TOP + 0.97 + RAIL_BAR, RAIL_BAR / 2, variant)
    rail_path(f"{prefix}house_mid_rail", coll, m["rails"], TUG_RAIL_PATH, TUG_HOUSE_TOP + 0.50,
              TUG_HOUSE_TOP + 0.50 + RAIL_BAR, RAIL_BAR / 2, variant)
    posts_along(f"{prefix}house_rail_post", coll, m["rails"], TUG_RAIL_PATH, lambda p: TUG_HOUSE_TOP - 0.03,
                lambda p: TUG_HOUSE_TOP + 0.97 + RAIL_BAR + 0.02, 0.07, 1.7, variant)
    # the mast on the wheelhouse roof: three towing lights on its face, a
    # masthead light, a yard; radar and searchlight on the roof
    mx, my = TUG_MAST_AT
    width_at = mast(prefix, coll, m, mx, my, roof_top - 0.06, TUG_MAST_TOP, 0.30, 0.16,
                    TUG_MAST_TOP - 1.90, 1.10, variant)
    lights_on_mast(prefix, coll, fit, mx, my, width_at, (TUG_MAST_TOP - 1.50, TUG_MAST_TOP - 1.05, TUG_MAST_TOP - 0.60),
                   TUG_MAST_TOP, variant)
    place(f"{prefix}radar", fit["radar"], coll, (0.0, RADAR_ROOF_Y, roof_top), variant)
    place(f"{prefix}searchlight", fit["searchlight"], coll, (0.0, 3.90, roof_top), variant)
    # twin stacks aft of the wheelhouse
    for side, sgn in (("s", 1), ("p", -1)):
        stack(f"{prefix}stack_{side}", coll, m, sgn * TUG_STACK_X, TUG_STACK_Y, TUG_STACK_PLAN,
              TUG_HOUSE_TOP - 0.10, TUG_STACK_TOP, TUG_STACK_RAKE, TUG_STACK_BAND, TUG_STACK_SOOT, variant)
        place(f"{prefix}life_raft_{side}", fit["raft"], coll, (sgn * 2.55, -4.55, TUG_HOUSE_TOP), variant)

    # the foredeck: the hawser winch ahead of the house, an H-bitt, the bow staple
    y0, y1 = TUG_WINCH_SPAN
    z0, z1 = hull.deck_z(y0) - 0.12, hull.deck_z(y1) + 0.22
    box(f"{prefix}winch_bed", coll, m["fittings"], -1.35, 1.35, y0, y1, z0, z1, variant)
    for side, sgn in (("s", 1), ("p", -1)):
        a, b = sorted((sgn * 1.00, sgn * 1.16))
        box(f"{prefix}winch_frame_{side}", coll, m["fittings"], a, b, y0 + 0.10, y1 - 0.10, z1 - 0.02, z1 + 1.30, variant)
    bm, _ = cylinder_bm("x", (0.0, (y0 + y1) / 2, z1 + 0.68), 0.52, 1.02, 12)
    finish(f"{prefix}winch_drum", bm, coll, [m["band"]], variant)
    place(f"{prefix}bitt_fore", fit["bitt"], coll, (0.0, 9.80, hull.deck_z(9.80)), variant)
    place(f"{prefix}bitt_aft", fit["bitt"], coll, (0.0, -11.20, hull.deck_z(-11.20)), variant)
    sy = TUG_STAPLE_Y
    sz = hull.deck_z(sy)
    for side, sgn in (("s", 1), ("p", -1)):
        a, b = sorted((sgn * 0.40, sgn * 0.72))
        box(f"{prefix}staple_post_{side}", coll, m["fittings"], a, b, sy - 0.16, sy + 0.16, sz - 0.11,
            sz + TUG_BULWARK_H + 0.75, variant)
    box(f"{prefix}staple_bar", coll, m["fittings"], -0.86, 0.86, sy - 0.12, sy + 0.12,
        sz + TUG_BULWARK_H + 0.55, sz + TUG_BULWARK_H + 0.83, variant)

    # under water: the box skeg and the two Z-drives
    yz_prism(f"{prefix}skeg", coll, m["bottom"], TUG_SKEG, -0.30, 0.30, variant)
    for side, sgn in (("s", 1), ("p", -1)):
        x = sgn * TUG_DRIVE_X
        box(f"{prefix}drive_leg_{side}", coll, m["bottom"], x - 0.25, x + 0.25, TUG_DRIVE_Y - 0.35,
            TUG_DRIVE_Y + 0.35, TUG_NOZZLE_Z + TUG_NOZZLE_R - 0.20, -1.40, variant)
        bm, _ = cylinder_bm("y", (x, TUG_DRIVE_Y, TUG_NOZZLE_Z), TUG_NOZZLE_R, TUG_NOZZLE_HL, 12)
        finish(f"{prefix}drive_nozzle_{side}", bm, coll, [m["bottom"]], variant)
    return hull


# --- the pilot boat ------------------------------------------------------------------

def build_pilot(coll, m, fit, variant="pilot_boat", prefix="pilot_"):
    hull = Hull(PILOT_STATIONS, PILOT_CAMBER)
    hull.build(f"{prefix}hull", coll, m, variant)
    every = list(range(len(hull.loop)))
    hull.tube_along(f"{prefix}collar", coll, m["rubber"], every, PILOT_COLLAR_R, 0.02,
                    lambda z: z - 0.12, 6, variant, closed=True)
    # the band where a real pilot boat says PILOT, unlettered, on each side
    y0, y1, foot, head = PILOT_BAND
    for side, sgn in (("s", 1), ("p", -1)):
        run = hull.indices(lambda p, s=sgn: p.x * s > 0 and y0 - 1e-6 <= p.y <= y1 + 1e-6)
        hull.apron(f"{prefix}band_{side}", coll, m["band"], run, lambda z: z - foot, lambda z: z - head,
                   2, 0.04, 0.03, variant, step=0.5)
    # rails all round the deck, inside the collar, on stanchions
    _, pts, zs, ns = hull.wall(f"{prefix}rail_top", coll, m["rails"], PILOT_RAIL_INSET - RAIL_BAR / 2, RAIL_BAR,
                               lambda z: z + PILOT_RAIL_H, lambda z: z + PILOT_RAIL_H + RAIL_BAR, variant,
                               skip_ends=1)
    hull.wall(f"{prefix}rail_mid", coll, m["rails"], PILOT_RAIL_INSET - RAIL_BAR / 2 + 0.005, RAIL_BAR - 0.01,
              lambda z: z + PILOT_MID_RAIL, lambda z: z + PILOT_MID_RAIL + RAIL_BAR - 0.01, variant, skip_ends=1)
    for k, (p, zd, nv) in enumerate(zip(pts, zs, ns)):
        c = p - nv * PILOT_RAIL_INSET
        box(f"{prefix}stanchion_{k:02d}", coll, m["rails"], c.x - 0.035, c.x + 0.035, c.y - 0.035, c.y + 0.035,
            zd - 0.06, zd + PILOT_RAIL_H + RAIL_BAR + 0.02, variant)

    # the cabin, set forward, big windows, the windscreen raked back; a door aft
    roof_top = wheelhouse(prefix, coll, m, PILOT_CABIN, PILOT_CABIN_BASE, PILOT_SILL, PILOT_HEAD, PILOT_TOP,
                          PILOT_RAKE, variant, pitch=1.35, roof_over=PILOT_ROOF_OVER, roof_t=PILOT_ROOF_T,
                          skip_facets=(3,))
    ay = min(y for _, y in PILOT_CABIN)
    dz = hull.deck_z(ay)
    box(f"{prefix}cabin_door", coll, m["glass"], -1.05, -0.25, ay - 0.04, ay + 0.03, dz + 0.06, PILOT_HEAD - 0.07, variant)
    box(f"{prefix}cabin_aft_window", coll, m["glass"], 0.15, 1.15, ay - 0.04, ay + 0.03, PILOT_SILL + 0.07,
        PILOT_HEAD - 0.07, variant)
    # grab rails along the cabin top, each on three posts
    for side, sgn in (("s", 1), ("p", -1)):
        x = sgn * 1.45
        box(f"{prefix}grab_rail_{side}", coll, m["rails"], x - 0.03, x + 0.03, -1.20, 2.60, roof_top + 0.28,
            roof_top + 0.34, variant)
        for k, y in enumerate((-1.10, 0.75, 2.50)):
            box(f"{prefix}grab_post_{side}{k}", coll, m["rails"], x - 0.025, x + 0.025, y - 0.025, y + 0.025,
                roof_top - 0.04, roof_top + 0.30, variant)
    mx, my = PILOT_MAST_AT
    width_at = mast(prefix, coll, m, mx, my, roof_top - 0.06, PILOT_MAST_TOP, 0.16, 0.09,
                    PILOT_MAST_TOP - 0.80, 0.75, variant, mat_key="rails")
    lights_on_mast(prefix, coll, fit, mx, my, width_at, (PILOT_MAST_TOP - 0.55,), PILOT_MAST_TOP, variant)
    place(f"{prefix}radar", fit["radar"], coll, (0.0, 0.90, roof_top), variant)
    place(f"{prefix}searchlight", fit["searchlight"], coll, (0.0, 2.75, roof_top), variant)

    # under water: the keel skeg, twin shafts, struts, propellers and rudders
    yz_prism(f"{prefix}skeg", coll, m["bottom"], PILOT_SKEG, -0.07, 0.07, variant)
    for side, sgn in (("s", 1), ("p", -1)):
        x = sgn * PILOT_PROP_X
        bm, _ = cylinder_bm("y", (x, PILOT_PROP_Y, PILOT_PROP_Z), PILOT_PROP_R, 0.12, 10)
        finish(f"{prefix}propeller_{side}", bm, coll, [m["fittings"]], variant)
        shaft = [V(x, PILOT_PROP_Y + 0.10, PILOT_PROP_Z), V(x, -3.00, -0.52)]
        finish(f"{prefix}shaft_{side}", tube_bm(shaft, 0.06, 6), coll, [m["fittings"]], variant)
        box(f"{prefix}strut_{side}", coll, m["fittings"], x - 0.04, x + 0.04, -6.05, -5.85, -1.06, -0.42, variant)
        box(f"{prefix}rudder_{side}", coll, m["fittings"], x - 0.04, x + 0.04, -7.60, -7.00, -1.42, -0.38, variant)
    return hull


# --- the conventional tug ---------------------------------------------------------------

def build_conventional(coll, m, fit, variant="tug_conventional", prefix="conventional_"):
    hull = Hull(CONV_STATIONS, CONV_CAMBER)
    hull.build(f"{prefix}hull", coll, m, variant)
    hull.wall(f"{prefix}bulwark", coll, m["hull"], BULWARK_INSET, CONV_BULWARK_T,
              lambda z: z - 0.15, lambda z: z + CONV_BULWARK_H, variant)
    hull.wall(f"{prefix}cap_rail", coll, m["house"], BULWARK_INSET - 0.03, CONV_BULWARK_T + 0.06,
              lambda z: z + CONV_BULWARK_H - 0.03, lambda z: z + CONV_BULWARK_H + CAP_H - 0.03, variant)
    # the rope bow pudding over the stem, a beard down it, the stern fender
    # round the fantail and a rubbing strake along each side between them
    bow = hull.indices(lambda p: p.y >= CONV_PUDDING_FROM_Y - 1e-6)
    hull.tube_along(f"{prefix}bow_pudding", coll, m["rubber"], bow, CONV_PUDDING_R, 0.18,
                    lambda z: z - 0.30, 8, variant, hug=hull.bvh)
    beard = []
    for z in (2.80, 2.00, 1.20, 0.45):
        hit = hull_hit(hull.bvh, Vector((0.0, 12.8)), Vector((0.0, 1.0)), z)
        beard.append(V(0.0, hit.y + 0.12, z))
    finish(f"{prefix}bow_beard", tube_bm(beard, 0.30, 8), coll, [m["rubber"]], variant)
    stern = hull.indices(lambda p: p.y <= CONV_STERN_TO_Y + 1e-6)
    hull.tube_along(f"{prefix}stern_fender", coll, m["rubber"], stern, CONV_STERN_R, 0.05,
                    lambda z: z - 0.28, 8, variant, hug=hull.bvh)
    for side, sgn in (("s", 1), ("p", -1)):
        run = hull.indices(lambda p, s=sgn: p.x * s > 0 and CONV_STERN_TO_Y - 0.5 <= p.y <= CONV_PUDDING_FROM_Y + 1.0)
        hull.tube_along(f"{prefix}rubbing_strake_{side}", coll, m["rubber"], run, CONV_GUARD_R, 0.04,
                        lambda z: z - 0.28, 6, variant, hug=hull.bvh)

    # the deckhouse straddling midships, doors and windows
    house_base = hull.deck_z(min(y for _, y in CONV_HOUSE)) - 0.12
    bm, _ = prism_bm(CONV_HOUSE, house_base, CONV_HOUSE_TOP)
    finish(f"{prefix}deckhouse", bm, coll, [m["house"]], variant)
    hw = max(x for x, _ in CONV_HOUSE)
    for side, sgn in (("s", 1), ("p", -1)):
        x0, x1 = (hw - 0.03, hw + 0.04) if sgn > 0 else (-hw - 0.04, -hw + 0.03)
        dz = hull.deck_z(-3.0)
        box(f"{prefix}house_door_{side}", coll, m["glass"], x0, x1, -3.40, -2.60, dz + 0.06, dz + 1.95, variant)
        for k, (y0, y1) in enumerate(((-0.80, -0.20), (1.00, 1.60), (2.60, 3.20))):
            box(f"{prefix}house_porthole_{side}{k}", coll, m["glass"], x0, x1, y0, y1, 2.70, 3.30, variant)
    wh_roof = wheelhouse(prefix, coll, m, CONV_WH_PLAN, CONV_HOUSE_TOP - 0.05, CONV_WH_SILL, CONV_WH_HEAD,
                         CONV_WH_TOP, 0.0, variant, pitch=0.95, roof_over=CONV_ROOF_OVER, roof_t=CONV_ROOF_T)
    mx, my = CONV_MAST_AT
    width_at = mast(prefix, coll, m, mx, my, wh_roof - 0.06, CONV_MAST_TOP, 0.26, 0.14,
                    CONV_MAST_TOP - 1.70, 1.00, variant)
    lights_on_mast(prefix, coll, fit, mx, my, width_at, (CONV_MAST_TOP - 1.35, CONV_MAST_TOP - 0.95, CONV_MAST_TOP - 0.55),
                   CONV_MAST_TOP, variant)
    place(f"{prefix}radar", fit["radar"], coll, (0.0, 1.70, wh_roof), variant)
    place(f"{prefix}searchlight", fit["searchlight"], coll, (1.20, 3.40, wh_roof), variant)
    stack(f"{prefix}stack", coll, m, 0.0, CONV_STACK_Y, CONV_STACK_PLAN, CONV_HOUSE_TOP - 0.10,
          CONV_STACK_TOP, CONV_STACK_RAKE, (6.40, 6.95), 7.55, variant)
    for side, sgn in (("s", 1), ("p", -1)):
        place(f"{prefix}life_raft_{side}", fit["raft"], coll, (sgn * 1.70, -4.10, CONV_HOUSE_TOP), variant)

    # the foredeck bitt; the towing hook on its post aft of the house; the tow bows
    place(f"{prefix}bitt_fore", fit["bitt"], coll, (0.0, 9.20, hull.deck_z(9.20)), variant)
    ty = CONV_TOW_POST_Y
    tz = hull.deck_z(ty)
    box(f"{prefix}tow_post", coll, m["fittings"], -0.26, 0.26, ty - 0.26, ty + 0.26, tz - 0.13, tz + 1.45, variant)
    box(f"{prefix}tow_hook", coll, m["band"], -0.13, 0.13, ty - 0.62, ty - 0.24, tz + 0.85, tz + 1.30, variant)
    for k, by in enumerate(CONV_TOW_BOWS_Y):
        half = hull.half_breadth(by) - BULWARK_INSET - CONV_BULWARK_T / 2
        base = hull.deck_z(by) + CONV_BULWARK_H + 0.02
        arc = [V(half * math.cos(a), by, base + CONV_TOW_BOW_RISE * math.sin(a))
               for a in (math.pi * t / 10 for t in range(11))]
        finish(f"{prefix}tow_bow_{k}", tube_bm(arc, 0.08, 4), coll, [m["fittings"]], variant)

    # under water: the deadwood, its keel shoe, the propeller and the rudder
    yz_prism(f"{prefix}deadwood", coll, m["bottom"], CONV_SKEG, -0.22, 0.22, variant)
    # the shoe laps 5 cm into the deadwood's after edge and stands 2 cm
    # shallower than its foot, so their bottoms never share a plane
    box(f"{prefix}keel_shoe", coll, m["bottom"], -0.14, 0.14, -12.35, CONV_SKEG[2][0] - 0.05, -3.58, -3.35, variant)
    bm, _ = cylinder_bm("y", (0.0, CONV_PROP_Y, CONV_PROP_Z), CONV_PROP_R, 0.15, 12)
    finish(f"{prefix}propeller", bm, coll, [m["fittings"]], variant)
    box(f"{prefix}rudder", coll, m["bottom"], -0.10, 0.10, -12.30, -11.30, -3.40, -0.50, variant)
    return hull


# --- the variants: linked copies and what each changes --------------------------------

def link_parts(coll, variant, prefix, src_prefix, src_variant, keep, offset=(0.0, 0.0, 0.0)):
    """Linked copies of another variant's parts: the same mesh, so reshaping
    one reshapes both, in an object of this variant's own, moved by
    `offset`. `keep(name)` picks them by name without the source's prefix."""
    out = []
    srcs = sorted((o for o in bpy.data.collections["export"].all_objects
                   if o.type == "MESH" and o.get("kyt_variant") == src_variant), key=lambda o: o.name)
    for src in srcs:
        base = src.name[len(src_prefix):]
        if not keep(base):
            continue
        dup = bpy.data.objects.new(f"{prefix}{base}", src.data)
        dup.location = src.location + Vector(offset)
        coll.objects.link(dup)
        out.append(tag(dup, variant))
    return out


def recolour(coll, variant, prefix, src_prefix, base, swap):
    """A copy of a part's mesh with some materials swapped: the same shape in
    another colour (a linked mesh would carry the source's colours)."""
    src = bpy.data.objects[f"{src_prefix}{base}"]
    me = src.data.copy()
    me.name = f"{prefix}{base}"
    for i, mt in enumerate(me.materials):
        if mt is not None and mt.name in swap:
            me.materials[i] = swap[mt.name]
    dup = bpy.data.objects.new(f"{prefix}{base}", me)
    dup.location = src.location
    coll.objects.link(dup)
    return tag(dup, variant)


def build_escort(coll, m, fit, hull, variant="tug_escort", prefix="escort_"):
    """The tug with its wheelhouse on a second tier; everything below the
    house top, the house, its rails and rafts are the tug's own meshes."""
    own = ("wheelhouse", "wh_glass_", "roof", "mast", "towing_light_", "masthead_light", "radar",
           "searchlight", "stack_")
    link_parts(coll, variant, prefix, "", "tug", lambda b: not b.startswith(own))
    # the tier: the wheelhouse's plan 15 cm larger, small windows, a ledge roof
    tier = offset_poly(TUG_WH_PLAN, ESCORT_TIER_OUT)
    ledge_top = wheelhouse(prefix, coll, m, tier, TUG_HOUSE_TOP - 0.05, ESCORT_TIER_SILL, ESCORT_TIER_HEAD,
                           ESCORT_TIER_TOP, 0.0, variant, pitch=None, roof_over=ESCORT_LEDGE_OVER,
                           roof_t=ESCORT_LEDGE_T, body="tier", glass="tier_glass", roof_name="tier_ledge",
                           spans_fn=window_spans)
    # the tug's wheelhouse, every height lifted by the tier
    lift = ledge_top - TUG_HOUSE_TOP
    roof_top = wheelhouse(prefix, coll, m, TUG_WH_PLAN, TUG_HOUSE_TOP - 0.05 + lift, TUG_WH_SILL + lift,
                          TUG_WH_HEAD + lift, TUG_WH_TOP + lift, TUG_WH_RAKE, variant, pitch=1.15,
                          roof_over=TUG_ROOF_OVER, roof_t=TUG_ROOF_T)
    mx, my = TUG_MAST_AT
    width_at = mast(prefix, coll, m, mx, my, roof_top - 0.06, ESCORT_MAST_TOP, 0.30, 0.16,
                    ESCORT_MAST_TOP - 1.90, 1.10, variant)
    lights_on_mast(prefix, coll, fit, mx, my, width_at,
                   (ESCORT_MAST_TOP - 1.50, ESCORT_MAST_TOP - 1.05, ESCORT_MAST_TOP - 0.60), ESCORT_MAST_TOP, variant)
    place(f"{prefix}radar", fit["radar"], coll, (0.0, RADAR_ROOF_Y, roof_top), variant)
    place(f"{prefix}searchlight", fit["searchlight"], coll, (0.0, 3.90, roof_top), variant)
    # the stacks lifted with it, so the exhaust still clears the wheelhouse
    for side, sgn in (("s", 1), ("p", -1)):
        stack(f"{prefix}stack_{side}", coll, m, sgn * TUG_STACK_X, TUG_STACK_Y, TUG_STACK_PLAN,
              TUG_HOUSE_TOP - 0.10, TUG_STACK_TOP + lift, TUG_STACK_RAKE,
              (TUG_STACK_BAND[0] + lift, TUG_STACK_BAND[1] + lift), TUG_STACK_SOOT + lift, variant)


def build_tractor(coll, m, fit, hull, variant="tug_tractor", prefix="tractor_"):
    """The tug driven from forward: her drives moved forward, a big skeg aft,
    the winch moved to the after deck and the staple to the stern, the
    after bitt gone from the towline's path; the rest is the tug's meshes."""
    own = ("skeg", "drive_", "winch_", "staple_", "bitt_aft", "radar")
    link_parts(coll, variant, prefix, "", "tug", lambda b: not b.startswith(own))
    link_parts(coll, variant, prefix, "", "tug", lambda b: b.startswith("drive_"),
               offset=(0.0, TRACTOR_DRIVE_Y - TUG_DRIVE_Y, 0.0))
    wy = sum(TUG_WINCH_SPAN) / 2
    link_parts(coll, variant, prefix, "", "tug", lambda b: b.startswith("winch_"),
               offset=(0.0, TRACTOR_WINCH_Y - wy, hull.deck_z(TRACTOR_WINCH_Y) - hull.deck_z(wy)))
    link_parts(coll, variant, prefix, "", "tug", lambda b: b.startswith("staple_"),
               offset=(0.0, TRACTOR_STAPLE_Y - TUG_STAPLE_Y, hull.deck_z(TRACTOR_STAPLE_Y) - hull.deck_z(TUG_STAPLE_Y)))
    yz_prism(f"{prefix}skeg", coll, m["bottom"], TRACTOR_SKEG, -TRACTOR_SKEG_HALF, TRACTOR_SKEG_HALF, variant)
    place(f"{prefix}radar", fit["radar"], coll, (0.0, RADAR_ROOF_Y, TUG_WH_TOP + TUG_ROOF_T), variant)


def build_pilot_b(coll, fit, variant="pilot_boat_b", prefix="pilot_b_"):
    """The pilot boat with a reverse-raked windscreen, a white hull and an
    orange band; the rest is the pilot boat's meshes."""
    m = mats("pilot_")
    same = ("collar", "rail_", "stanchion_", "cabin_", "grab_", "mast", "towing_light_", "masthead_light",
            "radar", "searchlight", "skeg", "propeller_", "shaft_", "strut_", "rudder_")
    link_parts(coll, variant, prefix, "pilot_", "pilot_boat", lambda b: b.startswith(same))
    recolour(coll, variant, prefix, "pilot_", "hull", {f"{PROP}_pilot_hull": material(f"{PROP}_pilot_b_hull")})
    for side in ("s", "p"):
        recolour(coll, variant, prefix, "pilot_", f"band_{side}",
                 {f"{PROP}_pilot_band": material(f"{PROP}_pilot_b_band")})
    wheelhouse(prefix, coll, m, PILOT_CABIN, PILOT_CABIN_BASE, PILOT_SILL, PILOT_HEAD, PILOT_TOP,
               PILOT_B_RAKE, variant, pitch=1.35, roof_over=PILOT_ROOF_OVER, roof_t=PILOT_ROOF_T,
               skip_facets=(3,))


def build_conventional_b(coll, m, fit, hull, variant="tug_conventional_b", prefix="conventional_b_"):
    """The old tug with her whole house aft of midships, a long foredeck, a
    tall hinged foremast and tyre fenders; the hull and everything on it
    that did not move are the old tug's meshes, the house moved aft whole."""
    src, sp = "tug_conventional", "conventional_"
    still = ("hull", "bulwark", "cap_rail", "bow_pudding", "bow_beard", "stern_fender", "rubbing_strake_",
             "deadwood", "keel_shoe", "propeller", "rudder", "bitt_fore")
    moved = ("deckhouse", "house_", "wheelhouse", "wh_glass_", "roof", "stack", "life_raft_", "radar",
             "searchlight")
    link_parts(coll, variant, prefix, sp, src, lambda b: b.startswith(still))
    link_parts(coll, variant, prefix, sp, src, lambda b: b.startswith(moved), offset=(0.0, CONV_B_SHIFT, 0.0))
    link_parts(coll, variant, prefix, sp, src, lambda b: b.startswith(("tow_post", "tow_hook")),
               offset=(0.0, CONV_B_TOW_POST_Y - CONV_TOW_POST_Y,
                       hull.deck_z(CONV_B_TOW_POST_Y) - hull.deck_z(CONV_TOW_POST_Y)))
    # one tow bow over the short after deck
    by = CONV_B_TOW_BOW_Y
    half = hull.half_breadth(by) - BULWARK_INSET - CONV_BULWARK_T / 2
    base = hull.deck_z(by) + CONV_BULWARK_H + 0.02
    arc = [V(half * math.cos(a), by, base + CONV_TOW_BOW_RISE * math.sin(a))
           for a in (math.pi * t / 10 for t in range(11))]
    finish(f"{prefix}tow_bow", tube_bm(arc, 0.08, 4), coll, [m["fittings"]], variant)
    # the foremast in its tabernacle: two cheeks, a hinge pin through them
    # and the mast's heel, the heel standing clear of the deck so it can swing
    fy = CONV_B_FOREMAST_Y
    dz = hull.deck_z(fy)
    for side, sgn in (("s", 1), ("p", -1)):
        a, b = sorted((sgn * 0.17, sgn * 0.30))
        box(f"{prefix}tabernacle_{side}", coll, m["fittings"], a, b, fy - 0.20, fy + 0.20, dz - 0.12,
            dz + CONV_B_CHEEK_UP, variant)
    bm, _ = cylinder_bm("x", (0.0, fy, dz + CONV_B_HINGE_UP), 0.07, 0.34, 8)
    finish(f"{prefix}hinge_pin", bm, coll, [m["fittings"]], variant)
    width_at = mast(f"{prefix}fore", coll, m, 0.0, fy, dz + CONV_B_HEEL_UP, CONV_B_FOREMAST_TOP, 0.30, 0.15,
                    CONV_B_FOREMAST_TOP - 1.60, 1.00, variant)
    lights_on_mast(prefix, coll, fit, 0.0, fy, width_at,
                   (CONV_B_FOREMAST_TOP - 1.35, CONV_B_FOREMAST_TOP - 0.95, CONV_B_FOREMAST_TOP - 0.55),
                   CONV_B_FOREMAST_TOP, variant)
    # tyre fenders along both sides: one tyre mesh, hung over the rubbing
    # strake, its inner face 4 cm into the strake's outer side
    bm, _ = cylinder_bm("x", (0.0, 0.0, 0.0), CONV_B_TYRE_R, CONV_B_TYRE_T / 2, 10)
    tyre = make_mesh("harbour_craft_tyre", bm, [m["rubber"]])
    for side, sgn in (("s", 1), ("p", -1)):
        for k, ty in enumerate(CONV_B_TYRE_YS):
            dz = hull.deck_z(ty)
            hit = hull_hit(hull.bvh, Vector((sgn * hull.half_breadth(ty), ty)), Vector((sgn, 0.0)), dz - 0.28)
            inner = hit.x + sgn * (0.04 + CONV_GUARD_R - 0.04)     # the strake: 4 cm out, its radius
            place(f"{prefix}tyre_{side}{k}", tyre, coll, (inner + sgn * CONV_B_TYRE_T / 2, ty, dz - CONV_B_TYRE_DROP),
                  variant)


# --- reference ---------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm, _ = prism_bm(ring, 0.0, height - 0.40)
    body = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:
        if v not in body:
            v.co.z += height - 0.17
    obj = bpy.data.objects.new(name, make_mesh(name, bm, [mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0))],
                                               flat=False))
    obj.location = (x, y, z)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def outline(name, coll, x0, x1, y0, y1, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    for i in range(4):
        bm.edges.new((vs[i], vs[(i + 1) % 4]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


# --- checks ------------------------------------------------------------------

def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def triangles(objs):
    total = 0
    for o in objs:
        o.data.calc_loop_triangles()
        total += len(o.data.loop_triangles)
    return total


def bounds(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def coplanar_pairs(objs, tol=1e-4):
    """Faces of different objects in one plane whose bounds in that plane
    overlap: the z-fights. Bucketed by normal and swept by distance."""
    buckets = {}
    for o in objs:
        mw = o.matrix_world
        rot = mw.to_3x3()
        for p in o.data.polygons:
            n = (rot @ p.normal)
            if n.length < 1e-6:
                continue
            n.normalize()
            sign = next((1 if c > 0 else -1) for c in (round(n.x, 4), round(n.y, 4), round(n.z, 4), 1.0)
                        if abs(c) > 1e-3)
            n = n * sign
            pts = [mw @ o.data.vertices[i].co for i in p.vertices]
            d = n.dot(pts[0])
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            us = [q.dot(e1) for q in pts]
            vs = [q.dot(e2) for q in pts]
            key = (round(n.x, 3), round(n.y, 3), round(n.z, 3))
            buckets.setdefault(key, []).append((d, o.name, n, min(us), max(us), min(vs), max(vs),
                                                list(zip(us, vs))))
    found = []
    for faces in buckets.values():
        faces.sort(key=lambda f: f[0])
        for i in range(len(faces)):
            di, oi, ni, u0, u1, v0, v1, pi = faces[i]
            for j in range(i + 1, len(faces)):
                dj, oj, nj, w0, w1, x0, x1, pj = faces[j]
                if dj - di > tol:
                    break
                if oi == oj or (ni - nj).length > 1e-3:
                    continue
                ou, ov = min(u1, w1) - max(u0, w0), min(v1, x1) - max(v0, x0)
                if ou > 1e-3 and ov > 1e-3 and overlap_2d(convex(pi), convex(pj)):
                    found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def convex(pts):
    """The convex hull of 2D points, anticlockwise (monotone chain)."""
    pts = sorted(set((round(u, 6), round(v, 6)) for u, v in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def overlap_2d(a, b, eps=1e-3):
    """Whether two convex polygons overlap by more than eps (separating axes)."""
    if len(a) < 3 or len(b) < 3:
        return False
    for poly in (a, b):
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            nx, ny = y0 - y1, x1 - x0
            ln = math.hypot(nx, ny)
            if ln < 1e-9:
                continue
            nx, ny = nx / ln, ny / ln
            pa = [x * nx + y * ny for x, y in a]
            pb = [x * nx + y * ny for x, y in b]
            if min(max(pa), max(pb)) - max(min(pa), min(pb)) <= eps:
                return False
    return True


def report(variant):
    bpy.context.view_layer.update()
    objs = variant_objects(variant)
    tris = triangles(objs)
    lo, hi = bounds(objs)
    print(f"{PROP}: {variant}: {len(objs)} parts, {tris} triangles; length over all {hi.y - lo.y:.2f} m "
          f"(y {lo.y:.2f}..{hi.y:.2f}), beam {hi.x - lo.x:.2f} m, draft {-lo.z:.2f} m, air draft {hi.z:.2f} m")
    pairs = coplanar_pairs(objs)
    print(f"{PROP}: {variant}: {len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs[:12])))
    return lo, hi


# --- renders -----------------------------------------------------------------

def show_variant(variant):
    for v in VARIANTS:
        for o in variant_objects(v):
            o.hide_render = v != variant


def render(folder, hulls):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    water = mat("_water", (0.07, 0.24, 0.42))
    ink = mat("_ink", (0.02, 0.02, 0.02))
    line = mat("_waterline", (0.05, 0.35, 0.85))
    float_mat = mat("_float", (0.55, 0.50, 0.42))
    fig_mat = mat("_figure_stage", (0.85, 0.30, 0.55))
    water_obj = box("_water", stage, water, -400, 400, -400, 400, -0.30, 0.0, None)

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.70, 0.88, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.45, -0.65, 0.62)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False

    def shoot(name, eye, target, lens=35, size=(1600, 1000), ortho=None):
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 2000
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{PROP}: rendered {scene.render.filepath}")

    temp = []

    def clear():
        for o in temp:
            bpy.data.objects.remove(o, do_unlink=True)
        temp.clear()

    for v in VARIANTS:
        show_variant(v)
        lo, hi = bounds(variant_objects(v))
        L, B = hi.y - lo.y, hi.x - lo.x
        hull = hulls[v]
        # three-quarter from the starboard bow, on the water
        water_obj.hide_render = False
        shoot(f"{v}_three_quarter", (0.85 * L, 0.75 * L, 0.38 * L), (0.0, 0.0, 0.25 * hi.z), lens=40)
        # from the port quarter, lower
        shoot(f"{v}_port_quarter", (-0.80 * L, -0.80 * L, 0.22 * L), (0.0, 0.0, 0.25 * hi.z), lens=40)
        # plan from above, a 5 m bar and a metre grid on the water
        for gx in range(-int(B / 2) - 3, int(B / 2) + 4):
            temp.append(box(f"_grid_x{gx}", stage, ink, gx - 0.02, gx + 0.02, lo.y - 3, hi.y + 3, 0.0, 0.01, None))
        for gy in range(int(lo.y) - 3, int(hi.y) + 4):
            temp.append(box(f"_grid_y{gy}", stage, ink, -B / 2 - 3, B / 2 + 3, gy - 0.02, gy + 0.02, 0.0, 0.01, None))
        temp.append(box("_bar", stage, line, -B / 2 - 2.5, -B / 2 - 2.2, lo.y, lo.y + 5.0, 0.0, 0.03, None))
        shoot(f"{v}_plan", (0.0, (lo.y + hi.y) / 2, 200.0), (0.0, (lo.y + hi.y) / 2, 0.0), size=(900, 1400),
              ortho=max(L, B) + 8.0)
        clear()
        # side elevation from starboard, level at the waterline, the water
        # edge-on and a line marking z = 0 across the hull
        water_obj.hide_render = True
        temp.append(box("_wl", stage, line, B / 2 + 1.0, B / 2 + 1.05, lo.y - 6, hi.y + 6, -0.03, 0.03, None))
        span = max(L + 6.0, (hi.z - lo.z + 4.0) * 1.6)
        shoot(f"{v}_side_elevation", (200.0, 0.0, (hi.z + lo.z) / 2), (0.0, 0.0, (hi.z + lo.z) / 2),
              size=(1600, 1000), ortho=span)
        clear()
        # the hull below the waterline, from low off the starboard bow, the water gone
        shoot(f"{v}_hull_below", (1.00 * L, 0.45 * L, lo.z - 0.10 * L), (0.0, 0.0, 0.0), lens=30)
        # beside a 1.7 m figure: one on a float at the starboard side, one on deck
        water_obj.hide_render = False
        fx = B / 2 + 1.6
        temp.append(box("_float", stage, float_mat, fx - 1.0, fx + 1.0, -4.0, 4.0, -0.30, 0.40, None))
        temp.append(figure("_figure_float", stage, fx, 0.5, 0.40, mat=fig_mat))
        dy = {"tug": -10.0, "pilot_boat": -5.5, "tug_conventional": -8.8, "tug_escort": -10.0,
              "tug_tractor": -10.6, "pilot_boat_b": -5.5, "tug_conventional_b": 3.0}[v]
        dx = {"tug": 3.2, "pilot_boat": 1.5, "tug_conventional": 2.0, "tug_escort": 3.2,
              "tug_tractor": 3.2, "pilot_boat_b": 1.5, "tug_conventional_b": 2.0}[v]
        temp.append(figure("_figure_deck", stage, dx, dy, hull.deck_z(dy) + 0.10, mat=fig_mat))
        shoot(f"{v}_with_figure", (fx + 0.45 * L, -0.55 * L, 0.18 * L + 2.0), (0.0, -0.15 * L, 1.5), lens=35)
        clear()
    # the three side by side, on the water
    water_obj.hide_render = False
    # side by side, bows toward the camera; in the image, left to right:
    # tug_tractor, tug_escort, tug, tug_conventional, tug_conventional_b,
    # pilot_boat, pilot_boat_b
    shifts = {"pilot_boat_b": -53.0, "pilot_boat": -45.0, "tug_conventional_b": -33.0,
              "tug_conventional": -21.0, "tug": -6.0, "tug_escort": 9.0, "tug_tractor": 24.0}
    for v in VARIANTS:
        for o in variant_objects(v):
            o.hide_render = False
            o.location.x += shifts[v]
    temp.append(figure("_figure_lineup", stage, -45.0, 10.5, 0.0, mat=fig_mat))
    shoot("lineup", (-14.0 + 55.0, 105.0, 38.0), (-14.0, 0.0, 3.0), lens=35, size=(2000, 1000))
    for v in VARIANTS:
        for o in variant_objects(v):
            o.location.x -= shifts[v]
    clear()
    show_variant("tug")


# --- main ----------------------------------------------------------------------

def layer_collection(name, root=None):
    root = root or bpy.context.view_layer.layer_collection
    if root.name == name:
        return root
    for child in root.children:
        found = layer_collection(name, child)
        if found is not None:
            return found
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != PROP:
        raise SystemExit(f"{PROP}: open {PROP}.blend, not {name}")
    export, reference = (bpy.data.collections[n] for n in ("export", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"{PROP}: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    fit = fitting_meshes(mats())
    hulls = {"tug": build_tug(export, mats(), fit)}
    pilot = bpy.data.collections.new("variant_pilot_boat")
    export.children.link(pilot)
    hulls["pilot_boat"] = build_pilot(pilot, mats("pilot_"), fit)
    conv = bpy.data.collections.new("variant_tug_conventional")
    export.children.link(conv)
    hulls["tug_conventional"] = build_conventional(conv, mats("conventional_"), fit)
    bpy.context.view_layer.update()
    # the four variants (2026-10-03), each from its source's meshes
    made = {}
    for v in VARIANTS[3:]:
        made[v] = bpy.data.collections.new(f"variant_{v}")
        export.children.link(made[v])
    build_escort(made["tug_escort"], mats(), fit, hulls["tug"])
    build_tractor(made["tug_tractor"], mats(), fit, hulls["tug"])
    build_pilot_b(made["pilot_boat_b"], fit)
    build_conventional_b(made["tug_conventional_b"], mats("conventional_"), fit, hulls["tug_conventional"])
    for v, src in (("tug_escort", "tug"), ("tug_tractor", "tug"), ("pilot_boat_b", "pilot_boat"),
                   ("tug_conventional_b", "tug_conventional")):
        hulls[v] = hulls[src]
    bpy.context.view_layer.update()
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    for v in VARIANTS:
        lo, hi = report(v)
        suffix = "" if v == "tug" else f"_{v}"
        waterline_marker(f"waterline{suffix}", hulls[v].waterline, reference)
        outline(f"outline_{v}_{hi.y - lo.y:.1f}x{hi.x - lo.x:.1f}".replace(".", "p"), reference,
                lo.x, hi.x, lo.y, hi.y)
    figure("figure_1p7m", reference, 3.2, -10.0, hulls["tug"].deck_z(-10.0) + 0.10)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], hulls)


main()
