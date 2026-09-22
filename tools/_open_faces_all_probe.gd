extends Node

## Dev probe: every open face `footprint_test` counts, in full, grouped by
## 40m cell, so the remainder after a stitch can be read by place. A copy of
## that test's open-face check with its printing changed; not a test.

const Plan := preload("res://scripts/park_plan.gd")
const LighthouseRegrade := preload("res://scripts/lighthouse_regrade_source.gd")
const EPS := 0.12
const CROSSING_CAPTURE := 12.0
const PROTECTED_MARGIN := 1.0

var _fails: Array[String] = []

func _ready() -> void:
	_check_open_faces()
	get_tree().quit()

func _check_open_faces() -> void:
	var ground: Node = load("res://scenes/world/park_groundworks.tscn").instantiate()
	var edges := {}
	var triangles := 0
	for name in ["terrain_world_mainland_reserve", "terrain_world_coast_north",
			"terrain_world_coast_south", "terrain_road_corridor"]:
		var node: Node = ground.find_child(name, true, false)
		if node == null:
			_fail("%s is not in the groundworks scene" % name)
			continue
		var surface := node.find_child("surface", false, false) as MeshInstance3D
		if surface == null or surface.mesh == null:
			_fail("%s has no surface mesh" % name)
			continue
		var xf := Transform3D.IDENTITY
		var walk: Node = surface
		while walk != null and walk != ground:
			if walk is Node3D:
				xf = (walk as Node3D).transform * xf
			walk = walk.get_parent()
		for si in surface.mesh.get_surface_count():
			var arrays: Array = surface.mesh.surface_get_arrays(si)
			var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			# A SurfaceTool mesh committed without `index()` carries no index
			# array at all; then every three vertices are one triangle.
			var index := PackedInt32Array()
			if arrays[Mesh.ARRAY_INDEX] != null:
				index = arrays[Mesh.ARRAY_INDEX]
			var n := index.size() if index.size() > 0 else verts.size()
			for i in range(0, n, 3):
				var tri: Array[Vector3] = []
				for k in 3:
					var vi: int = index[i + k] if index.size() > 0 else i + k
					tri.append(xf * verts[vi])
				for k in 3:
					_count_edge(edges, tri[k], tri[(k + 1) % 3], name)
				triangles += 1
	var stray: Array = []
	for key in edges:
		var rec: Array = edges[key]
		if int(rec[0]) == 1:
			stray.append(rec)
	var mids := {}
	for rec in stray:
		var mk := _mid_key(rec[1], rec[2])
		mids[mk] = int(mids.get(mk, 0)) + 1
	# A stray whose twin sits a few centimetres off — a wall's side edge at a
	# shore vertex the clipper placed twice, a centimetre apart — is closed
	# for any purpose the eye has; pair those by proximity.
	var near_paired := {}
	for i in stray.size():
		if near_paired.has(i):
			continue
		var a1: Vector3 = stray[i][1]
		var b1: Vector3 = stray[i][2]
		for j in range(i + 1, stray.size()):
			if near_paired.has(j):
				continue
			var a2: Vector3 = stray[j][1]
			var b2: Vector3 = stray[j][2]
			if (a1.distance_to(a2) < 0.3 and b1.distance_to(b2) < 0.3) \
					or (a1.distance_to(b2) < 0.3 and b1.distance_to(a2) < 0.3):
				near_paired[i] = true
				near_paired[j] = true
				break
	# A T-junction (2026-09-05): the road corridor's boundary is its rows'
	# outer vertices, and the lattice cell clipped against it carries a
	# vertex wherever a lattice line crosses that edge, so along the whole
	# corridor one of its edges faces two or three of the lattice's. Closed
	# if the short edges tile the long one within a hand, with their ends on
	# it: collinear in plan and on its chord in height.
	var t_closed := _pair_t_junctions(stray, near_paired, mids)
	var open: Array = []
	var length := 0.0
	# The coast meshes ramp from the strip's −6 to the reserve's level over
	# |z| 170..260, inside and just outside the envelope; that ramp is the
	# working strip's own hand-over and is covered by the park's ground.
	var margin := 45.0
	for si in stray.size():
		var rec: Array = stray[si]
		var a: Vector3 = rec[1]
		var b: Vector3 = rec[2]
		if int(mids[_mid_key(a, b)]) >= 2 or near_paired.has(si) or t_closed.has(si):
			continue
		if maxf(a.y, b.y) < Plan.WATER_TOP + 1.0:
			continue
		# A sliver: the clipper leaves the odd triangle a few centimetres
		# across at a cell corner on the outline, the generator drops it as
		# degenerate, and its neighbour's edge is left unpaired. Nothing to
		# see through at that size.
		if a.distance_to(b) < 0.3:
			continue
		# A wall's side edge, vertical: two panels meeting a hair apart at a
		# shore vertex. The ground's own edge above it is what the census
		# counts; a hairline between panels is nothing to see through.
		if Vector2(a.x - b.x, a.z - b.z).length() < 0.3:
			continue
		var m := (a + b) * 0.5
		if m.x > Plan.REBUILD_FOOTPRINT_MIN_X - margin and m.x < Plan.REBUILD_FOOTPRINT_MAX_X + margin \
				and m.z > Plan.REBUILD_FOOTPRINT_MIN_Z - margin and m.z < Plan.REBUILD_FOOTPRINT_MAX_Z + margin:
			continue
		open.append(rec)
		length += a.distance_to(b)
	ground.free()
	if open.is_empty():
		print("  terrain: no open face above the water (%d triangles, %d boundary edges)" % [
			triangles, stray.size()])
		return
	_fail("the terrain has %d open faces above the water, %.0fm in all" % [open.size(), length])
	# Where they are, by the line they lie on, so a seam reads as a seam and
	# a world edge as a world edge rather than as 371 coordinates.
	var classes := {}
	for rec in open:
		var a: Vector3 = rec[1]
		var b: Vector3 = rec[2]
		var label := "elsewhere"
		if absf(a.x - Plan.SHORE_FROM_X) < 0.05 and absf(b.x - Plan.SHORE_FROM_X) < 0.05:
			label = "coast seam x %.0f" % Plan.SHORE_FROM_X
		elif absf(a.z - Plan.REBUILD_WORLD_LAND_FROM_Z) < 0.05 and absf(b.z - Plan.REBUILD_WORLD_LAND_FROM_Z) < 0.05:
			label = "world north edge"
		elif absf(a.z - Plan.REBUILD_WORLD_LAND_TO_Z) < 0.05 and absf(b.z - Plan.REBUILD_WORLD_LAND_TO_Z) < 0.05:
			label = "world south edge"
		elif absf(a.x - Plan.REBUILD_WORLD_LAND_TO_X) < 0.05 and absf(b.x - Plan.REBUILD_WORLD_LAND_TO_X) < 0.05:
			label = "world east edge"
		if not classes.has(label):
			classes[label] = {"count": 0, "length": 0.0, "z_lo": INF, "z_hi": -INF,
				"x_lo": INF, "x_hi": -INF, "sample": rec}
		var c: Dictionary = classes[label]
		c["count"] = int(c["count"]) + 1
		c["length"] = float(c["length"]) + a.distance_to(b)
		c["z_lo"] = minf(float(c["z_lo"]), minf(a.z, b.z))
		c["z_hi"] = maxf(float(c["z_hi"]), maxf(a.z, b.z))
		c["x_lo"] = minf(float(c["x_lo"]), minf(a.x, b.x))
		c["x_hi"] = maxf(float(c["x_hi"]), maxf(a.x, b.x))
	var cells := {}
	for rec in open:
		var m: Vector3 = ((rec[1] as Vector3) + (rec[2] as Vector3)) * 0.5
		var key := "%-32s %5d %5d" % [rec[3], floori(m.x / 40.0) * 40, floori(m.z / 40.0) * 40]
		if not cells.has(key):
			cells[key] = {"n": 0, "len": 0.0, "eg": rec}
		cells[key]["n"] += 1
		cells[key]["len"] += (rec[1] as Vector3).distance_to(rec[2])
	var keys := cells.keys()
	keys.sort()
	for key in keys:
		print("%s: %2d edges %6.1fm e.g. %s -> %s" % [key, cells[key]["n"], cells[key]["len"],
			cells[key]["eg"][1], cells[key]["eg"][2]])
	return
	# And by mesh, with a few in full, since a crack along the road corridor
	# is one thing from the corridor's side and another from the lattice's.
	var by_mesh := {}
	for rec in open:
		by_mesh[rec[3]] = int(by_mesh.get(rec[3], 0)) + 1
	print("    by mesh: %s" % [by_mesh])
	for i in mini(open.size(), 8):
		var rec: Array = open[i]
		print("      %s %.2fm %s to %s" % [rec[3], (rec[1] as Vector3).distance_to(rec[2]), rec[1], rec[2]])
		# What the T-junction rule saw: every other-mesh stray touching an
		# end, with the other end's offset from its chord.
		var a: Vector3 = rec[1]
		var b: Vector3 = rec[2]
		for other in stray:
			if other[3] == rec[3]:
				continue
			var c: Vector3 = other[1]
			var d: Vector3 = other[2]
			for pair in [[a, b], [b, a]]:
				var v: Vector3 = pair[0]
				var far: Vector3 = pair[1]
				if c.distance_to(v) > 0.05 and d.distance_to(v) > 0.05:
					continue
				var cd := Vector2(d.x - c.x, d.z - c.z)
				var t := Vector2(far.x - c.x, far.z - c.z).dot(cd) / maxf(cd.length_squared(), 0.0001)
				var foot := Vector3(c.x, 0.0, c.z).lerp(Vector3(d.x, 0.0, d.z), t)
				print("        touches %s %.2fm %s to %s: far end t=%.3f, %.3fm off in plan, %.3fm off in height" % [
					other[3], c.distance_to(d), c, d, t, Vector2(far.x - foot.x, far.z - foot.z).length(),
					far.y - lerpf(c.y, d.y, t)])


