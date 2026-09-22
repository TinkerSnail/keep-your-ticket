@tool
extends Node3D

## A directly editor-owned parking composition. The eight Path3D bay courses,
## six island sockets, four banner sockets and six south-edge hedge courses in
## parking_lot_layout.tscn own the visible layout. This script derives only
## repetitive paint, parked vehicles, planting and banner panels from those
## selectable controls.

@export var asphalt_material: Material
@export var line_material: Material
@export var accessible_material: Material
@export var curb_material: Material
@export var soil_material: Material
@export var trunk_material: Material
@export var foliage_material: Material
@export var foliage_light_material: Material
@export var glass_material: Material
@export var tyre_material: Material
@export var metal_material: Material
@export var west_banner_material: Material
@export var east_banner_material: Material
@export var paint_materials: Array[Material] = []

var _queued := false


func _ready() -> void:
	_connect_control_curves(get_node_or_null("layout_controls"))
	_queue_rebuild()


func _connect_control_curves(root: Node) -> void:
	if root == null:
		return
	if root is Path3D:
		var course := root as Path3D
		if course.curve != null and not course.curve.changed.is_connected(_queue_rebuild):
			course.curve.changed.connect(_queue_rebuild)
	for child in root.get_children():
		_connect_control_curves(child)


func _queue_rebuild() -> void:
	if _queued or not is_inside_tree():
		return
	_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_queued = false
	var derived := get_node_or_null("derived") as Node3D
	if derived == null:
		return
	for child in derived.get_children():
		child.free()
	var surfaces := Node3D.new()
	surfaces.name = "lot_surfaces"
	derived.add_child(surfaces)
	var paint := Node3D.new()
	paint.name = "parking_paint"
	derived.add_child(paint)
	var vehicles := Node3D.new()
	vehicles.name = "parked_vehicles"
	derived.add_child(vehicles)
	var landscape := Node3D.new()
	landscape.name = "tree_islands"
	derived.add_child(landscape)
	var hedge := Node3D.new()
	hedge.name = "south_edge_hedge"
	derived.add_child(hedge)
	var furniture := Node3D.new()
	furniture.name = "wayfinding"
	derived.add_child(furniture)

	_build_surfaces(surfaces)
	_build_rows(paint, vehicles)
	_build_collectors(paint)
	_build_islands(landscape)
	_build_edge_hedges(hedge)
	_build_banners(furniture)


func _build_surfaces(parent: Node3D) -> void:
	# The field rectangles remain the dimensions fixed by the parking clause.
	# Their ordinary source is this scene, rather than the generated entrance.
	for side in [-1.0, 1.0]:
		_box(parent, "lot_surface_%s" % ("west" if side < 0.0 else "east"),
			Vector3(side * 40.5, -0.055, 198.0), Vector3(55.0, 0.10, 34.0),
			asphalt_material)
		# An inner collector lets every parked guest reach the two existing breaks
		# in the planted allée edge without walking down a vehicle aisle.
		_box(parent, "inner_collector_%s" % ("west" if side < 0.0 else "east"),
			Vector3(side * 11.25, 0.011, 198.0), Vector3(3.2, 0.022, 34.0),
			curb_material)
		# North and outer curbs contain the field. The south edge stays open to
		# the four entry drives fixed by the parking clause.
		_box(parent, "north_curb_%s" % ("west" if side < 0.0 else "east"),
			Vector3(side * 40.5, 0.09, 181.15), Vector3(55.0, 0.18, 0.30),
			curb_material)
		_box(parent, "outer_curb_%s" % ("west" if side < 0.0 else "east"),
			Vector3(side * 67.85, 0.09, 198.0), Vector3(0.30, 0.18, 34.0),
			curb_material)


