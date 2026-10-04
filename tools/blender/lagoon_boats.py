"""The lagoon's rental boats, blocked out (2026-10-03): the boating centre on
Shore Street, "after the one at Lake Merritt" (Christina, 2026-09-30, in
`documentation/maps/entrance-landscaping.html` and
`documentation/maps/beach-town-plan.html`): "Its boats are small rentals that
stay inside the lagoon, all from the floating landing below it. Paddle boats
keep to a roped calm corner of the west body. Kayaks follow a trail of about
234 m each way ... A covered glass-bottom boat of about 10 m loops along the
ridge under the belvedere and back." No sailing.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/lagoon_boats.blend --python tools/blender/lagoon_boats.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, sixteen boats, all at the origin, each
marked `kyt_variant` so Send writes each as a prop of its own (`send.py`):

- **paddle_boat**, in `export` itself: a 1990s rental pedal boat for two, a
  moulded white tub with a thick rim and a rubber bumper, two orange bucket
  seats side by side, the pedal cranks on one axle in front of them through
  a centre console, the tiller on the armrest between the seats, the paddle
  wheel under a moulded housing at the stern and the rudder behind it.
- **paddle_boat_canopy**, in `export/variant_paddle_boat_canopy`: the same
  boat (linked copies of every part, so reshaping one reshapes both) under a
  flat shade canopy on four posts.
- **kayak_single**, in `export/variant_kayak_single`: an 11 ft sit-on-top
  rental kayak, yellow, a moulded seat well with a moulded backrest behind it
  and the leg well forward, carry handles at both ends, the paddle lying
  across it as its own part.
- **kayak_tandem**, in `export/variant_kayak_tandem`: the 13 ft two-seater,
  red, two seat wells and leg wells, two paddles (linked copies of the
  single's paddle).
- **glass_bottom_boat**, in `export/variant_glass_bottom_boat`: the covered
  tour boat of about 10 m. A flat canopy roof on eight posts over the
  passenger well; a glass viewing well down the middle of the floor, a real
  hole through the floor and through the hull bottom joined by a shaft, four
  glass slabs set in its bottom between three cross bars; a bench down each
  side facing the well, a backrest on the bulwark behind each; the helm at
  the stern (console, wheel, a stool) with a small outboard on the transom;
  a bow locker with a life ring on it. The passenger interior is built
  because guests and the player's camera look in and down through the glass.

The further variants (2026-10-03, Christina: "build all the offered
variants"), each in `export/variant_<name>`, share every unchanged part with
the five above as linked copies (moved, where a part moves, by its object's
location only):

- **paddle_boat_four**: two adults and two kids, a 2.8 m hull and bumper of
  their own; the bow deck, console, pedals, seats, armrest and tiller move
  forward with the bow, the wheel housing, wheel and rudder aft with the
  stern, and a moulded kids' bench fills the stern behind the seats.
- **paddle_boat_tunnel**: the map's 2.2 m overall, bumper included: a
  shorter hull with a slot through it under the armrest, a narrow paddle
  wheel in the slot whose lower blades show under the hull, no stern
  housing, and a rudder hung on the transom.
- **kayak_single_lime**, **_orange**, **_teal** and **kayak_tandem_lime**,
  **_purple**, **_blue**: the kayaks in other rental colours, every part a
  linked copy, the hull wearing its colour as an object material
  (`lagoon_boats_kayak_<colour>`), so the shape is shared and the colour is
  not.
- **glass_bottom_boat_electric**: no outboard; a quiet electric launch's
  small propeller on a shaft out of the skeg and a rudder hung under the
  transom.
- **glass_bottom_boat_bow_helm**: the console, wheel and stool forward at
  the bow ahead of the well, the bow locker shortened in front of them with
  the life ring moved onto it, and a bench across the stern where the helm
  was.
- **glass_bottom_boat_side_gate**: a boarding gate in the starboard
  bulwark between two posts: the hull and the rubrail of its own with the
  bulwark cut down to a sill and the rubrail cut short each side, a teal
  gate leaf in the opening, and the starboard bench and backrest in two
  pieces either side of it.

Every variant but the first has its eye shut. Into the locked `reference`
collection go a `waterline` marker (an empty at the origin, which Check reads
as a floating prop: it reports the draft and the height over the water), each hull's
waterline as an edge loop (`waterline_<variant>`, the hull sliced at z = 0),
each variant's length-by-beam outline and a 1.7 m figure. Everything the
tool makes carries `kyt_lagoon_boats`, so a rerun removes and rebuilds its
own work and keeps anything of hers; `export` holding anything untagged
refuses without `--replace`. The further variants are built after the first
five and only copy them, so the first five come out the same as before
(their geometry hashes were compared before and after the further variants
were added).

**Frame.** Real metres, Z up. z = 0 is the waterline, the water's surface
where the boat floats; every hull goes below it by its draft as a closed
form down to the keel. The bow is +Y (the glTF export turns Blender +Y into
Godot -Z, Godot's forward for `Basis.looking_at`, as `ride_vehicle.gd`
orients its trains). The origin is on the centreline, midships of the hull's
length, at the waterline; what hangs off the stern (the paddle boat's wheel
housing and rudder, the outboard) is outside the hull's length.

**Contract.** Closed shells, silhouette first; interiors where a boat is
open: the paddle boat's tub, the kayaks' wells and the glass-bottom boat's
passenger well. Every part is `kyt_collision = none` this pass; collision
and boarding are decided when the boats are placed and scheduled. No two
shapes share a plane: a part that meets another laps 2 cm into it or stands
proud of it. Repeated pieces are linked copies of one mesh (the paddle
boat's two seats and its whole hull in the canopy variant, the two paddles,
the glass boat's benches, backrests, posts, glass slabs and bars).

**How it is built.** A hull is lofted through rings of one plan outline
(straight sides, an elliptical bow, rounded stern corners) inset by given
amounts at given heights: up the outside, across the rim, down the inside to
the floor (`tub`); the glass well is a rectangle cut through the floor and
the bottom and joined by its shaft. A kayak is lofted through cross-sections
along its length, each the same 18 points, its wells dipping the deck where
a well is (`station_loft`). Bumpers and rubrails are the same rings closed
round a profile. Stand-in materials by surface, `lagoon_boats_<surface>`,
the colours the plan's map gives its symbols where it gives one; the glass
is a half-transparent stand-in so the well reads in the viewport.
"""

import math
import os
import re
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

TAG = "kyt_lagoon_boats"
PROP = "lagoon_boats"
VARIANTS = ("paddle_boat", "paddle_boat_canopy", "kayak_single", "kayak_tandem", "glass_bottom_boat",
            "paddle_boat_four", "paddle_boat_tunnel",
            "kayak_single_lime", "kayak_single_orange", "kayak_single_teal",
            "kayak_tandem_lime", "kayak_tandem_purple", "kayak_tandem_blue",
            "glass_bottom_boat_electric", "glass_bottom_boat_bow_helm", "glass_bottom_boat_side_gate")
SHARP = math.radians(50.0)      # faces meeting at more than this read as a crease

# --- the paddle boat -------------------------------------------------------
# The plan's map draws each paddle boat 2.2 x 1.6 m (entrance-landscaping.html,
# "Paddle boat"); a two-seat moulded pedal boat is about that (chosen: the
# hull is the map's size, the wheel housing and rudder hang off the stern).
PB_L = 2.20                    # hull length, the map's
PB_B = 1.60                    # beam, the map's
PB_BOW_RY = 0.55               # the bow's elliptical round in plan, chosen
PB_STERN_R = 0.40              # the stern corners' radius, chosen
PB_DRAFT = 0.18                # chosen: two adults in a moulded pedal boat
PB_SHEER = 0.44                # the rim's top over the water, chosen
PB_RIM = 0.10                  # the rim's flat, chosen chunky
PB_FLOOR = 0.12                # the footwell floor over the water, chosen (self-draining)
# rings of the hull, outside up, across the rim, inside down: (inset at the
# sides, at the bow, at the stern, z); the bottom is raked up at the bow
PB_RINGS = ((0.24, 0.40, 0.16, -PB_DRAFT), (0.07, 0.14, 0.05, -0.12), (0.0, 0.0, 0.0, 0.02),
            (0.0, 0.0, 0.0, 0.34), (0.03, 0.03, 0.03, PB_SHEER),
            (0.03 + PB_RIM, 0.03 + PB_RIM, 0.03 + PB_RIM, PB_SHEER),
            (0.15, 0.15, 0.15, 0.40), (0.17, 0.17, 0.17, PB_FLOOR))
# the rubber bumper round the hull, (inset, z), 2 cm into the hull's side
PB_BUMPER = ((0.02, 0.22), (-0.03, 0.225), (-0.055, 0.27), (-0.03, 0.315), (0.02, 0.32))
PB_BOWDECK_Y = 0.42            # the moulded bow deck starts here, chosen
PB_BOWDECK_TOP = 0.415         # 2.5 cm under the rim
PB_SEAT_X = 0.39               # each bucket seat's centre, chosen
PB_SEAT_HALF = 0.27            # half a seat's width (0.54 m), out 2 cm into the hull's side
# a seat in side view, (y, z): front lip, dished pan, raked back, down to the floor
PB_SEAT = ((-0.10, 0.10), (-0.10, 0.32), (-0.15, 0.355), (-0.48, 0.30), (-0.56, 0.33),
           (-0.68, 0.84), (-0.76, 0.87), (-0.86, 0.85), (-0.92, 0.46), (-0.92, 0.10))
