extends SceneTree

## Guards the approved map-to-editor handoff without generating terrain.

const Source = preload("res://scripts/park_vertical_controls_source.gd")
const Drainage = preload("res://scripts/park_drainage_terrain_source.gd")
const Plan = preload("res://scripts/park_plan.gd")
const Generator = preload("res://tools/gen_props.gd")
const EPSILON := 0.011

var _failures: PackedStringArray = PackedStringArray()


func _initialize() -> void:
	assert(Generator != null, "terrain generator did not compile")
	var root := Source.instantiate()
	_check_levels(root)
	_check_terrain_shapes(root)
	_check_drainage_derivation(root)
	_check_generator_derivation(root)
	_check_lighthouse(root)
	_check_editor_ownership(root)
	root.free()
	if not _failures.is_empty():
		for failure in _failures:
			push_error(failure)
		print("PARK VERTICAL CONTROLS FAIL: %d issue(s)" % _failures.size())
		quit(1)
		return
	print("PARK VERTICAL CONTROLS PASS: fifty map levels, four authored terrain rims and localized P1 regrade")
	quit()


func _check_levels(root: Node3D) -> void:
	# Source x/z and literal y are the synchronized map's verticalPlans facts.
	# The scene stores their expanded world x/z so it is directly useful in the
	# editor; this test owns the coordinate-space conversion check.
	var expected := [
		[&"entrance_gate", 0.0, 123.0, 0.0, &"entrance", &"measured", &"GATE"],
		[&"entrance_j1", 0.0, 86.0, 0.0, &"entrance", &"measured", &"J1"],
		[&"plaza_j2", 0.0, 0.0, 0.0, &"plaza", &"measured", &"J2"],
		[&"nt1_top", -58.0, -2.0, 0.0, &"plaza", &"protected", &"NT-1 TOP"],
		[&"nt1_low", -72.0, -2.0, -6.0, &"plaza", &"protected", &"NT-1 LOW"],
		[&"nt2_low", 46.0, 0.0, 0.0, &"plaza,high_terrace", &"protected", &"NT-2 LOW"],
		[&"nt2_upper", 74.0, 48.0, 12.0, &"plaza,high_terrace", &"protected", &"NT-2 UPPER"],
		[&"boardwalk_deck", -96.0, -2.0, -6.0, &"boardwalk", &"protected", &"B DECK"],
		[&"boardwalk_n_crest", -6.0, -68.0, 0.0, &"boardwalk", &"measured", &"N CREST"],
		[&"boardwalk_s_crest", -48.0, 78.0, 0.0, &"boardwalk", &"measured", &"S CREST"],
		[&"pier_deck", -130.0, 6.0, -6.0, &"boardwalk", &"protected", &"PIER"],
		[&"boardwalk_water", -146.0, 40.0, -7.5, &"boardwalk", &"protected", &"WATER"],
		[&"fairground_j6", -48.0, 78.0, 0.0, &"fairground", &"measured", &"J6"],
		[&"fairground_c_low", -72.0, 76.0, -1.74, &"fairground", &"measured", &"C LOW"],
		[&"p3_floor", -32.0, 92.0, 0.0, &"fairground", &"measured", &"P3 FFL"],
		[&"i1_floor", -35.0, 68.0, 0.0, &"fairground", &"measured", &"I1 FFL"],
		[&"D3_low", -18.0, 131.0, -0.3, &"fairground", &"approved", &"D3 LOW"],
		[&"kiddieland_j7", 49.0, 68.0, 0.0, &"kiddieland", &"measured", &"J7"],
		[&"ks1_floor", 55.0, 88.0, 0.0, &"kiddieland", &"measured", &"KS1 FFL"],
		[&"r5_rail", 68.0, 88.0, 0.14, &"kiddieland", &"measured", &"R5 RAIL"],
		[&"r6_pad", 95.0, 96.0, 5.73, &"kiddieland", &"measured", &"R6 PAD"],
		[&"r7_pad", 109.0, 62.0, 5.05, &"kiddieland", &"measured", &"R7 PAD"],
		[&"r14_floor", 107.0, 111.0, 5.28, &"kiddieland", &"measured", &"R14 FFL"],
		[&"kc1_floor", 43.0, 115.0, 0.0, &"kiddieland", &"measured", &"KC1 FFL"],
		[&"kc2_floor", 55.0, 118.0, 0.49, &"kiddieland", &"measured", &"KC2 FFL"],
		[&"kc3_floor", 70.0, 119.0, 1.74, &"kiddieland", &"measured", &"KC3 FFL"],
		[&"D4_low", 88.0, 123.0, 2.93, &"kiddieland", &"approved", &"D4 LOW"],
		[&"D5_low", 133.0, 112.0, 3.63, &"kiddieland", &"approved", &"D5 LOW"],
		[&"high_terrace_j9", 94.0, -58.0, 14.72, &"high_terrace", &"measured", &"J9"],
		[&"r8_pad", 104.0, -66.0, 14.72, &"high_terrace", &"measured", &"R8 PAD"],
		[&"r13_floor", 135.0, -41.0, 19.1, &"high_terrace", &"measured", &"R13 FFL"],
		[&"f_high", 118.0, -42.0, 20.66, &"high_terrace", &"measured", &"F HIGH"],
		[&"frontier_f_west", 58.0, -70.0, 9.41, &"frontier", &"measured", &"F WEST"],
		[&"r10_pad", 80.0, -94.0, 11.14, &"frontier", &"measured", &"R10 PAD"],
		[&"r12_east", 112.0, -106.0, 12.46, &"frontier", &"measured", &"R12 EAST"],
		[&"r11_pad", 111.0, -87.0, 14.34, &"frontier", &"measured", &"R11 PAD"],
		[&"frontier_f_east", 120.0, -86.0, 14.75, &"frontier", &"measured", &"F EAST"],
		[&"grove_j3", -6.0, -68.0, 0.0, &"grove", &"measured", &"J3"],
		[&"grove_f1", 4.0, -82.0, 1.5, &"grove", &"measured", &"F1"],
		[&"r9_pad", 28.0, -84.0, 2.55, &"grove", &"measured", &"R9 PAD"],
		[&"grove_f2", 40.0, -113.0, 6.05, &"grove", &"measured", &"F2"],
		[&"r12_west", -18.0, -104.0, 3.02, &"grove", &"measured", &"R12 WEST"],
		[&"D6_low", 45.0, -142.0, -0.5, &"grove", &"approved", &"D6 LOW"],
		[&"headland_a_loop", -37.0, -125.0, 4.0, &"headland", &"measured", &"A LOOP"],
		[&"p1_floor", -174.0, -202.5, 31.1, &"headland", &"measured", &"P1 FFL"],
		[&"e2_floor", -160.7, -213.4, 30.61, &"headland", &"measured", &"E2 FFL"],
		[&"aquarium_floor", -151.7, -213.4, 30.61, &"headland", &"approved", &"AQ FFL"],
		[&"working_quay", -83.0, -146.7, -5.8, &"headland", &"measured", &"QUAY"],
		[&"cannery_floor", -58.0, -143.0, -5.8, &"headland", &"approved", &"CANNERY FFL"],
		[&"headland_water", -145.0, -155.0, -7.5, &"headland", &"protected", &"WATER"],
	]
	var levels := Source.approved_levels(root)
	for item in expected:
		var id: StringName = item[0]
		if not levels.has(id):
			_failures.append("missing approved level %s" % id)
			continue
		var source := Vector2(float(item[1]), float(item[2]))
		var world := Plan.rebuild_expand_point(source)
		_check_position(String(id), levels[id]["position"],
			Vector3(world.x, float(item[3]), world.y))
		if levels[id]["district"] != item[4]:
			_failures.append("%s has district %s; expected %s" % [id, levels[id]["district"], item[4]])
		if levels[id]["status"] != item[5]:
			_failures.append("%s has status %s; expected %s" % [id, levels[id]["status"], item[5]])
		if levels[id]["map_id"] != item[6]:
			_failures.append("%s has map id %s; expected %s" % [id, levels[id]["map_id"], item[6]])
	if levels.size() != expected.size():
		_failures.append("source has %d map levels; expected %d" % [
			levels.size(), expected.size()])
	if levels[&"D4_low"]["protection"] != &"independent_from_NT-2":
		_failures.append("D4 must remain independent from NT-2")
	if levels[&"D5_low"]["protection"] != &"independent_from_NT-2":
		_failures.append("D5 must remain independent from NT-2")
	if levels[&"aquarium_floor"]["relationship"] != &"match_keeper_court":
		_failures.append("aquarium floor must match the keeper court")
	if levels[&"cannery_floor"]["relationship"] != &"match_working_quay":
		_failures.append("cannery floor must match the working quay")


