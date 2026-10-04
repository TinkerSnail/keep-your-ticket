"""The beach town's Victorian worker's cottage, blocked out (2026-10-02):
two storeys, gable to the street, on a 9 m lot with a side driveway, in two
variants from Christina's photographs (`documentation/reference/houses/`).

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/victorian_cottage.blend --python tools/blender/victorian_cottage.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, one shell in four `kyt_variant`s that stand
at the origin together, as the park lamp's three do (`plaza_street.py`):
`blue` in `export` itself and `purple`, `blue_b` and `purple_b` each in
`export/variant_<name>` with its eye shut (Send writes one prop per variant;
Check and the handback render show the first). All four are cartoony builds
(below): the study approved on 2026-10-04 as the standard for every house
replaced the realistic blue, and the other three were converted to it in
place the same day (her "do the purple and the b variants next"; "these
would be replacements and not variants"), the realistic builds left to git
history. The `_b` pair (2026-10-03) are Christina's "this AND that": the
alternatives the first pass asked about, built as variants beside the blue
and the purple. `blue_b` is the blue with the glazed porch wrapping the
corner under an L-shaped lean-to tucked under the main eave, a side door,
landing and flight on the driveway side instead of the back stoop, and the
blue's brick chimney. `purple_b` is the purple at a lower pitch over a knee
wall, so the upstairs windows straddle the eave as its photo's do and the
peak ornament has room, its porch railed, and a brick chimney. Into the
locked `reference` go the lot and footprint outlines, a
1.7 m figure and the `ground_line` marker Check reads (the walls reach below
z = 0 on purpose). Everything the tool makes carries `kyt_victorian_cottage`,
so a rerun removes and rebuilds its own work and keeps anything of hers;
`export` holding anything untagged refuses without `--replace`.

**Frame.** Real metres, Z up, the street-side ground at z = 0, the origin at
the body's footprint centre. The front (gable, porch, door) faces -Y here,
which the glTF export (`send.py`, `export_yup=True`) turns into Godot's +Z.
+X is the viewer's right from the street: the driveway side.

**Contract** (enclosing, as the beach cottage): public faces, porches and
windows, no interior. Every opening is a real hole through a wall of real
thickness; the door and the panes are solid slabs set in the holes. Every
door's sill stands THRESHOLD over the deck it opens onto, flush for the
player. The decks are walkable from their steps, and the steps follow the
park's stair rule: a narrow ramp is the floor, the treads are scenery showing
past it and do not collide (`kyt_collision = none`). No two shapes share a
plane: a part that meets another laps into it or stands proud of it, and the
tool's own scan (`coplanar_pairs`) reports any pair that does.

**What the photographs say.** `victorian_blue_cottage.webp`: a tall narrow
gable, steeper than 45 degrees, the balcony's floor on the eave line (so the
upstairs floor is the eave and the upstairs is in the gable), a triple
window over the balcony, a sunburst at the peak between bargeboards with a
red inner band, the main floor about ten risers over the driveway, the stair
straight down from the door, the glazed porch at the right-front corner with
its own small gable tucked under the main eave, the entry landing open under
the balcony. `purple_painted_lady.png`: the same bones three risers up, the
porch the house's width on turned posts with a shed roof under the eave,
paired upstairs windows with pointed hoods tight under the rakes, a
spindle-work fan in the peak, a door at the left and a window at the right.
Both read in silhouette and chunky trim, so that is what is built:
bargeboards, the fan, brackets, posts, railings, hoods. Board-and-batten,
lap siding, divided lights and the sawn ornament are left to painting.

**Choices to state.** The body is W = 6.0 m across by D = 10.5 m deep: the
blue photo's front is about seven doors wide and the lot leaves 2.4 m for
the driveway beside a 6.0 m body plus eaves. The upstairs floor is the eave
(purple_b's is a knee wall under it). The blue's main floor is 1.55 m up,
ten risers at the first builds' going, the purple's 0.60 m, four: those set
each house's grade, which its few chunky risers keep. Each variant keeps
its own palette (`PALETTES`), with a shaded accent for its trim under the
eaves. Colours are flat stand-ins named
`victorian_cottage_<variant>_<surface>` for the painting to replace.

**blue, the cartoony build** (2026-10-03; approved 2026-10-04 as the
study variant `blue_cartoon`, then made the blue). The houses had drifted
realistic beside the approved chunky props (bench, globe lamp, bin, azalea):
rows of thin uprights, 14 cm newels, trim at photo size. This is the blue,
same photo, palette, lot and frame, drawn the way the props are.
Few, big pieces, and the folksy ones enlarged rather than dropped: the
sunburst becomes a bold gable truss of four fat wedge rays and a king post
with a finial, set across the rake under the bargeboards (the deeper rake
would hide it on the wall), its red only the hub as the photo's, the wall
between its rays, a red frieze with three drops under its collar; the
bargeboards are one board each, white over the photo's sawn red band, two
big drops a rake, the red under the eaves a shade darker as if in their
shadow; two big shaped brackets carry the balcony; the
newels are fat with a cap and a knob; the railings are a bottom rail or
stringer with square balusters at 0.30 m under a fat top rail, one piece and
a rail each run; the porch has timber posts and its own plain white barge.
Casings are single pieces 0.16 across, mullions included. The roof is the
heavy part (World of Warcraft's lesson, from Christina): a 0.30 slab at 55
degrees over a squatter storey (2.64 m), a bell-cast kick of 27 degrees
lapped under it to a 0.75 m eave, a 0.75 m rake, a 5 cm sag at mid-length,
and a fat stepped brick chimney. The walls lean in 1.75 degrees about the
eave line over a flared plinth: they are warped as tapered shells
(`body_warp`, `porch_warp`), so every casing and board follows the face and
nothing is tilted. A seeded hand (BC_SEED) puts the irregularities in: rays,
drops, brackets, newel caps, chimney steps, sagging top rails and a centimetre
off square on corner boards and casings; decks, sills and the stair's ramp
stay exact. A few clusters of chunky shingle tabs lie on the slopes, as the
hedges' leaf clusters do: scattered, never banded, the slab between them the
painted surface. Shingles, siding (its painted exposure 0.24 m, twice the
realistic blue's, 11 courses floor to eave) and grain stay in the paint. Its
chunky parts and the shingle grid are `cartoon_kit`'s, shared with every
house that takes the standard; the composition, the house's numbers and the
order of work (which the seeded hand's draws depend on) are here.

**purple and purple_b, the cartoony build** (2026-10-04; `build_purple_cartoon`).
The purple's photo, palette, lot and layout, converted as the blue was (the
standard's casings, newels, balusters, rails, bargeboards and bell-cast roof
from `cartoon_kit`), its own seeds (PC_SEED, PBC_SEED and their shingle
seeds), and its four ideas pushed. The turned porch posts: the photo's slim
teal posts made fat, a square gold pedestal capped with a flare, an
octagonal shaft turned with a ring, a fat belly and necks, a gold capital,
shaped brackets (the blue's balcony brackets, in the shaded magenta) from
each capital along the beam. The pointed hoods: a gold tympanum on each
paired window's casing, a fat teal cornice along its rakes, a knob on the
point, tight under the bargeboards. The spindle-work fan: on the wall, a fat
teal bar across the peak, the shaded magenta panel over it, gold rays shaped
as turned spindles in silhouette reaching up under the rakes, so the fan
fills the peak as the photo's slats do, and fat gold spindles hanging under
the bar, the middle one a pendant. The shed porch roof: a 0.26 slab at 9
degrees with its own bell-cast kick to a deep eave, a gold fascia over a
shaded magenta frieze, as the photo's edge, two shingle clusters of its own
(it falls toward the street, so `street_clusters` builds them turned). The
roof is the standard's: a 0.30 slab at 50 degrees (the purple's 48, a touch
steeper, for the hoods and fan under the deeper rakes), a 25 degree kick to
0.75 m eaves and rakes, the bargeboards plain over the shaded band, as the
photo's. The storey is 3.24 m (the purple's 3.0): the shed porch roof must
pass under the bargeboards' ends where they bend down with the kick. Three
chunky risers at the purple's grade, front and back; the back stoop is the
blue's, with parapets. The walls stay plumb: the blue's lean costs every
opening and barely shows, and the purple's porch and hoods would pay it.
purple_b: 38 degrees over a 1.2 m knee wall (a 19 degree kick), the
upstairs windows straddling the eave, 0.90 under it and 0.35 over, across a
teal belt at the eave line broken by their casings, which makes the
straddle read; a sunburst of seven rays on the palette's deep pink (its
accent is the rays' gold) with the room its flatter peak gives; the posts on
rail-high pedestals between square-baluster rails; a fat brick chimney.

**blue_b, the cartoony build** (2026-10-04; `build_blue_cartoon` with `b`).
The cartoony blue itself, leaning walls, roof, sunburst, balcony, entry
stair and chimney, from its own seeds (BBC_SEED and its shingle seed) and
palette, with blue_b's differences branching off it, so the blue's draws are
untouched. The wrapping glazed porch: from the body's front wall round its
right-front corner and 2.6 m back along the side, under one L-shaped lean-to
of two planar slabs welded on a hip that runs into the body's corner (the
side's slope set so both meet it at one height), its eave as high as the
front bargeboard's bent end and the main eaves let it stand (`wrap_eave`,
3.44 m: a squat lean-to tucked under the corner), a fat cream fascia
wrapping both eaves in one piece; plumb walls (the shared warp is a
rectangle's) on fat timber posts at the three outer corners, a glass band of
few big lights wrapping the corner. The side door's flight: a landing along
the wall at the door, the flight running down along the wall toward the back
in the blue's chunky risers at its grade, one bold mass of solid parapets
with fat caps and piers (as the blue's back stoop it replaces), standing off
the leaning wall. The blue's side window inside the porch is gone (its head
would stand over the lean-to); the side door moved 10 cm back so the
landing's parapet passes between its casing and the window's.
"""

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartoon_kit as ck  # noqa: E402

TAG = "kyt_victorian_cottage"
NAME = "victorian_cottage"

# --- the shell and the layout all four share ------------------------------------
# (the first, realistic builds' numbers that the cartoony ones kept: the frame,
# the lot's layout, the floors and the stairs' grades)
W, D = 6.0, 10.5           # the body: across the front, and deep
T = 0.20                   # wall thickness
PITCH_DEG = 48.0           # the first builds' gable, between the two photographs (a Kit's default)
ROOF_T = 0.20              # their slab (a Kit's default; the cartoony slab is BC_ROOF_T)
WALL_TOP_IN = 0.28         # their side walls' tops over the eave (a Kit's default)
LIFT = 0.03                # a gable wall's top, this far inside the slab
PROUD = 0.04               # corner boards and posts, this far proud of the walls
BELOW = 0.05               # the end walls' feet under the ground (sides 1 cm lower, boards 3)
THRESHOLD = 0.01           # a door's sill over the deck outside it (the door is shut)
RISER_ABOUT, GOING = 0.155, 0.28   # the first builds' risers and going, which set each house's grade
RAIL_H = 0.90
SIDE_WINDOWS = (-3.5, 0.0, 3.5)   # centres along each side, BC_SIDE_WIN_W wide
BACK_DOOR_X = (0.45, 1.40)
STOOP_D = 1.20             # the back landing, deep
STAIR_W = 1.10

# the blue's (and blue_b's): its floor, entry landing and corner porch
B_FLOOR = 1.55             # ten risers over the driveway at the first build's going: the blue's grade
B_LANDING_D = 1.30         # the entry landing, open under the balcony
B_PORCH_X0 = 0.90          # the glazed corner porch's left face
B_PORCH_PROUD = 0.07       # the first blue's porch past the body's corner board, which set the driveway's edge
B_PORCH_D = 1.25           # how far it stands in front of the body
B_PORCH_T = 0.15
B_PORCH_PITCH = math.radians(38)

# the purple's (and purple_b's): its floor, door, window and porch
P_FLOOR = 0.60             # four risers at the first build's going: the purple's grade
P_DOOR_X = (-2.35, -1.40)
P_WINDOW_X = (0.30, 1.80)
P_PORCH_D = 2.30           # the full-width porch

# blue_b's porch round the corner; purple_b's pitch and knee wall
BB_WRAP = 1.0              # the porch past the body's right wall
BB_SIDE_D = 2.6            # how far it runs back along the side from the front wall
PB_PITCH_DEG = 38.0
PB_KNEE = 1.20             # the side walls rise this far over the upstairs floor

# --- blue, the cartoony build (BC_, for the study's name, blue_cartoon) ----------
# (2026-10-03) The blue's house, photo, palette and lot, drawn the way the
# park's approved props are: few big pieces, the folksy ones enlarged, the
# roof the heavy part, the walls leaning in, and a seeded touch of the hand.
# Each number's reason is beside the code that uses it. The standard's own
# sizes (casings, newels, balusters, rails, bargeboards) and the shingle grid
# are cartoon_kit's, shared with every house that takes the standard.
BC_SEED = 20261003         # every rerun draws the same irregularities
BC_SHINGLE_SEED = 20261004 # the roof's clusters, apart from the trim's hand
BC_STOREY = 2.64           # floor to eave: squatter than the blue's 3.0, and 11 courses of 0.24 m siding
BC_PITCH_DEG = 55.0        # steeper than the blue's 48: the house's one idea, pushed
BC_ROOF_T = 0.30           # the main slab (the blue's 0.20)
BC_LEAN_DEG = 1.75         # every body wall leans in going up, about the eave line
BC_GABLE_LIFT = 0.10       # a gable wall's top inside the slab, room for the lean to carry it across
BC_WALL_TOP_IN = 0.40      # the side walls' tops, inside the deeper slab at both faces
BC_KICK_AT = 0.10          # the bell-cast kick leaves the main slab's top this far past the wall
BC_KICK_DEG = 27.0         # the kick's pitch, half the main's
BC_KICK_T = 0.24           # vertical
BC_KICK_IN = 0.35          # the kick reaches this far inside the wall, under the main slab
BC_EAVE_OVER, BC_RAKE_OVER = 0.75, 0.75   # the blue's 0.40 and 0.50, deepened
BC_SAG = 0.05              # the ridge and eaves dip this much at mid-length
BC_CORNER = 0.30           # the corner boards (the blue's 0.26)
BC_PANE_RECESS = 0.06
BC_DOOR_X = (-0.55, 0.35)
BC_DOOR_H = 2.18           # 2.17 m clear over the threshold, for the 1.8 m capsule
BC_WINDOW_X = (-2.45, -1.10)
BC_SILL, BC_HEAD_Z = 0.58, 2.18   # the main storey's windows over the floor: taller than the blue's
BC_UP_WINDOW_X = (-0.95, 0.95)    # the triple window, wider than the blue's
BC_UP_SILL, BC_UP_HEAD = 0.65, 2.05
BC_SIDE_WIN_W = 1.10
BC_BACK_WINDOW_X = (-2.35, -1.00)
BC_BACK_UP_WINDOW_X = (-0.60, 0.60)
BC_BACK_UP_HEAD = 1.80
BC_BAND_H = 0.20
BC_PLINTH = ((-0.08, -0.075), (0.11, -0.075), (0.045, 0.42), (-0.08, 0.42))   # (out, z): it flares at the foot
BC_DECK_T = 0.24
BC_BALCONY_HW, BC_BALCONY_D, BC_BALCONY_T = 1.9, 0.80, 0.18
BC_BRACKETS_X = (-0.825, 0.675)   # two, in the gaps beside the door's casing
BC_BRACKET_W = 0.18
BC_RISERS = 8              # eight chunky risers for the blue's ten, at the blue's grade
BC_GRADE = (B_FLOOR / round(B_FLOOR / RISER_ABOUT)) / GOING
BC_STOOP_X, BC_STOOP_STAIR_W = (0.05, 1.80), 1.40   # wider, so its parapets clear the door's casing
BC_PARAPET, BC_PARAPET_CAP = 0.14, 0.20
BC_PORCH_PROUD = 0.10      # the porch's right face past the body's corner board, which the lean pushes out
BC_PORCH_EAVE = 2.10       # over the floor
BC_PORCH_POST = 0.26
BC_PORCH_ROOF_T = 0.18
BC_PORCH_RAKE = 0.40
BC_PORCH_GLASS = (0.80, 1.85)
BC_PORCH_INSET = 0.42      # the glass in from the porch's corners, so the casings clear the posts' collars
BC_BARGE_H, BC_BARGE_BAND = 0.45, 0.18   # one board, white over red
BC_FAN_Z = 2.66            # the sunburst's centre over the eave
BC_FAN_R, BC_FAN_RING = 0.80, 0.15
BC_FAN_HUB = 0.17
BC_FAN_HUB_RED = 0.30      # the red behind the hub, a third of the fan across, as the photo's
BC_COLLAR_FRIEZE = 0.16    # the red frieze under the collar, deep
BC_FAN_RAYS = (22.0, 52.0, 128.0, 158.0)   # four wedges and the king post at 90
BC_FAN_WEDGE = (7.0, 11.0)                  # a ray's half-angle at the hub and at the ring
BC_FAN_BAR = 0.15
BC_KING = 0.065            # the king post's half-width
BC_CHIMNEY = (0.65, 1.50, 0.42, 0.52)       # centre x, y and half-sizes: through the east slope
BC_SIDING = 0.24           # the painted lap siding's exposure: twice the blue's 0.12

