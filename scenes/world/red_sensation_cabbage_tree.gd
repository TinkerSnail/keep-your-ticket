@tool
extends Node3D

## The Path3D children own this Cordyline's sword-leaf courses. This script
## derives folded, tapered blades and raised midribs from them so the three
## catalog variants remain directly reshapeable in the editor.

@export_enum("vA", "vB", "vC") var catalog_variant := 0:
	set(value):
		catalog_variant = clampi(value, 0, 2)
		_queue_rebuild()
@export var outer_material: Material
@export var mature_material: Material
@export var young_material: Material
@export var midrib_material: Material

const LENGTH_SAMPLES := 15
const WIDTH_SAMPLES := 5
const MIDRIB_HALF_WIDTH := 0.011

var _queued := false


func _ready() -> void:
	var courses := get_node_or_null("leaf_courses")
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
	var derived := get_node_or_null("derived_leaves") as Node3D
	var courses := get_node_or_null("leaf_courses") as Node3D
	if derived == null or courses == null:
		return
	for child in derived.get_children():
		child.free()
	for child in courses.get_children():
		var path := child as Path3D
		if path == null or path.curve == null \
				or int(path.get_meta("variant_min", 0)) > catalog_variant:
			continue
		_build_leaf(path, derived)


func _build_leaf(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.35:
		return
	var half_width := float(path.get_meta("half_width", 0.075))
	var fold_depth := float(path.get_meta("fold_depth", 0.026))
	var tone := int(path.get_meta("tone", 1))

	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_blade_arrays(curve, length, half_width, fold_depth))
	var blade_material := mature_material
	if tone <= 0:
		blade_material = outer_material
	elif tone >= 2:
		blade_material = young_material
	mesh.surface_set_material(0, blade_material)
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_midrib_arrays(curve, length, fold_depth))
	mesh.surface_set_material(1, midrib_material)

	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.transform = path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _blade_arrays(curve: Curve3D, length: float, half_width: float,
		fold_depth: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var side := _leaf_side(curve, length)
	for length_index in LENGTH_SAMPLES - 1:
		var t0 := float(length_index) / float(LENGTH_SAMPLES - 1)
		var t1 := float(length_index + 1) / float(LENGTH_SAMPLES - 1)
		for width_index in WIDTH_SAMPLES - 1:
			var u0 := lerpf(-1.0, 1.0,
				float(width_index) / float(WIDTH_SAMPLES - 1))
			var u1 := lerpf(-1.0, 1.0,
				float(width_index + 1) / float(WIDTH_SAMPLES - 1))
			var a := _blade_point(curve, length, side, t0, u0,
				half_width, fold_depth)
			var b := _blade_point(curve, length, side, t1, u0,
				half_width, fold_depth)
			var c := _blade_point(curve, length, side, t1, u1,
				half_width, fold_depth)
			var d := _blade_point(curve, length, side, t0, u1,
				half_width, fold_depth)
			_append_triangle(vertices, normals, uvs, a, b, c,
				Vector2((u0 + 1.0) * 0.5, t0),
				Vector2((u0 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t1))
			_append_triangle(vertices, normals, uvs, a, c, d,
				Vector2((u0 + 1.0) * 0.5, t0),
				Vector2((u1 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t0))
	return _arrays(vertices, normals, uvs)


func _blade_point(curve: Curve3D, length: float, side: Vector3, t: float,
		u: float, half_width: float, fold_depth: float) -> Vector3:
	var point: Vector3 = curve.sample_baked(length * t, true)
	var tangent := _tangent(curve, length * t, length)
	var normal := side.cross(tangent).normalized()
	if normal.dot(Vector3.UP) < 0.0:
		normal = -normal
	# Cordyline leaves are narrow straps with a strong central fold, a broad
	# shoulder near the crown and a long, sharp taper into the arching tip.
	var envelope := pow(sin(PI * t), 0.48) * (1.0 - 0.34 * t)
	var central_fold := fold_depth * (1.0 - absf(u)) * sin(PI * t)
	return point + side * u * half_width * envelope + normal * central_fold


func _midrib_arrays(curve: Curve3D, length: float, fold_depth: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	var side := _leaf_side(curve, length)
	for index in LENGTH_SAMPLES:
		var t := float(index) / float(LENGTH_SAMPLES - 1)
		var point: Vector3 = curve.sample_baked(length * t, true)
		var tangent := _tangent(curve, length * t, length)
		var normal := side.cross(tangent).normalized()
		if normal.dot(Vector3.UP) < 0.0:
			normal = -normal
		var width := MIDRIB_HALF_WIDTH * lerpf(1.0, 0.18, t)
		point += normal * (fold_depth * sin(PI * t) + 0.006)
		vertices.append(point - side * width)
		vertices.append(point + side * width)
		normals.append(normal)
		normals.append(normal)
		uvs.append(Vector2(0.0, t))
		uvs.append(Vector2(1.0, t))
		if index < LENGTH_SAMPLES - 1:
			var base := index * 2
			indices.append_array(PackedInt32Array([
				base, base + 2, base + 1,
				base + 1, base + 2, base + 3,
			]))
	var arrays := _arrays(vertices, normals, uvs)
	arrays[Mesh.ARRAY_INDEX] = indices
	return arrays


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


func _arrays(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array) -> Array:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	return arrays


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.06, length * 0.04)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.FORWARD


func _leaf_side(curve: Curve3D, length: float) -> Vector3:
	var tip: Vector3 = curve.sample_baked(length, true)
	var radial := Vector3(tip.x, 0.0, tip.z).normalized()
	if radial.length_squared() < 0.5:
		radial = Vector3.FORWARD
	return Vector3(-radial.z, 0.0, radial.x)
