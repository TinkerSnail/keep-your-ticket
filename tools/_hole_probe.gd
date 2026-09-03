extends Node

## Dev probe: rain rays over the whole east and dump what they hit.
##
## A hole in the ground cover cannot be photographed until you know where to
## stand, and the head-wedge of 2026-08-23 proved a ray finds in one line what
## eight frames of guessing missed. One ray per metre over the east's whole
## footprint, straight down; the dump is analysed offline, because "lower than
## its neighbours" is a cliff half the time and only the offline pass knows
## which cliffs are architecture.

const X0 := 60.0
const X1 := 127.0
const Z0 := -70.0
const Z1 := 70.0
const STEP := 1.0


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	await get_tree().create_timer(6.0).timeout
	var space := get_viewport().get_world_3d().direct_space_state
	var out := ""
	var x := X0
	while x <= X1 + 0.001:
		var z := Z0
		while z <= Z1 + 0.001:
			var q := PhysicsRayQueryParameters3D.create(
				Vector3(x, 40.0, z), Vector3(x, -6.0, z))
			var hit := space.intersect_ray(q)
			if hit.is_empty():
				out += "%.1f %.1f NONE -\n" % [x, z]
			else:
				out += "%.1f %.1f %.3f %s\n" % [x, z, hit["position"].y,
					hit["collider"].name]
			z += STEP
		x += STEP
	var f := FileAccess.open("user://hole_report.txt", FileAccess.WRITE)
	f.store_string(out + "done\n")
	f.close()
	print("hole probe done")
	get_tree().quit()
