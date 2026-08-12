class_name Player
extends CharacterBody3D

## First-person walk-and-look controller.
##
## All input arrives through named actions, never raw device polling. Mouse look
## is read from motion events; stick look is read from the look_* actions.

const GRAVITY := 24.0

## CharacterBody3D has no step-up of its own — any riser is a ninety-degree wall
## and stops you dead, however small. A kerb, a planter lip, the fountain edge
## and the seam where a ramp meets a landing are all the same obstacle to it, so
## this is a general capability rather than a fix for one stair. Set to an
## ordinary step: enough for a kerb, nowhere near enough to climb anything.
const STEP_HEIGHT := 0.35

@export var walk_speed := 3.2
## Enough to get onto a bench or a planter, not enough to be platforming.
## Climbing is meant to be a route you read, not a jump you time.
@export var jump_velocity := 6.5
@export var acceleration := 14.0
@export var friction := 16.0
@export var mouse_sensitivity := 0.0022
@export var stick_sensitivity := 2.8
@export var pitch_limit_degrees := 88.0

## How far up the walking view may be pitched, which is much less than the eye.
##
## A third-person camera orbits: pitching up swings the arm down. At 88 degrees
## the arm is pointing almost straight at the ground, so it collides and pulls
## in to eighteen centimetres — the camera ends at ankle height, looking almost
## vertically at the underside of the photographer with nothing but sky behind
## them. It reads exactly like falling through the floor, and it was reported as
## that, but the arm is doing its job: measured across the range, it shortens
## from 2.60 to 1.42 and the camera never goes below y = +0.18.
##
## So this is not a collision fix, it is a clamp. Fifty-two degrees is as far up
## as the arm can swing while still clearing the ground at its full length.
##
## The eye keeps the full 88. Looking straight up through the finder is how you
## photograph the top of a coaster, and there is no arm to collapse.
@export var third_pitch_limit_degrees := 52.0

## What the raise costs. Up to now putting the camera up was free — it added an
## overlay and took nothing away, so there was never a reason to put it down.
## The finder is a tunnel: you walk at a shuffle, you turn deliberately, and the
## park either side of the frame stops existing. Everything the crowd does off
## to the side — the guest who just noticed, the chain of noticing travelling
## along a queue — is now something the player gave up in order to compose.
@export var raised_speed_scale := 0.45
@export var raised_look_scale := 0.55

## Not a zoom. The finder takes screen area, not angle: the mask is what makes
## the world small, and the lens is roughly what the eye was already seeing. The
## few degrees here are the motion of pressing your face to the back of a camera
## and nothing more — enough to feel, not enough to reach with.
@export var walk_fov := 70.0
@export var finder_fov := 64.0
@export var raise_seconds := 0.18

## The arm is pushed in by whatever is behind the player, and in a park at one
## prop per 30m² there is usually something. Below this it has collapsed far
## enough that the camera is inside the body, so the body stops being drawn and
## the frame goes back to being about the park. It keeps its shadow either way,
## so the give-away is not that the photographer vanished.
@export var body_fade_length := 1.3

## Over the shoulder, so the player is not standing in the middle of their own
## frame. Applied at the camera end rather than to the arm's origin: an origin
## half a metre to the player's right is not guaranteed to be anywhere the
## player could stand, and against a wall it starts inside one — which reads as
## the arm collapsing to nothing for no visible reason. The arm now measures
## from the player's own axis, which is by definition somewhere they fit, and
## the offset slides back to centre as the arm pulls in so the camera does not
## swing sideways into whatever pinched it.
@export var shoulder_offset := 0.42

## The arm pulls in as the view pitches up, and this is why the clamp above can
## afford to be as generous as it is.
##
## A 2.6m arm swinging from a 1.72m pivot reaches the ground at about 40
## degrees, and is already at waist height by 20 — measured, not guessed. So no
## clamp alone gives both a usable range and a camera that stays off the floor;
## at any angle worth having, a pure orbit is under the player looking up at
## them. Tapering the arm instead means looking up tucks the camera in behind
## the head rather than swinging it down past the knees, which is also what it
## looks like when somebody leans back to see the top of something.
##
## The full length is read off the scene at load, so the arm's resting length
## stays a property of the scene and this is only how far it collapses.
@export var third_arm_close := 1.1

const LOOK_SETTLE_FRAMES := 2
const LOOK_JUMP_LIMIT := 400.0

@onready var head: Node3D = $head
@onready var camera: Camera3D = $head/camera
@onready var spring: SpringArm3D = $head/spring
@onready var camera_third: Camera3D = $head/spring/camera_third
@onready var body: Node3D = $body

