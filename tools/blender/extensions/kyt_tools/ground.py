"""The Ground box: the world's ground as the height grid's tiles, sculpted in Blender.

Stage 3 of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-14). The ground is
`assets/source/world_ground/height/x{tx}_z{tz}.exr`: one float32 height per 2 m node, in 1 km
tiles of 501 x 501 nodes that share their edges (`grid.json`). Those files are the ground; these
buttons are one way to edit them, Photoshop the other.

- **Load tiles** brings tiles into the open file as meshes in a `Ground tiles` collection: the
  tiles named in the box ("x0_z0, x1_z0"), the tile under the 3D cursor, or the tiles under the
  selected objects. One object per tile, `ground_x{tx}_z{tz}`, one vertex per node that has
  ground, at its world place (Blender x, y = Godot x, -z; z = the height exactly as stored).
  Nodes with no ground are left out, so their faces are missing. Each tile wears its colour image
  (`colour/x{tx}_z{tz}.png`), so it is sculpted in the colour the game shows; Solid shading is set
  to show textures. Loading a tile that is loaded already reloads it from its file, unless it has
  unsaved sculpting. Its object is locked against moving, turning and scaling.
- **Sculpt** with any brush. While a tile is sculpted, Lock X and Lock Y are on (and go back to
  what they were for anything else), dynamic topology is off and symmetry is off, so a vertex only
  moves up or down. A brush stops at a tile's edge: each tile is its own object.
- **Save tiles** writes the heights back as one recorded grid edit, `tools/ground_grid_edit.py`'s
  `apply_values`, logged in `edits.json` like G1-G7 under the short name and the line of why typed
  above it, and undoable. Only nodes moved by more than 1 mm are written; every other node keeps
  its bytes. A node on a tile's edge is written into every tile that holds it, loaded or not. It
  refuses, writing nothing, when a vertex moved sideways, vertices were added or removed,
  a tile object was moved or has modifiers or shape keys, a shared edge was sculpted differently in
  two loaded tiles, or a node's file changed since the tile was loaded (load it again). Afterwards
  the tiles it wrote show exactly what is in their files.
- **Undo last ground edit** takes back the newest edit (`ground_grid_edit.py --undo`) if it was
  saved by an editor (this button's Save, or Photoshop's); a named edit such as G7 is the command
  line's to undo. Loaded tiles without unsaved sculpting are reloaded.
- **Send ground to game** runs `tools/ground_send.py` in the background: the changed tiles'
  meshes (`ground_build.py`), the follow step (`ground_follow.py`: rocks, city blocks and roosts
  follow the ground, and the follow of an undone edit is put back), Godot's import, the mount and
  its check, `world_terrain_delta.gd` and the generator, about eight minutes in all. Blender stays
  usable; the box shows each step as it ends. It refuses while a loaded tile has unsaved
  sculpting.

How many tiles sculpt comfortably, measured: `assets/source/world_ground/README.md`, "Editing in
Blender".
"""

import contextlib
import hashlib
import importlib
import io
import json
import math
import os
import re
import subprocess
import sys
import threading
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import checks

COLLECTION = "Ground tiles"
TILE_PROP = "kyt_ground_tile"
NODE_ATTR = "kyt_node"
BASE_ATTR = "kyt_loaded_z"
## How far a vertex may sit from its node in plan before Save calls it moved sideways: the nodes'
## places are whole metres, exact in float32, so anything but zero is a move.
SIDEWAYS_M = 1e-4
## Tiles Load brings in at once: 5 x 5, the most measured (2026-10-14, M1 Pro, 16 GB), which still
## sculpted at 60 frames a second, since a brush works on one tile; see the README.
MAX_LOAD = 25
POLL_S = 0.5
REPORT = "kyt_ground_report"
PREV_LOCKS = "kyt_ground_prev_locks"


# --- the project and its tools -------------------------------------------------

def project_root():
    """The project this extension is part of (it is loaded from the project's own folder), or the
    one the open file is in."""
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), *[os.pardir] * 4))
    if os.path.isfile(os.path.join(here, "project.godot")):
        return here
    return checks.project_root(bpy.data.filepath) if bpy.data.filepath else None


def ground_dir(root):
    return os.path.join(root, "assets", "source", "world_ground")


