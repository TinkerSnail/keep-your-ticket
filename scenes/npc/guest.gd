class_name Guest
extends AnimatableBody3D

## A park guest: walks the plaza's path graph, looks at things, and reacts to
## having a camera pointed at them.
##
## Bodies and placement are generated. `tools/gen_crowd.gd` writes the scene
## this lives in, `scenes/world/plaza_crowd.tscn` — a guest edited by hand in
## the editor is lost on the next regeneration. Behaviour lives here so that it
## stays hand-editable while the crowd around it is disposable.
##
## Attention is a priority stack rather than a state machine. Several things can
## be worth looking at at once, the highest-priority one wins, and the head only
## turns as far as a neck goes — past that the guest either turns their body or
## gives up and faces forward. At this fidelity what a guest is looking at is
## the whole of their performance, so it is where the detail went.

enum Attention { FORWARD, POI, COMPANION, CAMERA, POSE }

## How a guest takes being photographed. Rolled once per camera raise, against
## the guest's own curiosity and shyness, so the same person tends to respond
## the same way twice — but not always, because people don't.
enum Reaction { OBLIVIOUS, GLANCE, HOLD, AVOID }

const ARRIVE_DISTANCE := 0.35
const SEPARATION_RADIUS := 0.95
const SEPARATION_STRENGTH := 1.4

const HEAD_YAW_LIMIT := deg_to_rad(78.0)
const HEAD_PITCH_LIMIT := deg_to_rad(32.0)
const HEAD_TURN_RATE := 7.0

## Beyond this the guest turns their whole body rather than craning, but only
## when stopped. Walking guests just let the target go.
const BODY_TURN_THRESHOLD := deg_to_rad(60.0)

const CAMERA_NOTICE_RANGE := 13.0
const CAMERA_NOTICE_RANGE_SQ := CAMERA_NOTICE_RANGE * CAMERA_NOTICE_RANGE
const GLANCE_SECONDS := Vector2(0.9, 2.1)

const POSE_HOLD := 7.0
## The pose does not end, it comes apart. Each guest drops out somewhere in
## this window, so a group unravels raggedly instead of switching off.
const POSE_DECAY := Vector2(1.5, 4.5)
const POSE_GATHER_DISTANCE := 2.6

## Set by the generator. Everything about a guest that varies is data.
@export var walk_speed := 1.25
@export var rng_seed := 0
@export var curiosity := 0.5
@export var shyness := 0.25
@export var seated := false
## Top of whatever they are sitting on. Benches and cafe chairs differ, and a
## guest hovering two centimetres above a seat is the first thing anyone sees.
@export var seat_height := 0.51
## Followers shadow their group's leader instead of routing for themselves,
## which is what makes a family read as a family rather than four strangers
## on the same heading.
@export var leader_path := NodePath()
@export var follow_offset := Vector3.ZERO
## Who a guest arrived with. The crowd turns this into the list of people they
## look at while stopped — a group standing in silence all facing the same way
## is the thing that makes a crowd look wrong.
@export var group_id := 0

var _crowd: Node = null
var _rng := RandomNumberGenerator.new()

var _body: Node3D
var _head_pivot: Node3D
var _arm_l: Node3D
var _arm_r: Node3D
var _hip_l: Node3D
var _hip_r: Node3D
var _knee_l: Node3D
var _knee_r: Node3D
var _body_rest_y := 0.0

var _leader: Guest = null
var _companions: Array[Guest] = []

var _route: PackedInt32Array = PackedInt32Array()
var _leg := 0
var _wait := 0.0
var _wander := Vector3.ZERO

var _phase := 0.0
var _stride := 0.0
var _speed := 0.0
var _idle_phase := 0.0

var _attention := Attention.FORWARD
var _look_point := Vector3.ZERO
var _look_weight := 0.0
var _head_yaw := 0.0
var _head_pitch := 0.0

var _reaction := Reaction.OBLIVIOUS
var _reaction_timer := 0.0
var _was_camera_raised := false

var _posing := false
var _pose_timer := 0.0
var _pose_anchor := Vector3.ZERO
## Some guests — usually the small ones — do not comply, and that is a better
## photograph than the one that was asked for.
var _pose_complies := true


func _ready() -> void:
	add_to_group("npc")
	add_to_group("guest")

	_rng.seed = rng_seed if rng_seed != 0 else hash(name)

	_body = $body
	_head_pivot = $body/neck/head_pivot
	_arm_l = $body/arm_l
	_arm_r = $body/arm_r
	_hip_l = $body/hip_l
	_hip_r = $body/hip_r
	_knee_l = $body/hip_l/knee_l
	_knee_r = $body/hip_r/knee_r
	_body_rest_y = _body.position.y

	_idle_phase = _rng.randf() * TAU
	_wander = Vector3(_rng.randfn(0.0, 0.5), 0.0, _rng.randfn(0.0, 0.5))
	_pose_complies = _rng.randf() > 0.16

	_crowd = get_tree().get_first_node_in_group("crowd")
	if _crowd != null and _crowd.has_method("register"):
		_crowd.register(self)

	call_deferred("_resolve_group")

	if seated:
		_apply_seated_pose()


