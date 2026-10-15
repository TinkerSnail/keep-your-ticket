extends RefCounted

## How far the world's ground now stands above or below the frozen copy the generator was
## measured from, for `tools/gen_props.gd`'s five ground functions and its embankment index,
## `tools/world_terrain_delta.gd` and `tools/_ground_follow_probe.gd`.
##
## The ground is one height grid (`documentation/terrain-height-grid-plan-2026-10-12.md`, since
## its Stage 2, 2026-10-13): `assets/source/world_ground/height/` holds it, one float32 EXR a
## tile, and `baseline/` the copy, frozen at `1926e71` and never edited. The copy is the ground
## the generator built before the world terrain master took it over (2026-10-05) with the range's
## and city's landforms that joined the master on 2026-10-06, baked from exactly the faces the
## generator measured from then, so that unchanged ground is bit for bit the same in both. The
## generator adds `delta_y`, height − baseline, to its own ground functions, so what it places on
## the ground follows an edit to the grid; where nothing has changed it adds nothing, and the park
## is built exactly as it was before. A point where either image has no ground reads zero: nothing
## stands there to follow, or there was nothing it stood on before.
##
## The master's ground pieces that the grid was baked from were retired in Stage 5 (2026-10-15);
## they, the faces reading of them and the frozen copy as faces are in git up to `a8cd64b`.
## The master keeps its `Earthworks`, which `road_natural` reads.
##
## Everything that asks builds this class with `new()`; a probe may hand in the grid's two folders
## instead, as `load_grid` reads them.

## The grid: `grid.json` says where its tiles lie; `height/` and `baseline/` hold one float32
## EXR a tile, NaN where there is no ground.
const GRID_DIR := "res://assets/source/world_ground"
## Where the ground the generator still holds meets the grid's: each held body's open edges,
## chained (Stage 1). Their outlines in plan keep `delta_y` from reading across a seam.
const HOLES := GRID_DIR + "/holes.json"
## The ground the grid is built into (Stage 2): one GLB a tile, `x{tx}_z{tz}.glb`, holding the
## mesh `ground_x{tx}_z{tz}` in tile-local metres under a node at the tile's corner. `master_faces`
## serves these, the ground the game mounts.
const GROUND_TILES_DIR := "res://assets/world_ground/tiles"

## The world terrain master's export: since Stage 5 its `Lakes` and its `Earthworks` only.
const MASTER_GLB := "res://assets/world_terrain_master.glb"
## The generator's own ground bodies, in the order it builds them. It still builds them, because
## what follows in its build reads them (their seam ordinals, the corridor stitched to their edges,
## the routes banked against them), and then drops them: the grid is mounted in their place.
const BODIES: Array[String] = [
	"terrain_world_mainland_reserve",
	"terrain_world_coast_north",
	"terrain_world_coast_south",
	"terrain_T2_lowland",
	"terrain_T3_headland",
	"terrain_T6_outer_highland",
	"east_shoulder_n",
	"east_shoulder_s",
]
## Where an edit reshaped ground a road's corridor covers (the hillside, Ground edit 6, 2026-10-08:
## the hill ran down into the coast highway's cutting), the master hands over the edit's natural
## ground there, which is no ground one stands on (`kyt_collision=none`, hidden in
## `scenes/world/world_terrain.tscn`): a mesh named with this prefix in its `Earthworks`, each point
## on the designed ground and carrying, as its u texture coordinate, how far the design governs
## there, 1 inside the edit and 0 where it leaves the ground as it was. `road_natural` reads it.
## Stage 6 of the height-grid plan, her call, would read it from the grid instead.
const ROAD_NATURAL_PREFIX := "corridor_natural_"
## The plan cell the road's natural ground is indexed in.
const CELL := 8.0
## A face whose normal is flatter than this has no top to stand on (seam and closure walls). The
## grid's bake skipped such faces; `tools/_underlap_probe.gd` reads the same rule from here.
const MIN_UP := 0.05
const INSIDE_EPS := 1e-6

