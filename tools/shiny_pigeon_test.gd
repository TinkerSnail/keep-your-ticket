extends Node

## Focused source and mission-boundary check for the special shiny pigeon.


func _ready() -> void:
	var scene := load("res://scenes/wildlife/shiny_pigeon.tscn") as PackedScene
	if scene == null:
		_fail("shiny-pigeon wrapper did not load")
		return
	var pigeon := scene.instantiate()
	add_child(pigeon)
	await get_tree().process_frame
	var failures: Array[String] = []
	_expect(pigeon.name == &"shiny_pigeon", "mission subject has the wrong scene identity", failures)
	_expect(pigeon.is_in_group("mission_subject"), "shiny pigeon is not marked as a mission subject", failures)
	_expect(bool(pigeon.get_meta("mission_only", false)), "shiny pigeon is not marked mission-only", failures)
	_expect(pigeon.get_meta("subject_id", &"") == &"shiny_pigeon", "shiny-pigeon subject id is missing", failures)
	var wildlife_text := FileAccess.get_file_as_string("res://scenes/wildlife/wildlife.tscn")
	_expect(not wildlife_text.contains("shiny_pigeon") and not wildlife_text.contains("white_pigeon.glb"),
		"shiny pigeon leaked into ordinary wildlife placement", failures)

	var root := pigeon.call("get_pose_root") as Node3D
	_expect(root != null, "shiny-pigeon pose root is missing", failures)
	if root != null:
		for path in ["body", "head_pivot/head", "head_pivot/neck",
			"head_pivot/beak/cere_left", "head_pivot/beak/cere_right",
			"wing_left/folded_overlay", "wing_right/folded_overlay_001", "tail"]:
			_expect(root.get_node_or_null(path) != null,
				"shiny pigeon is missing %s" % path, failures)
		for descendant in root.find_children("*", "MeshInstance3D", true, false):
			var mesh_instance := descendant as MeshInstance3D
			_expect(not mesh_instance.mesh is SphereMesh,
				"shiny pigeon regressed to a SphereMesh at %s" % root.get_path_to(mesh_instance), failures)
			for surface_index in mesh_instance.mesh.get_surface_count():
				var material := mesh_instance.mesh.surface_get_material(surface_index) as BaseMaterial3D
				_expect(material != null and material.albedo_texture != null,
					"shiny-pigeon surface lacks its packed texture at %s" % root.get_path_to(mesh_instance), failures)
	pigeon.call("scare_from", pigeon.global_position + Vector3(0.5, 0.0, 0.0))
	await get_tree().process_frame
	_expect(bool(pigeon.call("is_flying")), "shiny pigeon did not retain flush response", failures)
	if root != null:
		for path in ["wing_left/folded_overlay", "wing_right/folded_overlay_001",
			"wing_left/outer_pivot/outer_folded_overlay",
			"wing_right/outer_pivot_001/outer_folded_overlay_001"]:
			var overlay := root.get_node_or_null(path) as Node3D
			_expect(overlay != null and not overlay.visible,
				"shiny-pigeon folded overlay did not hide in flight at %s" % path, failures)
	pigeon.queue_free()
	if failures.is_empty():
		print("PASS: independent shiny-pigeon mission subject, packed textures and wing-state behavior")
		get_tree().quit()
		return
	for failure in failures:
		printerr("FAIL: ", failure)
	get_tree().quit(1)


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)


func _fail(message: String) -> void:
	printerr("FAIL: ", message)
	get_tree().quit(1)
