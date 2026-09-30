extends Node

## Focused source acceptance for the catalog-only California coast live oak
## (PRP-PLANT-049), since 2026-09-29 the Blender oak: the scene wraps
## assets/props/coastal_live_oak.glb, and for each variant and chapter shows
## that variant's trunk, leaves and the chapter's merge groups only, collides
## with that variant's trunk only, wears the chapter's canvas on its leaves,
## and stands at a mature oak's size.

const SOURCE := "res://scenes/world/coastal_live_oak.tscn"
const OAK_SCRIPT := "res://scenes/world/coastal_live_oak.gd"
const MODEL := "res://assets/props/coastal_live_oak.glb"
const PREFIX := "coastal_live_oak_"
const VARIANTS := ["a", "b", "c"]
const GROUPS := [["spring_buds"], ["summer_acorns"], ["fall_acorns", "fall_ground"], ["winter_acorns"]]
const CANVASES := ["coastal_live_oak_colour_spring.png", "coastal_live_oak_coastal_live_oak_colour.png",
	"coastal_live_oak_colour_fall.png", "coastal_live_oak_colour_winter.png"]

var _fails: Array[String] = []


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var packed := load(SOURCE) as PackedScene
	var oak := packed.instantiate() as Node3D if packed != null else null
	if oak == null:
		_fails.append("PRP-PLANT-049 source does not load")
		_finish()
		return
	add_child(oak)
	await get_tree().process_frame
	var script := oak.get_script() as Script
	if script == null or script.resource_path != OAK_SCRIPT:
		_fails.append("oak lost its wrapper script")
	if not String(oak.editor_description).contains("PRP-PLANT-049"):
		_fails.append("oak source lost its catalog identity")
	var model := oak.get_node_or_null("model")
	if model == null or model.scene_file_path != MODEL:
		_fails.append("oak no longer wraps %s" % MODEL)
	if not oak.is_in_group("seasonal_planting"):
		_fails.append("oak is not in seasonal_planting, so no season system reaches it")
	for v in VARIANTS.size():
		for chapter in 4:
			oak.set("variant", v)
			oak.call("set_season", chapter)
			await get_tree().process_frame
			_check(oak, v, chapter)
	_finish()


func _check(oak: Node3D, v: int, chapter: int) -> void:
	var tag: String = VARIANTS[v]
	var label := "variant %s, chapter %d" % [tag, chapter]
	var want := {"": true, "visual": true}
	for group in GROUPS[chapter]:
		want[group] = true
	var seen := {}
	var colliding := 0
	for found in oak.find_children("*", "MeshInstance3D", true, false):
		var mesh := found as MeshInstance3D
		var rest := String(mesh.name).trim_prefix(PREFIX)
		var mine := rest.get_slice("_", 0) == tag
		var group := rest.substr(2) if rest.length() > 2 else ""
		var should := mine and want.has(group)
		if mesh.visible != should:
			_fails.append("%s: %s is %s" % [label, mesh.name, "shown" if mesh.visible else "hidden"])
		if mesh.visible:
			seen[group] = true
		for shape in mesh.find_children("*", "CollisionShape3D", true, false):
			if not (shape as CollisionShape3D).disabled:
				colliding += 1
				if not mine:
					_fails.append("%s: %s still collides" % [label, mesh.name])
		if mesh.visible and group != "":
			_check_canvas(mesh, chapter, label)
	for group in want:
		if not seen.has(group):
			_fails.append("%s: nothing shown for '%s'" % [label, group if group != "" else "trunk"])
	if colliding != 1:
		_fails.append("%s: %d collision shapes on, not the one trunk" % [label, colliding])
	var bounds := _visible_bounds(oak)
	if bounds.size.y < 9.5 or bounds.size.y > 11.5:
		_fails.append("%s: %.2f m tall, not a mature oak's 9.5 to 11.5" % [label, bounds.size.y])
	if bounds.size.x < 11.0 or bounds.size.z < 11.0:
		_fails.append("%s: its crown is only %.1f by %.1f m" % [label, bounds.size.x, bounds.size.z])


func _check_canvas(mesh: MeshInstance3D, chapter: int, label: String) -> void:
	for surface in mesh.mesh.get_surface_count():
		var material := mesh.get_active_material(surface) as StandardMaterial3D
		if material == null or material.albedo_texture == null:
			continue
		var path := material.albedo_texture.resource_path
		if path.ends_with("_bark.png") or path.ends_with("_knot.png"):
			continue
		if not path.ends_with(CANVASES[chapter]):
			_fails.append("%s: %s wears %s" % [label, mesh.name, path.get_file()])


func _visible_bounds(root: Node3D) -> AABB:
	var found := false
	var box := AABB()
	var inverse := root.global_transform.affine_inverse()
	for child in root.find_children("*", "MeshInstance3D", true, false):
		var visual := child as MeshInstance3D
		if not visual.is_visible_in_tree():
			continue
		var local := (inverse * visual.global_transform) * visual.get_aabb()
		box = local if not found else box.merge(local)
		found = true
	return box


func _finish() -> void:
	if _fails.is_empty():
		print("PASS: PRP-PLANT-049 wraps the Blender oak; each of its three variants shows its own trunk, leaves and each chapter's acorns, buds or litter and canvas, and collides with its own trunk only")
	else:
		for failure in _fails:
			push_error("coastal_live_oak_catalog_test: " + failure)
	get_tree().quit(1 if not _fails.is_empty() else 0)
