extends Node

## Dev probe: does the frame get worse when the real player looks and walks?
##
## Written on 2026-09-18 after Christina reported the game "starts out fine" and
## grinds to a halt once she moves the camera and walks. The other perf probes
## park a free camera, which cannot show that. This one mounts `main.tscn` as
## the game does, leaves the clock, crowd and wildlife running, and drives the
## real player through its own input actions: still, look only, walk only, walk
## and look, still again. One line a second: wall frame time, worst frame,
## physics ticks per drawn frame, the engine's process and physics times, the
## viewport's render CPU and GPU times, draw calls, and where the player is.
##
## Launch windowed with `--disable-vsync`, frontmost, no other Godot rendering.
## Writes `user://player_motion_perf.txt`.

const PHASES := [
	{"name": "still", "seconds": 8, "look": 0.0, "walk": false},
	{"name": "look", "seconds": 10, "look": 0.6, "walk": false},
	{"name": "walk", "seconds": 12, "look": 0.0, "walk": true},
	{"name": "walk+look", "seconds": 14, "look": 0.4, "walk": true},
	{"name": "still again", "seconds": 8, "look": 0.0, "walk": false},
]

var _main: Node
var _player: Node3D
var _lines: PackedStringArray = []
var _ticks := 0


func _ready() -> void:
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
	DisplayServer.window_move_to_foreground()
	_line("player_motion_perf_probe  driver=%s  %s" % [
		DisplayServer.get_name(), Time.get_datetime_string_from_system()])
	_main = (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(_main)
	_player = _main.get_node("player") as Node3D
	var vp := get_viewport().get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp, true)
	for i in 60:
		await get_tree().process_frame
	for phase in PHASES:
		await _run(phase, vp)
	for action in ["look_right", "move_forward"]:
		Input.action_release(action)
	var f := FileAccess.open("user://player_motion_perf.txt", FileAccess.WRITE)
	f.store_string("\n".join(_lines) + "\n")
	f.close()
	get_tree().quit()


func _physics_process(_delta: float) -> void:
	_ticks += 1


func _run(phase: Dictionary, vp: RID) -> void:
	if phase.look > 0.0:
		Input.action_press("look_right", phase.look)
	else:
		Input.action_release("look_right")
	if phase.walk:
		Input.action_press("move_forward", 1.0)
	else:
		Input.action_release("move_forward")
	for second in int(phase.seconds):
		var frames := 0
		var worst := 0.0
		var process := 0.0
		var physics := 0.0
		var cpu := 0.0
		var gpu := 0.0
		var draws := 0.0
		_ticks = 0
		var start := Time.get_ticks_usec()
		var last := start
		while Time.get_ticks_usec() - start < 1_000_000:
			await get_tree().process_frame
			var now := Time.get_ticks_usec()
			worst = maxf(worst, (now - last) / 1000.0)
			last = now
			frames += 1
			process += Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
			physics += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
			cpu += RenderingServer.viewport_get_measured_render_time_cpu(vp) \
				+ RenderingServer.get_frame_setup_time_cpu()
			gpu += RenderingServer.viewport_get_measured_render_time_gpu(vp)
			draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		var wall := (Time.get_ticks_usec() - start) / 1000.0
		var at := _player.global_position
		_line("%-11s %2d  frame %6.1f ms  worst %7.1f  ticks/frame %4.1f  process %5.1f  physics/tick %5.1f  render cpu %5.1f  gpu %5.1f  draws %6d  at (%6.1f %5.1f %6.1f)" % [
			phase.name, second, wall / frames, worst, float(_ticks) / frames,
			process / frames, physics / frames, cpu / frames, gpu / frames,
			int(draws / frames), at.x, at.y, at.z])


func _line(text: String) -> void:
	print(text)
	_lines.append(text)
