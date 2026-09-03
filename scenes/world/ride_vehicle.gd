extends Node3D

## The two moving rail-shaped things in the park.
##
## They share motion and nothing else. `KIDDIE_TRAIN` is a low, slow attraction
## on a closed miniature railway; `GRAND_TRAM` is the rubber-tyred road train that
## carries people between lands. Keeping one route sampler prevents the visible
## vehicle and the generated right-of-way from becoming two descriptions of the
## same curve.
##
## Vehicles are deliberately visual in this greybox. The track and station
## barriers own safety; a moving collision body can launch a player standing at
## a curve seam and would turn a circulation test into a physics test. Boarding
## becomes interaction work when a section has a real queue and crowd graph.

const Plan := preload("res://scripts/park_plan.gd")

enum Service {
	KIDDIE_TRAIN,
	GRAND_TRAM,
}

@export var service := Service.KIDDIE_TRAIN
@export var route_override := PackedVector3Array()

const MINI_SPEED := 1.75
const MINI_DWELL := 5.0
const TRAM_SPEED := 4.2
const TRAM_DWELL := 9.0

const PALETTE := {
	&"wood": [Color(0.55, 0.42, 0.30), 0.90, 0.0],
	&"metal": [Color(0.30, 0.31, 0.33), 0.55, 0.20],
	&"white": [Color(0.87, 0.86, 0.82), 0.80, 0.0],
	&"red": [Color(0.84, 0.27, 0.24), 0.70, 0.0],
	&"yellow": [Color(0.93, 0.76, 0.24), 0.70, 0.0],
	&"blue": [Color(0.27, 0.50, 0.72), 0.70, 0.0],
	&"green": [Color(0.25, 0.48, 0.31), 0.78, 0.0],
	&"canvas": [Color(0.86, 0.40, 0.33), 0.85, 0.0],
	&"canvas_alt": [Color(0.35, 0.55, 0.66), 0.85, 0.0],
	&"skin": [Color(0.80, 0.67, 0.53), 0.90, 0.0],
}

var _route: Array[Vector3] = []
var _cumulative := PackedFloat32Array()
var _length := 0.0
var _distance := 0.0
var _speed := MINI_SPEED
var _dwell_seconds := MINI_DWELL
var _dwell := 0.0
var _returning := false
var _operating := false
var _units: Array[Node3D] = []
var _offsets := PackedFloat32Array()
var _stop_distances := PackedFloat32Array()
var _riders: Array[Node3D] = []
var _materials: Dictionary = {}


func _ready() -> void:
	if route_override.size() > 1:
		for point in route_override:
			_route.append(point)
	else:
		_route = (Plan.kiddie_rail_loop() if service == Service.KIDDIE_TRAIN
			else Plan.grand_tram_loop())
	_speed = MINI_SPEED if service == Service.KIDDIE_TRAIN else TRAM_SPEED
	_dwell_seconds = MINI_DWELL if service == Service.KIDDIE_TRAIN else TRAM_DWELL
	_build_distance_table()
	_build_materials()
	if service == Service.KIDDIE_TRAIN:
		_build_kiddie_train()
	else:
		_build_grand_tram()
	_build_stops()

	ParkClock.park_opened.connect(_on_park_opened)
	ParkClock.park_closed.connect(_on_park_closed)
	ParkClock.clock_jumped.connect(_on_clock_jumped)
	_sync_to_clock(true)
	_place_units()


func _process(delta: float) -> void:
	if _length <= 0.0:
		return
	if _dwell > 0.0:
		_dwell = maxf(_dwell - delta, 0.0)
		return
	if not _operating and not _returning:
		return

	var travel := _speed * delta
	if _returning:
		var home := fposmod(-_distance, _length)
		if home <= travel or home >= _length - 0.001:
			_distance = 0.0
			_returning = false
			_operating = false
			_set_riders(false)
			_place_units()
			return
	else:
		for stop in _stop_distances:
			var to_stop := fposmod(stop - _distance, _length)
			if to_stop > 0.001 and to_stop <= travel:
				_distance = stop
				_dwell = _dwell_seconds
				_place_units()
				return

	_distance = fposmod(_distance + travel, _length)
	_place_units()


func route_distance() -> float:
	return _distance


func route_length() -> float:
	return _length


func is_operating() -> bool:
	return _operating or _returning


func service_name() -> StringName:
	return &"kiddie_train" if service == Service.KIDDIE_TRAIN else &"grand_tram"


func _on_park_opened() -> void:
	_operating = true
	_returning = false
	_dwell = _dwell_seconds
	_set_riders(true)


func _on_park_closed() -> void:
	_operating = false
	_returning = not is_zero_approx(_distance)
	_dwell = 0.0
	if not _returning:
		_set_riders(false)