func _exit_tree() -> void:
	if _crowd != null and _crowd.has_method("unregister"):
		_crowd.unregister(self)


func _resolve_group() -> void:
	if not leader_path.is_empty():
		_leader = get_node_or_null(leader_path) as Guest
	if _crowd != null:
		_companions.assign(_crowd.companions(self))


func _physics_process(delta: float) -> void:
	_update_reaction(delta)
	_update_pose(delta)

	var moved := 0.0
	if not seated:
		moved = _update_movement(delta)
		_speed = moved / maxf(delta, 0.0001)

	_update_attention()
	_update_head(delta)
	_animate(delta, moved)


# --- movement ---------------------------------------------------------------


## Returns distance covered this frame, which is what drives the walk cycle —
## the legs are tied to ground actually crossed rather than to a clock, so a
## guest slowed by the crowd around them does not skate.
func _update_movement(delta: float) -> float:
	var before := global_position

	if _wait > 0.0 and not _posing:
		_wait -= delta
		_apply_separation(delta)
		return (global_position - before).length()

	var target := _movement_target()
	if target == Vector3.INF:
		_apply_separation(delta)
		return (global_position - before).length()

	var to_target := target - global_position
	to_target.y = 0.0
	var distance := to_target.length()

	var stop_distance := ARRIVE_DISTANCE
	if _leader != null:
		# Followers keep station loosely. Holding a precise offset looks like
		# formation marching; letting them drift and catch up looks like people.
		stop_distance = 0.55
	if _posing:
		stop_distance = 0.4

	if distance > stop_distance:
		var direction := to_target / distance
		var step := minf(walk_speed * delta, distance - stop_distance * 0.5)
		global_position += direction * step
		_face_direction(direction, delta, 6.0)
	elif _leader == null and not _posing:
		_advance_route()

	_apply_separation(delta)
	return (global_position - before).length()


func _movement_target() -> Vector3:
	if _posing:
		return _pose_anchor

	if _leader != null:
		if not is_instance_valid(_leader):
			_leader = null
		else:
			var basis := Basis(Vector3.UP, _leader.rotation.y)
			return _leader.global_position + basis * follow_offset

	if _route.is_empty():
		_request_route()
		if _route.is_empty():
			return Vector3.INF

	if _leg >= _route.size():
		return Vector3.INF

	if _crowd == null:
		return Vector3.INF
	return _crowd.node_position(_route[_leg]) + _wander


func _advance_route() -> void:
	_leg += 1
	if _leg < _route.size():
		# A short beat at intermediate nodes and a real stop at the end, so the
		# crowd has people standing in it and not only people crossing it.
		if _rng.randf() < 0.25:
			_wait = _rng.randf_range(1.5, 5.0)
		return
	_wait = _rng.randf_range(2.5, 9.0)
	_route = PackedInt32Array()


func _request_route() -> void:
	if _crowd == null:
		return
	_route = _crowd.route_from(global_position, _rng.randi())
	_leg = 0
	_wander = Vector3(_rng.randfn(0.0, 0.45), 0.0, _rng.randfn(0.0, 0.45))


## Guests do not path around each other, they just refuse to overlap. At this
## density that is indistinguishable from the real thing and costs nothing.
func _apply_separation(delta: float) -> void:
	if _crowd == null:
		return
	var push := Vector3.ZERO
	var others: Array = _crowd.guests
	for entry in others:
		var other := entry as Node3D
		if other == self or other == null or not is_instance_valid(other):
			continue
		var away := global_position - other.global_position
		away.y = 0.0
		var d := away.length()
		if d > SEPARATION_RADIUS or d < 0.001:
			continue
		push += (away / d) * (1.0 - d / SEPARATION_RADIUS)
	if push == Vector3.ZERO:
		return
	global_position += push * SEPARATION_STRENGTH * delta


func _face_direction(direction: Vector3, delta: float, rate: float) -> void:
	if direction.length_squared() < 0.0001:
		return
	var wanted := atan2(-direction.x, -direction.z)
	rotation.y = lerp_angle(rotation.y, wanted, rate * delta)


# --- being photographed -----------------------------------------------------


func _update_reaction(delta: float) -> void:
	if _reaction_timer > 0.0:
		_reaction_timer -= delta

	if _crowd == null:
		return

	var raised: bool = _crowd.camera_raised
	if raised and not _was_camera_raised:
		_roll_reaction()
	elif not raised and _was_camera_raised:
		_reaction = Reaction.OBLIVIOUS
		_reaction_timer = 0.0
	_was_camera_raised = raised


