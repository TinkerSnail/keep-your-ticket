extends Node

## Test: the boardwalk's pier and its open edges, walked by the real player.
##
## `footprint_walk_test` walks the waterfront spine centre and both edges, but
## the pier is not a route body and an edge test asks a different question:
## not "can I walk along it" but "does it stop me". Pushed square at the water,
## the wheel's jetty, the bluff, the shop backs, the yard and the coaster
## fence; none of those may arrive. The pier is walked out to the pavilion and
## back, and the Grand Circuit platform in the back lane is walked and its
## lane-side guard probed.
##
## Split out of the retired `walk_test.gd` on 2026-09-05, minus its strip-end
## probes, which named the pre-expansion boundary: the coast now tapers into
## planted ground past both ends of the promenade rather than stopping.

const ARRIVE := 1.6
const STALL_FRAMES := 90
const MAX_SECONDS := 22.0
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
	_legs = _legs_list()
	print("--- boardwalk edges: %d legs ---" % _legs.size())
	_start_leg()


## Eye height is the shore plus the same 1.2 the plaza legs use.
func _legs_list() -> Array:
	var y := ParkPlan.SHORE_TOP + 1.2
	var alley_in := Vector3(ParkPlan.BACK_LANE_X, y, ParkPlan.ALLEY_Z)
	var alley_out := Vector3(ParkPlan.PROMENADE_X + 5.0, y, ParkPlan.ALLEY_Z)
	var prom := alley_out
	# The Grand Circuit stop is a side destination off the back lane. Until
	# boarding can open a gate, the platform must not be a pedestrian crossing
	# into a moving service.
	var tram_lane := Vector3(ParkPlan.BACK_LANE_X, y, 5.0)
	var tram_apron := Vector3(-76.85, y, 5.0)
	var tram_north := Vector3(-76.85, y, 11.0)
	var tram_south := Vector3(-76.85, y, 25.0)
	# Onto the pier is two legs, out of the alley then south along the promenade
	# to the mouth: a shallow diagonal is the waypoint trap.
	var pz := ParkPlan.PIER_ROOT.y
	var mouth := Vector3(ParkPlan.PROMENADE_X + 5.0, y, pz)
	return [
		["bw lane -> tram", alley_in, tram_lane, true],
		["bw tram apron", tram_lane, tram_apron, true],
		["bw tram platform in", tram_apron, tram_north, true],
		["bw tram platform length", tram_north, tram_south, true],
		["bw tram platform back", tram_south, tram_north, true],
		["bw tram platform out", tram_north, tram_apron, true],
		["bw tram -> lane", tram_apron, tram_lane, true],
		["bw tram lane guard holds", Vector3(-76.85, y, 18.0), Vector3(-70.0, y, 18.0), false],
		["bw tram -> alley", tram_lane, alley_in, true],
		["bw lane -> alley", alley_in, alley_out, true],
		["bw alley -> pier mouth", prom, mouth, true],
		["bw onto the pier", mouth, Vector3(-106, y, pz), true],
		["bw out the pier", Vector3(-106, y, pz), Vector3(-149, y, pz), true],
		["bw pavilion holds", Vector3(-149, y, pz), Vector3(-162, y, pz), false],
		["bw back down pier", Vector3(-149, y, pz), Vector3(-102, y, pz), true],
		["bw mouth -> alley", mouth, prom, true],
		# The jetty: the promenade rail breaks across the wheel's platform, and
		# what stops the player there is the platform's own face, half a metre
		# proud. Start west of the lamp standards at `PROMENADE_X`, or the leg
		# stops on a lamp and passes for the wrong reason.
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
		["bw bluff holds n", Vector3(-70.0, y, -50.0), Vector3(-50.0, y, -50.0), false],
	]


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
		print("PASS: the pier walks both ways and every boardwalk edge holds")
	else:
		print("FAIL: %d" % _fails.size())
		for f in _fails:
			print("  - %s" % f)
	get_tree().quit(1 if _fails.size() else 0)
