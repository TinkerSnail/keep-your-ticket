extends Node

## Dev probe: what the coastal palms and the arrival and roadside landscaping
## put in the tree at runtime. For each palm set (`coastal_palm_set.gd`): its
## trunks, crowns and beds summed over every palm, then one palm's. For each
## landscaping builder: each of its output groups. Every line counts visible
## nodes by class, surfaces, distinct meshes and materials, and names the
## scripts it met, so it shows whether `scripts/static_merge.gd` ran. Headless
## is fine; nothing is drawn.

## The parts `coastal_palm.gd` builds under each palm.
const PALM_PARTS := ["trunk", "crown", "footing"]


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
		if file == "coastal_palm_set.gd":
			print("== %s  (%s, %d palms)" % [node.get_path(), file, node.get_child_count()])
			for part in PALM_PARTS:
				var roots := []
				for palm in node.get_children():
					var found := palm.get_node_or_null(part)
					if found != null:
						roots.append(found)
				_census(roots, "%s x%d" % [part, roots.size()], "  ")
			if node.get_child_count() > 0:
				var palm := node.get_child(0)
				print("  one palm, %s:" % palm.name)
				for part in PALM_PARTS:
					var found := palm.get_node_or_null(part)
					if found != null:
						_census([found], part, "    ")
		elif file in ["coastal_arrival_curb_landscaping.gd", "coastal_roadside_landscaping.gd"]:
			print("== %s  (%s)" % [node.get_path(), file])
			for group in node.get_children():
				_census([group], group.name, "  ")
	get_tree().quit()


## One line for everything under `roots` together.
func _census(roots: Array, label: String, indent: String) -> void:
	var by_class := {}
	var materials := {}
	var meshes := {}
	var surfaces := 0
	var scripts := {}
	for root in roots:
		for n in [root] + (root as Node).find_children("*", "", true, false):
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
		indent, label, by_class, surfaces, meshes.size(), materials.size(), scripts.keys()])
