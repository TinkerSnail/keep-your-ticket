extends Node

## Does the dev flight do what it is for: leave the ground on the `dev_fly`
## action, travel along the look and through a wall, and put the player back on
## ground when it is switched off somewhere there is none.
##
## Driven with actions through `Input.parse_input_event`, the same argument as
## `menu_test.gd`: the toggle is an `_unhandled_input` handler on an action that
## only exists because the player registered it, and calling `set_flying`
## directly would pass without either being true.

const SETTLE := 1.5
## Under the plaza floor, where terrain collision faces away and a walking body
## would fall for ever.
const BURIED := Vector3(12.0, -30.0, 12.0)

var _failures := 0
var _checks := 0


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	await get_tree().create_timer(SETTLE).timeout

	var player := get_tree().get_first_node_in_group("player") as Player
	if player == null:
		push_error("fly_test: no player in the tree")
		get_tree().quit(1)
		return

	var ground_y := player.global_position.y
	await _tap("dev_fly")
	_check("dev_fly leaves the ground", player.flying, true)

	# Straight up first, so the run along the look starts clear of the crowd.
	await _hold("jump", 1.0)
	var rise := player.global_position.y - ground_y
	_check("jump climbs", rise > 5.0, true)

	# Level flight along the look has to cover ground at the set speed and hold
	# its height: no gravity, and nothing in the plaza stops it.
	# The climb eases out over a few frames; measure once it has.
	await get_tree().create_timer(0.75).timeout
	player.fly_speed = Player.FLY_SPEEDS[2]
	var from := player.global_position
	var ahead := -player.head.global_transform.basis.z
	await _hold("move_forward", 2.0)
	var moved := player.global_position - from
	_check("forward follows the look", moved.normalized().dot(ahead) > 0.99, true)
	_check("covers ground at fly speed", moved.length() > Player.FLY_SPEEDS[2] * 1.5, true)
	_check("holds height", absf(moved.y) < 0.5, true)

	# Through the floor rather than onto it.
	await _hold("dev_fly_down", 1.0)
	_check("descends through the ground", player.global_position.y < -20.0, true)

	player.global_position = BURIED
	await _tap("dev_fly")
	_check("dev_fly lands", player.flying, false)
	await get_tree().create_timer(1.0).timeout
	_check("landed on ground above, not falling", player.global_position.y > -1.0, true)
	_check("standing", player.is_on_floor(), true)

	print("")
	print("fly_test: %d checks, %d failed" % [_checks, _failures])
	get_tree().quit(1 if _failures > 0 else 0)


func _check(what: String, got, want) -> void:
	_checks += 1
	var ok: bool = got == want
	if not ok:
		_failures += 1
	print("%s  %s  (got %s, wanted %s)" % ["PASS" if ok else "FAIL", what, got, want])


func _send(action: String, pressed: bool) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = pressed
	Input.parse_input_event(event)


func _tap(action: String) -> void:
	_send(action, true)
	await get_tree().process_frame
	_send(action, false)
	await get_tree().physics_frame
	await get_tree().physics_frame


func _hold(action: String, seconds: float) -> void:
	_send(action, true)
	await get_tree().create_timer(seconds).timeout
	_send(action, false)
	await get_tree().physics_frame
