extends RefCounted

## Generator-facing derivation of the editor-owned world terrain master,
## `assets/source/world_terrain_master.blend`, whose `Ground` collection reaches
## the game as `assets/world_terrain_master.glb` (Stage 2 of
## `documentation/terrain-master-into-game-plan-2026-10-05.md`, 2026-10-05).
##
## The master's ground began as the generator's own, copied vertex for vertex on
## 2026-10-05, and `assets/source/world_terrain_baseline.res` keeps that copy,
## frozen. Whatever has changed in the master since is the difference between
## the two, and `delta_y` reads it: how far the master's top ground at a point
## now stands above or below the copy's. The generator adds it to its own ground
## functions, so what it places on the ground follows an edit to the master;
## where nothing has changed it adds nothing, and the park is built exactly as
## it was before the master existed.
##
## The comparison is of the ground as a whole, not body by body, so joining,
## splitting or renaming the master's objects changes nothing. A point where the
## master no longer has ground (a hole cut through it) or where the copy had
## none (ground added beyond it) reads zero: nothing stands there to follow, or
## there is nothing it was standing on before.
##
## Since Stage 2 of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-13) there
## are two readings of the same change, and `GROUND_FROM_GRID` picks one. The faces: the master
## GLB's against the frozen copy's, as above. The grid: the height grid's images,
## `assets/source/world_ground/height/` against `baseline/`, which Stage 1 baked from exactly
## those faces as `_top` reads them, so that at every node height − baseline is the faces'
## `delta_y` (within float32, 3e-5 m) and unchanged ground is bit for bit the same.

## The switch: false reads the faces (the game as it has been), true reads the grid. It lives
## here, beside the reading, because everything that asks what the ground has done (the
## generator's five ground functions and its embankment index, `tools/world_terrain_delta.gd`,
## `tools/_ground_follow_probe.gd`) builds this class with `new()` and nothing else, so this one
## line flips them all and flipping it back is the whole rollback until Stage 5. The
## generator's formulas never see it. A probe that wants a reading regardless passes
## `READ_FACES` or `READ_GRID` to `new()`.
const GROUND_FROM_GRID := true
const READ_SWITCH := 0
const READ_FACES := 1
const READ_GRID := 2
## The grid: `grid.json` says where its tiles lie; `height/` and `baseline/` hold one float32
## EXR a tile, NaN where there is no ground.
const GRID_DIR := "res://assets/source/world_ground"
## Where the ground the generator still holds meets the master's: each held body's open edges,
## chained (Stage 1). Their outlines in plan keep `delta_y` from reading across a seam.
const HOLES := GRID_DIR + "/holes.json"
## The ground the grid is built into (Stage 2): one GLB a tile, `x{tx}_z{tz}.glb`, holding the
## mesh `ground_x{tx}_z{tz}` in tile-local metres under a node at the tile's corner. On the
## grid's reading `master_faces` serves these, the ground the game then mounts.
const GROUND_TILES_DIR := "res://assets/world_ground/tiles"

const MASTER_GLB := "res://assets/world_terrain_master.glb"
const BASELINE := "res://assets/source/world_terrain_baseline.res"
## The generator's copied bodies, in the order it builds them. It no longer
## writes them; the master is mounted in their place.
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
## The range's and city's landforms, which joined the master on 2026-10-06 exactly as their
## own sources drew them (`tools/blender/world_terrain_join_landforms.py`, its `LANDFORMS`).
## They were the game's ground before the master took them, so the baseline holds them as
## they joined, and only an edit to them since reads as change.
const JOINED: Array[String] = [
	"background_distant_range_middle",
	"background_distant_range_north",
	"background_distant_range_north_inland_saddle",
	"background_distant_range_north_west_companion",
	"background_distant_range_south",
	"background_distant_range_southeast_connector",
	"north_plug_s_curve_sand_infill",
	"north_shore_volcanic_plug",
	"southeast_range_ridge_1",
	"southeast_range_ridge_2",
	"southeast_range_ridge_3",
	"southeast_range_ridge_4",
	"southern_range_connection_lowland",
	"southern_range_connection_ridge_0",
	"southern_range_connection_ridge_1",
	"southern_range_connection_ridge_2",
	"southern_range_connection_ridge_3",
	"southern_range_connection_ridge_4",
	"relocated_city_peninsula",
	"relocated_city_peninsula_beaches",
	"southern_city_range_foothills",
	"southern_city_range_beaches",
]
## Where an edit to the master reshapes ground a road's corridor covers (the hillside, Ground
## edit 6, 2026-10-08: the hill ran down into the coast highway's cutting), the master hands
## over the edit's natural ground there, which is no ground one stands on (`kyt_collision=none`,
## hidden in `scenes/world/world_terrain.tscn`): a mesh named with this prefix, each point on the
## designed ground and carrying, as its u texture coordinate, how far the design governs there,
## 1 inside the edit and 0 where it leaves the ground as it was. `road_natural` reads it; see
## `tools/blender/world_terrain_ground_edit.py`, `ROAD_NATURAL`.
const ROAD_NATURAL_PREFIX := "corridor_natural_"
## The plan cell the changed faces are indexed in.
const CELL := 8.0
## A face whose normal is flatter than this has no top to stand on (the seam
## and closure walls), so it carries no height.
const MIN_UP := 0.05
const INSIDE_EPS := 1e-6

