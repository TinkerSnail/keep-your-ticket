extends Node

## Probe: a computed section along every edge of every crowd graph. For each
## edge, the height a guest walking it is given (the straight line between its
## two nodes, as `guest.gd` `_settle_height` does) against the physical floor
## under the centreline and `SIDE` metres to either side. Prints only the edges
## where some sample is more than `MAX_GAP` off, worst centreline first, with
## the surface it met. Read-only.
##
## Written 2026-09-25 for `ground_contact_test`'s failures: it separates a graph
## that disagrees with the built floor (fix the graph) from guests who stray off
## a graph that agrees with it (look at `guest.gd`).

const STEP := 0.2
const SIDE := 0.6
const MAX_GAP := 0.18


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 30:
		await get_tree().physics_frame
	var space := get_viewport().get_world_3d().direct_space_state
	for crowd in get_tree().get_nodes_in_group("crowd"):
		var nodes: PackedVector3Array = crowd.get("nodes")
		var edges: PackedInt32Array = crowd.get("edges")
		var rows := []
		for e in edges.size() / 2:
			var a := nodes[edges[e * 2]]
			var b := nodes[edges[e * 2 + 1]]
			var plan := Vector2(b.x - a.x, b.z - a.z)
			var length := plan.length()
			if length < 0.01:
				continue
			var across := Vector3(-plan.y, 0.0, plan.x) / length
			var worst := {-1: 0.0, 0: 0.0, 1: 0.0}
			var where := Vector3.ZERO
			var what := ""
			var failing := 0
			var total := 0
			var n := maxi(2, ceili(length / STEP))
			for i in n + 1:
				var on := a.lerp(b, float(i) / float(n))
				for lane in [-1, 0, 1]:
					var p: Vector3 = on + across * SIDE * lane
					var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(
						p + Vector3.UP * 1.2, p - Vector3.UP * 24.0, 1))
					var gap := 99.0 if hit.is_empty() else p.y - float(hit["position"].y)
					total += 1
					if absf(gap) > MAX_GAP:
						failing += 1
					if absf(gap) > absf(worst[lane]):
						worst[lane] = gap
						if lane == 0:
							where = p
							what = "(no floor)" if hit.is_empty() else String((hit["collider"] as Node).name)
			if failing == 0:
				continue
			rows.append([absf(worst[0]), "%3d-%3d  (%.2f, %.2f, %.2f) -> (%.2f, %.2f, %.2f)  %d/%d off  centre %+.2f at (%.1f, %.1f) on %s  sides %+.2f %+.2f" % [
				edges[e * 2], edges[e * 2 + 1], a.x, a.y, a.z, b.x, b.y, b.z, failing, total,
				worst[0], where.x, where.z, what, worst[-1], worst[1]]])
		rows.sort_custom(func(x, y): return x[0] > y[0])
		print("\n== %s: %d of %d edges have samples more than %.2fm off" % [
			crowd.get_parent().name if crowd.name == &"crowd" else crowd.name, rows.size(), edges.size() / 2, MAX_GAP])
		for r in rows:
			print(r[1])
	get_tree().quit()
