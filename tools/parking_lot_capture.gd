extends Node

## Player-eye proof of the rebuilt parking fields, their crossings, islands,
## road-edge palms, curb beds and the still-open Q0 arrival axis.

const OUTPUT_DIR := "res://documentation/screenshots/parking-lot-2026-09-11"
const SHOTS := [
	{"name": "01_arrival_west_field", "pos": Vector3(0.0, 0.2, 224.0), "yaw": -62.0, "pitch": 7.0},
	{"name": "02_arrival_east_field", "pos": Vector3(0.0, 0.2, 224.0), "yaw": 62.0, "pitch": 7.0},
	{"name": "03_west_collector", "pos": Vector3(-8.0, 0.2, 204.0), "yaw": -78.0, "pitch": -3.0},
	{"name": "04_east_accessible_bays", "pos": Vector3(8.0, 0.2, 187.0), "yaw": 78.0, "pitch": -5.0},
	{"name": "05_islands_and_banners", "pos": Vector3(-12.0, 0.2, 198.0), "yaw": -90.0, "pitch": 10.0},
	{"name": "06_q0_arrival_axis", "pos": Vector3(0.0, 0.2, 232.0), "yaw": 0.0, "pitch": 8.0},
	{"name": "07_drop_off_from_walk", "pos": Vector3(0.0, 0.2, 227.0), "yaw": 90.0, "pitch": -3.0},
	{"name": "08_drop_off_from_front_road", "pos": Vector3(34.0, 0.2, 238.0), "yaw": -72.0, "pitch": -2.0},
	{"name": "09_front_road_palm_border", "pos": Vector3(8.0, 0.2, 237.0), "yaw": -88.0, "pitch": -5.0},
	{"name": "10_palm_ring_in_linear_bed", "pos": Vector3(55.0, 0.2, 245.0), "yaw": 18.0, "pitch": -8.0},
	{"name": "11_lower_approach_curbs", "pos": Vector3(86.0, 0.2, 236.0), "yaw": -56.0, "pitch": 1.0},
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
		push_error("parking_lot_capture: no player")
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