## Faces the master has that the copy does not, and the reverse.
var added := 0
var removed := 0
var _master_faces := PackedVector3Array()
var _dirty := {}
var _master_cells := {}
var _base_cells := {}
var _base_faces := PackedVector3Array()
var _road_faces := PackedVector3Array()
var _road_weights := PackedFloat32Array()
var _road_cells := {}

## Which reading this is; see `GROUND_FROM_GRID`.
var from_grid := false
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


## Reads the imported master and the baseline unless faces are handed in, as
## {mesh name: corners in world space, three per face}; a probe hands them in.
## On the grid's reading (`reading` `READ_GRID`, or the switch with nothing handed in) it reads
## the grid's tiles instead, unless they are handed in as {Vector2i(tx, tz): heights}, a
## `load_grid` each; then nothing is read from disk.
func _init(master := {}, baseline := {}, reading := READ_SWITCH) -> void:
	var t0 := Time.get_ticks_usec()
	from_grid = reading == READ_GRID or (reading == READ_SWITCH and GROUND_FROM_GRID
		and master.is_empty() and baseline.is_empty())
	if from_grid:
		_init_grid(master, baseline)
		load_seconds = (Time.get_ticks_usec() - t0) / 1e6
		return
	_init_faces(master, baseline)
	load_seconds = (Time.get_ticks_usec() - t0) / 1e6


func _init_faces(master: Dictionary, baseline: Dictionary) -> void:
	if master.is_empty():
		var scene := (load(MASTER_GLB) as PackedScene).instantiate()
		master = _ground_of(scene)
		_read_road_natural(scene)
		scene.free()
	if baseline.is_empty():
		baseline = load_baseline()
	assert(not baseline.is_empty(), "the world terrain baseline is missing: %s" % BASELINE)
	_master_faces = _joined(master)
	_base_faces = _joined(baseline)
	if _master_faces == _base_faces:
		return
	_compare()


func changed() -> bool:
	if from_grid:
		return _grid_changed > 0
	return added + removed > 0


## Every face of the master's ground in world space, three corners each. On the grid's reading,
## the faces of the ground built from it (`GROUND_TILES_DIR`), which is what the game mounts
## then: the master's own faces are the ones the grid replaces.
func master_faces() -> PackedVector3Array:
	if from_grid:
		if not _tile_faces_read:
			_tile_faces = load_tile_faces()
			_tile_faces_read = true
		return _tile_faces
	return _master_faces


## How far the master's top ground at `p` (world x, z) stands above the copy's.
func delta_y(p: Vector2) -> float:
	if from_grid:
		return _grid_delta(p)
	if added + removed == 0:
		return 0.0
	var key := Vector2i(floori(p.x / CELL), floori(p.y / CELL))
	if not _dirty.has(key):
		return 0.0
	var now := _top(_master_cells, _master_faces, key, p)
	var then := _top(_base_cells, _base_faces, key, p)
	if is_nan(now) or is_nan(then):
		return 0.0
	return now - then


## The natural ground a road's corridor cuts its sides to at `p` (world x, z), given the
## landform's `y` there: `y`, blended towards the master's designed natural ground where an
## edit reshapes what the corridor covers (`ROAD_NATURAL_PREFIX`). A road's own level never
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


