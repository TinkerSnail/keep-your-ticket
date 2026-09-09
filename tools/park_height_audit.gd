extends SceneTree

## Read-only planning audit. It reports the vertical datums that the current
## accepted world assigns to the atlas controls; it writes no scene and is not
## a construction source. The HTML maps can then distinguish measured existing
## levels from proposed ones instead of silently inventing either.

const Plan = preload("res://scripts/park_plan.gd")
const LighthouseRegrade = preload("res://scripts/lighthouse_regrade_source.gd")


func _initialize() -> void:
	var generator_script = load("res://tools/gen_props.gd")
	var generator = generator_script.new()
	print("HEIGHT_AUDIT|datum|Plaza paving|0.00|existing")
	print("HEIGHT_AUDIT|datum|Boardwalk deck|%.2f|existing" % Plan.SHORE_TOP)
	print("HEIGHT_AUDIT|datum|East upper terrace|%.2f|protected" % Plan.TERRACE_TWO_Y)

	for run in Plan.REBUILD_PRIMARY_ROUTE_RUNS:
		_report_primary_run(run)
	for run in Plan.REBUILD_DISTRICT_ROUTE_RUNS:
		if not bool(run.get("build", false)):
			continue
		var graded: Array = generator.call("_rebuild_graded_route",
			Plan._rebuild_expand_plan_run(run))
		_report_control_heights(String(run["id"]), run["points"], graded)
		_report_max_grade(String(run["id"]), graded)

	var sites := [
		["P1 lighthouse forecourt", Vector2(-174.0, -202.5), &"headland"],
		["E2 keeper exhibit", Vector2(-160.7, -213.4), &"headland"],
		["P2 funhouse", Vector2(-77.0, 32.0), &"boardwalk"],
		["P3 Big Top", Vector2(-32.0, 92.0), &"coastal"],
		["I1 Food Hall", Vector2(-35.0, 68.0), &"fairground"],
		["P4 play garden", Vector2(27.0, 93.0), &"family"],
		["KS1 miniature railway station", Vector2(55.0, 88.0), &"family"],
		["KC1 character garden", Vector2(43.0, 115.0), &"family"],
		["KC2 family photo", Vector2(55.0, 118.0), &"family"],
		["KC3 birthday pavilion", Vector2(70.0, 119.0), &"family"],
		["R5 miniature railway", Vector2(68.0, 88.0), &"family"],
		["R6 spinning tubs", Vector2(95.0, 96.0), &"family"],
		["R7 carousel", Vector2(109.0, 62.0), &"family"],
		["R8 chair swing", Vector2(104.0, -66.0), &"highland"],
		["R9 water ride", Vector2(28.0, -84.0), &"north"],
		["R10 mine train", Vector2(80.0, -94.0), &"north"],
		["R11 observation tower", Vector2(111.0, -87.0), &"north"],
		["R12 west sky-ride threshold", Vector2(-18.0, -104.0), &"north"],
		["R13 steel coaster station", Vector2(135.0, -41.0), &"highland"],
		["R14 junior coaster station", Vector2(107.0, 111.0), &"family"],
	]
	for site in sites:
		var p: Vector3 = generator.call("_rebuild_site", site[1], site[2])
		print("HEIGHT_AUDIT|site|%s|%.2f|existing" % [site[0], p.y])
	var p1_regrade := LighthouseRegrade.new()
	_report_approved_access_grade("P1_public_access", p1_regrade.path_points(1.0))
	var drainage := [
		["D3 Fairground garden", Vector2(-18.0, 131.0)],
		["D4 Family garden", Vector2(88.0, 123.0)],
		["D5 East detention", Vector2(133.0, 112.0)],
		["D6 North detention", Vector2(45.0, -142.0)],
	]
	for basin in drainage:
		var world := Plan.rebuild_expand_point(basin[1])
		var ground: float = generator.call("_rebuild_landscape_floor", world)
		print("HEIGHT_AUDIT|drainage_ground|%s|%.2f|existing" % [basin[0], ground])
	var approved := [
		["D3_low", Vector2(-18.0, 131.0), -0.30],
		["D4_low", Vector2(88.0, 123.0), 2.93],
		["D5_low", Vector2(133.0, 112.0), 3.63],
		["D6_low", Vector2(45.0, -142.0), -0.50],
		["aquarium_floor", Vector2(-151.7, -213.4), 30.61],
		["cannery_floor", Vector2(-58.0, -143.0), -5.80],
	]
	for control in approved:
		var world := Plan.rebuild_expand_point(control[1])
		print("HEIGHT_AUDIT|approved_world|%s|(%.2f,%.2f,%.2f)|approved" % [
			control[0], world.x, float(control[2]), world.y])
	generator.free()
	quit()


