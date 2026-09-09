extends SceneTree

## Dev probe: the highway's and the approach road's section, read off the
## generator's own height functions without regenerating anything. For every
## open station: the graded road level, the natural ground at the centre and
## at the shoulder line either side, so a cut reads as cut depth and a fill
## as drop. Lists the runs that call for a retaining wall (a cut deeper than
## `WALL_FROM` at the shoulder), a guardrail (a drop of more than `GUARD_FROM`
## at the shoulder) and a viaduct (a dip the road descends into and climbs
## out of again within `DIP_MAX_RUN` whose floor is more than `DIP_FROM`
## under the chord). Prints tables; writes nothing.

const Plan := preload("res://scripts/park_plan.gd")
const SHOULDER := 9.5
const WALL_FROM := 2.5
const GUARD_FROM := 1.5
const DIP_FROM := 5.0
const DIP_MAX_RUN := 300.0


func _initialize() -> void:
	var gen = load("res://tools/gen_props.gd").new()
	_plan_lines(gen)
	_corridor(gen)
	_failure_points(gen)
	var st: Array = gen._highway_stations()
	var open: PackedByteArray = gen._highway_open
	print("== highway: %d stations ==" % st.size())
	_section(gen, st, open, "highway")
	var ap: Array = Plan.approach_road_points()
	var ap_open := PackedByteArray()
	ap_open.resize(ap.size() - 1)
	ap_open.fill(1)
	print("== approach road: %d points ==" % ap.size())
	_section(gen, ap, ap_open, "approach")
	gen.free()
	quit()


func _failure_points(gen) -> void:
	print("== road-ground diagnostic points ==")
	for p in [Vector2(-9.4, 495.5), Vector2(-9.1, 503.3), Vector2(-8.1, 463.9),
			Vector2(193.8, 310.8), Vector2(213.2, 334.0),
			Vector2(-480.7806, -2063.505), Vector2(-470.7235, -2066.522),
			Vector2(305.4392, 1185.706), Vector2(320.003, 1179.298)]:
		var natural: float = gen._rebuild_natural_y(p)
		var cut: float = gen._town_ground_y(p)
		var rec: Array = gen._road_records_cut(p, natural)
		print("   %s natural %.2f road %.2f town %.2f world %.2f coast %.2f record %.2f found %s edge %.2f" % [
			p, natural, gen._road_ground_y(p), cut, gen._rebuild_world_reserve_y(p),
			gen._rebuild_coastal_reserve_y(p), float(rec[0]), rec[1], float(rec[2])])


