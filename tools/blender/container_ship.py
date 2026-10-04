"""The container port's ships, blocked out (2026-10-03): Christina's "we need
to add boats to our props" and "lets add a modern port near the city", the
port ships for the new container terminal on the mainland shore facing the
city across the water, by the bridge's east end.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/container_ship.blend --python tools/blender/container_ship.py -- \
        [--replace] [--save] [--render <folder> [--only <variant,...>] [--views <view,...>] [--lineup]]

Builds, from scratch every run, eight `kyt_variant`s, each standing at the
origin, so Send writes each as a prop of its own (`container_ship_<variant>`):

- **panamax** (in `export` itself): a late-1990s Panamax boxship of about
  4,400 TEU, 294 x 32.25 m on a 12 m draft, its deckhouse aft over the engine
  room with the funnel against its back and one 40 ft bay aft of the funnel,
  sixteen 40 ft bays forward of the house, 13 across on deck where the deck
  is full width (12 on the flared bow, 10 on the first bay), stacked 3 high
  at the bow rising to 6, open bridge wings to the ship's side, a raised
  forecastle with a V breakwater, a raked stem over a bulbous bow, a
  transom stern, rudder and propeller. Black hull, red-brown bottom, cream
  house, buff funnel with a black top.
- **post_panamax** (in `export/variant_post_panamax`, eye shut): the 1996
  Regina Maersk class ("K-class", Odense), 318.2 x 42.8 m on its 12.2 m
  design draft, 17 across on deck, thirteen 40 ft bays forward of the
  deckhouse and six aft of it (read), so the house stands about two thirds
  aft; a closed bridge spanning the full breadth and lashing bridges between
  the bays (read). The funnel stands against the back of the house, over the
  engine room; I could not confirm that from a source (see the card).
  Navy hull, white house, white funnel with a navy top.
- **panamax_light** (in `export/variant_panamax_light`, eye shut): the
  Panamax half-empty, arriving or leaving: every part of the panamax but its
  deck cargo is a linked copy (one mesh, so reshaping one reshapes both),
  raised 2.4 m to a 9.6 m mean draft and trimmed 1.8 m by the stern, with a
  partial deck load of its own: empty bays, low stacks, part rows.

The further five (2026-10-03, Christina: "build all the offered variants"),
each in `export/variant_<name>` with its eye shut. Each is built whole and
then every part that is a shifted copy of one already made takes that mesh,
linked (`link_identical`), so only what differs is new; the first three are
built exactly as before:

- **post_panamax_split**: the K-class with its funnel standing on its own
  over an engine room aft, four bays behind the house, then the funnel, then
  two bays; the house where it was.
- **panamax_three_quarter_house**: the Panamax with fourteen bays before the
  house and three behind the funnel, the house front 71% of the length aft
  of the stem head.
- **post_panamax_light**: the K-class half-empty, made as panamax_light:
  linked copies raised 2.6 m and trimmed 2.0 m by the stern, its own load.
- **panamax_lashing**: the Panamax with lashing bridges, 0.5 m deep to fit
  its 1 m gaps between the hatch covers' ends.
- **panamax_wing_cabs**: the Panamax with a closed cab on each bridge wing,
  its window band set proud. The lashing bridges and the cabs are separate
  variants because each is one change against the panamax.

Everything the tool makes carries `kyt_container_ship`, so a rerun removes
and rebuilds its own work and keeps anything of hers; `export` holding
anything untagged refuses without `--replace`. Into the locked `reference`
collection go each variant's waterline (the hull cut at z = 0), its length
by beam outline, the bridge's sightline over the cargo to the sea 500 m
ahead of the bow, and a 1.7 m figure on the Panamax's foredeck.

**Frame** (the boats brief): real metres, Z up, z = 0 the waterline, the
origin on the centreline, midships (half the length overall), at the
waterline. The bow is +Y (the glTF export turns Blender +Y into Godot -Z,
Godot's forward, as `ride_vehicle.gd` turns its trains); starboard is +X.

**Contract** (scenery block-out): closed shells, silhouette first, no
interiors; the wheelhouse windows are a dark band set 3 cm proud all round,
not holes. Every part has `kyt_collision = none` this pass. No two shapes
share a plane: a part that meets another laps 2 cm into it or stands proud.
Era late 1990s; no names, logos, flags or lettering; colour is stand-in
materials by surface, `container_ship_<surface>` (the post-Panamax's own
hull, house and funnel `container_ship_post_panamax_<surface>`), the boxes
`container_ship_box_<colour>` in the container kit's colour set and hexes.

**How it is built.** The hull is one closed loft of horizontal waterlines
(`Hull`): each level a half-breadth curve from the stern profile to the stem
profile, a flat-bottomed bilge-rounded midship section, an entrance and a
run whose fullness grows with height (the bow flare and the wide transom),
an elliptic bulb laid over the entrance below the water, the raised
forecastle lofted on from the main deck's forward stations, the transom as
the strip of stern ends above its foot. A level at `BOOT_TOP` splits the red
bottom from the hull colour. Each 40 ft bay's deck cargo is one closed block
(`stack_bm`): its outer faces cut at the boxes' edges, each box face its own
colour, so the boxes read by colour; where a face looks into the narrow gap
against a neighbouring bay only its outer columns and the tiers that can be
seen past the neighbour keep their cells, and the rest is one face. The
hatch covers and the lashing bridges are linked meshes. The builder checks
the bridge's view over the cargo against SOLAS (printed every run).
"""

import math
import os
import random
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

TAG = "kyt_container_ship"
PROP = "container_ship"
VARIANTS = ("panamax", "post_panamax", "panamax_light", "post_panamax_split", "panamax_three_quarter_house",
            "post_panamax_light", "panamax_lashing", "panamax_wing_cabs")

# --- ISO 668 boxes (read; the port's shared numbers) ---------------------------
BOX_W = 2.438              # outside width, read
BOX_40 = 12.192            # 40 ft outside length, read
BOX_H = 2.591              # 8 ft 6 in, read
BOX_HC = 2.896             # 9 ft 6 in high-cube, read
ROW_GAP = 0.025            # between rows on deck, chosen (cell guides allow 25-38 mm)
LAP = 0.02                 # a part that meets another laps 2 cm into it (the project's rule)

# --- the bridge's view (read: SOLAS V/22.1.1, the sea surface may be hidden
# for no more than two ship lengths or 500 m ahead of the bow, the lesser) ----
BLIND_LIMIT = 500.0
EYE_OVER_FLOOR = 1.7       # the conning eye over the wheelhouse floor, chosen

# --- hull form, both ships (chosen: a single-screw boxship's lines, read off
# typical 1990s profiles; fractions of the draft T or the length LBP) -------
BOOT_TOP = 0.5             # the red bottom paint's top over the loaded waterline, chosen
STEM_NECK_Z = -0.20        # x T: where the raked stem meets the bulb's top
STEM_NECK_BACK = 0.6       # m: the neck aft of the forward perpendicular (FP)
STEM_CURVE = 1.25          # the stem's rake curves forward toward the forecastle deck
FOREFOOT = 0.033           # x LBP: the keel's fore end aft of the neck
FOREFOOT_CURVE = 1.6
BULB_Z = -0.54             # x T: the bulb's axis
BULB_RH = 0.33             # x T: its half height
BULB_RW = 0.085            # x B: its half breadth
BULB_NOSE = 0.016          # x LBP: its nose forward of the FP
BULB_ROUND = 0.022         # x LBP: the length its nose rounds over
BULB_TAIL = 0.08           # x LBP: how far aft of the rounding it is drawn (inside the hull by then)
# the stern profile on the centreline, (height x T, y from the aft
# perpendicular x LBP), keel to the transom's foot; the deck edge ends at -LOA/2
STERN = ((-1.00, 0.035), (-0.25, 0.028), (-0.20, 0.014), (-0.10, -0.002), (0.00, -0.010), (0.10, -0.015))
TRANSOM_FOOT = 0.10        # x T: the transom's lower edge over the waterline
TRANSOM_W = (0.50, 0.85)   # the transom's half breadth at its foot and at the deck, x B/2
# where the full breadth ends forward and aft (y x LBP) and how full the ends
# are (the exponent), at the keel, the waterline, the main deck and the
# forecastle deck: fuller higher up is the bow flare and the wide transom
ENTRANCE = (0.07, 0.16, 0.30, 0.33)
ENTRANCE_P = (1.6, 2.0, 3.5, 4.0)
RUN = (-0.10, -0.15, -0.34)
RUN_Q = (1.6, 1.9, 2.4)
N_RUN, N_ENT = 7, 14       # stations per waterline: the run, the entrance
# rudder and propeller (chosen)
RUDDER_FWD = 0.011         # x LBP: the rudder's leading edge forward of the AP
RUDDER_AFT = 0.009         # x LBP: its trailing edge aft of the AP
RUDDER_T = 1.0             # its greatest thickness
RUDDER_FOOT = 0.10         # x T: its foot over the keel
RUDDER_TOP = 0.5           # its top, ending inside the counter
PROP_R = 0.33              # x T: the propeller's radius
PROP_CLEAR = 0.05          # x T: its tips over the keel line
PROP_Y = 0.022             # x LBP: its disc forward of the AP
PROP_BLADES = 4

