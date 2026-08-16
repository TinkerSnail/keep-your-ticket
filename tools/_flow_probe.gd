extends Node

## Dev tool: which way is the water going?
##
## `water_fall.gdshader` had its travel term signed backwards from the day it
## was written. The sheets under each basin climbed their own lip and the jets
## rained down into their own nozzles, and it survived four rounds of looking at
## screenshots — because **every still frame of water going up is a still frame
## of water going down**. The pattern, the break-up, the alpha and the brightness
## are all identical; the only difference is the direction, and a single frame
## has no opinion about that.
##
## So this does what the menu capture does for a tab change: takes consecutive
## frames of one fixed camera and lets something else measure the difference.
## The frames are cross-correlated vertically by `tools/flow_probe.py`, which
## reports which way the pattern moved.
##
## Narrow FOV on purpose. At the player's 70 degrees a fall is a few dozen pixels
## tall and one frame of travel is under three of them; at 22 the same travel is
## twenty, which is the difference between a measurement and a guess.

const FOV := 22.0
const FRAMES := 8
const GAP := 0.09

## Both directions, because fixing a sign is exactly the change that can put the
## error in the other one. The jets should climb and the sheets should fall, and
## the probe has to see them disagree.
const VIEWS := [
	# The sheet off the lower basin, framed on the falls themselves rather than
	# on the basin — a crop with pool and passers-by in it leaves them in the
	# residual after the static scene comes out, and they are not water.
	{"name": "fall", "yaw": 0.0, "pitch": 15.0, "pos": Vector3(0.0, 0.2, 10.0)},
	# The ring of jets, from the same side.
	{"name": "jet", "yaw": 0.0, "pitch": 3.0, "pos": Vector3(0.0, 0.2, 11.4)},
	# And the plume, which is the same material family as the jets and the one
	# piece of water the whole park can see. Shot from as close as the kerb
	# allows: at 12.5m it came back indeterminate, because a 0.6m column at that
	# range is a sliver and the crop that finds it is mostly sky.
	{"name": "plume", "yaw": 0.0, "pitch": 30.0, "pos": Vector3(0.0, 0.2, 9.8)},
]

var _player: Node3D
var _head: Node3D
var _cam: Camera3D


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run(main)


func _run(main: Node) -> void:
	ParkClock.running = false
	ParkClock.set_clock(14, 0)
	await get_tree().create_timer(4.0).timeout

	_player = main.get_node_or_null("player")
	_head = _player.get_node("head")
	_cam = _player.get_node("head/camera") as Camera3D
	if _player.has_method("set_third_person"):
		_player.set_third_person(false)
		await get_tree().physics_frame
	_cam.fov = FOV

	for view in VIEWS:
		_player.global_position = view["pos"]
		_player.rotation.y = deg_to_rad(view["yaw"])
		_head.rotation.x = deg_to_rad(view["pitch"])
		for _i in 4:
			await get_tree().physics_frame
		var last := Time.get_ticks_msec()
		for f in FRAMES:
			await get_tree().create_timer(GAP).timeout
			await RenderingServer.frame_post_draw
			var now := Time.get_ticks_msec()
			var img := get_viewport().get_texture().get_image()
			img.save_png("user://flow_%s_%02d.png" % [view["name"], f])
			print("flow_%s_%02d  +%dms" % [view["name"], f, now - last])
			last = now

	get_tree().quit()
