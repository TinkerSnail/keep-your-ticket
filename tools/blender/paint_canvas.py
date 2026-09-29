"""The paint canvas for a prop's own texture, and its one material.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>.blend \
        --python tools/blender/paint_canvas.py -- [--size 2048] [--orm-size 1024] [--grain]
        [--knots part,part] [--wear part,part] [--chips part,part] [--dings part,part]
        [--ground part,part] [--weather part,part] [--perforate part,part] [--overwrite]
        [--holes-only] [--guide-only] [--save]
    ... --python tools/blender/paint_canvas.py -- --leaflets [--overwrite | --cutout-only | --shading-only
        | --normal-only | --base-fade <kind>:<share>] [--save]
    ... --python tools/blender/paint_canvas.py -- --bands [--size 1024] [--orm-size 256] [--overwrite] [--save]

Runs on the game-ready working file (after Make game mesh), whose game mesh is
unwrapped for its own texture. Writes three images to
`assets/source/textures/<prop>/`:

- `<prop>_colour.png`: each piece filled with the colour its material has now,
  and spread a few pixels past its edge so mipmaps don't pull in the gaps.
  **Paint on this**, in Blender texture paint or over the PNG in Photoshop or
  Procreate.
- `<prop>_orm.png`: occlusion, roughness and metalness packed in red, green
  and blue (the glTF and Godot convention), from the materials' values; no
  occlusion yet (red is white).
- `<prop>_uv_guide.png`: transparent, the outline of every piece in white, to
  lay over the colour as a locked top layer in Photoshop or Procreate and hide
  before exporting. Drawn from the mesh, so always safe to redraw:
  `--guide-only` redraws it and touches nothing else.

`--grain` gives timber (a material whose name contains "timber") wood grain
instead of a flat colour: growth rings round the bench's length (its x axis)
as a solid 3D pattern, so the grain runs unbroken round a board's edges and
shows as rings on its cut ends, with wavy figure and fine streaks along the
grain.

`--knots back_` lets those parts' wood carry the knots listed in KNOTS: a dark
core stretched along the grain, with the growth rings bulging round it. `--wear seat_` wears
the top edges of those parts' wood pale and smooth where people sit, most on
the front board's rounded front edge where legs rub, fading away from the seat
contract's two seats.

`--weather arm_loop,scroll,armrest,front_leg:0.4` weathers the painted metal
(any material but timber) of the parts whose names start with those
words, `:0.4` scaling that part's rust streaks, read
from the `kyt_part` record Make game mesh leaves on each face: paint faded on
top and worn through to dark, hand-polished iron where hands rest, chips on
edges with rust round them and streaking down, rust and dirt climbing from the
paving, grime in the crevices. Rust is rough and bare iron metallic in the ORM
too.

`--chips arm_loop,scroll,armrest` is the light touch: only a few small chips
along the edges of those parts' painted iron, grey iron showing through, and
nothing else. An edge is wherever the surface turns within a few millimetres:
a bar's corner, or the ridge between two facets of a tube. `front_leg:0.5`
thins a part's chips: a straight leg's long ridges catch far more than a ring's
curved ones. `--dings arm_loop` adds small chips across the tops of those
parts, not just their edges, where hands and bags knock them. `--ground
front_leg,foot_front` adds only the rust and dirt climbing from the paving.
The ground band also carries a few dark spots of dirt near the paving. The
plaza bench wears chips on its whole frame, dings on top of its outer arm rings
and its feet, and a little ground dirt with dark spots at its feet
(Christina, 2026-09-24).

`--perforate seat_sheet,back_sheet` cuts expanded-metal diamond holes through
those parts' broad faces (both faces of a sheet at the same places, so it can
be seen through): into the colour PNG's alpha, which the material clips (glTF
alphaMode MASK, Godot alpha scissor), and into `<prop>_holes.png`, which
`tools/blender/apply_holes.py` puts back into the colour PNG after every export
of the painting, because a flattened PSD has no alpha. Collision stays solid.
`--holes-only --perforate <parts>` cuts them again on an existing canvas after
a change to the `HOLE_*` numbers: the colour keeps its pixels, only its alpha
and `<prop>_holes.png` change.

`--leaflets` is the canvas for a crown whose game chooses its fronds
(`kyt_keep_parts`, the palm crown), after `unwrap_blades.py` has laid its
blades out; there is no game mesh. Each blade's island gets its colour and,
for the kinds in `LEAFLETS`, leaflets and basal spines from the rachis to the
blade's outline, cut into the colour's alpha and into `<prop>_cutout.png`.
That is the starting cut-out: `prop_handback.py --open` gives the PSD a
"cut-out" layer made from it, which Christina paints (black cuts, white
keeps), and every export writes it back and puts it into the alpha. The spear,
the stub and the heart stay whole. `--leaflets --cutout-only` cuts the leaflets
again after a change to `LEAFLETS`, into `<prop>_cutout.png` only.

`--bands` is the canvas for a banded trunk (the palm trunk), whose segments
share a few bands laid round the canvas's full width, as its shaping left them
(`kyt_band_islands` on the mesh); there is no game mesh. Each band gets the
BAND_* look: dark base, scalloped tan, pale collar.

All of these are starting points to paint over, not a finish.

Then the game mesh's materials (timber, cast iron, fixings) are replaced by one
material named after the prop that reads both images, so each placement is one
draw and the prop looks as it did until the colour is painted. Refuses to
overwrite the colour or ORM PNG: by then it may be Christina's painting.
`--overwrite` is for a canvas nobody has painted yet. Without `--save` the file
is not written.
"""

import json
import os
import sys
import zlib

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bump_to_normal import DEPTH_PX, WRAP_U, normal_from_height  # noqa: E402

MARGIN_PX = 16
BAKE_SAMPLES = 32  # smooths grain finer than a pixel, and the crevice sampling

# Wood grain, in metres. Rings circle a pith line along x, below and in front
# of the seat, so seat and back boards are cut well away from the heart and
# show long, gently curved bands.
PITH_YZ = (0.12, -0.05)
RING_M = 0.009  # one growth ring; 5 px at the bench's 576 px per metre
EARLY, LATE = 1.10, 0.72  # earlywood and latewood, times the timber colour; they average about 1
# Knots, placed by hand in object space (x along the bench, y front to back, z
# up), just behind a back board's front face (y 0.307), so the face cuts them
# through the middle. Christina asked for one or two on the whole back rest
# (2026-09-24).
KNOTS = [(-0.32, 0.309, 0.72),  # back_1, left of centre
         (0.58, 0.309, 0.84)]  # back_2, right of centre
KNOT_ALONG_M, KNOT_ACROSS_M = 0.125, 0.05  # a knot's reach, along and across the grain
KNOT_CORE = 0.2  # the knot's dark core, as a fraction of its reach: about 5 cm by 2 cm
KNOT_BULGE_M = 0.025  # how far the rings bend round a knot
KNOT_DARK = 0.45  # the core, times the wood's colour; its rim darker still
KNOT_RING = 0.035  # the knot's own growth rings, as a fraction of a cell

# Wear on seat boards, in metres along the bench (x) and back from its front (y).
SEATS_X = 0.45  # the seat contract: a guest 0.45 m either side of centre
SEAT_SPREAD_M = 0.3  # wear fades out this far from a seat
FRONT_Y = -0.266  # the front edge of the front board, where legs rub
WORN = (0.30, 0.17, 0.08, 1.0)  # timber rubbed pale, the finish gone
WORN_ROUGH = 0.5  # smoothed by use
WEAR_EDGE_M = 0.015  # how far round an edge the wear reaches
SEAT_TOP_Z = 0.51  # the seat contract's seat top; only the boards' top edges wear
ARRIS_M = 0.028  # the front edge wears this far round, over the top and down the front
WEAR = 0.8  # how far worn wood goes to WORN; the grain still shows

# Weathering on painted iron, linear colours and 0-1 amounts.
FADED = (0.014, 0.075, 0.036, 1.0)  # the green bleached on surfaces facing the sky
BARE_IRON = (0.02, 0.019, 0.018, 1.0)  # paint worn through, polished by hands
RUST = (0.16, 0.05, 0.012, 1.0)
FADE = 0.5  # how far the tops fade
HAND_WEAR = 0.85  # how much of the paint hands have worn off the tops
CHIP_EDGE_M = 0.006  # how far round an edge the chipping reaches
GRIME = 0.55  # how dark the crevices get
STREAKS = 0.6  # rust running down upright faces; `part:0.4` scales it for a part
GROUND_M = 0.05  # rust and dirt climb this far up from the paving; the feet are 5 cm tall
GROUND_RUST = 0.3  # how much of the ground band rusts, at the paving itself
GROUND_DIRT = 0.15  # how dark the dirt is there; much more and the feet read as muddy
DIRT = (0.004, 0.0035, 0.003, 1.0)  # a dirt spot: near-black, about a sixth as bright as the green paint
DIRT_SPOT_M = 0.025  # the patchiness dirt spots are cut from
DIRT_LEVEL = 0.58  # how high it must reach for a spot: higher, fewer spots
DIRT_REACH_M = 0.12  # spots only this near the ground
CHIP_IRON = (0.11, 0.105, 0.1, 1.0)  # a chip's grey iron: light enough to read against dark green paint
CHIP_ROUGH, CHIP_METAL = 0.55, 0.6  # dull: a shiny chip mirrors its surroundings and reads as a dark speck
CHIP_SIZE_M = 0.07  # the patchiness chips are cut from; a chip is a fraction of it
CHIP_LEVEL = 0.64  # how high that patchiness must reach for a chip: higher, fewer chips
CHIP_THIN = 0.06  # how much higher it must reach on a part chipped at `part:0`
DING_SIZE_M = 0.03  # dings on a part's top are smaller and closer than edge chips
DING_LEVEL = 0.64  # how high their patchiness must reach: higher, fewer dings
BARE_ROUGH, BARE_METAL = 0.32, 0.95
RUST_ROUGH, RUST_METAL = 0.92, 0.05

# Perforations: expanded-metal diamonds, their long way along the bench (x),
# after Christina's photo of the perforated bench (2026-09-11), scaled up for
# the game at her request. A strand's width is
# 2 * HOLE_STRAND / sqrt(1/along^2 + 1/across^2): about 11 mm here, with the
# panel about 46% open and a diamond about 83 by 35 px at 925 px per metre.
# (30 by 13 mm with strand 0.12 made 2.9 mm wires, "too thin"; strand 0.24 on
# that cell closed the mesh to 27%; 45 by 19 mm at 0.16 was "too delicate".)
HOLE_ALONG_M, HOLE_ACROSS_M = 0.090, 0.038
HOLE_STRAND = 0.16  # the metal between two diamonds, as a fraction of a cell

# Leaflets (--leaflets), cut into a crown's blades. The crown is Phoenix
# canariensis, the classic California date palm, drawn in the park's cartoony
# style: a few broad, pointed leaflets in a row down each side of the rachis,
# pointing toward the tip, turning to spines near the base. Per blade kind, in
# metres and degrees: a leaflet every `spacing` along each side (the two sides
# offset by half), `width` at its widest, leaving the rachis at `open` degrees
# where the spines end and closing steadily to `tip` at the tip. Each leaflet
# opens no wider than the one below it, so neighbours fan apart and never
# cross, and each reaches the blade's outline. The first `spines` of the
# frond's length carries spines instead. `missing` and `broken` are the
# fractions of leaflets gone or snapped short. The spear, the stub and the
# heart stay whole.
#
# Christina asked for "wider and fewer, to match our cartoony style" on
# 2026-09-26: about 20 leaflets a side on the mature frond, 3.5 times as wide
# as the first cut's 70 (0.05 m apart, 0.042 wide; "B" of three she was
# shown). The blade stays about 46% leaf, which each kind keeps through the
# 0.5 alpha cut at every mip level: much less and a frond would vanish at a
# distance.
LEAFLETS = {
    "young": dict(spacing=0.14, width=0.08, open=36, tip=20, spines=0.14, missing=0.0, broken=0.0),
    "mature": dict(spacing=0.18, width=0.15, open=62, tip=34, spines=0.16, missing=0.0, broken=0.03),
    "old": dict(spacing=0.18, width=0.135, open=66, tip=38, spines=0.16, missing=0.05, broken=0.15),
    "dead": dict(spacing=0.18, width=0.105, open=46, tip=28, spines=0.16, missing=0.15, broken=0.3),
}
# The torn style (CUT_STYLE "tears"), after the Mario Kart 7 palm Christina
# pointed to (2026-09-26, `documentation/reference/palm_crown/`): each frond one
# broad folded leaf, torn like a banana leaf along its side veins. Per blade
# kind: `tears` (fewest, most) per side, from `start` of the way up to near the
# tip, each a narrow slit `width` metres wide at the edge (least, most),
# pointed at its inner end, reaching `depth` of the way in from the edge (least,
# most; deeper toward the tip); `nicks` small notches per side, `nick_depth`
# deep. Tears and veins leave the midrib at `open` degrees, closing to `tip`.
# (The first fringed cut, wide bites like a saw, she called "abysmal".)
TEARS = {
    "young": dict(tears=(1, 3), start=0.35, width=(0.04, 0.07), depth=(0.2, 0.45), nicks=2,
                  nick_depth=(0.04, 0.08), open=62, tip=48),
    "mature": dict(tears=(3, 6), start=0.25, width=(0.05, 0.1), depth=(0.25, 0.65), nicks=4,
                   nick_depth=(0.04, 0.1), open=62, tip=48),
    "old": dict(tears=(4, 7), start=0.2, width=(0.05, 0.11), depth=(0.3, 0.75), nicks=5,
                nick_depth=(0.05, 0.12), open=62, tip=48),
    "dead": dict(tears=(6, 9), start=0.15, width=(0.06, 0.12), depth=(0.4, 0.85), nicks=6,
                 nick_depth=(0.06, 0.14), open=60, tip=45),
}
TEAR_PAST_PX = 4  # a tear runs this far past the outline, so it opens at the edge
# Her call, 2026-09-26: "this is a better direction for the crown"; the torn
# leaf's texture went into her PSD on today's blades ("just texture").
CUT_STYLE = "tears"  # "tears" (torn broad leaves) or "leaflets" (separate leaflets)

# A painted starting look for the torn leaves (`--shading-only`), after the
# same references: dark at the base and in the crease beside the midrib,
# lightening along the leaf to a pale rim and tip, a bright midrib, faint
# darker veins along the fan, soft mottling. sRGB, as painted. Per kind:
# `dark` (base and crease), `light` (the leaf's body toward the tip), `rim`
# (its outer edge), `midrib`. The stub and the heart are left to her paint.
SHADING = {
    "spear": dict(dark=(0.16, 0.42, 0.10), light=(0.50, 0.80, 0.26), rim=(0.74, 0.94, 0.42), midrib=(0.88, 0.97, 0.66)),
    "young": dict(dark=(0.12, 0.36, 0.08), light=(0.44, 0.76, 0.22), rim=(0.72, 0.93, 0.40), midrib=(0.88, 0.97, 0.64)),
    "mature": dict(dark=(0.04, 0.20, 0.06), light=(0.28, 0.60, 0.15), rim=(0.64, 0.89, 0.34), midrib=(0.84, 0.95, 0.60)),
    "old": dict(dark=(0.14, 0.22, 0.05), light=(0.44, 0.58, 0.16), rim=(0.72, 0.80, 0.34), midrib=(0.86, 0.88, 0.56)),
    "dead": dict(dark=(0.25, 0.15, 0.06), light=(0.56, 0.42, 0.22), rim=(0.76, 0.62, 0.36), midrib=(0.86, 0.75, 0.52)),
}
SHADE_BASE = 0.3  # the first this share of the leaf darkens toward the crown's heart
SHADE_CREASE = (0.35, 0.45)  # how much darker the crease is, and how far out it reaches (share of the half-width)
SHADE_RIM = 0.35  # the rim begins this share of the way out
MIDRIB_M = 0.02  # the midrib's half-width
VEIN_EVERY_M, VEIN_DARK = 0.22, 0.05  # faint vein lines along the fan, this far apart, this much darker
MOTTLE, MOTTLE_M = 0.07, 0.25  # soft light-and-dark patches this strong, about this big
BASE_FADE_ALPHA = 0.85  # `--base-fade`: how strongly the colour holds at the stalk
# The leaves' relief (`--normal-only`), in metres, after Christina's "mostly for
# the crenelated nature of the surface" (2026-09-27): a palm leaf is pleated
# like an accordion, ridge and valley between its side veins, sharp at both
# creases, the pleats deepening from nothing near the midrib to `PLEAT_M` from
# `PLEAT_OUT` of the way out; a rib along the midrib; a slight curl at the rim.
# Raised toward the mesh normal, which faces the underside (the blades'
# normals point down): the midrib and veins stand proud underneath and sit as
# grooves on top, as they do on a real leaf.
PLEAT_M, PLEAT_OUT = 0.035, 0.45
RIB_M, RIB_WIDTH_M = 0.015, 0.02
CURL_M = 0.03

LEAFLET_WIDEST = 0.3  # where along a leaflet it is widest; it narrows to a point at the tip
LEAFLET_SLENDER = 0.3  # no leaflet is wider than this share of its length: short ones stay points
LEAFLET_JITTER = 0.25  # how far a leaflet's place and width wander, as a fraction of each
ANGLE_JITTER = 0.03  # and its angle: more and long leaflets cross their neighbours
SPINE_ANGLE = 30  # degrees off the rachis
SPINE_WIDTH, SPINE_REACH_M, SPINE_EVERY = 0.3, 0.2, 1.5  # spines: a share of the leaflet width, shorter, sparser
RACHIS_M = (0.03, 0.006)  # the rachis's half-width at the base and at the tip
RACHIS_STRAW = (0.34, 0.26, 0.05)  # linear; the rachis and spines are the leaf's colour taken this way
RACHIS_TINT = 0.45
TIP_INSET_PX = 2  # a leaflet's tip stops this far inside its blade's outline
ALPHA_SPREAD_PX = 4  # opaque edges carried this far past an island, so filtering never frays them

