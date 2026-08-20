extends Node

## Test: is everybody standing on the floor of the section they are in?
##
## **Written failing.** The terraces are the first ground in the park that is not
## one plane — the climb rises twelve metres from the forecourt to terrace two —
## and `guest.gd` flattened `to_target` before it steered and then never took the
## height at all, so a guest kept whatever y they were put down at for their
## whole visit. What that looks like from the belvedere is a family walking
## straight through the cascade's steps instead of up them, and from the
## forecourt it is two people out over your head with nothing under them.
##
## Nothing else in the tree could have reported it. `walk_test` drives the
## *player*, who has gravity; `day_test` counts heads and never asks where they
## are; `coplanar_test` has no opinion about a body six metres from the floor;
## and every screenshot of the east is taken from the axis, where a guest inside
## the monument is simply a guest you cannot see.
##
## The assertion is the crowd's own graph. Every node up there carries a real
## height, so the surface somebody should be standing on is the graph's edges —
## which makes the test independent of the geometry: it does not know what a
## cascade is, only that people walk on the routes the crowd was given.
##
## It runs on all three sections rather than on the one that broke, because the
## plaza and the boardwalk are what say the check is honest — both are flat, so
## both should read zero everywhere, and a tolerance that fails them is a
## tolerance measuring its own arithmetic.

const SECTIONS: Array[StringName] = [&"plaza", &"boardwalk", &"terraces"]

## Sampled over time rather than at an instant, for `inpool_test`'s reason: a
## guest is only mid-leg for part of their walk, and one look can prove a bug
## exists and can never show it gone.
const WATCH_SECONDS := 10.0
const SETTLE_FRAMES := 90

## How far off the floor a guest may stand.
##
## A riser on the climb is 0.25m and a flight is 1.5m, so this is inside the
## thing being measured: three quarters of a metre is a step or two, and the bug
## it was written for was six metres. What spends the slack is one case, and it
## is worth knowing because it is the floor on how tight this can be made. A
## follower takes their height from the nearest point on their leader's own
## trail, and a guest keeping station a metre to the side of somebody climbing a
## flight can have their nearest point most of a stride further up it — so they
## stand at the height of the tread beside them rather than the one under them.
## Measured at 0.58m, once, in 16,800 samples.
const TOLERANCE := 0.75

## **How far a route may be and still be the one somebody is standing on.**
##
## Guests are not on their route and are not meant to be: `_wander` offsets a
## node by about half a metre, separation shoves people about, and a follower
## keeps station up to a metre to one side. So the question this asks is not
## "which edge is nearest" but "is there a route near you whose height you are
## at" — and that distinction is not pedantry, it is the cascade's wings. They
## are a hairpin whose two legs pass 4m apart with 3m of height between them, so
## a guest drifting off the upper leg is, at some point, nearer the lower one in
## plan while standing at the upper one's height. Nearest-in-plan calls that a
## three metre error. It is not one: they are on the upper leg, a stride wide of
## it. What *would* still fail is somebody at neither height, which is what
## walking through the flights looks like.
##
## Being wide of a route at all is a real thing to want to measure and this does
## not measure it. That is a separation question and it wants its own test.
const NEAR := 3.0

var _fails: Array[String] = []


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame
	ParkClock.running = false

	for id in SECTIONS:
		await _measure(id)

	print("")
	if _fails.is_empty():
		print("PASS everybody is on the floor")
		get_tree().quit()
		return
	for f in _fails:
		print("FAIL: %s" % f)
	get_tree().quit(1)


