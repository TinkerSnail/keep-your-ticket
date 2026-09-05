extends Node

## Dev probe: the coast highway's three reveals from the car's own eye, and a
## strip of frames along the north descent where the sea is meant to show
## through the trees. The camera stands 1.4m over the road surface at each
## station, found by ray from above, so a road in a cutting is shot from the
## cutting and not from the plan's optimism. Q-3 the north tunnel's mouth (or
## the head of the descent), Q-2 the crest turnout, Q-1 the last portal before
## the junction (or the last station), all looking at what the map says.

const Plan := preload("res://scripts/park_plan.gd")
const OUTPUT_DIR := "user://drive_probe"
const SETTLE_SECONDS := 4.0
const EYE := 1.4

var _main: Node
var _camera: Camera3D
var _shots: Array = []
var _index := -1
var _timer := 0.0


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(9, 30)
	_camera = Camera3D.new()
	_camera.far = 8000.0
	_camera.fov = 62.0
	add_child(_camera)
	_camera.make_current()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	_timer = 3.0


func _stations() -> PackedVector3Array:
	var road := _main.find_child("highway", true, false)
	assert(road != null, "the highway is not mounted")
	return road.get_meta("points")


func _nearest(stations: PackedVector3Array, xz: Vector2) -> int:
	var best := 0
	var best_d := INF
	for i in stations.size():
		var d := Vector2(stations[i].x, stations[i].z).distance_to(xz)
		if d < best_d:
			best_d = d
			best = i
	return best


func _eye_at(station: Vector3) -> Vector3:
	var space: PhysicsDirectSpaceState3D = get_viewport().find_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(
		station + Vector3.UP * 40.0, station - Vector3.UP * 40.0, 1)
	var hit: Dictionary = space.intersect_ray(query)
	var y := station.y
	if not hit.is_empty():
		y = hit["position"].y
	return Vector3(station.x, y + EYE, station.z)


func _plan() -> void:
	var st := _stations()
	var portals: Array = []
	for child in _main.find_child("park_approach", true, false).get_children():
		if String(child.name).ends_with("_portal_a_lintel") or String(child.name).ends_with("_portal_b_lintel"):
			portals.append(child)
	print("drive probe: %d stations, %d portals" % [st.size(), portals.size()])
	var lighthouse := Vector3(-153.0, 30.0, -268.0)
	var tower := Vector3(-1.5, 30.0, -32.0)
	# Q-3: high on the north coast, the first sight of the headland and the
	# bay across the water.
	var q3 := st[_nearest(st, Vector2(-240.0, -1200.0))]
	_shots.append({"name": "q3_north_first_sight", "at": _eye_at(q3), "target": lighthouse})
	# Q-2: the view bend on the descent round the arm's foot, the park below.
	var q2 := st[_nearest(st, Plan.HIGHWAY_VIEW)]
	_shots.append({"name": "q2_view_bend", "at": _eye_at(q2), "target": tower})
	# Q-1: the park's own road coming over the foothill, the tower ahead.
	var approach := _main.find_child("approach_road", true, false)
	var ap: PackedVector3Array = approach.get_meta("points")
	var q1 := ap[_nearest(ap, Vector2(172.0, 288.0))]
	_shots.append({"name": "q1_foothill", "at": _eye_at(q1), "target": tower})
	var junction_i := _nearest(st, Plan.HIGHWAY_JUNCTION)
	# The descent strip: eight frames down the north coast looking along the road.
	var from_i := _nearest(st, Vector2(-240.0, -1200.0))
	var to_i := _nearest(st, Vector2(-85.0, -450.0))
	var step := maxi(1, absi(to_i - from_i) / 8)
	var dir := 1 if to_i > from_i else -1
	var k := 0
	var i := from_i
	while (i - to_i) * dir < 0 and k < 8:
		var ahead := st[clampi(i + dir * 3, 0, st.size() - 1)]
		_shots.append({"name": "strip_north_%d" % k, "at": _eye_at(st[i]),
			"target": ahead + Vector3.UP * EYE})
		i += dir * step
		k += 1
	# And the trough behind the park: four frames from the headland's back to
	# the junction, looking along the road, to see how hidden the park is.
	var back_i := _nearest(st, Vector2(-55.0, -354.0))
	step = maxi(1, absi(junction_i - back_i) / 4)
	dir = 1 if junction_i > back_i else -1
	k = 0
	i = back_i
	while (i - junction_i) * dir < 0 and k < 4:
		var ahead := st[clampi(i + dir * 3, 0, st.size() - 1)]
		_shots.append({"name": "strip_trough_%d" % k, "at": _eye_at(st[i]),
			"target": ahead + Vector3.UP * EYE})
		i += dir * step
		k += 1
	# The park road down from the junction: three frames.
	for j in 3:
		var idx := clampi(j, 0, ap.size() - 2)
		_shots.append({"name": "strip_park_road_%d" % j, "at": _eye_at(ap[idx]),
			"target": ap[idx + 1] + Vector3.UP * EYE})
	for s in _shots:
		print("  %s at %s" % [s["name"], s["at"]])
	_pose(0)


func _pose(index: int) -> void:
	_index = index
	var shot: Dictionary = _shots[index]
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
	print("drive probe wrote ", path)
	if _index + 1 < _shots.size():
		_pose(_index + 1)
	else:
		_index = -1
		_shots = [{}]
		get_tree().quit()
