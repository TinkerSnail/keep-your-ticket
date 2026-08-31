extends Node

## Dev tool: checks that both park transport layers are real loops, move during
## opening hours, carry visible riders, and park empty after close.
##
## This is deliberately about service rather than scenery. A still can show a
## train on a rail and cannot show whether it ever leaves the station, stops on
## the route that owns its platform, or responds to the park clock.

const MAIN := preload("res://scenes/main/main.tscn")
const Plan := preload("res://scripts/park_plan.gd")

const SETTLE_FRAMES := 8
const MOVE_FRAMES := 660 # Eleven seconds at the documented fixed 60 fps.

var _fails: Array[String] = []


func _ready() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	add_child(MAIN.instantiate())
	_run.call_deferred()


func _run() -> void:
	for i in SETTLE_FRAMES:
		await get_tree().process_frame

	var mini := get_node_or_null("main/park_world/places/thresholds/kiddie_train")
	var grand := get_node_or_null("main/park_world/shared/park_transit/grand_tram")
	if mini == null or grand == null:
		_fail("the land-local railway or persistent Grand Circuit did not mount")
		_finish()
		return

	_check_route("kiddie railway", Plan.kiddie_rail_loop(), 40.0, 80.0, 0.04)
	_check_route("Grand Circuit", Plan.grand_tram_loop(), 600.0, 1200.0, 0.14)
	_check_stations(Plan.grand_tram_loop())
	_check_vehicle("kiddie railway", mini, 3, 4)
	_check_vehicle("Grand Circuit", grand, 4, 18)

	var mini_before: float = mini.route_distance()
	var grand_before: float = grand.route_distance()
	for i in MOVE_FRAMES:
		await get_tree().process_frame
	if _forward_distance(mini_before, mini.route_distance(), mini.route_length()) < 0.5:
		_fail("kiddie railway did not leave its opening dwell")
	if _forward_distance(grand_before, grand.route_distance(), grand.route_length()) < 0.5:
		_fail("Grand Circuit did not leave its opening dwell")

	ParkClock.set_clock(22, 15)
	for i in 3:
		await get_tree().process_frame
	_check_parked("kiddie railway", mini)
	_check_parked("Grand Circuit", grand)

	ParkClock.set_clock(15, 0)
	for i in 3:
		await get_tree().process_frame
	if not mini.is_operating() or not grand.is_operating():
		_fail("one or both services did not restart when the open day was restored")
	if not _all_riders_visible(mini) or not _all_riders_visible(grand):
		_fail("one or both services restarted without passengers")

	_finish()


func _check_route(label: String, route: Array[Vector3], min_length: float,
		max_length: float, max_grade: float) -> void:
	if route.size() < 4:
		_fail("%s has too few route samples" % label)
		return
	if not route[0].is_equal_approx(route[-1]):
		_fail("%s is not a closed loop" % label)
	var length := 0.0
	var steepest := 0.0
	for i in route.size() - 1:
		var delta := route[i + 1] - route[i]
		length += delta.length()
		var run := Vector2(delta.x, delta.z).length()
		if run > 0.001:
			steepest = maxf(steepest, absf(delta.y) / run)
	if length < min_length or length > max_length:
		_fail("%s length %.1fm is outside %.1f-%.1fm" % [
			label, length, min_length, max_length])
	if steepest > max_grade:
		_fail("%s reaches a %.1f%% grade (limit %.1f%%)" % [
			label, steepest * 100.0, max_grade * 100.0])
	print("  %-16s %6.1fm, steepest sampled grade %4.1f%%" % [
		label, length, steepest * 100.0])


func _check_stations(route: Array[Vector3]) -> void:
	for station in Plan.GRAND_TRAM_STATIONS:
		var nearest := INF
		for i in route.size() - 1:
			nearest = minf(nearest, _point_segment_distance(
				station["at"], route[i], route[i + 1]))
		if nearest > 0.75:
			_fail("Grand Circuit's %s platform is %.2fm off its service route" % [
				station["id"], nearest])


func _check_vehicle(label: String, vehicle: Node, expected_units: int,
		expected_riders: int) -> void:
	if vehicle.route_length() <= 0.0 or not vehicle.is_operating():
		_fail("%s did not start as an operating service" % label)
	var units := vehicle.get_children()
	if units.size() != expected_units:
		_fail("%s has %d vehicles, expected %d" % [label, units.size(), expected_units])
	var riders := vehicle.find_children("rider_*", "Node3D", true, false)
	if riders.size() != expected_riders:
		_fail("%s carries %d riders, expected %d" % [label, riders.size(), expected_riders])
	if not _all_riders_visible(vehicle):
		_fail("%s opened without visible riders" % label)


func _check_parked(label: String, vehicle: Node) -> void:
	if not is_zero_approx(vehicle.route_distance()) or vehicle.is_operating():
		_fail("%s did not park at its home point after a closed-hours jump" % label)
	if not _all_riders_hidden(vehicle):
		_fail("%s remained occupied after it parked" % label)


func _all_riders_visible(vehicle: Node) -> bool:
	var riders := vehicle.find_children("rider_*", "Node3D", true, false)
	return not riders.is_empty() and riders.all(func(rider: Node) -> bool: return rider.visible)


func _all_riders_hidden(vehicle: Node) -> bool:
	var riders := vehicle.find_children("rider_*", "Node3D", true, false)
	return not riders.is_empty() and riders.all(func(rider: Node) -> bool: return not rider.visible)


func _point_segment_distance(point: Vector3, a: Vector3, b: Vector3) -> float:
	var ab := b - a
	var t := clampf((point - a).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
	return point.distance_to(a + ab * t)


func _forward_distance(before: float, after: float, length: float) -> float:
	return fposmod(after - before, length)


func _fail(message: String) -> void:
	_fails.append(message)
	printerr("FAIL: ", message)


func _finish() -> void:
	if _fails.is_empty():
		print("\n  both transport services loop, move, carry riders, and park after close")
		get_tree().quit()
	else:
		printerr("\n  %d transit checks failed" % _fails.size())
		get_tree().quit(1)
