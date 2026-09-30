extends Node

## The hardscape kit (2026-09-30). In the model: every wall piece of every kind
## has a body that collides; every railing piece a body (rails and posts) that
## collides and pickets that don't; every curb piece only what doesn't
## collide; droppings never collide, and most wall and railing pieces have
## some. The fence's straights and curves are there twice, for a first cell on
## an even and an odd grid square, with posts every other square. Every open end of a piece has exactly its straight's cross-section,
## so pieces laid on the 1 m grid meet without a step or a gap (curves
## included: their ends square to the curve). In the wrapper
## (scenes/world/landscape_kit/hardscape_kit.tscn): every kind and piece, and
## every wall with its pier, railing and railing post, builds as one mesh of one surface and
## the collision its layers carry, standing where its heights say; a fence
## has posts wherever its square says it should. Measured on
## the imported meshes, not the builder's numbers.

const SOURCE := "res://scenes/world/landscape_kit/hardscape_kit.tscn"
const MODEL := "res://assets/props/hardscape_kit.glb"
const PREFIX := "hardscape_kit_"
const WALL_KINDS := ["wall", "town_wall", "concrete_wall"]
const SIZES := ["seat", "garden"]
const WALL_PIECES := ["straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "bend", "curve",
	"curve_large", "pier"]
const RAILING_PIECES := {
	"wall": ["straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "pier", "post", "bend",
		"curve", "curve_large"],
	"fence": ["straight_even", "straight_odd", "straight_2_even", "straight_2_odd", "straight_4_even",
		"straight_4_odd", "corner", "tee", "cross", "end", "post", "bend_even", "bend_odd", "curve_even",
		"curve_odd", "curve_large_even", "curve_large_odd"],
}
## The fence pieces with no post of their own on a square: [piece, square].
const FENCE_BARE := [["straight", "odd"], ["bend", "odd"]]
## The fence's top rail, and how far its posts go into the ground.
const FENCE_RAIL_TOP := 1.10
const FENCE_POST_SINK := 0.3
const CURB_PIECES := {
	"road": ["straight", "straight_2", "straight_4", "bend", "curve", "curve_large", "bend_in", "curve_in",
		"curve_large_in", "end", "cut"],
	"road_red": ["straight", "straight_2", "straight_4", "bend", "curve", "curve_large", "bend_in", "curve_in",
		"curve_large_in", "end", "cut"],
	"edging": ["straight", "straight_2", "straight_4", "corner", "tee", "end", "bend", "curve", "curve_large"],
}
## Each piece's open ends in its own space: [axis, where, centre], the end in
## the plane where that axis (0 x, 2 z) is `where`, the run's middle at
## `centre` on the other axis. Godot's -z is north (Blender's +y).
const ENDS := {
	"straight": [[0, -0.5, 0.0], [0, 0.5, 0.0]],
	"straight_2": [[0, -0.5, 0.0], [0, 1.5, 0.0]],
	"straight_4": [[0, -0.5, 0.0], [0, 3.5, 0.0]],
	"corner": [[0, -0.5, 0.0], [2, -0.5, 0.0]],
	"tee": [[0, -0.5, 0.0], [0, 0.5, 0.0], [2, -0.5, 0.0]],
	"cross": [[0, -0.5, 0.0], [0, 0.5, 0.0], [2, -0.5, 0.0], [2, 0.5, 0.0]],
	"end": [[0, -0.5, 0.0]],
	"pier": [[0, -0.5, 0.0], [0, 0.5, 0.0]],
	"post": [[0, -0.5, 0.0], [0, 0.5, 0.0]],
	"bend": [[0, -0.5, 0.0], [2, -0.5, 0.0]],
	"curve": [[0, -0.5, 0.0], [2, -1.5, 1.0]],
	"curve_large": [[0, -0.5, 0.0], [2, -2.5, 2.0]],
	"bend_in": [[0, -0.5, 0.0], [2, 0.5, 0.0]],
	"curve_in": [[0, -0.5, 0.0], [2, 1.5, 1.0]],
	"curve_large_in": [[0, -0.5, 0.0], [2, 2.5, 2.0]],
	"cut": [[0, -0.5, 0.0], [0, 1.5, 0.0]],
}
const PLANE := 0.0005
const MATCH := 0.001
## Heights (hardscape_kit.py): each wall's coping top at its middle (the face's
## top plus its wash), its pier's cap top likewise, how far below the ground a
## wall reaches, and the wall railing's top rail and its posts' tops over the
## coping.
const COPING_TOP := {"seat": 0.487, "garden": 0.712}
const CAP_TOP := {"seat": 1.162, "garden": 1.387}
const COPING_FACE := {"seat": 0.475, "garden": 0.70}
const FOOT := 0.2
const RAIL_TOP := 0.55
const POST_TOP := 0.56
## Droppings lie this far over what they're on, at most.
const LIFT := 0.003
const SETS := ["a", "b", "c"]

