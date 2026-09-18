class_name ParkBird
extends Node3D

## Shared motion for the park's directly authored bird scenes.
##
## The visible gull and pigeon forms live in ordinary `.tscn` scenes so every
## body part remains selectable and replaceable in Godot. This script owns only
## their small repertoire: looking, pecking, strolling, flushing and circling.
## Birds are ambient life and photographic subjects. They expose no collectible
## or scoring state.

enum Activity { IDLE, PECK, WALK, FLY }
enum ColonyPhase { NONE, ROOST, OUTBOUND, FORAGE, INBOUND }

@export_enum("gull", "pigeon") var species := "gull"
@export var juvenile := false
@export var black_tail := false
@export var starts_airborne := false
@export var pose_root_path: NodePath = NodePath("visual")
@export var model_has_authored_plumage := false
@export_range(0.25, 8.0, 0.05) var wander_radius := 2.4
@export_range(1.0, 12.0, 0.1) var scare_radius := 3.8
@export_range(0.1, 3.0, 0.05) var walk_speed := 0.58
@export_range(2.0, 40.0, 0.5) var flight_radius := 14.0
@export_range(0.2, 8.0, 0.1) var flight_relief := 1.8
@export_group("Colony flight")
@export_range(8.0, 80.0, 1.0) var colony_flight_speed := 42.0
@export_range(10.0, 120.0, 1.0) var colony_cruise_relief := 48.0
@export_range(40.0, 500.0, 5.0) var colony_long_leg_height := 340.0
@export_range(4.0, 90.0, 1.0) var colony_roost_min_seconds := 16.0
@export_range(4.0, 90.0, 1.0) var colony_roost_max_seconds := 34.0
@export_range(4.0, 90.0, 1.0) var colony_forage_min_seconds := 24.0
@export_range(4.0, 90.0, 1.0) var colony_forage_max_seconds := 48.0
@export_range(1, 4, 1) var colony_sites_per_trip := 2
@export var rng_seed := 1998

@onready var visual: Node3D = $visual
@onready var pose_root: Node3D = get_node(pose_root_path) as Node3D
@onready var head_pivot: Node3D = pose_root.get_node("head_pivot") as Node3D
@onready var wing_left: Node3D = pose_root.get_node("wing_left") as Node3D
@onready var wing_right: Node3D = pose_root.get_node("wing_right") as Node3D
@onready var leg_left: Node3D = pose_root.get_node("leg_left") as Node3D
@onready var leg_right: Node3D = pose_root.get_node("leg_right") as Node3D
@onready var beak_upper_pivot: Node3D = head_pivot.get_node("beak/upper_pivot") as Node3D
@onready var beak_lower_pivot: Node3D = head_pivot.get_node("beak/lower_pivot") as Node3D
@onready var wing_left_outer: Node3D = _find_outer_pivot(wing_left)
@onready var wing_right_outer: Node3D = _find_outer_pivot(wing_right)
@onready var wing_left_folded: Node3D = wing_left.get_node_or_null("folded_overlay") as Node3D
@onready var wing_right_folded: Node3D = wing_right.get_node_or_null("folded_overlay_001") as Node3D
@onready var wing_left_outer_folded: Node3D = wing_left_outer.get_node_or_null("outer_folded_overlay") as Node3D if wing_left_outer != null else null
@onready var wing_right_outer_folded: Node3D = wing_right_outer.get_node_or_null("outer_folded_overlay_001") as Node3D if wing_right_outer != null else null