# --- deck fittings, both ships (chosen, typical) --------------------------------
COAMING_H = 1.6            # hatch coaming over the deck
COVER_Z0 = 1.55            # the hatch cover's underside, 5 cm down over the coaming
COVER_TOP = 2.4            # the cover's top over the deck: the deck cargo stands on it
COVER_OVER_END = 0.2       # the cover runs past the stack's ends
COAMING_OVER_END = 0.1
COVER_SIDE_PROUD = 0.02    # the cover stands 2 cm proud of the stack's sides
COAMING_INSET = 1.2        # the coaming inside the cover each side (the cover overhangs the side passage)
DECK_MARGIN = 0.1          # least room from the outer row to the deck edge
FIRST_BAY_CLEAR = 1.1      # the forecastle break to the first bay's fore end
HOUSE_GAP = 2.0            # bay ends to the house front and from the funnel's back
FUNNEL_LAP = 0.3           # the funnel's front inside the house's back wall
LASHING_D = 0.8            # a lashing bridge's depth fore and aft
MOORING_MIN = 5.0          # least aft mooring deck behind the last bay
BREAKWATER_AFT = 1.0       # the breakwater's back over the forecastle break
BREAKWATER_APEX = 3.0      # its V's depth
BREAKWATER_T = 0.3
FOREMAST_BACK = 9.0        # the foremast aft of the stem head
WINDOW_PROUD = 0.03        # the wheelhouse's window band stands proud all round
WINDOW_Z = (1.0, 2.3)      # its band over the wheelhouse floor
WING_D = 3.3               # an open bridge wing's depth fore and aft
WING_Z = (-0.6, 1.2)       # its deck slab and bulwark about the bridge floor
LIFEBOAT = (8.5, 3.0, 3.0)  # length, breadth, height of a davit lifeboat
LIFEBOAT_OUT = 0.4         # its side off the house wall
LIFEBOAT_TIER = 3          # the house tier it hangs at

# --- Panamax, late 1990s, deckhouse aft --------------------------------------
PX_LOA = 294.0             # read: the canal's limit for container ships, 294.13 m (965 ft)
PX_LBP = 281.6             # chosen, typical of 4,000-4,400 TEU Panamax boxships
PX_B = 32.25               # read: the locks' 32.31 m (106 ft); 13 rows on deck need 31.99 m
PX_D = 21.4                # moulded depth, chosen (typical)
PX_T = 12.0                # read: 12.04 m (39.5 ft) tropical fresh water, the canal's limit
PX_BOW_OVER = 6.4          # the stem head forward of the FP, chosen (LOA - LBP = 12.4 m)
PX_FC_LEN = 22.0           # the forecastle, stem head to its break, chosen
PX_FC_H = 3.0              # the forecastle deck over the main deck, chosen
PX_BILGE_R = 2.2           # chosen
PX_ROWS = 13               # across on deck, read (the brief and the beam)
PX_BAY_GAP = 1.0           # between 40 ft bays: no lashing bridges, chosen
# deck cargo, fore to aft: (tiers, "std" 8'6" or "hc" 9'6", 20 ft pairs?);
# low at the bow so the bridge sees over (checked each run), chosen
PX_FORE_BAYS = ((3, "std", True), (4, "std", False), (5, "std", False), (5, "hc", False),
                (6, "std", False), (6, "std", True), (6, "std", False), (5, "hc", False),
                (6, "std", False), (6, "std", False), (6, "std", True), (6, "std", False),
                (5, "hc", False), (6, "std", False), (6, "std", False), (6, "std", False))
PX_AFT_BAYS = ((5, "std", False),)
PX_HOUSE_L = 16.0          # the deckhouse fore and aft, chosen
PX_HOUSE_W = 25.0          # its breadth, chosen (side passages outboard)
PX_HOUSE_TIERS = 9         # decks from the main deck to the bridge deck, chosen for the view
PX_TIER = 2.8              # deck height in the house, chosen
PX_WH_L, PX_WH_W, PX_WH_H = 9.0, 26.0, 3.2   # the wheelhouse, chosen
PX_WH_OVER = 0.6           # the wheelhouse's front over the house front, chosen
PX_WINGS = True            # open bridge wings out to the ship's side, chosen
PX_FUNNEL = (10.0, 8.0)    # length, breadth at its foot, chosen
PX_FUNNEL_TOP = 42.5       # over the waterline: 4.7 m over the wheelhouse roof, chosen
PX_FUNNEL_RAKE = 1.5       # its top aft of its foot, chosen
PX_FUNNEL_CAP = 2.5        # the black top band, chosen
PX_MAST_H = 9.0            # the radar mast over the wheelhouse roof, chosen
PX_FOREMAST_H = 8.0        # over the forecastle deck, chosen
PX_BREAKWATER_H = 4.0      # over the forecastle deck, chosen

# --- Post-Panamax: the 1996 Regina Maersk class --------------------------------
PP_LOA = 318.2             # read (Maritime Reporter, Dec 1996: 318.2 m o.a.)
PP_LBP = 302.2             # read (the same: 302.2 m b.p.)
PP_B = 42.8                # read
PP_D = 24.1                # read
PP_T = 12.2                # read: design draft (14.5 m scantling)
PP_BOW_OVER = 7.5          # chosen (LOA - LBP = 16 m: 7.5 forward, 8.5 aft)
PP_FC_LEN = 22.0           # chosen
PP_FC_H = 3.0              # chosen
PP_BILGE_R = 2.6           # chosen
PP_ROWS = 17               # read: 17 across
PP_BAY_GAP = 1.4           # chosen: room for the lashing bridges (read: it has them)
PP_FORE_BAYS = ((4, "std", True), (5, "std", False), (5, "hc", False), (6, "std", False),
                (6, "std", False), (6, "std", True), (6, "std", False), (5, "hc", False),
                (6, "std", False), (6, "std", False), (6, "std", True), (6, "std", False),
                (6, "std", False))   # read: thirteen bays forward of the deckhouse
PP_AFT_BAYS = ((6, "std", False), (6, "std", False), (5, "hc", False), (6, "std", True),
               (5, "std", False), (4, "std", False))   # read: six aft of it
PP_HOUSE_L = 14.0          # chosen
PP_HOUSE_W = 30.0          # chosen
PP_HOUSE_TIERS = 9         # chosen for the view (8 left the sea hidden 560 m ahead)
PP_TIER = 2.85             # chosen
PP_WH_L, PP_WH_W, PP_WH_H = 7.0, PP_B - 0.1, 3.2   # read: a closed bridge over the full breadth
PP_WH_OVER = 0.6           # chosen
PP_WINGS = False           # the wheelhouse is the wings
PP_FUNNEL = (10.0, 10.0)   # chosen
PP_FUNNEL_TOP = 46.5       # chosen: 5.8 m over the wheelhouse roof
PP_FUNNEL_RAKE = 1.5
PP_FUNNEL_CAP = 2.5
PP_MAST_H = 9.0
PP_FOREMAST_H = 8.0
PP_BREAKWATER_H = 4.5

# --- the Panamax half-empty (chosen) ------------------------------------------
LIGHT_RISE = 2.4           # out of the water at midships: a 9.6 m mean draft
LIGHT_TRIM = 1.8           # by the stern over the length between perpendiculars
# its deck cargo, the panamax's bays fore to aft: None for an empty bay, or
# (tiers, height, 20 ft pairs?, rows (first, last) or None for all)
PX_LIGHT_BAYS = (None, (1, "std", True, None), (2, "std", False, (2, 10)), None,
                 (2, "hc", False, None), (3, "std", False, (0, 7)), (1, "std", True, (3, 13)), None,
                 (2, "std", False, None), (3, "std", False, None), None, (2, "std", True, (4, 13)),
                 (1, "hc", False, None), None, (2, "std", False, (0, 9)), (3, "std", False, None),
                 (2, "std", False, None))

# --- the further variants (2026-10-03, Christina: "build all the offered
# variants"); each shares every part it has unchanged as a linked mesh -------
# post_panamax_split: the K-class with its funnel standing on its own over an
# engine room aft: four bays behind the house, the funnel, two behind it
# (chosen: the split arrangement later post-Panamax ships took)
PP_SPLIT_AFT = PP_AFT_BAYS[:4] + ("funnel",) + PP_AFT_BAYS[4:]
# panamax_three_quarter_house: the Panamax's house about three quarters aft,
# fourteen bays before it and three behind the funnel (chosen)
PX_TQ_FORE = PX_FORE_BAYS[:14]
PX_TQ_AFT = PX_FORE_BAYS[14:] + PX_AFT_BAYS
# panamax_lashing: lashing bridges between the bays, as deep as the Panamax's
# 1 m gap allows between the hatch covers' ends (chosen)
PX_LASHING_D = 0.5
# panamax_wing_cabs: the open wings closed in by a cab on each (chosen)
WING_CAB_Z = (-0.3, 2.9)          # the cab about the bridge floor, under the wheelhouse roof
WING_CAB_WINDOWS = (1.05, 2.25)   # its window band, off the wheelhouse's band
WING_CAB_PROUD = 0.02             # the cab past the wing's tip and its front and back
# post_panamax_light: the K-class half-empty, made as panamax_light (chosen)
PP_LIGHT_RISE = 2.6        # a 9.6 m mean draft
PP_LIGHT_TRIM = 2.0        # by the stern
PP_LIGHT_BAYS = (None, (1, "std", True, None), (2, "std", False, (3, 14)), None, (3, "std", False, None),
                 (2, "hc", False, (0, 9)), None, (2, "std", False, None), (1, "std", True, (5, 17)),
                 (3, "std", False, (2, 15)), None, (2, "std", False, None), (1, "hc", False, None),
                 (2, "std", False, None), None, (3, "std", False, (0, 10)), (2, "std", True, None), None,
                 (1, "std", False, None))


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


# the container kit's colour set and hexes (`tools/blender/container_kit.py`),
# with how often each turns up on deck (chosen)
BOX_COLOURS = (("rust_red", "9e3b26", 17), ("sky_blue", "5ea3d0", 9), ("dark_blue", "1f3a6b", 12),
               ("green", "2f6e3e", 9), ("grey", "8a8d8f", 13), ("white", "e6e4dc", 9),
               ("orange", "d9682a", 7), ("yellow", "e3b52a", 5), ("brown", "6b4a2e", 19))
COLOUR_NAMES = tuple(c for c, _, _ in BOX_COLOURS)
COLOUR_WEIGHTS = tuple(w for _, _, w in BOX_COLOURS)
SAME_AS_BELOW, SAME_AS_BESIDE = 0.18, 0.22   # a box takes its neighbour's colour (consignments), chosen