# A plant other than the palm crown whose leaves bend blades along courses
# (`plant_blades.py`) gets its own leaflet table: which cut, the LEAFLETS for
# its blade kinds, and its rachis's half-width (base, tip), colour (linear) and
# how fully the rachis takes that colour. `use_prop_leaflets` puts it in place
# of the crown's for the run. The fern fan (PRP-PLANT-011, 2026-09-27,
# Christina: "on things with leaflets like the fern, use our same approach we
# used with the palm fronds texture to avoid too many triangles"): its pinnae
# leave the geometry for the cut-out, on a blade whose outline their tips
# traced; out from the rachis at a wide angle, no spines, a green rachis.
#
# Her direction the same evening, for all the palm-bed plants: "more cartoony",
# "think animal crossing sizing", "very nintendo". So the fern's pinnae are few
# and broad, six or so a side, with round ends (`profile="round"`) and allowed
# half as wide as they are long (`slender`), placed a little more evenly
# (`jitter`), on a thick rachis.
PROP_LEAFLETS = {
    "fern_fan": dict(style="leaflets", rachis=(0.016, 0.006), rachis_colour=(0.016, 0.053, 0.007),
                     rachis_tint=1.0, profile="round", slender=0.55, jitter=0.12, kinds={
                         "mature": dict(spacing=0.135, width=0.095, open=74, tip=58, spines=0.0,
                                        missing=0.0, broken=0.0),
                         "young": dict(spacing=0.125, width=0.082, open=68, tip=52, spines=0.0,
                                       missing=0.0, broken=0.0),
                     }),
    # The Purple Heart (PRP-PLANT-015 to 017, 2026-09-28, her "we need to figure
    # out how to do the same thing with the purple heart"): each leaf a card
    # whose one broad, softly pointed purple leaf and pale midrib are cut from
    # the texture (`style="leaf"`); `fill` is how much of the card's half-width
    # the leaf takes at its widest.
    "purple_heart_sprig": dict(style="leaf", rachis=(0.007, 0.002), rachis_colour=(0.21, 0.09, 0.28),
                               rachis_tint=0.7, profile="lance", kinds={
                                   "leaf": dict(fill=0.94), "young": dict(fill=0.94),
                               }),
    # The bushes' greenery (`leaf_skin.py`, 2026-09-28), after the Animal
    # Crossing bushes she pointed to: one leaf per card, many cards shingled
    # over the bush. `shade` darkens the leaf's base and lightens its tip
    # (times the colour, base to tip), the soft gradient each AC leaf wears;
    # `teeth` (count a side, depth as a share of the width) saws the margin.
    # Azalea: a fresh green, pointed oval. Hibiscus (her "a darker leaf with a
    # different shape"): dark blue-green, broader, toothed.
    # Then her "the leafs need to be grouped and merged" and "texture creates
    # the definition within the clusters": each card is a clump of `leaves`
    # (`style="cluster"`, `cut_cluster`), fanned `spread` degrees, the outer
    # ones `lengths[0]` of the way to the card's edge and the middle one
    # `lengths[1]`, each `width` of its length across either side of its
    # midrib, casting a `shadow` on those beneath.
    # Then, after the Mario Kart trees she pointed to ("lots of painted on
    # leaves layered in shaped sections"), a card was a whole section of the
    # bush; and after her Mario Kart tree of semi-domes ("our shrubs will be
    # assembled from a series of these types of shapes"), the greenery is a
    # few big domes (`style="dome"`, `cut_dome`): rings of leaves `leaf_m`
    # long round the apex, pointing out, the rings nearer the apex laid over
    # those beyond like shingles, each leaf `width` of its length across either
    # side of its midrib, shaded stalk to tip (`shade`), throwing a `shadow` on
    # those under it; the dome filled under its leaves with their shade
    # (`gap`, times the colour), lighter at its apex (`top`) and darker toward
    # its drooping rim (`rim_dark`).
    #
    # `bloom`: the flowers' card (her "needs to be optimized for using
    # textures"), drawn once per colourway side by side along the canvas
    # (`slots`, sRGB; the card's island is the first, each next one a
    # `1 / len(slots)` of the canvas to the right), so each colourway is
    # painted, and a placement's Godot script picks one by sliding the bloom
    # material's UVs. `art`: "truss", seven azalea blooms in a bunch (her
    # "azalea blooms need to be clustered together ... more intensely and more
    # densely"), since one "azalea", one trumpet flower (her "each individual
    # azalea flower needs to be given a cone/trumpet shape"), its top petal
    # speckled, long stamens; "hibiscus", one big round flower. Each slot is
    # (petal, throat); the hibiscus's stamens are `pollen`, the azalea's its
    # throat's colour.
    #
    # Each colourway is painted again in each of the card's shades
    # (`kyt_shades`, `leaf_skin.py`: every flower wears one), side by side in
    # its slot, lightest first (`bloom_shade`). With `light` and `dark` (per
    # slot, (petal, throat), sRGB) the shades run from `light` through the
    # colourway itself in the middle to `dark`, reaching `spread` of the way
    # out to either (1 when not given); with `darken`, from the
    # colourway to that share darker. `vary_dark`: each leaf painted up to
    # that share darker than its neighbours, as the colour picker reads (her
    # "vary the leaves in darkness on each bush by about 3%"), besides the
    # touch lighter or darker each already was.
    "azalea_bush": dict(style="dome", rachis=(0.004, 0.0015), rachis_colour=(0.36, 0.62, 0.16),
                        rachis_tint=0.5, profile="ovate", kinds={
                            "leaf": dict(leaf_m=0.22, width=0.3, splay=25.0, shade=(0.64, 1.15), shadow=0.4, rim_dark=0.3,
                                         gap=0.45, top=0.08, vary_dark=0.03),
                            # Her "on the azaleas the lightest will be a light pink
                            # almost white, the dark will be almost fushia, and every
                            # shade in between": the pink's; the magenta and white
                            # the same way round their own colour. Then "lets make
                            # the contrast a little less severe between the lightest
                            # and darkest flowers": three quarters of the way out.
                            "bloom": dict(art="azalea", slots=[((0.97, 0.52, 0.76), (0.80, 0.14, 0.46)),
                                                              ((0.88, 0.2, 0.55), (0.55, 0.04, 0.3)),
                                                              ((0.98, 0.95, 0.96), (0.92, 0.52, 0.68))],
                                          light=[((0.99, 0.90, 0.94), (0.93, 0.55, 0.72)),
                                                 ((0.93, 0.38, 0.67), (0.68, 0.08, 0.40)),
                                                 ((1.0, 0.99, 0.99), (0.95, 0.68, 0.79))],
                                          dark=[((0.85, 0.13, 0.60), (0.58, 0.03, 0.37)),
                                                ((0.74, 0.08, 0.47), (0.42, 0.02, 0.25)),
                                                ((0.97, 0.87, 0.91), (0.88, 0.40, 0.58))],
                                          spread=0.75),
                        }),
    "azalea_tree": None,  # the azalea's own leaf: set just below
    "hibiscus_shrub": dict(style="dome", rachis=(0.005, 0.0015), rachis_colour=(0.16, 0.38, 0.30),
                           rachis_tint=0.45, profile="ovate", kinds={
                               # Her hibiscus photos: a hardy hibiscus's leaf, palmate,
                               # three pointed lobes, sharply serrated (her "the shape of
                               # the hibiscus leaves isnt right" of the toothed oval).
                               "leaf": dict(leaf_m=0.22, width=0.3, splay=25.0, shade=(0.6, 1.18), shadow=0.4, rim_dark=0.3,
                                            gap=0.45, top=0.08, vary_dark=0.03,
                                            teeth=(7, 0.1, "saw"), col_width=1.05, row_step=0.5,
                                            lobes=[(0.0, 1.0, 0.3), (-48.0, 0.72, 0.3), (48.0, 0.72, 0.3)],
                                            # Her "make the three veins on each hibiscus leaf a little
                                            # shorter so they dont visually go all the way to the tips",
                                            # "the edge of each hibiscus leaf slightly lighter than the
                                            # rest of the leaf", "a subtle drop shadow under each leaf",
                                            # then "make the drop shadows more pronounced and the lighter
                                            # color more pronounced too".
                                            rib_reach=0.72, edge_m=0.01, edge_light=0.45,
                                            drop=0.55, drop_m=0.014, drop_blur_m=0.011),
                               # Her "the tolerance will be smaller with some blooms
                               # just being a slightly darker shade of red, by maybe 2%".
                               "bloom": dict(art="hibiscus", pollen=(1.0, 0.86, 0.3),
                                             slots=[((0.93, 0.20, 0.15), (0.55, 0.03, 0.06)),
                                                    ((0.95, 0.40, 0.62), (0.62, 0.05, 0.2)),
                                                    ((1.0, 0.80, 0.18), (0.88, 0.18, 0.08)),
                                                    ((0.99, 0.93, 0.94), (0.9, 0.34, 0.52))],
                                             darken=0.02, petal_rim=0.18, petal_rim_w=0.07,
                                             petal_drop=0.5, petal_drop_off=0.08, petal_drop_blur=0.06),
                           }),
}


# The box shrub (her "a small box shrub that is just a singular one of these
# domes", 2026-09-28): one ice-cap dome in a boxwood's leaves, small (0.13 m,
# still chunky beside the azalea's 0.22), pointed ovals, dense, their tips a
# jagged rim; a faint midrib. Rounder leaves read as fish scales and bigger
# ones as an azalea (`documentation/screenshots/plant-lineup-2026-09-28/
# box_shrub_leaves.png`). No flowers.
PROP_LEAFLETS["box_shrub"] = dict(style="dome", rachis=(0.003, 0.001), rachis_colour=(0.40, 0.62, 0.18),
                                  rachis_tint=0.25, profile="ovate", kinds={
                                      "leaf": dict(leaf_m=0.13, width=0.32, shade=(0.62, 1.18), shadow=0.4,
                                                   rim_dark=0.3, gap=0.45, top=0.1, row_step=0.5),
                                  })


# The giant tree form wears the bush's leaf and blooms, the leaves scaled up
# with the shrubs' (her "scale up the leaves on the azalea tree too").
PROP_LEAFLETS["azalea_tree"] = PROP_LEAFLETS["azalea_bush"]
# A shrub's body (its one sphere or egg under the domes, `leaf_skin.py`) wears
# the same leaves as its domes.
for _shrub in ("azalea_bush", "hibiscus_shrub"):
    PROP_LEAFLETS[_shrub]["kinds"]["body"] = PROP_LEAFLETS[_shrub]["kinds"]["leaf"]
    PROP_LEAFLETS[_shrub]["kinds"]["tier"] = PROP_LEAFLETS[_shrub]["kinds"]["leaf"]  # a band round the body
    PROP_LEAFLETS[_shrub]["kinds"]["topper"] = PROP_LEAFLETS[_shrub]["kinds"]["leaf"]  # the leaves on its very top
    PROP_LEAFLETS[_shrub]["kinds"]["sprig"] = PROP_LEAFLETS[_shrub]["kinds"]["leaf"]  # its stray leaf groupings
# A shrub's buds (`leaf_skin.py`, her "flower buds need to be added"): the
# flowers' colourways, over a calyx of pointed sepals in `sepal`, sRGB.
PROP_LEAFLETS["azalea_bush"]["kinds"]["bud"] = dict(PROP_LEAFLETS["azalea_bush"]["kinds"]["bloom"], sepal=(0.40, 0.62, 0.22))
# Unopened azalea buds, light green, no colour showing yet (her "include some
# light green buds that dont show their color yet"): the same green in every
# colourway, so the slide leaves them green.
PROP_LEAFLETS["azalea_bush"]["kinds"]["bud_green"] = dict(
    PROP_LEAFLETS["azalea_bush"]["kinds"]["bud"],
    slots=[((0.72, 0.88, 0.44), (0.56, 0.76, 0.32))] * len(PROP_LEAFLETS["azalea_bush"]["kinds"]["bloom"]["slots"]))
PROP_LEAFLETS["hibiscus_shrub"]["kinds"]["bud"] = dict(PROP_LEAFLETS["hibiscus_shrub"]["kinds"]["bloom"],
                                                       sepal=(0.22, 0.46, 0.28))
# The shrubs' sphere versions (`leaf_skin.py`) wear their egg versions' leaves and flowers.
for _shrub in ("azalea_bush", "hibiscus_shrub", "azalea_tree"):
    PROP_LEAFLETS[f"{_shrub}_sphere"] = PROP_LEAFLETS[_shrub]


def ovate_leaf_profile(t):
    """A pointed oval from its stalk: rounding out to its widest two fifths of
    the way, full shoulders, then narrowing to a point."""
    rise = 0.25 + 0.75 * np.sqrt(np.clip(1.0 - (1.0 - np.clip(t / 0.4, 0.0, 1.0)) ** 2, 0.0, 1.0))
    fall = np.clip(1.0 - np.clip((t - 0.4) / 0.6, 0.0, 1.0) ** 1.6, 0.0, 1.0) ** 0.75
    return np.where(t < 0.4, rise, fall)


def toothed(profile, count, depth, style="scallop"):
    """`profile` with a toothed margin, `count` teeth a side, `depth` of the
    width deep, fading out at the stalk and the tip: "scallop", rounded teeth
    with a sharp notch between; "saw", sharp teeth leaning to the tip (a
    serrated hibiscus leaf)."""
    def cut(t):
        ramp = np.mod(t * count, 1.0)
        lobe = ramp ** 0.7 if style == "saw" else np.sqrt(np.sin(np.pi * ramp))
        fade = np.clip(t / 0.2, 0.0, 1.0) * np.clip((1.0 - t) / 0.08, 0.0, 1.0)
        return profile(t) * (1.0 - depth * fade * (1.0 - lobe))
    return cut


def lance_leaf_profile(t):
    """A leaf from its stalk: broad from the base, widest a third of the way,
    a soft point at the tip."""
    rise = np.sqrt(np.clip(t / 0.33, 0.0, 1.0))
    fall = np.clip(1.0 - np.clip((t - 0.33) / 0.67, 0.0, 1.0) ** 1.5, 0.0, 1.0) ** 0.85  # full shoulders
    return np.where(t < 0.33, 0.35 + 0.65 * rise, fall)


def cut_leaf(obj, kind, label, index, size, px_m, rng):
    """(leaf, midrib) for a blade that is one whole leaf on a card (the Purple
    Heart's): the leaf drawn up the card's middle, `fill` of its half-width at
    its widest, and the midrib."""
    straw, total, at, half_rachis, reach = frond(obj, label, index, size, px_m)
    leaf = np.zeros((size, size), dtype=np.float32)
    base, _ = at(0.0)
    tip, _ = at(total)
    half = obj.dimensions.x / 2 * px_m * LEAFLETS[kind]["fill"]
    teeth = LEAFLETS[kind].get("teeth")
    stroke(leaf, base, tip, half, toothed(leaflet_profile, *teeth) if teeth else leaflet_profile)
    tone = np.ones((size, size), dtype=np.float32)
    shade = LEAFLETS[kind].get("shade")
    if shade:
        # Darker at the stalk, lighter toward the tip, along the leaf.
        yy, xx = np.mgrid[0:size, 0:size]
        axis = (tip - base) / max(float(np.hypot(*(tip - base))), 1.0)
        along = np.clip(((xx - base[0]) * axis[0] + (yy - base[1]) * axis[1])
                        / max(float(np.hypot(*(tip - base))), 1.0), 0.0, 1.0)
        tone = np.where(label == index, shade[0] + (shade[1] - shade[0]) * along ** 0.8, 1.0).astype(np.float32)
    return leaf, straw * leaf, tone


def cut_cluster(obj, kind, label, index, size, px_m, rng):
    """(leaves, midribs, tone) for a card that is a clump of leaves merged into
    one piece (the bushes, 2026-09-28, her "the leafs need to be grouped and
    merged" and "texture creates the definition within the clusters"): `leaves`
    broad leaves fanning `spread` degrees from the stalk at the card's foot,
    the outer ones shorter and drawn first, the middle one last and on top.
    The clump is shaded as one lump, dark at its stalk to light at its far end
    (`shade`); inside it each leaf is a touch lighter or darker than the next
    and throws a thin shadow `shadow` deep on the leaves under it, and its
    midrib is pale: the definition is in the texture, the clump one shape."""
    spec = LEAFLETS[kind]
    mine = label == index
    ys, xs = np.nonzero(mine)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    base = np.array([(x0 + x1) / 2.0, y0 + 2.0])
    count = spec["leaves"]
    angles = np.linspace(-spec["spread"] / 2, spec["spread"] / 2, count) + rng.uniform(-4, 4, count)
    order = np.argsort(-np.abs(angles))  # outer first: each lies over those beside it
    yy, xx = np.mgrid[0:size, 0:size]
    leaves = np.zeros((size, size), dtype=np.float32)
    ribs = np.zeros((size, size), dtype=np.float32)
    lift = np.ones((size, size), dtype=np.float32)
    shadow = np.ones((size, size), dtype=np.float32)
    shadow_r = max(2, int(spec.get("shadow_m", 0.01) * px_m))
    profile = toothed(leaflet_profile, *spec["teeth"]) if spec.get("teeth") else leaflet_profile
    far = 1.0
    for i in order:
        a = np.radians(angles[i])
        direction = np.array([np.sin(a), np.cos(a)])
        reach = 0.0
        while True:  # out along the leaf until it leaves the card's island
            p = base + direction * (reach + 1.0)
            if not (0 <= int(p[0]) < size and 0 <= int(p[1]) < size) or label[int(p[1]), int(p[0])] != index:
                break
            reach += 1.0
        middle = 1.0 - abs(angles[i]) / (spec["spread"] / 2)
        length = reach * (spec["lengths"][0] + (spec["lengths"][1] - spec["lengths"][0]) * middle)
        far = max(far, length)
        tip = base + direction * length
        leaf = np.zeros((size, size), dtype=np.float32)
        stroke(leaf, base, tip, length * spec["width"], profile)
        rib = np.zeros((size, size), dtype=np.float32)
        stroke(rib, base + direction * length * 0.12, tip, spec.get("rib_px", 2.0), lambda t: 1.0 - 0.8 * t)
        near = box_blur2((leaf > 0.5).astype(np.float32), shadow_r)
        shadow = shadow * (1.0 - spec.get("shadow", 0.3) * np.clip(near * 2.0, 0.0, 1.0) * (1.0 - leaf) * leaves)
        own = 1.0 + rng.uniform(-0.07, 0.07)
        lift = lift * (1.0 - leaf) + own * leaf
        shadow = shadow * (1.0 - leaf) + leaf
        ribs = ribs * (1.0 - leaf) + rib * leaf
        leaves = np.maximum(leaves, leaf)
    along = np.clip(np.hypot(xx - base[0], yy - base[1]) / far, 0.0, 1.0)
    clump = spec["shade"][0] + (spec["shade"][1] - spec["shade"][0]) * along ** 0.8
    tone = clump * lift * shadow
    return leaves * mine, ribs * mine, np.where(mine, tone, 1.0).astype(np.float32)


