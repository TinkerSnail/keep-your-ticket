@tool
extends Node3D

## The selectable Path3D courses own this coast live oak's low-forking trunk
## and broad crown. This script derives only tapered bark tubes and repetitive
## leathery leaves; there are no sphere or capsule canopy masses.

@export var bark_material: Material
@export var twig_material: Material
@export var leaf_material: Material
@export_range(0.1, 0.28, 0.01) var leaf_spacing := 0.15:
	set(value):
		leaf_spacing = value
		_queue_rebuild()
@export_range(0.28, 0.58, 0.01) var leaf_length := 0.38:
	set(value):
		leaf_length = value
		_queue_rebuild()
@export_range(0.1, 0.24, 0.005) var leaf_half_width := 0.15:
	set(value):
		leaf_half_width = value
		_queue_rebuild()

const WOOD_SIDES := 8
const WOOD_RINGS := 15
const LEAF_COLORS := [
	Color(0.035, 0.11, 0.045, 1.0),
	Color(0.05, 0.16, 0.055, 1.0),
	Color(0.075, 0.215, 0.07, 1.0),
	Color(0.12, 0.285, 0.09, 1.0),
]

var _queued := false


func _ready() -> void:
	if Engine.is_editor_hint():
		for group_name in [&"trunk_courses", &"branch_courses"]:
			var group := get_node_or_null(NodePath(String(group_name)))
			if group == null:
				continue
			for child in group.get_children():
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
	var wood_parent := get_node("derived_wood") as Node3D
	var leaf_parent := get_node("derived_leaves") as Node3D
	for child in wood_parent.get_children():
		child.free()
	for child in leaf_parent.get_children():
		child.free()
	for child in get_node("trunk_courses").get_children():
		var path := child as Path3D
		if path == null or path.curve == null:
			continue
		_build_wood(path, wood_parent, bark_material,
			float(path.get_meta("base_radius", 0.34)),
			float(path.get_meta("tip_radius", 0.13)))
	for child in get_node("branch_courses").get_children():
		var path := child as Path3D
		if path == null or path.curve == null:
			continue
		_build_wood(path, wood_parent, twig_material,
			float(path.get_meta("base_radius", 0.12)),
			float(path.get_meta("tip_radius", 0.025)))
		_build_leaf_spray(path, leaf_parent)


func _build_wood(path: Path3D, parent: Node3D, material: Material,
		base_radius: float, tip_radius: float) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.3:
		return
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	for ring in WOOD_RINGS:
		var t := float(ring) / float(WOOD_RINGS - 1)
		var distance := length * t
		var centre: Vector3 = path.transform * curve.sample_baked(distance, true)
		var tangent := (path.transform.basis * _tangent(curve, distance, length)).normalized()
		var side := _frame_side(tangent)
		var forward := tangent.cross(side).normalized()
		var radius := lerpf(base_radius, tip_radius, pow(t, 0.72))
		for side_index in WOOD_SIDES:
			var angle := TAU * float(side_index) / float(WOOD_SIDES)
			var radial := side * cos(angle) + forward * sin(angle)
			vertices.append(centre + radial * radius)
			normals.append(radial)
			uvs.append(Vector2(float(side_index) / float(WOOD_SIDES), t))
		if ring < WOOD_RINGS - 1:
			for side_index in WOOD_SIDES:
				var next_side := (side_index + 1) % WOOD_SIDES
				var a := ring * WOOD_SIDES + side_index
				var b := ring * WOOD_SIDES + next_side
				var c := (ring + 1) * WOOD_SIDES + side_index
				var d := (ring + 1) * WOOD_SIDES + next_side
				indices.append_array(PackedInt32Array([a, c, b, b, c, d]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, material)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _build_leaf_spray(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.5:
		return
	var seed := int(path.get_meta("seed", 0))
	var samples := maxi(6, int(floor(length / leaf_spacing)))
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var colors := PackedColorArray()
	var uvs := PackedVector2Array()
	for index in samples:
		var t := lerpf(0.22, 1.0, float(index) / float(maxi(1, samples - 1)))
		var distance := length * t
		var point: Vector3 = path.transform * curve.sample_baked(distance, true)
		var tangent := (path.transform.basis * _tangent(curve, distance, length)).normalized()
		var frame_side := _frame_side(tangent)
		var phase := deg_to_rad(float((index * 137 + seed * 53) % 360))
		for spoke in 10:
			var turn := fposmod(float(spoke) * 0.6180339 + float(seed) * 0.117
				+ float(index) * 0.071, 1.0)
			var azimuth := phase + TAU * turn
			var radial := (Basis(tangent, azimuth) * frame_side).normalized()
			var radial_offset := 0.12 + 0.46 \
				* float((spoke * 3 + index + seed) % 7) / 6.0
			var vertical_offset := (float((spoke * 5 + index * 3 + seed) % 9)
				/ 8.0 - 0.5) * 0.54
			var tangent_offset := (float((spoke * 7 + index + seed * 2) % 7)
				/ 6.0 - 0.5) * 0.38
			var lift := 0.12 + 0.16 * sin(float(index * 2 + spoke + seed))
			var direction := (radial * 0.58 + tangent * 0.3 + Vector3.UP * lift).normalized()
			var size := 0.88 + 0.16 * float((index + spoke * 2 + seed) % 5) / 4.0
			var color: Color = LEAF_COLORS[(index + spoke + seed) % LEAF_COLORS.size()]
			_append_leaf(vertices, normals, colors, uvs,
				point + radial * radial_offset + Vector3.UP * vertical_offset
					+ tangent * tangent_offset,
				direction, leaf_length * size, leaf_half_width * size, color)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, leaf_material)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _append_leaf(vertices: PackedVector3Array, normals: PackedVector3Array,
		colors: PackedColorArray, uvs: PackedVector2Array, root: Vector3,
		direction: Vector3, length: float, half_width: float, color: Color) -> void:
	var width_axis := Vector3.UP.cross(direction).normalized()
	if width_axis.length_squared() < 0.5:
		width_axis = Vector3.RIGHT
	var centre := root + direction * length * 0.5
	var tip := root + direction * length
	var left_low := root + direction * length * 0.28 + width_axis * half_width * 0.82
	var left_high := root + direction * length * 0.62 + width_axis * half_width
	var right_low := root + direction * length * 0.28 - width_axis * half_width * 0.82
	var right_high := root + direction * length * 0.62 - width_axis * half_width
	var normal := width_axis.cross(direction).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.UP
	# Six small triangles give the evergreen oak leaf a compact, slightly
	# scalloped outline rather than the laurel's long spear shape.
	var points := [root, left_low, left_high, tip, right_high, right_low]
	for edge in 6:
		var a: Vector3 = points[edge]
		var b: Vector3 = points[(edge + 1) % 6]
		vertices.append_array(PackedVector3Array([centre, a, b]))
		normals.append_array(PackedVector3Array([normal, normal, normal]))
		colors.append_array(PackedColorArray([color, color, color]))
		uvs.append_array(PackedVector2Array([Vector2(0.5, 0.5), Vector2(0, 1), Vector2(1, 1)]))


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.12, length * 0.04)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.UP


func _frame_side(tangent: Vector3) -> Vector3:
	var side := tangent.cross(Vector3.UP).normalized()
	if side.length_squared() < 0.5:
		side = tangent.cross(Vector3.FORWARD).normalized()
	return side if side.length_squared() > 0.5 else Vector3.RIGHT
