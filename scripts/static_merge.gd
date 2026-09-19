extends RefCounted

## Collapses a subtree of still MeshInstance3Ds into one mesh per shadow
## setting, one surface per material, for the running game only.
##
## Written on 2026-09-18. The coastal palm footings are built leaf by leaf so
## each fern, blade and sprig stays an ordinary editable node: 1,478 mesh nodes
## under one arrival palm, 45,000 across the approach, every one with its own
## mesh, so nothing batched and the view south from the plaza was 73,000 draw
## calls against 8,000 looking north. They share 20 materials. The sources are
## hidden, not freed, so tests and tools that read them still find them, and
## nothing here runs in the editor: what Christina opens and edits is untouched.
##
## A caller's children may build themselves with their own deferred calls, so
## `merge_children_later` waits two frames before looking.

const MERGED := "merged_static"


static func merge_children_later(host: Node, parents: Array) -> void:
	if Engine.is_editor_hint() or not host.is_inside_tree() \
			or OS.get_environment("KYT_NO_STATIC_MERGE") != "":
		return
	await host.get_tree().process_frame
	await host.get_tree().process_frame
	for parent in parents:
		if not is_instance_valid(parent):
			continue
		for child in (parent as Node).get_children():
			if child is Node3D:
				merge(child as Node3D)


## Returns how many source nodes were folded in.
static func merge(root: Node3D) -> int:
	if Engine.is_editor_hint() or not root.is_inside_tree():
		return 0
	var inverse := root.global_transform.affine_inverse()
	# shadow setting -> material -> [tool for indexed sources, tool for plain].
	# SurfaceTool.append_from offsets a source's indices but invents none, so a
	# plain source appended after an indexed one would never be drawn.
	var groups := {}
	var sources: Array[MeshInstance3D] = []
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var source := node as MeshInstance3D
		if not _mergeable(source):
			continue
		var xform := inverse * source.global_transform
		if xform.basis.determinant() <= 0.0:
			continue
		var by_material: Dictionary = groups.get_or_add(source.cast_shadow, {})
		for s in source.mesh.get_surface_count():
			var pair: Array = by_material.get_or_add(
				source.get_active_material(s), [null, null])
			var indexed := _indexed(source.mesh, s)
			var slot := 0 if indexed else 1
			if pair[slot] == null:
				pair[slot] = SurfaceTool.new()
				(pair[slot] as SurfaceTool).begin(Mesh.PRIMITIVE_TRIANGLES)
			(pair[slot] as SurfaceTool).append_from(source.mesh, s, xform)
		sources.append(source)
	if sources.size() < 2:
		return 0
	for shadow in groups:
		var mesh := ArrayMesh.new()
		var by_material: Dictionary = groups[shadow]
		for material in by_material:
			for tool in by_material[material]:
				if tool == null:
					continue
				(tool as SurfaceTool).commit(mesh)
				mesh.surface_set_material(mesh.get_surface_count() - 1, material)
		var merged := MeshInstance3D.new()
		merged.name = "%s_%d" % [MERGED, shadow]
		merged.mesh = mesh
		merged.cast_shadow = shadow
		root.add_child(merged)
	for source in sources:
		source.visible = false
	root.set_meta("merged_sources", sources.size())
	return sources.size()


static func _indexed(mesh: Mesh, surface: int) -> bool:
	var array_mesh := mesh as ArrayMesh
	if array_mesh != null:
		return array_mesh.surface_get_format(surface) & Mesh.ARRAY_FORMAT_INDEX != 0
	return mesh.surface_get_arrays(surface)[Mesh.ARRAY_INDEX] != null


static func _mergeable(source: MeshInstance3D) -> bool:
	if source.mesh == null or not source.is_visible_in_tree() \
			or source.skin != null or String(source.name).begins_with(MERGED) \
			or source.layers != 1 or source.transparency != 0.0 \
			or source.mesh.get_surface_count() == 0:
		return false
	# Only an ArrayMesh can be anything but triangles; a PrimitiveMesh is solid.
	var array_mesh := source.mesh as ArrayMesh
	if array_mesh != null:
		for s in array_mesh.get_surface_count():
			if array_mesh.surface_get_primitive_type(s) != Mesh.PRIMITIVE_TRIANGLES:
				return false
	return source.mesh is ArrayMesh or source.mesh is PrimitiveMesh
