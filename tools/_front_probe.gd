extends Node

## Throwaway: the perimeter's upper storeys, from the fountain and from close
## enough to count the floors. Aimed at the two runs the storey ladder changed
## most — `e_mid_s`, the 19m east wall that carries five, and `n_west`, the 16m
## north-west one that carries four.

const SETTLE := 3.0

const SHOTS := [
	# From the fountain, which is the distance the diminution is tuned for.
	{"name": "east_from_fountain", "yaw": -88.0, "pitch": 11.0, "pos": Vector3(0, 0.2, 6)},
	{"name": "nw_from_fountain", "yaw": 26.0, "pitch": 12.0, "pos": Vector3(0, 0.2, 6)},
	{"name": "north_from_fountain", "yaw": 0.0, "pitch": 12.0, "pos": Vector3(0, 0.2, 12)},
	# Close, straight on, so the floor lines can be counted.
	{"name": "east_close", "yaw": -90.0, "pitch": 20.0, "pos": Vector3(20, 0.2, 6)},
	{"name": "nw_close", "yaw": 10.0, "pitch": 22.0, "pos": Vector3(-14, 0.2, -22)},
	# The user's own view: standing north of the fountain looking up the plaza.
	{"name": "user_view", "yaw": 4.0, "pitch": 6.0, "pos": Vector3(6, 0.2, 2)},
]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run(main)


func _run(main: Node) -> void:
	ParkClock.running = false
	ParkClock.set_clock(16, 0)
	await get_tree().create_timer(SETTLE).timeout

	_player = main.get_node_or_null("player")
	if _player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")
	if _player.has_method("set_third_person"):
		_player.set_third_person(false)

	for shot in SHOTS:
		await _shoot(shot, "front_%s" % shot["name"])
	get_tree().quit()


func _shoot(shot: Dictionary, label: String) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 3:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("user://%s.png" % label)
	print("saved ", label)
