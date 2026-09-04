extends Node

## Drives the real player controller over every segment introduced by the park
## rebuild: the expanded A/B trunks and every emitted C/D/F district route. The
## district legs are read back from the generated route bodies, so this checks
## the rounded, graded collision geometry rather than a parallel approximation
## of it in the test.

const ARRIVE := 1.45
const STALL_FRAMES := 72
const MAX_SECONDS := 10.0
const FALL_BELOW := 3.0
const TEST_SPEED := 8.0
const SETTLE_FRAMES := 4
const SETTLE_SECONDS := 1.5
const CROSS_TRACK := ARRIVE * 2.0
# The Player capsule is 0.35m in radius. Walking 0.90m inside the physical
# asphalt edge leaves only 0.55m of visual tolerance: close enough to prove the
# complete operating envelope, with enough room that tiny mesh seams are not
# mistaken for scenery occupying the route.
const EDGE_INSET := 0.90

var _player: CharacterBody3D
var _legs: Array[Dictionary] = []
var _leg := 0
var _from := Vector3.ZERO
var _to := Vector3.ZERO
var _elapsed := 0.0
var _still := 0
var _last := Vector3.ZERO
var _minimum_y := INF
var _fails: Array[String] = []
var _settling := false
var _settle_frames := 0
var _settle_elapsed := 0.0
var _plan_direction := Vector2.ZERO
var _plan_length := 0.0
var _closest_target_distance := INF
var _closest_target_at := Vector3.ZERO
var _settled_at := Vector3.ZERO
var _encountered_colliders := {}


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for _frame in 5:
		await get_tree().physics_frame
	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if _player == null:
		printerr("FAIL: no player in the persistent park")
		get_tree().quit(1)
		return
	_player.set("walk_speed", TEST_SPEED)
	_clear_crowds()
	await get_tree().physics_frame
	_build_legs()
	var filters := OS.get_cmdline_user_args().slice(1)
	if not filters.is_empty():
		_legs = _legs.filter(func(leg: Dictionary) -> bool:
			return _matches_filter(String(leg["label"]), filters))
	print("  walking %d directed complete-rebuild segments" % _legs.size())
	_start_leg()


func _matches_filter(label: String, filters: PackedStringArray) -> bool:
	for filter in filters:
		if label.contains(filter):
			return true
	return false


func _clear_crowds() -> void:
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_process(false)
		crowd.set_physics_process(false)
	for guest in get_tree().get_nodes_in_group("guest"):
		guest.queue_free()


func _build_legs() -> void:
	var world := get_tree().root.find_child("park_world", true, false)
	if world == null:
		_fails.append("the persistent world has no park_world")
		return
	var layers := [
		{"node": world.get_node_or_null("places/park_circulation"),
			"public_routes_only": true},
		{"node": world.get_node_or_null("places/park_routes"),
			"public_routes_only": true},
		# P5 is the one programmed parcel inside the fixed Plaza datum. Its three
		# audience-facing branches are structural circulation too, and their tight
		# pass round the protected west-arch pier needs the same full-envelope proof
		# as A-F. Performer and service paths remain operational, not public.
		{"node": world.get_node_or_null("places/park_program"),
			"public_routes_only": false},
	]
	# The promontory walk joins them since 2026-09-04: an access path rather
	# than a route run, and the only public path in the park that climbs a
	# landform end to end, so it is walked centre and both edges like A-F.
	var p5_public := [&"P5_audience_entry", &"P5_audience_release",
		&"P5_photo_access", &"P1_public_access"]
	for layer_spec in layers:
		var layer: Node = layer_spec["node"]
		if layer == null:
			_fails.append("the persistent world is missing a rebuild route layer")
			continue
		for body in layer.find_children("*", "StaticBody3D", true, false):
			var route := StringName(body.get_meta("route", &""))
			var is_primary := route in [&"A", &"B", &"C", &"D", &"E", &"F"]
			var is_p5_public := StringName(body.name) in p5_public
			if (bool(layer_spec["public_routes_only"]) and not is_primary) \
					or (not bool(layer_spec["public_routes_only"])
						and not is_p5_public):
				continue
			var points: PackedVector3Array = body.get_meta("points",
				PackedVector3Array())
			if points.size() < 2:
				_fails.append("%s has no published collision centreline" % body.name)
				continue
			var width := float(body.get_meta("width", 0.0))
			var closed := bool(body.get_meta("closed", false))
			_add_run_legs(String(body.name), points, width, closed)

	# These two rebuild runs deliberately retain their established scene owners,
	# so they have no generated `route_*` body to discover above. They are still
	# ordinary broad paving and belong in the complete-envelope walk. The west
	# monument and all NT-2-owned approaches remain with `walk_test.gd`, whose
	# authored legs follow the real cascade wings and terraces rather than drawing
	# a fictitious straight line through either protected water feature.
	for run in ParkPlan.REBUILD_PRIMARY_ROUTE_RUNS:
		if StringName(run["id"]) not in [&"a_parking_arrival", &"b_waterfront"]:
			continue
		var points: Array[Vector3] = []
		for source in run["points"]:
			points.append(ParkPlan.rebuild_expand_position(source))
		_add_run_legs(String(run["id"]), points, float(run["width"]), false)


