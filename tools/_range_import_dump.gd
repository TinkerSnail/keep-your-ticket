extends Node

## Dev probe: what Godot made of the exported range GLB.
##
## Lists every direct child of the imported scene with its class, the class and
## name of anything under it, and for each concave shape its triangle count.
## Exists because the export's `-col` hints are a contract with the importer,
## and the only way to know the importer kept a name, put the body under the
## visual and gave it the whole mesh is to look. Takes another GLB as its
## argument after the tool name; the city mount is the other export.

const SOURCE := "res://assets/range_forest_distinct_background.glb"


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var source := args[1] if args.size() > 1 else SOURCE
	var scene := load(source) as PackedScene
	if scene == null:
		push_error("could not load %s" % source)
		get_tree().quit(1)
		return
	var root := scene.instantiate()
	add_child(root)
	var bodies := 0
	var shapes := 0
	var tris := 0
	var meshes := 0
	var surfaces := 0
	for child in root.get_children():
		var line := "%-48s %s" % [child.name, child.get_class()]
		if child is MeshInstance3D and (child as MeshInstance3D).mesh != null:
			meshes += 1
			surfaces += (child as MeshInstance3D).mesh.get_surface_count()
			line += "  surfaces=%d" % (child as MeshInstance3D).mesh.get_surface_count()
		for under in child.find_children("*", "", true, false):
			line += "  > %s:%s" % [under.get_class(), under.name]
			if under is StaticBody3D:
				bodies += 1
			if under is CollisionShape3D:
				shapes += 1
				var shape := (under as CollisionShape3D).shape
				if shape is ConcavePolygonShape3D:
					var n := (shape as ConcavePolygonShape3D).get_faces().size() / 3
					tris += n
					line += "(%d tris)" % n
		print(line)
	print("children %d  mesh_instances %d  surfaces %d  bodies %d  shapes %d  collision_triangles %d" % [
		root.get_child_count(), meshes, surfaces, bodies, shapes, tris])
	get_tree().quit()
