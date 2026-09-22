@tool
extends Node3D

@export_color_no_alpha var petal_color := Color(0.84, 0.12, 0.68)
@export_color_no_alpha var throat_color := Color(0.98, 0.78, 0.22)
@export_range(0.08, 0.22, 0.005) var diameter := 0.14


func _ready() -> void:
	_rebuild()


func _rebuild() -> void:
	for child in get_children():
		child.queue_free()

	var petal_mesh := SphereMesh.new()
	petal_mesh.radius = 0.5
	petal_mesh.height = 1.0
	petal_mesh.radial_segments = 7
	petal_mesh.rings = 3
	var petal_material := StandardMaterial3D.new()
	petal_material.albedo_color = petal_color
	petal_material.roughness = 0.82

	for index in 5:
		var angle := TAU * float(index) / 5.0
		var petal := MeshInstance3D.new()
		petal.name = "petal_%02d" % index
		petal.mesh = petal_mesh
		petal.material_override = petal_material
		petal.position = Vector3(sin(angle), 0.0, cos(angle)) * diameter * 0.28
		petal.rotation.y = angle
		petal.scale = Vector3(diameter * 0.78, diameter * 0.2,
			diameter * 1.05)
		add_child(petal)

	var throat_mesh := SphereMesh.new()
	throat_mesh.radius = 0.5
	throat_mesh.height = 1.0
	throat_mesh.radial_segments = 7
	throat_mesh.rings = 3
	var throat_material := StandardMaterial3D.new()
	throat_material.albedo_color = throat_color
	throat_material.roughness = 0.76
	var throat := MeshInstance3D.new()
	throat.name = "throat"
	throat.mesh = throat_mesh
	throat.material_override = throat_material
	throat.position.y = diameter * 0.06
	throat.scale = Vector3.ONE * diameter * 0.24
	add_child(throat)
