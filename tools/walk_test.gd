extends Node

## Dev tool: drives the real player down the entrance street and back, round the
## four scaffolded passages, and — once the seam is crossed — over every route on
## the boardwalk, probing every open edge of all of it.
##
## Pressing the actual input actions rather than setting velocity, so the run
## goes through `_physics_process` and `_try_step` exactly as a player's would.
## Teleporting the body would test the geometry and skip the controller, and on
## the west stair it was the controller that was wrong.
##
## The boardwalk legs run in a second phase, after `ParkSections.enter`, because
## a section that is not mounted has no floor and every leg in it would report
## the same thing: fell. `tools/section_test.gd` owns the crossing itself; this
## owns what is on either side of it.

const ARRIVE := 1.6
const STALL_FRAMES := 90
const MAX_SECONDS := 22.0

## How far below its own starting height a leg may take the player before it
## counts as falling. Relative, not absolute: the boardwalk's floor is at −6 and
## a fixed threshold of −3 called every leg down there a fall.
const FALL_BELOW := 3.0

var _player: CharacterBody3D
var _legs: Array = []
var _leg := 0
var _from := Vector3.ZERO
var _to := Vector3.ZERO
var _t := 0.0
var _still := 0
var _min_y := 1e9
var _last := Vector3.ZERO
var _fails: Array = []
## Whether the run has already dropped into the boardwalk. One-way: the plaza
## legs are done by then and there is nothing to go back for.
var _crossed := false


## Mount the boardwalk and queue its legs. `enter` is awaited rather than called
## and hoped at — it fades, swaps and places the player, and starting a leg
## mid-fade teleports the body out from under a transition that is still holding
## it.
func _enter_boardwalk() -> void:
	print("--- crossing to the boardwalk ---")
	await ParkSections.enter(&"boardwalk", &"plaza")
	for i in 4:
		await get_tree().physics_frame
	if ParkSections.current() != &"boardwalk":
		_fails.append("could not mount the boardwalk")
		_report()
		return
	_legs = _boardwalk_legs()
	_leg = 0
	_start_leg()


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 4:
		await get_tree().physics_frame

	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if _player == null:
		print("FAIL: no player")
		get_tree().quit(1)
		return

	# Geometry only. Guests are CharacterBody3D and push back, so a group
	# standing in the south gap reads as a blocked route when the route is fine —
	# the first run failed exactly that way. Whether the crowd congests a
	# doorway is a real question, but it is a crowd question, and answering it
	# here would also mean testing against another session's half-edited guest.
	var crowd := get_tree().get_first_node_in_group("crowd")
	if crowd != null:
		for g in crowd.guests:
			if is_instance_valid(g):
				g.queue_free()
		await get_tree().physics_frame

	# label, from, to, must_arrive
	_legs = [
		["plaza -> gap", Vector3(0, 1.2, 10), Vector3(-1.5, 1.2, 34), true],
		["gap -> mid street", Vector3(-1.5, 1.2, 34), Vector3(-1.5, 1.2, 66), true],
		["mid street -> gate", Vector3(-1.5, 1.2, 66), Vector3(-1.5, 1.2, 92), true],
		["through turnstiles", Vector3(-1.5, 1.2, 92), Vector3(-1.5, 1.2, 100), true],
		["apron -> gate", Vector3(-1.5, 1.2, 104), Vector3(-1.5, 1.2, 92), true],
		["gate -> mid street", Vector3(-1.5, 1.2, 92), Vector3(-1.5, 1.2, 60), true],
		["street -> plaza", Vector3(-1.5, 1.2, 60), Vector3(0, 1.2, 20), true],
		# Edge probes. Each must NOT arrive: something should stop the player.
		["probe west shops", Vector3(-1.5, 1.2, 55), Vector3(-30, 1.2, 55), false],
		["probe east shops", Vector3(-1.5, 1.2, 70), Vector3(28, 1.2, 70), false],
		["probe west shops far", Vector3(-1.5, 1.2, 85), Vector3(-30, 1.2, 85), false],
		# Clear of the flagpole row at z=104, which stopped the first run's probes
		# before they ever reached the walls they were aimed at.
		["probe apron west", Vector3(-1.5, 1.2, 107), Vector3(-30, 1.2, 107), false],
		["probe apron east", Vector3(-1.5, 1.2, 107), Vector3(28, 1.2, 107), false],
		["probe apron south", Vector3(-1.5, 1.2, 107), Vector3(-1.5, 1.2, 130), false],
		["probe apron sw", Vector3(-1.5, 1.2, 107), Vector3(-30, 1.2, 130), false],
		["probe apron se", Vector3(-1.5, 1.2, 107), Vector3(28, 1.2, 130), false],
		["probe street seam", Vector3(-1.5, 1.2, 41), Vector3(-30, 1.2, 41), false],
		# The arcade, which is a room you walk into rather than a scene that
		# loads. In and back out under your own power, and the back wall holds.
		["arcade in", Vector3(-6.0, 1.2, 66), Vector3(-20.0, 1.2, 66), true],
		["arcade back out", Vector3(-20.0, 1.2, 66), Vector3(-4.0, 1.2, 66), true],
		["arcade rear holds", Vector3(-20.0, 1.2, 66), Vector3(-40.0, 1.2, 66), false],
		["arcade north holds", Vector3(-20.0, 1.2, 66), Vector3(-20.0, 1.2, 50), false],
		["arcade south holds", Vector3(-20.0, 1.2, 66), Vector3(-20.0, 1.2, 82), false],
	]
	# The four scaffolded section thresholds. Head-on plus both corners, because
	# the leak in a gate is never the middle — it is the hand's width between
	# the post and the wall it was supposed to meet.
	# For each passage: walk in from the plaza and reach the bend, make the turn
	# and reach the end, then push on past the end and be stopped. The last of
	# the three is the one that matters — a passage that leaks is a hole.
	for t in [
		["nnw", Vector3(-13, 1.2, -34), Vector3(-13, 1.2, -46), Vector3(-22, 1.2, -46), Vector3(-40, 1.2, -46)],
		["ne", Vector3(34, 1.2, -21), Vector3(46, 1.2, -21), Vector3(46, 1.2, -30), Vector3(46, 1.2, -48)],
		["se", Vector3(34, 1.2, 24), Vector3(46, 1.2, 24), Vector3(46, 1.2, 33), Vector3(46, 1.2, 51)],
		["sw", Vector3(-24, 1.2, 34), Vector3(-24, 1.2, 46), Vector3(-33, 1.2, 46), Vector3(-51, 1.2, 46)],
	]:
		_legs.append(["way %s in" % t[0], t[1], t[2], true])
		_legs.append(["way %s turn" % t[0], t[2], t[3], true])
		_legs.append(["way %s holds" % t[0], t[3], t[4], false])
	_start_leg()


