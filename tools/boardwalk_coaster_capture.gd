extends Node

## Player-camera proof for the directly editor-owned R2 wooden coaster.
## The frames cover the public station face, lift/catwalk, timber depth,
## Boardwalk broadside, operating lights and the protected west compositions.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-coaster-2026-09-10"
const SHORE_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_station_front", "time": [18, 45], "pos": Vector3(-100.0, SHORE_Y, -60.0), "yaw": -90.0, "pitch": 5.0},
	{"name": "02_station_oblique", "time": [18, 45], "pos": Vector3(-99.0, SHORE_Y, -67.0), "yaw": -70.0, "pitch": 7.0},
	{"name": "03_train_and_brake_bay", "time": [18, 45], "pos": Vector3(-96.5, SHORE_Y, -59.0), "yaw": -90.0, "pitch": 0.0},
	{"name": "04_lift_catwalk", "time": [18, 45], "pos": Vector3(-99.0, SHORE_Y, -74.0), "yaw": -74.0, "pitch": 20.0},
	{"name": "05_timber_bents_from_public_edge", "time": [18, 45], "pos": Vector3(-96.0, SHORE_Y, -80.0), "yaw": -86.0, "pitch": 16.0},
	{"name": "06_pier_broadside", "time": [19, 10], "pos": Vector3(-151.0, SHORE_Y, 6.0), "yaw": -22.0, "pitch": 9.0},
	{"name": "07_boardwalk_skyline", "time": [19, 10], "pos": Vector3(-99.0, SHORE_Y, -34.0), "yaw": 6.0, "pitch": 12.0},
	{"name": "08_station_night", "time": [21, 15], "pos": Vector3(-100.0, SHORE_Y, -60.0), "yaw": -90.0, "pitch": 5.0},
	{"name": "09_lattice_night", "time": [21, 15], "pos": Vector3(-99.0, SHORE_Y, -74.0), "yaw": -74.0, "pitch": 20.0},
	{"name": "10_after_close_service_only", "time": [22, 15], "pos": Vector3(-100.0, SHORE_Y, -60.0), "yaw": -90.0, "pitch": 5.0},
	{"name": "11_q3_open", "time": [19, 0], "pos": Vector3(-102.0, SHORE_Y, -2.0), "yaw": -90.0, "pitch": 5.0},
	{"name": "12_west_arch_reveal", "time": [19, 0], "pos": Vector3(-49.0, 0.2, -2.0), "yaw": 78.0, "pitch": 8.0},
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
		push_error("boardwalk_coaster_capture: no player")
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
