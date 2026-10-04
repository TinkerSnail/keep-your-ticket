"""A render-only painted preview of a cartoony house (2026-10-04): stand-in
painting for its roof and siding, so a build can be judged as it will read
once painted, before anyone paints it. Nothing is ever saved into the blend.

    /Applications/Blender.app/Contents/MacOS/Blender --background <house>.blend \\
        --python tools/blender/cartoon_preview.py -- <variant> <folder> [<shot> ...] \\
        [--scale <s>] [--siding-origin <z>]

Renders the variant (its `kyt_variant` parts in `export`; every other part,
`reference` and `authored` hidden) into <folder> as `painted_<shot>.png`,
every shot in SHOTS or only those named. It changes, in memory only:

- **The roof** (the variant's material ending `_roof`): painted shingles on
  `cartoon_kit`'s grid, read from the kit so the painting and the raised
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
- **The walls** (the material ending `_walls`): lap siding at the standard's
  0.24 m exposure, its courses counted from `--siding-origin` (the main
  floor, 1.55 on the Victorian; 0 by default), its grain magnified with it.

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
}
SIZE = (1800, 1100)
SIDING = 0.24              # the standard's painted lap siding exposure: twice a real one
SIDING_GRAIN = 2.0         # its grain magnified with it


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"--scale": 1.0, "--siding-origin": 0.0}
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] in opts:
            opts[argv[i]] = float(argv[i + 1])
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    if len(rest) < 2:
        raise SystemExit("cartoon_preview: give <variant> <folder> [<shot> ...]")
    shots = rest[2:] or list(SHOTS)
    unknown = [s for s in shots if s not in SHOTS]
    if unknown:
        raise SystemExit(f"cartoon_preview: no shot {unknown}; there are {list(SHOTS)}")
    return rest[0], rest[1], shots, opts["--scale"], opts["--siding-origin"]


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
    # its clusters' t_mid measure them (the world position dotted with the
    # face's downhill and across directions)
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], nsep.inputs[0])
    down = V("NORMALIZE", V("ADD", V("SCALE", geo.outputs["Normal"], scale=nsep.outputs["Z"]), (0.0, 0.0, -1.0)))
    across = V("NORMALIZE", V("CROSS_PRODUCT", geo.outputs["Normal"], (0.0, 0.0, 1.0)))
    s = M("DIVIDE", V("DOT_PRODUCT", geo.outputs["Position"], down), ck.SHINGLE_E)
    t = M("DIVIDE", V("DOT_PRODUCT", geo.outputs["Position"], across), ck.SHINGLE_W)
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

def stage(scene, parts):
    """A ground, a walk, a street and a drive, a sky and a sun, as the house
    builders' renders have them; returns the camera."""
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
        box("_drive", walk, x0 + 0.1, x1 - 0.2, kerb - 1.6, y1, -0.30, 0.004)
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
    return cam


def main():
    variant, folder, shots, scale, siding_origin = args()
    os.makedirs(folder, exist_ok=True)
    scene = bpy.context.scene
    export = bpy.data.collections["export"]
    parts = [o for o in export.all_objects if o.type == "MESH" and o.get("kyt_variant") == variant]
    if not parts:
        raise SystemExit(f"cartoon_preview: export has no parts of variant {variant!r}")
    # a list first: setting hide_render while walking all_objects itself sets nothing
    for o in list(export.all_objects):
        o.hide_render = o.get("kyt_variant") != variant
    for name in ("reference", "authored"):
        c = bpy.data.collections.get(name)
        if c:
            c.hide_render = True
    used = {s.material for o in parts for s in o.material_slots if s.material}
    roof = next(m for m in used if m.name.endswith("_roof"))
    walls = next(m for m in used if m.name.endswith("_walls"))
    painted = shingles("_shingles", base_rgb(roof))
    raised = shingles("_tabs", base_rgb(roof), use_uv=True)
    side = siding("_siding", base_rgb(walls), siding_origin)
    tabs = [o for o in parts if o.name.endswith("shingles")]
    for o in parts:
        for slot in o.material_slots:
            if slot.material == roof:
                slot.material = raised if o in tabs else painted
            elif slot.material == walls:
                slot.material = side
    slabs = bake_slab_frame(tabs, painted, parts)
    print(f"cartoon_preview: {variant}: {len(parts)} parts, {len(tabs)} raised-tab parts on {slabs} slab planes; "
          f"shingles {ck.SHINGLE_E} x {ck.SHINGLE_W} m, siding {SIDING} m from z {siding_origin}")
    cam = stage(scene, parts)
    for name in shots:
        eye, target, lens = SHOTS[name]
        eye, target = Vector(eye) * scale, Vector(target) * scale
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 600
        scene.render.resolution_x, scene.render.resolution_y = SIZE
        scene.render.filepath = os.path.join(folder, f"painted_{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"cartoon_preview: rendered {scene.render.filepath}")


main()
