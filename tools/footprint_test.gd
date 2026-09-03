extends Node

## Dev tool: proves that the expanded park reads as one intentional circulation
## system rather than a collection of ribbons that happen to overlap.
##
## It owns the facts introduced by the footprint pass: the outer envelope, the
## split parking arrival, the protected cascade clearances, the named pedestrian
## crossings of the Grand Circuit, and the retirement of the obsolete NNW
## dogleg. Traversal remains `walk_test`'s job; this catches plan errors before a
## body has to discover them.

const Plan := preload("res://scripts/park_plan.gd")

const EPS := 0.12
const CROSSING_CAPTURE := 12.0
const PROTECTED_MARGIN := 1.0

var _fails: Array[String] = []


func _ready() -> void:
	_check_envelope()
	_check_world_reserve()
	_check_route_handoffs()
	_check_grand_circuit()
	_check_arrival_scene()
	_check_retired_geometry()
	_finish()


func _check_envelope() -> void:
	var lo := Vector2(Plan.REBUILD_FOOTPRINT_MIN_X, Plan.REBUILD_FOOTPRINT_MIN_Z)
	var hi := Vector2(Plan.REBUILD_FOOTPRINT_MAX_X, Plan.REBUILD_FOOTPRINT_MAX_Z)
	for run in Plan.rebuild_route_runs():
		for point in run["points"]:
			if point.x < lo.x - EPS or point.x > hi.x + EPS \
					or point.y < lo.y - EPS or point.y > hi.y + EPS:
				_fail("%s leaves the expanded park envelope at %s" % [run["id"], point])
	for band in Plan.REBUILD_TERRAIN_BANDS:
		var shapes: Array = Plan.REBUILD_TERRAIN_BANDS[band]["shapes"]
		for i in shapes.size():
			for point in Plan.rebuild_terrain_shape(band, i):
				if point.x < lo.x - EPS or point.x > hi.x + EPS \
						or point.y < lo.y - EPS or point.y > hi.y + EPS:
					_fail("terrain %s leaves the expanded park envelope at %s" % [band, point])
	print("  developed park envelope %.0fm x %.0fm" % [hi.x - lo.x, hi.y - lo.y])


## The atlas envelope is allowed to be tight around program; the world is not.
## These are independent constants so extending scenery can never re-transform
## a path, move a ride, or disturb either protected cascade.
func _check_world_reserve() -> void:
	var margin := Plan.REBUILD_WORLD_MIN_PROGRAM_MARGIN
	var east := Plan.REBUILD_WORLD_LAND_TO_X - Plan.REBUILD_FOOTPRINT_MAX_X
	var north := Plan.REBUILD_FOOTPRINT_MIN_Z - Plan.REBUILD_WORLD_LAND_FROM_Z
	var south := Plan.REBUILD_WORLD_LAND_TO_Z - Plan.REBUILD_FOOTPRINT_MAX_Z
	var west_water := Plan.REBUILD_FOOTPRINT_MIN_X \
		- Plan.REBUILD_WORLD_WATER_FROM_X
	for pair in [
		["east land", east], ["north land", north], ["south land", south],
		["west ocean", west_water],
	]:
		if float(pair[1]) < margin - EPS:
			_fail("%s leaves only %.1fm beyond the developed park, expected %.1fm" % [
				pair[0], pair[1], margin])

	var ground: Node = load("res://scenes/world/park_groundworks.tscn").instantiate()
	var reserve := ground.find_child("terrain_world_mainland_reserve", true, false)
	if reserve == null:
		_fail("the surrounding mainland reserve is not mounted")
	else:
		var surface := reserve.find_child("surface", false, false) as MeshInstance3D
		if surface == null or surface.mesh == null:
			_fail("the surrounding mainland reserve has no surface mesh")
		else:
			var bounds := surface.mesh.get_aabb()
			if bounds.position.x > Plan.REBUILD_WORLD_LAND_FROM_X + EPS \
					or bounds.end.x < Plan.REBUILD_WORLD_LAND_TO_X - EPS \
					or bounds.position.z > Plan.REBUILD_WORLD_LAND_FROM_Z + EPS \
					or bounds.end.z < Plan.REBUILD_WORLD_LAND_TO_Z - EPS:
				_fail("the mainland mesh does not reach all four published world bounds")
	for id in ["north", "south"]:
		if ground.find_child("terrain_world_coast_%s" % id, true, false) == null:
			_fail("the %s coastal reserve is not mounted" % id)
	ground.free()

	var west: Node = load("res://scenes/world/west_shell.tscn").instantiate()
	var water := west.find_child("water", true, false) as CSGBox3D
	if water == null:
		_fail("the enlarged ocean is missing")
	else:
		var water_lo := water.position - water.size * 0.5
		var water_hi := water.position + water.size * 0.5
		if water_lo.x > Plan.REBUILD_WORLD_WATER_FROM_X + EPS \
				or water_hi.x < Plan.REBUILD_WORLD_WATER_TO_X - EPS \
				or water_lo.z > Plan.REBUILD_WORLD_WATER_FROM_Z + EPS \
				or water_hi.z < Plan.REBUILD_WORLD_WATER_TO_Z - EPS:
			_fail("the ocean does not reach all four published world bounds")
	var shore_n := west.find_child("shore_north_reserve", true, false) as CSGBox3D
	var shore_s := west.find_child("shore_south_reserve", true, false) as CSGBox3D
	if shore_n == null or shore_s == null:
		_fail("the planted north/south coastal benches are missing")
	else:
		var shore_lo := shore_n.position.z - shore_n.size.z * 0.5
		var shore_hi := shore_s.position.z + shore_s.size.z * 0.5
		if shore_lo > Plan.REBUILD_WORLD_COAST_FROM_Z + EPS \
				or shore_hi < Plan.REBUILD_WORLD_COAST_TO_Z - EPS:
			_fail("the coastal bench still stops inside the surrounding world")
	west.free()

	print("  world reserve margins: E %.0fm, N %.0fm, S %.0fm, W ocean %.0fm" % [
		east, north, south, west_water])