func _check_terrain_shapes(root: Node3D) -> void:
	var basins := Source.drainage_basins(root)
	var drops := {
		&"D3_basin": 0.30,
		&"D4_basin": 0.50,
		&"D5_basin": 0.50,
		&"D6_basin": 0.50,
	}
	if basins.size() != drops.size():
		_failures.append("source has %d drainage shapes; expected %d" % [basins.size(), drops.size()])
	for id in drops:
		if not basins.has(id):
			_failures.append("missing authored terrain shape %s" % id)
			continue
		var basin: Dictionary = basins[id]
		if basin["status"] != &"approved_source_unpublished":
			_failures.append("%s has unexpected status %s" % [id, basin["status"]])
		if basin["shape_source"] != &"authored_in_godot_not_traced_from_svg":
			_failures.append("%s is not marked as an authored Godot shape" % id)
		var rim: Array[Vector3] = basin["rim"]
		if rim.size() < 6:
			_failures.append("%s has only %d rim controls" % [id, rim.size()])
			continue
		var low: Vector3 = basin["low"]
		var rim_y := rim[0].y
		_check_float("%s depth" % id, rim_y - low.y, float(drops[id]))
		for point in rim:
			_check_float("%s level rim" % id, point.y, rim_y)
			if Vector2(point.x, point.z).distance_to(Vector2(low.x, low.z)) < 5.0:
				_failures.append("%s rim closes within 5m of its low at %s" % [id, point])
	for id in [&"D4_basin", &"D5_basin"]:
		if basins[id]["protection"] != &"independent_from_NT-2":
			_failures.append("%s must remain independent from NT-2" % id)
	for required in ["route_D", "ride_pads", "NT-2", "Q4"]:
		if not String(basins[&"D4_basin"]["hold_fixed"]).split(",").has(required):
			_failures.append("D4 does not hold %s fixed" % required)
	for required in ["route_D", "ride_pads", "S3", "NT-2", "Q4"]:
		if not String(basins[&"D5_basin"]["hold_fixed"]).split(",").has(required):
			_failures.append("D5 does not hold %s fixed" % required)


