@tool
extends Node3D

## The Path3D children own the fountain gesture of this Hakone grass clump.
## Each course derives a close pair of narrow, striped blades: the course stays
## directly reshapeable while the repetitive lemon-green foliage rebuilds.

@export_enum("vA", "vB") var catalog_variant := 0:
	set(value):
		catalog_variant = clampi(value, 0, 1)
		_queue_rebuild()
@export var edge_material: Material
@export var lemon_material: Material
@export var young_edge_material: Material
@export var young_lemon_material: Material

## 9 since 2026-09-18, from 25. At 25 a 4.5cm blade was 144 triangles, the
## clumps at the arrival palms' feet came to 2.36M, 40% of the mounted world,
## and a facet bent 5 degrees from the next, finer than any player view
## resolves. Christina approved coarser blades the same day; 9 is 48 triangles.
## The stripe is three strips across the blade, not a texture, so it does not
## depend on this. Normals follow the blade instead of each facet, so the arch
## shades as one curve. `coastal_plant_catalog_test` holds the matching floor.
const LENGTH_SAMPLES := 9
const MeshCache := preload("res://scripts/derived_mesh_cache.gd")
const STRIPE_EDGE := 0.68

var _queued := false


func _ready() -> void:
	var courses := get_node_or_null("blade_courses") as Node3D
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
	var courses := get_node_or_null("blade_courses") as Node3D
	var derived := get_node_or_null("derived_blades") as Node3D
	if courses == null or derived == null:
		return
	for child in derived.get_children():
		child.free()
	for child in courses.get_children():
		var path := child as Path3D
		if path == null or path.curve == null \
				or int(path.get_meta("variant_min", 0)) > catalog_variant:
			continue
		_build_course(path, derived)


func _build_course(path: Path3D, parent: Node3D) -> void:
	var curve := path.curve
	var length := curve.get_baked_length()
	if length < 0.25:
		return
	var half_width := float(path.get_meta("half_width", 0.027)) * 0.78
	var fold_depth := float(path.get_meta("fold_depth", 0.012))
	var copies := int(path.get_meta("blade_copies", 3))
	var spread := float(path.get_meta("copy_spread", half_width * 0.9))
	var young := bool(path.get_meta("young", false))
	for copy_index in copies:
		var share := float(copy_index) / float(maxi(copies - 1, 1))
		var offset := lerpf(-spread, spread, share)
		var length_scale := 1.0 - 0.04 * float(copy_index)
		var sway := (0.012 if copy_index % 2 == 0 else -0.014) \
			* float(1 + int(path.get_meta("rhythm", 0)) % 3)
		var edge := young_edge_material if young else edge_material
		var lemon := young_lemon_material if young else lemon_material
		# Every clump placed from this scene shares its courses, so the blade
		# is built once for the first and handed to the rest.
		var mesh := MeshCache.fetch(["hakone_blade", LENGTH_SAMPLES,
				MeshCache.id_of(curve), half_width, fold_depth, offset,
				length_scale, sway, MeshCache.id_of(edge), MeshCache.id_of(lemon)],
				[curve, edge, lemon], func() -> Mesh:
			var built := ArrayMesh.new()
			built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
				_edge_arrays(curve, length, half_width, fold_depth,
					offset, length_scale, sway))
			built.surface_set_material(0, edge)
			built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,
				_band_arrays(curve, length, half_width, fold_depth,
					-STRIPE_EDGE, STRIPE_EDGE, offset, length_scale, sway))
			built.surface_set_material(1, lemon)
			return built)
		var instance := MeshInstance3D.new()
		instance.name = "%s_blade_%d" % [path.name, copy_index]
		instance.mesh = mesh
		instance.transform = path.transform
		instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		parent.add_child(instance)


