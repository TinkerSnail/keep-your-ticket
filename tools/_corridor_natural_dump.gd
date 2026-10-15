extends SceneTree
## Dev probe: what Stage 6 of `documentation/terrain-height-grid-plan-2026-10-12.md` (2026-10-15)
## bakes into the height grid inside the road corridor and over the tunnels, read off the
## generator without regenerating anything. Run once, before the grid took the corridor's
## natural ground: from then on `_road_natural_y` reads the grid, so `--nodes` reads it back
## rather than the master's `Earthworks` sheet it baked.
##
##   Godot --headless --path . --script res://tools/_corridor_natural_dump.gd -- \
##       --nodes=/abs/nodes.f32 --out=/abs/natural.f32 [--lids=/abs/lids.f32]
##
## `--nodes`: plan points, (x, z) float32 pairs, Godot world metres. Writes `--out`, per point
## six float32: the generator's natural ground (`_rebuild_natural_y`, the landform before any
## road), the natural ground its corridor cuts its sides to (`_road_natural_y`), and the ground's
## colour there at that height (`_rebuild_ground_colour`, sRGB r, g, b, as the generator writes
## vertex colours), then 1 where `WorldTerrainSource` counts the node inside a held body's outline
## (`holes.json`), so `delta_y` reads it only for points inside, else 0.
##
## `--lids`: the tunnel lids' strip as the game loads it, from the generated groundworks: its
## faces' corners, each (x, y, z, r, g, b) float32, three a face, the portal faces' (vertical)
## included; the lid wears its colour per vertex in sRGB (`ground_banded`).
##
## Writes nothing in the project. Returns 0, or 1.

const LIDS := "res://scenes/world/generated/park_groundworks_data/terrain_tunnel_lids__surface_mesh.res"


func _initialize() -> void:
	var nodes := ""
	var out := ""
	var lids := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--nodes="):
			nodes = arg.trim_prefix("--nodes=")
		elif arg.begins_with("--out="):
			out = arg.trim_prefix("--out=")
		elif arg.begins_with("--lids="):
			lids = arg.trim_prefix("--lids=")
	var code := 0
	if not nodes.is_empty() and not out.is_empty():
		code = _natural(nodes, out)
	if code == 0 and not lids.is_empty():
		code = _lids(lids)
	if nodes.is_empty() and lids.is_empty():
		printerr("corridor natural dump: pass --nodes=<f32> --out=<f32>, or --lids=<f32>")
		code = 1
	quit(code)


func _natural(nodes_path: String, out_path: String) -> int:
	var raw := FileAccess.get_file_as_bytes(nodes_path)
	var xz := raw.to_float32_array()
	if xz.size() % 2 != 0 or xz.is_empty():
		printerr("corridor natural dump: %s holds no (x, z) pairs" % nodes_path)
		return 1
	var gen: Object = load("res://tools/gen_props.gd").new()
	var src: Object = gen._world_terrain_source()
	var t0 := Time.get_ticks_msec()
	var n := xz.size() / 2
	var values := PackedFloat32Array()
	values.resize(n * 6)
	for i in n:
		var p := Vector2(xz[2 * i], xz[2 * i + 1])
		var natural: float = gen._rebuild_natural_y(p)
		var cut_to: float = gen._road_natural_y(p)
		var colour: Color = gen._rebuild_ground_colour(p, cut_to)
		values[6 * i] = natural
		values[6 * i + 1] = cut_to
		values[6 * i + 2] = colour.r
		values[6 * i + 3] = colour.g
		values[6 * i + 4] = colour.b
		values[6 * i + 5] = float(_held_mark(src, p))
	var f := FileAccess.open(out_path, FileAccess.WRITE)
	f.store_buffer(values.to_byte_array())
	f.close()
	print("corridor natural dump: %d points in %.1f s; %s" % [n, (Time.get_ticks_msec() - t0) / 1000.0,
		gen._world_terrain_source().summary()])
	gen.free()
	return 0


## The reader's mark at the node nearest `p`: 1 inside a held body's outline.
@warning_ignore("integer_division")
func _held_mark(src: Object, p: Vector2) -> int:
	var c: int = roundi((p.x - src._grid_x0) / src._grid_step)
	var r: int = roundi((p.y - src._grid_z0) / src._grid_step)
	if c < 0 or r < 0 or c > src._grid_cols or r > src._grid_rows:
		return 0
	var cells: int = src._grid_cells
	var ti := mini(c / cells, src._grid_ntx - 1)
	var tj := mini(r / cells, src._grid_ntz - 1)
	var mask: PackedByteArray = src._grid_hole[tj * src._grid_ntx + ti]
	if mask.is_empty():
		return 0
	return mask[(r - tj * cells) * src._grid_samples + (c - ti * cells)]


func _lids(out_path: String) -> int:
	var mesh := load(LIDS) as ArrayMesh
	if mesh == null:
		printerr("corridor natural dump: %s does not load" % LIDS)
		return 1
	var values := PackedFloat32Array()
	for s in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(s)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var c: PackedColorArray = arr[Mesh.ARRAY_COLOR]
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		var order: PackedInt32Array = idx
		if order.is_empty():
			order.resize(v.size())
			for i in v.size():
				order[i] = i
		for i in order:
			values.append_array([v[i].x, v[i].y, v[i].z, c[i].r, c[i].g, c[i].b])
	var f := FileAccess.open(out_path, FileAccess.WRITE)
	f.store_buffer(values.to_byte_array())
	f.close()
	print("corridor natural dump: the lids' %d faces" % (values.size() / 18))
	return 0