def leaf_darkness(spec, vary):
    """A leaf's own darkness, times its colour (linear): up to `vary_dark`
    darker as the colour picker reads it, drawn from `vary` (its own random,
    so the leaves are laid out as before)."""
    return (1.0 - vary.uniform(0.0, spec.get("vary_dark", 0.0))) ** 2.2


def shift2(a, dx, dy):
    """`a` moved `dx`, `dy` px (to the nearest), nothing where it came from."""
    dx, dy = int(round(dx)), int(round(dy))
    h, w = a.shape
    out = np.zeros_like(a)
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = a[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def paint_leaf(state, start, direction, here, spec, profile, mine, xx, yy, rng, wide=1.0, warp=None, dark=1.0, down=None):
    """One leaf of a bush's greenery drawn over `state` (leaves, midribs,
    tone): from `start` along `direction`, `here` px long, `wide` times its
    width, as one stroke or as `lobes` (turn in degrees, share of the length,
    width share), each with its midrib (`rib_reach` of the way to its tip);
    nothing past the island (`mine`); with `warp`, drawn in a dome's own
    proportions (`stroke`). It is shaded stalk to tip (`shade`), a touch
    lighter or darker than the last, times `dark` (`leaf_darkness`), its rim
    `edge_light` lighter `edge_px` in from its outline, and throws a thin
    shadow `shadow` deep on the leaves already drawn under it, and with
    `drop` a soft shadow that deep `drop_px` on `down` the dome from it
    (`direction` if not given)."""
    leaves, ribs, tone = state
    size = leaves.shape[0]
    leaf = np.zeros((size, size), dtype=np.float32)
    rib = np.zeros((size, size), dtype=np.float32)
    for turn, reach_share, width_share in spec.get("lobes", [(0.0, 1.0, spec["width"])]):
        t = np.radians(turn)
        d = np.array([direction[0] * np.cos(t) - direction[1] * np.sin(t),
                      direction[0] * np.sin(t) + direction[1] * np.cos(t)])
        end = start + d * here * reach_share
        stroke(leaf, start, end, here * reach_share * width_share * wide, profile, warp)
        rib_end = start + d * here * reach_share * spec.get("rib_reach", 1.0)
        stroke(rib, start + d * here * 0.08, rib_end, spec.get("rib_px", 1.5), lambda t: 1.0 - 0.8 * t, warp)
    leaf *= mine
    solid = (leaf > 0.5).astype(np.float32)
    along = np.clip(((xx - start[0]) * direction[0] + (yy - start[1]) * direction[1]) / here, 0.0, 1.0)
    own = (spec["shade"][0] + (spec["shade"][1] - spec["shade"][0]) * along ** 0.8) * (1.0 + rng.uniform(-0.06, 0.06)) * dark
    if spec.get("edge_light"):
        inside = box_blur2(solid, max(1, int(round(spec["edge_px"]))))  # 1 well inside, a half at the outline
        own = own * (1.0 + spec["edge_light"] * np.clip((1.0 - inside) * 2.0, 0.0, 1.0))
    near = box_blur2(solid, max(2, int(spec.get("shadow_px", 8))))
    tone = tone * (1.0 - spec["shadow"] * np.clip(near * 2.0, 0.0, 1.0) * (1.0 - leaf) * leaves)
    if spec.get("drop"):
        off = (direction if down is None else down) * spec["drop_px"]
        cast = box_blur2(shift2(solid, off[0], off[1]), max(1, int(round(spec["drop_blur_px"]))))
        tone = tone * (1.0 - spec["drop"] * cast * (1.0 - leaf) * leaves)
    tone = tone * (1.0 - leaf) + own * leaf
    ribs = ribs * (1.0 - leaf) + rib * leaf
    return np.maximum(leaves, leaf), ribs, tone


def cut_dome(obj, kind, label, index, size, px_m, rng):
    """(leaves, midribs, tone) for a bush's semi-dome (`leaf_skin.py`, after
    the Mario Kart tree she pointed to: "our shrubs will be assembled from a
    series of these types of shapes and texture approaches"): its many leaves
    in rings round the apex, pointing out and down the dome, each ring nearer
    the apex laid over the one beyond like shingles and a few from the apex
    itself on top; the outer ring's tips are the rim. Under them the dome is
    filled with the leaves' shaded colour (`gap`), so it is seen through only
    between the rim's tips. The dome is lighter at its apex (`top`) and
    darker toward its rim (`rim_dark`), where it droops. A leaf is painted
    wider round the dome where the dome's girth is less than the canvas's
    (`kyt_rings`), so it is its own shape on the dome, and its splay holds
    (her "you need to address the way the leaf textures have been enlongated
    on the egg shapes": widened across its own length instead, a leaf low on
    an egg came out long and thin, hanging straight)."""
    spec = LEAFLETS[kind]
    mine = label == index
    ys, xs = np.nonzero(mine)
    centre = np.array([(xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0])
    # The rim is a polygon of `kyt_around` corners: tips stop inside its sides.
    rim = min(xs.max() - xs.min(), ys.max() - ys.min()) / 2.0 * np.cos(np.pi / int(obj.get("kyt_around", 8))) - TIP_INSET_PX
    length = spec["leaf_m"] * px_m
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.hypot(xx - centre[0], yy - centre[1])
    fill = np.clip(rim - length * spec.get("gap_short", 0.6) - dist + 0.5, 0.0, 1.0) * mine
    state = (fill.astype(np.float32), np.zeros((size, size), dtype=np.float32),
             np.where(fill > 0, spec.get("gap", 0.5), 1.0).astype(np.float32))
    profile = toothed(leaflet_profile, *spec["teeth"]) if spec.get("teeth") else leaflet_profile
    spec = dict(spec, shadow_px=spec.get("shadow_m", 0.008) * px_m, edge_px=spec.get("edge_m", 0.0) * px_m,
                drop_px=spec.get("drop_m", 0.0) * px_m, drop_blur_px=spec.get("drop_blur_m", 0.0) * px_m)
    col_step = length * spec.get("col_width", spec["width"] * 2.0) * spec.get("col_step", 0.8)
    # Each ring's (distance along the dome, radius), metres: painted width to
    # true width is the one over the other, 1 at the apex.
    girth = list(obj.data.get("kyt_rings", []))
    along = [0.0] + girth[0::2]
    widen = [1.0] + [s_ / max(r_, 1e-6) for s_, r_ in zip(girth[0::2], girth[1::2])]
    flat_px = (xs.max() - xs.min()) / 2.0 / max(along[-1], 1e-6)  # canvas px per metre along the dome
    rings = []
    ring = rim - length
    while ring > length * 0.35:
        rings.append(ring)
        ring -= length * spec.get("row_step", 0.55)
    rings.append(0.0)  # the apex's own leaves, on top
    vary = np.random.default_rng(zlib.crc32(("dark " + kind).encode()))
    for ring in rings:
        # As many as fit round the dome's own girth there.
        true = ring / (np.interp(ring / flat_px, along, widen) if girth else 1.0)
        count = spec.get("apex", 5) if ring == 0.0 else max(5, int(round(2 * np.pi * true / col_step)))
        turn = rng.uniform(0, 2 * np.pi)
        for j in range(count):
            a = turn + (j + rng.uniform(-0.15, 0.15)) / count * 2 * np.pi
            start = centre + np.array([np.cos(a), np.sin(a)]) * max(ring, length * 0.06)
            # Every other leaf splays `splay` degrees to one side and the next
            # to the other, a herringbone, so they don't all hang straight down
            # (her "in general the leaves look a bit too droopy").
            a += np.radians((1 if j % 2 else -1) * spec.get("splay", 0.0) + rng.uniform(-12, 12))
            direction = np.array([np.cos(a), np.sin(a)])
            # No longer than reaches the rim from here.
            p = start - centre
            reach = -p @ direction + np.sqrt(max((p @ direction) ** 2 - (p @ p - rim * rim), 0.0))
            here = min(length * rng.uniform(0.9, 1.05), reach)
            warp = (centre, lambda rho: np.interp(rho / flat_px, along, widen)) if girth else None
            out = start - centre
            state = paint_leaf(state, start, direction, here, spec, profile, mine, xx, yy, rng, 1.0, warp,
                               leaf_darkness(spec, vary), out / max(float(np.hypot(*out)), 1e-6))
    leaves, ribs, tone = state
    f = dist / rim
    tone = tone * (1.0 + spec.get("top", 0.0) * (1.0 - smooth(0.0, 0.55, f))) * (1.0 - spec.get("rim_dark", 0.0) * smooth(0.5, 1.0, f))
    return leaves * mine, ribs * mine, np.where(mine, tone, 1.0).astype(np.float32)


def cut_topper(obj, kind, label, index, size, px_m, rng):
    """(leaf, midrib, tone) for a shrub's topper card (`leaf_skin.py`, her
    "a little like two or three leaf topper"): one of the species' leaves, up
    the card's middle from its foot nearly to its top."""
    spec = LEAFLETS[kind]
    mine = label == index
    ys, xs = np.nonzero(mine)
    y0, y1 = ys.min(), ys.max()
    start = np.array([(xs.min() + xs.max()) / 2.0, y0 + 2.0])
    yy, xx = np.mgrid[0:size, 0:size]
    profile = toothed(leaflet_profile, *spec["teeth"]) if spec.get("teeth") else leaflet_profile
    state = (np.zeros((size, size), dtype=np.float32), np.zeros((size, size), dtype=np.float32),
             np.ones((size, size), dtype=np.float32))
    spec = dict(spec, shadow_px=2, shadow=0.0, drop=0.0, edge_px=spec.get("edge_m", 0.0) * px_m)
    leaves, ribs, tone = paint_leaf(state, start, np.array([0.0, 1.0]), (y1 - y0) * 0.96, spec, profile, mine, xx, yy, rng,
                                    spec.get("topper_wide", 1.0))
    return leaves * mine, ribs * mine, np.where(mine, tone, 1.0).astype(np.float32)


def slot_step(obj, size):
    """How far along the canvas, in pixels, each next colourway of a slotted
    blade (the bloom card) is painted: the canvas's width over its slots."""
    return size // int(obj.get("kyt_slots", 1))


def copy_steps(obj, size):
    """Every copy of a slotted blade's island, (colourway, shade, pixels
    along the canvas): each colourway `slot_step` from the last, and inside
    its slot each of the card's shades (`kyt_shades`) a `1 / (slots x
    shades)` of the canvas from the last, as `leaf_skin.py` slides each
    flower's UVs (to the nearest pixel)."""
    slots, shades = int(obj.get("kyt_slots", 1)), int(obj.get("kyt_shades", 1))
    return [(k, j, k * slot_step(obj, size) + int(round(j * size / (slots * shades))))
            for k in range(slots) for j in range(shades)]


def bloom_shade(spec, k, j, shades):
    """Colourway `k`'s (petal, throat), sRGB, in shade `j` of `shades`,
    0 the lightest: from `light` through the colourway to `dark`, `spread`
    of the way out to each, or from the colourway to `darken` darker."""
    petal, heart = spec["slots"][k]
    t = j / (shades - 1) if shades > 1 else 0.0
    if "light" in spec and shades > 1:
        t = 0.5 + (t - 0.5) * spec.get("spread", 1.0)
        a, b = (spec["light"][k], (petal, heart)) if t < 0.5 else ((petal, heart), spec["dark"][k])
        f = t * 2.0 if t < 0.5 else t * 2.0 - 1.0
        return tuple(tuple(x + (y - x) * f for x, y in zip(a[m], b[m])) for m in (0, 1))
    dim = 1.0 - spec.get("darken", 0.0) * t
    return tuple(c * dim for c in petal), tuple(c * dim for c in heart)


def cut_bloom(obj, kind, label, index, size, px_m, rng):
    """(alpha, nothing, no tone, paint) for the flowers' card, drawn once per
    colourway in `slots` and shade (`copy_steps`, `bloom_shade`): the card's
    own island first, the rest to its right. `paint` is the colour, linear."""
    spec = LEAFLETS[kind]
    step = slot_step(obj, size) // int(obj.get("kyt_shades", 1))  # the card's own island is inside the first
    mine0 = (label == index) & (np.arange(size)[None, :] < step)
    ys, xs = np.nonzero(mine0)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    centre = np.array([(x0 + x1) / 2.0, (y0 + y1) / 2.0])
    R = min(x1 - x0, y1 - y0) / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    lin = lambda c: np.array([srgb_to_linear(v) for v in c], dtype=np.float32)  # noqa: E731
    shape = np.zeros((size, size), dtype=np.float32)
    throat = np.zeros((size, size), dtype=np.float32)  # 1 at a bloom's heart, 0 at its petal tips
    edge = np.ones((size, size), dtype=np.float32)
    extra = np.zeros((size, size), dtype=np.float32)  # the hibiscus's stamens
    rim = np.zeros((size, size), dtype=np.float32)  # 1 at a petal's own outline
    if spec["art"] == "truss":
        # A rounded bunch: blooms of mixed sizes round one in the middle, off
        # a regular ring, each round the edge squashed along the line from
        # the middle (turned away from the eye) so the bunch reads as a ball,
        # not a flat rosette (her "the clusters are a little funny").
        count = int(rng.integers(6, 9))
        spots = []
        for a in np.linspace(0, 2 * np.pi, count, endpoint=False) + rng.uniform(0, 2 * np.pi):
            out = np.array([np.cos(a), np.sin(a)])
            reach = R * rng.uniform(0.45, 0.62)
            spots.append((centre + out * reach, R * 0.4 * rng.uniform(0.75, 1.05), out, 0.62))
        spots.sort(key=lambda sp: -sp[1])  # the big ones first: the smaller lie over them at the rim
        spots.append((centre + rng.uniform(-0.06, 0.06, 2) * R, R * 0.46, np.zeros(2), 1.0))
        for c, r, out, squash in spots:
            bloom = np.zeros((size, size), dtype=np.float32)
            turn = rng.uniform(0, 2 * np.pi)
            for k in range(5):
                a = turn + k / 5 * 2 * np.pi
                d = np.array([np.cos(a), np.sin(a)])
                along_out = abs(float(d @ out))
                reach = r * (1.0 - (1.0 - squash) * along_out)
                stroke(bloom, c, c + d * reach, r * 0.46 * (1.0 - 0.25 * (1.0 - squash) * along_out), leaflet_profile)
            near = box_blur2((bloom > 0.5).astype(np.float32), max(2, int(r * 0.12)))
            edge = edge * (1.0 - 0.35 * np.clip(near * 2.0, 0.0, 1.0) * (1.0 - bloom) * shape)
            heart = np.clip(1.0 - np.hypot(xx - c[0], yy - c[1]) / (r * 0.45), 0.0, 1.0)
            throat = throat * (1.0 - bloom) + heart * bloom
            edge = edge * (1.0 - bloom) + bloom
            shape = np.maximum(shape, bloom)
        # Darker toward the bunch's lower rim, lighter on top.
        edge = edge * (1.0 - 0.18 * smooth(0.3, 1.0, np.clip((centre[1] - yy) / R, 0.0, 1.0)))
    elif spec["art"] == "azalea":
        # Five broad pointed petals round a deep throat, the top one
        # speckled, and long stamens curving up over it, tipped dark.
        turn = rng.uniform(0, 2 * np.pi)
        for k in range(5):
            a = turn + k / 5 * 2 * np.pi
            petal = np.zeros((size, size), dtype=np.float32)
            stroke(petal, centre, centre + np.array([np.cos(a), np.sin(a)]) * R * 0.97, R * 0.5, ovate_leaf_profile)
            near = box_blur2((petal > 0.5).astype(np.float32), max(2, int(R * 0.06)))
            edge = edge * (1.0 - 0.3 * np.clip(near * 2.0, 0.0, 1.0) * (1.0 - petal) * shape)
            edge = edge * (1.0 - petal) + petal
            shape = np.maximum(shape, petal)
        throat = np.clip(1.0 - np.hypot(xx - centre[0], yy - centre[1]) / (R * 0.4), 0.0, 1.0) ** 0.8
        top = np.array([np.cos(turn), np.sin(turn)])
        for _ in range(9):
            at = centre + (top * rng.uniform(0.18, 0.55) + np.array([-top[1], top[0]]) * rng.uniform(-0.18, 0.18)) * R
            spot = np.clip(1.0 - np.hypot(xx - at[0], yy - at[1]) / max(1.2, R * 0.06), 0.0, 1.0)
            throat = np.maximum(throat, spot)
        for k in range(5):
            a = turn + rng.uniform(-0.5, 0.5)
            tip = centre + np.array([np.cos(a), np.sin(a)]) * R * rng.uniform(0.6, 0.8)
            stroke(extra, centre, tip, max(1.0, R * 0.025), lambda t: np.ones_like(t))
            stroke(extra, tip, tip + np.array([np.cos(a), np.sin(a)]) * R * 0.06, max(1.5, R * 0.05), lambda t: 1.0 - t)
    else:  # one hibiscus
        # With `petal_rim` (the leaves' treatment, her "do a similar
        # treatment for the petals of the flowers"): each petal's rim that
        # much of the way to white `petal_rim_w` of the flower's radius in
        # from its outline, and a soft shadow `petal_drop` deep cast back on
        # the petal it overlaps, `petal_drop_off` of the radius round.
        turn = rng.uniform(0, 2 * np.pi)
        for k in range(5):
            a = turn + k / 5 * 2 * np.pi
            petal = np.zeros((size, size), dtype=np.float32)
            stroke(petal, centre, centre + np.array([np.cos(a), np.sin(a)]) * R * 0.98, R * 0.52, round_leaflet_profile)
            solid = (petal > 0.5).astype(np.float32)
            near = box_blur2(solid, max(2, int(R * 0.05)))
            edge = edge * (1.0 - 0.3 * np.clip(near * 2.0, 0.0, 1.0) * (1.0 - petal) * shape)
            if spec.get("petal_drop"):
                back = np.array([np.sin(a), -np.cos(a)]) * R * spec["petal_drop_off"]  # round toward the petal before
                cast = box_blur2(shift2(solid, back[0], back[1]), max(1, int(round(R * spec["petal_drop_blur"]))))
                edge = edge * (1.0 - spec["petal_drop"] * cast * (1.0 - petal) * shape)
            if spec.get("petal_rim"):
                inside = box_blur2(solid, max(1, int(round(R * spec["petal_rim_w"]))))
                rim = rim * (1.0 - petal) + petal * np.clip((1.0 - inside) * 2.0, 0.0, 1.0)
            edge = edge * (1.0 - petal) + petal
            shape = np.maximum(shape, petal)
        throat = np.clip(1.0 - np.hypot(xx - centre[0], yy - centre[1]) / (R * 0.42), 0.0, 1.0) ** 0.8
        tip = centre + np.array([0.12, 0.4]) * R
        stroke(extra, centre, tip, max(1.5, R * 0.035), lambda t: np.ones_like(t))
        for k in range(6):
            a = k / 6 * 2 * np.pi
            stroke(extra, tip, tip + np.array([np.cos(a), np.sin(a)]) * R * 0.07, R * 0.05, lambda t: 1.0 - t)
    paint = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)
    shades = int(obj.get("kyt_shades", 1))
    for k, j, along in copy_steps(obj, size):
        petal, heart = bloom_shade(spec, k, j, shades)
        colour = lin(petal)[None, None, :] * (1.0 - throat[..., None]) + lin(heart)[None, None, :] * throat[..., None]
        colour = colour * edge[..., None]
        light = (spec.get("petal_rim", 0.0) * rim * (1.0 - throat))[..., None]
        colour = colour + (1.0 - colour) * light
        if spec["art"] == "hibiscus":
            colour = colour * (1.0 - extra[..., None]) + lin(spec["pollen"])[None, None, :] * extra[..., None]
        elif spec["art"] == "azalea":
            colour = colour * (1.0 - extra[..., None]) + lin(heart)[None, None, :] * 0.8 * extra[..., None]
        shifted = np.roll(colour, along, axis=1)
        region = np.roll(shape * mine0, along, axis=1) > 0
        paint[region] = shifted[region]
        alpha = np.maximum(alpha, np.roll(shape * mine0, along, axis=1))
    return alpha, np.zeros((size, size), dtype=np.float32), np.ones((size, size), dtype=np.float32), paint


def cut_bud(obj, kind, label, index, size, px_m, rng):
    """(alpha, nothing, no tone, paint) for a shrub's bud (`leaf_skin.py`,
    `bud_card`, laid out flat as seen from the side, its foot at the bottom):
    a calyx of pointed sepals from its foot, then the flower's colour up to
    its point, deeper low down; once per colourway in `slots`, as the
    flowers' card is. The whole island is opaque."""
    spec = LEAFLETS[kind]
    step = slot_step(obj, size)
    mine0 = (label == index) & (np.arange(size)[None, :] < step)
    ys, xs = np.nonzero(mine0)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    yy, xx = np.mgrid[0:size, 0:size]
    t = np.clip((yy - y0) / max(1, y1 - y0), 0.0, 1.0)  # 0 at its foot, 1 at its point
    across = np.clip((xx - x0) / max(1, x1 - x0), 0.0, 1.0)
    tooth = 1.0 - np.abs(2.0 * ((across * 2.0) % 1.0) - 1.0)  # two sepal points across a face
    top = 0.36 + 0.24 * tooth
    sepal = smooth(top + 0.02, top - 0.02, t)
    rim = np.clip(1.0 - np.abs(t - top) / 0.03, 0.0, 1.0) * (t < top + 0.03)  # a dark line at the sepals' edge
    lin = lambda c: np.array([srgb_to_linear(v) for v in c], dtype=np.float32)  # noqa: E731
    deep = smooth(0.3, 0.95, t)[..., None]
    paint = np.zeros((size, size, 3), dtype=np.float32)
    for k, (petal, heart) in enumerate(spec["slots"]):
        colour = lin(heart)[None, None, :] * (1.0 - deep) + lin(petal)[None, None, :] * deep
        colour = colour * (1.0 - sepal[..., None]) + lin(spec["sepal"])[None, None, :] * sepal[..., None]
        colour = colour * (1.0 - 0.35 * rim[..., None])
        region = np.roll(mine0, k * step, axis=1)
        paint[region] = np.roll(colour, k * step, axis=1)[region]
    alpha = np.zeros((size, size), dtype=np.float32)
    for k in range(len(spec["slots"])):
        alpha = np.maximum(alpha, np.roll(mine0, k * step, axis=1).astype(np.float32))
    return alpha, np.zeros((size, size), dtype=np.float32), np.ones((size, size), dtype=np.float32), paint


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def round_leaflet_profile(t):
    """A lobe: out from the rachis, widest a little before halfway, a round end."""
    widest = 0.4
    rise = 0.6 + 0.4 * np.sqrt(np.clip(t / widest, 0.0, 1.0))
    fall = np.sqrt(np.clip(1.0 - ((t - widest) / (1.0 - widest)) ** 2, 0.0, 1.0))
    return np.where(t < widest, rise, fall)


def use_prop_leaflets(name):
    """The prop's own leaflet table in place of the palm crown's, if it has one."""
    global CUT_STYLE, LEAFLETS, RACHIS_M, RACHIS_STRAW, RACHIS_TINT, LEAFLET_SLENDER, LEAFLET_JITTER
    global leaflet_profile
    spec = PROP_LEAFLETS.get(name)
    if spec is not None:
        CUT_STYLE, LEAFLETS = spec["style"], spec["kinds"]
        RACHIS_M, RACHIS_STRAW, RACHIS_TINT = spec["rachis"], spec["rachis_colour"], spec["rachis_tint"]
        LEAFLET_SLENDER = spec.get("slender", LEAFLET_SLENDER)
        LEAFLET_JITTER = spec.get("jitter", LEAFLET_JITTER)
        if spec.get("profile") == "round":
            leaflet_profile = round_leaflet_profile
        elif spec.get("profile") == "lance":
            leaflet_profile = lance_leaf_profile
        elif spec.get("profile") == "ovate":
            leaflet_profile = ovate_leaf_profile

# `--bands`, the segmented palm trunk (PRP-COAST-007, 2026-09-27), after
# Christina's two references (`documentation/reference/palm_trunk/`): each
# segment dark reddish brown at its base, tucked under the collar below, warm
# tan above a scalloped line whose points hang down into the dark, pale straw
# at its own collar. The collar's teeth, over the next segment's dark base,
# make the other edge of the zigzag. sRGB, as painted. `s` is the share of the
# way up a segment's band (`kyt_band_zones` on the mesh say where its rings
# fall); `u` the share of the way round.
BAND_DARK = (0.60, 0.35, 0.20)
BAND_TAN = (0.80, 0.58, 0.32)
BAND_RIM = (0.90, 0.75, 0.49)  # the collar's outer rim, catching the light
BAND_COLLAR_TOP = (0.78, 0.62, 0.40)  # where the collar turns in to the next segment
BAND_EDGE = 0.6  # the dark-to-tan line, at the teeth's roots
BAND_TEETH = 7  # scallops round the trunk
BAND_TOOTH = 0.14  # how far a scallop's point hangs below the line
BAND_RIM_FROM = 0.72  # the tan lightens toward the rim from here
BAND_SHADE = 0.18  # how much darker the very base is, tucked under the collar
BAND_FIBRES, BAND_FIBRE_DARK = 90, 0.05  # faint streaks up the segment: how many round, how much darker
BAND_MOTTLE = 0.05
BAND_ROUGH = 0.92
# The bump (`<prop>_bump.png`, greyscale height, hers to paint; the normal map
# the game reads is made from it, `tools/bump_to_normal.py`): the tan sheath
# stands a step proud of the dark husk, so the scallop edge catches the light;
# rounded fibres run up the segment, coarser in the dark; the collar's rim is a
# raised lip. Heights 0..1, 0.5 level.
BUMP_DARK, BUMP_TAN = 0.36, 0.6
BUMP_FIBRE_DARK, BUMP_FIBRE_TAN = 0.16, 0.07  # a fibre's rounded rise
BUMP_FIBRES = 60  # fibres round the trunk in the bump; the colour's streaks are finer
BUMP_RIM = 0.16  # the collar's lip, rising over the last stretch before the rim
BUMP_MOTTLE = 0.05


def arg(argv, name, default):
    return int(argv[argv.index(name) + 1]) if name in argv else default


def sock(sockets, identifier):
    """A socket by identifier: a Mix node's A, B and Result come once per type."""
    return next(x for x in sockets if x.identifier == identifier)


class Nodes:
    """Small shader-building vocabulary for one material's node tree. Every node
    it makes is remembered, so a bake can take them all away again."""

    def __init__(self, nt):
        self.nt, self.made = nt, []
        self.coord = self.node("ShaderNodeTexCoord").outputs["Object"]

    def node(self, kind):
        n = self.nt.nodes.new(kind)
        self.made.append(n)
        return n

    def link(self, a, b):
        self.nt.links.new(a, b)

    def math(self, op, a, b=0.0):
        m = self.node("ShaderNodeMath")
        m.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                self.link(v, m.inputs[i])
        return m.outputs[0]

    def ramp(self, value, lo, hi):
        """0 below `lo`, 1 above `hi`, straight between: a soft threshold."""
        return self.math("MINIMUM", self.math("MAXIMUM", self.math(
            "DIVIDE", self.math("SUBTRACT", value, lo), hi - lo), 0.0), 1.0)

    def lerp(self, a, b, t):
        return self.math("ADD", a, self.math("MULTIPLY", self.math("SUBTRACT", b, a), t))

    def noise(self, scale_xyz, detail=2.0):
        """Noise in 0-1 over the object, `scale_xyz` cycles per metre per axis."""
        m = self.node("ShaderNodeMapping")
        m.inputs["Scale"].default_value = scale_xyz
        self.link(self.coord, m.inputs["Vector"])
        t = self.node("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = 1.0
        t.inputs["Detail"].default_value = detail
        self.link(m.outputs["Vector"], t.inputs["Vector"])
        return t.outputs["Fac"]

    def wobble(self, scale_xyz, detail, strength):
        """Noise centred on zero, times strength."""
        return self.math("MULTIPLY", self.math("SUBTRACT", self.noise(scale_xyz, detail), 0.5),
                         strength)

    def mix(self, a, b, factor, blend="MIX"):
        m = self.node("ShaderNodeMix")
        m.data_type = "RGBA"
        m.blend_type = blend
        for identifier, v in (("A_Color", a), ("B_Color", b)):
            if isinstance(v, tuple):
                sock(m.inputs, identifier).default_value = v
            else:
                self.link(v, sock(m.inputs, identifier))
        if isinstance(factor, (int, float)):
            m.inputs["Factor"].default_value = factor
        else:
            self.link(factor, m.inputs["Factor"])
        return sock(m.outputs, "Result_Color")

    def grey(self, value):
        c = self.node("ShaderNodeCombineColor")
        for ch in ("Red", "Green", "Blue"):
            self.link(value, c.inputs[ch])
        return c.outputs["Color"]

    def rgb(self, r, g, b):
        c = self.node("ShaderNodeCombineColor")
        for ch, v in zip(("Red", "Green", "Blue"), (r, g, b)):
            if isinstance(v, (int, float)):
                c.inputs[ch].default_value = v
            else:
                self.link(v, c.inputs[ch])
        return c.outputs["Color"]


def wood_grain(g, base):
    """A colour socket: `base` as solid wood, rings round the x axis."""
    xyz = g.node("ShaderNodeSeparateXYZ")
    g.link(g.coord, xyz.inputs["Vector"])
    dy = g.math("SUBTRACT", xyz.outputs["Y"], PITH_YZ[0])
    dz = g.math("SUBTRACT", xyz.outputs["Z"], PITH_YZ[1])
    # Distance from the pith, bent by broad figure and a finer wobble.
    r = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", dy, dy), g.math("MULTIPLY", dz, dz)))
    r = g.math("ADD", r, g.wobble((0.6, 4.0, 4.0), 3.0, 0.05))
    r = g.math("ADD", r, g.wobble((2.5, 40.0, 40.0), 2.0, 0.006))
    # Knots at KNOTS, on the parts `kyt_knots` names: distance to the nearest,
    # stretched along the grain. Rings bulge round each.
    knots = g.node("ShaderNodeAttribute")
    knots.attribute_type = "GEOMETRY"
    knots.attribute_name = "kyt_knots"
    has = knots.outputs["Fac"]
    d = None
    for k in KNOTS:
        off = g.node("ShaderNodeVectorMath")
        off.operation = "SUBTRACT"
        g.link(g.coord, off.inputs[0])
        off.inputs[1].default_value = k
        stretch = g.node("ShaderNodeVectorMath")
        stretch.operation = "MULTIPLY"
        g.link(off.outputs["Vector"], stretch.inputs[0])
        stretch.inputs[1].default_value = (1 / KNOT_ALONG_M, 1 / KNOT_ACROSS_M, 1 / KNOT_ACROSS_M)
        length = g.node("ShaderNodeVectorMath")
        length.operation = "LENGTH"
        g.link(stretch.outputs["Vector"], length.inputs[0])
        d = length.outputs["Value"] if d is None else g.math("MINIMUM", d, length.outputs["Value"])
    if d is None:
        d = 9.0  # no knots listed
    near = g.math("SUBTRACT", 1.0, g.ramp(d, 0.0, 0.9))
    r = g.math("ADD", r, g.math("MULTIPLY", g.math("MULTIPLY", near, near),
                                g.math("MULTIPLY", has, KNOT_BULGE_M)))
    core = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.ramp(d, KNOT_CORE * 0.85, KNOT_CORE)), has)
    # Inside the knot, its own rings and a darker rim; round it, the grain darkens.
    rim = g.math("MULTIPLY", g.ramp(d, KNOT_CORE * 0.6, KNOT_CORE * 0.9), core)
    own = g.math("MULTIPLY", g.ramp(g.math("FRACT", g.math("DIVIDE", d, KNOT_RING)), 0.55, 0.8), core)
    knot_shade = g.math("SUBTRACT", g.lerp(1.0, KNOT_DARK, core),
                        g.math("ADD", g.math("MULTIPLY", rim, 0.15), g.math("MULTIPLY", own, 0.08)))
    knot_shade = g.math("MULTIPLY", knot_shade, g.math("SUBTRACT", 1.0, g.math(
        "MULTIPLY", g.math("MULTIPLY", near, has), 0.15)))
    ring = g.math("FRACT", g.math("DIVIDE", r, RING_M))
    # Earlywood most of the ring, a darker latewood band with soft edges.
    ramp = g.node("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (EARLY,) * 3 + (1.0,)
    els[1].position, els[1].color = 0.62, (EARLY,) * 3 + (1.0,)
    e = els.new(0.82)
    e.color = (LATE,) * 3 + (1.0,)
    e = els.new(0.97)
    e.color = (EARLY,) * 3 + (1.0,)
    g.link(ring, ramp.inputs["Fac"])
    # Fine streaks along the grain and a slow change in tone along each board.
    shade = g.math("ADD", 1.0, g.wobble((3.0, 350.0, 350.0), 1.0, 0.16))
    shade = g.math("MULTIPLY", shade, g.math("ADD", 1.0, g.wobble((1.2, 8.0, 8.0), 2.0, 0.18)))
    wood = g.mix(base, ramp.outputs["Color"], 1.0, "MULTIPLY")
    wood = g.mix(wood, g.grey(shade), 1.0, "MULTIPLY")
    return g.mix(wood, g.grey(knot_shade), 1.0, "MULTIPLY")


def seat_wear(g):
    """0-1: how worn the wood is, on the parts `kyt_wear` names. The boards' top
    edges wear where people sit, the front board's rounded front edge most,
    where legs rub; smooth, in streaks along the board."""
    mask = g.node("ShaderNodeAttribute")
    mask.attribute_type = "GEOMETRY"
    mask.attribute_name = "kyt_wear"
    at = g.node("ShaderNodeSeparateXYZ")
    g.link(g.coord, at.inputs["Vector"])
    geo = g.node("ShaderNodeNewGeometry")
    bevel = g.node("ShaderNodeBevel")
    bevel.inputs["Radius"].default_value = WEAR_EDGE_M
    turn = g.node("ShaderNodeVectorMath")
    turn.operation = "DOT_PRODUCT"
    g.link(geo.outputs["True Normal"], turn.inputs[0])
    g.link(bevel.outputs["Normal"], turn.inputs[1])
    edge = g.ramp(g.math("SUBTRACT", 1.0, turn.outputs["Value"]), 0.01, 0.15)
    top = g.ramp(at.outputs["Z"], SEAT_TOP_Z - 0.03, SEAT_TOP_Z - 0.005)
    # The front board's front edge, where legs rub: a band measured round the
    # edge itself, so it covers the top and the front alike.
    dy = g.math("SUBTRACT", at.outputs["Y"], FRONT_Y)
    dz = g.math("SUBTRACT", at.outputs["Z"], SEAT_TOP_Z)
    arris = g.ramp(g.math("SQRT", g.math("ADD", g.math("MULTIPLY", dy, dy), g.math("MULTIPLY", dz, dz))),
                   ARRIS_M, 0.005)
    where = g.math("MAXIMUM", g.math("MULTIPLY", g.math("MULTIPLY", edge, top), 0.3), arris)
    # Where people sit: the two seats, and a little in the middle.
    off = g.math("ABSOLUTE", g.math("SUBTRACT", g.math("ABSOLUTE", at.outputs["X"]), SEATS_X))
    seated = g.math("MAXIMUM", g.ramp(off, SEAT_SPREAD_M, 0.05),
                    g.math("MULTIPLY", g.ramp(g.math("ABSOLUTE", at.outputs["X"]), 0.25, 0.0), 0.5))
    streaks = g.ramp(g.noise((3.0, 50.0, 50.0), 3.0), 0.25, 0.65)
    return g.math("MULTIPLY", g.math("MULTIPLY", g.math("MULTIPLY", where, seated), streaks),
                  mask.outputs["Fac"])

def weathering(g, base, rough, metal):
    """(colour, roughness, metalness) sockets for painted iron, weathered where the
    face attribute `kyt_weather` is 1 and as it was where it is 0."""
    weather = g.node("ShaderNodeAttribute")
    weather.attribute_type = "GEOMETRY"
    weather.attribute_name = "kyt_weather"
    w = weather.outputs["Fac"]
    geo = g.node("ShaderNodeNewGeometry")
    n = geo.outputs["Normal"]
    up_xyz = g.node("ShaderNodeSeparateXYZ")
    g.link(n, up_xyz.inputs["Vector"])
    up = g.ramp(up_xyz.outputs["Z"], 0.3, 0.9)  # faces the sky
    # Edges: how far the normal a few millimetres round the surface turns away.
    bevel = g.node("ShaderNodeBevel")
    bevel.inputs["Radius"].default_value = CHIP_EDGE_M
    turn = g.node("ShaderNodeVectorMath")
    turn.operation = "DOT_PRODUCT"
    g.link(n, turn.inputs[0])
    g.link(bevel.outputs["Normal"], turn.inputs[1])
    edge = g.ramp(g.math("SUBTRACT", 1.0, turn.outputs["Value"]), 0.0, 0.08)
    # Chips where an edge and a patchy noise agree; rust round each chip, and
    # streaking down the sides below.
    patch = g.noise((45.0, 45.0, 45.0), 6.0)
    knock = g.math("ADD", g.math("MULTIPLY", edge, 0.8), patch)
    chip = g.ramp(knock, 1.0, 1.1)
    halo = g.math("MAXIMUM", g.math("SUBTRACT", g.ramp(knock, 0.8, 0.98), chip), 0.0)
    streaks = g.node("ShaderNodeAttribute")
    streaks.attribute_type = "GEOMETRY"
    streaks.attribute_name = "kyt_streaks"
    streak = g.math("MULTIPLY", g.ramp(g.noise((30.0, 30.0, 2.5), 2.0), 0.58, 0.78),
                    g.math("MULTIPLY", g.math("SUBTRACT", 1.0, up),
                           g.math("MULTIPLY", streaks.outputs["Fac"], STREAKS)))
    hand = g.math("MULTIPLY", up, g.ramp(g.noise((6.0, 6.0, 6.0), 3.0), 0.42, 0.6))
    bare = g.math("MULTIPLY", g.math("MAXIMUM", chip, g.math("MULTIPLY", hand, HAND_WEAR)), w)
    # Rust and dirt climbing from the paving: full at the ground, gone GROUND_M up.
    at = g.node("ShaderNodeSeparateXYZ")
    g.link(g.coord, at.inputs["Vector"])
    ground = g.ramp(at.outputs["Z"], GROUND_M, 0.0)
    ground_rust = g.math("MULTIPLY", g.math("MULTIPLY", ground, GROUND_RUST),
                         g.ramp(g.noise((20.0, 20.0, 6.0), 3.0), 0.35, 0.65))
    rust = g.math("MULTIPLY", g.math("MAXIMUM", g.math("MAXIMUM", halo, streak), ground_rust), w)
    # Grime where the surface is hemmed in by other parts, and splashed up from the ground.
    ao = g.node("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.03
    ao.samples = 16
    hemmed = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), g.math("MULTIPLY", ground, 0.5))
    grime = g.math("MULTIPLY", hemmed, g.math("MULTIPLY", w, GRIME))

    colour = g.mix(base, FADED, g.math("MULTIPLY", up, g.math("MULTIPLY", w, FADE)))
    colour = g.mix(colour, RUST, rust)
    colour = g.mix(colour, BARE_IRON, bare)
    colour = g.mix(colour, g.grey(g.math("SUBTRACT", 1.0, grime)), 1.0, "MULTIPLY")
    r = g.lerp(g.lerp(rough, RUST_ROUGH, rust), BARE_ROUGH, bare)
    m = g.lerp(g.lerp(metal, RUST_METAL, rust), BARE_METAL, bare)
    return colour, r, m


