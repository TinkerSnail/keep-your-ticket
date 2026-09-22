class_name ParkBird
extends Node3D

## Shared motion for the park's directly authored bird scenes.
##
## The visible gull and pigeon forms live in ordinary `.tscn` scenes so every
## body part remains selectable and replaceable in Godot. This script owns only
## their small repertoire: looking, pecking, strolling, flushing and circling.
## Birds are ambient life and photographic subjects. They expose no collectible
## or scoring state.

# EAT and SQUABBLE are the gulls' feeding states; they sit after FLY so the
# older values keep their numbers.
## Emitted by an airborne gull at the instant it takes what it dived for.
signal prize_taken(prize: Node3D)

enum Activity { IDLE, PECK, WALK, FLY, EAT, SQUABBLE, CARRY, CHASE }
enum ColonyPhase { NONE, ROOST, OUTBOUND, FORAGE, INBOUND, LANDING, FEED }

@export_enum("gull", "pigeon") var species := "gull"
@export var juvenile := false
@export var black_tail := false
@export var starts_airborne := false
@export var pose_root_path: NodePath = NodePath("visual")
@export var model_has_authored_plumage := false
## A repainted copy of this bird's atlas, for variety inside a flock: same UV
## layout, different plumage. Empty leaves the model's own painting. The cere
## keeps its separate material, and the eye tiles are part of the atlas, so a
## variant can change eye colour too.
@export var plumage_atlas: Texture2D
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
## How far the body tips forward about the hips while pecking, in radians. The
## head swings about the neck's base, so the neck and body share the reach:
## 0.68 puts the bill tip about 1cm off the paving at the bottom of each jab.
@export_range(0.0, 1.4, 0.02) var peck_body_pitch := 0.68
@export_group("Gull feeding")
## How far a grounded gull will go for food. Food is any Node3D in the
## "gull_food" group, which is how a hand-placed prop attracts gulls, plus the
## park's own generated litter pieces, found by name at runtime.
@export_range(0.0, 60.0, 0.5) var food_attraction_radius := 26.0
## How far from a colony foraging marker, in plan, a circling commuter will
## come down to land beside food.
@export_range(0.0, 200.0, 1.0) var colony_food_radius := 60.0
## From the food to the bird's feet, so the bill comes down on the food.
@export_range(0.1, 1.5, 0.01) var food_stand_distance := 0.5
## The threat posture in a fight over food: how far the wings open and lift.
@export_range(0.0, 1.2, 0.01) var mantle_spread := 0.9
@export_range(-1.2, 1.2, 0.01) var mantle_lift := 0.55
@export_group("")

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
# Glances draw from their own generator so adding or tuning them never shifts
# the wander, peck and flight decisions _rng already hands out.
var _glance_rng := RandomNumberGenerator.new()
var _glance_yaw := 0.0
var _glance_roll := 0.0
var _peck_pitch := 0.0
var _food: Node3D
var _food_cooldown := 0.0
var _eat_phase := 0.0
var _squabble_rival: Node3D
var _squabble_loses := false
var _squabble_cooldown := 0.0
var _retreat_timer := 0.0
# What a gull has in its bill: a fry it made, or the carton off a food prop.
var _carried: Node3D
var _carried_is_box := false
var _swallow_timer := 0.0
var _chase_target: Node3D
# The airborne theft: 0 circling, 1 diving on the prize, 2 climbing away with it.
var _swoop_stage := 0
var _swoop_prize: Node3D
var _swoop_elapsed := 0.0
var _swoop_from := Vector3.ZERO
var _swoop_heading := Vector3.FORWARD
var _carry_swallow_delay := 0.0
var _land_check_timer := INF
# The generated litter never changes while the game runs, so one scan of the
# tree serves every gull; a freed entry means the world was reloaded.
static var _litter_cache: Array[Node3D] = []
static var _litter_scan_time := -1000.0
var _head_position_smoothed := Vector3.ZERO
# The head pivot sits at the head's centre with the neck hanging from it. The
# neck's base, in pivot-local space, is where the head should actually turn,
# so the pivot is moved each frame to keep that point where it rested.
var _neck: Node3D
var _neck_rest_basis := Basis.IDENTITY
var _neck_base := Vector3.ZERO
var _neck_base_rest_offset := Vector3.ZERO
var _leg_left_pose := Vector3.ZERO
var _leg_right_pose := Vector3.ZERO
var _hip_rest := Vector3.ZERO
# The wrapper's visual node carries the bird's size, so lengths written in
# metres for the pose follow it, and the bill's reach is measured, not assumed.
var _body_scale := 1.0
var _bill_forward := 0.6
var _bill_up := 0.6
var _glance_timer := 0.0
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
	_head_position_smoothed = _head_position_rest
	_neck = head_pivot.get_node_or_null("neck") as Node3D
	if _neck != null:
		_neck_rest_basis = _neck.transform.basis
		_neck_base = _find_neck_base(_neck as MeshInstance3D)
		_neck_base_rest_offset = Basis.from_euler(_head_rest) * _neck_base
	_wing_left_rest = wing_left.rotation
	_wing_right_rest = wing_right.rotation
	if wing_left_outer != null:
		_wing_left_outer_rest = wing_left_outer.rotation
	if wing_right_outer != null:
		_wing_right_outer_rest = wing_right_outer.rotation
	_leg_left_rest = leg_left.rotation
	_hip_rest = to_local((leg_left.global_position + leg_right.global_position) * 0.5) - visual.position
	_body_scale = visual.scale.y
	var bill_tip := to_local(beak_upper_pivot.global_transform * _bill_tip_local())
	_bill_forward = -bill_tip.z
	_bill_up = bill_tip.y
	_leg_right_rest = leg_right.rotation
	_leg_left_pose = _leg_left_rest
	_leg_right_pose = _leg_right_rest
	_beak_upper_rest_x = beak_upper_pivot.rotation.x
	_beak_lower_rest_x = beak_lower_pivot.rotation.x
	_apply_plumage_atlas()
	_apply_plumage_variant()
	_apply_adult_tail_variant()
	_phase = _rng.randf_range(0.0, TAU)
	# Every bird begins with a neutral portrait and then calls on its own stable
	# offset. This keeps catalog loads closed without synchronizing the flock.
	_beak_first_call_phase = _phase + 2.0 + float(rng_seed % 7) * 0.4
	_timer = _rng.randf_range(0.5, 2.8)
	_glance_rng.seed = rng_seed * 31 + 7
	_glance_timer = _glance_rng.randf_range(0.4, 2.2)
	if starts_airborne:
		activity = Activity.FLY
	else:
		_choose_idle_heading()


