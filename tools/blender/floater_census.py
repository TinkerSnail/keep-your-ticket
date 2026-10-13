"""Floater census: how well each kind of thing sits on the world ground (terrain height-grid plan, Stage 0).

For each kind, how far each item's footing stands from the ground under it: positive floating, negative buried.
The ground is the top of the ground collection (default `Ground`) of the blend named by --ground, evaluated in
world space (modifiers applied), against one BVH; only its top surface counts: the first hit of a ray cast
straight down from above it, which is the highest Ground surface at that plan position. Objects marked
`kyt_collision=none` in the ground collection are left out, as `range_rocks_on_ground.py` and
`city_blocks_on_ground.py` leave them out.

Read-only: every source is linked for the read; nothing is saved. Run it in an empty Blender:

    Blender --background --factory-startup --python tools/blender/floater_census.py -- --ground <master.blend>
        [--ground-collection Ground] [--range <range.blend>] [--city <city.blend>]
        [--wildlife <wildlife.tscn>] [--godot <roost_census.json>] [--commit <hash>] --out <census.json>
        [--compare <older census.json>]

--compare prints each kind's floating and buried counts beside the older census's, and the rocks and blocks
whose footing got worse (newly floating > 0.05 m, or newly buried > 0.25 m), and exits 1 if any count rose.

--range and --city default to the files of those names beside --ground. Stage 2 re-runs it with --ground
pointing at a blend holding the grid's ground (under the collection --ground-collection names).

Kinds and footings (Blender is Z-up; positions are reported in Godot's (x, z) = Blender's (x, -y)):
  range_rocks     each rock's lowest vertex against the ground under that vertex (`foot`); also `clear`, the
                  least height of any of its vertices over the ground under it (> 0: nothing of it touches).
  city_blocks     each `city_block_*` and `city_skyline_anchor_*` as `city_blocks_on_ground.py` sees it: its
                  base (lowest vertex) against the lowest ground under its bottom face, swept at 2 m with the
                  edges included (`base - lo`); `climb` is how far that ground rises across it (hi - lo).
                  Overhang: a block whose bottom stands > 0.05 m over some of the ground under it.
  other           per object, the same footprint sweep over its own underside (bridge piers and towers,
                  ferry landings, terminal, flat road pieces), road centrelines sampled every 5 m,
                  earthworks' bottom vertices, the lakes' open edges and their water over the ground,
                  the range canopy's vertices, and (with --wildlife) the gull roosts' markers.
"""
import hashlib
import json
import math
import os
import re
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROCK_COLLECTIONS = ("range_main_beach_middle_band_rocks", "range_remaining_beach_rocks", "range_beach_rocks",
                    "range_base_boulders")
CANOPY = ("middle_continuous_canopy_mass", "transition_broken_canopy_surface")
BLOCKS = ("city_block_", "city_skyline_anchor_")
# The city's other things that stand on, in or over the master's ground, by how they meet it.
FOOTPRINT = ("bridge_approach_pier_", "bridge_tower_0_", "bridge_tower_1_", "beach_town_ferry_landing",
             "beach_town_ferry_shelter", "city_ferry_landing", "city_ferry_head", "city_ferry_terminal",
             "bridge_city_intersection", "bridge_city_southern_offramp", "city_highway_approach_ground")
