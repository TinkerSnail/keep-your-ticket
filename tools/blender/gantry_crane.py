"""The container port's ship-to-shore gantry crane, blocked out (2026-10-03):
the new port on the mainland shore facing the city across the water, by the
bridge's east end ("lets add a modern port near the city"). Its cranes are the
port's silhouette, the way Oakland's read from San Francisco: seen from
kilometres off and from the suspension bridge, so the A-frame, the long boom
and the stays come first and everything else is a block.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        assets/source/props/gantry_crane.blend --python tools/blender/gantry_crane.py -- \
        [--replace] [--save] [--render <folder>]

Builds, from scratch every run, sixteen variants, all standing at the origin,
each marked `kyt_variant` so Send writes each as a prop of its own:

- **working**, in `export`: a late-1990s post-Panamax A-frame crane with its
  boom lowered over the water, the trolley out over a ship and the spreader
  hanging at mid height.
- **stowed**, in `export/variant_stowed` with its eye shut: the same crane
  with the boom raised 80 degrees for a ship to berth, the trolley parked at
  the back and the spreader hoisted under it. Every part that does not move
  is a linked copy of the working crane's mesh; the boom, the trolley, the
  cab and the spreader are linked copies too, only posed differently (the
  boom turns about its hinge as an object rotation), so reshaping one
  reshapes both. Only the forestays and the hoist ropes are its own meshes.
- **panamax_older**, in `export/variant_panamax_older` with its eye shut: a
  smaller Panamax-era crane on a 50 ft gauge, in grey-blue, of the kind 1990s
  ports still ran beside the new ones. It shares the gantry bogie set and
  the spreader with the other two as linked meshes.
- **working_far** and **stowed_far**, in `export/variant_working_far` and
  `export/variant_stowed_far` with their eyes shut (2026-10-03, Christina on
  fattening it for distance: "yes we like cartoony proportions so this
  works"): the same crane in both poses at the same size and clearances,
  its members fattened, chunky and cartoony, so its silhouette survives
  2 km in the player's 70 degree view at 1080p, where a pixel covers
  2.593 m: legs at least 2 px (5.3 m at the head), stays at least 1 px
  (2.72-2.80 m), struts, girders, boom, beams and braces about 1 px or
  more (table `FAR`). The legs' centres stay put, so the bogie footprint
  does and the clear between the legs narrows from 18.3 to 15.0 m. It has
  its own chunkier bogie set and spreader; stowed_far shares working_far's
  meshes the way stowed shares working's.
- The further variants (2026-10-03, Christina: "build all the offered
  variants"), each in `export/variant_<name>` with its eye shut and each the
  working crane's meshes linked but for what it changes:
  **working_white_red** and **working_grey_blue**, liveries on the same
  meshes through object-level material slots, each on its own materials;
  **panamax_older_stowed**, the older crane's boom raised 80 degrees;
  **working_spreader_down** (the spreader set on a ship's hatch covers),
  **working_trolley_backreach** (the trolley at full backreach, the spreader
  on a box on a chassis) and **working_trolley_portal** (the trolley parked
  between the legs, the spreader hoisted), poses for a busy row;
  **working_lattice**, lattice-truss girders and boom as 1970s cranes had;
  **working_single_girder**, a single box girder and boom (the "monobox")
  with a trolley that wraps round it; **working_house_under**, the
  machinery house hung under the girders; and **working_details**, a stair
  tower on a landside leg and aircraft warning lights on the apex and the
  boom's nose.

**The frame (the O-frame; 2026-10-03, Christina: "yes fold in the
o-frame").** Every crane is built the way real ship-to-shore cranes are: the
legs rise past the trolley to a girder support beam over each rail line,
and the girders hang from those beams on hangers outside the trolley, so
nothing crosses the trolley's path: the trolley passes under the support
beams, and the cab and the hoist ropes run down the gap between the girders
with nothing below it but the portal beams' clear 15.24 m. (The first pass
put those beams at the girders' level, where a travelling trolley's cab and
ropes cut them; a sweep of every variant's trolley, cab, ropes and hoisted
spreader along the whole travel now finds nothing.) With the support beams
over the trolley, the raised boom must clear the waterside one, so the
hinge's distance waterside of the rail is derived (`Spec.hinge_y`): the
raised boom's landward edge clears that beam's waterside face by
`stow_clear` at the beam's underside. Its height stays 46 m (36.6 m for the
older crane); it stands 2.90 m out (the far crane 4.59 m, the older 2.43 m),
which shortens each boom a little and puts the stowed noses at 99.1, 97.5 and
76.4 m. Names follow the trade's glossary: the beams joining the waterside
and landside legs at the 15.24 m clearance are the **portal beams**, the
beams over each rail line that the girders hang from are the **girder
support beams**; there are no base-level sill beams.

Everything the tool makes carries `kyt_gantry_crane`, so a rerun removes and
rebuilds its own work and keeps anything of hers; `export` holding anything
untagged refuses without `--replace`. Into the locked `reference` collection
go the two crane rails of each gauge as lines (the rails are the quay's, not
the crane's), the bogie footprint and plan outlines, and a 1.7 m figure.

**Frame** (shore equipment, the boats brief): real metres, Z up, z = 0 the
quay top and the rail head the wheels stand on (crane rails are set flush in
the quay). The origin is the footprint's centre: midway between the rails and
between the legs, so the crane is placed by its rails. +Y faces the water: the
waterside rail is at +Y, the boom reaches out over +Y, the backreach and the
machinery house are at -Y. X runs along the quay, the way the crane travels.
The glTF export turns +Y into Godot's -Z.

**Read** (the brief's shared port numbers, checked against real cranes): 100 ft
(30.48 m) gauge, 50' (15.24 m) clear under the portal beams and about 86'6"
(26.4 m) over the bumpers, from the Samsung post-Panamax cranes at Port
Everglades (porteverglades.net, "Cranes & Services"; their 145'6" outreach and
155' lift are a little shorter and taller than the brief's); the trade's
12-18 m portal clearance; outreach 50 m, lift 38 m, backreach 18 m, hinge
46 m, apex 72 m and an 80 degree stow from the brief. The older crane: 50 ft
gauge, 100 ft (30.5 m) lift and 75 ft (22.9 m) backreach from the Paceco
Portainer at Port Everglades (whose boom stows at 270 ft), outreach about
36 m and apex about 55 m from the brief.

**Chosen** (no source): every other number below, each marked "chosen".

**Contract** (scenery block-out): closed shells, silhouette first, no
interiors. The boom and the girders are **solid tapered box girders, no
cut-outs**: twin girders 9 m apart that the trolley rides on, the boom
tapering toward its nose, as the box-girder cranes of the late 1990s were;
the lattice read comes from the legs, the A-frame, the stays and the gaps
between them. The cab's windows are **dark slabs set proud** of the cab, not
holes. Every part is `kyt_collision = none` this pass. No two shapes share a
plane: a part that meets another laps into it or stands proud of it; the
stays of one crane differ in width by 4 cm so their faces never coincide where
they meet in the apex. Stand-in materials by surface, `gantry_crane_<surface>`;
no company names, logos or lettering.

**How it is built.** Each crane is about thirty parts. The gantry: a bogie
set under each leg (an equaliser beam, two bogie frames, four wheels on the
rail head), four legs tapering upward past the trolley, a portal beam each
side joining the waterside and landside legs at the portal clearance, a
diagonal brace each side above it, a girder support beam over each rail line
joining the legs' heads over the trolley, and the girder hangers (one object)
from those beams down to the girders' outer webs. The girders (one object:
both boxes, the trolley rails, the backstays' lugs, a tail tie) hang from
the tail to just past the hinge; the boom (one object,
origin on the hinge axis: both tapered boxes, rails, the forestays' lugs, pin
stubs, a nose tie) runs from the hinge out over the water. The A-frame (one
object): on each side a front strut from the waterside support beam and a
back strut from the landside one meeting at the apex, a crossbar between
them, cross ties between the sides, the apex beam on top. Backstays to the
girders' lugs and two forestay pairs to the boom's, one mesh per pair. The
machinery house on the girders' tail; the trolley on its rails, the operator
cab hanging under it through the gap between the girders; the spreader on
four hoist-rope falls. Nothing spans the gap between the girders or the boom
but the tail tie and the nose tie, beyond the trolley's travel, because the
cab and the ropes run down through it.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TAG = "kyt_gantry_crane"
PROP = "gantry_crane"
VARIANTS = ("working", "stowed", "panamax_older", "working_far", "stowed_far",
            "working_white_red", "working_grey_blue", "panamax_older_stowed", "working_spreader_down",
            "working_trolley_backreach", "working_trolley_portal", "working_lattice", "working_single_girder",
            "working_house_under", "working_details")

# --- the post-Panamax crane (working, stowed) ----------------------------------
NEW = dict(
    gauge=30.48,              # read: 100 ft between the waterside and landside rails
    outreach=50.0,            # read (brief): waterside rail to the spreader's farthest centre, 17 boxes across
    lift=38.0,                # read (brief): the spreader's underside at full hoist, over the rail
    backreach=18.0,           # read (brief): landside rail to the spreader's farthest centre landward
    hinge_z=46.0,             # read (brief): the boom hinge's axis
    apex_top=72.0,            # read (brief): the top of the apex beam
    portal_clear=15.24,       # read: 50 ft under the portal beams (Port Everglades' "portal clearance 50'")
    stow_deg=80.0,            # read (brief): the boom raised for a ship to berth
    leg_clear=18.3,           # chosen: 60 ft clear between the legs along the quay, room for a hatch cover
    leg_foot=2.6,             # chosen: a leg's square box section at its foot
    leg_head=2.0,             # chosen: and at its head, the legs taper upward
    girder_depth=4.0,         # chosen: the fixed girder's depth, the hinge at its mid-depth
    girder_x=4.5,             # chosen: the twin girders' centres off the middle (a 9 m trolley gauge)
    girder_hw=0.8,            # chosen: half a girder's width (1.6 m box)
    boom_hw=0.75,             # chosen: half a boom girder's width, 5 cm narrower than the girder's
    boom_top_drop=0.1,        # chosen: the boom's top under the girder's, so the two never share a plane
    boom_root_depth=3.8,      # chosen: the boom's depth at the hinge
    boom_tip_depth=2.0,       # chosen: and at its nose
    boom_nose=6.5,            # chosen: the boom's nose past the spreader's farthest centre (trolley and cab fit)
    boom_root_back=0.6,       # chosen: the boom's root reaches this far behind the hinge, inside the girder's end
    girder_past_hinge=0.4,    # chosen: the girder runs this far past the hinge, round the boom's root
    hinge_out_min=1.8,        # chosen: the hinge at least this far waterside of the waterside rail; further
                              # where the raised boom needs it to clear the waterside girder support beam
    stow_clear=0.3,           # chosen: by this much (Spec.hinge_y)
    apex_back=2.24,           # chosen: the apex this far landward of the waterside rail (front strut near upright)
    apex_hx=6.8,              # chosen: half the apex beam's length across the crane
    apex_hy=1.3,              # chosen: half its depth along Y
    apex_depth=2.6,           # chosen: its height
    apex_node_drop=1.4,       # chosen: where the struts and stays meet, under the apex top
    strut=1.6,                # chosen: the A-frame struts' box section
    a_tie_frac=0.4,           # chosen: the A's crossbar, this far up from the girder top to the apex
    a_tie_w=1.0,              # chosen: the crossbars' width
    a_tie_side_h=0.9,         # chosen: the side crossbars' depth (front strut to back strut)
    a_tie_cross_h=0.7,        # chosen: the cross ties' depth (side to side), unlike the side ones'
    stay_out=0.3,             # chosen: the stays' plane this far outside the girder's outer face (on lugs)
    stay_hw=(0.345, 0.325, 0.305),   # chosen: half widths of the backstay, mid forestay, tip forestay
    forestay_mid=0.45,        # chosen: the mid forestay's lug, this share of the boom out from the hinge
    forestay_tip_in=7.0,      # chosen: the tip forestay's lug, this far in from the boom's nose
    girder_lug_out=0.38,      # chosen: a backstay's lug reaches this far past the stay's plane
    girder_lug_hl=0.9,        # chosen: half its length along the girder
    girder_lug_hz=1.0,        # chosen: half its height about the stay's foot
    boom_lug_out=0.37,        # chosen: a forestay's lug reaches this far past the stay's plane
    boom_lug_hl=1.0,          # chosen: half its length along the boom
    boom_lug_below=1.0,       # chosen: how far it reaches down the boom's web from the boom's top
    boom_lug_above=0.7,       # chosen: and up above the boom's top
    forestay_foot_lift=0.1,   # chosen: a forestay's foot over the boom's top, inside its lug
    backstay_foot_lift=0.3,   # chosen: a backstay's foot over the girder's top, inside its lug
    pin_r=0.5,                # chosen: half the boom's hinge pin stubs' section
    pin_out=0.4,              # chosen: how far they stand out of the boom's web
    support_clear=0.7,        # chosen: the girder support beams' underside this far over the trolley's
                              # top: the legs rise past the trolley to them (the O-frame) and the girders
                              # hang from them, so nothing crosses the trolley's path
    support_depth=2.9,        # chosen: their height
    support_beam_hy=1.4,      # chosen: half their depth along Y, round the legs' heads
    hanger_out=0.75,          # chosen: the girder hangers stand this far out from the girders' outer webs,
                              # outside the trolley, from the support beams down to the girders
    hanger_hy=0.6,            # chosen: half a hanger's length along the girder
    portal_beam_depth=2.0,    # chosen: the portal beams' height (their underside is the portal clearance)
    portal_beam_hx=1.0,       # chosen: half their width
    portal_beam_in=0.9,       # chosen: their ends stop this far short of the rail line, inside the legs
    brace_w=1.4,              # chosen: the portal's diagonal brace, width across the crane
    brace_h=1.0,              # chosen: and depth
    eq_hl=3.05,               # chosen: half the equaliser beam under a leg, so 27.0 m over the bogies
    eq_hy=1.4,                # chosen: half its width across the rail, under the whole leg foot
    eq_z0=1.15,               # chosen: its underside
    eq_top=2.6,               # chosen: its top, where the leg stands
    bogie_dx=1.65,            # chosen: two bogies under each equaliser, this far either side of the leg
    bogie_hl=1.25,            # chosen: half a bogie frame's length
    bogie_hy=0.55,            # chosen: half its width
    bogie_z0=0.55,            # chosen: its underside; the wheels show below it
    wheel_r=0.45,             # chosen: a 0.9 m gantry wheel, two per bogie, sixteen per crane
    wheel_dx=0.7,             # chosen: each wheel this far from its bogie's centre
    wheel_hy=0.14,            # chosen: half a wheel's tread width
    rail_h=0.15,              # chosen: the trolley rails on the girders, their height
    rail_hw=0.10,             # chosen: half their width on the girders
    boom_rail_hw=0.09,        # chosen: half their width on the boom, unlike the girder's
    trolley_hx=5.0,           # chosen: half the trolley's width, inside the stays' lugs
    trolley_hl=4.0,           # chosen: half its length along the girders
    trolley_h=2.65,           # chosen: its height over the rails
    rope_dy=-1.0,             # chosen: the spreader hangs this far landward of the trolley's centre
    rope_x=1.2,               # chosen: the hoist ropes' falls, this far either side of the middle
    rope_y=0.6,               # chosen: and either side of the spreader's centre
    rope_w=0.16,              # chosen: one fall's square stand-in section
    cab_hx=1.3,               # chosen: half the operator cab's width
    cab_y=(1.0, 4.0),         # chosen: the cab under the trolley's waterside end, from its centre
    cab_h=2.8,                # chosen: the cab's height
    cab_gap=0.6,              # chosen: the cab's roof this far under the girder
    spreader=(12.192, 2.438, 0.6),   # read: a 40 ft ISO box's length and width (brief); depth chosen
    headblock=(3.4, 2.0, 1.0),       # chosen: the headblock over the spreader
    house_hx=6.2,             # chosen: half the machinery house's width across the girders
    house_len=12.0,           # chosen: its length along them
    house_h=6.5,              # chosen: its height over the girders
    house_gap=0.76,           # chosen: its front this far behind the trolley at full backreach
    tail_past_house=0.6,      # chosen: the girders' tail past the house's back
    backstay_foot_in=1.4,     # chosen: the backstays' feet this far waterside of the house
    work_out=30.0,            # chosen: working, the spreader's centre this far out from the waterside rail
    work_z=20.0,              # chosen: working, the spreader's underside at mid height
    park_below=1.0,           # chosen: stowed, the spreader parked this far under full hoist
)

# --- the older Panamax-era crane (panamax_older): what differs ---------------------
OLD = dict(
    NEW,
    gauge=15.24,              # read (brief): 50 ft gauge, the Panamax-era standard
    outreach=36.6,            # chosen: 120 ft, 13 boxes across a Panamax ship (brief "about 36 m")
    lift=30.5,                # read: 100 ft, the Paceco at Port Everglades
    backreach=22.9,           # read: 75 ft, the same Paceco (a narrow gauge wants a long backreach)
    hinge_z=36.6,             # chosen: 6 m over the lift, as the new crane's 8 m scaled down
    apex_top=55.0,            # read (brief): about 55 m
    portal_clear=12.2,        # chosen: 40 ft under the portal beams, for chassis and top-picks
    stow_deg=80.0,            # chosen: as the new crane (not built stowed this pass)
    leg_foot=2.3,             # chosen
    leg_head=1.8,             # chosen
    girder_depth=3.2,         # chosen
    girder_x=4.0,             # chosen: an 8 m trolley gauge
    girder_hw=0.7,            # chosen
    boom_hw=0.66,             # chosen
    boom_root_depth=3.0,      # chosen
    boom_tip_depth=1.7,       # chosen
    boom_nose=6.0,            # chosen
    hinge_out_min=1.5,        # chosen
    apex_back=2.0,            # chosen
    apex_hx=6.0,              # chosen
    apex_hy=1.1,              # chosen
    apex_depth=2.2,           # chosen
    apex_node_drop=1.2,       # chosen
    strut=1.4,                # chosen
    stay_hw=(0.295, 0.275, 0.255),   # chosen
    forestay_tip_in=6.0,      # chosen
    support_beam_hy=1.2,      # chosen
    portal_beam_depth=1.8,    # chosen
    portal_beam_hx=0.9,       # chosen
    brace_w=1.2,              # chosen
    brace_h=0.9,              # chosen
    trolley_hx=4.4,           # chosen
    trolley_hl=3.5,           # chosen
    trolley_h=2.3,            # chosen
    house_hx=5.6,             # chosen
    house_len=10.0,           # chosen
    house_h=5.5,              # chosen
    work_out=22.0,            # chosen
    work_z=15.0,              # chosen
)

# --- the far crane (working_far, stowed_far): what differs ---------------------------
# Christina, 2026-10-03, on fattening the crane for distance: "yes we like
# cartoony proportions so this works". The same crane at the same size and
# clearances (gauge, outreach, lift, backreach, hinge height, apex, 15.24 m
# under the portal beams, 27.0 m over the bogies, tail and nose where they
# were; the hinge stands further out, where the fat raised boom clears the
# fat waterside support beam), its
# members fattened so the silhouette survives 2 km in the player's view. The
# target: at 2 km, 70 degrees vertical at 1080 lines, a pixel is
# 2 * 2000 * tan(35) / 1080 = 2.593 m; legs at least 2 px (5.19 m), stays at
# least 1 px (2.59 m).
FAR_PX_M = 2 * 2000.0 * math.tan(math.radians(35.0)) / 1080   # metres a pixel covers at 2 km
FAR = dict(
    NEW,
    leg_foot=5.9,             # chosen: 2.3 px at 2 km
    leg_head=5.3,             # chosen: 2.04 px at 2 km, the narrowest a leg gets
    leg_clear=NEW["leg_clear"] + NEW["leg_foot"] - 5.9,   # derived: the legs' centres stay put, so
                              # the bogie footprint does; 15.0 m clear between the feet, 15.6 m at the heads
    girder_depth=5.0,         # chosen: 1.9 px from the side; the hinge stays at its mid-depth
    girder_hw=1.4,            # chosen: 2.8 m boxes, 1.1 px each from the front
    boom_hw=1.35,             # chosen: 5 cm narrower than the girder, as before
    boom_root_depth=4.8,      # chosen: 1.9 px at the hinge
    boom_tip_depth=2.8,       # chosen: 1.1 px at the nose
    apex_hx=9.9,              # chosen: the apex beam holds the fat stays' and struts' ends
    apex_hy=2.4,              # chosen
    apex_depth=4.6,           # chosen: its top stays at 72 m
    apex_node_drop=2.3,       # chosen: mid-depth of the apex beam
    strut=3.0,                # chosen: 1.16 px
    a_tie_w=2.8,              # chosen
    a_tie_side_h=2.75,        # chosen: 1.06 px
    a_tie_cross_h=2.65,       # chosen: 1.02 px
    stay_out=1.55,            # chosen: the fat stays clear the trolley as the thin ones did
    stay_hw=(1.40, 1.38, 1.36),      # chosen: 2.80, 2.76 and 2.72 m, 1.08, 1.06 and 1.05 px
    girder_lug_out=1.48,      # chosen: the lugs grow to hold the fat stays' feet
    girder_lug_hl=2.2,        # chosen
    girder_lug_hz=2.0,        # chosen
    boom_lug_out=1.47,        # chosen
    boom_lug_hl=2.0,          # chosen
    boom_lug_below=1.65,      # chosen
    boom_lug_above=2.0,       # chosen
    forestay_foot_lift=0.3,   # chosen
    backstay_foot_in=2.4,     # chosen: the backstays' lugs stay clear of the house's front
    support_beam_hy=2.8,      # chosen: just round the fat legs' heads; 2.9 m deep (1.12 px), as before
    hanger_out=1.6,           # chosen: chunkier hangers, still inside the legs' heads
    hanger_hy=1.35,           # chosen: 2.7 m along the girder, 1.04 px from the side
    portal_beam_depth=3.4,    # chosen: 1.3 px; its underside stays at 15.24 m
    portal_beam_hx=2.2,       # chosen
    portal_beam_in=2.0,       # chosen: the ends still inside the fat legs
    brace_w=2.8,              # chosen
    brace_h=2.7,              # chosen: 1.04 px
    eq_top=3.0,               # chosen: a taller equaliser under the fat leg
    eq_hy=3.05,               # chosen: wide enough across the rail for the leg's foot
    bogie_hy=0.9,             # chosen
    wheel_r=0.5,              # chosen: a chunkier 1.0 m wheel, still on the rail head
    wheel_hy=0.25,            # chosen
    trolley_hx=5.6,           # chosen: chunkier, still inside the stays' lugs
    trolley_h=3.4,            # chosen
    rope_w=0.4,               # chosen
    cab_hx=1.8,               # chosen
    cab_h=3.0,                # chosen
    spreader=(12.192, 2.438, 1.0),   # read: 40 ft box length and width; depth chosen, chunkier
    headblock=(4.0, 2.4, 1.2),       # chosen
    house_hx=6.8,             # chosen
    house_h=7.5,              # chosen
    pin_r=1.0,                # chosen
    pin_out=0.6,              # chosen
)

# --- the further variants (2026-10-03, Christina: "build all the offered
# variants"): liveries, the older crane stowed, working poses, a lattice
# truss, a single box girder, the house hung under, the close-up details.
# Each is the working crane's meshes linked, but for what it changes.
POSES = dict(
    deck_z=4.0,               # chosen: working_spreader_down, the spreader set on a laden ship's
                              # hatch covers about 4 m over the quay
    chassis_box_top=4.0,      # chosen: working_trolley_backreach, the spreader on a 40 ft box on a
                              # road chassis (about 1.4 m deck + 2.59 m box)
    portal_spreader_y=0.0,    # chosen: working_trolley_portal, the spreader's centre midway between
                              # the rails, hoisted as when stowed
)
LATTICE = dict(
    girder_panels=13,         # chosen: about 5.2 m panels along each girder truss
    boom_panels=11,           # chosen: about 5.0 m panels along each boom truss
    chord_h=0.6,              # chosen: the chords' depth; their width is the box girder's
    girder_web=(0.55, 0.60, 0.62),   # chosen: half widths across of the girder trusses' verticals and
                              # their two sets of diagonals, all different so no two share a plane
    boom_web=(0.53, 0.57, 0.59),     # chosen: and the boom trusses', unlike the girders'
    web_h=0.45,               # chosen: the web members' depth
    vertical_hl=0.22,         # chosen: half a vertical's length along the truss
)
SINGLE = dict(
    NEW,
    girder_x=0.0,             # chosen: one box girder on the middle, the "monobox" boom
    girder_hw=1.8,            # chosen: 3.6 m wide
    boom_hw=1.75,             # chosen: 5 cm narrower than the girder, as before
    stay_out=-0.8,            # chosen: the stays' plane 1.0 m off the middle, so their feet land on the
                              # box's top, where the trolley (which wraps round under the top) never goes
    forestay_foot_lift=0.4,   # chosen: the stays' feet over the top, inside lugs on it
    backstay_foot_lift=0.4,   # chosen
)
SINGLE_LUG = (0.45, 0.1, 0.9)   # chosen: a top lug's half width about the stay's plane, how far it sinks
                                # into the box's top, and how far it stands over it
SINGLE_LEDGE = (0.3, 1.15, 0.95)   # chosen: the trolley's rails as ledges on the box's sides: how far they
                                # stand out, and their underside and top under the box's top
SINGLE_TROLLEY = dict(
    side_in=0.05,             # chosen: the trolley's side frames this far off the box's sides
    side_w=0.9,               # chosen: and this wide
    top_under=0.8,            # chosen: their tops this far under the box's top
    under=0.6,                # chosen: the frame under the box this far below its underside
    under_h=1.0,              # chosen: and this deep
)
SINGLE_HANGER = (0.9, 0.6)    # chosen: the box hangs from each girder support beam on a hanger this wide across
                              # (half) and long along (half), standing on its top
STAIR = dict(
    width=2.4,                # chosen: the stair tower on the landside leg at +x, across
    depth=3.0,                # chosen: and out from the leg's landside face
    face_in=0.96,             # chosen: its leg-side face this far landside of the rail line, inside
                              # the tapering leg all the way up
    z0=3.2,                   # chosen: it starts over the bogies; a ladder climbs to it from the quay
    landing_every=8.0,        # chosen: a landing slab on its outer face every 8 m
    ladder_w=0.6,             # chosen
)
LIGHT = 0.6                   # chosen: an aircraft warning light, a 0.6 m box 0.5 m tall, two on the
LIGHT_H = 0.5                 # apex beam's top and two on the boom's nose


class Spec:
    """One crane's numbers, the table above plus what follows from them."""

    def __init__(self, name, table):
        self.name = name
        for key, value in table.items():
            setattr(self, key, value)
        self.ws_y = self.gauge / 2                      # the waterside rail
        self.ls_y = -self.gauge / 2                     # the landside rail
        self.gt = self.hinge_z + self.girder_depth / 2  # the girders' top
        self.gb = self.hinge_z - self.girder_depth / 2  # and underside
        self.rail_top = self.gt + self.rail_h           # what the trolley stands on
        # the O-frame: the girder support beams over the trolley's top
        self.support_z0 = self.rail_top + self.trolley_h + self.support_clear
        self.support_z1 = self.support_z0 + self.support_depth
        self.bt = self.gt - self.boom_top_drop - self.hinge_z   # the boom's top, hinge-local
        self.boom_rail_top = self.rail_top - 0.01 - self.hinge_z
        # the hinge: where the raised boom's landward edge (its rails' top),
        # at the support beam's underside, clears the waterside support beam
        # by stow_clear, or hinge_out_min if that is further
        th = math.radians(self.stow_deg)
        u = (self.support_z0 - self.hinge_z - self.boom_rail_top * math.cos(th)) / math.sin(th)
        need = self.support_beam_hy + self.stow_clear - u * math.cos(th) + self.boom_rail_top * math.sin(th)
        self.hinge_out = max(self.hinge_out_min, need)
        self.hinge_y = self.ws_y + self.hinge_out
        self.boom_tip_y = self.ws_y + self.outreach + self.boom_nose
        self.boom_len = self.boom_tip_y - self.hinge_y
        self.leg_x = self.leg_clear / 2 + self.leg_foot / 2
        self.stay_x = self.girder_x + self.girder_hw + self.stay_out
        self.apex_y = self.ws_y - self.apex_back
        self.apex_node_z = self.apex_top - self.apex_node_drop
        self.strut_foot_z = (self.support_z0 + self.support_z1) / 2   # inside the girder support beam
        self.forestay_u = (self.forestay_mid * self.boom_len, self.boom_len - self.forestay_tip_in)
        # the trolley's stations: the spreader hangs rope_dy from its centre
        self.trolley_back_y = self.ls_y - self.backreach - self.rope_dy
        self.house_y1 = self.trolley_back_y - self.trolley_hl - self.house_gap
        self.house_y0 = self.house_y1 - self.house_len
        self.tail_y = self.house_y0 - self.tail_past_house
        self.backstay_foot = (self.house_y1 + self.backstay_foot_in, self.gt + self.backstay_foot_lift)
        self.work_trolley_y = self.ws_y + self.work_out - self.rope_dy
        self.park_z = self.lift - self.park_below
        self.overall_x = 2 * (self.leg_x + self.eq_hl)


