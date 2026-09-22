extends Node

## Focused source acceptance for the catalog-only Torbay Dazzler and Electric
## Pink cordylines. The test guards editable leaf courses, surfaced ribbons,
## cultivar-specific palettes and Electric Pink's multi-shoot habit.

const SOURCE := "res://scenes/world/cordyline_catalog_family.tscn"
const ROSETTE_SCRIPT := "res://scenes/world/cordyline_rosette.gd"

var _fails: Array[String] = []


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var packed := load(SOURCE) as PackedScene
	var family := packed.instantiate() as Node3D if packed != null else null
	if family == null:
		_fail("catalog family does not load")
		_finish()
		return
	add_child(family)
	for _frame in 4:
		await get_tree().process_frame
	if family.get_script() != null:
		_fail("family root must remain directly editor-owned")
	var dazzler := family.get_node_or_null("torbay_dazzler") as Node3D
	var electric := family.get_node_or_null("electric_pink") as Node3D
	if dazzler == null or electric == null:
		_fail("one or both catalog anchors are missing")
		_finish()
		return
	if not String(dazzler.editor_description).contains("PRP-PLANT-047"):
		_fail("Torbay Dazzler anchor lost its catalog identity")
	if not String(electric.editor_description).contains("PRP-PLANT-048"):
		_fail("Electric Pink anchor lost its catalog identity")
	_check_crown(dazzler.get_node_or_null("crown") as Node3D, 24, "Torbay Dazzler")
	_check_crown(electric.get_node_or_null("crown_main") as Node3D, 20, "Electric Pink main shoot")
	_check_crown(electric.get_node_or_null("crown_left") as Node3D, 12, "Electric Pink left shoot")
	_check_crown(electric.get_node_or_null("crown_right") as Node3D, 10, "Electric Pink right shoot")
	if electric.find_children("crown_*", "Node3D", true, false).size() != 3:
		_fail("Electric Pink must remain a three-shoot clump")
	_check_palette(dazzler.get_node_or_null("crown") as Node3D,
		electric.get_node_or_null("crown_main") as Node3D)
	_finish()


func _check_crown(crown: Node3D, expected: int, label: String) -> void:
	if crown == null:
		_fail("%s crown is missing" % label)
		return
	var script := crown.get_script() as Script
	if script == null or script.resource_path != ROSETTE_SCRIPT:
		_fail("%s no longer uses the course-surfacing handoff" % label)
	var courses := crown.get_node_or_null("leaf_courses") as Node3D
	var derived := crown.get_node_or_null("derived_leaves") as Node3D
	if courses == null or courses.get_child_count() != expected:
		_fail("%s lost its %d selectable courses" % [label, expected])
		return
	if derived == null or derived.get_child_count() != expected:
		_fail("%s did not surface every leaf course" % label)
	for child in courses.get_children():
		var path := child as Path3D
		if path == null or path.curve == null or path.curve.point_count != 5:
			_fail("%s/%s lost its editable five-point course" % [label, child.name])
			continue
		if not child.has_meta("half_width"):
			_fail("%s/%s lost its local width control" % [label, child.name])
	for child in derived.get_children() if derived != null else []:
		var leaf := child as MeshInstance3D
		if leaf == null or leaf.mesh == null or leaf.mesh.get_surface_count() != 1:
			_fail("%s/%s is not one complete surfaced blade" % [label, child.name])


func _check_palette(dazzler: Node3D, electric: Node3D) -> void:
	if dazzler == null or electric == null:
		return
	var dazzler_mat := dazzler.get("leaf_material") as ShaderMaterial
	var electric_mat := electric.get("leaf_material") as ShaderMaterial
	if dazzler_mat == null or electric_mat == null:
		_fail("cultivar leaf materials are missing")
		return
	var dazzler_base: Color = dazzler_mat.get_shader_parameter("base_color")
	var dazzler_edge: Color = dazzler_mat.get_shader_parameter("edge_color")
	var electric_base: Color = electric_mat.get_shader_parameter("base_color")
	var electric_edge: Color = electric_mat.get_shader_parameter("edge_color")
	if dazzler_edge.get_luminance() < dazzler_base.get_luminance() + 0.25:
		_fail("Torbay Dazzler lost its bright cream-yellow margins")
	if electric_edge.r < electric_base.r + 0.55 or electric_edge.b < 0.35:
		_fail("Electric Pink lost its hot-pink edge against the maroon blade")
	if dazzler_edge.get_luminance() < electric_edge.get_luminance() + 0.2:
		_fail("the two cultivar palettes are no longer unmistakably different")


func _fail(message: String) -> void:
	_fails.append(message)


func _finish() -> void:
	if _fails.is_empty():
		print("PASS: Torbay Dazzler keeps its cream-striped single fountain and Electric Pink its hot-pink three-shoot clump")
	else:
		for failure in _fails:
			push_error("cordyline_catalog_test: " + failure)
	get_tree().quit(1 if not _fails.is_empty() else 0)
