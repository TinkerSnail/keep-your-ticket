"""A render-only painted preview of a cartoony house (2026-10-04): stand-in
painting for its roof and siding, so a build can be judged as it will read
once painted, before anyone paints it. Nothing is ever saved into the blend.

    /Applications/Blender.app/Contents/MacOS/Blender --background <house>.blend \\
        --python tools/blender/cartoon_preview.py -- <variant>[,<variant>...] <folder> [<shot> ...] \\
        [--scale <s>] [--keep-eye] [--siding-origin <z> | <variant>=<z>,...] [--figure] \\
        [--gap <m> [--rows <n>]]

Renders the variant (its `kyt_variant` parts in `export`; every other part,
`reference` and `authored` hidden) into <folder> as `painted_<shot>.png`,
every shot in SHOTS or only those named. Several variants, comma-separated,
stand side by side for the shot only, each moved over one lot (the width of
the blend's `lot...` outline, 9 m without one) in the order given, each with
its own painted stand-in and siding origin; the `lineup_...` shots frame four
of them. `--figure` stands a 1.7 m figure on the lawn for scale.

A kit of houses of different widths (the cottage kit, 2026-10-04) lines up
with `--gap`: each house stands `gap` metres clear of the one before it, by
their own widths, and the `lineup_...` shots are framed on the row instead of
on four lots. `--rows` splits the houses into that many rows, in the order
given, each rendered with the same camera (so every house is at one scale)
and the rows stacked into one image, the first on top; a figure (with
`--figure`) stands at the left of each row. `--keep-eye` keeps the
eye-height shots' eye (any eye 2 m or lower) at its height in metres when
`--scale` shrinks the rest, so a small house is still seen from where a
person stands. It changes, in memory only:

- **The roof** (each of the variant's materials named `..._roof` or
  `..._roof_<kind>`; a metal one is left plain, as metal is): painted
  shingles on `cartoon_kit`'s grid, read from the kit so the painting and the raised
  clusters cannot drift apart: courses SHINGLE_E apart down each slope,
  tabs SHINGLE_W across, each course slid by STAGGER of a tab, keyways
  SHINGLE_KEY wide on the grid's lines. Each row reads as overlapping the
  one below, never as bricks (the standard, `prop-pipeline.md`, "Buildings
  are cartoony"): a soft cast shadow under each butt fading down the row,
  each tab lighter toward its own butt, no light line along the butt, a
  tone and tint per tab, some tabs split narrower, grain down the slope.
- **The raised tabs** (the variant's parts named `...shingles`, the
  clusters): the same painting through a UV map baked in the frame of the
  slab each face lies nearest, since a tab's own faces lean a degree or two
  off the slab, which would swing a world-position projection by decimetres.
- **Log walls** (a material named `..._walls_log`): logs in `cartoon_kit`'s
  log rhythm, a tone per course, grain magnified along them, darker where
  each rounds into the chinking.
- **Board-and-batten** (a material named `..._walls_batten`): vertical boards
  and battens at double a real one's width.
- **Stone** (each material named `..._stone`): fieldstone on `cartoon_kit`'s
  stone grid, the raised stones of a stone stack sitting on painted ones.
- **The walls** (each material named `..._walls` or `..._walls_<kind>`): lap siding at the standard's
  0.24 m exposure, its courses counted from `--siding-origin` (the main
  floor, 1.55 on the Victorian blue, 0.60 on its purple; 0 by default; one
  per variant as `blue=1.55,purple=0.6`), its grain magnified with it.

The painting reads each part's own (object) coordinates, which are the
house's frame, so a house moved over for a lineup keeps its painted courses
on its raised tabs.

The stage is a ground, a walk and a street at the front of the blend's
`lot...` reference outline and a drive on its `driveway` outline, as the
house builders' own renders lay them; without a lot, the kerb is 6 m in
front of the house. SHOTS are in the house builders' shared frame (origin at
the body's footprint centre, front to -Y, ground at z = 0), framed on the
Victorian, about 7.6 by 19 m and 9.7 m tall; `--scale` scales every eye and
target about the origin for a bigger or smaller house.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartoon_kit as ck  # noqa: E402

# name: (eye, target, lens), metres in the house frame
SHOTS = {
    "three_quarter": ((6.5, -18.5, 1.75), (0.2, -2.0, 4.6), 26),      # from the street, right of centre, eye height
    "east_side": ((13.0, -9.0, 1.75), (0.5, -0.5, 4.2), 24),          # the driveway side
    "rear_east": ((11.0, 15.0, 2.2), (0.5, 2.0, 4.6), 26),
    "roof": ((-9.0, 6.5, 9.5), (-1.2, 0.5, 6.4), 30),                 # over the west slope from above the eave
    "front": ((0.4, -21.0, 1.8), (0.4, -0.5, 4.8), 26),
    "gable_close": ((0.3, -13.5, 4.6), (0.0, -5.0, 6.6), 30),         # the front gable's trim
    "rear_west": ((-12.0, 15.0, 3.0), (-0.8, 2.0, 6.2), 28),
    "vents_close": ((-6.5, 7.5, 7.8), (-1.6, 2.2, 6.6), 30),          # the back half of the west slope
    # the three-quarter and the side from the left, for a house whose photo
    # (or whose door) is on the west (the cottage kit's classic, its ranch)
    "three_quarter_west": ((-6.5, -18.5, 1.75), (-0.2, -2.0, 4.6), 26),
    "west_side": ((-13.0, -9.0, 1.75), (-0.5, -0.5, 4.2), 24),
    # four houses on neighbouring lots (x 0, 9, 18, 27), with a fourth
    # element, an orthographic width in metres
    "lineup_three_quarter": ((27.5, -36.0, 1.75), (13.0, -1.0, 4.4), 30),   # from the street, right of the row, eye height
    "lineup_elevation": ((13.5, -60.0, 4.9), (13.5, 0.0, 4.9), 50, 37.0),  # straight on, every house at one scale
}
LINEUP_SIZE = (2400, 1000)
SIZE = (1800, 1100)
SIDING = 0.24              # the standard's painted lap siding exposure: twice a real one
SIDING_GRAIN = 2.0         # its grain magnified with it
BATTEN_BOARD, BATTEN_W = 0.40, 0.08   # board-and-batten: boards and battens double a real one's


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"--scale": "1.0", "--siding-origin": "0.0", "--gap": "", "--rows": "1"}
    flags = {"--figure": False, "--keep-eye": False}
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] in opts:
            opts[argv[i]] = argv[i + 1]
            i += 2
        elif argv[i] in flags:
            flags[argv[i]] = True
            i += 1
        else:
            rest.append(argv[i])
            i += 1
    if len(rest) < 2:
        raise SystemExit("cartoon_preview: give <variant> <folder> [<shot> ...]")
    shots = rest[2:] or list(SHOTS)
    unknown = [s for s in shots if s not in SHOTS]
    if unknown:
        raise SystemExit(f"cartoon_preview: no shot {unknown}; there are {list(SHOTS)}")
    variants = rest[0].split(",")
    so = opts["--siding-origin"]
    if "=" in so:
        origins = {k: float(z) for k, z in (item.split("=") for item in so.split(","))}
    else:
        origins = {v: float(so) for v in variants}
    gap = float(opts["--gap"]) if opts["--gap"] else None
    return (variants, rest[1], shots, float(opts["--scale"]), origins, flags["--figure"], gap, int(opts["--rows"]),
            flags["--keep-eye"])


# --- the stand-in painting ------------------------------------------------------------

def shingles(name, rgb, use_uv=False):
    """Shingles on cartoon_kit's grid, not bricks: a soft shadow under each
    butt fading down the row below, each tab lighter toward its own butt,
    keyways on the grid's lines, some tabs split narrower, a tone and tint
    per tab, grain running down the slope. `use_uv` reads the position in
    the slab's frame from the `_plane` UV map (the raised tabs)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    geo = nt.nodes.new("ShaderNodeNewGeometry")

    def M(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def V(op, a, b=None, scale=None):
        n = nt.nodes.new("ShaderNodeVectorMath")
        n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, tuple):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)):
                n.inputs["Scale"].default_value = scale
            else:
                L.new(scale, n.inputs["Scale"])
        return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Vector"]

    def white(vec):
        n = nt.nodes.new("ShaderNodeTexWhiteNoise")
        n.noise_dimensions = "3D"
        L.new(vec, n.inputs["Vector"])
        return n

    def xyz(a, b, c=0.0):
        n = nt.nodes.new("ShaderNodeCombineXYZ")
        for i, x in enumerate((a, b, c)):
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def ramp(x, a, b, lo, hi):
        n = nt.nodes.new("ShaderNodeMapRange")
        n.clamp = True
        L.new(x, n.inputs["Value"])
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a, b
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = lo, hi
        return n.outputs["Result"]

    # s: courses down the slope, t: tabs across, as cartoon_kit's slope_s and
    # its clusters' t_mid measure them (the position in the house's frame, the
    # part's object coordinates, dotted with the face's downhill and across
    # directions; the parts are built unmoved, so it is their world position
    # until a lineup moves them over)
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], nsep.inputs[0])
    down = V("NORMALIZE", V("ADD", V("SCALE", geo.outputs["Normal"], scale=nsep.outputs["Z"]), (0.0, 0.0, -1.0)))
    across = V("NORMALIZE", V("CROSS_PRODUCT", geo.outputs["Normal"], (0.0, 0.0, 1.0)))
    pos = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    s = M("DIVIDE", V("DOT_PRODUCT", pos, down), ck.SHINGLE_E)
    t = M("DIVIDE", V("DOT_PRODUCT", pos, across), ck.SHINGLE_W)
    if use_uv:
        # the raised tabs: their own faces lean a degree or two off the slab,
        # which swings a world-position projection by decimetres, so their
        # (across, down) in the slab's frame is baked into a UV map instead
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "_plane"
        usep = nt.nodes.new("ShaderNodeSeparateXYZ")
        L.new(uvn.outputs["UV"], usep.inputs[0])
        s = M("DIVIDE", usep.outputs["Y"], ck.SHINGLE_E)
        t = M("DIVIDE", usep.outputs["X"], ck.SHINGLE_W)
    # grain down the slope, stretched along it
    gn = nt.nodes.new("ShaderNodeTexNoise")
    gn.inputs["Scale"].default_value = 1.0
    gn.inputs["Detail"].default_value = 3.0
    L.new(xyz(M("MULTIPLY", t, 9.0), M("MULTIPLY", s, 0.7)), gn.inputs["Vector"])
    grain = ramp(gn.outputs["Fac"], 0.3, 0.7, 0.90, 1.05)
    course = M("FLOOR", s)
    fs = M("FRACT", s)
    tt = M("ADD", t, M("FRACT", M("MULTIPLY", course, ck.STAGGER)))   # cartoon_kit's shingle_stagger
    tab = M("FLOOR", tt)
    ft = M("FRACT", tt)
    r = white(xyz(course, tab)).outputs["Value"]
    # some tabs split narrower, at 35-65% across, with a keyway of their own
    at = M("ADD", 0.35, M("MULTIPLY", M("FRACT", M("MULTIPLY", r, 7.3)), 0.30))
    split = M("GREATER_THAN", r, 0.55 if not use_uv else 2.0)    # a raised tab is one whole shingle
    sub = M("ADD", M("MULTIPLY", tab, 2.0), M("MULTIPLY", split, M("GREATER_THAN", ft, at)))
    # the keyways: SHINGLE_KEY wide, centred on the grid's lines, where a
    # raised tab's gap is
    k = ck.SHINGLE_KEY / ck.SHINGLE_W / 2
    key = M("MAXIMUM", M("MAXIMUM", M("LESS_THAN", ft, k), M("GREATER_THAN", ft, 1.0 - k)),
            M("MULTIPLY", split, M("LESS_THAN", M("ABSOLUTE", M("SUBTRACT", ft, at)), 0.010)))
    wn = white(xyz(course, sub, 1.0))
    jit = M("MULTIPLY", M("SUBTRACT", wn.outputs["Value"], 0.5), 0.10)
    fsj = M("ADD", fs, jit)                       # the shadow's depth varies tab to tab: the butts above read uneven
    # each row overlaps the one below it: a hard cast shadow right under the
    # butt above, fading down the row; no light line along the butt (her
    # "kind of weird")
    cast = M("SUBTRACT", 1.0, M("MULTIPLY", M("LESS_THAN", fsj, 0.06), 0.50))
    shade = M("MULTIPLY", cast, ramp(fsj, 0.06, 0.30, 0.68, 1.0))
    grad = ramp(fsj, 0.30, 1.0, 0.86, 1.10)      # lighter toward its own butt, as if it bows out over the row below
    tone = ramp(white(xyz(course, sub, 2.0)).outputs["Value"], 0.0, 1.0, 0.86, 1.08)
    keyf = M("SUBTRACT", 1.0, M("MULTIPLY", key, 0.42))
    f = M("MULTIPLY", M("MULTIPLY", M("MULTIPLY", shade, grad), M("MULTIPLY", tone, keyf)), grain)
    tint = V("ADD", V("SCALE", V("SUBTRACT", wn.outputs["Color"], (0.5, 0.5, 0.5)), scale=0.10), (1.0, 1.0, 1.0))
    L.new(V("MULTIPLY", V("SCALE", tint, scale=f), rgb), bsdf.inputs["Base Color"])
    return m