func _build_rows(paint: Node3D, vehicles: Node3D) -> void:
	var courses := get_node_or_null("layout_controls/bay_courses") as Node3D
	if courses == null:
		return
	var occupancy := [
		[1, 4, 7, 11, 14, 17],
		[0, 3, 6, 9, 13],
		[1, 5, 8, 12, 16],
		[3, 6, 11, 15, 17],
	]
	var vehicle_index := 0
	for candidate in courses.get_children():
		var course := candidate as Path3D
		if course == null or course.curve == null or course.curve.point_count < 2:
			continue
		var row_index := int(course.get_meta("row_index", 0))
		var side := int(course.get_meta("lot_side", 1))
		var facing := float(course.get_meta("facing", 0.0))
		var angle := float(course.get_meta("bay_angle", 0.0)) * float(side)
		var bay_count := int(course.get_meta("bay_count", 19))
		var length := course.curve.get_baked_length()
		for bay in bay_count:
			var station := length * float(bay) / float(maxi(1, bay_count - 1))
			var before := course.curve.sample_baked(maxf(0.0, station - 0.1))
			var after := course.curve.sample_baked(minf(length, station + 0.1))
			var tangent := (after - before).normalized()
			var yaw := atan2(tangent.x, tangent.z) + angle
			var at := course.curve.sample_baked(station)
			_box(paint, "%s_bay_line_%02d" % [course.name, bay],
				at + Vector3.UP * 0.018, Vector3(0.10, 0.018, 4.75),
				line_material, yaw)
		# The blue fields occupy the two inner north bays. One stays empty so the
		# access provision reads as infrastructure rather than decoration.
		if row_index == 0:
			for bay in [0, 1]:
				var station := length * float(bay) / float(maxi(1, bay_count - 1))
				var at := course.curve.sample_baked(station)
				_box(paint, "%s_accessible_%02d" % [course.name, bay],
					at + Vector3.UP * 0.009, Vector3(2.55, 0.016, 4.45),
					accessible_material, angle)
				_box(paint, "%s_accessible_bar_%02d" % [course.name, bay],
					at + Vector3.UP * 0.023, Vector3(1.35, 0.020, 0.12),
					line_material, angle)
		for bay in occupancy[row_index]:
			var station := length * float(bay) / float(maxi(1, bay_count - 1))
			var before := course.curve.sample_baked(maxf(0.0, station - 0.1))
			var after := course.curve.sample_baked(minf(length, station + 0.1))
			var tangent := (after - before).normalized()
			var yaw := atan2(tangent.x, tangent.z) + facing + angle
			var at := course.curve.sample_baked(station)
			_build_vehicle(vehicles, vehicle_index, at, yaw)
			vehicle_index += 1


func _build_collectors(parent: Node3D) -> void:
	# Marked priority crossings connect each one-way aisle to the pedestrian
	# collector, not through the lush allée planting. The allée is entered only
	# at its existing north and south openings.
	for side in [-1.0, 1.0]:
		for z in [189.0, 207.0]:
			for stripe in 5:
				_box(parent, "collector_crossing_%s_%d_%d" % [
					"w" if side < 0.0 else "e", int(z), stripe],
					Vector3(side * (12.4 + float(stripe) * 0.68), 0.025, z),
					Vector3(0.36, 0.018, 2.2), line_material)
	# Two clear one-way arrows per field give the rows a comprehensible flow.
	for side in [-1.0, 1.0]:
		_build_arrow(parent, Vector3(side * 40.5, 0.027, 189.0), -side)
		_build_arrow(parent, Vector3(side * 40.5, 0.027, 207.0), side)


func _build_arrow(parent: Node3D, at: Vector3, direction: float) -> void:
	var root := Node3D.new()
	root.name = "aisle_arrow_%s_%d" % ["w" if at.x < 0.0 else "e", int(at.z)]
	root.position = at
	root.rotation.y = PI * 0.5 if direction > 0.0 else -PI * 0.5
	parent.add_child(root)
	_box(root, "shaft", Vector3.ZERO, Vector3(0.18, 0.018, 2.0), line_material)
	_box(root, "head_left", Vector3(-0.38, 0.0, -0.82),
		Vector3(0.16, 0.018, 1.0), line_material, -0.7)
	_box(root, "head_right", Vector3(0.38, 0.0, -0.82),
		Vector3(0.16, 0.018, 1.0), line_material, 0.7)


