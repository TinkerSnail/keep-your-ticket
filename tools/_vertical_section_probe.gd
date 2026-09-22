extends Node

## Dev probe: every visible surface and every collision hit on a vertical line.
## Pass `x,z` pairs after the tool name. Reads the drawn meshes, not only the
## colliders, so it tells a path floating over open air from one standing on
## an earthwork that merely has no collision.


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 30:
		await get_tree().physics_frame
	var world := get_tree().root.find_child("park_world", true, false)
	var meshes: Array = world.find_children("*", "MeshInstance3D", true, false)
	var space := get_viewport().get_world_3d().direct_space_state
	for arg in OS.get_cmdline_user_args().slice(1):
		var parts := String(arg).split(",")
		var x := float(parts[0])
		var z := float(parts[1])
		print("== (%.1f, %.1f)" % [x, z])
		var rows: Array = []
		for mi in meshes:
			if mi.mesh == null or not mi.is_visible_in_tree():
				continue
			var inv: Transform3D = mi.global_transform.affine_inverse()
			var box: AABB = mi.global_transform * mi.mesh.get_aabb()
			if x < box.position.x or x > box.end.x or z < box.position.z or z > box.end.z:
				continue
			var faces: PackedVector3Array = mi.mesh.get_faces()
			var from: Vector3 = inv * Vector3(x, 200.0, z)
			var dir: Vector3 = (inv.basis * Vector3.DOWN).normalized()
			for f in range(0, faces.size(), 3):
				var hit = Geometry3D.ray_intersects_triangle(from, dir,
					faces[f], faces[f + 1], faces[f + 2])
				if hit != null:
					var n: Vector3 = (faces[f + 2] - faces[f]).cross(faces[f + 1] - faces[f])
					n = (mi.global_transform.basis * n).normalized()
					var w: Vector3 = mi.global_transform * hit
					rows.append([w.y, "%s  ny %.2f" % [world.get_path_to(mi), n.y]])
		rows.sort_custom(func(a, b): return a[0] > b[0])
		for r in rows:
			print("   mesh y %8.3f  %s" % r)
		var top := 200.0
		var exclude: Array[RID] = []
		for k in 12:
			var q := PhysicsRayQueryParameters3D.create(Vector3(x, top, z), Vector3(x, -30.0, z), 1)
			q.exclude = exclude
			var hit := space.intersect_ray(q)
			if hit.is_empty():
				break
			print("   body y %8.3f  %s" % [hit["position"].y, world.get_path_to(hit["collider"])])
			exclude.append(hit["rid"])
	get_tree().quit()
