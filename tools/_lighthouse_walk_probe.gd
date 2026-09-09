extends Node

## Visual proof of the emitted P1 walk from the real player's camera, followed
## by one oblique overview. Traversal itself is guarded by footprint_walk_test;
## these frames answer whether the contour bends and their terrain ribbon read
## as one believable climb rather than paving laid across a hillside.

const OUTPUT_DIR := "user://lighthouse_walk_2026_09_09"
const SETTLE_SECONDS := 6.0

var _player: CharacterBody3D
var _head: Node3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	_clear_previous_frames()
	var output := ProjectSettings.globalize_path(OUTPUT_DIR)
	DirAccess.make_dir_recursive_absolute(output)
	var hud := get_tree().root.find_child("hud", true, false) as CanvasLayer
	if hud != null:
		hud.visible = false
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_process(false)
		crowd.set_physics_process(false)
	for guest in get_tree().get_nodes_in_group("guest"):
		guest.queue_free()
	await get_tree().create_timer(SETTLE_SECONDS).timeout
	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if _player == null:
		push_error("lighthouse walk probe found no real Player")
		get_tree().quit(1)
		return
	_head = _player.get_node("head") as Node3D
	var walk := get_tree().root.find_child("P1_public_access", true, false)
	var points: PackedVector3Array = walk.get_meta("points", PackedVector3Array()) \
		if walk != null else PackedVector3Array()
	if points.size() < 600:
		push_error("lighthouse walk probe found no dense emitted P1 path")
		get_tree().quit(1)
		return
	var shots := [
		["00_from_loop", 0, 100],
		["01_lower_bend", 145, 245],
		["02_middle_bend", 275, 385],
		["03_upper_bend", 425, 540],
		["04_forecourt_arrival", points.size() - 1, 510],
		["05_shore_side", 300, 250],
	]
	for shot in shots:
		await _player_shot(String(shot[0]), points[int(shot[1])],
			points[int(shot[2])])
	await _overview(points)
	get_tree().quit()


func _player_shot(label: String, at: Vector3, target: Vector3) -> void:
	_player.global_position = at + Vector3.UP * 0.30
	_player.velocity = Vector3.ZERO
	for _frame in 30:
		await get_tree().physics_frame
	var to := target + Vector3.UP * 1.2 - _player.global_position
	_player.rotation.y = atan2(-to.x, -to.z)
	_head.rotation.x = atan2(to.y, Vector2(to.x, to.z).length())
	for _frame in 8:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [OUTPUT_DIR, label]
	get_viewport().get_texture().get_image().save_png(path)
	var camera := get_viewport().get_camera_3d()
	print("lighthouse probe wrote %s; body %s; eye %s" % [path,
		_player.global_position, camera.global_position if camera != null else "?"])


func _overview(points: PackedVector3Array) -> void:
	var camera := Camera3D.new()
	add_child(camera)
	camera.far = 1200.0
	camera.fov = 48.0
	camera.global_position = Vector3(-18.0, 145.0, -125.0)
	camera.look_at(points[330] + Vector3.UP * 4.0, Vector3.UP)
	camera.make_current()
	for _frame in 12:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "%s/06_overview.png" % OUTPUT_DIR
	get_viewport().get_texture().get_image().save_png(path)
	print("lighthouse probe wrote ", path)


func _clear_previous_frames() -> void:
	var output := ProjectSettings.globalize_path(OUTPUT_DIR)
	if not DirAccess.dir_exists_absolute(output):
		return
	var directory := DirAccess.open(output)
	for file in directory.get_files():
		if file.get_extension().to_lower() == "png":
			directory.remove(file)