func _check_drainage_derivation(root: Node3D) -> void:
	var terrain = Drainage.new(root)
	var basins := Source.drainage_basins(root)
	if terrain.basin_ids().size() != 4:
		_failures.append("drainage terrain reader did not load four basins")
	for id in basins:
		var basin: Dictionary = basins[id]
		var low3: Vector3 = basin["low"]
		var low := Vector2(low3.x, low3.z)
		_check_float("%s derived low" % id,
			terrain.terrain_y(low, 99.0, [id]), low3.y)
		var controls := terrain.control_points(id)
		var rim: Array[Vector3] = basin["rim"]
		if controls.size() != rim.size() + 1:
			_failures.append("%s construction controls lost a saved marker" % id)
		for rim3 in rim:
			_check_float("%s derived rim" % id,
				terrain.terrain_y(Vector2(rim3.x, rim3.z), 99.0, [id]), rim3.y)
		var rim0: Vector3 = basin["rim"][0]
		var outward := (Vector2(rim0.x, rim0.z) - low).normalized()
		var far := Vector2(rim0.x, rim0.z) + outward \
			* (Drainage.OUTER_JOIN_RUN + 0.1)
		_check_float("%s exterior join" % id,
			terrain.terrain_y(far, 7.25, [id]), 7.25)
		_check_float("%s supporting offset" % id,
			terrain.terrain_y(low, 99.0, [id], -0.12), low3.y - 0.12)


