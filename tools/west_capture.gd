extends Node

## Dev tool: the walk from the plaza to the boardwalk, shot in order.
##
## Separate from `capture.gd` rather than folded into it, because this one has to
## cross a section boundary halfway through and `capture.gd`'s whole structure is
## "pose the player in the plaza and read the frame". A pass that changes which
## section is mounted is a different kind of run, and mixing them would mean
## every plaza shot paid for a boardwalk load.
##
## Shot at the end of the afternoon on purpose. The boardwalk is west because the
## sun sets into it — that is the reason the section exists on that side — so
## every judgement about whether it reads is a judgement about it in this light.
## The last two shots step the clock on to catch the sun actually going down
## behind the pavilion, which is the composition the whole west was laid out for.

const HOUR := 19
const MINUTE := 0

## Everything up to and including the shut gate. The question these answer is
## whether the approach *narrows*: the arch is wide, the terrace is wider, the
## stair is 2.6m, and the gate at the bottom is the whole frame. If the sequence
## does not tighten, the reveal on the far side has nothing to open out of.
const APPROACH := [
	{"name": "01_arch", "yaw": 90.0, "pitch": 3.0, "pos": Vector3(16.0, 0.2, -2.0)},
	{"name": "02_under_arch", "yaw": 90.0, "pitch": 1.0, "pos": Vector3(-39.0, 0.2, -2.0)},
	{"name": "03_overlook", "yaw": 88.0, "pitch": 0.0, "pos": Vector3(-49, 0.2, -2)},
	{"name": "04_overlook_down", "yaw": 92.0, "pitch": -18.0, "pos": Vector3(-49.5, 0.2, -2)},
	{"name": "05_stair_head", "yaw": 62.0, "pitch": -8.0, "pos": Vector3(-46, 0.2, -6)},
	{"name": "06_stair_turn", "yaw": 178.0, "pitch": -16.0, "pos": Vector3(-56.7, -0.6, -9.7)},
	{"name": "07_stair_down", "yaw": 178.0, "pitch": -6.0, "pos": Vector3(-56.7, -3, -2)},
	# The gate, from inside the well, which is the last thing seen before the cut.
	{"name": "08_gate", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-56.2, -5.6, 5.5)},
]

## The far side, in walking order. `04` and `05` are the pair that matters: the
## alley is nine metres of building with nothing in it, and then the whole
## section arrives sideways. If the second of those is not a surprise, the
## frontage is not doing its job and the gap wants narrowing.
const ARRIVED := [
	{"name": "09_arrival", "yaw": 8.6, "pitch": 0.0, "pos": Vector3(-61.5, -5.8, 12)},
	{"name": "10_gate_behind", "yaw": -60.0, "pitch": 2.0, "pos": Vector3(-61.5, -5.8, 9)},
	{"name": "11_lane", "yaw": 8.0, "pitch": -1.0, "pos": Vector3(-61.8, -5.8, 7)},
	{"name": "12_alley_mouth", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-63.5, -5.8, -1)},
	{"name": "13_in_the_alley", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-70, -5.8, -1)},
	{"name": "14_reveal", "yaw": 90.0, "pitch": 1.0, "pos": Vector3(-76, -5.8, -1)},
	{"name": "15_reveal_north", "yaw": 20.0, "pitch": 2.0, "pos": Vector3(-76, -5.8, -1)},
	{"name": "16_reveal_south", "yaw": 160.0, "pitch": 0.0, "pos": Vector3(-76, -5.8, -1)},
	# The strip, both ways, from the middle of the paving.
	{"name": "17_prom_north", "yaw": 0.0, "pitch": 2.0, "pos": Vector3(-80, -5.8, 6)},
	{"name": "18_prom_south", "yaw": 180.0, "pitch": 0.0, "pos": Vector3(-80, -5.8, -20)},
	{"name": "19_shopfronts", "yaw": 125.0, "pitch": 2.0, "pos": Vector3(-82, -5.8, 8)},
	# The three anchors, close enough to judge as objects rather than silhouettes.
	{"name": "20_wheel", "yaw": 90.0, "pitch": 22.0, "pos": Vector3(-78, -5.8, -16)},
	{"name": "21_wheel_along", "yaw": 12.0, "pitch": 14.0, "pos": Vector3(-80, -5.8, 2)},
	{"name": "22_coaster", "yaw": -60.0, "pitch": 8.0, "pos": Vector3(-82, -5.8, -30)},
	{"name": "23_under_coaster", "yaw": 20.0, "pitch": 12.0, "pos": Vector3(-78, -5.8, -58)},
	{"name": "24_pier_mouth", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-88, -5.8, -1)},
	{"name": "25_pier_out", "yaw": 90.0, "pitch": 2.0, "pos": Vector3(-112, -5.8, -1)},
	{"name": "26_pavilion", "yaw": 90.0, "pitch": 10.0, "pos": Vector3(-130, -5.8, -1)},
	# The section photographing itself, which is the argument for the pier being
	# walkable at all: forty metres offshore is the only place the whole strip is
	# in one frame.
	{"name": "27_from_the_pier", "yaw": -80.0, "pitch": 3.0, "pos": Vector3(-124, -5.8, -1)},
	{"name": "28_from_the_pier_n", "yaw": -50.0, "pitch": 4.0, "pos": Vector3(-124, -5.8, -1)},
	# Back east at the bluff. This is the shot that says whether the plaza still
	# exists from down here — the parapet, the buildings on the rise, and the
	# sign tower clearing the top of the bluff.
	{"name": "29_back_east", "yaw": -90.0, "pitch": 8.0, "pos": Vector3(-82, -5.8, 2)},
	{"name": "30_bluff", "yaw": -70.0, "pitch": 10.0, "pos": Vector3(-74, -5.8, 20)},
]

