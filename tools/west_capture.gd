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
	# The shot the top came off for: square on the axis, pitched up far enough to
	# catch the wheel's rim, which tops at 25.80. Under a 5m soffit at the far end
	# of 13.5m of tube this framed masonry from y=12 up, which is most of the
	# height of the biggest silhouette in the west.
	#
	# **Shot from `ARCH_RIM_CLEAR_X`, which is where the promise binds and not
	# where the geometry is tightest.** The wheel stands 14m off the axis, so the
	# 6m slot hides most of it from far back and uncovers it as you approach —
	# 46% of it at x −11, 57% here, all of it by x −24. The rim is clipped from
	# −11 and −13 on purpose: those are the standpoints seeing under half a wheel
	# through a slot, and buying them costs 0.9m of beam and puts the sign back
	# into the crane angle. From here in, the rim must be whole.
	#
	# If the wheel is not whole here, the beam is too low or it has crept forward
	# — or somebody has raised the wheel, which has happened once already.
	#
	# **Do not raise the pitch to frame it better.** The camera is on a 2.6m spring
	# arm, so pitching up swings it *down*, and a lower eye needs a lower soffit to
	# clear the same rim — which makes the shot easier to pass. Measured in the
	# running game the camera sits near y 1.2 here and the margin is about 0.39m;
	# at y 1.75 it would be −0.03m and this frame would crop. The tidying instinct
	# and the test's sensitivity pull in opposite directions, so the pitch is part
	# of the assertion and not part of the composition.
	{"name": "01b_wheel_over_the_beam", "yaw": 90.0, "pitch": 11.0,
		"pos": Vector3(ParkPlan.ARCH_RIM_CLEAR_X, 0.2, -2.0)},
	# Off the axis, because the walk west off the ring does not arrive square to
	# it. Kept on the spoke's own paving — anywhere off it is somewhere a tree may
	# be standing this regeneration and not the last.
	{"name": "02_gate_house", "yaw": 104.0, "pitch": 8.0, "pos": Vector3(-19.0, 0.2, 1.5)},
	# Where the asphalt stops. The floor changing under you at the piers is the
	# park saying the passage is not the plaza.
	{"name": "03_forecourt", "yaw": 90.0, "pitch": 1.0, "pos": Vector3(-25.0, 0.2, -2.0)},
	{"name": "04_mouth", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-29.5, 0.2, -2.0)},
	# Inside, and short of the crossing.
	#
	# **This used to have to show a far end that was a bright rectangle rather
	# than a view.** The top came off on 2026-08-16 and it is the opposite now:
	# open sky overhead, the piers either side, and the west in the gap between
	# them. What it has to show is that the cutting still narrows — the frame is
	# 6m of pier at arm's length whichever way you look — and that the pitch below
	# is doing nothing, because with no soffit there is nothing left to duck.
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
	{"name": "09_overlook", "yaw": 92.0, "pitch": -8.0, "pos": Vector3(-49.0, 0.2, 4.0)},
	# North along the ledge, which is where the eleven metres a six-metre drop
	# needs are spent — and where the ramp's head is, further on.
	# Straight down it. No ledge walk and no deck: the flight leaves the bluff's
	# own edge heading the way you were already going.
	{"name": "10_head_of_the_flight", "yaw": 90.0, "pitch": -20.0, "pos": Vector3(-56.0, 0.2, -2.0)},
	{"name": "11_halfway_down", "yaw": 90.0, "pitch": -8.0, "pos": Vector3(-63.0, -2.8, -2.0)},
	{"name": "12_at_the_foot", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-69.0, -2.8, -2.0)},
	# The ramp, which is the other way down and has to read as one.
	{"name": "13_ramp_head", "yaw": 2.0, "pitch": -10.0, "pos": Vector3(-60.0, 0.2, -25.0)},
	{"name": "14_ramp_from_court", "yaw": -40.0, "pitch": 12.0, "pos": Vector3(-78.0, -2.8, -20.0)},
	{"name": "15_the_court", "yaw": 90.0, "pitch": 2.0, "pos": Vector3(-62.0, -2.8, -2.0)},
	{"name": "16_court_back_east", "yaw": -90.0, "pitch": 10.0, "pos": Vector3(-78.0, -2.8, -2.0)},
	{"name": "17_entry", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-64.5, -2.8, -2)},
	{"name": "18_in_the_alley", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-70, -2.8, -2)},
	{"name": "19_reveal", "yaw": 90.0, "pitch": 1.0, "pos": Vector3(-92, -2.8, -2)},
	{"name": "20_reveal_north", "yaw": 20.0, "pitch": 2.0, "pos": Vector3(-92, -2.8, -2)},
	{"name": "21_reveal_south", "yaw": 160.0, "pitch": 0.0, "pos": Vector3(-92, -2.8, -2)},
	# The strip, both ways, from the middle of the paving.
	{"name": "22_prom_north", "yaw": 0.0, "pitch": 2.0, "pos": Vector3(-96, -2.8, 6)},
	{"name": "23_prom_south", "yaw": 180.0, "pitch": 0.0, "pos": Vector3(-96, -2.8, -20)},
	{"name": "24_shopfronts", "yaw": 125.0, "pitch": 2.0, "pos": Vector3(-98, -2.8, 8)},
	# The three anchors, close enough to judge as objects rather than silhouettes.
	{"name": "25_wheel", "yaw": 90.0, "pitch": 22.0, "pos": Vector3(-94, -2.8, -16)},
	{"name": "26_wheel_along", "yaw": 12.0, "pitch": 14.0, "pos": Vector3(-96, -2.8, 2)},
	{"name": "27_coaster", "yaw": -60.0, "pitch": 8.0, "pos": Vector3(-98, -2.8, -30)},
	{"name": "28_under_coaster", "yaw": 20.0, "pitch": 12.0, "pos": Vector3(-94, -2.8, -58)},
	{"name": "29_pier_mouth", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-104, -2.8, -2)},
	{"name": "30_pier_out", "yaw": 90.0, "pitch": 2.0, "pos": Vector3(-128, -2.8, -2)},
	{"name": "31_pavilion", "yaw": 90.0, "pitch": 10.0, "pos": Vector3(-146, -2.8, -2)},
	# The section photographing itself, which is the argument for the pier being
	# walkable at all: forty metres offshore is the only place the whole strip is
	# in one frame.
	{"name": "32_from_the_pier", "yaw": -80.0, "pitch": 3.0, "pos": Vector3(-140, -2.8, -2)},
	{"name": "33_from_the_pier_n", "yaw": -50.0, "pitch": 4.0, "pos": Vector3(-140, -2.8, -2)},
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
	{"name": "34_back_east", "yaw": -90.0, "pitch": 12.0, "pos": Vector3(-104, -2.8, -2)},
	# The cascade from the head of the pier, which is what it is *for*: three
	# arches on one axis at rising heights — the boardwalk's entry, the portal, the
	# plaza's tunnel — with the wings spread between them.
	{"name": "34a_cascade_from_pier", "yaw": -90.0, "pitch": 6.0, "pos": Vector3(-140, -2.8, -2)},
	{"name": "34b_cascade_close", "yaw": -90.0, "pitch": 4.0, "pos": Vector3(-96, -2.8, -2)},
	{"name": "35_bluff", "yaw": -118.0, "pitch": 7.0, "pos": Vector3(-66.5, -2.8, -2)},
]