# --- purple and purple_b, the cartoony build (PC_, PBC_) -------------------------
# (2026-10-04) The purple's house, photo, palette and lot, converted to the
# standard as the blue was, its own ideas pushed: the turned porch posts, the
# pointed hoods, the spindle-work fan and the shed porch roof. purple_b is the
# same build at the lower pitch over the knee wall, railed, with a chimney.
# The standard's sizes, the bell roof and the parapets are cartoon_kit's; each
# number's reason is beside the code that uses it.
PC_SEED, PC_SHINGLE_SEED = 20261005, 20261006
PBC_SEED, PBC_SHINGLE_SEED = 20261007, 20261008
PC_PITCH_DEG = 50.0        # the purple's 48, a touch steeper: the hoods and the fan need room under the deeper rakes
PC_STOREY = 3.24           # the purple's 3.0, taller: the shed porch roof passes under the bargeboards' bent ends
PC_WALL_TOP_IN = 0.36      # the side walls' tops inside the slab; the corner boards' tops then 4 cm under its top
PC_RISERS = 3              # three chunky risers, as the photo's, for the purple's four
PC_GRADE = (P_FLOOR / round(P_FLOOR / RISER_ABOUT)) / GOING   # at the purple's grade
PC_DOOR_H = 2.30           # 2.29 m clear over the threshold
PC_SILL, PC_HEAD = 0.68, 2.30
PC_WINDOW_LIGHTS = 2       # the photo's front window, two panes
PC_UP_WINDOWS_X = ((-1.00, -0.30), (0.30, 1.00))   # the paired windows, wider than the purple's 0.65
PC_UP_SILL, PC_UP_HEAD = 0.40, 1.55   # over the upstairs floor: the hoods' corners a third of a metre under the rakes
PC_HOOD_DEG, PC_HOOD_OVER = 35.0, 0.06   # the hoods' rake, and how far past the casing each side
PC_HOOD_CORNICE = (0.03, 0.09, 0.04)     # the cornice under and over the hood's rake, and past its ends
PC_PLINTH = ((-0.08, -0.075), (0.10, -0.075), (0.045, 0.30), (-0.08, 0.30))   # lower than the blue's, under the band
PC_DECK_OVER = 0.20        # the porch deck past the body each side
PC_POSTS_X = (-2.80, -0.95, 0.95, 2.80)
PC_POST_IN = 0.30          # the posts' centres in from the deck's front edge
PC_PEDESTAL = (0.18, 0.50)  # the turned posts' square gold base: half-size, top over the floor
PC_CAPITAL = (0.19, 0.18)   # the gold capital: half-size, how far under the beam
# the turned shaft, (radius, z): a ring, a neck, the fat belly, a neck over
# the pedestal's top (pz); a ring and a neck under the capital (cz)
PC_SHAFT_LOW = ((0.12, -0.03), (0.15, 0.04), (0.11, 0.12), (0.17, 0.36), (0.17, 0.44), (0.11, 0.64))
PC_SHAFT_HIGH = ((0.12, -0.22), (0.155, -0.16), (0.155, -0.08), (0.12, 0.03))
PC_BEAM = (2.16, 0.26)     # the porch beam's underside over the floor, and its depth
PC_BRACKET = (0.40, 0.50, 0.10)   # the posts' shaped brackets: reach, drop, thickness
PC_SHED_SLOPE = 0.16       # the shed roof's rise per metre toward the wall (9 degrees)
PC_SHED_T = 0.26           # its slab, vertical
PC_SHED_OVER = 0.50        # its eave past the beam's line
PC_SHED_END = 0.08         # its ends past the body's sides
PC_SHED_KICK = (0.16, 0.08, 0.20)   # its own kick: leaving the top this far before the beam's line, rise per metre, depth
PC_FASCIA = (0.28, 0.10)   # the shed's gold fascia along its eave, and the shaded magenta frieze under it, deep
PC_STEP_X = (-2.55, -1.20)
PC_FAN_BAR = (0.04, 0.16)  # the spindle bar: its underside over the hoods' knobs, and its depth
PC_FAN_CLEAR = 0.15        # each ray's tip this far under the rake's underside, so the fan fills the peak
PC_FAN_HUB = 0.16
PC_FAN_RAYS = (18.0, 54.0, 90.0, 126.0, 162.0)
PC_FAN_RAY = (0.055, 0.10, 0.09)    # a ray's half-widths: its shaft, its bead, its ball
PC_SPINDLES_X = (-0.30, -0.15, 0.0, 0.15, 0.30)   # 15 cm apart, so the fat beads and balls stand clear of each other
PC_SPINDLE_L = 0.34        # the middle one hangs PC_PENDANT longer, as the photo's pendant
PC_PENDANT = 0.16

PBC_KNEE = PB_KNEE         # the side walls 1.2 over the upstairs floor, so the upstairs windows straddle the eave
PBC_WALL_TOP_IN = 0.26     # inside the flatter slab (0.38 deep at 38 degrees)
PBC_UP_SILL, PBC_UP_HEAD = 0.30, 1.55   # 0.90 under the eave line and 0.35 over it, leaving the fan its room
PBC_BELT = (0.14, 0.08)    # the belt at the eave line across both gables: under the eave, over it
PBC_PEDESTAL = (0.18, 1.00)   # the railed porch's posts on rail-high pedestals, which the rails lap into
PBC_FAN_HUB = 0.20         # the room in the flatter, wider peak: a bigger hub and seven rays
PBC_FAN_RAYS = (15.0, 40.0, 65.0, 90.0, 115.0, 140.0, 165.0)
PBC_SPINDLE_L = 0.26
PBC_CHIMNEY = (0.80, 1.65, 0.42, 0.52)   # centre x, y and half-sizes: through the east slope near the ridge

# --- blue_b, the cartoony build (BBC_) -----------------------------------------------
# (2026-10-04) The cartoony blue's build with blue_b's three differences: the
# glazed porch wrapping the corner under an L-shaped lean-to, the side door's
# landing and flight on the driveway side in place of the back stoop, and the
# chimney the cartoony blue already has. Its own seeds and palette.
BBC_SEED, BBC_SHINGLE_SEED = 20261009, 20261010
BBC_SIDE_DOOR_Y = (1.10, 2.05)   # blue_b's side door, 10 cm further back, so the landing's rail clears its casing and the window's
BBC_LANDING_Y = (0.72, 2.45)     # the side landing along the wall: its front parapet's cap between the window's casing and the door's
BBC_FLIGHT_IN = 0.38             # the side flight's inner edge off the wall's line: its cap clears the window's casing, its pier the plinth
BBC_WRAP_OVER = 0.30             # the lean-to's eaves past the porch's walls, front and side
BBC_WRAP_OVER_W = 0.08           # its west end past the porch's west wall, clear of the balcony's bracket
BBC_WRAP_T = 0.22                # its slab, vertical
BBC_WRAP_SLOPE = 0.15            # the front slope's rise per metre (8.5 degrees); the side's is set so both meet at the body's corner
BBC_WRAP_CLEAR = 0.04            # the lean-to's top under the front bargeboard's bent end and the main roof's eaves, at least
BBC_WRAP_GLASS = 0.62            # the glass band's sill over the floor; its head is set under the lean-to
BBC_WRAP_INSET = 0.48            # the glass in from the porch's corners, so the casings clear the posts' collars
BBC_FASCIA = (0.10, 0.24)        # the fat fascia wrapping the lean-to's eaves: its top under the slab's, its depth

LOT_W, LOT_X0, LOT_Y = 9.0, -3.6, (-16.0, 14.0)   # the lot: 9 m wide, the kerb to the back fence

PALETTES = {
    "blue": dict(walls="a9c4d3", base="8aa7ba", trim="f6f3ec", accent="b5202c", frames="f6f3ec",
                 door="b5202c", deck="7d8a94", roof="6b6f66", glass="3e5566"),
    "purple": dict(walls="5b2e9e", base="4a2480", trim="1e8a7c", accent="c2298e", frames="d8a62a",
                   door="6a1a3a", deck="8a7a6a", roof="4a4a4c", glass="3e5566"),
}
# the b pair in their own colours (Christina, 3 Oct 2026: "on the variations
# lets change the colors", "can the doors be different colors too"): sage,
# cream and deep red with a navy door; pink, teal and gold with a sunflower door
PALETTES["blue_b"] = dict(walls="a3b899", base="86997f", trim="f3ead6", accent="8e1f24", frames="f3ead6",
                          door="1f2f5a", deck="7d8a94", roof="6b6f66", glass="3e5566", brick="8a4a3a")
PALETTES["purple_b"] = dict(walls="e8559a", base="c43f80", trim="1e8a7c", accent="d8a62a", frames="d8a62a",
                            door="f2b705", deck="8a7a6a", roof="4a4a4c", glass="3e5566", brick="7a3f36")