func _build_islands(parent: Node3D) -> void:
	var sockets := get_node_or_null("layout_controls/island_sockets") as Node3D
	if sockets == null:
		return
	var index := 0
	for socket in sockets.get_children():
		var marker := socket as Node3D
		if marker == null:
			continue
		var island := Node3D.new()
		island.name = "island_%02d" % index
		island.position = marker.position
		island.rotation = marker.rotation
		parent.add_child(island)
		_box(island, "curb", Vector3(0.0, 0.11, 0.0),
			Vector3(3.4, 0.22, 7.0), curb_material)
		_box(island, "soil", Vector3(0.0, 0.235, 0.0),
			Vector3(3.0, 0.08, 6.6), soil_material)
		_cylinder(island, "trunk", Vector3(0.0, 2.65, 0.0), 0.24, 4.8,
			trunk_material, 10)
		_sphere(island, "canopy_low", Vector3(-0.55, 5.1, 0.25),
			Vector3(2.2, 1.15, 1.9), foliage_material)
		_sphere(island, "canopy_high", Vector3(0.45, 5.65, -0.35),
			Vector3(2.0, 1.25, 1.75), foliage_light_material)
		_sphere(island, "canopy_side", Vector3(0.7, 4.9, 0.75),
			Vector3(1.55, 0.9, 1.45), foliage_material)
		for shrub in 5:
			var sx := -1.0 + float(shrub % 3) * 0.95
			var sz := -2.15 + float(shrub / 3) * 4.1 + float(shrub % 2) * 0.45
			_sphere(island, "shrub_%d" % shrub, Vector3(sx, 0.58, sz),
				Vector3(0.72, 0.42, 0.62),
				foliage_light_material if shrub % 2 else foliage_material)
		index += 1


func _build_edge_hedges(parent: Node3D) -> void:
	# Six editor-owned courses make a planted arrival edge while the four gaps
	# at x ±20 and ±60 remain legible vehicle entries from the front road.
	var courses := get_node_or_null("layout_controls/edge_hedge_courses") as Node3D
	if courses == null:
		return
	for candidate in courses.get_children():
		var course := candidate as Path3D
		if course == null or course.curve == null or course.curve.point_count < 2:
			continue
		var length := course.curve.get_baked_length()
		var count := maxi(2, ceili(length / 1.35) + 1)
		var hedge_run := Node3D.new()
		hedge_run.name = course.name
		parent.add_child(hedge_run)
		for index in count:
			var station := length * float(index) / float(count - 1)
			var at := course.curve.sample_baked(station)
			var before := course.curve.sample_baked(maxf(0.0, station - 0.1))
			var after := course.curve.sample_baked(minf(length, station + 0.1))
			var tangent := (after - before).normalized()
			var shrub := _sphere(hedge_run, "shrub_%02d" % index,
				at + Vector3(0.0, 0.62 + 0.05 * float(index % 3), 0.0),
				Vector3(0.92, 0.58 + 0.04 * float(index % 2), 0.72),
				foliage_light_material if index % 4 == 0 else foliage_material)
			shrub.rotation.y = atan2(tangent.x, tangent.z)


func _build_banners(parent: Node3D) -> void:
	var sockets := get_node_or_null("layout_controls/banner_sockets") as Node3D
	if sockets == null:
		return
	var index := 0
	for socket in sockets.get_children():
		var marker := socket as Node3D
		if marker == null:
			continue
		var banner := Node3D.new()
		banner.name = "banner_%02d" % index
		banner.position = marker.position
		banner.rotation = marker.rotation
		parent.add_child(banner)
		var cloth := west_banner_material if marker.position.x < 0.0 else east_banner_material
		_box(banner, "panel_front", Vector3(-0.88, 7.15, 0.0),
			Vector3(1.45, 2.4, 0.055), cloth)
		_box(banner, "panel_back", Vector3(0.88, 7.15, 0.0),
			Vector3(1.45, 2.4, 0.055), cloth)
		_box(banner, "crossbar", Vector3(0.0, 8.32, 0.0),
			Vector3(2.65, 0.08, 0.10), metal_material)
		index += 1