func _check_route_handoffs() -> void:
	var parking := _run(&"a_parking_arrival")
	var entrance := _run(&"a_entrance")
	var headland := _run(&"a_headland")
	var lighthouse := _run(&"a_lighthouse_loop")
	var hub := _run(&"a_hub_ring")
	if parking.is_empty() or entrance.is_empty() or headland.is_empty() \
			or lighthouse.is_empty() or hub.is_empty():
		return
	_expect_near("parking arrival outer end", parking[0],
		Vector2(0.0, Plan.ARRIVAL_AXIS_TO_Z))
	_expect_near("parking arrival to apron", parking[-1], entrance[0])
	_expect_near("route A begins at the apron", entrance[0],
		Vector2(0.0, Plan.APRON_Z))
	_expect_near("route A enters the hub", entrance[-1], Vector2(0.0, 18.0))
	_expect_near("route A leaves the hub", headland[0], Vector2(0.0, -18.0))
	_expect_near("route A reaches the lighthouse loop", headland[-1], lighthouse[0])
	if hub[0].distance_to(hub[-1]) > EPS or lighthouse[0].distance_to(lighthouse[-1]) > EPS:
		_fail("one of route A's two destination loops is open")

	var north := _run(&"b_north_return")
	var waterfront := _run(&"b_waterfront")
	var south := _run(&"b_south_return")
	if not north.is_empty() and not waterfront.is_empty() and not south.is_empty():
		_expect_near("B north return to waterfront", north[-1], waterfront[0])
		_expect_near("B waterfront to south return", waterfront[-1], south[0])