PB_ARMREST = (-0.14, 0.14, -0.90, -0.16, 0.08, 0.46)    # between the seats, the tiller's base
PB_TILLER_Y = -0.33
PB_TILLER_TOP = 0.72           # the stick's top; a 7 cm knob on it
PB_CONSOLE = (-0.11, 0.11, -0.08, PB_BOWDECK_Y + 0.02, 0.09, 0.35)   # the drive tunnel
PB_AXLE_Y, PB_AXLE_Z, PB_AXLE_R = 0.22, 0.27, 0.025     # the crank axle across the footwell
PB_CRANK = 0.11                # crank radius, chosen (a bicycle's is 0.17)
PB_PEDAL = (0.11, 0.09, 0.035)                          # pedal block, chosen chunky
# the wheel housing behind the transom in side view (y, z), 0.5 m wide
PB_HOUSING = ((-1.06, 0.06), (-1.46, 0.06), (-1.50, 0.12), (-1.50, 0.28), (-1.45, 0.40),
              (-1.34, 0.47), (-1.20, 0.49), (-1.06, 0.49))
PB_HOUSING_HALF = 0.25
PB_WHEEL_C, PB_WHEEL_R = (-1.27, 0.10), 0.22            # the paddle wheel, six blades
PB_RUDDER = (-0.02, 0.02, -1.62, -1.48, -0.12, 0.30)
# the canopy: four posts and a flat top, chosen; its underside 1.6 m over
# the water clears a seated adult's head by about 0.4 m
PB_POSTS = ((0.60, 0.50), (-0.60, 0.50), (0.72, -0.62), (-0.72, -0.62))
PB_POST_R = 0.03
PB_CANOPY = dict(W=0.80, y_bow=0.72, y_stern=-0.92, bow=(0.25, 0.25, 4), stern=(0.25, 0.25, 4))
PB_CANOPY_Z = (1.60, 1.68)

# --- the kayaks -------------------------------------------------------------
# The map draws a kayak about 3.8 x 0.65 m. Chosen: the classes the 1990s
# rental fleets used, an 11 ft sit-on-top (Ocean Kayak Scrambler class) and
# a 13 ft 4 in tandem (Malibu Two XL class), inside the brief's 3-3.5 m and
# 4-4.5 m.
KS = dict(
    L=3.35, B=0.76,            # 11 ft by 30 in
    draft=0.10,                # chosen: one adult aboard
    deck=0.24,                 # the deck edge over the water midships (hull 0.34 deep)
    rocker=0.18, sheer_rise=0.08,      # the keel and the deck rise toward the ends
    sweep=0.16,                # and the keel sweeps up into a raked bow and stern, chosen
    # wells, (y from, y to, floor z): the seat, then the legs to the foot wall
    wells=((-0.62, -0.02, 0.05), (-0.02, 0.62, 0.09)),
    # moulded backrests, (y far, y near the seat, height over the deck)
    humps=((-0.95, -0.62, 0.07),),
    paddles=(0.35,),           # where the paddle lies across the rails
    grid=0.19,                 # station spacing, chosen for the budget
)
KT = dict(
    L=4.10, B=0.86, draft=0.11, deck=0.26, rocker=0.20, sheer_rise=0.08, sweep=0.18,
    wells=((-1.25, -0.65, 0.05), (-0.65, 0.00, 0.09), (0.25, 0.85, 0.05), (0.85, 1.45, 0.09)),
    humps=((-1.55, -1.25, 0.07), (0.00, 0.25, 0.07)),
    paddles=(1.15, -0.33),
    grid=0.24,
)
WELL_EDGE = 0.03               # stations either side of a well's end: a steep moulded wall
PADDLE_L = 2.20                # a 220 cm paddle, the sit-on-top rental length
PADDLE_SHAFT_R = 0.02
PADDLE_BLADE = (0.47, 0.17, 0.024)   # length, width, thickness, chosen chunky
HANDLE = (0.12, 0.06, 0.07)    # carry handle blocks at bow and stern, chosen

# --- the glass-bottom boat ----------------------------------------------------
# Read: "Glass-bottom boat (P), about 10 m, covered"; the map draws it
# 9.0 x 3.2 m. Chosen: the canopy launch type (benches down both sides facing
# a glass well in the floor, a flat roof on posts); the lagoon is "2 m deep at
# its lowest", tide +-0.9, so it draws 0.70 m.
GBB_L = 10.0
GBB_B = 3.20
GBB_BOW_RY = 2.80              # the bow's elliptical round in plan, chosen
GBB_STERN_R = 0.55
GBB_DRAFT = 0.70
GBB_BOOT = 0.05                # the bottom paint stops 5 cm over the waterline
GBB_SHEER = 0.92               # the gunwale's top over the water, chosen
GBB_FLOOR = 0.12               # the passenger floor over the water, chosen
GBB_RINGS = ((0.40, 1.10, 0.10, -GBB_DRAFT), (0.16, 0.55, 0.04, -0.58), (0.03, 0.18, 0.01, -0.35),
             (0.0, 0.0, 0.0, GBB_BOOT), (0.0, 0.0, 0.0, 0.80), (0.03, 0.03, 0.03, GBB_SHEER),
             (0.14, 0.14, 0.14, GBB_SHEER), (0.16, 0.16, 0.16, 0.88), (0.18, 0.18, 0.18, GBB_FLOOR))
GBB_RUBRAIL = ((0.02, 0.70), (-0.04, 0.705), (-0.065, 0.77), (-0.04, 0.835), (0.02, 0.84))
GBB_WELL = (-0.45, 0.45, -2.70, 2.30)       # the viewing well, 0.9 x 5.0 m, chosen
GBB_PANES = 4                               # glass slabs along the well
GBB_BAR_W = 0.10                            # the cross bars between them
GBB_GLASS_Z = (-0.66, -0.63)                # 3 cm slabs, 4 cm up from the bottom
GBB_BAR_Z = (-0.68, -0.60)
GBB_COAMING = (0.55, 0.42, -2.80, -2.67, 2.40, 2.27, 0.10, 0.40)   # outer x, inner x, y.., z..
GBB_BENCH = (1.02, 1.44, -3.05, 2.15, 0.10, GBB_FLOOR + 0.45)     # x in, x out, y, z: seat 0.45 up
GBB_BACKREST = (1.33, 1.44, -3.00, 2.10, 0.64, 0.86)
GBB_POST_X = 1.515                          # the middle of the gunwale's flat
GBB_POST_Y = (-4.30, -2.15, 0.0, 2.15)
GBB_POST_R = 0.05
GBB_ROOF = dict(W=1.68, y_bow=2.55, y_stern=-4.85, bow=(0.35, 0.35, 4), stern=(0.35, 0.35, 4))
GBB_ROOF_Z = (2.20, 2.32)                   # 2.08 m clear over the floor
GBB_LOCKER_Y = 2.45                         # the bow locker from here forward
GBB_LOCKER_TOP = 0.84
# the helm console in side view (y, z), 0.7 m wide, its sloped dash to the stern
GBB_CONSOLE = ((-3.40, 0.10), (-3.40, 1.02), (-3.52, 1.08), (-3.85, 0.96), (-3.85, 0.10))
GBB_CONSOLE_HALF = 0.35
GBB_WHEEL = (0.0, 0.82, 0.20)               # x, z, radius; on the console's aft face
GBB_STOOL = (-4.35, 0.62, 0.18)             # y, seat height, seat radius
GBB_SKEG = (-0.05, 0.05, -4.75, -3.10, -0.80, -0.68)
GBB_LIFERING = (3.40, 0.30, 0.065)          # y, radius, tube radius; on the bow locker

# --- the further variants (2026-10-03, "build all the offered variants") ----
# the four-seater: two adults and two kids; a 2.8 m hull, chosen, so a kids'
# bench fits behind the seats with 0.3 m for their legs
PB4_L = 2.80
PB4_SHIFT = (PB4_L - PB_L) / 2        # the bow's parts move forward this much, the stern's aft
# the kids' bench in side view (y, z): seat 0.22 m over the floor, its back
# against the stern, rising over the rim
PB4_KIDS_BENCH = ((-0.92, 0.10), (-0.92, 0.31), (-0.96, 0.34), (-1.12, 0.33), (-1.18, 0.36),
                  (-1.24, 0.64), (-1.30, 0.66), (-1.33, 0.60), (-1.33, 0.10))
