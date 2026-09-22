@tool
extends Node3D

## The Path3D owns the stem's visible gesture. This tool derives only a slim,
## tapered set of cylinder segments so an editor-drawn bend stays easy to
## reshape without rebuilding the stalk by hand.

@export var stem_material: Material:
	set(value):
		stem_material = value
		_queue_rebuild()
@export_range(0.012, 0.04, 0.001) var base_radius := 0.026:
	set(value):
		base_radius = value
		_queue_rebuild()
@export_range(0.008, 0.03, 0.001) var tip_radius := 0.018:
	set(value):
		tip_radius = value
		_queue_rebuild()
@export_range(6, 14, 1) var segment_count := 10:
	set(value):
		segment_count = value
		_queue_rebuild()

var _queued := false


func _ready() -> void:
	var course := get_node_or_null("course") as Path3D
	if course != null and course.curve != null \
			and not course.curve.changed.is_connected(_queue_rebuild):
		course.curve.changed.connect(_queue_rebuild)
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _queued or not is_inside_tree():
		return
	_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_queued = false
	var course := get_node_or_null("course") as Path3D
	var derived := get_node_or_null("derived_stem") as Node3D
	if course == null or course.curve == null or derived == null:
		return
	for child in derived.get_children():
		child.free()
	var curve := course.curve
	var length := curve.get_baked_length()
	if length < 0.2:
		return
	for index in segment_count:
		var t0 := float(index) / float(segment_count)
		var t1 := float(index + 1) / float(segment_count)
		var start: Vector3 = curve.sample_baked(length * t0, true)
		var finish: Vector3 = curve.sample_baked(length * t1, true)
		_add_segment(derived, index, start, finish, t0, t1)


func _add_segment(parent: Node3D, index: int, start: Vector3,
		finish: Vector3, t0: float, t1: float) -> void:
	var delta := finish - start
	if delta.length_squared() < 0.00001:
		return
	var mesh := CylinderMesh.new()
	mesh.bottom_radius = lerpf(base_radius, tip_radius, t0)
	mesh.top_radius = lerpf(base_radius, tip_radius, t1)
	mesh.height = delta.length()
	mesh.radial_segments = 7
	mesh.rings = 1
	var instance := MeshInstance3D.new()
	instance.name = "segment_%02d" % index
	instance.mesh = mesh
	instance.material_override = stem_material
	instance.transform = Transform3D(
		Basis(Quaternion(Vector3.UP, delta.normalized())),
		(start + finish) * 0.5)
	parent.add_child(instance)
