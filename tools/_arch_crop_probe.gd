extends Node

## Dev tool, throwaway: is the wheel's top rim cropped by the arch beam?
##
## The arithmetic and the picture disagree, so this is the tiebreaker. The ray
## from a 1.7m eye at `ARCH_NEAR_STAND_X` over the beam's near soffit reaches
## y=23.4 at the wheel's plane, and the real wheel's rim tops out at 25.80 —
## measured from the boardwalk scene, not quoted. That predicts about 2.4m behind
## masonry. A shot from the same standpoint reportedly shows it uncropped.
##
## Only one of those can be right, and the thing that would reconcile them is
## occlusion this arithmetic does not model: the piers are 12.5m tall and the
## opening is cut to the sky above them, so the lateral limit stops being the
## pier's far edge somewhere partway up. That is not something to reason about
## from constants — the arch belongs to another session and its shape is being
## edited. Look at it instead.
##
## Prints the camera's own world position as well as the head's, because the
## rig is third person on a spring arm: the eye the arithmetic assumes is not
## where the frame is actually taken from, and which one is further back
## decides the answer.

const HOUR := 16
const MINUTE := 0
const SETTLE := 6.0

## Two standpoints, and the second is the control. `ARCH_RIM_CLEAR_X` (−16) is
## where the whole rim is *required* to show, at 0.14m of soffit in hand. −11 is
## where it is known to crop, from the run that found the shortfall. Shooting
## both means the pass has something to be a pass against: a frame where the arc
## reaches an apex with sky above it, beside a frame where it meets a straight
## edge. One frame alone cannot tell those apart if you have not seen the other.
const STANDS := [-16.0, -11.0]

## Pitched up in steps, because the interesting strip is narrow and a single
## pose that misses it looks exactly like a pose that proves it clears.
const PITCHES := [9.0, 11.0, 14.0]

var _player: Node3D
var _head: Node3D


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(HOUR, MINUTE)
	await get_tree().create_timer(SETTLE).timeout
	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		push_error("no player")
		get_tree().quit(1)
		return
	_head = _player.get_node("head")

	for x in STANDS:
		for p in PITCHES:
			await _shoot(x, p)
	get_tree().quit()


func _shoot(stand_x: float, pitch: float) -> void:
	_player.global_position = Vector3(stand_x, 0.2, -2.0)
	_player.rotation.y = deg_to_rad(90.0)
	_head.rotation.x = deg_to_rad(pitch)
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var cam := get_viewport().get_camera_3d()
	print("stand %5.1f  pitch %5.1f  head %v  camera %v" % [stand_x, pitch,
		_head.global_position, cam.global_position if cam != null else Vector3.ZERO])
	var path := "user://archcrop_x%d_p%02d.png" % [int(-stand_x), int(pitch)]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