func _physics_process(delta: float) -> void:
	_phase += delta
	_flee_cooldown = maxf(0.0, _flee_cooldown - delta)
	_food_cooldown = maxf(0.0, _food_cooldown - delta)
	_squabble_cooldown = maxf(0.0, _squabble_cooldown - delta)
	_retreat_timer = maxf(0.0, _retreat_timer - delta)
	if _swallow_timer > 0.0:
		_swallow_timer = maxf(0.0, _swallow_timer - delta)
		if _swallow_timer <= 0.0 and _carried != null and not _carried_is_box:
			_carried.queue_free()
			_carried = null
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node3D

	if _colony_enabled:
		_update_colony(delta)
	elif starts_airborne:
		if _swoop_stage != 0:
			_update_swoop(delta)
		else:
			_update_circling(delta)
		if _carry_swallow_delay > 0.0:
			_carry_swallow_delay -= delta
			if _carry_swallow_delay <= 0.0 and _carried != null:
				_swallow_timer = 0.75
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
			Activity.EAT:
				_update_eat(delta)
			Activity.SQUABBLE:
				_update_squabble(delta)
			Activity.CARRY:
				_update_carry(delta)
			Activity.CHASE:
				_update_chase(delta)
	_animate_pose(delta)


## Public for interactions and the focused wildlife check. Passing a position
## rather than a Player keeps the reaction reusable for guests or vehicles.
func scare_from(point: Vector3) -> void:
	if _colony_enabled or starts_airborne or activity == Activity.FLY:
		return
	_food = null
	_squabble_rival = null
	_chase_target = null
	_drop_carried()
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
	if species == "gull" and _food_cooldown <= 0.0:
		var food := _nearest_food(global_position, food_attraction_radius, 0.6)
		if food != null:
			_go_to_food(food)
			return
	# A gull with nothing to eat mostly stands and looks; it is the pigeons
	# that work the ground all day.
	if _rng.randf() < (0.64 if species == "pigeon" else 0.1):
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
		if _food != null and is_instance_valid(_food):
			_begin_eating()
			return
		activity = Activity.IDLE
		_timer = _rng.randf_range(0.7, 2.8)
		return
	_face_direction(offset)
	var speed := walk_speed
	if _retreat_timer > 0.0:
		speed *= 2.6
	elif _food != null:
		speed *= 1.9
	global_position += offset.normalized() * minf(speed * delta, offset.length())
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


## Sends a circling gull down on something held out in the open. It takes the
## prize in its bill, climbs back to its circle and bolts it down on the wing.
func steal_from_air(prize: Node3D) -> bool:
	if not starts_airborne or _swoop_stage != 0 or _carried != null or prize == null:
		return false
	_swoop_prize = prize
	_swoop_stage = 1
	_swoop_elapsed = 0.0
	_swoop_from = global_position
	return true


func is_swooping() -> bool:
	return _swoop_stage != 0


func _circle_point() -> Vector3:
	var rate := (2.4 if species == "gull" else 3.0) / maxf(flight_radius, 1.0)
	var angle := _phase * rate + float(rng_seed % 17)
	return _home + Vector3(
		cos(angle) * flight_radius,
		sin(angle * 1.7) * flight_relief,
		sin(angle) * flight_radius * 0.72)