func _roll_reaction() -> void:
	var player: Vector3 = _crowd.player_position
	if global_position.distance_squared_to(player) > CAMERA_NOTICE_RANGE_SQ:
		_reaction = Reaction.OBLIVIOUS
		return

	# Nearer guests notice more reliably. Someone across the plaza mostly does
	# not clock a camera, which is what keeps the reaction from reading as the
	# whole crowd flinching at once.
	var distance := global_position.distance_to(player)
	var closeness := 1.0 - clampf(distance / CAMERA_NOTICE_RANGE, 0.0, 1.0)
	var notices := _rng.randf() < 0.25 + closeness * (0.35 + curiosity * 0.5)
	if not notices:
		_reaction = Reaction.OBLIVIOUS
		return

	if _rng.randf() < shyness:
		_reaction = Reaction.AVOID
	elif _rng.randf() < curiosity * 0.55:
		_reaction = Reaction.HOLD
	else:
		_reaction = Reaction.GLANCE
		_reaction_timer = _rng.randf_range(GLANCE_SECONDS.x, GLANCE_SECONDS.y)


## Asked to pose. The guest does not stop being a person about it — they walk
## in a little, turn, and hold, and then they stop holding.
func ask_to_pose(anchor: Vector3) -> void:
	if seated:
		_posing = true
		_pose_timer = POSE_HOLD + _rng.randf_range(POSE_DECAY.x, POSE_DECAY.y)
		return
	_posing = true
	_pose_timer = POSE_HOLD + _rng.randf_range(POSE_DECAY.x, POSE_DECAY.y)
	_wait = 0.0
	_pose_anchor = _gather_point(anchor)


## Stand near the anchor without standing on it or on each other, facing back
## the way the ask came from.
func _gather_point(anchor: Vector3) -> Vector3:
	var away := global_position - anchor
	away.y = 0.0
	if away.length() < 0.5:
		away = Vector3(_rng.randfn(0.0, 1.0), 0.0, _rng.randfn(0.0, 1.0))
	var spread := _rng.randf_range(-0.7, 0.7)
	var offset := away.normalized().rotated(Vector3.UP, spread) * POSE_GATHER_DISTANCE
	return anchor + offset


func _update_pose(delta: float) -> void:
	if not _posing:
		return
	_pose_timer -= delta
	if _pose_timer <= 0.0:
		_posing = false
		_route = PackedInt32Array()
		_wait = _rng.randf_range(0.4, 2.0)


func is_posing() -> bool:
	return _posing


# --- attention --------------------------------------------------------------


func _update_attention() -> void:
	if _crowd == null:
		_attention = Attention.FORWARD
		_look_weight = 0.0
		return

	var eye: Vector3 = _crowd.player_eye

	if _posing:
		if _pose_complies:
			_set_attention(Attention.POSE, eye, 1.0)
		else:
			# Looking at anything except the camera. Reliably the better photo.
			var elsewhere := global_position + Vector3(sin(_idle_phase) * 4.0, 1.2, cos(_idle_phase * 0.7) * 4.0)
			_set_attention(Attention.POSE, elsewhere, 0.8)
		return

	if _crowd.camera_raised and _reaction != Reaction.OBLIVIOUS:
		var holding := _reaction == Reaction.HOLD
		var glancing := _reaction == Reaction.GLANCE and _reaction_timer > 0.0
		if holding or glancing:
			_set_attention(Attention.CAMERA, eye, 1.0)
			return
		if _reaction == Reaction.AVOID:
			var to_player := (eye - global_position).normalized()
			var turned := to_player.rotated(Vector3.UP, PI * 0.55)
			_set_attention(Attention.CAMERA, global_position + turned * 6.0 + Vector3.UP * 1.4, 0.7)
			return

	# Measured rather than declared. A follower keeping station is standing
	# still without ever having decided to, and looks at their group for the
	# same reason a leader on a pause does.
	var stopped := _speed < 0.2

	if stopped and not _companions.is_empty():
		var companion: Guest = _companions[wrapi(int(_idle_phase * 0.25), 0, _companions.size())]
		if is_instance_valid(companion):
			_set_attention(Attention.COMPANION, companion.eye_position(), 0.85)
			return

	var poi: Vector3 = _crowd.poi_near(global_position, 9.0 if stopped else 5.0)
	if poi != Vector3.INF:
		_set_attention(Attention.POI, poi, 0.7 if stopped else 0.45)
		return

	_attention = Attention.FORWARD
	_look_weight = lerpf(_look_weight, 0.0, 0.05)