COLOURS = {f"{PROP}_box_{c}": srgb(h) for c, h, _ in BOX_COLOURS}
COLOURS.update({
    f"{PROP}_hull": srgb("1b1c20"),          # black topsides
    f"{PROP}_bottom": srgb("7b2d22"),        # red-brown bottom and boot-top
    f"{PROP}_deck": srgb("59614f"),          # decks, the forecastle
    f"{PROP}_hatch": srgb("6d706b"),         # coamings and hatch covers
    f"{PROP}_house": srgb("eee8d6"),         # cream deckhouse
    f"{PROP}_glass": srgb("1d2a33"),         # the wheelhouse windows, a dark band
    f"{PROP}_funnel": srgb("c7b085"),        # buff
    f"{PROP}_funnel_top": srgb("18181a"),    # black top
    f"{PROP}_mast": srgb("ece9df"),          # masts, the breakwater
    f"{PROP}_lifeboat": srgb("e2632a"),
    f"{PROP}_propeller": srgb("a9844f"),     # bronze
    f"{PROP}_lashing": srgb("9a9c95"),       # lashing bridges
    f"{PROP}_post_panamax_hull": srgb("1d2b4a"),       # navy topsides
    f"{PROP}_post_panamax_house": srgb("f3f3ef"),      # white
    f"{PROP}_post_panamax_funnel": srgb("eceae4"),     # white
    f"{PROP}_post_panamax_funnel_top": srgb("1d2b4a"),  # a navy top
})
SURFACES = ("hull", "bottom", "deck", "hatch", "house", "glass", "funnel", "funnel_top", "mast",
            "lifeboat", "propeller", "lashing")
OWN = ("hull", "house", "funnel", "funnel_top")   # what the post-Panamax colours its own way


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


def mats(tag=""):
    """The stand-in materials by surface; `tag` gives a ship its own hull,
    house and funnel colours."""
    return {k: material(f"{PROP}_{tag}{k}" if (tag and k in OWN) else f"{PROP}_{k}") for k in SURFACES}


def box_mat(colour):
    return material(f"{PROP}_box_{colour}")


# --- building blocks -------------------------------------------------------------

def finish(name, bm, coll, mat_list, variant):
    """A bmesh into an object in `coll`, tagged, with its material slots and
    no collision (this pass)."""
    mesh = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    for m in mat_list:
        mesh.materials.append(m)
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    obj["kyt_variant"] = variant
    obj["kyt_collision"] = "none"
    coll.objects.link(obj)
    return obj


def prism_into(bm, poly, axis, lo, hi):
    """A 2D polygon extruded along `axis` into `bm` ('x' takes (y, z) pairs,
    'y' (x, z), 'z' (x, y)); returns its vertices."""
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
    return near + far


