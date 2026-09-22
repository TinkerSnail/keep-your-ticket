extends Node

## Read-only mounted-coordinate inventory for the range recovery gate.
##
## This tool deliberately does not modify or save any scene or source. It loads
## the persistent world, measures the terrain meshes that participate in the
## range/city/coast composition, and prints one JSON record between stable
## markers so the review map can be regenerated without using a camera.

const WORLD := "res://scenes/world/park_world.tscn"
const Plan = preload("res://scripts/park_plan.gd")
const GROUNDWORKS := "res://scenes/world/park_groundworks.tscn"
const APPROACH := "res://scenes/world/park_approach.tscn"
const RANGE_MOUNT := "res://scenes/world/range_forest_background.tscn"
const CITY_MOUNT := "res://scenes/world/far_shore_city_relocation.tscn"

const GENERATED_SOURCE := "res://tools/gen_props.gd + res://scripts/park_plan.gd"
const RANGE_SOURCE := "res://assets/source/range_forest_distinct_background.blend"
const CITY_SOURCE := "res://assets/source/far_shore_city_relocation.blend"
const PLAN_CELL := 40.0

const SECTIONS := [
	{
		"id": "north_town_valley",
		"label": "North-town valley and northern coast",
		"from": Vector2(-900.0, -1830.0),
		"to": Vector2(1050.0, -1830.0),
	},
	{
		"id": "north_northeast_overlap",
		"label": "North / northeast range overlap",
		"from": Vector2(-950.0, -900.0),
		"to": Vector2(1750.0, -900.0),
	},
	{
		"id": "park_city_axis",
		"label": "Park-to-city / bridge axis",
		"path": [Vector2(-150.0, 0.0), Vector2(-55.0, 2450.0),
			Vector2(-650.0, 2650.0)],
	},
	{
		"id": "southern_range_connection",
		"label": "Southern range and city connection",
		"from": Vector2(-1500.0, 3000.0),
		"to": Vector2(450.0, 6000.0),
	},
	{
		"id": "southern_highway_cut",
		"label": "Coastal highway and southern branch",
		"from": Vector2(-1800.0, 4300.0),
		"to": Vector2(700.0, 4300.0),
	},
]

var _cells_by_id := {}

const RECORDS := [
	{
		"id": "generated_mainland",
		"root": "groundworks",
		"node": "terrain_world_mainland_reserve/surface",
		"scene": "res://scenes/world/generated/park_groundworks.tscn",
		"source": GENERATED_SOURCE,
		"authority": "generated",
		"role": "primary mainland support and generator-owned crescent range",
	},
	{
		"id": "generated_coast_north",
		"root": "groundworks",
		"node": "terrain_world_coast_north/surface",
		"scene": "res://scenes/world/generated/park_groundworks.tscn",
		"source": GENERATED_SOURCE,
		"authority": "generated",
		"role": "northern coast support and north-town valley mouth",
	},
	{
		"id": "generated_coast_south",
		"root": "groundworks",
		"node": "terrain_world_coast_south/surface",
		"scene": "res://scenes/world/generated/park_groundworks.tscn",
		"source": GENERATED_SOURCE,
		"authority": "generated",
		"role": "southern coast support and beach-town shelf",
	},
	{
		"id": "generated_road_corridor",
		"root": "groundworks",
		"node": "terrain_road_corridor/surface",
		"scene": "res://scenes/world/generated/park_groundworks.tscn",
		"source": GENERATED_SOURCE,
		"authority": "generated",
		"role": "coast-highway and approach-road cut/fill terrain",
	},
	{
		"id": "road__approach_road",
		"root": "approach",
		"node": "approach_road/surface",
		"scene": "res://scenes/world/generated/park_approach.tscn",
		"source": GENERATED_SOURCE,
		"authority": "generated",
		"category": "infrastructure",
		"role": "park approach road surface",
	},
	{
		"id": "road__coast_highway_a",
		"root": "approach",
		"node": "highway/surface",
		"scene": "res://scenes/world/generated/park_approach.tscn",
		"source": GENERATED_SOURCE,
		"authority": "generated",
		"category": "infrastructure",
		"role": "coast highway carriageway A",
	},
	{
		"id": "road__coast_highway_b",
		"root": "approach",
		"node": "highway_b/surface",
		"scene": "res://scenes/world/generated/park_approach.tscn",
		"source": GENERATED_SOURCE,
		"authority": "generated",
		"category": "infrastructure",
		"role": "coast highway carriageway B",
	},
]