func _set_attention(kind: int, point: Vector3, weight: float) -> void:
	_attention = kind
	_look_point = point
	_look_weight = weight


func eye_position() -> Vector3:
	if _head_pivot == null:
		return global_position + Vector3.UP * 1.5
	return _head_pivot.global_position


func _update_head(delta: float) -> void:
	var wanted_yaw := 0.0
	var wanted_pitch := 0.0

	if _look_weight > 0.01:
		var local: Vector3 = global_transform.basis.inverse() * (_look_point - eye_position())
		var flat := Vector2(local.x, local.z).length()
		wanted_yaw = atan2(-local.x, -local.z)
		wanted_pitch = atan2(local.y, maxf(flat, 0.001))

		# A neck that cannot reach either turns the shoulders or looks away. It
		# does not stretch, which is the tell in every game that gets this wrong.
		if absf(wanted_yaw) > BODY_TURN_THRESHOLD:
			var can_turn := _posing or (_wait > 0.0 and _attention >= Attention.COMPANION)
			if can_turn:
				var to_point := _look_point - global_position
				to_point.y = 0.0
				_face_direction(to_point.normalized(), delta, 3.2)
			elif absf(wanted_yaw) > HEAD_YAW_LIMIT:
				wanted_yaw = 0.0
				wanted_pitch = 0.0

		wanted_yaw = clampf(wanted_yaw, -HEAD_YAW_LIMIT, HEAD_YAW_LIMIT) * _look_weight
		wanted_pitch = clampf(wanted_pitch, -HEAD_PITCH_LIMIT, HEAD_PITCH_LIMIT) * _look_weight

	# Idle drift so a head at rest is never perfectly still.
	wanted_yaw += sin(_idle_phase * 0.31) * 0.05
	wanted_pitch += sin(_idle_phase * 0.23) * 0.02

	_head_yaw = lerp_angle(_head_yaw, wanted_yaw, HEAD_TURN_RATE * delta)
	_head_pitch = lerp_angle(_head_pitch, wanted_pitch, HEAD_TURN_RATE * delta)
	_head_pivot.rotation = Vector3(_head_pitch, _head_yaw, 0.0)


# --- animation --------------------------------------------------------------


func _animate(delta: float, moved: float) -> void:
	_idle_phase += delta

	if seated:
		_animate_seated()
		return

	# Stride length scales with height so short guests take more steps to cross
	# the same ground, which is most of what makes a mixed crowd read as mixed.
	var cadence := 3.4
	_stride = lerpf(_stride, clampf(moved / maxf(delta, 0.0001) / walk_speed, 0.0, 1.0), 8.0 * delta)
	_phase += moved * cadence

	var swing := 0.62 * _stride
	var hip := sin(_phase)
	_hip_l.rotation.x = hip * swing
	_hip_r.rotation.x = -hip * swing
	# Knees only bend one way, and only on the leg that is swinging through.
	_knee_l.rotation.x = -maxf(sin(_phase - 0.9), 0.0) * 0.85 * _stride
	_knee_r.rotation.x = -maxf(sin(_phase - 0.9 + PI), 0.0) * 0.85 * _stride

	_arm_l.rotation.x = -hip * swing * 0.7
	_arm_r.rotation.x = hip * swing * 0.7

	var bob := absf(sin(_phase)) * 0.022 * _stride
	var sway := sin(_idle_phase * 0.9) * 0.012 * (1.0 - _stride)
	_body.position.y = _body_rest_y + bob + sway
	_body.rotation.z = sin(_phase) * 0.03 * _stride


func _animate_seated() -> void:
	var shift := sin(_idle_phase * 0.6) * 0.012
	_body.position.y = _body_rest_y + shift
	_body.rotation.z = sin(_idle_phase * 0.4) * 0.02
	_arm_l.rotation.x = 0.35 + sin(_idle_phase * 0.5) * 0.04
	_arm_r.rotation.x = 0.35 + sin(_idle_phase * 0.43) * 0.04


## Sitting is the same skeleton folded: hips raised to the seat, thighs swung
## forward, shins hanging back down. The generator puts the root at the seat's
## centre, so the only thing to solve here is the fold.
##
## Positive rotation about X carries a limb forward (-Z). The thigh goes almost
## all the way over; the knee takes almost all of it back off, which leaves the
## shins vertical and the feet under the seat's front edge rather than out in
## front of it.
func _apply_seated_pose() -> void:
	_body_rest_y = seat_height
	_body.position.y = _body_rest_y
	_hip_l.rotation.x = deg_to_rad(84.0)
	_hip_r.rotation.x = deg_to_rad(80.0)
	_knee_l.rotation.x = deg_to_rad(-80.0)
	_knee_r.rotation.x = deg_to_rad(-76.0)
	_arm_l.rotation.x = 0.35
	_arm_r.rotation.x = 0.35