def srgb(hex6):
    """A CSS colour as Blender's linear RGBA."""
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(chan(int(hex6[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLOURS = {
    f"{PROP}_steel": srgb("b8322a"),          # crane red: legs, beams, girders, boom, A-frame, stays
    f"{PROP}_house": srgb("ece9e2"),          # off-white: machinery house, trolley, cab
    f"{PROP}_glass": srgb("1d2731"),          # the cab's dark window slabs
    f"{PROP}_running_gear": srgb("3b3d40"),   # bogies, wheels, trolley rails, hoist ropes
    f"{PROP}_spreader": srgb("e2a91d"),       # the spreader and its headblock
    f"{PROP}_older_steel": srgb("5d7590"),    # the older crane's grey-blue
    f"{PROP}_older_house": srgb("cfd3d6"),    # and its pale grey house, trolley, cab
    # the liveries (2026-10-03), each on its own materials, on the same meshes
    f"{PROP}_livery_white": srgb("efefeb"),   # working_white_red: white legs, beams, girders, boom
    f"{PROP}_livery_red": srgb("c8282a"),     # and red A-frame and stays
    f"{PROP}_livery_light_grey": srgb("c4c8cb"),   # and a light grey house, trolley and cab
    f"{PROP}_livery_grey": srgb("8e959b"),    # working_grey_blue: grey legs, beams and girders
    f"{PROP}_livery_blue": srgb("2f5f9e"),    # and blue A-frame, stays and boom
    f"{PROP}_livery_pale": srgb("e6e8ea"),    # and a pale house, trolley and cab
    f"{PROP}_warning_light": srgb("ff2a1a"),  # working_details: the aircraft warning lights
}


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


def mats(older=False):
    tag = "older_" if older else ""
    return {
        "steel": material(f"{PROP}_{tag}steel"),
        "house": material(f"{PROP}_{tag}house"),
        "glass": material(f"{PROP}_glass"),
        "gear": material(f"{PROP}_running_gear"),
        "spreader": material(f"{PROP}_spreader"),
    }


# --- building blocks -----------------------------------------------------------

def hexa(bm, pts, mat=0):
    """Six faces over eight corners: one end's four in order, then the
    other end's four in the same order."""
    v = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([v[i] for i in f]).material_index = mat


def add_box(bm, x0, x1, y0, y1, z0, z1, mat=0):
    """An axis-aligned box, 12 triangles."""
    assert x1 > x0 and y1 > y0 and z1 > z0, (x0, x1, y0, y1, z0, z1)
    hexa(bm, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], mat)


def add_bar(bm, p, q, w, h, mat=0):
    """A box-section bar from p to q, `w` wide across (horizontal, square to
    the bar) and `h` deep. A bar in a plane of constant x has its width along
    X, so every stay in one plane has its side faces in planes x = const."""
    p, q = Vector(p), Vector(q)
    d = (q - p).normalized()
    a = d.cross(Vector((0.0, 0.0, 1.0)))
    if a.length < 1e-6:
        a = Vector((1.0, 0.0, 0.0))
    a.normalize()
    b = a.cross(d).normalized()
    ring = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    hexa(bm, [p + a * (sa * w / 2) + b * (sb * h / 2) for sa, sb in ring] +
             [q + a * (sa * w / 2) + b * (sb * h / 2) for sa, sb in ring], mat)


def add_frustum(bm, z0, z1, h0, h1, mat=0):
    """A square column tapering from half-width h0 at z0 to h1 at z1."""
    hexa(bm, [(-h0, -h0, z0), (h0, -h0, z0), (h0, h0, z0), (-h0, h0, z0),
              (-h1, -h1, z1), (h1, -h1, z1), (h1, h1, z1), (-h1, h1, z1)], mat)


def add_prism_y(bm, poly, y0, y1, mat=0):
    """A polygon in (x, z) extruded along Y (a wheel on an axle across the rail)."""
    near = [bm.verts.new((a, y0, b)) for a, b in poly]
    far = [bm.verts.new((a, y1, b)) for a, b in poly]
    bm.faces.new(near).material_index = mat
    bm.faces.new(list(reversed(far))).material_index = mat
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i])).material_index = mat


