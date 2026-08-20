extends Node

## Dev probe: **the two stand-ins for the plaza, against the plaza itself.**
##
## `_plaza_from_below` and `_plaza_from_the_east` each stand a massing copy of the
## hand-authored plaza up in the section that has just deleted it. The question
## nobody has ever put a picture to is whether the copy looks like the thing it
## replaces — and it cannot be answered from one section, because the two are
## mutually exclusive by construction: a player standing where the stand-in is
## visible can never see the original from the same spot.
##
## So every camera here is shot **three times**: once with `plaza` standing (the
## real thing, with its frontage, fountain, paving, props and clock faces), once
## with `boardwalk` standing (the west stand-in), once with `terraces` standing
## (the east one). Same position, same bearing, same hour. The pairs are the
## report; a single frame of a grey box says nothing about what it is standing in
## for.
##
## Free camera throughout. Half of these standpoints are on ground one of the
## three sections does not own, so a body put there falls out of the frame — and
## the point is to hold the camera still across a swap, which is the one thing a
## player-mounted shot cannot do.

const SETTLE := 7.0

## Standpoints on the west side of the plaza, aimed back at it. The bluff top is
## y 0 and the shore is at −6, so these climb as they come in.
const WEST := [
	# On the terrace, two metres from the arch's west reveal. The near boundary:
	# whatever this wall is wearing is what the player is standing against.
	{"name": "w1_terrace", "pos": Vector3(-42.0, 1.7, -2.0), "yaw": -90.0, "pitch": 2.0},
	# The overlook parapet, looking back east at the wall and the arch in it.
	{"name": "w2_overlook", "pos": Vector3(-49.0, 1.7, -2.0), "yaw": -90.0, "pitch": 4.0},
	# Off the axis on the terrace, where the wall is a run rather than an opening.
	{"name": "w3_terrace_north", "pos": Vector3(-47.0, 1.7, -12.0), "yaw": -66.0, "pitch": 8.0},
	# The back lane / arrival court, at the foot of the cascade looking up.
	{"name": "w4_court", "pos": Vector3(-74.0, -4.3, -2.0), "yaw": -90.0, "pitch": 14.0},
	# The promenade, mid-strip. Sixty metres out and five below.
	{"name": "w5_promenade", "pos": Vector3(-99.2, -4.3, -10.0), "yaw": -90.0, "pitch": 12.0},
	# The alley mouth, on the axis, which is the layered shot the arches were
	# aligned for.
	{"name": "w6_alley", "pos": Vector3(-92.0, -4.3, -2.0), "yaw": -90.0, "pitch": 10.0},
	# The pier head. The furthest anybody stands, and the shallowest angle over
	# the shop roofs.
	{"name": "w7_pier_head", "pos": Vector3(-148.0, -4.3, -2.0), "yaw": -90.0, "pitch": 6.0},
]

## Standpoints east of the plaza, aimed back through the gate at it. These climb
## the cascade and then the basin staircase, which is the whole reason the east
## sees more of the plaza than the west does.
const EAST := [
	# The forecourt, on the axis, at the gate's outer face.
	{"name": "e1_court", "pos": Vector3(52.0, 1.7, -2.0), "yaw": 90.0, "pitch": -1.0},
	# The foot of the climb, back through the 13.5m passage.
	{"name": "e2_foot", "pos": Vector3(60.0, 1.7, -2.0), "yaw": 90.0, "pitch": -1.0},
	# The belvedere parapet at y 6, which is the first standpoint that is *above*
	# the beam's soffit and looks down into the plaza rather than through at it.
	{"name": "e3_belvedere", "pos": Vector3(71.0, 7.7, -2.0), "yaw": 90.0, "pitch": -4.0},
	# The belvedere's north end, off the axis.
	{"name": "e4_belvedere_n", "pos": Vector3(76.0, 7.7, -17.0), "yaw": 112.0, "pitch": -4.0},
	# Terrace two at y 12, the head of the climb: forty metres up the hill and
	# six over the east wall's shorter runs.
	{"name": "e5_terrace_two", "pos": Vector3(108.0, 13.7, -2.0), "yaw": 90.0, "pitch": -4.0},
	# Elevated on the axis, which is not a standpoint. It is the control frame:
	# everything the two stand-ins could possibly need to carry is in it.
	{"name": "e6_free_high", "pos": Vector3(90.0, 26.0, -2.0), "yaw": 90.0, "pitch": -10.0},
]

var _cam: Camera3D


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	await get_tree().create_timer(SETTLE).timeout

	_cam = Camera3D.new()
	add_child(_cam)
	_cam.current = true

	# The plaza is already standing — `main.gd` adopts it on frame one — so the
	# reference pass costs no swap.
	await _pass("plaza")

	await _swap(&"boardwalk", &"plaza")
	await _pass("boardwalk")

	# Back through the plaza, because `enter` takes a `from` and the sections do
	# not neighbour each other.
	await _swap(&"plaza", &"boardwalk")
	await _swap(&"terraces", &"plaza")
	await _pass("terraces")

	get_tree().quit()


func _swap(to: StringName, from: StringName) -> void:
	print("--- swapping to ", to)
	await ParkSections.enter(to, from)
	# The fade and the held shot both belong to the swap; take the camera back.
	_cam.current = true
	await get_tree().create_timer(3.0).timeout


func _pass(tag: String) -> void:
	for shot in WEST:
		await _shoot(tag, shot)
	for shot in EAST:
		await _shoot(tag, shot)


func _shoot(tag: String, shot: Dictionary) -> void:
	_cam.global_position = shot["pos"]
	_cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
	_cam.current = true
	for _i in 8:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "user://mass_%s_%s.png" % [shot["name"], tag]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path, "  eye ", _cam.global_position)
