"""The bay ferry, blocked out (2026-10-03): the one boat between the beach
town's landing at the pier head and the city's ferry terminal across the bay
(about 1.9 km; `world_terrain_reference_ferry.py`, "Ferry to the city (A)").
Christina's words: "we need to add boats to our props, we have a few
different scenarios"; the bay ferry is one of the four she chose.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/bay_ferry.blend --python tools/blender/bay_ferry.py -- \
        [--replace] [--save] [--render <folder> [--only <variant>,...,lineup]]

Builds, from scratch every run, two variants of the ferry, both standing at
the origin, each marked `kyt_variant` so Send writes each as a prop of its
own (`send.py`):

- **catamaran**, in `export`: a late-1990s California high-speed aluminium
  passenger catamaran, 38.0 x 10.6 m over the deck (38.1 x 10.8 m over its
  black rubbing strake). Two slender demi-hulls under a bridging
  deck with 1.15 m of clear water under it; a main cabin and an upper cabin,
  each with one continuous window band round its sides and raked front; the
  open upper deck aft over the main cabin with five rows of benches; the
  wheelhouse on top forward with a band of windows all round, a pole mast
  with its light and a radar on a pedestal of its own (a scanner across a
  pole read as a cross); rails round the open aft main deck and round the
  foredeck and both bow lobes, the last 2 m of each bow left open; a stair
  from the open aft main deck up to the upper deck; boarding doors midships
  on both sides. White, with one colour band along the hulls
  (`bay_ferry_band`); no names or logos.
- **monohull**, in `export/variant_monohull` with its eye shut: an older
  conventional monohull passenger ferry of the kind bay services ran from
  the 1970s, 36.0 x 9.0 m, of similar capacity. A round-bilge hull with a
  raked, flared stem, the sheer rising 1.3 m to the bow, a transom stern and
  a skeg and rudder below; rows of single windows (not bands) in a
  round-fronted main cabin and upper cabin; a square pilothouse with a sun
  visor; a raked buff stack with a black top; a pole mast (no yard) and a
  radar on a pedestal; a high bulwark round the foredeck, ramping up from
  low at its aft ends; benches along the open upper deck's rails and one
  back to back on the centreline. Green hull over red bottom paint, a white
  sheer strake, a green deck. It shares no mesh with the catamaran, only
  four generic stand-in materials (`bay_ferry_white`, `_glass`, `_bottom`,
  `_mast`); its hull, deck, doors, benches and stack have their own.

Four more (3 October 2026, Christina: "build all the offered variants"),
each in `export/variant_<name>` with its eye shut:

- **catamaran_b**: the catamaran in another livery: a navy hull and deck
  sides, a coral band that sweeps up from 0.25-0.60 m at the stern to just
  under the deck's edge at the bow, sand benches, on its own materials
  (`bay_ferry_catamaran_b_<surface>`). Its hulls, deck and benches are its own
  meshes; every other part is a linked copy of the catamaran's.
- **catamaran_waterjets**: the catamaran with a waterjet unit under each
  transom (an octagonal housing, full width to 0.60 m aft of the transom
  and tapering to the nozzle at 1.15 m, a reversing bucket over its mouth to
  1.45 m: real length for the class); every other part a linked copy of the
  catamaran's.
- **catamaran_small**: a late-1990s 25 x 8 m catamaran of the US
  small-passenger class (up to 150 passengers): one enclosed cabin of about
  110 seats, an open top deck of 40 with the wheelhouse on it forward; built
  by the same code as the catamaran from its own numbers (S_), in the same
  livery.
- **double_ended**: an older double-ended ferry like the old San
  Diego-Coronado and Puget Sound boats, 36 x 10 m: the same at both ends,
  round-ended cabins, a pilothouse at each end of the upper cabin's roof, an
  upright stack between them, a stair, a bulwark, benches and a skeg with
  screw and rudder at each end. Everything at the -Y end is a linked copy of
  the +Y end's, turned 180 degrees about the origin; black hull, cream stack,
  red-brown decks, on its own materials.

All six board at 1.80 m.

Both main decks are at the boarding doors 1.80 m over the waterline, the
beach-town landing's height, so either boards level at the pier head.

Into the locked `reference` collection go the `waterline` marker (an outline
at z = 0, the sea's surface), each variant's length x beam outline at the
waterline, the 17 x 46 m outline of the placeholder this replaces
(`far_shore_city_relocation.blend`, `bay_ferry_hull`), an outline of the
landing's deck at 1.80 m alongside the starboard side, and a 1.7 m figure on
the catamaran's aft deck. Everything the tool makes carries `kyt_bay_ferry`,
so a rerun removes and rebuilds its own work and keeps anything of hers;
`export` holding anything untagged refuses without `--replace`.

**Frame.** Real metres, Z up, one unit a metre. z = 0 is the waterline; the
hulls go below it by their draft and are modelled as closed forms down to the
keel. The bow is toward +Y (the glTF export turns Blender +Y into Godot -Z,
Godot's forward for `Basis.looking_at`, as `ride_vehicle.gd` orients its
trains); starboard is +X. The origin is on the centreline, midships, at the
waterline.

**Contract.** Scenery block-out: closed shells, silhouette first, no
interiors. Every window, the wheelhouse's and pilothouse's included, is a dark
slab set proud of its wall (3 cm out, lapping 2 cm in), not a hole; every door
is a closed slab the same way. Every part is `kyt_collision = none` this
pass: collision and boarding are decided when the ferry is placed and
scheduled. No two shapes share a plane: a part that meets another laps into
it or stands proud of it, and each kind of part laps by its own depth (cabins
2 cm, rails 3 cm, the monohull's bulwark and fantail rail 10 cm, stair 2.5 cm,
benches 3.5 cm, bitts 4 cm) so their buried faces never meet in one plane
either.

**How it is built.** Each hull is lofted through stations along Y from a
half-section template (keel, bilge, waterline, band or sheer, deck edge),
mirrored to a closed ring; the template narrows to the bow on a parabola
from an entry station, and every point ahead of the raked stem line collapses
onto it, so the stem is a true line and the bow a point. Material zones run
between template levels, so the band, the bottom paint and the sheer strake
are faces of the hull, not parts on it. Cabins are lofted from a plan outline
whose front leans (catamaran) or stands upright on a faceted arc
(monohull); window bands are ribbons along the outline at their heights,
offset out and in by the outline's mitres so they stay parallel to the walls;
rails and bulwarks are ribbons along the deck edge. Repeated pieces (the
second demi-hull, windows, doors, benches, bitts, stair side panels) are
linked copies of one mesh, so reshaping one reshapes all. Stand-in materials
by surface, `bay_ferry_<surface>` and `bay_ferry_monohull_<surface>`; window
mullions, non-skid, hull plating and the lettering a real ferry carries are
painting or left out.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_bay_ferry"
PROP = "bay_ferry"
VARIANTS = ("catamaran", "monohull", "catamaran_b", "catamaran_waterjets", "catamaran_small", "double_ended")

# --- read: the landing, the route, the placeholder --------------------------
LANDING = 1.80     # read: the beach-town pier, "the built ferry landing kept at 1.8 m over the sea ... where the bay ferry from the city ties up and boards level" (beach-town-plan.html, decision 2)
MAIN_DECK = LANDING  # chosen: each variant's main deck at its boarding doors is the landing's height
PLACEHOLDER_HULL = (17.0, 46.0)   # read: far_shore_city_relocation.blend, bay_ferry_hull 17 x 46 m, 0.15 m below the sea to 4.35 m over it
PLACEHOLDER_TOP = 8.5             # read: bay_ferry_cabin (14 x 28 m) tops out 8.5 m over the sea

# --- construction rules both variants keep (chosen) -----------------------------
SLAB_OUT, SLAB_IN = 0.03, 0.02   # a window slab or band stands 3 cm proud of its wall and laps 2 cm into it
SLAB_T = SLAB_OUT + SLAB_IN
DOOR_T = 0.06                    # a door slab: 4 cm proud, a centimetre past the windows, so they never share a face
DOOR_SINK = 0.01                 # a door slab's foot sits a centimetre into the deck
LAP_CABIN = 0.02                 # how far each kind of part sinks into the deck under it; each kind its own,
LAP_RAIL = 0.03                  # so their buried faces never meet in one plane either
LAP_STAIR = 0.025
LAP_BENCH = 0.035
LAP_BITT = 0.04
RAIL_INSET = 0.03                # a rail's outer face stands this far in from the deck edge
BAND_END = 0.4                   # a side window band stops this far short of a cabin's aft wall
STAIR_GAP = 0.13                 # the upper deck's rail stops this far either side of the stair
STAIR_SOFFIT = 0.30              # the stair's underside, below its top tread
STAIR_PANEL = (0.35, 0.95, 0.06) # its side panels: below and above the nosing line, thickness
BENCH_BACK = 0.08                # a bench's back slab
LIGHT_SINK = 0.04                # a masthead light sinks this far over the mast's top
RADAR_SINK = 0.03                # a scanner sinks this far into its pedestal

# --- the catamaran ------------------------------------------------------------
# Type: a late-1990s US bay high-speed passenger catamaran (the 1996-99
# Nichols Bros / Dakota Creek / Incat Crowther generation on San Francisco Bay
# and Puget Sound: 33-43 m, 10-12 m beam, 250-400 seats, waterjets, two
# passenger decks); the task asked for about 35-40 x 10-11 m.
C_STERN_Y = -18.95     # chosen: the demi-hulls' transoms
C_AFT_Y = -19.0        # the bridging deck's aft edge, 5 cm proud of the transoms
C_TIP_Y = 19.0         # the deck's bow points: length overall 38.0 m (chosen in the task's 35-40)
C_HALF = 5.30          # the deck edge: beam 10.6 m (chosen in the task's 10-11)
C_HULL_X = 3.90        # demi-hull centrelines 7.8 m apart (chosen: about 0.74 of the beam, as the type)
C_HULL_HW = 1.30       # demi-hull half-beam: a 2.6 m hull, about 1/14 of its length (chosen, as the type)
C_KEEL = -1.40         # the draft, nothing below it (chosen: 1.2-1.6 m is the type's on waterjets)
C_KEEL_STERN = -1.20   # the keel rises 20 cm to the transom (chosen)
C_KEEL_FLAT_AFT = -6.0 # where that rise begins (chosen)
C_WET_DECK = 1.15      # the bridging deck's underside: clear water under it (chosen: 1.0-1.5 m on sheltered-water cats)
C_HULL_TOP = 1.45      # the demi-hulls end inside the bridging deck
C_ENTRY_Y = 5.0        # the demi-hulls begin to narrow to the bow (chosen)
C_STEM = ((-1.40, 13.9), (-1.15, 15.9), (-0.65, 17.1), (0.0, 17.9), (1.45, 18.9))   # (z, y): the raked stem (chosen)
C_TUNNEL_Y = 15.2      # the bridging deck's forward edge between the bows (chosen)
C_LOBE_OVER = 0.10     # the deck's edge stands this far out from the hull below it, round the bows
C_BAND = (0.45, 0.95)  # the one colour band along the hulls (chosen)
C_BAND_LEVELS = (5, 6)  # which levels of the half-section template below are the band's edges
C_STATIONS = (-18.95, -12.0, -6.0, 0.0, 5.0, 8.0, 10.5, 12.5, 14.0, 15.2, 16.2, 17.0, 17.7, 18.3, 18.9)
# half-section template from the demi-hull's centre: (half-width, z), keel first
C_LEVELS = ((0.00, -1.40), (0.55, -1.15), (1.15, -0.65), (1.30, -0.15), (1.30, 0.0),
            (1.30, C_BAND[0]), (1.30, C_BAND[1]), (1.30, C_HULL_TOP))
C_ZONES = ("bottom", "bottom", "bottom", "bottom", "white", "band", "white")   # between consecutive levels
C_FENDER = (1.30, 1.62, 0.12, 0.03)   # the black rubbing strake round the stern and sides: z from, z to, how far it stands out, how far it laps in (chosen)
C_FENDER_TO = 16.2              # it runs forward along each bow lobe to here
C_RAIL_FROM = 8.2               # the foredeck rail: from beside the cabin's front ...
C_RAIL_NOSE = 17.0              # ... round each lobe to here, the last 2 m of each bow left open (crew only)
# main cabin: walls 25 cm in from the deck edge, an open aft deck behind it,
# a front that leans back 0.8 m over its height and chamfers to the sides
C_MAIN_HW = 5.05
C_MAIN_AFT = -12.6     # 6.4 m of open aft main deck (boarding overflow, bikes, the stair up) (chosen)
C_MAIN_SIDE_FWD = 7.4
C_MAIN_FRONT = 10.0
C_MAIN_FRONT_HW = 3.4
C_MAIN_TOP = 4.45      # the walls end inside the upper deck slab
C_MAIN_RAKE = 0.8
C_UPPER_DECK = 4.60    # 2.8 m main deck to upper deck (chosen: 2.4 m headroom under a 0.4 m deck)
C_SLAB_T = 0.20
C_SLAB_OVER = 0.15
C_MAIN_WIN = (2.55, 3.85)        # sill 0.75 and head 2.05 over the floor (chosen)
C_DOOR_Y = (-1.6, -0.2)          # the boarding doors, midships both sides, 1.4 m double doors (chosen)
C_DOOR_H = 2.0
C_DOOR_GAP = 0.40                # the window band stops this far short of a door
C_MAIN_AFT_WIN = (1.2, 4.4)      # the aft wall's windows, each side of its door (x)
# upper cabin: 45 cm in from the main cabin, open deck aft of it
C_UP_HW = 4.60
C_UP_AFT = -3.0                  # 9.7 m of open upper deck aft (chosen)
C_UP_SIDE_FWD = 5.6
C_UP_FRONT = 7.8
C_UP_FRONT_HW = 3.0
C_UP_TOP = 7.05
C_UP_RAKE = 0.7
C_UP_ROOF = (7.00, 7.18)
C_UP_ROOF_OVER = 0.12
C_UP_WIN = (5.35, 6.55)
C_UP_AFT_WIN = (1.1, 4.0)
# the wheelhouse on top forward, wide for docking sight lines, its front
# leaning out 0.35 m at the top (as the type's, against glare)
C_WH_HW = 3.2
C_WH_AFT = 2.0
C_WH_SIDE_FWD = 4.6
C_WH_FRONT = 5.6
C_WH_FRONT_HW = 2.4
C_WH_BASE = 7.16
C_WH_TOP = 9.30
C_WH_LEAN = 0.35
C_WH_WIN = (8.05, 9.05)
C_WH_ROOF = (9.25, 9.45)
C_WH_ROOF_OVER = 0.20
C_MAST_AT = (0.0, 2.6)
C_MAST = (9.43, 11.6, 0.30, 0.16)   # base, top, base width, top width (chosen); a plain pole, the light on top
C_RADAR_AT = (0.0, 4.4)             # the radar on its own pedestal on the wheelhouse roof, forward of the mast
C_RADAR = (0.50, 0.42, 2.2, 0.30, 0.12)   # pedestal width, pedestal height, scanner length, depth, thickness (chosen)
C_LIGHT = 0.20                      # the masthead light box
C_RAIL_H = 1.05                     # rails and bulwark panels over their deck (chosen: 1.0-1.1 m passenger rails)
C_RAIL_T = 0.05
C_RAIL_AFT_RUN = 0.3                # the aft deck's rail runs on this far forward past the main cabin's aft wall
C_STAIR_HW = 0.62
C_STAIR_RISERS = 14                 # 2.8 m in 14 risers of 0.20 (chosen)
C_STAIR_GOING = 0.22
C_BENCH = (3.2, 0.45, 0.45, 0.90)   # length, depth, seat height, back top (chosen)
C_BENCH_X = 2.45
C_BENCH_ROWS = (-11.8, -10.2, -8.6, -7.0, -5.4)
C_BITTS = ((3.9, 12.5), (-3.9, 12.5), (4.4, -18.2), (-4.4, -18.2))
C_BITT = (0.15, 0.42)            # radius, height over the deck (chosen)

# --- the monohull -------------------------------------------------------------
# Type: an older bay passenger ferry of the 1970s generation (steel or
# aluminium monohulls of 30-50 m, 300-700 seats, twin screws, two enclosed
# decks under a pilothouse and a stack); sized here to carry about the
# catamaran's load.
M_STERN_Y = -17.6      # the transom
M_STEM_Y = 18.4        # the stem's head: length overall 36.0 m (chosen)
M_HW = 4.50            # beam 9.0 m (chosen: about 1/4 of the length, as the type)
M_KEEL = -1.85         # the canoe body's keel (chosen)
M_TRANSOM_BOTTOM = -0.35   # the run rises to an immersed transom (chosen)
M_KEEL_FLAT_AFT = -5.0
M_SKEG = -2.10         # the skeg's bottom: the draft (chosen: 2.0-2.4 m for the type)
M_SKEG_PROFILE = ((-15.0, -0.60), (-15.0, M_SKEG), (-3.5, M_SKEG), (-1.0, -1.60))   # (y, z), its top buried in the run (chosen)
M_SKEG_T = 0.30
M_RUDDER = (0.12, -16.3, -15.3, -1.95, -0.50)   # thickness, y from, y to, z from, z to: aft of the skeg, its head in the run (chosen)
M_SHEER_RISE = 1.30    # the sheer rises from the main deck at midships to 3.10 m at the stem (chosen)
M_ENTRY_Y = 2.0
M_NARROW_FROM = -8.0   # the hull narrows 6% to the transom from here (chosen)
M_NARROW = 0.06
M_STEM = ((-1.85, 9.5), (-1.6, 12.6), (-1.0, 14.8), (0.0, 16.4), (1.5, 17.4), (3.10, 18.4))   # (z, y): raked, flared (chosen)
M_STATIONS = (-17.6, -14.5, -10.5, -5.0, 0.0, 4.0, 7.5, 10.0, 12.0, 13.6, 14.8, 15.8, 16.6, 17.3, 17.9, 18.4)
M_SHEER_STRAKE = 0.35  # the white strake under the deck edge (chosen)
# half-section template: (fraction of M_HW, how z is set, value); "keel" is a
# fraction of the keel's depth at the station, "wl" the waterline, "sheer" an
# offset from the deck edge
M_LEVELS = ((0.00, "keel", 1.00), (0.30, "keel", 0.97), (0.70, "keel", 0.80), (0.90, "keel", 0.50),
            (0.98, "keel", 0.20), (1.00, "wl", 0.0), (1.00, "sheer", -M_SHEER_STRAKE), (1.00, "sheer", 0.0))
M_ZONES = ("bottom", "bottom", "bottom", "bottom", "bottom", "hull", "white")
M_MAIN_HW = 4.20       # main cabin, 30 cm side decks
M_MAIN_AFT = -10.5     # 7.1 m of open fantail (chosen)
M_MAIN_ARC = (3.5, 4.2)   # its round front: the arc's centre y and radius (a semicircle in plan)
M_MAIN_TOP = 4.30
M_UPPER_DECK = 4.45    # 2.65 m deck to deck (chosen)
M_SLAB_T = 0.20
M_SLAB_OVER = 0.15
M_FACET = 22.5         # degrees: the round fronts are faceted at 22.5 degree stations
M_WIN = (1.00, 0.95)   # main deck windows, width x height (chosen: 1970s single windows)
M_WIN_Z = (2.65, 3.60)
M_WIN_Y = (-9.6, -8.05, -6.5, -4.95, -3.4, 1.15, 2.7)
M_DOOR_Y = (-1.2, 0.0)  # midships boarding doors, 1.2 m (chosen)
M_DOOR_H = 2.0
M_AFT_WIN_X = (-3.1, -1.7, 1.7, 3.1)
M_UP_HW = 3.50
M_UP_AFT = -2.5        # 8.15 m of open upper deck aft (chosen)
M_UP_ARC = (1.8, 3.5)
M_UP_TOP = 6.70
M_UP_ROOF = (6.65, 6.85)
M_UP_ROOF_OVER = 0.15
M_UP_WIN = (0.90, 0.85)
M_UP_WIN_Z = (5.25, 6.10)
M_UP_WIN_Y = (-1.7, -0.2, 1.3)
M_UP_AFT_WIN_X = (-2.2, 2.2)
M_PH = (2.0, 0.4, 3.4)   # pilothouse: half-width, aft y, front y (chosen)
M_PH_BASE = 6.83
M_PH_TOP = 8.85
M_PH_WIN = (0.80, 0.85)
M_PH_WIN_Z = (7.75, 8.60)
M_PH_FRONT_WIN_X = (-1.35, -0.45, 0.45, 1.35)
M_PH_SIDE_WIN_Y = (1.2, 2.6)
M_PH_AFT_WIN_X = (-1.1, 1.1)
M_PH_ROOF = (8.80, 8.98)
M_PH_VISOR = 0.45        # the roof runs on forward as a sun visor (chosen)
M_PH_ROOF_OVER = (0.25, 0.20)   # and overhangs the sides and the back by these
M_STACK_AT = (0.0, -1.15)
M_STACK = (0.70, 1.20)   # half-axes of its oval plan (chosen)
M_STACK_Z = (6.83, 9.25, 9.70)   # base, black top band, top (chosen)
M_STACK_RAKE = 0.55      # the top stands this far aft of the base
M_MAST_AT = (0.0, 1.0)
M_MAST = (8.96, 11.6, 0.10, 0.06)   # base, top, base radius, top radius (chosen); a plain pole, no yard, the light on top
M_RADAR_AT = (0.0, 2.7)             # the radar on its own pedestal on the pilothouse roof, forward of the mast
M_RADAR = (0.40, 0.34, 1.6, 0.24, 0.12)   # pedestal width, pedestal height, scanner length, depth, thickness (chosen)
M_LIGHT = 0.18
M_BULWARK_FROM = 1.0     # the foredeck bulwark starts here, low ...
M_BULWARK_FULL = 4.0     # ... and is full height from here to the stem
M_BULWARK_FOOT = 0.25    # its height at the start (chosen)
M_BULWARK_H = 1.00
M_BULWARK_T = 0.08
M_EDGE_INSET = 0.04      # the bulwark and the fantail's rail stand this far in from the deck edge
M_EDGE_SINK = 0.10       # and sink this far into the deck, which slopes with the sheer
M_STEM_INSET = 0.10      # the bulwark's point stands this far aft of the stem's head
M_STAIR_HW = 0.55
M_STAIR_RISERS = 13      # 2.65 m in 13 risers (chosen)
M_STAIR_GOING = 0.23
M_BENCH = (2.8, 0.45, 0.45, 0.90)
M_SIDE_BENCH_Y = (-8.8, -5.6)
M_CENTRE_BENCH = (0.0, -5.1, 3.2, 0.90)   # x, y, length, depth: back to back, facing out (chosen)
M_BENCH_CLEAR = 0.05     # a side bench's back stands this far off the rail
M_FANTAIL_RAIL_T = 0.06

# --- catamaran_b: the catamaran in another livery (chosen) ---------------------
# Its hulls, its deck's sides and its benches are its own meshes on its own
# materials (`bay_ferry_catamaran_b_<surface>`); every other part is a linked
# copy of the catamaran's.
B_BAND_AFT = (0.25, 0.60)    # the band from the stern ...
B_BAND_BOW = (0.72, 1.10)    # ... sweeps up to this at the stem's head, just under the deck's edge
B_SWEEP_FROM = -2.0          # where the sweep begins; it eases in and out (smoothstep) to the stem

# --- catamaran_waterjets: the catamaran with its jets (chosen) ------------------
# One jet unit per hull on its centreline (as the type's twin-engine boats of
# this size), the catamaran's every other part a linked copy.
J_Z = -0.40                  # the jet's axis: about half the unit under water
# The housing in plan along its axis, (distance aft of the transom, radius):
# from 0.30 m inside the hull, full width (0.92 m across, the pump and its
# stator bowl) to 0.60 m aft, then tapering to the steering nozzle 1.15 m aft
# of the transom. Chosen for the class: a two-jet 35-40 m fast ferry runs
# units of about 0.6-0.7 m impeller, whose nozzle and reversing bucket stand
# 1.0-1.5 m past the transom; this takes the upper middle of that range,
# because the bucket hangs past the nozzle's mouth.
J_RINGS = ((-0.30, 0.46), (0.60, 0.46), (1.15, 0.28))
J_BUCKET = (0.44, 1.00, 1.45, -0.86, 0.04)   # reversing bucket: half-width, from and to aft of the transom, z from, z to

# --- catamaran_small: a late-1990s small passenger catamaran (chosen) -----------
# Type: the US small-passenger-vessel class of the time (under 100 tons, up
# to 150 passengers): 23-26 m catamarans with one enclosed passenger cabin,
# an open top deck and the wheelhouse on it. About 110 seats inside and 40 on
# top. Same construction and livery as the catamaran.
S_STERN_Y = -12.45
S_AFT_Y = -12.5
S_TIP_Y = 12.5               # length overall 25.0 m (chosen)
S_HALF = 4.0                 # beam 8.0 m (chosen)
S_HULL_X = 2.95              # hulls 1.9 m wide at 5.9 m centres (chosen)
S_KEEL = -1.20               # draft (chosen)
S_KEEL_STERN = -1.05
S_KEEL_FLAT_AFT = -4.0
S_WET_DECK = 1.05            # clear water under the deck (chosen)
S_HULL_TOP = 1.40
S_ENTRY_Y = 3.0
S_STEM = ((-1.20, 8.6), (-0.98, 10.1), (-0.55, 11.2), (0.0, 11.8), (1.40, 12.4))   # (z, y)
S_TUNNEL_Y = 10.0
S_BAND = (0.40, 0.80)
S_STATIONS = (-12.45, -8.0, -4.0, 0.0, 3.0, 5.0, 6.8, 8.2, 9.3, 10.0, 10.7, 11.3, 11.8, 12.4)
S_LEVELS = ((0.00, -1.20), (0.42, -0.98), (0.85, -0.55), (0.95, -0.12), (0.95, 0.0),
            (0.95, S_BAND[0]), (0.95, S_BAND[1]), (0.95, S_HULL_TOP))
S_FENDER = (1.25, 1.55, 0.10, 0.03)
S_FENDER_TO = 10.7
S_RAIL_FROM = 4.0
S_RAIL_NOSE = 11.3
S_MAIN = (3.75, -7.0, 3.6, 5.6, 2.4, 0.6)    # main cabin: half-width, aft wall, side's end, front, front half-width, rake
S_MAIN_TOP = 4.30
S_UPPER_DECK = 4.45          # the open top deck, 2.65 m over the main deck (chosen)
S_MAIN_WIN = (2.50, 3.70)
S_DOOR_Y = (-1.4, -0.2)      # 1.2 m boarding doors midships (chosen)
S_DOOR_H = 2.0
S_MAIN_AFT_WIN = (1.0, 3.25)
S_WH = (2.0, 0.6, 2.6, 3.6, 1.4, -0.25)   # wheelhouse on the top deck: as S_MAIN, its front leaning out 0.25 m
S_WH_BASE = S_UPPER_DECK - 0.02
S_WH_TOP = 6.55
S_WH_WIN = (5.35, 6.25)
S_WH_ROOF = (6.50, 6.68)
S_WH_ROOF_OVER = 0.18
S_MAST_AT = (0.0, 1.2)
S_MAST = (6.66, 8.4, 0.22, 0.12)
S_LIGHT = 0.16
S_RADAR_AT = (0.0, 2.7)
S_RADAR = (0.40, 0.32, 1.6, 0.24, 0.10)
S_STAIR = (0.55, 13, 0.22)   # half-width, risers, going
S_BENCH = (2.5, 0.45, 0.45, 0.90)
S_BENCH_X = 1.85
S_BENCH_ROWS = (-6.3, -4.9, -3.5, -2.1, -0.7)
S_BITTS = ((2.95, 7.6), (-2.95, 7.6), (3.3, -11.9), (-3.3, -11.9))
S_BITT = (0.12, 0.36)
S_FIGURE = (2.2, -11.0)

# --- double_ended: the older double-ended ferry (chosen) ------------------------
# Type: the old double-ended bay ferries (San Diego-Coronado, Puget Sound):
# the same at both ends, a pilothouse at each end, the stack between them,
# a skeg with screw and rudder at each end. Passenger-only here, about the
# monohull's capacity. Everything at the -Y end is the +Y end's linked copy,
# turned 180 degrees about the origin.
D_HALF_L = 18.0              # length overall 36.0 m, the monohull's (chosen)
D_HW = 5.0                   # beam 10.0 m: double-enders run beamier (chosen)
D_KEEL = -1.90
D_SHEER_RISE = 0.60          # the sheer rises from 1.80 at midships to 2.40 at each end (chosen)
D_ENTRY_Y = 6.0
D_STEM = ((-1.90, 11.5), (-1.5, 14.5), (-0.8, 16.2), (0.0, 17.0), (1.2, 17.6), (2.40, 18.0))   # (z, |y|): each end's raked, overhanging profile
D_STATIONS_HALF = (0.0, 4.0, 6.0, 8.5, 10.5, 12.0, 13.3, 14.4, 15.4, 16.2, 16.9, 17.5, 18.0)
D_LEVELS = ((0.00, "keel", 1.00), (0.35, "keel", 0.97), (0.75, "keel", 0.80), (0.92, "keel", 0.50),
            (0.985, "keel", 0.20), (1.00, "wl", 0.0), (1.00, "sheer", -M_SHEER_STRAKE), (1.00, "sheer", 0.0))
D_ZONES = M_ZONES
D_SKEG = ((11.0, -1.70), (11.0, -2.20), (13.8, -2.20), (15.4, -1.05))   # (|y|, z) at each end; its foot is the draft, 2.20
D_SKEG_T = 0.30
D_FACET = 20.0               # degrees: 9 facets round each cabin end, so a flat one faces each end
D_MAIN = (4.70, 8.0)         # main cabin: half-width, where its ends begin; each end a half-round of that radius
D_MAIN_TOP = 4.30
D_UPPER_DECK = 4.45
D_WIN = (1.00, 0.95)
D_WIN_Z = (2.65, 3.60)
D_WIN_Y = (1.6, 3.1, 4.6, 6.1, 7.4)        # each side, mirrored fore and aft
D_END_FACETS = (1, 2, 3, 5, 6, 7)          # window facets round each end; the middle one has the door
D_DOOR_Y = (-0.6, 0.6)       # boarding doors midships, 1.2 m (chosen)
D_DOOR_H = 2.0
D_UP = (3.60, 3.0)           # upper cabin: half-width, where its ends begin
D_UP_TOP = 6.70
D_UP_ROOF = (6.65, 6.85)
D_UP_ROOF_OVER = 0.15
D_UP_WIN = (0.90, 0.85)
D_UP_WIN_Z = (5.25, 6.10)
D_UP_WIN_Y = (0.7, 2.1)
D_UP_DOOR_W = 1.0
D_PH = (1.8, 3.6, 6.0)       # each pilothouse: half-width, inner wall, outer wall (|y|)
D_PH_BASE = 6.83
D_PH_TOP = 8.75
D_PH_ROOF = (8.70, 8.88)
D_PH_VISOR = 0.40
D_PH_ROOF_OVER = (0.22, 0.18)
D_PH_WIN = (0.80, 0.85)
D_PH_WIN_Z = (7.70, 8.55)
D_PH_FRONT_WIN_X = (-1.0, 0.0, 1.0)
D_PH_SIDE_WIN_Y = (4.3, 5.4)
D_PH_BACK_WIN_X = (-0.8, 0.8)
D_STACK = (0.75, 1.00)       # the stack amidships, upright: half-axes
D_STACK_Z = (6.83, 9.10, 9.55)
D_MAST_AT = (0.0, 4.2)       # on each pilothouse
D_MAST = (8.86, 11.0, 0.09, 0.055)
D_LIGHT = 0.16
D_RADAR_AT = (0.0, 5.4)
D_RADAR = (0.36, 0.30, 1.4, 0.22, 0.10)
D_BULWARK_FROM = 11.0        # each end's bulwark, as the monohull's foredeck's
D_BULWARK_FULL = 13.0
D_STAIR = (0.55, 11, 0.22)   # a stair at each end from the end deck up to the upper deck
D_BENCH = (2.4, 0.45, 0.45, 0.90)
D_BENCH_X = 1.9
D_BENCH_ROWS = (8.0, 9.4, 10.8)   # |y|: three rows on each open end of the upper deck, facing the end
D_FIGURE = (1.6, -14.0)


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {
    f"{PROP}_white": srgb("f2f2ec"),       # hulls and superstructure
    f"{PROP}_band": srgb("0f7f9a"),        # the catamaran's one colour band
    f"{PROP}_glass": srgb("1d2630"),       # window slabs
    f"{PROP}_door": srgb("3a4652"),        # the catamaran's glazed doors
    f"{PROP}_deck": srgb("8b908c"),        # non-skid grey
    f"{PROP}_bottom": srgb("7a2a24"),      # bottom paint below the waterline
    f"{PROP}_fender": srgb("1c1c1c"),      # rubbing strakes
    f"{PROP}_seats": srgb("5a6f86"),       # the catamaran's benches
    f"{PROP}_mast": srgb("c9ccc9"),        # masts, radar, lights
    f"{PROP}_monohull_hull": srgb("1f4a3a"),       # the older ferry's green hull
    f"{PROP}_monohull_deck": srgb("6a7d6c"),       # green deck paint
    f"{PROP}_monohull_door": srgb("2e5a46"),
    f"{PROP}_monohull_seats": srgb("a0652e"),      # varnished wood
    f"{PROP}_monohull_stack": srgb("d9b87a"),      # buff
    f"{PROP}_monohull_stack_top": srgb("151515"),  # black top
    f"{PROP}_catamaran_b_hull": srgb("16324f"),    # navy hull and deck sides
    f"{PROP}_catamaran_b_band": srgb("d94a38"),    # coral band, swept up at the bow
    f"{PROP}_catamaran_b_seats": srgb("d8b46a"),   # sand benches
    f"{PROP}_jet": srgb("9aa1a6"),                 # waterjet housings
    f"{PROP}_double_ended_hull": srgb("1c1d20"),   # black hull
    f"{PROP}_double_ended_deck": srgb("7a4636"),   # red-brown deck paint
    f"{PROP}_double_ended_door": srgb("6b4a2e"),   # varnished doors
    f"{PROP}_double_ended_seats": srgb("8a5a2b"),  # varnished benches
    f"{PROP}_double_ended_stack": srgb("e9dfc4"),  # cream stack
    f"{PROP}_double_ended_stack_top": srgb("17181a"),
}


def material(name, colour=None):
    """A stand-in material by name; a rerun resets the builder's colours."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour or COLOURS[name]
        bsdf.inputs["Roughness"].default_value = 0.6
    elif name in COLOURS and mat.node_tree is not None:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = COLOURS[name]
    return mat


