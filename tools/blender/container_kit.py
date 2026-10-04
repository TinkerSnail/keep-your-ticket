"""The container port's yard kit, blocked out (2026-10-03): Christina's "lets
add a modern port near the city", the yard of the new container terminal on
the mainland shore facing the city across the water, by the bridge's east
end. A yard holds thousands of boxes, so this kit is about sharing and
merging: a single box is a prop for the few seen close, and the yard itself
is built from merged stack blocks, never one object per box.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/container_kit.blend --python tools/blender/container_kit.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, twenty-one `kyt_variant`s, all at the
origin, so Send writes each as a prop of its own (`container_kit_<variant>`):

- **box_40** (in `export` itself): a 40 ft ISO dry box at the ISO outside
  size: a body whose long sides and front end are panels recessed behind the
  corner posts and rails, the door end recessed behind its frame with the
  doors' seam, four locking bars and two chunky hinges per leaf standing on
  it (the whole door end 5.5 cm inside the castings, so the door gear stays
  inside the ISO envelope), and a corner casting at each of the eight
  corners. The corrugation is flat here and left to the paint and normal
  map (a few broad ribs did not fit the 300-triangle budget alongside the
  castings).
- **box_20**, **box_40_hc** (high-cube): the same parts at their sizes.
- **box_40_reefer**: a high-cube reefer, its long sides flat and flush as a
  reefer's skinned walls are, its front end a machinery bay: the
  evaporator panel standing in the bay's upper half, a fan guard and a
  control box in the lower.
- **stack_block_40** and **stack_block_20**: a yard row of boxes, six long
  end to end and four high, as ONE mesh: each slot's stack a single closed
  column with a dark V seam cut round it between tiers (where the corner
  castings hold stacked boxes apart), each box's long sides recessed between
  its posts and rails as the single box's are, the row's two end faces
  recessed as door ends and front ends. Mixed colours by material slot. The
  20 ft row stands its boxes in pairs, 76 mm apart, in 40 ft slots, so it
  fills exactly three of the 40 ft row's slots and the two swap in the yard.
- **straddle_carrier**: a late-1990s 1-over-3 straddle carrier: two side
  frames on four 16.00R25 wheels each, tapered legs, a top frame with a
  20 ft spreader hung raised, the engine house on top at the back, an
  electrical cabinet front right, the cab high at the front left, a ladder.
  It straddles the stack block's 4-high row and passes under the gantry
  crane's 15 m portal (the margins are printed every run).
- **yard_tractor_chassis**: a terminal tractor with its offset one-seat cab
  and engine housing beside it, hitched by its fifth wheel to a 40 ft
  straight-frame container chassis; **yard_tractor_loaded**: the same, linked
  part for part, with a box_40 (linked) on the chassis's twist-locks.

The further variants (3 Oct 2026, Christina: "build all the offered
variants"), built after the nine above and touching none of them:

- **box_40_ribbed**, the close-up box: box_40's parts linked, with broad ribs
  standing in its side and front panels (one mesh per panel kind, linked
  rib to rib, the -X side's turned, never mirrored), about 600 triangles.
- **box_45**: a 45 ft high-cube with the extra bottom fittings at the 40 ft
  positions (two bars across its base); its front end is left flat to keep
  it under 300 triangles.
- **stack_block_40_hc** (high-cubes, 4 high), **stack_block_40_3h** and
  **stack_block_20_3h** (3 high, a 1-over-2 carrier's rows),
  **stack_block_40_double** (two rows 0.3 m apart, their facing sides flat),
  **stack_block_40_mix_b** (another colour mix) and
  **stack_block_40_consignment** (the container ship's weighted mix, clumped
  as consignments are).
- **gooseneck_chassis**: a 40 ft gooseneck chassis parked on its landing
  gear, its neck riding up into a box's tunnel, its twist-locks and running
  gear linked from the rig's chassis; **gooseneck_chassis_loaded**: with a
  box_40_hc (linked) on it, its top at the 13 ft 6 in road height.
- **straddle_carrier_1over2**: the 1-over-3's wheels and bottom beams linked,
  everything above its legs linked 1.70 m lower, its own shorter legs and
  ladder: 12.70 m.
- **straddle_carrier_low_cab**: the 1-over-3 linked part for part but the
  cab, which hangs low outboard of the left front leg, its floor just over a
  neighbouring 4-high row; the ladder stops in its floor.

Parts that are identical are one mesh linked into every object that shows
them: the corner casting (in every box, eight times), the hinge, the door
bars and seam strip of each box height, the box_40's parts on the loaded
chassis, and the wheels (one mesh for every 11R22.5 dual on the tractor and
the chassis). Everything the tool makes carries `kyt_container_kit`, so a
rerun removes and rebuilds its own work and keeps anything of hers; `export`
holding anything untagged refuses without `--replace`. Into the locked
`reference` collection go each variant's footprint outline, a 1.7 m figure
and the crane portal's 15 m clear-height line over the carrier.

`--render <folder>` runs after any save and saves nothing: a quay at z = 0
with water beyond its +Y edge, sun, camera and a figure beside each variant;
per variant a three-quarter (boxes and rows from their door end, vehicles
from the front), a side elevation and a plan, each box's door end and front
end close, the carrier straddling the 40 ft row under a stand-in portal beam
at 15 m, and the kit side by side.

**Frame** (shore equipment, the boats brief): real metres, Z up, z = 0 the
ground or quay top the prop stands on, the origin at the footprint's centre.
A box's length runs along Y, its front end (the reefer's machinery) to +Y
and its doors to -Y, the way it rides a chassis behind a tractor and the way
the ship stows it fore and aft; a vehicle drives toward +Y (the glTF export
turns Blender +Y into Godot -Z, Godot's forward, as `ride_vehicle.gd` turns
its trains). The yard plan turns the props as its rows need; nothing here
has a waterside.

**Contract** (scenery block-out): closed shells, silhouette first, no
interiors; windows are dark slabs set proud, not holes. Every part has
`kyt_collision = none` this pass (collision is decided when the yard is
placed). No two shapes share a plane: a part that meets another laps 2 cm
into it or stands proud of it. Era late 1990s, no logos or lettering;
colour is stand-in materials by surface, `container_kit_<surface>`, the box
colours `container_kit_box_<colour>`, the set the container ship uses.
"""

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_container_kit"
PROP = "container_kit"

# --- ISO boxes (the boats brief's shared port numbers; ISO 668) -------------
BOX_W = 2.438              # every ISO box, outside
BOX_H = 2.591              # 8 ft 6 in
BOX_HC_H = 2.896           # high-cube, 9 ft 6 in; the reefer too
L40 = 12.192               # 40 ft
L20 = 6.058                # 20 ft (two and a 76 mm gap make a 40)
ISO_PAIR_GAP = L40 - 2 * L20   # 0.076, ISO 668's gap between two 20s in a 40 ft slot
CAST_X, CAST_Y, CAST_Z = 0.162, 0.178, 0.118   # ISO 1161 corner fitting, across x along x high
BODY_IN = 0.010            # chosen: sides and ends 1 cm inside the castings' outer faces
BODY_Z0 = 0.0125           # ISO 668: the base stands 12.5 mm clear above the bottom castings
TOP_PROUD = 0.006          # ISO 668: the top castings stand 6 mm proud of the roof
# the long side's frame round its recessed panel
SIDE_POST = 0.18           # chosen: the corner post seen from the side, a casting's length
TOP_RAIL = 0.11            # chosen: the top side rail
BOTTOM_RAIL = 0.16         # chosen: the bottom side rail (a ~158 mm channel on most dry boxes)
SIDE_RECESS = 0.035        # chosen: the corrugated panel's mean plane (corrugation ~36 mm deep)
# the front end (the blind end, +Y)
FRONT_POST = 0.15          # chosen
FRONT_SILL_Z = 0.17        # chosen: the front panel's foot over the box's bottom
FRONT_HEADER = 0.12        # chosen: the front header under the roof
FRONT_RECESS = 0.035       # chosen, as the side
# the door end (-Y)
DOOR_OPEN_W = 2.340        # ISO 668 door opening width (read)
DOOR_OPEN_H = 2.280        # ISO 668 door opening height, 8 ft 6 in box (read)
DOOR_OPEN_H_HC = 2.585     # ISO 668 door opening height, high-cube (read)
DOOR_SILL = 0.16           # chosen: the opening's sill over the box's bottom (floor and cross-members)
DOOR_END_IN = 0.055        # chosen: the rear frame's face this far inside the castings', so the
                           # door gear stays inside the envelope the castings define (ISO 668:
                           # nothing may project past the corner fittings)
DOOR_RECESS = 0.030        # chosen: the doors' face behind the rear frame
BAR_X = (-0.88, -0.29, 0.29, 0.88)   # chosen: two locking bars per leaf, at a quarter and three quarters
BAR_T = 0.05               # chosen: chunky (real bars are 33-48 mm pipe)
BAR_PROUD = 0.05           # the bars' face proud of the doors
BAR_OVERRUN = 0.07         # the bars run this far past the opening into the cam keepers
SEAM_W = 0.06              # chosen: the right leaf's overlapping edge down the middle
HINGE_X0, HINGE_X1 = 1.06, 1.20     # chosen: across the leaf's outer edge and the corner post
HINGE_H = 0.16             # chosen: chunky, two per leaf ("a few chunky parts"; real boxes have four)
HINGE_PROUD = 0.04         # proud of the rear frame
HINGE_Z = (0.55, 1.95)     # chosen: the 8 ft 6 in box's two hinges per leaf
HINGE_Z_HC = (0.55, 2.25)  # chosen: the high-cube's
# the reefer's machinery bay (front end)
REEFER_POST = 0.12         # chosen
REEFER_HEADER = 0.10       # chosen
REEFER_RECESS = 0.12       # chosen: the bay's depth behind the front frame
REEFER_PANEL_Z = 1.50      # chosen: the evaporator panel's foot; the condenser and compressor below
REEFER_PANEL_OUT = 0.08    # the panel's face out of the bay's back (4 cm behind the frame)
REEFER_FAN = (-0.45, 0.85, 0.36)    # chosen: the condenser fan guard's centre x, z and radius
REEFER_FAN_OUT = 0.06
REEFER_CONTROL = (0.35, 0.95, 0.45, 1.25)  # chosen: the control box, x0 x1 z0 z1
REEFER_CONTROL_OUT = 0.10

# --- the yard rows (stack blocks) ---------------------------------------------
ROW_SLOTS = 6              # the brief: six long
ROW_TIERS = 4              # the brief: four high, a 1-over-3 straddle carrier's stack
SLOT_GAP = 0.40            # chosen: the gap between 40 ft slots in a row (yards use 0.3-0.6 m)
SEAM_H = 0.06              # chosen: the V seam between tiers, exaggerated from the castings' ~19 mm
SEAM_D = 0.04              # chosen: its depth
ROW_SEED_40, ROW_SEED_20 = 1997, 1998   # the colour mixes, fixed so a rerun repeats them

# --- colours (the set the container ship agent uses; hex chosen) ------------
BOX_COLOURS = {
    "rust_red": "9e3b26",
    "sky_blue": "5ea3d0",
    "dark_blue": "1f3a6b",
    "green": "2f6e3e",
    "grey": "8a8d8f",
    "white": "e6e4dc",
    "orange": "d9682a",
    "yellow": "e3b52a",
    "brown": "6b4a2e",
}
COLOUR_NAMES = tuple(BOX_COLOURS)