func _update_swoop(delta: float) -> void:
	_swoop_elapsed += delta
	var next := global_position
	if _swoop_stage == 1:
		if not is_instance_valid(_swoop_prize) or not _swoop_prize.is_inside_tree():
			_swoop_stage = 2
			_swoop_elapsed = 0.0
			_swoop_from = global_position
			return
		var prize := _swoop_prize.global_position
		var flat := prize - _swoop_from
		flat.y = 0.0
		_swoop_heading = flat.normalized() if flat.length_squared() > 0.0001 else Vector3.FORWARD
		# The bird's origin is at its feet; aim so the bill, not the feet, meets it.
		var aim := prize - _swoop_heading * _bill_forward - Vector3.UP * _bill_up
		var control := aim - _swoop_heading * 7.0 + Vector3.UP * 2.2
		var length := maxf(2.2, _swoop_from.distance_to(aim) / 16.0)
		var u := clampf(_swoop_elapsed / length, 0.0, 1.0)
		var eased := u * u
		next = _swoop_from.lerp(control, eased).lerp(control.lerp(aim, eased), eased)
		if u >= 1.0:
			var world_scale := beak_upper_pivot.global_transform.basis.get_scale()
			_swoop_prize.reparent(beak_upper_pivot, true)
			_swoop_prize.position = _bill_tip_local()
			_swoop_prize.scale = Vector3.ONE / world_scale
			_carried = _swoop_prize
			_carried_is_box = false
			prize_taken.emit(_swoop_prize)
			_swoop_prize = null
			_swoop_stage = 2
			_swoop_elapsed = 0.0
			_swoop_from = aim
	else:
		var home := _circle_point()
		var control := _swoop_from + _swoop_heading * 8.0 + Vector3.UP * 1.5
		var u := clampf(_swoop_elapsed / 3.4, 0.0, 1.0)
		var eased := 1.0 - (1.0 - u) * (1.0 - u)
		next = _swoop_from.lerp(control, eased).lerp(control.lerp(home, eased), eased)
		if u >= 1.0:
			_swoop_stage = 0
			if _carried != null:
				_carry_swallow_delay = 2.2
	var travel := next - global_position
	if travel.length_squared() > 0.0001:
		_face_direction(travel)
	global_position = next


func _update_colony(delta: float) -> void:
	match _colony_phase:
		ColonyPhase.ROOST:
			_update_colony_roost(delta)
		ColonyPhase.OUTBOUND, ColonyPhase.INBOUND, ColonyPhase.LANDING:
			_update_colony_leg(delta)
		ColonyPhase.FORAGE:
			_update_colony_foraging(delta)
		ColonyPhase.FEED:
			_update_colony_feed(delta)


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
	# Circle for a while, then look down: food near this site brings most
	# commuters to the ground.
	_land_check_timer -= delta
	if _land_check_timer <= 0.0:
		_land_check_timer = INF
		if _rng.randf() < 0.7 and _try_land_for_food():
			return
	if _colony_phase_timer > 0.0:
		return
	_depart_foraging_site()


func _depart_foraging_site() -> void:
	_food = null
	_squabble_rival = null
	_chase_target = null
	_drop_carried()
	_colony_sites_visited += 1
	if _colony_sites_visited < colony_sites_per_trip:
		_colony_site_index = (_colony_site_index + 1) % _colony_foraging_sites.size()
		_begin_colony_leg(_colony_foraging_sites[_colony_site_index], ColonyPhase.OUTBOUND)
	else:
		_begin_colony_leg(_colony_roost, ColonyPhase.INBOUND)


func _try_land_for_food() -> bool:
	var centre := _colony_foraging_centre
	var best: Node3D = null
	var best_score := INF
	for food in _food_candidates():
		if not is_instance_valid(food) or not food.is_inside_tree():
			continue
		var p := food.global_position
		if Vector2(p.x - centre.x, p.z - centre.z).length() > colony_food_radius:
			continue
		var score := Vector2(p.x - global_position.x, p.z - global_position.z).length()
		score += _crowd_score(food)
		if score < best_score:
			best_score = score
			best = food
	if best == null:
		return false
	_food = best
	_ground_y = _ground_below(best)
	_flight_from = global_position
	_flight_to = _stand_point(best)
	# Come down early and skim in low, the flare a landing gull makes, rather
	# than the climbing arc the long colony legs use.
	_flight_control = _flight_to + (_flight_from - _flight_to) * 0.35
	_flight_control.y = _flight_to.y + 0.6
	_flight_elapsed = 0.0
	_flight_duration = clampf(_flight_from.distance_to(_flight_to) / (colony_flight_speed * 0.4), 3.0, 12.0)
	_colony_phase = ColonyPhase.LANDING
	activity = Activity.FLY
	return true


