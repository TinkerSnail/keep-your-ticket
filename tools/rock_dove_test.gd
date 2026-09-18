extends Node

## Focused source-handoff check for the atlas-wrapped rock dove. This is
## separate from wildlife_test so the active gull refinement can continue
## without either session rewriting the other's acceptance work.


func _ready() -> void:
	var scene := load("res://scenes/wildlife/rock_dove.tscn") as PackedScene
	if scene == null:
		_fail("rock-dove wrapper did not load")
		return
	var pigeon := scene.instantiate()
	add_child(pigeon)
	await get_tree().process_frame
	var failures: Array[String] = []
	var root := pigeon.call("get_pose_root") as Node3D
	_expect(bool(pigeon.get("model_has_authored_plumage")),
		"rock dove is not marked as authored plumage", failures)
	_expect(root != null, "rock-dove pose root is missing", failures)
	if root != null:
		_check_form(root, failures)
		_check_texture(root, failures)
		_check_region(root.get_node_or_null("head_pivot/neck") as MeshInstance3D,
			Vector2(0.50, 0.75), Vector2(0.75, 1.00), "neck", failures)
		_check_region(root.get_node_or_null("tail") as MeshInstance3D,
			Vector2(0.50, 0.50), Vector2(0.75, 0.75), "tail", failures)
		_check_wing_regions(root, failures)
	_check_bill_pose(pigeon, failures)
	pigeon.call("scare_from", pigeon.global_position + Vector3(0.5, 0.0, 0.0))
	_expect(bool(pigeon.call("is_flying")), "rock dove did not retain flush response", failures)
	await get_tree().process_frame
	_check_flight_overlays(root, failures)
	pigeon.queue_free()
	if failures.is_empty():
		print("PASS: editable rock-dove model, UV atlas regions, articulated bill and flush behavior")
		get_tree().quit()
		return
	for failure in failures:
		printerr("FAIL: ", failure)
	get_tree().quit(1)


func _check_form(root: Node3D, failures: Array[String]) -> void:
	var body := root.get_node_or_null("body") as MeshInstance3D
	_expect(body != null and body.mesh is ArrayMesh,
		"rock dove lacks its single authored pear body", failures)
	for path in ["head_pivot", "head_pivot/beak/upper_pivot",
		"head_pivot/beak/lower_pivot", "head_pivot/beak/cere_left",
		"head_pivot/beak/cere_right", "wing_left", "wing_right",
		"leg_left", "leg_right", "tail"]:
		_expect(root.get_node_or_null(path) != null, "rock dove is missing %s" % path, failures)
	for descendant in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		_expect(not mesh_instance.mesh is SphereMesh,
			"rock dove regressed to primitive sphere construction at %s" % root.get_path_to(mesh_instance), failures)


func _check_texture(root: Node3D, failures: Array[String]) -> void:
	var surfaces := 0
	var uv_surfaces := 0
	var textured_surfaces := 0
	for descendant in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		if mesh_instance.mesh == null:
			continue
		for surface_index in mesh_instance.mesh.get_surface_count():
			surfaces += 1
			if mesh_instance.mesh.surface_get_format(surface_index) & Mesh.ARRAY_FORMAT_TEX_UV:
				uv_surfaces += 1
			var material := mesh_instance.mesh.surface_get_material(surface_index) as BaseMaterial3D
			if material != null and material.albedo_texture != null:
				textured_surfaces += 1
	_expect(surfaces > 0, "rock dove contains no visible surfaces", failures)
	_expect(uv_surfaces == surfaces,
		"rock dove has %d of %d surfaces UV-wrapped" % [uv_surfaces, surfaces], failures)
	_expect(textured_surfaces == surfaces,
		"rock dove has %d of %d surfaces using its atlas" % [textured_surfaces, surfaces], failures)


func _check_region(mesh_instance: MeshInstance3D, minimum: Vector2, maximum: Vector2,
		label: String, failures: Array[String]) -> void:
	_expect(mesh_instance != null and mesh_instance.mesh != null,
		"rock dove is missing its %s mesh" % label, failures)
	if mesh_instance == null or mesh_instance.mesh == null:
		return
	var count := 0
	for surface_index in mesh_instance.mesh.get_surface_count():
		var arrays: Array = mesh_instance.mesh.surface_get_arrays(surface_index)
		for uv in arrays[Mesh.ARRAY_TEX_UV] as PackedVector2Array:
			if uv.x > minimum.x and uv.x < maximum.x and uv.y > minimum.y and uv.y < maximum.y:
				count += 1
	_expect(count > 0, "rock-dove %s does not use its dedicated atlas region" % label, failures)


func _check_wing_regions(root: Node3D, failures: Array[String]) -> void:
	var folded_coverts := 0
	var underside := 0
	var folded_primaries := 0
	for descendant in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		var name_string := String(mesh_instance.name)
		for surface_index in mesh_instance.mesh.get_surface_count():
			var arrays: Array = mesh_instance.mesh.surface_get_arrays(surface_index)
			for uv in arrays[Mesh.ARRAY_TEX_UV] as PackedVector2Array:
				if name_string.begins_with("folded_overlay") and uv.x > 0.75 and uv.y > 0.75:
					folded_coverts += 1
				elif (name_string.begins_with("inner_mesh") or name_string.begins_with("outer_mesh")) \
						and uv.x > 0.25 and uv.x < 0.50 and uv.y > 0.50 and uv.y < 0.75:
					underside += 1
				elif name_string.begins_with("outer_folded_overlay") \
						and uv.x < 0.25 and uv.y > 0.50 and uv.y < 0.75:
					folded_primaries += 1
	_expect(folded_coverts > 0,
		"rock-dove closed wings do not use the barred covert region", failures)
	_expect(underside > 0,
		"rock-dove open wings do not use the ventral feather region", failures)
	_expect(folded_primaries > 0,
		"rock-dove closed primary overlays do not use their dark region", failures)


func _check_flight_overlays(root: Node3D, failures: Array[String]) -> void:
	for path in ["wing_left/folded_overlay", "wing_right/folded_overlay_001",
		"wing_left/outer_pivot/outer_folded_overlay",
		"wing_right/outer_pivot_001/outer_folded_overlay_001"]:
		var overlay := root.get_node_or_null(path) as Node3D
		_expect(overlay != null, "rock dove is missing folded-state overlay %s" % path, failures)
		if overlay != null:
			_expect(not overlay.visible,
				"rock-dove folded-state overlay remains visible in flight at %s" % path, failures)


func _check_bill_pose(pigeon: Node, failures: Array[String]) -> void:
	var root := pigeon.call("get_pose_root") as Node3D
	var upper := root.get_node_or_null("head_pivot/beak/upper_pivot") as Node3D
	var lower := root.get_node_or_null("head_pivot/beak/lower_pivot") as Node3D
	_expect(upper != null and lower != null, "rock-dove bill pivots are missing", failures)
	if upper == null or lower == null:
		return
	pigeon.call("set_beak_open", 0.0)
	var upper_closed := upper.rotation.x
	var lower_closed := lower.rotation.x
	pigeon.call("set_beak_open", 1.0)
	_expect(upper.rotation.x > upper_closed, "rock-dove upper bill does not lift", failures)
	_expect(lower.rotation.x < lower_closed, "rock-dove lower bill does not drop", failures)
	pigeon.call("set_beak_open", 0.0)
	pigeon.call("clear_beak_pose")


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)


func _fail(message: String) -> void:
	printerr("FAIL: ", message)
	get_tree().quit(1)