PB4_KIDS_HALF = 0.56                  # inside the stern's rounded corners
# the tunnel boat: the map's 2.2 m overall over the bumper, the wheel in a
# slot through the hull under the armrest (which covers it), no housing
PB_BUMPER_PROUD = -min(d for d, _ in PB_BUMPER)
PBT_L = PB_L - 2 * PB_BUMPER_PROUD
PBT_SHIFT = (PBT_L - PB_L) / 2        # the bow deck moves aft with the bow
PBT_SLOT = (-0.11, 0.11, -0.80, -0.30)                  # inside the armrest's plan
PBT_WHEEL_C, PBT_WHEEL_R, PBT_WHEEL_HALF = (-0.55, -0.06), 0.20, 0.085
PBT_RUDDER = (-0.02, 0.02, -PBT_L / 2 - 0.045, -PBT_L / 2 + 0.015, -0.15, 0.20)
# the kayaks in other bright rental colours, chosen
KAYAK_COLOURS = {"kayak_single": ("lime", "orange", "teal"), "kayak_tandem": ("lime", "purple", "blue")}
# the electric launch: a small propeller on a shaft out of the skeg's aft
# end, just under the bottom, and a rudder hung under the transom, chosen
GBB_E_SHAFT = (-4.78, -4.70, -0.80, 0.025)             # y from, y to, z, radius
GBB_E_PROP = (-4.82, -4.77, 0.095)                      # y from, y to, radius
GBB_E_RUDDER = (-0.015, 0.015, -5.00, -4.88, -0.88, -0.33)
# the bow helm: console, wheel and stool forward ahead of the well, the
# locker shortened in front of them, a bench across the stern
GBB_BH_SHIFT = 7.25
GBB_BH_LOCKER_Y = 3.95
GBB_BH_RING_SHIFT = 0.95
GBB_BH_STERN_BENCH = (-1.20, 1.20, -4.84, -4.40, GBB_FLOOR - 0.02, GBB_FLOOR + 0.45)
# the side gate: 0.8 m in the starboard bulwark between the posts at -2.15
# and 0, the bulwark cut down to a sill 0.18 m over the floor
GBB_GATE = (-1.475, -0.675)
GBB_GATE_SILL = 0.30
GBB_GATE_LEAF = (1.47, 1.53)                            # x: set in from both faces
GBB_GATE_RAIL_GAP = 0.03                                # the rubrail stops short each side
_INNER = GBB_RINGS[7][0] + (GBB_RINGS[8][0] - GBB_RINGS[7][0]) * \
    (GBB_RINGS[7][3] - GBB_GATE_SILL) / (GBB_RINGS[7][3] - GBB_RINGS[8][3])
GBB_GATE_RINGS = GBB_RINGS[:4] + ((0.0, 0.0, 0.0, GBB_GATE_SILL),) + GBB_RINGS[4:8] + \
    ((_INNER, _INNER, _INNER, GBB_GATE_SILL),) + GBB_RINGS[8:]
GBB_GATE_NOTCH = (4, 9)               # the rings the cut runs between: the sills


def srgb(hex6, alpha=1.0):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (alpha,)


COLOURS = {
    # the paddle boat: white moulded hull, the map's paddle-boat orange inside
    f"{PROP}_pb_hull": srgb("f6f4ee"),
    f"{PROP}_pb_moulding": srgb("e8913a"),      # the map's .paddle colour
    f"{PROP}_pb_bumper": srgb("33363a"),
    f"{PROP}_pb_metal": srgb("9aa1a8"),
    f"{PROP}_pb_canopy": srgb("1f9e9a"),
    # the kayaks: the map's two kayak colours, a paddle's alloy and blades
    f"{PROP}_kayak_yellow": srgb("f0c24b"),     # the map's .kayak.k1
    f"{PROP}_kayak_red": srgb("d9503f"),        # the map's .kayak.k2
    f"{PROP}_kayak_handle": srgb("2a2a2c"),
    f"{PROP}_kayak_lime": srgb("8cc63f"),
    f"{PROP}_kayak_orange": srgb("f28c28"),
    f"{PROP}_kayak_teal": srgb("1fa3a3"),
    f"{PROP}_kayak_purple": srgb("7b4fb3"),
    f"{PROP}_kayak_blue": srgb("2f6fd6"),
    f"{PROP}_paddle_shaft": srgb("b8bec4"),
    f"{PROP}_paddle_blade": srgb("2b5fb4"),
    # the glass-bottom boat: the map's cream hull and teal-blue trim
    f"{PROP}_gbb_hull": srgb("f5f2e8"),         # the map's .gbb fill
    f"{PROP}_gbb_trim": srgb("1d5a73"),         # the map's .gbb stroke
    f"{PROP}_gbb_bottom": srgb("9a3a2e"),       # bottom paint
    f"{PROP}_gbb_liner": srgb("e9ece6"),        # the inside of the bulwarks and the well
    f"{PROP}_gbb_floor": srgb("b9bcb6"),        # non-skid
    f"{PROP}_gbb_wood": srgb("a8703c"),         # benches and backrests
    f"{PROP}_gbb_glass": srgb("9fd6d2", 0.35),
    f"{PROP}_gbb_metal": srgb("c8ccd0"),        # posts, bars
    f"{PROP}_gbb_motor": srgb("2b2f33"),
    f"{PROP}_gbb_lifering": srgb("f06a2a"),
}


def material(name, colour=None):
    """A stand-in material by name. Colours in COLOURS are the builder's: a
    rerun resets them (a material survives `--replace`)."""
    mat = bpy.data.materials.get(name)
    rgba = COLOURS.get(name, colour)
    if mat is None:
        mat = bpy.data.materials.new(name)
        if mat.node_tree is None:
            mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
    if bsdf is not None and rgba is not None:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.6 if rgba[3] < 1.0 else 0.8
        bsdf.inputs["Alpha"].default_value = rgba[3]
        mat.diffuse_color = rgba
    return mat


def M(surface):
    return material(f"{PROP}_{surface}")


# --- building blocks -------------------------------------------------------

def finish(name, bm, coll, mats, variant, unwrap="facets"):
    """A bmesh into an object in `coll`, tagged, smooth with creases over
    SHARP, no collision this pass."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=SHARP)
    for m in mats:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    obj["kyt_unwrap"] = unwrap
    obj["kyt_variant"] = variant
    obj["kyt_collision"] = "none"
    coll.objects.link(obj)
    return obj


def linked(src, name, coll, variant, location=None):
    """A linked copy of a part: one mesh, so reshaping one reshapes both."""
    dup = src.copy()
    dup.name = name
    dup["kyt_variant"] = variant
    if location is not None:
        dup.location = location
    coll.objects.link(dup)
    return dup


def prism_into(bm, poly, axis, lo, hi, mat=0):
    """A 2D polygon extruded along `axis` into `bm` ('x' takes (y, z) pairs,
    'y' takes (x, z), 'z' takes (x, y))."""
    def at(a, b, t):
        return {"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis]

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    faces = [bm.faces.new(near), bm.faces.new(list(reversed(far)))]
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((near[i], near[j], far[j], far[i])))
    for f in faces:
        f.material_index = mat
    return faces


def box_into(bm, x0, x1, y0, y1, z0, z1, mat=0):
    assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
    return prism_into(bm, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1, mat)


def ngon(cx, cy, r, n=8, phase=None):
    """A regular n-gon's points; by default a flat side faces each axis."""
    phase = math.pi / n if phase is None else phase
    return [(cx + r * math.cos(phase + math.tau * i / n), cy + r * math.sin(phase + math.tau * i / n))
            for i in range(n)]


def part(name, coll, mats, variant, build, unwrap="facets"):
    """A part from a function that fills a fresh bmesh."""
    bm = bmesh.new()
    build(bm)
    return finish(name, bm, coll, mats, variant, unwrap)


# --- plan outlines and lofts ------------------------------------------------

def plan_points(spec, dx, dbow=None, dstern=None, side_y=()):
    """A hull's plan outline, anticlockwise from above: straight sides at
    +-W, an elliptical corner each side of the bow and of the stern, inset by
    `dx` at the sides, `dbow` at the bow and `dstern` at the stern (negative
    is outward). A bow whose corner radius is the half-beam is one half
    ellipse; every inset of one spec has the same points in the same order,
    so rings of it loft face to face. `side_y` adds points at those y on the
    starboard straight side (a gate's ends), the same y on every ring."""
    dbow = dx if dbow is None else dbow
    dstern = dx if dstern is None else dstern
    w = spec["W"] - dx
    yb, ys = spec["y_bow"] - dbow, spec["y_stern"] + dstern
    brx, bry, bn = spec["bow"]
    srx, sry, sn = spec["stern"]
    brx, bry, srx, sry = brx - dx, bry - dbow, srx - dx, sry - dstern
    assert min(brx, bry, srx, sry) > 0.01, ("inset past a corner", spec, dx, dbow, dstern)
    pts = []

    def arc(cx, cy, rx, ry, a0, a1, n):
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))

    arc(w - srx, ys + sry, srx, sry, -math.pi / 2, 0.0, sn)
    for y in sorted(side_y):
        assert ys + sry < y < yb - bry, ("off the straight side", y)
        pts.append((w, y))
    arc(w - brx, yb - bry, brx, bry, 0.0, math.pi / 2, bn)
    arc(-(w - brx), yb - bry, brx, bry, math.pi / 2, math.pi, bn)
    arc(-(w - srx), ys + sry, srx, sry, math.pi, 1.5 * math.pi, sn)
    out = []
    for p in pts:
        if not out or (Vector(p) - Vector(out[-1])).length > 1e-6:
            out.append(p)
    if (Vector(out[0]) - Vector(out[-1])).length < 1e-6:
        out.pop()
    return out


def clip_poly(pts, y_cut, keep_above=True):
    """A polygon cut by the line y = y_cut (Sutherland-Hodgman)."""
    def inside(p):
        return p[1] >= y_cut if keep_above else p[1] <= y_cut

    out = []
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        if inside(p):
            out.append(p)
        if inside(p) != inside(q):
            t = (y_cut - p[1]) / (q[1] - p[1])
            out.append((p[0] + (q[0] - p[0]) * t, y_cut))
    return out