# the cartoony blue gains the blue_b's brick for its chimney, and the red
# under the eaves a little darker, as if in their shadow (her "the red under
# the eves can be a little darker as if its in shadpw", 2026-10-04): the
# rakes' sawn band and the collar's frieze; the door and the fan's hub, in the
# light, keep the blue's red
PALETTES["blue"].update(brick=PALETTES["blue_b"]["brick"], accent_shade="86161f")
# the converted three take the same: each one's accent a shade darker (about
# 0.72 of it, as the blue's), for its trim under the eaves
PALETTES["purple"].update(accent_shade="8e1d65")
PALETTES["purple_b"].update(accent_shade="a0781d")
PALETTES["blue_b"].update(accent_shade="691519")
VARIANTS = ("blue", "purple", "blue_b", "purple_b")


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def material(name, colour):
    """A flat stand-in by name; its colour is set every run, so a palette
    change reaches a material the file already holds."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = colour
    mat.diffuse_color = colour
    return mat


# --- building blocks ---------------------------------------------------------

class Top:
    """A wall's top edge: flat, or a gable following the roof's underside
    LIFT higher (inside the slab, so the two never share a plane)."""

    def __init__(self, flat=None, gable=None):
        self.flat = flat
        self.gable = gable      # (u of the ridge, half span, eave z, tan of the pitch)

    def z(self, u):
        if self.gable is None:
            return self.flat
        ridge_u, half, eave, tan = self.gable
        return eave + (half - abs(u - ridge_u)) * tan + LIFT

    def apex(self):
        ridge_u, half, eave, tan = self.gable
        return eave + half * tan + LIFT


class LiftedTop(Top):
    """A gable top `lift` inside the slab rather than LIFT: the cartoony blue's
    walls lean in, which carries a gable's top in across the slope, where
    the underside is higher (5 cm at most on the main gables)."""

    def __init__(self, gable, lift):
        super().__init__(gable=gable)
        self.lift = lift

    def z(self, u):
        ridge_u, half, eave, tan = self.gable
        return eave + (half - abs(u - ridge_u)) * tan + self.lift

    def apex(self):
        ridge_u, half, eave, tan = self.gable
        return eave + half * tan + self.lift


class SlopeTop(Top):
    """A wall's top running straight from z0 at u = 0 to z1 at u = length,
    inside a lean-to's slab over it (blue_b's wrapping porch); it has no
    ridge inside the wall."""

    def __init__(self, z0, z1, length):
        super().__init__(gable=(-1.0, 0.0, 0.0, 0.0))
        self.z0, self.z1, self.length = z0, z1, length

    def z(self, u):
        return self.z0 + (self.z1 - self.z0) * u / self.length

    def apex(self):
        return max(self.z0, self.z1)


class Kit:
    """One variant's parts: every maker here names, tags and colours for it."""

    def __init__(self, variant, coll, pitch_deg=PITCH_DEG, knee=0.0, wall_top_in=WALL_TOP_IN):
        self.v = variant
        self.coll = coll
        self.m = {k: material(f"{NAME}_{variant}_{k}", srgb(hex6)) for k, hex6 in PALETTES[variant].items()}
        self.pitch = math.radians(pitch_deg)
        self.tan = math.tan(self.pitch)
        self.rise = (W / 2) * self.tan
        self.roof_vt = ROOF_T / math.cos(self.pitch)
        self.knee = knee                  # the side walls over the upstairs floor
        self.wall_top_in = wall_top_in

    def finish(self, part, bm, mats, collide=True):
        name = f"{self.v}_{part}"
        mesh = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            f.smooth = False
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        for m in mats:
            mesh.materials.append(m)
        obj[TAG] = True
        obj["kyt_unwrap"] = "facets"
        obj["kyt_variant"] = self.v
        if not collide:
            obj["kyt_collision"] = "none"
        self.coll.objects.link(obj)
        return obj

    def box(self, part, mat, x0, x1, y0, y1, z0, z1, collide=True):
        """An axis-aligned box, 12 triangles."""
        assert x1 > x0 and y1 > y0 and z1 > z0, (part, x0, x1, y0, y1, z0, z1)
        bm = ck.prism_bm([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)
        return self.finish(part, bm, [mat], collide=collide)

    def prism(self, part, mat, poly, axis, lo, hi, collide=True):
        return self.finish(part, ck.prism_bm(poly, axis, lo, hi), [mat], collide=collide)

    # -- walls --

    def wall(self, part, origin, u_dir, v_dir, length, thick, z0, top, openings, base_below, mats):
        """One wall as a closed shell: two skins, ends, bottom, top, and a real
        reveal round every opening. `origin` is the outer face's start,
        `u_dir` runs along it, `v_dir` into the wall. An opening is
        (u0, u1, z0, z1), anywhere under the top, the gable included: the
        wall is a grid of cells between the opening lines, each cell clipped
        by the roof line, and a cell's edge gets a side face wherever its
        neighbour is an opening, the outside or the sky. Faces below
        `base_below` take the second material (the base)."""
        O, U, V = Vector(origin), Vector(u_dir), Vector(v_dir)
        us, zs = {0.0, length}, {z0}
        for u0, u1, oz0, oz1 in openings:
            assert 0.0 < u0 < u1 < length and z0 < oz0 < oz1, (part, u0, u1, oz0, oz1)
            if top.gable is None:
                assert oz1 <= top.flat - 0.05, (part, "an opening through the top", oz1, top.flat)
            else:
                assert oz1 + 0.03 <= min(top.z(u0), top.z(u1)), (part, "an opening through the gable", u0, u1, oz1)
            us.update((u0, u1))
            zs.update((oz0, oz1))
        if top.gable is None:
            zs.add(top.flat)
        else:
            if 0.0 < top.gable[0] < length:
                us.add(top.gable[0])
            zs.add(top.apex() + 1.0)       # a nominal top, clipped away
        us, zs = sorted(us), sorted(zs)
        nu, nz = len(us) - 1, len(zs) - 1
        bm = bmesh.new()
        verts = {}

        def vert(u, z, side):
            key = (round(u, 5), round(z, 5), side)
            if key not in verts:
                verts[key] = bm.verts.new(O + U * u + V * (thick if side else 0.0) + Vector((0.0, 0.0, z)))
            return verts[key]

        def is_open(i, j):
            um, zm = (us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            return any(u0 < um < u1 and oz0 < zm < oz1 for u0, u1, oz0, oz1 in openings)

        def clip(i, j):
            ua, ub, za, zb = us[i], us[i + 1], zs[j], zs[j + 1]
            poly = [(ua, za), (ub, za), (ub, zb), (ua, zb)]
            if top.gable is None:
                return poly
            out = []
            for k in range(4):
                p, q = poly[k], poly[(k + 1) % 4]
                fp, fq = top.z(p[0]) - p[1], top.z(q[0]) - q[1]
                if fp >= 0:
                    out.append(p)
                if (fp >= 0) != (fq >= 0):
                    t = fp / (fp - fq)
                    out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
            clean = []
            for p in out:
                if not clean or (abs(p[0] - clean[-1][0]) > 1e-6 or abs(p[1] - clean[-1][1]) > 1e-6):
                    clean.append(p)
            if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-6 and abs(clean[0][1] - clean[-1][1]) < 1e-6:
                clean.pop()
            return clean if len(clean) >= 3 else None

        solid = {(i, j): (None if is_open(i, j) else clip(i, j)) for i in range(nu) for j in range(nz)}

        def index(zm):
            return 1 if zm < base_below else 0

        for (i, j), poly in solid.items():
            if poly is None:
                continue
            zm = sum(p[1] for p in poly) / len(poly)
            f = bm.faces.new([vert(u, z, 0) for u, z in poly])
            f.material_index = index(zm)
            f = bm.faces.new([vert(u, z, 1) for u, z in reversed(poly)])
            f.material_index = index(zm)
            n = len(poly)
            for k in range(n):
                p, q = poly[k], poly[(k + 1) % n]
                eps = 1e-6
                if abs(p[0] - q[0]) < eps and abs(p[0] - us[i]) < eps:
                    nb = (i - 1, j)
                elif abs(p[0] - q[0]) < eps and abs(p[0] - us[i + 1]) < eps:
                    nb = (i + 1, j)
                elif abs(p[1] - q[1]) < eps and abs(p[1] - zs[j]) < eps:
                    nb = (i, j - 1)
                elif abs(p[1] - q[1]) < eps and abs(p[1] - zs[j + 1]) < eps:
                    nb = (i, j + 1)
                else:
                    nb = None
                if nb is not None and solid.get(nb) is not None:
                    continue        # shared with a solid neighbour
                f = bm.faces.new((vert(*p, 0), vert(*q, 0), vert(*q, 1), vert(*p, 1)))
                f.material_index = index((p[1] + q[1]) / 2)
        return self.finish(part, bm, mats)

    def shell(self, prefix, x0, x1, y0, y1, thick, e, feet, tops, openings, mats, base_below, which=("front", "back", "west", "east")):
        """Walls as closed shells round the rectangle (x0..x1, y0..y1), their
        ends lost inside the corner boards (`e` short of each corner). `feet`
        gives each wall's foot z; `tops` a Top per wall; `openings` per wall a
        list of (a0, a1, z0, z1) in world x (front, back) or world y (west,
        east) and absolute z."""
        spec = {
            "front": ((x0 + e, y0, 0.0), (1, 0, 0), (0, 1, 0), x1 - x0 - 2 * e, lambda a: a - x0 - e),
            "back": ((x1 - e, y1, 0.0), (-1, 0, 0), (0, -1, 0), x1 - x0 - 2 * e, lambda a: x1 - e - a),
            "west": ((x0, y1 - e, 0.0), (0, -1, 0), (1, 0, 0), y1 - y0 - 2 * e, lambda a: y1 - e - a),
            "east": ((x1, y0 + e, 0.0), (0, 1, 0), (-1, 0, 0), y1 - y0 - 2 * e, lambda a: a - y0 - e),
        }
        for key in which:
            origin, u_dir, v_dir, length, to_u = spec[key]
            ops = []
            for a0, a1, z0, z1 in openings.get(key, ()):
                ua, ub = sorted((to_u(a0), to_u(a1)))
                ops.append((ua, ub, z0, z1))
            self.wall(f"{prefix}wall_{key}", origin, u_dir, v_dir, length, thick, feet[key], tops[key], ops,
                      base_below, mats)

    def gable_roof(self, part, mat, xc, half, eave, tan, over, thick, y0, y1):
        """A gable roof as one piece: an inverted V of `thick` perpendicular
        thickness whose underside passes through z = eave at x = xc +- half
        and peaks over xc, extruded from rake to rake."""
        vt = thick / math.cos(math.atan(tan))

        def under(x):
            return eave + (half - abs(x - xc)) * tan
        xe = half + over
        section = [(xc - xe, under(xc - xe)), (xc, under(xc)), (xc + xe, under(xc + xe)),
                   (xc + xe, under(xc + xe) + vt), (xc, under(xc) + vt), (xc - xe, under(xc - xe) + vt)]
        return self.prism(part, mat, section, "y", y0, y1)

    # -- openings --

    def pane(self, part, mat, axis, face_at, outward, a0, a1, z0, z1, recess=0.08, thick=0.05, collide=True):
        """A slab set in an opening, recessed into the wall, 2 cm into the reveals all round."""
        lo, hi = sorted((face_at - recess * outward, face_at - (recess + thick) * outward))
        if axis == "x":
            return self.box(part, mat, a0 - 0.02, a1 + 0.02, lo, hi, z0 - 0.02, z1 + 0.02, collide=collide)
        return self.box(part, mat, lo, hi, a0 - 0.02, a1 + 0.02, z0 - 0.02, z1 + 0.02, collide=collide)

    # -- decks, rails, stairs --

    def skirt(self, part, mat, x0, x1, y0, y1, z_deck):
        """The solid base under a deck, 10 cm under the ground, its top inside the deck."""
        self.box(part, mat, x0, x1, y0, y1, -0.10, z_deck - 0.18)

    # -- ornament --

    def half_disc(self, part, mat, xc, zc, r, y_lo, y_hi, segments=12, collide=False):
        return ck.half_disc(self.finish, part, mat, xc, zc, r, y_lo, y_hi, segments=segments, collide=collide)

class Chunky(Kit):
    """A cartoony variant's maker: the Kit's parts, plus the shared cartoon
    kit's chunky ones (`cartoon_kit`) bound to this kit's finish, hand and
    the house's own heights, a warp that leans whatever is built while it is
    set (the blue's walls and everything on them), and a seeded hand for the
    irregularities. Every maker here goes through `finish`, so the warp
    leans the kit's pieces too. Its defaults are the blue's; each converted
    variant passes its own pitch, slab, seeds and stair (risers at its old
    grade), so no two houses share their irregularities."""

    def __init__(self, variant, coll, pitch_deg=BC_PITCH_DEG, slab=BC_ROOF_T, seed=BC_SEED, shingle_seed=BC_SHINGLE_SEED,
                 risers=None, grade=None, knee=0.0, wall_top_in=BC_WALL_TOP_IN):
        super().__init__(variant, coll, pitch_deg=pitch_deg, knee=knee, wall_top_in=wall_top_in)
        self.roof_vt = slab / math.cos(self.pitch)
        self.warp = None
        self.rng = random.Random(seed)
        self.shingle_seed = shingle_seed
        self.risers = BC_RISERS if risers is None else risers
        self.grade = BC_GRADE if grade is None else grade

    def jit(self, amount):
        """A seeded nudge in -amount..amount."""
        return ck.jit(self.rng, amount)

    def finish(self, part, bm, mats, collide=True):
        if self.warp is not None:
            for v in bm.verts:
                v.co = self.warp(v.co)
        return super().finish(part, bm, mats, collide=collide)

    def plate(self, part, mats, polys, axis, lo, hi, collide=True):
        return ck.plate(self.finish, part, mats, polys, axis, lo, hi, collide=collide)

    def lathe(self, part, mat, cx, cy, rings, lean=(0.0, 0.0), collide=True):
        return ck.lathe(self.finish, part, mat, cx, cy, rings, lean=lean, collide=collide)

    def swept(self, part, mat, section, stations, collide=True):
        return ck.swept(self.finish, part, mat, section, stations, collide=collide)

    def sweep(self, part, mat, path, section, closed=True, collide=True):
        return ck.sweep(self.finish, part, mat, path, section, closed=closed, collide=collide)

    def casing(self, part, mat, axis, face_at, outward, a0, a1, z0, z1, lights=1, sill=True):
        return ck.casing(self.finish, self.rng, part, mat, axis, face_at, outward, a0, a1, z0, z1, lights=lights, sill=sill)

    def newel_post(self, part, mat, cx, cy, z_floor):
        return ck.newel_post(self.finish, self.rng, part, mat, cx, cy, z_floor, rail_h=RAIL_H)

    def straight_rail(self, name, axis, at, a0, a1, open0, open1, z_floor):
        ck.straight_rail(self.finish, self.rng, name, self.m["trim"], axis, at, a0, a1, open0, open1, z_floor, rail_h=RAIL_H)

    def stair_rails(self, prefix, x_ats, y_edge, out, z_top, n, riser, going):
        ck.stair_rails(self.finish, self.rng, prefix, self.m["trim"], x_ats, y_edge, out, z_top, n, riser, going, rail_h=RAIL_H)

    def flight(self, prefix, mat, x0, x1, y_edge, out, z_top):
        """The variant's flight in its few chunky risers at its old grade (the
        blue's BC_RISERS at the blue's)."""
        return ck.flight(self.finish, prefix, mat, x0, x1, y_edge, out, z_top, self.risers, self.grade, BELOW)

    def bell_roof(self, xc, half, eave, slab, y0, y1, **kw):
        return ck.bell_roof(self.finish, self.m["roof"], xc, half, eave, self.pitch, slab, y0, y1, **kw)

    def shaped_bracket(self, part, mat, axis, at, face, out, z_top, reach, drop, **kw):
        return ck.shaped_bracket(self.finish, self.rng, part, mat, axis, at, face, out, z_top, reach, drop, **kw)

    def timber_post(self, part, mat, cx, cy, z_foot, base, z_eave, z_top, **kw):
        return ck.timber_post(self.finish, self.rng, part, mat, cx, cy, z_foot, base, z_eave, z_top, **kw)

    def stoop_parapets(self, prefix, x_ats, y_edge, out, z_floor, n, riser, going, s_wall):
        ck.stoop_parapets(self.finish, self.rng, prefix, self.m["trim"], x_ats, y_edge, out, z_floor, n, riser, going, s_wall,
                          rail_h=RAIL_H, width=BC_PARAPET, cap_w=BC_PARAPET_CAP)

    def barge(self, part, profile, knees, r_end, xc, y_rake, out, board, band, pendants, band_mat=None):
        """White over the photo's sawn red band, in the shaded red unless
        `band_mat` says otherwise (the porch's gable, plain white in the
        photo)."""
        band_mat = band_mat or self.m["accent_shade"]
        return ck.barge(self.finish, self.rng, part, [self.m["trim"], band_mat], profile, knees, r_end, xc, y_rake, out,
                        board, band, pendants)


# --- the house -----------------------------------------------------------------



# --- blue, the cartoony build --------------------------------------------------------

def body_warp(eave):
    """The cartoon's lean as a warp of what is built on the body: at height z
    every face of the footprint has come in by (z - eave) * tan(BC_LEAN_DEG),
    so the walls stand wider than the blue's below the eave and narrower
    above, while the eave line, where the roof sits, is the blue's footprint.
    Planes stay planes and level faces stay level: the walls become tapered
    shells and every casing, pane and board on them follows the face, with
    nothing tilted."""
    k = math.tan(math.radians(BC_LEAN_DEG))
    hw, hd = W / 2, D / 2

    def warp(co):
        d = (co.z - eave) * k
        return Vector((co.x * (1 - d / hw), co.y * (1 - d / hd), co.z))
    return warp


def porch_warp(x0, x1, y_front, y_back, eave):
    """The glazed porch's own lean about its eave: its sides come in toward
    its middle and its front leans back, while its back, inside the body's
    front wall, stays put."""
    k = math.tan(math.radians(BC_LEAN_DEG))
    xc, half = (x0 + x1) / 2, (x1 - x0) / 2

    def warp(co):
        d = (co.z - eave) * k
        return Vector((xc + (co.x - xc) * (1 - d / half), co.y + d * (y_back - co.y) / (y_back - y_front), co.z))
    return warp


def cartoon_body(kit, floor, eave, openings, doors, lights, gable_lift=BC_GABLE_LIFT, wall_top_in=BC_WALL_TOP_IN):
    """A cartoony body on the shared 6 x 10.5 footprint: the four walls as
    shells with gables front and back (their tops `gable_lift` inside the
    slab, the sides' `wall_top_in` over the eave), the fat corner boards each
    sheared up to a centimetre off plumb, a single-piece casing round every
    opening (`lights` across, by (face, index)) and its pane or door leaf.
    `doors` names the doors, as (face, index); `openings` per face, as the
    shell takes them. Whatever warp the kit holds leans all of it."""
    hw, hd = W / 2, D / 2
    m, j = kit.m, kit.jit
    e = BC_CORNER / 2 - PROUD
    gable = LiftedTop(gable=(hw - e, hw, eave, kit.tan), lift=gable_lift)
    flat = Top(flat=eave + wall_top_in)
    kit.shell("", -hw, hw, -hd, hd, T, e, {"front": -BELOW, "back": -BELOW, "west": -BELOW - 0.01, "east": -BELOW - 0.01},
              {"front": gable, "back": gable, "west": flat, "east": flat}, openings, [m["walls"], m["base"]], floor)
    # the corner boards, 0.30 square, each sheared up to a centimetre off plumb
    zb, zt = -BELOW - 0.03, eave + wall_top_in + 0.02
    for sx, sy, tag in ((-1, -1, "sw"), (1, -1, "se"), (-1, 1, "nw"), (1, 1, "ne")):
        h = BC_CORNER / 2
        kit.lathe(f"corner_{tag}", m["trim"], sx * (hw + PROUD - h), sy * (hd + PROUD - h), [(h, h, zb), (h, h, zt)],
                  lean=(j(0.01) / (zt - zb), j(0.01) / (zt - zb)))
    for face, axis, at, out in (("front", "x", -hd, -1), ("back", "x", hd, 1), ("west", "y", -hw, -1), ("east", "y", hw, 1)):
        for k, (a0, a1, z0, z1) in enumerate(openings[face]):
            door = (face, k) in doors
            kit.casing(f"{face}{k}_casing", m["frames"], axis, at, out, a0, a1, z0, z1, lights=lights.get((face, k), 1), sill=not door)
            kit.pane(f"{face}{k}_{'door' if door else 'pane'}", m["door"] if door else m["glass"], axis, at, out, a0, a1, z0, z1,
                     recess=BC_PANE_RECESS)


def fat_chimney(kit, cx, cy, hx, hy, rt, z_base):
    """A fat brick chimney (hx, hy its half-sizes) through a slope, from
    z_base inside the attic: stepping in once over the ridge's height (rt)
    and capped, its steps a little uneven and the stack a touch off plumb."""
    j = kit.jit
    zs, zt = rt - 0.10 + j(0.04), rt + 0.55 + j(0.04)
    inset = 0.06 + j(0.012)
    kit.lathe("chimney", kit.m["brick"], cx, cy,
              [(hx, hy, z_base), (hx, hy, zs), (hx - inset, hy - inset, zs + 0.08 + j(0.02)), (hx - inset, hy - inset, zt),
               (hx + 0.05, hy + 0.05, zt), (hx + 0.05, hy + 0.05, zt + 0.14 + j(0.02)), (hx - 0.02, hy - 0.02, zt + 0.19)],
              lean=(j(0.012), j(0.012)))


def sunburst(kit, eave, y_rake, rt):
    """The peak's sunburst, pushed: a bold gable truss across the rake under
    the bargeboards, where the deeper rake no longer hides it. A white star
    (the base bar, its ends 3 cm up in the slab's underside behind the
    bargeboards, a hub, four fat wedge rays and the king post rising through
    the ridge to a finial) over a white ring and a red half-disc, three
    pieces in place of the blue's ten. The rays differ a little in angle,
    width and reach, as sawn by hand."""
    j, rng = kit.jit, kit.rng
    m = kit.m
    zc = eave + BC_FAN_Z
    R, Rin, hub, K = BC_FAN_R, BC_FAN_R - BC_FAN_RING, BC_FAN_HUB, BC_KING

    def x_at(z):            # where the roof's underside is 3 cm under z
        return W / 2 - (z - 0.03 - eave) / kit.tan

    def pol(r, deg):
        return (r * math.cos(math.radians(deg)), zc + r * math.sin(math.radians(deg)))
    rays = []
    for th in BC_FAN_RAYS:
        rays.append((th + j(2.5), BC_FAN_WEDGE[0] + j(1.0), BC_FAN_WEDGE[1] + j(1.5), Rin + 0.02 + rng.uniform(0.0, 0.04)))
    king = math.degrees(math.acos(K / hub))
    hub_pts = {d: pol(hub, d) for d in {t - a for t, a, b, r in rays} | {t + a for t, a, b, r in rays}}
    hub_pts[0.0], hub_pts[180.0] = (hub, zc), (-hub, zc)
    zk = zc + math.sqrt(hub * hub - K * K)
    hub_pts[king], hub_pts[180.0 - king] = (K, zk), (-K, zk)
    bar0 = zc - BC_FAN_BAR
    base = [(-x_at(bar0), bar0), (x_at(bar0), bar0), (x_at(zc), zc)] + [hub_pts[d] for d in sorted(hub_pts)] + [(-x_at(zc), zc)]
    polys = [(base, 0)]
    for t, a, b, r in rays:
        polys.append(([hub_pts[t - a], pol(r, t - b), pol(r, t + b), hub_pts[t + a]], 0))
    z_post = rt + 0.10
    polys.append(([(K, zk), (K, z_post), (-K, z_post), (-K, zk)], 0))
    fw = 0.12 + j(0.01)
    polys.append(([(K, z_post), (fw, z_post + 0.08), (j(0.015), z_post + 0.27 + j(0.02)), (-fw, z_post + 0.08), (-K, z_post)], 0))
    kit.plate("fan_star", [m["trim"]], polys, "y", y_rake + 0.03, y_rake + 0.10, collide=False)
    steps = [180.0 * k / 8 for k in range(9)]
    ring = [([pol(Rin, a), pol(R, a), pol(R, b), pol(Rin, b)], 0) for a, b in zip(steps, steps[1:])]
    ring += [([(Rin, zc - 0.05), (R, zc - 0.05), (R, zc), (Rin, zc)], 0),
             ([(-R, zc - 0.05), (-Rin, zc - 0.05), (-Rin, zc), (-R, zc)], 0)]
    kit.plate("fan_ring", [m["trim"]], ring, "y", y_rake + 0.05, y_rake + 0.12, collide=False)
    # the photo's red is only the hub, a third of the fan across; the wall
    # shows between the rays
    rd = BC_FAN_HUB_RED
    disc = [(-rd, zc - 0.06), (rd, zc - 0.06)] + [pol(rd, 180.0 * k / 8) for k in range(9)]
    kit.prism("fan_disc", m["accent"], disc, "y", y_rake + 0.07, y_rake + 0.14, collide=False)
    # the photo's sawn red frieze under the collar, rake to rake, in the
    # shaded red: its top 2 cm up inside the base bar, its ends 3 cm up in the
    # roof's underside (4.5), three big drops from its lower edge
    zt, zb = bar0 + 0.02, bar0 - BC_COLLAR_FRIEZE

    def x_in(z):            # 4.5 cm up in the underside, so its ends miss the bar's
        return x_at(z - 0.015)
    polys = [([(-x_in(zb), zb), (x_in(zb), zb), (x_in(zt), zt), (-x_in(zt), zt)], 0)]
    for f in (-0.55, 0.0, 0.55):
        c, half, d = f * x_in(zb) + j(0.04), 0.15 + j(0.02), 0.26 + j(0.04)
        polys.append(([(c - half, zb), (c + half, zb), (c + half - 0.04, zb - 0.40 * d), (c + 0.06, zb - 0.66 * d),
                       (c, zb - d), (c - 0.06, zb - 0.66 * d), (c - half + 0.04, zb - 0.40 * d)][::-1], 0))
    kit.plate("collar_frieze", [m["accent_shade"]], polys, "y", y_rake + 0.04, y_rake + 0.09, collide=False)


def gable_porch_top(floor):
    """The blue's porch gable roof's top: (p_xc, p_half, p_top(r)), r from its
    ridge line, for the porch itself and for the balcony bracket that rests
    on it."""
    hw = W / 2
    px0, px1 = B_PORCH_X0, hw + BC_PORCH_PROUD
    p_eave = floor + BC_PORCH_EAVE
    p_tan = math.tan(B_PORCH_PITCH)
    p_half, p_xc = (px1 - px0) / 2, (px0 + px1) / 2
    p_vt = BC_PORCH_ROOF_T / math.cos(B_PORCH_PITCH)
    prt = p_eave + p_half * p_tan + p_vt

    def p_top(r):
        return prt - r * p_tan
    return p_xc, p_half, p_top


def gable_porch(kit, floor):
    """The blue's glazed porch at the right-front corner and its little gable,
    leaning on its own (`porch_warp`); returns what the landing and its
    clusters need."""
    hw, hd = W / 2, D / 2
    m = kit.m
    trim, frames, glass, base, roof = (m[k] for k in ("trim", "frames", "glass", "base", "roof"))
    px0, px1 = B_PORCH_X0, hw + BC_PORCH_PROUD
    py0 = -hd - B_PORCH_D
    pe = BC_PORCH_POST / 2 - PROUD
    p_eave = floor + BC_PORCH_EAVE
    p_tan = math.tan(B_PORCH_PITCH)
    p_half, p_xc = (px1 - px0) / 2, (px0 + px1) / 2
    p_vt = BC_PORCH_ROOF_T / math.cos(B_PORCH_PITCH)
    g0, g1 = floor + BC_PORCH_GLASS[0], floor + BC_PORCH_GLASS[1]
    ins = BC_PORCH_INSET
    p_open = {"front": [(px0 + ins, px1 - ins, g0, g1)], "east": [(py0 + ins, -hd - 0.30, g0, g1)],
              "west": [(py0 + ins, py0 + ins + 0.62, g0, g1)]}
    kit.warp = porch_warp(px0, px1, py0, -hd + 0.10, p_eave)
    kit.shell("porch_", px0, px1, py0, -hd + 0.02 + pe, B_PORCH_T, pe,
              {"front": -BELOW + 0.005, "west": -BELOW - 0.015, "east": -BELOW - 0.015},
              {"front": LiftedTop(gable=(p_half - pe, p_half, p_eave, p_tan), lift=0.06),
               "west": Top(flat=p_eave + 0.14), "east": Top(flat=p_eave + 0.14)},
              p_open, [m["walls"], base], floor, which=("front", "west", "east"))
    # timber posts at its front corners: a base block over the plinth, a
    # collar under the eave, the shaft on up into the slab
    for tag, sx in (("sw", -1), ("se", 1)):
        pcx = (px0 - PROUD + BC_PORCH_POST / 2) if sx < 0 else (px1 + PROUD - BC_PORCH_POST / 2)
        pcy = py0 - PROUD + BC_PORCH_POST / 2
        kit.timber_post(f"porch_post_{tag}", trim, pcx, pcy, -BELOW - 0.045, (0.55, 0.62), p_eave, p_eave + 0.185,
                        size=BC_PORCH_POST)
    for face, axis, at, out in (("front", "x", py0, -1), ("west", "y", px0, -1), ("east", "y", px1, 1)):
        for k, (a0, a1, z0, z1) in enumerate(p_open[face]):
            kit.casing(f"porch_{face}{k}_casing", frames, axis, at, out, a0, a1, z0, z1, lights=3 if face == "front" else 1)
            kit.pane(f"porch_{face}{k}_pane", glass, axis, at, out, a0, a1, z0, z1, recess=BC_PANE_RECESS)
    kit.sweep("porch_plinth", base, [(px0, -hd + 0.06), (px0, py0), (px1, py0), (px1, -hd + 0.06)],
              ((-0.06, -0.09), (0.10, -0.09), (0.04, 0.40), (-0.06, 0.40)), closed=False)
    kit.warp = None
    kit.gable_roof("porch_roof", roof, p_xc, p_half, p_eave, p_tan, 0.25, BC_PORCH_ROOF_T, py0 - BC_PORCH_RAKE, -hd + 0.045)
    _, _, p_top = gable_porch_top(floor)
    prt = p_top(0.0)
    ph = 0.15
    kit.swept("porch_ridge_cap", roof, [(p_xc - ph, p_top(ph) - 0.03), (p_xc, prt - 0.03), (p_xc + ph, p_top(ph) - 0.03),
                                        (p_xc + ph, p_top(ph) + 0.06), (p_xc, prt + 0.07), (p_xc - ph, p_top(ph) + 0.06)],
              [(py0 - BC_PORCH_RAKE - 0.02, 0.0), (-hd + 0.04, 0.0)], collide=False)
    kit.barge("porch_barge", p_top, [], p_half + 0.30, p_xc, py0 - BC_PORCH_RAKE, -1, 0.26, 0.10, (), band_mat=trim)
    return px0, py0, p_xc, p_half, p_top


def back_stoop(kit, floor):
    """The blue's back stoop: a deck, a wider flight, solid parapets with fat
    caps (the back is not in the photograph: one plain piece a side), piers
    at the foot. Returns the flight's (n, riser, going)."""
    hd = D / 2
    m = kit.m
    deck, base = m["deck"], m["base"]
    x0, x1 = BC_STOOP_X
    y_edge = hd + STOOP_D
    kit.box("stoop_deck", deck, x0, x1, hd - 0.06, y_edge, floor - BC_DECK_T, floor)
    kit.skirt("stoop_skirt", base, x0 + 0.08, x1 - 0.08, hd - 0.04, y_edge - 0.08, floor)
    scx = (x0 + x1) / 2
    ssx0, ssx1 = scx - BC_STOOP_STAIR_W / 2, scx + BC_STOOP_STAIR_W / 2
    n, riser, going = kit.flight("stoop_stair", deck, ssx0, ssx1, y_edge, 1, floor)
    kit.stoop_parapets("stoop", (("w", ssx0 - 0.05), ("e", ssx1 + 0.05)), y_edge, 1, floor, n, riser, going, -(STOOP_D + 0.05))
    return n, riser, going


def build_blue_cartoon(kit, b=False):
    """`blue`, the cartoony build, and with `b` `blue_b`, the same build with
    its porch round the corner, a side door and flight in place of the back
    stoop: see the module docstring. The blue's statements and the order of
    its draws are untouched; blue_b's differences branch off them."""
    floor = B_FLOOR
    hw, hd = W / 2, D / 2
    eave = floor + BC_STOREY
    m = kit.m
    trim, accent, frames, glass, deck, base, roof = (m[k] for k in ("trim", "accent", "frames", "glass", "deck", "base", "roof"))
    j, rng = kit.jit, kit.rng

    # -- the body, leaning in: walls, corner boards, casings, panes, band, plinth
    kit.warp = body_warp(eave)
    sill, head = floor + BC_SILL, floor + BC_HEAD_Z
    front = [(*BC_DOOR_X, floor + THRESHOLD, floor + BC_DOOR_H), (*BC_WINDOW_X, sill, head),
             (*BC_UP_WINDOW_X, eave + BC_UP_SILL, eave + BC_UP_HEAD)]
    sides = [(c - BC_SIDE_WIN_W / 2, c + BC_SIDE_WIN_W / 2, sill, head) for c in SIDE_WINDOWS]
    back = [(*BC_BACK_WINDOW_X, sill, head), (*BACK_DOOR_X, floor + THRESHOLD, floor + BC_DOOR_H),
            (*BC_BACK_UP_WINDOW_X, eave + BC_UP_SILL, eave + BC_BACK_UP_HEAD)]
    openings = {"front": front, "back": back, "west": sides, "east": list(sides)}
    doors = {("front", 0), ("back", 1)}
    if b:
        # blue_b: no back door; the side door on the driveway side, between the
        # side windows; the front side window is inside the wrapping porch (its
        # head would stand over the lean-to), so it goes
        del back[1]
        openings["east"] = sides[1:] + [(*BBC_SIDE_DOOR_Y, floor + THRESHOLD, floor + BC_DOOR_H)]
        doors = {("front", 0), ("east", len(sides) - 1)}
    lights = {("front", 1): 2, ("front", 2): 3}
    cartoon_body(kit, floor, eave, openings, doors, lights)
    # the door's fan light, a centimetre proud of the leaf
    kit.half_disc("door_fanlight", glass, sum(BC_DOOR_X) / 2, floor + BC_DOOR_H - 0.42, 0.28, -hd + 0.05, -hd + 0.08, segments=6)
    # the water table at the floor line, chunkier, clear of the stoop
    bx, by = hw - BC_CORNER + PROUD + 0.02, hd - BC_CORNER + PROUD + 0.02
    bz0, bz1 = floor - BC_BAND_H / 2, floor + BC_BAND_H / 2
    if not b:
        kit.box("band_back0", trim, -bx, BC_STOOP_X[0] - 0.06, hd - 0.01, hd + 0.03, bz0, bz1, collide=False)
        kit.box("band_back1", trim, BC_STOOP_X[1] + 0.06, bx, hd - 0.01, hd + 0.03, bz0, bz1, collide=False)
        kit.box("band_west", trim, -hw - 0.03, -hw + 0.01, -by, by, bz0, bz1, collide=False)
        kit.box("band_east", trim, hw - 0.01, hw + 0.03, -by, by, bz0, bz1, collide=False)
    else:
        # blue_b's: whole across the back, the east clear of the porch's back wall and the side landing
        ly0, ly1 = BBC_LANDING_Y
        kit.box("band_back", trim, -bx, bx, hd - 0.01, hd + 0.03, bz0, bz1, collide=False)
        kit.box("band_west", trim, -hw - 0.03, -hw + 0.01, -by, by, bz0, bz1, collide=False)
        kit.box("band_east0", trim, hw - 0.01, hw + 0.03, -hd + BB_SIDE_D + 0.06, ly0 - 0.06, bz0, bz1, collide=False)
        kit.box("band_east1", trim, hw - 0.01, hw + 0.03, ly1 + 0.06, by, bz0, bz1, collide=False)
        # (blue_b's hood board over the side door went to the triangle budget:
        # under the 0.75 m eave the casing's fat head does its work)
    # a chunky plinth round the foot, flaring 7 cm outward to the ground: the
    # wide base the lean starts from
    kit.sweep("plinth", base, [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)], BC_PLINTH)
    # the knee brackets at the front gable's lower corners, under the rakes,
    # white as the photo's trim is (they were the blue's red)
    for tag, sx in (("w", -1), ("e", 1)):
        run = 0.62 + j(0.03)
        if tag == "e" and not b:
            # the glazed porch's little gable fills this corner and its roof
            # ran through the bracket (her "fix the bracket on the blue",
            # 2026-10-04); the draw stays, so nothing after it moves
            continue
        xo, xi = sx * (hw - 0.10), sx * (hw - 0.10 - run)
        poly = [(xi, eave + 0.06), (xo, eave + 0.06), (xi, eave + 0.06 + run * kit.tan)]
        kit.prism(f"gable_bracket_{tag}", trim, poly, "y", -hd - 0.07, -hd + 0.02, collide=False)
    kit.warp = None

    # -- the roof, the heavy part (cartoon_kit's bell roof): a 0.30 slab at
    # 55 degrees, a bell-cast kick of 27 lapped under it to a 0.75 eave, a
    # 0.75 rake, a 5 cm sag at mid-length, a ridge roll on the slopes
    y0, y1 = -hd - BC_RAKE_OVER, hd + BC_RAKE_OVER
    br = kit.bell_roof(0.0, hw, eave, BC_ROOF_T, y0, y1, sag=BC_SAG, kick_at=BC_KICK_AT, kick_deg=BC_KICK_DEG,
                       kick_t=BC_KICK_T, kick_in=BC_KICK_IN, eave_over=BC_EAVE_OVER)
    x_k, x_out, rt = br.r_k, br.r_out, br.rt
    # two big drops down each rake, as the photo's, front and back
    for face, y_rake, out in (("front", y0, -1), ("back", y1, 1)):
        kit.barge(f"barge_{face}", br.profile, [x_k], x_out + 0.05, 0.0, y_rake, out, BC_BARGE_H, BC_BARGE_BAND, (0.42, 0.76))
    sunburst(kit, eave, y0, rt)
    # a fat brick chimney through the east slope, stepping in once over the
    # ridge's height and capped, its steps a little uneven and the stack a
    # touch off plumb
    cx, cy, hx, hy = BC_CHIMNEY
    fat_chimney(kit, cx, cy, hx, hy, rt, eave + 2.0)

    # -- the balcony on the eave line: the plate, two big shaped brackets,
    # fat newels, square balusters under a fat sagging rail
    by0 = -hd - BC_BALCONY_D
    bx1 = BC_BALCONY_HW
    if not b:
        # on the blue it stops where the porch gable's roof rises under it,
        # the roof 5 cm under its plate there, as the photo's balcony stops
        # where its porch begins (her "end the balcony at the porch",
        # 2026-10-04; the roof came up 0.35 m through its east end)
        p_xc, _, p_top = gable_porch_top(floor)
        bx1 = p_xc - (p_top(0.0) - (eave - BC_BALCONY_T - 0.05)) / math.tan(B_PORCH_PITCH)
    kit.box("balcony", deck, -BC_BALCONY_HW, bx1, by0, -hd + 0.06, eave - BC_BALCONY_T, eave)
    for k, x in enumerate(BC_BRACKETS_X):
        # a knee bracket with a cove sawn out of its face and a short drop at
        # its foot, each one a little different (cartoon_kit's shaped bracket)
        z_top = eave - BC_BALCONY_T + 0.02
        if not b and x + BC_BRACKET_W / 2 > B_PORCH_X0 - 0.25:
            # on the blue the right one stands over the porch gable's roof,
            # which it ran through: it rests on the roof instead, short and
            # chunky, its foot 6 cm into the slab at its high (ridge) side
            # so the hand's drop of up to 5 cm never lifts it off
            p_xc, _, p_top = gable_porch_top(floor)
            drop = z_top - p_top(p_xc - (x + BC_BRACKET_W / 2 + 0.02)) + 0.06
            kit.shaped_bracket(f"balcony_bracket_{k}", trim, "y", x, -hd, -1, z_top, BC_BALCONY_D - 0.16, drop,
                               width=BC_BRACKET_W, foot=0.09, band=0.09)
            continue
        kit.shaped_bracket(f"balcony_bracket_{k}", trim, "y", x, -hd, -1, z_top, BC_BALCONY_D - 0.16, 0.88,
                           width=BC_BRACKET_W)
    xw = -(BC_BALCONY_HW - 0.03 - ck.NEWEL / 2)
    xe = bx1 - 0.03 - ck.NEWEL / 2
    ny = by0 + 0.045 + ck.NEWEL / 2
    for tag, x in (("w", xw), ("e", xe)):
        kit.newel_post(f"balcony_newel_{tag}", trim, x, ny, eave)
    kit.straight_rail("balcony_rail_front", "x", ny, xw + 0.055, xe - 0.055, xw + ck.NEWEL / 2, xe - ck.NEWEL / 2, eave)
    for tag, x in (("w", xw), ("e", xe)):
        kit.straight_rail(f"balcony_rail_{tag}", "y", x, ny + 0.055, -hd + 0.08, ny + ck.NEWEL / 2, -hd, eave)

    # -- the porch: the blue's glazed porch and its little gable; blue_b's
    # wrapping the corner under an L-shaped lean-to
    if b:
        wrap = wrap_porch(kit, floor, br)
        px0 = B_PORCH_X0
    else:
        px0, py0, p_xc, p_half, p_top = gable_porch(kit, floor)

    # -- the entry landing, its flight and railings
    lx0, lx1 = -hw - 0.14, px0 + 0.08
    ly0 = -hd - B_LANDING_D
    kit.box("landing", deck, lx0, lx1, ly0, -hd + 0.06, floor - BC_DECK_T, floor)
    kit.skirt("landing_skirt", base, -hw + 0.04, px0 + 0.06, ly0 + 0.10, -hd + 0.04, floor)
    dx = sum(BC_DOOR_X) / 2
    sx0, sx1 = dx - STAIR_W / 2, dx + STAIR_W / 2
    n, riser, going = kit.flight("stair", deck, sx0, sx1, ly0, -1, floor)
    xw, xe = sx0 - 0.03, sx1 + 0.03       # the stringers lap 2 cm over the treads' ends
    kit.stair_rails("stair_rail", (("w", xw), ("e", xe)), ly0, -1, floor, n, riser, going)
    lnx, lny = lx0 + 0.03 + ck.NEWEL / 2, ly0 + 0.03 + ck.NEWEL / 2
    kit.newel_post("landing_newel_w", trim, lnx, lny, floor)
    kit.straight_rail("landing_rail_w", "y", lnx, lny + 0.055, -hd + 0.08, lny + ck.NEWEL / 2, -hd - PROUD, floor)
    kit.straight_rail("landing_rail_fw", "x", lny, lnx + 0.055, xw - 0.055, lnx + ck.NEWEL / 2, xw - ck.NEWEL / 2, floor)
    kit.straight_rail("landing_rail_fe", "x", lny, xe + 0.055, px0 + 0.03, xe + ck.NEWEL / 2, px0 - PROUD, floor)

    # -- the blue's back stoop; blue_b's side door's landing and flight in its place
    n, riser, going = side_stoop(kit, floor) if b else back_stoop(kit, floor)

    # -- shingle clusters on the roof, as the hedges' leaf clusters: a few
    # small patches lying almost flat, scattered, never banded, different on
    # each slope; the slab under them stays the painted surface, and each tab
    # is one of its painted shingles lifting (cartoon_kit's shingle grid).
    # They draw from a seed of their own (her "yes give the clusters their own
    # seed", 2026-10-04), so changing the trim's hand no longer reshuffles the roof
    trim_rng = kit.rng
    rng = kit.rng = random.Random(kit.shingle_seed)
    bm = bmesh.new()
    # on each main slope a cluster at a rake, one on the kick and three
    # scattered, clear of the chimney (cartoon_kit's roof_clusters)
    tabs, mains = ck.roof_clusters(rng, bm, br, avoid={1: [(cx - hx - 0.25, cx + hx + 0.25, cy - hy - 0.25, cy + hy + 0.25)]})
    if not b:
        # one small cluster on each slope of the porch's gable, at its front, clear of the balcony
        for s in (1, -1):
            porch = dict(s=s, xc=p_xc, theta=B_PORCH_PITCH, surf=lambda r, y: p_top(r),
                         r=(0.20, p_half + 0.25), y=(py0 - BC_PORCH_RAKE + 0.03, -hd - 0.85))
            tabs += ck.shingle_cluster(rng, bm, porch, rng.uniform(0.45, p_half - 0.15), rng.uniform(py0 - 0.10, py0 + 0.25), max_courses=2)
    # (blue_b's lean-to, at 8 and 10 degrees under the main eave, shows its
    # top to no one standing; its clusters went to the triangle budget)
    kit.finish("roof_shingles", bm, [roof], collide=False)

    # a few little vent pipes on the back half of the roof (her "you can add
    # a few more little vent tubes to the roof", 2026-10-04): two on the west
    # slope, one on the east clear of the chimney, each clear of every lifted
    # shingle; drawn after the clusters, so they never move them
    vents = ck.roof_vents(kit.finish, rng, [m["deck"], m["glass"]], br, mains)
    kit.rng = trim_rng
    extra = (f"; lean-to eave {wrap['z_e']:.2f} ({wrap['z_e'] - floor:.2f} over the floor), slopes "
             f"{math.degrees(math.atan(wrap['s_f'])):.1f} and {math.degrees(math.atan(wrap['s_s'])):.1f} deg; side door at y "
             f"{BBC_SIDE_DOOR_Y[0]:.2f}..{BBC_SIDE_DOOR_Y[1]:.2f}" if b else "")
    return dict(pitch=BC_PITCH_DEG, floor=floor, storey=BC_STOREY, eave=eave, rt=rt, kick=BC_KICK_DEG, lean=True,
                door_clear=BC_DOOR_H - THRESHOLD, tabs=tabs, vents=vents, risers=n, riser=riser, going=going, extra=extra)


# --- purple and purple_b, the cartoony build ---------------------------------------------

def pointed_hood(kit, prefix, a0, a1, z_head):
    """A pointed hood over a front-wall window, pushed: a gold tympanum on the
    casing's head (2 cm down into it), PC_HOOD_OVER wider than the casing each
    side, rising at PC_HOOD_DEG to its point, 8 cm proud; a fat teal cornice
    along both rakes, lapped 3 cm over the tympanum's edge, standing 9 cm
    over it and 6 cm prouder, its ends 4 cm past; a square knob on the point.
    The point sits a hair off centre and each is a centimetre different."""
    hd = D / 2
    m, j = kit.m, kit.jit
    t = math.tan(math.radians(PC_HOOD_DEG))
    xl, xr = a0 - 0.02 - ck.CASING - PC_HOOD_OVER, a1 + 0.02 + ck.CASING + PC_HOOD_OVER
    xc = (a0 + a1) / 2 + j(0.012)
    zb = z_head - 0.02 + ck.CASING_HEAD - 0.02
    tip = zb + (xr - xl) / 2 * t + j(0.015)
    kit.prism(f"{prefix}_hood", m["frames"], [(xl, zb), (xr, zb), (xc, tip)], "y", -hd - 0.08, -hd + 0.02, collide=False)
    under, over, past = PC_HOOD_CORNICE

    def edge(x):                      # the tympanum's raking edge
        return zb + (x - xl) * (tip - zb) / (xc - xl) if x <= xc else zb + (xr - x) * (tip - zb) / (xr - xc)
    xa, xb = xl - past, xr + past
    kit.plate(f"{prefix}_hood_cornice", [m["trim"]],
              [([(xa, edge(xa) - under), (xc, tip - under), (xc, tip + over), (xa, edge(xa) + over)], 0),
               ([(xc, tip - under), (xb, edge(xb) - under), (xb, edge(xb) + over), (xc, tip + over)], 0)],
              "y", -hd - 0.14, -hd - 0.05, collide=False)
    kit.lathe(f"{prefix}_hood_knob", m["frames"], xc, -hd - 0.095,
              [(0.035, 0.035, tip + over - 0.04), (0.065, 0.065, tip + over + 0.03), (0.065, 0.065, tip + over + 0.07 + j(0.01)),
               (0.02, 0.02, tip + over + 0.15 + j(0.015))], collide=False)
    return tip + over + 0.17          # over the knob's point


def spindle_fan(kit, eave, z_bar, hub_r, rays, spindles_x, spindle_l, panel):
    """The purple's spindle-work fan in the peak, pushed: on the gable wall,
    where the deeper rake still shows it, a fat teal bar across the gable
    (its ends 3 cm up in the slab's underside), a dark panel (`panel`: the
    purple's shaded magenta; purple_b's accent is its rays' gold, so its deep
    pink) filling the peak over it, a fan of fat gold rays round a gold hub,
    each shaped as a turned spindle in silhouette (a bead and a ball) and
    reaching to PC_FAN_CLEAR under the rake above it, so the fan fills the
    peak as the photo's slats do, the middle ray the longest and the panel
    showing between them; and fat turned gold spindles hanging under the bar,
    the middle one a long pendant. Rays, beads and lengths differ a little,
    as turned and sawn by hand."""
    hw, hd = W / 2, D / 2
    m, j = kit.m, kit.jit
    zb0, zb1 = z_bar, z_bar + PC_FAN_BAR[1]

    def x_under(z):         # where the slab's underside is at z, over the wall's face
        return hw - (z - eave) / kit.tan
    xb = x_under(zb1 - 0.03)
    kit.box("fan_bar", m["trim"], -xb, xb, -hd - 0.10, -hd + 0.02, zb0, zb1, collide=False)
    zp = zb1 - 0.02
    xp = x_under(zp - 0.03)
    apex = eave + hw * kit.tan
    kit.prism("fan_panel", panel, [(-xp, zp), (xp, zp), (0.0, apex + 0.03)], "y", -hd - 0.03, -hd + 0.015, collide=False)
    # the rays: along each, (r, half-width) as a spindle's silhouette from
    # inside the hub out, a bead two fifths of the way and a ball near the tip
    zc = zb1 - 0.01
    sw, bw, kw = PC_FAN_RAY
    polys = []
    for deg in rays:
        a = math.radians(deg + j(1.5))
        dx, dz = math.cos(a), math.sin(a)
        R = (apex - PC_FAN_CLEAR - zc) / (dz + abs(dx) * kit.tan) + j(0.02)
        prof = [(hub_r - 0.03, sw), (0.33 * R, sw), (0.42 * R, bw + j(0.008)), (0.51 * R, sw),
                (0.76 * R, sw), (0.86 * R, kw + j(0.008)), (R, 0.0)]
        pts = [((r * dx - w * dz, zc + r * dz + w * dx), (r * dx + w * dz, zc + r * dz - w * dx)) for r, w in prof]
        for (l0, r0), (l1, r1) in zip(pts, pts[1:]):
            polys.append(([l0, r0, r1] if r1 == l1 else [l0, r0, r1, l1], 0))
    kit.plate("fan_rays", [m["frames"]], polys, "y", -hd - 0.07, -hd - 0.02, collide=False)
    hub = [(-hub_r, zc), (hub_r, zc)] + [(hub_r * math.cos(math.pi * k / 6), zc + hub_r * math.sin(math.pi * k / 6)) for k in range(1, 6)]
    kit.prism("fan_hub", m["frames"], hub, "y", -hd - 0.115, -hd - 0.05, collide=False)
    # the spindles under the bar: hexagonal, a bead under the bar, a long
    # shaft, a ball at the foot; the middle one the pendant
    for k, x in enumerate(spindles_x):
        L = spindle_l + (PC_PENDANT if abs(x) < 1e-6 else 0.0) + j(0.02)
        top = zb0 + 0.03
        ck.turned(kit.finish, f"fan_spindle{k}", m["frames"], x, -hd - 0.045,
                  [(0.045, top), (0.072, top - 0.07), (0.045, top - 0.13), (0.045, top - L + 0.14),
                   (0.08, top - L + 0.07), (0.055, top - L + 0.015), (0.0, top - L)], sides=6, collide=False)


def turned_post(kit, k, x, y, floor, pedestal, beam0):
    """A fat turned porch post, pushed from the photo's slim teal ones: a
    square gold pedestal capped with a flare, a teal octagonal shaft turned
    with a ring, a fat belly and necks (PC_SHAFT_LOW over the pedestal,
    PC_SHAFT_HIGH under the capital), a square gold capital flaring into the
    beam. The pedestal's cap and the belly differ by a centimetre."""
    m, j = kit.m, kit.jit
    ph, pz = pedestal[0], floor + pedestal[1]
    cz = beam0 - PC_CAPITAL[1]
    kit.lathe(f"post{k}_pedestal", m["frames"], x, y,
              [(ph, ph, floor - 0.02), (ph, ph, pz - 0.07), (ph + 0.025, ph + 0.025, pz - 0.04 + j(0.008)), (ph + 0.025, ph + 0.025, pz)])
    belly = j(0.01)
    rings = [(r + (belly if 0.3 < dz < 0.5 else 0.0), pz + dz) for r, dz in PC_SHAFT_LOW]
    rings += [(r, cz + dz) for r, dz in PC_SHAFT_HIGH]
    ck.turned(kit.finish, f"post{k}_shaft", m["trim"], x, y, rings)
    ch = PC_CAPITAL[0]
    kit.lathe(f"post{k}_capital", m["frames"], x, y,
              [(ch - 0.03, ch - 0.03, cz), (ch - 0.03, ch - 0.03, cz + 0.06), (ch, ch, cz + 0.10 + j(0.008)), (ch, ch, beam0 + 0.04)],
              collide=False)


def shed_porch(kit, floor, b):
    """The full-width porch on fat turned posts under a heavy shed roof,
    returning the shed's top as surf(distance out from the wall) and its
    ends, for its shingles. purple_b's posts stand on rail-high pedestals
    between square-baluster rails."""
    hw, hd = W / 2, D / 2
    m, j = kit.m, kit.jit
    trim, frames, deck, base, roof = (m[k] for k in ("trim", "frames", "deck", "base", "roof"))
    dx0, dx1 = -hw - PC_DECK_OVER, hw + PC_DECK_OVER
    dy0 = -hd - P_PORCH_D
    # the deck 5 cm into the wall, a centimetre short of the door leaf's face (the walls are plumb)
    kit.box("porch_deck", deck, dx0, dx1, dy0, -hd + 0.05, floor - BC_DECK_T, floor)
    kit.skirt("porch_skirt", base, dx0 + 0.10, dx1 - 0.10, dy0 + 0.10, -hd + 0.04, floor)
    post_y = dy0 + PC_POST_IN
    beam0, beam1 = floor + PC_BEAM[0], floor + PC_BEAM[0] + PC_BEAM[1]
    pedestal = PBC_PEDESTAL if b else PC_PEDESTAL
    for k, x in enumerate(PC_POSTS_X):
        turned_post(kit, k, x, post_y, floor, pedestal, beam0)
        # shaped brackets from the capital along the beam, in the shaded
        # accent under the shed (the end posts' outer sides bare)
        for tag, sx in (("w", -1), ("e", 1)):
            if (k == 0 and sx < 0) or (k == len(PC_POSTS_X) - 1 and sx > 0):
                continue
            reach, drop, thick = PC_BRACKET
            kit.shaped_bracket(f"post{k}_bracket_{tag}", m["accent_shade"], "x", post_y, x + sx * 0.15, sx, beam0 + 0.02,
                               reach, drop, width=thick)
    xe = PC_POSTS_X[-1] + PC_CAPITAL[0] + 0.03
    kit.box("porch_beam", trim, -xe, xe, post_y - 0.12, post_y + 0.12, beam0, beam1, collide=False)
    # the shed: a main slab from inside the wall to just before the beam's
    # line, the beam lapped 4 cm up into it, and its own bell-cast kick
    # lapped under it out to a deep eave, half its pitch, as the main roof's;
    # the slab's ends past the body's sides show the bend
    s, vt = PC_SHED_SLOPE, PC_SHED_T
    u_b = beam1 - 0.04

    def under(y):
        return u_b + (y - post_y) * s
    ry1, y_k = -hd + 0.02, post_y - PC_SHED_KICK[0]
    ex = hw + PC_SHED_END
    kit.prism("porch_roof", roof, [(y_k - 0.02, under(y_k - 0.02)), (ry1, under(ry1)), (ry1, under(ry1) + vt),
                                   (y_k - 0.02, under(y_k - 0.02) + vt)], "x", -ex, ex)
    k_top, s_k, k_t = under(y_k) + vt, PC_SHED_KICK[1], PC_SHED_KICK[2]

    def kick(y):
        return k_top - (y_k - y) * s_k
    ry0, y_in = post_y - PC_SHED_OVER, y_k + 0.30
    kit.prism("porch_roof_kick", roof, [(ry0, kick(ry0) - k_t), (y_in, kick(y_in) - k_t), (y_in, kick(y_in)), (ry0, kick(ry0))],
              "x", -ex - 0.01, ex + 0.01)
    # the gold fascia along the eave over a shaded magenta frieze, one piece
    # as the photo's porch edge, its top 2 cm under the kick's, past the ends
    zf, (fd, fr) = kick(ry0) - 0.02, PC_FASCIA
    xf = ex + 0.03
    kit.plate("porch_fascia", [frames, m["accent_shade"]],
              [([(-xf, zf - fd), (xf, zf - fd), (xf, zf), (-xf, zf)], 0),
               ([(-xf, zf - fd - fr), (xf, zf - fd - fr), (xf, zf - fd), (-xf, zf - fd)], 1)],
              "y", ry0 - 0.06, ry0 + 0.02, collide=False)
    # the steps at the door, no rails, as the photograph
    kit.flight("stair", deck, *PC_STEP_X, dy0, -1, floor)
    if b:
        # square balusters between the pedestals (the steps' bay open), their
        # ends 2 cm into the pedestals; the side rails back to the corner boards
        ph = pedestal[0]
        for k in range(1, len(PC_POSTS_X) - 1):
            a, c = PC_POSTS_X[k], PC_POSTS_X[k + 1]
            kit.straight_rail(f"porch_rail_{k}", "x", post_y, a + ph - 0.02, c - ph + 0.02, a + ph, c - ph, floor)
        for tag, x in (("w", PC_POSTS_X[0]), ("e", PC_POSTS_X[-1])):
            kit.straight_rail(f"porch_rail_{tag}", "y", x, post_y + ph - 0.02, -hd - PROUD + 0.03, post_y + ph, -hd - PROUD, floor)

    def surf(r):            # the shed's top at r out from the wall's face
        y = -hd - r
        return under(y) + vt if y >= y_k else kick(y)
    return surf, -hd - y_k, ex


def build_purple_cartoon(kit, b=False):
    """`purple`, and with `b` `purple_b`: see the module docstring."""
    floor = P_FLOOR
    hw, hd = W / 2, D / 2
    up = floor + PC_STOREY                         # the upstairs floor
    eave = up + (PBC_KNEE if b else 0.0)           # purple_b's side walls rise a knee wall over it
    m = kit.m
    trim, shade, deck, base = (m[k] for k in ("trim", "accent_shade", "deck", "base"))
    j = kit.jit

    # -- the body, plumb (the lean is left out): walls, corner boards, casings, panes
    sill, head = floor + PC_SILL, floor + PC_HEAD
    up_sill, up_head = (up + PBC_UP_SILL, up + PBC_UP_HEAD) if b else (up + PC_UP_SILL, up + PC_UP_HEAD)
    front = [(*P_DOOR_X, floor + THRESHOLD, floor + PC_DOOR_H), (*P_WINDOW_X, sill, head)]
    front += [(a0, a1, up_sill, up_head) for a0, a1 in PC_UP_WINDOWS_X]
    sides = [(c - BC_SIDE_WIN_W / 2, c + BC_SIDE_WIN_W / 2, sill, head) for c in SIDE_WINDOWS]
    back = [(*BC_BACK_WINDOW_X, sill, head), (*BACK_DOOR_X, floor + THRESHOLD, floor + PC_DOOR_H),
            (*BC_BACK_UP_WINDOW_X, up_sill, up_head)]
    openings = {"front": front, "back": back, "west": sides, "east": list(sides)}
    cartoon_body(kit, floor, eave, openings, {("front", 0), ("back", 1)}, {("front", 1): PC_WINDOW_LIGHTS},
                 wall_top_in=PBC_WALL_TOP_IN if b else PC_WALL_TOP_IN)
    # the water table at the floor line, clear of the stoop; the porch deck covers the front's
    bx, by = hw - BC_CORNER + PROUD + 0.02, hd - BC_CORNER + PROUD + 0.02
    bz0, bz1 = floor - BC_BAND_H / 2, floor + BC_BAND_H / 2
    kit.box("band_back0", trim, -bx, BC_STOOP_X[0] - 0.06, hd - 0.01, hd + 0.03, bz0, bz1, collide=False)
    kit.box("band_back1", trim, BC_STOOP_X[1] + 0.06, bx, hd - 0.01, hd + 0.03, bz0, bz1, collide=False)
    kit.box("band_west", trim, -hw - 0.03, -hw + 0.01, -by, by, bz0, bz1, collide=False)
    kit.box("band_east", trim, hw - 0.01, hw + 0.03, -by, by, bz0, bz1, collide=False)
    kit.sweep("plinth", base, [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)], PC_PLINTH)
    if b:
        # purple_b's belt at the eave line across both gables, broken by the
        # upstairs windows' casings (lapped 3 cm behind them), so the windows
        # read straddling the eave; the gable brackets stand 2 cm into it
        ce = ck.CASING - 0.02 - 0.03          # 3 cm in from the casing's outer edge
        for face, y, sy, wins in (("front", -hd, -1, PC_UP_WINDOWS_X), ("back", hd, 1, (BC_BACK_UP_WINDOW_X,))):
            cuts = [-bx] + [v for a0, a1 in wins for v in (a0 - ce, a1 + ce)] + [bx]
            for k in range(0, len(cuts), 2):
                kit.box(f"belt_{face}{k // 2}", trim, cuts[k], cuts[k + 1], *sorted((y + sy * 0.035, y - sy * 0.01)),
                        eave - PBC_BELT[0], eave + PBC_BELT[1], collide=False)
    # the knee brackets at the front gable's lower corners, under the rakes,
    # in the shaded accent (the purple's were its magenta)
    # (on purple_b's belt, 2 cm down into its top)
    for tag, sx in (("w", -1), ("e", 1)):
        run = 0.62 + j(0.03)
        xo, xi = sx * (hw - 0.10), sx * (hw - 0.10 - run)
        poly = [(xi, eave + 0.06), (xo, eave + 0.06), (xi, eave + 0.06 + run * kit.tan)]
        kit.prism(f"gable_bracket_{tag}", shade, poly, "y", -hd - 0.07, -hd + 0.02, collide=False)
    # the pointed hoods over the paired windows, tight under the rakes
    knob = max(pointed_hood(kit, f"front{k}", a0, a1, up_head) for k, (a0, a1) in enumerate(PC_UP_WINDOWS_X, start=2))

    # -- the roof, the heavy part (cartoon_kit's bell roof): the standard's
    # slab, kick at half the pitch, overhangs and sag; bargeboards plain over
    # the shaded magenta band, as the photo's (no drops)
    y0, y1 = -hd - BC_RAKE_OVER, hd + BC_RAKE_OVER
    pitch_deg = PB_PITCH_DEG if b else PC_PITCH_DEG
    br = kit.bell_roof(0.0, hw, eave, BC_ROOF_T, y0, y1, sag=BC_SAG, kick_deg=pitch_deg / 2, eave_over=BC_EAVE_OVER)
    for face, y_rake, out in (("front", y0, -1), ("back", y1, 1)):
        kit.barge(f"barge_{face}", br.profile, [br.r_k], br.r_out + 0.05, 0.0, y_rake, out, BC_BARGE_H, BC_BARGE_BAND, ())
    # the spindle fan over the hoods' knobs, with room in purple_b's flatter peak
    spindle_fan(kit, eave, knob + PC_FAN_BAR[0], PBC_FAN_HUB if b else PC_FAN_HUB, PBC_FAN_RAYS if b else PC_FAN_RAYS,
                PC_SPINDLES_X, PBC_SPINDLE_L if b else PC_SPINDLE_L, m["base"] if b else shade)
    avoid = {}
    if b:
        cx, cy, hx, hy = PBC_CHIMNEY
        fat_chimney(kit, cx, cy, hx, hy, br.rt, eave + 1.0)
        avoid = {1: [(cx - hx - 0.25, cx + hx + 0.25, cy - hy - 0.25, cy + hy + 0.25)]}

    # -- the porch, and the back stoop as the blue's: a deck, a wider flight,
    # solid parapets with fat caps, piers at the foot
    surf, r_kick, ex = shed_porch(kit, floor, b)
    x0, x1 = BC_STOOP_X
    y_edge = hd + STOOP_D
    # the deck 4.5 cm into the wall: off the door leaf's face, the skirt's and the parapets' ends
    kit.box("stoop_deck", deck, x0, x1, hd - 0.045, y_edge, floor - BC_DECK_T, floor)
    kit.skirt("stoop_skirt", base, x0 + 0.08, x1 - 0.08, hd - 0.04, y_edge - 0.08, floor)
    scx = (x0 + x1) / 2
    ssx0, ssx1 = scx - BC_STOOP_STAIR_W / 2, scx + BC_STOOP_STAIR_W / 2
    n, riser, going = kit.flight("stoop_stair", deck, ssx0, ssx1, y_edge, 1, floor)
    kit.stoop_parapets("stoop", (("w", ssx0 - 0.05), ("e", ssx1 + 0.05)), y_edge, 1, floor, n, riser, going, -(STOOP_D + 0.05))

    # -- shingle clusters from their own seed: the main roof's (cartoon_kit's
    # roof_clusters), then two on the shed, then the vents on the back half
    trim_rng = kit.rng
    rng = kit.rng = random.Random(kit.shingle_seed)
    bm = bmesh.new()
    tabs, mains = ck.roof_clusters(rng, bm, br, avoid=avoid)
    kit.finish("roof_shingles", bm, [m["roof"]], collide=False)
    tabs += shed_clusters(kit, rng, surf, r_kick, ex)
    vents = ck.roof_vents(kit.finish, rng, [m["deck"], m["glass"]], br, mains)
    kit.rng = trim_rng
    pitch_deg = PB_PITCH_DEG if b else PC_PITCH_DEG
    extra = (f"; porch beam {PC_BEAM[0]:.2f} clear, shed {math.degrees(math.atan(PC_SHED_SLOPE)):.1f} deg with a "
             f"{math.degrees(math.atan(PC_SHED_KICK[1])):.1f} deg kick, upstairs windows {up_sill - eave:+.2f}..{up_head - eave:+.2f} "
             f"about the eave")
    return dict(pitch=pitch_deg, floor=floor, storey=PC_STOREY, knee=PBC_KNEE if b else 0.0, eave=eave, rt=br.rt,
                kick=pitch_deg / 2, lean=False, door_clear=PC_DOOR_H - THRESHOLD, tabs=tabs, vents=vents, risers=n,
                riser=riser, going=going, extra=extra)


