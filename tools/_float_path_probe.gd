extends Node

## Dev probe: `path_ground_test`'s ray under every ribbon in the persistent
## world, not only the three layers that test reads, summarised per ribbon:
## samples floating over 0.35m, the worst gap, where, and over what.

const STATION := 2.0
const EDGE_INSET := 0.6
const MAX_FLOAT := 0.35
const MAX_BURY := 0.25


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 30:
		await get_tree().physics_frame
	ParkClock.running = false
	var world := get_tree().root.find_child("park_world", true, false)
	var ribbons: Array = []
	var rids: Array[RID] = []
	for b in world.find_children("*", "StaticBody3D", true, false):
		if b.get_meta("points", PackedVector3Array()).size() >= 2:
			ribbons.append(b)
			rids.append(b.get_rid())
	var space := get_viewport().get_world_3d().direct_space_state
	for body in ribbons:
		var points: PackedVector3Array = body.get_meta("points")
		var half := maxf(float(body.get_meta("width", 0.0)) * 0.5 - EDGE_INSET, 0.0)
		var tunnels: PackedInt32Array = body.get_meta("tunnels", PackedInt32Array())
		var n := 0
		var floats := 0
		var buries := 0
		var voids := 0
		var worst := 0.0
		var worst_at := Vector3.ZERO
		var worst_over := ""
		var worst_bury := 0.0
		var bury_at := Vector3.ZERO
		var over := {}
		for i in points.size() - 1:
			var closed := false
			for k in range(0, tunnels.size(), 2):
				if i >= tunnels[k] and i < tunnels[k + 1]:
					closed = true
			if closed:
				continue
			var a := points[i]
			var b := points[i + 1]
			var steps := maxi(1, ceili(a.distance_to(b) / STATION))
			var along := b - a
			along.y = 0.0
			var side := Vector3(-along.z, 0.0, along.x).normalized() * half
			for step in steps + 1:
				var at := a.lerp(b, float(step) / float(steps))
				for offset in [Vector3.ZERO, side, -side]:
					var q: Vector3 = at + offset
					var query := PhysicsRayQueryParameters3D.create(
						q + Vector3.UP * 3.0, q - Vector3.UP * 60.0, 1)
					query.exclude = rids
					var hit := space.intersect_ray(query)
					n += 1
					if hit.is_empty():
						voids += 1
						continue
					var gap: float = q.y - float(hit["position"].y)
					var who := String(hit["collider"].name)
					if gap > MAX_FLOAT:
						floats += 1
						over[who] = int(over.get(who, 0)) + 1
						if gap > worst:
							worst = gap
							worst_at = q
							worst_over = who
					elif -gap > MAX_BURY:
						buries += 1
						if -gap > worst_bury:
							worst_bury = -gap
							bury_at = q
		var place := String(world.get_path_to(body)).get_slice("/", 1)
		print("%-26s %-16s w%.1f n%5d float %4d (worst %.2fm at %.0f,%.1f,%.0f over %s) bury %4d (worst %.2fm at %.0f,%.1f,%.0f) void %d %s" % [
			body.name, place, float(body.get_meta("width", 0.0)), n, floats, worst,
			worst_at.x, worst_at.y, worst_at.z, worst_over, buries, worst_bury,
			bury_at.x, bury_at.y, bury_at.z, voids, str(over) if floats > 0 else ""])
	get_tree().quit()