var activity := Activity.IDLE
var _home := Vector3.ZERO
var _ground_y := 0.0
var _target := Vector3.ZERO
var _timer := 0.0
var _phase := 0.0
var _flight_elapsed := 0.0
var _flight_duration := 4.8
var _flight_from := Vector3.ZERO
var _flight_control := Vector3.ZERO
var _flight_to := Vector3.ZERO
var _flee_cooldown := 0.0
var _player: Node3D
var _rng := RandomNumberGenerator.new()
var _visual_rest := Vector3.ZERO
var _visual_rotation_rest := Vector3.ZERO
var _head_rest := Vector3.ZERO
var _head_position_rest := Vector3.ZERO
var _wing_left_rest := Vector3.ZERO
var _wing_right_rest := Vector3.ZERO
var _wing_left_outer_rest := Vector3.ZERO
var _wing_right_outer_rest := Vector3.ZERO
var _leg_left_rest := Vector3.ZERO
var _leg_right_rest := Vector3.ZERO
var _beak_upper_rest_x := 0.0
var _beak_lower_rest_x := 0.0
var _beak_open := 0.0
var _forced_beak_open := -1.0
var _beak_first_call_phase := 0.0
var _colony_enabled := false
var _colony_resident := false
var _colony_roost := Vector3.ZERO
var _colony_foraging_sites: Array[Vector3] = []
var _colony_phase := ColonyPhase.NONE
var _colony_phase_timer := 0.0
var _colony_site_index := 0
var _colony_sites_visited := 0
var _colony_foraging_centre := Vector3.ZERO


func _ready() -> void:
	add_to_group("wildlife")
	add_to_group("bird")
	add_to_group(species)
	_home = global_position
	_ground_y = global_position.y
	_rng.seed = rng_seed
	_visual_rest = visual.position
	_visual_rotation_rest = visual.rotation
	_head_rest = head_pivot.rotation
	_head_position_rest = head_pivot.position
	_wing_left_rest = wing_left.rotation
	_wing_right_rest = wing_right.rotation
	if wing_left_outer != null:
		_wing_left_outer_rest = wing_left_outer.rotation
	if wing_right_outer != null:
		_wing_right_outer_rest = wing_right_outer.rotation
	_leg_left_rest = leg_left.rotation
	_leg_right_rest = leg_right.rotation
	_beak_upper_rest_x = beak_upper_pivot.rotation.x
	_beak_lower_rest_x = beak_lower_pivot.rotation.x
	_apply_plumage_variant()
	_apply_adult_tail_variant()
	_phase = _rng.randf_range(0.0, TAU)
	# Every bird begins with a neutral portrait and then calls on its own stable
	# offset. This keeps catalog loads closed without synchronizing the flock.
	_beak_first_call_phase = _phase + 2.0 + float(rng_seed % 7) * 0.4
	_timer = _rng.randf_range(0.5, 2.8)
	if starts_airborne:
		activity = Activity.FLY
	else:
		_choose_idle_heading()


func _physics_process(delta: float) -> void:
	_phase += delta
	_flee_cooldown = maxf(0.0, _flee_cooldown - delta)
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node3D

	if _colony_enabled:
		_update_colony(delta)
	elif starts_airborne:
		_update_circling(delta)
	else:
		if activity != Activity.FLY and _flee_cooldown <= 0.0 and _player != null:
			var distance := Vector2(global_position.x - _player.global_position.x,
				global_position.z - _player.global_position.z).length()
			if distance < scare_radius:
				scare_from(_player.global_position)
		match activity:
			Activity.IDLE:
				_update_idle(delta)
			Activity.PECK:
				_update_peck(delta)
			Activity.WALK:
				_update_walk(delta)
			Activity.FLY:
				_update_escape_flight(delta)
	_animate_pose(delta)


## Public for interactions and the focused wildlife check. Passing a position
## rather than a Player keeps the reaction reusable for guests or vehicles.
func scare_from(point: Vector3) -> void:
	if _colony_enabled or starts_airborne or activity == Activity.FLY:
		return
	var away := global_position - point
	away.y = 0.0
	if away.length_squared() < 0.01:
		away = Vector3.FORWARD.rotated(Vector3.UP, _rng.randf_range(0.0, TAU))
	away = away.normalized()
	var sideways := Vector3(-away.z, 0.0, away.x) * _rng.randf_range(-2.8, 2.8)
	_flight_from = global_position
	_flight_to = _home + Vector3(
		_rng.randf_range(-wander_radius * 0.45, wander_radius * 0.45), 0.0,
		_rng.randf_range(-wander_radius * 0.45, wander_radius * 0.45))
	_flight_to.y = _ground_y
	_flight_control = _flight_from + away * _rng.randf_range(6.0, 9.0) + sideways
	_flight_control.y = _ground_y + _rng.randf_range(3.2, 5.2)
	_flight_elapsed = 0.0
	_flight_duration = _rng.randf_range(4.2, 5.8)
	activity = Activity.FLY


