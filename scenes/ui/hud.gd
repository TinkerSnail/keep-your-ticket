extends CanvasLayer

## Overlay layer: viewfinder, shutter flash, album.
##
## The capture lives here because this layer is what has to disappear for a
## frame before the viewport is read — a photograph should not contain its own
## viewfinder.

## Control prompts, in the idiom of the period the game is set in: key names in
## a warm accent, the action in plain white, both in capitals, over a hard
## two-pixel shadow. Boxed keycaps are a much later convention — the late
## nineties put the key in a colour and trusted you to read it.
##
## Written as pairs rather than as one string, and handed to `ParkUI.prompts`,
## which is where the idiom itself now lives. The two rows in the game — this one
## and the pause screen's footer — were building the same string from two copies
## of the same loop, and they had drifted: the menu's was Silkscreen and this one
## was whatever face the engine falls back to, because nothing ever put a theme
## on the HUD. Only the pairs belong here.
const HINT_PLAYING := [
	["F", "CAMERA"], ["E", "ASK"], ["V", "VIEW"],
	["SPACE", "JUMP"], ["TAB", "ALBUM"], ["ESC", "MENU"],
]
## What is left when the finder is up. One line, because the surround is meant
## to read as the inside of a camera body and a row of prompts there undoes it.
const HINT_SHOOTING := [["SPACE", "SHUTTER"]]

## Matches the raise. Fast enough not to be a transition anyone waits through.
const HINT_FADE := 0.16

@onready var viewfinder: Control = $viewfinder
@onready var lines: Control = $viewfinder/lines
@onready var flash: ColorRect = $flash
@onready var hint: RichTextLabel = $hint
@onready var shutter_hint: RichTextLabel = $shutter_hint
@onready var minimap: Control = $minimap

var _capturing := false
var _hint_tween: Tween
var _shutter_hint_tween: Tween
var _minimap_tween: Tween
var _raised := false


func _ready() -> void:
	add_to_group("hud")
	viewfinder.visible = false
	flash.modulate.a = 0.0
	_set_prompts(hint, HINT_PLAYING)
	_set_prompts(shutter_hint, HINT_SHOOTING)
	shutter_hint.modulate.a = 0.0
	call_deferred("_connect")


func _connect() -> void:
	var camera_tool := get_tree().get_first_node_in_group("camera_tool")
	if camera_tool == null:
		push_warning("hud: no camera_tool found in the scene tree")
	else:
		camera_tool.raised_changed.connect(_on_raised_changed)
		camera_tool.shutter_requested.connect(_on_shutter_requested)

	# The menu replaces the HUD rather than sitting over it. A row of key
	# prompts showing along the bottom of a pause screen is the tell that an
	# overlay was put on top of a game instead of the game being paused.
	var menu := get_tree().get_first_node_in_group("park_menu")
	if menu != null and menu.has_signal("menu_visibility_changed"):
		menu.menu_visibility_changed.connect(_on_menu_visibility_changed)


func _on_menu_visibility_changed(open: bool) -> void:
	visible = not open


## The album key and escape both belong to `park_menu` now — the album is one of
## its subscreens and escape opens the menu rather than handing back the cursor.
## Releasing the mouse is what pausing does, so it no longer needs a key of its
## own. What is left here is the click that takes the cursor back.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			# The click that takes the mouse back is not also a shutter press.
			# Now that losing focus releases the cursor, this is the ordinary way
			# back into the game rather than a rare one, and without this a
			# player who tabbed away with the camera up returns holding a
			# photograph of wherever they happened to click.
			get_viewport().set_input_as_handled()


## Tabbing away hands the mouse back.
##
## Without this the game goes on believing it owns the cursor while the window
## is in the background: the pointer wanders off wherever the user takes it, and
## the first motion event after the window returns arrives as one enormous
## relative delta. The view whips round before the player has touched anything.
func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _on_raised_changed(raised: bool) -> void:
	_raised = raised
	_apply_overlays()


