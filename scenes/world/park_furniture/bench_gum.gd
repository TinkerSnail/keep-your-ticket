extends Node3D

## Chewing gum on this bench: story dressing, decided per bench, not painted in.
##
## Christina painted three pieces of gum into the plaza bench's texture, then
## agreed (2026-09-25) that gum belongs to one bench and not all six, and asked
## for it to be randomised completely, colour included. The texture standard
## says the same: asymmetry comes from a dressing layer, not the shared texture.
## So each bench decides here how many pieces it has (often none), where, what
## colour, and which of her three painted shapes, turned and sized a little.
##
## Seeded by where the bench stands, so a bench keeps the same gum every visit
## (a photograph of it stays true) while no two benches agree and nobody placed
## any of it.
##
## Where gum can go is found on the model, not written down: rays at the
## bench's own collision (derived from the visible mesh on export) up at the
## seat's underside, back at the backrest's front, and down at the seat top. A
## spot is kept only if the ray meets the right kind of face at the right
## height, and four more rays round it meet the same flat face, so a piece
## never hangs over an edge or a gap between boards. Heights come from the seat
## contract's markers, so they move with the bench.
##
## Guests share the bench's render layer, so a decal can't be told to skip
## them. It projects only DEPTH either way of the surface, and never onto the
## seat top where people sit.

const SHAPES := [
	preload("res://assets/props/dressing/gum_shape_green.png"),
	preload("res://assets/props/dressing/gum_shape_pink.png"),
	preload("res://assets/props/dressing/gum_shape_tan.png"),
]
## The shapes were cut from the bench texture at 576 px per metre, so that is
## their true size.
const SHAPE_PX_PER_M := 576.0

## How many pieces a bench has, and how likely each count is.
const COUNT_WEIGHTS := [0.4, 0.35, 0.17, 0.08]
## Where a piece goes: under the seat mostly, on the backrest's front
## sometimes, the seat top now and then.
const PLACE_WEIGHTS := {"under": 0.55, "back": 0.3, "top": 0.15}
## Gum as it comes out of mouths, and as it ages to grey.
const COLOURS := [
	Color8(235, 60, 150), Color8(245, 140, 185), Color8(120, 200, 110),
	Color8(80, 140, 220), Color8(215, 210, 195), Color8(180, 155, 100),
	Color8(150, 90, 190), Color8(205, 55, 65), Color8(230, 145, 60),
	Color8(95, 92, 88),
]

const DEPTH := 0.012  ## how far the decal projects either side of the surface
const EDGE_CHECK := 0.03  ## the four checking rays land this far round the spot
const SEAT_CLEAR := 0.22  ## no gum on the seat top this near a seat marker
const TRIES := 40

var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	var p := global_position
	_rng.seed = hash(Vector3i(roundi(p.x * 100.0), roundi(p.y * 100.0), roundi(p.z * 100.0)))
	# The bench's collision exists once physics has stepped.
	await get_tree().physics_frame
	var count := _pick(COUNT_WEIGHTS)
	for _i in count:
		_place_one()


func _pick(weights: Array) -> int:
	var r: float = _rng.randf() * weights.reduce(func(a, b): return a + b, 0.0)
	for i in weights.size():
		r -= weights[i]
		if r <= 0.0:
			return i
	return weights.size() - 1