def tub(bm, spec, rings, band_mat, first_mat, last_mat, hole=None, shaft_mat=0,
        side_y=(), notch=None, notch_mat=0):
    """A hull lofted through `rings`, (dx, dbow, dstern, z) insets of one
    plan outline, closed by a flat cap on the first and the last ring. The
    caps meet the bands at the rings' edges, so the whole is one closed
    shell. `hole` (x0, x1, y0, y1) cuts the same rectangle through both caps
    and joins them with a shaft: the glass boat's well. `notch` (ring from,
    ring to) cuts the bands between those rings away along the starboard
    side between the two `side_y` points and closes the cut with a sill
    face and an end wall each side: a gate in the bulwark."""
    loops = []
    for dx, dbow, dstern, z in rings:
        loops.append([bm.verts.new((x, y, z)) for x, y in plan_points(spec, dx, dbow, dstern, side_y)])
    n = len(loops[0])
    assert all(len(lp) == n for lp in loops)
    k0 = None
    if notch:
        k0 = next(k for k, vx in enumerate(loops[0]) if vx.co.x > 0 and abs(vx.co.y - min(side_y)) < 1e-5)
    for i in range(len(loops) - 1):
        a, b = loops[i], loops[i + 1]
        for k in range(n):
            if notch and k == k0 and notch[0] <= i < notch[1]:
                continue
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            f.material_index = band_mat(i)
    if notch:
        lo, hi = notch
        k1 = k0 + 1
        faces = [bm.faces.new((loops[lo][k0], loops[lo][k1], loops[hi][k1], loops[hi][k0])),
                 bm.faces.new([loops[i][k0] for i in range(lo, hi + 1)]),
                 bm.faces.new([loops[i][k1] for i in range(hi, lo - 1, -1)])]
        for f in faces:
            f.material_index = notch_mat
    holes = []
    for lp, z, mat in ((loops[0], rings[0][3], first_mat), (loops[-1], rings[-1][3], last_mat)):
        edges = [bm.edges.get((lp[k], lp[(k + 1) % n])) for k in range(n)]
        hv = []
        if hole:
            x0, x1, y0, y1 = hole
            hv = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
            edges += [bm.edges.new((hv[k], hv[(k + 1) % 4])) for k in range(4)]
        made = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
        for f in made["geom"]:
            if isinstance(f, bmesh.types.BMFace):
                f.material_index = mat
        holes.append(hv)
    if hole:
        lo, hi = holes
        for k in range(4):
            f = bm.faces.new((lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]))
            f.material_index = shaft_mat
    return bm


def band(bm, spec, profile, mat=0, side_y=()):
    """A closed band round a hull (a bumper, a rubrail): the plan outline
    swept round a closed profile of (inset, z) points. With two `side_y`
    points the band stops at them, open on the starboard side between, each
    end capped by the profile."""
    loops = [[bm.verts.new((x, y, z)) for x, y in plan_points(spec, d, side_y=side_y)] for d, z in profile]
    n, m = len(loops[0]), len(loops)
    k0 = None
    if side_y:
        k0 = next(k for k, vx in enumerate(loops[0]) if vx.co.x > 0 and abs(vx.co.y - min(side_y)) < 1e-5)
    for i in range(m):
        a, b = loops[i], loops[(i + 1) % m]
        for k in range(n):
            if k == k0:
                continue
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            f.material_index = mat
    if side_y:
        for f in (bm.faces.new([lp[k0] for lp in loops]), bm.faces.new([lp[k0 + 1] for lp in reversed(loops)])):
            f.material_index = mat
    return bm


def slab(bm, spec, d, z0, z1, mat=0, y_cut=None):
    """A flat slab on a plan outline (inset `d`), optionally only forward of
    `y_cut`."""
    pts = plan_points(spec, d)
    if y_cut is not None:
        pts = clip_poly(pts, y_cut)
    return prism_into(bm, pts, "z", z0, z1, mat)


def station_loft(bm, sections, tips, mat=0):
    """Sections along the length (aft to forward), each a closed loop of the
    same number of points, joined face to face; each end closes in a fan to
    its tip point."""
    rows = [[bm.verts.new(p) for p in s] for s in sections]
    n = len(rows[0])
    for a, b in zip(rows, rows[1:]):
        for k in range(n):
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            f.material_index = mat
    for row, tip in ((rows[0], tips[0]), (rows[-1], tips[1])):
        t = bm.verts.new(tip)
        for k in range(n):
            f = bm.faces.new((row[k], row[(k + 1) % n], t))
            f.material_index = mat
    return bm


# --- the paddle boat -----------------------------------------------------------

def pb_spec(length=PB_L):
    return dict(W=PB_B / 2, y_bow=length / 2, y_stern=-length / 2,
                bow=(PB_B / 2, PB_BOW_RY, 6), stern=(PB_STERN_R, PB_STERN_R, 4))


def build_paddle_boat(coll, v):
    spec = pb_spec()
    hull, moulding, bumper, metal = M("pb_hull"), M("pb_moulding"), M("pb_bumper"), M("pb_metal")
    parts = {}
    # the tub: white outside and across the rim, the orange moulding inside
    parts["hull"] = part(f"{v}_hull", coll, [hull, moulding], v,
                         lambda bm: tub(bm, spec, PB_RINGS, lambda i: 0 if i < 5 else 1, 0, 1))
    parts["bumper"] = part(f"{v}_bumper", coll, [bumper], v, lambda bm: band(bm, spec, PB_BUMPER))
    # the bow deck fills the bow inside the rim, lapping into the walls
    parts["bow_deck"] = part(f"{v}_bow_deck", coll, [moulding], v,
                             lambda bm: slab(bm, spec, 0.12, 0.10, PB_BOWDECK_TOP, y_cut=PB_BOWDECK_Y))
    parts["console"] = part(f"{v}_pedal_console", coll, [moulding], v, lambda bm: box_into(bm, *PB_CONSOLE))

    def pedals(bm):
        prism_into(bm, ngon(PB_AXLE_Y, PB_AXLE_Z, PB_AXLE_R), "x", -0.655, 0.655)
        for side in (1, -1):
            for k, (arm_x, foot_dir, up) in enumerate(((PB_SEAT_X - 0.065, -1, 1), (PB_SEAT_X + 0.065, 1, -1))):
                ax = side * arm_x
                end_z = PB_AXLE_Z + up * PB_CRANK
                z0, z1 = sorted((PB_AXLE_Z, end_z + up * 0.01))
                box_into(bm, ax - 0.015, ax + 0.015, PB_AXLE_Y - 0.025, PB_AXLE_Y + 0.025, z0, z1)
                px, py, pz = PB_PEDAL
                inner = ax + side * foot_dir * -0.005           # 1 cm into the arm
                outer = ax + side * foot_dir * (px - 0.005)
                x0, x1 = sorted((inner, outer))
                box_into(bm, x0, x1, PB_AXLE_Y - py / 2, PB_AXLE_Y + py / 2, end_z - pz / 2, end_z + pz / 2, 1)
    parts["pedals"] = part(f"{v}_pedals", coll, [metal, bumper], v, pedals)

    def seat(bm):
        prism_into(bm, PB_SEAT, "x", -PB_SEAT_HALF, PB_SEAT_HALF)
    parts["seat_starboard"] = part(f"{v}_seat_starboard", coll, [moulding], v, seat)
    parts["seat_starboard"].location = (PB_SEAT_X, 0.0, 0.0)
    parts["seat_port"] = linked(parts["seat_starboard"], f"{v}_seat_port", coll, v, (-PB_SEAT_X, 0.0, 0.0))
    parts["armrest"] = part(f"{v}_armrest", coll, [moulding], v, lambda bm: box_into(bm, *PB_ARMREST))

    def tiller(bm):
        box_into(bm, -0.0175, 0.0175, PB_TILLER_Y - 0.0175, PB_TILLER_Y + 0.0175, PB_ARMREST[5] - 0.02, PB_TILLER_TOP, 0)
        box_into(bm, -0.035, 0.035, PB_TILLER_Y - 0.035, PB_TILLER_Y + 0.035, PB_TILLER_TOP - 0.02, PB_TILLER_TOP + 0.06, 1)
    parts["tiller"] = part(f"{v}_tiller", coll, [metal, bumper], v, tiller)
    parts["housing"] = part(f"{v}_wheel_housing", coll, [moulding], v,
                            lambda bm: prism_into(bm, PB_HOUSING, "x", -PB_HOUSING_HALF, PB_HOUSING_HALF))

    def wheel(bm):
        cy, cz = PB_WHEEL_C
        prism_into(bm, ngon(cy, cz, 0.07), "x", -0.19, 0.19)
        for k in range(6):
            a = math.radians(30 + 60 * k)
            ca, sa = math.cos(a), math.sin(a)
            quad = [(0.05, -0.0125), (PB_WHEEL_R, -0.0125), (PB_WHEEL_R, 0.0125), (0.05, 0.0125)]
            poly = [(cy + u * ca - w * sa, cz + u * sa + w * ca) for u, w in quad]
            prism_into(bm, poly, "x", -0.18, 0.18)
    parts["wheel"] = part(f"{v}_paddle_wheel", coll, [moulding], v, wheel)
    parts["rudder"] = part(f"{v}_rudder", coll, [moulding], v, lambda bm: box_into(bm, *PB_RUDDER))
    return parts


def build_canopy(coll, v):
    canvas, metal = M("pb_canopy"), M("pb_metal")
    post = part(f"{v}_post_0", coll, [metal], v,
                lambda bm: prism_into(bm, ngon(0.0, 0.0, PB_POST_R), "z", 0.40, PB_CANOPY_Z[0] + 0.02),
                unwrap="lathe")
    x, y = PB_POSTS[0]
    post.location = (x, y, 0.0)
    for i, (x, y) in enumerate(PB_POSTS[1:], 1):
        linked(post, f"{v}_post_{i}", coll, v, (x, y, 0.0))
    part(f"{v}_canopy_top", coll, [canvas], v, lambda bm: slab(bm, PB_CANOPY, 0.0, *PB_CANOPY_Z))


