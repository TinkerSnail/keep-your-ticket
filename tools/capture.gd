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

## Whichever time the ordinary vantage pass is shot at. Mid-afternoon: the sun
## is off the vertical again and the shadows have direction.
const STANDARD_TIME := 16.0

## Aimed up at the sign tower to read the clock face. The time is set to
## something no symmetry can hide — the hands are not near each other and not
## near a tick.
const CLOCK_SHOT := {"name": "tower_clock", "yaw": -35.0, "pitch": 21.0, "pos": Vector3(6.0, 0.2, 2.0)}
const CLOCK_TIME := 15.0
const CLOCK_MINUTE := 40

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

	ParkClock.set_clock(int(CLOCK_TIME), CLOCK_MINUTE)
	await _shoot(CLOCK_SHOT, "shot_%s" % CLOCK_SHOT["name"])

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
