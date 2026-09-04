extends Node

## Dev probe: what the range forest costs to draw, at several densities, from
## two standpoints that face it — the promenade's north end and the foot of
## the arrival walk. Whole-frame wall clock, the same unit `perf_test` uses,
## because the budget is shared. Writes `user://forest_perf.txt`, since a run
## launched by `open` has no stdout anyone can read.

## Each entry is [near density per hectare, far density per hectare]; far
## trees are impostor cards, shadows off throughout.
const DENSITIES := [[45.0, 200.0], [110.0, 200.0], [160.0, 200.0]]
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
var _d := 0
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
	_forest = _main.find_child("range_forest", true, false)
	if _forest == null:
		_lines.append("no range_forest node")
		_finish()
		return
	_apply()


func _apply() -> void:
	_forest.forest_per_hectare = float(DENSITIES[_d][0])
	_forest.far_per_hectare = float(DENSITIES[_d][1])
	_forest.meadow_per_hectare = 3.0
	_forest.set_shadows(false)
	_forest.replant()
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
	_lines.append("near %4.0f far %4.0f /ha  trees %7d  plant %7.0f ms  %-16s avg %6.2f ms  worst %6.2f ms" % [
		float(DENSITIES[_d][0]), float(DENSITIES[_d][1]), _forest.planted, _forest.plant_ms,
		STANDPOINTS[_s]["name"], avg, _worst * 1000.0])
	_s += 1
	if _s < STANDPOINTS.size():
		_pose()
		return
	_d += 1
	if _d < DENSITIES.size():
		_apply()
		return
	_finish()


func _finish() -> void:
	var f := FileAccess.open("user://forest_perf.txt", FileAccess.WRITE)
	for line in _lines:
		f.store_line(line)
	f.close()
	get_tree().quit()
