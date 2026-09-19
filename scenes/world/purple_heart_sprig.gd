@tool
extends Node3D

## The Path3D owns one Purple Heart stem's habit. This tool derives the
## repetitive paired lance leaves, segmented stem and optional three-petal
## flower while the source course stays directly reshapeable in the editor.

@export_range(3, 8, 1) var leaf_pair_count := 6:
	set(value):
		leaf_pair_count = clampi(value, 3, 8)
		_queue_rebuild()
@export var flowered := false:
	set(value):
		flowered = value
		_queue_rebuild()
@export_range(0.7, 1.3, 0.01) var leaf_scale := 1.0:
	set(value):
		leaf_scale = clampf(value, 0.7, 1.3)
		_queue_rebuild()
@export var stem_material: Material
@export var leaf_material: Material
@export var young_leaf_material: Material
@export var flower_material: Material
@export var flower_center_material: Material

const STEM_SAMPLES := 9
const LEAF_LENGTH_SAMPLES := 5
const LEAF_WIDTH_SAMPLES := 3

var _queued := false


func _ready() -> void:
	var course := get_node_or_null("stem_course") as Path3D
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
	var course := get_node_or_null("stem_course") as Path3D
	var stems := get_node_or_null("derived_stem") as Node3D
	var leaves := get_node_or_null("derived_leaves") as Node3D
	var flowers := get_node_or_null("derived_flowers") as Node3D
	if course == null or course.curve == null or stems == null \
			or leaves == null or flowers == null:
		return
	for parent in [stems, leaves, flowers]:
		for child in parent.get_children():
			child.free()
	var curve := course.curve
	var length := curve.get_baked_length()
	if length < 0.2:
		return
	_build_stem(curve, length, stems)
	_build_leaf_pairs(curve, length, leaves)
	if flowered:
		_build_flower(curve.sample_baked(length, true), flowers)


func _build_stem(curve: Curve3D, length: float, parent: Node3D) -> void:
	for index in STEM_SAMPLES - 1:
		var t0 := float(index) / float(STEM_SAMPLES - 1)
		var t1 := float(index + 1) / float(STEM_SAMPLES - 1)
		var a: Vector3 = curve.sample_baked(length * t0, true)
		var b: Vector3 = curve.sample_baked(length * t1, true)
		var delta := b - a
		if delta.length_squared() < 0.0001:
			continue
		var mesh := CylinderMesh.new()
		mesh.top_radius = lerpf(0.011, 0.006, t1)
		mesh.bottom_radius = lerpf(0.013, 0.007, t0)
		mesh.height = delta.length()
		# A stem is 12 to 26mm across. Seven sides, a ring and two caps buried
		# inside the neighbouring segments made 42 triangles a segment, 336 a
		# sprig, and the stems alone came to 324,000 at the arrival palms. Four
		# smooth-shaded sides and no caps is 8 a segment. 2026-09-18.
		mesh.radial_segments = 4
		mesh.rings = 0
		mesh.cap_top = false
		mesh.cap_bottom = false
		var instance := MeshInstance3D.new()
		instance.name = "segment_%02d" % index
		instance.mesh = mesh
		instance.material_override = stem_material
		instance.transform = Transform3D(
			Basis(Quaternion(Vector3.UP, delta.normalized())), (a + b) * 0.5)
		parent.add_child(instance)


func _build_leaf_pairs(curve: Curve3D, length: float, parent: Node3D) -> void:
	for pair_index in leaf_pair_count:
		var share := float(pair_index) / float(maxi(leaf_pair_count - 1, 1))
		var t := lerpf(0.17, 0.82, share)
		var origin: Vector3 = curve.sample_baked(length * t, true)
		var angle := 0.42 + float(pair_index) * 1.37
		var young := pair_index >= leaf_pair_count - 1
		for side_index in 2:
			var side_angle := angle + (PI if side_index == 1 else 0.0)
			var direction := Vector3(cos(side_angle),
				lerpf(0.07, 0.22, share), sin(side_angle)).normalized()
			var length_scale := (0.24 + 0.04 * sin(float(pair_index) * 2.1 \
				+ float(side_index))) * leaf_scale
			if young:
				length_scale *= 0.78
			var width := length_scale * (0.25 if young else 0.27)
			_add_leaf(parent, "leaf_%02d_%s" % [pair_index,
				"a" if side_index == 0 else "b"], origin, direction,
				length_scale, width, young)


