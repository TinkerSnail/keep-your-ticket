extends Node

## The boxwood hedge kit (2026-09-29). In the model: every piece of every
## height has a body that collides, a lid and three scatterings of leaf
## clusters, and every open end of a piece's body and lid has exactly the
## straight's cross-section, so pieces laid on the 1 m grid meet without a step
## or a gap. In the wrapper (scenes/world/landscape_kit/boxwood_hedge.tscn):
## for every height, piece and choice of scattering it builds that piece as
## one mesh and one collision shape and nothing else, standing on the ground,
## its lid at its height and the leaf clusters lying on the lid no more than
## `TOP_LIFT` over it. Measured on the imported meshes, not the builder's
## numbers.

const SOURCE := "res://scenes/world/landscape_kit/boxwood_hedge.tscn"
const MODEL := "res://assets/props/boxwood_hedge.glb"
const PREFIX := "boxwood_hedge_"
## Each height's lid top (hedge_kit.py, HEIGHTS: a step under 0.5, 1 and 2.2 m
## since the lid was lowered).
const HEIGHTS := {"standard": 0.495, "waist": 0.993, "privacy": 2.192}
const PIECES := ["straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "post", "bend", "curve",
	"curve_large"]
const SETS := ["a", "b", "c"]
## Each piece's open ends in its own space: [axis, where, centre], the end
## lying in the plane where that axis (0 x, 2 z) is `where`, the hedge's middle
## at `centre` on the other axis. Godot's -z is north (Blender's +y).
const ENDS := {
	"straight": [[0, -0.5, 0.0], [0, 0.5, 0.0]],
	"straight_2": [[0, -0.5, 0.0], [0, 1.5, 0.0]],
	"straight_4": [[0, -0.5, 0.0], [0, 3.5, 0.0]],
	"corner": [[0, -0.5, 0.0], [2, -0.5, 0.0]],
	"tee": [[0, -0.5, 0.0], [0, 0.5, 0.0], [2, -0.5, 0.0]],
	"cross": [[0, -0.5, 0.0], [0, 0.5, 0.0], [2, -0.5, 0.0], [2, 0.5, 0.0]],
	"end": [[0, -0.5, 0.0]],
	"post": [],
	"bend": [[0, -0.5, 0.0], [2, -0.5, 0.0]],
	"curve": [[0, -0.5, 0.0], [2, -1.5, 1.0]],
	"curve_large": [[0, -0.5, 0.0], [2, -2.5, 2.0]],
}
const PLANE := 0.0005
const MATCH := 0.001
## The clusters on the lid tip up this far at most (hedge_kit.py, CLUSTER_TIP
## and TIP_JITTER, 33 mm).
const TOP_LIFT := 0.04

var _fails: Array[String] = []


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var model_scene := load(MODEL) as PackedScene
	var packed := load(SOURCE) as PackedScene
	if model_scene == null or packed == null:
		_fails.append("the model or the hedge scene does not load")
		_finish()
		return
	_check_model(model_scene.instantiate())
	var hedge := packed.instantiate() as Node3D
	add_child(hedge)
	await get_tree().process_frame
	var built := 0
	for h in HEIGHTS.size():
		var height_name: String = HEIGHTS.keys()[h]
		hedge.set("height", h)
		for p in PIECES.size():
			hedge.set("piece", p)
			for choice in SETS.size() + 1:
				hedge.set("leaf_clusters", choice)
				_check_built(hedge, "%s %s, clusters %s" % [height_name, PIECES[p],
					"by square" if choice == 0 else SETS[choice - 1]], HEIGHTS[height_name])
				built += 1
	if built != HEIGHTS.size() * PIECES.size() * (SETS.size() + 1):
		_fails.append("only %d placements were built" % built)
	_finish()


