extends Node

## Dev probe: do mirrored palm fronds look the same merged as drawn one by one?
##
## Written on 2026-09-27, when palm_crown.gd began mirroring about half the
## fronds across their midrib. Mirroring by a mirrored transform lit the
## unmerged fronds pale: Godot lights a mirrored instance of a double-sided
## material from the wrong side. palm_crown.gd now gives a mirrored frond a
## mirrored copy of its mesh. Run it twice under a real renderer, once as is
## and once with KYT_NO_STATIC_MERGE=1, and compare the frames: a wrong side
## shows as pale, washed-out leaves.
##
## Writes `user://palm_mirror/<merged|unmerged>_<view>.png`, or `<tag>_<view>.png`
## with KYT_TAG=<tag> set, for any before-and-after of the crown's look (the
## leaf shader's undersides, 2026-09-27) or the trunk's (`trunk`, `trunk_up`).

const VIEWS := [
	{"name": "up_into_crown", "feet": Vector3(0.0, 0.2, 199.0), "yaw": 90.0, "pitch": 60.0},
	{"name": "boardwalk_crown", "feet": Vector3(-99.0, ParkPlan.SHORE_TOP + 0.2, -52.0), "yaw": 90.0, "pitch": 27.0},
	{"name": "allee", "feet": Vector3(0.0, 0.2, 220.0), "yaw": 0.0, "pitch": 10.0},
	# walk_palm_3_w's trunk (PRP-COAST-007, 2026-09-27): from 6.5 m, and up it from its foot.
	{"name": "trunk", "feet": Vector3(-6.0, 0.2, 191.5), "yaw": 57.5, "pitch": 18.0},
	{"name": "trunk_up", "feet": Vector3(-9.3, 0.2, 189.4), "yaw": 57.5, "pitch": 55.0},
]
const EYE := 1.65


func _ready() -> void:
	var tag := "unmerged" if OS.get_environment("KYT_NO_STATIC_MERGE") != "" else "merged"
	if OS.get_environment("KYT_TAG") != "":
		tag = OS.get_environment("KYT_TAG")
	add_child(load("res://scenes/main/main.tscn").instantiate())
	ParkClock.running = false
	ParkClock.set_clock(17, 30)
	var camera := Camera3D.new()
	camera.fov = 70.0
	camera.far = 4200.0
	add_child(camera)
	camera.make_current()
	await get_tree().create_timer(5.0).timeout
	var folder := "user://palm_mirror"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	for view in VIEWS:
		camera.global_position = view["feet"] + Vector3.UP * EYE
		camera.rotation = Vector3(deg_to_rad(view["pitch"]), deg_to_rad(view["yaw"]), 0.0)
		for _i in 30:
			await get_tree().process_frame
		var path := "%s/%s_%s.png" % [folder, tag, view["name"]]
		get_viewport().get_texture().get_image().save_png(path)
		print("wrote ", path)
	get_tree().quit()
