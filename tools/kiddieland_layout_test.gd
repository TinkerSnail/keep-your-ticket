extends SceneTree

## Guards the first editor-ownership handoff for the rebuild atlas.
##
## The source scene begins as a lossless promotion of the current built
## ParkPlan records, not as a trace of the HTML map. The builder now consumes
## Route D, R5-R7, R14, P4 and its support sites from this source. While another pass keeps the
## generated world dirty, this test proves the migration without publishing a
## regenerated scene. These parity checks are migration history; spatial
## acceptance becomes the long-term guard after the first publication.

const Plan = preload("res://scripts/park_plan.gd")
const Source = preload("res://scripts/kiddieland_layout_source.gd")
const Generator = preload("res://tools/gen_props.gd")
const EPSILON := 0.001

var _failures: PackedStringArray = PackedStringArray()


func _initialize() -> void:
	var root := Source.instantiate()
	_check_required(root)
	_check_routes(root)
	_check_generator_routes(root)
	_check_rides(root)
	_check_r14(root)
	_check_p4(root)
	_check_support(root)
	_check_protection(root)
	_check_editor_ownership(root)
	root.free()
	if not _failures.is_empty():
		for failure in _failures:
			push_error(failure)
		print("KIDDIELAND LAYOUT SOURCE FAIL: %d issue(s)" % _failures.size())
		quit(1)
		return
	print("KIDDIELAND LAYOUT SOURCE PASS: Route D, R5-R7, R14, P4, support, S3, Q4 and NT-2")
	quit()


func _check_required(root: Node) -> void:
	for path in [
		"public_routes/d_arrival",
		"public_routes/d_family_loop",
		"public_routes/d_plaza_return",
		"public_routes/d_terrace_link",
		"rides/R5", "rides/R6", "rides/R7", "rides/R14/track",
		"rides/R14/station", "rides/R14/queue", "rides/R14/exit",
		"rides/R14/service", "rides/R14/manual_photo",
		"destinations/P4_play_garden", "destinations/P4_play_garden/access",
		"destinations/P4_play_garden/access/p00",
		"destinations/KG1_squirt_garden",
		"destinations/KC1_character_garden", "destinations/KC2_family_photo",
		"destinations/KC3_birthday_pavilion", "operations/S3",
		"protection/NT-2", "protection/Q4/standpoint",
		"protection/Q4/primary_target",
	]:
		if root.get_node_or_null(path) == null:
			_failures.append("missing source node %s" % path)


func _check_routes(root: Node) -> void:
	var source_runs := Source.route_runs(root)
	for id in [&"d_arrival", &"d_family_loop", &"d_plaza_return", &"d_terrace_link"]:
		var source := _plan_record(source_runs, id)
		var built := _plan_record(Plan.REBUILD_DISTRICT_ROUTE_RUNS, id)
		if built.is_empty():
			_failures.append("ParkPlan has no %s route" % id)
			continue
		_check_points("route %s" % id, source["points"], built["points"])
		_check_float("route %s width" % id, float(source["width"]), float(built["width"]))
		if bool(source["build"]) != bool(built.get("build", true)):
			_failures.append("route %s build ownership differs from ParkPlan" % id)
		if bool(source["closed"]) != bool(built.get("closed", false)):
			_failures.append("route %s closed state differs from ParkPlan" % id)


func _check_generator_routes(root: Node) -> void:
	var generator = Generator.new()
	var generated: Array = generator._rebuild_district_build_runs()
	for source in Source.route_runs(root):
		if not bool(source["build"]):
			continue
		var built := _plan_record(generated, source["id"])
		var expanded: Array = []
		for point in source["points"]:
			expanded.append(Plan.rebuild_expand_point(Vector2(point)))
		_check_points("generator route %s" % source["id"], built["points"], expanded)
	generator.free()


func _check_rides(root: Node) -> void:
	var source := Source.ride_sites(root)
	for id in [&"R5", &"R6", &"R7"]:
		var built := _plan_record(Plan.REBUILD_RIDE_SITES, id)
		if not source.has(id) or built.is_empty():
			_failures.append("missing %s ride source" % id)
			continue
		_check_point("%s centre" % id, source[id]["at"], built["at"])
		if built.has("radii"):
			_check_vec2("%s radii" % id, source[id]["radii"], built["radii"])
		else:
			_check_float("%s radius" % id, source[id]["radius"], built["radius"])


func _check_r14(root: Node) -> void:
	var source := Source.r14_site(root)
	var built := _plan_record(Plan.REBUILD_RIDE_SITES, &"R14")
	if built.is_empty():
		_failures.append("ParkPlan has no R14 ride")
		return
	_check_points("R14 track", source["track"], built["track"])
	_check_points("R14 queue", source["queue"], built["queue"])
	_check_point("R14 station", source["station"], built["station"])
	_check_vec2("R14 station size", source["station_size"], built["station_size"])
	var track: Array = source["track"]
	if track.size() < 2 or not track[0].is_equal_approx(track[track.size() - 1]):
		_failures.append("R14 track must remain closed")
	_check_float("R14 maximum lift", float(source["max_lift"]), 8.0)