var _fails: Array[String] = []
var _meshes := {}
var _shapes := {}


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var model_scene := load(MODEL) as PackedScene
	var packed := load(SOURCE) as PackedScene
	if model_scene == null or packed == null:
		_fails.append("the model or the kit scene does not load")
		_finish()
		return
	var model := model_scene.instantiate()
	for found in model.find_children("*", "MeshInstance3D", true, false):
		var mesh := found as MeshInstance3D
		var part := String(mesh.name).trim_prefix(PREFIX)
		_meshes[part] = mesh.mesh
		if not mesh.find_children("*", "CollisionShape3D", true, false).is_empty():
			_shapes[part] = true
	model.free()
	_check_model()
	var kit := packed.instantiate() as Node3D
	add_child(kit)
	await get_tree().process_frame
	_check_wrapper(kit)
	_finish()


func _check_model() -> void:
	for kind: String in WALL_KINDS:
		for size: String in SIZES:
			var group := "%s_%s" % [kind, size]
			_check_family(group, WALL_PIECES, "", true)
			_check_droppings(group, WALL_PIECES)
	for size: String in RAILING_PIECES:
		var group := "railing_%s" % size
		_check_family(group, RAILING_PIECES[size], "", true)
		for piece: String in RAILING_PIECES[size]:
			var pickets := "%s_%s_visual" % [group, piece]
			if not _meshes.has(pickets):
				_fails.append("%s_%s: no pickets" % [group, piece])
			elif _shapes.has(pickets):
				_fails.append("%s: pickets collide" % pickets)
		_check_droppings(group, RAILING_PIECES[size])
	for size: String in CURB_PIECES:
		_check_family("curb_%s" % size, CURB_PIECES[size], "_visual", false)
	for part: String in _meshes:
		if part.contains("_droppings_") and _shapes.has(part):
			_fails.append("%s: droppings collide" % part)


## Every piece of a family present, colliding or not, and its open ends
## matching its straight's.
func _check_family(group: String, pieces: Array, suffix: String, collides: bool) -> void:
	var straight := group + "_straight" + suffix
	if not _meshes.has(straight):
		straight = group + "_straight_odd" + suffix
	var reference := _end_section(_vertices(_meshes.get(straight)), ENDS["straight"][1])
	if reference.size() < 4:
		_fails.append("%s straight: its end has only %d points" % [group, reference.size()])
		return
	for piece: String in pieces:
		var key := "%s_%s%s" % [group, piece, suffix]
		if not _meshes.has(key):
			_fails.append("%s: missing from the model" % key)
			continue
		if collides != _shapes.has(key):
			_fails.append("%s: %s" % [key, "doesn't collide" if collides else "collides"])
		if not collides and _meshes.has("%s_%s" % [group, piece]):
			_fails.append("%s_%s: a colliding body it shouldn't have" % [group, piece])
		var points := _vertices(_meshes[key])
		# A wall's pier stands on its own, closed all round.
		var ends: Array = [] if piece == "pier" and not group.begins_with("railing") else ENDS[_base(piece)]
		for end: Array in ends:
			var off := _mismatch(_end_section(points, end), reference)
			if off > MATCH:
				_fails.append("%s: its end at %s = %.1f is %.1f mm off the straight's section" % [key,
					"xyz"[end[0]], end[1], off * 1000.0])


## A fence piece's name without its square.
func _base(piece: String) -> String:
	return piece.trim_suffix("_even").trim_suffix("_odd")


func _check_droppings(group: String, pieces: Array) -> void:
	var found := 0
	for piece: String in pieces:
		for tag: String in SETS:
			if _meshes.has("%s_%s_droppings_%s" % [group, piece, tag]):
				found += 1
	if found < pieces.size() * SETS.size() / 3:
		_fails.append("%s: only %d of %d droppings scatterings have any" % [group, found, pieces.size() * SETS.size()])


func _check_wrapper(kit: Node3D) -> void:
	var constants: Dictionary = kit.get_script().get_script_constant_map()
	var kinds: Array = constants["KINDS"]
	var pieces: Array = constants["PIECES"]
	var built := 0
	for k in kinds.size():
		var kind_name: String = kinds[k]
		# A fence on an even square and on an odd one.
		for at: Vector3 in ([Vector3.ZERO, Vector3(1.0, 0.0, 0.0)] if kind_name == "railing_fence" else [Vector3.ZERO]):
			kit.position = at
			built += _check_kind(kit, k, kind_name, pieces)
	kit.position = Vector3.ZERO
	kit.set("pier", false)
	kit.set("railing", false)
	kit.set("post", false)
	if built < 400:
		_fails.append("only %d placements were built" % built)


