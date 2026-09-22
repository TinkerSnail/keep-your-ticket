extends Node

## Structural and spatial guard for the editor-owned city, foothill and highway
## package. Cameras are not part of this acceptance test.

func _ready() -> void:
	var failures: Array[String] = []
	var south_coast_open_point := Vector2(900.0, 3150.0)
	var world: Node = load("res://scenes/world/park_world.tscn").instantiate()
	add_child(world)
	for frame in 3:
		await get_tree().physics_frame
	var package := world.get_node_or_null("places/far_shore_city_relocation")
	if package == null:
		failures.append("far-shore relocation is not mounted exactly in places")
	else:
		for required in [
			"relocated_city_peninsula",
			"city_highway_extension",
			"city_highway_approach_ground",
			"bridge_main_deck",
			"bridge_city_intersection",
			"bridge_city_southern_offramp",
			"southern_city_range_foothills",
			"southern_city_range_beaches",
			"southern_city_bypass_highway",
			"southern_city_bypass_earthwork",
			"southern_coastal_highway_extension",
			"southern_coastal_highway_earthwork",
			"city_skyline_anchor_0",
			"city_ferry_landing",
			"beach_town_ferry_landing",
			"bay_ferry_hull",
		]:
			if package.find_child(required, true, false) == null:
				failures.append("missing editable source node %s" % required)
		for retired in [
			"southern_range_city_land",
			"southern_range_connection_cliffs",
			"southern_range_rocky_skirt",
			"southern_range_connection_beach",
			"southern_range_perimeter_rock_cliffs",
		]:
			if package.find_child(retired, true, false) != null:
				failures.append("retired flat or shell geometry remains: %s" % retired)
		if package.find_children("*", "StaticBody3D", true, false).size() < 2:
			failures.append("city approach and foothills do not both have imported collision")
		var city := package.find_child(
			"relocated_city_peninsula", true, false) as MeshInstance3D
		var foothills := package.find_child(
			"southern_city_range_foothills", true, false) as MeshInstance3D
		var bypass := package.find_child(
			"southern_city_bypass_highway", true, false) as MeshInstance3D
		var bypass_centreline := package.find_child(
			"southern_city_bypass_centreline", true, false) as MeshInstance3D
		var extension := package.find_child(
			"southern_coastal_highway_extension", true, false) as MeshInstance3D
		var extension_centreline := package.find_child(
			"southern_coastal_highway_extension_centreline", true, false) as MeshInstance3D
		var range_package := world.get_node_or_null("shared/range_forest_background")
		var southern_massif := range_package.find_child(
			"background_distant_range_south", true, false) as MeshInstance3D \
			if range_package != null else null
		var eastern_connection := range_package.find_child(
			"southern_range_connection_lowland", true, false) as MeshInstance3D \
			if range_package != null else null
		if southern_massif == null:
			failures.append("southern range massif is not mounted")
		if eastern_connection == null:
			failures.append("eastern range connection is not mounted")
		if foothills != null:
			var bounds := _world_bounds(foothills)
			if bounds.size.x < 2100.0 or bounds.size.z < 2850.0:
				failures.append("southern foothills do not form the long city-to-range land connection")
			if bounds.size.y < 160.0 or bounds.position.y > -10.9:
				failures.append("southern foothills are not a closed terrain body")
			if _mesh_covers_plan_point(foothills, south_coast_open_point):
				failures.append("southern foothills occupy established south-coast open water")
			if city != null and not _overlaps_plan(_world_bounds(city), bounds):
				failures.append("southern foothills do not connect to the city peninsula")
			if southern_massif == null or not _overlaps_plan(
					bounds, _world_bounds(southern_massif)):
				failures.append("southern foothills do not connect to the southern massif")
			if eastern_connection == null or not _overlaps_plan(
					bounds, _world_bounds(eastern_connection)):
				failures.append("southern foothills do not connect to the eastern range")
		for terrain in [southern_massif, eastern_connection]:
			if terrain != null and _mesh_covers_plan_point(terrain, south_coast_open_point):
				failures.append("mounted range occupies established south-coast open water")
		if bypass != null and extension != null:
			var bypass_bounds := _world_bounds(bypass)
			var extension_bounds := _world_bounds(extension)
			if not _overlaps_plan(bypass_bounds, extension_bounds):
				failures.append("southbound highway does not branch from the city bypass")
			if extension_bounds.end.z < 5350.0:
				failures.append("southbound highway does not reach the new southern massif")
			if southern_massif != null and not _overlaps_plan(
					extension_bounds, _world_bounds(southern_massif)):
				failures.append("southbound highway does not enter the southern massif")
		for pair in [["city bypass", bypass_centreline],
				["coastal branch", extension_centreline]]:
			var ribbon := pair[1] as MeshInstance3D
			if ribbon == null:
				failures.append("%s centreline is missing" % pair[0])
			elif _maximum_ribbon_grade(ribbon) > 0.0201:
				failures.append("%s exceeds its 2%% source-grade cap" % pair[0])
			else:
				_check_ribbon_ground(String(pair[0]), ribbon, failures)
	var towns := world.get_node_or_null("places/park_towns")
	for retired in ["far_city_buildings", "far_city_windows"]:
		var node := towns.get_node_or_null(retired) as Node3D if towns != null else null
		if node == null or node.visible:
			failures.append("retired skyline remains visible: %s" % retired)
	if failures.is_empty():
		print("far_shore_city_test: PASS")
		get_tree().quit()
	else:
		for failure in failures:
			push_error("far_shore_city_test: " + failure)
		get_tree().quit(1)