def finish(name, bm, coll, materials, variant, mesh_name=None, location=(0.0, 0.0, 0.0)):
    """A bmesh into a tagged object in `coll` with its material slots."""
    mesh = bpy.data.meshes.new(mesh_name or f"{PROP}_{name}")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    for m in materials:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    obj[TAG] = True
    obj["kyt_unwrap"] = "facets"
    obj["kyt_collision"] = "none"
    obj["kyt_variant"] = variant
    obj.location = location
    coll.objects.link(obj)
    return obj


def instance(src, name, coll, variant, location=None, rotation=None):
    """A linked copy: a new object on the same mesh, so reshaping one
    reshapes every copy."""
    obj = bpy.data.objects.new(name, src.data)
    for key in (TAG, "kyt_unwrap", "kyt_collision"):
        obj[key] = src[key]
    obj["kyt_variant"] = variant
    obj.location = src.location if location is None else location
    obj.rotation_euler = src.rotation_euler if rotation is None else rotation
    coll.objects.link(obj)
    return obj


# --- the shared kit: one gantry bogie set and one spreader for every crane -------------

def bogie_set_bm(s):
    """One corner's gantry travel: an equaliser beam under the leg, two bogie
    frames under it, two 0.9 m wheels in each standing on the rail head at
    z = 0 (an octagon with a flat at the bottom). Origin at the leg's centre
    on the rail line."""
    bm = bmesh.new()
    add_box(bm, -s.eq_hl, s.eq_hl, -s.eq_hy, s.eq_hy, s.eq_z0, s.eq_top)
    cz = s.wheel_r * math.cos(math.pi / 8)
    for c in (-s.bogie_dx, s.bogie_dx):
        add_box(bm, c - s.bogie_hl, c + s.bogie_hl, -s.bogie_hy, s.bogie_hy, s.bogie_z0, s.eq_z0 + 0.05)
        for wx in (c - s.wheel_dx, c + s.wheel_dx):
            poly = [(wx + s.wheel_r * math.cos(t), cz + s.wheel_r * math.sin(t))
                    for t in (-math.pi / 2 + math.pi / 8 + k * math.pi / 4 for k in range(8))]
            add_prism_y(bm, poly, -s.wheel_hy, s.wheel_hy)
    return bm