## Stray edges closed as T-junctions: a stray is closed when strays of
## other meshes collinear with it tile its whole length, within 15cm. The
## partners may overlap its ends rather than lie within them, since the
## clipper drops collinear vertices from a cut cell's outline and the two
## meshes' vertices along a shared straight edge interleave rather than
## nest (2026-09-06). Collinear means both of a partner's ends within 12cm
## of this stray's line in plan and 30cm of its chord in height; the height
## allows for the range rise's metre-scale grain across a 4m chord.
func _pair_t_junctions(stray: Array, near_paired: Dictionary, mids: Dictionary) -> Dictionary:
	var closed := {}
	var buckets := {}
	for i in stray.size():
		var a: Vector3 = stray[i][1]
		var b: Vector3 = stray[i][2]
		var lo := Vector2i(floori(minf(a.x, b.x) / 16.0), floori(minf(a.z, b.z) / 16.0))
		var hi := Vector2i(floori(maxf(a.x, b.x) / 16.0), floori(maxf(a.z, b.z) / 16.0))
		for gx in range(lo.x, hi.x + 1):
			for gz in range(lo.y, hi.y + 1):
				var key := Vector2i(gx, gz)
				if not buckets.has(key):
					buckets[key] = []
				(buckets[key] as Array).append(i)
	for i in stray.size():
		var a: Vector3 = stray[i][1]
		var b: Vector3 = stray[i][2]
		var run := Vector2(b.x - a.x, b.z - a.z).length()
		if run < 0.05:
			continue
		var lo := Vector2i(floori(minf(a.x, b.x) / 16.0), floori(minf(a.z, b.z) / 16.0))
		var hi := Vector2i(floori(maxf(a.x, b.x) / 16.0), floori(maxf(a.z, b.z) / 16.0))
		var spans: Array = []
		var seen := {}
		for gx in range(lo.x, hi.x + 1):
			for gz in range(lo.y, hi.y + 1):
				var key := Vector2i(gx, gz)
				if not buckets.has(key):
					continue
				for j in buckets[key]:
					# Partners of any mesh, its own included: two cut cells'
					# pieces meet along a lattice line with different vertices.
					if j == i or seen.has(j):
						continue
					seen[j] = true
					var c: Vector3 = stray[j][1]
					var d: Vector3 = stray[j][2]
					# Collinear, judged on the longer chord so a short one's
					# slope is never extrapolated over the long one.
					var longer := c.distance_to(d) > a.distance_to(b)
					if longer:
						if _on_line(a, c, d) == INF or _on_line(b, c, d) == INF:
							continue
					elif _on_line(c, a, b) == INF or _on_line(d, a, b) == INF:
						continue
					var cd := Vector2(b.x - a.x, b.z - a.z)
					var tc := Vector2(c.x - a.x, c.z - a.z).dot(cd) / (run * run)
					var td := Vector2(d.x - a.x, d.z - a.z).dot(cd) / (run * run)
					var t0 := clampf(minf(tc, td), 0.0, 1.0)
					var t1 := clampf(maxf(tc, td), 0.0, 1.0)
					if t1 - t0 > 0.001:
						spans.append([t0, t1])
		if spans.is_empty():
			continue
		spans.sort_custom(func(p: Array, q: Array) -> bool: return float(p[0]) < float(q[0]))
		var reached := 0.0
		var whole := true
		for span in spans:
			if float(span[0]) * run > reached + 0.15:
				whole = false
				break
			reached = maxf(reached, float(span[1]) * run)
		if whole and reached >= run - 0.15:
			closed[i] = true
	return closed


