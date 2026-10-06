extends SceneTree
## Dump the generator's ground bodies, exactly, for the Blender terrain master.
## Written 2026-10-05 for Stage 0 of
## `documentation/terrain-master-into-game-plan-2026-10-05.md` (Christina:
## "Exact copy"): the world terrain master's base becomes a vertex-for-vertex
## copy of the ground the generator emits, so mounting it changes nothing.
##
##   Godot --headless --path . --script res://tools/ground_copy_dump.gd -- <out folder>
##
## Reads `scenes/world/generated/park_groundworks.tscn` and, for each body in
## `BODIES`, writes `<body>.json` (counts, the body's transform, each surface's
## material) and `<body>.bin`: per surface, little-endian float32 vertices (x, y,
## z in Godot world metres, the body's and mesh node's transforms applied, so
## the generator's seam displacement is kept), float32 normals, float32 RGBA
## colours and float32 UVs where the mesh has them, and int32 indices. Nothing
## is rounded. The road corridor, the tunnel lids, the west shell and both
## protected anchors are not ground this copy takes over, so they are not here.
## Prints one line per body; returns 0.

const SCENE := "res://scenes/world/generated/park_groundworks.tscn"
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


func _xf(n: Node) -> Transform3D:
	var t := Transform3D.IDENTITY
	var cur := n
	while cur != null and cur is Node3D:
		t = (cur as Node3D).transform * t
		cur = cur.get_parent()
	return t


func _material_record(m: Material) -> Dictionary:
	if m == null:
		return {}
	var rec := {"class": m.get_class(), "path": m.resource_path}
	if m is StandardMaterial3D:
		var s := m as StandardMaterial3D
		var c := s.albedo_color
		rec["albedo"] = [c.r, c.g, c.b, c.a]
		rec["vertex_color_use_as_albedo"] = s.vertex_color_use_as_albedo
		rec["roughness"] = s.roughness
		rec["metallic"] = s.metallic
		rec["cull_mode"] = s.cull_mode
		rec["shading_mode"] = s.shading_mode
	return rec


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		push_error("ground_copy_dump: give an output folder after --")
		quit(1)
		return
	var out_dir := String(args[0])
	DirAccess.make_dir_recursive_absolute(out_dir)
	var root: Node3D = (load(SCENE) as PackedScene).instantiate()
	for body_name in BODIES:
		var body := root.get_node_or_null(body_name)
		if body == null:
			push_error("ground_copy_dump: no body %s" % body_name)
			quit(1)
			return
		var mis := body.find_children("*", "MeshInstance3D", false, false)
		if mis.size() != 1:
			push_error("ground_copy_dump: %s has %d mesh nodes" % [body_name, mis.size()])
			quit(1)
			return
		var mi := mis[0] as MeshInstance3D
		var xf := _xf(mi)
		var mesh := mi.mesh
		var bin := FileAccess.open(out_dir.path_join(body_name + ".bin"), FileAccess.WRITE)
		var surfaces: Array = []
		var offset := 0
		for s in mesh.get_surface_count():
			var arr := mesh.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var nrm: PackedVector3Array = arr[Mesh.ARRAY_NORMAL] if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
			var col: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
			var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV] if arr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			if idx.is_empty():
				for i in v.size():
					idx.append(i)
			var basis := xf.basis
			var wv := PackedFloat32Array()
			wv.resize(v.size() * 3)
			for i in v.size():
				var p := xf * v[i]
				wv[i * 3] = p.x
				wv[i * 3 + 1] = p.y
				wv[i * 3 + 2] = p.z
			var wn := PackedFloat32Array()
			if not nrm.is_empty():
				wn.resize(nrm.size() * 3)
				for i in nrm.size():
					var q := (basis * nrm[i]).normalized()
					wn[i * 3] = q.x
					wn[i * 3 + 1] = q.y
					wn[i * 3 + 2] = q.z
			var wc := PackedFloat32Array()
			if not col.is_empty():
				wc.resize(col.size() * 4)
				for i in col.size():
					wc[i * 4] = col[i].r
					wc[i * 4 + 1] = col[i].g
					wc[i * 4 + 2] = col[i].b
					wc[i * 4 + 3] = col[i].a
			var wu := PackedFloat32Array()
			if not uv.is_empty():
				wu.resize(uv.size() * 2)
				for i in uv.size():
					wu[i * 2] = uv[i].x
					wu[i * 2 + 1] = uv[i].y
			var rec := {
				"vertices": v.size(), "indices": idx.size(),
				"has_normals": not nrm.is_empty(), "has_colors": not col.is_empty(), "has_uv": not uv.is_empty(),
				"primitive": int(mesh.surface_get_primitive_type(s)) if mesh is ArrayMesh else -1,
				"material": _material_record(mesh.surface_get_material(s)),
				"byte_offset": offset,
			}
			for buf in [wv.to_byte_array(), wn.to_byte_array(), wc.to_byte_array(), wu.to_byte_array(), idx.to_byte_array()]:
				bin.store_buffer(buf)
				offset += buf.size()
			surfaces.append(rec)
		bin.close()
		var meta := {
			"body": body_name, "source": SCENE,
			"mesh_node": String(body.get_path_to(mi)),
			"transform": [xf.basis.x.x, xf.basis.x.y, xf.basis.x.z, xf.basis.y.x, xf.basis.y.y, xf.basis.y.z,
				xf.basis.z.x, xf.basis.z.y, xf.basis.z.z, xf.origin.x, xf.origin.y, xf.origin.z],
			"material_override": _material_record(mi.material_override),
			"surfaces": surfaces,
		}
		var jf := FileAccess.open(out_dir.path_join(body_name + ".json"), FileAccess.WRITE)
		jf.store_string(JSON.stringify(meta, "  "))
		jf.close()
		var nv := 0
		var nt := 0
		for r in surfaces:
			nv += int(r["vertices"])
			nt += int(r["indices"]) / 3
		print("ground_copy_dump: %s %d surface(s), %d vertices, %d triangles, origin %s" % [body_name, surfaces.size(), nv, nt, xf.origin])
	quit()
