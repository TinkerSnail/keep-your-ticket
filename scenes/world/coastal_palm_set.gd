@tool
extends Node3D

## A placement set of coastal palms (GRP-PARK-007): each child is a
## `coastal_palm.tscn` Christina places and tunes in the editor.
##
## The generator still emits a stick palm (`<name>_trunk`, `_crown`,
## `_frond_<n>`) at each of these feet in the wrapper's generated scene; this
## hides the ones named for a palm here. It reads nothing else from them: the
## feet, heights and crowns are the palms' own values.

@export var generated_root := NodePath("../.."):
	set(value):
		generated_root = value
		_retire_generated.call_deferred()


func _ready() -> void:
	_retire_generated.call_deferred()


func _retire_generated() -> void:
	var root := get_node_or_null(generated_root)
	if root == null:
		return
	for palm in get_children():
		var prefix := String(palm.name)
		for suffix in ["_trunk", "_crown"]:
			var stick := root.get_node_or_null(prefix + suffix) as Node3D
			if stick != null:
				stick.visible = false
		var index := 0
		while true:
			var frond := root.get_node_or_null("%s_frond_%d" % [prefix, index]) as Node3D
			if frond == null:
				break
			frond.visible = false
			index += 1