## Where a point lies along a chord's line as a fraction, beyond its ends
## included, or INF if it is more than 12cm off the line in plan or 30cm
## off the chord's height at that fraction.
func _on_line(p: Vector3, c: Vector3, d: Vector3) -> float:
	var cd := Vector2(d.x - c.x, d.z - c.z)
	var run := cd.length()
	if run < 0.01:
		return INF
	var t := Vector2(p.x - c.x, p.z - c.z).dot(cd) / (run * run)
	var foot := Vector3(c.x, 0.0, c.z).lerp(Vector3(d.x, 0.0, d.z), t)
	if Vector2(p.x - foot.x, p.z - foot.z).length() > 0.12:
		return INF
	if absf(p.y - lerpf(c.y, d.y, t)) > 0.30:
		return INF
	return t


func _count_edge(edges: Dictionary, a: Vector3, b: Vector3, mesh := "") -> void:
	var qa := Vector3i((a * 100.0).round())
	var qb := Vector3i((b * 100.0).round())
	var key := ""
	if qa.x < qb.x or (qa.x == qb.x and (qa.z < qb.z or (qa.z == qb.z and qa.y <= qb.y))):
		key = "%d,%d,%d|%d,%d,%d" % [qa.x, qa.y, qa.z, qb.x, qb.y, qb.z]
	else:
		key = "%d,%d,%d|%d,%d,%d" % [qb.x, qb.y, qb.z, qa.x, qa.y, qa.z]
	if edges.has(key):
		var rec: Array = edges[key]
		rec[0] = int(rec[0]) + 1
	else:
		edges[key] = [1, a, b, mesh]


