extends Node

## Dev probe: how much of the park's ground is decided by the order the generator
## happens to ask for it, and how far the generator's intent stands from what was
## actually built. Written 2026-09-21 for the ground-ownership question in
## `technical.md`.
##
## A0, a control. Fingerprints every graded route per configuration, so A1's
## numbers can be trusted. A first pass primed the generator in all of them and
## measured a flat zero — the probe was varying nothing.
##
## A1, order sensitivity. `load(gen_props).new()` does not run the generator's own
## setup, so a fresh instance starts with every cache empty and this probe chooses
## what is graded before it asks. The decisive contrast is "cold" against
## "as-built": the outer highland consults D and F through `cached_only`, so it
## answers with route cuts only once those routes are graded. Forcing a single
## route first, with the setup then run, changes nothing — the setup imposes its
## own order regardless. What moves is cache state, not route order.
##
## A2, intent against what was built. The grid sampled through the nearest thing to
## a single composed entry point, then raycast against the standing world, and the
## signed delta reported. `_road_ground_y` resolves to the mainland underlay, so
## the size of that delta measures how little of the park's ground any one entry
## point answers, rather than a fault in it.
##
## Prints and returns 0; it is a measurement, not a verdict. Pass a step in metres
## after the tool name to change the grid; the default is 4m, which is at or below
## the lattice's own resolution over nearly all of the box. The east shoulders
## (1.25m x 2m) and P1's 2m refinement band are finer, so findings inside them are
## under-sampled at the default and want a finer re-run before they are believed.

const GEN_PATH := "res://tools/gen_props.gd"

## The program envelope padded by the embankment region's own 60m, so this covers
## the same ground `_embank_cells` does.
const BOX_MIN := Vector2(-272.0, -290.0)
const BOX_MAX := Vector2(282.0, 280.0)
const DEFAULT_STEP := 4.0
const CELL := 40.0

## From forty metres up, so a surface lying over the sample still counts, and deep
## enough to reach the cut corridor's floor.
const RAY_ABOVE := 40.0
const RAY_BELOW := 60.0
const WORLD_LAYER := 1
const SETTLE_FRAMES := 30

## Routes in the order the generator's own setup reaches them; each is also forced
## first once, on its own generator.
const ORDERS: Array[StringName] = [&"F", &"D", &"E", &"C"]

## The surfaces worth asking, because order dependence does not live in the same
## place as the composed entry point. `_road_ground_y` is the nearest thing to a
## single entry, but it resolves to `_town_ground_y`, the mainland *underlay*, so
## inside the park it is not the ground anyone stands on. The route priority and
## the `cached_only` guard live in the outer highland and the lowland surface, so
## those are sampled directly. "xz" takes two floats rather than a Vector2.
const ENTRIES := [
	{"name": "road_ground", "method": "_road_ground_y", "xz": false},
	{"name": "outer_highland", "method": "_rebuild_outer_highland_y", "xz": true,
		"min_x": 127.0, "min_z": -154.0, "max_z": 198.0},
	{"name": "lowland_surface", "method": "_rebuild_lowland_surface_y", "xz": false},
	{"name": "natural", "method": "_rebuild_natural_y", "xz": false},
]
const ENTRY := "_road_ground_y"
const BRANCH_NAMES := ["outer-highland band", "T3 cap", "T2 polygon", "road/coast/reserve"]

## A3's dispatch. The reproduction test asks a narrower question than A2: not
## "does one entry point answer the park's ground" (it does not), but "does the
## function that nominally owns each surface actually reproduce that surface".
## If every owner reproduces its own mesh, a field evaluated in a declared order
## reproduces today's ground and composition is only a question of which owner
## wins where. If an owner does not reproduce its own mesh, the ground there is
## not a function of plan position at all and no field can hold it.
const OWNERS := {
	"terrain_T2_lowland": {"method": "_rebuild_lowland_surface_y", "xz": false},
	"terrain_T6_outer_highland": {"method": "_rebuild_outer_highland_y", "xz": true},
	"terrain_world_mainland_reserve": {"method": "_rebuild_world_reserve_y", "xz": false},
	"terrain_world_coast_north": {"method": "_rebuild_coastal_reserve_y", "xz": false},
	"terrain_world_coast_south": {"method": "_rebuild_coastal_reserve_y", "xz": false},
	"terrain_road_corridor": {"method": "_road_ground_y", "xz": false},
}

