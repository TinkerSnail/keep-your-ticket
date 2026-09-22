extends Node

## Focused acceptance for the open-air north Boardwalk and its two separate
## midway ride courts. This intentionally loads only the Boardwalk wrapper so unrelated
## far-world work cannot disguise a local parse or scene-tree failure.

const Plan := preload("res://scripts/park_plan.gd")
const EXPECTED_EXTENSION: Array[Vector2] = [
	Vector2(-99, -78), Vector2(-107, -92), Vector2(-108, -112),
	Vector2(-108, -136), Vector2(-106, -158), Vector2(-102, -176),
	Vector2(-98, -188), Vector2(-96, -198), Vector2(-92, -205),
	Vector2(-80, -205),
]
const SCRAMBLER_CENTER := Vector2(-86, -164)
const SCRAMBLER_RADIUS := 7.2
const DODGEMS_CENTER := Vector2(-84, -184)
const DODGEMS_HALF := Vector2(7, 5)
const QUAY_CENTER := Vector2(-83, -146.7)
const QUAY_HALF := Vector2(3, 5)
const MIN_PUBLIC_OVERHEAD_CLEARANCE := 4.0
const TRACK_STRUCTURE_DEPTH := 0.91
const TRACK_HALF_WIDTH := 1.125
const MAX_ROUTE_GRADE := 1.0 / 12.0
const ROUTE_HALF_WIDTH := 4.0
const SERVICE_HALF_WIDTH := 2.0
const MIN_SERVICE_EDGE_GAP := 1.0
const MIN_RIDE_EDGE_GAP := 0.5
const PLAZA_NORTH_WALL_Z := -52.0
const MIN_PLAZA_WALL_GAP := 1.0
const PAVILION_HALF := Vector2(2.6, 2.9)
const PAVILION_CENTERS: Array[Vector2] = [
	Vector2(-99, -95), Vector2(-53, -120),
]

var _fails: Array[String] = []


