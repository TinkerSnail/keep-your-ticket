extends SceneTree
## Dev probe: the faces the generator measures the ground from, exactly as
## Godot loads them, for the height grid's bake. Written 2026-10-12 for Stage 1,
## Bake, of `documentation/terrain-height-grid-plan-2026-10-12.md`; its reader
## is `tools/ground_bake.py`, which rasterises them into
## `assets/source/world_ground/`.
##
##   Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --out=/abs/dir
##   Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --delta=/abs/points.f32,/abs/out.f64
##   Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --read=/abs/exr_dir,/abs/out_dir
##
## `--out` writes, each a raw little-endian float32 file of faces, three corners
## a face, (x, y, z) a corner, Godot world metres:
##   `master.f32`    the master's ground as `WorldTerrainSource.load_master` gives
##                   it, in the order `_joined` puts it (the generator's
##                   `_master_faces`);
##   `baseline.f32`  the frozen copy, `load_baseline`, in the same order;
##   `held.f32`      every collider of the ground the generator still holds and
##                   the master meets: `places/park_groundworks` (the road
##                   corridor, the tunnel lids, the east shoulder walls, the
##                   promenade banks), `places/west_shell`, and the two anchors,
##                   `places/west_stair` (NT-1) and `places/east_cascade` (NT-2),
##                   from their collision shapes as the physics sees them (a CSG
##                   root's baked collision, a body's ConcavePolygonShape3D);
##   `held_open.f32` each held collider's open edges, two corners an edge: the
##                   edges one face uses, corners matched bit for bit.
## and `faces.json`: per file, its pieces in order (name or path, first face or
## edge, count), and the header (commit, Godot, what changed in the tree).
##
## `--delta` reads plan points (float32 x, z pairs) and writes, for each, the
## generator's own `WorldTerrainSource.new().delta_y` (float64), with the
## counts of faces added and removed and of dirty cells on stdout: the bake's
## proof that the grid reads what the generator reads.
##
## `--read` loads every `.exr` in a folder with `Image.load_from_file` and
## writes `<name>.bin` (the image's raw data) and `<name>.json` (size and
## format) beside each other in the out folder: the bake's Godot round trip.
##
## Writes nothing in the project. Prints one line per piece; returns 0, or 1.

const WorldTerrainSource := preload("res://scripts/world_terrain_source.gd")
const HELD := {
	"park_groundworks": "res://scenes/world/park_groundworks.tscn",
	"west_shell": "res://scenes/world/west_shell.tscn",
	"west_stair": "res://scenes/world/west_stair.tscn",
	"east_cascade": "res://scenes/world/east_cascade.tscn",
}


func _initialize() -> void:
	var code := 1
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			code = await _dump(arg.trim_prefix("--out="))
		elif arg.begins_with("--delta="):
			var pair := arg.trim_prefix("--delta=").split(",")
			code = _delta(pair[0], pair[1])
		elif arg.begins_with("--read="):
			var pair := arg.trim_prefix("--read=").split(",")
			code = _read(pair[0], pair[1])
	if code != 0:
		printerr("ground faces dump: pass --out=<dir>, --delta=<points>,<out> or --read=<dir>,<out>")
	quit(code)


