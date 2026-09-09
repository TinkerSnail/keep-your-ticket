extends Node3D

## Lightweight motion only. Every subject's course, range and phase are
## authored on the node in coastal_fast_pass.tscn so the visible arrangement
## remains editable without changing this script.

var _elapsed := 0.0
var _origins: Dictionary = {}


func _ready() -> void:
	for subject in get_tree().get_nodes_in_group(&"coastal_fast_mover"):
		if subject is Node3D and is_ancestor_of(subject):
			_origins[subject] = subject.position


func _process(delta: float) -> void:
	_elapsed += delta
	for subject in _origins:
		if not is_instance_valid(subject):
			continue
		var axis: Vector3 = subject.get_meta(&"motion_axis", Vector3.RIGHT)
		var distance := float(subject.get_meta(&"motion_distance", 2.0))
		var speed := float(subject.get_meta(&"motion_speed", 0.35))
		var phase := float(subject.get_meta(&"motion_phase", 0.0))
		subject.position = _origins[subject] + axis.normalized() * sin(_elapsed * speed + phase) * distance
