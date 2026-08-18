extends Node

## Dev probe: the east gate, and what it frames.
##
## Its own throwaway rather than entries in `capture.gd`, for the reason
## `_niche_probe.gd` gives: these are all one opening at a range of distances,
## and the question they ask is not the question a walk-the-park pass asks.
##
## **The question is whether the gate frames the cascade.** Everything here is on
## the fountain's east-west line or deliberately off it, because that line is the
## entire argument for cutting a seventh way out rather than using the `ne` or
## `se` threshold that were already in this wall. If the monument does not read
## through the opening, the gate is in the wrong place and no amount of dressing
## fixes it.
##
## Distances matter more than usual here. An opening's clear height is not what
## it crops by — its depth is, and this one is 13.5m deep like the arch. Walking
## *towards* it raises the ceiling and widens the band at once, so the tight case
## is the near standpoint rather than the far one. `EAST_NEAR_STAND_X` is that
## standpoint and it is shot first.

const SETTLE := 6.0

## The axis, from the fountain out to the court.
##
## **Yaw −90 is east and +90 is west**, and the first run of this probe had every
## bearing backwards — fifteen frames of the arch, taken to check the gate facing
## the other way. Godot's forward is −Z, so a yaw of θ points at
## `(−sin θ, −cos θ)`, which puts +90 at −x. The tell was in the printout rather
## than in the pictures: the spring arm hangs the camera *behind* the player, and
## the eye came out 2.6m further east than the standpoint on a shot that was
## supposed to be looking that way. Print the camera, not the pose.
const AXIS := [
	# The binding standpoint — just past the fountain's coping, which is the
	# furthest anyone stands on this line with the pool not in the way. If the
	# crop is wrong anywhere it is wrong here.
	{"name": "a_near_stand", "yaw": -90.0, "pitch": -2.0, "pos": Vector3(11.0, 1.2, -2.0)},
	# The ring's east vertex, where the decision to walk east gets made.
	{"name": "b_ring", "yaw": -90.0, "pitch": -2.0, "pos": Vector3(16.0, 1.2, -2.0)},
	# Backed off to the far side of the plaza. A distant ridge should open up as
	# you back away from it, and this is the frame that says whether it does.
	{"name": "c_far_side", "yaw": -90.0, "pitch": -1.0, "pos": Vector3(-16.0, 1.2, -2.0)},
	# At the gate's plaza face, about to go under it.
	{"name": "d_at_the_mouth", "yaw": -90.0, "pitch": -2.0, "pos": Vector3(31.0, 1.2, -2.0)},
	# Inside the passage. 13.5m of it, and the beam is behind you.
	{"name": "e_in_the_passage", "yaw": -90.0, "pitch": -2.0, "pos": Vector3(40.0, 1.2, -2.0)},
	# Out the far side, in the court, with the monument filling the frame.
	{"name": "f_court", "yaw": -90.0, "pitch": -4.0, "pos": Vector3(50.0, 1.2, -2.0)},
	{"name": "g_foot", "yaw": -90.0, "pitch": 6.0, "pos": Vector3(56.0, 1.2, -2.0)},
]

## Looking back west, which is the half of a gate nobody checks. Coming down out
## of the east the gate is the way in, and the plaza is what it frames.
const BACK := [
	{"name": "h_back_from_court", "yaw": 90.0, "pitch": -2.0, "pos": Vector3(56.0, 1.2, -2.0)},
	{"name": "i_back_at_the_face", "yaw": 90.0, "pitch": -2.0, "pos": Vector3(48.0, 1.2, -2.0)},
]

## Off the axis. **The gate's one asymmetry lives in these two frames**: its
## north neighbour tops out at 11.5m and its south at 19, where the west arch
## has 11.0 and 10.5 and stands 1.5–2m over both. Whether a 12.5m pier reads as
## a gate beside a block half again its height cannot be reasoned about, only
## looked at.
const OBLIQUE := [
	{"name": "j_from_the_north", "yaw": -127.6, "pitch": -2.0, "pos": Vector3(14.0, 1.2, -22.0)},
	{"name": "k_from_the_south", "yaw": -52.4, "pitch": -2.0, "pos": Vector3(14.0, 1.2, 18.0)},
	# Square on to the wall from close in, which is where the 19m block is most
	# of what you see.
	{"name": "l_wall_south", "yaw": -68.2, "pitch": 6.0, "pos": Vector3(24.0, 1.2, 10.0)},
]

## After dark. The valance, the thirteen bulbs, the three pools on the board and
## the throat light behind — none of which the arch had until 2026-08-16 and all
## of which this gate has from the day it was cut.
const NIGHT := [
	{"name": "m_night_ring", "yaw": -90.0, "pitch": -2.0, "pos": Vector3(16.0, 1.2, -2.0)},
	{"name": "n_night_mouth", "yaw": -90.0, "pitch": -2.0, "pos": Vector3(31.0, 1.2, -2.0)},
	{"name": "o_night_court", "yaw": 90.0, "pitch": -2.0, "pos": Vector3(52.0, 1.2, -2.0)},
]

## The elevation, free camera. The gate and the monument on one axis at rising
## heights is the composition the whole east is for, and no standpoint in the
## plaza shows both whole — the same reason `_cascade_probe.gd` exists for the
## west. Half of these are in mid-air, so a body put here falls out of the shot.
const FREE := [
	{"name": "p_elev_axis", "pos": Vector3(-4.0, 18.0, -2.0), "yaw": -90.0, "pitch": -12.0},
	{"name": "q_elev_close", "pos": Vector3(24.0, 14.0, -2.0), "yaw": -90.0, "pitch": -10.0},
	# From due east above the court, back at the gate: the plaza wall as the
	# monument's own backdrop.
	{"name": "r_elev_back", "pos": Vector3(74.0, 12.0, -2.0), "yaw": 90.0, "pitch": -8.0},
	# Side on, which is the only way to see that the gate, the court and the
	# cascade are three depths rather than one wall.
	{"name": "s_elev_side", "pos": Vector3(50.0, 16.0, -46.0), "yaw": -172.2, "pitch": -18.0},
]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	await get_tree().create_timer(SETTLE).timeout

	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")

	for shot in AXIS:
		await _shoot(shot)
	for shot in BACK:
		await _shoot(shot)
	for shot in OBLIQUE:
		await _shoot(shot)

	ParkClock.set_clock(21, 15)
	await get_tree().create_timer(3.0).timeout
	for shot in NIGHT:
		await _shoot(shot)

	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true
	ParkClock.set_clock(15, 30)
	await get_tree().create_timer(3.0).timeout
	for shot in FREE:
		await _free(cam, shot)

	get_tree().quit()


func _free(cam: Camera3D, shot: Dictionary) -> void:
	cam.global_position = shot["pos"]
	cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "user://east_%s.png" % shot["name"]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)


func _shoot(shot: Dictionary) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 40:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "user://east_%s.png" % shot["name"]
	img.save_png(path)
	# The camera is on a 2.6m spring arm and is **not** at `pos` — it hangs about
	# 2.5m back, and pitching up swings it *down*. Printed rather than assumed,
	# which is the only reason the arch's clearances were ever right.
	var cam := get_viewport().get_camera_3d()
	print("saved ", path, "  eye ", cam.global_position if cam != null else "?")
