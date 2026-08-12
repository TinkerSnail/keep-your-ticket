extends Node

## Dev tool: loads the main scene, poses the player at a list of vantages, and
## saves viewport captures so the plaza can be inspected without playing it.
##
## Each entry takes a yaw and pitch in degrees, and optionally a position to
## teleport to. Without a position the player stays where it spawned.

const SHOTS := [
	{"name": "spawn", "yaw": 0.0, "pitch": 0.0},
	{"name": "sky_north", "yaw": 0.0, "pitch": 12.0},
	{"name": "sky_ne", "yaw": -48.0, "pitch": 14.0},
	{"name": "sky_west", "yaw": 96.0, "pitch": 10.0},
	{"name": "east", "yaw": -70.0, "pitch": -4.0},
	{"name": "west", "yaw": 80.0, "pitch": -4.0},
	{"name": "back_south", "yaw": 180.0, "pitch": -4.0},
	{"name": "ladder", "yaw": -95.0, "pitch": 6.0, "pos": Vector3(15.0, 0.2, 3.5)},
	{"name": "bench_close", "yaw": 150.0, "pitch": -12.0, "pos": Vector3(4.0, 0.2, 1.0)},
	{"name": "cafe_close", "yaw": -60.0, "pitch": -8.0, "pos": Vector3(10.0, 0.2, 6.0)},
	{"name": "aframe_close", "yaw": 8.0, "pitch": -10.0, "pos": Vector3(2.0, 0.2, 14.0)},
	{"name": "balloons", "yaw": -20.0, "pitch": -6.0, "pos": Vector3(4.5, 0.2, 9.5)},
	{"name": "balloon_ground", "yaw": -144.0, "pitch": -12.0, "pos": Vector3(-1.5, 0.2, 27.5)},
	# The crowd. Aimed at where guests are generated rather than where they end
	# up, so these are worth re-taking after changing `SETTLE_SECONDS`.
	{"name": "crowd_gate", "yaw": 0.0, "pitch": -3.0, "pos": Vector3(-1.5, 0.2, 30.0)},
	{"name": "crowd_fountain", "yaw": 140.0, "pitch": -6.0, "pos": Vector3(6.0, 0.2, 10.0)},
	{"name": "crowd_bench", "yaw": -125.0, "pitch": -8.0, "pos": Vector3(2.0, 0.2, 6.0)},
	{"name": "crowd_band", "yaw": 55.0, "pitch": -5.0, "pos": Vector3(-6.0, 0.2, -4.0)},
	{"name": "crowd_cafe", "yaw": -55.0, "pitch": -6.0, "pos": Vector3(11.0, 0.2, 8.0)},
	{"name": "guest_face", "yaw": 180.0, "pitch": -4.0, "pos": Vector3(0.0, 0.2, 5.0)},
	# The west opening, read as a sequence: the arch from inside the plaza, the
	# passage under it, the view over the parapet, and the wheel that the north
	# pier covers until you step out from behind it.
	{"name": "west_arch", "yaw": 90.0, "pitch": 3.0, "pos": Vector3(0.0, 0.2, -2.0)},
	{"name": "west_under", "yaw": 90.0, "pitch": 1.0, "pos": Vector3(-24.0, 0.2, -2.0)},
	{"name": "west_overlook", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-37.0, 0.2, -2.0)},
	{"name": "west_wheel", "yaw": 68.0, "pitch": 4.0, "pos": Vector3(-37.0, 0.2, -2.0)},
	# The way down, which is the thing the overlook was missing. The head of the
	# flight from the terrace, the turn, and the gate at the foot.
	{"name": "stair_head", "yaw": 62.0, "pitch": -8.0, "pos": Vector3(-34.0, 0.2, -6.0)},
	{"name": "stair_turn", "yaw": 178.0, "pitch": -16.0, "pos": Vector3(-44.7, -0.6, -9.7)},
	{"name": "stair_foot", "yaw": 100.0, "pitch": 2.0, "pos": Vector3(-44.7, -5.6, 5.2)},
	# The arrival, walked in order. The first two decide whether the street
	# works: what the gate frames from outside, and whether the plaza reads as a
	# widening at the end of the run rather than as another room.
	{"name": "arrive_apron", "yaw": 0.0, "pitch": 2.0, "pos": Vector3(-1.5, 0.2, 106.0)},
	{"name": "arrive_gate", "yaw": 0.0, "pitch": 1.0, "pos": Vector3(-1.5, 0.2, 90.0)},
	{"name": "arrive_street", "yaw": 0.0, "pitch": 2.0, "pos": Vector3(-1.5, 0.2, 62.0)},
	{"name": "arrive_mouth", "yaw": 0.0, "pitch": 1.0, "pos": Vector3(-1.5, 0.2, 36.0)},
	# Back the other way: the street as the thing you leave down.
	{"name": "arrive_back", "yaw": 180.0, "pitch": -1.0, "pos": Vector3(-1.5, 0.2, 26.0)},
	# Oblique, because a street is read off its frontage rather than its axis.
	{"name": "arrive_shops", "yaw": 132.0, "pitch": -2.0, "pos": Vector3(-1.5, 0.2, 72.0)},
	# Enclosure. Six openings in a 320m perimeter is roughly a quarter of the
	# plaza's edge missing, and whether it still reads as a room rather than a
	# crossroads is the one thing scaffolding the thresholds was for. A turn on
	# the spot answers it and nothing else does.
	{"name": "room_000", "yaw": 0.0, "pitch": -1.0, "pos": Vector3(3.0, 0.2, 3.0)},
	{"name": "room_060", "yaw": -60.0, "pitch": -1.0, "pos": Vector3(3.0, 0.2, 3.0)},
	{"name": "room_120", "yaw": -120.0, "pitch": -1.0, "pos": Vector3(3.0, 0.2, 3.0)},
	{"name": "room_180", "yaw": 180.0, "pitch": -1.0, "pos": Vector3(3.0, 0.2, 3.0)},
	{"name": "room_240", "yaw": 120.0, "pitch": -1.0, "pos": Vector3(3.0, 0.2, 3.0)},
	{"name": "room_300", "yaw": 60.0, "pitch": -1.0, "pos": Vector3(3.0, 0.2, 3.0)},
	# Each new opening from close enough to see whether the turn hides its end.
	{"name": "way_nnw", "yaw": 0.0, "pitch": -1.0, "pos": Vector3(-13.0, 0.2, -30.0)},
	{"name": "way_ne", "yaw": -90.0, "pitch": -1.0, "pos": Vector3(30.0, 0.2, -21.0)},
	{"name": "way_se", "yaw": -90.0, "pitch": -1.0, "pos": Vector3(30.0, 0.2, 24.0)},
	{"name": "way_sw", "yaw": 180.0, "pitch": -1.0, "pos": Vector3(-24.0, 0.2, 30.0)},
]

