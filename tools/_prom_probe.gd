extends Node

## Dev probe: rain rays over the promontory walk and dump what they hit,
## beside the plan's own promontory height at the same points. The ground
## contact test reported the walk floating half a metre over the coast mesh on
## one stretch with nothing in the arithmetic to explain it; a dump on a
## one-metre grid says whether the mesh is lower than the function it was
## built from, or the function has a step the stations straddle.

const X0 := -160.0
const X1 := -40.0
const Z0 := -290.0
const Z1 := -160.0
const STEP := 1.0


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	await get_tree().create_timer(4.0).timeout
	var space := get_viewport().get_world_3d().direct_space_state
	var out := ""
	var world := get_tree().root.find_child("park_world", true, false)
	var walk: Node = world.find_child("P1_public_access", true, false)
	if walk != null:
		for p in walk.get_meta("points", PackedVector3Array()):
			out += "STATION %.2f %.2f %.2f %.3f\n" % [p.x, p.y, p.z,
				ParkPlan.promontory_y(Vector2(p.x, p.z))]
	var x := X0
	while x <= X1 + 0.001:
		var z := Z0
		while z <= Z1 + 0.001:
			var q := PhysicsRayQueryParameters3D.create(
				Vector3(x, 60.0, z), Vector3(x, -20.0, z), 1)
			var hit := space.intersect_ray(q)
			var st := ParkPlan.promontory_station(Vector2(x, z))
			if hit.is_empty():
				out += "%.1f %.1f NONE - %.3f %.2f %.2f %.2f\n" % [x, z,
					ParkPlan.promontory_y(Vector2(x, z)), ParkPlan.coast_inland(Vector2(x, z)),
					st.x, st.y]
			else:
				out += "%.1f %.1f %.3f %s %.3f %.2f %.2f %.2f\n" % [x, z, hit["position"].y,
					hit["collider"].name, ParkPlan.promontory_y(Vector2(x, z)),
					ParkPlan.coast_inland(Vector2(x, z)), st.x, st.y]
			z += STEP
		x += STEP
	var f := FileAccess.open("user://prom_report.txt", FileAccess.WRITE)
	f.store_string(out + "done\n")
	f.close()
	print("prom probe done")
	get_tree().quit()