func is_flying() -> bool:
	return activity == Activity.FLY


## Connects this explicitly placed bird to editor-owned roost and feeding
## markers. The colony scheduler supplies positions but never owns their shape
## or placement, so moving a marker in wildlife.tscn moves the behavior with it.
func configure_colony(roost: Vector3, foraging_sites: Array[Vector3],
		resident: bool, initial_site_index: int) -> void:
	if species != "gull" or foraging_sites.is_empty():
		return
	_colony_enabled = true
	_colony_resident = resident
	_colony_roost = roost
	_colony_foraging_sites = foraging_sites.duplicate()
	_colony_site_index = posmod(initial_site_index, _colony_foraging_sites.size())
	_colony_sites_visited = 0
	_home = _colony_roost
	_ground_y = _colony_roost.y
	add_to_group("gull_colony_member")
	if _colony_resident:
		add_to_group("gull_roost_resident")
		_enter_colony_roost(true)
	else:
		add_to_group("gull_colony_commuter")
		_enter_colony_foraging(_colony_site_index, true)


func is_colony_member() -> bool:
	return _colony_enabled


func is_colony_resident() -> bool:
	return _colony_enabled and _colony_resident


func is_roosting() -> bool:
	return _colony_enabled and _colony_phase == ColonyPhase.ROOST


func get_colony_roost() -> Vector3:
	return _colony_roost


func get_colony_foraging_sites() -> Array[Vector3]:
	return _colony_foraging_sites.duplicate()


## Holds the articulated bill at an explicit amount for authored moments and
## visual proof. Zero is shut and one is the species' full, readable gape.
func set_beak_open(amount: float) -> void:
	_forced_beak_open = clampf(amount, 0.0, 1.0)
	_beak_open = _forced_beak_open
	_pose_beak(_beak_open)


## Returns the bill to its sparse deterministic ambient-call motion.
func clear_beak_pose() -> void:
	_forced_beak_open = -1.0


func get_beak_open_amount() -> float:
	return _beak_open


## Gives focused checks and authored events one stable way to reach a model.
## Older primitive birds keep their parts directly under visual; imported gulls
## point this at the editable Blender model nested inside the wrapper.
func get_pose_root() -> Node3D:
	return pose_root


func _update_idle(delta: float) -> void:
	_timer -= delta
	if _timer > 0.0:
		return
	if _rng.randf() < (0.64 if species == "pigeon" else 0.38):
		activity = Activity.PECK
		_timer = _rng.randf_range(0.8, 2.0)
	else:
		_choose_walk_target()


func _update_peck(delta: float) -> void:
	_timer -= delta
	if _timer <= 0.0:
		activity = Activity.IDLE
		_timer = _rng.randf_range(0.6, 2.5)
		_choose_idle_heading()


func _update_walk(delta: float) -> void:
	var offset := _target - global_position
	offset.y = 0.0
	if offset.length() < 0.08:
		activity = Activity.IDLE
		_timer = _rng.randf_range(0.7, 2.8)
		return
	_face_direction(offset)
	global_position += offset.normalized() * minf(walk_speed * delta, offset.length())
	global_position.y = _ground_y


func _update_escape_flight(delta: float) -> void:
	_flight_elapsed += delta
	var t := clampf(_flight_elapsed / _flight_duration, 0.0, 1.0)
	var a := _flight_from.lerp(_flight_control, t)
	var b := _flight_control.lerp(_flight_to, t)
	var next := a.lerp(b, t)
	var travel := next - global_position
	if travel.length_squared() > 0.0001:
		_face_direction(travel)
	global_position = next
	if t >= 1.0:
		global_position.y = _ground_y
		activity = Activity.IDLE
		_timer = _rng.randf_range(1.5, 3.5)
		_flee_cooldown = 1.2