## The two vantages the day pass is shot from, both standing at the spawn: one
## up the plaza to the north, one west toward where the boardwalk attaches. West
## is the one that matters — the sun sets into it, so it is where a wrong axis
## would show.
const SPAWN := Vector3(0.0, 0.2, 16.0)

const DAY_VIEWS := [
	{"name": "north", "yaw": 0.0, "pitch": 8.0, "pos": SPAWN},
	{"name": "west", "yaw": 90.0, "pitch": 6.0, "pos": SPAWN},
	# Over the parapet. The sun sets into this one, which is the reason the
	# boardwalk went west and the reason the axis was worth computing.
	{"name": "overlook", "yaw": 84.0, "pitch": 1.0, "pos": Vector3(-37.0, 0.2, -2.0)},
]

## Times of day, chosen for the moments the arc is supposed to hit rather than
## for even spacing: before dawn, sunrise, opening, the flat overhead noon,
## afternoon, the low evening light, sunset, and after dark.
const DAY_TIMES := [6.5, 7.5, 10.0, 13.75, 17.0, 19.0, 20.5, 21.5]

## The crowd across the open day, from two places the plaza floor reads from:
## across the fountain, and down the gap at the south towards the gate. Both are
## about how many people are in shot rather than about the light, so they are
## shot low and wide rather than at the sky.
##
## The gate view is the one that answers whether the day is legible. If eleven
## in the morning and eight at night are the same picture, the schedule is a
## number in a file and not something the player can read off the park.
const CROWD_TIMES := [10.0, 11.5, 13.0, 15.0, 18.0, 20.0, 21.5]

const CROWD_VIEWS := [
	{"name": "floor", "yaw": 155.0, "pitch": -4.0, "pos": Vector3(7.0, 0.2, -4.0)},
	{"name": "gate", "yaw": 178.0, "pitch": -2.0, "pos": Vector3(0.0, 0.2, 8.0)},
	{"name": "cafe", "yaw": -58.0, "pitch": -6.0, "pos": Vector3(9.0, 0.2, 7.0)},
]

