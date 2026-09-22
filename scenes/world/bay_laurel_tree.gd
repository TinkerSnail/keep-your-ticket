@tool
extends Node3D

## The Path3D children under branch_courses own the laurel's silhouette. This
## script derives only repetitive twigs and leaves from those editable paths.

@export var bark_material: Material
@export var leaf_material: Material
@export var show_trunk := true
@export_range(0.08, 0.24, 0.01) var leaf_spacing := 0.11:
	set(value):
		leaf_spacing = value
		_queue_rebuild()
@export_range(0.22, 0.48, 0.01) var leaf_length := 0.38:
	set(value):
		leaf_length = value
		_queue_rebuild()
@export_range(0.045, 0.14, 0.005) var leaf_half_width := 0.09:
	set(value):
		leaf_half_width = value
		_queue_rebuild()

const BRANCH_RINGS := 11
const BRANCH_SIDES := 6
const LEAF_COLORS := [
	Color(0.055, 0.19, 0.065, 1.0),
	Color(0.075, 0.255, 0.075, 1.0),
	Color(0.12, 0.34, 0.085, 1.0),
	Color(0.20, 0.42, 0.10, 1.0),
]

var _queued := false


func _ready() -> void:
	var trunk := get_node_or_null("trunk") as GeometryInstance3D
	if trunk != null:
		trunk.visible = show_trunk
	var trunk_collision := get_node_or_null("collision/trunk") as CollisionShape3D
	if trunk_collision != null:
		trunk_collision.disabled = not show_trunk
	# Runtime only needs one build. Curve-change connections belong in the
	# editor; connecting them during capture can retrigger as bake caches settle.
	if Engine.is_editor_hint():
		for child in get_node("branch_courses").get_children():
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
	var branch_parent := get_node("derived_branches") as Node3D
	var leaf_parent := get_node("derived_leaves") as Node3D
	for child in branch_parent.get_children():
		child.free()
	for child in leaf_parent.get_children():
		child.free()
	for child in get_node("branch_courses").get_children():
		var path := child as Path3D
		if path == null or path.curve == null:
			continue
		_build_branch(path, branch_parent)
		_build_leaf_spray(path, leaf_parent)


func _build_branch(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.25:
		return
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	for ring in BRANCH_RINGS:
		var t := float(ring) / float(BRANCH_RINGS - 1)
		var distance := length * t
		var centre: Vector3 = path.transform * curve.sample_baked(distance, true)
		var tangent := (path.transform.basis * _tangent(curve, distance, length)).normalized()
		var side := _frame_side(tangent)
		var forward := tangent.cross(side).normalized()
		var radius := lerpf(0.035, 0.008, t)
		for side_index in BRANCH_SIDES:
			var angle := TAU * float(side_index) / float(BRANCH_SIDES)
			var radial := side * cos(angle) + forward * sin(angle)
			vertices.append(centre + radial * radius)
			normals.append(radial)
			uvs.append(Vector2(float(side_index) / float(BRANCH_SIDES), t))
		if ring < BRANCH_RINGS - 1:
			for side_index in BRANCH_SIDES:
				var next_side := (side_index + 1) % BRANCH_SIDES
				var a := ring * BRANCH_SIDES + side_index
				var b := ring * BRANCH_SIDES + next_side
				var c := (ring + 1) * BRANCH_SIDES + side_index
				var d := (ring + 1) * BRANCH_SIDES + next_side
				indices.append_array(PackedInt32Array([a, c, b, b, c, d]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, bark_material)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _build_leaf_spray(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.35:
		return
	var seed := int(path.get_meta("seed", 0))
	var pair_count := maxi(5, int(floor(length / leaf_spacing)))
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var colors := PackedColorArray()
	var uvs := PackedVector2Array()
	for index in pair_count:
		var t := lerpf(0.14, 0.98, float(index) / float(maxi(1, pair_count - 1)))
		var distance := length * t
		var point: Vector3 = path.transform * curve.sample_baked(distance, true)
		var tangent := (path.transform.basis * _tangent(curve, distance, length)).normalized()
		var frame_side := _frame_side(tangent)
		var phase := deg_to_rad(float((index * 137 + seed * 47) % 360))
		for pair_side in [-1.0, 1.0]:
			for cluster_twist_value in [-0.24, 0.24]:
				var cluster_twist: float = cluster_twist_value
				var azimuth := phase + (0.0 if pair_side < 0.0 else PI) + cluster_twist
				var radial := (Basis(tangent, azimuth) * frame_side).normalized()
				var lift := 0.14 + 0.12 * sin(float(index + seed) * 1.7 + cluster_twist)
				var direction := (radial * 0.92 + tangent * 0.25 + Vector3.UP * lift).normalized()
				var size_variation := 0.9 + 0.16 * float((index * 3 + seed) % 5) / 4.0
				var color_index := index + seed + (0 if pair_side < 0.0 else 2) \
					+ (0 if cluster_twist < 0.0 else 1)
				var color: Color = LEAF_COLORS[color_index % LEAF_COLORS.size()]
				var leaf_root := point + tangent * cluster_twist * 0.09
				_append_leaf(vertices, normals, colors, uvs, leaf_root, direction,
					leaf_length * size_variation, leaf_half_width * size_variation, color)
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
	var shoulder := root + direction * length * 0.46
	var tip := root + direction * length
	var left := shoulder + width_axis * half_width
	var right := shoulder - width_axis * half_width
	var normal := (left - root).cross(tip - root).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.UP
	vertices.append_array(PackedVector3Array([root, left, tip, root, tip, right]))
	normals.append_array(PackedVector3Array([normal, normal, normal, normal, normal, normal]))
	colors.append_array(PackedColorArray([color, color, color, color, color, color]))
	uvs.append_array(PackedVector2Array([
		Vector2(0.5, 1), Vector2(0, 0.48), Vector2(0.5, 0),
		Vector2(0.5, 1), Vector2(0.5, 0), Vector2(1, 0.48),
	]))


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.1, length * 0.04)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.UP


func _frame_side(tangent: Vector3) -> Vector3:
	var side := tangent.cross(Vector3.UP).normalized()
	if side.length_squared() < 0.5:
		side = tangent.cross(Vector3.FORWARD).normalized()
	return side if side.length_squared() > 0.5 else Vector3.RIGHT