def street_clusters(rng, bm, theta, surf, y_wall, r_lim, x_lim, draws):
    """Shingle clusters on a slope that falls toward the street (-Y) from a
    wall's line at y_wall, where the kit's slopes fall along X: built in a
    frame turned a quarter about the origin (local x = -y, local y = x), so
    the slope falls toward local +X from local x = -y_wall, then turned back.
    The turn keeps every dot product, so the tabs stay on the painted grid.
    `surf(r)` is the slope's top r out from the wall, `r_lim` and `x_lim` the
    region the tabs keep inside; each of `draws` gives a cluster's (r, x,
    max_courses), drawn just before it is built. Into `bm`; returns the tabs."""
    old = set(bm.verts)
    slope = dict(s=1, xc=-y_wall, theta=theta, surf=lambda r, y: surf(r), r=r_lim, y=x_lim)
    tabs = 0
    for draw in draws:
        r, x, courses = draw()
        tabs += ck.shingle_cluster(rng, bm, slope, r, x, max_courses=courses)
    for v in bm.verts:
        if v not in old:
            v.co = Vector((v.co.y, -v.co.x, v.co.z))
    return tabs


def shed_clusters(kit, rng, surf, r_kick, ex):
    """Two clusters on the purple's shed porch roof, one each side of the
    middle, on the main slab, clear of the kick."""
    hd = D / 2
    bm = bmesh.new()
    tabs = street_clusters(rng, bm, math.atan(PC_SHED_SLOPE), surf, -hd, (0.25, r_kick - 0.05), (-ex + 0.05, ex - 0.05),
                           [lambda side=side: (rng.uniform(0.6, r_kick - 0.6), side * rng.uniform(0.6, ex - 0.9), 2)
                            for side in (-1, 1)])
    kit.finish("porch_roof_shingles", bm, [kit.m["roof"]], collide=False)
    return tabs