## Third person to move, first person to shoot — the Fatal Frame and Jet Grind
## Radio arrangement, where the switch is what makes the act an act rather than
## a button. Under test: the park's sightlines were all composed for an eye at
## 1.6m, and whether the compositions survive a camera three metres back is the
## open question, not whether the camera works.
## Third person to move, first person to shoot — so walking around is the
## default state and the eye is the exception you enter by raising the camera.
## This started false, which meant the game opened in first person and the
## whole arrangement was invisible unless you knew to press V.
var third_person := true

var _pitch := 0.0
var _look_enabled := true
var _shooting := false
var _fov_tween: Tween

## Motion arriving in the first frames after the cursor is grabbed is the grab
## itself, not the player. Two frames is enough to swallow it and short enough
## that a genuine movement started in the same breath is not lost.
var _look_settle := 0
var _pitch_tween: Tween
var _arm_length := 2.6
var _was_captured := false


func _ready() -> void:
	add_to_group("player")
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	# Otherwise the arm collides with the body it is attached to and collapses
	# to zero the moment it is switched on.
	spring.add_excluded_object(get_rid())
	_arm_length = spring.spring_length
	_apply_view()
	call_deferred("_connect_ui")


func _connect_ui() -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if hud != null and hud.has_signal("album_visibility_changed"):
		hud.album_visibility_changed.connect(_on_album_visibility_changed)
	# Raising the Instamatic drops to the eye whatever the walking view is. The
	# viewfinder has to be the lens, so it cannot be a camera hanging in space
	# three metres behind the person holding it.
	var tool_node := get_node_or_null("camera_tool")
	if tool_node != null and tool_node.has_signal("raised_changed"):
		tool_node.raised_changed.connect(_on_camera_raised)


func set_third_person(on: bool) -> void:
	if third_person == on:
		return
	third_person = on
	_apply_view()


func _on_camera_raised(raised: bool) -> void:
	_shooting = raised
	_apply_view()
	_tween_fov()


## First person whenever the Instamatic is up, whatever the walking view is set
## to. `third_person` is the preference; this is what the frame actually does.
func _apply_view() -> void:
	var tool_node := get_node_or_null("camera_tool")
	_shooting = tool_node != null and bool(tool_node.get("raised"))
	var behind := third_person and not _shooting
	camera_third.current = behind
	camera.current = not behind
	# Drawn only when there is a camera back there to see it. Otherwise it stays
	# in the scene casting a shadow, so the photographer turns up in their own
	# photographs the way they actually would — as a shadow across the bottom of
	# the frame in the late light.
	body.set_seen(behind and spring.get_hit_length() > body_fade_length)
	body.set_raised(_shooting)
	_settle_pitch()


## Coming back to the walking view from a steep look up — lowering the camera
## after shooting something overhead — leaves the pitch outside what the arm can
## take. Eased rather than snapped, over the same beat as the raise, so it reads
## as part of putting the camera down rather than as the view being grabbed.
func _settle_pitch() -> void:
	var ceiling := _pitch_ceiling()
	if _pitch <= ceiling + 0.0001:
		return
	if _pitch_tween != null and _pitch_tween.is_valid():
		_pitch_tween.kill()
	_pitch_tween = create_tween()
	_pitch_tween.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	_pitch_tween.tween_method(_set_pitch, _pitch, ceiling, raise_seconds)


func _set_pitch(value: float) -> void:
	_pitch = value
	head.rotation.x = _pitch


func _tween_fov() -> void:
	if _fov_tween != null and _fov_tween.is_valid():
		_fov_tween.kill()
	_fov_tween = create_tween()
	_fov_tween.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	_fov_tween.tween_property(camera, "fov", finder_fov if _shooting else walk_fov, raise_seconds)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("view_toggle"):
		set_third_person(not third_person)
		return
	if event is InputEventMouseMotion and _look_enabled:
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and _look_settle == 0:
			# A single event this large is the cursor being put somewhere by the
			# compositor, not a flick of the wrist. Motion events arrive per OS
			# event rather than per frame, so even a fast whip-round comes in
			# well under this; anything above it is a warp and is dropped.
			if event.relative.length() > LOOK_JUMP_LIMIT:
				return
			_apply_look(
				-event.relative.x * mouse_sensitivity,
				-event.relative.y * mouse_sensitivity
			)


