extends Node

## Dev tool: walks the player out of the plaza, across the west seam into the
## boardwalk, and back again.
##
## The same argument as `walk_test.gd`: the player is driven by pressing the
## real input actions so the run goes through `_physics_process`, `_try_step`
## and the spring arm exactly as a player's would. What is being tested here is
## not the geometry of the stair — `walk_test.gd` already walks that — but the
## threshold: that the swap fires, that the player is put down on a floor rather
## than inside the bluff, that they are still standing a moment later, and that
## the way back exists and lands them where they started.
##
## A section boundary is the easiest thing in the project to get subtly wrong
## and the hardest to see in a screenshot. An arrival point half a metre out is
## a player falling through the world, and it looks identical to a working one
## right up until it does not.
##
## Every position below comes from `ParkPlan`. That matters for a reason beyond
## tidiness: `boardwalk_stub.tscn` *cannot* read `ParkPlan` — it is a scene, and
## a scene's transforms are baked literals with nowhere to put an expression. So
## the far side of the seam is still a hand-placed number and always will be
## until something generates it.
##
## This test is what stops that being a silent duplication. It walks to a marker
## placed by hand in the stub and asserts it is where `ParkPlan` says it should
## be, so the two agreeing is *checked* rather than assumed. Duplication a test
## enforces is fine; duplication nothing looks at is how the stair foot ended up
## written down as three different numbers in one afternoon.

## Close enough to a waypoint to call it reached. Tight, because the last
## waypoint of each route is deliberately on the far side of a trigger volume
## and a loose tolerance counts it as reached from short of the trigger — which
## is a test that walks up to the seam, declares itself finished and never
## crosses anything.
const ARRIVE := 0.8

## How near the expected arrival the player has to land. Generous, because they
## are still walking when they get there — the crossing keeps their momentum on
## purpose — and a metre of drift is the transition working, not failing.
const LANDING_TOLERANCE := 2.5

## Below this and they have gone through the floor. The boardwalk deck is at −6
## and the stair foot is the lowest thing anybody should reach.
const FLOOR_LIMIT := -12.0

const STALL_FRAMES := 240
const MAX_SECONDS := 60.0

## How far past the shut gate the last waypoint of each leg sits. Deliberately
## unreachable — the gate is solid and stops the player short of it, which puts
## them inside the crossing volume. Walking at something you cannot get to is
## how the seam gets tripped rather than merely approached, and if it never
## fires the player stalls against the gate and the stall detector says so.
##
## West on both legs, because the gate is in the well's west face. It was south
## until 2026-08-12 and this test is what caught the change: the player walked
## down, pushed at the back wall of the well and stalled there, which is exactly
## what a wrongly-placed threshold looks like from inside the game.
const PAST_THE_GATE := 2.7

## Terrace, stair head, the landing, and the point behind the gate. Built in
## `_ready` rather than declared const, because they are derived from `ParkPlan`
## and a route that stops following the plan is the failure this exists to
## catch.
var _outbound: Array[Vector3] = []
var _inbound: Array[Vector3] = []

