extends Node

## Dev tool: proves that the expanded park reads as one intentional circulation
## system rather than a collection of ribbons that happen to overlap.
##
## It owns the facts introduced by the footprint pass: the outer envelope, the
## split parking arrival, the protected cascade clearances, the named pedestrian
## crossings of the Grand Circuit, and the retirement of the obsolete NNW
## dogleg. Traversal remains `walk_test`'s job; this catches plan errors before a
## body has to discover them.

const Plan := preload("res://scripts/park_plan.gd")
const LighthouseRegrade := preload("res://scripts/lighthouse_regrade_source.gd")

const EPS := 0.12
const CROSSING_CAPTURE := 12.0
const PROTECTED_MARGIN := 1.0

var _fails: Array[String] = []


func _ready() -> void:
	_check_envelope()
	_check_world_reserve()
	_check_open_faces()
	_check_route_handoffs()
	_check_grand_circuit()
	_check_rim_clearance()
	_check_promontory()
	_check_towns()
	_check_arrival_scene()
	_check_retired_geometry()
	_finish()


func _check_envelope() -> void:
	var lo := Vector2(Plan.REBUILD_FOOTPRINT_MIN_X, Plan.REBUILD_FOOTPRINT_MIN_Z)
	var hi := Vector2(Plan.REBUILD_FOOTPRINT_MAX_X, Plan.REBUILD_FOOTPRINT_MAX_Z)
	for run in Plan.rebuild_route_runs():
		for point in run["points"]:
			if point.x < lo.x - EPS or point.x > hi.x + EPS \
					or point.y < lo.y - EPS or point.y > hi.y + EPS:
				_fail("%s leaves the expanded park envelope at %s" % [run["id"], point])
	for band in Plan.REBUILD_TERRAIN_BANDS:
		var shapes: Array = Plan.REBUILD_TERRAIN_BANDS[band]["shapes"]
		for i in shapes.size():
			for point in Plan.rebuild_terrain_shape(band, i):
				if point.x < lo.x - EPS or point.x > hi.x + EPS \
						or point.y < lo.y - EPS or point.y > hi.y + EPS:
					_fail("terrain %s leaves the expanded park envelope at %s" % [band, point])
	print("  developed park envelope %.0fm x %.0fm" % [hi.x - lo.x, hi.y - lo.y])


