extends Node

## Dev probe: the crescent range behind the rim, from far enough away to see
## it. `footprint_capture` frames the developed park and crops 300m past it,
## which is the one distance a 1.6km range cannot be judged from. Three shots:
## a plan wide enough for the whole crescent, an oblique from out over the sea
## looking at the park with the range behind it, and the south arm from the
## parking approach, which is where the road question lives.

const OUTPUT_DIR := "user://range_probe"
const SETTLE_SECONDS := 7.0

const SHOTS := [
	{"name": "00_crescent_plan", "position": Vector3(200.0, 3200.0, -200.0),
		"target": Vector3(200.0, 0.0, -200.0), "orthographic": 3600.0},
	{"name": "01_from_the_sea", "position": Vector3(-1500.0, 260.0, 300.0),
		"target": Vector3(300.0, 120.0, -150.0), "fov": 55.0},
	{"name": "02_from_the_north_sea", "position": Vector3(-1200.0, 260.0, -1100.0),
		"target": Vector3(250.0, 100.0, 0.0), "fov": 55.0},
	{"name": "03_parking_approach_south", "position": Vector3(0.0, 6.0, 240.0),
		"target": Vector3(0.0, 40.0, 900.0), "fov": 60.0},
	{"name": "04_east_axis_ground", "position": Vector3(130.0, 20.5, -2.0),
		"target": Vector3(900.0, 150.0, -2.0), "fov": 60.0},
	# The parking clause's Q0 and the shape brief's six acceptance standpoints.
	{"name": "10_Q0_arrival_from_the_car", "position": Vector3(0.0, 2.0, 236.0),
		"target": Vector3(-6.0, 30.0, -600.0), "fov": 60.0},
	{"name": "11_pier_head", "position": Vector3(-150.0, -4.3, -2.0),
		"target": Vector3(200.0, 60.0, -260.0), "fov": 70.0},
	{"name": "12_promenade_north", "position": Vector3(-98.0, -4.3, -70.0),
		"target": Vector3(-140.0, 20.0, -420.0), "fov": 70.0},
	{"name": "13_lighthouse_forecourt", "position": Vector3(-158.0, 22.0, -262.0),
		"target": Vector3(0.0, 20.0, -90.0), "fov": 70.0},
	{"name": "13b_promontory_walk", "position": Vector3(-52.0, 6.8, -240.0),
		"target": Vector3(-153.0, 30.0, -268.0), "fov": 70.0},
	{"name": "13c_promontory_from_the_cove", "position": Vector3(-75.0, 3.0, -205.0),
		"target": Vector3(-160.0, 20.0, -262.0), "fov": 70.0},
	{"name": "14_climb_head", "position": Vector3(118.0, 19.7, -2.0),
		"target": Vector3(900.0, 250.0, -300.0), "fov": 70.0},
	{"name": "15_east_forecourt", "position": Vector3(58.0, 1.7, -2.0),
		"target": Vector3(900.0, 250.0, -60.0), "fov": 70.0},
	{"name": "16_parking_arrival_north", "position": Vector3(0.0, 1.7, 226.0),
		"target": Vector3(0.0, 30.0, -600.0), "fov": 70.0},
	{"name": "17_parking_arrival_south", "position": Vector3(0.0, 1.7, 215.0),
		"target": Vector3(120.0, 60.0, 700.0), "fov": 70.0},
	# The bay (2026-09-04): its far shore from the pier head, the cove and the
	# point from the coaster's end, and a plan of the whole bay.
	{"name": "18_bay_from_pier_head", "position": Vector3(-150.0, -4.3, -2.0),
		"target": Vector3(120.0, 20.0, 700.0), "fov": 70.0},
	{"name": "19_cove_from_coaster_end", "position": Vector3(-100.0, -4.3, -150.0),
		"target": Vector3(-170.0, 12.0, -262.0), "fov": 70.0},
	{"name": "20_bay_plan", "position": Vector3(0.0, 2600.0, 400.0),
		"target": Vector3(0.0, 0.0, 400.0), "orthographic": 2800.0},
]

var _main: Node
var _camera: Camera3D
var _index := -1
var _timer := 0.0


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	_camera = Camera3D.new()
	_camera.far = 8000.0
	add_child(_camera)
	_camera.make_current()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	_pose(0)


func _pose(index: int) -> void:
	_index = index
	var shot: Dictionary = SHOTS[index]
	var position: Vector3 = shot["position"]
	var target: Vector3 = shot["target"]
	if shot.has("orthographic"):
		_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		_camera.size = float(shot["orthographic"])
		_camera.global_position = position
		_camera.global_rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	else:
		_camera.projection = Camera3D.PROJECTION_PERSPECTIVE
		_camera.fov = float(shot.get("fov", 55.0))
		_camera.global_position = position
		_camera.look_at(target, Vector3.UP)
	_timer = SETTLE_SECONDS


func _process(delta: float) -> void:
	if _index < 0:
		return
	_timer -= delta
	if _timer > 0.0:
		return
	var shot: Dictionary = SHOTS[_index]
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
	get_viewport().get_texture().get_image().save_png(path)
	print("range probe wrote ", path)
	if _index + 1 < SHOTS.size():
		_pose(_index + 1)
	else:
		_index = -1
		get_tree().quit()
