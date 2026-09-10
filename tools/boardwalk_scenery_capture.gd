extends Node

## Player-camera proof for the first editor-owned Boardwalk scenery pass.
## The frames ask whether the two recurring interiors and four midway units are
## now distinct places while Q3 remains a clean opening to the protected stair.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-fidelity-2026-09-09"
const SHORE_STAND_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_i2_arcade_front", "time": [19, 0], "pos": Vector3(-98, SHORE_STAND_Y, -29), "yaw": -90.0, "pitch": 2.0},
	{"name": "02_i2_floor_spine", "time": [19, 0], "pos": Vector3(-86.5, SHORE_STAND_Y, -29), "yaw": -90.0, "pitch": 0.0},
	{"name": "03_i3_cafe_front", "time": [19, 0], "pos": Vector3(-76, ParkPlan.SHORE_TOP + 1.35, -57), "yaw": 150.0, "pitch": 2.0},
	{"name": "04_north_midway_pair", "time": [19, 0], "pos": Vector3(-98, SHORE_STAND_Y, -15), "yaw": -90.0, "pitch": 3.0},
	{"name": "05_south_midway_pair", "time": [19, 0], "pos": Vector3(-98, SHORE_STAND_Y, 13), "yaw": -90.0, "pitch": 3.0},
	{"name": "06_q3_opening", "time": [19, 0], "pos": Vector3(-102, SHORE_STAND_Y, -2), "yaw": -90.0, "pitch": 6.0},
	{"name": "07_strip_context", "time": [19, 30], "pos": Vector3(-99, SHORE_STAND_Y, -37), "yaw": 172.0, "pitch": 3.0},
	{"name": "08_powered_after_close", "time": [22, 15], "pos": Vector3(-98, SHORE_STAND_Y, -23), "yaw": -35.0, "pitch": 3.0},
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
		push_error("boardwalk_scenery_capture: no player")
		get_tree().quit(1)
		return
	_head = _player.get_node("head") as Node3D
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
