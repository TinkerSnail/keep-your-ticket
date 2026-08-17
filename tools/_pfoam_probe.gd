extends Node

## Dev probe: the plaza fountain's froth, at the waterline.
##
## Shot low and close on purpose. `_foam_patch`'s float was invisible from
## standing height for two days because a disc 3cm above water is only 3cm wrong
## when you can see the water edge-on — from above it is just a patch.

const SHOTS := [
	# The fountain is at the world origin, pool radius 8.26, water top 0.30 and the
	# froth ring at 4.03. Low and looking in across the surface, which is the only
	# angle a 3cm float shows from: seen from above it is just a patch.
	{"name": "a_across", "pos": Vector3(7.0, 0.62, 0.0), "yaw": 90.0, "pitch": -4.0},
	{"name": "b_jets", "pos": Vector3(5.2, 0.55, 5.2), "yaw": 45.0, "pitch": -3.0},
	{"name": "c_ring", "pos": Vector3(6.0, 1.10, 3.0), "yaw": 63.0, "pitch": -14.0},
	# Back off the kerb for the whole object, which is what the submerged lamps
	# have to read at: nobody stands in the pool.
	{"name": "d_whole", "pos": Vector3(15.0, 2.6, 9.0), "yaw": 59.0, "pitch": -6.0},
	{"name": "e_across", "pos": Vector3(0.0, 1.9, 16.0), "yaw": 180.0, "pitch": -3.0},
]


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	await get_tree().create_timer(5.0).timeout
	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true
	for shot in SHOTS:
		await _shoot(cam, shot, "day")
	# And after dark, which is the half the submerged lamps exist for.
	ParkClock.set_clock(21, 15)
	await get_tree().create_timer(3.0).timeout
	for shot in SHOTS:
		await _shoot(cam, shot, "night")
	get_tree().quit()


func _shoot(cam: Camera3D, shot: Dictionary, when: String) -> void:
	cam.global_position = shot["pos"]
	cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(
		"user://pfoam_%s_%s.png" % [shot["name"], when])
	print("saved ", shot["name"], " ", when)
