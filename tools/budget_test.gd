extends Node

## Dev tool: does what the park draws stay inside a budget, and what does each
## placed scene cost?
##
## Written on 2026-09-18. The palm footings went in on 2026-09-10 at 45,000 mesh
## nodes, 40% of the world's triangles and nine tenths of the draw calls looking
## south from the plaza, and every test passed for a week because the tests ask
## whether a thing is there and looks right, never what it costs. Christina
## found it by turning the camera. This is the test that would have said so the
## same day.
##
## Headless, so it counts rather than draws. For each standpoint and heading it
## takes every visible mesh and root CSG shape whose bounds meet the player's
## frustum (70 degrees, 16:9, 4200m, honouring `visibility_range_end`) and sums
## their **surfaces**, which is what becomes a draw call before the renderer
## batches identical meshes, and their **triangles**. Nothing is occluded, so
## the figures are ceilings on the main pass, and the sun's shadow passes draw
## the near part of it again. Sources hidden by `static_merge` do not count;
## what it merged does. The crowd and the wildlife are left out: they change
## with the hour and have their own `perf_test`.
##
## Three verdicts: no view over `VIEW_SURFACES` or `VIEW_TRIANGLES`, the world
## under `WORLD_TRIANGLES`, and no scene placed `REPEATED` times or more over
## `PLACEMENT_SURFACES` or `PLACEMENT_TRIANGLES` a placement, which is the
## leaf-by-leaf mistake by name. It then prints the heaviest views, owners and
## placed scenes whether it passed or not, so the cost of something new is in
## the log the day it is added.
##
## **Raising a ceiling is Christina's decision**, made against a frame time from
## `player_motion_perf_probe`, not a way to make a new thing pass. The cheap
## fixes come first: share one mesh between identical placements, merge still
## geometry, give small things a `visibility_range_end`.
##
##   godot --headless --fixed-fps 60 --path . tools/run.tscn -- budget_test

const Plan := preload("res://scripts/park_plan.gd")

## Ceilings, set on 2026-09-18 about a fifth over that day's worst: 12,567
## surfaces and 2.88M triangles from the entrance walk looking north, 3.62M in
## the world, when the real player held 12-18ms a frame on an M1 Pro. Unoccluded
## counts run about twice the renderer's own draw calls for the same view.
const VIEW_SURFACES := 15_000
const VIEW_TRIANGLES := 3_500_000
const WORLD_TRIANGLES := 4_400_000
## A scene placed this many times or more is a repeated prop, and answers for
## what one placement costs. The merged palm footing is 20 surfaces and 46,862
## triangles, the heaviest repeated thing standing; unmerged it was 2,150.
const REPEATED := 3
const PLACEMENT_SURFACES := 60
const PLACEMENT_TRIANGLES := 50_000

const HEADINGS := 8
const EYE := 1.7
const FAR := 4200.0
const FOV := 70.0
const ASPECT := 16.0 / 9.0

const STANDPOINTS := [
	{"name": "player_spawn", "xz": Vector2(0.0, 24.0)},
	{"name": "promenade_north", "xz": Vector2(-98.0, -70.0)},
	{"name": "entrance_walk_foot", "xz": Vector2(0.0, 236.0)},
	{"name": "pier_head", "plan": "pier"},
	{"name": "east_belvedere", "plan": "belvedere"},
]

var _fails: PackedStringArray = []
## [global AABB, surfaces, triangles, visibility end, owner name, placed scene
## path, placement instance id]
var _items: Array = []


