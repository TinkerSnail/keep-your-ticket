@tool
extends Node3D

## The artistic courses of the fronds are the editable Path3D children in the
## source scene. This script derives only their repeated leaflet and midrib
## surfaces, so reshaping a curve in the editor updates every coastal palm.

@export var new_growth_material: Material
@export var mature_material: Material
@export var old_growth_material: Material
@export var midrib_material: Material
@export var remnant_material: Material
@export_range(0, 20, 1) var extra_frond_count := 0:
	set(value):
		extra_frond_count = value
		_queue_rebuild()
@export_range(7, 12, 1) var remnant_count := 9:
	set(value):
		remnant_count = value
		_queue_rebuild()
@export_range(1, 2, 1) var density_multiplier := 1:
	set(value):
		density_multiplier = value
		_queue_rebuild()

const LEAFLET_PAIRS := 16
const MIDRIB_HALF_WIDTH := 0.028
const MeshCache := preload("res://scripts/derived_mesh_cache.gd")

var _queued := false


func _ready() -> void:
	for group_name in ["frond_courses", "remnant_courses"]:
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
	var derived := get_node("derived_fronds") as Node3D
	for child in derived.get_children():
		child.free()
	var active_paths: Array[Path3D] = []
	for child in get_node("frond_courses").get_children():
		var path := child as Path3D
		var extra_index := int(path.get_meta("extra_index", -1)) if path != null else -1
		if path != null and path.curve != null \
				and (extra_index < 0 or extra_index < extra_frond_count):
			active_paths.append(path)
	var density_step := TAU / float(maxi(active_paths.size() * density_multiplier, 1))
	for path in active_paths:
		for density_index in density_multiplier:
			_build_frond(path, derived, density_index, density_step * density_index)
	var remnants := get_node("derived_remnants") as Node3D
	for child in remnants.get_children():
		child.free()
	var source_remnants := get_node("remnant_courses").get_children()
	for index in mini(remnant_count, source_remnants.size()):
		_build_remnant(source_remnants[index] as Path3D, remnants)


func _build_frond(path: Path3D, parent: Node3D, density_index := 0,
		density_rotation := 0.0) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.5:
		return
	var age := String(path.get_meta("age", "mature"))
	var material := mature_material
	if age == "new":
		material = new_growth_material
	elif age == "old":
		material = old_growth_material

	# Every crown placed from this scene shares its courses, so a frond is
	# built once and handed to the rest.
	var spear: bool = path.name == "new_0"
	var mesh := MeshCache.fetch(["palm_frond", MeshCache.id_of(curve), age, spear,
			MeshCache.id_of(material), MeshCache.id_of(midrib_material)],
			[curve, material, midrib_material], func() -> Mesh:
		var built := ArrayMesh.new()
		if age == "new":
			if path.name == "new_0":
				# The youngest leaf is still folded into one narrow central spear.
				built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
					_ribbon_arrays(curve, length, 0.14))
			else:
				# Its two slightly older neighbours have only begun to separate.
				built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
					_leaflet_arrays(curve, length, 0.28, 6, 0.45))
		else:
			built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
				_leaflet_arrays(curve, length, 0.84 if age == "mature" else 0.70))
		built.surface_set_material(0, material)
		built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
			_ribbon_arrays(curve, length, MIDRIB_HALF_WIDTH))
		built.surface_set_material(1, midrib_material)
		return built)

	var instance := MeshInstance3D.new()
	instance.name = path.name if density_index == 0 else \
		"%s_density_%d" % [path.name, density_index]
	instance.mesh = mesh
	# A density copy must occupy a visibly different tier, not merely lie almost
	# on top of its source course. The second shell is lifted and drawn inward,
	# filling the crown's upper volume while the authored course still owns its
	# gesture. This remains derived repetition, not a second artistic source.
	var density_scale := 1.0 if density_index == 0 else 0.86
	var density_lift := 0.0 if density_index == 0 else 0.38
	var density_basis := Basis(Vector3.UP, density_rotation).scaled(
		Vector3(density_scale, 0.92 if density_index > 0 else 1.0, density_scale))
	instance.transform = Transform3D(density_basis,
		Vector3.UP * density_lift) * path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	instance.set_meta("silhouette", "pinnate")
	instance.set_meta("density_copy", density_index)
	instance.set_meta("density_scale", density_scale)
	instance.set_meta("density_lift", density_lift)
	instance.set_meta("leaflet_pair_count",
		0 if age == "new" and path.name == "new_0" else (6 if age == "new" else LEAFLET_PAIRS))
	parent.add_child(instance)


