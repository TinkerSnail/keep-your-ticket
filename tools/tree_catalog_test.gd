extends Node

## The current tree census has editable source geometry. The mounted range keeps
## its north, middle and southeast sections, then continues through the new
## southern connection and closed southern massif. Rejected duplicate shells
## and the per-tree implementation remain absent; detailed trees stay catalog-only.

const FOREST_SCRIPT := "res://scenes/world/range_forest.gd"
const CANOPY_SCENE := "res://scenes/world/range_forest_canopy.tscn"
const BACKGROUND_SCENE := "res://scenes/world/range_forest_background.tscn"
const MIDGROUND_PROOF_SCENE := "res://scenes/world/range_forest_midground_proof.tscn"
const Plan := preload("res://scripts/park_plan.gd")
const SOUTH_COAST_OPEN_POINT := Vector2(900.0, 3150.0)
## The range's sections in order along it, north to south, each with its summit in plan
## and the relief over the water it must keep there: the summits are the tops of the
## master's pieces as they were mounted until height-grid Stage 2 (2026-10-13; the pieces
## were retired in Stage 5, 2026-10-15, and are in git up to a8cd64b), the
## reliefs the minima those pieces were held to before, measured now from the water rather
## than from their closed base at -11 m. The connection's lowland, the base the ridges
## stood on, is in the land between them. A section Christina moves on purpose moves here
## too.
const RANGE_SECTIONS := [
	["north range", Vector2(127.26, -1247.87), 250.0],
	["middle range", Vector2(1132.64, -355.02), 275.0],
	["southeast range", Vector2(1261.42, 716.74), 160.0],
	["southeast ridge 1", Vector2(1450.0, 1266.72), 140.0],
	["southeast ridge 2", Vector2(1538.78, 1863.32), 140.0],
	["southeast ridge 3", Vector2(1489.01, 2460.3), 140.0],
	["southeast ridge 4", Vector2(1771.21, 3154.79), 140.0],
	["southern connection ridge 0", Vector2(1297.7, 3778.69), 140.0],
	["southern connection ridge 1", Vector2(682.45, 4052.93), 140.0],
	["southern connection ridge 2", Vector2(322.78, 4573.34), 140.0],
	["southern connection ridge 3", Vector2(-27.08, 5038.58), 140.0],
	["southern connection ridge 4", Vector2(-401.17, 5475.0), 140.0],
	["southern range", Vector2(0.0, 5652.99), 250.0],
]
const MIDGROUND_NEAR_DEPTH := 0.0
const MIDGROUND_FAR_DEPTH := 164.0
const TRANSITION_NEAR_DEPTH := 180.0
const TRANSITION_FAR_DEPTH := 224.0
const TRANSITION_MAX_HEIGHT := 65.2
const PARK_WORLD := "res://scenes/world/park_world.tscn"
const PALM_SPECIMEN := "res://scenes/world/coastal_palm_tree_specimen.tscn"
const REDWOOD_FAMILY := "res://scenes/world/coastal_redwood_family.tscn"
const NEEDLE_SPRAY_SCRIPT := "res://scenes/world/conifer_needle_spray_mesh.gd"
const SOURCES := {
	"PRP-PLANT-001": {
		"path": "res://scenes/world/park_shade_tree.tscn",
		"parts": [&"trunk", &"crown_a", &"crown_b"],
		"runtime": false,
	},
	"PRP-PLANT-030": {
		"path": "res://scenes/world/forest_conifer_tree.tscn",
		"parts": [&"trunk", &"lower_crown", &"upper_crown"],
		"runtime": false,
	},
	"PRP-PLANT-031": {
		"path": "res://scenes/world/forest_broadleaf_tree.tscn",
		"parts": [&"trunk", &"crown"],
		"runtime": false,
	},
	"PRP-PLANT-032": {
		"path": "res://scenes/world/mature_grove_tree.tscn",
		"parts": [&"trunk", &"crown_a", &"crown_b", &"crown_c"],
		"runtime": false,
	},
	"PRP-PLANT-041": {
		"path": "res://scenes/world/coastal_douglas_fir.tscn",
		"parts": [&"trunk_lower", &"trunk_mid", &"trunk_upper"],
		"runtime": false,
	},
}