CENTRELINES = ("southern_city_bypass_centreline", "southern_coastal_highway_extension_centreline")
EARTHWORKS = ("southern_city_bypass_earthwork", "southern_coastal_highway_earthwork", "city_highway_approach_ground")
LAKES = ("lake_K1", "lake_L0", "plunge_pool")
SAMPLE = 2.0        # footprint sweep spacing, as city_blocks_on_ground.py
LINE_STEP = 5.0     # centreline sampling
FLOAT_EPS = 0.05    # the scripts' MIN_RAISE / MIN_MOVE


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a else default
    ground = os.path.abspath(opt("--ground"))
    here = os.path.dirname(ground)
    return {
        "ground": ground,
        "ground_collection": opt("--ground-collection", "Ground"),
        "range": os.path.abspath(opt("--range", os.path.join(here, "range_forest_distinct_background.blend"))),
        "city": os.path.abspath(opt("--city", os.path.join(here, "far_shore_city_relocation.blend"))),
        "wildlife": opt("--wildlife"),
        "godot": opt("--godot"),
        "commit": opt("--commit", ""),
        "out": os.path.abspath(opt("--out", "census.json")),
        "compare": opt("--compare"),
    }


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def link(path, collections=(), objects=()):
    """Links the named collections and objects from `path` and puts them in the scene, so the depsgraph
    gives them world matrices and evaluated meshes. Missing names are reported, not fatal."""
    with bpy.data.libraries.load(path, link=True, relative=False) as (src, dst):
        missing = [n for n in collections if n not in src.collections] + [n for n in objects if n not in src.objects]
        dst.collections = [n for n in collections if n in src.collections]
        dst.objects = [n for n in objects if n in src.objects]
    scene = bpy.context.scene
    for c in dst.collections:
        if c is not None:
            scene.collection.children.link(c)
    for o in dst.objects:
        if o is not None:
            scene.collection.objects.link(o)
    if missing:
        print("floater_census: not in %s: %s" % (os.path.basename(path), ", ".join(missing)))
    return [c for c in dst.collections if c], [o for o in dst.objects if o]


def object_names(path, keep):
    with bpy.data.libraries.load(path, link=True, relative=False) as (src, dst):
        return [n for n in src.objects if keep(n)]


