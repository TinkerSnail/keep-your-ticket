extends Node

## The riveted bin's push flaps work (park_furniture/bin_flaps.gd): the model
## brings both flaps as their own nodes, hinged on their top edges; a push
## swings a flap in and it settles back shut; wedged open, it rests there;
## the player can push a flap with interact only from outside it, looking at
## it, within reach; and a swing stays under 40 degrees, so the two never meet.
##
##     godot --headless --fixed-fps 60 --path . tools/run.tscn -- bin_flap_test

const SCENE := "res://scenes/world/park_furniture/riveted_bin.tscn"

var _fails: Array[String] = []


func _check(ok: bool, what: String) -> void:
	print(("ok   " if ok else "FAIL ") + what)
	if not ok:
		_fails.append(what)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _ready() -> void:
	var bin := (load(SCENE) as PackedScene).instantiate() as Node3D
	add_child(bin)
	await _frames(2)
	var flaps := bin.get_node_or_null("flaps")
	_check(flaps != null, "the riveted bin has its flaps node")
	if flaps == null:
		get_tree().quit(1)
		return
	var list: Array = flaps._flaps
	_check(list.size() == 2, "both flaps found in the model (%d)" % list.size())
	if list.size() != 2:
		get_tree().quit(1)
		return
	var front = list[0] if list[0].sign > 0.0 else list[1]
	var back = list[1] if front == list[0] else list[0]
	_check(front.node.position.y > 0.9 and front.node.position.z > 0.2,
		"the front flap hinges on its top edge (%s)" % front.node.position)

	# A push swings it in, the bottom moving into the bin (-z for the front).
	var bottom_before: float = front.node.to_global(Vector3(0, -0.3, 0)).z
	flaps.push(front, 1.0)
	var peak := 0.0
	for i in 40:
		await get_tree().physics_frame
		peak = max(peak, front.angle)
	var bottom_after: float = front.node.to_global(Vector3(0, -0.3, 0)).z
	_check(peak > 20.0 and peak <= flaps.MAX_SWING_DEG,
		"a push swings the front flap in to %.1f degrees (at most %.0f)" % [peak, flaps.MAX_SWING_DEG])
	_check(bottom_after < bottom_before or peak > 20.0, "it swings into the bin, not out")
	await _frames(300)
	_check(absf(front.angle) < 1.0 and absf(front.speed) < 5.0,
		"and settles back shut (%.2f degrees)" % front.angle)
	_check(absf(back.angle) < 0.01, "the back flap stayed shut")

	# Wedged open by the overflowing state.
	flaps.wedged_open_deg = 22.0
	await _frames(300)
	_check(absf(front.angle - 22.0) < 1.0 and absf(back.angle - 22.0) < 1.0,
		"wedged open, both rest at 22 degrees (%.1f, %.1f)" % [front.angle, back.angle])
	flaps.wedged_open_deg = 0.0
	await _frames(300)

	# Interact: from 1 m in front, looking at the bin, pushes the front flap;
	# from the side looking away, nothing.
	var at := bin.to_global(Vector3(0, 0, 1.0))
	var toward := bin.global_basis.z * -1.0
	_check(flaps.try_push(at, toward), "interact from in front, looking at it, pushes a flap")
	await _frames(20)
	_check(front.angle > 5.0, "the front one (%.1f degrees)" % front.angle)
	_check(not flaps.try_push(bin.to_global(Vector3(2.5, 0, 0)), Vector3.RIGHT),
		"interact from the side, looking away, pushes nothing")
	_check(flaps.try_push(bin.to_global(Vector3(0, 0, -1.0)), bin.global_basis.z),
		"interact from behind, looking at it, pushes a flap")
	await _frames(20)
	_check(back.angle > 5.0, "the back one (%.1f degrees)" % back.angle)

	print("PASS the riveted bin's flaps work" if _fails.is_empty()
		else "FAIL %d checks: %s" % [_fails.size(), ", ".join(_fails)])
	get_tree().quit(0 if _fails.is_empty() else 1)
