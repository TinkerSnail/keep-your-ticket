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
## Every crowd standing, not the first one found. `get_first_node_in_group` was
## fine while the plaza was the only section with a cast in it.
##
## **Everybody, not `crowd.guests`.** That array is the register of who is
## actually in the park — the day admits groups out of a dormant pool as the
## hour turns, and a dormant guest is not in it. So this cleared the crowd
## standing at the moment it ran and left the rest of the cast to walk in
## afterwards, which made the verdict depend on how long the run took to reach a
## leg: `bw back down pier` failed on a guest who arrived during the descent, and
## only once the stair legs made the run long enough for them to.
##
## Stopping the crowd itself is the other half. Freeing the guests is not enough
## while the thing that admits them is still ticking.
func _clear_crowds() -> void:
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_physics_process(false)
	for g in get_tree().get_nodes_in_group("guest"):
		g.queue_free()


func _enter_boardwalk() -> void:
	print("--- crossing to the boardwalk ---")
	await ParkSections.enter(&"boardwalk", &"plaza")
	for i in 4:
		await get_tree().physics_frame
	if ParkSections.current() != &"boardwalk":
		_fails.append("could not mount the boardwalk")
		_report()
		return

	# Clear the crowd again. The one freed at startup was the plaza's — the
	# section swap stands up a second one, 57 guests on a 17m strip, and this
	# test is geometry only for the reason stated up there.
	#
	# It failed as a *timeout* rather than a block, which is why it went
	# unnoticed: bodies pushing back do not stop the player, they slow him to a
	# third of his pace, and whether 52m fits in the budget then depends on how
	# many guests the hour has put on the promenade — which depends on how long
	# the run took to get here. Adding geometry anywhere in the park was enough
	# to tip it. A test whose verdict moves when an unrelated scene grows is
	# worse than no test.
	_clear_crowds()
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
	_clear_crowds()
	await get_tree().physics_frame

	# label, from, to, must_arrive
	_legs = [
		["plaza -> gap", Vector3(0, 1.2, 20), Vector3(-1.5, 1.2, 46), true],
		["gap -> mid street", Vector3(-1.5, 1.2, 46), Vector3(-1.5, 1.2, 78), true],
		["mid street -> gate", Vector3(-1.5, 1.2, 78), Vector3(-1.5, 1.2, 104), true],
		["through turnstiles", Vector3(-1.5, 1.2, 104), Vector3(-1.5, 1.2, 112), true],
		["apron -> gate", Vector3(-1.5, 1.2, 116), Vector3(-1.5, 1.2, 104), true],
		["gate -> mid street", Vector3(-1.5, 1.2, 104), Vector3(-1.5, 1.2, 72), true],
		["street -> plaza", Vector3(-1.5, 1.2, 72), Vector3(0, 1.2, 24), true],
		# Edge probes. Each must NOT arrive: something should stop the player.
		["probe west shops", Vector3(-1.5, 1.2, 67), Vector3(-30, 1.2, 67), false],
		["probe east shops", Vector3(-1.5, 1.2, 82), Vector3(28, 1.2, 82), false],
		["probe west shops far", Vector3(-1.5, 1.2, 97), Vector3(-30, 1.2, 97), false],
		# Clear of the flagpole row, which stopped the first run's probes before
		# they ever reached the walls they were aimed at.
		["probe apron west", Vector3(-1.5, 1.2, 119), Vector3(-30, 1.2, 119), false],
		["probe apron east", Vector3(-1.5, 1.2, 119), Vector3(28, 1.2, 119), false],
		["probe apron south", Vector3(-1.5, 1.2, 119), Vector3(-1.5, 1.2, 142), false],
		["probe apron sw", Vector3(-1.5, 1.2, 119), Vector3(-30, 1.2, 142), false],
		["probe apron se", Vector3(-1.5, 1.2, 119), Vector3(28, 1.2, 142), false],
		["probe street seam", Vector3(-1.5, 1.2, 53), Vector3(-30, 1.2, 53), false],
		# The arcade, which is a room you walk into rather than a scene that
		# loads. In and back out under your own power, and the back wall holds.
		["arcade in", Vector3(-6.0, 1.2, 78), Vector3(-20.0, 1.2, 78), true],
		["arcade back out", Vector3(-20.0, 1.2, 78), Vector3(-4.0, 1.2, 78), true],
		["arcade rear holds", Vector3(-20.0, 1.2, 78), Vector3(-40.0, 1.2, 78), false],
		["arcade north holds", Vector3(-20.0, 1.2, 78), Vector3(-20.0, 1.2, 62), false],
		["arcade south holds", Vector3(-20.0, 1.2, 78), Vector3(-20.0, 1.2, 94), false],
	]
	# The four spokes, ring to passage mouth, one leg per dogleg.
	#
	# **These are the legs that were missing.** Every threshold test below starts
	# at the mouth, so nothing here had ever walked the plaza itself — and three
	# of the four spokes in `ParkPlan.WALKWAYS` turned out to run through
	# buildings, `spoke_ne` for 21m of it. A passage nothing can reach passes
	# every test aimed at the passage.
	for s in [
		["nnw", [Vector3(-8.0, 1.2, -13.86), Vector3(-14.0, 1.2, -30.0),
			Vector3(-16.9, 1.2, -46.0)]],
		["ne", [Vector3(13.86, 1.2, -8.0), Vector3(30.0, 1.2, -24.0),
			Vector3(46.0, 1.2, -27.4)]],
		["se", [Vector3(13.86, 1.2, 8.0), Vector3(27.0, 1.2, 13.0),
			Vector3(34.0, 1.2, 26.0), Vector3(46.0, 1.2, 31.3)]],
		["sw", [Vector3(-8.0, 1.2, 13.86), Vector3(-28.0, 1.2, 30.0),
			Vector3(-31.3, 1.2, 46.0)]],
	]:
		var run: Array = s[1]
		for i in run.size() - 1:
			_legs.append(["spoke %s %d" % [s[0], i], run[i], run[i + 1], true])

	# The four scaffolded section thresholds. Head-on plus both corners, because
	# the leak in a gate is never the middle — it is the hand's width between
	# the post and the wall it was supposed to meet.
	# For each passage: walk in from the plaza and reach the bend, make the turn
	# and reach the end, then push on past the end and be stopped. The last of
	# the three is the one that matters — a passage that leaks is a hole.
	for t in [
		["nnw", Vector3(-16.9, 1.2, -46), Vector3(-16.9, 1.2, -58), Vector3(-27.9, 1.2, -58), Vector3(-45, 1.2, -58)],
		["ne", Vector3(46, 1.2, -27.4), Vector3(58, 1.2, -27.4), Vector3(58, 1.2, -38.4), Vector3(58, 1.2, -56)],
		["se", Vector3(46, 1.2, 31.3), Vector3(58, 1.2, 31.3), Vector3(58, 1.2, 41.3), Vector3(58, 1.2, 59)],
		["sw", Vector3(-31.3, 1.2, 46), Vector3(-31.3, 1.2, 58), Vector3(-41.3, 1.2, 58), Vector3(-59, 1.2, 58)],
	]:
		_legs.append(["way %s in" % t[0], t[1], t[2], true])
		_legs.append(["way %s turn" % t[0], t[2], t[3], true])
		_legs.append(["way %s holds" % t[0], t[3], t[4], false])
	_start_leg()