func _place_one() -> void:
	var bench := get_parent() as Node3D
	var seat_top: float = (bench.get_node("seat_l") as Marker3D).position.y
	var seats := [(bench.get_node("seat_l") as Marker3D).position.x,
			(bench.get_node("seat_r") as Marker3D).position.x]
	var box := _model_box(bench)
	var places: Array = PLACE_WEIGHTS.keys()
	var place: String = places[_pick(PLACE_WEIGHTS.values())]
	for _attempt in TRIES:
		var x := _rng.randf_range(box.position.x + 0.05, box.end.x - 0.05)
		var from: Vector3
		var to: Vector3
		var normal: Vector3
		var low: float
		var high: float
		match place:
			"under":
				var z := _rng.randf_range(box.position.z, box.end.z)
				from = Vector3(x, seat_top - 0.2, z)
				to = Vector3(x, seat_top + 0.05, z)
				normal = Vector3.DOWN
				low = seat_top - 0.08
				high = seat_top - 0.02
			"back":
				var y := _rng.randf_range(seat_top + 0.03, box.end.y)
				from = Vector3(x, y, box.end.z + 0.2)
				to = Vector3(x, y, box.position.z)
				normal = Vector3.BACK
				low = y - 0.001
				high = y + 0.001
			_:
				if absf(x - seats[0]) < SEAT_CLEAR or absf(x - seats[1]) < SEAT_CLEAR:
					continue
				var z := _rng.randf_range(box.position.z, box.end.z)
				from = Vector3(x, seat_top + 0.2, z)
				to = Vector3(x, seat_top - 0.1, z)
				normal = Vector3.UP
				low = seat_top - 0.01
				high = seat_top + 0.01
		var hit := _cast(bench, from, to)
		if hit.is_empty():
			continue
		var at: Vector3 = bench.to_local(hit.position)
		var n: Vector3 = (bench.global_basis.inverse() * hit.normal).normalized()
		if n.dot(normal) < 0.95 or at.y < low or at.y > high:
			continue
		if not _flat_around(bench, at, n, from.direction_to(to)):
			continue
		_stick(bench, at, n)
		return


func _model_box(bench: Node3D) -> AABB:
	var box := AABB()
	var first := true
	for mesh in bench.get_node("model").find_children("*", "MeshInstance3D", true, false):
		var m := mesh as MeshInstance3D
		var local: AABB = bench.global_transform.affine_inverse() * m.global_transform * m.get_aabb()
		box = local if first else box.merge(local)
		first = false
	return box


func _cast(bench: Node3D, from: Vector3, to: Vector3) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(bench.to_global(from), bench.to_global(to))
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	# Only this bench counts; a guest or a neighbouring prop is not a spot.
	if hit.is_empty() or not bench.is_ancestor_of(hit.collider):
		return {}
	return hit


## True if the surface round `at` is the same flat face: four rays, EDGE_CHECK
## away along the surface, each meet it at the same depth.
func _flat_around(bench: Node3D, at: Vector3, n: Vector3, along: Vector3) -> bool:
	var side := n.cross(Vector3.RIGHT if absf(n.x) < 0.9 else Vector3.UP).normalized()
	var other := n.cross(side).normalized()
	for offset in [side, -side, other, -other]:
		var start: Vector3 = at + offset * EDGE_CHECK - along * 0.1
		var hit := _cast(bench, start, start + along * 0.2)
		if hit.is_empty():
			return false
		var there: Vector3 = bench.to_local(hit.position)
		var nn: Vector3 = (bench.global_basis.inverse() * hit.normal).normalized()
		if nn.dot(n) < 0.98 or absf((there - at).dot(n)) > 0.002:
			return false
	return true


func _stick(bench: Node3D, at: Vector3, n: Vector3) -> void:
	var shape: Texture2D = SHAPES[_rng.randi() % SHAPES.size()]
	var tint: Color = COLOURS[_rng.randi() % COLOURS.size()]
	# Older gum is duller and darker.
	tint = tint.darkened(_rng.randf_range(0.0, 0.35))
	var size := _rng.randf_range(0.85, 1.15)
	var decal := Decal.new()
	decal.name = "gum"
	decal.texture_albedo = shape
	decal.modulate = tint
	decal.size = Vector3(shape.get_width() / SHAPE_PX_PER_M * size, DEPTH * 2.0,
			shape.get_height() / SHAPE_PX_PER_M * size)
	decal.normal_fade = 0.5  # nothing on faces turned across the decal
	decal.distance_fade_enabled = true
	decal.distance_fade_begin = 12.0
	decal.distance_fade_length = 6.0
	# A decal projects down its own -Y: its Y is the surface's outward normal,
	# turned a random amount about it.
	var x_axis := n.cross(Vector3.FORWARD if absf(n.z) < 0.9 else Vector3.UP).normalized()
	var facing := Basis(x_axis, n, x_axis.cross(n)).orthonormalized()
	facing = Basis(n, _rng.randf_range(0.0, TAU)) * facing
	add_child(decal)
	decal.global_transform = bench.global_transform * Transform3D(facing, at)