func _update_colony_feed(delta: float) -> void:
	_colony_phase_timer -= delta
	# A landed commuter flushes like any grounded bird, by leaving for its next
	# site rather than circling back.
	if _player != null and activity != Activity.SQUABBLE:
		var distance := Vector2(global_position.x - _player.global_position.x,
			global_position.z - _player.global_position.z).length()
		if distance < scare_radius:
			_depart_foraging_site()
			return
	match activity:
		Activity.EAT:
			_update_eat(delta)
		Activity.SQUABBLE:
			_update_squabble(delta)
		Activity.WALK:
			_update_walk(delta)
		Activity.CARRY:
			_update_carry(delta)
		Activity.CHASE:
			_update_chase(delta)
		Activity.PECK:
			_update_peck(delta)
		_:
			_timer -= delta
			if _timer <= 0.0:
				if _colony_phase_timer <= 0.0:
					_depart_foraging_site()
					return
				var food := _nearest_food(global_position, 14.0, 0.6) if _food_cooldown <= 0.0 else null
				if food != null:
					_go_to_food(food)
				else:
					_choose_idle_heading()
					_timer = _rng.randf_range(1.0, 2.5)


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
	elif _colony_phase == ColonyPhase.LANDING:
		_colony_phase = ColonyPhase.FEED
		_colony_phase_timer = _rng.randf_range(colony_forage_min_seconds, colony_forage_max_seconds) * 0.7
		global_position = _flight_to
		_home = _flight_to
		if _food != null and is_instance_valid(_food):
			_begin_eating()
		else:
			activity = Activity.IDLE
			_timer = 0.5
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
	_land_check_timer = _rng.randf_range(5.0, 16.0)
	_colony_phase_timer = _rng.randf_range(
		colony_forage_min_seconds, colony_forage_max_seconds)
	if initial:
		var angle := float(rng_seed % 17) / 17.0 * TAU
		var radius := flight_radius + float(rng_seed % 5) * 2.2
		global_position = _colony_foraging_centre + Vector3(
			cos(angle) * radius,
			sin(angle * 1.7) * flight_relief,
			sin(angle) * radius * 0.72)


## Food a gull is walking to, eating or fighting over; null otherwise.
func get_food() -> Node3D:
	return _food


func _food_candidates() -> Array[Node3D]:
	var now := Time.get_ticks_msec() / 1000.0
	var stale := false
	for node in _litter_cache:
		if not is_instance_valid(node):
			stale = true
			break
	if stale or (_litter_cache.is_empty() and now - _litter_scan_time > 20.0):
		_litter_scan_time = now
		_litter_cache.clear()
		for node in get_tree().root.find_children("litter_*", "Node3D", true, false):
			_litter_cache.append(node as Node3D)
	var found: Array[Node3D] = []
	for node in get_tree().get_nodes_in_group("gull_food"):
		if node is Node3D:
			found.append(node as Node3D)
	found.append_array(_litter_cache)
	return found


func _nearest_food(origin: Vector3, radius: float, level_tolerance: float) -> Node3D:
	var best: Node3D = null
	var best_score := radius
	for food in _food_candidates():
		if not is_instance_valid(food) or not food.is_inside_tree():
			continue
		var p := food.global_position
		# A walking gull cannot change level, so food on another deck is not food.
		if absf(p.y - _ground_y) > level_tolerance:
			continue
		var distance := Vector2(p.x - origin.x, p.z - origin.z).length()
		if distance > radius:
			continue
		var score := distance + _crowd_score(food)
		if score < best_score:
			best_score = score
			best = food
	return best


## One gull already eating makes a piece more attractive, which is where the
## fights come from; a third makes it a crowd not worth joining.
func _crowd_score(food: Node3D) -> float:
	var eaters := 0
	for bird in get_tree().get_nodes_in_group("gull"):
		if bird != self and bird.has_method("get_food") and bird.call("get_food") == food:
			eaters += 1
	if eaters == 1:
		return -5.0
	return 8.0 * float(maxi(0, eaters - 1))


func _ground_below(food: Node3D) -> float:
	var from := food.global_position + Vector3.UP * 0.4
	var query := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 2.0)
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return food.global_position.y
	# Paving sits 12mm proud of its collision, and the pigeons stand at +0.02.
	return (hit["position"] as Vector3).y + 0.02


func _stand_point(food: Node3D) -> Vector3:
	var p := food.global_position
	var side := global_position - p
	side.y = 0.0
	# Face a gull already there from across the food rather than standing in it.
	for bird in get_tree().get_nodes_in_group("gull"):
		if bird != self and bird.has_method("get_food") and bird.call("get_food") == food:
			side = p - (bird as Node3D).global_position
			side.y = 0.0
			break
	if side.length_squared() < 0.0001:
		side = Vector3.BACK
	side = side.normalized().rotated(Vector3.UP, _rng.randf_range(-0.35, 0.35))
	var point := p + side * food_stand_distance
	point.y = _ground_y
	return point


func _go_to_food(food: Node3D) -> void:
	_food = food
	_target = _stand_point(food)
	activity = Activity.WALK


func _begin_eating() -> void:
	activity = Activity.EAT
	_eat_phase = 0.0
	_timer = _rng.randf_range(5.0, 11.0)
	_face_food()


func _face_food() -> void:
	if _food != null and is_instance_valid(_food):
		var toward := _food.global_position - global_position
		toward.y = 0.0
		_face_direction(toward)