const RANGE_ROLES := {
	"middle_continuous_canopy_mass": "older continuous middle range layer",
	"transition_broken_canopy_surface": "older broken transition layer",
	"background_distant_range_north": "northern distant range body with the accepted smaller seaward plan form and irregular exposed rock-to-skirt contact",
	"background_distant_range_north_inland_saddle": "closed editor-owned blue saddle connecting the northern massif to the inland blue range while remaining clear of the highway tunnel portals",
	"background_distant_range_north_west_companion": "twice-linear-sized closed blue companion massif west of the northern body with its own integral beach skirt and retained buried eastern join",
	"background_distant_range_middle": "middle distant range body",
	"background_distant_range_south": "southern massif",
	"background_distant_range_southeast_connector": "southeast connector ridge",
	"southern_range_connection_lowland": "broad eastern connection",
	"southeast_range_ridge_1": "southeast geographic ridge",
	"southeast_range_ridge_2": "southeast geographic ridge",
	"southeast_range_ridge_3": "southeast geographic ridge",
	"southeast_range_ridge_4": "southeast geographic ridge",
	"southern_range_connection_ridge_0": "southern geographic ridge",
	"southern_range_connection_ridge_1": "southern geographic ridge",
	"southern_range_connection_ridge_2": "southern geographic ridge",
	"southern_range_connection_ridge_3": "southern geographic ridge",
	"southern_range_connection_ridge_4": "southern geographic ridge",
	"north_shore_volcanic_plug": "Morro-like volcanic plug with an off-centre crown, unequal upper shoulders, an irregular rock-to-skirt contact, a widened south beach shelf and vertically lowered inland sand reveal",
}

const CITY_ROLES := {
	"relocated_city_peninsula": "primary city peninsula land",
	"city_highway_approach_ground": "bridge/highway approach earthwork",
	"southern_city_range_foothills": "city-to-range foothill connection",
	"southern_city_range_beaches": "southern beach and cliff edge",
	"southern_city_bypass_earthwork": "city bypass road earthwork",
	"southern_coastal_highway_earthwork": "southern coastal-branch earthwork",
}

const CITY_INFRASTRUCTURE_ROLES := {
	"city_highway_extension": "far-shore highway into the suspension bridge",
	"bridge_main_deck": "protected suspension bridge deck",
	"bridge_city_intersection": "protected bridge/city intersection",
	"bridge_city_southern_offramp": "protected bridge/city southern off-ramp",
	"southern_city_bypass_highway": "city bypass road surface",
	"southern_coastal_highway_extension": "southern coastal-branch road surface",
}


