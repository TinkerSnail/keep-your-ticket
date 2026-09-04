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
	_check_rim_clearance()
	_check_promontory()
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


## Package 02A: the range's toe line keeps `RIM_CLEARANCE` clear of every route
## edge, the Grand Circuit, both parking fields and every ride, interior,
## attraction and midway parcel. The toe line is `ParkPlan.range_toe_line`, the
## same line the generator raises the ground from.
func _check_rim_clearance() -> void:
	var toes: Array[Vector2] = Plan.range_toe_line(2.0)
	var worst := {}
	var nearest_toe := func(a: Vector2, b: Vector2) -> Vector2:
		var best := toes[0]
		var bd := INF
		for t in toes:
			var dd := t.distance_to(Geometry2D.get_closest_point_to_segment(t, a, b))
			if dd < bd:
				bd = dd
				best = t
		return best
	var note := func(kind: String, d: float, what: String) -> void:
		if not worst.has(kind) or d < worst[kind][0]:
			worst[kind] = [d, what]

	for run in Plan.rebuild_route_runs():
		var pts: Array = run["points"]
		var half := float(run["width"]) * 0.5
		var closed := bool(run.get("closed", false))
		var n := pts.size() if closed else pts.size() - 1
		for i in n:
			var a := _rim_xz(pts[i])
			var b := _rim_xz(pts[(i + 1) % pts.size()])
			note.call("route", _toes_to_segment(toes, a, b) - half,
				"%s, toe near %s" % [run["id"], nearest_toe.call(a, b)])
	var tram: Array = Plan.grand_tram_loop()
	for i in tram.size():
		var a := _rim_xz(tram[i])
		var b := _rim_xz(tram[(i + 1) % tram.size()])
		note.call("Grand Circuit", _toes_to_segment(toes, a, b)
			- Plan.GRAND_TRAM_LANE_W * 0.5,
			"circuit lane %s-%s, toe near %s" % [a, b, nearest_toe.call(a, b)])
	for side in [-1.0, 1.0]:
		var x0 := minf(side * Plan.PARKING_INNER_X, side * Plan.PARKING_OUTER_X)
		var x1 := maxf(side * Plan.PARKING_INNER_X, side * Plan.PARKING_OUTER_X)
		note.call("parking", _toes_to_rect(toes, x0, Plan.PARKING_FROM_Z, x1,
			Plan.PARKING_TO_Z), "parking field")
	for site in Plan.REBUILD_RIDE_SITES:
		var id := String(site["id"])
		if site.has("track"):
			var anchor: Vector2 = site.get("track_anchor", site["station"])
			var at := Plan.rebuild_expand_point(anchor)
			var track: Array = site["track"]
			for i in track.size() - 1:
				note.call("ride", _toes_to_segment(toes, at + (Vector2(track[i]) - anchor),
					at + (Vector2(track[i + 1]) - anchor)), id)
			var st := Plan.rebuild_expand_point(site["station"])
			var sz: Vector2 = site["station_size"]
			note.call("ride", _toes_to_rect(toes, st.x - sz.x * 0.5, st.y - sz.y * 0.5,
				st.x + sz.x * 0.5, st.y + sz.y * 0.5), id + " station")
		elif site.has("points"):
			var pts: Array = site["points"]
			var centre := Vector2.ZERO
			for q in pts:
				centre += Vector2(q)
			centre /= float(pts.size())
			var at := Plan.rebuild_expand_point(centre)
			for i in pts.size():
				note.call("ride", _toes_to_segment(toes, at + (Vector2(pts[i]) - centre),
					at + (Vector2(pts[(i + 1) % pts.size()]) - centre)), id)
		elif site.has("terminals"):
			for t in site["terminals"]:
				note.call("ride", _toes_to_point(toes, Plan.rebuild_expand_point(t)) - 6.0, id)
		else:
			var at := Plan.rebuild_expand_point(site["at"])
			var r := 0.0
			if site.has("radius"):
				r = float(site["radius"])
			elif site.has("radii"):
				r = maxf((site["radii"] as Vector2).x, (site["radii"] as Vector2).y)
			elif site.has("size"):
				r = maxf((site["size"] as Vector2).x, (site["size"] as Vector2).y) * 0.5
			note.call("ride", _toes_to_point(toes, at) - r, id)
	for site in Plan.REBUILD_ATTRACTION_SITES:
		var at := Plan.rebuild_expand_point(site["at"])
		var r := 8.0
		if site.has("radius"):
			r = float(site["radius"])
		elif site.has("radii"):
			r = maxf((site["radii"] as Vector2).x, (site["radii"] as Vector2).y)
		elif site.has("size"):
			r = maxf((site["size"] as Vector2).x, (site["size"] as Vector2).y) * 0.5
		note.call("attraction", _toes_to_point(toes, at) - r, String(site["id"]))
	for site in Plan.REBUILD_INTERIOR_SITES:
		var at := Plan.rebuild_expand_point(site["at"])
		var sz: Vector2 = site["size"]
		note.call("interior", _toes_to_rect(toes, at.x - sz.x * 0.5, at.y - sz.y * 0.5,
			at.x + sz.x * 0.5, at.y + sz.y * 0.5), String(site["id"]))
	for site in Plan.REBUILD_MIDWAY_UNITS:
		var at := Plan.rebuild_expand_point(site["at"])
		note.call("midway", _toes_to_rect(toes, at.x - 2.5, at.y - 2.5, at.x + 2.5,
			at.y + 2.5), String(site["id"]))

	print("  range toe line: %d points about (%.0f, %.0f), inner %.0fm" % [
		toes.size(), Plan.RIM_RANGE_CENTRE.x, Plan.RIM_RANGE_CENTRE.y,
		Plan.RIM_RANGE_INNER_R + Plan.RIM_RANGE_TOE_D])
	for kind in worst:
		var d: float = worst[kind][0]
		print("  rim toe to nearest %s: %.1fm (%s)" % [kind, d, worst[kind][1]])
		if d < Plan.RIM_CLEARANCE - EPS:
			_fail("rim toe leaves only %.1fm to %s %s, rule is %.0fm" % [
				d, kind, worst[kind][1], Plan.RIM_CLEARANCE])


