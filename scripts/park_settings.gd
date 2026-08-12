extends Node

## Player settings, autoloaded as `ParkSettings`.
##
## Deliberately short. The options screen offers what the game actually has —
## how the look behaves, which view it starts in, and whether the window is
## full screen. There is no audio yet, so there are no volume rows; a slider
## that moves and changes nothing is worse than an absent one.
##
## This is not save data. Settings are how the game is operated and belong to
## the machine; the park's own state — the hour, the standing section, who is
## owed a claim ticket — is a different file that does not exist yet. Keeping
## them apart now means the day one is written, this one does not have to be
## renamed or migrated.

signal changed(key: StringName, value: Variant)

const PATH := "user://settings.cfg"
const SECTION := "player"

## Defaults, and the list of what exists. A key not in here cannot be set —
## which is what stops a stale config file from a future build putting
## unrecognised values into the game.
##
## Sliders are 0..1 and get mapped where they are applied, so the file stays
## readable and the ranges can be retuned without invalidating anyone's config.
const DEFAULTS := {
	&"look_sensitivity": 0.5,
	&"invert_look_y": false,
	&"start_third_person": true,
	&"fullscreen": false,
}

## What a look sensitivity of 0 and 1 mean, as multipliers over the player's own
## exported values. The middle of the slider is deliberately not 1.0× — it is
## the geometric mean, so that half-way feels half-way rather than the bottom
## half of the scale being a rounding error.
const LOOK_MIN := 0.35
const LOOK_MAX := 2.4

var _values := {}


func _ready() -> void:
	_values = DEFAULTS.duplicate()
	_load()
	# Deferred because the window and the player are both younger than the
	# autoloads. Applying full screen in an autoload's `_ready` sets it on a
	# window that has not finished being sized.
	call_deferred("apply_all")


func get_value(key: StringName) -> Variant:
	return _values.get(key, DEFAULTS.get(key))


## Set, apply, and write. Written on every change rather than on quit, because
## the game can be closed from the window's own button and a settings file that
## only survives a tidy exit is a settings file that loses the one change the
## player made before they closed it.
func set_value(key: StringName, value: Variant) -> void:
	if not DEFAULTS.has(key):
		push_warning("settings: unknown key '%s'" % key)
		return
	if _values.get(key) == value:
		return
	_values[key] = value
	_apply(key)
	_save()
	changed.emit(key, value)


## The look multiplier, mapped off the stored 0..1. Read by the player rather
## than pushed at it, so a player that enters the tree after a section swap
## picks up the current setting without anything having to remember to tell it.
func look_scale() -> float:
	return lerpf(LOOK_MIN, LOOK_MAX, float(get_value(&"look_sensitivity")))


func apply_all() -> void:
	for key in DEFAULTS:
		_apply(key)


func _apply(key: StringName) -> void:
	match key:
		&"fullscreen":
			var mode := DisplayServer.WINDOW_MODE_FULLSCREEN if bool(get_value(key)) \
				else DisplayServer.WINDOW_MODE_WINDOWED
			DisplayServer.window_set_mode(mode)
		&"look_sensitivity", &"invert_look_y":
			var player := get_tree().get_first_node_in_group("player")
			if player != null and player.has_method("apply_look_settings"):
				player.call("apply_look_settings")
		&"start_third_person":
			# Read at spawn, not applied live. Flipping the default view while
			# standing in the park would yank the camera for a setting that is
			# about how the *next* session starts.
			pass


func _load() -> void:
	var file := ConfigFile.new()
	if file.load(PATH) != OK:
		return
	for key in DEFAULTS:
		if file.has_section_key(SECTION, key):
			var stored: Variant = file.get_value(SECTION, key)
			# Typed against the default rather than trusted. A hand-edited file
			# with a string where a bool belongs should fall back, not crash the
			# first time something multiplies by it.
			if typeof(stored) == typeof(DEFAULTS[key]):
				_values[key] = stored


func _save() -> void:
	var file := ConfigFile.new()
	for key in DEFAULTS:
		file.set_value(SECTION, key, _values[key])
	var err := file.save(PATH)
	if err != OK:
		push_warning("settings: could not write %s (error %d)" % [PATH, err])