## One place decides what is on screen, from the camera rather than from
## whichever thing changed last.
##
## Opening the album used to set the finder invisible directly and nothing ever
## set it back, so raising the camera, opening the album and closing it again
## left the finder gone until it was toggled twice — the tool still believed it
## was raised, and only the overlay had been switched off behind its back. The
## album is a subscreen of a paused menu now and the whole layer goes with it,
## so there is only the camera left to read.
func _apply_overlays() -> void:
	viewfinder.visible = _raised
	# The hint goes out while the camera is up. It sat in the black surround,
	# which is the inside of the camera body — the one part of the frame meant
	# to read as an object rather than as a screen, and a line of bracketed key
	# names there undoes the whole tunnel.
	_hint_tween = _fade(hint, _hint_tween, not viewfinder.visible)

	# The minimap goes out with the prompts, and for the same reason. The black
	# surround is the inside of a camera body — the one part of the frame meant
	# to read as an object rather than as a screen — and a lit disc sitting in
	# it undoes the tunnel exactly the way a row of key names did. It is also
	# the moment the player is composing, which is the moment they should be
	# looking at the park rather than at a diagram of it.
	_minimap_tween = _fade(minimap, _minimap_tween, not viewfinder.visible)

	# Except for this one, which is the shutter and stays.
	#
	# Taking the whole row out of the finder was right and it left the one
	# control that matters in camera mode with nowhere to be taught: the line
	# saying how to fire the shutter was visible exactly when the camera was
	# down and gone the moment it went up. Playing it, the shutter turned out to
	# be undiscoverable — found by accident or not at all.
	#
	# It retired itself after the first photograph at first, on the reasoning
	# that one shot is enough to learn a key. Christina, having taken six of
	# them and then raised the camera again: keep it there. So it stays up
	# whenever the finder is. Three words rather than the row is what makes that
	# affordable — the row is what undid the tunnel, not the fact of a label.
	_shutter_hint_tween = _fade(shutter_hint, _shutter_hint_tween, viewfinder.visible)


## Key in the display face and the accent, action in the body face, everything
## centred. `park_ui` owns all of that; the HUD owns which pairs to show.
##
## It also raises the body size from the 15 this scene was authored with to 16.
## Silkscreen is drawn on an eight-pixel grid and is sharp at 16 and mush at
## anything between, and 15 was exactly the sort of value that looks harmless.
func _set_prompts(label: RichTextLabel, pairs: Array) -> void:
	ParkUI.prompts(label, pairs)


## Faded rather than switched, because a label vanishing on the same frame the
## finder appears reads as a glitch, and because the raise is already a tween.
func _fade(item: CanvasItem, tween: Tween, shown: bool) -> Tween:
	if tween != null and tween.is_valid():
		tween.kill()
	var next := create_tween()
	next.set_ease(Tween.EASE_OUT)
	next.tween_property(item, "modulate:a", 1.0 if shown else 0.0, HINT_FADE)
	return next


func _on_shutter_requested() -> void:
	if _capturing:
		return
	_capturing = true

	# Read before the overlay goes, because parallax depends on what the frame
	# is pointed at and the raycast does not care that the lines are hidden.
	var region := _picture_region()

	visible = false
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	visible = true

	if region.size.x > 0 and region.size.y > 0:
		image = image.get_region(region)
	PhotoAlbum.add_photo(image)
	_jolt()
	_capturing = false


## What the lens got, which is not what the finder showed. The bright lines mark
## the picture; the offset is how far below them the lens was actually looking,
## and it grows as the player closes on a subject. Nothing announces it. It
## turns up on the print.
func _picture_region() -> Rect2i:
	var view_size := Vector2(get_viewport().get_visible_rect().size)
	if lines.size.x <= 0.0 or lines.size.y <= 0.0:
		return Rect2i()
	var to_pixels := view_size / lines.size

	var frame: Rect2 = lines.picture_rect()
	var top_left := frame.position * to_pixels
	var frame_size := frame.size * to_pixels

	var camera_tool := get_tree().get_first_node_in_group("camera_tool")
	if camera_tool != null and camera_tool.has_method("parallax_screen_fraction"):
		top_left.y += camera_tool.parallax_screen_fraction() * view_size.y

	# The frame sits well inside the viewport, so the offset has room — but a
	# stretched window or an odd aspect could still push it off the bottom.
	top_left.x = clampf(top_left.x, 0.0, maxf(view_size.x - frame_size.x, 0.0))
	top_left.y = clampf(top_left.y, 0.0, maxf(view_size.y - frame_size.y, 0.0))

	return Rect2i(Vector2i(top_left.round()), Vector2i(frame_size.round()))


## There is no mirror in an Instamatic, so the finder never blacks out. The
## shutter fires and the view does not change — the clack and this twitch are the
## only evidence, and the player has no idea what they caught until it comes
## back developed.
func _jolt() -> void:
	var tween := create_tween()
	tween.tween_property(lines, "jolt", 3.0, 0.035)
	tween.tween_property(lines, "jolt", 0.0, 0.12).set_trans(Tween.TRANS_ELASTIC)


## The flash. Nothing fires it yet — daylight does not need it, and at night it
## lights the photographer as well as the shot, which is a decision that has to
## exist before the white frame does.
func _play_flash() -> void:
	flash.modulate.a = 0.5
	var tween := create_tween()
	tween.tween_property(flash, "modulate:a", 0.0, 0.3)
