extends Node

## Player-camera proof for the editor-owned Boardwalk operations pass.
## Frames cover ride loading, P2's distinct entry/exit, pier fishing work and
## the recently-vacated after-close condition without treating the pier as a destination.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-operations-2026-09-09"
const SHORE_STAND_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_wheel_load_operator", "time": [18, 15], "pos": Vector3(-101.0, SHORE_STAND_Y, -25.0), "yaw": 90.0, "pitch": 3.0},
	{"name": "02_wheel_exit_maintenance", "time": [18, 15], "pos": Vector3(-101.0, SHORE_STAND_Y, -6.0), "yaw": 90.0, "pitch": 3.0},
	{"name": "03_coaster_load_operator", "time": [18, 30], "pos": Vector3(-100.0, SHORE_STAND_Y, -60.0), "yaw": -90.0, "pitch": 3.0},
	{"name": "04_coaster_service_edge", "time": [18, 30], "pos": Vector3(-100.0, SHORE_STAND_Y, -54.0), "yaw": -61.0, "pitch": 2.0},
	{"name": "05_funhouse_entry_exit", "time": [18, 45], "pos": Vector3(-94.5, SHORE_STAND_Y, 32.0), "yaw": -90.0, "pitch": 3.0},
	{"name": "06_funhouse_operator", "time": [18, 45], "pos": Vector3(-86.0, SHORE_STAND_Y, 28.0), "yaw": -90.0, "pitch": 1.0},
	{"name": "07_pier_fishing_work", "time": [19, 0], "pos": Vector3(-151.0, SHORE_STAND_Y, 14.0), "yaw": 90.0, "pitch": 2.0},
	{"name": "08_operations_after_close", "time": [22, 15], "pos": Vector3(-100.0, SHORE_STAND_Y, -60.0), "yaw": -90.0, "pitch": 4.0},
]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run()


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	ParkClock.running = false
	await get_tree().create_timer(5.0).timeout
	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("boardwalk_operations_capture: no player")
		get_tree().quit(1)
		return
	_head = _player.get_node("head") as Node3D
	_player.call("set_third_person", false)
	for shot in SHOTS:
		ParkClock.set_clock(shot["time"][0], shot["time"][1])
		await get_tree().create_timer(1.2).timeout
		await _shoot(shot)
	get_tree().quit()


func _shoot(shot: Dictionary) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 120:
		await get_tree().physics_frame
		if _player.is_on_floor():
			break
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