func _ready() -> void:
	# Loading only the three singular mounts avoids compiling unrelated park
	# shaders while preserving their identity transforms from `park_world`.
	var groundworks := load(GROUNDWORKS).instantiate() as Node3D
	groundworks.name = "groundworks"
	add_child(groundworks)
	var approach := load(APPROACH).instantiate() as Node3D
	approach.name = "approach"
	add_child(approach)
	var range_root := load(RANGE_MOUNT).instantiate() as Node3D
	range_root.name = "range_mount"
	add_child(range_root)
	var city_root := load(CITY_MOUNT).instantiate() as Node3D
	city_root.name = "city_mount"
	add_child(city_root)
	for frame in 3:
		await get_tree().physics_frame

	var inventory: Array[Dictionary] = []
	for spec in RECORDS:
		var root := get_node_or_null(String(spec["root"]))
		var visual := root.get_node_or_null(String(spec["node"])) as MeshInstance3D \
			if root != null else null
		if visual == null or visual.mesh == null:
			push_error("range_geography_audit: missing %s" % spec["id"])
			continue
		inventory.append(_record_with_footprint(visual, spec))

	if range_root == null:
		push_error("range_geography_audit: mounted range root is missing")
	else:
		for visual in range_root.find_children("*", "MeshInstance3D", true, false):
			if not _is_range_terrain(String(visual.name)):
				continue
			inventory.append(_record_with_footprint(visual, {
				"id": "range__%s" % visual.name,
				"scene": "res://scenes/world/range_forest_background.tscn",
				"source": RANGE_SOURCE,
				"authority": "editor-owned",
				"role": _range_role(String(visual.name)),
			}))

	if city_root == null:
		push_error("range_geography_audit: mounted city root is missing")
	else:
		for visual in city_root.find_children("*", "MeshInstance3D", true, false):
			if not CITY_ROLES.has(String(visual.name)) \
					and not CITY_INFRASTRUCTURE_ROLES.has(String(visual.name)):
				continue
			var role: String = CITY_ROLES[String(visual.name)] \
				if CITY_ROLES.has(String(visual.name)) \
				else CITY_INFRASTRUCTURE_ROLES[String(visual.name)]
			inventory.append(_record_with_footprint(visual, {
				"id": "city__%s" % visual.name,
				"scene": "res://scenes/world/far_shore_city_relocation.tscn",
				"source": CITY_SOURCE,
				"authority": "editor-owned",
				"category": "terrain" if CITY_ROLES.has(String(visual.name)) \
					else "protected infrastructure",
				"role": role,
			}))

	var overlaps := _sampled_footprint_overlaps(inventory)
	_attach_intersections(inventory, overlaps)
	var result := {
		"world_scene": WORLD,
		"plan_cell_metres": PLAN_CELL,
		"inventory": inventory,
		"sampled_plan_overlaps": overlaps,
		"cross_sections": _cross_sections(inventory),
		"reference_regions": _reference_regions(),
		"notes": [
			"Bounds and overlap pairs are measured from the mounted scene in world coordinates.",
			"Plan footprints are conservative 40m cells intersected by projected source triangles; reported overlap area is cell-count area, not exact polygon area.",
			"Cross-sections show the minimum-to-maximum source volume in each intersected 40m plan cell; they are ownership diagnostics rather than smooth terrain profiles.",
			"The mounted range remains a rejected overlapping composition; this audit records ownership conflicts rather than accepting them.",
		],
	}
	print("RANGE_GEOGRAPHY_AUDIT_JSON_BEGIN")
	print(JSON.stringify(result, "  ", false, true))
	print("RANGE_GEOGRAPHY_AUDIT_JSON_END")
	get_tree().quit()


func _reference_regions() -> Array[Dictionary]:
	var north_town := []
	var town_rect: Rect2 = Plan.NORTH_TOWN_EXTENT_ST
	for st in [town_rect.position,
			Vector2(town_rect.end.x, town_rect.position.y), town_rect.end,
			Vector2(town_rect.position.x, town_rect.end.y)]:
		var point: Vector2 = Plan.valley_point(st.x, st.y)
		north_town.append([point.x, point.y])
	var beach_town := []
	for point: Vector2 in Plan.BEACH_TOWN_OUTLINE:
		beach_town.append([point.x, point.y])
	return [
		{
			"id": "developed_park",
			"label": "Developed park envelope",
			"points": [
				[Plan.REBUILD_FOOTPRINT_MIN_X, Plan.REBUILD_FOOTPRINT_MIN_Z],
				[Plan.REBUILD_FOOTPRINT_MAX_X, Plan.REBUILD_FOOTPRINT_MIN_Z],
				[Plan.REBUILD_FOOTPRINT_MAX_X, Plan.REBUILD_FOOTPRINT_MAX_Z],
				[Plan.REBUILD_FOOTPRINT_MIN_X, Plan.REBUILD_FOOTPRINT_MAX_Z],
			],
		},
		{"id": "north_town", "label": "North town", "points": north_town},
		{"id": "beach_town", "label": "Beach town", "points": beach_town},
	]


