extends CanvasLayer

## The pause screen: tabbed subscreens over a frozen park.
##
## The shape is Ocarina of Time's, which `CLAUDE.md` already cites for how
## sections load — the same answer applied to the interface. The game stops, the
## screen becomes a set of subscreens, the shoulders change tab and the stick
## moves inside one. That arrangement is not nostalgia for its own sake: it is
## the only common menu layout that never grew a pointer, and this game has a
## hard no-pointer constraint. A tabbed grid satisfies it by construction rather
## than by working around it.
##
## Colour-coding per tab is the Pokémon Snap and Donkey Kong Country habit and
## it earns its place — the body panel takes the current tab's colour, so the
## screen says where you are before a word of it has been read.
##
## The park really is paused. `get_tree().paused` stops the clock, the crowd and
## the player together, which is what makes this a menu rather than an overlay.
## The map is the exception and does not live only here: `map_tool` holds the
## same drawing up in the player's hands with the park still running, because
## `design.md` says nothing pauses for the player and a foldout in a live park
## is the version that honours it.

## Open or shut. The player and the HUD both hang off this — the player to stop
## looking, the HUD to put its prompts away.
signal menu_visibility_changed(open: bool)

## Above the HUD and below the section fade. Crossing a threshold with the menu
## somehow open should still go black over the top of it.
const LAYER := 64

const TABS := [
	{"id": &"map", "label": "Park map"},
	{"id": &"album", "label": "Album"},
	{"id": &"options", "label": "Options"},
	{"id": &"quit", "label": "Quit"},
]

## What the footer says on every screen. The tab keys are worth repeating
## because they are the one control a player has no reason to guess.
const HINTS := [
	["Q / E", "PAGE"], ["ARROWS", "MOVE"], ["ENTER", "CHOOSE"], ["ESC", "BACK"],
]

const SCRIM := Color(0.02, 0.03, 0.07, 0.55)

## The tab strip is indented from the frame below it rather than starting at its
## corner, because the frame's corner is cut and a tab hanging over a chamfer is
## the one place the two shapes argue.
const TAB_INDENT := 24
const TAB_GAP := 8
const TAB_PAD_X := 24
const TAB_PAD_Y := 9

## The field's hatch: fine diagonals at almost no opacity.
##
## The subscreens do not fill their field and two of them never will — options
## has four rows because four things are adjustable, and inventing a fifth to
## balance a rectangle is how a menu ends up with a graphics preset that changes
## nothing. So the field has to survive being mostly empty, and a flat expanse of
## one colour does not; it reads as a screen that failed to load.
##
## Diagonal rather than a grid, and at 3% rather than at anything you would
## notice. Star Fox's panels are all textured this way and the texture is never
## the thing you see — it is what stops the panel reading as a hole.
## What sits at the far end of the tab strip.
const MARK := "Keep your ticket"

const HATCH_STEP := 34.0
const HATCH_WIDTH := 3.0
const HATCH_COLOUR := Color(1.0, 1.0, 1.0, 0.012)

var _open := false
var _tab := 0
var _screens: Array[Control] = []
var _tab_panels: Array[PanelContainer] = []
var _tab_pads: Array[MarginContainer] = []
var _tab_labels: Array[Label] = []
var _mark: PanelContainer
var _body: PanelContainer
var _well: PanelContainer
var _hatch: Control
var _footer: PanelContainer
var _note: Label
var _root: Control
var _tween: Tween


func _ready() -> void:
	add_to_group("park_menu")
	layer = LAYER
	# The menu is the one thing that has to keep running while everything else
	# is stopped, or opening the pause screen would be the last input the game
	# ever accepted.
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build()
	_root.visible = false


func is_open() -> bool:
	return _open


func open(tab_id: StringName = &"") -> void:
	if _open:
		return
	if tab_id != &"":
		_select(_index_of(tab_id))
	_open = true
	_root.visible = true
	get_tree().paused = true
	# A paused game has no business holding the cursor, and the menu is
	# navigated with the keyboard anyway.
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_notify_shown()
	menu_visibility_changed.emit(true)