func _mid_key(a: Vector3, b: Vector3) -> String:
	var m := (a + b) * 0.5
	return "%d,%d,%d" % [roundi(m.x / 0.25), roundi(m.y / 0.25), roundi(m.z / 0.25)]


func _check_route_handoffs() -> void:
	var parking := _run(&"a_parking_arrival")
	var entrance := _run(&"a_entrance")
	var headland := _run(&"a_headland")
	var lighthouse := _run(&"a_lighthouse_loop")
	var hub := _run(&"a_hub_ring")
	if parking.is_empty() or entrance.is_empty() or headland.is_empty() \
			or lighthouse.is_empty() or hub.is_empty():
		return
	_expect_near("parking arrival outer end", parking[0],
		Vector2(0.0, Plan.ARRIVAL_AXIS_TO_Z))
	_expect_near("parking arrival to apron", parking[-1], entrance[0])
	_expect_near("route A begins at the apron", entrance[0],
		Vector2(0.0, Plan.APRON_Z))
	_expect_near("route A enters the hub", entrance[-1], Vector2(0.0, 18.0))
	_expect_near("route A leaves the hub", headland[0], Vector2(0.0, -18.0))
	_expect_near("route A reaches the lighthouse loop", headland[-1], lighthouse[0])
	if hub[0].distance_to(hub[-1]) > EPS or lighthouse[0].distance_to(lighthouse[-1]) > EPS:
		_fail("one of route A's two destination loops is open")

	var north := _run(&"b_north_return")
	var waterfront := _run(&"b_waterfront")
	var south := _run(&"b_south_return")
	if not north.is_empty() and not waterfront.is_empty() and not south.is_empty():
		var ride_loop := _boardwalk_ride_loop()
		if ride_loop.is_empty():
			_fail("the north Boardwalk ride loop is missing")
		elif _nearest_on_run(north[-1], ride_loop)["distance"] > EPS:
			_fail("B north return misses the editor-owned ride loop")
		_expect_near("B waterfront to south return", waterfront[-1], south[0])