func _on_clock_jumped() -> void:
	_sync_to_clock(false)
	_place_units()


func _sync_to_clock(initial: bool) -> void:
	if ParkClock.is_open():
		_operating = true
		_returning = false
		_dwell = _dwell_seconds if initial else 0.0
		_set_riders(true)
	else:
		_distance = 0.0
		_operating = false
		_returning = false
		_dwell = 0.0
		_set_riders(false)


func _build_distance_table() -> void:
	_cumulative.clear()
	_cumulative.append(0.0)
	_length = 0.0
	for i in _route.size() - 1:
		_length += _route[i].distance_to(_route[i + 1])
		_cumulative.append(_length)


func _build_stops() -> void:
	_stop_distances.clear()
	if service == Service.KIDDIE_TRAIN:
		_stop_distances.append(0.0)
		return
	for station in Plan.GRAND_TRAM_STATIONS:
		_stop_distances.append(_nearest_distance(station["at"]))
	_stop_distances.sort()


func _nearest_distance(at: Vector3) -> float:
	var best_d2 := INF
	var best := 0.0
	for i in _route.size() - 1:
		var a := _route[i]
		var b := _route[i + 1]
		var ab := b - a
		var t := clampf((at - a).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
		var d2 := at.distance_squared_to(a + ab * t)
		if d2 < best_d2:
			best_d2 = d2
			best = _cumulative[i] + ab.length() * t
	return best


func _sample(along: float) -> Array[Vector3]:
	var d := fposmod(along, _length)
	var segment := _route.size() - 2
	for i in _cumulative.size() - 1:
		if d <= _cumulative[i + 1]:
			segment = i
			break
	var a := _route[segment]
	var b := _route[segment + 1]
	var span := maxf(_cumulative[segment + 1] - _cumulative[segment], 0.001)
	var t := (d - _cumulative[segment]) / span
	return [a.lerp(b, t), (b - a).normalized()]


func _place_units() -> void:
	for i in _units.size():
		var sample := _sample(_distance - _offsets[i])
		var unit := _units[i]
		unit.position = sample[0]
		var direction: Vector3 = sample[1]
		var up := Vector3.UP if absf(direction.dot(Vector3.UP)) < 0.96 else Vector3.FORWARD
		unit.basis = Basis.looking_at(direction, up)


func _build_materials() -> void:
	for key in PALETTE:
		var values: Array = PALETTE[key]
		var mat := StandardMaterial3D.new()
		mat.albedo_color = values[0]
		mat.roughness = values[1]
		mat.metallic = values[2]
		_materials[key] = mat


func _unit(nm: String, offset: float) -> Node3D:
	var unit := Node3D.new()
	unit.name = nm
	add_child(unit)
	_units.append(unit)
	_offsets.append(offset)
	return unit


func _build_kiddie_train() -> void:
	var engine := _unit("engine", 0.0)
	_box(engine, "frame", Vector3(1.55, 0.25, 2.45), Vector3(0.0, 0.48, 0.0), &"red")
	_cylinder(engine, "boiler", 0.53, 1.55, Vector3(0.0, 1.20, -0.36),
		Vector3(PI * 0.5, 0.0, 0.0), &"blue", 12)
	_box(engine, "cab", Vector3(1.40, 1.50, 0.90), Vector3(0.0, 1.38, 0.78), &"yellow")
	_box(engine, "roof", Vector3(1.72, 0.14, 1.18), Vector3(0.0, 2.18, 0.78), &"canvas_alt")
	_cylinder(engine, "stack", 0.20, 0.82, Vector3(0.0, 1.96, -0.82),
		Vector3.ZERO, &"metal", 10)
	_wheels(engine, 0.82, [-0.78, 0.72], 0.40)

	for i in 2:
		var car := _unit("car_%d" % i, 3.0 + float(i) * 2.75)
		_box(car, "floor", Vector3(1.72, 0.20, 2.20), Vector3(0.0, 0.52, 0.0),
			&"yellow" if i == 0 else &"red")
		_box(car, "back", Vector3(1.65, 0.78, 0.12), Vector3(0.0, 1.02, 0.98), &"blue")
		for side in [-1.0, 1.0]:
			_box(car, "side_%s" % str(side), Vector3(0.12, 0.55, 2.05),
				Vector3(side * 0.80, 0.88, 0.0), &"blue")
		_box(car, "roof", Vector3(1.88, 0.12, 2.35), Vector3(0.0, 2.06, 0.0),
			&"canvas_alt" if i == 0 else &"canvas")
		for side in [-0.70, 0.70]:
			for z in [-0.72, 0.72]:
				_cylinder(car, "post_%s_%s" % [str(side), str(z)], 0.055, 1.28,
					Vector3(side, 1.38, z), Vector3.ZERO, &"white", 8)
		_wheels(car, 0.78, [-0.72, 0.72], 0.34)
		_passenger(car, Vector3(-0.38, 0.78, -0.28), i * 2)
		_passenger(car, Vector3(0.38, 0.78, 0.38), i * 2 + 1)


func _build_grand_tram() -> void:
	var tractor := _unit("tractor", 0.0)
	_box(tractor, "chassis", Vector3(2.45, 0.40, 3.75), Vector3(0.0, 0.58, 0.0), &"green")
	_box(tractor, "hood", Vector3(2.15, 1.05, 1.70), Vector3(0.0, 1.18, -0.90), &"yellow")
	_box(tractor, "cab", Vector3(2.10, 1.80, 1.38), Vector3(0.0, 1.55, 0.95), &"white")
	_box(tractor, "roof", Vector3(2.55, 0.16, 1.78), Vector3(0.0, 2.52, 0.96), &"green")
	_box(tractor, "bumper", Vector3(2.55, 0.20, 0.24), Vector3(0.0, 0.48, -1.98), &"metal")
	_wheels(tractor, 1.08, [-1.22, 1.10], 0.48)

	for i in 3:
		var car := _unit("trailer_%d" % i, 5.1 + float(i) * 4.65)
		_box(car, "floor", Vector3(2.60, 0.28, 3.72), Vector3(0.0, 0.56, 0.0),
			&"red" if i % 2 == 0 else &"blue")
		_box(car, "roof", Vector3(2.82, 0.16, 3.95), Vector3(0.0, 2.55, 0.0),
			&"canvas" if i % 2 == 0 else &"canvas_alt")
		for side in [-1.12, 1.12]:
			for z in [-1.48, 1.48]:
				_cylinder(car, "post_%s_%s" % [str(side), str(z)], 0.065, 1.72,
					Vector3(side, 1.62, z), Vector3.ZERO, &"white", 8)
			_box(car, "side_%s" % str(side), Vector3(0.12, 0.58, 3.48),
				Vector3(side * 1.23, 0.93, 0.0), &"green")
		for z in [-1.18, 0.0, 1.18]:
			_box(car, "bench_%s" % str(z), Vector3(2.15, 0.14, 0.62),
				Vector3(0.0, 0.92, z), &"wood")
		_wheels(car, 1.10, [-1.25, 1.25], 0.44)
		for row in 3:
			_passenger(car, Vector3(-0.60, 1.02, -1.18 + float(row) * 1.18), i * 6 + row * 2)
			_passenger(car, Vector3(0.60, 1.02, -1.18 + float(row) * 1.18), i * 6 + row * 2 + 1)


func _wheels(root: Node3D, x: float, zs: Array, radius: float) -> void:
	for side in [-x, x]:
		for z in zs:
			_cylinder(root, "wheel_%s_%s" % [str(side), str(z)], radius, 0.18,
				Vector3(side, radius, z), Vector3(0.0, 0.0, PI * 0.5), &"metal", 12)


func _passenger(root: Node3D, at: Vector3, index: int) -> void:
	var rider := Node3D.new()
	rider.name = "rider_%02d" % index
	rider.position = at
	root.add_child(rider)
	_riders.append(rider)
	_box(rider, "body", Vector3(0.42, 0.62, 0.34), Vector3(0.0, 0.42, 0.0),
		[&"red", &"yellow", &"blue", &"green"][index % 4])
	_sphere(rider, "head", 0.20, Vector3(0.0, 0.92, 0.0), &"skin")


func _set_riders(shown: bool) -> void:
	for rider in _riders:
		rider.visible = shown


func _box(root: Node3D, nm: String, size: Vector3, at: Vector3, mat: StringName) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size
	var node := MeshInstance3D.new()
	node.name = nm
	node.mesh = mesh
	node.material_override = _materials[mat]
	node.position = at
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	root.add_child(node)


func _cylinder(root: Node3D, nm: String, radius: float, height: float,
		at: Vector3, rotation: Vector3, mat: StringName, sides: int) -> void:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = sides
	var node := MeshInstance3D.new()
	node.name = nm
	node.mesh = mesh
	node.material_override = _materials[mat]
	node.position = at
	node.rotation = rotation
	root.add_child(node)


func _sphere(root: Node3D, nm: String, radius: float, at: Vector3,
		mat: StringName) -> void:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh.radial_segments = 10
	mesh.rings = 6
	var node := MeshInstance3D.new()
	node.name = nm
	node.mesh = mesh
	node.material_override = _materials[mat]
	node.position = at
	root.add_child(node)
