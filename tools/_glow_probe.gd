extends Node

## Dev probe: the water's night glow, against the same frames by day.
##
## **Pairs, always.** The whole risk in an emissive term is that it does not know
## the hour — `water_pool` carried "albedo and gloss, not emission" for exactly
## as long as it had no way to find out, because a glow with nothing driving it
## glows just as hard at noon and reads as a bug rather than as magic. So every
## standpoint here is shot twice at the same position and the same bearing, and
## the noon frame is the one that has to be *unchanged*. A night frame on its own
## proves nothing at all.
##
## Free camera throughout: the spring arm puts the body between the eye and the
## fountain on every axis shot, and the body is the width of the thing being
## judged.
##
## Bearings are `atan2(-dx, -dz)`, and they are computed rather than guessed —
## Godot's forward is −Z, so yaw 0 looks down −z and +90 looks down −x. Two of
## these were written as 180 on the first pass and produced a very nice
## photograph of the entrance street.

const SETTLE := 6.0

## Noon and a good way after the lamps are up. 21:15 is inside park hours — after
## close the glow goes out on purpose, because it takes `feature_on` and a
## fountain presenting itself to nobody is what `night.md` argues against.
const NOON := [12, 30]
const LIT := [21, 15]

const SHOTS := [
	# The plaza's fountain from the ring, which is where it is seen from most.
	{"name": "a_fountain_ring", "pos": Vector3(0.0, 2.2, 17.0),
		"yaw": 0.0, "pitch": -4.0},
	# Close, across the coping — the froth and the basins are the parts that
	# carry the most glow and this is the distance they read at.
	{"name": "b_fountain_close", "pos": Vector3(0.0, 2.6, 10.5),
		"yaw": 0.0, "pitch": -10.0},
	# From the east gate looking back down the axis, so the fountain is against
	# the lit frontage rather than against sky. If the glow is too strong this is
	# the frame that shows it, because here it has competition.
	{"name": "c_fountain_from_gate", "pos": Vector3(34.0, 2.2, -2.0),
		"yaw": 90.0, "pitch": -2.0},
	# The cascade's niche, which takes nearly twice the plaza's strength.
	{"name": "d_niche", "pos": Vector3(-66.5, -4.4, -2.0),
		"yaw": -90.0, "pitch": -6.0},
	{"name": "e_niche_close", "pos": Vector3(-64.8, -4.2, -2.0),
		"yaw": -90.0, "pitch": -4.0},
	# And the east one, which shares the shape and not the coordinates.
	{"name": "f_niche_east", "pos": Vector3(56.5, 1.6, -2.0),
		"yaw": -90.0, "pitch": 2.0},
]

var _cam: Camera3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(NOON[0], NOON[1])
	await get_tree().create_timer(SETTLE).timeout

	_cam = Camera3D.new()
	add_child(_cam)
	_cam.current = true

	for shot in SHOTS:
		await _shoot(shot, "noon")

	ParkClock.set_clock(LIT[0], LIT[1])
	await get_tree().create_timer(4.0).timeout
	# Printed rather than assumed: this is the number the whole thing hangs on,
	# and if it is zero at 21:15 the glow is off for a reason that has nothing to
	# do with the shader.
	print("park_night = ",
		RenderingServer.global_shader_parameter_get(&"park_night"))
	for shot in SHOTS:
		await _shoot(shot, "night")

	get_tree().quit()


func _shoot(shot: Dictionary, when: String) -> void:
	_cam.global_position = shot["pos"]
	_cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
	for _i in 6:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "user://glow_%s_%s.png" % [shot["name"], when]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
