@tool
extends Node3D

## Derives a continuous soil ribbon and repetitive lush planting from four
## directly editor-owned curb courses. Move those Path3D points to reshape the
## beds; the script owns only the repeated surface and module spacing.

@export var module_scene: PackedScene
@export var soil_material: Material
@export_range(1.0, 4.0, 0.1) var bed_width := 1.9
@export_range(2.0, 6.0, 0.1) var module_spacing := 2.6

const StaticMerge := preload("res://scripts/static_merge.gd")

var _queued := false


func _ready() -> void:
	var courses := get_node_or_null("bed_courses") as Node3D
	if courses != null:
		for candidate in courses.get_children():
			var course := candidate as Path3D
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
	var courses := get_node_or_null("bed_courses") as Node3D
	var beds := get_node_or_null("derived_beds") as Node3D
	var modules := get_node_or_null("derived_modules") as Node3D
	if courses == null or beds == null or modules == null \
			or module_scene == null or soil_material == null:
		return
	for child in beds.get_children():
		child.free()
	for child in modules.get_children():
		child.free()
	for candidate in courses.get_children():
		var course := candidate as Path3D
		if course == null or course.curve == null or course.curve.point_count < 2:
			continue
		var bed := MeshInstance3D.new()
		bed.name = String(course.name) + "_soil"
		bed.mesh = _bed_ribbon(course.curve)
		bed.material_override = soil_material
		bed.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		beds.add_child(bed)
		var length := course.curve.get_baked_length()
		var station := module_spacing * 0.5
		var module_index := 0
		while station <= length - module_spacing * 0.5 + 0.001:
			var before := course.curve.sample_baked(maxf(0.0, station - 0.1))
			var after := course.curve.sample_baked(minf(length, station + 0.1))
			var tangent := (after - before).normalized()
			var across := Vector3(tangent.z, 0.0, -tangent.x).normalized()
			var module := module_scene.instantiate() as Node3D
			module.name = "%s_%02d" % [course.name, module_index]
			modules.add_child(module)
			# A small deterministic four-beat breaks the repeated circular read while
			# leaving the authored course, planting width and open thresholds intact.
			var variation := module_index % 4
			var across_offsets := [-0.12, 0.05, 0.14, -0.04]
			var angle_offsets := [-0.055, 0.035, 0.07, -0.025]
			var scales := [0.98, 1.02, 0.96, 1.01]
			module.position = course.curve.sample_baked(station) \
				+ across * across_offsets[variation]
			module.rotation.y = atan2(tangent.x, tangent.z) + angle_offsets[variation]
			module.scale = Vector3.ONE * scales[variation]
			module.set_meta("bed_variation", variation)
			station += module_spacing
			module_index += 1
	# In the running game only: each planting module draws as one mesh. The
	# plant-by-plant sources stay in the tree, hidden; the editor never merges.
	StaticMerge.merge_children_later(self, [modules, get_node_or_null("purple_heart_accents")])


func _bed_ribbon(curve: Curve3D) -> ArrayMesh:
	var length := curve.get_baked_length()
	var steps := maxi(2, int(ceil(length / 0.75)) + 1)
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var indices := PackedInt32Array()
	for index in steps:
		var station := length * float(index) / float(steps - 1)
		var before := curve.sample_baked(maxf(0.0, station - 0.1))
		var after := curve.sample_baked(minf(length, station + 0.1))
		var tangent := (after - before).normalized()
		var across := Vector3(tangent.z, 0.0, -tangent.x).normalized()
		var centre := curve.sample_baked(station) + Vector3.UP * 0.025
		vertices.append(centre - across * bed_width * 0.5)
		vertices.append(centre + across * bed_width * 0.5)
		normals.append(Vector3.UP)
		normals.append(Vector3.UP)
		if index > 0:
			var current := index * 2
			indices.append_array(PackedInt32Array([
				current - 2, current - 1, current,
				current, current - 1, current + 1,
			]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh
