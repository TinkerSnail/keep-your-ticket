extends CanvasLayer

## Overlay layer: viewfinder, shutter flash, album.
##
## The capture lives here because this layer is what has to disappear for a
## frame before the viewport is read — a photograph should not contain its own
## viewfinder.

signal album_visibility_changed(album_open: bool)

const HINT_PLAYING := "[Space] camera — tap or hold    [click / Enter] shutter    [Tab] album    [Esc] free mouse"
const HINT_ALBUM := "[arrows / d-pad] browse    [Tab / Y] close"

@onready var viewfinder: Control = $viewfinder
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

	visible = false
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	visible = true

	PhotoAlbum.add_photo(image)
	_play_flash()
	_capturing = false


func _play_flash() -> void:
	flash.modulate.a = 0.5
	var tween := create_tween()
	tween.tween_property(flash, "modulate:a", 0.0, 0.3)
