@tool
extends Node3D

## The yard stairs' editor source (see this scene's description). In the editor
## only, this draws each element of each stair as an outline at its width and
## levels, so a course reads while its markers are dragged: walks white, the
## crossing yellow, landings cyan, flights orange, the bridge magenta. The stairs
## themselves are built by the generator from the same markers
## (`scripts/yard_connections_source.gd`). The preview has no owner, so it is
## never saved, and nothing runs in the game.

const Source = preload("res://scripts/yard_connections_source.gd")
const COLOURS := {
	&"walk": Color(1.0, 1.0, 1.0), &"crossing": Color(1.0, 0.85, 0.1),
	&"landing": Color(0.2, 0.9, 1.0), &"flight": Color(1.0, 0.5, 0.1),
	&"bridge": Color(1.0, 0.3, 0.9),
}

var _preview: MeshInstance3D
var _drawn := ""


func _ready() -> void:
	set_process(Engine.is_editor_hint())


func _process(_delta: float) -> void:
	# Read the markers again only when one of them, or an element, changed, so a
	# course left half-edited reports once rather than every frame.
	var parts := PackedStringArray()
	_key(self, parts)
	var key := "\n".join(parts)
	if key == _drawn:
		return
	_drawn = key
	var records := Source.records(self)
	if _preview == null:
		_preview = MeshInstance3D.new()
		_preview.name = "editor_preview"
		var material := StandardMaterial3D.new()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.vertex_color_use_as_albedo = true
		material.no_depth_test = true
		_preview.material_override = material
		_preview.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_preview)
	var mesh := ImmediateMesh.new()
	mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	for record in records:
		for element in record["elements"]:
			var a: Vector3 = element["p"][0]
			var b: Vector3 = element["p"][1]
			var along := Vector3(b.x - a.x, 0.0, b.z - a.z).normalized()
			var across := Vector3(-along.z, 0.0, along.x) * float(element["w"]) * 0.5
			mesh.surface_set_color(COLOURS.get(StringName(element["kind"]), Color.WHITE))
			for pair in [[a, b], [a + across, b + across], [a - across, b - across],
					[a - across, a + across], [b - across, b + across]]:
				mesh.surface_add_vertex(pair[0])
				mesh.surface_add_vertex(pair[1])
	mesh.surface_end()
	_preview.mesh = mesh


func _key(node: Node, parts: PackedStringArray) -> void:
	for child in node.get_children():
		if child == _preview or not child is Node3D:
			continue
		var metas := {}
		for meta_name in child.get_meta_list():
			metas[meta_name] = child.get_meta(meta_name)
		parts.append("%s %s %s" % [child.get_path(), (child as Node3D).transform, metas])
		_key(child, parts)
