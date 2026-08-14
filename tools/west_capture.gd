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

## The plaza's side of the seam, which is now everything *before* the middle of
## the tunnel — the crossing sits at x −38.5 and these all stand east of it.
##
## The question they answer is whether the approach narrows. The plaza is 104m
## across, the forecourt in front of the gate house is 8m of asphalt, the tunnel
## is 6m wide and 5m clear, and the flight past it is 4m. If the sequence does
## not tighten, the reveal on the far side has nothing to open out of.
##
## **These used to run all the way down to the gate at the foot of the stair**,
## which was correct while the seam was down there and became a tool driving the
## player through a crossing volume the moment it moved up to the arch. Anything
## west of the tunnel's middle belongs in the list below now.
const APPROACH := [
	# From the ring's own west vertex, which is where the decision to walk west
	# gets made. Not from across the plaza: the fountain is 18m across and stands
	# on the axis, so the far half of the west spoke has no view of the arch at
	# all — which is a fact about the hub rather than a bad camera.
	{"name": "01_from_the_ring", "yaw": 92.0, "pitch": 7.0, "pos": Vector3(-16.0, 0.2, 0.0)},
	# Off the axis, because the walk west off the ring does not arrive square to
	# it. Kept on the spoke's own paving — anywhere off it is somewhere a tree may
	# be standing this regeneration and not the last.
	{"name": "02_gate_house", "yaw": 104.0, "pitch": 8.0, "pos": Vector3(-19.0, 0.2, 1.5)},
	# Where the asphalt stops. The floor changing under you at the piers is the
	# park saying the passage is not the plaza.
	{"name": "03_forecourt", "yaw": 90.0, "pitch": 1.0, "pos": Vector3(-25.0, 0.2, -2.0)},
	{"name": "04_mouth", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-29.5, 0.2, -2.0)},
	# Inside, and short of the crossing. What this has to show is a far end that
	# is a bright rectangle rather than a view.
	{"name": "05_in_the_tunnel", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-35.5, 0.2, -2.0)},
]

## The far side, in walking order, beginning on the terrace — because the player
## arrives there now rather than at the foot of the stair.
##
## `06` and `07` are the pair the crossing is judged on: what you see having
## stepped out of the tunnel, and what you see turning round to look back at it.
## The second is the one that catches a hole, since the plaza is not mounted here
## and everything behind the arch is a copy.
##
## `13` is the one the descent was rebuilt for: from the lane, looking back at
## what you came down. Both ends have to read as the same place, and until
## 2026-08-14 they could not — the flight was inside the rock.
##
## `17` and `18` are the older pair that still matters: the alley is nine metres
## of building with nothing in it, and then the whole section arrives sideways.
## If the second of those is not a surprise, the frontage is not doing its job.
const ARRIVED := [
	{"name": "06_out_of_the_tunnel", "yaw": 90.0, "pitch": -2.0, "pos": Vector3(-45.5, 0.2, -2.0)},
	{"name": "07_looking_back", "yaw": -90.0, "pitch": 2.0, "pos": Vector3(-46.0, 0.2, -2.0)},
	# In the gap in the parapet, which is on the arch's axis — so the way down is
	# straight ahead rather than eight metres off to one side.
	{"name": "08_the_way_down", "yaw": 90.0, "pitch": -10.0, "pos": Vector3(-50.5, 0.2, -2.0)},
	# Over the rail, south of the gap. What the overlook is for.
	{"name": "09_overlook", "yaw": 92.0, "pitch": -6.0, "pos": Vector3(-49.0, 0.2, 4.0)},
	{"name": "10_head_of_the_flight", "yaw": 178.0, "pitch": -22.0, "pos": Vector3(-59.2, 0.2, -2.5)},
	{"name": "11_halfway_down", "yaw": 178.0, "pitch": -10.0, "pos": Vector3(-59.9, -2.8, 4.9)},
	{"name": "12_foot", "yaw": 4.0, "pitch": 0.0, "pos": Vector3(-60.5, -5.8, 11.0)},
	# **The shot the rebuild is for.** From the lane, looking back at what you came
	# down. If the flight, the bluff top, the parapet and the arch above it do not
	# read as the place you were standing two minutes ago, the descent is still
	# hidden and this is still a cliff with a hole in it.
	{"name": "13_look_back_up", "yaw": -22.0, "pitch": 10.0, "pos": Vector3(-65.0, -5.8, 22.0)},
	{"name": "14_up_the_lane", "yaw": 6.0, "pitch": 0.0, "pos": Vector3(-63.6, -5.8, 8.0)},
	{"name": "15_flight_from_north", "yaw": -150.0, "pitch": 12.0, "pos": Vector3(-63.6, -5.8, -6.0)},
	{"name": "16_alley_mouth", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-64.5, -5.8, -1)},
	{"name": "17_in_the_alley", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-70, -5.8, -1)},
	{"name": "18_reveal", "yaw": 90.0, "pitch": 1.0, "pos": Vector3(-76, -5.8, -1)},
	{"name": "19_reveal_north", "yaw": 20.0, "pitch": 2.0, "pos": Vector3(-76, -5.8, -1)},
	{"name": "20_reveal_south", "yaw": 160.0, "pitch": 0.0, "pos": Vector3(-76, -5.8, -1)},
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
	# Back east at the bluff, and both of these were aimed at things they had
	# stopped showing. `29` stood on the gap's own axis, so what filled the frame
	# was the alley mouth rather than the rise behind it; `30` had been walked
	# west over the years until it was pointing at the shopfronts.
	#
	# `29` is the shot that says whether the plaza still exists from down here.
	# On the gap's own axis, which is the only line from the strip with no shopfront
	# in it. Everywhere else the frontage is 4.5 to 11m tall and its *near* roof
	# edge is seven metres from the promenade, so the rise behind it is cropped —
	# opposite the lowest unit on the row it still did not clear. That is a fact
	# about the section rather than a bad camera: from the strip you cannot see the
	# plaza, and the boardwalk being somewhere else is the point.
	#
	# Through the gap you can, and it is the whole west composition run backwards:
	# from the overlook the arch frames the gap and the gap frames the pier; from
	# the pier the gap frames the bluff and the plaza standing on it.
	{"name": "29_back_east", "yaw": -90.0, "pitch": 12.0, "pos": Vector3(-88, -5.8, -1)},
	{"name": "30_bluff", "yaw": -118.0, "pitch": 7.0, "pos": Vector3(-66.5, -5.8, -1)},
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
