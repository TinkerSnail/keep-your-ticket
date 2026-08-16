extends Node

## Dev tool: shoots the park through the evening, and measures what the lights
## cost while it is doing it.
##
## Two jobs in one run because they need the same thing — a real renderer. The
## headless dummy renderer draws nothing, so it can neither photograph the park
## nor tell you what a hundred lights cost to draw. `night_test.gd` covers
## everything that *can* be checked headlessly (which lights are on, at which
## hour, of which kind); this covers the two things that cannot.
##
##   open -n -a /Applications/Godot.app --args --path <abs path> _night_capture.tscn
##
## No `--quit-after`: it counts frames and would cut the settle short. The path
## has to be absolute — `open` goes through LaunchServices and the child does not
## inherit the shell's directory, so a relative one lands in the project manager
## and idles at 2% forever.

## The hours, and what each is being asked.
##
## 15:00 is the control and the reason the perf numbers mean anything: it is the
## same park, same crowd, same views, with every light switched off. The night
## cost is the difference between the two rows, not the absolute number.
const TIMES := [
	[15.0, "day"],
	[20.6, "sunset"],
	[21.4, "night"],
	[22.6, "closed"],
]

## Vantages, chosen to put each part of the lighting pass in at least one frame.
const VIEWS := [
	# The tower, from the street it is aimed down. The uplighting's headline, and
	# the one shot that says whether floodlit architecture reads at all.
	{"name": "tower_street", "yaw": 0.0, "pitch": 12.0, "pos": Vector3(-1.5, 0.2, 12.0)},
	# The fountain from the ring, which is where the crowd is and where the lamp
	# pools overlap.
	{"name": "fountain", "yaw": 200.0, "pitch": -4.0, "pos": Vector3(6.0, 0.2, 14.0)},
	# The perimeter wash. The enclosure argument the 104m plaza was rebuilt
	# around is entirely about these walls, and this asks whether it survives
	# sunset.
	{"name": "perimeter_ne", "yaw": -45.0, "pitch": 6.0, "pos": Vector3(0.0, 0.2, 0.0)},
	{"name": "perimeter_sw", "yaw": 135.0, "pitch": 6.0, "pos": Vector3(0.0, 0.2, 0.0)},
	# The bandstand, lit from under its own roof rather than washed.
	{"name": "bandstand", "yaw": 42.0, "pitch": -2.0, "pos": Vector3(-8.0, 0.2, -8.0)},
	# A threshold mouth: does an unlit passage read as closed after dark?
	{"name": "threshold_ne", "yaw": -62.0, "pitch": 2.0, "pos": Vector3(30.0, 0.2, -16.0)},
	# The arrival, south. Nothing in the first two capture runs pointed this way,
	# which is exactly how `entrance.tscn` kept zero lights through a whole
	# lighting pass and a screenshot review. A vantage that does not exist cannot
	# report a scene that is dark.
	{"name": "street_down", "yaw": 180.0, "pitch": 1.0, "pos": Vector3(-1.5, 0.2, 58.0)},
	{"name": "street_up", "yaw": 0.0, "pitch": 3.0, "pos": Vector3(-1.5, 0.2, 100.0)},
	{"name": "street_arcade", "yaw": 118.0, "pitch": 0.0, "pos": Vector3(2.0, 0.2, 78.0)},
	{"name": "gate_outside", "yaw": 0.0, "pitch": 3.0, "pos": Vector3(-1.5, 0.2, 122.0)},
	{"name": "plaza_mouth", "yaw": 178.0, "pitch": 2.0, "pos": Vector3(-2.0, 0.2, 46.0)},
	# The cafe terrace, which is one of the plaza's two ways of telling the time.
	{"name": "cafe_terrace", "yaw": 250.0, "pitch": -4.0, "pos": Vector3(-14.0, 0.2, 10.0)},
	# The overlook, west. The tableau's night presentation, and the shot that
	# caught it being absent.
	{"name": "overlook_west", "yaw": 90.0, "pitch": 0.0, "pos": Vector3(-49.0, 0.2, -2.0)},
	{"name": "overlook_wheel", "yaw": 68.0, "pitch": 4.0, "pos": Vector3(-49.0, 0.2, -2.0)},
	# Through the arch from inside the plaza — the framed view, which is what the
	# tunnel exists to make.
	{"name": "arch_framed", "yaw": 90.0, "pitch": 2.0, "pos": Vector3(-20.0, 0.2, -2.0)},
	# The cascade. The first pass put the camera at x=-52 on the terrace, which
	# is *behind* the parapet — it photographed the gate house and a wheel and
	# no cascade at all, and the shot was useless without being obviously wrong,
	# which is the worst kind. The monument starts at the bluff face (x=-58) and
	# descends west to about x=-84, so it has to be seen either from the parapet
	# gap itself looking down, or from the court at the bottom looking back up.
	# Both, because they are the two ends of the descent and the whole point of
	# the thing is that they read as the same place.
	{"name": "cascade_above", "yaw": 90.0, "pitch": -22.0, "pos": Vector3(-57.0, 0.2, -2.0)},
	# Off the axis by 7m, because the player stands on it. Third person puts the
	# body between the camera and whatever the camera is aimed at, and on a
	# monument built symmetrically about a centre line that means the body lands
	# exactly on the portal — the one element the whole rework is about. The
	# first pass photographed the back of a photographer.
	{"name": "cascade_below", "yaw": -74.0, "pitch": 14.0, "pos": Vector3(-92.0, -2.8, 5.0)},
]

