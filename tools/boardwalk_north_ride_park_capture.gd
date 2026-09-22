extends Node

## Player-camera proof for the corrected open-air north Boardwalk. The frames
## follow the old promenade into the extended waterfront, show R2's one high
## flyover, the separate R15/R16 courts and the shoreline return, then recheck
## the protected views.

const OUTPUT_DIR := "res://documentation/screenshots/boardwalk-open-air-redesign-2026-09-11"
const SHORE_Y := ParkPlan.SHORE_TOP + 0.2
const SHOTS := [
	{"name": "01_old_boardwalk_continues", "time": [18, 35], "pos": Vector3(-99.0, SHORE_Y, -62.0), "target": Vector3(-105.0, -1.0, -104.0)},
	{"name": "02_visible_midway_under_first_hill", "time": [18, 40], "pos": Vector3(-107.0, SHORE_Y, -96.0), "target": Vector3(-99.0, 1.0, -95.0)},
	{"name": "03_clear_walk_beneath_flyover", "time": [18, 40], "pos": Vector3(-108.0, SHORE_Y, -112.0), "target": Vector3(-106.0, 4.5, -104.0)},
	{"name": "03b_roofed_midway_in_high_bay", "time": [18, 42], "pos": Vector3(-60.0, 0.2, -120.0), "target": Vector3(-53.0, 2.0, -120.0)},
	{"name": "04_open_waterfront_run", "time": [18, 45], "pos": Vector3(-108.0, SHORE_Y, -138.0), "target": Vector3(-102.0, -3.5, -176.0)},
	{"name": "05_r15_separate_court", "time": [18, 45], "pos": Vector3(-100.0, SHORE_Y, -164.0), "target": Vector3(-86.0, -2.0, -164.0)},
	{"name": "06_r16_separate_court", "time": [18, 45], "pos": Vector3(-98.0, SHORE_Y, -184.0), "target": Vector3(-84.0, -1.5, -184.0)},
	{"name": "07_four_ride_district", "time": [19, 0], "pos": Vector3(-98.0, SHORE_Y, -187.0), "target": Vector3(-84.0, 3.0, -150.0)},
	{"name": "08_shoreline_turn", "time": [19, 0], "pos": Vector3(-98.0, SHORE_Y, -187.0), "target": Vector3(-82.0, -4.5, -204.0)},
	{"name": "09_land_return_approach", "time": [19, 0], "pos": Vector3(-47.0, SHORE_Y, -184.0), "target": Vector3(-82.0, -4.5, -204.0)},
	{"name": "10_open_connection_back", "time": [19, 0], "pos": Vector3(-80.0, SHORE_Y, -204.0), "target": Vector3(-92.0, -2.0, -182.0)},
	{"name": "10b_grand_circuit_overpass", "time": [19, 0], "pos": Vector3(-73.0, SHORE_Y, -209.0), "target": Vector3(-70.14, -1.74, -198.65)},
	{"name": "11_ride_district_at_night", "time": [21, 15], "pos": Vector3(-103.0, SHORE_Y, -158.0), "target": Vector3(-81.0, 3.0, -132.0)},
	{"name": "12_q3_open", "time": [19, 0], "pos": Vector3(-102.0, SHORE_Y, -2.0), "target": Vector3(-150.0, -3.0, 6.0)},
	{"name": "13_west_arch_reveal", "time": [19, 0], "pos": Vector3(-49.0, 0.2, -2.0), "target": Vector3(-108.0, 4.0, -16.0)},
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
		push_error("boardwalk_north_ride_park_capture: no player")
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
	_player.velocity = Vector3.ZERO
	for _i in 120:
		await get_tree().physics_frame
		if _player.is_on_floor():
			break
	var eye := _player.global_position + Vector3.UP * 1.62
	var target: Vector3 = shot["target"]
	var direction: Vector3 = target - eye
	_player.rotation.y = atan2(-direction.x, -direction.z)
	_head.rotation.x = atan2(direction.y,
		Vector2(direction.x, direction.z).length())
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