# --- the straddle carrier -------------------------------------------------------
# Liebherr SC 1-over-3 (read): 10.0 m long, 4.94 m wide, 15.6 m high, 12.0 m
# under the spreader (for high-cubes, a modern machine); Kalmar: 3.5 m inside
# clear width, 16.00R25 tyres; Liebherr: wheel base 2000 / 3700 / 2000 mm,
# cab 2.1 x 1.5 x 2.0 m front left. A late-1990s 1-over-3 for 8 ft 6 in boxes
# is lower: chosen to straddle the 4-high row and pass under a 15 m portal.
SC_HALF = 4.90             # chosen: the frame 9.8 m long; with the cab 9.98 (Liebherr 10.0)
SC_IN = 3.50 / 2           # Kalmar inside clear width 3,500 mm (read)
SC_OUT = 2.40              # chosen: each side frame 0.65 m wide, 4.80 m overall at the frames
SC_TYRE_D, SC_TYRE_W = 1.49, 0.43   # 16.00R25 (read)
SC_AXLES = (-3.85, -1.85, 1.85, 3.85)   # Liebherr wheel base 2000 / 3700 / 2000 mm (read)
SC_SILL_Z = (1.62, 2.40)   # chosen: the bottom beams over the wheel housings
SC_UNDER_SPREADER = 10.80  # chosen: over 4 x 2.591 = 10.364 m, the 4-high row, with 0.44 m
SC_SPREADER_T = 0.42       # chosen
SC_SPREADER_L = 6.06       # chosen: telescoped to 20 ft, its travelling length
SC_TOP_Z = (11.45, 12.25)  # chosen: the top side beams
SC_HEIGHT = 14.40          # chosen: the exhaust's top; between a 1-over-2's 12.7 and a modern 1-over-3's 15.6
SC_CAB = (-2.43, -0.93, 2.98, 5.08, 12.05, 14.05)   # x0 x1 y0 y1 z0 z1: 1.5 x 2.1 x 2.0 m (Liebherr, read)
SC_CAB_WINDOW_Z = (12.75, 13.85)   # chosen: the side windows; the front one starts lower,
SC_CAB_FRONT_SILL = 12.60          # chosen  so the driver sees down to the spreader
SC_WHEEL_HOUSING = (1.82, 2.33, 0.55, 1.25)   # chosen: x from the middle, half length, foot
SC_BEAM_CHAMFER = (4.55, 1.95)     # chosen: where the bottom beam's lower ends start to chamfer, y and z
SC_LEG_X = (1.78, 2.37)            # chosen: the legs, x from the middle
SC_LEG_FOOT_Y = (4.00, 4.80)       # chosen: a leg's foot, y from the middle
SC_LEG_HEAD_Y = (3.70, 4.80)       # chosen: its head, wider: the legs taper in as they rise
SC_GIRDER_X = 2.38                 # chosen: the cross girders' half length, inside the side beams
SC_GIRDERS = {                     # chosen: y0 y1 of the end portals and the two hoist beams
    "girder_front": (4.02, 4.78), "girder_rear": (-4.78, -4.02),
    "hoist_beam_front": (2.35, 2.85), "hoist_beam_rear": (-2.85, -2.35)}
SC_SPREADER_HALF_W = 1.15          # chosen
SC_ROPES = (0.90, 2.60, 0.07)      # chosen: the four falls at x, y from the middle, and their half size
SC_ENGINE_HOUSE = (-2.30, 1.20, -4.80, -2.20, 13.75)   # chosen: x0 x1 y0 y1 and top
SC_ENGINE_ROOF_T = 0.10            # chosen
SC_LOUVRES = (-1.90, 0.80, 12.50, 13.50)   # chosen: the louvres on its back face, x0 x1 z0 z1
SC_EXHAUST = (0.85, -2.70, 0.12)   # chosen: x, y and radius; its top is SC_HEIGHT
SC_CABINET = (0.70, 2.35, 2.70, 4.74, 13.05)   # chosen: the electrical cabinet, x0 x1 y0 y1 top
SC_BEACON = (-1.68, 4.00, 0.09, 0.18)          # chosen: x, y, radius, height
SC_LADDER = (-2.52, -2.35, 4.05, 4.65, 2.30)   # chosen: up the left front leg, x0 x1 y0 y1 foot
SC_HUB_R = 0.40                    # chosen: the wheel disc, 2 cm proud of the tyre
CRANE_PORTAL_CLEAR = 15.0  # the boats brief: the gantry crane's clear height under the portal

# --- the yard tractor and chassis (tractor-local y: the rear axle at 0) --------
YT_WHEELBASE = 2.79        # Ottawa YT30 terminal tractor, 110 in (read)
YT_FRONT = YT_WHEELBASE + 1.15   # chosen front overhang; 5.19 m overall
YT_REAR = -1.25            # chosen rear overhang
YT_HALF_W = 1.275          # chosen: 2.55 m over the rear duals
YT_CAB = (-1.25, 0.07, 1.85, 3.65, 1.20, 3.25)   # x0 x1 y0 y1 z0 z1: 1.32 wide, 1.80 deep (Autocar 52 x 71 in, read)
YT_CAB_WINDOW_Z = (2.05, 3.05)   # chosen: the cab's glass, all round
YT_CAB_MOUNT = (-0.70, -0.20, 2.00, 3.40)   # chosen: x0 x1 y0 y1 under the cab
TYRE_D, TYRE_W = 1.054, 0.28     # 11R22.5 (read)
DUAL_W = 0.62              # chosen: a dual pair and its gap as one wheel
YT_HUB_R = 0.29            # chosen: the wheel disc, 2 cm proud of the tyre
YT_FRONT_TRACK = 2.00      # chosen
YT_FRAME_X = (0.35, 0.55)  # chosen: the frame rails, x from the middle
YT_FRAME_Z = (0.55, 0.80)  # chosen
YT_HOOD = (0.10, 1.20, 1.85, 3.80, 1.12, 2.00)   # chosen: the engine housing beside the cab, x0 x1 y0 y1 z0 z1
YT_HOOD_NOSE = (3.40, 1.60)      # chosen: its sloped nose runs from y 3.40 at the top to z 1.60 at the front
YT_GRILLE = (0.22, 1.08, 1.20, 1.52)   # chosen: x0 x1 z0 z1 on the housing's front
YT_ENGINE = (0.15, 0.80, 2.00, 3.50, 0.70)  # chosen: the engine under the housing, x0 x1 y0 y1 foot
YT_EXHAUST = (1.05, 1.95, 0.08, 1.50, 3.40)  # chosen: x, y, radius, foot (inside the housing), top
YT_BEACON = (-0.60, 2.40, 0.09, 0.17)        # chosen: x, y, radius, height
YT_BUMPER_FRONT = (1.20, 3.74, 0.42, 0.78)   # chosen: half width, back face, z0 z1
YT_BUMPER_REAR = (0.80, 0.45, 0.82)          # chosen: half width, z0 z1
YT_FENDER = (0.66, 1.28, 0.62, 1.04, 1.10)   # chosen: the rear fenders, x0 x1, half length, z0 z1
YT_FENDER_BRACKET = (0.53, 0.70, 0.75)       # chosen: x0 x1 and foot, the rail to the fender
YT_DECK = (-0.90, 0.60, 0.75, 1.80, 0.78, 0.84)   # chosen: the deck plate behind the cab
YT_FUEL_TANK = (-1.15, -0.53, 0.74, 1.75, 0.45, 0.93)   # chosen
YT_STEP_X = -0.80          # chosen: the cab's entry step, from the cab's side in to here
YT_APRON_X = 1.19          # chosen: the front apron, from the cab's side across to here
KINGPIN_Y = 0.25           # chosen: the fifth wheel's centre 0.25 m ahead of the rear axle
FIFTH_TOP = 0.93           # Terberg's lowest fifth wheel 935 mm (read)
FIFTH_PLATE = (0.60, 0.45, 0.10)   # chosen: half width, half length, thickness
FIFTH_MOUNT = (0.40, 0.30)         # chosen: half width, half length
KINGPIN_SETBACK = 0.91     # the chassis front to its kingpin, 36 in (read)
CH_FRONT = KINGPIN_Y + KINGPIN_SETBACK
CH_LEN = 12.40             # chosen: the box, a centimetre at the front and 0.2 m of bumper behind
CH_REAR = CH_FRONT - CH_LEN
CH_HALF_W = 1.22           # chosen: the bolsters a box's width
DECK_Z = 1.30              # chosen: the box's bottom on the twist-locks (straight frame; a gooseneck is 1.22)
CH_RAIL_X = (0.43, 0.57)   # chosen: the two main rails, x from the middle
CH_RAIL_Z = (0.95, 1.22)   # chosen
CH_BOLSTER = (0.30, 1.00)  # chosen: the front and rear bolsters' depth along y and their foot
CH_CROSS_MEMBERS = (-2.50, -5.50, -8.00)   # chosen: y, tractor-local
CH_CROSS = (0.80, 0.08, 0.98, 1.18)        # chosen: half width, half depth, z0 z1
CH_TWISTLOCK_X = (1.075, 1.195)            # chosen: inside a casting's footprint
CH_AXLES = (CH_REAR + 1.10, CH_REAR + 2.35)   # chosen: a tandem 1.25 m apart (typical 49-50 in)
CH_AXLE = (0.62, 0.06, 0.45, 0.57)         # chosen: half width, half depth, z0 z1
CH_HANGER = (0.44, 0.56, 0.10, 0.52)       # chosen: x0 x1, half depth, foot
LANDING_Y = KINGPIN_Y - 2.10                 # chosen
CH_LANDING_LEG = (0.55, 0.67, 0.06, 0.30)  # chosen: x0 x1, half depth, foot (wound up clear of the ground)
CH_SAND_SHOE = (0.47, 0.75, 0.15, 0.25, 0.31)   # chosen: x0 x1, half depth, z0 z1
CH_CROSSBAR = (0.60, 0.03, 0.55, 0.61)     # chosen: the landing gear's crank shaft
CH_COUPLER = (0.62, 0.70)  # chosen: the coupler plate's half width, and how far behind the kingpin it starts
CH_BUMPER = (1.10, 0.12, 0.42, 0.56)       # chosen: the rear underride bar, half width, depth, z0 z1
CH_BUMPER_STRUT = (0.44, 0.56, 0.07, 0.15, 0.54)   # chosen: x0 x1, y from the rear, foot
CH_MUDFLAP = (0.65, 1.20, 0.36, 0.39, 0.20)        # chosen: x0 x1, y from the rear, foot
YT_SHIFT = -(YT_FRONT + CH_REAR) / 2         # centres the rig's footprint on the origin
BOX_ON_CHASSIS_Y = CH_FRONT - 0.01 - L40 / 2 # the box's centre, tractor-local

# --- further variants (3 Oct 2026, Christina: "build all the offered variants") ---
# the close-up box: real corrugation as broad ribs standing in the side and
# front panels (linked, one mesh per panel kind), on box_40's own parts
RIB_SIDE_COUNT = 13        # chosen: about 0.9 m apart, three times a real box's ~0.28 m, chunky
RIB_FRONT_COUNT = 3        # chosen
RIB_OUTER = 0.40           # chosen: a rib's outer face, as a share of the side's rib pitch
RIB_BASE = 0.62            # chosen: its base, as a share of the pitch
RIB_SHY = 0.004            # chosen: its face this far behind the posts' and rails' face
# the 45 ft box
L45 = 13.716               # ISO 668 45 ft (read); built high-cube, as 45s are
FITTING_40_Y = L40 / 2 - CAST_Y / 2   # read: a 45 has bottom fittings at the 40 ft positions too, to stack on 40s
# the rows
ROW_TIERS_LOW = 3          # a 1-over-2 carrier's rows, three high
DOUBLE_GAP = 0.30          # chosen: two rows side by side in one block (an RTG or reach-stacker block, not a straddle row)
ROW_SEED_HC, ROW_SEED_MIX_B, ROW_SEED_CONSIGN, ROW_SEED_DOUBLE = 1999, 2001, 2002, 2003   # chosen
CONSIGN_WEIGHTS = (17, 9, 12, 9, 13, 9, 7, 5, 19)   # read: the container ship's colour weights, COLOUR_NAMES' order
SAME_AS_BELOW, SAME_AS_BESIDE = 0.18, 0.22          # read: the ship's consignment clumping
# the gooseneck chassis, parked on its landing gear (chassis-local, front +Y)
GN_HALF = CH_LEN / 2       # chosen: 12.40 m, as the straight chassis
GN_DECK_Z = 1.22           # chosen: a 9 ft 6 in box's top at 4.116 m, the US 13 ft 6 in road height, which is why goosenecks exist
GN_RAIL_Z = (0.87, 1.14)   # chosen
GN_NECK = (3.15, 0.50, 0.12)   # ISO 1496-1's gooseneck tunnel, about 3.15 m long, 1.03 m wide and 120 mm deep
                               # (recalled, not fetched): the neck's length, half width and rise over the deck
