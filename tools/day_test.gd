extends Node

## The park's layout, so the poses and floors below cannot drift from it again.
const Plan := preload("res://scripts/park_plan.gd")

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

## How far off the floor a live guest may be, on a section that has relief.
##
## **This is `climb_test.TOLERANCE` and it has to stay that number.** The two
## tools ask overlapping questions and only one of them asks the tight version:
## `climb_test` reads the floor off the crowd's own graph per guest and knows
## what a follower on a slope is allowed to be, and this only wants to know that
## nobody is live at the dormant height or hanging over the park. Asserting
## something *stricter* here than the tool that measures it properly is how you
## get a red line that means nothing.
##
## The terraces found it immediately: a guest 0.14m under the forecourt during
## the drain, which is a fifth of what `climb_test` accepts and passes there.
##
## Flat sections keep 0.05 — see `FLAT_SLACK` — because on one level a live
## guest really should be at the floor, and that check has caught things.
const RELIEF_SLACK := 0.75

## And the tight one, for a section that is a single plane.
const FLAT_SLACK := 0.05

## The two windows worth walking, rather than all twelve hours. Everything the
## second pass can catch happens during a turnover, and the turnovers are the
## morning fill and the evening drain — the middle of the day is a plateau
## where almost nobody arrives or leaves and there is nothing to observe.
##
## Seconds are real seconds at the clock's own scale. Speeding the clock up to
## cover more ground would be measuring a different game: whether guests can
## walk in fast enough to keep up with the curve is one of the things in
## question, and it is only a fair question at the rate the game runs at.
##
## Per section, because a section's day is its own — see `crowd.gd`'s curve
## exports. The plaza fills at ten and drains at ten; the boardwalk is still
## filling at seven in the evening, so running the plaza's windows against it
## would measure a plateau at one end and a plateau at the other and call it a
## day.
##
## The live floor band is measured from each crowd's own graph when that crowd
## is selected. It used to be copied into this table as `floor_y` and
## `floor_rise`; the east hill grew from 12m to 20m and left the test measuring
## an old park. The band is still deliberately broad: this check catches a live
## guest at the dormant height or hanging outside the district's entire vertical
## range. `climb_test` asks the tighter per-guest question against the particular
## path under their feet. `RELIEF_SLACK` is where that hand-off is written down.
##
## `idle` is where the player is parked so they are not staring at the way in,
## and `watch` is where they are parked so that they are.
const SECTIONS := [
	{
		"id": &"plaza",
		"idle": {"at": Vector3(0.0, 0.2, 6.0), "yaw": 0.0},
		"watch": {"at": Vector3(-1.5, 0.2, 14.0), "yaw": PI},
		"windows": [
			{"name": "the fill", "hour": 10, "minute": 0, "seconds": 900.0},
			# Runs well past ten so that closing time is inside the window and not
			# at the edge of it. The first version of this stopped eighteen game
			# minutes after close, reported PASS, and had twenty-three people
			# still in the park.
			{"name": "the drain", "hour": 19, "minute": 30, "seconds": 1100.0},
		],
	},
	{
		"id": &"boardwalk",
		# **Read off the plan rather than typed.** All three of these were
		# literals from the day the boardwalk was built, and all three went stale
		# together on 2026-08-14b when the drop was halved to 3m and the strip
		# moved sixteen metres west: the floor was still −6, so *every live guest
		# down here failed the placement check on every sampled frame*, and the
		# two poses were parked inland of the frontage. The whole boardwalk phase
		# had been failing since that afternoon, which is a test that had stopped
		# being able to say anything about the section it names.
		# On the promenade at the mouth of the alley, facing the water — which is
		# where a player actually stands and is a wall away from the back lane.
		"idle": {"at": Vector3(-94.0, Plan.SHORE_TOP + 0.2, Plan.ALLEY_Z), "yaw": PI * 0.5},
		# Down the back lane, looking at the way in — which is `lane_s`, at the
		# south end of the lane, with off-stage further south again.
		"watch": {"at": Vector3(Plan.BACK_LANE_X, Plan.SHORE_TOP + 0.2, 8.0), "yaw": PI},
		"windows": [
			# The strip's turnover is late. Nothing much moves before four, and
			# the drain is a single hour after the sun goes down.
			{"name": "the fill", "hour": 16, "minute": 30, "seconds": 900.0},
			{"name": "the drain", "hour": 20, "minute": 30, "seconds": 1100.0},
		],
	},
	{
		# **Added 2026-08-20, two days after the section shipped with a crowd.**
		# `SECTIONS` had two entries and `CLAUDE.md` described this tool as
		# checking "each section's day, section by section", which had been
		# describing two of three since the third arrived. Nothing had ever
		# measured the hillside.
		"id": &"terraces",
		# The court, on the gate's own axis, which is where `EAST_ARRIVE_OUT`
		# puts the player crossing east and therefore ground that `section_test`
		# already lands a body on. Both poses stand in the same place and differ
		# only in facing, because the one thing being varied is whether the way
		# in is in shot — and the way in here is a 6m opening on one axis rather
		# than a gap you can be beside.
		#
		# **x 55 and not 52, because `e_court` is at 52.** Parking the player on
		# a graph node puts a body in the doorway: every guest routing through
		# the court has to squeeze past them, in a court six metres wide, for
		# the whole window. It is a bad standpoint for a pose whose entire job
		# is to be out of the way, whatever else it does.
		#
		# It is also the one thing I changed that might explain a `guest_08 is
		# live at y=-0.14` this test threw on its first terraces run. Might.
		# Sweeping every frame of the whole drain afterwards found nobody below
		# the floor at all, so the reading is unreproduced rather than
		# explained, and 0.14m is a fifth of what `climb_test` accepts and
		# passes on this section. Removed as a plausible contributor, not fixed
		# as a known cause — and said that way round on purpose.
		"idle": {"at": Vector3(55.0, 0.2, Plan.ARCH_AT.y), "yaw": -PI * 0.5},
		"watch": {"at": Vector3(55.0, 0.2, Plan.ARCH_AT.y), "yaw": PI * 0.5},
		# **The plaza's windows, because these are the plaza's curves.**
		# `_build_terraces` sets no `wander_day`, `cafe_day`, `bench_day` or
		# `flow_day`, so `crowd.gd`'s exports keep their plaza defaults — unlike
		# the boardwalk, which overrides all four. That is defensible rather
		# than an oversight: everybody up here walked out of the plaza and the
		# hillside has nothing on it yet to give it a rhythm of its own. But it
		# is inherited rather than chosen, and the day this section gets kiosks
		# in its bays is the day these windows want re-picking with the curves.
		"windows": [
			{"name": "the fill", "hour": 10, "minute": 0, "seconds": 900.0},
			{"name": "the drain", "hour": 19, "minute": 30, "seconds": 1100.0},
		],
	},
]

