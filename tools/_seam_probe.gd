extends SceneTree

## Dev probe: the height the coast meshes and the mainland reserve each give
## the seam they share at x = SHORE_FROM_X, along the whole of it, without
## regenerating anything. The two are built from two functions that are meant
## to agree there vertex for vertex; where they do not, the seam is a step,
## and a step on a single-sided surface is a face the world does not have.
##
##   godot --headless --path . --script tools/_seam_probe.gd

const Plan := preload("res://scripts/park_plan.gd")


func _initialize() -> void:
	var gen: Object = load("res://tools/gen_props.gd").new()
	var x: float = Plan.SHORE_FROM_X
	var worst := 0.0
	var worst_z := 0.0
	var z: float = Plan.REBUILD_WORLD_LAND_FROM_Z
	print("z, coast, reserve, reserve - coast")
	while z <= Plan.REBUILD_WORLD_LAND_TO_Z:
		var p := Vector2(x, z)
		var coast: float = gen.call("_rebuild_coastal_reserve_y", p)
		var reserve: float = gen.call("_rebuild_world_reserve_y", p)
		var d := reserve - coast
		if absf(d) > worst:
			worst = absf(d)
			worst_z = z
		if int(z) % 200 == 0 or absf(d) > 0.5:
			print("%6.0f %8.2f %8.2f %7.2f" % [z, coast, reserve, d])
		z += 50.0
	print("worst seam step %.2fm at z %.0f" % [worst, worst_z])
	quit()