func _update_circling(delta: float) -> void:
	var rate := (2.4 if species == "gull" else 3.0) / maxf(flight_radius, 1.0)
	var angle := _phase * rate + float(rng_seed % 17)
	var next := _home + Vector3(
		cos(angle) * flight_radius,
		sin(angle * 1.7) * flight_relief,
		sin(angle) * flight_radius * 0.72)
	var tangent := next - global_position
	if tangent.length_squared() > 0.0001:
		_face_direction(tangent)
	global_position = global_position.lerp(next, minf(1.0, delta * 2.4))


func _update_colony(delta: float) -> void:
	match _colony_phase:
		ColonyPhase.ROOST:
			_update_colony_roost(delta)
		ColonyPhase.OUTBOUND, ColonyPhase.INBOUND:
			_update_colony_leg(delta)
		ColonyPhase.FORAGE:
			_update_colony_foraging(delta)


func _update_colony_roost(delta: float) -> void:
	global_position = _colony_roost
	_ground_y = _colony_roost.y
	_colony_phase_timer -= delta
	_timer -= delta
	if activity == Activity.PECK:
		if _timer <= 0.0:
			activity = Activity.IDLE
			_timer = _rng.randf_range(2.0, 5.0)
	elif _timer <= 0.0:
		if _rng.randf() < 0.28:
			activity = Activity.PECK
			_timer = _rng.randf_range(0.7, 1.3)
		else:
			_choose_idle_heading()
			_timer = _rng.randf_range(2.0, 5.5)
	if not _colony_resident and _colony_phase_timer <= 0.0:
		_colony_sites_visited = 0
		_begin_colony_leg(_colony_foraging_sites[_colony_site_index], ColonyPhase.OUTBOUND)


func _update_colony_foraging(delta: float) -> void:
	_colony_phase_timer -= delta
	var radius := flight_radius + float(rng_seed % 5) * 2.2
	var rate := 2.4 / maxf(radius, 1.0)
	var angle := _phase * rate + float(rng_seed % 17)
	var next := _colony_foraging_centre + Vector3(
		cos(angle) * radius,
		sin(angle * 1.7) * flight_relief,
		sin(angle) * radius * 0.72)
	var tangent := next - global_position
	if tangent.length_squared() > 0.0001:
		_face_direction(tangent)
	global_position = global_position.lerp(next, minf(1.0, delta * 2.4))
	if _colony_phase_timer > 0.0:
		return
	_colony_sites_visited += 1
	if _colony_sites_visited < colony_sites_per_trip:
		_colony_site_index = (_colony_site_index + 1) % _colony_foraging_sites.size()
		_begin_colony_leg(_colony_foraging_sites[_colony_site_index], ColonyPhase.OUTBOUND)
	else:
		_begin_colony_leg(_colony_roost, ColonyPhase.INBOUND)


func _begin_colony_leg(destination: Vector3, phase: ColonyPhase) -> void:
	_flight_from = global_position
	_flight_to = destination
	var plan_distance := Vector2(
		_flight_to.x - _flight_from.x,
		_flight_to.z - _flight_from.z).length()
	var apex := maxf(_flight_from.y, _flight_to.y) + colony_cruise_relief
	if plan_distance >= 700.0:
		apex = maxf(apex, colony_long_leg_height)
	_flight_control = (_flight_from + _flight_to) * 0.5
	# A quadratic curve reaches only halfway from its endpoints to its control;
	# solve the control height so `apex` is the actual mid-leg altitude.
	_flight_control.y = apex * 2.0 - (_flight_from.y + _flight_to.y) * 0.5
	_flight_elapsed = 0.0
	_flight_duration = clampf(plan_distance / colony_flight_speed, 5.0, 80.0)
	_colony_phase = phase
	activity = Activity.FLY