def chipping(g, colour, rough, metal):
    """(colour, roughness, metalness) with a few chips of bare iron along the
    edges, where the face attribute `kyt_chips` is 1; unchanged elsewhere."""
    chips = g.node("ShaderNodeAttribute")
    chips.attribute_type = "GEOMETRY"
    chips.attribute_name = "kyt_chips"
    # An edge: the flat face's own normal against the normal rounded over a few
    # millimetres, which turns wherever the surface does, even between the
    # facets of a smooth-shaded tube.
    geo = g.node("ShaderNodeNewGeometry")
    bevel = g.node("ShaderNodeBevel")
    bevel.inputs["Radius"].default_value = CHIP_EDGE_M
    turn = g.node("ShaderNodeVectorMath")
    turn.operation = "DOT_PRODUCT"
    g.link(geo.outputs["True Normal"], turn.inputs[0])
    g.link(bevel.outputs["Normal"], turn.inputs[1])
    edge = g.ramp(g.math("SUBTRACT", 1.0, turn.outputs["Value"]), 0.01, 0.05)
    # `kyt_chips` is each part's density: 1 chips at CHIP_LEVEL, less asks the
    # patchiness to reach higher, so fewer chips; 0 is no chips at all.
    density = chips.outputs["Fac"]
    level = g.math("ADD", CHIP_LEVEL, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, density), CHIP_THIN))
    size = 1.0 / CHIP_SIZE_M
    patch = g.math("MINIMUM", g.math("MAXIMUM", g.math("DIVIDE", g.math(
        "SUBTRACT", g.noise((size, size, size), 6.0), level), 0.02), 0.0), 1.0)
    chipped = g.math("GREATER_THAN", density, 0.0)
    chip = g.math("MULTIPLY", g.math("MULTIPLY", edge, patch), chipped)
    # Dings: the same bare iron, anywhere on a surface facing the sky, on the
    # parts `kyt_dings` names (its value their density, as for chips).
    dings = g.node("ShaderNodeAttribute")
    dings.attribute_type = "GEOMETRY"
    dings.attribute_name = "kyt_dings"
    ding_density = dings.outputs["Fac"]
    up_xyz = g.node("ShaderNodeSeparateXYZ")
    g.link(geo.outputs["Normal"], up_xyz.inputs["Vector"])
    up = g.ramp(up_xyz.outputs["Z"], 0.4, 0.8)
    ding_level = g.math("ADD", DING_LEVEL, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ding_density), CHIP_THIN))
    ding_size = 1.0 / DING_SIZE_M
    ding_patch = g.math("MINIMUM", g.math("MAXIMUM", g.math("DIVIDE", g.math(
        "SUBTRACT", g.noise((ding_size, ding_size, ding_size), 6.0), ding_level), 0.02), 0.0), 1.0)
    ding = g.math("MULTIPLY", g.math("MULTIPLY", up, ding_patch), g.math("GREATER_THAN", ding_density, 0.0))
    chip = g.math("MAXIMUM", chip, ding)
    return (g.mix(colour, CHIP_IRON, chip), g.lerp(rough, CHIP_ROUGH, chip),
            g.lerp(metal, CHIP_METAL, chip))