## Package 02A: the range's toe line keeps `RIM_CLEARANCE` clear of every route
## edge, the Grand Circuit, both parking fields and every ride, interior,
## attraction and midway parcel. The toe line is `ParkPlan.range_toe_line`, the
## same line the generator raises the ground from.
func _check_rim_clearance() -> void:
	var toes: Array[Vector2] = Plan.range_toe_line(2.0)
	var worst := {}
	var nearest_toe := func(a: Vector2, b: Vector2) -> Vector2:
		var best := toes[0]
		var bd := INF
		for t in toes:
			var dd := t.distance_to(Geometry2D.get_closest_point_to_segment(t, a, b))
			if dd < bd:
				bd = dd
				best = t
		return best
	var note := func(kind: String, d: float, what: String) -> void:
		if not worst.has(kind) or d < worst[kind][0]:
			worst[kind] = [d, what]

	for run in Plan.rebuild_route_runs():
		var pts: Array = run["points"]
		var half := float(run["width"]) * 0.5
		var closed := bool(run.get("closed", false))
		var n := pts.size() if closed else pts.size() - 1
		for i in n:
			var a := _rim_xz(pts[i])
			var b := _rim_xz(pts[(i + 1) % pts.size()])
			note.call("route", _toes_to_segment(toes, a, b) - half,
				"%s, toe near %s" % [run["id"], nearest_toe.call(a, b)])
	var tram: Array = Plan.grand_tram_loop()
	for i in tram.size():
		var a := _rim_xz(tram[i])
		var b := _rim_xz(tram[(i + 1) % tram.size()])
		note.call("Grand Circuit", _toes_to_segment(toes, a, b)
			- Plan.GRAND_TRAM_LANE_W * 0.5,
			"circuit lane %s-%s, toe near %s" % [a, b, nearest_toe.call(a, b)])
	for side in [-1.0, 1.0]:
		var x0 := minf(side * Plan.PARKING_INNER_X, side * Plan.PARKING_OUTER_X)
		var x1 := maxf(side * Plan.PARKING_INNER_X, side * Plan.PARKING_OUTER_X)
		note.call("parking", _toes_to_rect(toes, x0, Plan.PARKING_FROM_Z, x1,
			Plan.PARKING_TO_Z), "parking field")
	for site in Plan.rebuild_ride_sites():
		var id := String(site["id"])
		if site.has("track"):
			var anchor: Vector2 = site.get("track_anchor", site["station"])
			var at := Plan.rebuild_expand_point(anchor)
			var track: Array = site["track"]
			for i in track.size() - 1:
				note.call("ride", _toes_to_segment(toes, at + (Vector2(track[i]) - anchor),
					at + (Vector2(track[i + 1]) - anchor)), id)
			var st := Plan.rebuild_expand_point(site["station"])
			var sz: Vector2 = site["station_size"]
			note.call("ride", _toes_to_rect(toes, st.x - sz.x * 0.5, st.y - sz.y * 0.5,
				st.x + sz.x * 0.5, st.y + sz.y * 0.5), id + " station")
		elif site.has("points"):
			var pts: Array = site["points"]
			var centre := Vector2.ZERO
			for q in pts:
				centre += Vector2(q)
			centre /= float(pts.size())
			var at := Plan.rebuild_expand_point(centre)
			for i in pts.size():
				note.call("ride", _toes_to_segment(toes, at + (Vector2(pts[i]) - centre),
					at + (Vector2(pts[(i + 1) % pts.size()]) - centre)), id)
		elif site.has("terminals"):
			for t in site["terminals"]:
				note.call("ride", _toes_to_point(toes, Plan.rebuild_expand_point(t)) - 6.0, id)
		else:
			var at := Plan.rebuild_expand_point(site["at"])
			var r := 0.0
			if site.has("radius"):
				r = float(site["radius"])
			elif site.has("radii"):
				r = maxf((site["radii"] as Vector2).x, (site["radii"] as Vector2).y)
			elif site.has("size"):
				r = maxf((site["size"] as Vector2).x, (site["size"] as Vector2).y) * 0.5
			note.call("ride", _toes_to_point(toes, at) - r, id)
	for site in Plan.rebuild_attraction_sites():
		var at := Plan.rebuild_expand_point(site["at"])
		var r := 8.0
		if site.has("radius"):
			r = float(site["radius"])
		elif site.has("radii"):
			r = maxf((site["radii"] as Vector2).x, (site["radii"] as Vector2).y)
		elif site.has("size"):
			r = maxf((site["size"] as Vector2).x, (site["size"] as Vector2).y) * 0.5
		note.call("attraction", _toes_to_point(toes, at) - r, String(site["id"]))
	for site in Plan.rebuild_interior_sites():
		var at := Plan.rebuild_expand_point(site["at"])
		var sz: Vector2 = site["size"]
		note.call("interior", _toes_to_rect(toes, at.x - sz.x * 0.5, at.y - sz.y * 0.5,
			at.x + sz.x * 0.5, at.y + sz.y * 0.5), String(site["id"]))
	for site in Plan.rebuild_midway_units():
		var at := Plan.rebuild_expand_point(site["at"])
		note.call("midway", _toes_to_rect(toes, at.x - 2.5, at.y - 2.5, at.x + 2.5,
			at.y + 2.5), String(site["id"]))

	print("  range toe line: %d points about (%.0f, %.0f), inner %.0fm" % [
		toes.size(), Plan.RIM_RANGE_CENTRE.x, Plan.RIM_RANGE_CENTRE.y,
		Plan.RIM_RANGE_INNER_R + Plan.RIM_RANGE_TOE_D])
	for kind in worst:
		var d: float = worst[kind][0]
		print("  rim toe to nearest %s: %.1fm (%s)" % [kind, d, worst[kind][1]])
		if d < Plan.RIM_CLEARANCE - EPS:
			_fail("rim toe leaves only %.1fm to %s %s, rule is %.0fm" % [
				d, kind, worst[kind][1], Plan.RIM_CLEARANCE])