func _check_model(model: Node) -> void:
	var meshes := {}
	var shapes := {}
	for found in model.find_children("*", "MeshInstance3D", true, false):
		var mesh := found as MeshInstance3D
		meshes[String(mesh.name).trim_prefix(PREFIX)] = mesh.mesh
		if not mesh.find_children("*", "CollisionShape3D", true, false).is_empty():
			shapes[String(mesh.name).trim_prefix(PREFIX)] = true
	for height_name: String in HEIGHTS:
		var reference := _end_section(_vertices([meshes.get(height_name + "_straight"),
			meshes.get(height_name + "_straight_hat")]), ENDS["straight"][1])
		if reference.size() < 6:
			_fails.append("%s straight: its end has only %d points" % [height_name, reference.size()])
		var clustered := 0
		for piece: String in PIECES:
			var key := "%s_%s" % [height_name, piece]
			if not meshes.has(key) or not meshes.has(key + "_hat"):
				_fails.append("%s: body or lid missing from the model" % key)
				continue
			if not shapes.has(key):
				_fails.append("%s: its body doesn't collide" % key)
			for tag: String in SETS:
				var clusters := "%s_clusters_%s" % [key, tag]
				if meshes.has(clusters):
					clustered += 1
			for other: String in [key + "_hat"] + SETS.map(func(t: String) -> String: return "%s_clusters_%s" % [key, t]):
				if shapes.has(other):
					_fails.append("%s collides; only a body should" % other)
			var lid := (meshes[key + "_hat"] as Mesh).get_aabb()
			if absf(lid.end.y - HEIGHTS[height_name]) > 0.002:
				_fails.append("%s: its lid tops out at %.3f m, not %.3f" % [key, lid.end.y, HEIGHTS[height_name]])
			var points := _vertices([meshes[key], meshes[key + "_hat"]])
			for end: Array in ENDS[piece]:
				var off := _mismatch(_end_section(points, end), reference)
				if off > MATCH:
					_fails.append("%s: its end at %s = %.1f is %.1f mm off the straight's section" % [key,
						"xyz"[end[0]], end[1], off * 1000.0])
		# A scattering may happen to hold no cluster on a small piece, but most do.
		if clustered < PIECES.size() * SETS.size() / 2:
			_fails.append("%s: only %d of %d scatterings have clusters" % [height_name, clustered,
				PIECES.size() * SETS.size()])
	model.free()


func _check_built(hedge: Node3D, label: String, top: float) -> void:
	var shown := hedge.get_children(true)
	var meshes := shown.filter(func(n: Node) -> bool: return n is MeshInstance3D and n.mesh != null)
	var shapes: Array[Node] = []
	for n in shown:
		shapes.append_array(n.find_children("*", "CollisionShape3D", true, false))
	if meshes.size() != 1 or shown.size() != 2:
		_fails.append("%s: %d nodes, %d meshes; not one mesh and its collision" % [label, shown.size(), meshes.size()])
		return
	if shapes.size() != 1 or (shapes[0] as CollisionShape3D).shape == null:
		_fails.append("%s: %d collision shapes, not the body's one" % [label, shapes.size()])
	var mesh := (meshes[0] as MeshInstance3D).mesh
	if mesh.get_surface_count() != 1 or mesh.surface_get_material(0) == null:
		_fails.append("%s: %d surfaces, not one wearing the hedge's material" % [label, mesh.get_surface_count()])
	var box := mesh.get_aabb()
	if absf(box.position.y) > 0.002 or box.end.y < top - 0.002 or box.end.y > top + TOP_LIFT:
		_fails.append("%s: stands from %.3f to %.3f m, not 0 to %.3f (and its clusters' %.0f mm)" % [label,
			box.position.y, box.end.y, top, TOP_LIFT * 1000.0])


func _vertices(meshes: Array) -> PackedVector3Array:
	var out := PackedVector3Array()
	for mesh: Mesh in meshes:
		if mesh == null:
			continue
		for s in mesh.get_surface_count():
			out.append_array(mesh.surface_get_arrays(s)[Mesh.ARRAY_VERTEX])
	return out


## The points in an end's plane, as (across the hedge, up), rounded to a
## tenth of a millimetre and each once.
func _end_section(points: PackedVector3Array, end: Array) -> Array[Vector2]:
	var axis: int = end[0]
	var other := 2 if axis == 0 else 0
	var seen := {}
	var out: Array[Vector2] = []
	for v in points:
		if absf(v[axis] - float(end[1])) > PLANE:
			continue
		var p := Vector2(snappedf(absf(v[other] - float(end[2])), 0.0001), snappedf(v.y, 0.0001))
		if not seen.has(p):
			seen[p] = true
			out.append(p)
	return out


## The farthest any point of either section is from the other's nearest.
func _mismatch(a: Array[Vector2], b: Array[Vector2]) -> float:
	if a.is_empty() or b.is_empty():
		return INF
	var worst := 0.0
	for pair in [[a, b], [b, a]]:
		for p: Vector2 in pair[0]:
			var best := INF
			for q: Vector2 in pair[1]:
				best = minf(best, p.distance_to(q))
			worst = maxf(worst, best)
	return worst


func _finish() -> void:
	if _fails.is_empty():
		print("PASS: every piece of the boxwood hedge kit, in all three heights, has a colliding body, a lid and three cluster scatterings; every open end has the straight's exact cross-section; and the wrapper builds each piece and scattering as one mesh and one collision shape, standing on the ground at its height with its clusters no more than 4 cm over its lid")
	else:
		for failure in _fails:
			push_error("boxwood_hedge_test: " + failure)
	get_tree().quit(1 if not _fails.is_empty() else 0)
