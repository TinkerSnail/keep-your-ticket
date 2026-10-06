extends SceneTree
## Is the world terrain master's exported ground the generator's ground, exactly?
## Written 2026-10-05 for Stage 0 of
## `documentation/terrain-master-into-game-plan-2026-10-05.md`.
##
##   Godot --headless --path . --script res://tools/ground_copy_compare.gd
##
## For each body `ground_copy_dump.gd` copies, compares
## `scenes/world/generated/park_groundworks.tscn` with the imported
## `assets/world_terrain_master.glb`: the drawn triangles as a multiset (three
## world positions in winding order, compared exactly as float32), and for
## matched drawn triangles the corner colours (exact) and normals (largest
## angle). Collision: the master's collision is derived from its drawn mesh,
## so it must equal that mesh exactly; the generator's collision is not
## exactly its own drawn mesh (its faces sit up to a fraction of a millimetre
## off, 2026-10-05), so it is matched to the master's within `COLLISION_TOL_M`
## and the largest distance is printed. Prints one line per body and a
## verdict; quits 1 on any drawn difference beyond the triangles listed in
## `KNOWN_DUPLICATES` (doubled triangles in the generator's own output, which
## the glTF export writes once), any master collision face that is not its
## drawn mesh, or any generator collision face farther than the tolerance.

const GENERATED := "res://scenes/world/generated/park_groundworks.tscn"
const MASTER_GLB := "res://assets/world_terrain_master.glb"
const BODIES := [
	"terrain_world_mainland_reserve",
	"terrain_world_coast_north",
	"terrain_world_coast_south",
	"terrain_T2_lowland",
	"terrain_T3_headland",
	"terrain_T6_outer_highland",
	"east_shoulder_n",
	"east_shoulder_s",
]
const KNOWN_DUPLICATES := {"terrain_world_mainland_reserve": 1, "terrain_world_coast_north": 1}
const COLLISION_TOL_M := 0.001
const CELL := 0.01


func _xf(n: Node) -> Transform3D:
	var t := Transform3D.IDENTITY
	var cur := n
	while cur != null and cur is Node3D:
		t = (cur as Node3D).transform * t
		cur = cur.get_parent()
	return t


func _vkey(p: Vector3) -> String:
	var b := PackedFloat32Array([p.x, p.y, p.z]).to_byte_array()
	return b.hex_encode()


func _tkey(a: Vector3, b: Vector3, c: Vector3) -> String:
	# Rotate to start at the smallest key, keeping the cyclic order (winding).
	var ka := _vkey(a)
	var kb := _vkey(b)
	var kc := _vkey(c)
	if ka <= kb and ka <= kc:
		return ka + kb + kc
	if kb <= ka and kb <= kc:
		return kb + kc + ka
	return kc + ka + kb


func _mesh_tris(mi: MeshInstance3D) -> Dictionary:
	# key -> [count, colours (3 Color or empty), normals (3 Vector3)]
	var out := {}
	var xf := _xf(mi)
	var m := mi.mesh
	for s in m.get_surface_count():
		var arr := m.surface_get_arrays(s)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var n: PackedVector3Array = arr[Mesh.ARRAY_NORMAL] if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
		var c: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		if idx.is_empty():
			for i in v.size():
				idx.append(i)
		for t in range(0, idx.size(), 3):
			var i0 := idx[t]
			var i1 := idx[t + 1]
			var i2 := idx[t + 2]
			var a := xf * v[i0]
			var b := xf * v[i1]
			var cc := xf * v[i2]
			var k := _tkey(a, b, cc)
			var rec: Array = out.get(k, [0, null, null])
			rec[0] = int(rec[0]) + 1
			if rec[1] == null:
				var cols := {}
				var nors := {}
				for pair in [[a, i0], [b, i1], [cc, i2]]:
					var vk := _vkey(pair[0])
					if not c.is_empty():
						cols[vk] = c[pair[1]]
					if not n.is_empty():
						nors[vk] = (xf.basis * n[pair[1]]).normalized()
				rec[1] = cols
				rec[2] = nors
			out[k] = rec
	return out


func _shape_tris(body: Node) -> Dictionary:
	var out := {}
	for cs in body.find_children("*", "CollisionShape3D", true, false):
		var shape := (cs as CollisionShape3D).shape
		if not (shape is ConcavePolygonShape3D):
			continue
		var xf := _xf(cs)
		var f := (shape as ConcavePolygonShape3D).get_faces()
		for t in range(0, f.size(), 3):
			var k := _tkey(xf * f[t], xf * f[t + 1], xf * f[t + 2])
			out[k] = int(out.get(k, 0)) + 1
	return out


func _shape_faces(body: Node) -> PackedVector3Array:
	var out := PackedVector3Array()
	for cs in body.find_children("*", "CollisionShape3D", true, false):
		var shape := (cs as CollisionShape3D).shape
		if not (shape is ConcavePolygonShape3D):
			continue
		var xf := _xf(cs)
		for p in (shape as ConcavePolygonShape3D).get_faces():
			out.append(xf * p)
	return out


