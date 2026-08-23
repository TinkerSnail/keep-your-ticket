extends Node

const SETTLE := 6.0
const SHOTS := [
	{"name": "a_shelf", "pos": Vector3(72.5, 7.6, -2.0), "yaw": -90.0, "pitch": 6.0},
	{"name": "b_terrace1", "pos": Vector3(86.2, 11.6, 2.0), "yaw": -140.0, "pitch": -4.0},
	{"name": "c_terrace2", "pos": Vector3(97.5, 15.6, -3.0), "yaw": -50.0, "pitch": -6.0},
	{"name": "d_court", "pos": Vector3(50.0, 1.6, -2.0), "yaw": -90.0, "pitch": 8.0},
]

func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()

func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	await get_tree().create_timer(SETTLE).timeout
	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true
	var menu := get_tree().get_first_node_in_group("park_menu")
	for shot in SHOTS:
		if menu != null and menu.is_open():
			menu.close()
			await get_tree().process_frame
		cam.global_position = shot["pos"]
		cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
		for _i in 4:
			await get_tree().physics_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("user://topo_%s.png" % shot["name"])
		print("saved ", shot["name"])
	get_tree().quit()