GN_NECK_RAMP = 0.40        # chosen: the neck's step down to the main rails
GN_NECK_Z0 = 0.95          # chosen: the neck's underside, on the coupler plate
GN_BOLSTER_Z0 = 0.92       # chosen
GN_LANDING_Y = GN_HALF - 3.35   # chosen: the landing gear just behind the neck
GN_CROSS_Z = (0.90, 1.10)  # chosen
GN_SAND_SHOE_Z = (0.0, 0.06)    # parked: the shoes on the ground
# the 1-over-2 straddle carrier: the 1-over-3 with everything above the
# bottom beams lowered, so its legs are shorter
SC2_UNDER_SPREADER = 9.10  # chosen: Liebherr's 1-over-2 is 9.2 m under the spreader and 12.7 m overall (read)
SC2_DROP = SC_UNDER_SPREADER - SC2_UNDER_SPREADER
SC2_HEIGHT = SC_HEIGHT - SC2_DROP
# the low cab: Kalmar offers a side cabin beside its front-left one (read);
# hung outboard of the left front leg, under the top beam, its floor just
# over a neighbouring 4-high row
SIDE_CAB = (-3.84, -2.34, 3.20, 5.30, 10.50, 12.50)   # chosen: x0 x1 y0 y1 z0 z1, the Liebherr cab's size
SIDE_CAB_WINDOW_Z = (11.20, 12.30)   # chosen
SIDE_CAB_FRONT_SILL = 10.90          # chosen: the front glass lower, to see down past the leg
SIDE_CAB_BEACON = (-3.10, 4.25)      # chosen
LANE_CLEAR = 0.30                    # chosen: a carrier's frame to the next row, in the clearance render

VARIANTS = ("box_40", "box_20", "box_40_hc", "box_40_reefer", "stack_block_40", "stack_block_20",
            "straddle_carrier", "yard_tractor_chassis", "yard_tractor_loaded",
            "box_40_ribbed", "box_45", "stack_block_40_hc", "stack_block_40_3h", "stack_block_20_3h",
            "stack_block_40_double", "stack_block_40_mix_b", "stack_block_40_consignment",
            "gooseneck_chassis", "gooseneck_chassis_loaded", "straddle_carrier_1over2", "straddle_carrier_low_cab")
VEHICLES = ("straddle_carrier", "yard_tractor_chassis", "yard_tractor_loaded", "gooseneck_chassis",
            "gooseneck_chassis_loaded", "straddle_carrier_1over2", "straddle_carrier_low_cab")


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {f"{PROP}_box_{k}": srgb(v) for k, v in BOX_COLOURS.items()}
COLOURS.update({
    f"{PROP}_seam": srgb("1c1c1e"),          # the stack blocks' V seams
    f"{PROP}_fittings": srgb("3a3a3c"),      # castings, door bars, hinges, the doors' seam strip
    f"{PROP}_reefer_unit": srgb("c4c8cb"),   # the reefer's evaporator panel and control box
    f"{PROP}_reefer_bay": srgb("3e4246"),    # the back of its machinery bay (condenser, compressor)
    f"{PROP}_carrier_paint": srgb("e8b81e"), # the straddle carrier's structure
    f"{PROP}_carrier_housing": srgb("d8d6cf"),   # its engine house, cabinet and cab
    f"{PROP}_spreader": srgb("d9682a"),
    f"{PROP}_tractor_paint": srgb("c8372d"), # the yard tractor's cab and hood
    f"{PROP}_chassis": srgb("2b2b2d"),       # frames, chassis, axles
    f"{PROP}_steel": srgb("6d7073"),         # ladder, ropes, fifth wheel, fuel tank, bumpers
    f"{PROP}_glass": srgb("23313a"),         # windows, dark slabs set proud
    f"{PROP}_grille": srgb("151515"),
    f"{PROP}_tyre": srgb("1a1a1a"),
    f"{PROP}_hub": srgb("9a9da0"),
    f"{PROP}_beacon": srgb("f29a1e"),
})


def material(name, colour=None):
    """A stand-in material by name; a rerun resets the builder's colours."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour or COLOURS[name]
        bsdf.inputs["Roughness"].default_value = 0.85
    elif name in COLOURS and mat.node_tree is not None:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = COLOURS[name]
    return mat


def M(surface):
    return material(f"{PROP}_{surface}")


def box_mat(colour):
    return material(f"{PROP}_box_{colour}")


# --- building blocks -------------------------------------------------------------

def tag(obj, variant, unwrap="facets"):
    obj[TAG] = True
    obj["kyt_unwrap"] = unwrap
    obj["kyt_collision"] = "none"
    if variant:
        obj["kyt_variant"] = variant
    return obj


def make_mesh(name, bm, mats, flat=True):
    """A bmesh into a mesh datablock with its material slots."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if flat:
        for f in bm.faces:
            f.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    for m in mats:
        mesh.materials.append(m)
    return mesh


def place(name, mesh, coll, variant, loc=(0.0, 0.0, 0.0), unwrap="facets"):
    """An object showing `mesh` (shared or not) at `loc`."""
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    coll.objects.link(obj)
    return tag(obj, variant, unwrap)


def finish(name, bm, coll, mats, variant, unwrap="facets"):
    return place(name, make_mesh(name, bm, mats), coll, variant, unwrap=unwrap)


def prism_bm(poly, axis, lo, hi, bm=None):
    """A 2D polygon extruded along `axis` ('x' gives (y, z) pairs, 'y' gives
    (x, z), 'z' gives (x, y))."""
    bm = bm or bmesh.new()

    def at(a, b, t):
        return {"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis]

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return bm


def box_bm(x0, x1, y0, y1, z0, z1, bm=None):
    assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
    return prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1, bm)


def box(name, coll, mat, x0, x1, y0, y1, z0, z1, variant):
    """An axis-aligned box, 12 triangles."""
    return finish(name, box_bm(x0, x1, y0, y1, z0, z1), coll, [mat], variant)


def ring(cx, cy, r, sides, flat_bottom=True):
    """A regular polygon about (cx, cy), a flat edge at the bottom (lowest b)."""
    off = -math.pi / 2 + (math.pi / sides if flat_bottom else 0.0)
    return [(cx + r * math.cos(off + math.tau * i / sides), cy + r * math.sin(off + math.tau * i / sides))
            for i in range(sides)]


def cylinder_bm(axis, radius, half, sides, flat_bottom=True):
    """A cylinder about the origin, its axis along `axis`."""
    return prism_bm(ring(0.0, 0.0, radius, sides, flat_bottom), axis, -half, half)


def tapered_bm(bottom, top):
    """A solid between two axis-aligned rectangles (x0, x1, y0, y1, z) one
    over the other."""
    bm = bmesh.new()
    lo = [bm.verts.new(v) for v in ((bottom[0], bottom[2], bottom[4]), (bottom[1], bottom[2], bottom[4]),
                                    (bottom[1], bottom[3], bottom[4]), (bottom[0], bottom[3], bottom[4]))]
    hi = [bm.verts.new(v) for v in ((top[0], top[2], top[4]), (top[1], top[2], top[4]),
                                    (top[1], top[3], top[4]), (top[0], top[3], top[4]))]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


class Verts:
    """Shared vertices by position, so faces built separately close up."""

    def __init__(self, bm):
        self.bm, self.cache = bm, {}

    def __call__(self, p):
        key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
        v = self.cache.get(key)
        if v is None:
            v = self.cache[key] = self.bm.verts.new(key)
        return v


def face(bm, verts, mat_index):
    f = bm.faces.new(verts)
    f.material_index = mat_index
    return f


def panel(bm, vert, o, inward, spec, mat_frame, mat_back=None):
    """A rectangle o0 o1 o2 o3 (o0 to o1 is its 'a' edge, o0 to o3 its 'b'),
    whole or with a recess cut in it: `spec` is (a_lo, a_hi, b_lo, b_hi,
    depth), the frame's widths at each edge and the panel's depth along
    `inward`. The frame is four trapezoids, the recess four walls and its
    back: 18 triangles where the whole face is 2."""
    vs = [vert(p) for p in o]
    if spec is None:
        face(bm, vs, mat_frame)
        return
    a_lo, a_hi, b_lo, b_hi, depth = spec
    ea, eb = o[1] - o[0], o[3] - o[0]
    la, lb = ea.length, eb.length
    ua, ub = ea / la, eb / lb
    assert a_lo + a_hi < la and b_lo + b_hi < lb, (spec, la, lb)
    inner = [o[0] + ua * a_lo + ub * b_lo, o[0] + ua * (la - a_hi) + ub * b_lo,
             o[0] + ua * (la - a_hi) + ub * (lb - b_hi), o[0] + ua * a_lo + ub * (lb - b_hi)]
    vi = [vert(p) for p in inner]
    vb = [vert(p + inward * depth) for p in inner]
    for k in range(4):
        j = (k + 1) % 4
        face(bm, (vs[k], vs[j], vi[j], vi[k]), mat_frame)
        face(bm, (vi[k], vi[j], vb[j], vb[k]), mat_frame)
    face(bm, vb, mat_frame if mat_back is None else mat_back)


def recessed_box_bm(x0, x1, y0, y1, z0, z1, specs, back_mats=None):
    """A closed box with recessed panels on the faces named in `specs`
    ('-x', '+x', '-y', '+y', '-z', '+z'). On the x faces 'a' runs along +y
    and 'b' up; on the y faces 'a' runs along +x and 'b' up."""
    back_mats = back_mats or {}
    bm = bmesh.new()
    vert = Verts(bm)
    C = Vector
    faces = {
        "-x": ([C((x0, y0, z0)), C((x0, y1, z0)), C((x0, y1, z1)), C((x0, y0, z1))], C((1, 0, 0))),
        "+x": ([C((x1, y0, z0)), C((x1, y1, z0)), C((x1, y1, z1)), C((x1, y0, z1))], C((-1, 0, 0))),
        "-y": ([C((x0, y0, z0)), C((x1, y0, z0)), C((x1, y0, z1)), C((x0, y0, z1))], C((0, 1, 0))),
        "+y": ([C((x0, y1, z0)), C((x1, y1, z0)), C((x1, y1, z1)), C((x0, y1, z1))], C((0, -1, 0))),
        "-z": ([C((x0, y0, z0)), C((x1, y0, z0)), C((x1, y1, z0)), C((x0, y1, z0))], C((0, 0, 1))),
        "+z": ([C((x0, y0, z1)), C((x1, y0, z1)), C((x1, y1, z1)), C((x0, y1, z1))], C((0, 0, -1))),
    }
    for key, (o, inward) in faces.items():
        panel(bm, vert, o, inward, specs.get(key), 0, back_mats.get(key))
    return bm


# --- the single boxes ------------------------------------------------------------

def door_spec(h, door_h, w=BOX_W - 2 * BODY_IN, z0=BODY_Z0, z1=None):
    """The door end's recess: the ISO opening, its sill at DOOR_SILL over the
    box's bottom. `z0`/`z1` are the face's own bottom and top."""
    z1 = h - TOP_PROUD if z1 is None else z1
    post = (w - DOOR_OPEN_W) / 2
    return (post, post, DOOR_SILL - z0, z1 - (DOOR_SILL + door_h), DOOR_RECESS)


def front_spec(h, w=BOX_W - 2 * BODY_IN, z0=BODY_Z0, z1=None, extra=0.0):
    z1 = h - TOP_PROUD if z1 is None else z1
    post = FRONT_POST + extra
    return (post, post, FRONT_SILL_Z - z0, z1 - (h - TOP_PROUD - FRONT_HEADER), FRONT_RECESS)


def side_spec(h, z0=BODY_Z0, z1=None, extra=0.0):
    """The long side's recess between the corner posts and the rails."""
    z1 = h - TOP_PROUD if z1 is None else z1
    return (SIDE_POST + extra, SIDE_POST + extra, BODY_Z0 + BOTTOM_RAIL - z0,
            z1 - (h - TOP_PROUD - TOP_RAIL), SIDE_RECESS)


