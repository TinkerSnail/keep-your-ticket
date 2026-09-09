extends SceneTree

## Dev probe: the coast highway's tunnels as a car will drive them, read off
## the generator's own stations without regenerating anything. For each
## tunnel: its length and the seconds it takes at driving speeds; the grade and
## bend of each carriageway through it, which the segmented bores now follow;
## and the heading change over the hundred metres past each portal, which is
## whether a portal frames the road ahead or swings off it. Prints tables;
## writes nothing.

const Plan := preload("res://scripts/park_plan.gd")
const HEADLAND_POINT := Vector2(-242.0, -295.0)


func _initialize() -> void:
	var gen = load("res://tools/gen_props.gd").new()
	var st: Array = gen._highway_stations()
	print("== tunnels in station order (the plan's drive order) ==")
	var n := 0
	for run in gen._highway_tunnels:
		var i0: int = run["from"]
		var i1: int = run["to"]
		var a: Vector3 = st[i0]
		var b: Vector3 = st[i1]
		var d := b - a
		var length := d.length()
		var flat := Vector2(d.x, d.z)
		var flat_len := flat.length()
		var dir := flat / flat_len
		print("tunnel %d: %.0fm from (%.0f, %.0f) %.0fm up to (%.0f, %.0f) %.0fm up, %d stations inside" % [
			n, length, a.x, a.z, a.y, b.x, b.z, b.y, i1 - i0 - 1])
		print("   at 60 km/h %4.1fs, at 80 km/h %4.1fs; exit beyond the player's 400m far plane from the entrance: %s" % [
			length / (60.0 / 3.6), length / (80.0 / 3.6), "yes" if length > 400.0 else "no"])
		for bore in [["A", gen._highway_a], ["B", gen._highway_b]]:
			var pts: Array = bore[1]
			var max_grade := 0.0
			var max_turn := 0.0
			var previous := NAN
			for i in range(i0, i1):
				var p0: Vector3 = pts[i]
				var p1: Vector3 = pts[i + 1]
				var seg := Vector2(p1.x - p0.x, p1.z - p0.z)
				max_grade = maxf(max_grade, absf(p1.y - p0.y) / maxf(seg.length(), 0.001))
				var heading := atan2(seg.x, seg.y)
				if not is_nan(previous):
					max_turn = maxf(max_turn, absf(wrapf(heading - previous, -PI, PI)))
				previous = heading
			print("   bore %s follows %d segments: steepest 1:%.0f, sharpest joint %.1f deg; 0.70m wall margin, 5.20m roof clearance" % [
				bore[0], i1 - i0, 1.0 / maxf(max_grade, 0.0001), rad_to_deg(max_turn)])
		var axis_deg := rad_to_deg(atan2(dir.x, dir.y))
		for end in [[i0, -1, "entrance (a)"], [i1, 1, "exit (b)"]]:
			var idx: int = end[0]
			var step: int = end[1]
			var label: String = end[2]
			var p0: Vector3 = st[idx]
			var here := Vector2(p0.x, p0.z)
			var walked := 0.0
			var j := idx
			var turn_max := 0.0
			var prev_h := axis_deg if step > 0 else axis_deg + 180.0
			while walked < 100.0 and j + step >= 0 and j + step < st.size():
				var q: Vector3 = st[j + step]
				var seg := Vector2(q.x - st[j].x, q.z - st[j].z)
				walked += seg.length()
				var h := rad_to_deg(atan2(seg.x, seg.y))
				var dh := wrapf(h - prev_h, -180.0, 180.0)
				turn_max = maxf(turn_max, absf(wrapf(h - (axis_deg if step > 0 else axis_deg + 180.0), -180.0, 180.0)))
				prev_h = h
				j += step
			var to_head := rad_to_deg(atan2(HEADLAND_POINT.x - here.x, HEADLAND_POINT.y - here.y))
			var to_plaza := rad_to_deg(atan2(-here.x, -here.y))
			var out_axis := axis_deg if step > 0 else axis_deg + 180.0
			print("   %s at (%.0f, %.0f): axis out %.0f deg; road swings %.0f deg within %.0fm; headland point is %.0f deg off axis, plaza %.0f deg off, at %.0fm and %.0fm" % [
				label, here.x, here.y, wrapf(out_axis, -180.0, 180.0), turn_max, walked,
				absf(wrapf(to_head - out_axis, -180.0, 180.0)), absf(wrapf(to_plaza - out_axis, -180.0, 180.0)),
				here.distance_to(HEADLAND_POINT), here.length()])
		n += 1
	print("== %d tunnels, %d stations ==" % [n, st.size()])
	if n != 5:
		push_error("expected the three north and two far-shore tunnel locations, got %d" % n)
		gen.free()
		quit(1)
		return
	gen.free()
	quit()