def grounding(g, colour, rough, metal):
    """(colour, roughness, metalness) with rust and dirt climbing from the paving,
    full at the ground and gone GROUND_M up, where the face attribute
    `kyt_ground` is 1; unchanged elsewhere."""
    mask = g.node("ShaderNodeAttribute")
    mask.attribute_type = "GEOMETRY"
    mask.attribute_name = "kyt_ground"
    at = g.node("ShaderNodeSeparateXYZ")
    g.link(g.coord, at.inputs["Vector"])
    ground = g.math("MULTIPLY", g.ramp(at.outputs["Z"], GROUND_M, 0.0), mask.outputs["Fac"])
    rust = g.math("MULTIPLY", g.math("MULTIPLY", ground, GROUND_RUST),
                  g.ramp(g.noise((20.0, 20.0, 6.0), 3.0), 0.35, 0.65))
    dirt = g.math("MULTIPLY", ground, GROUND_DIRT)
    # A few darker spots of dirt splashed up, only near the ground.
    low = g.math("MULTIPLY", g.ramp(at.outputs["Z"], DIRT_REACH_M, DIRT_REACH_M / 2), mask.outputs["Fac"])
    spot_size = 1.0 / DIRT_SPOT_M
    spot = g.math("MULTIPLY", g.ramp(g.noise((spot_size, spot_size, spot_size), 5.0),
                                     DIRT_LEVEL, DIRT_LEVEL + 0.03), low)
    colour = g.mix(colour, RUST, rust)
    colour = g.mix(colour, g.grey(g.math("SUBTRACT", 1.0, dirt)), 1.0, "MULTIPLY")
    colour = g.mix(colour, DIRT, spot)
    rough = g.lerp(g.lerp(rough, RUST_ROUGH, rust), 0.9, spot)
    metal = g.lerp(g.lerp(metal, RUST_METAL, rust), 0.0, spot)
    return colour, rough, metal


def mark_parts(obj, attr_name, prefixes):
    """Face attribute `attr_name`: 1 on faces of the parts named by prefix, or the
    value given as `prefix:0.5`; 0 elsewhere."""
    me = obj.data
    if "kyt_part" not in me.attributes or "kyt_parts" not in me:
        raise SystemExit("paint_canvas: the game mesh doesn't record its parts; "
                         "make it again with the current Make game mesh")
    names = json.loads(me["kyt_parts"])
    part = me.attributes["kyt_part"].data
    owners = [names[part[i].value] for i in range(len(me.polygons))]
    value = {}
    for group in prefixes:
        prefix, _, v = group.partition(":")
        for n in names:
            if n.startswith(prefix):
                value[n] = float(v) if v else 1.0
    attr = me.attributes.get(attr_name) or me.attributes.new(attr_name, "FLOAT", "FACE")
    attr.data.foreach_set("value", [value.get(n, 0.0) for n in owners])
    return sum(1 for n in owners if n in value), sorted(value)


def mark_perforated(obj, prefixes):
    """Face attribute `kyt_perforate`: 1 on the broad faces of the parts named by
    prefix (those facing along the part's thinnest axis, so a sheet's two faces
    and not its edges), 0 elsewhere."""
    me = obj.data
    if "kyt_part" not in me.attributes or "kyt_parts" not in me:
        raise SystemExit("paint_canvas: the game mesh doesn't record its parts; "
                         "make it again with the current Make game mesh")
    names = json.loads(me["kyt_parts"])
    part = me.attributes["kyt_part"].data
    chosen = {n for n in names for p in prefixes if n.startswith(p)}
    faces = {}
    for poly in me.polygons:
        n = names[part[poly.index].value]
        if n in chosen:
            faces.setdefault(n, []).append(poly)
    flags = [0.0] * len(me.polygons)
    for polys in faces.values():
        pts = [me.vertices[v].co for p in polys for v in p.vertices]
        extent = [max(c[i] for c in pts) - min(c[i] for c in pts) for i in range(3)]
        thin = extent.index(min(extent))
        for p in polys:
            if abs(p.normal[thin]) > 0.9:
                flags[p.index] = 1.0
    attr = me.attributes.get("kyt_perforate") or me.attributes.new("kyt_perforate", "FLOAT", "FACE")
    attr.data.foreach_set("value", flags)
    return int(sum(flags)), sorted(chosen)


def perforation(g):
    """A float socket: 0 in a diamond hole, 1 on metal, holes only where the face
    attribute `kyt_perforate` is 1. The diamonds sit on a rhombic lattice in the
    face's own plane (x along the bench, then y on a level face or z on an
    upright one), so a sheet's two faces are cut at the same places and it can
    be seen through."""
    mark = g.node("ShaderNodeAttribute")
    mark.attribute_type = "GEOMETRY"
    mark.attribute_name = "kyt_perforate"
    at = g.node("ShaderNodeSeparateXYZ")
    g.link(g.coord, at.inputs["Vector"])
    facing = g.node("ShaderNodeSeparateXYZ")
    g.link(g.node("ShaderNodeNewGeometry").outputs["True Normal"], facing.inputs["Vector"])
    u = g.math("DIVIDE", at.outputs["X"], HOLE_ALONG_M)
    across = g.math("ADD", g.math("MULTIPLY", at.outputs["Y"], g.math("ABSOLUTE", facing.outputs["Z"])),
                    g.math("MULTIPLY", at.outputs["Z"], g.math("ABSOLUTE", facing.outputs["Y"])))
    v = g.math("DIVIDE", across, HOLE_ACROSS_M)

    def from_centre(shift):
        """|du| + |dv| from the nearest diamond centre of one of the two sublattices."""
        du = g.math("ADD", u, shift)
        dv = g.math("ADD", v, shift)
        return g.math("ADD", g.math("ABSOLUTE", g.math("SUBTRACT", du, g.math("ROUND", du))),
                      g.math("ABSOLUTE", g.math("SUBTRACT", dv, g.math("ROUND", dv))))
    hole = g.math("LESS_THAN", g.math("MINIMUM", from_centre(0.0), from_centre(0.5)), 0.5 - HOLE_STRAND)
    return g.math("SUBTRACT", 1.0, g.math("MULTIPLY", hole, mark.outputs["Fac"]))


def mark_weather(obj, groups):
    """Face attributes `kyt_weather` (1 on faces of the named parts) and
    `kyt_streaks` (how strongly rust streaks there). `groups` are part-name
    prefixes, each optionally `prefix:strength` for its streaks: strong streaks
    break up on a curved arm but stripe a straight vertical leg."""
    me = obj.data
    if "kyt_part" not in me.attributes or "kyt_parts" not in me:
        raise SystemExit("paint_canvas: the game mesh doesn't record its parts; "
                         "make it again with the current Make game mesh")
    names = json.loads(me["kyt_parts"])
    strength = {}
    for group in groups:
        prefix, _, s = group.partition(":")
        for n in names:
            if n.startswith(prefix):
                strength[n] = float(s) if s else 1.0
    part = me.attributes["kyt_part"].data
    owners = [names[part[i].value] for i in range(len(me.polygons))]
    for attr_name, value_of in (("kyt_weather", lambda n: 1.0 if n in strength else 0.0),
                                ("kyt_streaks", lambda n: strength.get(n, 0.0))):
        attr = me.attributes.get(attr_name) or me.attributes.new(attr_name, "FLOAT", "FACE")
        attr.data.foreach_set("value", [value_of(n) for n in owners])
    return sum(1 for n in owners if n in strength), sorted(strength)


def bake(obj, image, surface):
    """Bake `surface(nodes, material, principled)` for each material into `image`,
    as emission. It returns a colour socket or an RGBA tuple."""
    saved = []
    for slot in obj.material_slots:
        mat = slot.material
        nt = mat.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
        g = Nodes(nt)
        emit = g.node("ShaderNodeEmission")
        value = surface(g, mat, bsdf)
        if isinstance(value, tuple):
            emit.inputs["Color"].default_value = value
        else:
            g.link(value, emit.inputs["Color"])
        target = g.node("ShaderNodeTexImage")
        target.image = image
        nt.nodes.active = target
        was = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
        g.link(emit.outputs["Emission"], out.inputs["Surface"])
        saved.append((nt, out, was, g.made))
    bpy.ops.object.bake(type="EMIT", margin=MARGIN_PX, margin_type="EXTEND", use_clear=True)
    for nt, out, was, made in saved:
        if was is not None:
            nt.links.new(was, out.inputs["Surface"])
        for node in made:
            nt.nodes.remove(node)