var _road_faces := PackedVector3Array()
var _road_weights := PackedFloat32Array()
var _road_cells := {}

## The grid's reading. Nodes run from (`_grid_x0`, `_grid_z0`) every `_grid_step` metres,
## `_grid_cols` cells across and `_grid_rows` down, in tiles of `_grid_cells` cells a side
## (`_grid_samples` nodes, the last row and column shared with the neighbour). Per tile, in
## row-major order from the north-west: the heights now and then, or two empty arrays where
## the two are the same bit for bit, which reads zero without being kept.
var _grid_x0 := 0.0
var _grid_z0 := 0.0
var _grid_step := 2.0
var _grid_cells := 500
var _grid_samples := 501
var _grid_tx0 := 0
var _grid_tz0 := 0
var _grid_ntx := 0
var _grid_ntz := 0
var _grid_cols := 0
var _grid_rows := 0
var _grid_now: Array[PackedFloat32Array] = []
var _grid_then: Array[PackedFloat32Array] = []
var _grid_changed := 0
## Per tile, 1 at a node inside a held body's outline in plan, or empty where no node is; and per
## body, its outline's edges (ax, az, bx, bz) with, per row band of the grid, the edges crossing it.
var _grid_hole: Array[PackedByteArray] = []
var _hole_edges: Array[PackedFloat64Array] = []
var _hole_bands: Array[Dictionary] = []
## Points whose four nodes all lie on the other side of an outline from them, read as if there were
## none (counted, for a probe).
var hole_fallbacks := 0
var _tile_faces := PackedVector3Array()
var _tile_faces_read := false
## Seconds the reading took to load, for a log.
var load_seconds := 0.0


## Reads the grid's tiles, now and then, and the master's `Earthworks` for `road_natural`, unless
## the tiles are handed in as {Vector2i(tx, tz): heights}, a `load_grid` each; then nothing is read
## from disk.
func _init(height := {}, baseline := {}) -> void:
	var t0 := Time.get_ticks_usec()
	_init_grid(height, baseline)
	load_seconds = (Time.get_ticks_usec() - t0) / 1e6


func changed() -> bool:
	return _grid_changed > 0


## Every face of the ground the game mounts, built from the grid (`GROUND_TILES_DIR`), in world
## space, three corners each.
func master_faces() -> PackedVector3Array:
	if not _tile_faces_read:
		_tile_faces = load_tile_faces()
		_tile_faces_read = true
	return _tile_faces


## How far the ground at `p` (world x, z) now stands above the copy's.
func delta_y(p: Vector2) -> float:
	return _grid_delta(p)


## The natural ground a road's corridor cuts its sides to at `p` (world x, z), given the
## landform's `y` there: `y`, blended towards the master's designed natural ground where an
## edit reshaped what the corridor covers (`ROAD_NATURAL_PREFIX`). A road's own level never
## reads it, so it keeps its graded profile; its sides follow the ground beside it.
func road_natural(p: Vector2, y: float) -> float:
	if _road_cells.is_empty():
		return y
	var key := Vector2i(floori(p.x / CELL), floori(p.y / CELL))
	if not _road_cells.has(key):
		return y
	for t in (_road_cells[key] as Array):
		var a := _road_faces[t]
		var b := _road_faces[t + 1]
		var c := _road_faces[t + 2]
		var e0 := Vector2(b.x - a.x, b.z - a.z)
		var e1 := Vector2(c.x - a.x, c.z - a.z)
		var e2 := Vector2(p.x - a.x, p.y - a.z)
		var den := e0.x * e1.y - e1.x * e0.y
		if absf(den) < 1e-9:
			continue
		var u := (e2.x * e1.y - e1.x * e2.y) / den
		var v := (e0.x * e2.y - e2.x * e0.y) / den
		if u < -INSIDE_EPS or v < -INSIDE_EPS or u + v > 1.0 + INSIDE_EPS:
			continue
		var z := a.y + u * (b.y - a.y) + v * (c.y - a.y)
		var w := _road_weights[t] + u * (_road_weights[t + 1] - _road_weights[t]) \
			+ v * (_road_weights[t + 2] - _road_weights[t])
		return lerpf(y, z, clampf(w, 0.0, 1.0))
	return y