func _ready() -> void:
	var boardwalk: Node = load("res://scenes/world/boardwalk.tscn").instantiate()
	add_child(boardwalk)
	for i in 5:
		await get_tree().process_frame

	var extension: Node = boardwalk.get_node_or_null("authored_additions/boardwalk_north_ride_park")
	_expect(extension != null, "north ride park is mounted under the stable Boardwalk wrapper")
	if extension == null:
		_report()
		return

	var course := extension.get_node_or_null("public_ride_loop") as Path3D
	_expect(course != null and course.curve != null, "editor-owned public Boardwalk extension exists")
	if course != null and course.curve != null:
		_expect(not course.curve.closed, "the waterfront extension stays open instead of doubling back through R2")
		_expect(course.curve.point_count == EXPECTED_EXTENSION.size(), "public extension keeps all 10 authored controls")
		for i in mini(course.curve.point_count, EXPECTED_EXTENSION.size()):
			var p := course.curve.get_point_position(i)
			_expect(Vector2(p.x, p.z).distance_to(EXPECTED_EXTENSION[i]) < 0.01,
				"public extension control %02d matches the approved map" % i)
		_expect(float(course.get_meta("width", 0.0)) == 8.0, "public extension holds its 8m operating width")

	var derived: Node = extension.get_node_or_null("derived_deck")
	_expect(derived != null and derived.get_node_or_null("wearing_surface") != null,
		"the editable extension derives one continuous wearing surface")
	_expect(derived != null and derived.get_node_or_null("walking_surface") != null,
		"the route surface derives collision")
	var apron_sources := extension.get_node_or_null("public_aprons")
	var derived_aprons := extension.get_node_or_null("derived_aprons")
	_expect(apron_sources != null and apron_sources.get_child_count() == 2,
		"R15 and R16 each have a separate editor-owned timber forecourt")
	_expect(derived_aprons != null \
		and derived_aprons.get_node_or_null("R15_public_apron_wearing_surface") != null \
		and derived_aprons.get_node_or_null("R16_public_apron_wearing_surface") != null,
		"both ride forecourts derive visible planks")
	_expect(derived_aprons != null \
		and derived_aprons.get_node_or_null("R15_public_apron_walking_surface") != null \
		and derived_aprons.get_node_or_null("R16_public_apron_walking_surface") != null,
		"both ride forecourts derive collision")
	if derived_aprons != null:
		var expected_bounds := {
			"R15_public_apron": AABB(Vector3(-104, -5.963, -172), Vector3(10, 0.002, 16)),
			"R16_public_apron": AABB(Vector3(-101, -5.963, -196), Vector3(10, 0.002, 24)),
		}
		for apron_name in expected_bounds:
			var surface_node := derived_aprons.get_node_or_null(
				"%s_wearing_surface" % apron_name) as MeshInstance3D
			if surface_node != null and surface_node.mesh != null:
				var bounds := surface_node.mesh.get_aabb()
				var expected: AABB = expected_bounds[apron_name]
				_expect(absf(bounds.position.x - expected.position.x) < 0.01 \
					and absf(bounds.position.z - expected.position.z) < 0.01 \
					and absf(bounds.size.x - expected.size.x) < 0.01 \
					and absf(bounds.size.z - expected.size.z) < 0.01,
					"%s derived planks cover their complete authored forecourt" % apron_name)
				_expect(_mesh_uses_clockwise_top_faces(surface_node.mesh),
					"%s planks face upward in Godot's clockwise renderer" % apron_name)
		var r15_bounds: AABB = (derived_aprons.get_node(
			"R15_public_apron_wearing_surface") as MeshInstance3D).mesh.get_aabb()
		var r16_bounds: AABB = (derived_aprons.get_node(
			"R16_public_apron_wearing_surface") as MeshInstance3D).mesh.get_aabb()
		_expect(absf(r15_bounds.position.z - (r16_bounds.position.z + r16_bounds.size.z)) < 0.01,
			"the R15 and R16 timber courts meet without a landscape gap")
	if apron_sources != null:
		var apron_generator = load("res://tools/gen_props.gd").new()
		for child in apron_sources.get_children():
			var apron := child as Path3D
			if apron == null or apron.curve == null or apron.curve.point_count < 2:
				continue
			var a := apron.curve.get_point_position(0)
			var b := apron.curve.get_point_position(apron.curve.point_count - 1)
			var midpoint := (a + b) * 0.5
			var terrain_y: float = apron_generator.call("_rebuild_coastal_reserve_y",
				Vector2(midpoint.x, midpoint.z))
			_expect(terrain_y <= -6.12,
				"%s has a hidden ground bed below its visible timber surface (%.2fm)" % [
					apron.name, terrain_y])
		apron_generator.free()

	var scrambler: Node = extension.get_node_or_null("rides/R15_scrambler")
	var dodgems: Node = extension.get_node_or_null("rides/R16_dodgems")
	_expect(scrambler != null and scrambler.get_meta("map_id", &"") == &"R15",
		"R15 Scrambler is mounted as a named ride")
	_expect(dodgems != null and dodgems.get_meta("map_id", &"") == &"R16",
		"R16 dodgems are mounted as a named ride")
	if scrambler != null:
		var scrambler_3d := scrambler as Node3D
		_expect(Vector2(scrambler_3d.global_position.x, scrambler_3d.global_position.z).distance_to(SCRAMBLER_CENTER) < 0.01,
			"R15 stands in its separate north-midway court")
		_expect(StringName(scrambler.get_meta("ride_court", &"")) == &"north_midway",
			"R15 is no longer described as nested beneath R2")
		var machine: Node = scrambler.get_node_or_null("derived_machine")
		_expect(machine != null and machine.get_child_count() == 19,
			"Scrambler derives six arms, twelve cars and one hub")
	if dodgems != null:
		var dodgems_3d := dodgems as Node3D
		_expect(Vector2(dodgems_3d.global_position.x, dodgems_3d.global_position.z).distance_to(DODGEMS_CENTER) < 0.01,
			"R16 stands in its separate north-midway court")
		_expect(StringName(dodgems.get_meta("ride_court", &"")) == &"north_midway",
			"R16 is no longer described as nested beneath R2")
		_expect(dodgems.get_node_or_null("roof") != null, "dodgems supply enclosed weather refuge")
		_expect(dodgems.get_node_or_null("sign") != null, "dodgems have a public-facing identity")
		var bed_depth := float(dodgems.get_meta("terrain_bed_depth", 0.0))
		var court_margin := float(dodgems.get_meta("terrain_court_margin", 0.0))
		var terrain_ease := float(dodgems.get_meta("terrain_ease", 0.0))
		var public_direction := Vector2(dodgems.get_meta("terrain_public_direction", Vector2.ZERO))
		var public_apron := float(dodgems.get_meta("terrain_public_apron", 0.0))
		_expect(bed_depth >= 0.12, "R16 publishes a hidden terrain bed below its floor")
		_expect(court_margin >= 1.0, "R16's flat terrain court extends beyond its shell")
		_expect(terrain_ease >= 8.0, "R16's terrain court eases broadly into the coastal shelf")
		_expect(public_direction.distance_to(Vector2.LEFT) < 0.01,
			"R16's public terrain apron faces the waterfront Boardwalk")
		_expect(public_apron >= 5.0, "R16's public court reaches toward the waterfront deck")
		var generator = load("res://tools/gen_props.gd").new()
		for probe in [
			DODGEMS_CENTER,
			DODGEMS_CENTER + Vector2(-DODGEMS_HALF.x, -DODGEMS_HALF.y),
			DODGEMS_CENTER + Vector2(DODGEMS_HALF.x, DODGEMS_HALF.y),
		]:
			var terrain_y: float = generator.call("_rebuild_coastal_reserve_y", probe)
			_expect(terrain_y <= dodgems_3d.global_position.y - bed_depth + 0.01,
				"R16 terrain stays below the editor-owned court at %s (%.2fm)" % [probe, terrain_y])
		generator.free()

	var coaster_scene: Node = boardwalk.get_node_or_null("authored_additions/boardwalk_wooden_coaster")
	var coaster_course: Path3D = coaster_scene.get_node_or_null("course") as Path3D if coaster_scene != null else null
	_expect(coaster_course != null and coaster_course.curve != null, "R2 canonical course is available for parcel and flyover proof")
	if coaster_course != null and coaster_course.curve != null:
		var track := _curve_points_xz(coaster_course.curve)
		var bounds := _polyline_bounds(track)
		_expect(bounds.size.x >= 55.0 and bounds.size.y >= 85.0,
			"R2 uses a genuinely larger parcel (%.1f × %.1fm)" % [bounds.size.x, bounds.size.y])
		var scrambler_gap := _distance_to_polyline(SCRAMBLER_CENTER, track) - SCRAMBLER_RADIUS
		_expect(scrambler_gap >= 4.5, "R15 keeps at least 4.5m from the R2 track centerline (%.2fm)" % scrambler_gap)
		var dodgems_gap := _rect_to_polyline_gap(DODGEMS_CENTER, DODGEMS_HALF, track)
		_expect(dodgems_gap >= 3.0, "R16 keeps at least 3m from the R2 track centerline (%.2fm)" % dodgems_gap)
		var north_run := _build_run(&"b_north_return")
		_expect(not north_run.is_empty(), "the editor-owned B north return reaches the clearance proof")
		if not north_run.is_empty():
			var route_points: Array = north_run["points"]
			var route_xz: Array[Vector2] = []
			for point in route_points:
				var p: Vector3 = point
				route_xz.append(Vector2(p.x, p.z))
			var track_gap := _polyline_distance(route_xz, track) \
				- ROUTE_HALF_WIDTH - TRACK_HALF_WIDTH
			_expect(track_gap >= 1.0,
				"the land-side return stays completely outside R2 (%.2fm edge gap)" % track_gap)
			_expect(_maximum_grade(route_points) <= MAX_ROUTE_GRADE + 0.001,
				"the expanded station bypass keeps every sloped chord at or below 1:12")
			var source_run := _source_run(&"b_north_return")
			var source_wall_gap := INF
			if not source_run.is_empty():
				for point in source_run["points"]:
					var p: Vector3 = point
					source_wall_gap = minf(source_wall_gap,
						PLAZA_NORTH_WALL_Z - p.z - ROUTE_HALF_WIDTH)
			_expect(source_wall_gap >= MIN_PLAZA_WALL_GAP,
				"the bypass stays north of the plaza wall by a full route envelope (%.2fm)" % source_wall_gap)
			var s1 := _service_source(&"S1")
			var s1_points: Array[Vector2] = []
			if not s1.is_empty():
				for point in s1["points"]:
					s1_points.append(Plan.rebuild_expand_point(Vector2(point)))
			var service_gap := _polyline_distance(route_xz, s1_points) \
				- ROUTE_HALF_WIDTH - SERVICE_HALF_WIDTH
			_expect(service_gap >= MIN_SERVICE_EDGE_GAP,
				"the land-side return walks around S1 instead of beneath it (%.2fm edge gap)" % service_gap)
			var scrambler_service_gap := _distance_to_polyline(SCRAMBLER_CENTER,
				s1_points) - SCRAMBLER_RADIUS - SERVICE_HALF_WIDTH
			_expect(scrambler_service_gap >= MIN_SERVICE_EDGE_GAP,
				"R15's court remains outside S1 (%.2fm edge gap)" % scrambler_service_gap)
			var dodgems_service_gap := _rect_to_polyline_gap(
				DODGEMS_CENTER, DODGEMS_HALF, s1_points) - SERVICE_HALF_WIDTH
			_expect(dodgems_service_gap >= MIN_SERVICE_EDGE_GAP,
				"R16's court remains outside S1 (%.2fm edge gap)" % dodgems_service_gap)
			var ride_gap := _distance_to_polyline(SCRAMBLER_CENTER, route_xz) \
				- SCRAMBLER_RADIUS - ROUTE_HALF_WIDTH
			_expect(ride_gap >= MIN_RIDE_EDGE_GAP,
				"the through-route stays outside R15's operating envelope (%.2fm edge gap)" % ride_gap)
			var dodgems_route_gap := _rect_to_polyline_gap(
				DODGEMS_CENTER, DODGEMS_HALF, route_xz) - ROUTE_HALF_WIDTH
			_expect(dodgems_route_gap >= MIN_RIDE_EDGE_GAP,
				"the through-route stays outside R16's operating envelope (%.2fm edge gap)" % dodgems_route_gap)
			if course != null and course.curve != null:
				var extension_points: Array = []
				for i in course.curve.point_count:
					extension_points.append(course.curve.get_point_position(i))
				_expect(Vector2(Vector3(route_points[-1]).x, Vector3(route_points[-1]).z).distance_to(
					Vector2(Vector3(extension_points[-1]).x, Vector3(extension_points[-1]).z)) < 0.5,
					"the land-side return meets the timber Boardwalk without a dead end")
				var minimum := _minimum_overhead_clearance(coaster_course.curve,
					extension_points, float(course.get_meta("width", 0.0)))
				_expect(minimum < INF and minimum >= MIN_PUBLIC_OVERHEAD_CLEARANCE,
					"R2's single waterfront flyover leaves at least %.2fm beneath fixed structure (%.2fm)" % [
						MIN_PUBLIC_OVERHEAD_CLEARANCE, minimum])
				var extension_xz: Array[Vector2] = []
				for point in extension_points:
					var p: Vector3 = point
					extension_xz.append(Vector2(p.x, p.z))
				var extension_scrambler_gap := _distance_to_polyline(SCRAMBLER_CENTER,
					extension_xz) - SCRAMBLER_RADIUS - ROUTE_HALF_WIDTH
				_expect(extension_scrambler_gap >= MIN_RIDE_EDGE_GAP,
					"R15 has a distinct frontage outside the Boardwalk envelope (%.2fm)" % extension_scrambler_gap)
				var extension_dodgems_gap := _rect_to_polyline_gap(DODGEMS_CENTER,
					DODGEMS_HALF, extension_xz) - ROUTE_HALF_WIDTH
				_expect(extension_dodgems_gap >= MIN_RIDE_EDGE_GAP,
					"R16 has a distinct frontage outside the Boardwalk envelope (%.2fm)" % extension_dodgems_gap)
		var construction := coaster_scene.get_node_or_null("derived_construction")
		var catch_count := 0
		if construction != null:
			for child in construction.get_children():
				if String(child.name).begins_with("public_catch_"):
					catch_count += 1
		_expect(catch_count >= 1, "the single waterfront flyover derives visible catch protection")
		_expect(float(coaster_scene.get_meta("public_overhead_clearance_metres", 0.0)) == MIN_PUBLIC_OVERHEAD_CLEARANCE,
			"R2 publishes the public overhead-clearance contract")
		_expect(StringName(coaster_scene.get_meta("falling_object_control", &"")) == &"catch_net",
			"R2 publishes its falling-object control")
		_expect(coaster_scene.get_node_or_null("public_overhead_crossings").get_child_count() == 1,
			"R2 has one intentional public flyover, not a tunnel sequence")
		var pavilions := extension.get_node_or_null("under_coaster_pavilions")
		_expect(pavilions != null and pavilions.get_child_count() == PAVILION_CENTERS.size(),
			"two visible midway uses occupy the open R2 support field")
		if pavilions != null:
			var directly_overhead := 0
			for i in mini(pavilions.get_child_count(), PAVILION_CENTERS.size()):
				var pavilion := pavilions.get_child(i) as Node3D
				var center := Vector2(pavilion.global_position.x, pavilion.global_position.z)
				_expect(center.distance_to(PAVILION_CENTERS[i]) < 0.01,
					"midway pavilion %d keeps its authored support-field placement" % i)
				_expect(StringName(pavilion.get_meta("falling_object_control", &"")) == &"solid_roof",
					"midway pavilion %d provides a solid falling-object roof" % i)
				_expect(float(pavilion.get_meta("minimum_fixed_clearance_metres", 0.0)) \
					>= MIN_PUBLIC_OVERHEAD_CLEARANCE,
					"midway pavilion %d publishes the 4m fixed-clearance contract" % i)
				var route_gap := _rect_to_polyline_gap(center, PAVILION_HALF, EXPECTED_EXTENSION) \
					- ROUTE_HALF_WIDTH
				_expect(route_gap >= MIN_RIDE_EDGE_GAP,
					"midway pavilion %d stays outside the through-route (%.2fm edge gap)" % [i, route_gap])
				var roof_y := pavilion.global_position.y \
					+ float(pavilion.get_meta("roof_top_local_y", 0.0))
				var roof_clearance := _minimum_roof_clearance(
					coaster_course.curve, center, PAVILION_HALF, roof_y)
				if roof_clearance < INF:
					directly_overhead += 1
					_expect(roof_clearance >= MIN_PUBLIC_OVERHEAD_CLEARANCE,
						"midway pavilion %d keeps at least 4m below fixed track structure (%.2fm)" % [
							i, roof_clearance])
			_expect(directly_overhead >= 1,
				"at least one roofed midway use stands directly beneath a safely high R2 span")
		var high_bays := coaster_scene.get_node_or_null("occupied_high_bays")
		_expect(high_bays != null and high_bays.get_child_count() == 1,
			"the directly occupied R2 span has an editor-owned clear-bay control")

	var chain: Node3D = boardwalk.get_node_or_null("north_chain") as Node3D
	_expect(chain != null and not chain.visible and not bool(chain.get("use_collision")),
		"the old premature north chain is retired visibly and physically")
	var sign: Node3D = boardwalk.get_node_or_null("north_sign") as Node3D
	_expect(sign != null and not sign.visible, "the obsolete END OF BOARDWALK sign is retired")

	var quay_gap := _rect_to_polyline_gap(QUAY_CENTER, QUAY_HALF, EXPECTED_EXTENSION)
	_expect(quay_gap >= 3.0, "the route leaves the existing harbour quay clear (%.2fm)" % quay_gap)

	_report()