func _physics_process(delta: float) -> void:
	# Watch for the cursor being grabbed rather than being told about it, so the
	# guard covers every route back in — the click that recaptures, the album
	# closing, or anything later that takes the mouse.
	var captured := Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
	if captured and not _was_captured:
		_look_settle = LOOK_SETTLE_FRAMES
	elif _look_settle > 0:
		_look_settle -= 1
	_was_captured = captured

	if _look_enabled:
		var look := Input.get_vector("look_left", "look_right", "look_up", "look_down")
		if look != Vector2.ZERO:
			_apply_look(
				-look.x * stick_sensitivity * delta,
				-look.y * stick_sensitivity * delta
			)

	var input_dir := Vector2.ZERO
	if _look_enabled:
		input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var wish := (transform.basis * Vector3(input_dir.x, 0.0, input_dir.y))
	wish.y = 0.0
	if wish.length_squared() > 1.0:
		wish = wish.normalized()

	var target := wish * walk_speed * (raised_speed_scale if _shooting else 1.0)
	var rate := acceleration if target != Vector3.ZERO else friction
	velocity.x = move_toward(velocity.x, target.x, rate * delta)
	velocity.z = move_toward(velocity.z, target.z, rate * delta)

	if is_on_floor():
		velocity.y = 0.0
		# Space is bound to both `jump` and `shutter`, and which one it is depends
		# on whether the camera is at the eye. Nobody jumps with a viewfinder
		# against their face, and the thumb is already on that key — so with the
		# Instamatic up it fires the shutter and does not leave the ground.
		#
		# The suppression has to be here rather than left to input handling.
		# `camera_tool` consumes the event, but this is a poll, and a poll does
		# not care what was marked handled: without this line raising the camera
		# and pressing space takes the photograph *and* jumps.
		if _look_enabled and not _shooting and Input.is_action_just_pressed("jump"):
			velocity.y = jump_velocity
	else:
		velocity.y -= GRAVITY * delta

	var grounded := is_on_floor()
	# Kept from before the slide: `move_and_slide` cancels the component heading
	# into whatever stopped it, so afterwards there is nothing left to say which
	# way the player was trying to go.
	var wanted := Vector3(velocity.x, 0.0, velocity.z)
	var was_at := global_position
	move_and_slide()
	if grounded and velocity.y <= 0.0:
		var intended := Vector2(wanted.x, wanted.z).length() * delta
		var got := Vector2(global_position.x - was_at.x, global_position.z - was_at.z).length()
		# Not `is_on_wall`. Where a ramp meets a landing the two surfaces are
		# coplanar, and the sliver that catches the capsule reports a normal
		# pointing up — so the snag is a floor by every test except the one that
		# matters, which is that the player stopped moving.
		if intended > 0.001 and got < intended * 0.7:
			_try_step(wanted, delta)

	# The arm length is decided by whatever is behind the player, which changes
	# every step, so this cannot live in `_apply_view` with the rest of it.
	if camera_third.current:
		var up := clampf(_pitch / maxf(_pitch_ceiling(), 0.001), 0.0, 1.0)
		spring.spring_length = lerpf(_arm_length, third_arm_close, up)
		var reach := spring.get_hit_length()
		camera_third.position.x = shoulder_offset * clampf(reach / spring.spring_length, 0.0, 1.0)
		body.set_seen(reach > body_fade_length)


## Walk into something short: lift by a step, try the move again from up there,
## and drop back onto whatever is underneath. Every stage has to succeed or the
## position is left exactly as `move_and_slide` left it.
func _try_step(wanted: Vector3, delta: float) -> void:
	var motion := wanted * delta
	if motion.length_squared() < 0.0001:
		return
	var lift := Vector3.UP * STEP_HEIGHT
	var probe := global_transform
	if test_move(probe, lift):
		return
	probe.origin += lift
	if test_move(probe, motion):
		return
	probe.origin += motion
	var landing := KinematicCollision3D.new()
	if not test_move(probe, Vector3.DOWN * (STEP_HEIGHT + 0.1), landing):
		return
	global_position = probe.origin + landing.get_travel()


func _apply_look(yaw_delta: float, pitch_delta: float) -> void:
	# Whoever is looking wins. Otherwise the settle keeps yanking the view back
	# for a fifth of a second after the player has started aiming somewhere.
	if _pitch_tween != null and _pitch_tween.is_valid():
		_pitch_tween.kill()
	var scale := raised_look_scale if _shooting else 1.0
	rotate_y(yaw_delta * scale)
	_pitch = clampf(_pitch + pitch_delta * scale, -_pitch_floor(), _pitch_ceiling())
	head.rotation.x = _pitch


## Looking down is the same in both views — the arm swings up and over, and
## there is nothing above the player to collide with. Only the up end differs.
func _pitch_ceiling() -> float:
	if third_person and not _shooting:
		return deg_to_rad(third_pitch_limit_degrees)
	return deg_to_rad(pitch_limit_degrees)


func _pitch_floor() -> float:
	return deg_to_rad(pitch_limit_degrees)


func _on_album_visibility_changed(album_open: bool) -> void:
	_look_enabled = not album_open
