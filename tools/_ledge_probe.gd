extends Node

## Dev probe: the walkable profile where the climb meets the head landing.
## Rays straight down along the two route lanes and the median, x 104..112,
## printing what was hit and at what height — the "weird ledge before the
## landing" report, measured instead of squinted at.

var _log := ""


func _say(msg: String) -> void:
	_log += msg + "\n"
	print(msg)
	var f := FileAccess.open("user://ledge_report.txt", FileAccess.WRITE)
	f.store_string(_log)
	f.close()


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	await get_tree().create_timer(6.0).timeout
	var space := get_viewport().get_world_3d().direct_space_state
	for lane in [["median", -2.0], ["ramp_n", -7.65], ["stair_s", 3.65]]:
		var name: String = lane[0]
		var z: float = lane[1]
		var row := name + ":"
		var x := 104.0
		while x <= 112.01:
			var q := PhysicsRayQueryParameters3D.create(
				Vector3(x, 30.0, z), Vector3(x, 5.0, z))
			var hit := space.intersect_ray(q)
			if hit.is_empty():
				row += " %.2f=NONE" % x
			else:
				var nm: String = hit["collider"].name
				row += " %.2f=%.3f(%s)" % [x, hit["position"].y, nm]
			x += 0.25
		_say(row)
	_say("done")
	get_tree().quit()