func _update_eat(delta: float) -> void:
	if _food == null or not is_instance_valid(_food):
		_finish_eating()
		return
	_face_food()
	_timer -= delta
	if _timer <= 0.0:
		_finish_eating()
		return
	if _squabble_cooldown > 0.0:
		return
	for bird in get_tree().get_nodes_in_group("gull"):
		if bird == self or not bird.has_method("get_food") or bird.call("get_food") != _food:
			continue
		var rival := bird as Node3D
		if int(rival.get("activity")) != Activity.EAT:
			continue
		if rival.global_position.distance_to(global_position) > 1.8:
			continue
		# About once every two seconds of shared eating, somebody makes a move,
		# and it is nearly always about the food rather than the other bird.
		if _rng.randf() < delta * 0.5:
			var roll := _rng.randf()
			var carton := _stealable_carton()
			if roll < 0.5 or (carton == null and roll < 0.82):
				# Keepaway: run off with a fry, the rival in pursuit.
				_begin_carry(false, null, rival)
				rival.call("begin_chase", self, _rng.randf_range(2.2, 3.6))
			elif roll < 0.82 and carton != null:
				# Steal the whole carton. Half the time the rival is smart
				# enough to stay with the fries that spilled.
				_begin_carry(true, carton, rival)
				if _rng.randf() < 0.5:
					rival.call("begin_chase", self, _rng.randf_range(2.5, 4.0))
			else:
				var duration := _rng.randf_range(1.0, 1.7)
				var i_lose := _rng.randf() < 0.5
				begin_squabble(rival, i_lose, duration)
				rival.call("begin_squabble", self, not i_lose, duration)
		return


func is_carrying() -> bool:
	return _carried != null


## A food prop may offer a child named "carton" as something to run off with.
func _stealable_carton() -> Node3D:
	if _food == null or not is_instance_valid(_food):
		return null
	var carton := _food.get_node_or_null("carton") as Node3D
	if carton == null or carton.global_position.distance_to(global_position) > 1.3:
		return null
	return carton


func _bill_tip_local() -> Vector3:
	# Front centre of the upper bill, in the upper pivot's frame.
	for child in beak_upper_pivot.get_children():
		var mesh_instance := child as MeshInstance3D
		if mesh_instance != null and mesh_instance.mesh != null:
			var aabb := mesh_instance.mesh.get_aabb()
			return mesh_instance.transform * Vector3(
				aabb.position.x + aabb.size.x * 0.5, aabb.position.y, aabb.position.z + aabb.size.z * 0.12)
	return Vector3(0.0, 0.0, -0.1)


func _begin_carry(box: bool, carton: Node3D, rival: Node3D) -> void:
	_drop_carried()
	_carried_is_box = box
	var world_scale := beak_upper_pivot.global_transform.basis.get_scale()
	if box:
		_carried = carton
		if not carton.has_meta("food_owner"):
			carton.set_meta("food_owner", _food.name)
		carton.reparent(beak_upper_pivot, true)
		carton.position = _bill_tip_local() + Vector3(0.0, -0.028, -0.03) / world_scale.y
	else:
		var fry := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		mesh.size = Vector3(0.075, 0.011, 0.011)
		var material := StandardMaterial3D.new()
		material.albedo_color = Color(0.94, 0.76, 0.3)
		material.roughness = 0.85
		mesh.material = material
		fry.mesh = mesh
		fry.name = "carried_fry"
		beak_upper_pivot.add_child(fry)
		# Held crosswise at the bill tip, at world size whatever the model's scale.
		fry.scale = Vector3.ONE / world_scale
		fry.position = _bill_tip_local()
		_carried = fry
	var away := global_position - rival.global_position
	away.y = 0.0
	if away.length_squared() < 0.0001:
		away = Vector3.BACK
	away = away.normalized()
	_target = global_position
	var reach := _rng.randf_range(3.0, 5.0) if box else _rng.randf_range(2.4, 4.2)
	for attempt in 8:
		var candidate := global_position + away.rotated(Vector3.UP, _rng.randf_range(-0.9, 0.9) + float(attempt) * 0.7) * reach
		candidate.y = _ground_y
		if _walkable(candidate):
			_target = candidate
			break
	activity = Activity.CARRY
	_timer = 6.0


## Is there deck or ground at this bird's level under the point? A walking bird
## holds its height, so without this it would run off the pier and stand on air.
func _walkable(point: Vector3) -> bool:
	var from := Vector3(point.x, _ground_y + 0.5, point.z)
	var hit := get_world_3d().direct_space_state.intersect_ray(
		PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 1.2))
	if hit.is_empty():
		return false
	return absf((hit["position"] as Vector3).y - _ground_y) < 0.2


func _update_carry(delta: float) -> void:
	_timer -= delta
	var offset := _target - global_position
	offset.y = 0.0
	if offset.length() > 0.1 and _timer > 0.0:
		_face_direction(offset)
		global_position += offset.normalized() * minf(walk_speed * 2.6 * delta, offset.length())
		global_position.y = _ground_y
		return
	if _carried_is_box:
		# Put the carton down and work at it; it stays wherever it was dropped.
		_drop_carried()
		activity = Activity.PECK
		_timer = _rng.randf_range(2.0, 4.0)
		_food_cooldown = _rng.randf_range(3.0, 6.0)
		_food = null
	else:
		# Far enough: head back and bolt it down.
		_swallow_timer = 0.75
		activity = Activity.IDLE
		_timer = 1.0
		_food_cooldown = _rng.randf_range(1.0, 3.0)
		_food = null


