extends SceneTree

## Proves that the approved editor curve, rather than copied coordinates,
## controls both the localized terrain ribbon and the generated walk.

const Controls = preload("res://scripts/park_vertical_controls_source.gd")
const Regrade = preload("res://scripts/lighthouse_regrade_source.gd")
const Plan = preload("res://scripts/park_plan.gd")

const EPSILON := 0.002
var _failures := PackedStringArray()


func _initialize() -> void:
	var source := Controls.instantiate()
	var regrade := Regrade.new(source)
	_check_cross_section(regrade)
	_check_path(regrade)
	var generator = load("res://tools/gen_props.gd").new()
	_check_generator_terrain(generator, regrade)
	generator.free()
	_check_editor_ownership(source, regrade)
	source.free()
	if not _failures.is_empty():
		for failure in _failures:
			push_error(failure)
		print("LIGHTHOUSE REGRADE FAIL: %d issue(s)" % _failures.size())
		quit(1)
		return
	print("LIGHTHOUSE REGRADE PASS: approved curve drives localized terrain and paving")
	quit()


func _check_cross_section(regrade: RefCounted) -> void:
	var standing := 17.25
	var minimum_edge_shore := INF
	for point in regrade.path_points(2.0):
		var centre := Vector2(point.x, point.z)
		var profile: Dictionary = regrade.profile_at(centre)
		_check_float("terrain bed at %s" % centre,
			regrade.terrain_y(centre, standing),
			float(profile["centre_y"]) - regrade.bed_depth())
		var seaward: Vector2 = profile["seaward_direction"]
		var sea_edge: Vector2 = centre + seaward * regrade.seaward_outer_width()
		_check_join_outside(regrade, centre, seaward, standing)
		_check_join_outside(regrade, centre, -seaward, standing)
		minimum_edge_shore = minf(minimum_edge_shore, Plan.coast_inland(sea_edge))
	if minimum_edge_shore < 2.0:
		_failures.append("P1 terrain ribbon leaves only %.2fm to the shoreline" %
			minimum_edge_shore)
	var bounds: Rect2 = regrade.terrain_bounds()
	var remote := bounds.end + Vector2(4.0, 4.0)
	_check_float("terrain outside P1 bounds", regrade.terrain_y(remote, standing), standing)
	_check_float("fixed lighthouse table", regrade.terrain_y(
		Vector2(-205.0, -300.0), standing), standing)
	_check_float("fixed headland loop", regrade.terrain_y(
		Vector2(-37.0, -170.0), standing), standing)
	print("P1 TERRAIN RIBBON: %.2fm minimum shoreline gap; bounds %s" % [
		minimum_edge_shore, bounds])


func _check_join_outside(regrade: RefCounted, centre: Vector2,
		direction: Vector2, standing: float) -> void:
	# At a contour bend one cross-section can enter its neighbour before reaching
	# open ground. Walk outward until the nearest part of the complete ribbon has
	# ended, then prove that the standing terrain is returned exactly.
	for distance in range(6, 31):
		var candidate := centre + direction * float(distance)
		var profile: Dictionary = regrade.profile_at(candidate)
		if float(profile["distance"]) < float(profile["outer_width"]):
			continue
		_check_float("terrain ribbon outer join",
			regrade.terrain_y(candidate, standing), standing)
		return
	_failures.append("P1 terrain ribbon did not end within 30m of %s" % centre)


func _check_path(regrade: RefCounted) -> void:
	var points: Array[Vector3] = regrade.path_points(0.5)
	_check_position("P1 generated start", points[0], Vector3(-37.0, 4.0, -172.31))
	_check_position("P1 generated finish", points[-1], Vector3(-196.0, 31.1, -303.01))
	var maximum_grade := 0.0
	var maximum_spacing := 0.0
	for index in points.size() - 1:
		var a := points[index]
		var b := points[index + 1]
		var run := Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
		maximum_spacing = maxf(maximum_spacing, run)
		maximum_grade = maxf(maximum_grade, absf(b.y - a.y) / maxf(run, 0.001))
	if maximum_grade > 0.1255:
		_failures.append("P1 derived paving reaches %.2f%%" % (maximum_grade * 100.0))
	if maximum_spacing > 0.51:
		_failures.append("P1 derived paving spacing reaches %.3fm" % maximum_spacing)
	print("P1 DERIVED WALK: %d stations, %.2f%% max grade, %.3fm max spacing" % [
		points.size(), maximum_grade * 100.0, maximum_spacing])


func _check_generator_terrain(generator: Object, regrade: RefCounted) -> void:
	var points: Array[Vector3] = regrade.path_points(0.5)
	for index in [40, 180, 340, 500]:
		var point := points[index]
		var xz := Vector2(point.x, point.z)
		var method := "_rebuild_coastal_reserve_y" if xz.x < Plan.REBUILD_WORLD_LAND_FROM_X \
			else "_rebuild_world_reserve_y"
		var generated_y: float = generator.call(method, xz)
		_check_float("generator terrain follows P1 at station %d" % index,
			generated_y, point.y - regrade.bed_depth())


func _check_editor_ownership(source: Node3D, before: RefCounted) -> void:
	var p: Vector3 = before.path_points(1.0)[100]
	var probe := Vector2(p.x, p.z)
	var old_y: float = before.terrain_y(probe, 40.0)
	var control := source.get_node("approved_regrades/P1_lighthouse_walk")
	control.set_meta("terrain_bed_depth", before.bed_depth() + 0.2)
	var after := Regrade.new(source)
	_check_float("live editor cross-section read", after.terrain_y(probe, 40.0),
		old_y - 0.2)


func _check_position(label: String, actual: Vector3, expected: Vector3) -> void:
	if actual.distance_to(expected) > 0.011:
		_failures.append("%s is %s; expected %s" % [label, actual, expected])


func _check_float(label: String, actual: float, expected: float) -> void:
	if absf(actual - expected) > EPSILON:
		_failures.append("%s is %.4f; expected %.4f" % [label, actual, expected])
