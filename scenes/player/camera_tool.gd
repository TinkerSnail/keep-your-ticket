extends Node

## The Instamatic.
##
## Fixed focus, fixed exposure, no zoom — raising the camera changes what the
## player sees framed, not what the lens does. This node only tracks whether the
## camera is up and announces shutter presses; the HUD owns the actual capture
## because it owns overlay visibility.

signal raised_changed(raised: bool)
signal shutter_requested

## Raising the camera is tap-or-hold. A quick tap leaves it up until tapped
## again; holding keeps it up only while held. A trackpad cannot hold one
## button and click another, so nothing here requires two hands or two fingers.
const TAP_SECONDS := 0.25

var raised := false

var _pressed_at := 0.0
var _latched := false
var _swallow_release := false


func _ready() -> void:
	add_to_group("camera_tool")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("camera_raise"):
		_on_raise_pressed()
	elif event.is_action_released("camera_raise"):
		_on_raise_released()
	elif raised and event.is_action_pressed("shutter"):
		shutter_requested.emit()


func lower() -> void:
	_latched = false
	_set_raised(false)


func _on_raise_pressed() -> void:
	_pressed_at = Time.get_ticks_msec() / 1000.0
	if _latched:
		# Already held up by a previous tap — this press puts it away, and the
		# matching release must not be read as another tap.
		_latched = false
		_swallow_release = true
		_set_raised(false)
	else:
		_set_raised(true)


func _on_raise_released() -> void:
	if _swallow_release:
		_swallow_release = false
		return
	if Time.get_ticks_msec() / 1000.0 - _pressed_at <= TAP_SECONDS:
		_latched = true
	else:
		_set_raised(false)


func _set_raised(value: bool) -> void:
	if raised == value:
		return
	raised = value
	raised_changed.emit(raised)
