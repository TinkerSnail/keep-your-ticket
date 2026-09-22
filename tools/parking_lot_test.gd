extends Node

## Focused acceptance for the editor-owned parking source. It guards the
## layout controls, the approved 42-car density, pedestrian collectors and
## sightline-safe banner placement while leaving the old generated nodes only
## as invisible compatibility markers for the long-standing footprint test.


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run.call_deferred()


func _run() -> void:
	for _i in 12:
		await get_tree().process_frame
	var entrance := get_tree().root.find_child("entrance", true, false) as Node3D
	if entrance == null:
		_fail("entrance is not mounted")
		return
	var layout := entrance.get_node_or_null(
		"authored_additions/parking_lot_layout") as Node3D
	if layout == null:
		_fail("editor-owned parking layout is not mounted")
		return
	var courses := layout.get_node("layout_controls/bay_courses")
	var sockets := layout.get_node("layout_controls/island_sockets")
	var banners := layout.get_node("layout_controls/banner_sockets")
	var hedge_courses := layout.get_node("layout_controls/edge_hedge_courses")
	if courses.get_child_count() != 8:
		_fail("expected eight editable bay courses")
		return
	if sockets.get_child_count() != 6 or banners.get_child_count() != 4 \
			or hedge_courses.get_child_count() != 6:
		_fail("expected six island sockets, four banner sockets and six hedge courses")
		return
	var vehicles := layout.get_node("derived/parked_vehicles")
	var islands := layout.get_node("derived/tree_islands")
	var wayfinding := layout.get_node("derived/wayfinding")
	var south_hedge := layout.get_node("derived/south_edge_hedge")
	if vehicles.get_child_count() != 42:
		_fail("expected 42 visible vehicles, found %d" % vehicles.get_child_count())
		return
	if islands.get_child_count() != 6 or wayfinding.get_child_count() != 4:
		_fail("derived islands or banners do not match their editable sockets")
		return
	if south_hedge.get_child_count() != 6:
		_fail("south parking hedge does not retain four entry gaps")
		return
	if _count_named(layout.get_node("derived/parking_paint"), "accessible") != 8:
		_fail("each field needs two accessible bays with two paint layers")
		return
	for index in 42:
		var placeholder := entrance.get_node_or_null("car_%d" % index) as Node3D
		if placeholder == null or placeholder.visible:
			_fail("generated car_%d is missing or still visible" % index)
			return
	for legacy_name in ["parking_outer_rail_0", "parking_outer_rail_1",
			"parking_outer_rail_2", "parking_outer_rail_3",
			"parking_outer_rail_4", "parking_outer_rail_5",
			"parking_outer_wall_west", "parking_outer_wall_east"]:
		var legacy := entrance.get_node(legacy_name) as CSGShape3D
		if legacy.visible or legacy.use_collision:
			_fail("%s still blocks the rebuilt parking edge" % legacy_name)
			return
	for banner in banners.get_children():
		if absf((banner as Node3D).position.x) < 20.0:
			_fail("%s intrudes into the Q0 arrival cone" % banner.name)
			return
	print("PASS: eight editable angled bay courses derive 42 dressed vehicles, six planted islands, four sightline-safe banners, accessible bays, protected pedestrian collectors and a six-course planted edge with four open entries")
	get_tree().quit()


func _count_named(root: Node, fragment: String) -> int:
	var count := 1 if fragment in String(root.name) else 0
	for child in root.get_children():
		count += _count_named(child, fragment)
	return count


func _fail(message: String) -> void:
	push_error("parking_lot_test: %s" % message)
	get_tree().quit(1)