## The reason the boardwalk is west. Sunset is about 20:20 for this latitude, so
## these bracket it: the low light down the strip, and the sun behind the
## pavilion at the head of the pier.
const SUNSET := [
	{"time": [19, 30], "name": "31_evening_strip", "yaw": 172.0, "pitch": 3.0,
		"pos": Vector3(-82, -5.8, -34)},
	{"time": [20, 20], "name": "32_sunset_pier", "yaw": 90.0, "pitch": 4.0,
		"pos": Vector3(-82, -5.8, -1)},
	{"time": [20, 20], "name": "33_sunset_wheel", "yaw": 118.0, "pitch": 14.0,
		"pos": Vector3(-76, -5.8, -6)},
	{"time": [21, 15], "name": "34_dusk_bulbs", "yaw": 160.0, "pitch": 2.0,
		"pos": Vector3(-84, -5.8, -30)},
	# The claim, and the same frame twice to test it. `design.md` asks the player
	# to read the hour off the park; the plaza does it with a headcount and with
	# whether the cafe is full. The boardwalk's version is that it is nearly
	# empty when the plaza is busy and full when the plaza is going home. If
	# these two pictures are the same picture, the curves are a number in a file.
	{"time": [11, 0], "name": "35_eleven_am", "yaw": 172.0, "pitch": 1.0,
		"pos": Vector3(-82, -5.8, -34)},
	{"time": [19, 0], "name": "36_seven_pm", "yaw": 172.0, "pitch": 1.0,
		"pos": Vector3(-82, -5.8, -34)},
]

const SETTLE_SECONDS := 7.0

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(HOUR, MINUTE)
	await get_tree().create_timer(SETTLE_SECONDS).timeout

	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")

	for shot in APPROACH:
		await _shoot(shot, shot["name"])

	# Straight in rather than walked. The crossing itself is `section_test.gd`'s
	# job and it already passes; what this run is for is what the far side looks
	# like once it is standing.
	await ParkSections.enter(&"boardwalk", &"plaza")
	# The strip's crowd is generated standing where it was put down. A settle beat
	# is what turns fifty-seven people facing random directions into a promenade.
	await get_tree().create_timer(SETTLE_SECONDS).timeout
	if ParkSections.current() != &"boardwalk":
		push_error("the boardwalk did not mount")
		get_tree().quit(1)
		return

	for shot in ARRIVED:
		await _shoot(shot, shot["name"])

	for shot in SUNSET:
		var t: Array = shot["time"]
		ParkClock.set_clock(t[0], t[1])
		# A jump re-places the crowd rather than walking it in, so each of these is
		# the strip as that hour actually holds it — after a beat for guests to
		# pick a route and turn their heads.
		await get_tree().create_timer(2.5).timeout
		await _shoot(shot, shot["name"])

	get_tree().quit()


func _shoot(shot: Dictionary, label: String) -> void:
	_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "user://west_%s.png" % label
	img.save_png(path)
	print("saved ", path)
