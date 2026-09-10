extends RefCounted

## Reader for the eight editor-owned horizontal section layouts.
##
## Every coordinate comes from a Marker3D saved in an ordinary Godot scene.
## The HTML atlas is a review surface; construction reads these scenes. Values
## remain in rebuild source space until ParkPlan applies its one expansion.

const SECTION_IDS := [
	&"entrance", &"plaza", &"boardwalk", &"fairground",
	&"high_terrace", &"frontier", &"grove", &"headland",
]


static func path_for(section_id: StringName) -> String:
	return "res://scenes/world/%s_layout.tscn" % section_id


static func instantiate(section_id: StringName) -> Node3D:
	assert(section_id in SECTION_IDS, "unknown park section layout %s" % section_id)
	var root := load(path_for(section_id)).instantiate() as Node3D
	assert(root != null, "%s layout source did not instantiate" % section_id)
	assert(root.get_meta("coordinate_space", "") == "rebuild_source_before_expansion",
		"%s layout source has the wrong coordinate space" % section_id)
	return root


static func records(group_name: StringName) -> Array:
	var out: Array = []
	for section_id in SECTION_IDS:
		var root := instantiate(section_id)
		var group := root.get_node_or_null(String(group_name))
		if group != null:
			for source in group.get_children():
				out.append(_record(source, root))
		root.free()
	return out


static func section_records(section_id: StringName, group_name: StringName) -> Array:
	var root := instantiate(section_id)
	var out: Array = []
	var group := root.get_node_or_null(String(group_name))
	if group != null:
		for source in group.get_children():
			out.append(_record(source, root))
	root.free()
	return out


static func find_record(group_name: StringName, record_id: StringName) -> Dictionary:
	for record in records(group_name):
		if StringName(record["id"]) == record_id:
			return record
	return {}


static func _record(source: Node, root: Node3D) -> Dictionary:
	var out := {"id": StringName(source.name)}
	for meta_name in source.get_meta_list():
		if StringName(meta_name) in [&"point_type", &"section"]:
			continue
		out[String(meta_name)] = source.get_meta(meta_name)
	var point_type := StringName(source.get_meta("point_type", "vector2"))
	for child in source.get_children():
		if child is Marker3D:
			out[String(child.name)] = _marker_value(child, root, point_type)
		elif child is Node3D:
			var values: Array = []
			for marker in child.get_children():
				if marker is Marker3D:
					values.append(_marker_value(marker, root, point_type))
			out[String(child.name)] = values
	return out


static func _marker_value(marker: Node3D, root: Node3D,
		point_type: StringName) -> Variant:
	var transform := marker.transform
	var parent := marker.get_parent()
	while parent is Node3D and parent != root:
		transform = (parent as Node3D).transform * transform
		parent = parent.get_parent()
	assert(parent == root, "%s is not inside its section source root" % marker.name)
	var p := transform.origin
	if point_type == &"vector3":
		return Vector3(p.x, p.y, p.z)
	return Vector2(p.x, p.z)
