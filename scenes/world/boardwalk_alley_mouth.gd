@tool
extends Node3D

## The alley mouth's editor source (see this scene's description). In the
## editor only, this draws each end's frame as it will be built, so it reads
## while its markers are dragged: the posts white, the valance yellow and the
## bulb run orange. The frames themselves are built by the generator from the
## same markers (`scripts/boardwalk_alley_mouth_source.gd`). The preview has no
## owner, so it is never saved, and nothing runs in the game.

const Source = preload("res://scripts/boardwalk_alley_mouth_source.gd")

var _preview: MeshInstance3D
var _drawn := ""


func _ready() -> void:
	set_process(Engine.is_editor_hint())


func _process(_delta: float) -> void:
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
	for record in records.values():
		var size: Vector3 = record["post_size"]
		mesh.surface_set_color(Color.WHITE)
		for foot: Vector3 in record["posts"]:
			var top := foot + Vector3.UP * size.y
			for corner in [Vector3(-1, 0, -1), Vector3(1, 0, -1), Vector3(1, 0, 1), Vector3(-1, 0, 1)]:
				var c: Vector3 = corner * Vector3(size.x, 0.0, size.z) * 0.5
				_line(mesh, foot + c, top + c)
		var a: Vector3 = record["valance"][0]
		var b: Vector3 = record["valance"][1]
		var along := Vector3(b.x - a.x, 0.0, b.z - a.z).normalized()
		var across := Vector3(along.z, 0.0, -along.x) * float(record["valance_size"].x) * 0.5
		mesh.surface_set_color(Color(1.0, 0.85, 0.1))
		for pair in [[a + across, b + across], [a - across, b - across],
				[a - across, a + across], [b - across, b + across]]:
			_line(mesh, pair[0], pair[1])
		var first: Vector3 = record["bulbs"][0]
		var last: Vector3 = record["bulbs"][1]
		var count := int(record["bulb_count"])
		var r := float(record["bulb_radius"])
		mesh.surface_set_color(Color(1.0, 0.5, 0.1))
		for i in count:
			var p := first.lerp(last, float(i) / float(count - 1)) if count > 1 \
				else (first + last) * 0.5
			for axis in [Vector3.RIGHT, Vector3.UP, Vector3.BACK]:
				_line(mesh, p - axis * r, p + axis * r)
	mesh.surface_end()
	_preview.mesh = mesh


func _line(mesh: ImmediateMesh, a: Vector3, b: Vector3) -> void:
	mesh.surface_add_vertex(a)
	mesh.surface_add_vertex(b)


func _key(node: Node, parts: PackedStringArray) -> void:
	for child in node.get_children():
		if child == _preview or not child is Node3D:
			continue
		var metas := {}
		for meta_name in child.get_meta_list():
			metas[meta_name] = child.get_meta(meta_name)
		parts.append("%s %s %s" % [child.get_path(), (child as Node3D).transform, metas])
		_key(child, parts)