## The way down from the arch: the terrace, the bluff top, the flight, and out
## into the lane.
##
## Both directions, because a stair is the one route where down and up are
## different problems. `CharacterBody3D` has no step-up, so a flight that walks
## down a treat can be a wall coming back — which is why the treads are scenery
## and the ramp under them is the floor.
##
## The descent is split in three, because `FALL_BELOW` is measured from where a
## leg started and the flight drops six metres. One leg from head to foot cannot
## be told apart from walking off the side of it.
func _stair_legs() -> Array:
	var arch := Vector3(ParkPlan.ARCH_ARRIVE_WEST.x, 1.2, ParkPlan.ARCH_ARRIVE_WEST.z)
	# On the head deck, still on the arch's axis — the walk west is one straight
	# line from the tunnel to here, across the terrace and the bluff top.
	var deck := Vector3(ParkPlan.STAIR_X, 1.2, ParkPlan.ARCH_AT.y)
	var third := _on_flight(1.0 / 3.0)
	var two_thirds := _on_flight(2.0 / 3.0)
	var foot := Vector3(ParkPlan.STAIR_X, ParkPlan.STAIR_FOOT.y + 0.2,
		ParkPlan.STAIR_FOOT.z)
	var y := ParkPlan.SHORE_TOP + 1.2
	var lane := Vector3(ParkPlan.BACK_LANE_X, y, ParkPlan.STAIR_FOOT.z)
	var alley := Vector3(ParkPlan.BACK_LANE_X, y, ParkPlan.ALLEY_Z)
	return [
		["bw arch -> deck", arch, deck, true],
		["bw deck -> third", deck, third, true],
		["bw third -> two thirds", third, two_thirds, true],
		["bw two thirds -> foot", two_thirds, foot, true],
		["bw foot -> lane", foot, lane, true],
		["bw lane -> alley mouth", lane, alley, true],
		["bw alley mouth -> lane", alley, lane, true],
		["bw lane -> foot", lane, foot, true],
		["bw foot -> two thirds", foot, two_thirds, true],
		["bw two thirds -> third", two_thirds, third, true],
		["bw third -> deck", third, deck, true],
		["bw deck -> arch", deck, arch, true],
		# The parapet is all that is between the terrace walk and the shore. It is
		# hand-authored in `plaza.tscn`, which is *not* mounted here — what holds
		# these is the copy `_plaza_from_below` reads out of that file, so these two
		# probes really ask whether the copy still collides.
		["bw parapet holds", Vector3(-46.0, 1.2, 4.0),
			Vector3(-56.0, 1.2, 4.0), false],
		["bw parapet holds n", Vector3(-46.0, 1.2, -9.0),
			Vector3(-56.0, 1.2, -9.0), false],
		# And the bluff top past the parapet is a seven-metre ledge running the
		# length of the map. Both ends of it have to hold, or the way down is also a
		# way to walk to the coaster along the top of a cliff.
		["bw ledge holds n", Vector3(-54.5, 1.2, -6.0),
			Vector3(-54.5, 1.2, -22.0), false],
		["bw ledge holds s", Vector3(-54.5, 1.2, 2.0),
			Vector3(-54.5, 1.2, 18.0), false],
		# The open side of the flight, which is a six-metre drop onto the lane.
		["bw flight rail holds", _on_flight(0.5),
			_on_flight(0.5) + Vector3(-6.0, 0.0, 0.0), false],
	]


