extends Node

## Dev probe: what the mounted editor-owned range costs, so that a change to how
## its Blender source is exported can be measured rather than argued about.
##
## Written for the 2026-09-15 coastal-rock handoff repair, where the source held
## one selectable collision twin per boulder and the mounted GLB therefore
## carried some 15,000 rock-related nodes. The same run before and after the
## export change gives the comparison; nothing here is a budget on its own.
##
## Four readings, each written as its own block:
##
##   startup   wall-clock to load, instantiate and mount `main.tscn`, and the
##             same three steps for the range wrapper alone.
##   tree      node counts under the range mount by class, and the collision
##             triangle total across its concave shapes.
##   physics   a grid of downward rays over the northern rock field and over the
##             plaza as a control, a sphere-query grid over the same field, and a
##             CharacterBody3D walked along the massif beach and across the
##             plaza, timed per physics frame.
##   render    from three standpoints with the range visible and hidden: mean and
##             worst frame time and the renderer's object, primitive and draw-call
##             monitors. Meaningful only under a real driver; the headless run
##             prints zeros here and is right about the rest.
##
## Writes `user://range_perf_<driver>.txt`, because a run launched by `open` has
## no stdout anyone can read, and prints the same lines.

const SETTLE := 40
const MEASURE := 150
const WALK_FRAMES := 900
const WALK_SPEED := 4.0

## Northern rock field in world coordinates. The Blender source lays the rocks at
## x -1078..1187, y 569..1874; Godot's z is the negative of Blender's y.
const FIELD_MIN := Vector2(-1050.0, -1850.0)
const FIELD_MAX := Vector2(1150.0, -600.0)
const FIELD_COLS := 60
const FIELD_ROWS := 50
const CONTROL_MIN := Vector2(-50.0, -50.0)
const CONTROL_MAX := Vector2(50.0, 50.0)
const RAY_TOP := 90.0
const RAY_BOTTOM := -40.0

## The beach walk starts inside the densest talus of the main massif and heads
## east along the shore; the control walk crosses the plaza.
const WALKS := [
	{"name": "massif_beach", "start": Vector3(-900.0, 30.0, -950.0), "dir": Vector3(1.0, 0.0, 0.0)},
	{"name": "plaza_control", "start": Vector3(-30.0, 30.0, 20.0), "dir": Vector3(1.0, 0.0, 0.0)},
]

const STANDPOINTS := [
	{"name": "massif_beach", "position": Vector3(-900.0, 16.0, -950.0), "target": Vector3(-700.0, 8.0, -1300.0)},
	{"name": "promenade_north", "position": Vector3(-98.0, -4.3, -70.0), "target": Vector3(-140.0, 20.0, -420.0)},
	{"name": "walk_foot", "position": Vector3(0.0, 2.0, 236.0), "target": Vector3(-6.0, 30.0, -600.0)},
]

var _main: Node
var _range: Node
var _camera: Camera3D
var _lines: PackedStringArray = []
var _phase := "physics"
var _walk := 0
var _walker: CharacterBody3D
var _walk_frame := 0
var _walk_acc := 0.0
var _walk_worst := 0.0
var _walk_last_us := 0
var _walk_dist := 0.0
var _visible_state := 0
var _standpoint := 0
var _frame := 0
var _acc := 0.0
var _worst := 0.0
var _frame_last_us := 0


func _ready() -> void:
	_line("range_perf_probe  driver=%s  %s" % [DisplayServer.get_name(), Time.get_datetime_string_from_system()])
	_startup()
	_tree()
	ParkClock.running = false
	ParkClock.set_clock(15, 30)
	_camera = Camera3D.new()
	_camera.far = 8000.0
	add_child(_camera)
	_camera.make_current()
	# Physics needs a frame or two of the world settled before rays see it.
	await get_tree().physics_frame
	await get_tree().physics_frame
	_queries()
	_begin_walk()


