extends Node

## Dev probe: what the player's far plane costs to draw.
##
## Written on 2026-09-18, when both player cameras went from 400m to 4200m
## together with the camera-distance haze. Mounts `main.tscn`, stands a camera
## with the player's lens (fov 70, near 0.05) at eye height over a handful of
## places the player really reaches, turns it through eight headings at each,
## and reads the same frames at each far value in `FARS`. The comparison is the
## result; nothing here is a budget on its own.
##
## Per standpoint and far value: mean and worst wall-clock frame, the viewport's
## measured CPU and GPU render time, and the renderer's object, primitive and
## draw-call monitors, averaged over the eight headings. Launch windowed with
## `--disable-vsync`, or the wall clock is capped; the GPU figure is not.
## Headless prints zeros. Writes `user://far_plane_perf.txt` and prints it.

const Plan := preload("res://scripts/park_plan.gd")

const FARS := [400.0, 4200.0]
const HEADINGS := 8
const WARM := 30
const SETTLE := 20
const MEASURE := 60
const EYE := 1.7

## Plan positions; the height is found by a ray so a moved floor cannot put the
## eye underground.
const STANDPOINTS := [
	{"name": "plaza_fountain", "xz": Vector2(0.0, 14.0)},
	{"name": "promenade_north", "xz": Vector2(-98.0, -70.0)},
	{"name": "entrance_walk_foot", "xz": Vector2(0.0, 236.0)},
	{"name": "pier_head", "xz": Vector2.ZERO, "plan": "pier"},
	{"name": "east_belvedere", "xz": Vector2.ZERO, "plan": "belvedere"},
]

var _camera: Camera3D
var _lines: PackedStringArray = []


func _ready() -> void:
	_line("far_plane_perf_probe  driver=%s  vsync=%d  %s" % [
		DisplayServer.get_name(), DisplayServer.window_get_vsync_mode(),
		Time.get_datetime_string_from_system()])
	# macOS stops a covered window drawing at all, and a probe launched from
	# another app's session starts covered; hold it on top for the run.
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
	DisplayServer.window_move_to_foreground()
	var main := (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	var weather := main.get_node_or_null("weather") as Node3D
	if weather != null:
		weather.visible = false
		weather.process_mode = Node.PROCESS_MODE_DISABLED
	for layer_name in ["hud", "park_menu"]:
		var layer := main.get_node_or_null(layer_name) as CanvasLayer
		if layer != null:
			layer.visible = false
	_camera = Camera3D.new()
	_camera.fov = 70.0
	_camera.near = 0.05
	add_child(_camera)
	_camera.make_current()
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	for i in 120:
		await get_tree().process_frame
	await _run()
	var f := FileAccess.open("user://far_plane_perf.txt", FileAccess.WRITE)
	if f != null:
		f.store_string("\n".join(_lines) + "\n")
	get_tree().quit()


func _run() -> void:
	# The first look in any direction compiles pipelines and stalls for seconds.
	# That is a loading cost, not the far plane's, so every view is visited once
	# at the longest far value before anything is timed.
	var eyes: Array[Vector3] = []
	for sp in STANDPOINTS:
		eyes.append(_eye(sp))
	_camera.far = FARS.max()
	for eye in eyes:
		for h in HEADINGS:
			_face(eye, h)
			for i in WARM:
				await get_tree().process_frame
	_line("warm-up done")
	var totals := {}
	for k in STANDPOINTS.size():
		var sp: Dictionary = STANDPOINTS[k]
		var eye := eyes[k]
		for far in FARS:
			_camera.far = far
			var r := await _spin(eye)
			_line("%-20s far %6.0f  frame %6.2f ms  worst %6.2f  cpu %5.2f  gpu %5.2f  objects %6d  primitives %9d  draws %5d%s" % [
				sp.name, far, r.frame, r.worst, r.cpu, r.gpu, r.objects, r.primitives, r.draws,
				"" if r.undrawn <= 0 else "  UNDRAWN %d, ignore" % r.undrawn])
			var t: Dictionary = totals.get(far, {"frame": 0.0, "gpu": 0.0, "worst": 0.0})
			t.frame += r.frame
			t.gpu += r.gpu
			t.worst = maxf(t.worst, r.worst)
			totals[far] = t
	for far in FARS:
		var t: Dictionary = totals[far]
		_line("ALL                  far %6.0f  frame %6.2f ms  worst %6.2f  gpu %5.2f" % [
			far, t.frame / STANDPOINTS.size(), t.worst, t.gpu / STANDPOINTS.size()])


func _eye(sp: Dictionary) -> Vector3:
	var xz: Vector2 = sp.xz
	if sp.has("plan"):
		xz = _named(sp.plan)
	var space := get_viewport().world_3d.direct_space_state
	var q := PhysicsRayQueryParameters3D.create(
		Vector3(xz.x, 120.0, xz.y), Vector3(xz.x, -60.0, xz.y), 1)
	var hit := space.intersect_ray(q)
	var ground: float = hit.position.y if not hit.is_empty() else 0.0
	_line("standpoint %-20s x %7.1f  z %7.1f  ground %6.2f%s" % [
		sp.name, xz.x, xz.y, ground, "" if not hit.is_empty() else "  (no ground hit)"])
	return Vector3(xz.x, ground + EYE, xz.y)


## The two standpoints whose place is a `ParkPlan` fact rather than a number
## here, so they follow the plan if it moves.
func _named(which: String) -> Vector2:
	if which == "pier":
		return Vector2(Plan.PIER_ROOT.x - Plan.PIER_LENGTH + 2.0, Plan.PIER_Z)
	return Vector2(Plan.EAST_BELVEDERE_VIEWER_X, 0.0)


func _spin(eye: Vector3) -> Dictionary:
	var vp := get_viewport().get_viewport_rid()
	var frame := 0.0
	var worst := 0.0
	var cpu := 0.0
	var gpu := 0.0
	var objects := 0.0
	var primitives := 0.0
	var draws := 0.0
	var n := 0
	var undrawn := 0
	for h in HEADINGS:
		_face(eye, h)
		for i in SETTLE:
			await get_tree().process_frame
		var last := Time.get_ticks_usec()
		var drawn_before := Engine.get_frames_drawn()
		for i in MEASURE:
			await get_tree().process_frame
			var now := Time.get_ticks_usec()
			var ms := (now - last) / 1000.0
			last = now
			frame += ms
			worst = maxf(worst, ms)
			cpu += RenderingServer.viewport_get_measured_render_time_cpu(vp)
			gpu += RenderingServer.viewport_get_measured_render_time_gpu(vp)
			objects += Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
			primitives += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
			draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
			n += 1
		# An occluded or minimised window idles without drawing and reports a
		# fast, meaningless frame; say so rather than average it in.
		undrawn += MEASURE - (Engine.get_frames_drawn() - drawn_before)
	return {"undrawn": undrawn, "frame": frame / n, "worst": worst, "cpu": cpu / n, "gpu": gpu / n,
		"objects": int(objects / n), "primitives": int(primitives / n), "draws": int(draws / n)}


func _face(eye: Vector3, heading: int) -> void:
	var yaw := TAU * float(heading) / float(HEADINGS)
	_camera.global_position = eye
	_camera.look_at(eye + Vector3(sin(yaw), 0.0, -cos(yaw)), Vector3.UP)


func _line(text: String) -> void:
	_lines.append(text)
	print(text)