func _mesh_uses_clockwise_top_faces(mesh: Mesh) -> bool:
	var faces := mesh.get_faces()
	if faces.size() < 3:
		return false
	for i in range(0, faces.size(), 3):
		if (faces[i + 1] - faces[i]).cross(faces[i + 2] - faces[i]).y >= -0.99:
			return false
	return true


func _curve_points_xz(curve: Curve3D) -> Array[Vector2]:
	var points: Array[Vector2] = []
	for p in curve.get_baked_points():
		points.append(Vector2(p.x, p.z))
	if curve.closed and not points.is_empty() and points[-1].distance_to(points[0]) > 0.01:
		points.append(points[0])
	return points


func _minimum_roof_clearance(curve: Curve3D, center: Vector2,
		half: Vector2, roof_y: float) -> float:
	var minimum := INF
	var length := curve.get_baked_length()
	var count := maxi(1, ceili(length / 0.10))
	for i in count + 1:
		var track_point := curve.sample_baked(length * float(i) / float(count), true)
		if absf(track_point.x - center.x) > half.x + TRACK_HALF_WIDTH \
				or absf(track_point.z - center.y) > half.y + TRACK_HALF_WIDTH:
			continue
		minimum = minf(minimum, track_point.y - roof_y - TRACK_STRUCTURE_DEPTH)
	return minimum