func _cell(p: Vector3) -> Vector3i:
	return Vector3i(floori(p.x / CELL), floori(p.y / CELL), floori(p.z / CELL))


## The largest distance from each face of `a` to its nearest face of `b` with the
## same winding (vertex by vertex, best cyclic rotation), searching faces whose
## centroid lies in the neighbouring cells; -1 where none is within reach.
func _match_faces(a: PackedVector3Array, b: PackedVector3Array) -> Array:
	var grid := {}
	for t in range(0, b.size(), 3):
		var k := _cell((b[t] + b[t + 1] + b[t + 2]) / 3.0)
		if not grid.has(k):
			grid[k] = []
		(grid[k] as Array).append(t)
	var worst := 0.0
	var unmatched := 0
	for t in range(0, a.size(), 3):
		var c := (a[t] + a[t + 1] + a[t + 2]) / 3.0
		var k := _cell(c)
		var best := INF
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				for dz in [-1, 0, 1]:
					var kk := k + Vector3i(dx, dy, dz)
					if not grid.has(kk):
						continue
					for u in grid[kk]:
						for r in 3:
							var d := maxf(a[t].distance_to(b[u + r]), maxf(a[t + 1].distance_to(b[u + (r + 1) % 3]), a[t + 2].distance_to(b[u + (r + 2) % 3])))
							best = minf(best, d)
		if best > COLLISION_TOL_M:
			unmatched += 1
		if best < INF:
			worst = maxf(worst, best)
	return [unmatched, worst]


func _diff(a: Dictionary, b: Dictionary) -> Array:
	# counts of keys missing from b and extra in b
	var missing := 0
	var extra := 0
	for k in a:
		var ca := int(a[k][0]) if a[k] is Array else int(a[k])
		var cb := 0
		if b.has(k):
			cb = int(b[k][0]) if b[k] is Array else int(b[k])
		missing += maxi(0, ca - cb)
	for k in b:
		var cb := int(b[k][0]) if b[k] is Array else int(b[k])
		var ca := 0
		if a.has(k):
			ca = int(a[k][0]) if a[k] is Array else int(a[k])
		extra += maxi(0, cb - ca)
	return [missing, extra]


func _init() -> void:
	var gen: Node3D = (load(GENERATED) as PackedScene).instantiate()
	var glb: Node3D = (load(MASTER_GLB) as PackedScene).instantiate()
	var failures := 0
	for body_name in BODIES:
		var gbody := gen.get_node(body_name)
		var gmi := gbody.find_children("*", "MeshInstance3D", false, false)[0] as MeshInstance3D
		var mmi := glb.find_child(body_name, true, false) as MeshInstance3D
		if mmi == null:
			print("ground_copy_compare: %s MISSING from the GLB" % body_name)
			failures += 1
			continue
		var gt := _mesh_tris(gmi)
		var mt := _mesh_tris(mmi)
		var d := _diff(gt, mt)
		var colour_bad := 0
		var normal_worst := 0.0
		for k in gt:
			if not mt.has(k):
				continue
			var gc: Dictionary = gt[k][1]
			var mc: Dictionary = mt[k][1]
			for vk in gc:
				if not mc.has(vk) or not (gc[vk] as Color).is_equal_approx(mc[vk]):
					if not mc.has(vk) or (gc[vk] as Color) != (mc[vk] as Color):
						colour_bad += 1
			var gn: Dictionary = gt[k][2]
			var mn: Dictionary = mt[k][2]
			for vk in gn:
				if mn.has(vk):
					normal_worst = maxf(normal_worst, rad_to_deg((gn[vk] as Vector3).angle_to(mn[vk])))
		var ms := _shape_tris(mmi)
		var own := _diff(mt, ms)            # the master's collision against its own drawn mesh: exact
		var gf := _shape_faces(gbody)
		var mf := _shape_faces(mmi)
		var near := _match_faces(gf, mf)    # the generator's collision against the master's, within tolerance
		var allowed := int(KNOWN_DUPLICATES.get(body_name, 0))
		var ok := int(d[1]) == 0 and int(d[0]) <= allowed and int(own[0]) == 0 and int(own[1]) == 0 \
			and int(near[0]) <= allowed and colour_bad == 0
		if not ok:
			failures += 1
		print("ground_copy_compare: %s drawn %d tris: missing %d, extra %d; master collision = its drawn mesh: missing %d, extra %d; generator collision %d faces: %d farther than %.0f mm, largest %.4f mm; colours differing %d; normals worst %.3f deg; %s" % [
			body_name, gt.size(), d[0], d[1], own[0], own[1], gf.size() / 3, near[0], COLLISION_TOL_M * 1000.0, float(near[1]) * 1000.0, colour_bad, normal_worst, "OK" if ok else "DIFFERS"])
	print("ground_copy_compare: %s" % ("PASS" if failures == 0 else "FAIL (%d bodies)" % failures))
	quit(0 if failures == 0 else 1)