def bake_holes(obj, name, size):
    """The perforation mask on the canvas, 1 metal and 0 hole, as a (size, size)
    array. The bake is 0.5 + half the mask, so the canvas it leaves empty
    (cleared to 0) can be told from a hole and made metal: mipmaps then never
    thin an island's edge."""
    if bpy.data.images.get(f"{name}_holes"):
        bpy.data.images.remove(bpy.data.images[f"{name}_holes"])
    holes = bpy.data.images.new(f"{name}_holes", size, size, alpha=False)
    holes.colorspace_settings.name = "Non-Color"
    bake(obj, holes, lambda g, mat, b: g.grey(g.math("ADD", 0.5, g.math("MULTIPLY", perforation(g), 0.5))))
    hp = np.empty(size * size * 4, dtype=np.float32)
    holes.pixels.foreach_get(hp)
    bpy.data.images.remove(holes)
    baked = hp.reshape(size, size, 4)[..., 0]
    return np.where(baked >= 0.25, np.clip((baked - 0.5) * 2.0, 0.0, 1.0), 1.0)


def save_holes(metal, path):
    size = metal.shape[0]
    img = bpy.data.images.new("_kyt_holes", size, size, alpha=False)
    hp = np.repeat(metal[..., None], 4, axis=2)
    hp[..., 3] = 1.0
    img.pixels.foreach_set(hp.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def write_uv_guide(objs, path, size):
    """The outline of every UV piece of `objs` (one object or several), white on
    transparent: edges where the two faces disagree in UV, or that have one face.
    Mirrored twins share outlines."""
    segs = []
    for obj in (objs if isinstance(objs, (list, tuple)) else [objs]):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        uv = bm.loops.layers.uv.active
        for e in bm.edges:
            ends = []
            for f in e.link_faces:
                at = {l.vert: l[uv].uv.copy() for l in f.loops}
                ends.append((at[e.verts[0]], at[e.verts[1]]))
            if len(ends) == 2 and all((ends[0][i] - ends[1][i]).length < 1e-6 for i in (0, 1)):
                continue
            segs.extend(ends)
        bm.free()
    px = np.zeros((size, size, 4), dtype=np.float32)
    for a, b in segs:
        n = int(max(abs(b.x - a.x), abs(b.y - a.y)) * size * 2) + 2
        t = np.linspace(0.0, 1.0, n)
        x = np.clip(((a.x + (b.x - a.x) * t) * size).astype(int), 0, size - 1)
        y = np.clip(((a.y + (b.y - a.y) * t) * size).astype(int), 0, size - 1)
        for dx in (0, 1):
            for dy in (0, 1):
                px[np.clip(y + dy, 0, size - 1), np.clip(x + dx, 0, size - 1)] = (1.0, 1.0, 1.0, 1.0)
    img = bpy.data.images.new(os.path.basename(path), size, size, alpha=True)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def holes_only(obj, parts, name, colour_path, holes_path, root):
    """`--holes-only`: cut a canvas's holes again (after a change to HOLE_*),
    nothing else. The colour PNG keeps every pixel's colour and takes the new
    mask as its alpha; `<prop>_holes.png` is rewritten; the material is left as
    it is. A PSD made from the old canvas still carries the old holes as
    transparency, so an unpainted one is made again with `--open`."""
    if not parts or not os.path.exists(colour_path):
        raise SystemExit("paint_canvas: --holes-only needs --perforate parts and an existing canvas")
    marked = mark_perforated(obj, parts)
    scene = bpy.context.scene
    engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.samples = BAKE_SAMPLES
    scene.cycles.device = "CPU"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    colour = bpy.data.images.load(colour_path, check_existing=False)
    size = colour.size[0]
    metal = bake_holes(obj, name, size)
    scene.render.engine = engine
    px = np.empty(size * size * 4, dtype=np.float32)
    colour.pixels.foreach_get(px)
    px = px.reshape(size, size, 4)
    px[..., 3] = metal
    out = bpy.data.images.new("_kyt_colour", size, size, alpha=True)
    out.pixels.foreach_set(px.ravel())
    out.filepath_raw = colour_path
    out.file_format = "PNG"
    out.save()
    for img in (out, colour):
        bpy.data.images.remove(img)
    save_holes(metal, holes_path)
    for img in bpy.data.images:
        if img.source == "FILE" and os.path.normpath(bpy.path.abspath(img.filepath)) == os.path.normpath(colour_path):
            img.reload()
    print(f"paint_canvas: holes cut again in {marked[0]} faces of {', '.join(marked[1])}: "
          f"{os.path.relpath(colour_path, root)} alpha and {os.path.relpath(holes_path, root)} "
          f"({(metal < 0.5).mean():.1%} of the canvas open)")


def srgb(linear):
    """Linear to sRGB, per channel: the value a byte image stores."""
    linear = np.clip(linear, 0.0, 1.0)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * np.power(linear, 1 / 2.4) - 0.055)


def box(a, r):
    """Box blur of an (h, w, c) array, radius r, edges clamped."""
    for axis in (0, 1):
        a = np.moveaxis(a, axis, 0)
        pad = [(r + 1, r)] + [(0, 0)] * (a.ndim - 1)
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=0)
        n = a.shape[0]
        a = np.moveaxis((c[2 * r + 1:2 * r + 1 + n] - c[:n]) / (2 * r + 1), 0, axis)
    return a


def grow(rgb, known, reach, passes=4):
    """Carry the colours where `known` outward, `reach` px a pass, into the rest:
    the gutter round islands, so mipmaps never pull in the background."""
    known = known.astype(np.float32)[..., None]
    for _ in range(passes):
        num, den = box(rgb * known, reach), box(known, reach)
        fill = (known[..., 0] == 0) & (den[..., 0] > 1e-4)
        rgb[fill] = num[fill] / den[fill]
        known[fill] = 1.0
    return rgb


def max_filter(a, r):
    """Greyscale dilation, a (2r+1) square, separable."""
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        p = np.pad(a, pad, mode="edge")
        n = a.shape[axis]
        a = np.max([np.take(p, range(k, k + n), axis=axis) for k in range(2 * r + 1)], axis=0)
    return a


def raster_islands(objs, size):
    """Which object's island covers each pixel centre (index + 1, 0 for none),
    rows from the bottom as Blender stores images."""
    label = np.zeros((size, size), dtype=np.int16)
    for i, obj in enumerate(objs):
        me = obj.data
        me.calc_loop_triangles()
        uv = me.uv_layers.active.data
        for tri in me.loop_triangles:
            p = np.array([uv[k].uv for k in tri.loops], dtype=np.float64) * size
            x0, y0 = np.floor(p.min(axis=0)).astype(int)
            x1, y1 = np.ceil(p.max(axis=0)).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size), min(y1, size)
            if x1 <= x0 or y1 <= y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            (ax, ay), (bx, by), (cx, cy) = p
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-12:
                continue
            l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
            l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
            inside = (l1 >= 0) & (l2 >= 0) & (l1 + l2 <= 1)
            label[y0:y1, x0:x1][inside] = i + 1
    return label


def rachis_line(obj, size):
    """The blade's midrib on the canvas, base first, in pixels: the UVs of its
    vertices on x = 0, or the island's middle if it has none there."""
    me = obj.data
    uv = me.uv_layers.active.data
    at = {}
    for l in me.loops:
        co = me.vertices[l.vertex_index].co
        if abs(co.x) < 1e-4:
            at[round(co.y, 5)] = np.array(uv[l.index].uv) * size
    if len(at) < 2:
        pts = np.array([uv[l.index].uv for l in me.loops]) * size
        mid = (pts[:, 0].min() + pts[:, 0].max()) / 2
        return np.array([[mid, pts[:, 1].min()], [mid, pts[:, 1].max()]])
    return np.array([at[y] for y in sorted(at)])


def stroke(mask, a, b, half, profile, warp=None):
    """Draw a tapering stroke from `a` to `b` into `mask` (max), antialiased:
    `half` px half-width at its widest, `profile(t)` its fraction along 0..1.
    With `warp` (centre, widen), the stroke is drawn as it will lie on a dome
    unwrapped round `centre` (`cut_dome`): its direction taken against the
    line out from the centre at `a`, and its shape laid out in the dome's own
    proportions, then spread round the centre `widen(radius px)` times wider
    than it is long, as the canvas is round the dome against the dome
    itself, so the dome squeezes it back to its shape."""
    d = b - a
    length = float(np.hypot(*d))
    if length < 1.0:
        return
    d = d / length
    h, w = mask.shape
    if warp is not None:
        centre, widen = warp
        out = a - centre
        rho_a = float(np.hypot(*out))
        if rho_a > 1.0:
            er = out / rho_a
            et = np.array([-er[1], er[0]])
            dr, dt = float(d @ er), float(d @ et)  # along, round: its direction against the line out
            theta_a = float(np.arctan2(out[1], out[0]))
            # Where it reaches on the canvas, for the window to draw in.
            pts = []
            for k in range(9):
                v, u = length * k / 8 * dr, length * k / 8 * dt
                rho = rho_a + v
                th = theta_a + u * widen(rho) / max(rho, 1.0)
                pts.append(centre + rho * np.array([np.cos(th), np.sin(th)]))
            pts = np.array(pts)
            spread = (half + 2) * max(widen(rho_a), widen(rho_a + length * max(dr, 0.0)))
            x0, y0 = np.floor(pts.min(axis=0) - spread).astype(int)
            x1, y1 = np.ceil(pts.max(axis=0) + spread).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w), min(y1, h)
            if x1 <= x0 or y1 <= y0:
                return
            px, py = np.meshgrid(np.arange(x0, x1) + 0.5 - centre[0], np.arange(y0, y1) + 0.5 - centre[1])
            rho = np.hypot(px, py)
            dth = (np.arctan2(py, px) - theta_a + np.pi) % (2 * np.pi) - np.pi
            ys = rho - rho_a  # along the line out, true px
            xs = dth * rho / widen(rho)  # round the dome, true px
            t = (ys * dr + xs * dt) / length
            off = np.abs(ys * dt - xs * dr)
            cover = np.clip(half * profile(np.clip(t, 0.0, 1.0)) - off + 0.5, 0.0, 1.0)
            cover[(t < 0) | (t > 1)] = 0.0
            np.maximum(mask[y0:y1, x0:x1], cover, out=mask[y0:y1, x0:x1])
            return
    r = half + 2
    x0, y0 = np.floor(np.minimum(a, b) - r).astype(int)
    x1, y1 = np.ceil(np.maximum(a, b) + r).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w), min(y1, h)
    if x1 <= x0 or y1 <= y0:
        return
    xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5 - a[0], np.arange(y0, y1) + 0.5 - a[1])
    t = (xs * d[0] + ys * d[1]) / length
    off = np.abs(xs * d[1] - ys * d[0])
    cover = np.clip(half * profile(np.clip(t, 0.0, 1.0)) - off + 0.5, 0.0, 1.0)
    cover[(t < 0) | (t > 1)] = 0.0
    np.maximum(mask[y0:y1, x0:x1], cover, out=mask[y0:y1, x0:x1])


def leaflet_profile(t):
    """Narrow where it leaves the rachis, widest at LEAFLET_WIDEST, a point at the tip."""
    rise = 0.55 + 0.45 * t / LEAFLET_WIDEST
    fall = ((1.0 - t) / (1.0 - LEAFLET_WIDEST)) ** 0.8
    return np.where(t < LEAFLET_WIDEST, rise, fall)


def spine_profile(t):
    return 1.0 - t


def frond(obj, label, index, size, px_m):
    """What both cutters need of one blade's island: the rachis drawn as straw
    coverage, its length in pixels, `at(s)` (the point and direction that far
    along it), `half_rachis(f)` (its half-width at fraction f of the way to the
    tip) and `reach(start, direction, limit)` (how far a line runs before it
    leaves the island, less TIP_INSET_PX)."""
    straw = np.zeros((size, size), dtype=np.float32)
    line = rachis_line(obj, size)
    seg = np.diff(line, axis=0)
    seg_len = np.hypot(seg[:, 0], seg[:, 1])
    run = np.concatenate([[0.0], np.cumsum(seg_len)])
    total = run[-1]

    def at(s):
        i = int(np.clip(np.searchsorted(run, s) - 1, 0, len(seg) - 1))
        f = (s - run[i]) / max(seg_len[i], 1e-9)
        return line[i] + seg[i] * f, seg[i] / max(seg_len[i], 1e-9)

    def half_rachis(f):
        return (RACHIS_M[0] + (RACHIS_M[1] - RACHIS_M[0]) * f) * px_m

    for i in range(len(seg)):
        f0, f1 = run[i] / total, run[i + 1] / total
        h0, h1 = half_rachis(f0), half_rachis(f1)
        stroke(straw, line[i], line[i + 1], max(h0, h1), lambda t, h0=h0, h1=h1: (h0 + (h1 - h0) * t) / max(h0, h1))

    def reach(start, direction, limit):
        steps = np.arange(0.0, limit, 1.0)
        pts = start[None, :] + direction[None, :] * steps[:, None]
        ix = np.clip(pts[:, 0].astype(int), 0, size - 1)
        iy = np.clip(pts[:, 1].astype(int), 0, size - 1)
        out = np.nonzero(label[iy, ix] != index)[0]
        return (out[0] if len(out) else len(steps)) - TIP_INSET_PX

    return straw, total, at, half_rachis, reach


def cut_tears(obj, kind, label, index, size, px_m, rng):
    """(leaf, straw) coverage for one blade's island in the torn style: the
    whole leaf, less narrow tears running in from its edge along the side veins
    (the fan the leaflets use), pointed at their inner ends and deeper toward
    the tip, and a few small nicks; and the rachis."""
    spec = TEARS[kind]
    straw, total, at, half_rachis, reach = frond(obj, label, index, size, px_m)
    gap = np.zeros((size, size), dtype=np.float32)

    def angle_at(g):
        return spec["open"] + (spec["tip"] - spec["open"]) * g

    def cut(here, side, depth, width_m, profile):
        f = here / total
        p, tangent = at(here)
        normal = np.array([tangent[1], -tangent[0]]) * side
        angle = np.radians(angle_at(f) + rng.uniform(-4, 4))
        direction = tangent * np.cos(angle) + normal * np.sin(angle)
        start = p + normal * half_rachis(f)
        length = reach(start, direction, size) + TIP_INSET_PX + TEAR_PAST_PX
        inner = start + direction * length * (1.0 - min(depth, 0.95))
        stroke(gap, inner, start + direction * length, width_m * px_m / 2, profile)

    for side in (-1.0, 1.0):
        lo, hi = spec["start"] * total, 0.93 * total
        count = int(rng.integers(spec["tears"][0], spec["tears"][1] + 1))
        for k in range(count):
            here = lo + (hi - lo) * (k + rng.uniform(0.1, 0.9)) / count
            g = (here - lo) / max(hi - lo, 1e-9)
            depth = rng.uniform(*spec["depth"]) * (0.75 + 0.5 * g)
            cut(here, side, depth, rng.uniform(*spec["width"]), lambda t: 0.12 + 0.88 * t ** 1.5)
        for _ in range(spec["nicks"]):
            here = total * rng.uniform(spec["start"], 0.97)
            cut(here, side, rng.uniform(*spec["nick_depth"]), rng.uniform(0.03, 0.06), lambda t: t)
    mine = (label == index).astype(np.float32)
    return np.maximum(mine * (1.0 - gap), straw * mine), straw


def cut_leaflets(obj, kind, label, index, size, px_m, rng):
    """(leaf, straw) coverage for one blade's island: the leaflets reaching from
    the rachis to the blade's outline; the rachis and the spines."""
    spec = LEAFLETS[kind]
    leaf = np.zeros((size, size), dtype=np.float32)
    straw, total, at, half_rachis, reach = frond(obj, label, index, size, px_m)

    spine_end = spec["spines"] * total
    for side in (-1.0, 1.0):
        s = (0.25 if side > 0 else 0.75) * spec["spacing"] * px_m * SPINE_EVERY
        while s < total:
            spine = s < spine_end
            step = spec["spacing"] * px_m * (SPINE_EVERY if spine else 1.0)
            jitter = rng.uniform(-1.0, 1.0, 4) * LEAFLET_JITTER
            here = min(max(s + jitter[0] * step, 0.0), total)
            s += step
            if rng.random() < spec["missing"] and not spine:
                continue
            f = here / total
            p, tangent = at(here)
            normal = np.array([tangent[1], -tangent[0]]) * side
            if spine:
                angle = SPINE_ANGLE
            else:
                g = max(0.0, (here - spine_end) / max(total - spine_end, 1e-9))
                angle = spec["open"] + (spec["tip"] - spec["open"]) * g ** 1.5
            angle = np.radians(angle * (1.0 + jitter[1] * ANGLE_JITTER / LEAFLET_JITTER))
            direction = tangent * np.cos(angle) + normal * np.sin(angle)
            start = p + normal * half_rachis(f) * 0.6
            limit = (SPINE_REACH_M * px_m) if spine else size
            length = reach(start, direction, limit)
            if rng.random() < spec["broken"] and not spine:
                length *= rng.uniform(0.45, 0.8)
            if length < 3:
                continue
            width = spec["width"] * (SPINE_WIDTH if spine else 1.0 - 0.35 * f) * px_m * (1.0 + jitter[2])
            width = min(width, length * LEAFLET_SLENDER)
            stroke(straw if spine else leaf, start, start + direction * length, width / 2,
                   spine_profile if spine else leaflet_profile)
    return leaf, straw


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def leaf_frame(obj, kind, label, index, size, px_m):
    """Where each pixel of one blade's island lies on its leaf, read off the
    island itself (base at the bottom, the midrib the UVs of its x = 0
    vertices): its box, `along` (0 at the base, 1 at the tip), `off` (pixels
    from the midrib), `out` (0 on the midrib, 1 at the edge) and `phase`, which
    side vein it lies on: each point run back along a line at the tears'
    angle to where it leaves the midrib, spaced irregularly so the veins don't
    read as ruled but each stays straight. Shared by the shading and the
    normal map, so the pleats fall where the veins are painted."""
    mine = label == index
    ys, xs = np.nonzero(mine)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    box = mine[y0:y1 + 1, x0:x1 + 1]
    line = rachis_line(obj, size)
    mid = float(np.median(line[:, 0])) - x0
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    along = (yy - y0) / max(y1 - y0, 1)
    # The half-width of each row, from the island's own extent.
    left = np.where(box.any(axis=1), box.argmax(axis=1), 0)
    right = np.where(box.any(axis=1), box.shape[1] - 1 - box[:, ::-1].argmax(axis=1), 0)
    half = np.maximum(np.maximum(mid - left, right - mid), 1.0)[:, None]
    off = np.abs(xx - x0 - mid)
    out = np.clip(off / half, 0.0, 1.0)
    fan = TEARS.get(kind, TEARS["mature"])
    angle = np.radians(fan["open"] + (fan["tip"] - fan["open"]) * along)
    origin_m = ((yy - y0) - off / np.tan(angle)) / px_m
    phase = origin_m / VEIN_EVERY_M + 0.35 * np.sin(origin_m * 1.7 + 0.4) + 0.2 * np.sin(origin_m * 4.1 + 1.3)
    return mine, (y0, y1, x0, x1), box, along, off, out, phase