func _check_generator_derivation(root: Node3D) -> void:
	# Call the four actual mesh-height seams without starting the generator or
	# saving a scene. This catches a compiled but unwired editor source.
	var generator = Generator.new()
	generator._kiddie_rail = Plan.kiddie_rail_loop()
	var levels := Source.approved_levels(root)
	var d3: Vector3 = levels[&"D3_low"]["position"]
	var d4: Vector3 = levels[&"D4_low"]["position"]
	var d5: Vector3 = levels[&"D5_low"]["position"]
	var d6: Vector3 = levels[&"D6_low"]["position"]
	_check_float("D3 lowland publication seam",
		generator._rebuild_lowland_surface_y(Vector2(d3.x, d3.z)), d3.y)
	_check_float("D4 shoulder publication seam",
		generator._shoulder_y(d4.x, d4.z, 1.0,
			generator._shoulder_prm(1.0)), d4.y)
	_check_float("D5 outer-highland publication seam",
		generator._rebuild_outer_highland_y(d5.x, d5.z), d5.y)
	_check_float("D6 lowland publication seam",
		generator._rebuild_lowland_surface_y(Vector2(d6.x, d6.z)), d6.y)
	generator.free()


func _check_lighthouse(root: Node3D) -> void:
	var regrade := Source.lighthouse_regrade(root)
	var target := root.get_node_or_null(
		"approved_regrades/P1_lighthouse_walk/target_path_curve") as Path3D
	if target == null or target.curve == null:
		_failures.append("P1 has no editor-owned target path curve")
	else:
		_check_lighthouse_curve(root, target, regrade)
	_check_float("P1 target grade", regrade["target_max_grade"], 0.125)
	_check_float("P1 measured grade", regrade["current_max_grade"], 0.2195)
	_check_float("P1 current length", regrade["current_length"], 241.58)
	_check_float("P1 violation span", regrade["violation_span"], 118.13)
	_check_float("P1 minimum extra run", regrade["minimum_extra_run"], 62.99)
	if regrade["ownership"] != &"localized_climb_corridor":
		_failures.append("P1 correction ownership is not localized")
	if regrade["curve_status"] != &"approved_editor_curve":
		_failures.append("P1 curve is not the approved editor source")
	if regrade["path_status"] != &"approved_source":
		_failures.append("P1 Path3D is not marked as an approved source")
	for required in ["headland_loop", "lighthouse_table", "path_endpoints",
			"shoreline", "headland_silhouette", "NT-1", "NT-2"]:
		if not String(regrade["hold_fixed"]).split(",").has(required):
			_failures.append("P1 correction does not hold %s fixed" % required)
	var a: Vector3 = regrade["peak_from"]
	var b: Vector3 = regrade["peak_to"]
	var horizontal := Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
	if absf(absf(b.y - a.y) / horizontal - 0.2195) > 0.0002:
		_failures.append("P1 displayed peak segment no longer reconstructs the 21.95%% audit")


func _check_lighthouse_curve(root: Node3D, path: Path3D, regrade: Dictionary) -> void:
	var curve := path.curve
	if curve.point_count != 21:
		_failures.append("P1 target curve has %d controls; expected 21" % curve.point_count)
		return
	var controls := Source.lighthouse_curve_points(root)
	_check_position("P1 target start", controls[0], Vector3(-37.0, 4.0, -172.31))
	_check_position("P1 target finish", controls[-1], Vector3(-196.0, 31.10, -303.01))
	var transform := Source.lighthouse_curve_transform(root)
	var baked_length := curve.get_baked_length()
	var samples: Array[Vector3] = []
	for index in ceili(baked_length) + 1:
		samples.append(transform * curve.sample_baked(minf(float(index), baked_length), true))
	if samples[-1].distance_to(transform * curve.sample_baked(baked_length, true)) > 0.001:
		samples.append(transform * curve.sample_baked(baked_length, true))
	var horizontal_length := 0.0
	var maximum_grade := 0.0
	var minimum_shore_clearance := INF
	var maximum_spine_offset := 0.0
	var peak_grade_at := Vector3.ZERO
	var minimum_shore_at := Vector3.ZERO
	for index in samples.size():
		var p := Vector2(samples[index].x, samples[index].z)
		var shore_clearance := Plan.coast_inland(p)
		if shore_clearance < minimum_shore_clearance:
			minimum_shore_clearance = shore_clearance
			minimum_shore_at = samples[index]
		maximum_spine_offset = maxf(maximum_spine_offset, Plan.promontory_station(p).y)
		if index == 0:
			continue
		var a := samples[index - 1]
		var b := samples[index]
		var run := Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
		horizontal_length += run
		var grade := absf(b.y - a.y) / maxf(run, 0.001)
		if grade > maximum_grade:
			maximum_grade = grade
			peak_grade_at = b
	if maximum_grade > float(regrade["target_max_grade"]) + 0.0005:
		_failures.append("P1 target curve reaches %.2f%%; maximum is 12.5%%" % [
			maximum_grade * 100.0])
	var required_run := float(regrade["current_length"]) + float(regrade["minimum_extra_run"])
	if horizontal_length + 1.0 < required_run:
		_failures.append("P1 target curve has %.2fm horizontal run; review target is %.2fm" % [
			horizontal_length, required_run])
	if minimum_shore_clearance < 8.0:
		_failures.append("P1 target curve comes within %.2fm of shore; minimum is 8m" %
			minimum_shore_clearance)
	if maximum_spine_offset > 20.0:
		_failures.append("P1 target curve leaves the 20m central climb corridor at %.2fm" %
			maximum_spine_offset)
	print("P1 TARGET CURVE: %.2fm horizontal, %.2f%% max, %.2fm shore, %.2fm corridor" % [
		horizontal_length, maximum_grade * 100.0, minimum_shore_clearance,
		maximum_spine_offset])
	print("P1 TARGET LIMITS: peak at %s; nearest shore at %s" % [
		peak_grade_at, minimum_shore_at])