def spreader_bm(s):
    """A 40 ft spreader with its headblock; origin at its underside's centre.
    Its long side runs along X, as a box on a ship moored along the quay."""
    bm = bmesh.new()
    sl, sw, sd = s.spreader
    hl, hw, hd = s.headblock
    add_box(bm, -sl / 2, sl / 2, -sw / 2, sw / 2, 0.0, sd)
    add_box(bm, -hl / 2, hl / 2, -hw / 2, hw / 2, sd - 0.02, sd + hd)
    return bm


# --- the crane ------------------------------------------------------------------

def boom_local(s, u, z, deg):
    """A point on the boom, given along it (u, from the hinge) and over the
    hinge (z), with the boom raised `deg` degrees: its (y, z) in the world."""
    th = math.radians(deg)
    return (s.hinge_y + u * math.cos(th) - z * math.sin(th),
            s.hinge_z + u * math.sin(th) + z * math.cos(th))


def stay_bm(s, foot, hw):
    """A stay from the apex down to `foot` (y, z), its centreline at x = 0;
    placed at x = +-stay_x."""
    bm = bmesh.new()
    add_bar(bm, (0.0, s.apex_y, s.apex_node_z), (0.0, foot[0], foot[1]), 2 * hw, 2 * hw)
    return bm


def ropes_bm(s, spreader_y, spreader_z):
    """The hoist ropes' four falls, trolley to headblock, as thin square bars."""
    bm = bmesh.new()
    top = spreader_z + s.spreader[2] + s.headblock[2] - 0.02
    r = s.rope_w / 2
    for rx in (-s.rope_x, s.rope_x):
        for ry in (-s.rope_y, s.rope_y):
            add_box(bm, rx - r, rx + r, spreader_y + ry - r, spreader_y + ry + r, top, s.rail_top + 0.1)
    return bm


def a_frame_bm(s):
    """The A-frame: on each side a front strut from the waterside leg's head
    and a back strut from the landside leg's head meeting at the apex, a
    crossbar between them; cross ties between the sides' struts; the apex
    beam across the top, where the stays meet. The struts stand in the
    girder support beams; the crossbars are a_tie_frac of the way from
    there to the apex."""
    bm = bmesh.new()
    t = s.a_tie_frac
    xt = s.leg_x + (s.stay_x - s.leg_x) * t
    yf = s.ws_y + (s.apex_y - s.ws_y) * t
    yb = s.ls_y + (s.apex_y - s.ls_y) * t
    zt = s.strut_foot_z + (s.apex_node_z - s.strut_foot_z) * t
    for sx in (-1, 1):
        node = (sx * s.stay_x, s.apex_y, s.apex_node_z)
        add_bar(bm, (sx * s.leg_x, s.ws_y, s.strut_foot_z), node, s.strut, s.strut)
        add_bar(bm, (sx * s.leg_x, s.ls_y, s.strut_foot_z), node, s.strut, s.strut)
        add_bar(bm, (sx * xt, yb, zt), (sx * xt, yf, zt), s.a_tie_w, s.a_tie_side_h)
    for y in (yf, yb):
        add_bar(bm, (-xt, y, zt), (xt, y, zt), s.a_tie_w, s.a_tie_cross_h)
    add_box(bm, -s.apex_hx, s.apex_hx, s.apex_y - s.apex_hy, s.apex_y + s.apex_hy,
            s.apex_top - s.apex_depth, s.apex_top)
    return bm


def build_crane(s, coll, variant, prefix, m, kit):
    """One whole crane at the origin, working pose. Returns its parts by name."""
    parts = {}

    def put(name, bm, materials, location=(0.0, 0.0, 0.0)):
        parts[name] = finish(prefix + name, bm, coll, materials, variant,
                             mesh_name=f"{PROP}_{prefix}{name}", location=location)
        return parts[name]

    def copy(name, src, location):
        parts[name] = instance(src, prefix + name, coll, variant, location=location)
        return parts[name]

    corners = [("ws", s.ws_y, "px", 1), ("ws", s.ws_y, "nx", -1), ("ls", s.ls_y, "px", 1), ("ls", s.ls_y, "nx", -1)]

    # the gantry, an O-frame: four bogie sets (the kit's), four tapered legs
    # rising past the trolley, a portal beam each side joining the waterside
    # and landside legs at the portal clearance with a diagonal brace over
    # it, a girder support beam over each rail line joining the legs' heads
    # above the trolley's top, and the girders hung from those beams on
    # hangers outside the trolley, so nothing crosses the trolley's path
    for side, ry, end, sx in corners:
        loc = (sx * s.leg_x, ry, 0.0)
        copy(f"bogies_{side}_{end}", kit["bogies"], loc)
    leg = None
    for side, ry, end, sx in corners:
        loc = (sx * s.leg_x, ry, 0.0)
        if leg is None:
            bm = bmesh.new()
            add_frustum(bm, s.eq_top - 0.1, s.support_z0 + 1.0, s.leg_foot / 2, s.leg_head / 2)
            leg = put(f"leg_{side}_{end}", bm, [m["steel"]], loc)
        else:
            copy(f"leg_{side}_{end}", leg, loc)
    bm = bmesh.new()
    add_box(bm, -s.portal_beam_hx, s.portal_beam_hx, s.ls_y + s.portal_beam_in, s.ws_y - s.portal_beam_in,
            s.portal_clear, s.portal_clear + s.portal_beam_depth)
    portal = put("portal_beam_px", bm, [m["steel"]], (s.leg_x, 0.0, 0.0))
    copy("portal_beam_nx", portal, (-s.leg_x, 0.0, 0.0))
    # the diagonal rises from the waterside leg at the portal beam to the
    # landside leg at the girders, against the A-frame's back strut, so the
    # side reads as a truss
    bm = bmesh.new()
    add_bar(bm, (0.0, s.ws_y, s.portal_clear + 0.8 * s.portal_beam_depth), (0.0, s.ls_y, s.gb - 0.5),
            s.brace_w, s.brace_h)
    brace = put("portal_brace_px", bm, [m["steel"]], (s.leg_x, 0.0, 0.0))
    copy("portal_brace_nx", brace, (-s.leg_x, 0.0, 0.0))
    bm = bmesh.new()
    px = s.leg_x + s.leg_head / 2 + 0.4
    add_box(bm, -px, px, -s.support_beam_hy, s.support_beam_hy, s.support_z0, s.support_z1)
    support = put("girder_support_beam_ws", bm, [m["steel"]], (0.0, s.ws_y, 0.0))
    copy("girder_support_beam_ls", support, (0.0, s.ls_y, 0.0))
    bm = bmesh.new()
    for ry in (s.ws_y, s.ls_y):
        for sx in (-1, 1):
            hx = sorted((sx * (s.girder_x + s.girder_hw - 0.06), sx * (s.girder_x + s.girder_hw + s.hanger_out)))
            add_box(bm, hx[0], hx[1], ry - s.hanger_hy, ry + s.hanger_hy, s.gb + 1.0, s.support_z0 + 0.1)
    put("girder_hangers", bm, [m["steel"]])

    # the girders: twin boxes from the tail to just past the hinge, the
    # trolley's rails on them, the backstays' lugs on their outer webs, a tie
    # between them at the tail under the house
    bm = bmesh.new()
    gx, ghw = s.girder_x, s.girder_hw
    by, bz = s.backstay_foot
    for sx in (-1, 1):
        add_box(bm, sx * gx - ghw, sx * gx + ghw, s.tail_y, s.hinge_y + s.girder_past_hinge, s.gb, s.gt)
        add_box(bm, sx * gx - s.rail_hw, sx * gx + s.rail_hw, s.house_y1 + 0.2,
                s.hinge_y + s.girder_past_hinge - 0.05, s.gt - 0.02, s.rail_top, mat=1)
        lx = sorted((sx * (gx + ghw - 0.05), sx * (s.stay_x + s.girder_lug_out)))
        add_box(bm, lx[0], lx[1], by - s.girder_lug_hl, by + s.girder_lug_hl, bz - s.girder_lug_hz, bz + s.girder_lug_hz)
    add_box(bm, -(gx - ghw) - 0.05, (gx - ghw) + 0.05, s.tail_y + 0.2, s.tail_y + 1.4, s.gb + 0.4, s.gt - 0.4)
    put("girders", bm, [m["steel"], m["gear"]])

    # the boom, hinge-local: twin girders tapering on their undersides to the
    # nose, rails on top, the forestays' lugs on the outer webs, hinge pin
    # stubs through the girders' ends, a tie between the two at the nose
    # (nothing else spans the gap: the cab and the ropes run down through it)
    bm = bmesh.new()
    bhw, bt, L = s.boom_hw, s.bt, s.boom_len

    def depth(u):
        return s.boom_root_depth + (s.boom_tip_depth - s.boom_root_depth) * max(u, 0.0) / L

    u0 = -s.boom_root_back
    for sx in (-1, 1):
        x0, x1 = sx * gx - bhw, sx * gx + bhw
        hexa(bm, [(x0, u0, bt - depth(u0)), (x1, u0, bt - depth(u0)), (x1, u0, bt), (x0, u0, bt),
                  (x0, L, bt - depth(L)), (x1, L, bt - depth(L)), (x1, L, bt), (x0, L, bt)])
        add_box(bm, sx * gx - s.boom_rail_hw, sx * gx + s.boom_rail_hw, u0 + 0.1, L - 0.3,
                bt - 0.02, s.boom_rail_top, mat=1)
        lx = sorted((sx * (gx + bhw - 0.05), sx * (s.stay_x + s.boom_lug_out)))
        for u in s.forestay_u:
            add_box(bm, lx[0], lx[1], u - s.boom_lug_hl, u + s.boom_lug_hl, bt - s.boom_lug_below, bt + s.boom_lug_above)
        hx = sorted((sx * (gx + bhw - 0.08), sx * (gx + bhw + s.pin_out)))
        add_box(bm, hx[0], hx[1], -s.pin_r, s.pin_r, -s.pin_r, s.pin_r)
    add_box(bm, -(gx - bhw) - 0.05, (gx - bhw) + 0.05, L - 1.2, L - 0.2, bt - s.boom_tip_depth + 0.2, bt - 0.2)
    put("boom", bm, [m["steel"], m["gear"]], (0.0, s.hinge_y, s.hinge_z))

    put("a_frame", a_frame_bm(s), [m["steel"]])

    # the stays, one pair per mesh: the backstays to the girders' lugs, the
    # forestays to the boom's
    hw_back, hw_mid, hw_tip = s.stay_hw
    back = put("backstay_px", stay_bm(s, s.backstay_foot, hw_back), [m["steel"]], (s.stay_x, 0.0, 0.0))
    copy("backstay_nx", back, (-s.stay_x, 0.0, 0.0))
    build_forestays(s, parts, coll, variant, prefix, m, 0.0)

    # the machinery house on the girders' tail
    bm = bmesh.new()
    add_box(bm, -s.house_hx, s.house_hx, s.house_y0, s.house_y1, s.gt - 0.02, s.gt + s.house_h)
    put("machinery_house", bm, [m["house"]])

    # the trolley on its rails, the cab hanging under its waterside end
    # through the gap between the girders, the cab's dark window slabs set
    # proud (front, both sides and the floor the operator looks down through)
    ty = s.work_trolley_y
    bm = bmesh.new()
    add_box(bm, -s.trolley_hx, s.trolley_hx, -s.trolley_hl, s.trolley_hl, -0.02, s.trolley_h)
    put("trolley", bm, [m["house"]], (0.0, ty, s.rail_top))
    cz1 = s.gb - s.cab_gap - s.rail_top
    cz0 = cz1 - s.cab_h
    cy0, cy1 = s.cab_y
    bm = bmesh.new()
    add_box(bm, -s.cab_hx, s.cab_hx, cy0, cy1, cz0, cz1)
    add_box(bm, -0.5, 0.5, cy0 + 1.0, cy0 + 2.0, cz1 - 0.1, 0.1)
    put("cab", bm, [m["house"]], (0.0, ty, s.rail_top))
    bm = bmesh.new()
    add_box(bm, -s.cab_hx + 0.2, s.cab_hx - 0.2, cy1 - 0.02, cy1 + 0.03, cz0 + 0.6, cz1 - 0.3)
    for sx in (-1, 1):
        gxs = sorted((sx * (s.cab_hx - 0.02), sx * (s.cab_hx + 0.03)))
        add_box(bm, gxs[0], gxs[1], cy0 + 0.4, cy1 - 0.3, cz0 + 0.6, cz1 - 0.3)
    add_box(bm, -0.8, 0.8, cy0 + 0.6, cy1 - 0.4, cz0 - 0.03, cz0 + 0.02)
    put("cab_glass", bm, [m["glass"]], (0.0, ty, s.rail_top))

    # the spreader (the kit's) hanging at mid height, and the ropes to it
    sy = ty + s.rope_dy
    copy("spreader", kit["spreader"], (0.0, sy, s.work_z))
    put("hoist_ropes", ropes_bm(s, sy, s.work_z), [m["gear"]])
    return parts