func close() -> void:
	if not _open:
		return
	_open = false
	_root.visible = false
	get_tree().paused = false
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_notify_hidden()
	menu_visibility_changed.emit(false)


func toggle(tab_id: StringName = &"") -> void:
	if _open:
		close()
	else:
		open(tab_id)


## `_input` rather than `_unhandled_input`, and handled events are swallowed:
## while the menu is up nothing below it should see a key, and the subscreens
## run at the same priority so their own `_input` gets first refusal on the
## arrow keys.
func _input(event: InputEvent) -> void:
	if event.is_action_pressed("menu"):
		toggle()
		get_viewport().set_input_as_handled()
		return

	# Straight to the album, which is the screen the player opens most and the
	# one that already had its own key. Period menus did this too — a button per
	# subscreen alongside the pause button.
	if event.is_action_pressed("album"):
		if _open and _current_id() == &"album":
			close()
		else:
			open(&"album")
		get_viewport().set_input_as_handled()
		return

	if not _open:
		return

	if event.is_action_pressed("ui_cancel"):
		close()
	elif event.is_action_pressed("menu_next_tab"):
		_select(wrapi(_tab + 1, 0, TABS.size()))
	elif event.is_action_pressed("menu_prev_tab"):
		_select(wrapi(_tab - 1, 0, TABS.size()))
	else:
		return
	get_viewport().set_input_as_handled()


func _current_id() -> StringName:
	return TABS[_tab]["id"]


func _index_of(id: StringName) -> int:
	for index in TABS.size():
		if TABS[index]["id"] == id:
			return index
	return 0


func _select(index: int) -> void:
	if index == _tab and not _screens.is_empty():
		return
	if _open and _tab < _screens.size():
		_hide_one(_screens[_tab])
	_tab = index
	for at in _screens.size():
		_screens[at].visible = at == _tab
	if _open:
		_notify_shown()
	# Only while the menu is up. `open(&"album")` selects its tab before the root
	# is visible, so animating there would mean the pause screen appears with a
	# tab halfway out of the strip — the movement has to be something the player
	# caused, not something they arrived in the middle of.
	_restyle(_open)


## Subscreens may implement `_on_shown` and `_on_hidden` — options re-reads its
## values on the way in, quit backs out of its confirm on the way out. Both are
## optional; a screen that needs neither implements neither.
## Cleared before the screen is told, not after. `_on_shown` is what makes a
## screen emit its first note — clearing afterwards wiped it every time, so the
## note line was permanently blank and the save row never got to explain itself.
func _notify_shown() -> void:
	_note.text = ""
	var screen := _screens[_tab]
	if screen.has_method("_on_shown"):
		screen.call("_on_shown")


func _notify_hidden() -> void:
	_hide_one(_screens[_tab])


func _hide_one(screen: Control) -> void:
	if screen.has_method("_on_hidden"):
		screen.call("_on_hidden")


