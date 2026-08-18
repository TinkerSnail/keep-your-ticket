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

## Seconds between frames, and it is `flow_probe.py`'s number rather than this
## file's.
##
## **It was 0.09 and the analysis was written for 0.035**, which is the kind of
## disagreement that does not announce itself. `SEARCH` over there is 34 pixels,
## sized so it is wider than one frame of travel and narrower than half the band
## spacing: at 35ms the three views travel about 13, 20 and 11 pixels against
## bands 161, 141 and 62 apart. Scale that to 90ms and the jets travel about 51,
## which is outside a 34-pixel window — so the correlation cannot reach the true
## peak, returns whatever sits at the edge of its range, and reports a *sign*
## rather than a shift. Both values had been in the tree unchanged since the day
## the pair was written, so they never agreed.
##
## Which way to fix it is not arbitrary. Widening `SEARCH` to reach 51 would put
## it past the plume's own wrap point of 31 and start matching one band onto the
## next; shortening the gap moves every view further inside both limits at once.
## So the gap comes down to what the window was cut for.
##
## Not verified in a web session and it cannot be: `create_timer` sets a floor,
## not a ceiling, and lavapipe delivers frames 150-1000ms apart whatever this
## says. Under that, travel is more than a whole band per frame for every view
## and the reading is modulo the pattern - see the warning at the foot of the
## capture loop, which is there to stop the result being read as a verdict.
const GAP := 0.035

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
		var worst := 0
		for f in FRAMES:
			await get_tree().create_timer(GAP).timeout
			await RenderingServer.frame_post_draw
			var now := Time.get_ticks_msec()
			var img := get_viewport().get_texture().get_image()
			img.save_png("user://flow_%s_%02d.png" % [view["name"], f])
			print("flow_%s_%02d  +%dms" % [view["name"], f, now - last])
			worst = maxi(worst, now - last)
			last = now
		# **Say so when the frames are too far apart to mean anything.**
		#
		# `flow_probe.py` measures how far the pattern moved between consecutive
		# frames, which only answers a direction while the pattern moves less than
		# half its own period in `GAP`. Miss that and the correlation aliases: the
		# shifts come back alternating at the window limit and the median is
		# noise, but it is a *signed* noise and it reads exactly like a verdict.
		#
		# Which is not hypothetical. On a box with no GPU — lavapipe under Xvfb,
		# which is how this runs in a web session — 90ms of intent arrives as 500
		# to 1000ms, and the probe cheerfully reported the falls and the jets both
		# running UP. That is the original bug's own signature, so the failure
		# mode here is not a wrong number, it is a convincing false regression on
		# the one shader this tool exists to watch.
		if worst > int(GAP * 1000.0) * 2:
			push_warning(("flow_%s: frames up to %dms apart against a %dms gap — "
				+ "too slow for the correlation to resolve a direction. The "
				+ "verdict from these frames is not usable; run on a real GPU.")
				% [view["name"], worst, int(GAP * 1000.0)])

	get_tree().quit()