func _boardwalk_ride_loop() -> Array[Vector2]:
	var out: Array[Vector2] = []
	var packed: PackedScene = load("res://scenes/world/boardwalk_north_ride_park.tscn")
	if packed == null:
		return out
	var root := packed.instantiate()
	var path := root.get_node_or_null("public_ride_loop") as Path3D
	if path != null and path.curve != null:
		for i in path.curve.point_count:
			var p := path.curve.get_point_position(i)
			out.append(Vector2(p.x, p.z))
		if path.curve.closed and not out.is_empty():
			out.append(out[0])
	root.free()
	return out


func _check_grand_circuit() -> void:
	var grand3: Array[Vector3] = Plan.grand_tram_loop(16)
	var grand := _xz(grand3)
	if grand.size() < 4 or grand[0].distance_to(grand[-1]) > EPS:
		_fail("the Grand Circuit is not a closed loop")
		return

	var lane_half: float = Plan.GRAND_TRAM_LANE_W * 0.5
	var nt1: Dictionary = Plan.REBUILD_PROTECTED_ZONES[&"NT-1"]
	var nt2: Dictionary = Plan.REBUILD_PROTECTED_ZONES[&"NT-2"]
	var nt1_clear := INF
	var nt2_clear := INF
	for point in grand:
		nt1_clear = minf(nt1_clear, _point_rect_distance(point,
			nt1["min"], nt1["max"]))
		nt2_clear = minf(nt2_clear, _point_ellipse_distance(point,
			nt2["centre"], nt2["radii"]))
	if nt1_clear < lane_half + PROTECTED_MARGIN:
		_fail("Grand Circuit leaves only %.2fm centreline clearance to NT-1" % nt1_clear)
	if nt2_clear < lane_half + PROTECTED_MARGIN:
		_fail("Grand Circuit leaves only %.2fm centreline clearance to NT-2" % nt2_clear)
	print("  Grand Circuit edge clearance: NT-1 %.2fm, NT-2 %.2fm" % [
		nt1_clear - lane_half, nt2_clear - lane_half])

	for station in Plan.GRAND_TRAM_STATIONS:
		var near := _nearest_on_run(Vector2(station["at"].x, station["at"].z), grand)
		if near["distance"] > 0.75:
			_fail("Grand Circuit station %s is %.2fm off its lane" % [
				station["id"], near["distance"]])

	var crossings := {}
	for crossing in Plan.GRAND_TRAM_CROSSINGS:
		var id: StringName = crossing["id"]
		var at := Vector2(crossing["at"].x, crossing["at"].z)
		var pedestrian := _run(crossing["pedestrian"])
		var road_hit := _nearest_on_run(at, grand)
		var walk_hit := _nearest_on_run(at, pedestrian)
		if road_hit["distance"] > 0.9 or walk_hit["distance"] > 0.9:
			_fail("crossing %s is not on both of its named routes" % id)
		var angle := _crossing_angle(road_hit["tangent"], walk_hit["tangent"])
		if angle < 30.0:
			_fail("crossing %s meets at only %.1f degrees" % [id, angle])
		if bool(crossing.get("grade_separated", false)):
			var road_y := _height_on_run3(at, grand3)
			var walk_y := _height_on_run3(at, _build_run3(crossing["pedestrian"]))
			var fixed_clearance := road_y \
				- float(crossing["fixed_structure_depth"]) - walk_y
			if fixed_clearance + EPS < float(crossing["minimum_fixed_clearance_metres"]):
				_fail("crossing %s has only %.2fm fixed clearance" % [id, fixed_clearance])
		var captures: Array = crossing.get("captures", [crossing["pedestrian"]])
		for captured in captures:
			crossings[captured] = at

	# Any overlap between a pedestrian route and the vehicle envelope must be
	# captured by one of the crossings above. This is what distinguishes a
	# deliberate crossing from the former near-tangent shared lanes.
	for run in Plan.rebuild_route_runs():
		var points: Array = run["points"]
		var hit := _nearest_between_runs(grand, points)
		var envelope: float = lane_half + float(run["width"]) * 0.5
		if hit["distance"] >= envelope:
			continue
		if not crossings.has(run["id"]):
			_fail("Grand Circuit overlaps unregistered route %s by %.2fm" % [
				run["id"], envelope - hit["distance"]])
			continue
		if hit["at"].distance_to(crossings[run["id"]]) > CROSSING_CAPTURE:
			_fail("Grand Circuit's overlap with %s escapes its controlled crossing" % run["id"])
	print("  %d controlled Grand Circuit crossings" % Plan.GRAND_TRAM_CROSSINGS.size())


