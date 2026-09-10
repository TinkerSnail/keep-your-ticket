extends Node

## Player-camera proof for the Boardwalk finish pass. The frames ask whether
## restrained material variation, merchandise and caused wear replace blank
## greybox fields without becoming route clutter or obscuring protected views.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-finish-2026-09-09"
const SHORE_STAND_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_i2_photo_and_cladding", "time": [18, 15], "pos": Vector3(-98.0, SHORE_STAND_Y, -29.0), "yaw": -90.0, "pitch": 2.0},
	{"name": "02_i3_cafe_residue", "time": [18, 15], "pos": Vector3(-77.0, ParkPlan.SHORE_TOP + 1.35, -58.0), "yaw": 147.0, "pitch": 4.0},
	{"name": "03_north_midway_merchandise", "time": [18, 30], "pos": Vector3(-98.0, SHORE_STAND_Y, -15.0), "yaw": -90.0, "pitch": 3.0},
	{"name": "04_south_midway_merchandise", "time": [18, 30], "pos": Vector3(-98.0, SHORE_STAND_Y, 13.0), "yaw": -90.0, "pitch": 3.0},
	{"name": "05_p2_face_and_thresholds", "time": [18, 45], "pos": Vector3(-99.0, SHORE_STAND_Y, 32.0), "yaw": -90.0, "pitch": 2.0},
	{"name": "06_pier_finish_and_open_route", "time": [19, 0], "pos": Vector3(-112.0, SHORE_STAND_Y, 6.0), "yaw": 90.0, "pitch": 2.0},
	{"name": "07_q3_finish_context", "time": [19, 0], "pos": Vector3(-102.0, SHORE_STAND_Y, -2.0), "yaw": -90.0, "pitch": 5.0},
	{"name": "08_after_close_practical", "time": [22, 15], "pos": Vector3(-98.0, SHORE_STAND_Y, -11.0), "yaw": -90.0, "pitch": 3.0},
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
		push_error("boardwalk_finish_capture: no player")
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