## One line for a log: how many nodes changed since the copy, where, and the largest rise and
## fall among them.
func summary() -> String:
	return _grid_summary()


## The master's natural ground under road corridors, three corners a face with their weights,
## indexed in every plan cell a face touches.
func _read_road_natural(scene: Node) -> void:
	for node in scene.find_children(ROAD_NATURAL_PREFIX + "*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		var xf := _world_xf(mi)
		for s in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var order: PackedInt32Array = idx
			if order.is_empty():
				order.resize(v.size())
				for i in v.size():
					order[i] = i
			for i in order:
				_road_faces.append(xf * v[i])
				_road_weights.append(uv[i].x)
	for t in range(0, _road_faces.size(), 3):
		for key in _cells_of(_road_faces, t):
			if not _road_cells.has(key):
				_road_cells[key] = []
			(_road_cells[key] as Array).append(t)


static func faces_of(mesh: Mesh, xf: Transform3D) -> PackedVector3Array:
	var out := PackedVector3Array()
	for s in mesh.get_surface_count():
		_append_faces(mesh.surface_get_arrays(s), xf, out)
	return out


static func _append_faces(arr: Array, xf: Transform3D, out: PackedVector3Array) -> void:
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
	if idx.is_empty():
		for i in v.size():
			out.append(xf * v[i])
	else:
		for i in idx:
			out.append(xf * v[i])


static func _world_xf(n: Node) -> Transform3D:
	var t := Transform3D.IDENTITY
	var cur := n
	while cur != null and cur is Node3D:
		t = (cur as Node3D).transform * t
		cur = cur.get_parent()
	return t


func _cells_of(faces: PackedVector3Array, t: int) -> Array[Vector2i]:
	var a := faces[t]
	var b := faces[t + 1]
	var c := faces[t + 2]
	var x0 := floori(minf(a.x, minf(b.x, c.x)) / CELL)
	var x1 := floori(maxf(a.x, maxf(b.x, c.x)) / CELL)
	var z0 := floori(minf(a.z, minf(b.z, c.z)) / CELL)
	var z1 := floori(maxf(a.z, maxf(b.z, c.z)) / CELL)
	var out: Array[Vector2i] = []
	for x in range(x0, x1 + 1):
		for z in range(z0, z1 + 1):
			out.append(Vector2i(x, z))
	return out


## The grid's reading: `grid.json`, then the master's Earthworks for `road_natural` (which stays in
## the master until Stage 6 of the height-grid plan), then every tile, now and then. A tile whose
## two images are the same bit for bit is not kept: it reads zero.
func _init_grid(height: Dictionary, baseline: Dictionary) -> void:
	var spec := grid_spec()
	_grid_step = float(spec["spacing_m"])
	_grid_samples = int(spec["tile_samples"])
	_grid_cells = _grid_samples - 1
	var tile_m := float(spec["tile_m"])
	assert(is_equal_approx(_grid_cells * _grid_step, tile_m), "grid.json: tiles of %d cells of %.1fm are not %.0fm" % [
		_grid_cells, _grid_step, tile_m])
	_grid_tx0 = int(spec["tiles_x"][0])
	_grid_tz0 = int(spec["tiles_z"][0])
	_grid_ntx = int(spec["tiles_x"][1]) - _grid_tx0 + 1
	_grid_ntz = int(spec["tiles_z"][1]) - _grid_tz0 + 1
	_grid_x0 = _grid_tx0 * tile_m
	_grid_z0 = _grid_tz0 * tile_m
	_grid_cols = _grid_ntx * _grid_cells
	_grid_rows = _grid_ntz * _grid_cells
	var read := height.is_empty() and baseline.is_empty()
	if read:
		var scene := (load(MASTER_GLB) as PackedScene).instantiate()
		_read_road_natural(scene)
		scene.free()
	var n := _grid_samples * _grid_samples
	for j in _grid_ntz:
		for i in _grid_ntx:
			var key := Vector2i(_grid_tx0 + i, _grid_tz0 + j)
			var then: PackedFloat32Array = _read_tile("baseline", key) if read \
				else baseline.get(key, PackedFloat32Array())
			# A tile with no baseline (the sea tiles Stage 4 added, 2026-10-14) has no ground then,
			# so every change there reads zero, as `_grid_delta`'s NAN does: it is not read at all.
			if then.size() != n:
				_grid_now.append(PackedFloat32Array())
				_grid_then.append(PackedFloat32Array())
				continue
			var now: PackedFloat32Array = _read_tile("height", key) if read \
				else height.get(key, PackedFloat32Array())
			if now.size() != n:
				now = _no_ground(n)
			if then.size() != n:
				then = _no_ground(n)
			if now.to_byte_array() == then.to_byte_array():
				_grid_now.append(PackedFloat32Array())
				_grid_then.append(PackedFloat32Array())
				continue
			_grid_now.append(now)
			_grid_then.append(then)
			_grid_changed += 1
	_read_holes()


## `grid.json`, parsed.
static func grid_spec() -> Dictionary:
	var spec: Variant = JSON.parse_string(FileAccess.get_file_as_string(GRID_DIR.path_join("grid.json")))
	assert(spec is Dictionary, "%s/grid.json is missing or not JSON" % GRID_DIR)
	return spec


## One of the grid's folders (`height` or `baseline`) as {Vector2i(tx, tz): its heights}, node
## (c, r) of a tile at index r * samples + c, NaN for no ground. A probe hands two of these to
## `new()`, changed or not.
static func load_grid(folder: String) -> Dictionary:
	var spec := grid_spec()
	var out := {}
	for tz in range(int(spec["tiles_z"][0]), int(spec["tiles_z"][1]) + 1):
		for tx in range(int(spec["tiles_x"][0]), int(spec["tiles_x"][1]) + 1):
			out[Vector2i(tx, tz)] = _read_tile(folder, Vector2i(tx, tz))
	return out


## A tile's heights from its EXR: Godot reads the one channel as RGBF with g and b copying r;
## converting to RF keeps r bit for bit. The folder carries a `.gdignore`, so the file is read
## from disk as it is, never imported.
static func _read_tile(folder: String, key: Vector2i) -> PackedFloat32Array:
	var path := ProjectSettings.globalize_path(GRID_DIR.path_join(folder).path_join(
		"x%d_z%d.exr" % [key.x, key.y]))
	# No file is no ground (grid.json, since Stage 4): an empty array, which reads as NaN.
	if not FileAccess.file_exists(path):
		return PackedFloat32Array()
	var img := Image.load_from_file(path)
	if img == null or img.is_empty():
		push_error("the height grid has no tile %s" % path)
		return PackedFloat32Array()
	if img.get_format() != Image.FORMAT_RF:
		img.convert(Image.FORMAT_RF)
	return img.get_data().to_float32_array()


static func _no_ground(n: int) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(n)
	out.fill(NAN)
	return out


## How far the grid's ground now stands above the copy's at `p`: bilinear between the four
## nodes round it, each node's change its height now less its height then, or zero where either
## has no ground, as `_top`'s NAN reads zero on the faces. Where both hold ground at all four
## nodes this is bilinear(height) − bilinear(baseline), to float64 rounding; at a node it is that
## node's change exactly; where the four are unchanged it is exactly 0.0.
@warning_ignore("integer_division")
func _grid_delta(p: Vector2) -> float:
	if _grid_changed == 0:
		return 0.0
	var gx := (p.x - _grid_x0) / _grid_step
	var gz := (p.y - _grid_z0) / _grid_step
	if not (gx >= 0.0 and gz >= 0.0 and gx <= _grid_cols and gz <= _grid_rows):
		return 0.0
	# The domain's last row and column belong to the cell before them, at weight 1.
	var c := mini(floori(gx), _grid_cols - 1)
	var r := mini(floori(gz), _grid_rows - 1)
	var ti := c / _grid_cells
	var tj := r / _grid_cells
	var now := _grid_now[tj * _grid_ntx + ti]
	if now.is_empty():
		return 0.0
	var then := _grid_then[tj * _grid_ntx + ti]
	var i := (r - tj * _grid_cells) * _grid_samples + (c - ti * _grid_cells)
	var k := i + _grid_samples
	var d00 := now[i] - then[i]
	var d10 := now[i + 1] - then[i + 1]
	var d01 := now[k] - then[k]
	var d11 := now[k + 1] - then[k + 1]
	if is_nan(d00):
		d00 = 0.0
	if is_nan(d10):
		d10 = 0.0
	if is_nan(d01):
		d01 = 0.0
	if is_nan(d11):
		d11 = 0.0
	if d00 == 0.0 and d10 == 0.0 and d01 == 0.0 and d11 == 0.0:
		return 0.0
	var fx := gx - c
	var fz := gz - r
	var hole := _grid_hole[tj * _grid_ntx + ti]
	if not hole.is_empty() and (hole[i] | hole[i + 1] | hole[k] | hole[k + 1]) != 0:
		# A node in a held body's outline: only the nodes on the point's own side count.
		var side := 1 if _in_hole(p) else 0
		var w00 := (1.0 - fx) * (1.0 - fz) if hole[i] == side else 0.0
		var w10 := fx * (1.0 - fz) if hole[i + 1] == side else 0.0
		var w01 := (1.0 - fx) * fz if hole[k] == side else 0.0
		var w11 := fx * fz if hole[k + 1] == side else 0.0
		var sum := w00 + w10 + w01 + w11
		if sum > 0.0:
			return (w00 * d00 + w10 * d10 + w01 * d01 + w11 * d11) / sum
		var on_side := int(hole[i] == side) + int(hole[i + 1] == side) + int(hole[k] == side) \
			+ int(hole[k + 1] == side)
		if on_side > 0:
			# The point stands on a node of the other side with weight on no node of its own.
			return ((d00 if hole[i] == side else 0.0) + (d10 if hole[i + 1] == side else 0.0)
				+ (d01 if hole[k] == side else 0.0) + (d11 if hole[k + 1] == side else 0.0)) / on_side
		hole_fallbacks += 1
	return (d00 * (1.0 - fx) + d10 * fx) * (1.0 - fz) + (d01 * (1.0 - fx) + d11 * fx) * fz


## The grid's line for a log, in the faces' shape: how many nodes changed, where, and the largest
## rise and fall among them. A node on a shared tile edge is counted once.
@warning_ignore("integer_division")
func _grid_summary() -> String:
	var tiles := _grid_ntx * _grid_ntz
	if _grid_changed == 0:
		return "world terrain grid: unchanged since the copy (%d tiles of %d nodes)" % [
			tiles, _grid_samples * _grid_samples]
	var nodes := 0
	var came_or_went := 0
	var lo := Vector2(INF, INF)
	var hi := -lo
	var rise := 0.0
	var fall := 0.0
	var row_bytes := _grid_samples * 4
	for t in tiles:
		var now := _grid_now[t]
		if now.is_empty():
			continue
		var then := _grid_then[t]
		var now_bytes := now.to_byte_array()
		var then_bytes := then.to_byte_array()
		var ti := t % _grid_ntx
		var tj := t / _grid_ntx
		var x0 := _grid_x0 + ti * _grid_cells * _grid_step
		var z0 := _grid_z0 + tj * _grid_cells * _grid_step
		var last_c := _grid_cells if ti == _grid_ntx - 1 else _grid_cells - 1
		var last_r := _grid_cells if tj == _grid_ntz - 1 else _grid_cells - 1
		for r in last_r + 1:
			if now_bytes.slice(r * row_bytes, (r + 1) * row_bytes) \
					== then_bytes.slice(r * row_bytes, (r + 1) * row_bytes):
				continue
			for c in last_c + 1:
				var i := r * _grid_samples + c
				var d := now[i] - then[i]
				if is_nan(d):
					if is_nan(now[i]) == is_nan(then[i]):
						continue
					came_or_went += 1
				elif d == 0.0:
					continue
				else:
					rise = maxf(rise, d)
					fall = minf(fall, d)
				nodes += 1
				var at := Vector2(x0 + c * _grid_step, z0 + r * _grid_step)
				lo = lo.min(at)
				hi = hi.max(at)
	return "world terrain grid: %d nodes changed since the copy (%d where ground came or went), in %d of %d tiles of %.0fm nodes, between x %.0f..%.0f z %.0f..%.0f; the ground moves %+.2f..%+.2fm" % [
		nodes, came_or_went, _grid_changed, tiles, _grid_step, lo.x, hi.x, lo.y, hi.y, fall, rise]


## The ground built from the grid, every tile's faces in world space, three corners a face, tiles
## in name order. Read through the import when Godot has imported the tile, as the game mounts
## it, else from the GLB itself. Empty, loudly, until the build has finished
## (`GROUND_TILES_DIR/BUILD_DONE`).
static func load_tile_faces(dir := GROUND_TILES_DIR) -> PackedVector3Array:
	var out := PackedVector3Array()
	if not FileAccess.file_exists(dir.path_join("BUILD_DONE")):
		push_error("the ground's tiles are not built: no %s/BUILD_DONE" % dir)
		return out
	var files := Array(DirAccess.get_files_at(dir)).filter(
		func(f: String) -> bool: return f.ends_with(".glb"))
	files.sort()
	for file: String in files:
		var path := dir.path_join(file)
		var scene: Node = null
		if ResourceLoader.exists(path, "PackedScene"):
			scene = (load(path) as PackedScene).instantiate()
		else:
			var doc := GLTFDocument.new()
			var state := GLTFState.new()
			if doc.append_from_file(ProjectSettings.globalize_path(path), state) != OK:
				push_error("the ground's tile %s does not read" % path)
				continue
			scene = doc.generate_scene(state)
		var want := "ground_" + file.get_basename()
		var found := false
		for node in scene.find_children("*", "MeshInstance3D", true, false):
			var mi := node as MeshInstance3D
			var name := String(mi.name)
			if mi.mesh != null and (name == want or name.begins_with(want + "-")):
				out.append_array(faces_of(mi.mesh, _world_xf(mi)))
				found = true
		if not found:
			push_error("the ground's tile %s holds no %s" % [path, want])
		scene.free()
	return out


## The held bodies' outlines from `HOLES`, each body's open edges in plan, and from them a mask of
## the nodes inside any (even-odd, per body). The chains are each body's open edges exactly once;
## where a body's edges leave a plan corner odd (the tunnel lids end on the corridor at both portals,
## the corridor's two short slits), the odd corners are joined nearest first, so every outline
## closes. A node on an outline is outside it, as a point is.
@warning_ignore("integer_division")
func _read_holes() -> void:
	_grid_hole.clear()
	for t in _grid_ntx * _grid_ntz:
		_grid_hole.append(PackedByteArray())
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(HOLES))
	if not (data is Dictionary and (data as Dictionary).has("holes")):
		push_error("%s is missing or holds no holes; delta_y reads across the held ground's seams" % HOLES)
		return
	var marks := {}
	for body in data["holes"]:
		var edges := PackedFloat64Array()
		var degree := {}
		for chain in body["chains"]:
			var pts: Array = chain["points"]
			var n := pts.size()
			for e in (n if chain["closed"] else n - 1):
				var a: Array = pts[e]
				var b: Array = pts[(e + 1) % n]
				_hole_edge(edges, degree, float(a[0]), float(a[2]), float(b[0]), float(b[2]))
		var odd: Array[Vector2] = []
		for key in degree:
			if int(degree[key]) % 2 == 1:
				odd.append(key)
		while odd.size() > 1:
			var a := odd.pop_back() as Vector2
			var best := 0
			for j in odd.size():
				if a.distance_to(odd[j]) < a.distance_to(odd[best]):
					best = j
			var b := odd[best]
			odd.remove_at(best)
			_hole_edge(edges, degree, a.x, a.y, b.x, b.y)
		var bands := {}
		for e in range(0, edges.size(), 4):
			var z0 := minf(edges[e + 1], edges[e + 3])
			var z1 := maxf(edges[e + 1], edges[e + 3])
			for band in range(floori((z0 - _grid_z0) / _grid_step), floori((z1 - _grid_z0) / _grid_step) + 1):
				if not bands.has(band):
					bands[band] = []
				(bands[band] as Array).append(e)
		_hole_edges.append(edges)
		_hole_bands.append(bands)
		# The mask: along each node row, the stretches with an odd count of crossings to their right.
		for band in bands:
			var row: int = band
			if row < 0 or row > _grid_rows:
				continue
			var z := _grid_z0 + row * _grid_step
			var xs: Array[float] = []
			for e in (bands[band] as Array):
				var x := _hole_cross(edges, e, z)
				if not is_nan(x):
					xs.append(x)
			xs.sort()
			for m in range(0, xs.size() - 1):
				if (xs.size() - m - 1) % 2 == 0:
					continue
				for col in range(maxi(0, floori((xs[m] - _grid_x0) / _grid_step)),
						mini(_grid_cols, ceili((xs[m + 1] - _grid_x0) / _grid_step)) + 1):
					var x := _grid_x0 + col * _grid_step
					if x > xs[m] and x < xs[m + 1]:
						_hole_mark(marks, col, row)
	for t in marks:
		var mask := PackedByteArray()
		mask.resize(_grid_samples * _grid_samples)
		mask.fill(0)
		for idx in (marks[t] as Array):
			mask[idx] = 1
		_grid_hole[t] = mask


