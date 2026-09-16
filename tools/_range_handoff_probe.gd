extends Node

## Dev probe: did a boulder edited in Blender arrive in Godot as collision?
##
##     godot --headless --path . tools/run.tscn -- _range_handoff_probe <edit.json>
##
## The JSON is written by whoever made the edit, in Godot coordinates: the
## boulder's plan centre before and after, and the height of its top surface at
## each centre as Blender measures it on the edited file (`old_top_y` is where
## the top *was*; after the edit nothing of this boulder stands there).
##
##     {"name": ..., "old_centre": [x, z], "old_top_y": y,
##      "new_centre": [x, z], "new_top_y": y}
##
## A ray dropped at the new centre must land on the top Blender predicts, so
## the derived collision moved with the visual. A ray at the old centre must
## land somewhere else, so no collision stayed behind, which is the defect the
## derived export replaced. The mesh and material side of the same edit is
## proved by diffing the exported GLB against the previous one, which needs no
## Godot; see the 2026-09-15 journal.

const WRAPPER := "res://scenes/world/range_forest_background.tscn"
const TOLERANCE := 0.05

var _fails: Array[String] = []


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		push_error("usage: -- _range_handoff_probe <edit.json>")
		get_tree().quit(2)
		return
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
	var range_root := (load(WRAPPER) as PackedScene).instantiate()
	add_child(range_root)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var new_hit := _drop(spec["new_centre"])
	var old_hit := _drop(spec["old_centre"])
	var new_top: float = spec["new_top_y"]
	var old_top: float = spec["old_top_y"]
	print("new centre: Blender top y %.3f, Godot collision y %s" % [new_top, _fmt(new_hit)])
	print("old centre: Blender former top y %.3f, Godot collision y %s" % [old_top, _fmt(old_hit)])
	_expect(not new_hit.is_empty() and absf(new_hit["position"].y - new_top) <= TOLERANCE,
		"collision at the new position does not match the edited boulder's top")
	_expect(old_hit.is_empty() or absf(old_hit["position"].y - old_top) > TOLERANCE,
		"collision still stands at the boulder's old top height; a twin was left behind")
	if not new_hit.is_empty():
		print("collider: %s" % (new_hit["collider"] as Node).get_path())
	if _fails.is_empty():
		print("PASS: the Blender edit to %s reached Godot's collision" % spec["name"])
		get_tree().quit(0)
	else:
		for f in _fails:
			print("FAIL: " + f)
		get_tree().quit(1)


func _drop(centre: Array) -> Dictionary:
	var space := get_viewport().world_3d.direct_space_state
	var q := PhysicsRayQueryParameters3D.create(
		Vector3(centre[0], 200.0, centre[1]), Vector3(centre[0], -60.0, centre[1]), 1)
	return space.intersect_ray(q)


func _fmt(hit: Dictionary) -> String:
	return "none" if hit.is_empty() else "%.3f" % hit["position"].y


func _expect(ok: bool, message: String) -> void:
	if not ok:
		_fails.append(message)