# --- blue_b, the cartoony build -----------------------------------------------------------

def wrap_eave(br, rise, inside, x0, x1, y0, y1):
    """The highest eave (the lean-to's top at its eaves' edge, to the
    centimetre) for blue_b's lean-to whose top, eave + rise(x, y), stays
    BBC_WRAP_CLEAR under everything of the main roof over it, sampled over
    its plan (`inside`): the front bargeboard's lower edge across its depth
    (board and sawn band, which bend down with the kick at the corner) and
    the main slab's and the kick's undersides, with their sag. The pendant
    drops hang far higher, over the porch's middle. The relationship, not a
    number: a change to the roof moves the lean-to with it."""
    yr, r_end = br.y0, br.r_out + 0.05
    best = None
    for i in range(121):
        x = x0 + (x1 - x0) * i / 120
        r = abs(x - br.xc)
        for k in range(121):
            y = y0 + (y1 - y0) * k / 120
            if not inside(x, y):
                continue
            sag = ck.sag_at(br.stations, y)
            ceiling = []
            if yr - ck.BARGE_PROUD <= y <= yr + 0.02 and r <= r_end:
                ceiling.append(br.profile(r) - 0.02 - BC_BARGE_H - BC_BARGE_BAND)
            if br.y0 <= y <= br.y1 and r <= br.r_k + 0.02:
                ceiling.append(br.under(x) - sag)
            if br.y0 - 0.03 <= y <= br.y1 + 0.03 and br.r_in <= r <= br.r_out:
                ceiling.append(br.kick_top(r) - br.kick_t - sag)
            if ceiling:
                z = min(ceiling) - BBC_WRAP_CLEAR - rise(x, y)
                best = z if best is None else min(best, z)
    return math.floor(best * 100) / 100


