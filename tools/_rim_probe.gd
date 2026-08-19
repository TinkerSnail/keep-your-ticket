extends Node

## Dev probe: the rim, and whether it stands over the east roofline.
##
## `ParkPlan` has carried the rim's whole geometry since the east cascade went
## in — foot, crest, a seven-point profile and a `rim_crest` accessor with no
## callers — and the plan's argument for the crest height is entirely about what
## shows from inside the plaza. That argument has never been looked at, because
## until now there was nothing out there to look at.
##
## **The claim under test is a function of where you stand, not a number.** An
## eye at 1.7 clears the east wall's 11.5m top on a ray whose slope is set by how
## far the eye is *from that wall*, so walking east hides the ridge and walking
## west reveals it. Worked from the plan's own figures, before shooting:
##
##   x = +11 (the fountain's east coping)   ray reaches y 56 at the crest — none
##   x = -11 (the west coping)              y 35 — about 15m of crest
##   x = -16 (the ring's west vertex)       y 33 — about 17m
##   x = -36 (the plaza's west side)        y 27 — about 23m
##
## Two things fall out of that, and neither was in the plan. The plan's own
## "seven metres from the fountain" is taken at the plaza's **centre**, which is
## a point nobody can stand at — the fountain is eighteen metres across and
## sitting on it — so it is a datum rather than a standpoint, and the nearest
## place anyone can actually stand on that line sees none of the ridge at all.
##
## And x = -36 on this line is **inside the west gate house**, because the west
## arch is cut on the same axis. So the westmost standpoint on the park's own
## east-west line is under the west arch, and the deepest view east in the park
## is taken from the mouth of the way west. Shot as found rather than nudged out
## onto the plaza floor: that is where a player walking this line stands.
##
## Yaw −90 is east. Godot's forward is −Z, so a yaw of θ points at
## `(−sin θ, −cos θ)`, and `_east_probe.gd` took nineteen frames the wrong way
## before anybody noticed. The eye is printed on every shot for the same reason:
## the spring arm hangs the camera about 2.5m behind the pose and pitching up
## swings it down, so the standpoint is never where the picture is taken from.

const SETTLE := 6.0

## Over the wall, backing away. The whole sequence is one claim — a distant ridge
## should open up as you retreat from it — and it can only be read as a run.
const OVER := [
	{"name": "a_east_coping", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(11.0, 1.2, -2.0)},
	{"name": "b_west_coping", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(-11.0, 1.2, -2.0)},
	{"name": "c_ring_west", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(-16.0, 1.2, -2.0)},
	# Under the west arch, and see the header — this is not the plaza floor.
	{"name": "d_west_arch", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(-36.0, 1.2, -2.0)},
	# The last of it that is on the plaza's own paving, in front of the mouth.
	{"name": "d2_plaza_west", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(-30.0, 1.2, -2.0)},
	# Off the axis, where the ridge has to be a ridge rather than a backdrop
	# behind one gate. The profile falls 50 → 40 over a hundred metres of z and
	# this is the only frame that can show whether that reads as a profile.
	{"name": "e_north_west", "yaw": -62.0, "pitch": 4.0, "pos": Vector3(-30.0, 1.2, -30.0)},
	{"name": "f_south_west", "yaw": -118.0, "pitch": 4.0, "pos": Vector3(-30.0, 1.2, 26.0)},
]

## Through the gap, which sees the other half of it: the foot and the lower
## slope, cropped near 29m by the beam. The two views share no ground at all.
const THROUGH := [
	{"name": "g_at_the_mouth", "yaw": -90.0, "pitch": 0.0, "pos": Vector3(31.0, 1.2, -2.0)},
	{"name": "h_in_the_passage", "yaw": -90.0, "pitch": 0.0, "pos": Vector3(40.0, 1.2, -2.0)},
	{"name": "i_court", "yaw": -90.0, "pitch": 2.0, "pos": Vector3(56.0, 1.2, -2.0)},
]

## Morning, and it is not a duplicate frame. The sun rises north-east, so at ten
## the ridge is backlit and the face the plaza looks at is entirely in shade;
## by half three the sun is west and rakes it. A landform with no lights on it
## has only those two readings, and the one that can fail is the first — a
## shadowed ridge against a bright sky is a silhouette or it is a smudge.
const MORNING := [
	{"name": "j_morning_west_arch", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(-36.0, 1.2, -2.0)},
	{"name": "k_morning_mouth", "yaw": -90.0, "pitch": 0.0, "pos": Vector3(31.0, 1.2, -2.0)},
]

## After dark. Nothing out here is lit and nothing should be — it is 150m of
## landform, and a ridge with lamps on it is a ride. The question is only whether
## it goes to a flat black hole in the sky or keeps an edge.
const NIGHT := [
	{"name": "l_night_west_arch", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(-36.0, 1.2, -2.0)},
]

## The whole thing at once, which no standpoint in the park can show — the same
## reason `_cascade_probe.gd` shoots from over the shop roofs. This is the frame
## that says whether the crest is a ridge line or a row of facets.
const FREE := [
	{"name": "m_elev_axis", "pos": Vector3(-30.0, 30.0, -2.0), "yaw": -90.0, "pitch": -4.0},
	{"name": "n_elev_high", "pos": Vector3(-20.0, 70.0, -2.0), "yaw": -90.0, "pitch": -14.0},
	# Along the ridge rather than at it, which is where banding would show.
	{"name": "o_elev_along", "pos": Vector3(96.0, 46.0, -150.0), "yaw": -14.0, "pitch": -6.0},
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

	for shot in OVER:
		await _shoot(shot)
	for shot in THROUGH:
		await _shoot(shot)

	ParkClock.set_clock(10, 0)
	await get_tree().create_timer(3.0).timeout
	for shot in MORNING:
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
	var path := "user://rim_%s.png" % shot["name"]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)


func _shoot(shot: Dictionary) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 40:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("user://rim_%s.png" % shot["name"])
	# Printed rather than assumed: the eye is not at `pos`, and the difference
	# is what decides how much of a 50m crest clears an 11.5m wall.
	var cam := get_viewport().get_camera_3d()
	print("saved ", shot["name"], "  eye ", cam.global_position if cam != null else "?")