func _build_remnant(path: Path3D, parent: Node3D) -> void:
	if path == null or path.curve == null:
		return
	var curve := path.curve
	var mesh := MeshCache.fetch(["palm_remnant", MeshCache.id_of(curve),
			MeshCache.id_of(remnant_material)], [curve, remnant_material],
			func() -> Mesh:
		var built := ArrayMesh.new()
		built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
			_remnant_arrays(curve, curve.get_baked_length()))
		built.surface_set_material(0, remnant_material)
		return built)
	var instance := MeshInstance3D.new()
	instance.name = path.name
	instance.mesh = mesh
	instance.transform = path.transform
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(instance)


func _leaflet_arrays(curve: Curve3D, length: float, half_span: float,
		pair_count: int = LEAFLET_PAIRS, droop_scale: float = 1.0) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	for index in pair_count:
		for sign_variant in [-1.0, 1.0]:
			var sign_value: float = sign_variant
			# Real pinnae alternate instead of forming exact mirrored rungs. The
			# small offset and reach variation break the generated fishbone rhythm.
			var t := clampf((float(index) + 1.0) / float(pair_count + 1) \
				+ sign_value * 0.012, 0.03, 0.97)
			var distance := length * t
			var root: Vector3 = curve.sample_baked(distance, true)
			var tangent := _tangent(curve, distance, length)
			var side := _frond_side(curve, length)
			var stagger := 0.94 if sign_value < 0.0 else 1.0
			var span := half_span * sin(PI * t) \
				* (0.94 if index % 3 == 0 else 1.0) * stagger
			# The blade advances toward the frond tip, then hangs slightly. A
			# narrow four-point lance reads as a leaflet rather than a saw tooth.
			var flutter := float((index * 5 + (0 if sign_value < 0.0 else 2)) % 4) * 0.012
			var tip: Vector3 = root + side * sign_value * span \
				+ tangent * (0.12 + 0.07 * t) \
				- Vector3.UP * (0.07 + 0.075 * t + flutter) * droop_scale
			var direction := (tip - root).normalized()
			var width_axis := Vector3.UP.cross(direction).normalized()
			if width_axis.length_squared() < 0.5:
				width_axis = tangent
			var shoulder := root.lerp(tip, 0.42)
			var half_width := 0.055 + 0.018 * sin(PI * t)
			var flank_a := shoulder + width_axis * half_width
			var flank_b := shoulder - width_axis * half_width
			_append_triangle(vertices, normals, uvs, root, flank_a, tip)
			_append_triangle(vertices, normals, uvs, root, tip, flank_b)
	return _arrays(vertices, normals, uvs)


func _ribbon_arrays(curve: Curve3D, length: float, half_width: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	var side := _frond_side(curve, length)
	var samples := LEAFLET_PAIRS + 2
	for index in samples:
		var t := float(index) / float(samples - 1)
		var point: Vector3 = curve.sample_baked(length * t, true)
		var width := half_width
		if half_width > 0.1:
			width *= maxf(0.12, sin(PI * t))
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


func _remnant_arrays(curve: Curve3D, length: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	var side := _frond_side(curve, length)
	var samples := 7
	for index in samples:
		var t := float(index) / float(samples - 1)
		var point: Vector3 = curve.sample_baked(length * t, true)
		var tangent := _tangent(curve, length * t, length)
		var width := lerpf(0.13, 0.035, t)
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
	uvs.append_array(PackedVector2Array([Vector2(0, 0), Vector2(0, 1), Vector2(1, 0.5)]))


func _arrays(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array) -> Array:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	return arrays


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.12, length * 0.04)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.RIGHT


func _frond_side(curve: Curve3D, length: float) -> Vector3:
	var tip: Vector3 = curve.sample_baked(length, true)
	var radial := Vector3(tip.x, 0.0, tip.z).normalized()
	if radial.length_squared() < 0.5:
		radial = Vector3.RIGHT
	return Vector3(-radial.z, 0.0, radial.x)