func _check_grand_circuit() -> void:
	var grand3: Array[Vector3] = Plan.grand_tram_loop(16)
	var grand := _xz(grand3)
	if grand.size() < 4 or grand[0].distance_to(grand[-1]) > EPS:
		_fail("the Grand Circuit is not a closed loop")
		return

	var lane_half: float = Plan.GRAND_TRAM_LANE_W * 0.5
	var nt1: Dictionary = Plan.REBUILD_PROTECTED_ZONES[&"NT-1"]
	var nt2: Dictionary = Plan.REBUILD_PROTECTED_ZONES[&"NT-2"]
	var nt1_clear := INF
	var nt2_clear := INF
	for point in grand:
		nt1_clear = minf(nt1_clear, _point_rect_distance(point,
			nt1["min"], nt1["max"]))
		nt2_clear = minf(nt2_clear, _point_ellipse_distance(point,
			nt2["centre"], nt2["radii"]))
	if nt1_clear < lane_half + PROTECTED_MARGIN:
		_fail("Grand Circuit leaves only %.2fm centreline clearance to NT-1" % nt1_clear)
	if nt2_clear < lane_half + PROTECTED_MARGIN:
		_fail("Grand Circuit leaves only %.2fm centreline clearance to NT-2" % nt2_clear)
	print("  Grand Circuit edge clearance: NT-1 %.2fm, NT-2 %.2fm" % [
		nt1_clear - lane_half, nt2_clear - lane_half])

	for station in Plan.GRAND_TRAM_STATIONS:
		var near := _nearest_on_run(Vector2(station["at"].x, station["at"].z), grand)
		if near["distance"] > 0.75:
			_fail("Grand Circuit station %s is %.2fm off its lane" % [
				station["id"], near["distance"]])

	var crossings := {}
	for crossing in Plan.GRAND_TRAM_CROSSINGS:
		var id: StringName = crossing["id"]
		var at := Vector2(crossing["at"].x, crossing["at"].z)
		var pedestrian := _run(crossing["pedestrian"])
		var road_hit := _nearest_on_run(at, grand)
		var walk_hit := _nearest_on_run(at, pedestrian)
		if road_hit["distance"] > 0.9 or walk_hit["distance"] > 0.9:
			_fail("crossing %s is not on both of its named routes" % id)
		var angle := _crossing_angle(road_hit["tangent"], walk_hit["tangent"])
		if angle < 30.0:
			_fail("crossing %s meets at only %.1f degrees" % [id, angle])
		var captures: Array = crossing.get("captures", [crossing["pedestrian"]])
		for captured in captures:
			crossings[captured] = at

	# Any overlap between a pedestrian route and the vehicle envelope must be
	# captured by one of the crossings above. This is what distinguishes a
	# deliberate crossing from the former near-tangent shared lanes.
	for run in Plan.rebuild_route_runs():
		var points: Array = run["points"]
		var hit := _nearest_between_runs(grand, points)
		var envelope: float = lane_half + float(run["width"]) * 0.5
		if hit["distance"] >= envelope:
			continue
		if not crossings.has(run["id"]):
			_fail("Grand Circuit overlaps unregistered route %s by %.2fm" % [
				run["id"], envelope - hit["distance"]])
			continue
		if hit["at"].distance_to(crossings[run["id"]]) > CROSSING_CAPTURE:
			_fail("Grand Circuit's overlap with %s escapes its controlled crossing" % run["id"])
	print("  %d controlled Grand Circuit crossings" % Plan.GRAND_TRAM_CROSSINGS.size())


func _check_arrival_scene() -> void:
	var packed: PackedScene = load("res://scenes/world/entrance.tscn")
	var root: Node = packed.instantiate()
	var cars := root.find_children("car_*", "Node3D", true, false)
	if cars.size() != 42:
		_fail("split parking has %d cars, expected 42" % cars.size())
	for car in cars:
		var p: Vector3 = car.position
		if absf(p.x) < Plan.PARKING_INNER_X + 5.5:
			_fail("%s intrudes into the central parking walk at x=%.2f" % [car.name, p.x])
		if p.z < Plan.PARKING_FROM_Z or p.z > Plan.PARKING_TO_Z:
			_fail("%s sits outside its parking field at z=%.2f" % [car.name, p.z])
	for required in ["parking_arrival_bed", "lot_ground_west", "lot_ground_east",
			"apron_rail_west", "apron_rail_east"]:
		if root.find_child(required, true, false) == null:
			_fail("expanded arrival is missing %s" % required)
	if root.find_child("apron_rail", true, false) != null:
		_fail("the obsolete full-width apron rail still exists")
	if root.find_children("parking_crosswalk_*", "Node3D", true, false).size() != 7:
		_fail("the parking/Grand Circuit crossing is not fully marked")
	root.free()
	print("  split parking keeps a %.0fm clear central arrival" % [
		Plan.PARKING_INNER_X * 2.0])


