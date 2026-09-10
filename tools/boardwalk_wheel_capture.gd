extends Node

## Player-camera proof for the directly editor-owned R1 wheel. The viewpoints
## keep the player on established public paving and include the exact protected
## west-arch rim-clearance standpoint, so a more detailed silhouette cannot
## quietly consume the composition that fixed WHEEL_TOP was created to protect.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-wheel-2026-09-10"
const DECK_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_1990s_palette_whole_wheel", "time": [18, 45], "pos": Vector3(-91.5, DECK_Y, -2.0), "yaw": 55.0, "pitch": 31.0},
	{"name": "02_faceted_cabins_and_dark_roofs", "time": [18, 45], "pos": Vector3(-103.0, DECK_Y, -16.0), "yaw": 90.0, "pitch": 28.0},
	{"name": "03_north_load_stair", "time": [18, 45], "pos": Vector3(-104.8, DECK_Y, -27.2), "yaw": 132.0, "pitch": 18.0},
	{"name": "04_level_transfer_and_lift", "time": [18, 45], "pos": Vector3(-106.7, DECK_Y, -22.8), "yaw": 122.0, "pitch": 13.0},
	{"name": "05_south_unload_to_exit", "time": [18, 45], "pos": Vector3(-104.8, DECK_Y, -5.0), "yaw": 48.0, "pitch": 18.0},
	{"name": "06_lattice_depth_and_cross_ties", "time": [18, 45], "pos": Vector3(-96.0, DECK_Y, 2.0), "yaw": 12.0, "pitch": 15.0},
	{"name": "07_protected_arch_rim_clearance", "time": [19, 0], "pos": Vector3(ParkPlan.ARCH_RIM_CLEAR_X, 0.2, -2.0), "yaw": 90.0, "pitch": 11.0},
	{"name": "08_west_arch_reveal", "time": [19, 0], "pos": Vector3(-49.0, 0.2, -2.0), "yaw": 78.0, "pitch": 8.0},
	{"name": "09_sunset_pier_character", "time": [20, 20], "pos": Vector3(-96.0, DECK_Y, 2.0), "yaw": 12.0, "pitch": 14.0},
	{"name": "10_radial_color_night_wheel", "time": [21, 15], "pos": Vector3(-91.5, DECK_Y, -2.0), "yaw": 55.0, "pitch": 31.0},
	{"name": "11_color_tubes_hub_and_cabins", "time": [21, 15], "pos": Vector3(-103.0, DECK_Y, -16.0), "yaw": 90.0, "pitch": 29.0},
	{"name": "12_after_close_performance_lights_off", "time": [22, 15], "pos": Vector3(-91.5, DECK_Y, -2.0), "yaw": 55.0, "pitch": 31.0},
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
		push_error("boardwalk_wheel_capture: no player")
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
