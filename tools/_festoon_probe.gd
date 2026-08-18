extends Node

## Dev probe: where the street's festoons meet the frontage.
##
## The run was hung at a flat 5.6m between x's inset 0.3m from both faces, so no
## string touched a building — and three ends were *above* the parapet they were
## nailed to, the arcade's by 0.8m, with the sixth string spanning the turnstiles
## where there is no frontage at all. All of it measurable and none of it visible
## in any shot the park already takes: `capture.gd`'s three street poses look
## along the axis at pitch 1–2°, which is the one direction that puts every one
## of those junctions out of frame.
##
## So these look *up and sideways* at the ends, which is the only thing that can
## show a wire ending in air 30cm from a wall it is supposed to be tied to.
##
## Day and night both. The bulbs are emissive and the string's own omni hangs at
## the chord's mid-height now, so after dark the pool moves with the tilt — a
## light left at a constant y on a tilted string is a pool sitting off its wire.

const SETTLE := 6.0

## The two lowest strings, which are the ones that were floating. String 2 ties
## to the arcade roof at 4.4 on the west and a 5.0m shop on the east; string 1
## ties to a 5.0m shop on the west. If a pin reads as a fixing from here, they
## all do — every other end has more wall under it.
## Yaw 0 faces −Z, which up this street is *towards the plaza*; the gate is at
## +Z. Yaw +90 looks west. Worth writing down because the first run of this file
## had every axis shot pointing the wrong way and produced four perfectly sharp
## photographs of the turnstiles.
const SHOTS := [
	# Under the west end of the arcade's string, looking up at its own junction.
	# Its anchor is at (−9.0, 4.10) and the eye is 11.5m off it, so the junction
	# sits about 19° up — the pitch is the shot, not a tidy framing.
	{"name": "a_arcade_west", "yaw": 90.0, "pitch": 20.0, "pos": Vector3(2.5, 0.2, 78.0)},
	# The same string's east end, from the other side of the street.
	{"name": "b_arcade_east", "yaw": -90.0, "pitch": 20.0, "pos": Vector3(-5.5, 0.2, 78.0)},
	# The west end of string 1, the 5.0m shop — the one whose parapet the old
	# constant cleared by 0.2m and hung above.
	{"name": "c_shop1_west", "yaw": 90.0, "pitch": 20.0, "pos": Vector3(2.5, 0.2, 68.0)},
	# The whole of string 0 side-on, which is the largest tilt in the run: 6.5m
	# of shop on the west against 5.5m on the east.
	{"name": "d_tilt_across", "yaw": 66.0, "pitch": 16.0, "pos": Vector3(4.0, 0.2, 63.0)},
	# The run as a run, both ways. This is what says whether five tilted strings
	# read as a fair or as a mistake.
	{"name": "e_run_from_gate", "yaw": 0.0, "pitch": 12.0, "pos": Vector3(-1.5, 0.2, 103.0)},
	{"name": "f_run_from_plaza", "yaw": 180.0, "pitch": 12.0, "pos": Vector3(-1.5, 0.2, 53.0)},
	# Oblique, off the axis, which is how the frontage is actually read on the
	# walk up — and the angle at which a wire that stops short shows as a gap
	# against the wall behind it rather than against sky.
	{"name": "g_oblique_west", "yaw": 28.0, "pitch": 14.0, "pos": Vector3(4.0, 0.2, 88.0)},
	# The gate end, where the sixth string used to hang over the turnstiles. The
	# question is whether the run now stops somewhere or merely stops.
	{"name": "h_gate_end", "yaw": 178.0, "pitch": 12.0, "pos": Vector3(-1.5, 0.2, 94.0)},
]

## The junctions themselves, from a free camera at the anchor's own height.
##
## Not a luxury: the player is on a 2.6m spring arm, so every third-person shot
## at a fitting 4m up puts the photographer's own head between the eye and the
## thing in question. These are 3–5m out from the wall and level with the pin.
const FREE := [
	# The west end of string 2 — the arcade, the lowest anchor in the run and the
	# one the old constant floated 0.8m above.
	{"name": "j_pin_arcade_west", "pos": Vector3(-5.0, 4.3, 80.5), "yaw": 58.0, "pitch": -2.0},
	# The east end of string 0, against a parapet rather than an arcade roof.
	{"name": "k_pin_shop10_east", "pos": Vector3(2.0, 5.4, 55.5), "yaw": -122.0, "pitch": -2.0},
	# Straight down the run from above head height, where all five are in one
	# frame and the tilts either agree with the roofline or argue with it.
	{"name": "l_run_high", "pos": Vector3(-1.5, 7.2, 106.0), "yaw": 0.0, "pitch": -4.0},
	{"name": "m_run_high_back", "pos": Vector3(-1.5, 7.2, 52.0), "yaw": 180.0, "pitch": -4.0},
]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(16, 30)
	await get_tree().create_timer(SETTLE).timeout

	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")

	for shot in SHOTS:
		await _shoot(shot, "day")

	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true
	for shot in FREE:
		await _free(cam, shot, "day")

	ParkClock.set_clock(21, 15)
	await get_tree().create_timer(3.0).timeout
	for shot in FREE:
		await _free(cam, shot, "night")
	cam.current = false
	for shot in SHOTS:
		await _shoot(shot, "night")

	get_tree().quit()


func _free(cam: Camera3D, shot: Dictionary, when: String) -> void:
	cam.current = true
	cam.global_position = shot["pos"]
	cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "user://festoon_%s_%s.png" % [shot["name"], when]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)


func _shoot(shot: Dictionary, when: String) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 30:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "user://festoon_%s_%s.png" % [shot["name"], when]
	get_viewport().get_texture().get_image().save_png(path)
	# The camera is on a spring arm and is not at `pos`, and pitching *up* swings
	# it down. Printed rather than assumed — the arch's clearances were only ever
	# right because somebody printed this.
	var cam := get_viewport().get_camera_3d()
	print("saved ", path, "  eye ", cam.global_position if cam != null else "?")
