extends Node

## One-hour breadth-pass proof: one frame for each cluster added by the
## editor-owned coastal fast-pass scene. These are inspection views, not new
## canonical composition decisions.

const OUTPUT_DIR := "user://coastal_fast_pass_2026_09_06_v2"
const SETTLE_SECONDS := 2.0

var _main: Node
var _camera: Camera3D
var _shots := [
	{"name": "01_beach_public_realm", "at": Vector3(-145, 13, 345), "target": Vector3(-45, 1, 425), "fov": 58.0},
	{"name": "02_beach_plan", "at": Vector3(-50, 320, 415), "target": Vector3(-50, 0, 415), "ortho": 260.0},
	{"name": "03_north_main_street", "at": Vector3(-525, 28, -1910), "target": Vector3(-360, 11, -1840), "fov": 54.0},
	{"name": "04_lake_and_drive_in", "at": Vector3(-500, 180, -2040), "target": Vector3(-220, 10, -1870), "fov": 52.0},
	{"name": "05_harbour_and_headland", "at": Vector3(-390, 70, -170), "target": Vector3(-160, 2, -280), "fov": 52.0},
	{"name": "06_fishing_deck", "at": Vector3(-165, 8, 28), "target": Vector3(-135, -1, 9), "fov": 58.0},
	{"name": "07_rail_and_park_halt", "at": Vector3(420, 330, 300), "target": Vector3(170, 5, 75), "fov": 48.0},
	{"name": "08_city_facelift", "at": Vector3(-80, 190, 2260), "target": Vector3(350, 45, 2525), "fov": 45.0},
]
var _index := -1
var _timer := 3.0


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	_camera = Camera3D.new()
	_camera.far = 9000.0
	add_child(_camera)
	_camera.make_current()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))


func _pose(index: int) -> void:
	_index = index
	var shot: Dictionary = _shots[index]
	_camera.global_position = shot["at"]
	if shot.has("ortho"):
		_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		_camera.size = shot["ortho"]
		_camera.global_rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	else:
		_camera.projection = Camera3D.PROJECTION_PERSPECTIVE
		_camera.fov = shot["fov"]
		_camera.look_at(shot["target"], Vector3.UP)
	_timer = SETTLE_SECONDS


func _process(delta: float) -> void:
	_timer -= delta
	if _index < 0:
		if _timer <= 0.0:
			_pose(0)
		return
	if _timer > 0.0:
		return
	var path := "%s/%s.png" % [OUTPUT_DIR, _shots[_index]["name"]]
	get_viewport().get_texture().get_image().save_png(path)
	print("coastal fast-pass probe wrote ", path)
	if _index + 1 < _shots.size():
		_pose(_index + 1)
	else:
		get_tree().quit()