func _check_kind(kit: Node3D, k: int, kind_name: String, pieces: Array) -> int:
	var built := 0
	kit.set("kind", k)
	for p in pieces.size():
		var piece_name: String = pieces[p]
		var named := "%s_%s" % [kind_name, piece_name]
		if not (_meshes.has(named) or _meshes.has(named + "_visual") or _meshes.has(named + "_even")):
			continue
		kit.set("piece", p)
		var size := kind_name.get_slice("_", kind_name.get_slice_count("_") - 1)
		var wall := COPING_TOP.has(size)
		var combos := [[false, false, false]]
		if wall and piece_name != "pier":
			combos = []
			for bits in 8:
				combos.append([bits & 1 != 0, bits & 2 != 0, bits & 4 != 0])
		for combo: Array in combos:
			kit.set("pier", combo[0])
			kit.set("railing", combo[1])
			kit.set("post", combo[2])
			for choice in SETS.size() + 2:
				kit.set("droppings", choice)
				_check_built(kit, kind_name, piece_name, combo, choice)
				built += 1
	return built


func _check_built(kit: Node3D, kind_name: String, piece_name: String, combo: Array, choice: int) -> void:
	var with_pier: bool = combo[0]
	var with_railing: bool = combo[1]
	var with_post: bool = combo[2]
	var label := "%s %s%s%s%s, droppings %d" % [kind_name, piece_name, " + pier" if with_pier else "",
		" + railing" if with_railing else "", " + post" if with_post else "", choice]
	var shown := kit.get_children(true)
	var meshes := shown.filter(func(n: Node) -> bool: return n is MeshInstance3D and n.mesh != null)
	var shapes: Array[Node] = []
	for n in shown:
		shapes.append_array(n.find_children("*", "CollisionShape3D", true, false))
	if meshes.size() != 1:
		_fails.append("%s: %d meshes, not one" % [label, meshes.size()])
		return
	var mesh := (meshes[0] as MeshInstance3D).mesh
	if mesh.get_surface_count() != 1 or mesh.surface_get_material(0) == null:
		_fails.append("%s: %d surfaces, not one wearing the kit's material" % [label, mesh.get_surface_count()])
	var size := kind_name.get_slice("_", kind_name.get_slice_count("_") - 1)
	var want_shapes := 0
	if kind_name.begins_with("railing"):
		want_shapes = 1
	elif COPING_TOP.has(size):
		want_shapes = 1 + int(with_pier and piece_name != "pier") + int(with_railing and piece_name != "pier")
	if shapes.size() != want_shapes:
		_fails.append("%s: %d collision shapes, not %d" % [label, shapes.size(), want_shapes])
	var box := mesh.get_aabb()
	if kind_name == "railing_fence":
		var square := "even" if posmod(roundi(kit.position.x) + roundi(kit.position.z), 2) == 0 else "odd"
		var posted := not FENCE_BARE.has([piece_name, square])
		var ball := box.end.y > FENCE_RAIL_TOP + 0.05
		var sunk := box.position.y < -FENCE_POST_SINK + 0.01
		if ball != posted or sunk != posted:
			_fails.append("%s on an %s square: %s, but stands from %.3f to %.3f m" % [label, square,
				"should have a post" if posted else "should have none", box.position.y, box.end.y])
	if not COPING_TOP.has(size):
		return
	var top: float = CAP_TOP[size] if piece_name == "pier" or with_pier else COPING_TOP[size]
	if with_railing and piece_name != "pier" and not with_pier:
		top = maxf(top, COPING_FACE[size] + RAIL_TOP)
	if absf(box.position.y + FOOT) > 0.002 or box.end.y < top - 0.002 or box.end.y > top + 0.012 + LIFT:
		_fails.append("%s: stands from %.3f to %.3f m, not %.3f to %.3f" % [label, box.position.y, box.end.y,
			-FOOT, top])
	# The middle post rises a centimetre over the top rail; without it nothing
	# but droppings does (an end has its own post).
	var post_shown := with_railing and with_post and not with_pier and piece_name == "straight"
	var post_top: float = COPING_FACE[size] + POST_TOP
	if with_railing and not with_pier and piece_name not in ["pier", "end"] \
			and (box.end.y > post_top - 0.002) != post_shown:
		_fails.append("%s: its railing %s a post (top %.3f m)" % [label, "lacks" if post_shown else "has",
			box.end.y])


func _vertices(mesh: Mesh) -> PackedVector3Array:
	var out := PackedVector3Array()
	if mesh == null:
		return out
	for s in mesh.get_surface_count():
		out.append_array(mesh.surface_get_arrays(s)[Mesh.ARRAY_VERTEX])
	return out


## The points in an end's plane, as (across the run, up), rounded to a tenth
## of a millimetre and each once.
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
		print("PASS: every piece of the hardscape kit is in the model, walls and rails colliding, pickets, curbs and droppings not; every open end has its straight's exact cross-section; and the wrapper builds every kind, piece, pier, railing, railing post and droppings choice as one mesh of one surface with its layers' collision, the walls standing from 0.2 m below the ground to their coping, cap or top rail")
	else:
		for failure in _fails.slice(0, 40):
			push_error("hardscape_kit_test: " + failure)
		print("FAIL: %d problems in the hardscape kit" % _fails.size())
	get_tree().quit(1 if not _fails.is_empty() else 0)