func _add_leaf(parent: Node3D, node_name: String, origin: Vector3,
		direction: Vector3, length: float, half_width: float,
		young: bool) -> void:
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_leaf_arrays(origin, direction, length, half_width))
	mesh.surface_set_material(0, young_leaf_material if young else leaf_material)
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _leaf_arrays(origin: Vector3, direction: Vector3, length: float,
		half_width: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var side := Vector3.UP.cross(direction).normalized()
	if side.length_squared() < 0.5:
		side = Vector3.RIGHT
	var normal := direction.cross(side).normalized()
	if normal.dot(Vector3.UP) < 0.0:
		normal = -normal
	for length_index in LEAF_LENGTH_SAMPLES - 1:
		var t0 := float(length_index) / float(LEAF_LENGTH_SAMPLES - 1)
		var t1 := float(length_index + 1) / float(LEAF_LENGTH_SAMPLES - 1)
		for width_index in LEAF_WIDTH_SAMPLES - 1:
			var u0 := lerpf(-1.0, 1.0,
				float(width_index) / float(LEAF_WIDTH_SAMPLES - 1))
			var u1 := lerpf(-1.0, 1.0,
				float(width_index + 1) / float(LEAF_WIDTH_SAMPLES - 1))
			var a := _leaf_point(origin, direction, side, normal, length,
				half_width, t0, u0)
			var b := _leaf_point(origin, direction, side, normal, length,
				half_width, t1, u0)
			var c := _leaf_point(origin, direction, side, normal, length,
				half_width, t1, u1)
			var d := _leaf_point(origin, direction, side, normal, length,
				half_width, t0, u1)
			_append_triangle(vertices, normals, uvs, a, b, c,
				Vector2((u0 + 1.0) * 0.5, t0),
				Vector2((u0 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t1))
			_append_triangle(vertices, normals, uvs, a, c, d,
				Vector2((u0 + 1.0) * 0.5, t0),
				Vector2((u1 + 1.0) * 0.5, t1),
				Vector2((u1 + 1.0) * 0.5, t0))
	return _arrays(vertices, normals, uvs)


func _leaf_point(origin: Vector3, direction: Vector3, side: Vector3,
		normal: Vector3, length: float, half_width: float,
		t: float, u: float) -> Vector3:
	var envelope := pow(sin(PI * t), 0.62) * (1.0 - 0.12 * t)
	var arch := normal * (0.032 * sin(PI * t) - 0.025 * t * t)
	var central_fold := normal * (0.012 * (1.0 - absf(u)) * sin(PI * t))
	return origin + direction * length * t + side * half_width * u * envelope \
		+ arch + central_fold


func _build_flower(at: Vector3, parent: Node3D) -> void:
	for index in 3:
		var angle := float(index) * TAU / 3.0
		var mesh := SphereMesh.new()
		mesh.radius = 0.5
		mesh.height = 1.0
		# A petal is a 5cm flattened sphere: 6 by 2 is 36 triangles against 80.
		mesh.radial_segments = 6
		mesh.rings = 2
		var petal := MeshInstance3D.new()
		petal.name = "petal_%d" % index
		petal.mesh = mesh
		petal.material_override = flower_material
		petal.position = at + Vector3(cos(angle), 0.0, sin(angle)) * 0.026
		petal.rotation = Vector3(0.35, -angle, 0.0)
		petal.scale = Vector3(0.052, 0.016, 0.027)
		parent.add_child(petal)
	var center_mesh := SphereMesh.new()
	center_mesh.radius = 0.5
	center_mesh.height = 1.0
	center_mesh.radial_segments = 6
	center_mesh.rings = 2
	var center := MeshInstance3D.new()
	center.name = "flower_center"
	center.mesh = center_mesh
	center.material_override = flower_center_material
	center.position = at + Vector3.UP * 0.006
	center.scale = Vector3(0.021, 0.015, 0.021)
	parent.add_child(center)


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
