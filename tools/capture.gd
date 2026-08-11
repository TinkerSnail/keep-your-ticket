extends Node

## Dev tool: loads the main scene, poses the player at a list of vantages, and
## saves viewport captures so the plaza can be inspected without playing it.
##
## Each entry takes a yaw and pitch in degrees, and optionally a position to
## teleport to. Without a position the player stays where it spawned.

const SHOTS := [
	{"name": "spawn", "yaw": 0.0, "pitch": 0.0},
	{"name": "east", "yaw": -70.0, "pitch": -4.0},
	{"name": "west", "yaw": 80.0, "pitch": -4.0},
	{"name": "back_south", "yaw": 180.0, "pitch": -4.0},
	{"name": "ladder", "yaw": -95.0, "pitch": 6.0, "pos": Vector3(15.0, 0.2, 3.5)},
	{"name": "bench_close", "yaw": 150.0, "pitch": -12.0, "pos": Vector3(4.0, 0.2, 1.0)},
	{"name": "cafe_close", "yaw": -60.0, "pitch": -8.0, "pos": Vector3(10.0, 0.2, 6.0)},
	{"name": "aframe_close", "yaw": 8.0, "pitch": -10.0, "pos": Vector3(2.0, 0.2, 14.0)},
	{"name": "balloons", "yaw": -20.0, "pitch": -6.0, "pos": Vector3(4.5, 0.2, 9.5)},
	{"name": "balloon_ground", "yaw": -144.0, "pitch": -12.0, "pos": Vector3(-1.5, 0.2, 27.5)},
]


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run(main)


func _run(main: Node) -> void:
	await get_tree().create_timer(1.0).timeout

	var player: Node3D = main.get_node_or_null("player")
	if player == null:
		push_error("no player in main scene")
		get_tree().quit(1)
		return
	var head: Node3D = player.get_node("head")

	for shot in SHOTS:
		if shot.has("pos"):
			player.global_position = shot["pos"]
		player.rotation.y = deg_to_rad(shot["yaw"])
		head.rotation.x = deg_to_rad(shot["pitch"])
		# let the body settle onto the floor before reading the frame
		for _i in 3:
			await get_tree().physics_frame
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		var path := "user://shot_%s.png" % shot["name"]
		img.save_png(path)
		print("saved ", path)

	get_tree().quit()
