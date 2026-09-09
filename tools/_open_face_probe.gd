extends SceneTree

## Dev probe: the terrain's open faces by mesh, with each one's nearest
## edge on another mesh, so a crack between the road corridor and the
## lattice can be read as what it is. Loads the groundworks scene; writes
## nothing.

const Plan := preload("res://scripts/park_plan.gd")
const NAMES := ["terrain_world_mainland_reserve", "terrain_world_coast_north",
	"terrain_world_coast_south", "terrain_road_corridor"]


func _initialize() -> void:
	var ground: Node = load("res://scenes/world/park_groundworks.tscn").instantiate()
	var edges := {}
	for name in NAMES:
		var node: Node = ground.find_child(name, true, false)
		var surface := node.find_child("surface", false, false) as MeshInstance3D
		var arrays: Array = surface.mesh.surface_get_arrays(0)
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var index := PackedInt32Array()
		if arrays[Mesh.ARRAY_INDEX] != null:
			index = arrays[Mesh.ARRAY_INDEX]
		var n := index.size() if index.size() > 0 else verts.size()
		for i in range(0, n, 3):
			var tri: Array = []
			for k in 3:
				var vi: int = index[i + k] if index.size() > 0 else i + k
				tri.append(verts[vi])
			for k in 3:
				_count(edges, tri[k], tri[(k + 1) % 3], name)
	var stray: Array = []
	for key in edges:
		var rec: Array = edges[key]
		if int(rec[0]) == 1 and maxf((rec[1] as Vector3).y, (rec[2] as Vector3).y) >= Plan.WATER_TOP + 1.0 \
				and (rec[1] as Vector3).distance_to(rec[2]) >= 0.3:
			stray.append(rec)
	var by_mesh := {}
	for rec in stray:
		by_mesh[rec[3]] = int(by_mesh.get(rec[3], 0)) + 1
	print("strays above the water by mesh: ", by_mesh)
	# The reserve's world edges and shores are expected; look at the ones
	# near the corridor.
	var corridor: Array = []
	var others: Array = []
	for rec in stray:
		if rec[3] == "terrain_road_corridor":
			corridor.append(rec)
		else:
			others.append(rec)
	var shown := 0
	for rec in corridor:
		if shown >= 12:
			break
		var a: Vector3 = rec[1]
		var b: Vector3 = rec[2]
		var m := (a + b) * 0.5
		var best := INF
		var best_rec: Array = []
		for o in others:
			var oa: Vector3 = o[1]
			var ob: Vector3 = o[2]
			var d := Vector2(m.x - (oa.x + ob.x) * 0.5, m.z - (oa.z + ob.z) * 0.5).length()
			if d < best:
				best = d
				best_rec = o
		print("corridor edge %.2fm %s -> %s; nearest other stray %.2fm away: %s %s -> %s (%.2fm)" % [
			a.distance_to(b), a, b, best, best_rec[3] if not best_rec.is_empty() else "-",
			best_rec[1] if not best_rec.is_empty() else "", best_rec[2] if not best_rec.is_empty() else "",
			(best_rec[1] as Vector3).distance_to(best_rec[2]) if not best_rec.is_empty() else 0.0])
		shown += 1
	# And the lengths: are the corridor's strays profile-sized (a row) or row-sized (a side)?
	var hist := {}
	for rec in corridor:
		var l: float = (rec[1] as Vector3).distance_to(rec[2])
		var bucket := "<1" if l < 1.0 else ("1-3" if l < 3.0 else ("3-5" if l < 5.0 else ">5"))
		hist[bucket] = int(hist.get(bucket, 0)) + 1
	print("corridor stray lengths: ", hist)
	var reserve_near := 0
	for o in others:
		var oa: Vector3 = o[1]
		var ob: Vector3 = o[2]
		var mo := (oa + ob) * 0.5
		var near := false
		for rec in corridor:
			var mc: Vector3 = ((rec[1] as Vector3) + (rec[2] as Vector3)) * 0.5
			if Vector2(mo.x - mc.x, mo.z - mc.z).length() < 6.0:
				near = true
				break
		if near:
			reserve_near += 1
	print("other-mesh strays within 6m of a corridor stray: %d of %d" % [reserve_near, others.size()])
	# For a few of the lattice's strays: every corridor edge, stray or not,
	# that touches either end within half a metre, and the nearest corridor
	# vertex to each end. Whether the corridor has the vertex at all is the
	# question.
	var corridor_edges: Array = []
	for key in edges:
		var rec: Array = edges[key]
		if rec[3] == "terrain_road_corridor":
			corridor_edges.append(rec)
	var shown2 := 0
	for o in others:
		if shown2 >= 6:
			break
		var oa: Vector3 = o[1]
		var ob: Vector3 = o[2]
		if oa.distance_to(ob) > 2.0:
			continue
		shown2 += 1
		print("lattice stray %s %.2fm %s -> %s" % [o[3], oa.distance_to(ob), oa, ob])
		for end in [oa, ob]:
			var best := INF
			var best_v := Vector3.ZERO
			var touching := 0
			for ce in corridor_edges:
				for v in [ce[1], ce[2]]:
					var d: float = (v as Vector3).distance_to(end)
					if d < best:
						best = d
						best_v = v
					if d < 0.5:
						touching += 1
			print("   end %s: nearest corridor vertex %.3fm away at %s; %d corridor edge-ends within 0.5m" % [
				end, best, best_v, touching])
	# And the corridor's own boundary edges at that vertex: does one run
	# collinear with the lattice's stray, and if so how far off is the
	# lattice's far end from its chord?
	var shown3 := 0
	for o in others:
		if shown3 >= 8:
			break
		var oa: Vector3 = o[1]
		var ob: Vector3 = o[2]
		if oa.distance_to(ob) > 2.5:
			continue
		for pair in [[oa, ob], [ob, oa]]:
			var v: Vector3 = pair[0]
			var far: Vector3 = pair[1]
			var found := false
			for ce in corridor:
				var c: Vector3 = ce[1]
				var d: Vector3 = ce[2]
				var other := Vector3.ZERO
				if c.distance_to(v) < 0.01:
					other = d
				elif d.distance_to(v) < 0.01:
					other = c
				else:
					continue
				found = true
				var cd := Vector2(other.x - v.x, other.z - v.z)
				var t := Vector2(far.x - v.x, far.z - v.z).dot(cd) / maxf(cd.length_squared(), 0.0001)
				var foot := v.lerp(other, t)
				var off_plan := Vector2(far.x - foot.x, far.z - foot.z).length()
				var off_y := far.y - foot.y
				print("lattice stray %.2fm at %s: corridor boundary edge %.2fm to %s: far end t=%.3f, %.3fm off in plan, %.3fm off in height" % [
					oa.distance_to(ob), v, v.distance_to(other), other, t, off_plan, off_y])
			if found:
				shown3 += 1
				break
	ground.free()
	quit()


func _count(edges: Dictionary, a: Vector3, b: Vector3, mesh: String) -> void:
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
