extends Control

## The album — a grid of filled and empty slots.
##
## Navigated with directional input only. Nothing here is a score; the empty
## slots are the point, and they are drawn as empty pockets rather than hidden,
## because a grid that grows as you fill it never shows you what is missing.
##
## This used to be a screen of its own with its own backdrop and its own title,
## opened straight off the album key. It is now a subscreen of the pause menu
## and builds its own children rather than reading them out of `hud.tscn` — the
## hand-authored greys in that scene were exactly the styling the menu theme
## replaced, so there was nothing in the layout worth keeping.

signal note_changed(note: String)

## The album turns pages, because it is an album. A grid that grows until it
## runs off the bottom of the panel is what this was before — thirty-six
## photographs and the last two rows were behind the footer. Paging is also the
## period answer and the thematic one at once: five across, four down, and the
## corner tells you which page of how many.
const COLUMNS := 5
const ROWS := 4
const PER_PAGE := COLUMNS * ROWS
## A floor, not a size. The slots used to be exactly this and the grid was
## centred in the field, so the album was a small rectangle of photographs
## floating in a much larger rectangle of nothing — fine while the field had no
## edge, and obviously wrong once it became a well inside a frame, because the
## frame drew a line around the emptiness and made it read as unused rather than
## as background.
##
## They fill the well now and this only stops them collapsing if the window is
## ever small enough for twenty of them not to fit. The thumbnails were already
## `STRETCH_KEEP_ASPECT_COVERED`, so a slot that ends up a little wider or
## squarer than a photograph crops it rather than stretching it.
const SLOT_MIN := Vector2(120.0, 72.0)
const SLOT_GAP := 12

## The empty pocket and the frame around the selected one. Selection is a frame
## rather than a tint because the slots are photographs — dimming the ones you
## are not on makes the album look like it is loading.
const EMPTY_FILL := Color(0.06, 0.09, 0.18, 0.85)
const EMPTY_EDGE := Color(0.20, 0.27, 0.45, 1.0)

var _grid: GridContainer
var _slots: Array[PanelContainer] = []

## An index across the whole album, not into the visible page. Which page is
## showing is derived from it, so moving off the bottom row turns the page
## rather than stopping — one cursor, no separate page state to get out of step.
var _selected := 0
var _page := -1


func _ready() -> void:
	# Straight onto the field rather than into a `CenterContainer`. Centring is
	# what kept the grid at its minimum size no matter how much room it had.
	_grid = GridContainer.new()
	_grid.columns = COLUMNS
	_grid.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_grid.add_theme_constant_override("h_separation", SLOT_GAP)
	_grid.add_theme_constant_override("v_separation", SLOT_GAP)
	_grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_grid)

	PhotoAlbum.photo_added.connect(_on_photo_added)
	_show_page()


## `_input` and swallowed, matching `menu_list`: the menu runs everything at the
## same priority and the tab bar must not also see the arrow keys.
func _input(event: InputEvent) -> void:
	if not is_visible_in_tree():
		return
	var total := _total()

	var moved := false
	if event.is_action_pressed("ui_right", true):
		_selected = mini(_selected + 1, total - 1)
		moved = true
	elif event.is_action_pressed("ui_left", true):
		_selected = maxi(_selected - 1, 0)
		moved = true
	elif event.is_action_pressed("ui_down", true):
		_selected = mini(_selected + COLUMNS, total - 1)
		moved = true
	elif event.is_action_pressed("ui_up", true):
		_selected = maxi(_selected - COLUMNS, 0)
		moved = true

	if moved:
		accept_event()
		_show_page()


## Every photograph, rounded up to a whole page, never fewer than one page. The
## trailing empty slots are deliberate — the album is filled and empty slots,
## and a grid sized exactly to what you have never shows what you are missing.
func _total() -> int:
	var pages := maxi(int(ceil(float(PhotoAlbum.count()) / float(PER_PAGE))), 1)
	return pages * PER_PAGE


func _pages() -> int:
	return _total() / PER_PAGE


## Which page is showing follows the cursor rather than being steered
## separately, so moving off the bottom row turns the page instead of stopping.
## Only rebuilds when the page actually changes.
func _show_page() -> void:
	var wanted := _selected / PER_PAGE
	if wanted != _page:
		_page = wanted
		_rebuild()
	else:
		_refresh_selection()


func _rebuild() -> void:
	for child in _grid.get_children():
		# Out of the tree as well as freed. A `queue_free` alone leaves the old
		# page's slots in the grid for the rest of the frame, and the container
		# lays out twenty-one of them before they go.
		_grid.remove_child(child)
		child.queue_free()
	_slots.clear()

	var filled := PhotoAlbum.count()
	var first := _page * PER_PAGE

	for offset in PER_PAGE:
		var index := first + offset
		var slot := PanelContainer.new()
		slot.custom_minimum_size = SLOT_MIN
		# Every slot expands, so `GridContainer` hands the leftover width and
		# height out evenly across the five columns and four rows instead of
		# leaving it around the outside.
		slot.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		slot.size_flags_vertical = Control.SIZE_EXPAND_FILL
		slot.clip_contents = true
		var thumbnail := TextureRect.new()
		thumbnail.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		thumbnail.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		if index < filled:
			thumbnail.texture = PhotoAlbum.thumbnails[index]
		slot.add_child(thumbnail)
		_grid.add_child(slot)
		_slots.append(slot)

	_refresh_selection()


func _refresh_selection() -> void:
	var first := _page * PER_PAGE
	for offset in _slots.size():
		var chosen := first + offset == _selected
		var box := ParkUI.inset(EMPTY_FILL,
			ParkUI.ACCENT if chosen else EMPTY_EDGE)
		if chosen:
			box.set_border_width_all(ParkUI.BORDER * 2)
		_slots[offset].add_theme_stylebox_override("panel", box)

	note_changed.emit(_caption())


## Where you are in the album, then what you are looking at. The filename is
## also the timestamp — `PhotoAlbum` date-stamps them — so the caption doubles
## as when the picture was taken without a second field having to exist.
func _caption() -> String:
	var where := "Page %d of %d" % [_page + 1, _pages()]
	if _selected < PhotoAlbum.count():
		return "%s   ·   %s" % [where, PhotoAlbum.paths[_selected].get_file()]
	return "%s   ·   Empty slot" % where


## A new photograph selects itself, which may be on a page that does not exist
## yet — so the page is invalidated rather than refreshed.
func _on_photo_added(_index: int, _thumbnail: Texture2D) -> void:
	_selected = maxi(PhotoAlbum.count() - 1, 0)
	_page = -1
	_show_page()


func _on_shown() -> void:
	_page = -1
	_show_page()
