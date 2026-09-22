extends Node

## Focused source acceptance for the catalog-only California coast live oak.
## The test guards its authored low fork, broad asymmetric course silhouette,
## leaf-defined crown and independence from any standing park or range tree.

const SOURCE := "res://scenes/world/coastal_live_oak.tscn"
const OAK_SCRIPT := "res://scenes/world/coastal_live_oak.gd"

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
	for _frame in 4:
		await get_tree().process_frame
	var script := oak.get_script() as Script
	if script == null or script.resource_path != OAK_SCRIPT:
		_fails.append("oak lost its editor-course surfacing handoff")
	if not String(oak.editor_description).contains("PRP-PLANT-049"):
		_fails.append("oak source lost its catalog identity")
	var trunks := oak.get_node_or_null("trunk_courses") as Node3D
	var branches := oak.get_node_or_null("branch_courses") as Node3D
	if trunks == null or trunks.get_child_count() != 5:
		_fails.append("oak must retain five selectable low-forking trunk courses")
	if branches == null or branches.get_child_count() != 23:
		_fails.append("oak must retain twenty-three selectable crown courses")
	_check_courses(trunks, true)
	_check_courses(branches, false)
	var wood := oak.get_node_or_null("derived_wood") as Node3D
	var leaves := oak.get_node_or_null("derived_leaves") as Node3D
	if wood == null or wood.get_child_count() != 28:
		_fails.append("every trunk and branch course must produce one bark surface")
	if leaves == null or leaves.get_child_count() != 23:
		_fails.append("every crown course must produce one leaf spray")
	var leaf_vertices := 0
	if leaves != null:
		for child in leaves.get_children():
			var visual := child as MeshInstance3D
			if visual == null or visual.mesh == null:
				_fails.append("one crown course has no leaf-defined surface")
				continue
			var arrays := visual.mesh.surface_get_arrays(0)
			leaf_vertices += (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
	if leaf_vertices < 70000:
		_fails.append("the broad evergreen crown is no longer leaf-defined and dense")
	var bounds := _mesh_bounds(oak)
	if bounds.size.y < 10.5:
		_fails.append("oak lost the reference's mature roadside stature")
	if bounds.size.x < 9.0 or bounds.size.z < 7.0:
		_fails.append("oak lost its broad irregular live-oak crown")
	var source_text := FileAccess.get_file_as_string(SOURCE)
	if source_text.contains("SphereMesh") or source_text.contains("CapsuleMesh"):
		_fails.append("oak must not regress to sphere or capsule canopy masses")
	var oak_leaf_length := float(oak.get("leaf_length"))
	var oak_leaf_half_width := float(oak.get("leaf_half_width"))
	if oak_leaf_half_width / oak_leaf_length < 0.34:
		_fails.append("oak leaves have drifted back toward the bay laurel's narrow spear form")
	_finish()


func _check_courses(group: Node3D, trunks: bool) -> void:
	if group == null:
		return
	for child in group.get_children():
		var path := child as Path3D
		if path == null or path.curve == null or path.curve.point_count < 4:
			_fails.append("%s lost its editable four-point path" % child.name)
			continue
		if trunks and path.curve.get_point_position(0).y > 0.08:
			_fails.append("trunk %s no longer begins at grade" % child.name)


func _mesh_bounds(root: Node3D) -> AABB:
	var found := false
	var minimum := Vector3.ZERO
	var maximum := Vector3.ZERO
	var inverse := root.global_transform.affine_inverse()
	for child in root.find_children("*", "MeshInstance3D", true, false):
		var visual := child as MeshInstance3D
		var local_transform := inverse * visual.global_transform
		for endpoint in 8:
			var point := local_transform * visual.get_aabb().get_endpoint(endpoint)
			if not found:
				minimum = point
				maximum = point
				found = true
			else:
				minimum = minimum.min(point)
				maximum = maximum.max(point)
	return AABB(minimum, maximum - minimum) if found else AABB()


func _finish() -> void:
	if _fails.is_empty():
		print("PASS: PRP-PLANT-049 retains five low-forking trunks, twenty-three broad crown courses and a dense leaf-defined coast-live-oak silhouette")
	else:
		for failure in _fails:
			push_error("coastal_live_oak_catalog_test: " + failure)
	get_tree().quit(1 if not _fails.is_empty() else 0)
