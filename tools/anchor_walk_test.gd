extends Node

## Test: the two protected anchors, walked by the real player controller.
##
## NT-1 Cascading Staircases: the approach along the bluff top, both wings
## vertex to vertex in both directions, the joints where each wing meets the
## landing and the court, the court itself, and the open side of each wing.
## NT-2 Terraced Fountain: the east spoke and gate, the forecourt, both wings of
## the monument, the belvedere and its sill, the basin staircase both ways, the
## garden bays, and every edge of the notch.
##
## Split out of the retired `walk_test.gd` on 2026-09-05. `footprint_walk_test`
## reads its legs off the generated route bodies and neither anchor has one: a
## straight line through either would run through the water. These legs follow
## `ParkPlan.wing_path` and `ParkPlan.climb_reaches` rather than a copy of that
## arithmetic, so a change to an anchor's shape shows up as a moved test and not
## as broken geometry. Both anchors are protected: a failure here is reported to
## Christina, not fixed in passing.
##
## Presses the real input actions so the run goes through `_physics_process`
## and `_try_step` exactly as a player's would. Every leg is aimed vertex to
## vertex along the thing it asks about, because a waypoint the body can walk
## past is a test that lies both ways.

const ARRIVE := 1.6
const STALL_FRAMES := 90
const MAX_SECONDS := 22.0

## How far below the lower of a leg's own two ends the player may go before it
## counts as falling. Relative to the ends, not to the start: a leg down a wing
## drops by design, and a leg that dips 3m below both of its ends has fallen
## whatever height either end is at.
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


## Everybody, not `crowd.guests`, and stop the thing that admits them: guests
## push back, and a group standing in a gateway reads as a blocked route.
func _clear_crowds() -> void:
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_physics_process(false)
	for g in get_tree().get_nodes_in_group("guest"):
		g.queue_free()


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 4:
		await get_tree().physics_frame
	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if _player == null:
		print("FAIL: no player")
		get_tree().quit(1)
		return
	_clear_crowds()
	await get_tree().physics_frame
	_legs = _west_legs() + _east_legs()
	var filters := OS.get_cmdline_user_args().slice(1)
	if not filters.is_empty():
		_legs = _legs.filter(func(leg: Array) -> bool:
			for f in filters:
				if String(leg[0]).contains(String(f)):
					return true
			return false)
	print("--- anchor routes: %d legs ---" % _legs.size())
	_start_leg()


## NT-1. All three ways down converge on the court, which is the point of the
## monument: a group with a wheelchair in it does not split up to reach the
## boardwalk. The middle is water and nobody walks it, so the approach runs
## along the bluff top to the head of each wing.
func _west_legs() -> Array:
	var axis: float = ParkPlan.CASCADE_AXIS_Z
	var top_x: float = ParkPlan.CASCADE_TOP_X
	var y: float = ParkPlan.SHORE_TOP + 1.2
	var arch := Vector3(ParkPlan.ARCH_ARRIVE_WEST.x, 1.2, axis)
	var head := Vector3(top_x - 0.8, 1.2, axis)
	var foot := Vector3(ParkPlan.STAIR_FOOT.x - 2.5, ParkPlan.SHORE_TOP + 0.2, axis)
	var court := Vector3(ParkPlan.BACK_LANE_X, y, axis)
	var out: Array = [
		["cas arch -> head", arch, head, true],
		["cas head -> arch", head, arch, true],
		["cas foot -> court", foot, court, true],
		["cas court -> foot", court, foot, true],
	]
	for w in [[-1.0, "north"], [1.0, "south"]]:
		var side: float = w[0]
		var nm: String = w[1]
		var path: Array = ParkPlan.wing_path(ParkPlan.CASCADE_WEST, side)
		var stand: Array[Vector3] = []
		for v in path:
			stand.append(v + Vector3(0, 0.2, 0))
		# Vertex to vertex along the hairpin, never in thirds: thirds cut the
		# corner and send the player through the wall between the two legs.
		for i in 3:
			out.append(["cas %s %d" % [nm, i], stand[i], stand[i + 1], true])
		for i in range(2, -1, -1):
			out.append(["cas %s up %d" % [nm, i], stand[i + 1], stand[i], true])
		# The joints where a wing meets something that is not itself.
		var land := Vector3(top_x - 2.0, 1.2, axis)
		out.append(["cas %s landing -> head" % nm, land, stand[0], true])
		out.append(["cas %s head -> landing" % nm, stand[0], land, true])
		out.append(["cas %s wing -> foot" % nm, stand[3], foot, true])
		out.append(["cas %s foot -> wing" % nm, foot, stand[3], true])
		# The open side, a drop into the court the whole way down.
		var mid := ParkPlan.wing_point(ParkPlan.CASCADE_WEST, side, 0.25) \
			+ Vector3(0, 0.2, 0)
		out.append(["cas %s rail holds" % nm, mid, mid + Vector3(-9.0, 0.0, 0.0), false])
	return out


