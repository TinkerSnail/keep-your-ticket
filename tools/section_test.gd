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

## Terrace, stair head, the landing, and a point behind the shut gate at the
## foot. The last one is not reachable — the gate is solid and stops the player
## about a third of a metre short of it, which puts them inside the crossing
## volume. Walking at something they cannot get to is how the seam gets tripped
## rather than approached, and if it never fires they stall against the gate and
## the stall detector says so.
const OUTBOUND := [
	Vector3(-38.0, 0.2, -9.7),
	Vector3(-42.0, 0.0, -9.7),
	Vector3(-44.7, -1.0, -7.5),
	Vector3(-44.7, -6.0, 8.2),
]

## Back the other way, aimed off the north edge of the stub deck for the same
## reason: the crossing is between here and there, and the player should meet it
## well before they run out of planking.
const INBOUND := [
	Vector3(-44.7, -5.8, 6.0),
]

var _player: CharacterBody3D
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

	# Onto the terrace by hand. Getting there from the spawn is `walk_test.gd`'s
	# job and repeating it here only buys a longer run.
	_player.global_position = OUTBOUND[0]
	_player.velocity = Vector3.ZERO
	_last = _player.global_position
	ParkSections.section_entered.connect(_on_entered)


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
			_walk(OUTBOUND)
		1:
			_check_landing(&"boardwalk", Vector3(-44.7, -5.8, 14.0))
		2:
			_walk(INBOUND)
		3:
			_check_landing(&"plaza", Vector3(-44.7, -5.8, 4.8))


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
