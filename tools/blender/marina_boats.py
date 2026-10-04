"""The Headland working harbour's boats, blocked out (2026-10-03): the
coastal plan's marina (`documentation/coastal-world-expansion-plan-2026-09-06.md`,
"Working waterfront": "a few working boats and sailboats", "Fishing boats
idle, leave and return on authored loops; offshore anglers are readable groups
seated in small boats. Sailboats use slower, wider loops and also sit moored
in the marina"), on `documentation/maps/park-waterfront.html` (the marina
grows from the quay; the working-boat loop through the harbour mouth, the
wider sailing loop outside the breakwater). The cove was laid out for the two
stand-in boxes in `tools/gen_props.gd` (`_rebuild_harbour`, a 2.2 x 6 m hull
with a cabin); the coast is Morro Bay / Avila, late 1990s.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/marina_boats.blend --python tools/blender/marina_boats.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, five `kyt_variant`s, all at the origin (Send
writes one prop per variant, `marina_boats_<variant>`, as the park lamp's
three go):

- **troller**, in `export` itself: a West Coast salmon troller of 12.5 m on
  deck, the classic Morro Bay fishing-boat silhouette. A white hull with a
  sheer that sweeps up to a high bow, a green trim band and cap round the
  bulwark, red bottom paint and a black boot stripe; a full keel that deepens
  aft to 1.8 m, a rudder and a three-bladed propeller in the aperture. The
  pilothouse stands forward with its front leaning out at the top (the West
  Coast reverse-raked windscreen), a radar dome, a dry stack and two whips on
  its roof. A mast just aft of it with a crosstree and a cargo boom topped up
  over the fish hold hatch; the trolling pit at the stern between two gurdies.
  The two trolling poles stand raised (stowed), hinged on the rail at the
  mast and leaning in past the crosstree so they cross above it.
- **troller_poles_down** (`export/variant_troller_poles_down`, eye shut): the
  same boat, every part a linked copy of the troller's (one mesh each, so
  reshaping one reshapes both); the poles are the same mesh turned down about
  their hinges to `T_POLE_DOWN` above horizontal, with a lift from each
  crosstree end, two tag lines trailing aft into the water off each pole and a
  stabiliser ("flopper stopper") hanging on a chain from each.
- **skiff** (`export/variant_skiff`): an 18 ft open aluminium skiff with a
  tiller outboard, the plan's "readable group seated in a small boat": an open
  hull (the one interior in the family, because guests sit in it), a small
  foredeck, three bench seats for four anglers (`angler_seat_1`..`4` in
  `reference` mark where seated guests go), four rods standing in gunwale
  holders, a red fuel tank and a white cooler.
- **sloop_moored** (`export/variant_sloop_moored`): a 30 ft production sloop
  of the 1980s-90s (Catalina 30 class): fin keel and spade rudder, a raked
  bow, a raked transom, a low cabin trunk with ports and a sliding hatch, a
  cockpit with seats and coamings and a tiller, a masthead rig 12.8 m over the
  deck, the main furled on the boom under a blue sail cover, the jib rolled on
  its furler, pulpit, pushpit, stanchions and one lifeline.
- **sloop_sailing** (`export/variant_sloop_sailing`): the same boat as linked
  copies, the boom swung out `SL_BOOM_OUT` to port, main and jib set as
  cambered sheets `SAIL_T` thick (never single-sided), sheets led to the
  traveller and the winch; no heel (the loop can tilt it later).

Nine further variants (2026-10-03, Christina: "build all the offered
variants"), each in `export/variant_<name>` with its eye shut, each sharing
every unchanged part of the boat it varies as a linked mesh; the five above
are built first by the same code and are proven unchanged by a geometry hash:

- **troller_canoe_stern**: the double-ender. Its own hull (no transom; the
  sheer rises aft to 1.40 m, the stern narrows to a raked sternpost and a
  closed afterdeck, as the bow does), the keel run aft to the post, a rudder
  hung on the post, the propeller in the aperture, the pit and gurdies moved
  forward to where the stern still has room. Everything above the deck is the
  troller's, linked.
- **troller_mizzen**: the troller with a mizzen just forward of the pit, a
  boom to the stern and a flat riding sail in tanned canvas
  (`marina_boats_sail_tan`), a stay to the mainmast and a sheet to the
  transom.
- **troller_red**: the second colour set, red trim as the cove's red
  stand-in: the hull, the pilothouse glass (its door) and roof are copies of
  the troller's meshes carrying their own materials (`_trim_red`,
  `_bottom_green`, `_deck_grey`, `_door_red`, `_roof_red`); every other part
  is linked.
- **skiff_console**: an 18 ft fibreglass centre-console skiff: a deep-V white
  hull with a navy sheer stripe, a casting deck with a bow rail, the console
  with its tinted windscreen and wheel, a leaning-post seat, a cooler seat on
  the console's front, a stern bench, a big white outboard steered from the
  console, the skiff's rods (linked) in four holders;
  `console_angler_seat_1`..`4` in `reference`.
- **sloop_wheel**, **sloop_dodger**, **sloop_reverse_transom**,
  **sloop_double_lifelines**: the moored sloop with one change each: a
  steering pedestal and wheel in place of the tiller; a blue spray dodger over
  the companionway; the 1990s stern (its own hull with the transom leaning
  forward at the top, a moulded swim step with a teak pad, the pushpit and
  backstay brought forward with the shorter deck); a second, lower lifeline.
- **sloop_sailing_port_tack**: the sailing sloop on the other tack, the boom
  and the sails out to starboard and the sheets led to the starboard winch,
  built for that side (Check refuses negative scale, so nothing is mirrored).

**Frame.** Real metres, Z up. z = 0 is the waterline; every hull goes below it
by its draft as a simple closed form down to the keel, because it is seen
through clear water. The bow is +Y (the glTF export turns Blender +Y into
Godot -Z, Godot's forward for `Basis.looking_at`, as `ride_vehicle.gd` orients
its trains); the origin is on the centreline, midships, at the waterline.

**Into the locked `reference` collection** go `waterline` (the troller's
waterline as an edge loop, cut from its hull at z = 0) with `waterline_skiff`
and `waterline_sloop`, the length/beam outlines, a 1.7 m figure on the
troller's working deck and the four `angler_seat_` markers. Everything the tool
makes carries `kyt_marina_boats`, so a rerun removes and rebuilds its own work
and keeps anything of hers; `export` holding anything untagged refuses without
`--replace`.

**Contract** (scenery): closed shells, silhouette first, no interior except the
skiff's. The pilothouse windows and the trunk's ports are dark slabs set 2 cm
proud and 2 cm into the wall, not holes; the trolling pit is a coaming round a
dark slab. Every part carries `kyt_collision = none` this pass: collision and
boarding are decided when the boats are placed and scheduled. No two shapes
share a plane: a part that meets another laps into it or stands proud of it.

**How it is built.** Each hull is one loft through stations along Y. A station
is a closed section, keel to deck, on fixed waterlines (so the bottom paint,
boot stripe and trim band are horizontal bands of faces, not separate parts);
the bulwark, toe rail, cockpit well and the skiff's open interior are part of
the section, and a deck or foredeck that closes over them is a second station
2 cm from an open one. The bow stations narrow to the stem line and the last
collapses to it; the transom is the last station's face, raked. Stand-in
materials by surface, `marina_boats_<surface>`; Christina paints later. No
names, numbers, flags or logos anywhere.
"""

import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

TAG = "kyt_marina_boats"
PROP = "marina_boats"
ORIGINAL = ("troller", "troller_poles_down", "skiff", "sloop_moored", "sloop_sailing")
FURTHER = ("troller_canoe_stern", "troller_mizzen", "troller_red", "skiff_console", "sloop_wheel", "sloop_dodger",
           "sloop_reverse_transom", "sloop_double_lifelines", "sloop_sailing_port_tack")
VARIANTS = ORIGINAL + FURTHER

# --- the troller ---------------------------------------------------------------
# Read: West Coast wooden salmon trollers of 38-46 ft run 12.5-13.5 ft beam and
# 5.5-7 ft draft (brokers' listings, e.g. a 42 x 12.5 x 5.6 ft 1946 troller);
# trolling poles are 3-6 in. thick (Oregon Sea Grant, "Salmon trollers").
T_STEM_Y = 6.25                    # the stem head; chosen: 12.5 m on deck, the task's 12-13 m
T_TRANSOM_WL_Y = -5.95             # where the raked transom meets the water (chosen)
T_TRANSOM_RAKE = math.radians(15)  # top aft (chosen)
T_HALF_BEAM = 2.00                 # beam 4.0 m, 13 ft (read)
T_MAX_Y = -0.5                     # where the beam is greatest (chosen, just aft of midships)
T_TRANSOM_HALF = 1.50              # a broad working transom (chosen)
T_SHEER_LOW, T_SHEER_LOW_Y = 1.10, -2.5   # the deck's low point over the water (chosen)
T_SHEER_STERN = 1.18
T_SHEER_BOW = 2.05                 # the sheer sweeps up to a high bow (chosen, the type's look)
T_BULWARK = 0.62                   # bulwark over the deck (chosen, about 2 ft)
T_BULWARK_T = 0.12                 # chunky
T_STRIPE = 0.26                    # the trim band down from the bulwark top
T_BOOT = 0.10                      # the boot stripe over the waterline
T_CAMBER = 0.10
T_BODY_K = -1.15                   # the hull body's bottom midships, the keel below it
T_K_STERN = -0.50                  # the run rises to the transom
T_FOREFOOT = (5.0, -0.55)          # the stem rakes up from here to the stem head
T_FOREDECK_Y = 5.15                # forward of this the foredeck is at the bulwark top
T_KW = 0.12                        # the body's flat keel strip, each side
T_KEEL_HALF = 0.09                 # the keel below the body
T_KEEL_AFT_Y = -4.60
T_DRAFT = 1.80                     # 5.9 ft (read: 5.5-7 ft)
T_KEEL_FWD = (1.5, -1.38)          # the keel's forward foot (chosen: drag keel, deeper aft)
T_RUDDER = (-5.05, -5.70, -1.58)   # leading edge, trailing edge, bottom
T_PROP = (-4.82, -1.22, 0.36)      # y, z, radius
# the pilothouse: forward of midships, front leaning out at the top
T_HOUSE_BACK_Y = 0.85
T_HOUSE_FRONT_Y = (3.45, 3.65)     # bottom, top: the reverse-raked front
T_HOUSE_HALF = (1.30, 1.10)        # at the back, at the front's foot (it narrows forward)
T_HOUSE_H = 2.05                   # over the deck at the back (standing headroom)
T_ROOF_OVER, T_ROOF_T = 0.12, 0.12
T_MAST_Y = 0.55                    # just aft of the house
T_MAST_H = 8.6                     # over the deck (chosen)
T_CROSSTREE = (0.85, 8.15)         # half-span, height over the deck
T_BOOM = (2.3, 4.6, math.radians(15))   # gooseneck over the deck, length, topped up
T_POLE_L = 12.2                    # 40 ft, about the boat's length (chosen)
T_POLE_R = (0.075, 0.038)          # 6 in. at the foot, 3 in. at the tip (read)
T_POLE_DOWN = math.radians(40)     # above horizontal when fishing (chosen)
T_HATCH = (-1.4, 1.30, 1.15, 0.32)  # centre y, width, length, coaming height
T_PIT = (-5.25, 1.0, 0.8, 0.16)    # the trolling pit: centre y, width, length, coaming
T_GURDY_X = 0.86

# --- the skiff -------------------------------------------------------------------
# Read: 18 ft open aluminium skiffs of the 1990s run about 6.5-7 ft beam with
# a tiller outboard. The motor here is chosen: transom top to cavitation plate
# 0.82 m (an extra-long shaft for the 0.78 m transom), plate 4 cm under the hull.
SK_STEM_Y = 2.75                   # 5.5 m on deck with the transom, 18 ft (chosen)
SK_TRANSOM_WL_Y = -2.66
SK_RAKE = math.radians(12)
SK_HALF = 1.05                     # beam 2.1 m, 6.9 ft (read)
SK_MAX_Y = -0.3
SK_TRANSOM_HALF = 0.88
SK_SHEER_MID, SK_SHEER_LOW_Y = 0.60, -0.8
SK_SHEER_STERN, SK_SHEER_BOW = 0.62, 1.00
SK_K, SK_K_STERN = -0.22, -0.16    # the hull's draft (chosen)
SK_FOREFOOT = (1.70, -0.05)
SK_KW = 0.035
SK_GW = 0.07                       # the gunwale cap's width, chunky
SK_WALL = 0.05                     # the side's thickness at the floor
SK_FLOOR = 0.24                    # the floor over the keel
SK_FOREDECK_Y = 1.70
SK_BENCHES = ((-2.22, -1.86), (-0.40, -0.04), (0.92, 1.24))   # aft, middle, forward
SK_SEAT_H = 0.36                   # bench top over the floor (chosen, a boat bench)

# --- the sloop -------------------------------------------------------------------
# Read: Catalina 30 (1972-91, the decade's best-selling 30-footer): LOA 30.0 ft,
# LWL 25.0 ft, beam 10.8 ft, draft 5.25 ft (fin), I 41.0, J 11.5, P 35.0,
# E 11.5 ft (Good Old Boat sail data). The task: mast about 13 m over the deck.
SL_STEM_Y = 4.60                   # 9.2 m on deck (read: 30.0 ft)
SL_TRANSOM_TOP_Y = -4.60
SL_RAKE = math.radians(22)         # the 1980s raked transom, top aft (chosen)
SL_SHEER_STERN = 1.02
SL_TRANSOM_WL_Y = SL_TRANSOM_TOP_Y + SL_SHEER_STERN * math.tan(SL_RAKE)
SL_HALF = 1.65                     # beam 3.3 m (read: 10.8 ft)
SL_MAX_Y = -0.6
SL_TRANSOM_HALF = 1.25
SL_SHEER_LOW, SL_SHEER_LOW_Y = 0.98, -1.0
SL_SHEER_BOW = 1.25
SL_K, SL_K_STERN = -0.55, 0.25     # the canoe body; the counter clears the water aft
SL_FOREFOOT = (3.65, -0.05)        # gives LWL 7.15 m (read: 25 ft, 7.6 m; chosen a little short)
SL_KW = 0.05
SL_TOE = (0.07, 0.05)              # toe rail height, width
SL_CAMBER = 0.06
SL_STRIPE = 0.20
SL_BOOT = 0.08
SL_COCKPIT = (-4.05, -1.87)        # the open stations
SL_COAMING = (0.95, 0.86, 0.30)    # outer x, inner x, over the sheer
SL_SEAT = (0.50, -0.02)            # the seat's front x, its top under the sheer
SL_SOLE = 0.42                     # the cockpit floor under the sheer
SL_TRUNK_Y = (-1.82, 1.75, 1.45)   # aft face, front foot, front top
SL_TRUNK_HALF = (0.92, 0.80)       # aft foot, front foot
SL_TRUNK_TOP = 1.48                # its top at the sides; tumblehome 0.08
SL_KEEL = ((-0.35, 1.30, 0.09), (-0.45, 0.60, 0.07), -1.60)   # root, tip (trailing y, leading y, half thickness), tip z
SL_RUDDER = ((-3.55, -4.02), (-3.62, -3.92), -1.20)
SL_MAST_Y = 0.95                   # J 3.6 m back from the stem head (read: 11.5 ft)
SL_MAST_H = 12.8                   # over the deck (the task; read: I 41 ft)
SL_MAST_HALF = (0.08, 0.12)        # across, fore-and-aft (chunky)
SL_SPREADER = (6.6, 0.90, math.radians(12))   # over the deck, span each side, swept aft
SL_BOOM = (0.80, 3.70)             # gooseneck over the trunk top, length (read: E 11.5 ft)
SL_BOOM_OUT = math.radians(-20)    # sailing: swung out to port (a close reach)
SAIL_T = 0.005                     # the sails' thickness, 5 mm
SL_CHAINPLATE = 0.08               # in from the hull side

