extends Node3D

## Runtime motion for the editor-owned R1 wheel form. The scene owns every
## artistic transform; this script only advances those rest transforms around
## the fixed axle while the park is open. Gondola roots orbit without rotating,
## which leaves their passenger floors hanging upright under gravity.

const HUB := Vector3(-111.6, 12.6, -16.0)

@export_range(1.0, 12.0, 0.25) var seconds_per_car_step := 3.0
@export_range(0.0, 12.0, 0.25) var boarding_dwell_seconds := 4.0

var _phase := 0.0
var _step_progress := 0.0
var _dwell := 0.0
var _spoke_rest: Dictionary = {}
var _gondola_rest: Dictionary = {}


func _ready() -> void:
	for member in $machine/spokes.get_children():
		if member is Node3D:
			_spoke_rest[member] = member.transform
	var index := 0
	for car in $machine/gondolas.get_children():
		if car is Node3D:
			_gondola_rest[car] = car.position
			var cabin := car.get_node_or_null("cabin")
			if cabin != null:
				var number := "%02d" % (index + 1)
				var number_east := cabin.get_node_or_null("number_east") as Label3D
				var number_west := cabin.get_node_or_null("number_west") as Label3D
				if number_east != null:
					number_east.text = number
				if number_west != null:
					number_west.text = number
			index += 1
	_dwell = boarding_dwell_seconds


func _process(delta: float) -> void:
	if not ParkClock.is_open() or seconds_per_car_step <= 0.0:
		return
	if _dwell > 0.0:
		_dwell = maxf(_dwell - delta, 0.0)
		return
	var car_step := TAU / maxf(float(_gondola_rest.size()), 1.0)
	var advance := car_step * delta / seconds_per_car_step
	_step_progress += advance
	if _step_progress >= car_step:
		advance -= _step_progress - car_step
		_step_progress = 0.0
		_dwell = boarding_dwell_seconds
	_phase = fposmod(_phase + advance, TAU)
	_place_rotor()


func phase_radians() -> float:
	return _phase


func release_boarding_dwell_for_test() -> void:
	## Focused acceptance can exercise motion without waiting through the
	## passenger dwell; normal runtime never calls this.
	_dwell = 0.0


func _place_rotor() -> void:
	var turn := Basis(Vector3.RIGHT, -_phase)
	for member in _spoke_rest:
		var spoke := member as Node3D
		var rest: Transform3D = _spoke_rest[spoke]
		spoke.transform = Transform3D(
			turn * rest.basis,
			HUB + turn * (rest.origin - HUB))
	for car in _gondola_rest:
		var gondola := car as Node3D
		var rest: Vector3 = _gondola_rest[gondola]
		gondola.position = HUB + turn * (rest - HUB)
		gondola.basis = Basis.IDENTITY
