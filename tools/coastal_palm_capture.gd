extends Node

## Player-camera proof for the editor-owned coastal palm sources and footing.
## Arrival frames show the dense classic-California pinnate crown and layered
## planting; long frames guard the open allée and lush
## curb-bed continuity.

const OUTPUT_DIR := "res://documentation/screenshots/arrival-dense-california-palms-2026-09-11"
const SHORE_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_boardwalk_close_crown", "time": [18, 30], "pos": Vector3(-99.0, SHORE_Y, -52.0), "yaw": 90.0, "pitch": 27.0},
	{"name": "02_boardwalk_row", "time": [18, 30], "pos": Vector3(-97.0, SHORE_Y, -48.0), "yaw": 43.0, "pitch": 15.0},
	{"name": "03_wheel_and_palms", "time": [18, 45], "pos": Vector3(-98.0, SHORE_Y, 42.0), "yaw": 42.0, "pitch": 12.0},
	{"name": "04_q3_remains_open", "time": [18, 45], "pos": Vector3(-102.0, SHORE_Y, -2.0), "yaw": 90.0, "pitch": 7.0},
	{"name": "05_arrival_allee_northbound", "time": [17, 30], "pos": Vector3(0.0, 0.2, 220.0), "yaw": 0.0, "pitch": 10.0},
	{"name": "06_arrival_allee_southbound", "time": [17, 30], "pos": Vector3(0.0, 0.2, 145.0), "yaw": 180.0, "pitch": 9.0},
	{"name": "07_arrival_close_crown", "time": [17, 30], "pos": Vector3(0.0, 0.2, 199.0), "yaw": 90.0, "pitch": 25.0},
	{"name": "08_front_road_row", "time": [17, 30], "pos": Vector3(0.0, 0.2, 228.0), "yaw": 158.0, "pitch": 11.0},
	{"name": "09_boardwalk_flared_base", "time": [18, 30], "pos": Vector3(-100.5, SHORE_Y, -52.0), "yaw": 90.0, "pitch": -7.0},
	{"name": "10_arrival_pair_arch", "time": [17, 30], "pos": Vector3(0.0, 0.2, 218.0), "yaw": 0.0, "pitch": 18.0},
	{"name": "11_arrival_soil_and_flowers", "time": [17, 30], "pos": Vector3(5.0, 0.2, 212.0), "yaw": 90.0, "pitch": -16.0},
	{"name": "12_arrival_layered_curb_bed", "time": [17, 30], "pos": Vector3(0.0, 0.2, 196.0), "yaw": 90.0, "pitch": -10.0},
	{"name": "13_arrival_lush_curb_rows", "time": [17, 30], "pos": Vector3(0.0, 0.2, 221.0), "yaw": 0.0, "pitch": -4.0},
	{"name": "14_fern_pinnae_close", "time": [17, 30], "pos": Vector3(10.0, 0.2, 212.1), "yaw": 90.0, "pitch": -45.0},
	{"name": "15_purple_heart_accent", "time": [17, 30], "pos": Vector3(10.5, 0.2, 211.0), "yaw": 90.0, "pitch": -28.0},
	{"name": "16_arrival_palm_bed_close", "time": [17, 30], "pos": Vector3(-9.2, 0.2, 211.2), "yaw": 90.0, "pitch": -32.0},
]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	ParkClock.running = false
	await get_tree().create_timer(5.0).timeout
	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("coastal_palm_capture: no player")
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
