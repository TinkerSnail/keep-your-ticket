extends Node

## Dev tool, throwaway: walk into the fountain from every side.
##
## The barrier changed shape. It used to be one `CSGCylinder3D` of radius 9 and
## height 0.9, and it is now a ring of 36 kerb blocks and 36 coping blocks whose
## outer faces form an inscribed 36-gon. That is a different collider in three
## ways that a screenshot has no opinion about: it is faceted rather than
## smooth, it is 72 bodies rather than one, and it is 52cm tall rather than 90.
##
## Three things have to be true and only a driven player can say so:
##
##   1. **You are stopped.** A gap between two blocks, or a ring whose radius
##      came out short, is a hole into the middle of the plaza's centrepiece.
##   2. **You are stopped at the right radius**, near 9 rather than well outside
##      it — the whole point of not moving `FOUNTAIN_RADIUS` was that nothing
##      about where a person may stand changed.
##   3. **You do not end up on top of it.** `CharacterBody3D` has no step-up, so
##      a 52cm kerb should be unclimbable; if the capsule rides up onto the
##      coping the player is standing in the water.
##
## Sixteen bearings, because a 36-gon has 36 corners and a rule that only holds
## at the middle of a facet is not a rule.

const BEARINGS := 16
const START_R := 14.0
const SECONDS := 5.0

## Where the coping's outer face is, and how close a capsule should get to it.
## The body's radius is a little over a third of a metre, so anything from about
## 9.2 to 9.8 is "stopped by the kerb". Past 10.5 something else stopped it
## first, which would be a prop pushed into the skirt rather than a fountain
## fault — but it is still a thing to know.
const RIM := 9.0
const NEAR = 10.6

var _player: CharacterBody3D
var _i := 0
var _t := 0.0
var _fails: Array = []
var _lines: Array = []


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run(main)


func _run(main: Node) -> void:
	ParkClock.running = false
	ParkClock.set_clock(16, 0)
	await get_tree().create_timer(2.0).timeout
	_player = main.get_node_or_null("player") as CharacterBody3D
	if _player == null:
		push_error("no player")
		get_tree().quit(1)
		return
	_start()


func _start() -> void:
	if _i >= BEARINGS:
		_report()
		return
	var a := TAU * float(_i) / float(BEARINGS)
	var from := Vector3(sin(a) * START_R, 0.4, cos(a) * START_R)
	_player.global_position = from
	_player.velocity = Vector3.ZERO
	# Aim at the origin. `atan2(-d.x, -d.z)` is the same convention `walk_test`
	# uses, so a leg here and a leg there mean the same thing by "forward".
	var d := -from
	_player.rotation.y = atan2(-d.x, -d.z)
	_t = 0.0
	Input.action_press("move_forward")


func _physics_process(delta: float) -> void:
	if _player == null or _i >= BEARINGS:
		return
	_t += delta
	if _t < SECONDS:
		return
	Input.action_release("move_forward")

	var p := _player.global_position
	var r := Vector2(p.x, p.z).length()
	var blockers := _blockers()
	var bad := ""
	if r < RIM:
		bad = "INSIDE the pool"
	elif p.y > 0.35:
		bad = "climbed onto the coping"
	elif r > NEAR:
		# Stopping short is only a fault if *nothing* stopped you. Due south the
		# run is blocked by `bench_1_back`, which is one of the ring of five that
		# `_benches` puts on the fountain's skirt on purpose — the bench is meant
		# to be there and the probe is meant to say so by name rather than to
		# call it a hole in the kerb.
		bad = "stopped early by nothing" if blockers == "" else ""
	var deg := int(round(360.0 * float(_i) / float(BEARINGS)))
	var line := "%s %3d deg  r=%.2f  y=%.2f  [%s] %s" % [
		"FAIL" if bad != "" else "ok  ", deg, r, p.y, blockers, bad]
	_lines.append(line)
	if bad != "":
		_fails.append(line)

	_i += 1
	_t = 0.0
	_start()


func _blockers() -> String:
	var seen := {}
	for i in _player.get_slide_collision_count():
		var c: KinematicCollision3D = _player.get_slide_collision(i)
		var o: Object = c.get_collider()
		if o != null:
			seen[String(o.get("name"))] = true
	return ", ".join(seen.keys())


func _report() -> void:
	print("=== fountain probe ===")
	for l in _lines:
		print(l)
	if _fails.is_empty():
		print("PASS %d bearings stopped at the kerb" % BEARINGS)
	else:
		print("FAIL %d of %d" % [_fails.size(), BEARINGS])
	get_tree().quit(0 if _fails.is_empty() else 1)