## The boardwalk, one section down. Eye height is the shore plus the same 1.2 the
## plaza legs use.
##
## The order is the order the player meets it, because that is the thing being
## tested: the arrival, the lane, the alley, and then the promenade in both
## directions with the pier out of the middle of it. Everything after that is a
## probe — the water, the shops, the bluff, and both ends of the strip.
func _boardwalk_legs() -> Array:
	var y := ParkPlan.SHORE_TOP + 1.2
	var arrive := Vector3(ParkPlan.BOARDWALK_ARRIVAL.x, y, ParkPlan.BOARDWALK_ARRIVAL.z)
	var alley_in := Vector3(ParkPlan.BACK_LANE_X - 3.0, y, ParkPlan.ALLEY_Z)
	var alley_out := Vector3(ParkPlan.PROMENADE_X + 5.0, y, ParkPlan.ALLEY_Z)
	var prom := Vector3(ParkPlan.PROMENADE_X + 5.0, y, ParkPlan.ALLEY_Z)
	return [
		["bw arrive -> lane", arrive, alley_in, true],
		["bw lane -> alley", alley_in, alley_out, true],
		["bw alley -> pier head", prom, Vector3(-78.0, y, ParkPlan.ALLEY_Z), true],
		["bw out the pier", Vector3(-78.0, y, ParkPlan.ALLEY_Z),
			Vector3(-121.0, y, ParkPlan.ALLEY_Z), true],
		["bw pavilion holds", Vector3(-121.0, y, ParkPlan.ALLEY_Z),
			Vector3(-134.0, y, ParkPlan.ALLEY_Z), false],
		["bw back down pier", Vector3(-121.0, y, ParkPlan.ALLEY_Z),
			Vector3(-74.0, y, ParkPlan.ALLEY_Z), true],
		# The walk north weaves, and both pinches are real. The tables outside the
		# corn-dog stand and the wheel's platform leave 4m between them; then the
		# wheel's ticket booth takes the west half of what is left. A straight
		# line up the promenade walks into one or the other, which is the same
		# route the crowd's graph threads and for the same reason.
		["bw north past tables", Vector3(-68.5, y, -4.0), Vector3(-68.5, y, -14.0), true],
		["bw past the booth", Vector3(-68.5, y, -14.0), Vector3(-66.5, y, -24.0), true],
		["bw wheel -> coaster", Vector3(-66.5, y, -24.0), Vector3(-68.0, y, -52.0), true],
		["bw north end holds", Vector3(-70.0, y, -72.0), Vector3(-70.0, y, -95.0), false],
		["bw south along strip", Vector3(-70.0, y, 10.0), Vector3(-70.0, y, 62.0), true],
		["bw south end holds", Vector3(-70.0, y, 70.0), Vector3(-70.0, y, 92.0), false],
		# Probes. None of these may arrive.
		["bw water holds", Vector3(-70.0, y, 30.0), Vector3(-92.0, y, 30.0), false],
		["bw water holds n", Vector3(-70.0, y, -50.0), Vector3(-92.0, y, -50.0), false],
		["bw shops hold", Vector3(-68.0, y, 26.0), Vector3(-48.0, y, 26.0), false],
		["bw yard holds", Vector3(-70.0, y, 70.0), Vector3(-50.0, y, 70.0), false],
		["bw coaster fence holds", Vector3(-68.0, y, -60.0), Vector3(-48.0, y, -60.0), false],
		["bw bluff holds", Vector3(-50.0, y, 20.0), Vector3(-36.0, y, 20.0), false],
		["bw well holds", Vector3(-50.0, y, -4.0), Vector3(-36.0, y, -4.0), false],
	]