func _is_range_terrain(name: String) -> bool:
	return RANGE_ROLES.has(name)


func _range_role(name: String) -> String:
	return RANGE_ROLES.get(name, "unclassified range terrain")


func _record(visual: MeshInstance3D, spec: Dictionary) -> Dictionary:
	var bounds := _world_bounds(visual)
	var materials: Array[String] = []
	for surface in visual.mesh.get_surface_count():
		var material := visual.get_active_material(surface)
		var label := "<none>"
		if material != null:
			label = String(material.resource_name)
			if label.is_empty() and not String(material.resource_path).is_empty():
				label = String(material.resource_path)
			if label.is_empty():
				label = material.get_class()
		if not materials.has(label):
			materials.append(label)
	var collision_owner := _collision_owner(visual)
	return {
		"id": String(spec["id"]),
		"node_path": String(visual.get_path()),
		"scene": String(spec["scene"]),
		"editable_source": String(spec["source"]),
		"authority": String(spec["authority"]),
		"category": String(spec.get("category", "terrain")),
		"role": String(spec["role"]),
		"bounds": {
			"min_x": snappedf(bounds.position.x, 0.01),
			"max_x": snappedf(bounds.end.x, 0.01),
			"min_y": snappedf(bounds.position.y, 0.01),
			"max_y": snappedf(bounds.end.y, 0.01),
			"min_z": snappedf(bounds.position.z, 0.01),
			"max_z": snappedf(bounds.end.z, 0.01),
		},
		"materials": materials,
		"collision_owner": collision_owner,
		"surfaces": visual.mesh.get_surface_count(),
		"triangles": _triangle_count(visual.mesh),
	}


func _record_with_footprint(visual: MeshInstance3D, spec: Dictionary) -> Dictionary:
	var record := _record(visual, spec)
	var cells := _footprint_cells(visual)
	_cells_by_id[record["id"]] = cells
	record["footprint_cells"] = cells.size()
	record["footprint_rle"] = _footprint_rle(cells)
	return record


func _collision_owner(visual: MeshInstance3D) -> String:
	# A `-col` import hint puts the derived StaticBody under the visual itself;
	# the range source has exported that way since 2026-09-15.
	for own in visual.get_children():
		if own is CollisionObject3D:
			return String(own.get_path())
	var parent := visual.get_parent()
	if parent is CollisionObject3D:
		return String(parent.get_path())
	var root := parent
	while root != null and not (root is CollisionObject3D):
		root = root.get_parent()
	if root is CollisionObject3D:
		return String(root.get_path())
	# Blender imports usually place the generated StaticBody beside the visual.
	var search := visual.get_parent()
	if search != null:
		for body in search.find_children("*", "StaticBody3D", true, false):
			if String(body.name).contains(String(visual.name)):
				return String(body.get_path())
	return "none"