def body_mesh(name, length, h, door_h, colour, reefer=False, front=True):
    """The box's body: one closed shell inside the castings. `front=False`
    leaves the front end flat (the 45, whose budget goes on its extra
    fittings)."""
    hw, hl = BOX_W / 2 - BODY_IN, length / 2 - BODY_IN
    specs = {"-y": door_spec(h, door_h)}
    back = {}
    if reefer:
        # the machinery bay: the front frame round a deep recess
        specs["+y"] = (REEFER_POST, REEFER_POST, FRONT_SILL_Z - BODY_Z0, REEFER_HEADER, REEFER_RECESS)
        back["+y"] = 1
    else:
        if front:
            specs["+y"] = front_spec(h)
        specs["-x"] = specs["+x"] = side_spec(h)
    bm = recessed_box_bm(-hw, hw, -(length / 2 - DOOR_END_IN), hl, BODY_Z0, h - TOP_PROUD, specs, back)
    mats = [box_mat(colour)] + ([M("reefer_bay")] if reefer else [])
    return make_mesh(name, bm, mats)


class BoxKit:
    """The meshes the boxes share: one casting, one hinge, and the door bars
    and seam strip of each box height."""

    def __init__(self):
        self.casting = make_mesh("box_casting", box_bm(-CAST_X / 2, CAST_X / 2, -CAST_Y / 2, CAST_Y / 2,
                                                       -CAST_Z / 2, CAST_Z / 2), [M("fittings")])
        depth = DOOR_RECESS + 0.02 + HINGE_PROUD
        self.hinge = make_mesh("box_hinge", box_bm(-(HINGE_X1 - HINGE_X0) / 2, (HINGE_X1 - HINGE_X0) / 2,
                                                   -depth / 2, depth / 2, -HINGE_H / 2, HINGE_H / 2), [M("fittings")])
        self.bar, self.seam = {}, {}
        for key, door_h in (("std", DOOR_OPEN_H), ("hc", DOOR_OPEN_H_HC)):
            bar_l = door_h + 2 * BAR_OVERRUN
            bar_d = 0.02 + BAR_PROUD   # 2 cm into the doors, BAR_PROUD out of them
            self.bar[key] = make_mesh(f"box_door_bar_{key}", box_bm(-BAR_T / 2, BAR_T / 2, -bar_d / 2, bar_d / 2,
                                                                    -bar_l / 2, bar_l / 2), [M("fittings")])
            seam_l = door_h - 0.02
            self.seam[key] = make_mesh(f"box_door_seam_{key}", box_bm(-SEAM_W / 2, SEAM_W / 2, -0.02, 0.02,
                                                                      -seam_l / 2, seam_l / 2), [M("fittings")])


def build_box(kit, coll, variant, length, h, colour, reefer=False, front=True):
    """One box at the origin: body, castings, door hardware (and the
    reefer's machinery). Returns its objects (the loaded rig links them)."""
    hc = h > BOX_H + 0.01
    door_h = DOOR_OPEN_H_HC if hc else DOOR_OPEN_H
    body = body_mesh(f"{variant}_body", length, h, door_h, colour, reefer, front)
    objs = [place(f"{variant}_body", body, coll, variant)]
    for sx, xs in ((-1, "l"), (1, "r")):
        for sy, ys in ((-1, "door"), (1, "front")):
            for z, zs in ((CAST_Z / 2, "bot"), (h - CAST_Z / 2, "top")):
                loc = (sx * (BOX_W / 2 - CAST_X / 2), sy * (length / 2 - CAST_Y / 2), z)
                objs.append(place(f"{variant}_casting_{ys}_{xs}_{zs}", kit.casting, coll, variant, loc))
    # the door end, at -Y: the frame's face y_f, the doors' face y_d behind it
    y_f = -(length / 2 - DOOR_END_IN)
    y_d = y_f + DOOR_RECESS
    key = "hc" if hc else "std"
    bar_l = door_h + 2 * BAR_OVERRUN
    bar_y = ((y_d + 0.02) + (y_d - BAR_PROUD)) / 2
    for k, x in enumerate(BAR_X):
        objs.append(place(f"{variant}_door_bar_{k}", kit.bar[key], coll, variant,
                          (x, bar_y, DOOR_SILL - BAR_OVERRUN + bar_l / 2)))
    objs.append(place(f"{variant}_door_seam", kit.seam[key], coll, variant,
                      (0.0, y_d, DOOR_SILL + door_h / 2)))
    hinge_y = ((y_d + 0.02) + (y_f - HINGE_PROUD)) / 2
    for sx, xs in ((-1, "l"), (1, "r")):
        for k, z in enumerate(HINGE_Z_HC if hc else HINGE_Z):
            objs.append(place(f"{variant}_hinge_{xs}{k}", kit.hinge, coll, variant,
                              (sx * (HINGE_X0 + HINGE_X1) / 2, hinge_y, z)))
    if reefer:
        objs += build_reefer_unit(coll, variant, length, h)
    return objs


def build_reefer_unit(coll, variant, length, h):
    """The machinery in the front bay: the evaporator panel over the bay's
    upper half, the condenser fan's guard and the control box below."""
    y_f = length / 2 - BODY_IN
    y_b = y_f - REEFER_RECESS
    x_wall = BOX_W / 2 - BODY_IN - REEFER_POST
    top = h - TOP_PROUD - REEFER_HEADER
    unit = M("reefer_unit")
    objs = [box(f"{variant}_reefer_panel", coll, unit, -x_wall - 0.02, x_wall + 0.02, y_b - 0.02,
                y_b + REEFER_PANEL_OUT, REEFER_PANEL_Z, top + 0.02, variant)]
    fx, fz, fr = REEFER_FAN
    fan = prism_bm(ring(fx, fz, fr, 6), "y", y_b - 0.02, y_b + REEFER_FAN_OUT)
    objs.append(finish(f"{variant}_reefer_fan_guard", fan, coll, [unit], variant))
    cx0, cx1, cz0, cz1 = REEFER_CONTROL
    objs.append(box(f"{variant}_reefer_control_box", coll, unit, cx0, cx1, y_b - 0.02, y_b + REEFER_CONTROL_OUT,
                    cz0, cz1, variant))
    return objs


# --- the yard rows ---------------------------------------------------------------

def row_colours(seed, slots, tiers):
    """A colour per box: never the colour of the box under it or beside it."""
    rng = random.Random(seed)
    grid = {}
    for s in range(slots):
        for t in range(tiers):
            banned = {grid.get((s, t - 1)), grid.get((s - 1, t))}
            grid[(s, t)] = rng.choice([c for c in range(len(COLOUR_NAMES)) if c not in banned])
    return grid