# --- the kayaks ------------------------------------------------------------------

def kayak_profile(K, y):
    """The kayak's numbers at station y: half-beam, keel, deck edge, the
    well's weight and floor, the backrest hump."""
    h = K["L"] / 2
    s = max(-1.0, min(1.0, y / h))
    hb = K["B"] / 2 * max(1.0 - abs(s) ** 2.2, 0.0) ** 0.5
    zk = -K["draft"] + K["rocker"] * s ** 4 + K["sweep"] * s ** 12
    zs = K["deck"] + K["sheer_rise"] * s ** 4
    w, zr = 0.0, zs
    for y0, y1, floor in K["wells"]:
        if y0 - 1e-9 <= y <= y1 + 1e-9:
            w, zr = 1.0, floor
    hump = 0.0
    for far, near, height in K["humps"]:
        lo, hi = sorted((far, near))
        if lo <= y <= hi:
            t = abs(near - y) / abs(near - far)
            hump = max(hump, height * (1.0 - t * t))
    return hb, zk, zs, w, zr, hump


def kayak_section(K, y):
    """One cross-section, 18 points round from the keel: the starboard
    bottom, bilge and side, the rounded deck edge, the rail, the well's wall
    and floor (or the crowned deck where there is no well), and the port side
    back down."""
    hb, zk, zs, w, zr, hump = kayak_profile(K, y)
    H = zs - zk

    def lerp(a, b):
        return a + (b - a) * w

    half = [
        (0.45 * hb, zk + 0.05 * H),
        (0.80 * hb, zk + 0.20 * H),
        (0.97 * hb, zk + 0.48 * H),
        (1.00 * hb, zk + 0.74 * H),
        (0.95 * hb, zs),
        (0.80 * hb, zs + 0.02),
        (0.62 * hb, zs + 0.018 + 0.5 * hump),
        (0.50 * hb, lerp(zs + 0.03 + hump, zr)),    # straight down: no fold at a well's end
    ]
    top = lerp(zs + 0.035 + hump, zr - 0.005)
    pts = [(0.0, y, zk)] + [(x, y, z) for x, z in half] + [(0.0, y, top)]
    pts += [(-x, y, z) for x, z in reversed(half)]
    return pts


def kayak_stations(K):
    """Stations aft to forward: an even grid, a pair close either side of
    every well end and hump end, and three toward each tip."""
    h = K["L"] / 2
    edges = set()
    for y0, y1, _ in K["wells"]:
        edges.update((y0, y1))
    marks = set()
    for e in edges:
        marks.update((e - WELL_EDGE, e + WELL_EDGE))
    for far, near, _ in K["humps"]:
        marks.add(far)
        marks.add((far + near) / 2)
    n = max(2, int(round(1.8 * h / K["grid"])))
    grid = [-0.9 * h + 1.8 * h * i / n for i in range(n + 1)]
    ys = set(marks)
    for g in grid:
        if all(abs(g - m) > 0.6 * K["grid"] / 2 for m in marks):
            ys.add(g)
    for s in (0.95, 0.985):
        ys.update((s * h, -s * h))
    return sorted(ys)


def kayak_tip(K, end):
    h = K["L"] / 2
    _, zk, zs, _, _, _ = kayak_profile(K, end * h)
    return (0.0, end * h, (zk + zs) / 2 + 0.02)


def rail_top(K, y):
    hb, zk, zs, w, zr, hump = kayak_profile(K, y)
    return zs + 0.02


def build_paddle(coll, v):
    """A 220 cm paddle lying flat: an octagonal shaft through two flat
    blades, centred on its own origin."""
    shaft, blade = M("paddle_shaft"), M("paddle_blade")
    bl, bw, bt = PADDLE_BLADE
    half = PADDLE_L / 2

    def build(bm):
        neck = half - bl
        prism_into(bm, ngon(0.0, 0.0, PADDLE_SHAFT_R), "x", -(neck + 0.03), neck + 0.03, 0)
        for side in (1, -1):
            out = [(neck, 0.035), (neck + 0.08, bw / 2), (half - 0.05, bw / 2), (half, bw / 2 - 0.04),
                   (half, -bw / 2 + 0.04), (half - 0.05, -bw / 2), (neck + 0.08, -bw / 2), (neck, -0.035)]
            if side < 0:
                out = [(-x, y) for x, y in reversed(out)]
            prism_into(bm, out, "z", -bt / 2, bt / 2, 1)
    return part(f"{v}_paddle", coll, [shaft, blade], v, build)


def build_kayak(coll, v, K, colour, paddle_src=None):
    body, black = M(colour), M("kayak_handle")
    stations = kayak_stations(K)
    sections = [kayak_section(K, y) for y in stations]
    parts = {"hull": part(f"{v}_hull", coll, [body], v,
                          lambda bm: station_loft(bm, sections, (kayak_tip(K, -1), kayak_tip(K, 1))))}
    h = K["L"] / 2

    def handles(bm):
        hx, hy, hz = HANDLE
        for end in (1, -1):
            y = end * (h - 0.16)
            _, _, zs, _, _, _ = kayak_profile(K, y)
            box_into(bm, -hx / 2, hx / 2, y - hy / 2, y + hy / 2, zs - 0.02, zs + hz)
    parts["handles"] = part(f"{v}_handles", coll, [black], v, handles)
    flat = PADDLE_SHAFT_R * math.cos(math.pi / 8)       # the octagon's flat under the shaft
    for i, y in enumerate(K["paddles"]):
        z = rail_top(K, y) + flat - 0.01                # resting 1 cm into the rails
        if paddle_src is None:
            paddle_src = build_paddle(coll, v)
            paddle_src.location = (0.0, y, z)
            parts["paddle_0"] = paddle_src
        else:
            parts[f"paddle_{i}"] = linked(paddle_src, f"{v}_paddle_{i}", coll, v, (0.0, y, z))
    return parts, sections, stations, paddle_src


# --- the glass-bottom boat -------------------------------------------------------

def gbb_spec():
    return dict(W=GBB_B / 2, y_bow=GBB_L / 2, y_stern=-GBB_L / 2,
                bow=(GBB_B / 2, GBB_BOW_RY, 8), stern=(GBB_STERN_R, GBB_STERN_R, 4))


def gbb_pane_slots():
    """The glass openings along the well between the bars, each (y0, y1),
    and the bars' centres."""
    x0, x1, y0, y1 = GBB_WELL
    open_len = (y1 - y0 - (GBB_PANES - 1) * GBB_BAR_W) / GBB_PANES
    slots, bars, y = [], [], y0
    for k in range(GBB_PANES):
        slots.append((y, y + open_len))
        y += open_len
        if k < GBB_PANES - 1:
            bars.append(y + GBB_BAR_W / 2)
            y += GBB_BAR_W
    return slots, bars


