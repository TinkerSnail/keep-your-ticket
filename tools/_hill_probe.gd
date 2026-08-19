extends Node

## Dev probe: the east hill — the scarp, the shelf cut into it, and the terrace
## above.
##
## Its own throwaway rather than legs in `_east_probe.gd`, for the usual reason:
## that probe asks whether the gate frames the monument, and this asks whether
## the monument arrives somewhere. Different question, different standpoints.
##
## **Half of these are the first views from a place that did not exist before
## 2026-08-18.** The shelf is reached only by climbing a cascade wing, so nothing
## in any earlier capture pass could have stood here, and the belvedere's whole
## claim — that the walk up is worth making because of what you see from the top
## — has never been looked at by anybody.
##
## The other half are the check that the hill did not cost the gate its picture.
## A 12m scarp either side of the monument and a 6m terrace face behind it are
## both inside the cone the opening frames, so what was monument-then-ridge is
## now monument-then-terrace-then-ridge. Three planes is the better composition
## if it reads as three planes and a wall across the frame if it does not.
##
## Yaw −90 is east, +90 is west. Godot's forward is −Z.

const SETTLE := 6.0
const HEAD := 6.0

## From below: the court, and what the scarp does to it.
const COURT := [
	# On the axis, backed against the gate. The monument, and now a hillside
	# behind it rather than sky.
	{"name": "a_court_axis", "yaw": -90.0, "pitch": 6.0, "pos": Vector3(50.0, 1.2, -2.0)},
	# Off to the north, square at the stretch of scarp the monument does not
	# cover. This is the face that did not exist yesterday and it is 12m of it.
	{"name": "b_court_north", "yaw": -90.0, "pitch": 10.0, "pos": Vector3(52.0, 1.2, -22.0)},
	{"name": "c_court_south", "yaw": -90.0, "pitch": 10.0, "pos": Vector3(52.0, 1.2, 18.0)},
	# Standing at the foot of the climb looking up the north wing, which is the
	# view that has to say "this goes somewhere".
	{"name": "d_foot_of_climb", "yaw": -58.0, "pitch": 12.0, "pos": Vector3(58.5, 1.2, -2.0)},
]

## The climb itself, from the turn up. Nobody has been up here.
const CLIMB := [
	{"name": "e_wing_turn", "yaw": -90.0, "pitch": 8.0, "pos": Vector3(62.5, 3.2, -12.0)},
	{"name": "f_wing_head", "yaw": -90.0, "pitch": 2.0, "pos": Vector3(66.5, HEAD + 0.2, -5.5)},
	# On the landing, at the head of the monument, about to step through the
	# parapet's gap. The one stride the sill laps.
	{"name": "g_landing", "yaw": -90.0, "pitch": 0.0, "pos": Vector3(68.0, HEAD + 0.2, -2.0)},
]

## On the shelf. **The west frame is the one the whole hill is for** — if the
## belvedere does not pay for the climb from here, the shape is wrong and no
## amount of dressing on the scarp fixes it.
const SHELF := [
	{"name": "h_belvedere_west", "yaw": 90.0, "pitch": -4.0, "pos": Vector3(76.0, HEAD + 0.2, -2.0)},
	# Hard against the parapet, leaning over it at the court six metres down.
	# A guard is either something you lean on or something in your way.
	{"name": "i_over_the_parapet", "yaw": 90.0, "pitch": -18.0, "pos": Vector3(71.5, HEAD + 0.2, -12.0)},
	# East, at the second scarp and the rim standing over it. Two terraces and a
	# ridge, which is the whole east in one frame and the only place it exists.
	{"name": "j_shelf_east", "yaw": -90.0, "pitch": 10.0, "pos": Vector3(74.0, HEAD + 0.2, -2.0)},
	# The two walls. A notch is only a notch if its ends read as hillside rather
	# than as the back of a set.
	{"name": "k_shelf_north", "yaw": 180.0, "pitch": 6.0, "pos": Vector3(78.0, HEAD + 0.2, 4.0)},
	{"name": "l_shelf_south", "yaw": 0.0, "pitch": 6.0, "pos": Vector3(78.0, HEAD + 0.2, -8.0)},
	# Along it, which is the walk rather than the view.
	{"name": "m_shelf_length", "yaw": 180.0, "pitch": -2.0, "pos": Vector3(76.0, HEAD + 0.2, 12.0)},
	# **The basin staircase**, which is what the belvedere turned out to be the
	# bottom of. Square up the axis from behind the collecting pool, then from the
	# flight itself, then back down the whole feature from the head — the three
	# views the reference photographs are taken from.
	{"name": "ma_pool_and_chain", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(76.5, HEAD + 0.2, -2.0)},
	{"name": "mb_mouth_up", "yaw": -90.0, "pitch": 8.0, "pos": Vector3(84.5, HEAD + 0.2, -2.0)},
	{"name": "mc_on_the_flight", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(92.0, 7.7, -7.65)},
	{"name": "md_flight_across", "yaw": -60.0, "pitch": -2.0, "pos": Vector3(97.0, 9.2, -7.65)},
	{"name": "me_head_looking_back", "yaw": 90.0, "pitch": -8.0, "pos": Vector3(109.0, 12.2, -2.0)},
	{"name": "mf_head_over_park", "yaw": 90.0, "pitch": -3.0, "pos": Vector3(112.0, 13.4, -2.0)},
]

