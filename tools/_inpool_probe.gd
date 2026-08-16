extends Node

## Dev tool: is anybody standing in the fountain?
##
## Rim sitters are placed at radius 8.66, which is *inside* `FOUNTAIN_RADIUS` —
## deliberately, because that is where the coping is. That makes "no guest
## inside radius 9" the wrong assertion and "no guest over the water" the right
## one: the pool's surface runs out to 8.26, so anybody whose body is inside
## that is standing in it.
##
## **This currently FAILS, and the failure is a real pre-existing bug it was
## written to pin down.** Three guests per run walk over the water, and all
## three turn out to be *followers*: `leader=../guest_NN`, zero waypoints,
## walking at full speed. A follower does not route — it steers straight at its
## leader's current position — so when the leader rounds the fountain on the
## ring walkway, the follower takes the chord and cuts straight through the
## middle of it.
##
## Nothing else catches that. `_validate_graph` checks every *edge* against the
## fountain circle and the graph is clean; the guests going through it are the
## ones not using it. It has nothing to do with the fountain rebuild — an 18m
## obstacle in the middle of the ring just makes the oldest chord in the plaza
## the most visible one.
##
## Leave it failing until followers either route or steer around what their
## leader went around.
const WATER_R := 8.26

func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run()

func _run() -> void:
	ParkClock.running = false
	var bad := 0
	var seen := 0
	for hour in [12, 16, 19]:
		ParkClock.set_clock(hour, 0)
		await get_tree().create_timer(7.0).timeout
		var closest := 999.0
		for g in get_tree().get_nodes_in_group("guest"):
			if not g.is_inside_tree() or not g.visible:
				continue
			seen += 1
			var r := Vector2(g.global_position.x, g.global_position.z).length()
			closest = minf(closest, r)
			if r < WATER_R:
				bad += 1
				var seat = g.get("seat_at")
				var sr := 0.0
				if seat != null:
					var sv: Vector3 = seat
					sr = Vector2(sv.x, sv.z).length()
				var lp = g.get("leader_path")
				var wps = g.get("_waypoints")
				var n := 0
				if wps != null:
					n = (wps as Array).size()
				var nxt := "-"
				if n > 0:
					nxt = "%v" % (wps as Array)[0]
				print("FAIL %02d:00 %s r=%.2f leader=%s waypoints=%d next=%s"
					% [hour, g.name, r, str(lp), n, nxt])
		print("%02d:00 closest guest to the middle: r=%.2f (water ends at %.2f, coping at 9.00)"
			% [hour, closest, WATER_R])
	print("PASS nobody in the pool" if bad == 0 else "FAIL %d" % bad)
	get_tree().quit(0 if bad == 0 else 1)
