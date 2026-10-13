"""Stage 3 of documentation/terrain-master-into-game-plan-2026-10-05.md: an authored edit
made on the grid master `terrain_world` carried onto the world terrain master's `Ground`,
the ground the game stands on (2026-10-05, Christina: "start stage 3").

    Blender --background assets/source/world_terrain_master.blend --python
        tools/blender/world_terrain_ground_edit.py -- --edit 4 [--dry] [--undo] [--render <folder>]

Edits 1-7 were made on the 25 m grid, which matches the game only at its sample points
(a median 0.35 m off around the park, up to 20 m at cliffs), so an edit is not copied as
a height change. It is carried as the surface it designed: wherever edit N moved the grid,
Ground takes the edited grid surface, faded in over the first `BLEND` of the change so the
edit's edge meets untouched ground smoothly. Nothing the edit did not reach moves.

Ground's lattice does not line up with the grid's (the reserve is 24 m out where the hill
lakes are), and its long triangles would climb back out of a cut up to a cell early: on
the first try K1 lost a 19 m band of shore, 3.8 ha. So the faces the edit reaches, and two
rings round them, are first refined: every original vertex and edge is kept, and points are
added on a `LATTICE` lattice and at the edit's own grid vertices, triangulated inside the
original faces (constrained Delaunay), each new corner taking its colour and UV from the
face it lies in. Only then is the surface cut or raised. Every vertex outside the region
keeps its position exactly, and the region's edge does not move.

Edit 4, the hill lakes: cut only. Each lake's water is then built on Ground itself, not
taken from the grid's plane: every Ground triangle connected to the lake's floor that lies
below the brim, clipped at the brim, walled off where the lake spills (the spill and the
creek below it, from edit 4's own `LAKES`) and where another source's ground stands over
Ground. The planes go in the `Lakes` collection, which the export now carries with
`Ground`; edit 4's design planes are hidden, since the game planes stand in their place.

Edit 2, the south beach front (2026-10-06), designed land where the game has open sea, beyond
Ground's edge, so it is built rather than cut: a new Ground object, `NEW_LAND`, the edited grid
from the coasts' shore wall out to the grid's seabed, running on below the waterline. See
`new_land`.

Edit 1, the south range blend (2026-10-06), lands on the range's and city's closed landform
shells, which overlap: in the zone it changed they are cut along its edge, emptied and capped,
and one sheet, `RANGE_BLEND`, takes the designed surface there. See `range_blend`.

Edit 6, the hillside regrade (2026-10-08), goes in with edit 7, its refinement of the band
beside the coast highway (`WITH`), measured from the grid before either. It reshapes ground the
highway's corridor covers, so Ground's edge along the corridor moves with it and the edit's
designed natural ground under the corridor is handed to the generator, which cuts the road's
sides down to it (`ROAD_NATURAL`, `road_natural`).

The hill lakes' banks (2026-10-11, `-- --edit lake_banks`, id `LAKE_BANKS_ID`) are no grid edit
either: edit 4 left K1 and L0 under walls 20 to 45 m tall, and a 45-degree bank now rises from each
waterline, the reserve above it cut down to it (`lake_banks_design`), carried as edits are.

The city's foothills (2026-10-11, `-- --edit city_cut`, id `CITY_CUT_ID`) are no grid edit either:
they buried the city's southern rows and stood over its streets in a straight edge, and they are cut
back with an exact Boolean (the shell is closed, so `carry` cannot take it) to a city on hills, loosely
San Francisco (`city_cut_design`); the city's blocks are then set on the ground by
`tools/blender/city_blocks_on_ground.py`.

The reserve's seams (2026-10-11, `-- --edit seams`, id `SEAMS_ID`) are no grid edit either: where the
generator's ground bands met at different heights the reserve stood against itself in sheer walls, and
their slope is limited round each (`seams_design`), carried as edits are.

The sea bluffs (2026-10-11, `-- --edit bluffs`, id `BLUFFS_ID`) move vertices only: the reserve's shore
walls, cut by the coast shelf, lean back to `BLUFF_ANGLE`, their feet out to sea under the shelf
(`bluffs`); the undo puts the feet and the walls' normals back. Edit 109 (2026-10-12, `-- --edit
bluffs_facing`, id `BLUFFS_FACING_ID`) turns those walls that were wound to the land, and the shore walls
still standing by coast north, to face the sea (`bluffs_facing`): windings and normals only.

The hillside's colours (2026-10-12, `-- --edit hillside_colours`, id `HILLSIDE_COLOURS_ID`): edit 6's
faces take their colours and texture coordinates again from the faces it replaced (`hillside_colours`),
since `carry` extrapolated them when it went in; colours only.

Range north's flanks (2026-10-12, `-- --edit range_flanks`, id `RANGE_FLANKS_ID`) are no grid edit
either: the block hill by the headland stood in big flat faces of 50 to 76 degrees, and the ground at
their foot is raised and their crest's edges cut until no flank is steeper than `RF_SLOPE`
(`range_flanks_design`), carried as the seams' are but on the faces one sees from above only, since
range north is a closed shell with internal sheets (`carry`'s `top_only`; an exact Boolean took those
sheets out across the whole shell). Its rocks move with the ground by `tools/blender/range_rocks_on_ground.py`.

Coast north's faces (2026-10-12, `-- --edit north_coast`, id `NORTH_COAST_ID`) are no grid edit either:
over the tunnel north of the headland and by the plug, coast north is cut back to 45 and 55 degrees from
what it keeps (`north_coast_design`), carried as range north's flanks are, on its top faces only.

Range north's east nose (2026-10-12, `-- --edit range_east`, id `RANGE_EAST_ID`) is no grid edit either:
the west end of range north's separate east piece, a ridge through the reserve, is cut back to 45 degrees
from the ground it keeps, the reserve's included (`range_east_design`), carried on its top faces, those
meeting its own sides included (`carry`'s `joined`), since the nose's faces run from the ridge down to them.

The coast shelf (2026-10-06, `-- --edit shelf`, id `SHELF_ID`) is no grid edit: every coast's
shore wall is cut just under the waterline and a shelf runs out from it under the water, so the
coast goes on below the sea instead of ending in a wall. See `coast_shelf`.

Logged and reversible: the faces each edit replaced are kept, hidden and unexported, as
`<object>__before_edit<N>` in the `Ground_history` collection; the new faces carry the
face attribute `authored_edit`; `--undo` puts the old faces back exactly, removes what the
edit added and unhides what it hid. The log is the scene's `kyt_ground_edits` and the
README text. Prints the proof: every vertex outside the edit's faces unchanged, the cut's
depth, each lake's area against the grid design. `--dry` reports without saving.
"""
import ast
import base64
import datetime
import hashlib
import json
import math
import os
import re
import sys

import numpy as np

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()
GRID = "terrain_world"
GROUND = "Ground"
HISTORY = "Ground_history"
LAKES_COLLECTION = "Lakes"
# The refined lattice inside an edit's region.
LATTICE = 8.0
# A lattice point nearer than this to a kept vertex, an edge point or a grid vertex is
# dropped, so the triangulation makes no slivers (they shade as spikes).
CROWD = 0.35 * LATTICE
# And an edit's own grid points and the lattice keep this far from every edge of the region's
# faces, which stay as constraints: a point a hair beside one makes a sliver that shades as a
# notch (2026-10-08: edits 6 and 7's 10 m and 3 m grids left 889 along the reserve's 24 m edges).
# Edits 4 and 5, carried before, had sparse grids and were not refined with it.
SEP = 1.0
# The bay's water (tools/gen_props.gd, mats["water"]), so lake and sea read as one water.
LAKE_COLOUR = (0.34, 0.44, 0.52, 1.0)
DESIGN_PLANES = {"K1": "water_K1_enlarged", "L0": "water_L0_enlarged"}
# Small still water an edit designed as a plane on the grid, built on Ground inside that
# plane's outline grown by `POOL_GROW`: {edit: {game name: design plane}}.
POOLS = {5: {"plunge_pool": "water_plunge_pool"}}
POOL_GROW = 2.0
# Render views per edit beyond the lakes: {name: ((x, z) centre, width across, eye level)}.
VIEWS = {109: {"facing_north_east": ((3050.0, -2300.0), 900.0, 10.0), "facing_by_coast_north": ((30.0, -2670.0), 400.0, 5.0)},
         108: {"range_east": ((40.0, -1220.0), 600.0, 160.0)},
         107: {"north_tunnel": ((-250.0, -1420.0), 800.0, 120.0), "north_plug": ((-560.0, -2260.0), 600.0, 60.0)},
         106: {"flanks": ((-660.0, -1100.0), 900.0, 120.0)},
         105: {"bluffs_east": ((3520.0, 20.0), 500.0, 10.0), "bluffs_north_east": ((3050.0, -2300.0), 900.0, 10.0)},
         104: {"seam_site4": ((1165.0, -270.0), 800.0, 300.0), "seam_site7": ((325.0, -1810.0), 700.0, 170.0)},
         103: {"city": ((-575.0, 2660.0), 1000.0, 0.0)},
         102: {"banks_K1": ((600.0, -471.0), 900.0, 79.7), "banks_L0": ((730.0, 206.0), 860.0, 92.0)},
         6: {"hillside": ((160.0, 570.0), 520.0, 30.0), "hillside_band": ((120.0, 600.0), 280.0, 25.0)},
         101: {"landform_bay": ((200.0, 3500.0), 1800.0, -8.0), "landform_plug": ((-730.0, -2220.0), 900.0, -8.0),
              "landform_south": ((-600.0, 6600.0), 1500.0, -8.0)},
         1: {"range_west": ((-1150.0, 5550.0), 1100.0, 40.0), "range_east": ((-150.0, 5800.0), 1500.0, 60.0)},
         100: {"shelf_north": ((-300.0, -1300.0), 1400.0, -8.0), "shelf_east": ((3300.0, 600.0), 1400.0, -8.0),
              "shelf_spur": ((500.0, 2450.0), 900.0, -8.0)},
         2: {"beach_north": ((130.0, 900.0), 900.0, -4.0), "beach_south": ((500.0, 1850.0), 900.0, -4.0)},
         5: {"falls": ((355.0, -290.0), 320.0, 41.9)}}
# Where a lake runs out over its spill: triangles past the spill (further from the lake's
# centre than the spill, within this of it) and within this of the creek below are dry.
SPILL_WALL = 60.0
CREEK_WALL = 35.0
# Where another source's ground stands over Ground (the range's hills east of L0 stand up
# to 130 m over the copied reserve), the grid, sampled from the game's top ground, is the
# rim: water stands only where the edited grid is within this of the brim or below it, which
# runs the water a little under that ground rather than leaving a dry strip below the brim
# where the 25 m grid is unsure of its edge. Water still crosses only Ground below the brim.
TOP_RIM = 5.0
MIN_CHANGE = 0.01
# Over the first this-many metres of an edit's change, Ground fades from its own surface to
# the edit's, so the edge of a cut meets the untouched ground without a step.
BLEND = 2.0
# How far an edit may move Ground against its own direction to meet the design.
AGAINST = 1.0
# The bound `designed` applies. An edit that only lays ground back sets it to nothing
# (`lake_banks`), so ground under another body is never lifted to meet a cut.
against = AGAINST
# Edits that build land where the game has open sea, beyond Ground's own edge: {edit: the new
# Ground object}. Edit 2, the south beach front (option B), lies wholly beyond the shore.
NEW_LAND = {2: "terrain_south_beach_front"}
# The generator's coasts end at the shore in a vertical wall down to this depth, its skirt.
SKIRT_Z = -13.5
# The sea and the beach front's bench are the edit's own (`world_terrain_coast_extension.py`'s
# `SEA_LEVEL` and `BENCH_H`), read where they are used.
# The bench meets the shore's top edge over a bank this wide (a smoothstep, so it leaves the
# shore level and lands on the bench without a crease).
RAMP = 10.0
# New land's colours: the shore's own planting on the bench and its bank, the generator's beach
# sand (`gen_props.gd`, the 02B beaches) from the bench's crest down past the waterline, and its
# sea-cliff colour (`REBUILD_SEA_CLIFF_COLOUR`) once the shelf is well under water.
SAND = (0.78, 0.72, 0.58)
SEABED = (0.47, 0.44, 0.39)
# The beach's crest: the bench is -4 at the bluff falling 1 % seaward, up to 86 m, to a crest
# 3 m over the sea; this takes the lowest. Sand begins here, and wherever the design stands
# above it against the shore wall, the bank climbs to the wall's top.
CREST = -4.6
SAND_FROM = (CREST + 0.4, CREST)
# An edge this close under the wall's top is the top: no sliver of wall is left above it.
SNAP = 0.05
SEABED_FROM = (-8.5, -10.5)
# A face flatter than this is a wall, not ground one could stand on (`world_terrain_source.gd`'s
# `MIN_UP`).
MIN_UP_FACE = 0.05
# Each end of new land meets the shore wall at least this far under the sea.
END_UNDER = 0.5
JOIN = 0.01
# The coast shelf (2026-10-06), a ground job that is no grid edit, so it takes an id clear of
# them: `--edit shelf`.
SHELF_ID = 100
SHELF = "terrain_coast_shelf"
# The wall keeps this much below the waterline, so the water meets the wall and not the crease
# where the shelf begins.
SHELF_UNDER = 0.5
# How far out the shelf runs, and its depth there (Godot y): 8.5 m of water, the generator's
# skirt going down to -13.5 and edit 2's shelf to about -14.
SHELF_W = 60.0
SHELF_DEPTH = -16.0
# Rows out from the wall, metres; a row point nearer than min(CROWD + SHELF_SPREAD * distance,
# 0.45 * the gap from the row before) to one already placed is dropped.
SHELF_ROWS = (3.0, 8.0, 15.0, 25.0, 40.0, 60.0)
SHELF_SPREAD = 0.3
SHELF_LONGEST = 60.0
# The park's own west shore is left alone: its rebuild footprint grown by this, the margin
# `footprint_test` gives it.
SHELF_CLEAR = 45.0
# A shore whose top colour is within this of the generator's beach sand has a sandy shelf.
SANDY = 0.15
# Edit 1, the south range blend (2026-10-06), lands on the range's and city's landforms, which
# joined Ground that day as their sources drew them: closed shells (a top, sides straight down,
# a floor at -11) lying over one another. Carried shell by shell, a cut would bare the shell
# under it and a raise would leave a slot against the next one's side. So in the zone the edit
# changed, Ground becomes one sheet, this object: every shell is cut along the zone's edge,
# emptied inside it and capped where it was cut, so each is still closed, and the sheet takes the
# designed surface inside and meets the topmost shell's cut edge, edge for edge. See `range_blend`.
RANGE_BLEND = {1: "terrain_south_range_blend"}
# The sheet's lattice inside the zone: the grid's own 25 m, halved.
RANGE_LATTICE = 12.5
# Where the zone's edge crosses a shell's straight side, the ground steps down it; the sheet, a
# surface over the plan, takes the step over twice this of its edge.
JUMP = 0.01
OFF_LINE = 0.05
# The sheet's lattice by the coastal branch's road box (see `range_blend`).
HELD_LATTICE = 4.0
# Over this far in from the zone's edge the edit fades in, and the sheet has rows along it,
# points this far apart.
EDGE_FADE = 12.5
EDGE_ROW = 6.0
# The range's level bands (background_distant_range_south's `toe_rock_bands`): a sheet face that
# was in one takes its band again from its height after the edit.
TOE_BANDS = ((16.0, "distant_massif_toe_dark"), (32.0, "distant_massif_toe_rock"),
             (43.0, "distant_massif_toe_rock_forest_1"), (54.0, "distant_massif_toe_rock_forest_2"),
             (65.0, "distant_massif_toe_rock_forest_3"), (math.inf, "distant_massif_forest"))
# Land the edit made out of the sea is the range's cove sand below this, its bands above.
SAND_BELOW = -4.0
# The landforms' coasts (2026-10-08), the coast shelf's sibling: `-- --edit landform_shelf`, one
# more object, the landform shells themselves untouched. See `landform_shelf`.
LANDFORM_SHELF_ID = 101
LANDFORM_SHELF = "terrain_landform_shelf"
# Shore points along a landform's side, at most this far apart, as the generator's wall panels are.
LANDFORM_SHORE_STEP = 8.0
# The edits this script knows how to carry, each in its own Stage 3 batch.
# Edit 7 (2026-10-03) refined edit 6, the hillside regrade: the band beside the coast highway
# that edit 6 had to hold, re-cut at 3 m on faces of its own. It is the rest of edit 6's design,
# not a design of its own, so the two go onto Ground together as edit 6, measured from the grid
# as it stood before either. Edit 7's own heights before it are edit 6's surface, and its band's
# old faces are kept on the grid as `kyt_<tag>_removed_faces`: {edit: (its refinement, face tag)}.
WITH = {6: (7, "edit7_face")}
# Edit 6 reshapes ground the coast highway's corridor covers: the hill's old surface runs down into
# the cutting's batter, which the generator builds, 15 to 20 m wider than the strip edit 7 kept.
# Christina, 2026-10-08, "let the slope follow": Ground's edge along the corridor moves with the
# edit instead of being held (by `design_at`'s weight, uncapped, as the corridor's side will), and
# the edit's designed natural ground under the corridor goes to the game beside Ground, so the
# generator cuts the road's sides down to it; the road's own level never reads it. The object
# stands on the designed ground and carries, as its u texture coordinate, how far the design
# governs at each point, 1 inside the edit fading to 0 where it leaves the ground as it was; it is
# no ground one stands on (`kyt_collision=none`, hidden in the game). {edit: that object}.
ROAD_NATURAL = {6: "corridor_natural_edit6"}
EARTHWORKS = "Earthworks"
ROAD_NATURAL_STEP = 3.0
# A lattice point this close to Ground's edge is dropped, so the triangulation makes no slivers.
ROAD_NATURAL_CLEAR = 1.0
# What the grid may name under a corridor point the design governs: the corridor, and the ground
# its edge faces straddle. Anything else there (a tunnel lid, an anchor) is refused.
ROAD_NATURAL_OWNERS = ("terrain_road_corridor", "terrain_world_mainland_reserve")
# The hill lakes' banks laid back (2026-10-11, kind A of the sheer-face survey,
# `documentation/screenshots/sheer-faces-survey-2026-10-11/`; Christina chose 45° banks once 1:2 was
# measured at 83 ha of hill cut, up to 104 m). Edit 4 took the hill down to each lake's 1:3 bowl
# inside one 25 m grid cell, so most of K1's and L0's shores rise straight out of the water 20 to
# 45 m. A bank now rises from each lake's waterline, `BANK_LIP` over its brim, at `BANK_SLOPE`, and
# the reserve wherever it stands above that bank within `BANK_REACH` of the water is cut down to it.
# The water, its level and its outline stay: nothing is cut below the brim and the lip. Held: the
# falls (edit 5's faces and `BANK_FALLS` round them, designed steep), `BANK_SEAM` round Ground's open
# edges (the road corridor), and every other body. `-- --edit lake_banks`.
LAKE_BANKS_ID = 102
BANK_SLOPE = 1.0
BANK_LIP = 0.3
BANK_REACH = 220.0
BANK_STEP = 4.0
BANK_FALLS = 60.0
BANK_SEAM = 30.0
# The bank's contours follow the waterline, which edit 4 drew in 8 m steps, and the bare bank rose in
# flutes from every step; smoothed over this it reads as one slope.
BANK_SMOOTH = 12.0
# Godot x0, x1, z0, z1: both lakes and `BANK_REACH` round them.
BANK_BOX = (150.0, 1250.0, -950.0, 650.0)
# The city's foothills cut back (2026-10-11, kind D of the sheer-face survey; Christina: "Cut the
# hill off the city"). The city stands on the peninsula at 0 m, every block's base at 0, and the
# foothills, which reach north over the peninsula to a straight edge at z 2560, buried 28 of its
# blocks and towers up to 43 m deep and stood over its streets in that edge, 16 to 20 m tall (the
# clash logged 2026-09-30). The city's extent is its blocks and towers grown by `CITY_MARGIN`, the
# streets between them filled in (`CITY_CLOSE`) and its holes filled; under the peninsula the ground
# goes `CITY_UNDER` under its top. Only the foothills are cut, never raised; the city's source is
# read here, and its blocks are set on the result by their own tool. `-- --edit city_cut`.
CITY_CUT_ID = 103
CITY_SOURCE = "far_shore_city_relocation.blend"
CITY_SHELL = "southern_city_range_foothills"
CITY_PENINSULA = "relocated_city_peninsula"
# The bypass is not among them: it stands on its own closed earthwork, and the foothills were only
# ever benched under it so as not to stand through it.
CITY_ROADS = ("bridge_city_intersection", "bridge_city_southern_offramp", "city_highway_extension")
# Not a pit with a wall round it (Christina, of the first cut, the city's whole extent flat with the
# hill rising behind it at 1:1.5: "the abrupt cliff is odd", then "model it on san francisco
# loosly"): the city's waterfront, where the foothills never reached, stays flat, and from it the
# ground climbs through the city at street grades, level at first and steepening over `CITY_TOE` to
# `CITY_GRADE`; past the city's edge the hills rise by `CITY_HILL` more. Where the cut meets the hill
# as it stood the crease is rounded over `CITY_CREST` of height. The blocks are then set on it
# (`tools/blender/city_blocks_on_ground.py`).
CITY_GRADE = 1.0 / 4.0
CITY_TOE = 60.0
CITY_HILL = 1.0 / 4.0
CITY_CREST = 8.0
# The ground falls away from under a road the foothills hold up at this, and the foothills' straight
# north edge, the survey's site 30 west of the city, comes down to the peninsula and the beach at it,
# from a foot `CITY_EDGE_TOE` long. The off-ramp's trench (2026-10-04, 2:1 walls) is left as it is:
# roads go on through these foothills in tunnels (Christina, 2026-10-11: "we can put a tunnel through
# those foothills for more roads"), and the off-ramp ends at the hill where a portal would stand.
CITY_SLOPE = 1.0 / 2.0
CITY_EDGE_TOE = 20.0
CITY_STEP = 4.0
CITY_MARGIN = 6.0
CITY_CLOSE = 40.0
CITY_UNDER = 0.3
# The 2026-10-04 bench rule for the city's roads in these foothills.
CITY_ROAD_UNDER = 0.45
CITY_ROAD_GROW = 2.0
# A road the peninsula holds within this of its surface needs no foothills under it.
CITY_ROAD_HELD = 1.0
# The extent's edge, drawn on the raster, is rounded over this before the slope is laid from it.
CITY_SMOOTH = 8.0
# Beyond the city, until the slope stands over every foothill.
CITY_PAD = 320.0
# The reserve's seams blended (2026-10-11, kind B of the sheer-face survey; her "do the next
# recommended part"): where the generator's ground bands meet at different heights the reserve stands
# against itself in walls up to 36 m: a straight north-south wall for 480 m high in the hills east of
# the lakes (site 4), a sawtooth scarp north of the park (site 7) and a short one north of that (site
# 20). No edit made them; the copy carried them from the generator. Within `SEAM_REACH` of every sheer
# cell the ground's slope is limited to `SEAM_SLOPE`, symmetrically (the top of a too-steep pair comes
# down and its foot comes up by equal parts), alternated with `SEAM_PASSES` of smoothing of how far it
# moved, for `SEAM_ROUNDS` rounds, the limit last; a single blur did not do it, since site 4's wall stands on a
# 43-degree flank. Held: `SEAM_HOLD` round Ground's open edges, lake water, and anywhere another body
# stands over the reserve: site 4's wall is the reserve's face rising 80 m out of
# `background_distant_range_middle`, which covers its foot, so there it is laid back by cutting alone.
# `-- --edit seams`.
SEAMS_ID = 104
# Godot x0, x1, z0, z1 round each site, `SEAM_REACH` and the smoothing beyond it.
SEAM_SITES = {"site4": (1000.0, 1330.0, -620.0, 80.0), "site7": (20.0, 630.0, -2000.0, -1620.0),
              "site20": (-60.0, 220.0, -2320.0, -2110.0)}
SEAM_STEP = 4.0
SEAM_SHEER = 1.5
SEAM_SLOPE = 1.2
SEAM_REACH = 100.0
SEAM_ROUNDS = 4
SEAM_PASSES = 20
SEAM_FINISH = 6
SEAM_FINISH_SLOPE = 1.42
SEAM_HOLD = 30.0
# The sea bluffs laid back (2026-10-11, kind E of the sheer-face survey; her "do the next part"):
# along the reserve's coasts the generator's shore wall stands vertical from the land's edge to
# `SHELF_UNDER` under the water, where the coast shelf (`SHELF_ID`) cut it and runs on, 15 to 25 m tall
# along the east and north-east coasts and lower all round. The land's edge stays where it is and each
# wall's foot moves out to sea until the face leans back to `BLUFF_ANGLE`, its foot `BLUFF_UNDER` under
# the shelf there, so the shelf itself is not touched (the headland fork swaps it whole). A foot that
# would cross a neighbour's or come under land is brought back in until it does not. Only the reserve,
# and not within `BLUFF_CLEAR` of coast north (the fork's): `-- --edit bluffs`.
BLUFFS_ID = 105
# Just under the sheer-face survey's line (a drop of 1.5 times the distance), as the seams finish; the
# survey proposed about 60, which a bluff over 15 m tall still crosses.
BLUFF_ANGLE = 55.0
BLUFF_UNDER = 0.3
BLUFF_OBJECT = "terrain_world_mainland_reserve"
BLUFF_CLEAR = 200.0
# The bluffs turned to face the sea (2026-10-12): `bluffs` laid each wall back as it was wound, and the
# north-east coast's and more were wound to the land. Standing, that was a wall the sea saw from behind;
# laid back, 1,072 faces (12.1 ha) faced down where they are the top ground. The game's collision is
# derived at export as a one-sided concave shape, so anything coming down onto them went through. Each
# such face of the reserve's shore walls, laid back or still standing (by coast north, inside
# `BLUFF_CLEAR`), is wound to face the sea and shaded flat along it; no vertex moves:
# `-- --edit bluffs_facing`.
BLUFFS_FACING_ID = 109
# How far in front of and behind a face its sides are read: a wall faces the land when ground stands
# over the point in front of it and none over the point behind.
FACING_PROBE = 0.6
# The hillside's colours sampled again (2026-10-12): edit 6, the hillside regrade (`a94abf2`), was carried
# before `carry` held a new corner's weights to its parent face, and the triangulator named parents its
# corners lay outside of: 11,672 of its 13,209 faces took colours of -10,000 to +10,000, which the game
# (its land coloured by its vertex colours) drew black and white, and texture coordinates off the plan.
# Every corner of edit 6's faces takes both again from the faces it replaced, kept in `Ground_history`,
# as `carry` now samples them; nothing moves: `-- --edit hillside_colours`.
HILLSIDE_COLOURS_ID = 110
HILLSIDE_EDIT = 6
HILLSIDE_OBJECT = "terrain_world_mainland_reserve"
# Range north's flanks (2026-10-12, kind C of the sheer-face survey; her "do the next part"): the block
# hill by the headland, range north's peak of 262 m, stood on flanks of big flat triangles meeting in
# straight creases, 58 degrees on average down its west face and 50 down its north, up to 76, until no
# flank is steeper than `RF_SLOPE`: within `RF_REACH` of each of the hill's sheer cells, on range north's
# own land, the slope limited symmetrically as the seams' was, cut and fill (the crest's edges round over,
# the foot comes out; holding the crest and filling alone measured 11 million m3, up to 139 m deep, and ran
# into the road), alternated with smoothing over what moved, and limited again. It stays `RF_ROAD_CLEAR`
# from the coast highway's centreline, so range north under the road corridor's hole, which the
# generator builds the corridor on, does not change (the headland fork's lesson). `-- --edit range_flanks`.
RANGE_FLANKS_ID = 106
RF_OBJECT = "background_distant_range_north"
# Godot x0, x1, z0, z1: where the hill's sheer cells are (the survey's sites 2 and, at its south-east foot,
# 19), and the raster the design is laid out on.
RF_SEED = (-820.0, -400.0, -1400.0, -740.0)
RF_BOX = (-1100.0, -300.0, -1700.0, -640.0)
RF_STEP = 4.0
# A drop of more than this to a neighbour `RF_STEP` away is sheer (56 degrees, the survey's line).
RF_SHEER = 6.0
# 45 degrees, as the lake banks were laid back (her choice, 2026-10-11).
RF_SLOPE = 1.0
# The share of each correction taken off the high side; the rest raises the low side. A half, as the seams:
# the crest comes down 30 m, from 273 to 242, since a hill that tall has no room for 45-degree flanks
# under its peak (a quarter ran the east foot 40 m up against the road's clearance; fill alone, 139 m).
RF_CUT = 0.5
RF_REACH = 160.0
# The headland fork's north shore (C1, approved 2026-10-09) lies south of this; it is not reshaped again.
RF_SOUTH = -690.0
RF_ROAD = "coast_highway_centreline"
RF_ROAD_CLEAR = 60.0
# And this far from any point of the design grid the road corridor or a tunnel lid owns: the grid's 25 m,
# the headland fork's 12 m guard and the delta's 8 m cell. The corridor and lids reach 115 m from the
# centreline by the tunnel north of the hill, and 60 m let the corridor's side move 52 mm.
RF_ROAD_GUARD = 45.0
RF_ROAD_OWNERS = ("terrain_road_corridor", "terrain_tunnel_lids")
# Rounds of the limit, with `RF_PASSES` of smoothing between them and `RF_FINISH` before the last, as the seams.
RF_ROUNDS = 4
RF_PASSES = 20
RF_FINISH = 6
RF_EPS = 0.05
# The change fades in over this from the edge of where it may move, so held ground it meets steep (the
# headland fork's caps at the hill's south-east foot, the south-west corner at `RF_SOUTH`) is met, not stepped.
RF_TAPER = 24.0
# A face steeper than this (81 degrees) is a wall, not ground one sees from above, even where a ray from
# above reaches it: the fork's caps at the hill's south-east foot stand in such walls, and taken in, their
# thin outlines overlapped the ground at their top and foot and the refinement crumpled them.
TOP_MIN_NZ = 0.15
# Ground is held this far round every place range north's top meets its walls, underside or caps.
RF_JOIN_HOLD = 24.0
# Cells this many in from range north's own edge (the sea, or other ground over it), so its sides never move.
RF_INSET = 3
# Coast north's faces (2026-10-12, kind G and the plug's sawtooth of the sheer-face survey, her choices):
# over the twin-bore tunnel north of the headland, coast north's face stands 20 to 70 m over the
# generator's own ground on the tunnel (its lids, which stay as they are) and on up to its 200 m
# plateau; by the plug its sea face rises from the shore to 110-150 m at up to 71 degrees in a sawtooth.
# Cut only, on coast north alone: in each zone the ground is brought down until nothing is steeper than
# the zone's slope (`NC_ZONES`: 45 degrees over the tunnel, 55 by the plug, as the bluffs), laid out
# from what it keeps: `NC_HOLD` round Ground's open edges (where coast north meets the corridor and the
# lids, which never move) and, by the plug, the shore. Within `NC_REACH` of the zone's sheer cells,
# faded out over `NC_TAPER` at the edge, its crest rounded over `NC_CREST`. `-- --edit north_coast`.
NORTH_COAST_ID = 107
NC_OBJECT = "terrain_world_coast_north"
NC_STEP = 4.0
# Godot x0, x1, z0, z1 and the slope (rise over run) of each zone.
NC_ZONES = {"tunnel": ((-460.0, -50.0, -1800.0, -1050.0), 1.0),
            "plug": ((-700.0, -420.0, -2440.0, -2080.0), math.tan(math.radians(53.0)))}
# By the plug, 55 degrees as the bluffs (her choice) as built: laid out at 53 on the 4 m raster, since the faces
# carried onto it stand a degree or two steeper than the raster's slope (at 55, patches over the survey's line).
NC_REACH = 160.0
NC_HOLD = 12.0
# Ground this low by the plug is the shore its face is laid back from.
NC_SHORE = 2.0
NC_TAPER = 24.0
NC_CREST = 8.0
# Coast north's sawtooth is teeth of near-vertical faces: here only a face within a degree of vertical is a
# wall (`carry`'s `top_min_nz`), and the design wins outright (`against`), so a notch between teeth fills to
# the cut rather than staying under it.
NC_TOP_MIN_NZ = 0.02
NC_AGAINST = 1e9
# Ground is held this far round every place coast north's top meets a wall or skirt of its own.
NC_JOIN_HOLD = 8.0
# Range north's east nose (2026-10-12), G4 of the sheer-face survey. Range north's east piece is a closed
# shell of its own, an 880 m ridge running east from x -44 through the reserve, standing 25 m over the
# reserve's ground under it; at its west end it stops in a nose about 160 m tall of faces at 59 to 71
# degrees whose foot meets the reserve at about 100 m, 190 m and more from the corridor. Cut only, at 45
# degrees as the block hill (her angle), laid out from the ground it keeps, the reserve's included: the
# piece has no land of its own past its foot, so nothing can be filled there. Never within `RE_SKIN` of the
# reserve under it, so the two never lie together. `-- --edit range_east`.
RANGE_EAST_ID = 108
RE_OBJECT = RF_OBJECT
RE_STEP = 4.0
# Godot x0, x1, z0, z1: the piece's west end; range north's main body ends at x -64.
RE_ZONE = (-50.0, 250.0, -1420.0, -1000.0)
RE_SLOPE = 1.0
RE_REACH = 160.0
RE_HOLD = 12.0
RE_SKIN = 1.0
RE_UNDER = 8.0
RE_TAPER = 24.0
RE_CREST = 8.0
CARRIED = (1, 2, 4, 5, 6, SHELF_ID, LANDFORM_SHELF_ID, LAKE_BANKS_ID, CITY_CUT_ID, SEAMS_ID, BLUFFS_ID,
           RANGE_FLANKS_ID, NORTH_COAST_ID, RANGE_EAST_ID, BLUFFS_FACING_ID, HILLSIDE_COLOURS_ID)


def argv():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"edit": None, "dry": "--dry" in a, "undo": "--undo" in a, "render": None}
    if "--edit" in a:
        v = a[a.index("--edit") + 1]
        out["edit"] = {"shelf": SHELF_ID, "landform_shelf": LANDFORM_SHELF_ID, "lake_banks": LAKE_BANKS_ID,
                       "city_cut": CITY_CUT_ID, "seams": SEAMS_ID, "bluffs": BLUFFS_ID,
                       "range_flanks": RANGE_FLANKS_ID, "north_coast": NORTH_COAST_ID,
                       "range_east": RANGE_EAST_ID, "bluffs_facing": BLUFFS_FACING_ID,
                       "hillside_colours": HILLSIDE_COLOURS_ID}.get(v) or int(v)
        for edit, (also, _tag) in WITH.items():
            if out["edit"] == also:
                raise SystemExit("edit %d refines edit %d and is carried with it: --edit %d" % (also, edit, edit))
    if "--render" in a:
        out["render"] = a[a.index("--render") + 1]
    return out