var _fails: Array[String] = []


func _ready() -> void:
	for label in SOURCES:
		_check_source(String(label), SOURCES[label])
	await _check_palm_specimen()
	_check_redwood_family()
	_check_coastal_douglas_fir()
	_check_range_forest_handoff()
	if _fails.is_empty():
		print("PASS: the distinct-background recovery source is mounted once and remains editable; foreground and detailed range trees remain absent")
	else:
		for failure in _fails:
			push_error(failure)
	get_tree().quit(1 if not _fails.is_empty() else 0)


func _check_source(label: String, record: Dictionary) -> void:
	var packed := load(String(record["path"])) as PackedScene
	if packed == null:
		_fails.append("%s source does not load: %s" % [label, record["path"]])
		return
	var tree := packed.instantiate() as Node3D
	if tree == null:
		_fails.append("%s source root is not Node3D" % label)
		return
	if tree.get_script() != null:
		_fails.append("%s source must stay directly editable without a geometry-owning script" % label)
	for part_name in record["parts"]:
		var part := tree.get_node_or_null(NodePath(String(part_name))) as MeshInstance3D
		if part == null or part.mesh == null:
			_fails.append("%s is missing selectable mesh part %s" % [label, part_name])
			continue
		if part.get_aabb().size == Vector3.ZERO:
			_fails.append("%s part %s has empty geometry" % [label, part_name])
	tree.free()


func _check_palm_specimen() -> void:
	var packed := load(PALM_SPECIMEN) as PackedScene
	if packed == null:
		_fails.append("GRP-PARK-012 whole-palm specimen does not load")
		return
	var palm := packed.instantiate() as Node3D
	if palm == null:
		_fails.append("GRP-PARK-012 whole-palm specimen root is not Node3D")
		return
	for part_name in [&"lawn_footing", &"trunk", &"crown"]:
		if palm.get_node_or_null(NodePath(String(part_name))) == null:
			_fails.append("GRP-PARK-012 is missing %s" % part_name)
	# The Blender crown, showing the thirteen fronds and nine stubs the
	# specimen was approved with. It chooses its fronds once it is in the tree.
	var crown := palm.get_node_or_null("crown")
	if crown != null:
		add_child(palm)
		for _i in 3:
			await get_tree().process_frame
		var shown := crown.call("shown_counts") as Dictionary \
			if crown.has_method("shown_counts") else {}
		if crown.scene_file_path != "res://scenes/world/palm_crown.tscn" \
				or int(shown.get("live", 0)) != 13 or int(shown.get("remnant", 0)) != 9 \
				or int(shown.get("dead", -1)) != 0 or int(shown.get("density", -1)) != 0:
			_fails.append("GRP-PARK-012 crown is not the Blender palm crown with 13 fronds and 9 stubs; it shows %s" % shown)
		remove_child(palm)
	palm.free()