func _polyline_bounds(points: Array[Vector2]) -> Rect2:
	var minimum := points[0]
	var maximum := points[0]
	for point in points:
		minimum.x = minf(minimum.x, point.x)
		minimum.y = minf(minimum.y, point.y)
		maximum.x = maxf(maximum.x, point.x)
		maximum.y = maxf(maximum.y, point.y)
	return Rect2(minimum, maximum - minimum)


func _distance_to_polyline(point: Vector2, line: Array[Vector2]) -> float:
	var best := INF
	for i in line.size() - 1:
		best = minf(best, Geometry2D.get_closest_point_to_segment(point, line[i], line[i + 1]).distance_to(point))
	return best


func _rect_to_polyline_gap(center: Vector2, half: Vector2, line: Array[Vector2]) -> float:
	var best := INF
	for step in 101:
		var t := float(step) / 100.0
		for p in [
			center + Vector2(-half.x + half.x * 2.0 * t, -half.y),
			center + Vector2(-half.x + half.x * 2.0 * t, half.y),
			center + Vector2(-half.x, -half.y + half.y * 2.0 * t),
			center + Vector2(half.x, -half.y + half.y * 2.0 * t),
		]:
			best = minf(best, _distance_to_polyline(p, line))
	return best


func _build_run(id: StringName) -> Dictionary:
	for run in Plan.rebuild_build_runs():
		if StringName(run["id"]) == id:
			return run
	return {}