def build_gbb(coll, v):
    spec = gbb_spec()
    hull, trim, bottom, liner, floor = M("gbb_hull"), M("gbb_trim"), M("gbb_bottom"), M("gbb_liner"), M("gbb_floor")
    wood, glass, metal, motor, ring = M("gbb_wood"), M("gbb_glass"), M("gbb_metal"), M("gbb_motor"), M("gbb_lifering")
    parts = {}

    def band_mat(i):
        z_top = GBB_RINGS[i + 1][3]
        if z_top <= GBB_BOOT + 1e-9:
            return 1                     # bottom paint up to the boot top
        return 0 if i < 5 else 2         # the outside; the rim and the inside are the liner
    parts["hull"] = part(f"{v}_hull", coll, [hull, bottom, liner, floor], v,
                         lambda bm: tub(bm, spec, GBB_RINGS, band_mat, 1, 3, hole=GBB_WELL, shaft_mat=2))
    parts["rubrail"] = part(f"{v}_rubrail", coll, [trim], v, lambda bm: band(bm, spec, GBB_RUBRAIL))
    parts["skeg"] = part(f"{v}_skeg", coll, [bottom], v, lambda bm: box_into(bm, *GBB_SKEG))

    # the well: four glass slabs between three cross bars, set in the bottom
    x0, x1, wy0, wy1 = GBB_WELL
    slots, bars = gbb_pane_slots()
    pane_len = slots[0][1] - slots[0][0] + 0.04       # 2 cm into a bar or the shaft each end
    pane = part(f"{v}_glass_0", coll, [glass], v,
                lambda bm: box_into(bm, x0 - 0.02, x1 + 0.02, -pane_len / 2, pane_len / 2, *GBB_GLASS_Z),
                unwrap="planar")
    pane.location = (0.0, (slots[0][0] + slots[0][1]) / 2, 0.0)
    for k, (a, b) in enumerate(slots[1:], 1):
        linked(pane, f"{v}_glass_{k}", coll, v, (0.0, (a + b) / 2, 0.0))
    bar = part(f"{v}_bar_0", coll, [metal], v,
               lambda bm: box_into(bm, x0 - 0.03, x1 + 0.03, -GBB_BAR_W / 2, GBB_BAR_W / 2, *GBB_BAR_Z))
    bar.location = (0.0, bars[0], 0.0)
    for k, y in enumerate(bars[1:], 1):
        linked(bar, f"{v}_bar_{k}", coll, v, (0.0, y, 0.0))

    def coaming(bm):
        ox, ix, oy0, iy0, oy1, iy1, z0, z1 = GBB_COAMING
        outer = [(-ox, oy0), (ox, oy0), (ox, oy1), (-ox, oy1)]
        inner = [(-ix, iy0), (ix, iy0), (ix, iy1), (-ix, iy1)]
        lo_o = [bm.verts.new((x, y, z0)) for x, y in outer]
        hi_o = [bm.verts.new((x, y, z1)) for x, y in outer]
        lo_i = [bm.verts.new((x, y, z0)) for x, y in inner]
        hi_i = [bm.verts.new((x, y, z1)) for x, y in inner]
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((hi_o[k], hi_o[j], hi_i[j], hi_i[k]))
            bm.faces.new((lo_o[k], lo_i[k], lo_i[j], lo_o[j]))
            bm.faces.new((lo_o[k], lo_o[j], hi_o[j], hi_o[k]))
            bm.faces.new((lo_i[k], hi_i[k], hi_i[j], lo_i[j]))
    parts["coaming"] = part(f"{v}_well_coaming", coll, [trim], v, coaming)

    # the benches and backrests down each side, facing the well
    bx0, bx1, by0, by1, bz0, bz1 = GBB_BENCH
    bench = part(f"{v}_bench_starboard", coll, [wood], v,
                 lambda bm: box_into(bm, -(bx1 - bx0) / 2, (bx1 - bx0) / 2, by0, by1, bz0, bz1))
    bench.location = ((bx0 + bx1) / 2, 0.0, 0.0)
    linked(bench, f"{v}_bench_port", coll, v, (-(bx0 + bx1) / 2, 0.0, 0.0))
    rx0, rx1, ry0, ry1, rz0, rz1 = GBB_BACKREST
    back = part(f"{v}_backrest_starboard", coll, [wood], v,
                lambda bm: box_into(bm, -(rx1 - rx0) / 2, (rx1 - rx0) / 2, ry0, ry1, rz0, rz1))
    back.location = ((rx0 + rx1) / 2, 0.0, 0.0)
    linked(back, f"{v}_backrest_port", coll, v, (-(rx0 + rx1) / 2, 0.0, 0.0))

    # the canopy: eight posts on the gunwale, a flat roof
    post = part(f"{v}_post_0", coll, [metal], v,
                lambda bm: prism_into(bm, ngon(0.0, 0.0, GBB_POST_R), "z", GBB_SHEER - 0.02, GBB_ROOF_Z[0] + 0.02),
                unwrap="lathe")
    spots = [(sx * GBB_POST_X, y) for sx in (1, -1) for y in GBB_POST_Y]
    post.location = (spots[0][0], spots[0][1], 0.0)
    for k, (x, y) in enumerate(spots[1:], 1):
        linked(post, f"{v}_post_{k}", coll, v, (x, y, 0.0))
    parts["roof"] = part(f"{v}_canopy_roof", coll, [trim], v, lambda bm: slab(bm, GBB_ROOF, 0.0, *GBB_ROOF_Z))

    # the bow locker, filling the bow inside the bulwarks, a life ring on it
    parts["locker"] = part(f"{v}_bow_locker", coll, [liner], v,
                           lambda bm: slab(bm, spec, 0.15, GBB_FLOOR - 0.02, GBB_LOCKER_TOP, y_cut=GBB_LOCKER_Y))

    def lifering(bm):
        yc, R, r = GBB_LIFERING
        zc = GBB_LOCKER_TOP + r - 0.01
        nu, nv = 12, 6
        rows = []
        for i in range(nu):
            a = math.tau * i / nu
            rows.append([bm.verts.new(((R + r * math.cos(math.tau * j / nv)) * math.cos(a),
                                       yc + (R + r * math.cos(math.tau * j / nv)) * math.sin(a),
                                       zc + r * math.sin(math.tau * j / nv))) for j in range(nv)])
        for i in range(nu):
            for j in range(nv):
                a, b = rows[i], rows[(i + 1) % nu]
                bm.faces.new((a[j], b[j], b[(j + 1) % nv], a[(j + 1) % nv]))
    parts["lifering"] = part(f"{v}_life_ring", coll, [ring], v, lifering, unwrap="lathe")

    # the helm at the stern: console, wheel, a stool for the skipper
    parts["console"] = part(f"{v}_helm_console", coll, [liner], v,
                            lambda bm: prism_into(bm, GBB_CONSOLE, "x", -GBB_CONSOLE_HALF, GBB_CONSOLE_HALF))
    wx, wz, wr = GBB_WHEEL
    aft = GBB_CONSOLE[-1][0]
    parts["wheel"] = part(f"{v}_helm_wheel", coll, [motor], v,
                          lambda bm: prism_into(bm, ngon(wx, wz, wr), "y", aft - 0.05, aft + 0.02),
                          unwrap="planar")

    def stool(bm):
        sy, sz, sr = GBB_STOOL
        prism_into(bm, ngon(0.0, sy, 0.05), "z", GBB_FLOOR - 0.02, sz + 0.02, 0)
        prism_into(bm, ngon(0.0, sy, sr), "z", sz, sz + 0.08, 1)
    parts["stool"] = part(f"{v}_helm_stool", coll, [metal, motor], v, stool)

    def outboard(bm):
        box_into(bm, -0.10, 0.10, -5.12, -4.97, 0.70, 0.98)                       # transom clamp
        prism_into(bm, [(-5.08, 0.78), (-5.50, 0.78), (-5.58, 0.92), (-5.56, 1.16), (-5.46, 1.28),
                        (-5.18, 1.30), (-5.08, 1.20)], "x", -0.20, 0.20)          # the cowling
        box_into(bm, -0.07, 0.07, -5.40, -5.22, -0.50, 0.80)                      # the leg
        prism_into(bm, ngon(0.0, -0.52, 0.075), "y", -5.48, -5.12)                # gear case
        box_into(bm, -0.015, 0.015, -5.38, -5.24, -0.78, -0.55)                   # skeg
        prism_into(bm, ngon(0.0, -0.52, 0.17), "y", -5.52, -5.46)                 # the propeller, a disc
    parts["outboard"] = part(f"{v}_outboard", coll, [motor], v, outboard)
    return parts


# --- the further variants ---------------------------------------------------------

def renamed(src, old, new):
    return src.name.replace(f"{old}_", f"{new}_", 1)


def build_paddle_boat_four(coll, v, pb):
    """Two adults and two kids: a 2.8 m hull and bumper of its own, the
    first paddle boat's parts moved with the bow and the stern, a kids'
    bench behind the seats."""
    spec = pb_spec(PB4_L)
    hull, moulding, bumper = M("pb_hull"), M("pb_moulding"), M("pb_bumper")
    parts = {"hull": part(f"{v}_hull", coll, [hull, moulding], v,
                          lambda bm: tub(bm, spec, PB_RINGS, lambda i: 0 if i < 5 else 1, 0, 1)),
             "bumper": part(f"{v}_bumper", coll, [bumper], v, lambda bm: band(bm, spec, PB_BUMPER))}
    forward = ("bow_deck", "console", "pedals", "seat_starboard", "seat_port", "armrest", "tiller")
    for key in forward + ("housing", "wheel", "rudder"):
        src = pb[key]
        dy = PB4_SHIFT if key in forward else -PB4_SHIFT
        parts[key] = linked(src, renamed(src, "paddle_boat", v), coll, v, src.location + Vector((0.0, dy, 0.0)))
    parts["kids_bench"] = part(f"{v}_kids_bench", coll, [moulding], v,
                               lambda bm: prism_into(bm, PB4_KIDS_BENCH, "x", -PB4_KIDS_HALF, PB4_KIDS_HALF))
    return parts


def build_paddle_boat_tunnel(coll, v, pb):
    """The map's 2.2 m overall: a shorter hull with the wheel in a slot
    under the armrest, no housing, a rudder on the transom."""
    spec = pb_spec(PBT_L)
    hull, moulding, bumper = M("pb_hull"), M("pb_moulding"), M("pb_bumper")
    parts = {"hull": part(f"{v}_hull", coll, [hull, moulding], v,
                          lambda bm: tub(bm, spec, PB_RINGS, lambda i: 0 if i < 5 else 1, 0, 1,
                                         hole=PBT_SLOT, shaft_mat=1)),
             "bumper": part(f"{v}_bumper", coll, [bumper], v, lambda bm: band(bm, spec, PB_BUMPER))}
    parts["bow_deck"] = linked(pb["bow_deck"], renamed(pb["bow_deck"], "paddle_boat", v), coll, v,
                               (0.0, PBT_SHIFT, 0.0))
    for key in ("console", "pedals", "seat_starboard", "seat_port", "armrest", "tiller"):
        parts[key] = linked(pb[key], renamed(pb[key], "paddle_boat", v), coll, v)

    def wheel(bm):
        cy, cz = PBT_WHEEL_C
        prism_into(bm, ngon(cy, cz, 0.06), "x", -(PBT_WHEEL_HALF + 0.005), PBT_WHEEL_HALF + 0.005)
        for k in range(6):
            a = math.radians(30 + 60 * k)
            ca, sa = math.cos(a), math.sin(a)
            quad = [(0.05, -0.0125), (PBT_WHEEL_R, -0.0125), (PBT_WHEEL_R, 0.0125), (0.05, 0.0125)]
            poly = [(cy + u * ca - w * sa, cz + u * sa + w * ca) for u, w in quad]
            prism_into(bm, poly, "x", -PBT_WHEEL_HALF, PBT_WHEEL_HALF)
    parts["wheel"] = part(f"{v}_paddle_wheel", coll, [moulding], v, wheel)
    parts["rudder"] = part(f"{v}_rudder", coll, [moulding], v, lambda bm: box_into(bm, *PBT_RUDDER))
    return parts