def build_forestays(s, parts, coll, variant, prefix, m, deg):
    """The two forestay pairs from the apex to the boom's lugs, the boom
    raised `deg` degrees. Raised, they stand for the articulated forestays
    and the boom hoist holding the boom up off the apex; one mesh per pair."""
    hw = s.stay_hw[1:]
    for (tag, u), w in zip((("mid", s.forestay_u[0]), ("tip", s.forestay_u[1])), hw):
        foot = boom_local(s, u, s.bt + s.forestay_foot_lift, deg)
        name = f"forestay_{tag}_px"
        obj = finish(prefix + name, stay_bm(s, foot, w), coll, [m["steel"]], variant,
                     mesh_name=f"{PROP}_{prefix}{name}", location=(s.stay_x, 0.0, 0.0))
        parts[name] = obj
        parts[f"forestay_{tag}_nx"] = instance(obj, f"{prefix}forestay_{tag}_nx", coll, variant,
                                               location=(-s.stay_x, 0.0, 0.0))


def build_stowed(s, working, coll, m, variant="stowed", prefix="stowed_"):
    """The stowed crane: linked copies of every working part, the boom turned
    about its hinge, the trolley, cab and spreader moved to the back, its own
    forestays and ropes."""
    parts = {}
    moving = {"boom", "trolley", "cab", "cab_glass", "spreader", "hoist_ropes"}
    for name, src in working.items():
        if name.startswith("forestay_") or name in moving:
            continue
        parts[name] = instance(src, f"{prefix}{name}", coll, variant)
    parts["boom"] = instance(working["boom"], f"{prefix}boom", coll, variant,
                             rotation=(math.radians(s.stow_deg), 0.0, 0.0))
    ty = s.trolley_back_y
    for name in ("trolley", "cab", "cab_glass"):
        parts[name] = instance(working[name], f"{prefix}{name}", coll, variant, location=(0.0, ty, s.rail_top))
    sy = ty + s.rope_dy
    parts["spreader"] = instance(working["spreader"], f"{prefix}spreader", coll, variant, location=(0.0, sy, s.park_z))
    parts["hoist_ropes"] = finish(f"{prefix}hoist_ropes", ropes_bm(s, sy, s.park_z), coll, [m["gear"]], variant,
                                  mesh_name=f"{PROP}_{prefix}hoist_ropes")
    build_forestays(s, parts, coll, variant, prefix, m, s.stow_deg)
    return parts


# --- the further variants ---------------------------------------------------------

def link_all(working, coll, variant, prefix, skip=(), moves=None):
    """Linked copies of the working crane's parts but `skip`; `moves` gives
    some of them a new location."""
    parts = {}
    moves = moves or {}
    for name, src in working.items():
        if name in skip:
            continue
        parts[name] = instance(src, f"{prefix}{name}", coll, variant, location=moves.get(name))
    return parts


def build_livery(working, coll, variant, prefix, paint):
    """The working crane's own meshes in another livery: each part's material
    slots linked to the object, so the meshes stay shared and the colours
    are the variant's. `paint(part, material)` gives the livery's material
    or None to keep the mesh's."""
    parts = link_all(working, coll, variant, prefix)
    for name, obj in parts.items():
        for slot, mat in zip(obj.material_slots, obj.data.materials):
            new = paint(name, mat.name)
            if new is not None:
                slot.link = "OBJECT"
                slot.material = new
    return parts


def paint_white_red(part, mat):
    """White legs, beams, girders and boom; red A-frame and stays; a light
    grey house, trolley and cab."""
    if mat == f"{PROP}_steel":
        upper = part.startswith(("a_frame", "backstay", "forestay"))
        return material(f"{PROP}_livery_red" if upper else f"{PROP}_livery_white")
    if mat == f"{PROP}_house":
        return material(f"{PROP}_livery_light_grey")
    return None


def paint_grey_blue(part, mat):
    """Grey legs, beams and girders; blue A-frame, stays and boom; a pale
    house, trolley and cab."""
    if mat == f"{PROP}_steel":
        upper = part.startswith(("a_frame", "backstay", "forestay", "boom"))
        return material(f"{PROP}_livery_blue" if upper else f"{PROP}_livery_grey")
    if mat == f"{PROP}_house":
        return material(f"{PROP}_livery_pale")
    return None


def build_pose(s, working, coll, m, variant, prefix, trolley_y, spreader_z):
    """The working crane with its trolley, cab and spreader moved: linked
    copies throughout, its own hoist ropes."""
    sy = trolley_y + s.rope_dy
    moves = {n: (0.0, trolley_y, s.rail_top) for n in ("trolley", "cab", "cab_glass")}
    moves["spreader"] = (0.0, sy, spreader_z)
    parts = link_all(working, coll, variant, prefix, skip=("hoist_ropes",), moves=moves)
    parts["hoist_ropes"] = finish(f"{prefix}hoist_ropes", ropes_bm(s, sy, spreader_z), coll, [m["gear"]],
                                  variant, mesh_name=f"{PROP}_{prefix}hoist_ropes")
    return parts


def truss(bm, x, y0, y1, zb, zt, chord_hw, web, slanted, panels):
    """One truss in the plane x = const, from y0 to y1: a top chord with
    its top at zt, a bottom chord with its underside at zb(y) (a sloping bar
    where `slanted`), a vertical at every panel point and a diagonal in
    every panel, alternating, the two sets of diagonals a little different
    in width so neighbours never share a plane."""
    ch, wh, vhl = LATTICE["chord_h"], LATTICE["web_h"], LATTICE["vertical_hl"]
    v_hw, d_hw = web[0], web[1:]
    add_box(bm, x - chord_hw, x + chord_hw, y0, y1, zt - ch, zt)
    if slanted:
        add_bar(bm, (x, y0, zb(y0) + ch / 2), (x, y1, zb(y1) + ch / 2), 2 * chord_hw, ch)
    else:
        add_box(bm, x - chord_hw, x + chord_hw, y0, y1, zb(y0), zb(y0) + ch)
    step = (y1 - y0) / panels
    ys = [y0 + k * step for k in range(panels + 1)]
    for y in ys:
        a = min(max(y - vhl, y0 + 0.05), y1 - 0.05 - 2 * vhl)
        add_box(bm, x - v_hw, x + v_hw, a, a + 2 * vhl, zb(y) + ch - 0.05, zt - ch + 0.05)
    hi = zt - ch / 2
    for k in range(panels):
        # the end diagonals stop at the end verticals' middles, inside the chords
        ya, yb = max(ys[k], y0 + 0.05 + vhl), min(ys[k + 1], y1 - 0.05 - vhl)
        if k % 2 == 0:
            p, q = (x, ya, zb(ya) + ch / 2), (x, yb, hi)
        else:
            p, q = (x, ya, hi), (x, yb, zb(yb) + ch / 2)
        add_bar(bm, p, q, 2 * d_hw[k % 2], wh)


def build_lattice(s, working, coll, m):
    """The working crane with lattice-truss girders and boom, as many 1970s
    cranes had: each of the twin girders a truss of the box girder's width
    and depth, on the same rails, lugs and ties; everything else linked."""
    variant, prefix = "working_lattice", "lattice_"
    parts = link_all(working, coll, variant, prefix, skip=("girders", "boom"))
    gx, ghw = s.girder_x, s.girder_hw
    by, bz = s.backstay_foot
    bm = bmesh.new()
    for sx in (-1, 1):
        truss(bm, sx * gx, s.tail_y, s.hinge_y + s.girder_past_hinge, lambda y: s.gb, s.gt, ghw,
              LATTICE["girder_web"], False, LATTICE["girder_panels"])
        add_box(bm, sx * gx - s.rail_hw, sx * gx + s.rail_hw, s.house_y1 + 0.2,
                s.hinge_y + s.girder_past_hinge - 0.05, s.gt - 0.02, s.rail_top, mat=1)
        lx = sorted((sx * (gx + ghw - 0.05), sx * (s.stay_x + s.girder_lug_out)))
        add_box(bm, lx[0], lx[1], by - s.girder_lug_hl, by + s.girder_lug_hl, bz - s.girder_lug_hz, bz + s.girder_lug_hz)
    add_box(bm, -(gx - ghw) - 0.05, (gx - ghw) + 0.05, s.tail_y + 0.2, s.tail_y + 1.4, s.gb + 0.4, s.gt - 0.4)
    parts["girders"] = finish(f"{prefix}girders", bm, coll, [m["steel"], m["gear"]], variant,
                              mesh_name=f"{PROP}_{prefix}girders")
    bm = bmesh.new()
    bhw, bt, L = s.boom_hw, s.bt, s.boom_len

    def depth(u):
        return s.boom_root_depth + (s.boom_tip_depth - s.boom_root_depth) * max(u, 0.0) / L

    u0 = -s.boom_root_back
    for sx in (-1, 1):
        truss(bm, sx * gx, u0, L, lambda u: bt - depth(u), bt, bhw, LATTICE["boom_web"], True,
              LATTICE["boom_panels"])
        add_box(bm, sx * gx - s.boom_rail_hw, sx * gx + s.boom_rail_hw, u0 + 0.1, L - 0.3,
                bt - 0.02, s.boom_rail_top, mat=1)
        lx = sorted((sx * (gx + bhw - 0.05), sx * (s.stay_x + s.boom_lug_out)))
        for u in s.forestay_u:
            add_box(bm, lx[0], lx[1], u - s.boom_lug_hl, u + s.boom_lug_hl, bt - s.boom_lug_below, bt + s.boom_lug_above)
        hx = sorted((sx * (gx + bhw - 0.08), sx * (gx + bhw + s.pin_out)))
        add_box(bm, hx[0], hx[1], -s.pin_r, s.pin_r, -s.pin_r, s.pin_r)
    add_box(bm, -(gx - bhw) - 0.05, (gx - bhw) + 0.05, L - 1.2, L - 0.2, bt - s.boom_tip_depth + 0.2, bt - 0.2)
    parts["boom"] = finish(f"{prefix}boom", bm, coll, [m["steel"], m["gear"]], variant,
                           mesh_name=f"{PROP}_{prefix}boom", location=(0.0, s.hinge_y, s.hinge_z))
    return parts