func _start_leg() -> void:
	if _leg >= _legs.size():
		if not _crossed:
			_crossed = true
			_enter_boardwalk()
			return
		_report()
		return
	var leg: Array = _legs[_leg]
	_from = leg[1]
	_to = leg[2]
	_player.global_position = _from
	_player.velocity = Vector3.ZERO
	var d := _to - _from
	_player.rotation.y = atan2(-d.x, -d.z)
	_t = 0.0
	_still = 0
	_min_y = _from.y
	_last = _from
	Input.action_press("move_forward")


func _physics_process(delta: float) -> void:
	if _player == null or _leg >= _legs.size():
		return
	_t += delta
	var p := _player.global_position
	_min_y = minf(_min_y, p.y)

	if p.distance_to(_last) < 0.004:
		_still += 1
	else:
		_still = 0
	_last = p

	var flat_to := Vector3(_to.x, p.y, _to.z)
	var arrived := p.distance_to(flat_to) < ARRIVE
	var stalled := _still >= STALL_FRAMES
	var fell := p.y < _from.y - FALL_BELOW
	if arrived or stalled or fell or _t > MAX_SECONDS:
		Input.action_release("move_forward")
		_finish_leg(arrived, stalled, fell, p)


## What actually stopped us. Names beat coordinates: on the west stair the
## blocker turned out to be a piece nobody had thought about.
func _blockers() -> String:
	var seen := {}
	for i in _player.get_slide_collision_count():
		var c := _player.get_slide_collision(i)
		var o := c.get_collider()
		if o != null:
			seen[String(o.name)] = true
	var names := seen.keys()
	names.sort()
	return ", ".join(names) if names.size() else "nothing"


func _finish_leg(arrived: bool, stalled: bool, fell: bool, at: Vector3) -> void:
	var leg: Array = _legs[_leg]
	var label: String = leg[0]
	var must_arrive: bool = leg[3]
	var verdict := "ok"
	if fell:
		verdict = "FELL"
	elif must_arrive and not arrived:
		verdict = "BLOCKED" if stalled else "TIMEOUT"
	elif not must_arrive and arrived:
		verdict = "LEAKED"
	if verdict != "ok":
		_fails.append("%s (%s)" % [label, verdict])
	print("%-22s %-8s  end=(%6.1f,%5.2f,%6.1f)  min_y=%5.2f  t=%4.1f  hit: %s" % [
		label, verdict, at.x, at.y, at.z, _min_y, _t, _blockers()])

	_leg += 1
	_start_leg()


func _report() -> void:
	print("---")
	if _fails.is_empty():
		print("PASS: route walks both directions, every edge holds")
	else:
		print("FAIL: %d" % _fails.size())
		for f in _fails:
			print("  - %s" % f)
	get_tree().quit(1 if _fails.size() else 0)
