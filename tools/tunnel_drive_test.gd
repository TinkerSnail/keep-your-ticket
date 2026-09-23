extends Node

## Can a car drive the coast highway's tunnels?
##
## Nothing in the acceptance set drives the bores. `clearance_test` checks the
## park's own routes, and `path_ground_test` rays *downward* to ask whether a
## path stands on the ground, which a tunnel passes by construction: its ground
## is the bore's floor and the hill overhead is not in the way of a downward
## ray. So eight segments where terrain closes across a carriageway sat under a
## fully green set until Christina saw one in an aerial (2026-09-22).
##
## This drives instead. For every tunnel, both bores, **both directions**, a ray
## at eye height from each station to the next: if it stops short, something
## stands in the road. Direction matters — a ray hits ground that rises ahead of
## it, so driving one way finds the entry mouths and driving the other finds the
## exits. The first probe of this ran one direction only and reported every
## blockage at an entry, which was an artifact of that.
##
## It also reports the least headroom over each carriageway, which is the other
## way a bore can be undrivable, and prints the count so it can be read against
## the standing baseline rather than only as a verdict.

const EYE := 1.5
## Stations either side of a bore, so a mouth's approach is driven too.
const PAD := 3
## A bore claims 5.20m of roof clearance; flag anything that leaves less than a
## lorry's worth.
const LOW_ROOF := 4.6
const SETTLE_FRAMES := 30
## Headroom is sampled this often along a segment, and drives and headroom at
## these offsets across the carriageway: its centre and a metre inside each edge line (the
## carriageway is 10.8m).
const HEADROOM_STEP := 1.0
const HEADROOM_ACROSS := [-4.4, 0.0, 4.4]
## Drives run at a driver's eye and at a box lorry's roof.
const DRIVE_HEIGHTS := [EYE, 4.2]

var _fails: Array[String] = []
var _low: Array[String] = []


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for _i in SETTLE_FRAMES:
		await get_tree().physics_frame
	var clock := get_node_or_null("/root/ParkClock")
	if clock != null:
		clock.running = false
	var world := get_tree().get_root().find_child("park_world", true, false)
	if world == null:
		_finish("no park_world in the tree")
		return
	var space := get_viewport().get_world_3d().direct_space_state

	var gen: Object = load("res://tools/gen_props.gd").new()
	for needed in ["_highway_stations"]:
		if not gen.has_method(needed):
			gen.free()
			_finish("gen_props has no %s" % needed)
			return
	gen.call("_highway_stations")
	var tunnels: Array = gen.get("_highway_tunnels")
	var bores := {"A": gen.get("_highway_a"), "B": gen.get("_highway_b")}
	gen.free()
	if tunnels.is_empty():
		_finish("no tunnels to drive")
		return

	var segments := 0
	for n in tunnels.size():
		var from_i: int = int(tunnels[n]["from"])
		var to_i: int = int(tunnels[n]["to"])
		for tag in ["A", "B"]:
			var bore: Array = bores[tag]
			var i0 := maxi(0, from_i - PAD)
			var i1 := mini(bore.size() - 2, to_i + PAD)
			var headroom := INF
			var headroom_at := -1
			for i in range(i0, i1 + 1):
				var a: Vector3 = bore[i]
				var b: Vector3 = bore[i + 1]
				var flat := Vector2(b.x - a.x, b.z - a.z)
				var across := Vector3(flat.y, 0.0, -flat.x).normalized()
				# Both ways down the same segment: a ray stops on ground rising
				# ahead of it, so one direction alone sees one mouth. At a
				# driver's eye and at a lorry's roof, down each lane edge as
				# well as the centre: a face hanging 2.5m over the upper bore's
				# road passed an eye-height drive on the centre line alone.
				for height in DRIVE_HEIGHTS:
					for lane in HEADROOM_ACROSS:
						var lift := Vector3.UP * float(height) + across * float(lane)
						var here: Vector3 = a + lift
						var next: Vector3 = b + lift
						for leg in [[here, next, "south"], [next, here, "north"]]:
							segments += 1
							var query := PhysicsRayQueryParameters3D.create(leg[0], leg[1], 1)
							var hit := space.intersect_ray(query)
							if hit.is_empty():
								continue
							_fails.append("tunnel %d bore %s station %d-%d driving %s at %.1fm, %+.1fm across: %s %.1fm in, at (%.1f, %.1f)" % [
								n, tag, i, i + 1, leg[2], float(height), float(lane),
								String(world.get_path_to(hit["collider"])).get_slice("/", 1)
									+ "/" + String(hit["collider"].name),
								Vector3(hit["position"]).distance_to(leg[0]),
								hit["position"].x, hit["position"].z])
				# Headroom over the whole carriageway, not only up from each
				# station on its centre line: the lid's portal face once hung
				# 2.5m over the upper bore's road between two stations and
				# passed both this check and the eye-height drive.
				var steps := maxi(1, ceili(flat.length() / HEADROOM_STEP))
				for s in steps:
					var on: Vector3 = Vector3(bore[i]).lerp(bore[i + 1], float(s) / steps)
					for lane in HEADROOM_ACROSS:
						var over := _headroom(space, on + across * float(lane))
						if over < headroom:
							headroom = over
							headroom_at = i
			if headroom < LOW_ROOF and headroom_at >= 0:
				_low.append("tunnel %d bore %s: %.2fm of headroom at station %d" % [
					n, tag, headroom, headroom_at])

	print("  %d tunnels, both bores, both directions: %d segment drives" % [
		tunnels.size(), segments])
	for line in _low:
		print("  low roof: %s" % line)
	_finish("")


## The first surface over the carriageway, or INF where a bore is open to the
## sky, which is not this test's business.
func _headroom(space: PhysicsDirectSpaceState3D, at: Vector3) -> float:
	var query := PhysicsRayQueryParameters3D.create(
		at + Vector3.UP * 0.3, at + Vector3.UP * 60.0, 1)
	var hit := space.intersect_ray(query)
	if hit.is_empty():
		return INF
	return float(hit["position"].y) - at.y


func _finish(problem: String) -> void:
	if problem != "":
		printerr("FAIL: ", problem)
		get_tree().quit(1)
		return
	if _fails.is_empty() and _low.is_empty():
		print("PASS every tunnel drives clear in both directions")
		get_tree().quit()
		return
	print("BLOCKED SEGMENTS: %d" % _fails.size())
	for line in _fails.slice(0, 40):
		print("  ", line)
	if _fails.size() > 40:
		print("  ... and %d more" % (_fails.size() - 40))
	printerr("FAIL: %d tunnel segments are blocked, %d bores have a low roof" % [
		_fails.size(), _low.size()])
	get_tree().quit(1)
