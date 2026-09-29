@tool
extends Node3D

## Purple Heart sprig (PRP-PLANT-015 to 017). Its stem, leaves and flower are
## shaped in assets/source/props/purple_heart_sprig.blend: one leaf and one
## young leaf placed up the stem course, and the flower at its tip. The GLB
## carries the stem, one mesh of leaves for each pair count, 4 to 7, and the
## flower; each placement shows its own. Until 2026-09-28 this script built the
## sprig from a Path3D course here, with a leaf_scale two catalog sprigs set;
## git holds that version.

@export_range(4, 7, 1) var leaf_pair_count := 6:
	set(value):
		leaf_pair_count = clampi(value, 4, 7)
		_show()
@export var flowered := false:
	set(value):
		flowered = value
		_show()


func _ready() -> void:
	_show()


## The meshes not shown are hidden, not freed; StaticMerge leaves hidden meshes
## out of the running game's merged mesh.
func _show() -> void:
	var model := get_node_or_null("model")
	if model == null:
		return
	for pairs in range(4, 8):
		var leaves := model.get_node_or_null("purple_heart_sprig_pairs_%d" % pairs) as Node3D
		if leaves != null:
			leaves.visible = pairs == leaf_pair_count
	var flower := model.get_node_or_null("purple_heart_sprig_flower") as Node3D
	if flower != null:
		flower.visible = flowered