def column(bm, vert, x0, x1, y0, y1, h, colours, seam_index, door_end, front_end, door_h=DOOR_OPEN_H, flat=()):
    """One slot's stack as a single closed column: a tier per box, a V seam
    cut round it between tiers, each box's long sides recessed between its
    posts and rails, and its -Y / +Y faces recessed as door / front ends
    where `door_end` / `front_end` (the row's two ends). Sides in `flat`
    (1 is +X, 3 is -X) stay unrecessed: a double row's inner sides."""
    tiers = len(colours)
    rings = [(0.0, 0.0)]
    for t in range(1, tiers):
        rings += [(t * h - SEAM_H / 2, 0.0), (t * h, SEAM_D), (t * h + SEAM_H / 2, 0.0)]
    rings.append((tiers * h, 0.0))

    def corners(z, s):
        return [Vector((x0 + s, y0 + s, z)), Vector((x1 - s, y0 + s, z)),
                Vector((x1 - s, y1 - s, z)), Vector((x0 + s, y1 - s, z))]

    inward = (Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, -1, 0)), Vector((1, 0, 0)))
    for r in range(len(rings) - 1):
        (za, sa), (zb, sb) = rings[r], rings[r + 1]
        lo, hi = corners(za, sa), corners(zb, sb)
        if sa == 0.0 and sb == 0.0:
            t = int(za // h + 1e-6) if za > 0 else 0
            t = min(t, tiers - 1)
            base = t * h
            for side in range(4):
                o = [lo[side], lo[(side + 1) % 4], hi[(side + 1) % 4], hi[side]]
                spec = None
                if side in (1, 3) and side not in flat:
                    spec = side_spec(h, z0=za - base, z1=zb - base, extra=BODY_IN)
                elif side == 0 and door_end:
                    spec = door_spec(h, door_h, w=BOX_W, z0=za - base, z1=zb - base)
                elif side == 2 and front_end:
                    spec = front_spec(h, w=BOX_W, z0=za - base, z1=zb - base, extra=BODY_IN)
                panel(bm, vert, o, inward[side], spec, colours[t])
        else:
            for side in range(4):
                face(bm, [vert(p) for p in (lo[side], lo[(side + 1) % 4], hi[(side + 1) % 4], hi[side])],
                     seam_index)
    face(bm, [vert(p) for p in corners(0.0, 0.0)], colours[0])
    face(bm, [vert(p) for p in corners(tiers * h, 0.0)], colours[-1])


def consignment_colours(seed, slots, tiers):
    """The container ship's mix: weighted colours, clumped as consignments
    are, a box taking the colour of the one under it or the one before it."""
    rng = random.Random(seed)
    grid = {}
    for t in range(tiers):
        for s in range(slots):
            r = rng.random()
            if t > 0 and r < SAME_AS_BELOW:
                grid[(s, t)] = grid[(s, t - 1)]
            elif s > 0 and r < SAME_AS_BELOW + SAME_AS_BESIDE:
                grid[(s, t)] = grid[(s - 1, t)]
            else:
                grid[(s, t)] = rng.choices(range(len(COLOUR_NAMES)), CONSIGN_WEIGHTS)[0]
    return grid


def build_row(coll, variant, box_l, seed, h=BOX_H, door_h=DOOR_OPEN_H, tiers=ROW_TIERS, rows=1, mix=None):
    """A row of ROW_SLOTS boxes end to end, `tiers` high, as one mesh. 40 ft
    boxes stand SLOT_GAP apart; 20 ft boxes stand in pairs ISO_PAIR_GAP apart
    in 40 ft slots, so a 20 ft row is three 40 ft slots long. `rows=2` puts
    two rows side by side DOUBLE_GAP apart, their facing sides flat; `mix`
    picks the colours (row_colours by default)."""
    ys, y = [], 0.0
    for s in range(ROW_SLOTS):
        ys.append(y)
        gap = SLOT_GAP if (box_l > L20 + 0.01 or s % 2 == 1) else ISO_PAIR_GAP
        y += box_l + gap
    total = ys[-1] + box_l
    mix = mix or row_colours
    seam_index = len(COLOUR_NAMES)
    bm = bmesh.new()
    vert = Verts(bm)
    span = rows * BOX_W + (rows - 1) * DOUBLE_GAP
    for r in range(rows):
        grid = mix(seed + r, ROW_SLOTS, tiers)
        x0 = -span / 2 + r * (BOX_W + DOUBLE_GAP)
        flat = (() if rows == 1 else (1,) if r == 0 else (3,) if r == rows - 1 else (1, 3))
        for s, y0 in enumerate(ys):
            y0 -= total / 2
            column(bm, vert, x0, x0 + BOX_W, y0, y0 + box_l, h,
                   [grid[(s, t)] for t in range(tiers)], seam_index, s == 0, s == ROW_SLOTS - 1, door_h, flat)
    mats = [box_mat(c) for c in COLOUR_NAMES] + [M("seam")]
    obj = finish(variant, bm, coll, mats, variant)
    return obj, total


# --- the straddle carrier -----------------------------------------------------------

def build_straddle(coll, variant="straddle_carrier"):
    """The straddle carrier: two side frames on their wheels, legs, the top
    frame and its girders, the raised spreader, the engine house, cabinet and
    cab on top, the ladder. Every part laps 2 cm or more into what it meets."""
    v = variant
    paint, housing, steel = M("carrier_paint"), M("carrier_housing"), M("steel")
    tyre_mesh = make_mesh("sc_tyre", cylinder_bm("x", SC_TYRE_D / 2, SC_TYRE_W / 2, 12), [M("tyre")])
    hub_mesh = make_mesh("sc_hub", cylinder_bm("x", SC_HUB_R, 0.04, 8), [M("hub")])
    xc = (SC_IN + SC_OUT) / 2
    zc = SC_TYRE_D / 2 * math.cos(math.pi / 12)    # the 12-gon's flat sits on the ground
    z0, z1 = SC_SILL_Z
    hx0, hx1, hhalf, hfoot = SC_WHEEL_HOUSING
    cy, cz = SC_BEAM_CHAMFER
    for sx, s in ((-1, "l"), (1, "r")):
        for k, y in enumerate(SC_AXLES):
            place(f"{v}_tyre_{s}{k}", tyre_mesh, coll, v, (sx * xc, y, zc))
            place(f"{v}_hub_{s}{k}", hub_mesh, coll, v, (sx * (xc + SC_TYRE_W / 2 - 0.02), y, zc))
            # the wheel's fork housing, lapped into the bottom beam and over the tyre's top
            box(f"{v}_wheel_housing_{s}{k}", coll, paint, *sorted((sx * hx0, sx * hx1)),
                y - hhalf, y + hhalf, hfoot, z0 + 0.04, v)
        # the bottom beam, its lower ends chamfered
        prof = [(-SC_HALF, z1), (-SC_HALF, cz), (-cy, z0), (cy, z0), (SC_HALF, cz), (SC_HALF, z1)]
        lo, hi = sorted((sx * SC_IN, sx * SC_OUT))
        finish(f"{v}_bottom_beam_{s}", prism_bm(prof, "x", lo, hi), coll, [paint], v)
        # the legs, tapering in toward the middle as they rise
        for sy, e in ((-1, "rear"), (1, "front")):
            xa, xb = sorted((sx * SC_LEG_X[0], sx * SC_LEG_X[1]))
            ya0, ya1 = sorted((sy * SC_LEG_FOOT_Y[0], sy * SC_LEG_FOOT_Y[1]))
            yb0, yb1 = sorted((sy * SC_LEG_HEAD_Y[0], sy * SC_LEG_HEAD_Y[1]))
            finish(f"{v}_leg_{e}_{s}", tapered_bm((xa, xb, ya0, ya1, z1 - 0.02), (xa, xb, yb0, yb1, SC_TOP_Z[0] + 0.02)),
                   coll, [paint], v)
        # the top side beam
        box(f"{v}_top_beam_{s}", coll, paint, lo, hi, -SC_HALF, SC_HALF, *SC_TOP_Z, v)
    # the top frame's cross girders, inset top and bottom from the side
    # beams' faces (the hoist beams a little more), so none shares a plane
    for name, (y0, y1) in SC_GIRDERS.items():
        inset = 0.05 + (0.02 if "hoist" in name else 0.0)
        box(f"{v}_{name}", coll, paint, -SC_GIRDER_X, SC_GIRDER_X, y0, y1, SC_TOP_Z[0] + inset, SC_TOP_Z[1] - inset, v)
    # the spreader, raised, telescoped to 20 ft, on four rope falls into the hoist beams
    box(f"{v}_spreader", coll, M("spreader"), -SC_SPREADER_HALF_W, SC_SPREADER_HALF_W, -SC_SPREADER_L / 2,
        SC_SPREADER_L / 2, SC_UNDER_SPREADER, SC_UNDER_SPREADER + SC_SPREADER_T, v)
    rx, ry, rh = SC_ROPES
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * rx, sy * ry
            box(f"{v}_rope_{'lr'[sx > 0]}{'rf'[sy > 0]}", coll, steel, x - rh, x + rh, y - rh, y + rh,
                SC_UNDER_SPREADER + SC_SPREADER_T - 0.02, SC_TOP_Z[0] + 0.07 + 0.02, v)
    # the engine house on top at the back, its roof, louvres and exhaust
    ex0, ex1, ey0, ey1, etop = SC_ENGINE_HOUSE
    box(f"{v}_engine_house", coll, housing, ex0, ex1, ey0, ey1, SC_TOP_Z[1] - 0.10, etop, v)
    box(f"{v}_engine_roof", coll, housing, ex0 - 0.05, ex1 + 0.05, ey0 - 0.05, ey1 + 0.05,
        etop - 0.03, etop - 0.03 + SC_ENGINE_ROOF_T, v)
    lx0, lx1, lz0, lz1 = SC_LOUVRES
    box(f"{v}_engine_louvres", coll, M("grille"), lx0, lx1, ey0 - 0.03, ey0 + 0.02, lz0, lz1, v)
    px, py, pr = SC_EXHAUST
    finish(f"{v}_exhaust", prism_bm(ring(px, py, pr, 8), "z", etop + 0.05, SC_HEIGHT), coll, [steel], v)
    # the electrical cabinet, front right
    bx0, bx1, by0, by1, btop = SC_CABINET
    box(f"{v}_cabinet", coll, housing, bx0, bx1, by0, by1, SC_TOP_Z[1] - 0.10, btop, v)
    # the cab, high at the front left, and its windows as dark slabs set proud
    cx0, cx1, cy0, cy1, cz0, cz1 = SC_CAB
    wz0, wz1 = SC_CAB_WINDOW_Z
    box(f"{v}_cab", coll, housing, cx0, cx1, cy0, cy1, cz0, cz1, v)
    box(f"{v}_cab_roof", coll, housing, cx0 - 0.04, cx1 + 0.04, cy0 - 0.04, cy1 + 0.06, cz1 - 0.03, cz1 + 0.07, v)
    glass = M("glass")
    box(f"{v}_cab_window_front", coll, glass, cx0 + 0.08, cx1 - 0.08, cy1 - 0.02, cy1 + 0.02, SC_CAB_FRONT_SILL, wz1, v)
    box(f"{v}_cab_window_left", coll, glass, cx0 - 0.02, cx0 + 0.02, cy0 + 0.17, cy1 - 0.13, wz0, wz1, v)
    box(f"{v}_cab_window_right", coll, glass, cx1 - 0.02, cx1 + 0.02, cy0 + 0.17, cy1 - 0.13, wz0, wz1, v)
    gx, gy, gr, gh = SC_BEACON
    finish(f"{v}_beacon", prism_bm(ring(gx, gy, gr, 8), "z", cz1 + 0.05, cz1 + 0.05 + gh), coll, [M("beacon")], v)
    # the ladder up the left front leg, into the top beam
    ax0, ax1, ay0, ay1, afoot = SC_LADDER
    box(f"{v}_ladder", coll, steel, ax0, ax1, ay0, ay1, afoot, SC_TOP_Z[0] + 0.04, v)


# --- the yard tractor and chassis ---------------------------------------------------

def build_tractor(coll, v, wheels):
    """The terminal tractor, tractor-local y shifted by YT_SHIFT: the frame,
    the offset cab with the engine housing beside it, the apron and step
    that close the front, the fifth wheel, deck plate, fenders, fuel tank."""
    S = YT_SHIFT
    paint, chassis, steel, glass = M("tractor_paint"), M("chassis"), M("steel"), M("glass")

    def bx(name, mat, x0, x1, y0, y1, z0, z1):
        return box(f"{v}_tractor_{name}", coll, mat, x0, x1, y0 + S, y1 + S, z0, z1, v)

    single, dual, hub = wheels
    zc = TYRE_D / 2 * math.cos(math.pi / 12)
    fx0, fx1, fhalf, fz0, fz1 = YT_FENDER
    kx0, kx1, kfoot = YT_FENDER_BRACKET
    for sx, s in ((-1, "l"), (1, "r")):
        place(f"{v}_tractor_tyre_front_{s}", single, coll, v, (sx * YT_FRONT_TRACK / 2, YT_WHEELBASE + S, zc))
        place(f"{v}_tractor_hub_front_{s}", hub, coll, v,
              (sx * (YT_FRONT_TRACK / 2 + TYRE_W / 2 - 0.02), YT_WHEELBASE + S, zc))
        xd = YT_HALF_W - DUAL_W / 2
        place(f"{v}_tractor_tyre_rear_{s}", dual, coll, v, (sx * xd, S, zc))
        place(f"{v}_tractor_hub_rear_{s}", hub, coll, v, (sx * (xd + DUAL_W / 2 - 0.02), S, zc))
        # frame rail (into the front bumper), rear fender and its bracket
        bx(f"frame_rail_{s}", chassis, *sorted((sx * YT_FRAME_X[0], sx * YT_FRAME_X[1])), YT_REAR,
           YT_BUMPER_FRONT[1] + 0.02, *YT_FRAME_Z)
        bx(f"fender_rear_{s}", steel, *sorted((sx * fx0, sx * fx1)), -fhalf, fhalf, fz0, fz1)
        bx(f"fender_bracket_{s}", steel, *sorted((sx * kx0, sx * kx1)), -0.08, 0.08, kfoot, fz0 + 0.02)
    # the cab, offset left, on its mount; roof, windows, beacon
    cx0, cx1, cy0, cy1, cz0, cz1 = YT_CAB
    wz0, wz1 = YT_CAB_WINDOW_Z
    bx("cab", paint, cx0, cx1, cy0, cy1, cz0, cz1)
    mx0, mx1, my0, my1 = YT_CAB_MOUNT
    bx("cab_mount", chassis, mx0, mx1, my0, my1, YT_FRAME_Z[1] - 0.02, cz0 + 0.02)
    bx("cab_roof", paint, cx0 - 0.025, cx1 + 0.025, cy0 - 0.03, cy1 + 0.03, cz1 - 0.03, cz1 + 0.07)
    bx("cab_window_front", glass, cx0 + 0.10, cx1 - 0.10, cy1 - 0.02, cy1 + 0.02, wz0, wz1)
    bx("cab_window_rear", glass, cx0 + 0.10, cx1 - 0.10, cy0 - 0.02, cy0 + 0.02, wz0, wz1)
    bx("cab_window_left", glass, cx0 - 0.015, cx0 + 0.02, cy0 + 0.12, cy1 - 0.12, wz0, wz1)
    bx("cab_window_right", glass, cx1 - 0.02, cx1 + 0.015, cy0 + 0.12, cy1 - 0.12, wz0, wz1)
    gx, gy, gr, gh = YT_BEACON
    finish(f"{v}_tractor_beacon", prism_bm(ring(gx, gy + S, gr, 8), "z", cz1 + 0.05, cz1 + 0.05 + gh), coll,
           [M("beacon")], v)
    # the engine housing beside the cab, its sloped nose, grille, the engine under it
    hx0, hx1, hy0, hy1, hz0, hz1 = YT_HOOD
    ny, nz = YT_HOOD_NOSE
    prof = [(hy0 + S, hz0), (hy1 + S, hz0), (hy1 + S, nz), (ny + S, hz1), (hy0 + S, hz1)]
    finish(f"{v}_tractor_engine_hood", prism_bm(prof, "x", hx0, hx1), coll, [paint], v)
    gx0, gx1, gz0, gz1 = YT_GRILLE
    bx("radiator_grille", M("grille"), gx0, gx1, hy1 - 0.02, hy1 + 0.03, gz0, gz1)
    ex0, ex1, ey0, ey1, efoot = YT_ENGINE
    bx("engine", chassis, ex0, ex1, ey0, ey1, efoot, hz0 + 0.02)
    px, py, pr, pz0, pz1 = YT_EXHAUST
    finish(f"{v}_tractor_exhaust", prism_bm(ring(px, py + S, pr, 8), "z", pz0, pz1), coll, [steel], v)
    bw, by0, bz0, bz1 = YT_BUMPER_FRONT
    bx("bumper_front", chassis, -bw, bw, by0, YT_FRONT, bz0, bz1)
    rw, rz0, rz1 = YT_BUMPER_REAR
    bx("bumper_rear", chassis, -rw, rw, YT_REAR - 0.02, YT_REAR + 0.18, rz0, rz1)
    # the apron across the front ahead of the front wheels, under the cab and
    # hood, and the cab's entry step behind the left front wheel, so the
    # front reads solid rather than as a frame on wheels
    bx("front_apron", paint, cx0 + 0.01, YT_APRON_X, YT_WHEELBASE + TYRE_D / 2 + 0.04, by0 + 0.025,
       YT_FRAME_Z[0] - 0.05, cz0 + 0.04)
    bx("cab_step", steel, cx0 + 0.01, YT_STEP_X, cy0 + 0.03, YT_WHEELBASE - TYRE_D / 2 - 0.04,
       YT_FRAME_Z[0] - 0.05, cz0 + 0.04)
    # the fifth wheel on its mount, the deck plate behind the cab, the fuel tank
    fw, fl, ft = FIFTH_PLATE
    bx("fifth_wheel", steel, -fw, fw, KINGPIN_Y - fl, KINGPIN_Y + fl, FIFTH_TOP - ft, FIFTH_TOP)
    mw, ml = FIFTH_MOUNT
    bx("fifth_wheel_mount", chassis, -mw, mw, KINGPIN_Y - ml, KINGPIN_Y + ml, YT_FRAME_Z[1] - 0.02, FIFTH_TOP - 0.07)
    bx("deck_plate", steel, *YT_DECK)
    bx("fuel_tank", steel, *YT_FUEL_TANK)


def build_chassis(coll, v, wheels):
    """The 40 ft straight-frame chassis, its kingpin on the fifth wheel: two
    rails, bolsters with twist-locks under the box's four bottom castings,
    cross members, landing gear wound up, a tandem on duals, the rear
    underride bar and mudflaps."""
    S = YT_SHIFT
    chassis, steel = M("chassis"), M("steel")

    def bx(name, mat, x0, x1, y0, y1, z0, z1):
        return box(f"{v}_chassis_{name}", coll, mat, x0, x1, y0 + S, y1 + S, z0, z1, v)

    single, dual, hub = wheels
    zc = TYRE_D / 2 * math.cos(math.pi / 12)
    box_front = CH_FRONT - 0.01
    box_rear = box_front - L40
    for sx, s in ((-1, "l"), (1, "r")):
        bx(f"rail_{s}", chassis, *sorted((sx * CH_RAIL_X[0], sx * CH_RAIL_X[1])), CH_REAR + 0.05, CH_FRONT - 0.05,
           *CH_RAIL_Z)
        # twist-locks: lapped 2 cm up into the box's castings when it is on
        xa, xb = sorted((sx * CH_TWISTLOCK_X[0], sx * CH_TWISTLOCK_X[1]))
        bx(f"twistlock_front_{s}", steel, xa, xb, box_front - 0.16, box_front - 0.02, DECK_Z - 0.05, DECK_Z + 0.02)
        bx(f"twistlock_rear_{s}", steel, xa, xb, box_rear + 0.02, box_rear + 0.16, DECK_Z - 0.05, DECK_Z + 0.02)
        # landing leg and its sand shoe, wound up clear of the ground
        lx0, lx1, lhalf, lfoot = CH_LANDING_LEG
        bx(f"landing_leg_{s}", steel, *sorted((sx * lx0, sx * lx1)), LANDING_Y - lhalf, LANDING_Y + lhalf, lfoot,
           CH_RAIL_Z[0] + 0.02)
        sx0, sx1, shalf, sz0, sz1 = CH_SAND_SHOE
        bx(f"sand_shoe_{s}", steel, *sorted((sx * sx0, sx * sx1)), LANDING_Y - shalf, LANDING_Y + shalf, sz0, sz1)
        ux0, ux1, uy0, uy1, ufoot = CH_BUMPER_STRUT
        bx(f"bumper_strut_{s}", steel, *sorted((sx * ux0, sx * ux1)), CH_REAR + uy0, CH_REAR + uy1, ufoot,
           CH_RAIL_Z[0] + 0.02)
        fx0, fx1, fy0, fy1, ffoot = CH_MUDFLAP
        bx(f"mudflap_{s}", chassis, *sorted((sx * fx0, sx * fx1)), CH_REAR + fy0, CH_REAR + fy1, ffoot,
           CH_BOLSTER[1] + 0.02)
        hx0, hx1, hhalf, hfoot = CH_HANGER
        for k, y in enumerate(CH_AXLES):
            xd = CH_HALF_W - DUAL_W / 2
            place(f"{v}_chassis_tyre_{s}{k}", dual, coll, v, (sx * xd, y + S, zc))
            place(f"{v}_chassis_hub_{s}{k}", hub, coll, v, (sx * (xd + DUAL_W / 2 - 0.02), y + S, zc))
            bx(f"hanger_{s}{k}", chassis, *sorted((sx * hx0, sx * hx1)), y - hhalf, y + hhalf, hfoot,
               CH_RAIL_Z[0] + 0.02)
    cw, cback = CH_COUPLER
    bx("coupler_plate", steel, -cw, cw, KINGPIN_Y - cback, CH_FRONT - 0.10, FIFTH_TOP - 0.02, FIFTH_TOP + 0.04)
    depth, foot = CH_BOLSTER
    bx("bolster_front", chassis, -CH_HALF_W, CH_HALF_W, CH_FRONT - depth, CH_FRONT, foot, DECK_Z - 0.03)
    bx("bolster_rear", chassis, -CH_HALF_W, CH_HALF_W, CH_REAR + 0.10, CH_REAR + 0.10 + depth, foot, DECK_Z - 0.03)
    mw, mhalf, mz0, mz1 = CH_CROSS
    for k, y in enumerate(CH_CROSS_MEMBERS):
        bx(f"cross_member_{k}", chassis, -mw, mw, y - mhalf, y + mhalf, mz0, mz1)
    qw, qhalf, qz0, qz1 = CH_CROSSBAR
    bx("landing_crossbar", steel, -qw, qw, LANDING_Y - qhalf, LANDING_Y + qhalf, qz0, qz1)
    aw, ahalf, az0, az1 = CH_AXLE
    for k, y in enumerate(CH_AXLES):
        bx(f"axle_{k}", chassis, -aw, aw, y - ahalf, y + ahalf, az0, az1)
    rw, rd, rz0, rz1 = CH_BUMPER
    bx("bumper_rear", chassis, -rw, rw, CH_REAR, CH_REAR + rd, rz0, rz1)


# --- the further variants -------------------------------------------------------------

def link(src, name, coll, variant, offset=(0.0, 0.0, 0.0)):
    """A linked copy of the object `src` (its mesh shared), moved by `offset`."""
    dup = src.copy()
    dup.name = name
    dup["kyt_variant"] = variant
    dup.location = src.location + Vector(offset)
    coll.objects.link(dup)
    return dup


def build_ribbed(coll, variant, box40):
    """The close-up box: box_40's parts linked, and broad ribs standing in its
    side and front panels, one mesh per panel kind, linked rib to rib. Each
    rib laps 2 cm into the panel and stops RIB_SHY behind the frame's face;
    its ends run 2 cm into the rails."""
    for src in box40:
        link(src, src.name.replace("box_40_", f"{variant}_", 1), coll, variant)
    y0, y1 = -(L40 / 2 - DOOR_END_IN) + SIDE_POST, L40 / 2 - BODY_IN - SIDE_POST
    pitch = (y1 - y0) / RIB_SIDE_COUNT
    a, b = RIB_OUTER * pitch / 2, RIB_BASE * pitch / 2
    back = -(SIDE_RECESS + 0.02)
    prof = [(back, -b), (-RIB_SHY, -a), (-RIB_SHY, a), (back, b)]
    side = make_mesh("box_rib_side", prism_bm(prof, "z", BODY_Z0 + BOTTOM_RAIL - 0.02,
                                              BOX_H - TOP_PROUD - TOP_RAIL + 0.02), [box_mat("rust_red")])
    prof = [(-(FRONT_RECESS + 0.02), -b), (-RIB_SHY, -a), (-RIB_SHY, a), (-(FRONT_RECESS + 0.02), b)]
    front = make_mesh("box_rib_front", prism_bm(prof, "z", FRONT_SILL_Z - 0.02,
                                                BOX_H - TOP_PROUD - FRONT_HEADER + 0.02), [box_mat("rust_red")])
    face_x = BOX_W / 2 - BODY_IN
    for k in range(RIB_SIDE_COUNT):
        y = y0 + pitch * (k + 0.5)
        place(f"{variant}_rib_r{k}", side, coll, variant, (face_x, y, 0.0))
        o = place(f"{variant}_rib_l{k}", side, coll, variant, (-face_x, y, 0.0))
        o.rotation_euler = (0.0, 0.0, math.pi)          # faces -X; a turn, never a mirror
    x0 = -(BOX_W / 2 - BODY_IN - FRONT_POST)
    fpitch = -2 * x0 / RIB_FRONT_COUNT
    for k in range(RIB_FRONT_COUNT):
        o = place(f"{variant}_rib_front{k}", front, coll, variant, (x0 + fpitch * (k + 0.5), L40 / 2 - BODY_IN, 0.0))
        o.rotation_euler = (0.0, 0.0, math.pi / 2)      # its outward face toward +Y


def build_box_45(kit, coll, variant):
    """The 45 ft high-cube: the high-cube's parts at 45 ft, its front left
    flat, and the extra bottom fittings at the 40 ft positions as two bars
    across the base, their ends standing out like castings."""
    build_box(kit, coll, variant, L45, BOX_HC_H, "dark_blue", front=False)
    bar = make_mesh("box_45_fitting_bar", box_bm(-BOX_W / 2, BOX_W / 2, -CAST_Y / 2, CAST_Y / 2, 0.0, CAST_Z),
                    [M("fittings")])
    for sy, e in ((-1, "door"), (1, "front")):
        place(f"{variant}_fitting_40ft_{e}", bar, coll, variant, (0.0, sy * FITTING_40_Y, 0.0))


def build_gooseneck(coll, variant, hc_box=None):
    """A 40 ft gooseneck chassis parked on its landing gear, front +Y: lower
    rails, the neck that rides up into a box's tunnel, bolsters and the
    straight chassis's twist-locks, running gear, bumper and coupler plate
    linked from the rig at their new place; with `hc_box`, a box_40_hc on it."""
    v = variant
    chassis, steel = M("chassis"), M("steel")
    front, rear = GN_HALF, -GN_HALF
    dy = front - (CH_FRONT + YT_SHIFT)              # the rig's chassis front to this one's
    rig = "yard_tractor_chassis_chassis_"
    for part in ("twistlock_front_l", "twistlock_front_r", "twistlock_rear_l", "twistlock_rear_r"):
        link(bpy.data.objects[rig + part], f"{v}_{part}", coll, v, (0.0, dy, GN_DECK_Z - DECK_Z))
    for part in ("tyre_l0", "tyre_l1", "tyre_r0", "tyre_r1", "hub_l0", "hub_l1", "hub_r0", "hub_r1",
                 "axle_0", "axle_1", "hanger_l0", "hanger_l1", "hanger_r0", "hanger_r1",
                 "bumper_rear", "bumper_strut_l", "bumper_strut_r", "mudflap_l", "mudflap_r", "coupler_plate"):
        link(bpy.data.objects[rig + part], f"{v}_{part}", coll, v, (0.0, dy, 0.0))
    for sx, s in ((-1, "l"), (1, "r")):
        box(f"{v}_rail_{s}", coll, chassis, *sorted((sx * CH_RAIL_X[0], sx * CH_RAIL_X[1])), rear + 0.05, front - 0.07,
            *GN_RAIL_Z, v)
        lx0, lx1, lhalf, _ = CH_LANDING_LEG
        box(f"{v}_landing_leg_{s}", coll, steel, *sorted((sx * lx0, sx * lx1)), GN_LANDING_Y - lhalf,
            GN_LANDING_Y + lhalf, GN_SAND_SHOE_Z[1] - 0.02, GN_RAIL_Z[0] + 0.02, v)
        sx0, sx1, shalf, _, _ = CH_SAND_SHOE
        box(f"{v}_sand_shoe_{s}", coll, steel, *sorted((sx * sx0, sx * sx1)), GN_LANDING_Y - shalf,
            GN_LANDING_Y + shalf, *GN_SAND_SHOE_Z, v)
    # the neck: a beam from the coupler plate up into the box's tunnel, its
    # rear end stepping down onto the main rails
    length, half_w, rise = GN_NECK
    step = front - length
    top = GN_DECK_Z + rise
    prof = [(step - GN_NECK_RAMP, GN_NECK_Z0), (front - 0.05, GN_NECK_Z0), (front - 0.05, top), (step, top),
            (step - GN_NECK_RAMP, GN_RAIL_Z[1] - 0.02)]
    finish(f"{v}_neck", prism_bm(prof, "x", -half_w, half_w), coll, [chassis], v)
    depth = CH_BOLSTER[0]
    box(f"{v}_bolster_front", coll, chassis, -CH_HALF_W, CH_HALF_W, front - depth, front, GN_BOLSTER_Z0,
        GN_DECK_Z - 0.03, v)
    box(f"{v}_bolster_rear", coll, chassis, -CH_HALF_W, CH_HALF_W, rear + 0.10, rear + 0.10 + depth, GN_BOLSTER_Z0,
        GN_DECK_Z - 0.03, v)
    mw, mhalf, _, _ = CH_CROSS
    for k, y in enumerate(CH_CROSS_MEMBERS):
        y += front - CH_FRONT                         # the same distance behind the front as the straight chassis's
        box(f"{v}_cross_member_{k}", coll, chassis, -mw, mw, y - mhalf, y + mhalf, *GN_CROSS_Z, v)
    qw, qhalf, qz0, qz1 = CH_CROSSBAR
    box(f"{v}_landing_crossbar", coll, steel, -qw, qw, GN_LANDING_Y - qhalf, GN_LANDING_Y + qhalf, qz0, qz1, v)
    if hc_box:
        offset = (0.0, front - 0.01 - L40 / 2, GN_DECK_Z)
        for src in hc_box:
            link(src, f"{v}_" + src.name, coll, v, offset)


def build_straddle_1over2(coll, variant="straddle_carrier_1over2"):
    """The 1-over-2: the 1-over-3's wheels, housings and bottom beams linked
    where they are, everything above its legs linked SC2_DROP lower, and
    shorter legs and ladder of its own."""
    v, base = variant, "straddle_carrier_"
    paint, steel = M("carrier_paint"), M("steel")
    for o in list(bpy.data.collections["variant_straddle_carrier"].objects):
        part = o.name[len(base):]
        if part.startswith(("leg_", "ladder")):
            continue
        low = not part.startswith(("tyre_", "hub_", "wheel_housing_", "bottom_beam_"))
        link(o, f"{v}_{part}", coll, v, (0.0, 0.0, -SC2_DROP if low else 0.0))
    z1 = SC_SILL_Z[1]
    top = SC_TOP_Z[0] - SC2_DROP
    for sx, s in ((-1, "l"), (1, "r")):
        for sy, e in ((-1, "rear"), (1, "front")):
            xa, xb = sorted((sx * SC_LEG_X[0], sx * SC_LEG_X[1]))
            ya0, ya1 = sorted((sy * SC_LEG_FOOT_Y[0], sy * SC_LEG_FOOT_Y[1]))
            yb0, yb1 = sorted((sy * SC_LEG_HEAD_Y[0], sy * SC_LEG_HEAD_Y[1]))
            finish(f"{v}_leg_{e}_{s}", tapered_bm((xa, xb, ya0, ya1, z1 - 0.02), (xa, xb, yb0, yb1, top + 0.02)),
                   coll, [paint], v)
    ax0, ax1, ay0, ay1, afoot = SC_LADDER
    box(f"{v}_ladder", coll, steel, ax0, ax1, ay0, ay1, afoot, top + 0.04, v)


def build_straddle_low_cab(coll, variant="straddle_carrier_low_cab"):
    """The 1-over-3 with its cab hung low on the side: every part linked but
    the top cab, which goes, and the ladder, which now stops in the side
    cab's floor; the side cab outboard of the left front leg, under the top
    beam, with its roof, glass and beacon."""
    v, base = variant, "straddle_carrier_"
    housing, steel, glass = M("carrier_housing"), M("steel"), M("glass")
    for o in list(bpy.data.collections["variant_straddle_carrier"].objects):
        part = o.name[len(base):]
        if part == "cab" or part.startswith(("cab_", "beacon", "ladder")):
            continue
        link(o, f"{v}_{part}", coll, v)
    cx0, cx1, cy0, cy1, cz0, cz1 = SIDE_CAB
    wz0, wz1 = SIDE_CAB_WINDOW_Z
    box(f"{v}_cab", coll, housing, cx0, cx1, cy0, cy1, cz0, cz1, v)
    box(f"{v}_cab_roof", coll, housing, cx0 - 0.04, cx1 + 0.04, cy0 - 0.04, cy1 + 0.06, cz1 - 0.03, cz1 + 0.07, v)
    box(f"{v}_cab_window_front", coll, glass, cx0 + 0.08, cx1 - 0.08, cy1 - 0.02, cy1 + 0.02, SIDE_CAB_FRONT_SILL, wz1, v)
    box(f"{v}_cab_window_rear", coll, glass, cx0 + 0.08, cx1 - 0.08, cy0 - 0.02, cy0 + 0.02, wz0, wz1, v)
    box(f"{v}_cab_window_outer", coll, glass, cx0 - 0.02, cx0 + 0.02, cy0 + 0.17, cy1 - 0.13, wz0, wz1, v)
    gx, gy = SIDE_CAB_BEACON
    _, _, gr, gh = SC_BEACON
    finish(f"{v}_beacon", prism_bm(ring(gx, gy, gr, 8), "z", cz1 + 0.05, cz1 + 0.05 + gh), coll, [M("beacon")], v)
    ax0, ax1, ay0, ay1, afoot = SC_LADDER
    box(f"{v}_ladder", coll, steel, ax0, ax1, ay0, ay1, afoot, cz0 + 0.02, v)


# --- reference ----------------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    bm = prism_bm(ring(0.0, 0.0, r, 12, False), "z", 0.0, height - 0.40)
    body_verts = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for vv in bm.verts:
        if vv not in body_verts:
            vv.co.z += height - 0.17
    obj = place(name, make_mesh(name, bm, [mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0))], flat=False),
                coll, None, (x, y, z))
    return obj


