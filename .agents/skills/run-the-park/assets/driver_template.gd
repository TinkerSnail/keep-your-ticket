extends Node

## Driver skeleton: instantiate the game, play it, save what you saw.
##
## Copy this, edit `_drive`, and run it with `scripts/drive.sh`. The two helpers
## below are the parts that are easy to get wrong; the shape of the visit is
## yours.

var _shots := 0


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_drive()


## A frame of the real game window, HUD and all.
##
## `frame_post_draw` is the wait that matters: without it the image is whatever
## was in the buffer before the camera moved, which looks like the camera not
## having moved.
func _snap(tag: String) -> void:
	for _i in 3:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("user://shot_%02d_%s.png" % [_shots, tag])
	_shots += 1
	print("shot ", tag)


## One key, up or down, as the keyboard would send it.
##
## Real `InputEventKey` with a **physical** keycode, because that is what the
## actions are bound to and what `_unhandled_input` listens for. A synthesised
## `InputEventAction` is ignored by the Instamatic, and `Input.action_press`
## only moves things that poll action state -- which movement does and nothing
## else here does.
func _key(code: Key, down: bool) -> void:
	var e := InputEventKey.new()
	e.physical_keycode = code
	e.pressed = down
	Input.parse_input_event(e)
	await get_tree().create_timer(0.3).timeout


func _drive() -> void:
	# Freeze the clock, or two runs of the same shot are lit differently and
	# nothing can be compared. 15:00 is daylight; 21:15 is after dark.
	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	# CSG has to build and the crowd has to spawn.
	await get_tree().create_timer(6.0).timeout

	var player := get_tree().get_first_node_in_group("player") as Node3D
	print("spawned at ", player.global_position)
	await _snap("spawn")

	# Spawn faces -Z and the fountain is at the origin, so forward is straight
	# at it. The kerb stops the capsule around z = 11.
	Input.action_press("move_forward")
	await get_tree().create_timer(5.6).timeout
	Input.action_release("move_forward")
	await get_tree().create_timer(0.8).timeout
	print("walked to ", player.global_position)
	await _snap("at_the_kerb")

	# F held, not tapped: a scripted tap outlasts TAP_SECONDS under software
	# rendering, so the game reads it as a hold and lowers on release.
	await _key(KEY_F, true)
	await get_tree().create_timer(0.6).timeout
	await _snap("viewfinder")

	# Enter is the shutter, while the finder is up.
	await _key(KEY_ENTER, true)
	await _key(KEY_ENTER, false)
	await get_tree().create_timer(1.5).timeout
	await _snap("after_shutter")

	await _key(KEY_F, false)

	var photos := DirAccess.open("user://photos")
	print("photos: ", photos.get_files() if photos else "none")
	get_tree().quit()
