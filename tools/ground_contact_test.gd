extends Node

## Test: every moving guest has real world collision immediately underfoot.
##
## `climb_test.gd` compares a guest with the crowd graph. That proves the guest
## followed the route it was assigned, but the graph and the generated ground
## can still be wrong together. This test asks the physics world instead. It is
## deliberately sampled over time and at two busy hours so followers, arrivals,
## departures and both flat and graded crowds all take a turn.
##
## **A seated guest stands on the floor under the seat with the body raised to
## `seat_height`**, so the first surface above their feet is the seat: that is
## what is checked for them, which keeps real collision under every seat. A
## wheelchair user's seat is their own, so they are checked like anybody else.
##
## **Every failure is reported, grouped by the surface hit.** This used to print
## the first 80 of its sorted messages, which were all one guest's, on the east
## cascade's wings. On 2026-09-25 the rest turned out to be 70,000 samples in
## places nobody had read, seated guests among them.

const HOURS := [13, 18]
const SETTLE_FRAMES := 90
const WATCH_SECONDS := 10.0
const MAX_GAP := 0.18
const RAY_ABOVE := 1.2
const RAY_BELOW := 24.0
const WORLD_LAYER := 1

## Surface name -> {n, gmin, gmax, lo, hi, crowds, example}.
var _fails := {}


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame
	ParkClock.running = false

	var worst_gap := 0.0
	var samples := 0
	var failed := 0
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
					failed += 1
					_record("(no floor)", INF, at, guest)
					continue
				var expected := 0.0
				if guest.is_seated() and not guest.wheelchair:
					expected = -float(guest.seat_height)
				var gap := at.y - float(hit["position"].y) - expected
				worst_gap = maxf(worst_gap, absf(gap))
				if absf(gap) <= MAX_GAP:
					continue
				failed += 1
				_record(String((hit["collider"] as Node).name), gap, at, guest)

	print("%d guest-ground samples; worst physical gap %.3fm" % [samples, worst_gap])
	if _fails.is_empty():
		print("PASS every visible guest is on physical ground")
		get_tree().quit()
		return
	var names := _fails.keys()
	names.sort_custom(func(a, b): return _fails[a]["n"] > _fails[b]["n"])
	for surface in names:
		var f: Dictionary = _fails[surface]
		var lo: Vector3 = f["lo"]
		var hi: Vector3 = f["hi"]
		var crowds: Array = (f["crowds"] as Dictionary).keys()
		crowds.sort()
		print("FAIL: %d samples on %s, gap %+.2f..%+.2fm, x %.0f..%.0f z %.0f..%.0f, %s, e.g. %s" % [
			f["n"], surface, f["gmin"], f["gmax"], lo.x, hi.x, lo.z, hi.z,
			", ".join(crowds), f["example"]])
	print("FAIL: %d of %d samples on %d surfaces" % [failed, samples, names.size()])
	get_tree().quit(1)


func _record(surface: String, gap: float, at: Vector3, guest: Node) -> void:
	if not _fails.has(surface):
		_fails[surface] = {"n": 0, "gmin": INF, "gmax": -INF, "lo": at, "hi": at,
			"crowds": {}, "example": "%s/%s at (%.2f, %.2f, %.2f)" % [
				guest.get_parent().name, guest.name, at.x, at.y, at.z]}
	var f: Dictionary = _fails[surface]
	f["n"] += 1
	if is_finite(gap):
		f["gmin"] = minf(f["gmin"], gap)
		f["gmax"] = maxf(f["gmax"], gap)
	f["lo"] = (f["lo"] as Vector3).min(at)
	f["hi"] = (f["hi"] as Vector3).max(at)
	(f["crowds"] as Dictionary)[String(guest.get_parent().name)] = true
