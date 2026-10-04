"""The site and the rules for the hillside terraces proposal (2026-10-02).

Christina's red lines across the coast highway from the beach town, the
fixed points they hang from, the street, lot, wall and slope rules, the
protected sets and the viewpoints. World metres, x east, z south; every
height in this proposal is metres OVER THE SEA (the beach town plan's
datum), H = Godot y + 7.5.
"""

import os

SEA_Y = -7.5                       # Godot y of the sea


def over_sea(y):
    return y + 7.5


# --- her lines (traced from her sketch on the pass 12 plan; the brief's points) ---
LINE1 = [(43, 450), (41, 493), (52, 530), (66, 563), (84, 594)]     # from the lower terrace street's west end
LINE2 = [(58, 485), (70, 515), (89, 545), (104, 570), (110, 587)]   # from the upper terrace street's west end
MEET = (98.0, 591.0)                                                 # where the two meet
DOWN = [(98, 591), (89, 594), (77, 616), (69, 628)]                  # the leg down to the highway's east side
J3 = (29.07, 649.25)                                                 # junction on Beach Road's climb (pass 13)
J3_H = 18.2                                                          # its height over the sea (J1 10.7 + 7.07 % x 106 m)
LOWER_TERRACE_H = 25.0             # the lower terrace street at its west end (pass 10 / pass 13)
UPPER_TERRACE_H = 35.0             # the upper terrace street at its west end

# pass 13's lower street (design13.py LOW_CTRL): from the lower terrace's west end along the hill's foot
# and down under the highway to J3; B and C reuse it as the street to the underpass
LOW_CTRL = [(44, 451), (39, 456), (33.7, 466), (30, 476), (27.5, 486), (25.9, 496), (25.6, 505), (26.6, 513),
            (28.4, 522), (31, 531), (34.2, 541), (37.6, 551), (41.6, 562), (46.4, 574), (51.4, 586), (56.4, 598),
            (60.4, 608), (62.4, 615), (61.8, 622), (58.2, 629), (52.4, 635), (45, 640), (37.4, 644.6), (29.07, 649.25)]

# --- the rules ---
G_MAX = 0.11            # street grade
G_WORST = 0.12          # allowed at worst, and said where
G_LANDING = 0.04        # within LANDING m of a street junction
LANDING = 10.0
VC_LEN = 20.0           # vertical curves: the profile is averaged over this length
STREET_HALF = 4.5       # carriageway 5 m + two 2 m sidewalks = 9 m
LOT_FRONT = 8.0         # lots 8 m along the street ...
LOT_DEPTH = 7.0         # ... by 7 m deep (pass 10's hillside rule)
LOT_RISE = 3.0          # a lot cut into the hill is a pad one garage storey over the street: the garage under, its front at the sidewalk
WALL_MAX = 4.0          # retaining wall at the back of a lot (or of a sidewalk with no lots), at most
CUT_SLOPES = (1.0, 1.5)  # planted cut slope above the wall, horizontal per vertical: 1:1 designed, 1:1.5 compared
FILL_SLOPE = 2.0        # fill below a street's downhill edge, 1:2
STEPS_HALF = 2.0        # public steps 4 m wide
STEP_RISE, STEP_TREAD = 0.15, 0.30   # risers and treads: 1:2
STEP_LANDING_EVERY = 12  # risers between landings
STEP_LANDING = 1.5      # m of landing
LOT_MAX_CUT_SHALLOW = 1.0   # a downhill-side lot stands on natural ground at most this much above the street ...
LOT_MAX_DROP = 8.0          # ... and at most this far below it
DOWNHILL_LOTS = True

# --- the highway: protected ---
HW_HALF = 15.6          # coast extension tool's HIGHWAY_W / 2: both carriageways and their shoulders
HW_VERGE = 2.0          # and a verge beyond: the highway's ground ends HW_HALF + HW_VERGE from the centreline
HW_PAVED_HALF = 12.5    # the paved carriageways and median: x 42.5..67.5 about a centre of 55 at z 630 (1 Oct probe)
HW_CLEAR = 4.9          # clear height under the highway for the street (16 ft)
HW_DECK = 1.6           # the highway's deck depth at the underpass
RAMP_ZMAX = 390.0       # the interchange ramps lie at z 380..386 (1 Oct probe): north of this proposal's box

# --- rasters ---
NEAR = dict(x0=-10.0, x1=400.0, z0=380.0, z1=820.0, step=1.0)     # the design raster (wide enough for D's regrade)
FAR = dict(x0=-160.0, x1=1200.0, z0=150.0, z1=1150.0, step=5.0)   # the backdrop for skylines

# --- D, the regrade: her lines as ordinary streets on a reshaped hill ---
D_SLOPE = 1.0 / 3.0     # steepest ground of the regrade, planted
D_BLEND = 15.0          # m over which the regrade is smoothed into today's ground
D_PASSES = 150          # relaxation passes that round its creases (about sqrt(150) = 12 m of reach)
D_LOT_WALL = 2.0        # lots on low terraces: walls at most this
# pass 10's terrace streets that her lines continue (pass 12 plan data): level at 25 and 35 m; the regrade keeps them on grade
TERRACE_25 = [(171, 400), (150, 408), (129, 417), (100, 427), (75, 435), (57, 441), (44, 451)]
TERRACE_35 = [(236, 400), (190, 420), (148, 440), (112, 452), (77, 463), (62, 471), (52, 484)]
SUMMIT_BOX = (100.0, 200.0, 570.0, 690.0)  # the hill's own top, about 87 m near (140..160, 620..630)
D_REACH_X = 360.0       # the regrade stops short of the range's ridge beyond x 400 (a 1:3 slope from the meeting would just clip it)

# --- viewpoints in the town (eye 1.6 m over the ground) ---
EYE = 1.6
VIEWS = {
    "beach_road_row": {"xz": (-61.2, 440.0), "label": "Beach Road at the row (the terrace crosswalk)"},
    "second_street": {"xz": (-28.0, 457.5), "label": "Second Street, by the laundromat"},
    "V4": {"xz": (-18.5, 470.5), "label": "V4, the skate park's upper deck"},
}
UNDERPASS_MOUTH = (20.0, 462.0)    # Second Street's underpass, its mouth on the hill side (pass 12 plan)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
MASTER = os.path.join(ROOT, "assets", "source", "world_terrain_master.blend")
RENDERS = os.path.join(ROOT, "documentation", "terrain", "renders")
PREFIX = "proposal_hillside_terraces_"

REF_CURVES = ("coast_highway_centreline", "beach_town_outline", "street_beach_road", "street_beach_second_street",
              "street_beach_shore_street", "street_beach_lot", "coast_extension_B_shoreline",
              "rail_beach_town_from_plan_town", "rail_beach_town_from_plan_platform")


def refuse_assets(path):
    """Never write under assets/ (the master lives there)."""
    p = os.path.realpath(path)
    if p == os.path.realpath(MASTER) or p.startswith(os.path.realpath(os.path.join(ROOT, "assets")) + os.sep):
        raise SystemExit(f"refusing to write under assets/: {p}")
