extends Node

## Dev capture: the ground audit of 2026-09-21 from standpoints that show what
## the numbers said. The open items (the east climb's slot, the shoulder toes,
## a tunnel portal) and, for comparison, what was fixed (F's north arc on its
## embankment, B's ramp bed). Metal/Forward+; run through `open -n -a Godot`.
## Frames go to `documentation/screenshots/ground-audit-2026-09-21/`.

const OUTPUT_DIR := "res://documentation/screenshots/ground-audit-2026-09-21"
const SETTLE_SECONDS := 6.0
const SHOTS := [
	{"name": "01_east_climb_slot_from_above", "position": Vector3(127.5, 40.0, 30.0), "target": Vector3(127.5, 16.0, 0.0), "far": 400.0},
	{"name": "02_east_climb_slot_from_landing", "position": Vector3(124.0, 19.8, -12.0), "target": Vector3(128.0, 17.0, 4.0), "far": 400.0},
	{"name": "03_south_shoulder_toe", "position": Vector3(52.0, 4.0, 40.0), "target": Vector3(62.0, 1.5, 29.0), "far": 400.0},
	{"name": "04_north_shoulder_face", "position": Vector3(58.0, 4.0, -24.0), "target": Vector3(70.5, 6.0, -33.0), "far": 400.0},
	{"name": "05_tunnel3_portal", "position": Vector3(348.0, 46.0, 1262.0), "target": Vector3(336.0, 38.5, 1236.0), "far": 1200.0},
	{"name": "06_f_north_arc_embankment", "position": Vector3(60.0, 22.0, -200.0), "target": Vector3(105.0, 9.0, -155.0), "far": 800.0},
	{"name": "07_f_arc_from_below", "position": Vector3(90.0, 1.5, -185.0), "target": Vector3(95.0, 9.0, -163.0), "far": 800.0},
	{"name": "08_b_north_ramp_bed", "position": Vector3(-30.0, 6.0, -80.0), "target": Vector3(-48.0, -2.0, -100.0), "far": 600.0},
	{"name": "09_s3_spur_nose", "position": Vector3(30.0, 12.0, -215.0), "target": Vector3(52.0, 6.0, -190.0), "far": 800.0},
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
	camera.name = "ground_audit_camera"
	camera.fov = 55.0
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
	get_tree().quit()
