extends Node

## Dev tool: what the crowd costs per frame, hour by hour.
##
## Exists to answer one question before any of it is designed against — how many
## guests the plain path holds before it needs tiering. `documentation` has the
## estimate that a real peak for a plaza this size is somewhere between 320 and
## 640 people against a cast of 56, so the number that matters is where the
## curve stops being flat, not what it reads at any one hour.
##
## **Headless, so this is simulation cost and nothing else.** No rendering, no
## draw calls, no shadow passes, no skinning. What it measures is the part that
## scales with how many guests are *thinking* — the attention stacks, the
## separation, the alert scan, the path following — which is the part a tiering
## scheme would move off the critical path. It says nothing about what 150
## bodies cost to draw, and that number will matter later and is not this one.
##
## The reading is wall clock between consecutive physics frames — the whole
## frame, engine included. `Performance`'s own monitors were tried first and
## reported 0.000 for two hours running and then an identical 59.866 for two
## more, which is a stale value rather than a measurement.
##
## Whole-frame is also the honest unit. The budget is shared, nothing here is
## the crowd's alone, and **what the crowd costs is the difference between two
## cast sizes** rather than any figure a single monitor hands over. Read the
## rows against each other, not on their own.

## Hours worth reading. Opening, the climb, the peak, and a real evening — the
## same shape `crowd.gd`'s curves are built on.
const HOURS := [10, 12, 13, 15, 18, 20]

## Long enough for the population to settle after the clock is jumped. A jump
## re-places rather than walks, so this is short on purpose.
const SETTLE_FRAMES := 90

## Sampled per hour. At 60fps fixed this is four seconds of physics per reading,
## which is enough to average out a stray allocation without the run taking all
## afternoon.
const SAMPLE_FRAMES := 240

var _crowd: Node = null
var _hour := 0
var _frames := 0
var _settling := true
var _phys: Array[float] = []
var _last_us := 0
var _rows: Array = []


## Builds its own tree rather than instancing `main.tscn`: the plaza, the crowd
## and the player, and nothing else.
##
## Partly because the HUD, the menu and the sun are not crowd cost and only add
## noise to the reading. Mostly because this tool has to be runnable while
## somebody else is halfway through editing the interface — `main.tscn` failing
## to load took the measurement down with it once, and the number being measured
## had nothing to do with the file that broke.
##
## The player is placed where `main.tscn` spawns them, because they are not
## inert: the crowd watches them once per frame on everyone's behalf, and guests
## give them a berth. A harness with no player measures a cheaper crowd than the
## real one.
func _ready() -> void:
	var host := Node3D.new()
	host.name = "sections"
	host.add_to_group("section_host")
	add_child(host)
	host.add_child(load("res://scenes/world/plaza.tscn").instantiate())
	host.add_child(load("res://scenes/world/plaza_crowd.tscn").instantiate())

	var player := load("res://scenes/player/player.tscn").instantiate() as Node3D
	player.position = Vector3(0.0, 0.2, 16.0)
	add_child(player)

	for i in 8:
		await get_tree().physics_frame

	_crowd = get_tree().get_first_node_in_group("crowd")
	if _crowd == null:
		print("perf: no crowd in the tree")
		get_tree().quit(1)
		return

	print("cast: %d guests" % _cast_size())
	_begin(0)


func _cast_size() -> int:
	# The whole cast, standing or dormant, which is what the generator produced.
	var n := 0
	for child in _crowd.get_children():
		if child is AnimatableBody3D:
			n += 1
	return n


func _begin(index: int) -> void:
	_hour = index
	_frames = 0
	_settling = true
	_phys.clear()
	_last_us = 0
	ParkClock.set_clock(HOURS[index], 0)
	# The clock has to stop, or the hour drifts under the sample and the reading
	# belongs to no particular time of day.
	ParkClock.running = false


func _physics_process(_delta: float) -> void:
	if _hour >= HOURS.size():
		return

	_frames += 1
	if _settling:
		if _frames >= SETTLE_FRAMES:
			_settling = false
			_frames = 0
		return

	# Wall clock between consecutive physics frames, not `Performance`'s
	# monitors. Those reported 0.000 for two hours running and then the same
	# 59.866 for two more — a stale reading, not a measurement. This is the whole
	# frame including the engine, which is also the honest number: the budget is
	# shared, and what the crowd costs is the difference between two cast sizes
	# rather than a figure any one monitor reports.
	var now := Time.get_ticks_usec()
	if _last_us > 0:
		_phys.append(float(now - _last_us) / 1000.0)
	_last_us = now

	if _frames < SAMPLE_FRAMES:
		return

	_rows.append({
		"hour": HOURS[_hour],
		"live": _live(),
		"phys": _mean(_phys),
		"phys_max": _max(_phys),
		"proc": _median(_phys),
	})

	if _hour + 1 < HOURS.size():
		_begin(_hour + 1)
	else:
		_hour = HOURS.size()
		_report()


## Only the people actually in the park. `crowd.guests` is the live list the
## per-frame work runs off, which is the number the cost should track.
func _live() -> int:
	var live: Variant = _crowd.get("guests")
	return (live as Array).size() if live != null else -1


func _mean(a: Array[float]) -> float:
	if a.is_empty():
		return 0.0
	var total := 0.0
	for v in a:
		total += v
	return total / float(a.size())


func _max(a: Array[float]) -> float:
	var top := 0.0
	for v in a:
		top = maxf(top, v)
	return top


func _median(a: Array[float]) -> float:
	if a.is_empty():
		return 0.0
	var b := a.duplicate()
	b.sort()
	return b[b.size() / 2]


func _report() -> void:
	print("--- crowd cost, simulation only (headless, no rendering) ---")
	print("hour   live   mean ms   peak ms   median ms   us/guest")
	for r in _rows:
		var live: int = r["live"]
		var per: float = (float(r["phys"]) * 1000.0 / float(live)) if live > 0 else 0.0
		print("%02d:00  %4d   %8.3f   %7.3f   %9.3f   %7.1f"
			% [r["hour"], r["live"], r["phys"], r["phys_max"], r["proc"], per])
	# The budget, said out loud so the table means something. 60Hz physics is
	# 16.67ms a frame for everything — crowd, player, CSG collision, the lot.
	print("budget: 16.67 ms per physics frame at 60Hz, shared with everything else")
	get_tree().quit(0)