func _check_arrival_scene() -> void:
	var packed: PackedScene = load("res://scenes/world/entrance.tscn")
	var root: Node = packed.instantiate()
	var cars := root.find_children("car_*", "Node3D", true, false)
	if cars.size() != 42:
		_fail("split parking has %d cars, expected 42" % cars.size())
	for car in cars:
		var p: Vector3 = car.position
		if absf(p.x) < Plan.PARKING_INNER_X + 5.5:
			_fail("%s intrudes into the central parking walk at x=%.2f" % [car.name, p.x])
		if p.z < Plan.PARKING_FROM_Z or p.z > Plan.PARKING_TO_Z:
			_fail("%s sits outside its parking field at z=%.2f" % [car.name, p.z])
	for required in ["parking_arrival_bed", "lot_ground_west", "lot_ground_east",
			"apron_rail_west", "apron_rail_east"]:
		if root.find_child(required, true, false) == null:
			_fail("expanded arrival is missing %s" % required)
	if root.find_child("apron_rail", true, false) != null:
		_fail("the obsolete full-width apron rail still exists")
	if root.find_children("parking_crosswalk_*", "Node3D", true, false).size() != 7:
		_fail("the parking/Grand Circuit crossing is not fully marked")
	root.free()
	print("  split parking keeps a %.0fm clear central arrival" % [
		Plan.PARKING_INNER_X * 2.0])


func _check_retired_geometry() -> void:
	var thresholds: Node = load("res://scenes/world/thresholds.tscn").instantiate()
	if not thresholds.find_children("way_*", "Node", true, false).is_empty():
		_fail("an obsolete X1-X4 threshold still mounts across routes A, C, or D")
	thresholds.free()
	var east: Node = load("res://scenes/world/east_cascade.tscn").instantiate()
	for retired in ["kiddie_arrival_path", "kiddie_arrival_end_guard",
			"kiddie_train", "east_swing_deck", "east_carousel_deck"]:
		if east.find_child(retired, true, false) != null:
			_fail("demolition geometry %s still survives in east_cascade" % retired)
	east.free()
	var program: Node = load("res://scenes/world/park_program.tscn").instantiate()
	for required in ["R5_outer_00", "R7_deck", "R13_rail_00",
			"R14_rail_00", "P1_lighthouse_tower", "P2_funhouse_back"]:
		if program.find_child(required, true, false) == null:
			_fail("the atlas program is missing %s" % required)
	program.free()
	var ground: Node = load("res://scenes/world/park_groundworks.tscn").instantiate()
	if ground.find_child("terrain_T6_outer_highland", true, false) == null:
		_fail("the expanded eastern highland reserve is not mounted")
	ground.free()


