class_name MenuList
extends VBoxContainer

## A vertical list of rows with an inverted selection bar.
##
## Options and quit are both this; the album is not, because a grid of pictures
## is its own thing. Factored out because two lists that navigate almost the
## same way is how a menu ends up with the cursor wrapping on one screen and
## stopping dead on the other.
##
## Directional input only. There is no pointer anywhere in this game and a list
## is the shape most likely to grow one by accident.
##
## `carded` is how it gets a home. A list of four rows centred in a field the
## size of the screen is four rows adrift in a field the size of the screen —
## the field is coloured and textured and it still cannot make a hundred pixels
## of text look placed. A plate under them can, and it is the same plate the tabs
## and the frame are made of, so the screen ends up with one object in it rather
## than with a margin problem.

## An action row was chosen.
signal activated(id: StringName)

## A toggle or a slider moved. Emitted on every step rather than on release —
## look sensitivity is only judged by moving the mouse, so the value has to be
## live while the row is being held.
signal changed(id: StringName, value: Variant)

## What the selected row wants said underneath it. The menu shows this; the list
## does not draw it, because the note belongs to the screen's layout rather than
## to the list's.
signal note_changed(note: String)

const ROW_HEIGHT := 44
const ROW_SEPARATION := 6
const ROW_PAD := 18

## Rows are a fixed width and the list is centred in whatever it is given.
##
## They used to fill the panel, which on a 1600px screen put "INVERT UP/DOWN" and
## the word "OFF" that belongs to it about twelve hundred pixels apart. A label
## and its value stop reading as a pair somewhere well before that, and the
## screen looked like four headings with four unrelated words down the far side.
## Six hundred is close to the width these menus were actually drawn at.
const ROW_WIDTH := 620

## The plate's own padding. Wider than it is tall, because the rows already carry
## their own vertical rhythm and a card with even margins reads as too tall.
const CARD_PAD_X := 24
const CARD_PAD_Y := 20

## How far a slider moves per press, as a fraction of its range. Eight steps
## end to end — enough to tune sensitivity, few enough that a player holding
## the key does not overshoot the whole scale before they let go.
const SLIDER_STEPS := 8.0

## Sliders are drawn rather than spelled. They were a string of block and dot
## characters, which is fine in a bitmap face chosen for the job and is a row of
## empty boxes in the engine's fallback — and the fallback is what the game runs
## on until a font is picked. Drawn cells look the same in both.
##
## Cells rather than a filled bar, because a bar is a meter and this game does
## not have meters. Eight cells is a setting with eight positions, which is a
## different thing from a quantity.
const CELL := Vector2(16.0, 16.0)
const CELL_GAP := 5.0

## Row kinds. `disabled` is drawn and selectable but does nothing when
## activated, which is deliberate: the save slot has a reason it cannot work yet
## and a row you cannot land on is a row that never explains itself.
enum Kind { ACTION, TOGGLE, SLIDER, DISABLED }

var _rows: Array[Dictionary] = []
var _panels: Array[PanelContainer] = []
var _labels: Array[Label] = []

## Either a `Label` or a drawn meter, depending on the row's kind, so this is
## the base type rather than `Label`.
var _values: Array[Control] = []
var _selected := 0
var _tween: Tween


## Wide enough for the furthest a row ever gets, and then a little.
##
## Without this the list is as wide as its widest row, which during a cursor move
## is neither — the leaving row is shrinking while the arriving one grows, so the
## maximum dips through the middle and the card breathes in and out on every
## keypress. The allowance on the end is for the overshoot, which is small and
## would otherwise be the one thing still able to push the width past its mark.
const OVERSHOOT := 6


func _ready() -> void:
	add_theme_constant_override("separation", ROW_SEPARATION)
	custom_minimum_size.x = ROW_WIDTH + ParkUI.JUT + OVERSHOOT