func _section(gen, st: Array, open: PackedByteArray, label: String) -> void:
	var chain := 0.0
	var runs := {"wall_l": [], "wall_r": [], "guard_l": [], "guard_r": [], "fillwall_l": [], "fillwall_r": []}
	var cur := {}
	var chains := PackedFloat32Array()
	var naturals := PackedFloat32Array()
	for i in st.size():
		var p: Vector3 = st[i]
		if i > 0:
			chain += Vector2(p.x - st[i - 1].x, p.z - st[i - 1].z).length()
		chains.append(chain)
		var seg_open := (i < open.size() and open[i]) or (i > 0 and open[i - 1])
		var d := Vector2.ZERO
		if i + 1 < st.size():
			d = Vector2(st[i + 1].x - p.x, st[i + 1].z - p.z).normalized()
		elif i > 0:
			d = Vector2(p.x - st[i - 1].x, p.z - st[i - 1].z).normalized()
		var n := Vector2(-d.y, d.x)
		var c := Vector2(p.x, p.z)
		var nat_c: float = gen._rebuild_natural_y(c)
		var nat_l: float = gen._rebuild_natural_y(c + n * SHOULDER)
		var nat_r: float = gen._rebuild_natural_y(c - n * SHOULDER)
		naturals.append(nat_c)
		if not seg_open:
			continue
		var marks := {"wall_l": nat_l - p.y >= WALL_FROM, "wall_r": nat_r - p.y >= WALL_FROM,
			"guard_l": p.y - nat_l >= GUARD_FROM, "guard_r": p.y - nat_r >= GUARD_FROM,
			"fillwall_l": p.y - nat_l >= 6.0, "fillwall_r": p.y - nat_r >= 6.0}
		for k in marks:
			if marks[k]:
				if not cur.has(k):
					cur[k] = {"from": chain, "at": c, "max": 0.0}
				var depth: float = absf((nat_l if k.ends_with("_l") else nat_r) - p.y)
				cur[k]["max"] = maxf(float(cur[k]["max"]), depth)
			elif cur.has(k):
				cur[k]["to"] = chain
				runs[k].append(cur[k])
				cur.erase(k)
	for k in cur:
		cur[k]["to"] = chain
		runs[k].append(cur[k])
	for k in runs:
		var total := 0.0
		for r in runs[k]:
			total += float(r["to"]) - float(r["from"])
		print("%s %s: %d runs, %.0fm in all" % [label, k, runs[k].size(), total])
		for r in runs[k]:
			if float(r["to"]) - float(r["from"]) >= 40.0 or float(r["max"]) >= 4.0:
				print("   chain %5.0f..%5.0f (%.0fm) from (%.0f, %.0f): up to %.1fm" % [
					r["from"], r["to"], float(r["to"]) - float(r["from"]), r["at"].x, r["at"].y, r["max"]])
	# Dips: the road's own graded line descends and climbs again. For each
	# local maximum pair (i, j) with j - i within the run, the chord between
	# and the deepest station under it.
	var dips: Array = []
	var ys := PackedFloat32Array()
	for p in st:
		ys.append((p as Vector3).y)
	var i := 0
	while i < st.size():
		# Walk to the next local maximum.
		if not (i == 0 or ys[i] >= ys[i - 1]) or not (i == st.size() - 1 or ys[i] >= ys[i + 1]):
			i += 1
			continue
		var best: Dictionary = {}
		var j := i + 1
		while j < st.size() and chains[j] - chains[i] <= DIP_MAX_RUN:
			if (j == st.size() - 1 or ys[j] >= ys[j + 1]) and ys[j] >= ys[j - 1]:
				var deepest := 0.0
				var deep_k := i
				for k in range(i + 1, j):
					var t := (chains[k] - chains[i]) / maxf(chains[j] - chains[i], 0.001)
					var chord := lerpf(ys[i], ys[j], t)
					if chord - ys[k] > deepest:
						deepest = chord - ys[k]
						deep_k = k
				if deepest >= DIP_FROM and (best.is_empty() or deepest > float(best["depth"])):
					best = {"from": chains[i], "to": chains[j], "depth": deepest,
						"at": Vector2((st[deep_k] as Vector3).x, (st[deep_k] as Vector3).z),
						"y_from": ys[i], "y_to": ys[j], "floor": ys[deep_k],
						"natural": naturals[deep_k]}
			j += 1
		if not best.is_empty():
			dips.append(best)
		i += 1
	print("%s dips deeper than %.0fm under a chord within %.0fm: %d" % [label, DIP_FROM, DIP_MAX_RUN, dips.size()])
	for d in dips:
		print("   chain %5.0f..%5.0f (%.0fm): rims %.1f and %.1f, floor %.1f (natural %.1f) at (%.0f, %.0f), %.1fm under the chord" % [
			d["from"], d["to"], float(d["to"]) - float(d["from"]), d["y_from"], d["y_to"],
			d["floor"], d["natural"], d["at"].x, d["at"].y, d["depth"]])
	# The profile itself, coarse: every 200m of chain.
	print("%s profile (chain: road / natural centre / natural L / natural R):" % label)
	var next := 0.0
	for k in st.size():
		if chains[k] < next:
			continue
		next += 200.0
		var p: Vector3 = st[k]
		var d := Vector2.ZERO
		if k + 1 < st.size():
			d = Vector2(st[k + 1].x - p.x, st[k + 1].z - p.z).normalized()
		else:
			d = Vector2(p.x - st[k - 1].x, p.z - st[k - 1].z).normalized()
		var n := Vector2(-d.y, d.x)
		var c := Vector2(p.x, p.z)
		print("   %5.0f (%5.0f, %5.0f): %6.1f / %6.1f / %6.1f / %6.1f %s" % [chains[k], p.x, p.z, p.y,
			naturals[k], gen._rebuild_natural_y(c + n * SHOULDER), gen._rebuild_natural_y(c - n * SHOULDER),
			"" if (k < open.size() and open[k]) else "(tunnel)"])


## The plan lines after `fillet_polyline`: how many points, the tightest
## turn between consecutive chords, and the ground along the interchange's
## stub, which is the one new piece of road on ground nobody has read.
func _plan_lines(gen) -> void:
	var raw: Array = Plan.highway_path_raw()
	var line: Array = Plan.highway_path()
	print("== plan lines ==")
	print("highway: %d control points, %d after fillets" % [raw.size(), line.size()])
	var worst := 0.0
	var worst_at := Vector2.ZERO
	for i in range(1, line.size() - 1):
		var din: Vector2 = (line[i] - line[i - 1]).normalized()
		var dout: Vector2 = (line[i + 1] - line[i]).normalized()
		var turn := absf(din.angle_to(dout))
		if turn > worst:
			worst = turn
			worst_at = line[i]
	print("   largest turn between chords %.1f deg at (%.0f, %.0f)" % [rad_to_deg(worst), worst_at.x, worst_at.y])
	for corner in [Vector2(-80.0, -330.0), Vector2(10.0, 350.0), Vector2(0.0, 520.0), Vector2(-420.0, -1700.0)]:
		var best := INF
		for q in line:
			best = minf(best, (q as Vector2).distance_to(corner))
		print("   line passes %.1fm from the old corner (%.0f, %.0f)" % [best, corner.x, corner.y])
	var ap: Array = Plan.approach_road_points()
	print("approach road: %d points; crossing %s; stub end %s" % [ap.size(), Plan.approach_crossing(), ap[ap.size() - 1]])
	var cross: Vector3 = Plan.approach_crossing()
	var stub_end: Vector3 = ap[ap.size() - 1]
	for k in 12:
		var t := float(k) / 11.0
		var q := Vector2(lerpf(cross.x, stub_end.x, t), lerpf(cross.z, stub_end.z, t))
		var nat: float = gen._rebuild_natural_y(q)
		var d := Vector2(stub_end.x - cross.x, stub_end.z - cross.z).normalized()
		var n := Vector2(-d.y, d.x)
		print("   stub %4.0fm (%.0f, %.0f): road %.1f natural %.1f, at +-12m %.1f / %.1f" % [
			t * float(Plan.INTERCHANGE["stub"]), q.x, q.y, cross.y, nat,
			gen._rebuild_natural_y(q + n * 12.0), gen._rebuild_natural_y(q - n * 12.0)])
	for street in Plan.town_streets():
		var pts: Array = street["points"]
		print("street %s: %d points, from (%.1f, %.1f) to (%.1f, %.1f)" % [street["id"], pts.size(),
			(pts[0] as Vector2).x, (pts[0] as Vector2).y, (pts[pts.size() - 1] as Vector2).x, (pts[pts.size() - 1] as Vector2).y])


