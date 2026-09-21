extends Node

## Dev probe: where a frame's time goes, by switching one thing off at a time.
##
## Written on 2026-09-18 after `far_plane_perf_probe` showed 60-79ms a frame
## from inside the park whatever the far plane was. Mounts `main.tscn`, stands a
## player-lens camera at three reachable standpoints, four headings each, and
## draws the same views under each entry of `_configs()`: sun shadows off,
## shorter shadow distance, fewer splits, small CSG shapes not casting, small CSG
## hidden, all CSG hidden, positional lights hidden, crowd off, MSAA off, SSAO
## and glow off, haze off, range and city hidden. Every change is made on the
## running instance and put back; nothing is saved. The baseline is drawn first
## and again last, so drift shows.
##
## Launch windowed with `--disable-vsync` and keep the window in front: macOS
## stops a covered window drawing. Writes `user://frame_cost.txt`.

const Plan := preload("res://scripts/park_plan.gd")

const HEADINGS := 4
const WARM := 25
const SETTLE := 8
const MEASURE := 30
const EYE := 1.7
const FAR := 4200.0
## Longest side under this is a "small" shape: rungs, pickets, bulbs, brackets.
const SMALL := 0.5

var _main: Node
var _camera: Camera3D
var _sun: DirectionalLight3D
var _eyes: Array[Vector3] = []
var _csg: Array[CSGShape3D] = []
var _small: Array[CSGShape3D] = []
var _lights: Array[Light3D] = []
var _crowds: Array[Node] = []
var _lines: PackedStringArray = []
var _base := 0.0


