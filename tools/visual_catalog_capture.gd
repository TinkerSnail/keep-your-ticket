extends Node

## Captures the roster catalog from the real persistent park. The Python
## companion owns the inventory and target plan; this tool owns only rendering.

const PLAN_PATH := "res://documentation/visual-catalog/capture-plan.json"
const OUTPUT_DIR := "res://documentation/visual-catalog/images"
const COMPLETE_PATH := "res://documentation/visual-catalog/capture-complete.json"
const SETTLE_SECONDS := 6.0


func _ready() -> void:
	print("visual catalog: reading capture plan")
	var plan := _read_plan()
	if plan.is_empty():
		get_tree().quit(2)
		return

	print("visual catalog: loading persistent park")
	var main_scene: PackedScene = load("res://scenes/main/main.tscn")
	print("visual catalog: instantiating persistent park")
	var main: Node = main_scene.instantiate()
	add_child(main)
	print("visual catalog: persistent park mounted")
	ParkClock.running = false
	ParkClock.set_clock(15, 30)

	var hud: CanvasLayer = main.get_node_or_null("hud") as CanvasLayer
	if hud != null:
		hud.visible = false
	var menu: CanvasLayer = main.get_node_or_null("park_menu") as CanvasLayer
	if menu != null:
		menu.visible = false
	var player: Node3D = main.get_node_or_null("player") as Node3D
	if player != null:
		player.hide()
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_process(false)
		crowd.set_physics_process(false)
	for guest in get_tree().get_nodes_in_group("guest"):
		guest.queue_free()

	var sun: DirectionalLight3D = main.get_node_or_null("sun") as DirectionalLight3D
	if sun != null:
		sun.directional_shadow_max_distance = 800.0

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	await get_tree().create_timer(SETTLE_SECONDS).timeout
	print("visual catalog: settled; rendering %d views" % plan.get("shots", []).size())

	var camera := Camera3D.new()
	camera.name = "visual_catalog_camera"
	camera.far = 1800.0
	camera.fov = 46.0
	add_child(camera)
	camera.current = true

	for shot in plan.get("shots", []):
		await _capture(camera, shot)
	_write_completion(plan)
	get_tree().quit()


func _read_plan() -> Dictionary:
	if not FileAccess.file_exists(PLAN_PATH):
		push_error("missing %s; run visual_catalog.py prepare first" % PLAN_PATH)
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(PLAN_PATH))
	if not parsed is Dictionary or not parsed.has("shots"):
		push_error("invalid visual catalog plan")
		return {}
	return parsed


func _capture(camera: Camera3D, shot: Dictionary) -> void:
	var raw_target: Array = shot["target"]
	var target := Vector3(float(raw_target[0]), float(raw_target[1]), float(raw_target[2]))
	var extent := float(shot["extent"])
	var distance := maxf(18.0, extent * 1.25)
	if shot.has("position"):
		var raw_position: Array = shot["position"]
		camera.global_position = Vector3(float(raw_position[0]), float(raw_position[1]), float(raw_position[2]))
	else:
		var direction := Vector2(0.72, 1.0)
		if shot.has("direction"):
			var raw_direction: Array = shot["direction"]
			direction = Vector2(float(raw_direction[0]), float(raw_direction[1])).normalized()
		var height_scale := float(shot.get("height_scale", 0.46))
		camera.global_position = target + Vector3(direction.x * distance, maxf(9.0, extent * height_scale), direction.y * distance)
	camera.look_at(target, Vector3.UP)
	for _frame in 5:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	image.resize(640, 360, Image.INTERPOLATE_LANCZOS)
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["key"]]
	var error := image.save_png(path)
	if error != OK:
		push_error("could not save %s: %s" % [path, error_string(error)])
	else:
		print("saved ", path)


func _write_completion(plan: Dictionary) -> void:
	var file := FileAccess.open(COMPLETE_PATH, FileAccess.WRITE)
	if file == null:
		push_error("could not write visual catalog completion marker")
		return
	file.store_string(JSON.stringify({
		"request_id": plan.get("request_id", ""),
		"shot_count": plan.get("shots", []).size(),
	}) + "\n")