## The promontory walk, the P1 forecourt and the keeper's exhibit stand on the
## land, not on its edge: every walk station, the forecourt's rim and the
## exhibit's corners keep `PROMONTORY_SHORE_CLEARANCE` inland of the coast
## outline, and the spine itself does the same up to its tip. Written after
## the first walk was laid along the cove-side shoreline to within a metre,
## which nothing measured and one frame from the walk showed.
func _check_promontory() -> void:
	var clearance: float = Plan.PROMONTORY_SHORE_CLEARANCE
	var site := {}
	for record in Plan.REBUILD_ATTRACTION_SITES:
		if StringName(record["id"]) == &"P1":
			site = record
	if site.is_empty():
		_fail("the atlas program has no P1")
		return
	# A dictionary rather than two locals: a lambda captures a local by value,
	# so a minimum kept in one never leaves the lambda. The first run printed
	# INF and found nothing.
	var nearest := {"d": INF, "what": ""}
	var note := func(inland: float, what: String) -> void:
		if inland < float(nearest["d"]):
			nearest["d"] = inland
			nearest["what"] = what
	var spine: Array = Plan.PROMONTORY_SPINE
	for i in spine.size() - 1:
		note.call(Plan.coast_inland(spine[i]), "spine vertex %d at %s" % [i, spine[i]])
	var access: Array = site["access"]
	for i in access.size():
		var p := Plan.rebuild_expand_point(Vector2(access[i]))
		note.call(Plan.coast_inland(p), "walk station %d at %s" % [i, p])
		if i > 0:
			var q := Plan.rebuild_expand_point(Vector2(access[i - 1]))
			var steps := maxi(1, ceili(p.distance_to(q) / 4.0))
			for step in range(1, steps):
				var m := q.lerp(p, float(step) / float(steps))
				note.call(Plan.coast_inland(m), "walk between stations %d and %d at %s" % [i - 1, i, m])
	var tower := Plan.rebuild_expand_point(site["at"])
	note.call(Plan.coast_inland(tower) - 7.0, "P1 forecourt rim at %s" % tower)
	var keeper := Plan.rebuild_expand_point(site["keeper"])
	var half: Vector2 = (site["keeper_size"] as Vector2) * 0.5
	for corner in [Vector2(-half.x, -half.y), Vector2(half.x, -half.y),
			Vector2(half.x, half.y), Vector2(-half.x, half.y)]:
		note.call(Plan.coast_inland(keeper + corner), "keeper's exhibit corner at %s" % (keeper + corner))
	var worst := float(nearest["d"])
	var worst_what := String(nearest["what"])
	print("promontory: nearest approach to the shoreline %.1fm, %s" % [worst, worst_what])
	if not is_finite(worst):
		_fail("the promontory check measured nothing")
	elif worst < clearance:
		_fail("the promontory parcel stands %.1fm from the shoreline at %s, under the %.1fm clearance" % [
			worst, worst_what, clearance])
	# And the walk climbs: the tower's ground stands above the pad, so the
	# walk is a climb and not a chord over a dip.
	var tower_y: float = Plan.promontory_y(tower)
	if tower_y < Plan.PROMONTORY_ROOT_Y + 8.0:
		_fail("the promontory under P1 is only %.1fm high" % tower_y)


