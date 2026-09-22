@tool
extends Node3D

## The Path3D owns the gesture of one delphinium flower spike. This tool
## derives its segmented stem, palmate lower foliage and dense raceme while
## keeping the tall silhouette directly reshapeable in the editor.

@export_range(10, 28, 1) var bloom_count := 18:
	set(value):
		bloom_count = clampi(value, 10, 28)
		_queue_rebuild()
@export_range(3, 10, 1) var bud_count := 6:
	set(value):
		bud_count = clampi(value, 3, 10)
		_queue_rebuild()
@export_range(4, 9, 1) var leaf_count := 6:
	set(value):
		leaf_count = clampi(value, 4, 9)
		_queue_rebuild()
@export_range(0.75, 1.3, 0.01) var bloom_scale := 1.0:
	set(value):
		bloom_scale = clampf(value, 0.75, 1.3)
		_queue_rebuild()
@export var stem_material: Material
@export var leaf_material: Material
@export var young_leaf_material: Material
@export var petal_material: Material
@export var young_petal_material: Material
@export var flower_center_material: Material
@export var bud_material: Material

const STEM_SAMPLES := 13
const GOLDEN_ANGLE := 2.399963

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
	if length < 0.8:
		return
	_build_stem(curve, length, stems)
	_build_foliage(curve, length, leaves)
	_build_raceme(curve, length, stems, flowers)


func _build_stem(curve: Curve3D, length: float, parent: Node3D) -> void:
	for index in STEM_SAMPLES - 1:
		var t0 := float(index) / float(STEM_SAMPLES - 1)
		var t1 := float(index + 1) / float(STEM_SAMPLES - 1)
		_add_stem_segment(parent, "stem_%02d" % index,
			curve.sample_baked(length * t0, true),
			curve.sample_baked(length * t1, true),
			lerpf(0.016, 0.007, t1))


func _build_foliage(curve: Curve3D, length: float, parent: Node3D) -> void:
	var mature_vertices := PackedVector3Array()
	var mature_normals := PackedVector3Array()
	var mature_uvs := PackedVector2Array()
	var young_vertices := PackedVector3Array()
	var young_normals := PackedVector3Array()
	var young_uvs := PackedVector2Array()
	for index in leaf_count:
		var share := float(index) / float(maxi(leaf_count - 1, 1))
		var t := lerpf(0.035, 0.29, share)
		var origin: Vector3 = curve.sample_baked(length * t, true)
		var angle := 0.4 + float(index) * GOLDEN_ANGLE
		var outward := Vector3(cos(angle), lerpf(0.05, 0.18, share),
			sin(angle)).normalized()
		var size := lerpf(0.44, 0.3, share)
		var vertices := young_vertices if index >= leaf_count - 2 else mature_vertices
		var normals := young_normals if index >= leaf_count - 2 else mature_normals
		var uvs := young_uvs if index >= leaf_count - 2 else mature_uvs
		_append_palmate_leaf(vertices, normals, uvs, origin, outward, size)
	_add_surface_mesh(parent, "mature_palmate_leaves", mature_vertices,
		mature_normals, mature_uvs, leaf_material)
	_add_surface_mesh(parent, "young_palmate_leaves", young_vertices,
		young_normals, young_uvs, young_leaf_material)


func _append_palmate_leaf(vertices: PackedVector3Array,
		normals: PackedVector3Array, uvs: PackedVector2Array,
		origin: Vector3, outward: Vector3, size: float) -> void:
	var horizontal := Vector3(outward.x, 0.0, outward.z).normalized()
	if horizontal.length_squared() < 0.5:
		horizontal = Vector3.FORWARD
	var base := origin + horizontal * 0.025
	for lobe_index in 7:
		var spread := lerpf(-0.78, 0.78, float(lobe_index) / 6.0)
		var lobe_horizontal := horizontal.rotated(Vector3.UP, spread)
		var from_center := absf(float(lobe_index) - 3.0) / 3.0
		var lobe_length := size * (1.0 - 0.28 * from_center)
		var direction := (lobe_horizontal + Vector3.UP *
			lerpf(0.1, 0.24, 1.0 - from_center)).normalized()
		var side := Vector3.UP.cross(direction).normalized()
		if side.length_squared() < 0.5:
			side = Vector3.RIGHT
		var normal := direction.cross(side).normalized()
		if normal.dot(Vector3.UP) < 0.0:
			normal = -normal
		var shoulder := base + direction * lobe_length * 0.42
		var half_width := lobe_length * (0.2 if lobe_index == 3 else 0.16)
		var tip := base + direction * lobe_length + normal * lobe_length * 0.025
		var mid := shoulder + normal * lobe_length * 0.035
		_append_triangle(vertices, normals, uvs, base, mid - side * half_width,
			tip, Vector2(0.5, 0.0), Vector2(0.0, 0.45), Vector2(0.5, 1.0))
		_append_triangle(vertices, normals, uvs, base, tip,
			mid + side * half_width, Vector2(0.5, 0.0), Vector2(0.5, 1.0),
			Vector2(1.0, 0.45))