var _step := DEFAULT_STEP


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 1:
		_step = maxf(0.5, float(args[1]))
	var points := _grid()
	print("ground field probe: %d samples at %.2fm over (%.0f, %.0f)..(%.0f, %.0f)" % [
		points.size(), _step, BOX_MIN.x, BOX_MIN.y, BOX_MAX.x, BOX_MAX.y])

	# Each configuration is [label, route forced first, run the generator's own
	# setup]. "cold" is the one that isolates `cached_only`: the outer highland
	# consults D and F only when they are already graded, so a surface sampled
	# before anything is graded and after should differ if that branch bites.
	# Priming in every configuration is what hid this in the first pass.
	var configs: Array = [
		["cold", &"", false],
		["as-built", &"", true],
	]
	for route in ORDERS:
		configs.append(["%s first" % route, route, true])
	var names: Array[String] = []
	for c in configs:
		names.append(c[0])

	print("")
	print("A0  can the probe actually vary the order? Fingerprint of every graded")
	print("    route per configuration. Identical rows mean the forcing does not")
	print("    bite, and A1's zeros would be measuring nothing.")
	var base_fp := {}
	for c in configs:
		var tag: String = c[0]
		var fp := _fingerprint(c[1], c[2])
		if tag == "as-built":
			base_fp = fp
		var diff: Array[String] = []
		for k in fp:
			if not base_fp.has(k) or absf(float(base_fp[k]) - float(fp[k])) > 0.001:
				diff.append(String(k))
		print("    %-10s %d routes graded, %s" % [tag, fp.size(),
			"same as as-built" if diff.is_empty() else "differs on %s" % ", ".join(diff)])
		if base_fp.is_empty():
			base_fp = fp

	print("")
	print("A1  order sensitivity, %d configurations: %s" % [names.size(), ", ".join(names)])
	var intent := PackedFloat32Array()
	for entry in ENTRIES:
		var domain := _domain(points, entry)
		if domain.is_empty():
			print("  %-16s no samples in its domain" % entry["name"])
			continue
		var fields: Array = []
		for c in configs:
			fields.append(_sample(c[1], domain, entry, c[2]))
		_report_spread(entry["name"], domain, fields)
		if entry["method"] == ENTRY:
			intent = fields[0]

	await _report_against_world(points, intent)
	_report_reproduction(points)
	get_tree().quit()


## One number per route: the sum of its graded stations' heights. If two
## configurations grade a route to different heights these differ, which is what
## makes A1's zeros trustworthy or not.
func _fingerprint(route: StringName, prime: bool) -> Dictionary:
	var gen: Object = load(GEN_PATH).new()
	if route != &"":
		for run in gen.call("_rebuild_district_build_runs"):
			if StringName(run["route"]) == route:
				gen.call("_rebuild_graded_route", run)
	if prime:
		_prime(gen)
	var out := {}
	for run in gen.call("_rebuild_district_build_runs"):
		var key := StringName(run["route"])
		var total: float = out.get(key, 0.0)
		for p in gen.call("_rebuild_graded_route", run):
			total += Vector3(p).y
		out[key] = total
	gen.free()
	return out


## The sub-grid a surface is defined over; outside it the answer is meaningless
## rather than wrong.
func _domain(points: PackedVector2Array, entry: Dictionary) -> PackedVector2Array:
	if not (entry.has("min_x") or entry.has("min_z") or entry.has("max_z")):
		return points
	var out := PackedVector2Array()
	for p in points:
		if entry.has("min_x") and p.x < float(entry["min_x"]):
			continue
		if entry.has("min_z") and p.y < float(entry["min_z"]):
			continue
		if entry.has("max_z") and p.y > float(entry["max_z"]):
			continue
		out.append(p)
	return out


func _grid() -> PackedVector2Array:
	var out := PackedVector2Array()
	var x := BOX_MIN.x
	while x <= BOX_MAX.x:
		var z := BOX_MIN.y
		while z <= BOX_MAX.y:
			out.append(Vector2(x, z))
			z += _step
		x += _step
	return out


