@tool
extends Node3D

## The coastal palm trunk, PRP-COAST-007. Its shape is Christina's, in
## `assets/source/props/palm_trunk.blend`, sent straight and upright to
## `assets/props/palm_trunk.glb` (`model`), foot at the origin and its highest
## point the crown seat. The selectable Path3D owns the trunk's bow; this script
## bends the model along it and shows the result as `derived_trunk`.
##
## The model is brought to one metre tall, so instances still scale the whole
## trunk to their seat, as they did when the trunk was built here. A vertex's
## height up the model is how far along the course it goes; across, it keeps its
## place in the course's frame, so an unbent course shows the model exactly as
## modelled. `bend_strength` scales the course's sideways reach, as before.
##
## Until 2026-09-27 this script built the trunk itself, a 14-ring, 8-sided tube;
## that tube moved to the Blender file unchanged first (every vertex of all 36
## palms within 0.20 mm, `tools/_palm_trunk_migration_probe.gd`), and was
## reshaped there after.

@export var model: PackedScene:
	set(value):
		model = value
		_queue_rebuild()
## Drawn in place of the model's own material when set.
@export var trunk_material: Material
@export_range(0.25, 1.35, 0.05) var bend_strength := 1.0:
	set(value):
		bend_strength = value
		_queue_rebuild()

## PackedScene -> [surface arrays, material, height], shared by every trunk.
static var _straight := {}

var _queued := false


func _ready() -> void:
	var path := get_node("trunk_course") as Path3D
	if path.curve != null and not path.curve.changed.is_connected(_queue_rebuild):
		path.curve.changed.connect(_queue_rebuild)
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _queued or not is_inside_tree():
		return
	_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_queued = false
	var path := get_node("trunk_course") as Path3D
	var instance := get_node("derived_trunk") as MeshInstance3D
	var source := _source(model)
	if path.curve == null or source.is_empty():
		instance.mesh = null
		return
	var curve := path.curve
	var length := curve.get_baked_length()
	var arrays: Array = (source[0] as Array).duplicate()
	var height: float = source[2]
	var vertices: PackedVector3Array = (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).duplicate()
	var normals: PackedVector3Array = (arrays[Mesh.ARRAY_NORMAL] as PackedVector3Array).duplicate() \
		if arrays[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
	var tangents: PackedFloat32Array = (arrays[Mesh.ARRAY_TANGENT] as PackedFloat32Array).duplicate() \
		if arrays[Mesh.ARRAY_TANGENT] != null else PackedFloat32Array()
	# Vertices of one ring share a height, and so a frame.
	var frames := {}
	for i in vertices.size():
		var v := vertices[i] / height
		var frame: Basis
		var centre: Vector3
		if frames.has(v.y):
			frame = frames[v.y][0]
			centre = frames[v.y][1]
		else:
			var t := clampf(v.y, 0.0, 1.0)
			centre = curve.sample_baked(length * t, true)
			centre.x *= bend_strength
			centre.z *= bend_strength
			var tangent := _tangent(curve, length * t, length)
			tangent = Vector3(tangent.x * bend_strength, tangent.y,
				tangent.z * bend_strength).normalized()
			var side := tangent.cross(Vector3.FORWARD).normalized()
			if side.length_squared() < 0.5:
				side = Vector3.RIGHT
			var forward := side.cross(tangent).normalized()
			# Upright, side is -x and forward -z: this frame is the identity there.
			frame = Basis(-side, tangent, -forward)
			frames[v.y] = [frame, centre]
		vertices[i] = centre + frame * Vector3(v.x, 0.0, v.z)
		if not normals.is_empty():
			normals[i] = (frame * normals[i]).normalized()
		if not tangents.is_empty():
			var t3 := frame * Vector3(tangents[i * 4], tangents[i * 4 + 1], tangents[i * 4 + 2])
			tangents[i * 4] = t3.x
			tangents[i * 4 + 1] = t3.y
			tangents[i * 4 + 2] = t3.z
	arrays[Mesh.ARRAY_VERTEX] = vertices
	if not normals.is_empty():
		arrays[Mesh.ARRAY_NORMAL] = normals
	if not tangents.is_empty():
		arrays[Mesh.ARRAY_TANGENT] = tangents
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, trunk_material if trunk_material != null else source[1])
	instance.mesh = mesh


## The model's one surface, its material and its height, read once per model.
static func _source(scene: PackedScene) -> Array:
	if scene == null:
		return []
	if _straight.has(scene):
		return _straight[scene]
	var root := scene.instantiate()
	var found: Array = []
	for node in [root] + root.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		if mi == null or mi.mesh == null:
			continue
		var arrays := mi.mesh.surface_get_arrays(0)
		# Send to game stands the model at its node's origin, unturned; the
		# height is its highest vertex, the crown seat.
		var height := 0.0
		for v in arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array:
			height = maxf(height, v.y)
		found = [arrays, mi.get_active_material(0), height]
		break
	root.free()
	if not found.is_empty():
		_straight[scene] = found
	return found


func _tangent(curve: Curve3D, distance: float, length: float) -> Vector3:
	var epsilon := minf(0.025, length * 0.04)
	var before: Vector3 = curve.sample_baked(maxf(0.0, distance - epsilon), true)
	var after: Vector3 = curve.sample_baked(minf(length, distance + epsilon), true)
	var tangent := (after - before).normalized()
	return tangent if tangent.length_squared() > 0.5 else Vector3.UP
