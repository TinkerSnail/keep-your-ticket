extends Node

## Player-camera proof for the directly editor-owned Boardwalk streetwall.
## The pass checks each primary building silhouette, the complete frontage
## rhythm, Q3 and the scheduled twilight/after-close lighting handoff.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-architecture-2026-09-10"
const SHORE_STAND_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_i2_arcade_front", "time": [18, 45], "pos": Vector3(-98.0, SHORE_STAND_Y, -29.0), "yaw": -90.0, "pitch": 5.0},
	{"name": "02_i2_arcade_oblique", "time": [18, 45], "pos": Vector3(-98.0, SHORE_STAND_Y, -38.0), "yaw": -55.0, "pitch": 5.0},
	{"name": "03_i3_cafe_rear_window", "time": [18, 45], "pos": Vector3(-68.5, SHORE_STAND_Y, -38.0), "yaw": 60.0, "pitch": 6.0},
	{"name": "04_i3_cafe_roof_and_service", "time": [18, 45], "pos": Vector3(-68.5, SHORE_STAND_Y, -57.0), "yaw": 125.0, "pitch": 7.0},
	{"name": "05_b1_b2_north_midway", "time": [18, 45], "pos": Vector3(-98.0, SHORE_STAND_Y, -15.0), "yaw": -90.0, "pitch": 6.0},
	{"name": "06_b3_b4_south_midway", "time": [18, 45], "pos": Vector3(-98.0, SHORE_STAND_Y, 13.0), "yaw": -90.0, "pitch": 6.0},
	{"name": "07_streetwall_context", "time": [19, 15], "pos": Vector3(-99.0, SHORE_STAND_Y, -37.0), "yaw": 172.0, "pitch": 3.0},
	{"name": "08_twilight_practicals", "time": [21, 15], "pos": Vector3(-99.0, SHORE_STAND_Y, -22.0), "yaw": -72.0, "pitch": 5.0},
	{"name": "09_after_close_arcade", "time": [22, 15], "pos": Vector3(-98.0, SHORE_STAND_Y, -29.0), "yaw": -90.0, "pitch": 4.0},
	{"name": "10_q3_remains_open", "time": [19, 0], "pos": Vector3(-102.0, SHORE_STAND_Y, -2.0), "yaw": -90.0, "pitch": 5.0},
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
		push_error("boardwalk_architecture_capture: no player")
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