func _check_p4(root: Node) -> void:
	var built := _plan_record(Plan.REBUILD_ATTRACTION_SITES, &"P4")
	if built.is_empty():
		_failures.append("ParkPlan has no P4 play garden")
		return
	var source := Source.p4_site(root)
	_check_point("P4 centre", source["at"], built["at"])
	_check_vec2("P4 radii", source["radii"], built["radii"])
	_check_points("P4 access", source["access"], built["access"])


func _check_support(root: Node) -> void:
	# These pin the editor source's initial 04G+ promotion. gen_props reads the
	# same records through Source.support_sites rather than copying them.
	var expected := {
		"destinations/KG1_squirt_garden": [Vector2(31, 94), Vector2(3.5, 2.5), &"radii"],
		"destinations/KC1_character_garden": [Vector2(43, 115), Vector2(7, 5), &"radii"],
		"destinations/KC2_family_photo": [Vector2(55, 118), Vector2(8, 5), &"size"],
		"destinations/KC3_birthday_pavilion": [Vector2(70, 119), Vector2(12, 6), &"size"],
	}
	var sites := Source.support_sites(root)
	for path in expected:
		var id := StringName(String(path).get_file().get_slice("_", 0))
		var node: Dictionary = sites[id]
		var record: Array = expected[path]
		_check_point(path, node["at"], record[0])
		_check_vec2("%s footprint" % path, node[String(record[2])], record[1])
	var s3 := _plan_record(Plan.REBUILD_SERVICE_SPINES, &"S3")
	_check_points("S3 context", _marker_points(root.get_node("operations/S3")),
		(s3["points"] as Array).slice(0, 5))


func _check_protection(root: Node) -> void:
	var nt2: Dictionary = Plan.REBUILD_PROTECTED_ZONES[&"NT-2"]
	var source := root.get_node("protection/NT-2")
	_check_point("NT-2 centre", _marker_point(source), nt2["centre"])
	_check_vec2("NT-2 radii", source.get_meta("radii"), nt2["radii"])
	_check_point("Q4 standpoint", _marker_point(root.get_node("protection/Q4/standpoint")), Vector2(49, 68))
	_check_point("Q4 target", _marker_point(root.get_node("protection/Q4/primary_target")), Vector2(86, 0))


## This is the ownership proof for generator integration: moving a saved source
## point or its parent is observed by the consumer immediately, without changing
## a ParkPlan constant or copying a coordinate into code.
func _check_editor_ownership(root: Node) -> void:
	var control := root.get_node("rides/R14/track/p03") as Marker3D
	var before: Vector2 = Source.r14_site(root)["track"][3]
	control.position.x += 0.75
	var after: Vector2 = Source.r14_site(root)["track"][3]
	_check_point("R14 live editor read", after, before + Vector2(0.75, 0.0))
	var ride := root.get_node("rides/R14") as Node3D
	ride.position.z -= 1.25
	var moved_with_parent: Vector2 = Source.r14_site(root)["track"][3]
	_check_point("R14 parent-transform read", moved_with_parent,
		before + Vector2(0.75, -1.25))


func _plan_record(records: Array, id: StringName) -> Dictionary:
	for record in records:
		if StringName(record["id"]) == id:
			return record
	return {}


func _marker_points(parent: Node) -> Array[Vector2]:
	var out: Array[Vector2] = []
	for child in parent.get_children():
		if child is Marker3D:
			out.append(Vector2(child.position.x, child.position.z))
	return out


func _marker_point(node: Node3D) -> Vector2:
	return Vector2(node.position.x, node.position.z)


func _check_points(label: String, actual: Array, expected: Array) -> void:
	if actual.size() != expected.size():
		_failures.append("%s has %d points; expected %d" % [label, actual.size(), expected.size()])
		return
	for i in actual.size():
		_check_point("%s point %d" % [label, i], actual[i], Vector2(expected[i]))


func _check_point(label: String, actual: Vector2, expected: Vector2) -> void:
	if actual.distance_to(expected) > EPSILON:
		_failures.append("%s is %s; expected %s" % [label, actual, expected])


func _check_vec2(label: String, actual: Variant, expected: Variant) -> void:
	_check_point(label, Vector2(actual), Vector2(expected))


func _check_float(label: String, actual: float, expected: float) -> void:
	if absf(actual - expected) > EPSILON:
		_failures.append("%s is %.3f; expected %.3f" % [label, actual, expected])
