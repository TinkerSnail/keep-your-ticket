@tool
extends Node3D

## The upright elephant ear (Alocasia), landscape kit (2026-09-29, her "using
## the same principles from our hakone grass and our palm crowns, lets make one
## of these - it should be shoulder height at the most and thigh height at the
## least"). Its shape is assets/source/props/elephant_ear.blend: a course per
## leaf, each bending a shared blade; its leaves' textures are drawn by
## tools/blender/elephant_ear_leaves.py. Send to game writes
## assets/props/elephant_ear.glb. Visual only.

## Which plant (her "lets make a mature version in addition to this one",
## "then make a redder varietal"): the clump, the mature clump on its short
## trunk, and both in the red varietal. Each is its own mesh,
## `elephant_ear_<variant>_visual`; the others are hidden.
@export_enum("green", "green_mature", "red", "red_mature") var variant := 0:
	set(value):
		variant = clampi(value, 0, VARIANTS.size() - 1)
		_show()

## How tall this one stands, in metres, from thigh (0.70) to shoulder (1.40)
## height, her range. The plant is scaled to it from the height it was
## modelled at (the clump about 1.27 m, the mature clump 1.38 m).
@export_range(0.70, 1.40, 0.01, "suffix:m") var height := 1.27:
	set(value):
		height = clampf(value, 0.70, 1.40)
		_show()

const PREFIX := "elephant_ear_"
const VARIANTS := ["green", "green_mature", "red", "red_mature"]


func _ready() -> void:
	_show()


func _show() -> void:
	var model := get_node_or_null(^"model") as Node3D
	if model == null:
		return
	var shown: MeshInstance3D = null
	for found in model.find_children(PREFIX + "*", "MeshInstance3D", true, false):
		var mesh := found as MeshInstance3D
		mesh.visible = String(mesh.name) == PREFIX + VARIANTS[variant] + "_visual"
		if mesh.visible:
			shown = mesh
	if shown != null and shown.mesh != null:
		var top := shown.mesh.get_aabb().end.y
		if top > 0.0:
			model.scale = Vector3.ONE * (height / top)
