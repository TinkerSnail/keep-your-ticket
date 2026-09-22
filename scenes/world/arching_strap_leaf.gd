@tool
extends Node3D

## One editor-owned strap-leaf course shared by Lily of the Nile and lilyturf.
## The Path3D owns the rise, arch and drooping tip; this script derives only a
## softly folded ribbon whose width closes to a real point.

@export var leaf_material: Material:
	set(value):
		leaf_material = value
		_queue_rebuild()
@export_range(0.025, 0.16, 0.005) var half_width := 0.09:
	set(value):
		half_width = value
		_queue_rebuild()
@export_range(0.0, 0.035, 0.0025) var fold_depth := 0.012:
	set(value):
		fold_depth = value
		_queue_rebuild()

const LENGTH_SAMPLES := 25
const WIDTH_SAMPLES := 3

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
	var derived := get_node_or_null("derived_leaf") as MeshInstance3D
	if course == null or course.curve == null or derived == null:
		return
	var curve := course.curve
	var length := curve.get_baked_length()
	if length < 0.4:
		derived.mesh = null
		return
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var side := Vector3.FORWARD
	for length_index in LENGTH_SAMPLES - 1:
		var t0 := float(length_index) / float(LENGTH_SAMPLES - 1)
		var t1 := float(length_index + 1) / float(LENGTH_SAMPLES - 1)
		for width_index in WIDTH_SAMPLES - 1:
			var u0 := lerpf(-1.0, 1.0,
				float(width_index) / float(WIDTH_SAMPLES - 1))
			var u1 := lerpf(-1.0, 1.0,
				float(width_index + 1) / float(WIDTH_SAMPLES - 1))
			var a := _point(curve, length, side, t0, u0)
			var b := _point(curve, length, side, t1, u0)
			var c := _point(curve, length, side, t1, u1)
			var d := _point(curve, length, side, t0, u1)
			_append_triangle(vertices, normals, uvs, a, b, c,
				Vector2((u0 + 1.0) * 0.5, t0),
				Vector2((u0 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t1))
			_append_triangle(vertices, normals, uvs, a, c, d,
				Vector2((u0 + 1.0) * 0.5, t0),
				Vector2((u1 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t0))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, leaf_material)
	derived.mesh = mesh


func _point(curve: Curve3D, length: float, side: Vector3, t: float,
		u: float) -> Vector3:
	var point: Vector3 = curve.sample_baked(length * t, true)
	var tangent := _tangent(curve, length * t, length)
	var normal := side.cross(tangent).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.RIGHT
	elif normal.dot(Vector3.RIGHT) < 0.0:
		normal = -normal
	# A broad shoulder and late taper match Agapanthus and lilyturf better than
	# the former rectangular quad; the final sample closes completely.
	var shoulder := lerpf(0.58, 1.0, smoothstep(0.0, 0.2, t))
	var taper := pow(maxf(0.0, 1.0 - t), 0.3)
	var envelope := shoulder * taper
	var fold := fold_depth * (1.0 - absf(u)) * sin(PI * t)
	return point + side * u * half_width * envelope + normal * fold


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.035, length * 0.045)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.UP


func _append_triangle(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, a: Vector3, b: Vector3, c: Vector3,
		uv_a: Vector2, uv_b: Vector2, uv_c: Vector2) -> void:
	var normal := (b - a).cross(c - a).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.RIGHT
	vertices.append_array(PackedVector3Array([a, b, c]))
	normals.append_array(PackedVector3Array([normal, normal, normal]))
	uvs.append_array(PackedVector2Array([uv_a, uv_b, uv_c]))
