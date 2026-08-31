extends Node

## Asking guests for a picture.
##
## There is no cursor and no highlight, because look is already the pointer:
## whoever is nearest the centre of the view within arm's-length-and-a-bit is
## who you are talking to. The only feedback that someone is reachable is that
## they look back at you when you get close, which is feedback the world gives
## rather than the interface.
##
## Like `camera_tool.gd` this node only reads the action and announces it. What
## a pose actually looks like belongs to the guest.

signal asked(guest: Node, group_size: int)

@onready var _player: Node3D = get_parent() as Node3D

var _camera: Node3D = null


func _ready() -> void:
	add_to_group("interact_tool")
	_camera = _player.get_node_or_null("head/camera") as Node3D


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed("interact"):
		return
	var crowd := ParkSections.current_crowd()
	if crowd == null or _camera == null:
		return

	# Aim from the eye along the eye's own heading, so who you are asking is
	# whoever you are looking at rather than whoever the body happens to face.
	var forward := -_camera.global_transform.basis.z
	forward.y = 0.0
	if forward.length_squared() < 0.0001:
		return

	var guest: Node = crowd.interaction_candidate(_player.global_position, forward)
	if guest == null:
		return

	var group_size: int = crowd.ask_to_pose(guest, _player.global_position)
	asked.emit(guest, group_size)