def mats():
    return {k[len(PROP) + 1:]: material(k) for k in COLOURS}


# --- building blocks -------------------------------------------------------

def finish(name, bm, coll, mat_list, variant, smooth_angle=None, mesh_only=False):
    """A bmesh into a mesh (and an object in `coll`), tagged. Flat shaded, or
    smooth with edges sharper than `smooth_angle` degrees kept sharp."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = smooth_angle is not None
    if smooth_angle is not None:
        limit = math.radians(smooth_angle)
        for e in bm.edges:
            if not e.is_manifold or e.calc_face_angle(math.pi) > limit:
                e.smooth = False
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for m in mat_list:
        mesh.materials.append(m)
    mesh[TAG] = True
    if mesh_only:
        return mesh
    return place(name, mesh, coll, variant)


def place(name, mesh, coll, variant, loc=(0.0, 0.0, 0.0), rot_z=0.0):
    """An object of `mesh` (shared with any other placed from it)."""
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = (0.0, 0.0, rot_z)
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    obj["kyt_collision"] = "none"
    if variant:
        obj["kyt_variant"] = variant
    coll.objects.link(obj)
    return obj


def prism_bm(poly, axis, lo, hi):
    """A 2D polygon extruded along `axis` ('x' takes (y, z) pairs, 'y'
    (x, z), 'z' (x, y))."""
    bm = bmesh.new()

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


def box_bm(x0, x1, y0, y1, z0, z1, bm=None, mat_index=0):
    """An axis-aligned box, 12 triangles, into `bm` (or a new one)."""
    assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
    bm = bm or bmesh.new()
    v = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f]).material_index = mat_index
    return bm


def box(name, coll, mat, x0, x1, y0, y1, z0, z1, variant):
    return finish(name, box_bm(x0, x1, y0, y1, z0, z1), coll, [mat], variant)


def centred_box_mesh(name, sx, sy, sz, mat):
    """A box mesh centred on its own origin, for linked copies."""
    return finish(name, box_bm(-sx / 2, sx / 2, -sy / 2, sy / 2, -sz / 2, sz / 2), None, [mat], None,
                  mesh_only=True)


def rings_bm(rings, zones=None, cap_zones=(0, 0)):
    """A closed solid through horizontal rings [(points2d, z), ...] of equal
    count: the bands between rings take `zones[k]`, the bottom and top caps
    `cap_zones`."""
    bm = bmesh.new()
    vs = [[bm.verts.new((x, y, z)) for x, y in pts] for pts, z in rings]
    n = len(vs[0])
    bm.faces.new(list(reversed(vs[0]))).material_index = cap_zones[0]
    bm.faces.new(vs[-1]).material_index = cap_zones[1]
    for k in range(len(vs) - 1):
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
            f.material_index = zones[k] if zones else 0
    return bm


def mitres(pts, closed):
    """Per point of a plan path, the mitre vector to the right of travel
    (outward for an anticlockwise outline): its projection on each adjacent
    run's normal is 1, so an offset by it keeps every run parallel."""
    n = len(pts)
    runs = n if closed else n - 1
    normals = []
    for i in range(runs):
        a, b = Vector(pts[i][:2]), Vector(pts[(i + 1) % n][:2])
        d = (b - a).normalized()
        normals.append(Vector((d.y, -d.x)))
    out = []
    for i in range(n):
        if closed:
            n0, n1 = normals[i - 1], normals[i]
        else:
            n0 = normals[max(i - 1, 0)]
            n1 = normals[min(i, runs - 1)]
        out.append((n0 + n1) / (1.0 + n0.dot(n1)))
    return out


