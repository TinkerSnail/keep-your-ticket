@tool
extends Node3D

## The seven Path3D children own this small fern's fan and arch. This script
## only turns those editable courses into a fine rachis and paired pinnae, the
## same source/derived relationship used by the coastal palm crowns.

@export var mature_material: Material
@export var young_material: Material
@export var rachis_material: Material
@export_range(9, 14, 1) var pinnae_pairs := 11:
	set(value):
		pinnae_pairs = value
		_queue_rebuild()

const RACHIS_HALF_WIDTH := 0.007
const MeshCache := preload("res://scripts/derived_mesh_cache.gd")

var _queued := false


func _ready() -> void:
	for child in get_node("frond_courses").get_children():
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
	var derived := get_node("derived_fronds") as Node3D
	for child in derived.get_children():
		child.free()
	for child in get_node("frond_courses").get_children():
		var path := child as Path3D
		if path != null and path.curve != null:
			_build_frond(path, derived)


func _build_frond(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.25:
		return
	var half_span := float(path.get_meta("half_span", 0.15))
	var leaf := young_material if bool(path.get_meta("young", false)) \
		else mature_material
	# Built once for the first placement of this course and shared after.
	var mesh := MeshCache.fetch(["fern_frond", MeshCache.id_of(curve), half_span,
			pinnae_pairs, MeshCache.id_of(leaf), MeshCache.id_of(rachis_material)],
			[curve, leaf, rachis_material], func() -> Mesh:
		var built := ArrayMesh.new()
		built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
			_pinnae_arrays(curve, length, half_span))
		built.surface_set_material(0, leaf)
		built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
			_rachis_arrays(curve, length))
		built.surface_set_material(1, rachis_material)
		return built)

	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.transform = path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _pinnae_arrays(curve: Curve3D, length: float, half_span: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var side := _frond_side(curve, length)
	for index in pinnae_pairs:
		for sign_variant in [-1.0, 1.0]:
			var sign_value: float = sign_variant
			# Fern pinnae form a close, alternating fishbone. Their tiny forward
			# cant follows the rachis instead of producing the palm's long teeth.
			var t := clampf((float(index) + 0.9) / float(pinnae_pairs + 0.9) \
				+ sign_value * 0.009, 0.05, 0.96)
			var distance := length * t
			var root: Vector3 = curve.sample_baked(distance, true)
			var tangent := _tangent(curve, distance, length)
			var envelope := pow(sin(PI * t), 0.68) * (1.0 - 0.26 * t)
			var rhythm := 0.94 if (index + (0 if sign_value < 0.0 else 1)) % 3 == 0 else 1.0
			var span := half_span * envelope * rhythm
			var tip := root + side * sign_value * span \
				+ tangent * (0.018 + 0.014 * t) \
				- Vector3.UP * (0.008 + 0.012 * t)
			var shoulder := root.lerp(tip, 0.42)
			var half_width := (0.014 + 0.006 * sin(PI * t)) \
				* (0.88 if index % 4 == 0 else 1.0)
			var flank_a := shoulder + tangent * half_width
			var flank_b := shoulder - tangent * half_width
			_append_triangle(vertices, normals, uvs, root, flank_a, tip)
			_append_triangle(vertices, normals, uvs, root, tip, flank_b)
	return _arrays(vertices, normals, uvs)


func _rachis_arrays(curve: Curve3D, length: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	var side := _frond_side(curve, length)
	# The rachis is a 14mm ribbon; a station every other pinna pair keeps it
	# within a few millimetres of the pinna roots at half the triangles.
	var samples := pinnae_pairs / 2 + 3
	for index in samples:
		var t := float(index) / float(samples - 1)
		var point: Vector3 = curve.sample_baked(length * t, true)
		var width := RACHIS_HALF_WIDTH * lerpf(1.0, 0.28, t)
		var tangent := _tangent(curve, length * t, length)
		var normal := side.cross(tangent).normalized()
		if normal.length_squared() < 0.5:
			normal = Vector3.UP
		vertices.append(point - side * width)
		vertices.append(point + side * width)
		normals.append(normal)
		normals.append(normal)
		uvs.append(Vector2(0.0, t))
		uvs.append(Vector2(1.0, t))
		if index < samples - 1:
			var base := index * 2
			indices.append_array(PackedInt32Array([
				base, base + 2, base + 1,
				base + 1, base + 2, base + 3,
			]))
	var arrays := _arrays(vertices, normals, uvs)
	arrays[Mesh.ARRAY_INDEX] = indices
	return arrays


func _append_triangle(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, a: Vector3, b: Vector3, c: Vector3) -> void:
	var normal := (b - a).cross(c - a).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.UP
	elif normal.dot(Vector3.UP) < 0.0:
		normal = -normal
	vertices.append_array(PackedVector3Array([a, b, c]))
	normals.append_array(PackedVector3Array([normal, normal, normal]))
	uvs.append_array(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(0.0, 1.0), Vector2(1.0, 0.5)]))


func _arrays(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array) -> Array:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	return arrays


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.035, length * 0.055)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.FORWARD


func _frond_side(curve: Curve3D, length: float) -> Vector3:
	var tip: Vector3 = curve.sample_baked(length, true)
	var radial := Vector3(tip.x, 0.0, tip.z).normalized()
	if radial.length_squared() < 0.5:
		radial = Vector3.FORWARD
	return Vector3(-radial.z, 0.0, radial.x)