func _add_run_legs(label: String, points, width: float, closed: bool) -> void:
	if width <= EDGE_INSET * 2.0:
		_fails.append("%s is too narrow for edge traversal" % label)
		return
	var lines := {"center": PackedVector3Array(points)}
	var edges := _path_edges(points, width - EDGE_INSET * 2.0, closed)
	lines["left"] = edges["left"]
	lines["right"] = edges["right"]
	for side in ["center", "left", "right"]:
		var line: PackedVector3Array = lines[side]
		for i in line.size() - 1:
			_add_leg("%s %s %02d out" % [label, side, i], line[i], line[i + 1])
			_add_leg("%s %s %02d back" % [label, side, i], line[i + 1], line[i])


# This is intentionally the same miter construction as `gen_props.gd` uses for
# the actual ribbon. Testing a per-segment normal would cut inside every bend
# and could pass while a façade or guard still occupied the real outside edge.
func _path_edges(points, width: float, closed: bool) -> Dictionary:
	var count: int = points.size()
	if closed and Vector3(points[0]).distance_to(Vector3(points[-1])) < 0.01:
		count -= 1
	var left := PackedVector3Array()
	var right := PackedVector3Array()
	var half := width * 0.5
	for i in count:
		var p := Vector3(points[i])
		var offset := Vector2.ZERO
		if not closed and i == 0:
			var d := Vector2(Vector3(points[1]).x - p.x,
				Vector3(points[1]).z - p.z).normalized()
			offset = Vector2(-d.y, d.x) * half
		elif not closed and i == count - 1:
			var d := Vector2(p.x - Vector3(points[i - 1]).x,
				p.z - Vector3(points[i - 1]).z).normalized()
			offset = Vector2(-d.y, d.x) * half
		else:
			var previous := Vector3(points[(i - 1 + count) % count])
			var following := Vector3(points[(i + 1) % count])
			var into := Vector2(p.x - previous.x, p.z - previous.z).normalized()
			var out := Vector2(following.x - p.x, following.z - p.z).normalized()
			var n0 := Vector2(-into.y, into.x)
			var n1 := Vector2(-out.y, out.x)
			var miter := n0 + n1
			if miter.length_squared() < 0.0001:
				miter = n1
			else:
				miter = miter.normalized()
			var reach := half / maxf(absf(miter.dot(n1)), 0.25)
			offset = miter * minf(reach, width)
		left.append(p + Vector3(offset.x, 0.0, offset.y))
		right.append(p - Vector3(offset.x, 0.0, offset.y))
	if closed:
		left.append(left[0])
		right.append(right[0])
	return {"left": left, "right": right}


func _add_leg(label: String, a: Vector3, b: Vector3) -> void:
	_legs.append({
		"label": label,
		"from": a + Vector3.UP * 1.2,
		"to": b + Vector3.UP * 1.2,
	})


func _start_leg() -> void:
	if _leg >= _legs.size():
		_report()
		return
	var current := _legs[_leg]
	_from = current["from"]
	_to = current["to"]
	Input.action_release("move_forward")
	var direction := _to - _from
	# A direct transform assignment leaves CharacterBody's physics transform one
	# frame behind and can sweep the capsule from the previous leg. On short
	# chords that displaced the settled start by metres, after which a perfectly
	# clear route looked like an overshoot into nearby scenery. The Player owns
	# its teleport contract; use it here as every real relocation does.
	_player.place_at(_from, atan2(-direction.x, -direction.z))
	_player.reset_physics_interpolation()
	var plan_delta := Vector2(direction.x, direction.z)
	_plan_length = plan_delta.length()
	_plan_direction = plan_delta / maxf(_plan_length, 0.001)
	_elapsed = 0.0
	_still = 0
	_last = _from
	_minimum_y = _from.y
	_settling = true
	_settle_frames = 0
	_settle_elapsed = 0.0
	_closest_target_distance = INF
	_closest_target_at = _from
	_encountered_colliders.clear()