def offset(pts, d, closed=True):
    """A plan outline moved outward by `d` (inward if negative)."""
    return [(p[0] + m.x * d, p[1] + m.y * d) for p, m in zip(pts, mitres(pts, closed))]


def ribbon_bm(bottom, top, out, inn, closed=False, top_zone=0):
    """A solid ribbon along a path given at its lower and upper edge
    (`bottom`, `top`: equal lists of (x, y, z)): its outer face `out` to the
    right of travel (outward), its inner face `inn` to the left, each edge
    offset by its own mitres so the faces stay parallel to the wall or edge
    the path follows."""
    mb, mt = mitres(bottom, closed), mitres(top, closed)
    bm = bmesh.new()

    def ring(pts, ms, d):
        return [bm.verts.new((p[0] + m.x * d, p[1] + m.y * d, p[2])) for p, m in zip(pts, ms)]

    ob, ib = ring(bottom, mb, out), ring(bottom, mb, -inn)
    ot, it = ring(top, mt, out), ring(top, mt, -inn)
    n = len(bottom)
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i])).material_index = top_zone
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
    if not closed:
        bm.faces.new((ob[0], ot[0], it[0], ib[0]))
        bm.faces.new((ob[-1], ib[-1], it[-1], ot[-1]))
    return bm


def at_z(path, z):
    return [(x, y, z) for x, y in path]


def lerp_outline(bottom, top, t):
    return [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(bottom, top)]


def slab(name, coll, m_side, m_top, outline, z0, z1, variant):
    """A flat slab over a plan outline, its top face in the deck material."""
    return finish(name, rings_bm([(outline, z0), (outline, z1)], cap_zones=(0, 1)), coll,
                  [m_side, m_top], variant)


