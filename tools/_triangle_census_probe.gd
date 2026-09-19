extends Node

## Dev probe: where the world's triangles are, without drawing anything.
## Sums the faces of every visible MeshInstance3D and CSG root under each child
## of `park_world`'s groups, then breaks the coastal planting down by material.
## Headless. A triangle here is drawn once in the main pass and again in each
## shadow split that sees it.


func _ready() -> void:
	var main := (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(main)
	for i in 12:
		await get_tree().process_frame
	var rows: Array = []
	var total := 0
	for group in ["park_world/places", "park_world/shared", "park_world/crowds", "park_world"]:
		for child in main.get_node(group).get_children():
			if child.name in ["places", "shared", "crowds"]:
				continue
			var n := _triangles(child, {})
			total += n
			rows.append([n, "%s/%s" % [group.get_file(), child.name]])
	rows.sort_custom(func(a, b): return a[0] > b[0])
	print("world triangles %d" % total)
	for row in rows.slice(0, 12):
		print("  %9d  %4.1f%%  %s" % [row[0], 100.0 * row[0] / total, row[1]])
	for path in ["park_world/places/park_approach/authored_additions",
			"park_world/places/boardwalk/authored_additions"]:
		var by_material := {}
		var n := _triangles(main.get_node(path), by_material)
		print("%s  %d triangles" % [path, n])
		var mats: Array = []
		for key in by_material:
			mats.append([by_material[key], key])
		mats.sort_custom(func(a, b): return a[0] > b[0])
		for m in mats.slice(0, 14):
			print("  %9d  %s" % m)
	get_tree().quit()


func _triangles(root: Node, by_material: Dictionary) -> int:
	var count := 0
	for n in [root] + root.find_children("*", "", true, false):
		var mi := n as MeshInstance3D
		if mi != null and mi.mesh != null and mi.is_visible_in_tree():
			for s in mi.mesh.get_surface_count():
				var arrays := mi.mesh.surface_get_arrays(s)
				var tris := 0
				if arrays[Mesh.ARRAY_INDEX] != null:
					tris = (arrays[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
				else:
					tris = (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
				count += tris
				var material := mi.get_active_material(s)
				var label := "(none)"
				if material != null:
					label = material.resource_name if material.resource_name != "" \
						else material.resource_path.get_file()
				by_material[label] = int(by_material.get(label, 0)) + tris
		var csg := n as CSGShape3D
		if csg != null and csg.is_root_shape() and csg.is_visible_in_tree():
			var meshes := csg.get_meshes()
			if meshes.size() > 1 and meshes[1] != null:
				count += (meshes[1] as Mesh).get_faces().size() / 3
	return count
