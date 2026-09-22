@tool
extends Node3D

## Broad palmetto fan crown. The selectable Path3D children own the live frond
## and retained-skirt courses; this script derives their exuberant palmate
## paddles, narrow petioles and hanging dry surfaces.

@export var new_growth_material: Material
@export var mature_material: Material
@export var old_growth_material: Material
@export var midrib_material: Material
@export var skirt_material: Material
@export_range(0, 2, 1) var extra_frond_count := 0:
	set(value):
		extra_frond_count = value
		_queue_rebuild()
@export_range(14, 18, 1) var remnant_count := 16:
	set(value):
		remnant_count = value
		_queue_rebuild()

const FAN_SEGMENTS := 9
const PETIOLE_HALF_WIDTH := 0.035

var _queued := false


func _ready() -> void:
	for group_name in ["frond_courses", "skirt_courses"]:
		for child in get_node(group_name).get_children():
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
	var frond_output := get_node("derived_fronds") as Node3D
	for child in frond_output.get_children():
		child.free()
	for child in get_node("frond_courses").get_children():
		var path := child as Path3D
		var extra_index := int(path.get_meta("extra_index", -1)) if path != null else -1
		if path != null and path.curve != null \
				and (extra_index < 0 or extra_index < extra_frond_count):
			_build_frond(path, frond_output)

	var skirt_output := get_node("derived_skirt") as Node3D
	for child in skirt_output.get_children():
		child.free()
	var source_skirt := get_node("skirt_courses").get_children()
	for index in mini(remnant_count, source_skirt.size()):
		_build_skirt(source_skirt[index] as Path3D, skirt_output)


func _build_frond(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.4:
		return
	var age := String(path.get_meta("age", "mature"))
	var material := mature_material
	if age == "new":
		material = new_growth_material
	elif age == "old":
		material = old_growth_material

	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_fan_arrays(curve, length, age))
	mesh.surface_set_material(0, material)
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_petiole_arrays(curve, length, age))
	mesh.surface_set_material(1, midrib_material)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.transform = path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _build_skirt(path: Path3D, parent: Node3D) -> void:
	if path == null or path.curve == null:
		return
	var length := path.curve.get_baked_length()
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_skirt_arrays(path.curve, length))
	mesh.surface_set_material(0, skirt_material)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.transform = path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _fan_arrays(curve: Curve3D, length: float, age: String) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var base_root := curve.sample_baked(length, true)
	var base_tangent := _tangent(curve, length, length)
	var lift := 0.28 + clampf(base_tangent.y, -0.8, 0.8) * 0.34
	var radius := 0.86
	var spread := deg_to_rad(67.0)
	if age == "new":
		lift += 0.34
		radius = 0.60
		spread = deg_to_rad(48.0)
	elif age == "old":
		lift -= 0.22
		radius = 0.74
		spread = deg_to_rad(61.0)
	var variant_angles := [-0.06, 0.06] if age == "new" \
		else ([-0.11, 0.0, 0.11] if age == "mature" else [-0.075, 0.075])
	for variant_index in variant_angles.size():
		var variant_angle: float = variant_angles[variant_index]
		var tangent := base_tangent.rotated(Vector3.UP, variant_angle)
		var outward := Vector3(tangent.x, 0.0, tangent.z).normalized()
		if outward.length_squared() < 0.5:
			outward = Vector3.RIGHT
		var side := Vector3.UP.cross(outward).normalized()
		var layer_offset := (float(variant_index) \
			- float(variant_angles.size() - 1) * 0.5) * 0.17
		var reach := (outward * 0.88 + Vector3.UP * (lift + layer_offset)).normalized()
		var root := base_root.rotated(Vector3.UP, variant_angle)
		var centre := root + outward * 0.06
		var variant_radius := radius * (0.96 + 0.07 * float(variant_index))
		var step := spread * 2.0 / float(FAN_SEGMENTS)
		for index in FAN_SEGMENTS:
			# A narrow slit between wedges makes the broad blade read as a fan of
			# radiating fingers instead of one floating polygon.
			var centre_angle := -spread + (float(index) + 0.5) * step
			var a0 := centre_angle - step * 0.43
			var a1 := centre_angle + step * 0.43
			var d0 := (reach * cos(a0) + side * sin(a0)).normalized()
			var d1 := (reach * cos(a1) + side * sin(a1)).normalized()
			var r0 := variant_radius * (0.94 + 0.06 * float((index + 1) % 2))
			var r1 := variant_radius * (0.94 + 0.06 * float(index % 2))
			_append_triangle(vertices, normals, uvs, centre,
				centre + d0 * r0, centre + d1 * r1)
	return _arrays(vertices, normals, uvs)


func _petiole_arrays(curve: Curve3D, length: float, age: String) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	const SAMPLES := 9
	var variant_angles := [-0.06, 0.06] if age == "new" \
		else ([-0.11, 0.0, 0.11] if age == "mature" else [-0.075, 0.075])
	for variant_index in variant_angles.size():
		var variant_angle: float = variant_angles[variant_index]
		var vertex_base := vertices.size()
		for index in SAMPLES:
			var t := float(index) / float(SAMPLES - 1)
			var point := curve.sample_baked(length * t, true).rotated(
				Vector3.UP, variant_angle)
			point.y += (float(variant_index) \
				- float(variant_angles.size() - 1) * 0.5) * 0.08 * t
			var tangent := _tangent(curve, length * t, length).rotated(
				Vector3.UP, variant_angle)
			var side := Vector3.UP.cross(tangent).normalized()
			if side.length_squared() < 0.5:
				side = Vector3.FORWARD
			var width := lerpf(PETIOLE_HALF_WIDTH * 1.35,
				PETIOLE_HALF_WIDTH * 0.65, t)
			var normal := tangent.cross(side).normalized()
			if normal.dot(Vector3.UP) < 0.0:
				normal = -normal
			vertices.append(point - side * width)
			vertices.append(point + side * width)
			normals.append_array(PackedVector3Array([normal, normal]))
			uvs.append_array(PackedVector2Array([Vector2(0.0, t), Vector2(1.0, t)]))
			if index < SAMPLES - 1:
				var base := vertex_base + index * 2
				indices.append_array(PackedInt32Array([
					base, base + 2, base + 1,
					base + 1, base + 2, base + 3,
				]))
	var arrays := _arrays(vertices, normals, uvs)
	arrays[Mesh.ARRAY_INDEX] = indices
	return arrays


func _skirt_arrays(curve: Curve3D, length: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	const SAMPLES := 8
	for index in SAMPLES:
		var t := float(index) / float(SAMPLES - 1)
		var point := curve.sample_baked(length * t, true)
		var tangent := _tangent(curve, length * t, length)
		var side := Vector3.UP.cross(tangent).normalized()
		if side.length_squared() < 0.5:
			side = Vector3.FORWARD
		var width := lerpf(0.23, 0.035, t) * (0.92 + 0.08 * sin(t * PI * 5.0))
		var normal := tangent.cross(side).normalized()
		if normal.dot(Vector3.UP) < 0.0:
			normal = -normal
		vertices.append(point - side * width)
		vertices.append(point + side * width)
		normals.append_array(PackedVector3Array([normal, normal]))
		uvs.append_array(PackedVector2Array([Vector2(0.0, t), Vector2(1.0, t)]))
		if index < SAMPLES - 1:
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
	uvs.append_array(PackedVector2Array([Vector2(0.5, 0.0), Vector2(0.0, 1.0), Vector2(1.0, 1.0)]))


func _arrays(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array) -> Array:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	return arrays


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.10, length * 0.05)
	var before := curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after := curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.RIGHT