func _ready() -> void:
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
	DisplayServer.window_move_to_foreground()
	_line("frame_cost_probe  driver=%s  %s" % [
		DisplayServer.get_name(), Time.get_datetime_string_from_system()])
	_main = (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	var weather := _main.get_node_or_null("weather") as Node3D
	if weather != null:
		weather.visible = false
		weather.process_mode = Node.PROCESS_MODE_DISABLED
	for layer_name in ["hud", "park_menu"]:
		var layer := _main.get_node_or_null(layer_name) as CanvasLayer
		if layer != null:
			layer.visible = false
	_camera = Camera3D.new()
	_camera.fov = 70.0
	_camera.near = 0.05
	_camera.far = FAR
	add_child(_camera)
	_camera.make_current()
	for i in 120:
		await get_tree().process_frame
	_collect()
	for xz in [Vector2(0.0, 236.0), Vector2(-98.0, -70.0),
			Vector2(Plan.EAST_BELVEDERE_VIEWER_X, 0.0)]:
		_eyes.append(_eye(xz))
	for eye in _eyes:
		for h in HEADINGS:
			_face(eye, h)
			for i in WARM:
				await get_tree().process_frame
	_line("warm-up done")
	# FRAME_COST_ONLY="baseline,sun shadows off" runs a short list; a long run
	# is a long time to keep a shared GPU to yourself.
	var only := OS.get_environment("FRAME_COST_ONLY")
	for config in _configs():
		if only != "" and not (config.name in only.split(",")):
			continue
		config.on.call()
		var r := await _measure()
		config.off.call()
		if _base == 0.0:
			_base = r.frame
		_line("%-34s frame %6.2f ms  %+6.1f%%  worst %7.2f  objects %6d  primitives %8d  draws %6d%s" % [
			config.name, r.frame, (r.frame / _base - 1.0) * 100.0, r.worst,
			r.objects, r.primitives, r.draws,
			"" if r.undrawn <= 0 else "  UNDRAWN %d, ignore" % r.undrawn])
	var f := FileAccess.open("user://frame_cost.txt", FileAccess.WRITE)
	if f != null:
		f.store_string("\n".join(_lines) + "\n")
	get_tree().quit()


func _collect() -> void:
	var stack: Array[Node] = [_main]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is DirectionalLight3D and _sun == null:
			_sun = n
		elif n is OmniLight3D or n is SpotLight3D:
			_lights.append(n)
		elif n is CSGShape3D and not (n.get_parent() is CSGShape3D):
			_csg.append(n)
			var size := (n as CSGShape3D).get_aabb().size * (n as Node3D).global_basis.get_scale()
			if maxf(size.x, maxf(size.y, size.z)) < SMALL:
				_small.append(n)
		var script := n.get_script() as Script
		if script != null and script.resource_path.ends_with("/crowd.gd"):
			_crowds.append(n)
		for c in n.get_children():
			stack.append(c)
	var shadowed := 0
	for l in _lights:
		if l.shadow_enabled:
			shadowed += 1
	var casting := 0
	for c in _csg:
		if c.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			casting += 1
	_line("world  csg %d (small %d, casting %d)  lights %d (shadowed %d)  crowds %d" % [
		_csg.size(), _small.size(), casting, _lights.size(), shadowed, _crowds.size()])
	_line("sun    shadow %s  mode %d  max_distance %.0f" % [
		_sun.shadow_enabled, _sun.directional_shadow_mode, _sun.directional_shadow_max_distance])
	var vp := get_viewport()
	_line("view   msaa_3d %d  scaling_3d %.2f  size %s" % [vp.msaa_3d, vp.scaling_3d_scale, vp.size])


func _configs() -> Array:
	var env := (_main.get_node("world_environment") as WorldEnvironment).environment
	var vp := get_viewport()
	var nothing := func() -> void: pass
	var sun_distance := _sun.directional_shadow_max_distance
	var sun_mode := _sun.directional_shadow_mode
	var msaa := vp.msaa_3d
	var scenery: Array[Node3D] = []
	for scenery_name in ["range_forest_background", "far_shore_city_relocation", "park_towns"]:
		var node := _main.find_child(scenery_name, true, false) as Node3D
		if node != null:
			scenery.append(node)
	return [
		{"name": "baseline", "on": nothing, "off": nothing},
		{"name": "sun shadows off",
			"on": func() -> void: _sun.shadow_enabled = false,
			"off": func() -> void: _sun.shadow_enabled = true},
		{"name": "sun shadow distance 60m",
			"on": func() -> void: _sun.directional_shadow_max_distance = 60.0,
			"off": func() -> void: _sun.directional_shadow_max_distance = sun_distance},
		{"name": "sun shadow 2 splits",
			"on": func() -> void: _sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS,
			"off": func() -> void: _sun.directional_shadow_mode = sun_mode},
		{"name": "small csg cast no shadow",
			"on": func() -> void: _cast(_small, false),
			"off": func() -> void: _cast(_small, true)},
		{"name": "small csg hidden",
			"on": func() -> void: _show(_small, false),
			"off": func() -> void: _show(_small, true)},
		{"name": "all csg hidden",
			"on": func() -> void: _show(_csg, false),
			"off": func() -> void: _show(_csg, true)},
		{"name": "positional lights hidden",
			"on": func() -> void: _show(_lights, false),
			"off": func() -> void: _show(_lights, true)},
		{"name": "crowd off",
			"on": func() -> void: _crowd(false),
			"off": func() -> void: _crowd(true)},
		{"name": "msaa off",
			"on": func() -> void: vp.msaa_3d = Viewport.MSAA_DISABLED,
			"off": func() -> void: vp.msaa_3d = msaa},
		{"name": "ssao and glow off",
			"on": func() -> void:
				env.ssao_enabled = false
				env.glow_enabled = false,
			"off": func() -> void:
				env.ssao_enabled = true
				env.glow_enabled = true},
		{"name": "haze off",
			"on": func() -> void: env.fog_enabled = false,
			"off": func() -> void: env.fog_enabled = true},
		{"name": "range, city, towns hidden",
			"on": func() -> void: _show(scenery, false),
			"off": func() -> void: _show(scenery, true)},
		{"name": "baseline again", "on": nothing, "off": nothing},
	]


## Visibility and shadow casting are put back to what each node had, not to a
## guess, because some shapes are hidden or non-casting by design.
var _was := {}


func _show(nodes: Array, on: bool) -> void:
	for n in nodes:
		if not on:
			_was[n] = n.visible
			n.visible = false
		else:
			n.visible = _was.get(n, true)


func _cast(nodes: Array, on: bool) -> void:
	for n in nodes:
		if not on:
			_was[n] = n.cast_shadow
			n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		else:
			n.cast_shadow = _was.get(n, GeometryInstance3D.SHADOW_CASTING_SETTING_ON)


func _crowd(on: bool) -> void:
	for c in _crowds:
		if c is Node3D:
			(c as Node3D).visible = on
		c.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED


func _eye(xz: Vector2) -> Vector3:
	var space := get_viewport().world_3d.direct_space_state
	var q := PhysicsRayQueryParameters3D.create(
		Vector3(xz.x, 120.0, xz.y), Vector3(xz.x, -60.0, xz.y), 1)
	var hit := space.intersect_ray(q)
	var ground: float = hit.position.y if not hit.is_empty() else 0.0
	return Vector3(xz.x, ground + EYE, xz.y)


func _face(eye: Vector3, heading: int) -> void:
	var yaw := TAU * float(heading) / float(HEADINGS)
	_camera.global_position = eye
	_camera.look_at(eye + Vector3(sin(yaw), 0.0, -cos(yaw)), Vector3.UP)


func _measure() -> Dictionary:
	var frame := 0.0
	var worst := 0.0
	var objects := 0.0
	var primitives := 0.0
	var draws := 0.0
	var n := 0
	var undrawn := 0
	for eye in _eyes:
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
				objects += Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
				primitives += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
				draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
				n += 1
			undrawn += MEASURE - (Engine.get_frames_drawn() - drawn_before)
	return {"frame": frame / n, "worst": worst, "undrawn": undrawn,
		"objects": int(objects / n), "primitives": int(primitives / n), "draws": int(draws / n)}


func _line(text: String) -> void:
	_lines.append(text)
	print(text)
