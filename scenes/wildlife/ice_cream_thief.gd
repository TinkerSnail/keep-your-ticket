extends Node3D

## Gives a few of the boardwalk's cup-carrying guests an ice cream instead, and
## every so often sends one of the circling waterfront gulls down to take the
## scoop. The victim and the people around them look up after it. The crowd's
## generated bodies are never edited: the cone is added to a guest's hand at
## runtime and the cup they were generated with is only hidden.

@export var cone_scene: PackedScene
## How many guests carry a cone at once.
@export_range(0, 12, 1) var cones_wanted := 4
## Seconds between thefts, picked between x and y each time.
@export var theft_interval := Vector2(40.0, 90.0)
## How far from where it is circling a gull will dive.
@export_range(10.0, 300.0, 1.0) var reach := 110.0
## Seconds before a robbed guest is served again.
@export_range(5.0, 300.0, 1.0) var refill_seconds := 75.0
## How far forward a guest holds their cone, in radians from a hanging arm.
@export_range(0.0, 1.6, 0.05) var hold_angle := 1.2
@export var crowd_name := "boardwalk_crowd"

var _rng := RandomNumberGenerator.new()
var _crowd: Node
var _cones := {}        # guest -> cone node
var _refill := {}       # guest -> seconds left with an empty cone
var _next_theft := 0.0
var _dress_timer := 2.0


func _ready() -> void:
	_rng.seed = 1998
	_next_theft = _rng.randf_range(theft_interval.x, theft_interval.y) * 0.5


func _physics_process(delta: float) -> void:
	_dress_timer -= delta
	if _dress_timer <= 0.0:
		_dress_timer = 8.0
		_dress()
	for guest in _refill.keys():
		_refill[guest] -= delta
		if _refill[guest] <= 0.0:
			_undress(guest)
			_dress_timer = 0.5
	_next_theft -= delta
	if _next_theft <= 0.0:
		_next_theft = _rng.randf_range(theft_interval.x, theft_interval.y)
		if not steal_now():
			_next_theft = 8.0


func _on_stage(guest) -> bool:
	if not is_instance_valid(guest) or not (guest as Node3D).is_visible_in_tree():
		return false
	if guest.has_method("is_off_stage") and bool(guest.call("is_off_stage")):
		return false
	return true


func _dress() -> void:
	if cone_scene == null:
		return
	if _crowd == null or not is_instance_valid(_crowd):
		_crowd = get_tree().root.find_child(crowd_name, true, false)
		if _crowd == null:
			return
	# The crowd parks guests off stage as the day thins out. A cone on a guest
	# who has gone home is no use to a gull, so it moves to somebody present.
	for guest in _cones.keys():
		if not _on_stage(guest) or not is_instance_valid(_cones[guest]):
			_undress(guest)
	if _cones.size() >= cones_wanted:
		return
	for child in _crowd.get_children():
		if _cones.has(child) or not _on_stage(child):
			continue
		var cup := child.get_node_or_null("body/arm_r/cup") as Node3D
		if cup == null:
			continue
		var cone := cone_scene.instantiate() as Node3D
		cup.get_parent().add_child(cone)
		cone.position = cup.position + Vector3(0.0, 0.05, 0.0)
		# The arm comes forward so the cone is held out in front, and the cone
		# leans back by the same angle to stay upright.
		cone.rotation.x = -hold_angle
		if child.has_method("hold_up"):
			child.call("hold_up", hold_angle)
		cup.visible = false
		_cones[child] = cone
		if _cones.size() >= cones_wanted:
			return


func _undress(guest) -> void:
	var cone = _cones.get(guest)
	if is_instance_valid(cone):
		cone.queue_free()
	_cones.erase(guest)
	_refill.erase(guest)
	if is_instance_valid(guest):
		if guest.has_method("hold_up"):
			guest.call("hold_up", 0.0)
		var cup := (guest as Node).get_node_or_null("body/arm_r/cup") as Node3D
		if cup != null:
			cup.visible = true


## Picks the nearest free circling gull and the closest guest still holding a
## full cone, and starts the dive. Returns false when there is nobody to rob.
func steal_now() -> bool:
	var best_gull: Node3D = null
	var best_scoop: Node3D = null
	var best_distance := reach
	for bird in get_tree().get_nodes_in_group("gull"):
		if not bool(bird.get("starts_airborne")) or bool(bird.call("is_swooping")) or bool(bird.call("is_carrying")):
			continue
		for guest in _cones.keys():
			if _refill.has(guest) or not _on_stage(guest):
				continue
			var scoop := (_cones[guest] as Node3D).get_node_or_null("scoop") as Node3D
			if scoop == null:
				continue
			var distance := (bird as Node3D).global_position.distance_to(scoop.global_position)
			if distance < best_distance:
				best_distance = distance
				best_gull = bird
				best_scoop = scoop
	if best_gull == null:
		return false
	if not best_gull.is_connected("prize_taken", _on_prize_taken):
		best_gull.connect("prize_taken", _on_prize_taken.bind(best_gull))
	return bool(best_gull.call("steal_from_air", best_scoop))


func _on_prize_taken(_prize: Node3D, gull: Node3D) -> void:
	for guest in _cones.keys():
		if not is_instance_valid(guest) or not is_instance_valid(_cones[guest]):
			continue
		if (_cones[guest] as Node3D).get_node_or_null("scoop") != null or _refill.has(guest):
			continue
		# This is the one who just lost it: they and everyone close by look up.
		_refill[guest] = refill_seconds
		var at := (guest as Node3D).global_position
		guest.call("startle", gull, 4.5)
		for other in _crowd.get_children():
			if other != guest and other.has_method("startle") \
					and (other as Node3D).global_position.distance_to(at) < 8.0:
				other.call("startle", gull, _rng.randf_range(1.8, 3.2))
