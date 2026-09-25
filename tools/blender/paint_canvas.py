"""The paint canvas for a prop's own texture, and its one material.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>.blend \
        --python tools/blender/paint_canvas.py -- [--size 2048] [--orm-size 1024] [--grain]
        [--knots part,part] [--wear part,part] [--chips part,part] [--dings part,part]
        [--ground part,part] [--weather part,part] [--overwrite] [--guide-only] [--save]

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

`--weather arm_loop,scroll,armrest,front_leg:0.4` weathers the painted iron (a
material whose name contains "iron" or "steel": the backless bench's frame is
`painted_steel`) of the parts whose names start with those
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


def write_uv_guide(obj, path, size):
    """The outline of every UV piece, white on transparent: edges where the two
    faces disagree in UV, or that have one face. Mirrored twins share outlines."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    segs = []
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
    blend = bpy.data.filepath
    name = os.path.splitext(os.path.basename(blend))[0]
    root = blend[:blend.index(os.sep + "assets" + os.sep)]
    folder = os.path.join(root, "assets", "source", "textures", name)
    colour_path = os.path.join(folder, f"{name}_colour.png")
    orm_path = os.path.join(folder, f"{name}_orm.png")
    guide_path = os.path.join(folder, f"{name}_uv_guide.png")
    obj = next(o for o in bpy.data.collections["export"].objects if o.get("kyt_game_mesh"))
    if "--guide-only" in argv:
        write_uv_guide(obj, guide_path, size)
        print(f"paint_canvas: redrew {os.path.relpath(guide_path, root)}")
        return
    for path in (colour_path, orm_path):
        if os.path.exists(path) and "--overwrite" not in argv:
            raise SystemExit(f"paint_canvas: {path} exists (it may be painted); leaving everything alone")
    if not obj.data.uv_layers:
        raise SystemExit("paint_canvas: the game mesh has no UVs; make the game mesh first")
    weathered = mark_weather(obj, weather) if weather else (0, [])
    chipped = mark_parts(obj, "kyt_chips", chip_parts) if chip_parts else (0, [])
    grounded = mark_parts(obj, "kyt_ground", ground_parts) if ground_parts else (0, [])
    dinged = mark_parts(obj, "kyt_dings", ding_parts) if ding_parts else (0, [])
    knotted = mark_parts(obj, "kyt_knots", knot_parts) if knot_parts else (0, [])
    worn = mark_parts(obj, "kyt_wear", wear_parts) if wear_parts else (0, [])
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
        """Painted iron or steel as the flags ask: weathered, chipped, or plain (None)."""
        if not any(k in mat.name for k in ("iron", "steel")) \
                or not (weather or chip_parts or ding_parts or ground_parts):
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
    colour = bpy.data.images.new(f"{name}_colour", size, size, alpha=False)
    bake(obj, colour, colour_of)
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

    # One material reading both: colour to base colour; the ORM's green and blue
    # to roughness and metalness, the wiring the glTF exporter recognises.
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = obj.data.uv_layers[0].name
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
    nt.nodes.active = col  # texture paint paints the colour image
    mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)

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
          + (f"; ground dirt on {int(grounded[0])} faces of {', '.join(grounded[1])}" if ground_parts else ""))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


main()