## Build the list inside a plate, centred in `parent`. Both list screens want
## exactly this and neither wants to know how it is put together.
static func carded(parent: Control) -> MenuList:
	var centre := CenterContainer.new()
	centre.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	centre.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(centre)

	# Blue, on a field that is green or violet or red. `park_ui` argues blue is
	# the right canvas because none of the references is blue and a warm surface
	# under a gold selection bar is gold on gold — the field moved to the tab's
	# hue, so this is where that argument now lives.
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel",
		ParkUI.plate(ParkUI.PANEL, ParkUI.PANEL_HI, ParkUI.CUT))
	centre.add_child(card)

	var pad := MarginContainer.new()
	for side in ["left", "right"]:
		pad.add_theme_constant_override("margin_" + side, CARD_PAD_X)
	for side in ["top", "bottom"]:
		pad.add_theme_constant_override("margin_" + side, CARD_PAD_Y)
	card.add_child(pad)

	var list := MenuList.new()
	pad.add_child(list)
	return list


## Replace the whole list. Rows are dictionaries so a screen can declare its
## contents in one literal rather than assembling widgets — see `options_view`.
##
##   id        StringName, unique within the list
##   label     String, shown left, capitalised here
##   kind      Kind
##   value     bool for TOGGLE, float 0..1 for SLIDER, unused otherwise
##   note      String, shown under the list while this row is selected
func set_rows(rows: Array[Dictionary]) -> void:
	for child in get_children():
		child.queue_free()
	_rows = rows.duplicate(true)
	_panels.clear()
	_labels.clear()
	_values.clear()

	for row in _rows:
		var panel := PanelContainer.new()
		panel.custom_minimum_size = Vector2(ROW_WIDTH, ROW_HEIGHT)
		# Left-aligned inside the list rather than filling it, so the selected
		# row can be wider than the others without moving the ones above it.
		panel.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN

		var box := HBoxContainer.new()
		box.add_theme_constant_override("separation", ROW_PAD)

		var pad := MarginContainer.new()
		pad.add_theme_constant_override("margin_left", ROW_PAD)
		pad.add_theme_constant_override("margin_right", ROW_PAD)
		pad.add_child(box)

		var label := Label.new()
		label.text = ParkUI.caps(row.get("label", ""))
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL

		var value: Control
		if int(row.get("kind", Kind.ACTION)) == Kind.SLIDER:
			value = _make_meter()
		else:
			var text := Label.new()
			text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			text.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			value = text

		box.add_child(label)
		box.add_child(value)
		panel.add_child(pad)
		add_child(panel)

		_panels.append(panel)
		_labels.append(label)
		_values.append(value)

	_selected = clampi(_selected, 0, maxi(_rows.size() - 1, 0))
	_refresh()


func selected_id() -> StringName:
	if _rows.is_empty():
		return &""
	return _rows[_selected].get("id", &"")


## Set a row's value from outside, without emitting. Used when a screen loads
## saved settings into a list it has already built.
func set_value(id: StringName, value: Variant) -> void:
	for row in _rows:
		if row.get("id", &"") == id:
			row["value"] = value
			break
	_refresh()


## `_input` rather than `_unhandled_input`: the menu is the only thing alive
## while the tree is paused, so there is nothing below to leave events for, and
## `accept_event` stops the tab bar seeing the same press.
func _input(event: InputEvent) -> void:
	if not is_visible_in_tree() or _rows.is_empty():
		return

	if event.is_action_pressed("ui_down", true):
		_move(1)
	elif event.is_action_pressed("ui_up", true):
		_move(-1)
	elif event.is_action_pressed("ui_left", true):
		_adjust(-1)
	elif event.is_action_pressed("ui_right", true):
		_adjust(1)
	elif event.is_action_pressed("ui_accept"):
		_activate()
	else:
		return
	accept_event()


## Wraps. A four-row list where down does nothing on the last row is a list that
## makes the player check whether the input registered.
##
## The one place the list animates. Adjusting a slider moves nothing — the bar
## stays where it is and only the cells change — and rebuilding the rows has to
## land them at their final widths, or opening a screen would play the cursor
## sliding into place on a list that was not there a frame ago.
func _move(step: int) -> void:
	_selected = wrapi(_selected + step, 0, _rows.size())
	_refresh(true)


func _adjust(step: int) -> void:
	var row := _rows[_selected]
	match int(row.get("kind", Kind.ACTION)):
		Kind.TOGGLE:
			row["value"] = not bool(row.get("value", false))
		Kind.SLIDER:
			var at := float(row.get("value", 0.0))
			row["value"] = clampf(at + float(step) / SLIDER_STEPS, 0.0, 1.0)
		_:
			return
	_refresh()
	changed.emit(row.get("id", &""), row["value"])