## One generator, one forced route order, one pass over the grid. `route` empty
## replicates the generator's own setup order instead of forcing anything.
func _sample(route: StringName, points: PackedVector2Array,
		entry: Dictionary, prime := true) -> PackedFloat32Array:
	var gen: Object = load(GEN_PATH).new()
	var method: String = entry["method"]
	for needed in [method, "_rebuild_district_build_runs", "_rebuild_graded_route"]:
		if not gen.has_method(needed):
			push_error("gen_props has no %s; the probe is reading a renamed private" % needed)
			gen.free()
			get_tree().quit(1)
			return PackedFloat32Array()

	if route != &"":
		# Force this route to solve against an empty cache, which is what the
		# generator does to F and to nothing else.
		for run in gen.call("_rebuild_district_build_runs"):
			if StringName(run["route"]) == route:
				gen.call("_rebuild_graded_route", run)
	if prime:
		_prime(gen)

	var xz: bool = entry["xz"]
	var out := PackedFloat32Array()
	out.resize(points.size())
	for i in points.size():
		var p := points[i]
		out[i] = float(gen.call(method, p.x, p.y)) if xz else float(gen.call(method, p))
	gen.free()
	return out


## What the generator's own setup assigns, in its own order. Called after a forced
## route so that route is already cached, which is the whole point of the contrast.
func _prime(gen: Object) -> void:
	for pair in [
			["_frontier_r10_queue", "_frontier_r10_queue_from_source"],
			["_fairground_r4_queue", "_fairground_r4_queue_from_source"],
			["_highland_terrain_paths", "_highland_terrain_paths_from_sources"],
			["_family_terrain_paths", "_family_terrain_paths_from_source"]]:
		if gen.has_method(pair[1]):
			gen.set(pair[0], gen.call(pair[1]))


func _report_spread(label: String, points: PackedVector2Array, fields: Array) -> void:
	var spread := PackedFloat32Array()
	spread.resize(points.size())
	var cells := {}
	for i in points.size():
		var lo := INF
		var hi := -INF
		for f in fields:
			var v: float = f[i]
			lo = minf(lo, v)
			hi = maxf(hi, v)
		var s := hi - lo
		spread[i] = s
		if s > 0.01:
			var key := Vector2i(floori(points[i].x / CELL) * int(CELL),
				floori(points[i].y / CELL) * int(CELL))
			var rec: Array = cells.get(key, [0, 0.0])
			cells[key] = [int(rec[0]) + 1, maxf(float(rec[1]), s)]

	var moved := 0
	for s in spread:
		if s > 0.01:
			moved += 1
	print("  %-16s %6d samples, %4d move >1cm (%4.1f%%)" % [
		label, spread.size(), moved,
		100.0 * float(moved) / maxf(1.0, float(spread.size()))])
	_stats("      spread", spread)
	if cells.is_empty():
		print("      call order changes nothing here")
		return
	var keys := cells.keys()
	keys.sort_custom(func(a, b): return float(cells[a][1]) > float(cells[b][1]))
	print("      worst cells (40m):")
	for k in keys.slice(0, 8):
		print("        (%5d,%6d)  %4d samples, up to %6.2fm" % [
			k.x, k.y, int(cells[k][0]), float(cells[k][1])])


