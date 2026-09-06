extends Node

## Dev probe: the three towns of package 02B from the standpoints they are
## for. The north town from the highway arriving out of the tunnel and along
## its main street at the car's eye, from the house's porch, from its beach,
## and from over the sea; the beach town from the pier head, the turning
## circle, its own road and the highway; the city from the pier head and the
## promenade over three kilometres of water. Each at 09:30 and the ones that
## matter again at 21:30, when the windows and the lamps are on. Three plans
## from above. The road standpoints are found by ray, so a road in a cutting
## is shot from the cutting.

const Plan := preload("res://scripts/park_plan.gd")
const OUTPUT_DIR := "user://town_probe"
const SETTLE_SECONDS := 4.0
const EYE := 1.4

var _main: Node
var _camera: Camera3D
var _shots: Array = []
var _index := -1
var _timer := 0.0
var _clock := -1


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(9, 30)
	_camera = Camera3D.new()
	_camera.far = 9000.0
	_camera.fov = 62.0
	add_child(_camera)
	_camera.make_current()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	_timer = 3.0


func _ground(xz: Vector2, fallback: float) -> float:
	var space: PhysicsDirectSpaceState3D = get_viewport().find_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(
		Vector3(xz.x, 400.0, xz.y), Vector3(xz.x, -40.0, xz.y), 1)
	var hit: Dictionary = space.intersect_ray(query)
	if hit.is_empty():
		return fallback
	return hit["position"].y


func _road_eye(points: PackedVector3Array, xz: Vector2) -> Vector3:
	var best := points[0]
	var best_d := INF
	for p in points:
		var d := Vector2(p.x, p.z).distance_to(xz)
		if d < best_d:
			best_d = d
			best = p
	return Vector3(best.x, _ground(Vector2(best.x, best.z), best.y) + EYE, best.z)


func _standing(xz: Vector2, fallback := 0.0) -> Vector3:
	return Vector3(xz.x, _ground(xz, fallback) + 1.7, xz.y)


