extends Node

## Dev probe: the wall fountain in the cascade's niche, from the court.
##
## Its own throwaway rather than four more entries in `west_capture.gd`, because
## that file is in flight elsewhere and because these are all one object at one
## distance — the walk-the-west run has no shot closer than eleven metres to the
## wall, which is the distance a monument is judged at and not a fountain.
##
## Day and night both, and the night half is not decoration: `niche_glow` and
## `niche_wash` are aimed at parts that did not exist this morning.

const SETTLE := 6.0

const SHOTS := [
	# The monument with the fountain in it — the standpoint the wings deliver you
	# to. If the niche does not read as occupied from here it has failed.
	{"name": "a_court", "yaw": -90.0, "pitch": -8.0, "pos": Vector3(-70.0, -5.5, -2.0)},
	# Close enough that the three stages are three stages.
	{"name": "b_close", "yaw": -90.0, "pitch": -10.0, "pos": Vector3(-67.0, -5.5, -2.0)},
	# At the trough, looking up into the arch. This is the shot the depth was
	# bought for: at 0.6m of recess the spout and the bowl would both be outside
	# the opening.
	{"name": "c_at_the_trough", "yaw": -90.0, "pitch": -6.0, "pos": Vector3(-65.6, -5.5, -2.0)},
	# Off the axis, which is how anybody coming down a wing actually sees it.
	{"name": "d_oblique", "yaw": -66.0, "pitch": -8.0, "pos": Vector3(-67.5, -5.5, -6.5)},
	{"name": "e_from_the_wing", "yaw": -50.0, "pitch": -6.0, "pos": Vector3(-68.0, -5.5, 3.0)},
]

## The planted bank down the outbound leg, at the end where it stops.
const BANK := [
	# Standing on the bank itself at the top, looking straight down the row. A
	# missing planter in a marching row shows here or nowhere.
	{"name": "h_bank_n_row", "yaw": 0.0, "pitch": -12.0, "pos": Vector3(-58.6, 0.6, -4.5)},
	{"name": "i_bank_s_row", "yaw": 180.0, "pitch": -12.0, "pos": Vector3(-58.6, 0.6, 0.5)},
	# From the north turn landing, back at the end of the row: yaw −69 points at
	# the last planter's far corner, which is the thing in question.
	{"name": "j_bank_n_end", "yaw": -69.0, "pitch": -2.0, "pos": Vector3(-62.5, -2.9, -11.0)},
	{"name": "k_bank_s_end", "yaw": -111.0, "pitch": -2.0, "pos": Vector3(-62.5, -2.9, 7.0)},
	# The return leg's rail from the court, side-on to the whole diagonal. Where
	# it stops is the question; a rail that quits early reads as a rail from any
	# angle but this one.
	{"name": "l_rail_n", "yaw": -67.0, "pitch": 4.0, "pos": Vector3(-73.0, -5.5, -6.0)},
	{"name": "m_rail_s", "yaw": -113.0, "pitch": 4.0, "pos": Vector3(-73.0, -5.5, 2.0)},
	# And walking off the foot of it, which is the standpoint the setback exists
	# to protect.
	{"name": "n_rail_n_foot", "yaw": 30.0, "pitch": 2.0, "pos": Vector3(-68.0, -5.5, -4.5)},
]

const NIGHT := [
	{"name": "f_night_court", "yaw": -90.0, "pitch": -8.0, "pos": Vector3(-70.0, -5.5, -2.0)},
	{"name": "g_night_close", "yaw": -90.0, "pitch": -10.0, "pos": Vector3(-66.5, -5.5, -2.0)},
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
		await _shoot(shot)
	for shot in BANK:
		await _shoot(shot)

	ParkClock.set_clock(21, 15)
	await get_tree().create_timer(3.0).timeout
	for shot in NIGHT:
		await _shoot(shot)

	get_tree().quit()


func _shoot(shot: Dictionary) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	# Dropped rather than placed: the court floor is at −6 and a pose written at
	# court height starts the body three metres up. Enough frames to land.
	for _i in 40:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "user://niche_%s.png" % shot["name"]
	img.save_png(path)
	# The camera is on a 2.6m spring arm and is not at `pos`. Printed rather than
	# assumed, which is the only reason the arch's own clearances were ever right.
	var cam := get_viewport().get_camera_3d()
	print("saved ", path, "  eye ", cam.global_position if cam != null else "?")