func _check_redwood_family() -> void:
	var packed := load(REDWOOD_FAMILY) as PackedScene
	if packed == null:
		_fails.append("coastal-redwood family does not load")
		return
	var family := packed.instantiate() as Node3D
	if family == null:
		_fails.append("coastal-redwood family root is not Node3D")
		return
	add_child(family)
	if family.get_script() != null:
		_fails.append("coastal-redwood family must stay directly editor-owned")
	var heights: Array[float] = []
	for variant_name in [&"variant_a", &"variant_b", &"variant_c"]:
		var variant := family.get_node_or_null(NodePath(String(variant_name))) as Node3D
		if variant == null:
			_fails.append("coastal-redwood family is missing %s" % variant_name)
			continue
		for required in [&"buttress", &"lower_trunk", &"upper_trunk"]:
			var part := variant.get_node_or_null(NodePath(String(required))) \
				as MeshInstance3D
			if part == null or part.mesh == null:
				_fails.append("%s is missing selectable %s geometry" % [variant_name, required])
		var leader := variant.get_node_or_null("leader") as Node3D
		if leader == null:
			_fails.append("%s is missing its editable living leader" % variant_name)
		else:
			var leader_sprays := leader.find_children("*", "MeshInstance3D", true, false)
			if leader_sprays.size() < 5:
				_fails.append("%s leader needs five overlapping selectable sprays" % variant_name)
			for node in leader_sprays:
				_check_needle_spray("%s/leader/%s" % [variant_name, node.name], \
					node as MeshInstance3D)
		var branch_count := 0
		var foliage_count := 0
		var found := false
		var minimum := Vector3.ZERO
		var maximum := Vector3.ZERO
		var inverse := variant.global_transform.affine_inverse()
		for child in variant.get_children():
			if String(child.name).begins_with("branch_"):
				branch_count += 1
		for node in variant.find_children("*", "MeshInstance3D", true, false):
			var visual := node as MeshInstance3D
			if String(visual.name).begins_with("foliage_"):
				foliage_count += 1
				_check_needle_spray("%s/%s" % [variant_name, visual.name], visual)
			elif String(visual.name).begins_with("crown_core_"):
				_check_needle_spray("%s/%s" % [variant_name, visual.name], visual)
			var local_transform := inverse * visual.global_transform
			for endpoint in 8:
				var point := local_transform * visual.get_aabb().get_endpoint(endpoint)
				if not found:
					minimum = point
					maximum = point
					found = true
				else:
					minimum = minimum.min(point)
					maximum = maximum.max(point)
		if branch_count < 12 or foliage_count < 22:
			_fails.append("%s needs at least twelve editable branch courses and twenty-two needle sprays" % variant_name)
		var bounds := AABB(minimum, maximum - minimum) if found else AABB()
		if bounds.size.y < 22.0 or maxf(bounds.size.x, bounds.size.z) < 5.5:
			_fails.append("%s does not read as a tall, spreading redwood silhouette" % variant_name)
		heights.append(bounds.size.y)
	if heights.size() == 3 and (heights[0] < heights[1] + 3.0 \
			or heights[2] < heights[1] + 1.0):
		_fails.append("redwood age and exposure variants do not have distinct height profiles")
	remove_child(family)
	family.free()


func _check_coastal_douglas_fir() -> void:
	var packed := load("res://scenes/world/coastal_douglas_fir.tscn") as PackedScene
	if packed == null:
		_fails.append("PRP-PLANT-041 coastal Douglas fir source does not load")
		return
	var fir := packed.instantiate() as Node3D
	if fir == null:
		_fails.append("PRP-PLANT-041 source root is not Node3D")
		return
	add_child(fir)
	if fir.get_script() != null:
		_fails.append("PRP-PLANT-041 must stay directly editor-owned")
	var branches := fir.get_node_or_null("branches")
	var needles := fir.get_node_or_null("needles")
	if branches == null or branches.find_children("*", "MeshInstance3D", true, false).size() < 40:
		_fails.append("PRP-PLANT-041 needs at least forty selectable branch pieces")
	var needle_visuals: Array[Node] = []
	if needles != null:
		needle_visuals = needles.find_children("*", "MeshInstance3D", true, false)
	if needle_visuals.size() < 50:
		_fails.append("PRP-PLANT-041 needs at least fifty selectable needle sprays")
	for node in needle_visuals:
		_check_needle_spray("PRP-PLANT-041/%s" % node.name, node as MeshInstance3D)
	var bounds := _mesh_bounds(fir)
	if bounds.size.y < 19.0:
		_fails.append("PRP-PLANT-041 is not tall enough to read as the mature reference tree")
	if maxf(bounds.size.x, bounds.size.z) < 8.0:
		_fails.append("PRP-PLANT-041 crown does not carry the reference's long lower boughs")
	remove_child(fir)
	fir.free()


func _check_needle_spray(label: String, visual: MeshInstance3D) -> void:
	if visual == null or visual.mesh == null:
		_fails.append("%s has no needle geometry" % label)
		return
	if visual.mesh is PrismMesh:
		_fails.append("%s has fallen back to a solid prism pad" % label)
		return
	if not visual.mesh is ArrayMesh:
		_fails.append("%s is not layered needle-spray geometry" % label)
		return
	var mesh_script := visual.mesh.get_script() as Script
	if mesh_script == null or mesh_script.resource_path != NEEDLE_SPRAY_SCRIPT:
		_fails.append("%s does not use the shared inspector-controlled needle spray" % label)
	if visual.mesh.get_surface_count() == 0 or visual.mesh.get_aabb().size == Vector3.ZERO:
		_fails.append("%s needle spray has empty geometry" % label)
	if int(visual.mesh.get("needle_pairs")) < 20 \
			or int(visual.mesh.get("spray_layers")) < 5:
		_fails.append("%s needs at least twenty needle pairs across five layers" % label)