func _plan() -> void:
	var highway: PackedVector3Array = _main.find_child("highway", true, false).get_meta("points")
	var towns := _main.find_child("park_towns", true, false)
	var house: Vector3 = towns.get_meta("house", Vector3.ZERO)
	var vp := func(s: float, t: float) -> Vector2: return Plan.valley_point(s, t)
	var u: Vector2 = Plan.NORTH_VALLEY["inland"]
	var mouth: Vector2 = vp.call(-250.0, 0.0)
	var head: Vector2 = vp.call(300.0, 0.0)
	var pier := Vector3(-150.0, -2.6, -2.0)
	var city_centre: Vector2 = Plan.FAR_CITY["centre"]
	var city := Vector3(city_centre.x, 30.0, city_centre.y)
	# The north town.
	var arrive := _road_eye(highway, vp.call(60.0, 235.0))
	_shots.append({"name": "n00_arriving_from_the_tunnel", "clock": 9,
		"at": arrive, "target": Vector3(mouth.x, 4.0, mouth.y) * 0.4 + Vector3(head.x, 8.0, head.y) * 0.6})
	var main_st := _road_eye(highway, vp.call(60.0, 0.0))
	var south := _road_eye(highway, vp.call(60.0, 220.0))
	_shots.append({"name": "n01_main_street_looking_south", "clock": 9,
		"at": main_st, "target": south + Vector3.UP * EYE})
	_shots.append({"name": "n02_main_street_looking_north", "clock": 9,
		"at": _road_eye(highway, vp.call(60.0, 120.0)),
		"target": _road_eye(highway, vp.call(60.0, -120.0)) + Vector3.UP * EYE})
	var n := Vector2(-u.y, u.x)
	var facing := (-u + n * 0.6).normalized()
	var porch := house + Vector3(facing.x, 0.0, facing.y) * 7.0 + Vector3.UP * 1.9
	_shots.append({"name": "n03_from_the_house", "clock": 9, "at": porch,
		"target": Vector3(mouth.x, -4.0, mouth.y)})
	_shots.append({"name": "n04_from_the_beach", "clock": 9,
		"at": _standing(vp.call(12.0, 30.0), -6.0), "target": Vector3(head.x, 22.0, head.y)})
	var hill_foot: Vector2 = vp.call(128.0, 0.0)
	_shots.append({"name": "n05_up_hill_road", "clock": 9, "at": _standing(hill_foot),
		"target": Vector3(head.x, 14.0, head.y)})
	var sea: Vector2 = vp.call(-700.0, 120.0)
	_shots.append({"name": "n06_valley_from_the_sea", "clock": 9,
		"at": Vector3(sea.x, 150.0, sea.y), "target": Vector3(hill_foot.x, 10.0, hill_foot.y)})
	_shots.append({"name": "n07_night_from_the_house", "clock": 21, "at": porch,
		"target": Vector3(mouth.x, -4.0, mouth.y)})
	_shots.append({"name": "n08_night_from_the_sea", "clock": 21,
		"at": Vector3(sea.x, 150.0, sea.y), "target": Vector3(hill_foot.x, 10.0, hill_foot.y)})
	_shots.append({"name": "n09_night_main_street", "clock": 21, "at": main_st,
		"target": south + Vector3.UP * EYE})
	# The beach town.
	var town := Vector3(-60.0, 1.0, 420.0)
	_shots.append({"name": "b00_from_the_pier_head", "clock": 9, "at": pier, "target": town})
	_shots.append({"name": "b01_from_the_turning_circle", "clock": 9,
		"at": Vector3(-80.0, 1.7, 236.0), "target": Vector3(-62.0, 2.0, 430.0)})
	_shots.append({"name": "b02_along_the_beach_road", "clock": 9,
		"at": _standing(Vector2(-79.0, 350.0)), "target": Vector3(-30.0, 2.0, 500.0)})
	_shots.append({"name": "b03_from_the_highway", "clock": 9,
		"at": _road_eye(highway, Vector2(4.0, 430.0)), "target": Vector3(-80.0, 0.0, 400.0)})
	_shots.append({"name": "b04_oblique_from_the_sea", "clock": 9,
		"at": Vector3(-420.0, 150.0, 260.0), "target": Vector3(-50.0, 0.0, 430.0)})
	_shots.append({"name": "b05_night_from_the_pier_head", "clock": 21, "at": pier, "target": town})
	_shots.append({"name": "b06_from_the_beach", "clock": 9,
		"at": _standing(Vector2(-100.0, 395.0), -6.0), "target": Vector3(-40.0, 4.0, 440.0)})
	# The city.
	_shots.append({"name": "c00_from_the_pier_head", "clock": 9, "at": pier, "target": city, "fov": 40.0})
	_shots.append({"name": "c01_from_the_promenade_south", "clock": 9,
		"at": Vector3(-98.0, -4.3, 66.0), "target": city, "fov": 40.0})
	_shots.append({"name": "c02_night_from_the_pier_head", "clock": 21, "at": pier, "target": city, "fov": 40.0})
	_shots.append({"name": "c03_oblique", "clock": 9,
		"at": Vector3(-200.0, 260.0, 2100.0), "target": Vector3(city.x, 0.0, city.z)})
	_shots.append({"name": "c04_from_the_far_shore_highway", "clock": 9,
		"at": _road_eye(highway, Vector2(400.0, 1400.0)), "target": Vector3(city.x, 20.0, city.z)})
	_shots.append({"name": "c05_night_oblique", "clock": 21,
		"at": Vector3(-200.0, 260.0, 2100.0), "target": Vector3(city.x, 0.0, city.z)})
	# Plans.
	var nt: Vector2 = vp.call(180.0, 0.0)
	_shots.append({"name": "p00_plan_north_town", "clock": 12,
		"at": Vector3(nt.x, 1500.0, nt.y), "orthographic": 900.0})
	_shots.append({"name": "p01_plan_beach_town", "clock": 12,
		"at": Vector3(-50.0, 900.0, 400.0), "orthographic": 420.0})
	_shots.append({"name": "p02_plan_city", "clock": 12,
		"at": Vector3(city.x, 2000.0, city.z), "orthographic": 1100.0})
	# The world's ends as geology (2026-09-05): the north shore's headlands
	# and coves from the sea and from the air, the city on its peninsula
	# from across the bay and from its own road, the south coast from the sea.
	_shots.append({"name": "w00_north_shore_from_the_sea", "clock": 9,
		"at": Vector3(-1250.0, 40.0, -3000.0), "target": Vector3(-100.0, 60.0, -2640.0)})
	_shots.append({"name": "w01_north_end_from_the_air", "clock": 9,
		"at": Vector3(-1500.0, 420.0, -2500.0), "target": Vector3(-200.0, 40.0, -2300.0)})
	_shots.append({"name": "w02_peninsula_from_the_air", "clock": 9,
		"at": Vector3(-450.0, 380.0, 2050.0), "target": Vector3(380.0, 20.0, 2650.0)})
	_shots.append({"name": "w03_city_from_the_beach", "clock": 9,
		"at": _standing(Vector2(-98.0, 462.0), -6.0), "target": Vector3(city.x, 40.0, city.z), "fov": 40.0})
	_shots.append({"name": "w04_city_from_its_road", "clock": 9,
		"at": _road_eye(highway, Vector2(790.0, 2440.0)), "target": Vector3(380.0, 30.0, 2560.0)})
	_shots.append({"name": "w05_south_coast_from_the_sea", "clock": 9,
		"at": Vector3(900.0, 60.0, 3150.0), "target": Vector3(1500.0, 40.0, 2650.0)})
	_shots.append({"name": "w06_night_city_from_the_beach", "clock": 21,
		"at": _standing(Vector2(-98.0, 462.0), -6.0), "target": Vector3(city.x, 40.0, city.z), "fov": 40.0})
	# The island whole, from the heights a start-screen aerial would use.
	_shots.append({"name": "a00_island_from_the_south_west", "clock": 15,
		"at": Vector3(-3400.0, 1500.0, 3800.0), "target": Vector3(900.0, 0.0, 100.0)})
	_shots.append({"name": "a01_island_from_the_north_east", "clock": 15,
		"at": Vector3(5200.0, 1700.0, -4200.0), "target": Vector3(700.0, 0.0, 300.0)})
	_shots.append({"name": "a02_park_from_the_sea_at_height", "clock": 15,
		"at": Vector3(-1600.0, 700.0, 900.0), "target": Vector3(120.0, 0.0, -60.0)})
	_shots.append({"name": "a03_island_plan", "clock": 12,
		"at": Vector3(1400.0, 5000.0, 150.0), "orthographic": 6400.0})
	for s in _shots:
		print("  %s at %s" % [s["name"], s["at"]])
	_pose(0)


func _pose(index: int) -> void:
	_index = index
	var shot: Dictionary = _shots[index]
	var clock: int = shot["clock"]
	if clock != _clock:
		_clock = clock
		ParkClock.set_clock(clock, 30)
	if shot.has("orthographic"):
		_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		_camera.size = float(shot["orthographic"])
		_camera.global_position = shot["at"]
		_camera.global_rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	else:
		_camera.projection = Camera3D.PROJECTION_PERSPECTIVE
		_camera.fov = float(shot.get("fov", 62.0))
		_camera.global_position = shot["at"]
		_camera.look_at(shot["target"], Vector3.UP)
	_timer = SETTLE_SECONDS


func _process(delta: float) -> void:
	_timer -= delta
	if _index < 0:
		if _timer <= 0.0 and _shots.is_empty():
			_plan()
		return
	if _timer > 0.0:
		return
	var shot: Dictionary = _shots[_index]
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
	get_viewport().get_texture().get_image().save_png(path)
	print("town probe wrote ", path)
	if _index + 1 < _shots.size():
		_pose(_index + 1)
	else:
		_index = -1
		_shots = [{}]
		get_tree().quit()