## Where the frame cost is measured from. One fixed vantage at every hour, aimed
## across the widest spread of lit geometry in the plaza — the fountain, the
## crowd, the tower and two ranges of washed perimeter in one frustum. A view
## with nothing in it measures nothing.
const PERF_VIEW := {"name": "perf", "yaw": -20.0, "pitch": 2.0, "pos": Vector3(10.0, 0.2, 20.0)}

## Frames averaged per reading, after a warm-up that is thrown away. The first
## frames after a clock jump include shadow maps being repopulated and light
## clusters being rebuilt, which is a real cost but not a per-frame one.
const PERF_WARMUP := 45
const PERF_FRAMES := 120

const SETTLE_SECONDS := 6.0

var _player: Node3D
var _head: Node3D
var _rows: Array = []


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run(main)


func _run(main: Node) -> void:
	# Vsync off, or the perf half of this run measures the display instead of the
	# park. The first pass reported 8.33ms at every hour — day, sunset, night and
	# closed all identical to two decimal places, which is 120Hz exactly and not
	# a fact about lighting. A capped frame time cannot show a cost that fits
	# inside the cap, which is the cost worth knowing about.
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0

	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	await get_tree().create_timer(SETTLE_SECONDS).timeout

	_player = main.get_node_or_null("player")
	if _player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")

	for entry in TIMES:
		var hour: float = entry[0]
		var tag: String = entry[1]
		ParkClock.set_clock(int(hour), int(round(fmod(hour, 1.0) * 60.0)))
		# The crowd is re-placed by a clock jump rather than walked in, so give
		# it a beat to pick routes before anything is photographed.
		await get_tree().create_timer(2.5).timeout
		for view in VIEWS:
			await _shoot(view, "night_%s_%s" % [tag, view["name"]])
		await _measure(tag)

	_report()
	get_tree().quit()


func _shoot(shot: Dictionary, label: String) -> void:
	if shot.has("pos"):
		_player.global_position = shot["pos"]
	_player.rotation.y = deg_to_rad(shot["yaw"])
	_head.rotation.x = deg_to_rad(shot["pitch"])
	for _i in 3:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := "user://%s.png" % label
	img.save_png(path)
	print("saved ", path)


## Wall-clock per frame at this hour, plus what the renderer says it is drawing.
##
## Measured as elapsed time over a fixed frame count rather than by reading a
## per-frame monitor, because the monitors are themselves sampled and a light
## that costs 0.2ms is inside their noise. Over 120 frames it is not.
func _measure(tag: String) -> void:
	_player.global_position = PERF_VIEW["pos"]
	_player.rotation.y = deg_to_rad(PERF_VIEW["yaw"])
	_head.rotation.x = deg_to_rad(PERF_VIEW["pitch"])

	for _i in PERF_WARMUP:
		await RenderingServer.frame_post_draw

	var began := Time.get_ticks_usec()
	for _i in PERF_FRAMES:
		await RenderingServer.frame_post_draw
	var elapsed := Time.get_ticks_usec() - began

	var lights := 0
	for n in get_tree().get_nodes_in_group(&"park_light"):
		var l := n as Light3D
		if l != null and l.visible:
			lights += 1

	_rows.append({
		"tag": tag,
		"ms": float(elapsed) / float(PERF_FRAMES) / 1000.0,
		"lights": lights,
		"draw": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"prims": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
	})


func _report() -> void:
	print("\n  when      lights   ms/frame     fps   draw calls   primitives")
	print("  " + "-".repeat(66))
	var day := 0.0
	for r in _rows:
		if r["tag"] == "day":
			day = r["ms"]
		print("  %-8s  %6d   %8.2f  %6.1f   %10d   %10d" % [
			r["tag"], r["lights"], r["ms"], 1000.0 / maxf(r["ms"], 0.001),
			int(r["draw"]), int(r["prims"])])

	print("")
	for r in _rows:
		if r["tag"] == "day":
			continue
		var cost: float = r["ms"] - day
		print("  %-8s costs %+.2f ms/frame over the same park unlit (%d lights, %.3f ms each)"
			% [r["tag"], cost, r["lights"], cost / maxf(float(r["lights"]), 1.0)])
