extends Node

## Focused source and behavior check for the ordinary ash-red pigeon morph.


func _ready() -> void:
	var scene := load("res://scenes/wildlife/ash_red_pigeon.tscn") as PackedScene
	if scene == null:
		_fail("ash-red pigeon scene did not load")
		return
	var pigeon := scene.instantiate()
	add_child(pigeon)
	await get_tree().process_frame
	var failures: Array[String] = []
	_expect(pigeon.name == &"ash_red_pigeon", "morph has the wrong scene identity", failures)
	_expect(pigeon.get_meta("morph", &"") == &"ash_red_cream",
		"ash-red/cream morph identity is missing", failures)
	_expect(not pigeon.is_in_group("mission_subject") and not pigeon.has_meta("mission_only"),
		"ordinary ash-red morph was marked as the shiny mission subject", failures)
	_expect(pigeon.is_in_group("wildlife") and pigeon.is_in_group("pigeon"),
		"ash-red morph did not retain ordinary pigeon groups", failures)
	_expect(bool(pigeon.get("model_has_authored_plumage")),
		"ash-red morph is not marked as authored plumage", failures)

	var expected_material := load(
		"res://assets/wildlife/ash_red_pigeon_plumage.tres") as StandardMaterial3D
	var root := pigeon.call("get_pose_root") as Node3D
	_expect(root != null, "ash-red pigeon pose root is missing", failures)
	if root != null:
		_check_form_and_material(root, expected_material, failures)
		_check_eye_seating(root, failures)
	_check_palette(failures)
	pigeon.call("scare_from", pigeon.global_position + Vector3(0.5, 0.0, 0.0))
	await get_tree().process_frame
	_expect(bool(pigeon.call("is_flying")),
		"ash-red pigeon did not retain flush response", failures)
	if root != null:
		for path in ["wing_left/folded_overlay", "wing_right/folded_overlay_001",
			"wing_left/outer_pivot/outer_folded_overlay",
			"wing_right/outer_pivot_001/outer_folded_overlay_001"]:
			var overlay := root.get_node_or_null(path) as Node3D
			_expect(overlay != null and not overlay.visible,
				"folded overlay did not hide in flight at %s" % path, failures)
	pigeon.queue_free()
	if failures.is_empty():
		print("PASS: independent ash-red/cream rock-dove morph, authored atlas and ordinary flush behavior")
		get_tree().quit()
		return
	for failure in failures:
		printerr("FAIL: ", failure)
	get_tree().quit(1)


func _check_form_and_material(root: Node3D, expected_material: StandardMaterial3D,
		failures: Array[String]) -> void:
	for path in ["body", "head_pivot/head", "head_pivot/neck",
		"head_pivot/beak/upper_pivot", "head_pivot/beak/lower_pivot",
		"head_pivot/beak/cere_left", "head_pivot/beak/cere_right",
		"wing_left/folded_overlay", "wing_right/folded_overlay_001",
		"leg_left", "leg_right", "tail"]:
		_expect(root.get_node_or_null(path) != null, "ash-red pigeon is missing %s" % path, failures)
	for descendant in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		_expect(not mesh_instance.mesh is SphereMesh,
			"ash-red pigeon regressed to a SphereMesh at %s" % root.get_path_to(mesh_instance),
			failures)
		if String(mesh_instance.name).begins_with("cere_"):
			_expect(mesh_instance.material_override == null,
				"pale cere lost its dedicated source material", failures)
		else:
			_expect(mesh_instance.material_override == expected_material,
				"morph atlas is not applied at %s" % root.get_path_to(mesh_instance), failures)


func _check_palette(failures: Array[String]) -> void:
	var texture := load("res://assets/wildlife/ash_red_pigeon_atlas.png") as Texture2D
	_expect(texture != null, "ash-red atlas did not import", failures)
	if texture == null:
		return
	# Sample the authored PNG itself: the imported texture has been VRAM
	# compressed since the editor's Detect 3D pass on 2026-09-15, and a
	# compressed Image cannot answer get_pixel().
	var image := Image.load_from_file(ProjectSettings.globalize_path("res://assets/wildlife/ash_red_pigeon_atlas.png"))
	_expect(image != null and image.get_width() == 1024 and image.get_height() == 1024,
		"ash-red atlas is not the expected 1024px authored texture", failures)
	if image == null or image.get_width() != 1024 or image.get_height() != 1024:
		return
	var chest := image.get_pixel(64, 800)
	var belly := image.get_pixel(64, 990)
	var crown := image.get_pixel(384, 800)
	var cheek := image.get_pixel(384, 960)
	var neck := image.get_pixel(640, 880)
	var wing := image.get_pixel(896, 880)
	var feet := image.get_pixel(128, 384)
	var iris := image.get_pixel(384, 384)
	var beak := image.get_pixel(896, 640)
	var open_wing_tip := image.get_pixel(280, 540)
	var open_wing_root := image.get_pixel(480, 730)
	_expect(chest.r > chest.b + 0.18 and _luma(chest) < _luma(belly),
		"body no longer grades from cinnamon chest to pale lower plumage", failures)
	var cheek_high := maxf(cheek.r, maxf(cheek.g, cheek.b))
	var cheek_low := minf(cheek.r, minf(cheek.g, cheek.b))
	_expect(crown.r > crown.b + 0.18 and cheek_high - cheek_low < 0.15,
		"cinnamon crown no longer fades into restrained warm-gray cheeks", failures)
	_expect(neck.r > neck.b + 0.18 and wing.r > wing.b + 0.18 \
			and _luma(neck) < _luma(wing),
		"cinnamon neck and lighter cinnamon-buff wing shield relationship was lost", failures)
	_expect(feet.r > feet.g + 0.18 and iris.r > iris.g + 0.18,
		"rose feet or red iris no longer carry the reference morph", failures)
	_expect(beak.r > beak.b + 0.18 and beak.g > 0.45,
		"bill no longer reads as pale pink", failures)
	_expect(open_wing_root.r > open_wing_root.b + 0.25 \
			and _luma(open_wing_root) < _luma(open_wing_tip),
		"open wing no longer carries visible cinnamon roots into cream tips", failures)


func _check_eye_seating(root: Node3D, failures: Array[String]) -> void:
	var head := root.get_node("head_pivot/head") as MeshInstance3D
	var head_half_x := head.mesh.get_aabb().size.x * head.scale.x * 0.5
	for side in ["left", "right"]:
		var eye := root.get_node("head_pivot/eye_%s" % side) as MeshInstance3D
		var pupil := root.get_node("head_pivot/pupil_%s" % side) as MeshInstance3D
		var eye_half_x := eye.mesh.get_aabb().size.x * eye.scale.x * 0.5
		var pupil_half_x := pupil.mesh.get_aabb().size.x * pupil.scale.x * 0.5
		_expect(absf(eye.position.x) - eye_half_x < head_half_x - 0.005,
			"%s iris ring is no longer seated into the pale head" % side, failures)
		_expect(absf(pupil.position.x) - pupil_half_x < head_half_x - 0.005,
			"%s pupil is no longer seated into the pale head" % side, failures)


func _luma(color: Color) -> float:
	return color.r * 0.2126 + color.g * 0.7152 + color.b * 0.0722


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)


func _fail(message: String) -> void:
	printerr("FAIL: ", message)
	get_tree().quit(1)
