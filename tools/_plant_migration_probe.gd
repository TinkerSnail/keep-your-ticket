extends Node

## Dev probe: does a plant moved to Blender look as it did in Godot?
##
## Written on 2026-09-27, when the palm-bed plants (the fern fan first) moved
## from Godot courses and tool scripts to Blender files. Run it under a real
## renderer before and after the swap, with KYT_TAG=before and KYT_TAG=after,
## and compare the frames:
##
##     KYT_TAG=before KYT_PLANT=res://scenes/world/coastal_palm_fern_fill.tscn \
##         open -n -a /Applications/Godot.app --args --path "$PWD" tools/run.tscn -- _plant_migration_probe
##
## The studio views stand the plant alone at the world's origin on a soil
## plane, the park hidden and the game's own sun, sky and haze kept; the bed
## views show the park as it is, at the foot of `walk_palm_3_w` (an arrival
## palm: ferns, Hakone ring and Purple Heart). Writes
## `user://plant_migration/<tag>_<view>.png`.

const STUDIO := [
	{"name": "side", "eye": Vector3(0.0, 0.55, 1.9), "look": Vector3(0.0, 0.2, 0.0)},
	{"name": "three_quarter", "eye": Vector3(1.1, 1.05, 1.1), "look": Vector3(0.0, 0.12, 0.0)},
	{"name": "top", "eye": Vector3(0.0, 1.6, 0.01), "look": Vector3.ZERO},
	{"name": "low", "eye": Vector3(-1.3, 0.25, -0.6), "look": Vector3(0.0, 0.18, 0.0)},
]
const BED := [
	{"name": "bed", "from": Vector3(2.4, 1.65, 1.2)},
	{"name": "bed_close", "from": Vector3(1.2, 1.1, -0.9)},
]
## KYT_CONTEXT=1: the plants where the player meets them, at eye height,
## instead of the studio (2026-09-28, her "the hakone grass looks a little
## weird in context"): an arrival palm from walking distance and close, down
## the arrival allée, and a Boardwalk palm box.
const CONTEXT := [
	{"name": "arrival_walk", "palm": "walk_palm_3_w", "from": Vector3(5.0, 1.65, 2.5)},
	{"name": "arrival_near", "palm": "walk_palm_3_w", "from": Vector3(2.6, 1.65, -1.2)},
	{"name": "allee", "palm": "", "eye": Vector3(0.0, 1.85, 214.0), "look": Vector3(0.0, 0.3, 190.0)},
	{"name": "boardwalk_box", "palm": "deck_palm_1", "from": Vector3(3.2, 1.65, 2.0)},
	# Straight down on one stretch of the allée: walk, curb beds, palm row.
	{"name": "allee_top", "palm": "", "eye": Vector3(-6.0, 26.0, 188.0), "look": Vector3(-6.0, 0.0, 187.9)},
	{"name": "front_road_top", "palm": "", "eye": Vector3(-22.0, 22.0, 238.0), "look": Vector3(-22.0, 0.0, 237.9)},
]