def build_single(s, working, coll, m):
    """The working crane with a single box girder and boom (the "monobox"),
    on the same O-frame: one 3.6 m box hung on a hanger from each girder
    support beam; the trolley wraps round it on ledges along its sides,
    never above its top and with a frame under it, from which the ropes
    fall and the cab hangs; the stays land on lugs on the box's top, 1 m off
    the middle, where the trolley never goes, and the A-frame narrows to
    meet them. The bogies, legs, portal beams, braces, support beams, house
    and spreader are the working crane's, linked."""
    variant, prefix = "working_single_girder", "single_"
    keep = ("bogies_", "leg_", "portal_beam_", "portal_brace_", "girder_support_beam_", "machinery_house", "spreader")
    parts = link_all(working, coll, variant, prefix, skip=[n for n in working if not n.startswith(keep)])

    def put(name, bm, materials, location=(0.0, 0.0, 0.0)):
        parts[name] = finish(prefix + name, bm, coll, materials, variant,
                             mesh_name=f"{PROP}_{prefix}{name}", location=location)
        return parts[name]

    gw, bw = s.girder_hw, s.boom_hw
    lug_hw, lug_in, lug_up = SINGLE_LUG
    ledge_out, ledge_lo, ledge_hi = SINGLE_LEDGE
    by, bz = s.backstay_foot
    bm = bmesh.new()
    add_box(bm, -gw, gw, s.tail_y, s.hinge_y + s.girder_past_hinge, s.gb, s.gt)
    for sx in (-1, 1):
        lx = sorted((sx * (gw - 0.02), sx * (gw + ledge_out)))
        add_box(bm, lx[0], lx[1], s.house_y1 + 0.2, s.hinge_y + s.girder_past_hinge - 0.05,
                s.gt - ledge_lo, s.gt - ledge_hi, mat=1)
        add_box(bm, sx * s.stay_x - lug_hw, sx * s.stay_x + lug_hw, by - s.girder_lug_hl, by + s.girder_lug_hl,
                s.gt - lug_in, s.gt + lug_up)
    put("girders", bm, [m["steel"], m["gear"]])
    bm = bmesh.new()
    bt, L = s.bt, s.boom_len

    def depth(u):
        return s.boom_root_depth + (s.boom_tip_depth - s.boom_root_depth) * max(u, 0.0) / L

    u0 = -s.boom_root_back
    hexa(bm, [(-bw, u0, bt - depth(u0)), (bw, u0, bt - depth(u0)), (bw, u0, bt), (-bw, u0, bt),
              (-bw, L, bt - depth(L)), (bw, L, bt - depth(L)), (bw, L, bt), (-bw, L, bt)])
    for sx in (-1, 1):
        lx = sorted((sx * (bw - 0.02), sx * (bw + ledge_out)))
        # a centimetre under the girder's ledges, so the two never share a plane where they meet at the hinge
        add_box(bm, lx[0], lx[1], u0 + 0.1, L - 0.3, bt + 0.09 - ledge_lo, bt + 0.09 - ledge_hi, mat=1)
        for u in s.forestay_u:
            add_box(bm, sx * s.stay_x - lug_hw + 0.01, sx * s.stay_x + lug_hw - 0.01, u - s.boom_lug_hl,
                    u + s.boom_lug_hl, bt - lug_in, bt + lug_up)
    put("boom", bm, [m["steel"], m["gear"]], (0.0, s.hinge_y, s.hinge_z))
    # the box hangs from the girder support beams on a hanger standing on its top
    hx, hy = SINGLE_HANGER
    bm = bmesh.new()
    for ry in (s.ws_y, s.ls_y):
        add_box(bm, -hx, hx, ry - hy, ry + hy, s.gt - 0.05, s.support_z0 + 0.1)
    put("girder_hangers", bm, [m["steel"]])
    put("a_frame", a_frame_bm(s), [m["steel"]])
    back = put("backstay_px", stay_bm(s, s.backstay_foot, s.stay_hw[0]), [m["steel"]], (s.stay_x, 0.0, 0.0))
    parts["backstay_nx"] = instance(back, f"{prefix}backstay_nx", coll, variant, location=(-s.stay_x, 0.0, 0.0))
    build_forestays(s, parts, coll, variant, prefix, m, 0.0)
    # the trolley, trolley-local from the box's underside: side frames on the
    # ledges, a frame under the box joining them; the cab under its
    # waterside end; the ropes from its underside
    t = SINGLE_TROLLEY
    ty = s.work_trolley_y
    xi, xo = gw + t["side_in"], gw + t["side_in"] + t["side_w"]
    zb_ = -t["under"] - t["under_h"]
    bm = bmesh.new()
    for sx in (-1, 1):
        sxs = sorted((sx * xi, sx * xo))
        add_box(bm, sxs[0], sxs[1], -s.trolley_hl, s.trolley_hl, zb_ + 0.05, s.girder_depth - t["top_under"])
    add_box(bm, -xo + 0.03, xo - 0.03, -s.trolley_hl + 0.03, s.trolley_hl - 0.03, zb_, -t["under"])
    put("trolley", bm, [m["house"]], (0.0, ty, s.gb))
    cy0, cy1 = s.cab_y
    cz1 = zb_ + 0.02
    cz0 = cz1 - s.cab_h
    bm = bmesh.new()
    add_box(bm, -s.cab_hx, s.cab_hx, cy0, cy1, cz0, cz1)
    put("cab", bm, [m["house"]], (0.0, ty, s.gb))
    bm = bmesh.new()
    add_box(bm, -s.cab_hx + 0.2, s.cab_hx - 0.2, cy1 - 0.02, cy1 + 0.03, cz0 + 0.6, cz1 - 0.3)
    for sx in (-1, 1):
        gxs = sorted((sx * (s.cab_hx - 0.02), sx * (s.cab_hx + 0.03)))
        add_box(bm, gxs[0], gxs[1], cy0 + 0.4, cy1 - 0.3, cz0 + 0.6, cz1 - 0.3)
    add_box(bm, -0.8, 0.8, cy0 + 0.6, cy1 - 0.4, cz0 - 0.03, cz0 + 0.02)
    put("cab_glass", bm, [m["glass"]], (0.0, ty, s.gb))
    sy = ty + s.rope_dy
    parts["spreader"].location = (0.0, sy, s.work_z)
    bm = bmesh.new()
    top = s.gb + zb_ + 0.1
    r = s.rope_w / 2
    for rx in (-s.rope_x, s.rope_x):
        for ry in (-s.rope_y, s.rope_y):
            add_box(bm, rx - r, rx + r, sy + ry - r, sy + ry + r,
                    s.work_z + s.spreader[2] + s.headblock[2] - 0.02, top)
    put("hoist_ropes", bm, [m["gear"]])
    return parts


def build_house_under(s, working, coll, m):
    """The working crane with its machinery house hung under the girders'
    tail instead of standing on it; everything else linked."""
    variant, prefix = "working_house_under", "house_under_"
    parts = link_all(working, coll, variant, prefix, skip=("machinery_house",))
    bm = bmesh.new()
    add_box(bm, -s.house_hx, s.house_hx, s.house_y0, s.house_y1, s.gb - s.house_h, s.gb + 0.02)
    parts["machinery_house"] = finish(f"{prefix}machinery_house", bm, coll, [m["house"]], variant,
                                      mesh_name=f"{PROP}_{prefix}machinery_house")
    return parts


def build_details(s, working, coll, m):
    """The working crane with the close-up details: a stair tower on the
    landside leg at +x, landings on its outer face, a ladder up to it from
    the quay; aircraft warning lights on the apex beam's top and on the
    boom's nose (boom-local, so they ride with the boom)."""
    variant, prefix = "working_details", "details_"
    parts = link_all(working, coll, variant, prefix)
    st = STAIR
    x0, x1 = s.leg_x - st["width"] / 2, s.leg_x + st["width"] / 2
    y1 = s.ls_y - st["face_in"]
    y0 = y1 - st["depth"]
    top = s.gb + 1.2
    bm = bmesh.new()
    add_box(bm, x0, x1, y0, y1, st["z0"], top)
    z = st["landing_every"]
    while z < top - 2.0:
        add_box(bm, x0 - 0.2, x1 + 0.2, y0 - 0.35, y0 + 0.02, z - 0.15, z + 0.15)
        z += st["landing_every"]
    add_box(bm, s.leg_x - st["ladder_w"] / 2, s.leg_x + st["ladder_w"] / 2, y0 - 0.3, y0 + 0.2, 0.0, st["z0"] + 0.3,
            mat=1)
    # clad, in the house's colour, so it reads apart from the leg; the ladder dark
    parts["stair_tower"] = finish(f"{prefix}stair_tower", bm, coll, [m["house"], m["gear"]], variant,
                                  mesh_name=f"{PROP}_{prefix}stair_tower")
    light = material(f"{PROP}_warning_light")
    bm = bmesh.new()
    for sx in (-1, 1):
        cx = sx * (s.apex_hx - 0.6)
        add_box(bm, cx - LIGHT / 2, cx + LIGHT / 2, s.apex_y - LIGHT / 2, s.apex_y + LIGHT / 2,
                s.apex_top - 0.02, s.apex_top + LIGHT_H)
    parts["apex_lights"] = finish(f"{prefix}apex_lights", bm, coll, [light], variant,
                                  mesh_name=f"{PROP}_{prefix}apex_lights")
    bm = bmesh.new()
    for sx in (-1, 1):
        cx = sx * (s.girder_x + 0.45)
        add_box(bm, cx - 0.25, cx + 0.25, s.boom_len - 0.85, s.boom_len - 0.25, s.bt - 0.02, s.bt + LIGHT_H)
    parts["nose_lights"] = finish(f"{prefix}nose_lights", bm, coll, [light], variant,
                                  mesh_name=f"{PROP}_{prefix}nose_lights", location=(0.0, s.hinge_y, s.hinge_z))
    return parts


# --- reference -------------------------------------------------------------------

def figure(name, coll, x, y, z=0.0, height=1.70, mat=None):
    """A 1.7 m standing figure for scale: a 12-sided body with a ball head."""
    r = 0.18
    bm = bmesh.new()
    ring = [(r * math.cos(math.tau * i / 12), r * math.sin(math.tau * i / 12)) for i in range(12)]
    low = [bm.verts.new((a, b, 0.0)) for a, b in ring]
    high = [bm.verts.new((a, b, height - 0.40)) for a, b in ring]
    bm.faces.new(list(reversed(low)))
    bm.faces.new(high)
    for i in range(12):
        j = (i + 1) % 12
        bm.faces.new((low[i], low[j], high[j], high[i]))
    body = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
    for v in bm.verts:
        if v not in body:
            v.co.z += height - 0.17
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


def lines(name, coll, pts, closed=True):
    """A wire outline or line at the quay (edges only, never rendered)."""
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


def metres(v):
    return f"{v:.1f}".replace(".", "p")