## Whichever time the ordinary vantage pass is shot at. Mid-afternoon: the sun
## is off the vertical again and the shadows have direction.
const STANDARD_TIME := 16.0

## Aimed up at the sign tower to read the clock face. The time is set to
## something no symmetry can hide — the hands are not near each other and not
## near a tick.
const CLOCK_SHOT := {"name": "tower_clock", "yaw": -35.0, "pitch": 21.0, "pos": Vector3(6.0, 0.2, 2.0)}
const CLOCK_TIME := 15.0
const CLOCK_MINUTE := 40

## The shots most likely to break under a camera three metres back, taken twice
## — once from the eye, once from the arm. The question the spring arm test is
## actually asking is not whether the camera works but whether the compositions
## survive it, and these are where it would show first: the skyline glimpses the
## rooflines are tuned to crop, the arch framing the pier, and the tight spaces.
const COMPARE := [
	{"name": "sky_north", "yaw": 0.0, "pitch": 12.0, "pos": SPAWN},
	{"name": "sky_ne", "yaw": -48.0, "pitch": 14.0, "pos": SPAWN},
	{"name": "west_arch", "yaw": 90.0, "pitch": 3.0, "pos": Vector3(0.0, 0.2, -2.0)},
	{"name": "room", "yaw": -60.0, "pitch": -1.0, "pos": Vector3(3.0, 0.2, 3.0)},
	{"name": "street", "yaw": 0.0, "pitch": 1.0, "pos": Vector3(-1.5, 0.2, 78.0)},
	{"name": "way_nnw", "yaw": 0.0, "pitch": -1.0, "pos": Vector3(-13.0, 0.2, -34.0)},
	{"name": "arcade", "yaw": 90.0, "pitch": -1.0, "pos": Vector3(-13.0, 0.2, 66.0)},
]


## Long enough for guests to have picked a route, taken a few steps, and settled
## their heads onto something. At one second the whole crowd is still standing
## where it was generated, facing whichever way it was pointed.
const SETTLE_SECONDS := 6.0

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run(main)


func _run(main: Node) -> void:
	# Hold the clock still. Everything below sets it explicitly, and a shot that
	# drifted between the frame it was set up on and the frame it was read on
	# would be the sort of difference that reads as a bug in the sun.
	ParkClock.running = false
	ParkClock.set_clock(int(STANDARD_TIME), 0)

	await get_tree().create_timer(SETTLE_SECONDS).timeout

	_player = main.get_node_or_null("player")
	if _player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")

	for shot in SHOTS:
		await _shoot(shot, "shot_%s" % shot["name"])

	for hour in DAY_TIMES:
		ParkClock.set_clock(int(hour), int(round(fmod(hour, 1.0) * 60.0)))
		for view in DAY_VIEWS:
			var label := "day_%02d%02d_%s" % [ParkClock.hour(), ParkClock.minute(), view["name"]]
			await _shoot(view, label)

	# Jumping the clock re-places the crowd rather than walking it in, so each
	# of these is the plaza as that hour actually holds it. A settle beat after
	# the jump, because the guests are put down facing where they were left and
	# want a moment to pick a route and turn their heads.
	for hour in CROWD_TIMES:
		ParkClock.set_clock(int(hour), int(round(fmod(hour, 1.0) * 60.0)))
		await get_tree().create_timer(2.5).timeout
		for view in CROWD_VIEWS:
			var label := "crowd_%02d%02d_%s" % [ParkClock.hour(), ParkClock.minute(), view["name"]]
			await _shoot(view, label)

	ParkClock.set_clock(int(CLOCK_TIME), CLOCK_MINUTE)
	await _shoot(CLOCK_SHOT, "shot_%s" % CLOCK_SHOT["name"])

	ParkClock.set_clock(int(STANDARD_TIME), 0)
	for view in COMPARE:
		await _shoot(view, "cmp_1p_%s" % view["name"])
	if _player.has_method("set_third_person"):
		_player.set_third_person(true)
		await get_tree().physics_frame
		for view in COMPARE:
			await _shoot(view, "cmp_3p_%s" % view["name"])
		_player.set_third_person(false)

	get_tree().quit()


func _shoot(shot: Dictionary, label: String) -> void:
	if shot.has("pos"):
		_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	# let the body settle onto the floor before reading the frame
	for _i in 3:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "user://%s.png" % label
	img.save_png(path)
	print("saved ", path)