def wrap_porch(kit, floor, br):
    """blue_b's glazed porch, pushed as the wrap it is: from the body's front
    wall round its right-front corner, BB_WRAP past the right wall and
    BB_SIDE_D back along it, under one L-shaped lean-to tucked under the main
    roof's corner. The lean-to is two planar slabs welded on a hip from the
    outer corner into the body's corner (the side's slope set so both reach
    the body at one height), its eave as high as the front bargeboard's bent
    end and the main eaves let it stand (`wrap_eave`), a fat cream fascia
    wrapping both eaves in one piece. Under it, plumb walls on fat timber
    posts at the three outer corners (the lean is left out here: the shared
    warp is a rectangle's), a glass band wrapping the corner over a solid
    wainscot, single-piece casings with fat mullions, a plinth round the foot.
    Returns what its clusters need."""
    hw, hd = W / 2, D / 2
    m = kit.m
    trim, frames, glass, base = (m[k] for k in ("trim", "frames", "glass", "base"))
    px0, px1 = B_PORCH_X0, hw + BB_WRAP
    py0, py1 = -hd - B_PORCH_D, -hd + BB_SIDE_D
    pe = BC_PORCH_POST / 2 - PROUD
    over, t, pt = BBC_WRAP_OVER, BBC_WRAP_T, B_PORCH_T
    x_w, x_out, y_out, y_back = px0 - BBC_WRAP_OVER_W, px1 + over, py0 - over, py1 + over
    x_in = hw - 0.05                         # the side slab's inner edge, inside the body's east wall
    d_f, d_s = -hd - y_out, x_out - hw
    s_f = BBC_WRAP_SLOPE
    s_s = s_f * d_f / d_s                    # both slopes reach the body's corner at one height
    y_c = -hd + (hw - x_in) * d_f / d_s      # the hip carried on to x_in, inside the front wall

    def rise(x, y):                          # the top over the eave: the lower of the two slopes
        return min((y - y_out) * s_f, (x_out - x) * s_s)

    def inside(x, y):
        return (x >= x_w and y_out <= y <= y_c) or (x_in <= x <= x_out and y_out <= y <= y_back)
    z_e = wrap_eave(br, rise, inside, x_w, x_out, y_out, y_back)

    def top(x, y):
        return z_e + rise(x, y)
    # the lean-to: the front slab A B C D and the side slab B E F C, welded on the hip B C
    pts = {"A": (x_w, y_out), "B": (x_out, y_out), "C": (x_in, y_c), "D": (x_w, y_c), "E": (x_out, y_back), "F": (x_in, y_back)}
    bm = bmesh.new()
    vt = {k: bm.verts.new((x, y, top(x, y))) for k, (x, y) in pts.items()}
    vb = {k: bm.verts.new((x, y, top(x, y) - t)) for k, (x, y) in pts.items()}
    for loop in (("A", "B", "C", "D"), ("B", "E", "F", "C")):
        bm.faces.new([vt[k] for k in loop])
        bm.faces.new([vb[k] for k in reversed(loop)])
    for p, q in (("A", "B"), ("C", "D"), ("D", "A"), ("B", "E"), ("E", "F"), ("F", "C")):
        bm.faces.new((vt[p], vt[q], vb[q], vb[p]))
    kit.finish("porch_roof", bm, [m["roof"]])
    # the fascia wrapping both eaves, mitred at the corner, 2 cm into the
    # slab's edge and 6 cm proud, a band of the slab's edge showing over it so
    # the lean-to reads as a roof, its ends 2 cm past the slab's
    fz1 = z_e - BBC_FASCIA[0]
    kit.sweep("porch_fascia", trim, [(x_w - 0.02, y_out), (x_out, y_out), (x_out, y_back + 0.02)],
              ((-0.02, fz1 - BBC_FASCIA[1]), (0.06, fz1 - BBC_FASCIA[1]), (0.06, fz1), (-0.02, fz1)),
              closed=False, collide=False)

    def under(x, y):
        return top(x, y) - t
    # the walls: tops 4 cm into the slab over their inner faces; the glass's
    # head under the slab over the front wall's outer face, the lowest
    g0 = floor + BBC_WRAP_GLASS
    g1 = under(px0, py0) - 0.03 - (ck.CASING_HEAD - 0.02)
    ins = BBC_WRAP_INSET
    x_start = px1 - pe
    back_len = x_start - (hw - 0.02)
    p_open = {"front": [(px0 + ins, px1 - ins, g0, g1)], "east": [(py0 + ins, py1 - ins, g0, g1)],
              "west": [(py0 + ins, py0 + ins + 0.50, g0, g1)]}
    yw1 = -hd + 0.02 + pe
    west_len = (yw1 - pe) - (py0 + pe)
    kit.shell("porch_", px0, px1, py0, yw1, pt, pe, {"front": -BELOW + 0.005, "west": -BELOW - 0.015},
              {"front": Top(flat=under(px0, py0 + pt) + 0.04),
               "west": SlopeTop(under(px0, yw1 - pe) + 0.04, under(px0, py0 + pe) + 0.04, west_len)},
              p_open, [m["walls"], base], floor, which=("front", "west"))
    kit.shell("porch_", px0, px1, py0, py1, pt, pe, {"east": -BELOW - 0.015}, {"east": Top(flat=under(px1 - pt, py1) + 0.04)},
              p_open, [m["walls"], base], floor, which=("east",))
    kit.wall("porch_wall_back", (x_start, py1, 0.0), (-1, 0, 0), (0, -1, 0), back_len, pt, -BELOW - 0.005,
             SlopeTop(under(x_start, py1) + 0.04, under(hw - 0.02, py1) + 0.04, back_len), [], floor, [m["walls"], base])
    # fat timber posts at the three outer corners, their collars just under
    # the slab over them and their shafts on up into it
    for tag, cx, cy in (("sw", px0 - PROUD + BC_PORCH_POST / 2, py0 - PROUD + BC_PORCH_POST / 2),
                        ("se", px1 + PROUD - BC_PORCH_POST / 2, py0 - PROUD + BC_PORCH_POST / 2),
                        ("ne", px1 + PROUD - BC_PORCH_POST / 2, py1 + PROUD - BC_PORCH_POST / 2)):
        z_u = under(cx, cy)
        kit.timber_post(f"porch_post_{tag}", trim, cx, cy, -BELOW - 0.045, (0.55, 0.62), z_u, z_u + 0.12, size=BC_PORCH_POST)
    lights = {"front": 3, "east": 3}       # few, big lights wrapping the corner
    for face, axis, at, out, opens in (("front", "x", py0, -1, p_open["front"]), ("west", "y", px0, -1, p_open["west"]),
                                       ("east", "y", px1, 1, p_open["east"])):
        for k, (a0, a1, z0, z1) in enumerate(opens):
            kit.casing(f"porch_{face}{k}_casing", frames, axis, at, out, a0, a1, z0, z1, lights=lights.get(face, 1))
            kit.pane(f"porch_{face}{k}_pane", glass, axis, at, out, a0, a1, z0, z1, recess=BC_PANE_RECESS)
    # (its inner faces 4.5 cm in, off the entry landing skirt's end and front)
    kit.sweep("porch_plinth", base, [(px0, -hd + 0.06), (px0, py0), (px1, py0), (px1, py1), (hw - 0.06, py1)],
              ((-0.045, -0.09), (0.10, -0.09), (0.04, 0.40), (-0.045, 0.40)), closed=False)
    return dict(z_e=z_e, s_f=s_f, s_s=s_s, d_f=d_f, d_s=d_s, x_w=x_w, x_in=x_in, y_back=y_back)


