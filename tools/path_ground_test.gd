extends Node

## Test: every programmed access path stands on the ground it was laid over.
##
## `footprint_walk_test` asks whether the Player can walk a path; this asks
## whether the path is on the land. A ribbon can be walkable end to end while
## floating a metre over a hillside or lying a metre inside it, and the
## promontory walk did the first for a day: its stations were held at the pad
## height over ground that dipped to the coast, and its seaward edge stood
## over the sea-cliff skirt. Neither showed in a walk. This samples every
## access path in `park_program` at short stations, centre and both edges,
## and casts a ray straight down past the path's own collision prism to the
## first terrain body under it. A gap over `MAX_FLOAT` is a path in the air;
## terrain above the path by more than `MAX_BURY` is a path in the hill; no
## terrain at all is a path over water or over nothing.

const SETTLE_FRAMES := 30
const STATION := 2.0
const EDGE_INSET := 0.6
const MAX_FLOAT := 0.35
const MAX_BURY := 0.25
const RAY_ABOVE := 3.0
const RAY_BELOW := 40.0
const WORLD_LAYER := 1

var _fails: Array[String] = []


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame
	ParkClock.running = false
	var world := get_tree().root.find_child("park_world", true, false)
	var program: Node = world.get_node_or_null("places/park_program") if world else null
	if program == null:
		printerr("FAIL: the persistent world has no park_program layer")
		get_tree().quit(1)
		return
	var filters := OS.get_cmdline_user_args().slice(1)
	var space := get_viewport().get_world_3d().direct_space_state
	var paths := 0
	var samples := 0
	var worst_float := 0.0
	var worst_bury := 0.0
	for body in program.find_children("*", "StaticBody3D", true, false):
		var points: PackedVector3Array = body.get_meta("points", PackedVector3Array())
		if points.size() < 2:
			continue
		if not filters.is_empty():
			var keep := false
			for f in filters:
				if String(body.name).findn(String(f)) != -1:
					keep = true
			if not keep:
				continue
		paths += 1
		var half := float(body.get_meta("width", 0.0)) * 0.5 - EDGE_INSET
		var own := [body.get_rid()]
		for i in points.size() - 1:
			var a := points[i]
			var b := points[i + 1]
			var steps := maxi(1, ceili(a.distance_to(b) / STATION))
			var along := (b - a)
			along.y = 0.0
			var side := Vector3(-along.z, 0.0, along.x).normalized() * maxf(half, 0.0)
			for step in steps + 1:
				var at := a.lerp(b, float(step) / float(steps))
				for offset_v in [Vector3.ZERO, side, -side]:
					var offset: Vector3 = offset_v
					var q: Vector3 = at + offset
					var query := PhysicsRayQueryParameters3D.create(
						q + Vector3.UP * RAY_ABOVE, q - Vector3.UP * RAY_BELOW, WORLD_LAYER)
					query.exclude = own
					var hit := space.intersect_ray(query)
					samples += 1
					if hit.is_empty():
						_fails.append("%s at (%.1f, %.1f, %.1f) has no ground under it" % [
							body.name, q.x, q.y, q.z])
						continue
					var gap: float = q.y - float(hit["position"].y)
					if gap > MAX_FLOAT:
						worst_float = maxf(worst_float, gap)
						_fails.append("%s at (%.1f, %.1f, %.1f) floats %.2fm over %s" % [
							body.name, q.x, q.y, q.z, gap, String(hit["collider"].name)])
					elif -gap > MAX_BURY:
						worst_bury = maxf(worst_bury, -gap)
						_fails.append("%s at (%.1f, %.1f, %.1f) is %.2fm inside %s" % [
							body.name, q.x, q.y, q.z, -gap, String(hit["collider"].name)])
	print("%d access paths, %d ground samples; worst float %.2fm, worst bury %.2fm" % [
		paths, samples, worst_float, worst_bury])
	if _fails.is_empty():
		print("PASS every access path stands on the ground")
		get_tree().quit()
		return
	var unique := {}
	for failure in _fails:
		unique[failure] = true
	var messages: Array = unique.keys()
	messages.sort()
	for i in mini(messages.size(), 60):
		print("FAIL: %s" % messages[i])
	if messages.size() > 60:
		print("FAIL: ... %d more" % (messages.size() - 60))
	get_tree().quit(1)
