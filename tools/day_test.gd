extends Node

## Dev tool: checks that the crowd actually has a day.
##
## Two passes, because the schedule and the walking are different things and
## they fail differently.
##
## **The table.** Jump the clock to each hour and force an immediate sync, which
## teleports rather than walks. This measures the curves and the admit/retire
## arithmetic on their own — whether the plaza is thin at ten and full at three,
## whether the cafe disagrees with the crowd, and whether the counts settle on
## the target instead of hunting around it.
##
## **The day.** Run the clock from open to close at speed with nobody
## teleported, so every arrival and departure is walked. This measures the parts
## the table cannot see: that a group admitted at the threshold reaches the
## plaza, that a group sent home reaches the street and is put away, and that
## nobody is left standing in the world at a height they should not be.
##
## The second pass exists because of what running the game found last time. A
## harness that sets up the state it wants to measure only ever measures that
## state — the table would report a perfect day with every guest frozen at the
## gate, and never notice.
##
##   godot --headless --path . --fixed-fps 60 _day_test.tscn
##
## Wants a scene root, like `capture.gd` — write a throwaway `_day_test.tscn`
## with this as the root and delete it afterwards.

const SETTLE_FRAMES := 8

## The two windows worth walking, rather than all twelve hours. Everything the
## second pass can catch happens during a turnover, and the turnovers are the
## morning fill and the evening drain — the middle of the day is a plateau
## where almost nobody arrives or leaves and there is nothing to observe.
##
## Seconds are real seconds at the clock's own scale. Speeding the clock up to
## cover more ground would be measuring a different game: whether guests can
## walk in fast enough to keep up with the curve is one of the things in
## question, and it is only a fair question at the rate the game runs at.
const WINDOWS := [
	{"name": "the fill", "hour": 10, "minute": 0, "seconds": 900.0},
	# Runs well past ten so that closing time is inside the window and not at
	# the edge of it. The first version of this stopped eighteen game minutes
	# after close, reported PASS, and had twenty-three people still in the park.
	{"name": "the drain", "hour": 19, "minute": 30, "seconds": 1100.0},
]

## Checking 56 guests every frame for a quarter of an hour is most of the
## harness's runtime and finds nothing the same check a half-second later would
## not. Anything it is looking for persists.
const PLACEMENT_EVERY := 30

var _crowd: Node = null
var _fails: Array = []
var _seen: Dictionary = {}
var _peak := 0


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame

	_crowd = get_tree().get_first_node_in_group("crowd")
	if _crowd == null:
		print("FAIL: no crowd")
		get_tree().quit(1)
		return

	# The clock is what everything here is measuring against, so it does not get
	# to run underneath the measurement.
	ParkClock.running = false
	_peak = _crowd.get("_roster").size()

	await _table()
	for window in WINDOWS:
		await _walk_window(window)
	await _watched_gate()

	print("")
	if _fails.is_empty():
		print("PASS")
		get_tree().quit()
		return
	for f in _fails:
		print("FAIL: %s" % f)
	get_tree().quit(1)


## Deduplicated on the message rather than appended blind. A guest stuck in a
## bad place is wrong on every frame it is checked, and the first run of this
## buried the one interesting line under sixty copies of another.
func _fail(message: String) -> void:
	if _seen.has(message):
		return
	_seen[message] = true
	_fails.append(message)


# --- the table --------------------------------------------------------------


func _table() -> void:
	print("hour   wander  bench  cafe   total   of peak %d" % _peak)
	var seen_peak := 0
	var opening := 0

	for h in range(9, 24):
		ParkClock.set_clock(h, 0)
		_crowd.call("_sync_population", true)
		for i in 2:
			await get_tree().physics_frame

		var counts := _live_counts()
		var total: int = counts["wander"] + counts["bench"] + counts["cafe"]
		print("%2d:00  %5d  %5d  %5d  %6d   %3d%%" % [
			h, counts["wander"], counts["bench"], counts["cafe"],
			total, roundi(100.0 * float(total) / float(_peak))])

		if h == 10:
			opening = total
		if total > seen_peak:
			seen_peak = total

		var shut := h < 10 or h >= 22
		if shut and total != 0:
			_fail("%d:00 is outside park hours and has %d guests" % [h, total])
		if not shut and total == 0:
			_fail("%d:00 is inside park hours and has nobody" % h)

		# Every live guest stands on the ground, and every dormant one is out of
		# sight. Cheap, and it is the invariant a bad teleport breaks first.
		_check_placement(h)

	if opening >= seen_peak:
		_fail("the plaza is no busier at its peak (%d) than at opening (%d)"
			% [seen_peak, opening])
	# The whole claim is that the crowd tells the time. If the busiest hour and
	# the thinnest hour are within a third of each other, it does not.
	if float(opening) > float(seen_peak) * 0.66:
		_fail("opening (%d) is too close to the peak (%d) to read as a different hour"
			% [opening, seen_peak])


# --- the day ----------------------------------------------------------------


## Standing still and staring at the only door.
##
## Coming and going is gated on the player not looking at the way in, and the
## first version gated only the arrivals. So a player who parked facing the gate
## watched the plaza drain and never refill — eleven heads under the curve and
## still falling when the window closed, and the walked pass reported PASS
## throughout because it had no assertion about *why* a count moved.
##
## What it should do instead is hold. The hour is a target and a target can wait
## for somebody to look away.
func _watched_gate() -> void:
	ParkClock.set_clock(20, 30)
	_crowd.call("_sync_population", true)
	_face_gate()
	for i in 4:
		await get_tree().physics_frame

	if not _crowd.call("_threshold_is_watched"):
		_fail("watched gate: the player is facing the gate and the crowd disagrees")
		return

	var before: int = _crowd.get("guests").size()
	ParkClock.running = true
	var elapsed := 0.0
	while elapsed < 240.0:
		await get_tree().physics_frame
		elapsed += get_tree().root.get_process_delta_time()
		# Guests shove the player about, so the facing has to be reasserted or
		# the test wanders off the thing it is testing.
		_face_gate()
	ParkClock.running = false

	var after: int = _crowd.get("guests").size()
	print("")
	print("watched gate — %s to %s, held %d to %d" % ["8:30pm", ParkClock.clock_text(), before, after])

	# Groups already walking out when it started are allowed to finish. A drain
	# is not.
	if after < before - 8:
		_fail("watched gate: the plaza drained from %d to %d while the player watched the way in"
			% [before, after])