# --- the further variants (2026-10-03, Christina: "build all the offered variants") ---
# troller_canoe_stern: the double-ender, the older West Coast troller's stern
T_CANOE_STERN_Y = -6.25            # the stern head, as far aft as the stem head is forward (chosen)
T_CANOE_SHEER_STERN = 1.40         # a double-ender's sheer rises aft as well (chosen)
T_CANOE_POST = (-5.40, -0.75)      # the sternpost rakes up from here to the stern head
T_CANOE_AFTDECK_Y = -5.55          # aft of this the afterdeck is at the bulwark top
T_CANOE_KEEL_AFT_Y = -5.00
T_CANOE_RUDDER = (-5.40, -6.05, -1.55)   # hung on the sternpost: leading edge, trailing edge, bottom
T_CANOE_PROP_Y = -5.20
T_CANOE_PIT_Y = -4.65              # the pit moves forward where the stern narrows
# troller_mizzen: a riding (steadying) sail on a mizzen just forward of the pit
T_MIZZEN_Y = -4.35
T_MIZZEN_H = 5.6                   # over the deck (chosen)
T_MIZZEN_BOOM = (1.45, -6.25)      # the boom over the deck, the y of its end
# skiff_console: an 18 ft fibreglass centre console (chosen; 17-18 ft boats of
# the kind run 6.8-7.5 ft beam and a deep V)
CS_STEM_Y = 2.85
CS_TRANSOM_WL_Y = -2.70
CS_RAKE = math.radians(12)
CS_HALF = 1.12                     # beam 2.24 m, 7.3 ft
CS_MAX_Y = -0.3
CS_TRANSOM_HALF = 0.98
CS_SHEER_MID, CS_SHEER_LOW_Y = 0.72, -0.6
CS_SHEER_STERN, CS_SHEER_BOW = 0.74, 1.08
CS_K, CS_K_STERN = -0.30, -0.24    # the hull's draft
CS_FOREFOOT = (1.55, -0.10)
CS_KW = 0.04
CS_GW = 0.11                       # the moulded gunwale cap, chunky
CS_WALL = 0.07
CS_FLOOR = 0.34
CS_FOREDECK_Y = 1.55               # the casting deck forward of this
CS_STRIPE = 0.10                   # the sheer stripe's depth
CS_CONSOLE = (-0.10, 0.72, 0.36)   # its aft face's y, its length, half its width
CS_STERN_BENCH = (-2.25, -1.88)
# sloops
SL_WHEEL = (-3.42, 0.36)           # the wheel's y and radius (a 28 in. wheel; chosen)
SL_REV_TOP_Y = -4.35               # the reverse transom's top at the deck (chosen)
SL_REV_RAKE = math.radians(15)     # top forward
SL_REV_TRANSOM_WL_Y = SL_REV_TOP_Y - SL_SHEER_STERN * math.tan(SL_REV_RAKE)
SL_SWIM_STEP = (0.80, -4.85, 0.40, 0.12)   # half-width, aft edge, top, thickness
SL_LOWER_LIFELINE = 0.32           # over the deck

FIGURE_H = 1.70


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def lerp(a, b, t):
    return a + (b - a) * t


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {
    f"{PROP}_hull_white": srgb("f2f0ea"),
    f"{PROP}_bottom_red": srgb("8f2a22"),       # the troller's antifouling
    f"{PROP}_bottom_navy": srgb("27304a"),      # the sloop's
    f"{PROP}_boot_black": srgb("1c1d1f"),
    f"{PROP}_trim_green": srgb("1f7a63"),       # the troller's band and cap
    f"{PROP}_stripe_navy": srgb("1f3a6b"),      # the sloop's sheer and boot stripes
    f"{PROP}_deck_buff": srgb("c8b893"),
    f"{PROP}_deck_cream": srgb("e5dcc4"),
    f"{PROP}_cabin_white": srgb("f7f6f1"),
    f"{PROP}_roof_grey": srgb("aeb2b0"),
    f"{PROP}_glass": srgb("26333d"),
    f"{PROP}_door": srgb("2d5d7b"),
    f"{PROP}_pit_dark": srgb("2a2724"),
    f"{PROP}_spar_white": srgb("ece9df"),       # the troller's mast and boom
    f"{PROP}_pole_wood": srgb("b98d55"),
    f"{PROP}_spar_silver": srgb("b9bec2"),      # the sloop's aluminium
    f"{PROP}_metal": srgb("8c9195"),
    f"{PROP}_line": srgb("3b3d40"),
    f"{PROP}_stack_black": srgb("232323"),
    f"{PROP}_teak": srgb("9a6a3c"),
    f"{PROP}_sail": srgb("f1ede2"),
    f"{PROP}_cover_blue": srgb("27508f"),
    f"{PROP}_aluminium": srgb("a7adb1"),
    f"{PROP}_skiff_green": srgb("2f5d3a"),
    f"{PROP}_floor_grey": srgb("7f8478"),
    f"{PROP}_seat_tan": srgb("b39a72"),
    f"{PROP}_outboard_black": srgb("25272b"),
    f"{PROP}_tank_red": srgb("c8342b"),
    f"{PROP}_cooler_white": srgb("eeeeea"),
    f"{PROP}_rod_dark": srgb("2e2a26"),
    # the further variants' own colours (2026-10-03)
    f"{PROP}_sail_tan": srgb("c49a62"),       # the troller's riding sail, tanned canvas
    f"{PROP}_trim_red": srgb("b3262b"),       # troller_red: the cove's red stand-in
    f"{PROP}_bottom_green": srgb("2c4433"),
    f"{PROP}_deck_grey": srgb("9c9f98"),
    f"{PROP}_door_red": srgb("8e1f24"),
    f"{PROP}_roof_red": srgb("a8302c"),
    f"{PROP}_outboard_white": srgb("e9e8e3"),  # skiff_console's motor
    f"{PROP}_cushion_teal": srgb("2f7f86"),
}


def material(name, colour=None):
    """A stand-in material by name; a rerun resets the builder's colours (a
    material survives `--replace`)."""
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


def mat(surface):
    return material(f"{PROP}_{surface}")


# --- building blocks ---------------------------------------------------------

class Mesher:
    """One part's geometry: vertices merged by position, so a section that
    narrows to a point or a line closes the shell instead of leaving slivers."""

    def __init__(self):
        self.bm = bmesh.new()
        self.verts = {}

    def v(self, p):
        key = (round(p[0], 5), round(p[1], 5), round(p[2], 5))
        vert = self.verts.get(key)
        if vert is None:
            vert = self.bm.verts.new((p[0], p[1], p[2]))
            self.verts[key] = vert
        return vert

    def face(self, pts, mat_index=0):
        vs = []
        for p in pts:
            v = self.v(p)
            if not vs or vs[-1] is not v:
                vs.append(v)
        while len(vs) > 1 and vs[0] is vs[-1]:
            vs.pop()
        if len(vs) < 3 or len(set(vs)) != len(vs):
            return None
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = mat_index
        return f

    def loft(self, rings, mats, cap_first=True, cap_last=True, cap_mats=None):
        """Closed rings of equal length joined in order. `mats` is a list per
        segment (segment i runs from point i to i + 1) or a function
        (pair, segment) -> slot."""
        n = len(rings[0])
        pick = mats if callable(mats) else (lambda k, i: mats[i])
        for k, (a, b) in enumerate(zip(rings, rings[1:])):
            for i in range(n):
                j = (i + 1) % n
                self.face((a[i], a[j], b[j], b[i]), pick(k, i))
        first, last = cap_mats if cap_mats is not None else (pick(0, 0), pick(0, 0))
        if cap_first:
            self.face(list(reversed(rings[0])), first)
        if cap_last:
            self.face(list(rings[-1]), last)

    def prism(self, poly, axis, lo, hi, mat_index=0):
        def at(a, b, t):
            return {"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis]
        self.loft([[at(a, b, lo) for a, b in poly], [at(a, b, hi) for a, b in poly]],
                  [mat_index] * len(poly))

    def box(self, x0, x1, y0, y1, z0, z1, mat_index=0):
        assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
        self.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1, mat_index)

    def obox(self, c, u, v, n, hu, hv, hn, mat_index=0):
        """A box on axes u, v, n (unit vectors) with half sizes."""
        c, u, v, n = Vector(c), Vector(u), Vector(v), Vector(n)
        ring = lambda s: [c + n * s * hn + u * a * hu + v * b * hv for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        self.loft([ring(-1), ring(1)], [mat_index] * 4)

    def tube(self, pts, radii, sides=8, mat_index=0, up=None, caps=True, squash=(1.0, 1.0), phase=0.0):
        """A tube through `pts` with a radius per point, its section a
        `sides`-gon (scaled by `squash` on its two axes), one frame along
        it so it never twists."""
        pts = [Vector(p) for p in pts]
        d = (pts[-1] - pts[0]).normalized()
        ref = Vector(up) if up is not None else (Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0)))
        u = (ref - d * ref.dot(d)).normalized()
        v = d.cross(u)
        rings = []
        for p, r in zip(pts, radii):
            ring = []
            for k in range(sides):
                t = phase + math.tau * k / sides
                ring.append(p + u * (math.cos(t) * r * squash[0]) + v * (math.sin(t) * r * squash[1]))
            rings.append(ring)
        self.loft(rings, [mat_index] * sides, cap_first=caps, cap_last=caps)

    def line(self, a, b, w=0.025, mat_index=0, running=False):
        """A rope or wire: a square bar from a to b. Standing rigging is
        turned 45 degrees so its faces never lie in a box's planes; running
        rigging square to its frame, so a halyard or lift beside a stay in
        the centre plane never lies parallel to it (the topping lift and the
        backstay meet at the masthead)."""
        self.tube([a, b], [w * 0.7071, w * 0.7071], sides=4, mat_index=mat_index,
                  phase=0.0 if running else math.pi / 4)

    def torus(self, c, axis, R, r, seg=12, sides=4, mat_index=0):
        """A ring (a wheel's rim): `seg` stations round a circle of radius
        R about `axis`, each a `sides`-gon of radius r."""
        c, axis = Vector(c), Vector(axis).normalized()
        ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
        e1 = (ref - axis * ref.dot(axis)).normalized()
        e2 = axis.cross(e1)
        rings = []
        for k in range(seg):
            t = math.tau * k / seg
            radial = e1 * math.cos(t) + e2 * math.sin(t)
            centre = c + radial * R
            rings.append([centre + (radial * math.cos(q) + axis * math.sin(q)) * r
                          for q in (math.tau * j / sides + math.pi / sides for j in range(sides))])
        rings.append(rings[0])
        self.loft(rings, [mat_index] * sides, cap_first=False, cap_last=False)

    def sheet(self, grid, thick, mat_index=0):
        """A sail: a grid of points (rows of equal length) as a closed solid
        `thick` through, skins offset along the surface normal."""
        R, C = len(grid), len(grid[0])
        top, bot = [], []
        for r in range(R):
            tr, br = [], []
            for c in range(C):
                du = grid[r][min(c + 1, C - 1)] - grid[r][max(c - 1, 0)]
                dv = grid[min(r + 1, R - 1)][c] - grid[max(r - 1, 0)][c]
                n = du.cross(dv)
                n = n.normalized() if n.length > 1e-9 else Vector((1, 0, 0))
                tr.append(grid[r][c] + n * thick / 2)
                br.append(grid[r][c] - n * thick / 2)
            top.append(tr)
            bot.append(br)
        for r in range(R - 1):
            for c in range(C - 1):
                self.face((top[r][c], top[r][c + 1], top[r + 1][c + 1], top[r + 1][c]), mat_index)
                self.face((bot[r][c], bot[r + 1][c], bot[r + 1][c + 1], bot[r][c + 1]), mat_index)
        loop = [(0, c) for c in range(C)] + [(r, C - 1) for r in range(1, R)] + \
               [(R - 1, c) for c in range(C - 2, -1, -1)] + [(r, 0) for r in range(R - 2, 0, -1)]
        for (r0, c0), (r1, c1) in zip(loop, loop[1:] + loop[:1]):
            self.face((top[r0][c0], top[r1][c1], bot[r1][c1], bot[r0][c0]), mat_index)


def prop_blades(m, centre, axis, r, hub_r, hub_len, blades, mat_index, chord=0.22, thick=0.04, pitch=30):
    """A propeller: a hub along `axis` and chunky pitched blades."""
    centre, axis = Vector(centre), Vector(axis).normalized()
    m.tube([centre - axis * hub_len / 2, centre + axis * hub_len / 2], [hub_r, hub_r * 0.8], 8, mat_index)
    ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    e1 = (ref - axis * ref.dot(axis)).normalized()
    for k in range(blades):
        rk = Matrix.Rotation(math.tau * k / blades, 3, axis) @ e1
        t = axis.cross(rk)
        cd = (t * math.cos(math.radians(pitch)) + axis * math.sin(math.radians(pitch))).normalized()
        n = rk.cross(cd).normalized()
        half = (r - hub_r * 0.5) / 2
        m.obox(centre + rk * (hub_r * 0.5 + half), rk, cd, n, half, chord / 2, thick / 2, mat_index)


def finish(name, m, coll, mats, variant):
    """A part into an object in `coll`, tagged, no collision this pass."""
    bm = m.bm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = False
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    for mt in mats:
        mesh.materials.append(mt)
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    obj["kyt_collision"] = "none"
    obj["kyt_variant"] = variant
    coll.objects.link(obj)
    return obj


def mirror_ring(starboard, y_of):
    """A section from its starboard half (keel centre round to deck centre,
    both on x = 0) to a closed 3D ring; `y_of(z)` places each point along Y
    (a raked transom)."""
    pts = list(starboard) + [(-x, z) for x, z in reversed(starboard[1:-1])]
    return [(x, y_of(z), z) for x, z in pts]


def mirrored_mats(seg):
    return list(seg) + list(reversed(seg))


def polyline_x(pts, z):
    """The x of a polyline of (x, z) points rising in z, at height z."""
    if z <= pts[0][1]:
        return pts[0][0]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if z <= z1:
            return x0 if z1 - z0 < 1e-9 else lerp(x0, x1, (z - z0) / (z1 - z0))
    return pts[-1][0]


# --- the troller's hull ---------------------------------------------------------

def t_sheer(y):
    if y >= T_SHEER_LOW_Y:
        u = clamp((y - T_SHEER_LOW_Y) / (T_STEM_Y - T_SHEER_LOW_Y), 0, 1)
        return T_SHEER_LOW + (T_SHEER_BOW - T_SHEER_LOW) * u ** 2.2
    u = clamp((T_SHEER_LOW_Y - y) / (T_SHEER_LOW_Y - T_TRANSOM_WL_Y), 0, 1.2)
    return T_SHEER_LOW + (T_SHEER_STERN - T_SHEER_LOW) * u ** 2


def t_half(y):
    if y >= T_MAX_Y:
        u = clamp((y - T_MAX_Y) / (T_STEM_Y - T_MAX_Y), 0, 1)
        return T_HALF_BEAM * max(0.0, 1 - u ** 1.8) ** 0.5
    u = clamp((T_MAX_Y - y) / (T_MAX_Y - T_TRANSOM_WL_Y), 0, 1)
    return T_HALF_BEAM - (T_HALF_BEAM - T_TRANSOM_HALF) * u ** 2


def t_keel(y):
    """The hull body's bottom on the centreline; forward of the forefoot it is
    the stem line, which reaches the sheer at the stem head."""
    fy, fz = T_FOREFOOT
    if y >= fy:
        return fz + (T_SHEER_BOW - fz) * clamp((y - fy) / (T_STEM_Y - fy), 0, 1)
    if y >= 1.5:
        return T_BODY_K + (fz - T_BODY_K) * ((y - 1.5) / (fy - 1.5)) ** 2
    if y >= -2.0:
        return T_BODY_K
    u = clamp((-2.0 - y) / (-2.0 - T_TRANSOM_WL_Y), 0, 1)
    return T_BODY_K + (T_K_STERN - T_BODY_K) * u ** 1.6