func _rim_xz(v: Variant) -> Vector2:
	if v is Vector3:
		return Vector2((v as Vector3).x, (v as Vector3).z)
	return v as Vector2


func _toes_to_segment(toes: Array[Vector2], a: Vector2, b: Vector2) -> float:
	var best := INF
	for t in toes:
		best = minf(best, t.distance_to(Geometry2D.get_closest_point_to_segment(t, a, b)))
	return best


func _toes_to_point(toes: Array[Vector2], q: Vector2) -> float:
	var best := INF
	for t in toes:
		best = minf(best, t.distance_to(q))
	return best


func _toes_to_rect(toes: Array[Vector2], x0: float, z0: float, x1: float,
		z1: float) -> float:
	var best := INF
	for t in toes:
		var dx := maxf(maxf(x0 - t.x, 0.0), t.x - x1)
		var dz := maxf(maxf(z0 - t.y, 0.0), t.y - z1)
		best = minf(best, Vector2(dx, dz).length())
	return best


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
	# The coast meshes are the ground beyond the working strip (2026-09-04):
	# the north one has to reach the world's north coast bound, the south one
	# the point where the bay's far shore crosses onto the mainland reserve.
	var south_to_z := minf(Plan.REBUILD_WORLD_COAST_TO_Z,
		Plan.coast_south_crossing_z(Plan.SHORE_FROM_X))
	for pair in [["north", Plan.REBUILD_WORLD_COAST_FROM_Z], ["south", south_to_z]]:
		var coast := ground.find_child("terrain_world_coast_%s" % pair[0], true, false)
		if coast == null:
			_fail("the %s coastal reserve is not mounted" % pair[0])
			continue
		var coast_surface := coast.find_child("surface", false, false) as MeshInstance3D
		if coast_surface == null or coast_surface.mesh == null:
			_fail("the %s coastal reserve has no surface mesh" % pair[0])
			continue
		var coast_bounds := coast_surface.mesh.get_aabb()
		var reach: float = coast_bounds.position.z if pair[0] == "north" else coast_bounds.end.z
		if absf(reach - float(pair[1])) > 1.0:
			_fail("the %s coast mesh ends at z %.1f, expected %.1f" % [
				pair[0], reach, float(pair[1])])
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
	# The bay's water lies under the whole of the far shore: from the ocean's
	# east edge to past the outline's eastmost point, and from north of the
	# crossing to the world's south coast bound.
	var bay := west.find_child("water_bay", true, false) as CSGBox3D
	if bay == null:
		_fail("the bay water sheet is missing")
	else:
		var bay_lo := bay.position - bay.size * 0.5
		var bay_hi := bay.position + bay.size * 0.5
		var far: Vector2 = Plan.COAST_SOUTH_OUTLINE[Plan.COAST_SOUTH_OUTLINE.size() - 1]
		var crossing := Plan.coast_south_crossing_z(Plan.REBUILD_WORLD_WATER_TO_X)
		if bay_lo.x > Plan.REBUILD_WORLD_WATER_TO_X + EPS or bay_hi.x < far.x - EPS \
				or bay_lo.z > crossing - 30.0 \
				or bay_hi.z < Plan.REBUILD_WORLD_COAST_TO_Z - EPS:
			_fail("the bay water does not lie under the whole of the far shore")
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