def interp(table, x):
    """Linear interpolation in a table of (x, y), held flat beyond its ends."""
    if x <= table[0][0]:
        return table[0][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return table[-1][1]


# --- hulls -----------------------------------------------------------------

def hull_point(y, hw, z, stem, entry_y):
    """A template point at station `y` narrowed to the bow: on a parabola from
    `entry_y` to the stem at the point's own height, and collapsed onto the
    stem line where the station is ahead of it."""
    stem_y = interp(stem, z)
    if y >= stem_y - 1e-9:
        return 0.0, interp([(b, a) for a, b in stem], y)
    if y > entry_y:
        u = (y - entry_y) / (stem_y - entry_y)
        hw *= max(0.0, 1.0 - u * u)
    return hw, z


def hull_loft(stations, half_section, zones, top_zone, cap_zone):
    """A closed hull lofted through `stations`: `half_section(y)` gives the
    (half-width, z) points from the keel up to the deck edge; each ring runs
    keel, starboard up, across the deck, port down. Points that coincide (the
    keel, the stem, the bow point) are one vertex, so the bow closes to a
    line and a point; faces left with fewer than three corners are dropped."""
    bm = bmesh.new()
    cache = {}

    def vert(p):
        key = tuple(round(c, 5) for c in p)
        if key not in cache:
            cache[key] = bm.verts.new(p)
        return cache[key]

    rings = []
    for y in stations:
        half = half_section(y)
        k = len(half)
        ring = [vert((0.0, y, half[0][1]))]
        ring += [vert((hw, y, z)) for hw, z in half[1:]]
        ring += [vert((-hw, y, z)) for hw, z in reversed(half[1:])]
        rings.append(ring)
    # the zone of each ring run: up the starboard side, across, down the port
    seg_zones = list(zones) + [top_zone] + list(reversed(zones))
    n = len(rings[0])

    def face(vs, zone):
        uniq = []
        for v in vs:
            if v not in uniq:
                uniq.append(v)
        if len(uniq) < 3:
            return
        try:
            bm.faces.new(uniq).material_index = zone
        except ValueError:
            pass

    for a, b in zip(rings, rings[1:]):
        for j in range(n):
            i2 = (j + 1) % n
            face((a[j], a[i2], b[i2], b[j]), seg_zones[j])
    for ring in (rings[0], rings[-1]):
        face(ring, cap_zone)
    return bm


class Cat:
    """One catamaran's numbers: the catamaran's from the C_ constants, the
    small one's from the S_ constants."""

    def __init__(self, **numbers):
        self.__dict__.update(numbers)


BIG_CAT = Cat(
    stern_y=C_STERN_Y, aft_y=C_AFT_Y, tip_y=C_TIP_Y, half=C_HALF, hull_x=C_HULL_X, keel=C_KEEL,
    keel_stern=C_KEEL_STERN, keel_flat_aft=C_KEEL_FLAT_AFT, wet_deck=C_WET_DECK, entry_y=C_ENTRY_Y, stem=C_STEM,
    tunnel_y=C_TUNNEL_Y, stations=C_STATIONS, levels=C_LEVELS, zones=C_ZONES, fender=C_FENDER,
    fender_to=C_FENDER_TO, rail_from=C_RAIL_FROM, rail_nose=C_RAIL_NOSE,
    main=(C_MAIN_HW, C_MAIN_AFT, C_MAIN_SIDE_FWD, C_MAIN_FRONT, C_MAIN_FRONT_HW, C_MAIN_RAKE), main_top=C_MAIN_TOP,
    upper_deck=C_UPPER_DECK, main_win=C_MAIN_WIN, door_y=C_DOOR_Y, door_h=C_DOOR_H, main_aft_win=C_MAIN_AFT_WIN,
    upper=(C_UP_HW, C_UP_AFT, C_UP_SIDE_FWD, C_UP_FRONT, C_UP_FRONT_HW, C_UP_RAKE), up_top=C_UP_TOP,
    up_roof=C_UP_ROOF, up_roof_over=C_UP_ROOF_OVER, up_win=C_UP_WIN, up_aft_win=C_UP_AFT_WIN,
    wh=(C_WH_HW, C_WH_AFT, C_WH_SIDE_FWD, C_WH_FRONT, C_WH_FRONT_HW, -C_WH_LEAN), wh_base=C_WH_BASE,
    wh_top=C_WH_TOP, wh_win=C_WH_WIN, wh_roof=C_WH_ROOF, wh_roof_over=C_WH_ROOF_OVER, mast_at=C_MAST_AT,
    mast=C_MAST, light=C_LIGHT, radar_at=C_RADAR_AT, radar=C_RADAR,
    stair=(C_STAIR_HW, C_STAIR_RISERS, C_STAIR_GOING), bench=C_BENCH, bench_x=C_BENCH_X, bench_rows=C_BENCH_ROWS,
    bitts=C_BITTS, bitt=C_BITT)

SMALL_CAT = Cat(
    stern_y=S_STERN_Y, aft_y=S_AFT_Y, tip_y=S_TIP_Y, half=S_HALF, hull_x=S_HULL_X, keel=S_KEEL,
    keel_stern=S_KEEL_STERN, keel_flat_aft=S_KEEL_FLAT_AFT, wet_deck=S_WET_DECK, entry_y=S_ENTRY_Y, stem=S_STEM,
    tunnel_y=S_TUNNEL_Y, stations=S_STATIONS, levels=S_LEVELS, zones=C_ZONES, fender=S_FENDER,
    fender_to=S_FENDER_TO, rail_from=S_RAIL_FROM, rail_nose=S_RAIL_NOSE, main=S_MAIN, main_top=S_MAIN_TOP,
    upper_deck=S_UPPER_DECK, main_win=S_MAIN_WIN, door_y=S_DOOR_Y, door_h=S_DOOR_H, main_aft_win=S_MAIN_AFT_WIN,
    upper=None, wh=S_WH, wh_base=S_WH_BASE, wh_top=S_WH_TOP, wh_win=S_WH_WIN, wh_roof=S_WH_ROOF,
    wh_roof_over=S_WH_ROOF_OVER, mast_at=S_MAST_AT, mast=S_MAST, light=S_LIGHT, radar_at=S_RADAR_AT,
    radar=S_RADAR, stair=S_STAIR, bench=S_BENCH, bench_x=S_BENCH_X, bench_rows=S_BENCH_ROWS, bitts=S_BITTS,
    bitt=S_BITT)


def cat_section(cat, y, band=None):
    """A catamaran's demi-hull at station `y`, from its own centreline;
    `band(y)`, if given, moves the band's two edges (catamaran_b's sweep)."""
    out = []
    if y < cat.keel_flat_aft:
        s = (cat.keel_flat_aft - y) / (cat.keel_flat_aft - cat.stern_y)
        depth = 1.0 + (cat.keel_stern / cat.keel - 1.0) * s
    else:
        depth = 1.0
    levels = list(cat.levels)
    if band is not None:
        for k, z in zip(C_BAND_LEVELS, band(y)):
            levels[k] = (levels[k][0], z)
    for hw, z in levels:
        out.append(hull_point(y, hw, z * depth if z < 0 else z, cat.stem, cat.entry_y))
    return out


def cat_top_hw(cat, y):
    """The demi-hull's half-width at its top, as lofted."""
    return cat_section(cat, y)[-1][0]


def cat_lobe_x(cat, y, inner=False):
    """The starboard bow lobe's edge at `y`: 10 cm outside the hull's top,
    outside or inside it. Exact at stations, as the deck outline has it."""
    hw = cat_top_hw(cat, y) + C_LOBE_OVER
    return cat.hull_x - hw if inner else cat.hull_x + hw


def b_band(y):
    """catamaran_b's band edges at `y`, swept up to the bow."""
    t = min(1.0, max(0.0, (y - B_SWEEP_FROM) / (C_STEM[-1][1] - B_SWEEP_FROM)))
    t = t * t * (3.0 - 2.0 * t)
    return tuple(a + (b - a) * t for a, b in zip(B_BAND_AFT, B_BAND_BOW))


def m_sheer(y):
    return MAIN_DECK + M_SHEER_RISE * max(0.0, y / M_STEM_Y) ** 2


def m_keel(y):
    if y >= M_KEEL_FLAT_AFT:
        return M_KEEL
    s = (M_KEEL_FLAT_AFT - y) / (M_KEEL_FLAT_AFT - M_STERN_Y)
    return M_KEEL + (M_TRANSOM_BOTTOM - M_KEEL) * s ** 1.6


def m_section(y):
    """The monohull, from the centreline."""
    s = min(1.0, max(0.0, (M_NARROW_FROM - y) / (M_NARROW_FROM - M_STERN_Y)))
    width = M_HW * (1.0 - M_NARROW * s * s)
    out = []
    for frac, kind, val in M_LEVELS:
        z = {"keel": val * m_keel(y), "wl": 0.0, "sheer": m_sheer(y) + val}[kind]
        out.append(hull_point(y, frac * width, z, M_STEM, M_ENTRY_Y))
    return out


def m_deck_hw(y):
    """The monohull's deck edge half-width at `y`, linear between stations
    as the loft has it."""
    table = [(s, m_section(s)[-1][0]) for s in M_STATIONS]
    return interp(table, y)


def m_deck_z(y):
    table = [(s, m_section(s)[-1][1]) for s in M_STATIONS]
    return interp(table, y)


def d_sheer(y):
    return MAIN_DECK + D_SHEER_RISE * (abs(y) / D_HALF_L) ** 2


def d_section(y):
    """The double-ender, from the centreline: the same at both ends."""
    out = []
    for frac, kind, val in D_LEVELS:
        z = {"keel": val * D_KEEL, "wl": 0.0, "sheer": d_sheer(y) + val}[kind]
        out.append(hull_point(abs(y), frac * D_HW, z, D_STEM, D_ENTRY_Y))
    return out


D_STATIONS = tuple(sorted({-y for y in D_STATIONS_HALF} | set(D_STATIONS_HALF)))


def d_deck_hw(y):
    return interp([(s, d_section(s)[-1][0]) for s in D_STATIONS], y)


def d_deck_z(y):
    return interp([(s, d_section(s)[-1][1]) for s in D_STATIONS], y)


# --- shared fittings -----------------------------------------------------------

def stair_bms(base, top, risers, going, hw, y_top):
    """A straight stair from a deck at `base` up to a deck edge at `y_top`
    whose floor is `top`: the last tread a centimetre under that floor (so
    the two never share a plane) running 5 cm in under the upper deck, the
    foot sunk LAP_STAIR into the lower deck; and the profile of its side
    panels, which end 4 cm inside the upper deck's edge, not on its face."""
    last = top - 0.01
    rise = (last - base) / risers
    y_in = y_top + 0.05
    y0 = y_in - risers * going
    prof = [(y0, base - LAP_STAIR)]
    for k in range(1, risers + 1):
        prof += [(y0 + (k - 1) * going, base + k * rise), (y0 + k * going, base + k * rise)]
    prof += [(y_in, last - STAIR_SOFFIT), (y0 + STAIR_SOFFIT, base - LAP_STAIR)]
    stair = prism_bm(prof, "x", -hw, hw)

    def nose(y):
        return base + rise + (y - y0) * (last - base - rise) / (y_in - going - y0)

    below, above, _ = STAIR_PANEL
    y_end = y_top + 0.04
    panel = [(y0 - 0.05, base - LAP_STAIR - 0.005), (y_end, nose(y_end) - below),
             (y_end, nose(y_end) + above), (y0 - 0.05, base + above)]
    return stair, panel, y0


def bench_bm(length, depth, seat, back_top):
    """A chunky bench facing +Y: a solid plinth to the seat, sunk LAP_BENCH
    into the deck, and a back slab standing 2 cm proud of the plinth's back
    and 2 cm short of its ends, its foot 3 cm down inside the plinth."""
    bm = box_bm(-length / 2, length / 2, -depth / 2, depth / 2, -LAP_BENCH, seat)
    box_bm(-length / 2 + 0.02, length / 2 - 0.02, -depth / 2 - 0.02, -depth / 2 - 0.02 + BENCH_BACK,
           seat - 0.03, back_top, bm)
    return bm


def window_slabs(prefix, coll, mesh, variant, items):
    """Linked copies of one window mesh: (name, x, y, z, rotation)."""
    return [place(f"{prefix}{name}", mesh, coll, variant, (x, y, z), rot) for name, x, y, z, rot in items]


# --- the catamaran -------------------------------------------------------------

def cat_deck_outline(cat):
    """The bridging deck in plan, anticlockwise from the port quarter: square
    aft, straight sides to the hulls' entry, then a lobe over each bow 10 cm
    outside the hull's top, and the tunnel's edge across between them."""
    lobe = [y for y in cat.stations if cat.entry_y < y < cat.stations[-1]]
    inner = [y for y in reversed(lobe) if y >= cat.tunnel_y]
    stbd = [(cat.hull_x + cat_top_hw(cat, y) + C_LOBE_OVER, y) for y in lobe]
    stbd += [(cat.hull_x, cat.tip_y)]
    stbd += [(cat.hull_x - cat_top_hw(cat, y) - C_LOBE_OVER, y) for y in inner]
    port = [(-x, y) for x, y in reversed(stbd)]
    return ([(-cat.half, cat.aft_y), (cat.half, cat.aft_y), (cat.half, cat.entry_y)] + stbd + port +
            [(-cat.half, cat.entry_y)])


def c_cabin_outlines(hw, aft, side_fwd, front, front_hw, rake):
    """A cabin's plan at its foot and at its top: square aft, chamfered front
    corners, the front and chamfers leaning back by `rake` (negative: out)."""
    foot = [(-hw, aft), (hw, aft), (hw, side_fwd), (front_hw, front), (-front_hw, front), (-hw, side_fwd)]
    head = [(-hw, aft), (hw, aft), (hw, side_fwd - rake), (front_hw, front - rake), (-front_hw, front - rake),
            (-hw, side_fwd - rake)]
    return foot, head


def front_band(foot, head, z0, z1, za, zb, y_start):
    """The window band's path round a cabin's front at heights za and zb,
    from the starboard side at `y_start` round to the port side."""
    def path(z):
        t = (z - z0) / (z1 - z0)
        pts = lerp_outline(foot, head, t)
        hw = pts[1][0]
        return [(hw, y_start)] + pts[2:] + [(-hw, y_start)]
    return at_z(path(za), za), at_z(path(zb), zb)


def build_cat(coll, m, cat, v, p):
    """A catamaran from its numbers `cat`, as variant `v`, every part's name
    prefixed `p` (the catamaran's none)."""
    # the demi-hulls: one mesh, two placings
    zones = [{"white": 0, "band": 1, "bottom": 2}[z] for z in cat.zones]
    hull = finish(f"{p}hull", hull_loft(cat.stations, lambda y: cat_section(cat, y), zones, 0, 0), None,
                  [m["white"], m["band"], m["bottom"]], None, smooth_angle=35, mesh_only=True)
    place(f"{p}hull_starboard", hull, coll, v, (cat.hull_x, 0.0, 0.0))
    place(f"{p}hull_port", hull, coll, v, (-cat.hull_x, 0.0, 0.0))
    # the bridging deck, its top the main deck
    deck = cat_deck_outline(cat)
    slab(f"{p}deck", coll, m["white"], m["deck"], deck, cat.wet_deck, MAIN_DECK, v)
    # the rubbing strake: along the deck's edge from one bow lobe round the
    # stern to the other, lapping into the deck's side
    z0, z1, proud, lap = cat.fender
    stbd = [(cat.half, cat.aft_y), (cat.half, cat.entry_y)]
    stbd += [(cat_lobe_x(cat, y), y) for y in cat.stations if cat.entry_y < y <= cat.fender_to]
    path = [(-x, y) for x, y in reversed(stbd)] + stbd
    finish(f"{p}fender", ribbon_bm(at_z(path, z0), at_z(path, z1), proud, lap), coll, [m["fender"]], v)

    # main cabin, its roof the upper deck
    main_hw, main_aft = cat.main[0], cat.main[1]
    foot, head = c_cabin_outlines(*cat.main)
    cz0 = MAIN_DECK - LAP_CABIN
    finish(f"{p}cabin_main", rings_bm([(foot, cz0), (head, cat.main_top)]), coll, [m["white"]], v)
    upper = offset(head, C_SLAB_OVER)
    slab(f"{p}upper_deck", coll, m["white"], m["deck"], upper, cat.upper_deck - C_SLAB_T, cat.upper_deck, v)
    za, zb = cat.main_win
    bot, top = front_band(foot, head, cz0, cat.main_top, za, zb, cat.door_y[1] + C_DOOR_GAP)
    finish(f"{p}windows_main_front", ribbon_bm(bot, top, SLAB_OUT, SLAB_IN), coll, [m["glass"]], v)
    y0, y1 = main_aft + BAND_END, cat.door_y[0] - C_DOOR_GAP
    aft_band = centred_box_mesh(f"{p}windows_main_aft", SLAB_T, y1 - y0, zb - za, m["glass"])
    for side, sx in (("starboard", 1), ("port", -1)):
        place(f"{p}windows_main_aft_{side}", aft_band, coll, v, (sx * (main_hw + slab_centre(SLAB_T)), (y0 + y1) / 2,
                                                                 (za + zb) / 2))
    # the boarding doors, both sides, and the aft wall's door and windows
    door = centred_box_mesh(f"{p}door", DOOR_T, cat.door_y[1] - cat.door_y[0], cat.door_h, m["door"])
    dz = MAIN_DECK - DOOR_SINK + cat.door_h / 2
    dy = (cat.door_y[0] + cat.door_y[1]) / 2
    dc = slab_centre(DOOR_T)
    place(f"{p}door_starboard", door, coll, v, (main_hw + dc, dy, dz))
    place(f"{p}door_port", door, coll, v, (-(main_hw + dc), dy, dz))
    place(f"{p}door_main_aft", door, coll, v, (0.0, main_aft - dc, dz), math.pi / 2)
    x0, x1 = cat.main_aft_win
    aft_win = centred_box_mesh(f"{p}window_main_aft_wall", x1 - x0, SLAB_T, zb - za, m["glass"])
    for side, sx in (("starboard", 1), ("port", -1)):
        place(f"{p}window_main_aft_wall_{side}", aft_win, coll, v,
              (sx * (x0 + x1) / 2, main_aft - slab_centre(SLAB_T), (za + zb) / 2))

    # upper cabin (the small catamaran has none: its top deck is open)
    if cat.upper is not None:
        up_aft = cat.upper[1]
        ufoot, uhead = c_cabin_outlines(*cat.upper)
        uz0 = cat.upper_deck - LAP_CABIN
        finish(f"{p}cabin_upper", rings_bm([(ufoot, uz0), (uhead, cat.up_top)]), coll, [m["white"]], v)
        slab(f"{p}roof_upper", coll, m["white"], m["white"], offset(uhead, cat.up_roof_over), cat.up_roof[0],
             cat.up_roof[1], v)
        za, zb = cat.up_win
        bot, top = front_band(ufoot, uhead, uz0, cat.up_top, za, zb, up_aft + BAND_END)
        finish(f"{p}windows_upper", ribbon_bm(bot, top, SLAB_OUT, SLAB_IN), coll, [m["glass"]], v)
        place(f"{p}door_upper_aft", door, coll, v, (0.0, up_aft - dc, cat.upper_deck - DOOR_SINK + cat.door_h / 2),
              math.pi / 2)
        x0, x1 = cat.up_aft_win
        up_aft_win = centred_box_mesh(f"{p}window_upper_aft_wall", x1 - x0, SLAB_T, zb - za, m["glass"])
        for side, sx in (("starboard", 1), ("port", -1)):
            place(f"{p}window_upper_aft_wall_{side}", up_aft_win, coll, v,
                  (sx * (x0 + x1) / 2, up_aft - slab_centre(SLAB_T), (za + zb) / 2))

    # the wheelhouse, its windows a band all round
    wfoot, whead = c_cabin_outlines(*cat.wh)
    finish(f"{p}wheelhouse", rings_bm([(wfoot, cat.wh_base), (whead, cat.wh_top)]), coll, [m["white"]], v)
    za, zb = cat.wh_win

    def wh_at(z):
        return at_z(lerp_outline(wfoot, whead, (z - cat.wh_base) / (cat.wh_top - cat.wh_base)), z)

    finish(f"{p}windows_wheelhouse", ribbon_bm(wh_at(za), wh_at(zb), SLAB_OUT, SLAB_IN, closed=True), coll,
           [m["glass"]], v)
    slab(f"{p}roof_wheelhouse", coll, m["white"], m["white"], offset(whead, cat.wh_roof_over), cat.wh_roof[0],
         cat.wh_roof[1], v)
    # the mast, a plain pole with the masthead light on top
    mx, my = cat.mast_at
    zb0, zt, wb, wt = cat.mast

    def sq(w):
        return [(mx - w / 2, my - w / 2), (mx + w / 2, my - w / 2), (mx + w / 2, my + w / 2), (mx - w / 2, my + w / 2)]

    finish(f"{p}mast", rings_bm([(sq(wb), zb0), (sq(wt), zt)]), coll, [m["mast"]], v)
    box(f"{p}masthead_light", coll, m["mast"], mx - cat.light / 2, mx + cat.light / 2, my - cat.light / 2,
        my + cat.light / 2, zt - LIGHT_SINK, zt - LIGHT_SINK + cat.light, v)
    # the radar on a pedestal of its own (a scanner across a pole read as a cross)
    radar(coll, m, v, p, cat.radar_at, cat.radar, cat.wh_roof[1])

    # rails: round the open aft main deck, round the foredeck, round the upper deck
    rz0, rz1 = MAIN_DECK - LAP_RAIL, MAIN_DECK + C_RAIL_H
    edge = cat.half - RAIL_INSET
    y_fwd = main_aft + C_RAIL_AFT_RUN
    aft_path = [(-edge, y_fwd), (-edge, cat.aft_y + RAIL_INSET), (edge, cat.aft_y + RAIL_INSET), (edge, y_fwd)]
    finish(f"{p}rail_aft_deck", ribbon_bm(at_z(aft_path, rz0), at_z(aft_path, rz1), 0.0, C_RAIL_T), coll,
           [m["white"]], v)
    # the foredeck's: up the outside of each lobe, across its nose short of
    # the bow point, down its inside and across the tunnel's edge
    stbd = [(cat_lobe_x(cat, cat.rail_from), cat.rail_from)]
    stbd += [(cat_lobe_x(cat, y), y) for y in cat.stations if cat.rail_from < y <= cat.rail_nose]
    stbd += [(cat_lobe_x(cat, y, inner=True), y) for y in reversed(cat.stations) if cat.tunnel_y <= y <= cat.rail_nose]
    fore = stbd + [(-x, y) for x, y in reversed(stbd)]
    finish(f"{p}rail_foredeck", ribbon_bm(at_z(fore, rz0), at_z(fore, rz1), -RAIL_INSET, C_RAIL_T), coll,
           [m["white"]], v)
    # the upper deck's rail follows its slab's edge, with a gap aft for the stair
    shw, risers, going = cat.stair
    aft_y = upper_rail(coll, m, v, f"{p}rail_upper_deck", upper, cat.upper_deck, shw)

    # the stair from the aft main deck up to the upper deck, on the centreline
    stair(coll, m, v, p, m["deck"], MAIN_DECK, cat.upper_deck, risers, going, shw, aft_y)

    # benches on the open upper deck, rows of two, facing forward
    bench = finish(f"{p}bench", bench_bm(*cat.bench), None, [m["seats"]], None, mesh_only=True)
    for r, y in enumerate(cat.bench_rows):
        for side, sx in (("starboard", 1), ("port", -1)):
            place(f"{p}bench_{r}_{side}", bench, coll, v, (sx * cat.bench_x, y, cat.upper_deck))
    # mooring bitts
    br, bh = cat.bitt
    ring = [(br * math.cos(math.tau * i / 8), br * math.sin(math.tau * i / 8)) for i in range(8)]
    bitt = finish(f"{p}bitt", prism_bm(ring, "z", -LAP_BITT, bh), None, [m["mast"]], None, mesh_only=True)
    for k, (x, y) in enumerate(cat.bitts):
        place(f"{p}bitt_{k}", bitt, coll, v, (x, y, MAIN_DECK))


def linked_copy(src, name, coll, variant, loc=None, rot_z=None):
    """An object sharing `src`'s mesh (reshape one, reshape both), as part of
    `variant`; where it stands is `src`'s unless given."""
    obj = src.copy()
    obj.name = name
    obj["kyt_variant"] = variant
    if loc is not None:
        obj.location = loc
    if rot_z is not None:
        obj.rotation_euler = (0.0, 0.0, rot_z)
    coll.objects.link(obj)
    return obj


def turned(src, name, coll, variant):
    """`src`'s linked copy turned 180 degrees about the origin: the other end
    of a double-ender."""
    x, y, z = src.location
    return linked_copy(src, name, coll, variant, (-x, -y, z), src.rotation_euler.z + math.pi)


def build_catamaran_b(coll, m, source):
    """The catamaran in another livery: its own hulls (the band swept up to
    the bow), deck (navy sides) and benches on its own materials; every
    other part a linked copy of the catamaran's."""
    v, p = "catamaran_b", "catamaran_b_"
    own = ("hull_", "deck", "bench_")
    for src in source:
        if not src.name.startswith(own):
            linked_copy(src, f"{p}{src.name}", coll, v)
    zones = [{"white": 0, "band": 1, "bottom": 2}[z] for z in C_ZONES]
    hull = finish(f"{p}hull", hull_loft(C_STATIONS, lambda y: cat_section(BIG_CAT, y, band=b_band), zones, 0, 0),
                  None, [m["catamaran_b_hull"], m["catamaran_b_band"], m["bottom"]], None, smooth_angle=35,
                  mesh_only=True)
    place(f"{p}hull_starboard", hull, coll, v, (C_HULL_X, 0.0, 0.0))
    place(f"{p}hull_port", hull, coll, v, (-C_HULL_X, 0.0, 0.0))
    slab(f"{p}deck", coll, m["catamaran_b_hull"], m["deck"], cat_deck_outline(BIG_CAT), C_WET_DECK, MAIN_DECK, v)
    bench = finish(f"{p}bench", bench_bm(*C_BENCH), None, [m["catamaran_b_seats"]], None, mesh_only=True)
    for src in source:
        if src.name.startswith("bench_"):
            place(f"{p}{src.name}", bench, coll, v, tuple(src.location), src.rotation_euler.z)


def jet_bm():
    """One waterjet unit about its hull's centreline: an octagonal housing
    from inside the hull, tapering to the nozzle aft of the transom, and the
    reversing bucket over the nozzle's mouth."""
    bm = bmesh.new()
    rings = []
    for aft, r in J_RINGS:
        rings.append([bm.verts.new((r * math.cos(a), C_STERN_Y - aft, J_Z + r * math.sin(a)))
                      for a in (math.tau * (i + 0.5) / 8 for i in range(8))])
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    for ra, rb in zip(rings, rings[1:]):
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    hw, a0, a1, z0, z1 = J_BUCKET
    box_bm(-hw, hw, C_STERN_Y - a1, C_STERN_Y - a0, z0, z1, bm)
    return bm


def build_catamaran_waterjets(coll, m, source):
    """The catamaran with a waterjet under each transom; every other part a
    linked copy of the catamaran's."""
    v, p = "catamaran_waterjets", "catamaran_waterjets_"
    for src in source:
        linked_copy(src, f"{p}{src.name}", coll, v)
    jet = finish(f"{p}jet", jet_bm(), None, [m["jet"]], None, mesh_only=True)
    place(f"{p}jet_starboard", jet, coll, v, (C_HULL_X, 0.0, 0.0))
    place(f"{p}jet_port", jet, coll, v, (-C_HULL_X, 0.0, 0.0))


def slab_centre(t):
    """Where a slab `t` thick, lapping SLAB_IN into its wall, has its centre,
    measured outward from the wall's face."""
    return t / 2 - SLAB_IN


def radar(coll, m, v, p, at, dims, roof_top):
    """A radar scanner on a pedestal of its own on a roof."""
    rx, ry = at
    pw, ph, sl, sd, st = dims
    zr = roof_top - LAP_CABIN
    zs = zr + ph - RADAR_SINK
    return [box(f"{p}radar_pedestal", coll, m["mast"], rx - pw / 2, rx + pw / 2, ry - pw / 2, ry + pw / 2, zr,
                zr + ph, v),
            box(f"{p}radar", coll, m["mast"], rx - sl / 2, rx + sl / 2, ry - sd / 2, ry + sd / 2, zs, zs + st, v)]


def upper_rail(coll, m, v, name, upper, deck, stair_hw):
    """The rail round an upper deck, along its slab's edge, open aft either
    side of the stair. Returns the deck's aft edge."""
    gap = stair_hw + STAIR_GAP
    aft_y = upper[0][1]
    path = [(gap, aft_y)] + upper[1:] + [upper[0], (-gap, aft_y)]
    finish(name, ribbon_bm(at_z(path, deck - LAP_RAIL), at_z(path, deck + C_RAIL_H), -RAIL_INSET, C_RAIL_T),
           coll, [m["white"]], v)
    return aft_y


def stair(coll, m, v, p, mat, base, top, risers, going, hw, aft_y):
    """The stair up to an upper deck's aft edge on the centreline, its two
    side panels linked copies of one mesh."""
    st, panel, _ = stair_bms(base, top, risers, going, hw, aft_y)
    out = [finish(f"{p}stair", st, coll, [mat], v)]
    t = STAIR_PANEL[2]
    pmesh = finish(f"{p}stair_side", prism_bm(panel, "x", -t / 2, t / 2), None, [m["white"]], None, mesh_only=True)
    for side, sx in (("starboard", 1), ("port", -1)):
        out.append(place(f"{p}stair_side_{side}", pmesh, coll, v, (sx * (hw + t / 2 - 0.02), 0.0, 0.0)))
    return out


# --- the monohull ----------------------------------------------------------------

def arc_outline(hw, aft, arc_c, r):
    """A cabin in plan: square aft, straight sides, a semicircular front
    faceted at M_FACET, anticlockwise from the port quarter."""
    pts = [(-hw, aft), (hw, aft)]
    k = int(round(180.0 / M_FACET))
    for i in range(k + 1):
        th = math.radians(i * M_FACET)
        pts.append((r * math.cos(th), arc_c + r * math.sin(th)))
    return pts


def arc_windows(arc_c, r, z, first=1, last=6):
    """Placings for window slabs on the faceted front's facets `first`..`last`:
    (x, y, z, rotation) with the slab's thickness along each facet's normal,
    lapping SLAB_IN in and standing SLAB_OUT out."""
    out = []
    half = math.radians(M_FACET / 2)
    for k in range(first, last + 1):
        phi = math.radians(k * M_FACET) + half
        d = r * math.cos(half) + slab_centre(SLAB_T)
        out.append((d * math.cos(phi), arc_c + d * math.sin(phi), z, phi))
    return out


def side_windows(name, hw, ys, z):
    """Placings for window slabs on both side walls of a cabin `hw` wide."""
    out = []
    for k, y in enumerate(ys):
        out.append((f"{name}_s{k}", hw + slab_centre(SLAB_T), y, z, 0.0))
        out.append((f"{name}_p{k}", -(hw + slab_centre(SLAB_T)), y, z, 0.0))
    return out


def build_monohull(coll, m):
    v = "monohull"
    p = "monohull_"
    zone_ix = {"hull": 0, "white": 1, "bottom": 2, "deck": 3}
    hull = hull_loft(M_STATIONS, m_section, [zone_ix[z] for z in M_ZONES], zone_ix["deck"], zone_ix["hull"])
    finish(f"{p}hull", hull, coll, [m["monohull_hull"], m["white"], m["bottom"], m["monohull_deck"]], v,
           smooth_angle=35)
    # the skeg and rudder under the run
    finish(f"{p}skeg", prism_bm(M_SKEG_PROFILE, "x", -M_SKEG_T / 2, M_SKEG_T / 2), coll, [m["bottom"]], v)
    rt, ry0, ry1, rz0, rz1 = M_RUDDER
    box(f"{p}rudder", coll, m["bottom"], -rt / 2, rt / 2, ry0, ry1, rz0, rz1, v)

    # main cabin, round-fronted, upright
    foot = arc_outline(M_MAIN_HW, M_MAIN_AFT, *M_MAIN_ARC)
    cz0 = MAIN_DECK - LAP_CABIN
    finish(f"{p}cabin_main", rings_bm([(foot, cz0), (foot, M_MAIN_TOP)]), coll, [m["white"]], v)
    upper = offset(foot, M_SLAB_OVER)
    slab(f"{p}upper_deck", coll, m["white"], m["monohull_deck"], upper, M_UPPER_DECK - M_SLAB_T, M_UPPER_DECK, v)
    ww, wh = M_WIN
    win = centred_box_mesh(f"{p}window", SLAB_T, ww, wh, m["glass"])
    wz = (M_WIN_Z[0] + M_WIN_Z[1]) / 2
    sc = slab_centre(SLAB_T)
    items = side_windows("main", M_MAIN_HW, M_WIN_Y, wz)
    items += [(f"main_front{k}", *w) for k, w in enumerate(arc_windows(M_MAIN_ARC[0], M_MAIN_ARC[1], wz))]
    items += [(f"main_aft{k}", x, M_MAIN_AFT - sc, wz, math.pi / 2) for k, x in enumerate(M_AFT_WIN_X)]
    window_slabs(f"{p}window_", coll, win, v, items)
    door = centred_box_mesh(f"{p}door", DOOR_T, M_DOOR_Y[1] - M_DOOR_Y[0], M_DOOR_H, m["monohull_door"])
    dz = MAIN_DECK - DOOR_SINK + M_DOOR_H / 2
    dy = (M_DOOR_Y[0] + M_DOOR_Y[1]) / 2
    dc = slab_centre(DOOR_T)
    place(f"{p}door_starboard", door, coll, v, (M_MAIN_HW + dc, dy, dz))
    place(f"{p}door_port", door, coll, v, (-(M_MAIN_HW + dc), dy, dz))
    place(f"{p}door_main_aft", door, coll, v, (0.0, M_MAIN_AFT - dc, dz), math.pi / 2)

    # upper cabin
    ufoot = arc_outline(M_UP_HW, M_UP_AFT, *M_UP_ARC)
    uz0 = M_UPPER_DECK - LAP_CABIN
    finish(f"{p}cabin_upper", rings_bm([(ufoot, uz0), (ufoot, M_UP_TOP)]), coll, [m["white"]], v)
    uroof = offset(ufoot, M_UP_ROOF_OVER)
    slab(f"{p}roof_upper", coll, m["white"], m["white"], uroof, M_UP_ROOF[0], M_UP_ROOF[1], v)
    uw, uh = M_UP_WIN
    uwin = centred_box_mesh(f"{p}window_upper", SLAB_T, uw, uh, m["glass"])
    uwz = (M_UP_WIN_Z[0] + M_UP_WIN_Z[1]) / 2
    items = side_windows("upper", M_UP_HW, M_UP_WIN_Y, uwz)
    items += [(f"upper_front{k}", *w) for k, w in enumerate(arc_windows(M_UP_ARC[0], M_UP_ARC[1], uwz))]
    items += [(f"upper_aft{k}", x, M_UP_AFT - sc, uwz, math.pi / 2) for k, x in enumerate(M_UP_AFT_WIN_X)]
    window_slabs(f"{p}window_", coll, uwin, v, items)
    place(f"{p}door_upper_aft", door, coll, v, (0.0, M_UP_AFT - dc, M_UPPER_DECK - DOOR_SINK + M_DOOR_H / 2),
          math.pi / 2)

    # the pilothouse: square, upright, single windows, a sun visor forward
    hw, ya, yf = M_PH
    finish(f"{p}pilothouse", box_bm(-hw, hw, ya, yf, M_PH_BASE, M_PH_TOP), coll, [m["white"]], v)
    pw, ph = M_PH_WIN
    pwin = centred_box_mesh(f"{p}window_pilothouse", SLAB_T, pw, ph, m["glass"])
    pz = (M_PH_WIN_Z[0] + M_PH_WIN_Z[1]) / 2
    items = [(f"ph_front{k}", x, yf + sc, pz, math.pi / 2) for k, x in enumerate(M_PH_FRONT_WIN_X)]
    items += side_windows("ph", hw, M_PH_SIDE_WIN_Y, pz)
    items += [(f"ph_aft{k}", x, ya - sc, pz, math.pi / 2) for k, x in enumerate(M_PH_AFT_WIN_X)]
    window_slabs(f"{p}window_", coll, pwin, v, items)
    side_over, aft_over = M_PH_ROOF_OVER
    box(f"{p}roof_pilothouse", coll, m["white"], -hw - side_over, hw + side_over, ya - aft_over, yf + M_PH_VISOR,
        M_PH_ROOF[0], M_PH_ROOF[1], v)

    # the stack: an oval, raked aft, its top band black
    sx, sy = M_STACK_AT
    ax, ay = M_STACK
    z0, zband, z1 = M_STACK_Z

    def oval(cy):
        return [(sx + ax * math.cos(math.tau * i / 12), cy + ay * math.sin(math.tau * i / 12)) for i in range(12)]

    def cy_at(z):
        return sy - M_STACK_RAKE * (z - z0) / (z1 - z0)

    finish(f"{p}stack", rings_bm([(oval(cy_at(z0)), z0), (oval(cy_at(zband)), zband), (oval(cy_at(z1)), z1)],
                                 zones=(0, 1), cap_zones=(0, 1)), coll,
           [m["monohull_stack"], m["monohull_stack_top"]], v)
    # the pole mast with its light on top, the radar on its own pedestal
    mx, my = M_MAST_AT
    zb0, zt, rb, rtop = M_MAST

    def circ(r):
        return [(mx + r * math.cos(math.tau * i / 8), my + r * math.sin(math.tau * i / 8)) for i in range(8)]

    finish(f"{p}mast", rings_bm([(circ(rb), zb0), (circ(rtop), zt)]), coll, [m["mast"]], v)
    box(f"{p}masthead_light", coll, m["mast"], mx - M_LIGHT / 2, mx + M_LIGHT / 2, my - M_LIGHT / 2, my + M_LIGHT / 2,
        zt - LIGHT_SINK, zt - LIGHT_SINK + M_LIGHT, v)
    radar(coll, m, v, p, M_RADAR_AT, M_RADAR, M_PH_ROOF[1])

    # the foredeck bulwark, rising with the sheer, in from the deck edge;
    # its aft ends ramp up from low, as a ship's bulwark ends
    ys = [M_BULWARK_FROM] + [y for y in M_STATIONS if M_BULWARK_FROM < y < M_STEM_Y]
    stbd = [(m_deck_hw(y) - M_EDGE_INSET, y) for y in ys]
    path = stbd + [(0.0, M_STEM_Y - M_STEM_INSET)] + [(-x, y) for x, y in reversed(stbd)]
    zs = [m_deck_z(y) for _, y in path]

    def height(y):
        if y >= M_BULWARK_FULL:
            return M_BULWARK_H
        t = (y - M_BULWARK_FROM) / (M_BULWARK_FULL - M_BULWARK_FROM)
        return M_BULWARK_FOOT + (M_BULWARK_H - M_BULWARK_FOOT) * t

    bot = [(x, y, z - M_EDGE_SINK) for (x, y), z in zip(path, zs)]
    top = [(x, y, z + height(y)) for (x, y), z in zip(path, zs)]
    finish(f"{p}bulwark_fore", ribbon_bm(bot, top, 0.0, M_BULWARK_T), coll, [m["white"]], v)
    # the fantail's rail round the open aft deck
    y_fwd = M_MAIN_AFT + C_RAIL_AFT_RUN
    ys = [y_fwd] + [y for y in reversed(M_STATIONS) if y < y_fwd]
    port = [(-(m_deck_hw(y) - M_EDGE_INSET), y if y > M_STERN_Y else M_STERN_Y + M_EDGE_INSET) for y in ys]
    path = port + [(-x, y) for x, y in reversed(port)]
    finish(f"{p}rail_fantail", ribbon_bm(at_z(path, MAIN_DECK - M_EDGE_SINK), at_z(path, MAIN_DECK + C_RAIL_H), 0.0,
                                         M_FANTAIL_RAIL_T), coll, [m["white"]], v)
    # the upper deck's rail, a gap aft for the stair, and the stair from the fantail up
    aft_y = upper_rail(coll, m, v, f"{p}rail_upper_deck", upper, M_UPPER_DECK, M_STAIR_HW)
    stair(coll, m, v, p, m["monohull_deck"], MAIN_DECK, M_UPPER_DECK, M_STAIR_RISERS, M_STAIR_GOING, M_STAIR_HW, aft_y)
    # benches: along each rail facing in, and one back to back on the centreline
    bench = finish(f"{p}bench", bench_bm(*M_BENCH), None, [m["monohull_seats"]], None, mesh_only=True)
    rail_in = upper[1][0] - RAIL_INSET - C_RAIL_T
    bx = rail_in - M_BENCH_CLEAR - (M_BENCH[1] / 2 + 0.02)
    for k, y in enumerate(M_SIDE_BENCH_Y):
        place(f"{p}bench_s{k}", bench, coll, v, (bx, y, M_UPPER_DECK), math.pi / 2)
        place(f"{p}bench_p{k}", bench, coll, v, (-bx, y, M_UPPER_DECK), -math.pi / 2)
    cx, cy, cl, cd = M_CENTRE_BENCH
    cbm = box_bm(-cd / 2, cd / 2, -cl / 2, cl / 2, -LAP_BENCH, M_BENCH[2])
    box_bm(-BENCH_BACK / 2 - 0.01, BENCH_BACK / 2 + 0.01, -cl / 2 + 0.02, cl / 2 - 0.02, M_BENCH[2] - 0.03,
           M_BENCH[3], cbm)
    finish(f"{p}bench_centre", cbm, coll, [m["monohull_seats"]], v).location = (cx, cy, M_UPPER_DECK)


# --- the double-ender ----------------------------------------------------------

def d_outline(hw, c, r):
    """A cabin in plan with a half-round at each end, faceted at D_FACET so a
    flat facet faces each end: straight sides from y -c to c, anticlockwise
    from the starboard side's forward end."""
    k = int(round(180.0 / D_FACET))
    fwd = [(r * math.cos(math.radians(i * D_FACET)), c + r * math.sin(math.radians(i * D_FACET))) for i in range(k + 1)]
    aft = [(r * math.cos(math.radians(180.0 + i * D_FACET)), -c + r * math.sin(math.radians(180.0 + i * D_FACET)))
           for i in range(k + 1)]
    return fwd + aft


def d_end_facets(c, r, facets, z):
    """Placings on the +Y end's facets: (x, y, z, rotation), a slab's
    thickness along each facet's normal."""
    half = math.radians(D_FACET / 2)
    out = []
    for k in facets:
        phi = math.radians(k * D_FACET) + half
        d = r * math.cos(half) + slab_centre(SLAB_T)
        out.append((d * math.cos(phi), c + d * math.sin(phi), z, phi))
    return out


def build_double_ended(coll, m):
    v, p = "double_ended", "double_ended_"
    mats_hull = [m["double_ended_hull"], m["white"], m["bottom"], m["double_ended_deck"]]
    zone_ix = {"hull": 0, "white": 1, "bottom": 2, "deck": 3}
    finish(f"{p}hull", hull_loft(D_STATIONS, d_section, [zone_ix[z] for z in D_ZONES], 3, 0), coll, mats_hull, v,
           smooth_angle=35)
    ends = []      # the +Y end's parts; each gets a turned linked copy at the -Y end

    # a skeg with screw and rudder at each end
    ends.append(finish(f"{p}skeg_fwd", prism_bm(D_SKEG, "x", -D_SKEG_T / 2, D_SKEG_T / 2), coll, [m["bottom"]], v))

    # main cabin, round at both ends, its roof the upper deck
    mhw, mc = D_MAIN
    foot = d_outline(mhw, mc, mhw)
    cz0 = MAIN_DECK - LAP_CABIN
    finish(f"{p}cabin_main", rings_bm([(foot, cz0), (foot, D_MAIN_TOP)]), coll, [m["white"]], v)
    upper = offset(foot, M_SLAB_OVER)
    slab(f"{p}upper_deck", coll, m["white"], m["double_ended_deck"], upper, D_UPPER_DECK - M_SLAB_T, D_UPPER_DECK, v)
    win = centred_box_mesh(f"{p}window", SLAB_T, D_WIN[0], D_WIN[1], m["glass"])
    wz = (D_WIN_Z[0] + D_WIN_Z[1]) / 2
    ys = sorted({-y for y in D_WIN_Y} | set(D_WIN_Y))
    window_slabs(f"{p}window_", coll, win, v, side_windows("main", mhw, ys, wz))
    ends += window_slabs(f"{p}window_", coll, win, v,
                         [(f"main_fwd{k}", *w) for k, w in enumerate(d_end_facets(mc, mhw, D_END_FACETS, wz))])
    door = centred_box_mesh(f"{p}door", DOOR_T, D_DOOR_Y[1] - D_DOOR_Y[0], D_DOOR_H, m["double_ended_door"])
    dc = slab_centre(DOOR_T)
    dz = MAIN_DECK - DOOR_SINK + D_DOOR_H / 2
    place(f"{p}door_starboard", door, coll, v, (mhw + dc, 0.0, dz))
    place(f"{p}door_port", door, coll, v, (-(mhw + dc), 0.0, dz))
    end_y = mc + mhw * math.cos(math.radians(D_FACET / 2))
    ends.append(place(f"{p}door_main_fwd", door, coll, v,
                      (0.0, end_y + dc, d_deck_z(end_y) - DOOR_SINK + D_DOOR_H / 2), math.pi / 2))

    # upper cabin, round at both ends
    uhw, uc = D_UP
    ufoot = d_outline(uhw, uc, uhw)
    uz0 = D_UPPER_DECK - LAP_CABIN
    finish(f"{p}cabin_upper", rings_bm([(ufoot, uz0), (ufoot, D_UP_TOP)]), coll, [m["white"]], v)
    slab(f"{p}roof_upper", coll, m["white"], m["white"], offset(ufoot, D_UP_ROOF_OVER), D_UP_ROOF[0], D_UP_ROOF[1], v)
    uwin = centred_box_mesh(f"{p}window_upper", SLAB_T, D_UP_WIN[0], D_UP_WIN[1], m["glass"])
    uwz = (D_UP_WIN_Z[0] + D_UP_WIN_Z[1]) / 2
    ys = sorted({-y for y in D_UP_WIN_Y} | set(D_UP_WIN_Y))
    window_slabs(f"{p}window_", coll, uwin, v, side_windows("upper", uhw, ys, uwz))
    ends += window_slabs(f"{p}window_", coll, uwin, v,
                         [(f"upper_fwd{k}", *w) for k, w in enumerate(d_end_facets(uc, uhw, D_END_FACETS, uwz))])
    udoor = centred_box_mesh(f"{p}door_upper", DOOR_T, D_UP_DOOR_W, D_DOOR_H, m["double_ended_door"])
    uend_y = uc + uhw * math.cos(math.radians(D_FACET / 2))
    ends.append(place(f"{p}door_upper_fwd", udoor, coll, v,
                      (0.0, uend_y + dc, D_UPPER_DECK - DOOR_SINK + D_DOOR_H / 2), math.pi / 2))

    # a pilothouse at each end of the upper cabin's roof, single windows, a
    # sun visor over its end; its mast and radar
    hw, y_in, y_out = D_PH
    ends.append(finish(f"{p}pilothouse_fwd", box_bm(-hw, hw, y_in, y_out, D_PH_BASE, D_PH_TOP), coll, [m["white"]], v))
    pwin = centred_box_mesh(f"{p}window_pilothouse", SLAB_T, D_PH_WIN[0], D_PH_WIN[1], m["glass"])
    pz = (D_PH_WIN_Z[0] + D_PH_WIN_Z[1]) / 2
    sc = slab_centre(SLAB_T)
    items = [(f"ph_fwd_front{k}", x, y_out + sc, pz, math.pi / 2) for k, x in enumerate(D_PH_FRONT_WIN_X)]
    items += side_windows("ph_fwd", hw, D_PH_SIDE_WIN_Y, pz)
    items += [(f"ph_fwd_back{k}", x, y_in - sc, pz, math.pi / 2) for k, x in enumerate(D_PH_BACK_WIN_X)]
    ends += window_slabs(f"{p}window_", coll, pwin, v, items)
    side_over, back_over = D_PH_ROOF_OVER
    ends.append(box(f"{p}roof_pilothouse_fwd", coll, m["white"], -hw - side_over, hw + side_over, y_in - back_over,
                    y_out + D_PH_VISOR, D_PH_ROOF[0], D_PH_ROOF[1], v))
    mx, my = D_MAST_AT
    zb0, zt, rb, rtop = D_MAST

    def circ(r):
        return [(mx + r * math.cos(math.tau * i / 8), my + r * math.sin(math.tau * i / 8)) for i in range(8)]

    ends.append(finish(f"{p}mast_fwd", rings_bm([(circ(rb), zb0), (circ(rtop), zt)]), coll, [m["mast"]], v))
    ends.append(box(f"{p}masthead_light_fwd", coll, m["mast"], mx - D_LIGHT / 2, mx + D_LIGHT / 2, my - D_LIGHT / 2,
                    my + D_LIGHT / 2, zt - LIGHT_SINK, zt - LIGHT_SINK + D_LIGHT, v))
    ends += radar(coll, m, v, f"{p}fwd_", D_RADAR_AT, D_RADAR, D_PH_ROOF[1])

    # the stack amidships, upright, its top black
    ax, ay = D_STACK
    z0, zband, z1 = D_STACK_Z
    oval = [(ax * math.cos(math.tau * i / 12), ay * math.sin(math.tau * i / 12)) for i in range(12)]
    finish(f"{p}stack", rings_bm([(oval, z0), (oval, zband), (oval, z1)], zones=(0, 1), cap_zones=(0, 1)), coll,
           [m["double_ended_stack"], m["double_ended_stack_top"]], v)

    # each end's bulwark, rising with the sheer, ramping up from low
    ys = [D_BULWARK_FROM] + [y for y in D_STATIONS if D_BULWARK_FROM < y < D_HALF_L]
    stbd = [(d_deck_hw(y) - M_EDGE_INSET, y) for y in ys]
    path = stbd + [(0.0, D_HALF_L - M_STEM_INSET)] + [(-x, y) for x, y in reversed(stbd)]
    zs = [d_deck_z(y) for _, y in path]

    def height(y):
        if y >= D_BULWARK_FULL:
            return M_BULWARK_H
        return M_BULWARK_FOOT + (M_BULWARK_H - M_BULWARK_FOOT) * (y - D_BULWARK_FROM) / (D_BULWARK_FULL - D_BULWARK_FROM)

    bot = [(x, y, z - M_EDGE_SINK) for (x, y), z in zip(path, zs)]
    top = [(x, y, z + height(y)) for (x, y), z in zip(path, zs)]
    ends.append(finish(f"{p}bulwark_fwd", ribbon_bm(bot, top, 0.0, M_BULWARK_T), coll, [m["white"]], v))

    # the upper deck's rail: the starboard half from the aft end's middle
    # facet to the forward end's, a gap at each for its stair; the port half
    # is the same rail turned
    k = int(round(180.0 / D_FACET))
    shw, risers, going = D_STAIR
    gap = shw + STAIR_GAP
    y_end = upper[k // 2][1]             # the forward end's middle facet, offset
    half = [(gap, -y_end)] + upper[k + 1 + k // 2 + 1:] + upper[:k // 2 + 1] + [(gap, y_end)]
    uz = D_UPPER_DECK
    rail = finish(f"{p}rail_upper_deck_starboard", ribbon_bm(at_z(half, uz - LAP_RAIL), at_z(half, uz + C_RAIL_H),
                                                              -RAIL_INSET, C_RAIL_T), coll, [m["white"]], v)
    turned(rail, f"{p}rail_upper_deck_port", coll, v)
    # each end's stair, from its end deck up to the upper deck's end facet,
    # built at the aft end and turned for the forward one
    y_top = -y_end
    foot_y = y_top + 0.05 - risers * going
    aft_stair = stair(coll, m, v, f"{p}aft_", m["double_ended_deck"], d_deck_z(foot_y), D_UPPER_DECK, risers, going,
                      shw, y_top)
    for o in aft_stair:
        turned(o, o.name.replace("_aft_", "_fwd_"), coll, v)
    # benches on each open end of the upper deck, facing the end
    bench = finish(f"{p}bench", bench_bm(*D_BENCH), None, [m["double_ended_seats"]], None, mesh_only=True)
    for r, y in enumerate(D_BENCH_ROWS):
        for side, sx in (("starboard", 1), ("port", -1)):
            ends.append(place(f"{p}bench_fwd_{r}_{side}", bench, coll, v, (sx * D_BENCH_X, y, D_UPPER_DECK)))

    for o in ends:
        name = o.name.replace("_fwd", "_aft") if "_fwd" in o.name else f"{o.name}_aft"
        turned(o, name, coll, v)


# --- reference ---------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm = prism_bm(ring, "z", 0.0, height - 0.40)
    body = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for vv in bm.verts:
        if vv not in body:
            vv.co.z += height - 0.17
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0)))
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    obj["kyt_collision"] = "none"
    obj.location = (x, y, z)
    coll.objects.link(obj)
    return obj