## A point on the flight, `t` of the way down it, a stride above the treads.
func _on_flight(t: float) -> Vector3:
	var run: float = ParkPlan.STAIR_GOING * ParkPlan.STAIR_TREADS
	var drop: float = ParkPlan.STAIR_RISE * ParkPlan.STAIR_TREADS
	return Vector3(ParkPlan.STAIR_X, -drop * t + 0.2,
		ParkPlan.STAIR_HEAD_Z + run * t)


## The boardwalk, one section down. Eye height is the shore plus the same 1.2 the
## plaza legs use.
##
## The order is the order the player meets it, because that is the thing being
## tested: the terrace, the stair, the lane, the alley, and then the promenade in
## both directions with the pier out of the middle of it. Everything after that
## is a probe — the water, the shops, the bluff, and both ends of the strip.
##
## **The stair is in this list rather than the plaza's since 2026-08-14.** The
## seam moved to the arch, so the player descends it with the boardwalk standing
## and the plaza gone — different neighbours, different scene, and the flight is
## a scene mounted with this one. It was walked in the plaza's phase until the
## seam moved and then in neither, because `section_test.gd` gave it up the same
## day and nothing picked it up — and what nothing was walking turned out to be a
## flight buried inside the boardwalk's own fill for the slot it descends. A
## route nothing walks is a route that is not walkable, and this one was not.
func _boardwalk_legs() -> Array:
	var y := ParkPlan.SHORE_TOP + 1.2
	var alley_in := Vector3(ParkPlan.BACK_LANE_X, y, ParkPlan.ALLEY_Z)
	var alley_out := Vector3(ParkPlan.PROMENADE_X + 5.0, y, ParkPlan.ALLEY_Z)
	var prom := Vector3(ParkPlan.PROMENADE_X + 5.0, y, ParkPlan.ALLEY_Z)
	return _stair_legs() + [
		["bw lane -> alley", alley_in, alley_out, true],
		["bw alley -> pier head", prom, Vector3(-90.0, y, ParkPlan.ALLEY_Z), true],
		["bw out the pier", Vector3(-90.0, y, ParkPlan.ALLEY_Z),
			Vector3(-133.0, y, ParkPlan.ALLEY_Z), true],
		["bw pavilion holds", Vector3(-133.0, y, ParkPlan.ALLEY_Z),
			Vector3(-146.0, y, ParkPlan.ALLEY_Z), false],
		["bw back down pier", Vector3(-133.0, y, ParkPlan.ALLEY_Z),
			Vector3(-86.0, y, ParkPlan.ALLEY_Z), true],
		# The walk north weaves, and both pinches are real. The tables outside the
		# corn-dog stand and the wheel's platform leave 4m between them; then the
		# wheel's ticket booth takes the west half of what is left. A straight
		# line up the promenade walks into one or the other, which is the same
		# route the crowd's graph threads and for the same reason.
		["bw north past tables", Vector3(-80.5, y, -4.0), Vector3(-80.5, y, -14.0), true],
		["bw past the booth", Vector3(-80.5, y, -14.0), Vector3(-78.5, y, -24.0), true],
		["bw wheel -> coaster", Vector3(-78.5, y, -24.0), Vector3(-80.0, y, -52.0), true],
		["bw north end holds", Vector3(-82.0, y, -72.0), Vector3(-82.0, y, -95.0), false],
		["bw south along strip", Vector3(-82.0, y, 10.0), Vector3(-82.0, y, 62.0), true],
		["bw south end holds", Vector3(-82.0, y, 70.0), Vector3(-82.0, y, 92.0), false],
		# Probes. None of these may arrive.
		["bw water holds", Vector3(-82.0, y, 30.0), Vector3(-104.0, y, 30.0), false],
		["bw water holds n", Vector3(-82.0, y, -50.0), Vector3(-104.0, y, -50.0), false],
		["bw shops hold", Vector3(-80.0, y, 26.0), Vector3(-60.0, y, 26.0), false],
		["bw yard holds", Vector3(-82.0, y, 70.0), Vector3(-62.0, y, 70.0), false],
		["bw coaster fence holds", Vector3(-80.0, y, -60.0), Vector3(-60.0, y, -60.0), false],
		["bw bluff holds", Vector3(-62.0, y, 20.0), Vector3(-48.0, y, 20.0), false],
		["bw well holds", Vector3(-62.0, y, -4.0), Vector3(-48.0, y, -4.0), false],
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