func _startup() -> void:
	var t0 := Time.get_ticks_usec()
	var wrapper := load("res://scenes/world/range_forest_background.tscn") as PackedScene
	var t1 := Time.get_ticks_usec()
	var alone := wrapper.instantiate()
	var t2 := Time.get_ticks_usec()
	add_child(alone)
	var t3 := Time.get_ticks_usec()
	_line("startup range_alone  load %8.1f ms  instantiate %8.1f ms  mount %8.1f ms" % [
		(t1 - t0) / 1000.0, (t2 - t1) / 1000.0, (t3 - t2) / 1000.0])
	remove_child(alone)
	alone.queue_free()
	var m0 := Time.get_ticks_usec()
	var scene := load("res://scenes/main/main.tscn") as PackedScene
	var m1 := Time.get_ticks_usec()
	_main = scene.instantiate()
	var m2 := Time.get_ticks_usec()
	add_child(_main)
	var m3 := Time.get_ticks_usec()
	_line("startup main         load %8.1f ms  instantiate %8.1f ms  mount %8.1f ms" % [
		(m1 - m0) / 1000.0, (m2 - m1) / 1000.0, (m3 - m2) / 1000.0])
	_line("memory  static %.1f MB  objects %d  nodes %d  resources %d" % [
		Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0,
		Performance.get_monitor(Performance.OBJECT_COUNT),
		Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT)])


func _tree() -> void:
	_range = _main.find_child("range_forest_background", true, false)
	if _range == null:
		_line("tree    no range_forest_background node")
		return
	var counts := {}
	var faces := 0
	var surfaces := 0
	var stack: Array[Node] = [_range]
	var total := 0
	var bodies_under_mesh := 0
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		total += 1
		counts[n.get_class()] = counts.get(n.get_class(), 0) + 1
		if n is StaticBody3D and n.get_parent() is MeshInstance3D:
			bodies_under_mesh += 1
		if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
			surfaces += (n as MeshInstance3D).mesh.get_surface_count()
		if n is CollisionShape3D:
			var shape := (n as CollisionShape3D).shape
			if shape is ConcavePolygonShape3D:
				faces += (shape as ConcavePolygonShape3D).get_faces().size() / 3
		for c in n.get_children():
			stack.append(c)
	var keys := counts.keys()
	keys.sort()
	var parts: PackedStringArray = []
	for k in keys:
		parts.append("%s=%d" % [k, counts[k]])
	_line("tree    nodes %d  mesh_surfaces %d  collision_triangles %d  bodies_under_mesh %d" % [total, surfaces, faces, bodies_under_mesh])
	_line("tree    " + " ".join(parts))


func _queries() -> void:
	var space := get_viewport().world_3d.direct_space_state
	_ray_grid(space, "rock_field", FIELD_MIN, FIELD_MAX, FIELD_COLS, FIELD_ROWS)
	_ray_grid(space, "plaza_control", CONTROL_MIN, CONTROL_MAX, FIELD_COLS, FIELD_ROWS)
	var shape := SphereShape3D.new()
	shape.radius = 1.5
	var params := PhysicsShapeQueryParameters3D.new()
	params.shape = shape
	params.collision_mask = 1
	var hits := 0
	var t0 := Time.get_ticks_usec()
	for i in FIELD_COLS:
		for j in FIELD_ROWS:
			var x := lerpf(FIELD_MIN.x, FIELD_MAX.x, float(i) / float(FIELD_COLS - 1))
			var z := lerpf(FIELD_MIN.y, FIELD_MAX.y, float(j) / float(FIELD_ROWS - 1))
			params.transform = Transform3D(Basis.IDENTITY, Vector3(x, 4.0, z))
			if not space.intersect_shape(params, 8).is_empty():
				hits += 1
	var t1 := Time.get_ticks_usec()
	_line("physics sphere_grid rock_field   %5d queries  %5d hits  %8.2f ms" % [
		FIELD_COLS * FIELD_ROWS, hits, (t1 - t0) / 1000.0])


func _ray_grid(space: PhysicsDirectSpaceState3D, label: String, lo: Vector2, hi: Vector2, cols: int, rows: int) -> void:
	var hits := 0
	var t0 := Time.get_ticks_usec()
	for i in cols:
		for j in rows:
			var x := lerpf(lo.x, hi.x, float(i) / float(cols - 1))
			var z := lerpf(lo.y, hi.y, float(j) / float(rows - 1))
			var q := PhysicsRayQueryParameters3D.create(Vector3(x, RAY_TOP, z), Vector3(x, RAY_BOTTOM, z), 1)
			if not space.intersect_ray(q).is_empty():
				hits += 1
	var t1 := Time.get_ticks_usec()
	_line("physics ray_grid    %-14s %5d rays     %5d hits  %8.2f ms" % [label, cols * rows, hits, (t1 - t0) / 1000.0])


