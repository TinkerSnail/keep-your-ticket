"""The paint canvas for a prop's own texture, and its one material.

    /Applications/Blender.app/Contents/MacOS/Blender --background <prop>.blend \
        --python tools/blender/paint_canvas.py -- [--size 2048] [--orm-size 1024] [--grain]
        [--weather part,part] [--overwrite] [--guide-only] [--save]

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

`--weather arm_loop,scroll,armrest` weathers the painted iron (a material whose
name contains "iron") of the parts whose names start with those words, read
from the `kyt_part` record Make game mesh leaves on each face: paint faded on
top and worn through to dark, hand-polished iron where hands rest, chips on
edges with rust round them and streaking down, grime in the crevices. Rust is
rough and bare iron metallic in the ORM too.

Both are starting points to paint over, not a finish.

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

# Weathering on painted iron, linear colours and 0-1 amounts.
FADED = (0.014, 0.075, 0.036, 1.0)  # the green bleached on surfaces facing the sky
BARE_IRON = (0.02, 0.019, 0.018, 1.0)  # paint worn through, polished by hands
RUST = (0.16, 0.05, 0.012, 1.0)
FADE = 0.5  # how far the tops fade
HAND_WEAR = 0.85  # how much of the paint hands have worn off the tops
CHIP_EDGE_M = 0.006  # how far round an edge the chipping reaches
GRIME = 0.55  # how dark the crevices get
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
    return g.mix(wood, g.grey(shade), 1.0, "MULTIPLY")


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
    streak = g.math("MULTIPLY", g.ramp(g.noise((30.0, 30.0, 2.5), 2.0), 0.58, 0.78),
                    g.math("MULTIPLY", g.math("SUBTRACT", 1.0, up), 0.6))
    hand = g.math("MULTIPLY", up, g.ramp(g.noise((6.0, 6.0, 6.0), 3.0), 0.42, 0.6))
    bare = g.math("MULTIPLY", g.math("MAXIMUM", chip, g.math("MULTIPLY", hand, HAND_WEAR)), w)
    rust = g.math("MULTIPLY", g.math("MAXIMUM", halo, streak), w)
    # Grime where the surface is hemmed in by other parts.
    ao = g.node("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.03
    ao.samples = 16
    grime = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, ao.outputs["AO"]), g.math("MULTIPLY", w, GRIME))

    colour = g.mix(base, FADED, g.math("MULTIPLY", up, g.math("MULTIPLY", w, FADE)))
    colour = g.mix(colour, RUST, rust)
    colour = g.mix(colour, BARE_IRON, bare)
    colour = g.mix(colour, g.grey(g.math("SUBTRACT", 1.0, grime)), 1.0, "MULTIPLY")
    r = g.lerp(g.lerp(rough, RUST_ROUGH, rust), BARE_ROUGH, bare)
    m = g.lerp(g.lerp(metal, RUST_METAL, rust), BARE_METAL, bare)
    return colour, r, m


def mark_weather(obj, prefixes):
    """Set the face attribute `kyt_weather` to 1 on faces of the named parts."""
    me = obj.data
    if "kyt_part" not in me.attributes or "kyt_parts" not in me:
        raise SystemExit("paint_canvas: the game mesh doesn't record its parts; "
                         "make it again with the current Make game mesh")
    names = json.loads(me["kyt_parts"])
    wanted = [any(n.startswith(p) for p in prefixes) for n in names]
    part = me.attributes["kyt_part"].data
    values = [1.0 if wanted[part[i].value] else 0.0 for i in range(len(me.polygons))]
    attr = me.attributes.get("kyt_weather") or me.attributes.new("kyt_weather", "FLOAT", "FACE")
    attr.data.foreach_set("value", values)
    return sum(values), sorted({n for n, w in zip(names, wanted) if w})


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

    def weathers(mat):
        return weather and "iron" in mat.name

    def colour_of(g, mat, b):
        if grain and "timber" in mat.name:
            return wood_grain(g, base(b))
        if weathers(mat):
            return weathering(g, base(b), b.inputs["Roughness"].default_value,
                              b.inputs["Metallic"].default_value)[0]
        return base(b)

    def orm_of(g, mat, b):
        rough, metal = b.inputs["Roughness"].default_value, b.inputs["Metallic"].default_value
        if weathers(mat):
            _, r, m = weathering(g, base(b), rough, metal)
            return g.rgb(1.0, r, m)
        return (1.0, rough, metal, 1.0)

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
          + (f"; weathered {int(weathered[0])} faces of {', '.join(weathered[1])}" if weather else ""))
    if "--save" in argv:
        bpy.ops.wm.save_mainfile()


main()