## The reason the boardwalk is west. Sunset is about 20:20 for this latitude, so
## these bracket it: the low light down the strip, and the sun behind the
## pavilion at the head of the pier.
const SUNSET := [
	{"time": [19, 30], "name": "31_evening_strip", "yaw": 172.0, "pitch": 3.0,
		"pos": Vector3(-98, -2.8, -34)},
	{"time": [20, 20], "name": "32_sunset_pier", "yaw": 90.0, "pitch": 4.0,
		"pos": Vector3(-98, -2.8, -2)},
	{"time": [20, 20], "name": "33_sunset_wheel", "yaw": 118.0, "pitch": 14.0,
		"pos": Vector3(-92, -2.8, -6)},
	{"time": [21, 15], "name": "34_dusk_bulbs", "yaw": 160.0, "pitch": 2.0,
		"pos": Vector3(-100, -2.8, -30)},
	# The claim, and the same frame twice to test it. `design.md` asks the player
	# to read the hour off the park; the plaza does it with a headcount and with
	# whether the cafe is full. The boardwalk's version is that it is nearly
	# empty when the plaza is busy and full when the plaza is going home. If
	# these two pictures are the same picture, the curves are a number in a file.
	{"time": [11, 0], "name": "35_eleven_am", "yaw": 172.0, "pitch": 1.0,
		"pos": Vector3(-98, -2.8, -34)},
	{"time": [19, 0], "name": "36_seven_pm", "yaw": 172.0, "pitch": 1.0,
		"pos": Vector3(-98, -2.8, -34)},
]

