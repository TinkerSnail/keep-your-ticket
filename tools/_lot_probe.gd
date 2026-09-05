extends Node

## Dev probe: does the coast highway show from the parking lots? The trough
## behind the first ridge passes about a hundred metres south of the front
## road, ten metres up the south arm's foot, and the parking clause's hedge
## at z 222 is the only thing between the lots and it. Five frames from
## the lots and the front road at a standing eye, and one back from the
## highway at the car's eye, looking at the lots and the park.

const Plan := preload("res://scripts/park_plan.gd")
const OUTPUT_DIR := "user://lot_probe"
const SETTLE_SECONDS := 4.0

const SHOTS := [
	{"name": "00_walk_head_south", "position": Vector3(0.0, 1.7, 215.0),
		"target": Vector3(20.0, 12.0, 380.0)},
	{"name": "01_west_lot_south_east", "position": Vector3(-40.0, 1.7, 198.0),
		"target": Vector3(60.0, 12.0, 370.0)},
	{"name": "02_east_lot_south", "position": Vector3(40.0, 1.7, 198.0),
		"target": Vector3(0.0, 12.0, 372.0)},
	{"name": "03_drop_off_south", "position": Vector3(0.0, 1.7, 232.0),
		"target": Vector3(-40.0, 12.0, 360.0)},
	{"name": "04_turning_circle_east", "position": Vector3(-80.0, 1.7, 236.0),
		"target": Vector3(120.0, 12.0, 330.0)},
	{"name": "05_east_lot_south_east", "position": Vector3(60.0, 1.7, 205.0),
		"target": Vector3(180.0, 14.0, 330.0)},
	{"name": "10_highway_behind_parking_north", "highway": Vector2(40.0, 370.0),
		"target": Vector3(0.0, 8.0, 150.0)},
	{"name": "11_highway_junction_north_west", "highway": Vector2(150.0, 340.0),
		"target": Vector3(-1.5, 30.0, -32.0)},
]

var _main: Node
var _camera: Camera3D
var _index := -1
var _timer := 0.0
var _started := false


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(11, 0)
	_camera = Camera3D.new()
	_camera.far = 8000.0
	_camera.fov = 62.0
	add_child(_camera)
	_camera.make_current()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	_timer = 3.0


func _highway_eye(xz: Vector2) -> Vector3:
	var road := _main.find_child("highway", true, false)
	var st: PackedVector3Array = road.get_meta("points")
	var best := st[0]
	var best_d := INF
	for p in st:
		var d := Vector2(p.x, p.z).distance_to(xz)
		if d < best_d:
			best_d = d
			best = p
	var space: PhysicsDirectSpaceState3D = get_viewport().find_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(best + Vector3.UP * 40.0, best - Vector3.UP * 40.0, 1)
	var hit: Dictionary = space.intersect_ray(query)
	var y := best.y
	if not hit.is_empty():
		y = hit["position"].y
	return Vector3(best.x, y + 1.4, best.z)


func _pose(index: int) -> void:
	_index = index
	var shot: Dictionary = SHOTS[index]
	var at: Vector3
	if shot.has("highway"):
		at = _highway_eye(shot["highway"])
	else:
		at = shot["position"]
	_camera.global_position = at
	_camera.look_at(shot["target"], Vector3.UP)
	print("lot probe %s at %s" % [shot["name"], at])
	_timer = SETTLE_SECONDS


func _process(delta: float) -> void:
	_timer -= delta
	if not _started:
		if _timer <= 0.0:
			_started = true
			_pose(0)
		return
	if _index < 0 or _timer > 0.0:
		return
	var shot: Dictionary = SHOTS[_index]
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
	get_viewport().get_texture().get_image().save_png(path)
	print("lot probe wrote ", path)
	if _index + 1 < SHOTS.size():
		_pose(_index + 1)
	else:
		_index = -1
		get_tree().quit()