## The promontory walk, the P1 forecourt and the keeper's exhibit stand on the
## land, not on its edge: every walk station, the forecourt's rim and the
## exhibit's corners keep `PROMONTORY_SHORE_CLEARANCE` inland of the coast
## outline, and the spine itself does the same up to its tip. Written after
## the first walk was laid along the cove-side shoreline to within a metre,
## which nothing measured and one frame from the walk showed.
func _check_promontory() -> void:
	var clearance: float = Plan.PROMONTORY_SHORE_CLEARANCE
	var site := {}
	for record in Plan.rebuild_attraction_sites():
		if StringName(record["id"]) == &"P1":
			site = record
	if site.is_empty():
		_fail("the atlas program has no P1")
		return
	# A dictionary rather than two locals: a lambda captures a local by value,
	# so a minimum kept in one never leaves the lambda. The first run printed
	# INF and found nothing.
	var nearest := {"d": INF, "what": ""}
	var note := func(inland: float, what: String) -> void:
		if inland < float(nearest["d"]):
			nearest["d"] = inland
			nearest["what"] = what
	var spine: Array = Plan.PROMONTORY_SPINE
	for i in spine.size() - 1:
		note.call(Plan.coast_inland(spine[i]), "spine vertex %d at %s" % [i, spine[i]])
	var access: Array[Vector3] = LighthouseRegrade.new().path_points(4.0)
	for i in access.size():
		var p := Vector2(access[i].x, access[i].z)
		note.call(Plan.coast_inland(p), "walk station %d at %s" % [i, p])
	var tower := Plan.rebuild_expand_point(site["at"])
	note.call(Plan.coast_inland(tower) - 7.0, "P1 forecourt rim at %s" % tower)
	var keeper := Plan.rebuild_expand_point(site["keeper"])
	var half: Vector2 = (site["keeper_size"] as Vector2) * 0.5
	for corner in [Vector2(-half.x, -half.y), Vector2(half.x, -half.y),
			Vector2(half.x, half.y), Vector2(-half.x, half.y)]:
		note.call(Plan.coast_inland(keeper + corner), "keeper's exhibit corner at %s" % (keeper + corner))
	var worst := float(nearest["d"])
	var worst_what := String(nearest["what"])
	print("promontory: nearest approach to the shoreline %.1fm, %s" % [worst, worst_what])
	if not is_finite(worst):
		_fail("the promontory check measured nothing")
	elif worst < clearance:
		_fail("the promontory parcel stands %.1fm from the shoreline at %s, under the %.1fm clearance" % [
			worst, worst_what, clearance])
	# And the walk climbs: the tower's ground stands above the pad, so the
	# walk is a climb and not a chord over a dip.
	var tower_y: float = Plan.promontory_y(tower)
	if tower_y < Plan.PROMONTORY_ROOT_Y + 8.0:
		_fail("the promontory under P1 is only %.1fm high" % tower_y)


func _rim_xz(v: Variant) -> Vector2:
	if v is Vector3:
		return Vector2((v as Vector3).x, (v as Vector3).z)
	return v as Vector2


func _toes_to_segment(toes: Array[Vector2], a: Vector2, b: Vector2) -> float:
	var best := INF
	for t in toes:
		best = minf(best, t.distance_to(Geometry2D.get_closest_point_to_segment(t, a, b)))
	return best


func _toes_to_point(toes: Array[Vector2], q: Vector2) -> float:
	var best := INF
	for t in toes:
		best = minf(best, t.distance_to(q))
	return best


func _toes_to_rect(toes: Array[Vector2], x0: float, z0: float, x1: float,
		z1: float) -> float:
	var best := INF
	for t in toes:
		var dx := maxf(maxf(x0 - t.x, 0.0), t.x - x1)
		var dz := maxf(maxf(z0 - t.y, 0.0), t.y - z1)
		best = minf(best, Vector2(dx, dz).length())
	return best