def c_sheer(y):
    """The double-ender's sheer: the troller's forward, rising aft."""
    if y >= T_SHEER_LOW_Y:
        return t_sheer(y)
    u = clamp((T_SHEER_LOW_Y - y) / (T_SHEER_LOW_Y - T_CANOE_STERN_Y), 0, 1)
    return T_SHEER_LOW + (T_CANOE_SHEER_STERN - T_SHEER_LOW) * u ** 2


def c_half(y):
    """The double-ender's half-beam: fuller aft than the bow, to a point."""
    if y >= T_MAX_Y:
        return t_half(y)
    u = clamp((T_MAX_Y - y) / (T_MAX_Y - T_CANOE_STERN_Y), 0, 1)
    return T_HALF_BEAM * max(0.0, 1 - u ** 2.4) ** 0.6


def c_keel(y):
    """The double-ender's centreline bottom: the run rises to the sternpost,
    which rakes up to the sheer at the stern head."""
    if y >= -2.0:
        return t_keel(y)
    py, pz = T_CANOE_POST
    if y >= py:
        return T_BODY_K + (pz - T_BODY_K) * ((-2.0 - y) / (-2.0 - py)) ** 2
    return pz + (T_CANOE_SHEER_STERN - pz) * clamp((py - y) / (py - T_CANOE_STERN_Y), 0, 1)


def t_khs(y, canoe):
    return (c_keel(y), c_sheer(y), c_half(y)) if canoe else (t_keel(y), t_sheer(y), t_half(y))


def t_section_x(y, z, canoe=False):
    """The outer half-width at height z: a round V from the keel strip to the
    bilge, then flaring straight to the sheer. The double-ender's sections
    turn to a V aft as the bow's do forward."""
    K, S, B = t_khs(y, canoe)
    if S - K < 1e-6 or B <= 0.0:
        return 0.0
    s = clamp((y - 1.0) / (T_STEM_Y - 1.0), 0, 1)
    if canoe:
        s = max(s, clamp((-1.0 - y) / (-1.0 - T_CANOE_STERN_Y), 0, 1))
    p, tb = 1.7 - 0.6 * s, 0.55 + 0.30 * s
    kw = min(T_KW * (1 - s), 0.9 * B)
    bb = 0.93 * B
    t = clamp((z - K) / (S - K), 0, 1)
    if t <= tb:
        return kw + (bb - kw) * (1 - (1 - t / tb) ** p) ** (1 / p)
    return bb + (B - bb) * (t - tb) / (1 - tb)


T_HULL_SEGS = (0, 0, 0, 0, 0, 1, 2, 2, 3, 3, 4, 5, 5)   # bottom, boot, white, trim, bulwark inside, deck


def t_ring(y, closed, canoe=False):
    K, S, B = t_khs(y, canoe)
    top = S + T_BULWARK

    def px(z):
        z = min(max(z, K), S)
        return (t_section_x(y, z, canoe), z)

    pts = [(0.0, K), px(K)]
    for f in (0.70, 0.42, 0.18):
        pts.append(px(T_BODY_K * f))
    pts += [px(0.0), px(T_BOOT), (B, S), (B, top - T_STRIPE), (B, top)]
    bi = max(0.0, B - T_BULWARK_T)
    if closed:
        pts += [(bi, top), (bi, top), (0.5 * bi, top), (0.0, top)]
    else:
        pts += [(bi, top), (bi, S), (0.5 * bi, S + 0.75 * T_CAMBER), (0.0, S + T_CAMBER)]
    return pts


def t_deck(y, x=0.0, canoe=False):
    """The troller's deck inside the bulwarks."""
    S, bi = (c_sheer(y), max(0.01, c_half(y) - T_BULWARK_T)) if canoe else \
        (t_sheer(y), max(0.01, t_half(y) - T_BULWARK_T))
    x = abs(x)
    if x <= 0.5 * bi:
        return S + T_CAMBER - 0.25 * T_CAMBER * x / (0.5 * bi)
    return S + 0.75 * T_CAMBER * max(0.0, bi - x) / (0.5 * bi)


def t_stations():
    """(nominal y, closed, raked): the transom and its 12 cm bulwark, open
    stations to the foredeck, the closed bow to the stem head."""
    st = [(T_TRANSOM_WL_Y, True, True), (T_TRANSOM_WL_Y + T_BULWARK_T, False, True)]
    st += [(y, False, False) for y in (-5.3, -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.4, 4.2, 4.8,
                                       T_FOREDECK_Y - 0.02)]
    st += [(y, True, False) for y in (T_FOREDECK_Y, 5.45, 5.75, 6.0, 6.15, T_STEM_Y)]
    return st


def raked(y0, rake):
    t = math.tan(rake)
    return lambda z: y0 - z * t


def troller_hull_rings():
    rings = []
    for y, closed, rk in t_stations():
        y_of = raked(y, T_TRANSOM_RAKE) if rk else (lambda z, y=y: y)
        rings.append(mirror_ring(t_ring(y, closed), y_of))
    return rings


def canoe_hull_rings():
    """The double-ender: closed afterdeck stations narrowing to the stern
    head as the foredeck's do to the stem head; no transom."""
    st = [(y, True) for y in (T_CANOE_STERN_Y, -6.15, -6.0, -5.8, T_CANOE_AFTDECK_Y)]
    st += [(y, False) for y in (T_CANOE_AFTDECK_Y + 0.02, -5.0, -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.4,
                                4.2, 4.8, T_FOREDECK_Y - 0.02)]
    st += [(y, True) for y in (T_FOREDECK_Y, 5.45, 5.75, 6.0, 6.15, T_STEM_Y)]
    return [mirror_ring(t_ring(y, closed, canoe=True), lambda z, y=y: y) for y, closed in st]


# --- the troller -----------------------------------------------------------------

def pole_pivot(side):
    """The trolling pole's hinge on the rail at the mast, `side` +1 or -1."""
    y = T_MAST_Y
    return Vector((side * (t_half(y) + 0.08), y, t_sheer(y) + T_BULWARK - 0.10))


def pole_stowed_angle(side):
    """Lean the pole in so its axis passes the crosstree's end."""
    piv = pole_pivot(side)
    ct = Vector((side * (T_CROSSTREE[0] - 0.15), T_MAST_Y, t_sheer(T_MAST_Y) + T_CROSSTREE[1]))
    lean = math.atan2(abs(piv.x - ct.x), ct.z - piv.z)
    return -side * lean


def pole_down_angle(side):
    return side * (math.pi / 2 - T_POLE_DOWN)


def pole_point(side, angle, frac):
    piv = pole_pivot(side)
    return piv + Matrix.Rotation(angle, 3, "Y") @ Vector((0, 0, T_POLE_L * frac))


def build_troller(coll, variant="troller", prefix="troller_"):
    parts = {}

    def part(name, m, surfaces):
        obj = finish(prefix + name, m, coll, [mat(s) for s in surfaces], variant)
        parts[name] = obj
        return obj

    # the hull: one loft, bands by waterline; the transom is its first face
    m = Mesher()
    m.loft(troller_hull_rings(), mirrored_mats(T_HULL_SEGS), cap_first=True, cap_last=False, cap_mats=(2, 2))
    part("hull", m, ("bottom_red", "boot_black", "hull_white", "trim_green", "cabin_white", "deck_buff"))

    # the keel under the body: deeper aft, fading into the forefoot; its top
    # edge 12 cm inside the body
    ys = (3.6, 3.0, 2.0, 1.5, -2.0, -3.0, -4.0, T_KEEL_AFT_Y)
    poly = [(T_KEEL_AFT_Y, -T_DRAFT), T_KEEL_FWD] + [(y, t_keel(y) + 0.12) for y in ys]
    m = Mesher()
    m.prism(poly, "x", -T_KEEL_HALF, T_KEEL_HALF)
    part("keel", m, ("bottom_red",))

    # the rudder, hung under the counter aft of the propeller aperture
    y0, y1, zb = T_RUDDER
    m = Mesher()
    m.prism([(y0, zb), (y1, zb + 0.08), (y1, t_keel(y1) + 0.10), (y0, t_keel(y0) + 0.10)], "x", -0.05, 0.05)
    part("rudder", m, ("bottom_red",))

    # the propeller and its shaft out of the keel's after edge
    py, pz, pr = T_PROP
    m = Mesher()
    m.tube([(0, T_KEEL_AFT_Y + 0.15, pz), (0, py + 0.05, pz)], [0.05, 0.05], 8)
    prop_blades(m, (0, py, pz), (0, -1, 0), pr, 0.10, 0.22, 3, 0)
    part("propeller", m, ("metal",))

    # the pilothouse: a loft from its back wall to its front, which leans out
    # at the top; the sides are planes, so the front's top is narrowed to stay
    # on them
    zb = t_sheer(T_HOUSE_BACK_Y) - 0.06
    zt = t_sheer(T_HOUSE_BACK_Y) + T_HOUSE_H
    hb_, hf = T_HOUSE_HALF
    fy0, fy1 = T_HOUSE_FRONT_Y
    side_x = lambda y: hb_ + (hf - hb_) * (y - T_HOUSE_BACK_Y) / (fy0 - T_HOUSE_BACK_Y)
    hft = side_x(fy1)
    back = [(hb_, T_HOUSE_BACK_Y, zb), (hb_, T_HOUSE_BACK_Y, zt), (-hb_, T_HOUSE_BACK_Y, zt), (-hb_, T_HOUSE_BACK_Y, zb)]
    front = [(hf, fy0, zb), (hft, fy1, zt), (-hft, fy1, zt), (-hf, fy0, zb)]
    m = Mesher()
    m.loft([back, front], [0, 0, 0, 0])
    part("pilothouse", m, ("cabin_white",))

    # its windows and door: dark slabs 2 cm proud, 2 cm into the walls
    m = Mesher()
    fu = Vector((1, 0, 0))
    fv = (Vector((0, fy1, zt)) - Vector((0, fy0, zb))).normalized()
    fn = fv.cross(fu).normalized()
    if fn.y < 0:
        fn = -fn
    win0, win1 = zt - 0.80, zt - 0.22
    fh = (win1 + win0) / 2 - zb

    def on_front(xc, w):
        c = Vector((xc, fy0, zb)) + fv * (fh / fv.z)
        m.obox(c, fu, fv, fn, w / 2, (win1 - win0) / fv.z / 2, 0.02, 0)

    for xc in (-0.68, 0.0, 0.68):
        on_front(xc, 0.58)
    for side in (1, -1):
        a = Vector((side * hb_, T_HOUSE_BACK_Y, zb))
        b = Vector((side * hf, fy0, zb))
        su = (b - a).normalized()
        sn = Vector((0, 0, 1)).cross(su).normalized() * (1 if side < 0 else -1)
        if sn.x * side < 0:
            sn = -sn
        for along, w in ((0.75, 0.80), (1.75, 0.80)):
            c = a + su * along + Vector((0, 0, (win0 + win1) / 2 - zb))
            m.obox(c, su, Vector((0, 0, 1)), sn, w / 2, (win1 - win0) / 2, 0.02, 0)
    bn = Vector((0, -1, 0))
    m.obox((0.55, T_HOUSE_BACK_Y, zb + (t_deck(T_HOUSE_BACK_Y) - zb) + 0.98), (1, 0, 0), (0, 0, 1), bn,
           0.33, 0.93, 0.02, 1)                                   # the door
    m.obox((-0.55, T_HOUSE_BACK_Y, (win0 + win1) / 2), (1, 0, 0), (0, 0, 1), bn, 0.30, (win1 - win0) / 2, 0.02, 0)
    part("pilothouse_glass", m, ("glass", "door"))

    # the roof slab, overhanging all round
    o = T_ROOF_OVER
    rb, rf = T_HOUSE_BACK_Y - o, fy1 + o + 0.03
    rz0, rz1 = zt - 0.03, zt - 0.03 + T_ROOF_T
    ring = lambda z: [(side_x(rb) + o, rb, z), (side_x(rf) + o, rf, z), (-side_x(rf) - o, rf, z), (-side_x(rb) - o, rb, z)]
    m = Mesher()
    m.loft([ring(rz0), ring(rz1)], [0, 0, 0, 0])
    part("pilothouse_roof", m, ("roof_grey",))

    # on the roof: a radar dome on its pedestal, a dry stack, two whips
    m = Mesher()
    m.box(-0.11, 0.11, 1.72, 1.94, rz1 - 0.02, rz1 + 0.22)
    m.tube([(0, 1.83, rz1 + 0.20), (0, 1.83, rz1 + 0.50)], [0.33, 0.30], 12)
    part("radar", m, ("cabin_white",))
    m = Mesher()
    m.tube([(-0.88, 1.12, rz1 - 0.03), (-0.88, 1.12, rz1 + 1.05)], [0.10, 0.10], 8)
    part("stack", m, ("stack_black",))
    m = Mesher()
    for side in (1, -1):
        m.tube([(side * 0.98, 3.25, rz1 - 0.02), (side * 1.03, 2.95, rz1 + 2.4)], [0.025, 0.015], 6)
    part("whips", m, ("line",))

    # the mast, its crosstree and the cargo boom topped up over the hatch
    md = t_deck(T_MAST_Y)
    m = Mesher()
    m.tube([(0, T_MAST_Y, md - 0.12), (0, T_MAST_Y, md + T_MAST_H)], [0.11, 0.07], 8)
    part("mast", m, ("spar_white",))
    cz = t_sheer(T_MAST_Y) + T_CROSSTREE[1]
    m = Mesher()
    m.box(-T_CROSSTREE[0], T_CROSSTREE[0], T_MAST_Y - 0.065, T_MAST_Y + 0.065, cz - 0.07, cz + 0.07)
    part("crosstree", m, ("spar_white",))
    gz, bl, ba = T_BOOM
    g = Vector((0, T_MAST_Y - 0.04, md + gz))
    bend = g + Vector((0, -math.cos(ba), math.sin(ba))) * bl
    m = Mesher()
    m.tube([g, bend], [0.075, 0.055], 8)
    part("boom", m, ("spar_white",))
    m = Mesher()
    m.line((0, T_MAST_Y - 0.05, md + T_MAST_H - 0.6), bend + Vector((0, 0.05, 0.03)), 0.03, running=True)
    part("boom_lift", m, ("line",))

    # the trolling poles: one mesh along local +Z from the hinge, a linked
    # copy for port; stowed, they lean in past the crosstree's ends
    m = Mesher()
    m.tube([(0, 0, -0.10), (0, 0, T_POLE_L)], list(T_POLE_R), 8)
    pole = part("pole_starboard", m, ("pole_wood",))
    pole.location = pole_pivot(1)
    pole.rotation_euler = (0, pole_stowed_angle(1), 0)
    port = pole.copy()
    port.name = prefix + "pole_port"
    port.location = pole_pivot(-1)
    port.rotation_euler = (0, pole_stowed_angle(-1), 0)
    coll.objects.link(port)
    parts["pole_port"] = port
    m = Mesher()
    for side in (1, -1):
        piv = pole_pivot(side)
        inner, outer = side * (t_half(T_MAST_Y) - 0.06), piv.x + side * 0.10
        m.box(min(inner, outer), max(inner, outer), T_MAST_Y - 0.13, T_MAST_Y + 0.13, piv.z - 0.20, piv.z + 0.06)
    part("pole_steps", m, ("metal",))

    # the fish hold hatch: a coaming and a lid
    hy, hw, hl, hh = T_HATCH
    d = t_deck(hy)
    m = Mesher()
    m.box(-hw / 2, hw / 2, hy - hl / 2, hy + hl / 2, d - 0.10, d + hh)
    part("hatch_coaming", m, ("cabin_white",))
    m = Mesher()
    m.box(-hw / 2 - 0.05, hw / 2 + 0.05, hy - hl / 2 - 0.05, hy + hl / 2 + 0.05, d + hh - 0.03, d + hh + 0.07)
    part("hatch_lid", m, ("deck_buff",))

    troller_pit(part, T_PIT[0], t_deck)
    return parts


