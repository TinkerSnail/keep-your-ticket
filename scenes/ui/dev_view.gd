extends Control

## The dev subscreen. Debug builds only; `park_menu.gd` does not add the tab to
## an exported game, so none of this can reach a player.
##
## It exists because judging the park means seeing it at an hour and in a
## weather of your choosing, and the game proper offers neither: the clock is
## the park's and the shower is authored for 10:00. A page in the pause menu
## rather than a typed console, because the menu is already grid-navigable on a
## stick and a console needs a keyboard.
##
## Nothing here is stored. Each row reads the live node on the way in and writes
## it on the way out, so a fresh launch is the scene file's state again.

signal note_changed(note: String)

## Accept steps to the next one. Opening, the midday peak, the boardwalk's hour,
## sunset on the protected bearing, civil twilight with everything lit, close,
## the small hours.
const TIMES := [[10, 0], [13, 0], [16, 0], [19, 0], [20, 30], [21, 15], [22, 30], [2, 0]]

enum Skies { SCHEDULED, CLEAR, RAIN }
const SKY_TEXT := ["Scheduled", "Clear", "Rain"]
## The authored shower at its hardest, `weather.gd`'s 10:35 stop.
const RAIN_STATE := Vector4(0.94, 1.0, 0.90, 0.68)
## `weather.gd`'s own "none": a negative cloudiness.
const NO_OVERRIDE := Vector4(-1.0, 0.0, 0.0, 0.0)

var _list: MenuList
var _sky: int = Skies.SCHEDULED


func _ready() -> void:
	_list = MenuList.carded(self)
	_list.changed.connect(_on_changed)
	_list.activated.connect(_on_activated)
	_list.note_changed.connect(func(note: String) -> void: note_changed.emit(note))
	_rebuild()


func _on_shown() -> void:
	var weather := _weather()
	if weather != null:
		if weather.dev_override.x >= 0.0:
			_sky = Skies.RAIN
		else:
			_sky = Skies.SCHEDULED if weather.enabled else Skies.CLEAR
	_rebuild()


func _rebuild() -> void:
	var environment := _environment()
	var player := _player()
	_list.set_rows([
		{
			"id": &"weather",
			"label": "Weather",
			"kind": MenuList.Kind.ACTION if _weather() != null else MenuList.Kind.DISABLED,
			"text": SKY_TEXT[_sky],
			"note": "Scheduled is the authored day. Clear and rain hold whatever the hour.",
		},
		{
			"id": &"time",
			"label": "Time of day",
			"kind": MenuList.Kind.ACTION,
			"text": ParkClock.clock_text(),
			"note": "Steps to the next hour worth looking at. The park catches up when the menu closes.",
		},
		{
			"id": &"clock_running",
			"label": "Clock runs",
			"kind": MenuList.Kind.TOGGLE,
			"value": ParkClock.running,
			"note": "Off holds the light where it is.",
		},
		{
			"id": &"haze",
			"label": "Distance haze",
			"kind": MenuList.Kind.TOGGLE,
			"value": environment != null and environment.fog_enabled,
			"note": "The camera-distance blue. Off shows every surface's own colour.",
		},
		{
			"id": &"fly",
			"label": "Fly",
			"kind": MenuList.Kind.TOGGLE if player != null else MenuList.Kind.DISABLED,
			"value": player != null and player.flying,
			"note": "G in the park. Moves along the look and through everything; space up, C down, shift fast.",
		},
		{
			"id": &"fly_speed",
			"label": "Fly speed",
			"kind": MenuList.Kind.ACTION if player != null else MenuList.Kind.DISABLED,
			"text": "%d m/s" % int(player.fly_speed) if player != null else "",
			"note": "Shift multiplies it by five.",
		},
	])


func _on_activated(id: StringName) -> void:
	match id:
		&"weather":
			_sky = wrapi(_sky + 1, 0, SKY_TEXT.size())
			var weather := _weather()
			if weather != null:
				weather.enabled = _sky != Skies.CLEAR
				weather.dev_override = RAIN_STATE if _sky == Skies.RAIN else NO_OVERRIDE
		&"fly_speed":
			var player := _player()
			if player != null:
				var speeds := Player.FLY_SPEEDS
				player.fly_speed = speeds[wrapi(speeds.find(player.fly_speed) + 1, 0, speeds.size())]
		&"time":
			var next: Array = TIMES[0]
			var now := ParkClock.hours()
			# The first stop later today, or tomorrow's first. 02:00 sorts last in
			# the list and first on the clock, so it is compared as its own hour.
			var best := INF
			for stop in TIMES:
				var ahead := fposmod(float(stop[0]) + float(stop[1]) / 60.0 - now, 24.0)
				if ahead > 0.02 and ahead < best:
					best = ahead
					next = stop
			ParkClock.set_clock(next[0], next[1])
	_rebuild()


func _on_changed(id: StringName, value: Variant) -> void:
	match id:
		&"fly":
			var player := _player()
			if player != null:
				player.set_flying(bool(value))
		&"clock_running":
			ParkClock.running = bool(value)
		&"haze":
			var environment := _environment()
			if environment != null:
				environment.fog_enabled = bool(value)


## Found by what it can do, not by class: the weather layer is another
## session's uncommitted work, and this page has to load in a tree without it.
func _weather() -> Node:
	for node in get_tree().root.find_children("*", "Node3D", true, false):
		if "dev_override" in node and "enabled" in node:
			return node
	return null


func _player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player


func _environment() -> Environment:
	var found := get_tree().root.find_children("*", "WorldEnvironment", true, false)
	return null if found.is_empty() else (found[0] as WorldEnvironment).environment
