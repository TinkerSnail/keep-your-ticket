extends Node

## Throwaway: drives the pause menu with real input and checks what it does.
##
## The same argument as `walk_test.gd`. A screenshot shows that a screen draws;
## it does not show that the shoulders change tab, that the cursor wraps, that
## backing out of quit gets you back, or that the park is actually stopped while
## you are in there. None of that is visible in a still and all of it is what
## the menu is for.
##
## Events go through `Input.parse_input_event` rather than by calling the menu's
## own methods, because the thing under test is partly the input routing — three
## `_input` handlers at the same priority, each expecting first refusal on a
## different key. Calling `_select` directly would pass while the real thing
## swallowed every arrow.
##
## Needs a scene root rather than `--script`, same as the other tools. Write
## `_menu_test.tscn` with this as the root and run `godot --path . _menu_test.tscn`.
##
## It never confirms the quit row. That row ends the process, which would look
## exactly like a crash in the middle of a test run.

const SETTLE := 1.5
const TABS := [&"map", &"album", &"options", &"quit"]

var _failures := 0
var _checks := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	ParkClock.set_clock(15, 20)
	await get_tree().create_timer(SETTLE).timeout

	var menu := get_tree().get_first_node_in_group("park_menu")
	if menu == null:
		push_error("menu_test: no park_menu in the tree")
		get_tree().quit(1)
		return

	await _shut(menu)
	await _opens_and_pauses(menu)
	await _tabs_cycle(menu)
	await _album_moves(menu)
	await _options_moves(menu)
	await _quit_backs_out(menu)
	await _closes_and_resumes(menu)

	print("")
	print("menu_test: %d checks, %d failed" % [_checks, _failures])
	get_tree().quit(1 if _failures > 0 else 0)


func _check(what: String, got, want) -> void:
	_checks += 1
	var ok: bool = got == want
	if not ok:
		_failures += 1
	print("%s  %s  (got %s, wanted %s)" % ["PASS" if ok else "FAIL", what, got, want])


## Actions, not keycodes. The bindings are the player's to change and a test
## that presses a physical key is testing the keyboard layout.
func _press(action: String) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.parse_input_event(event)
	await get_tree().process_frame
	var release := InputEventAction.new()
	release.action = action
	release.pressed = false
	Input.parse_input_event(release)
	await get_tree().process_frame
	await get_tree().process_frame


func _tab_of(menu: Node) -> int:
	return int(menu.get("_tab"))


func _shut(menu: Node) -> void:
	if bool(menu.call("is_open")):
		menu.call("close")
	await get_tree().process_frame
	_check("starts shut", bool(menu.call("is_open")), false)
	_check("park running at start", get_tree().paused, false)


func _opens_and_pauses(menu: Node) -> void:
	await _press("menu")
	_check("menu opens", bool(menu.call("is_open")), true)
	_check("park pauses with it", get_tree().paused, true)


## All the way round and one past, because wrapping is the bit that gets
## written as `min(tab + 1, 3)` and never noticed.
func _tabs_cycle(menu: Node) -> void:
	var start := _tab_of(menu)
	for step in TABS.size():
		await _press("menu_next_tab")
		var want := (start + step + 1) % TABS.size()
		_check("next tab lands on %s" % TABS[want], _tab_of(menu), want)
	_check("forward cycle returns to start", _tab_of(menu), start)

	await _press("menu_prev_tab")
	_check("previous tab wraps backwards", _tab_of(menu),
		(start - 1 + TABS.size()) % TABS.size())
	await _press("menu_next_tab")


func _goto(menu: Node, id: StringName) -> void:
	for guard in TABS.size() + 1:
		if TABS[_tab_of(menu)] == id:
			return
		await _press("menu_next_tab")


## The album's cursor is an index across the whole album rather than into the
## page, so walking off the bottom row is supposed to turn the page instead of
## stopping. That is the claim worth testing.
func _album_moves(menu: Node) -> void:
	await _goto(menu, &"album")
	_check("on the album", TABS[_tab_of(menu)], &"album")
	var view := _screen(menu, 1)
	if view == null:
		return
	var start := int(view.get("_selected"))
	await _press("ui_right")
	_check("right moves the cursor", int(view.get("_selected")), start + 1)
	await _press("ui_left")
	_check("left moves it back", int(view.get("_selected")), start)
	var page := int(view.get("_page"))
	for _i in 5:
		await _press("ui_down")
	print("      album page %d -> %d, cursor %d" %
		[page, int(view.get("_page")), int(view.get("_selected"))])


func _options_moves(menu: Node) -> void:
	await _goto(menu, &"options")
	_check("on the options", TABS[_tab_of(menu)], &"options")
	var before: Variant = ParkSettings.get_value(&"look_sensitivity")
	await _press("ui_down")
	await _press("ui_left")
	var after: Variant = ParkSettings.get_value(&"look_sensitivity")
	print("      look_sensitivity %s -> %s" % [before, after])
	await _press("ui_up")


## Onto the quit row and straight back off it. `ui_cancel` on a subscreen is
## meant to back out of the screen's own state before it closes the menu, and
## this is the one screen where getting that wrong ends the process.
func _quit_backs_out(menu: Node) -> void:
	await _goto(menu, &"quit")
	_check("on the quit", TABS[_tab_of(menu)], &"quit")
	await _press("ui_cancel")
	print("      menu open after cancel on quit: %s" % bool(menu.call("is_open")))
	if not bool(menu.call("is_open")):
		await _press("menu")
		await _goto(menu, &"album")


func _closes_and_resumes(menu: Node) -> void:
	if bool(menu.call("is_open")):
		await _press("menu")
	_check("menu closes", bool(menu.call("is_open")), false)
	_check("park resumes", get_tree().paused, false)


func _screen(menu: Node, index: int) -> Control:
	var screens = menu.get("_screens")
	if screens == null or index >= screens.size():
		push_error("menu_test: no screen at %d" % index)
		return null
	return screens[index]