func _drop_carried() -> void:
	if _carried == null or not is_instance_valid(_carried):
		_carried = null
		return
	if not _carried_is_box:
		_carried.queue_free()
		_carried = null
		return
	var carton := _carried
	_carried = null
	var drop := carton.global_position
	var home := get_parent()
	for food in get_tree().get_nodes_in_group("gull_food"):
		if food.name == carton.get_meta("food_owner", &""):
			home = food
	carton.reparent(home, true)
	carton.global_position = Vector3(drop.x, _ground_y + 0.04, drop.z)
	carton.global_rotation = Vector3(0.0, _rng.randf_range(0.0, TAU), 0.0)


## The bird that did not get the prize, running after the one that did.
func begin_chase(carrier: Node3D, duration: float) -> void:
	if activity == Activity.FLY:
		return
	_chase_target = carrier
	activity = Activity.CHASE
	_timer = duration


func _update_chase(delta: float) -> void:
	_timer -= delta
	var over := _timer <= 0.0 or _chase_target == null or not is_instance_valid(_chase_target) \
		or not bool(_chase_target.call("is_carrying"))
	if over:
		# Nothing left to win: straight back to the food.
		_chase_target = null
		activity = Activity.IDLE
		_timer = 0.3
		_food_cooldown = 0.0
		_food = null
		return
	var offset := _chase_target.global_position - global_position
	offset.y = 0.0
	_face_direction(offset)
	if offset.length() > maxf(0.3, 1.3 * _body_scale):
		var step := offset.normalized() * walk_speed * 2.4 * delta
		var next := global_position + step
		next.y = _ground_y
		if _walkable(next):
			global_position = next


func _finish_eating() -> void:
	_food = null
	_food_cooldown = _rng.randf_range(6.0, 14.0)
	activity = Activity.IDLE
	_timer = _rng.randf_range(1.0, 3.0)


## Both birds in a fight are told the same outcome and length by whoever
## started it, so they finish together and only one of them leaves.
func begin_squabble(rival: Node3D, loses: bool, duration: float) -> void:
	if activity == Activity.FLY:
		return
	activity = Activity.SQUABBLE
	_squabble_rival = rival
	_squabble_loses = loses
	_timer = duration


func _update_squabble(delta: float) -> void:
	var rival_gone := _squabble_rival == null or not is_instance_valid(_squabble_rival) \
		or int(_squabble_rival.get("activity")) == Activity.FLY
	if not rival_gone:
		var toward := _squabble_rival.global_position - global_position
		toward.y = 0.0
		_face_direction(toward)
	_timer -= delta
	if _timer > 0.0 and not rival_gone:
		return
	_squabble_cooldown = 5.0
	if _squabble_loses and not rival_gone:
		# Driven off: scurry a couple of metres away with the wings still up,
		# and leave this piece alone for a while.
		var away := global_position - _squabble_rival.global_position
		away.y = 0.0
		if away.length_squared() < 0.0001:
			away = Vector3.BACK
		_target = global_position + away.normalized() * _rng.randf_range(1.8, 2.8)
		_target.y = _ground_y
		if not _walkable(_target):
			_target = global_position
		_food = null
		_food_cooldown = _rng.randf_range(8.0, 14.0)
		_retreat_timer = 1.6
		activity = Activity.WALK
	else:
		activity = Activity.EAT
		_timer = maxf(_timer, _rng.randf_range(3.0, 6.0))
	_squabble_rival = null


func _find_neck_base(neck: MeshInstance3D) -> Vector3:
	# Average of the neck mesh's lowest vertices, in the pivot's frame.
	if neck == null or neck.mesh == null:
		return Vector3.ZERO
	var lowest := INF
	var points: PackedVector3Array = []
	for surface in neck.mesh.get_surface_count():
		var arrays := neck.mesh.surface_get_arrays(surface)
		for v in arrays[Mesh.ARRAY_VERTEX]:
			var local: Vector3 = neck.transform * v
			points.append(local)
			lowest = minf(lowest, local.y)
	var sum := Vector3.ZERO
	var count := 0
	var aabb_height: float = neck.mesh.get_aabb().size.y * neck.scale.y
	for point in points:
		if point.y <= lowest + aabb_height * 0.08:
			sum += point
			count += 1
	return sum / maxf(1.0, float(count))


