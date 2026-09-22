extends Node

## Focused source acceptance for the catalog-only shaded-waterfront kit derived
## from the supplied reference photograph. It checks reusable editor ownership,
## the distinct parts that make each family useful and the complete vignette;
## it makes no world-placement claim.

const SOURCES := {
	"PRP-PARK-022": {
		"path": "res://scenes/world/park_furniture/granite_circle_picnic_table.tscn",
		"groups": {"stone_seats": 6},
		"required": [&"round_tabletop", &"collision"],
	},
	"PRP-PARK-023": {
		"path": "res://scenes/world/park_furniture/color_block_information_panel.tscn",
		"groups": {"panel": 10, "supports": 2},
		"required": [&"collision"],
	},
	"PRP-COAST-011": {
		"path": "res://scenes/world/park_furniture/reclined_waterfront_viewing_bench.tscn",
		"groups": {"seat_slats": 5, "reclined_back": 6, "frames": 4},
		"required": [&"collision"],
	},
	"PRP-PLANT-034": {
		"path": "res://scenes/world/white_bark_tree_cluster.tscn",
		"groups": {"trunks": 4, "bark_scars": 7, "crowns": 5},
		"required": [&"collision"],
	},
	"PRP-PLANT-035": {
		"path": "res://scenes/world/clipped_hedge_module.tscn",
		"groups": {"crown_blocks": 3},
		"required": [&"body", &"collision"],
	},
	"PRP-PLANT-036": {
		"path": "res://scenes/world/lilyturf_clump.tscn",
		"groups": {"blades": 16},
		"required": [],
	},
	"PRP-PLANT-037": {
		"path": "res://scenes/world/lilyturf_row.tscn",
		"groups": {".": 7},
		"required": [],
	},
	"PRP-FENCE-002": {
		"path": "res://scenes/world/park_fencing/waterfront_guardrail.tscn",
		"groups": {"posts": 4, "rails": 3},
		"required": [&"collision"],
	},
}

const VIGNETTE := "res://scenes/world/shaded_waterfront_promenade_catalog.tscn"

var _fails: Array[String] = []


func _ready() -> void:
	for label in SOURCES:
		_check_source(String(label), SOURCES[label])
	_check_vignette()
	if _fails.is_empty():
		print("PASS: shaded waterfront catalog kit preserves eight reusable editor-owned families and one complete catalog-only vignette")
	else:
		for failure in _fails:
			push_error(failure)
	get_tree().quit(1 if not _fails.is_empty() else 0)


func _check_source(label: String, specification: Dictionary) -> void:
	var packed := load(String(specification["path"])) as PackedScene
	if packed == null:
		_fails.append("%s does not load: %s" % [label, specification["path"]])
		return
	var source := packed.instantiate() as Node3D
	if source == null:
		_fails.append("%s root is not Node3D" % label)
		return
	if source.get_script() != null:
		_fails.append("%s must remain directly editor-owned" % label)
	var description := String(source.get("editor_description"))
	if not description.contains(label):
		_fails.append("%s source description lost its catalog label" % label)
	for required_name in specification["required"]:
		if source.get_node_or_null(NodePath(String(required_name))) == null:
			_fails.append("%s is missing %s" % [label, required_name])
	for group_name in specification["groups"]:
		var group: Node = source if String(group_name) == "." else \
			source.get_node_or_null(NodePath(String(group_name)))
		if group == null:
			_fails.append("%s is missing group %s" % [label, group_name])
			continue
		var expected := int(specification["groups"][group_name])
		if group.get_child_count() != expected:
			_fails.append("%s/%s expected %d selectable parts, found %d" % [
				label, group_name, expected, group.get_child_count()])
	if label == "PRP-PARK-022":
		for top_name in [&"northwest_top", &"northeast_top", &"south_top"]:
			var top := source.get_node("stone_seats/%s" % top_name) as Node3D
			if absf(top.position.y - 0.512) > 0.006:
				_fails.append("%s/%s lost the 0.51m seat top" % [label, top_name])
	if label == "PRP-COAST-011":
		var highest_seat := -INF
		for slat in source.get_node("seat_slats").get_children():
			highest_seat = maxf(highest_seat, (slat as MeshInstance3D).position.y + 0.025)
		if absf(highest_seat - 0.53) > 0.025:
			_fails.append("%s lost its approximately 0.51m seat surface" % label)
	source.free()


func _check_vignette() -> void:
	var packed := load(VIGNETTE) as PackedScene
	var vignette := packed.instantiate() as Node3D if packed != null else null
	if vignette == null:
		_fails.append("GRP-PARK-017 does not load")
		return
	if vignette.get_script() != null:
		_fails.append("GRP-PARK-017 must stay directly editor-owned")
	var expected := {
		"white_bark_canopy": 2,
		"clipped_hedge_edge": 6,
		"dark_lilyturf_seams": 4,
		"information_panel_rhythm": 10,
		"waterfront_guard": 6,
		"furniture_pockets": 3,
	}
	for group_name in expected:
		var group := vignette.get_node_or_null(NodePath(String(group_name)))
		if group == null or group.get_child_count() != int(expected[group_name]):
			_fails.append("GRP-PARK-017/%s lost its catalog recipe" % group_name)
	vignette.free()
