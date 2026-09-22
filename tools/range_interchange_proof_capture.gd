extends Node

## Side-by-side construction proof for the hardest south-range segment. The
## persistent world stays background-only; each unmounted alternative is added
## temporarily, shot from the same cameras, then hidden before the next pass.

const OUTPUT_DIR := "user://range_interchange_proof_2026_09_11_c"
const SETTLE_SECONDS := 2.0

const VARIANTS := [
	{"name": "baseline", "scene": ""},
	{"name": "clustered", "scene": "res://scenes/world/range_interchange_clustered_proof.tscn"},
	{"name": "silhouette", "scene": "res://scenes/world/range_interchange_silhouette_proof.tscn"},
]

const SHOTS := [
	{"name": "00_interchange_plan", "position": Vector3(204.0, 620.0, 322.0),
		"orthographic": 620.0},
	{"name": "01_interchange_oblique", "position": Vector3(-56.0, 170.0, 542.0),
		"target": Vector3(250.0, 24.0, 350.0), "fov": 58.0},
	{"name": "02_approach_to_overpass", "position": Vector3(132.0, 7.0, 264.0),
		"target": Vector3(285.0, 30.0, 410.0), "fov": 62.0},
	{"name": "03_highway_southbound", "position": Vector3(245.0, 15.0, 342.0),
		"target": Vector3(350.0, 35.0, 455.0), "fov": 62.0},
	{"name": "04_parking_south_arc", "position": Vector3(0.0, 1.7, 215.0),
		"target": Vector3(280.0, 45.0, 430.0), "fov": 70.0},
	{"name": "05_east_forecourt_south_arc", "position": Vector3(58.0, 1.7, -2.0),
		"target": Vector3(315.0, 48.0, 420.0), "fov": 70.0},
	{"name": "06_interchange_to_range", "position": Vector3(204.0, 14.2, 322.0),
		"target": Vector3(250.0, 55.0, 435.0), "fov": 66.0},
]


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	_hide_overlays(main)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	await get_tree().create_timer(5.0).timeout
	var camera := Camera3D.new()
	camera.name = "range_interchange_proof_camera"
	camera.far = 900.0
	add_child(camera)
	camera.current = true
	for variant in VARIANTS:
		var proof: Node = null
		if not String(variant["scene"]).is_empty():
			proof = load(variant["scene"]).instantiate()
			main.add_child(proof)
		for shot in SHOTS:
			await _capture(camera, variant["name"], shot)
		if proof != null:
			proof.queue_free()
			await get_tree().process_frame
	get_tree().quit()


func _hide_overlays(main: Node) -> void:
	for path in ["hud", "park_menu", "player"]:
		var node: Node = main.get_node_or_null(path)
		if node is CanvasItem:
			(node as CanvasItem).visible = false
		elif node is Node3D:
			(node as Node3D).hide()
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_process(false)
		crowd.set_physics_process(false)
	for guest in get_tree().get_nodes_in_group("guest"):
		guest.queue_free()


func _capture(camera: Camera3D, variant: String, shot: Dictionary) -> void:
	camera.global_position = shot["position"]
	if shot.has("orthographic"):
		camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		camera.size = float(shot["orthographic"])
		camera.global_rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	else:
		camera.projection = Camera3D.PROJECTION_PERSPECTIVE
		camera.fov = float(shot["fov"])
		camera.look_at(shot["target"], Vector3.UP)
	await get_tree().create_timer(SETTLE_SECONDS).timeout
	await RenderingServer.frame_post_draw
	var path := "%s/%s_%s.png" % [OUTPUT_DIR, variant, shot["name"]]
	var error := get_viewport().get_texture().get_image().save_png(path)
	if error != OK:
		push_error("could not save %s: %s" % [path, error_string(error)])
	else:
		print("saved ", path)
