extends Node

## Standing visual proof for the developed park inside its expanded surrounding
## geography. These views use the real persistent park scene; nothing is
## replaced with the planning overlay.

const OUTPUT_DIR := "user://world_expansion_checkpoint_2026_09_03"
const SETTLE_SECONDS := 7.0

const SHOTS := [
	{
		"name": "00_plan_aerial",
		"position": Vector3(0.0, 520.0, -5.0),
		"target": Vector3(0.0, 0.0, -5.0),
		"orthographic": 700.0,
	},
	{
		"name": "01_south_oblique",
		"position": Vector3(-315.0, 330.0, 350.0),
		"target": Vector3(-2.0, 0.0, -10.0),
		"fov": 52.0,
	},
	{
		"name": "02_arrival_axis",
		"position": Vector3(0.0, 150.0, 312.0),
		"target": Vector3(0.0, 0.0, 72.0),
		"fov": 50.0,
	},
	{
		"name": "03_headland_axis",
		"position": Vector3(-78.0, 250.0, -338.0),
		"target": Vector3(-12.0, 0.0, -48.0),
		"fov": 51.0,
	},
	{
		"name": "04_west_return_and_cascade",
		"position": Vector3(-286.0, 190.0, 92.0),
		"target": Vector3(-48.0, -1.0, 0.0),
		"fov": 48.0,
	},
	{
		"name": "05_east_reserve_and_terraces",
		"position": Vector3(322.0, 235.0, 92.0),
		"target": Vector3(72.0, 8.0, -12.0),
		"fov": 49.0,
	},
	{
		"name": "06_plaza_branch_plan",
		"position": Vector3(0.0, 190.0, 48.0),
		"target": Vector3(0.0, 0.0, 48.0),
		"orthographic": 205.0,
	},
	{
		"name": "07_coastal_and_fairground",
		"position": Vector3(-245.0, 175.0, 190.0),
		"target": Vector3(-48.0, -1.0, 74.0),
		"fov": 48.0,
	},
	{
		"name": "08_family_circuit",
		"position": Vector3(260.0, 180.0, 190.0),
		"target": Vector3(72.0, 3.0, 72.0),
		"fov": 48.0,
	},
	{
		"name": "09_northern_ride_circuit",
		"position": Vector3(10.0, 255.0, -335.0),
		"target": Vector3(45.0, 4.0, -92.0),
		"fov": 50.0,
	},
]


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)

	# The proof is about the world assembly. UI, player body and crowds would be
	# arbitrary specks in the high views and can hide a path edge in the closer
	# ones, so keep the park and its moving rides and remove only those overlays.
	var hud: CanvasLayer = main.get_node_or_null("hud") as CanvasLayer
	if hud != null:
		hud.visible = false
	var menu: CanvasLayer = main.get_node_or_null("park_menu") as CanvasLayer
	if menu != null:
		menu.visible = false
	var player: Node3D = main.get_node_or_null("player") as Node3D
	if player != null:
		player.hide()
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_process(false)
		crowd.set_physics_process(false)
	for guest in get_tree().get_nodes_in_group("guest"):
		guest.queue_free()

	var sun: DirectionalLight3D = main.get_node_or_null("sun") as DirectionalLight3D
	if sun != null:
		sun.directional_shadow_max_distance = 800.0

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))
	await get_tree().create_timer(SETTLE_SECONDS).timeout

	var camera := Camera3D.new()
	camera.name = "footprint_camera"
	camera.far = 1800.0
	add_child(camera)
	camera.current = true

	for shot in SHOTS:
		await _capture(camera, shot)
	get_tree().quit()


func _capture(camera: Camera3D, shot: Dictionary) -> void:
	camera.global_position = shot["position"]
	if shot.has("orthographic"):
		camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		camera.size = shot["orthographic"]
		# Fixed rotation instead of `look_at`: straight down makes the requested
		# up vector singular. This keeps north at the top, parking at the bottom
		# and the Boardwalk/water at the left like the reference map.
		camera.global_rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	else:
		camera.projection = Camera3D.PROJECTION_PERSPECTIVE
		camera.fov = shot["fov"]
		camera.look_at(shot["target"], Vector3.UP)
	for _frame in 8:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "%s/%s.png" % [OUTPUT_DIR, shot["name"]]
	var error := get_viewport().get_texture().get_image().save_png(path)
	if error != OK:
		push_error("could not save %s: %s" % [path, error_string(error)])
	else:
		print("saved ", path)
