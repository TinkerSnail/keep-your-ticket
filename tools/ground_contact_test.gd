extends Node

## Test: every moving guest has real world collision immediately underfoot.
##
## `climb_test.gd` compares a guest with the crowd graph. That proves the guest
## followed the route it was assigned, but the graph and the generated ground
## can still be wrong together. This test asks the physics world instead. It is
## deliberately sampled over time and at two busy hours so followers, arrivals,
## departures and both flat and graded crowds all take a turn.

const HOURS := [13, 18]
const SETTLE_FRAMES := 90
const WATCH_SECONDS := 10.0
const MAX_GAP := 0.18
const RAY_ABOVE := 1.2
const RAY_BELOW := 24.0
const WORLD_LAYER := 1

var _fails: Array[String] = []


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame
	ParkClock.running = false

	var worst_gap := 0.0
	var samples := 0
	for hour in HOURS:
		ParkClock.set_clock(hour, 0)
		for i in SETTLE_FRAMES:
			await get_tree().physics_frame
		var elapsed := 0.0
		while elapsed < WATCH_SECONDS:
			await get_tree().physics_frame
			elapsed += get_physics_process_delta_time()
			var space := get_viewport().get_world_3d().direct_space_state
			for guest in get_tree().get_nodes_in_group("guest"):
				if not guest.is_inside_tree() or not guest.visible:
					continue
				var at: Vector3 = guest.global_position
				var query := PhysicsRayQueryParameters3D.create(
					at + Vector3.UP * RAY_ABOVE,
					at - Vector3.UP * RAY_BELOW,
					WORLD_LAYER)
				query.collide_with_areas = false
				query.collide_with_bodies = true
				var hit := space.intersect_ray(query)
				samples += 1
				if hit.is_empty():
					_fails.append("%s at (%.2f, %.2f, %.2f) has no world floor" % [
						guest.name, at.x, at.y, at.z])
					continue
				var gap := at.y - float(hit["position"].y)
				worst_gap = maxf(worst_gap, absf(gap))
				if absf(gap) <= MAX_GAP:
					continue
				_fails.append("%s at (%.2f, %.2f, %.2f) is %.2fm from %s at %.2f" % [
					guest.name, at.x, at.y, at.z, gap,
					String(hit["collider"].name), float(hit["position"].y)])

	print("%d guest-ground samples; worst physical gap %.3fm" % [samples, worst_gap])
	if _fails.is_empty():
		print("PASS every visible guest is on physical ground")
		get_tree().quit()
		return
	# Keep the output useful when one persistent fault appears on every frame.
	var unique := {}
	for failure in _fails:
		unique[failure] = true
	var messages: Array = unique.keys()
	messages.sort()
	for i in mini(messages.size(), 80):
		print("FAIL: %s" % messages[i])
	if messages.size() > 80:
		print("FAIL: ... %d additional unique contacts" % (messages.size() - 80))
	get_tree().quit(1)
