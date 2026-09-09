extends Node

## Dev probe: the roads as rebuilt on 2026-09-05/06, from the standpoints
## they are for. The interchange from the approach road, from a carriageway
## arriving at the bridge, from a ramp terminal, from the air in plan and
## oblique, and at night under its sodium lamps; the split-level section on
## the north coast from the seaward carriageway and from over the water;
## a walled cut in the trough; a portal; the north town's main street by
## day and night with its lanterns, kerbs and median; the beach town's
## shore-street junction; the beach road's rounded bend; the far shore's
## section. Road standpoints are found by ray, so a road in a cutting is
## shot from the cutting.

const Plan := preload("res://scripts/park_plan.gd")
const OUTPUT_DIR := "user://road_probe"
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


func _nearest(points: PackedVector3Array, xz: Vector2) -> int:
	var best := 0
	var best_d := INF
	for i in points.size():
		var d := Vector2(points[i].x, points[i].z).distance_to(xz)
		if d < best_d:
			best_d = d
			best = i
	return best


func _road_eye(points: PackedVector3Array, xz: Vector2) -> Vector3:
	var p := points[_nearest(points, xz)]
	return Vector3(p.x, _ground(Vector2(p.x, p.z), p.y) + EYE, p.z)


## Along a road: the eye at `xz` looking at the road `ahead` stations on.
func _along(points: PackedVector3Array, xz: Vector2, ahead: int) -> Dictionary:
	var i := _nearest(points, xz)
	var j := clampi(i + ahead, 0, points.size() - 1)
	var eye := _road_eye(points, xz)
	return {"at": eye, "target": points[j] + Vector3.UP * EYE}


## Along a tunnel bore, where the downward standpoint ray would otherwise put
## the camera on the roof instead of on the carriageway.
func _inside(points: PackedVector3Array, xz: Vector2, ahead: int) -> Dictionary:
	var i := _nearest(points, xz)
	var j := clampi(i + ahead, 0, points.size() - 1)
	return {"at": points[i] + Vector3.UP * EYE, "target": points[j] + Vector3.UP * EYE}


func _standing(xz: Vector2, fallback := 0.0) -> Vector3:
	return Vector3(xz.x, _ground(xz, fallback) + 1.7, xz.y)