func _triangle_count(mesh: Mesh) -> int:
	var count := 0
	for surface in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(surface)
		if arrays.is_empty():
			continue
		var raw_indices = arrays[Mesh.ARRAY_INDEX]
		if raw_indices == null:
			count += (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
		else:
			var indices := raw_indices as PackedInt32Array
			count += indices.size() / 3
	return count


func _sampled_footprint_overlaps(inventory: Array[Dictionary]) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for i in inventory.size():
		for j in range(i + 1, inventory.size()):
			var a := inventory[i]
			var b := inventory[j]
			var ac: Dictionary = _cells_by_id[a["id"]]
			var bc: Dictionary = _cells_by_id[b["id"]]
			var smaller := ac if ac.size() <= bc.size() else bc
			var larger := bc if ac.size() <= bc.size() else ac
			var shared := 0
			var lo := Vector2i(2147483647, 2147483647)
			var hi := Vector2i(-2147483648, -2147483648)
			for cell in smaller:
				if not larger.has(cell):
					continue
				shared += 1
				lo = lo.min(cell)
				hi = hi.max(cell)
			if shared == 0:
				continue
			result.append({
				"a": a["id"],
				"b": b["id"],
				"shared_cells": shared,
				"sampled_area_m2": shared * PLAN_CELL * PLAN_CELL,
				"bounds": {
					"min_x": lo.x * PLAN_CELL,
					"max_x": (hi.x + 1) * PLAN_CELL,
					"min_z": lo.y * PLAN_CELL,
					"max_z": (hi.y + 1) * PLAN_CELL,
				},
			})
	return result


func _attach_intersections(inventory: Array[Dictionary], overlaps: Array[Dictionary]) -> void:
	var records := {}
	for record in inventory:
		record["intersects"] = []
		records[record["id"]] = record
	for overlap in overlaps:
		(records[overlap["a"]]["intersects"] as Array).append(overlap["b"])
		(records[overlap["b"]]["intersects"] as Array).append(overlap["a"])


func _footprint_cells(visual: MeshInstance3D) -> Dictionary:
	var cells := {}
	for surface in visual.mesh.get_surface_count():
		var arrays := visual.mesh.surface_get_arrays(surface)
		if arrays.is_empty():
			continue
		var vertices := arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
		var raw_indices = arrays[Mesh.ARRAY_INDEX]
		var indices := PackedInt32Array()
		if raw_indices == null:
			indices.resize(vertices.size())
			for index in indices.size():
				indices[index] = index
		else:
			indices = raw_indices as PackedInt32Array
		for index in range(0, indices.size(), 3):
			var a3 := visual.global_transform * vertices[indices[index]]
			var b3 := visual.global_transform * vertices[indices[index + 1]]
			var c3 := visual.global_transform * vertices[indices[index + 2]]
			var a := Vector2(a3.x, a3.z)
			var b := Vector2(b3.x, b3.z)
			var c := Vector2(c3.x, c3.z)
			if absf((b - a).cross(c - a)) < 0.001:
				continue
			var min_x := floori(minf(a.x, minf(b.x, c.x)) / PLAN_CELL)
			var max_x := floori(maxf(a.x, maxf(b.x, c.x)) / PLAN_CELL)
			var min_z := floori(minf(a.y, minf(b.y, c.y)) / PLAN_CELL)
			var max_z := floori(maxf(a.y, maxf(b.y, c.y)) / PLAN_CELL)
			for ix in range(min_x, max_x + 1):
				for iz in range(min_z, max_z + 1):
					if not _triangle_intersects_cell(a, b, c, ix, iz):
						continue
					var key := Vector2i(ix, iz)
					var low := minf(a3.y, minf(b3.y, c3.y))
					var high := maxf(a3.y, maxf(b3.y, c3.y))
					if cells.has(key):
						var interval: Vector2 = cells[key]
						cells[key] = Vector2(minf(interval.x, low), maxf(interval.y, high))
					else:
						cells[key] = Vector2(low, high)
	return cells


func _triangle_intersects_cell(a: Vector2, b: Vector2, c: Vector2,
		ix: int, iz: int) -> bool:
	var lo := Vector2(ix * PLAN_CELL, iz * PLAN_CELL)
	var hi := lo + Vector2.ONE * PLAN_CELL
	for point in [a, b, c]:
		if point.x >= lo.x and point.x <= hi.x and point.y >= lo.y and point.y <= hi.y:
			return true
	var corners := [lo, Vector2(hi.x, lo.y), hi, Vector2(lo.x, hi.y)]
	for corner in corners:
		if _point_in_triangle(corner, a, b, c):
			return true
	var tri_edges := [[a, b], [b, c], [c, a]]
	var cell_edges := [[corners[0], corners[1]], [corners[1], corners[2]],
		[corners[2], corners[3]], [corners[3], corners[0]]]
	for tri_edge in tri_edges:
		for cell_edge in cell_edges:
			if Geometry2D.segment_intersects_segment(
					tri_edge[0], tri_edge[1], cell_edge[0], cell_edge[1]) != null:
				return true
	return false


func _point_in_triangle(point: Vector2, a: Vector2, b: Vector2, c: Vector2) -> bool:
	var ab := (b - a).cross(point - a)
	var bc := (c - b).cross(point - b)
	var ca := (a - c).cross(point - c)
	return (ab >= -0.001 and bc >= -0.001 and ca >= -0.001) \
		or (ab <= 0.001 and bc <= 0.001 and ca <= 0.001)


func _footprint_rle(cells: Dictionary) -> Array:
	var rows := {}
	for cell: Vector2i in cells:
		if not rows.has(cell.y):
			rows[cell.y] = []
		(rows[cell.y] as Array).append(cell.x)
	var z_rows: Array = rows.keys()
	z_rows.sort()
	var result := []
	for iz in z_rows:
		var xs: Array = rows[iz]
		xs.sort()
		var start: int = xs[0]
		var previous := start
		for at in range(1, xs.size()):
			var current: int = xs[at]
			if current > previous + 1:
				result.append([iz, start, previous])
				start = current
			previous = current
		result.append([iz, start, previous])
	return result


func _cross_sections(inventory: Array[Dictionary]) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for spec in SECTIONS:
		var path: Array = spec["path"] if spec.has("path") \
			else [spec["from"], spec["to"]]
		var length := _polyline_length(path)
		var samples := maxi(2, ceili(length / (PLAN_CELL * 0.5)))
		var series := []
		for record in inventory:
			var cells: Dictionary = _cells_by_id[record["id"]]
			var points := []
			for index in range(samples + 1):
				var distance := length * index / samples
				var position := _point_along_polyline(path, distance)
				var key := Vector2i(floori(position.x / PLAN_CELL),
					floori(position.y / PLAN_CELL))
				if not cells.has(key):
					continue
				var interval: Vector2 = cells[key]
				points.append([snappedf(distance, 0.1), snappedf(interval.x, 0.1),
					snappedf(interval.y, 0.1)])
			if not points.is_empty():
				series.append({"id": record["id"], "points": points})
		result.append({
			"id": spec["id"],
			"label": spec["label"],
			"path": path.map(func(point: Vector2): return [point.x, point.y]),
			"length_metres": snappedf(length, 0.1),
			"series": series,
		})
	return result


func _polyline_length(path: Array) -> float:
	var length := 0.0
	for index in path.size() - 1:
		length += (path[index] as Vector2).distance_to(path[index + 1])
	return length


func _point_along_polyline(path: Array, distance: float) -> Vector2:
	var remaining := distance
	for index in path.size() - 1:
		var a := path[index] as Vector2
		var b := path[index + 1] as Vector2
		var leg := a.distance_to(b)
		if remaining <= leg or index == path.size() - 2:
			return a.lerp(b, clampf(remaining / maxf(leg, 0.001), 0.0, 1.0))
		remaining -= leg
	return path[path.size() - 1]


func _world_bounds(visual: MeshInstance3D) -> AABB:
	var local := visual.get_aabb()
	var minimum := visual.global_transform * local.get_endpoint(0)
	var maximum := minimum
	for endpoint in range(1, 8):
		var point := visual.global_transform * local.get_endpoint(endpoint)
		minimum = minimum.min(point)
		maximum = maximum.max(point)
	return AABB(minimum, maximum - minimum)