def edit_constant(script, name):
    """A literal assigned at the top of a grid edit script, read without running it."""
    tree = ast.parse(open(os.path.join(HERE, script)).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit("%s has no %s" % (script, name))


def ground_objects():
    return [o for o in bpy.data.collections[GROUND].all_objects if o.type == 'MESH']


def coords(ob):
    co = np.zeros(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def grid_surfaces(edit):
    """BVH trees of the grid as edit `edit` left it and as it stood before it, the plan
    box the edit's vertices cover, and those vertices' plan positions. An edit carried `WITH`
    its refinement is measured as both left the grid against the grid before either."""
    ob = bpy.data.objects[GRID]
    me = ob.data
    M = ob.matrix_world
    co = coords(ob)
    ed = np.zeros(len(me.vertices), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", ed)
    pre = np.zeros(len(me.vertices))
    me.attributes["height_pre_edit"].data.foreach_get("value", pre)
    sel = ed == edit
    if not sel.any():
        raise SystemExit("the grid has no vertex of edit %d" % edit)
    now = [M @ Vector(v) for v in co]
    before = [Vector((v.x, v.y, pre[i] if sel[i] else v.z)) for i, v in enumerate(now)]
    polys = [tuple(p.vertices) for p in me.polygons]
    before_polys = polys
    moved = sel
    if edit in WITH:
        also, tag = WITH[edit]
        if not (ed == also).any():
            raise SystemExit("the grid has no vertex of edit %d, which edit %d is carried with" % (also, edit))
        refined = np.zeros(len(me.polygons), dtype=np.int32)
        me.attributes[tag].data.foreach_get("value", refined)
        # The refinement's faces are none of the grid before it; the faces it dropped are.
        before_polys = [tuple(p.vertices) for p in me.polygons if not refined[p.index]] + [
            tuple(s["v"]) for s in json.loads(ob["kyt_%s_removed_faces" % tag])]
        moved = sel | (ed == also)
    idx = np.nonzero(moved)[0]
    xs = np.array([now[i].x for i in idx])
    ys = np.array([now[i].y for i in idx])
    box = (xs.min() - 60.0, xs.max() + 60.0, ys.min() - 60.0, ys.max() + 60.0)
    points = [Vector((now[i].x, now[i].y)) for i in idx]
    return BVHTree.FromPolygons(now, polys), BVHTree.FromPolygons(before, before_polys), box, points


def height(tree, x, y):
    hit = tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
    return None if hit[0] is None else hit[0].z


def design_at(now_t, pre_t, x, y):
    """The edited grid surface at (x, y), how far it governs there (1 where the edit moved the
    grid by `BLEND` or more, fading to 0 where it did not move it) and the grid's move; None
    where the edit left the grid alone."""
    t = height(now_t, x, y)
    p = height(pre_t, x, y)
    if t is None or p is None:
        return None
    d = t - p
    if abs(d) <= MIN_CHANGE:
        return None
    return t, min(1.0, abs(d) / BLEND), d


def designed(now_t, pre_t, x, y, z):
    """Where edit N puts ground that stands at z at (x, y): unchanged where the edit left
    the grid alone, and the edited grid surface where it moved the grid by `BLEND` or more,
    faded between. The design wins outright inside the edit even where Ground stood a few
    tenths below it: taking the lower of the two at every point (the first try) flipped
    between them along every bank, by the grid's own 0.3 m, and serrated it."""
    tw = design_at(now_t, pre_t, x, y)
    if tw is None:
        return z
    t, w, d = tw
    # A cut never lifts Ground by more than the grid's own error, nor a raise lowers it:
    # where another source's ground was the grid's top (the range's hills over the reserve),
    # Ground lies far below the design and stays there.
    change = t - z
    if d < 0.0:
        change = min(change, against)
    else:
        change = max(change, -against)
    return z + w * change


def edge_on(tri):
    """A triangle seen edge-on from above (a wall): next to no area in plan for its edges' length."""
    a, b, c = tri
    v0x, v0y = b.x - a.x, b.y - a.y
    v1x, v1y = c.x - a.x, c.y - a.y
    return abs(v0x * v1y - v1x * v0y) <= 1e-6 * (v0x * v0x + v0y * v0y + v1x * v1x + v1y * v1y)


def plan_weights(tri, p):
    """The barycentric weights of `p` in triangle `tri` seen from above; a triangle seen edge-on (a
    wall) gives all the weight to its corner nearest `p` in plan."""
    if edge_on(tri):
        d = [(q.x - p.x) ** 2 + (q.y - p.y) ** 2 for q in tri]
        return tuple(1.0 if k == d.index(min(d)) else 0.0 for k in range(3))
    a, b, c = tri
    v0x, v0y = b.x - a.x, b.y - a.y
    v1x, v1y = c.x - a.x, c.y - a.y
    den = v0x * v1y - v1x * v0y
    v2x, v2y = p.x - a.x, p.y - a.y
    u = (v2x * v1y - v1x * v2y) / den
    w = (v0x * v2y - v2x * v0y) / den
    return (1.0 - u - w, u, w)


def clamped(bary):
    """Weights held to the triangle: none negative, summing to one."""
    b = [max(0.0, x) for x in bary]
    s = sum(b)
    return tuple(x / s for x in b) if s > 0.0 else (1.0, 0.0, 0.0)


def corner_key(co, centre):
    # Height too: a shore wall's top and foot share their plan position, and without it their
    # normals were swapped between them (fixed 2026-10-06; edits 4 and 5 had done it).
    return (round(co.x, 3), round(co.y, 3), round(co.z, 3), round(centre.x, 3), round(centre.y, 3), round(centre.z, 3))


def history_collection():
    c = bpy.data.collections.get(HISTORY)
    if c is None:
        c = bpy.data.collections.new(HISTORY)
        bpy.context.scene.collection.children.link(c)
        c.hide_viewport = True
        c.hide_render = True
    return c


def carry(ob, edit, now_t, pre_t, box, grid_points, dry, top_only=False, top_min_nz=None, joined=False):
    """Refine and cut one Ground object. Returns its report, or None if untouched. `top_only` (a closed
    shell, range north) takes only the faces one sees from above, never its sides or underside; a face
    flatter than `top_min_nz` (`TOP_MIN_NZ` unless given) is a wall. `joined` takes in the top faces with a
    corner on a wall too; those corners stay where they are, the walls hanging from them untouched."""
    if top_min_nz is None:
        top_min_nz = TOP_MIN_NZ
    me = ob.data
    if ob.matrix_world != ob.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin; Ground objects hold world positions" % ob.name)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    top = None
    if top_only:
        ftree = BVHTree.FromBMesh(bm)
        top = set()
        for f in bm.faces:
            c = f.calc_center_median()
            hit = ftree.ray_cast(Vector((c.x, c.y, 5000.0)), Vector((0.0, 0.0, -1.0)))
            # By height, not by which face the ray names: a sliver's centre ray lands on its neighbour.
            if hit[0] is not None and abs(hit[0].z - c.z) < 0.01 and f.normal.z >= top_min_nz:
                top.add(f.index)
        # A top face with a corner on a wall, the underside or a cap stays out of the region (unless `joined`):
        # the ground at a wall's top and foot lie within a metre of each other in plan, and the plan's
        # triangulation joined them in teeth.
        # Read off the top as it was, not as faces leave it (that cascaded across the whole shell).
        on_wall = set()
        for v in bm.verts:
            ins = [f.index in top for f in v.link_faces]
            if any(ins) and not all(ins):
                on_wall.update(f.index for f in v.link_faces)
        if not joined:
            top -= on_wall

    def in_box(co):
        return box[0] <= co.x <= box[1] and box[2] <= co.y <= box[3]

    def reached(co):
        return in_box(co) and abs(designed(now_t, pre_t, co.x, co.y, co.z) - co.z) > MIN_CHANGE

    touched = set()
    for f in bm.faces:
        c = f.calc_center_median()
        if not in_box(c) or (top is not None and f.index not in top):
            continue
        # A face is reached if the edit moves any of its corners, its centre, or the middle of
        # any edge, so a cut that falls between Ground's vertices is not missed.
        probes = [c] + [v.co for v in f.verts] + [(e.verts[0].co + e.verts[1].co) * 0.5 for e in f.edges]
        if any(reached(q) for q in probes):
            touched.add(f.index)
    if not touched:
        bm.free()
        return None
    region = set(touched)
    for _ in range(2):
        ring = set()
        for fi in region:
            for v in bm.faces[fi].verts:
                for f in v.link_faces:
                    if top is None or f.index in top:
                        ring.add(f.index)
        region |= ring
    faces = [bm.faces[i] for i in sorted(region)]
    if any(len(f.verts) != 3 for f in faces):
        raise SystemExit("%s: a face in the region is not a triangle" % ob.name)
    rverts = sorted({v.index for f in faces for v in f.verts})
    edge_verts = set()
    seam = set()
    for vi in rverts:
        v = bm.verts[vi]
        if any(e.is_boundary for e in v.link_edges):
            seam.add(vi)
        elif not all(f.index in region for f in v.link_faces):
            edge_verts.add(vi)
    # With `joined`, a corner on the region's edge whose other faces are all walls or underside: it stays put.
    hung = set()
    if joined and top is not None:
        hung = {vi for vi in edge_verts if all(f.index in region or f.index not in top for f in bm.verts[vi].link_faces)}
    moving_edge = [vi for vi in edge_verts if vi not in hung and reached(bm.verts[vi].co)]
    if moving_edge:
        raise SystemExit("%s: the edit reaches %d vertices on the region's edge (e.g. %s); refusing" % (
            ob.name, len(moving_edge), tuple(round(c, 1) for c in bm.verts[moving_edge[0]].co)))
    # Ground's open edges are stitched to what the generator still builds (the road
    # corridor, the tunnel lids, the anchors): a vertex on one never moves, and what the
    # edit asked of it is reported.
    held = [designed(now_t, pre_t, bm.verts[vi].co.x, bm.verts[vi].co.y, bm.verts[vi].co.z) - bm.verts[vi].co.z
            for vi in seam if reached(bm.verts[vi].co)]
    # Unless the corridor follows the edit (`ROAD_NATURAL`): then its edge moves with it.
    follow = edit in ROAD_NATURAL
    pinned = set() if follow else {bm.verts[vi] for vi in seam}
    pinned |= {bm.verts[vi] for vi in hung}
    report = {"faces_before": len(faces), "region_vertices": len(rverts), "seam_held": 0 if follow else len(held),
              "seam_held_most": 0.0 if follow else max((abs(h) for h in held), default=0.0)}
    if hung:
        asked = [designed(now_t, pre_t, bm.verts[vi].co.x, bm.verts[vi].co.y, bm.verts[vi].co.z) - bm.verts[vi].co.z for vi in hung]
        report.update({"wall_corners_held": sum(1 for d in asked if abs(d) > MIN_CHANGE),
                       "wall_corners_held_most": max((abs(d) for d in asked), default=0.0)})
    if follow:
        report.update({"seam_followed": len(held), "seam_followed_most": max((abs(h) for h in held), default=0.0)})
    if dry:
        bm.free()
        return report
    col = bm.loops.layers.float_color.get("Col")
    uv = bm.loops.layers.uv.get("UVMap")

    # Keep the region's faces as they are, for the undo.
    hist = bmesh.new()
    vmap = {vi: hist.verts.new(bm.verts[vi].co) for vi in rverts}
    hcol = hist.loops.layers.float_color.new("Col") if col is not None else None
    huv = hist.loops.layers.uv.new("UVMap") if uv is not None else None
    # Their corner normals too (2026-10-12), so the undo gives them back as they were rather than smooth.
    corner_normals = me.corner_normals
    hnormals = []
    for f in faces:
        nf = hist.faces.new([vmap[v.index] for v in f.verts])
        nf.material_index = f.material_index
        nf.smooth = f.smooth
        for la, lb in zip(f.loops, nf.loops):
            if col is not None:
                lb[hcol] = la[col]
            if uv is not None:
                lb[huv].uv = la[uv].uv
        hnormals.extend(corner_normals[li].vector[:] for li in me.polygons[f.index].loop_indices)
    hme = bpy.data.meshes.new("%s__before_edit%d" % (ob.name, edit))
    hist.to_mesh(hme)
    hist.free()
    hme.attributes.new("kyt_normal", 'FLOAT_VECTOR', 'CORNER').data.foreach_set("vector", [x for n in hnormals for x in n])
    for m in me.materials:
        hme.materials.append(m)
    hob = bpy.data.objects.new(hme.name, hme)
    hob["kyt_note"] = "the faces of %s that Ground edit %d replaced, for its --undo; never exported" % (ob.name, edit)
    history_collection().objects.link(hob)

    # The normal of every corner outside the region, to set again after the rebuild.
    kept_normals = {}
    corner_normals = me.corner_normals
    for poly in me.polygons:
        if poly.index in region:
            continue
        c = poly.center
        for li in poly.loop_indices:
            kept_normals[corner_key(me.vertices[me.loops[li].vertex_index].co, c)] = Vector(corner_normals[li].vector)

    # Refine: the region's own vertices and faces as constraints, plus lattice points and
    # the edit's grid vertices inside it.
    local = {vi: k for k, vi in enumerate(rverts)}
    tri_idx = [[local[v.index] for v in f.verts] for f in faces]
    pts2 = [Vector((bm.verts[vi].co.x, bm.verts[vi].co.y)) for vi in rverts]
    flat = BVHTree.FromPolygons([Vector((p.x, p.y, 0.0)) for p in pts2], tri_idx)

    def inside(p):
        return flat.ray_cast(Vector((p.x, p.y, 1.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    xs = [p.x for p in pts2]
    ys = [p.y for p in pts2]
    extra = []
    # On a closed shell (`top_only`) an original edge the edit moves no part of stays (the creases of
    # ground it leaves, a cap's rim and foot, which a free triangulation serrated), with the region's
    # outline; one it moves goes: range north's triangles run 100 m and more, and kept as constraints
    # through the moving ground they left the lattice in needles that folded.
    def still(e):
        a_, b_ = e.verts[0].co, e.verts[1].co
        return not any(reached(q) for q in (a_, b_, (a_ + b_) * 0.5))

    kept_edges = {e for f in faces for e in f.edges
                  if sum(1 for lf in e.link_faces if lf.index in region) == 1 or (top is not None and still(e))}
    outline = [(local[e.verts[0].index], local[e.verts[1].index]) for e in kept_edges]
    # Points along every original edge inside the region too: an edge kept whole would span
    # the cut as a straight bridge between its ends. The region's outer edges stay whole,
    # since the faces outside still use them.
    for f in faces:
        for e in f.edges:
            if top is not None or e.is_boundary or not all(lf.index in region for lf in e.link_faces):
                continue
            a, b = e.verts[0].co, e.verts[1].co
            n = int(math.floor((a - b).xy.length / LATTICE))
            for k in range(1, n + 1):
                t = k / (n + 1)
                extra.append(Vector((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)))
    taken = {}

    def take(q):
        taken.setdefault((int(q.x // CROWD), int(q.y // CROWD)), []).append(q)

    for q in pts2 + extra:
        take(q)

    def crowded(q, r=CROWD):
        cx, cy = int(q.x // CROWD), int(q.y // CROWD)
        return any((q - o).length < r for i in (-1, 0, 1) for j in (-1, 0, 1) for o in taken.get((cx + i, cy + j), ()))

    edges_at = {}
    for f in faces:
        for e in f.edges:
            if top is not None and e not in kept_edges:
                continue
            a, b = e.verts[0].co.xy.copy(), e.verts[1].co.xy.copy()
            for cx in range(int((min(a.x, b.x) - SEP) // LATTICE), int((max(a.x, b.x) + SEP) // LATTICE) + 1):
                for cy in range(int((min(a.y, b.y) - SEP) // LATTICE), int((max(a.y, b.y) + SEP) // LATTICE) + 1):
                    edges_at.setdefault((cx, cy), []).append((a, b))

    def beside_edge(q):
        for a, b in edges_at.get((int(q.x // LATTICE), int(q.y // LATTICE)), ()):
            d = b - a
            l2 = d.length_squared
            s = 0.0 if l2 < 1e-12 else min(1.0, max(0.0, (q - a).dot(d) / l2))
            if (q - (a + d * s)).length < SEP:
                return True
        return False

    for p in grid_points:
        if inside(p) and not beside_edge(p) and not crowded(p, SEP):
            extra.append(p)
            take(p)

    x = math.floor(min(xs) / LATTICE) * LATTICE
    while x <= max(xs):
        y = math.floor(min(ys) / LATTICE) * LATTICE
        while y <= max(ys):
            q = Vector((x, y))
            if inside(q) and not crowded(q) and not beside_edge(q):
                extra.append(q)
            y += LATTICE
        x += LATTICE
    if top is None:
        out_v, _, out_f, orig_v, _, orig_f = delaunay_2d_cdt(pts2 + extra, [], tri_idx, 1, 1e-4, True)
    else:
        out_v, _, out_f, orig_v, _, orig_f = delaunay_2d_cdt(pts2 + extra, outline, [], 0, 1e-4, True)
        orig_f = [[] for _ in out_f]
    surf = BVHTree.FromPolygons([bm.verts[vi].co.copy() for vi in rverts], tri_idx)
    loops = [[(lp[col][:] if col is not None else None, lp[uv].uv.copy() if uv is not None else None) for lp in f.loops]
             for f in faces]
    corners = [[lp.vert.co.copy() for lp in f.loops] for f in faces]
    materials = [(f.material_index, f.smooth) for f in faces]

    def parent_sample(fi, p):
        # Its weights in the original face it lies in, clamped to that face: a point the triangulator
        # names a parent it lies outside of, or a parent seen edge-on from above (a wall), takes the
        # face's nearest values, never an extrapolation (edit 6's corners took colours of -10,000 so).
        bary = plan_weights(corners[fi], p)
        if min(bary) < -1e-6:
            hit = flat.ray_cast(Vector((p.x, p.y, 1.0)), Vector((0.0, 0.0, -1.0)))
            if hit[0] is not None and min(plan_weights(corners[hit[2]], p)) >= -1e-6:
                fi = hit[2]
                bary = plan_weights(corners[fi], p)
        bary = clamped(bary)
        colour = None if col is None else [sum(bary[k] * loops[fi][k][0][j] for k in range(3)) for j in range(4)]
        tex = None if uv is None else loops[fi][0][1] * bary[0] + loops[fi][1][1] * bary[1] + loops[fi][2][1] * bary[2]
        return colour, tex

    # Rebuild: the region's faces go, its vertices stay (inner ones may move), new vertices
    # and faces come in.
    bmesh.ops.delete(bm, geom=faces, context='FACES_ONLY')
    bm.verts.ensure_lookup_table()
    made = []
    for k, p in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(rverts)]
        if src:
            made.append(bm.verts[rverts[src[0]]])
            continue
        z = height(surf, p.x, p.y)
        if z is None:
            # A point on the region's open edge (an edit's grid vertex on Ground's edge at the
            # road corridor, edit 6) can graze past it; it is on the surface a hair inward.
            for dx, dy in ((1e-3, 0.0), (-1e-3, 0.0), (0.0, 1e-3), (0.0, -1e-3)):
                z = height(surf, p.x + dx, p.y + dy)
                if z is not None:
                    break
        if z is None:
            raise SystemExit("%s: a refined point at (%.1f, %.1f) lies off the original surface" % (ob.name, p.x, p.y))
        made.append(bm.verts.new((p.x, p.y, z)))
    fa = bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
    new_faces = []
    islands = 0
    for k, tri in enumerate(out_f):
        vs = [made[i] for i in tri]
        if len(set(vs)) < 3:
            continue
        fi = orig_f[k][0] if orig_f[k] else None
        if fi is None:
            # The triangulator names no parent for some faces along split constraint edges;
            # the original face under the centre is the parent.
            cx = sum(out_v[i].x for i in tri) / 3.0
            cy = sum(out_v[i].y for i in tri) / 3.0
            hit = flat.ray_cast(Vector((cx, cy, 1.0)), Vector((0.0, 0.0, -1.0)))
            if hit[0] is None and top is not None:
                # Outside the outline: the convex hull's triangles, or a hole the region surrounds.
                continue
            if hit[0] is None:
                # The triangulator fills any island of faces the region surrounds but does not
                # take in (the falls, held by `lake_banks`); those faces are still there, so its
                # filling goes.
                islands += 1
                continue
            fi = hit[2]
        if bm.faces.get(vs) is not None:
            islands += 1
            continue
        nf = bm.faces.new(vs)
        for lp in nf.loops:
            colour, tex = parent_sample(fi, lp.vert.co)
            if col is not None:
                lp[col] = colour
            if uv is not None:
                lp[uv].uv = tex
        nf.material_index, nf.smooth = materials[fi]
        nf[fa] = edit
        new_faces.append(nf)
    # Cut (or raise) every vertex of the new faces to the edit's surface, except on the seams.
    depth = [0.0, 0.0]
    moved = 0
    for v in {v for f in new_faces for v in f.verts}:
        if v in pinned:
            continue
        if any(e.is_boundary for e in v.link_edges):
            if not follow:
                continue
            # On the road corridor's edge: moved as the corridor's side will be, by the design's
            # weight and uncapped, so the two meet.
            tw = design_at(now_t, pre_t, v.co.x, v.co.y)
            z = v.co.z if tw is None else v.co.z + tw[1] * (tw[0] - v.co.z)
        else:
            z = designed(now_t, pre_t, v.co.x, v.co.y, v.co.z)
        if abs(z - v.co.z) > MIN_CHANGE:
            depth[0] = min(depth[0], z - v.co.z)
            depth[1] = max(depth[1], z - v.co.z)
            v.co.z = z
            moved += 1
    bm.to_mesh(me)
    bm.free()
    me.update()

    # Normals: every corner outside the region as it was, the new ones smooth.
    vn = [Vector(v.vector) for v in me.vertex_normals]
    normals = []
    for poly in me.polygons:
        c = poly.center
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            normals.append(kept_normals.get(corner_key(me.vertices[vi].co, c), vn[vi]))
    me.normals_split_custom_set(normals)
    report.update({"faces_after": len(new_faces), "moved": moved, "deepest": depth[0], "highest": depth[1]})
    if islands:
        report["island_fill_dropped"] = islands
    return report


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def region_faces(edit):
    """The grid's faces edit `edit` moved any corner of, flattened to a plan BVH, and their
    corners' plan positions."""
    ob = bpy.data.objects[GRID]
    me = ob.data
    M = ob.matrix_world
    ed = np.zeros(len(me.vertices), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", ed)
    world = [M @ Vector(v) for v in coords(ob)]
    polys = [tuple(p.vertices) for p in me.polygons if any(ed[i] == edit for i in p.vertices)]
    corners = sorted({i for p in polys for i in p})
    flat = BVHTree.FromPolygons([Vector((v.x, v.y, 0.0)) for v in world], polys)
    return flat, [Vector((world[i].x, world[i].y)) for i in corners]


def column_top(b):
    """The vertex straight above `b` on its wall: the generator's skirt drops each shore vertex
    to `SKIRT_Z` in one vertical edge."""
    for e in b.link_edges:
        o = e.other_vert(b)
        if (o.co.xy - b.co.xy).length < 1e-3 and o.co.z > b.co.z + 0.01:
            return o
    return None


def plan_constant(name):
    """A number written in `scripts/park_plan.gd`, read without Godot."""
    text = open(os.path.join(HERE, os.pardir, os.pardir, "scripts", "park_plan.gd")).read()
    m = re.search(r"^const %s\s*:?=\s*(-?[0-9.]+)\s*$" % name, text, re.M)
    if m is None:
        raise SystemExit("scripts/park_plan.gd has no number %s" % name)
    return float(m.group(1))


def ground_from_above(box=None, margin=100.0):
    """Whether Ground stands at (x, y): every upward face of Ground, within `box` grown by
    `margin` when one is given."""
    up_v = []
    up_f = []
    for ob in ground_objects():
        me = ob.data
        for poly in me.polygons:
            if poly.normal.z < MIN_UP_FACE:
                continue
            c = poly.center
            if box is not None and not (box[0] - margin <= c.x <= box[1] + margin and box[2] - margin <= c.y <= box[3] + margin):
                continue
            base = len(up_v)
            up_v.extend(Vector(me.vertices[i].co) for i in poly.vertices)
            up_f.append(tuple(range(base, base + len(poly.vertices))))
    land = BVHTree.FromPolygons(up_v, up_f)

    def over_ground(x, y):
        return land.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    return over_ground


def uv_projection(box=None):
    """The reserve's texture coordinates as a plan projection, (u, v) = [x, y, 1] @ coef, and
    how far its own corners stray from it."""
    reserve = bpy.data.objects["terrain_world_mainland_reserve"].data
    ruv = reserve.uv_layers["UVMap"]
    fit = []
    for poly in reserve.polygons:
        if poly.normal.z < 0.3:
            continue
        c = poly.center
        if box is not None and not (box[0] <= c.x <= box[1] and box[2] <= c.y <= box[3]):
            continue
        for li in poly.loop_indices:
            co = reserve.vertices[reserve.loops[li].vertex_index].co
            fit.append((co.x, co.y, ruv.data[li].uv.x, ruv.data[li].uv.y))
        if len(fit) >= 20000:
            break
    F = np.array(fit)
    coef, *_ = np.linalg.lstsq(np.c_[F[:, 0], F[:, 1], np.ones(len(F))], F[:, 2:], rcond=None)
    err = float(np.abs(np.c_[F[:, 0], F[:, 1], np.ones(len(F))] @ coef - F[:, 2:]).max())
    if err > 1e-3:
        raise SystemExit("the reserve's texture coordinates are not a plan projection (off by %.4f)" % err)
    return coef, err


class Shore:
    """The coasts' vertical shore walls in Ground, the generator's skirt: each panel a sea edge
    at `SKIRT_Z`, the two vertices straight above it, and the panel's faces between them.

    `box` limits the panels to a plan box. Holds a bmesh of every Ground object until `cut`."""

    def __init__(self, over_ground, box=None):
        self.over_ground = over_ground
        self.bms = {}
        self.panels = []
        # A shore vertex by its plan position. The two coasts' walls meet a few millimetres
        # apart (each body carries its seam displacement), so a vertex within `JOIN` of one
        # already seen is the same shore vertex.
        self.canon = {}
        for ob in ground_objects():
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            # The edit's face mark goes on before any face is held: adding a layer later leaves
            # every face reference stale.
            bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            self.bms[ob.name] = bm
            for e in bm.edges:
                if not e.is_boundary:
                    continue
                b0, b1 = e.verts
                if b0.co.z > SKIRT_Z + 0.01 or b1.co.z > SKIRT_Z + 0.01:
                    continue
                mid = (b0.co + b1.co) * 0.5
                if box is not None and not (box[0] <= mid.x <= box[1] and box[2] <= mid.y <= box[3]):
                    continue
                t0, t1 = column_top(b0), column_top(b1)
                if t0 is None or t1 is None:
                    continue
                quad = {b0, b1, t0, t1}
                fs = sorted({f for v in (b0, b1) for f in v.link_faces if set(f.verts) <= quad}, key=lambda f: f.index)
                if not fs or len(fs) > 2:
                    raise SystemExit("%s: the shore wall at (%.1f, %.1f) is not one panel" % (ob.name, mid.x, mid.y))
                self.panels.append({"ob": ob.name, "b": (b0, b1), "t": (t0, t1), "faces": fs})
        self.at_key = {}
        for n, p in enumerate(self.panels):
            for b in p["b"]:
                self.at_key.setdefault(self.key(b), []).append(n)
        self.top_z = {}
        self.top_xy = {}
        for p in self.panels:
            for b, t in zip(p["b"], p["t"]):
                self.top_z.setdefault(self.key(b), t.co.z)
                self.top_xy.setdefault(self.key(b), Vector((t.co.x, t.co.y)))
        # Which side of the shore is the sea: each panel's outward normal, away from the
        # coast's own ground. The land side may also be ground the generator still builds (the
        # road corridor's hole at the spur), which Ground does not hold, so sea is told by the
        # wall, not by the absence of Ground.
        self.outward = []
        for p in self.panels:
            a, b = (Vector(v.co.xy) for v in p["b"])
            d = (b - a).normalized()
            out = Vector((d.y, -d.x))
            if over_ground(*((a + b) * 0.5 + out * 1.5)):
                out = -out
            self.outward.append(out)
        self.SA = np.array([tuple(p["b"][0].co.xy) for p in self.panels])
        self.SAB = np.array([tuple(p["b"][1].co.xy) for p in self.panels]) - self.SA
        self.SO = np.array([tuple(o) for o in self.outward])
        self.SL2 = np.maximum((self.SAB ** 2).sum(axis=1), 1e-9)

    def find(self, x, y):
        cx, cy = int(math.floor(x / 0.05)), int(math.floor(y / 0.05))
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for k in self.canon.get((cx + i, cy + j), ()):
                    if abs(k[0] - x) < JOIN and abs(k[1] - y) < JOIN:
                        return k
        return None

    def key(self, v):
        k = self.find(v.co.x, v.co.y)
        if k is None:
            k = (round(v.co.x, 3), round(v.co.y, 3))
            self.canon.setdefault((int(math.floor(v.co.x / 0.05)), int(math.floor(v.co.y / 0.05))), []).append(k)
        return k

    def nearest(self, x, y):
        """The nearest panel to (x, y), the distance to it, and how far along it."""
        P = np.array((x, y))
        u = np.clip(((P - self.SA) * self.SAB).sum(axis=1) / self.SL2, 0.0, 1.0)
        Q = self.SA + self.SAB * u[:, None]
        d2 = ((Q - P) ** 2).sum(axis=1)
        i = int(np.argmin(d2))
        return i, math.sqrt(float(d2[i])), float(u[i])

    def seaward(self, x, y):
        i, _, u = self.nearest(x, y)
        Q = self.SA[i] + self.SAB[i] * u
        return float(((np.array((x, y)) - Q) * self.SO[i]).sum()) > 0.0

    def normals(self, run, keys):
        """Each run vertex's seaward direction: the mean of its panels' outward normals."""
        normal = {k: Vector((0.0, 0.0)) for k in keys}
        for n in run:
            for k in map(self.key, self.panels[n]["b"]):
                normal[k] += self.outward[n]
        return {k: v.normalized() for k, v in normal.items()}

    def cut(self, edit, run, edge_z, dry, what):
        """Cut each run panel at `edge_z` and drop the part below; keep the panels' old faces in
        `Ground_history` for the undo. Frees every bmesh. Returns a report per object cut."""
        cut = {}
        for n in sorted(run):
            cut.setdefault(self.panels[n]["ob"], []).append(self.panels[n])
        for name, bm in self.bms.items():
            if name not in cut or dry:
                bm.free()
        report = {}
        for name, ps in sorted(cut.items()):
            report[name] = {"wall_panels": len(ps), "wall_faces_before": sum(len(p["faces"]) for p in ps)}
        if dry:
            return report
        for name, ps in sorted(cut.items()):
            ob = bpy.data.objects[name]
            me = ob.data
            bm = self.bms[name]
            col = bm.loops.layers.float_color.get("Col")
            uv = bm.loops.layers.uv.get("UVMap")
            fa = bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
            gone = {f for p in ps for f in p["faces"]}
            corner_normals = me.corner_normals
            # Every other face's corner normals, to set again; and the panels' own, for the undo.
            kept_normals = {}
            old_normals = {}
            gone_index = {f.index for f in gone}
            for poly in me.polygons:
                if poly.index in gone_index:
                    old_normals[poly.index] = [Vector(corner_normals[li].vector) for li in poly.loop_indices]
                    continue
                c = poly.center
                for li in poly.loop_indices:
                    kept_normals[corner_key(me.vertices[me.loops[li].vertex_index].co, c)] = Vector(corner_normals[li].vector)
            hist = bmesh.new()
            hcol = hist.loops.layers.float_color.new("Col")
            huv = hist.loops.layers.uv.new("UVMap")
            hmap = {}
            hnormals = []
            for f in sorted(gone, key=lambda f: f.index):
                vs = []
                for v in f.verts:
                    if v not in hmap:
                        hmap[v] = hist.verts.new(v.co)
                    vs.append(hmap[v])
                nf = hist.faces.new(vs)
                nf.material_index = f.material_index
                nf.smooth = f.smooth
                for la, lb, n in zip(f.loops, nf.loops, old_normals[f.index]):
                    lb[hcol] = la[col]
                    lb[huv].uv = la[uv].uv
                    hnormals.append(n)
            hme = bpy.data.meshes.new("%s__before_edit%d" % (name, edit))
            hist.to_mesh(hme)
            hist.free()
            hme.attributes.new("kyt_normal", 'FLOAT_VECTOR', 'CORNER').data.foreach_set(
                "vector", [x for n in hnormals for x in n])
            for m in me.materials:
                hme.materials.append(m)
            hob = bpy.data.objects.new(hme.name, hme)
            hob["kyt_note"] = "the shore wall panels of %s that %s cut, for its --undo; never exported" % (name, what)
            history_collection().objects.link(hob)

            made = {}
            new_faces = []
            for p in ps:
                # The panel's corners as they were, colour and texture at its top and foot: a
                # column shared by two panels carries each its own texture coordinate.
                data = {}
                for f in p["faces"]:
                    for lp in f.loops:
                        data[lp.vert] = (Vector(lp[col][:]), lp[uv].uv.copy())
                outward = p["faces"][0].normal.copy()
                mids = []
                for b, t in zip(p["b"], p["t"]):
                    k = self.key(b)
                    if edge_z[k] >= t.co.z - SNAP:
                        mids.append(t)
                        continue
                    if k not in made:
                        made[k] = bm.verts.new((t.co.x, t.co.y, edge_z[k]))
                    w = (edge_z[k] - b.co.z) / (t.co.z - b.co.z)
                    data[made[k]] = (data[b][0].lerp(data[t][0], w), data[b][1].lerp(data[t][1], w))
                    mids.append(made[k])
                t0, t1 = p["t"]
                m0, m1 = mids
                tris = []
                if m0 is not t0 and m1 is not t1:
                    tris = [(t0, t1, m1), (t0, m1, m0)]
                elif m0 is not t0:
                    tris = [(t0, t1, m0)]
                elif m1 is not t1:
                    tris = [(t0, t1, m1)]
                for tri in tris:
                    n = (tri[1].co - tri[0].co).cross(tri[2].co - tri[0].co)
                    if n.dot(outward) < 0.0:
                        tri = (tri[0], tri[2], tri[1])
                    nf = bm.faces.new(tri)
                    nf.material_index = p["faces"][0].material_index
                    nf.smooth = p["faces"][0].smooth
                    nf[fa] = edit
                    for lp in nf.loops:
                        lp[col], lp[uv].uv = data[lp.vert][0], data[lp.vert][1]
                    new_faces.append(nf)
            bmesh.ops.delete(bm, geom=list(gone), context='FACES')
            bm.to_mesh(me)
            bm.free()
            me.update()
            normals = []
            for poly in me.polygons:
                c = poly.center
                for li in poly.loop_indices:
                    vi = me.loops[li].vertex_index
                    normals.append(kept_normals.get(corner_key(me.vertices[vi].co, c), Vector(poly.normal)))
            me.normals_split_custom_set(normals)
            report[name]["wall_faces_after"] = len(new_faces)
        return report


def build_ground(name, out_v, zmap, faces, colour, coef, edit, note):
    """A new Ground object from a triangulation's points, heights and kept faces, smooth, with
    corner colours from `colour(x, y, z)` and the reserve's plan projection for its texture."""
    me = bpy.data.meshes.new(name)
    verts = [(p.x, p.y, zmap[k]) for k, p in enumerate(out_v)]
    used = sorted({i for f in faces for i in f})
    remap = {i: n for n, i in enumerate(used)}
    me.from_pydata([verts[i] for i in used], [], [tuple(remap[i] for i in f) for f in faces])
    me.validate()
    for poly in me.polygons:
        if poly.normal.z < 0.0:
            poly.flip()
        poly.use_smooth = True
    ccol = me.color_attributes.new("Col", 'FLOAT_COLOR', 'CORNER')
    cuv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            ccol.data[li].color = colour(co.x, co.y, co.z)
            u, v = np.array([co.x, co.y, 1.0]) @ coef
            cuv.data[li].uv = (float(u), float(v))
    fa = me.attributes.new("authored_edit", 'INT', 'FACE')
    fa.data.foreach_set("value", [edit] * len(me.polygons))
    me.materials.append(bpy.data.objects["terrain_world_mainland_reserve"].data.materials[0])
    ob = bpy.data.objects.new(name, me)
    ob["kyt_note"] = note
    bpy.data.collections[GROUND].objects.link(ob)
    return me


def triangulate(pts, segs, zs):
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, segs, [], 0, 1e-4, True)
    zmap = []
    for k, p in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(pts)]
        if not src:
            raise SystemExit("the triangulator added a point at (%.1f, %.1f)" % (p.x, p.y))
        zmap.append(zs[src[0]])
    return out_v, out_f, zmap


def new_land(edit, now_t, pre_t, box, dry):
    """Build the land an edit designed beyond Ground's edge, where the game has open sea.

    The coasts end at the shore in a vertical wall, the generator's skirt, from the shore's top
    edge down to `SKIRT_Z`. The new land is one new Ground object, the grid's edited surface
    from that wall out to where the edit meets the grid's seabed again, so it runs on below the
    waterline the way a real shore does (Christina, 2026-10-06: "new land can go down into the
    ocean a little like in real life"). It meets the shore along the wall: on its top edge where
    the design stands out of the water, the bench rising to it over a `RAMP` bank, and lower
    down the wall towards the ends, where the edit's taper leaves only water against the wall.
    Each wall panel the new land reaches is cut at that line and the part below it, buried,
    goes, so the new land's edge is the wall's own edge and nothing is left inside the land.
    The bluff above the wall and everything else of Ground stays exactly where it was."""
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    bench = float(edit_constant("world_terrain_coast_extension.py", "BENCH_H"))
    if not sea < CREST < bench:
        raise SystemExit("CREST %.1f is not between the sea %.1f and the bench %.1f" % (CREST, sea, bench))
    region, corners = region_faces(edit)

    def in_region(x, y):
        return region.ray_cast(Vector((x, y, 1.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    over_ground = ground_from_above(box)
    shore = Shore(over_ground, (box[0] - 200.0, box[1] + 200.0, box[2] - 200.0, box[3] + 200.0))
    panels = shore.panels
    key = shore.key
    seaward = shore.seaward

    def edge_height(x, y, top_z):
        """Where the new land meets the wall at (x, y): the wall's top edge wherever the design
        stands on the bench, down the wall to the design itself where it is under water."""
        t = height(design_t, x, y)
        if t is None:
            return SKIRT_Z
        f = min(1.0, max(0.0, (t - sea) / (CREST - sea)))
        e = t + f * (top_z - t)
        return top_z if e > top_z - SNAP else max(SKIRT_Z, e)

    # The design: the edited grid, except that a grid vertex the edit did not move, standing
    # off Ground above the sea near the edit, lies under water. Off Ground the grid is either
    # its 10 m smear of the shore wall or ground the generator builds (the road corridor), and
    # neither is new land: at the spur the design rose round the bend against the wall on
    # them. This shapes only the new land; nothing else reads it.
    grid = bpy.data.objects[GRID]
    gme = grid.data
    ged = np.zeros(len(gme.vertices), dtype=np.int32)
    gme.attributes["authored_edit"].data.foreach_get("value", ged)
    gco = [grid.matrix_world @ Vector(v) for v in coords(grid)]
    smeared = 0
    for i, v in enumerate(gco):
        if ged[i] == edit or v.z <= sea - END_UNDER:
            continue
        if not (box[0] <= v.x <= box[1] and box[2] <= v.y <= box[3]) or over_ground(v.x, v.y):
            continue
        v.z = sea - END_UNDER
        smeared += 1
    design_t = BVHTree.FromPolygons(gco, [tuple(p.vertices) for p in gme.polygons])
    run = {n for n, p in enumerate(panels) if in_region(*((p["b"][0].co.xy + p["b"][1].co.xy) * 0.5))}
    if not run:
        raise SystemExit("edit %d reaches no shore wall" % edit)

    def e_at(k):
        return edge_height(k[0], k[1], shore.top_z[k])

    # Carry the run on along the wall until each end meets the wall under water, so no edge
    # of the new land is left standing open above the sea.
    for _ in range(2):
        for k in sorted({k for n in run for k in map(key, panels[n]["b"])}):
            steps = 0
            while sum(1 for n in shore.at_key[k] if n in run) == 1 and e_at(k) > sea - END_UNDER:
                nxt = [n for n in shore.at_key[k] if n not in run]
                if not nxt or steps > 60:
                    raise SystemExit("the new land's end at (%.1f, %.1f) stands %.1f m over the sea against the wall" % (
                        k[0], k[1], e_at(k) - sea))
                run.add(nxt[0])
                k = [kk for kk in map(key, panels[nxt[0]]["b"]) if kk != k][0]
                steps += 1
    keys = sorted({k for n in run for k in map(key, panels[n]["b"])})
    edge_z = {k: e_at(k) for k in keys}
    design_at = {k: (height(design_t, k[0], k[1]) if height(design_t, k[0], k[1]) is not None else edge_z[k]) for k in keys}
    ends = [k for k in keys if sum(1 for n in shore.at_key[k] if n in run) == 1]
    normal = shore.normals(run, keys)

    # Points: the shore line, rows across the bank, and the edit's grid corners off the land.
    # The shore points stand exactly on the wall's top vertices, so the new land's edge is the
    # wall's own edge, not one a rounding away.
    pts = [shore.top_xy[k].copy() for k in keys]
    index = {k: i for i, k in enumerate(keys)}
    segs = [(index[key(panels[n]["b"][0])], index[key(panels[n]["b"][1])]) for n in sorted(run)]
    taken = {}

    def take(q):
        taken.setdefault((int(q.x // CROWD), int(q.y // CROWD)), []).append(q)

    def crowded(q):
        cx, cy = int(q.x // CROWD), int(q.y // CROWD)
        return any((q - o).length < CROWD for i in (-1, 0, 1) for j in (-1, 0, 1) for o in taken.get((cx + i, cy + j), ()))

    for q in pts:
        take(q)
    for k in keys:
        if edge_z[k] - design_at[k] < 0.1:
            continue
        for s in (2.5, 5.0, 7.5, RAMP):
            q = shore.top_xy[k] + normal[k] * s
            if not over_ground(q.x, q.y) and seaward(q.x, q.y) and not crowded(q):
                pts.append(q)
                take(q)
    for q in corners:
        if not over_ground(q.x, q.y) and seaward(q.x, q.y) and not crowded(q):
            pts.append(q)
            take(q)

    # Heights: the edited grid, lifted near the shore by the bank.
    A = np.array([pts[i].to_tuple() for i, _ in segs])
    B = np.array([pts[j].to_tuple() for _, j in segs])
    lift_a = np.array([max(0.0, edge_z[keys[i]] - design_at[keys[i]]) for i, _ in segs])
    lift_b = np.array([max(0.0, edge_z[keys[j]] - design_at[keys[j]]) for _, j in segs])
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(axis=1), 1e-9)

    def to_shore(p):
        P = np.array(p.to_tuple())
        u = np.clip(((P - A) * AB).sum(axis=1) / L2, 0.0, 1.0)
        d = np.sqrt((((A + AB * u[:, None]) - P) ** 2).sum(axis=1))
        i = int(np.argmin(d))
        return float(d[i]), float(lift_a[i] + (lift_b[i] - lift_a[i]) * u[i])

    zs = []
    for i, p in enumerate(pts):
        if i < len(keys):
            zs.append(edge_z[keys[i]])
            continue
        t = height(design_t, p.x, p.y)
        if t is None:
            raise SystemExit("a new-land point at (%.1f, %.1f) lies off the grid" % (p.x, p.y))
        d, lift = to_shore(p)
        zs.append(t + lift * (1.0 - smoothstep(0.0, RAMP, d)))

    out_v, out_f, zmap = triangulate(pts, segs, zs)
    faces = []
    for tri in out_f:
        c = Vector((sum(out_v[i].x for i in tri) / 3.0, sum(out_v[i].y for i in tri) / 3.0))
        longest = max((out_v[tri[k]] - out_v[tri[(k + 1) % 3]]).length for k in range(3))
        if longest > 40.0 or over_ground(c.x, c.y) or not seaward(c.x, c.y):
            continue
        if not in_region(c.x, c.y) and to_shore(c)[0] > RAMP:
            continue
        faces.append(tuple(tri))

    land_report = {"faces": len(faces), "shore_m": round(sum((pts[i] - pts[j]).length for i, j in segs), 1),
                   "shore_vertices": len(keys), "top_of_wall": sum(1 for k in keys if edge_z[k] >= shore.top_z[k] - SNAP),
                   "highest": round(max(zmap), 2), "deepest": round(min(zmap), 2), "grid_held_under_sea": smeared,
                   "ends_under_sea": [round(edge_z[k] - sea, 2) for k in ends]}
    # The colours read the walls' top faces before the cut changes them.
    shore_col = {}
    for ob in ground_objects():
        if ob.name not in {panels[n]["ob"] for n in run}:
            continue
        ome = ob.data
        ocol = ome.color_attributes["Col"]
        for poly in ome.polygons:
            if poly.normal.z < 0.3:
                continue
            c = poly.center
            if ob.name == "terrain_world_mainland_reserve" and not (box[0] <= c.x <= box[1] and box[2] <= c.y <= box[3]):
                continue
            for li in poly.loop_indices:
                co = ome.vertices[ome.loops[li].vertex_index].co
                k = shore.find(co.x, co.y)
                if k in index:
                    shore_col.setdefault(k, []).append(Vector(ocol.data[li].color))
    report = shore.cut(edit, run, edge_z, dry, "Ground edit %d" % edit)
    if dry:
        return report, land_report, None

    # The new land's colours: the planting at the top of the wall it meets, sand from the
    # bench's crest down, the sea cliff's colour deep under water; its texture coordinates
    # continue the reserve's own.
    coef, uv_err = uv_projection(box)
    kk = sorted(shore_col)
    if not kk:
        raise SystemExit("no planting found at the top of the shore wall")
    tree = KDTree(len(kk))
    for i, k in enumerate(kk):
        tree.insert((k[0], k[1], 0.0), i)
    tree.balance()
    bench_col = {k: sum(shore_col[k], Vector((0.0, 0.0, 0.0, 0.0))) / len(shore_col[k]) for k in kk}

    def colour(x, y, z):
        c = bench_col[kk[tree.find((x, y, 0.0))[1]]]
        grain = 1.0 + math.sin(x * 0.37) * math.sin(-y * 0.41) * 0.05
        sand = Vector((SAND[0] * grain, SAND[1] * grain, SAND[2] * grain, 1.0))
        bed = Vector((SEABED[0] * grain, SEABED[1] * grain, SEABED[2] * grain, 1.0))
        c = c.lerp(sand, 1.0 - smoothstep(SAND_FROM[1], SAND_FROM[0], z))
        return c.lerp(bed, 1.0 - smoothstep(SEABED_FROM[1], SEABED_FROM[0], z))

    name = NEW_LAND[edit]
    me = build_ground(name, out_v, zmap, faces, colour, coef, edit,
                      "Ground edit %d: land the grid edit designed beyond the shore, where the game had open sea; "
                      "built by tools/blender/world_terrain_ground_edit.py, undone by its --undo" % edit)
    area = sum(p.area for p in me.polygons if min(me.vertices[i].co.z for i in p.vertices) >= sea)
    land_report.update({"faces": len(me.polygons), "vertices": len(me.vertices), "dry_ha": round(area / 10000.0, 2),
                        "uv_fit_error": round(uv_err, 6)})
    return report, land_report, name


def coast_shelf(edit, dry):
    """Run every coast in Ground on below the waterline (Christina, 2026-10-06: "in general the
    coast should have enough mesh extending into the water and below the water line").

    The coasts end at the shore in the generator's vertical wall, down to `SKIRT_Z` with nothing
    beyond it. Each wall is cut `SHELF_UNDER` below the waterline, so the water still meets the
    wall and the shore above it is exactly as it was, and the part below goes. From that line a
    shelf, one new Ground object, slopes out `SHELF_W` to `SHELF_DEPTH`, steepest at the wall and
    easing out flat, where a seabed can join it. Where two shores face each other across narrow
    water their shelves meet, each point taking the depth its nearest wall gives it. The park's
    own west shore is left alone: there the generator's shore strip, pier and protected NT-1 meet
    the sea, not Ground."""
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    cut_z = sea - SHELF_UNDER
    over_ground = ground_from_above()
    shore = Shore(over_ground)
    panels = shore.panels
    key = shore.key
    x0 = plan_constant("REBUILD_FOOTPRINT_MIN_X") - SHELF_CLEAR
    x1 = plan_constant("REBUILD_FOOTPRINT_MAX_X") + SHELF_CLEAR
    z0 = plan_constant("REBUILD_FOOTPRINT_MIN_Z") - SHELF_CLEAR
    z1 = plan_constant("REBUILD_FOOTPRINT_MAX_Z") + SHELF_CLEAR

    def in_park(x, y):
        return x0 <= x <= x1 and z0 <= -y <= z1

    run = {n for n, p in enumerate(panels) if not in_park(*((p["b"][0].co.xy + p["b"][1].co.xy) * 0.5))}
    if not run:
        raise SystemExit("Ground has no shore wall to run on below the water")
    keys = sorted({k for n in run for k in map(key, panels[n]["b"])})
    edge_z = {k: (shore.top_z[k] if shore.top_z[k] <= cut_z + SNAP else cut_z) for k in keys}
    normal = shore.normals(run, keys)
    pts = [shore.top_xy[k].copy() for k in keys]
    index = {k: i for i, k in enumerate(keys)}
    segs = [(index[key(panels[n]["b"][0])], index[key(panels[n]["b"][1])]) for n in sorted(run)]

    A = np.array([pts[i].to_tuple() for i, _ in segs])
    AB = np.array([pts[j].to_tuple() for _, j in segs]) - A
    EA = np.array([edge_z[keys[i]] for i, _ in segs])
    EB = np.array([edge_z[keys[j]] for _, j in segs])
    L2 = np.maximum((AB ** 2).sum(axis=1), 1e-9)

    def to_run(x, y):
        """The distance to the nearest wall the shelf runs from, and that wall's cut height."""
        P = np.array((x, y))
        u = np.clip(((P - A) * AB).sum(axis=1) / L2, 0.0, 1.0)
        d2 = (((A + AB * u[:, None]) - P) ** 2).sum(axis=1)
        i = int(np.argmin(d2))
        return math.sqrt(float(d2[i])), float(EA[i] + (EB[i] - EA[i]) * u[i])

    def depth(d, e):
        t = min(1.0, d / SHELF_W)
        return min(e, e + (SHELF_DEPTH - e) * (1.0 - (1.0 - t) ** 2))

    def wanted(x, y):
        """A point the shelf covers: on the sea side, off the land and the park, and in front of
        a wall it runs from rather than one it leaves alone."""
        if in_park(x, y) or over_ground(x, y) or not shore.seaward(x, y):
            return False
        return shore.nearest(x, y)[0] in run

    # Rows out from the wall, nearest first; a row's point too near one already placed goes, so
    # rows from the two walls of a cove do not pile up.
    taken = {}

    def crowded(q, r):
        cx, cy = int(q.x // 8.0), int(q.y // 8.0)
        reach = int(math.ceil(r / 8.0))
        return any((q - o).length < r for i in range(-reach, reach + 1) for j in range(-reach, reach + 1)
                   for o in taken.get((cx + i, cy + j), ()))

    rows = 0
    last = 0.0
    for s in SHELF_ROWS:
        r = min(CROWD + SHELF_SPREAD * s, 0.45 * (s - last))
        last = s
        for k in keys:
            q = shore.top_xy[k] + normal[k] * s
            if not wanted(q.x, q.y) or crowded(q, r):
                continue
            pts.append(q)
            taken.setdefault((int(q.x // 8.0), int(q.y // 8.0)), []).append(q)
            rows += 1
    zs = [edge_z[k] for k in keys] + [depth(*to_run(p.x, p.y)) for p in pts[len(keys):]]

    out_v, out_f, zmap = triangulate(pts, segs, zs)
    faces = []
    for tri in out_f:
        c = Vector((sum(out_v[i].x for i in tri) / 3.0, sum(out_v[i].y for i in tri) / 3.0))
        longest = max((out_v[tri[k]] - out_v[tri[(k + 1) % 3]]).length for k in range(3))
        if longest > SHELF_LONGEST or not wanted(c.x, c.y) or to_run(c.x, c.y)[0] > SHELF_W + 1.0:
            continue
        faces.append(tuple(tri))

    shelf_report = {"faces": len(faces), "shore_m": round(sum((pts[i] - pts[j]).length for i, j in segs), 1),
                    "wall_panels": len(run), "left_at_the_park": len(panels) - len(run),
                    "walls_kept_above": sum(1 for k in keys if edge_z[k] < shore.top_z[k] - SNAP),
                    "walls_wholly_under": sum(1 for k in keys if edge_z[k] >= shore.top_z[k] - SNAP),
                    "row_points": rows, "deepest": round(min(zmap), 2)}
    # Sand under a beach: the shore's own colour at the top of the wall, where it is the
    # generator's beach sand.
    sandy = set()
    run_objects = {panels[n]["ob"] for n in run}
    for ob in ground_objects():
        if ob.name not in run_objects:
            continue
        ome = ob.data
        ocol = ome.color_attributes["Col"]
        for poly in ome.polygons:
            if poly.normal.z < 0.3:
                continue
            for li in poly.loop_indices:
                co = ome.vertices[ome.loops[li].vertex_index].co
                k = shore.find(co.x, co.y)
                if k in index and (Vector(ocol.data[li].color[:3]) - Vector(SAND)).length < SANDY:
                    sandy.add(k)
    report = shore.cut(edit, run, edge_z, dry, "the coast shelf (Ground edit %d)" % edit)
    shelf_report["sandy_shore_vertices"] = len(sandy)
    if dry:
        return report, shelf_report, None

    coef, uv_err = uv_projection()
    tree = KDTree(len(keys))
    for i, k in enumerate(keys):
        tree.insert((k[0], k[1], 0.0), i)
    tree.balance()

    def colour(x, y, z):
        grain = 1.0 + math.sin(x * 0.37) * math.sin(-y * 0.41) * 0.05
        bed = Vector((SEABED[0] * grain, SEABED[1] * grain, SEABED[2] * grain, 1.0))
        if keys[tree.find((x, y, 0.0))[1]] not in sandy:
            return bed
        sand = Vector((SAND[0] * grain, SAND[1] * grain, SAND[2] * grain, 1.0))
        return sand.lerp(bed, 1.0 - smoothstep(SEABED_FROM[1], SEABED_FROM[0], z))

    me = build_ground(SHELF, out_v, zmap, faces, colour, coef, edit,
                      "The coast shelf (Ground edit %d): every coast run on below the waterline from its shore "
                      "wall, cut %.1f m under the sea; built by tools/blender/world_terrain_ground_edit.py "
                      "-- --edit shelf, undone by its --undo" % (edit, SHELF_UNDER))
    area = sum(p.area for p in me.polygons)
    shelf_report.update({"faces": len(me.polygons), "vertices": len(me.vertices), "area_ha": round(area / 10000.0, 1),
                         "uv_fit_error": round(uv_err, 6)})
    return report, shelf_report, SHELF


def landform_shelf(edit, dry):
    """Run the landforms' coasts on below the waterline (Christina, 2026-10-06: "in general the
    coast should have enough mesh extending into the water and below the water line"), as the
    coast shelf does the generator's.

    The range's and city's landforms, which joined Ground on 2026-10-06, are closed shells, and
    where one meets the open sea its side runs straight down to its floor at about -11 with nothing
    beyond; since the sea cleared (2026-10-07) that side shows under the water. The shells are kept
    whole. The shelf starts on each sea-facing side `SHELF_UNDER` below the waterline, or at the
    side's top where that is lower, and slopes out `SHELF_W` to `SHELF_DEPTH`; the side below its
    start stands behind it. It meets no other ground: where ground already lies under the water
    (the coast shelf, edit 1's sheet, another shell), it stops short of it. Sandy where the shore is:
    the landform's own sand or beach colour at the top of its side, or a beach sheet on it."""
    if LANDFORM_SHELF in bpy.data.objects:
        raise SystemExit("%s already exists" % LANDFORM_SHELF)
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    cut_z = sea - SHELF_UNDER
    over_ground = ground_from_above()
    beach_bm = bmesh.new()
    for ob in ground_objects():
        if ob.get("kyt_collision") == "none":
            beach_bm.from_mesh(ob.data)
    beach_tree = BVHTree.FromBMesh(beach_bm)
    beach_bm.free()

    def on_beach(x, y):
        return beach_tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))[0] is not None

    keys = []
    index = {}
    xy = []
    edge_z = []
    normal = []
    sandy = set()
    segs = []
    seg_out = []
    shells = []

    def key(co):
        k = (round(co.x, 2), round(co.y, 2))
        if k not in index:
            index[k] = len(keys)
            keys.append(k)
            xy.append(Vector((co.x, co.y)))
            edge_z.append(None)
            normal.append(Vector((0.0, 0.0)))
        return index[k]

    for ob in ground_objects():
        if ob.get("kyt_collision") == "none":
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.normal_update()
        if any(e.is_boundary for e in bm.edges) or not any(f.normal.z < -0.5 for f in bm.faces):
            bm.free()
            continue
        if ob.matrix_world != ob.matrix_world.Identity(4):
            raise SystemExit("%s is not at the origin; Ground objects hold world positions" % ob.name)
        bm.faces.ensure_lookup_table()
        own = BVHTree.FromBMesh(bm)
        mats = [m.name if m else "" for m in ob.data.materials]

        def own_top(p):
            hit = own.ray_cast(Vector((p.x, p.y, 5000.0)), Vector((0.0, 0.0, -1.0)))
            return None if hit[0] is None else (hit[0].z, hit[2])

        found = 0
        for e in bm.edges:
            # The floor's rim: where a face looking down meets one that does not.
            fs = e.link_faces
            if len(fs) != 2 or (fs[0].normal.z < -0.5) == (fs[1].normal.z < -0.5):
                continue
            a, b = e.verts
            # A floor standing above the cut is buried in other ground, not at the sea.
            if max(a.co.z, b.co.z) > cut_z:
                continue
            d = b.co.xy - a.co.xy
            if d.length < 0.05:
                continue
            m = (a.co.xy + b.co.xy) * 0.5
            n = Vector((d.y, -d.x)).normalized()
            if own_top(m + n * 0.5) is not None:
                n = -n
            if own_top(m - n * 0.5) is None or own_top(m + n * 0.5) is not None:
                continue
            if over_ground(*(m + n * 2.0)):
                continue
            # The side in pieces of at most `LANDFORM_SHORE_STEP` (the shells' sides run up to a
            # hundred metres), each point's height its top just inside, under the cut; a side
            # with a point that has no top (a sliver at a corner of edit 1's caps) is left.
            pieces = max(1, int(math.ceil(d.length / LANDFORM_SHORE_STEP)))
            along = [a.co.xy.lerp(b.co.xy, k / pieces) for k in range(pieces + 1)]
            tops = [own_top(q - n * 0.05) for q in along]
            if None in tops:
                continue
            ids = []
            for q, top in zip(along, tops):
                i = key(q)
                normal[i] += n
                if edge_z[i] is None:
                    edge_z[i] = min(cut_z, top[0])
                    name = mats[bm.faces[top[1]].material_index]
                    if "sand" in name or "beach" in name or on_beach(*(q - n * 0.05)):
                        sandy.add(i)
                ids.append(i)
            for ia, ib in zip(ids, ids[1:]):
                segs.append((ia, ib))
                seg_out.append(n)
            found += 1
        if found:
            shells.append("%s %d" % (ob.name, found))
        bm.free()
    if not segs:
        raise SystemExit("no landform meets the open sea")
    normal = [v.normalized() for v in normal]

    A = np.array([xy[i].to_tuple() for i, _ in segs])
    AB = np.array([xy[j].to_tuple() for _, j in segs]) - A
    EA = np.array([edge_z[i] for i, _ in segs])
    EB = np.array([edge_z[j] for _, j in segs])
    SO = np.array([n.to_tuple() for n in seg_out])
    L2 = np.maximum((AB ** 2).sum(axis=1), 1e-9)

    def to_run(x, y):
        """The nearest sea-facing side: the distance to it, its height there, and whether (x, y) is
        in front of it."""
        P = np.array((x, y))
        u = np.clip(((P - A) * AB).sum(axis=1) / L2, 0.0, 1.0)
        Q = A + AB * u[:, None]
        d2 = ((Q - P) ** 2).sum(axis=1)
        i = int(np.argmin(d2))
        return math.sqrt(float(d2[i])), float(EA[i] + (EB[i] - EA[i]) * u[i]), float(((P - Q[i]) * SO[i]).sum()) > 0.0

    def depth(d, e):
        t = min(1.0, d / SHELF_W)
        return min(e, e + (SHELF_DEPTH - e) * (1.0 - (1.0 - t) ** 2))

    def wanted(x, y):
        if over_ground(x, y):
            return False
        d, _, front = to_run(x, y)
        return front and d <= SHELF_W + 1.0

    pts = list(xy)
    taken = {}

    def crowded(q, r):
        cx, cy = int(q.x // 8.0), int(q.y // 8.0)
        reach = int(math.ceil(r / 8.0))
        return any((q - o).length < r for i in range(-reach, reach + 1) for j in range(-reach, reach + 1)
                   for o in taken.get((cx + i, cy + j), ()))

    rows = 0
    last = 0.0
    for s in SHELF_ROWS:
        r = min(CROWD + SHELF_SPREAD * s, 0.45 * (s - last))
        last = s
        for i in range(len(keys)):
            q = xy[i] + normal[i] * s
            if not wanted(q.x, q.y) or crowded(q, r):
                continue
            pts.append(q)
            taken.setdefault((int(q.x // 8.0), int(q.y // 8.0)), []).append(q)
            rows += 1
    zs = list(edge_z) + [depth(*to_run(p.x, p.y)[:2]) for p in pts[len(keys):]]

    # Where two landforms touch, their sea-facing sides can cross; the triangulator puts a point
    # there, and it takes the shelf's height at it like any other.
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, segs, [], 0, 1e-4, True)
    zmap = []
    for k, p in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(pts)]
        zmap.append(zs[src[0]] if src else depth(*to_run(p.x, p.y)[:2]))
    faces = []
    for tri in out_f:
        c = Vector((sum(out_v[i].x for i in tri) / 3.0, sum(out_v[i].y for i in tri) / 3.0))
        longest = max((out_v[tri[k]] - out_v[tri[(k + 1) % 3]]).length for k in range(3))
        if longest > SHELF_LONGEST or not wanted(c.x, c.y):
            continue
        # Off other ground over the whole face, not only at its centre: each edge's middle, drawn
        # a quarter of the way in, so a side's own rim, which the face shares, is not asked.
        if any(over_ground(*(((out_v[tri[k]] + out_v[tri[(k + 1) % 3]]) * 0.5).lerp(c, 0.25))) for k in range(3)):
            continue
        faces.append(tuple(tri))
    shelf_report = {"faces": len(faces), "shore_m": round(sum((xy[i] - xy[j]).length for i, j in segs), 1),
                    "sides": len(segs), "row_points": rows, "sandy_shore_points": len(sandy),
                    "starting_under_the_cut": sum(1 for z in edge_z if z < cut_z - SNAP), "deepest": round(min(zmap), 2),
                    "shells": "; ".join(shells)}
    if dry or not faces:
        return {}, shelf_report, None

    coef, uv_err = uv_projection()
    tree = KDTree(len(keys))
    for i, k in enumerate(keys):
        tree.insert((k[0], k[1], 0.0), i)
    tree.balance()

    def colour(x, y, z):
        grain = 1.0 + math.sin(x * 0.37) * math.sin(-y * 0.41) * 0.05
        bed = Vector((SEABED[0] * grain, SEABED[1] * grain, SEABED[2] * grain, 1.0))
        if tree.find((x, y, 0.0))[1] not in sandy:
            return bed
        sand = Vector((SAND[0] * grain, SAND[1] * grain, SAND[2] * grain, 1.0))
        return sand.lerp(bed, 1.0 - smoothstep(SEABED_FROM[1], SEABED_FROM[0], z))

    me = build_ground(LANDFORM_SHELF, out_v, zmap, faces, colour, coef, edit,
                      "The landforms' shelf (Ground edit %d): the range's and city's landforms run on below the "
                      "waterline from each sea-facing side, %.1f m under the sea; the shells untouched; built by "
                      "tools/blender/world_terrain_ground_edit.py -- --edit landform_shelf, undone by its --undo" % (
                          edit, SHELF_UNDER))
    area = sum(p.area for p in me.polygons)
    shelf_report.update({"faces": len(me.polygons), "vertices": len(me.vertices), "area_ha": round(area / 10000.0, 1)})
    return {}, shelf_report, LANDFORM_SHELF


def zone_cells(edit, step):
    """The grid cells edit `edit` changed a corner of (by more than `MIN_CHANGE`), as (i, j) for
    the cell [i, i + 1] x [j, j + 1] in `step`s, with every hole filled and every place two cells
    meet only at a corner filled out, so the zone's edge is one simple loop."""
    ob = bpy.data.objects[GRID]
    me = ob.data
    M = ob.matrix_world
    co = coords(ob)
    ed = np.zeros(len(me.vertices), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", ed)
    pre = np.zeros(len(me.vertices))
    me.attributes["height_pre_edit"].data.foreach_get("value", pre)
    cells = set()
    for i in np.nonzero(ed == edit)[0]:
        w = M @ Vector(co[i])
        if abs(w.z - pre[i]) <= MIN_CHANGE:
            continue
        fx, fy = w.x / step, w.y / step
        if abs(fx - round(fx)) > 1e-6 or abs(fy - round(fy)) > 1e-6:
            raise SystemExit("the grid vertex at (%.3f, %.3f) is off its %.0f m lattice" % (w.x, w.y, step))
        for a in (0, -1):
            for b in (0, -1):
                cells.add((round(fx) + a, round(fy) + b))
    while True:
        grew = False
        for (i, j) in list(cells):
            for di, dj in ((1, 1), (1, -1)):
                if (i + di, j + dj) in cells and (i + di, j) not in cells and (i, j + dj) not in cells:
                    cells.add((i + di, j))
                    grew = True
        i0 = min(c[0] for c in cells) - 1
        i1 = max(c[0] for c in cells) + 1
        j0 = min(c[1] for c in cells) - 1
        j1 = max(c[1] for c in cells) + 1
        outside = set()
        todo = [(i0, j0)]
        while todo:
            c = todo.pop()
            if c in outside or c in cells or not (i0 <= c[0] <= i1 and j0 <= c[1] <= j1):
                continue
            outside.add(c)
            todo.extend(((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)))
        holes = {(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)} - cells - outside
        if holes:
            cells |= holes
            grew = True
        if not grew:
            return cells


def zone_loops(cells, step):
    """The zone's edge as loops of corner points, counter-clockwise, the zone on the left."""
    edges = {}
    for (i, j) in cells:
        for a, b in (((i, j), (i + 1, j)), ((i + 1, j), (i + 1, j + 1)), ((i + 1, j + 1), (i, j + 1)), ((i, j + 1), (i, j))):
            if (b, a) in edges:
                del edges[(b, a)]
            else:
                edges[(a, b)] = True
    nxt = {}
    for a, b in edges:
        if a in nxt:
            raise SystemExit("the zone's edge touches itself at (%d, %d)" % a)
        nxt[a] = b
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop = [start]
        p = nxt.pop(start)
        while p != start:
            loop.append(p)
            p = nxt.pop(p)
        n = len(loop)

        def turn(k):
            d0 = (loop[k][0] - loop[k - 1][0], loop[k][1] - loop[k - 1][1])
            d1 = (loop[(k + 1) % n][0] - loop[k][0], loop[(k + 1) % n][1] - loop[k][1])
            return d0 != d1

        loops.append([Vector((c[0] * step, c[1] * step)) for k, c in enumerate(loop) if turn(k)])
    return loops


class Zone:
    """Edit 1's zone: its cells, its edge as straight runs, and where a point lies against them."""

    def __init__(self, cells, step):
        self.cells = cells
        self.step = step
        # One loop per separate piece of the zone; the holes are filled.
        self.loops = zone_loops(cells, step)
        self.runs = []
        self.by_line = {}
        self.perimeters = []
        self.first_run = []
        for li, corners in enumerate(self.loops):
            s = 0.0
            self.first_run.append(len(self.runs))
            for k in range(len(corners)):
                # In Python's doubles, not mathutils' single floats: along a run, distance is
                # exact, so a corner is the same point seen from either side.
                a, b = corners[k], corners[(k + 1) % len(corners)]
                ax, ay, bx, by = float(a.x), float(a.y), float(b.x), float(b.y)
                dx, dy = (bx > ax) - (bx < ax), (by > ay) - (by < ay)
                length = abs(bx - ax) + abs(by - ay)
                run = {"loop": li, "a": a, "b": b, "ax": ax, "ay": ay, "dx": dx, "dy": dy, "len": length, "s0": s,
                       "horizontal": dy == 0, "inside": Vector((-dy, dx))}
                self.runs.append(run)
                key = ("y", round(ay / step)) if run["horizontal"] else ("x", round(ax / step))
                self.by_line.setdefault(key, []).append(len(self.runs) - 1)
                s += length
            self.perimeters.append(s)
        xs = [c.x for loop in self.loops for c in loop]
        ys = [c.y for loop in self.loops for c in loop]
        self.box = (min(xs), max(xs), min(ys), max(ys))

    def next_run(self, ri):
        """The run after `ri` round its loop."""
        li = self.runs[ri]["loop"]
        nxt = ri + 1
        if nxt == len(self.runs) or self.runs[nxt]["loop"] != li:
            nxt = self.first_run[li]
        return nxt

    def inside(self, x, y):
        return (math.floor(x / self.step), math.floor(y / self.step)) in self.cells

    def on_edge(self, x, y, tol=1e-4):
        """The runs (index, distance along) that (x, y) lies on."""
        out = []
        for axis, c, along in (("y", y, x), ("x", x, y)):
            k = round(c / self.step)
            if abs(c - k * self.step) > tol:
                continue
            for ri in self.by_line.get((axis, k), ()):
                r = self.runs[ri]
                u = (x - r["ax"]) * r["dx"] + (y - r["ay"]) * r["dy"]
                if -tol <= u <= r["len"] + tol:
                    out.append((ri, min(max(u, 0.0), r["len"])))
        return out

    def edge_distance(self, x, y, within=math.inf):
        """The distance from (x, y) to the zone's edge, looked for only `within` that of it."""
        best = math.inf
        span = self.step if within == math.inf else within
        for axis, c in (("y", y), ("x", x)):
            k0 = math.floor((c - span) / self.step)
            k1 = math.ceil((c + span) / self.step)
            rng = range(k0, k1 + 1) if within != math.inf else None
            keys = [(axis, k) for k in rng] if rng is not None else [key for key in self.by_line if key[0] == axis]
            for key in keys:
                for ri in self.by_line.get(key, ()):
                    best = min(best, self.run_distance(ri, x, y))
        return best

    def run_distance(self, ri, x, y):
        r = self.runs[ri]
        px, py = x - r["ax"], y - r["ay"]
        u = min(max(px * r["dx"] + py * r["dy"], 0.0), r["len"])
        return math.hypot(px - r["dx"] * u, py - r["dy"] * u)

    def nearest_run(self, x, y):
        return min(range(len(self.runs)), key=lambda ri: self.run_distance(ri, x, y))

    def face_inside(self, f):
        """Whether a face cut along the zone's edge lies in the zone: tested at its centre, or
        halfway from it to a corner when the centre sits on the edge."""
        c = f.calc_center_median()
        for q in [c] + [c.lerp(v.co, 0.5) for v in f.verts]:
            if not self.on_edge(q.x, q.y, 1e-5):
                return self.inside(q.x, q.y)
        raise SystemExit("a face at (%.2f, %.2f) lies along the zone's edge: %s, area %.6f" % (
            c.x, c.y, [tuple(round(x, 4) for x in v.co) for v in f.verts], f.calc_area()))


def as_exported(bm, me, indices):
    """Rebuild the faces `indices` as the triangles the exporter draws (Blender's own loop
    triangles), so a non-planar face can be cut without its surface moving."""
    me.calc_loop_triangles()
    tris = {}
    for lt in me.loop_triangles:
        if lt.polygon_index in indices:
            tris.setdefault(lt.polygon_index, []).append(tuple(lt.vertices))
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    held = [(bm.faces[pi], [[bm.verts[i] for i in t] for t in ts]) for pi, ts in tris.items()]
    gone = []
    for f, ts in held:
        if len(f.verts) == 3:
            continue
        for t in ts:
            nf = bm.faces.new(t)
            nf.material_index = f.material_index
            nf.smooth = f.smooth
        gone.append(f)
    bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')


def all_hits(tree, x, y):
    out = []
    z = 5000.0
    while True:
        hit = tree.ray_cast(Vector((x, y, z)), Vector((0.0, 0.0, -1.0)))
        if hit[0] is None:
            return out
        out.append(hit[0].z)
        z = hit[0].z - 1e-4


def range_band(z):
    for top, name in TOE_BANDS:
        if z < top:
            return name
    return TOE_BANDS[-1][1]


def range_blend(edit, now_t, pre_t, dry):
    """Edit 1 on the landforms it lands on: one sheet in the zone it changed, the shells cut along
    that zone's edge, emptied inside it and capped (see `RANGE_BLEND`)."""
    name = RANGE_BLEND[edit]
    if name in bpy.data.objects:
        raise SystemExit("%s already exists" % name)
    script = "world_terrain_edit_blend_south_range.py"
    step = float(edit_constant(script, "STEP"))
    sea = float(edit_constant(script, "SEA_LEVEL"))
    zone = Zone(zone_cells(edit, step), step)
    zb = zone.box
    print("  zone: %d cells, %.1f ha, %d runs, x %.0f..%.0f, y %.0f..%.0f" % (
        len(zone.cells), len(zone.cells) * step * step / 10000.0, len(zone.runs), *zb))

    def near(ob, margin):
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        return not (max(b.x for b in bb) < zb[0] - margin or min(b.x for b in bb) > zb[1] + margin or
                    max(b.y for b in bb) < zb[2] - margin or min(b.y for b in bb) > zb[3] + margin)

    shells = []
    decor = []
    for ob in ground_objects():
        if not near(ob, 1.0):
            continue
        if ob.matrix_world != ob.matrix_world.Identity(4):
            raise SystemExit("%s is not at the origin; Ground objects hold world positions" % ob.name)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        closed = not any(e.is_boundary for e in bm.edges)
        bm.free()
        if ob.get("kyt_collision") == "none":
            decor.append(ob)
        elif closed:
            shells.append(ob)
        else:
            raise SystemExit("%s is open and collides; edit 1 knows only closed shells" % ob.name)
    print("  shells: %s; decoration: %s" % (", ".join(o.name for o in shells), ", ".join(o.name for o in decor) or "none"))

    # The ground as it stands, before anything is cut: its top, and whose face that is.
    before = {}
    for ob in shells:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mats = [ob.data.materials[f.material_index].name for f in bm.faces]
        before[ob.name] = (BVHTree.FromBMesh(bm), mats)
        bm.free()

    def top_before(x, y):
        best = None
        for oname, (tree, mats) in before.items():
            hit = tree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
            if hit[0] is not None and (best is None or hit[0].z > best[0]):
                best = (hit[0].z, mats[hit[2]])
        return best

    # How far the edit cut the grid and how far it raised it, each a surface of its own. The fade
    # reads their sum, not the change itself, which where a cut row meets a raised row (the wall
    # at z 5500, cut 80 m above and raised 75 m below) passes through nothing halfway and would
    # fade the edit out along that line, wall and all. And the ground is cut only where the edit
    # cut, raised only where it raised, beyond `AGAINST`: by the coastal branch's end the grid
    # sampled the hill either side of the road's cutting, 35 m over its floor, and the design,
    # 2 m under the grid there, would otherwise fill the cutting.
    gob = bpy.data.objects[GRID]
    gco = [gob.matrix_world @ Vector(v) for v in coords(gob)]
    ged = np.zeros(len(gco), dtype=np.int32)
    gob.data.attributes["authored_edit"].data.foreach_get("value", ged)
    gpre = np.zeros(len(gco))
    gob.data.attributes["height_pre_edit"].data.foreach_get("value", gpre)
    gpolys = [tuple(p.vertices) for p in gob.data.polygons]
    gcut = [max(0.0, gpre[i] - v.z) if ged[i] == edit else 0.0 for i, v in enumerate(gco)]
    graised = [max(0.0, v.z - gpre[i]) if ged[i] == edit else 0.0 for i, v in enumerate(gco)]

    def field(values):
        return BVHTree.FromPolygons([Vector((v.x, v.y, values[i])) for i, v in enumerate(gco)], gpolys)

    cut_t, raised_t = field(gcut), field(graised)

    def moved(x, y):
        return height(cut_t, x, y), height(raised_t, x, y)

    # Edit 1 held the coastal branch's road box fixed (its `NO_RAISE`, Godot x0, x1, z0, z1) so
    # the blend worked round the road. A cell beyond it the grid still moved a little, over ground
    # the grid never saw (the road's cutting and the hill beside it, up to 35 m under the grid),
    # so there the ground comes down with the design and does not rise at all.
    nr = edit_constant(script, "NO_RAISE")
    held = (nr[0] - step, nr[1] + step, -nr[3] - step, -nr[2] + step)

    def target(x, y):
        """Where edit 1 puts the ground at (x, y): the ground as it stands where the edit left the
        grid alone, its designed surface where it moved the grid by `BLEND` or more, faded
        between. The design wins outright, as in `designed`, except against the edit's own
        direction, where `AGAINST` holds (see `cut_t`). Where the game had open sea, the ground
        as it stands is the grid's sea floor, kept a metre under the water: in a cell between
        sea and a cliff the grid rises straight across it, and that is no land anyone designed."""
        t = height(now_t, x, y)
        p = height(pre_t, x, y)
        top = top_before(x, y)
        base = top[0] if top is not None else min(p, sea - 1.0)
        cut, raised = moved(x, y)
        if cut + raised <= MIN_CHANGE:
            return base
        change = t - base
        if change < 0.0 and cut <= MIN_CHANGE:
            change = max(change, -AGAINST)
        elif change > 0.0 and held[0] <= x <= held[1] and held[2] <= y <= held[3]:
            change = 0.0
        elif change > 0.0 and raised <= MIN_CHANGE:
            change = min(change, AGAINST)
        # Faded by distance from the zone's edge as well: there the grid, a straight line between
        # two of its samples, stands off the shells' own surface, and faded over `BLEND` alone the
        # sheet stepped from the one to the other within a metre, a saw along the edge's stair.
        edge = smoothstep(0.0, EDGE_FADE, zone.edge_distance(x, y, EDGE_FADE))
        return base + min(1.0, (cut + raised) / BLEND) * edge * change

    # Each shell cut along the zone's edge: the faces near the zone first rebuilt as the
    # triangles the game draws, then split along every run.
    work = {}
    for ob in shells + decor:
        me = ob.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        fa = bm.faces.layers.int.get("authored_edit") or bm.faces.layers.int.new("authored_edit")
        bm.faces.ensure_lookup_table()

        def overlaps(f, margin=1.0):
            xs = [v.co.x for v in f.verts]
            ys = [v.co.y for v in f.verts]
            return not (max(xs) < zb[0] - margin or min(xs) > zb[1] + margin or max(ys) < zb[2] - margin or min(ys) > zb[3] + margin)

        near_faces = {f.index for f in bm.faces if overlaps(f)}
        ring = {g.index for i in near_faces for v in bm.faces[i].verts for g in v.link_faces}
        as_exported(bm, me, near_faces | ring)
        kept_ngons = {f: len(f.verts) for f in bm.faces if len(f.verts) > 3}
        for r in zone.runs:
            if r["horizontal"]:
                c, lo, hi = r["a"].y, min(r["a"].x, r["b"].x), max(r["a"].x, r["b"].x)
            else:
                c, lo, hi = r["a"].x, min(r["a"].y, r["b"].y), max(r["a"].y, r["b"].y)
            cand = []
            for f in bm.faces:
                if r["horizontal"]:
                    across = [v.co.y for v in f.verts]
                    along = [v.co.x for v in f.verts]
                else:
                    across = [v.co.x for v in f.verts]
                    along = [v.co.y for v in f.verts]
                if min(across) < c - 1e-6 and max(across) > c + 1e-6 and max(along) > lo - 1e-6 and min(along) < hi + 1e-6:
                    cand.append(f)
            if not cand:
                continue
            geom = set(cand)
            for f in cand:
                geom.update(f.edges)
                geom.update(f.verts)
            no = Vector((0.0, 1.0, 0.0)) if r["horizontal"] else Vector((1.0, 0.0, 0.0))
            co = Vector((0.0, c, 0.0)) if r["horizontal"] else Vector((c, 0.0, 0.0))
            # A vertex within 0.1 mm of the line counts as on it; each cut's vertices go onto the
            # line exactly (the cut leaves them up to 3e-5 off; the lines are whole metres), so the
            # next cut finds them there and both rims of a corner agree to the bit.
            cut = bmesh.ops.bisect_plane(bm, geom=list(geom), dist=1e-4, plane_co=co, plane_no=no)
            for v in cut["geom_cut"]:
                if isinstance(v, bmesh.types.BMVert):
                    if r["horizontal"]:
                        v.co.y = c
                    else:
                        v.co.x = c
        degenerate = [f for f in bm.faces if f.calc_area() < 1e-8]
        if degenerate:
            c = degenerate[0].calc_center_median()
            raise SystemExit("%s: the cut left %d faces of no area, the first at (%.3f, %.3f)" % (ob.name, len(degenerate), c.x, c.y))
        for f, n in kept_ngons.items():
            if not f.is_valid or len(f.verts) != n:
                raise SystemExit("%s: a face away from the zone was cut; widen the ring rebuilt first" % ob.name)
        pieces = [f for f in bm.faces if len(f.verts) > 3 and f not in kept_ngons]
        if pieces:
            bmesh.ops.triangulate(bm, faces=pieces)
        gone = [f for f in bm.faces if overlaps(f, 0.0) and zone.face_inside(f)]
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        work[ob.name] = {"bm": bm, "fa": fa, "deleted": len(gone), "faces_before": len(me.polygons)}

    # The rim each shell is left with lies on the zone's edge; along each run, the topmost rim
    # is the ground the sheet meets.
    rims = {}
    for ob in shells:
        bm = work[ob.name]["bm"]
        rim = []
        for e in bm.edges:
            if not e.is_boundary:
                continue
            a, b = e.verts
            ra = {ri for ri, _ in zone.on_edge(a.co.x, a.co.y)}
            rb = {ri for ri, _ in zone.on_edge(b.co.x, b.co.y)}
            if not (ra & rb):
                raise SystemExit("%s: an open edge at (%.2f, %.2f) is off the zone's edge" % (ob.name, a.co.x, a.co.y))
            rim.append(e)
        rims[ob.name] = rim
    splits = {ob.name: {} for ob in shells}
    boundary = {}
    corner_ends = []
    jumps = 0
    for ri, r in enumerate(zone.runs):
        segs = []
        for ob in shells:
            for e in rims[ob.name]:
                a, b = e.verts
                on_a = {k: u for k, u in zone.on_edge(a.co.x, a.co.y)}
                on_b = {k: u for k, u in zone.on_edge(b.co.x, b.co.y)}
                if ri in on_a and ri in on_b:
                    segs.append((on_a[ri], a.co.z, on_b[ri], b.co.z, ob.name, e, a, b))
        flat = [s for s in segs if abs(s[2] - s[0]) > 1e-6]

        def z_on(s, u):
            return s[1] + (u - s[0]) / (s[2] - s[0]) * (s[3] - s[1])

        def point(u):
            return r["ax"] + r["dx"] * u, r["ay"] + r["dy"] * u

        cuts = {0.0, r["len"]}
        for s in segs:
            cuts.update((min(max(s[0], 0.0), r["len"]), min(max(s[2], 0.0), r["len"])))
        for i in range(len(flat)):
            for j in range(i + 1, len(flat)):
                s, t = flat[i], flat[j]
                lo = max(min(s[0], s[2]), min(t[0], t[2]))
                hi = min(max(s[0], s[2]), max(t[0], t[2]))
                if hi - lo <= 1e-6:
                    continue
                f0 = z_on(s, lo) - z_on(t, lo)
                f1 = z_on(s, hi) - z_on(t, hi)
                if f0 * f1 < 0.0:
                    cuts.add(lo + (hi - lo) * f0 / (f0 - f1))
        cuts = sorted(cuts)
        pieces = []
        for u0, u1 in zip(cuts, cuts[1:]):
            if u1 - u0 <= 1e-6:
                continue
            mid = 0.5 * (u0 + u1)
            cover = [s for s in flat if min(s[0], s[2]) < mid < max(s[0], s[2])]
            owner = max(cover, key=lambda s: z_on(s, mid)) if cover else None
            if pieces and pieces[-1][2] is owner:
                pieces[-1][1] = u1
            else:
                pieces.append([u0, u1, owner])

        def piece_z(p, u):
            if p[2] is None:
                # Open sea along the edge: the edit left the grid alone here, so `target` there.
                return target(*point(u))
            return z_on(p[2], u)

        def vertex_at(p, u):
            s = p[2] if p is not None else None
            if s is None:
                return None
            if abs(u - s[0]) <= 1e-6:
                return s[6]
            if abs(u - s[2]) <= 1e-6:
                return s[7]
            return None

        def edge_point(p, q, u, z):
            """The sheet's edge point at u, where piece p ends and piece q begins (either may be
            None): an owner's own vertex there, or a new point split into the owners' edges. Its
            position is the shell's own, to the last bit, so the two rims are one edge."""
            own = next((v for v in (vertex_at(p, u), vertex_at(q, u)) if v is not None), None)
            if own is not None:
                at = own.co.copy()
            else:
                x, y = point(u)
                at = Vector((x, y, z))
            for piece in (p, q):
                if piece is not None and piece[2] is not None and vertex_at(piece, u) is None:
                    splits[piece[2][4]].setdefault(piece[2][5], []).append(at)
            return at

        # A piece of the edge shorter than this is bridged, not followed: the sheet's edge spans
        # it, and what it leaves is a hairline, narrower than anything to see through.
        pieces = [p for k, p in enumerate(pieces) if p[1] - p[0] >= 4.0 * JUMP or k in (0, len(pieces) - 1)]
        run_pts = []
        for k, p in enumerate(pieces):
            u0, u1 = p[0], p[1]
            if k == 0:
                run_pts.append(edge_point(None, p, u0, piece_z(p, u0)))
            if p[2] is None:
                n = int(math.ceil((u1 - u0) / RANGE_LATTICE))
                for m in range(1, n):
                    u = u0 + (u1 - u0) * m / n
                    run_pts.append(Vector((*point(u), piece_z(p, u))))
            if k + 1 < len(pieces):
                q = pieces[k + 1]
                v0 = q[0]
                zl, zr = piece_z(p, u1), piece_z(q, v0)
                if v0 - u1 <= 1e-6 and abs(zl - zr) <= 1e-4:
                    run_pts.append(edge_point(p, q, u1, zl))
                else:
                    # A step: the ground drops down a shell's side here. The sheet cannot stand
                    # straight, so it takes the step over a hair of its edge, `JUMP` either side.
                    dl = min(JUMP, 0.25 * (u1 - u0))
                    dr = min(JUMP, 0.25 * (q[1] - v0))
                    run_pts.append(edge_point(p, None, u1 - dl, piece_z(p, u1 - dl)))
                    run_pts.append(edge_point(None, q, v0 + dr, piece_z(q, v0 + dr)))
                    jumps += 1
            else:
                run_pts.append(edge_point(p, None, u1, piece_z(p, u1)))
        # Each run ends at the corner the next begins at.
        corner_ends.append((run_pts[0], run_pts[-1], pieces[0][2][4] if pieces[0][2] else None,
                            pieces[-1][2][4] if pieces[-1][2] else None,
                            [(round(s[0], 4), round(s[1], 4), round(s[2], 4), round(s[3], 4), s[4]) for s in segs
                             if min(s[0], s[2]) < 0.05 or max(s[0], s[2]) > r["len"] - 0.05]))
        boundary.setdefault(r["loop"], []).extend(run_pts[:-1])
    for k in range(len(corner_ends)):
        end = corner_ends[k][1]
        start = corner_ends[zone.next_run(k)][0]
        if (end - start).length > 1e-3:
            raise SystemExit("the ground at the zone's corner (%.2f, %.2f) is %.3f m apart along its two sides: %s %s / %s %s\n%s\n%s" % (
                end.x, end.y, (end - start).length, tuple(end), corner_ends[k][3], tuple(start), corner_ends[zone.next_run(k)][2],
                corner_ends[k][4], corner_ends[zone.next_run(k)][4]))

    # Split the topmost rims where the sheet's edge turns, so every edge of the sheet's rim is an
    # edge of a shell.
    split_count = 0
    for oname, by_edge in splits.items():
        for e, ps in by_edge.items():
            v_from, v_to = e.verts
            ps = sorted(ps, key=lambda p: (p - v_from.co).length)
            ps = [p for k, p in enumerate(ps) if k == 0 or (p - ps[k - 1]).length > 1e-6]
            cur = e
            for p in ps:
                span = (v_to.co - v_from.co).length
                t = (p - v_from.co).length / span
                _, nv = bmesh.utils.edge_split(cur, v_from, t)
                nv.co = p
                cur = next(g for g in nv.link_edges if v_to in g.verts)
                v_from = nv
                split_count += 1
    for oname in splits:
        bm = work[oname]["bm"]
        quads = [f for f in bm.faces if len(f.verts) > 3 and any(zone.on_edge(v.co.x, v.co.y) for v in f.verts)]
        if quads:
            bmesh.ops.triangulate(bm, faces=quads)

    # Caps: each shell closed again along its cut, flat on the zone's edge, facing into the zone.
    caps = {}
    for ob in shells:
        bm = work[ob.name]["bm"]
        fa = work[ob.name]["fa"]
        me = ob.data
        walls = [p.material_index for p in me.polygons if abs(p.normal.z) <= 0.05]
        wall_mat = max(set(walls), key=walls.count) if walls else 0
        rim = [e for e in bm.edges if e.is_boundary]
        link = {}
        for e in rim:
            for v in e.verts:
                link.setdefault(v, []).append(e)
        if any(len(es) != 2 for es in link.values()):
            raise SystemExit("%s: its cut rim branches" % ob.name)
        seen = set()
        made = 0
        for e0 in rim:
            if e0 in seen:
                continue
            loop = [e0.verts[0]]
            e = e0
            v = e0.verts[1]
            seen.add(e0)
            while v is not loop[0]:
                loop.append(v)
                e = next(g for g in link[v] if g is not e)
                seen.add(e)
                v = e.other_vert(v)

            def s_of(v):
                ri, u = zone.on_edge(v.co.x, v.co.y)[0]
                return zone.runs[ri]["loop"], zone.runs[ri]["s0"] + u

            li = s_of(loop[0])[0]
            if any(s_of(v)[0] != li for v in loop):
                raise SystemExit("%s: one rim of its cut lies on two pieces of the zone" % ob.name)
            per = zone.perimeters[li]
            s = [s_of(loop[0])[1]]
            for v in loop[1:] + loop[:1]:
                d = s_of(v)[1] - s[-1] % per
                d = (d + 0.5 * per) % per - 0.5 * per
                s.append(s[-1] + d)
            if abs(s.pop() - s[0]) > 1e-3:
                raise SystemExit("%s: its cut runs right round a piece of the zone" % ob.name)
            pts = [Vector((s[k], loop[k].co.z)) for k in range(len(loop))]
            area = sum(pts[k].x * pts[(k + 1) % len(pts)].y - pts[(k + 1) % len(pts)].x * pts[k].y for k in range(len(pts)))
            order = list(range(len(loop))) if area > 0.0 else list(reversed(range(len(loop))))
            # Across a corner of the zone the cap must fold, not cut the corner: a constraint up
            # each corner the rim passes.
            cons = []
            lo, hi = min(s), max(s)
            for r in zone.runs:
                if r["loop"] != li:
                    continue
                for k in range(int(math.floor((lo - r["s0"]) / per)), int(math.ceil((hi - r["s0"]) / per)) + 1):
                    sc = r["s0"] + k * per
                    at = sorted((i for i in range(len(loop)) if abs(s[i] - sc) < 1e-4), key=lambda i: pts[i].y)
                    for i, j in zip(at, at[1:]):
                        m = Vector((sc, 0.5 * (pts[i].y + pts[j].y)))
                        inside = False
                        for k2 in range(len(pts)):
                            p0, p1 = pts[k2], pts[(k2 + 1) % len(pts)]
                            if (p0.y > m.y) != (p1.y > m.y) and m.x < p0.x + (m.y - p0.y) * (p1.x - p0.x) / (p1.y - p0.y):
                                inside = not inside
                        if inside:
                            cons.append((i, j))
            out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, cons, [order], 1, 1e-6, True)
            idx = []
            for k, ov in enumerate(orig_v):
                src = [i for i in ov if i < len(loop)]
                if not src:
                    raise SystemExit("%s: its cap needed a point the rim does not have, at s %.2f z %.2f" % (ob.name, out_v[k].x, out_v[k].y))
                idx.append(src[0])
            for tri in out_f:
                vs = [loop[idx[i]] for i in tri]
                if len(set(vs)) < 3:
                    continue
                nf = bm.faces.new(vs)
                nf.material_index = wall_mat
                nf.smooth = False
                nf[fa] = edit
                nf.normal_update()
                c = nf.calc_center_median()
                inward = zone.runs[zone.nearest_run(c.x, c.y)]["inside"]
                if nf.normal.x * inward.x + nf.normal.y * inward.y < 0.0:
                    nf.normal_flip()
                made += 1
        caps[ob.name] = made
        if any(e.is_boundary for e in bm.edges):
            raise SystemExit("%s is still open after its caps" % ob.name)
        if any(len(e.link_faces) > 2 for e in bm.edges):
            raise SystemExit("%s: an edge with more than two faces after its caps" % ob.name)

    # The sheet: its edge as found, the grid's own vertices and a lattice inside, and where the
    # edit faded in or left the ground alone, the shells' own top vertices. By the road box the
    # ground keeps the shape the grid never saw (the road's cutting), so there the sheet takes
    # every top vertex of the shells and a `HELD_LATTICE` lattice, and its triangles do not
    # bridge the cutting.
    pts = []
    zs = []
    rings = []
    for li in sorted(boundary):
        rings.append(list(range(len(pts), len(pts) + len(boundary[li]))))
        pts.extend(Vector((p.x, p.y)) for p in boundary[li])
        zs.extend(p.z for p in boundary[li])
    nb = len(pts)
    crowd = 0.35 * RANGE_LATTICE
    taken = {}

    def in_held(q):
        return held[0] <= q.x <= held[1] and held[2] <= q.y <= held[3]

    def crowded(q):
        near = 0.35 * HELD_LATTICE if in_held(q) else crowd
        cx, cy = int(q.x // crowd), int(q.y // crowd)
        return any((q - o).length < near for i in (-1, 0, 1) for j in (-1, 0, 1) for o in taken.get((cx + i, cy + j), ()))

    def take(q):
        taken.setdefault((int(q.x // crowd), int(q.y // crowd)), []).append(q)

    for q in pts:
        take(q)
    # The grid's vertices and the lattice stand `OFF_LINE` off the grid's lines: the foothills
    # were drawn on the same 25 m lattice, so their old wall stands on a grid row, and on it the
    # ground as it stands is the plateau's edge and the base at once.
    cand = []
    for oname, (tree, mats) in before.items():
        for v in bpy.data.objects[oname].data.vertices:
            q = Vector((v.co.x, v.co.y))
            top = top_before(q.x, q.y)
            if top is not None and abs(top[0] - v.co.z) < 1e-3 and (in_held(q) or sum(moved(q.x, q.y)) < BLEND):
                cand.append(q)
    # Rows a little inside the edge, so the fade there is drawn, not spanned by long fans.
    for r in zone.runs:
        n = int(math.ceil(r["len"] / EDGE_ROW))
        for inset in (EDGE_FADE / 3.0, 2.0 * EDGE_FADE / 3.0):
            for k in range(n):
                u = (k + 0.5) * r["len"] / n
                cand.append(Vector((r["ax"] + r["dx"] * u - r["dy"] * inset, r["ay"] + r["dy"] * u + r["dx"] * inset)))
    x = math.floor(held[0] / HELD_LATTICE) * HELD_LATTICE
    while x <= held[1]:
        y = math.floor(held[2] / HELD_LATTICE) * HELD_LATTICE
        while y <= held[3]:
            cand.append(Vector((x + OFF_LINE, y + OFF_LINE)))
            y += HELD_LATTICE
        x += HELD_LATTICE
    cand.extend(Vector((v.x + OFF_LINE, v.y + OFF_LINE)) for v in gco)
    x = math.floor(zb[0] / RANGE_LATTICE) * RANGE_LATTICE
    while x <= zb[1]:
        y = math.floor(zb[2] / RANGE_LATTICE) * RANGE_LATTICE
        while y <= zb[3]:
            cand.append(Vector((x + OFF_LINE, y + OFF_LINE)))
            y += RANGE_LATTICE
        x += RANGE_LATTICE
    for q in cand:
        if not (zb[0] < q.x < zb[1] and zb[2] < q.y < zb[3]) or not zone.inside(q.x, q.y):
            continue
        clear = 0.3 * (HELD_LATTICE if in_held(q) else RANGE_LATTICE)
        if zone.edge_distance(q.x, q.y, clear) < clear or crowded(q):
            continue
        take(q)
        pts.append(q)
        zs.append(target(q.x, q.y))
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, [], rings, 1, 1e-5, True)
    zmap = []
    for k, ov in enumerate(orig_v):
        src = [i for i in ov if i < len(pts)]
        if not src:
            raise SystemExit("the sheet's triangulation added a point at (%.2f, %.2f)" % (out_v[k].x, out_v[k].y))
        zmap.append(zs[src[0]])
    merged = sum(1 for ov in orig_v if len([i for i in ov if i < len(pts)]) > 1)
    if merged:
        raise SystemExit("the sheet's triangulation merged %d of its points" % merged)

    report = {}
    for oname, w in work.items():
        report[oname] = {"faces_before": w["faces_before"], "faces_in_zone_removed": w["deleted"],
                         "cap_faces": caps.get(oname, 0)}
    sheet = {"zone_ha": round(len(zone.cells) * step * step / 10000.0, 1), "edge_points": nb, "rim_splits": split_count,
             "steps_along_edge": jumps, "faces": len(out_f)}
    if dry:
        for w in work.values():
            w["bm"].free()
        return report, sheet, None

    # The shells as they were, whole, for the undo.
    hist = history_collection()
    for ob in shells + decor:
        hme = ob.data.copy()
        hme.name = "%s__before_edit%d" % (ob.name, edit)
        hob = bpy.data.objects.new(hme.name, hme)
        hob["kyt_whole"] = 1
        hob["kyt_note"] = "%s whole as it stood before Ground edit %d, for its --undo; never exported" % (ob.name, edit)
        hist.objects.link(hob)
    old_tris = {}
    for ob in shells + decor:
        me = ob.data
        me.calc_loop_triangles()
        old_tris[ob.name] = [tuple(tuple(me.vertices[i].co) for i in lt.vertices) for lt in me.loop_triangles]
        bm = work[ob.name]["bm"]
        bm.to_mesh(me)
        bm.free()
        me.update()

    # The sheet's faces take the colour of the ground the edit found under them: the range's
    # level bands again at their new height; where the edit made land out of the sea, the
    # range's cove sand under `SAND_BELOW`, its bands above.
    mats = []
    faces = []
    findex = []
    verts = [(p.x, p.y, zmap[k]) for k, p in enumerate(out_v)]
    for tri in out_f:
        a, b, c = (Vector(verts[i]) for i in tri)
        if (b - a).cross(c - a).z < 0.0:
            tri = [tri[0], tri[2], tri[1]]
        m = (a + b + c) / 3.0
        top = top_before(m.x, m.y)
        if top is None:
            mat = "distant_range_cove_sand" if m.z < SAND_BELOW else range_band(m.z)
        elif top[1] in (band for _, band in TOE_BANDS):
            mat = range_band(m.z)
        else:
            mat = top[1]
        if mat not in mats:
            mats.append(mat)
        faces.append(tuple(tri))
        findex.append(mats.index(mat))
    sheet_me = bpy.data.meshes.new(name)
    sheet_me.from_pydata(verts, [], faces)
    sheet_me.validate()
    for mat in mats:
        sheet_me.materials.append(bpy.data.materials[mat])
    sheet_me.polygons.foreach_set("material_index", findex)
    sheet_me.polygons.foreach_set("use_smooth", [True] * len(sheet_me.polygons))
    fa = sheet_me.attributes.new("authored_edit", 'INT', 'FACE')
    fa.data.foreach_set("value", [edit] * len(sheet_me.polygons))
    sob = bpy.data.objects.new(name, sheet_me)
    sob["kyt_note"] = ("Ground edit %d, the south range blend: one sheet where the grid edit changed the range's and "
                       "city's landforms, which are cut along its edge and capped; built by "
                       "tools/blender/world_terrain_ground_edit.py -- --edit %d, undone by its --undo" % (edit, edit))
    bpy.data.collections[GROUND].objects.link(sob)
    sheet_me.update()

    # Proof. Outside the zone every shell's surface is where it was: each triangle the cut did
    # not touch is still there exactly, and on every one it touched (rebuilt or split), points
    # sampled off the zone's edge lie on the other surface, the old on the new and the new on
    # the old.
    worst_outside = 0.0
    worst_at = None
    kept_exactly = 0
    for ob in shells + decor:
        me = ob.data
        me.calc_loop_triangles()
        new = [tuple(tuple(me.vertices[i].co) for i in lt.vertices) for lt in me.loop_triangles]
        bm = bmesh.new()
        bm.from_mesh(me)
        new_tree = BVHTree.FromBMesh(bm)
        bm.free()
        old = old_tris[ob.name]
        old_tree = BVHTree.FromPolygons([Vector(c) for t in old for c in t], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(old))])
        old_keys = {tuple(sorted(t)) for t in old}
        new_keys = {tuple(sorted(t)) for t in new}
        kept_exactly += len(old_keys & new_keys)
        for side, tris, other, theirs in (("old", old, new_tree, new_keys), ("new", new, old_tree, old_keys)):
            for t in tris:
                if tuple(sorted(t)) in theirs:
                    continue
                A, B, C = (Vector(c) for c in t)
                if (B - A).cross(C - A).length < 1e-6:
                    continue
                for bary in ((1 / 3, 1 / 3, 1 / 3), (0.8, 0.1, 0.1), (0.1, 0.8, 0.1), (0.1, 0.1, 0.8), (0.45, 0.45, 0.1), (0.1, 0.45, 0.45), (0.45, 0.1, 0.45)):
                    q = A * bary[0] + B * bary[1] + C * bary[2]
                    if zone.inside(q.x, q.y) or zone.edge_distance(q.x, q.y, 0.01) < 0.01:
                        continue
                    # How far the point is from the other surface: straight down, or in 3D for a
                    # shell's straight sides, which a ray from above never meets. Either near
                    # enough will do: the nearest-point search is a few centimetres out on the
                    # range's long sliver faces, and the ray slips through the crease of a side.
                    down = min((abs(h - q.z) for h in all_hits(other, q.x, q.y)), default=math.inf)
                    off = min(down, (other.find_nearest(q)[0] - q).length)
                    if off > worst_outside:
                        worst_outside = off
                        worst_at = (ob.name, side, tuple(round(c, 3) for c in q), [tuple(round(x, 3) for x in c) for c in t])
    if worst_outside > 0.01:
        raise SystemExit("a shell's surface outside the zone moved by %.4f m: %s" % (worst_outside, worst_at))

    # The sheet's rim is the shells' cut, edge for edge, wherever it stands clear of the water.
    keys = set()
    for ob in shells:
        for e in ob.data.edges:
            a, b = (tuple(round(c, 4) for c in ob.data.vertices[i].co) for i in e.vertices)
            keys.add((min(a, b), max(a, b)))
    bm = bmesh.new()
    bm.from_mesh(sheet_me)
    open_above = 0
    open_at = []
    vkeys = {k for pair in keys for k in pair}
    for e in bm.edges:
        if not e.is_boundary:
            continue
        a, b = e.verts
        if max(a.co.z, b.co.z) < sea + 1.0 or (a.co.xy - b.co.xy).length < 0.3:
            continue
        ka, kb = tuple(round(c, 4) for c in a.co), tuple(round(c, 4) for c in b.co)
        if (min(ka, kb), max(ka, kb)) not in keys:
            open_above += 1
            if len(open_at) < 6:
                open_at.append((ka, ka in vkeys, kb, kb in vkeys))
    sheet_tree = BVHTree.FromBMesh(bm)
    bm.free()
    if open_above:
        raise SystemExit("%s: %d edges of its rim above the water meet no shell: %s" % (name, open_above, open_at))

    # Inside the zone the sheet is the ground, at the edit's surface.
    after = []
    for ob in shells:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        after.append(BVHTree.FromBMesh(bm))
        bm.free()
    errs = []
    poke = 0
    dry_new = 0.0
    sample = 5.0
    x = math.floor(zb[0] / sample) * sample + 0.5 * sample
    while x < zb[1]:
        y = math.floor(zb[2] / sample) * sample + 0.5 * sample
        while y < zb[3]:
            if zone.inside(x, y) and zone.edge_distance(x, y, 1.0) > 1.0:
                h = height(sheet_tree, x, y)
                if h is None:
                    raise SystemExit("the sheet has a hole at (%.1f, %.1f)" % (x, y))
                errs.append(abs(h - target(x, y)))
                for tree in after:
                    g = height(tree, x, y)
                    if g is not None and g > h + 0.01:
                        poke += 1
                top = top_before(x, y)
                if h > sea and (top is None or top[0] <= sea):
                    dry_new += sample * sample
            y += sample
        x += sample
    if poke:
        raise SystemExit("a shell stands above the sheet at %d points in the zone" % poke)
    errs.sort()
    sheet.update({"faces": len(sheet_me.polygons), "vertices": len(sheet_me.vertices), "materials": len(mats),
                  "off_design_p99": round(errs[int(0.99 * len(errs))], 2), "off_design_most": round(errs[-1], 2),
                  "new_dry_land_ha": round(dry_new / 10000.0, 1), "shell_surface_outside_moved": round(worst_outside, 6),
                  "shell_triangles_kept_exactly": kept_exactly})
    return report, sheet, name


def road_natural(edit, now_t, pre_t, box, dry):
    """The designed natural ground under the road corridor where edit `edit` reshapes what the
    corridor covers (`ROAD_NATURAL`): every point of the edit's box with no Ground over it, on a
    `ROAD_NATURAL_STEP` lattice, and Ground's open edges there as they now stand, triangulated
    with those edges as constraints, the faces over Ground or wholly ungoverned dropped. Returns
    the object (None when `dry`) and its report."""
    over = ground_from_above(box)
    grid = bpy.data.objects[GRID]
    gme = grid.data
    owner_names = json.loads(grid["kyt_owner_table"])
    owner = np.zeros(len(gme.vertices), dtype=np.int32)
    gme.attributes["owner"].data.foreach_get("value", owner)
    gtree = BVHTree.FromPolygons([grid.matrix_world @ v.co for v in gme.vertices], [tuple(q.vertices) for q in gme.polygons])
    # Ground's open edges in the box that bound ground one stands on: where Ground meets the
    # corridor. (A shore wall's skirt is open too, under its top; its faces are walls.)
    pts = []
    zs = []
    ws = []
    index = {}
    segs = []

    def point(x, y, z, w):
        key = (round(x, 4), round(y, 4))
        if key not in index:
            index[key] = len(pts)
            pts.append(Vector((x, y)))
            zs.append(z)
            ws.append(w)
        return index[key]

    for ob in ground_objects():
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        for e in bm.edges:
            if not e.is_boundary or e.link_faces[0].normal.z < MIN_UP_FACE:
                continue
            a, b = e.verts
            if not all(box[0] <= v.co.x <= box[1] and box[2] <= v.co.y <= box[3] for v in (a, b)):
                continue
            ends = []
            for v in (a, b):
                tw = design_at(now_t, pre_t, v.co.x, v.co.y)
                ends.append(point(v.co.x, v.co.y, v.co.z if tw is None else tw[0], 0.0 if tw is None else tw[1]))
            segs.append(tuple(ends))
        bm.free()
    edge_pts = list(pts)
    near = KDTree(len(edge_pts))
    for k, q in enumerate(edge_pts):
        near.insert((q.x, q.y, 0.0), k)
    near.balance()
    refused = {}
    x = math.floor(box[0] / ROAD_NATURAL_STEP) * ROAD_NATURAL_STEP
    while x <= box[1]:
        y = math.floor(box[2] / ROAD_NATURAL_STEP) * ROAD_NATURAL_STEP
        while y <= box[3]:
            if not over(x, y) and (not edge_pts or near.find((x, y, 0.0))[2] >= ROAD_NATURAL_CLEAR):
                tw = design_at(now_t, pre_t, x, y)
                if tw is not None:
                    hit = gtree.ray_cast(Vector((x, y, 5000.0)), Vector((0.0, 0.0, -1.0)))
                    names = {owner_names[owner[i]] for i in gme.polygons[hit[2]].vertices} if hit[0] is not None else set()
                    if not any(n.endswith(ROAD_NATURAL_OWNERS) for n in names):
                        refused[(x, y)] = sorted(names)
                    point(x, y, tw[0], tw[1])
                else:
                    z = height(now_t, x, y)
                    if z is not None:
                        point(x, y, z, 0.0)
            y += ROAD_NATURAL_STEP
        x += ROAD_NATURAL_STEP
    if refused:
        where, names = next(iter(refused.items()))
        raise SystemExit("edit %d reshapes %d points under no road corridor (e.g. (%.0f, %.0f), under %s); refusing" % (
            edit, len(refused), where[0], -where[1], names))
    out_v, _, out_f, orig_v, _, _ = delaunay_2d_cdt(pts, segs, [], 0, 1e-4, True)
    vz = []
    vw = []
    for k, q in enumerate(out_v):
        src = [i for i in orig_v[k] if i < len(pts)]
        if src:
            vz.append(zs[src[0]])
            vw.append(ws[src[0]])
        else:
            tw = design_at(now_t, pre_t, q.x, q.y)
            vz.append(height(now_t, q.x, q.y) if tw is None else tw[0])
            vw.append(0.0 if tw is None else tw[1])
    faces = []
    for f in out_f:
        if max(vw[i] for i in f) <= 0.0:
            continue
        cx = sum(out_v[i].x for i in f) / 3.0
        cy = sum(out_v[i].y for i in f) / 3.0
        if over(cx, cy):
            continue
        faces.append(tuple(f))
    used = sorted({i for f in faces for i in f})
    area = 0.0
    for f in faces:
        a, b, c = (out_v[i] for i in f)
        area += abs((b - a).cross(c - a)) * 0.5
    report = {"faces": len(faces), "points": len(used), "edge_points": len(edge_pts), "ha": round(area / 10000.0, 2),
              "governed": sum(1 for i in used if vw[i] >= 1.0)}
    if dry or not faces:
        return None, report
    remap = {i: n for n, i in enumerate(used)}
    name = ROAD_NATURAL[edit]
    me = bpy.data.meshes.new(name)
    me.from_pydata([(out_v[i].x, out_v[i].y, vz[i]) for i in used], [], [tuple(remap[i] for i in f) for f in faces])
    me.validate()
    for poly in me.polygons:
        if poly.normal.z < 0.0:
            poly.flip()
    weight = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            weight.data[li].uv = (vw[used[me.loops[li].vertex_index]], 0.0)
    ob = bpy.data.objects.new(name, me)
    ob["kyt_collision"] = "none"
    ob["kyt_note"] = ("not ground: the natural ground the road corridor's sides are cut to where Ground edit %d "
                      "reshapes what the corridor covers, on the edit's design, its u texture coordinate how far "
                      "the design governs (1 inside the edit, 0 where it leaves the ground as it was); "
                      "tools/blender/world_terrain_ground_edit.py, ROAD_NATURAL" % edit)
    c = bpy.data.collections.get(EARTHWORKS)
    if c is None:
        c = bpy.data.collections.new(EARTHWORKS)
        bpy.context.scene.collection.children.link(c)
    c.objects.link(ob)
    # Drawn as wire, so it never reads as ground in the master; hidden, it would not export.
    ob.display_type = 'WIRE'
    return ob, report


def lake_banks_design():
    """The banks' design (`LAKE_BANKS_ID`) on a `BANK_STEP` raster over `BANK_BOX`: BVH trees of the
    reserve as the banks leave it and as it stands, the box in Blender plan coordinates, the raster
    points the banks cut (for the refinement), and a report."""
    lakes = edit_constant("world_terrain_edit_hill_lakes.py", "LAKES")
    res = bpy.data.objects["terrain_world_mainland_reserve"]
    me = res.data
    mw = res.matrix_world
    rtree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    fa = np.zeros(len(me.polygons), dtype=np.int32)
    if "authored_edit" in me.attributes:
        me.attributes["authored_edit"].data.foreach_get("value", fa)
    lv, lp = [], []
    for ob in bpy.data.collections[LAKES_COLLECTION].all_objects:
        base = len(lv)
        lv.extend(ob.matrix_world @ v.co for v in ob.data.vertices)
        lp.extend([base + i for i in q.vertices] for q in ob.data.polygons)
    ltree = BVHTree.FromPolygons(lv, lp)
    x0, x1, z0, z1 = BANK_BOX
    s = BANK_STEP
    nx, nz = int((x1 - x0) / s) + 1, int((z1 - z0) / s) + 1
    z = np.full((nz, nx), np.nan)
    wet = np.zeros((nz, nx), bool)
    falls = np.zeros((nz, nx), bool)
    down = Vector((0.0, 0.0, -1.0))
    for j in range(nz):
        for i in range(nx):
            o = Vector((x0 + i * s, -(z0 + j * s), 5000.0))
            h = rtree.ray_cast(o, down, 10000.0)
            if h[0] is None:
                continue
            z[j, i] = h[0].z
            falls[j, i] = fa[h[2]] == 5
            w = ltree.ray_cast(o, down, 10000.0)
            wet[j, i] = w[0] is not None and w[0].z > h[0].z

    def grow(mask, r):
        n = int(math.ceil(r / s))
        out = mask.copy()
        jj, ii = np.nonzero(mask)
        for dj in range(-n, n + 1):
            for di in range(-n, n + 1):
                if dj * dj + di * di <= n * n:
                    out[np.clip(jj + dj, 0, nz - 1), np.clip(ii + di, 0, nx - 1)] = True
        return out

    seam = np.zeros((nz, nx), bool)
    for ob in ground_objects():
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        om = ob.matrix_world
        for e in bm.edges:
            if not e.is_boundary or e.link_faces[0].normal.z < MIN_UP_FACE:
                continue
            a, b = om @ e.verts[0].co, om @ e.verts[1].co
            for f in np.linspace(0.0, 1.0, max(2, int((a - b).xy.length / s) + 1)):
                i = int(round((a.x + (b.x - a.x) * f - x0) / s))
                j = int(round((-(a.y + (b.y - a.y) * f) - z0) / s))
                if 0 <= i < nx and 0 <= j < nz:
                    seam[j, i] = True
        bm.free()
    held = np.isnan(z) | wet | grow(falls, BANK_FALLS) | grow(seam, BANK_SEAM)
    held[:2, :] = held[-2:, :] = True
    held[:, :2] = held[:, -2:] = True
    xs = x0 + np.arange(nx) * s
    zs = z0 + np.arange(nz) * s
    xx, zz = np.meshgrid(xs, zs)
    brim = np.zeros((nz, nx))
    best = np.full((nz, nx), np.inf)
    for lk in lakes.values():
        d2 = (xx - lk["centre"][0]) ** 2 + (zz - lk["centre"][1]) ** 2
        brim = np.where(d2 < best, lk["brim"], brim)
        best = np.minimum(best, d2)
    shore = np.zeros_like(wet)
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1),
            (1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
    for dj, di in dirs[:8]:
        shore |= np.roll(np.roll(wet, dj, 0), di, 1)
    shore &= ~held
    big = 1e9
    cone = np.where(shore, brim + BANK_LIP, big)
    dist = np.where(shore, 0.0, big)
    for _ in range(int(BANK_REACH / s) * 3):
        prev = cone.copy()
        for dj, di in dirs:
            step = s * math.hypot(dj, di)
            cone = np.minimum(cone, np.where(held, big, np.roll(np.roll(cone, -dj, 0), -di, 1) + BANK_SLOPE * step))
            dist = np.minimum(dist, np.where(held, big, np.roll(np.roll(dist, -dj, 0), -di, 1) + step))
        if np.array_equal(cone, prev):
            break
    zz0 = np.nan_to_num(z, nan=-big)
    target = np.where(held | (dist > BANK_REACH), zz0, np.minimum(zz0, cone))
    # A wall whose foot stands part-way up the slope is under the bank from the water and stays:
    # one at L0's south-west (0.09 ha); limiting every slope within the reach instead would have cut
    # 9 ha more of natural hillside to clear it.
    # Smoothed (a Gaussian over the ground that is neither held nor a hole), never above where the
    # ground stood: the smoothing only ever rounds the bank and its crest.
    active = ~held & ~np.isnan(z)
    sig = BANK_SMOOTH / s
    r = int(math.ceil(3.0 * sig))
    kern = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)

    def blur(a):
        a = np.apply_along_axis(lambda v: np.convolve(v, kern, mode="same"), 0, a)
        return np.apply_along_axis(lambda v: np.convolve(v, kern, mode="same"), 1, a)

    wsum = blur(active.astype(float))
    smooth = np.where(wsum > 1e-6, blur(np.where(active, target, 0.0)) / np.maximum(wsum, 1e-6), target)
    reach = np.zeros_like(active)
    reach[np.nonzero(zz0 - target > 0.01)] = True
    for _ in range(r):
        reach |= np.roll(reach, 1, 0) | np.roll(reach, -1, 0) | np.roll(reach, 1, 1) | np.roll(reach, -1, 1)
    target = np.where(active & reach, np.minimum(zz0, smooth), target)
    target = np.maximum(target, np.minimum(zz0, brim + BANK_LIP))
    cut = np.where(np.isnan(z), 0.0, zz0 - target)

    def sheet(h):
        verts = [Vector((x0 + i * s, -(z0 + j * s), float(h[j, i]) if not np.isnan(z[j, i]) else -big))
                 for j in range(nz) for i in range(nx)]
        faces = []
        for j in range(nz - 1):
            for i in range(nx - 1):
                if not (np.isnan(z[j, i]) or np.isnan(z[j, i + 1]) or np.isnan(z[j + 1, i]) or np.isnan(z[j + 1, i + 1])):
                    a = j * nx + i
                    faces.append((a, a + 1, a + nx + 1, a + nx))
        return BVHTree.FromPolygons(verts, faces)

    points = [Vector((x0 + i * s, -(z0 + j * s))) for j, i in zip(*np.nonzero(cut > 0.5))]
    report = {"cut_ha": round(float((cut > 0.5).sum() * s * s / 1e4), 2), "deepest": round(float(cut.max()), 1),
              "volume_m3": int(cut.sum() * s * s)}
    for key, lk in lakes.items():
        near = ((xx - lk["centre"][0]) ** 2 + (zz - lk["centre"][1]) ** 2) <= (lk["R"] + BANK_REACH) ** 2
        c = np.where(near, cut, 0.0)
        report[key] = {"cut_ha": round(float((c > 0.5).sum() * s * s / 1e4), 2), "deepest": round(float(c.max()), 1)}
    box = (x0, x1, -z1, -z0)
    return sheet(np.where(np.isnan(z), 0.0, target)), sheet(np.where(np.isnan(z), 0.0, zz0)), box, points, report


DIRS16 = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1),
          (1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]


def shifted(a, dj, di, fill):
    """`a` read at (j + dj, i + di), `fill` past its edge (np.roll would wrap the far side in)."""
    out = np.full_like(a, fill)
    nz, nx = a.shape
    j0, j1 = max(0, -dj), nz - max(0, dj)
    i0, i1 = max(0, -di), nx - max(0, di)
    out[j0:j1, i0:i1] = a[j0 + dj:j1 + dj, i0 + di:i1 + di]
    return out


def spread(a, rate, step, rising):
    """The lowest of a + rate * distance (`rising`), or the highest of a - rate * distance, over the
    raster: a slope laid out from every cell, 16 directions."""
    big = 1e9 if rising else -1e9
    while True:
        prev = a
        for dj, di in DIRS16:
            d = rate * step * math.hypot(dj, di)
            a = np.minimum(a, shifted(a, dj, di, big) + d) if rising else np.maximum(a, shifted(a, dj, di, big) - d)
        if np.array_equal(a, prev):
            return a


def city_cut_design():
    """The city cut's design (`CITY_CUT_ID`) on a `CITY_STEP` raster in Godot x and z: the surface the
    foothills go down to, their top as it stands, the ground of every other body, the raster's origin,
    the city's objects as (name, world vertices) and a report. The city is read from its own source,
    linked for the read and let go."""
    path = os.path.normpath(os.path.join(HERE, "..", "..", "assets", "source", CITY_SOURCE))
    libs = set(bpy.data.libraries)
    with bpy.data.libraries.load(path, link=True) as (src, dst):
        dst.objects = list(src.objects)
    def world(ob):
        # A linked object no scene evaluates keeps an identity matrix_world: composed here.
        if ob.parent is None:
            return ob.matrix_basis
        if ob.parent_type != 'OBJECT':
            raise SystemExit("%s hangs from its parent by %s" % (ob.name, ob.parent_type))
        return world(ob.parent) @ ob.matrix_parent_inverse @ ob.matrix_basis

    city = []
    for ob in dst.objects:
        if ob is not None and ob.type == 'MESH':
            mw = world(ob)
            city.append((ob.name, [mw @ v.co for v in ob.data.vertices], [tuple(p.vertices) for p in ob.data.polygons]))
    for lib in set(bpy.data.libraries) - libs:
        bpy.data.libraries.remove(lib)
    if set(bpy.data.libraries) != libs:
        raise SystemExit("the city source is still linked")
    blocks = [c for c in city if c[0].startswith(("city_block_", "city_skyline_anchor_"))]
    roads = [c for c in city if c[0] in CITY_ROADS]
    if len(roads) != len(CITY_ROADS) or not blocks:
        raise SystemExit("%s lacks its blocks or roads %s" % (CITY_SOURCE, sorted(set(CITY_ROADS) - {r[0] for r in roads})))

    def tree(parts):
        vs, ps = [], []
        for _name, v, p in parts:
            base = len(vs)
            vs.extend(v)
            ps.extend(tuple(base + i for i in q) for q in p)
        return BVHTree.FromPolygons(vs, ps)

    shell = bpy.data.objects[CITY_SHELL]
    others = [o for o in ground_objects() if o.name != CITY_SHELL and o.get("kyt_collision") != "none"]
    s = CITY_STEP
    bx = [v.x for _n, vs, _p in blocks for v in vs]
    bz = [-v.y for _n, vs, _p in blocks for v in vs]
    x0 = math.floor((min(bx) - CITY_PAD) / s) * s
    z0 = math.floor((min(bz) - CITY_PAD) / s) * s
    nx = int(math.ceil((max(bx) + CITY_PAD - x0) / s)) + 1
    nz = int(math.ceil((max(bz) + CITY_PAD - z0) / s)) + 1
    st = tree([(shell.name, [v.co.copy() for v in shell.data.vertices], [tuple(p.vertices) for p in shell.data.polygons])])
    pen = bpy.data.objects[CITY_PENINSULA]
    pt = tree([(pen.name, [v.co.copy() for v in pen.data.vertices], [tuple(p.vertices) for p in pen.data.polygons])])
    ot = tree([(o.name, [o.matrix_world @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons]) for o in others])
    bt = tree(blocks)
    rt = tree(roads)
    top = np.full((nz, nx), np.nan)
    pen_top = np.full((nz, nx), np.nan)
    other = np.full((nz, nx), np.nan)
    road_y = np.full((nz, nx), np.nan)
    blk = np.zeros((nz, nx), bool)
    down = Vector((0.0, 0.0, -1.0))
    for j in range(nz):
        for i in range(nx):
            o = Vector((x0 + i * s, -(z0 + j * s), 5000.0))
            for t, a in ((st, top), (pt, pen_top), (ot, other), (rt, road_y)):
                h = t.ray_cast(o, down, 10000.0)
                if h[0] is not None:
                    a[j, i] = h[0].z
            blk[j, i] = bt.ray_cast(o, down, 10000.0)[0] is not None

    def grow(mask, r):
        n = int(math.ceil(r / s))
        out = mask.copy()
        jj, ii = np.nonzero(mask)
        for dj in range(-n, n + 1):
            for di in range(-n, n + 1):
                if dj * dj + di * di <= n * n:
                    out[np.clip(jj + dj, 0, nz - 1), np.clip(ii + di, 0, nx - 1)] = True
        return out

    # The city's extent: its blocks and towers grown, the streets between them filled in, and every
    # hole filled (the junction's pad and roads leave one wider than the streets).
    city_e = ~grow(~grow(grow(blk, CITY_MARGIN), CITY_CLOSE), CITY_CLOSE)
    outside = np.zeros((nz, nx), bool)
    outside[0, :] = outside[-1, :] = outside[:, 0] = outside[:, -1] = True
    outside &= ~city_e
    while True:
        more = outside.copy()
        for dj, di in DIRS16[:4]:
            more |= shifted(outside, dj, di, False)
        more &= ~city_e
        if np.array_equal(more, outside):
            break
        outside = more
    city_e = ~outside
    if not (~city_e[:2, :]).all() or not (~city_e[-2:, :]).all() or not (~city_e[:, :2]).all() or not (~city_e[:, -2:]).all():
        raise SystemExit("the city's extent reaches the raster's edge")
    has_pen = ~np.isnan(pen_top)
    # The floor follows the peninsula, `CITY_UNDER` under its top: 0 m over its flat middle, sloping
    # to -5.6 m at its shore, where the city's edge blocks already stand. Past the peninsula it carries
    # the nearest of that on, so the slope below rises from a floor without steps.
    base = np.where(has_pen, np.minimum(np.nan_to_num(pen_top), 0.0) - CITY_UNDER, np.nan)
    under = np.where(city_e & ~np.isnan(top), base, np.nan)

    def filled(a):
        # Every empty cell takes the mean of its filled neighbours, ring by ring outward.
        while np.isnan(a).any():
            acc = np.zeros((nz, nx))
            cnt = np.zeros((nz, nx))
            for dj, di in DIRS16[:8]:
                nb = shifted(a, dj, di, np.nan)
                ok = ~np.isnan(nb)
                acc += np.where(ok, nb, 0.0)
                cnt += ok
            a = np.where(np.isnan(a) & (cnt > 0), acc / np.maximum(cnt, 1), a)
        return a

    base = filled(base)
    # The extent's edge rounded: its signed distance, blurred; the slope is laid from that.
    big = 1e9
    d_out = spread(np.where(city_e, 0.0, big), 1.0, s, True)
    d_in = spread(np.where(city_e, big, 0.0), 1.0, s, True)
    sd = d_out - d_in
    sig = CITY_SMOOTH / s
    r = int(math.ceil(3.0 * sig))
    kern = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)
    kern /= kern.sum()
    sdp = np.pad(sd, r, mode="edge")
    sdp = np.apply_along_axis(lambda v: np.convolve(v, kern, mode="valid"), 0, sdp)
    sd_b = np.apply_along_axis(lambda v: np.convolve(v, kern, mode="valid"), 1, sdp)
    # The waterfront: the city's extent where the foothills never stood. The climb is measured from
    # it, rounded the same way.
    flat = city_e & np.isnan(top)
    f_out = spread(np.where(flat, 0.0, big), 1.0, s, True)
    f_in = spread(np.where(flat, big, 0.0), 1.0, s, True)
    fp = np.pad(f_out - f_in, r, mode="edge")
    fp = np.apply_along_axis(lambda v: np.convolve(v, kern, mode="valid"), 0, fp)
    fd = np.maximum(np.apply_along_axis(lambda v: np.convolve(v, kern, mode="valid"), 1, fp), 0.0)
    climb = CITY_GRADE * np.where(fd < CITY_TOE, fd * fd / (2.0 * CITY_TOE), fd - 0.5 * CITY_TOE)
    cone = base + climb + CITY_HILL * np.maximum(sd_b, 0.0)
    # The straight edge: everything north of the foothills' north side, the climb from it at most
    # `CITY_SLOPE` wherever the city's own is steeper (beyond the city, where the hills rise).
    edge_z = min(-v.co.y for v in shell.data.vertices)
    north = (z0 + np.arange(nz) * s)[:, None] < edge_z + 0.5 * s
    north = np.broadcast_to(north, (nz, nx)) & np.isnan(top)
    e_out = spread(np.where(north, 0.0, big), 1.0, s, True)
    e_in = spread(np.where(north, big, 0.0), 1.0, s, True)
    ep = np.pad(e_out - e_in, r, mode="edge")
    ep = np.apply_along_axis(lambda v: np.convolve(v, kern, mode="valid"), 0, ep)
    ed = np.maximum(np.apply_along_axis(lambda v: np.convolve(v, kern, mode="valid"), 1, ep), 0.0)
    cone = np.minimum(cone, base + CITY_SLOPE * np.where(ed < CITY_EDGE_TOE, ed * ed / (2.0 * CITY_EDGE_TOE), ed - 0.5 * CITY_EDGE_TOE))
    # Roads the foothills hold up keep ground just under them, falling away at the same slope.
    needs = ~np.isnan(road_y) & ~(has_pen & (np.nan_to_num(pen_top, nan=-big) >= road_y - CITY_ROAD_HELD))
    held = np.where(needs, road_y - CITY_ROAD_UNDER, -big)
    src = held.copy()
    n = int(math.ceil(CITY_ROAD_GROW / s))
    for dj in range(-n, n + 1):
        for di in range(-n, n + 1):
            if dj * dj + di * di <= n * n:
                src = np.maximum(src, shifted(held, dj, di, -big))
    floor = spread(src, CITY_SLOPE, s, False)
    design = np.maximum(cone, floor)
    # The surface the foothills go down to: the lower of the hill and the design, the crease where
    # they meet rounded by a polynomial smooth minimum over `CITY_CREST`, never above the hill. Past
    # that band it carries on `CITY_CREST` under the design, over the hill, so the cutter is one
    # continuous surface. Never under the ground a road keeps.
    hill = filled(top.copy())
    k = CITY_CREST
    gap = design - hill
    h = np.clip((k - np.abs(gap)) / k, 0.0, 1.0)
    surface = np.where(gap < k, np.minimum(hill, design) - h * h * k / 4.0, design - k)
    # A hair over the hill where a road keeps it: the cutter laid onto the shell exactly left it open.
    surface = np.maximum(surface, np.minimum(floor, hill + 0.05))
    has = ~np.isnan(top)
    cut = np.where(has, np.maximum(np.nan_to_num(top) - surface, 0.0), 0.0)
    after = np.where(has, np.minimum(np.nan_to_num(top), surface), np.nan)
    ground_before = np.fmax(top, other)
    ground_after = np.fmax(after, other)
    # The blocks and towers the foothills stood over, before and after.
    buried = {}
    xs = x0 + np.arange(nx) * s
    zs = z0 + np.arange(nz) * s
    for name, vs, _ps in blocks:
        lo_x, hi_x = min(v.x for v in vs), max(v.x for v in vs)
        lo_z, hi_z = min(-v.y for v in vs), max(-v.y for v in vs)
        base = min(v.z for v in vs)
        m = blk & (xs[None, :] >= lo_x) & (xs[None, :] <= hi_x) & (zs[:, None] >= lo_z) & (zs[:, None] <= hi_z)
        if not m.any():
            continue
        b0 = float(np.nanmax(np.where(m, ground_before, -big))) - base
        b1 = float(np.nanmax(np.where(m, ground_after, -big))) - base
        if b0 > 0.5:
            buried[name] = (round(b0, 1), round(b1, 1))
    # Anything of the city's that stood on the foothills and would be left standing over the cut.
    hover = {}
    for name, vs, _ps in city:
        lo = min(v.z for v in vs)
        for v in vs:
            if v.z > lo + 0.5:
                continue
            i = int(round((v.x - x0) / s))
            j = int(round((-v.y - z0) / s))
            if not (0 <= i < nx and 0 <= j < nz) or np.isnan(ground_before[j, i]) or np.isnan(ground_after[j, i]):
                continue
            if abs(ground_before[j, i] - v.z) <= 0.6 and v.z - ground_after[j, i] > 0.6:
                hover[name] = max(hover.get(name, 0.0), round(float(v.z - ground_after[j, i]), 1))
    report = {"cut_ha": round(float((cut > 0.5).sum() * s * s / 1e4), 2), "deepest": round(float(cut.max()), 1),
              "volume_m3": int(cut.sum() * s * s),
              "floor": [round(float(np.nanmin(under)), 2), round(float(np.nanmax(under)), 2)],
              "extent_off_peninsula_ha": round(float((city_e & ~has_pen & ~np.isnan(top)).sum() * s * s / 1e4), 2),
              "blocks_buried_before": len(buried), "blocks_buried_after": sum(1 for v in buried.values() if v[1] > 0.5),
              "left_standing_over_the_cut": hover}
    return {"design": surface, "top": top, "cut": cut, "origin": (x0, z0), "shape": (nz, nx), "report": report,
            "buried": buried}


def city_cut(edit, dry):
    """Cut the foothills down to the city cut's design (`city_cut_design`): an exact Boolean with a
    cutter whose underside is the design, so every face the cut does not reach stays as it was and the
    shell stays closed. The shell is kept whole in `HISTORY` for the undo."""
    d = city_cut_design()
    rep = d["report"]
    print("  city cut design: %s" % json.dumps(rep))
    design, top, cut = d["design"], d["top"], d["cut"]
    x0, z0 = d["origin"]
    nz, nx = d["shape"]
    s = CITY_STEP
    shell = bpy.data.objects[CITY_SHELL]
    if shell.matrix_world != shell.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin" % CITY_SHELL)
    # The cutter covers the cut and enough round it that the design stands well over the foothills
    # all along its edge, so its sides never reach them.
    jj, ii = np.nonzero(cut > 0.01)
    j0, j1, i0, i1 = jj.min() - 4, jj.max() + 4, ii.min() - 4, ii.max() + 4
    while True:
        j0, i0 = max(j0, 0), max(i0, 0)
        j1, i1 = min(j1, nz - 1), min(i1, nx - 1)
        ring = np.zeros((nz, nx), bool)
        ring[j0, i0:i1 + 1] = ring[j1, i0:i1 + 1] = ring[j0:j1 + 1, i0] = ring[j0:j1 + 1, i1] = True
        clear = np.isnan(top) | (design >= np.nan_to_num(top, nan=0.0) + 3.0)
        if clear[ring].all():
            break
        if j0 == 0 or i0 == 0 or j1 == nz - 1 or i1 == nx - 1:
            raise SystemExit("the design stands under the foothills at the raster's edge")
        j0, j1, i0, i1 = j0 - 8, j1 + 8, i0 - 8, i1 + 8
    cap = float(np.nanmax(top)) + 50.0
    report = {"faces_before": len(shell.data.polygons), "cutter_cells": int((j1 - j0) * (i1 - i0))}
    if dry:
        return {CITY_SHELL: report}, rep
    bm = bmesh.new()
    grid = {}
    for j in range(j0, j1 + 1):
        for i in range(i0, i1 + 1):
            grid[j, i] = bm.verts.new((x0 + i * s, -(z0 + j * s), min(float(design[j, i]), cap - 1.0)))
    for j in range(j0, j1):
        for i in range(i0, i1):
            a, b, c, e = grid[j, i], grid[j, i + 1], grid[j + 1, i + 1], grid[j + 1, i]
            bm.faces.new((a, b, c))
            bm.faces.new((a, c, e))
    # The outline round the box, its top at `cap`; the sides and one lid close the cutter.
    outline = ([grid[j0, i] for i in range(i0, i1 + 1)] + [grid[j, i1] for j in range(j0 + 1, j1 + 1)] +
               [grid[j1, i] for i in range(i1 - 1, i0 - 1, -1)] + [grid[j, i0] for j in range(j1 - 1, j0, -1)])
    lid = [bm.verts.new((v.co.x, v.co.y, cap)) for v in outline]
    for k in range(len(outline)):
        bm.faces.new((outline[k], outline[(k + 1) % len(outline)], lid[(k + 1) % len(outline)], lid[k]))
    bm.faces.new(lid)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if not all(e.is_manifold for e in bm.edges):
        raise SystemExit("the cutter is not closed")
    ctree = BVHTree.FromBMesh(bm)
    # Faces that lie in one plane (the city's floor, the slope off a straight run) become one.
    under = [f for f in bm.faces if f.normal.z < -0.05]
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.05), verts=list({v for f in under for v in f.verts}),
                             edges=list({e for f in under for e in f.edges}), delimit={'NORMAL'})
    cme = bpy.data.meshes.new("tmp_city_cutter")
    bm.to_mesh(cme)
    bm.free()
    fa = cme.attributes.new("authored_edit", 'INT', 'FACE')
    fa.data.foreach_set("value", np.full(len(cme.polygons), edit, dtype=np.int32))
    cme.polygons.foreach_set("material_index", np.zeros(len(cme.polygons), dtype=np.int32))
    cme.polygons.foreach_set("use_smooth", np.ones(len(cme.polygons), dtype=bool))
    cutter = bpy.data.objects.new("tmp_city_cutter", cme)
    bpy.context.scene.collection.objects.link(cutter)
    old = shell.data
    before = coords(shell).copy()
    mod = shell.modifiers.new("tmp_city_cut", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    mod.material_mode = 'INDEX'
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(shell.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    shell.modifiers.remove(mod)
    bpy.data.objects.remove(cutter)
    bpy.data.meshes.remove(cme)
    # The proof, before anything is kept: the shell closed; every corner the design stands over
    # where it was; every new corner on the design; no side of the cutter in it.
    bm = bmesh.new()
    bm.from_mesh(new)
    bad = [e for e in bm.edges if not e.is_manifold]
    if bad:
        raise SystemExit("the cut left %s open: %d edges, e.g. %s" % (CITY_SHELL, len(bad), [
            (tuple(round(c, 2) for c in e.verts[0].co), round(e.calc_length(), 4), len(e.link_faces)) for e in bad[:8]]))
    ob_bm = bmesh.new()
    ob_bm.from_mesh(old)
    vol0 = ob_bm.calc_volume(signed=True)
    ob_bm.free()
    vol1 = bm.calc_volume(signed=True)
    bm.free()
    now = coords_of(new)
    kept = {tuple(np.round(v, 4)) for v in now}

    def design_at_xy(x, y):
        # From below: the first face up is the cutter's underside, the design.
        h = ctree.ray_cast(Vector((x, y, -1000.0)), Vector((0.0, 0.0, 1.0)))
        return None if h[0] is None else h[0].z

    lost = 0
    for v in before:
        if tuple(np.round(v, 4)) in kept:
            continue
        t = design_at_xy(v[0], v[1])
        if t is None or v[2] < t - 0.01:
            lost += 1
    if lost:
        raise SystemExit("the cut moved %d corners of %s that the design stands over" % (lost, CITY_SHELL))
    old_set = {tuple(np.round(v, 4)) for v in before}
    off = 0
    for v in now:
        if tuple(np.round(v, 4)) in old_set:
            continue
        t = design_at_xy(v[0], v[1])
        if t is None:
            continue
        # A new corner is on the design, or where it meets one of the shell's own faces (its
        # sides at the straight edge, which stand from the bottom up).
        if v[2] > t + 0.01:
            off += 1
    if off:
        raise SystemExit("%d new corners of %s stand over the design" % (off, CITY_SHELL))
    nfa = np.zeros(len(new.polygons), dtype=np.int32)
    new.attributes["authored_edit"].data.foreach_get("value", nfa)
    # Needles the Boolean leaves along the cutter's grid lines (two corners a millimetre apart) have no
    # direction to speak of; they are counted, not refused.
    slivers = sum(1 for p in new.polygons if nfa[p.index] == edit and p.area < 0.01)
    walls = [p for p in new.polygons if nfa[p.index] == edit and p.normal.z < 0.05 and p.area >= 0.01]
    if walls:
        raise SystemExit("%d of the cutter's side or lid faces are in %s: %s" % (len(walls), CITY_SHELL, [
            (tuple(round(c, 2) for c in p.center), tuple(round(c, 3) for c in p.normal), round(p.area, 6), len(p.vertices),
             [tuple(round(c, 3) for c in new.vertices[i].co) for i in p.vertices]) for p in walls[:5]]))
    # Kept whole for the undo, as edit 1 keeps the shells it cuts.
    hob = bpy.data.objects.new("%s__before_edit%d" % (CITY_SHELL, edit), old)
    hob["kyt_whole"] = True
    hob["kyt_note"] = "%s as it stood before Ground edit %d (the city cut), for its --undo; never exported" % (CITY_SHELL, edit)
    history_collection().objects.link(hob)
    name = old.name
    old.name = hob.name
    shell.data = new
    new.name = name
    report.update({"faces_after": len(new.polygons), "new_faces": int((nfa == edit).sum()), "slivers": slivers,
                   "volume_cut_m3": int(vol0 - vol1)})
    return {CITY_SHELL: report}, rep


def city_readme(edit, name, report):
    return ("Ground edit %d (%s), %s: %s cut back under the city, loosely as San Francisco's hills: flat on the "
            "waterfront where the foothills never reached (%.1f m under the peninsula), climbing from it through the "
            "city at up to 1:%.0f (level at first, steepening over %.0f m), the hills past the city's extent (its "
            "blocks and towers from %s grown %.0f m, streets and holes filled) rising by 1:%.0f more, the foothills' "
            "straight north edge brought down on a 1:%.0f bank, the crease with the hill as it stood rounded over "
            "%.0f m; cut only, the ground under a road the foothills hold kept %.2f m under it, the off-ramp's trench "
            "left for a tunnel (%s); the shell kept whole in %s. The city's blocks are set on it by "
            "tools/blender/city_blocks_on_ground.py. Undo: tools/blender/world_terrain_ground_edit.py -- --edit "
            "city_cut --undo." % (edit, name, TODAY, CITY_SHELL, CITY_UNDER, 1.0 / CITY_GRADE, CITY_TOE, CITY_SOURCE,
                                  CITY_MARGIN, 1.0 / CITY_HILL, 1.0 / CITY_SLOPE, CITY_CREST, CITY_ROAD_UNDER,
                                  json.dumps(report), HISTORY))


def bluffs(edit, dry):
    """Lay the reserve's shore walls back to `BLUFF_ANGLE` (`BLUFFS_ID`): the land's edge held, each
    wall's foot moved out to sea and down under the coast shelf. Returns the report per object and the
    edit's own report."""
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    cut_z = sea - SHELF_UNDER
    ob = bpy.data.objects[BLUFF_OBJECT]
    me = ob.data
    if ob.matrix_world != ob.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin" % BLUFF_OBJECT)
    north = bpy.data.objects["terrain_world_coast_north"]
    nb = [north.matrix_world @ Vector(c) for c in north.bound_box]
    clear = (min(b.x for b in nb) - BLUFF_CLEAR, max(b.x for b in nb) + BLUFF_CLEAR,
             min(b.y for b in nb) - BLUFF_CLEAR, max(b.y for b in nb) + BLUFF_CLEAR)
    # What a foot may not come under: land, every upward face but the shelves'.
    up_v, up_f = [], []
    for o in ground_objects():
        if o.name in (SHELF, LANDFORM_SHELF):
            continue
        om = o.matrix_world
        for poly in o.data.polygons:
            if poly.normal.z < MIN_UP_FACE:
                continue
            base = len(up_v)
            up_v.extend(om @ o.data.vertices[i].co for i in poly.vertices)
            up_f.append(tuple(range(base, base + len(poly.vertices))))
    land = BVHTree.FromPolygons(up_v, up_f)
    shelf_t = BVHTree.FromPolygons([v.co.copy() for v in bpy.data.objects[SHELF].data.vertices],
                                   [tuple(q.vertices) for q in bpy.data.objects[SHELF].data.polygons])
    down = Vector((0.0, 0.0, -1.0))

    def under_land(q):
        h = land.ray_cast(Vector((q.x, q.y, 5000.0)), down)
        return h[0] is not None and h[0].z > cut_z + 0.01

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    # The panels: an open edge at the shelf's cut, the land's edge straight above each end.
    panels = []
    buried = 0
    for e in bm.edges:
        if not e.is_boundary:
            continue
        b0, b1 = e.verts
        if abs(b0.co.z - cut_z) > 0.02 or abs(b1.co.z - cut_z) > 0.02:
            continue
        mid = (b0.co + b1.co) * 0.5
        if clear[0] <= mid.x <= clear[1] and clear[2] <= mid.y <= clear[3]:
            continue
        tops = []
        for b in (b0, b1):
            above = [v for f in b.link_faces for v in f.verts if (v.co.xy - b.co.xy).length < 1e-3 and v.co.z > b.co.z + 0.01]
            tops.append(max(above, key=lambda v: v.co.z) if above else None)
        if None in tops:
            continue
        quad = {b0, b1, tops[0], tops[1]}
        fs = sorted({f for b in (b0, b1) for f in b.link_faces if set(f.verts) <= quad}, key=lambda f: f.index)
        if not fs:
            continue
        # The sea side is the side with no land: the walls are not all wound to face it (the north
        # coast's face the land).
        a2, b2 = tops[0].co.xy, tops[1].co.xy
        if (b2 - a2).length < 1e-6:
            continue
        d2 = (b2 - a2).normalized()
        out = Vector((d2.y, -d2.x))
        if under_land((a2 + b2) * 0.5 + out * 1.5):
            out = -out
            if under_land((a2 + b2) * 0.5 + out * 1.5):
                # Land on both sides: a wall another body buries (the south coast under the southern
                # landforms), facing no sea.
                buried += 1
                continue
        inward = fs[0].normal.xy.dot(out) < 0.0
        panels.append({"b": (b0, b1), "t": tuple(tops), "faces": fs, "out": out, "inward": inward})
    if not panels:
        raise SystemExit("%s has no cut shore wall" % BLUFF_OBJECT)
    feet = {}
    for n, p in enumerate(panels):
        for b, t in zip(p["b"], p["t"]):
            f = feet.setdefault(b.index, {"v": b, "top": t, "n": Vector((0.0, 0.0)), "panels": []})
            f["n"] += p["out"]
            f["panels"].append(n)
    run = math.tan(math.radians(BLUFF_ANGLE))
    for f in feet.values():
        f["n"] = f["n"].normalized() if f["n"].length > 1e-6 else Vector((0.0, 0.0))
        f["d"] = (f["top"].co.z - f["v"].co.z) / run


    def at(f):
        return f["v"].co.xy + f["n"] * f["d"]

    def crosses(a0, a1, b0, b1):
        def side(p, q, r):
            return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)
        return (side(a0, a1, b0) * side(a0, a1, b1) < 0.0) and (side(b0, b1, a0) * side(b0, b1, a1) < 0.0)

    # A foot at the end of a run where the wall meets buried ground is under land where it stands, and
    # one whose wall's side edge is open (a run's end against a wall left alone) would turn that edge
    # from a vertical hairline into an open face: both stay where they are.
    def open_side(f):
        e = next((e for e in f["v"].link_edges if e.other_vert(f["v"]) is f["top"]), None)
        return e is not None and e.is_boundary

    pinned = {k for k, f in feet.items() if under_land(f["v"].co.xy + f["n"] * 0.05) or open_side(f)}
    for k in pinned:
        feet[k]["d"] = 0.0
    reduced = set()
    for _ in range(30):
        bad = set()
        for k, f in feet.items():
            if k not in pinned and under_land(at(f)):
                bad.add(k)
        segs = []
        for p in panels:
            k0, k1 = p["b"][0].index, p["b"][1].index
            a0, a1 = at(feet[k0]), at(feet[k1])
            old = p["b"][1].co.xy - p["b"][0].co.xy
            if (a1 - a0).dot(old) < 0.25 * old.length_squared:
                bad |= {k0, k1}
            segs.append((k0, k1, a0, a1))
        # The new feet against each other, and against the walls' own top edges, by a coarse grid.
        cells = {}
        lines = [(s[0], s[1], s[2], s[3]) for s in segs] + [(p["b"][0].index, p["b"][1].index, p["t"][0].co.xy, p["t"][1].co.xy) for p in panels]
        for n, (k0, k1, a0, a1) in enumerate(lines):
            for cx in range(int(min(a0.x, a1.x) // 20), int(max(a0.x, a1.x) // 20) + 1):
                for cy in range(int(min(a0.y, a1.y) // 20), int(max(a0.y, a1.y) // 20) + 1):
                    cells.setdefault((cx, cy), []).append(n)
        for members in cells.values():
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    m, o2 = lines[members[i]], lines[members[j]]
                    if {m[0], m[1]} & {o2[0], o2[1]}:
                        continue
                    if members[i] >= len(segs) and members[j] >= len(segs):
                        continue
                    if crosses(m[2], m[3], o2[2], o2[3]):
                        bad |= {m[0], m[1]} if members[i] < len(segs) else set()
                        bad |= {o2[0], o2[1]} if members[j] < len(segs) else set()
        if not bad:
            break
        for k in bad - pinned:
            feet[k]["d"] *= 0.7
            reduced.add(k)
    else:
        raise SystemExit("%d wall feet still cross or come under land" % len(bad))

    no_shelf = 0
    new = {}
    for k, f in feet.items():
        q = at(f)
        h = shelf_t.ray_cast(Vector((q.x, q.y, 5000.0)), down)
        if h[0] is None:
            no_shelf += 1
            z = cut_z
        else:
            z = min(cut_z, h[0].z - BLUFF_UNDER)
        new[k] = (q.x, q.y, z)
    ds = np.array([f["d"] for f in feet.values()])
    heights = np.array([f["top"].co.z - sea for f in feet.values()])
    report = {"panels": len(panels), "feet": len(feet),
              "shore_m": round(sum((p["t"][0].co.xy - p["t"][1].co.xy).length for p in panels), 1),
              "wall_over_sea_m": [round(float(heights.min()), 1), round(float(np.median(heights)), 1), round(float(heights.max()), 1)],
              "foot_out_m": [round(float(np.median(ds)), 1), round(float(ds.max()), 1)],
              "feet_brought_in": len(reduced), "feet_kept_at_buried_ends": len(pinned), "feet_with_no_shelf": no_shelf,
              "walls_wound_to_the_land": sum(1 for p in panels if p["inward"]), "walls_buried_left": buried}
    faces = sorted({f.index for p in panels for f in p["faces"]})
    to_land = {f.index for p in panels if p["inward"] for f in p["faces"]}
    bm.free()
    if dry:
        return {BLUFF_OBJECT: {"wall_faces": len(faces)}}, report
    before = coords(ob).copy()
    corner = me.corner_normals
    old_normals = {str(fi): [list(corner[li].vector) for li in me.polygons[fi].loop_indices] for fi in faces}
    hme = bpy.data.meshes.new("%s__before_edit%d" % (BLUFF_OBJECT, edit))
    hob = bpy.data.objects.new(hme.name, hme)
    hob["kyt_vertices"] = json.dumps([[k] + [float(c) for c in me.vertices[k].co] for k in sorted(new)])
    hob["kyt_normals"] = json.dumps(old_normals)
    hob["kyt_note"] = ("the wall feet of %s that Ground edit %d (the bluffs) moved and the walls' corner normals, "
                       "for its --undo; never exported" % (BLUFF_OBJECT, edit))
    history_collection().objects.link(hob)
    normals = [Vector(n.vector) for n in corner]
    for k, co in new.items():
        me.vertices[k].co = co
    me.update()
    face_set = set(faces)
    # Each laid-back wall shaded flat along its own winding, as the shelf left the walls: the renderers
    # light a face seen from behind with its normal turned, so a wall wound to the land still lights
    # from the sea (turning its normal to the sea instead rendered it black).
    for poly in me.polygons:
        if poly.index in face_set:
            for li in poly.loop_indices:
                normals[li] = Vector(poly.normal)
    me.normals_split_custom_set(normals)
    now = coords(ob)
    moved = np.nonzero(np.any(np.abs(now - before) > 1e-6, axis=1))[0]
    if set(int(i) for i in moved) - set(new):
        raise SystemExit("%s: vertices other than the wall feet moved" % BLUFF_OBJECT)
    flipped = sum(1 for fi in faces if (-1.0 if fi in to_land else 1.0) * me.polygons[fi].normal.z < 0.0)
    if flipped:
        raise SystemExit("%d of the laid-back walls face down" % flipped)
    return {BLUFF_OBJECT: {"wall_faces": len(faces), "feet_moved": len(moved)}}, report


def bluffs_facing(edit, dry):
    """Turn the reserve's shore walls that face the land to face the sea (`BLUFFS_FACING_ID`): those
    `bluffs` laid back and those it left standing by coast north. Windings and the turned faces' normals
    only. Returns the report per object and the edit's own report."""
    ob = bpy.data.objects[BLUFF_OBJECT]
    me = ob.data
    if ob.matrix_world != ob.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin" % BLUFF_OBJECT)
    hist = bpy.data.objects.get("%s__before_edit%d" % (BLUFF_OBJECT, BLUFFS_ID))
    if hist is None:
        raise SystemExit("Ground carries no edit %d (the bluffs) to turn" % BLUFFS_ID)
    laid = {int(k) for k in json.loads(hist["kyt_normals"])}
    cut_z = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL")) - SHELF_UNDER
    # The top ground over a point: every Ground face, either way up, as one sees it from above.
    verts, polys = [], []
    for o in ground_objects():
        om = o.matrix_world
        base = len(verts)
        verts.extend(om @ v.co for v in o.data.vertices)
        polys.extend(tuple(base + i for i in p.vertices) for p in o.data.polygons)
    tree = BVHTree.FromPolygons(verts, polys)
    down = Vector((0.0, 0.0, -1.0))

    def inside(q):
        h = tree.ray_cast(Vector((q.x, q.y, 6000.0)), down)
        return h[0] is not None and h[0].z > q.z + 0.05

    def to_land(f):
        c = f.calc_center_median()
        front, back = inside(c + f.normal * FACING_PROBE), inside(c - f.normal * FACING_PROBE)
        return None if front == back else front

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    # The walls still standing, as `bluffs` found its panels: every corner a foot on an open edge at the
    # shelf's cut or the land's edge straight above one. Then any panel between a foot and that edge: one
    # at the end of a laid-back run, tilted by the foot it shares, was in neither.
    feet = {v for e in bm.edges if e.is_boundary for v in e.verts if v.co.z <= cut_z + 0.02}
    cut_feet = {v for v in feet if abs(v.co.z - cut_z) <= 0.02}
    columns = {(round(v.co.x, 3), round(v.co.y, 3)) for v in cut_feet}
    standing = {f.index for f in bm.faces if any(v in cut_feet for v in f.verts)
                and all(v in cut_feet or (round(v.co.x, 3), round(v.co.y, 3)) in columns for v in f.verts)}
    edge = {v for fi in laid | standing for v in bm.faces[fi].verts if v not in feet}
    standing |= {f.index for f in bm.faces if any(v in feet for v in f.verts)
                 and all(v in feet or v in edge for v in f.verts)} - laid
    walls = sorted(laid | standing)
    sides = {fi: to_land(bm.faces[fi]) for fi in walls}
    turn = [fi for fi in walls if sides[fi]]
    report = {"walls_laid_back": len(laid), "walls_left_by_it": len(standing - laid),
              "turned": len(turn), "turned_laid_back": sum(1 for fi in turn if fi in laid),
              "turned_ha": round(sum(bm.faces[fi].calc_area() for fi in turn) / 1e4, 2),
              "facing_the_sea": sum(1 for fi in walls if sides[fi] is False),
              "undecided": sum(1 for fi in walls if sides[fi] is None)}
    if dry:
        bm.free()
        return {BLUFF_OBJECT: {"wall_faces": len(walls)}}, report
    if not turn:
        bm.free()
        raise SystemExit("no shore wall of %s faces the land" % BLUFF_OBJECT)
    before = coords(ob).copy()
    kept = np.zeros(len(me.loops) * 3)
    me.corner_normals.foreach_get("vector", kept)
    kept = kept.reshape(-1, 3)
    old_normals = {str(fi): [[me.loops[li].vertex_index] + kept[li].tolist() for li in me.polygons[fi].loop_indices]
                   for fi in turn}
    bmesh.ops.reverse_faces(bm, faces=[bm.faces[fi] for fi in turn])
    bm.to_mesh(me)
    bm.free()
    me.update()
    # Every other corner keeps its normal; a turned wall is shaded flat along its new winding, as the
    # laid-back walls were along theirs.
    normals = kept.copy()
    for fi in turn:
        poly = me.polygons[fi]
        for li in poly.loop_indices:
            normals[li] = poly.normal[:]
    me.normals_split_custom_set([tuple(n) for n in normals])
    hme = bpy.data.meshes.new("%s__before_edit%d" % (BLUFF_OBJECT, edit))
    hob = bpy.data.objects.new(hme.name, hme)
    hob["kyt_reversed"] = json.dumps(turn)
    hob["kyt_normals"] = json.dumps(old_normals)
    hob["kyt_note"] = ("the faces of %s that Ground edit %d (the bluffs facing) turned and their corner normals, "
                       "for its --undo; never exported" % (BLUFF_OBJECT, edit))
    history_collection().objects.link(hob)
    if not np.array_equal(before, coords(ob)):
        raise SystemExit("%s: a vertex moved" % BLUFF_OBJECT)
    now = np.zeros(len(me.loops) * 3)
    me.corner_normals.foreach_get("vector", now)
    now = now.reshape(-1, 3)
    mask = np.ones(len(me.loops), dtype=bool)
    for fi in turn:
        mask[list(me.polygons[fi].loop_indices)] = False
    report["normal_drift_elsewhere"] = round(float(np.abs(now[mask] - kept[mask]).max()), 5)
    if report["normal_drift_elsewhere"] > 2e-3:
        raise SystemExit("%s: corner normals off the turned walls moved %.4f" % (BLUFF_OBJECT, report["normal_drift_elsewhere"]))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    still = sum(1 for fi in walls if to_land(bm.faces[fi]))
    bm.free()
    if still:
        raise SystemExit("%d shore walls of %s still face the land" % (still, BLUFF_OBJECT))
    return {BLUFF_OBJECT: {"wall_faces": len(walls), "faces_turned": len(turn)}}, report


def hillside_colours(edit, dry):
    """Edit 6's faces take their colours and texture coordinates again from the faces it replaced
    (`HILLSIDE_COLOURS_ID`), sampled as `carry` now samples. Returns the report per object and the
    edit's own report."""
    ob = bpy.data.objects[HILLSIDE_OBJECT]
    me = ob.data
    old = bpy.data.objects.get("%s__before_edit%d" % (HILLSIDE_OBJECT, HILLSIDE_EDIT))
    if old is None:
        raise SystemExit("Ground carries no edit %d to sample again" % HILLSIDE_EDIT)
    hme = old.data
    col, hcol = me.color_attributes.get("Col"), hme.color_attributes.get("Col")
    uv, huv = me.uv_layers.get("UVMap"), hme.uv_layers.get("UVMap")
    if None in (col, hcol, uv, huv) or col.domain != 'CORNER' or hcol.domain != 'CORNER':
        raise SystemExit("%s or its edit %d history has no corner colours and texture" % (HILLSIDE_OBJECT, HILLSIDE_EDIT))
    hco = [v.co.copy() for v in hme.vertices]
    if any(len(p.vertices) != 3 for p in hme.polygons):
        raise SystemExit("edit %d's history has faces other than triangles" % HILLSIDE_EDIT)
    # The replaced faces seen from above, those seen edge-on (walls) left to the faces beside them.
    seen = [p.index for p in hme.polygons if not edge_on([hco[i] for i in p.vertices])]
    flat = BVHTree.FromPolygons([Vector((v.x, v.y, 0.0)) for v in hco], [tuple(hme.polygons[i].vertices) for i in seen])
    hc = np.zeros(len(hme.loops) * 4)
    hcol.data.foreach_get("color", hc)
    hc = hc.reshape(-1, 4)
    hu = np.zeros(len(hme.loops) * 2)
    huv.data.foreach_get("uv", hu)
    hu = hu.reshape(-1, 2)
    fa = np.zeros(len(me.polygons), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", fa)
    c = np.zeros(len(me.loops) * 4, dtype=np.float32)
    col.data.foreach_get("color", c)
    c = c.reshape(-1, 4)
    u = np.zeros(len(me.loops) * 2, dtype=np.float32)
    uv.data.foreach_get("uv", u)
    u = u.reshape(-1, 2)
    down = Vector((0.0, 0.0, -1.0))
    loops, new_c, new_u = [], [], []
    nearest = 0
    for poly in me.polygons:
        if fa[poly.index] != HILLSIDE_EDIT:
            continue
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            hit = flat.ray_cast(Vector((p.x, p.y, 1.0)), down)
            if hit[0] is None:
                hit = flat.find_nearest(Vector((p.x, p.y, 0.0)))
                nearest += 1
            hp = hme.polygons[seen[hit[2]]]
            bary = clamped(plan_weights([hco[i] for i in hp.vertices], p))
            hl = list(hp.loop_indices)
            loops.append(li)
            new_c.append(sum(bary[k] * hc[hl[k]] for k in range(3)))
            new_u.append(sum(bary[k] * hu[hl[k]] for k in range(3)))
    if not loops:
        raise SystemExit("%s has no faces of edit %d" % (HILLSIDE_OBJECT, HILLSIDE_EDIT))
    loops = np.array(loops, dtype=np.int32)
    new_c = np.array(new_c, dtype=np.float32)
    new_u = np.array(new_u, dtype=np.float32)
    was = c[loops]
    report = {"corners": len(loops), "faces": int(np.count_nonzero(fa == HILLSIDE_EDIT)),
              "corners_out_of_range_before": int(np.count_nonzero((was[:, :3] < -0.01).any(1) | (was[:, :3] > 1.01).any(1))),
              "corners_out_of_range_after": int(np.count_nonzero((new_c[:, :3] < -0.01).any(1) | (new_c[:, :3] > 1.01).any(1))),
              "corners_recoloured": int(np.count_nonzero(np.abs(new_c - was).max(1) > 0.01)),
              "texture_moved_most": round(float(np.abs(new_u - u[loops]).max()), 2),
              "corners_by_nearest_face": nearest}
    if dry:
        return {HILLSIDE_OBJECT: {"corners": len(loops)}}, report
    hob = bpy.data.objects.new("%s__before_edit%d" % (HILLSIDE_OBJECT, edit), bpy.data.meshes.new("%s__before_edit%d" % (HILLSIDE_OBJECT, edit)))
    hob["kyt_loops"] = base64.b64encode(loops.tobytes()).decode()
    hob["kyt_colours"] = base64.b64encode(np.ascontiguousarray(was).tobytes()).decode()
    hob["kyt_uvs"] = base64.b64encode(np.ascontiguousarray(u[loops]).tobytes()).decode()
    hob["kyt_note"] = ("the corner colours and texture coordinates of %s's edit %d faces that Ground edit %d sampled "
                       "again, for its --undo; never exported" % (HILLSIDE_OBJECT, HILLSIDE_EDIT, edit))
    history_collection().objects.link(hob)
    c[loops] = new_c
    u[loops] = new_u
    col.data.foreach_set("color", c.ravel())
    uv.data.foreach_set("uv", u.ravel())
    me.update()
    if report["corners_out_of_range_after"]:
        raise SystemExit("%d corners of edit %d still out of range" % (report["corners_out_of_range_after"], HILLSIDE_EDIT))
    return {HILLSIDE_OBJECT: {"corners": len(loops)}}, report


def range_flanks_design():
    """The block hill's design (`RANGE_FLANKS_ID`) on an `RF_STEP` raster over `RF_BOX`, as the seams': BVH
    sheets of range north's top as the design leaves it and as it stands, a box round them in Blender plan
    coordinates, the raster points the design moves (for the refinement), and a report."""
    ob = bpy.data.objects[RF_OBJECT]
    if ob.matrix_world != ob.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin" % RF_OBJECT)
    me = ob.data
    tree = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices for p in me.polygons])
    x0, x1, z0, z1 = RF_BOX
    s = RF_STEP
    ov, op = [], []
    for o in ground_objects():
        if o.name == RF_OBJECT:
            continue
        w = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if max(c.x for c in w) < x0 or min(c.x for c in w) > x1 or max(-c.y for c in w) < z0 or min(-c.y for c in w) > z1:
            continue
        base = len(ov)
        ov.extend(o.matrix_world @ v.co for v in o.data.vertices)
        op.extend([base + i for i in p.vertices] for p in o.data.polygons)
    otree = BVHTree.FromPolygons(ov, op) if op else None
    road = bpy.data.objects[RF_ROAD]
    dg = bpy.context.evaluated_depsgraph_get()
    rme = road.evaluated_get(dg).to_mesh()
    kd = KDTree(len(rme.vertices))
    for k, v in enumerate(rme.vertices):
        w = road.matrix_world @ v.co
        kd.insert((w.x, w.y, 0.0), k)
    kd.balance()
    road.evaluated_get(dg).to_mesh_clear()
    grid = bpy.data.objects[GRID]
    owner_names = json.loads(grid["kyt_owner_table"])
    gown = np.zeros(len(grid.data.vertices), dtype=np.int32)
    grid.data.attributes["owner"].data.foreach_get("value", gown)
    held_at = [grid.matrix_world @ v.co for v in grid.data.vertices if owner_names[gown[v.index]].endswith(RF_ROAD_OWNERS)]
    kd_road = KDTree(len(held_at))
    for k, w in enumerate(held_at):
        kd_road.insert((w.x, w.y, 0.0), k)
    kd_road.balance()
    nx, nz = int(round((x1 - x0) / s)) + 1, int(round((z1 - z0) / s)) + 1
    h = np.full((nz, nx), np.nan)
    bot = np.full((nz, nx), np.nan)
    oth = np.full((nz, nx), np.nan)
    road_d = np.zeros((nz, nx))
    down, up = Vector((0.0, 0.0, -1.0)), Vector((0.0, 0.0, 1.0))
    for j in range(nz):
        for i in range(nx):
            x, y = x0 + i * s, -(z0 + j * s)
            hit = tree.ray_cast(Vector((x, y, 5000.0)), down)
            if hit[0] is not None:
                h[j, i] = hit[0].z
                hit = tree.ray_cast(Vector((x, y, -5000.0)), up)
                bot[j, i] = hit[0].z
            if otree is not None:
                hit = otree.ray_cast(Vector((x, y, 5000.0)), down)
                if hit[0] is not None:
                    oth[j, i] = hit[0].z
            road_d[j, i] = kd.find((x, y, 0.0))[2]
            if kd_road.find((x, y, 0.0))[2] <= RF_ROAD_GUARD:
                road_d[j, i] = 0.0
    sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
    # Range north's own land, where it is what one sees (its body buried under coast north and the
    # reserve stands higher than the ground there), and `RF_INSET` in from where it is not.
    land = np.isfinite(h) & (np.nan_to_num(h, nan=-1e9) > sea + 1.0) & ~(np.nan_to_num(oth, nan=-1e9) > np.nan_to_num(h, nan=0.0) + 0.5)
    inner = land.copy()
    for _ in range(RF_INSET):
        inner &= shifted(inner, 0, 1, False) & shifted(inner, 0, -1, False) & shifted(inner, 1, 0, False) & shifted(inner, -1, 0, False)
    zz = np.where(land, h, np.nan)
    jj, ii = np.mgrid[0:nz, 0:nx]
    X, Z = x0 + ii * s, z0 + jj * s
    sx0, sx1, sz0, sz1 = RF_SEED
    # Sheer, as the seams read it: a drop of more than `SEAM_SHEER` times the distance, its top and its foot.
    sheer = np.zeros((nz, nx), bool)
    for dj, di in DIRS16[:8]:
        nb = shifted(zz, dj, di, np.nan)
        top = np.isfinite(zz) & np.isfinite(nb) & ((zz - nb) / (s * math.hypot(dj, di)) > SEAM_SHEER)
        sheer |= top | shifted(top, -dj, -di, False)
    seeds = sheer & (X >= sx0) & (X <= sx1) & (Z >= sz0) & (Z <= sz1)
    reach = spread(np.where(seeds, 0.0, 1e9), 1.0, s, True)
    # Where range north's top meets its own sides, underside or buried caps (as `carry`'s `top_only` reads
    # them), those faces stay, so the ground there is held, `RF_JOIN_HOLD` round.
    bm = bmesh.new()
    bm.from_mesh(me)
    top = set()
    for f in bm.faces:
        c = f.calc_center_median()
        hit = tree.ray_cast(Vector((c.x, c.y, 5000.0)), down)
        if hit[0] is not None and abs(hit[0].z - c.z) < 0.01 and f.normal.z >= TOP_MIN_NZ:
            top.add(f.index)
    joins = np.zeros((nz, nx), bool)
    for v in bm.verts:
        ins = [f.index in top for f in v.link_faces]
        if any(ins) and not all(ins):
            i, j = int(round((v.co.x - x0) / s)), int(round((-v.co.y - z0) / s))
            if 0 <= i < nx and 0 <= j < nz:
                joins[j, i] = True
    bm.free()
    near_join = spread(np.where(joins, 0.0, 1e9), 1.0, s, True) <= RF_JOIN_HOLD
    may = inner & (road_d > RF_ROAD_CLEAR) & (reach <= RF_REACH) & (Z <= RF_SOUTH) & ~near_join
    ok = np.isfinite(zz)
    a = np.nan_to_num(zz, nan=0.0)
    za = a.copy()
    # Where the edit's edge crosses ground steeper than `RF_SLOPE` (the hill's south-west corner at
    # `RF_SOUTH`), the held side cannot always be met at the slope; the limit must settle three cells in.
    deep = may.copy()
    for _ in range(3):
        deep &= shifted(deep, 0, 1, False) & shifted(deep, 0, -1, False) & shifted(deep, 1, 0, False) & shifted(deep, -1, 0, False)

    def limit(a, k):
        # The seams' Jacobi steps, at half their share: on faces this steep a cell's eight corrections at a
        # quarter each overshoot and grow. An eighth of each pair's excess at each end (a quarter at a free
        # end whose partner is held), until none is steeper by a centimetre.
        for _ in range(20000):
            corr = np.zeros((nz, nx))
            worst, at = 0.0, None
            for dj, di in ((0, 1), (1, 0), (1, 1), (1, -1)):
                nb = shifted(np.where(ok, a, np.nan), dj, di, np.nan)
                nfree = shifted(may, dj, di, False)
                diff = a - nb
                ex = np.abs(diff) - k * s * math.hypot(dj, di)
                v = ok & ~np.isnan(nb) & (ex > 0.0) & (may | nfree)
                if not v.any():
                    continue
                k_ = np.nanargmax(np.where(v & deep & shifted(deep, dj, di, False), ex, -np.inf))
                if ex.flat[k_] > worst:
                    worst, at = float(ex.flat[k_]), (k_ // nx, k_ % nx, dj, di)
                amt = np.where(v, np.sign(diff) * ex, 0.0)
                share_a = np.where(may & nfree, 0.125, np.where(may, 0.25, 0.0))
                share_b = np.where(may & nfree, 0.125, np.where(nfree, 0.25, 0.0))
                # The high end takes `RF_CUT` of it, the low end the rest, scaled so neither exceeds the share.
                w_hi, w_lo = RF_CUT / max(RF_CUT, 1.0 - RF_CUT), (1.0 - RF_CUT) / max(RF_CUT, 1.0 - RF_CUT)
                corr -= amt * share_a * np.where(diff > 0, w_hi, w_lo)
                corr += shifted(amt * share_b * np.where(diff > 0, w_lo, w_hi), -dj, -di, 0.0)
            a = a + np.where(may, corr, 0.0)
            if worst < 0.01:
                return a, worst, at
        return a, worst, at

    def smoothed(a, passes):
        # What moved is smoothed, not the ground, as the seams do.
        zone = may & (spread(np.where(np.abs(a - za) > 0.01, 0.0, 1e9), 1.0, s, True) <= 3.0 * s)
        m = a - za
        for _ in range(passes):
            acc = np.zeros((nz, nx))
            cnt = np.zeros((nz, nx))
            for dj, di in DIRS16[:8]:
                nb = shifted(np.where(ok, m, np.nan), dj, di, np.nan)
                acc += np.nan_to_num(nb)
                cnt += ~np.isnan(nb)
            m = np.where(zone & (cnt > 0), m + 0.5 * (acc / np.maximum(cnt, 1) - m), m)
        return za + m

    for rnd in range(RF_ROUNDS):
        a, worst, at = limit(a, RF_SLOPE)
        if rnd < RF_ROUNDS - 1:
            a = smoothed(a, RF_PASSES)
    a, worst, at = limit(smoothed(a, RF_FINISH), RF_SLOPE)
    edge_d = spread(np.where(may, 1e9, 0.0), 1.0, s, True)
    a = za + (a - za) * np.clip((edge_d - s) / RF_TAPER, 0.0, 1.0)
    if worst > 0.05:
        j, i, dj, di = at
        raise SystemExit("the slope limit did not settle: %.2f m over it at (%.0f, %.0f) towards (%.0f, %.0f), free %s and %s, "
                         "%.1f and %.1f" % (worst, X[j, i], Z[j, i], X[j, i] + di * s, Z[j, i] + dj * s, may[j, i],
                                            may[min(j + dj, nz - 1), min(max(i + di, 0), nx - 1)], a[j, i],
                                            a[min(j + dj, nz - 1), min(max(i + di, 0), nx - 1)]))
    D = np.where(ok, a, np.nan)
    move = np.where(may, a - za, 0.0)
    ring = may & ~(shifted(may, 0, 1, False) & shifted(may, 0, -1, False) & shifted(may, 1, 0, False) & shifted(may, -1, 0, False))
    if np.abs(move[ring]).max() > 0.3:
        j, i = np.unravel_index(np.argmax(np.where(ring, np.abs(move), 0.0)), move.shape)
        raise SystemExit("the change reaches the edge of where it may move: %.2f m at (%.0f, %.0f)" % (move[j, i], X[j, i], Z[j, i]))

    def steepest(b):
        g = np.zeros((nz, nx))
        for dj, di in DIRS16[:8]:
            nb = shifted(b, dj, di, np.nan)
            g = np.fmax(g, np.abs(b - nb) / (s * math.hypot(dj, di)))
        return float(np.degrees(np.arctan(np.nanmax(np.where(may, g, np.nan)))))

    edge_over = 0.0
    for dj, di in ((0, 1), (1, 0), (1, 1), (1, -1)):
        nb = shifted(np.where(ok, a, np.nan), dj, di, np.nan)
        ex = np.abs(a - nb) - RF_SLOPE * s * math.hypot(dj, di)
        v = ok & ~np.isnan(nb) & (may | shifted(may, dj, di, False))
        if v.any():
            edge_over = max(edge_over, float(np.nanmax(np.where(v, ex, -np.inf))))
    report = {"seed_cells": int(seeds.sum()), "join_cells": int((near_join & inner).sum()), "edge_over_m": round(edge_over, 2), "may_ha": round(float(may.sum()) * s * s / 1e4, 1),
              "moved_ha": round(float((np.abs(move) > RF_EPS).sum()) * s * s / 1e4, 2),
              "cut_m": round(float(-move.min()), 1), "fill_m": round(float(move.max()), 1),
              "cut_m3": int(-move[move < 0].sum() * s * s), "fill_m3": int(move[move > 0].sum() * s * s),
              "ring_most_m": round(float(np.abs(move[ring]).max()), 3),
              "steepest_before_deg": round(steepest(zz), 1), "steepest_after_deg": round(steepest(D), 1),
              "crest_m": round(float(np.nanmax(np.where(may, zz, np.nan))), 1),
              "crest_after_m": round(float(np.nanmax(np.where(may, D, np.nan))), 1)}
    # Range north holds internal sheets (the slab under the road corridor, caps over its buried body): a
    # cut never goes down to one, or it would show.
    hits = 0
    for j, i in zip(*np.nonzero(may & (move < -MIN_CHANGE))):
        x, y = x0 + i * s, -(z0 + j * s)
        under = []
        for z in all_hits(tree, x, y):
            # A ray down an edge meets both its faces: one surface.
            if not under or under[-1] - z > 0.01:
                under.append(z)
        if len(under) > 2 and D[j, i] < under[1] + 0.5:
            hits += 1
    if hits:
        raise SystemExit("the cut goes down to an internal sheet of %s at %d cells" % (RF_OBJECT, hits))
    big = 1e9
    sheets = {}
    # Less than `RF_EPS` is left where it is: the smoothing's fringe would reach the vertices range north's
    # top shares with its buried caps.
    a = np.where(np.abs(move) > RF_EPS, a, za)
    for which, z in (("now", np.where(ok, a, np.nan)), ("pre", zz)):
        sheets[which] = BVHTree.FromPolygons(
            [Vector((x0 + i * s, -(z0 + j * s), float(z[j, i]) if ok[j, i] else -big)) for j in range(nz) for i in range(nx)],
            [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
             for j in range(nz - 1) for i in range(nx - 1) if ok[j, i] and ok[j, i + 1] and ok[j + 1, i] and ok[j + 1, i + 1]])
    points = [Vector((x0 + i * s, -(z0 + j * s))) for j, i in zip(*np.nonzero(np.abs(move) > 0.5))]
    box = (x0, x1, -z1, -z0)
    return sheets["now"], sheets["pre"], box, points, report


def north_coast_design():
    """Coast north's design (`NORTH_COAST_ID`) on an `NC_STEP` raster round `NC_ZONES`, as the seams': BVH
    sheets of its top as the design leaves it and as it stands, a box round them in Blender plan
    coordinates, the raster points the design moves, and a report."""
    ob = bpy.data.objects[NC_OBJECT]
    if ob.matrix_world != ob.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin" % NC_OBJECT)
    me = ob.data
    tree = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices for p in me.polygons])
    boxes = [b for b, _k in NC_ZONES.values()]
    x0 = min(b[0] for b in boxes) - NC_REACH / 2
    x1 = max(b[1] for b in boxes) + NC_REACH / 2
    z0 = min(b[2] for b in boxes) - NC_REACH / 2
    z1 = max(b[3] for b in boxes) + NC_REACH / 2
    s = NC_STEP
    ov, op = [], []
    for o in ground_objects():
        if o.name == NC_OBJECT:
            continue
        w = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if max(c.x for c in w) < x0 or min(c.x for c in w) > x1 or max(-c.y for c in w) < z0 or min(-c.y for c in w) > z1:
            continue
        base = len(ov)
        ov.extend(o.matrix_world @ v.co for v in o.data.vertices)
        op.extend([base + i for i in p.vertices] for p in o.data.polygons)
    otree = BVHTree.FromPolygons(ov, op) if op else None
    # Ground's open edges with ground on them: where it meets what the generator still builds (the road
    # corridor, the tunnels' lids), which never moves.
    seams = []
    for o in ground_objects():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        om = o.matrix_world
        for e in bm.edges:
            if e.is_boundary and e.link_faces[0].normal.z >= MIN_UP_FACE:
                a, b = om @ e.verts[0].co, om @ e.verts[1].co
                if x0 - NC_HOLD <= min(a.x, b.x) and max(a.x, b.x) <= x1 + NC_HOLD and z0 - NC_HOLD <= min(-a.y, -b.y) and max(-a.y, -b.y) <= z1 + NC_HOLD:
                    seams.append((a, b))
        bm.free()
    nx, nz = int(round((x1 - x0) / s)) + 1, int(round((z1 - z0) / s)) + 1
    h = np.full((nz, nx), np.nan)
    oth = np.full((nz, nx), np.nan)
    layers = np.zeros((nz, nx), dtype=np.int32)
    down = Vector((0.0, 0.0, -1.0))
    for j in range(nz):
        for i in range(nx):
            x, y = x0 + i * s, -(z0 + j * s)
            hit = tree.ray_cast(Vector((x, y, 5000.0)), down)
            if hit[0] is not None:
                h[j, i] = hit[0].z
                under = []
                for z in all_hits(tree, x, y):
                    if not under or under[-1] - z > 0.01:
                        under.append(z)
                layers[j, i] = len(under)
            if otree is not None:
                hit = otree.ray_cast(Vector((x, y, 5000.0)), down)
                if hit[0] is not None:
                    oth[j, i] = hit[0].z
    seam = np.zeros((nz, nx), bool)
    for a, b in seams:
        for f in np.linspace(0.0, 1.0, max(2, int((a - b).xy.length / s) + 1)):
            i = int(round((a.x + (b.x - a.x) * f - x0) / s))
            j = int(round((-(a.y + (b.y - a.y) * f) - z0) / s))
            if 0 <= i < nx and 0 <= j < nz:
                seam[j, i] = True
    top = np.isfinite(h) & ~(np.nan_to_num(oth, nan=-1e9) > np.nan_to_num(h, nan=0.0) + 0.01)
    # Where coast north's top meets a wall or skirt of its own (as `carry` reads them), those faces stay.
    bm = bmesh.new()
    bm.from_mesh(me)
    tops = set()
    for f in bm.faces:
        c = f.calc_center_median()
        hit = tree.ray_cast(Vector((c.x, c.y, 5000.0)), down)
        if hit[0] is not None and abs(hit[0].z - c.z) < 0.01 and f.normal.z >= NC_TOP_MIN_NZ:
            tops.add(f.index)
    # `carry` leaves out every top face with a corner there, so every corner of those is held.
    joined = set()
    for v in bm.verts:
        ins = [f.index in tops for f in v.link_faces]
        if any(ins) and not all(ins):
            joined.update(f for f in v.link_faces)
    joins = np.zeros((nz, nx), bool)
    for f in joined:
        for v in f.verts:
            i, j = int(round((v.co.x - x0) / s)), int(round((-v.co.y - z0) / s))
            if 0 <= i < nx and 0 <= j < nz:
                joins[j, i] = True
    bm.free()
    held = (spread(np.where(seam, 0.0, 1e9), 1.0, s, True) <= NC_HOLD) | (spread(np.where(joins, 0.0, 1e9), 1.0, s, True) <= NC_JOIN_HOLD)
    jj, ii = np.mgrid[0:nz, 0:nx]
    X, Z = x0 + ii * s, z0 + jj * s
    zz = np.where(top, h, np.nan)
    sheer = np.zeros((nz, nx), bool)
    for dj, di in DIRS16[:8]:
        nb = shifted(zz, dj, di, np.nan)
        t = np.isfinite(zz) & np.isfinite(nb) & ((zz - nb) / (s * math.hypot(dj, di)) > SEAM_SHEER)
        sheer |= t | shifted(t, -dj, -di, False)
    a = np.where(top, h, 1e9)
    free_all = np.zeros((nz, nx), bool)
    report = {}
    for key, ((bx0, bx1, bz0, bz1), k) in NC_ZONES.items():
        zone = (X >= bx0) & (X <= bx1) & (Z >= bz0) & (Z <= bz1)
        seeds = sheer & zone & ~held
        near = spread(np.where(seeds, 0.0, 1e9), 1.0, s, True) <= NC_REACH
        free = top & zone & near & ~held
        if key == "plug":
            free &= np.nan_to_num(h, nan=-1e9) > NC_SHORE
        # Cut only: each free cell no higher than any other ground of coast north's plus the slope.
        while True:
            prev = a
            for dj, di in DIRS16:
                a = np.where(free, np.minimum(a, shifted(a, dj, di, 1e9) + k * s * math.hypot(dj, di)), a)
            if np.array_equal(a, prev):
                break
        free_all |= free
        report[key] = {"seeds": int(seeds.sum()), "slope_deg": round(math.degrees(math.atan(k)), 1)}
    za = np.where(top, h, 0.0)
    a = np.where(free_all, a, za)
    # The crease where the cut meets the ground it leaves, rounded (a smooth minimum, as the city cut's).
    gap = za - a
    hk = np.clip(NC_CREST - gap, 0.0, None) / NC_CREST
    a = np.where(free_all & (gap > 0.0), np.minimum(za, a) - hk * hk * NC_CREST / 4.0, a)
    a = np.minimum(a, za)
    edge_d = spread(np.where(free_all, 1e9, 0.0), 1.0, s, True)
    a = za + (a - za) * np.clip((edge_d - s) / NC_TAPER, 0.0, 1.0)
    move = np.where(free_all, a - za, 0.0)
    a = np.where(np.abs(move) > RF_EPS, a, za)
    move = np.where(free_all, a - za, 0.0)
    cut = move < -RF_EPS
    if (cut & (layers > 1)).any():
        jx, ix = np.nonzero(cut & (layers > 1))
        raise SystemExit("coast north lies in more than one layer at %d cut cells, e.g. (%.0f, %.0f)" % (len(jx), X[jx[0], ix[0]], Z[jx[0], ix[0]]))
    bared = cut & (np.nan_to_num(oth, nan=-1e9) > a - 1.0)
    if bared.any():
        jx, ix = np.nonzero(bared)
        raise SystemExit("the cut comes within a metre of other ground at %d cells, e.g. (%.0f, %.0f)" % (len(jx), X[jx[0], ix[0]], Z[jx[0], ix[0]]))
    for key, ((bx0, bx1, bz0, bz1), k) in NC_ZONES.items():
        zone = (X >= bx0) & (X <= bx1) & (Z >= bz0) & (Z <= bz1)
        m = zone & cut
        report[key].update({"cut_ha": round(float(m.sum()) * s * s / 1e4, 2), "deepest_m": round(float(-move[zone].min()), 1),
                            "cut_m3": int(-move[m].sum() * s * s)})
    sheets = {}
    ok = np.isfinite(zz)
    for which, z in (("now", np.where(ok, a, np.nan)), ("pre", zz)):
        sheets[which] = BVHTree.FromPolygons(
            [Vector((x0 + i * s, -(z0 + j * s), float(z[j, i]) if ok[j, i] else -1e9)) for j in range(nz) for i in range(nx)],
            [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
             for j in range(nz - 1) for i in range(nx - 1) if ok[j, i] and ok[j, i + 1] and ok[j + 1, i] and ok[j + 1, i + 1]])
    points = [Vector((x0 + i * s, -(z0 + j * s))) for j, i in zip(*np.nonzero(np.abs(move) > 0.5))]
    return sheets["now"], sheets["pre"], (x0, x1, -z1, -z0), points, report


def range_east_design():
    """Range north's east nose (`RANGE_EAST_ID`) on an `RE_STEP` raster round `RE_ZONE`, as coast north's:
    BVH sheets of its top as the design leaves it and as it stands, a box round them in Blender plan
    coordinates, the raster points the design moves, and a report."""
    ob = bpy.data.objects[RE_OBJECT]
    if ob.matrix_world != ob.matrix_world.Identity(4):
        raise SystemExit("%s is not at the origin" % RE_OBJECT)
    me = ob.data
    tree = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices for p in me.polygons])
    bx0, bx1, bz0, bz1 = RE_ZONE
    x0, x1, z0, z1 = bx0 - RE_REACH / 2, bx1 + RE_REACH / 2, bz0 - RE_REACH / 2, bz1 + RE_REACH / 2
    s = RE_STEP
    ov, op = [], []
    for o in ground_objects():
        if o.name == RE_OBJECT:
            continue
        w = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if max(c.x for c in w) < x0 or min(c.x for c in w) > x1 or max(-c.y for c in w) < z0 or min(-c.y for c in w) > z1:
            continue
        base = len(ov)
        ov.extend(o.matrix_world @ v.co for v in o.data.vertices)
        op.extend([base + i for i in p.vertices] for p in o.data.polygons)
    otree = BVHTree.FromPolygons(ov, op) if op else None
    seams = []
    for o in ground_objects():
        bm = bmesh.new()
        bm.from_mesh(o.data)
        om = o.matrix_world
        for e in bm.edges:
            if e.is_boundary and e.link_faces[0].normal.z >= MIN_UP_FACE:
                a, b = om @ e.verts[0].co, om @ e.verts[1].co
                if x0 - RE_HOLD <= min(a.x, b.x) and max(a.x, b.x) <= x1 + RE_HOLD and z0 - RE_HOLD <= min(-a.y, -b.y) and max(-a.y, -b.y) <= z1 + RE_HOLD:
                    seams.append((a, b))
        bm.free()
    nx, nz = int(round((x1 - x0) / s)) + 1, int(round((z1 - z0) / s)) + 1
    h = np.full((nz, nx), np.nan)
    oth = np.full((nz, nx), np.nan)
    # The second surface of range north under its top: its underside, or an internal sheet.
    second = np.full((nz, nx), -1e9)
    layers = np.zeros((nz, nx), dtype=np.int32)
    down = Vector((0.0, 0.0, -1.0))
    for j in range(nz):
        for i in range(nx):
            x, y = x0 + i * s, -(z0 + j * s)
            hit = tree.ray_cast(Vector((x, y, 5000.0)), down)
            if hit[0] is not None:
                h[j, i] = hit[0].z
                under = []
                for z in all_hits(tree, x, y):
                    if not under or under[-1] - z > 0.01:
                        under.append(z)
                layers[j, i] = len(under)
                if len(under) > 1:
                    second[j, i] = under[1]
            if otree is not None:
                hit = otree.ray_cast(Vector((x, y, 5000.0)), down)
                if hit[0] is not None:
                    oth[j, i] = hit[0].z
    seam = np.zeros((nz, nx), bool)
    for a, b in seams:
        for f in np.linspace(0.0, 1.0, max(2, int((a - b).xy.length / s) + 1)):
            i = int(round((a.x + (b.x - a.x) * f - x0) / s))
            j = int(round((-(a.y + (b.y - a.y) * f) - z0) / s))
            if 0 <= i < nx and 0 <= j < nz:
                seam[j, i] = True
    top = np.isfinite(h) & ~(np.nan_to_num(oth, nan=-1e9) > np.nan_to_num(h, nan=0.0) + 0.01)
    # Where range north's top meets its own sides, at the nose's foot under the reserve, `carry` keeps the
    # corners the sides hang from; nothing round them is held.
    held = spread(np.where(seam, 0.0, 1e9), 1.0, s, True) <= RE_HOLD
    jj, ii = np.mgrid[0:nz, 0:nx]
    X, Z = x0 + ii * s, z0 + jj * s
    zz = np.where(top, h, np.nan)
    sheer = np.zeros((nz, nx), bool)
    for dj, di in DIRS16[:8]:
        nb = shifted(zz, dj, di, np.nan)
        t = np.isfinite(zz) & np.isfinite(nb) & ((zz - nb) / (s * math.hypot(dj, di)) > SEAM_SHEER)
        sheer |= t | shifted(t, -dj, -di, False)
    zone = (X >= bx0) & (X <= bx1) & (Z >= bz0) & (Z <= bz1)
    seeds = sheer & zone & ~held
    near = spread(np.where(seeds, 0.0, 1e9), 1.0, s, True) <= RE_REACH
    floor = np.nan_to_num(oth, nan=-1e9) + RE_SKIN
    free = top & zone & near & ~held & (np.nan_to_num(h, nan=-1e9) > floor)
    # Cut only: each free cell no higher than the ground beside it, whoever's, plus the slope.
    a = np.where(top, h, np.where(np.isfinite(oth), oth, 1e9))
    while True:
        prev = a
        for dj, di in DIRS16:
            a = np.where(free, np.minimum(a, shifted(a, dj, di, 1e9) + RE_SLOPE * s * math.hypot(dj, di)), a)
        if np.array_equal(a, prev):
            break
    za = np.where(top, h, 0.0)
    a = np.where(free, a, za)
    gap = za - a
    hk = np.clip(RE_CREST - gap, 0.0, None) / RE_CREST
    a = np.where(free & (gap > 0.0), np.minimum(za, a) - hk * hk * RE_CREST / 4.0, a)
    a = np.minimum(a, za)
    # Faded out towards the ground of its own it keeps; not at its foot, where it meets the reserve it was laid
    # out from.
    edge_d = spread(np.where(top & ~free & (np.nan_to_num(h, nan=-1e9) > floor), 0.0, 1e9), 1.0, s, True)
    a = za + (a - za) * np.clip((edge_d - s) / RE_TAPER, 0.0, 1.0)
    # Never down to the reserve under it.
    a = np.where(free, np.maximum(a, np.minimum(za, floor)), a)
    move = np.where(free, a - za, 0.0)
    a = np.where(np.abs(move) > RF_EPS, a, za)
    move = np.where(free, a - za, 0.0)
    cut = move < -RF_EPS
    sheet = cut & (layers > 2) & (a < second + 0.5)
    if sheet.any():
        jx, ix = np.nonzero(sheet)
        raise SystemExit("the cut goes down to an internal sheet of %s at %d cells, e.g. (%.0f, %.0f)" % (RE_OBJECT, len(jx), X[jx[0], ix[0]], Z[jx[0], ix[0]]))
    if (cut & (a < second + 0.5)).any():
        raise SystemExit("the cut goes through %s's underside" % RE_OBJECT)
    # Under the reserve beside the cut, range north's buried top falls on as steeply as the nose did, and the
    # faces from the cut down to it crossed the reserve's line in steep slivers; within `RE_UNDER` of the cut it
    # is brought up to `RE_SKIN` under the reserve, so they lie at the cut's slope. None of it shows.
    under = np.isfinite(h) & ~top & (spread(np.where(cut, 0.0, 1e9), 1.0, s, True) <= RE_UNDER)
    lift = np.where(under, np.nan_to_num(oth, nan=-1e9) - RE_SKIN - np.nan_to_num(h, nan=0.0), 0.0)
    lift = np.where(lift > RF_EPS, lift, 0.0)

    def steepest(b):
        g = np.zeros((nz, nx))
        for dj, di in DIRS16[:8]:
            nb = shifted(b, dj, di, np.nan)
            g = np.fmax(g, np.abs(b - nb) / (s * math.hypot(dj, di)))
        return round(float(np.degrees(np.arctan(np.nanmax(np.where(free, g, np.nan))))), 1)

    D = np.where(top, a, np.nan)
    report = {"seeds": int(seeds.sum()), "slope_deg": round(math.degrees(math.atan(RE_SLOPE)), 1),
              "cut_ha": round(float(cut.sum()) * s * s / 1e4, 2), "deepest_m": round(float(-move.min()), 1),
              "cut_m3": int(-move[cut].sum() * s * s), "skin_cells": int((free & (a <= floor + 1e-6)).sum()),
              "steepest_before_deg": steepest(zz), "steepest_after_deg": steepest(D),
              "crest_m": round(float(np.nanmax(np.where(free, zz, np.nan))), 1),
              "crest_after_m": round(float(np.nanmax(np.where(free, D, np.nan))), 1),
              "under_lifted_cells": int((lift > 0).sum()), "under_lifted_most_m": round(float(lift.max()), 1)}
    sheets = {}
    ok = top | under
    pre = np.where(ok, h, np.nan)
    for which, z in (("now", np.where(top, a, np.where(under, h + lift, np.nan))), ("pre", pre)):
        sheets[which] = BVHTree.FromPolygons(
            [Vector((x0 + i * s, -(z0 + j * s), float(z[j, i]) if ok[j, i] else -1e9)) for j in range(nz) for i in range(nx)],
            [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
             for j in range(nz - 1) for i in range(nx - 1) if ok[j, i] and ok[j, i + 1] and ok[j + 1, i] and ok[j + 1, i + 1]])
    points = [Vector((x0 + i * s, -(z0 + j * s))) for j, i in zip(*np.nonzero((np.abs(move) > 0.5) | (lift > 0.5)))]
    return sheets["now"], sheets["pre"], (x0, x1, -z1, -z0), points, report


def range_flanks_bands(edit):
    """The faces the edit made on range north take the range's level bands from their height, as edit 1's
    sheet's do, where they came from a band or the forest above them."""
    me = bpy.data.objects[RF_OBJECT].data
    names = [m.name for m in me.materials]
    bands = {names.index(n) for _, n in TOE_BANDS}
    fa = np.zeros(len(me.polygons), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", fa)
    mi = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", mi)
    changed = 0
    for p in me.polygons:
        if fa[p.index] == edit and mi[p.index] in bands:
            m = names.index(range_band(p.center.z))
            if m != mi[p.index]:
                mi[p.index] = m
                changed += 1
    me.polygons.foreach_set("material_index", mi)
    return changed


def coords_of(me):
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def seams_design():
    """The seams' design (`SEAMS_ID`) on a `SEAM_STEP` raster round each of `SEAM_SITES`: BVH trees of the
    reserve as the blend leaves it and as it stands, a box round them all in Blender plan coordinates,
    the raster points the blend moves (for the refinement), and a report."""
    res = bpy.data.objects["terrain_world_mainland_reserve"]
    me = res.data
    mw = res.matrix_world
    rtree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    others = [o for o in ground_objects() if o is not res and o.get("kyt_collision") != "none"]
    ov, op = [], []
    for o in others:
        base = len(ov)
        ov.extend(o.matrix_world @ v.co for v in o.data.vertices)
        op.extend(tuple(base + i for i in q.vertices) for q in o.data.polygons)
    otree = BVHTree.FromPolygons(ov, op)
    lv, lp = [], []
    for ob in bpy.data.collections[LAKES_COLLECTION].all_objects:
        base = len(lv)
        lv.extend(ob.matrix_world @ v.co for v in ob.data.vertices)
        lp.extend([base + i for i in q.vertices] for q in ob.data.polygons)
    ltree = BVHTree.FromPolygons(lv, lp)
    open_edges = []
    for ob in ground_objects():
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        om = ob.matrix_world
        for e in bm.edges:
            if e.is_boundary and e.link_faces[0].normal.z >= MIN_UP_FACE:
                open_edges.append((om @ e.verts[0].co, om @ e.verts[1].co))
        bm.free()
    s = SEAM_STEP
    down = Vector((0.0, 0.0, -1.0))
    sheets_now, sheets_pre, points = ([], []), ([], []), []
    report = {}
    xs_all, zs_all = [], []
    for key, (x0, x1, z0, z1) in SEAM_SITES.items():
        nx, nz = int((x1 - x0) / s) + 1, int((z1 - z0) / s) + 1
        z = np.full((nz, nx), np.nan)
        held = np.zeros((nz, nx), bool)
        for j in range(nz):
            for i in range(nx):
                o = Vector((x0 + i * s, -(z0 + j * s), 5000.0))
                h = rtree.ray_cast(o, down, 10000.0)
                if h[0] is None:
                    continue
                z[j, i] = h[0].z
                g = otree.ray_cast(o, down, 10000.0)
                w = ltree.ray_cast(o, down, 10000.0)
                held[j, i] = (g[0] is not None and g[0].z > h[0].z - 0.01) or (w[0] is not None and w[0].z > h[0].z)
        seam = np.zeros((nz, nx), bool)
        for a, b in open_edges:
            if max(a.x, b.x) < x0 - SEAM_HOLD or min(a.x, b.x) > x1 + SEAM_HOLD:
                continue
            for f in np.linspace(0.0, 1.0, max(2, int((a - b).xy.length / s) + 1)):
                i = int(round((a.x + (b.x - a.x) * f - x0) / s))
                j = int(round((-(a.y + (b.y - a.y) * f) - z0) / s))
                if 0 <= i < nx and 0 <= j < nz:
                    seam[j, i] = True
        big = 1e9
        hold = np.isnan(z) | held | (spread(np.where(seam, 0.0, big), 1.0, s, True) <= SEAM_HOLD)
        zz = np.nan_to_num(z, nan=0.0)
        # Sheer: a drop of more than `SEAM_SHEER` times the distance to a neighbour, both its top and its foot.
        sheer = np.zeros((nz, nx), bool)
        for dj, di in DIRS16[:8]:
            nb = shifted(zz, dj, di, np.nan)
            drop = (zz - nb) / (s * math.hypot(dj, di))
            top = ~np.isnan(nb) & (drop > SEAM_SHEER)
            sheer |= top | shifted(top, -dj, -di, False)
        sheer &= ~hold
        dist = spread(np.where(sheer, 0.0, big), 1.0, s, True)
        ok = ~np.isnan(z)
        free = (dist <= SEAM_REACH) & ~hold
        a = zz.copy()

        def limit(a, k):
            # Jacobi steps: every too-steep pair corrected by a quarter of its excess at each end (all of
            # it at a free end whose partner is held), until none is steeper by a centimetre.
            for _ in range(4000):
                corr = np.zeros((nz, nx))
                worst = 0.0
                for dj, di in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    nb = shifted(a, dj, di, np.nan)
                    nfree = shifted(free, dj, di, False)
                    diff = a - nb
                    ex = np.abs(diff) - k * s * math.hypot(dj, di)
                    v = ~np.isnan(nb) & (ex > 0.0) & (free | nfree)
                    if not v.any():
                        continue
                    worst = max(worst, float(ex[v].max()))
                    amt = np.where(v, np.sign(diff) * ex, 0.0)
                    share_a = np.where(free & nfree, 0.25, np.where(free, 0.5, 0.0))
                    share_b = np.where(free & nfree, 0.25, np.where(nfree, 0.5, 0.0))
                    corr -= amt * share_a
                    corr += shifted(amt * share_b, -dj, -di, 0.0)
                a = a + np.where(free, corr, 0.0)
                if worst < 0.01:
                    break
            return a

        def smoothed(a, passes):
            # What moved is smoothed, not the ground (smoothing the ground took site 4's summit ridge
            # down 50 m).
            zone = free & (spread(np.where(np.abs(a - zz) > 0.01, 0.0, big), 1.0, s, True) <= 3.0 * s)
            m = a - zz
            for _ in range(passes):
                acc = np.zeros((nz, nx))
                cnt = np.zeros((nz, nx))
                for dj, di in DIRS16[:8]:
                    nb = shifted(np.where(ok, m, np.nan), dj, di, np.nan)
                    acc += np.nan_to_num(nb)
                    cnt += ~np.isnan(nb)
                m = np.where(zone & (cnt > 0), m + 0.5 * (acc / np.maximum(cnt, 1) - m), m)
            return zz + m

        for rnd in range(SEAM_ROUNDS):
            a = limit(a, SEAM_SLOPE)
            if rnd < SEAM_ROUNDS - 1:
                a = smoothed(a, SEAM_PASSES)
        # The hard limit leaves facets at exactly the slope, fluted along the raster's directions: a last
        # few passes take them off, and a last limit just under `SEAM_SHEER` clips only what that steepened.
        a = limit(smoothed(a, SEAM_FINISH), SEAM_FINISH_SLOPE)
        target = np.where(ok, a, np.nan)
        move = np.where(ok, target - zz, 0.0)
        band = free

        def steepest(a):
            out = np.zeros((nz, nx))
            for dj, di in DIRS16[:8]:
                nb = shifted(a, dj, di, np.nan)
                out = np.fmax(out, (a - nb) / (s * math.hypot(dj, di)))
            return out

        before, after = steepest(zz), steepest(np.nan_to_num(target))
        report[key] = {"sheer_cells": int(sheer.sum()), "moved_ha": round(float((np.abs(move) > 0.5).sum() * s * s / 1e4), 2),
                       "cut_m": round(float(-move.min()), 1), "fill_m": round(float(move.max()), 1),
                       "cut_m3": int(-move[move < 0].sum() * s * s), "fill_m3": int(move[move > 0].sum() * s * s),
                       "steepest_before": round(float(np.where(band, before, 0).max()), 2),
                       "steepest_after": round(float(np.where(band, after, 0).max()), 2),
                       "sheer_after": int((np.where(band & ~hold, after, 0) > SEAM_SHEER).sum())}
        for which, h, sheets in (("now", target, sheets_now), ("pre", z, sheets_pre)):
            base = len(sheets[0])
            sheets[0].extend(Vector((x0 + i * s, -(z0 + j * s), float(h[j, i]) if ok[j, i] else -big))
                             for j in range(nz) for i in range(nx))
            sheets[1].extend((base + j * nx + i, base + j * nx + i + 1, base + (j + 1) * nx + i + 1, base + (j + 1) * nx + i)
                             for j in range(nz - 1) for i in range(nx - 1)
                             if ok[j, i] and ok[j, i + 1] and ok[j + 1, i] and ok[j + 1, i + 1])
        points.extend(Vector((x0 + i * s, -(z0 + j * s))) for j, i in zip(*np.nonzero(np.abs(move) > 0.5)))
        xs_all += [x0, x1]
        zs_all += [z0, z1]
    box = (min(xs_all), max(xs_all), -max(zs_all), -min(zs_all))
    return (BVHTree.FromPolygons(*sheets_now), BVHTree.FromPolygons(*sheets_pre), box, points, report)


def ground_triangles():
    tris = []
    for ob in ground_objects():
        M = ob.matrix_world
        me = ob.data
        me.calc_loop_triangles()
        co = [M @ v.co for v in me.vertices]
        for lt in me.loop_triangles:
            a, b, c = (co[k] for k in lt.vertices)
            tris.append((a, b, c))
    return tris


def clip_below(tri, level):
    """The part of a triangle at or below `level`, as a polygon on that level."""
    out = []
    pts = list(tri)
    for k in range(3):
        p, q = pts[k], pts[(k + 1) % 3]
        if p.z <= level:
            out.append(Vector((p.x, p.y, level)))
        if (p.z - level) * (q.z - level) < 0.0:
            s = (level - p.z) / (q.z - p.z)
            out.append(Vector((p.x + (q.x - p.x) * s, p.y + (q.y - p.y) * s, level)))
    return out


def lake_water(key, lk, tris, top):
    """Ground triangles of one lake below its brim, flooded from its floor, and only
    where the game's top ground (the edited grid, `top`) is low enough for water too."""
    brim = float(lk["brim"])
    cx, cz = lk["centre"]
    sx, sz = lk["spill"]
    reach = float(lk["R"]) + 120.0
    centre = Vector((cx, -cz))
    spill = Vector((sx, -sz))
    creek = [Vector((x, -z)) for x, z in lk["creek"]]
    spill_r = (spill - centre).length

    def dry(c2):
        if (c2 - spill).length < SPILL_WALL and (c2 - centre).length > spill_r - 5.0:
            return True
        if any((c2 - q).length < CREEK_WALL for q in creek):
            return True
        t = height(top, c2.x, c2.y)
        return t is None or t > brim + TOP_RIM

    near = []
    for t in tris:
        c2 = Vector(((t[0].x + t[1].x + t[2].x) / 3.0, (t[0].y + t[1].y + t[2].y) / 3.0))
        if (c2 - centre).length < reach and min(v.z for v in t) < brim and not dry(c2):
            near.append(t)
    key_of = lambda v: (round(v.x, 2), round(v.y, 2))
    edges = {}
    for n, t in enumerate(near):
        for k in range(3):
            e = tuple(sorted((key_of(t[k]), key_of(t[(k + 1) % 3]))))
            edges.setdefault(e, []).append(n)
    # Start in the triangle nearest the lake's centre: anything else below the brim within
    # reach (the lowland west of K1) lies beyond the rim and is never reached.
    start = min(range(len(near)), key=lambda n: (Vector(((near[n][0].x + near[n][1].x + near[n][2].x) / 3.0,
                                                          (near[n][0].y + near[n][1].y + near[n][2].y) / 3.0)) - centre).length)
    wet = {start}
    todo = [start]
    while todo:
        n = todo.pop()
        t = near[n]
        for k in range(3):
            e = tuple(sorted((key_of(t[k]), key_of(t[(k + 1) % 3]))))
            # Water crosses an edge only where some of the edge is below the brim.
            if min(t[k].z, t[(k + 1) % 3].z) >= brim:
                continue
            for m in edges[e]:
                if m not in wet:
                    wet.add(m)
                    todo.append(m)
    polys = [clip_below(near[n], brim) for n in sorted(wet)]
    polys = [p for p in polys if len(p) >= 3]
    area = sum(0.5 * abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[(i + 1) % len(p)].x * p[i].y for i in range(len(p)))) for p in polys)
    xs = [v.x for p in polys for v in p]
    zs = [-v.y for p in polys for v in p]
    return polys, area, (min(xs), max(xs), min(zs), max(zs))


def pool_water(design, tris):
    """Ground triangles below a design plane's level, inside its outline grown by
    `POOL_GROW`, clipped at the level."""
    me = design.data
    M = design.matrix_world
    verts = [M @ v.co for v in me.vertices]
    level = sum(v.z for v in verts) / len(verts)
    flat = BVHTree.FromPolygons([Vector((v.x, v.y, 0.0)) for v in verts], [tuple(p.vertices) for p in me.polygons])
    polys = []
    for t in tris:
        if min(v.z for v in t) >= level:
            continue
        c = Vector(((t[0].x + t[1].x + t[2].x) / 3.0, (t[0].y + t[1].y + t[2].y) / 3.0, 0.0))
        hit = flat.find_nearest(c, POOL_GROW)
        if hit[0] is None:
            continue
        p = clip_below(t, level)
        if len(p) >= 3:
            polys.append(p)
    area = sum(0.5 * abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[(i + 1) % len(p)].x * p[i].y for i in range(len(p)))) for p in polys)
    return polys, area, level


def build_plane(name, polys, note):
    verts = []
    faces = []
    index = {}
    for p in polys:
        f = []
        for v in p:
            k = (round(v.x, 4), round(v.y, 4))
            if k not in index:
                index[k] = len(verts)
                verts.append((v.x, v.y, v.z))
            f.append(index[k])
        if len(set(f)) >= 3:
            faces.append(f)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    for poly in me.polygons:
        if poly.normal.z < 0:
            poly.flip()
    # The water is flat, so only its outline needs vertices: the clipped triangles of the
    # refined ground (tens of thousands) are merged into a few faces.
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.001, verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    mat = bpy.data.materials.get("lake_water") or bpy.data.materials.new("lake_water")
    mat.diffuse_color = LAKE_COLOUR
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob["kyt_collision"] = "none"
    ob["kyt_note"] = note
    return ob


def lakes_collection():
    c = bpy.data.collections.get(LAKES_COLLECTION)
    if c is None:
        c = bpy.data.collections.new(LAKES_COLLECTION)
        bpy.context.scene.collection.children.link(c)
    return c


def edit_face_vertices(ob, edit):
    me = ob.data
    if "authored_edit" not in me.attributes:
        return set()
    fa = np.zeros(len(me.polygons), dtype=np.int32)
    me.attributes["authored_edit"].data.foreach_get("value", fa)
    used = set()
    for p in me.polygons:
        if fa[p.index] == edit:
            used.update(p.vertices)
    return used


def log(entry=None, remove=None):
    scene = bpy.context.scene
    edits = json.loads(scene.get("kyt_ground_edits", "[]"))
    if remove is not None:
        edits = [e for e in edits if e.get("id") != remove]
    if entry is not None:
        edits = [e for e in edits if e.get("id") != entry["id"]] + [entry]
    scene["kyt_ground_edits"] = json.dumps(edits)
    return edits


def readme(line):
    t = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    t.write("\n" + line + "\n")


def undo(edit):
    edits = json.loads(bpy.context.scene.get("kyt_ground_edits", "[]"))
    entry = next((e for e in edits if e.get("id") == edit), None)
    if entry is None:
        raise SystemExit("Ground carries no edit %d" % edit)
    if edits[-1].get("id") != edit:
        raise SystemExit("edit %d was carried after edit %d; undo it first" % (edits[-1]["id"], edit))
    for name in entry["objects"]:
        ob = bpy.data.objects[name]
        hob = bpy.data.objects["%s__before_edit%d" % (name, edit)]
        if hob.get("kyt_colours"):
            # Only colours sampled again (the hillside's): each corner takes back what it had.
            me = ob.data
            li = np.frombuffer(base64.b64decode(hob["kyt_loops"]), dtype=np.int32)
            c = np.zeros(len(me.loops) * 4, dtype=np.float32)
            me.color_attributes["Col"].data.foreach_get("color", c)
            c = c.reshape(-1, 4)
            c[li] = np.frombuffer(base64.b64decode(hob["kyt_colours"]), dtype=np.float32).reshape(-1, 4)
            me.color_attributes["Col"].data.foreach_set("color", c.ravel())
            u = np.zeros(len(me.loops) * 2, dtype=np.float32)
            me.uv_layers["UVMap"].data.foreach_get("uv", u)
            u = u.reshape(-1, 2)
            u[li] = np.frombuffer(base64.b64decode(hob["kyt_uvs"]), dtype=np.float32).reshape(-1, 2)
            me.uv_layers["UVMap"].data.foreach_set("uv", u.ravel())
            me.update()
            hme = hob.data
            bpy.data.objects.remove(hob)
            bpy.data.meshes.remove(hme)
            continue
        if hob.get("kyt_reversed"):
            # Only windings turned (the bluffs facing): the same faces turned back, their normals restored.
            me = ob.data
            turned = json.loads(hob["kyt_reversed"])
            old = json.loads(hob["kyt_normals"])
            normals = np.zeros(len(me.loops) * 3)
            me.corner_normals.foreach_get("vector", normals)
            normals = normals.reshape(-1, 3)
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            bmesh.ops.reverse_faces(bm, faces=[bm.faces[fi] for fi in turned])
            bm.to_mesh(me)
            bm.free()
            me.update()
            for fi in turned:
                by_vertex = {c[0]: c[1:] for c in old[str(fi)]}
                for li in me.polygons[fi].loop_indices:
                    normals[li] = by_vertex[me.loops[li].vertex_index]
            me.normals_split_custom_set([tuple(n) for n in normals])
            hme = hob.data
            bpy.data.objects.remove(hob)
            bpy.data.meshes.remove(hme)
            continue
        if hob.get("kyt_vertices"):
            # Only vertices moved (the bluffs): each goes back, and the faces they held their normals.
            me = ob.data
            for i, x, y, z in json.loads(hob["kyt_vertices"]):
                me.vertices[i].co = (x, y, z)
            old = json.loads(hob["kyt_normals"])
            normals = [Vector(n.vector) for n in me.corner_normals]
            for fi, ns in old.items():
                for li, n in zip(me.polygons[int(fi)].loop_indices, ns):
                    normals[li] = Vector(n)
            me.update()
            me.normals_split_custom_set(normals)
            hme = hob.data
            bpy.data.objects.remove(hob)
            bpy.data.meshes.remove(hme)
            continue
        if hob.get("kyt_whole"):
            # Kept whole (edit 1): the object takes its old mesh back.
            old = ob.data
            keep = old.name
            ob.data = hob.data
            bpy.data.objects.remove(hob)
            bpy.data.meshes.remove(old)
            ob.data.name = keep
            continue
        me = ob.data
        fa = np.zeros(len(me.polygons), dtype=np.int32)
        me.attributes["authored_edit"].data.foreach_get("value", fa)
        kept_normals = {}
        corner_normals = me.corner_normals
        for poly in me.polygons:
            if fa[poly.index] == edit:
                continue
            for li in poly.loop_indices:
                kept_normals[corner_key(me.vertices[me.loops[li].vertex_index].co, poly.center)] = Vector(corner_normals[li].vector)
        bm = bmesh.new()
        bm.from_mesh(me)
        fl = bm.faces.layers.int["authored_edit"]
        gone = [f for f in bm.faces if f[fl] == edit]
        bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')
        bm.verts.ensure_lookup_table()
        # A kept vertex is found where it stands; one the edit moved, left without faces by theirs
        # going, by its plan position (a shore wall's foot under its top; range north's top over its
        # underside, whose corners stand in the same columns, which must never be taken).
        loose = {v for v in bm.verts if not v.link_faces}
        exact = {tuple(round(c, 4) for c in v.co): v for v in bm.verts if v not in loose}
        column = {}
        for v in loose:
            column.setdefault((round(v.co.x, 4), round(v.co.y, 4)), []).append(v)
        # Range north carries neither (edit 106): its faces come back without them.
        col = bm.loops.layers.float_color.get("Col")
        uv = bm.loops.layers.uv.get("UVMap")
        hme = hob.data
        hcol = hme.color_attributes.get("Col") if col is not None else None
        huv = hme.uv_layers.get("UVMap") if uv is not None else None
        claimed = {exact[k] for k in (tuple(round(c, 4) for c in v.co) for v in hme.vertices) if k in exact}
        made = []
        for v in hme.vertices:
            k3 = tuple(round(c, 4) for c in v.co)
            k2 = k3[:2]
            spare = [o for o in column.get(k2, []) if o not in claimed]
            if k3 in exact:
                made.append(exact[k3])
            elif len(spare) == 1 and len(column[k2]) == 1:
                spare[0].co = v.co
                claimed.add(spare[0])
                made.append(spare[0])
            else:
                nv = bm.verts.new(v.co)
                column.setdefault(k2, []).append(nv)
                claimed.add(nv)
                made.append(nv)
        for poly in hme.polygons:
            nf = bm.faces.new([made[i] for i in poly.vertices])
            nf.material_index = poly.material_index
            nf.smooth = poly.use_smooth
            for lp, li in zip(nf.loops, poly.loop_indices):
                if hcol is not None:
                    lp[col] = hcol.data[li].color
                if huv is not None:
                    lp[uv].uv = huv.data[li].uv
        # What only the edit's faces used: its new corners, and edges no face uses now.
        bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(me)
        bm.free()
        me.update()
        if "authored_edit" in me.attributes and not any(
                v for v in (lambda a: (me.attributes["authored_edit"].data.foreach_get("value", a), a)[1])(np.zeros(len(me.polygons), dtype=np.int32))):
            me.attributes.remove(me.attributes["authored_edit"])
        # The restored faces' corner normals, where the history kept them (edit 2 on); else smooth.
        if "kyt_normal" in hme.attributes:
            hn = np.zeros(len(hme.loops) * 3)
            hme.attributes["kyt_normal"].data.foreach_get("vector", hn)
            hn = hn.reshape(-1, 3)
            for poly in hme.polygons:
                c = poly.center
                for li in poly.loop_indices:
                    kept_normals[corner_key(hme.vertices[hme.loops[li].vertex_index].co, c)] = Vector(hn[li])
        vn = [Vector(v.vector) for v in me.vertex_normals]
        normals = []
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                normals.append(kept_normals.get(corner_key(me.vertices[vi].co, poly.center), vn[vi]))
        me.normals_split_custom_set(normals)
        bpy.data.objects.remove(hob)
        bpy.data.meshes.remove(hme)
    for name in entry.get("added", []):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            me = ob.data
            bpy.data.objects.remove(ob)
            if me.users == 0:
                bpy.data.meshes.remove(me)
    for name in entry.get("hid", []):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            ob.hide_set(False)
            ob.hide_render = False
    for cname in (LAKES_COLLECTION, HISTORY, EARTHWORKS):
        c = bpy.data.collections.get(cname)
        if c is not None and not c.all_objects:
            bpy.data.collections.remove(c)
    if entry.get("export_before") is not None:
        bpy.context.scene["kyt_export_collections"] = entry["export_before"]
    log(remove=edit)
    readme("Ground edit %d undone (%s): the replaced faces restored; %s removed." % (edit, entry["name"], ", ".join(entry.get("added", [])) or "nothing"))
    print("world_terrain_ground_edit: edit %d undone" % edit)


def render(folder, edit, views):
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'OBJECT'
    # The turned walls are seen as the game's collision sees them: a face from behind is not there.
    scene.display.shading.show_backface_culling = edit == BLUFFS_FACING_ID
    for ob in ground_objects():
        ob.color = (0.62, 0.66, 0.55, 1.0)
    for ob in bpy.data.collections[LAKES_COLLECTION].objects:
        ob.color = LAKE_COLOUR
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    for c in bpy.data.collections:
        if c.name not in (GROUND, LAKES_COLLECTION):
            for ob in c.objects:
                ob.hide_render = True
    if edit in NEW_LAND:
        # The sea, so the waterline reads; only in the render, which runs after the save.
        sea = float(edit_constant("world_terrain_coast_extension.py", "SEA_LEVEL"))
        sme = bpy.data.meshes.new("tmp_sea")
        sme.from_pydata([(-3000.0, 3000.0, sea), (4000.0, 3000.0, sea), (4000.0, -4000.0, sea), (-3000.0, -4000.0, sea)], [], [(0, 1, 2, 3)])
        sob = bpy.data.objects.new("tmp_sea", sme)
        sob.color = LAKE_COLOUR
        scene.collection.objects.link(sob)
    for key, (centre, across, level) in views.items():
        cx, cz = centre
        half = 0.5 * (across - 300.0) if across > 600.0 else 0.5 * across
        cam = bpy.data.cameras.new("tmp_cam")
        cam.type = 'ORTHO'
        cam.ortho_scale = across
        cam.clip_start = 1.0
        cam.clip_end = 20000.0
        ob = bpy.data.objects.new("tmp_cam", cam)
        scene.collection.objects.link(ob)
        ob.location = (cx, -cz, 3000.0)
        scene.camera = ob
        scene.render.filepath = os.path.join(folder, "ground_edit%d_%s_top.png" % (edit, key))
        bpy.ops.render.render(write_still=True)
        ob.location = (cx - 0.9 * half, -cz - 0.9 * half, level + 260.0 * half / 300.0)
        cam.type = 'PERSP'
        cam.lens = 30.0
        ob.rotation_euler = (math.radians(62.0), 0.0, math.radians(-45.0))
        scene.render.filepath = os.path.join(folder, "ground_edit%d_%s_oblique.png" % (edit, key))
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(ob)
        bpy.data.cameras.remove(cam)


def main():
    a = argv()
    if a["edit"] not in CARRIED:
        raise SystemExit("edits %s are carried so far; the rest come in their own batches" % sorted(CARRIED))
    edit = a["edit"]
    if a["undo"]:
        undo(edit)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_mainfile()
        return
    if any(e.get("id") == edit for e in json.loads(bpy.context.scene.get("kyt_ground_edits", "[]"))):
        raise SystemExit("Ground already carries edit %d; --undo first" % edit)
    bank_report = {}
    city_report = {}
    global against
    if edit == LAKE_BANKS_ID:
        against = 0.0
        now_t, pre_t, box, grid_points, bank_report = lake_banks_design()
        print("  lake banks design: %s" % json.dumps(bank_report))
    elif edit == SEAMS_ID:
        against = 0.0
        now_t, pre_t, box, grid_points, bank_report = seams_design()
        print("  seams design: %s" % json.dumps(bank_report))
    elif edit == RANGE_FLANKS_ID:
        against = 0.0
        now_t, pre_t, box, grid_points, bank_report = range_flanks_design()
        print("  range flanks design: %s" % json.dumps(bank_report))
    elif edit == NORTH_COAST_ID:
        against = NC_AGAINST
        now_t, pre_t, box, grid_points, bank_report = north_coast_design()
        print("  north coast design: %s" % json.dumps(bank_report))
    elif edit == RANGE_EAST_ID:
        against = 0.0
        now_t, pre_t, box, grid_points, bank_report = range_east_design()
        print("  range east design: %s" % json.dumps(bank_report))
    elif edit not in (SHELF_ID, LANDFORM_SHELF_ID, CITY_CUT_ID, BLUFFS_ID, BLUFFS_FACING_ID, HILLSIDE_COLOURS_ID):
        now_t, pre_t, box, grid_points = grid_surfaces(edit)
    before = {ob.name: coords(ob).copy() for ob in ground_objects()}
    reports = {}
    land = None
    land_report = {}
    if edit == SHELF_ID:
        reports, land_report, land = coast_shelf(edit, a["dry"])
        print("  %-34s %s" % (SHELF, ", ".join("%s %s" % kv for kv in land_report.items())))
    elif edit == LANDFORM_SHELF_ID:
        reports, land_report, land = landform_shelf(edit, a["dry"])
        print("  %-34s %s" % (LANDFORM_SHELF, ", ".join("%s %s" % kv for kv in land_report.items())))
        if not a["dry"] and land is None:
            raise SystemExit("no shelf face to build")
    elif edit in RANGE_BLEND:
        reports, land_report, land = range_blend(edit, now_t, pre_t, a["dry"])
        print("  %-34s %s" % (RANGE_BLEND[edit], ", ".join("%s %s" % kv for kv in land_report.items())))
    elif edit in NEW_LAND:
        reports, land_report, land = new_land(edit, now_t, pre_t, box, a["dry"])
        print("  %-34s %s" % (NEW_LAND[edit], ", ".join("%s %s" % kv for kv in land_report.items())))
    elif edit == CITY_CUT_ID:
        reports, city_report = city_cut(edit, a["dry"])
    elif edit == BLUFFS_ID:
        reports, city_report = bluffs(edit, a["dry"])
        print("  bluffs: %s" % json.dumps(city_report))
    elif edit == BLUFFS_FACING_ID:
        reports, city_report = bluffs_facing(edit, a["dry"])
        print("  bluffs facing: %s" % json.dumps(city_report))
    elif edit == HILLSIDE_COLOURS_ID:
        reports, city_report = hillside_colours(edit, a["dry"])
        print("  hillside colours: %s" % json.dumps(city_report))
    else:
        for ob in ground_objects():
            if edit in (LAKE_BANKS_ID, SEAMS_ID) and ob.name != "terrain_world_mainland_reserve":
                continue
            if edit == RANGE_FLANKS_ID and ob.name != RF_OBJECT:
                continue
            if edit == NORTH_COAST_ID and ob.name != NC_OBJECT:
                continue
            if edit == RANGE_EAST_ID and ob.name != RE_OBJECT:
                continue
            r = carry(ob, edit, now_t, pre_t, box, grid_points, a["dry"],
                      top_only=edit in (RANGE_FLANKS_ID, NORTH_COAST_ID, RANGE_EAST_ID),
                      top_min_nz=NC_TOP_MIN_NZ if edit == NORTH_COAST_ID else None, joined=edit == RANGE_EAST_ID)
            if r is not None:
                reports[ob.name] = r
        if edit in (RANGE_FLANKS_ID, RANGE_EAST_ID) and not a["dry"]:
            reports[RF_OBJECT]["banded"] = range_flanks_bands(edit)
    for name, r in reports.items():
        print("  %-34s %s" % (name, ", ".join("%s %s" % (k, ("%.2f" % v) if isinstance(v, float) else v) for k, v in r.items())))
    road = None
    road_report = {}
    if edit in ROAD_NATURAL:
        road, road_report = road_natural(edit, now_t, pre_t, box, a["dry"])
        print("  %-34s %s" % (ROAD_NATURAL[edit], ", ".join("%s %s" % kv for kv in road_report.items())))
    if a["dry"]:
        print("world_terrain_ground_edit: --dry; nothing saved")
        return
    # Every vertex outside the edit's faces exactly where it was.
    for ob in ground_objects():
        if ob.name == land:
            continue
        if ob.name not in reports:
            if not np.array_equal(before[ob.name], coords(ob)):
                raise SystemExit("%s moved, and the edit never reached it" % ob.name)
            continue
        if edit in RANGE_BLEND or edit in (CITY_CUT_ID, BLUFFS_ID):
            # `range_blend`, `city_cut` and `bluffs` proved what they did not move themselves.
            continue
        now = coords(ob)
        used = edit_face_vertices(ob, edit)
        old = {tuple(v) for v in before[ob.name]}
        strays = sum(1 for i in range(len(now)) if i not in used and tuple(now[i]) not in old)
        if strays:
            raise SystemExit("%s: %d vertices outside the edit's faces moved" % (ob.name, strays))
    if edit == SHELF_ID:
        design = {"name": "coast_shelf"}
    elif edit == LANDFORM_SHELF_ID:
        design = {"name": "landform_shelf"}
    elif edit == LAKE_BANKS_ID:
        design = {"name": "lake_banks"}
    elif edit == CITY_CUT_ID:
        design = {"name": "city_cut"}
    elif edit == SEAMS_ID:
        design = {"name": "seams"}
    elif edit == BLUFFS_ID:
        design = {"name": "bluffs"}
    elif edit == BLUFFS_FACING_ID:
        design = {"name": "bluffs_facing"}
    elif edit == HILLSIDE_COLOURS_ID:
        design = {"name": "hillside_colours"}
    elif edit == RANGE_FLANKS_ID:
        design = {"name": "range_flanks"}
    elif edit == NORTH_COAST_ID:
        design = {"name": "north_coast"}
    elif edit == RANGE_EAST_ID:
        design = {"name": "range_east"}
    else:
        design = next(e for e in json.loads(bpy.data.objects[GRID].get("kyt_edits", "[]")) if e.get("id") == edit)
        if edit in WITH:
            refine = next(e for e in json.loads(bpy.data.objects[GRID].get("kyt_edits", "[]")) if e.get("id") == WITH[edit][0])
            design = dict(design, name="%s with %s" % (design["name"], refine["name"]))
    tris = ground_triangles()
    coll = lakes_collection()
    added = [land] if land else []
    if road is not None:
        added.append(road.name)
    hid = []
    areas = {}
    lakes = edit_constant("world_terrain_edit_hill_lakes.py", "LAKES") if edit == 4 else {}
    for key, lk in lakes.items():
        polys, area, lbox = lake_water(key, lk, tris, now_t)
        areas[key] = round(area / 10000.0, 2)
        name = "lake_%s" % key
        note = ("%s at +%.1f, built on Ground's own triangles below the brim (Stage 3, edit 4 carried; "
                "%.1f ha against %.1f ha on the grid design); spill and creek walled off" % (key, lk["brim"], area / 10000.0, design["lakes"][key]["area_ha"]))
        ob = build_plane(name, polys, note)
        coll.objects.link(ob)
        added.append(name)
        print("  %s: %.2f ha of water at +%.1f, x %.0f..%.0f z %.0f..%.0f (grid design %.1f ha)" % (
            name, area / 10000.0, lk["brim"], lbox[0], lbox[1], lbox[2], lbox[3], design["lakes"][key]["area_ha"]))
        plane = bpy.data.objects.get(DESIGN_PLANES[key])
        if plane is not None and not plane.hide_get():
            plane.hide_set(True)
            plane.hide_render = True
            hid.append(plane.name)
    for name, plane_name in POOLS.get(edit, {}).items():
        plane = bpy.data.objects[plane_name]
        polys, area, level = pool_water(plane, tris)
        if not polys:
            raise SystemExit("%s: no Ground below +%.2f inside %s" % (name, level, plane_name))
        areas[name] = round(area, 1)
        ob = build_plane(name, polys, "%s at +%.1f, built on Ground's own triangles below that level inside %s's outline "
                                     "grown by %.0f m (Stage 3, edit %d carried)" % (name, level, plane_name, POOL_GROW, edit))
        coll.objects.link(ob)
        added.append(name)
        print("  %s: %.0f m2 of water at +%.2f (design plane %s)" % (name, area, level, plane_name))
        if not plane.hide_get():
            plane.hide_set(True)
            plane.hide_render = True
            hid.append(plane.name)
    scene = bpy.context.scene
    export_before = list(scene.get("kyt_export_collections", []))
    earthworks = bpy.data.collections.get(EARTHWORKS)
    scene["kyt_export_collections"] = [GROUND, LAKES_COLLECTION] + ([EARTHWORKS] if earthworks and earthworks.all_objects else [])
    entry = {"id": edit, "name": design["name"], "script": "tools/blender/world_terrain_ground_edit.py",
             "date": TODAY, "objects": sorted(reports), "report": reports, "lakes_ha": areas,
             "added": added, "hid": hid, "export_before": export_before}
    if land:
        entry["new_land"] = land_report
    if road is not None:
        entry["road_natural"] = road_report
    if bank_report:
        entry["seams" if edit == SEAMS_ID else "flanks" if edit == RANGE_FLANKS_ID else "coast_north" if edit == NORTH_COAST_ID
              else "range_east" if edit == RANGE_EAST_ID else "banks"] = bank_report
    if edit == CITY_CUT_ID:
        entry["city"] = city_report
    if edit == BLUFFS_ID:
        entry["bluffs"] = city_report
    if edit == BLUFFS_FACING_ID:
        entry["bluffs_facing"] = city_report
    if edit == HILLSIDE_COLOURS_ID:
        entry["hillside_colours"] = city_report
    log(entry)
    held = sum(r.get("seam_held", 0) for r in reports.values())
    if edit == SHELF_ID:
        readme("Ground edit %d (%s), %s: every coast's shore wall cut %.1f m under the sea and the part below "
               "dropped, in %s; from that line %s slopes %.0f m out to %.1f (%s); the wall panels' old faces "
               "kept in %s. Undo: tools/blender/world_terrain_ground_edit.py -- --edit shelf --undo." % (
                   edit, design["name"], TODAY, SHELF_UNDER, ", ".join(reports), land, SHELF_W, SHELF_DEPTH,
                   ", ".join("%s %s" % kv for kv in land_report.items()), HISTORY))
    elif edit == LANDFORM_SHELF_ID:
        readme("Ground edit %d (%s), %s: %s runs the landforms' coasts on below the waterline from each side "
               "facing the open sea, %.1f m under it, %.0f m out to %.1f (%s); the shells untouched. Undo: "
               "tools/blender/world_terrain_ground_edit.py -- --edit landform_shelf --undo." % (
                   edit, design["name"], TODAY, land, SHELF_UNDER, SHELF_W, SHELF_DEPTH,
                   ", ".join("%s %s" % kv for kv in land_report.items())))
    elif edit == LAKE_BANKS_ID:
        readme("Ground edit %d (%s), %s: the hill lakes' banks laid back to %.0f degrees from each waterline "
               "(%.1f m over its brim) wherever the reserve stood above that within %.0f m of the water (%s); "
               "the water, its level and outline, the falls and the seams held; the replaced faces kept in %s. "
               "Undo: tools/blender/world_terrain_ground_edit.py -- --edit lake_banks --undo." % (
                   edit, design["name"], TODAY, math.degrees(math.atan(BANK_SLOPE)), BANK_LIP, BANK_REACH,
                   json.dumps(bank_report), HISTORY))
    elif edit == CITY_CUT_ID:
        readme(city_readme(edit, design["name"], city_report))
    elif edit == BLUFFS_ID:
        readme("Ground edit %d (%s), %s: the reserve's shore walls laid back to %.0f degrees, the land's edge "
               "held and each wall's foot moved out to sea, %.1f m under the coast shelf there, which is not touched "
               "(%s); the old foot positions and the walls' normals kept on %s for the undo. Undo: "
               "tools/blender/world_terrain_ground_edit.py -- --edit bluffs --undo." % (
                   edit, design["name"], TODAY, BLUFF_ANGLE, BLUFF_UNDER, json.dumps(city_report),
                   "%s__before_edit%d" % (BLUFF_OBJECT, edit)))
    elif edit == BLUFFS_FACING_ID:
        readme("Ground edit %d (%s), %s: the reserve's shore walls wound to the land turned to face the sea, those "
               "edit %d laid back (which then faced down where they are the top ground, so the game's one-sided "
               "collision let anything coming down onto them through) and those still standing by coast north; each "
               "turned wall shaded flat along its new winding, no vertex moved (%s); the turned faces and their old "
               "corner normals kept on %s for the undo. Undo: tools/blender/world_terrain_ground_edit.py -- --edit "
               "bluffs_facing --undo." % (edit, design["name"], TODAY, BLUFFS_ID, json.dumps(city_report),
                                          "%s__before_edit%d" % (BLUFF_OBJECT, edit)))
    elif edit == HILLSIDE_COLOURS_ID:
        readme("Ground edit %d (%s), %s: edit %d's faces (the hillside regrade) take their corner colours and texture "
               "coordinates again from the faces it replaced, kept in %s, each corner by its weights in the face it lies "
               "in seen from above, held to that face; when it went in they were extrapolated from faces the corners lay "
               "outside of, and the game drew them black and white; nothing moved (%s); the old values kept on %s for the "
               "undo. Undo: tools/blender/world_terrain_ground_edit.py -- --edit hillside_colours --undo." % (
                   edit, design["name"], TODAY, HILLSIDE_EDIT, "%s__before_edit%d" % (HILLSIDE_OBJECT, HILLSIDE_EDIT),
                   json.dumps(city_report), "%s__before_edit%d" % (HILLSIDE_OBJECT, edit)))
    elif edit == RANGE_FLANKS_ID:
        readme("Ground edit %d (%s), %s: range north's block hill by the headland, its flanks big flat faces of 50 to "
               "76 degrees, laid back to %.0f degrees: within %.0f m of each sheer cell of the hill, on range north's own "
               "land, %.0f m clear of %s, %.0f m of the design grid's road corridor and tunnel lids, and north of z %.0f, the slope limited "
               "symmetrically as the seams', cut and fill, alternated with smoothing over what moved (%s); only the faces "
               "one sees from above refined and carried, its sides, underside and internal sheets untouched; the moved "
               "faces take the range's level bands; the replaced faces kept in %s. Its rocks move with the ground by "
               "tools/blender/range_rocks_on_ground.py. Undo: tools/blender/world_terrain_ground_edit.py -- --edit "
               "range_flanks --undo." % (edit, design["name"], TODAY, math.degrees(math.atan(RF_SLOPE)), RF_REACH,
                                         RF_ROAD_CLEAR, RF_ROAD, RF_ROAD_GUARD, RF_SOUTH, json.dumps(bank_report), HISTORY))
    elif edit == NORTH_COAST_ID:
        readme("Ground edit %d (%s), %s: coast north cut back, alone: over the twin-bore tunnel north of the headland "
               "its face above the generator's own ground on the tunnel (which stays) laid back to 45 degrees, and by the "
               "plug its sea face to 55 degrees from the shore; each from what it keeps, %.0f m round Ground's open edges "
               "(the corridor and the lids) and the shore, within %.0f m of the zone's sheer cells, faded out over %.0f m, "
               "its crest rounded over %.0f m (%s); only the faces one sees from above refined and carried; the replaced "
               "faces kept in %s. Undo: tools/blender/world_terrain_ground_edit.py -- --edit north_coast --undo." % (
                   edit, design["name"], TODAY, NC_HOLD, NC_REACH, NC_TAPER, NC_CREST, json.dumps(bank_report), HISTORY))
    elif edit == RANGE_EAST_ID:
        readme("Ground edit %d (%s), %s: the west nose of range north's east piece, a ridge through the reserve, cut "
               "back to %.0f degrees from the ground it keeps, the reserve's included, never within %.0f m of the reserve "
               "under it; the corners its sides hang from and %.0f m round Ground's open edges held, within %.0f m "
               "of its sheer cells, faded out over %.0f m, its crest rounded over %.0f m (%s); only the faces one sees "
               "from above refined and carried, those meeting its sides included; the moved faces take the range's level "
               "bands; the replaced faces kept in %s. Undo: tools/blender/world_terrain_ground_edit.py -- --edit "
               "range_east --undo." % (edit, design["name"], TODAY, math.degrees(math.atan(RE_SLOPE)), RE_SKIN,
                                       RE_HOLD, RE_REACH, RE_TAPER, RE_CREST, json.dumps(bank_report), HISTORY))
    elif edit == SEAMS_ID:
        readme("Ground edit %d (%s), %s: the reserve's seams blended where it stood against itself in sheer walls "
               "(sites %s of the sheer-face survey): within %.0f m of every sheer cell the slope limited to %.1f, "
               "symmetrically, alternated with smoothing over what moved, cut and fill (%s); %.0f m round Ground's open "
               "edges, lake water and every other body held; the replaced faces kept in %s. Undo: "
               "tools/blender/world_terrain_ground_edit.py -- --edit seams --undo." % (
                   edit, design["name"], TODAY, ", ".join(SEAM_SITES), SEAM_REACH, SEAM_SLOPE, json.dumps(bank_report),
                   SEAM_HOLD, HISTORY))
    elif edit in RANGE_BLEND:
        readme("Ground edit %d (%s), Stage 3, %s: in the zone grid edit %d changed, the landforms %s were cut along "
               "its edge, emptied inside it and capped, and %s built there as one sheet on the edit's surface (%s); "
               "the landforms kept whole in %s. Undo: tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
                   edit, design["name"], TODAY, edit, ", ".join(reports), land,
                   ", ".join("%s %s" % kv for kv in land_report.items()), HISTORY, edit))
    elif land:
        readme("Ground edit %d (%s), Stage 3, %s: the land grid edit %d designed beyond the shore built as %s in "
               "Ground (%s); the shore wall panels it meets cut at its edge in %s, their old faces kept in %s. Undo: "
               "tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
                   edit, design["name"], TODAY, edit, land, ", ".join("%s %s" % kv for kv in land_report.items()),
                   ", ".join(reports), HISTORY, edit))
    else:
        readme("Ground edit %d (%s), Stage 3, %s: grid edit %s carried onto Ground (%s): its region refined to "
           "a %.0f m lattice and given the grid's designed surface; %d vertices on the seams with the generator's "
           "ground held where they were; water %s built on Ground in the Lakes collection, exported with Ground; "
           "design planes %s hidden; the replaced faces kept in %s. Undo: "
           "tools/blender/world_terrain_ground_edit.py -- --edit %d --undo." % (
               edit, design["name"], TODAY, ("%d with %d, its refinement," % (edit, WITH[edit][0])) if edit in WITH else edit,
               ", ".join(reports), LATTICE, held,
               ", ".join("%s %s" % (k, ("%.2f ha" % v) if k in lakes else ("%.0f m2" % v)) for k, v in areas.items()) or "none",
               ", ".join(hid) or "none", HISTORY, edit))
        if road is not None:
            readme("Ground edit %d: Ground's edge along the road corridor moved with it (%d vertices, up to %.1f m), "
                   "and %s, in the %s collection, hands the generator the edit's natural ground under the "
                   "corridor (%s); the road's own level does not read it." % (
                       edit, sum(r.get("seam_followed", 0) for r in reports.values()),
                       max((r.get("seam_followed_most", 0.0) for r in reports.values()), default=0.0),
                       road.name, EARTHWORKS, ", ".join("%s %s" % kv for kv in road_report.items())))
    if edit in RANGE_BLEND:
        print("world_terrain_ground_edit: edit %d carried; every shell's surface outside its zone unchanged" % edit)
    elif edit == CITY_CUT_ID:
        print("world_terrain_ground_edit: edit %d carried; every corner of %s the design stands over unchanged" % (edit, CITY_SHELL))

    else:
        print("world_terrain_ground_edit: edit %d carried; every vertex outside its faces unchanged" % edit)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_mainfile()
    # After the save, so the render's hidden layers and cameras never reach the master.
    if a["render"]:
        views = {key: (lk["centre"], 2.0 * float(lk["R"]) + 300.0, float(lk["brim"])) for key, lk in lakes.items()}
        views.update(VIEWS.get(edit, {}))
        render(a["render"], edit, views)


main()
