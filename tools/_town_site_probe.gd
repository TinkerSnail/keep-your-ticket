extends SceneTree

## Dev probe: the natural ground along the coast highway and across the town
## sites, read straight off the generator's height functions without
## regenerating anything, plus the towns' street stations as the generator
## will lay them. Prints tables; writes nothing.

const Plan := preload("res://scripts/park_plan.gd")


func _initialize() -> void:
	var gen = load("res://tools/gen_props.gd").new()
	print("== natural ground along the highway line, north coast ==")
	var pts: Array[Vector2] = Plan.highway_path()
	for i in pts.size():
		var q: Vector2 = pts[i]
		if q.y > -400.0:
			continue
		print("  (%6.0f, %6.0f)  inland %5.1f  natural %6.1f  valley %.2f" % [
			q.x, q.y, Plan.coast_inland(q), gen._rebuild_natural_y(q), Plan.north_valley_factor(q)])
	print("== the valley: natural ground by (inland, across) ==")
	for s in [10.0, 30.0, 60.0, 100.0, 150.0, 200.0, 250.0, 300.0, 400.0, 600.0]:
		var row := "  s %4.0f:" % s
		for t in [0.0, 40.0, 80.0, 120.0, 160.0, 200.0, 260.0, 320.0]:
			row += " %6.1f" % gen._rebuild_natural_y(Plan.valley_point(s, t))
		print(row)
	print("== the beach town shelf ==")
	for z in [320.0, 380.0, 440.0, 500.0]:
		var sx2: float = Plan.shore_x(z)
		var row2 := "  z %6.0f shore x %6.0f:" % [z, sx2]
		for d in [0.0, 10.0, 30.0, 40.0, 60.0, 90.0, 120.0]:
			row2 += " %5.2f" % gen._rebuild_natural_y(Vector2(sx2 + d, z))
		print(row2)
	print("== street stations ==")
	for street in gen._town_street_stations():
		var p: Array = street["points"]
		var lo := INF
		var hi := -INF
		var steepest := 0.0
		for i in p.size():
			lo = minf(lo, (p[i] as Vector3).y)
			hi = maxf(hi, (p[i] as Vector3).y)
			if i > 0:
				var run: float = Vector2((p[i] as Vector3).x, (p[i] as Vector3).z).distance_to(
					Vector2((p[i - 1] as Vector3).x, (p[i - 1] as Vector3).z))
				steepest = maxf(steepest, absf((p[i] as Vector3).y - (p[i - 1] as Vector3).y) / maxf(run, 0.01))
		print("  %-22s %3d stations  y %6.1f .. %6.1f  steepest 1:%.1f  from %s to %s" % [
			street["id"], p.size(), lo, hi, 1.0 / maxf(steepest, 0.001),
			Vector2((p[0] as Vector3).x, (p[0] as Vector3).z).round(),
			Vector2((p[p.size() - 1] as Vector3).x, (p[p.size() - 1] as Vector3).z).round()])
	print("== highway tunnels with the valley ==")
	var st: Array = gen._highway_stations()
	for run in gen._highway_tunnels:
		var a: Vector3 = st[run["from"]]
		var b: Vector3 = st[run["to"]]
		print("  %.0fm from (%.0f, %.0f) %.0fm up to (%.0f, %.0f) %.0fm up" % [
			run["length"], a.x, a.z, a.y, b.x, b.z, b.y])
	gen.free()
	quit()
