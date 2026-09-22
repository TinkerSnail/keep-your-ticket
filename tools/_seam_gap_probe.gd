extends Node

## Dev probe: what is just outside every open edge of the generated ground.
## A boundary edge is one that a single triangle uses across all groundworks
## meshes together. From three stations on each, rays drop 5, 15, 30 and 60cm
## outside the edge, from forty metres up so a surface covering the seam
## counts: nothing at all is a seam the Player falls through; ground over 0.6m
## down and nothing above is an open face. Unlike `footprint_test` this reads every
## groundworks mesh and the developed envelope too. Clustered to 40m cells.

const OFFSETS := [0.05, 0.15, 0.3, 0.6]


func _key(v: Vector3) -> Vector3i:
	return Vector3i(roundi(v.x * 200.0), roundi(v.y * 200.0), roundi(v.z * 200.0))


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 30:
		await get_tree().physics_frame
	var world := get_tree().root.find_child("park_world", true, false)
	var ground: Node = world.get_node("places/park_groundworks")
	var edges := {}
	for mi in ground.find_children("*", "MeshInstance3D", true, false):
		if mi.get_parent() is not StaticBody3D:
			continue
		var faces: PackedVector3Array = mi.mesh.get_faces()
		var xf: Transform3D = mi.global_transform
		for f in range(0, faces.size(), 3):
			for k in 3:
				var a: Vector3 = xf * faces[f + k]
				var b: Vector3 = xf * faces[f + (k + 1) % 3]
				var c: Vector3 = xf * faces[f + (k + 2) % 3]
				var ka := _key(a)
				var kb := _key(b)
				var key := [ka, kb] if ka < kb else [kb, ka]
				if edges.has(key):
					edges[key][0] += 1
				else:
					edges[key] = [1, a, b, c, String(mi.get_parent().name)]
	var space := get_viewport().get_world_3d().direct_space_state
	var cells := {}
	var open_edges := 0
	for key in edges:
		var rec: Array = edges[key]
		if rec[0] != 1:
			continue
		var a: Vector3 = rec[1]
		var b: Vector3 = rec[2]
		var c: Vector3 = rec[3]
		var plan := Vector2(b.x - a.x, b.z - a.z)
		if plan.length() < 0.3 or maxf(a.y, b.y) < -5.0:
			continue
		open_edges += 1
		var out := Vector2(-plan.y, plan.x).normalized()
		var mid := (a + b) * 0.5
		if out.dot(Vector2(c.x - mid.x, c.z - mid.z)) > 0.0:
			out = -out
		var worst := 0.0
		var kind := ""
		for t in [0.2, 0.5, 0.8]:
			var e: Vector3 = a.lerp(b, float(t))
			for off in OFFSETS:
				var p: Vector3 = e + Vector3(out.x, 0.0, out.y) * float(off)
				var q := PhysicsRayQueryParameters3D.create(p + Vector3.UP * 40.0, p - Vector3.UP * 60.0, 1)
				var hit := space.intersect_ray(q)
				if hit.is_empty():
					kind = "VOID"
					worst = 60.0
				elif kind != "VOID" and e.y - hit["position"].y > maxf(0.6, worst) \
						and hit["position"].y < e.y:
					kind = "drop"
					worst = e.y - hit["position"].y
		if kind == "":
			continue
		var cell := "%s %-30s %5d %5d" % [kind, rec[4], floori(mid.x / 40.0) * 40, floori(mid.z / 40.0) * 40]
		if not cells.has(cell):
			cells[cell] = {"n": 0, "len": 0.0, "worst": 0.0, "at": mid}
		cells[cell]["n"] += 1
		cells[cell]["len"] += a.distance_to(b)
		if worst >= cells[cell]["worst"]:
			cells[cell]["worst"] = worst
			cells[cell]["at"] = mid
	print("%d open edges examined" % open_edges)
	var keys := cells.keys()
	keys.sort()
	for cell in keys:
		var c: Dictionary = cells[cell]
		print("%s: %3d edges %6.1fm worst %5.1fm at (%.1f, %.1f, %.1f)" % [cell, c["n"], c["len"],
			c["worst"], c["at"].x, c["at"].y, c["at"].z])
	get_tree().quit()