func _report_against_world(points: PackedVector2Array,
		intent: PackedFloat32Array) -> void:
	print("")
	print("A2  the nearest thing to a single entry point, against standing collision")
	print("    `_road_ground_y` resolves to `_town_ground_y`, the mainland underlay,")
	print("    so a large negative is not a fault in it: it is the measure of how")
	print("    little of the park's ground any one entry point actually answers.")
	if intent.is_empty():
		print("    no intent field; skipped")
		return
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame
	if Engine.has_singleton("ParkClock") or get_node_or_null("/root/ParkClock") != null:
		get_node("/root/ParkClock").running = false
	var world := get_tree().get_root().find_child("park_world", true, false)
	if world == null:
		print("    no park_world; skipped")
		return

	# Every ribbon is transparent to the ray. At a junction, hitting another road
	# answers whether two surfaces overlap, not whether either stands on terrain.
	var skip: Array[RID] = []
	for body in _bodies(world):
		if body.get_meta("points", PackedVector3Array()).size() >= 2:
			skip.append(body.get_rid())

	var space := get_viewport().get_world_3d().direct_space_state
	var delta := PackedFloat32Array()
	var missed := 0
	var cells := {}
	for i in points.size():
		var p := points[i]
		var q := PhysicsRayQueryParameters3D.create(
			Vector3(p.x, intent[i] + RAY_ABOVE, p.y),
			Vector3(p.x, intent[i] - RAY_BELOW, p.y), WORLD_LAYER)
		q.exclude = skip
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			missed += 1
			continue
		var d: float = intent[i] - float(hit["position"].y)
		delta.append(d)
		if absf(d) > 0.35:
			var key := Vector2i(floori(p.x / CELL) * int(CELL), floori(p.y / CELL) * int(CELL))
			var rec: Array = cells.get(key, [0, 0.0])
			cells[key] = [int(rec[0]) + 1, d if absf(d) > absf(float(rec[1])) else float(rec[1])]

	print("    %d hits, %d found no collision at all" % [delta.size(), missed])
	_stats("    signed delta", delta, true)
	if cells.is_empty():
		print("    nothing disagrees by more than 0.35m")
		return
	var keys := cells.keys()
	keys.sort_custom(func(a, b): return absf(float(cells[a][1])) > absf(float(cells[b][1])))
	print("    worst cells (40m), + means intent above what stands:")
	for k in keys.slice(0, 12):
		print("      (%5d,%6d)  %4d samples, worst %+7.2fm" % [
			k.x, k.y, int(cells[k][0]), float(cells[k][1])])


func _bodies(root: Node) -> Array[PhysicsBody3D]:
	var out: Array[PhysicsBody3D] = []
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is PhysicsBody3D:
			out.append(n)
		for c in n.get_children():
			stack.append(c)
	return out


func _stats(label: String, values: PackedFloat32Array, signed := false) -> void:
	if values.is_empty():
		print("%s: no samples" % label)
		return
	var sorted := values.duplicate()
	if signed:
		var mags := PackedFloat32Array()
		for v in sorted:
			mags.append(absf(v))
		mags.sort()
		sorted.sort()
		print("%s: median %+.3fm, |95th| %.3fm, min %+.3fm, max %+.3fm" % [
			label, sorted[sorted.size() / 2], mags[int(mags.size() * 0.95)],
			sorted[0], sorted[sorted.size() - 1]])
		return
	sorted.sort()
	print("%s: median %.3fm, 95th %.3fm, max %.3fm" % [
		label, sorted[sorted.size() / 2], sorted[int(sorted.size() * 0.95)],
		sorted[sorted.size() - 1]])


