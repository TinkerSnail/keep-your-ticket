extends Control

## The options subscreen.
##
## Four rows, because four things are actually adjustable. The temptation with a
## menu is to fill it — graphics presets, audio sliders, a key rebinder — and
## every one of those would be a control over something the game either does not
## have yet or does not let the player change. An options screen that is honest
## about a small game is period-correct anyway; the machines these menus come
## from had a page, not a tabbed preferences pane.

signal note_changed(note: String)

var _list: MenuList


func _ready() -> void:
	# Centred and on a plate, like the album's grid and the map's sheet. Four rows
	# pinned to the top-left of a panel the size of the screen is a list that has
	# been dropped into a room; the same four on a card in the middle is a page.
	_list = MenuList.carded(self)

	_list.changed.connect(_on_changed)
	_list.note_changed.connect(func(note: String) -> void: note_changed.emit(note))
	_rebuild()


## Values come off `ParkSettings` at build time rather than being held here, so
## the screen cannot drift from what is stored — closing and reopening the menu
## re-reads rather than showing whatever was last displayed.
func _rebuild() -> void:
	_list.set_rows([
		{
			"id": &"look_sensitivity",
			"label": "Look speed",
			"kind": MenuList.Kind.SLIDER,
			"value": ParkSettings.get_value(&"look_sensitivity"),
			"note": "How far the view turns for the same movement.",
		},
		{
			"id": &"invert_look_y",
			"label": "Invert up/down",
			"kind": MenuList.Kind.TOGGLE,
			"value": ParkSettings.get_value(&"invert_look_y"),
			"note": "Push away to look up, the way a camera tilts.",
		},
		{
			"id": &"start_third_person",
			"label": "Start behind",
			"kind": MenuList.Kind.TOGGLE,
			"value": ParkSettings.get_value(&"start_third_person"),
			"note": "Which view the park starts in. The camera always drops to the eye.",
		},
		{
			"id": &"fullscreen",
			"label": "Full screen",
			"kind": MenuList.Kind.TOGGLE,
			"value": ParkSettings.get_value(&"fullscreen"),
			"note": "",
		},
	])


func _on_changed(id: StringName, value: Variant) -> void:
	ParkSettings.set_value(id, value)


## Reopening re-reads. Cheap, and it means a setting changed from anywhere else
## — a future key, a config file edited between sessions — shows up here.
func _on_shown() -> void:
	_rebuild()
