extends Node

## Structural and spatial guard for the editor-owned city, foothill and highway
## package. Cameras are not part of this acceptance test.

const Plan := preload("res://scripts/park_plan.gd")

func _ready() -> void:
	var failures: Array[String] = []
	var south_coast_open_point := Vector2(900.0, 3150.0)
	var world: Node = load("res://scenes/world/park_world.tscn").instantiate()
	add_child(world)
	for frame in 3:
		await get_tree().physics_frame
	var package := world.get_node_or_null("places/far_shore_city_relocation")
	# The city's and the range's landforms are the world terrain master's since 2026-10-06
	# (tools/blender/world_terrain_join_landforms.py); the city source keeps the rest. Since
	# height-grid Stage 2 (2026-10-13) the world terrain mounts the ground as one height
	# grid, `world_ground`, whose tiles hold those landforms as ground among the rest, so
	# they are no longer bodies to find by name: the checks below that measured them one by
	# one ask the mounted ground instead, or say why they no longer apply.
	var world_terrain := world.get_node_or_null("places/world_terrain")
	if world_terrain == null:
		failures.append("the world terrain is not mounted in places")
	var grid := world_terrain.find_child("world_ground", true, false) \
		if world_terrain != null else null
	if grid == null or grid.get_child_count() == 0:
		failures.append("the world terrain does not mount the ground grid")
	if package == null:
		failures.append("far-shore relocation is not mounted exactly in places")
	else:
		for required in [
			"relocated_city_peninsula",
			"southern_city_range_foothills",
			"southern_city_range_beaches",
		]:
			if package.find_child(required, true, false) != null:
				failures.append("the landform %s is still drawn by the city source too" % required)
		for required in [
			"city_highway_extension",
			"city_highway_approach_ground",
			"bridge_main_deck",
			"bridge_city_intersection",
			"bridge_city_southern_offramp",
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
		# The foothills' collision is the grid's: every tile carries its own, derived at
		# import (2026-10-13).
		var tiles_without := 0
		if grid != null:
			for tile in grid.get_children():
				if tile.find_children("*", "StaticBody3D", true, false).is_empty():
					tiles_without += 1
		if package.find_children("*", "StaticBody3D", true, false).is_empty() \
				or grid == null or tiles_without > 0:
			failures.append("city approach and the ground grid (%d tiles without) do not both have imported collision" % tiles_without)
		var bypass := package.find_child(
			"southern_city_bypass_highway", true, false) as MeshInstance3D
		var bypass_centreline := package.find_child(
			"southern_city_bypass_centreline", true, false) as MeshInstance3D
		var extension := package.find_child(
			"southern_coastal_highway_extension", true, false) as MeshInstance3D
		var extension_centreline := package.find_child(
			"southern_coastal_highway_extension_centreline", true, false) as MeshInstance3D
		# Until 2026-10-13 the foothills, the southern massif and the eastern connection
		# were bodies, each measured for its breadth, its relief, its closure down to the
		# world's base, and its plan overlap with the next, as the evidence that the land
		# runs on from the city to the range. In one height grid there is no body to bound
		# or close, so those only made sense for the pieces. What they stood for is asked
		# of the mounted ground: the south coast's open water stays open (no ground of the
		# grid stands above the water there), and the land carries on from the city to the
		# massif, which the coastal branch proves below by having ground under it from the
		# bypass all the way to its end in the massif.
		var open_water_y := _grid_ground_y(world_terrain, south_coast_open_point) \
			if world_terrain != null else NAN
		print("south-coast open water at %s: the ground grid %s" % [south_coast_open_point,
			"has none" if is_nan(open_water_y) else "at y %.1f" % open_water_y])
		if not is_nan(open_water_y) and open_water_y > Plan.WATER_TOP:
			failures.append("the mounted ground stands %.1fm high in established south-coast open water" % open_water_y)
		if bypass != null and extension != null:
			var bypass_bounds := _world_bounds(bypass)
			var extension_bounds := _world_bounds(extension)
			if not _overlaps_plan(bypass_bounds, extension_bounds):
				failures.append("southbound highway does not branch from the city bypass")
			if extension_bounds.end.z < 5350.0:
				failures.append("southbound highway does not reach the new southern massif")
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


## The top of the mounted ground grid's collision over a plan point, or NAN where the
## grid has none there (2026-10-13). Anything else a ray meets first, a road or a
## building, is passed through.
func _grid_ground_y(world_terrain: Node, at: Vector2) -> float:
	var space := get_viewport().get_world_3d().direct_space_state
	var exclude: Array[RID] = []
	for attempt in 32:
		var query := PhysicsRayQueryParameters3D.create(
			Vector3(at.x, 2000.0, at.y), Vector3(at.x, -500.0, at.y))
		query.exclude = exclude
		var hit := space.intersect_ray(query)
		if hit.is_empty():
			return NAN
		if world_terrain.is_ancestor_of(hit["collider"]):
			return float(hit["position"].y)
		exclude.append(hit["rid"])
	return NAN


func _overlaps_plan(a: AABB, b: AABB) -> bool:
	return a.position.x <= b.end.x and a.end.x >= b.position.x \
		and a.position.z <= b.end.z and a.end.z >= b.position.z


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