def side_stoop(kit, floor):
    """blue_b's side door's landing and flight on the driveway side, in place
    of the back stoop, pushed as one bold mass: a deck along the wall at the
    door, the flight running down along the wall toward the back in the
    blue's chunky risers at its grade, and solid parapets with fat caps and
    fat piers at the foot, as the blue's back stoop has (cartoon_kit's): the
    outer one a single piece from the landing's front corner down to its
    pier, the inner one from just behind the flight's top (clear of the
    door) down, and a third across the landing's front, run between the
    window's casing and the door's into the leaning wall. The flight stands
    BBC_FLIGHT_IN off the wall, its inner cap clear of the window casing
    beside it and its pier of the plinth's flare. Returns its (n, riser, going)."""
    hw = W / 2
    m = kit.m
    deck, base, trim = m["deck"], m["base"], m["trim"]
    ly0, ly1 = BBC_LANDING_Y
    sx0 = hw + BBC_FLIGHT_IN
    sx1 = sx0 + STAIR_W
    x_in, x_out = sx0 - 0.05, sx1 + 0.05        # the parapets lap 2 cm over the treads' ends
    xd = x_out + BC_PARAPET / 2 + 0.03          # the deck's outer edge, 3 cm past the parapet
    kit.box("side_deck", deck, hw - 0.06, xd, ly0, ly1, floor - BC_DECK_T, floor)
    kit.skirt("side_skirt", base, hw - 0.04, xd - 0.08, ly0 + 0.08, ly1 - 0.08, floor)
    n, riser, going = kit.flight("side_stair", deck, sx0, sx1, ly1, 1, floor)
    # the outer parapet from 2 cm inside the front one; the inner from 0.20 behind the edge
    kit.stoop_parapets("side", (("out", x_out),), ly1, 1, floor, n, riser, going, ly0 + 0.05 - ly1)
    kit.stoop_parapets("side", (("in", x_in),), ly1, 1, floor, n, riser, going, -0.20)
    # the front parapet and its cap, a centimetre off the side ones' heights,
    # from inside the leaning wall to 2 cm past the outer parapet and its cap
    yf = ly0 + 0.03 + BC_PARAPET / 2
    pt = floor + RAIL_H - ck.CAP_H + 0.05
    kit.box("side_parapet_front", trim, hw + 0.02, x_out + BC_PARAPET / 2 + 0.02, yf - BC_PARAPET / 2, yf + BC_PARAPET / 2,
            floor - 0.03, pt)
    kit.box("side_parapet_front_cap", trim, hw + 0.01, x_out + BC_PARAPET_CAP / 2 + 0.02, yf - BC_PARAPET_CAP / 2,
            yf + BC_PARAPET_CAP / 2, floor + RAIL_H + 0.03 - ck.CAP_H, floor + RAIL_H + 0.03, collide=False)
    return n, riser, going