def outline(name, coll, x0, x1, y0, y1, z=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    for i in range(4):
        bm.edges.new((vs[i], vs[(i + 1) % 4]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def build_reference(reference, bounds):
    for v in VARIANTS:
        lo, hi = bounds[v]
        outline(f"footprint_{v}", reference, lo.x, hi.x, lo.y, hi.y)
    lo, hi = bounds["straddle_carrier"]
    outline("crane_portal_clear_15m_over_carrier", reference, lo.x - 1.0, hi.x + 1.0, lo.y, hi.y, CRANE_PORTAL_CLEAR)
    figure("figure_1p7m", reference, 3.5, -2.0)


# --- reports ------------------------------------------------------------------------

def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def triangles(objs):
    total = 0
    for o in objs:
        o.data.calc_loop_triangles()
        total += len(o.data.loop_triangles)
    return total


def bounds_of(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def report(variant):
    objs = variant_objects(variant)
    tris = triangles(objs)
    lo, hi = bounds_of(objs)
    meshes = len({o.data.name for o in objs})
    print(f"{PROP}: {variant}: {len(objs)} parts ({meshes} meshes), {tris} triangles, "
          f"{hi.x - lo.x:.3f} wide (x) x {hi.y - lo.y:.3f} long (y) x {hi.z - lo.z:.3f} high; "
          f"x {lo.x:.2f}..{hi.x:.2f}, y {lo.y:.2f}..{hi.y:.2f}, z {lo.z:.3f}..{hi.z:.3f}")
    return lo, hi


def carrier_margins():
    """The straddle carrier against the crane portal and the 4-high row."""
    stack_top = ROW_TIERS * BOX_H
    print(f"{PROP}: straddle_carrier: overall height {SC_HEIGHT:.2f} m, crane portal clear {CRANE_PORTAL_CLEAR:.2f} m, "
          f"margin {CRANE_PORTAL_CLEAR - SC_HEIGHT:.2f} m")
    print(f"{PROP}: straddle_carrier: under the raised spreader {SC_UNDER_SPREADER:.2f} m over a {ROW_TIERS}-high row's "
          f"top {stack_top:.3f} m: {SC_UNDER_SPREADER - stack_top:.3f} m; under the top frame "
          f"{SC_TOP_Z[0]:.2f} m; inside clear {2 * SC_IN:.2f} m at the frames, "
          f"{2 * ((SC_IN + SC_OUT) / 2 - SC_TYRE_W / 2):.2f} m at the tyres, over a {BOX_W:.3f} m box: "
          f"{(2 * SC_IN - BOX_W) / 2:.3f} m each side")
    print(f"{PROP}: straddle_carrier: rows it works need a lane of at least "
          f"{SC_OUT - BOX_W / 2:.2f} m from a box's side to the next row's (the side frame and its tyres)")
    low_top = ROW_TIERS_LOW * BOX_H
    print(f"{PROP}: straddle_carrier_1over2: overall height {SC2_HEIGHT:.2f} m, crane portal clear "
          f"{CRANE_PORTAL_CLEAR:.2f} m, margin {CRANE_PORTAL_CLEAR - SC2_HEIGHT:.2f} m")
    print(f"{PROP}: straddle_carrier_1over2: under the raised spreader {SC2_UNDER_SPREADER:.2f} m over a "
          f"{ROW_TIERS_LOW}-high row's top {low_top:.3f} m: {SC2_UNDER_SPREADER - low_top:.3f} m; over a "
          f"{ROW_TIERS_LOW}-high high-cube row's {ROW_TIERS_LOW * BOX_HC_H:.3f} m: "
          f"{SC2_UNDER_SPREADER - ROW_TIERS_LOW * BOX_HC_H:.3f} m; under the top frame {SC_TOP_Z[0] - SC2_DROP:.2f} m; "
          f"it cannot straddle a {ROW_TIERS}-high row ({stack_top:.3f} m); inside clear and lane as the 1-over-3")
    print(f"{PROP}: straddle_carrier: a {ROW_TIERS}-high high-cube row ({ROW_TIERS * BOX_HC_H:.3f} m) is over its "
          f"{SC_UNDER_SPREADER:.2f} m: it works high-cubes three high")
    cx0, _, _, _, cz0, _ = SIDE_CAB
    print(f"{PROP}: straddle_carrier_low_cab: the side cab overhangs the frame by {-cx0 - SC_OUT:.2f} m "
          f"({SC_OUT - cx0:.2f} m overall), its floor {cz0:.2f} m, {cz0 - stack_top:.3f} m over a neighbouring {ROW_TIERS}-high row; "
          f"height {SC_HEIGHT:.2f} m (the exhaust), portal margin {CRANE_PORTAL_CLEAR - SC_HEIGHT:.2f} m")


# --- renders -------------------------------------------------------------------------

def render(folder):
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    for name in ("authored", "reference"):
        bpy.data.collections[name].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    # the quay the shore props stand on, its top at z = 0, the water beyond
    # its +Y edge (the frame's waterside), lower
    quay, water = mat("_quay", (0.25, 0.24, 0.22)), mat("_water", (0.10, 0.28, 0.45))
    box_bm_obj = lambda n, m, *b: place(n, make_mesh(n, box_bm(*b), [m]), stage, None)
    box_bm_obj("_quay", quay, -400, 400, -400, 60, -2.0, -0.003)
    box_bm_obj("_water", water, -400, 400, 60, 400, -3.5, -2.5)
    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.45, -0.70, 0.75)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(sun)
    fill = bpy.data.objects.new("_fill", bpy.data.lights.new("_fill", "SUN"))
    fill.data.energy = 0.9
    fill.data.use_shadow = False
    fill.rotation_euler = Vector((0.5, 0.8, 0.45)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(fill)
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
    fig_mat = mat("_figure_stage", (0.30, 0.22, 0.40))

    export_meshes = [o for o in bpy.data.collections["export"].all_objects if o.type == "MESH"]

    def show(variants):
        for o in export_meshes:
            o.hide_render = str(o.get("kyt_variant", "")) not in variants

    def points(objs):
        bpy.context.view_layer.update()     # objects just placed have stale matrices until this
        return [o.matrix_world @ vv.co for o in objs for vv in o.data.vertices]

    def shoot(name, pts, direction, lens=35, ortho=False, size=(1600, 1000), up=None):
        scene.render.resolution_x, scene.render.resolution_y = size
        d = Vector(direction).normalized()
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        centre = (lo + hi) / 2
        span = max((hi - lo).length, 2.0)
        cam.data.clip_start = 0.05
        cam.data.clip_end = 4000
        cam.rotation_euler = (-d).to_track_quat("-Z", up or "Y").to_euler()
        if ortho:
            cam.data.type = "ORTHO"
            cam.location = centre + d * (span + 50)
            bpy.context.view_layer.update()
            inv = cam.matrix_world.inverted()
            cs = [inv @ p for p in pts]
            w = max(c.x for c in cs) - min(c.x for c in cs)
            h = max(c.y for c in cs) - min(c.y for c in cs)
            mid = Vector(((max(c.x for c in cs) + min(c.x for c in cs)) / 2, (max(c.y for c in cs) + min(c.y for c in cs)) / 2, 0))
            cam.location = cam.matrix_world @ mid
            aspect = size[0] / size[1]
            # ortho_scale spans the image's larger side
            cam.data.ortho_scale = (max(w, h * aspect) if aspect >= 1 else max(h, w / aspect)) * 1.12
        else:
            cam.data.type = "PERSP"
            cam.data.lens = lens
            target = centre.copy()
            for _ in range(3):
                dist = span * 0.3
                while dist < span * 8:
                    cam.location = target + d * dist
                    bpy.context.view_layer.update()
                    cs = [world_to_camera_view(scene, cam, p) for p in pts]
                    if all(0.04 <= c.x <= 0.96 and 0.04 <= c.y <= 0.96 for c in cs):
                        break
                    dist *= 1.04
                # re-aim so the prop sits in the middle of the frame
                ox = (min(c.x for c in cs) + max(c.x for c in cs)) / 2 - 0.5
                oy = (min(c.y for c in cs) + max(c.y for c in cs)) / 2 - 0.5
                wide = dist * cam.data.sensor_width / lens
                high = wide * size[1] / size[0]
                rot = cam.matrix_world.to_3x3()
                target += rot @ Vector((ox * wide, oy * high, 0.0))
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{PROP}: rendered {scene.render.filepath}")

    for v in VARIANTS:
        objs = variant_objects(v)
        lo, hi = bounds_of(objs)
        show({v})
        # the figure at the variant's front left corner, a metre clear of it
        # boxes and rows are seen from their door end, vehicles from the front;
        # the figure stands a metre clear of the near corner
        vehicle = v in VEHICLES
        near_y = hi.y - 1.5 if vehicle else lo.y + 1.5
        fig = figure(f"_figure_{v}", stage, lo.x - 1.2, near_y, mat=fig_mat)
        pts = points(objs) + points([fig])
        if vehicle:
            shoot(f"{v}_three_quarter", pts, (-1.0, 1.3, 0.55 if v.startswith("straddle") else 0.6))
        else:
            shoot(f"{v}_three_quarter", pts, (-1.0, -1.25, 0.6))
        if v.startswith("box_"):
            # the door end close, and the front end
            near = [p for p in points(objs) if p.y < lo.y + 2.5] + points([fig])
            shoot(f"{v}_door_end", near, (-0.9, -1.6, 0.55), lens=40)
            far = [p for p in points(objs) if p.y > hi.y - 2.5]
            shoot(f"{v}_front_end", far, (0.9, 1.6, 0.55), lens=40)
        shoot(f"{v}_side_elevation", pts, (-1.0, 0.0, 0.0), ortho=True, size=(1600, 900))
        shoot(f"{v}_plan", pts, (0.0, -0.001, 1.0), ortho=True,
              size=(1000, 1600) if hi.y - lo.y > 2 * (hi.x - lo.x) else (1200, 1200))
        bpy.data.objects.remove(fig, do_unlink=True)

    # the clearance check: the carrier straddling the 40 ft row under a
    # stand-in crane portal beam at its 15 m clear height, from the front
    show({"straddle_carrier", "stack_block_40"})
    beam = box_bm_obj("_portal_beam", mat("_portal", (0.55, 0.10, 0.10)), -8.0, 8.0, -1.0, 1.0, CRANE_PORTAL_CLEAR,
                      CRANE_PORTAL_CLEAR + 1.5)
    pts = points(variant_objects("straddle_carrier")) + points([beam])
    shoot("straddle_carrier_over_row_under_portal_front", pts, (0.0, 1.0, 0.0), ortho=True, size=(1200, 1400))
    shoot("straddle_carrier_over_row_under_portal_three_quarter", pts + points(variant_objects("stack_block_40")),
          (-1.0, 1.1, 0.55))
    bpy.data.objects.remove(beam, do_unlink=True)
    # the kit side by side: linked copies along x, never saved
    show(set())
    copies, x = [], 0.0
    lineup = ("box_20", "box_40", "box_40_hc", "box_40_reefer", "yard_tractor_loaded", "yard_tractor_chassis",
              "straddle_carrier", "stack_block_20", "stack_block_40")
    for v in lineup:
        objs = variant_objects(v)
        lo, hi = bounds_of(objs)
        x += -lo.x + 1.5
        for o in objs:
            c = o.copy()
            c.location.x += x
            c.location.y += 6.5 - hi.y if hi.y - lo.y > 20 else 0.0
            c.hide_render = False
            stage.objects.link(c)
            copies.append(c)
        x += hi.x + 1.5
    fig = figure("_figure_lineup", stage, -1.0, -2.0, mat=fig_mat)
    shoot("kit_lineup", points(copies) + points([fig]), (-0.55, 1.0, 0.45), size=(2000, 1000))
    for o in copies + [fig]:
        bpy.data.objects.remove(o, do_unlink=True)

    def stage_copies(v, offset):
        out = []
        for o in variant_objects(v):
            c = o.copy()
            c.location += Vector(offset)
            c.hide_render = False
            stage.objects.link(c)
            out.append(c)
        return out

    portal = mat("_portal", (0.55, 0.10, 0.10))
    # the 1-over-2 over the 3-high row, under the portal beam, from the front
    show({"straddle_carrier_1over2", "stack_block_40_3h"})
    beam = box_bm_obj("_portal_beam", portal, -8.0, 8.0, -1.0, 1.0, CRANE_PORTAL_CLEAR, CRANE_PORTAL_CLEAR + 1.5)
    pts = points(variant_objects("straddle_carrier_1over2")) + points([beam])
    shoot("straddle_carrier_1over2_over_3h_row_under_portal_front", pts, (0.0, 1.0, 0.0), ortho=True, size=(1200, 1400))
    # the low cab over a 4-high row, the next 4-high row LANE_CLEAR past its
    # frame on the cab's side, under the portal beam
    show({"straddle_carrier_low_cab", "stack_block_40"})
    nb = stage_copies("stack_block_40", (-(SC_OUT + LANE_CLEAR + BOX_W / 2), 0.0, 0.0))
    pts = points(variant_objects("straddle_carrier_low_cab")) + points([beam]) + points(nb)
    shoot("straddle_carrier_low_cab_beside_row_front", pts, (0.0, 1.0, 0.0), ortho=True, size=(1400, 1400))
    for o in nb + [beam]:
        bpy.data.objects.remove(o, do_unlink=True)
    # the whole kit: boxes and vehicles in front, the rows behind them
    show(set())
    front_row = ("box_20", "box_40", "box_40_ribbed", "box_40_hc", "box_40_reefer", "box_45", "gooseneck_chassis",
                 "gooseneck_chassis_loaded", "yard_tractor_chassis", "yard_tractor_loaded", "straddle_carrier",
                 "straddle_carrier_1over2", "straddle_carrier_low_cab")
    back_row = ("stack_block_20", "stack_block_20_3h", "stack_block_40", "stack_block_40_3h", "stack_block_40_hc",
                "stack_block_40_mix_b", "stack_block_40_consignment", "stack_block_40_double")
    copies = []
    for row, gap in ((front_row, 1.5), (back_row, 2.0)):
        x = 0.0
        for v in row:
            lo, hi = bounds_of(variant_objects(v))
            x += -lo.x + gap
            copies += stage_copies(v, (x, 0.0 if row is front_row else -12.0 - hi.y, 0.0))
            x += hi.x + gap
    fig = figure("_figure_lineup_all", stage, -1.0, -2.0, mat=fig_mat)
    shoot("kit_lineup_all", points(copies) + points([fig]), (-0.55, 1.0, 0.45), size=(2400, 1200))


# --- main ------------------------------------------------------------------------------

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
    export, authored, reference = (bpy.data.collections[n] for n in ("export", "authored", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"{PROP}: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    colls = {"box_40": export}
    for v in VARIANTS[1:]:
        c = bpy.data.collections.new(f"variant_{v}")
        export.children.link(c)
        colls[v] = c

    kit = BoxKit()
    box40 = build_box(kit, colls["box_40"], "box_40", L40, BOX_H, "rust_red")
    build_box(kit, colls["box_20"], "box_20", L20, BOX_H, "sky_blue")
    hc_box = build_box(kit, colls["box_40_hc"], "box_40_hc", L40, BOX_HC_H, "green")
    build_box(kit, colls["box_40_reefer"], "box_40_reefer", L40, BOX_HC_H, "white", reefer=True)
    build_row(colls["stack_block_40"], "stack_block_40", L40, ROW_SEED_40)
    build_row(colls["stack_block_20"], "stack_block_20", L20, ROW_SEED_20)
    build_straddle(colls["straddle_carrier"])
    wheels = (make_mesh("yt_tyre_single", cylinder_bm("x", TYRE_D / 2, TYRE_W / 2, 12), [M("tyre")]),
              make_mesh("yt_tyre_dual", cylinder_bm("x", TYRE_D / 2, DUAL_W / 2, 12), [M("tyre")]),
              make_mesh("yt_hub", cylinder_bm("x", YT_HUB_R, 0.035, 8), [M("hub")]))
    rig = colls["yard_tractor_chassis"]
    build_tractor(rig, "yard_tractor_chassis", wheels)
    build_chassis(rig, "yard_tractor_chassis", wheels)
    # the loaded rig: every part a linked copy of the empty rig's and the box_40's
    loaded = colls["yard_tractor_loaded"]
    for src in list(rig.objects):
        dup = src.copy()
        dup.name = src.name.replace("yard_tractor_chassis", "yard_tractor_loaded")
        dup["kyt_variant"] = "yard_tractor_loaded"
        loaded.objects.link(dup)
    for src in box40:
        dup = src.copy()
        dup.name = "yard_tractor_loaded_" + src.name
        dup["kyt_variant"] = "yard_tractor_loaded"
        dup.location = src.location + Vector((0.0, BOX_ON_CHASSIS_Y + YT_SHIFT, DECK_Z))
        loaded.objects.link(dup)
    # the further variants: none of them touches the nine above
    build_ribbed(colls["box_40_ribbed"], "box_40_ribbed", box40)
    build_box_45(kit, colls["box_45"], "box_45")
    build_row(colls["stack_block_40_hc"], "stack_block_40_hc", L40, ROW_SEED_HC, h=BOX_HC_H, door_h=DOOR_OPEN_H_HC)
    build_row(colls["stack_block_40_3h"], "stack_block_40_3h", L40, ROW_SEED_40, tiers=ROW_TIERS_LOW)
    build_row(colls["stack_block_20_3h"], "stack_block_20_3h", L20, ROW_SEED_20, tiers=ROW_TIERS_LOW)
    build_row(colls["stack_block_40_double"], "stack_block_40_double", L40, ROW_SEED_DOUBLE, rows=2)
    build_row(colls["stack_block_40_mix_b"], "stack_block_40_mix_b", L40, ROW_SEED_MIX_B)
    build_row(colls["stack_block_40_consignment"], "stack_block_40_consignment", L40, ROW_SEED_CONSIGN,
              mix=consignment_colours)
    build_gooseneck(colls["gooseneck_chassis"], "gooseneck_chassis")
    build_gooseneck(colls["gooseneck_chassis_loaded"], "gooseneck_chassis_loaded", hc_box)
    build_straddle_1over2(colls["straddle_carrier_1over2"])
    build_straddle_low_cab(colls["straddle_carrier_low_cab"])

    bpy.context.view_layer.update()
    bounds = {v: report(v) for v in VARIANTS}
    carrier_margins()
    build_reference(reference, bounds)
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1])


main()
