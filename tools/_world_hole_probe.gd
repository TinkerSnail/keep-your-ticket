extends Node

## Dev probe: rain rays over the whole land, two metres apart, against the
## ground owners only, and report where the ground is missing or drops into a
## slot: no hit at all with dry land on three sides, or a cell over 1.5m lower than both neighbours 4m away
## on either axis. A cliff has one low side and is not reported; a road cut is
## wider than the span. Clustered to 40m cells with the owner that was hit.

const X0 := -700.0
const X1 := 3600.0
const Z0 := -2700.0
const Z1 := 2700.0
const STEP := 2.0
const SPAN := 2
const DROP := 1.5
const GROUND_OWNERS := ["park_groundworks", "range_forest_background",
	"far_shore_city_relocation", "west_shell", "east_cascade", "west_stair"]


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 30:
		await get_tree().physics_frame
	var world := get_tree().root.find_child("park_world", true, false)
	var exclude: Array[RID] = []
	for b in world.find_children("*", "CollisionObject3D", true, false):
		var top := String(world.get_path_to(b)).get_slice("/", 1)
		if top not in GROUND_OWNERS:
			exclude.append(b.get_rid())
	var space := get_viewport().get_world_3d().direct_space_state
	var nx := int((X1 - X0) / STEP) + 1
	var nz := int((Z1 - Z0) / STEP) + 1
	var h := PackedFloat32Array()
	h.resize(nx * nz)
	var who := {}
	var q := PhysicsRayQueryParameters3D.new()
	q.exclude = exclude
	q.collision_mask = 1
	for ix in nx:
		for iz in nz:
			var x := X0 + ix * STEP
			var z := Z0 + iz * STEP
			q.from = Vector3(x, 600.0, z)
			q.to = Vector3(x, -40.0, z)
			var hit := space.intersect_ray(q)
			h[ix * nz + iz] = hit["position"].y if hit else -999.0
	var cells := {}
	for ix in range(SPAN, nx - SPAN):
		for iz in range(SPAN, nz - SPAN):
			var y := h[ix * nz + iz]
			var kind := ""
			var depth := 0.0
			if y < -900.0:
				# Open sea has no floor; a hole in the land has land around it.
				var dry := 0
				for o in [[-SPAN, 0], [SPAN, 0], [0, -SPAN], [0, SPAN]]:
					if h[(ix + o[0]) * nz + iz + o[1]] > 0.5:
						dry += 1
				if dry >= 3:
					kind = "none"
			else:
				var xa := h[(ix - SPAN) * nz + iz]
				var xb := h[(ix + SPAN) * nz + iz]
				var za := h[ix * nz + iz - SPAN]
				var zb := h[ix * nz + iz + SPAN]
				var dx := minf(xa, xb) - y
				var dz := minf(za, zb) - y
				if xa > -900.0 and xb > -900.0 and dx > DROP:
					kind = "slot"
					depth = dx
				if za > -900.0 and zb > -900.0 and dz > DROP and dz > depth:
					kind = "slot"
					depth = dz
			if kind == "":
				continue
			var x := X0 + ix * STEP
			var z := Z0 + iz * STEP
			var key := "%s %d %d" % [kind, floori(x / 40.0) * 40, floori(z / 40.0) * 40]
			if not cells.has(key):
				cells[key] = {"n": 0, "deep": 0.0, "at": Vector3(x, y, z)}
			cells[key]["n"] += 1
			if depth >= cells[key]["deep"]:
				cells[key]["deep"] = depth
				cells[key]["at"] = Vector3(x, y, z)
	var keys := cells.keys()
	keys.sort()
	for key in keys:
		var c: Dictionary = cells[key]
		q.from = Vector3(c["at"].x, 600.0, c["at"].z)
		q.to = Vector3(c["at"].x, -40.0, c["at"].z)
		var hit := space.intersect_ray(q)
		print("%s: %d samples, deepest %.1fm at %s on %s" % [key, c["n"], c["deep"], c["at"],
			world.get_path_to(hit["collider"]) if hit else "nothing"])
	get_tree().quit()