## NT-2. The gate is a route on the fountain's axis, so it is walked there and
## back rather than looked at; the monument must stop you in the middle; the
## wings, the belvedere, the basin staircase and the bays are each walked both
## ways; and every edge of the notch is probed square-on.
func _east_legs() -> Array:
	var out: Array = []
	var ex := ParkPlan.EAST_GAP_AT
	var ring_e := Vector3(16.0, 1.2, 0.0)
	var bend_e := Vector3(26.0, 1.2, ex.y)
	var mouth_e := Vector3(ex.x - 6.75, 1.2, ex.y)
	var far_e := Vector3(ex.x + 6.75, 1.2, ex.y)
	var foot_e := Vector3(ParkPlan.EAST_STAIR_FOOT.x, 1.2, ex.y)
	var gate_w := Vector3(ParkPlan.EAST_SEAM_AT.x - 3.0, 1.2, ex.y)
	var gate_e := Vector3(ParkPlan.EAST_SEAM_AT.x + 3.0, 1.2, ex.y)
	out.append(["east spoke in", ring_e, bend_e, true])
	out.append(["east spoke to mouth", bend_e, mouth_e, true])
	out.append(["east gate in", mouth_e, gate_w, true])
	out.append(["east gate through", gate_w, gate_e, true])
	out.append(["east court out", gate_e, foot_e, true])
	out.append(["east court back", foot_e, far_e, true])
	out.append(["east gate back", gate_e, gate_w, true])
	out.append(["east spoke home", mouth_e, ring_e, true])
	# The two piers from inside the passage: the leak in a gate is never the
	# middle. And the monument itself, whose niche is blind.
	out.append(["east pier n holds", gate_w, Vector3(gate_w.x, 1.2, ex.y - 10.0), false])
	out.append(["east pier s holds", gate_w, Vector3(gate_w.x, 1.2, ex.y + 10.0), false])
	out.append(["east cascade holds", foot_e,
		Vector3(ParkPlan.HILL_FACE_X - 2.0, 1.2, ex.y), false])

	# The wings, out of `ParkPlan` and never re-derived here.
	for w in [[-1.0, "n"], [1.0, "s"]]:
		var side: float = w[0]
		var nm: String = w[1]
		var path: Array = ParkPlan.wing_path(ParkPlan.CASCADE_EAST, side)
		var stand: Array[Vector3] = []
		for v in path:
			stand.append(v + Vector3(0, 0.2, 0))
		out.append(["ehill %s foot" % nm, foot_e, stand[3], true])
		for i in range(2, -1, -1):
			out.append(["ehill %s up %d" % [nm, i], stand[i + 1], stand[i], true])
		for i in 3:
			out.append(["ehill %s down %d" % [nm, i], stand[i], stand[i + 1], true])
		out.append(["ehill %s to foot" % nm, stand[3], foot_e, true])

	# The head of the monument, the sill, and the belvedere. The sill is the one
	# stride every route up here passes through and it laps two decks on the
	# scarp line; if a capsule can catch anywhere on this hill it catches there.
	var head_y: float = ParkPlan.HILL_TOP + 1.2
	var wing_head: Vector3 = ParkPlan.wing_path(ParkPlan.CASCADE_EAST, -1.0)[0] \
		+ Vector3(0, 0.2, 0)
	var land_e := Vector3(ParkPlan.HILL_FACE_X - 2.0, head_y, ex.y)
	var sill_e := Vector3(ParkPlan.HILL_FACE_X + 2.0, head_y, ex.y)
	# West of the pool's coping, derived off `POOL_FROM_X`: the room circulates
	# west of the pool and around its ends.
	var shelf_mid := Vector3(ParkPlan.POOL_FROM_X - 1.2, head_y, ex.y)
	out.append(["ehill head -> landing", wing_head, land_e, true])
	out.append(["ehill landing -> sill", land_e, sill_e, true])
	out.append(["ehill sill -> shelf", sill_e, shelf_mid, true])
	out.append(["ehill shelf -> sill", shelf_mid, sill_e, true])
	out.append(["ehill sill -> landing", sill_e, land_e, true])
	out.append(["ehill landing -> head", land_e, wing_head, true])
	var shelf_n := Vector3(ParkPlan.POOL_FROM_X - 1.2, head_y, ParkPlan.SHELF_FROM_Z + 3.0)
	var shelf_s := Vector3(ParkPlan.POOL_FROM_X - 1.2, head_y, ParkPlan.SHELF_TO_Z - 3.0)
	out.append(["ehill shelf north", shelf_mid, shelf_n, true])
	out.append(["ehill shelf south", shelf_n, shelf_s, true])
	out.append(["ehill shelf back", shelf_s, shelf_mid, true])

	# The basin staircase: the reach profile comes out of `ParkPlan.climb_reaches`.
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
		out.append(["climb %s on" % nm, Vector3(76.0, head_y, zc), stand[0], true])
		for i in stand.size() - 1:
			out.append(["climb %s up %d" % [nm, i], stand[i], stand[i + 1], true])
		for i in range(stand.size() - 1, 0, -1):
			out.append(["climb %s down %d" % [nm, i], stand[i], stand[i - 1], true])
		out.append(["climb %s off" % nm, stand[0], Vector3(76.0, head_y, zc), true])
		# The bank outboard and the garden inboard, probed at the mouth where the
		# bank is deepest and the wall under it is tallest.
		var mid: Vector3 = stand[1]
		out.append(["climb %s bank holds" % nm, mid, mid + Vector3(0.0, 0.0, side * 7.0), false])
		out.append(["climb %s garden holds" % nm, mid, Vector3(mid.x, mid.y, ex.y), false])
	# Across the top of the feature on terrace two, not at the head of the climb,
	# which is still inside the cutting with the top basin between the strips.
	var climb_head := Vector3(ParkPlan.CLIMB_TO_X + 4.0, ParkPlan.CLIMB_HEAD_Y + 1.2, ex.y - cfz)
	out.append(["climb head across", climb_head,
		Vector3(climb_head.x, climb_head.y, ex.y + cfz), true])
	out.append(["climb head to strip", climb_head,
		Vector3(ParkPlan.CLIMB_TO_X - 1.0, ParkPlan.CLIMB_HEAD_Y + 1.2, ex.y - cfz), true])

	# The bays: each garden terrace opens left and right into a shelf cut into
	# the hillside. Out from the landing, along the shelf, and a probe at the
	# back wall, which is the hill and must stop you.
	var bi := 0
	for r in ParkPlan.climb_reaches():
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
			out.append(["bay %d %s out" % [bi, bn], Vector3(bx, byy, ex.y + sd * cfz), onl, true])
			out.append(["bay %d %s deep" % [bi, bn], onl, deep, true])
			out.append(["bay %d %s back" % [bi, bn], deep, onl, true])
			out.append(["bay %d %s wall holds" % [bi, bn], deep,
				Vector3(bx, byy, ex.y + sd * (ParkPlan.CLIMB_HALF_Z + bd + 6.0)), false])
		bi += 1

	# Every edge of the notch, aimed square at each face: three are hillside and
	# one is the parapet over a six metre drop onto brick.
	out.append(["ehill parapet holds", Vector3(74.0, head_y, -12.0), Vector3(66.0, head_y, -12.0), false])
	out.append(["ehill parapet holds s", Vector3(74.0, head_y, 8.0), Vector3(66.0, head_y, 8.0), false])
	out.append(["ehill north wall holds", Vector3(78.0, head_y, -16.0), Vector3(78.0, head_y, -27.0), false])
	out.append(["ehill south wall holds", Vector3(78.0, head_y, 12.0), Vector3(78.0, head_y, 23.0), false])
	out.append(["ehill east wall holds", Vector3(74.0, head_y, -10.0), Vector3(85.0, head_y, -10.0), false])
	return out


func _start_leg() -> void:
	if _leg >= _legs.size():
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


## Names beat coordinates: what actually stopped us.
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
	print("%-26s %-8s  end=(%6.1f,%5.2f,%6.1f)  min_y=%5.2f  t=%4.1f  hit: %s" % [
		label, verdict, at.x, at.y, at.z, _min_y, _t, _blockers()])
	_leg += 1
	_start_leg()


func _report() -> void:
	print("---")
	if _fails.is_empty():
		print("PASS: both anchors walk in both directions, every edge holds")
	else:
		print("FAIL: %d" % _fails.size())
		for f in _fails:
			print("  - %s" % f)
	get_tree().quit(1 if _fails.size() else 0)