## Parked south of the fountain, looking down the gap. Teleported rather than
## walked, because where the player is standing is not what is being measured.
func _face_gate() -> void:
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return
	player.global_position = Vector3(-1.5, 0.2, 14.0)
	player.rotation.y = PI


func _walk_window(window: Dictionary) -> void:
	ParkClock.set_clock(window["hour"], window["minute"])
	_crowd.call("_sync_population", true)
	# Pinned facing north, away from the gate, for the same reason the geometry
	# run clears the crowd: guests jostle the idle player six metres a minute,
	# and a player that drifts into staring at the way in changes what these
	# windows are measuring. Whether the gate itself discriminates is
	# `_watched_gate`'s job, not this one's.
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player != null:
		player.global_position = Vector3(0.0, 0.2, 6.0)
		player.rotation.y = 0.0
	for i in 2:
		await get_tree().physics_frame

	var started: int = _crowd.get("guests").size()
	ParkClock.running = true

	var elapsed := 0.0
	var frame := 0
	var samples: Array = []
	var next_sample := 0.0

	while elapsed < float(window["seconds"]):
		await get_tree().physics_frame
		elapsed += get_tree().root.get_process_delta_time()
		frame += 1

		if player != null:
			player.global_position = Vector3(0.0, 0.2, 6.0)
			player.rotation.y = 0.0

		if frame % PLACEMENT_EVERY == 0:
			_check_placement(-1)

		var live: int = _crowd.get("guests").size()
		if live > _peak:
			_fail("%s: %d guests live, which is more than the cast"
				% [ParkClock.clock_text(), live])

		if elapsed >= next_sample:
			next_sample += 120.0
			samples.append([ParkClock.clock_text(), live, _leaving(), _wanted(),
				_state_counts(), _crowd.call("_threshold_is_watched")])

	ParkClock.running = false
	var ended: int = _crowd.get("guests").size()

	print("")
	print("%s — walked, not teleported (%d to %d):" % [window["name"], started, ended])
	for s in samples:
		print("  %-8s live %-3d wanted %-3d walking out %-3d groups out/in/leaving %s  watched %s"
			% [s[0], s[1], s[3], s[2], s[4], s[5]])

	# The whole reason for this pass. If the count never moved, either nothing
	# was admitted or nothing completed, and the table would have reported a
	# perfect day either way.
	if ended == started:
		_fail("%s: the headcount did not move at all across the window"
			% window["name"])

	# Groups mid-departure at the end of a window are fine — one may have been
	# retired seconds before it closed. A pile of them is not: it means the walk
	# out is not completing, and the sweep is only clearing them on patience.
	if _leaving() > 3:
		_fail("%s: %d groups still walking out when the window closed"
			% [window["name"], _leaving()])

	# Ten at night and the park is empty. This is the one assertion here that is
	# about the game rather than about the machinery: after close the player is
	# alone in the plaza, and everything `documentation/night.md` describes
	# depends on that being true without anybody switching the crowd off.
	if not ParkClock.is_open() and ended > 0:
		_fail("%s: the park shut and %d guests are still in it"
			% [window["name"], ended])


## What the hour is asking for, totalled across the three populations. Printed
## next to what is actually standing there, because "the count went down" and
## "the count went down when it was supposed to" are different claims and the
## first run of this could only make the first one.
func _wanted() -> int:
	var total := 0
	var by_kind: Dictionary = _crowd.get("_visits_by_kind")
	for kind in by_kind:
		var peak := 0
		for visit in by_kind[kind]:
			peak += visit["members"].size()
		total += _crowd.call("_target_for", kind, peak)
	return total


func _state_counts() -> String:
	var out := 0
	var inside := 0
	var leaving := 0
	for visit in _crowd.get("_visits"):
		match visit["state"]:
			0: out += 1
			1: inside += 1
			2: leaving += 1
	return "%d/%d/%d" % [out, inside, leaving]


func _leaving() -> int:
	var n := 0
	for visit in _crowd.get("_visits"):
		if visit["state"] == 2:  # Visit.LEAVING
			n += 1
	return n


# --- invariants -------------------------------------------------------------


func _check_placement(hour: int) -> void:
	var when := "%d:00" % hour if hour >= 0 else ParkClock.clock_text()
	for guest in get_tree().get_nodes_in_group("guest"):
		var live: bool = guest.is_live()
		var y: float = guest.global_position.y
		if live and absf(y) > 0.05:
			_fail("%s: %s is live at y=%.2f" % [when, guest.name, y])
			return
		if not live and guest.visible:
			_fail("%s: %s is dormant and visible" % [when, guest.name])
			return
		if not live and y > -100.0:
			_fail("%s: %s is dormant at y=%.2f, not parked" % [when, guest.name, y])
			return


func _live_counts() -> Dictionary:
	var counts := {"wander": 0, "bench": 0, "cafe": 0}
	for guest in _crowd.get("guests"):
		var kind: String = guest.group_kind
		counts[kind] = counts.get(kind, 0) + 1
	return counts
