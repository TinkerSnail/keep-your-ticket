extends Node

## Dev probe: the east climb's walled courts, banks, and basin chain.
##
## Throwaway diagnostic for the 2026-08-23 reports from play: masonry colliding
## with the ground skin at the courts, missing faces on the green, floating
## fall tubes on the chain. Free cameras only — half these standpoints are in
## mid-air, and the ones that are not are inside courts the player screenshots
## came from.

const SETTLE := 6.0

## Yaw convention (see `_east_probe.gd`): forward is (-sin yaw, -cos yaw), so
## 0 = north (-z), -90 = east (+x), +90 = west (-x), 180 = south (+z).
const FREE := [
	# The y=10 south walled court (terrace at x 85.6..89.2), from above and
	# outside — the standpoint of the player's first two screenshots.
	{"name": "a_court10s_above", "pos": Vector3(87.4, 14.5, 18.0), "yaw": 0.0, "pitch": -28.0},
	# Standing in it, facing along the cut — the frame that found the bank-end
	# holes on 2026-08-22.
	{"name": "b_court10s_east", "pos": Vector3(87.4, 11.6, 10.0), "yaw": -90.0, "pitch": -4.0},
	{"name": "c_court10s_back", "pos": Vector3(87.4, 11.6, 8.5), "yaw": 180.0, "pitch": -6.0},
	# The y=14 south court (terrace at x 96.8..100.4), same three ways.
	{"name": "d_court14s_above", "pos": Vector3(98.6, 18.5, 18.0), "yaw": 0.0, "pitch": -28.0},
	{"name": "e_court14s_east", "pos": Vector3(98.6, 15.6, 10.0), "yaw": -90.0, "pitch": -4.0},
	{"name": "f_court14s_stair", "pos": Vector3(95.5, 16.5, 3.5), "yaw": 155.0, "pitch": -22.0},
	# North side for the winding-dependent faults.
	{"name": "g_court14n_above", "pos": Vector3(98.6, 18.5, -22.0), "yaw": 180.0, "pitch": -28.0},
	{"name": "h_court10n_east", "pos": Vector3(87.4, 11.6, -14.0), "yaw": -90.0, "pitch": -4.0},
	# Across the ravine, low: what the far bank shows through its own holes.
	{"name": "i_across_ravine", "pos": Vector3(89.0, 12.0, -9.0), "yaw": 168.0, "pitch": -6.0},
	# The chain from the head looking down — the player's basin screenshot.
	{"name": "j_chain_from_head", "pos": Vector3(112.0, 21.0, 0.0), "yaw": 90.0, "pitch": -18.0},
	# The chain from the belvedere looking up.
	{"name": "k_chain_from_foot", "pos": Vector3(79.5, 8.3, -1.0), "yaw": -90.0, "pitch": -6.0},
	# One bowl close up, side on.
	{"name": "l_bowl_close", "pos": Vector3(96.0, 14.2, -3.2), "yaw": 145.0, "pitch": -18.0},
	# The head of the climb and the crest courts.
	{"name": "m_head", "pos": Vector3(103.0, 21.5, -16.0), "yaw": -145.0, "pitch": -18.0},
	# Aerial: the whole climb corridor.
	{"name": "n_aerial", "pos": Vector3(80.0, 42.0, 0.0), "yaw": -90.0, "pitch": -52.0},
	# From the west, plaza side of the hill, mid-height: the scarp and both
	# court flanks in one frame.
	{"name": "o_from_west", "pos": Vector3(62.0, 22.0, 0.0), "yaw": -90.0, "pitch": -14.0},
	# The structure at the head of the chain and the grey sail leaning on it,
	# from both flanks — close enough to name the node.
	{"name": "p_head_chain_s", "pos": Vector3(102.0, 20.0, 6.0), "yaw": -40.0, "pitch": -12.0},
	{"name": "q_head_chain_n", "pos": Vector3(103.0, 20.0, -9.0), "yaw": -151.0, "pitch": -12.0},
	# Straight down over the white dart seen from p, to read its plan position
	# off the frame.
	{"name": "r_dart_topdown", "pos": Vector3(106.0, 30.0, 5.0), "yaw": 0.0, "pitch": -89.0},
	{"name": "s_dart_low", "pos": Vector3(103.5, 18.6, 3.0), "yaw": -120.0, "pitch": -10.0},
	# Standing at each court's mouth at eye height, looking out over the back
	# wall — the standpoint of the 2026-08-23 "still see through the hill"
	# report, where the bay-edge column jump tears the plateau strip.
	{"name": "t_mouth10s", "pos": Vector3(87.4, 11.3, 3.8), "yaw": 180.0, "pitch": 5.0},
	{"name": "u_mouth14s", "pos": Vector3(98.6, 15.3, 3.8), "yaw": 180.0, "pitch": 5.0},
	{"name": "v_mouth10n", "pos": Vector3(87.4, 11.3, -7.8), "yaw": 0.0, "pitch": 5.0},
	{"name": "w_mouth14n", "pos": Vector3(98.6, 15.3, -7.8), "yaw": 0.0, "pitch": 5.0},
	# The junction where the climb delivers onto the head landing — the "weird
	# ledge before the landing" report. Both route heads and the median's end.
	{"name": "x_head_edge", "pos": Vector3(111.0, 19.6, -2.0), "yaw": 90.0, "pitch": -14.0},
	{"name": "y_ramp_head", "pos": Vector3(109.6, 19.4, -7.65), "yaw": 90.0, "pitch": -16.0},
	{"name": "z_stair_head", "pos": Vector3(109.6, 19.4, 3.65), "yaw": 90.0, "pitch": -16.0},
	# The surroundings: standing on the meadow and the shoulders, where the
	# 2026-08-23 "tears" reports come from. The skin/shoulder junction runs
	# along z -28 and 24 — half of these look straight down it.
	{"name": "aa_meadow_n", "pos": Vector3(112.0, 20.5, -22.0), "yaw": 135.0, "pitch": -10.0},
	{"name": "ab_meadow_s", "pos": Vector3(112.0, 20.5, 18.0), "yaw": 45.0, "pitch": -10.0},
	{"name": "ac_rim_toe", "pos": Vector3(124.0, 21.5, -2.0), "yaw": 90.0, "pitch": -8.0},
	{"name": "ad_join_n", "pos": Vector3(80.0, 17.5, -28.0), "yaw": -90.0, "pitch": -12.0},
	{"name": "ae_join_s", "pos": Vector3(80.0, 17.5, 24.0), "yaw": -90.0, "pitch": -12.0},
	{"name": "af_shoulder_n", "pos": Vector3(72.0, 17.0, -40.0), "yaw": -140.0, "pitch": -10.0},
	{"name": "ag_shoulder_s", "pos": Vector3(72.0, 17.0, 36.0), "yaw": -40.0, "pitch": -10.0},
	{"name": "ah_aerial_wide", "pos": Vector3(90.0, 55.0, -2.0), "yaw": -90.0, "pitch": -62.0},
	# Close along each bay's boundary line from the meadow side — the
	# 2026-08-23 "tears along the bays" report. `rel` cameras stand on the
	# ground the raycast finds plus an eye height, because three fixed-height
	# passes in a row buried the camera inside the meadow and photographed
	# fill masses through culled backfaces.
	{"name": "ba_bay14s_rear", "pos": Vector3(100.9, 1.7, 14.5), "yaw": 35.0, "pitch": -28.0, "rel": true},
	{"name": "bb_bay14s_rear_w", "pos": Vector3(96.2, 1.7, 14.5), "yaw": -30.0, "pitch": -28.0, "rel": true},
	{"name": "bc_bay10s_rear", "pos": Vector3(89.5, 1.7, 14.0), "yaw": 15.0, "pitch": -25.0, "rel": true},
	{"name": "bd_bay14n_rear", "pos": Vector3(98.6, 1.7, -16.5), "yaw": 170.0, "pitch": -28.0, "rel": true},
	{"name": "be_along_bays", "pos": Vector3(109.0, 1.7, 8.0), "yaw": 105.0, "pitch": -8.0, "rel": true},
]


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run()


func _run() -> void:
	ParkClock.running = false
	ParkClock.set_clock(15, 0)
	await get_tree().create_timer(SETTLE).timeout

	var cam := Camera3D.new()
	add_child(cam)
	cam.current = true
	for shot in FREE:
		await _free(cam, shot)
	get_tree().quit()


func _free(cam: Camera3D, shot: Dictionary) -> void:
	var pos: Vector3 = shot["pos"]
	if shot.get("rel", false):
		var space := get_viewport().get_world_3d().direct_space_state
		var q := PhysicsRayQueryParameters3D.create(
			Vector3(pos.x, 60.0, pos.z), Vector3(pos.x, -5.0, pos.z))
		var hit := space.intersect_ray(q)
		if not hit.is_empty():
			pos.y = hit["position"].y + pos.y
	cam.global_position = pos
	cam.rotation = Vector3(deg_to_rad(shot["pitch"]), deg_to_rad(shot["yaw"]), 0.0)
	for _i in 4:
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw
	var path := "user://terrace_%s.png" % shot["name"]
	get_viewport().get_texture().get_image().save_png(path)
	print("saved ", path)