func _report_primary_run(run: Dictionary) -> void:
	var points: Array = run["points"]
	var expanded: Array[Vector3] = []
	for index in points.size():
		var p := Vector3(points[index])
		print("HEIGHT_AUDIT|control|%s:%d|%.2f|existing" % [run["id"], index, p.y])
		expanded.append(Plan.rebuild_expand_position(p))
	_report_max_grade(String(run["id"]), expanded)


func _report_control_heights(id: String, controls: Array, graded: Array) -> void:
	for index in controls.size():
		var source := Vector2(controls[index])
		var world := Plan.rebuild_expand_point(source)
		var y := _polyline_height(graded, world)
		print("HEIGHT_AUDIT|control|%s:%d|%.2f|existing" % [id, index, y])


func _report_max_grade(id: String, points: Array) -> void:
	var maximum := 0.0
	var peak_from := Vector3.ZERO
	var peak_to := Vector3.ZERO
	for index in range(1, points.size()):
		var a := Vector3(points[index - 1])
		var b := Vector3(points[index])
		var horizontal := Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
		var grade := absf(b.y - a.y) / maxf(horizontal, 0.001)
		if grade > maximum:
			maximum = grade
			peak_from = a
			peak_to = b
	print("HEIGHT_AUDIT|grade|%s|%.2f|existing" % [id, maximum * 100.0])
	if id == "P1_public_access":
		print("HEIGHT_AUDIT|grade_peak|%s|(%.2f,%.2f,%.2f)->(%.2f,%.2f,%.2f)|existing" % [
			id, peak_from.x, peak_from.y, peak_from.z,
			peak_to.x, peak_to.y, peak_to.z])


func _report_approved_access_grade(id: String, points: Array[Vector3]) -> void:
	var horizontal := 0.0
	for index in range(1, points.size()):
		var a := points[index - 1]
		var b := points[index]
		horizontal += Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
	print("HEIGHT_AUDIT|access_run|%s|length=%.2f|rise=%.2f|average=%.2f%%|approved_unbuilt" % [
		id, horizontal, points[-1].y - points[0].y,
		(points[-1].y - points[0].y) / maxf(horizontal, 0.001) * 100.0])
	var maximum := 0.0
	for index in range(1, points.size()):
		var a := points[index - 1]
		var b := points[index]
		var run := Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
		maximum = maxf(maximum, absf(b.y - a.y) / maxf(run, 0.001))
	print("HEIGHT_AUDIT|grade|%s|%.2f|approved_unbuilt" % [id, maximum * 100.0])


func _report_access_grade(generator: Object, id: String, source: Array,
		zone: StringName, station: float) -> void:
	var world: Array[Vector2] = []
	for point in source:
		world.append(Plan.rebuild_expand_point(Vector2(point)))
	var samples: Array[Vector2] = []
	for index in world.size() - 1:
		if samples.is_empty():
			samples.append(world[index])
		var steps := maxi(1, ceili(world[index].distance_to(world[index + 1]) / station))
		for step in range(1, steps + 1):
			samples.append(world[index].lerp(world[index + 1], float(step) / float(steps)))
	var points: Array[Vector3] = []
	for sample in samples:
		points.append(generator.call("_rebuild_site_at", sample, zone))
	var horizontal := 0.0
	for index in range(1, points.size()):
		var a := points[index - 1]
		var b := points[index]
		horizontal += Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
	print("HEIGHT_AUDIT|access_run|%s|length=%.2f|rise=%.2f|average=%.2f%%|existing" % [
		id, horizontal, points[-1].y - points[0].y,
		(points[-1].y - points[0].y) / maxf(horizontal, 0.001) * 100.0])
	if id == "P1_public_access":
		_report_grade_violations(points, 0.125)
	_report_max_grade(id, points)
	if id == "P1_public_access" and OS.get_cmdline_user_args().has("p1_target"):
		_report_local_regrade(points, 0.125)