def build_reference(reference, specs):
    for s, tag in ((specs[0], ""), (specs[1], "_older")):
        gauge = "100ft" if not tag else "50ft"
        for side, y in (("waterside", s.ws_y), ("landside", s.ls_y)):
            lines(f"rail_{side}_{gauge}", reference, [(-80.0, y, 0.0), (80.0, y, 0.0)], closed=False)
        hx = s.overall_x / 2
        hy = s.ws_y + s.eq_hy
        lines(f"footprint_bogies{tag}_{metres(s.overall_x)}x{metres(2 * hy)}", reference,
              [(-hx, -hy, 0.0), (hx, -hy, 0.0), (hx, hy, 0.0), (-hx, hy, 0.0)])
        length = s.boom_tip_y - s.tail_y
        lines(f"plan_working{tag}_{metres(length)}x{metres(s.overall_x)}", reference,
              [(-hx, s.tail_y, 0.0), (hx, s.tail_y, 0.0), (hx, s.boom_tip_y, 0.0), (-hx, s.boom_tip_y, 0.0)])
    figure("figure_1p7m", reference, specs[0].leg_x + 5.0, specs[0].ws_y + 2.5)


# --- checks -------------------------------------------------------------------------

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
        mw = o.matrix_world
        for p in o.data.polygons:
            n = (mw.to_3x3() @ p.normal).normalized()
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


def variant_objects(variant):
    export = bpy.data.collections["export"]
    return [o for o in export.all_objects if o.type == "MESH" and str(o.get("kyt_variant", "")) == variant]


def extents(objs):
    xs, ys, zs = [], [], []
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            xs.append(p.x)
            ys.append(p.y)
            zs.append(p.z)
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def report(variant):
    bpy.context.view_layer.update()
    objs = variant_objects(variant)
    tris = triangles(objs)
    (x0, x1), (y0, y1), (z0, z1) = extents(objs)
    print(f"{PROP}: {variant}: {len(objs)} parts, {len({o.data.name for o in objs})} meshes, {tris} triangles, "
          f"x {x0:.2f}..{x1:.2f}, y {y0:.2f}..{y1:.2f}, z {z0:.3f}..{z1:.2f}")
    pairs = coplanar_pairs(objs)
    print(f"{PROP}: {variant}: {len(pairs)} coplanar overlapping face pairs" +
          ("" if not pairs else ": " + "; ".join(f"{a}/{b} {w}" for a, b, w in pairs)))
    return tris


def heights(s, prefix, stowed=False):
    """The numbers the brief asks for, measured off the built objects."""
    objs = [o for o in bpy.data.collections["export"].all_objects if o.name.startswith(prefix)]

    def top(name):
        o = bpy.data.objects[prefix + name]
        return max((o.matrix_world @ v.co).z for v in o.data.vertices)

    nose = boom_local(s, s.boom_len, s.bt, s.stow_deg if stowed else 0.0)
    return top("a_frame"), nose, top("boom")


# --- renders -------------------------------------------------------------------------

def far_report(new, far):
    """Each member's thickness in the original and the far crane, and how
    many pixels it covers at 2 km in the player's 70 degree view at 1080p."""
    rows = (
        ("leg, at its head (narrowest)", new.leg_head, far.leg_head),
        ("leg, at its foot", new.leg_foot, far.leg_foot),
        ("stay, backstay", 2 * new.stay_hw[0], 2 * far.stay_hw[0]),
        ("stay, mid forestay", 2 * new.stay_hw[1], 2 * far.stay_hw[1]),
        ("stay, tip forestay (thinnest)", 2 * new.stay_hw[2], 2 * far.stay_hw[2]),
        ("A-frame strut", new.strut, far.strut),
        ("girder depth (side view)", new.girder_depth, far.girder_depth),
        ("girder width (front view, each)", 2 * new.girder_hw, 2 * far.girder_hw),
        ("boom depth at the hinge", new.boom_root_depth, far.boom_root_depth),
        ("boom depth at the nose", new.boom_tip_depth, far.boom_tip_depth),
        ("portal beam depth", new.portal_beam_depth, far.portal_beam_depth),
        ("girder support beam depth", new.support_depth, far.support_depth),
        ("girder hanger, along the girder", 2 * new.hanger_hy, 2 * far.hanger_hy),
        ("girder hanger, across", new.hanger_out + 0.06, far.hanger_out + 0.06),
        ("portal brace", new.brace_h, far.brace_h),
        ("A crossbar", new.a_tie_cross_h, far.a_tie_cross_h),
    )
    for label, a, b in rows:
        print(f"{PROP}: far: {label}: {a:.2f} m ({a / FAR_PX_M:.2f} px) -> {b:.2f} m ({b / FAR_PX_M:.2f} px) "
              f"at 2 km, {FAR_PX_M:.3f} m a pixel")
    print(f"{PROP}: far: clear between the legs along the quay {2 * (far.leg_x - far.leg_foot / 2):.2f} m at the "
          f"feet ({2 * (new.leg_x - new.leg_foot / 2):.2f} before), {2 * (far.leg_x - far.leg_head / 2):.2f} m at "
          f"the heads; equaliser across the rail {2 * far.eq_hy:.2f} m ({2 * new.eq_hy:.2f} before); "
          f"cab's floor at {far.gb - far.cab_gap - far.cab_h:.2f} m")


def show_variant(variant):
    for v in VARIANTS:
        for o in variant_objects(v):
            o.hide_render = v != variant


