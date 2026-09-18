extends Node

## Dev probe: from the player's spawn, which heading is heavy and who owns it?
##
## Written on 2026-09-18 after `player_motion_perf_probe` showed 8,200 draws on
## the opening view and 66,000-76,000 a quarter turn away. Draws the real
## player's first-person view at sixteen headings, then at the heaviest one
## hides each child of `park_world` (and main's other 3D children) in turn and
## reports the draw calls and primitives that go with it. Counts only; they do
## not depend on GPU contention. Nothing is saved. Writes `user://view_draws.txt`.

const HEADINGS := 16
const SETTLE := 6

var _lines: PackedStringArray = []


func _ready() -> void:
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
	_line("_view_draws_probe  %s" % Time.get_datetime_string_from_system())
	var main := (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	add_child(main)
	ParkClock.running = false
	var player := main.get_node("player") as Node3D
	player.process_mode = Node.PROCESS_MODE_DISABLED
	var eye := player.global_position + Vector3(0.0, 1.6, 0.0)
	var camera := Camera3D.new()
	camera.fov = 70.0
	camera.near = 0.05
	camera.far = 4200.0
	add_child(camera)
	camera.global_position = eye
	camera.make_current()
	for i in 60:
		await get_tree().process_frame
	var worst_h := 0
	var worst := 0
	for h in HEADINGS:
		camera.rotation = Vector3(0.0, -TAU * h / HEADINGS, 0.0)
		var r := await _count()
		var dir := -camera.global_transform.basis.z
		_line("heading %2d  dir (%5.2f %5.2f)  draws %6d  primitives %9d  objects %6d" % [
			h, dir.x, dir.z, r.draws, r.primitives, r.objects])
		if r.draws > worst:
			worst = r.draws
			worst_h = h
	camera.rotation = Vector3(0.0, -TAU * worst_h / HEADINGS, 0.0)
	var base := await _count()
	_line("")
	_line("heaviest heading %d: draws %d  primitives %d" % [worst_h, base.draws, base.primitives])
	var owners: Array[Node3D] = []
	for child in main.get_children():
		if child.name == "park_world":
			for w in child.get_children():
				if w.name == "places":
					for place in w.get_children():
						if place is Node3D:
							owners.append(place)
				elif w is Node3D:
					owners.append(w)
		elif child is Node3D and child != player:
			owners.append(child)
	# VIEW_DRAWS_UNDER="park_world/places/park_approach" asks about that node's
	# children instead.
	var under := OS.get_environment("VIEW_DRAWS_UNDER")
	if under != "":
		owners.clear()
		for child in main.get_node(under).get_children():
			if child is Node3D:
				owners.append(child)
	var rows: Array = []
	for owner_node in owners:
		if not owner_node.visible:
			continue
		owner_node.visible = false
		var r := await _count()
		owner_node.visible = true
		rows.append([base.draws - r.draws, base.primitives - r.primitives, owner_node.name])
	rows.sort_custom(func(a, b): return a[0] > b[0])
	for row in rows:
		if row[0] > 50 or row[1] > 20000:
			_line("  %-34s draws %6d  primitives %9d" % [row[2], row[0], row[1]])
	var sun := main.get_node("sun") as DirectionalLight3D
	sun.shadow_enabled = false
	var ns := await _count()
	sun.shadow_enabled = true
	_line("  %-34s draws %6d  primitives %9d" % [
		"(sun shadows)", base.draws - ns.draws, base.primitives - ns.primitives])
	var f := FileAccess.open("user://view_draws.txt", FileAccess.WRITE)
	f.store_string("\n".join(_lines) + "\n")
	f.close()
	get_tree().quit()


func _count() -> Dictionary:
	for i in SETTLE:
		await get_tree().process_frame
	return {
		"draws": int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)),
		"primitives": int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)),
		"objects": int(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)),
	}


func _line(text: String) -> void:
	print(text)
	_lines.append(text)