func _activate() -> void:
	var row := _rows[_selected]
	if int(row.get("kind", Kind.ACTION)) != Kind.ACTION:
		# A toggle answers to left and right, not to accept — but accept is what
		# a player presses first, so it flips rather than doing nothing.
		if int(row.get("kind", Kind.ACTION)) == Kind.TOGGLE:
			_adjust(1)
		return
	activated.emit(row.get("id", &""))


## The inverted bar, and the row it is on sticking out further than the rest.
##
## The bar alone was the whole signal before, and a bar is colour — it is the
## thing that stops working the moment a screen has anything else bright on it.
## The jut is the second signal and it is the one that survives a photograph of
## the screen too small to read: Melee, Smash 64 and Star Fox's mission select
## all slide the current plate out of the stack, and none of them relies on the
## tint to say which one you are on.
func _refresh(animate: bool = false) -> void:
	# One tween for the list, killed before it is replaced — the cursor held on
	# the down key retargets rows that are still moving, and two tweens on one
	# row's width leaves it stuck between the two.
	if _tween != null:
		_tween.kill()
	_tween = ParkUI.tween(self) if animate else null

	for index in _rows.size():
		var row := _rows[index]
		var kind := int(row.get("kind", Kind.ACTION))
		var chosen := index == _selected

		var width := float(ROW_WIDTH + (ParkUI.JUT if chosen else 0))
		if _tween == null:
			_panels[index].custom_minimum_size.x = width
		else:
			ParkUI.settle(_tween.tween_property(_panels[index],
				"custom_minimum_size:x", width, ParkUI.MOVE_SECONDS), chosen)
		var box := ParkUI.plate(
			ParkUI.SELECT_FILL if chosen else Color(0, 0, 0, 0),
			ParkUI.SELECT_FILL if chosen else Color(0, 0, 0, 0),
			ParkUI.CUT_ROW, ParkUI.BORDER, false)
		_panels[index].add_theme_stylebox_override("panel", box)

		var tint := ParkUI.SELECT_TEXT if chosen else ParkUI.TEXT
		if kind == Kind.DISABLED:
			# Dimmed either way. A disabled row under the bar still has to look
			# unavailable or the bar reads as having enabled it.
			tint = ParkUI.INK.lerp(ParkUI.DIM, 0.55) if chosen else ParkUI.DIM
		_labels[index].add_theme_color_override("font_color", tint)

		var value := _values[index]
		if value is Label:
			value.add_theme_color_override("font_color", tint)
			(value as Label).text = _value_text(row)
		else:
			# The meter carries its own state so the draw handler does not have
			# to reach back into a row index that may have been rebuilt.
			value.set_meta("value", float(row.get("value", 0.0)))
			value.set_meta("chosen", chosen)
			value.queue_redraw()

	note_changed.emit(str(_rows[_selected].get("note", "")))


func _value_text(row: Dictionary) -> String:
	match int(row.get("kind", Kind.ACTION)):
		Kind.TOGGLE:
			return "ON" if bool(row.get("value", false)) else "OFF"
		Kind.DISABLED:
			return "—"
		_:
			return ""


func _make_meter() -> Control:
	var meter := Control.new()
	meter.custom_minimum_size = Vector2(
		SLIDER_STEPS * (CELL.x + CELL_GAP) - CELL_GAP, CELL.y)
	meter.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	meter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	meter.draw.connect(_draw_meter.bind(meter))
	return meter


## Filled cells are solid, empty ones are outlines. Under the selection bar both
## invert to ink, so the meter stays legible on gold without a second palette.
func _draw_meter(meter: Control) -> void:
	var value := float(meter.get_meta("value", 0.0))
	var chosen := bool(meter.get_meta("chosen", false))
	var filled := int(round(value * SLIDER_STEPS))

	var on := ParkUI.SELECT_TEXT if chosen else ParkUI.ACCENT
	var off := Color(ParkUI.SELECT_TEXT, 0.3) if chosen else Color(ParkUI.DIM, 0.6)

	for step in int(SLIDER_STEPS):
		var rect := Rect2(Vector2(float(step) * (CELL.x + CELL_GAP), 0.0), CELL)
		if step < filled:
			meter.draw_rect(rect, on, true)
		else:
			meter.draw_rect(rect, off, false, ParkUI.BORDER)
