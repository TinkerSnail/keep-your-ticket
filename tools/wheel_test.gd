extends Node

## Focused R1 acceptance: editor-owned envelope, twenty gondolas, operating
## rotation while open, gravity-upright cabins and a stopped wheel after close.

const Plan := preload("res://scripts/park_plan.gd")


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run.call_deferred()


func _run() -> void:
	for _i in 10:
		await get_tree().process_frame
	var wheel := get_tree().root.find_child("boardwalk_pacific_wheel", true, false) as Node3D
	if wheel == null:
		_fail("editor-owned R1 wheel is not mounted")
		return
	var rim := wheel.get_node("machine/rim_east") as CSGTorus3D
	var cars := wheel.get_node("machine/gondolas").get_children()
	if cars.size() != 20:
		_fail("expected 20 gondolas, found %d" % cars.size())
		return
	var crown := rim.position.y + rim.outer_radius
	if not is_equal_approx(crown, Plan.WHEEL_TOP):
		_fail("rim crown %.3f moved from WHEEL_TOP %.3f" % [crown, Plan.WHEEL_TOP])
		return
	for car in cars:
		var cabin := car.get_node_or_null("cabin")
		var canopy := cabin.get_node_or_null("canopy") as CSGCylinder3D if cabin != null else null
		if cabin == null or canopy == null or canopy.sides != 8:
			_fail("%s is missing its instanced octagonal-roof cabin" % car.name)
			return
	for index in 20:
		for member_name in ["west_%02d" % index, "east_%02d" % index]:
			if not _is_radial(wheel.get_node("machine/spokes/" + member_name), 6.35, 12.7):
				_fail("structural spoke %s is a chord instead of a hub-to-rim radial" % member_name)
				return
		var tube_name := "light_tube_%02d" % index
		if not _is_radial(wheel.get_node("machine/spokes/" + tube_name), 6.05, 12.4):
			_fail("%s is a chord instead of a hub-to-rim radial" % tube_name)
			return

	ParkClock.set_clock(15, 0)
	wheel.set("boarding_dwell_seconds", 0.0)
	wheel.call("release_boarding_dwell_for_test")
	var start: Vector3 = cars[0].position
	for _i in 60:
		await get_tree().process_frame
	if cars[0].position.distance_to(start) < 0.1:
		_fail("wheel did not turn while the park was open")
		return
	for car in cars:
		if car.global_basis.y.dot(Vector3.UP) < 0.999:
			_fail("%s did not remain upright" % car.name)
			return

	ParkClock.set_clock(22, 15)
	var stopped: Vector3 = cars[0].position
	for _i in 30:
		await get_tree().process_frame
	if cars[0].position.distance_to(stopped) > 0.001:
		_fail("wheel continued turning after close")
		return
	print("PASS: R1 has twenty upright moving gondolas, fixed crown and after-close stop")
	get_tree().quit()


func _fail(message: String) -> void:
	push_error("wheel_test: " + message)
	get_tree().quit(1)


func _is_radial(member: Node3D, half_length: float, outer_radius: float) -> bool:
	var axis := member.transform.basis.z.normalized()
	var end_a := member.position + axis * half_length
	var end_b := member.position - axis * half_length
	var hub_yz := Vector2(-16.0, 12.6)
	var radius_a := Vector2(end_a.z, end_a.y).distance_to(hub_yz)
	var radius_b := Vector2(end_b.z, end_b.y).distance_to(hub_yz)
	return minf(radius_a, radius_b) <= 0.35 \
		and absf(maxf(radius_a, radius_b) - outer_radius) <= 0.05
