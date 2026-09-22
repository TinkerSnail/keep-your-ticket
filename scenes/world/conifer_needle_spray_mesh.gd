@tool
extends ArrayMesh

## Lightweight reusable conifer spray. The tree scene owns every spray's
## position, scale and orientation; this inspector-controlled resource derives
## only the repeated fine needles around one small central branchlet.

@export var needle_material: Material:
	set(value):
		needle_material = value
		if get_surface_count() > 0:
			surface_set_material(0, needle_material)
@export_range(0.5, 3.0, 0.05) var extent := 1.0:
	set(value):
		extent = value
		_rebuild()
@export_range(8, 24, 1) var needle_pairs := 16:
	set(value):
		needle_pairs = value
		_rebuild()
@export_range(0.18, 0.5, 0.01) var needle_length := 0.32:
	set(value):
		needle_length = value
		_rebuild()
@export_range(0.004, 0.06, 0.001) var needle_width := 0.01:
	set(value):
		needle_width = value
		_rebuild()
@export_range(2, 5, 1) var spray_layers := 3:
	set(value):
		spray_layers = value
		_rebuild()
@export_range(0.0, 0.18, 0.01) var droop := 0.07:
	set(value):
		droop = value
		_rebuild()


func _init() -> void:
	_rebuild()


func _rebuild() -> void:
	clear_surfaces()
	if extent <= 0.0 or needle_pairs < 2:
		return
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var half := extent * 0.5
	# One fine rachis holds the silhouette together without returning to a solid
	# pad. A short crossing twig stops end-on sprays from vanishing.
	_append_ribbon(vertices, normals, uvs,
		Vector3(-half, 0.0, 0.0), Vector3(half, -extent * 0.025, 0.0),
		extent * 0.012, Vector3.FORWARD)
	_append_ribbon(vertices, normals, uvs,
		Vector3(-extent * 0.12, -extent * 0.012, -extent * 0.32),
		Vector3(extent * 0.12, -extent * 0.02, extent * 0.32),
		extent * 0.008, Vector3(0.93, 0.0, -0.37).normalized())
	for layer_index in spray_layers:
		var layer_t := float(layer_index) / float(maxi(1, spray_layers - 1))
		var layer_side := layer_t * 2.0 - 1.0
		var layer_span := 1.0 - absf(layer_side) * 0.28
		# The previous single plane vanished at full-tree distance. These remain
		# separate fine branchlets, but occupy the editable spray's full vertical
		# envelope so the crown retains readable foliage volume.
		var layer_y := extent * layer_side * 0.32
		var layer_z := extent * layer_side * 0.09
		var layer_x := extent * 0.028 * sin(float(layer_index) * 2.4)
		_append_ribbon(vertices, normals, uvs,
			Vector3(-half * 0.92 * layer_span + layer_x, layer_y, layer_z),
			Vector3(half * 0.92 * layer_span + layer_x,
				layer_y - extent * 0.025, layer_z),
			extent * 0.008, Vector3.FORWARD)
		for index in needle_pairs:
			var t := (float(index) + 0.5) / float(needle_pairs)
			var x := lerpf(-half * 0.94 * layer_span,
				half * 0.94 * layer_span, t) + layer_x
			var centre_weight := 1.0 - absf(t * 2.0 - 1.0)
			var variation := 0.84 + 0.18 * sin(
				float(index) * 2.17 + float(layer_index) * 1.31 + 0.6)
			var reach := extent * needle_length * variation \
				* (0.72 + 0.28 * centre_weight) * (1.0 - absf(layer_side) * 0.12)
			var axial_sweep := extent * 0.035 * sin(
				float(index) * 1.71 + float(layer_index) * 0.83)
			var ripple := extent * 0.028 * sin(
				float(index) * 2.83 + float(layer_index))
			for side in [-1.0, 1.0]:
				var base := Vector3(x, layer_y + ripple,
					layer_z + side * extent * 0.008)
				var tip := base + Vector3(axial_sweep,
					-extent * droop * variation, side * reach)
				_append_tapered_needle(vertices, normals, uvs, base, tip,
					extent * needle_width * (0.9 + 0.12 * centre_weight))
				# Short lifted siblings give the spray thickness without a solid core.
				if (index + layer_index) % 2 == 0:
					var upper_tip := base + Vector3(-axial_sweep * 0.45,
						extent * 0.07, side * reach * 0.72)
					_append_tapered_needle(vertices, normals, uvs, base, upper_tip,
						extent * needle_width * 0.72)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	if needle_material != null:
		surface_set_material(0, needle_material)


func _append_tapered_needle(vertices: PackedVector3Array,
		normals: PackedVector3Array, uvs: PackedVector2Array,
		base: Vector3, tip: Vector3, half_width: float) -> void:
	var direction := (tip - base).normalized()
	var across := direction.cross(Vector3.UP).normalized()
	if across.length_squared() < 0.5:
		across = Vector3.RIGHT
	var a := base - across * half_width
	var b := base + across * half_width
	_append_triangle(vertices, normals, uvs, a, tip, b,
		Vector2(0, 0), Vector2(0.5, 1), Vector2(1, 0))


func _append_ribbon(vertices: PackedVector3Array, normals: PackedVector3Array,
		uvs: PackedVector2Array, start: Vector3, finish: Vector3,
		half_width: float, side: Vector3) -> void:
	var a := start - side * half_width
	var b := start + side * half_width
	var c := finish + side * half_width * 0.55
	var d := finish - side * half_width * 0.55
	_append_triangle(vertices, normals, uvs, a, d, c,
		Vector2(0, 0), Vector2(0, 1), Vector2(1, 1))
	_append_triangle(vertices, normals, uvs, a, c, b,
		Vector2(0, 0), Vector2(1, 1), Vector2(1, 0))


func _append_triangle(vertices: PackedVector3Array,
		normals: PackedVector3Array, uvs: PackedVector2Array,
		a: Vector3, b: Vector3, c: Vector3,
		uv_a: Vector2, uv_b: Vector2, uv_c: Vector2) -> void:
	var normal := (b - a).cross(c - a).normalized()
	if normal.length_squared() < 0.5:
		normal = Vector3.UP
	vertices.append_array(PackedVector3Array([a, b, c]))
	normals.append_array(PackedVector3Array([normal, normal, normal]))
	uvs.append_array(PackedVector2Array([uv_a, uv_b, uv_c]))
