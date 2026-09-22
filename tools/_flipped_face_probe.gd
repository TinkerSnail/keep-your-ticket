extends SceneTree

## Dev probe: terrain triangles wound to face down, which back-face culling
## draws as holes from above: where they are, by mesh, clustered to 50m cells.


func _init() -> void:
	var ground: Node = load("res://scenes/world/generated/park_groundworks.tscn").instantiate()
	for body in ground.get_children():
		for mi in body.find_children("*", "MeshInstance3D", true, false):
			var faces: PackedVector3Array = mi.mesh.get_faces()
			var cells := {}
			for f in range(0, faces.size(), 3):
				var n: Vector3 = (faces[f + 2] - faces[f]).cross(faces[f + 1] - faces[f])
				if n.y < 0.0:
					var c := (faces[f] + faces[f + 1] + faces[f + 2]) / 3.0
					var key := Vector2i(floori(c.x / 50.0) * 50, floori(c.z / 50.0) * 50)
					if not cells.has(key):
						cells[key] = {"n": 0, "area": 0.0, "eg": c, "ny": 0.0}
					cells[key]["n"] += 1
					cells[key]["area"] += n.length() * 0.5
					cells[key]["ny"] = minf(cells[key]["ny"], n.normalized().y)
			for key in cells:
				print("%s cell %s: %d tris, %.1fm2, steepest ny %.2f, e.g. %s" % [body.name, key,
					cells[key]["n"], cells[key]["area"], cells[key]["ny"], cells[key]["eg"]])
	quit()
