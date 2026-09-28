extends Node

## Probe, 2026-09-27: did the palm trunk move from code to Blender unchanged?
##
## Until then `coastal_palm_trunk.gd` built a 14-ring, 8-sided tube along each
## trunk's course. Its shape now comes from `assets/source/props/palm_trunk.blend`
## and the script only bends it. This rebuilds the old tube from every trunk's
## own course and bend strength, the old code copied below, and measures how far
## each old vertex is from the nearest vertex of the trunk as the game now
## shows it, in metres at the palm's real size. Only meaningful while the
## Blender file holds the old tube (the lossless step); after the reshape it
## reports how far the new trunk strays from the old one.
##
##   godot --headless --path . tools/run.tscn -- _palm_trunk_migration_probe

const SCENES := [
	"res://scenes/world/approach_palms.tscn",
	"res://scenes/world/boardwalk_palms.tscn",
	"res://scenes/world/coastal_palm_tree_specimen.tscn",
	"res://scenes/world/classic_california_date_palm.tscn",
]


func _ready() -> void:
	var worst := 0.0
	var trunks := 0
	for path in SCENES:
		var root := (load(path) as PackedScene).instantiate() as Node3D
		add_child(root)
		for _i in 4:
			await get_tree().process_frame
		for node in root.find_children("*", "Node3D", true, false):
			if not node.has_node("trunk_course") or not node.has_node("derived_trunk"):
				continue
			var mi := node.get_node("derived_trunk") as MeshInstance3D
			if mi.mesh == null:
				print("%s: no trunk mesh" % root.get_path_to(node))
				continue
			var now: PackedVector3Array = mi.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
			var old := _old_tube((node.get_node("trunk_course") as Path3D).curve,
				float(node.get("bend_strength")))
			var scale := (node as Node3D).global_transform.basis.get_scale().x
			var far := 0.0
			for v in old:
				var best := INF
				for w in now:
					best = minf(best, v.distance_to(w))
				far = maxf(far, best)
			far *= scale
			worst = maxf(worst, far)
			trunks += 1
			print("%-44s %4d vertices (was %d)  farthest %.4f mm" % [
				String(root.get_path_to(node)), now.size(), old.size(), far * 1000.0])
		root.queue_free()
	print("%d trunks; the farthest any old vertex lies from the new trunk: %.4f mm" % [
		trunks, worst * 1000.0])
	get_tree().quit()


## The tube `coastal_palm_trunk.gd` built until 2026-09-27, in the trunk's own
## one-metre frame.
func _old_tube(curve: Curve3D, bend_strength: float) -> PackedVector3Array:
	var out := PackedVector3Array()
	var length := curve.get_baked_length()
	for ring in 14:
		var t := float(ring) / 13.0
		var centre: Vector3 = curve.sample_baked(length * t, true)
		centre.x *= bend_strength
		centre.z *= bend_strength
		var epsilon := minf(0.025, length * 0.04)
		var before: Vector3 = curve.sample_baked(maxf(0.0, length * t - epsilon), true)
		var after: Vector3 = curve.sample_baked(minf(length, length * t + epsilon), true)
		var tangent := (after - before).normalized()
		if tangent.length_squared() < 0.5:
			tangent = Vector3.UP
		tangent = Vector3(tangent.x * bend_strength, tangent.y, tangent.z * bend_strength).normalized()
		var side := tangent.cross(Vector3.FORWARD).normalized()
		if side.length_squared() < 0.5:
			side = Vector3.RIGHT
		var forward := side.cross(tangent).normalized()
		var radius := lerpf(0.015, 0.012, t) + 0.006 * pow(maxf(0.0, 1.0 - t / 0.13), 2.0)
		for k in 8:
			var angle := TAU * float(k) / 8.0
			out.append(centre + (side * cos(angle) + forward * sin(angle)) * radius)
	return out
