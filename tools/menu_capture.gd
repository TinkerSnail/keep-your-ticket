extends Node

## Throwaway: opens each menu tab over the running park and saves a screenshot.
##
## Needs a scene root rather than `--script`, same as the other capture tools.
## Write `_menu_capture.tscn` with this as the root, run
## `godot --path . _menu_capture.tscn`, and delete the scene afterwards.

const TABS := [&"map", &"album", &"options", &"quit"]
const SETTLE := 2.0
## `user://`, not `res://`. A running project cannot write to `res://` — the save
## fails, nothing appears, and because a windowed run is launched through `open`
## its stdout is detached, so the error goes nowhere and the tool looks like it
## is hanging. `capture.gd` has always written to `user://` for this reason.
const OUT := "user://%s.png"


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)

	# Mid-afternoon, so there is a lit park behind the scrim rather than the
	# ten-o'clock light the clock starts at.
	ParkClock.set_clock(15, 20)

	await get_tree().create_timer(SETTLE).timeout

	# No photographs are taken here, on purpose. An earlier version added three
	# so the album would have filled slots to show, and they went straight into
	# `user://photos` alongside the real ones — a capture tool for a photography
	# game has no business leaving pictures in the player's album. Whatever is
	# already in there is the sample.

	# The HUD, at two headings, so the minimap can be checked for turning with
	# the player rather than merely existing. A still of a rotating map proves
	# nothing on its own.
	var player := get_tree().get_first_node_in_group("player") as Node3D
	for heading in [0.0, 125.0]:
		if player != null:
			player.rotation.y = deg_to_rad(heading)
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var frame := get_viewport().get_texture().get_image()
		var tag := "hud_%d" % int(heading)
		frame.save_png(OUT % tag)
		# And a crop of the corner, because the disc is 184px in a 1600px frame
		# and the symbols cannot be judged at that size.
		frame.get_region(Rect2i(8, 644, 216, 216)).save_png(OUT % (tag + "_corner"))
		print("saved ", OUT % tag)

	var menu := get_tree().get_first_node_in_group("park_menu")
	if menu == null:
		push_error("menu_capture: no park_menu in the tree")
		get_tree().quit()
		return

	for tab in TABS:
		menu.call("close")
		menu.call("open", tab)
		# Two frames: one for the layout to settle after the tab swap, one to
		# draw it. A single frame catches the previous tab's panel colour.
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var image := get_viewport().get_texture().get_image()
		image.save_png(OUT % tab)
		print("saved ", OUT % tab)

	get_tree().quit()