func _measure(id: StringName) -> void:
	if ParkSections.current() != id:
		# Straight in, the same as `day_test` — whether the seam works is
		# `section_test`'s question and it already passes.
		await ParkSections.enter(id, ParkSections.current())
		for i in SETTLE_FRAMES:
			await get_tree().physics_frame
		ParkClock.running = false

	var crowd := get_tree().get_first_node_in_group("crowd")
	if crowd == null:
		_fails.append("%s: no crowd in the tree" % id)
		return

	var nodes: PackedVector3Array = crowd.get("nodes")
	var edges: PackedInt32Array = crowd.get("edges")
	if nodes.is_empty() or edges.is_empty():
		_fails.append("%s: crowd has no graph" % id)
		return

	print("")
	print("=== %s ===" % ParkSections.section_name(id))

	var worst := {}
	var peak := 0.0
	var samples := 0
	# Two hours rather than one: the crowd the hour admits is a different set of
	# people, and on the terraces the groups that start high are not the groups
	# that start at the gate.
	for hour in [13, 18]:
		ParkClock.set_clock(hour, 0)
		for i in SETTLE_FRAMES:
			await get_tree().physics_frame
		var elapsed := 0.0
		while elapsed < WATCH_SECONDS:
			await get_tree().physics_frame
			elapsed += get_physics_process_delta_time()
			for g in get_tree().get_nodes_in_group("guest"):
				if not g.is_inside_tree() or not g.visible:
					continue
				var at: Vector3 = g.global_position
				var found := _nearest_floor(nodes, edges, at)
				if found.is_empty():
					continue
				samples += 1
				var off: float = absf(at.y - float(found["y"]))
				peak = maxf(peak, off)
				if off <= TOLERANCE:
					continue
				if float(worst.get(g.name, [0.0])[0]) >= off:
					continue
				worst[g.name] = [off, at, found,
					String(g.get("leader_path")), (g.get("_waypoints") as Array).size()]

	print("%d guest-frames sampled, worst height off the floor: %.2fm" % [samples, peak])
	if worst.is_empty():
		print("nobody more than %.2fm off the floor" % TOLERANCE)
		return
	var names: Array = worst.keys()
	names.sort()
	for n in names:
		var w: Array = worst[n]
		var at: Vector3 = w[1]
		var f: Dictionary = w[2]
		_fails.append("%s: %s stood %.2fm off the floor at (%.1f, %.2f, %.1f) — "
			% [id, n, w[0], at.x, at.y, at.z]
			+ "nearest floor %.2f on node %d-%d, %.2fm wide of it; leader=%s waypoints=%d"
			% [f["y"], f["a"], f["b"], f["d"],
				"none" if String(w[3]) == "" else w[3], w[4]])


## The floor under `at`: the height of the graph edge that best explains where
## this guest is standing.
##
## Every edge within `NEAR` in plan is a candidate and the one whose height is
## closest to theirs wins, because a guest wide of a route is still on it. If
## nothing is within `NEAR` the plan-nearest edge answers instead, so somebody
## out in the middle of nowhere is measured against the route they left rather
## than excused.
func _nearest_floor(nodes: PackedVector3Array, edges: PackedInt32Array,
		at: Vector3) -> Dictionary:
	var here := Vector2(at.x, at.z)
	var near := {}
	var near_off := INF
	var far := {}
	var far_d := INF
	var pairs := edges.size() / 2
	for p in pairs:
		var ia := edges[p * 2]
		var ib := edges[p * 2 + 1]
		if ia < 0 or ib < 0 or ia >= nodes.size() or ib >= nodes.size():
			continue
		var a: Vector3 = nodes[ia]
		var b: Vector3 = nodes[ib]
		var pa := Vector2(a.x, a.z)
		var span := Vector2(b.x, b.z) - pa
		var t := 0.0
		if span.length_squared() > 0.000001:
			t = clampf((here - pa).dot(span) / span.length_squared(), 0.0, 1.0)
		var d := here.distance_to(pa + span * t)
		var y := lerpf(a.y, b.y, t)
		if d < far_d:
			far_d = d
			far = {"y": y, "a": ia, "b": ib, "d": d}
		if d > NEAR:
			continue
		var off := absf(at.y - y)
		if off >= near_off:
			continue
		near_off = off
		near = {"y": y, "a": ia, "b": ib, "d": d}
	return near if not near.is_empty() else far