## One line for a log: what changed, where, and the largest rise and fall at
## the changed faces' corners.
func summary() -> String:
	if from_grid:
		return _grid_summary()
	if not changed():
		return "world terrain master: unchanged since the copy (%d faces)" % (_master_faces.size() / 3)
	var lo := Vector2(INF, INF)
	var hi := -lo
	for key in _dirty:
		lo = lo.min(Vector2(key) * CELL)
		hi = hi.max((Vector2(key) + Vector2.ONE) * CELL)
	var rise := 0.0
	var fall := 0.0
	for list in _master_cells.values():
		for t in list:
			for k in 3:
				var corner: Vector3 = _master_faces[t + k]
				var d := delta_y(Vector2(corner.x, corner.z))
				rise = maxf(rise, d)
				fall = minf(fall, d)
	return "world terrain master: %d faces added and %d removed since the copy, in %d cells of %.0fm between x %.0f..%.0f z %.0f..%.0f; the ground moves %+.2f..%+.2fm" % [
		added, removed, _dirty.size(), CELL, lo.x, hi.x, lo.y, hi.y, fall, rise]


## The master's ground: every mesh in it that carries collision, which is every mesh one
## can stand on. The lakes' water (2026-10-05) is exported `kyt_collision=none` and so is
## not ground.
static func load_master() -> Dictionary:
	var scene := (load(MASTER_GLB) as PackedScene).instantiate()
	var out := _ground_of(scene)
	scene.free()
	return out


static func _ground_of(scene: Node) -> Dictionary:
	var out := {}
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if mi.mesh != null and not mi.find_children("*", "CollisionShape3D", true, false).is_empty():
			out[String(mi.name)] = faces_of(mi.mesh, _world_xf(mi))
	return out


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


static func load_baseline() -> Dictionary:
	var mesh := load(BASELINE) as ArrayMesh
	var out := {}
	if mesh == null:
		return out
	# A body with several materials is several surfaces under one name (the joined landforms).
	for s in mesh.get_surface_count():
		var name := mesh.surface_get_name(s)
		var faces: PackedVector3Array = out.get(name, PackedVector3Array())
		_append_faces(mesh.surface_get_arrays(s), Transform3D.IDENTITY, faces)
		out[name] = faces
	return out


## The master as it is now, frozen as the baseline: one surface per mesh, named
## after it, holding its world-space vertices and indices. Written once, on
## 2026-10-05, while the master was still the generator's ground exactly
## (`tools/ground_copy_compare.gd` PASS); refuses to overwrite.
static func write_baseline() -> Error:
	if FileAccess.file_exists(BASELINE):
		push_error("%s exists; the baseline is written once" % BASELINE)
		return ERR_ALREADY_EXISTS
	var scene := (load(MASTER_GLB) as PackedScene).instantiate()
	var out := ArrayMesh.new()
	var meshes := scene.find_children("*", "MeshInstance3D", true, false)
	meshes.sort_custom(func(a, b): return String(a.name) < String(b.name))
	for node in meshes:
		var mi := node as MeshInstance3D
		var xf := _world_xf(mi)
		for s in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(s)
			var world := PackedVector3Array()
			for v in (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array):
				world.append(xf * v)
			var kept := []
			kept.resize(Mesh.ARRAY_MAX)
			kept[Mesh.ARRAY_VERTEX] = world
			kept[Mesh.ARRAY_INDEX] = arr[Mesh.ARRAY_INDEX]
			out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, kept)
			out.surface_set_name(out.get_surface_count() - 1, String(mi.name))
	scene.free()
	return ResourceSaver.save(out, BASELINE, ResourceSaver.FLAG_COMPRESS)


## The joined landforms added to the baseline as the master holds them now: once, on
## 2026-10-06, straight after the join, while they were still exactly their sources' meshes.
## Only those that are ground (carry collision) go in, as `load_master` reads them. Refuses if
## any is already there.
static func extend_baseline() -> Error:
	var mesh := load(BASELINE) as ArrayMesh
	if mesh == null:
		push_error("%s is missing" % BASELINE)
		return ERR_FILE_NOT_FOUND
	for s in mesh.get_surface_count():
		if mesh.surface_get_name(s) in JOINED:
			push_error("%s already holds %s" % [BASELINE, mesh.surface_get_name(s)])
			return ERR_ALREADY_EXISTS
	var out := ArrayMesh.new()
	for s in mesh.get_surface_count():
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, mesh.surface_get_arrays(s))
		out.surface_set_name(s, mesh.surface_get_name(s))
	var scene := (load(MASTER_GLB) as PackedScene).instantiate()
	var added := 0
	for name in JOINED:
		var mi := scene.find_child(name, true, false) as MeshInstance3D
		if mi == null:
			push_error("the master has no %s" % name)
			scene.free()
			return ERR_DOES_NOT_EXIST
		if mi.find_children("*", "CollisionShape3D", true, false).is_empty():
			continue
		var xf := _world_xf(mi)
		for si in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(si)
			var world := PackedVector3Array()
			for v in (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array):
				world.append(xf * v)
			var kept := []
			kept.resize(Mesh.ARRAY_MAX)
			kept[Mesh.ARRAY_VERTEX] = world
			kept[Mesh.ARRAY_INDEX] = arr[Mesh.ARRAY_INDEX]
			out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, kept)
			out.surface_set_name(out.get_surface_count() - 1, name)
		added += 1
	scene.free()
	print("baseline: %d joined landforms added" % added)
	return ResourceSaver.save(out, BASELINE, ResourceSaver.FLAG_COMPRESS)


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