func _check_editor_ownership(root: Node3D) -> void:
	var marker := root.get_node("approved_levels/D3_low") as Marker3D
	var before: Vector3 = Source.approved_levels(root)[&"D3_low"]["position"]
	marker.position.y -= 0.2
	var after: Vector3 = Source.approved_levels(root)[&"D3_low"]["position"]
	_check_position("live D3 editor read", after, before + Vector3(0, -0.2, 0))
	var group := root.get_node("approved_levels") as Node3D
	group.position.x += 0.4
	var moved: Vector3 = Source.approved_levels(root)[&"D3_low"]["position"]
	_check_position("vertical-control parent transform", moved,
		before + Vector3(0.4, -0.2, 0))
	var rim_control := root.get_node("approved_terrain_shapes/D4_basin/rim_02") as Marker3D
	var rim_before: Vector3 = Source.drainage_basins(root)[&"D4_basin"]["rim"][2]
	rim_control.position.z += 0.6
	var rim_after: Vector3 = Source.drainage_basins(root)[&"D4_basin"]["rim"][2]
	_check_position("live D4 rim read", rim_after, rim_before + Vector3(0, 0, 0.6))
	var basin_group := root.get_node("approved_terrain_shapes/D4_basin") as Node3D
	basin_group.position.x += 0.3
	var moved_rim: Vector3 = Source.drainage_basins(root)[&"D4_basin"]["rim"][2]
	_check_position("D4 basin parent transform", moved_rim,
		rim_before + Vector3(0.3, 0, 0.6))
	var moved_terrain = Drainage.new(root)
	_check_float("derived terrain follows moved D3 low",
		moved_terrain.terrain_y(Vector2(moved.x, moved.z), 99.0,
			[&"D3_basin"]), moved.y)
	_check_float("derived terrain follows moved D4 rim",
		moved_terrain.terrain_y(Vector2(moved_rim.x, moved_rim.z), 99.0,
			[&"D4_basin"]), moved_rim.y)
	var target := root.get_node(
		"approved_regrades/P1_lighthouse_walk/target_path_curve") as Path3D
	var curve_before: Vector3 = Source.lighthouse_curve_points(root)[1]
	target.curve.set_point_position(1, target.curve.get_point_position(1) + Vector3(0.25, 0, 0))
	var curve_after: Vector3 = Source.lighthouse_curve_points(root)[1]
	_check_position("live P1 curve editor read", curve_after,
		curve_before + Vector3(0.25, 0, 0))
	target.position.z += 0.3
	var moved_curve: Vector3 = Source.lighthouse_curve_points(root)[1]
	_check_position("P1 curve parent transform", moved_curve,
		curve_before + Vector3(0.25, 0, 0.3))


func _check_position(label: String, actual: Vector3, expected: Vector3) -> void:
	if actual.distance_to(expected) > EPSILON:
		_failures.append("%s is %s; expected %s" % [label, actual, expected])


func _check_float(label: String, actual: float, expected: float) -> void:
	if absf(actual - expected) > 0.0001:
		_failures.append("%s is %.4f; expected %.4f" % [label, actual, expected])
