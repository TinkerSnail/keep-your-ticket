extends Node

## The Instamatic.
##
## Fixed focus, fixed exposure, no zoom — raising the camera changes what the
## player sees framed, not what the lens does. This node only tracks whether the
## camera is up and announces shutter presses; the HUD owns the actual capture
## because it owns overlay visibility.

signal raised_changed(raised: bool)
signal shutter_requested

var raised := false


func _ready() -> void:
	add_to_group("camera_tool")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("camera_raise"):
		_set_raised(true)
	elif event.is_action_released("camera_raise"):
		_set_raised(false)
	elif raised and event.is_action_pressed("shutter"):
		shutter_requested.emit()


func lower() -> void:
	_set_raised(false)


func _set_raised(value: bool) -> void:
	if raised == value:
		return
	raised = value
	raised_changed.emit(raised)
