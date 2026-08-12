extends Node

## The park's clock, autoloaded as `ParkClock`.
##
## Anything that happens on a schedule reads from here — the sun's arc, guest
## routines, the parade turning the corner at three, the gap between handing in
## film and the print reaching the wall. Time is held as seconds since midnight
## so that arithmetic across an hour boundary is ordinary subtraction, and it
## wraps at midnight rather than accumulating a date.
##
## Nothing here is a meter. It tells the time, which is what the player has to
## learn the park by, and it never counts anything up or down.

## Emitted once per whole game minute.
signal minute_passed(hour: int, minute: int)

## Emitted on the hour, after `minute_passed` for :00.
signal hour_passed(hour: int)

signal park_opened
signal park_closed

## The clock was jumped rather than run. Anything that catches up to the time by
## degrees — the crowd walking guests in through the gate — has to be told, or a
## dev tool that skips to eight in the evening gets the eight o'clock sun over
## the ten o'clock crowd, still filing in.
signal clock_jumped

const MINUTE := 60.0
const HOUR := 3600.0
const DAY := 86400.0

## The shift. Gates open at ten and the last guest is walked out at ten.
const OPEN_HOUR := 10.0
const CLOSE_HOUR := 22.0

## Game seconds per real second. Twelve puts the whole open day into an hour of
## play. This is the one number in the schedule chosen by feel rather than by
## the sky, and it is the one expected to move.
const DEFAULT_TIME_SCALE := 12.0

## Where a session begins. Opening, so the player watches the day arrive rather
## than walking in halfway through it.
const START_HOUR := OPEN_HOUR

var time_scale := DEFAULT_TIME_SCALE
var running := true

var seconds: float = START_HOUR * HOUR

var _last_minute := -1
var _was_open := false


func _ready() -> void:
	_last_minute = int(seconds / MINUTE)
	_was_open = is_open()


func _process(delta: float) -> void:
	if not running:
		return
	advance(delta * time_scale)


## Push the clock forward by a number of game seconds. Used by `_process`, and
## directly by the dev tools to jump to a time of day.
func advance(game_seconds: float) -> void:
	if game_seconds <= 0.0:
		return
	seconds = fposmod(seconds + game_seconds, DAY)
	_emit_crossings()


## Jump to a time of day without firing the signals for everything in between.
## Dev tooling only — the game itself has no way to skip time.
func set_clock(hour_of_day: int, minute_of_hour: int = 0) -> void:
	seconds = fposmod(hour_of_day * HOUR + minute_of_hour * MINUTE, DAY)
	_last_minute = int(seconds / MINUTE)
	_was_open = is_open()
	clock_jumped.emit()


func hour() -> int:
	return int(seconds / HOUR)


func minute() -> int:
	return int(fmod(seconds, HOUR) / MINUTE)


## Time of day as a fractional hour, which is what the sun wants.
func hours() -> float:
	return seconds / HOUR


func is_open() -> bool:
	var h := hours()
	return h >= OPEN_HOUR and h < CLOSE_HOUR


## Twelve-hour, no leading zero, the way a person says it.
func clock_text() -> String:
	var h := hour()
	var suffix := "am" if h < 12 else "pm"
	var display := h % 12
	if display == 0:
		display = 12
	return "%d:%02d%s" % [display, minute(), suffix]


func _emit_crossings() -> void:
	var m := int(seconds / MINUTE)
	if m != _last_minute:
		_last_minute = m
		var h := hour()
		minute_passed.emit(h, minute())
		if minute() == 0:
			hour_passed.emit(h)

	var open_now := is_open()
	if open_now != _was_open:
		_was_open = open_now
		if open_now:
			park_opened.emit()
		else:
			park_closed.emit()
