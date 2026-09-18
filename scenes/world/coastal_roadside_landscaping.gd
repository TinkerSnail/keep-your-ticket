@tool
extends Node3D

## Derives visual-only low curbs, soil ribbons and repeated planting from
## directly editor-owned Path3D courses. The courses are the artistic road-edge
## source: reshape them in the editor; this script only builds their finish.

@export var module_scene: PackedScene
@export var soil_material: Material
@export var curb_material: Material
@export_range(2.0, 5.0, 0.1) var bed_width := 3.9
@export_range(0.12, 0.3, 0.01) var curb_width := 0.24
@export_range(0.08, 0.24, 0.01) var curb_height := 0.16
@export_range(2.5, 6.0, 0.1) var module_spacing := 4.0

const StaticMerge := preload("res://scripts/static_merge.gd")

var _queued := false


func _ready() -> void:
	var courses := get_node_or_null("edge_courses") as Node3D
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
	var courses := get_node_or_null("edge_courses") as Node3D
	var curbs := get_node_or_null("derived_curbs") as Node3D
	var beds := get_node_or_null("derived_beds") as Node3D
	var modules := get_node_or_null("derived_modules") as Node3D
	if courses == null or curbs == null or beds == null or modules == null \
			or module_scene == null or soil_material == null or curb_material == null:
		return
	for output in [curbs, beds, modules]:
		for child in output.get_children():
			child.free()
	for candidate in courses.get_children():
		var course := candidate as Path3D
		if course == null or course.curve == null or course.curve.point_count < 2:
			continue
		var outward_side := signi(int(course.get_meta("outward_side", 1)))
		if outward_side == 0:
			outward_side = 1
		var curb := MeshInstance3D.new()
		curb.name = String(course.name) + "_low_curb"
		curb.mesh = _curb_ribbon(course.curve)
		curb.material_override = curb_material
		curb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		curb.set_meta("curb_height", curb_height)
		curbs.add_child(curb)

		var bed := MeshInstance3D.new()
		bed.name = String(course.name) + "_linear_bed"
		bed.mesh = _bed_ribbon(course.curve, outward_side)
		bed.material_override = soil_material
		bed.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		bed.set_meta("bed_width", bed_width)
		beds.add_child(bed)

		var length := course.curve.get_baked_length()
		var station := module_spacing * 0.5
		var module_index := 0
		while station <= length - module_spacing * 0.5 + 0.001:
			var before := course.curve.sample_baked(maxf(0.0, station - 0.1))
			var after := course.curve.sample_baked(minf(length, station + 0.1))
			var tangent := (after - before).normalized()
			var across := Vector3(tangent.z, 0.0, -tangent.x).normalized() \
				* float(outward_side)
			var module := module_scene.instantiate() as Node3D
			module.name = "%s_%02d" % [course.name, module_index]
			modules.add_child(module)
			var variation := module_index % 4
			var across_offsets := [-0.16, 0.08, 0.18, -0.05]
			var angle_offsets := [-0.06, 0.035, 0.07, -0.025]
			var scales := [0.96, 1.02, 0.98, 1.0]
			module.position = course.curve.sample_baked(station) \
				+ across * (curb_width * 0.5 + bed_width * 0.5 \
				+ across_offsets[variation]) + Vector3.UP * 0.025
			module.rotation.y = atan2(tangent.x, tangent.z) \
				+ (PI if outward_side < 0 else 0.0) + angle_offsets[variation]
			module.scale = Vector3.ONE * scales[variation]
			module.set_meta("roadside_variation", variation)
			station += module_spacing
			module_index += 1
	# In the running game only: each planting module draws as one mesh. The
	# plant-by-plant sources stay in the tree, hidden; the editor never merges.
	StaticMerge.merge_children_later(self, [modules])


func _bed_ribbon(curve: Curve3D, outward_side: int) -> ArrayMesh:
	var length := curve.get_baked_length()
	var steps := maxi(2, int(ceil(length / 0.75)) + 1)
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var indices := PackedInt32Array()
	for index in steps:
		var station := length * float(index) / float(steps - 1)
		var tangent := _tangent_at(curve, station, length)
		var across := Vector3(tangent.z, 0.0, -tangent.x).normalized() \
			* float(outward_side)
		var curb_edge := curve.sample_baked(station) \
			+ across * curb_width * 0.5 + Vector3.UP * 0.018
		vertices.append(curb_edge)
		vertices.append(curb_edge + across * bed_width)
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


func _curb_ribbon(curve: Curve3D) -> ArrayMesh:
	var length := curve.get_baked_length()
	var steps := maxi(2, int(ceil(length / 0.75)) + 1)
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for index in steps - 1:
		var station_a := length * float(index) / float(steps - 1)
		var station_b := length * float(index + 1) / float(steps - 1)
		var point_a := curve.sample_baked(station_a)
		var point_b := curve.sample_baked(station_b)
		var tangent_a := _tangent_at(curve, station_a, length)
		var tangent_b := _tangent_at(curve, station_b, length)
		var across_a := Vector3(tangent_a.z, 0.0, -tangent_a.x).normalized()
		var across_b := Vector3(tangent_b.z, 0.0, -tangent_b.x).normalized()
		var a_road := point_a - across_a * curb_width * 0.5
		var a_bed := point_a + across_a * curb_width * 0.5
		var b_road := point_b - across_b * curb_width * 0.5
		var b_bed := point_b + across_b * curb_width * 0.5
		var rise := Vector3.UP * curb_height
		_add_quad(surface, a_road + rise, b_road + rise,
			b_bed + rise, a_bed + rise)
		_add_quad(surface, a_road, b_road, b_road + rise, a_road + rise)
		_add_quad(surface, a_bed + rise, b_bed + rise, b_bed, a_bed)
	surface.generate_normals()
	return surface.commit()


func _tangent_at(curve: Curve3D, station: float, length: float) -> Vector3:
	var before := curve.sample_baked(maxf(0.0, station - 0.1))
	var after := curve.sample_baked(minf(length, station + 0.1))
	return (after - before).normalized()


func _add_quad(surface: SurfaceTool, a: Vector3, b: Vector3,
		c: Vector3, d: Vector3) -> void:
	for vertex in [a, b, c, a, c, d]:
		surface.add_vertex(vertex)