def troller_pit(part, py_, deck):
    """The trolling pit at the stern: a coaming round a dark slab, a gurdy
    on its pedestal each side; `deck(y, x)` is the deck it stands on."""
    _, pw, plen, ph = T_PIT
    d = deck(py_)
    m = Mesher()
    ox0, ox1, oy0, oy1 = -pw / 2 - 0.08, pw / 2 + 0.08, py_ - plen / 2 - 0.08, py_ + plen / 2 + 0.08
    ix0, ix1, iy0, iy1 = -pw / 2, pw / 2, py_ - plen / 2, py_ + plen / 2
    z0, z1 = d - 0.08, d + ph
    m.box(ox0, ox1, oy0, iy0, z0, z1)
    m.box(ox0, ox1, iy1, oy1, z0 - 0.005, z1 - 0.005)
    m.box(ox0 + 0.01, ix0 + 0.02, iy0 - 0.02, iy1 + 0.02, z0 + 0.005, z1 - 0.012)
    m.box(ix1 - 0.02, ox1 - 0.01, iy0 - 0.02, iy1 + 0.02, z0 + 0.008, z1 - 0.018)
    part("pit_coaming", m, ("cabin_white",))
    m = Mesher()
    m.box(ix0 + 0.01, ix1 - 0.01, iy0 + 0.01, iy1 - 0.01, d - 0.04, d + 0.025)
    part("pit", m, ("pit_dark",))
    m = Mesher()
    for side in (1, -1):
        x = side * T_GURDY_X
        dz = deck(py_ + 0.1, x)
        m.box(x - 0.08, x + 0.08, py_ + 0.02, py_ + 0.18, dz - 0.08, dz + 0.70)
        m.tube([(x - 0.15, py_ + 0.10, dz + 0.82), (x + 0.15, py_ + 0.10, dz + 0.82)], [0.20, 0.20], 10)
    part("gurdies", m, ("metal",))


def build_troller_canoe_parts(coll, variant, prefix):
    """What the double-ender does not share with the troller: the hull, the
    keel run aft to the sternpost, the rudder hung on it, the propeller in
    the aperture, the pit and gurdies moved forward."""
    parts = {}

    def part(name, m, surfaces):
        obj = finish(prefix + name, m, coll, [mat(s) for s in surfaces], variant)
        parts[name] = obj
        return obj

    m = Mesher()
    m.loft(canoe_hull_rings(), mirrored_mats(T_HULL_SEGS), cap_first=False, cap_last=False)
    part("hull", m, ("bottom_red", "boot_black", "hull_white", "trim_green", "cabin_white", "deck_buff"))
    ys = (3.6, 3.0, 2.0, 1.5, -2.0, -3.0, -4.0, -4.5, T_CANOE_KEEL_AFT_Y)
    poly = [(T_CANOE_KEEL_AFT_Y, -T_DRAFT), T_KEEL_FWD] + [(y, c_keel(y) + 0.12) for y in ys]
    m = Mesher()
    m.prism(poly, "x", -T_KEEL_HALF, T_KEEL_HALF)
    part("keel", m, ("bottom_red",))
    y0, y1, zb = T_CANOE_RUDDER
    m = Mesher()
    m.prism([(y0, zb), (y1, zb + 0.10), (y1, c_keel(y1) + 0.10), (y0, c_keel(y0) + 0.10)], "x", -0.05, 0.05)
    part("rudder", m, ("bottom_red",))
    _, pz, pr = T_PROP
    m = Mesher()
    m.tube([(0, T_CANOE_KEEL_AFT_Y + 0.15, pz), (0, T_CANOE_PROP_Y + 0.05, pz)], [0.05, 0.05], 8)
    prop_blades(m, (0, T_CANOE_PROP_Y, pz), (0, -1, 0), pr, 0.10, 0.22, 3, 0)
    part("propeller", m, ("metal",))
    troller_pit(part, T_CANOE_PIT_Y, lambda y, x=0.0: t_deck(y, x, canoe=True))
    return parts


def build_troller_mizzen_extras(coll, variant, prefix):
    """A mizzen mast just forward of the trolling pit with a boom to the
    stern and a flat riding sail, a stay to the mainmast and a sheet to the
    transom."""
    d = t_deck(T_MIZZEN_Y)
    top = d + T_MIZZEN_H
    bz, by = T_MIZZEN_BOOM
    m = Mesher()
    m.tube([(0, T_MIZZEN_Y, d - 0.10), (0, T_MIZZEN_Y, top)], [0.08, 0.05], 8)
    m.tube([(0, T_MIZZEN_Y - 0.03, d + bz), (0, by, d + bz)], [0.055, 0.045], 8, up=(0, 0, 1))
    spars = finish(prefix + "mizzen_spars", m, coll, [mat("spar_white")], variant)
    luff_y = T_MIZZEN_Y - 0.075
    m = Mesher()
    m.sheet(sail_grid(Vector((0, luff_y, d + bz + 0.10)), Vector((0, luff_y, top - 0.25)),
                      Vector((0, by + 0.10, d + bz + 0.10)), Vector((0, luff_y - 0.10, top - 0.25)),
                      6, 5, 0.03, 0.0, Vector((-1, 0, 0))), SAIL_T)
    sail = finish(prefix + "mizzen_sail", m, coll, [mat("sail_tan")], variant)
    m = Mesher()
    m.line((0, T_MIZZEN_Y + 0.04, top - 0.05), (0, T_MAST_Y - 0.06, t_deck(T_MAST_Y) + 6.0), 0.025)
    ty = T_TRANSOM_WL_Y - (t_sheer(T_TRANSOM_WL_Y) + T_BULWARK) * math.tan(T_TRANSOM_RAKE) + 0.07
    m.line((0, by + 0.05, d + bz - 0.04), (0, ty, t_sheer(T_TRANSOM_WL_Y) + T_BULWARK - 0.03), 0.03, running=True)
    lines = finish(prefix + "mizzen_lines", m, coll, [mat("line")], variant)
    return [spars, sail, lines]


RED_SET = {                       # troller_red's own colours, by the troller's surface they replace
    f"{PROP}_bottom_red": f"{PROP}_bottom_green",
    f"{PROP}_trim_green": f"{PROP}_trim_red",
    f"{PROP}_deck_buff": f"{PROP}_deck_grey",
    f"{PROP}_door": f"{PROP}_door_red",
    f"{PROP}_roof_grey": f"{PROP}_roof_red",
}


def recoloured_copies(src_parts, names, coll, variant, old_prefix, new_prefix, swap):
    """Copies of `names` with their own meshes (same shape) carrying the
    swapped materials; the rest of a variant links its meshes."""
    out = {}
    for name in names:
        src = src_parts[name]
        dup = src.copy()
        dup.data = src.data.copy()
        dup.name = dup.data.name = new_prefix + src.name[len(old_prefix):]
        for i, mt in enumerate(dup.data.materials):
            if mt is not None and mt.name in swap:
                dup.data.materials[i] = material(swap[mt.name])
        dup["kyt_variant"] = variant
        coll.objects.link(dup)
        out[name] = dup
    return out


def build_poles_down_extras(coll, variant, prefix):
    """The lifts, tag lines and stabilisers of the poles-down variant."""
    lines, stab = Mesher(), Mesher()
    cz = t_sheer(T_MAST_Y) + T_CROSSTREE[1]
    for side in (1, -1):
        a = pole_down_angle(side)
        lines.line((side * (T_CROSSTREE[0] - 0.05), T_MAST_Y, cz + 0.02), pole_point(side, a, 0.62), 0.03)
        for frac, back, depth in ((1.0, 3.2, -1.4), (0.55, 2.4, -1.1)):
            p = pole_point(side, a, frac)
            lines.line(p, Vector((p.x, p.y - back, depth)), 0.02)
        p = pole_point(side, a, 0.42)
        bird = Vector((p.x, p.y + 0.4, -1.9))
        stab.line(p, bird + Vector((0, 0, 0.25)), 0.035)
        # the bird: a chunky delta plate nose-down, a fin on its back
        stab.prism([(bird.y + 0.35, bird.z), (bird.y - 0.30, bird.z + 0.10), (bird.y - 0.30, bird.z - 0.10)],
                   "x", bird.x - 0.28, bird.x + 0.28)
        stab.box(bird.x - 0.02, bird.x + 0.02, bird.y - 0.28, bird.y + 0.10, bird.z + 0.05, bird.z + 0.30)
    lines_obj = finish(prefix + "pole_lines", lines, coll, [mat("line")], variant)
    stab_obj = finish(prefix + "stabilisers", stab, coll, [mat("metal")], variant)
    return [lines_obj, stab_obj]


# --- the skiff -------------------------------------------------------------------

def sk_sheer(y):
    if y >= SK_SHEER_LOW_Y:
        u = clamp((y - SK_SHEER_LOW_Y) / (SK_STEM_Y - SK_SHEER_LOW_Y), 0, 1)
        return SK_SHEER_MID + (SK_SHEER_BOW - SK_SHEER_MID) * u ** 2
    u = clamp((SK_SHEER_LOW_Y - y) / (SK_SHEER_LOW_Y - SK_TRANSOM_WL_Y), 0, 1.2)
    return SK_SHEER_MID + (SK_SHEER_STERN - SK_SHEER_MID) * u ** 2


def sk_half(y):
    if y >= SK_MAX_Y:
        u = clamp((y - SK_MAX_Y) / (SK_STEM_Y - SK_MAX_Y), 0, 1)
        return SK_HALF * max(0.0, 1 - u ** 2.0) ** 0.5
    u = clamp((SK_MAX_Y - y) / (SK_MAX_Y - SK_TRANSOM_WL_Y), 0, 1)
    return SK_HALF - (SK_HALF - SK_TRANSOM_HALF) * u ** 2


def sk_keel(y):
    fy, fz = SK_FOREFOOT
    if y >= fy:
        return fz + (SK_SHEER_BOW - fz) * clamp((y - fy) / (SK_STEM_Y - fy), 0, 1)
    if y >= 0.5:
        return SK_K + (fz - SK_K) * ((y - 0.5) / (fy - 0.5)) ** 2
    if y >= -1.5:
        return SK_K
    u = clamp((-1.5 - y) / (-1.5 - SK_TRANSOM_WL_Y), 0, 1)
    return SK_K + (SK_K_STERN - SK_K) * u ** 2


def sk_outer(y):
    """The skiff's outer section (x, z) from the keel strip: a modified V to a
    hard chine, flared sides to the gunwale."""
    K, S, B = sk_keel(y), sk_sheer(y), sk_half(y)
    s = clamp((y - 0.3) / (SK_STEM_Y - 0.3), 0, 1)
    kw = SK_KW * (1 - s)
    bc = max(kw, B * (0.84 - 0.18 * s))
    dr = math.radians(12 + 14 * s)
    zc = min(K + (bc - kw) * math.tan(dr), K + 0.85 * (S - K))
    return [(kw, K), (bc, zc), (B, S)]


SK_HULL_SEGS = (0, 0, 0, 1, 2, 3, 4)   # aluminium bottom, green topsides, gunwale cap, inside, floor


def sk_ring(y, closed):
    K, S, B = sk_keel(y), sk_sheer(y), sk_half(y)
    outer = sk_outer(y)
    (kw, _), (bc, zc), _ = outer
    zw = min(max(0.0, zc), S)
    pts = [(0.0, K), (kw, K), (bc, zc), (polyline_x(outer, zw), zw), (B, S)]
    gi = max(0.0, B - SK_GW)
    if closed:
        pts += [(gi, S), (0.5 * gi, S), (0.0, S)]
    else:
        zf = K + SK_FLOOR
        xi = max(0.02, polyline_x(outer, zf) - SK_WALL)
        pts += [(gi, S), (xi, zf), (0.0, zf)]
    return pts


def sk_inner_x(y, z):
    """The inside face of the skiff's side at (y, z), between the gunwale and
    the floor's edge."""
    p = sk_ring(y, False)
    (gi, S), (xi, zf) = p[5], p[6]
    return lerp(xi, gi, (z - zf) / (S - zf))


def sk_floor(y):
    return sk_keel(y) + SK_FLOOR


def sk_stations():
    st = [(SK_TRANSOM_WL_Y, True, True), (SK_TRANSOM_WL_Y + 0.06, False, True)]
    st += [(y, False, False) for y in (-2.2, -1.6, -0.9, -0.3, 0.3, 0.9, 1.35, SK_FOREDECK_Y - 0.02)]
    st += [(y, True, False) for y in (SK_FOREDECK_Y, 2.0, 2.3, 2.55, 2.68, SK_STEM_Y)]
    return st


def skiff_hull_rings():
    rings = []
    for y, closed, rk in sk_stations():
        y_of = raked(y, SK_RAKE) if rk else (lambda z, y=y: y)
        rings.append(mirror_ring(sk_ring(y, closed), y_of))
    return rings


def bench_top(i):
    y0, y1 = SK_BENCHES[i]
    return max(sk_floor(y0), sk_floor(y1)) + SK_SEAT_H


def seat_markers():
    """Where four seated anglers go: the helmsman on the aft bench to port by
    the tiller, two on the middle bench, one forward."""
    mid = lambda i: sum(SK_BENCHES[i]) / 2
    return [("angler_seat_1", (-0.42, mid(0), bench_top(0))),
            ("angler_seat_2", (0.42, mid(1), bench_top(1))),
            ("angler_seat_3", (-0.42, mid(1), bench_top(1))),
            ("angler_seat_4", (0.0, mid(2), bench_top(2)))]


def build_skiff(coll, variant="skiff", prefix="skiff_"):
    parts = {}

    def part(name, m, surfaces):
        obj = finish(prefix + name, m, coll, [mat(s) for s in surfaces], variant)
        parts[name] = obj
        return obj

    m = Mesher()
    m.loft(skiff_hull_rings(), mirrored_mats(SK_HULL_SEGS), cap_first=True, cap_last=False, cap_mats=(1, 1))
    part("hull", m, ("aluminium", "skiff_green", "aluminium", "aluminium", "floor_grey"))

    # the benches: buoyancy boxes wall to wall, their ends 2 cm into the
    # sides, which flare, so each end follows the side
    m = Mesher()
    for i, (y0, y1) in enumerate(SK_BENCHES):
        z0, z1 = min(sk_floor(y0), sk_floor(y1)) - 0.012, bench_top(i)
        ring = lambda y: [(sk_inner_x(y, z0) + 0.02, y, z0), (sk_inner_x(y, z1) + 0.02, y, z1),
                          (-sk_inner_x(y, z1) - 0.02, y, z1), (-sk_inner_x(y, z0) - 0.02, y, z0)]
        m.loft([ring(y0), ring(y1)], [0, 0, 0, 0])
    part("benches", m, ("seat_tan",))

    # the outboard on the transom: clamp bracket, cowling, leg, plate,
    # gearcase, skeg, propeller and the tiller arm reaching to the helmsman
    S = sk_sheer(SK_TRANSOM_WL_Y)
    m = Mesher()
    m.box(-0.13, 0.13, -2.92, -2.70, S - 0.22, S + 0.07, 1)
    m.prism([(-2.86, S + 0.05), (-3.40, S + 0.05), (-3.45, S + 0.36), (-3.34, S + 0.62), (-2.97, S + 0.645),
             (-2.84, S + 0.40)], "x", -0.21, 0.21, 0)
    m.box(-0.16, 0.16, -3.32, -2.92, S - 0.10, S + 0.075, 0)
    m.box(-0.075, 0.075, -3.24, -3.00, -0.21, S - 0.08, 0)
    m.box(-0.17, 0.17, -3.40, -2.94, -0.215, -0.185, 0)
    m.box(-0.065, 0.065, -3.34, -2.90, -0.40, -0.20, 0)
    m.box(-0.02, 0.02, -3.30, -3.08, -0.56, -0.38, 0)
    prop_blades(m, (0, -3.39, -0.30), (0, -1, 0), 0.16, 0.05, 0.10, 3, 1, chord=0.09, thick=0.02)
    arm0, arm1 = Vector((0, -2.83, S + 0.30)), Vector((-0.34, -2.20, S + 0.12))
    ad = (arm1 - arm0).normalized()
    m.tube([arm0, arm1], [0.035, 0.032], 6, 0)
    m.tube([arm1 - ad * 0.16, arm1 + ad * 0.04], [0.048, 0.048], 6, 1)            # the grip
    part("outboard", m, ("outboard_black", "metal"))

    # rod holders on the gunwale, four rods standing in them (one mesh,
    # linked copies), leaning out and aft
    holders = []
    for y in (-1.95, 0.55):
        for side in (1, -1):
            x = side * (sk_half(y) - SK_GW / 2)
            holders.append((side, Vector((x, y, sk_sheer(y)))))
    m = Mesher()
    rod_dirs = []
    for side, p in holders:
        d = Vector((side * math.sin(math.radians(38)), -math.sin(math.radians(14)), math.cos(math.radians(38))))
        d.normalize()
        rod_dirs.append(d)
        m.tube([p - d * 0.20, p + d * 0.07], [0.035, 0.035], 6)
    part("rod_holders", m, ("metal",))
    m = Mesher()
    m.tube([(0, 0, 0.0), (0, 0, 2.10)], [0.022, 0.010], 6, 0)
    m.box(0.02, 0.10, -0.045, 0.045, 0.30, 0.40, 1)          # the reel, under the rod
    first = None
    for k, ((side, p), d) in enumerate(zip(holders, rod_dirs)):
        if first is None:
            obj = part("rod_1", m, ("rod_dark", "metal"))
            first = obj
        else:
            obj = first.copy()
            obj.name = f"{prefix}rod_{k + 1}"
            coll.objects.link(obj)
            parts[f"rod_{k + 1}"] = obj
        obj.location = p - d * 0.18
        obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()

    # a red fuel tank in the stern well, a white cooler between the benches
    zf = sk_floor(-2.4)
    m = Mesher()
    m.box(0.30, 0.62, -2.56, -2.26, zf - 0.015, zf + 0.27)
    m.tube([(0.40, -2.41, zf + 0.25), (0.40, -2.41, zf + 0.32)], [0.035, 0.035], 6)
    part("fuel_tank", m, ("tank_red",))
    zf = sk_floor(0.5)
    m = Mesher()
    m.box(-0.32, 0.32, 0.30, 0.66, zf - 0.018, zf + 0.35)
    m.box(-0.34, 0.34, 0.28, 0.68, zf + 0.33, zf + 0.40)
    part("cooler", m, ("cooler_white",))
    return parts


# --- the centre-console skiff -------------------------------------------------------

def cs_sheer(y):
    if y >= CS_SHEER_LOW_Y:
        u = clamp((y - CS_SHEER_LOW_Y) / (CS_STEM_Y - CS_SHEER_LOW_Y), 0, 1)
        return CS_SHEER_MID + (CS_SHEER_BOW - CS_SHEER_MID) * u ** 2
    u = clamp((CS_SHEER_LOW_Y - y) / (CS_SHEER_LOW_Y - CS_TRANSOM_WL_Y), 0, 1.2)
    return CS_SHEER_MID + (CS_SHEER_STERN - CS_SHEER_MID) * u ** 2


def cs_half(y):
    if y >= CS_MAX_Y:
        u = clamp((y - CS_MAX_Y) / (CS_STEM_Y - CS_MAX_Y), 0, 1)
        return CS_HALF * max(0.0, 1 - u ** 2.1) ** 0.55
    u = clamp((CS_MAX_Y - y) / (CS_MAX_Y - CS_TRANSOM_WL_Y), 0, 1)
    return CS_HALF - (CS_HALF - CS_TRANSOM_HALF) * u ** 2


def cs_keel(y):
    fy, fz = CS_FOREFOOT
    if y >= fy:
        return fz + (CS_SHEER_BOW - fz) * clamp((y - fy) / (CS_STEM_Y - fy), 0, 1)
    if y >= 0.3:
        return CS_K + (fz - CS_K) * ((y - 0.3) / (fy - 0.3)) ** 2
    if y >= -1.5:
        return CS_K
    u = clamp((-1.5 - y) / (-1.5 - CS_TRANSOM_WL_Y), 0, 1)
    return CS_K + (CS_K_STERN - CS_K) * u ** 2


def cs_outer(y):
    """A deep V to a chine, flared topsides: 16 degrees deadrise aft, 32 at
    the bow."""
    K, S, B = cs_keel(y), cs_sheer(y), cs_half(y)
    s = clamp((y - 0.3) / (CS_STEM_Y - 0.3), 0, 1)
    kw = CS_KW * (1 - s)
    bc = max(kw, B * (0.86 - 0.20 * s))
    dr = math.radians(16 + 16 * s)
    zc = min(K + (bc - kw) * math.tan(dr), K + 0.80 * (S - K))
    return [(kw, K), (bc, zc), (B, S)]


CS_HULL_SEGS = (0, 0, 0, 1, 2, 3, 3, 4)   # bottom paint, white topsides, navy stripe, white cap and liner, non-skid


def cs_ring(y, closed):
    K, S, B = cs_keel(y), cs_sheer(y), cs_half(y)
    outer = cs_outer(y)
    (kw, _), (bc, zc), _ = outer
    zw = min(max(0.0, zc), S)
    zs = max(zw, S - CS_STRIPE)
    pts = [(0.0, K), (kw, K), (bc, zc), (polyline_x(outer, zw), zw), (polyline_x(outer, zs), zs), (B, S)]
    gi = max(0.0, B - CS_GW)
    if closed:
        pts += [(gi, S), (0.5 * gi, S), (0.0, S)]
    else:
        zf = K + CS_FLOOR
        xi = max(0.02, polyline_x(outer, zf) - CS_WALL)
        pts += [(gi, S), (xi, zf), (0.0, zf)]
    return pts


def cs_inner_x(y, z):
    p = cs_ring(y, False)
    (gi, S), (xi, zf) = p[6], p[7]
    return lerp(xi, gi, (z - zf) / (S - zf))


def cs_floor(y):
    return cs_keel(y) + CS_FLOOR


def console_hull_rings():
    st = [(CS_TRANSOM_WL_Y, True, True), (CS_TRANSOM_WL_Y + 0.07, False, True)]
    st += [(y, False, False) for y in (-2.2, -1.6, -0.9, -0.3, 0.3, 0.9, 1.25, CS_FOREDECK_Y - 0.02)]
    st += [(y, True, False) for y in (CS_FOREDECK_Y, 1.95, 2.3, 2.6, 2.77, CS_STEM_Y)]
    rings = []
    for y, closed, rk in st:
        y_of = raked(y, CS_RAKE) if rk else (lambda z, y=y: y)
        rings.append(mirror_ring(cs_ring(y, closed), y_of))
    return rings


def console_seats():
    """(marker, x, y, seat top): the helmsman on the leaning-post seat, one
    on the cooler seat in front of the console, two on the stern bench."""
    a, length, _ = CS_CONSOLE
    zf = cs_floor(a + length / 2)
    b0, b1 = CS_STERN_BENCH
    return [("console_angler_seat_1", 0.0, a - 0.575, zf + 0.62),
            ("console_angler_seat_2", 0.0, a + length + 0.17, zf + 0.44),
            ("console_angler_seat_3", 0.45, (b0 + b1) / 2, max(cs_floor(b0), cs_floor(b1)) + 0.42),
            ("console_angler_seat_4", -0.45, (b0 + b1) / 2, max(cs_floor(b0), cs_floor(b1)) + 0.42)]


def build_skiff_console(coll, rod_src, variant="skiff_console", prefix="skiff_console_"):
    """An 18 ft fibreglass centre-console skiff: a deep-V white hull with a
    navy sheer stripe, a casting deck forward with a bow rail, the console
    with its windscreen and wheel, a leaning-post seat behind it and a cooler
    seat in front, a stern bench, a big white outboard on hydraulic steering,
    and the skiff's rods (linked) in four gunwale holders."""
    parts = {}

    def part(name, m, surfaces):
        obj = finish(prefix + name, m, coll, [mat(s) for s in surfaces], variant)
        parts[name] = obj
        return obj

    m = Mesher()
    m.loft(console_hull_rings(), mirrored_mats(CS_HULL_SEGS), cap_first=True, cap_last=False, cap_mats=(1, 1))
    part("hull", m, ("bottom_navy", "hull_white", "stripe_navy", "cabin_white", "deck_cream"))

    # the console: a moulded box with a sloped dash facing the helmsman
    a, length, hw = CS_CONSOLE
    zf = cs_floor(a + length / 2)
    m = Mesher()
    m.prism([(a, zf - 0.03), (a + length, zf - 0.03), (a + length, zf + 0.80), (a + 0.20, zf + 1.00),
             (a, zf + 0.88)], "x", -hw, hw, 0)
    part("console", m, ("cabin_white",))
    # its windscreen (tinted), the wheel on the dash, a throttle box
    m = Mesher()
    w0, w1 = Vector((0, a + 0.64, zf + 0.79)), Vector((0, a + 0.30, zf + 1.32))
    wv = (w1 - w0).normalized()
    wn = Vector((1, 0, 0)).cross(wv).normalized()
    m.obox((w0 + w1) / 2, (1, 0, 0), wv, wn, hw + 0.04, (w1 - w0).length / 2, 0.0125, 0)
    dash = (Vector((0, a + 0.20, zf + 1.00)) - Vector((0, a, zf + 0.88))).normalized()
    axis = Vector((1, 0, 0)).cross(dash).normalized()
    if axis.y > 0:
        axis = -axis
    hub = Vector((-0.08, a + 0.08, zf + 0.93)) + axis * 0.14
    m.tube([hub - axis * 0.16, hub + axis * 0.03], [0.035, 0.035], 6, 1)
    m.torus(hub, axis, 0.17, 0.022, 12, 4, 1)
    e1 = axis.orthogonal().normalized()
    for k in range(3):
        sp = Matrix.Rotation(math.tau * k / 3, 3, axis) @ e1
        m.obox(hub + sp * 0.085, sp, axis, sp.cross(axis), 0.085, 0.012, 0.012, 1)
    m.box(0.12, 0.26, a - 0.03, a + 0.10, zf + 0.86, zf + 1.01, 1)
    part("helm", m, ("glass", "metal"))

    # the seats: a leaning post with its cushion, the cooler seat on the
    # console's front, the stern bench wall to wall with its cushion
    m = Mesher()
    m.box(-0.22, 0.22, a - 0.75, a - 0.40, zf - 0.025, zf + 0.50, 0)
    m.box(-0.34, 0.34, a - 0.82, a - 0.33, zf + 0.48, zf + 0.62, 1)
    m.box(-0.34, 0.34, a + length - 0.02, a + length + 0.36, zf - 0.02, zf + 0.37, 0)
    m.box(-0.35, 0.35, a + length - 0.01, a + length + 0.38, zf + 0.35, zf + 0.44, 1)
    b0, b1 = CS_STERN_BENCH
    z0, z1 = min(cs_floor(b0), cs_floor(b1)) - 0.015, max(cs_floor(b0), cs_floor(b1)) + 0.42
    ring = lambda y: [(cs_inner_x(y, z0) + 0.025, y, z0), (cs_inner_x(y, z1 - 0.07) + 0.025, y, z1 - 0.07),
                      (-cs_inner_x(y, z1 - 0.07) - 0.025, y, z1 - 0.07), (-cs_inner_x(y, z0) - 0.025, y, z0)]
    m.loft([ring(b0), ring(b1)], [0, 0, 0, 0])
    m.box(-0.75, 0.75, b0 + 0.03, b1 - 0.03, z1 - 0.09, z1, 1)
    part("seats", m, ("cabin_white", "cushion_teal"))

    # the bow rail round the casting deck
    m = Mesher()
    hz = lambda y: cs_sheer(y) + 0.42
    side_pts = [(cs_half(y) - CS_GW / 2, y) for y in (0.95, 1.65, 2.30)]
    tip_y = CS_STEM_Y - 0.14
    path = [Vector((x, y, hz(y))) for x, y in side_pts] + [Vector((0.0, tip_y, hz(tip_y)))] + \
           [Vector((-x, y, hz(y))) for x, y in reversed(side_pts)]
    for p0, p1 in zip(path, path[1:]):
        m.tube([p0, p1], [0.022, 0.022], 6)
    for p in path:
        m.tube([(p.x, p.y, cs_sheer(p.y) - 0.04), p], [0.02, 0.02], 6)
    part("bow_rail", m, ("metal",))

    # the outboard: a big white motor on the transom, steered from the
    # console, no tiller
    S = cs_sheer(CS_TRANSOM_WL_Y)
    m = Mesher()
    m.box(-0.15, 0.15, -2.98, -2.75, S - 0.25, S + 0.08, 1)
    m.prism([(-2.93, S + 0.06), (-3.55, S + 0.06), (-3.60, S + 0.42), (-3.47, S + 0.74), (-3.05, S + 0.77),
             (-2.91, S + 0.48)], "x", -0.25, 0.25, 0)
    m.box(-0.19, 0.19, -3.45, -2.99, S - 0.12, S + 0.085, 0)
    m.box(-0.085, 0.085, -3.35, -3.08, -0.275, S - 0.10, 0)
    m.box(-0.20, 0.20, -3.52, -3.02, -0.285, -0.255, 0)
    m.box(-0.075, 0.075, -3.46, -2.98, -0.48, -0.265, 0)
    m.box(-0.022, 0.022, -3.40, -3.15, -0.66, -0.46, 0)
    prop_blades(m, (0, -3.51, -0.37), (0, -1, 0), 0.19, 0.06, 0.11, 3, 1, chord=0.10, thick=0.02)
    part("outboard", m, ("outboard_white", "metal"))

    # rod holders and the skiff's rods (its mesh, linked)
    holders = []
    for y in (-1.70, 0.20):
        for side in (1, -1):
            holders.append((side, Vector((side * (cs_half(y) - CS_GW / 2), y, cs_sheer(y)))))
    m = Mesher()
    dirs = []
    for side, p in holders:
        d = Vector((side * math.sin(math.radians(35)), -math.sin(math.radians(12)), math.cos(math.radians(35))))
        d.normalize()
        dirs.append(d)
        m.tube([p - d * 0.20, p + d * 0.07], [0.035, 0.035], 6)
    part("rod_holders", m, ("metal",))
    for k, ((side, p), d) in enumerate(zip(holders, dirs)):
        rod = rod_src.copy()
        rod.name = f"{prefix}rod_{k + 1}"
        rod["kyt_variant"] = variant
        rod.location = p - d * 0.18
        rod.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        coll.objects.link(rod)
        parts[f"rod_{k + 1}"] = rod
    return parts


# --- the sloop -------------------------------------------------------------------

def sl_sheer(y):
    if y >= SL_SHEER_LOW_Y:
        u = clamp((y - SL_SHEER_LOW_Y) / (SL_STEM_Y - SL_SHEER_LOW_Y), 0, 1)
        return SL_SHEER_LOW + (SL_SHEER_BOW - SL_SHEER_LOW) * u ** 2
    u = clamp((SL_SHEER_LOW_Y - y) / (SL_SHEER_LOW_Y - SL_TRANSOM_WL_Y), 0, 1.2)
    return SL_SHEER_LOW + (SL_SHEER_STERN - SL_SHEER_LOW) * u ** 2


def sl_half(y):
    if y >= SL_MAX_Y:
        u = clamp((y - SL_MAX_Y) / (SL_STEM_Y - SL_MAX_Y), 0, 1)
        return SL_HALF * max(0.0, 1 - u ** 1.9) ** 0.6
    u = clamp((SL_MAX_Y - y) / (SL_MAX_Y - SL_TRANSOM_WL_Y), 0, 1)
    return SL_HALF - (SL_HALF - SL_TRANSOM_HALF) * u ** 2


