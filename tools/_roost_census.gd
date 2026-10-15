extends SceneTree

## Floater census, the game's half (terrain height-grid plan, Stage 0): the gull colony's roost markers in
## scenes/wildlife/wildlife.tscn against the game's collision, with the whole world mounted. Read-only.
##
##   Godot --headless --path <repo> --script res://tools/_roost_census.gd -- --out=<abs json> [--points=<census_blender.json>]
##
## For each roost: every body a ray straight down meets (birds left out), the top one, and the gap from the
## marker to it (+ floating, - buried); the first hit on places/world_terrain; and wildlife_test's own
## criterion, that first hit 0 to 0.2 m under the marker. Until height-grid Stage 5 (2026-10-15) the
## criterion was the test's older one, a vertex of range north, its west companion or the plug within 5 cm
## in plan and 0 to 0.2 m under the marker, read from the world terrain master's GLB; those landforms are
## the grid's now and the master exports none of them (the old reading is in git up to a8cd64b). With --points, the
## lakes' most floating edges from the Blender census are probed the same way, to see whether anything the
## game holds meets the water there.
## A MainLoop compiles before the autoloads register, so the world is loaded with load(), never preload.

const SETTLE := 12

var _frames := 0
var _world: Node = null


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames == 2:
		_world = (load("res://scenes/world/park_world.tscn") as PackedScene).instantiate()
		root.add_child(_world)
	elif _frames == 2 + SETTLE:
		_run()
		return true
	return false


func _arg(name: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with(name + "="):
			return a.substr(name.length() + 1)
	return ""


func _path(n: Node) -> String:
	return String(_world.get_path_to(n)) if _world.is_ancestor_of(n) else String(n.get_path())


func _hits(at: Vector3, above: float, below: float) -> Array:
	var space := root.get_world_3d().direct_space_state
	var out := []
	var exclude: Array[RID] = []
	for i in 12:
		var q := PhysicsRayQueryParameters3D.create(at + Vector3.UP * above, at - Vector3.UP * below)
		q.collide_with_areas = false
		q.exclude = exclude
		var h := space.intersect_ray(q)
		if h.is_empty():
			break
		exclude.append(h["rid"])
		var c := h["collider"] as Node
		var p := _path(c)
		if p.begins_with("wildlife"):
			continue
		out.append({"y": snappedf(h["position"].y, 0.001), "normal_y": snappedf(h["normal"].y, 0.001),
			"body": p, "layer": (c as CollisionObject3D).collision_layer if c is CollisionObject3D else 0})
	return out


func _run() -> void:
	var out := {"what": "gull roost markers against the game's collision (park_world.tscn mounted whole); + floating, - buried (m)",
		"roosts": [], "points": []}
	var roosts := _world.get_node_or_null("wildlife/gull_colony/roosts")
	if roosts == null:
		push_error("no wildlife/gull_colony/roosts")
		quit(1)
		return
	for m in roosts.get_children():
		var at: Vector3 = (m as Node3D).global_position
		var hits := _hits(at, 400.0, 600.0)
		var top: Dictionary = hits[0] if not hits.is_empty() else {}
		var terrain := {}
		for h in hits:
			if String(h["body"]).begins_with("places/world_terrain"):
				terrain = h
				break
		# wildlife_test's criterion: 0 to 0.2 m over the mounted ground.
		var on_ground := at.y - float(terrain["y"]) if not terrain.is_empty() else NAN
		var ok := on_ground >= 0.0 and on_ground <= 0.2
		out["roosts"].append({"name": String(m.name), "at": [snappedf(at.x, 0.01), snappedf(at.z, 0.01)],
			"y": snappedf(at.y, 0.001),
			"foot": snappedf(at.y - float(top["y"]), 0.001) if not top.is_empty() else null,
			"top_body": top.get("body", null),
			"foot_world_terrain": snappedf(on_ground, 0.001) if not terrain.is_empty() else null,
			"wildlife_test_criterion": ok, "hits": hits})
	var points := _arg("--points")
	if not points.is_empty():
		var census = JSON.parse_string(FileAccess.get_file_as_string(points))
		for lake in ["lake:lake_K1", "lake:lake_L0", "lake:plunge_pool"]:
			var e = census["kinds"]["other"][lake]
			var level: float = e["level_y"][0]
			for w in e["edge"]["worst_floating"].slice(0, 5):
				var at := Vector3(w["at"][0], level, w["at"][1])
				var hits := _hits(at, 200.0, 200.0)
				var top: Dictionary = hits[0] if not hits.is_empty() else {}
				out["points"].append({"lake": lake, "at": w["at"], "water_y": level, "blender_gap": w["gap_within_0.5m"],
					"game_gap": snappedf(level - float(top["y"]), 0.001) if not top.is_empty() else null,
					"top_body": top.get("body", null)})
	var path := _arg("--out")
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(out, " "))
	f.close()
	for r in out["roosts"]:
		print("roost %-24s foot %s on %s; world_terrain %s; test criterion %s" % [
			r["name"], r["foot"], r["top_body"], r["foot_world_terrain"], r["wildlife_test_criterion"]])
	for p in out["points"]:
		print("lake edge %s %s: blender %s, game %s on %s" % [p["lake"], p["at"], p["blender_gap"], p["game_gap"], p["top_body"]])
	print("roost_census: wrote %s" % path)