def tools(root):
    """`tools/ground_grid_edit.py` (with its `gb`, ground_bake.py), read again on every use so a
    tools update reaches the panel without restarting Blender."""
    folder = os.path.join(root, "tools")
    if folder not in sys.path:
        sys.path.insert(0, folder)
    for name in ("ground_bake", "ground_colour_bake", "ground_grid_edit"):
        if name in sys.modules:
            importlib.reload(sys.modules[name])
    import ground_grid_edit
    while sys.path.count(folder) > 1:  # each reload of it puts the folder on the path again
        sys.path.remove(folder)
    return ground_grid_edit


def spec(root):
    g = json.load(open(os.path.join(ground_dir(root), "grid.json")))
    return {"n": int(g["tile_samples"]), "step": float(g["spacing_m"]), "tile": float(g["tile_m"]),
            "tx": range(g["tiles_x"][0], g["tiles_x"][1] + 1), "tz": range(g["tiles_z"][0], g["tiles_z"][1] + 1)}


def tile_name(tx, tz):
    return "x%d_z%d" % (tx, tz)


def parse_tiles(text):
    return [(int(a), int(b)) for a, b in re.findall(r"x\s*(-?\d+)\s*[_ ,]?\s*z\s*(-?\d+)", text or "")]


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tile_objects(scene):
    return sorted((o for o in scene.objects if o.get(TILE_PROP) and o.type == "MESH"), key=lambda o: o[TILE_PROP])


def _report(context, lines):
    context.window_manager[REPORT] = "\n".join(lines)


# --- loading --------------------------------------------------------------------

