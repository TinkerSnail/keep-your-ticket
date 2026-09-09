extends RefCounted

## Read boundary for the editor-owned park vertical controls. The source scene
## stores literal Godot world metres, so consumers must not apply the rebuild
## expansion transform. It provides constraints, not terrain geometry.

const Layout = preload("res://scenes/world/park_vertical_controls.tscn")


static func instantiate() -> Node3D:
	var root := Layout.instantiate() as Node3D
	assert(root != null, "park vertical controls did not instantiate")
	assert(root.get_meta("coordinate_space", "") == "godot_world_metres",
		"park vertical controls must stay in literal Godot world metres")
	return root


static func approved_levels(root: Node3D) -> Dictionary:
	var out := {}
	for child in root.get_node("approved_levels").get_children():
		if child is Marker3D:
			out[StringName(child.name)] = {
				"position": marker_position(child, root),
				"kind": StringName(child.get_meta("kind", "")),
				"district": StringName(child.get_meta("district", "")),
				"status": StringName(child.get_meta("status", "")),
				"map_id": StringName(child.get_meta("map_id", "")),
				"relationship": StringName(child.get_meta("relationship", "")),
				"protection": StringName(child.get_meta("protection", "")),
			}
	return out


static func levels_for_district(root: Node3D, district: StringName) -> Dictionary:
	var out := {}
	var levels := approved_levels(root)
	for id in levels:
		var record: Dictionary = levels[id]
		if String(record["district"]).split(",").has(String(district)):
			out[id] = record
	return out


static func drainage_basins(root: Node3D) -> Dictionary:
	var out := {}
	var levels := approved_levels(root)
	for basin in root.get_node("approved_terrain_shapes").get_children():
		var low_id := StringName(basin.get_meta("low_level_id", ""))
		assert(levels.has(low_id), "%s names missing low level %s" % [basin.name, low_id])
		var rim: Array[Vector3] = []
		for child in basin.get_children():
			if child is Marker3D:
				rim.append(marker_position(child, root))
		out[StringName(basin.name)] = {
			"status": StringName(basin.get_meta("status", "")),
			"low_level_id": low_id,
			"low": levels[low_id]["position"],
			"rim": rim,
			"hold_fixed": String(basin.get_meta("hold_fixed", "")),
			"protection": StringName(basin.get_meta("protection", "")),
			"shape_source": StringName(basin.get_meta("shape_source", "")),
		}
	return out


static func lighthouse_regrade(root: Node3D) -> Dictionary:
	var node := root.get_node("approved_regrades/P1_lighthouse_walk") as Node3D
	var path := node.get_node("target_path_curve") as Path3D
	return {
		"target_max_grade": float(node.get_meta("target_max_grade")),
		"current_max_grade": float(node.get_meta("current_max_grade")),
		"current_length": float(node.get_meta("current_length")),
		"violation_span": float(node.get_meta("violation_span")),
		"minimum_extra_run": float(node.get_meta("minimum_extra_run_if_landform_held")),
		"ownership": StringName(node.get_meta("ownership")),
		"hold_fixed": String(node.get_meta("hold_fixed")),
		"terrain_bed_half_width": float(node.get_meta("terrain_bed_half_width")),
		"terrain_outer_seaward": float(node.get_meta("terrain_outer_seaward")),
		"terrain_outer_landward": float(node.get_meta("terrain_outer_landward")),
		"terrain_bed_depth": float(node.get_meta("terrain_bed_depth")),
		"terrain_sample_spacing": float(node.get_meta("terrain_sample_spacing")),
		"terrain_grid_step": float(node.get_meta("terrain_grid_step")),
		"peak_from": marker_position(node.get_node("measured_peak_from"), root),
		"peak_to": marker_position(node.get_node("measured_peak_to"), root),
		"curve_status": StringName(node.get_meta("curve_status", "")),
		"path_status": StringName(path.get_meta("status", "")),
		"target_path": path,
	}


static func lighthouse_curve_points(root: Node3D) -> Array[Vector3]:
	var path := root.get_node(
		"approved_regrades/P1_lighthouse_walk/target_path_curve") as Path3D
	assert(path.curve != null, "P1 target path has no Curve3D")
	var to_root := node_transform(path, root)
	var out: Array[Vector3] = []
	for index in path.curve.point_count:
		out.append(to_root * path.curve.get_point_position(index))
	return out


static func lighthouse_curve_transform(root: Node3D) -> Transform3D:
	var path := root.get_node(
		"approved_regrades/P1_lighthouse_walk/target_path_curve") as Path3D
	return node_transform(path, root)


## Read in source-root space so moving a marker or a complete control group in
## the editor is observed by every later consumer without copied coordinates.
static func marker_position(marker: Node3D, root: Node3D) -> Vector3:
	return (node_transform(marker, root) as Transform3D).origin


static func node_transform(node: Node3D, root: Node3D) -> Transform3D:
	var transform := node.transform
	var parent := node.get_parent()
	while parent is Node3D and parent != root:
		transform = (parent as Node3D).transform * transform
		parent = parent.get_parent()
	assert(parent == root, "%s is not inside the vertical-control root" % node.name)
	return transform
