extends Node

## Player-camera proof for the editor-owned Boardwalk creek/water-edge pass.
## The sequence follows D2 downhill, checks both crossings and the culvert, then
## proves the controlled outfall, shoreline wear and protected open-water view.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-water-edges-2026-09-09"
const SHOTS := [
	{"name": "01_creek_daylight", "time": [16, 30], "pos": Vector3(-53.0, 0.2, 29.0), "yaw": 151.0, "pitch": 10.0},
	{"name": "02_cx1_service_culvert", "time": [16, 45], "pos": Vector3(-56.0, -0.8, 34.5), "yaw": 150.0, "pitch": 5.0},
	{"name": "03_cb1_and_rain_pond", "time": [17, 0], "pos": Vector3(-73.0, -3.7, 43.5), "yaw": 158.0, "pitch": 6.0},
	{"name": "04_cb2_creek_crossing", "time": [17, 15], "pos": Vector3(-101.0, -5.8, 46.0), "yaw": -132.0, "pitch": 5.0},
	{"name": "05_controlled_outfall", "time": [17, 30], "pos": Vector3(-104.5, -5.8, 56.65), "yaw": 90.0, "pitch": -24.0},
	{"name": "06_waterline_transition", "time": [18, 0], "pos": Vector3(-101.0, -5.8, 70.0), "yaw": 63.0, "pitch": 1.0},
	{"name": "07_q3_open_water", "time": [19, 0], "pos": Vector3(-99.5, -5.8, 8.0), "yaw": 90.0, "pitch": 1.0},
	{"name": "08_outfall_after_close", "time": [22, 15], "pos": Vector3(-104.5, -5.8, 56.65), "yaw": 90.0, "pitch": -22.0},
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
		push_error("boardwalk_water_edges_capture: no player")
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