func _build() -> void:
	var theme := ParkUI.theme()

	_root = Control.new()
	_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = theme
	add_child(_root)

	# Dimmed rather than blacked out. The Squaresoft half of the reference: you
	# can still see the park through the menu, which matters here because the
	# park is what the player came for and a menu that hides it entirely reads
	# as having left the game.
	var scrim := ColorRect.new()
	scrim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scrim.color = SCRIM
	scrim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(scrim)

	var frame := MarginContainer.new()
	frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		frame.add_theme_constant_override("margin_" + side, 64)
	for side in ["top", "bottom"]:
		frame.add_theme_constant_override("margin_" + side, 40)
	_root.add_child(frame)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(column)

	# Tabs and body in their own column at zero separation, so the selected tab
	# meets the frame rather than hovering above it. The outer column's gap is
	# for the footer, which is a separate object and should look like one.
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 0)
	page.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(page)

	var tab_row := MarginContainer.new()
	tab_row.add_theme_constant_override("margin_left", TAB_INDENT)
	tab_row.add_theme_constant_override("margin_right", TAB_INDENT)
	tab_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	page.add_child(tab_row)

	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", TAB_GAP)
	tabs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# The row is as tall as its tallest state whether or not anything is standing
	# that tall right now, and without that the rise does the opposite of what it
	# looks like it does. A row sized to its content grows when the selected tab
	# grows, and because every tab is bottom-aligned inside it, what actually
	# happens is that the other three sink and the whole body below them shifts
	# down — measured at eleven pixels a keypress. Reserving the space means the
	# selected tab rises into it and nothing else moves at all.
	tabs.custom_minimum_size.y = ceili(
		ParkUI.display_font().get_height(ParkUI.SIZE_TAB)) \
		+ TAB_PAD_Y * 2 + ParkUI.BORDER * 2 + ParkUI.TAB_RISE
	tab_row.add_child(tabs)

	for entry in TABS:
		var panel := PanelContainer.new()
		# Sized to its word, not to a quarter of the screen. Four tabs stretched
		# edge to edge with equal widths is a browser's shape and nothing else's
		# — it was the single thing making this read as a web page rather than as
		# a console menu, and no amount of colour on it was going to fix that.
		# A strip of plates that are as wide as what is written on them, packed
		# left, is what the reference actually does.
		panel.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		# Bottom-aligned, so the one that grows grows upward. The selected tab
		# gets its extra height as top padding rather than as a taller box, which
		# keeps every label sitting on the same line while the plate behind the
		# current one rises out of the row.
		panel.size_flags_vertical = Control.SIZE_SHRINK_END
		var pad := MarginContainer.new()
		for side in ["left", "right"]:
			pad.add_theme_constant_override("margin_" + side, TAB_PAD_X)
		for side in ["top", "bottom"]:
			pad.add_theme_constant_override("margin_" + side, TAB_PAD_Y)
		var label := Label.new()
		label.text = ParkUI.caps(entry["label"])
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		# Tabs are the one place in the menu with room for the display face —
		# four short words, all caps, nothing to read at length.
		ParkUI.display_label(label, ParkUI.SIZE_TAB)
		pad.add_child(label)
		panel.add_child(pad)
		tabs.add_child(panel)
		_tab_panels.append(panel)
		_tab_pads.append(pad)
		_tab_labels.append(label)

	# Tabs sized to their words leave the right half of the strip empty, and an
	# empty half is what a strip that used to stretch edge to edge looks like
	# when you stop stretching it. The park's own name closes it.
	#
	# Not a clock, and that is the one thing this space could obviously hold. The
	# time is read off the tower in the plaza and nowhere else, and a menu is
	# exactly where that rule would get quietly broken — a pause screen feels
	# like chrome rather than like the park, right up until it is the thing every
	# player checks the hour on.
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tabs.add_child(spacer)

	_mark = PanelContainer.new()
	_mark.size_flags_horizontal = Control.SIZE_SHRINK_END
	_mark.size_flags_vertical = Control.SIZE_SHRINK_END
	var mark_pad := MarginContainer.new()
	for side in ["left", "right"]:
		mark_pad.add_theme_constant_override("margin_" + side, 18)
	for side in ["top", "bottom"]:
		mark_pad.add_theme_constant_override("margin_" + side, TAB_PAD_Y + 4)
	var mark_label := Label.new()
	mark_label.text = ParkUI.caps(MARK)
	mark_label.add_theme_font_size_override("font_size", ParkUI.SIZE_SMALL)
	mark_label.add_theme_color_override("font_color", ParkUI.FRAME)
	mark_pad.add_child(mark_label)
	_mark.add_child(mark_pad)
	tabs.add_child(_mark)

	_body = PanelContainer.new()
	_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.add_child(_body)

	var body_pad := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		body_pad.add_theme_constant_override("margin_" + side, 12)
	_body.add_child(body_pad)

	# The well. `_body` is the frame and this is what is mounted in it, and the
	# two together are why the screen has a near and a far — one translucent
	# rectangle the size of the menu had neither. Its fill and its edge both take
	# the tab's colour in `_restyle`, so the subscreen reads as one object all
	# the way out to the border rather than as a box inside an unrelated box.
	_well = PanelContainer.new()
	_well.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_well.clip_contents = true
	body_pad.add_child(_well)

	# First child, so it is under everything the subscreens draw. A
	# `PanelContainer` fits every child to itself, which is what makes this work
	# without a second container to hold the pair.
	_hatch = Control.new()
	_hatch.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hatch.draw.connect(_draw_hatch)
	_well.add_child(_hatch)

	var well_pad := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		well_pad.add_theme_constant_override("margin_" + side, 20)
	_well.add_child(well_pad)

	var stack := Control.new()
	stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	stack.mouse_filter = Control.MOUSE_FILTER_IGNORE
	well_pad.add_child(stack)

	# The footer is a plate now rather than two loose lines under the frame. What
	# the selected thing is and how to move are both chrome, and chrome that sits
	# on the backdrop with nothing behind it is the tell that a layout ran out of
	# places to put things. Note left, keys right, one strip.
	_footer = PanelContainer.new()
	column.add_child(_footer)

	var footer_pad := MarginContainer.new()
	for side in ["left", "right"]:
		footer_pad.add_theme_constant_override("margin_" + side, 20)
	for side in ["top", "bottom"]:
		footer_pad.add_theme_constant_override("margin_" + side, 7)
	_footer.add_child(footer_pad)

	var footer_row := HBoxContainer.new()
	footer_row.add_theme_constant_override("separation", 24)
	footer_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	footer_pad.add_child(footer_row)

	# Before the subscreens, not after. A screen's `_ready` fires the moment it
	# is added to the stack and the album's fires a caption at once, so a note
	# label built afterwards is a null the first three screens all write to.
	_note = Label.new()
	_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_note.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_note.clip_text = true
	_note.add_theme_font_size_override("font_size", ParkUI.SIZE_SMALL)
	_note.add_theme_color_override("font_color", ParkUI.DIM)
	footer_row.add_child(_note)

	var hints := RichTextLabel.new()
	hints.fit_content = true
	hints.scroll_active = false
	hints.autowrap_mode = TextServer.AUTOWRAP_OFF
	hints.size_flags_horizontal = Control.SIZE_SHRINK_END
	ParkUI.prompts(hints, HINTS, false)
	footer_row.add_child(hints)

	for entry in TABS:
		var screen := _make_screen(entry["id"])
		screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		screen.visible = false
		if screen.has_signal("note_changed"):
			screen.connect("note_changed", _on_note_changed)
		stack.add_child(screen)
		_screens.append(screen)

	# Forced through `_select` from an impossible tab, or its "already there"
	# guard returns before anything has been styled and the menu opens with no
	# tab lit and no colour on the body.
	_tab = -1
	_select(0)


