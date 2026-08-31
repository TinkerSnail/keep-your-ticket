extends Node

## Dev probe: the cascade's silhouette, shot square-on against the reference.
##
## Throwaway, and it exists because the one view that matters here cannot be
## taken from anywhere a player stands. The court is 10m deep between the wing
## toes and the backs of the shops, so from inside it the monument runs off both
## edges of the frame; from the promenade the shop row is 8–11m and the monument
## is 6m, so it is cropped. The elevation therefore comes from a free camera
## above the roofline — a drawing, not a photograph, which is the only way to
## compare a spread-to-rise ratio against a square-on reference plate.
##
## The court shots are the photographs, and they are what the complaint was
## about.

const HOUR := 15
const MINUTE := 0
const NIGHT := [21, 15]
const SETTLE := 3.0

## `yaw` −90 is east, which is the way the facade faces.
const SHOTS := [
	# The elevation: above the shop roofs, far enough west that a 29m spread fits
	# a 75° frame, pitched down onto the axis.
	{"name": "elevation", "pos": Vector3(-108.0, 12.0, -2.0), "yaw": -90.0, "pitch": -7.0},
	{"name": "elevation_near", "pos": Vector3(-92.0, 9.0, -2.0), "yaw": -90.0, "pitch": -9.0},
	# From the court on the axis, at eye height. This is the frame the complaint
	# came from.
	{"name": "court", "pos": Vector3(-72.0, -4.2, -2.0), "yaw": -90.0, "pitch": 6.0},
	{"name": "court_back", "pos": Vector3(-76.0, -4.2, -2.0), "yaw": -90.0, "pitch": 5.0},
	# Off the axis, which is how you actually arrive — out of the alley mouth to
	# the west and turning.
	{"name": "court_oblique", "pos": Vector3(-74.0, -4.2, 6.0), "yaw": -62.0, "pitch": 5.0},
	# One wing each, filling the frame, because the two are supposed to differ —
	# north is the ramp, south is the garden stair — and at 24m across a single
	# frame is too small to tell a tread from a step in the mass under it.
	{"name": "wing_north", "pos": Vector3(-73.0, -4.0, -11.0), "yaw": -90.0, "pitch": 8.0},
	{"name": "wing_south", "pos": Vector3(-73.0, -4.0, 7.0), "yaw": -90.0, "pitch": 8.0},
]


func _ready() -> void:
	var main: Node = load("res://scenes/main/main.tscn").instantiate()
	add_child(main)
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(HOUR, MINUTE)
	await get_tree().create_timer(SETTLE).timeout

	await ParkSections.enter(&"boardwalk", &"plaza")
	await get_tree().create_timer(SETTLE).timeout
	if ParkSections.current() != &"boardwalk":
		push_error("the boardwalk did not become the current logical area")
		get_tree().quit(1)
		return

	# A free camera rather than the player's. Half of these stand in mid-air over
	# the shops, and a CharacterBody3D put there falls out of the shot.
	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true

	# The niche head at three clocks. A recess 0.6m deep in a west-facing wall is
	# mostly shadow, and a shadow is the one thing a single still cannot tell
	# apart from geometry — so shoot the same frame as the sun moves and see
	# which parts of it hold still.
	for hm in [[11, 0], [15, 0], [18, 30]]:
		ParkClock.set_clock(hm[0], hm[1])
		await get_tree().create_timer(2.0).timeout
		cam.global_position = Vector3(-70.0, -4.0, -2.0)
		cam.rotation = Vector3(deg_to_rad(4.0), deg_to_rad(-90.0), 0.0)
		for _i in 4:
			await get_tree().physics_frame
		await RenderingServer.frame_post_draw
		var ni := get_viewport().get_texture().get_image()
		ni.save_png("user://cascade_niche_%02d%02d.png" % [hm[0], hm[1]])
		print("saved niche ", hm)
	# The crest after dark, which is the only time the globes are doing anything.
	ParkClock.set_clock(NIGHT[0], NIGHT[1])
	await get_tree().create_timer(2.5).timeout
	cam.global_position = Vector3(-70.0, -3.6, -2.0)
	cam.rotation = Vector3(deg_to_rad(-2.0), deg_to_rad(-90.0), 0.0)
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("user://cascade_globes_night.png")
	print("saved night")

	ParkClock.set_clock(HOUR, MINUTE)
	await get_tree().create_timer(2.5).timeout
	cam.global_position = Vector3(-70.0, -3.6, -2.0)
	cam.rotation = Vector3(deg_to_rad(-2.0), deg_to_rad(-90.0), 0.0)
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("user://cascade_globes_day.png")
	print("saved day")

	for shot in SHOTS:
		cam.global_position = shot["pos"]
		cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
		for _i in 4:
			await get_tree().physics_frame
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		var path := "user://cascade_%s.png" % shot["name"]
		img.save_png(path)
		print("saved ", path)

	get_tree().quit()