var _player: CharacterBody3D
var _seam := 0
var _phase := 0
var _wp := 0
var _t := 0.0
var _still := 0
var _last := Vector3.ZERO
var _fails: Array = []
var _notes: Array = []
var _waiting := false
## Set by the signal, consumed by the next frame that is not mid-transition.
## The seam is what ends a leg — not running out of waypoints, because the
## waypoint that trips it is on the far side of a teleport and steering at it
## afterwards walks the player straight back through the gate they came out of.
var _crossed := false


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 6:
		await get_tree().physics_frame

	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if _player == null:
		_fail("no player in the tree")
		return _report()

	if ParkSections.current() != &"plaza":
		_fail("started in '%s' rather than the plaza" % ParkSections.current())

	# The terrace and the stair head are on the plan's own west passage; the
	# landing is one flight down, which is `treads_a` risers below the terrace.
	# **The seam moved to the arch on 2026-08-14**, so this no longer walks the
	# stair. Out is west along the spoke and under the arch; back is east under the
	# same arch. Both routes end past the crossing at a point the player is never
	# allowed to reach on foot — walking at something unreachable is how a seam
	# gets tripped rather than merely approached, and it is the same trick the
	# stair version used.
	#
	# What this is really checking has changed with it. It used to ask whether the
	# player landed on a floor rather than inside the bluff. Now the outbound
	# landing is on `terrace_floor`, which exists only in the boardwalk's copy of
	# the plaza's boundary — so if that slab is ever missing or mispositioned, the
	# player crosses the arch and falls six metres to the shore, and this is what
	# says so.
	# **Two seams since 2026-08-18, and it is a table now rather than one pair of
	# routes.** The east gate got a load point mirroring the west's, and a test
	# hard-wired to one seam would have left the new one uncovered — which is
	# exactly the hole `walk_test` opened when its through-gate legs were pulled
	# back off the crossing volume. Between them these two files must cover every
	# seam in the park; neither covering it is how a seam goes untested.
	_load_seam(0)
	ParkSections.section_entered.connect(_on_entered)


## Every seam in the park, out and back. `out` and `in` both end past the
## crossing at a point the player cannot reach on foot — walking at something
## unreachable is how a seam gets tripped rather than merely approached.
const SEAMS := [
	{
		"name": "the west arch",
		"out": [Vector3(-18.0, 0.2, -2.0), Vector3(-30.0, 0.2, -2.0),
			Vector3(-46.0, 0.2, -2.0)],
		"in": [Vector3(-42.0, 0.2, -2.0), Vector3(-28.0, 0.2, -2.0)],
		"to": &"boardwalk",
	},
	# The east gate. Its outbound landing is the forecourt slab and its inbound
	# one the plaza's own paving, so a missing `east_court` puts the player on the
	# hillside's footing three metres down and this is what says so.
	{
		"name": "the east gate",
		"out": [Vector3(24.0, 0.2, -2.0), Vector3(36.0, 0.2, -2.0),
			Vector3(60.0, 0.2, -2.0)],
		"in": [Vector3(48.0, 0.2, -2.0), Vector3(20.0, 0.2, -2.0)],
		"to": &"terraces",
	},
]

## Arrival points, per seam, in the same order. Kept beside `SEAMS` rather than
## in it because they are `ParkPlan` constants and a table of literals next to a
## table of references is how one of them goes stale.
func _arrivals(i: int) -> Array:
	if i == 0:
		return [ParkPlan.ARCH_ARRIVE_WEST, ParkPlan.ARCH_ARRIVE_EAST]
	return [ParkPlan.EAST_ARRIVE_OUT, ParkPlan.EAST_ARRIVE_IN]


## Put the player at the head of a seam's outbound route by hand. Getting there
## from the spawn is `walk_test.gd`'s job and repeating it here only buys a
## longer run — and after the first seam the player is on the far side of the
## park from the second one.
func _load_seam(i: int) -> void:
	_seam = i
	var spec: Dictionary = SEAMS[i]
	_outbound.assign(spec["out"])
	_inbound.assign(spec["in"])
	_note("--- %s ---" % spec["name"])
	_player.global_position = _outbound[0]
	_player.velocity = Vector3.ZERO
	_last = _player.global_position
	_phase = 0
	_wp = 0
	_t = 0.0
	_still = 0
	_waiting = false
	_crossed = false


func _on_entered(id: StringName) -> void:
	_note("entered '%s' at %s" % [id, _fmt(_player.global_position)])
	_crossed = true