func _physics_process(delta: float) -> void:
	if _player == null or _leg >= _legs.size():
		return
	if _settling:
		_settle_elapsed += delta
		if _player.is_on_floor():
			_settle_frames += 1
		else:
			_settle_frames = 0
		if _settle_frames < SETTLE_FRAMES and _settle_elapsed < SETTLE_SECONDS:
			return
		_settling = false
		_elapsed = 0.0
		_still = 0
		_last = _player.global_position
		_settled_at = _player.global_position
		_minimum_y = _player.global_position.y
		Input.action_press("move_forward")
		return
	_elapsed += delta
	var p := _player.global_position
	_record_collisions()
	_minimum_y = minf(_minimum_y, p.y)
	if p.distance_to(_last) < 0.004:
		_still += 1
	else:
		_still = 0
	_last = p

	var horizontal_target := Vector3(_to.x, p.y, _to.z)
	var target_distance := p.distance_to(horizontal_target)
	if target_distance < _closest_target_distance:
		_closest_target_distance = target_distance
		_closest_target_at = p
	var from_plan := Vector2(_from.x, _from.z)
	var relative := Vector2(p.x, p.z) - from_plan
	var progress := relative.dot(_plan_direction)
	var cross_track := absf(relative.cross(_plan_direction))
	# A short rounded chord can be crossed between physics frames at the test's
	# eight metres per second. Crossing its target plane inside the same narrow
	# route is an arrival; continuing until the body hits unrelated scenery is
	# not evidence that the chord was blocked.
	var arrived := target_distance < ARRIVE \
		or (progress >= _plan_length and cross_track <= CROSS_TRACK)
	var stalled := _still >= STALL_FRAMES
	var fell := p.y < minf(_from.y, _to.y) - FALL_BELOW
	if arrived or stalled or fell or _elapsed > MAX_SECONDS:
		Input.action_release("move_forward")
		_finish_leg(arrived, stalled, fell, p)


func _finish_leg(arrived: bool, stalled: bool, fell: bool, at: Vector3) -> void:
	var label: String = _legs[_leg]["label"]
	var verdict := "ok"
	if fell:
		verdict = "FELL"
	elif not arrived:
		verdict = "BLOCKED" if stalled else "TIMEOUT"
	if verdict != "ok":
		var blockers := _blockers()
		var horizontal := Vector2(_to.x - _from.x, _to.z - _from.z).length()
		var grade := (_to.y - _from.y) / maxf(horizontal, 0.001)
		var detail := "%s (%s at %.1f, %.1f; %.2f,%.2f -> %.2f,%.2f; settled %.1f,%.1f; dy %.2f / %.2fm = %.1f%%; nearest %.2fm at %.1f,%.1f; hit %s)" % [
			label, verdict, at.x, at.z, _from.x, _from.z, _to.x, _to.z,
			_settled_at.x, _settled_at.z,
			_to.y - _from.y, horizontal, grade * 100.0,
			_closest_target_distance, _closest_target_at.x, _closest_target_at.z,
			blockers]
		_fails.append(detail)
		print("  ", detail)
	_leg += 1
	_start_leg()


func _report() -> void:
	Input.action_release("move_forward")
	if _fails.is_empty():
		print("\n  PASS: every rebuilt path segment traverses in both directions")
		get_tree().quit()
		return
	printerr("\n  FAIL: %d of %d directed segments" % [_fails.size(), _legs.size()])
	for failure in _fails:
		printerr("    ", failure)
	get_tree().quit(1)


func _blockers() -> String:
	_record_collisions()
	var names := _encountered_colliders.keys()
	names.sort()
	var details: Array[String] = []
	for name in names:
		details.append("%s %s" % [name, _encountered_colliders[name]])
	return "; ".join(details) if not details.is_empty() else "nothing"


func _record_collisions() -> void:
	for i in _player.get_slide_collision_count():
		var collision := _player.get_slide_collision(i)
		var collider := collision.get_collider()
		if collider != null:
			var name := String(collider.name)
			if not _encountered_colliders.has(name):
				var point := collision.get_position()
				var normal := collision.get_normal()
				_encountered_colliders[name] = "at %.2f,%.2f,%.2f n %.2f,%.2f,%.2f" % [
					point.x, point.y, point.z, normal.x, normal.y, normal.z]