## Checking 56 guests every frame for a quarter of an hour is most of the
## harness's runtime and finds nothing the same check a half-second later would
## not. Anything it is looking for persists.
const PLACEMENT_EVERY := 30

var _crowd: Node = null
var _fails: Array = []
var _seen: Dictionary = {}
var _peak := 0
## Whichever section is being measured. Everything below that used to name the
## plaza now reads this.
var _section: Dictionary = {}
## Global vertical range of the selected crowd's actual walk graph. Derived at
## measurement time so terrain and graph edits cannot leave this harness testing
## an obsolete copied height.
var _floor_min := 0.0
var _floor_max := 0.0


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame

	# The clock is what everything here is measuring against, so it does not get
	# to run underneath the measurement.
	ParkClock.running = false

	for section in SECTIONS:
		await _measure(section)

	print("")
	if _fails.is_empty():
		print("PASS")
		get_tree().quit()
		return
	for f in _fails:
		print("FAIL: %s" % f)
	get_tree().quit(1)


func _measure(section: Dictionary) -> void:
	_section = section
	var id: StringName = section["id"]

	_crowd = ParkSections.current_crowd(id)
	if _crowd == null:
		_fail("%s: no crowd in the tree" % id)
		return
	_measure_floor_band()

	print("")
	print("=== %s ===" % ParkSections.section_name(id))
	_peak = _crowd.get("_roster").size()

	await _table()
	for window in section["windows"]:
		await _walk_window(window)
	await _watched_gate()


func _measure_floor_band() -> void:
	var graph: PackedVector3Array = _crowd.get("nodes")
	if graph.is_empty():
		_floor_min = 0.0
		_floor_max = 0.0
		return

	_floor_min = INF
	_floor_max = -INF
	var crowd_3d := _crowd as Node3D
	for point in graph:
		var y := crowd_3d.to_global(point).y
		_floor_min = minf(_floor_min, y)
		_floor_max = maxf(_floor_max, y)


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
		_fail("%s is no busier at its peak (%d) than at opening (%d)"
			% [_section["id"], seen_peak, opening])
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


## Parked where the section's way in is in shot. Teleported rather than walked,
## because where the player is standing is not what is being measured.
func _face_gate() -> void:
	_pose(_section["watch"])


func _pose(spot: Dictionary) -> void:
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return
	player.global_position = spot["at"]
	player.rotation.y = spot["yaw"]


func _walk_window(window: Dictionary) -> void:
	ParkClock.set_clock(window["hour"], window["minute"])
	_crowd.call("_sync_population", true)
	# Pinned facing north, away from the gate, for the same reason the geometry
	# run clears the crowd: guests jostle the idle player six metres a minute,
	# and a player that drifts into staring at the way in changes what these
	# windows are measuring. Whether the gate itself discriminates is
	# `_watched_gate`'s job, not this one's.
	var player := get_tree().get_first_node_in_group("player") as Node3D
	_pose(_section["idle"])
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

		_pose(_section["idle"])

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
	var relief := _floor_max - _floor_min
	var slack := RELIEF_SLACK if relief > 0.1 else FLAT_SLACK
	for guest in get_tree().get_nodes_in_group("guest"):
		if not _crowd.is_ancestor_of(guest):
			continue
		var live: bool = guest.is_live()
		var y: float = guest.global_position.y
		if live and (y < _floor_min - slack or y > _floor_max + slack):
			_fail("%s: %s is live at y=%.2f, outside %.2f..%.2f"
				% [when, guest.name, y, _floor_min - slack, _floor_max + slack])
			return
		if not live and guest.visible:
			_fail("%s: %s is dormant and visible" % [when, guest.name])
			return
		if not live and y > _floor_min - 100.0:
			_fail("%s: %s is dormant at y=%.2f, not parked" % [when, guest.name, y])
			return


func _live_counts() -> Dictionary:
	var counts := {"wander": 0, "bench": 0, "cafe": 0}
	for guest in _crowd.get("guests"):
		var kind: String = guest.group_kind
		counts[kind] = counts.get(kind, 0) + 1
	return counts
