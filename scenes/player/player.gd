class_name Player
extends CharacterBody3D

## First-person walk-and-look controller.
##
## All input arrives through named actions, never raw device polling. Mouse look
## is read from motion events; stick look is read from the look_* actions.

const GRAVITY := 24.0

@export var walk_speed := 3.2
@export var acceleration := 14.0
@export var friction := 16.0
@export var mouse_sensitivity := 0.0022
@export var stick_sensitivity := 2.8
@export var pitch_limit_degrees := 88.0

@onready var head: Node3D = $head
@onready var camera: Camera3D = $head/camera

var _pitch := 0.0
var _look_enabled := true


func _ready() -> void:
	add_to_group("player")
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	call_deferred("_connect_ui")


func _connect_ui() -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if hud != null and hud.has_signal("album_visibility_changed"):
		hud.album_visibility_changed.connect(_on_album_visibility_changed)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and _look_enabled:
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			_apply_look(
				-event.relative.x * mouse_sensitivity,
				-event.relative.y * mouse_sensitivity
			)


func _physics_process(delta: float) -> void:
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

	var target := wish * walk_speed
	var rate := acceleration if target != Vector3.ZERO else friction
	velocity.x = move_toward(velocity.x, target.x, rate * delta)
	velocity.z = move_toward(velocity.z, target.z, rate * delta)

	if is_on_floor():
		velocity.y = 0.0
	else:
		velocity.y -= GRAVITY * delta

	move_and_slide()


func _apply_look(yaw_delta: float, pitch_delta: float) -> void:
	rotate_y(yaw_delta)
	var limit := deg_to_rad(pitch_limit_degrees)
	_pitch = clampf(_pitch + pitch_delta, -limit, limit)
	head.rotation.x = _pitch


func _on_album_visibility_changed(album_open: bool) -> void:
	_look_enabled = not album_open