func _build_raceme(curve: Curve3D, length: float, stem_parent: Node3D,
		flower_parent: Node3D) -> void:
	var mature_vertices := PackedVector3Array()
	var mature_normals := PackedVector3Array()
	var mature_uvs := PackedVector2Array()
	var young_vertices := PackedVector3Array()
	var young_normals := PackedVector3Array()
	var young_uvs := PackedVector2Array()
	var center_vertices := PackedVector3Array()
	var center_normals := PackedVector3Array()
	var center_uvs := PackedVector2Array()
	var bud_vertices := PackedVector3Array()
	var bud_normals := PackedVector3Array()
	var bud_uvs := PackedVector2Array()
	for index in bloom_count:
		var share := float(index) / float(maxi(bloom_count - 1, 1))
		var t := lerpf(0.43, 0.9, share)
		var stem_point: Vector3 = curve.sample_baked(length * t, true)
		var angle := 0.22 + float(index) * GOLDEN_ANGLE
		var outward := Vector3(cos(angle), 0.0, sin(angle)).normalized()
		var reach := lerpf(0.072, 0.034, share) * bloom_scale
		var centre := stem_point + outward * reach
		_add_stem_segment(stem_parent, "pedicel_%02d" % index,
			stem_point, centre, lerpf(0.006, 0.0035, share))
		var scale := lerpf(0.98, 0.7, share) * bloom_scale
		if share > 0.72:
			_append_flower(young_vertices, young_normals, young_uvs,
				centre, outward, scale)
		else:
			_append_flower(mature_vertices, mature_normals, mature_uvs,
				centre, outward, scale)
		_append_octahedron(center_vertices, center_normals, center_uvs,
			centre + outward * 0.015, 0.016 * scale, 0.013 * scale)
	for index in bud_count:
		var share := float(index) / float(maxi(bud_count - 1, 1))
		var t := lerpf(0.89, 0.995, share)
		var point: Vector3 = curve.sample_baked(length * t, true)
		var angle := 1.1 + float(index) * GOLDEN_ANGLE
		var outward := Vector3(cos(angle), 0.0, sin(angle)).normalized()
		_append_octahedron(bud_vertices, bud_normals, bud_uvs,
			point + outward * lerpf(0.035, 0.012, share),
			lerpf(0.022, 0.012, share) * bloom_scale,
			lerpf(0.032, 0.019, share) * bloom_scale)
	_add_surface_mesh(flower_parent, "cobalt_petals", mature_vertices,
		mature_normals, mature_uvs, petal_material)
	_add_surface_mesh(flower_parent, "young_blue_petals", young_vertices,
		young_normals, young_uvs, young_petal_material)
	_add_surface_mesh(flower_parent, "dark_flower_centres", center_vertices,
		center_normals, center_uvs, flower_center_material)
	_add_surface_mesh(flower_parent, "blue_green_buds", bud_vertices,
		bud_normals, bud_uvs, bud_material)


func _append_flower(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, centre: Vector3, outward: Vector3,
		scale: float) -> void:
	var right := Vector3.UP.cross(outward).normalized()
	for petal_index in 5:
		var angle := float(petal_index) * TAU / 5.0 + 0.18
		var direction := (right * cos(angle) + Vector3.UP * sin(angle)).normalized()
		var side := outward.cross(direction).normalized()
		var base := centre + outward * 0.006
		var shoulder := base + direction * 0.033 * scale + outward * 0.008
		var tip := base + direction * 0.067 * scale + outward * 0.018
		var width := 0.026 * scale
		_append_triangle(vertices, normals, uvs, base,
			shoulder - side * width, tip, Vector2(0.5, 0.0),
			Vector2(0.0, 0.52), Vector2(0.5, 1.0))
		_append_triangle(vertices, normals, uvs, base, tip,
			shoulder + side * width, Vector2(0.5, 0.0),
			Vector2(0.5, 1.0), Vector2(1.0, 0.52))


func _append_octahedron(vertices: PackedVector3Array,
		normals: PackedVector3Array, uvs: PackedVector2Array,
		centre: Vector3, radius: float, height: float) -> void:
	var top := centre + Vector3.UP * height
	var bottom := centre - Vector3.UP * height
	var ring := [
		centre + Vector3.RIGHT * radius,
		centre + Vector3.FORWARD * radius,
		centre - Vector3.RIGHT * radius,
		centre - Vector3.FORWARD * radius,
	]
	for index in 4:
		var next := (index + 1) % 4
		_append_triangle(vertices, normals, uvs, top, ring[index], ring[next],
			Vector2(0.5, 1.0), Vector2(0.0, 0.4), Vector2(1.0, 0.4))
		_append_triangle(vertices, normals, uvs, bottom, ring[next], ring[index],
			Vector2(0.5, 0.0), Vector2(1.0, 0.4), Vector2(0.0, 0.4))


func _add_stem_segment(parent: Node3D, node_name: String, a: Vector3,
		b: Vector3, radius: float) -> void:
	var delta := b - a
	if delta.length_squared() < 0.00001:
		return
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius * 0.82
	mesh.bottom_radius = radius
	mesh.height = delta.length()
	mesh.radial_segments = 7
	mesh.rings = 1
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = stem_material
	instance.transform = Transform3D(
		Basis(Quaternion(Vector3.UP, delta.normalized())), (a + b) * 0.5)
	parent.add_child(instance)


func _add_surface_mesh(parent: Node3D, node_name: String,
		vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, material: Material) -> void:
	if vertices.is_empty():
		return
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
		_arrays(vertices, normals, uvs))
	mesh.surface_set_material(0, material)
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _append_triangle(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, a: Vector3, b: Vector3, c: Vector3,
		uv_a: Vector2, uv_b: Vector2, uv_c: Vector2) -> void:
	var normal := (b - a).cross(c - a).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.UP
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
