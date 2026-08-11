extends Control

## The album — a grid of filled and empty slots.
##
## Navigated with directional input only. Nothing here is a score; the empty
## slots are the point.

const COLUMNS := 5
const MINIMUM_SLOTS := 20
const SLOT_SIZE := Vector2(220.0, 132.0)
const SELECTED_TINT := Color(1, 1, 1, 1)
const UNSELECTED_TINT := Color(0.55, 0.55, 0.6, 1)

@onready var grid: GridContainer = $margin/layout/grid
@onready var caption: Label = $margin/layout/caption

var _slots: Array[PanelContainer] = []
var _selected := 0


func _ready() -> void:
	grid.columns = COLUMNS
	PhotoAlbum.photo_added.connect(_on_photo_added)
	visibility_changed.connect(_on_visibility_changed)
	_rebuild()


func _input(event: InputEvent) -> void:
	if not visible or _slots.is_empty():
		return

	var moved := false
	if event.is_action_pressed("ui_right"):
		_selected = mini(_selected + 1, _slots.size() - 1)
		moved = true
	elif event.is_action_pressed("ui_left"):
		_selected = maxi(_selected - 1, 0)
		moved = true
	elif event.is_action_pressed("ui_down"):
		_selected = mini(_selected + COLUMNS, _slots.size() - 1)
		moved = true
	elif event.is_action_pressed("ui_up"):
		_selected = maxi(_selected - COLUMNS, 0)
		moved = true

	if moved:
		accept_event()
		_refresh_selection()


func _rebuild() -> void:
	for child in grid.get_children():
		child.queue_free()
	_slots.clear()

	var filled := PhotoAlbum.count()
	var rows := int(ceil(float(filled) / float(COLUMNS)))
	var total := maxi(MINIMUM_SLOTS, rows * COLUMNS)

	for index in total:
		var slot := PanelContainer.new()
		slot.custom_minimum_size = SLOT_SIZE
		slot.clip_contents = true
		var thumbnail := TextureRect.new()
		thumbnail.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		thumbnail.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		if index < filled:
			thumbnail.texture = PhotoAlbum.thumbnails[index]
		slot.add_child(thumbnail)
		grid.add_child(slot)
		_slots.append(slot)

	_selected = clampi(_selected, 0, maxi(_slots.size() - 1, 0))
	_refresh_selection()


func _refresh_selection() -> void:
	for index in _slots.size():
		_slots[index].modulate = SELECTED_TINT if index == _selected else UNSELECTED_TINT

	var filled := PhotoAlbum.count()
	if _slots.is_empty():
		caption.text = ""
	elif _selected < filled:
		caption.text = PhotoAlbum.paths[_selected].get_file()
	else:
		caption.text = "empty slot"


func _on_photo_added(_index: int, _thumbnail: Texture2D) -> void:
	_rebuild()
	_selected = maxi(PhotoAlbum.count() - 1, 0)
	_refresh_selection()


func _on_visibility_changed() -> void:
	if visible:
		_refresh_selection()