func _plan() -> void:
	var a: PackedVector3Array = _main.find_child("highway", true, false).get_meta("points")
	var b: PackedVector3Array = _main.find_child("highway_b", true, false).get_meta("points")
	var ap: PackedVector3Array = _main.find_child("approach_road", true, false).get_meta("points")
	var cross: Vector3 = Plan.approach_crossing()
	var cx := Vector2(cross.x, cross.z)
	# The interchange.
	var up_ap := _along(ap, cx - Vector2(0.54, 0.84) * 75.0, 3)
	_shots.append({"name": "r00_overpass_from_the_approach_road", "clock": 9, "at": up_ap["at"],
		"target": Vector3(cross.x, cross.y + 1.0, cross.z)})
	var on_a := _along(a, cx + Vector2(0.89, -0.45) * 140.0, 6)
	_shots.append({"name": "r01_bridge_from_carriageway_a", "clock": 9, "at": on_a["at"], "target": on_a["target"]})
	var on_b := _along(b, cx - Vector2(0.89, -0.45) * 140.0, -6)
	_shots.append({"name": "r02_bridge_from_carriageway_b", "clock": 9, "at": on_b["at"], "target": on_b["target"]})
	var t_a := cx - Vector2(0.54, 0.84) * float(Plan.INTERCHANGE["terminal"])
	_shots.append({"name": "r03_park_side_terminal", "clock": 9,
		"at": _standing(t_a - Vector2(0.54, 0.84) * 22.0 + Vector2(-0.84, 0.54) * 6.0),
		"target": Vector3(t_a.x, _ground(t_a, 9.0) + 2.5, t_a.y)})
	_shots.append({"name": "r04_interchange_plan", "clock": 12,
		"at": Vector3(cross.x, 900.0, cross.z), "orthographic": 560.0})
	_shots.append({"name": "r05_interchange_oblique", "clock": 9,
		"at": Vector3(cross.x - 260.0, 170.0, cross.z + 220.0), "target": Vector3(cross.x, 8.0, cross.z)})
	_shots.append({"name": "r06_night_overpass_from_the_approach_road", "clock": 21, "at": up_ap["at"],
		"target": Vector3(cross.x, cross.y + 1.0, cross.z)})
	_shots.append({"name": "r07_night_interchange_oblique", "clock": 21,
		"at": Vector3(cross.x - 260.0, 170.0, cross.z + 220.0), "target": Vector3(cross.x, 8.0, cross.z)})
	# The north coast's split level.
	var split := _along(a, Vector2(-162.0, -853.0), 6)
	_shots.append({"name": "r08_split_level_from_carriageway_a", "clock": 9, "at": split["at"], "target": split["target"]})
	var split_b := _along(b, Vector2(-162.0, -853.0), -6)
	_shots.append({"name": "r09_split_level_from_carriageway_b", "clock": 9, "at": split_b["at"], "target": split_b["target"]})
	_shots.append({"name": "r10_split_level_from_over_the_water", "clock": 9,
		"at": Vector3(-262.0, 34.0, -880.0), "target": Vector3(-160.0, 22.0, -850.0)})
	# A cut in the trough, and a portal.
	var trough := _along(a, Vector2(314.0, 199.0), 6)
	_shots.append({"name": "r11_trough_cut_from_carriageway_a", "clock": 9, "at": trough["at"], "target": trough["target"]})
	var portal := _along(a, Vector2(-250.0, -1130.0), -5)
	_shots.append({"name": "r12_portal_from_carriageway_a", "clock": 9, "at": portal["at"], "target": portal["target"]})
	# The north town's main street.
	var main_st := _road_eye(a, Plan.valley_point(62.0, 120.0))
	var south := Plan.valley_point(62.0, -120.0)
	_shots.append({"name": "r13_north_main_street", "clock": 9, "at": main_st,
		"target": Vector3(south.x, _ground(south, 3.0) + EYE, south.y)})
	_shots.append({"name": "r14_night_north_main_street", "clock": 21, "at": main_st,
		"target": Vector3(south.x, _ground(south, 3.0) + EYE, south.y)})
	var hill := Plan.valley_point(62.0, 0.0)
	_shots.append({"name": "r15_north_main_street_at_hill_road", "clock": 9,
		"at": _standing(Plan.valley_point(84.0, 24.0), 3.0),
		"target": Vector3(hill.x, _ground(hill, 3.0) + 1.0, hill.y)})
	var nt := Plan.valley_point(70.0, 0.0)
	_shots.append({"name": "r16_north_town_plan", "clock": 12,
		"at": Vector3(nt.x, 700.0, nt.y), "orthographic": 360.0})
	# The beach town's junction with the highway, and its bend.
	_shots.append({"name": "r17_beach_shore_street_junction", "clock": 9,
		"at": _standing(Vector2(-40.0, 403.5), 0.0), "target": Vector3(8.0, 1.5, 400.0)})
	_shots.append({"name": "r18_beach_road_bend", "clock": 9,
		"at": _standing(Vector2(-79.0, 330.0), 0.0), "target": Vector3(-48.0, 1.5, 470.0)})
	# The far shore.
	var far := _along(a, Vector2(369.0, 1329.0), 6)
	_shots.append({"name": "r19_far_shore_from_carriageway_a", "clock": 9, "at": far["at"], "target": far["target"]})
	var far_short := _along(a, Vector2(292.0, 1153.0), 6)
	_shots.append({"name": "r20_far_shore_short_tunnel_portal", "clock": 9,
		"at": far_short["at"], "target": far_short["target"]})
	var far_long := _along(a, Vector2(546.0, 1719.0), 8)
	_shots.append({"name": "r21_far_shore_long_tunnel_portal", "clock": 9,
		"at": far_long["at"], "target": far_long["target"]})
	var lit_bore := _inside(a, Vector2(610.0, 1860.0), 5)
	_shots.append({"name": "r22_far_shore_tunnel_lights", "clock": 21,
		"at": lit_bore["at"], "target": lit_bore["target"]})
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
	print("road probe wrote ", path)
	if _index + 1 < _shots.size():
		_pose(_index + 1)
	else:
		_index = -1
		_shots = [{}]
		get_tree().quit()