## The meshes' faces end to end, the copy's bodies first in build order and
## anything else after by name, so the same ground reads the same both ways.
static func _joined(faces: Dictionary) -> PackedVector3Array:
	var out := PackedVector3Array()
	var names: Array = faces.keys()
	names.sort()
	for body in BODIES:
		if faces.has(body):
			out.append_array(faces[body])
	for body in names:
		if not String(body) in BODIES:
			out.append_array(faces[body])
	return out


## A face as text: its three corners' float32 bytes, started at the smallest
## corner so the winding is kept and the starting corner does not matter.
static func _key(a: Vector3, b: Vector3, c: Vector3) -> String:
	var ka := PackedFloat32Array([a.x, a.y, a.z]).to_byte_array().hex_encode()
	var kb := PackedFloat32Array([b.x, b.y, b.z]).to_byte_array().hex_encode()
	var kc := PackedFloat32Array([c.x, c.y, c.z]).to_byte_array().hex_encode()
	if ka <= kb and ka <= kc:
		return ka + kb + kc
	if kb <= ka and kb <= kc:
		return kb + kc + ka
	return kc + ka + kb


## Which faces differ, as multisets; the plan cells they touch; and, in those
## cells only, every face of either ground that could stand over a point.
func _compare() -> void:
	var count := {}
	for t in range(0, _base_faces.size(), 3):
		var k := _key(_base_faces[t], _base_faces[t + 1], _base_faces[t + 2])
		count[k] = int(count.get(k, 0)) + 1
	var fresh: Array[int] = []
	for t in range(0, _master_faces.size(), 3):
		var k := _key(_master_faces[t], _master_faces[t + 1], _master_faces[t + 2])
		var n := int(count.get(k, 0))
		if n > 0:
			count[k] = n - 1
		else:
			fresh.append(t)
	added = fresh.size()
	for t in fresh:
		_mark(_master_faces, t)
	# What is left over in the count is the copy's faces the master lost.
	var lost := {}
	for k in count:
		if int(count[k]) > 0:
			lost[k] = int(count[k])
	for t in range(0, _base_faces.size(), 3):
		if lost.is_empty():
			break
		var k := _key(_base_faces[t], _base_faces[t + 1], _base_faces[t + 2])
		if lost.has(k):
			removed += 1
			_mark(_base_faces, t)
			lost[k] = int(lost[k]) - 1
			if int(lost[k]) == 0:
				lost.erase(k)
	_index(_master_faces, _master_cells)
	_index(_base_faces, _base_cells)


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


func _mark(faces: PackedVector3Array, t: int) -> void:
	for key in _cells_of(faces, t):
		_dirty[key] = true


func _index(faces: PackedVector3Array, cells: Dictionary) -> void:
	for t in range(0, faces.size(), 3):
		var a := faces[t]
		var n := (faces[t + 1] - a).cross(faces[t + 2] - a)
		if absf(n.y) < n.length() * MIN_UP:
			continue
		for key in _cells_of(faces, t):
			if not _dirty.has(key):
				continue
			if not cells.has(key):
				cells[key] = []
			(cells[key] as Array).append(t)


## The highest face over `p` among those indexed in its cell, or NAN.
static func _top(cells: Dictionary, faces: PackedVector3Array, key: Vector2i, p: Vector2) -> float:
	if not cells.has(key):
		return NAN
	var best := -INF
	for t in (cells[key] as Array):
		var a := faces[t]
		var b := faces[t + 1]
		var c := faces[t + 2]
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
		best = maxf(best, a.y + u * (b.y - a.y) + v * (c.y - a.y))
	return best if best > -INF else NAN


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
## `new()` with `READ_GRID`, changed or not.
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
