@tool
extends Node3D

## Surfaces the selectable Path3D leaves in one cordyline crown. Each course is
## the artistic source; this script only gives that course a folded, pointed
## ribbon and a slightly raised midrib.

@export var leaf_material: Material:
	set(value):
		leaf_material = value
		_queue_rebuild()
@export var midrib_material: Material:
	set(value):
		midrib_material = value
		_queue_rebuild()

const LENGTH_SAMPLES := 19
const WIDTH_SAMPLES := 5

var _queued := false


func _ready() -> void:
	var courses := get_node_or_null("leaf_courses") as Node3D
	if courses == null:
		return
	for child in courses.get_children():
		var path := child as Path3D
		if path != null and path.curve != null \
				and not path.curve.changed.is_connected(_queue_rebuild):
			path.curve.changed.connect(_queue_rebuild)
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _queued or not is_inside_tree():
		return
	_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_queued = false
	var courses := get_node_or_null("leaf_courses") as Node3D
	var derived := get_node_or_null("derived_leaves") as Node3D
	if courses == null or derived == null:
		return
	for child in derived.get_children():
		child.free()
	for child in courses.get_children():
		var path := child as Path3D
		if path == null or path.curve == null:
			continue
		_build_leaf(path, derived)


func _build_leaf(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.35:
		return
	var half_width := float(path.get_meta("half_width", 0.055))
	var fold_depth := float(path.get_meta("fold_depth", 0.018))
	var side := _leaf_side(curve, length)
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	for length_index in LENGTH_SAMPLES - 1:
		var t0 := float(length_index) / float(LENGTH_SAMPLES - 1)
		var t1 := float(length_index + 1) / float(LENGTH_SAMPLES - 1)
		for width_index in WIDTH_SAMPLES - 1:
			var u0 := lerpf(-1.0, 1.0, float(width_index) / float(WIDTH_SAMPLES - 1))
			var u1 := lerpf(-1.0, 1.0, float(width_index + 1) / float(WIDTH_SAMPLES - 1))
			var a := _blade_point(curve, length, side, t0, u0, half_width, fold_depth)
			var b := _blade_point(curve, length, side, t1, u0, half_width, fold_depth)
			var c := _blade_point(curve, length, side, t1, u1, half_width, fold_depth)
			var d := _blade_point(curve, length, side, t0, u1, half_width, fold_depth)
			_append_triangle(vertices, normals, uvs, a, b, c,
				Vector2((u0 + 1.0) * 0.5, t0), Vector2((u0 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t1))
			_append_triangle(vertices, normals, uvs, a, c, d,
				Vector2((u0 + 1.0) * 0.5, t0), Vector2((u1 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t0))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, leaf_material)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.transform = path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _blade_point(curve: Curve3D, length: float, side: Vector3, t: float,
		u: float, half_width: float, fold_depth: float) -> Vector3:
	var point: Vector3 = curve.sample_baked(length * t, true)
	var tangent := _tangent(curve, length * t, length)
	var normal := side.cross(tangent).normalized()
	if normal.dot(Vector3.UP) < 0.0:
		normal = -normal
	var envelope := pow(sin(PI * t), 0.43) * (1.0 - 0.22 * t)
	var fold := fold_depth * (1.0 - absf(u)) * sin(PI * t)
	return point + side * u * half_width * envelope + normal * fold


func _append_triangle(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, a: Vector3, b: Vector3, c: Vector3,
		uv_a: Vector2, uv_b: Vector2, uv_c: Vector2) -> void:
	var normal := (b - a).cross(c - a).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.UP
	elif normal.dot(Vector3.UP) < 0.0:
		normal = -normal
	vertices.append_array(PackedVector3Array([a, b, c]))
	normals.append_array(PackedVector3Array([normal, normal, normal]))
	uvs.append_array(PackedVector2Array([uv_a, uv_b, uv_c]))


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.05, length * 0.04)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.UP


func _leaf_side(curve: Curve3D, length: float) -> Vector3:
	var tip: Vector3 = curve.sample_baked(length, true)
	var radial := Vector3(tip.x, 0.0, tip.z).normalized()
	if radial.length_squared() < 0.5:
		radial = Vector3.FORWARD
	return Vector3(-radial.z, 0.0, radial.x)