func _run(id: StringName) -> Array:
	for run in Plan.rebuild_route_runs():
		if run["id"] == id:
			return run["points"]
	_fail("missing plan route %s" % id)
	return []


func _build_run3(id: StringName) -> Array:
	for run in Plan.rebuild_build_runs():
		if run["id"] == id:
			return run["points"]
	_fail("missing three-dimensional build route %s" % id)
	return []


func _xz(points: Array[Vector3]) -> Array:
	var out := []
	for point in points:
		out.append(Vector2(point.x, point.z))
	return out


func _expect_near(label: String, a: Vector2, b: Vector2) -> void:
	if a.distance_to(b) > EPS:
		_fail("%s misses by %.2fm" % [label, a.distance_to(b)])


func _nearest_on_run(point: Vector2, points: Array) -> Dictionary:
	if points.size() < 2:
		return {"distance": INF, "at": point, "tangent": Vector2.RIGHT}
	var best := {"distance": INF, "at": point, "tangent": Vector2.RIGHT}
	for i in points.size() - 1:
		var a: Vector2 = points[i]
		var b: Vector2 = points[i + 1]
		var q := _nearest_on_segment(point, a, b)
		var d := point.distance_to(q)
		if d < best["distance"]:
			best = {"distance": d, "at": q, "tangent": (b - a).normalized()}
	return best


func _height_on_run3(point: Vector2, points: Array) -> float:
	var best_distance := INF
	var best_height := 0.0
	for i in points.size() - 1:
		var a: Vector3 = points[i]
		var b: Vector3 = points[i + 1]
		var a2 := Vector2(a.x, a.z)
		var b2 := Vector2(b.x, b.z)
		var ab := b2 - a2
		var t := clampf((point - a2).dot(ab) /
			maxf(ab.length_squared(), 0.001), 0.0, 1.0)
		var q := a2.lerp(b2, t)
		if point.distance_to(q) < best_distance:
			best_distance = point.distance_to(q)
			best_height = lerpf(a.y, b.y, t)
	return best_height


func _nearest_between_runs(a: Array, b: Array) -> Dictionary:
	var best := {"distance": INF, "at": Vector2.ZERO}
	for i in a.size() - 1:
		for j in b.size() - 1:
			var hit = Geometry2D.segment_intersects_segment(a[i], a[i + 1], b[j], b[j + 1])
			if hit != null:
				return {"distance": 0.0, "at": hit}
			for pair in [[a[i], b[j], b[j + 1]], [a[i + 1], b[j], b[j + 1]],
					[b[j], a[i], a[i + 1]], [b[j + 1], a[i], a[i + 1]]]:
				var q := _nearest_on_segment(pair[0], pair[1], pair[2])
				var d: float = pair[0].distance_to(q)
				if d < best["distance"]:
					best = {"distance": d, "at": (pair[0] + q) * 0.5}
	return best


func _nearest_on_segment(point: Vector2, a: Vector2, b: Vector2) -> Vector2:
	var ab := b - a
	var t := clampf((point - a).dot(ab) / maxf(ab.length_squared(), 0.001), 0.0, 1.0)
	return a + ab * t


func _crossing_angle(a: Vector2, b: Vector2) -> float:
	return rad_to_deg(acos(clampf(absf(a.dot(b)), 0.0, 1.0)))


func _point_rect_distance(point: Vector2, lo: Vector2, hi: Vector2) -> float:
	var dx := maxf(maxf(lo.x - point.x, 0.0), point.x - hi.x)
	var dy := maxf(maxf(lo.y - point.y, 0.0), point.y - hi.y)
	return Vector2(dx, dy).length()


func _point_ellipse_distance(point: Vector2, centre: Vector2, radii: Vector2) -> float:
	var normalized := Vector2((point.x - centre.x) / radii.x,
		(point.y - centre.y) / radii.y)
	if normalized.length_squared() < 1.0:
		return 0.0
	var best := INF
	for i in 720:
		var a := TAU * float(i) / 720.0
		var edge := centre + Vector2(cos(a) * radii.x, sin(a) * radii.y)
		best = minf(best, point.distance_to(edge))
	return best