def world_mesh(ob, depsgraph):
    """World-space vertices (n, 3) and triangles (m, 3) of the evaluated object."""
    ev = ob.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        me.calc_loop_triangles()
        n = len(me.vertices)
        co = np.empty(n * 3, dtype=np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(n, 3)
        m = np.array(ev.matrix_world, dtype=np.float64)
        co = co @ m[:3, :3].T + m[:3, 3]
        tris = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", tris)
        tris = tris.reshape(-1, 3)
        edges = np.empty(len(me.edges) * 2, dtype=np.int64)
        me.edges.foreach_get("vertices", edges)
        edges = edges.reshape(-1, 2)
        # Open edges: edges used by exactly one face.
        use = {}
        for p in me.polygons:
            for k in p.edge_keys:
                use[k] = use.get(k, 0) + 1
        open_verts = sorted({v for k, c in use.items() if c == 1 for v in k})
    finally:
        ev.to_mesh_clear()
    return co, tris, open_verts


class Ground:
    def __init__(self, coll, depsgraph):
        vs, ts, base = [], [], 0
        self.objects, self.skipped, self.modified = [], [], []
        for ob in coll.all_objects:
            if ob.type != 'MESH':
                continue
            if ob.get("kyt_collision") == "none":
                self.skipped.append(ob.name)
                continue
            if ob.modifiers:
                self.modified.append(ob.name)
            co, tris, _ = world_mesh(ob, depsgraph)
            vs.append(co)
            ts.append(tris + base)
            base += len(co)
            self.objects.append(ob.name)
        v = np.concatenate(vs)
        t = np.concatenate(ts)
        self.triangles = int(len(t))
        self.top = float(v[:, 2].max()) + 1.0
        self.tree = BVHTree.FromPolygons([tuple(p) for p in v.tolist()], [tuple(p) for p in t.tolist()])

    def z(self, x, y):
        hit = self.tree.ray_cast(Vector((x, y, self.top)), Vector((0.0, 0.0, -1.0)))
        return None if hit[0] is None else hit[0].z

    def hit(self, x, y):
        """(z, faces_down) of the top Ground surface at (x, y), or (None, None). A top face wound downward is a
        back face from above: Godot culls it and its collision is one-sided."""
        hit = self.tree.ray_cast(Vector((x, y, self.top)), Vector((0.0, 0.0, -1.0)))
        return (None, None) if hit[0] is None else (hit[0].z, hit[1].z < 0.0)


def godot(x, y):
    return [round(float(x), 2), round(float(-y), 2)]


def stats(values):
    v = np.array([d for d in values if d is not None], dtype=np.float64)
    if len(v) == 0:
        return {"count": 0}
    return {
        "count": int(len(v)),
        "median": round(float(np.median(v)), 3),
        "p10": round(float(np.percentile(v, 10)), 3),
        "p90": round(float(np.percentile(v, 90)), 3),
        "min": round(float(v.min()), 3),
        "max": round(float(v.max()), 3),
        "floating_gt_0.05": int((v > 0.05).sum()),
        "floating_gt_0.25": int((v > 0.25).sum()),
        "floating_gt_1": int((v > 1.0).sum()),
        "buried_gt_0.25": int((v < -0.25).sum()),
        "buried_gt_1": int((v < -1.0).sum()),
    }


def worst(items, key, n=10):
    have = [i for i in items if i.get(key) is not None]
    out = {
        "worst": sorted(have, key=lambda i: -abs(i[key]))[:n],
        "worst_floating": [i for i in sorted(have, key=lambda i: -i[key]) if i[key] > FLOAT_EPS][:n],
        "worst_buried": [i for i in sorted(have, key=lambda i: i[key]) if i[key] < -0.25][:n],
    }
    return out


def kind(items, key, extra=None):
    k = {"footing": key, **stats([i.get(key) for i in items]),
         "no_ground": sum(1 for i in items if i.get(key) is None), **worst(items, key)}
    if extra:
        k.update(extra)
    k["items"] = items
    return k


# ---------------------------------------------------------------- range rocks


def census_rocks(ground, colls, depsgraph):
    items = []
    for coll in colls:
        for ob in coll.all_objects:
            if ob.type != 'MESH':
                continue
            co, _, _ = world_mesh(ob, depsgraph)
            low = co[int(np.argmin(co[:, 2]))]
            g_low, down = ground.hit(low[0], low[1])
            gaps = []
            for x, y, z in co:
                g = ground.z(x, y)
                if g is not None:
                    gaps.append(z - g)
            c = co.mean(axis=0)
            items.append({
                "name": ob.name, "collection": coll.name, "at": godot(c[0], c[1]),
                "foot": None if g_low is None else round(float(low[2] - g_low), 3),
                "clear": round(float(min(gaps)), 3) if gaps else None,
                # The highest vertex over the ground under it: < 0, the whole rock is under the ground.
                "top": round(float(max(gaps)), 3) if gaps else None,
                "low_y": round(float(low[2]), 3),
                "ground_faces_down": bool(down) if down is not None else None,
            })
    by = {c.name: stats([i["foot"] for i in items if i["collection"] == c.name]) for c in colls}
    for c in colls:
        by[c.name]["hidden"] = sum(1 for i in items if i["collection"] == c.name and i["top"] is not None and i["top"] < 0)
    return kind(items, "foot", {"by_collection": by,
                                "hidden": sum(1 for i in items if i["top"] is not None and i["top"] < 0),
                                "hidden_note": "rocks whose highest vertex is under the top Ground: wholly inside the ground",
                                "visible": stats([i["foot"] for i in items if i["top"] is not None and i["top"] >= 0]),
                                "ground_faces_down": sum(1 for i in items if i["ground_faces_down"]),
                                "clear": {**stats([i["clear"] for i in items]),
                                          **{k: v for k, v in worst(items, "clear").items() if k == "worst_floating"}}})


# ---------------------------------------------------------------- footprints


def sweep_bottom(ground, co):
    """city_blocks_on_ground.footprint_ground, on world vertices: base, lo, hi, samples, misses and the
    ground at each sample."""
    base = float(co[:, 2].min())
    order = np.argsort(co[:, 2], kind="stable")[:4]
    bottom = [Vector(co[i]) for i in order]
    centre = sum(bottom, Vector()) / 4.0
    bottom.sort(key=lambda c: math.atan2(c.y - centre.y, c.x - centre.x))
    a, b, c, d = bottom
    nu = max(1, int(math.ceil((b - a).length / SAMPLE)))
    nv = max(1, int(math.ceil((d - a).length / SAMPLE)))
    gs, miss = [], 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = i / nu, j / nv
            p = a.lerp(b, u).lerp(d.lerp(c, u), v)
            g = ground.z(p.x, p.y)
            if g is None:
                miss += 1
            else:
                gs.append(g)
    return base, gs, miss, (nu + 1) * (nv + 1)


def footprint_item(ob, ground, depsgraph):
    co, _, _ = world_mesh(ob, depsgraph)
    base, gs, miss, n = sweep_bottom(ground, co)
    c = co.mean(axis=0)
    item = {"name": ob.name, "at": godot(c[0], c[1]), "base_y": round(base, 3), "samples": n, "misses": miss}
    if gs:
        lo, hi = min(gs), max(gs)
        item.update({
            "foot": round(base - lo, 3), "lo_y": round(lo, 3), "hi_y": round(hi, 3), "climb": round(hi - lo, 3),
            # How much of its underside stands over the ground, and how far ground rises over its base.
            "floating_fraction": round(sum(1 for g in gs if base - g > FLOAT_EPS) / len(gs), 3),
            "over_base": round(hi - base, 3),
        })
    else:
        item["foot"] = None
    return item


def underside_item(ob, ground, depsgraph):
    """The object's underside against the top Ground, on a 2 m grid over its plan, 1 cm in from its bounds:
    a ray up from below finds the underside, a ray down from above the ground. foot is the most any of its
    underside stands over the ground (> 0 floating there), deepest the least (< 0 buried there)."""
    co, tris, _ = world_mesh(ob, depsgraph)
    tree = BVHTree.FromPolygons([tuple(p) for p in co.tolist()], [tuple(t) for t in tris.tolist()])
    (x0, y0), (x1, y1) = co[:, :2].min(axis=0) + 0.01, co[:, :2].max(axis=0) - 0.01
    nx = max(1, int(math.ceil((x1 - x0) / SAMPLE)))
    ny = max(1, int(math.ceil((y1 - y0) / SAMPLE)))
    below = float(co[:, 2].min()) - 1.0
    gaps, miss, down, worst_at = [], 0, 0, None
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny
            h = tree.ray_cast(Vector((x, y, below)), Vector((0.0, 0.0, 1.0)))
            if h[0] is None:
                continue
            g, d = ground.hit(x, y)
            if g is None:
                miss += 1
                continue
            down += bool(d)
            gap = h[0].z - g
            if worst_at is None or gap > worst_at[0]:
                worst_at = (gap, godot(x, y))
            gaps.append(gap)
    c = co.mean(axis=0)
    item = {"name": ob.name, "at": godot(c[0], c[1]), "base_y": round(float(co[:, 2].min()), 3),
            "samples": len(gaps) + miss, "no_ground": miss, "ground_faces_down": down}
    if gaps:
        g = np.array(gaps)
        item.update({"foot": round(float(g.max()), 3), "median": round(float(np.median(g)), 3),
                     "deepest": round(float(g.min()), 3),
                     "floating_fraction": round(float((g > FLOAT_EPS).mean()), 3),
                     "buried_fraction": round(float((g < -0.25).mean()), 3), "most_floating_at": worst_at[1]})
    else:
        item["foot"] = None
    return item


def census_blocks(ground, obs, depsgraph):
    items = [footprint_item(ob, ground, depsgraph) for ob in sorted(obs, key=lambda o: o.name)
             if ob.type == 'MESH' and ob.name.startswith(BLOCKS)]
    overhang = [{"name": i["name"], "at": i["at"], "foot": i["foot"], "floating_fraction": i["floating_fraction"],
                 "misses": i["misses"], "climb": i["climb"]}
                for i in items if i.get("foot") is not None and (i["foot"] > FLOAT_EPS or i["misses"])]
    steep = sorted(({"name": i["name"], "at": i["at"], "climb": i["climb"]} for i in items if i.get("climb")),
                   key=lambda i: -i["climb"])[:10]
    return kind(items, "foot", {"overhang": overhang, "steepest_ground_under": steep,
                                "climb": stats([i.get("climb") for i in items])})


# ---------------------------------------------------------------- other things


def centreline(ob, ground, depsgraph):
    co, _, _ = world_mesh(ob, depsgraph)
    # The centrelines are polylines in vertex order (open sheets of edges); sample every LINE_STEP.
    out = []
    for p, q in zip(co[:-1], co[1:]):
        p, q = Vector(p), Vector(q)
        n = max(1, int(math.ceil((q - p).length / LINE_STEP)))
        for k in range(n):
            s = p.lerp(q, k / n)
            g = ground.z(s.x, s.y)
            out.append({"at": godot(s.x, s.y), "y": round(s.z, 3), "over_ground": None if g is None else round(s.z - g, 3)})
    s = Vector(co[-1])
    g = ground.z(s.x, s.y)
    out.append({"at": godot(s.x, s.y), "y": round(s.z, 3), "over_ground": None if g is None else round(s.z - g, 3)})
    st = stats([o["over_ground"] for o in out])
    st["lowest"] = sorted((o for o in out if o["over_ground"] is not None), key=lambda o: o["over_ground"])[:5]
    st["note"] = "centreline height over the top Ground: positive is fill (an earthwork carries it), negative is ground over the road"
    return st


def bottom_vertices(ob, ground, depsgraph):
    co, _, _ = world_mesh(ob, depsgraph)
    zmin = co[:, 2].min()
    out = []
    for x, y, z in co[co[:, 2] < zmin + 0.01]:
        g = ground.z(x, y)
        out.append({"at": godot(x, y), "y": round(float(z), 3), "gap": None if g is None else round(float(z - g), 3)})
    st = stats([o["gap"] for o in out])
    st["no_ground"] = sum(1 for o in out if o["gap"] is None)
    st["points"] = out
    st["note"] = "the closed earthwork's bottom vertices against the top Ground: positive is its foot standing over the ground"
    return st


def lake(ob, ground, depsgraph):
    co, tris, open_verts = world_mesh(ob, depsgraph)
    edge, edge_at, near = [], [], []
    ring = [(0.0, 0.0)] + [(0.5 * math.cos(k * math.pi / 4), 0.5 * math.sin(k * math.pi / 4)) for k in range(8)]
    for i in open_verts:
        x, y, z = co[i]
        g = ground.z(x, y)
        edge.append(None if g is None else float(z - g))
        # The highest ground within 0.5 m: an edge on a vertical wall (the lakes are walled at the spill and
        # the creek) meets the wall, which a ray straight down the wall's face can miss.
        gs = [h for h in (ground.z(x + dx, y + dy) for dx, dy in ring) if h is not None]
        near.append(float(z - max(gs)) if gs else None)
        if g is not None:
            edge_at.append({"at": godot(x, y), "gap": round(float(z - g), 3),
                            "gap_within_0.5m": round(float(z - max(gs)), 3)})
    # The water over the ground at every vertex and face centre: depth > 0 is water over ground.
    pts = list(co) + list(co[tris].mean(axis=1))
    depth, dry = [], []
    for x, y, z in pts:
        g = ground.z(x, y)
        if g is not None:
            depth.append(float(z - g))
            if z - g < -FLOAT_EPS:
                dry.append(godot(x, y))
    e = stats(edge)
    e["worst_floating"] = sorted(edge_at, key=lambda o: -o["gap_within_0.5m"])[:10]
    e["within_0.5m"] = stats(near)
    e["note"] = "the water's open edge against the top Ground: positive is an edge standing over the bank (a gap), negative is an edge run into the bank"
    return {"level_y": [round(float(co[:, 2].min()), 3), round(float(co[:, 2].max()), 3)], "edge": e,
            "water_over_ground": stats(depth), "ground_through_water_points": len(dry), "ground_through_water_at": dry[:10]}


def canopy(ob, ground, depsgraph):
    co, _, _ = world_mesh(ob, depsgraph)
    gaps, below, down = [], [], 0
    for x, y, z in co:
        g, d = ground.hit(x, y)
        if g is not None:
            gaps.append(float(z - g))
            if z - g < 0:
                below.append((float(z - g), godot(x, y)))
                down += bool(d)
    st = stats(gaps)
    st["vertices"] = int(len(co))
    st["no_ground"] = int(len(co) - len(gaps))
    st["below_ground"] = len(below)
    st["below_ground_under_down_faces"] = down
    st["deepest_below"] = [{"at": a, "gap": round(d, 3)} for d, a in sorted(below)[:10]]
    st["note"] = "a merged mesh, not placed items: each vertex's height over the top Ground"
    return st


def roosts(path, ground):
    """The gull colony's roost markers in wildlife.tscn (parented under untransformed nodes in an untransformed
    mount), against the Blender ground: a cross-check of the Godot probe that Stage 2 can run before export."""
    text = open(path).read()
    out = []
    for name, x, y, z in re.findall(r'\[node name="([^"]+)" type="Marker3D" parent="gull_colony/roosts"\]\s*\n'
                                    r'position = Vector3\(([-\d.e]+), ([-\d.e]+), ([-\d.e]+)\)', text):
        x, y, z = float(x), float(y), float(z)
        g, down = ground.hit(x, -z)
        out.append({"name": name, "at": [x, z], "y": y, "foot": None if g is None else round(y - g, 3),
                    "ground_faces_down": down})
    return kind(out, "foot", {"note": "roost marker against the top Ground in Blender (the Godot probe measures the game's collision)"})


BUCKETS = ("floating_gt_0.05", "floating_gt_0.25", "floating_gt_1", "buried_gt_0.25", "buried_gt_1")


def headline(census):
    """Every block of counts in a census, by a flat name."""
    def counted(w):
        return isinstance(w, dict) and "count" in w and all(b in w for b in BUCKETS)
    out = {}
    for name, k in census["kinds"].items():
        if counted(k):
            out[name] = k
        if name != "other":
            continue
        for sub, v in k.items():
            if counted(v):
                out[sub] = v
            if "edge" in v:
                out[sub + "/edge"] = v["edge"]
                out[sub + "/edge_within_0.5m"] = v["edge"]["within_0.5m"]
                out[sub + "/water_over_ground"] = v["water_over_ground"]
    return {n: w for n, w in out.items() if counted(w)}


def compare(old_path, new):
    old = json.load(open(old_path))
    a, b = headline(old), headline(new)
    rose = False
    print("floater_census: against %s (commit %s)" % (old_path, old.get("commit", "?")))
    for name in sorted(set(a) & set(b)):
        row = []
        for k in BUCKETS:
            row.append("%s %d->%d" % (k.replace("floating_gt_", "f>").replace("buried_gt_", "b>"), a[name][k], b[name][k]))
            rose |= b[name][k] > a[name][k]
        print("  %-48s n %d->%d  %s" % (name, a[name]["count"], b[name]["count"], "  ".join(row)))
    for kind in ("range_rocks", "city_blocks"):
        was = {i["name"]: i.get("foot") for i in old["kinds"][kind]["items"]}
        worse = []
        for i in new["kinds"][kind]["items"]:
            f0, f1 = was.get(i["name"]), i.get("foot")
            if f0 is None or f1 is None:
                continue
            if (f1 > FLOAT_EPS >= f0) or (f1 < -0.25 <= f0):
                worse.append((i["name"], i["at"], f0, f1))
        print("  %s: %d worse" % (kind, len(worse)))
        for w in sorted(worse, key=lambda w: -abs(w[3] - w[2]))[:10]:
            print("    %-44s at %s  %+.3f -> %+.3f" % w)
    return rose


def main():
    a = args()
    print("floater_census: ground %s" % a["ground"])
    sources = {k: {"path": a[k], "sha256": sha256(a[k])} for k in ("ground", "range", "city")}
    gcoll, _ = link(a["ground"], collections=[a["ground_collection"], "Lakes"])
    gcoll = {c.name: c for c in gcoll}
    rcoll, robs = link(a["range"], collections=ROCK_COLLECTIONS, objects=CANOPY)
    city_names = object_names(a["city"], lambda n: True)
    _, cobs = link(a["city"], objects=city_names)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    ground = Ground(gcoll[a["ground_collection"]], dg)
    print("floater_census: ground %d objects, %d triangles, %d skipped (kyt_collision=none), %d with modifiers" % (
        len(ground.objects), ground.triangles, len(ground.skipped), len(ground.modified)))

    out = {
        "what": "floater census: each item's footing against the top of the ground under it; + floating, - buried (m)",
        "commit": a["commit"], "sources": sources,
        "ground": {"collection": a["ground_collection"], "objects": len(ground.objects), "triangles": ground.triangles,
                   "skipped_kyt_collision_none": ground.skipped, "with_modifiers": ground.modified,
                   "top_from": "first hit of a ray straight down from above the ground (two-sided BVH): the highest Ground surface"},
        "axes": "positions are Godot (x, z) = Blender (x, -y); heights are Godot y = Blender z",
        "kinds": {},
    }
    K = out["kinds"]
    K["range_rocks"] = census_rocks(ground, rcoll, dg)
    print("floater_census: range rocks done")
    K["city_blocks"] = census_blocks(ground, cobs, dg)
    other = {}
    other["city_things"] = kind([underside_item(o, ground, dg) for o in sorted(cobs, key=lambda o: o.name)
                                 if o.type == 'MESH' and o.name.startswith(FOOTPRINT)], "foot",
                                {"note": "each object's underside against the top Ground on a 2 m grid over its plan: foot the most it stands over the ground anywhere, deepest the least; no_ground counts samples with no Ground under them (sea, or ground the generator holds)"})
    for o in cobs:
        if o.name in CENTRELINES:
            other["centreline:" + o.name] = centreline(o, ground, dg)
        if o.name in EARTHWORKS:
            other["earthwork_bottom:" + o.name] = bottom_vertices(o, ground, dg)
    if "Lakes" in gcoll:
        for o in gcoll["Lakes"].all_objects:
            if o.type == 'MESH':
                other["lake:" + o.name] = lake(o, ground, dg)
    for o in robs:
        other["canopy:" + o.name] = canopy(o, ground, dg)
    K["other"] = other
    out["not_censused"] = {
        "range canopy as items": "two merged meshes (middle_continuous_canopy_mass, transition_broken_canopy_surface), not placed objects; only their vertices are measured, under other",
        "bay_ferry_hull, bay_ferry_cabin": "on the sea, not the ground",
        "southern_coastal_highway_guardrail_*": "on the road, which keeps its graded profile",
        "city_skyline_glass_*": "moves with its tower (city_blocks_on_ground.py)",
        "bridge deck, cables, hangers, beams, city_highway_extension": "carried by the towers and piers",
        "master Water_surfaces": "not exported (kyt_export_collections is Ground, Lakes, Earthworks)",
        "the falls' water": "a reference curve (falls_ribbon), not in the game",
        "Earthworks/corridor_natural_edit6": "ground data the generator reads, not a thing on the ground",
        "generator output": "follows the master through world_terrain_source.gd's delta; Stage 2 proves it with _ground_follow_probe",
    }
    if a["wildlife"]:
        K["roosts_blender"] = roosts(a["wildlife"], ground)
    if a["godot"] and os.path.exists(a["godot"]):
        K["roosts_godot"] = json.load(open(a["godot"]))
    os.makedirs(os.path.dirname(a["out"]), exist_ok=True)
    with open(a["out"], "w") as f:
        json.dump(out, f, indent=1)
    for name, k in K.items():
        if "count" in k:
            print("  %-16s n=%5d med %+7.3f p10 %+7.3f p90 %+7.3f  >0.05 %4d >0.25 %4d >1 %4d  bur>0.25 %4d bur>1 %4d  noground %d" % (
                name, k["count"], k["median"], k["p10"], k["p90"], k["floating_gt_0.05"], k["floating_gt_0.25"],
                k["floating_gt_1"], k["buried_gt_0.25"], k["buried_gt_1"], k.get("no_ground", 0)))
    print("floater_census: wrote %s" % a["out"])
    if a["compare"] and compare(a["compare"], out):
        print("floater_census: a count rose")
        sys.exit(1)


main()
