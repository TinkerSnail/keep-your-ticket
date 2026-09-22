@tool
extends Node3D

@export_color_no_alpha var leaf_color := Color(0.2, 0.48, 0.12)
@export_range(12, 36, 1) var leaf_count := 24
@export_range(0.2, 0.7, 0.01) var spread := 0.46
@export_range(0.16, 0.75, 0.01) var mound_height := 0.18
@export_range(0.08, 0.22, 0.005) var leaf_size := 0.15
@export var seed_value := 1


func _ready() -> void:
	_rebuild()


func _rebuild() -> void:
	for child in get_children():
		child.queue_free()

	var leaf_mesh := SphereMesh.new()
	leaf_mesh.radius = 0.5
	leaf_mesh.height = 1.0
	leaf_mesh.radial_segments = 7
	leaf_mesh.rings = 3
	var leaf_material := StandardMaterial3D.new()
	leaf_material.albedo_color = leaf_color
	leaf_material.roughness = 0.96
	var core_mesh := SphereMesh.new()
	core_mesh.radius = 0.5
	core_mesh.height = 1.0
	core_mesh.radial_segments = 10
	core_mesh.rings = 4
	var core := MeshInstance3D.new()
	core.name = "low_foliage_core"
	core.mesh = core_mesh
	core.material_override = leaf_material
	# Height is independent of spread so a compact basket pocket and a heaping
	# ground mound can share the same editable leaf recipe without squashing.
	core.position.y = mound_height * 0.45
	core.scale = Vector3(spread * 1.62, mound_height * 0.9, spread * 1.42)
	add_child(core)

	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	for index in leaf_count:
		var angle := float(index) * 2.399963 + rng.randf_range(-0.16, 0.16)
		var radius_fraction := sqrt((float(index) + 0.5) / float(leaf_count))
		var radius := radius_fraction * spread
		var leaf := MeshInstance3D.new()
		leaf.name = "leaf_%02d" % index
		leaf.mesh = leaf_mesh
		leaf.material_override = leaf_material
		leaf.position = Vector3(cos(angle) * radius,
			0.045 + mound_height * (0.2 + (1.0 - radius_fraction) * 0.75) \
				+ rng.randf_range(-0.018, 0.026),
			sin(angle) * radius)
		leaf.rotation = Vector3(rng.randf_range(-0.24, 0.24),
			-angle + PI * 0.5, rng.randf_range(-0.18, 0.18))
		var size_variation := rng.randf_range(0.82, 1.16)
		leaf.scale = Vector3(leaf_size * 0.72, leaf_size * 0.2,
			leaf_size * 1.15) * size_variation
		add_child(leaf)