func _physics_process(delta: float) -> void:
	if _player == null or _phase > 3:
		return

	_t += delta
	if _t > MAX_SECONDS:
		_fail("ran out of time in phase %d" % _phase)
		return _finish()

	if _player.global_position.y < FLOOR_LIMIT:
		_fail("fell through the world in phase %d, at %s"
			% [_phase, _fmt(_player.global_position)])
		return _finish()

	# The transition drives the walk itself and ignores input. Pressing actions
	# through it would prove nothing and releasing them would fight it.
	if _player.has_method("is_crossing") and _player.is_crossing():
		_release()
		return

	# Consumed here rather than in the signal, because the signal fires under the
	# fade while the player is still on rails and there is nothing to decide yet.
	if _crossed:
		_crossed = false
		_release()
		_wp = 0
		_t = 0.0
		_still = 0
		_waiting = false
		_last = _player.global_position
		_phase = 1 if _phase == 0 else 3
		return

	match _phase:
		0:
			_walk(_outbound)
		1:
			_check_landing(SEAMS[_seam]["to"], _arrivals(_seam)[0])
		2:
			_walk(_inbound)
		3:
			_check_landing(&"plaza", _arrivals(_seam)[1])


## Steer at the next waypoint and hold forward. Yaw is set rather than turned
## because this is a rig, not a demonstration of the controls.
## Reaching the end of a route without the seam having fired means the gate did
## not catch the player — walked past, too small, wrong collision mask. That is
## the failure this whole tool exists to notice, so it is not a quiet advance.
func _walk(route: Array) -> void:
	if _wp >= route.size():
		_release()
		_fail("walked the whole route in phase %d without crossing — at %s"
			% [_phase, _fmt(_player.global_position)])
		_finish()
		return

	var target: Vector3 = route[_wp]
	var here := _player.global_position
	var flat := Vector2(target.x - here.x, target.z - here.z)
	if flat.length() < ARRIVE:
		_wp += 1
		return

	_player.rotation.y = atan2(-flat.x, -flat.y)
	Input.action_press("move_forward")

	if here.distance_to(_last) < 0.004:
		_still += 1
		if _still > STALL_FRAMES:
			_fail("stuck in phase %d at %s, heading for %s"
				% [_phase, _fmt(here), _fmt(target)])
			_finish()
	else:
		_still = 0
	_last = here


## Give the arrival a moment to settle before judging it. The player is put down
## still walking, so the frame they land on is not the frame worth measuring.
func _check_landing(want: StringName, near: Vector3) -> void:
	_release()
	if not _waiting:
		_waiting = true
		_t = 0.0
		return
	if _t < 0.6:
		return
	_waiting = false

	if ParkSections.current() != want:
		_fail("expected to be in '%s', am in '%s'" % [want, ParkSections.current()])
	var at := _player.global_position
	var off := at.distance_to(near)
	if off > LANDING_TOLERANCE:
		_fail("landed %.2fm from the arrival point in '%s' — at %s, wanted %s"
			% [off, want, _fmt(at), _fmt(near)])
	else:
		_note("landed %.2fm from the arrival point in '%s'" % [off, want])
	if not _player.is_on_floor():
		_fail("not standing on anything in '%s', at %s" % [want, _fmt(at)])

	if _phase == 1:
		_phase = 2
		_t = 0.0
		_last = at
		_still = 0
	elif _seam + 1 < SEAMS.size():
		_load_seam(_seam + 1)
	else:
		_finish()


func _release() -> void:
	if Input.is_action_pressed("move_forward"):
		Input.action_release("move_forward")


func _fail(what: String) -> void:
	_fails.append(what)


func _note(what: String) -> void:
	_notes.append(what)


func _fmt(v: Vector3) -> String:
	return "(%.1f, %.1f, %.1f)" % [v.x, v.y, v.z]


func _finish() -> void:
	_phase = 4
	_release()
	_report()


func _report() -> void:
	print("--- section crossing ---")
	for n in _notes:
		print("  . %s" % n)
	if _fails.is_empty():
		print("  ok: plaza -> boardwalk -> plaza, both arrivals on their feet")
	else:
		for f in _fails:
			print("  FAIL: %s" % f)
	get_tree().quit(0 if _fails.is_empty() else 1)
