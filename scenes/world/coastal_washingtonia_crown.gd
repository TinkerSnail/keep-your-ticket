@tool
extends Node3D

## Tall arrival Washingtonia crown. Selectable Path3D children own the petiole
## and dry-skirt courses. The tool derives narrow, overlapping palmate fingers
## so the crown reads as one compact burst rather than separated paddle fans.

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

const FINGER_COUNT := 15
const PETIOLE_HALF_WIDTH := 0.026

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
		var extra_index := int(path.get_meta("extra_index", -1)) \
			if path != null else -1
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
	if length < 0.35:
		return
	var age := String(path.get_meta("age", "mature"))
	var material := mature_material
	if age == "new":
		material = new_growth_material
	elif age == "old":
		material = old_growth_material
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_finger_arrays(curve, length, age))
	mesh.surface_set_material(0, material)
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_petiole_arrays(curve, length))
	mesh.surface_set_material(1, midrib_material)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.transform = path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	instance.set_meta("silhouette", "washingtonia")
	instance.set_meta("fan_finger_count", FINGER_COUNT)
	parent.add_child(instance)


func _finger_arrays(curve: Curve3D, length: float, age: String) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var centre := curve.sample_baked(length, true)
	var tangent := _tangent(curve, length, length)
	var outward := Vector3(centre.x, 0.0, centre.z).normalized()
	if outward.length_squared() < 0.5:
		outward = Vector3(tangent.x, 0.0, tangent.z).normalized()
	if outward.length_squared() < 0.5:
		outward = Vector3.RIGHT
	var side := Vector3.UP.cross(outward).normalized()
	var lift := 0.42
	var spread := deg_to_rad(42.0)
	var blade_length := 0.92
	var tip_drop := 0.10
	if age == "new":
		lift = 0.72
		spread = deg_to_rad(29.0)
		blade_length = 0.76
		tip_drop = 0.01
	elif age == "old":
		lift = -0.08
		spread = deg_to_rad(37.0)
		blade_length = 0.82
		tip_drop = 0.24
	var reach := (outward * 0.82 + Vector3.UP * lift).normalized()
	for index in FINGER_COUNT:
		var across := float(index) / float(FINGER_COUNT - 1)
		var angle := lerpf(-spread, spread, across)
		var axis := (reach * cos(angle) + side * sin(angle)).normalized()
		var fan_side := (side * cos(angle) - reach * sin(angle)).normalized()
		var alternating := 0.94 + 0.06 * float(index % 2)
		var edge_taper := 1.0 - 0.13 * absf(across * 2.0 - 1.0)
		var finger_length := blade_length * alternating * edge_taper
		var root_half := 0.014
		var shoulder_half := 0.038 if age == "new" else 0.046
		var shoulder := centre + axis * finger_length * 0.58 \
			+ Vector3.UP * 0.035 * sin(across * PI)
		var tip := centre + axis * finger_length - Vector3.UP * tip_drop \
			* (0.45 + 0.55 * absf(across * 2.0 - 1.0))
		_append_triangle(vertices, normals, uvs,
			centre - fan_side * root_half,
			shoulder - fan_side * shoulder_half,
			centre + fan_side * root_half)
		_append_triangle(vertices, normals, uvs,
			centre + fan_side * root_half,
			shoulder - fan_side * shoulder_half,
			shoulder + fan_side * shoulder_half)
		_append_triangle(vertices, normals, uvs,
			shoulder - fan_side * shoulder_half,
			tip,
			shoulder + fan_side * shoulder_half)
	return _arrays(vertices, normals, uvs)


func _petiole_arrays(curve: Curve3D, length: float) -> Array:
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
		var width := lerpf(PETIOLE_HALF_WIDTH * 1.35,
			PETIOLE_HALF_WIDTH * 0.55, t)
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
		var width := lerpf(0.15, 0.025, t) \
			* (0.94 + 0.06 * sin(t * PI * 4.0))
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
	uvs.append_array(PackedVector2Array([
		Vector2(0.0, 0.0), Vector2(0.5, 0.62), Vector2(1.0, 1.0)]))


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