func _overlaps_plan(a: AABB, b: AABB) -> bool:
	return a.position.x <= b.end.x and a.end.x >= b.position.x \
		and a.position.z <= b.end.z and a.end.z >= b.position.z


func _mesh_covers_plan_point(visual: MeshInstance3D, point: Vector2) -> bool:
	for surface in visual.mesh.get_surface_count():
		var arrays := visual.mesh.surface_get_arrays(surface)
		if arrays.is_empty():
			continue
		var vertices := arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
		var indices := arrays[Mesh.ARRAY_INDEX] as PackedInt32Array
		if indices.is_empty():
			indices.resize(vertices.size())
			for index in indices.size():
				indices[index] = index
		for index in range(0, indices.size(), 3):
			var a := visual.global_transform * vertices[indices[index]]
			var b := visual.global_transform * vertices[indices[index + 1]]
			var c := visual.global_transform * vertices[indices[index + 2]]
			if (b - a).cross(c - a).y <= 0.01:
				continue
			if _point_in_triangle(point, Vector2(a.x, a.z), Vector2(b.x, b.z),
					Vector2(c.x, c.z)):
				return true
	return false


func _point_in_triangle(point: Vector2, a: Vector2, b: Vector2, c: Vector2) -> bool:
	var ab := (b - a).cross(point - a)
	var bc := (c - b).cross(point - b)
	var ca := (a - c).cross(point - c)
	return (ab >= -0.001 and bc >= -0.001 and ca >= -0.001) \
		or (ab <= 0.001 and bc <= 0.001 and ca <= 0.001)


func _maximum_ribbon_grade(ribbon: MeshInstance3D) -> float:
	var arrays := ribbon.mesh.surface_get_arrays(0)
	var vertices := arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
	var centres: Array[Vector3] = []
	for index in range(0, vertices.size(), 2):
		centres.append(ribbon.global_transform * (
			(vertices[index] + vertices[index + 1]) * 0.5))
	var maximum := 0.0
	for index in centres.size() - 1:
		var a := centres[index]
		var b := centres[index + 1]
		var run := Vector2(b.x - a.x, b.z - a.z).length()
		maximum = maxf(maximum, absf(b.y - a.y) / maxf(run, 0.001))
	return maximum


func _check_ribbon_ground(label: String, ribbon: MeshInstance3D,
		failures: Array[String]) -> void:
	var arrays := ribbon.mesh.surface_get_arrays(0)
	var vertices := arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
	var space := get_viewport().get_world_3d().direct_space_state
	var worst_gap := 0.0
	for index in range(0, vertices.size(), 2):
		var point := ribbon.global_transform * (
			(vertices[index] + vertices[index + 1]) * 0.5)
		var query := PhysicsRayQueryParameters3D.create(
			point + Vector3.UP * 4.0, point - Vector3.UP * 8.0, 1)
		var hit := space.intersect_ray(query)
		if hit.is_empty():
			failures.append("%s has no terrain at %s" % [label, point])
			continue
		var gap := point.y - float(hit["position"].y)
		worst_gap = maxf(worst_gap, gap)
		if gap < 0.02:
			failures.append("%s enters terrain by %.2fm at %s" % [label, -gap, point])
		elif gap > 0.35:
			failures.append("%s floats %.2fm over terrain at %s" % [label, gap, point])
	print("%s maximum terrain gap %.2fm" % [label, worst_gap])


func _world_bounds(visual: MeshInstance3D) -> AABB:
	var local := visual.get_aabb()
	var found := false
	var minimum := Vector3.ZERO
	var maximum := Vector3.ZERO
	for endpoint in 8:
		var point := visual.global_transform * local.get_endpoint(endpoint)
		if not found:
			minimum = point
			maximum = point
			found = true
		else:
			minimum = minimum.min(point)
			maximum = maximum.max(point)
	return AABB(minimum, maximum - minimum)