def box_into(bm, x0, x1, y0, y1, z0, z1):
    assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
    return prism_into(bm, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def box(name, coll, mat, variant, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    box_into(bm, x0, x1, y0, y1, z0, z1)
    return finish(name, bm, coll, [mat], variant)


def octagon(cx, cy, wx, wy, c):
    """An elongated octagon in plan: a rectangle with its corners cut by `c`."""
    return [(cx + wx, cy - wy + c), (cx + wx, cy + wy - c), (cx + wx - c, cy + wy), (cx - wx + c, cy + wy),
            (cx - wx, cy + wy - c), (cx - wx, cy - wy + c), (cx - wx + c, cy - wy), (cx + wx - c, cy - wy)]


def lerp_pts(pts, z):
    """Piecewise linear through (z, value) points, held flat past either end."""
    if z <= pts[0][0]:
        return pts[0][1]
    for (z0, v0), (z1, v1) in zip(pts, pts[1:]):
        if z <= z1:
            return v0 + (v1 - v0) * (z - z0) / (z1 - z0)
    return pts[-1][1]


# --- the hull -----------------------------------------------------------------------

class Hull:
    """One ship's hull form: half-breadth as a function of (y, z), the stem
    and stern profiles, and the loft that builds it."""

    def __init__(self, loa, lbp, b, d, t, bow_over, fc_len, fc_h, bilge_r):
        self.loa, self.lbp, self.b, self.d, self.t = loa, lbp, b, d, t
        self.fc_h, self.bilge_r = fc_h, bilge_r
        self.fp = loa / 2 - bow_over
        self.ap = self.fp - lbp
        self.zk = -t
        self.zd = d - t                       # the main deck at the side (freeboard)
        self.zfc = self.zd + fc_h             # the forecastle deck
        self.y_fc = loa / 2 - fc_len          # the forecastle break
        self.z_neck = STEM_NECK_Z * t
        self.y_neck = self.fp - STEM_NECK_BACK
        self.z_tr = TRANSOM_FOOT * t
        self.zb, self.rh, self.rw = BULB_Z * t, BULB_RH * t, BULB_RW * b
        self.yn = self.fp + BULB_NOSE * lbp
        self.ln = BULB_ROUND * lbp
        self.y0 = self.yn - self.ln
        self.stern = [(zt * t, self.ap + yl * lbp) for zt, yl in STERN] + [(self.zd, -loa / 2)]
        hz = (self.zk, 0.0, self.zd, self.zfc)
        self.pf = [(z, f * lbp) for z, f in zip(hz, ENTRANCE)]
        self.pp = list(zip(hz, ENTRANCE_P))
        self.pa = [(z, f * lbp) for z, f in zip(hz, RUN)]
        self.qq = list(zip(hz, RUN_Q))

    def hb_mid(self, z):
        r = self.bilge_r
        zk = max(0.0, z - self.zk)
        if zk >= r:
            return self.b / 2
        return self.b / 2 - r + math.sqrt(max(0.0, r * r - (r - zk) ** 2))

    def ys_main(self, z):
        """The stem without the bulb: raked above the neck, the forefoot below."""
        if z >= self.z_neck:
            u = min(1.0, (z - self.z_neck) / (self.zfc - self.z_neck))
            return self.y_neck + (self.loa / 2 - self.y_neck) * u ** STEM_CURVE
        u = (self.z_neck - z) / (self.z_neck - self.zk)
        return self.y_neck - FOREFOOT * self.lbp * u ** FOREFOOT_CURVE

    def bulb_extent(self, z):
        dz = abs(z - self.zb)
        if dz >= self.rh:
            return None
        return self.y0 + self.ln * math.sqrt(1 - (dz / self.rh) ** 2)

    def y_fwd(self, z):
        e, m = self.bulb_extent(z), self.ys_main(z)
        return m if e is None else max(m, e)

    def y_aft(self, z):
        return lerp_pts(self.stern, z)

    def transom(self, z):
        if z < self.z_tr - 1e-6:
            return 0.0
        return lerp_pts([(self.z_tr, TRANSOM_W[0]), (self.zd, TRANSOM_W[1])], z)

    def bulb_hb(self, y, z):
        if y > self.yn or y < self.y0 - BULB_TAIL * self.lbp:
            return 0.0
        g = 1.0 if y <= self.y0 else math.sqrt(max(0.0, 1 - ((y - self.y0) / self.ln) ** 2))
        c, dz = self.rh * g, z - self.zb
        if c <= 1e-9 or abs(dz) >= c:
            return 0.0
        return self.rw * g * math.sqrt(1 - (dz / c) ** 2)

    def hb(self, y, z):
        mid = self.hb_mid(z)
        ypf, ypa = lerp_pts(self.pf, z), lerp_pts(self.pa, z)
        if y > ypf:
            s = (y - ypf) / (self.ys_main(z) - ypf)
            f = 0.0 if s >= 1 else 1 - s ** lerp_pts(self.pp, z)
        elif y < ypa:
            s = min(1.0, (ypa - y) / (ypa - self.y_aft(z)))
            tw = self.transom(z)
            f = tw + (1 - tw) * (1 - s ** lerp_pts(self.qq, z))
        else:
            f = 1.0
        return max(mid * f, self.bulb_hb(y, z))

    def levels(self):
        """The waterlines the loft is built on: the bilge, through the bulb,
        the neck, the paint line, the transom's foot, the main deck."""
        r = self.bilge_r
        key = [self.zk, self.z_neck, BOOT_TOP, self.z_tr, self.zd]
        more = [self.zk + 0.134 * r, self.zk + 0.5 * r, self.zk + r,
                self.zb - 0.85 * self.rh, self.zb - 0.5 * self.rh, self.zb, self.zb + 0.5 * self.rh,
                self.zb + 0.85 * self.rh, -0.1 * self.t, 0.5 * (self.z_tr + self.zd)]
        zs = sorted(key)
        for z in sorted(more):
            if all(abs(z - k) > 0.3 for k in zs):
                zs.append(z)
                zs.sort()
        return zs

    def stations(self, z):
        """The y stations of one waterline, stern to stem: the run (closer
        at both ends), the parallel body's two ends, the entrance (closing
        up toward the stem, for the bulb's nose)."""
        ya, ypa, ypf, yf = self.y_aft(z), lerp_pts(self.pa, z), lerp_pts(self.pf, z), self.y_fwd(z)
        ys = [ya + (ypa - ya) * (0.5 - 0.5 * math.cos(math.pi * j / N_RUN)) for j in range(N_RUN)]
        ys.append(ypa)
        ys += [ypf + (yf - ypf) * math.sin(0.5 * math.pi * j / N_ENT) for j in range(N_ENT + 1)]
        return ys

    def build(self, name, coll, m, variant):
        bm = bmesh.new()
        rings = []

        def ring(z, ys):
            hbs = [self.hb(y, z) for y in ys]
            hbs[-1] = 0.0                     # the stem
            s = [bm.verts.new((h, y, z)) for h, y in zip(hbs, ys)]
            p = [bm.verts.new((-h, y, z)) for h, y in zip(hbs, ys)]
            return (z, ys, s, p)

        def band(a, b):
            _, _, sa, pa = a
            _, _, sb, pb = b
            for i in range(len(sa) - 1):
                bm.faces.new((sa[i], sa[i + 1], sb[i + 1], sb[i]))
                bm.faces.new((pa[i + 1], pa[i], pb[i], pb[i + 1]))
            if sa[0].co.x > 1e-6 or sb[0].co.x > 1e-6:     # the transom, or the counter under it
                bm.faces.new((sa[0], pa[0], pb[0], sb[0]))

        i_fc = None
        for z in self.levels():
            ys = self.stations(z)
            if abs(z - self.zd) < 1e-9:
                ent = list(range(N_RUN + 2, len(ys) - 1))
                i_fc = min(ent, key=lambda i: abs(ys[i] - self.y_fc))
                ys[i_fc] = self.y_fc
            rings.append(ring(z, ys))
        for a, b in zip(rings, rings[1:]):
            band(a, b)
        _, _, s0, p0 = rings[0]
        bm.faces.new(s0 + list(reversed(p0)))                       # the flat bottom
        zd, ysd, sd, pd = rings[-1]
        bm.faces.new(sd[:i_fc + 1] + list(reversed(pd[:i_fc + 1])))  # the main deck
        # the forecastle, lofted on from the main deck's forward stations
        base = ysd[i_fc:]
        yfd = ysd[-1]
        fc = [(zd, base, sd[i_fc:], pd[i_fc:])]
        for z in (zd + 0.5 * self.fc_h, self.zfc):
            yf = self.y_fwd(z)
            fc.append(ring(z, [self.y_fc + (y - self.y_fc) * (yf - self.y_fc) / (yfd - self.y_fc) for y in base]))
        for a, b in zip(fc, fc[1:]):
            band(a, b)                        # its end caps are the forecastle's aft bulkhead
        bm.faces.new(fc[2][2] + list(reversed(fc[2][3])))          # the forecastle deck

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            c = f.calc_center_median()
            if f.normal.z > 0.9 and c.z > self.zd - 0.05:
                f.material_index = 2
            elif c.z < BOOT_TOP:
                f.material_index = 1
            else:
                f.material_index = 0
        return finish(name, bm, coll, [m["hull"], m["bottom"], m["deck"]], variant)

    def build_rudder(self, name, coll, m, variant):
        y_le, y_te = self.ap + RUDDER_FWD * self.lbp, self.ap - RUDDER_AFT * self.lbp
        c = y_le - y_te
        h = RUDDER_T / 2
        poly = [(0.0, y_le), (h, y_le - 0.3 * c), (0.6 * h, y_te + 0.25 * c), (0.0, y_te),
                (-0.6 * h, y_te + 0.25 * c), (-h, y_le - 0.3 * c)]
        bm = bmesh.new()
        prism_into(bm, poly, "z", self.zk + RUDDER_FOOT * self.t, RUDDER_TOP)
        return finish(name, bm, coll, [m["bottom"]], variant)

    def build_propeller(self, name, coll, m, variant):
        r = PROP_R * self.t
        zc = self.zk + PROP_CLEAR * self.t + r
        yc = self.ap + PROP_Y * self.lbp
        y_post = self.y_aft(zc)
        bm = bmesh.new()
        hub = [(0.9 * math.cos(math.tau * i / 6), zc + 0.9 * math.sin(math.tau * i / 6)) for i in range(6)]
        prism_into(bm, hub, "y", yc - 0.9, y_post + 0.3)
        for k in range(PROP_BLADES):
            vs = box_into(bm, -0.9, 0.9, yc - 0.12, yc + 0.12, zc + 0.6, zc + r)
            bmesh.ops.rotate(bm, verts=vs, cent=(0.0, yc, zc),
                             matrix=Matrix.Rotation(math.pi / 4 + k * math.tau / PROP_BLADES, 3, "Y"))
        return finish(name, bm, coll, [m["propeller"]], variant)


# --- the deck cargo ------------------------------------------------------------------

def box_colours(rng, rows, tiers, segs):
    """Each box's colour, [row][tier][seg], in clumps as consignments are."""
    col = [[[None] * segs for _ in range(tiers)] for _ in range(rows)]
    for t in range(tiers):
        for i in range(rows):
            for j in range(segs):
                r = rng.random()
                if t > 0 and r < SAME_AS_BELOW:
                    col[i][t][j] = col[i][t - 1][j]
                elif i > 0 and r < SAME_AS_BELOW + SAME_AS_BESIDE:
                    col[i][t][j] = col[i - 1][t][j]
                else:
                    col[i][t][j] = rng.choices(COLOUR_NAMES, COLOUR_WEIGHTS)[0]
    return col


def stack_bm(x0, width, rows, y0, z0, tier_h, tiers, split, col, aft_plain, fore_plain):
    """One bay's deck cargo as one closed block, its outer faces cut at the
    boxes' edges and coloured box by box. `aft_plain`/`fore_plain` are
    (first column, end column, tiers) of an end face that looks into a
    narrow gap: those cells merge into one face. Each face's
    `material_index` is its colour's place in COLOUR_NAMES."""
    xs = [x0 + width * i / rows for i in range(rows + 1)]
    ys = [y0, y0 + BOX_40 / 2, y0 + BOX_40] if split else [y0, y0 + BOX_40]
    zs = [z0 - LAP] + [z0 + tier_h * t for t in range(1, tiers + 1)]
    nseg = len(ys) - 1
    bm = bmesh.new()
    vmap = {}

    def v(i, j, k):
        key = (i, j, k)
        if key not in vmap:
            vmap[key] = bm.verts.new((xs[i], ys[j], zs[k]))
        return vmap[key]

    def face(verts, c):
        f = bm.faces.new(verts)
        f.material_index = COLOUR_NAMES.index(c)
        return f

    bottom, plain_aft, plain_fore = [], [], []
    for i in range(rows):
        for j in range(nseg):
            face((v(i, j, tiers), v(i + 1, j, tiers), v(i + 1, j + 1, tiers), v(i, j + 1, tiers)), col[i][tiers - 1][j])
            bottom.append(face((v(i, j, 0), v(i, j + 1, 0), v(i + 1, j + 1, 0), v(i + 1, j, 0)), col[i][0][j]))
    for t in range(tiers):
        for j in range(nseg):
            face((v(0, j, t), v(0, j, t + 1), v(0, j + 1, t + 1), v(0, j + 1, t)), col[0][t][j])
            face((v(rows, j, t), v(rows, j + 1, t), v(rows, j + 1, t + 1), v(rows, j, t + 1)), col[rows - 1][t][j])
        for i in range(rows):
            f = face((v(i, 0, t), v(i + 1, 0, t), v(i + 1, 0, t + 1), v(i, 0, t + 1)), col[i][t][0])
            if aft_plain and aft_plain[0] <= i < aft_plain[1] and t < aft_plain[2]:
                plain_aft.append(f)
            f = face((v(i, nseg, t), v(i, nseg, t + 1), v(i + 1, nseg, t + 1), v(i + 1, nseg, t)), col[i][t][nseg - 1])
            if fore_plain and fore_plain[0] <= i < fore_plain[1] and t < fore_plain[2]:
                plain_fore.append(f)
    for group in (bottom, plain_aft, plain_fore):
        if len(group) > 1:
            fill = group[0].material_index
            res = bmesh.ops.dissolve_faces(bm, faces=group, use_verts=True)
            for f in res["region"]:
                f.material_index = fill
    # the merged faces' sides still carry the old cut points: a point between
    # only two collinear edges goes
    lone = [vv for vv in bm.verts if len(vv.link_edges) == 2 and
            abs((vv.link_edges[0].other_vert(vv).co - vv.co).normalized().dot(
                (vv.link_edges[1].other_vert(vv).co - vv.co).normalized()) + 1) < 1e-6]
    if lone:
        bmesh.ops.dissolve_verts(bm, verts=lone)
    return bm


class Bay:
    def __init__(self, y0, tiers, kind, split, rows_spec=None):
        self.y0, self.y1 = y0, y0 + BOX_40
        self.tiers, self.kind, self.split, self.rows_spec = tiers, kind, split, rows_spec
        self.tier_h = BOX_HC if kind == "hc" else BOX_H


# --- one ship --------------------------------------------------------------------------

class Ship:
    """A ship's hull, its layout fore and aft, and its parts."""

    def __init__(self, name, hull, rows_max, bay_gap, fore, aft, house_l, house_w, house_tiers, tier,
                 wh, wh_over, wings, funnel, funnel_top, funnel_rake, funnel_cap, mast_h, foremast_h,
                 breakwater_h, lashing, lashing_d=LASHING_D, wing_cabs=False):
        self.name, self.hull, self.rows_max, self.bay_gap = name, hull, rows_max, bay_gap
        self.lashing_d, self.wing_cabs = lashing_d, wing_cabs
        self.house_l, self.house_w, self.house_tiers, self.tier = house_l, house_w, house_tiers, tier
        self.wh, self.wh_over, self.wings = wh, wh_over, wings
        self.funnel, self.funnel_top, self.funnel_rake, self.funnel_cap = funnel, funnel_top, funnel_rake, funnel_cap
        self.mast_h, self.foremast_h, self.breakwater_h, self.lashing = mast_h, foremast_h, breakwater_h, lashing
        h = hull
        y1 = h.y_fc - FIRST_BAY_CLEAR
        self.fore = []
        for spec in fore:
            self.fore.append(Bay(y1 - BOX_40, *spec))
            y1 = y1 - BOX_40 - bay_gap
        self.house_front = self.fore[-1].y0 - HOUSE_GAP
        self.house_aft = self.house_front - house_l
        # the funnel stands against the house's back, unless the layout aft
        # names it among the bays ("funnel"), where it stands on its own
        if "funnel" in aft:
            y1 = self.house_aft - HOUSE_GAP
        else:
            self.funnel_fwd = self.house_aft + FUNNEL_LAP
            self.funnel_aft = self.funnel_fwd - funnel[0]
            y1 = self.funnel_aft - HOUSE_GAP
        self.aft = []
        self.groups = [self.fore]            # runs of bays with only a narrow gap between them
        run = []
        for spec in aft:
            if spec == "funnel":
                self.funnel_fwd = y1 + bay_gap - HOUSE_GAP
                self.funnel_aft = self.funnel_fwd - funnel[0]
                y1 = self.funnel_aft - HOUSE_GAP
                if run:
                    self.groups.append(run)
                run = []
                continue
            bay = Bay(y1 - BOX_40, *spec)
            self.aft.append(bay)
            run.append(bay)
            y1 = y1 - BOX_40 - bay_gap
        if run:
            self.groups.append(run)
        self.mooring = self.aft[-1].y0 - (-h.loa / 2) if self.aft else None
        assert self.mooring is None or self.mooring >= MOORING_MIN, (name, self.mooring)
        self.bridge_floor = h.zd + house_tiers * tier
        self.wh_front = self.house_front + wh_over
        self.eye = (self.wh_front - 1.0, self.bridge_floor + EYE_OVER_FLOOR)
        self.cover_top = h.zd + COVER_TOP

    def bays(self):
        return self.fore + self.aft

    def rows_at(self, bay):
        """How many rows the deck holds across this bay: the narrower end,
        less the margin at each side, capped at the class's rows."""
        h = self.hull
        hb = min(h.hb(y, h.zd) for y in (bay.y0 - COVER_OVER_END, bay.y1 + COVER_OVER_END))
        room = 2 * (hb - DECK_MARGIN) - 2 * COVER_SIDE_PROUD
        return min(self.rows_max, int((room + ROW_GAP) // (BOX_W + ROW_GAP)))

    @staticmethod
    def stack_width(rows):
        return rows * BOX_W + (rows - 1) * ROW_GAP

    def top(self, bay):
        return self.cover_top + bay.tiers * bay.tier_h

    # -- parts --
    def build_hatches(self, coll, m, variant, prefix):
        made = {}
        out = []
        h = self.hull
        for n, bay in enumerate(self.bays(), 1):
            rows = self.rows_at(bay)
            cover_w = self.stack_width(rows) + 2 * COVER_SIDE_PROUD
            coaming_w = cover_w - 2 * COAMING_INSET
            key = round(cover_w, 4)
            yc = (bay.y0 + bay.y1) / 2
            if key not in made:
                bm = bmesh.new()
                hl = BOX_40 / 2
                box_into(bm, -coaming_w / 2, coaming_w / 2, -hl - COAMING_OVER_END, hl + COAMING_OVER_END,
                         h.zd - LAP, h.zd + COAMING_H)
                box_into(bm, -cover_w / 2, cover_w / 2, -hl - COVER_OVER_END, hl + COVER_OVER_END,
                         h.zd + COVER_Z0, h.zd + COVER_TOP)
                obj = finish(f"{prefix}hatch_{n:02d}", bm, coll, [m["hatch"]], variant)
                made[key] = obj.data
            else:
                obj = bpy.data.objects.new(f"{prefix}hatch_{n:02d}", made[key])
                for k, val in (("kyt_unwrap", "facets"), ("kyt_variant", variant), ("kyt_collision", "none")):
                    obj[k] = val
                obj[TAG] = True
                coll.objects.link(obj)
            obj.location = (0.0, yc, 0.0)
            out.append(obj)
        return out

    def build_lashing(self, coll, m, variant, prefix):
        if not self.lashing:
            return []
        made, out, h = {}, [], self.hull
        n = 0
        for group in self.groups:
            for a, b in zip(group, group[1:]):
                n += 1
                fwd, aft = (a, b) if a.y0 > b.y0 else (b, a)
                w = min(self.stack_width(self.rows_at(fwd)), self.stack_width(self.rows_at(aft))) - 0.6
                key = round(w, 4)
                if key not in made:
                    bm = bmesh.new()
                    box_into(bm, -w / 2, w / 2, -self.lashing_d / 2, self.lashing_d / 2, h.zd - LAP,
                             h.zd + COVER_TOP + BOX_H)
                    obj = finish(f"{prefix}lashing_bridge_{n:02d}", bm, coll, [m["lashing"]], variant)
                    made[key] = obj.data
                else:
                    obj = bpy.data.objects.new(f"{prefix}lashing_bridge_{n:02d}", made[key])
                    for k, val in (("kyt_unwrap", "facets"), ("kyt_variant", variant), ("kyt_collision", "none")):
                        obj[k] = val
                    obj[TAG] = True
                    coll.objects.link(obj)
                obj.location = (0.0, (aft.y1 + fwd.y0) / 2, 0.0)
                out.append(obj)
        return out

    def build_stacks(self, coll, variant, prefix, loads=None, seed=None):
        """The deck cargo, a block per bay. `loads` (the light ship) gives
        each bay its own (tiers, height, 20 ft pairs, rows) or None; its
        ends are cut box by box all over. `seed` names whose colours to
        repeat, so a bay that is the same as another ship's comes out the same."""
        out = []
        bays = self.bays()
        for n, bay in enumerate(bays):
            if loads is not None:
                load = loads[n]
                if load is None:
                    continue
                bay = Bay(bay.y0, *load)
            rows_full = self.rows_at(bay)
            r0, r1 = 0, rows_full
            if bay.rows_spec:
                r0, r1 = max(0, bay.rows_spec[0]), min(rows_full, bay.rows_spec[1])
            rows = r1 - r0
            pitch = BOX_W + ROW_GAP
            x0 = -self.stack_width(rows_full) / 2 + r0 * pitch
            width = self.stack_width(rows)
            aft_plain = fore_plain = None
            if loads is None:
                aft_plain = self.plain(bay, rows, self.neighbour(bay, -1))
                fore_plain = self.plain(bay, rows, self.neighbour(bay, +1))
            rng = random.Random(f"{PROP}-{seed or variant}-{n}")
            segs = 2 if bay.split else 1
            col = box_colours(rng, rows, bay.tiers, segs)
            bm = stack_bm(x0, width, rows, bay.y0, self.cover_top, bay.tier_h, bay.tiers, bay.split,
                          col, aft_plain, fore_plain)
            used = sorted({f.material_index for f in bm.faces})
            for f in bm.faces:
                f.material_index = used.index(f.material_index)
            obj = finish(f"{prefix}deck_cargo_{n + 1:02d}", bm, coll, [box_mat(COLOUR_NAMES[c]) for c in used], variant)
            out.append(obj)
        return out

    def neighbour(self, bay, direction):
        """The bay across the narrow gap fore (+1) or aft (-1), or None where
        that end looks onto the forecastle, the house, the funnel or the stern."""
        for group in self.groups:
            if bay in group:
                k = group.index(bay)
                j = k - direction            # the groups run fore to aft
                return group[j] if 0 <= j < len(group) else None
        return None

    def plain(self, bay, rows, nb):
        """Which of an end face's cells look into the gap against `nb` and
        so merge: the columns inside the neighbour's span short of its outer
        ones and of this block's own, below the tier under the neighbour's top."""
        if nb is None or rows < 3:
            return None
        nrows = self.rows_at(nb)
        d = max(0, math.ceil((rows - nrows) / 2))
        c0, c1 = max(1, d + 1), min(rows - 1, rows - d - 1)
        k = int((self.top(nb) - self.cover_top) / bay.tier_h + 1e-6) - 1
        k = max(0, min(bay.tiers - 1, k))
        if c1 - c0 < 1 or k < 1:
            return None
        return (c0, c1, k)

    def build_house(self, coll, m, variant, prefix):
        h = self.hull
        out = []
        hw = self.house_w / 2
        out.append(box(f"{prefix}deckhouse", coll, m["house"], variant, -hw, hw, self.house_aft, self.house_front,
                       h.zd - LAP, self.bridge_floor))
        wl, ww, wh = self.wh
        f0 = self.bridge_floor
        out.append(box(f"{prefix}wheelhouse", coll, m["house"], variant, -ww / 2, ww / 2,
                       self.wh_front - wl, self.wh_front, f0 - LAP, f0 + wh))
        p = WINDOW_PROUD
        out.append(box(f"{prefix}wheelhouse_windows", coll, m["glass"], variant, -ww / 2 - p, ww / 2 + p,
                       self.wh_front - wl - p, self.wh_front + p, f0 + WINDOW_Z[0], f0 + WINDOW_Z[1]))
        if self.wings:
            bm = bmesh.new()
            reach = h.b / 2 - 0.05
            for sx in (-1, 1):
                xa, xb = sorted((sx * (ww / 2 - LAP), sx * reach))
                box_into(bm, xa, xb, self.wh_front - 0.2 - WING_D, self.wh_front - 0.2, f0 + WING_Z[0], f0 + WING_Z[1])
            out.append(finish(f"{prefix}bridge_wings", bm, coll, [m["house"]], variant))
        if self.wing_cabs:
            # a cab closing in each wing: from inside the wheelhouse's side to
            # 2 cm past the wing's tip, front and back, its window band set
            # proud all round and off the wheelhouse's band
            reach, q = h.b / 2 - 0.05, WING_CAB_PROUD
            y0, y1 = self.wh_front - 0.2 - WING_D - q, self.wh_front - 0.2 + q
            bm, bg = bmesh.new(), bmesh.new()
            for sx in (-1, 1):
                xa, xb = sorted((sx * (ww / 2 - 2 * LAP), sx * (reach + q)))   # its inner end past the wing's
                box_into(bm, xa, xb, y0, y1, f0 + WING_CAB_Z[0], f0 + WING_CAB_Z[1])
                xa, xb = sorted((sx * (ww / 2 + 0.2), sx * (reach + q + p)))
                box_into(bg, xa, xb, y0 - p, y1 + p, f0 + WING_CAB_WINDOWS[0], f0 + WING_CAB_WINDOWS[1])
            out.append(finish(f"{prefix}bridge_wing_cabs", bm, coll, [m["house"]], variant))
            out.append(finish(f"{prefix}bridge_wing_cab_windows", bg, coll, [m["glass"]], variant))
        # the radar mast on the wheelhouse roof, its yard across
        roof = f0 + wh
        ym = self.wh_front - wl / 2
        bm = bmesh.new()
        box_into(bm, -0.35, 0.35, ym - 0.35, ym + 0.35, roof - LAP, roof + self.mast_h)
        box_into(bm, -3.5, 3.5, ym - 0.15, ym + 0.15, roof + 0.65 * self.mast_h, roof + 0.65 * self.mast_h + 0.3)
        out.append(finish(f"{prefix}radar_mast", bm, coll, [m["mast"]], variant))
        # the funnel against the house's back, raked aft, its top band dark
        fl, fw = self.funnel
        z0, zt = h.zd - 2 * LAP, self.funnel_top     # its foot under the house's, not level with it
        zc = zt - self.funnel_cap
        yc0 = self.funnel_fwd - fl / 2
        rings = []
        for z, taper in ((z0, 1.0), (zc, 0.9), (zt, 0.86)):
            u = (z - z0) / (zt - z0)
            rings.append((z, octagon(0.0, yc0 - self.funnel_rake * u, taper * fw / 2, taper * fl / 2, 0.22 * fw * taper)))
        bm = bmesh.new()
        vs = [[bm.verts.new((x, y, z)) for x, y in pts] for z, pts in rings]
        bottom = bm.faces.new(vs[0])
        top = bm.faces.new(vs[-1])
        top.material_index = 1
        bottom.material_index = 0
        for k in range(len(vs) - 1):
            for i in range(8):
                j = (i + 1) % 8
                f = bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
                f.material_index = k
        out.append(finish(f"{prefix}funnel", bm, coll, [m["funnel"], m["funnel_top"]], variant))
        # a davit lifeboat each side, hung off the house wall
        bl, bb, bh = LIFEBOAT
        zl = h.zd + LIFEBOAT_TIER * self.tier + 0.5
        yl = (self.house_front + self.house_aft) / 2
        bm = bmesh.new()
        for sx in (-1, 1):
            xc = sx * (hw + LIFEBOAT_OUT + bb / 2)
            c = 0.3 * bb
            sec = [(xc + bb / 2, zl + c), (xc + bb / 2, zl + bh - c), (xc + bb / 2 - c, zl + bh), (xc - bb / 2 + c, zl + bh),
                   (xc - bb / 2, zl + bh - c), (xc - bb / 2, zl + c), (xc - bb / 2 + c, zl), (xc + bb / 2 - c, zl)]
            prism_into(bm, sec, "y", yl - bl / 2, yl + bl / 2)
        out.append(finish(f"{prefix}lifeboats", bm, coll, [m["lifeboat"]], variant))
        return out

    def build_bow(self, coll, m, variant, prefix):
        h = self.hull
        out = []
        y0 = h.y_fc + BREAKWATER_AFT
        hw = h.hb(y0 + BREAKWATER_APEX, h.zfc) - 0.5
        a, t = BREAKWATER_APEX, BREAKWATER_T
        poly = [(-hw, y0), (0.0, y0 + a), (hw, y0), (hw, y0 - t), (0.0, y0 + a - t), (-hw, y0 - t)]
        bm = bmesh.new()
        prism_into(bm, poly, "z", h.zfc - LAP, h.zfc + self.breakwater_h)
        out.append(finish(f"{prefix}breakwater", bm, coll, [m["mast"]], variant))
        yf = h.loa / 2 - FOREMAST_BACK
        out.append(box(f"{prefix}foremast", coll, m["mast"], variant, -0.25, 0.25, yf - 0.25, yf + 0.25,
                       h.zfc - LAP, h.zfc + self.foremast_h))
        return out

    def build(self, coll, m, variant, prefix=""):
        h = self.hull
        parts = [h.build(f"{prefix}hull", coll, m, variant),
                 h.build_rudder(f"{prefix}rudder", coll, m, variant),
                 h.build_propeller(f"{prefix}propeller", coll, m, variant)]
        parts += self.build_bow(coll, m, variant, prefix)
        parts += self.build_house(coll, m, variant, prefix)
        parts += self.build_hatches(coll, m, variant, prefix)
        parts += self.build_lashing(coll, m, variant, prefix)
        return parts

    def view(self, loads=None, pose=None):
        """The bridge's view over the cargo (SOLAS V/22): the eye, the point
        on the sea 500 m (or two lengths) ahead of the bow, and for each
        obstacle ahead of the bridge its top's margin under the sightline.
        `loads` is a light ship's deck cargo, `pose` its rise and trim."""
        h = self.hull
        if loads is None:
            obstacles = [(f"bay {n + 1}", b.y1, self.top(b)) for n, b in enumerate(self.fore)]
        else:
            obstacles = [(f"bay {n + 1}", b.y1, self.top(Bay(b.y0, *loads[n])))
                         for n, b in enumerate(self.fore) if loads[n] is not None]
        obstacles.append(("breakwater", h.y_fc + BREAKWATER_AFT + BREAKWATER_APEX, h.zfc + self.breakwater_h))
        ey, ez = self.eye
        bow = h.loa / 2
        if pose is not None:
            def posed(y, z):
                v = pose @ Vector((0.0, y, z))
                return v.y, v.z
            ey, ez = posed(ey, ez)
            bow = posed(bow, h.zfc)[0]
            obstacles = [(label, *posed(y, z)) for label, y, z in obstacles]
        target = bow + min(BLIND_LIMIT, 2 * h.loa)
        rows = []
        worst = 0.0
        for label, y, z in obstacles:
            line = ez * (target - y) / (target - ey)
            hit = ey + (y - ey) * ez / (ez - z) if ez > z else float("inf")
            worst = max(worst, hit - bow)
            rows.append((label, line - z))
        return target, worst, rows


def panamax(name="panamax", fore=PX_FORE_BAYS, aft=PX_AFT_BAYS, lashing=False, wing_cabs=False):
    hull = Hull(PX_LOA, PX_LBP, PX_B, PX_D, PX_T, PX_BOW_OVER, PX_FC_LEN, PX_FC_H, PX_BILGE_R)
    return Ship(name, hull, PX_ROWS, PX_BAY_GAP, fore, aft, PX_HOUSE_L, PX_HOUSE_W,
                PX_HOUSE_TIERS, PX_TIER, (PX_WH_L, PX_WH_W, PX_WH_H), PX_WH_OVER, PX_WINGS, PX_FUNNEL,
                PX_FUNNEL_TOP, PX_FUNNEL_RAKE, PX_FUNNEL_CAP, PX_MAST_H, PX_FOREMAST_H, PX_BREAKWATER_H, lashing,
                lashing_d=PX_LASHING_D, wing_cabs=wing_cabs)


def post_panamax(name="post_panamax", aft=PP_AFT_BAYS):
    hull = Hull(PP_LOA, PP_LBP, PP_B, PP_D, PP_T, PP_BOW_OVER, PP_FC_LEN, PP_FC_H, PP_BILGE_R)
    return Ship(name, hull, PP_ROWS, PP_BAY_GAP, PP_FORE_BAYS, aft, PP_HOUSE_L, PP_HOUSE_W,
                PP_HOUSE_TIERS, PP_TIER, (PP_WH_L, PP_WH_W, PP_WH_H), PP_WH_OVER, PP_WINGS, PP_FUNNEL,
                PP_FUNNEL_TOP, PP_FUNNEL_RAKE, PP_FUNNEL_CAP, PP_MAST_H, PP_FOREMAST_H, PP_BREAKWATER_H, True)


def light_matrix(ship, rise=LIGHT_RISE, trim=LIGHT_TRIM):
    """A half-empty ship's pose: raised, and trimmed by the stern (bow up)
    about midships."""
    angle = math.atan2(trim, ship.hull.lbp)
    return Matrix.Translation((0.0, 0.0, rise)) @ Matrix.Rotation(angle, 4, "X")


def same_mesh(a, b, tol=1e-5):
    """The shift that turns mesh `b` into mesh `a`, if they are the same
    shape, topology and materials up to a shift; else None."""
    if (len(a.vertices) != len(b.vertices) or len(a.polygons) != len(b.polygons)
            or [m.name for m in a.materials] != [m.name for m in b.materials]):
        return None
    t = a.vertices[0].co - b.vertices[0].co
    for va, vb in zip(a.vertices, b.vertices):
        if (va.co - vb.co - t).length > tol:
            return None
    for pa, pb in zip(a.polygons, b.polygons):
        if tuple(pa.vertices) != tuple(pb.vertices) or pa.material_index != pb.material_index:
            return None
    return t


def link_identical(objs, pool):
    """Every part in `objs` that is a shifted copy of a mesh in `pool` takes
    that mesh, linked, moved by the shift: one mesh, so reshaping one
    reshapes both. Returns how many were linked."""
    meshes = []
    for o in pool:
        if o.data not in meshes:
            meshes.append(o.data)
    linked = 0
    for o in objs:
        for me in meshes:
            if me is o.data:
                break
            t = same_mesh(o.data, me)
            if t is not None:
                old = o.data
                o.data = me
                o.location = o.location + t
                if old.users == 0:
                    bpy.data.meshes.remove(old)
                linked += 1
                break
    return linked


# --- reference --------------------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    bm = bmesh.new()
    prism_into(bm, ring, "z", 0.0, height - 0.40)
    body = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:
        if v not in body:
            v.co.z += height - 0.17
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    mesh.materials.append(mat or material("reference_figure", (0.30, 0.22, 0.40, 1.0)))
    obj[TAG] = True
    obj.location = (x, y, z)
    coll.objects.link(obj)
    return obj


def edges_obj(name, coll, pts, closed=True):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    for i in range(len(vs) - (0 if closed else 1)):
        bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    return obj


def waterline(name, coll, hull_obj):
    """The hull cut at z = 0 in its pose: the waterline it floats at."""
    bm = bmesh.new()
    bm.from_mesh(hull_obj.data)
    bm.transform(hull_obj.matrix_world)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                                 plane_co=(0, 0, 0), plane_no=(0, 0, 1))
    cut = {e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)}
    out = bmesh.new()
    vmap = {}
    for e in cut:
        vs = []
        for v in e.verts:
            if v not in vmap:
                vmap[v] = out.verts.new(v.co)
            vs.append(vmap[v])
        out.edges.new(vs)
    bm.free()
    mesh = bpy.data.meshes.new(name)
    out.to_mesh(mesh)
    out.free()
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    coll.objects.link(obj)
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    return obj, (max(ys) - min(ys), max(xs) - min(xs))


def build_reference(reference, ships, hulls):
    out = {}
    for (label, ship), hull_obj in zip(ships, hulls):
        h = ship.hull
        if label != "panamax_light":
            tag = f"{h.loa:g}x{h.b:g}".replace(".", "p")
            edges_obj(f"outline_{label}_{tag}", reference,
                      [(-h.b / 2, -h.loa / 2, 0), (h.b / 2, -h.loa / 2, 0), (h.b / 2, h.loa / 2, 0), (-h.b / 2, h.loa / 2, 0)])
            ey, ez = ship.eye
            target, _, _ = ship.view()
            edges_obj(f"sightline_{label}", reference, [(0, ey, ez), (0, target, 0)], closed=False)
        name = "waterline" if label == "panamax" else f"waterline_{label}"
        out[label] = waterline(name, reference, hull_obj)[1]
    px = ships[0][1]
    figure("figure_1p7m", reference, px.hull.b / 2 - 1.0, px.fore[2].y1 + 0.5, px.hull.zd)
    return out


# --- checks ---------------------------------------------------------------------------

def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def triangles(objs):
    total = 0
    for o in objs:
        o.data.calc_loop_triangles()
        total += len(o.data.loop_triangles)
    return total


def extents(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def report(variant, wl):
    bpy.context.view_layer.update()
    objs = variant_objects(variant)
    tris = triangles(objs)
    cargo = triangles([o for o in objs if "deck_cargo" in o.name])
    lo, hi = extents(objs)
    print(f"{PROP}: {variant}: {len(objs)} parts, {tris} triangles ({cargo} of them deck cargo); "
          f"{hi.y - lo.y:.1f} x {hi.x - lo.x:.2f} m overall, waterline {wl[0]:.1f} x {wl[1]:.2f} m, "
          f"draft {-lo.z:.2f} m, air draft {hi.z:.2f} m (highest point over the waterline)")
    return tris


def print_ship(ship, variant):
    h = ship.hull
    rows = [ship.rows_at(b) for b in ship.bays()]
    tiers = [b.tiers for b in ship.bays()]
    print(f"{PROP}: {variant}: LOA {h.loa:g}, LBP {h.lbp:g}, B {h.b:g}, D {h.d:g}, T {h.t:g}: freeboard "
          f"{h.zd:.1f} m, forecastle deck {h.zfc:.1f}, FP y {h.fp:.1f}, AP y {h.ap:.1f}, bulb nose y {h.yn:.1f}")
    print(f"{PROP}: {variant}: bays fore {len(ship.fore)}, aft {len(ship.aft)}; rows {rows}; tiers {tiers}; "
          f"house y {ship.house_aft:.1f}..{ship.house_front:.1f} "
          f"({(h.loa / 2 - ship.house_front) / h.loa * 100:.0f}% of the length aft of the stem head), "
          f"funnel y {ship.funnel_aft:.1f}..{ship.funnel_fwd:.1f}, aft mooring deck {ship.mooring:.1f} m; "
          f"bridge floor {ship.bridge_floor:.1f}, eye {ship.eye[1]:.1f}, wheelhouse roof {ship.bridge_floor + ship.wh[2]:.1f}, "
          f"cargo top {max(ship.top(b) for b in ship.bays()):.1f}")
    target, worst, margins = ship.view()
    low = min(margins, key=lambda r: r[1])
    print(f"{PROP}: {variant}: bridge view: sea hidden for {worst:.0f} m ahead of the bow (SOLAS allows "
          f"{min(BLIND_LIMIT, 2 * h.loa):.0f}); least margin under the sightline {low[1]:.2f} m at {low[0]}; "
          + ", ".join(f"{a} {b:+.1f}" for a, b in margins))
    assert worst <= min(BLIND_LIMIT, 2 * h.loa) + 1e-6, (variant, worst)


def print_view(ship, variant, loads, pose):
    """A light ship's bridge view: its own deck load, raised and trimmed."""
    h = ship.hull
    target, worst, margins = ship.view(loads=loads, pose=pose)
    low = min(margins, key=lambda r: r[1])
    print(f"{PROP}: {variant}: bridge view: sea hidden for {worst:.0f} m ahead of the bow (SOLAS allows "
          f"{min(BLIND_LIMIT, 2 * h.loa):.0f}); least margin under the sightline {low[1]:.2f} m at {low[0]}")
    assert worst <= min(BLIND_LIMIT, 2 * h.loa) + 1e-6, (variant, worst)


# --- renders ---------------------------------------------------------------------------

def show_variant(variant):
    for v in VARIANTS:
        for o in variant_objects(v):
            o.hide_render = v != variant


def render(folder, ships, only=None, views=None, lineup=False):
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb, alpha=1.0):
        mt = material(name, (*rgb, 1.0))
        if alpha < 1.0:
            bsdf = mt.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Alpha"].default_value = alpha
            bsdf.inputs["Roughness"].default_value = 0.25
            for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
                try:
                    setattr(mt, attr, val)
                except (AttributeError, TypeError):
                    pass
        return mt

    def stage_box(name, m_, x0, x1, y0, y1, z0, z1):
        bm = bmesh.new()
        box_into(bm, x0, x1, y0, y1, z0, z1)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        o = bpy.data.objects.new(name, mesh)
        mesh.materials.append(m_)
        stage.objects.link(o)
        return o

    water = mat("_water", (0.05, 0.20, 0.33), alpha=0.72)
    plane = bpy.data.meshes.new("_water")
    plane.from_pydata([(-3000, -3000, 0), (3000, -3000, 0), (3000, 3000, 0), (-3000, 3000, 0)], [], [(0, 1, 2, 3)])
    plane.materials.append(water)
    stage.objects.link(bpy.data.objects.new("_water", plane))

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((0.45, -0.30, 0.80)).to_track_quat("Z", "Y").to_euler()   # from starboard, a little aft
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

    def points(variant):
        return [o.matrix_world @ Vector(c) for o in variant_objects(variant) for c in o.bound_box]

    def shoot(name, eye, target, lens=35, size=(1600, 1000), ortho=None, fit=None, rot=None):
        cam.location = eye
        d = Vector(target) - Vector(eye)
        cam.rotation_euler = rot if rot is not None else d.to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.lens = lens
        cam.data.clip_start = 0.1
        cam.data.clip_end = 6000
        scene.render.resolution_x, scene.render.resolution_y = size
        if fit:
            backed = 1.0
            while backed < 6.0:
                bpy.context.view_layer.update()
                if all(0.03 <= c.x <= 0.97 and 0.03 <= c.y <= 0.97 and c.z > 0
                       for c in (world_to_camera_view(scene, cam, p) for p in fit)):
                    break
                backed *= 1.08
                cam.location = Vector(target) - d * backed
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{PROP}: rendered {scene.render.filepath}")

    fig_mat = mat("_figure_stage", (0.85, 0.20, 0.55))
    quay_mat = mat("_quay", (0.30, 0.29, 0.27))
    crane_mat = mat("_crane", (0.80, 0.30, 0.20))
    line_mat = mat("_sightline", (0.95, 0.10, 0.10))
    plan_rot = Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1))).to_euler()   # bow to the right, looking down
    QUAY_TOP = 3.5             # render only: a stand-in quay top over the water, chosen
    def want(view):
        return views is None or view in views

    for label, ship in ships:
        if only is not None and label not in only:
            continue
        h = ship.hull
        show_variant(label)
        pts = points(label)
        lo, hi = extents(variant_objects(label))
        L = h.loa
        if want("three_quarter"):
            shoot(f"{label}_three_quarter", (0.75 * L, 0.80 * L, 0.32 * L), (0.0, 0.05 * L, 10.0), lens=50, fit=pts)
        if want("bow_three_quarter_low"):
            shoot(f"{label}_bow_three_quarter_low", (0.45 * L, 0.95 * L, 8.0), (0.0, 0.25 * L, 12.0), lens=50, fit=pts)
        zmid = (hi.z + lo.z) / 2
        # 4 degrees down, so the water shows as a band over the hull below it
        if want("side_elevation"):
            shoot(f"{label}_side_elevation", (900.0, 0.0, zmid + 900.0 * math.tan(math.radians(4.0))), (0.0, 0.0, zmid),
                  size=(2400, 640), ortho=345.0)
        if want("plan"):
            shoot(f"{label}_plan", (0.0, 0.0, 600.0), (0.0, 0.0, 0.0), size=(2400, 640), ortho=345.0, rot=plan_rot)
        if want("house_close"):
            # the house, its bridge wings and the bays round it, close, from
            # the starboard bow quarter
            yh = ship.house_front
            shoot(f"{label}_house_close", (h.b / 2 + 48.0, yh + 62.0, ship.bridge_floor + 12.0),
                  (0.0, yh - 6.0, ship.bridge_floor - 10.0), lens=35)
        if not (want("with_figure") or want("beside_crane") or want("from_the_bridge")):
            continue
        # beside a 1.7 m figure on a stand-in quay along the starboard side
        xq = h.b / 2 + 2.0
        q = stage_box("_quay", quay_mat, xq, xq + 80.0, -L / 2 - 40, L / 2 + 40, -3.0, QUAY_TOP)
        yfig = 0.22 * L
        f = figure("_figure_quay", stage, xq + 3.0, yfig, QUAY_TOP, mat=fig_mat)
        if want("with_figure"):
            shoot(f"{label}_with_figure", (xq + 24.0, yfig + 16.0, QUAY_TOP + 1.6), (xq - 3.0, yfig - 22.0, 14.0), lens=24)
        # beside a stand-in post-Panamax gantry crane (the brief's numbers:
        # 30.48 m gauge, 50 m outreach, 18 m backreach, boom at 46 m, apex 72 m,
        # 15 m clear under the portal), on the same quay
        crane = []
        xr = xq + 3.0                          # the waterside rail 3 m in from the quay edge, chosen
        yc = 0.05 * L
        zq = QUAY_TOP
        for xl in (xr, xr + 30.48):
            for yl in (yc - 9.0, yc + 9.0):
                crane.append(stage_box("_crane_leg", crane_mat, xl - 0.8, xl + 0.8, yl - 0.8, yl + 0.8, zq, zq + 46.0))
            crane.append(stage_box("_crane_sill", crane_mat, xl - 0.9, xl + 0.9, yc - 13.5, yc + 13.5, zq, zq + 1.5))
        for yl in (yc - 9.0, yc + 9.0):
            crane.append(stage_box("_crane_portal", crane_mat, xr - 0.9, xr + 30.48 + 0.9, yl - 0.9, yl + 0.9,
                                   zq + 15.0, zq + 17.0))
            crane.append(stage_box("_crane_boom", crane_mat, xr - 50.0, xr + 30.48 + 18.0, yl - 0.9, yl + 0.9,
                                   zq + 44.0, zq + 47.0))
            crane.append(stage_box("_crane_apex", crane_mat, xr + 4.0, xr + 6.0, yl - 0.6, yl + 0.6, zq + 46.0, zq + 72.0))
        if want("beside_crane"):
            shoot(f"{label}_beside_crane", (xq + 260.0, yc + 230.0, 70.0), (0.0, yc - 20.0, 25.0), lens=40)
        for o in crane + [q, f]:
            bpy.data.objects.remove(o, do_unlink=True)
        if not label.endswith("_light") and want("from_the_bridge"):
            # from the bridge: the conning position's eye looking ahead; a red
            # float marks the sea 500 m ahead of the bow, the end of the blind
            # zone SOLAS allows, which must show over the cargo
            ey, ez = ship.eye
            target, _, _ = ship.view()
            float_ = stage_box("_float", line_mat, -6.0, 6.0, target - 1.0, target + 1.0, -0.5, 1.5)
            shoot(f"{label}_from_the_bridge", (0.0, ship.wh_front + 0.3, ez), (0.0, target, ez * 0.55), lens=28)
            bpy.data.objects.remove(float_, do_unlink=True)
    if lineup:
        # every variant's side elevation, one above the next, each in its own
        # band of see-through water, named on the left (the objects are moved
        # after the save and never saved)
        step = 80.0
        bpy.data.objects["_water"].hide_render = True
        ink = mat("_ink", (0.03, 0.03, 0.04))
        sea = mat("_lineup_water", (0.05, 0.20, 0.33), alpha=0.6)
        for i, v in enumerate(VARIANTS):
            off = -i * step
            for o in variant_objects(v):
                o.hide_render = False
                o.matrix_world = Matrix.Translation((0.0, 0.0, off)) @ o.matrix_world
            stage_box(f"_sea_{i}", sea, -60.0, 60.0, -175.0, 175.0, off - 16.0, off)
            curve = bpy.data.curves.new(f"_label_{i}", "FONT")
            curve.body = v
            curve.size = 8.0
            curve.materials.append(ink)
            label_o = bpy.data.objects.new(f"_label_{i}", curve)
            label_o.location = (40.0, -312.0, off + 4.0)
            label_o.rotation_euler = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0))).to_euler()
            stage.objects.link(label_o)
        zc = -(len(VARIANTS) - 1) * step / 2 + 18.0
        shoot("lineup_side_elevations", (900.0, -75.0, zc), (0.0, -75.0, zc), size=(1800, 2400),
              ortho=len(VARIANTS) * step + 20.0)
    show_variant("panamax")


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

    px, pp = panamax(), post_panamax()
    m = mats()
    px_parts = px.build(export, m, "panamax")
    px.build_stacks(export, "panamax", "")
    sub = bpy.data.collections.new("variant_post_panamax")
    export.children.link(sub)
    pp_parts = pp.build(sub, mats("post_panamax_"), "post_panamax", "post_panamax_")
    pp.build_stacks(sub, "post_panamax", "post_panamax_")
    light = bpy.data.collections.new("variant_panamax_light")
    export.children.link(light)
    pose = light_matrix(px)
    bpy.context.view_layer.update()          # the hatches' locations into their matrices
    light_parts = []
    for src in px_parts:                       # linked copies: one mesh each, reshaping one reshapes both
        dup = src.copy()
        dup.name = f"light_{src.name}"
        dup["kyt_variant"] = "panamax_light"
        light.objects.link(dup)
        dup.matrix_world = pose @ src.matrix_world
        light_parts.append(dup)
    for o in px.build_stacks(light, "panamax_light", "light_", loads=PX_LIGHT_BAYS):
        o.matrix_world = pose @ o.matrix_world
    bpy.context.view_layer.update()
    ships = [("panamax", px), ("post_panamax", pp), ("panamax_light", px)]
    wls = build_reference(reference, ships, [px_parts[0], pp_parts[0], light_parts[0]])

    # the further variants: built whole, then every part that is a shifted
    # copy of one already made takes that mesh, linked
    pool = [o for o in export.all_objects if o.type == "MESH"]
    linked = {}

    def further(ship, variant, m_, seed):
        coll = bpy.data.collections.new(f"variant_{variant}")
        export.children.link(coll)
        objs = ship.build(coll, m_, variant, f"{variant}_")
        objs += ship.build_stacks(coll, variant, f"{variant}_", seed=seed)
        bpy.context.view_layer.update()
        linked[variant] = (link_identical(objs, pool), len(objs))
        pool.extend(objs)
        return objs

    split = post_panamax("post_panamax_split", aft=PP_SPLIT_AFT)
    further(split, "post_panamax_split", mats("post_panamax_"), "post_panamax")
    tq = panamax("panamax_three_quarter_house", fore=PX_TQ_FORE, aft=PX_TQ_AFT)
    tq_parts = further(tq, "panamax_three_quarter_house", m, "panamax")
    lash = panamax("panamax_lashing", lashing=True)
    further(lash, "panamax_lashing", m, "panamax")
    cabs = panamax("panamax_wing_cabs", wing_cabs=True)
    further(cabs, "panamax_wing_cabs", m, "panamax")
    # the K-class half-empty, made as the panamax_light: its parts linked
    # copies of the post_panamax's, posed, with a deck load of its own
    pplight = bpy.data.collections.new("variant_post_panamax_light")
    export.children.link(pplight)
    pose_pp = light_matrix(pp, PP_LIGHT_RISE, PP_LIGHT_TRIM)
    pplight_parts = []
    for src in pp_parts:
        dup = src.copy()
        dup.name = "post_panamax_light_" + src.name[len("post_panamax_"):]
        dup["kyt_variant"] = "post_panamax_light"
        pplight.objects.link(dup)
        dup.matrix_world = pose_pp @ src.matrix_world
        pplight_parts.append(dup)
    for o in pp.build_stacks(pplight, "post_panamax_light", "post_panamax_light_", loads=PP_LIGHT_BAYS):
        o.matrix_world = pose_pp @ o.matrix_world
    bpy.context.view_layer.update()
    wls["post_panamax_light"] = waterline("waterline_post_panamax_light", reference, pplight_parts[0])[1]
    for v in ("post_panamax_split",):
        wls[v] = wls["post_panamax"]
    for v in ("panamax_three_quarter_house", "panamax_lashing", "panamax_wing_cabs"):
        wls[v] = wls["panamax"]
    ey, ez = tq.eye
    edges_obj("sightline_panamax_three_quarter_house", reference, [(0, ey, ez), (0, tq.view()[0], 0)], closed=False)
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    print_ship(px, "panamax")
    print_ship(pp, "post_panamax")
    print(f"{PROP}: panamax_light: the panamax raised {LIGHT_RISE:g} m and trimmed {LIGHT_TRIM:g} m by the stern "
          f"({math.degrees(math.atan2(LIGHT_TRIM, px.hull.lbp)):.3f} deg): drafts {px.hull.t - LIGHT_RISE + LIGHT_TRIM / 2:.1f} "
          f"aft, {px.hull.t - LIGHT_RISE:.1f} midships, {px.hull.t - LIGHT_RISE - LIGHT_TRIM / 2:.1f} forward; "
          f"{sum(1 for b in PX_LIGHT_BAYS if b)} of {len(PX_LIGHT_BAYS)} bays loaded")
    print_view(px, "panamax_light", PX_LIGHT_BAYS, light_matrix(px))
    print_ship(split, "post_panamax_split")
    print_ship(tq, "panamax_three_quarter_house")
    print_ship(lash, "panamax_lashing")
    print_ship(cabs, "panamax_wing_cabs")
    print(f"{PROP}: post_panamax_light: the post_panamax raised {PP_LIGHT_RISE:g} m and trimmed {PP_LIGHT_TRIM:g} m "
          f"by the stern: drafts {pp.hull.t - PP_LIGHT_RISE + PP_LIGHT_TRIM / 2:.1f} aft, {pp.hull.t - PP_LIGHT_RISE:.1f} "
          f"midships, {pp.hull.t - PP_LIGHT_RISE - PP_LIGHT_TRIM / 2:.1f} forward; "
          f"{sum(1 for b in PP_LIGHT_BAYS if b)} of {len(PP_LIGHT_BAYS)} bays loaded")
    print_view(pp, "post_panamax_light", PP_LIGHT_BAYS, pose_pp)
    for v, (n, of) in linked.items():
        print(f"{PROP}: {v}: {n} of its {of} new parts are linked meshes of parts already made")
    for v in VARIANTS:
        report(v, wls[v])
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
        views = argv[argv.index("--views") + 1].split(",") if "--views" in argv else None
        ships += [("post_panamax_split", split), ("panamax_three_quarter_house", tq), ("post_panamax_light", pp),
                  ("panamax_lashing", lash), ("panamax_wing_cabs", cabs)]
        render(argv[argv.index("--render") + 1], ships, only=only, views=views, lineup="--lineup" in argv)


main()