## The divided highway and its corridor as the generator builds them: the
## carriageways' split, the median, the ramps, the chunks, and the corridor
## mesh's cost, without writing a scene.
func _corridor(gen) -> void:
	var t0 := Time.get_ticks_msec()
	gen._highway_build()
	print("== divided highway (%d ms) ==" % (Time.get_ticks_msec() - t0))
	var a: Array = gen._highway_a
	var b: Array = gen._highway_b
	var m: PackedFloat32Array = gen._highway_m
	var split_max := 0.0
	var split_at := 0
	var narrow := 0
	for i in a.size():
		var d := absf((a[i] as Vector3).y - (b[i] as Vector3).y)
		if d > split_max:
			split_max = d
			split_at = i
		if m[i] < 5.0:
			narrow += 1
	print("   %d stations; median under 5m at %d; largest split %.1fm at station %d (%.0f, %.0f)" % [
		a.size(), narrow, split_max, split_at, (a[split_at] as Vector3).x, (a[split_at] as Vector3).z])
	var cx: Dictionary = gen._highway_crossing
	print("   crossing: A station %d at %.1fm, B station %d at %.1fm; approach deck at %.1f" % [
		cx["a"], (a[cx["a"]] as Vector3).y, cx["b"], (b[cx["b"]] as Vector3).y, Plan.approach_crossing().y])
	for ramp in gen._interchange_ramps():
		var pts: Array = ramp["points"]
		var worst := 0.0
		for i in pts.size() - 1:
			var run := (pts[i] as Vector3).distance_to(pts[i + 1])
			worst = maxf(worst, absf((pts[i + 1] as Vector3).y - (pts[i] as Vector3).y) / maxf(run, 0.1))
		print("   %s: %d stations, %s -> %s, steepest 1:%.0f" % [ramp["id"], pts.size(), pts[0], pts[pts.size() - 1],
			1.0 / maxf(worst, 0.0001)])
	t0 = Time.get_ticks_msec()
	var packed: Array = gen._road_chunks()
	var chunks: Array = packed[0]
	var groups: Dictionary = packed[1]
	print("   %d chunks in %d groups (%d ms)" % [chunks.size(), groups.size(), Time.get_ticks_msec() - t0])
	for root in groups:
		if (groups[root] as Array).size() > 1:
			var ids := {}
			for k in groups[root]:
				ids[chunks[k]["id"]] = true
			print("   group of %d chunks: %s" % [(groups[root] as Array).size(), ids.keys()])
	t0 = Time.get_ticks_msec()
	var mesh: ArrayMesh = gen._rebuild_road_corridor_mesh()
	var arrays: Array = mesh.surface_get_arrays(0)
	print("   corridor mesh: %d vertices in %d ms" % [(arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size(), Time.get_ticks_msec() - t0])
	# The section at a few stations, read back through the cut.
	for xz in [Vector2(-161.0, -850.0), Vector2(310.0, 207.0), Vector2(204.0, 322.0), Vector2(369.0, 1329.0)]:
		var best := 0
		var bd := INF
		for i in a.size():
			var c: Vector3 = gen._highway_cache[i]
			var d := Vector2(c.x, c.z).distance_to(xz)
			if d < bd:
				bd = d
				best = i
		var c: Vector3 = gen._highway_cache[best]
		var r: Vector2 = gen._highway_r[best]
		var line := ""
		for o in [-40.0, -30.0, -24.0, -20.0, -17.0, -15.0, -13.0, -11.0, -8.0, -4.0, 0.0, 4.0, 8.0, 11.0, 13.0, 15.0, 17.0, 20.0, 24.0, 30.0, 40.0]:
			var q := Vector2(c.x, c.z) + r * float(o)
			line += " %.1f" % gen._town_ground_y(q)
		print("   section at (%.0f, %.0f) m %.1f A %.1f B %.1f:%s" % [c.x, c.z, m[best], (a[best] as Vector3).y, (b[best] as Vector3).y, line])