func _begin_walk() -> void:
	if _walk >= WALKS.size():
		_phase = "render"
		_visible_state = 0
		_standpoint = 0
		_pose()
		return
	var spec: Dictionary = WALKS[_walk]
	_walker = CharacterBody3D.new()
	var col := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.35
	capsule.height = 1.8
	col.shape = capsule
	_walker.add_child(col)
	_walker.collision_mask = 1
	add_child(_walker)
	var space := get_viewport().world_3d.direct_space_state
	var start: Vector3 = spec["start"]
	var q := PhysicsRayQueryParameters3D.create(start + Vector3.UP * 60.0, start + Vector3.DOWN * 60.0, 1)
	var hit := space.intersect_ray(q)
	if not hit.is_empty():
		start.y = (hit["position"] as Vector3).y + 1.0
	_walker.global_position = start
	_walk_frame = 0
	_walk_acc = 0.0
	_walk_worst = 0.0
	_walk_dist = 0.0
	_walk_last_us = Time.get_ticks_usec()
	_phase = "walk"


func _physics_process(delta: float) -> void:
	if _phase != "walk" or _walker == null:
		return
	var now := Time.get_ticks_usec()
	var frame_ms := (now - _walk_last_us) / 1000.0
	_walk_last_us = now
	_walk_frame += 1
	if _walk_frame > SETTLE:
		_walk_acc += frame_ms
		_walk_worst = maxf(_walk_worst, frame_ms)
	var spec: Dictionary = WALKS[_walk]
	var before := _walker.global_position
	var v := (spec["dir"] as Vector3) * WALK_SPEED
	v.y = _walker.velocity.y - 9.8 * delta
	if _walker.is_on_floor():
		v.y = 0.0
	_walker.velocity = v
	_walker.move_and_slide()
	_walk_dist += (_walker.global_position - before).length()
	if _walk_frame < SETTLE + WALK_FRAMES:
		return
	_line("physics walk        %-14s %4d frames  mean %6.3f ms  worst %6.3f ms  moved %6.1f m  end y %6.2f" % [
		spec["name"], WALK_FRAMES, _walk_acc / float(WALK_FRAMES), _walk_worst, _walk_dist, _walker.global_position.y])
	_phase = "physics"
	remove_child(_walker)
	_walker.queue_free()
	_walker = null
	_walk += 1
	_begin_walk.call_deferred()


func _pose() -> void:
	if _range != null:
		_range.visible = _visible_state == 1
	var sp: Dictionary = STANDPOINTS[_standpoint]
	_camera.fov = 70.0
	_camera.global_position = sp["position"]
	_camera.look_at(sp["target"], Vector3.UP)
	_frame = 0
	_acc = 0.0
	_worst = 0.0
	_frame_last_us = Time.get_ticks_usec()


## Wall clock between rendered frames rather than `delta`: under `--fixed-fps`
## the delta is a constant and reads 16.67 ms whatever the renderer does. Run
## with `--disable-vsync` or the wall clock is capped too.
func _process(_delta: float) -> void:
	if _phase != "render":
		return
	var now := Time.get_ticks_usec()
	var frame_s := (now - _frame_last_us) / 1000000.0
	_frame_last_us = now
	_frame += 1
	if _frame <= SETTLE:
		return
	_acc += frame_s
	_worst = maxf(_worst, frame_s)
	if _frame < SETTLE + MEASURE:
		return
	_line("render  range %-7s %-16s mean %6.2f ms  worst %6.2f ms  objects %6d  primitives %9d  draw_calls %6d" % [
		"visible" if _visible_state == 1 else "hidden", STANDPOINTS[_standpoint]["name"],
		_acc / float(MEASURE) * 1000.0, _worst * 1000.0,
		int(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)),
		int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)),
		int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))])
	_standpoint += 1
	if _standpoint < STANDPOINTS.size():
		_pose()
		return
	_standpoint = 0
	_visible_state += 1
	if _visible_state < 2:
		_pose()
		return
	_finish()


func _line(text: String) -> void:
	print(text)
	_lines.append(text)


func _finish() -> void:
	_phase = "done"
	if _range != null:
		_range.visible = true
	var path := "user://range_perf_%s.txt" % DisplayServer.get_name()
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f != null:
		f.store_string("\n".join(_lines) + "\n")
		f.close()
	print("wrote ", path)
	get_tree().quit()
