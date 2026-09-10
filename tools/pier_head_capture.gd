extends Node

## Player-camera proof for the editor-owned pavilion T-head. The pass checks
## public circulation, fishing separation, marine support and the two protected
## compositions that caused the pier to occupy this bearing in the first place.

const OUTPUT_DIR := "res://documentation/screenshots/pier-head-2026-09-10"
const DECK_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_head_from_stem", "time": [18, 45], "pos": Vector3(-138.0, DECK_Y, 6.0), "yaw": 90.0, "pitch": 4.0},
	{"name": "02_open_t_junction", "time": [18, 45], "pos": Vector3(-146.5, DECK_Y, 6.0), "yaw": 90.0, "pitch": 2.0},
	{"name": "03_north_circulation", "time": [18, 45], "pos": Vector3(-150.5, DECK_Y, -2.0), "yaw": 90.0, "pitch": 1.0},
	{"name": "04_outer_turnaround", "time": [18, 45], "pos": Vector3(-166.0, DECK_Y, -2.0), "yaw": 180.0, "pitch": 1.0},
	{"name": "05_south_fishing_bypass", "time": [18, 45], "pos": Vector3(-150.5, DECK_Y, 14.5), "yaw": 90.0, "pitch": 1.0},
	{"name": "06_south_return", "time": [18, 45], "pos": Vector3(-166.0, DECK_Y, 14.5), "yaw": -90.0, "pitch": 2.0},
	{"name": "07_marine_support", "time": [18, 45], "pos": Vector3(-107.0, DECK_Y, -16.0), "yaw": 114.0, "pitch": -5.0},
	{"name": "08_west_arch_reveal", "time": [19, 0], "pos": Vector3(ParkPlan.ARCH_RIM_CLEAR_X, 0.2, -2.0), "yaw": 92.0, "pitch": 7.0},
	{"name": "09_sunset_pier", "time": [20, 20], "pos": Vector3(-98.0, DECK_Y, ParkPlan.PIER_Z), "yaw": 90.0, "pitch": 4.0},
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
		push_error("pier_head_capture: no player")
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