def render(folder, specs):
    """Review frames on a staging quay that is made after the save and never
    saved: the crane on a grey quay at z = 0 with its rails drawn in, blue
    water 2.5 m below past the quay edge, a 40 ft box and a 1.7 m figure for
    scale; each variant three-quarter from the water, in side and front
    elevation, in plan (10 m grid) and beside the figure, close and whole;
    the far crane's two poses three-quarter and in side and front elevation;
    working and working_far side by side, three-quarter and in side
    elevation; then all five side by side on one quay 45 m apart, from the
    water, in front elevation, and from 2 km across it, once at the player's
    70 degree vertical view and once through a 280 mm lens."""
    new, old, far = specs
    scene = bpy.context.scene
    os.makedirs(folder, exist_ok=True)
    stage = bpy.data.collections.new("_review")
    scene.collection.children.link(stage)
    bpy.data.collections["authored"].hide_render = True
    bpy.data.collections["reference"].hide_render = True

    def mat(name, rgb):
        return material(name, (*rgb, 1.0))

    def slab(name, mat_, x0, x1, y0, y1, z0, z1):
        bm = bmesh.new()
        add_box(bm, x0, x1, y0, y1, z0, z1)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mat_)
        obj = bpy.data.objects.new(name, mesh)
        stage.objects.link(obj)
        return obj

    edge = new.ws_y + 4.0                      # the quay's edge, 4 m past the waterside rail
    quay = mat("_quay", (0.50, 0.50, 0.48))
    water = mat("_water", (0.06, 0.20, 0.42))
    ink = mat("_ink", (0.03, 0.03, 0.03))
    box40 = mat("_box40", (0.10, 0.40, 0.45))
    slab("_quay", quay, -3000, 3000, -600, edge, -4.0, -0.005)
    slab("_water", water, -3000, 3000, edge, 3000, -2.6, -2.5)
    rails = {}
    for key, y, x0, x1 in (("new_ws", new.ws_y, -420, 420), ("new_ls", new.ls_y, -420, 420),
                           ("old_ws", old.ws_y, -300, 300), ("old_ls", old.ls_y, -300, 300),
                           ("line_old_ls", 0.0, 70, 300)):
        rails[key] = [slab(f"_rail_{key}", ink, x0, x1, y - 0.15, y + 0.15, -0.006, -0.002)]
    container = slab("_box40", box40, -6.096, 6.096, 2.8, 2.8 + 2.438, 0.0, 2.591)
    fig = figure("_figure", stage, new.leg_x + 5.0, new.ws_y + 2.5, mat=mat("_figure_stage", (0.30, 0.22, 0.40)))
    grid = []
    for g in range(-8, 9):
        grid.append(slab(f"_grid_x{g}", ink, g * 10 - 0.12, g * 10 + 0.12, -70, edge, -0.004, -0.001))
    for g in range(-7, 2):
        grid.append(slab(f"_grid_y{g}", ink, -80, 80, g * 10 - 0.12, g * 10 + 0.12, -0.004, -0.001))

    def show_rails(*keys):
        for key, objs in rails.items():
            for o in objs:
                o.hide_render = key not in keys

    def show(objs, on):
        for o in objs:
            o.hide_render = not on

    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.45, 0.63, 0.85, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((0.55, 0.45, 0.70)).to_track_quat("Z", "Y").to_euler()
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

    def shoot(name, eye, target, lens=32, size=(1600, 1000), ortho=None, vfov=None):
        cam.location = eye
        direction = Vector(target) - Vector(eye)
        if abs(direction.x) < 1e-6 and abs(direction.y) < 1e-6:
            cam.rotation_euler = (0.0, 0.0, 0.0)          # straight down, +Y up the frame
        else:
            cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho
        cam.data.sensor_fit = "VERTICAL" if vfov else "AUTO"
        cam.data.sensor_width, cam.data.sensor_height = 36.0, 24.0
        cam.data.lens = (12.0 / math.tan(math.radians(vfov) / 2)) if vfov else lens
        cam.data.clip_start = 0.1
        cam.data.clip_end = 8000
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = os.path.join(folder, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"{PROP}: rendered {scene.render.filepath}")

    for v, s in (("working", new), ("stowed", new), ("panamax_older", old)):
        show_variant(v)
        show_rails("old_ws", "old_ls") if s is old else show_rails("new_ws", "new_ls")
        show(grid, False)
        show([fig, container], True)
        aim = {"working": 38.0, "stowed": 50.0, "panamax_older": 30.0}[v]
        shoot(f"{v}_three_quarter", (105.0, 95.0, 28.0), (0.0, 8.0, aim), lens=22)
        shoot(f"{v}_side_elevation", (500.0, 10.0, 50.0), (0.0, 10.0, 50.0), size=(1600, 1200), ortho=150.0)
        shoot(f"{v}_front_elevation", (0.0, 600.0, 45.0), (0.0, 0.0, 45.0), size=(1200, 1200), ortho=110.0)
        show(grid, True)
        shoot(f"{v}_plan", (0.0, 10.0, 600.0), (0.0, 10.0, 0.0), size=(1000, 1500), ortho=140.0)
        show(grid, False)
        fx, fy = s.leg_x + 5.0, s.ws_y + 2.5
        fig.location = (fx, fy, 0.0)
        shoot(f"{v}_with_figure", (fx + 13.0, fy + 15.0, 2.4), (fx - 4.0, fy - 2.5, 3.2), lens=28)
        shoot(f"{v}_with_figure_whole", (fx + 14.0, fy + 20.0, 1.5), (fx - 12.0, fy - 18.0, 24.0), lens=16)
    fig.location = (new.leg_x + 5.0, new.ws_y + 2.5, 0.0)
    for v in ("working_far", "stowed_far"):
        show_variant(v)
        show_rails("new_ws", "new_ls")
        show([fig, container], True)
        shoot(f"{v}_three_quarter", (105.0, 95.0, 28.0), (0.0, 8.0, 38.0 if v == "working_far" else 50.0), lens=22)
        shoot(f"{v}_side_elevation", (500.0, 10.0, 50.0), (0.0, 10.0, 50.0), size=(1600, 1200), ortho=150.0)
        shoot(f"{v}_front_elevation", (0.0, 600.0, 45.0), (0.0, 0.0, 45.0), size=(1200, 1200), ortho=110.0)

    def zoom(name, pts, scale=8, pad=10):
        """The last render's pixels round `pts`, enlarged `scale` times with
        no smoothing, so a member's width can be counted in pixels."""
        import numpy as np
        from bpy_extras.object_utils import world_to_camera_view
        w, h = scene.render.resolution_x, scene.render.resolution_y
        cs = [world_to_camera_view(scene, cam, Vector(p)) for p in pts]
        x0, x1 = max(0, int(min(c.x for c in cs) * w) - pad), min(w, int(max(c.x for c in cs) * w) + pad)
        y0, y1 = max(0, int(min(c.y for c in cs) * h) - pad), min(h, int(max(c.y for c in cs) * h) + pad)
        src = bpy.data.images.load(scene.render.filepath)
        arr = np.array(src.pixels[:], dtype=np.float32).reshape(h, w, 4)[y0:y1, x0:x1]
        big = np.repeat(np.repeat(arr, scale, axis=0), scale, axis=1)
        out = bpy.data.images.new("_zoom", big.shape[1], big.shape[0])
        out.pixels = big.ravel()
        out.filepath_raw = os.path.join(folder, f"{name}.png")
        out.file_format = "PNG"
        out.save()
        print(f"{PROP}: wrote {out.filepath_raw} ({x1 - x0} x {y1 - y0} px of the render, x{scale})")

    def place(offsets):
        """Linked copies of whole variants, moved; the originals hidden."""
        for v in VARIANTS:
            for o in variant_objects(v):
                o.hide_render = True
        dups = []
        for v, off in offsets.items():
            for o in variant_objects(v):
                dup = o.copy()
                dup.location = o.location + off
                dup.hide_render = False
                stage.objects.link(dup)
                dups.append(dup)
        return dups

    # working and working_far side by side, close, then in side elevation
    # with the far crane beyond the original's nose
    show([container], False)
    dups = place({"working": Vector((45.0, 0.0, 0.0)), "working_far": Vector((-45.0, 0.0, 0.0))})
    shoot("working_vs_far_three_quarter", (95.0, 200.0, 32.0), (0.0, 0.0, 38.0), lens=24, size=(1800, 1000))
    for o in dups:
        bpy.data.objects.remove(o, do_unlink=True)
    dups = place({"working": Vector((0.0, 0.0, 0.0)), "working_far": Vector((0.0, 130.0, 0.0))})
    dups.append(slab("_quay_far", quay, -60, 60, edge, 210, -4.0, -0.005))
    shoot("working_vs_far_side_elevation", (500.0, 74.0, 52.0), (0.0, 74.0, 52.0), size=(1800, 900), ortho=270.0)
    for o in dups:
        bpy.data.objects.remove(o, do_unlink=True)

    # the lineup: linked copies on one quay 45 m apart, the far cranes beside
    # their originals, the older crane on its 50 ft pair moved so its
    # waterside rail is the new cranes' (ports kept the waterside rail and
    # laid a second landside one)
    dups = place({"panamax_older": Vector((90.0, new.ws_y - old.ws_y, 0.0)), "working": Vector((45.0, 0.0, 0.0)),
           "working_far": Vector((0.0, 0.0, 0.0)), "stowed": Vector((-45.0, 0.0, 0.0)),
           "stowed_far": Vector((-90.0, 0.0, 0.0))})
    show_rails("new_ws", "new_ls", "line_old_ls")
    shoot("lineup_from_water", (260.0, 200.0, 55.0), (0.0, 0.0, 40.0), lens=30, size=(1800, 1000))
    shoot("lineup_front_elevation", (0.0, 600.0, 50.0), (0.0, 0.0, 50.0), size=(1800, 1100), ortho=235.0)
    shoot("lineup_from_2km_player_view", (-700.0, 1900.0, 60.0), (0.0, 10.0, 45.0), size=(1920, 1080), vfov=70.0)
    zoom("lineup_from_2km_player_view_pixels_x8", [(x, y, z) for x in (-104.0, 104.0)
                                                   for y in (-50.0, 80.0) for z in (0.0, 101.0)])
    shoot("lineup_from_2km_telephoto", (-700.0, 1900.0, 60.0), (0.0, 10.0, 52.0), lens=280, size=(1800, 1000))
    for o in dups:
        bpy.data.objects.remove(o, do_unlink=True)

    # the further variants, each three-quarter and in side elevation; the
    # details' stair tower close up
    for v in VARIANTS[5:]:
        show_variant(v)
        older = v.startswith("panamax_older")
        show_rails("old_ws", "old_ls") if older else show_rails("new_ws", "new_ls")
        show([fig, container], True)
        aim = 40.0 if older else 38.0
        shoot(f"{v}_three_quarter", (105.0, 95.0, 28.0), (0.0, 8.0, aim), lens=22)
        shoot(f"{v}_side_elevation", (500.0, 10.0, 50.0), (0.0, 10.0, 50.0), size=(1600, 1200), ortho=150.0)
    show_variant("working_details")
    show_rails("new_ws", "new_ls")
    shoot("working_details_stair_close", (34.0, -42.0, 9.0), (new.leg_x, new.ls_y - 2.0, 16.0), lens=26)
    shoot("working_details_apex_lights_close", (24.0, 26.0, 80.0), (0.0, new.apex_y, 71.0), lens=35)
    shoot("working_details_nose_lights_close", (18.0, 86.0, 54.0), (0.0, new.boom_tip_y - 1.0, 48.0), lens=35)

    # every variant in one row, 45 m apart, in the order of the card; the
    # older cranes' waterside rail is the new cranes', their landside rail
    # drawn under them
    order = ("working", "working_white_red", "working_grey_blue", "working_details", "working_lattice",
             "working_single_girder", "working_house_under", "working_spreader_down", "working_trolley_backreach",
             "working_trolley_portal", "working_far", "stowed", "stowed_far", "panamax_older", "panamax_older_stowed")
    gap = 45.0
    offs = {}
    for i, v in enumerate(order):
        dy = new.ws_y - old.ws_y if v.startswith("panamax_older") else 0.0
        offs[v] = Vector(((len(order) - 1) / 2 * gap - i * gap, dy, 0.0))
    dups = place(offs)
    old_x = [offs[v].x for v in order if v.startswith("panamax_older")]
    dups.append(slab("_rail_old_ls_all", ink, min(old_x) - 20, max(old_x) + 20, -0.15, 0.15, -0.006, -0.002))
    show_rails("new_ws", "new_ls")
    show([fig, container], False)
    shoot("lineup_all_front_elevation", (0.0, 800.0, 55.0), (0.0, 0.0, 55.0), size=(3600, 800), ortho=700.0)
    shoot("lineup_all_aerial", (40.0, 480.0, 230.0), (0.0, 0.0, 25.0), lens=20, size=(2400, 1300))


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

    new, old = Spec("post_panamax", NEW), Spec("panamax_older", OLD)
    m_new, m_old = mats(), mats(older=True)
    # the kit both cranes share: built into the working crane, linked into the rest
    kit_coll = export
    kit = {
        "bogies": finish("_kit_bogies", bogie_set_bm(new), kit_coll, [m_new["gear"]], "working",
                         mesh_name=f"{PROP}_bogie_set"),
        "spreader": finish("_kit_spreader", spreader_bm(new), kit_coll, [m_new["spreader"]], "working",
                           mesh_name=f"{PROP}_spreader"),
    }
    working = build_crane(new, export, "working", "", m_new, kit)
    for k in kit.values():
        bpy.data.objects.remove(k, do_unlink=True)
    stowed_coll = bpy.data.collections.new("variant_stowed")
    export.children.link(stowed_coll)
    build_stowed(new, working, stowed_coll, m_new)
    older_coll = bpy.data.collections.new("variant_panamax_older")
    export.children.link(older_coll)
    kit = {"bogies": working["bogies_ws_px"], "spreader": working["spreader"]}
    older = build_crane(old, older_coll, "panamax_older", "older_", m_old, kit)
    # the far crane: its own chunkier bogie set and spreader, shared by its two poses
    far = Spec("post_panamax_far", FAR)
    far_coll = bpy.data.collections.new("variant_working_far")
    export.children.link(far_coll)
    kit = {
        "bogies": finish("_kit_far_bogies", bogie_set_bm(far), far_coll, [m_new["gear"]], "working_far",
                         mesh_name=f"{PROP}_bogie_set_far"),
        "spreader": finish("_kit_far_spreader", spreader_bm(far), far_coll, [m_new["spreader"]], "working_far",
                           mesh_name=f"{PROP}_spreader_far"),
    }
    working_far = build_crane(far, far_coll, "working_far", "far_", m_new, kit)
    for k in kit.values():
        bpy.data.objects.remove(k, do_unlink=True)
    stowed_far_coll = bpy.data.collections.new("variant_stowed_far")
    export.children.link(stowed_far_coll)
    build_stowed(far, working_far, stowed_far_coll, m_new, variant="stowed_far", prefix="stowed_far_")

    # the further variants, each the working crane's meshes linked but for
    # what it changes
    def new_coll(v):
        c = bpy.data.collections.new(f"variant_{v}")
        export.children.link(c)
        return c

    single = Spec("post_panamax_single_girder", SINGLE)
    build_livery(working, new_coll("working_white_red"), "working_white_red", "white_red_", paint_white_red)
    build_livery(working, new_coll("working_grey_blue"), "working_grey_blue", "grey_blue_", paint_grey_blue)
    build_stowed(old, older, new_coll("panamax_older_stowed"), m_old, variant="panamax_older_stowed",
                 prefix="older_stowed_")
    build_pose(new, working, new_coll("working_spreader_down"), m_new, "working_spreader_down", "deck_",
               new.work_trolley_y, POSES["deck_z"])
    build_pose(new, working, new_coll("working_trolley_backreach"), m_new, "working_trolley_backreach", "back_",
               new.trolley_back_y, POSES["chassis_box_top"])
    build_pose(new, working, new_coll("working_trolley_portal"), m_new, "working_trolley_portal", "portal_",
               POSES["portal_spreader_y"] - new.rope_dy, new.park_z)
    build_lattice(new, working, new_coll("working_lattice"), m_new)
    build_single(single, working, new_coll("working_single_girder"), m_new)
    build_house_under(new, working, new_coll("working_house_under"), m_new)
    build_details(new, working, new_coll("working_details"), m_new)
    build_reference(reference, (new, old))
    hy = far.ws_y + far.eq_hy
    hx = far.overall_x / 2
    lines(f"footprint_bogies_far_{metres(far.overall_x)}x{metres(2 * hy)}", reference,
          [(-hx, -hy, 0.0), (hx, -hy, 0.0), (hx, hy, 0.0), (-hx, hy, 0.0)])
    bpy.context.view_layer.update()
    for v in VARIANTS[1:]:
        eye = layer_collection(f"variant_{v}")
        if eye is not None:
            eye.hide_viewport = True

    for s, prefix, v, stowed in ((new, "", "working", False), (new, "stowed_", "stowed", True),
                                 (old, "older_", "panamax_older", False), (far, "far_", "working_far", False),
                                 (far, "stowed_far_", "stowed_far", True),
                                 (old, "older_stowed_", "panamax_older_stowed", True),
                                 (new, "lattice_", "working_lattice", False),
                                 (single, "single_", "working_single_girder", False),
                                 (new, "details_", "working_details", False)):
        apex, nose, boom_top = heights(s, prefix, stowed)
        print(f"{PROP}: {v}: gauge {s.gauge:.2f}, outreach {s.outreach:.1f} (boom nose at y {s.boom_tip_y:.2f}), "
              f"backreach {s.backreach:.1f} (tail at y {s.tail_y:.2f}), lift {s.lift:.1f}, hinge {s.hinge_z:.1f} "
              f"at y {s.hinge_y:.2f}, portal clear {s.portal_clear:.2f}, over the bogies {s.overall_x:.2f}; "
              f"apex top {apex:.2f}; boom nose top at y {nose[0]:.2f} z {nose[1]:.2f}, boom's highest {boom_top:.2f}")
    for v in VARIANTS:
        report(v)
    far_report(new, far)
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()
        print(f"{PROP}: saved", bpy.data.filepath)
    if "--render" in argv:
        render(argv[argv.index("--render") + 1], (new, old, far))


main()
