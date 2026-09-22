extends Node

## Dev capture: the places `footprint_test` counts its 165 open faces, and the
## one sample `path_ground_test` fails when the seam's wall tolerance comes off.
## Clusters are taken from `_open_faces_all_probe`'s 40m cells. Metal/Forward+,
## so `open -n -a Godot`, never `--headless`.
## Frames go to `documentation/screenshots/open-faces-2026-09-21/`.

const OUTPUT_DIR := "res://documentation/screenshots/open-faces-2026-09-21"
const SETTLE_SECONDS := 6.0
const SHOTS := [
	# The path_ground_test sample and the cut it sits in.
	{"name": "01_highway_b_cut_from_east", "position": Vector3(372.0, 62.0, 1236.0), "target": Vector3(338.8, 38.2, 1234.8), "far": 1500.0},
	{"name": "02_highway_b_cut_from_above", "position": Vector3(339.0, 96.0, 1290.0), "target": Vector3(339.0, 38.0, 1230.0), "far": 1500.0},
	{"name": "03_highway_b_cut_along_road", "position": Vector3(338.0, 44.0, 1300.0), "target": Vector3(338.0, 39.0, 1190.0), "far": 1500.0},
	# The largest corridor cluster: 11 edges, 60.8m, cell (320, 1200).
	{"name": "04_corridor_cluster_320_1200", "position": Vector3(300.0, 110.0, 1265.0), "target": Vector3(348.0, 60.0, 1215.0), "far": 1500.0},
	{"name": "05_corridor_cluster_320_1200_low", "position": Vector3(300.0, 44.0, 1180.0), "target": Vector3(345.0, 60.0, 1220.0), "far": 1500.0},
	# 9 edges, 55.6m, cell (560, 1720).
	{"name": "06_corridor_cluster_560_1720", "position": Vector3(535.0, 100.0, 1700.0), "target": Vector3(583.0, 62.0, 1740.0), "far": 1500.0},
	# The south edge where the highway meets the city GLB's ground, y about 0.
	{"name": "07_south_edge_city_handoff", "position": Vector3(600.0, 42.0, 2500.0), "target": Vector3(620.0, 0.0, 2575.0), "far": 2000.0},
	{"name": "08_south_edge_low", "position": Vector3(560.0, 6.0, 2520.0), "target": Vector3(640.0, 0.0, 2570.0), "far": 2000.0},
	# The coast seam at x -56, 18 edges over z -276..-294.
	{"name": "09_coast_seam_x_minus56", "position": Vector3(-96.0, 26.0, -285.0), "target": Vector3(-56.0, 9.0, -285.0), "far": 800.0},
	{"name": "10_coast_seam_from_north", "position": Vector3(-60.0, 30.0, -330.0), "target": Vector3(-56.0, 9.0, -280.0), "far": 800.0},
	# Context: the whole corridor through the southern cut.
	{"name": "11_corridor_context_aerial", "position": Vector3(330.0, 360.0, 1450.0), "target": Vector3(360.0, 40.0, 1200.0), "far": 3000.0},
]


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	ParkClock.running = false
	ParkClock.set_clock(13, 0)
	for overlay_name in [&"hud", &"park_menu"]:
		var overlay := main.get_node_or_null(NodePath(String(overlay_name))) as CanvasLayer
		if overlay != null:
			overlay.visible = false
	var player := main.get_node_or_null("player") as Node3D
	if player != null:
		player.hide()
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_process(false)
		crowd.set_physics_process(false)
	for guest in get_tree().get_nodes_in_group("guest"):
		guest.queue_free()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	await get_tree().create_timer(SETTLE_SECONDS).timeout
	var camera := Camera3D.new()
	camera.name = "open_face_camera"
	camera.fov = 58.0
	add_child(camera)
	camera.current = true
	for shot in SHOTS:
		camera.far = float(shot["far"])
		camera.global_position = shot["position"]
		camera.look_at(shot["target"], Vector3.UP)
		for _frame in 10:
			await get_tree().physics_frame
		await RenderingServer.frame_post_draw
		var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
		var error := get_viewport().get_texture().get_image().save_png(path)
		if error != OK:
			push_error("could not save %s: %s" % [path, error_string(error)])
		else:
			print("saved ", path)
	print("capture complete")
	get_tree().quit()
