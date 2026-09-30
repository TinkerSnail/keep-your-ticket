@tool
extends Node3D

## The bird of paradise (Strelitzia reginae), landscape kit (2026-09-29, her
## "lets use the same principles from our hakone grass and our palm crowns to
## make some bird of paradise plants"). Its shape is
## assets/source/props/bird_of_paradise.blend, built by
## tools/blender/bird_of_paradise.py: a course per leaf and per flower stalk,
## each bending a shared blade. Send to game writes
## assets/props/bird_of_paradise.glb. Visual only.

## Which clump (her "keep both"): a, few big leaves and four flowers; b,
## fuller like her photo, with seven. Both have low leaves drooping over the
## soil. Each is its own mesh, `bird_of_paradise_<variant>_visual`; the other
## is hidden.
@export_enum("a", "b") var variant := 0:
	set(value):
		variant = clampi(value, 0, VARIANTS.size() - 1)
		_show()

const PREFIX := "bird_of_paradise_"
const VARIANTS := ["a", "b"]


func _ready() -> void:
	_show()


func _show() -> void:
	for found in find_children(PREFIX + "*", "MeshInstance3D", true, false):
		var part := String(found.name).trim_prefix(PREFIX)
		(found as MeshInstance3D).visible = part.get_slice("_", 0) == VARIANTS[variant]
