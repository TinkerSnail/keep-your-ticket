extends Node

## Focused R2 acceptance: the directly editable course remains inside its map
## parcel, derives a complete timber/track assembly, and fully retires the old
## single-line greybox without moving the established station foundation.

const Plan := preload("res://scripts/park_plan.gd")
const PARCEL := Rect2(-92.0, -129.0, 39.0, 76.0)


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run.call_deferred()


func _run() -> void:
	for _i in 10:
		await get_tree().process_frame
	var world := get_tree().root.find_child("boardwalk", true, false)
	if world == null:
		_fail("Boardwalk is not mounted")
		return
	var coaster := world.get_node_or_null("authored_additions/boardwalk_wooden_coaster")
	if coaster == null:
		_fail("editor-owned R2 coaster is not mounted")
		return
	var course := coaster.get_node("course") as Path3D
	if course.get_meta("ownership", "") != "editor":
		_fail("course ownership is no longer editor")
		return
	if course.curve == null or not course.curve.closed or course.curve.point_count < 20:
		_fail("course is not a closed, resolved circuit")
		return

	var crown := -INF
	for index in course.curve.point_count:
		var point := course.curve.get_point_position(index)
		crown = maxf(crown, point.y)
		if not PARCEL.has_point(Vector2(point.x, point.z)):
			_fail("course point %d left the approved R2 parcel: %s" % [index, point])
			return
	if crown < 20.0 or crown > 22.0:
		_fail("lift crown %.2fm is outside the accepted 20–22m silhouette" % crown)
		return

	var foundation := coaster.get_node("station_collision/foundation") as CollisionShape3D
	var shape := foundation.shape as BoxShape3D
	if shape == null or shape.size != Vector3(11.0, 1.1, 12.0) \
			or foundation.position != Vector3(-86.0, -5.45, -59.0):
		_fail("established station foundation moved")
		return
	for index in 4:
		if coaster.get_node_or_null("station_train/car_%d_body" % index) == null:
			_fail("parked train is missing car %d" % index)
			return

	var derived := coaster.get_node("derived_construction")
	var names: Array[String] = []
	for child in derived.get_children():
		names.append(child.name)
	if names.filter(func(name: String) -> bool: return name.begins_with("running_rail_")).size() < 100:
		_fail("derived circuit has too few running-rail members")
		return
	if names.filter(func(name: String) -> bool: return name.begins_with("bent_") and name.ends_with("_cap")).size() < 20:
		_fail("derived circuit has too few timber bents")
		return
	if names.filter(func(name: String) -> bool: return name.begins_with("lift_catwalk_")).size() < 5:
		_fail("lift hill has no resolved catwalk")
		return

	for old_name in ["coaster_col_0", "coaster_track_14", "station_floor", "station_roof", "station_sign"]:
		var old := world.get_node_or_null(old_name) as GeometryInstance3D
		if old == null or old.visible:
			_fail("generated greybox node %s was not retired" % old_name)
			return
	if not is_equal_approx(Plan.COASTER_STATION.x, -94.0) or not is_equal_approx(Plan.COASTER_STATION.y, -55.0):
		_fail("ParkPlan R2 operating address moved")
		return

	print("PASS: R2 keeps its map parcel and station while deriving a closed track, timber bents, lift catwalk and four-car train")
	get_tree().quit()


func _fail(message: String) -> void:
	push_error("boardwalk_coaster_test: " + message)
	get_tree().quit(1)