## From the plaza, through the gap — the check that the hill did not cost the
## gate its picture. Same standpoints `_east_probe.gd` uses, so the two runs can
## be laid side by side.
const THROUGH := [
	{"name": "n_near_stand", "yaw": -90.0, "pitch": 0.0, "pos": Vector3(11.0, 1.2, -2.0)},
	{"name": "o_ring", "yaw": -90.0, "pitch": 0.0, "pos": Vector3(16.0, 1.2, -2.0)},
	{"name": "p_at_the_mouth", "yaw": -90.0, "pitch": 0.0, "pos": Vector3(31.0, 1.2, -2.0)},
]

## Morning and night on the belvedere. The shelf faces west, so it takes the
## afternoon sun full on its own face and the whole park is backlit from it at
## ten — the opposite of the rim, one hillside away.
const HOURS := [
	{"name": "q_morning_belvedere", "yaw": 90.0, "pitch": -4.0, "pos": Vector3(76.0, HEAD + 0.2, -2.0), "h": 10, "m": 0},
	{"name": "r_evening_belvedere", "yaw": 90.0, "pitch": -4.0, "pos": Vector3(76.0, HEAD + 0.2, -2.0), "h": 19, "m": 30},
	{"name": "s_night_belvedere", "yaw": 90.0, "pitch": -4.0, "pos": Vector3(76.0, HEAD + 0.2, -2.0), "h": 21, "m": 15},
	# And the climb after dark, which is the one that decides whether the shelf
	# needs a lamp on it. Nothing up here is lit.
	{"name": "t_night_climb", "yaw": -58.0, "pitch": 12.0, "pos": Vector3(58.5, 1.2, -2.0), "h": 21, "m": 15},
	# The chain lit, which is the whole of what the historic photograph is of.
	{"name": "ta_night_chain", "yaw": -90.0, "pitch": 5.0, "pos": Vector3(80.0, HEAD + 0.2, -2.0), "h": 21, "m": 15},
	{"name": "tb_night_from_flight", "yaw": -75.0, "pitch": 2.0, "pos": Vector3(95.0, 8.5, -7.65), "h": 21, "m": 15},
]

## The whole hill from outside it, which no standpoint has — the shelf is walled
## and the court is under the scarp, so the two terraces and the notch between
## them can only be seen from the air.
const FREE := [
	{"name": "u_elev_section", "pos": Vector3(30.0, 26.0, -2.0), "yaw": -90.0, "pitch": -12.0},
	{"name": "v_elev_notch", "pos": Vector3(56.0, 30.0, -2.0), "yaw": -90.0, "pitch": -26.0},
	{"name": "w_elev_north", "pos": Vector3(70.0, 34.0, -70.0), "yaw": -8.0, "pitch": -20.0},
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

	for shot in COURT:
		await _shoot(shot)
	for shot in CLIMB:
		await _shoot(shot)
	for shot in SHELF:
		await _shoot(shot)
	for shot in THROUGH:
		await _shoot(shot)

	for shot in HOURS:
		ParkClock.set_clock(shot["h"], shot["m"])
		await get_tree().create_timer(3.0).timeout
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
	get_viewport().get_texture().get_image().save_png("user://hill_%s.png" % shot["name"])
	print("saved ", shot["name"])


func _shoot(shot: Dictionary) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 40:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("user://hill_%s.png" % shot["name"])
	# **Printed, and on this probe it is doing real work rather than ceremony.**
	# Half these standpoints are six metres up on ground the player is dropped
	# onto rather than walked onto, so a pose that misses the deck falls to the
	# court and photographs the scarp from below while looking exactly like a
	# shot from the shelf of a hill that is not there.
	var cam := get_viewport().get_camera_3d()
	print("saved ", shot["name"], "  body ", _player.global_position,
		"  eye ", cam.global_position if cam != null else "?")