func _mesh_bounds(root: Node3D) -> AABB:
	var found := false
	var minimum := Vector3.ZERO
	var maximum := Vector3.ZERO
	var inverse := root.global_transform.affine_inverse()
	for child in root.find_children("*", "MeshInstance3D", true, false):
		var visual := child as MeshInstance3D
		var local_transform := inverse * visual.global_transform
		for endpoint in 8:
			var point := local_transform * visual.get_aabb().get_endpoint(endpoint)
			if not found:
				minimum = point
				maximum = point
				found = true
			else:
				minimum = minimum.min(point)
				maximum = maximum.max(point)
	return AABB(minimum, maximum - minimum) if found else AABB()


func _check_range_forest_handoff() -> void:
	# Keep both rejected implementations parseable as reversible recovery
	# sources, but neither may own the persistent range composition.
	var forest_script := load(FOREST_SCRIPT) as Script
	if forest_script == null:
		_fails.append("retired range_forest.gd recovery source does not parse")

	var packed := load(CANOPY_SCENE) as PackedScene
	if packed == null:
		_fails.append("rejected range canopy recovery scene does not load")
		return
	var canopy := packed.instantiate() as Node3D
	if canopy == null:
		_fails.append("rejected range canopy recovery root is not Node3D")
		return
	if canopy.get_script() != null:
		_fails.append("rejected range canopy recovery source must remain directly editor-owned")
	for part_name in [
		&"background_canopy_mass",
		&"middle_continuous_canopy_mass",
		&"transition_broken_canopy_surface",
	]:
		var part := canopy.find_child(String(part_name), true, false) as MeshInstance3D
		if part == null or part.mesh == null or part.mesh.get_aabb().size == Vector3.ZERO:
			_fails.append("rejected range canopy recovery source is missing %s" % part_name)
	canopy.free()

	var midground_packed := load(MIDGROUND_PROOF_SCENE) as PackedScene
	if midground_packed == null:
		_fails.append("unmounted midground-only proof scene does not load")
	else:
		var midground_proof := midground_packed.instantiate() as Node3D
		if midground_proof == null:
			_fails.append("unmounted midground-only proof root is not Node3D")
		else:
			if midground_proof.get_script() != null:
				_fails.append("midground-only proof must remain directly editor-owned")
			var midground_part := midground_proof.find_child(
				"middle_continuous_canopy_mass", true, false) as MeshInstance3D
			if midground_part == null or midground_part.mesh == null \
					or midground_part.mesh.get_aabb().size == Vector3.ZERO:
				_fails.append("midground-only proof is missing its continuous mass")
			for forbidden in ["background_canopy_mass", "transition_broken_canopy_surface"]:
				if midground_proof.find_child(forbidden, true, false) != null:
					_fails.append("midground-only proof contains forbidden layer %s" % forbidden)
			midground_proof.free()

	var background_packed := load(BACKGROUND_SCENE) as PackedScene
	if background_packed == null:
		_fails.append("persistent distinct-background range scene does not load")
		return
	var background := background_packed.instantiate() as Node3D
	if background == null:
		_fails.append("persistent distinct-background range root is not Node3D")
		return
	add_child(background)
	if background.get_script() != null:
		_fails.append("persistent distinct-background range scene must remain directly editor-owned")
	# The range's landforms are the world terrain master's since 2026-10-06
	# (tools/blender/world_terrain_join_landforms.py); the range source keeps its forest,
	# canopy and rocks. Since height-grid Stage 2 (2026-10-13) the world terrain mounts the
	# ground as one height grid, `world_ground`, so the range is ground among the rest and
	# its sections are no longer bodies to find by name. Until then each body was measured
	# for its breadth in plan, its relief, its closure down to the world's base and its plan
	# overlap with the next, and fourteen of them had to carry collision. Breadth, closure
	# and overlap only made sense for the pieces. What they stood for is asked of the
	# mounted ground: each section still stands at its relief over its summit, the summits
	# taken from the pieces as they were on 2026-10-13 (`RANGE_SECTIONS`); the range runs
	# on as land from the north section to the southern massif, never down to the water on
	# the line between one summit and the next; the south coast's open water stays open;
	# and every tile under the range carries its collision.
	var landforms := (load("res://scenes/world/world_terrain.tscn") as PackedScene).instantiate() as Node3D
	add_child(landforms)
	var grid := landforms.find_child("world_ground", true, false)
	if grid == null or grid.get_child_count() == 0:
		_fails.append("the world terrain does not mount the ground grid the range stands in")
	else:
		var points := PackedVector2Array()
		for section in RANGE_SECTIONS:
			points.append(section[1])
		points.append(SOUTH_COAST_OPEN_POINT)
		var chain_from := points.size()
		for index in RANGE_SECTIONS.size() - 1:
			var a: Vector2 = RANGE_SECTIONS[index][1]
			var b: Vector2 = RANGE_SECTIONS[index + 1][1]
			var steps := ceili(a.distance_to(b) / 10.0)
			for step in steps + 1:
				points.append(a.lerp(b, float(step) / steps))
		var heights := _grid_heights(grid, points)
		for index in RANGE_SECTIONS.size():
			var section: Array = RANGE_SECTIONS[index]
			var top := heights[index]
			if is_nan(top) or top - Plan.WATER_TOP < float(section[2]):
				_fails.append("the %s stands only %s over the water at its summit %s, under its %.0fm of relief" % [
					section[0], "nothing" if is_nan(top) else "%.1fm" % (top - Plan.WATER_TOP),
					section[1], float(section[2])])
		var water := heights[RANGE_SECTIONS.size()]
		if not is_nan(water) and water > Plan.WATER_TOP:
			_fails.append("the mounted ground stands %.1fm high in established south-coast open water" % water)
		var at := chain_from
		for index in RANGE_SECTIONS.size() - 1:
			var a: Vector2 = RANGE_SECTIONS[index][1]
			var b: Vector2 = RANGE_SECTIONS[index + 1][1]
			var steps := ceili(a.distance_to(b) / 10.0)
			var lowest := INF
			for step in steps + 1:
				var y := heights[at + step]
				lowest = minf(lowest, -INF if is_nan(y) else y)
			at += steps + 1
			if lowest <= Plan.WATER_TOP:
				_fails.append("the range does not run on as land between the %s and the %s" % [
					RANGE_SECTIONS[index][0], RANGE_SECTIONS[index + 1][0]])
		for section in RANGE_SECTIONS:
			var at_summit: Vector2 = section[1]
			var tile := grid.get_node_or_null("x%d_z%d" % [floori(at_summit.x / 1000.0), floori(at_summit.y / 1000.0)])
			if tile == null or tile.find_children("*", "StaticBody3D", true, false).is_empty():
				_fails.append("the ground grid's tile under the %s has no imported collision" % section[0])
	for rejected_name in [
		"background_canopy_mass", "background_middle_ridge", "background_far_ridge",
		"background_distant_range_northeast_connector",
		"background_bald_mountain", "southern_range_mass",
		"southern_range_east_connection",
	]:
		if background.find_child(rejected_name, true, false) != null:
			_fails.append("persistent source retains rejected scenery shell %s" % rejected_name)
	var midground_part := background.find_child("middle_continuous_canopy_mass", true, false) as MeshInstance3D
	var transition_part := background.find_child("transition_broken_canopy_surface", true, false) as MeshInstance3D
	if midground_part == null or midground_part.mesh == null:
		_fails.append("persistent range is missing its midground")
	if transition_part == null or transition_part.mesh == null:
		_fails.append("persistent range is missing its broken transition")
	if midground_part != null and midground_part.mesh != null \
			and transition_part != null and transition_part.mesh != null:
		var middle_bounds := _range_depth_bounds(midground_part)
		var transition_bounds := _range_depth_bounds(transition_part)
		if middle_bounds.x < MIDGROUND_NEAR_DEPTH - 0.01 \
				or middle_bounds.y > MIDGROUND_FAR_DEPTH + 0.01:
			_fails.append("persistent midground exceeds its 0-164m depth band")
		if transition_bounds.x < TRANSITION_NEAR_DEPTH - 0.01 \
				or transition_bounds.y > TRANSITION_FAR_DEPTH + 0.01:
			_fails.append("persistent transition exceeds its 180-224m depth band")
		if _world_height_bounds(transition_part).y > TRANSITION_MAX_HEIGHT:
			_fails.append("persistent transition is tall enough to read as a continuous shell")
		if transition_bounds.x - middle_bounds.y < 15.99:
			_fails.append("persistent range lost the 16m midground-to-transition gap")
	remove_child(background)
	background.free()
	landforms.free()

	var world_source := FileAccess.get_file_as_string(PARK_WORLD)
	if not world_source.contains(BACKGROUND_SCENE):
		_fails.append("park_world does not mount the persistent distinct-background range scene")
	if world_source.contains(CANOPY_SCENE):
		_fails.append("park_world still mounts the rejected solid range canopy")
	if world_source.contains(MIDGROUND_PROOF_SCENE):
		_fails.append("park_world mounts the midground proof before visual approval")
	if world_source.contains('path="res://scenes/world/range_forest.gd"'):
		_fails.append("park_world still mounts the retired per-tree placeholder")
	var plan_source := FileAccess.get_file_as_string("res://scripts/park_plan.gd")
	var generator_source := FileAccess.get_file_as_string("res://tools/gen_props.gd")
	if plan_source.contains("BALD_MOUNTAIN_OLD") \
			or generator_source.contains("BALD_MOUNTAIN_OLD"):
		_fails.append("the real generated range summit is still suppressed for a retired duplicate")