func _build_vehicle(parent: Node3D, index: int, at: Vector3, yaw: float) -> void:
	var root := Node3D.new()
	root.name = "authored_vehicle_%02d" % index
	root.position = at
	root.rotation.y = yaw
	parent.add_child(root)
	var variant := index % 4
	var widths := [1.72, 1.82, 1.88, 1.94]
	var lengths := [3.65, 4.25, 4.55, 4.65]
	var body_heights := [0.44, 0.48, 0.50, 0.58]
	var cabin_heights := [0.52, 0.55, 0.58, 0.78]
	var cabin_lengths := [1.75, 2.05, 2.55, 3.0]
	var w: float = widths[variant]
	var l: float = lengths[variant]
	var body_h: float = body_heights[variant]
	var cabin_h: float = cabin_heights[variant]
	var cabin_l: float = cabin_lengths[variant]
	var paint := paint_materials[index % paint_materials.size()] \
		if not paint_materials.is_empty() else curb_material
	_box(root, "lower_body", Vector3(0.0, 0.34 + body_h * 0.5, 0.0),
		Vector3(w, body_h, l), paint)
	_box(root, "cabin", Vector3(0.0, 0.58 + body_h + cabin_h * 0.5,
		-0.1 if variant < 2 else 0.05), Vector3(w * 0.83, cabin_h, cabin_l), paint)
	var cabin_y := 0.58 + body_h + cabin_h * 0.5
	_box(root, "windshield", Vector3(0.0, cabin_y, -cabin_l * 0.505),
		Vector3(w * 0.72, cabin_h * 0.56, 0.035), glass_material)
	_box(root, "rear_glass", Vector3(0.0, cabin_y, cabin_l * 0.505),
		Vector3(w * 0.72, cabin_h * 0.56, 0.035), glass_material)
	for side in [-1.0, 1.0]:
		_box(root, "side_window_%s" % ("l" if side < 0.0 else "r"),
			Vector3(side * w * 0.418, cabin_y, 0.0),
			Vector3(0.035, cabin_h * 0.54, cabin_l * 0.72), glass_material)
	for side in [-1.0, 1.0]:
		for axle in [-1.0, 1.0]:
			var wheel := _cylinder(root,
				"wheel_%s_%s" % ["l" if side < 0.0 else "r", "f" if axle < 0.0 else "r"],
				Vector3(side * (w * 0.5 + 0.015), 0.31, axle * l * 0.31),
				0.27, 0.18, tyre_material, 10)
			wheel.rotation.z = PI * 0.5
	# Slim bright bumpers and black number-plate recesses keep the cars from
	# reading as the old single boxes without spending close-detail geometry.
	for end in [-1.0, 1.0]:
		_box(root, "bumper_%s" % ("front" if end < 0.0 else "rear"),
			Vector3(0.0, 0.42, end * (l * 0.5 + 0.025)),
			Vector3(w * 0.82, 0.10, 0.055), metal_material)


func _box(parent: Node3D, node_name: String, at: Vector3, size: Vector3,
		material: Material, yaw: float = 0.0) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.position = at
	instance.rotation.y = yaw
	parent.add_child(instance)
	return instance


func _cylinder(parent: Node3D, node_name: String, at: Vector3, radius: float,
		height: float, material: Material, sides: int) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = sides
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.position = at
	parent.add_child(instance)
	return instance


func _sphere(parent: Node3D, node_name: String, at: Vector3, scale_value: Vector3,
		material: Material) -> MeshInstance3D:
	var mesh := SphereMesh.new()
	mesh.radius = 1.0
	mesh.height = 2.0
	mesh.radial_segments = 12
	mesh.rings = 6
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.position = at
	instance.scale = scale_value
	parent.add_child(instance)
	return instance
