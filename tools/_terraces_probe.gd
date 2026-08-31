extends Node

## Dev probe: **the terraces district, seen from inside itself.**
##
## The park is persistent now, so this walks east to verify the actual continuous
## composition rather than waiting for a section swap or photographing a far
## copy. What it is asking remains useful: from every terrace level, is the park
## still legible behind you and does the real rim close the view ahead?
const SETTLE := 6.0
const WALK_LIMIT := 25.0

## Where the walk starts and what it aims at. Both on the east spoke's own centre
## line, and the target is past the crossing at a point the player cannot reach
## on foot — walking at something unreachable is how a seam gets tripped rather
## than merely approached. `section_test.gd` uses the same trick and says so.
const START := Vector3(24.0, 0.2, -2.0)
const AIM := Vector3(60.0, 0.2, -2.0)

## Free-camera standpoints inside the terraces, once the walk has happened.
##
## The first four are the whole question — back down the axis from the places the
## section delivers you to. The rest check the other three bearings, because a
## section that only looks right in the direction it was fixed for is a section
## nobody has walked round.
const SHOTS := [
	# From the forecourt, square at the gate. This is the frame that was empty.
	{"name": "a_court_back_west", "pos": Vector3(56.0, 1.7, -2.0), "yaw": 90.0, "pitch": -2.0},
	# Further out, where the wall should read as a wall with a park behind it.
	{"name": "b_foot_back_west", "pos": Vector3(64.0, 1.7, -2.0), "yaw": 90.0, "pitch": 0.0},
	# From the belvedere, over the parapet and down the axis at the clock tower —
	# the view the whole climb is for, and the one `_hill_probe` could only take
	# with the plaza mounted.
	{"name": "c_belvedere_west", "pos": Vector3(76.0, 7.7, -2.0), "yaw": 90.0, "pitch": -4.0},
	# From the head of the staircase, which is the deepest standpoint in the
	# section and the furthest the massing has to carry.
	{"name": "d_head_west", "pos": Vector3(112.0, 13.7, -2.0), "yaw": 90.0, "pitch": -5.0},
	# East, at the persistent rim. If the shared skyline is missing, this is sky.
	{"name": "e_head_east", "pos": Vector3(108.0, 13.7, -2.0), "yaw": -90.0, "pitch": 4.0},
	# North and south off the belvedere, for the two bearings nothing has asked
	# about since the section existed.
	{"name": "f_belvedere_north", "pos": Vector3(78.0, 7.7, -2.0), "yaw": 180.0, "pitch": 2.0},
	{"name": "g_belvedere_south", "pos": Vector3(78.0, 7.7, -2.0), "yaw": 0.0, "pitch": 2.0},
	# And from above, which is the only way to read the whole continuous join.
	{"name": "h_over_the_gate", "pos": Vector3(70.0, 34.0, -2.0), "yaw": 90.0, "pitch": -26.0},
]

var _player: CharacterBody3D
var _crossed := false


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	await get_tree().create_timer(SETTLE).timeout

	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if _player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	ParkSections.section_entered.connect(func(id: StringName) -> void:
		if id == &"terraces":
			_crossed = true)

	_player.global_position = START
	_player.velocity = Vector3.ZERO
	var t := 0.0
	while not _crossed and t < WALK_LIMIT:
		# Steered rather than driven: yaw is set and forward is held, which is
		# `section_test`'s rig. Released while the transition has the player, or
		# the input fights the rails it is riding.
		if _player.has_method("is_crossing") and _player.is_crossing():
			if Input.is_action_pressed("move_forward"):
				Input.action_release("move_forward")
		else:
			var to: Vector3 = AIM - _player.global_position
			_player.rotation.y = atan2(-to.x, -to.z)
			if not Input.is_action_pressed("move_forward"):
				Input.action_press("move_forward")
		t += get_process_delta_time()
		await get_tree().physics_frame
	if Input.is_action_pressed("move_forward"):
		Input.action_release("move_forward")

	if not _crossed:
		push_error("never crossed into the terraces — the gate did not catch the player")
		get_tree().quit(1)
		return
	print("crossed into '%s' at %v" % [ParkSections.current(), _player.global_position])

	# Let the fade finish and the section settle before anything is photographed.
	await get_tree().create_timer(4.0).timeout

	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true
	for shot in SHOTS:
		cam.global_position = shot["pos"]
		cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
		for _i in 4:
			await get_tree().physics_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("user://terr_%s.png" % shot["name"])
		print("saved ", shot["name"])

	get_tree().quit()