func _check_retired_geometry() -> void:
	var thresholds: Node = load("res://scenes/world/thresholds.tscn").instantiate()
	if not thresholds.find_children("way_*", "Node", true, false).is_empty():
		_fail("an obsolete X1-X4 threshold still mounts across routes A, C, or D")
	thresholds.free()
	var east: Node = load("res://scenes/world/east_cascade.tscn").instantiate()
	for retired in ["kiddie_arrival_path", "kiddie_arrival_end_guard",
			"kiddie_train", "east_swing_deck", "east_carousel_deck"]:
		if east.find_child(retired, true, false) != null:
			_fail("demolition geometry %s still survives in east_cascade" % retired)
	east.free()
	var program: Node = load("res://scenes/world/park_program.tscn").instantiate()
	for required in ["R5_outer_00", "R7_deck", "R13_rail_00",
			"R14_rail_00", "P1_lighthouse_tower", "P2_funhouse_back"]:
		if program.find_child(required, true, false) == null:
			_fail("the atlas program is missing %s" % required)
	program.free()
	var ground: Node = load("res://scenes/world/park_groundworks.tscn").instantiate()
	if ground.find_child("terrain_T6_outer_highland", true, false) == null:
		_fail("the expanded eastern highland reserve is not mounted")
	ground.free()


func _run(id: StringName) -> Array:
	for run in Plan.rebuild_route_runs():
		if run["id"] == id:
			return run["points"]
	_fail("missing plan route %s" % id)
	return []


func _xz(points: Array[Vector3]) -> Array:
	var out := []
	for point in points:
		out.append(Vector2(point.x, point.z))
	return out


func _expect_near(label: String, a: Vector2, b: Vector2) -> void:
	if a.distance_to(b) > EPS:
		_fail("%s misses by %.2fm" % [label, a.distance_to(b)])


func _nearest_on_run(point: Vector2, points: Array) -> Dictionary:
	if points.size() < 2:
		return {"distance": INF, "at": point, "tangent": Vector2.RIGHT}
	var best := {"distance": INF, "at": point, "tangent": Vector2.RIGHT}
	for i in points.size() - 1:
		var a: Vector2 = points[i]
		var b: Vector2 = points[i + 1]
		var q := _nearest_on_segment(point, a, b)
		var d := point.distance_to(q)
		if d < best["distance"]:
			best = {"distance": d, "at": q, "tangent": (b - a).normalized()}
	return best


func _nearest_between_runs(a: Array, b: Array) -> Dictionary:
	var best := {"distance": INF, "at": Vector2.ZERO}
	for i in a.size() - 1:
		for j in b.size() - 1:
			var hit = Geometry2D.segment_intersects_segment(a[i], a[i + 1], b[j], b[j + 1])
			if hit != null:
				return {"distance": 0.0, "at": hit}
			for pair in [[a[i], b[j], b[j + 1]], [a[i + 1], b[j], b[j + 1]],
					[b[j], a[i], a[i + 1]], [b[j + 1], a[i], a[i + 1]]]:
				var q := _nearest_on_segment(pair[0], pair[1], pair[2])
				var d: float = pair[0].distance_to(q)
				if d < best["distance"]:
					best = {"distance": d, "at": (pair[0] + q) * 0.5}
	return best


func _nearest_on_segment(point: Vector2, a: Vector2, b: Vector2) -> Vector2:
	var ab := b - a
	var t := clampf((point - a).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
	return a + ab * t


func _crossing_angle(a: Vector2, b: Vector2) -> float:
	return rad_to_deg(acos(clampf(absf(a.dot(b)), 0.0, 1.0)))


func _point_rect_distance(point: Vector2, lo: Vector2, hi: Vector2) -> float:
	var dx := maxf(maxf(lo.x - point.x, 0.0), point.x - hi.x)
	var dy := maxf(maxf(lo.y - point.y, 0.0), point.y - hi.y)
	return Vector2(dx, dy).length()


func _point_ellipse_distance(point: Vector2, centre: Vector2, radii: Vector2) -> float:
	var normalized := Vector2((point.x - centre.x) / radii.x,
		(point.y - centre.y) / radii.y)
	if normalized.length_squared() < 1.0:
		return 0.0
	var best := INF
	for i in 720:
		var a := TAU * float(i) / 720.0
		var edge := centre + Vector2(cos(a) * radii.x, sin(a) * radii.y)
		best = minf(best, point.distance_to(edge))
	return best


func _fail(message: String) -> void:
	_fails.append(message)
	printerr("FAIL: ", message)


func _finish() -> void:
	if _fails.is_empty():
		print("\n  expanded footprint, protected monuments, arrival, and crossings agree")
		get_tree().quit()
	else:
		printerr("\n  %d footprint checks failed" % _fails.size())
		get_tree().quit(1)