func _dump(dir: String) -> int:
	DirAccess.make_dir_recursive_absolute(dir)
	var t0 := Time.get_ticks_msec()
	var index := {"header": _header()}

	var master := WorldTerrainSource.load_master()
	index["master"] = _write_faces(dir.path_join("master.f32"), master)
	var baseline := WorldTerrainSource.load_baseline()
	index["baseline"] = _write_faces(dir.path_join("baseline.f32"), baseline)

	# The held scenes as `park_world.tscn` mounts them (at the origin, under
	# `places`), in the tree, so every CSG root has built its shape.
	var places := Node3D.new()
	places.name = "places"
	root.add_child(places)
	for name in HELD:
		var scene := (load(HELD[name]) as PackedScene).instantiate()
		scene.name = name
		places.add_child(scene)
	for i in 4:
		await process_frame
		await physics_frame
	var held := {}
	var open := {}
	var kinds := {}
	for name in HELD:
		var scene := places.get_node(name)
		for n in [scene] + scene.find_children("*", "", true, false):
			var faces := _collision_faces(n)
			if faces.is_empty():
				continue
			var path := "places/" + str(places.get_path_to(n))
			held[path] = faces
			open[path] = _open_edges(faces)
			kinds[path] = "csg" if n is CSGShape3D else "body"
	index["held"] = _write_pieces(dir.path_join("held.f32"), held, 3)
	for rec in index["held"]:
		rec["kind"] = kinds[rec["name"]]
	index["held_open"] = _write_pieces(dir.path_join("held_open.f32"), open, 2)
	places.free()

	index["header"]["seconds"] = (Time.get_ticks_msec() - t0) / 1000.0
	var f := FileAccess.open(dir.path_join("faces.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(index, " ", false) + "\n")
	f.close()
	var faces_n := 0
	for rec in index["held"]:
		faces_n += int(rec["count"])
	var edges_n := 0
	for rec in index["held_open"]:
		edges_n += int(rec["count"])
	print("ground faces dump: master %d faces, baseline %d, held %d faces in %d colliders with %d open edges; %.1fs; %s" % [
		_count(index["master"]), _count(index["baseline"]), faces_n, held.size(), edges_n,
		index["header"]["seconds"], dir])
	return 0


func _count(pieces: Array) -> int:
	var n := 0
	for rec in pieces:
		n += int(rec["count"])
	return n


func _header() -> Dictionary:
	return {
		"what": "The faces the generator measures the ground from, as Godot loads them, for the height grid's bake.",
		"probe": "res://tools/_ground_faces_dump.gd",
		"written": Time.get_datetime_string_from_system(true) + "Z",
		"commit": _git(["rev-parse", "HEAD"]),
		"modified_tracked_in_scenes_assets_scripts": Array(_git(["status", "--porcelain", "--untracked-files=no", "--", "scenes", "assets", "scripts"]).split("\n", false)),
		"godot": Engine.get_version_info()["string"],
		"layout": "raw little-endian float32; faces three corners each, open edges two; a corner is (x, y, z), Godot world metres, y up, x east, z south",
		"master": WorldTerrainSource.MASTER_GLB,
		"baseline": WorldTerrainSource.BASELINE,
	}


## The master's or the copy's meshes end to end in `_joined`'s order: the
## generator's `_master_faces` and `_base_faces`, byte for byte.
func _write_faces(path: String, faces: Dictionary) -> Array:
	var joined := WorldTerrainSource._joined(faces)
	var order: Array = []
	for body in WorldTerrainSource.BODIES:
		if faces.has(body):
			order.append(body)
	var names: Array = faces.keys()
	names.sort()
	for body in names:
		if not String(body) in WorldTerrainSource.BODIES:
			order.append(body)
	var pieces: Array = []
	var first := 0
	for body in order:
		var n: int = (faces[body] as PackedVector3Array).size() / 3
		pieces.append({"name": String(body), "first": first, "count": n})
		first += n
	assert(first * 3 == joined.size())
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_buffer(joined.to_byte_array())
	f.close()
	print("  %s: %d meshes, %d faces" % [path.get_file(), pieces.size(), first])
	return pieces


func _write_pieces(path: String, pieces: Dictionary, per: int) -> Array:
	var out: Array = []
	var first := 0
	var f := FileAccess.open(path, FileAccess.WRITE)
	var names: Array = pieces.keys()
	names.sort()
	for name in names:
		var arr: PackedVector3Array = pieces[name]
		var n := arr.size() / per
		out.append({"name": name, "first": first, "count": n})
		f.store_buffer(arr.to_byte_array())
		first += n
	f.close()
	print("  %s: %d pieces, %d %s" % [path.get_file(), out.size(), first, "faces" if per == 3 else "edges"])
	return out


## A collider's faces in world space as the physics has them, or none.
func _collision_faces(n: Node) -> PackedVector3Array:
	var out := PackedVector3Array()
	if n is CSGShape3D:
		var csg := n as CSGShape3D
		if not (csg.is_root_shape() and csg.use_collision):
			return out
		var shape := csg.bake_collision_shape()
		if shape == null:
			return out
		var xf := WorldTerrainSource._world_xf(csg)
		for v in shape.get_faces():
			out.append(xf * v)
		return out
	if n is CollisionObject3D:
		for c in n.get_children():
			var cs := c as CollisionShape3D
			if cs == null or cs.disabled or cs.shape == null:
				continue
			var xf := WorldTerrainSource._world_xf(cs)
			if cs.shape is ConcavePolygonShape3D:
				for v in (cs.shape as ConcavePolygonShape3D).get_faces():
					out.append(xf * v)
			else:
				# A box or other convex shape: its debug mesh's faces are its faces.
				var mesh := cs.shape.get_debug_mesh()
				for v in mesh.get_faces():
					out.append(xf * v)
	return out


## The edges one face uses, corners matched bit for bit, each as its face gives it.
func _open_edges(faces: PackedVector3Array) -> PackedVector3Array:
	var count := {}
	var first := {}
	for t in range(0, faces.size(), 3):
		for k in 3:
			var a := faces[t + k]
			var b := faces[t + (k + 1) % 3]
			var key := _edge_key(a, b)
			count[key] = int(count.get(key, 0)) + 1
			if not first.has(key):
				first[key] = [a, b]
	var out := PackedVector3Array()
	for key in count:
		if int(count[key]) == 1:
			out.append(first[key][0])
			out.append(first[key][1])
	return out


func _edge_key(a: Vector3, b: Vector3) -> String:
	var ka := PackedVector3Array([a]).to_byte_array().hex_encode()
	var kb := PackedVector3Array([b]).to_byte_array().hex_encode()
	return ka + kb if ka <= kb else kb + ka


func _delta(points_path: String, out_path: String) -> int:
	var bytes := FileAccess.get_file_as_bytes(points_path)
	if bytes.is_empty():
		printerr("ground faces dump: no points in ", points_path)
		return 1
	var pts := bytes.to_float32_array()
	var t0 := Time.get_ticks_msec()
	var source := WorldTerrainSource.new()
	var t1 := Time.get_ticks_msec()
	# The counts `summary()` opens with; its rise and fall cost minutes.
	print("world terrain master: %d faces added and %d removed since the copy, in %d cells of %.0fm" % [
		source.added, source.removed, source._dirty.size(), WorldTerrainSource.CELL])
	var out := PackedFloat64Array()
	out.resize(pts.size() / 2)
	for i in out.size():
		out[i] = source.delta_y(Vector2(pts[i * 2], pts[i * 2 + 1]))
	var f := FileAccess.open(out_path, FileAccess.WRITE)
	f.store_buffer(out.to_byte_array())
	f.close()
	print("ground faces dump: delta_y at %d points; source %.1fs, points %.1fs; %s" % [
		out.size(), (t1 - t0) / 1000.0, (Time.get_ticks_msec() - t1) / 1000.0, out_path])
	return 0


func _read(exr_dir: String, out_dir: String) -> int:
	DirAccess.make_dir_recursive_absolute(out_dir)
	var n := 0
	var files := Array(DirAccess.get_files_at(exr_dir))
	files.sort()
	for file in files:
		if not String(file).ends_with(".exr"):
			continue
		var img := Image.load_from_file(exr_dir.path_join(file))
		if img == null:
			printerr("ground faces dump: cannot read ", file)
			return 1
		var base := out_dir.path_join(String(file).get_basename())
		var f := FileAccess.open(base + ".bin", FileAccess.WRITE)
		f.store_buffer(img.get_data())
		f.close()
		var meta := {"width": img.get_width(), "height": img.get_height(),
			"format": img.get_format(), "format_name": _format_name(img.get_format()),
			"mipmaps": img.has_mipmaps()}
		f = FileAccess.open(base + ".json", FileAccess.WRITE)
		f.store_string(JSON.stringify(meta) + "\n")
		f.close()
		n += 1
	print("ground faces dump: read %d EXR into %s" % [n, out_dir])
	return 0 if n > 0 else 1


func _format_name(format: int) -> String:
	match format:
		Image.FORMAT_RF:
			return "RF"
		Image.FORMAT_RGF:
			return "RGF"
		Image.FORMAT_RGBF:
			return "RGBF"
		Image.FORMAT_RGBAF:
			return "RGBAF"
		Image.FORMAT_RH:
			return "RH"
		Image.FORMAT_RGBAH:
			return "RGBAH"
	return str(format)


func _git(args: Array) -> String:
	var out := []
	OS.execute("git", PackedStringArray(["-C", ProjectSettings.globalize_path("res://")] + args), out, true)
	return (out[0] as String).strip_edges(false, true) if not out.is_empty() else ""
