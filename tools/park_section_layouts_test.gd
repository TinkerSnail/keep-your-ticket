extends SceneTree

## Guards the eight horizontal editor-source handoffs that complete the section
## atlas after Kiddieland. Initial parity proves they were promoted from the
## accepted ParkPlan rather than traced from the HTML review map. The live-read
## check proves construction observes editor transforms without regeneration of
## the source itself.

const Plan = preload("res://scripts/park_plan.gd")
const Source = preload("res://scripts/park_section_layout_source.gd")
const EPSILON := 0.001

var _failures := PackedStringArray()


func _initialize() -> void:
	for section_id in Source.SECTION_IDS:
		_check_scene(section_id)
	_check_group(&"primary_routes", Plan.REBUILD_PRIMARY_ROUTE_RUNS, [])
	_check_group(&"primary_connectors", Plan.REBUILD_PRIMARY_CONNECTORS, [])
	_check_group(&"district_routes", Plan.REBUILD_DISTRICT_ROUTE_RUNS,
		[&"d_arrival", &"d_family_loop", &"d_plaza_return", &"d_terrace_link"])
	_check_group(&"rides", Plan.REBUILD_RIDE_SITES,
		[&"R5", &"R6", &"R7", &"R14"])
	_check_group(&"attractions", Plan.REBUILD_ATTRACTION_SITES, [&"P4"])
	_check_group(&"interiors", Plan.REBUILD_INTERIOR_SITES, [])
	_check_group(&"midway", Plan.REBUILD_MIDWAY_UNITS, [&"K1", &"K2"])
	_check_group(&"services", Plan.REBUILD_SERVICE_SPINES, [])
	_check_water()
	_check_live_editor_read()
	_check_plan_consumers()
	if not _failures.is_empty():
		for failure in _failures:
			push_error(failure)
		print("PARK SECTION LAYOUTS FAIL: %d issue(s)" % _failures.size())
		quit(1)
		return
	print("PARK SECTION LAYOUTS PASS: Entrance, Plaza, Boardwalk, Fairground, High Terrace, Frontier, Grove and Headland")
	quit()


func _check_scene(section_id: StringName) -> void:
	var root := Source.instantiate(section_id)
	if root.editor_description.is_empty():
		_failures.append("%s has no editor handoff description" % section_id)
	if int(root.get_meta("layout_version", 0)) < 1:
		_failures.append("%s has no layout version" % section_id)
	root.free()


func _check_group(group_name: StringName, baseline: Array,
		excluded: Array[StringName]) -> void:
	var actual := Source.records(group_name)
	var expected_count := 0
	for record in baseline:
		var id := StringName(record["id"])
		if id in excluded:
			continue
		expected_count += 1
		var source := _find(actual, id)
		if source.is_empty():
			_failures.append("%s is missing %s" % [group_name, id])
			continue
		_compare_dictionary("%s/%s" % [group_name, id], source, record)
	if actual.size() != expected_count:
		_failures.append("%s has %d records; expected %d" % [
			group_name, actual.size(), expected_count])


func _check_water() -> void:
	var water := Source.find_record(&"water", &"CW-AQ")
	if water.is_empty():
		_failures.append("Fairground is missing Coastal Creek")
		return
	_compare_array("water/CW-AQ/points", water["points"],
		Plan.REBUILD_COASTAL_CREEK)


func _check_live_editor_read() -> void:
	var root := Source.instantiate(&"frontier")
	var queue := root.get_node("rides/R10/queue/p01") as Marker3D
	var before := Source._record(root.get_node("rides/R10"), root)["queue"][1] as Vector2
	queue.position += Vector3(0.75, 0.0, -0.5)
	var after := Source._record(root.get_node("rides/R10"), root)["queue"][1] as Vector2
	if after.distance_to(before + Vector2(0.75, -0.5)) > EPSILON:
		_failures.append("Frontier R10 queue does not follow its editor marker")
	var ride := root.get_node("rides/R10") as Node3D
	ride.position.x += 1.25
	var parent_moved := Source._record(ride, root)["queue"][1] as Vector2
	if parent_moved.distance_to(after + Vector2(1.25, 0.0)) > EPSILON:
		_failures.append("Frontier R10 queue does not follow its parent transform")
	root.free()


func _check_plan_consumers() -> void:
	_check_ids("primary consumer", Plan.rebuild_primary_route_sources(),
		Plan.REBUILD_PRIMARY_ROUTE_RUNS)
	_check_ids("district consumer", Plan.rebuild_district_route_sources(),
		Plan.REBUILD_DISTRICT_ROUTE_RUNS)
	_check_ids("ride consumer", Plan.rebuild_ride_sites(), Plan.REBUILD_RIDE_SITES)
	_check_ids("attraction consumer", Plan.rebuild_attraction_sites(),
		Plan.REBUILD_ATTRACTION_SITES)
	_compare_array("Coastal Creek consumer", Plan.rebuild_coastal_creek(),
		Plan.REBUILD_COASTAL_CREEK)


func _check_ids(label: String, actual: Array, expected: Array) -> void:
	if actual.size() != expected.size():
		_failures.append("%s has %d records; expected %d" % [
			label, actual.size(), expected.size()])
		return
	for i in expected.size():
		if StringName(actual[i]["id"]) != StringName(expected[i]["id"]):
			_failures.append("%s order differs at %d" % [label, i])


func _find(records: Array, id: StringName) -> Dictionary:
	for record in records:
		if StringName(record["id"]) == id:
			return record
	return {}


func _compare_dictionary(label: String, actual: Dictionary,
		expected: Dictionary) -> void:
	for key in expected:
		if not actual.has(key):
			_failures.append("%s is missing field %s" % [label, key])
			continue
		_compare_value("%s/%s" % [label, key], actual[key], expected[key])


func _compare_array(label: String, actual: Array, expected: Array) -> void:
	if actual.size() != expected.size():
		_failures.append("%s has %d values; expected %d" % [
			label, actual.size(), expected.size()])
		return
	for i in expected.size():
		_compare_value("%s/%d" % [label, i], actual[i], expected[i])


func _compare_value(label: String, actual: Variant, expected: Variant) -> void:
	if actual is Array and expected is Array:
		_compare_array(label, actual, expected)
	elif actual is Vector2 and expected is Vector2:
		if (actual as Vector2).distance_to(expected) > EPSILON:
			_failures.append("%s differs: %s / %s" % [label, actual, expected])
	elif actual is Vector3 and expected is Vector3:
		if (actual as Vector3).distance_to(expected) > EPSILON:
			_failures.append("%s differs: %s / %s" % [label, actual, expected])
	elif actual is float or expected is float:
		if absf(float(actual) - float(expected)) > EPSILON:
			_failures.append("%s differs: %s / %s" % [label, actual, expected])
	elif actual != expected:
		_failures.append("%s differs: %s / %s" % [label, actual, expected])
