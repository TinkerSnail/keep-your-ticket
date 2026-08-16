extends Node

## Dev tool, throwaway: the same wheel from the same camera, both sides of the
## seam.
##
## The tableau's wheel and the section's wheel stand in the same world
## coordinates and are never in the tree together, so the only way to compare
## them is to put a camera at one point, shoot it with the plaza mounted, cross,
## and shoot it again without moving. Anything that differs between the two
## frames is a difference in the wheel rather than in the view of it.
##
## Two standpoints, because the two failures live at different distances. From
## the ring the question is whether the silhouette is the same shape — that is
## the 87m read the tableau exists for. From the alley mouth it is whether the
## thing you walk up to is the thing you were looking at.

const HOUR := 16
const MINUTE := 0
const SETTLE := 6.0

## Both stand in the open with a clear line to the wheel in either section.
## `ring` is the plaza's own west vertex, which is where the arch is aimed and
## where `west_capture`'s `01b` is taken from; `close` is the alley mouth.
const SHOTS := [
	{"name": "ring", "yaw": 100.0, "pitch": 7.0, "pos": Vector3(-16.0, 0.2, -2.0)},
	{"name": "close", "yaw": 16.0, "pitch": 20.0, "pos": Vector3(-96.0, -2.8, 8.0)},
]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(HOUR, MINUTE)
	await get_tree().create_timer(SETTLE).timeout
	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("no player")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")

	for shot in SHOTS:
		await _shoot(shot, "%s_far" % shot["name"])

	await ParkSections.enter(&"boardwalk", &"plaza")
	await get_tree().create_timer(3.0).timeout
	for shot in SHOTS:
		await _shoot(shot, "%s_real" % shot["name"])

	get_tree().quit()


func _shoot(shot: Dictionary, label: String) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "user://wheel_%s.png" % label
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