def shade_leaf(obj, kind, label, index, size, px_m, rng):
    """(rgb, coverage) of the painted starting look for one blade's island, in
    sRGB, laid on `leaf_frame`."""
    spec = SHADING[kind]
    mine, (y0, y1, x0, x1), box, along, off, out, phase = leaf_frame(obj, kind, label, index, size, px_m)
    dark, light, rim, midrib = (np.array(spec[k], dtype=np.float32) for k in ("dark", "light", "rim", "midrib"))
    lengthwise = smooth(0.0, 0.85, along)[..., None]
    rgb = dark + (light - dark) * (0.3 + 0.7 * lengthwise)
    rgb = rgb + (rim - rgb) * (smooth(SHADE_RIM, 1.0, out) * (0.45 + 0.55 * lengthwise[..., 0]))[..., None]
    crease = 1.0 - SHADE_CREASE[0] * (1.0 - smooth(0.0, SHADE_CREASE[1], out))
    base = 0.55 + 0.45 * smooth(0.0, SHADE_BASE, along)
    vein = smooth(0.7, 1.0, 0.5 + 0.5 * np.cos(2 * np.pi * phase)) * smooth(0.12, 0.3, out)
    noise = rng.standard_normal((box.shape[0] // 8 + 2, box.shape[1] // 8 + 2)).astype(np.float32)
    noise = np.kron(noise, np.ones((8, 8), dtype=np.float32))[:box.shape[0], :box.shape[1]]
    noise = box_blur2(noise, max(2, int(MOTTLE_M * px_m / 2)))
    noise = noise / max(float(np.abs(noise).max()), 1e-6)
    rgb = rgb * (crease * base * (1.0 - VEIN_DARK * vein) * (1.0 + MOTTLE * noise))[..., None]
    rib = np.exp(-(off / (MIDRIB_M * px_m)) ** 2) * (1.0 - 0.6 * along)
    rgb = rgb + (midrib - rgb) * rib[..., None]
    full = np.zeros((size, size, 3), dtype=np.float32)
    full[y0:y1 + 1, x0:x1 + 1] = np.clip(rgb, 0.0, 1.0)
    return full, mine


def box_blur2(a, r):
    """Box blur of a 2D array, radius r, edges clamped."""
    return box(a[..., None], r)[..., 0]


def cut_islands(objs, blades, size):
    """The canvas's islands (`raster_islands`), its alpha, and where the rachis
    and spines are (for their straw tint), with a report line per island. A
    blade whose kind is in LEAFLETS gets its leaflets; every other island stays
    whole. Past the islands, alpha is carried a few pixels where an island's
    edge is opaque (a stub, the rachis at a frond's base), so neither filtering
    nor mipmaps fray an edge the game shows."""
    label = raster_islands(objs, size)
    for i, obj in enumerate(objs):
        # A slotted blade (the bloom card) owns its island's copies along the
        # canvas too, one per colourway and shade.
        mine = label == i + 1
        for _, _, along in copy_steps(obj, size)[1:]:
            label[np.roll(mine, along, axis=1)] = i + 1
    alpha = np.zeros((size, size), dtype=np.float32)
    straw_all = np.zeros((size, size), dtype=np.float32)
    tone_all = np.ones((size, size), dtype=np.float32)  # the colour times this: a leaf's own light and shade
    paint_all = np.zeros((size, size, 3), dtype=np.float32)  # colour painted outright (the blooms), linear
    painted = np.zeros((size, size), dtype=bool)
    report = []
    for i, obj in enumerate(objs):
        mine = label == i + 1
        kind = obj.name.removeprefix("blade_") if obj in blades else None
        table, cutter = {"tears": (TEARS, cut_tears), "leaf": (LEAFLETS, cut_leaf),
                         "cluster": (LEAFLETS, cut_cluster),
                         "dome": (LEAFLETS, cut_dome)}.get(CUT_STYLE, (LEAFLETS, cut_leaflets))
        if kind == "bloom":
            cutter = cut_bloom
        elif kind in ("bud", "bud_green"):
            cutter = cut_bud
        elif kind in ("topper", "sprig"):
            cutter = cut_topper
        if kind in table:
            rng = np.random.default_rng(zlib.crc32(kind.encode()))
            px_m = uv_px_per_metre(obj, size)
            leaf, straw, *more = cutter(obj, kind, label, i + 1, size, px_m, rng)
            opaque = np.maximum(leaf, straw)
            alpha[mine] = opaque[mine]
            straw_all[mine] = straw[mine]
            if more:
                tone_all[mine] = more[0][mine]
            if len(more) > 1:
                paint_all[mine] = more[1][mine]
                painted |= mine
            report.append(f"{obj.name} {opaque[mine].mean():.0%} leaf at {px_m:.0f} px/m")
        else:
            alpha[mine] = 1.0
            report.append(f"{obj.name} whole")
    alpha = np.where(label == 0, max_filter(alpha, ALPHA_SPREAD_PX), alpha)
    return label, alpha, straw_all, tone_all, (paint_all, painted), report


def leaflet_canvas(argv, name, root, folder, size, orm_size):
    """`--leaflets`: the canvas for a crown whose game chooses its fronds
    (`kyt_keep_parts`), laid out by unwrap_blades.py. Each island is filled with
    its material's colour (rachis and spines tinted toward straw), the leaflets
    are cut into the colour's alpha and into `<prop>_cutout.png`, the starting
    cut-out: the PSD carries it as a layer Christina paints, every export
    writes it back from that layer, and apply_holes.py puts it into the alpha.
    The blades and the heart are given one double-sided material that clips by
    it. Every frond of a kind shows its blade's island."""
    use_prop_leaflets(name)
    blades = [o for o in bpy.data.collections["blades"].objects if o.type == "MESH"]
    others = [o for o in bpy.data.collections["export"].objects
              if o.type == "MESH" and not any(m.type == "NODES" for m in o.modifiers)]
    objs = blades + others
    stale = [o.name for o in objs if not o.get("kyt_unwrapped")]
    if stale:
        raise SystemExit(f"paint_canvas: {', '.join(stale)} not laid out yet; run unwrap_blades.py first")
    colour_path = os.path.join(folder, f"{name}_colour.png")
    orm_path = os.path.join(folder, f"{name}_orm.png")
    guide_path = os.path.join(folder, f"{name}_uv_guide.png")
    cutout_path = os.path.join(folder, f"{name}_cutout.png")
    if "--base-fade" in argv:
        # A colour at one kind's base fading up its leaf, as a layer:
        # `<prop>_<kind>_base.png`, the green of her painted mature fronds (from
        # `<prop>_colour.png`), opaque at the stalk and gone `share` of the way
        # to the tip. `prop_handback.py <prop> --base-layer <kind>` puts it in
        # her PSD at Color blend, so her painting's light and dark show through.
        # The dead fronds' green base, her ask on 2026-09-27.
        kind, share = argv[argv.index("--base-fade") + 1].split(":")
        share = float(share)
        label = raster_islands(objs, size)
        index = {o.name: i + 1 for i, o in enumerate(objs)}
        target, source = index[f"blade_{kind}"], index["blade_mature"]
        painted = bpy.data.images.load(colour_path, check_existing=False)
        px = np.empty(size * size * 4, dtype=np.float32)
        painted.pixels.foreach_get(px)
        bpy.data.images.remove(painted)
        px = px.reshape(size, size, 4)
        leaf = (label == source) & (px[..., 3] > 0.5)
        green = np.median(px[leaf][:, :3], axis=0)
        mine = label == target
        rows = np.nonzero(mine.any(axis=1))[0]
        base_row, tip_row = rows.min(), rows.max()
        along = (np.arange(size, dtype=np.float32) - base_row) / max(tip_row - base_row, 1)
        fade = (BASE_FADE_ALPHA * (1.0 - np.clip(along / share, 0.0, 1.0)) ** 1.5)[:, None]
        alpha = np.where(mine, fade, 0.0)
        alpha = np.where(label == 0, max_filter(alpha, ALPHA_SPREAD_PX), alpha)
        out = np.zeros((size, size, 4), dtype=np.float32)
        out[..., :3] = green
        out[..., 3] = alpha
        base_path = os.path.join(folder, f"{name}_{kind}_base.png")
        img = bpy.data.images.new("_kyt_base", size, size, alpha=True)
        img.pixels.foreach_set(out.ravel())
        img.filepath_raw = base_path
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        print(f"paint_canvas: {kind} base in {os.path.relpath(base_path, root)}: green "
              f"{tuple(round(float(c), 3) for c in green)} from blade_mature, gone {share:.0%} of the way up")
        return
    if "--normal-only" in argv:
        # The leaves' relief as a tangent-space normal map (OpenGL: green up,
        # Godot's convention), flat everywhere else. It goes straight to
        # `assets/props/<prop>_normal.png`: `assets/source` is hidden from
        # Godot, and the leaf shader that reads it is Godot's own
        # (assets/shaders/palm_leaf.gdshader); the GLB doesn't carry it.
        label = raster_islands(objs, size)
        normal = np.zeros((size, size, 3), dtype=np.float32)
        normal[..., 2] = 1.0
        cover = np.zeros((size, size), dtype=np.float32)
        relieved = []
        for i, obj in enumerate(objs):
            kind = obj.name.removeprefix("blade_") if obj in blades else None
            if kind not in SHADING:
                continue
            px_m = uv_px_per_metre(obj, size)
            mine, (y0, y1, x0, x1), box, along, off, out, phase = leaf_frame(obj, kind, label, i + 1, size, px_m)
            pleat = np.abs(phase - np.floor(phase) - 0.5) * 2.0  # 1 on a vein's crease, 0 midway
            # `out` steps row to row with the island's pixel edge; smoothed,
            # the curl and pleat depth don't band.
            out = box_blur2(out.astype(np.float32), 6)
            height = PLEAT_M * pleat * smooth(0.05, PLEAT_OUT, out) \
                + RIB_M * np.exp(-(off / (RIB_WIDTH_M * px_m)) ** 2) + CURL_M * smooth(0.75, 1.0, out) ** 2
            # Rows run up the image here (Blender's order), so the slopes are
            # per metre east and north, and the normal is (-dh/dx, -dh/dy, 1).
            dy, dx = np.gradient(height.astype(np.float32))
            n = np.stack([-dx * px_m, -dy * px_m, np.ones_like(height)], axis=-1)
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            region = normal[y0:y1 + 1, x0:x1 + 1]
            region[box] = n[box]
            cover[y0:y1 + 1, x0:x1 + 1][box] = 1.0
            relieved.append(obj.name)
        # Past each island, its edge normals carried a few pixels, so filtering
        # never pulls in the flat background.
        normal = grow(normal, cover > 0, MARGIN_PX)
        normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        normal_path = os.path.join(root, "assets", "props", f"{name}_normal.png")
        img = bpy.data.images.new("_kyt_normal", size, size, alpha=False)
        img.colorspace_settings.name = "Non-Color"
        px = np.ones((size, size, 4), dtype=np.float32)
        px[..., :3] = normal * 0.5 + 0.5
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = normal_path
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        print(f"paint_canvas: relief for {', '.join(relieved)} in {os.path.relpath(normal_path, root)}")
        return
    if "--shading-only" in argv:
        # A painted starting look for the leaves, as a layer: `<prop>_shading.png`,
        # the leaf kinds in SHADING shaded, transparent elsewhere, spread a few
        # pixels past each island so filtering never pulls in the background.
        # `prop_handback.py <prop> --shading-layer` puts it in her PSD as
        # "shading (Claude)", above her paint, unsaved.
        label = raster_islands(objs, size)
        rgb = np.zeros((size, size, 3), dtype=np.float32)
        cover = np.zeros((size, size), dtype=np.float32)
        shaded = []
        for i, obj in enumerate(objs):
            kind = obj.name.removeprefix("blade_") if obj in blades else None
            if kind not in SHADING:
                continue
            rng = np.random.default_rng(zlib.crc32(("shade" + kind).encode()))
            part, mine = shade_leaf(obj, kind, label, i + 1, size, uv_px_per_metre(obj, size), rng)
            rgb[mine] = part[mine]
            cover[mine] = 1.0
            shaded.append(obj.name)
        near = (max_filter(cover, MARGIN_PX) > 0) & (cover == 0)
        rgb = grow(rgb, cover > 0, MARGIN_PX)
        cover = np.where(near, 1.0, cover)
        img = bpy.data.images.new("_kyt_shading", size, size, alpha=True)
        px = np.concatenate([rgb, cover[..., None]], axis=2)
        img.pixels.foreach_set(px.astype(np.float32).ravel())
        shading_path = os.path.join(folder, f"{name}_shading.png")
        img.filepath_raw = shading_path
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        print(f"paint_canvas: shading for {', '.join(shaded)} in {os.path.relpath(shading_path, root)}")
        return
    if "--cutout-only" in argv:
        # The leaflets cut again (after a change to LEAFLETS), nothing else:
        # the colour, the ORM, the guide, the materials and her PSD stay as
        # they are. `prop_handback.py <prop> --cutout-layer` then puts the new
        # cut-out into the PSD for her to look at before she saves.
        _, alpha, _, _, _, report = cut_islands(objs, blades, size)
        save_holes(alpha, cutout_path)
        print(f"paint_canvas: leaflets cut again into {os.path.relpath(cutout_path, root)}: " + "; ".join(report))
        return
    for path in (colour_path, orm_path, cutout_path):
        if os.path.exists(path) and "--overwrite" not in argv:
            raise SystemExit(f"paint_canvas: {path} exists (it may be painted); leaving everything alone")
    os.makedirs(folder, exist_ok=True)

    label, alpha, straw, tone, (paint, painted), report = cut_islands(objs, blades, size)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    orm = np.zeros((size, size, 3), dtype=np.float32)
    for i, obj in enumerate(objs):
        # The colour each island starts from is the material it wore before
        # the canvas, remembered on it and kept in the file (a fake user; the
        # heart's has no other), so the canvas can be made again.
        mat = obj.material_slots[0].material if obj.material_slots else None
        if mat is not None and mat.name != name:
            obj["kyt_canvas_from"] = mat.name
        mat = bpy.data.materials.get(obj.get("kyt_canvas_from", ""), mat)
        if mat is not None and mat.name == name:
            raise SystemExit(f"paint_canvas: '{obj.name}' wears the canvas material and its own "
                             f"('{obj.get('kyt_canvas_from')}') is gone, so its colour is unknown")
        if mat is not None:
            mat.use_fake_user = True
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if mat else None
        base = np.array(bsdf.inputs["Base Color"].default_value[:3] if bsdf else (0.5, 0.5, 0.5))
        rough = bsdf.inputs["Roughness"].default_value if bsdf else 0.8
        metal = bsdf.inputs["Metallic"].default_value if bsdf else 0.0
        mine = label == i + 1
        rgb[mine] = base
        orm[mine] = (1.0, rough, metal)
    rgb = rgb * tone[..., None]
    tint = straw[..., None] * RACHIS_TINT
    rgb = rgb * (1.0 - tint) + np.array(RACHIS_STRAW, dtype=np.float32) * tint
    rgb = np.where(painted[..., None], paint, rgb)
    # Past an island: colour carried outward (alpha was carried by cut_islands),
    # so mipmaps never pull in the background.
    outside = label == 0
    rgb = grow(rgb, ~outside, MARGIN_PX)
    orm = grow(orm, ~outside, MARGIN_PX)

    def write(path, pixels, alpha_channel, colour_space="sRGB"):
        h, w = pixels.shape[:2]
        img = bpy.data.images.new(os.path.basename(path), w, h, alpha=alpha_channel is not None)
        img.colorspace_settings.name = colour_space
        px = np.ones((h, w, 4), dtype=np.float32)
        px[..., :3] = pixels
        if alpha_channel is not None:
            px[..., 3] = alpha_channel
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        return img

    for stale_img in (f"{name}_colour", f"{name}_orm"):
        if bpy.data.images.get(stale_img):
            bpy.data.images.remove(bpy.data.images[stale_img])
    colour = write(colour_path, srgb(rgb), alpha)
    colour.name = f"{name}_colour"
    small = orm.reshape(orm_size, size // orm_size, orm_size, size // orm_size, 3).mean(axis=(1, 3))
    orm_img = write(orm_path, small, None, "Non-Color")
    orm_img.name = f"{name}_orm"
    save_holes(alpha, cutout_path)
    write_uv_guide(objs, guide_path, size)
    for img, path in ((colour, colour_path), (orm_img, orm_path)):
        img.filepath = bpy.path.relpath(path)
        img.source = "FILE"
        img.reload()

    mat = one_material(name, colour, orm_img, objs[0].data.uv_layers.active.name, True, double_sided=True)
    for obj in objs:
        me = obj.data
        for p in me.polygons:
            p.material_index = 0
        me.materials.clear()
        # A slotted blade (the bloom card) wears its own material on the same
        # canvas, `<prop>_bloom`, so a placement can slide that material's UVs
        # to another colourway without moving the leaves'.
        me.materials.append(one_material(f"{name}_bloom", colour, orm_img, me.uv_layers.active.name, True,
                                         double_sided=True) if obj.get("kyt_slots") else mat)
    print(f"paint_canvas: {os.path.relpath(colour_path, root)} ({size} px) with the leaflets in its alpha "
          f"and {os.path.relpath(cutout_path, root)}, {os.path.relpath(orm_path, root)} ({orm_size} px), "
          f"and its UV guide; {len(objs)} islands wear one double-sided material, '{name}': "
          + "; ".join(report))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


def band_canvas(argv, name, root, folder, size, orm_size):
    """`--bands`: the canvas for a banded trunk, whose segments each wear one of
    a few bands stacked up the canvas, laid round its full width so a band
    wraps the trunk without a seam (`kyt_band_islands`, `kyt_band_gap` and
    `kyt_band_zones` on the mesh, set when it was shaped). Each band is painted
    after BAND_*: dark base, scalloped tan, pale collar. The trunk is given one
    material reading the colour and the ORM."""
    obj = next(o for o in bpy.data.collections["export"].objects
               if o.type == "MESH" and o.get("kyt_band_islands"))
    colour_path = os.path.join(folder, f"{name}_colour.png")
    orm_path = os.path.join(folder, f"{name}_orm.png")
    guide_path = os.path.join(folder, f"{name}_uv_guide.png")
    for path in (colour_path, orm_path):
        if os.path.exists(path) and "--overwrite" not in argv:
            raise SystemExit(f"paint_canvas: {path} exists (it may be painted); leaving everything alone")
    os.makedirs(folder, exist_ok=True)
    islands = int(obj["kyt_band_islands"])
    gap = float(obj["kyt_band_gap"])
    rim_s = float(obj["kyt_band_zones"][2])
    rng = np.random.default_rng(27)

    u = (np.arange(size, dtype=np.float32) + 0.5) / size
    v = (np.arange(size, dtype=np.float32) + 0.5) / size
    island = np.clip((v * islands).astype(int), 0, islands - 1)
    s = np.clip((v - island / islands - gap / 2) / (1.0 / islands - gap), 0.0, 1.0)
    uu, ss = np.meshgrid(u, s)
    band = island[:, None].repeat(size, axis=1)
    phase = rng.random(islands)[band]
    px = 1.0 / (size / islands)  # one pixel, as a share of a band

    def periodic(freqs, amp):
        """Smooth noise round the trunk, seamless where u wraps."""
        out = np.zeros_like(uu)
        for f in freqs:
            out += np.sin(np.pi * 2 * (f * uu + rng.random())) * amp / len(freqs)
        return out

    # Scallops: a pointed wave round the trunk, its points hanging below the
    # line, a little irregular in width and depth.
    warp = uu + periodic((2, 3), 0.1 / BAND_TEETH)
    wave = 1.0 - np.abs(2.0 * np.mod(BAND_TEETH * warp + phase, 1.0) - 1.0)
    edge = BAND_EDGE - BAND_TOOTH * wave * (1.0 + periodic((1, 4), 0.4))
    tan = np.clip((ss - edge) / (1.5 * px) + 0.5, 0.0, 1.0)[..., None]
    dark = np.array(BAND_DARK, dtype=np.float32) * (
        1.0 - BAND_SHADE * np.clip(1.0 - ss / 0.18, 0.0, 1.0))[..., None]
    light = np.array(BAND_TAN, dtype=np.float32) + (
        np.array(BAND_RIM, dtype=np.float32) - np.array(BAND_TAN, dtype=np.float32)) * (
        np.clip((ss - BAND_RIM_FROM) / (rim_s - BAND_RIM_FROM), 0.0, 1.0) ** 2)[..., None]
    rgb = dark * (1.0 - tan) + light * tan
    top = np.clip((ss - rim_s) / (1.5 * px) + 0.5, 0.0, 1.0)[..., None]
    rgb = rgb * (1.0 - top) + np.array(BAND_COLLAR_TOP, dtype=np.float32) * top
    fibres = rng.random((BAND_FIBRES,))[np.mod((uu * BAND_FIBRES).astype(int), BAND_FIBRES)]
    rgb *= (1.0 - BAND_FIBRE_DARK * fibres + periodic((5, 9, 13), BAND_MOTTLE))[..., None]
    rgb = np.clip(rgb, 0.0, 1.0)

    bump = BUMP_DARK + (BUMP_TAN - BUMP_DARK) * tan[..., 0]
    ridge = 0.5 - 0.5 * np.cos(np.pi * 2 * np.mod(uu * BUMP_FIBRES, 1.0))
    lift = rng.random((BUMP_FIBRES,))[np.mod((uu * BUMP_FIBRES).astype(int), BUMP_FIBRES)]
    bump += ridge * (0.6 + 0.4 * lift) * (BUMP_FIBRE_DARK * (1.0 - tan[..., 0]) + BUMP_FIBRE_TAN * tan[..., 0])
    bump += BUMP_RIM * np.clip((ss - BAND_RIM_FROM) / (rim_s - BAND_RIM_FROM), 0.0, 1.0) ** 3 * (1.0 - top[..., 0])
    bump += periodic((3, 7, 11), BUMP_MOTTLE)
    bump = np.clip(bump, 0.0, 1.0)
    # bump_to_normal works top row first; Blender's pixels start at the bottom.
    normal = np.flipud(normal_from_height(np.flipud(bump), DEPTH_PX[name], name in WRAP_U))

    def write(path, pixels, colour_space="sRGB"):
        h, w = pixels.shape[:2]
        img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
        img.colorspace_settings.name = colour_space
        out = np.ones((h, w, 4), dtype=np.float32)
        out[..., :3] = pixels
        img.pixels.foreach_set(out.ravel())
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        return img

    for stale_img in (f"{name}_colour", f"{name}_orm", f"{name}_normal"):
        if bpy.data.images.get(stale_img):
            bpy.data.images.remove(bpy.data.images[stale_img])
    # Painted in sRGB already: Blender's byte image stores what it is given.
    colour = write(colour_path, rgb)
    colour.name = f"{name}_colour"
    orm = np.empty((orm_size, orm_size, 3), dtype=np.float32)
    orm[...] = (1.0, BAND_ROUGH, 0.0)
    orm_img = write(orm_path, orm, "Non-Color")
    orm_img.name = f"{name}_orm"
    bump_path = os.path.join(folder, f"{name}_bump.png")
    normal_path = os.path.join(folder, f"{name}_normal.png")
    write(bump_path, np.repeat(bump[..., None], 3, axis=2), "Non-Color")
    normal_img = write(normal_path, normal, "Non-Color")
    normal_img.name = f"{name}_normal"
    write_uv_guide(obj, guide_path, size)
    for img, path in ((colour, colour_path), (orm_img, orm_path), (normal_img, normal_path)):
        img.filepath = bpy.path.relpath(path)
        img.source = "FILE"
        img.reload()
    mat = one_material(name, colour, orm_img, obj.data.uv_layers.active.name, False, normal=normal_img)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    print(f"paint_canvas: {os.path.relpath(colour_path, root)} ({size} px), {islands} bands, "
          f"{uv_px_per_metre(obj, size):.0f} px per metre on average; "
          f"{os.path.relpath(orm_path, root)} ({orm_size} px), {os.path.basename(bump_path)} and "
          f"{os.path.basename(normal_path)} from it, and its UV guide; '{obj.name}' wears '{name}'")
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


def uv_px_per_metre(obj, size):
    """Canvas pixels per metre of the object, from its area in UV and in 3D."""
    me = obj.data
    uv = me.uv_layers.active.data
    uv_area = 0.0
    for p in me.polygons:
        pts = [uv[k].uv for k in p.loop_indices]
        uv_area += abs(sum(pts[j][0] * pts[j - 1][1] - pts[j - 1][0] * pts[j][1] for j in range(len(pts)))) / 2
    area = sum(p.area for p in me.polygons)
    return size * (uv_area / area) ** 0.5


def one_material(name, colour, orm, uv_name, clip, double_sided=False, normal=None):
    """The prop's one material, reading both images: colour to base colour; the
    ORM's green and blue to roughness and metalness, the wiring the glTF
    exporter recognises. `clip` cuts by the colour's alpha. `normal`, a
    tangent-space normal map, goes through a Normal Map node, which the
    exporter writes as the glTF normal texture."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = uv_name
    col = nt.nodes.new("ShaderNodeTexImage")
    col.image = colour
    orm_node = nt.nodes.new("ShaderNodeTexImage")
    orm_node.image = orm
    split = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(uv.outputs["UV"], col.inputs["Vector"])
    nt.links.new(uv.outputs["UV"], orm_node.inputs["Vector"])
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(orm_node.outputs["Color"], split.inputs["Color"])
    nt.links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    for n, x in ((uv, -900), (col, -600), (orm_node, -600), (split, -300), (bsdf, 0), (out, 300)):
        n.location = (x, -320 if n is orm_node or n is split else 0)
    if normal is not None:
        nrm = nt.nodes.new("ShaderNodeTexImage")
        nrm.image = normal
        nrm.location = (-600, -640)
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.space = "TANGENT"
        nmap.uv_map = uv_name
        nmap.location = (-300, -640)
        nt.links.new(uv.outputs["UV"], nrm.inputs["Vector"])
        nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    if clip:
        # Alpha through Round is the alpha clip the glTF exporter writes as
        # alphaMode MASK, cutoff 0.5; Godot imports it as alpha scissor.
        cut = nt.nodes.new("ShaderNodeMath")
        cut.operation = "ROUND"
        cut.location = (-300, 200)
        nt.links.new(col.outputs["Alpha"], cut.inputs[0])
        nt.links.new(cut.outputs[0], bsdf.inputs["Alpha"])
        mat.surface_render_method = "DITHERED"
    if double_sided:
        # glTF doubleSided, which Godot imports as culling off: a leaf is seen
        # from both faces.
        mat.use_backface_culling = False
    nt.nodes.active = col  # texture paint paints the colour image
    mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
    return mat


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    size = arg(argv, "--size", 2048)
    orm_size = arg(argv, "--orm-size", 1024)
    grain = "--grain" in argv
    weather = argv[argv.index("--weather") + 1].split(",") if "--weather" in argv else []
    chip_parts = argv[argv.index("--chips") + 1].split(",") if "--chips" in argv else []
    ground_parts = argv[argv.index("--ground") + 1].split(",") if "--ground" in argv else []
    ding_parts = argv[argv.index("--dings") + 1].split(",") if "--dings" in argv else []
    knot_parts = argv[argv.index("--knots") + 1].split(",") if "--knots" in argv else []
    wear_parts = argv[argv.index("--wear") + 1].split(",") if "--wear" in argv else []
    perforate_parts = argv[argv.index("--perforate") + 1].split(",") if "--perforate" in argv else []
    blend = bpy.data.filepath
    name = os.path.splitext(os.path.basename(blend))[0]
    root = blend[:blend.index(os.sep + "assets" + os.sep)]
    folder = os.path.join(root, "assets", "source", "textures", name)
    colour_path = os.path.join(folder, f"{name}_colour.png")
    orm_path = os.path.join(folder, f"{name}_orm.png")
    guide_path = os.path.join(folder, f"{name}_uv_guide.png")
    holes_path = os.path.join(folder, f"{name}_holes.png")
    if "--leaflets" in argv:
        leaflet_canvas(argv, name, root, folder, size, orm_size)
        return
    if "--bands" in argv:
        band_canvas(argv, name, root, folder, size, orm_size)
        return
    obj = next(o for o in bpy.data.collections["export"].objects if o.get("kyt_game_mesh"))
    if "--guide-only" in argv:
        write_uv_guide(obj, guide_path, size)
        print(f"paint_canvas: redrew {os.path.relpath(guide_path, root)}")
        return
    for path in (colour_path, orm_path):
        if os.path.exists(path) and "--overwrite" not in argv and "--holes-only" not in argv:
            raise SystemExit(f"paint_canvas: {path} exists (it may be painted); leaving everything alone")
    if not obj.data.uv_layers:
        raise SystemExit("paint_canvas: the game mesh has no UVs; make the game mesh first")
    if "--holes-only" in argv:
        holes_only(obj, perforate_parts, name, colour_path, holes_path, root)
        return
    weathered = mark_weather(obj, weather) if weather else (0, [])
    chipped = mark_parts(obj, "kyt_chips", chip_parts) if chip_parts else (0, [])
    grounded = mark_parts(obj, "kyt_ground", ground_parts) if ground_parts else (0, [])
    dinged = mark_parts(obj, "kyt_dings", ding_parts) if ding_parts else (0, [])
    knotted = mark_parts(obj, "kyt_knots", knot_parts) if knot_parts else (0, [])
    worn = mark_parts(obj, "kyt_wear", wear_parts) if wear_parts else (0, [])
    perforated = mark_perforated(obj, perforate_parts) if perforate_parts else (0, [])
    os.makedirs(folder, exist_ok=True)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = BAKE_SAMPLES
    scene.cycles.device = "CPU"
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    def base(b):
        return tuple(b.inputs["Base Color"].default_value)

    def iron(g, mat, b):
        """Painted metal (any material but timber) as the flags ask: weathered,
        chipped, or plain (None). The flags' part lists say where."""
        if "timber" in mat.name or not (weather or chip_parts or ding_parts or ground_parts):
            return None
        surface = (base(b), b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value)
        if weather:
            surface = weathering(g, *surface)
        if ground_parts:
            surface = grounding(g, *surface)
        if chip_parts or ding_parts:
            surface = chipping(g, *surface)
        return surface

    def colour_of(g, mat, b):
        if "timber" in mat.name and (grain or wear_parts):
            wood = wood_grain(g, base(b)) if grain else base(b)
            if wear_parts:
                wood = g.mix(wood, WORN, g.math("MULTIPLY", seat_wear(g), WEAR))
            return wood
        surface = iron(g, mat, b)
        return surface[0] if surface else base(b)

    def orm_of(g, mat, b):
        if "timber" in mat.name and wear_parts:
            return g.rgb(1.0, g.lerp(b.inputs["Roughness"].default_value, WORN_ROUGH, seat_wear(g)),
                         b.inputs["Metallic"].default_value)
        surface = iron(g, mat, b)
        if surface:
            return g.rgb(1.0, surface[1], surface[2])
        return (1.0, b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value, 1.0)

    # A rebake replaces the images rather than adding `.001` copies, whose names
    # would reach the GLB and give Godot new files to extract.
    for stale in (f"{name}_colour", f"{name}_orm"):
        if bpy.data.images.get(stale):
            bpy.data.images.remove(bpy.data.images[stale])
    colour = bpy.data.images.new(f"{name}_colour", size, size, alpha=bool(perforate_parts))
    bake(obj, colour, colour_of)
    if perforate_parts:
        # The holes go in the colour's alpha, which glTF cuts as a mask, and in
        # <prop>_holes.png, which every export of the painting puts back
        # (tools/blender/apply_holes.py): a flattened PSD has no alpha.
        metal = bake_holes(obj, name, size)
        px = np.empty(size * size * 4, dtype=np.float32)
        colour.pixels.foreach_get(px)
        px = px.reshape(size, size, 4)
        px[..., 3] = metal
        colour.pixels.foreach_set(px.ravel())
        save_holes(metal, holes_path)
    colour.filepath_raw = colour_path
    colour.file_format = "PNG"
    colour.save()

    orm = bpy.data.images.new(f"{name}_orm", orm_size, orm_size, alpha=False)
    orm.colorspace_settings.name = "Non-Color"
    bake(obj, orm, orm_of)
    orm.filepath_raw = orm_path
    orm.file_format = "PNG"
    orm.save()
    write_uv_guide(obj, guide_path, size)
    for img, path in ((colour, colour_path), (orm, orm_path)):
        img.filepath = bpy.path.relpath(path)
        img.source = "FILE"
        img.reload()

    mat = one_material(name, colour, orm, obj.data.uv_layers[0].name, bool(perforate_parts))

    me = obj.data
    for p in me.polygons:
        p.material_index = 0
    me.materials.clear()
    me.materials.append(mat)
    scene.render.engine = "BLENDER_EEVEE"
    print(f"paint_canvas: {os.path.relpath(colour_path, root)} ({size} px), "
          f"{os.path.relpath(orm_path, root)} ({orm_size} px), and its UV guide; "
          f"'{obj.name}' now wears one material, '{name}'"
          + (f"; weathered {int(weathered[0])} faces of {', '.join(weathered[1])}" if weather else "")
          + (f"; chipped {int(chipped[0])} faces of {', '.join(chipped[1])}" if chip_parts else "")
          + (f"; dings on {int(dinged[0])} faces of {', '.join(dinged[1])}" if ding_parts else "")
          + (f"; knots in {', '.join(knotted[1])}" if knot_parts else "")
          + (f"; wear on {', '.join(worn[1])}" if wear_parts else "")
          + (f"; ground dirt on {int(grounded[0])} faces of {', '.join(grounded[1])}" if ground_parts else "")
          + (f"; perforated {perforated[0]} faces of {', '.join(perforated[1])} "
             f"({os.path.relpath(holes_path, root)})" if perforate_parts else ""))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


main()
