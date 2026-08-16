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

## How far below the lower of a leg's own two ends it may take the player before
## it counts as falling.
##
## Relative, not absolute: the boardwalk's floor is at −6 and a fixed threshold
## of −3 called every leg down there a fall.
##
## **Below the lower end and not below the start, since 2026-08-15.** Measuring
## from the start makes the threshold a cap on how far a leg is allowed to
## descend, which is a different question and one this test has no business
## asking — a leg from the head of the flight to its middle drops 3m by design,
## and it began failing the moment the cascade went back to a 6m drop. A leg that
## ends 4m below where it started has not fallen; a leg that dips 3m below *both*
## of its ends has, whatever height either end is at.
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


## The cascade — all three ways down it, both directions.
##
## The middle flight, the north wing's ramp and the south wing's garden stair
## start together at the bluff top and land together in the court, which is the
## whole point of the thing: a group with a wheelchair in it does not have to
## split up to get to the boardwalk. So all three get walked, and so does the
## portal they converge on.
func _cascade_legs() -> Array:
	var axis: float = ParkPlan.CASCADE_AXIS_Z
	var top_x: float = ParkPlan.CASCADE_TOP_X
	var y: float = ParkPlan.SHORE_TOP + 1.2
	var arch := Vector3(ParkPlan.ARCH_ARRIVE_WEST.x, 1.2, axis)
	var head := Vector3(top_x - 0.8, 1.2, axis)
	var foot := Vector3(ParkPlan.STAIR_FOOT.x - 2.5, ParkPlan.SHORE_TOP + 0.2, axis)
	var court := Vector3(ParkPlan.BACK_LANE_X, y, axis)
	# **No legs down the middle since 2026-08-15.** The centre is the cascade —
	# water, basins and terraces — and nobody walks it. What used to be three legs
	# down a flight is now the approach along the bluff top to the head of each
	# wing, which is below.
	var out: Array = [
		["cas arch -> head", arch, head, true],
		["cas head -> arch", head, arch, true],
		["cas foot -> court", foot, court, true],
		["cas court -> foot", court, foot, true],
	]
	# Each wing, vertex to vertex along its own hairpin — out and down, across the
	# turn, back in and down — then the same three in reverse.
	#
	# **Vertex to vertex and not in equal thirds**, which is the rule about
	# waypoints applied to a route with corners in it: thirds of a hairpin send
	# the player diagonally through the wall between the legs and report it as
	# broken geometry rather than as a badly aimed test.
	for w in [[-1.0, "north"], [1.0, "south"]]:
		var side: float = w[0]
		var nm: String = w[1]
		var path: Array = ParkPlan.wing_path(side)
		var stand: Array[Vector3] = []
		for v in path:
			stand.append(v + Vector3(0, 0.2, 0))
		for i in 3:
			out.append(["cas %s %d" % [nm, i], stand[i], stand[i + 1], true])
		for i in range(2, -1, -1):
			out.append(["cas %s up %d" % [nm, i], stand[i + 1], stand[i], true])
		# The joints where a wing meets something that is not itself: the landing
		# at the head, and the court at the foot. The second is the design's own
		# claim under test — both wings are supposed to land beside the middle,
		# and an earlier shape failed exactly that by eighty-five metres while
		# passing a leg that only asked whether it could walk further along its
		# own line.
		var land := Vector3(top_x - 2.0, 1.2, axis)
		out.append(["cas %s landing -> head" % nm, land, stand[0], true])
		out.append(["cas %s head -> landing" % nm, stand[0], land, true])
		out.append(["cas %s wing -> foot" % nm, stand[3], foot, true])
		out.append(["cas %s foot -> wing" % nm, foot, stand[3], true])
		# The open side, which is a drop into the court the whole way down.
		var mid := ParkPlan.wing_point(side, 0.25) + Vector3(0, 0.2, 0)
		out.append(["cas %s rail holds" % nm, mid,
			mid + Vector3(-9.0, 0.0, 0.0), false])
	return out


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
	return _cascade_legs() + [
		["bw lane -> alley", alley_in, alley_out, true],
		["bw alley -> pier head", prom, Vector3(-106, y, ParkPlan.ALLEY_Z), true],
		["bw out the pier", Vector3(-106, y, ParkPlan.ALLEY_Z),
			Vector3(-149, y, ParkPlan.ALLEY_Z), true],
		["bw pavilion holds", Vector3(-149, y, ParkPlan.ALLEY_Z),
			Vector3(-162, y, ParkPlan.ALLEY_Z), false],
		["bw back down pier", Vector3(-149, y, ParkPlan.ALLEY_Z),
			Vector3(-102, y, ParkPlan.ALLEY_Z), true],
		# The walk north weaves, and both pinches are real. The tables outside the
		# corn-dog stand and the wheel's platform leave 4m between them; then the
		# wheel's ticket booth takes the west half of what is left. A straight
		# line up the promenade walks into one or the other, which is the same
		# route the crowd's graph threads and for the same reason.
		["bw north past tables", Vector3(-96.5, y, -4.0), Vector3(-96.5, y, -14.0), true],
		["bw past the booth", Vector3(-96.5, y, -14.0), Vector3(-94.5, y, -24.0), true],
		["bw wheel -> coaster", Vector3(-94.5, y, -24.0), Vector3(-96, y, -52.0), true],
		["bw north end holds", Vector3(-98, y, -72.0), Vector3(-98, y, -95.0), false],
		["bw south along strip", Vector3(-98, y, 10.0), Vector3(-98, y, 62.0), true],
		["bw south end holds", Vector3(-98, y, 70.0), Vector3(-98, y, 92.0), false],
		# Probes. None of these may arrive.
		["bw water holds", Vector3(-98, y, 30.0), Vector3(-120, y, 30.0), false],
		["bw water holds n", Vector3(-98, y, -50.0), Vector3(-120, y, -50.0), false],
		["bw shops hold", Vector3(-96, y, 26.0), Vector3(-60.0, y, 26.0), false],
		["bw yard holds", Vector3(-98, y, 70.0), Vector3(-62.0, y, 70.0), false],
		["bw coaster fence holds", Vector3(-96, y, -60.0), Vector3(-60.0, y, -60.0), false],
		["bw bluff holds", Vector3(-70.0, y, 20.0), Vector3(-50.0, y, 20.0), false],
		# The bluff face north of the ramp, where there is no way up at all.
		["bw bluff holds n", Vector3(-70.0, y, -50.0), Vector3(-50.0, y, -50.0), false],
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
	var fell := p.y < minf(_from.y, _to.y) - FALL_BELOW
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