## A3, the reproduction test. Raycasts each plan point, notes which body the ray
## actually landed on, and compares that body's own height function against it.
## The world is already mounted by A2.
func _report_reproduction(points: PackedVector2Array) -> void:
	print("")
	print("A3  reproduction: does each surface's own function reproduce it?")
	var world := get_tree().get_root().find_child("park_world", true, false)
	if world == null:
		print("    no park_world; skipped")
		return
	var skip: Array[RID] = []
	for body in _bodies(world):
		if body.get_meta("points", PackedVector3Array()).size() >= 2:
			skip.append(body.get_rid())

	var space := get_viewport().get_world_3d().direct_space_state
	var by_owner := {}
	for p in points:
		var q := PhysicsRayQueryParameters3D.create(
			Vector3(p.x, RAY_ABOVE * 6.0, p.y),
			Vector3(p.x, -RAY_BELOW, p.y), WORLD_LAYER)
		q.exclude = skip
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			continue
		var owner: String = String(hit["collider"].name)
		var rec: Array = by_owner.get(owner, [])
		rec.append([p, float(hit["position"].y)])
		by_owner[owner] = rec

	var gen: Object = load(GEN_PATH).new()
	_prime(gen)
	var names := by_owner.keys()
	names.sort_custom(func(a, b): return by_owner[a].size() > by_owner[b].size())
	var reproduced := 0
	var total := 0
	var owned := 0
	var field_ok := 0
	var field_n := 0
	var unowned := 0
	var unowned_kinds := 0
	for owner in names:
		var hits: Array = by_owner[owner]
		total += hits.size()
		if not OWNERS.has(owner):
			unowned += hits.size()
			unowned_kinds += 1
			if hits.size() >= 5:
				print("  %-32s %6d hits  no height function owns this surface" % [
					owner, hits.size()])
			continue
		owned += hits.size()
		var spec: Dictionary = OWNERS[owner]
		var xz: bool = spec["xz"]
		var method: String = spec["method"]
		var diffs := PackedFloat32Array()
		var field_diffs := PackedFloat32Array()
		var worst := 0.0
		var worst_at := Vector2.ZERO
		for h in hits:
			var p: Vector2 = h[0]
			var y: float = float(gen.call(method, p.x, p.y)) if xz else float(gen.call(method, p))
			var d: float = y - float(h[1])
			diffs.append(d)
			if gen.has_method("_ground_field_y"):
				field_diffs.append(float(gen.call("_ground_field_y", p)) - float(h[1]))
			if absf(d) > absf(worst):
				worst = d
				worst_at = p
		var close := 0
		for d in diffs:
			if absf(d) < 0.05:
				close += 1
		reproduced += close
		var sorted := diffs.duplicate()
		var mags := PackedFloat32Array()
		for d in sorted:
			mags.append(absf(d))
		mags.sort()
		var fclose := 0
		var branch_miss := {}
		var branch_where := {}
		for i in field_diffs.size():
			if absf(field_diffs[i]) < 0.05:
				fclose += 1
			elif absf(diffs[i]) < 0.05 and gen.has_method("_ground_field_branch"):
				# the surface's own function got it right and the field did not:
				# which branch took the point?
				var b: int = int(gen.call("_ground_field_branch", hits[i][0]))
				branch_miss[b] = int(branch_miss.get(b, 0)) + 1
				var wh: Array = branch_where.get(b, [])
				if wh.size() < 6:
					wh.append(hits[i][0])
					branch_where[b] = wh
		field_ok += fclose
		field_n += field_diffs.size()
		print("  %-32s %6d hits  own fn %5.1f%% <5cm (median |d| %6.3fm)   declared-order field %5.1f%% <5cm" % [
			owner, hits.size(), 100.0 * float(close) / float(hits.size()),
			mags[mags.size() / 2],
			100.0 * float(fclose) / maxf(1.0, float(field_diffs.size()))])
		if not branch_miss.is_empty():
			var bits: Array[String] = []
			for b in [0, 1, 2, 3]:
				if branch_miss.has(b):
					bits.append("%s %d" % [BRANCH_NAMES[b], int(branch_miss[b])])
			print("      field lost points the own function got, by branch taken: %s" % ", ".join(bits))
			for b in branch_where:
				var pts: Array[String] = []
				for q in branch_where[b]:
					pts.append("(%.0f,%.0f)" % [q.x, q.y])
				print("        via %-20s %s" % [BRANCH_NAMES[b], " ".join(pts)])
	gen.free()
	print("")
	print("    Of %d standing samples, %d (%.1f%%) are on a surface with a height" % [
		total, owned, 100.0 * float(owned) / maxf(1.0, float(total))])
	print("    function, and %d of those (%.1f%%) are reproduced within 5cm." % [
		reproduced, 100.0 * float(reproduced) / maxf(1.0, float(owned))])
	print("    The other %d (%.1f%%), across %d kinds of body, are ground the player" % [
		unowned, 100.0 * float(unowned) / maxf(1.0, float(total)), unowned_kinds])
	print("    stands on that no function answers: embankments read back from emitted")
	print("    geometry, the east shoulders, decks, entrance ground and the headland.")
	print("    That split, not the agreement, is what sizes a field.")
	if field_n > 0:
		print("")
		print("    Declared-order field over the same %d owned samples: %d within 5cm (%.1f%%)." % [
			field_n, field_ok, 100.0 * float(field_ok) / float(field_n)])
		print("    This is the step-2 question: does one stated priority pick the same")
		print("    owner each surface picks for itself?")