def sl_keel(y):
    fy, fz = SL_FOREFOOT
    if y >= fy:
        return fz + (SL_SHEER_BOW - fz) * clamp((y - fy) / (SL_STEM_Y - fy), 0, 1)
    if y >= 0.6:
        return SL_K + (fz - SL_K) * ((y - 0.6) / (fy - 0.6)) ** 2
    if y >= -1.0:
        return SL_K
    u = clamp((-1.0 - y) / (-1.0 - SL_TRANSOM_WL_Y), 0, 1)
    return SL_K + (SL_K_STERN - SL_K) * u ** 1.7


def sl_section_x(y, z):
    K, S, B = sl_keel(y), sl_sheer(y), sl_half(y)
    if S - K < 1e-6 or B <= 0.0:
        return 0.0
    s = clamp((y - 0.5) / (SL_STEM_Y - 0.5), 0, 1)
    p, tb = 2.2 - 0.9 * s, 0.62 + 0.25 * s
    kw = min(SL_KW * (1 - s), 0.9 * B)
    bb = 0.96 * B
    t = clamp((z - K) / (S - K), 0, 1)
    if t <= tb:
        return kw + (bb - kw) * (1 - (1 - t / tb) ** p) ** (1 / p)
    return bb + (B - bb) * (t - tb) / (1 - tb)


# bottom, white, navy (boot and sheer stripes), teak toe rail, deck, white coamings
SL_HULL_SEGS = (0, 0, 0, 0, 2, 1, 2, 3, 3, 3, 4, 5, 5, 5, 4, 5, 4)


def sl_deck_x(y):
    """The deck's half-width inside the toe rail."""
    return max(0.0, sl_half(y) - SL_TOE[1])


def sl_deck(y, x=0.0):
    bd, S = sl_deck_x(y), sl_sheer(y)
    if bd <= 1e-6:
        return S
    return S + SL_CAMBER * (1 - min(1.0, (abs(x) / bd)) ** 2)


def sl_ring(y, open_):
    K, S, B = sl_keel(y), sl_sheer(y), sl_half(y)

    def px(z):
        z = min(max(z, K), S)
        return (sl_section_x(y, z), z)

    th, tw = SL_TOE
    bd = max(0.0, B - tw)
    pts = [(0.0, K), px(K), px(-0.40), px(-0.22), px(0.0), px(SL_BOOT), px(S - SL_STRIPE),
           (B, S), (B, S + th), (bd, S + th), (bd, S)]
    x10, x12, x14 = (min(SL_COAMING[0], 0.80 * bd), min(SL_COAMING[1], 0.72 * bd), min(SL_SEAT[0], 0.42 * bd))
    d = lambda x: sl_deck(y, x)
    if open_:
        top = S + SL_COAMING[2]
        seat = S + SL_SEAT[1]
        sole = S - SL_SOLE
        pts += [(x10, d(x10)), (x10, top), (x12, top), (x12, seat), (x14, seat), (x14, sole), (0.0, sole)]
    else:
        pts += [(x10, d(x10)), (x10, d(x10)), (x12, d(x12)), (x12, d(x12)), (x14, d(x14)), (x14, d(x14)),
                (0.0, S + SL_CAMBER)]
    return pts


def sl_stations(reverse=False):
    """(nominal y, cockpit open, raked: True, or "reverse" for the 1990s
    transom leaning forward at the top)."""
    c0, c1 = SL_COCKPIT
    st = [(SL_REV_TRANSOM_WL_Y, False, "reverse") if reverse else (SL_TRANSOM_WL_Y, False, True),
          (c0 - 0.02, False, False)]
    st += [(y, True, False) for y in (c0, -3.5, -2.9, -2.4, c1)]
    st += [(y, False, False) for y in (c1 + 0.02, -1.0, -0.2, 0.6, 1.4, 2.2, 2.9, 3.5, 3.9, 4.2, 4.42, 4.55,
                                       SL_STEM_Y)]
    return st


def sloop_hull_rings(reverse=False):
    rings, opens = [], []
    for y, open_, rk in sl_stations(reverse):
        if rk == "reverse":
            y_of = raked(y, -SL_REV_RAKE)
        else:
            y_of = raked(y, SL_RAKE) if rk else (lambda z, y=y: y)
        rings.append(mirror_ring(sl_ring(y, open_), y_of))
        opens.append(open_)
    return rings, opens


def sl_mast_base():
    return Vector((0, SL_MAST_Y, sl_deck(SL_MAST_Y)))


def sl_masthead_z():
    return sl_sheer(SL_MAST_Y) + SL_MAST_H


def sl_gooseneck():
    return Vector((0, SL_MAST_Y - SL_MAST_HALF[1] + 0.01, SL_TRUNK_TOP + SL_BOOM[0]))


def sl_forestay():
    return (Vector((0, SL_STEM_Y - 0.08, SL_SHEER_BOW + 0.13)),
            Vector((0, SL_MAST_Y + SL_MAST_HALF[1] - 0.01, sl_masthead_z() - 0.10)))


def sl_boom_point(along, angle, dz=0.0):
    """A point `along` the boom from the gooseneck, the boom turned `angle`."""
    return sl_gooseneck() + Matrix.Rotation(angle, 3, "Z") @ Vector((0, -along, dz))


def sl_traveller():
    y = -2.75
    return y, sl_sheer(y) - SL_SOLE


SL_HULL_SURFACES = ("bottom_navy", "hull_white", "stripe_navy", "teak", "deck_cream", "cabin_white")


def sloop_hull_mesher(reverse=False):
    rings, opens = sloop_hull_rings(reverse)
    seg = mirrored_mats(SL_HULL_SEGS)
    n_side = len(SL_HULL_SEGS)

    def pick(k, i):
        j = i if i < n_side else 2 * n_side - 1 - i
        if j >= 11 and not opens[k] and not opens[k + 1]:
            return 4                                  # the deck where the cockpit is shut
        return seg[i]

    m = Mesher()
    m.loft(rings, pick, cap_first=True, cap_last=False, cap_mats=(1, 1))
    return m


def sl_spreader_tips():
    sz = sl_sheer(SL_MAST_Y) + SL_SPREADER[0]
    span, sweep = SL_SPREADER[1], SL_SPREADER[2]
    return sz, {side: Vector((side * span, SL_MAST_Y - span * math.tan(sweep), sz)) for side in (1, -1)}


def sloop_standing_rigging(backstay_y=-4.50):
    """Forestay, backstay to `backstay_y` on the centreline, cap shrouds
    over the spreader tips, fore and aft lowers."""
    mz = sl_masthead_z()
    sz, tips = sl_spreader_tips()
    fs0, fs1 = sl_forestay()
    m = Mesher()
    m.line(fs0, fs1, 0.022)
    ys = backstay_y
    m.line((0, SL_MAST_Y - SL_MAST_HALF[1] + 0.01, mz - 0.05), (0, ys, sl_deck(ys) + 0.05), 0.022)
    for side in (1, -1):
        cy = SL_MAST_Y - 0.15
        cp = Vector((side * (sl_half(cy) - SL_CHAINPLATE), cy, sl_deck(cy, sl_half(cy) - SL_CHAINPLATE) + 0.02))
        m.line(cp, tips[side] + Vector((side * 0.03, 0, 0)), 0.02)
        m.line(tips[side] + Vector((side * 0.03, 0, 0)), (side * 0.05, SL_MAST_Y, mz - 0.25), 0.02)
        for ly in (SL_MAST_Y + 0.35, SL_MAST_Y - 0.65):
            lp = Vector((side * (sl_half(ly) - SL_CHAINPLATE - 0.04), ly,
                         sl_deck(ly, sl_half(ly) - SL_CHAINPLATE - 0.04) + 0.02))
            m.line(lp, (side * 0.06, SL_MAST_Y + (0.06 if ly > SL_MAST_Y else -0.06), sz - 0.12), 0.02)
    return m


def sloop_rails(push_fwd=(1.06, -3.92), push_aft=(0.95, -4.42), double=False):
    """Pulpit, pushpit (its forward and aft corners), stanchions and the
    lifeline; `double` adds the lower lifeline at SL_LOWER_LIFELINE."""
    m = Mesher()
    pz = sl_deck(3.85) + 0.66
    pulpit = [Vector((0.38, 3.85, pz)), Vector((0.14, 4.36, pz)), Vector((-0.14, 4.36, pz)), Vector((-0.38, 3.85, pz))]
    for a, b in zip(pulpit, pulpit[1:]):
        m.tube([a, b], [0.024, 0.024], 6)
    for p in pulpit:
        m.tube([(p.x, p.y, sl_deck(p.y, p.x) - 0.04), p], [0.022, 0.022], 6)
    qz = sl_deck(-4.1) + 0.66
    (fx, fy), (ax, ay) = push_fwd, push_aft
    push = [Vector((fx, fy, qz)), Vector((ax, ay, qz)), Vector((-ax, ay, qz)), Vector((-fx, fy, qz))]
    for a, b in zip(push, push[1:]):
        m.tube([a, b], [0.024, 0.024], 6)
    for p in push:
        m.tube([(p.x, p.y, sl_deck(p.y, p.x) - 0.04), p], [0.022, 0.022], 6)
    lower = []
    for side in (1, -1):
        path = [pulpit[0 if side > 0 else 3]]
        low = []
        for y in (2.9, 1.6, 0.2, -1.2, -2.7):
            x = side * (sl_half(y) - 0.12)
            top = Vector((x, y, sl_deck(y, x) + 0.62))
            m.tube([(x, y, sl_deck(y, x) - 0.04), top + Vector((0, 0, 0.03))], [0.02, 0.02], 6)
            path.append(top)
            low.append(Vector((x, y, sl_deck(y, x) + SL_LOWER_LIFELINE)))
        path.append(push[0 if side > 0 else 3])
        for a, b in zip(path, path[1:]):
            m.line(a, b, 0.018)
        if double:
            p0, p1 = pulpit[0 if side > 0 else 3], push[0 if side > 0 else 3]
            ends = [Vector((p0.x, p0.y, sl_deck(p0.y, p0.x) + SL_LOWER_LIFELINE))] + low + \
                   [Vector((p1.x, p1.y, sl_deck(p1.y, p1.x) + SL_LOWER_LIFELINE))]
            lower.append(ends)
    for ends in lower:
        for a, b in zip(ends, ends[1:]):
            m.line(a, b, 0.016)
    return m


def build_sloop(coll, variant="sloop_moored", prefix="sloop_moored_"):
    parts = {}

    def part(name, m, surfaces):
        obj = finish(prefix + name, m, coll, [mat(s) for s in surfaces], variant)
        parts[name] = obj
        return obj

    part("hull", sloop_hull_mesher(), SL_HULL_SURFACES)

    # the fin keel: a foil lofted from inside the hull to its tip
    (r0, r1, rt), (t0, t1, tt), tz = SL_KEEL

    def foil(y_te, y_le, half, z):
        chord = y_le - y_te
        us = (0.0, 0.05, 0.2, 0.4, 0.7, 1.0)
        ts = (0.0, 0.6, 0.95, 1.0, 0.7, 0.08)
        up = [(half * t, y_le - chord * u, z) for u, t in zip(us, ts)]
        down = [(-half * t, y_le - chord * u, z) for u, t in zip(us, ts)][1:]
        return up + list(reversed(down))

    root_z = SL_K + 0.06
    m = Mesher()
    m.loft([foil(r0, r1, rt, root_z), foil(t0, t1, tt, tz)], [0] * 11)
    part("keel", m, ("bottom_navy",))

    # the spade rudder
    (le_t, te_t), (le_b, te_b), rz = SL_RUDDER
    m = Mesher()
    m.prism([(le_t, sl_keel(le_t) + 0.08), (le_b, rz), (te_b, rz + 0.03), (te_t, sl_keel(te_t) + 0.08)], "x",
            -0.04, 0.04)
    part("rudder", m, ("bottom_navy",))

    # the cabin trunk: a loft from its aft face to its raked front, the
    # sides planes leaning in
    ya, yf, yft = SL_TRUNK_Y
    xa, xf = SL_TRUNK_HALF
    zt = SL_TRUNK_TOP
    zb = min(sl_deck(ya, xa), sl_deck(yf, xf)) - 0.06
    tumble = 0.08
    xat = xa - tumble
    xft = xat + (xf - xa) * (yft - ya) / (yf - ya)
    aft = [(xa, ya, zb), (xat, ya, zt), (0, ya, zt + 0.05), (-xat, ya, zt), (-xa, ya, zb)]
    fwd = [(xf, yf, zb), (xft, yft, zt), (0, yft, zt + 0.05), (-xft, yft, zt), (-xf, yf, zb)]
    m = Mesher()
    m.loft([aft, fwd], [0] * 5)
    part("trunk", m, ("cabin_white",))

    # its ports: dark slabs with chamfered corners, 2 cm proud
    m = Mesher()
    for side in (1, -1):
        A = Vector((side * xa, ya, zb))
        Bv = Vector((side * xf, yf, zb))
        D = Vector((side * xat, ya, zt))
        su = (Bv - A).normalized()
        sv = (D - A) - su * (D - A).dot(su)
        sv.normalize()
        sn = su.cross(sv).normalized()
        if sn.x * side < 0:
            sn = -sn
        zc = zt - 0.21
        for along, w, h in ((0.95, 0.56, 0.16), (1.95, 0.56, 0.16), (2.90, 0.30, 0.14)):
            c = A + su * along + sv * ((zc - zb) / sv.z)
            k = min(w, h) * 0.3
            outline = [(-w / 2 + k, -h / 2), (w / 2 - k, -h / 2), (w / 2, -h / 2 + k), (w / 2, h / 2 - k),
                       (w / 2 - k, h / 2), (-w / 2 + k, h / 2), (-w / 2, h / 2 - k), (-w / 2, -h / 2 + k)]
            ring = lambda s: [c + su * a + sv * b + sn * s for a, b in outline]
            m.loft([ring(-0.02), ring(0.02)], [0] * 8)
    part("ports", m, ("glass",))

    # the sliding hatch with its sea hood, the washboards, the fore hatch
    m = Mesher()
    m.box(-0.38, 0.38, ya - 0.06, ya + 0.90, zt - 0.02, zt + 0.14)
    m.box(-0.30, 0.30, ya - 0.02, ya + 0.02, zb + 0.10, zt - 0.03, 1)
    fy = 2.65
    m.box(-0.30, 0.30, fy - 0.28, fy + 0.28, sl_deck(fy, 0.30) - 0.05, sl_deck(fy) + 0.11)
    part("hatches", m, ("cabin_white", "glass"))

    # the mast stepped on the trunk, its masthead fitting and VHF whip
    mz = sl_masthead_z()
    m = Mesher()
    m.tube([(0, SL_MAST_Y, zt - 0.06), (0, SL_MAST_Y, mz)], [1.0, 1.0], 8, 0,
           squash=SL_MAST_HALF)
    m.box(-0.07, 0.07, SL_MAST_Y - 0.20, SL_MAST_Y + 0.17, mz - 0.03, mz + 0.09, 1)
    m.tube([(0, SL_MAST_Y - 0.10, mz + 0.08), (0, SL_MAST_Y - 0.10, mz + 0.95)], [0.02, 0.012], 6, 1)
    part("mast", m, ("spar_silver", "metal"))

    # spreaders, swept aft
    sz, tips = sl_spreader_tips()
    m = Mesher()
    for side in (1, -1):
        m.tube([(side * 0.03, SL_MAST_Y, sz), tips[side]], [0.04, 0.03], 4, phase=math.pi / 4)
    part("spreaders", m, ("spar_silver",))

    # the standing rigging
    fs0, fs1 = sl_forestay()
    part("standing_rigging", sloop_standing_rigging(), ("metal",))

    # the stem fitting and the furler drum on it
    m = Mesher()
    m.box(-0.05, 0.05, SL_STEM_Y - 0.24, SL_STEM_Y - 0.02, SL_SHEER_BOW - 0.04, SL_SHEER_BOW + 0.14)
    ax = (fs1 - fs0).normalized()
    m.tube([fs0 + ax * 0.06, fs0 + ax * 0.24], [0.085, 0.085], 10)
    part("stem_fitting", m, ("metal",))

    # the boom from the gooseneck, its mesh at the gooseneck so the sailing
    # variant turns the same mesh
    m = Mesher()
    m.tube([(0, 0.07, 0), (0, -SL_BOOM[1], 0)], [1.0, 0.9], 8, up=(0, 0, 1), squash=(0.09, 0.06))
    boom = part("boom", m, ("spar_silver",))
    boom.location = sl_gooseneck()

    # rails: pulpit, pushpit, stanchions and the lifeline
    part("rails", sloop_rails(), ("metal",))

    # the primary winches on the coamings, the traveller, the tiller
    m = Mesher()
    wy = -2.30
    for side in (1, -1):
        x = side * (SL_COAMING[0] + SL_COAMING[1]) / 2
        base = sl_sheer(wy) + SL_COAMING[2]
        m.tube([(x, wy, base - 0.02), (x, wy, base + 0.12)], [0.085, 0.085], 8)
        m.tube([(x, wy, base + 0.11), (x, wy, base + 0.22)], [0.065, 0.05], 8)
    ty, tsole = sl_traveller()
    m.box(-SL_SEAT[0] - 0.02, SL_SEAT[0] + 0.02, ty - 0.04, ty + 0.04, tsole - 0.02, tsole + 0.05)
    part("deck_hardware", m, ("metal",))
    m = Mesher()
    sy = -3.80
    sole = sl_sheer(sy) - SL_SOLE
    m.box(-0.06, 0.06, sy - 0.06, sy + 0.06, sole - 0.03, sole + 0.10)
    m.tube([(0, sy, sole + 0.06), (0, -2.50, sole + 0.48)], [0.04, 0.032], 6)
    part("tiller", m, ("teak",))
    return parts