def outline(name, coll, pts, z=0.0):
    """An edge loop (no faces) in plan at height z."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in pts]
    for i in range(len(vs)):
        bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def build_reference(reference):
    outline("waterline", reference, rect(-22.0, 22.0, -26.0, 26.0), 0.0)
    outline("catamaran_38x10p6_at_waterline", reference, rect(-C_HALF, C_HALF, C_AFT_Y, C_TIP_Y))
    outline("monohull_36x9_at_waterline", reference, rect(-M_HW, M_HW, M_STERN_Y, M_STEM_Y))
    outline("catamaran_small_25x8_at_waterline", reference, rect(-S_HALF, S_HALF, S_AFT_Y, S_TIP_Y))
    outline("double_ended_36x10_at_waterline", reference, rect(-D_HW, D_HW, -D_HALF_L, D_HALF_L))
    hx, hy = PLACEHOLDER_HULL
    outline("placeholder_hull_17x46", reference, rect(-hx / 2, hx / 2, -hy / 2, hy / 2))
    outline("landing_deck_1p8m_starboard", reference, rect(C_HALF + C_FENDER[2] + 0.05, C_HALF + 12.0,
                                                           -20.0, 20.0), LANDING)
    figure("figure_1p7m", reference, 2.6, -16.5, MAIN_DECK)


# --- report ------------------------------------------------------------------

def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def report(variant):
    bpy.context.view_layer.update()
    objs = variant_objects(variant)
    tris, xs, ys, zs = 0, [], [], []
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
        for vv in o.data.vertices:
            w = o.matrix_world @ vv.co
            xs.append(w.x)
            ys.append(w.y)
            zs.append(w.z)
    print(f"{PROP}: {variant}: {len(objs)} parts, {tris} triangles, length {max(ys) - min(ys):.2f} "
          f"(y {min(ys):.2f}..{max(ys):.2f}), beam {max(xs) - min(xs):.2f}, air draft {max(zs):.2f}, "
          f"draft {-min(zs):.2f}, boarding (main deck at the doors) {MAIN_DECK:.2f}")
    return tris


# --- renders -----------------------------------------------------------------

def show_variant(variant):
    for vv in VARIANTS:
        for o in variant_objects(vv):
            o.hide_render = vv != variant


def render(folder, only=None):
    """The review frames into `folder`; `only` (variant names, and `lineup`
    for the two lineups) limits them."""
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    def stage_box(name, m_, x0, x1, y0, y1, z0, z1):
        obj = finish(name, box_bm(x0, x1, y0, y1, z0, z1), stage, [m_], None)
        return obj

    water_m = mat("_water", (0.05, 0.20, 0.36))
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-400, -400, 0), (400, -400, 0), (400, 400, 0), (-400, 400, 0))]
    bm.faces.new(vs)
    water = finish("_water", bm, stage, [water_m], None)
    ink = mat("_ink", (0.85, 0.10, 0.10))
    hx, hy = PLACEHOLDER_HULL
    ring = [stage_box("_ph_s", ink, -hx / 2, hx / 2, -hy / 2 - 0.15, -hy / 2, 0.0, 0.03),
            stage_box("_ph_n", ink, -hx / 2, hx / 2, hy / 2, hy / 2 + 0.15, 0.0, 0.03),
            stage_box("_ph_w", ink, -hx / 2 - 0.15, -hx / 2, -hy / 2, hy / 2, 0.0, 0.03),
            stage_box("_ph_e", ink, hx / 2, hx / 2 + 0.15, -hy / 2, hy / 2, 0.0, 0.03)]
    bar = [stage_box("_bar", ink, -7.5, -2.5, -24.6, -24.3, 0.0, 0.04)]
    for k in range(6):
        bar.append(stage_box(f"_tick{k}", ink, -7.5 + k - 0.05, -7.5 + k + 0.05, -24.9, -24.0, 0.0, 0.04))
    curve = bpy.data.curves.new("_label", "FONT")
    curve.body = "red: the 17 x 46 m placeholder; bar 5 m"
    curve.size = 0.9
    label = bpy.data.objects.new("_label", curve)
    label.location = (-1.5, -24.9, 0.05)
    curve.materials.append(ink)
    stage.objects.link(label)
    plan_only = ring + bar + [label]
    line = mat("_line", (0.95, 0.85, 0.10))
    wl_bar = stage_box("_waterline", line, 6.5, 6.6, -26.0, 26.0, -0.03, 0.03)
    pier_m = mat("_pier", (0.45, 0.42, 0.38))
    fig_m = mat("_figure_stage", (0.30, 0.22, 0.40))
    cat_stand = dict(side=C_HALF + C_FENDER[2] + 0.05, door=sum(C_DOOR_Y) / 2, wall=C_MAIN_HW,
                     fig_deck=(2.6, -16.5, MAIN_DECK))
    stand = {
        "catamaran": dict(cat_stand),
        "monohull": dict(side=M_HW + 0.10, door=sum(M_DOOR_Y) / 2, wall=M_MAIN_HW, fig_deck=(2.2, -15.5, MAIN_DECK)),
        "catamaran_b": dict(cat_stand),
        "catamaran_waterjets": dict(cat_stand),
        "catamaran_small": dict(side=S_HALF + S_FENDER[2] + 0.05, door=sum(S_DOOR_Y) / 2, wall=S_MAIN[0],
                                fig_deck=(*S_FIGURE, MAIN_DECK)),
        "double_ended": dict(side=D_HW + 0.10, door=sum(D_DOOR_Y) / 2, wall=D_MAIN[0],
                             fig_deck=(*D_FIGURE, d_deck_z(D_FIGURE[1]))),
    }
    for vv, s in stand.items():
        s["pier"] = stage_box(f"_pier_{vv}", pier_m, s["side"], s["side"] + 12.0, -22.0, 22.0, -3.0, LANDING)
        s["fig_pier"] = figure(f"_figure_pier_{vv}", stage, s["side"] + 0.9, s["door"] + 1.6, LANDING, mat=fig_m)
        s["fig_deck_obj"] = figure(f"_figure_deck_{vv}", stage, *s["fig_deck"], mat=fig_m)

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((0.45, 0.55, 0.70)).to_track_quat("Z", "Y").to_euler()
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
    scene.eevee.taa_render_samples = 48
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

    def stage_show(objs, on):
        for o in objs:
            o.hide_render = not on

    # the first two variants keep their full set of views; the four added
    # on 3 October get the four asked for, and the waterjets a look at them
    full = ("catamaran", "monohull")
    for vv in VARIANTS:
        if only is not None and vv not in only:
            continue
        show_variant(vv)
        for ww, s in stand.items():
            stage_show([s["pier"], s["fig_pier"], s["fig_deck_obj"]], False)
        s = stand[vv]
        stage_show(plan_only + [wl_bar], False)
        stage_show([water], True)
        stage_show([s["fig_deck_obj"]], True)
        shoot(f"{vv}_three_quarter", (29.0, 33.0, 11.5), (0.0, 0.5, 3.5), lens=35)
        if vv in full:
            shoot(f"{vv}_three_quarter_aft", (-27.0, -33.0, 10.5), (0.0, -2.0, 3.5), lens=35)
        # tipped 4 degrees down so the water plane hides what is under it
        shoot(f"{vv}_side_elevation", (120.0, 0.0, 4.5 + 120.0 * math.tan(math.radians(4.0))), (0.0, 0.0, 4.5),
              size=(2000, 800), ortho=42.0)
        if vv in full:
            shoot(f"{vv}_bow_low", (11.0, 60.0, 1.0), (0.0, 0.0, 2.2), lens=50)
        stage_show(plan_only, True)
        shoot(f"{vv}_plan", (0.0, 0.0, 120.0), (0.0, 0.0, 0.0), size=(1000, 1600), ortho=52.0)
        stage_show(plan_only, False)
        # from the pier at a standing eye, looking aft along the ship's side
        # to the boarding door, the figure beside it on the landing
        stage_show([s["pier"], s["fig_pier"]], True)
        shoot(f"{vv}_with_figure_at_the_landing", (s["side"] + 3.2, s["door"] + 12.0, LANDING + 1.6),
              (s["wall"] - 0.6, s["door"] - 2.0, 2.5), lens=30)
        stage_show([s["pier"], s["fig_pier"], water], False)
        if vv in full:
            stage_show([wl_bar], True)
            shoot(f"{vv}_hull_profile_no_water", (120.0, 0.0, 3.5), (0.0, 0.0, 3.5), size=(2000, 900), ortho=42.0)
            stage_show([wl_bar], False)
        if vv == "catamaran_waterjets":
            shoot(f"{vv}_stern_no_water", (-16.0, -44.0, 2.5), (0.0, -17.0, 0.6), lens=35)
        stage_show([water], True)

    # the lineup: all six side by side, bows forward, and the placeholder's
    # outline at the end of the row; moved for the picture only, never saved
    if only is not None and "lineup" not in only:
        show_variant(VARIANTS[0])
        return
    for ww, s in stand.items():
        stage_show([s["pier"], s["fig_pier"], s["fig_deck_obj"]], False)
    order = ("catamaran", "catamaran_b", "catamaran_waterjets", "catamaran_small", "monohull", "double_ended")
    spans = {}
    for vv in order:
        xs, ys = [], []
        for o in variant_objects(vv):
            o.hide_render = False
            for vtx in o.data.vertices:
                w = o.matrix_world @ vtx.co
                xs.append(w.x)
                ys.append(w.y)
        spans[vv] = (min(xs), max(xs), min(ys), max(ys))
    gap = 8.0
    widths = [spans[vv][1] - spans[vv][0] for vv in order] + [PLACEHOLDER_HULL[0]]
    x = -(sum(widths) + gap * (len(widths) - 1)) / 2
    labels = []
    for k, vv in enumerate(order + ("placeholder",)):
        if vv == "placeholder":
            off = x + widths[k] / 2
            for o in ring:
                o.location.x += off
                o.hide_render = False
            text = f"the placeholder\n17 x 46 m"
        else:
            x0, x1, y0, y1 = spans[vv]
            off = x - x0
            for o in variant_objects(vv):
                o.location.x += off
            text = f"{vv}\n{y1 - y0:.1f} x {x1 - x0:.1f} m"
            off = x + widths[k] / 2
        curve = bpy.data.curves.new(f"_lineup_label_{k}", "FONT")
        curve.body = text
        curve.size = 1.6
        curve.align_x = "CENTER"
        curve.materials.append(ink)
        lab = bpy.data.objects.new(f"_lineup_label_{k}", curve)
        lab.location = (off, -26.0, 0.05)
        stage.objects.link(lab)
        labels.append(lab)
        x += widths[k] + gap
    total = sum(widths) + gap * (len(widths) - 1)
    shoot("lineup_plan", (0.0, -3.0, 200.0), (0.0, -3.0, 0.0), size=(2400, 1100), ortho=total + 12.0)
    for lab in labels:
        lab.hide_render = True
    shoot("lineup_three_quarter", (0.0, 118.0, 46.0), (0.0, -4.0, 2.0), size=(2400, 1100), lens=24)
    show_variant(VARIANTS[0])


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
    export, reference = bpy.data.collections["export"], bpy.data.collections["reference"]
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"{PROP}: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [me for me in bpy.data.meshes if me.users == 0]:
        bpy.data.meshes.remove(me)

    m = mats()
    build_cat(export, m, BIG_CAT, "catamaran", "")
    source = [o for o in export.objects if o.get("kyt_variant") == "catamaran"]
    builders = {
        "monohull": lambda c: build_monohull(c, m),
        "catamaran_b": lambda c: build_catamaran_b(c, m, source),
        "catamaran_waterjets": lambda c: build_catamaran_waterjets(c, m, source),
        "catamaran_small": lambda c: build_cat(c, m, SMALL_CAT, "catamaran_small", "catamaran_small_"),
        "double_ended": lambda c: build_double_ended(c, m),
    }
    for vv in VARIANTS[1:]:
        coll = bpy.data.collections.new(f"variant_{vv}")
        export.children.link(coll)
        builders[vv](coll)
    build_reference(reference)
    bpy.context.view_layer.update()
    for vv in VARIANTS[1:]:
        eye = layer_collection(f"variant_{vv}")
        if eye is not None:
            eye.hide_viewport = True

    print(f"{PROP}: catamaran deck {2 * C_HALF:.1f} m wide, hulls {2 * C_HULL_HW:.1f} m at {2 * C_HULL_X:.1f} m centres, "
          f"wet deck {C_WET_DECK:.2f}, main deck {MAIN_DECK:.2f}, upper deck {C_UPPER_DECK:.2f}, wheelhouse floor "
          f"{C_WH_BASE:.2f}; monohull sheer {MAIN_DECK:.2f} to {m_sheer(M_STEM_Y):.2f} at the stem, upper deck "
          f"{M_UPPER_DECK:.2f}, pilothouse floor {M_PH_BASE:.2f}; the placeholder {PLACEHOLDER_HULL[0]:.0f} x "
          f"{PLACEHOLDER_HULL[1]:.0f} m, {PLACEHOLDER_TOP:.1f} m high")
    for vv in VARIANTS:
        report(vv)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
        render(argv[argv.index("--render") + 1], only)


main()
