extends Node

## Dev tool: checks that the park's lights actually come on, and go off again.
##
## `park_lights.gd` fails in the quiet way everything in this project fails —
## by succeeding. If the emissive materials do not load, the lights still light
## the ground and only the fittings stay dark. If the group scan runs before a
## section mounts, the new section's lights stay at zero and nothing reports it.
## If `_closing_level` gets its sense inverted the park lights up at midnight and
## goes dark at noon, and every individual number in the file still looks right.
##
## None of that is visible in a screenshot of the plaza at three in the
## afternoon, which is what most captures are. So this walks the clock through
## the day and prints what is actually on.
##
##   godot --headless --fixed-fps 60 --path . _night_test.tscn
##
## Extends `Node`, so it needs a scene root — see the note in CLAUDE.md. It also
## has to let a few frames pass after each jump: `park_lights` applies on
## `_process`, and reading the tree in the same frame as the jump reads the
## previous hour.

const MAIN := preload("res://scenes/main/main.tscn")
const Plan := preload("res://scripts/park_plan.gd")

## The hours worth asking about, and why each one is here.
const HOURS := [
	[10.0, "opening — full day, nothing should be lit"],
	[15.0, "mid-afternoon — the plaza's peak, still nothing"],
	[19.0, "the boardwalk's peak hour, sun getting low"],
	[20.5, "sunset — the lamps should be coming up"],
	[21.3, "civil twilight — everything on"],
	[21.9, "last minutes before close"],
	[22.5, "after close — features out, a few fixtures left"],
	[2.0, "the small hours — service only"],
]

var _main: Node
var _rows: Array = []


func _ready() -> void:
	_main = MAIN.instantiate()
	add_child(_main)
	_run.call_deferred()


func _run() -> void:
	# Let the world stand up and the sections adopt before asking anything.
	for i in 10:
		await get_tree().process_frame

	for row in HOURS:
		var hour: float = row[0]
		ParkClock.set_clock(int(hour), int(round((hour - floorf(hour)) * 60.0)))
		# Three frames: one for the jump's signal, one for `_process` to apply,
		# one for the change to be readable. Two was enough until it was not.
		for i in 3:
			await get_tree().process_frame
		_measure(hour, String(row[1]))

	_report()
	get_tree().quit()


func _measure(hour: float, note: String) -> void:
	var lights := get_tree().get_nodes_in_group(Plan.LIGHT_GROUP)
	var on := {Plan.LIGHT_FIXTURE: 0, Plan.LIGHT_FEATURE: 0, Plan.LIGHT_SERVICE: 0}
	var total := {Plan.LIGHT_FIXTURE: 0.0, Plan.LIGHT_FEATURE: 0.0, Plan.LIGHT_SERVICE: 0.0}
	for n in lights:
		var l := n as Light3D
		if l == null or not l.visible:
			continue
		var kind: int = l.get_meta("light_kind", Plan.LIGHT_FIXTURE)
		on[kind] += 1
		total[kind] += l.light_energy

	var bulb := load(Plan.BULB_MATERIAL) as StandardMaterial3D
	var trim := load(Plan.TRIM_MATERIAL) as StandardMaterial3D
	_rows.append({
		"hour": hour,
		"note": note,
		"count": lights.size(),
		"fixture": on[Plan.LIGHT_FIXTURE],
		"feature": on[Plan.LIGHT_FEATURE],
		"service": on[Plan.LIGHT_SERVICE],
		"energy": total[Plan.LIGHT_FIXTURE] + total[Plan.LIGHT_FEATURE]
			+ total[Plan.LIGHT_SERVICE],
		"emission": 0.0 if bulb == null else bulb.emission_energy_multiplier,
		"trim": 0.0 if trim == null else trim.emission_energy_multiplier,
	})


func _report() -> void:
	print("\n  hour   in scene   fixture  feature  service    energy  bulb  trim   note")
	print("  " + "-".repeat(98))
	for r in _rows:
		print("  %5.1f   %8d   %7d  %7d  %7d   %7.1f  %4.2f  %4.2f   %s" % [
			r["hour"], r["count"], r["fixture"], r["feature"], r["service"],
			r["energy"], r["emission"], r["trim"], r["note"]])

	# The checks worth failing on, as opposed to the numbers worth reading.
	var day: Dictionary = _rows[1]
	var night: Dictionary = _rows[4]
	var closed: Dictionary = _rows[6]
	var small: Dictionary = _rows[7]
	var bad := 0

	if day["fixture"] + day["feature"] + day["service"] > 0:
		printerr("FAIL: %d lights on at three in the afternoon"
			% [day["fixture"] + day["feature"] + day["service"]])
		bad += 1
	if not is_zero_approx(day["emission"]):
		printerr("FAIL: bulbs are emitting at three in the afternoon")
		bad += 1
	if night["fixture"] == 0 or night["feature"] == 0:
		printerr("FAIL: the park is not lit at civil twilight")
		bad += 1
	if night["emission"] <= 0.0:
		printerr("FAIL: the fittings are not lit at civil twilight — "
			+ "the materials probably did not load")
		bad += 1
	if closed["feature"] > 0:
		printerr("FAIL: %d uplights still burning after close" % closed["feature"])
		bad += 1
	if closed["fixture"] >= night["fixture"]:
		printerr("FAIL: the park did not thin out at close (%d then, %d now)"
			% [night["fixture"], closed["fixture"]])
		bad += 1
	# The trim is the cascade's silhouette and it is feature lighting made of
	# stone rather than of spotlights, so it has to follow the same rule the
	# floodlights do: on at twilight, gone at close. The fittings only dim.
	if night["trim"] <= 0.0:
		printerr("FAIL: the cascade's coping is not lit at civil twilight")
		bad += 1
	if closed["trim"] > 0.001:
		printerr("FAIL: the cascade is still presenting itself after close")
		bad += 1
	if closed["emission"] >= night["emission"]:
		printerr("FAIL: the fittings did not dim at close (%.2f then, %.2f now) — "
			% [night["emission"], closed["emission"]]
			+ "every bulb in the park is glowing over a switched-off light")
		bad += 1
	if small["service"] == 0:
		printerr("FAIL: nothing is on at two in the morning — "
			+ "the shut park should read as powered, not as a power cut")
		bad += 1

	print("")
	if bad == 0:
		print("  the park lights up and shuts down. %d lights in the plaza." % _rows[0]["count"])
	else:
		printerr("  %d checks failed" % bad)