## The subscreens. Built here rather than as four `.tscn` files because each is
## one script that assembles itself, and a scene per screen would be four files
## whose entire content is "a Control with this script on it".
func _make_screen(id: StringName) -> Control:
	var screen: Control
	match id:
		&"map":
			screen = Control.new()
			screen.set_script(load("res://scenes/ui/map_view.gd"))
		&"album":
			screen = Control.new()
			screen.set_script(load("res://scenes/ui/album_view.gd"))
		&"options":
			screen = Control.new()
			screen.set_script(load("res://scenes/ui/options_view.gd"))
		&"quit":
			screen = Control.new()
			screen.set_script(load("res://scenes/ui/quit_view.gd"))
		_:
			screen = Control.new()
	screen.name = str(id)
	return screen


func _on_note_changed(note: String) -> void:
	_note.text = ParkUI.caps(note)


## The selected tab is a plate of its own colour that rises out of the row and
## runs into the frame below it, and the field behind the subscreen takes the
## same hue — so the tab and the screen it opens are visibly one object rather
## than a strip of buttons above a box.
func _restyle(animate: bool = false) -> void:
	var tint: Color = ParkUI.tab_colour(_current_id())

	# One tween for the whole strip, killed before it is replaced. Four separate
	# ones would be four things racing on the same four constants the moment the
	# tab key is held down, and the tab that lost would be left part-risen.
	if _tween != null:
		_tween.kill()
	_tween = ParkUI.tween(self) if animate else null

	for index in _tab_panels.size():
		var chosen := index == _tab
		var colour: Color = ParkUI.tab_colour(TABS[index]["id"])
		var box := ParkUI.plate(
			colour if chosen else ParkUI.TAB_IDLE,
			colour if chosen else colour.darkened(ParkUI.TAB_IDLE_FADE),
			ParkUI.CUT_TAB)
		# Square at the bottom on the selected one, so the plate and the frame
		# under it are one shape. A cut corner in the middle of a join reads as
		# a gap, which is the opposite of what the join is for.
		if chosen:
			box.corners = [true, true, false, false]
		_tab_panels[index].add_theme_stylebox_override("panel", box)
		# The rise. Extra top padding rather than a taller box: the labels stay
		# on one line and the plate grows upward out of the strip, which is the
		# half of the signal that survives not being able to read the words.
		#
		# A theme constant rather than a property, so it goes through
		# `tween_method` — and it is read back off the pad rather than derived
		# from which tab *was* selected, because a tab key held down retargets a
		# rise that is already part way up and has to start from where it is.
		var rise := float(TAB_PAD_Y + (ParkUI.TAB_RISE if chosen else 0))
		if _tween == null:
			_set_tab_rise(rise, index)
		else:
			ParkUI.settle(_tween.tween_method(_set_tab_rise.bind(index),
				float(_tab_pads[index].get_theme_constant("margin_top")),
				rise, ParkUI.MOVE_SECONDS), chosen)
		# Light letters with a black line, chosen or not. The selected tab used
		# to knock its label out in ink, which is a tile-era idea and made the
		# one tab you are looking at the only dark text on the screen. The fill
		# already swings from navy to full chroma, so selection has never needed
		# the letters to carry it as well.
		_tab_labels[index].add_theme_color_override("font_color",
			ParkUI.PAPER if chosen else ParkUI.DIM)
		# The chosen tab is the only one that gets the hot fill. Four gradients
		# in a row would be four titles competing, and the ramp would stop
		# meaning "this one" and start meaning "these are tabs".
		ParkUI.display_gradient(_tab_labels[index], chosen)

	# Gold frame, black line, and a field in the tab's own hue. The frame is the
	# same object on every subscreen because a frame does not change when you
	# hang a different picture in it; the colour moves inside it.
	if _body != null:
		_body.add_theme_stylebox_override("panel",
			ParkUI.plate(ParkUI.FRAME, ParkUI.FRAME_EDGE, ParkUI.CUT,
				ParkUI.BORDER_FRAME))
	if _well != null:
		_well.add_theme_stylebox_override("panel",
			ParkUI.plate(ParkUI.field(tint), tint, ParkUI.CUT - 5.0,
				ParkUI.BORDER, false))
	if _mark != null:
		_mark.add_theme_stylebox_override("panel",
			ParkUI.plate(ParkUI.TAB_IDLE, ParkUI.FRAME.darkened(0.4), ParkUI.CUT_TAB))
	if _footer != null:
		_footer.add_theme_stylebox_override("panel",
			ParkUI.plate(ParkUI.TAB_IDLE, tint.darkened(0.35), ParkUI.CUT_TAB))
	if _hatch != null:
		_hatch.queue_redraw()


## Rounded, because a theme constant is an integer and the pixel face under it
## has no business landing on a half. The tween runs in floats and this is where
## it comes back to the grid.
func _set_tab_rise(amount: float, index: int) -> void:
	_tab_pads[index].add_theme_constant_override("margin_top", roundi(amount))


## Diagonals across the field, running the way the light does — down to the
## right, matching the hard shadow every plate throws.
func _draw_hatch() -> void:
	var span := _hatch.size
	if span.x <= 0.0 or span.y <= 0.0:
		return
	var at := -span.y
	while at < span.x:
		_hatch.draw_line(Vector2(at, span.y), Vector2(at + span.y, 0.0),
			HATCH_COLOUR, HATCH_WIDTH, false)
		at += HATCH_STEP