func _range_depth_bounds(visual: MeshInstance3D) -> Vector2:
	var minimum := INF
	var maximum := -INF
	for surface in visual.mesh.get_surface_count():
		var arrays := visual.mesh.surface_get_arrays(surface)
		if arrays.is_empty():
			continue
		var vertices := arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
		for local_point in vertices:
			var point := visual.global_transform * local_point
			var radial := Vector2(point.x - 40.0, point.z)
			var theta := atan2(radial.y, radial.x)
			var inner := 290.0 + 75.0 * absf(sin(theta))
			var depth := radial.length() - inner
			minimum = minf(minimum, depth)
			maximum = maxf(maximum, depth)
	return Vector2(minimum, maximum)


func _range_material_depth_bounds(visual: MeshInstance3D, material_name: String) -> Vector2:
	var minimum := INF
	var maximum := -INF
	for surface in visual.mesh.get_surface_count():
		var material := visual.mesh.surface_get_material(surface)
		if material == null or material.resource_name != material_name:
			continue
		var arrays := visual.mesh.surface_get_arrays(surface)
		if arrays.is_empty():
			continue
		for local_point in arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array:
			var point := visual.global_transform * local_point
			var radial := Vector2(point.x - 40.0, point.z)
			var theta := atan2(radial.y, radial.x)
			var inner := 290.0 + 75.0 * absf(sin(theta))
			var depth := radial.length() - inner
			minimum = minf(minimum, depth)
			maximum = maxf(maximum, depth)
	return Vector2(minimum, maximum)