def build_kayak_colour(coll, v, src_variant, colour):
    """Every part a linked copy; the hull wears its colour as an object
    material, so the shape is shared and the colour is not."""
    parts = {}
    for src in variant_objects(src_variant):
        dup = linked(src, renamed(src, src_variant, v), coll, v)
        if src.name.endswith("_hull"):
            dup.material_slots[0].link = "OBJECT"
            dup.material_slots[0].material = M(f"kayak_{colour}")
            parts["hull"] = dup
    return parts


def copy_gbb(coll, v, skip=(), moved=None):
    """Linked copies of the glass boat's parts, all but `skip`, each moved
    along y by `moved[part]`."""
    moved = moved or {}
    parts = {}
    for src in variant_objects("glass_bottom_boat"):
        key = src.name[len("glass_bottom_boat_"):]
        if key in skip:
            continue
        parts[key] = linked(src, renamed(src, "glass_bottom_boat", v), coll, v,
                            src.location + Vector((0.0, moved.get(key, 0.0), 0.0)))
    return parts


def build_gbb_electric(coll, v):
    parts = copy_gbb(coll, v, skip=("outboard",))

    def drive(bm):
        y0, y1, z, r = GBB_E_SHAFT
        prism_into(bm, ngon(0.0, z, r), "y", y0, y1)
        p0, p1, pr = GBB_E_PROP
        prism_into(bm, ngon(0.0, z, pr), "y", p0, p1)
        box_into(bm, *GBB_E_RUDDER)
    parts["drive"] = part(f"{v}_electric_drive", coll, [M("gbb_motor")], v, drive)
    return parts


def build_gbb_bow_helm(coll, v):
    parts = copy_gbb(coll, v, skip=("bow_locker",),
                     moved={"helm_console": GBB_BH_SHIFT, "helm_wheel": GBB_BH_SHIFT, "helm_stool": GBB_BH_SHIFT,
                            "life_ring": GBB_BH_RING_SHIFT})
    parts["locker"] = part(f"{v}_bow_locker", coll, [M("gbb_liner")], v,
                           lambda bm: slab(bm, gbb_spec(), 0.15, GBB_FLOOR - 0.02, GBB_LOCKER_TOP,
                                           y_cut=GBB_BH_LOCKER_Y))
    parts["stern_bench"] = part(f"{v}_stern_bench", coll, [M("gbb_wood")], v,
                                lambda bm: box_into(bm, *GBB_BH_STERN_BENCH))
    return parts


def build_gbb_side_gate(coll, v):
    spec = gbb_spec()
    parts = copy_gbb(coll, v, skip=("hull", "rubrail", "bench_starboard", "backrest_starboard"))
    hull, trim, bottom, liner, floor, wood = (M("gbb_hull"), M("gbb_trim"), M("gbb_bottom"), M("gbb_liner"),
                                              M("gbb_floor"), M("gbb_wood"))

    def band_mat(i):
        if GBB_GATE_RINGS[i + 1][3] <= GBB_BOOT + 1e-9:
            return 1
        return 0 if i < 6 else 2
    parts["hull"] = part(f"{v}_hull", coll, [hull, bottom, liner, floor], v,
                         lambda bm: tub(bm, spec, GBB_GATE_RINGS, band_mat, 1, 3, hole=GBB_WELL, shaft_mat=2,
                                        side_y=GBB_GATE, notch=GBB_GATE_NOTCH, notch_mat=2))
    ga, gb = GBB_GATE
    parts["rubrail"] = part(f"{v}_rubrail", coll, [trim], v,
                            lambda bm: band(bm, spec, GBB_RUBRAIL,
                                            side_y=(ga - GBB_GATE_RAIL_GAP, gb + GBB_GATE_RAIL_GAP)))
    bx0, bx1, by0, by1, bz0, bz1 = GBB_BENCH
    rx0, rx1, ry0, ry1, rz0, rz1 = GBB_BACKREST
    for tag, (b0, b1), (r0, r1) in (("aft", (by0, ga - 0.10), (ry0, ga - 0.15)),
                                    ("fwd", (gb + 0.10, by1), (gb + 0.15, ry1))):
        bench = part(f"{v}_bench_starboard_{tag}", coll, [wood], v,
                     lambda bm, b0=b0, b1=b1: box_into(bm, -(bx1 - bx0) / 2, (bx1 - bx0) / 2, b0, b1, bz0, bz1))
        bench.location = ((bx0 + bx1) / 2, 0.0, 0.0)
        back = part(f"{v}_backrest_starboard_{tag}", coll, [wood], v,
                    lambda bm, r0=r0, r1=r1: box_into(bm, -(rx1 - rx0) / 2, (rx1 - rx0) / 2, r0, r1, rz0, rz1))
        back.location = ((rx0 + rx1) / 2, 0.0, 0.0)
    lx0, lx1 = GBB_GATE_LEAF
    parts["gate"] = part(f"{v}_gate", coll, [trim], v,
                         lambda bm: box_into(bm, lx0, lx1, ga + 0.01, gb - 0.01, GBB_GATE_SILL - 0.01, GBB_SHEER - 0.02))
    return parts


# --- reference -------------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    bm = bmesh.new()
    prism_into(bm, ngon(0.0, 0.0, 0.18, 12), "z", 0.0, height - 0.40)
    body = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for vtx in bm.verts:
        if vtx not in body:
            vtx.co.z += height - 0.17
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0)))
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    obj.location = (x, y, z)
    coll.objects.link(obj)
    return obj


def edge_object(name, coll, loops):
    bm = bmesh.new()
    for pts in loops:
        vs = [bm.verts.new(p) for p in pts]
        for i in range(len(vs)):
            bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def waterline_loop(name, coll, hull, keep=None):
    """The hull sliced at z = 0: the edges where the water meets it."""
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    bm.transform(hull.matrix_world)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                           clear_inner=True, clear_outer=True)
    if keep is not None:
        bmesh.ops.delete(bm, geom=[vx for vx in bm.verts if not keep(vx.co)], context="VERTS")
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def build_reference(reference, hulls):
    if "waterline" not in bpy.data.objects:
        marker = bpy.data.objects.new("waterline", None)
        marker.empty_display_type = "PLAIN_AXES"
        marker.empty_display_size = 0.5
        marker[TAG] = True
        reference.objects.link(marker)
    for v, hull in hulls.items():
        keep = None
        # not a well's or a slot's shaft: it is dry inside
        hole = GBB_WELL if v.startswith("glass_bottom_boat") else PBT_SLOT if v == "paddle_boat_tunnel" else None
        if hole:
            def keep(co, hole=hole):
                x0, x1, y0, y1 = hole
                return not (x0 - 0.01 <= co.x <= x1 + 0.01 and y0 - 0.01 <= co.y <= y1 + 0.01)
        waterline_loop(f"waterline_{v}", reference, hull, keep)
    for v in VARIANTS:
        # the boat's own length and beam, not the paddles lying across it
        lo, hi = bounds([o for o in variant_objects(v) if not re.search(r"_paddle(_\d+)?$", o.name)])
        edge_object(f"outline_{v}_{hi.y - lo.y:.2f}x{hi.x - lo.x:.2f}".replace(".", "p"), reference,
                    [[(lo.x, lo.y, 0.0), (hi.x, lo.y, 0.0), (hi.x, hi.y, 0.0), (lo.x, hi.y, 0.0)]])
    figure("figure_1p7m", reference, 2.6, 0.0)


# --- checks ------------------------------------------------------------------------

