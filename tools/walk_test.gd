extends Node

## Dev tool: drives the real player down the entrance street and back, round the
## three scaffolded passages, and — once the seam is crossed — over every route on
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
	# Three threshold spokes, one leg per dogleg.
	#
	# **These are the legs that were missing.** Every threshold test below starts
	# at the mouth, so nothing here had ever walked the plaza itself — and three
	# of the four original spokes in `ParkPlan.WALKWAYS` turned out to run through
	# buildings. A passage nothing can reach passes every test aimed at the passage.
	for s in [
		["nnw", [Vector3(-8.0, 1.2, -13.86), Vector3(-14.0, 1.2, -30.0),
			Vector3(-16.9, 1.2, -46.0)]],
		["se", [Vector3(13.86, 1.2, 8.0), Vector3(27.0, 1.2, 13.0),
			Vector3(34.0, 1.2, 26.0), Vector3(46.0, 1.2, 31.3)]],
		["sw", [Vector3(-8.0, 1.2, 13.86), Vector3(-28.0, 1.2, 30.0),
			Vector3(-31.3, 1.2, 46.0)]],
	]:
		var run: Array = s[1]
		for i in run.size() - 1:
			_legs.append(["spoke %s %d" % [s[0], i], run[i], run[i + 1], true])
	# The ride remains reachable across ordinary plaza brick, but this is not a
	# spoke and does not reserve or pave a corridor in the plan.
	_legs.append(["plaza brick -> dark ride court", Vector3(24.0, 1.2, -18.0),
		Vector3(29.0, 1.2, -29.0), true])
	_legs.append(["dark ride court -> front", Vector3(29.0, 1.2, -29.0),
		Vector3(33.5, 1.2, -27.4), true])
	_legs.append(["dark ride front holds", Vector3(31.5, 1.2, -27.4),
		Vector3(45.0, 1.2, -27.4), false])
	# The dark ride's back-of-house court is reachable from the east forecourt,
	# but remains absent from the public walkway plan and minimap. Walk the clear
	# lane both ways, then prove the staff gate and retaining wall terminate it.
	var service_x := ParkPlan.EAST_SERVICE_LANE_X
	_legs.append(["east service yard north",
		Vector3(service_x, 1.2, ParkPlan.EAST_SERVICE_FROM_Z - 1.0),
		Vector3(service_x, 1.2, ParkPlan.EAST_SERVICE_GATE_Z + 2.0), true])
	_legs.append(["east service yard south",
		Vector3(service_x, 1.2, ParkPlan.EAST_SERVICE_GATE_Z + 2.0),
		Vector3(service_x, 1.2, ParkPlan.EAST_SERVICE_FROM_Z - 1.0), true])
	_legs.append(["east service gate holds",
		Vector3(service_x, 1.2, ParkPlan.EAST_SERVICE_GATE_Z + 2.0),
		Vector3(service_x, 1.2, ParkPlan.EAST_SERVICE_GATE_Z - 7.0), false])
	_legs.append(["east service wall holds",
		Vector3(service_x, 1.2, -25.0), Vector3(67.0, 1.2, -25.0), false])

	# The east gate and the forecourt behind it, both directions.
	#
	# **Walked rather than screenshotted, because a straight 6m opening on the
	# fountain's axis is a route and not a view.** The three thresholds above bend,
	# so what they need proving is that they hold; this one goes somewhere, and
	# what it needs proving is that you get there and back. The court sits a
	# centimetre under the plaza's own floor — `GROUND_SEAM`, the street's
	# arrangement — and a centimetre is exactly the size of mistake that a
	# `CharacterBody3D` with no step-up turns into a wall.
	#
	# Aimed along the axis at every leg. A waypoint the player can walk past is a
	# test that lies both ways, and the two 22m diagonals on the cascade's wings
	# are what taught that.
	var ex := ParkPlan.EAST_GAP_AT
	var ring_e := Vector3(16.0, 1.2, 0.0)
	var bend_e := Vector3(26.0, 1.2, ex.y)
	var mouth_e := Vector3(ex.x - 6.75, 1.2, ex.y)
	var far_e := Vector3(ex.x + 6.75, 1.2, ex.y)
	var foot_e := Vector3(ParkPlan.EAST_STAIR_FOOT.x, 1.2, ex.y)
	_legs.append(["east spoke in", ring_e, bend_e, true])
	_legs.append(["east spoke to mouth", bend_e, mouth_e, true])
	var seam_w := Vector3(ParkPlan.EAST_SEAM_AT.x - 3.0, 1.2, ex.y)
	var seam_e := Vector3(ParkPlan.EAST_SEAM_AT.x + 3.0, 1.2, ex.y)
	_legs.append(["east gate to seam", mouth_e, seam_w, true])
	# **Not through the gate any more.** The east seam went in on 2026-08-18 and
	# `cross_terraces` sits on the wall's centre line, so a leg that walks the
	# passage trips a section swap and the hold shot freezes the body — which
	# arrives here as a timeout on the *return* leg and looks like broken
	# geometry. Both sides are `section_test`'s now. This walks up to the mouth
	# and stops, which is still the question walk_test can answer: is the passage
	# clear to its own threshold.
	_legs.append(["east court out", far_e, foot_e, true])
	_legs.append(["east court back", foot_e, far_e, true])
	_legs.append(["east gate from seam", seam_e, far_e, true])
	_legs.append(["east spoke home", mouth_e, ring_e, true])
	# The two piers, from inside the passage. The leak in a gate is never the
	# middle.
	# **Started clear of the crossing volume, not on the gap's own centre line.**
	# Both of these stood at `ex` until the seam went in, which is inside
	# `cross_terraces` — so the probe tripped the swap, the plaza was freed, and
	# the body fell through ground that no longer existed. It reported as FELL
	# with `hit: nothing`, which reads exactly like a hole in the world and is
	# the section machinery working. The piers are still probed; the standpoint
	# is a stride back into the passage.
	_legs.append(["east pier n holds", seam_w,
		Vector3(seam_w.x, 1.2, ex.y - 10.0), false])
	_legs.append(["east pier s holds", seam_w,
		Vector3(seam_w.x, 1.2, ex.y + 10.0), false])
	# And the monument itself, which must stop you. The middle of a cascade is
	# water and the niche behind it is blind — it stopped being a doorway when
	# the fountain went into it, and nothing has walked up the middle since. If
	# this leg arrives, the niche is a hole again.
	_legs.append(["east cascade holds", foot_e,
		Vector3(ParkPlan.HILL_FACE_X - 2.0, 1.2, ex.y), false])

	# **The climb, and the shelf at the top of it.** Both are new on 2026-08-18
	# and neither had ever been walked — the east cascade's wings have existed
	# since the day the monument was sited and every leg above only ever asked
	# whether the *middle* of it stops you. A route nobody has walked is a route
	# that does not work yet, and this one is six metres of rise with a hairpin
	# in each half.
	for w in [[-1.0, "n"], [1.0, "s"]]:
		var side: float = w[0]
		var nm: String = w[1]
		# Out of `ParkPlan`, never re-derived here. The west's copy of this
		# arithmetic agreed with the real wing right up until the shape changed,
		# and then reported broken geometry rather than a stale test.
		var path: Array = ParkPlan.wing_path(ParkPlan.CASCADE_EAST, side)
		var stand: Array[Vector3] = []
		for v in path:
			stand.append(v + Vector3(0, 0.2, 0))
		# Vertex to vertex, because thirds of a hairpin cut the corner and walk
		# the player into the wall between the two legs.
		_legs.append(["ehill %s foot" % nm, foot_e, stand[3], true])
		for i in range(2, -1, -1):
			_legs.append(["ehill %s up %d" % [nm, i], stand[i + 1], stand[i], true])
		for i in 3:
			_legs.append(["ehill %s down %d" % [nm, i], stand[i], stand[i + 1], true])
		_legs.append(["ehill %s to foot" % nm, stand[3], foot_e, true])

	# The head of the monument, the sill, and across the shelf. The sill is the
	# single stride every route up here passes through and it laps two decks that
	# meet on the scarp line — if a capsule can catch anywhere on this hill it
	# catches there.
	var head_y: float = ParkPlan.HILL_TOP + 1.2
	# Typed rather than inferred: `wing_path` returns a bare `Array`, so its
	# elements are Variant and `:=` cannot infer Vector3 from one.
	var wing_head: Vector3 = ParkPlan.wing_path(ParkPlan.CASCADE_EAST, -1.0)[0] \
		+ Vector3(0, 0.2, 0)
	var land_e := Vector3(ParkPlan.HILL_FACE_X - 2.0, head_y, ex.y)
	var sill_e := Vector3(ParkPlan.HILL_FACE_X + 2.0, head_y, ex.y)
	# In front of the pool's west coping, derived off `POOL_FROM_X` rather than
	# typed: the literal 78 this held was fine on a 16m belvedere and was inside
	# the collecting pool the day the shelf shrank to 8 — five legs BLOCKED on
	# copings, all of them the test walking through water rather than the room
	# failing. The room circulates west of the pool and around its ends.
	var shelf_mid := Vector3(ParkPlan.POOL_FROM_X - 1.2, head_y, ex.y)
	_legs.append(["ehill head -> landing", wing_head, land_e, true])
	_legs.append(["ehill landing -> sill", land_e, sill_e, true])
	_legs.append(["ehill sill -> shelf", sill_e, shelf_mid, true])
	_legs.append(["ehill shelf -> sill", shelf_mid, sill_e, true])
	_legs.append(["ehill sill -> landing", sill_e, land_e, true])
	_legs.append(["ehill landing -> head", land_e, wing_head, true])
	# The length of it, north to south, which is the walk the belvedere is for —
	# down the strip west of the pool, which is the only lane that runs the full
	# length now that the pool owns the room's east half.
	var shelf_n := Vector3(ParkPlan.POOL_FROM_X - 1.2, head_y, ParkPlan.SHELF_FROM_Z + 3.0)
	var shelf_s := Vector3(ParkPlan.POOL_FROM_X - 1.2, head_y, ParkPlan.SHELF_TO_Z - 3.0)
	_legs.append(["ehill shelf north", shelf_mid, shelf_n, true])
	_legs.append(["ehill shelf south", shelf_n, shelf_s, true])
	_legs.append(["ehill shelf back", shelf_s, shelf_mid, true])

	# **The basin staircase**, which is six metres of rise in four flights and had
	# never been walked when it was written. The reach profile comes out of
	# `ParkPlan.climb_reaches` and is never re-derived here — see `wing_path` for
	# what re-deriving a shape costs the first time the shape moves.
	var cfz: float = ParkPlan.climb_flight_z()
	for w in [[-1.0, "n"], [1.0, "s"]]:
		var side: float = w[0]
		var nm: String = w[1]
		var zc: float = ex.y + side * cfz
		var stand: Array[Vector3] = []
		var xs: Array[float] = [ParkPlan.CLIMB_FROM_X]
		for r in ParkPlan.climb_reaches():
			xs.append(float(r[1]))
		for x in xs:
			stand.append(Vector3(x, ParkPlan.climb_floor_y(x) + 0.2, zc))
		# Onto the strip off the belvedere first: the mouth is where the pool
		# coping, the scarp and the flight all arrive at one stride.
		_legs.append(["climb %s on" % nm, Vector3(76.0, head_y, zc), stand[0], true])
		for i in stand.size() - 1:
			_legs.append(["climb %s up %d" % [nm, i], stand[i], stand[i + 1], true])
		for i in range(stand.size() - 1, 0, -1):
			_legs.append(["climb %s down %d" % [nm, i], stand[i], stand[i - 1], true])
		_legs.append(["climb %s off" % nm, stand[0], Vector3(76.0, head_y, zc), true])
		# The bank outboard and the garden inboard. Neither is walkable and both
		# are what stops the player leaving the cut sideways — probed at the
		# mouth, where the bank is deepest and the wall under it is 2.4m.
		var mid: Vector3 = stand[1]
		_legs.append(["climb %s bank holds" % nm, mid,
			mid + Vector3(0.0, 0.0, side * 7.0), false])
		_legs.append(["climb %s garden holds" % nm, mid,
			Vector3(mid.x, mid.y, ex.y), false])
	# Across the top of the whole feature — **on terrace two, not at the head of
	# the climb.** The first version crossed at `CLIMB_TO_X - 1`, which is still
	# inside the cutting with the twelfth basin between the two strips, and it
	# was blocked by `basin_11_bowl`. That is the chain doing its job: the garden
	# is not a place you cross, and the crossing is the ground above it.
	var climb_head := Vector3(ParkPlan.CLIMB_TO_X + 4.0,
		ParkPlan.CLIMB_HEAD_Y + 1.2, ex.y - cfz)
	_legs.append(["climb head across", climb_head,
		Vector3(climb_head.x, climb_head.y, ex.y + cfz), true])
	# The two attraction promenades beyond the crest courts. Their first bend
	# clears the courts' west parapets, then the route climbs with the graded
	# shoulder to each ride gate. Walk both directions and push into the ride
	# machinery once, so a pretty path that falls through its bank or a fenced
	# deck with nothing solid in it cannot pass by appearance alone.
	var end_head := Vector3(ParkPlan.CLIMB_TO_X + 4.0,
		ParkPlan.CLIMB_HEAD_Y + 1.2, ex.y)
	for w in [[-1.0, "n"], [1.0, "s"]]:
		var side: float = w[0]
		var nm: String = w[1]
		var route := ParkPlan.east_end_path(side)
		var stand: Array[Vector3] = []
		for v in route:
			stand.append(v + Vector3(0.0, 1.2, 0.0))
		_legs.append(["east end %s on" % nm, end_head, stand[0], true])
		for i in stand.size() - 1:
			_legs.append(["east end %s out %d" % [nm, i], stand[i], stand[i + 1], true])
		for i in range(stand.size() - 1, 0, -1):
			_legs.append(["east end %s back %d" % [nm, i], stand[i], stand[i - 1], true])
		_legs.append(["east end %s off" % nm, stand[0], end_head, true])
		_legs.append(["east end %s ride holds" % nm, stand[-1],
			Vector3(ParkPlan.EAST_END_RIDE_X, ParkPlan.EAST_END_FLOOR_Y + 1.2,
				ex.y + side * ParkPlan.EAST_END_RIDE_D), false])
	# The observation tower branches around the north ride's queue. Walk the
	# actual bends both ways, then push into the lift house from the clear side of
	# the court so a fence post cannot make an empty tower base look solid.
	var tower_route: Array[Vector3] = ParkPlan.east_tower_path()
	var tower_stand: Array[Vector3] = []
	for v in tower_route:
		tower_stand.append(v + Vector3(0.0, 1.2, 0.0))
	for i in tower_stand.size() - 1:
		_legs.append(["east tower out %d" % i,
			tower_stand[i], tower_stand[i + 1], true])
	for i in range(tower_stand.size() - 1, 0, -1):
		_legs.append(["east tower back %d" % i,
			tower_stand[i], tower_stand[i - 1], true])
	var tower_probe := ParkPlan.east_tower_point(0.0, -5.5) + Vector3(0.0, 1.2, 0.0)
	_legs.append(["east tower base holds", tower_probe,
		ParkPlan.east_tower_center() + Vector3(0.0, 1.2, 0.0), false])
	# **The bays**, which are the reason the landings exist as more than a pause:
	# each terrace opens left and right into a shelf cut into the hillside. New
	# ground, so it gets walked — out from the landing, along the shelf, and a
	# probe at the back wall, which is the hill and must stop you.
	var bi := 0
	var creaches := ParkPlan.climb_reaches()
	for ri in creaches.size():
		var r: Array = creaches[ri]
		# Narrow landings carry no bay — see `CLIMB_BAY_MIN_T`.
		if bool(r[4]) or float(r[1]) - float(r[0]) < ParkPlan.CLIMB_BAY_MIN_T:
			continue
		var bx: float = (float(r[0]) + float(r[1])) * 0.5
		var byy: float = float(r[2]) + 1.2
		var bd: float = ParkPlan.CLIMB_BAY_D
		for w2 in [[-1.0, "n"], [1.0, "s"]]:
			var sd: float = w2[0]
			var bn: String = w2[1]
			var onl := Vector3(bx, byy, ex.y + sd * (ParkPlan.CLIMB_HALF_Z + 1.5))
			var deep := Vector3(bx, byy, ex.y + sd * (ParkPlan.CLIMB_HALF_Z + bd - 1.2))
			_legs.append(["bay %d %s out" % [bi, bn],
				Vector3(bx, byy, ex.y + sd * cfz), onl, true])
			_legs.append(["bay %d %s deep" % [bi, bn], onl, deep, true])
			_legs.append(["bay %d %s back" % [bi, bn], deep, onl, true])
			# The hill behind it. A shelf you can walk off the back of is a hole.
			_legs.append(["bay %d %s wall holds" % [bi, bn], deep,
				Vector3(bx, byy, ex.y + sd * (ParkPlan.CLIMB_HALF_Z + bd + 6.0)),
				false])
		bi += 1
	_legs.append(["climb head to strip", climb_head,
		Vector3(ParkPlan.CLIMB_TO_X - 1.0, ParkPlan.CLIMB_HEAD_Y + 1.2,
			ex.y - cfz), true])
	# Every edge of it, and there are four. Three are hillside and one is the
	# parapet over a six metre drop onto brick — the notch was built the shape it
	# is so that all four are structure rather than a rail, and this is the only
	# thing that can say whether that came out true. Aimed square at each face:
	# a probe that runs at a corner reports on its own aim.
	_legs.append(["ehill parapet holds", Vector3(74.0, head_y, -12.0),
		Vector3(66.0, head_y, -12.0), false])
	_legs.append(["ehill parapet holds s", Vector3(74.0, head_y, 8.0),
		Vector3(66.0, head_y, 8.0), false])
	_legs.append(["ehill north wall holds", Vector3(78.0, head_y, -16.0),
		Vector3(78.0, head_y, -27.0), false])
	_legs.append(["ehill south wall holds", Vector3(78.0, head_y, 12.0),
		Vector3(78.0, head_y, 23.0), false])
	# Off the ravine's line, because on the axis the way east is the climb and
	# the pool — the wall this probes is the notch's east reveal beside the
	# mouth. The old start of x 82 was on the shelf when the shelf ran to 86
	# and was over the ravine's channel the day it shrank to 78; a probe that
	# spawns inside the cut reports on the cut's plumbing, not the wall.
	_legs.append(["ehill east wall holds", Vector3(74.0, head_y, -10.0),
		Vector3(85.0, head_y, -10.0), false])

	# The three scaffolded section thresholds. Head-on plus both corners, because
	# the leak in a gate is never the middle — it is the hand's width between
	# the post and the wall it was supposed to meet.
	# For each passage: walk in from the plaza and reach the bend, make the turn
	# and reach the end, then push on past the end and be stopped. The last of
	# the three is the one that matters — a passage that leaks is a hole.
	for t in [
		["nnw", Vector3(-16.9, 1.2, -46), Vector3(-16.9, 1.2, -58), Vector3(-27.9, 1.2, -58), Vector3(-45, 1.2, -58)],
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
		var path: Array = ParkPlan.wing_path(ParkPlan.CASCADE_WEST, side)
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
		var mid := ParkPlan.wing_point(ParkPlan.CASCADE_WEST, side, 0.25) \
			+ Vector3(0, 0.2, 0)
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
	# The pier is 8m south of the alley's axis since 2026-08-20, so getting onto
	# it is two legs rather than one — out of the alley, then south along the
	# promenade to the mouth. Walked as two legs and not one diagonal on
	# purpose: a shallow diagonal is the waypoint trap this file already
	# records, and the junction opening up is the whole point of the move.
	var pz := ParkPlan.PIER_ROOT.y
	var mouth := Vector3(ParkPlan.PROMENADE_X + 5.0, y, pz)
	return _cascade_legs() + [
		["bw lane -> alley", alley_in, alley_out, true],
		["bw alley -> pier mouth", prom, mouth, true],
		["bw onto the pier", mouth, Vector3(-106, y, pz), true],
		["bw out the pier", Vector3(-106, y, pz), Vector3(-149, y, pz), true],
		["bw pavilion holds", Vector3(-149, y, pz), Vector3(-162, y, pz), false],
		["bw back down pier", Vector3(-149, y, pz), Vector3(-102, y, pz), true],
		["bw mouth -> alley", mouth, prom, true],
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
		# **The jetty, which is a new open edge.** The promenade's rail breaks
		# across the wheel's 26m, because a rail along the front of a boarding
		# platform is a rail across the ride — so what stops the player there is
		# the platform's own east face, half a metre proud, and nothing else.
		# That is a barrier only because `CharacterBody3D` has no step-up, which
		# is a fact about the engine rather than about the geometry, and exactly
		# the kind of thing that has to be walked rather than reasoned about.
		# Three legs: the middle of the break and both of its ends.
		#
		# They start at x -103 rather than at the promenade's own line, and the
		# first run of this probe is why. `holds s` began at -98, walked 0.8m,
		# stopped dead on `prom_lamp_8` and reported ok — a leg that asks
		# whether an edge holds and never reaches the edge passes for the wrong
		# reason, which is worse than failing. The lamp standards stand at
		# `PROMENADE_X`; start west of them.
		["bw jetty holds", Vector3(-103, y, ParkPlan.WHEEL_AT.y),
			Vector3(-120, y, ParkPlan.WHEEL_AT.y), false],
		["bw jetty holds n", Vector3(-103, y, ParkPlan.WHEEL_FROM_Z + 1.0),
			Vector3(-120, y, ParkPlan.WHEEL_FROM_Z + 1.0), false],
		["bw jetty holds s", Vector3(-103, y, ParkPlan.WHEEL_TO_Z - 1.0),
			Vector3(-120, y, ParkPlan.WHEEL_TO_Z - 1.0), false],
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