func _ready() -> void:
	var tag := OS.get_environment("KYT_TAG")
	if tag == "":
		tag = "now"
	var plant_path := OS.get_environment("KYT_PLANT")
	if plant_path == "":
		plant_path = "res://scenes/world/coastal_palm_fern_fill.tscn"
	var main: Node = (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(main)
	ParkClock.running = false
	ParkClock.set_clock(14, 0)
	var camera := Camera3D.new()
	camera.fov = 50.0
	camera.far = 4200.0
	add_child(camera)
	camera.make_current()
	# The HUD is a CanvasLayer; KYT_HUD=1 keeps it, as the first fern frames had it.
	var hud := main.get_node_or_null("hud")
	if hud != null and OS.get_environment("KYT_HUD") == "":
		hud.set("visible", false)

	var world := main.get_node("park_world") as Node3D
	var folder := "user://plant_migration"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	if OS.get_environment("KYT_LINEUP") != "":
		await _lineup(main, camera, folder, tag)
		get_tree().quit()
		return
	if OS.get_environment("KYT_CONTEXT") != "":
		camera.fov = 70.0
		await get_tree().create_timer(5.0).timeout
		for view in CONTEXT:
			if view["palm"] == "":
				camera.look_at_from_position(view["eye"], view["look"], Vector3.UP)
			else:
				var foot := (main.find_child(view["palm"], true, false) as Node3D).global_position
				camera.look_at_from_position(foot + view["from"], foot + Vector3.UP * 0.3, Vector3.UP)
			await _shoot(camera, "%s/%s_%s.png" % [folder, tag, view["name"]])
		get_tree().quit()
		return
	world.visible = false
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(6.0, 6.0)
	var soil := StandardMaterial3D.new()
	soil.albedo_color = Color(0.33, 0.25, 0.18)
	soil.roughness = 1.0
	plane.material = soil
	ground.mesh = plane
	add_child(ground)
	var plant := (load(plant_path) as PackedScene).instantiate() as Node3D
	add_child(plant)
	await get_tree().create_timer(4.0).timeout

	for view in STUDIO:
		camera.look_at_from_position(view["eye"], view["look"],
			Vector3.FORWARD if view["name"] == "top" else Vector3.UP)
		await _shoot(camera, "%s/%s_%s.png" % [folder, tag, view["name"]])

	plant.queue_free()
	ground.queue_free()
	world.visible = true
	var palm := main.find_child("walk_palm_3_w", true, false) as Node3D
	await get_tree().create_timer(2.0).timeout
	for view in BED:
		var foot := palm.global_position
		camera.look_at_from_position(foot + view["from"], foot + Vector3.UP * 0.15, Vector3.UP)
		await _shoot(camera, "%s/%s_%s.png" % [folder, tag, view["name"]])
	get_tree().quit()


## KYT_LINEUP=1: the planting palette side by side on a soil plane, the park
## hidden, a 1.7 m figure for scale (2026-09-28, her "focus on getting each
## plant right").
const LINEUP := [
	["res://scenes/world/coastal_palm_fern_fill.tscn", -4.4],
	["res://scenes/world/hakone_grass_tuft_vb.tscn", -2.3],
	["res://scenes/world/purple_heart_cluster.tscn", -0.4],
	["res://scenes/world/landscape_kit/azalea_bush.tscn", 1.6],
	["res://scenes/world/landscape_kit/hibiscus_shrub.tscn", 3.8],
]


func _lineup(main: Node, camera: Camera3D, folder: String, tag: String) -> void:
	(main.get_node("park_world") as Node3D).visible = false
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(20.0, 12.0)
	var soil := StandardMaterial3D.new()
	soil.albedo_color = Color(0.33, 0.25, 0.18)
	plane.material = soil
	ground.mesh = plane
	add_child(ground)
	for entry in LINEUP:
		var plant := (load(entry[0]) as PackedScene).instantiate() as Node3D
		add_child(plant)
		plant.position = Vector3(entry[1], 0.0, 0.0)
	var figure := MeshInstance3D.new()
	var body := CapsuleMesh.new()
	body.radius = 0.22
	body.height = 1.7
	var blue := StandardMaterial3D.new()
	blue.albedo_color = Color(0.35, 0.45, 0.62)
	body.material = blue
	figure.mesh = body
	figure.position = Vector3(5.9, 0.85, 0.0)
	add_child(figure)
	await get_tree().create_timer(3.0).timeout
	camera.fov = 55.0
	for view in [["lineup", Vector3(0.75, 1.65, 8.5), Vector3(0.75, 0.6, 0.0)],
			["lineup_high", Vector3(0.75, 5.0, 7.0), Vector3(0.75, 0.3, 0.0)]]:
		camera.look_at_from_position(view[1], view[2], Vector3.UP)
		camera.make_current()  # the player's camera takes over if not
		await _shoot(camera, "%s/%s_%s.png" % [folder, tag, view[0]])


func _shoot(camera: Camera3D, path: String) -> void:
	for _i in 30:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(path)
	print("wrote ", path)
