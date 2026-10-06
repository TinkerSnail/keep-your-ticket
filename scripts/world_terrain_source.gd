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


## Reads the imported master and the baseline unless faces are handed in, as
## {mesh name: corners in world space, three per face}; a probe hands them in.
func _init(master := {}, baseline := {}) -> void:
	if master.is_empty():
		master = load_master()
	if baseline.is_empty():
		baseline = load_baseline()
	assert(not baseline.is_empty(), "the world terrain baseline is missing: %s" % BASELINE)
	_master_faces = _joined(master)
	_base_faces = _joined(baseline)
	if _master_faces == _base_faces:
		return
	_compare()


func changed() -> bool:
	return added + removed > 0


## Every face of the master's ground in world space, three corners each.
func master_faces() -> PackedVector3Array:
	return _master_faces


## How far the master's top ground at `p` (world x, z) stands above the copy's.
func delta_y(p: Vector2) -> float:
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


## One line for a log: what changed, where, and the largest rise and fall at
## the changed faces' corners.
func summary() -> String:
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


static func load_master() -> Dictionary:
	var scene := (load(MASTER_GLB) as PackedScene).instantiate()
	var out := {}
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if mi.mesh != null:
			out[String(mi.name)] = faces_of(mi.mesh, _world_xf(mi))
	scene.free()
	return out


static func load_baseline() -> Dictionary:
	var mesh := load(BASELINE) as ArrayMesh
	var out := {}
	if mesh == null:
		return out
	for s in mesh.get_surface_count():
		var faces := PackedVector3Array()
		_append_faces(mesh.surface_get_arrays(s), Transform3D.IDENTITY, faces)
		out[mesh.surface_get_name(s)] = faces
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