func _update_colony_leg(delta: float) -> void:
	_flight_elapsed += delta
	var t := clampf(_flight_elapsed / _flight_duration, 0.0, 1.0)
	var eased_t := t * t * (3.0 - 2.0 * t)
	var a := _flight_from.lerp(_flight_control, eased_t)
	var b := _flight_control.lerp(_flight_to, eased_t)
	var next := a.lerp(b, eased_t)
	var travel := next - global_position
	if travel.length_squared() > 0.0001:
		_face_direction(travel)
	global_position = next
	if t < 1.0:
		return
	if _colony_phase == ColonyPhase.INBOUND:
		_enter_colony_roost(false)
	else:
		_enter_colony_foraging(_colony_site_index, false)


func _enter_colony_roost(resident: bool) -> void:
	_colony_phase = ColonyPhase.ROOST
	global_position = _colony_roost
	_ground_y = _colony_roost.y
	activity = Activity.IDLE
	_timer = _rng.randf_range(1.0, 3.0)
	_colony_phase_timer = INF if resident else _rng.randf_range(
		colony_roost_min_seconds, colony_roost_max_seconds)
	_choose_idle_heading()


func _enter_colony_foraging(site_index: int, initial: bool) -> void:
	_colony_phase = ColonyPhase.FORAGE
	_colony_site_index = posmod(site_index, _colony_foraging_sites.size())
	_colony_foraging_centre = _colony_foraging_sites[_colony_site_index]
	activity = Activity.FLY
	_colony_phase_timer = _rng.randf_range(
		colony_forage_min_seconds, colony_forage_max_seconds)
	if initial:
		var angle := float(rng_seed % 17) / 17.0 * TAU
		var radius := flight_radius + float(rng_seed % 5) * 2.2
		global_position = _colony_foraging_centre + Vector3(
			cos(angle) * radius,
			sin(angle * 1.7) * flight_relief,
			sin(angle) * radius * 0.72)