def build_sloop_moored_extras(coll, parts, variant, prefix):
    """The moored boat's furled sails and its slack running rigging."""
    out = []
    g = sl_gooseneck()
    # the sail cover over the main on the boom, tapering aft
    rings = []
    for along, w, h in ((0.02, 0.17, 0.42), (0.6, 0.16, 0.40), (1.7, 0.14, 0.33), (2.9, 0.115, 0.26),
                        (3.30, 0.10, 0.22), (3.38, 0.06, 0.14)):
        c = g + Vector((0, -along - 0.05, h / 2 - 0.05))
        rings.append([c + Vector((math.cos(t) * w, 0, math.sin(t) * h / 2))
                      for t in (math.tau * k / 8 for k in range(8))])
    m = Mesher()
    m.loft(rings, [0] * 8)
    out.append(finish(prefix + "sail_cover", m, coll, [mat("cover_blue")], variant))
    # the jib rolled on its furler: a spindle along the forestay
    fs0, fs1 = sl_forestay()
    ax = fs1 - fs0
    pts, radii = [], []
    for t, r in ((0.035, 0.06), (0.06, 0.115), (0.35, 0.10), (0.70, 0.07), (0.90, 0.035)):
        pts.append(fs0 + ax * t)
        radii.append(r)
    m = Mesher()
    m.tube(pts, radii, 8, phase=math.pi / 8)
    out.append(finish(prefix + "furled_jib", m, coll, [mat("cover_blue")], variant))
    # the topping lift and the mainsheet from the boom's end
    ty, tsole = sl_traveller()
    m = Mesher()
    m.line((0, SL_MAST_Y - SL_MAST_HALF[1] - 0.04, sl_masthead_z() - 0.15), sl_boom_point(SL_BOOM[1] - 0.12, 0, 0.06),
           0.02, running=True)
    m.line((0, ty, g.z - 0.07), (0.25, ty, tsole + 0.06), 0.04, running=True)
    out.append(finish(prefix + "running_rigging", m, coll, [mat("line")], variant))
    return out


def sail_grid(luff0, luff1, leech0, leech1, rows, cols, depth, twist, leeward, roach=0.0):
    """A sail's cambered surface: rows from foot to head; each row's chord
    from the luff to the leech, bellied `depth` of its length toward
    `leeward` (a unit vector), peaking a third of the way aft, the leech
    turned `twist` further off at the head and pushed out by `roach`."""
    grid = []
    for r in range(rows):
        v = r / (rows - 1)
        L = luff0.lerp(luff1, v)
        R = leech0.lerp(leech1, v)
        ch = R - L
        R = L + Matrix.Rotation(twist * v, 3, "Z") @ ch
        if roach:
            R = R + ch.normalized() * roach * math.sin(math.pi * v)
        ch = R - L
        nrm = ch.cross(Vector((0, 0, 1)))
        nrm = nrm.normalized() if nrm.length > 1e-9 else Vector(leeward)
        if nrm.dot(Vector(leeward)) < 0:
            nrm = -nrm
        row = []
        for c in range(cols):
            u = c / (cols - 1)
            belly = 27 / 4 * u * (1 - u) ** 2
            row.append(L + ch * u + nrm * (depth * ch.length * belly))
        grid.append(row)
    return grid


def build_sloop_sailing_extras(coll, variant, prefix, side=-1):
    """The set sails and their sheets, on the side `side` (-1: to port,
    the starboard tack; +1: to starboard, the port tack). Built for each
    side, never mirrored (Check refuses negative scale)."""
    out = []
    g = sl_gooseneck()
    mz = sl_masthead_z()
    port = Vector((side, 0, 0))
    a = SL_BOOM_OUT if side < 0 else -SL_BOOM_OUT
    luff_y = SL_MAST_Y - SL_MAST_HALF[1] + 0.005
    tack = Vector((0, luff_y, g.z + 0.07))
    head = Vector((0, luff_y, mz - 0.45))
    clew = sl_boom_point(SL_BOOM[1] - 0.15, a, 0.10)
    head_aft = head + (Matrix.Rotation(a, 3, "Z") @ Vector((0, -0.14, 0)))
    m = Mesher()
    m.sheet(sail_grid(tack, head, clew, head_aft, 8, 6, 0.09, a * 0.5, port, roach=0.30), SAIL_T)
    out.append(finish(prefix + "mainsail", m, coll, [mat("sail")], variant))
    fs0, fs1 = sl_forestay()
    jtack = fs0.lerp(fs1, 0.035)
    jhead = fs0.lerp(fs1, 0.86)
    jclew = Vector((side * 1.02, 0.58, sl_deck(0.58, 1.02) + 0.78))
    m = Mesher()
    m.sheet(sail_grid(jtack, jhead, jclew, jhead + Vector((0, -0.05, 0)), 8, 5, 0.09,
                      math.radians(-8) if side < 0 else math.radians(8), port), SAIL_T)
    out.append(finish(prefix + "jib", m, coll, [mat("sail")], variant))
    ty, tsole = sl_traveller()
    m = Mesher()
    m.line(sl_boom_point(SL_BOOM[1] - 0.25, a, -0.07), (side * 0.36, ty, tsole + 0.06), 0.04, running=True)
    lead = Vector((side * (sl_half(-0.9) - 0.30), -0.9, sl_deck(-0.9, sl_half(-0.9) - 0.30) + 0.06))
    winch = Vector((side * ((SL_COAMING[0] + SL_COAMING[1]) / 2), -2.30, sl_sheer(-2.30) + SL_COAMING[2] + 0.18))
    m.line(jclew, lead, 0.03, running=True)
    m.line(lead, winch, 0.03, running=True)
    out.append(finish(prefix + "sheets", m, coll, [mat("line")], variant))
    return out


def build_sloop_wheel(coll, variant, prefix):
    """A steering pedestal with its compass and a wheel in the cockpit, in
    place of the tiller (the rudder stock is under the cockpit floor)."""
    yw, R = SL_WHEEL
    sole = sl_sheer(yw) - SL_SOLE
    hz = sole + R + 0.42
    m = Mesher()
    m.tube([(0, yw + 0.14, sole - 0.03), (0, yw + 0.14, hz + 0.06)], [0.075, 0.06], 8, 0)
    m.tube([(0, yw + 0.14, hz + 0.05), (0, yw + 0.14, hz + 0.20)], [0.12, 0.08], 8, 1)
    axis = Vector((0, -1, 0))
    hub = Vector((0, yw, hz))
    m.tube([hub - axis * 0.10, hub + axis * 0.05], [0.045, 0.045], 8, 0)
    m.torus(hub, axis, R, 0.024, 16, 4, 0)
    e1 = Vector((1, 0, 0))
    for k in range(4):
        sp = Matrix.Rotation(math.tau * k / 4 + math.pi / 4, 3, axis) @ e1
        m.obox(hub + sp * (R / 2), sp, axis, sp.cross(axis), R / 2, 0.014, 0.014, 0)
    return {"wheel": finish(prefix + "wheel", m, coll, [mat("metal"), mat("glass")], variant)}


def build_sloop_dodger(coll, variant, prefix):
    """A blue canvas spray dodger over the companionway: an arched shell 3 cm
    thick standing on the coamings aft and on the trunk forward, its sloped
    front and its front panel the windows."""
    rows = ((-2.10, sl_sheer(-2.10) + SL_COAMING[2] - 0.02, (SL_COAMING[0] + SL_COAMING[1]) / 2, 0.74),
            (-1.75, SL_TRUNK_TOP - 0.03, 0.83, 0.63),
            (-1.45, SL_TRUNK_TOP - 0.03, 0.80, 0.45),
            (-1.30, SL_TRUNK_TOP - 0.03, 0.78, 0.29))
    n, t = 10, 0.03
    rings = []
    for y, base, hw, h in rows:
        outer = [(hw * math.cos(math.pi * k / n), y, base + h * math.sin(math.pi * k / n)) for k in range(n + 1)]
        inner = [((hw - t) * math.cos(math.pi * k / n), y, base + (h - t) * math.sin(math.pi * k / n))
                 for k in range(n, -1, -1)]
        rings.append(outer + inner)

    def pick(k, i):
        return 1 if (k == 1 and 2 <= i <= n - 3) else 0       # the sloped front's windows

    m = Mesher()
    m.loft(rings, pick, cap_first=True, cap_last=True, cap_mats=(0, 0))
    # the front panel, its window, closing the arch down to the trunk
    y, base, hw, h = rows[-1]
    m.prism([(hw * math.cos(math.pi * k / n), base + h * math.sin(math.pi * k / n)) for k in range(n + 1)],
            "y", y - 0.02, y + 0.012, 1)
    return {"dodger": finish(prefix + "dodger", m, coll, [mat("cover_blue"), mat("glass")], variant)}


def build_sloop_reverse_parts(coll, variant, prefix):
    """The 1990s stern: the hull with its transom leaning forward at the top,
    a moulded swim step with a teak pad at its foot; the pushpit and the
    backstay come forward with the shorter deck."""
    parts = {}
    parts["hull"] = finish(prefix + "hull", sloop_hull_mesher(reverse=True), coll,
                           [mat(n) for n in SL_HULL_SURFACES], variant)
    parts["rails"] = finish(prefix + "rails", sloop_rails(push_fwd=(1.06, -3.85), push_aft=(0.95, -4.18)), coll,
                            [mat("metal")], variant)
    parts["standing_rigging"] = finish(prefix + "standing_rigging", sloop_standing_rigging(backstay_y=-4.20), coll,
                                       [mat("metal")], variant)
    hw, aft, top, th = SL_SWIM_STEP
    m = Mesher()
    m.box(-hw, hw, aft, -4.48, top - th, top, 0)
    m.box(-hw + 0.08, hw - 0.08, aft + 0.05, aft + 0.25, top - 0.01, top + 0.025, 1)
    parts["swim_step"] = finish(prefix + "swim_step", m, coll, [mat("hull_white"), mat("teak")], variant)
    return parts


# --- linked copies -----------------------------------------------------------------

def linked_copies(src_parts, coll, variant, old_prefix, new_prefix, skip=()):
    out = {}
    for name, src in src_parts.items():
        if name in skip:
            continue
        dup = src.copy()                       # shares its mesh
        dup.name = new_prefix + src.name[len(old_prefix):]
        dup["kyt_variant"] = variant
        coll.objects.link(dup)
        out[name] = dup
    return out


# --- the reference -----------------------------------------------------------------

def figure_bm(height=FIGURE_H, seated=False):
    """A figure for scale: a 12-sided body with a ball head; seated, a
    shorter body over thighs reaching forward (+Y)."""
    m = Mesher()
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    if seated:
        m.prism(ring, "z", 0.0, 0.62)
        m.box(-0.17, 0.17, 0.0, 0.48, 0.0, 0.16)
        m.box(-0.15, 0.15, 0.36, 0.48, -0.40, 0.02)
        hz = 0.62 + 0.20
    else:
        m.prism(ring, "z", 0.0, height - 0.40)
        hz = height - 0.17
    bmesh.ops.create_uvsphere(m.bm, u_segments=12, v_segments=8, radius=0.17,
                              matrix=Matrix.Translation((0, 0, hz)))
    return m


def figure(name, coll, at, mat_=None, seated=False, tag=True):
    m = figure_bm(seated=seated)
    mesh = bpy.data.meshes.new(name)
    m.bm.to_mesh(mesh)
    m.bm.free()
    obj = bpy.data.objects.new(name, mesh)
    mesh.materials.append(mat_ or material("reference_figure", (0.30, 0.22, 0.40, 1.0)))
    if tag:
        obj[TAG] = True
    obj.location = at
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


def waterline(name, coll, hull):
    """The hull cut at z = 0, edges only."""
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                                 plane_co=(0, 0, 0), plane_no=(0, 0, 1))
    keep = {e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)}
    bmesh.ops.delete(bm, geom=bm.faces[:], context="FACES_ONLY")
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if e not in keep], context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context="VERTS")
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    n = len(bm.edges)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj, n