## The gate after dark, from the plaza side.
##
## It has to be shot here, in the middle of the run, and that is the whole reason
## this list exists rather than four more entries in `SUNSET`. Everything timed in
## this tool fires *after* the crossing, where the plaza is not mounted — so the
## one entrance in the park these lights belong to was on the far side of a seam
## from every night shot the west had.
##
## `gate_valance_glow` and `gate_throat` arrived with the entrance kit on
## 2026-08-16 and are the first lights the arch has ever had. Two things to read:
## a bulb run that reads as a *run* rather than as one smear, and a cutting that
## reads as open rather than as a black slot — which is why the throat light is
## set seven metres back rather than over the opening.
##
## 21:15 and 21:45, and the window is narrow at both ends. The fittings are not
## fully up until the sun is 6° down, which is about 21:00 for this latitude, and
## `park_lights.gd` follows the park closing — at 22:00 every bulb in the park
## goes out. A night shot at 22:30 is a photograph of an unlit gate.
const PLAZA_NIGHT := [
	# From the ring's west vertex, which is where the four threshold mouths are
	# judged from too. The question is whether the arch now reads as the fifth
	# and biggest way out at the hour the four of them are doing their best work.
	{"time": [21, 15], "name": "01n_gate_from_the_ring", "yaw": 92.0, "pitch": 7.0,
		"pos": Vector3(-16.0, 0.2, 0.0)},
	# Square on, close enough that the bulbs are individual lamps rather than a
	# line. If the run smears here it will smear everywhere.
	{"time": [21, 15], "name": "02n_gate_square", "yaw": 90.0, "pitch": 6.0,
		"pos": Vector3(-22.0, 0.2, -2.0)},
	# At the mouth, looking through. This is the throat light's shot: with the top
	# off, 13.5m of unlit canyon at night is a slot of nothing, and a threshold
	# that reads as closed is the failure the four mouths' throat lamps exist to
	# prevent.
	{"time": [21, 45], "name": "03n_into_the_cutting", "yaw": 90.0, "pitch": 0.0,
		"pos": Vector3(-29.5, 0.2, -2.0)},
	# Inside it, where the only lights are behind and ahead. What this catches is
	# the reveals — 13.5m of blank pier either side, which the day shots already
	# say is the standing cost of taking the top off.
	{"time": [21, 45], "name": "04n_in_the_cutting", "yaw": 90.0, "pitch": 2.0,
		"pos": Vector3(-35.5, 0.2, -2.0)},
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

	# The gate after dark, before the crossing, because the plaza is only mounted
	# on this side of it. See `PLAZA_NIGHT`.
	for shot in PLAZA_NIGHT:
		var nt: Array = shot["time"]
		ParkClock.set_clock(nt[0], nt[1])
		await get_tree().create_timer(2.5).timeout
		await _shoot(shot, shot["name"])
	# Back to the hour the rest of the run is judged in. Everything past the
	# crossing is an evening-light pass and the boardwalk at 21:45 is a different
	# set of pictures than the ones `ARRIVED` was written to ask about.
	ParkClock.set_clock(HOUR, MINUTE)
	await get_tree().create_timer(2.5).timeout

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
