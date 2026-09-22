extends Node

## Dev probe: the centreline gap between named ribbons and the first ground
## under them, every ten metres: where along a route it leaves the land.


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 30:
		await get_tree().physics_frame
	var world := get_tree().root.find_child("park_world", true, false)
	var rids: Array[RID] = []
	var ribbons := {}
	for b in world.find_children("*", "StaticBody3D", true, false):
		if b.get_meta("points", PackedVector3Array()).size() >= 2:
			rids.append(b.get_rid())
			ribbons[String(b.name)] = b
	var space := get_viewport().get_world_3d().direct_space_state
	for nm in OS.get_cmdline_user_args().slice(1):
		var pts: PackedVector3Array = ribbons[nm].get_meta("points")
		print("== ", nm)
		var run := 0.0
		var next := 0.0
		for i in pts.size() - 1:
			var seg := pts[i].distance_to(pts[i + 1])
			while next <= run + seg:
				var q := pts[i].lerp(pts[i + 1], (next - run) / maxf(seg, 0.001))
				var query := PhysicsRayQueryParameters3D.create(q + Vector3.UP * 3.0, q - Vector3.UP * 60.0, 1)
				query.exclude = rids
				var hit := space.intersect_ray(query)
				print("  s%4.0f (%6.1f,%6.1f) path %6.2f ground %6.2f gap %5.2f %s" % [next, q.x, q.z, q.y,
					hit["position"].y if hit else NAN, q.y - hit["position"].y if hit else NAN,
					hit["collider"].name if hit else "NONE"])
				next += 10.0
			run += seg
	get_tree().quit()
