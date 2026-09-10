extends Node

## Player-camera proof for Boardwalk planting and middle-scale prop density.
## Frames verify that the public fixtures occupy edge bands, that Q3 stays open,
## and that pier safety hardware does not narrow its approach or turnaround.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-density-2026-09-09"
const SHORE_STAND_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_north_terminal_edge", "time": [18, 30], "pos": Vector3(-100.0, SHORE_STAND_Y, -69.0), "yaw": -42.0, "pitch": 2.0},
	{"name": "02_cafe_arcade_amenities", "time": [18, 30], "pos": Vector3(-100.0, SHORE_STAND_Y, -43.0), "yaw": -90.0, "pitch": 2.0},
	{"name": "03_q3_remains_open", "time": [18, 45], "pos": Vector3(-102.0, SHORE_STAND_Y, -2.0), "yaw": -90.0, "pitch": 5.0},
	{"name": "04_south_frontage_amenities", "time": [18, 45], "pos": Vector3(-101.0, SHORE_STAND_Y, 47.0), "yaw": -90.0, "pitch": 2.0},
	{"name": "05_rail_furniture_strip", "time": [19, 0], "pos": Vector3(-100.0, SHORE_STAND_Y, -58.0), "yaw": 164.0, "pitch": 2.0},
	{"name": "06_pier_route_and_hardware", "time": [19, 0], "pos": Vector3(-111.0, SHORE_STAND_Y, 6.0), "yaw": 90.0, "pitch": 2.0},
	{"name": "07_pier_return_route", "time": [19, 0], "pos": Vector3(-146.0, SHORE_STAND_Y, 6.0), "yaw": -90.0, "pitch": 2.0},
	{"name": "08_after_close_amenities", "time": [22, 15], "pos": Vector3(-100.0, SHORE_STAND_Y, 47.0), "yaw": -90.0, "pitch": 3.0},
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
		push_error("boardwalk_density_capture: no player")
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