func _update_glance(delta: float) -> void:
	_glance_timer -= delta
	if _glance_timer > 0.0:
		return
	# Hold a look for a moment, then more often than not come back to straight
	# ahead so the flock never reads as permanently craning.
	if _glance_yaw != 0.0 and _glance_rng.randf() < 0.55:
		_glance_yaw = 0.0
		_glance_roll = 0.0
	else:
		var side := 1.0 if _glance_rng.randf() < 0.5 else -1.0
		_glance_yaw = side * _glance_rng.randf_range(0.15, 0.45)
		# About a third of looks come with the signature cocked head: the bird
		# rolls its head to bring one eye onto whatever caught its attention.
		_glance_roll = 0.0
		if _glance_rng.randf() < 0.35:
			_glance_roll = -side * _glance_rng.randf_range(0.25, 0.45)
	_glance_timer = _glance_rng.randf_range(0.7, 2.6)


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
	var carrying := activity == Activity.CARRY
	var chasing := activity == Activity.CHASE
	var moving := activity == Activity.WALK or carrying or chasing
	var eating := activity == Activity.EAT
	var squabbling := activity == Activity.SQUABBLE
	# Eating is a cycle: jab at the food, then throw the head back with the bill
	# open and bolt it down.
	var eat_cycle := 0.0
	if eating:
		_eat_phase += delta
		eat_cycle = fposmod(_eat_phase, 1.6) / 1.6
	var swallowing := (eating and eat_cycle >= 0.55) or _swallow_timer > 0.0
	var pecking := activity == Activity.PECK or (eating and not swallowing)
	var mantled := squabbling or _retreat_timer > 0.0 or carrying
	var body_bob := sin(_phase * (10.0 if moving else 2.2)) * (0.025 if moving else 0.008) * _body_scale
	var desired_beak_open := _forced_beak_open
	if desired_beak_open < 0.0:
		if squabbling:
			desired_beak_open = 0.75 + 0.25 * sin(_phase * 14.0)
		elif _carried != null:
			desired_beak_open = 0.3
		elif _swoop_stage == 1:
			desired_beak_open = 0.7
		elif chasing:
			desired_beak_open = 0.55 + 0.25 * sin(_phase * 12.0)
		elif _swallow_timer > 0.0:
			desired_beak_open = 0.9 if _swallow_timer > 0.35 else 0.0
		elif swallowing:
			desired_beak_open = 0.9 if (eat_cycle - 0.55) / 0.45 < 0.5 else 0.0
		elif eating:
			desired_beak_open = absf(sin(_phase * 8.5)) * 0.35
		else:
			desired_beak_open = _natural_beak_open()
	_beak_open = lerpf(_beak_open, desired_beak_open, minf(1.0, delta * 14.0))
	_pose_beak(_beak_open)
	# The peck tips the whole body nose-down about the hips. The visual node
	# turns about the bird origin at the feet, so shift it by the hip's swing to
	# keep the hip, and with it the plumb legs, where they stood.
	_peck_pitch = lerpf(_peck_pitch, peck_body_pitch if pecking else 0.0, minf(1.0, delta * 6.0))
	var hip_swung := _hip_rest.rotated(Vector3.RIGHT, -_peck_pitch)
	visual.position = _visual_rest + Vector3(0.0, body_bob, 0.0) + (_hip_rest - hip_swung)
	if squabbling:
		# Lunge at the rival, the two of them out of step.
		var beat := sin(_phase * 7.0 + (PI if _squabble_loses else 0.0))
		visual.position.z -= maxf(0.0, beat) * 0.07 * _body_scale
	var head_position := _head_position_rest
	var head_bob := 0.0
	if moving and species == "pigeon":
		# The pigeon walk: one bob per step, locked to the stride. The head
		# thrusts forward quickly, then holds still in the world while the body
		# walks up under it, which in the body's frame is a slow slide back.
		# It is a distance here and becomes a neck swing below: the neck levers
		# about its base, which stays buried in the chest, and the head rides
		# its top staying level. Sliding the whole pivot made the neck's base
		# peek in and out of the breast.
		var step := fposmod(_phase * 22.0, TAU) / TAU
		var bob := 0.0
		if step < 0.3:
			bob = smoothstep(0.0, 1.0, step / 0.3) - 0.5
		else:
			bob = 0.5 - (step - 0.3) / 0.7
		head_bob = -bob * 0.13
	_head_position_smoothed = _head_position_smoothed.lerp(head_position, minf(1.0, delta * 12.0))

	var head_x := _head_rest.x
	if pecking:
		# Quick jabs from a dipped head; the body pitch below does the reaching.
		head_x -= 0.3 + absf(sin(_phase * 8.5)) * 0.35
	elif _swallow_timer > 0.0:
		head_x += sin((1.0 - _swallow_timer / 0.75) * PI) * 0.75
	elif swallowing:
		head_x += sin((eat_cycle - 0.55) / 0.45 * PI) * 0.75
	elif squabbling:
		head_x -= 0.12
	elif carrying:
		head_x += 0.18
	elif chasing:
		head_x -= 0.2
	elif not flying:
		head_x += sin(_phase * 1.8 + float(rng_seed)) * 0.11
	head_pivot.rotation.x = lerp_angle(head_pivot.rotation.x, head_x, minf(1.0, delta * 10.0))

	# A grounded bird glances about by turning its head, never its eyes, which
	# sit rigid in the head as a real pigeon's do. Pecking and flight look
	# straight ahead. The turn is quick, the way a pigeon snaps its head.
	var head_y := _head_rest.y
	var head_z := _head_rest.z
	if flying or pecking or eating or squabbling or carrying or chasing:
		_glance_yaw = 0.0
		_glance_roll = 0.0
		_glance_timer = minf(_glance_timer, 0.4)
	else:
		_update_glance(delta)
		head_y += _glance_yaw
		head_z += _glance_roll
	head_pivot.rotation.y = lerp_angle(head_pivot.rotation.y, head_y, minf(1.0, delta * 9.0))
	head_pivot.rotation.z = lerp_angle(head_pivot.rotation.z, head_z, minf(1.0, delta * 7.0))
	# Pitch and yaw turn the head about the neck's base, so the neck keeps
	# growing out of the body. The roll is the cocked head: it turns the head
	# about its own centre and the neck is counter-rolled to stay still.
	var swing := Vector3.ZERO
	if _neck != null:
		var roll := head_pivot.rotation.z - _head_rest.z
		# The walk bob as a lever angle: a swing of a about the base moves the
		# head fore-aft by a times the neck's height.
		var lever := head_bob / maxf(0.05, absf(_neck_base.y))
		# Undo the roll first, then swing, so both stay exact together.
		_neck.transform.basis = Basis(Vector3.BACK, -roll) * Basis(Vector3.RIGHT, lever) * _neck_rest_basis
		var without_roll := Basis.from_euler(Vector3(head_pivot.rotation.x, head_pivot.rotation.y, _head_rest.z))
		swing = _neck_base_rest_offset - without_roll * (Basis(Vector3.RIGHT, lever) * _neck_base)
	else:
		swing = Vector3(0.0, 0.0, head_bob)
	head_pivot.position = _head_position_smoothed + swing

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
		_leg_left_pose = leg_left.rotation
		_leg_right_pose = leg_right.rotation
		var bank := sin(_phase * 0.75 + float(rng_seed % 13)) * (0.1 if gliding else 0.04)
		visual.rotation.z = lerp_angle(visual.rotation.z, bank, minf(1.0, delta * 3.0))
		visual.rotation.x = lerp_angle(visual.rotation.x, _visual_rotation_rest.x, minf(1.0, delta * 5.0))
	else:
		var wing_left_pose := _wing_left_rest
		var wing_right_pose := _wing_right_rest
		if mantled:
			# Wings half raised and shivering: the threat posture.
			var shiver := sin(_phase * 16.0) * 0.12
			wing_left_pose += Vector3(0.0, -mantle_spread, mantle_lift + shiver)
			wing_right_pose += Vector3(0.0, mantle_spread, -mantle_lift - shiver)
		wing_left.rotation = wing_left.rotation.lerp(wing_left_pose, minf(1.0, delta * 7.0))
		wing_right.rotation = wing_right.rotation.lerp(wing_right_pose, minf(1.0, delta * 7.0))
		# The outer wing opens about two thirds of its flight angle when mantled.
		var outer_open := 0.32 if mantled else 0.0
		if wing_left_outer != null:
			wing_left_outer.rotation = wing_left_outer.rotation.lerp(
				_wing_left_outer_rest + Vector3(0.0, outer_open, 0.0), minf(1.0, delta * 7.0))
		if wing_right_outer != null:
			wing_right_outer.rotation = wing_right_outer.rotation.lerp(
				_wing_right_outer_rest - Vector3(0.0, outer_open, 0.0), minf(1.0, delta * 7.0))
		var stride := sin(_phase * (11.0 if species == "pigeon" else 8.0)) * (0.36 if species == "pigeon" else 0.22)
		var left_leg := _leg_left_rest
		var right_leg := _leg_right_rest
		if moving:
			left_leg.x += stride
			right_leg.x -= stride
		_leg_left_pose = _leg_left_pose.lerp(left_leg, minf(1.0, delta * 12.0))
		_leg_right_pose = _leg_right_pose.lerp(right_leg, minf(1.0, delta * 12.0))
		# Legs counter the body pitch exactly, so they stay plumb under the
		# pinned hip; the pitch itself is already smoothed, so no second lerp.
		leg_left.rotation = _leg_left_pose + Vector3(_peck_pitch, 0.0, 0.0)
		leg_right.rotation = _leg_right_pose + Vector3(_peck_pitch, 0.0, 0.0)
		visual.rotation = visual.rotation.lerp(_visual_rotation_rest, minf(1.0, delta * 5.0))
		visual.rotation.x = _visual_rotation_rest.x - _peck_pitch


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
	var anchor := _home
	if species == "gull":
		# A gull with food in reach loiters around it between meals instead of
		# marching home and back; its authored home takes over when the food goes.
		var food := _nearest_food(global_position, food_attraction_radius, 0.6)
		if food != null:
			anchor = food.global_position
			distance = _rng.randf_range(1.2, 3.2)
	_target = anchor + Vector3(cos(angle) * distance, 0.0, sin(angle) * distance)
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


# One material per source material and atlas, shared by every bird wearing it.
static var _atlas_materials := {}


func _apply_plumage_atlas() -> void:
	if plumage_atlas == null:
		return
	for descendant in pose_root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		if mesh_instance.mesh == null or String(mesh_instance.name).begins_with("cere_"):
			continue
		var source := mesh_instance.get_active_material(0) as BaseMaterial3D
		if source == null or source.albedo_texture == null:
			continue
		var key := "%s|%d" % [plumage_atlas.resource_path, source.get_instance_id()]
		var material: BaseMaterial3D = _atlas_materials.get(key)
		if material == null:
			material = source.duplicate() as BaseMaterial3D
			material.albedo_texture = plumage_atlas
			_atlas_materials[key] = material
		mesh_instance.material_override = material


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
