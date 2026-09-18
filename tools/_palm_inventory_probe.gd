extends Node

## Dev probe: what the coastal palm replacements put in the tree at runtime:
## visual nodes by class under each output group, per palm, distinct materials,
## and the same census for every other node in the world running the same
## scripts. Headless is fine; nothing is drawn.


func _ready() -> void:
	var main := (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(main)
	for i in 10:
		await get_tree().process_frame
	for node in main.find_children("*", "Node3D", true, false):
		var script := node.get_script() as Script
		if script == null:
			continue
		var file := script.resource_path.get_file()
		if file in ["coastal_palm_replacements.gd", "coastal_arrival_curb_landscaping.gd",
				"coastal_roadside_landscaping.gd"]:
			print("== %s  (%s)" % [node.get_path(), file])
			for group in node.get_children():
				_census(group, "  ")
			var crowns := node.get_node_or_null("generated_crowns")
			if crowns != null and crowns.get_child_count() > 0:
				print("  one palm:")
				for g in ["generated_crowns", "generated_trunks", "generated_bases"]:
					_census(node.get_node(g).get_child(0), "    ")
	get_tree().quit()


func _census(root: Node, indent: String) -> void:
	var by_class := {}
	var materials := {}
	var meshes := {}
	var surfaces := 0
	var scripts := {}
	for n in [root] + root.find_children("*", "", true, false):
		if n is GeometryInstance3D and (n as GeometryInstance3D).visible:
			by_class[n.get_class()] = int(by_class.get(n.get_class(), 0)) + 1
			var mi := n as MeshInstance3D
			if mi != null and mi.mesh != null:
				meshes[mi.mesh] = true
				surfaces += mi.mesh.get_surface_count()
				for s in mi.mesh.get_surface_count():
					materials[mi.get_active_material(s)] = true
		if n.get_script() != null:
			scripts[(n.get_script() as Script).resource_path.get_file()] = true
	print("%s%-28s %s  surfaces %d  distinct meshes %d  materials %d  scripts %s" % [
		indent, root.name, by_class, surfaces, meshes.size(), materials.size(), scripts.keys()])