func _report_grade_violations(points: Array[Vector3], maximum: float) -> void:
	var count := 0
	var horizontal := 0.0
	var extra_run := 0.0
	var first := -1
	var last := -1
	for index in range(1, points.size()):
		var a := points[index - 1]
		var b := points[index]
		var d := Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
		var rise := absf(b.y - a.y)
		if rise / maxf(d, 0.001) > maximum + 0.00001:
			count += 1
			horizontal += d
			extra_run += rise / maximum - d
			if first < 0:
				first = index - 1
			last = index
	print("HEIGHT_AUDIT|grade_violations|P1_public_access|segments=%d|span=%d..%d|horizontal=%.2f|extra_run=%.2f|target=%.2f%%|existing" % [
		count, first, last, horizontal, extra_run, maximum * 100.0])


func _report_local_regrade(current: Array[Vector3], maximum: float) -> void:
	var target := current.duplicate()
	# Project the existing profile into the fixed-endpoint grade envelope.
	# Unconstrained samples remain untouched, which localizes the correction.
	for index in range(1, target.size()):
		var d := Vector2(target[index - 1].x, target[index - 1].z).distance_to(
			Vector2(target[index].x, target[index].z))
		target[index].y = minf(target[index].y, target[index - 1].y + maximum * d)
	target[-1].y = current[-1].y
	for index in range(target.size() - 2, -1, -1):
		var d := Vector2(target[index].x, target[index].z).distance_to(
			Vector2(target[index + 1].x, target[index + 1].z))
		target[index].y = maxf(target[index].y, target[index + 1].y - maximum * d)
	target[0].y = current[0].y
	for index in range(1, target.size()):
		var d := Vector2(target[index - 1].x, target[index - 1].z).distance_to(
			Vector2(target[index].x, target[index].z))
		target[index].y = minf(target[index].y, target[index - 1].y + maximum * d)
	var first := -1
	var last := -1
	for index in target.size():
		if absf(target[index].y - current[index].y) > 0.001:
			if first < 0:
				first = index
			last = index
	if first < 0:
		print("HEIGHT_AUDIT|target_profile|P1_public_access|no correction required")
		return
	first = maxi(0, first - 1)
	last = mini(target.size() - 1, last + 1)
	print("HEIGHT_AUDIT|target_profile|P1_public_access|controls=%d..%d|max=%.2f%%|approved" % [
		first, last, maximum * 100.0])
	for index in range(first, last + 1):
		print("HEIGHT_AUDIT|target_point|%02d|(%.3f,%.3f,%.3f)|was=%.3f|approved" % [
			index, target[index].x, target[index].y, target[index].z, current[index].y])
	_report_max_grade("P1_local_target", target)


func _polyline_height(points: Array, p: Vector2) -> float:
	var best := INF
	var y := 0.0
	for index in points.size() - 1:
		var a := Vector3(points[index])
		var b := Vector3(points[index + 1])
		var a2 := Vector2(a.x, a.z)
		var b2 := Vector2(b.x, b.z)
		var chord := b2 - a2
		var t := clampf((p - a2).dot(chord) / maxf(chord.length_squared(), 0.001), 0.0, 1.0)
		var distance := p.distance_to(a2 + chord * t)
		if distance < best:
			best = distance
			y = lerpf(a.y, b.y, t)
	return y
