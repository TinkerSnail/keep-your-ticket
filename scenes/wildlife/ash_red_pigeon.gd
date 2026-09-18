extends "res://scenes/wildlife/bird.gd"

## Applies an independent ash-red/cream atlas to the shared authored pigeon
## form. The pale cere keeps the source model's dedicated material so it reads
## as flesh above the pink bill rather than as another patch of plumage.

@export var morph_material: StandardMaterial3D


func _ready() -> void:
	_apply_morph_material()
	super._ready()


func _apply_morph_material() -> void:
	if morph_material == null:
		return
	for descendant in pose_root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		if String(mesh_instance.name).begins_with("cere_"):
			continue
		mesh_instance.material_override = morph_material