## The towns (02B, 2026-09-05) are scenery outside the developed envelope,
## so no building of theirs may reach into it, into either parking field or
## the front road's clearance, or stand inside the sunset sector from the
## pier head; the north town's house is published; and the scene is mounted in
## the world. The former FAR_CITY plain is retired: the editor-owned relocation
## package and the world-reach chain above now guard the city's land instead.
func _check_towns() -> void:
	var towns: Node = load("res://scenes/world/park_towns.tscn").instantiate()
	var clearings: PackedVector3Array = towns.get_meta("clearings", PackedVector3Array())
	if clearings.size() < 60:
		_fail("the towns publish only %d building clearings" % clearings.size())
	if not towns.has_meta("house"):
		_fail("the north town does not say where the character lives")
	var envelope := Rect2(Plan.REBUILD_FOOTPRINT_MIN_X, Plan.REBUILD_FOOTPRINT_MIN_Z,
		Plan.REBUILD_FOOTPRINT_MAX_X - Plan.REBUILD_FOOTPRINT_MIN_X,
		Plan.REBUILD_FOOTPRINT_MAX_Z - Plan.REBUILD_FOOTPRINT_MIN_Z)
	var pier := Vector2(-150.0, -2.0)
	var front_a := Vector2(-Plan.FRONT_ROAD_HALF_X, Plan.FRONT_ROAD_Z)
	var front_b := Vector2(Plan.FRONT_ROAD_HALF_X, Plan.FRONT_ROAD_Z)
	var circle: Vector3 = Plan.TURNING_CIRCLE
	var nearest_front := INF
	var nearest_lot := INF
	for c in clearings:
		var p := Vector2(c.x, c.y)
		if envelope.grow(c.z).has_point(p):
			_fail("a town building at %s reaches into the developed envelope" % p)
		for field in [[-Plan.PARKING_OUTER_X, -Plan.PARKING_INNER_X], [Plan.PARKING_INNER_X, Plan.PARKING_OUTER_X]]:
			var lot := Rect2(float(field[0]), Plan.PARKING_FROM_Z,
				float(field[1]) - float(field[0]), Plan.PARKING_TO_Z - Plan.PARKING_FROM_Z)
			nearest_lot = minf(nearest_lot, _rect_distance(p, lot) - c.z)
		nearest_front = minf(nearest_front,
			p.distance_to(Geometry2D.get_closest_point_to_segment(p, front_a, front_b))
			- Plan.FRONT_ROAD_W * 0.5 - c.z)
		nearest_front = minf(nearest_front,
			p.distance_to(Vector2(circle.x, circle.y)) - circle.z - c.z)
		var v := p - pier
		var azimuth := fmod(rad_to_deg(atan2(v.x, -v.y)) + 360.0, 360.0)
		if azimuth >= 280.0 and azimuth <= 310.0:
			_fail("a town building at %s stands in the sunset sector from the pier head" % p)
	if nearest_lot < 8.0 - EPS:
		_fail("a town building comes within %.1fm of a parking field" % nearest_lot)
	if nearest_front < 8.0 - EPS:
		_fail("a town building comes within %.1fm of the front road" % nearest_front)
	towns.free()
	var world: Node = load("res://scenes/world/park_world.tscn").instantiate()
	if world.find_child("park_towns", true, false) == null:
		_fail("the towns are not mounted in the persistent world")
	world.free()
	print("  towns: %d buildings, nearest %.0fm to a parking field and %.0fm to the front road" % [
		clearings.size(), nearest_lot, nearest_front])


func _rect_distance(p: Vector2, r: Rect2) -> float:
	var dx := maxf(maxf(r.position.x - p.x, 0.0), p.x - r.end.x)
	var dz := maxf(maxf(r.position.y - p.y, 0.0), p.y - r.end.y)
	return sqrt(dx * dx + dz * dz)


func _fail(message: String) -> void:
	_fails.append(message)
	printerr("FAIL: ", message)


func _finish() -> void:
	if _fails.is_empty():
		print("\n  expanded footprint, protected monuments, arrival, and crossings agree")
		get_tree().quit()
	else:
		printerr("\n  %d footprint checks failed" % _fails.size())
		get_tree().quit(1)
