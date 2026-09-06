extends Node

## Dev probe: what a standpoint is actually looking at. Puts the town probe's
## camera at a named standpoint, then rays a grid of frame pixels out to the
## camera's far plane and prints, per ray, what the physics world says is
## there: the hit's distance, position, collider, whether the face it struck
## looks toward the camera or away from it, and the generator's own height
## and colour terms at that spot (the natural ground, the range rise, the
## treeline blend). Written for the pale slope above the north town's valley
## in `n05_up_hill_road` (2026-09-05): a frame cannot say whether a surface
## is a front face, a culled back face seen through a hole, or a bare summit,
## and this can.
##
##   godot --headless --fixed-fps 60 --path . tools/run.tscn -- _sight_probe
##
## The standpoint and the pixel window are constants below; edit them.

const Plan := preload("res://scripts/park_plan.gd")
const SETTLE_SECONDS := 3.0
const FRAME := Vector2(1600.0, 900.0)
## The pixel window in the 1600x900 frame, and the grid step.
const WINDOW := Rect2(250.0, 0.0, 650.0, 340.0)
const STEP := Vector2(50.0, 34.0)

var _main: Node
var _camera: Camera3D
var _timer := 0.0
var _done := false
var _gen: Object


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	ParkClock.running = false
	ParkClock.set_clock(9, 30)
	_camera = Camera3D.new()
	_camera.far = 9000.0
	_camera.fov = 62.0
	add_child(_camera)
	_camera.make_current()
	_gen = load("res://tools/gen_props.gd").new()
	_timer = SETTLE_SECONDS


func _ground(xz: Vector2, fallback: float) -> float:
	var space: PhysicsDirectSpaceState3D = get_viewport().find_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(
		Vector3(xz.x, 400.0, xz.y), Vector3(xz.x, -40.0, xz.y), 1)
	var hit: Dictionary = space.intersect_ray(query)
	if hit.is_empty():
		return fallback
	return hit["position"].y


func _process(delta: float) -> void:
	if _done:
		return
	_timer -= delta
	if _timer > 0.0:
		return
	_done = true
	# n05_up_hill_road, exactly as `_town_probe` places it.
	var hill_foot: Vector2 = Plan.valley_point(128.0, 0.0)
	var head: Vector2 = Plan.valley_point(300.0, 0.0)
	var at := Vector3(hill_foot.x, _ground(hill_foot, 0.0) + 1.7, hill_foot.y)
	var target := Vector3(head.x, 14.0, head.y)
	_camera.global_position = at
	_camera.look_at(target, Vector3.UP)
	print("sight_probe: eye %s looking at %s, viewport %s" % [at, target, get_viewport().get_visible_rect().size])
	var vp_size: Vector2 = get_viewport().get_visible_rect().size
	var space: PhysicsDirectSpaceState3D = get_viewport().find_world_3d().direct_space_state
	var y := WINDOW.position.y
	while y <= WINDOW.end.y:
		var x := WINDOW.position.x
		while x <= WINDOW.end.x:
			var px := Vector2(x, y) / FRAME * vp_size
			var origin := _camera.project_ray_origin(px)
			var dir := _camera.project_ray_normal(px)
			var query := PhysicsRayQueryParameters3D.create(origin, origin + dir * 9000.0)
			query.hit_back_faces = true
			var hit: Dictionary = space.intersect_ray(query)
			if hit.is_empty():
				print("  px(%4d,%4d) sky" % [int(x), int(y)])
			else:
				var pos: Vector3 = hit["position"]
				var n: Vector3 = hit["normal"]
				var facing := "front" if n.dot(dir) < 0.0 else "BACK"
				var who: Object = hit["collider"]
				var name: String = String(who.name) if who != null else "?"
				var parent: String = String(who.get_parent().name) if who != null and who.get_parent() != null else "?"
				var xz := Vector2(pos.x, pos.z)
				var natural: float = _gen.call("_rebuild_natural_y", xz)
				var rise: float = _gen.call("_rebuild_range_rise", xz)
				var r := clampf((pos.y - Plan.RIM_RANGE_TREELINE_Y) / 60.0, 0.0, 1.0)
				print("  px(%4d,%4d) %5s d=%6.0f at (%6.0f,%6.1f,%6.0f) n=(%.2f,%.2f,%.2f) %s/%s natural=%6.1f rise=%6.1f rock=%.2f inland=%5.0f" % [
					int(x), int(y), facing, origin.distance_to(pos), pos.x, pos.y, pos.z,
					n.x, n.y, n.z, parent, name, natural, rise, r, Plan.coast_inland(xz)])
			x += STEP.x
		y += STEP.y
	get_tree().quit()
