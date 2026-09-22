extends Node

## Player-eye proof that the continuous promenade's brick bond forms repeated
## surf fronts washing toward the gate, including the drop-off seam.

const OUTPUT_DIR := "res://documentation/screenshots/arrival-tram-crossing-2026-09-11"
const SHOTS := [
	{"name": "01_south_entry_northbound", "pos": Vector3(0.0, 0.2, 226.0), "yaw": 0.0, "pitch": -9.0},
	{"name": "02_long_wave_from_south", "pos": Vector3(0.0, 0.2, 216.0), "yaw": 0.0, "pitch": -18.0},
	{"name": "03_brick_bond_close", "pos": Vector3(2.8, 0.2, 201.0), "yaw": -18.0, "pitch": -48.0},
	{"name": "04_palms_and_wave", "pos": Vector3(-5.0, 0.2, 196.0), "yaw": 8.0, "pitch": -9.0},
	{"name": "05_north_end_southbound", "pos": Vector3(0.0, 0.2, 163.0), "yaw": 180.0, "pitch": -11.0},
	{"name": "06_tram_crossing_southbound", "pos": Vector3(0.0, 0.2, 166.0), "yaw": 180.0, "pitch": -22.0},
	{"name": "07_tram_crossing_northbound", "pos": Vector3(0.0, 0.2, 181.0), "yaw": 0.0, "pitch": -22.0},
]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	ParkClock.running = false
	ParkClock.set_clock(16, 30)
	await get_tree().create_timer(5.0).timeout
	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("arrival_walk_paving_capture: no player")
		get_tree().quit(1)
		return
	_head = _player.get_node("head") as Node3D
	_player.call("set_third_person", false)
	for shot in SHOTS:
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
	for _i in 8:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