def build_variant(v, coll):
    if v == "blue":
        return build_blue_cartoon(Chunky("blue", coll))
    elif v == "purple":
        return build_purple_cartoon(Chunky("purple", coll, pitch_deg=PC_PITCH_DEG, seed=PC_SEED, shingle_seed=PC_SHINGLE_SEED,
                                           risers=PC_RISERS, grade=PC_GRADE, wall_top_in=PC_WALL_TOP_IN))
    elif v == "blue_b":
        return build_blue_cartoon(Chunky("blue_b", coll, seed=BBC_SEED, shingle_seed=BBC_SHINGLE_SEED), b=True)
    elif v == "purple_b":
        return build_purple_cartoon(Chunky("purple_b", coll, pitch_deg=PB_PITCH_DEG, seed=PBC_SEED, shingle_seed=PBC_SHINGLE_SEED,
                                           risers=PC_RISERS, grade=PC_GRADE, knee=PBC_KNEE, wall_top_in=PBC_WALL_TOP_IN), b=True)


# --- reference -----------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm = ck.prism_bm(ring, "z", 0.0, height - 0.40)
    body_verts = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:
        if v not in body_verts:
            v.co.z += height - 0.17
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    mesh.materials.append(mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0)))
    obj[TAG] = True
    obj["kyt_collision"] = "none"
    obj.location = (x, y, z)
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


def build_reference(reference):
    hw, hd = W / 2, D / 2
    outline("footprint_body", reference, -hw, hw, -hd, hd)
    outline("lot_9m", reference, LOT_X0, LOT_X0 + LOT_W, LOT_Y[0], LOT_Y[1])
    outline("driveway", reference, hw + B_PORCH_PROUD + 0.1, LOT_X0 + LOT_W, LOT_Y[0], hd + 2.0)
    figure("figure_1p7m", reference, -4.4, -9.0)
    if "ground_line" not in bpy.data.objects:
        marker = bpy.data.objects.new("ground_line", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker[TAG] = True
        reference.objects.link(marker)


# --- checks --------------------------------------------------------------------

def triangles(objs):
    total = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            total += len(o.data.loop_triangles)
    return total


def coplanar_pairs(objs, tol=1e-4):
    """Pairs of faces from different objects lying in one plane and
    overlapping in area (by their bounds in the plane): the z-fights. Each
    face's plane is written the same way up, so a pair facing opposite
    ways is found too."""
    faces = []
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        rot = mw.to_3x3()
        for p in o.data.polygons:
            n = (rot @ p.normal).normalized()
            for c in n:
                if abs(c) > 1e-6:
                    if c < 0:
                        n = -n
                    break
            pts = [mw @ o.data.vertices[i].co for i in p.vertices]
            d = n.dot(pts[0])
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            flat = [(q.dot(e1), q.dot(e2)) for q in pts]
            us, vs = [a for a, _ in flat], [b for _, b in flat]
            faces.append((d, o.name, n, min(us), max(us), min(vs), max(vs), flat))
    faces.sort(key=lambda f: f[0])

    def overlap(P, Q):
        """Two polygons in the plane overlap unless an edge of either
        separates them (exact for convex faces, conservative otherwise)."""
        for poly in (P, Q):
            n = len(poly)
            for k in range(n):
                ax, ay = poly[(k + 1) % n][0] - poly[k][0], poly[(k + 1) % n][1] - poly[k][1]
                length = math.hypot(ax, ay)
                if length < 1e-9:
                    continue
                nx, ny = -ay / length, ax / length
                p = [x * nx + y * ny for x, y in P]
                q = [x * nx + y * ny for x, y in Q]
                if min(max(p), max(q)) - max(min(p), min(q)) <= 1e-3:
                    return False
        return True

    found = []
    for i in range(len(faces)):
        di, oi, ni, u0, u1, v0, v1, pi = faces[i]
        j = i + 1
        while j < len(faces) and faces[j][0] - di < tol:
            dj, oj, nj, w0, w1, x0, x1, pj = faces[j]
            j += 1
            if oi == oj or (ni - nj).length > 1e-3:
                continue
            ou = min(u1, w1) - max(u0, w0)
            ov = min(v1, x1) - max(v0, x0)
            if ou > 1e-3 and ov > 1e-3 and overlap(pi, pj):
                found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def report(objs, label):
    bpy.context.view_layer.update()
    objs = [o for o in objs if o.type == "MESH"]
    tris = triangles(objs)
    xs, ys, zs = [], [], []
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x); ys.append(p.y); zs.append(p.z)
    print(f"{NAME}: {label}: {len(objs)} parts, {tris} triangles, "
          f"x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}, z {min(zs):.2f}..{max(zs):.2f}")
    return tris


# --- renders -------------------------------------------------------------------

def variant_parts(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and o.get("kyt_variant") == variant]


def render(folder):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True
    kit = Kit("blue", stage)       # a maker for the stage's own pieces
    kit.v = "_stage"

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    ground = mat("_ground", (0.36, 0.44, 0.26))
    walk = mat("_walk", (0.62, 0.60, 0.56))
    street = mat("_street", (0.28, 0.28, 0.30))
    kit.box("ground", ground, -60, 60, -60, 60, -0.30, -0.01, collide=False)
    kit.box("walk", walk, -60, 60, LOT_Y[0] - 1.6, LOT_Y[0], -0.30, 0.0, collide=False)
    kit.box("street", street, -60, 60, -60, LOT_Y[0] - 1.6, -0.30, -0.005, collide=False)
    kit.box("drive", walk, W / 2 + B_PORCH_PROUD + 0.2, LOT_X0 + LOT_W - 0.2, LOT_Y[0] - 1.6, D / 2 + 2.0, -0.30, 0.004, collide=False)
    fig = mat("_figure_stage", (0.30, 0.22, 0.40))
    fig_obj = figure("_figure", stage, -1.7, -10.0, mat=fig)
    fig_obj.hide_render = True

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.45, -0.70, 0.55)).to_track_quat("Z", "Y").to_euler()
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

    def show(variant):
        for v in VARIANTS:
            for o in variant_parts(v):
                o.hide_render = v != variant

    def shoot(name, eye, target, lens=32, size=(1600, 1000), ortho=None):
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 500
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{NAME}: rendered {scene.render.filepath}")

    # the blue from the street at the photo's angle (right of centre, eye height)
    show("blue")
    shoot("blue_three_quarter", (4.8, -15.5, 1.6), (0.2, -1.5, 3.8), lens=30)
    shoot("blue_front_elevation", (0.0, -40.0, 4.1), (0.0, 0.0, 4.1), ortho=14.0)
    shoot("blue_side_elevation", (40.0, -1.0, 4.1), (0.0, -1.0, 4.1), ortho=20.0)
    shoot("blue_rear_three_quarter", (7.0, 17.0, 1.7), (0.5, 3.0, 3.6), lens=30)
    fig_obj.hide_render = False
    shoot("blue_with_figure", (5.5, -16.5, 1.6), (-0.6, -4.5, 2.9), lens=30)
    fig_obj.hide_render = True
    # the purple from the left front, closer, as its photo
    show("purple")
    shoot("purple_three_quarter", (-8.5, -12.5, 1.5), (-0.5, -1.5, 3.0), lens=26)
    shoot("purple_front_elevation", (0.0, -40.0, 3.6), (0.0, 0.0, 3.6), ortho=14.0)
    shoot("purple_side_elevation", (40.0, -1.0, 3.6), (0.0, -1.0, 3.6), ortho=20.0)
    # the b pair: the blue_b from the driveway side, where its porch wraps
    # and its side door is; the purple_b as the purple
    show("blue_b")
    shoot("blue_b_three_quarter", (10.5, -14.0, 1.6), (0.8, -1.0, 3.6), lens=28)
    show("purple_b")
    shoot("purple_b_three_quarter", (-8.5, -12.5, 1.5), (-0.5, -1.5, 3.6), lens=26)
    # both originals on neighbouring lots, then all four: the others moved
    # over for the shot only
    for o in variant_parts("purple"):
        o.location.x += LOT_W
    for v in ("blue", "purple"):
        for o in variant_parts(v):
            o.hide_render = False
    shoot("both_side_by_side", (1.0, -26.0, 1.7), (4.6, -1.0, 3.8), lens=30)
    for o in variant_parts("purple"):
        o.location.x -= LOT_W
    lots = ("blue", "blue_b", "purple", "purple_b")
    for k, v in enumerate(lots):
        for o in variant_parts(v):
            o.location.x += k * LOT_W
            o.hide_render = False
    shoot("four_up_lots", (13.5, -37.0, 1.8), (13.5, -1.0, 4.4), lens=26, size=(2000, 900))
    for k, v in enumerate(lots):
        for o in variant_parts(v):
            o.location.x -= k * LOT_W


# --- main ------------------------------------------------------------------------

def layer_collection(name, root=None):
    """The view layer's entry for a collection, whose `hide_viewport` is its eye."""
    root = root or bpy.context.view_layer.layer_collection
    if root.name == name:
        return root
    for child in root.children:
        found = layer_collection(name, child)
        if found:
            return found
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if name != NAME:
        raise SystemExit(f"{NAME}: open {NAME}.blend, not {name}")
    export, reference = (bpy.data.collections[n] for n in ("export", "reference"))
    hers = [o.name for o in export.all_objects if not o.get(TAG)]
    if hers and "--replace" not in argv:
        raise SystemExit(f"{NAME}: export holds {hers[:4]}, which may be hers; --replace builds over it")
    for o in [o for o in bpy.data.objects if o.get(TAG) or (hers and o.name in hers)]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(("variant_", "_"))]:
        bpy.data.collections.remove(coll)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    built = {"blue": build_variant("blue", export)}
    for v in VARIANTS[1:]:
        sub = bpy.data.collections.new(f"variant_{v}")
        export.children.link(sub)
        built[v] = build_variant(v, sub)
    bpy.context.view_layer.update()
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True
    build_reference(reference)
    # the tool's materials nothing uses any more (a retired variant's, as
    # blue_cartoon's) go, so the file keeps no orphans of its own
    for mat in [m for m in bpy.data.materials if m.users == 0 and m.name.startswith(f"{NAME}_")]:
        bpy.data.materials.remove(mat)

    tris = {}
    for v in VARIANTS:
        tris[v] = report(variant_parts(v), f"{v} ({'export' if v == 'blue' else 'export/variant_' + v})")
    for v in VARIANTS:
        b = built[v]
        print(f"{NAME}: {v} (cartoony): pitch {b['pitch']:.0f} deg, floor {b['floor']:.2f}, storey {b['storey']:.2f} m"
              + (f" and a {b['knee']:.2f} m knee wall" if b.get("knee") else "")
              + f", eave {b['eave']:.2f}, ridge top {b['rt']:.2f} (sagging {BC_SAG:.2f} at mid-length), slab {BC_ROOF_T:.2f}, "
              f"eave and rake over {BC_EAVE_OVER:.2f} with a {b['kick']:.1f} deg kick; walls "
              + (f"leaning {BC_LEAN_DEG} deg" if b["lean"] else "plumb")
              + f"; doors {b['door_clear']:.2f} m clear; {b['risers']} risers of {b['riser']:.3f} on {b['going']:.3f} "
              f"(grade {b['riser'] / b['going']:.4f}); {b['tabs']} shingle tabs, {b['vents']} vents; painted siding "
              f"{BC_SIDING:.2f} m, {b['storey'] / BC_SIDING:.2f} courses floor to eave" + b.get("extra", ""))
    for v in VARIANTS:
        pairs = coplanar_pairs(variant_parts(v))
        print(f"{NAME}: {v}: {len(pairs)} coplanar overlapping face pairs" +
              ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{NAME}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1])


main()