func _source_run(id: StringName) -> Dictionary:
	for run in Plan.rebuild_primary_route_sources():
		if StringName(run["id"]) == id:
			return run
	return {}


func _service_source(id: StringName) -> Dictionary:
	for spine in Plan.rebuild_service_spines():
		if StringName(spine["id"]) == id:
			return spine
	return {}


func _polyline_distance(a: Array[Vector2], b: Array[Vector2]) -> float:
	var best := INF
	if a.size() < 2 or b.size() < 2:
		return best
	for i in a.size() - 1:
		for j in b.size() - 1:
			if Geometry2D.segment_intersects_segment(a[i], a[i + 1], b[j], b[j + 1]) != null:
				return 0.0
			var endpoint_gap := minf(
				minf(Geometry2D.get_closest_point_to_segment(a[i], b[j], b[j + 1]).distance_to(a[i]),
					Geometry2D.get_closest_point_to_segment(a[i + 1], b[j], b[j + 1]).distance_to(a[i + 1])),
				minf(Geometry2D.get_closest_point_to_segment(b[j], a[i], a[i + 1]).distance_to(b[j]),
					Geometry2D.get_closest_point_to_segment(b[j + 1], a[i], a[i + 1]).distance_to(b[j + 1])))
			best = minf(best, endpoint_gap)
	return best