func _animate_pose(delta: float) -> void:
	var flying := activity == Activity.FLY
	if wing_left_folded != null:
		wing_left_folded.visible = not flying
	if wing_right_folded != null:
		wing_right_folded.visible = not flying
	if wing_left_outer_folded != null:
		wing_left_outer_folded.visible = not flying
	if wing_right_outer_folded != null:
		wing_right_outer_folded.visible = not flying
	var moving := activity == Activity.WALK
	var pecking := activity == Activity.PECK
	var body_bob := sin(_phase * (10.0 if moving else 2.2)) * (0.025 if moving else 0.008)
	var desired_beak_open := _forced_beak_open
	if desired_beak_open < 0.0:
		desired_beak_open = _natural_beak_open()
	_beak_open = lerpf(_beak_open, desired_beak_open, minf(1.0, delta * 14.0))
	_pose_beak(_beak_open)
	visual.position.y = _visual_rest.y + body_bob
	var head_position := _head_position_rest
	if moving and species == "pigeon":
		head_position.z += sin(_phase * 10.0 + 0.8) * 0.038
	head_pivot.position = head_pivot.position.lerp(head_position, minf(1.0, delta * 12.0))

	var head_x := _head_rest.x
	if pecking:
		head_x -= absf(sin(_phase * 8.5)) * 0.86
	elif not flying:
		head_x += sin(_phase * 1.8 + float(rng_seed)) * 0.11
	head_pivot.rotation.x = lerp_angle(head_pivot.rotation.x, head_x, minf(1.0, delta * 10.0))

	if flying:
		var gliding := species == "gull" and (starts_airborne or _colony_enabled)
		var flap_rate := 4.2 if gliding else (11.0 if species == "gull" else 18.0)
		var flap_amount := 0.2 if gliding else (0.52 if species == "gull" else 0.68)
		var flap := sin(_phase * flap_rate) * flap_amount
		# The pigeon source's folded wings share the gull hierarchy but lie in a
		# flatter local plane. Opening them near horizontal keeps the broad pale
		# inner panels visible from below; the gull retains its steeper spread.
		var spread_angle := 0.08 if species == "pigeon" else 1.18
		wing_left.rotation.y = lerp_angle(wing_left.rotation.y, -spread_angle, minf(1.0, delta * 8.0))
		wing_right.rotation.y = lerp_angle(wing_right.rotation.y, spread_angle, minf(1.0, delta * 8.0))
		if species == "pigeon":
			wing_left.rotation.z = -1.15 + flap * 0.55
			wing_right.rotation.z = 1.15 - flap * 0.55
		else:
			wing_left.rotation.z = flap
			wing_right.rotation.z = -flap
		if wing_left_outer != null:
			wing_left_outer.rotation.y = lerp_angle(wing_left_outer.rotation.y,
				_wing_left_outer_rest.y + 0.48, minf(1.0, delta * 7.0))
		if wing_right_outer != null:
			wing_right_outer.rotation.y = lerp_angle(wing_right_outer.rotation.y,
				_wing_right_outer_rest.y - 0.48, minf(1.0, delta * 7.0))
		leg_left.rotation.x = lerp_angle(leg_left.rotation.x, -1.05, minf(1.0, delta * 7.0))
		leg_right.rotation.x = lerp_angle(leg_right.rotation.x, -1.05, minf(1.0, delta * 7.0))
		var bank := sin(_phase * 0.75 + float(rng_seed % 13)) * (0.1 if gliding else 0.04)
		visual.rotation.z = lerp_angle(visual.rotation.z, bank, minf(1.0, delta * 3.0))
	else:
		wing_left.rotation = wing_left.rotation.lerp(_wing_left_rest, minf(1.0, delta * 7.0))
		wing_right.rotation = wing_right.rotation.lerp(_wing_right_rest, minf(1.0, delta * 7.0))
		if wing_left_outer != null:
			wing_left_outer.rotation = wing_left_outer.rotation.lerp(
				_wing_left_outer_rest, minf(1.0, delta * 7.0))
		if wing_right_outer != null:
			wing_right_outer.rotation = wing_right_outer.rotation.lerp(
				_wing_right_outer_rest, minf(1.0, delta * 7.0))
		var stride := sin(_phase * (11.0 if species == "pigeon" else 8.0)) * (0.36 if species == "pigeon" else 0.22)
		var left_leg := _leg_left_rest
		var right_leg := _leg_right_rest
		if moving:
			left_leg.x += stride
			right_leg.x -= stride
		leg_left.rotation = leg_left.rotation.lerp(left_leg, minf(1.0, delta * 12.0))
		leg_right.rotation = leg_right.rotation.lerp(right_leg, minf(1.0, delta * 12.0))
		visual.rotation = visual.rotation.lerp(_visual_rotation_rest, minf(1.0, delta * 5.0))


func _natural_beak_open() -> float:
	if activity == Activity.PECK or activity == Activity.FLY:
		return 0.0
	var elapsed := _phase - _beak_first_call_phase
	if elapsed < 0.0:
		return 0.0
	var period := 6.5 if species == "gull" else 8.5
	var call_phase := fposmod(elapsed, period)
	var call_length := 0.52 if species == "gull" else 0.34
	if call_phase >= call_length:
		return 0.0
	return sin(call_phase / call_length * PI)


func _pose_beak(amount: float) -> void:
	var upper_angle := deg_to_rad(3.0 if species == "gull" else 2.0)
	var lower_angle := deg_to_rad(18.0 if species == "gull" else 20.0)
	beak_upper_pivot.rotation.x = _beak_upper_rest_x + upper_angle * amount
	beak_lower_pivot.rotation.x = _beak_lower_rest_x - lower_angle * amount


func _choose_walk_target() -> void:
	var angle := _rng.randf_range(0.0, TAU)
	var distance := _rng.randf_range(wander_radius * 0.25, wander_radius)
	_target = _home + Vector3(cos(angle) * distance, 0.0, sin(angle) * distance)
	_target.y = _ground_y
	activity = Activity.WALK