def siding(name, rgb, origin):
    """Lap siding at SIDING exposure counted from z = `origin`: a shadow line
    under each course's lap, and grain magnified with the boards."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    geo = nt.nodes.new("ShaderNodeNewGeometry")

    def node(kind, op=None):
        n = nt.nodes.new(kind)
        if op:
            n.operation = op
        return n
    sep = node("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep.inputs[0])
    sub = node("ShaderNodeMath", "SUBTRACT")
    L.new(sep.outputs["Z"], sub.inputs[0])
    sub.inputs[1].default_value = origin
    div = node("ShaderNodeMath", "DIVIDE")
    L.new(sub.outputs[0], div.inputs[0])
    div.inputs[1].default_value = SIDING
    fr = node("ShaderNodeMath", "FRACT")
    L.new(div.outputs[0], fr.inputs[0])
    lt = node("ShaderNodeMath", "LESS_THAN")       # the bottom 13% of each course, in the lap's shadow
    L.new(fr.outputs[0], lt.inputs[0])
    lt.inputs[1].default_value = 0.13
    sh = node("ShaderNodeMath", "MULTIPLY_ADD")
    L.new(lt.outputs[0], sh.inputs[0])
    sh.inputs[1].default_value = -0.30
    sh.inputs[2].default_value = 1.0
    mp = nt.nodes.new("ShaderNodeMapping")         # the grain, long along the boards
    L.new(geo.outputs["Position"], mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (1.6 / SIDING_GRAIN, 1.6 / SIDING_GRAIN, 40.0 / SIDING_GRAIN)
    nzt = nt.nodes.new("ShaderNodeTexNoise")
    L.new(mp.outputs[0], nzt.inputs["Vector"])
    nzt.inputs["Scale"].default_value = 1.0
    nzt.inputs["Detail"].default_value = 2.0
    gr = node("ShaderNodeMath", "MULTIPLY_ADD")
    L.new(nzt.outputs["Fac"], gr.inputs[0])
    gr.inputs[1].default_value = 0.30
    gr.inputs[2].default_value = 0.85
    f = node("ShaderNodeMath", "MULTIPLY")
    L.new(sh.outputs[0], f.inputs[0])
    L.new(gr.outputs[0], f.inputs[1])
    sc = node("ShaderNodeVectorMath", "SCALE")
    sc.inputs[0].default_value = rgb
    L.new(f.outputs[0], sc.inputs["Scale"])
    L.new(sc.outputs[0], bsdf.inputs["Base Color"])
    return m


def stones(name, rgb):
    """Fieldstone on `cartoon_kit`'s stone grid (STONE_E courses from z = 0,
    STONE_W stones across each face, slid by STAGGER a course, some split by
    `stone_split`'s hash, STONE_KEY joints on the lines), so the raised
    stones sit on painted ones: dark joints round each stone's rounded corners, a tone and tint per stone,
    each stone a pillow darker toward its edges and lighter toward its top."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    geo = nt.nodes.new("ShaderNodeNewGeometry")

    def M(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def ramp(x, a, b, lo, hi):
        n = nt.nodes.new("ShaderNodeMapRange")
        n.clamp = True
        L.new(x, n.inputs["Value"])
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a, b
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = lo, hi
        return n.outputs["Result"]
    pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], pos.inputs[0])
    nrm = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], nrm.inputs[0])
    # across a face: x on a face looking along y, y on one looking along x
    on_y = M("GREATER_THAN", M("ABSOLUTE", nrm.outputs["Y"]), M("ABSOLUTE", nrm.outputs["X"]))
    a = M("ADD", M("MULTIPLY", pos.outputs["X"], on_y), M("MULTIPLY", pos.outputs["Y"], M("SUBTRACT", 1.0, on_y)))
    s = M("DIVIDE", pos.outputs["Z"], ck.STONE_E)
    course, fs = M("FLOOR", s), M("FRACT", s)
    t = M("ADD", M("DIVIDE", a, ck.STONE_W), M("FRACT", M("MULTIPLY", course, ck.STAGGER)))
    stone, ft = M("FLOOR", t), M("FRACT", t)
    # cartoon_kit's stone_split, node for node: some stones split in two
    h = M("FRACT", M("ADD", M("MULTIPLY", course, 0.7548777), M("MULTIPLY", stone, 0.5698403)))
    split = M("GREATER_THAN", h, 0.6)
    at = M("ADD", 0.35, M("MULTIPLY", M("FRACT", M("MULTIPLY", h, 7.3)), 0.30))
    right = M("MULTIPLY", split, M("GREATER_THAN", ft, at))
    # across the stone (or the half it is in), 0 to 1
    left_u = M("DIVIDE", ft, M("ADD", M("MULTIPLY", split, M("SUBTRACT", at, 1.0)), 1.0))
    right_u = M("DIVIDE", M("SUBTRACT", ft, at), M("SUBTRACT", 1.0, at))
    u = M("ADD", M("MULTIPLY", right, right_u), M("MULTIPLY", M("SUBTRACT", 1.0, right), left_u))
    # the joint: outside each stone's rounded rectangle (its own width, the
    # half's when split, less the joint, corners rounded STONE_ROUND)
    ws = M("MULTIPLY", ck.STONE_W, M("ADD", M("MULTIPLY", right, M("SUBTRACT", 1.0, at)),
                                         M("MULTIPLY", M("SUBTRACT", 1.0, right),
                                           M("ADD", M("MULTIPLY", split, M("SUBTRACT", at, 1.0)), 1.0))))
    r, k2 = ck.STONE_ROUND, ck.STONE_KEY / 2
    qx = M("SUBTRACT", M("ABSOLUTE", M("MULTIPLY", M("SUBTRACT", u, 0.5), ws)), M("SUBTRACT", M("MULTIPLY", ws, 0.5), k2 + r))
    qz = M("SUBTRACT", M("ABSOLUTE", M("MULTIPLY", M("SUBTRACT", fs, 0.5), ck.STONE_E)), ck.STONE_E / 2 - k2 - r)
    outer = M("SQRT", M("ADD", M("POWER", M("MAXIMUM", qx, 0.0), 2.0), M("POWER", M("MAXIMUM", qz, 0.0), 2.0)))
    d = M("SUBTRACT", M("ADD", outer, M("MINIMUM", M("MAXIMUM", qx, qz), 0.0)), r)
    joint = M("GREATER_THAN", d, 0.0)
    cell = nt.nodes.new("ShaderNodeCombineXYZ")
    L.new(course, cell.inputs[0])
    L.new(M("ADD", M("MULTIPLY", stone, 2.0), right), cell.inputs[1])
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    L.new(cell.outputs[0], wn.inputs["Vector"])
    tone = ramp(wn.outputs["Value"], 0.0, 1.0, 0.76, 1.12)
    grad = ramp(fs, 0.0, 1.0, 0.86, 1.06)
    # each stone a pillow: darker toward its own edges, so it reads round
    dx = M("MULTIPLY", M("ABSOLUTE", M("SUBTRACT", u, 0.5)), 2.0)
    dz = M("MULTIPLY", M("ABSOLUTE", M("SUBTRACT", fs, 0.5)), 2.0)
    pillow = M("SUBTRACT", 1.0, M("MULTIPLY", M("POWER", M("MAXIMUM", dx, dz), 2.0), 0.45))
    f = M("MULTIPLY", M("MULTIPLY", M("MULTIPLY", tone, grad), pillow), M("SUBTRACT", 1.0, M("MULTIPLY", joint, 0.55)))
    tint = nt.nodes.new("ShaderNodeVectorMath")
    tint.operation = "MULTIPLY_ADD"
    L.new(wn.outputs["Color"], tint.inputs[0])
    tint.inputs[1].default_value = (0.22, 0.22, 0.22)        # warm and cool stones side by side
    tint.inputs[2].default_value = (0.89, 0.89, 0.89)
    col = nt.nodes.new("ShaderNodeVectorMath")
    col.operation = "MULTIPLY"
    L.new(tint.outputs[0], col.inputs[0])
    col.inputs[1].default_value = rgb
    out = nt.nodes.new("ShaderNodeVectorMath")
    out.operation = "SCALE"
    L.new(col.outputs[0], out.inputs[0])
    L.new(f, out.inputs["Scale"])
    L.new(out.outputs[0], bsdf.inputs["Base Color"])
    return m