func _ready() -> void:
	var main := (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(main)
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	# The derived planting builds itself deferred and merges two frames later.
	for i in 12:
		await get_tree().process_frame
	var world := main.get_node("park_world")
	for group in world.get_children():
		if group.name in ["crowds", "wildlife"]:
			continue
		var owners: Array = group.get_children() if group.name in ["places", "shared"] \
			else [group]
		for owner_node in owners:
			_collect(owner_node, String(owner_node.name))

	var world_triangles := 0
	var by_owner := {}
	var by_scene := {}
	for item in _items:
		world_triangles += item[2]
		var o: Array = by_owner.get_or_add(item[4], [0, 0])
		o[0] += item[1]
		o[1] += item[2]
		var s: Array = by_scene.get_or_add(item[5], [0, 0, {}])
		s[0] += item[1]
		s[1] += item[2]
		s[2][item[6]] = true

	var views: Array = []
	for sp in STANDPOINTS:
		var eye := _eye(sp)
		for h in HEADINGS:
			var yaw := -TAU * h / HEADINGS
			var r := _view(eye, yaw)
			views.append([r[0], r[1], "%s heading %d" % [sp.name, h]])
			if r[0] > VIEW_SURFACES:
				_fail("%s heading %d draws %d surfaces, over %d" % [
					sp.name, h, r[0], VIEW_SURFACES])
			if r[1] > VIEW_TRIANGLES:
				_fail("%s heading %d holds %d triangles, over %d" % [
					sp.name, h, r[1], VIEW_TRIANGLES])
	if world_triangles > WORLD_TRIANGLES:
		_fail("the world holds %d triangles, over %d" % [world_triangles, WORLD_TRIANGLES])

	var scenes: Array = []
	for path in by_scene:
		var s: Array = by_scene[path]
		var placements: int = maxi((s[2] as Dictionary).size(), 1)
		scenes.append([s[0] / placements, s[1] / placements, placements, s[1], path])
		if placements < REPEATED or path == "(no scene)":
			continue
		if s[0] / placements > PLACEMENT_SURFACES:
			_fail("%s, placed %d times, costs %d surfaces a placement, over %d: share or merge its meshes" % [
				path, placements, s[0] / placements, PLACEMENT_SURFACES])
		if s[1] / placements > PLACEMENT_TRIANGLES:
			_fail("%s, placed %d times, costs %d triangles a placement, over %d" % [
				path, placements, s[1] / placements, PLACEMENT_TRIANGLES])

	print("world: %d surfaces, %d triangles in %d drawn objects" % [
		_sum(0), world_triangles, _items.size()])
	views.sort_custom(func(a, b): return a[0] > b[0])
	print("heaviest views by surfaces (ceiling %d, %d triangles):" % [
		VIEW_SURFACES, VIEW_TRIANGLES])
	for v in views.slice(0, 6):
		print("  %6d surfaces  %9d triangles  %s" % v)
	var owner_rows: Array = []
	for key in by_owner:
		owner_rows.append([by_owner[key][1], by_owner[key][0], key])
	owner_rows.sort_custom(func(a, b): return a[0] > b[0])
	print("heaviest owners by triangles:")
	for o in owner_rows.slice(0, 8):
		print("  %9d triangles  %6d surfaces  %s" % o)
	scenes.sort_custom(func(a, b): return a[3] > b[3])
	print("heaviest placed scenes by total triangles (per placement; repeated ones held to %d surfaces, %d triangles):"
		% [PLACEMENT_SURFACES, PLACEMENT_TRIANGLES])
	for s in scenes.slice(0, 12):
		print("  %5d surfaces  %8d triangles  x%-4d = %9d  %s" % s)

	if _fails.is_empty():
		print("PASS: every view, the world and every placed scene are inside the budget")
	else:
		for f in _fails:
			print("FAIL: %s" % f)
	get_tree().quit(0 if _fails.is_empty() else 1)


func _collect(root: Node, owner_name: String) -> void:
	for n in [root] + root.find_children("*", "", true, false):
		var visual := n as GeometryInstance3D
		if visual == null or not visual.is_visible_in_tree():
			continue
		var surfaces := 0
		var triangles := 0
		var mi := visual as MeshInstance3D
		var csg := visual as CSGShape3D
		if mi != null and mi.mesh != null:
			surfaces = mi.mesh.get_surface_count()
			for s in surfaces:
				triangles += _surface_triangles(mi.mesh, s)
		elif csg != null and csg.is_root_shape():
			var meshes := csg.get_meshes()
			if meshes.size() > 1 and meshes[1] != null:
				var mesh := meshes[1] as Mesh
				surfaces = mesh.get_surface_count()
				for s in surfaces:
					triangles += _surface_triangles(mesh, s)
		elif visual is MultiMeshInstance3D:
			var mm := (visual as MultiMeshInstance3D).multimesh
			if mm != null and mm.mesh != null:
				surfaces = mm.mesh.get_surface_count()
				for s in surfaces:
					triangles += _surface_triangles(mm.mesh, s) * mm.instance_count
		if surfaces == 0:
			continue
		var placed := _placement(visual)
		_items.append([visual.global_transform * visual.get_aabb(), surfaces, triangles,
			visual.visibility_range_end, owner_name, placed[0], placed[1]])


func _surface_triangles(mesh: Mesh, surface: int) -> int:
	var array_mesh := mesh as ArrayMesh
	if array_mesh != null:
		var indexed := array_mesh.surface_get_array_index_len(surface)
		return (indexed if indexed > 0 else array_mesh.surface_get_array_len(surface)) / 3
	var arrays := mesh.surface_get_arrays(surface)
	if arrays[Mesh.ARRAY_INDEX] != null:
		return (arrays[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
	return (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3


## The nearest ancestor that is an instanced scene, and which instance of it:
## what a person placed, as opposed to a node inside it.
func _placement(node: Node) -> Array:
	var at := node
	while at != null:
		if at.scene_file_path != "" and at != node:
			return [at.scene_file_path, at.get_instance_id()]
		at = at.get_parent()
	return ["(no scene)", 0]


func _view(eye: Vector3, yaw: float) -> Array:
	var basis := Basis(Vector3.UP, yaw)
	var forward := -basis.z
	var right := basis.x
	var half_v := deg_to_rad(FOV) * 0.5
	var half_h := atan(tan(half_v) * ASPECT)
	# Outward-facing planes through the eye, plus the far plane.
	var planes := [
		Plane(right.rotated(Vector3.UP, -half_h), eye),
		Plane((-right).rotated(Vector3.UP, half_h), eye),
		Plane(Vector3.UP.rotated(right, half_v), eye),
		Plane(Vector3.DOWN.rotated(right, -half_v), eye),
		Plane(forward, eye + forward * FAR),
	]
	var surfaces := 0
	var triangles := 0
	for item in _items:
		var box: AABB = item[0]
		var range_end: float = item[3]
		if range_end > 0.0 and box.get_center().distance_to(eye) > range_end:
			continue
		var inside := true
		for plane in planes:
			if (plane as Plane).is_point_over(box.get_support(-(plane as Plane).normal)):
				inside = false
				break
		if inside:
			surfaces += item[1]
			triangles += item[2]
	return [surfaces, triangles]


func _eye(sp: Dictionary) -> Vector3:
	var xz: Vector2 = sp.get("xz", Vector2.ZERO)
	if sp.get("plan", "") == "pier":
		xz = Vector2(Plan.PIER_ROOT.x - Plan.PIER_LENGTH + 2.0, Plan.PIER_Z)
	elif sp.get("plan", "") == "belvedere":
		xz = Vector2(Plan.EAST_BELVEDERE_VIEWER_X, 0.0)
	var space := get_viewport().world_3d.direct_space_state
	var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(
		Vector3(xz.x, 120.0, xz.y), Vector3(xz.x, -60.0, xz.y), 1))
	var ground: float = hit.position.y if not hit.is_empty() else 0.0
	return Vector3(xz.x, ground + EYE, xz.y)


func _sum(column: int) -> int:
	var total := 0
	for item in _items:
		total += item[column + 1]
	return total


func _fail(message: String) -> void:
	_fails.append(message)
