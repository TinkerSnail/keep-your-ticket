extends Node

## Dev probe: what the palm crowns cost to draw, and what their cut-out leaflets
## add, from the player's standpoints down the arrival allée and on the
## Boardwalk.
##
## Written on 2026-09-26, when the crown's leaflets moved into its texture's
## alpha (`paint_canvas.py --leaflets`): alpha-scissored fronds cost more to
## fill than opaque ones, and nobody had measured by how much. Three states at
## each standpoint:
##
##   hidden   every palm crown hidden (trunks, beds and the rest still drawn);
##   cut-out  the crowns as the game ships them;
##   opaque   the same merged crown meshes with an opaque copy of their
##            material: the same triangles without the alpha test, so cut-out
##            minus opaque is what the leaflets themselves cost.
##
## Mean and worst frame time over MEASURE frames, and the renderer's object,
## primitive and draw-call monitors. Meaningful only under a real driver and
## with `--disable-vsync`; headless prints zeros. The crowd keeps walking, so
## repeat a run before trusting a difference under a few tenths of a
## millisecond. Writes `user://palm_perf_<driver>.txt` and prints the same lines.

const SETTLE := 60
const MEASURE := 240
const EYE := 1.65
const STATES := ["hidden", "cut-out", "opaque"]
## The player's feet, heading and head pitch, from coastal_palm_capture.gd.
const STANDPOINTS := [
	{"name": "allee_northbound", "feet": Vector3(0.0, 0.2, 220.0), "yaw": 0.0, "pitch": 10.0},
	{"name": "allee_southbound", "feet": Vector3(0.0, 0.2, 145.0), "yaw": 180.0, "pitch": 9.0},
	{"name": "under_a_crown", "feet": Vector3(0.0, 0.2, 199.0), "yaw": 90.0, "pitch": 25.0},
	{"name": "boardwalk_row", "feet": Vector3(-97.0, ParkPlan.SHORE_TOP + 0.2, -48.0), "yaw": 43.0, "pitch": 15.0},
]

var _camera: Camera3D
var _crowns: Array[Node3D] = []
var _merged: Array[MeshInstance3D] = []
var _lines: PackedStringArray = []
var _state := 0
var _standpoint := 0
var _frame := 0
var _acc := 0.0
var _worst := 0.0
var _last_us := 0
var _running := false


func _ready() -> void:
	_line("palm_perf_probe  driver=%s  %s" % [DisplayServer.get_name(), Time.get_datetime_string_from_system()])
	add_child(load("res://scenes/main/main.tscn").instantiate())
	ParkClock.running = false
	ParkClock.set_clock(17, 30)
	# Palms merge their crowns two frames after they build; give them time.
	await get_tree().create_timer(5.0).timeout
	_find(get_tree().root)
	_line("crowns %d  merged crown meshes %d" % [_crowns.size(), _merged.size()])
	_camera = Camera3D.new()
	_camera.fov = 70.0
	_camera.far = 4200.0
	add_child(_camera)
	_camera.make_current()
	_pose()
	_running = true


func _find(node: Node) -> void:
	if node.scene_file_path == "res://scenes/world/palm_crown.tscn":
		_crowns.append(node as Node3D)
		for child in node.get_children():
			if child is MeshInstance3D and String(child.name).begins_with("merged_static"):
				_merged.append(child)
		return
	for child in node.get_children():
		_find(child)


func _apply_state() -> void:
	for crown in _crowns:
		crown.visible = STATES[_state] != "hidden"
	for mesh in _merged:
		if STATES[_state] != "opaque":
			mesh.material_override = null
			continue
		var source := mesh.get_active_material(0) as BaseMaterial3D
		if source == null:
			continue
		var solid := source.duplicate() as BaseMaterial3D
		solid.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
		mesh.material_override = solid


func _pose() -> void:
	_apply_state()
	var sp: Dictionary = STANDPOINTS[_standpoint]
	_camera.global_position = sp["feet"] + Vector3.UP * EYE
	_camera.rotation = Vector3(deg_to_rad(sp["pitch"]), deg_to_rad(sp["yaw"]), 0.0)
	_frame = 0
	_acc = 0.0
	_worst = 0.0
	_last_us = Time.get_ticks_usec()


## Wall clock between rendered frames, not `delta`, which `--fixed-fps` would
## hold constant.
func _process(_delta: float) -> void:
	if not _running:
		return
	var now := Time.get_ticks_usec()
	var frame_s := (now - _last_us) / 1000000.0
	_last_us = now
	_frame += 1
	if _frame <= SETTLE:
		return
	_acc += frame_s
	_worst = maxf(_worst, frame_s)
	if _frame < SETTLE + MEASURE:
		return
	_line("render  %-17s %-8s mean %6.2f ms  worst %6.2f ms  objects %6d  primitives %9d  draw_calls %6d" % [
		STANDPOINTS[_standpoint]["name"], STATES[_state],
		_acc / float(MEASURE) * 1000.0, _worst * 1000.0,
		int(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)),
		int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)),
		int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))])
	_state += 1
	if _state >= STATES.size():
		_state = 0
		_standpoint += 1
	if _standpoint < STANDPOINTS.size():
		_pose()
		return
	_finish()


func _line(text: String) -> void:
	print(text)
	_lines.append(text)


func _finish() -> void:
	_running = false
	var path := "user://palm_perf_%s.txt" % DisplayServer.get_name()
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f != null:
		f.store_string("\n".join(_lines) + "\n")
		f.close()
	print("wrote ", path)
	get_tree().quit()