func _world_height_bounds(visual: MeshInstance3D) -> Vector2:
	var minimum := INF
	var maximum := -INF
	for surface in visual.mesh.get_surface_count():
		var arrays := visual.mesh.surface_get_arrays(surface)
		if arrays.is_empty():
			continue
		var vertices := arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
		for local_point in vertices:
			var height := (visual.global_transform * local_point).y
			minimum = minf(minimum, height)
			maximum = maxf(maximum, height)
	return Vector2(minimum, maximum)


## The top of the ground grid's tiles over each plan point, or NAN where the grid has
## none (2026-10-13). Each tile is `x{tx}_z{tz}/ground_x{tx}_z{tz}` under `grid`, 1 km
## square from (1000 tx, 1000 tz); its triangles are read once for all its points.
func _grid_heights(grid: Node, points: PackedVector2Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(points.size())
	out.fill(NAN)
	var by_tile := {}
	for index in points.size():
		var tile := "x%d_z%d" % [floori(points[index].x / 1000.0), floori(points[index].y / 1000.0)]
		if not by_tile.has(tile):
			by_tile[tile] = []
		(by_tile[tile] as Array).append(index)
	for tile in by_tile:
		var holder := grid.get_node_or_null(String(tile))
		var mesh := holder.find_child("ground_" + String(tile), true, false) as MeshInstance3D \
			if holder != null else null
		if mesh == null or mesh.mesh == null:
			continue
		var xf := (holder as Node3D).transform * mesh.transform
		for surface in mesh.mesh.get_surface_count():
			var arrays := mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var indices := PackedInt32Array()
			if arrays[Mesh.ARRAY_INDEX] != null:
				indices = arrays[Mesh.ARRAY_INDEX]
			var count := indices.size() if indices.size() > 0 else vertices.size()
			for i in range(0, count, 3):
				var a := xf * vertices[indices[i] if indices.size() > 0 else i]
				var b := xf * vertices[indices[i + 1] if indices.size() > 0 else i + 1]
				var c := xf * vertices[indices[i + 2] if indices.size() > 0 else i + 2]
				var den := (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
				if absf(den) < 1e-9:
					continue
				var lo := Vector2(minf(a.x, minf(b.x, c.x)), minf(a.z, minf(b.z, c.z)))
				var hi := Vector2(maxf(a.x, maxf(b.x, c.x)), maxf(a.z, maxf(b.z, c.z)))
				for index in by_tile[tile]:
					var p := points[index]
					if p.x < lo.x or p.x > hi.x or p.y < lo.y or p.y > hi.y:
						continue
					var l1 := ((b.z - c.z) * (p.x - c.x) + (c.x - b.x) * (p.y - c.z)) / den
					var l2 := ((c.z - a.z) * (p.x - c.x) + (a.x - c.x) * (p.y - c.z)) / den
					if l1 < -1e-6 or l2 < -1e-6 or 1.0 - l1 - l2 < -1e-6:
						continue
					var y := l1 * a.y + l2 * b.y + (1.0 - l1 - l2) * c.y
					out[index] = y if is_nan(out[index]) else maxf(out[index], y)
	return out


func _open_edge_count(visual: MeshInstance3D) -> int:
	var edge_counts := {}
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
			var triangle := [indices[index], indices[index + 1], indices[index + 2]]
			for edge_index in 3:
				var a := _vertex_key(vertices[triangle[edge_index]])
				var b := _vertex_key(vertices[triangle[(edge_index + 1) % 3]])
				var key := a + "|" + b if a < b else b + "|" + a
				edge_counts[key] = int(edge_counts.get(key, 0)) + 1
	var open_edges := 0
	for key in edge_counts:
		# Imported sharp/material seams can duplicate a closed edge four times.
		# A genuinely exposed boundary still has exactly one incident triangle.
		if int(edge_counts[key]) == 1:
			open_edges += 1
	return open_edges


func _vertex_key(point: Vector3) -> String:
	return "%d,%d,%d" % [roundi(point.x * 1000.0), roundi(point.y * 1000.0),
		roundi(point.z * 1000.0)]


func _range_end_grounding(visual: MeshInstance3D) -> Vector2:
	var north_z := INF
	var south_z := -INF
	var points: Array[Vector3] = []
	for surface in visual.mesh.get_surface_count():
		var arrays := visual.mesh.surface_get_arrays(surface)
		if arrays.is_empty():
			continue
		for local_point in arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array:
			var point := visual.global_transform * local_point
			points.append(point)
			north_z = minf(north_z, point.z)
			south_z = maxf(south_z, point.z)
	var north_y := INF
	var south_y := INF
	for point in points:
		if absf(point.z - north_z) < 0.1:
			north_y = minf(north_y, point.y)
		if absf(point.z - south_z) < 0.1:
			south_y = minf(south_y, point.y)
	return Vector2(north_y, south_y)