def tile_mesh(name, H, tx, tz, sp):
    """A tile's mesh: a vertex per node with ground, a quad per cell with four, a triangle per
    cell with three, all facing up; UVs on the colour image's texel centres; each vertex's node
    and the height it was loaded at as attributes."""
    n, step, tile = sp["n"], sp["step"], sp["tile"]
    x0, z0 = tile * tx, tile * tz
    V = np.isfinite(H)
    idx = np.full(H.shape, -1, np.int64)
    idx[V] = np.arange(int(V.sum()))
    rr, cc = np.nonzero(V)
    nodes = (rr * n + cc).astype(np.int32)
    co = np.empty((len(nodes), 3), np.float32)
    co[:, 0] = x0 + step * cc
    co[:, 1] = -(z0 + step * rr)
    co[:, 2] = H[V]
    # Counter-clockwise seen from above (Blender +Z): south-west, south-east, north-east, north-west.
    Q = np.stack([idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:], idx[:-1, :-1]], -1).reshape(-1, 4)
    have = (Q >= 0).sum(1)
    quads = Q[have == 4]
    three = Q[have == 3]
    tris = three[three >= 0].reshape(-1, 3)
    loops = np.concatenate([quads.ravel(), tris.ravel()]).astype(np.int32)
    starts = np.concatenate([np.arange(len(quads)) * 4, len(quads) * 4 + np.arange(len(tris)) * 3]).astype(np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(len(loops))
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(len(starts))
    me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    lr, lc = nodes[loops] // n, nodes[loops] % n
    uv = np.empty((len(loops), 2), np.float32)
    uv[:, 0] = (lc + 0.5) / n
    uv[:, 1] = 1.0 - (lr + 0.5) / n
    me.uv_layers.new(name="UVMap").data.foreach_set("uv", uv.ravel())
    me.attributes.new(NODE_ATTR, "INT", "POINT").data.foreach_set("value", nodes)
    me.attributes.new(BASE_ATTR, "FLOAT", "POINT").data.foreach_set("value", co[:, 2].copy())
    me.shade_smooth()
    for axis in ("x", "y", "z"):
        setattr(me, "use_mirror_" + axis, False)
    return me, nodes


def tile_material(name, png):
    mat = bpy.data.materials.get("ground_colour_" + name) or bpy.data.materials.new("ground_colour_" + name)
    if mat.node_tree is None:
        mat.use_nodes = True
    nt = mat.node_tree
    img = bpy.data.images.load(png, check_existing=True)
    img.reload()
    img.colorspace_settings.name = "sRGB"
    img.alpha_mode = "NONE"  # alpha 0 is only where there is no ground, and no face
    tex = next((nd for nd in nt.nodes if nd.type == "TEX_IMAGE"), None) or nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    tex.extension = "EXTEND"
    tex.location = (-400, 300)
    bsdf = next((nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED"), None)
    if bsdf is not None:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.97
    nt.nodes.active = tex  # Solid shading's Texture colour shows the active image node
    return mat


def collection(scene):
    coll = bpy.data.collections.get(COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION)
    if coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    return coll


def set_locks(scene):
    """Lock X and Y on in this scene's Sculpt settings, remembering what they were."""
    ts = scene.tool_settings
    if ts.sculpt is None:
        return  # made the first time the scene enters Sculpt mode; the watcher sets them then
    s = ts.sculpt
    if not (s.lock_x and s.lock_y):
        if PREV_LOCKS not in scene:
            scene[PREV_LOCKS] = [bool(s.lock_x), bool(s.lock_y)]
        s.lock_x = s.lock_y = True


def show_tiles(context):
    """Each 3D view sees far enough for a tile and shows its colour in Solid shading."""
    changed = set()
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            if space.clip_end < 10000.0:
                space.clip_end = 10000.0
                changed.add("the view's clip end to 10 km")
            if space.clip_start < 0.1:
                space.clip_start = 0.1
                changed.add("its clip start to 0.1 m")
            if space.shading.type == "SOLID" and space.shading.color_type != "TEXTURE":
                space.shading.color_type = "TEXTURE"
                changed.add("Solid shading's colour to Texture")
    return sorted(changed)


def load(context, tiles):
    """Loads the tiles; returns (ok, lines)."""
    root = project_root()
    if root is None:
        return False, ["This extension isn't in the Keep Your Ticket project, and the open file isn't either."]
    sp = spec(root)
    gge = tools(root)
    gd = ground_dir(root)
    tiles = list(dict.fromkeys(tiles))
    if not tiles:
        return False, ["Name the tiles first, as x0_z0, x1_z0."]
    if len(tiles) > MAX_LOAD:
        return False, ["That is %d tiles; load at most %d at once (5 x 5), the most measured sculpting smoothly." % (
            len(tiles), MAX_LOAD)]
    scene = context.scene
    if context.object is not None and context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    loaded = {o[TILE_PROP]: o for o in tile_objects(scene)}
    coll = None
    lines, done = [], []
    for tx, tz in tiles:
        name = tile_name(tx, tz)
        exr = os.path.join(gd, "height", name + ".exr")
        if tx not in sp["tx"] or tz not in sp["tz"] or not os.path.exists(exr):
            lines.append("%s isn't a tile of the grid (x %d..%d, z %d..%d)." % (
                name, sp["tx"][0], sp["tx"][-1], sp["tz"][0], sp["tz"][-1]))
            continue
        obj = loaded.get(name)
        if obj is not None:
            st = tile_state(obj, sp)
            if st["problems"] or st["changed"].any():
                lines.append("%s has unsaved sculpting (or changes Save would refuse): Save tiles first, or delete "
                             "it to load it fresh." % name)
                continue
        t0 = time.time()
        H = gge.gb.read_exr(exr)[0]
        if not np.isfinite(H).any():
            lines.append("%s holds no ground." % name)
            continue
        me, nodes = tile_mesh("ground_" + name, H, tx, tz, sp)
        me.materials.append(tile_material(name, os.path.join(gd, "colour", name + ".png")))
        if obj is None:
            obj = bpy.data.objects.new("ground_" + name, me)
            coll = coll or collection(scene)
            coll.objects.link(obj)
        else:
            old = obj.data
            obj.data = me
            if old.users == 0:
                bpy.data.meshes.remove(old)
            me.name = "ground_" + name
        obj.matrix_world = Matrix.Identity(4)
        obj.lock_location = obj.lock_rotation = obj.lock_scale = (True, True, True)
        obj[TILE_PROP] = name
        obj["kyt_ground_sha"] = sha_file(exr)
        obj["kyt_ground_vertices"] = len(me.vertices)
        obj["kyt_ground_faces"] = len(me.polygons)
        obj["kyt_ground_nodes_sha"] = hashlib.sha256(nodes.tobytes()).hexdigest()
        done.append("%s (%s vertices, %.1f s)" % (name, format(len(me.vertices), ","), time.time() - t0))
    set_locks(scene)
    if done:
        lines.insert(0, "Loaded %s into '%s'." % (", ".join(done), COLLECTION))
        view = show_tiles(context)
        if view:
            lines.append("Set %s." % ", ".join(view))
        lines.append("Frame them with View > Frame Selected. Sculpt with any brush; Save tiles writes them back.")
    return bool(done), lines


def tiles_under_cursor(context):
    c = context.scene.cursor.location
    return [(math.floor(c.x / 1000.0), math.floor(-c.y / 1000.0))]


def tiles_under_selection(context):
    out = []
    for obj in context.selected_objects:
        pts = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        xa, xb = min(p.x for p in pts), max(p.x for p in pts)
        za, zb = min(-p.y for p in pts), max(-p.y for p in pts)
        for tx in range(math.floor(xa / 1000.0), math.floor((xb - 1e-6) / 1000.0) + 1):
            for tz in range(math.floor(za / 1000.0), math.floor((zb - 1e-6) / 1000.0) + 1):
                out.append((tx, tz))
    return sorted(set(out))


# --- a tile's state, saving -----------------------------------------------------

def tile_state(obj, sp, min_change=0.001):
    """What Save would make of a tile object: its problems (sentences), and per vertex its node,
    height, loaded height and whether it moved by more than `min_change`."""
    name = obj[TILE_PROP]
    me = obj.data
    out = {"name": name, "obj": obj, "problems": [], "changed": np.zeros(0, bool)}
    p = out["problems"]
    if obj.modifiers:
        p.append("%s has modifiers (%s): apply or remove them." % (name, ", ".join(m.name for m in obj.modifiers)))
    if me.shape_keys is not None:
        p.append("%s has shape keys: apply or remove them." % name)
    # matrix_basis is read from the object's location, rotation and scale (deltas too) as they
    # stand, not from the last depsgraph update.
    if obj.parent is not None or any(abs(a - b) > 1e-6 for ra, rb in zip(obj.matrix_basis, Matrix.Identity(4))
                                     for a, b in zip(ra, rb)):
        p.append("%s was moved, turned or scaled as an object: set its location and rotation to 0 and its scale "
                 "to 1 (Object > Clear)." % name)
    # Faces carry nothing Save reads (switching dynamic topology on and off splits every quad), so
    # only the vertices count.
    nv = len(me.vertices)
    if nv != obj.get("kyt_ground_vertices") or NODE_ATTR not in me.attributes or BASE_ATTR not in me.attributes:
        p.append("%s: vertices were added or removed (it was loaded with %s, has %s). Undo that, or delete it "
                 "and load it again." % (name, format(obj.get("kyt_ground_vertices", 0), ","), format(nv, ",")))
        return out
    co = np.empty(nv * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    node = np.empty(nv, np.int32)
    me.attributes[NODE_ATTR].data.foreach_get("value", node)
    base = np.empty(nv, np.float32)
    me.attributes[BASE_ATTR].data.foreach_get("value", base)
    if hashlib.sha256(node.tobytes()).hexdigest() != obj.get("kyt_ground_nodes_sha"):
        p.append("%s: its vertices were remade or reordered. Delete it and load it again." % name)
        return out
    tx, tz = (int(v) for v in name[1:].split("_z"))
    n, step, tile = sp["n"], sp["step"], sp["tile"]
    gx = tile * tx + step * (node % n)
    gz = tile * tz + step * (node // n)
    side = np.maximum(np.abs(co[:, 0] - gx), np.abs(co[:, 1] + gz))
    moved = side > SIDEWAYS_M
    if moved.any():
        p.append("%s: %s vertices moved sideways, up to %.3f m. With Lock X and Y on a brush only lifts and "
                 "lowers; undo those strokes, or delete it and load it again." % (
                     name, format(int(moved.sum()), ","), float(side.max())))
    z = co[:, 2]
    if not np.isfinite(z).all():
        p.append("%s has vertices with no height." % name)
    out.update(node=node, z=z, base=base, gx=gx, gz=gz, changed=np.abs(z.astype(np.float64) - base) > min_change)
    return out


@contextlib.contextmanager
def object_mode(context):
    """Object mode for the duration (a sculpt or an edit reaches the mesh's data on leaving its
    mode), then the mode it was in."""
    obj = context.view_layer.objects.active
    mode = obj.mode if obj is not None else "OBJECT"
    if mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    try:
        yield
    finally:
        if mode != "OBJECT" and context.view_layer.objects.active is obj:
            try:
                bpy.ops.object.mode_set(mode=mode)
            except RuntimeError:
                pass


def refresh(obj, gb, gd, sp):
    """Sets a loaded tile to what its file holds; returns a sentence when it can't."""
    name = obj[TILE_PROP]
    exr = os.path.join(gd, "height", name + ".exr")
    H = gb.read_exr(exr)[0]
    me = obj.data
    node = np.empty(len(me.vertices), np.int32)
    me.attributes[NODE_ATTR].data.foreach_get("value", node)
    z = H.ravel()[node]
    if not np.isfinite(z).all():
        return "%s: its file has no ground at some of its vertices now; delete it and load it again." % name
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co[:, 2] = z
    me.vertices.foreach_set("co", co.ravel())
    me.attributes[BASE_ATTR].data.foreach_set("value", z.astype(np.float32))
    me.update()
    obj["kyt_ground_sha"] = sha_file(exr)
    for mat in me.materials:  # an edit may carry colour too (a Photoshop save)
        for nd in mat.node_tree.nodes if mat and mat.node_tree else []:
            if nd.type == "TEX_IMAGE" and nd.image is not None:
                nd.image.reload()
    if int(np.isfinite(H).sum()) != len(node):
        return "%s's file has ground the loaded mesh lacks; load it again to see it." % name
    return None


def snake(text):
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9_]", "", re.sub(r"[\s\-]+", "_", (text or "").strip().lower()))).strip("_")


def save(context, name, why):
    """Save tiles; returns (ok, lines)."""
    root = project_root()
    if root is None:
        return False, ["This extension isn't in the Keep Your Ticket project, and the open file isn't either."]
    scene = context.scene
    objs = tile_objects(scene)
    if not objs:
        return False, ["No ground tiles are loaded: Load tiles first."]
    sp = spec(root)
    gge = tools(root)
    gd = ground_dir(root)
    with object_mode(context):
        states = [tile_state(o, sp, gge.MIN_CHANGE) for o in objs]
        problems = [p for st in states for p in st["problems"]]
        if problems:
            return False, ["Not saved; nothing was written."] + problems
        per = {}
        for st in states:
            for i in np.flatnonzero(st["changed"]):
                key = (int(st["gx"][i]), int(st["gz"][i]))
                per.setdefault(key, []).append((st["name"], np.float32(st["z"][i]), np.float32(st["base"][i])))
        values, expect, edges = {}, {}, {}
        for key, seen in per.items():
            if len(seen) > 1:
                news = [float(v) for _, v, _ in seen]
                if max(news) - min(news) > gge.MIN_CHANGE or len({b.tobytes() for _, _, b in seen}) > 1:
                    pair = " and ".join(sorted({t for t, _, _ in seen}))
                    k, d = edges.get(pair, (0, 0.0))
                    edges[pair] = (k + 1, max(d, max(news) - min(news)))
            values[key] = float(seen[0][1])
            expect[key] = float(seen[0][2])
        if edges:
            return False, ["Not saved; nothing was written."] + [
                "The edge between %s was sculpted differently in each at %d nodes, up to %.2f m apart. Undo the "
                "strokes on one side: sculpt an edge from one tile, and Save copies it to the other." % (pair, k, d)
                for pair, (k, d) in sorted(edges.items())]
        if not values:
            return True, ["Nothing moved by more than 1 mm: no edit recorded, no file written."]
        name, why = snake(name), " ".join((why or "").split())
        if not name or not why:
            return False, ["Not saved: type a short name for the edit and one line of why above Save tiles."]
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                entry = gge.apply_values(gd, name, why, values, expect, made_by="Blender panel: Save tiles")
        except SystemExit as e:
            return False, ["Not saved: %s." % str(e).rstrip(".")]
        if entry is None:
            return True, ["Nothing moved by more than 1 mm: no edit recorded, no file written."]
        notes = [refresh(o, gge.gb, gd, sp) for o in objs if o[TILE_PROP] in entry["tiles"]]
    sculpted = sorted({st["name"] for st in states if st["changed"].any()})
    copied = [t for t in entry["tiles"] if t not in sculpted]
    lines = ["Saved %s %s: %s nodes in %s." % (entry["id"], entry["name"], format(entry["nodes"], ","),
                                               ", ".join(entry["tiles"]))]
    if copied:
        lines.append("Edge nodes were copied into %s, which share%s them." % (", ".join(copied), "s" if len(copied) == 1 else ""))
    lines += [n for n in notes if n]
    lines.append("Send ground to game to see it there; Undo last ground edit takes it back.")
    scene.kyt_ground_edit_name = ""
    scene.kyt_ground_edit_why = ""
    return True, lines


def unsaved(scene, sp):
    """Loaded tiles with sculpting not yet saved."""
    out = []
    for o in tile_objects(scene):
        st = tile_state(o, sp)
        if st["problems"] or st["changed"].any():
            out.append(o[TILE_PROP])
    return out


def last_edit(root):
    p = os.path.join(ground_dir(root), "edits.json")
    edits = json.load(open(p))["edits"] if os.path.exists(p) else []
    return edits[-1] if edits else None


# --- sending, in the background --------------------------------------------------

class Job:
    """One ground_send.py run: its output read on a thread, shown by a timer."""

    def __init__(self, cmd, cwd):
        self.output = []
        self.code = None
        self.started, self.ended = time.time(), None
        self.drawn_final = False
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        env["PYTHONUNBUFFERED"] = "1"
        self.proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            self.output.append(line.rstrip("\n"))
        self.code = self.proc.wait()
        self.ended = time.time()

    @property
    def running(self):
        return self.ended is None

    def step(self):
        for line in reversed(self.output):
            if line.startswith("step "):
                return line[5:]
        return "starting"

    def lines(self):
        shown = [l for l in self.output if l.startswith(("ok ", "FAIL", "note", "Ground sent"))]
        if not self.running and self.code and not any(l.startswith("FAIL") for l in shown):
            shown += ["FAIL " + l for l in self.output[-3:]] or ["FAIL exit %d" % self.code]
        return shown

    def status(self):
        elapsed = (self.ended or time.time()) - self.started
        clock = "%d:%02d" % (elapsed // 60, elapsed % 60)
        if self.running:
            return "Send ground to game: running, %s" % clock
        return "Send ground to game: %s in %s" % ("done" if self.code == 0 else "stopped", clock)


_job = None


def _redraw():
    wm = bpy.context.window_manager
    for window in wm.windows if wm else []:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _tick():
    _redraw()
    if _job is None:
        return None
    if _job.running or (not _job.drawn_final and time.time() - _job.ended < 5):
        return POLL_S
    return None


def send(context):
    global _job
    from . import handback
    root = project_root()
    if root is None:
        return False, ["This extension isn't in the Keep Your Ticket project, and the open file isn't either."]
    if _job is not None and _job.running:
        return False, ["Send ground to game is still running."]
    other = handback.current()
    if other is not None and other.running:
        return False, ["%s is running; send the ground when it has finished." % other.title]
    sp = spec(root)
    with object_mode(context):
        waiting = unsaved(context.scene, sp)
    if waiting:
        return False, ["%s %s sculpting not saved yet: Save tiles first, or the game gets the files as they are." % (
            ", ".join(waiting), "has" if len(waiting) == 1 else "have")]
    cmd = [sys.executable, os.path.join(root, "tools", "ground_send.py"), "--blender", bpy.app.binary_path]
    try:
        _job = Job(cmd, root)
    except OSError as exc:
        return False, ["Couldn't start tools/ground_send.py: %s" % exc]
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=POLL_S, persistent=True)
    return True, ["Sending the ground to the game: about eight minutes. Blender stays usable."]


# --- the sculpt guard -------------------------------------------------------------

def _view3d(window):
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            for region in area.regions:
                if region.type == "WINDOW":
                    return area, region
    return None, None


def _guard():
    """While a ground tile is sculpted: Lock X and Y on, dynamic topology and symmetry off. When
    something else is sculpted, the locks go back to what they were."""
    try:
        wm = bpy.context.window_manager
        for window in wm.windows if wm else []:
            scene, obj = window.scene, window.view_layer.objects.active
            s = scene.tool_settings.sculpt
            if obj is None or obj.mode != "SCULPT" or s is None:
                continue
            if obj.get(TILE_PROP):
                set_locks(scene)
                me = obj.data
                for axis in ("x", "y", "z"):
                    if getattr(me, "use_mirror_" + axis):
                        setattr(me, "use_mirror_" + axis, False)
                if obj.use_dynamic_topology_sculpting:
                    area, region = _view3d(window)
                    if area is not None:
                        with bpy.context.temp_override(window=window, area=area, region=region):
                            bpy.ops.sculpt.dynamic_topology_toggle()
                        wm[REPORT] = ("Dynamic topology is off for ground tiles: it adds and removes vertices, "
                                      "and Save needs one vertex per node.")
            elif PREV_LOCKS in scene:
                s.lock_x, s.lock_y = (bool(v) for v in scene[PREV_LOCKS])
                del scene[PREV_LOCKS]
    except Exception as exc:  # a timer that raises is dropped for the session
        print("Keep Your Ticket: ground guard: %s" % exc)
    return POLL_S


# --- operators and the box ---------------------------------------------------------

class KYT_OT_ground_load(bpy.types.Operator):
    """Load ground tiles from assets/source/world_ground/ into the 'Ground tiles' collection, one mesh per tile with a vertex per 2 m node and its colour image, to sculpt. A tile loaded already is reloaded from its file unless it has unsaved sculpting"""
    bl_idname = "kyt.ground_load"
    bl_label = "Load tiles"
    bl_options = {"REGISTER", "UNDO"}

    how: bpy.props.EnumProperty(items=[
        ("NAMES", "Named", "The tiles named in the box, as x0_z0, x1_z0"),
        ("CURSOR", "Under 3D cursor", "The tile under the 3D cursor"),
        ("SELECTION", "Under selection", "The tiles under the selected objects")], default="NAMES")

    @classmethod
    def description(cls, context, properties):
        return {"NAMES": "Load the tiles named in the box (x0_z0, x1_z0) to sculpt: one mesh each, a vertex per "
                         "2 m node, in its colour",
                "CURSOR": "Load the tile under the 3D cursor to sculpt",
                "SELECTION": "Load the tiles under the selected objects to sculpt"}[properties.how]

    def execute(self, context):
        if self.how == "CURSOR":
            tiles = tiles_under_cursor(context)
        elif self.how == "SELECTION":
            tiles = tiles_under_selection(context)
            if not tiles:
                _report(context, ["Select one or more objects over the area first."])
                self.report({"ERROR"}, "Nothing selected")
                return {"CANCELLED"}
        else:
            tiles = parse_tiles(context.scene.kyt_ground_tiles)
        ok, lines = load(context, tiles)
        _report(context, lines)
        self.report({"INFO"} if ok else {"ERROR"}, lines[0])
        return {"FINISHED"} if ok else {"CANCELLED"}


class KYT_OT_ground_save(bpy.types.Operator):
    """Write the loaded tiles' heights back to assets/source/world_ground/height/ as one recorded, undoable grid edit, under the name and why above. Only nodes moved by more than 1 mm are written; edge nodes go into the neighbouring tile too. Refuses sideways moves, added or removed vertices, and edges sculpted differently in two tiles"""
    bl_idname = "kyt.ground_save"
    bl_label = "Save tiles"

    def execute(self, context):
        scene = context.scene
        ok, lines = save(context, scene.kyt_ground_edit_name, scene.kyt_ground_edit_why)
        _report(context, lines)
        self.report({"INFO"} if ok else {"ERROR"}, lines[0] if ok else (lines[1] if len(lines) > 1 else lines[0]))
        return {"FINISHED"} if ok else {"CANCELLED"}


class KYT_OT_ground_undo(bpy.types.Operator):
    """Take back the newest ground edit, if an editor saved it (Save tiles, or Photoshop); loaded tiles without unsaved sculpting are reloaded. Send ground to game afterwards"""
    bl_idname = "kyt.ground_undo"
    bl_label = "Undo last ground edit"

    def invoke(self, context, event):
        root = project_root()
        e = last_edit(root) if root else None
        why = None
        if e is None:
            why = "There is no ground edit to undo."
        elif e.get("kind") != "values":
            why = ("The newest edit, %s %s, wasn't saved from an editor; undo it with "
                   "tools/ground_grid_edit.py --undo." % (e["id"], e["name"]))
        if why:
            _report(context, [why])
            self.report({"ERROR"}, why)
            return {"CANCELLED"}
        title = "Undo %s %s?" % (e["id"], e["name"])
        message = "%s nodes in %s: %s" % (format(e["nodes"], ","), ", ".join(e["tiles"]), e["why"])
        try:
            return context.window_manager.invoke_confirm(self, event, title=title, message=message,
                                                         confirm_text="Undo")
        except TypeError:
            return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        root = project_root()
        e = last_edit(root)
        if e is None or e.get("kind") != "values":
            return {"CANCELLED"}
        gge = tools(root)
        gd = ground_dir(root)
        sp = spec(root)
        out = io.StringIO()
        with object_mode(context):
            try:
                with contextlib.redirect_stdout(out):
                    gge.undo(gd, False)
            except SystemExit as exc:
                _report(context, ["Not undone: %s." % exc])
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}
            kept, notes = [], []
            for o in tile_objects(context.scene):
                if o[TILE_PROP] not in e["tiles"]:
                    continue
                st = tile_state(o, sp)
                if st["problems"] or st["changed"].any():
                    kept.append(o[TILE_PROP])
                else:
                    notes.append(refresh(o, gge.gb, gd, sp))
        lines = ["Undone: %s %s (%s nodes in %s)." % (e["id"], e["name"], format(e["nodes"], ","), ", ".join(e["tiles"]))]
        if kept:
            lines.append("%s kept as it is here: it has unsaved sculpting." % ", ".join(kept))
        lines += [n for n in notes if n]
        lines.append("Send ground to game to take it out of the game too.")
        _report(context, lines)
        self.report({"INFO"}, lines[0])
        return {"FINISHED"}


class KYT_OT_ground_send(bpy.types.Operator):
    """Send the ground to the game in the background (tools/ground_send.py): rebuild the changed tiles' meshes, let rocks, city blocks and roosts follow the ground, import in Godot, mount and check the tiles, read world_terrain_delta, and run the generator. About eight minutes; uses the files as saved"""
    bl_idname = "kyt.ground_send"
    bl_label = "Send ground to game"

    def execute(self, context):
        ok, lines = send(context)
        _report(context, lines)
        self.report({"INFO"} if ok else {"ERROR"}, lines[0])
        return {"FINISHED"} if ok else {"CANCELLED"}


def _wrap(text, width):
    out, line = [], ""
    for word in text.split():
        if line and len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = ("%s %s" % (line, word)).strip()
    return out + [line] if line else (out or [""])


class KYT_PT_ground(bpy.types.Panel):
    bl_label = "Ground"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Keep Your Ticket"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        width = max(24, int(context.region.width / (context.preferences.system.ui_scale * 7)) - 2)
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(scene, "kyt_ground_tiles", text="")
        row.operator("kyt.ground_load", text="Load", icon="IMPORT").how = "NAMES"
        row = col.row(align=True)
        row.operator("kyt.ground_load", text="Under cursor", icon="PIVOT_CURSOR").how = "CURSOR"
        row.operator("kyt.ground_load", text="Under selection", icon="RESTRICT_SELECT_OFF").how = "SELECTION"
        names = [o[TILE_PROP] for o in tile_objects(scene)]
        if names:
            for chunk in _wrap("Loaded: " + ", ".join(names), width):
                layout.label(text=chunk)
        box = layout.box()
        box.prop(scene, "kyt_ground_edit_name", text="Name")
        box.prop(scene, "kyt_ground_edit_why", text="Why")
        row = box.row()
        row.scale_y = 1.3
        row.operator("kyt.ground_save", icon="FILE_TICK")
        box.operator("kyt.ground_undo", icon="LOOP_BACK")
        job = _job
        row = layout.row()
        row.scale_y = 1.3
        row.enabled = job is None or not job.running
        row.operator("kyt.ground_send", icon="EXPORT")
        if job is not None:
            if not job.running:
                job.drawn_final = True
            jb = layout.box()
            jb.label(text=job.status(), icon="SORTTIME" if job.running else ("CHECKMARK" if job.code == 0 else "ERROR"))
            if job.running:
                for chunk in _wrap("Now: " + job.step(), width - 3):
                    jb.label(text=chunk)
            icons = {"ok": "CHECKMARK", "FAIL": "ERROR", "note": "INFO"}
            for line in job.lines():
                mark, _, rest = line.partition(" ")
                icon = icons.get(mark)
                text = rest if icon else line
                for i, chunk in enumerate(_wrap(text, width - 3)):
                    jb.label(text=chunk, icon=(icon if i == 0 else "BLANK1") if icon else "NONE")
        report = context.window_manager.get(REPORT)
        if report:
            rb = layout.box()
            for line in report.split("\n"):
                for chunk in _wrap(line, width):
                    rb.label(text=chunk)


CLASSES = (KYT_OT_ground_load, KYT_OT_ground_save, KYT_OT_ground_undo, KYT_OT_ground_send, KYT_PT_ground)


def register():
    bpy.types.Scene.kyt_ground_tiles = bpy.props.StringProperty(
        name="Tiles", default="x0_z0", description="Tiles to load, as x0_z0, x1_z0 (x and z in km from the plaza; "
                                                   "z runs south)")
    bpy.types.Scene.kyt_ground_edit_name = bpy.props.StringProperty(
        name="Name", description="A short name for the edit Save tiles records, as hill_by_the_lake")
    bpy.types.Scene.kyt_ground_edit_why = bpy.props.StringProperty(
        name="Why", description="One line: why the ground changes")
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    if not bpy.app.timers.is_registered(_guard):
        bpy.app.timers.register(_guard, first_interval=POLL_S, persistent=True)


def unregister():
    for fn in (_guard, _tick):
        if bpy.app.timers.is_registered(fn):
            bpy.app.timers.unregister(fn)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.kyt_ground_edit_why
    del bpy.types.Scene.kyt_ground_edit_name
    del bpy.types.Scene.kyt_ground_tiles
