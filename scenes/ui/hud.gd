extends CanvasLayer

## Overlay layer: viewfinder, shutter flash, album.
##
## The capture lives here because this layer is what has to disappear for a
## frame before the viewport is read — a photograph should not contain its own
## viewfinder.

signal album_visibility_changed(album_open: bool)

const HINT_PLAYING := "[F] camera — tap or hold    [click / Enter] shutter    [E] ask    [V] view    [Space] jump    [Tab] album    [Esc] free mouse"
const HINT_ALBUM := "[arrows / d-pad] browse    [Tab / Y] close"

@onready var viewfinder: Control = $viewfinder
@onready var lines: Control = $viewfinder/lines
@onready var flash: ColorRect = $flash
@onready var hint: Label = $hint
@onready var album_view: Control = $album_view

var _capturing := false


func _ready() -> void:
	add_to_group("hud")
	viewfinder.visible = false
	album_view.visible = false
	flash.modulate.a = 0.0
	hint.text = HINT_PLAYING
	call_deferred("_connect_camera_tool")


func _connect_camera_tool() -> void:
	var camera_tool := get_tree().get_first_node_in_group("camera_tool")
	if camera_tool == null:
		push_warning("hud: no camera_tool found in the scene tree")
		return
	camera_tool.raised_changed.connect(_on_raised_changed)
	camera_tool.shutter_requested.connect(_on_shutter_requested)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("album"):
		_set_album_open(not album_view.visible)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel"):
		if album_view.visible:
			_set_album_open(false)
		else:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.pressed:
		if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not album_view.visible:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _set_album_open(album_open: bool) -> void:
	album_view.visible = album_open
	if album_open:
		viewfinder.visible = false
	hint.text = HINT_ALBUM if album_open else HINT_PLAYING
	album_visibility_changed.emit(album_open)


func _on_raised_changed(raised: bool) -> void:
	viewfinder.visible = raised and not album_view.visible


func _on_shutter_requested() -> void:
	if _capturing or album_view.visible:
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
