"""The paint canvas for a prop's own texture, and its one material.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>.blend \
        --python tools/blender/paint_canvas.py -- [--size 2048] [--orm-size 1024] [--grain]
        [--knots part,part] [--wear part,part] [--chips part,part] [--dings part,part]
        [--ground part,part] [--weather part,part] [--perforate part,part] [--overwrite]
        [--holes-only] [--guide-only] [--save]
    ... --python tools/blender/paint_canvas.py -- --leaflets [--overwrite | --cutout-only | --shading-only
        | --base-fade <kind>:<share>] [--save]

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


def stroke(mask, a, b, half, profile):
    """Draw a tapering stroke from `a` to `b` into `mask` (max), antialiased:
    `half` px half-width at its widest, `profile(t)` its fraction along 0..1."""
    d = b - a
    length = float(np.hypot(*d))
    if length < 1.0:
        return
    d = d / length
    r = half + 2
    x0, y0 = np.floor(np.minimum(a, b) - r).astype(int)
    x1, y1 = np.ceil(np.maximum(a, b) + r).astype(int)
    h, w = mask.shape
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


def shade_leaf(obj, kind, label, index, size, px_m, rng):
    """(rgb, coverage) of the painted starting look for one blade's island, in
    sRGB: its place along the leaf and out from the midrib read off the island
    itself (base at the bottom, the midrib the UVs of its x = 0 vertices)."""
    spec = SHADING[kind]
    mine = label == index
    ys, xs = np.nonzero(mine)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    box = mine[y0:y1 + 1, x0:x1 + 1]
    line = rachis_line(obj, size)
    mid = float(np.median(line[:, 0])) - x0
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    along = (yy - y0) / max(y1 - y0, 1)  # 0 at the base, 1 at the tip
    # The half-width of each row, from the island's own extent.
    left = np.where(box.any(axis=1), box.argmax(axis=1), 0)
    right = np.where(box.any(axis=1), box.shape[1] - 1 - box[:, ::-1].argmax(axis=1), 0)
    half = np.maximum(np.maximum(mid - left, right - mid), 1.0)[:, None]
    off = np.abs(xx - x0 - mid)
    out = np.clip(off / half, 0.0, 1.0)  # 0 on the midrib, 1 at the edge

    def smooth(e0, e1, x):
        t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
        return t * t * (3 - 2 * t)

    dark, light, rim, midrib = (np.array(spec[k], dtype=np.float32) for k in ("dark", "light", "rim", "midrib"))
    lengthwise = smooth(0.0, 0.85, along)[..., None]
    rgb = dark + (light - dark) * (0.3 + 0.7 * lengthwise)
    rgb = rgb + (rim - rgb) * (smooth(SHADE_RIM, 1.0, out) * (0.45 + 0.55 * lengthwise[..., 0]))[..., None]
    crease = 1.0 - SHADE_CREASE[0] * (1.0 - smooth(0.0, SHADE_CREASE[1], out))
    base = 0.55 + 0.45 * smooth(0.0, SHADE_BASE, along)
    # Veins: lines along the fan, found by running each point back along a
    # line at the tears' angle to where it leaves the rachis.
    fan = TEARS.get(kind, TEARS["mature"])
    angle = np.radians(fan["open"] + (fan["tip"] - fan["open"]) * along)
    origin_m = ((yy - y0) - off / np.tan(angle)) / px_m
    # Irregular spacing, set by where a vein leaves the midrib alone, so each
    # vein stays a straight line and they don't read as ruled.
    phase = origin_m / VEIN_EVERY_M + 0.35 * np.sin(origin_m * 1.7 + 0.4) + 0.2 * np.sin(origin_m * 4.1 + 1.3)
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
    alpha = np.zeros((size, size), dtype=np.float32)
    straw_all = np.zeros((size, size), dtype=np.float32)
    report = []
    for i, obj in enumerate(objs):
        mine = label == i + 1
        kind = obj.name.removeprefix("blade_") if obj in blades else None
        table, cutter = (TEARS, cut_tears) if CUT_STYLE == "tears" else (LEAFLETS, cut_leaflets)
        if kind in table:
            rng = np.random.default_rng(zlib.crc32(kind.encode()))
            px_m = uv_px_per_metre(obj, size)
            leaf, straw = cutter(obj, kind, label, i + 1, size, px_m, rng)
            opaque = np.maximum(leaf, straw)
            alpha[mine] = opaque[mine]
            straw_all[mine] = straw[mine]
            report.append(f"{obj.name} {opaque[mine].mean():.0%} leaf at {px_m:.0f} px/m")
        else:
            alpha[mine] = 1.0
            report.append(f"{obj.name} whole")
    alpha = np.where(label == 0, max_filter(alpha, ALPHA_SPREAD_PX), alpha)
    return label, alpha, straw_all, report


def leaflet_canvas(argv, name, root, folder, size, orm_size):
    """`--leaflets`: the canvas for a crown whose game chooses its fronds
    (`kyt_keep_parts`), laid out by unwrap_blades.py. Each island is filled with
    its material's colour (rachis and spines tinted toward straw), the leaflets
    are cut into the colour's alpha and into `<prop>_cutout.png`, the starting
    cut-out: the PSD carries it as a layer Christina paints, every export
    writes it back from that layer, and apply_holes.py puts it into the alpha.
    The blades and the heart are given one double-sided material that clips by
    it. Every frond of a kind shows its blade's island."""
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
        _, alpha, _, report = cut_islands(objs, blades, size)
        save_holes(alpha, cutout_path)
        print(f"paint_canvas: leaflets cut again into {os.path.relpath(cutout_path, root)}: " + "; ".join(report))
        return
    for path in (colour_path, orm_path, cutout_path):
        if os.path.exists(path) and "--overwrite" not in argv:
            raise SystemExit(f"paint_canvas: {path} exists (it may be painted); leaving everything alone")
    os.makedirs(folder, exist_ok=True)

    label, alpha, straw, report = cut_islands(objs, blades, size)
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
    tint = straw[..., None] * RACHIS_TINT
    rgb = rgb * (1.0 - tint) + np.array(RACHIS_STRAW, dtype=np.float32) * tint
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
        me.materials.append(mat)
    print(f"paint_canvas: {os.path.relpath(colour_path, root)} ({size} px) with the leaflets in its alpha "
          f"and {os.path.relpath(cutout_path, root)}, {os.path.relpath(orm_path, root)} ({orm_size} px), "
          f"and its UV guide; {len(objs)} islands wear one double-sided material, '{name}': "
          + "; ".join(report))
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


def one_material(name, colour, orm, uv_name, clip, double_sided=False):
    """The prop's one material, reading both images: colour to base colour; the
    ORM's green and blue to roughness and metalness, the wiring the glTF
    exporter recognises. `clip` cuts by the colour's alpha."""
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
