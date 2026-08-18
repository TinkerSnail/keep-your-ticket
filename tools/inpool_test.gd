extends Node

## Test: is anybody standing in the fountain?
##
## Rim sitters are placed at radius 8.66, which is *inside* `FOUNTAIN_RADIUS` —
## deliberately, because that is where the coping is. That makes "no guest
## inside radius 9" the wrong assertion and "no guest over the water" the right
## one: the pool's surface runs out to 8.26, so anybody whose body is inside
## that is standing in it.
##
## **It was written failing and it passes now**, which is why it is a test rather
## than a probe. What it was written to pin down: three guests per run walked
## over the water, and all three were *followers* — `leader=../guest_NN`, zero
## waypoints, full speed. A follower does not route, it steers straight at its
## leader's current position, so when the leader rounded the fountain on the ring
## walkway the follower took the chord and cut through the middle of it.
##
## Nothing else catches that, and that has not changed. `_validate_graph` checks
## every *edge* against the fountain circle and the graph is clean; the guests
## going through it are the ones not using it. So the assertion is worth keeping
## standing even though it is green: the closest approach it measures is 8.66 at
## the two busy hours, which is the rim sitters and nobody else, and 10.21 at
## noon. The margin over the water's 8.26 is 40cm, and a follower taking a chord
## again would spend it immediately.
##
## Renamed out of `_inpool_probe` when it went green. The `_` prefix was the
## project's mark for a throwaway written for one question; this one outlived its
## question.
const WATER_R := 8.26

func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run()

## **Sampled continuously, not once per clock.** The first version looked at a
## single instant at each of three hours and reported three offenders one run and
## none the next — a follower is only mid-chord for part of its walk, so an
## instant sample can prove the bug exists and can never show it gone. Twelve
## seconds a clock at sixty frames is seven hundred looks instead of one.
const WATCH_SECONDS := 12.0


func _run() -> void:
	ParkClock.running = false
	var bad := 0
	var seen := 0
	for hour in [12, 16, 19]:
		ParkClock.set_clock(hour, 0)
		await get_tree().create_timer(4.0).timeout
		var closest := 999.0
		var worst := {}
		var elapsed := 0.0
		while elapsed < WATCH_SECONDS:
			await get_tree().physics_frame
			elapsed += get_physics_process_delta_time()
			for g in get_tree().get_nodes_in_group("guest"):
				if not g.is_inside_tree() or not g.visible:
					continue
				seen += 1
				var r := Vector2(g.global_position.x, g.global_position.z).length()
				closest = minf(closest, r)
				if r >= WATER_R:
					continue
				bad += 1
				var seat = g.get("seat_at")
				var sr := 0.0
				if seat != null:
					var sv: Vector3 = seat
					sr = Vector2(sv.x, sv.z).length()
				# One line per offender per clock, not per frame: the frame
				# spam buried the one number that mattered.
				if worst.get(g.name, 999.0) <= r:
					continue
				worst[g.name] = r
				var lp = g.get("leader_path")
				var lr := -1.0
				var trail := -1
				var ld: Node = g.get_node_or_null(String(lp)) if String(lp) != "" else null
				if ld != null:
					lr = Vector2(ld.global_position.x, ld.global_position.z).length()
					var t = ld.get("_trail")
					if t != null:
						trail = (t as PackedVector3Array).size()
				var station := Vector3.INF
				var fo = g.get("follow_offset")
				if ld != null and ld.has_method("trail_station") and fo != null:
					var f: Vector3 = fo
					station = ld.call("trail_station", f.z, f.x)
				var off := 0.0
				if station != Vector3.INF:
					off = Vector2(station.x - g.global_position.x,
						station.z - g.global_position.z).length()
				print("FAIL %02d:00 %-9s r=%.2f  leader r=%.2f trail=%d  "
					% [hour, g.name, r, lr, trail]
					+ "station r=%.2f, %.2fm from them  seated=%s wait=%s"
					% [Vector2(station.x, station.z).length(), off,
					str(g.get("_seated")), str(g.get("_wait"))])
		print("%02d:00 closest any guest came to the middle over %.0fs: r=%.2f "
			% [hour, WATCH_SECONDS, closest]
			+ "(water ends at %.2f, coping at 9.00)" % WATER_R)
	print("%d guest-frames sampled" % seen)
	print("PASS nobody in the pool" if bad == 0 else "FAIL %d guest-frames over the water" % bad)
	get_tree().quit(0 if bad == 0 else 1)