func _hole_edge(edges: PackedFloat64Array, degree: Dictionary, ax: float, az: float, bx: float, bz: float) -> void:
	edges.append_array([ax, az, bx, bz])
	for key in [Vector2(ax, az), Vector2(bx, bz)]:
		degree[key] = int(degree.get(key, 0)) + 1


## Where edge `e` crosses the line z, counting each end once (half-open in z), or NAN.
static func _hole_cross(edges: PackedFloat64Array, e: int, z: float) -> float:
	var az := edges[e + 1]
	var bz := edges[e + 3]
	if not ((az <= z and z < bz) or (bz <= z and z < az)):
		return NAN
	var ax := edges[e]
	return ax + (z - az) * (edges[e + 2] - ax) / (bz - az)


## Marks node (col, row) of the whole grid in every tile that holds it (edges are shared), into
## `marks`, {tile: [node index]}, which `_read_holes` turns into the masks once.
@warning_ignore("integer_division")
func _hole_mark(marks: Dictionary, col: int, row: int) -> void:
	for ti in [col / _grid_cells, col / _grid_cells - 1]:
		if ti < 0 or ti >= _grid_ntx or col - ti * _grid_cells > _grid_cells:
			continue
		for tj in [row / _grid_cells, row / _grid_cells - 1]:
			if tj < 0 or tj >= _grid_ntz or row - tj * _grid_cells > _grid_cells:
				continue
			var t: int = tj * _grid_ntx + ti
			if not marks.has(t):
				marks[t] = []
			(marks[t] as Array).append((row - tj * _grid_cells) * _grid_samples + (col - ti * _grid_cells))


## Whether `p` lies inside a held body's outline: an odd count of its edges crossing the line
## through it to its right, and none through it.
func _in_hole(p: Vector2) -> bool:
	var band := floori((p.y - _grid_z0) / _grid_step)
	for b in _hole_bands.size():
		var bands := _hole_bands[b]
		if not bands.has(band):
			continue
		var edges := _hole_edges[b]
		var right := 0
		var on := false
		for e in (bands[band] as Array):
			var x := _hole_cross(edges, e, p.y)
			if is_nan(x):
				continue
			if x == p.x:
				on = true
				break
			if x > p.x:
				right += 1
		if not on and right % 2 == 1:
			return true
	return false