def logs(name, rgb):
    """Log walls in `cartoon_kit`'s log rhythm (a log every LOG_COURSE up from
    LOG_R): each course a log of its own tone, its grain magnified and run
    along it, darker toward its top and bottom where it rounds into the
    chinking crease, so the modelled logs and their painting agree."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    geo = nt.nodes.new("ShaderNodeNewGeometry")

    def M(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def ramp(x, a, b, lo, hi):
        n = nt.nodes.new("ShaderNodeMapRange")
        n.clamp = True
        L.new(x, n.inputs["Value"])
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a, b
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = lo, hi
        return n.outputs["Result"]
    pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], pos.inputs[0])
    s = M("DIVIDE", M("SUBTRACT", pos.outputs["Z"], ck.LOG_R - ck.LOG_COURSE / 2), ck.LOG_COURSE)
    course, fs = M("FLOOR", s), M("FRACT", s)
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "1D"
    L.new(course, wn.inputs["W"])
    tone = ramp(wn.outputs["Value"], 0.0, 1.0, 0.82, 1.10)
    edge = M("MULTIPLY", M("ABSOLUTE", M("SUBTRACT", fs, 0.5)), 2.0)
    roundness = M("SUBTRACT", 1.0, M("MULTIPLY", M("POWER", edge, 2.0), 0.40))
    mp = nt.nodes.new("ShaderNodeMapping")       # grain, magnified, long along the log
    L.new(geo.outputs["Position"], mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (0.8, 0.8, 22.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    L.new(mp.outputs[0], nz.inputs["Vector"])
    nz.inputs["Detail"].default_value = 2.0
    grain = ramp(nz.outputs["Fac"], 0.3, 0.7, 0.88, 1.06)
    f = M("MULTIPLY", M("MULTIPLY", tone, roundness), grain)
    out = nt.nodes.new("ShaderNodeVectorMath")
    out.operation = "SCALE"
    out.inputs[0].default_value = rgb
    L.new(f, out.inputs["Scale"])
    L.new(out.outputs[0], bsdf.inputs["Base Color"])
    return m


def battens(name, rgb):
    """Board-and-batten: vertical boards BATTEN_BOARD across (double a real
    board's width, as the siding is), a lighter batten over each joint with a
    shadow beside it, grain magnified and run up the boards."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    geo = nt.nodes.new("ShaderNodeNewGeometry")

    def M(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]
    pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], pos.inputs[0])
    nrm = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], nrm.inputs[0])
    on_y = M("GREATER_THAN", M("ABSOLUTE", nrm.outputs["Y"]), M("ABSOLUTE", nrm.outputs["X"]))
    a = M("ADD", M("MULTIPLY", pos.outputs["X"], on_y), M("MULTIPLY", pos.outputs["Y"], M("SUBTRACT", 1.0, on_y)))
    ft = M("FRACT", M("DIVIDE", a, BATTEN_BOARD))
    w = BATTEN_W / BATTEN_BOARD
    batten = M("LESS_THAN", ft, w)
    shadow = M("MULTIPLY", M("GREATER_THAN", ft, w), M("LESS_THAN", ft, w + 0.06))
    mp = nt.nodes.new("ShaderNodeMapping")
    L.new(geo.outputs["Position"], mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (14.0, 14.0, 0.8)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    L.new(mp.outputs[0], nz.inputs["Vector"])
    nz.inputs["Detail"].default_value = 2.0
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.clamp = True
    L.new(nz.outputs["Fac"], rr.inputs["Value"])
    rr.inputs["From Min"].default_value, rr.inputs["From Max"].default_value = 0.3, 0.7
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.88, 1.06
    f = M("MULTIPLY", M("MULTIPLY", M("ADD", 1.0, M("MULTIPLY", batten, 0.12)), M("SUBTRACT", 1.0, M("MULTIPLY", shadow, 0.30))),
          rr.outputs["Result"])
    out = nt.nodes.new("ShaderNodeVectorMath")
    out.operation = "SCALE"
    out.inputs[0].default_value = rgb
    L.new(f, out.inputs["Scale"])
    L.new(out.outputs[0], bsdf.inputs["Base Color"])
    return m


def base_rgb(mat):
    return tuple(mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value)[:3]


def bake_slab_frame(tabs, painted, parts):
    """The `_plane` UV map on the raised tabs: each face's (across, down) in
    the frame of the painted slab whose normal it lies nearest, measured
    from the world origin as the painting is."""
    normals = []
    for o in parts:
        if o in tabs:
            continue
        r3 = o.matrix_world.to_3x3()
        for poly in o.data.polygons:
            if o.material_slots[poly.material_index].material is painted:
                n = (r3 @ poly.normal).normalized()
                if n.z > 0.2 and all(n.angle(q) > 0.03 for q in normals):
                    normals.append(n)
    for o in tabs:
        me, mw = o.data, o.matrix_world
        uv = me.uv_layers.new(name="_plane")
        for poly in me.polygons:
            n = (mw.to_3x3() @ poly.normal).normalized()
            m = min(normals, key=lambda q: n.angle(q))
            D = (Vector((0.0, 0.0, -1.0)) + m * m.z).normalized()
            A = m.cross(Vector((0.0, 0.0, 1.0))).normalized()
            for li in poly.loop_indices:
                P = mw @ me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (P.dot(A), P.dot(D))
    return len(normals)


# --- the stage -------------------------------------------------------------------------

def stage(scene, parts, offsets=(0.0,), figures_at=()):
    """A ground, a walk, a street and a drive (one per lot, at each of
    `offsets` along X), a sky and a sun, as the house builders' renders have
    them, and a 1.7 m figure at each of `figures_at`; returns the camera and
    the figures."""
    def mat(name, rgb):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = 0.85
        return m

    def box(name, m, x0, x1, y0, y1, z0, z1):
        me = bpy.data.meshes.new(name)
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        me.from_pydata(v, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
        me.materials.append(m)
        scene.collection.objects.link(bpy.data.objects.new(name, me))

    def bounds(objs):
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts))
    ref = bpy.data.collections.get("reference")
    refs = list(ref.all_objects) if ref else []
    lot = [o for o in refs if o.name.startswith("lot") and o.type == "MESH"]
    drive = [o for o in refs if o.name.startswith("driveway") and o.type == "MESH"]
    kerb = bounds(lot)[2] if lot else bounds(parts)[2] - 6.0
    walk = mat("_walk", (0.62, 0.60, 0.56))
    box("_ground", mat("_ground", (0.36, 0.44, 0.26)), -80, 80, -80, 80, -0.30, -0.01)
    box("_walk", walk, -80, 80, kerb - 1.6, kerb, -0.30, 0.0)
    box("_street", mat("_street", (0.28, 0.28, 0.30)), -80, 80, -80, kerb - 1.6, -0.30, -0.005)
    if drive:
        x0, x1, _, y1 = bounds(drive)
        for k, dx in enumerate(offsets):
            box(f"_drive{k}", walk, dx + x0 + 0.1, dx + x1 - 0.2, kerb - 1.6, y1, -0.30, 0.004)
    figs = []
    for k, figure_at in enumerate(figures_at):
        # a 1.7 m standing figure, as the builders' reference one: a
        # 12-sided body and a ball head
        import bmesh
        bm = bmesh.new()
        ring = [bm.verts.new((0.18 * math.cos(math.tau * i / 12), 0.18 * math.sin(math.tau * i / 12), 0.0)) for i in range(12)]
        top = [bm.verts.new((v.co.x, v.co.y, 1.30)) for v in ring]
        bm.faces.new(list(reversed(ring)))
        bm.faces.new(top)
        for i in range(12):
            bm.faces.new((ring[i], ring[(i + 1) % 12], top[(i + 1) % 12], top[i]))
        head = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.17)
        for v in head["verts"]:
            v.co.z += 1.70 - 0.17
        me = bpy.data.meshes.new(f"_figure{k}")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat("_figure", (0.30, 0.22, 0.40)))
        fig = bpy.data.objects.new(f"_figure{k}", me)
        fig.location = figure_at
        scene.collection.objects.link(fig)
        figs.append(fig)
    world = bpy.data.worlds.new("_sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.62, 0.86, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65
    scene.world = world
    sun = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(2)
    sun.rotation_euler = Vector((-0.45, -0.70, 0.55)).to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(sun)
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    scene.collection.objects.link(cam)
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
    return cam, figs


def row_shot(name, x0, x1, top):
    """A `lineup_...` shot framed on a row of houses from x0 to x1 whose
    tallest reaches `top`, rather than on four lots, and its size: the
    elevation straight on with a metre and a half of margin each side, from a
    metre under the ground to a metre and a half over the top; the
    three-quarter from the street right of the row at eye height, near enough
    that the row fills the frame. Returns (eye, target, lens, ortho, size)."""
    cx, span = (x0 + x1) / 2, x1 - x0
    w = LINEUP_SIZE[0]
    if name == "lineup_elevation":
        zc, tall = (top + 0.5) / 2, top + 2.5
        return (cx, -80.0, zc), (cx, 0.0, zc), 50, span + 3.0, (w, int(w * tall / (span + 3.0)) // 2 * 2)
    return (cx + 0.30 * span, -1.0 - 1.02 * span, 1.75), (cx + 0.05 * span, -1.0, top * 0.42), 30, None, (w, 760)


def bounds_x(objs):
    xs = [(o.matrix_world @ Vector(c)).x for o in objs for c in o.bound_box]
    return min(xs), max(xs)


def stack_rows(paths, out):
    """The rows' renders, one under another, the first on top, into `out`."""
    import numpy as np
    imgs = [bpy.data.images.load(p) for p in paths]
    w, h = imgs[0].size
    arrays = []
    for img in imgs:
        a = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(a)
        arrays.append(a.reshape(h, w, 4))
    # Blender's pixels run from the bottom row up, so the first row goes last
    stacked = np.concatenate(list(reversed(arrays)), axis=0)
    res = bpy.data.images.new("_rows", w, h * len(imgs), alpha=False)
    res.pixels.foreach_set(stacked.ravel())
    res.filepath_raw = out
    res.file_format = "PNG"
    res.save()
    for p in paths:
        os.remove(p)


def main():
    variants, folder, shots, scale, origins, figure, gap, rows, keep_eye = args()
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    export = bpy.data.collections["export"]
    by = {v: [o for o in export.all_objects if o.type == "MESH" and o.get("kyt_variant") == v] for v in variants}
    missing = [v for v in variants if not by[v]]
    if missing:
        raise SystemExit(f"cartoon_preview: export has no parts of variant {missing}")
    # a list first: setting hide_render while walking all_objects itself sets nothing
    for o in list(export.all_objects):
        o.hide_render = o.get("kyt_variant") not in variants
    for name in ("reference", "authored"):
        c = bpy.data.collections.get(name)
        if c:
            c.hide_render = True
    def named(m, surface):
        """A material of `surface` by name: `..._roof`, `..._roof_shake`."""
        tail = m.name.rsplit(surface, 1)
        return len(tail) == 2 and (tail[0].endswith("_") or not tail[0]) and (not tail[1] or tail[1].startswith("_"))
    for v in variants:
        parts = by[v]
        used = {s.material for o in parts for s in o.material_slots if s.material}
        # every roof material but a metal one takes the shingles, every wall
        # material the siding (the log's logs and its batten gable alike)
        roofs = [m for m in used if named(m, "roof") and not m.name.endswith("_metal")]
        swap, slabs = {}, 0
        walls = [m for m in used if named(m, "walls") and not m.name.endswith(("_walls_log", "_walls_batten"))]
        for bw in [m for m in used if m.name.endswith("_walls_batten")]:
            painted_b = battens(f"_battens_{v}_{bw.name}", base_rgb(bw))
            swap[bw] = (painted_b, painted_b)
        for lw in [m for m in used if m.name.endswith("_walls_log")]:
            painted_logs = logs(f"_logs_{v}_{lw.name}", base_rgb(lw))
            swap[lw] = (painted_logs, painted_logs)
        tabs = [o for o in parts if o.name.endswith("shingles")]
        for roof in roofs:
            painted = shingles(f"_shingles_{v}_{roof.name}", base_rgb(roof))
            raised = shingles(f"_tabs_{v}_{roof.name}", base_rgb(roof), use_uv=True)
            swap[roof] = (painted, raised)
        for wall in walls:
            side = siding(f"_siding_{v}_{wall.name}", base_rgb(wall), origins.get(v, 0.0))
            swap[wall] = (side, side)
        for st in [m for m in used if named(m, "stone")]:
            # a fieldstone stack and its raised stones on the one stone grid
            painted_st = stones(f"_stones_{v}_{st.name}", base_rgb(st))
            swap[st] = (painted_st, painted_st)
        for o in parts:
            for slot in o.material_slots:
                if slot.material in swap:
                    slot.material = swap[slot.material][1 if o in tabs else 0]
        for roof in roofs:
            mine = [o for o in tabs if any(s.material is swap[roof][1] for s in o.material_slots)]
            slabs += bake_slab_frame(mine, swap[roof][0], parts)      # in the house's frame, before any move
        print(f"cartoon_preview: {v}: {len(parts)} parts, {len(tabs)} raised-tab parts on {slabs} slab planes; "
              f"shingles {ck.SHINGLE_E} x {ck.SHINGLE_W} m, siding {SIDING} m from z {origins.get(v, 0.0)}")
    groups = [variants]
    if gap is None:
        # several variants stand on neighbouring lots, for the shot only
        ref = bpy.data.collections.get("reference")
        lots = [o for o in (ref.all_objects if ref else []) if o.name.startswith("lot") and o.type == "MESH"]
        lot_w = 9.0
        if lots:
            xs = [(lots[0].matrix_world @ Vector(c)).x for c in lots[0].bound_box]
            lot_w = max(xs) - min(xs)
        offsets = [k * lot_w for k in range(len(variants))]
        placed = {0: dict(zip(variants, offsets))}
        figures_at = [(lot_w / 2, -8.0, 0.0)] if figure else []
        frame = None
    else:
        # a kit of different widths: in rows, each house `gap` clear of the
        # one before it by their own widths, every row starting at x = 0
        per = math.ceil(len(variants) / rows)
        groups = [variants[k:k + per] for k in range(0, len(variants), per)]
        placed, spans = {}, []
        for r, group in enumerate(groups):
            x, placed[r] = 0.0, {}
            for v in group:
                lo, hi = bounds_x(by[v])
                placed[r][v] = x - lo
                x += (hi - lo) + gap
            spans.append(x - gap)
        everything = [o for v in variants for o in by[v]]
        top = max((o.matrix_world @ Vector(c)).z for o in everything for c in o.bound_box)
        front = min((o.matrix_world @ Vector(c)).y for o in everything for c in o.bound_box)
        frame = (0.0, max(spans), top)
        offsets = [dx for r in placed for dx in placed[r].values()]
        figures_at = [(-1.2, front - 1.0, 0.0)] if figure else []
    cam, _ = stage(scene, [o for v in variants for o in by[v]], offsets, figures_at=figures_at)
    for name in shots:
        eye, target, lens = SHOTS[name][:3]
        ortho = SHOTS[name][3] if len(SHOTS[name]) > 3 else None
        eye, target = Vector(eye) * scale, Vector(target) * scale
        if keep_eye and SHOTS[name][0][2] <= 2.0:
            eye.z = SHOTS[name][0][2]
        size = LINEUP_SIZE if name.startswith("lineup") else SIZE
        if frame is not None and name.startswith("lineup"):
            eye, target, lens, ortho, size = row_shot(name, *frame)
            eye, target = Vector(eye), Vector(target)
            scale_o = 1.0
        else:
            scale_o = scale
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho:
            cam.data.ortho_scale = ortho * scale_o
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 600
        scene.render.resolution_x, scene.render.resolution_y = size
        out = os.path.join(folder, f"painted_{name}.png")
        paths = []
        for r, group in enumerate(groups):
            # each row in turn at its place, the others out of the shot
            for v in variants:
                for o in by[v]:
                    o.location.x = placed[r][v] if v in placed[r] else 0.0
                    o.hide_render = v not in placed[r]
            scene.render.filepath = out if len(groups) == 1 else os.path.join(folder, f"_row{r}_{name}.png")
            bpy.ops.render.render(write_still=True)
            paths.append(scene.render.filepath)
        if len(groups) > 1:
            stack_rows(paths, out)
        print(f"cartoon_preview: rendered {out}")

main()