func _choose_idle_heading() -> void:
	var angle := _rng.randf_range(0.0, TAU)
	_face_direction(Vector3(cos(angle), 0.0, sin(angle)))


func _face_direction(direction: Vector3) -> void:
	if absf(direction.x) + absf(direction.z) < 0.0001:
		return
	rotation.y = atan2(-direction.x, -direction.z)


func _find_outer_pivot(wing: Node3D) -> Node3D:
	for child in wing.get_children():
		if child is Node3D and String(child.name).begins_with("outer_pivot"):
			return child as Node3D
	return null


func _apply_plumage_variant() -> void:
	if species != "gull" or not juvenile:
		return
	if model_has_authored_plumage:
		return
	var colors := {
		"body": Color(0.48, 0.42, 0.35),
		"breast": Color(0.53, 0.47, 0.4),
		"back": Color(0.31, 0.28, 0.25),
		"neck": Color(0.58, 0.52, 0.45),
		"head_pivot/head": Color(0.55, 0.5, 0.44),
		"head_pivot/eye_left_ring": Color(0.16, 0.13, 0.11),
		"head_pivot/eye_right_ring": Color(0.16, 0.13, 0.11),
		"wing_left/feathers": Color(0.35, 0.31, 0.27),
		"wing_right/feathers": Color(0.35, 0.31, 0.27),
		"wing_left/primary_inner": Color(0.24, 0.215, 0.19),
		"wing_right/primary_inner": Color(0.24, 0.215, 0.19),
		"wing_left/tip": Color(0.18, 0.17, 0.16),
		"wing_right/tip": Color(0.18, 0.17, 0.16),
		"tail": Color(0.2, 0.18, 0.16),
		"tail_band": Color(0.15, 0.14, 0.13),
		"head_pivot/beak/upper_pivot/mesh": Color(0.17, 0.16, 0.15),
		"head_pivot/beak/lower_pivot/mesh": Color(0.17, 0.16, 0.15),
		"leg_left/shin": Color(0.72, 0.48, 0.45),
		"leg_right/shin": Color(0.72, 0.48, 0.45),
	}
	for side in ["leg_left", "leg_right"]:
		for toe in ["toe_centre", "toe_inner", "toe_outer", "toe_back"]:
			colors["%s/%s/mesh" % [side, toe]] = Color(0.72, 0.48, 0.45)
		colors["%s/web" % side] = Color(0.72, 0.48, 0.45)
	for path in colors:
		var mesh_instance := visual.get_node_or_null(path) as MeshInstance3D
		if mesh_instance == null or mesh_instance.material_override == null:
			continue
		var material := mesh_instance.material_override.duplicate() as StandardMaterial3D
		material.albedo_color = colors[path]
		mesh_instance.material_override = material
	var markings := visual.get_node_or_null("juvenile_markings") as Node3D
	if markings != null:
		markings.visible = true
	var adult_markings := visual.get_node_or_null(
		"head_pivot/beak/lower_pivot/adult_markings") as Node3D
	if adult_markings != null:
		adult_markings.visible = false
	for path in ["wing_left/tip_spot", "wing_right/tip_spot"]:
		var adult_spot := visual.get_node_or_null(path) as MeshInstance3D
		if adult_spot != null:
			adult_spot.visible = false


func _apply_adult_tail_variant() -> void:
	if species != "gull" or juvenile:
		return
	var white_tail := pose_root.get_node_or_null("tail_white") as GeometryInstance3D
	var dark_tail := pose_root.get_node_or_null("tail_dark") as GeometryInstance3D
	if white_tail != null:
		white_tail.visible = not black_tail
	if dark_tail != null:
		dark_tail.visible = black_tail
	# The red lower-mandible mark belongs to the dark-tail adult treatment. Both
	# side discs stay authored in Blender so the readable one follows the view.
	for spot_name in ["bill_spot_left", "bill_spot_right"]:
		var spot := pose_root.find_child(spot_name, true, false) as GeometryInstance3D
		if spot != null:
			spot.visible = black_tail