def bounds(objs):
    xs, ys, zs = [], [], []
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            xs.append(p.x)
            ys.append(p.y)
            zs.append(p.z)
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def build_reference(reference, groups):
    lines = []
    for label, hull in (("waterline", groups["troller"]["hull"]), ("waterline_skiff", groups["skiff"]["hull"]),
                        ("waterline_sloop", groups["sloop_moored"]["hull"])):
        obj, n = waterline(label, reference, hull)
        lines.append(f"{label} {n} edges")
    for v in VARIANTS:
        (x0, x1), (y0, y1), _ = bounds(groups[v].values())
        hull = groups[v]["hull"]
        (hx0, hx1), (hy0, hy1), _ = bounds([hull])
        if v in ("troller", "skiff", "sloop_moored"):
            outline(f"outline_{v}_{hy1 - hy0:.1f}x{hx1 - hx0:.1f}".replace(".", "p"), reference, hx0, hx1, hy0, hy1)
        if v == "troller_poles_down":
            outline(f"outline_{v}_span_{x1 - x0:.1f}".replace(".", "p"), reference, x0, x1, hy0, hy1, 0.002)
    fy = -3.2
    figure("figure_1p7m", reference, (0.95, fy, t_deck(fy, 0.95)))
    for name, at in seat_markers():
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.3
        e.location = at
        e[TAG] = True
        reference.objects.link(e)
    # the further variants' own hulls: the double-ender's and the console
    # skiff's waterlines (the reverse transom's is the sloop's), outlines,
    # and the console skiff's four seats
    for label, v in (("waterline_troller_canoe_stern", "troller_canoe_stern"),
                     ("waterline_skiff_console", "skiff_console")):
        obj, n = waterline(label, reference, groups[v]["hull"])
        lines.append(f"{label} {n} edges")
    for v in ("troller_canoe_stern", "skiff_console", "sloop_reverse_transom"):
        (hx0, hx1), (hy0, hy1), _ = bounds([groups[v]["hull"]])
        outline(f"outline_{v}_{hy1 - hy0:.1f}x{hx1 - hx0:.1f}".replace(".", "p"), reference, hx0, hx1, hy0, hy1,
                0.004)
    for name, x, y, z in console_seats():
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.3
        e.location = (x, y, z)
        e[TAG] = True
        reference.objects.link(e)
    return lines


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
    overlapping in area (by their bounds in the plane): the z-fights."""
    faces = []
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        rot = mw.to_3x3()
        for p in o.data.polygons:
            n = (rot @ p.normal).normalized()
            pts = [mw @ o.data.vertices[i].co for i in p.vertices]
            d = n.dot(pts[0])
            a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
            e1 = (a - n * a.dot(n)).normalized()
            e2 = n.cross(e1)
            us = [q.dot(e1) for q in pts]
            vs = [q.dot(e2) for q in pts]
            faces.append((o.name, n, d, min(us), max(us), min(vs), max(vs)))
    found = []
    for i in range(len(faces)):
        oi, ni, di, u0, u1, v0, v1 = faces[i]
        for j in range(i + 1, len(faces)):
            oj, nj, dj, w0, w1, x0, x1 = faces[j]
            if oi == oj:
                continue
            same = (ni - nj).length < 1e-3 and abs(di - dj) < tol
            flipped = (ni + nj).length < 1e-3 and abs(di + dj) < tol
            if not (same or flipped):
                continue
            if flipped:
                x0, x1 = -x1, -x0
            ou = min(u1, w1) - max(u0, w0)
            ov = min(v1, x1) - max(v0, x0)
            if ou > 1e-3 and ov > 1e-3:
                found.append((oi, oj, f"{ou:.3f}x{ov:.3f}"))
    return found


def report(variant, objs):
    bpy.context.view_layer.update()
    objs = [o for o in objs if o.type == "MESH"]
    tris = triangles(objs)
    (x0, x1), (y0, y1), (z0, z1) = bounds(objs)
    hull = next(o for o in objs if o.name.endswith("_hull"))
    (hx0, hx1), (hy0, hy1), (hz0, hz1) = bounds([hull])
    print(f"{PROP}: {variant}: {len(objs)} parts, {tris} triangles; hull {hy1 - hy0:.2f} long x {hx1 - hx0:.2f} "
          f"beam, hull bottom {hz0:.2f}; overall x {x0:.2f}..{x1:.2f} ({x1 - x0:.2f}), y {y0:.2f}..{y1:.2f} "
          f"({y1 - y0:.2f}), z {z0:.2f}..{z1:.2f}: air draft {z1:.2f}, draft {-z0:.2f}")
    pairs = coplanar_pairs(objs)
    print(f"{PROP}: {variant}: {len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs[:30])))
    return tris


# --- renders -----------------------------------------------------------------

def render(folder, groups):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["reference"].hide_render = True
    every = {v: list(groups[v].values()) for v in VARIANTS}

    water_m = material("_water", (0.07, 0.25, 0.40, 1.0))
    bsdf = water_m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Alpha"].default_value = 0.72
    m = Mesher()
    m.face([(-300, -300, 0), (300, -300, 0), (300, 300, 0), (-300, 300, 0)])
    water = finish("_water", m, stage, [water_m], "_")
    m = Mesher()
    m.box(-0.004, 0.004, -40, 40, -0.012, 0.012)
    wl_m = material("_wl", (0.02, 0.10, 0.25, 1.0))
    wl_strip = finish("_wl_strip", m, stage, [wl_m], "_")
    fig_m = material("_figure_stage", (0.55, 0.20, 0.42, 1.0))
    fig = figure("_figure", stage, (0, 0, 0), fig_m, tag=False)
    seated = [figure(f"_angler_{k}", stage, at, fig_m, seated=True, tag=False)
              for k, (_, at) in enumerate(seat_markers())]
    console_seated = [figure(f"_console_angler_{k}", stage, (x, y, z), fig_m, seated=True, tag=False)
                      for k, (_, x, y, z) in enumerate(console_seats())]

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.50, 0.68, 0.88, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.5, -0.65, 0.6)).to_track_quat("Z", "Y").to_euler()
    stage.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    stage.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False

    def show(variants, figure_at=None, anglers=False, water_on=True, strip=False, offsets=None,
             console_anglers=False):
        for v in VARIANTS:
            for o in every[v]:
                o.hide_render = v not in variants
        for v in VARIANTS:
            off = (offsets or {}).get(v)
            for o in every[v]:
                base = o.get("_base")
                if base is None:
                    o["_base"] = list(o.location)
                    base = o["_base"]
                o.location = Vector(base) + (Vector(off) if off else Vector())
        fig.hide_render = figure_at is None
        if figure_at is not None:
            fig.location = figure_at
        for s in seated:
            s.hide_render = not anglers
        for s in console_seated:
            s.hide_render = not console_anglers
        water.hide_render = not water_on
        wl_strip.hide_render = not strip

    def shown_points(only=None):
        """Every vertex the shot shows (or of `only`), the water and the strip aside."""
        pts = []
        for o in (only or list(bpy.data.objects)):
            if o.type != "MESH" or o.hide_render or o in (water, wl_strip):
                continue
            if not (o.users_collection and any(c.name in ("export", "_review") or c.name.startswith("variant_")
                                                 for c in o.users_collection)):
                continue
            mw = o.matrix_world
            pts.extend(mw @ v.co for v in o.data.vertices)
        return pts

    def shoot(name, eye, target, lens=35, size=(1600, 1000), ortho=None, plan=False, fit=True, fit_to=None):
        """A perspective shot backs off along its own line until every shown
        vertex is in frame; an orthographic one is sized to the shown extent
        and centred on it (a plan turned bow to the right)."""
        scene.render.resolution_x, scene.render.resolution_y = size
        aspect = size[0] / size[1]
        bpy.context.view_layer.update()        # moved parts' matrices before measuring them
        cam.data.clip_start = 0.05
        cam.data.clip_end = 3000
        pts = shown_points(fit_to)
        if ortho:
            cam.data.type = "ORTHO"
            xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
            if plan:
                cam.location = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 200.0)
                cam.rotation_euler = (0.0, 0.0, math.pi / 2)
                cam.data.ortho_scale = 1.10 * max(max(ys) - min(ys), (max(xs) - min(xs)) * aspect)
            else:
                cam.location = (200.0, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
                cam.rotation_euler = Vector((-1, 0, 0)).to_track_quat("-Z", "Y").to_euler()
                cam.data.ortho_scale = 1.10 * max(max(ys) - min(ys), (max(zs) - min(zs)) * aspect)
        else:
            cam.data.type = "PERSP"
            cam.data.lens = lens
            eye, target = Vector(eye), Vector(target)
            d = eye - target
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            k = 0.5 if fit else 1.0
            for _ in range(80):
                cam.location = target + d * k
                bpy.context.view_layer.update()
                if not fit or all(0.03 <= c.x <= 0.97 and 0.03 <= c.y <= 0.97 and c.z > 0
                                  for c in (world_to_camera_view(scene, cam, p) for p in pts)):
                    break
                k *= 1.05
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{PROP}: rendered {scene.render.filepath}")

    for v in ORIGINAL:
        (x0, x1), (y0, y1), (z0, z1) = bounds(every[v])
        show([v])
        centre = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) * 0.4))
        reach = max(x1 - x0, y1 - y0, z1 - z0)
        shoot(f"{v}_three_quarter", centre + Vector((1.0, 1.1, 0.55)).normalized() * reach, centre, lens=40)
        show([v], strip=True)
        wl_strip.location = (max(x1, 0.5) + 0.3, 0, 0)
        shoot(f"{v}_side", None, None, ortho=True)
        show([v])
        shoot(f"{v}_plan", None, None, ortho=True, plan=True, size=(1400, 1000))
        hx = bounds([groups[v]["hull"]])[0][1]
        show([v], figure_at=(hx + 1.0, 0.0, 0.0))
        shoot(f"{v}_beside_figure", Vector((hx + 6.0, -4.0, 1.6)), Vector((hx * 0.5, 0.0, 1.0)), lens=35,
              fit_to=[groups[v]["hull"], fig])
    show(["skiff"], anglers=True)
    shoot("skiff_with_anglers", (4.2, 5.0, 3.0), (0, -0.3, 0.5), lens=35, fit=False)
    show(["skiff"], anglers=True)
    shoot("skiff_with_anglers_from_stern", (-2.8, -6.6, 2.4), (0, 0, 0.5), lens=35, fit=False)
    show(["troller", "troller_poles_down", "skiff", "sloop_moored", "sloop_sailing"], figure_at=(-3.2, -15.0, 0),
         offsets={"troller": (-16, 6, 0), "troller_poles_down": (14, 10, 0), "skiff": (-3, -9, 0),
                  "sloop_moored": (-12, -14, 0), "sloop_sailing": (8, -16, 0)})
    shoot("lineup_three_quarter", (34, -52, 22), (0, -3, 4), lens=35, fit=False)
    # the further variants: three-quarter, side elevation, plan
    for v in FURTHER:
        (x0, x1), (y0, y1), (z0, z1) = bounds(every[v])
        show([v])
        centre = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) * 0.4))
        reach = max(x1 - x0, y1 - y0, z1 - z0)
        shoot(f"{v}_three_quarter", centre + Vector((1.0, 1.1, 0.55)).normalized() * reach, centre, lens=40)
        show([v], strip=True)
        wl_strip.location = (max(x1, 0.5) + 0.3, 0, 0)
        shoot(f"{v}_side", None, None, ortho=True)
        show([v])
        shoot(f"{v}_plan", None, None, ortho=True, plan=True, size=(1400, 1000))
    show(["sloop_reverse_transom"])
    shoot("sloop_reverse_transom_stern", (-5.0, -9.0, 2.2), (0, -3.8, 1.0), lens=35, fit=False)
    show(["troller_canoe_stern"])
    shoot("troller_canoe_stern_from_aft", (-7.0, -13.0, 3.6), (0, -3.5, 0.8), lens=35, fit=False)
    show(["sloop_double_lifelines"])
    shoot("sloop_double_lifelines_side_deck", (5.2, -6.0, 2.4), (1.2, -0.5, 1.2), lens=35, fit=False)
    show(["sloop_dodger"])
    shoot("sloop_dodger_cockpit", (-3.6, -7.4, 3.2), (0, -1.8, 1.6), lens=35, fit=False)
    show(["sloop_wheel"])
    shoot("sloop_wheel_cockpit", (-3.0, -7.6, 3.4), (0, -3.2, 1.0), lens=35, fit=False)
    show(["skiff_console"], console_anglers=True)
    shoot("skiff_console_with_anglers", (4.4, 5.2, 3.2), (0, -0.4, 0.6), lens=35, fit=False)
    # every boat: trollers behind, skiffs in the middle, sloops in front
    lay = {"troller": (-26, 22, 0), "troller_canoe_stern": (-18, 22, 0), "troller_mizzen": (-10, 22, 0),
           "troller_red": (-2, 22, 0), "troller_poles_down": (18, 22, 0),
           "skiff": (-4, 4, 0), "skiff_console": (4, 4, 0),
           "sloop_moored": (-27, -14, 0), "sloop_wheel": (-18, -14, 0), "sloop_dodger": (-9, -14, 0),
           "sloop_reverse_transom": (0, -14, 0), "sloop_double_lifelines": (9, -14, 0),
           "sloop_sailing": (18, -14, 0), "sloop_sailing_port_tack": (27, -14, 0)}
    show(list(lay), offsets=lay)
    shoot("lineup_all_three_quarter", Vector((0.55, -1.0, 0.55)) * 60, (0, 2, 3), lens=35)
    show([])


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


def build_further(groups, subs, moored_base):
    """The nine further variants (2026-10-03, Christina: "build all the
    offered variants"), each sharing the unchanged parts of the boat it
    varies as linked meshes; the five above are built first and untouched."""
    t = groups["troller"]

    def add(group, objs, prefix):
        for o in objs:
            group[o.name[len(prefix):]] = o

    v = "troller_canoe_stern"
    g = linked_copies(t, subs[v], v, "troller_", f"{v}_",
                      skip=("hull", "keel", "rudder", "propeller", "pit_coaming", "pit", "gurdies"))
    g.update(build_troller_canoe_parts(subs[v], v, f"{v}_"))
    groups[v] = g
    v = "troller_mizzen"
    g = linked_copies(t, subs[v], v, "troller_", f"{v}_")
    add(g, build_troller_mizzen_extras(subs[v], v, f"{v}_"), f"{v}_")
    groups[v] = g
    v = "troller_red"
    recoloured = ("hull", "pilothouse_glass", "pilothouse_roof")
    g = linked_copies(t, subs[v], v, "troller_", f"{v}_", skip=recoloured)
    g.update(recoloured_copies(t, recoloured, subs[v], v, "troller_", f"{v}_", RED_SET))
    groups[v] = g
    groups["skiff_console"] = build_skiff_console(subs["skiff_console"], groups["skiff"]["rod_1"])
    moored = groups["sloop_moored"]
    for v, skip, extra in (
            ("sloop_wheel", ("tiller",), build_sloop_wheel),
            ("sloop_dodger", (), build_sloop_dodger),
            ("sloop_reverse_transom", ("hull", "rails", "standing_rigging"), build_sloop_reverse_parts),
            ("sloop_double_lifelines", ("rails",),
             lambda c, var, pre: {"rails": finish(pre + "rails", sloop_rails(double=True), c, [mat("metal")], var)})):
        g = linked_copies(moored, subs[v], v, "sloop_moored_", f"{v}_", skip=skip)
        g.update(extra(subs[v], v, f"{v}_"))
        groups[v] = g
    v = "sloop_sailing_port_tack"
    g = linked_copies(moored_base, subs[v], v, "sloop_moored_", f"{v}_")
    g["boom"].rotation_euler = (0, 0, -SL_BOOM_OUT)
    add(g, build_sloop_sailing_extras(subs[v], v, f"{v}_", side=1), f"{v}_")
    groups[v] = g


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

    subs = {}
    for v in VARIANTS[1:]:
        c = bpy.data.collections.new(f"variant_{v}")
        export.children.link(c)
        subs[v] = c
    groups = {}
    groups["troller"] = build_troller(export)
    pd = linked_copies(groups["troller"], subs["troller_poles_down"], "troller_poles_down", "troller_",
                       "troller_poles_down_")
    for side, key in ((1, "pole_starboard"), (-1, "pole_port")):
        pd[key].rotation_euler = (0, pole_down_angle(side), 0)
    for o in build_poles_down_extras(subs["troller_poles_down"], "troller_poles_down", "troller_poles_down_"):
        pd[o.name[len("troller_poles_down_"):]] = o
    groups["troller_poles_down"] = pd
    groups["skiff"] = build_skiff(subs["skiff"])
    moored = build_sloop(subs["sloop_moored"])
    moored_base = dict(moored)
    sailing = linked_copies(moored, subs["sloop_sailing"], "sloop_sailing", "sloop_moored_", "sloop_sailing_")
    sailing["boom"].rotation_euler = (0, 0, SL_BOOM_OUT)
    for o in build_sloop_moored_extras(subs["sloop_moored"], moored, "sloop_moored", "sloop_moored_"):
        moored[o.name[len("sloop_moored_"):]] = o
    for o in build_sloop_sailing_extras(subs["sloop_sailing"], "sloop_sailing", "sloop_sailing_"):
        sailing[o.name[len("sloop_sailing_"):]] = o
    groups["sloop_moored"] = moored
    groups["sloop_sailing"] = sailing
    build_further(groups, subs, moored_base)
    bpy.context.view_layer.update()
    lines = build_reference(reference, groups)
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    print(f"{PROP}: reference: " + ", ".join(lines))
    for v in VARIANTS:
        report(v, list(groups[v].values()))
    sk_hull = bounds([groups["skiff"]["hull"]])[2][0]
    print(f"{PROP}: skiff hull draft {-sk_hull:.2f} (outboard skeg below it)")
    print(f"{PROP}: sloop masthead {sl_masthead_z():.2f} over the water, {SL_MAST_H:.1f} over the deck at the mast")
    print(f"{PROP}: troller poles stowed lean {math.degrees(abs(pole_stowed_angle(1))):.1f} deg, down "
          f"{math.degrees(T_POLE_DOWN):.0f} deg above horizontal; tips at "
          f"{pole_point(1, pole_down_angle(1), 1.0).x:.2f} m out")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], groups)


main()