## The atlas envelope is allowed to be tight around program; the world is not.
## These are independent constants so extending scenery can never re-transform
## a path, move a ride, or disturb either protected cascade.
func _check_world_reserve() -> void:
	var margin := Plan.REBUILD_WORLD_MIN_PROGRAM_MARGIN
	var east := Plan.REBUILD_WORLD_LAND_TO_X - Plan.REBUILD_FOOTPRINT_MAX_X
	var north := Plan.REBUILD_FOOTPRINT_MIN_Z - Plan.REBUILD_WORLD_LAND_FROM_Z
	var south := Plan.REBUILD_WORLD_LAND_TO_Z - Plan.REBUILD_FOOTPRINT_MAX_Z
	var west_water := Plan.REBUILD_FOOTPRINT_MIN_X \
		- Plan.REBUILD_WORLD_WATER_FROM_X
	for pair in [
		["east land", east], ["north land", north], ["south land", south],
		["west ocean", west_water],
	]:
		if float(pair[1]) < margin - EPS:
			_fail("%s leaves only %.1fm beyond the developed park, expected %.1fm" % [
				pair[0], pair[1], margin])

	var ground: Node = load("res://scenes/world/park_groundworks.tscn").instantiate()
	var reserve := ground.find_child("terrain_world_mainland_reserve", true, false)
	if reserve == null:
		_fail("the surrounding mainland reserve is not mounted")
	else:
		var surface := reserve.find_child("surface", false, false) as MeshInstance3D
		if surface == null or surface.mesh == null:
			_fail("the surrounding mainland reserve has no surface mesh")
		else:
			var bounds := surface.mesh.get_aabb()
			if bounds.position.x > Plan.REBUILD_WORLD_LAND_FROM_X + EPS \
					or bounds.end.x < Plan.REBUILD_WORLD_LAND_TO_X - EPS \
					or bounds.position.z > Plan.REBUILD_WORLD_LAND_FROM_Z + EPS \
					or bounds.end.z < Plan.REBUILD_WORLD_LAND_TO_Z - EPS:
				_fail("the mainland mesh does not reach all four published world bounds")
	# The coast meshes are the ground beyond the working strip (2026-09-04):
	# the north one has to reach the world's north coast bound, the south one
	# the point where the bay's far shore crosses onto the mainland reserve.
	var south_to_z := minf(Plan.REBUILD_WORLD_COAST_TO_Z,
		Plan.coast_south_crossing_z(Plan.SHORE_FROM_X))
	for pair in [["north", Plan.REBUILD_WORLD_COAST_FROM_Z], ["south", south_to_z]]:
		var coast := ground.find_child("terrain_world_coast_%s" % pair[0], true, false)
		if coast == null:
			_fail("the %s coastal reserve is not mounted" % pair[0])
			continue
		var coast_surface := coast.find_child("surface", false, false) as MeshInstance3D
		if coast_surface == null or coast_surface.mesh == null:
			_fail("the %s coastal reserve has no surface mesh" % pair[0])
			continue
		var coast_bounds := coast_surface.mesh.get_aabb()
		var reach: float = coast_bounds.position.z if pair[0] == "north" else coast_bounds.end.z
		if absf(reach - float(pair[1])) > 1.0:
			_fail("the %s coast mesh ends at z %.1f, expected %.1f" % [
				pair[0], reach, float(pair[1])])
	ground.free()

	var west: Node = load("res://scenes/world/west_shell.tscn").instantiate()
	var water := west.find_child("water", true, false) as CSGBox3D
	if water == null:
		_fail("the enlarged ocean is missing")
	else:
		var water_lo := water.position - water.size * 0.5
		var water_hi := water.position + water.size * 0.5
		if water_lo.x > Plan.REBUILD_WORLD_WATER_FROM_X + EPS \
				or water_hi.x < Plan.REBUILD_WORLD_WATER_TO_X - EPS \
				or water_lo.z > Plan.REBUILD_WORLD_WATER_FROM_Z + EPS \
				or water_hi.z < Plan.REBUILD_WORLD_WATER_TO_Z - EPS:
			_fail("the ocean does not reach all four published world bounds")
	# The bay's water lies under the whole of the far shore: from the ocean's
	# east edge to past the outline's eastmost point, and from north of the
	# crossing to the world's south coast bound.
	var bay := west.find_child("water_bay", true, false) as CSGBox3D
	if bay == null:
		_fail("the bay water sheet is missing")
	else:
		var bay_lo := bay.position - bay.size * 0.5
		var bay_hi := bay.position + bay.size * 0.5
		var far: Vector2 = Plan.COAST_SOUTH_OUTLINE[Plan.COAST_SOUTH_OUTLINE.size() - 1]
		var crossing := Plan.coast_south_crossing_z(Plan.REBUILD_WORLD_WATER_TO_X)
		if bay_lo.x > Plan.REBUILD_WORLD_WATER_TO_X + EPS or bay_hi.x < far.x - EPS \
				or bay_lo.z > crossing - 30.0 \
				or bay_hi.z < Plan.REBUILD_WORLD_COAST_TO_Z - EPS:
			_fail("the bay water does not lie under the whole of the far shore")
	# The sea north of the north shore (2026-09-05): from the ocean's east
	# edge to the world's east edge, reaching south under the land.
	var north_sea := west.find_child("water_north", true, false) as CSGBox3D
	if north_sea == null:
		_fail("the north water sheet is missing")
	else:
		var lo := north_sea.position - north_sea.size * 0.5
		var hi := north_sea.position + north_sea.size * 0.5
		# The sheet has to reach south past the deepest cove of the north
		# shore, so every bit of that shore stands over water.
		var deepest_cove: float = -INF
		for i in range(Plan.COAST_NORTH_FAR_FROM, Plan.COAST_NORTH_OUTLINE.size()):
			var q: Vector2 = Plan.COAST_NORTH_OUTLINE[i]
			# The north shore proper, not the east coast the outline runs on down.
			if q.y < -2500.0:
				deepest_cove = maxf(deepest_cove, q.y)
		if lo.x > Plan.REBUILD_WORLD_WATER_TO_X + EPS or hi.x < Plan.REBUILD_WORLD_WATER_FAR_X - EPS \
				or lo.z > Plan.REBUILD_WORLD_WATER_FROM_Z + EPS \
				or hi.z < deepest_cove - EPS:
			_fail("the north water does not lie under the whole of the north shore (x %.0f..%.0f, z %.0f..%.0f, deepest cove %.0f)" % [
				lo.x, hi.x, lo.z, hi.z, deepest_cove])
	# And the sea east of the island, between the north sheet and the bay's.
	var east_sea := west.find_child("water_east", true, false) as CSGBox3D
	if east_sea == null:
		_fail("the east water sheet is missing")
	else:
		var lo := east_sea.position - east_sea.size * 0.5
		var hi := east_sea.position + east_sea.size * 0.5
		if lo.x > Plan.EAST_WATER_FROM_X + EPS or hi.x < Plan.REBUILD_WORLD_WATER_FAR_X - EPS \
				or lo.z > Plan.NORTH_WATER_TO_Z + EPS or hi.z < Plan.BAY_WATER_FROM_Z - EPS:
			_fail("the east water does not lie under the whole of the east coast")
	west.free()

	print("  world reserve margins: E %.0fm, N %.0fm, S %.0fm, W ocean %.0fm" % [
		east, north, south, west_water])


