extends Node

## Focused acceptance for the shared pointed strap-leaf handoff and the paired
## deep/yellow-green Lily of the Nile and lilyturf catalog families. This is a
## source test only and makes no claim about park placement.

const CLUMPS := {
	"PRP-PLANT-029": {
		"path": "res://scenes/world/lily_of_the_nile_clump.tscn",
		"group": "strap_leaves",
		"count": 12,
		"min_half_width": 0.075,
		"max_half_width": 0.11,
	},
	"PRP-PLANT-042": {
		"path": "res://scenes/world/lily_of_the_nile_clump_light.tscn",
		"group": "strap_leaves",
		"count": 12,
		"min_half_width": 0.075,
		"max_half_width": 0.11,
	},
	"PRP-PLANT-036": {
		"path": "res://scenes/world/lilyturf_clump.tscn",
		"group": "blades",
		"count": 16,
		"min_half_width": 0.035,
		"max_half_width": 0.05,
	},
	"PRP-PLANT-043": {
		"path": "res://scenes/world/lilyturf_clump_light.tscn",
		"group": "blades",
		"count": 16,
		"min_half_width": 0.035,
		"max_half_width": 0.05,
	},
}

const ROWS := {
	"PRP-PLANT-037": "res://scenes/world/lilyturf_row.tscn",
	"PRP-PLANT-044": "res://scenes/world/lilyturf_row_light.tscn",
}

const LEAF_SCRIPT := "res://scenes/world/arching_strap_leaf.gd"
const FLOWER_STEM_SCRIPT := "res://scenes/world/arching_flower_stem.gd"

var _fails: Array[String] = []
var _palette_colors := {}


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	for label in CLUMPS:
		await _check_clump(String(label), CLUMPS[label])
	for label in ROWS:
		_check_row(String(label), String(ROWS[label]))
	_check_palette_pair("PRP-PLANT-029", "PRP-PLANT-042")
	_check_palette_pair("PRP-PLANT-036", "PRP-PLANT-043")
	if _fails.is_empty():
		print("PASS: both plant families share a pointed arching leaf and preserve distinct deep-green and yellow-green catalog variants")
	else:
		for failure in _fails:
			push_error(failure)
	get_tree().quit(1 if not _fails.is_empty() else 0)


func _check_clump(label: String, specification: Dictionary) -> void:
	var packed := load(String(specification["path"])) as PackedScene
	var source := packed.instantiate() as Node3D if packed != null else null
	if source == null:
		_fails.append("%s does not load" % label)
		return
	add_child(source)
	await get_tree().process_frame
	await get_tree().process_frame
	if source.get_script() != null:
		_fails.append("%s root must remain directly editor-owned" % label)
	if not String(source.editor_description).contains(label):
		_fails.append("%s source description lost its catalog label" % label)
	var group := source.get_node_or_null(NodePath(String(specification["group"])))
	if group == null or group.get_child_count() != int(specification["count"]):
		_fails.append("%s lost its selectable leaf count" % label)
		source.queue_free()
		await get_tree().process_frame
		return
	for leaf in group.get_children():
		var script := leaf.get_script() as Script
		if script == null or script.resource_path != LEAF_SCRIPT:
			_fails.append("%s/%s does not instance the shared leaf source" % [label, leaf.name])
			continue
		var half_width := float(leaf.get("half_width"))
		if half_width < float(specification["min_half_width"]) or \
				half_width > float(specification["max_half_width"]):
			_fails.append("%s/%s width no longer matches its plant family" % [label, leaf.name])
		var course := leaf.get_node_or_null("course") as Path3D
		if course == null or course.curve == null or course.curve.point_count < 6:
			_fails.append("%s/%s lost the editable six-point course" % [label, leaf.name])
		else:
			var tip := course.curve.get_point_position(course.curve.point_count - 1)
			var crown := course.curve.get_point_position(course.curve.point_count - 2)
			if tip.x < 0.5 or tip.y >= crown.y:
				_fails.append("%s/%s lost its outward lowered point" % [label, leaf.name])
		var derived := leaf.get_node_or_null("derived_leaf") as MeshInstance3D
		if derived == null or derived.mesh == null or derived.mesh.get_surface_count() != 1:
			_fails.append("%s/%s did not derive one surfaced folded ribbon" % [label, leaf.name])
	var first_material := group.get_child(0).get("leaf_material") as StandardMaterial3D
	if first_material == null:
		_fails.append("%s lost its readable leaf palette" % label)
	else:
		_palette_colors[label] = first_material.albedo_color
	if label == "PRP-PLANT-029" or label == "PRP-PLANT-042":
		_check_agapanthus_stems(label, source)
	source.queue_free()
	await get_tree().process_frame


func _check_agapanthus_stems(label: String, source: Node3D) -> void:
	var flower_stems := source.get_node_or_null("flower_stems") as Node3D
	if flower_stems == null:
		_fails.append("%s lost its flower-stem group" % label)
		return
	for index in 6:
		var stem := flower_stems.get_node_or_null("stem_%02d" % index) as Node3D
		var globe := flower_stems.get_node_or_null("globe_%02d" % index) as Node3D
		if stem == null or globe == null:
			_fails.append("%s lost selectable stem/globe pair %02d" % [label, index])
			continue
		var stem_script := stem.get_script() as Script
		if stem_script == null or stem_script.resource_path != FLOWER_STEM_SCRIPT:
			_fails.append("%s/stem_%02d does not instance the shared bending stem" % [label, index])
			continue
		var course := stem.get_node_or_null("course") as Path3D
		var derived := stem.get_node_or_null("derived_stem") as Node3D
		if course == null or course.curve == null or course.curve.point_count < 4:
			_fails.append("%s/stem_%02d lost its editable four-point course" % [label, index])
			continue
		var tip := course.curve.get_point_position(course.curve.point_count - 1)
		if Vector2(tip.x, tip.z).length() < 0.08:
			_fails.append("%s/stem_%02d no longer carries a visible bend" % [label, index])
		var expected_globe := stem.transform * tip
		if globe.position.distance_to(expected_globe) > 0.035:
			_fails.append("%s/globe_%02d no longer meets its bent stem" % [label, index])
		if derived == null or derived.get_child_count() < 8:
			_fails.append("%s/stem_%02d did not derive a smooth segmented stalk" % [label, index])


func _check_row(label: String, path: String) -> void:
	var packed := load(path) as PackedScene
	var row := packed.instantiate() as Node3D if packed != null else null
	if row == null:
		_fails.append("%s does not load" % label)
		return
	if row.get_script() != null or row.get_child_count() != 7:
		_fails.append("%s must remain seven directly editable clump instances" % label)
	if not String(row.editor_description).contains(label):
		_fails.append("%s source description lost its catalog label" % label)
	row.free()


func _check_palette_pair(dark_label: String, light_label: String) -> void:
	if not _palette_colors.has(dark_label) or not _palette_colors.has(light_label):
		return
	var dark: Color = _palette_colors[dark_label]
	var light: Color = _palette_colors[light_label]
	if light.get_luminance() < dark.get_luminance() + 0.12:
		_fails.append("%s is not materially lighter than %s" % [light_label, dark_label])
	if light.r / light.g < dark.r / dark.g + 0.18:
		_fails.append("%s is not materially yellower than %s" % [light_label, dark_label])
