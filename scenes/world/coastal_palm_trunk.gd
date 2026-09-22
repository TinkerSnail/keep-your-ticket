@tool
extends Node3D

## The selectable Path3D owns the trunk's subtle normalized bend. This script
## derives only a low-sided tapered tube with a slightly flared base. Instances
## scale the one-metre source to their established generated trunk length.

@export var trunk_material: Material
@export_range(0.25, 1.35, 0.05) var bend_strength := 1.0:
	set(value):
		bend_strength = value
		_queue_rebuild()

const RINGS := 14
const SIDES := 8

var _queued := false


func _ready() -> void:
	var path := get_node("trunk_course") as Path3D
	if path.curve != null and not path.curve.changed.is_connected(_queue_rebuild):
		path.curve.changed.connect(_queue_rebuild)
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _queued or not is_inside_tree():
		return
	_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_queued = false
	var path := get_node("trunk_course") as Path3D
	var instance := get_node("derived_trunk") as MeshInstance3D
	if path.curve == null:
		instance.mesh = null
		return
	var curve := path.curve
	var length := curve.get_baked_length()
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	for ring in RINGS:
		var t := float(ring) / float(RINGS - 1)
		var centre: Vector3 = curve.sample_baked(length * t, true)
		centre.x *= bend_strength
		centre.z *= bend_strength
		var tangent := _tangent(curve, length * t, length)
		tangent = Vector3(tangent.x * bend_strength, tangent.y,
			tangent.z * bend_strength).normalized()
		var side := tangent.cross(Vector3.FORWARD).normalized()
		if side.length_squared() < 0.5:
			side = Vector3.RIGHT
		var forward := side.cross(tangent).normalized()
		var radius := _radius_at(t)
		for side_index in SIDES:
			var angle := TAU * float(side_index) / float(SIDES)
			var radial := side * cos(angle) + forward * sin(angle)
			vertices.append(centre + radial * radius)
			normals.append(radial)
			uvs.append(Vector2(float(side_index) / float(SIDES), t))
		if ring < RINGS - 1:
			for side_index in SIDES:
				var next_side := (side_index + 1) % SIDES
				var a := ring * SIDES + side_index
				var b := ring * SIDES + next_side
				var c := (ring + 1) * SIDES + side_index
				var d := (ring + 1) * SIDES + next_side
				indices.append_array(PackedInt32Array([a, c, b, b, c, d]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, trunk_material)
	instance.mesh = mesh


func _radius_at(t: float) -> float:
	# At an eight-metre instance this is about 34cm across at the bulb, easing
	# to 23cm through the shaft and 19cm beneath the crown.
	var shaft := lerpf(0.015, 0.012, t)
	var base_flare := 0.006 * pow(maxf(0.0, 1.0 - t / 0.13), 2.0)
	return shaft + base_flare


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.025, length * 0.04)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.UP