## The terrain is single-sided, so a boundary edge standing above the water
## is a face the world does not have: from outside it you look straight
## through the mountain. Found from the towns on 2026-09-05 — the range's
## south arm dead-ending into the bay with its west face open, the reserve's
## summit north of the valley floating over the 200m its west edge ran past
## the coast mesh — and nothing had an opinion about it, because the census
## counts faces that fight and the walk asks whether something is in the
## way, never whether it is there. A boundary edge is one that exactly one
## triangle uses. The coast meshes and the reserve share their seam vertex
## for vertex, so an edge of one paired by an identical edge of the other is
## closed, and a wall's top edge pairs with the ground edge it was built
## from; edges that differ only by rounding are paired by their midpoints on
## a quarter-metre grid. What remains with an end above `WATER_TOP + 1`,
## outside the developed envelope where the park's own ground fills the
## reserve's openings, is an open face.
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
	for label in classes:
		var c: Dictionary = classes[label]
		print("    %s: %d edges, %.0fm, x %.0f..%.0f, z %.0f..%.0f, e.g. %s to %s" % [
			label, int(c["count"]), float(c["length"]), float(c["x_lo"]), float(c["x_hi"]),
			float(c["z_lo"]), float(c["z_hi"]), c["sample"][1], c["sample"][2]])
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
		_expect_near("B north return to waterfront", north[-1], waterfront[0])
		_expect_near("B waterfront to south return", waterfront[-1], south[0])


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
## pier head; the city's plain lies over the bay's water sheet; the north
## town's house is published; and the scene is mounted in the world.
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
	# The city stands on its peninsula since 2026-09-05: its downtown plain
	# and the built-up ground are land, inside the coast by a margin, and the
	# whole of it lies over the bay's water sheet for the skirt to stand in.
	for key in ["plain", "built"]:
		for q in Plan.FAR_CITY[key]:
			var corner: Vector2 = q
			if Plan.coast_inland(corner) < 20.0 - EPS:
				_fail("the city's %s corner %s is within 20m of the shore" % [key, corner])
			if corner.x < Plan.REBUILD_WORLD_WATER_TO_X - EPS or corner.x > Plan.BAY_WATER_TO_X + EPS \
					or corner.y < Plan.BAY_WATER_FROM_Z - EPS or corner.y > Plan.REBUILD_WORLD_WATER_TO_Z + EPS:
				_fail("the city's %s corner %s is off the bay's water sheet" % [key, corner])
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
