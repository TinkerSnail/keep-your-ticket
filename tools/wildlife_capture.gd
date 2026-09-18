extends Node

## Runtime visual proof for the persistent wildlife layer. Close frames show the
## authored models in their mounted places; short sequences show motion that a
## single still cannot prove.

const OUTPUT_DIR := "res://documentation/screenshots/wildlife-gull-refresh-2026-09-13"

var _world: Node3D
var _camera: Camera3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	ParkClock.running = false
	ParkClock.set_clock(10, 15)
	await get_tree().create_timer(5.0).timeout

	_world = get_node_or_null("main/park_world") as Node3D
	if _world == null:
		push_error("wildlife_capture: no mounted park world")
		get_tree().quit(1)
		return

	var hud := get_node_or_null("main/hud") as CanvasLayer
	if hud != null:
		hud.visible = false
	var park_menu := get_node_or_null("main/park_menu") as CanvasLayer
	if park_menu != null:
		park_menu.visible = false
	var weather := get_node_or_null("main/weather") as Node3D
	if weather != null:
		weather.visible = false
		weather.process_mode = Node.PROCESS_MODE_DISABLED
	_camera = Camera3D.new()
	_camera.name = "wildlife_proof_camera"
	_camera.fov = 64.0
	_camera.near = 0.05
	_camera.far = 400.0
	add_child(_camera)
	_camera.current = true

	var ground_birds: Array[Node] = []
	var flight_birds: Array[Node] = []
	for bird in get_tree().get_nodes_in_group("wildlife"):
		if bird.get("starts_airborne"):
			flight_birds.append(bird)
		else:
			ground_birds.append(bird)
		bird.set_physics_process(false)

	await _shoot_bird("01_pier_adult", _bird("pier_adult"), Vector3(2.2, 1.1, 2.7), 50.0)
	# The juvenile stands behind the pier rail from the park side. Lift this
	# runtime-only proof camera so the rail still locates the bird without hiding
	# the mottled body and pink legs.
	await _shoot_bird("02_pier_juvenile", _bird("pier_juvenile"), Vector3(2.2, 2.1, -2.5), 50.0)
	await _shoot_group("03_plaza_pigeons", Vector3(-11.5, 1.7, 24.5), Vector3(-15.4, 0.35, 19.8), 55.0)

	var flush_bird := _bird("fountain_edge_a")
	if flush_bird == null:
		push_error("wildlife_capture: no fountain_edge_a")
		get_tree().quit(1)
		return
	_camera.global_position = Vector3(-8.7, 2.0, 26.2)
	_camera.fov = 68.0
	_camera.look_at(Vector3(-16.8, 1.2, 18.0), Vector3.UP)
	await _save("04_flush_before")
	flush_bird.set_physics_process(true)
	flush_bird.call("scare_from", flush_bird.global_position + Vector3(2.0, 0.0, 0.0))
	await get_tree().create_timer(0.65).timeout
	await _save("05_flush_rise")
	await get_tree().create_timer(0.75).timeout
	await _save("06_flush_crossing")
	flush_bird.set_physics_process(false)

	for bird in flight_birds:
		bird.set_physics_process(true)
	_camera.global_position = Vector3(-103.0, 1.6, 1.0)
	_camera.fov = 70.0
	_camera.look_at(Vector3(-145.0, 21.0, -7.0), Vector3.UP)
	await get_tree().create_timer(0.8).timeout
	await _save("07_waterfront_circle_first")
	await get_tree().create_timer(1.2).timeout
	await _save("08_waterfront_circle_second")
	for bird in flight_birds:
		bird.set_physics_process(false)

	await _shoot_open_beak("09_pier_adult_beak_open", _bird("pier_adult"),
		Vector3(1.7, 0.82, 2.0), 43.0)
	await _shoot_open_beak("10_pier_juvenile_beak_open", _bird("pier_juvenile"),
		Vector3(1.7, 1.75, -1.9), 43.0)
	await _shoot_open_beak("11_plaza_pigeon_beak_open", _bird("fountain_edge_b"),
		Vector3(1.15, 0.65, 1.35), 39.0)

	for bird in ground_birds:
		bird.set_physics_process(true)
	for bird in flight_birds:
		bird.set_physics_process(true)
	get_tree().quit()


func _bird(node_name: StringName) -> Node3D:
	for bird in get_tree().get_nodes_in_group("wildlife"):
		if bird.name == node_name:
			return bird as Node3D
	return null


func _shoot_bird(label: String, bird: Node3D, camera_offset: Vector3, fov: float) -> void:
	if bird == null:
		push_error("wildlife_capture: missing bird for %s" % label)
		return
	_camera.global_position = bird.global_position + camera_offset
	_camera.fov = fov
	var toward_camera := _camera.global_position - bird.global_position
	bird.rotation.y = atan2(-toward_camera.x, -toward_camera.z) + 0.45
	_camera.look_at(bird.global_position + Vector3.UP * 0.42, Vector3.UP)
	await _save(label)


func _shoot_group(label: String, position: Vector3, target: Vector3, fov: float) -> void:
	_camera.global_position = position
	_camera.fov = fov
	_camera.look_at(target, Vector3.UP)
	await _save(label)


func _shoot_open_beak(label: String, bird: Node3D, camera_offset: Vector3, fov: float) -> void:
	if bird == null:
		push_error("wildlife_capture: missing bird for %s" % label)
		return
	bird.call("set_beak_open", 1.0)
	await _shoot_bird(label, bird, camera_offset, fov)
	bird.call("set_beak_open", 0.0)
	bird.call("clear_beak_pose")


func _save(label: String) -> void:
	for _i in 4:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [OUTPUT_DIR, label]
	var error := get_viewport().get_texture().get_image().save_png(path)
	if error != OK:
		push_error("wildlife_capture: could not save %s (%s)" % [path, error])
	else:
		print("saved ", path)