def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def bounds(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ vx.co for o in objs for vx in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def triangles(objs):
    total = 0
    for o in objs:
        o.data.calc_loop_triangles()
        total += len(o.data.loop_triangles)
    return total


def report(variant, hull_name=None):
    objs = variant_objects(variant)
    lo, hi = bounds(objs)
    line = (f"{PROP}: {variant}: {len(objs)} parts, {triangles(objs)} triangles, "
            f"length {hi.y - lo.y:.2f} x beam {hi.x - lo.x:.2f} m, top {hi.z:.2f} over the water, "
            f"draft {-lo.z:.2f}")
    hull = bpy.data.objects.get(hull_name) if hull_name else None
    if hull is not None:
        hl, hh = bounds([hull])
        line += f"; hull {hh.y - hl.y:.2f} x {hh.x - hl.x:.2f} m, hull draft {-hl.z:.2f}"
    print(line)


# --- renders -----------------------------------------------------------------------

def render(folder):
    """Review renders on a flat blue water plane at z = 0, half clear so the
    hull under it shows, over a sand bed 2 m down (the lagoon at its lowest).
    Each shot is staged from linked copies of the boat's parts and fresh
    water, pontoon and figure, all removed before the next: Eevee in a
    background run did not always follow `hide_render` toggled between
    renders (2026-10-03, the lineup drew hidden boats and missed shown ones).
    Everything here is made after the save and never saved."""
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    for f in os.listdir(folder):
        if f.endswith(".png"):
            os.remove(os.path.join(folder, f))
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    for name in ("authored", "reference", "export"):
        bpy.data.collections[name].hide_render = True
    shot = []

    def stage_obj(name, build, rgba):
        bm = bmesh.new()
        build(bm)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mat = material(name, rgba)
        if rgba[3] < 1.0:
            mat.surface_render_method = "BLENDED"
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        stage.objects.link(obj)
        return obj

    water_rgba = srgb("3d8fb8", 0.55)
    wx0, wx1, wy0, wy1 = GBB_WELL
    m = 0.02                             # the cut's edge stays inside the hull's walls
    fig_mat = material("_figure_stage", (0.30, 0.22, 0.40, 1.0))
    pontoon_rgba = srgb("b08a62")        # the map's dock colour
    stage_obj("_bed", lambda bm: box_into(bm, -80, 80, -80, 80, -2.10, -2.0), srgb("c9b98f"))

    def set_shot(objs, glass_boat=False, dx=0.0):
        """Clear the last shot; copies of `objs`, the water (cut round the
        glass boat's well when it is shown) and, under the well, eelgrass."""
        for o in shot:
            bpy.data.objects.remove(o, do_unlink=True)
        shot.clear()
        for o in objs:
            dup = o.copy()               # a linked copy: the same mesh
            dup.hide_render = False
            dup.location.x += dx
            stage.objects.link(dup)
            shot.append(dup)
        if glass_boat:
            shot.append(stage_obj("_water_cut", lambda bm: [
                box_into(bm, -80, 80, -80, wy0 - m, -0.004, 0.0), box_into(bm, -80, 80, wy1 + m, 80, -0.004, 0.0),
                box_into(bm, -80, wx0 - m, wy0 - m, wy1 + m, -0.004, 0.0),
                box_into(bm, wx1 + m, 80, wy0 - m, wy1 + m, -0.004, 0.0)], water_rgba))
            for k, (x, y, sx, sy) in enumerate(((0.3, 1.2, 1.4, 0.9), (-0.6, -1.6, 1.0, 1.3), (0.9, -0.2, 0.8, 0.7))):
                shot.append(stage_obj(f"_eelgrass_{k}", lambda bm, x=x, y=y, sx=sx, sy=sy: box_into(
                    bm, x - sx, x + sx, y - sy, y + sy, -2.0, -1.96), srgb("3f7a52")))
        else:
            shot.append(stage_obj("_water", lambda bm: box_into(bm, -80, 80, -80, 80, -0.004, 0.0), water_rgba))
        bpy.context.view_layer.update()
        return shot[:len(objs)]

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
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False

    def points_of(objs):
        bpy.context.view_layer.update()
        return [o.matrix_world @ vx.co for o in objs for vx in o.data.vertices]

    def shoot(name, eye, target, lens=35, size=(1600, 1000), ortho=None, fit=None, rot=None):
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.lens = lens
        cam.data.clip_start = 0.02
        cam.data.clip_end = 400
        scene.render.resolution_x, scene.render.resolution_y = size
        cam.location = eye
        d = Vector(target) - Vector(eye)
        cam.rotation_euler = rot if rot is not None else d.to_track_quat("-Z", "Y").to_euler()
        if fit and not ortho:
            # back off along the line of sight until the whole boat is in frame
            for _ in range(40):
                bpy.context.view_layer.update()
                if all(0.03 <= c.x <= 0.97 and 0.04 <= c.y <= 0.96 and c.z > 0
                       for c in (world_to_camera_view(scene, cam, p) for p in fit)):
                    break
                cam.location = Vector(target) - d * (1.08 * (Vector(target) - cam.location).length / d.length)
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{PROP}: rendered {scene.render.filepath}")

    for v in VARIANTS:
        gb = v.startswith("glass_bottom_boat")      # the water cut round the well
        objs = variant_objects(v)
        set_shot(objs, gb)
        lo, hi = bounds(objs)
        c = (lo + hi) / 2
        length = hi.y - lo.y
        size = max(length, 2.6)
        pts = points_of(objs)
        shoot(f"{v}_three_quarter", c + Vector((0.65, 0.85, 0.55)) * size, c, lens=40, fit=pts)
        shoot(f"{v}_side", (c.x + 60.0, c.y, (lo.z + hi.z) / 2), (c.x, c.y, (lo.z + hi.z) / 2),
              ortho=length * 1.12)
        shoot(f"{v}_plan", (c.x, c.y, 60.0), (c.x, c.y, 0.0), ortho=length * 1.12,
              rot=(0.0, 0.0, math.pi / 2))
        if v == "glass_bottom_boat":
            # inside: a standing passenger's eye by the helm, down the well;
            # along the well through the glass; the hull from under the water
            shoot(f"{v}_interior", (0.80, -3.20, GBB_FLOOR + 1.60), (0.0, 0.8, -0.70), lens=22)
            shoot(f"{v}_through_the_glass", (0.0, -2.35, GBB_FLOOR + 1.50), (0.0, 0.10, -0.66), lens=26)
            shoot(f"{v}_underwater", (5.5, -7.5, -1.35), (0.0, -0.5, -0.45), lens=30, fit=pts)
            # the plan with the roof and posts off
            set_shot([o for o in objs if "_post_" not in o.name and "canopy_roof" not in o.name], gb)
            shoot(f"{v}_plan_roof_off", (c.x, c.y, 60.0), (c.x, c.y, 0.0), ortho=length * 1.12,
                  rot=(0.0, 0.0, math.pi / 2))
            set_shot(objs, gb)
        # beside a 1.7 m figure on a floating landing 0.4 m over the water
        px = hi.x + 0.35
        shot.append(stage_obj(f"_pontoon_{v}", lambda bm: box_into(bm, px, px + 2.4, lo.y - 0.5, hi.y + 0.5,
                                                                   -0.30, 0.40), pontoon_rgba))
        fig = figure(f"_figure_{v}", stage, px + 0.6, c.y + 0.15 * length, z=0.40, mat=fig_mat)
        shot.append(fig)
        shoot(f"{v}_with_figure", (c.x - 0.45 * size - 1.0, hi.y + 1.1 * size + 1.5, 1.75),
              (px - 0.2, c.y, 0.6), lens=35, fit=pts + points_of([fig]))

    # the fleet, each at its own size, a row per family, with a figure
    set_shot([])
    rows = ([v for v in VARIANTS if v.startswith("glass_bottom_boat")],
            [v for v in VARIANTS if v.startswith("paddle_boat")],
            [v for v in VARIANTS if v.startswith("kayak_tandem")] + [v for v in VARIANTS if v.startswith("kayak_single")])
    lineup = []
    row_y, last_x = 0.0, 0.0
    for r, row in enumerate(rows):
        ext = [bounds(variant_objects(v)) for v in row]
        if r:
            row_y -= max(hi.y for lo, hi in ext) + 1.5
        x = 0.0
        for v, (lo, hi) in zip(row, ext):
            x += -lo.x if x == 0.0 else -lo.x + 0.9
            for o in variant_objects(v):
                dup = o.copy()
                dup.hide_render = False
                dup.location += Vector((x, row_y, 0.0))
                stage.objects.link(dup)
                shot.append(dup)
                lineup.append(dup)
            x += hi.x
        last_x = x
        row_y += min(lo.y for lo, hi in ext)
    fig = figure("_figure_lineup", stage, last_x + 1.0, row_y + 1.5, mat=fig_mat)
    pts = points_of(lineup) + points_of([fig])
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), 0))
    c = (lo + hi) / 2
    shoot("fleet_lineup", c + Vector((3.0, -20.0, 12.0)), c + Vector((0, 0, 0.3)), lens=35, fit=pts)


# --- main ----------------------------------------------------------------------------

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
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    colls = {"paddle_boat": export}
    for v in VARIANTS[1:]:
        colls[v] = bpy.data.collections.new(f"variant_{v}")
        export.children.link(colls[v])

    pb = build_paddle_boat(colls["paddle_boat"], "paddle_boat")
    v = "paddle_boat_canopy"
    for src in pb.values():
        linked(src, src.name.replace("paddle_boat_", f"{v}_", 1), colls[v], v)
    build_canopy(colls[v], v)
    ks, _, ks_stations, paddle = build_kayak(colls["kayak_single"], "kayak_single", KS, "kayak_yellow")
    kt, _, kt_stations, _ = build_kayak(colls["kayak_tandem"], "kayak_tandem", KT, "kayak_red", paddle_src=paddle)
    gbb = build_gbb(colls["glass_bottom_boat"], "glass_bottom_boat")
    # the further variants copy the five above and change nothing in them
    pb4 = build_paddle_boat_four(colls["paddle_boat_four"], "paddle_boat_four", pb)
    pbt = build_paddle_boat_tunnel(colls["paddle_boat_tunnel"], "paddle_boat_tunnel", pb)
    for src_variant, colours in KAYAK_COLOURS.items():
        for colour in colours:
            v = f"{src_variant}_{colour}"
            build_kayak_colour(colls[v], v, src_variant, colour)
    build_gbb_electric(colls["glass_bottom_boat_electric"], "glass_bottom_boat_electric")
    build_gbb_bow_helm(colls["glass_bottom_boat_bow_helm"], "glass_bottom_boat_bow_helm")
    gate = build_gbb_side_gate(colls["glass_bottom_boat_side_gate"], "glass_bottom_boat_side_gate")
    bpy.context.view_layer.update()
    build_reference(reference, {"paddle_boat": pb["hull"], "kayak_single": ks["hull"],
                                "kayak_tandem": kt["hull"], "glass_bottom_boat": gbb["hull"],
                                "paddle_boat_four": pb4["hull"], "paddle_boat_tunnel": pbt["hull"],
                                "glass_bottom_boat_side_gate": gate["hull"]})
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    print(f"{PROP}: kayak stations single {len(ks_stations)}, tandem {len(kt_stations)}; "
          f"glass slots {[(round(a, 3), round(b, 3)) for a, b in gbb_pane_slots()[0]]}")
    for v in VARIANTS:
        report(v, f"{v}_hull")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1])


main()
