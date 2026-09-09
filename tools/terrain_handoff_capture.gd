extends Node

## Standing visual proof for the four editor-owned drainage folds and the
## protected Terraced Fountain boundary after the 2026-09-09 map handoff.

const OUTPUT_DIR := "res://documentation/screenshots/terrain-handoff-2026-09-09"
const SETTLE_SECONDS := 7.0

const SHOTS := [
	{
		"name": "00_d3_fairground",
		"position": Vector3(-112.0, 70.0, 255.0),
		"target": Vector3(-18.0, -0.3, 174.45),
	},
	{
		"name": "01_d4_kiddieland",
		"position": Vector3(24.0, 72.0, 252.0),
		"target": Vector3(105.55, 2.93, 162.05),
	},
	{
		"name": "02_d5_outer_kiddieland",
		"position": Vector3(258.0, 68.0, 226.0),
		"target": Vector3(170.8, 3.63, 145.0),
	},
	{
		"name": "03_d6_grove",
		"position": Vector3(138.0, 72.0, -292.0),
		"target": Vector3(53.75, -0.5, -200.33),
	},
	{
		"name": "04_nt2_localized_boundary",
		"position": Vector3(218.0, 96.0, 92.0),
		"target": Vector3(86.0, 8.0, 0.0),
	},
]


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)

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
	camera.name = "terrain_handoff_camera"
	camera.far = 650.0
	camera.fov = 48.0
	add_child(camera)
	camera.current = true
	for shot in SHOTS:
		camera.global_position = shot["position"]
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
	get_tree().quit()