func _edge_arrays(curve: Curve3D, length: float, half_width: float,
		fold_depth: float, copy_offset: float, length_scale: float,
		sway: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	_append_band(vertices, normals, uvs, curve, length, half_width,
		fold_depth, -1.0, -STRIPE_EDGE, copy_offset, length_scale, sway)
	_append_band(vertices, normals, uvs, curve, length, half_width,
		fold_depth, STRIPE_EDGE, 1.0, copy_offset, length_scale, sway)
	return _arrays(vertices, normals, uvs)


func _band_arrays(curve: Curve3D, length: float, half_width: float,
		fold_depth: float, u_start: float, u_end: float, copy_offset: float,
		length_scale: float, sway: float) -> Array:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	_append_band(vertices, normals, uvs, curve, length, half_width,
		fold_depth, u_start, u_end, copy_offset, length_scale, sway)
	return _arrays(vertices, normals, uvs)


func _append_band(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, curve: Curve3D, length: float,
		half_width: float, fold_depth: float, u_start: float, u_end: float,
		copy_offset: float, length_scale: float, sway: float) -> void:
	var side := _blade_side(curve, length)
	for index in LENGTH_SAMPLES - 1:
		var t0 := float(index) / float(LENGTH_SAMPLES - 1)
		var t1 := float(index + 1) / float(LENGTH_SAMPLES - 1)
		var a := _blade_point(curve, length, side, t0, u_start,
			half_width, fold_depth, copy_offset, length_scale, sway)
		var b := _blade_point(curve, length, side, t1, u_start,
			half_width, fold_depth, copy_offset, length_scale, sway)
		var c := _blade_point(curve, length, side, t1, u_end,
			half_width, fold_depth, copy_offset, length_scale, sway)
		var d := _blade_point(curve, length, side, t0, u_end,
			half_width, fold_depth, copy_offset, length_scale, sway)
		var n0 := _blade_normal(curve, length, side, t0, length_scale)
		var n1 := _blade_normal(curve, length, side, t1, length_scale)
		vertices.append_array(PackedVector3Array([a, b, c, a, c, d]))
		normals.append_array(PackedVector3Array([n0, n1, n1, n0, n1, n0]))
		uvs.append_array(PackedVector2Array([
			Vector2((u_start + 1.0) * 0.5, t0),
			Vector2((u_start + 1.0) * 0.5, t1),
			Vector2((u_end + 1.0) * 0.5, t1),
			Vector2((u_start + 1.0) * 0.5, t0),
			Vector2((u_end + 1.0) * 0.5, t1),
			Vector2((u_end + 1.0) * 0.5, t0)]))


## The blade's own upward normal at a station, the one `_blade_point` folds
## along, so neighbouring facets share it and the arch shades without steps.
func _blade_normal(curve: Curve3D, length: float, side: Vector3, t: float,
		length_scale: float) -> Vector3:
	var tangent := _tangent(curve, length * t * length_scale, length)
	var normal := side.cross(tangent).normalized()
	if normal.length_squared() < 0.5:
		return Vector3.UP
	return normal if normal.dot(Vector3.UP) >= 0.0 else -normal


func _blade_point(curve: Curve3D, length: float, side: Vector3, t: float,
		u: float, half_width: float, fold_depth: float, copy_offset: float,
		length_scale: float, sway: float) -> Vector3:
	var distance := length * t * length_scale
	var point: Vector3 = curve.sample_baked(distance, true)
	var tangent := _tangent(curve, distance, length)
	var normal := side.cross(tangent).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.UP
	elif normal.dot(Vector3.UP) < 0.0:
		normal = -normal
	# Hakone blades hold most of their width through the arch, then finish in a
	# fine point. The broad lemon stripe is the clump's readable color identity.
	var shoulder := lerpf(0.52, 1.0, smoothstep(0.0, 0.18, t))
	var taper := pow(maxf(0.0, 1.0 - t), 0.24)
	var envelope := shoulder * taper
	var lateral := copy_offset * (0.25 + 0.75 * t) \
		+ sway * sin(PI * t) * t
	var central_fold := fold_depth * (1.0 - absf(u)) * sin(PI * t)
	return point + side * (lateral + u * half_width * envelope) \
		+ normal * central_fold


func _arrays(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array) -> Array:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	return arrays


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.035, length * 0.045)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.FORWARD


func _blade_side(curve: Curve3D, length: float) -> Vector3:
	var tip: Vector3 = curve.sample_baked(length, true)
	var radial := Vector3(tip.x, 0.0, tip.z).normalized()
	if radial.length_squared() < 0.5:
		radial = Vector3.FORWARD
	return Vector3(-radial.z, 0.0, radial.x)
