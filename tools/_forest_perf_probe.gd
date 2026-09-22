extends Node

## Dev probe: what the approved 240m-setback background-only range mass costs to draw,
## hidden and visible, from three standpoints that face it. Writes
## `user://range_canopy_perf.txt`, since a run launched by `open` has no stdout anyone
## can read.

const VISIBLE_STATES := [false, true]
const SETTLE := 40
const MEASURE := 150
const STANDPOINTS := [
	{"name": "promenade_north", "position": Vector3(-98.0, -4.3, -70.0), "target": Vector3(-140.0, 20.0, -420.0)},
	{"name": "walk_foot", "position": Vector3(0.0, 2.0, 236.0), "target": Vector3(-6.0, 30.0, -600.0)},
	{"name": "climb_head", "position": Vector3(118.0, 19.7, -2.0), "target": Vector3(900.0, 250.0, -300.0)},
]

var _main: Node
var _camera: Camera3D
var _forest: Node
var _lines: PackedStringArray = []
var _state := 0
var _s := 0
var _frame := 0
var _acc := 0.0
var _worst := 0.0


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	_camera = Camera3D.new()
	_camera.far = 8000.0
	add_child(_camera)
	_camera.make_current()
	_forest = _main.find_child("range_forest_background", true, false)
	if _forest == null:
		_lines.append("no range_forest_background node")
		_finish()
		return
	_apply()


func _apply() -> void:
	_forest.visible = VISIBLE_STATES[_state]
	_s = 0
	_pose()


func _pose() -> void:
	var sp: Dictionary = STANDPOINTS[_s]
	_camera.fov = 70.0
	_camera.global_position = sp["position"]
	_camera.look_at(sp["target"], Vector3.UP)
	_frame = 0
	_acc = 0.0
	_worst = 0.0


func _process(delta: float) -> void:
	if _forest == null:
		return
	_frame += 1
	if _frame <= SETTLE:
		return
	_acc += delta
	_worst = maxf(_worst, delta)
	if _frame < SETTLE + MEASURE:
		return
	var avg := _acc / float(MEASURE) * 1000.0
	_lines.append("background %-7s  %-16s avg %6.2f ms  worst %6.2f ms" % [
		"visible" if VISIBLE_STATES[_state] else "hidden",
		STANDPOINTS[_s]["name"], avg, _worst * 1000.0])
	_s += 1
	if _s < STANDPOINTS.size():
		_pose()
		return
	_state += 1
	if _state < VISIBLE_STATES.size():
		_apply()
		return
	_finish()


func _finish() -> void:
	var f := FileAccess.open("user://range_canopy_perf.txt", FileAccess.WRITE)
	for line in _lines:
		f.store_line(line)
	f.close()
	get_tree().quit()