func _minimum_overhead_clearance(curve: Curve3D, route: Array,
		route_width: float) -> float:
	var minimum := INF
	var length := curve.get_baked_length()
	var count := maxi(1, ceili(length / 0.10))
	for i in count + 1:
		var track_point := curve.sample_baked(length * float(i) / float(count), true)
		var nearest := _nearest_route_point(track_point, route)
		if float(nearest["distance"]) > route_width * 0.5 + TRACK_HALF_WIDTH:
			continue
		minimum = minf(minimum,
			track_point.y - float(nearest["height"]) - TRACK_STRUCTURE_DEPTH)
	return minimum


func _nearest_route_point(point: Vector3, route: Array) -> Dictionary:
	var p := Vector2(point.x, point.z)
	var best_distance := INF
	var best_height := 0.0
	for i in route.size() - 1:
		var a: Vector3 = route[i]
		var b: Vector3 = route[i + 1]
		var a2 := Vector2(a.x, a.z)
		var b2 := Vector2(b.x, b.z)
		var nearest := Geometry2D.get_closest_point_to_segment(p, a2, b2)
		var distance := p.distance_to(nearest)
		if distance >= best_distance:
			continue
		var denominator := a2.distance_squared_to(b2)
		var t := 0.0 if denominator < 0.0001 else clampf(
			(nearest - a2).dot(b2 - a2) / denominator, 0.0, 1.0)
		best_distance = distance
		best_height = lerpf(a.y, b.y, t)
	return {"distance": best_distance, "height": best_height}


func _maximum_grade(route: Array) -> float:
	var maximum := 0.0
	for i in route.size() - 1:
		var a: Vector3 = route[i]
		var b: Vector3 = route[i + 1]
		var horizontal := Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
		if horizontal > 0.001:
			maximum = maxf(maximum, absf(b.y - a.y) / horizontal)
	return maximum


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_fails.append(message)


func _report() -> void:
	if _fails.is_empty():
		print("PASS: the Boardwalk stays open-air around an expanded R2, with separate R15/R16 courts and one protected flyover")
		get_tree().quit()
		return
	print("FAIL: %d north Boardwalk ride-park checks" % _fails.size())
	for failure in _fails:
		print("  - %s" % failure)
	get_tree().quit(1)
